from __future__ import annotations

from pathlib import Path

from handleguard.db import IncidentStore
from handleguard.types import Incident, RiskScore
from scripts.seed_fake_incidents import seed

MEDIA = Path(__file__).resolve().parents[2] / "data" / "test_tmp"


def _incident(idx: int, behaviour_id: str, band: str, risk: float) -> Incident:
    return Incident(
        id=f"INC-{idx:04d}",
        behaviour_id=behaviour_id,
        name="drop" if behaviour_id == "B01" else "throw",
        video_id="vid",
        session="S1",
        camera="demo_cam_1",
        start_t=float(idx),
        end_t=float(idx + 1),
        risk=RiskScore(score=risk, band=band, confidence=0.8),
        explanation="observed event",
        sop=["inspect"],
        track_ids=(idx,),
        zone="loading_bay",
        evidence={"x": idx},
        created_at="2026-09-07T00:00:00+00:00",
    )


def test_store_round_trips_and_queries():
    path = MEDIA / "store_roundtrip.db"
    store = IncidentStore(path)
    store.init()
    store.add(_incident(1, "B01", "high", 72))
    store.add(_incident(2, "B02", "critical", 91))
    store.add(_incident(3, "B01", "medium", 40))

    one = store.get("INC-0001")
    assert one is not None
    assert one.track_ids == (1,)
    assert one.risk.score == 72

    assert [i.id for i in store.query(behaviour_id="B01")] == ["INC-0001", "INC-0003"]
    assert [i.id for i in store.query(min_risk=80)] == ["INC-0002"]
    assert [i.id for i in store.query(band="medium")] == ["INC-0003"]
    assert store.counts_by_behaviour() == {"B01": 2, "B02": 1}
    assert store.stats()["total"] == 3


def test_seed_fake_incidents_creates_40_rows():
    path = MEDIA / "seeded.db"
    seed(path, n=40)
    store = IncidentStore(path)

    rows = store.query(limit=100)
    assert len(rows) == 40
    assert all(row.id.startswith("SEED-") for row in rows)
    assert all(row.evidence["seeded"] is True for row in rows)
