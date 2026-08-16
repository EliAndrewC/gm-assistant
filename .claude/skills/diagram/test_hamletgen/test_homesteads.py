"""Unit tests for the houses, their appurtenances, and the wells (`hamletgen/homesteads.py`).

Split from test_hamletgen.py by feature 111; test bodies verbatim. See hamletgen/CLAUDE.md.
"""

import math

import pytest

import hamletgen as hg


def test_place_wells_never_clusters_two_wells_inside_the_spacing_floor():
    """The greedy coverage sort (2026-08-15) pops FAR seats first, so the 170 px spacing guard can
    only fire when every seat the engine will accept sits beside an existing well. Build exactly
    that: `well_at` accepts only a small disc, so after the first (central) well every acceptable
    candidate is inside the spacing floor and must be skipped - one well places, never a clustered
    pair (`wells_not_clustered` is the rule the guard exists for)."""
    from types import SimpleNamespace

    houses = [{"x": 500, "y": 500}, {"x": 520, "y": 500}, {"x": 500, "y": 520}, {"x": 520, "y": 520}]
    s = SimpleNamespace(well_at=lambda x, y: math.hypot(x - 510, y - 510) < 60.0, M={})  # M={}: no surface water, so every house is needy (the minimax filter reads s.M)
    plan = SimpleNamespace(spec=SimpleNamespace(households=12), ftpx=1.0)
    assert hg.place_wells(s, plan, houses) == 1  # type: ignore[arg-type]


@pytest.mark.parametrize(("households", "wells"), [(10, 2), (12, 2), (15, 2), (20, 3)])
def test_wells_are_one_per_six_households_or_so(households: int, wells: int) -> None:
    """Inside `wells_sized_to_population`'s 2-20 households-per-well band at hamlet scale."""
    got = hg.well_target(households)
    assert got == wells
    assert 2 <= households / got <= 20


def test_a_tiny_hamlet_still_keeps_one_well() -> None:
    assert hg.well_target(1) == 1
