"""End-to-end offline inference pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from handleguard import config
from handleguard.behaviours.base import FrameContext, TrackHistory
from handleguard.behaviours.registry import build_all
from handleguard.events.dedup import EventDeduper
from handleguard.features.compute import FeatureExtractor
from handleguard.incidents.builder import build_incident
from handleguard.tracking.tracker import Tracker
from handleguard.types import Detection, Frame, Incident, Track
from handleguard.video.reader import iter_frames


class DetectorLike(Protocol):
    def __call__(self, frame: Frame) -> list[Detection]:
        ...


class TrackerLike(Protocol):
    def update(self, dets: list[Detection], frame: Frame) -> list[Track]:
        ...


def run(
    video_path: str | Path,
    *,
    detector: DetectorLike | None = None,
    tracker: TrackerLike | None = None,
    feature_extractor: FeatureExtractor | None = None,
    detectors: list[Any] | None = None,
    store: Any | None = None,
    video_id: str | None = None,
    session: str = "synthetic",
    camera: str = "demo_cam_1",
    max_frames: int | None = None,
) -> list[Incident]:
    behaviour_cfg = config.behaviours()
    video_cfg = behaviour_cfg.get("video", {})
    inference_fps = float(video_cfg.get("inference_fps", 8))
    max_res = tuple(video_cfg.get("max_resolution", (1280, 720)))

    if detector is None:
        from handleguard.perception.detector import YoloWorldDetector

        detector = YoloWorldDetector()
    tracker = tracker or Tracker(frame_rate=int(round(inference_fps)))
    feature_extractor = feature_extractor or FeatureExtractor(camera=camera)
    detectors = detectors or build_all(behaviour_cfg)

    history = TrackHistory(max_seconds=_history_seconds(behaviour_cfg))
    deduper = EventDeduper(behaviour_cfg)
    prev_t = 0.0
    video_id = video_id or Path(video_path).stem

    if hasattr(tracker, "reset"):
        tracker.reset()
    feature_extractor.reset()
    for behaviour in detectors:
        if hasattr(behaviour, "reset"):
            behaviour.reset()

    for frame in iter_frames(video_path, inference_fps=inference_fps, max_res=(int(max_res[0]), int(max_res[1]))):
        if max_frames is not None and frame.index >= max_frames:
            break
        dets = detector(frame)
        tracks = tracker.update(dets, frame)
        feats = feature_extractor.update(tracks, frame)
        history.push(feats)
        dt = frame.t - prev_t if frame.index else 0.0
        prev_t = frame.t
        ctx = FrameContext(
            frame_index=frame.index,
            t=frame.t,
            dt=dt,
            fw=frame.w,
            fh=frame.h,
            tracks={track.id: track for track in tracks},
            feats=feats,
            history=history,
            zones=config.zones(),
            cfg=behaviour_cfg,
        )
        for behaviour in detectors:
            for event in behaviour.update(ctx):
                deduper.push(event)

    incidents = [
        build_incident(event, video_id=video_id, session=session, camera=camera)
        for event in deduper.flush()
    ]
    if store is not None:
        if hasattr(store, "init"):
            store.init()
        for incident in incidents:
            store.add(incident)
    return incidents


def _history_seconds(cfg: dict[str, Any]) -> float:
    windows = [float(v) for v in cfg.get("dedup", {}).values()]
    windows.extend(
        float(section.get("cooldown_seconds", 0.0))
        for section in cfg.values()
        if isinstance(section, dict) and "cooldown_seconds" in section
    )
    return max(windows + [5.0])
