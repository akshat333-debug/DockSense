"""Evidence-only explanation text for incidents."""

from __future__ import annotations

from handleguard.types import BehaviourEvent, RiskScore


def explain_event(event: BehaviourEvent, risk: RiskScore) -> str:
    parts = [
        f"Observed potential {event.name.replace('_', ' ')} from {event.start_t:.2f}s to {event.end_t:.2f}s",
        f"risk is {risk.band} ({risk.score:.1f}/100)",
        f"confidence is {risk.confidence:.2f}",
    ]
    if event.zone:
        parts.append(f"zone: {event.zone}")
    evidence = _evidence_phrase(event)
    if evidence:
        parts.append(evidence)
    return ". ".join(parts) + "."


def _evidence_phrase(event: BehaviourEvent) -> str:
    labels = {
        "fall_heights": "fall distance",
        "downward_velocity": "downward velocity",
        "impact_decel": "impact deceleration",
        "horizontal_ratio": "horizontal motion ratio",
        "horizontal_travel_heights": "horizontal travel",
        "drag_distance_heights": "drag distance",
        "speed": "speed",
    }
    items = []
    for key, label in labels.items():
        if key in event.evidence:
            items.append(f"{label} {event.evidence[key]}")
    if not items:
        return ""
    return "Evidence: " + ", ".join(items[:4])
