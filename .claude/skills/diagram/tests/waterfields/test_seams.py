"""`waterfields.seams.close_seams` - the pass that makes every paddy bund a SHARED one.

The pool gens exercise the happy paths; these hold the properties and the branches a real fan
does not reliably reach. The property under test throughout is the pass's postcondition: after it
runs, no square foot of the command area is bare - it is planted, it is water, or it is outside
the fan - and no basin's wall stands a short way off another's across dry ground.
"""

import random

import pytest
from shapely.geometry import Polygon

from l7r.diagram.waterfields.banks import _WELD_MIN_APEX, dedup_ring, jog_steps, jog_vertices, tapers_to_a_point
from l7r.diagram.waterfields.frame import _Frame
from l7r.diagram.waterfields.seams import MIN_PLOT_SIDE, _absorb, _despike, _min_apex, _open_to, _parts, _plant, _ring, _water, close_seams

GRAIN = 2.0
HALF = MIN_PLOT_SIDE * GRAIN / 2  # 6 px: a pocket narrower than 12 px cannot hold a basin


def _rect(x0: float, y0: float, x1: float, y1: float) -> list[tuple[float, float]]:
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _scene(plot_rings: list[list[tuple[float, float]]], envelope: list[tuple[float, float]], channels: list | None = None) -> list[dict]:
    """Run close_seams over a flat 90-degree fan with the canal far above and the drain far below,
    so the command-area clip admits the whole envelope and only the plots and water shape it."""
    plots: list[dict] = [{"poly": list(r), "fill": "#A6C398"} for r in plot_rings]
    close_seams(
        random.Random(1),
        _Frame(90),
        plots,
        envelope,
        GRAIN,
        channels or [],
        48.0,
        (26.0, 36.0),
        [(-4000.0, -4000.0), (4000.0, -4000.0)],  # supply canal, far upslope
        [(-4000.0, 4000.0), (4000.0, 4000.0)],  # drain collector, far downslope
        lambda _u: 2.0,
    )
    return plots


def _bare_area(plots: list[dict], envelope: list[tuple[float, float]]) -> float:
    from shapely.ops import unary_union

    field = Polygon(envelope).buffer(0)
    return field.difference(unary_union([Polygon(p["poly"]).buffer(0) for p in plots])).area


def test_a_thin_strip_between_two_basins_is_absorbed_not_left_as_a_doubled_bund():
    # two basins 8 px apart: too narrow to plant, so the strip must become part of one of them and
    # the two bunds become one. This is the GM's report in its smallest form.
    env = _rect(10, 10, 210, 110)
    plots = _scene([_rect(10, 10, 100, 110), _rect(108, 10, 210, 110)], env)
    assert len(plots) == 2, "a strip this narrow is a seam to weld, never a basin to plant"
    assert _bare_area(plots, env) < 1.0, "the strip is still bare - the weld did not happen"
    grown = [p for p in plots if Polygon(p["poly"]).area > 9000]
    assert grown, "neither basin grew, so nothing absorbed the strip"


def test_a_pocket_wide_enough_to_hold_a_basin_is_planted_and_shares_its_bunds():
    env = _rect(10, 10, 290, 110)
    plots = _scene([_rect(10, 10, 100, 110), _rect(200, 10, 290, 110)], env)
    assert len(plots) > 2, "the 100 px pocket between the two basins should have been planted"
    assert _bare_area(plots, env) < 1.0
    for p in plots[2:]:
        assert p["filler"] is True, "a reclaimed basin is tagged so the water anchors skip it"


def test_a_planted_pocket_is_subdivided_at_the_fan_grain_rather_than_shipped_as_one_slab():
    env = _rect(10, 10, 590, 290)
    plots = _scene([_rect(10, 10, 40, 290)], env)
    assert len(plots) > 4, "a 550 x 280 px pocket must be cut into plot-sized basins, not one slab"
    areas = [Polygon(p["poly"]).area for p in plots[1:]]
    assert max(areas) < 0.5 * 550 * 280


