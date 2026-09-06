# STATE — HandleGuard AI

Relay handoff file. **Read this first, update it last.**

---

## Protocol

1. `git pull`
2. Read this file top to bottom.
3. Pick the top unblocked item from **Next tasks**.
4. Build it. Run the check listed with it.
5. Update **Recent changes**, **Next tasks**, **Blockers**. Move done items to **Done**.
6. `git add -A && git commit && git push`

Rules:
- One person per owned directory at a time (see **Ownership**). Stay in your lane, no merge hell.
- Never mark a task done without running its check.
- If you tune a threshold, write down **which session's footage you tuned on**. S3 is off-limits.
- Do not put a number in the README or deck that you did not personally run.

---

## Ownership

| Lane | Directories | Owner |
|---|---|---|
| CV / behaviours | `handleguard/` | TBD |
| Backend / API / DB | `apps/api/`, `handleguard/db/` | TBD |
| Frontend / demo | `apps/web/`, `docs/`, `artifacts/` | TBD |

Shared, coordinate before editing: `configs/`, `STATE.md`, `requirements.txt`.

---

## Deadline

**10 September 2026.** Today is 7 September. **~3 days.**

---

## Current state

Plan approved ([plan.md](plan.md)). `project.md` drafted, **awaiting GATE 1 sign-off**.
Detector weights cached and benchmarked. **No implementation code yet. No footage yet.**

---

## Blockers

| Blocker | Severity | Owner | Note |
|---|---|---|---|
| **No warehouse video exists** | CRITICAL | unassigned | Blocks tuning, S3 metrics, demo, screenshots. See `docs/RECORDING_GUIDE.md`. Must happen today. |
| **GATE 1 unsigned** | HIGH | user | `project.md` needs confirmation before implementation starts. |
| **Lanes unassigned** | HIGH | user | All three rows below still say TBD. |

---

## Next tasks

Ordered. Top items are unblocked and can run in parallel across lanes.

### P0 — start now

1. **Record video** — `docs/RECORDING_GUIDE.md`, 3 sessions + hard negatives.
   *Check:* `data/raw/takes.csv` exists, S3 recorded from a different angle and untouched.
   *Blocks:* everything below marked ⛓.

2. **Detector wrapper** — `handleguard/perception/detector.py`.
   YOLO-World (`yolov8s-worldv2.pt`), classes set from `configs/products.yaml`.
   *Check:* runs on any mp4, prints per-frame boxes with class names.

3. **Tracker** — `handleguard/tracking/tracker.py`. ByteTrack via ultralytics `persist=True`.
   *Check:* IDs stay stable across a 10s clip.

4. **Geometry utils** — `handleguard/features/geometry.py`.
   `iou`, `intersection_area`, `horizontal_overlap`, `vertical_gap`, `point_in_polygon`,
   `bbox_bottom_center`, `support_fraction`.
   *Check:* `tests/unit/test_geometry.py` — asserts on hand-computed boxes. **Required.**

5. **Track history + velocity** — `handleguard/features/trajectory.py`.
   Smoothed velocity/acceleration. Never raw single-frame deltas.
   *Check:* synthetic track of known motion returns expected velocity.

### P0 — after 1–5

6. ⛓ **Vertical slice: drop only** — upload → detect → track → drop → risk → incident → clip → view.
   *Check:* one staged drop clip produces exactly 1 incident with a playable clip.
   **Nothing else starts until this works end to end.**

7. ⛓ Remaining 11 behaviour detectors, easiest first: zone → drag → overhang → unstable stack →
   improper stack → rough handling → throw → stepping → manual handling → sequence → surface.
   *Check per detector:* fires on its positive clips, silent on its named hard negative.

8. Risk engine + dedup + evidence clips — `handleguard/risk/`, `handleguard/incidents/`.
   *Check:* one continuous drop yields 1 incident, not 40.

9. FastAPI + SQLite + endpoints per master plan §30.
   *Check:* `/health` returns detector loaded; upload→process→incident round-trips.

10. Dashboard: incident list, detail + replay, review buttons, analytics.
    *Check:* full supervisor loop clicks through with no console errors.

11. Grounded assistant — tool-call layer over the incident DB, template fallback when no API key.
    *Check:* answers cite incident IDs; returns "no matching incidents" on an empty query;
    refuses "who is the worst worker".

### P1 — credibility, cheap, high value

12. ⛓ Eval harness — event-interval matching against `takes.csv`, per-behaviour P/R/F1 with **n shown**.
    *Check:* run on S3 only. Report the honest number even if it's bad.

13. ⛓ Ablations — same code, flags off: no tracking / no smoothing / no event graph.
    *Check:* a real table with real deltas. This is what backs the innovation claim.

14. Latency p50/p95 instrumentation.

### P2 — submission

15. Screenshots (master plan §70), 5–6 slide deck, demo recording, README, user feedback round.

---

## Recent changes

| When | Who | What |
|---|---|---|
| 7 Sep | Claude | Lane A started: `types.py` (FROZEN), `config.py`, `perception/geometry.py`. 19 unit tests green. |
| 7 Sep | Claude | `scripts/fetch_public_data.py` — reproducible CC BY 4.0 subset fetch, upstream train/test split preserved as tune/heldout. |
| 7 Sep | Claude | MPS benchmark: **36.1 fps** (28 ms/frame). Risk R2 retired. |
| 7 Sep | Claude | `plan.md` + `project.md` written. GATE 1 approved by user. |
| 6 Sep | — | Repo scaffolded, recording guide + configs written. |

---

## Done

- [x] `plan.md`, `project.md` — GATE 1 signed off
- [x] Detector weights cached to `models/yolov8s-worldv2.pt` (25 MB, committed)
- [x] MPS benchmark — 36.1 fps, logged in decisions
- [x] `.gitignore` bug fixed (was excluding the weights the offline demo needs)
- [x] `handleguard/types.py` — **FROZEN**, do not edit without announcing here
- [x] `handleguard/config.py` — single YAML entry point, `set_config_dir()` for tests
- [x] `handleguard/perception/geometry.py` + 13 hand-computed tests
- [x] `tests/unit/test_import_hygiene.py` — enforces one-directional layering
- [x] Public dataset subset fetching (58 clips, ~1.9 GB)

---

## Decisions log

| Decision | Rationale |
|---|---|
| **Measured 7 Sep: YOLO-World `yolov8s-worldv2` on MPS = 28 ms/frame (36.1 fps)** at 720p, imgsz=640, 5 classes | Benchmarked on the actual M3/8GB machine with a synthetic frame. Retires risk R2 — no need to drop resolution or pre-render. ~4.5x headroom over the 8 inference-fps target. Re-measure on real footage once S1 exists. |
| YOLO-World open-vocab detector | No annotation or training time available. Warehouse classes from text prompts. Cost: no custom-class mAP — report event-level metrics instead. |
| Detector weights committed to `models/` (25 MB) | Offline demo requirement. `.gitignore` corrected — it originally excluded `models/*.pt`, which would have broken a clean clone. |
| Thresholds normalized by object height, not pixels | Pixel thresholds break the moment the camera moves. See `configs/behaviours.yaml`. |
| S3 session held out, never tuned on | Only way any reported metric survives scrutiny. |
| SQLite, not Postgres | Prototype. One less service in the demo. |

---

## Claims ledger

Every number that reaches the README or deck gets a row. No row, no claim.

| Claim | Measured? | Where measured | Value |
|---|---|---|---|
| _(empty)_ | | | |
