#!/usr/bin/env python3
"""Seed deterministic demo incidents.

These are explicitly synthetic placeholders for UI/API work. They are not
model outputs and must not be used as evaluation numbers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from handleguard.db import IncidentStore
from handleguard.types import Incident, RiskScore


BEHAVIOURS = [
    ("B01", "drop", "loading_bay"),
    ("B02", "throw", "staging"),
    ("B03", "drag", "staging"),
    ("B07", "zone_violation", "walkway"),
]


def seeded_incidents(n: int = 40) -> list[Incident]:
    created_at = datetime.now(timezone.utc).isoformat()
    out: list[Incident] = []
    for i in range(n):
        behaviour_id, name, zone = BEHAVIOURS[i % len(BEHAVIOURS)]
        score = 25 + ((i * 13) % 70)
        band = _band(score)
        confidence = 0.55 + ((i * 7) % 40) / 100.0
        start_t = float(8 + i * 11)
        out.append(
            Incident(
                id=f"SEED-{i + 1:04d}",
                behaviour_id=behaviour_id,
                name=name,
                video_id="seeded_demo_video",
                session="seeded",
                camera="demo_cam_1",
                start_t=start_t,
                end_t=start_t + 2.5,
                risk=RiskScore(
                    score=float(score),
                    band=band,
                    confidence=round(min(confidence, 0.98), 2),
                    components={"behaviour_severity": score / 100.0},
                    weights_used={"behaviour_severity": 1.0},
                ),
                explanation=(
                    "Seeded placeholder incident for UI development; not a "
                    "model-generated or measured event."
                ),
                sop=[f"Seeded SOP placeholder for {name}."],
                clip_path=None,
                thumb_path=None,
                track_ids=(1000 + i,),
                zone=zone,
                evidence={"seeded": True, "sequence": i + 1},
                created_at=created_at,
            )
        )
    return out


def seed(path: str | Path = ROOT / "data" / "processed" / "incidents.db", *, n: int = 40) -> None:
    store = IncidentStore(path)
    store.init()
    for incident in seeded_incidents(n):
        store.add(incident)


def _band(score: float) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "processed" / "incidents.db"
    seed(path)
    print(f"seeded 40 placeholder incidents into {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
