"""SQLite incident persistence.

One table stores queryable incident columns plus the full incident as JSON.
Keeping the full dataclass payload intact makes the assistant/API layer stable
while allowing simple dashboard filters without an ORM.
"""

from __future__ import annotations

from dataclasses import asdict
import json
import sqlite3
from pathlib import Path
from typing import Any

from handleguard.types import Incident, RiskScore


class IncidentStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def init(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS incidents (
                    id TEXT PRIMARY KEY,
                    behaviour_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    video_id TEXT NOT NULL,
                    session TEXT NOT NULL,
                    camera TEXT NOT NULL,
                    start_t REAL NOT NULL,
                    end_t REAL NOT NULL,
                    risk_score REAL NOT NULL,
                    risk_band TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    zone TEXT,
                    review_status TEXT NOT NULL,
                    created_at TEXT,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_behaviour ON incidents(behaviour_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_risk ON incidents(risk_score)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_band ON incidents(risk_band)")

    def add(self, incident: Incident) -> None:
        payload = json.dumps(_incident_to_payload(incident), sort_keys=True)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO incidents (
                    id, behaviour_id, name, video_id, session, camera, start_t, end_t,
                    risk_score, risk_band, confidence, zone, review_status, created_at,
                    payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident.id,
                    incident.behaviour_id,
                    incident.name,
                    incident.video_id,
                    incident.session,
                    incident.camera,
                    incident.start_t,
                    incident.end_t,
                    incident.risk.score,
                    incident.risk.band,
                    incident.risk.confidence,
                    incident.zone,
                    incident.review_status,
                    incident.created_at,
                    payload,
                ),
            )

    def get(self, incident_id: str) -> Incident | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM incidents WHERE id = ?",
                (incident_id,),
            ).fetchone()
        return _incident_from_payload(json.loads(row["payload_json"])) if row else None

    def query(
        self,
        *,
        behaviour_id: str | None = None,
        name: str | None = None,
        min_risk: float | None = None,
        band: str | None = None,
        review_status: str | None = None,
        zone: str | None = None,
        limit: int = 100,
    ) -> list[Incident]:
        clauses: list[str] = []
        params: list[Any] = []
        if behaviour_id is not None:
            clauses.append("behaviour_id = ?")
            params.append(behaviour_id)
        if name is not None:
            clauses.append("name = ?")
            params.append(name)
        if min_risk is not None:
            clauses.append("risk_score >= ?")
            params.append(float(min_risk))
        if band is not None:
            clauses.append("risk_band = ?")
            params.append(band)
        if review_status is not None:
            clauses.append("review_status = ?")
            params.append(review_status)
        if zone is not None:
            clauses.append("zone = ?")
            params.append(zone)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(int(limit))
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT payload_json FROM incidents
                {where}
                ORDER BY risk_score DESC, start_t ASC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [_incident_from_payload(json.loads(row["payload_json"])) for row in rows]

    def stats(self) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    AVG(risk_score) AS avg_risk,
                    MAX(risk_score) AS max_risk,
                    AVG(confidence) AS avg_confidence
                FROM incidents
                """
            ).fetchone()
        return {
            "total": int(row["total"] or 0),
            "avg_risk": float(row["avg_risk"] or 0.0),
            "max_risk": float(row["max_risk"] or 0.0),
            "avg_confidence": float(row["avg_confidence"] or 0.0),
        }

    def counts_by_behaviour(self) -> dict[str, int]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT behaviour_id, COUNT(*) AS n FROM incidents GROUP BY behaviour_id ORDER BY behaviour_id"
            ).fetchall()
        return {str(row["behaviour_id"]): int(row["n"]) for row in rows}

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn


def _incident_to_payload(incident: Incident) -> dict[str, Any]:
    return asdict(incident)


def _incident_from_payload(payload: dict[str, Any]) -> Incident:
    risk_payload = dict(payload["risk"])
    payload = dict(payload)
    payload["risk"] = RiskScore(
        score=float(risk_payload["score"]),
        band=str(risk_payload["band"]),
        confidence=float(risk_payload["confidence"]),
        components=dict(risk_payload.get("components", {})),
        weights_used=dict(risk_payload.get("weights_used", {})),
    )
    payload["track_ids"] = tuple(payload.get("track_ids", ()))
    return Incident(**payload)
