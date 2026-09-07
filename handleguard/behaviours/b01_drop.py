from __future__ import annotations

from handleguard.behaviours.base import BehaviourDetector, FrameContext, confidence_from, travel_heights


class DropDetector(BehaviourDetector):
    id = "B01"
    name = "drop"
    config_key = "drop"

    def update(self, ctx: FrameContext):
        events = []
        lookback = float(self.cfg["cooldown_seconds"])
        for track_id in ctx.products():
            feat = ctx.f(track_id)
            window = ctx.window(track_id, lookback)
            dx, dy, _ = travel_heights(window, ctx.fh)
            prev = window[-2] if len(window) >= 2 else feat
            decel = max(prev.vy - feat.vy, 0.0)
            margin = min(
                dy / float(self.cfg["min_fall_heights"]),
                feat.vy / float(self.cfg["min_downward_velocity"]),
                decel / float(self.cfg["impact_decel"]) if decel else 0.0,
            )
            if (
                dy >= float(self.cfg["min_fall_heights"])
                and feat.vy >= float(self.cfg["min_downward_velocity"])
                and feat.horizontal_ratio <= float(self.cfg["max_horizontal_ratio"])
            ) or (
                dy >= float(self.cfg["min_fall_heights"])
                and decel >= float(self.cfg["impact_decel"])
                and feat.horizontal_ratio <= float(self.cfg["max_horizontal_ratio"])
            ):
                severity = float(self.cfg["base_severity"]) + min(max(dy - 1.0, 0.0), 1.0) * 0.15
                events.append(
                    self.event(
                        ctx,
                        (track_id,),
                        start_t=window[0].t if window else ctx.t,
                        severity=severity,
                        confidence=confidence_from(margin, ctx.tracks[track_id].conf),
                        evidence={
                            "fall_heights": round(dy, 3),
                            "downward_velocity": round(feat.vy, 3),
                            "impact_decel": round(decel, 3),
                            "horizontal_ratio": round(feat.horizontal_ratio, 3),
                        },
                        zone=feat.zone,
                    )
                )
        return events
