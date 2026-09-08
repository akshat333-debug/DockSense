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

Assigned 8 Sep from demonstrated work in git history, not guessed.

| Lane | Directories | Owner |
|---|---|---|
| **A — CV / perception / infra** | `handleguard/{video,perception,tracking,features}`, `scripts/`, `models/`, `configs/` | **Akshat** (`akshatagrawal.work@gmail.com`) |
| **B — Reasoning / evaluation** | `handleguard/{behaviours,events,risk,incidents,evaluation}`, `tests/` | **Anirudh** (`anirudhbadampudi@gmail.com`) |
| **C — Product / demo** | `apps/api/`, `apps/web/`, `handleguard/{db,assistant}`, `artifacts/`, slides | **UNASSIGNED — third teammate, name needed** |

Shared, coordinate before editing: `configs/`, `STATE.md`, `TASK_SHEET.md`, `requirements.txt`.

**Note:** git history shows only two contributors. Lane C is currently
uncovered, and it owns the demo, screenshots and slides — i.e. everything the
judges actually see. Until the third person is named, **Lane C work is split:
Anirudh takes `apps/web` (already active there), Akshat takes `apps/api` +
demo packaging.**

### Remaining work is no longer three parallel lanes

All twelve behaviours are implemented and the code is largely complete. What is
left is mostly sequential and mostly gated on footage:

| Work | Owner | Gated on |
|---|---|---|
| **Film S1/S2/S3** | Team — whoever is free first | Nothing. **This is the critical path.** |
| Tune thresholds on S1/S2 | A + B together | Footage |
| S3 held-out evaluation (run **once**) | B | Footage + tuning |
| Ablation table on real footage | B | Footage |
| Latency p50/p95 instrumentation | A | Nothing |
| Screenshots, deck, demo recording | C | A working demo |
| Two offline rehearsals | Team | Everything else |

---

## Deadline

**10 September 2026.** Today is 8 September. **~2 days.**

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
- `handleguard/evaluation/metrics.py` + `scripts/evaluate_events.py` — temporal-IoU
  event evaluation with per-behaviour TP/FP/FN, precision, recall, F1, and n.

Added 8 Sep:

- **All 12 behaviour detectors implemented, zero stubs.** Each has a positive test
  and a named hard negative.
- `handleguard/events/graph.py` — the Temporal Event Graph. Relates deduplicated
  events by FOLLOWS / SHARES_TRACK / RECURS; `chains()` gives per-entity stories,
  `recurrence()` feeds the frequency risk component so a third drop of the same
  carton outscores the first.
- `PipelineFlags` + `scripts/run_ablations.py` — the ablation switches are now
  wired to real mechanisms and executable end to end.
- `models/clip_parts/` + `scripts/setup_offline.py` + `scripts/demo.sh` — offline
  operation, verified with sockets blocked.
- `README.md` — with the CC BY 4.0 attribution both datasets require.

**123 tests pass.**

**Still missing: real footage of drops / throws / stacking.** Behaviour *logic* is
tested against injected synthetic tracks; perception is verified on real CCTV. What
does not exist yet is real video where those two meet, which is what every
per-behaviour metric and every "robustly demonstrated" claim depends on.

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
| **No real footage of drop / throw / stacking** | CRITICAL | unassigned | Public CCTV covers B07 + hard negatives only. B01/B02/B05/B06/B08 have no real video to fire on. **Decision taken 8 Sep: we record.** Full brief below — see *Recording brief*. ~35 min. |
| **No behaviour has ever fired on real video** | HIGH | CV | Pipeline runs clean on real CCTV (8.1 s / 60 frames warm) but yields **0 incidents**. Zones are placeholders, and see the note below on why the public dataset cannot supply B07 ground truth. Real zone validation needs our own footage. |
| **Lane C has no owner** | HIGH | team | Git history shows only two contributors. Lane C owns the demo, screenshots and slides — everything the judges actually see. Interim split recorded in Ownership; name the third person or accept the split. |

### Closed 8 Sep

