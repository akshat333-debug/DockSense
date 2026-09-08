"""FastAPI surface for DockSense incidents."""

from __future__ import annotations

from dataclasses import asdict
import os
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from handleguard.assistant import answer_question
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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        allow_credentials=False,
        allow_methods=["GET", "PATCH", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

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
        answer = answer_question(req.question, store)
        return ChatResponse(answer=answer.answer, incident_ids=answer.incident_ids)

    return app


def _incident_payload(incident: Incident) -> dict[str, Any]:
    return asdict(incident)


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


def _allowed_origins() -> list[str]:
    raw = os.getenv("DOCKSENSE_CORS_ORIGINS")
    if raw:
        return [item.strip() for item in raw.split(",") if item.strip()]
    return [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
    ]


def mount_web_console(app: FastAPI) -> bool:
    """Serve the built React console from the API itself.

    The demo must run offline from one command. Serving `dist/` here means no
    second process, no node, no `npm install`, and no CORS hop — the console is
    same-origin with the API it calls. Mounted last so it never shadows an API
    route.

    Returns False when the bundle is absent, so the caller can say so plainly
    rather than the demo silently coming up with no UI.
    """
    dist = Path(__file__).resolve().parent.parent / "web" / "dist"
    if not (dist / "index.html").is_file():
        return False
    app.mount("/", StaticFiles(directory=str(dist), html=True), name="web")
    return True


app = create_app()
WEB_CONSOLE_MOUNTED = mount_web_console(app)
