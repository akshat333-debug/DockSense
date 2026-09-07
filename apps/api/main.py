"""FastAPI surface for DockSense incidents."""

from __future__ import annotations

from dataclasses import asdict
import os
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from handleguard.db import IncidentStore
from handleguard.db.store import VALID_REVIEW_STATUSES
from handleguard.types import Incident

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = ROOT / "data" / "processed" / "incidents.db"
DEFAULT_CLIP_DIR = ROOT / "data" / "clips"


class ReviewUpdate(BaseModel):
    review_status: str
    review_note: str = ""


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    answer: str
    incident_ids: list[str] = Field(default_factory=list)


def create_app(
    *,
    db_path: str | Path | None = None,
    clip_dir: str | Path | None = None,
) -> FastAPI:
    db_path = Path(db_path or os.getenv("DOCKSENSE_DB_PATH", DEFAULT_DB_PATH))
    clip_dir = Path(clip_dir or os.getenv("DOCKSENSE_CLIP_DIR", DEFAULT_CLIP_DIR))
    store = IncidentStore(db_path)
    app = FastAPI(title="DockSense API", version="0.1.0")

    def get_store() -> IncidentStore:
        store.init()
        return store

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/incidents")
    def list_incidents(
        behaviour_id: str | None = None,
        name: str | None = None,
        min_risk: float | None = Query(default=None, ge=0, le=100),
        band: str | None = None,
        review_status: str | None = None,
        zone: str | None = None,
        limit: int = Query(default=100, ge=1, le=500),
        store: IncidentStore = Depends(get_store),
    ) -> dict[str, Any]:
        rows = store.query(
            behaviour_id=behaviour_id,
            name=name,
            min_risk=min_risk,
            band=band,
            review_status=review_status,
            zone=zone,
            limit=limit,
        )
        return {"count": len(rows), "items": [_incident_payload(row) for row in rows]}

    @app.get("/incidents/{incident_id}")
    def get_incident(incident_id: str, store: IncidentStore = Depends(get_store)) -> dict[str, Any]:
        incident = store.get(incident_id)
        if incident is None:
            raise HTTPException(status_code=404, detail="incident not found")
        return _incident_payload(incident)

    @app.patch("/incidents/{incident_id}/review")
    def update_review(
        incident_id: str,
        update: ReviewUpdate,
        store: IncidentStore = Depends(get_store),
    ) -> dict[str, Any]:
        if update.review_status not in VALID_REVIEW_STATUSES:
            raise HTTPException(status_code=422, detail="invalid review status")
        incident = store.update_review(
            incident_id,
            status=update.review_status,
            note=update.review_note,
        )
        if incident is None:
            raise HTTPException(status_code=404, detail="incident not found")
        return _incident_payload(incident)

    @app.get("/stats")
    def stats(store: IncidentStore = Depends(get_store)) -> dict[str, Any]:
        return {
            **store.stats(),
            "counts_by_behaviour": store.counts_by_behaviour(),
        }

    @app.get("/clips/{file_path:path}")
    def clip(file_path: str) -> FileResponse:
        base = clip_dir.resolve()
        candidate = (base / file_path).resolve()
        if not _is_relative_to(candidate, base) or not candidate.is_file():
            raise HTTPException(status_code=404, detail="clip not found")
        return FileResponse(candidate)

    @app.post("/chat", response_model=ChatResponse)
    def chat(req: ChatRequest, store: IncidentStore = Depends(get_store)) -> ChatResponse:
        return _answer_question(req.question, store)

    return app


app = create_app()


def _incident_payload(incident: Incident) -> dict[str, Any]:
    return asdict(incident)


def _answer_question(question: str, store: IncidentStore) -> ChatResponse:
    q = question.lower()
    if _asks_for_identity(q):
        return ChatResponse(
            answer=(
                "I cannot identify, rank, or describe workers. I can summarize "
                "observed product-handling incidents with incident IDs and timestamps."
            ),
            incident_ids=[],
        )

    kwargs: dict[str, Any] = {"limit": 10}
    for name in ("drop", "throw", "drag", "zone_violation"):
        if name.replace("_", " ") in q or name in q:
            kwargs["name"] = name
            break
    if "critical" in q:
        kwargs["band"] = "critical"
    elif "high" in q:
        kwargs["min_risk"] = 50.0

    rows = store.query(**kwargs)
    if not rows:
        return ChatResponse(answer="No matching incidents were found.", incident_ids=[])

    lines = [
        (
            f"{row.id} at {row.start_t:.2f}s: observed potential "
            f"{row.name.replace('_', ' ')}; risk {row.risk.band} "
            f"({row.risk.score:.1f}/100), confidence {row.risk.confidence:.2f}."
        )
        for row in rows[:5]
    ]
    if len(rows) > 5:
        lines.append(f"{len(rows) - 5} additional matching incidents were omitted from this short answer.")
    return ChatResponse(answer="\n".join(lines), incident_ids=[row.id for row in rows[:5]])


def _asks_for_identity(q: str) -> bool:
    identity_terms = ("who", "name", "identify", "person", "worker", "employee", "operator")
    return any(term in q for term in identity_terms)


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True
