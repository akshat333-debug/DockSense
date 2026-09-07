"""Shared behaviour detector contract.

Five rules:

1. A detector **never** deduplicates, cools down, or scores risk. It fires whenever its condition holds. `EventDeduper` owns cooldown; `risk.scorer` owns scoring. This single rule removes the largest source of twelve inconsistent implementations.
2. A detector reads thresholds **only** from `self.cfg`. No numeric literals in detector bodies. Need a new threshold -> add it to `behaviours.yaml` under your key.
3. All distances in object-heights, all velocities in object-heights/sec. **A detector touching raw `xyxy` is a bug** -- `grep xyxy handleguard/behaviours/` is a review check.
4. `severity` starts at config `base_severity`, may be scaled +/-0.15 by magnitude. `confidence` comes from the shared helper `base.confidence_from(margin, track_conf)` so all twelve agree.
5. `evidence` dict values must be JSON-serializable scalars -- they render into explanations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Sequence

from handleguard.perception import geometry as g
from handleguard.types import BehaviourEvent, Track, TrackFeatures


@dataclass
class TrackHistory:
    """Short per-track feature lookback."""

    max_seconds: float = 5.0
    _features: dict[int, deque[TrackFeatures]] = field(default_factory=lambda: defaultdict(deque))

    def push(self, feats: dict[int, TrackFeatures]) -> None:
        for track_id, feat in feats.items():
            q = self._features[track_id]
            q.append(feat)
            cutoff = feat.t - self.max_seconds
            while q and q[0].t < cutoff:
                q.popleft()

    def window(self, track_id: int, seconds: float, now: float | None = None) -> list[TrackFeatures]:
        values = list(self._features.get(track_id, ()))
        if not values:
            return []
        end_t = values[-1].t if now is None else now
        cutoff = end_t - seconds
        return [feat for feat in values if feat.t >= cutoff]


@dataclass(frozen=True)
class FrameContext:
    """Read-only frame context passed to all behaviour detectors."""

    frame_index: int
    t: float
    dt: float
    fw: int
    fh: int
    tracks: dict[int, Track]
    feats: dict[int, TrackFeatures]
    history: TrackHistory
    zones: Any = None
    floor: Any = None
    cfg: dict[str, Any] = field(default_factory=dict)
    recent_events: Sequence[BehaviourEvent] = ()

    def persons(self) -> list[int]:
        return self.by_role("actor")

    def products(self) -> list[int]:
        return self.by_role("product")

    def by_role(self, role: str) -> list[int]:
        return [track_id for track_id, track in self.tracks.items() if track.role == role]

    def f(self, track_id: int) -> TrackFeatures:
        return self.feats[track_id]

    def window(self, track_id: int, seconds: float) -> list[TrackFeatures]:
        return self.history.window(track_id, seconds, self.t)

    def overlapping(
        self,
        track_id: int,
        role: str | None = None,
        min_iou: float = 0.05,
    ) -> list[int]:
        base = self.tracks[track_id]
        out: list[int] = []
        for other_id, other in self.tracks.items():
            if other_id == track_id:
                continue
            if role is not None and other.role != role:
                continue
            if g.iou(base.xyxy, other.xyxy) >= min_iou:
                out.append(other_id)
        return out

    def below(self, track_id: int) -> list[int]:
        base = self.tracks[track_id]
        out: list[int] = []
        for other_id, other in self.tracks.items():
            if other_id == track_id:
                continue
            max_gap = max(base.height * 0.15, 2.0)
            if g.is_above(base.xyxy, other.xyxy, max_gap=max_gap):
                out.append(other_id)
        return out


class BehaviourDetector(ABC):
    id: str = ""
    name: str = ""
    config_key: str = ""
    requires_roles: set[str] = {"product"}

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.cfg = cfg

    @abstractmethod
    def update(self, ctx: FrameContext) -> list[BehaviourEvent]:
        raise NotImplementedError

    def reset(self) -> None:
        return None

    @property
    def enabled(self) -> bool:
        return bool(self.cfg.get("enabled", True))

    def event(
        self,
        ctx: FrameContext,
        track_ids: tuple[int, ...],
        *,
        start_t: float,
        severity: float,
        confidence: float,
        evidence: dict[str, Any],
        zone: str | None = None,
    ) -> BehaviourEvent:
        return BehaviourEvent(
            behaviour_id=self.id,
            name=self.name,
            track_ids=track_ids,
            start_frame=ctx.frame_index,
            end_frame=ctx.frame_index,
            start_t=start_t,
            end_t=ctx.t,
            severity=max(0.0, min(float(severity), 1.0)),
            confidence=max(0.0, min(float(confidence), 1.0)),
            evidence=evidence,
            zone=zone,
        )


class StubDetector(BehaviourDetector):
    """Registered placeholder for behaviours not yet implemented."""

    def update(self, ctx: FrameContext) -> list[BehaviourEvent]:
        return []


def confidence_from(margin: float, track_conf: float) -> float:
    """Shared confidence helper for detector decisions."""
    margin_score = max(0.0, min(float(margin), 1.0))
    return max(0.0, min(0.35 + 0.45 * margin_score + 0.20 * float(track_conf), 1.0))


def travel_heights(window: Sequence[TrackFeatures], frame_h: int) -> tuple[float, float, float]:
    """Return dx, dy, and total travel in object-height units."""
    if len(window) < 2:
        return 0.0, 0.0, 0.0
    first, last = window[0], window[-1]
    h_px = max((first.h_px + last.h_px) / 2.0, 1e-6)
    dx = (last.cx - first.cx) * frame_h / h_px
    dy = (last.cy - first.cy) * frame_h / h_px
    return dx, dy, float((dx * dx + dy * dy) ** 0.5)
