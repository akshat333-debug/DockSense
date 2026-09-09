"""Privacy redaction for stored evidence.

The Responsible AI position is that this system analyses *behaviour, not
identity*. Blurring the head region of people in saved clips is the concrete
expression of that: an incident stays reviewable — you can still see the carton
fall and who was near it — while the stored artefact carries less identifying
detail than the raw footage did.

Deliberately **not** face detection. Running a face detector to decide what to
blur would mean building exactly the capability we say we do not have, and it
fails open: an undetected face is an unblurred face. Blurring a fixed upper
fraction of every person box has no such failure mode.

This reduces identifiability. It is not anonymisation — gait, clothing and
context remain. Say the former, never the latter.
"""

from __future__ import annotations

from typing import Iterable, Sequence

import cv2
import numpy as np

BBox = Sequence[float]

# Fraction of a person box, measured from the top, treated as the head region.
HEAD_FRACTION = 0.25
# Odd kernel; larger blurs more. Scaled by region size so it works at any distance.
MIN_KERNEL = 15


def blur_regions(frame: np.ndarray, boxes: Iterable[BBox]) -> np.ndarray:
    """Gaussian-blur each box in `boxes`. Returns a new frame; input untouched."""
    out = frame.copy()
    h, w = out.shape[:2]
    for box in boxes:
        x0, y0, x1, y1 = (int(round(v)) for v in box[:4])
        x0, y0 = max(x0, 0), max(y0, 0)
        x1, y1 = min(x1, w), min(y1, h)
        if x1 - x0 < 2 or y1 - y0 < 2:
            continue
        region = out[y0:y1, x0:x1]
        # Kernel proportional to region size, forced odd, so a distant person is
        # blurred as thoroughly as a near one.
        k = max(MIN_KERNEL, (min(region.shape[:2]) // 2) | 1)
        k = k if k % 2 else k + 1
        out[y0:y1, x0:x1] = cv2.GaussianBlur(region, (k, k), 0)
    return out


def blur_person_regions(
    frame: np.ndarray,
    person_boxes: Iterable[BBox],
    *,
    head_fraction: float = HEAD_FRACTION,
) -> np.ndarray:
    """Blur the upper `head_fraction` of each person box.

    Keeps the body visible so a reviewer can still judge the handling action,
    which is the whole point of retaining the clip.
    """
    heads = []
    for box in person_boxes:
        x0, y0, x1, y1 = (float(v) for v in box[:4])
        height = max(y1 - y0, 0.0)
        heads.append((x0, y0, x1, y0 + height * head_fraction))
    return blur_regions(frame, heads)
