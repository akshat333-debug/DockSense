#!/usr/bin/env python3
"""Evaluate event predictions against temporal ground truth."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from handleguard.evaluation import evaluate_events, labels_from_csv, labels_from_incident_db


def main() -> int:
    args = _parse_args()
    gt = labels_from_csv(args.ground_truth)
    pred = labels_from_csv(args.predictions_csv) if args.predictions_csv else labels_from_incident_db(args.predictions_db)
    report = evaluate_events(gt, pred, iou_threshold=args.iou_threshold)
    payload = {
        "dataset": args.dataset,
        "ground_truth": str(args.ground_truth),
        "predictions": str(args.predictions_csv or args.predictions_db),
        **report.to_dict(),
    }
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n")
    print(text)
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=ROOT / "data" / "synthetic" / "ground_truth.csv",
        help="CSV with video, behaviour, t_start, t_end columns.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--predictions-db", type=Path, help="SQLite incident DB to evaluate.")
    group.add_argument("--predictions-csv", type=Path, help="Prediction CSV with video, behaviour, t_start, t_end columns.")
    parser.add_argument("--iou-threshold", type=float, default=0.5)
    parser.add_argument("--dataset", default="synthetic", help="Report provenance label; do not call S3 unless held out.")
    parser.add_argument("--output", type=Path, help="Optional JSON output path.")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
