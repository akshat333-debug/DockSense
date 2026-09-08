# DockSense Task Sheet

Generated: 7 September 2026.

## Stop Condition

- Stop Codex work if weekly usage reaches 40% used or higher, because that means 60% or less remains.
- Last checked during this pass: weekly usage 21% used, 79% remaining.

## Critical Blockers

| Priority | Task | Owner | Status | Check |
|---|---|---|---|---|
| P0 | Record S1, S2, S3 warehouse-style footage using `docs/RECORDING_GUIDE.md` | Team | Blocked outside code | Raw clips exist in `data/raw/`, S3 untouched for tuning |
| P0 | Assign lanes for CV, backend, and frontend | Team | **Done 8 Sep** — A=Akshat, B=Anirudh, C unassigned (interim split) | `STATE.md` Ownership |
| P0 | CLIP offline strategy | CV | **Done 8 Sep** — shipped as 4 chunks in `models/clip_parts/`, reassembled by `scripts/setup_offline.py` with SHA256 check | Verified with sockets blocked: 8.3 s run, zero network calls |

## Implementation Queue

| Priority | Task | Status | Check |
|---|---|---|---|
| P0 | `handleguard/video/reader.py`: timestamp-based OpenCV decoding to `Frame` | Done | Unit tests plus synthetic clip smoke test |
| P0 | `handleguard/perception/detector.py`: YOLO-World wrapper with MPS-to-CPU fallback | **Done.** Prompts verified on real CCTV: 57 and 52 detections, correct classes. The 0-detection result on synthetic clips is expected and unfixable (flat rectangles vs a photo-trained model) | Real-footage smoke test |
| P0 | `handleguard/tracking/tracker.py`: ByteTrack wrapper and `NullTracker` | Done | ByteTrack selected when `lap` is installed; IDs stable across 10 s synthetic-like motion |
| P0 | `handleguard/behaviours/base.py`: `FrameContext`, `TrackHistory`, registry contract | Done | `registry.build_all(cfg)` returns 12 detectors |
| P0 | `tests/fixtures/synth.py`: synthetic track scenarios | Done | `make_ctx` produces valid `FrameContext` |
| P0 | B01/B02/B03/B07 detectors with negative tests first | Done | Positive scenarios fire; hard negatives stay silent |
| P0 | `handleguard/db/store.py`: SQLite incident store | Done | Round-trip query by behaviour, risk, band |
| P0 | `scripts/seed_fake_incidents.py` | Done | 40 clearly seeded demo incidents written to `data/processed/incidents.db` |
| P1 | Vite incident table | Done | Renders and sorts seeded incidents |
| P1 | Vertical slice pipeline | **Done**, and verified end to end on real CCTV (~7.4 fps warm) | Real clip through full pipeline |
| P1 | Deduper, risk scorer, explanations, incident builder | Done | Continuous drop collapses to one incident |
| P1 | FastAPI endpoints | Done | `/incidents`, `/incidents/{id}`, `/stats`, `/chat`, `/clips/{file}` respond |
| P1 | Incident detail, clip playback, review controls | Done | Evidence clip plays in browser when `clip_path` exists |
| P1 | Evidence clip extraction | Done | Pipeline writes MP4 clip and JPEG thumbnail paths |
| P1 | Offline assistant templates and guardrails | Done | Cites incident IDs and refuses identity questions |
| P2 | Evaluation harness | Done | P/R/F1 with n from temporal-IoU event matching |
| P2 | Ablation comparison reports | Done for saved prediction CSVs | Manifest-driven JSON/Markdown reports, input hashes, counts and baseline deltas; CLI tests pass |
| P2 | Pipeline variant execution and measured ablations | **Done 8 Sep** — `PipelineFlags` wired to real mechanisms, `scripts/run_ablations.py` executes variants. Tests assert flags change behaviour; `no_tracking` loses the drop entirely | `python scripts/run_ablations.py` |
| P2 | Latency instrumentation | Not started | Per-stage p50/p95 on documented hardware and inputs |
| P1 | Remaining behaviours B04-B06, B08-B12 | **Done 8 Sep — all 12 implemented, zero stubs.** Real-footage validation still pending | Each has a positive test and a named hard negative |
| P2 | Offline demo script, README attribution, slides, rehearsal | `scripts/demo.sh` + README with CC BY 4.0 attribution **done**. Slides and the two rehearsals still outstanding | WiFi-off demo succeeds twice |

## Immediate Next After This Pass

Rewritten 8 Sep. Items 1 and 2 of the previous list are done; the event graph now
exists (`handleguard/events/graph.py`) and ablations are executable.

1. **Record S1/S2/S3 footage.** The only remaining critical-path item, and the
   only one that converts this project from "built" to "measured".
2. Latency p50/p95 instrumentation (`handleguard/metrics/`), not gated on footage.
3. Once footage lands: tune on S1/S2 (log which session), run S3 **once**, run the
   ablation table on real video, fill the claims ledger.
4. Screenshots, 5-6 slide deck, demo recording, two WiFi-off rehearsals.
