from __future__ import annotations

from handleguard.behaviours.base import BehaviourDetector, FrameContext, confidence_from


class ZoneViolationDetector(BehaviourDetector):
    id = "B07"
    name = "zone_violation"
    config_key = "zone_violation"

    def update(self, ctx: FrameContext):
        events = []
        duration = float(self.cfg["min_duration_seconds"])
        lookback = float(self.cfg["cooldown_seconds"])
        for track_id in ctx.products():
            feat = ctx.f(track_id)
            if feat.zone is None:
                continue
            window = ctx.window(track_id, lookback)
            in_same_zone = [f for f in window if f.zone == feat.zone]
            if feat.zone in {"walkway", "restricted", "restricted_product"} and in_same_zone:
                span = in_same_zone[-1].t - in_same_zone[0].t
                margin = span / duration
                if span >= duration:
                    events.append(
                        self.event(
                            ctx,
                            (track_id,),
                            start_t=in_same_zone[0].t,
                            severity=float(self.cfg["base_severity"]),
                            confidence=confidence_from(margin, ctx.tracks[track_id].conf),
                            evidence={
                                "zone": feat.zone,
                                "duration_seconds": round(span, 3),
                            },
                            zone=feat.zone,
                        )
                    )
        return events
