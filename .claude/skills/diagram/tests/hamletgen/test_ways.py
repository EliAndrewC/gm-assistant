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


# ---- feature 123: the web's guard rails, each exercised on its own -------------------------------


def _lanes(*polys):
    """A minimal Settlement stand-in carrying only what the web helpers read."""

    class _S:
        def __init__(self):
            self.M = {"lanes": [{"pts": [list(map(list, p))][0], "w": 5} for p in polys], "houses": []}

        def lane(self, pts, **kw):
            self.M["lanes"].append({"pts": [list(q) for q in pts], "w": kw.get("width", 5)})

    return _S()


def test_reachable_runs_admits_a_run_that_joins_THROUGH_another_run() -> None:
    """A back lane may join through a cross-tie and a tie through a back lane - that is what makes a
    framework a framework, and it is why the decision is made over candidates rather than as each
    lane is drawn: judged one at a time, a run is refused merely for being early in the loop."""
    skeleton = [((0.0, 0.0), (100.0, 0.0))]
    touching = [(100.0, 0.0), (200.0, 0.0)]
    second_hop = [(200.0, 0.0), (300.0, 0.0)]
    island = [(9000.0, 9000.0), (9100.0, 9000.0)]
    kept = hg.ways._reachable_runs([island, second_hop, touching], skeleton)
    assert touching in kept and second_hop in kept, "the far run joins through the near one"
    assert island not in kept, "an island is never drawn"


def test_reachable_runs_with_no_seed_network_seeds_from_the_first_run() -> None:
    """A hamlet always has its skeleton by the time the web is laid, so this is a defensive branch
    rather than a real case - but it must not silently return nothing, or a map that somehow reached
    it would come out with no web at all instead of with an obvious one."""
    runs = [[(0.0, 0.0), (10.0, 0.0)], [(9000.0, 9000.0), (9010.0, 9000.0)]]
    assert hg.ways._reachable_runs(runs, []) == [runs[0]]


def test_trim_to_service_pulls_an_end_back_to_what_it_serves() -> None:
    """A tread that stops in bare grass serves nobody. Trimming happens BEFORE the ink and before the
    join is computed - trimming afterwards moves the end out from under the link drawn to it."""
    run = [(0.0, 0.0), (50.0, 0.0), (100.0, 0.0), (900.0, 0.0)]
    segs = [((0.0, -20.0), (0.0, 20.0))]
    out = hg.ways._trim_to_service(run, segs, [(100.0, 30.0)])
    assert out[-1] == (100.0, 0.0), "the 800 ft tail into nothing is dropped"
    assert out[0] == (0.0, 0.0), "the end that meets a way is kept"


def test_trim_to_service_never_trims_below_two_points() -> None:
    run = [(5000.0, 5000.0), (5100.0, 5000.0), (5200.0, 5000.0)]
    assert len(hg.ways._trim_to_service(run, [], [])) == 2


def test_route_returns_nothing_when_the_way_is_genuinely_blocked() -> None:
    """[] is a real answer. The alternative - drawing something anyway - is what produced a 38 ft
    mark 71 ft from the house it served, touching nothing, to cure a one-foot violation."""
    wall = [(40.0, -400.0), (60.0, -400.0), (60.0, 400.0), (40.0, 400.0)]
    assert hg.ways._route((0.0, 0.0), (100.0, 0.0), [wall], [], [], cell=10.0) == []


def test_route_goes_around_an_obstacle_rather_than_through_it() -> None:
    wall = [(40.0, -60.0), (60.0, -60.0), (60.0, 60.0), (40.0, 60.0)]
    path = hg.ways._route((0.0, 0.0), (100.0, 0.0), [wall], [], [], cell=8.0)
    assert path, "there is a way round the end of the wall"
    assert hg.ways.polyline_len(path) > 100.0, "going round costs more than the straight line"
    assert max(abs(q[1]) for q in path) > 40.0, "and it leaves the straight line to do it"


def test_clear_link_requires_the_WHOLE_span_not_a_piece_of_it() -> None:
    """Accepting the first surviving run let a snap be drawn across ground that had been clipped out
    of the middle - the run existed, it just was not the gap being bridged."""
    blocker = [(45.0, -30.0), (55.0, -30.0), (55.0, 30.0), (45.0, 30.0)]
    assert hg.ways._clear_link((0.0, 0.0), (100.0, 0.0), [blocker], [], []) is False
    assert hg.ways._clear_link((0.0, 0.0), (30.0, 0.0), [blocker], [], []) is True
    assert hg.ways._clear_link((0.0, 0.0), (0.2, 0.0), [blocker], [], []) is True, "a zero-length link is trivially clear"


def test_net_reach_measures_the_paths_VERTICES_against_the_network() -> None:
    """Vertex-to-segment, not segment-to-segment, and the asymmetry is worth knowing: a long straight
    run whose middle passes close to a way but whose vertices do not will read as further off than it
    looks. The web samples its runs every few feet, so in practice the vertices are the line - but a
    caller handing it a two-point polyline gets the corner distance, not the perpendicular."""
    assert hg.ways._net_reach([(0.0, 50.0), (100.0, 50.0)], [((50.0, 0.0), (60.0, 0.0))]) == pytest.approx(64.031242, abs=1e-4)
    dense = [(float(x), 50.0) for x in range(0, 101, 5)]
    assert hg.ways._net_reach(dense, [((50.0, 0.0), (60.0, 0.0))]) == pytest.approx(50.0)


