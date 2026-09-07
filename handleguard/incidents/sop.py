from __future__ import annotations

from typing import Any

from handleguard import config


def sop_for(behaviour_name: str, cfg: dict[str, Any] | None = None) -> list[str]:
    rules = cfg or config.sop_rules()
    entry = rules.get(behaviour_name, {})
    out: list[str] = []
    if entry.get("rule"):
        out.append(str(entry["rule"]))
    if entry.get("recommendation"):
        out.append(" ".join(str(entry["recommendation"]).split()))
    return out
