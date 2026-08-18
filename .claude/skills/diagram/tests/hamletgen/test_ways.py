"""Unit tests for the lanes, the connector track, and path legality (`hamletgen/ways.py`).

Split from test_hamletgen.py by feature 111; test bodies verbatim. See hamletgen/CLAUDE.md.
"""

import math

import pytest

from l7r.diagram import hamletgen as hg
from l7r.diagram.hamletgen.ways import _margin_frame, _reach
from l7r.diagram.settlement import point_in_poly

from ._builders import SQUARE, a_plan


def test_the_connector_track_leaves_the_frame_without_crossing_the_crop() -> None:
    """The guarantee is about the DRAWN path, not the straight line to its endpoint.

    This test used to assert the chord and is the reason it is worth spelling out: a track bows ~40
    px either side of its bearing, so chord and path disagree, and routing by the chord while
    drawing the bow is exactly how a connector came to be drawn through the rice with the router
    insisting it had checked."""
    plan = a_plan()
    plan.seat = hg.seat_cluster(plan)
    track = hg.connector_track(plan, (700.0, 200.0), avoid=[SQUARE])
    assert hg.path_violations(track, [SQUARE], None, []) == 0, "no segment of the drawn track may cross the crop"
    assert not (0 <= track[-1][0] <= plan.W and 0 <= track[-1][1] <= plan.H)  # ends off the canvas


def test_a_point_in_the_crop_is_pushed_out_on_the_LOCAL_edge_normal() -> None:
    """The defect the GM reported: a way's tip stopped 28 px INSIDE the paddy because it was pulled
    back along one fixed map-wide direction. The way out is the nearest OUTLINE EDGE's normal - and
    the nearest edge, not the nearest vertex, since a point deep in a lobe can have its nearest
    vertex round the far side."""
    square = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
    out = hg.push_out_of(square, (90.0, 50.0), 10.0)  # nearest edge is the right one, x=100
    assert out == pytest.approx((110.0, 50.0))
    assert hg.push_out_of(square, (50.0, 5.0), 10.0) == pytest.approx((50.0, -10.0)), "the bottom edge is nearer here"
    far = hg.push_out_of(square, (300.0, 50.0), 10.0)
    assert far == (300.0, 50.0), "a point already clear is returned untouched - this must never drag a way back in"


def test_a_way_cutting_the_field_is_bent_ROUND_it_not_nibbled_at() -> None:
    """`route_around` walks the outline between where a leg enters and where it leaves.

    The first version inserted one waypoint at the mean of the crossings and re-ran; it converged a
    few px per round and ran out of rounds still crossing, because a point pushed off the middle of
    a lobe lands right beside the leg it came from. Both the detour and the odd-hit case (a leg that
    enters and does not leave) are asserted, and so is the do-nothing case."""
    square = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
    bent = hg.route_around(square, [(-50.0, 50.0), (150.0, 50.0)], 8.0)
    assert len(bent) > 2, "a leg straight through the square must gain waypoints"
    for q in bent:
        assert not point_in_poly(q[0], q[1], square), f"{q} is still inside the crop"
    clear = [(-50.0, 200.0), (150.0, 200.0)]
    assert hg.route_around(square, clear, 8.0) == clear, "a way that never touches the field is left alone"
    stub = hg.route_around(square, [(50.0, 50.0), (150.0, 50.0)], 8.0)  # STARTS inside: one crossing, not two
    assert not point_in_poly(stub[0][0], stub[0][1], square)


def test_a_way_is_clipped_where_the_crop_begins() -> None:
    """`clip_to_clear` truncates rather than dragging a vertex, and returns NOTHING when the
    surviving run is too short to be a lane - the arm is simply not drawn."""
    assert hg.clip_to_clear([(0.0, 0.0), (100.0, 0.0)], [], 10.0) == [(0.0, 0.0), (100.0, 0.0)]
    clipped = hg.clip_to_clear([(0.0, 700.0), (900.0, 700.0)], [SQUARE], 10.0)
    assert clipped and max(p[0] for p in clipped) < 400.0
    assert hg.clip_to_clear([(395.0, 700.0), (900.0, 700.0)], [SQUARE], 10.0) == []


def test_a_shallow_crossing_is_distinguished_from_a_square_one() -> None:
    """A way may cross a ditch - that is what a plank is for - but not at a slant."""
    ditch = ((0.0, 0.0), (100.0, 0.0))
    assert not hg.shallow_crossing((50.0, -50.0), (50.0, 50.0), *ditch)  # square
    assert hg.shallow_crossing((0.0, -10.0), (100.0, 10.0), *ditch)  # a slant
    assert not hg.shallow_crossing((0.0, 100.0), (100.0, 100.0), *ditch)  # never meets it


def test_a_way_that_misses_the_watercourse_lands_on_nothing() -> None:
    """`crossing_lands_on_crop` answers about the CROSSING POINT, so a way that never meets the
    course has no crossing point and no verdict to give."""
    assert not hg.crossing_lands_on_crop((0.0, 0.0), (10.0, 0.0), (0.0, 50.0), (10.0, 50.0), [SQUARE])
    # ...and one that meets it inside the crop does
    assert hg.crossing_lands_on_crop((700.0, 300.0), (700.0, 900.0), (400.0, 700.0), (1000.0, 700.0), [SQUARE])


