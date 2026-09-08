"""Collapse repeated detector firings into reviewable behaviour events."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from handleguard import config
from handleguard.types import BehaviourEvent


class EventDeduper:
    def __init__(self, cfg: dict[str, Any] | None = None) -> None:
        self.cfg = cfg or config.behaviours()
        self._active: dict[tuple[str, tuple[int, ...]], BehaviourEvent] = {}
        self._closed: list[BehaviourEvent] = []

    def push(self, event: BehaviourEvent) -> None:
        key = self._key(event)
        existing = self._active.get(key)
        if existing is None:
            self._active[key] = event
            return
        window = self._window_seconds(event)
        if event.start_t - existing.end_t <= window:
            self._active[key] = _merge(existing, event)
        else:
            self._closed.append(existing)
            self._active[key] = event

    def settled(self) -> list[BehaviourEvent]:
        """Events already closed by a cooldown, without draining anything.

        Detectors that reason over history (B11 sequence) and the recurrence risk
        component need to see earlier events mid-run. Only closed events are
        exposed: an event still merging would report a moving end time.
        """
        return list(self._closed)

    def flush(self) -> list[BehaviourEvent]:
        out = self._closed + list(self._active.values())
        self._closed = []
        self._active = {}
        return sorted(out, key=lambda ev: (ev.start_t, ev.behaviour_id, ev.track_ids))

    def _window_seconds(self, event: BehaviourEvent) -> float:
        dedup = self.cfg.get("dedup", {})
        return float(dedup.get(event.name, dedup.get(event.behaviour_id, 3.0)))

    @staticmethod
    def _key(event: BehaviourEvent) -> tuple[str, tuple[int, ...]]:
        return event.behaviour_id, tuple(sorted(event.track_ids))


def dedupe_events(events: list[BehaviourEvent], cfg: dict[str, Any] | None = None) -> list[BehaviourEvent]:
    deduper = EventDeduper(cfg)
    for event in sorted(events, key=lambda ev: (ev.start_t, ev.end_t)):
        deduper.push(event)
    return deduper.flush()


def _merge(left: BehaviourEvent, right: BehaviourEvent) -> BehaviourEvent:
    evidence = dict(left.evidence)
    evidence.update(right.evidence)
    return replace(
        left,
        end_frame=max(left.end_frame, right.end_frame),
        end_t=max(left.end_t, right.end_t),
        severity=max(left.severity, right.severity),
        confidence=max(left.confidence, right.confidence),
        evidence=evidence,
        zone=right.zone or left.zone,
    )
