from __future__ import annotations

import numpy as np

from handleguard.tracking import NullTracker, Tracker
from handleguard.types import Detection, Frame


def _frame(index: int) -> Frame:
    return Frame(index=index, t=index / 8, image=np.zeros((100, 100, 3), dtype=np.uint8), w=100, h=100)


def test_tracker_keeps_id_for_smooth_motion():
    tracker = Tracker(min_iou=0.2)
    seen = []
    for i in range(80):
        det = Detection("carton", "product", 0.9, (10 + i * 0.2, 10, 50 + i * 0.2, 50))
        tracks = tracker.update([det], _frame(i))
        seen.append(tracks[0].id)

    assert set(seen) == {1}


def test_null_tracker_assigns_fresh_id_every_frame():
    tracker = NullTracker()
    first = tracker.update([Detection("carton", "product", 0.9, (10, 10, 50, 50))], _frame(0))[0]
    second = tracker.update([Detection("carton", "product", 0.9, (10, 10, 50, 50))], _frame(1))[0]

    assert first.id != second.id
