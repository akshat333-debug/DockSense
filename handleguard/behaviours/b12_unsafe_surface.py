from __future__ import annotations

from handleguard.behaviours.base import (
    BehaviourDetector,
    FrameContext,
    confidence_from,
    sustained_seconds,
)

UNSAFE_ZONES = {"unsafe_surface", "wet_floor"}


class UnsafeSurfaceDetector(BehaviourDetector):
    """B12 — product moved through a zone marked wet or otherwise unsafe.

    Zone-driven like B07, but keyed on surface condition rather than on the zone
    being off-limits. The unsafe area is configured by an operator in
    ``configs/zones.yaml``; we do not attempt to detect wetness from pixels.
    """

    id = "B12"
    name = "unsafe_surface"
    config_key = "unsafe_surface"

    def update(self, ctx: FrameContext):
        events = []
        min_duration = float(self.cfg["min_duration_seconds"])
        lookback = float(self.cfg["cooldown_seconds"])

        for track_id in ctx.products():
            feat = ctx.f(track_id)
            if feat.zone not in UNSAFE_ZONES:
                continue

            window = ctx.window(track_id, lookback)
            zone_name = feat.zone
            span = sustained_seconds(window, lambda f: f.zone == zone_name)
            if span < min_duration:
                continue

            margin = span / min_duration - 1.0
            events.append(
                self.event(
                    ctx,
                    (track_id,),
                    start_t=ctx.t - span,
                    severity=float(self.cfg["base_severity"]),
                    confidence=confidence_from(margin, ctx.tracks[track_id].conf),
                    evidence={
                        "zone": zone_name,
                        "sustained_seconds": round(span, 3),
                        "basis": "operator-configured unsafe zone, not visual surface detection",
                    },
                    zone=zone_name,
                )
            )
        return events
