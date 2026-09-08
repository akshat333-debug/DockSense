"""Per-stage latency instrumentation."""

from __future__ import annotations

from handleguard.metrics.latency import Timings, _percentile


def test_no_samples_reports_cleanly():
    assert Timings().stats() == []
    assert "no timing samples" in Timings().report()


def test_percentile_uses_nearest_rank_not_interpolation():
    """With the sample counts a short clip yields, interpolating would invent a
    number that sits between two real measurements."""
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert _percentile(values, 0.50) == 3.0
    assert _percentile(values, 0.95) == 5.0
    assert _percentile([], 0.5) == 0.0


def test_records_and_orders_stages_by_pipeline_order():
    t = Timings()
    # deliberately recorded out of order
    for ms in (5.0, 7.0, 9.0):
        t.record("behaviours", ms)
    for ms in (1.0, 2.0):
        t.record("detect", ms)
    stages = [s.stage for s in t.stats()]
    assert stages == ["detect", "behaviours"], "report should read in pipeline order"


def test_stats_summarise_each_stage():
    t = Timings()
    for ms in (10.0, 20.0, 30.0, 40.0):
        t.record("detect", ms)
    (row,) = t.stats()
    assert row.count == 4
    assert row.mean_ms == 25.0
    assert row.max_ms == 40.0
    assert row.total_ms == 100.0


def test_context_manager_measures_elapsed_time():
    t = Timings()
    with t.stage("detect"):
        sum(range(10000))
    assert t.stats()[0].count == 1
    assert t.stats()[0].mean_ms >= 0.0


def test_to_dict_is_serializable_and_reports_fps():
    import json

    t = Timings()
    for ms in (100.0, 100.0):
        t.record("detect", ms)
    payload = t.to_dict()
    json.dumps(payload)
    assert payload["frames"] == 2
    assert payload["fps_end_to_end"] == 10.0  # 2 frames / 0.2 s


def test_pipeline_accepts_timings_and_populates_them():
    """Instrumentation must actually be wired into run(), not just importable."""
    from pathlib import Path

    import cv2
    import numpy as np

    from handleguard.pipeline import run
    from handleguard.tracking.tracker import Tracker
    from handleguard.types import Detection, Frame

    class Falling:
        def __call__(self, frame: Frame) -> list[Detection]:
            y = min(100.0 + frame.index * 28.0, 520.0)
            return [Detection(cls="carton", role="product", conf=0.9, xyxy=(560.0, y, 640.0, y + 80.0))]

    path = Path("data/test_tmp/latency.mp4")
    path.parent.mkdir(parents=True, exist_ok=True)
    w = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 8.0, (1280, 720))
    try:
        for _ in range(24):
            w.write(np.zeros((720, 1280, 3), dtype=np.uint8))
    finally:
        w.release()

    timings = Timings()
    run(path, detector=Falling(), tracker=Tracker(backend="iou", min_iou=0.0),
        write_clips=False, max_frames=16, timings=timings)

    recorded = {s.stage for s in timings.stats()}
    assert {"detect", "track", "features", "behaviours"} <= recorded
