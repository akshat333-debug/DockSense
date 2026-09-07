"""Convert scored events into supervisor-facing incidents."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib

from handleguard.incidents.sop import sop_for
from handleguard.risk.explain import explain_event
from handleguard.risk.scorer import score_event
from handleguard.types import BehaviourEvent, Incident, RiskScore


def build_incident(
    event: BehaviourEvent,
    *,
    video_id: str,
    session: str,
    camera: str,
    risk: RiskScore | None = None,
    clip_path: str | None = None,
    thumb_path: str | None = None,
    incident_id: str | None = None,
) -> Incident:
    risk = risk or score_event(event)
    incident_id = incident_id or incident_id_for(event, video_id)
    return Incident(
        id=incident_id,
        behaviour_id=event.behaviour_id,
        name=event.name,
        video_id=video_id,
        session=session,
        camera=camera,
        start_t=event.start_t,
        end_t=event.end_t,
        risk=risk,
        explanation=explain_event(event, risk),
        sop=sop_for(event.name),
        clip_path=clip_path,
        thumb_path=thumb_path,
        track_ids=event.track_ids,
        zone=event.zone,
        evidence=event.evidence,
        created_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
    )


def incident_id_for(event: BehaviourEvent, video_id: str) -> str:
    raw = f"{video_id}|{event.behaviour_id}|{event.start_t:.3f}|{event.end_t:.3f}|{event.track_ids}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8].upper()
    return f"INC-{digest}"
