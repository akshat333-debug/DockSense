"""Temporal event graph.

Both source documents lead with this as the primary novelty: reason over
*sequences* of interactions rather than classifying isolated frames. Concretely
that means relating deduplicated behaviour events to each other, so the system
can say "this carton was dragged, then dropped, then left in a walkway" instead
of reporting three unrelated rows.

Deliberately a plain dict-of-lists. A graph library would add a dependency for
what is a few dozen events per video, and the ablation only needs the edges to
exist or not.

Edges
-----
``FOLLOWS``      b started within ``window_seconds`` of a ending — temporal adjacency.
``SHARES_TRACK`` a and b involve the same tracked entity.
``RECURS``       same behaviour on the same entity — what the frequency risk
                 component counts, and what "repeated mishandling" means.

A chain is a maximal path over FOLLOWS edges restricted to a shared entity, which
is what makes it a story about one carton rather than a timeline of the room.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from handleguard.types import BehaviourEvent

FOLLOWS = "FOLLOWS"
SHARES_TRACK = "SHARES_TRACK"
RECURS = "RECURS"


@dataclass(frozen=True)
class Edge:
    src: int
    dst: int
    kind: str
    gap_seconds: float = 0.0


@dataclass
class EventGraph:
    """Relations between deduplicated behaviour events in one video."""

    window_seconds: float = 10.0
    events: list[BehaviourEvent] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)

    @classmethod
    def build(
        cls,
        events: Sequence[BehaviourEvent],
        *,
        window_seconds: float = 10.0,
    ) -> "EventGraph":
        ordered = sorted(events, key=lambda e: (e.start_t, e.behaviour_id))
        graph = cls(window_seconds=window_seconds, events=list(ordered))
        for i, a in enumerate(ordered):
            for j in range(i + 1, len(ordered)):
                b = ordered[j]
                gap = b.start_t - a.end_t
                if gap > window_seconds:
                    break  # ordered by start_t, so nothing later is closer
                shared = set(a.track_ids) & set(b.track_ids)
                if gap >= 0.0:
                    graph.edges.append(Edge(i, j, FOLLOWS, round(gap, 3)))
                if shared:
                    graph.edges.append(Edge(i, j, SHARES_TRACK, round(max(gap, 0.0), 3)))
                    if a.behaviour_id == b.behaviour_id:
                        graph.edges.append(Edge(i, j, RECURS, round(max(gap, 0.0), 3)))
        return graph

    # --- queries -----------------------------------------------------------

    def successors(self, index: int, kind: str | None = None) -> list[int]:
        return [e.dst for e in self.edges if e.src == index and (kind is None or e.kind == kind)]

    def chains(self, min_length: int = 2) -> list[list[BehaviourEvent]]:
        """Maximal sequences of events that follow one another on a shared entity.

        This is the artefact behind the novelty claim: an ordered story about one
        carton, not a flat list of alerts.
        """
        # Only the *nearest* following event on a shared entity counts as the next
        # step. Keeping every in-window pair would also link A->C alongside
        # A->B->C, and emit the transitive shortcut as a second, bogus chain.
        follows = {(e.src, e.dst) for e in self.edges if e.kind == FOLLOWS}
        nearest: dict[int, tuple[float, int]] = {}
        for e in self.edges:
            if e.kind != SHARES_TRACK or (e.src, e.dst) not in follows:
                continue
            best = nearest.get(e.src)
            if best is None or e.gap_seconds < best[0]:
                nearest[e.src] = (e.gap_seconds, e.dst)

        linked: dict[int, list[int]] = defaultdict(list)
        for src, (_, dst) in nearest.items():
            linked[src].append(dst)

        has_parent = {dst for dsts in linked.values() for dst in dsts}
        chains: list[list[BehaviourEvent]] = []

        def walk(node: int, path: list[int]) -> None:
            nxt = linked.get(node, [])
            if not nxt:
                if len(path) >= min_length:
                    chains.append([self.events[i] for i in path])
                return
            for child in nxt:
                walk(child, path + [child])

        for start in range(len(self.events)):
            if start not in has_parent:
                walk(start, [start])
        return chains

    def recurrence(self) -> dict[tuple[str, int], int]:
        """How many times each (behaviour, entity) pair repeated.

        Feeds the frequency component of the risk score — a third drop of the
        same carton is worse news than the first.
        """
        counts: dict[tuple[str, int], int] = defaultdict(int)
        for ev in self.events:
            for tid in ev.track_ids:
                counts[(ev.behaviour_id, tid)] += 1
        return dict(counts)

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable form for the API and the UI timeline."""
        return {
            "nodes": [
                {
                    "index": i,
                    "behaviour_id": e.behaviour_id,
                    "name": e.name,
                    "start_t": round(e.start_t, 3),
                    "end_t": round(e.end_t, 3),
                    "track_ids": list(e.track_ids),
                    "severity": round(e.severity, 3),
                    "zone": e.zone,
                }
                for i, e in enumerate(self.events)
            ],
            "edges": [
                {"src": e.src, "dst": e.dst, "kind": e.kind, "gap_seconds": e.gap_seconds}
                for e in self.edges
            ],
            "chains": [
                [f"{ev.behaviour_id}:{ev.name}" for ev in chain] for chain in self.chains()
            ],
        }


def build_graph(
    events: Iterable[BehaviourEvent],
    *,
    window_seconds: float = 10.0,
) -> EventGraph:
    return EventGraph.build(list(events), window_seconds=window_seconds)
