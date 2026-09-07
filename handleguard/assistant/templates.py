"""Offline assistant templates and safety guardrails.

This module is deliberately deterministic. It answers only from incidents
returned by the store and never infers identity, intent, discipline, or damage.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Protocol

from handleguard import config
from handleguard.types import Incident

NO_MATCHING_INCIDENTS = "No matching incidents were found."
IDENTITY_REFUSAL = (
    "I cannot identify, name, rank, or describe workers. I can summarize "
    "observed product-handling incidents with incident IDs and timestamps."
)


class IncidentReader(Protocol):
    def query(self, **kwargs: Any) -> list[Incident]:
        ...

    def get(self, incident_id: str) -> Incident | None:
        ...


@dataclass(frozen=True)
class AssistantAnswer:
    answer: str
    incident_ids: list[str]


def answer_question(question: str, store: IncidentReader, *, limit: int = 10) -> AssistantAnswer:
    q = question.strip()
    if not q:
        return AssistantAnswer(NO_MATCHING_INCIDENTS, [])
    if asks_for_identity(q):
        return AssistantAnswer(IDENTITY_REFUSAL, [])

    rows = _select_incidents(q, store, limit=limit)
    if not rows:
        return AssistantAnswer(NO_MATCHING_INCIDENTS, [])
    return AssistantAnswer(_render_incident_lines(rows), [row.id for row in rows[:5]])


def asks_for_identity(question: str) -> bool:
    q = question.lower()
    identity_patterns = [
        r"\bwho\b",
        r"\bidentify\b",
        r"\bname\b",
        r"\bworker\b",
        r"\bemployee\b",
        r"\boperator\b",
        r"\bperson\b",
        r"\bwhich\s+(worker|employee|operator|person)\b",
    ]
    return any(re.search(pattern, q) for pattern in identity_patterns)


def guardrails() -> list[str]:
    return [str(item) for item in config.sop_rules().get("assistant_guardrails", [])]


def _select_incidents(question: str, store: IncidentReader, *, limit: int) -> list[Incident]:
    q = question.lower()
    incident_id = _incident_id_from_text(question)
    if incident_id:
        incident = store.get(incident_id)
        return [incident] if incident else []

    kwargs: dict[str, Any] = {"limit": limit}
    behaviour = _behaviour_from_text(q)
    if behaviour:
        kwargs["name"] = behaviour
    if "critical" in q:
        kwargs["band"] = "critical"
    elif "high" in q:
        kwargs["min_risk"] = 50.0
    elif "medium" in q:
        kwargs["band"] = "medium"
    elif "low" in q:
        kwargs["band"] = "low"

    status = _review_status_from_text(q)
    if status:
        kwargs["review_status"] = status

    zone = _zone_from_text(q)
    if zone:
        kwargs["zone"] = zone

    return store.query(**kwargs)


def _render_incident_lines(rows: list[Incident]) -> str:
    lines = [_incident_line(row) for row in rows[:5]]
    if len(rows) > 5:
        lines.append(f"{len(rows) - 5} additional matching incidents were omitted from this short answer.")
    return "\n".join(lines)


def _incident_line(row: Incident) -> str:
    zone = f" in {row.zone}" if row.zone else ""
    return (
        f"{row.id} at {row.start_t:.2f}s: observed potential "
        f"{row.name.replace('_', ' ')}{zone}; risk {row.risk.band} "
        f"({row.risk.score:.1f}/100), confidence {row.risk.confidence:.2f}."
    )


def _incident_id_from_text(text: str) -> str | None:
    match = re.search(r"\b(?:INC|SEED)-[A-Za-z0-9_-]+\b", text, flags=re.IGNORECASE)
    return match.group(0).upper() if match else None


def _behaviour_from_text(q: str) -> str | None:
    options = {
        "zone violation": "zone_violation",
        "zone_violation": "zone_violation",
        "drop": "drop",
        "throw": "throw",
        "drag": "drag",
        "rough handling": "rough_handling",
        "improper stack": "improper_stack",
        "unstable stack": "unstable_stack",
        "pallet overhang": "pallet_overhang",
        "stepping": "stepping",
        "manual heavy handling": "manual_heavy_handling",
        "unsafe sequence": "unsafe_sequence",
        "unsafe surface": "unsafe_surface",
    }
    for phrase, name in options.items():
        if phrase in q:
            return name
    return None


def _review_status_from_text(q: str) -> str | None:
    if "false positive" in q:
        return "false_positive"
    if "investigate" in q or "investigation" in q:
        return "needs_investigation"
    if "confirmed" in q:
        return "confirmed"
    if re.search(r"\bnew\b", q):
        return "new"
    return None


def _zone_from_text(q: str) -> str | None:
    for zone in ("loading_bay", "loading bay", "walkway", "staging", "danger_zone", "danger zone"):
        if zone in q:
            return zone.replace(" ", "_")
    return None
