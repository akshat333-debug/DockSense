#!/usr/bin/env python3
"""Execute pipeline variants and emit the ablation comparison.

The project's central claim is that temporal reasoning beats frame-only rules.
`scripts/compare_ablations.py` can format a comparison, but only from prediction
CSVs somebody produced by hand — which meant the claim had no reproducible
evidence behind it. This script closes that gap: it runs the *same* pipeline over
the *same* videos with one mechanism disabled at a time, writes a prediction CSV
per variant plus a manifest, and hands the manifest to the comparison tool.

    python scripts/run_ablations.py --videos data/synthetic/*.mp4 \
        --ground-truth data/synthetic/ground_truth.csv \
        --output-dir artifacts/evaluation/ablation

Every row in the resulting table is a real run. If a variant scores the same as
baseline, that is the honest finding and it should be reported as such — a flag
that changes nothing is evidence the mechanism is not doing the work claimed.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from handleguard.evaluation.ablations import compare_predictions, markdown_table
from handleguard.pipeline import PipelineFlags, run

# One mechanism off per variant. Turning several off at once would confound which
# one mattered, which is the whole point of an ablation.
VARIANTS: dict[str, PipelineFlags] = {
    "baseline": PipelineFlags(),
    "no_tracking": PipelineFlags(use_tracking=False),
    "no_smoothing": PipelineFlags(use_smoothing=False),
    "no_event_graph": PipelineFlags(use_event_graph=False),
    "no_zones": PipelineFlags(use_zones=False),
    "no_contextual_risk": PipelineFlags(use_contextual_risk=False),
}


def write_predictions(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["video", "behaviour", "t_start", "t_end"])
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--videos", nargs="+", type=Path, required=True)
    ap.add_argument("--ground-truth", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, default=ROOT / "artifacts" / "evaluation" / "ablation")
    ap.add_argument("--iou-threshold", type=float, default=0.5)
    ap.add_argument("--max-frames", type=int, default=None)
    ap.add_argument(
        "--dataset",
        default="synthetic logic validation",
        help="Provenance label. Do not call it held-out unless it genuinely is.",
    )
    ap.add_argument("--only", nargs="*", help="Subset of variant names to run.")
    args = ap.parse_args()

    variants = (
        {k: v for k, v in VARIANTS.items() if k in set(args.only)} if args.only else VARIANTS
    )
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    runs: dict[str, dict] = {}
    for name, flags in variants.items():
        print(f"\n=== {name} ===", flush=True)
        rows: list[dict] = []
        for video in args.videos:
            incidents = run(
                video,
                flags=flags,
                write_clips=False,
                video_id=video.stem,
                session=args.dataset,
                max_frames=args.max_frames,
            )
            print(f"  {video.name}: {len(incidents)} incidents", flush=True)
            rows.extend(
                {
                    "video": video.stem,
                    "behaviour": inc.name,
                    "t_start": round(inc.start_t, 3),
                    "t_end": round(inc.end_t, 3),
                }
                for inc in incidents
            )
        csv_path = out / f"{name}.csv"
        write_predictions(rows, csv_path)
        runs[name] = {
            "predictions_csv": csv_path.name,
            "settings": {
                f: getattr(flags, f)
                for f in ("use_tracking", "use_smoothing", "use_event_graph", "use_zones", "use_contextual_risk")
            },
        }

    gt_local = out / "ground_truth.csv"
    gt_local.write_text(args.ground_truth.read_text())

    manifest = {
        "dataset": args.dataset,
        "ground_truth": gt_local.name,
        "baseline": "baseline",
        "iou_threshold": args.iou_threshold,
        "runs": runs,
    }
    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    report = compare_predictions(manifest_path)
    (out / "ablations.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    table = markdown_table(report)
    (out / "ablations.md").write_text(table + "\n")

    print("\n" + table)
    print(f"\nwrote {out}/ablations.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
