"""YOLO-World detector adapter.

The rest of DockSense speaks in internal class keys and roles from
``configs/products.yaml``. This module is the translation boundary from
Ultralytics result objects to plain ``Detection`` dataclasses.
"""

from __future__ import annotations

from collections.abc import Callable
import os
from pathlib import Path
from typing import Any

from handleguard import config
from handleguard.types import Detection, Frame

_ROOT = Path(__file__).resolve().parents[2]


class YoloWorldDetector:
    """Open-vocabulary detector with MPS-to-CPU prediction fallback."""

    def __init__(
        self,
        model_path: str | Path | None = None,
        *,
        cfg: dict[str, Any] | None = None,
        device: str = "mps",
        fallback_device: str = "cpu",
        model_factory: Callable[[str], Any] | None = None,
    ) -> None:
        self.cfg = cfg or config.products()
        detector_cfg = self.cfg.get("detector", {})
        self.conf_threshold = float(detector_cfg.get("conf_threshold", 0.25))
        self.iou_threshold = float(detector_cfg.get("iou_threshold", 0.45))
        self.imgsz = int(detector_cfg.get("imgsz", 640))
        self.device = device
        self.fallback_device = fallback_device

        self.class_names = list(self.cfg["classes"].keys())
        self.prompts = [self.cfg["classes"][name]["prompt"] for name in self.class_names]
        self.roles = {
            name: str(self.cfg["classes"][name].get("role", "unknown"))
            for name in self.class_names
        }
        self.predict_dir = _ROOT / "runs" / "detect"
        self.predict_dir.mkdir(parents=True, exist_ok=True)

        resolved_model_path = self._resolve_model_path(model_path, detector_cfg)
        self.model_path = resolved_model_path
        self.model = self._build_model(model_factory)
        _ensure_repo_cache_home()
        self.model.set_classes(self.prompts)

    def __call__(self, frame: Frame) -> list[Detection]:
        results = self._predict(frame.image, self.device)
        return self._parse_results(results)

    def _build_model(self, model_factory: Callable[[str], Any] | None):
        if model_factory is not None:
            return model_factory(str(self.model_path))

        try:
            from ultralytics import YOLOWorld
        except ImportError as exc:
            raise RuntimeError(
                "ultralytics is required for YoloWorldDetector; install requirements.txt"
            ) from exc

        return YOLOWorld(str(self.model_path))

    def _predict(self, image, device: str):
        try:
            return self.model.predict(
                image,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                imgsz=self.imgsz,
                device=device,
                verbose=False,
                save=False,
                project=str(self.predict_dir),
                name="predict",
                exist_ok=True,
            )
        except RuntimeError:
            if device == self.fallback_device:
                raise
            self.device = self.fallback_device
            return self.model.predict(
                image,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                imgsz=self.imgsz,
                device=self.fallback_device,
                verbose=False,
                save=False,
                project=str(self.predict_dir),
                name="predict",
                exist_ok=True,
            )

    def _parse_results(self, results) -> list[Detection]:
        detections: list[Detection] = []
        for result in results or []:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue
            for box in boxes:
                idx = int(_scalar(box.cls))
                if idx < 0 or idx >= len(self.class_names):
                    continue
                cls = self.class_names[idx]
                detections.append(
                    Detection(
                        cls=cls,
                        role=self.roles[cls],
                        conf=float(_scalar(box.conf)),
                        xyxy=_xyxy(box.xyxy),
                    )
                )
        return detections

    @staticmethod
    def _resolve_model_path(
        model_path: str | Path | None,
        detector_cfg: dict[str, Any],
    ) -> Path:
        raw = Path(model_path or detector_cfg.get("model", "yolov8s-worldv2.pt"))
        path = raw if raw.is_absolute() else _ROOT / "models" / raw
        if not path.exists():
            raise FileNotFoundError(f"detector model not found: {path}")
        return path


def _tolist(value):
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "numpy"):
        value = value.numpy()
    if hasattr(value, "tolist"):
        return value.tolist()
    return value


def _scalar(value) -> float:
    value = _tolist(value)
    while isinstance(value, (list, tuple)):
        value = value[0]
    return float(value)


def _xyxy(value) -> tuple[float, float, float, float]:
    values = _tolist(value)
    while values and isinstance(values[0], (list, tuple)):
        values = values[0]
    if len(values) != 4:
        raise ValueError(f"expected xyxy with 4 values, got {values!r}")
    return tuple(float(v) for v in values)


def _ensure_repo_cache_home() -> None:
    """Keep CLIP text-model assets inside the project.

    Ultralytics' YOLO-World calls ``clip.load(...)`` during ``set_classes()``.
    On Windows, CLIP expands ``~/.cache/clip`` through ``USERPROFILE``. The
    default profile cache can be unwritable in the Codex sandbox, so point it at
    a repo-local home unless the caller already supplied one.
    """
    if os.environ.get("HANDLEGUARD_USE_SYSTEM_CACHE") == "1":
        return
    cache_home = Path(os.environ.get("HANDLEGUARD_CACHE_HOME", _ROOT / "models" / ".cache_home"))
    cache_home.mkdir(parents=True, exist_ok=True)
    os.environ["USERPROFILE"] = str(cache_home)
    os.environ["HOME"] = str(cache_home)
