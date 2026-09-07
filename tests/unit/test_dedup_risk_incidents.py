from __future__ import annotations

from handleguard.events.dedup import dedupe_events
from handleguard.incidents.builder import build_incident
from handleguard.risk.scorer import score_event
from handleguard.types import BehaviourEvent


def drop_event(i: int) -> BehaviourEvent:
    t = i * 0.1
    return BehaviourEvent(
        behaviour_id="B01",
        name="drop",
        track_ids=(7,),
        start_frame=i,
        end_frame=i,
        start_t=t,
        end_t=t,
        severity=0.9,
        confidence=0.8,
        evidence={
            "fall_heights": 1.3,
            "downward_velocity": 2.5,
            "impact_decel": 3.0,
            "horizontal_ratio": 0.1,
        },
        zone="walkway",
    )


def test_continuous_drop_dedupes_to_one_event():
    events = [drop_event(i) for i in range(40)]

    merged = dedupe_events(events)

    assert len(merged) == 1
    assert merged[0].start_frame == 0
    assert merged[0].end_frame == 39
    assert round(merged[0].end_t, 1) == 3.9


def test_risk_scoring_keeps_confidence_separate():
    risk = score_event(drop_event(0))

    assert risk.score >= 70
    assert risk.band in {"high", "critical"}
    assert risk.confidence == 0.8
    assert "confidence" not in risk.components
    assert round(sum(risk.weights_used.values()), 3) == 1.0


def test_incident_builder_uses_sop_and_guarded_explanation():
    incident = build_incident(
        drop_event(0),
        video_id="synthetic-drop",
        session="synthetic",
        camera="demo_cam_1",
    )

    assert incident.id.startswith("INC-")
    assert incident.sop
    assert "Observed potential drop" in incident.explanation
    forbidden = ["confirmed damage", "careless", "worker", "disciplinary"]
    assert not any(word in incident.explanation.lower() for word in forbidden)
