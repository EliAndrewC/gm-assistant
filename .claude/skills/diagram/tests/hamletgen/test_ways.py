"""Unit tests for the lanes, the connector track, and path legality (`hamletgen/ways.py`).

Split from test_hamletgen.py by feature 111; test bodies verbatim. See hamletgen/CLAUDE.md.
"""

import math

import pytest

from l7r.diagram import hamletgen as hg
from l7r.diagram.hamletgen.ways import _margin_frame, _reach
from l7r.diagram.settlement import Settlement, point_in_poly

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
    # The barrier has to be genuinely CLOSED, not merely long: a link may now go the long way round,
    # which is the fix that joined the two halves of a split hamlet. A fence it can walk around is
    # not a test of giving up, it is a test of the detour.
    s = _StubSettlement(lanes=[[(0.0, 0.0), (0.0, 200.0)], [(900.0, 0.0), (900.0, 200.0)]])
    box = [(700.0, -300.0), (1150.0, -300.0), (1150.0, 520.0), (700.0, 520.0)]
    assert hg.ways._join_orphan_ways(s, [box], [], []) == 0
    assert len(s.M["lanes"]) == 2, "no link drawn when the orphan is walled in"


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


def test_margin_frame_without_a_house_cloud_falls_back_to_the_along_axis() -> None:
    """`near` is the placed houses, and callers inside the engine always have them. The fallback is
    for a caller that does not - it walks the outline by the seat band's own lateral reach instead,
    which is the same test `front_row` makes."""
    plan = a_plan()
    plan.seat = hg.seat_cluster(plan)
    frame = _margin_frame(plan, 150.0)
    assert frame.arc > 0.0
    assert len(frame.pts) >= 2


def test_reachable_runs_with_no_candidates_is_empty() -> None:
    assert hg.ways._reachable_runs([], [((0.0, 0.0), (10.0, 0.0))]) == []
    assert hg.ways._reachable_runs([[(0.0, 0.0)]], [((0.0, 0.0), (10.0, 0.0))]) == [], "a one-point run is not a run"


def test_join_orphan_ways_on_a_map_with_one_way_has_nothing_to_join() -> None:
    s = _StubSettlement(lanes=[[(0.0, 0.0), (0.0, 200.0)]])
    assert hg.ways._join_orphan_ways(s, [], [], []) == 0


def test_draw_web_refuses_a_lane_too_short_to_be_a_way() -> None:
    """A 4 ft mark fronts nobody and reads as a speck of clipping debris - Sawada shipped 4, 12 and
    20 ft fragments, left behind when the end-trim pulled a path back to its last serving point."""
    s = _StubSettlement(lanes=[[(0.0, 0.0), (0.0, 400.0)]])
    before = len(s.M["lanes"])
    assert hg.ways._draw_web(s, [(100.0, 100.0), (104.0, 100.0)]) is False
    assert len(s.M["lanes"]) == before
    assert hg.ways._draw_web(s, [(100.0, 100.0), (100.0, 200.0)]) is True
    assert s.M["lanes"][-1]["web"] is True


def test_draw_web_refuses_a_run_with_only_one_point() -> None:
    """A single point is not a way, and it reaches `_draw_web` for a real reason rather than as a
    defensive nicety: `clear_runs` returns whatever survived clipping, and a candidate clipped down
    to one surviving vertex arrives here looking like a run. Drawing it would put a zero-length lane
    in the manifest, which every way rule then measures - `lanes_reach_something` would see a tread
    that fronts nothing and `polyline_len` would divide by a zero chord."""
    s = _StubSettlement(lanes=[[(0.0, 0.0), (0.0, 400.0)]])
    before = len(s.M["lanes"])
    assert hg.ways._draw_web(s, [(100.0, 100.0)]) is False
    assert hg.ways._draw_web(s, []) is False
    assert len(s.M["lanes"]) == before


