# DockSense — Full Implementation Plan

> Approved 6 Sept 2026. Living document — if reality diverges, update this file, don't
> let it go stale. Day-by-day execution state lives in [STATE.md](STATE.md).

## Context

**What this is.** DockSense (formerly HandleGuard AI) is a hackathon submission for the "AI Video Intelligence for Warehouse Handling" challenge. It ingests warehouse loading/unloading video, detects and tracks objects, reasons over *temporal sequences* to identify risky handling behaviours, scores each event 0–100 with a separate confidence value, creates an incident with an evidence clip and an evidence-based explanation, serves a supervisor dashboard, and answers questions through an assistant grounded strictly in the incident database.

**Why now, and what's wrong.** Two planning documents exist (`HandleGuard_AI_Complete_Project_Master_Plan.md`, 3,480 lines; `HandleGuard_AI_Warehouse_Proposal.pdf`, 16 pages). Both are strong on *what* to build and silent on the two things that decide whether it ships:

1. **The deadline already moved.** Both docs plan a six-day sprint starting 4 Sept. Today is **6 Sept**, submission is **10 Sept**, and the repo contains zero lines of code. Day 1 and Day 2 exit conditions are both unmet. Every estimate in both documents is stale.
2. **No footage exists.** Every threshold, metric, demo scenario and screenshot is downstream of video nobody has recorded.

**Intended outcome.** A working, offline-runnable prototype that demonstrates ≥10 behaviours, of which six are tuned and measured on held-out footage, with an ablation table that substantiates the "temporal reasoning" innovation claim. Every number reported is one that was actually run.

**Guiding principle:** when a fix could be "reword it" or "rebuild it," surface the fork rather than silently taking the faster path. Concretely here — six measured behaviours plus six honestly-labelled ones beats twelve unmeasured ones, and it beats them in front of a judge.

---

## Research findings that changed the plan

Sourced live during planning, because the workflow discipline mandates public datasets with documented licenses.