class _StubSettlement:
    """The two things the web helpers touch on a Settlement: the manifest and `lane()`."""

    def __init__(self, lanes=(), houses=()):
        self.M = {
            "lanes": [{"pts": [list(q) for q in p], "w": 5, "connector": i == 0} for i, p in enumerate(lanes)],
            "houses": [{"x": x, "y": y, "w": 46.0, "h": 28.0, "rot": 0.0} for x, y in houses],
        }

    def lane(self, pts, **kw):
        self.M["lanes"].append({"pts": [list(q) for q in pts], "w": kw.get("width", 5)})


def test_a_web_lane_may_not_run_the_length_of_a_shelter_belt() -> None:
    """Crossing a belt costs it a lane's width of wall, which is a fair price for a way with
    somewhere to be. Running ALONG it splits one wind wall into two thinner ones - measured, a back
    lane 237 of 237 ft inside the belt, having deleted 15 of its 169 clumps."""
    # Houses at both ends so the run is not trimmed back before the belt rule is reached - the trim
    # runs first on purpose (see `_trim_to_service`), and a run serving nothing is dropped for that
    # reason rather than this one.
    ends = [(20.0, 190.0), (285.0, 190.0)]
    s = _StubSettlement(lanes=[[(0.0, 0.0), (0.0, 400.0)]], houses=ends)
    belt = [(-50.0, 100.0), (400.0, 100.0), (400.0, 160.0), (-50.0, 160.0)]
    lengthwise = [(float(x), 130.0) for x in range(10, 300, 5)]
    assert hg.ways._lay_web_lane(s, lengthwise, [], [], [], belts=[belt], houses=ends) is False
    crossing = [(200.0, float(y)) for y in range(60, 205, 5)]
    assert hg.ways._lay_web_lane(s, crossing, [], [], [], belts=[belt], houses=[(200.0, 70.0), (200.0, 195.0)]) is True, "crossing the belt is allowed"


def test_a_web_lane_that_cannot_reach_the_network_draws_a_link_or_is_refused() -> None:
    """A run further off than the touch tolerance gets a link drawn to the network - and if the link
    cannot be drawn, the run is not drawn either. Refusing is the right answer: the alternative is
    ink that looks like a way and is not one."""
    s = _StubSettlement(lanes=[[(0.0, 0.0), (0.0, 400.0)]], houses=[(150.0, 200.0)])
    detached = [(120.0, float(y)) for y in range(150, 255, 5)]
    before = len(s.M["lanes"])
    assert hg.ways._lay_web_lane(s, detached, [], [], [], houses=[(150.0, 200.0)]) is True
    assert len(s.M["lanes"]) == before + 2, "the link and the run"

    walled = _StubSettlement(lanes=[[(0.0, 0.0), (0.0, 400.0)]], houses=[(900.0, 200.0)])
    fence = [(300.0, -500.0), (320.0, -500.0), (320.0, 900.0), (300.0, 900.0)]
    far = [(880.0, float(y)) for y in range(150, 255, 5)]
    assert hg.ways._lay_web_lane(walled, far, [fence], [], [], houses=[(900.0, 200.0)]) is False
    assert len(walled.M["lanes"]) == 1, "nothing drawn when the link cannot be made"


def test_join_orphan_ways_gives_up_rather_than_forcing_a_link() -> None:
    """An orphan that cannot be linked stays orphaned and the gate says so. Forcing a link would draw
    a way through whatever stood between them."""
    s = _StubSettlement(lanes=[[(0.0, 0.0), (0.0, 200.0)], [(900.0, 0.0), (900.0, 200.0)]])
    fence = [(400.0, -900.0), (420.0, -900.0), (420.0, 1200.0), (400.0, 1200.0)]
    assert hg.ways._join_orphan_ways(s, [fence], [], []) == 0
    assert len(s.M["lanes"]) == 2, "no link drawn"


def test_join_orphan_ways_links_an_orphan_when_the_ground_allows() -> None:
    s = _StubSettlement(lanes=[[(0.0, 0.0), (0.0, 200.0)], [(120.0, 0.0), (120.0, 200.0)]])
    assert hg.ways._join_orphan_ways(s, [], [], []) == 1
    assert len(s.M["lanes"]) == 3


def test_a_web_lane_is_refused_when_its_link_is_blocked_though_the_gap_is_short() -> None:
    """The gap is well inside the search radius, so the run is not rejected for distance - it is
    rejected because the ground between it and the network will not take a lane. Refusing is the
    point: ink that looks like a way and is not one is worse than a house left for the footpath
    pass."""
    s = _StubSettlement(lanes=[[(0.0, 0.0), (0.0, 400.0)]], houses=[(120.0, 200.0)])
    fence = [(40.0, -400.0), (60.0, -400.0), (60.0, 800.0), (40.0, 800.0)]
    run = [(120.0, float(y)) for y in range(150, 255, 5)]
    assert hg.ways._lay_web_lane(s, run, [fence], [], [], houses=[(120.0, 200.0)]) is False
    assert len(s.M["lanes"]) == 1, "neither the link nor the run is drawn"


def test_the_footpath_search_stops_looking_past_its_backstop_radius() -> None:
    """The directness bound is the real limit on a footpath; the radius is only a backstop against
    searching the whole map. A steading this far out is beyond any path worth drawing, and the loop
    must stop rather than test every way on the sheet."""

    class _Plan:
        envelope = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)]
        watercourses: list = []

    s = _StubSettlement(lanes=[[(0.0, 0.0), (0.0, 200.0)]], houses=[(4000.0, 4000.0)])
    before = len(s.M["lanes"])
    hg.ways._serve_stragglers(s, _Plan(), [], [], [])
    assert len(s.M["lanes"]) == before, "nothing drawn for a steading beyond the backstop"
