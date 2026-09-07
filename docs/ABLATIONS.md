# Ablation comparisons

Compare saved event predictions against the same ground truth:

```sh
python scripts/compare_ablations.py path/to/manifest.json --output artifacts/ablations.json --markdown artifacts/ablations.md
```

The JSON manifest declares provenance and each run's settings. Paths resolve
relative to the manifest, independent of the command's working directory:

```json
{
  "dataset": "synthetic logic validation",
  "ground_truth": "ground_truth.csv",
  "baseline": "baseline",
  "iou_threshold": 0.5,
  "runs": {
    "baseline": {
      "predictions_csv": "baseline.csv",
      "settings": {"use_tracking": true}
    },
    "no_tracking": {
      "predictions_csv": "no_tracking.csv",
      "settings": {"use_tracking": false}
    }
  }
}
```

Every CSV needs `video,behaviour,t_start,t_end` columns. Video identifiers must
match exactly between predictions and ground truth. Include predictions from
negative clips, even though those clips have no ground-truth event rows. A
header-only prediction file represents a run with zero detections.

Reports contain per-behaviour and micro counts, precision, recall, F1, deltas
(variant minus baseline), declared settings, and SHA-256 input fingerprints.
The table is a summary; retain the JSON and original inputs for reproducibility.

This command evaluates existing predictions. Pipeline variant execution is still
pending. Settings are declarations, not independently verified execution logs.
Keep inputs fixed and vary one component at a time. Do not substitute copied or
handwritten predictions for measured pipeline runs. Unit-test fixture results
are checks of the comparison software, not detector accuracy evidence.

Remaining experiments: tracking off, smoothing off, event deduplication off, and
contextual risk off. The current feature window computes horizontal motion
ratio; a complete smoothing ablation needs an explicit smoothing implementation.
Deduplication is implemented, but a full event graph is not. Describe the actual
component disabled in each experiment. Contextual risk changes scoring, so event
F1 alone cannot evaluate it; collect risk labels and evaluate ranking/calibration.

Tune only on S1/S2; reserve S3 for the final held-out evaluation. Real footage and
validated detector prompts remain prerequisites for real-world accuracy claims.
