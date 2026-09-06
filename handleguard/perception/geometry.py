"""Pure box/polygon geometry. No torch, no cv2, no state.

Every spatial question the behaviour detectors ask reduces to something here.
Kept dependency-free on purpose: it is the one module cheap enough to test
exhaustively, and everything above it inherits that correctness.

Box convention throughout: (x1, y1, x2, y2), pixels, y grows DOWNWARD.
So y1 is the top edge and y2 is the bottom edge. Say it out loud once and the
sign errors go away.
"""

from __future__ import annotations

from handleguard.types import BBox


def width(b: BBox) -> float:
    return max(b[2] - b[0], 0.0)


def height(b: BBox) -> float:
    return max(b[3] - b[1], 0.0)


def area(b: BBox) -> float:
    return width(b) * height(b)


def center(b: BBox) -> tuple[float, float]:
    return (b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0


def bottom_center(b: BBox) -> tuple[float, float]:
    """Where the object meets the ground, roughly. Used for zones and floors."""
    return (b[0] + b[2]) / 2.0, b[3]


def top_edge(b: BBox) -> float:
    return b[1]


def bottom_edge(b: BBox) -> float:
    return b[3]


def intersection_area(a: BBox, b: BBox) -> float:
    dx = min(a[2], b[2]) - max(a[0], b[0])
    dy = min(a[3], b[3]) - max(a[1], b[1])
    if dx <= 0 or dy <= 0:
        return 0.0
    return dx * dy


def iou(a: BBox, b: BBox) -> float:
    inter = intersection_area(a, b)
    if inter <= 0:
        return 0.0
    union = area(a) + area(b) - inter
    return inter / union if union > 0 else 0.0


def horizontal_overlap(a: BBox, b: BBox) -> float:
    """Width of the x-range the two boxes share, in pixels. 0 if disjoint."""
    return max(min(a[2], b[2]) - max(a[0], b[0]), 0.0)


def vertical_gap(upper: BBox, lower: BBox) -> float:
    """Signed gap between `upper`'s bottom edge and `lower`'s top edge.

    Positive  -> a clear space between them.
    Negative  -> they overlap vertically.
    Near zero -> `upper` is resting on `lower`, which is what stacking cares
    about.
    """
    return lower[1] - upper[3]


def support_fraction(product: BBox, support: BBox) -> float:
    """Fraction of `product`'s footprint that sits over `support`, 0-1.

    This is the pallet-overhang metric (B08): area(product ∩ support) /
    area(product). 1.0 means fully on the pallet, 0.4 means well over half is
    hanging off.
    """
    a = area(product)
    return intersection_area(product, support) / a if a > 0 else 0.0


def support_ratio(upper: BBox, lower: BBox) -> float:
    """Fraction of `upper`'s WIDTH that is backed by `lower`, 0-1.

    The stack-stability proxy (B06). Distinct from `support_fraction`: this one
    ignores vertical extent, because a box resting on another only needs
    horizontal backing to be stable. Low ratio -> overhang -> tipping risk.
    """
    w = width(upper)
    return horizontal_overlap(upper, lower) / w if w > 0 else 0.0


def is_above(upper: BBox, lower: BBox, *, max_gap: float, min_overlap: float = 0.3) -> bool:
    """Is `upper` stacked on / directly above `lower`?

    `max_gap` is in pixels and should be derived from object height by the
    caller (features/support.py does this), not guessed here.
    """
    gap = vertical_gap(upper, lower)
    if gap < -height(upper) * 0.5 or gap > max_gap:
        return False
    return support_ratio(upper, lower) >= min_overlap


def point_in_polygon(pt: tuple[float, float], poly: list[tuple[float, float]]) -> bool:
    """Ray-casting point-in-polygon. Handles concave shapes.

    Points exactly on an edge are not guaranteed either way — zones are drawn by
    hand and a pixel of ambiguity at the boundary does not matter.
    """
    x, y = pt
    inside = False
    n = len(poly)
    if n < 3:
        return False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y):
            x_cross = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < x_cross:
                inside = not inside
        j = i
    return inside


def scale_polygon(
    poly: list[tuple[float, float]], w: int, h: int
) -> list[tuple[float, float]]:
    """Normalized (0-1) polygon -> pixel polygon for a given frame size.

    Zones are stored normalized so they survive a resolution change; this is
    where they become concrete.
    """
    return [(px * w, py * h) for px, py in poly]
