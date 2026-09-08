#!/usr/bin/env python3
"""Reassemble the large model assets that git cannot hold in one piece.

Why this exists
---------------
Ultralytics' YOLO-World calls ``clip.load(...)`` inside ``set_classes()``, which
pulls OpenAI CLIP ViT-B-32 (338 MB) from the network on first use. Measured
8 Sep 2026: a cold run took 186 s, of which 177 s was that download. The demo is
required to run with the network disabled (NFR1 / AC13), so the asset must ship
inside the clone.

338 MB exceeds GitHub's 100 MB per-file hard limit, and Git LFS would add a
tooling dependency plus a 1 GB/month bandwidth cap — roughly three fresh clones.
So the file is committed as ~90 MB chunks under ``models/clip_parts/`` and
reassembled here, with a SHA256 check so a truncated or corrupted part fails
loudly instead of surfacing later as a confusing model error.

Usage
-----
    python scripts/setup_offline.py            # reassemble (what a fresh clone runs)
    python scripts/setup_offline.py --verify   # check only, no writes
    python scripts/setup_offline.py --split    # maintainer: regenerate chunks

Idempotent: exits immediately if the assembled file is already present and valid.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Must match _ensure_repo_cache_home() in handleguard/perception/detector.py,
# which points HOME/USERPROFILE at models/.cache_home so CLIP resolves here.
TARGET = ROOT / "models" / ".cache_home" / ".cache" / "clip" / "ViT-B-32.pt"
PARTS_DIR = ROOT / "models" / "clip_parts"
MANIFEST = PARTS_DIR / "manifest.txt"

CHUNK = 90 * 1024 * 1024  # 90 MB — comfortably under GitHub's 100 MB limit
DETECTOR_WEIGHTS = ROOT / "models" / "yolov8s-worldv2.pt"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def read_manifest() -> tuple[str, int] | None:
    if not MANIFEST.exists():
        return None
    digest, size = MANIFEST.read_text().split()[:2]
    return digest, int(size)


def do_split() -> int:
    """Maintainer-only: chop the assembled file into committable chunks."""
    if not TARGET.exists():
        print(f"error: {TARGET} not present — nothing to split", file=sys.stderr)
        return 1

    PARTS_DIR.mkdir(parents=True, exist_ok=True)
    for stale in PARTS_DIR.glob("ViT-B-32.pt.*"):
        stale.unlink()

    digest, size = sha256(TARGET), TARGET.stat().st_size
    with open(TARGET, "rb") as fh:
        for i in range((size + CHUNK - 1) // CHUNK):
            part = PARTS_DIR / f"ViT-B-32.pt.{i:03d}"
            part.write_bytes(fh.read(CHUNK))
            print(f"  wrote {part.name}  {part.stat().st_size / 1e6:.1f} MB")

    MANIFEST.write_text(f"{digest} {size}\n")
    print(f"\nsplit complete: {size / 1e6:.1f} MB -> {len(list(PARTS_DIR.glob('*.0*')))} parts")
    print(f"sha256 {digest}")
    return 0


def do_join(verify_only: bool = False) -> int:
    manifest = read_manifest()
    if manifest is None:
        print(f"error: {MANIFEST} missing — clone is incomplete", file=sys.stderr)
        return 1
    want_digest, want_size = manifest

    if TARGET.exists() and TARGET.stat().st_size == want_size:
        if sha256(TARGET) == want_digest:
            print(f"CLIP weights already present and valid ({want_size / 1e6:.0f} MB)")
            return 0
        print("existing file failed checksum — rebuilding")

    if verify_only:
        print("error: assembled file missing or invalid", file=sys.stderr)
        return 1

    parts = sorted(PARTS_DIR.glob("ViT-B-32.pt.[0-9][0-9][0-9]"))
    if not parts:
        print(f"error: no chunks in {PARTS_DIR}", file=sys.stderr)
        return 1

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    tmp = TARGET.with_suffix(".pt.partial")
    with open(tmp, "wb") as out:
        for p in parts:
            out.write(p.read_bytes())
            print(f"  joined {p.name}")

    got = sha256(tmp)
    if got != want_digest:
        tmp.unlink()
        print(
            f"error: checksum mismatch\n  expected {want_digest}\n  got      {got}\n"
            "A chunk is corrupt or missing. Re-clone or re-pull models/clip_parts/.",
            file=sys.stderr,
        )
        return 1

    tmp.replace(TARGET)
    print(f"\nCLIP weights assembled: {TARGET.relative_to(ROOT)} ({want_size / 1e6:.0f} MB)")
    return 0


def preflight() -> int:
    """Assert every asset the offline demo needs. Loud, specific failures."""
    ok = True
    if not DETECTOR_WEIGHTS.exists():
        print(f"MISSING: {DETECTOR_WEIGHTS.relative_to(ROOT)}", file=sys.stderr)
        print("  -> committed to the repo; try `git checkout models/`", file=sys.stderr)
        ok = False
    if not TARGET.exists():
        print(f"MISSING: {TARGET.relative_to(ROOT)}", file=sys.stderr)
        print("  -> run: python scripts/setup_offline.py", file=sys.stderr)
        ok = False
    if ok:
        print("preflight OK — all offline assets present")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--split", action="store_true", help="maintainer: regenerate chunks")
    ap.add_argument("--verify", action="store_true", help="check only, no writes")
    ap.add_argument("--preflight", action="store_true", help="assert all demo assets exist")
    args = ap.parse_args()

    if args.split:
        return do_split()
    if args.preflight:
        return preflight()
    return do_join(verify_only=args.verify)


if __name__ == "__main__":
    sys.exit(main())