def test_a_web_lane_snaps_its_end_onto_the_way_it_almost_meets() -> None:
    """A run that stops a few feet short of the way it aims at renders as a gap, whatever the gate
    thinks of it - acceptance tolerances are not ink tolerances. So an end within `_LANE_JOIN_FT` is
    extended onto the way it meets, but ONLY if the ground between is clear: adding those few feet
    blind put lane ink across houses and garden beds on every cohort seed the moment snapping went
    in. This pins both halves - the snap, and the refusal to snap through a steading."""
    s = _StubSettlement(lanes=[[(0.0, 0.0), (0.0, 400.0)]])
    before = len(s.M["lanes"])
    # SAMPLED like a real run: the shadow clause caps the longest UNBROKEN shadowed stretch at a
    # bundle pitch, and with only two vertices the sample step IS the whole run, so a two-point run
    # trips it on its joining end alone.
    run = [(200.0 - 182.0 * i / 10.0, 200.0) for i in range(11)]
    assert hg.ways._lay_web_lane(s, run, [], [], []) is True
    assert len(s.M["lanes"]) == before + 1
    drawn = [(round(x), round(y)) for x, y in s.M["lanes"][-1]["pts"]]
    assert (0, 200) in drawn, drawn
    # ...and the same run refused the snap when a steading stands in the gap
    s2 = _StubSettlement(lanes=[[(0.0, 0.0), (0.0, 400.0)]])
    wall = [(2.0, 180.0), (16.0, 180.0), (16.0, 220.0), (2.0, 220.0)]
    hg.ways._lay_web_lane(s2, run, [], [wall], [])
    if len(s2.M["lanes"]) > 1:
        assert (0, 200) not in [(round(x), round(y)) for x, y in s2.M["lanes"][-1]["pts"]]


def test_bridge_collinear_breaks_closes_a_hole_and_leaves_an_honest_one() -> None:
    """One street drawn as two gets the missing piece drawn. A break with something genuinely in the
    way keeps it - the route cannot be made, so the interruption stands."""
    s = _StubSettlement(lanes=[[(0.0, 0.0), (0.0, 40.0)], [(200.0, 500.0), (400.0, 500.0)], [(510.0, 500.0), (710.0, 500.0)]])
    assert hg.ways._bridge_collinear_breaks(s, [], [], []) == 1
    assert len(s.M["lanes"]) == 4

    walled = _StubSettlement(lanes=[[(0.0, 0.0), (0.0, 40.0)], [(200.0, 500.0), (400.0, 500.0)], [(510.0, 500.0), (710.0, 500.0)]])
    fence = [(440.0, 200.0), (470.0, 200.0), (470.0, 800.0), (440.0, 800.0)]
    assert walled.M["lanes"][0] is not None
    assert hg.ways._bridge_collinear_breaks(walled, [fence], [], []) == 0
    assert len(walled.M["lanes"]) == 3


def test_a_routed_path_never_passes_nearer_than_it_planned_for() -> None:
    """THE PROPERTY THE LATTICE HAS TO GUARANTEE, and did not.

    A cell was marked free by testing its CENTER, so the drawn line through a free cell could pass
    half a cell nearer an obstacle than its center did - seven feet, at a 14 ft cell. Three web lanes
    on a cohort map came within 4.0 ft of a farmhouse corner having been planned at 7, and a
    farmhouse ended up standing on the lane. This asserts the guarantee directly rather than the
    implementation: every point of the returned path clears the obstacle by the requested margin."""
    wall = [(200.0, 0.0), (240.0, 0.0), (240.0, 300.0), (200.0, 300.0)]
    gap = 7.0
    for cell in (10.0, 14.0):
        path = hg.ways._route((0.0, 400.0), (400.0, 400.0), [], [wall], [], cell=cell, gap=gap)
        assert path, f"a way round the wall exists at cell {cell}"
        worst = min(
            hg.ways.seg_dist(q[0], q[1], wall[k], wall[(k + 1) % len(wall)])
            for a, b in zip(path, path[1:], strict=False)
            for q in [(a[0] + (b[0] - a[0]) * i / 20, a[1] + (b[1] - a[1]) * i / 20) for i in range(21)]
            for k in range(len(wall))
        )
        assert worst >= gap - 0.5, f"at cell {cell} the path came within {worst:.1f} ft, planned for {gap}"


