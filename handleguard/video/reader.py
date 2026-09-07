"""Video frame decoding for the inference pipeline.

This is the only place that skips frames. Downstream modules receive a compact
sequence of :class:`handleguard.types.Frame` objects and use ``Frame.t`` as the
single source of time.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import cv2

from handleguard.types import Frame


def iter_frames(
    path: str | Path,
    inference_fps: float = 8,
    max_res: tuple[int, int] = (1280, 720),
) -> Iterator[Frame]:
    """Yield BGR frames sampled at ``inference_fps`` and bounded by ``max_res``.

    Args:
        path: Video file readable by OpenCV.
        inference_fps: Target sampling rate in frames per second.
        max_res: Maximum ``(width, height)``. Frames are downscaled preserving
            aspect ratio and are never upscaled.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        ValueError: If fps or resolution arguments are invalid, or OpenCV cannot
            open the video.
    """
    video_path = Path(path)
    if not video_path.exists():
        raise FileNotFoundError(f"video not found: {video_path}")
    if inference_fps <= 0:
        raise ValueError("inference_fps must be positive")

    max_w, max_h = max_res
    if max_w <= 0 or max_h <= 0:
        raise ValueError("max_res dimensions must be positive")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        cap.release()
        raise ValueError(f"could not open video: {video_path}")

    try:
        source_fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        if source_fps <= 0:
            source_fps = inference_fps

        target_dt = 1.0 / float(inference_fps)
        next_emit_t = 0.0
        decoded_index = 0
        emitted_index = 0
        eps = 1e-9

        while True:
            ok, image = cap.read()
            if not ok:
                break

            t = decoded_index / source_fps
            decoded_index += 1

            if t + eps < next_emit_t:
                continue

            while next_emit_t <= t + eps:
                next_emit_t += target_dt

            image = _resize_to_max(image, max_w, max_h)
            h, w = image.shape[:2]
            yield Frame(
                index=emitted_index,
                t=t,
                image=image,
                w=w,
                h=h,
            )
            emitted_index += 1
    finally:
        cap.release()


def _resize_to_max(image, max_w: int, max_h: int):
    h, w = image.shape[:2]
    scale = min(max_w / w, max_h / h, 1.0)
    if scale >= 1.0:
        return image

    new_w = max(int(round(w * scale)), 1)
    new_h = max(int(round(h * scale)), 1)
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
