"""Single entry point for every YAML in configs/.

No other module opens a config file. That keeps the tuning surface in one place
and means tests can swap in fixture configs with one call to `set_config_dir`.

Values are cached after first read — configs are static during a run.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_DIR = _ROOT / "configs"


def set_config_dir(path: str | Path) -> None:
    """Point the loader elsewhere (tests, alternate deployments). Clears cache."""
    global _CONFIG_DIR
    _CONFIG_DIR = Path(path)
    load.cache_clear()


def config_dir() -> Path:
    return _CONFIG_DIR


@lru_cache(maxsize=None)
def load(name: str) -> dict[str, Any]:
    """Load `configs/<name>.yaml`. Cached.

    Raises FileNotFoundError with the resolved path — a missing config is a
    setup error worth failing loudly on, not something to default around.
    """
    path = _CONFIG_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"config not found: {path}")
    with open(path) as fh:
        data = yaml.safe_load(fh)
    return data or {}


def behaviours() -> dict[str, Any]:
    return load("behaviours")


def products() -> dict[str, Any]:
    return load("products")


def risk_weights() -> dict[str, Any]:
    return load("risk_weights")


def sop_rules() -> dict[str, Any]:
    return load("sop_rules")


def zones() -> dict[str, Any]:
    return load("zones")


# --------------------------------------------------------------------------- #
# Derived lookups used in more than one module
# --------------------------------------------------------------------------- #


def class_prompts() -> list[str]:
    """Detector text prompts, in a fixed order.

    The order IS the class index YOLO-World returns, so it must be stable —
    dict insertion order from the YAML gives us that.
    """
    return [spec["prompt"] for spec in products()["classes"].values()]


def class_names() -> list[str]:
    """Our internal class keys, index-aligned with `class_prompts()`."""
    return list(products()["classes"].keys())


def role_of(cls: str) -> str:
    """Map an internal class key to its role ("product", "actor", ...)."""
    spec = products()["classes"].get(cls)
    return spec["role"] if spec else "unknown"


def fragility_of(cls: str) -> float:
    """Fragility PRIOR for a class, 0-1.

    This is a prior, not a measurement. Anything surfaced to a user from this
    value must be labelled as a generic product-risk prior — we cannot see what
    is inside a box.
    """
    frag = products().get("fragility", {})
    return float(frag.get(cls, frag.get("default", 0.4)))