def test_a_way_is_clipped_at_a_watercourse_as_well_as_at_a_crop() -> None:
    """A cluster's lane arms stop at the bank: they serve the houses, and a lane that crosses a ditch
    gets a deck sized for whatever angle it happens to meet the water at."""
    ditch = [((500.0, 0.0), (500.0, 400.0))]
    clipped = hg.clip_to_clear([(100.0, 200.0), (900.0, 200.0)], [], 10.0, lines=ditch)
    assert clipped and max(p[0] for p in clipped) < 500.0, "the arm must stop short of the water"
    assert hg.clip_to_clear([(100.0, 200.0), (300.0, 200.0)], [], 10.0, lines=ditch) == [(100.0, 200.0), (300.0, 200.0)], "a run that never reaches the water is untouched"


# ---- feature 123: the lane web -------------------------------------------------------------------


def test_clear_runs_returns_every_run_not_just_the_first_or_longest() -> None:
    """A back lane interrupted by a steading is two lanes, not one shortened one.

    This is the whole difference from `clip_to_clear`, which stops at the first blockage - right for
    an arm radiating out of the cluster, wrong for a way that runs the length of the settlement and
    whose two ends are just its two ends. Measured when it was wrong: Inashiro's back lanes came back
    as 250 ft of an intended 1,400 because the sampling happened to start in the crop."""
    line = [(0.0, 0.0), (1000.0, 0.0)]
    blocker = [(400.0, -50.0), (500.0, -50.0), (500.0, 50.0), (400.0, 50.0)]
    runs = hg.clear_runs(line, [blocker], 10.0)
    assert len(runs) == 2, "the run before the blocker and the run after it"
    assert all(len(r) >= 2 for r in runs)
    assert runs[0][0][0] < 400.0 < runs[1][-1][0]


def test_clear_runs_holds_the_settlement_fabric_at_a_closer_margin_than_the_crop() -> None:
    """Two obstacle families on purpose: a web lane may not go near the crop at all, but it threads
    BETWEEN the steadings - it IS the leftover room between two plots. Held 20 ft off every wall
    there would be nowhere for it to be."""
    line = [(0.0, 0.0), (400.0, 0.0)]
    wall = [(190.0, 12.0), (210.0, 12.0), (210.0, 40.0), (190.0, 40.0)]  # 12 ft off the line
    assert len(hg.clear_runs(line, [wall], 20.0)) == 2, "as HARD ground, 20 ft, it severs the line in two"
    assert len(hg.clear_runs(line, [], 20.0, tight=[wall], tight_margin=6.0)) == 1, "as fabric, 6 ft, the lane passes unbroken"


def test_clear_runs_floor_admits_a_short_footpath_to_a_door() -> None:
    """The 70 ft floor is right for a through-lane and wrong for the path from an outlying
    steading's door to the nearest way, which is 60-odd feet by construction. Refusing those as
    stubs left eight houses unreachable while a path to each was drawn and thrown away."""
    short = [(0.0, 0.0), (60.0, 0.0)]
    assert hg.clear_runs(short, [[(500.0, 500.0), (510.0, 500.0), (510.0, 510.0)]], 20.0) == []
    assert hg.clear_runs(short, [[(500.0, 500.0), (510.0, 500.0), (510.0, 510.0)]], 20.0, floor=20.0)


def test_margin_frame_round_trips_a_point_through_arc_and_standoff() -> None:
    """`project` is the inverse of `__call__`, and the web depends on both agreeing: the cuts are
    computed from projected house positions and then mapped back out to screen."""
    plan = a_plan()
    plan.seat = hg.seat_cluster(plan)
    # A SPAN, and a `near` cloud, that describe one flank rather than the whole ring. Given neither,
    # the walk laps the field - and a frame that laps has no single answer for `project`, because two
    # stretches of it lie on top of each other. That is now capped at half the ring in the engine,
    # and the test says what a caller is expected to hand it.
    frame = _margin_frame(plan, 120.0, near=[(plan.seat["cx"], plan.seat["cy"])])
    assert frame.arc < 0.5 * sum(math.dist(plan.envelope[i], plan.envelope[(i + 1) % len(plan.envelope)]) for i in range(len(plan.envelope))) + 1.0
    for arc_f, stand in ((0.25, 40.0), (0.5, 90.0), (0.8, 15.0)):
        p = frame(frame.arc * arc_f, stand)
        got_arc, got_stand = frame.project(p)
        assert abs(got_arc - frame.arc * arc_f) < 20.0
        assert abs(got_stand - stand) < 20.0


def test_reach_measures_the_nearest_point_of_a_path_not_its_ends() -> None:
    """The same measurement `farmhouses_reach_a_way` makes. Measuring to the ENDS would call a house
    beside the middle of a long lane unreached."""
    path = [(0.0, 0.0), (1000.0, 0.0)]
    assert _reach((500.0, 30.0), path) == pytest.approx(30.0)
