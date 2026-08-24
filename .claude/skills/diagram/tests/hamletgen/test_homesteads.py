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
    # THE FRONTAGE PASS IS LINEAR-ONLY SINCE FEATURE 126. The internal lanes it used to walk are
    # drawn two stages later now, so for a nucleated or dispersed hamlet this pass has nothing to
    # offer and is skipped; for a LINEAR one it fronts the connector, which is the one way that
    # genuinely predates the houses. The form is pinned on the spec so the test exercises the pass
    # it is named for rather than whatever the seed happens to roll.
    plan = hg.plan_site(hg.HamletSpec(name="LaneOnly", seed=5, households=10, settlement_form="linear"))
    s = hg.build(plan)
    assert plan.placed > 0, "with the field row silent, the farmsteads must still be seated"
    # ASSERT THE PASS, NOT THE AGGREGATE (feature 126). This used to read
    # `meta["cluster_seeding"] == "frontage"`, inferring the pass ran from a summary field that
    # records which pass seated the MAJORITY. Since the frontage pass became linear-only and points
    # at the connector, it seats a real but minority share, so the summary now says "cloud" while
    # the pass is working perfectly - the assertion had stopped measuring what its own name claims.
    # Testing the offer directly is both narrower and truer.
    seats = HS.lane_frontage(s, plan.seat, connector=True)
    assert seats, "a linear hamlet must be offered seats along the connector it fronts"


def test_a_seat_on_forbidden_ground_is_refused() -> None:
    """`generate` re-rolls a stranding map with the offending ground passed as `avoid`; the seat loops
    honour it through `_seat_allowed`. Half a bundle pitch is the radius - enough to clear the pocket,
    not so much that the retry merely nudges the same steading along it."""

    class _S:
        pass

    s = _S()
    assert hg.homesteads._seat_allowed(s, 100.0, 100.0) is True  # nothing forbidden yet
    s._avoid_seats = [(100.0, 100.0)]
    assert hg.homesteads._seat_allowed(s, 100.0, 100.0) is False  # dead on the forbidden seat
    assert hg.homesteads._seat_allowed(s, 140.0, 100.0) is False  # inside half a bundle pitch
    assert hg.homesteads._seat_allowed(s, 400.0, 400.0) is True  # well clear


def test_the_linear_frontage_pass_stops_once_the_households_are_housed(monkeypatch: pytest.MonkeyPatch) -> None:
    """The connector offers more verge than the hamlet needs, and the pass must stop taking it.

    `lane_frontage` returns every seat the connector can carry, which is routinely more than there
    are farmsteads to put on them. Without the household check the pass keeps seating while the
    offers last, and the map ends up with more houses than the spec asked for - at which point the
    acreage checks are reading a hamlet nobody rolled.

    THE COUNT IS LOWERED AFTER PLANNING, on purpose. `HamletSpec` refuses anything under ten as an
    outlying farmstead rather than a hamlet, so a one-household spec cannot be constructed - but the
    guard under test is about the COUNT alone, and everything else the plan derives (canvas, acreage,
    connector) should stay a real hamlet's or the pass is being exercised on a site that could not
    exist. So the site is planned as a ten-household hamlet and only the target is cut, which is the
    smallest change that puts the guard on the critical path: the first offer is taken, and the
    second is refused by the count rather than by the verge running out.

    `front_row` is silenced for the same reason as the test above - so the frontage pass is what
    seats the hamlet, rather than whatever the field row happens to leave it."""
    from l7r.diagram.hamletgen import homesteads as HS

    monkeypatch.setattr(HS, "front_row", lambda plan, count, standoff=46.0: [])
    plan = hg.plan_site(hg.HamletSpec(name="OneHouse", seed=5, households=10, settlement_form="linear"))
    object.__setattr__(plan.spec, "households", 1)  # frozen, and `replace` would re-run the band validator
    s = hg.build(plan)
    assert len(s.M["houses"]) == 1, "a one-household target gets one farmstead, however much verge is on offer"
    assert len(HS.lane_frontage(s, plan.seat, connector=True)) > 1, "the guard is only under test when more seats were offered than taken"
