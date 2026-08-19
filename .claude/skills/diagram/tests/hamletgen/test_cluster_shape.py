#!/usr/bin/env python3
"""The rolled `cluster_shape` must bind, and must not be declared where it did not.

Background: over 48 cohort seeds and all four pool hamlets, `cluster_shape` was rolled, printed in
every cohort-audit header, and HONORED ON ONE (seed 34). It fed only the cloud seeding pass, which
runs for households the front rows do not seat - and the rows seat everyone on 47 of 48 seeds. Round,
elongated and crescent all drew the same 3:1 band."""

import inspect
import math
import re

from l7r.diagram import hamletgen as hg
from l7r.diagram.check_village import segments_04c_groves_and_shading as seg04c


def test_the_gates_drawn_aspect_table_matches_the_generators() -> None:
    """A DUPLICATED TABLE WITH NO PIN IS A TABLE THAT DRIFTS.

    The gate may not import the generator (`hamletgen` imports `check_village`, not the reverse), so
    `CLUSTER_DRAWN_ASPECT` is stated twice. This is the only thing keeping the copies equal, and
    without it the failure is silent in the worst direction: the generator would decline to declare a
    shape the gate would have accepted, or - far worse - declare one the gate would reject, and the
    disagreement would surface as a mystery gate failure on some seed nobody was looking at."""
    src = inspect.getsource(seg04c._seg_0615__cluster_shape_matches_the_drawing)
    m = re.search(r"_asp = (\{.*?\})\n", src, re.S)
    assert m, "the gate's drawn-aspect table moved or was renamed - re-pin it, do not delete this test"
    assert eval(m.group(1)) == hg.consts.CLUSTER_DRAWN_ASPECT, "the gate's drawn-aspect table has drifted from hamletgen.consts.CLUSTER_DRAWN_ASPECT; change both or neither"


def test_every_rollable_shape_has_a_band_a_row_span_and_a_drawn_range() -> None:
    """A shape that can be ROLLED but has no entry falls back to the crescent default, which is how a
    knob silently stops binding for one of its values - the exact defect this feature fixed."""
    for shape in set(hg.consts.CLUSTER_SHAPES):
        assert shape in hg.consts.CLUSTER_BAND_ASPECT, f"{shape} can be rolled but has no band aspect"
        assert shape in hg.consts.CLUSTER_ROW_SPAN, f"{shape} can be rolled but has no row span"
        assert shape in hg.consts.CLUSTER_DRAWN_ASPECT, f"{shape} can be rolled but has no drawn range"


def test_the_drawn_ranges_admit_the_band_they_are_meant_to_describe() -> None:
    """Ordering sanity, in the observable's own units: round must not reach as long as elongated's
    floor, or the two words describe the same picture and the knob buys no variance at all."""
    rnd = hg.consts.CLUSTER_DRAWN_ASPECT["round"]
    lng = hg.consts.CLUSTER_DRAWN_ASPECT["elongated"]
    assert rnd[0] >= 1.0, "an aspect ratio below 1.0 is not a shape, it is a swapped axis"
    assert rnd[1] < lng[0], "round's ceiling must sit below elongated's floor or the shapes are indistinguishable"
    for shape, (lo, hi) in hg.consts.CLUSTER_DRAWN_ASPECT.items():
        assert lo < hi, f"{shape} has an empty drawn range"


def test_the_two_aspect_measures_agree_on_the_same_point_sets() -> None:
    """PIN BY BEHAVIOR, NOT BY SOURCE. The table pin above compares text; this compares answers, which
    is what actually has to match - a mirrored formula can drift while both tables stay equal.

    The diagonal cases are the whole point. A page-axis bbox ratio tends to 1.0 for a band on a
    diagonal and is maximally blind at 45 degrees, which is how the first cut of this rule recorded
    Kashikawa's visibly 3.8:1 ribbon as 1.22 and denied its honest `elongated`, while honoring Sawada's
    `round` on a cluster drawing 3.02:1. Three independent reviews caught it the same day."""
    cases = [
        ([0.0, 100.0, 200.0, 300.0], [0.0, 0.0, 0.0, 0.0]),
        ([0.0, 0.0, 0.0, 0.0], [0.0, 100.0, 200.0, 300.0]),
        ([0.0, 70.7, 141.4, 212.1], [0.0, 70.7, 141.4, 212.1]),
        ([0.0, 100.0, 0.0, 100.0], [0.0, 0.0, 100.0, 100.0]),
        ([12.0, 305.0, 88.0, 190.0, 240.0], [40.0, 610.0, 130.0, 300.0, 500.0]),
    ]
    for xs, ys in cases:
        a = hg.homesteads.cluster_aspect(xs, ys)
        b = seg04c._cluster_aspect(xs, ys)
        assert abs(a - b) < 1e-9, f"generator {a} vs gate {b} on {xs}/{ys} - the mirrored formulas have drifted"


def test_the_drawn_aspect_does_not_care_which_way_the_field_margin_points() -> None:
    """Rotation invariance, asserted rather than assumed - it is the property the whole fix is for."""
    xs = [0.0, 100.0, 200.0, 300.0, 150.0]
    ys = [0.0, 10.0, -10.0, 0.0, 40.0]
    flat = hg.homesteads.cluster_aspect(xs, ys)
    for deg in (17.0, 45.0, 63.0, 90.0, 134.0):
        th = math.radians(deg)
        rx = [x * math.cos(th) - y * math.sin(th) for x, y in zip(xs, ys, strict=True)]
        ry = [x * math.sin(th) + y * math.cos(th) for x, y in zip(xs, ys, strict=True)]
        turned = hg.homesteads.cluster_aspect(rx, ry)
        assert abs(turned - flat) < 0.02 * flat, f"aspect changed from {flat:.2f} to {turned:.2f} when the cloud was turned {deg} deg"


def test_a_perfectly_diagonal_string_is_not_recorded_as_round() -> None:
    """The defect itself, pinned. If this reads near 1.0, the page-axis bbox measure has been restored."""
    diag = [0.0, 70.7, 141.4, 212.1, 282.8]
    assert hg.homesteads.cluster_aspect(diag, list(diag)) > 10.0, "a diagonal string must measure as extremely elongated"


def test_a_cluster_of_fewer_than_two_houses_has_no_aspect() -> None:
    """The degenerate guard, in BOTH copies. One house has no axis and no proportion, so the only
    honest answer is 1.0 - and a covariance over a single point is a divide-by-nothing waiting to
    happen.

    Held because no map in the corpus has fewer than two houses, so this branch never executes during
    a pool or cohort run and its coverage would depend entirely on a generator being re-run. That is
    the same cache-dependent, tested-by-luck state four other branches were in before today."""
    for xs, ys in (([], []), ([100.0], [200.0])):
        assert hg.homesteads.cluster_aspect(xs, ys) == 1.0, f"generator gave a proportion for {len(xs)} house(s)"
        assert seg04c._cluster_aspect(xs, ys) == 1.0, f"gate gave a proportion for {len(xs)} house(s)"
