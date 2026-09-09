"""Privacy redaction of stored evidence.

The Responsible AI claim is that identifying detail is reduced in retained
clips. These tests hold that claim to the code, including the two mistakes that
are easy to make here: blurring in the wrong coordinate space, and blurring the
whole person instead of the head.
"""

from __future__ import annotations

import numpy as np

from handleguard.privacy import blur_person_regions, blur_regions


def _frame(h=240, w=320):
    rng = np.random.default_rng(0)
    return (rng.random((h, w, 3)) * 255).astype("uint8")


def test_blur_does_not_mutate_the_input_frame():
    f = _frame()
    before = f.copy()
    blur_regions(f, [(10, 10, 100, 100)])
    assert np.array_equal(f, before)


def test_head_is_blurred_and_body_is_preserved():
    """Body must stay legible — a reviewer still has to judge the handling."""
    f = _frame()
    box = (60, 20, 160, 220)  # 200px tall person
    out = blur_person_regions(f, [box], head_fraction=0.25)

    head = (slice(25, 60), slice(70, 150))     # inside top 25%
    body = (slice(140, 210), slice(70, 150))   # well below it
    assert not np.array_equal(f[head], out[head]), "head region should be blurred"
    assert np.array_equal(f[body], out[body]), "body region must be untouched"


def test_boxes_outside_the_frame_are_clipped_not_crashed():
    f = _frame()
    out = blur_person_regions(f, [(-50, -50, 40, 40), (300, 200, 999, 999)])
    assert out.shape == f.shape


def test_degenerate_boxes_are_skipped():
    f = _frame()
    out = blur_person_regions(f, [(10, 10, 10, 10), (5, 5, 6, 6)])
    assert out.shape == f.shape


def test_no_boxes_leaves_frame_unchanged():
    f = _frame()
    assert np.array_equal(blur_person_regions(f, []), f)


def test_time_matching_reuses_nearest_sample_and_drops_stale_ones():
    """Inference runs slower than the source video, so most stored frames fall
    between samples; beyond the tolerance we must blur nothing rather than smear
    a stale box across the wrong part of the frame."""
    from handleguard.incidents.media import _boxes_at

    samples = [(1.0, [(0.1, 0.1, 0.2, 0.2)]), (2.0, [(0.5, 0.5, 0.6, 0.6)])]
    assert _boxes_at(samples, 1.05) == samples[0][1]
    assert _boxes_at(samples, 1.95) == samples[1][1]
    assert _boxes_at(samples, 50.0) == []
    assert _boxes_at([], 1.0) == []


def test_blur_reaches_the_stored_clip(tmp_path):
    """End-to-end: the pixels written to disk are actually redacted."""
    import cv2

    from handleguard.incidents.media import write_evidence_assets
    from handleguard.types import BehaviourEvent

    src = tmp_path / "src.mp4"
    w = cv2.VideoWriter(str(src), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (320, 240))
    rng = np.random.default_rng(1)
    for _ in range(30):
        w.write((rng.random((240, 320, 3)) * 255).astype("uint8"))
    w.release()

    event = BehaviourEvent(
        behaviour_id="B01", name="drop", track_ids=(1,),
        start_frame=10, end_frame=15, start_t=1.0, end_t=1.5,
        severity=0.8, confidence=0.9, evidence={}, zone=None,
    )
    common = dict(output_dir=tmp_path, incident_id="INC-1", pre_seconds=0.2, post_seconds=0.2)
    boxes = [(t / 10.0, [(0.2, 0.1, 0.8, 0.9)]) for t in range(30)]

    plain = write_evidence_assets(src, event, **common, blur_faces=False)
    redacted = write_evidence_assets(
        src, event, **{**common, "incident_id": "INC-2"},
        person_boxes=boxes, blur_faces=True,
    )
    assert plain.clip_path and redacted.clip_path

    def first_frame(name):
        cap = cv2.VideoCapture(str(tmp_path / name))
        ok, fr = cap.read()
        cap.release()
        assert ok
        return fr

    a, b = first_frame(plain.clip_path), first_frame(redacted.clip_path)
    # Blurring reduces local variance; that is the signal we assert on.
    head = (slice(30, 60), slice(80, 240))
    assert b[head].var() < a[head].var(), "stored clip head region was not blurred"
