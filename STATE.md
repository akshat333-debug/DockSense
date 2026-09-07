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

Plan approved ([plan.md](plan.md)), GATE 1 signed. Foundation and code-owned P0
landed, committed, and pushed through `e82f958`. P1 now has a deterministic
synthetic vertical slice:

- `handleguard/types.py` — **FROZEN.** Shared dataclasses. Do not edit without announcing here.
- `handleguard/config.py` — YAML entry point.
- `handleguard/perception/geometry.py` — pure geometry, 13 tests.
- `scripts/fetch_public_data.py` — CC BY 4.0 subset fetch (reproducible).
- `scripts/render_synthetic.py` — Newtonian synthetic drop/throw/drag/place clips
  with frame-exact ground truth. Lets behaviour detectors be tuned + measured
  before any real footage exists.
- `models/yolov8s-worldv2.pt` — committed (25 MB), MPS benchmarked at 36 fps.

- `handleguard/features/compute.py` — normalized velocities, acceleration, zone,
  floor proximity, support, and held-by-person features.
- `handleguard/events/dedup.py` — continuous detector firings collapse into one
  event per behaviour/track/window.
- `handleguard/risk/` — contextual risk scoring and guarded explanations.
- `handleguard/incidents/` — SOP-backed incident builder.
- `handleguard/pipeline.py` — video -> detect -> track -> features -> behaviours
  -> dedupe -> risk -> incident -> evidence media -> optional DB.
- `apps/api/main.py` — FastAPI read/review/chat/clip endpoints over SQLite.
- `handleguard/assistant/templates.py` — offline deterministic assistant answers
  with guardrails, citations, and identity refusal.
- `apps/web/` — Vite/React incident review console over the API.

**Real footage is still missing. YOLO-World prompt validation is still not passing
on procedural synthetic clips, so the end-to-end unit test uses deterministic fake
detections.**

---

## Data is NOT in git — fetch it after cloning

`data/raw/`, `data/public/`, `data/synthetic/`, `data/processed/`, `data/clips/`
are all gitignored. A fresh clone has no video. To reproduce:

```bash
pip install -r requirements.txt
python scripts/fetch_public_data.py      # ~1.9 GB, CC BY 4.0, into data/public/
python scripts/render_synthetic.py       # deterministic, into data/synthetic/
```

`data/raw/` = our own recordings (S1/S2/S3). Whoever films uploads them to shared
storage out of band; they are never committed (size + privacy).

---

## Blockers

| Blocker | Severity | Owner | Note |
|---|---|---|---|
| **No real warehouse footage (S1/S2/S3)** | CRITICAL | unassigned | Synthetic clips unblock detector *logic*. Real footage still required for the submission's "robustly demonstrated" claims and every S3 metric. ~20 min with boxes + a propped phone. See `docs/RECORDING_GUIDE.md`. |
| **Lanes unassigned** | HIGH | team | All three rows in Ownership still say TBD. Assign before parallel work starts or you will collide. |
| **YOLO-World prompt validation not yet passing on procedural synthetic clips** | HIGH | CV | Wrapper initializes after installing `clip`, but `data/synthetic/drop.mp4` returns 0 detections at current prompts and even at 0.01 confidence. Validate prompts on LOCO/real footage before relying on detector output. |
| **CLIP text-model cache strategy unresolved for clean clone** | MEDIUM | CV | Local workspace cache exists at `models/.cache_home/.cache/clip/ViT-B-32.pt`, and code redirects YOLO-World there. It remains gitignored to avoid committing a large cache. Final packaging must decide how a clean offline clone receives this asset. |

---

## Next tasks

Ordered. `types.py`, `config.py`, `geometry.py` are **done** (committed `00f0b03`).
Pick up from here.

### IMMEDIATE NEXT — Lane A, unblocked, no footage needed

1. **`handleguard/video/reader.py`** — `iter_frames(path, inference_fps=8, max_res=(1280,720))`
   yielding `Frame` (see `types.py`). Decode with cv2, skip to target fps, resize.
   `Frame.t` is seconds from start and is the only time source downstream.
   *Check:* iterate `data/synthetic/drop.mp4`, assert frame count ≈ duration × inference_fps,
   assert `t` monotonic.

2. **`handleguard/perception/detector.py`** — `YoloWorldDetector.__call__(frame) -> list[Detection]`.
   Load `models/yolov8s-worldv2.pt`, `set_classes()` from `configs/products.yaml` prompts,
   map class index → (cls, role). `device="mps"` with a `try/except → "cpu"` fallback.
   *Check:* runs on a synthetic clip, returns `Detection` objects with role populated.

3. **`handleguard/tracking/tracker.py`** — `Tracker.update(dets, frame) -> list[Track]` via
   ultralytics ByteTrack (`persist=True`). Plus `NullTracker` (fresh id per detection) for
   the `use_tracking=False` ablation row.
   *Check:* IDs stable across a 10 s synthetic clip.

### Lane B — unblocked, uses `data/synthetic/`

