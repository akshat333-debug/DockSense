# DockSense Task Sheet

Generated: 7 September 2026.

## Stop Condition

- Stop Codex work if weekly usage reaches 40% used or higher, because that means 60% or less remains.
- Last checked during this pass: weekly usage 12% used, 88% remaining.

## Critical Blockers

| Priority | Task | Owner | Status | Check |
|---|---|---|---|---|
| P0 | Record S1, S2, S3 warehouse-style footage using `docs/RECORDING_GUIDE.md` | Team | Blocked outside code | Raw clips exist in `data/raw/`, S3 untouched for tuning |
| P0 | Assign lanes for CV, backend, and frontend | Team | Blocked outside code | `STATE.md` Ownership rows no longer say `TBD` |
| P0 | Decide CLIP offline strategy: commit text embeddings/cache, vendor asset, or avoid runtime `set_classes()` | CV | Local cache prewarmed; clean-clone packaging still P2 | `YoloWorldDetector(...).set_classes()` runs from this workspace with WiFi off |

## Implementation Queue

| Priority | Task | Status | Check |
|---|---|---|---|
| P0 | `handleguard/video/reader.py`: timestamp-based OpenCV decoding to `Frame` | Done | Unit tests plus synthetic clip smoke test |
| P0 | `handleguard/perception/detector.py`: YOLO-World wrapper with MPS-to-CPU fallback | Implemented; prompt validation blocked | Unit tests pass; real synthetic smoke initializes but returns 0 detections |
| P0 | `handleguard/tracking/tracker.py`: ByteTrack wrapper and `NullTracker` | Done | ByteTrack selected when `lap` is installed; IDs stable across 10 s synthetic-like motion |
| P0 | `handleguard/behaviours/base.py`: `FrameContext`, `TrackHistory`, registry contract | Done | `registry.build_all(cfg)` returns 12 detectors |
| P0 | `tests/fixtures/synth.py`: synthetic track scenarios | Done | `make_ctx` produces valid `FrameContext` |
| P0 | B01/B02/B03/B07 detectors with negative tests first | Done | Positive scenarios fire; hard negatives stay silent |
| P0 | `handleguard/db/store.py`: SQLite incident store | Done | Round-trip query by behaviour, risk, band |
| P0 | `scripts/seed_fake_incidents.py` | Done | 40 clearly seeded demo incidents written to `data/processed/incidents.db` |
| P1 | Vite incident table | Not started | Renders and sorts seeded incidents |
| P1 | Vertical slice pipeline | Done for synthetic/fake-detector path; real YOLO prompt validation still blocked | Synthetic clip to incident in DB |
| P1 | Deduper, risk scorer, explanations, incident builder | Done | Continuous drop collapses to one incident |
| P1 | FastAPI endpoints | Done | `/incidents`, `/incidents/{id}`, `/stats`, `/chat`, `/clips/{file}` respond |
| P1 | Incident detail, clip playback, review controls | Not started | Evidence clip plays in browser |
| P1 | Offline assistant templates and guardrails | Not started | Cites incident IDs and refuses identity questions |
| P2 | Evaluation harness and ablations | Not started | P/R/F1 with n; ablation table with real deltas |
| P2 | Offline demo script, README attribution, slides, rehearsal | Not started | WiFi-off demo succeeds twice |

## Immediate Next After This Pass

1. Validate detector prompts on LOCO or real footage; procedural synthetic clips currently produce 0 YOLO-World detections even at low confidence.
2. Start P1 web UI: Vite incident table, incident detail, review controls, and clip playback against the API.
3. Record real S1/S2/S3 footage, assign team lanes, and validate YOLO-World prompts on real/public footage.
