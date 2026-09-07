"""Reproducible comparisons of previously generated event predictions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from handleguard.evaluation.metrics import evaluate_events, labels_from_csv


def compare_predictions(manifest_path: str | Path) -> dict:
    """Evaluate every run on one ground truth; paths are relative to the manifest."""
    manifest_path = Path(manifest_path).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dataset = manifest.get("dataset")
    runs = manifest.get("runs")
    baseline = manifest.get("baseline")
    if not isinstance(dataset, str) or not dataset.strip():
        raise ValueError("dataset must be an explicit, nonempty provenance label")
    if not isinstance(runs, dict) or len(runs) < 2 or baseline not in runs:
        raise ValueError("runs must contain the named baseline and at least one variant")
    if any(not name.strip() or not isinstance(run, dict) for name, run in runs.items()):
        raise ValueError("each run needs a nonempty name and an object specification")

    def resolve(value: str) -> Path:
        return (manifest_path.parent / value).resolve()

    gt_path = resolve(manifest["ground_truth"])
    gt = labels_from_csv(gt_path)
    if not gt:
        raise ValueError("ground truth must contain events for a meaningful comparison")
    threshold = manifest.get("iou_threshold", 0.5)
    results = {}
    for name, run in runs.items():
        if not isinstance(run.get("settings"), dict):
            raise ValueError(f"run {name!r} must declare its settings")
        path = resolve(run["predictions_csv"])
        results[name] = {
            "settings": run["settings"],
            "predictions": _source(path),
            **evaluate_events(gt, labels_from_csv(path), iou_threshold=threshold).to_dict(),
        }
    reference = results[baseline]["micro"]
    for row in results.values():
        row["delta_from_baseline"] = {
            metric: round(row["micro"][metric] - reference[metric], 4)
            for metric in ("precision", "recall", "f1")
        }
    return {
        "dataset": dataset,
        "baseline": baseline,
        "ground_truth": _source(gt_path),
        "iou_threshold": threshold,
        "limitations": [
            "Settings are declared by the manifest; this tool evaluates saved predictions and does not execute pipeline variants.",
            "Include every evaluated video, including negative clips, in each prediction export. Missing exports cannot be distinguished from no detections.",
            "Event F1 does not measure risk ranking or calibration; contextual risk requires separate risk labels and metrics.",
        ],
        "runs": results,
    }


def markdown_table(report: dict) -> str:
    lines = [
        f"Dataset: {_cell(report['dataset'])}",
        "",
        "| Run | GT | Predictions | Precision | Recall | F1 | Delta F1 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, row in report["runs"].items():
        m = row["micro"]
        delta = row["delta_from_baseline"]["f1"]
        lines.append(
            f"| {_cell(name)} | {m['n_gt']} | {m['n_pred']} | {m['precision']:.4f} | "
            f"{m['recall']:.4f} | {m['f1']:.4f} | {delta:+.4f} |"
        )
    lines.extend(["", *report["limitations"], ""])
    return "\n".join(lines)


def _source(path: Path) -> dict:
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").replace("\r", " ")