4. **`handleguard/behaviours/base.py`** — `BehaviourDetector` ABC + `FrameContext` +
   `TrackHistory` + `registry`. Copy the 5 contract rules from `plan.md` into the docstring
   verbatim. Add all 12 `from . import bNN_x` lines to `__init__.py` now with stub classes
   so nobody edits it again.
   *Check:* `registry.build_all(cfg)` returns 12 detectors, disabled ones skipped.

5. **`tests/fixtures/synth.py`** — `synth_track(...)`, `make_ctx(...)`, and per-behaviour
   scenario generators (`scenario_drop`, `scenario_gentle_place`, `scenario_throw`,
   `scenario_carry`, …).
   *Check:* `make_ctx` builds a valid `FrameContext` from a list of synthetic tracks.

6. **B01 drop, B02 throw, B03 drag, B07 zone** — one class each. Read thresholds only from
   `self.cfg`. Distances in object-heights (already normalized in `TrackFeatures`).
   *Check per detector:* positive scenario fires, hard-negative scenario stays silent.
   **Write the negative test first.**

### Lane C — unblocked, no footage needed

7. **`handleguard/db/store.py`** — SQLite via stdlib `sqlite3`, one table + JSON blob column.
   `IncidentStore`: `init / add / query / get / stats / counts_by_behaviour`.
   `query()` is also the assistant's tool surface — shape it for both.
   *Check:* add 3 incidents, query by behaviour/min_risk/band, round-trip intact.

8. **`scripts/seed_fake_incidents.py`** — 40 plausible incidents so Lane C can build UI
   before the pipeline produces real ones. Mark them clearly as seeded, not AI-generated.

9. **Vite scaffold + incident table** — `apps/web/`, React + Vite. Risk and confidence in
   **separate columns**, band-coloured. Runs against seeded data.
   *Check:* `npm run dev`, table renders 40 rows, sorts by risk.

### After 1–9 — needs the vertical slice wired (Lane A owns `pipeline.py`)

10. ⛓ **Vertical slice** — `pipeline.py`: synthetic clip → detect → track → features → B01 →
    risk → incident → clip → DB. **Nothing downstream starts until this runs end to end.**

11. Remaining behaviours B04–B06, B08–B12. `events/dedup.py`, `risk/scorer.py`, `risk/explain.py`,
    `incidents/builder.py`.
    *Check:* one continuous drop → exactly 1 incident, not 40.

12. FastAPI (`apps/api/`) — `GET /incidents`, `/incidents/{id}`, `/stats`, `/clips/{file}`, `POST /chat`.

13. Incident detail view + clip playback + review buttons. Chat panel.

14. Assistant — `assistant/templates.py` (offline, default) then LLM path behind `ANTHROPIC_API_KEY`.
    *Check:* cites incident IDs; "No matching incidents found." on empty; refuses identity questions.

### P1 — credibility

15. ⛓ Eval harness — temporal-IoU event matching, per-behaviour P/R/F1 with **n shown**.
    Synthetic first (logic), then S3 real footage (the real number). Report both honestly.

16. ⛓ Ablation table — flags off: `use_tracking`, `use_smoothing`, `use_event_graph`.
    Real deltas. Backs the innovation claim.

17. Latency p50/p95 instrumentation.

### P2 — submission

18. Screenshots, 5–6 slide deck, demo recording, README (with CC BY 4.0 dataset attribution),
    `scripts/demo.sh` (one command, offline), user-feedback round.

---

## Recent changes

