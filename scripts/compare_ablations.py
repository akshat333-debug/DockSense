#!/usr/bin/env python3
"""Compare saved baseline/variant prediction CSVs using a JSON manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from handleguard.evaluation.ablations import compare_predictions, markdown_table


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True, help="JSON report path")
    parser.add_argument("--markdown", type=Path, help="Optional Markdown comparison table")
    args = parser.parse_args()
    if args.markdown and args.output.resolve() == args.markdown.resolve():
        parser.error("JSON and Markdown output paths must differ")
    report = compare_predictions(args.manifest)
    inputs = {args.manifest.resolve(), Path(report["ground_truth"]["path"])}
    inputs.update(Path(row["predictions"]["path"]) for row in report["runs"].values())
    if any(path and path.resolve() in inputs for path in (args.output, args.markdown)):
        parser.error("output paths must not overwrite inputs")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    table = markdown_table(report)
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(table, encoding="utf-8")
    print(table)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
