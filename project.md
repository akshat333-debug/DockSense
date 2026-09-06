# DockSense — Project Definition

> **GATE 1 document.** No implementation code is written until the user confirms this
> file is correct and complete. Implementation plan lives in [plan.md](plan.md);
> day-to-day execution state in [STATE.md](STATE.md).

---

## 1. Problem statement

Warehouses already have cameras, but conventional CCTV produces **evidence after damage**, not prevention before it. Footage is reviewed only once a claim is filed, by which point the product is already damaged, the cause is contested, and the handling pattern that produced it has repeated many times unnoticed.

The gap is not recording. It is that nobody watches hours of footage, and a single frame cannot tell you whether a box was *placed* or *dropped* — that distinction lives in a sequence of frames, not in any one of them.

## 2. Objective

Convert existing warehouse video into **explainable, actionable, preventive operational intelligence**: identify risky handling *events*, explain why each was flagged with visible evidence, recommend an SOP-backed corrective action, and let a supervisor review, confirm, or reject each one — all without identifying individual workers.

## 3. Proposed solution

DockSense is a hybrid computer-vision and event-reasoning system. Rather than asking a model to label every frame "safe" or "unsafe," it tracks entities and builds short temporal interaction histories: what moved, where, how fast, whether contact occurred, whether support geometry became unstable, and what happened immediately before and after.

```
Video → Detection → Tracking → Temporal features → Event graph
      → Behaviour reasoning → Risk scoring → Incident + evidence clip
      → Dashboard / grounded assistant → Human review → Feedback
```

**Primary novelty:** a temporal event graph and a transparent, component-decomposed risk score, in place of an opaque frame classifier.

## 4. Target users

| User | Decision supported |
|---|---|
| Warehouse supervisor | Which events need attention now; fast replay and explanation |
| Loading/unloading operator | Timely, non-punitive guidance on safe handling |
| Logistics manager | Process-level risk patterns, bay comparison, preventable-loss indicators |
| Quality professional | Evidence linking handling events to inspection decisions |
| Safety professional | Repeatable behaviour taxonomy, audit trail, human-review workflow |

## 5. Functional requirements

| # | Requirement |
|---|---|
| FR1 | Ingest recorded video (MP4/AVI/MOV) via upload |
| FR2 | Detect warehouse entities: person, carton, large carton, pallet, trolley, pallet truck, forklift |
| FR3 | Track entities with persistent IDs across frames |
| FR4 | Compute scale-invariant temporal features: velocity, acceleration, floor gap, support relations, zone membership |
| FR5 | Detect **≥10** predefined behaviours from temporal evidence (12 implemented) |
| FR6 | Score each event 0–100 for risk, with a **separate** confidence value |
| FR7 | Deduplicate: one continuous event produces exactly one incident |
| FR8 | Generate an evidence clip (pre-roll + event + post-roll) and thumbnail per incident |
| FR9 | Produce an evidence-based explanation naming the observed quantities |
| FR10 | Recommend an SOP-backed corrective action |
| FR11 | Persist incidents with full evidence to a queryable database |
| FR12 | Dashboard: incident list with filters, detail view with replay, analytics |
| FR13 | Human review: confirm / false positive / needs investigation / note |
| FR14 | Assistant answering supervisor questions **grounded only** in stored incidents and SOPs, citing incident IDs |
| FR15 | Configurable zone polygons per camera |
| FR16 | Report per-behaviour precision/recall/F1 on a held-out session |
| FR17 | Ablation comparison substantiating the temporal-reasoning claim |

## 6. Non-functional requirements

| # | Requirement |
|---|---|
| NFR1 | **Runs fully offline.** No network at demo time. Weights, data, and frontend build all committed. |
| NFR2 | Runs on Apple M3 / 8 GB / MPS. No CUDA, no training. |
| NFR3 | Single command to start (`./scripts/demo.sh`) |
| NFR4 | Graceful degradation: if the LLM is unavailable, template explanations and a template assistant still work; if MPS fails, CPU fallback |
| NFR5 | No face recognition, no worker identity, no employee ranking, no automatic disciplinary output |
| NFR6 | Every reported metric is reproducible from committed code and committed config |
| NFR7 | Uploads validated for type and size; no arbitrary path reads; secrets only in `.env` |

## 7. Inputs and outputs

**Input:** an MP4 video file of a loading/unloading operation, plus (optional) camera zone configuration.

