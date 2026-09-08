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


# --- multi-track scenarios -------------------------------------------------
#
# B05/B06/B08/B09 are relations *between* tracks, so they need more than the
# single-track context above. Boxes are given as pixel xyxy because these
# behaviours are static geometry; the detectors read them only through the
# shared helpers in behaviours.base, never directly.


def make_multi_ctx(
    tracks: list[Track],
    per_track_features: dict[int, list[TrackFeatures]],
    *,
    cfg: dict | None = None,
) -> FrameContext:
    """Build a FrameContext holding several interacting tracks."""
    history = TrackHistory(max_seconds=10.0)
    length = max(len(v) for v in per_track_features.values())
    for i in range(length):
        step = {
            tid: feats[i]
            for tid, feats in per_track_features.items()
            if i < len(feats)
        }
        history.push(step)

    latest = {tid: feats[-1] for tid, feats in per_track_features.items()}
    now = max(f.t for f in latest.values())
    return FrameContext(
        frame_index=length - 1,
        t=now,
        dt=0.5,
        fw=FW,
        fh=FH,
        tracks={t.id: t for t in tracks},
        feats=latest,
        history=history,
        cfg=cfg or {},
    )


def _static_feats(track_id: int, cx: float, cy: float, h_px: float, n: int = 8, step: float = 0.5):
    """A track that sits still — the sustained-duration case."""
    return [feat(track_id=track_id, t=i * step, cx=cx, cy=cy, h_px=h_px) for i in range(n)]


def _stack(upper_box, lower_box, *, upper_h, lower_h, n=8):
    upper = synth_track(track_id=1, xyxy=upper_box)
    lower = synth_track(track_id=2, xyxy=lower_box)
    return make_multi_ctx(
        [upper, lower],
        {
            1: _static_feats(1, 0.5, 0.4, upper_h, n=n),
            2: _static_feats(2, 0.5, 0.6, lower_h, n=n),
        },
    )


def scenario_improper_stack() -> FrameContext:
    """Large box (200x120) resting on a small one (100x60). B05 must fire."""
    return _stack((400, 300, 600, 420), (450, 420, 550, 480), upper_h=120, lower_h=60)


def scenario_correct_stack() -> FrameContext:
    """HARD NEGATIVE: small box on a large one. B05 must stay silent."""
    return _stack((450, 360, 550, 420), (400, 420, 600, 540), upper_h=60, lower_h=120)


def scenario_unstable_stack() -> FrameContext:
    """Upper box overhangs badly — only a sliver is supported. B06 must fire."""
    return _stack((520, 300, 680, 420), (400, 420, 560, 540), upper_h=120, lower_h=120)


def scenario_stable_stack() -> FrameContext:
    """HARD NEGATIVE: fully supported and aligned. B06 must stay silent."""
    return _stack((410, 300, 590, 420), (400, 420, 600, 540), upper_h=120, lower_h=120)


def _pallet(product_box, pallet_box, n=8):
    product = synth_track(track_id=1, xyxy=product_box)
    pallet = synth_track(track_id=2, cls="pallet", role="support", xyxy=pallet_box)
    return make_multi_ctx(
        [product, pallet],
        {1: _static_feats(1, 0.5, 0.5, 120, n=n), 2: _static_feats(2, 0.5, 0.6, 40, n=n)},
    )


def scenario_pallet_overhang() -> FrameContext:
    """Product hangs half off the pallet edge. B08 must fire."""
    return _pallet((500, 400, 700, 520), (400, 400, 600, 560))


def scenario_pallet_well_supported() -> FrameContext:
    """HARD NEGATIVE: product sits fully within the pallet. B08 must stay silent."""
    return _pallet((430, 400, 570, 520), (400, 400, 600, 560))


def _person_product(person_box, product_box, n=8):
    person = synth_track(track_id=1, cls="person", role="actor", xyxy=person_box)
    product = synth_track(track_id=2, xyxy=product_box)
    return make_multi_ctx(
        [person, product],
        {1: _static_feats(1, 0.5, 0.4, 300, n=n), 2: _static_feats(2, 0.5, 0.7, 60, n=n)},
    )


def scenario_stepping_on_product() -> FrameContext:
    """Person's feet land on the carton's top face. B09 must fire."""
    return _person_product((480, 200, 580, 500), (460, 480, 620, 560))


def scenario_walking_past_product() -> FrameContext:
    """HARD NEGATIVE: person beside the carton, no contact. B09 must stay silent."""
    return _person_product((200, 200, 300, 500), (460, 480, 620, 560))


def scenario_unsafe_surface() -> FrameContext:
    """Product lingers in a wet-floor zone. B12 must fire."""
    values = [
        feat(t=i * 0.5, cx=0.45, cy=0.70, floor_gap=0.0, zone="wet_floor")
        for i in range(6)
    ]
    return make_ctx(values)


def scenario_safe_surface() -> FrameContext:
    """HARD NEGATIVE: same dwell, but the zone is a normal staging area."""
    values = [
        feat(t=i * 0.5, cx=0.45, cy=0.70, floor_gap=0.0, zone="staging")
        for i in range(6)
    ]
    return make_ctx(values)
