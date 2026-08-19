"""Unit tests for the houses, their appurtenances, and the wells (`hamletgen/homesteads.py`).

Split from test_hamletgen.py by feature 111; test bodies verbatim. See hamletgen/CLAUDE.md.
"""

import math

import pytest

from l7r.diagram import hamletgen as hg


def test_place_wells_never_clusters_two_wells_inside_the_spacing_floor():
    """The greedy coverage sort (2026-08-15) pops FAR seats first, so the 170 px spacing guard can
    only fire when every seat the engine will accept sits beside an existing well. Build exactly
    that: `well_at` accepts only a small disc, so after the first (central) well every acceptable
    candidate is inside the spacing floor and must be skipped - one well places, never a clustered
    pair (`wells_not_clustered` is the rule the guard exists for)."""
    from types import SimpleNamespace

    houses = [{"x": 500, "y": 500}, {"x": 520, "y": 500}, {"x": 500, "y": 520}, {"x": 520, "y": 520}]
    # M={}: no surface water, so every house is needy (the minimax filter reads s.M).
    # `_crop_boxes` returning [] is deliberate, not a shrug: the later-well tie-break asks the crop
    # for the box it will set (see `_outside_cloud`), and an empty answer is what exercises its
    # house-centers FALLBACK - so this stub covers both the call and the default it degrades to.
    s = SimpleNamespace(well_at=lambda x, y: math.hypot(x - 510, y - 510) < 60.0, M={}, _crop_boxes=lambda city=False: [])
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


def test_the_cluster_seeds_cloud_still_seats_a_hamlet_when_the_rows_offer_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    """The front row + lane frontage seat every household on all four scripted hamlets, so the
    `cluster_seeds` CLOUD - the fallback behind them - runs on no real map. It got quieter still on
    2026-08-17, when `front_row` began sampling by bundle pitch instead of by household count.

    A fallback nothing exercises is a fallback nobody knows is broken, so drive it directly: with
    both row passes returning no seats, the cloud has to seat the hamlet by itself. This also pins
    the lean-toward-the-field transform (`ly = -wdep + (ly + wdep) * 0.75`), which is the only place
    that compression is applied."""
    from l7r.diagram.hamletgen import homesteads as HS

    monkeypatch.setattr(HS, "front_row", lambda plan, count, standoff=46.0: [])
    monkeypatch.setattr(HS, "lane_frontage", lambda s, seat, step=86.0: [])
    plan = hg.plan_site(hg.HamletSpec(name="CloudOnly", seed=7, households=10))
    s = hg.build(plan)
    assert plan.placed > 0, "with both row passes silent, every farmstead must come from the cloud"
    assert s.M["meta"]["cluster_seeding"] == "cloud"
    # THE INVARIANT IS A TRACE EITHER WAY, not an unconditional stamp (updated 2026-08-19). The
    # declaration is validated against the DRAWN aspect now, so a cloud-seated cluster whose drawing
    # does not match its roll is correctly recorded `cluster_shape_unhonored` instead - which is the
    # whole point of the guard. Asserting the honored key unconditionally would re-assert the very
    # thing the honesty rule exists to deny.
    assert plan.cluster_shape in (s.M["meta"].get("cluster_shape"), s.M["meta"].get("cluster_shape_unhonored")), "the cloud must record the rolled shape either as honored or as unhonored"


def test_a_house_beside_open_water_needs_no_rescue_well() -> None:
    """`place_wells`' rescue pass exists for a household the grid left dry, and it skips any house
    already watered by a stream, channel or pond - the check's own verdict, so the rescue cannot
    plant a well the gate never asked for. The companion of the `M={}` case above, which has no
    surface water and so takes the other branch."""
    from types import SimpleNamespace

    houses = [{"x": 500, "y": 500}, {"x": 2000, "y": 2000}]  # the second sits far outside the first well's reach...
    s = SimpleNamespace(well_at=lambda x, y: math.hypot(x - 500, y - 500) < 60.0, M={"streams": [{"poly": [[1900, 1900], [2100, 2100]], "w": 9}]})  # ...but a stream runs right past it
    plan = SimpleNamespace(spec=SimpleNamespace(households=6), ftpx=1.0)
    assert hg.place_wells(s, plan, houses) == 1, "the watered house is skipped by the rescue, so only the first well is sited"  # type: ignore[arg-type]


def test_lane_frontage_seats_the_hamlet_when_the_field_row_offers_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    """The lane-frontage pass seats the BACK RANK on a real map, but only the households past one
    rank's worth of the band - so on a small hamlet it can place very few, and for part of one day
    (while `front_row` sampled by density with no cap) it placed nothing at all and the cluster came
    out a single rank. Drive it directly, with the field row silent, so the code that puts a door on
    a lane is exercised whatever the cap leaves it."""
    from l7r.diagram.hamletgen import homesteads as HS

    monkeypatch.setattr(HS, "front_row", lambda plan, count, standoff=46.0: [])
    plan = hg.plan_site(hg.HamletSpec(name="LaneOnly", seed=5, households=10))
    s = hg.build(plan)
    assert plan.placed > 0, "with the field row silent, the farmsteads must come off the lanes"
    assert s.M["meta"]["cluster_seeding"] == "frontage", "the lane pass alone still counts as frontage seeding"
