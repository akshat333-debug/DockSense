"""Geometry tests with hand-computed expectations.

Every number here was worked out on paper first. If one of these fails, the
bug is in geometry.py, not in the test — that is the entire point of pinning
them to arithmetic rather than to whatever the code currently returns.
"""

import pytest

from handleguard.perception import geometry as g

# A 100x50 box with top-left at (0, 0). Remember: y grows downward.
A = (0.0, 0.0, 100.0, 50.0)


def test_basic_measures():
    assert g.width(A) == 100
    assert g.height(A) == 50
    assert g.area(A) == 5000
    assert g.center(A) == (50.0, 25.0)
    assert g.bottom_center(A) == (50.0, 50.0)


def test_degenerate_box_is_zero_not_negative():
    # Inverted coordinates must not produce negative area.
    bad = (100.0, 50.0, 0.0, 0.0)
    assert g.width(bad) == 0
    assert g.area(bad) == 0


def test_intersection_and_iou():
    b = (50.0, 0.0, 150.0, 50.0)  # overlaps A on x in [50,100]
    assert g.intersection_area(A, b) == 50 * 50  # 2500
    # union = 5000 + 5000 - 2500 = 7500 -> iou = 1/3
    assert g.iou(A, b) == pytest.approx(1 / 3)


def test_disjoint_boxes():
    far = (500.0, 500.0, 600.0, 550.0)
    assert g.intersection_area(A, far) == 0.0
    assert g.iou(A, far) == 0.0
    assert g.horizontal_overlap(A, far) == 0.0


def test_identical_boxes_iou_one():
    assert g.iou(A, A) == pytest.approx(1.0)


def test_vertical_gap_sign():
    # `below` sits 20px under A's bottom edge (A bottom = 50, below top = 70)
    below = (0.0, 70.0, 100.0, 120.0)
    assert g.vertical_gap(A, below) == 20.0
    # Touching: gap exactly 0
    touching = (0.0, 50.0, 100.0, 100.0)
    assert g.vertical_gap(A, touching) == 0.0
    # Overlapping vertically -> negative
    overlapping = (0.0, 30.0, 100.0, 80.0)
    assert g.vertical_gap(A, overlapping) == -20.0


def test_support_fraction_is_area_based():
    pallet = (0.0, 40.0, 50.0, 200.0)  # covers only left half of A's x-range
    # A ∩ pallet = x[0,50] y[40,50] = 50*10 = 500; area(A)=5000 -> 0.1
    assert g.support_fraction(A, pallet) == pytest.approx(0.1)
    # Fully contained -> 1.0
    big = (-10.0, -10.0, 200.0, 200.0)
    assert g.support_fraction(A, big) == pytest.approx(1.0)
    # No contact -> 0.0
    assert g.support_fraction(A, (500.0, 500.0, 600.0, 600.0)) == 0.0


def test_support_ratio_is_width_based_not_area_based():
    """A box half-hanging off its support has ratio 0.5 regardless of heights."""
    lower = (50.0, 50.0, 150.0, 100.0)  # shares x in [50,100] = 50 of A's 100 wide
    assert g.support_ratio(A, lower) == pytest.approx(0.5)
    # Height of the support must not change the answer — this is what
    # distinguishes support_ratio from support_fraction.
    taller = (50.0, 50.0, 150.0, 900.0)
    assert g.support_ratio(A, taller) == pytest.approx(0.5)


def test_is_above_requires_proximity_and_overlap():
    resting = (10.0, 50.0, 110.0, 100.0)  # directly under A, big overlap
    assert g.is_above(A, resting, max_gap=5.0)

    # Same overlap but far below -> not stacked
    far_below = (10.0, 400.0, 110.0, 450.0)
    assert not g.is_above(A, far_below, max_gap=5.0)

    # Close below but barely any horizontal overlap -> not stacked
    offset = (95.0, 50.0, 195.0, 100.0)  # overlap = 5px of 100 = 0.05
    assert not g.is_above(A, offset, max_gap=5.0, min_overlap=0.3)


def test_point_in_polygon_convex():
    square = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    assert g.point_in_polygon((5.0, 5.0), square)
    assert not g.point_in_polygon((15.0, 5.0), square)
    assert not g.point_in_polygon((5.0, -1.0), square)


def test_point_in_polygon_concave():
    """An L-shape: the notch must read as outside."""
    L = [(0, 0), (10, 0), (10, 4), (4, 4), (4, 10), (0, 10)]
    L = [(float(x), float(y)) for x, y in L]
    assert g.point_in_polygon((2.0, 2.0), L)  # in the corner
    assert g.point_in_polygon((8.0, 2.0), L)  # in the top arm
    assert not g.point_in_polygon((8.0, 8.0), L)  # in the notch


def test_degenerate_polygon_is_never_inside():
    assert not g.point_in_polygon((0.0, 0.0), [])
    assert not g.point_in_polygon((0.0, 0.0), [(0.0, 0.0), (1.0, 1.0)])


def test_scale_polygon_maps_normalized_to_pixels():
    poly = [(0.0, 0.0), (0.5, 0.25), (1.0, 1.0)]
    assert g.scale_polygon(poly, 1280, 720) == [
        (0.0, 0.0),
        (640.0, 180.0),
        (1280.0, 720.0),
    ]