**Output:** a set of `Incident` records, each containing — behaviour id and name, start/end time, risk score 0–100 with band, confidence, per-component risk breakdown, involved track IDs, zone, evidence dict of measured quantities, explanation text, SOP recommendation, evidence clip path, thumbnail path, review status.

## 8. Behaviour taxonomy

| ID | Behaviour | Tier |
|---|---|---|
| B01 | Product dropped | **Robust** |
| B02 | Product thrown | **Robust** |
| B03 | Product dragged | Lightly validated |
| B04 | Rough handling / excessive impact | Lightly validated |
| B05 | Improper stack (large on small) | **Robust** |
| B06 | Unstable stack (insufficient support) | **Robust** |
| B07 | Product outside designated zone | **Robust** |
| B08 | Pallet overhang / insufficient support | **Robust** |
| B09 | Stepping / standing on product | Lightly validated |
| B10 | Large item handled without equipment present | Lightly validated |
| B11 | Unsafe loading sequence (narrow FSM) | Lightly validated |
| B12 | Movement through unsafe-surface zone | Lightly validated |

"Robust" = tuned on S1/S2 and measured on held-out S3. "Lightly validated" = implemented and demonstrated, insufficient held-out instances for a meaningful metric. **This distinction is stated in the submission, not hidden.**

## 9. Dataset decisions

**Dataset required: YES.** **Model training required: NO** — an open-vocabulary pretrained detector plus deterministic temporal/geometric rules is sufficient, and training is infeasible on 8 GB / MPS within the deadline. This is a deliberate architectural choice, not a compromise: rule-based temporal reasoning is *more* explainable, which is a scored criterion.

### 9.1 Public datasets used

| Dataset | Source | License | Version / date | Why it fits |
|---|---|---|---|---|
| **Safe and Unsafe Behaviours** (Unsafe-Net) | https://data.mendeley.com/datasets/xjmtb22pff/1 · mirror https://huggingface.co/datasets/Voxel51/Safe_and_Unsafe_Behaviours | **CC BY 4.0** | v1, published 11 June 2024; footage recorded 5 Nov – 13 Dec 2022 | 691 real industrial CCTV clips, 1920×1080 @ 24 fps, 1–20 s. Class "Safe Walkway Violation" maps to **B07**; "Safe Walkway" and "Safe Carrying" are genuine **hard negatives**. Real CCTV viewpoint and lighting, which staged footage cannot supply. |
| **LOCO — Logistics Objects in Context** | https://github.com/tum-fml/loco (TUM) | **CC BY 4.0** | v1 release | 5,593 bbox-annotated images, 151k instances of pallets, small load carriers, stillages, forklifts, pallet trucks. Used to **validate YOLO-World prompt strings** against real logistics scenes before any of our own footage exists. |

**Attribution:** both are CC BY 4.0 and require credit. Attribution block goes in `README.md` and on the submission slide citing datasets.

### 9.2 Self-recorded data

**No public dataset labels product drop / throw / drag / stacking events in a warehouse.** This was verified by search during planning; it is the reason the challenge is non-trivial. Therefore self-recorded footage is **mandatory** for B01, B02, B05, B06, B08.

- Protocol: `docs/RECORDING_GUIDE.md`
- Structure: three sessions (S1 near, S2 far, S3 elevated/angled)
- **S3 is held out and never tuned on.** Split is by *session*, not by clip or frame, to prevent temporal leakage.
- Participants are project members; footage contains no third parties; no identity data is stored or derived.
- Ground truth: event intervals in `data/raw/takes.csv`.

### 9.3 Leakage controls

- Split by recording session, never by frame or clip.
- Thresholds tuned on S1/S2 only; every tuning change logged in `STATE.md` with the session it was tuned against.
- S3 evaluated exactly once, at the end. Reported whatever the result.
- Hard negatives recorded deliberately (gentle placement, carrying at low height, trolley movement, correct stacking, transient zone crossing, 30 s of fully normal operation).

## 10. Technology

| Layer | Choice |
|---|---|
| Runtime | Python 3.13, torch 2.10 (MPS), Node 24 |
| Detection | Ultralytics YOLO-World (`yolov8s-worldv2`), open-vocabulary, zero training |
| Tracking | ByteTrack via ultralytics |
| Geometry | NumPy, OpenCV, Shapely |
| Backend | FastAPI + Uvicorn |
| Database | SQLite via stdlib `sqlite3`, no ORM |
| Frontend | React + Vite, build output committed |
| Video | OpenCV decode, ffmpeg for clip extraction |
| Assistant | Template intent-matcher (offline, default) + optional Anthropic tool-use path behind `ANTHROPIC_API_KEY` |

