from __future__ import annotations

from pathlib import Path

from handleguard.db import IncidentStore
from handleguard.evaluation.metrics import EventLabel, evaluate_events, labels_from_csv, labels_from_incident_db
from handleguard.types import Incident, RiskScore


def test_temporal_iou_matching_reports_counts_and_f1():
    gt = [
        EventLabel("clip-a.mp4", "drop", 1.0, 2.0, "gt-1"),
        EventLabel("clip-a.mp4", "drop", 5.0, 6.0, "gt-2"),
        EventLabel("clip-a.mp4", "throw", 3.0, 4.0, "gt-3"),
    ]
    pred = [
        EventLabel("clip-a.mp4", "drop", 1.1, 2.1, "pred-1"),
        EventLabel("clip-a.mp4", "drop", 8.0, 9.0, "pred-2"),
        EventLabel("clip-a.mp4", "throw", 3.1, 3.9, "pred-3"),
        EventLabel("clip-a.mp4", "drag", 1.0, 2.0, "pred-4"),
    ]

    report = evaluate_events(gt, pred, iou_threshold=0.5)

    drop = report.by_behaviour["drop"]
    assert drop.true_positive == 1
    assert drop.false_positive == 1
    assert drop.false_negative == 1
    assert drop.n_gt == 2
    assert drop.n_pred == 2
    assert drop.precision == 0.5
    assert drop.recall == 0.5
    assert drop.f1 == 0.5

    throw = report.by_behaviour["throw"]
    assert throw.true_positive == 1
    assert throw.mean_temporal_iou == 0.8

    drag = report.by_behaviour["drag"]
    assert drag.n_gt == 0
    assert drag.n_pred == 1
    assert drag.false_positive == 1

    assert report.micro.true_positive == 2
    assert report.micro.false_positive == 2
    assert report.micro.false_negative == 1
    assert report.micro.n_gt == 3
    assert report.micro.n_pred == 4


def test_labels_load_from_csv_and_incident_db():
    csv_path = Path("data/test_tmp/eval_gt.csv")
    db_path = Path("data/test_tmp/eval_pred.db")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.write_text("video,behaviour,t_start,t_end,note\nclip.mp4,drop,1.0,2.0,ok\n")

    store = IncidentStore(db_path)
    store.init()
    store.add(
        Incident(
            id="INC-EVAL",
            behaviour_id="B01",
            name="drop",
            video_id="clip.mp4",
            session="synthetic",
            camera="demo_cam_1",
            start_t=1.1,
            end_t=1.9,
            risk=RiskScore(score=70.0, band="high", confidence=0.9),
            explanation="observed potential drop",
            sop=[],
        )
    )

    gt = labels_from_csv(csv_path)
    pred = labels_from_incident_db(db_path)

    assert gt == [EventLabel("clip.mp4", "drop", 1.0, 2.0, "ok")]
    assert pred == [EventLabel("clip.mp4", "drop", 1.1, 1.9, "INC-EVAL")]
    assert evaluate_events(gt, pred).micro.f1 == 1.0