def test_a_scrap_touching_no_basin_at_all_is_left_to_the_fan_floor():
    # an island of bare ground with nothing to weld into: the pass must decline rather than invent
    env = _rect(0, 0, 60, 8)  # 8 px tall - too thin to plant, and no plot anywhere near it
    plots = _scene([], env)
    assert plots == []


def test_water_and_its_bank_are_never_planted():
    env = _rect(10, 10, 290, 110)
    chan = [{"pts": [(150.0, -10.0), (150.0, 130.0)], "w": 12.0, "w_tail": 12.0, "role": "branch"}]
    plots = _scene([_rect(10, 10, 100, 110), _rect(200, 10, 290, 110)], env, chan)
    stroke = _water(chan, GRAIN)
    for p in plots:
        assert not Polygon(p["poly"]).buffer(-0.5).intersects(stroke), "a basin was planted in the ditch"


def test_water_covers_the_outside_of_a_bend():
    # flat caps alone leave a wedge on the outside of every turn, and a basin planted in that wedge
    # puts a bund in the water (the defect this closed on Inashiro)
    chan = [{"pts": [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0)], "w": 12.0, "w_tail": 12.0, "role": "branch"}]
    stroke = _water(chan, GRAIN)
    assert stroke.contains(Polygon(_rect(98, -2, 102, 2)).centroid), "the bend's outside corner is uncovered"


def test_close_seams_declines_a_degenerate_call():
    plots: list[dict] = []
    close_seams(random.Random(1), _Frame(90), plots, _rect(0, 0, 10, 10), GRAIN, [], 48.0, (26.0, 36.0), [(0.0, 0.0)], [(0.0, 0.0)], lambda _u: 2.0)
    assert plots == []
    one = [{"poly": _rect(0, 0, 10, 10), "fill": "#A6C398"}]
    close_seams(random.Random(1), _Frame(90), one, [(0.0, 0.0), (1.0, 1.0)], GRAIN, [], 48.0, (26.0, 36.0), [(0.0, 0.0)], [(0.0, 0.0)], lambda _u: 2.0)
    assert len(one) == 1, "an envelope that is not a ring leaves the plots alone"


def test_despike_only_ever_removes_ground():
    spiky = Polygon([(0, 0), (100, 0), (100, 50), (60, 50), (60.05, 25), (59.95, 25), (0, 50)])
    out = _despike(spiky)
    assert out.area <= spiky.area + 1e-9, "the opening grew the pocket - it must be monotone"
    assert out.difference(spiky).area < 1e-6


def test_parts_drops_invalid_rings():
    bowtie = Polygon([(0, 0), (10, 10), (10, 0), (0, 10)])
    assert _parts(bowtie) == []


def test_ring_drops_vertices_that_rounding_collapses():
    assert _ring(Polygon([(0, 0), (0.02, 0.01), (10, 0), (10, 10), (0, 10)])) == [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]


def test_absorb_takes_the_neighbour_it_shares_the_most_bund_with():
    strip = Polygon(_rect(100, 0, 104, 100))
    into = [Polygon(_rect(0, 0, 100, 100)), Polygon(_rect(104, 40, 200, 60))]  # 100 px of shared wall vs 20
    grown: set[int] = set()
    _absorb(strip, into, grown, 3.0, GRAIN)
    assert grown == {0}


def test_absorb_falls_through_to_the_runner_up_when_the_best_neighbour_refuses():
    # the strip meets plot 0 at a POINT only, so that union is a MultiPolygon and must be declined
    strip = Polygon(_rect(100, 100, 140, 140))
    into = [Polygon(_rect(0, 0, 100, 100)), Polygon(_rect(140, 100, 200, 140))]
    grown: set[int] = set()
    _absorb(strip, into, grown, 3.0, GRAIN)
    assert grown == {1}, "the weld gave up instead of trying the basin that could take it"


