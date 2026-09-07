from __future__ import annotations

import numpy as np

from handleguard.features.compute import FeatureExtractor
from handleguard.types import Frame
from tests.fixtures.synth import synth_track


def frame(index: int, t: float) -> Frame:
    return Frame(index=index, t=t, image=np.zeros((720, 1280, 3), dtype=np.uint8), w=1280, h=720)


def test_feature_extractor_normalizes_motion_and_zone():
    extractor = FeatureExtractor(camera="demo_cam_1", window_frames=3)
    tr = synth_track(xyxy=(588.0, 360.0, 668.0, 440.0))
    first = extractor.update([tr], frame(0, 0.0))[1]

    tr.xyxy = (588.0, 440.0, 668.0, 520.0)
    second = extractor.update([tr], frame(1, 0.5))[1]

    assert first.vy == 0.0
    assert round(second.vy, 2) == 2.0
    assert second.ay > 0
    assert second.horizontal_ratio == 0.0
    assert second.zone == "walkway"
    assert round(second.floor_gap, 2) == 1.24


def test_feature_extractor_support_and_held_flags():
    extractor = FeatureExtractor(camera="demo_cam_1")
    product = synth_track(track_id=1, xyxy=(100.0, 100.0, 180.0, 180.0))
    support = synth_track(track_id=2, role="support", cls="pallet", xyxy=(90.0, 180.0, 200.0, 240.0))
    actor = synth_track(track_id=3, role="actor", cls="person", xyxy=(130.0, 80.0, 230.0, 300.0))

    feats = extractor.update([product, support, actor], frame(0, 0.0))

    assert feats[1].supported_by == (2,)
    assert feats[1].held_by_person is True
