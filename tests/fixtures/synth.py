from __future__ import annotations

from dataclasses import replace

from handleguard.behaviours.base import FrameContext, TrackHistory
from handleguard.types import Track, TrackFeatures


FW, FH = 1280, 720


def synth_track(
    *,
    track_id: int = 1,
    cls: str = "carton",
    role: str = "product",
    xyxy=(100.0, 100.0, 180.0, 180.0),
    conf: float = 0.9,
) -> Track:
    return Track(
        id=track_id,
        cls=cls,
        role=role,
        xyxy=xyxy,
        conf=conf,
        first_frame=0,
        last_frame=0,
        age=10,
    )


def feat(
    *,
    track_id: int = 1,
    t: float,
    cx: float,
    cy: float,
    h_px: float = 80.0,
    vx: float = 0.0,
    vy: float = 0.0,
    ax: float = 0.0,
    ay: float = 0.0,
    horizontal_ratio: float = 0.0,
    floor_gap: float | None = None,
    zone: str | None = None,
    held_by_person: bool = False,
) -> TrackFeatures:
    return TrackFeatures(
        track_id=track_id,
        t=t,
        h_px=h_px,
        cx=cx,
        cy=cy,
        vx=vx,
        vy=vy,
        ax=ax,
        ay=ay,
        horizontal_ratio=horizontal_ratio,
        floor_gap=floor_gap,
        zone=zone,
        held_by_person=held_by_person,
    )


def make_ctx(
    history_features: list[TrackFeatures],
    *,
    track: Track | None = None,
    cfg: dict | None = None,
) -> FrameContext:
    if not history_features:
        raise ValueError("history_features must not be empty")
    latest = history_features[-1]
    tr = track or synth_track(track_id=latest.track_id)
    tr.last_frame = len(history_features) - 1
    history = TrackHistory(max_seconds=10.0)
    for f in history_features:
        history.push({f.track_id: f})
    return FrameContext(
        frame_index=len(history_features) - 1,
        t=latest.t,
        dt=history_features[-1].t - history_features[-2].t if len(history_features) > 1 else 0.0,
        fw=FW,
        fh=FH,
        tracks={tr.id: tr},
        feats={latest.track_id: latest},
        history=history,
        cfg=cfg or {},
    )


def scenario_drop() -> FrameContext:
    values = [
        feat(t=0.0, cx=0.50, cy=0.20, vy=0.1, horizontal_ratio=0.1, floor_gap=3.0),
        feat(t=0.5, cx=0.50, cy=0.28, vy=1.7, horizontal_ratio=0.1, floor_gap=2.0),
        feat(t=1.0, cx=0.50, cy=0.35, vy=2.8, horizontal_ratio=0.1, floor_gap=1.0),
        feat(t=1.5, cx=0.50, cy=0.40, vy=0.0, horizontal_ratio=0.1, floor_gap=0.0),
    ]
    return make_ctx(values)


def scenario_gentle_place() -> FrameContext:
    values = [
        feat(t=0.0, cx=0.50, cy=0.20, vy=0.2, horizontal_ratio=0.1, floor_gap=3.0),
        feat(t=0.5, cx=0.50, cy=0.24, vy=0.3, horizontal_ratio=0.1, floor_gap=2.4),
        feat(t=1.0, cx=0.50, cy=0.28, vy=0.3, horizontal_ratio=0.1, floor_gap=1.8),
        feat(t=1.5, cx=0.50, cy=0.31, vy=0.1, horizontal_ratio=0.1, floor_gap=0.0),
    ]
    return make_ctx(values)


def scenario_throw() -> FrameContext:
    values = [
        feat(t=0.0, cx=0.25, cy=0.30, vx=0.5, vy=-0.1, horizontal_ratio=0.8, floor_gap=2.0),
        feat(t=0.5, cx=0.38, cy=0.28, vx=2.3, vy=0.1, horizontal_ratio=0.9, floor_gap=2.2),
        feat(t=1.0, cx=0.52, cy=0.31, vx=2.5, vy=0.6, horizontal_ratio=0.85, floor_gap=1.8),
        feat(t=1.5, cx=0.65, cy=0.36, vx=2.4, vy=1.0, horizontal_ratio=0.82, floor_gap=1.1),
    ]
    return make_ctx(values)


def scenario_carry() -> FrameContext:
    values = [
        feat(t=0.0, cx=0.25, cy=0.35, vx=0.4, vy=0.0, horizontal_ratio=0.95, floor_gap=1.5, held_by_person=True),
        feat(t=0.5, cx=0.36, cy=0.35, vx=1.2, vy=0.0, horizontal_ratio=1.0, floor_gap=1.5, held_by_person=True),
        feat(t=1.0, cx=0.47, cy=0.35, vx=1.2, vy=0.0, horizontal_ratio=1.0, floor_gap=1.5, held_by_person=True),
        feat(t=1.5, cx=0.58, cy=0.35, vx=1.2, vy=0.0, horizontal_ratio=1.0, floor_gap=1.5, held_by_person=True),
    ]
    return make_ctx(values)


def scenario_drag() -> FrameContext:
    values = [
        feat(t=0.0, cx=0.20, cy=0.75, vx=0.4, horizontal_ratio=1.0, floor_gap=0.05),
        feat(t=0.5, cx=0.32, cy=0.75, vx=1.4, horizontal_ratio=1.0, floor_gap=0.05),
        feat(t=1.0, cx=0.44, cy=0.75, vx=1.4, horizontal_ratio=1.0, floor_gap=0.05),
        feat(t=1.5, cx=0.56, cy=0.75, vx=1.4, horizontal_ratio=1.0, floor_gap=0.05),
    ]
    return make_ctx(values)


def scenario_zone_violation() -> FrameContext:
    values = [
        feat(t=0.0, cx=0.47, cy=0.70, floor_gap=0.0, zone="walkway"),
        feat(t=1.0, cx=0.47, cy=0.70, floor_gap=0.0, zone="walkway"),
        feat(t=2.1, cx=0.47, cy=0.70, floor_gap=0.0, zone="walkway"),
    ]
    return make_ctx(values)


def scenario_transient_zone_crossing() -> FrameContext:
    values = [
        feat(t=0.0, cx=0.40, cy=0.70, floor_gap=0.0, zone="staging"),
        feat(t=1.0, cx=0.47, cy=0.70, floor_gap=0.0, zone="walkway"),
    ]
    return make_ctx(values)
