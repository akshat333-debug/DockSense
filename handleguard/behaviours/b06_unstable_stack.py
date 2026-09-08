from __future__ import annotations

from handleguard.behaviours.base import (
    BehaviourDetector,
    FrameContext,
    confidence_from,
    stack_pair,
    sustained_seconds,
)


class UnstableStackDetector(BehaviourDetector):
    """B06 — a stacked item is insufficiently supported by the tier below it.

    Fires on low support ratio (the upper box hangs off the lower one) sustained
    long enough to be a real stack rather than a box mid-transit.
    """

    id = "B06"
    name = "unstable_stack"
    config_key = "unstable_stack"

    def update(self, ctx: FrameContext):
        events = []
        max_support = float(self.cfg["max_support_ratio"])
        min_duration = float(self.cfg["min_duration_seconds"])
        lookback = float(self.cfg["cooldown_seconds"])

        for upper_id in ctx.products():
            # Low overlap threshold on purpose: a badly overhanging box is the
            # case this detector exists for, and the default would hide it.
            candidates = ctx.below(upper_id, min_overlap=0.05)
            supports = [i for i in candidates if ctx.tracks[i].role in {"product", "support"}]
            if not supports:
                continue
            # Best-supported neighbour decides stability: a box resting across two
            # others is stable if either holds it well.
            ratios = [(stack_pair(ctx, upper_id, i)[2], i) for i in supports]
            support_ratio, lower_id = max(ratios)
            if support_ratio >= max_support:
                continue

            window = ctx.window(upper_id, lookback)
            span = sustained_seconds(window, lambda f: True)
            if span < min_duration:
                continue

            deficit = (max_support - support_ratio) / max(max_support, 1e-6)
            margin = min(deficit, span / min_duration - 1.0)
            severity = float(self.cfg["base_severity"]) + min(max(deficit, 0.0), 1.0) * 0.15
            events.append(
                self.event(
                    ctx,
                    (upper_id, lower_id),
                    start_t=window[0].t if window else ctx.t,
                    severity=severity,
                    confidence=confidence_from(margin, ctx.tracks[upper_id].conf),
                    evidence={
                        "support_ratio": round(support_ratio, 3),
                        "required_support_ratio": max_support,
                        "sustained_seconds": round(span, 3),
                    },
                    zone=ctx.f(upper_id).zone,
                )
            )
        return events
