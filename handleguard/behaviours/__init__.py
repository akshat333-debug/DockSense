"""Behaviour detector registry imports.

All twelve module imports live here so parallel detector work does not need to
keep editing package wiring.
"""

from . import (
    b01_drop,
    b02_throw,
    b03_drag,
    b04_rough_handling,
    b05_improper_stack,
    b06_unstable_stack,
    b07_zone_violation,
    b08_pallet_overhang,
    b09_stepping,
    b10_manual_heavy_handling,
    b11_unsafe_sequence,
    b12_unsafe_surface,
    registry,
)

__all__ = [
    "b01_drop",
    "b02_throw",
    "b03_drag",
    "b04_rough_handling",
    "b05_improper_stack",
    "b06_unstable_stack",
    "b07_zone_violation",
    "b08_pallet_overhang",
    "b09_stepping",
    "b10_manual_heavy_handling",
    "b11_unsafe_sequence",
    "b12_unsafe_surface",
    "registry",
]