def _wedge(h: float, ln: float) -> Polygon:
    """A wedge welded onto the x=100 wall of a 100x100 basin, tapering to a point `ln` away.

    Its apex angle is atan(h / ln), so the caller picks the sharpness it wants to test."""
    return Polygon([(100.0, 0.0), (100.0, h), (100.0 + ln, 0.0)])


def _apex_of(poly: Polygon) -> float:
    return _min_apex(dedup_ring(_ring(poly), 1.0))


# A 20 deg wedge truncated to a 3.4 ft end - the shape that reads as a pond when it wears the water
# tint, and the live instance the Inashiro review found (30.0 -> 3.4 ft over 75 ft).
_TRUNCATED_WEDGE = [(200.0, 35.3), (9.6, 1.7), (9.6, -1.7), (200.0, -35.3)]


def test_a_truncated_wedge_is_seen_as_tapering_to_a_point():
    assert tapers_to_a_point(_TRUNCATED_WEDGE, 5.0, 25.0, 20.0)


def test_a_chamfer_between_two_SHORT_edges_is_not_a_taper():
    """The guard that stops the predicate FABRICATING an apex (settlement-review, 2026-08-17).

    Its predecessor deduped the whole ring at the end width, which merges short edges ANYWHERE - so
    a staircase of chamfers mid-wall fused into a spike that was never in the drawing. Four measured
    fabrications on one roll, the worst turning a ring whose sharpest real corner is 86.7 deg into
    2.3, and one of them sat in the flooded candidate zone one roll from demoting an honest basin.

    Same 3.4 ft end edge and the same 20 deg convergence as the wedge above; only the ARMS are
    short. That is the whole difference between the end of a taper and a step in a wall."""
    chamfer = [(20.0, 5.0), (9.6, 1.7), (9.6, -1.7), (20.0, -5.0)]
    assert not tapers_to_a_point(chamfer, 5.0, 25.0, 20.0)


def test_a_parallel_sided_strip_is_not_a_taper_however_short_its_end():
    """The second fabrication guard, and the one the arm-length test alone does NOT catch.

    The angle between the two backward arms is the apex angle only when they DIVERGE; for parallel
    sides it is 0.0, which scores as maximally pointed while describing a strip of constant width.
    Measured live on Inashiro (ring #633: a parallel-sided strip with a 2.3 ft chamfer, converge
    exactly 0.0). A taper is narrow HERE and wide THERE, so the far ends of the arms must stand well
    apart before the angle is allowed to mean anything."""
    strip = [(200.0, 5.0), (0.0, 5.0), (0.0, 2.0), (200.0, 2.0)]
    assert not tapers_to_a_point(strip, 5.0, 25.0, 20.0)


def test_a_wedge_with_a_workable_end_is_not_a_taper():
    # 10.4 ft of end: two aze leave ~7.4 ft of standing water, which is a basin, not a point
    wide = [(200.0, 35.3), (9.6, 5.2), (9.6, -5.2), (200.0, -35.3)]
    assert not tapers_to_a_point(wide, 5.0, 25.0, 20.0)


def test_tapers_to_a_point_declines_a_ring_too_short_to_have_an_end():
    assert not tapers_to_a_point([(0.0, 0.0), (10.0, 0.0), (5.0, 8.0)], 5.0, 25.0, 20.0)


def test_min_apex_reads_the_sharpest_corner_and_survives_a_degenerate_ring():
    assert _min_apex([(0.0, 0.0), (100.0, 0.0), (0.0, 100.0)]) == pytest.approx(45.0, abs=0.1)
    assert _min_apex([(0.0, 0.0), (1.0, 1.0)]) == 180.0  # too short to have a corner


def test_open_to_sheds_the_tapering_tail_and_keeps_the_workable_core():
    kept = _open_to(_wedge(60.0, 200.0), 20.0)
    assert kept is not None
    # the tip (everything narrower than 20) is gone, but most of the wedge survives
    assert 0.3 < kept.area / _wedge(60.0, 200.0).area < 0.95
    assert kept.within(_wedge(60.0, 200.0).buffer(0.01)), "the opening must only ever REMOVE ground"


