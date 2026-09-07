from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.main import create_app
from scripts.seed_fake_incidents import seed


MEDIA = Path(__file__).resolve().parents[2] / "data" / "test_tmp"


def test_api_lists_gets_stats_and_reviews_incidents():
    db_path = MEDIA / "api_incidents.db"
    seed(db_path, n=8)
    client = TestClient(create_app(db_path=db_path, clip_dir=MEDIA))

    listed = client.get("/incidents", params={"limit": 3})
    assert listed.status_code == 200
    assert listed.json()["count"] == 3

    incident_id = listed.json()["items"][0]["id"]
    one = client.get(f"/incidents/{incident_id}")
    assert one.status_code == 200
    assert one.json()["id"] == incident_id

    stats = client.get("/stats")
    assert stats.status_code == 200
    assert stats.json()["total"] == 8
    assert stats.json()["counts_by_behaviour"]

    reviewed = client.patch(
        f"/incidents/{incident_id}/review",
        json={"review_status": "confirmed", "review_note": "checked"},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["review_status"] == "confirmed"
    assert reviewed.json()["review_note"] == "checked"


def test_api_chat_cites_incidents_and_refuses_identity_requests():
    db_path = MEDIA / "api_chat.db"
    seed(db_path, n=4)
    client = TestClient(create_app(db_path=db_path, clip_dir=MEDIA))

    answer = client.post("/chat", json={"question": "show high risk incidents"}).json()
    assert answer["incident_ids"]
    assert answer["incident_ids"][0] in answer["answer"]
    assert "risk" in answer["answer"]

    refused = client.post("/chat", json={"question": "who was the worker in this incident?"})
    assert refused.status_code == 200
    assert "cannot identify" in refused.json()["answer"]
    assert refused.json()["incident_ids"] == []


def test_api_clip_serving_is_confined_to_clip_directory():
    db_path = MEDIA / "api_clips.db"
    seed(db_path, n=1)
    clip = MEDIA / "sample_clip.txt"
    clip.write_text("clip-bytes")
    client = TestClient(create_app(db_path=db_path, clip_dir=MEDIA))

    ok = client.get("/clips/sample_clip.txt")
    assert ok.status_code == 200
    assert ok.text == "clip-bytes"

    blocked = client.get("/clips/../api_clips.db")
    assert blocked.status_code == 404