| Was | Finding |
|---|---|
| ~~"Offline demo broken — 338 MB CLIP downloads at runtime"~~ | **Fixed.** CLIP ships as four ~90 MiB chunks in `models/clip_parts/` (338 MB is over GitHub's 100 MB per-file limit; LFS would add tooling plus a 1 GB/month cap ≈ 3 clones). `scripts/setup_offline.py` reassembles with a SHA256 check; `scripts/demo.sh` reassembles then hard-fails with a fix message rather than silently downloading mid-demo. **Verified with `socket.connect` patched to raise: pipeline completes on real CCTV in 8.3 s with zero outbound connections.** |
| ~~"8 of 12 behaviours are stubs"~~ | **All 12 implemented, zero stubs.** B05/B06/B08/B09/B12 then B04/B10/B11 added 8 Sep, each with a positive test and a named hard negative. B04 and B10 carry suppression logic (defer to B01/B02; go silent when equipment is visible) so the weak three do not generate noise. |
| ~~"YOLO-World prompt validation not passing — 0 detections even at 0.01 conf"~~ | **Misdiagnosed. Prompts are fine.** Verified on real CCTV: `7_tr1.mp4` → **57 detections**, `4_te4.mp4` → **52**, correct classes (person / cardboard box / hand trolley). The 0-detection result happens **only on synthetic clips**, and it is expected and unfixable: `render_synthetic.py` draws flat coloured rectangles, and a model trained on photographs correctly refuses to call a grey rectangle a cardboard box. **Synthetic clips validate behaviour LOGIC via injected tracks; they can never validate perception.** Do not spend time tuning prompts. |

---

## Data semantics — why the public dataset is NOT B07 ground truth

Investigated 8 Sep. Worth reading before anyone tries to "just tune zones until
B07 fires on the public clips."

The Unsafe-Net footage is a **metal-press factory**, and its *Safe Walkway
Violation* label means **a person walking off a marked pedestrian walkway**.
Our B07 means **a product placed in a restricted zone in a loading bay**.
Different subject (person vs product) and inverted zone semantics (there, the
walkway is the *safe* area you must stay inside; here, the zone is the *forbidden*
area you must stay out of).

Traced the painted floor markings by HSV colour to check: the large green region
is a floor-marked **storage bay beside the shelving**, not the pedestrian route.

**If we drew polygons until B07 fired on their clips, we would produce a
precision/recall number that looks real but measures a behaviour we did not
build.** A judge probing the eval would find it. So:

| Public data IS used for | Public data is NOT used for |
|---|---|
| Detector validation on real industrial video (**verified: 57 and 52 correct detections**, classes person / cardboard box / hand trolley) | B07 precision/recall |
| Hard negatives — "does the system stay silent on normal operation" | Any per-behaviour metric |
| Demo b-roll showing real-world footage | The "robustly demonstrated" claims |

Real zone metrics come from **our own footage**, where we tape the zones and
therefore control what they mean.

---

## Recording brief — READ THIS BEFORE FILMING

Decision taken 8 Sep: **we record.** Without this footage, five of the six flagship
behaviours (B01 drop, B02 throw, B05 improper stack, B06 unstable stack, B08 pallet
overhang) have no real video to fire on, and the submission cannot claim they were
demonstrated. Public CCTV only covers B07 and hard negatives.

**Time: ~35 minutes. Two people. No warehouse needed.**

### Kit

| Item | Notes |
|---|---|
| 8–12 cardboard boxes | Amazon/delivery boxes fine. Need **at least 3 clearly large** and **5 small** — B05 needs a visible size difference |
| 1 pallet substitute | Real pallet ideal. Otherwise a low wooden board, crate, or upturned tray. Note in `takes.csv` what you used |
| 1 trolley substitute | Hand truck, luggage trolley, or office chair. Must be visibly *equipment*, not a box |
| Masking tape | Mark zone boundaries on the floor |
| Marker pen | **Write a big number on each box.** Massively helps tracking and annotation later |
| Phone + tripod | Or prop it on a stack of books. **Never hand-hold** — camera shake creates fake velocity and fires false drops |

### Camera setup

- **Fixed position.** Does not move at all within a session.
- Landscape, **1080p, 30 fps**.
- Frame must contain: the **floor line**, the **pallet**, and the **full height a box is lifted to**. If the box leaves frame at the top, the drop is unmeasurable.
- Good even light. No window or lamp directly behind the scene.
- Tape two floor zones and note which is which:
  - `staging` — products allowed
  - `walkway` — products forbidden (this is what B07 fires on)

### Session structure — this part matters most

Record in **sessions**. A session = one unbroken camera position.
Name every file `S{n}_{behaviour}_{take}.mp4` → e.g. `S1_drop_03.mp4`.

| Session | Camera | Purpose |
|---|---|---|
| **S1** | Near, side-on, ~3 m | Primary tuning data |
| **S2** | Far, side-on, ~6 m | Scale robustness |
| **S3** | Elevated / angled ~30° | **HELD OUT. Never tuned on. Evaluated once, at the end.** |

**Why sessions and not clips:** the train/test split is by *session*. Two takes of the
same drop from the same camera position must never land on opposite sides of the split
— that's leakage, and it's the first thing a judge probes. Recording in labelled
sessions is what makes an honest split possible at all.

S3 is the honesty artifact. Tuning on S1/S2 and reporting on S3 is the difference
between a real number and one that gets dismantled.

### Shot list — 3 takes minimum per behaviour per session

Vary speed and box size between takes.

| # | Behaviour | What to do | Priority |
|---|---|---|---|
| B01 | Drop | Lift box to chest height, release cleanly, let it hit the floor | **FLAGSHIP** |
| B02 | Throw | Toss box sideways 1–2 m onto floor or pallet | **FLAGSHIP** |
| B05 | Improper stack | Place a **large** box on top of a **small** one, leave it | **FLAGSHIP** |
| B06 | Unstable stack | Stack boxes with big overhang / visible lean | **FLAGSHIP** |
| B08 | Pallet overhang | Place box so ~half hangs off the pallet edge | **FLAGSHIP** |
| B03 | Drag | Push/pull box along floor 2 m+ without lifting | secondary |
| B07 | Zone violation | Place box in the taped `walkway` zone, leave 5 s+ | secondary |
| B09 | Stepping on box | Step on a box, hold foot there 2 s+ | secondary |
| B04 | Rough handling | Slam box down hard onto pallet; shove box into another | secondary |
| B10 | Manual heavy lift | Carry the largest box alone, **no trolley in frame** | secondary |
| B12 | Unsafe surface | Move box through the taped unsafe zone | secondary |
| B11 | Unsafe sequence | Lift heavy box, move, place unstably — trolley visible but unused | secondary |

**If short on time: shoot the five FLAGSHIP rows across S1 and S3 and stop.** Those are
what the submission's headline claims rest on.

### Hard negatives — do NOT skip

**Most-skipped, highest-value part of the shoot.** Without these, every detector looks
perfect because it never gets a chance to be wrong. These clips are what the
false-positive rate is measured on.

Record **5+ takes each**:

| Clip | Must NOT fire |
|---|---|
| Gentle controlled placement | drop |
| Carrying a box at knee height | drag |
| Box moved on the trolley | drag, manual-handling |
| Correct stack — small on large | improper stack |
| Person walking past a box, no contact | stepping |
| Box fully on pallet, well aligned | overhang |
| Person briefly crossing the walkway | zone violation (transient) |
| **Static scene, boxes at rest, 30 s** | anything at all |

That last one is the single best demo asset you will record. *"Here is 30 seconds of
normal operation and the system stayed silent"* answers the question every judge is
privately asking.

### Log every take — `data/raw/takes.csv`

One line per take, written **at record time**. Reconstructing timestamps from footage
afterwards takes hours; this takes seconds and is the input to every metric we report.

```csv
filename,session,behaviour,approx_start_s,approx_end_s,notes
S1_drop_01.mp4,S1,drop,2.4,3.1,large box chest height
S1_normal_01.mp4,S1,none,,,gentle placement
```

### Done when

- [ ] 3 sessions from genuinely different camera positions
- [ ] 5 flagship behaviours × 3 takes × at least S1 and S3
- [ ] 8 hard-negative categories, 5 takes each
- [ ] One 30 s+ fully-normal clip
- [ ] `takes.csv` filled in
- [ ] Files copied into `data/raw/` (gitignored — share via drive, never commit)

Full original version with extra detail: `docs/RECORDING_GUIDE.md`.

---

## Next tasks

**Queue rewritten 8 Sep after full audit at `26370d8`. This supersedes every
numbered list below it** (those are kept only as historical record — most are done).

Deadline **10 Sep**. ~2 days. Blocks are ordered; within a block, items are parallel.

### BLOCK 1 — unblock the demo (do first)
1. **Offline model assets.** CLIP ViT-B-32 is 338 MB, over GitHub's 100 MB per-file
   limit — plain `git add` will be rejected. Resolve via LFS / chunking / setup script,
   then add a `scripts/demo.sh` preflight that hard-fails with a fix message if either
   weight file is missing. *Check:* WiFi off, clean shell → pipeline runs.
2. **Film** per *Recording brief* above. Unblocks everything in Block 5's claims.

### BLOCK 2 — first real incident
3. Trace zone polygons from an actual frame of `data/public/tune/walkway_violation/`,
   add a `public_cam` entry to `configs/zones.yaml`, wire the camera id through.
   *Check:* `0_tr1.mp4` produces ≥1 B07 incident. **First real detection this project
   will ever have made.**

### BLOCK 3 — close the scope gap (4 behaviours → 11)
4. **B05, B06, B08** — static two-box geometry; `perception/geometry.py` already has
   the primitives (`support_ratio`, overlap, area). Restores the flagship tier. → 7
5. **B09, B12** — near-free. B12 is a zone lookup like B07; B09 is person-bottom-over-
   product overlap. → 9
6. **B04, B10** — conservative thresholds, labelled *lightly validated*. → 11
   **Every detector: write the hard-negative test BEFORE the positive one.**

### BLOCK 4 — evidence (what the judging actually rewards)
7. Wire ablation flags into `pipeline.run(flags=...)` — `use_tracking=False` →
   `NullTracker`, `use_smoothing=False` → raw single-frame velocity, `use_zones=False`
   → skip zone assignment. Feed `scripts/compare_ablations.py`. *Check:* real deltas.
8. Minimal `events/graph.py` — nodes = deduped events, edges = temporal-follows +
   shares-track, `chains()`. Feeds the frequency risk component and the UI timeline.
   This is what backs the novelty claim.
9. Run evaluation on the heldout split → per-behaviour P/R/F1 **with n shown** →
   `artifacts/evaluation/`. **Fill the claims ledger with whatever comes out.**
10. Per-stage latency p50/p95.

### BLOCK 5 — submission
11. `README.md` — incl. **CC BY 4.0 attribution for both datasets** (license
    obligation, not a nicety) and the honest robust / lightly-validated behaviour split.
12. Screenshots → `artifacts/screenshots/`, 5–6 slide deck, demo recording.
13. **Two offline rehearsals with WiFi off.**

---

## Historical task list (mostly done — kept for reference)

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
| 8 Sep | Claude | **All 12 behaviours implemented (B04/B10/B11 completed), ablation flags wired, temporal event graph added, README written.** 123 tests pass. B04 defers to B01/B02 and B10 goes silent when equipment is visible, so the weak three don't generate noise they can't justify. |
| 8 Sep | Claude | **B05/B06/B08/B09/B12 implemented — 4 behaviours to 9.** Shared geometry helpers added to `base.py` so detectors never touch raw `xyxy` (enforced by test). Fixed a real defect: `below()` used `is_above`'s default `min_overlap=0.3`, making a box overhanging >70% invisible to B06 — the most dangerous stack was the one it couldn't see. 103 tests pass. |
| 8 Sep | Claude | **Offline demo fixed.** CLIP shipped as 4 chunks + SHA256-checked reassembly + `demo.sh` preflight. Verified with sockets blocked: 8.3 s run, zero network calls. |
| 8 Sep | Claude | **Public dataset cannot supply B07 ground truth** — see *Data semantics* note below. Used for detector validation and hard negatives only. |
| 8 Sep | Claude | **Full audit at `26370d8`.** Verified by running, not reading: 92 tests pass; detector works on real CCTV (57 + 52 detections, correct classes); full pipeline runs end-to-end on real video at ~7.4 fps warm. Found: offline demo broken (338 MB runtime download), 8/12 behaviours are stubs, event graph absent, ablations unwired, 0 incidents on real footage (placeholder zones). **Closed the misdiagnosed prompt blocker** — prompts were never the problem. Queue rewritten; recording brief added. |
| 7 Sep | Codex | Added saved-prediction ablation comparison CLI with manifest-relative paths, SHA-256 input fingerprints, per-behaviour metrics, micro deltas, JSON/Markdown output, and input overwrite protection. Fixed zero-IoU threshold matching unrelated/disjoint events. Added usage and experiment limitations in `docs/ABLATIONS.md`. Verification: 92 unit tests passed, including CLI subprocess tests, outside sandbox after temporary-directory permissions blocked sandbox runs. Weekly usage: 21% used, 79% remaining. Actual pipeline variant execution and real accuracy measurements remain pending. |
| 7 Sep | Codex | Added P2 evaluation harness: `EventLabel`, greedy temporal-IoU matching by video/behaviour, per-behaviour and micro TP/FP/FN, precision/recall/F1, `n_gt`, `n_pred`, CSV and SQLite incident loaders, plus `scripts/evaluate_events.py`. Verification: `python -m pytest tests\unit -q` -> 83 passed; py_compile passed; CLI smoke against synthetic ground truth returned a valid JSON report; `npm run build` still passes. |
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

- [x] `handleguard/evaluation/ablations.py` + `scripts/compare_ablations.py` - saved-prediction comparison reports with provenance and deltas

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
- [x] `handleguard/evaluation/metrics.py` + `scripts/evaluate_events.py` — temporal-IoU event evaluation with counts and F1
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

Hardware for every row below: **Apple M3, 8 GB, MPS**. Input: 1920×1080 CCTV
downscaled to 1280×720, `imgsz=640`, `inference_fps=8`.

| Claim | Measured? | Where measured | Value |
|---|---|---|---|
| Detection latency, p50 | ✅ 8 Sep | `artifacts/evaluation/latency.json`, 80 frames of `0_tr1.mp4` | **37.6 ms** |
| Detection latency, p95 | ✅ 8 Sep | same | **78.7 ms** |
| End-to-end throughput | ✅ 8 Sep | same | **13.1 fps** |
| Tracking latency, p50 | ✅ 8 Sep | same | 0.5 ms |
| Feature + behaviour latency, p50 | ✅ 8 Sep | same | ≈0.1 ms combined |
| Detector on real industrial CCTV | ✅ 8 Sep | `7_tr1.mp4`, `4_te4.mp4`, one frame each | **57 and 52 detections**, classes person / cardboard box / hand trolley |
| Offline operation | ✅ 8 Sep | pipeline run with `socket.connect` patched to raise | completes in 8.3 s, **zero outbound connections** |
| Test suite | ✅ 8 Sep | `pytest -q` | **133 passing** |
| Clean-clone install | ✅ 8 Sep | fresh `git clone` to a temp dir, then `setup_offline.py` + `demo.sh --check` | **works — all assets present, CLIP reassembled, preflight OK** |
| Clean clone runs offline | ✅ 8 Sep | same clone, pipeline with `socket.connect` patched to raise | **ran in 7.4 s, zero network calls** |
| Repo size (clean clone) | ✅ 8 Sep | `du -sh` | 700 MB (detector 25 MB + CLIP chunks 338 MB + console 216 KB) |
| Demo console | ✅ 8 Sep | browser at `/` | renders; filters, separate risk/confidence columns, review controls, assistant panel; **12 behaviours shown** |
| Behaviours implemented | ✅ 8 Sep | `registry.build_all()` | **12 of 12, zero stubs** |
| Per-behaviour precision / recall | ❌ **NOT MEASURED** | — | **Blocked on footage. Do not quote a number.** |
| Ablation deltas on real video | ❌ **NOT MEASURED** | harness ready (`scripts/run_ablations.py`) | Blocked on footage |

**Caveats that must travel with these numbers:**

- The detect *mean* is 75.7 ms, skewed by a 2207 ms first-frame model warmup.
  **Quote p50, not mean**, and say warmup is excluded.
- Detection is ~99% of pipeline time. Tracking, features and behaviour reasoning
  are together under 1 ms — the temporal layer is effectively free, which is a
  genuinely good result and worth stating.
- 13.1 fps is offline batch throughput, **not** a real-time claim.
