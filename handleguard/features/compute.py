"""Track-to-feature conversion for behaviour detectors.

This is the normalization boundary. Everything below here may speak pixels;
everything above here receives object-height-scaled motion features.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

from handleguard import config
from handleguard.perception import geometry as g
from handleguard.types import Frame, Track, TrackFeatures


@dataclass
class FeatureExtractor:
    """Compute normalized temporal and context features for active tracks."""

    camera: str = "demo_cam_1"
    window_frames: int | None = None
    floor_y_norm: float = 0.86
    zones_cfg: dict[str, Any] | None = None
    _prev: dict[int, TrackFeatures] = field(default_factory=dict)
    _windows: dict[int, deque[TrackFeatures]] = field(default_factory=lambda: defaultdict(deque))

    def __post_init__(self) -> None:
        if self.window_frames is None:
            self.window_frames = int(config.behaviours().get("smoothing", {}).get("window_frames", 5))
        if self.zones_cfg is None:
            self.zones_cfg = config.zones()

    def reset(self) -> None:
        self._prev.clear()
        self._windows.clear()

    def update(self, tracks: list[Track], frame: Frame) -> dict[int, TrackFeatures]:
        out: dict[int, TrackFeatures] = {}
        by_id = {track.id: track for track in tracks}
        for track in tracks:
            feat = self._compute_one(track, frame, by_id)
            self._remember(feat)
            out[track.id] = feat

        active_ids = set(by_id)
        for track_id in list(self._prev):
            if track_id not in active_ids:
                del self._prev[track_id]
        for track_id in list(self._windows):
            if track_id not in active_ids:
                del self._windows[track_id]
        return out

    def _compute_one(self, track: Track, frame: Frame, tracks: dict[int, Track]) -> TrackFeatures:
        x1, y1, x2, y2 = track.xyxy
        h_px = max(y2 - y1, 1e-6)
        cx_px, cy_px = g.center(track.xyxy)
        cx = _clamp01(cx_px / max(frame.w, 1))
        cy = _clamp01(cy_px / max(frame.h, 1))
        area_px = g.area(track.xyxy)

        prev = self._prev.get(track.id)
        if prev is None or frame.t <= prev.t:
            vx = vy = ax = ay = 0.0
        else:
            dt = frame.t - prev.t
            norm_h = max((h_px + prev.h_px) / 2.0, 1e-6)
            vx = (cx - prev.cx) * frame.w / norm_h / dt
            vy = (cy - prev.cy) * frame.h / norm_h / dt
            ax = (vx - prev.vx) / dt
            ay = (vy - prev.vy) / dt

        zone = self._zone_for(track, frame)
        floor_gap = max((self.floor_y_norm * frame.h) - y2, 0.0) / h_px
        supported_by = tuple(
            other.id
            for other in tracks.values()
            if other.id != track.id and other.role != "actor" and g.is_above(track.xyxy, other.xyxy, max_gap=max(h_px * 0.15, 2.0))
        )
        held_by_person = any(
            self._looks_held(track, other)
            for other in tracks.values()
            if other.id != track.id and other.role == "actor"
        )

        provisional = TrackFeatures(
            track_id=track.id,
            t=frame.t,
            h_px=h_px,
            cx=cx,
            cy=cy,
            vx=vx,
            vy=vy,
            ax=ax,
            ay=ay,
            horizontal_ratio=0.0,
            floor_gap=floor_gap,
            area_px=area_px,
            zone=zone,
            supported_by=supported_by,
            held_by_person=held_by_person,
        )
        return TrackFeatures(
            **{
                **provisional.__dict__,
                "horizontal_ratio": self._horizontal_ratio(track.id, provisional, frame),
            }
        )

    def _remember(self, feat: TrackFeatures) -> None:
        self._prev[feat.track_id] = feat
        q = self._windows[feat.track_id]
        q.append(feat)
        while len(q) > int(self.window_frames or 1):
            q.popleft()

    def _horizontal_ratio(self, track_id: int, current: TrackFeatures, frame: Frame) -> float:
        values = list(self._windows.get(track_id, ())) + [current]
        if len(values) < 2:
            return 0.0
        first, last = values[0], values[-1]
        dx = abs(last.cx - first.cx) * frame.w
        dy = abs(last.cy - first.cy) * frame.h
        total = dx + dy
        return dx / total if total > 0 else 0.0

    def _zone_for(self, track: Track, frame: Frame) -> str | None:
        cameras = (self.zones_cfg or {}).get("cameras", {})
        zones = cameras.get(self.camera, {}).get("zones", [])
        bx, by = g.bottom_center(track.xyxy)
        pt = (bx / max(frame.w, 1), by / max(frame.h, 1))
        selected: str | None = None
        for zone in zones:
            poly = [(float(x), float(y)) for x, y in zone.get("polygon", [])]
            if g.point_in_polygon(pt, poly):
                selected = str(zone.get("name"))
                if str(zone.get("type", "")).startswith("restricted"):
                    return selected
        return selected

    @staticmethod
    def _looks_held(product: Track, actor: Track) -> bool:
        overlap = g.horizontal_overlap(product.xyxy, actor.xyxy) / max(product.width, 1e-6)
        vertical_intersection = min(product.xyxy[3], actor.xyxy[3]) - max(product.xyxy[1], actor.xyxy[1])
        return overlap >= 0.25 and vertical_intersection > 0


def _clamp01(value: float) -> float:
    return max(0.0, min(float(value), 1.0))