def test_route_pad_mult_is_what_lets_a_link_go_the_long_way_round() -> None:
    """A search box sized at 0.75x the gap has room for a path BETWEEN two steadings and nowhere near
    enough to find the way AROUND a field - it reported NO ROUTE for a journey that plainly exists,
    and that was a dozen houses counting as unreachable on one cohort seed."""
    barrier = [(180.0, -400.0), (220.0, -400.0), (220.0, 260.0), (180.0, 260.0)]
    a, b = (60.0, 0.0), (340.0, 0.0)
    assert hg.ways._route(a, b, [], [barrier], [], cell=12.0, pad_mult=0.75) == [], "the short box cannot see the way round"
    assert hg.ways._route(a, b, [], [barrier], [], cell=12.0, pad_mult=2.0), "the long box can"


def test_trim_to_service_trims_the_FRONT_end_too() -> None:
    """Both ends, not just the tail. This branch had no test of its own and was covered only because
    some pool map happened to lay a run whose head hung in bare grass - so a cluster-shape change
    that moved the houses took the coverage away with it, which is what a branch tested by luck
    looks like when the luck runs out."""
    run = [(-900.0, 0.0), (0.0, 0.0), (50.0, 0.0), (100.0, 0.0)]
    segs = [((100.0, -20.0), (100.0, 20.0))]
    out = hg.ways._trim_to_service(run, segs, [(0.0, 30.0)])
    assert out[0] == (0.0, 0.0), "the 900 ft head into nothing is dropped"
    assert out[-1] == (100.0, 0.0), "the end that meets a way is kept"


def test_a_web_lane_that_arrives_early_keeps_the_long_half() -> None:
    """The hairpin cure, on the side the existing test does not reach: when a run's closest approach
    to the network is an interior point, the SHORT half is the stub to drop - and which half is short
    is not always the tail. A run that touches the network 20 ft in and then travels 140 ft away is
    one lane arriving, not a lane with a tail; keeping the 20 ft head instead would delete the whole
    way and leave the houses it serves unserved."""
    s = _StubSettlement(lanes=[[(0.0, 0.0), (0.0, 400.0)]], houses=[(160.0, 230.0)])
    run = [(40.0, 200.0), (20.0, 200.0), (60.0, 200.0), (110.0, 200.0), (160.0, 200.0)]
    assert hg.ways._lay_web_lane(s, run, [], [], [], houses=[(160.0, 230.0)]) is True
    drawn = s.M["lanes"][-1]["pts"]
    assert [tuple(q) for q in drawn] == run[1:], "the 20 ft head is dropped, the 140 ft body is kept"


def test_a_web_lane_end_already_near_the_network_is_SNAPPED_onto_it() -> None:
    """The third arm of `_lay_web_lane`'s junction logic, and the only one with no test of its own: an
    end already inside `_LANE_JOIN_FT` is not linked and not refused - it is EXTENDED onto the way it
    meets, so the junction reads as a touch rather than a 12 ft gap. The snap is conditional on the
    ground between being walkable, because adding those few feet blind once put lane ink across houses
    and garden beds.

    Held here because its coverage was CACHE-DEPENDENT rather than absent (found 2026-08-19). The
    branch is exercised by regenerating a pool map, so a gate run that follows a `consts.py` change
    regenerates and covers it, while a gate run on an unchanged tree serves those maps from the gen
    cache and never executes the line. Same code, same seeds, coverage green or red depending on
    whether a cache happened to be warm - which is the flakiest kind of pass there is, and reads as a
    mystery regression when it flips."""
    lane = [(0.0, 0.0), (0.0, 400.0)]
    house = (160.0, 230.0)
    s = _StubSettlement(lanes=[lane], houses=[house])
    run = [(20.0, 200.0), (60.0, 200.0), (110.0, 200.0), (160.0, 200.0)]
    assert hg.ways._lay_web_lane(s, run, [], [], [], houses=[house]) is True
    drawn = [tuple(q) for q in s.M["lanes"][-1]["pts"]]
    assert drawn[0] == (0.0, 200.0), f"the near end should be snapped onto the lane, got {drawn[:2]}"
    assert drawn[1:] == run, "the rest of the run is unchanged - snapping adds a point, it does not re-route"


