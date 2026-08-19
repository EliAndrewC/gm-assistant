#!/usr/bin/env python3
"""The rolled `cluster_shape` must bind, and must not be declared where it did not.

Background: over 48 cohort seeds and all four pool hamlets, `cluster_shape` was rolled, printed in
every cohort-audit header, and HONORED ON ONE (seed 34). It fed only the cloud seeding pass, which
runs for households the front rows do not seat - and the rows seat everyone on 47 of 48 seeds. Round,
elongated and crescent all drew the same 3:1 band."""

import inspect
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
