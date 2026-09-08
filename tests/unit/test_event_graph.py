"""Temporal event graph — the artefact behind the novelty claim."""

from __future__ import annotations

from handleguard.events.graph import FOLLOWS, RECURS, SHARES_TRACK, build_graph
from handleguard.types import BehaviourEvent


def ev(bid, name, start, end, tracks, severity=0.6):
    return BehaviourEvent(
        behaviour_id=bid,
        name=name,
        track_ids=tuple(tracks),
        start_frame=0,
        end_frame=1,
        start_t=start,
        end_t=end,
        severity=severity,
        confidence=0.8,
        evidence={},
        zone=None,
    )


def test_empty_graph_has_no_edges_or_chains():
    g = build_graph([])
    assert g.edges == [] and g.chains() == []


def test_unrelated_events_share_no_track_edge():
    g = build_graph([ev("B01", "drop", 0.0, 1.0, [1]), ev("B03", "drag", 2.0, 3.0, [9])])
    kinds = {e.kind for e in g.edges}
    assert FOLLOWS in kinds
    assert SHARES_TRACK not in kinds, "different entities must not be linked"


def test_distant_events_are_not_linked():
    """Beyond the window there is no temporal relation to claim."""
    g = build_graph(
        [ev("B01", "drop", 0.0, 1.0, [1]), ev("B03", "drag", 500.0, 501.0, [1])],
        window_seconds=10.0,
    )
    assert g.edges == []


def test_same_entity_sequence_forms_a_chain():
    """The headline case: one carton, dragged then dropped then left in a zone."""
    g = build_graph(
        [
            ev("B03", "drag", 0.0, 1.0, [7]),
            ev("B01", "drop", 2.0, 3.0, [7]),
            ev("B07", "zone_violation", 4.0, 6.0, [7]),
        ]
    )
    chains = g.chains()
    assert len(chains) == 1
    assert [e.behaviour_id for e in chains[0]] == ["B03", "B01", "B07"]


def test_recurrence_counts_repeats_per_entity():
    g = build_graph(
        [
            ev("B01", "drop", 0.0, 1.0, [3]),
            ev("B01", "drop", 3.0, 4.0, [3]),
            ev("B01", "drop", 6.0, 7.0, [3]),
        ]
    )
    assert g.recurrence()[("B01", 3)] == 3
    assert any(e.kind == RECURS for e in g.edges)


def test_to_dict_is_json_serializable():
    import json

    g = build_graph([ev("B01", "drop", 0.0, 1.0, [1]), ev("B07", "zone", 2.0, 3.0, [1])])
    payload = g.to_dict()
    json.dumps(payload)  # must not raise
    assert payload["nodes"][0]["behaviour_id"] == "B01"
    assert payload["chains"] == [["B01:drop", "B07:zone"]]
