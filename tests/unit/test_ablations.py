from __future__ import annotations

import json
import subprocess
import sys

import pytest

from handleguard.evaluation.ablations import compare_predictions, markdown_table
from handleguard.evaluation.metrics import EventLabel, evaluate_events


@pytest.fixture
def manifest(tmp_path):
    header = "video,behaviour,t_start,t_end\n"
    event = "clip,drop,1,2\n"
    (tmp_path / "gt.csv").write_text(header + event)
    (tmp_path / "baseline.csv").write_text(header + event)
    (tmp_path / "variant.csv").write_text(header + event + "negative,drop,1,2\n")
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({
        "dataset": "unit-test fixtures",
        "ground_truth": "gt.csv",
        "baseline": "baseline",
        "runs": {
            "baseline": {"predictions_csv": "baseline.csv", "settings": {"use_tracking": True}},
            "no_tracking": {"predictions_csv": "variant.csv", "settings": {"use_tracking": False}},
        },
    }))
    return path


def test_comparison_counts_negative_clip_false_positives_and_deltas(manifest):
    report = compare_predictions(manifest)
    baseline = report["runs"]["baseline"]
    variant = report["runs"]["no_tracking"]
    assert baseline["micro"]["f1"] == 1
    assert variant["micro"]["false_positive"] == 1
    assert variant["micro"]["f1"] == 0.6667
    assert variant["delta_from_baseline"]["f1"] == -0.3333
    assert len(variant["predictions"]["sha256"]) == 64
    assert "-0.3333" in markdown_table(report)


def test_empty_predictions_are_valid(manifest):
    (manifest.parent / "variant.csv").write_text("video,behaviour,t_start,t_end\n")
    variant = compare_predictions(manifest)["runs"]["no_tracking"]
    assert variant["micro"]["false_negative"] == 1
    assert variant["delta_from_baseline"]["f1"] == -1


@pytest.mark.parametrize("change", [
    {"dataset": ""}, {"baseline": "missing"}, {"runs": {}},
])
def test_invalid_manifest_rejected(manifest, change):
    payload = json.loads(manifest.read_text())
    payload.update(change)
    manifest.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        compare_predictions(manifest)


@pytest.mark.parametrize("video,start,end", [("other", 1, 2), ("clip", 3, 4), ("clip", 2, 3)])
def test_zero_threshold_does_not_match_unrelated_or_disjoint_events(video, start, end):
    report = evaluate_events(
        [EventLabel("clip", "drop", 1, 2)],
        [EventLabel(video, "drop", start, end)],
        iou_threshold=0,
    )
    assert report.micro.true_positive == 0
    assert report.micro.false_positive == report.micro.false_negative == 1


def test_cli_writes_reports_and_protects_inputs(manifest):
    output = manifest.parent / "report.json"
    markdown = manifest.parent / "report.md"
    command = [sys.executable, "scripts/compare_ablations.py", str(manifest), "--output"]
    result = subprocess.run(command + [str(output), "--markdown", str(markdown)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(output.read_text())["dataset"] == "unit-test fixtures"
    assert "no_tracking" in markdown.read_text()
    original = manifest.read_bytes()
    result = subprocess.run(command + [str(manifest)], capture_output=True, text=True)
    assert result.returncode != 0
    assert manifest.read_bytes() == original
