"""Ablation flags must actually change the pipeline.

The innovation claim is that temporal reasoning beats frame-only rules. A flag
that silently does nothing would make the comparison table meaningless while
still looking convincing, so each switch is asserted to have a real effect.

Detections are injected deterministically: the flags are what is under test, not
the detector.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from handleguard.pipeline import PipelineFlags, run
from handleguard.tracking.tracker import Tracker
from handleguard.types import Detection, Frame

TMP = Path("data/test_tmp")


class FallingBoxDetector:
    """One carton accelerating downward, then stopping at the floor."""

    def __call__(self, frame: Frame) -> list[Detection]:
        y = min(100.0 + frame.index * 28.0, 520.0)
        return [Detection(cls="carton", role="product", conf=0.92, xyxy=(560.0, y, 640.0, y + 80.0))]


def _video(name: str) -> Path:
    path = TMP / name
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 8.0, (1280, 720))
    assert writer.isOpened()
    try:
        for _ in range(32):
            writer.write(np.zeros((720, 1280, 3), dtype=np.uint8))
    finally:
        writer.release()
    return path


def _run(flags: PipelineFlags, video: Path):
    return run(
        video,
        detector=FallingBoxDetector(),
        tracker=Tracker(backend="iou", min_iou=0.0) if flags.use_tracking else None,
        flags=flags,
        write_clips=False,
        video_id="ablation",
        max_frames=24,
    )


def test_flag_labels_name_the_disabled_mechanism():
    assert PipelineFlags().label() == "baseline"
    assert PipelineFlags(use_tracking=False).label() == "no_tracking"


def test_from_config_reads_the_ablation_block():
    flags = PipelineFlags.from_config({"ablation": {"use_tracking": False, "bogus_key": True}})
    assert flags.use_tracking is False
    assert flags.use_smoothing is True  # untouched keys keep their default


def test_baseline_detects_the_drop():
    incidents = _run(PipelineFlags(), _video("abl_baseline.mp4"))
    assert [i.behaviour_id for i in incidents] == ["B01"]


def test_disabling_tracking_loses_the_event():
    """Without persistent ids nothing temporal can accumulate, so the drop is lost.

    This is the row that carries the ablation table: it is the difference between
    'we detect sequences' and 'we detect frames'.
    """
    incidents = _run(PipelineFlags(use_tracking=False), _video("abl_notrack.mp4"))
    assert incidents == []


def test_disabling_contextual_risk_changes_the_score():
    video = _video("abl_risk.mp4")
    full = _run(PipelineFlags(), video)
    flat = _run(PipelineFlags(use_contextual_risk=False), video)
    assert full and flat
    # Same event detected either way; only the scoring model differs.
    assert full[0].behaviour_id == flat[0].behaviour_id == "B01"
    assert flat[0].risk.components.keys() == {"behaviour_severity"}
    assert len(full[0].risk.components) > 1
    assert full[0].risk.score != flat[0].risk.score