| When | Who | What |
|---|---|---|
| 7 Sep | Codex | Extracted offline assistant logic to `handleguard/assistant/templates.py` and wired `/chat` through it. Direct tests cover cited incident IDs/timestamps, exact empty-result wording, identity refusal, incident-id lookup, and loading guardrails from `configs/sop_rules.yaml`. Verification: `python -m pytest tests\unit -q` -> 81 passed; py_compile passed for assistant/API modules; `npm run build` still passes. |
| 7 Sep | Codex | Added evidence media extraction: `handleguard/incidents/media.py` writes bounded MP4 clips and JPEG thumbnails, and `pipeline.run()` attaches/persists `clip_path` and `thumb_path`. Verification: `python -m pytest tests\unit -q` -> 76 passed; py_compile passed for media/pipeline modules; `npm run build` still passes. |
| 7 Sep | Codex | Added `apps/web/` Vite/React console: risk-sorted incident queue, band filter, stats strip, incident detail, evidence/SOP panels, review controls, clip-player slot, and guarded chat panel. Added API CORS for local Vite. Verification: `npm install` -> 0 vulnerabilities; `npm run build` passed; `python -m pytest tests\unit -q` -> 75 passed; live API returned 40 seeded rows and Vite served `http://127.0.0.1:5173/`. |
| 7 Sep | Codex | Added FastAPI service in `apps/api/main.py`: `/incidents`, `/incidents/{id}`, `/incidents/{id}/review`, `/stats`, `/clips/{file_path}`, and guarded offline `/chat`. Verification: `python -m pytest tests\unit -q` -> 74 passed; py_compile passed for API/store modules. |
| 7 Sep | Codex | Added `TASK_SHEET.md` with prioritized remaining work and usage stop condition. Started Lane A by implementing `handleguard/video/reader.py` with timestamp-based sampling and unit coverage; synthetic `drop.mp4` smoke check passed at 32 frames / 4 s / 8 fps. |
| 7 Sep | Codex | Implemented `handleguard/perception/detector.py`: YOLO-World wrapper, YAML prompt mapping, role-populated `Detection` conversion, repo-local predict/cache paths, and RuntimeError-only MPS→CPU fallback. Unit tests pass; real synthetic smoke initializes but returns 0 detections. |
| 7 Sep | Codex | Added P1 synthetic vertical slice: `FeatureExtractor`, `EventDeduper`, risk scoring/explanations, SOP-backed incident builder, and `pipeline.run`. Verification: `python -m pytest tests\unit -q` -> 71 passed; py_compile passed for new modules. |
| 7 Sep | Codex | Finished code-owned P0: ByteTrack-backed `Tracker` with IoU fallback, `NullTracker`, behaviour `FrameContext`/`TrackHistory`/registry, B01/B02/B03/B07 detectors with hard-negative tests, SQLite `IncidentStore`, and deterministic fake incident seeding. |
| 7 Sep | Claude | `scripts/render_synthetic.py` + `data/synthetic/` — Newtonian drop/throw/drag/place clips, frame-exact GT. Detector logic no longer blocked on real footage. Clips gitignored (regenerate with the script). |
| 7 Sep | Claude | Lane A foundation: `types.py` (FROZEN), `config.py`, `perception/geometry.py`. Unit tests green. Committed `00f0b03`. |
| 7 Sep | Claude | `scripts/fetch_public_data.py` — reproducible CC BY 4.0 subset fetch, upstream train/test split preserved as tune/heldout. |
| 7 Sep | Claude | MPS benchmark: **36.1 fps** (28 ms/frame). Risk R2 retired. |
| 7 Sep | Claude | `plan.md` + `project.md` written. GATE 1 approved by user. |
| 6 Sep | — | Repo scaffolded, recording guide + configs written. |

---

## Done

- [x] `handleguard/video/reader.py` — OpenCV frame iterator with inference-fps sampling and max-resolution resize
- [x] `handleguard/perception/detector.py` — YOLO-World adapter implemented and unit-tested; prompt validation remains open
- [x] `handleguard/tracking/tracker.py` — ByteTrack-backed tracker with deterministic IoU fallback plus `NullTracker`
- [x] `handleguard/behaviours/base.py` — `FrameContext`, `TrackHistory`, shared detector contract, confidence helper
- [x] `handleguard/behaviours/registry.py` + all 12 behaviour module imports/stubs
- [x] B01 drop, B02 throw, B03 drag, B07 zone violation — implemented against normalized `TrackFeatures`
- [x] `tests/fixtures/synth.py` — synthetic track/context fixtures for behaviour tests
- [x] `handleguard/db/store.py` — SQLite incident persistence with query/get/stats/counts
- [x] `scripts/seed_fake_incidents.py` — 40 clearly seeded placeholder incidents for product work
- [x] `handleguard/features/compute.py` — scale-normalized track feature extractor
- [x] `handleguard/events/dedup.py` — one continuous drop collapses to one event
- [x] `handleguard/risk/scorer.py` + `handleguard/risk/explain.py` — contextual risk and guarded explanation text
- [x] `handleguard/incidents/builder.py` + `handleguard/incidents/sop.py` — SOP-backed incident assembly
- [x] `handleguard/incidents/media.py` — evidence MP4 and JPEG thumbnail extraction
- [x] `handleguard/pipeline.py` — deterministic synthetic clip to incident in SQLite path
- [x] `apps/api/main.py` — FastAPI incident list/detail/stats/review/clip/chat endpoints
- [x] `handleguard/assistant/templates.py` — offline assistant citations, empty-result handling, and identity refusal
- [x] `apps/web/` — Vite/React incident queue, detail, review, clip slot, and chat UI
- [x] `plan.md`, `project.md` — GATE 1 signed off
- [x] Detector weights cached to `models/yolov8s-worldv2.pt` (25 MB, committed)
- [x] MPS benchmark — 36.1 fps, logged in decisions
- [x] `.gitignore` bug fixed (was excluding the weights the offline demo needs)
- [x] `handleguard/types.py` — **FROZEN**, do not edit without announcing here
- [x] `handleguard/config.py` — single YAML entry point, `set_config_dir()` for tests
- [x] `handleguard/perception/geometry.py` + 13 hand-computed tests
- [x] `tests/unit/test_import_hygiene.py` — enforces one-directional layering
- [x] `scripts/fetch_public_data.py` — public dataset subset (~1.9 GB, gitignored)
- [x] `scripts/render_synthetic.py` — synthetic physics clips (gitignored, regenerable)

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