| Dataset | License | Contents | What it buys us |
|---|---|---|---|
| [Unsafe-Net / Safe & Unsafe Behaviours](https://data.mendeley.com/datasets/xjmtb22pff/1) (Önal & Dandıl 2024) — [HF mirror](https://huggingface.co/datasets/Voxel51/Safe_and_Unsafe_Behaviours) | **CC BY 4.0** | 691 clips, 1920×1080 @ 24fps, 1–20 s, real industrial CCTV, 10 GB. Classes: Safe Walkway **Violation**, Unauthorized Intervention, Opened Panel Cover, Carrying Overload with Forklift / Safe Walkway, Authorized Intervention, Closed Panel Cover, **Safe Carrying** | Real CCTV for **B07 zone violation** + genuine **hard negatives** (Safe Walkway, Safe Carrying). Already cited in the proposal's Appendix B — using it closes that loop. |
| [LOCO](https://github.com/tum-fml/loco) (TUM) | **CC BY 4.0** | 5,593 bbox-annotated images, 151k instances: pallets, small load carriers, stillages, forklifts, pallet trucks | Validates YOLO-World prompt strings on *real* logistics scenes **before any footage exists**. Removes the biggest day-1 unknown. |

**The finding that matters:** no public dataset labels product **drop / throw / drag / stacking** events in a warehouse. That is precisely why the challenge is interesting, and it means **self-recorded footage remains mandatory** for four of the six flagship behaviours. Public data supplements; it does not substitute.

**Consequence:** tonight is a *download* night, not a filming night. Filming moves to tomorrow morning without costing the critical path.

---

## Decisions locked

| Decision | Rationale |
|---|---|
| **YOLO-World** open-vocab detector, zero training | 8 GB M3 / MPS, no CUDA. Training is infeasible at any scale. Text prompts from `configs/products.yaml`. Verified: `YOLOWorld` + `.set_classes()` present in installed ultralytics 8.4.14. |
| **All thresholds in object-heights, not pixels** | Pixel thresholds silently stop firing when the camera moves. Also a real technical answer to "how does this generalize?" |
| **Session-based split; S3 held out, never tuned on** | The only way a reported metric survives a judge. |
| **6 robust + 6 labelled "lightly validated"** | Satisfies "≥10 behaviours" while keeping every reported number honest. |
| **React + Vite, built and vendored** | Build output committed so the demo needs no network and no `npm install`. |
| **Assistant: offline template path first, LLM behind env var** | Template path is the demo path. `ANTHROPIC_API_KEY` placeholder until supplied. |
| **SQLite via stdlib `sqlite3`, no ORM** | One fewer dependency; incident schema is a single table. |
| **Model weights committed to `models/`** | ~25 MB. Offline demo dies without this. |

---

## Architecture

### The one rule

```
video → perception → tracking → features → events → behaviours → risk → incidents → db → api → web
                                                                              ↘ assistant ↗
```

Strictly one-directional. `handleguard/{video,perception,tracking,features,events,behaviours,risk}` import **nothing** from `db`, `incidents`, `apps.api`, fastapi, or sqlalchemy. The CV core emits plain dataclasses; `incidents` is the only module that knows persistence exists.

Enforced by `tests/unit/test_import_hygiene.py` — this is what stops three parallel agents turning the repo into a ball of mud by day 2.

### Modules

Package root `handleguard/`. Directories already scaffolded and empty.

| Module | Files | Public interface | Depends on |
|---|---|---|---|
| **`types.py`** (new, root) | one file | All shared dataclasses: `Frame`, `Detection`, `Track`, `TrackFeatures`, `BehaviourEvent`, `RiskScore`, `Incident` | stdlib + numpy only |
| **`config.py`** (new, root) | one file | `load(name)`, `behaviours()`, `products()`, `risk_weights()`, `sop_rules()`, `zones()` — cached YAML | pyyaml |
| `video/` | `reader.py`, `clipper.py` | `iter_frames(path, inference_fps=8, max_res)` → `Iterator[Frame]`; `extract_clip(...)`, `thumbnail(...)` | cv2, ffmpeg |
| `perception/` | `detector.py`, `geometry.py` | `YoloWorldDetector.__call__(frame) → list[Detection]`; pure geometry fns | ultralytics, types |
| `tracking/` | `tracker.py` | `Tracker.update(dets, frame) → list[Track]`; plus `NullTracker` for the ablation | ultralytics bytetrack |
| `features/` | `state.py`, `compute.py`, `zones.py`, `floor.py`, `support.py` | `FeatureExtractor.update(tracks, frame) → dict[int, TrackFeatures]` | types, geometry |
| `behaviours/` | `base.py`, `registry.py`, `b01_drop.py` … `b12_wet_floor.py` | See contract below | types, config |
| `events/` | `dedup.py`, `graph.py`, `fsm.py` | `EventDeduper.push(ev)`; `EventGraph.chains()`; `SopFSM` | types, config |
| `risk/` | `scorer.py`, `explain.py` | `score(ev, feats, history, cfg) → RiskScore`; `explain(ev, risk) → str` | types, config |
| `incidents/` | `builder.py`, `sop.py` | `build(ev, risk, video_meta, clip_dir) → Incident` | video.clipper, db |
| `db/` | `store.py` | `IncidentStore`: `init/add/query/get/stats/counts_by_behaviour` | sqlite3 |
| `assistant/` | `tools.py`, `templates.py`, `agent.py` | `answer(question, store) → Answer(text, cited_ids, mode)` | db, config |
| `metrics/` | `evaluate.py`, `ablation.py` | temporal-IoU event matching → P/R/F1; ablation table writer | types, db |
| `privacy/` | `redact.py` | `blur_faces(frame, person_boxes)` — Gaussian blur, top 25% of person box. No face detector. | cv2 |
| **`pipeline.py`** (new, root) | one file | `run(video_path, *, flags, sink, cfg) → list[Incident]` — **the only place modules are composed** | all of the above |

`apps/api/` — `main.py` + `routes/{incidents,chat,ingest}.py`. Endpoints: `GET /incidents`, `GET /incidents/{id}`, `GET /stats`, `GET /clips/{file}`, `POST /chat`. Ingest is a background job writing status to a dict; no celery, no redis.

`apps/web/` — React + Vite. Three views: incident table (risk and confidence in **separate columns**, band-coloured), incident detail (clip + explanation + risk-component breakdown + SOP), chat panel. **`dist/` is committed** so the demo runs with no network and no install.

### The `BehaviourDetector` contract — the load-bearing decision

Twelve detectors written in parallel by three agents only stays coherent if the contract is airtight. `base.py` and `types.py` are **frozen after day 1 morning**.

```python
class FrameContext:
    """Read-only. Built once per inference frame, passed to all 12 detectors."""
    frame_index: int; t: float; dt: float; fw: int; fh: int
    tracks: dict[int, Track]
    feats:  dict[int, TrackFeatures]      # already scale-normalized
    history: TrackHistory                  # ~5 s per-track lookback
    zones: ZoneMap; floor: FloorModel
    cfg: dict
    recent_events: Sequence[BehaviourEvent]   # deduped; for B11 + frequency

    # convenience accessors — why detectors stay ~40 lines each
    def persons(self) -> list[int]; def products(self) -> list[int]
    def by_role(self, role) -> list[int]; def f(self, tid) -> TrackFeatures
    def window(self, tid, seconds) -> list[TrackFeatures]
    def overlapping(self, tid, role=None, min_iou=0.05) -> list[int]
    def below(self, tid) -> list[int]

class BehaviourDetector(ABC):
    id: str; name: str; config_key: str
    requires_roles: set[str] = {"product"}
    @abstractmethod
    def update(self, ctx: FrameContext) -> list[BehaviourEvent]: ...
    def reset(self) -> None: ...
```

**Five rules, verbatim in `base.py`'s docstring and in `STATE.md`:**

1. A detector **never** deduplicates, cools down, or scores risk. It fires whenever its condition holds. `EventDeduper` owns cooldown; `risk.scorer` owns scoring. This single rule removes the largest source of twelve inconsistent implementations.
2. A detector reads thresholds **only** from `self.cfg`. No numeric literals in detector bodies. Need a new threshold → add it to `behaviours.yaml` under your key.
3. All distances in object-heights, all velocities in object-heights/sec. **A detector touching raw `xyxy` is a bug** — `grep xyxy handleguard/behaviours/` is a review check.
4. `severity` starts at config `base_severity`, may be scaled ±0.15 by magnitude. `confidence` comes from the shared helper `base.confidence_from(margin, track_conf)` so all twelve agree.
5. `evidence` dict values must be JSON-serializable scalars — they render into explanations.

`__init__.py` gets all twelve `from . import bNN_x` lines **on day 1 with stub classes**, so it is never edited again and never conflicts.

---

## Execution — 4 days, 3 lanes

Lanes own directories. No two lanes edit the same file.

- **Lane A — Perception/Core:** `types.py`, `config.py`, `video/`, `perception/`, `tracking/`, `features/`, `pipeline.py`
- **Lane B — Reasoning:** `behaviours/`, `events/`, `risk/`, `incidents/`, `metrics/`
- **Lane C — Product:** `db/`, `assistant/`, `apps/api/`, `apps/web/`, `scripts/`

**What is actually blocked on footage:** threshold tuning, prompt validation, S3 metrics, ablation numbers, demo clip selection. **That is all.** Every line of code can be written and unit-tested first, because `FrameContext` is constructible from synthetic tracks.

### Day 0 — tonight, 6 Sept (~1 h, mostly unattended)

1. **Write `project.md`** — problem, objective, requirements, I/O, dataset decisions + licenses, acceptance criteria, Definition of Done. → **GATE 1: user confirms before any code.**
2. **Download and cache `yolov8s-worldv2.pt` into `models/`, commit it.** Offline demo depends on this.
3. **Download public data:** LOCO annotated images; Unsafe-Net subset (Safe Walkway Violation, Safe Walkway, Safe Carrying, Carrying Overload). Record source URL, CC BY 4.0 license, version and date in `project.md`.
4. **Validate YOLO-World prompts against LOCO images tonight** — this is the day-1 unknown removed a day early, with zero footage required.

### Day 1 — 7 Sept

- **Morning, all hands: film S1 + S2** per `docs/RECORDING_GUIDE.md`. ~2–3 h. Hard negatives are not optional.
- **A:** `types.py`, `config.py`, `video/reader.py`, `perception/geometry.py`, `perception/detector.py`. **Benchmark MPS end of day** — fps at 720p/8 inference-fps, peak RAM. Post the number in `STATE.md`; later decisions depend on it.
- **B:** `behaviours/base.py`, `FrameContext`, `TrackHistory`, `registry`, and **`tests/fixtures/synth.py`**. Then B01, B02, B03, B07 with unit tests — all green with zero video.
- **C:** `db/store.py` + schema + `scripts/seed_fake_incidents.py` (40 plausible incidents). Vite scaffold + incident table against fake data. **Lane C is demoable on day 1 and never blocked again.**
- **Freeze `types.py` + `base.py` by midday.**

### Day 2 — 8 Sept

- **A:** `tracking/`, `features/*`, `pipeline.py` wired end to end. **First real incident from real footage by EOD — the day's only real goal.**
- **B:** B05, B06, B08, B09, B12 + `events/dedup.py` + `risk/scorer.py` + `explain.py` + `incidents/builder.py`, all synthetically tested.
- **C:** `assistant/templates.py` offline path + `/chat` + chat UI + incident detail with clip playback. **Clip-playability spike early** — `ffmpeg -c copy` clips frequently won't play in `<video>`; fall back to `-c:v libx264 -preset ultrafast`.

**→ GATE 2 (day-2 EOD go/no-go):** if the pipeline has not produced one real incident from real footage, cut scope per the ledger below.

### Day 3 — 9 Sept

- **All hands on tuning.** Thresholds tuned on **S1/S2 only**, every change logged in `STATE.md`. This is the day footage debt gets paid.
- **A:** perf tuning, `clipper` finalization, privacy blur.
- **B:** `events/graph.py`, B11 (narrow 2-state FSM, not a general SOP model), B04, B10, `metrics/evaluate.py`, ablation harness.
- **C:** LLM tool-use path (key arriving), polish, `scripts/demo.sh` — one command, offline, deterministic.
- **EOD: full offline rehearsal with WiFi off. Non-negotiable.**

### Day 4 — 10 Sept (half day)

- Run **S3 held-out evaluation exactly once**. Report those numbers whatever they are.
- Ablation table → README. Submission writeup using the scope ledger verbatim.
- Audits: requirements / code / ML / security.
- Second offline rehearsal. **Freeze at noon.** → **GATE 3: ask before commit + push.**

---

## Testing — only what earns its cost

Four categories, ~35 tests, all sub-second, none needing video.

1. **Synthetic track fixtures** (`tests/fixtures/synth.py`) — highest ROI in the plan. `synth_track(...)`, `make_ctx(...)`, and named scenario generators. Each detector gets **exactly two tests: positive scenario fires, hard-negative scenario does not**. `scenario_gentle_place` must not trigger drop; `scenario_carry` must not trigger drag. **Write the negative test first** — a detector that fires on everything is what kills demos.
2. **Risk renormalization** — components dropped → remaining weights still sum to 1.0 with ratios preserved; score in [0,100]; band boundaries at 24/25, 49/50, 74/75.
3. **Deduper** — 40 consecutive identical drop events 0.125 s apart → exactly **1** incident with `end_t - start_t ≈ 5 s`. This is a stated requirement, so it gets an explicit test.
4. **Assistant guardrails** — "who dropped the most boxes?" → refusal; empty DB → "No matching incidents found."; populated query → answer contains an incident ID.

Plus `test_import_hygiene.py`.

**Explicitly skipped:** integration tests over real video (you'll be watching anyway), API route tests (the UI is the test), tracker tests (not our code), any mocking of ultralytics.

---

## Risk register

| # | Risk | Mitigation |
|---|---|---|
| R1 | **Footage slips past day 1** | Public data (LOCO + Unsafe-Net) covers prompt validation and B07 tonight. Filming is a 2-h morning task, not a project. |
| R2 | **8 GB / MPS too slow — YOLO-World is heavy** | Offline batch processing only; **never claim realtime**. 720p, 8 inference fps, `imgsz=640`. If <2 fps: 480p / 4 fps and pre-render demo videos to `data/processed/`. Benchmark day 1, not day 3. MPS OOM kills the process — wrap detector calls with a CPU fallback rather than crashing mid-demo. |
| R3 | **Weight download at demo time** | Committed to `models/` day 0. `scripts/demo.sh` asserts the file exists. |
| R4 | **YOLO-World prompts miss your boxes** | Prompts are a *threshold*, not a given. Validate on LOCO tonight; budget 45 min iterating strings ("cardboard box" → "box" → "brown box"). |
| R5 | **Track ID switching breaks temporal behaviours** | Not fixable in 4 days. Keep behaviour windows ≤2 s so an ID switch costs one event, not all. Report ID-switch rate as a known limitation — that honesty scores better than a broken demo. |
| R6 | **Threshold overfitting to ~20 min of footage** | Structurally handled: S3 held out, tuning provenance logged. Report S3 numbers even if bad; state that small-n confidence intervals are wide. |
| R7 | **Three agents diverge on interfaces** | `types.py` + `base.py` frozen day 1 midday; import-hygiene test; all twelve `__init__.py` lines added upfront. |
| R8 | **Clips don't play in browser** | Spike day 2, not day 4. Re-encode fallback ready. |
| R9 | **Ablation table shows no difference** | `use_tracking=False` → `NullTracker` genuinely degrades. That row carries the table. |

### The three weak behaviours — argued, not hand-waved

- **B04 rough handling** — weakest. "Rough" has no geometric definition; the proxy is acceleration, the *second* derivative of a jittery bbox centroid at 8 fps. Detector re-fitting on a partly-occluded carton produces spikes indistinguishable from real ones. It also overlaps B01/B02 by construction — every real drop spikes acceleration, so it mostly fires as a duplicate of things detected better elsewhere. Keep enabled, threshold conservatively high, label lightly-validated.
- **B10 manual heavy handling** — can see "person overlaps large box, no trolley nearby"; **cannot see mass**, and mass is the entire concept. Also brushes the "never infer intent" line. **Rename it in the UI to "large item handled without equipment present"** — an observation rather than a judgment. More honest and more defensible simultaneously.
- **B11 unsafe sequence** — not weak in concept, weak because it *compounds*: its precision is roughly the product of its dependencies'. A missed B05 breaks the FSM; an ID switch splits one entity's chain in two. **Build the event graph anyway** (cheap, needed for the frequency component and the UI timeline) but implement B11 as a 2-state FSM over one *reliable* behaviour pair. One demonstrable chain beats a general FSM that never fires; the graph visualization carries the innovation claim regardless.

Strong by contrast — **B01, B02, B05, B06, B07, B08** — single-object kinematics with clean thresholds, or static geometric relations between two boxes. B07 is nearly free and near-perfect. Lead the demo with B01, B05/B06, B07.

---

## Scope ledger — goes in the submission verbatim

**Robustly demonstrated** (tuned on S1/S2, measured on S3): B01 drop, B02 throw, B05 improper stack, B06 unstable stack, B07 zone violation, B08 pallet overhang. Plus full risk scoring with component breakdown and separate confidence; deduplication (demo the 40-frames→1-incident case explicitly, it's a strong slide); incident DB, dashboard, clip evidence, templated explanations, SOP recommendations; offline grounded assistant with citations and refusals; ablation table with at least `use_tracking` and `use_smoothing` rows.

**Implemented, lightly validated** (stated in exactly these words): B03 drag, B09 stepping, B12 wet floor — plausible, few held-out instances. B04, B10 — proxy heuristics with named confounds. B11 — narrow FSM; event graph itself is real and visualized. LLM assistant path — offline template path is what's demoed.

**Explicitly out of scope, stated up front:** real-time inference, multi-camera, worker identification, damage confirmation, any trained model, absolute-metric measurement (no calibration → all thresholds object-relative, which is a design choice, not an omission).

**Cut order if GATE 2 fails:** B04 → B10 → B11 → B03 → B09 → LLM path → ablation down to one row. **Never cut:** dedup, separate confidence, S3 held-out reporting, offline operation.

---

## Verification

**Per module:** expected input → expected output → invalid input → edge case → integrate → verify integrated output. One file at a time; never a whole backend in one pass.

**End to end:**
```bash
pytest tests/ -q                                   # ~35 tests, all green, no video needed
python scripts/run_video.py data/raw/S1_drop_01.mp4 --show
python -m handleguard.pipeline data/raw/S3_mixed.mp4   # held-out, once
python scripts/evaluate.py --split S3               # per-behaviour P/R/F1 with n shown
python scripts/ablation.py --video data/raw/S1_mixed.mp4   # → artifacts/evaluation/ablation.md
./scripts/demo.sh                                   # one command, WiFi OFF
```

**Clean-environment check:** fresh venv → `pip install -r requirements.txt` → `cp .env.example .env` → `./scripts/demo.sh` → dashboard loads, incidents render, clips play, chat answers with citations. "Works on my machine" does not count.

**Demo rehearsal:** twice, both with the network disabled. Day 3 EOD and day 4.

---

## Gates — non-negotiable

1. **After `project.md` is drafted** → user confirms requirements before any code.
2. **Day-2 EOD** → one real incident from real footage, or cut scope per the ledger.
3. **Before every commit/push** → always ask, even though earlier gates passed.

Commits carry no `Co-Authored-By` trailer (contributor-graph preference).
