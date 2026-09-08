from __future__ import annotations

from pathlib import Path

from handleguard.assistant.templates import (
    IDENTITY_REFUSAL,
    NO_MATCHING_INCIDENTS,
    answer_question,
    asks_for_identity,
    guardrails,
)
from handleguard.db import IncidentStore
from scripts.seed_fake_incidents import seed


MEDIA = Path(__file__).resolve().parents[2] / "data" / "test_tmp"


def test_assistant_cites_incident_ids_and_timestamps():
    db_path = MEDIA / "assistant_cites.db"
    seed(db_path, n=8)
    answer = answer_question("show high risk drops", IncidentStore(db_path))

    assert answer.incident_ids
    for incident_id in answer.incident_ids:
        assert incident_id in answer.answer
    assert " at " in answer.answer
    assert "risk" in answer.answer
    assert "confidence" in answer.answer


def test_assistant_empty_result_uses_required_phrase():
    db_path = MEDIA / "assistant_empty.db"
    seed(db_path, n=4)
    answer = answer_question("show critical drag incidents in danger zone", IncidentStore(db_path))

    assert answer.answer == NO_MATCHING_INCIDENTS
    assert answer.incident_ids == []


def test_assistant_refuses_identity_requests():
    db_path = MEDIA / "assistant_identity.db"
    seed(db_path, n=4)
    answer = answer_question("who was the worker in SEED-0001?", IncidentStore(db_path))

    assert answer.answer == IDENTITY_REFUSAL
    assert answer.incident_ids == []
    assert asks_for_identity("identify the operator") is True


def test_assistant_can_answer_specific_incident_id():
    db_path = MEDIA / "assistant_id.db"
    seed(db_path, n=4)
    answer = answer_question("summarize seed-0001", IncidentStore(db_path))

    assert answer.incident_ids == ["SEED-0001"]
    assert "SEED-0001" in answer.answer


def test_assistant_guardrails_loaded_from_sop_config():
    rules = guardrails()

    assert "Never infer intent." in rules
    assert any("Cite incident IDs" in rule for rule in rules)


# --- guardrails found broken by an API smoke test, 8 Sep --------------------


def _seeded_store(tmp_path):
    """Small store with drop incidents only, so 'unrelated query' is meaningful."""
    from handleguard.db.store import IncidentStore
    from handleguard.types import BehaviourEvent, Incident, RiskScore

    store = IncidentStore(tmp_path / "guard.db")
    store.init()
    for i in range(3):
        store.add(
            Incident(
                id=f"SEED-{i:04d}",
                behaviour_id="B01",
                name="drop",
                video_id="v",
                camera="c",
                session="s",
                start_t=float(i),
                end_t=float(i) + 1.0,
                risk=RiskScore(score=80.0, band="critical", confidence=0.9),
                explanation="seeded",
                sop=[],
                clip_path=None,
                thumb_path=None,
                track_ids=[1],
                evidence={},
            )
        )
    return store


def test_unrelated_query_says_no_match_instead_of_dumping_everything(tmp_path):
    """Regression: an unrecognised question used to fall through with no filters
    and return the whole table, which reads as a confident answer to a question
    the system did not understand."""
    from handleguard.assistant.templates import NO_MATCHING_INCIDENTS, answer_question

    result = answer_question("show me forklift collisions in bay 9", _seeded_store(tmp_path))
    assert result.answer == NO_MATCHING_INCIDENTS
    assert result.incident_ids == []


def test_damage_question_states_damage_is_unconfirmed(tmp_path):
    """Regression: a damage question used to return a bare list of drops, which a
    reader can take as confirmation that damage occurred."""
    from handleguard.assistant.templates import answer_question

    result = answer_question("did the carton get damaged", _seeded_store(tmp_path))
    assert "cannot be confirmed" in result.answer.lower()
    assert "inspect" in result.answer.lower()


def test_recognised_query_still_returns_incidents(tmp_path):
    from handleguard.assistant.templates import answer_question

    result = answer_question("show me high risk drops", _seeded_store(tmp_path))
    assert result.incident_ids
    assert "SEED-" in result.answer
