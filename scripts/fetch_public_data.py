#!/usr/bin/env python3
"""Fetch the public-dataset subset DockSense uses.

Source: Önal, O. & Dandıl, E. (2024), "Video dataset for the detection of safe and
unsafe behaviours in workplaces", Data in Brief.
  Primary : https://data.mendeley.com/datasets/xjmtb22pff/1
  Mirror  : https://huggingface.co/datasets/Voxel51/Safe_and_Unsafe_Behaviours
  License : CC BY 4.0  (attribution required — see README.md)

Why only a subset: the full set is 691 clips / ~10 GB across 8 classes, four of
which (electrical panel covers, maintenance interventions) have no counterpart in
warehouse handling. We pull the four that do:

    class 0  Safe Walkway Violation          -> B07 positive examples
    class 3  Carrying Overload with Forklift -> equipment-present context
    class 4  Safe Walkway                    -> HARD NEGATIVE for B07
    class 7  Safe Carrying                   -> HARD NEGATIVE for B03 / B10

Split handling: the upstream filename encodes the authors' own train/test split
(`{class}_{tr|te}{n}.mp4`). We keep it. Their `te` clips land in
data/public/heldout/ and are treated exactly like our own S3 session — tuned on
never, evaluated once. Their `tr` clips land in data/public/tune/.

Idempotent: files already present are skipped.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

REPO = "Voxel51/Safe_and_Unsafe_Behaviours"
API = f"https://huggingface.co/api/datasets/{REPO}"
RAW = f"https://huggingface.co/datasets/{REPO}/resolve/main/"

# class index -> (short name, tune-split cap, heldout-split cap)
#
# Measured 7 Sep: these clips average ~32 MB (1080p24, up to 20 s), so the full
# four-class set would be ~5.8 GB. We do not need volume here — public footage
# is for validating B07, supplying hard negatives, and demo realism, not for
# training anything. A few dozen clips does all three.
WANTED: dict[str, tuple[str, int, int]] = {
    "0": ("walkway_violation", 12, 8),
    "3": ("forklift_overload", 6, 4),
    "4": ("walkway_safe", 8, 6),
    "7": ("carrying_safe", 8, 6),
}

FNAME = re.compile(r"data/(\d+)_(tr|te)(\d+)\.mp4$")


def list_repo_files() -> list[str]:
    with urllib.request.urlopen(API, timeout=60) as r:
        meta = json.load(r)
    return [s["rfilename"] for s in meta.get("siblings", [])]


def select(files: list[str]) -> list[tuple[str, Path]]:
    """Return (remote_path, local_relative_path) pairs, deterministically ordered."""
    buckets: dict[tuple[str, str], list[tuple[int, str]]] = {}
    for f in files:
        m = FNAME.match(f)
        if not m:
            continue
        cls, split, n = m.group(1), m.group(2), int(m.group(3))
        if cls not in WANTED:
            continue
        buckets.setdefault((cls, split), []).append((n, f))

    out: list[tuple[str, Path]] = []
    for (cls, split), items in sorted(buckets.items()):
        name, tr_limit, te_limit = WANTED[cls]
        items.sort()  # by clip number — deterministic, not random
        items = items[: (te_limit if split == "te" else tr_limit)]
        sub = "heldout" if split == "te" else "tune"
        for _, remote in items:
            out.append((remote, Path("data/public") / sub / name / Path(remote).name))
    return out


def fetch(remote: str, dest: Path) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return 0
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(RAW + remote, timeout=120) as r, open(tmp, "wb") as fh:
        while chunk := r.read(1 << 20):
            fh.write(chunk)
    tmp.rename(dest)
    return dest.stat().st_size


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="list what would be fetched")
    args = ap.parse_args()

    root = Path(__file__).resolve().parent.parent
    plan = select(list_repo_files())
    print(f"selected {len(plan)} clips across {len(WANTED)} classes")

    if args.dry_run:
        for remote, rel in plan[:10]:
            print("  ", remote, "->", rel)
        print(f"   ... ({len(plan)} total)")
        return 0

    total = 0
    for i, (remote, rel) in enumerate(plan, 1):
        n = fetch(remote, root / rel)
        total += n
        status = "skip" if n == 0 else f"{n / 1e6:.1f}MB"
        print(f"[{i}/{len(plan)}] {rel.name} {status}", flush=True)

    print(f"\ndone. {total / 1e9:.2f} GB fetched into data/public/")
    print("heldout/ = upstream test split. Treat as S3: never tune on it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