## 11. Architecture

Strictly one-directional; see [plan.md](plan.md) for module tables and the detector contract.

```
video → perception → tracking → features → events → behaviours → risk → incidents → db → api → web
                                                                              ↘ assistant ↗
```

The CV core imports nothing from the database or web layers, enforced by a test.

## 12. Constraints

- **Deadline 10 September 2026.**
- Apple M3, 8 GB unified memory, MPS backend, no CUDA.
- Three people working in parallel lanes with AI coding agents, coordinating through `STATE.md`.
- Demo must run with the network disabled.

## 13. Assumptions

- Camera is fixed during a recording session (hand-held motion produces false velocity).
- One loading/unloading process, 1–2 camera views.
- Product weight is **not** observable; size is used as an explicitly-labelled proxy.
- No camera calibration, so all quantities are **object-relative**, never absolute metres.
- Participants consent to appearing in recorded footage.

## 14. Responsible AI position

- Analyses **behaviour, not identity**. No face recognition, no re-identification, no worker names, no ranking.
- Optional face blurring (Gaussian, top region of person box) on stored clips.
- Distinguishes **observed event** from **inferred risk** from **confirmed damage**. Only the first is asserted; damage is never claimed.
- Never infers intent. B10 is named "large item handled without equipment present" — an observation, not a judgment.
- Alerts are decision support subject to human review; the system produces no disciplinary output.
- Risk and confidence are always displayed separately.
- Track IDs reset per session; configurable retention.

## 15. Acceptance criteria

| # | Criterion | How verified |
|---|---|---|
| AC1 | Clean install from committed repo succeeds | Fresh venv, `pip install -r requirements.txt` |
| AC2 | Backend and frontend start with one command | `./scripts/demo.sh` |
| AC3 | Detector loads and produces detections on real footage | `/health` reports detector loaded |
| AC4 | Tracker maintains IDs across a 10 s clip | Visual check + ID-switch count logged |
| AC5 | ≥10 behaviours implemented and demonstrable | One demo clip per behaviour |
| AC6 | Risk and confidence stored and displayed separately | Incident detail view |
| AC7 | One continuous drop → exactly one incident | Automated deduper test |
| AC8 | Evidence clip generated and plays in browser | Manual playback |
| AC9 | Explanation cites measured quantities, claims no damage or intent | Review of generated text |
| AC10 | Assistant cites incident IDs, says "No matching incidents found." when empty, refuses identity questions | Automated guardrail tests |
| AC11 | Per-behaviour P/R/F1 reported on held-out S3, with n shown | `scripts/evaluate.py --split S3` |
| AC12 | Ablation table with ≥2 rows showing real deltas | `scripts/ablation.py` |
| AC13 | Full demo runs with network disabled | Two rehearsals |
| AC14 | No fabricated numbers anywhere in README or deck | Claims ledger in `STATE.md` |

## 16. Definition of Done

The project is done when **all** of the following hold:

1. All 14 acceptance criteria pass.
2. Every number in the README and the deck has a row in the `STATE.md` claims ledger naming where it was measured.
3. The scope ledger (robust vs lightly validated) appears in the submission verbatim — no behaviour is implied to be better validated than it is.
4. S3 held-out metrics are reported **as measured**, including bad results, with sample sizes shown.
5. Two full offline rehearsals completed with no critical failure.
6. Dataset attribution (CC BY 4.0 for both public datasets) present in README and slides.
7. No secrets, no `.env`, no large model caches or raw footage committed.
8. Repo builds and runs from a clean clone.

---

## Open items requiring user confirmation (GATE 1)

1. **Deadline is now 3 days, not 4** — it is 7 Sept. Day 0 tasks are compressed into this morning. Confirm 10 Sept is still the submission date.
2. **Filming must happen today.** Everything in the "robust" tier depends on it. Confirm who and when.
3. **Team lane assignment** — `STATE.md` still shows all three lanes as `TBD`.
4. **Unsafe-Net is 10 GB.** Confirm we should pull the full set, or a per-class subset (~2 GB) covering only the four classes we can use.
