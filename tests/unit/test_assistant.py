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
