from __future__ import annotations

from handleguard.behaviours.base import BehaviourDetector, FrameContext, confidence_from

# Ordered pairs that constitute a bad sequence for one entity. Deliberately a
# handful of concrete, reliable pairs rather than a general SOP state machine:
# a full FSM inherits every upstream error (a missed B05 breaks the chain, an id
# switch splits one entity's history in two), so its precision is roughly the
# product of its dependencies'. One demonstrable chain beats a general model that
# never fires.
UNSAFE_PAIRS: dict[tuple[str, str], str] = {
    ("B03", "B01"): "dragged, then dropped",
    ("B01", "B01"): "dropped repeatedly",
    ("B02", "B01"): "thrown, then dropped",
    ("B01", "B07"): "dropped, then left in a restricted zone",
    ("B03", "B07"): "dragged, then left in a restricted zone",
    ("B06", "B01"): "stacked unstably, then dropped",
}


class UnsafeSequenceDetector(BehaviourDetector):
    """B11 — two risky behaviours on the same entity, in a bad order.

    Consumes the deduplicated event history rather than raw tracks, which makes
    it the one detector that reasons across events. That is also why it is the
    most fragile: it can only be as good as everything upstream of it.

    Reported as *lightly validated*.
    """

    id = "B11"
    name = "unsafe_sequence"
    config_key = "unsafe_sequence"

    def update(self, ctx: FrameContext):
        window = float(self.cfg["cooldown_seconds"])
        recent = [e for e in ctx.recent_events if ctx.t - e.end_t <= window]
        if len(recent) < 2:
            return []

        events = []
        seen: set[tuple[str, str, int]] = set()
        ordered = sorted(recent, key=lambda e: e.start_t)

        for i, first in enumerate(ordered):
            for second in ordered[i + 1 :]:
                if second.start_t < first.end_t:
                    continue
                shared = set(first.track_ids) & set(second.track_ids)
                if not shared:
                    continue
                description = UNSAFE_PAIRS.get((first.behaviour_id, second.behaviour_id))
                if description is None:
                    continue

                entity = min(shared)
                key = (first.behaviour_id, second.behaviour_id, entity)
                if key in seen:
                    continue
                seen.add(key)

                gap = second.start_t - first.end_t
                events.append(
                    self.event(
                        ctx,
                        tuple(sorted(shared)),
                        start_t=first.start_t,
                        severity=float(self.cfg["base_severity"]),
                        confidence=confidence_from(
                            min(first.confidence, second.confidence),
                            min(first.confidence, second.confidence),
                        ),
                        evidence={
                            "sequence": f"{first.name} -> {second.name}",
                            "description": description,
                            "gap_seconds": round(gap, 3),
                            "basis": "ordered pair over deduplicated events for one entity",
                        },
                        zone=second.zone or first.zone,
                    )
                )
        return events
