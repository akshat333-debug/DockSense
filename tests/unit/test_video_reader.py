from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from handleguard.video.reader import iter_frames

ROOT = Path(__file__).resolve().parents[2]
MEDIA = ROOT / "data" / "test_tmp"


def _write_video(path: Path, *, fps: int = 30, seconds: float = 2.0, size=(640, 360)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, size)
    assert writer.isOpened(), "test setup could not create video"

    n = int(fps * seconds)
    for i in range(n):
        frame = np.zeros((size[1], size[0], 3), dtype=np.uint8)
        frame[:, :, 0] = i % 255
        writer.write(frame)
    writer.release()


def test_iter_frames_samples_near_target_fps_and_time_is_monotonic():
    path = MEDIA / "reader_drop.mp4"
    _write_video(path, fps=30, seconds=4.0)

    frames = list(iter_frames(path, inference_fps=8))

    assert len(frames) == pytest.approx(4.0 * 8, abs=1)
    assert [f.index for f in frames] == list(range(len(frames)))
    assert all(a.t < b.t for a, b in zip(frames, frames[1:]))
    assert frames[0].t == pytest.approx(0.0)


def test_iter_frames_downscales_without_upscaling():
    path = MEDIA / "reader_wide.mp4"
    _write_video(path, fps=10, seconds=0.5, size=(1920, 1080))

    first = next(iter_frames(path, inference_fps=5, max_res=(1280, 720)))

    assert (first.w, first.h) == (1280, 720)


def test_iter_frames_keeps_small_frames_at_source_resolution():
    path = MEDIA / "reader_small.mp4"
    _write_video(path, fps=10, seconds=0.5, size=(320, 180))

    first = next(iter_frames(path, inference_fps=5, max_res=(1280, 720)))

    assert (first.w, first.h) == (320, 180)


def test_iter_frames_rejects_invalid_inputs():
    path = MEDIA / "reader_clip.mp4"
    _write_video(path)

    with pytest.raises(FileNotFoundError):
        list(iter_frames(MEDIA / "missing.mp4"))
    with pytest.raises(ValueError, match="inference_fps"):
        list(iter_frames(path, inference_fps=0))
    with pytest.raises(ValueError, match="max_res"):
        list(iter_frames(path, max_res=(0, 720)))