def test_open_to_returns_none_when_the_whole_scrap_is_thinner_than_the_trim():
    assert _open_to(Polygon(_rect(0, 0, 100, 2)), 20.0) is None


def test_absorb_trims_a_tapering_tail_rather_than_refusing_the_weld():
    # 60/200 -> a 16.7 deg apex: the whole-scrap weld needles, so the strip would have been left
    # bare (the doubled bund that cost cohort seeds 9 and 11). Trimming rescues the weld.
    into = [Polygon(_rect(0, 0, 100, 100))]
    grown: set[int] = set()
    _absorb(_wedge(60.0, 200.0), into, grown, 20.0, GRAIN)
    assert grown == {0}, "the weld was refused where trimming the tail would have carried it"
    assert _apex_of(into[0]) >= _WELD_MIN_APEX, "the trimmed weld still left a needle"


def test_absorb_takes_a_least_bad_weld_that_still_clears_the_gate():
    # same 16.7 deg apex, but with trimming disabled (thin ~ 0). Above the gate line, so welding it
    # beats leaving a doubled bund - a basin the gate ACCEPTS is not a defect.
    into = [Polygon(_rect(0, 0, 100, 100))]
    grown: set[int] = set()
    _absorb(_wedge(60.0, 200.0), into, grown, 0.001, GRAIN)
    assert grown == {0}


def test_absorb_leaves_the_scrap_bare_when_every_weld_would_make_a_real_needle():
    # 60/300 -> 11.3 deg, below the gate line, and trimming is disabled: welding this would ship a
    # needle, so the honest answer is the odd corner left unpaddied.
    into = [Polygon(_rect(0, 0, 100, 100))]
    grown: set[int] = set()
    _absorb(_wedge(60.0, 300.0), into, grown, 0.001, GRAIN)
    assert grown == set()


def test_plant_hands_back_offcuts_rather_than_welding_them_among_siblings():
    # a body with a long thin tail: the grid cuts the body into basins and the tail into offcuts
    pocket = Polygon([(0, 0), (200, 0), (200, 40), (100, 40), (100, 160), (90, 160), (90, 40), (0, 40)])
    basins, offcuts = _plant(_Frame(90), pocket, 48.0, (26.0, 36.0), HALF)
    assert basins, "nothing plantable in a 200 x 40 body"
    assert all(not b.buffer(-HALF).is_empty for b in basins)
    assert offcuts, "the 10 px tail should have come back as an offcut, not shipped as a needle"
    assert all(o.buffer(-HALF).is_empty for o in offcuts)


def test_plant_keeps_a_pocket_whole_when_the_grid_would_cut_its_only_thick_part_up():
    # a grain fine enough that every cell is thinner than a basin - the pocket goes out as it is
    pocket = Polygon(_rect(0, 0, 40, 40))
    basins, offcuts = _plant(_Frame(90), pocket, 4.0, (4.0, 4.0), HALF)
    assert basins == [pocket]
    assert offcuts == []


@pytest.mark.parametrize("gap", [4.0, 8.0, 11.0])
def test_no_gap_narrower_than_a_basin_survives_the_pass(gap: float):
    env = _rect(10, 10, 290, 110)
    plots = _scene([_rect(10, 10, 100, 110), _rect(100 + gap, 10, 290, 110)], env)
    assert _bare_area(plots, env) < 1.0, f"a {gap} px seam survived - two walls where one belongs"


class _Refuses:
    """A geometry GEOS will node but not offset - the shape of the zero-length-edge cell that
    threw `TopologyException` out of the middle of a map generation (2026-08-17)."""

    is_empty = False

    def buffer(self, *_a, **_kw):
        from shapely.errors import GEOSException

        raise GEOSException("found non-noded intersection")


