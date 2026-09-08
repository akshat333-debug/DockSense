"""Per-stage latency instrumentation.

Reporting a single average frame time hides the thing that matters: a pipeline
that is fast on average but has a slow tail still drops frames and still misses
events. So this records every stage separately and reports p50 and p95 alongside
the mean.

Designed to cost nothing when unused — `Timings` is only created if the caller
asks for it, and `stage()` is a plain context manager over `perf_counter`.

    timings = Timings()
    with timings.stage("detect"):
        dets = detector(frame)
    print(timings.report())
"""

from __future__ import annotations

import statistics
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator

# Order stages are reported in — pipeline order, so a report reads like the
# pipeline runs rather than alphabetically.
STAGE_ORDER = ("decode", "detect", "track", "features", "behaviours", "risk", "evidence")


@dataclass
class StageStats:
    stage: str
    count: int
    mean_ms: float
    p50_ms: float
    p95_ms: float
    max_ms: float
    total_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "count": self.count,
            "mean_ms": round(self.mean_ms, 2),
            "p50_ms": round(self.p50_ms, 2),
            "p95_ms": round(self.p95_ms, 2),
            "max_ms": round(self.max_ms, 2),
            "total_ms": round(self.total_ms, 2),
        }


@dataclass
class Timings:
    """Collects per-stage wall-clock samples."""

    samples: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            self.samples[name].append((time.perf_counter() - start) * 1000.0)

    def record(self, name: str, ms: float) -> None:
        self.samples[name].append(float(ms))

    def stats(self) -> list[StageStats]:
        out: list[StageStats] = []
        known = [s for s in STAGE_ORDER if s in self.samples]
        extra = sorted(k for k in self.samples if k not in STAGE_ORDER)
        for name in known + extra:
            values = sorted(self.samples[name])
            if not values:
                continue
            out.append(
                StageStats(
                    stage=name,
                    count=len(values),
                    mean_ms=statistics.fmean(values),
                    p50_ms=_percentile(values, 0.50),
                    p95_ms=_percentile(values, 0.95),
                    max_ms=values[-1],
                    total_ms=sum(values),
                )
            )
        return out

    def to_dict(self) -> dict[str, Any]:
        rows = self.stats()
        frames = max((r.count for r in rows), default=0)
        wall_ms = sum(r.total_ms for r in rows)
        return {
            "frames": frames,
            "stages": [r.to_dict() for r in rows],
            "total_ms": round(wall_ms, 2),
            "fps_end_to_end": round(frames / (wall_ms / 1000.0), 2) if wall_ms else 0.0,
        }

    def report(self) -> str:
        rows = self.stats()
        if not rows:
            return "no timing samples collected"
        width = max(len(r.stage) for r in rows)
        lines = [f"{'stage'.ljust(width)}   n    mean     p50     p95     max"]
        for r in rows:
            lines.append(
                f"{r.stage.ljust(width)} {r.count:>3} "
                f"{r.mean_ms:>7.1f} {r.p50_ms:>7.1f} {r.p95_ms:>7.1f} {r.max_ms:>7.1f}   (ms)"
            )
        d = self.to_dict()
        lines.append(f"end-to-end: {d['fps_end_to_end']} fps over {d['frames']} frames")
        return "\n".join(lines)


def _percentile(sorted_values: list[float], q: float) -> float:
    """Nearest-rank percentile.

    No interpolation: with the small sample counts a short clip produces,
    interpolating invents a number between two real measurements.
    """
    if not sorted_values:
        return 0.0
    rank = max(1, min(len(sorted_values), int(round(q * len(sorted_values) + 0.5))))
    return sorted_values[rank - 1]
