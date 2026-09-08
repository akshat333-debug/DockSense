#!/usr/bin/env bash
# DockSense demo launcher — must work with the network disabled.
#
# Everything the demo needs ships in the clone. The one asset git cannot hold in
# a single piece (CLIP ViT-B-32, 338 MB, over GitHub's 100 MB limit) is committed
# as chunks and reassembled by scripts/setup_offline.py on first run.
#
#   ./scripts/demo.sh              serve API + web console on :8000
#   ./scripts/demo.sh --check      preflight only, start nothing
set -euo pipefail

cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"

echo "==> Checking offline assets"
# Reassemble CLIP if this is a fresh clone. No-op once valid.
if ! "$PY" scripts/setup_offline.py --verify >/dev/null 2>&1; then
  echo "    CLIP weights not assembled yet — building from chunks"
  "$PY" scripts/setup_offline.py
fi

# Hard-fail with a specific message rather than silently downloading mid-demo.
if ! "$PY" scripts/setup_offline.py --preflight; then
  echo
  echo "FATAL: offline assets missing. The demo would try to download ~338 MB." >&2
  echo "Fix the errors above before demoing." >&2
  exit 1
fi

if [[ "${1:-}" == "--check" ]]; then
  echo "==> Preflight passed. Not starting servers (--check)."
  exit 0
fi

echo "==> Seeding demo database"
"$PY" scripts/seed_fake_incidents.py

echo "==> Starting API on http://127.0.0.1:8000"
echo "    Ctrl-C to stop."
exec "$PY" -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
