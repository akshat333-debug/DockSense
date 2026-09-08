"""Contextual risk scoring for deduplicated behaviour events."""

from __future__ import annotations

from typing import Any

from handleguard import config
from handleguard.types import BehaviourEvent, RiskScore


def score_event(
    event: BehaviourEvent,
    cfg: dict[str, Any] | None = None,
    *,
    contextual: bool = True,
) -> RiskScore:
    """Score one deduplicated event.

    ``contextual=False`` is the ablation: risk collapses to behaviour severity
    alone, discarding kinematics, support geometry, duration, recurrence and
    zone. That is the "a drop is a drop" baseline the contextual model is
    supposed to beat, so it has to be runnable to be worth claiming.
    """
    cfg = cfg or config.risk_weights()
    weights = {k: float(v) for k, v in cfg.get("weights", {}).items()}
    components = _components(event, cfg)
    if not contextual:
        components = {"behaviour_severity": components["behaviour_severity"]}
    active_weights = {k: weights[k] for k in components if k in weights and weights[k] > 0}
    total = sum(active_weights.values())
    if total <= 0:
        return RiskScore(score=0.0, band="low", confidence=event.confidence)
    used = {k: v / total for k, v in active_weights.items()}
    score = 100.0 * sum(components[k] * used[k] for k in used)
    score = max(0.0, min(score, 100.0))
    return RiskScore(
        score=round(score, 2),
        band=_band(score, cfg.get("bands", {})),
        confidence=event.confidence,
        components={k: round(v, 4) for k, v in components.items() if k in used},
        weights_used={k: round(v, 4) for k, v in used.items()},
    )


def _components(event: BehaviourEvent, cfg: dict[str, Any]) -> dict[str, float]:
    evidence = event.evidence
    comps = {"behaviour_severity": _clamp(event.severity)}

    kin_values = [
        _ratio(evidence.get("speed"), 3.0),
        _ratio(evidence.get("downward_velocity"), 3.0),
        _ratio(evidence.get("impact_decel"), 5.0),
        _ratio(evidence.get("fall_heights"), 2.0),
        _ratio(evidence.get("horizontal_travel_heights"), 4.0),
        _ratio(evidence.get("drag_distance_heights"), 4.0),
    ]
    kin_values = [v for v in kin_values if v is not None]
    if kin_values:
        comps["kinematics"] = max(kin_values)

    support_values = [
        1.0 - _clamp(evidence["support_ratio"])
        for key in ("support_ratio",)
        if key in evidence
    ]
    if evidence.get("supported_by") == 0 or evidence.get("unsupported_frames"):
        support_values.append(_ratio(evidence.get("unsupported_frames", 0), 5.0) or 0.0)
    if support_values:
        comps["support_instability"] = max(support_values)

    if event.duration > 0:
        comps["duration"] = _ratio(event.duration, 10.0) or 0.0

    repeats = evidence.get("frequency_count", evidence.get("repeat_count"))
    if repeats is not None:
        freq_cfg = cfg.get("frequency", {})
        per = float(freq_cfg.get("repeat_multiplier", 0.15))
        cap = float(freq_cfg.get("max_multiplier", 0.6))
        comps["frequency"] = min(float(repeats) * per, cap)

    zone = event.zone or str(evidence.get("zone", "unknown"))
    if zone:
        zone_risk = cfg.get("zone_risk", {})
        comps["zone_context"] = _clamp(float(zone_risk.get(zone, zone_risk.get("unknown", 0.3))))

    return comps


def _band(score: float, bands: dict[str, list[float]]) -> str:
    for name, bounds in bands.items():
        if len(bounds) == 2 and float(bounds[0]) <= score <= float(bounds[1]):
            return str(name)
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def _ratio(value: Any, scale: float) -> float | None:
    if value is None:
        return None
    return _clamp(float(value) / scale)


def _clamp(value: float) -> float:
    return max(0.0, min(float(value), 1.0))
