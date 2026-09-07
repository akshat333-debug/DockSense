from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from handleguard.incidents.media import write_evidence_assets
from handleguard.types import BehaviourEvent


def test_write_evidence_assets_creates_confined_clip_and_thumbnail():
    video_path = Path("data/test_tmp/media_source.mp4")
    out_dir = Path("data/test_tmp/media_clips")
    video_path.parent.mkdir(parents=True, exist_ok=True)
    _write_video(video_path)

    assets = write_evidence_assets(
        video_path,
        BehaviourEvent(
            behaviour_id="B01",
            name="drop",
            track_ids=(1,),
            start_frame=8,
            end_frame=12,
            start_t=1.0,
            end_t=1.5,
            severity=0.8,
            confidence=0.9,
        ),
        output_dir=out_dir,
        incident_id="INC-test:01",
        pre_seconds=0.25,
        post_seconds=0.25,
    )

    assert assets.clip_path == "INC-test_01.mp4"
    assert assets.thumb_path == "INC-test_01.jpg"
    assert (out_dir / assets.clip_path).stat().st_size > 0
    assert (out_dir / assets.thumb_path).stat().st_size > 0


def _write_video(path: Path) -> None:
    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        8.0,
        (160, 90),
    )
    assert writer.isOpened()
    try:
        for i in range(24):
            frame = np.zeros((90, 160, 3), dtype=np.uint8)
            frame[:, :, 1] = i * 8
            writer.write(frame)
    finally:
        writer.release()
