"""Unit tests for the ground between everything - open-ground scan, woodland, windbreak (`hamletgen/hinterland.py`).

Split from test_hamletgen.py by feature 111; test bodies verbatim. See hamletgen/CLAUDE.md.
"""

import pytest

import hamletgen as hg
from settlement import Settlement

from ._builders import SQUARE, a_plan


def test_a_square_far_from_the_crop_clears_and_one_on_it_does_not() -> None:
    assert hg._clear_gap((700.0, 700.0), 50.0, [SQUARE], 1.0) is None  # standing in it
    assert hg._clear_gap((700.0, 200.0), 50.0, [SQUARE], 1.0) == pytest.approx(150.0)
    assert hg._clear_gap((700.0, 1100.0), 50.0, [SQUARE], 1.0) is None  # in the crop's sunny shadow
    assert hg._clear_gap((700.0, 700.0), 50.0, [], 1.0) is None  # no crop at all - nothing to measure


def test_a_square_near_a_line_is_detected() -> None:
    assert hg._near_line((100.0, 100.0), 20.0, [(0.0, 100.0), (200.0, 100.0)], pad=10.0)
    assert not hg._near_line((100.0, 400.0), 20.0, [(0.0, 100.0), (200.0, 100.0)], pad=10.0)


def test_a_windbreak_column_with_no_house_of_its_own_leans_on_the_whole_fringe() -> None:
    """`belt_polygon` samples the windward fringe in 8 columns ACROSS the wind; a cluster with a
    gap in the middle leaves some column with no house within its own width, and that column has to
    fall back on the cluster's overall fringe rather than divide by nothing.

    Held here because the branch is reached by cluster SHAPE, not by any spec knob: it was live on
    the pool until an unrelated re-roll moved the houses, and a fallback that no map happens to hit
    is exactly the kind that rots unnoticed (the skill CLAUDE.md's 'a check that never RUNS looks
    like a check that passes', one layer over). Two tight groups 1,100 px apart across a northerly
    wind put the three middle columns outside every house's reach."""
    plan = a_plan()
    s = Settlement(W=plan.W, H=plan.H, seed=plan.spec.seed)
    s.M["houses"] = [{"x": x, "y": 700.0, "w": 46.0, "h": 28.0} for x in (200.0, 260.0, 320.0, 1300.0, 1360.0, 1420.0)]
    belt = hg.belt_polygon(s, plan)
    assert belt, "a gapped cluster still needs a windbreak belt"
    assert len(belt) >= 4
