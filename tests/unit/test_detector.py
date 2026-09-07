from __future__ import annotations

import numpy as np

from handleguard.perception.detector import YoloWorldDetector
from handleguard.types import Frame


CFG = {
    "detector": {
        "model": "yolov8s-worldv2.pt",
        "conf_threshold": 0.31,
        "iou_threshold": 0.42,
        "imgsz": 320,
    },
    "classes": {
        "person": {"prompt": "person", "role": "actor"},
        "carton": {"prompt": "cardboard box", "role": "product"},
    },
}


class FakeBox:
    def __init__(self, cls, conf, xyxy):
        self.cls = [cls]
        self.conf = [conf]
        self.xyxy = [xyxy]


class FakeResult:
    def __init__(self, boxes):
        self.boxes = boxes


class FakeModel:
    def __init__(self, fail_first_predict=False):
        self.classes = None
        self.calls = []
        self.fail_first_predict = fail_first_predict

    def set_classes(self, classes):
        self.classes = classes

    def predict(self, image, **kwargs):
        self.calls.append(kwargs)
        if self.fail_first_predict and len(self.calls) == 1:
            raise RuntimeError("MPS unavailable")
        return [FakeResult([FakeBox(1, 0.88, (10, 20, 110, 160))])]


def _frame():
    image = np.zeros((720, 1280, 3), dtype=np.uint8)
    return Frame(index=0, t=0.0, image=image, w=1280, h=720)


def test_detector_sets_configured_prompts_and_maps_roles():
    model = FakeModel()

    detector = YoloWorldDetector(
        cfg=CFG,
        model_factory=lambda _: model,
    )
    detections = detector(_frame())

    assert model.classes == ["person", "cardboard box"]
    assert model.calls[0]["conf"] == 0.31
    assert model.calls[0]["iou"] == 0.42
    assert model.calls[0]["imgsz"] == 320
    assert detections[0].cls == "carton"
    assert detections[0].role == "product"
    assert detections[0].conf == 0.88
    assert detections[0].xyxy == (10.0, 20.0, 110.0, 160.0)


def test_detector_falls_back_to_cpu_when_primary_device_fails():
    model = FakeModel(fail_first_predict=True)

    detector = YoloWorldDetector(
        cfg=CFG,
        device="mps",
        fallback_device="cpu",
        model_factory=lambda _: model,
    )
    detections = detector(_frame())

    assert [call["device"] for call in model.calls] == ["mps", "cpu"]
    assert detector.device == "cpu"
    assert len(detections) == 1