class _Cleans:
    def buffer(self, *_a, **_kw):
        return _Refuses()


def test_despike_hands_back_a_geometry_geos_refuses_to_offset():
    # tidying is not worth a failed map: the un-tidied geometry goes on, and the validity
    # round-trip on the recorded ring is what actually keeps a bad ring out
    out = _despike(_Cleans())  # type: ignore[arg-type]
    assert isinstance(out, _Refuses)


def test_despike_short_circuits_an_empty_geometry():
    assert _despike(Polygon()).is_empty


def test_close_seams_records_no_self_intersecting_ring():
    # the pass may leave ground bare; it may never record a ring that crosses itself
    env = _rect(10, 10, 290, 110)
    plots = _scene([_rect(10, 10, 100, 110), _rect(112, 10, 290, 110)], env)
    for p in plots:
        assert Polygon(p["poly"]).is_valid, f"recorded a crossing ring: {p['poly']}"


# --- a bund runs on, or it turns for a reason: `jog_steps` and the two passes that answer to it ---


def _stepped(off: float, link_at: float = 60.0, run: float = 140.0) -> list[tuple[float, float]]:
    """A basin whose north wall runs east, hops `off` px south at x=link_at, and carries on east."""
    return [(0.0, 0.0), (link_at, 0.0), (link_at, off), (link_at + run, off), (link_at + run, 100.0), (0.0, 100.0)]


def test_jog_steps_counts_a_wall_that_steps_sideways_and_carries_on():
    assert jog_steps(_stepped(9.0), GRAIN) == 1
    assert jog_steps(_rect(0, 0, 200, 100), GRAIN) == 0


def test_jog_steps_ignores_a_step_under_the_placer_floor():
    # 2 ft is the placer's line (`_JOG_OFF_FT`), one notch under the gate's 3 ft; at GRAIN 2 a foot
    # is a pixel, so 1.9 px is under it and 2.1 px is over.
    assert jog_steps(_stepped(1.9), GRAIN) == 0
    assert jog_steps(_stepped(2.1), GRAIN) == 1


def test_jog_steps_ignores_a_hop_too_long_to_be_a_step():
    # a 31 px hop is a LIMB - an L-shaped parcel, which is the honest odd shape reclamation leaves
    assert jog_steps(_stepped(31.0), GRAIN) == 0


def test_jog_steps_ignores_a_run_too_short_to_be_a_wall():
    # the run BEFORE the hop is 5 px, under the 6 ft floor: a corner nub, not a wall carrying on
    assert jog_steps(_stepped(9.0, link_at=5.0), GRAIN) == 0


def test_jog_steps_passes_a_narrow_basin_on_its_own_end_wall():
    # THE REASON HEADINGS ARE COMPARED OVER THE FULL CIRCLE - a thin rectangle is two long parallel
    # runs a short link apart, which modulo 180 deg is indistinguishable from a step.
    assert jog_steps(_rect(0, 0, 300, 9), GRAIN) == 0


def test_jog_vertices_returns_the_two_ends_of_the_hop():
    assert jog_vertices(_stepped(9.0), GRAIN) == [((60.0, 0.0), (60.0, 9.0))]


def test_jog_steps_ignores_a_gently_curving_bund():
    # THE CLAUSE THIS HOLDS. A curve sampled into segments is a run, a link and a run resuming
    # near-parallel, with a perpendicular offset of a few feet purely from the bend - so without the
    # corner test the rule fires all along it. Measured on Kuwabata, whose paddies are long curved
    # parcels: 57 reported steps on 43 plot rings, every one a smooth bend.
    curve = [(0.0, 0.0)]
    for k in range(1, 9):
        curve.append((30.0 * k, 7.0 * k + 1.5 * k * k))  # each segment turns a few degrees on the last
    curve.append((curve[-1][0], curve[-1][1] + 200.0))
    curve.append((0.0, 200.0))
    assert jog_steps(curve, GRAIN) == 0