# ---- feature 126: ways split by provenance, and the settlement form ------------------------------


def test_the_form_roll_is_deterministic_and_covers_all_three_forms() -> None:
    """A seed must always produce the same form, and the cohort must actually exercise each one.

    The second half matters as much as the first: a form weighted so rarely that no cohort seed
    rolls it is a form nothing tests, and the whole point of the knob is that players can tell two
    settlements apart."""
    forms = {}
    for seed in range(48):
        plan = hg.plan_site(hg.HamletSpec(name=f"Roll-{seed}", seed=seed, households=12))
        again = hg.plan_site(hg.HamletSpec(name=f"Roll-{seed}", seed=seed, households=12))
        assert plan.settlement_form == again.settlement_form, f"seed {seed} rolled two different forms"
        forms[plan.settlement_form] = forms.get(plan.settlement_form, 0) + 1
    # PINNED TO NUCLEATED for now - the knob is live and every other part of it is tested, but the
    # per-house grove path the other two forms need has four unfixed defects (see SETTLEMENT_FORMS
    # in hamletgen/consts.py for the measurements and the sketch). This asserts the CURRENT contract
    # rather than the intended one, so that turning the forms back on fails here loudly and the test
    # is updated deliberately instead of drifting.
    assert set(forms) == {"nucleated"}, f"forms are pinned to nucleated; got {forms}"


def test_an_explicit_form_on_the_spec_beats_the_roll() -> None:
    """A pool gen pins the form the way it pins every other knob."""
    plan = hg.plan_site(hg.HamletSpec(name="Pinned", seed=3, households=12, settlement_form="dispersed"))
    assert plan.settlement_form == "dispersed"


def test_a_dispersed_hamlet_draws_no_internal_lanes() -> None:
    """The dispersed form's defining feature, pinned so a later change cannot quietly restore the web.

    A Tonami farmstead stands in the middle of its own holding; what joins it to the world is the
    connector, and what joins it to its neighbors is the field baulk. Drawing a web here would erase
    the one thing that makes the form legible at a glance."""
    plan = a_plan(settlement_form="dispersed")
    s = Settlement(W=plan.W, H=plan.H, seed=plan.spec.seed)
    s.M["houses"] = [{"x": 100.0, "y": 100.0}, {"x": 200.0, "y": 120.0}]
    hg.ways.stage_web(s, plan)
    assert not s.M.get("lanes"), "a dispersed hamlet must have no internal lane network"
    assert s.M["meta"]["lane_skeleton"] == "none"


def test_only_the_dispersed_form_short_circuits_stage_web() -> None:
    """The converse of the test above, and it needs to exist: a dispersed map with no lanes would
    also pass if `stage_web` had simply stopped drawing lanes for EVERYONE.

    The discriminator is that a nucleated map runs on past the guard into the seat-dependent code,
    so on this deliberately seatless fixture it raises where the dispersed map returned cleanly.
    That is an indirect assertion, and it is used here because building a real seat means running
    the whole pre-house pipeline; the direct evidence that nucleated maps still get lanes is the
    cohort, where they do."""
    plan = a_plan(settlement_form="nucleated")
    assert plan.settlement_form == "nucleated"
    s = Settlement(W=plan.W, H=plan.H, seed=plan.spec.seed)
    s.M["houses"] = [{"x": 100.0, "y": 100.0}, {"x": 200.0, "y": 120.0}]
    with pytest.raises(KeyError):
        hg.ways.stage_web(s, plan)
