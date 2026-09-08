from __future__ import annotations

from handleguard.behaviours.base import BehaviourDetector, FrameContext, confidence_from


class RoughHandlingDetector(BehaviourDetector):
    """B04 — abrupt acceleration or deceleration around contact.

    **Weakest of the twelve, deliberately conservative.** "Rough" has no geometric
    definition. The proxy here is acceleration, which is the second derivative of
    a bounding-box centroid sampled at 8 fps from a tracker that jitters — a
    detector re-fitting a partly occluded carton produces spikes indistinguishable
    from real ones.

    It also overlaps B01/B02 by construction: every genuine drop spikes
    acceleration too. To stop it echoing behaviours that are already detected
    better elsewhere, it suppresses itself when a drop or throw for the same
    entity is already in flight, and requires both a spike *and* a hard stop
    rather than either alone.

    Reported as *lightly validated*. Do not quote a precision figure for it.
    """

    id = "B04"
    name = "rough_handling"
    config_key = "rough_handling"

    _SUPERSEDED_BY = {"B01", "B02"}

    def update(self, ctx: FrameContext):
        events = []
        min_spike = float(self.cfg["min_accel_spike"])
        min_decel = float(self.cfg["min_decel"])
        lookback = float(self.cfg["cooldown_seconds"])

        claimed = {
            tid
            for ev in ctx.recent_events
            if ev.behaviour_id in self._SUPERSEDED_BY
            for tid in ev.track_ids
        }

        for track_id in ctx.products():
            if track_id in claimed:
                continue
            window = ctx.window(track_id, lookback)
            if len(window) < 3:
                continue

            feat = ctx.f(track_id)
            spike = max(abs(f.ax) + abs(f.ay) for f in window)
            decel = max(
                (prev.vy - nxt.vy for prev, nxt in zip(window, window[1:])),
                default=0.0,
            )
            # Both conditions, not either: a spike alone is usually tracker noise.
            if spike < min_spike or decel < min_decel:
                continue

            margin = min(spike / min_spike - 1.0, decel / min_decel - 1.0)
            events.append(
                self.event(
                    ctx,
                    (track_id,),
                    start_t=window[0].t,
                    severity=float(self.cfg["base_severity"]),
                    confidence=confidence_from(margin, ctx.tracks[track_id].conf),
                    evidence={
                        "peak_acceleration": round(spike, 3),
                        "peak_deceleration": round(decel, 3),
                        "basis": "acceleration proxy; sensitive to tracker jitter",
                    },
                    zone=feat.zone,
                )
            )
        return events
