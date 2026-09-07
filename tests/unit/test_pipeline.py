from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from handleguard.db.store import IncidentStore
from handleguard.pipeline import run
from handleguard.tracking.tracker import Tracker
from handleguard.types import Detection, Frame


class FallingBoxDetector:
    def __call__(self, frame: Frame) -> list[Detection]:
        y = min(100.0 + frame.index * 28.0, 520.0)
        return [Detection(cls="carton", role="product", conf=0.92, xyxy=(560.0, y, 640.0, y + 80.0))]


def test_pipeline_writes_synthetic_drop_incident_to_store():
    video_path = Path("data/test_tmp/pipeline_drop.mp4")
    db_path = Path("data/test_tmp/pipeline_incidents.db")
    video_path.parent.mkdir(parents=True, exist_ok=True)
    _write_blank_video(video_path)

    store = IncidentStore(db_path)
    incidents = run(
        video_path,
        detector=FallingBoxDetector(),
        tracker=Tracker(backend="iou", min_iou=0.0),
        store=store,
        video_id="pipeline-drop",
        max_frames=24,
    )

    assert len(incidents) == 1
    assert incidents[0].behaviour_id == "B01"
    assert incidents[0].risk.score > 0
    assert store.stats()["total"] == 1
    assert store.get(incidents[0].id).explanation == incidents[0].explanation


def _write_blank_video(path: Path) -> None:
    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        8.0,
        (1280, 720),
    )
    assert writer.isOpened()
    try:
        for _ in range(32):
            writer.write(np.zeros((720, 1280, 3), dtype=np.uint8))
    finally:
        writer.release()
