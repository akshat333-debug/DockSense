"""Evidence clip and thumbnail extraction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import cv2

from handleguard.types import BehaviourEvent


@dataclass(frozen=True)
class EvidenceAssets:
    clip_path: str | None
    thumb_path: str | None


def write_evidence_assets(
    video_path: str | Path,
    event: BehaviourEvent,
    *,
    output_dir: str | Path,
    incident_id: str,
    pre_seconds: float = 3.0,
    post_seconds: float = 4.0,
) -> EvidenceAssets:
    """Write a bounded event clip and thumbnail.

    Returned paths are relative filenames intended for API clip serving.
    """
    src = Path(video_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = _safe_stem(incident_id)
    clip_name = f"{stem}.mp4"
    thumb_name = f"{stem}.jpg"
    clip_path = out_dir / clip_name
    thumb_path = out_dir / thumb_name

    cap = cv2.VideoCapture(str(src))
    if not cap.isOpened():
        cap.release()
        return EvidenceAssets(None, None)

    try:
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        if fps <= 0:
            fps = 8.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        if total_frames <= 0 or width <= 0 or height <= 0:
            return EvidenceAssets(None, None)

        start_t = max(event.start_t - pre_seconds, 0.0)
        end_t = min(event.end_t + post_seconds, max((total_frames - 1) / fps, 0.0))
        start_frame = max(int(start_t * fps), 0)
        end_frame = min(max(int(end_t * fps), start_frame), total_frames - 1)

        writer = cv2.VideoWriter(
            str(clip_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (width, height),
        )
        if not writer.isOpened():
            writer.release()
            return EvidenceAssets(None, None)

        thumb_written = False
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        for frame_index in range(start_frame, end_frame + 1):
            ok, frame = cap.read()
            if not ok:
                break
            writer.write(frame)
            if not thumb_written and frame_index >= int(event.start_t * fps):
                cv2.imwrite(str(thumb_path), frame)
                thumb_written = True
        writer.release()

        if not thumb_written:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            ok, frame = cap.read()
            if ok:
                cv2.imwrite(str(thumb_path), frame)

        return EvidenceAssets(
            clip_name if clip_path.exists() and clip_path.stat().st_size > 0 else None,
            thumb_name if thumb_path.exists() and thumb_path.stat().st_size > 0 else None,
        )
    finally:
        cap.release()


def _safe_stem(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._") or "incident"
