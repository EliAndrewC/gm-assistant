"""Split from test_settlement.py by feature 025 - see tests/settlement/CLAUDE.md for the index."""

import math
import random

import pytest

import settlement
from settlement import Settlement, seg_dist
from tests.settlement._builders import _IDX_POLY, _cap020, _ladder_map, _max_turn_deg, _memo_city, _torii_city, _ward_city_with_samurai


def test_stroke_quads_makes_one_quad_per_segment():
    qs = settlement.stroke_quads([(0, 0), (100, 0), (100, 100)], 5.0)
    assert len(qs) == 2 and all(len(q) == 4 for q in qs)
    assert settlement.stroke_quads([(0, 0)], 5.0) == []
    assert settlement.stroke_quads([(7, 7), (7, 7)], 5.0)  # a degenerate segment still yields a quad rather than dividing by zero


def test_way_beds_carries_the_lane_network_lane_runs_does_not():
    # the AVOIDANCE list for a verge-hugging feature: lane_runs' roads/streets/alleys/ring road
    # PLUS the village lane network. Each siter used to build its own partial list, which is how a
    # punishment ground came to clip an alley (reported by another session, Tango 2026-07-27).
    M = {"road": [[0, 100], [500, 100]], "alleys": [{"pts": [[0, 300], [500, 300]], "w": 6}], "lane": [[0, 500], [500, 500]], "lanes": [{"pts": [[0, 700], [500, 700]], "w": 8}]}
    beds = settlement.way_beds(M)
    assert len(beds) == 4 and len(settlement.lane_runs(M)) == 2
    assert sorted(round(b[0][0][1]) for b in beds) == [100, 300, 500, 700]


def test_seg_closest_degenerate_segment():
    assert settlement.seg_closest(0, 0, (5, 5), (5, 5)) == (5, 5)


def test_shrine_hall_torii_count_pin_extends_a_single_point_avenue():
    # the per-temple pin (the per-hall analog of the village 'torii_count' knob): a pinned 7
    # marches the avenue away from the hall at the HOUSE PITCH (TORII_PITCH_FT, 20 real ft) from
    # the single given point - it was a fixed 44px until 2026-07-25, which is 132 ft at city scale
    s = _torii_city(torii_count=7)
    step = s.px(settlement.TORII_PITCH_FT)
    y0 = 500 + s.px(84) / 2 + step  # the hall's front edge + one pitch - _avenue_at_threshold owns the seat now
    assert s.M["religious"][-1]["torii_count"] == 7
    assert sorted(t[1] for t in s.M["torii"]) == pytest.approx([y0 + step * i for i in range(7)], abs=0.1)


def test_indexed_overrides_every_mutating_list_method():
    """Every way a list's CONTENT can change must bump the version, or an index cached against it
    goes stale silently - the exact failure that cost this engine two silent bugs in one day
    (a stale `placed` index, a stale well-geometry fingerprint).

    The mutator set is discovered by INTROSPECTION rather than hand-listed, so a future Python
    adding a mutating list method fails this test instead of opening a hole nobody notices.
    """
    non_mutating = {"copy", "__reversed__", "__init__", "__new__", "__class_getitem__", "__getitem__"}
    candidates = (set(dir(list)) - set(dir(tuple))) - non_mutating
    ops = {
        "append": lambda r: r.append(_IDX_POLY),
        "extend": lambda r: r.extend([_IDX_POLY]),
        "insert": lambda r: r.insert(0, _IDX_POLY),
        "remove": lambda r: r.remove(_IDX_POLY),
        "pop": lambda r: r.pop(),
        "clear": lambda r: r.clear(),
        "sort": lambda r: r.sort(),
        "reverse": lambda r: r.reverse(),
        "__setitem__": lambda r: r.__setitem__(0, _IDX_POLY),
        "__delitem__": lambda r: r.__delitem__(0),
        "__iadd__": lambda r: r.__iadd__([_IDX_POLY]),
        "__imul__": lambda r: r.__imul__(2),
    }
    assert set(ops) == candidates, f"the mutator table is out of step with list's API: {set(ops) ^ candidates}"
    for name, op in ops.items():
        assert name in settlement.Indexed.__dict__, f"Indexed does not override {name}"
        reg = settlement.Indexed([_IDX_POLY])
        before, before_appends = reg.version, reg.appends
        op(reg)
        assert reg.version > before, f"{name} changed the list without bumping the version"
        # `indexed_grid` extends a cached index instead of rebuilding it when version and appends
        # moved together, i.e. when every change was an append. That inference is only sound if
        # `appends` counts APPENDS AND NOTHING ELSE - a non-appending mutator that bumped it would
        # let a stale index survive a removal, which is the 2026-08-03 `placed` bug exactly.
        grew = name in {"append", "extend", "__iadd__", "__imul__", "insert"}
        assert (reg.appends > before_appends) == (name in {"append", "extend"}), f"{name} must {'' if grew else 'not '}bump appends"


def test_point_grid_never_omits_an_item_a_linear_scan_would_find():
    """The one property every PointGrid caller's exactness rests on: `near` may return extra items
    (or an item twice), but it must never OMIT one whose box comes within `pad` of the query.

    Includes the OVERSIZED path - a wildly-spanning box, which is what a negative fixture's
    9,000,000px vertex looks like - because that clamp is the difference between a cheap query and
    the gigabytes-of-RAM incident recorded in this skill's CLAUDE.md.
    """
    rng = random.Random(11)
    items = [(f"i{k}", *(lambda a, b, w, h: (a, b, a + w, b + h))(rng.uniform(0, 900), rng.uniform(0, 900), rng.uniform(1, 300), rng.uniform(1, 300))) for k in range(120)]
    items.append(("huge", -9_000_000.0, -9_000_000.0, 9_000_000.0, 9_000_000.0))  # the clamp case
    grid = settlement.PointGrid()
    grid.extend(items)
    assert grid.n == len(items) and grid.oversized, "the wild box must be filed as oversized, not as billions of cells"
    for pad in (0.0, 5.0, 140.0):  # 140 > cell, so the query spans several cells
        for _ in range(400):
            px, py = rng.uniform(-100, 1000), rng.uniform(-100, 1000)
            want = {it[0] for it in items if it[1] - pad <= px <= it[3] + pad and it[2] - pad <= py <= it[4] + pad}
            got = {it[0] for it in grid.near(px, py, pad)}
            assert want <= got, f"grid OMITTED {want - got} at ({px:.1f}, {py:.1f}) pad={pad}"


def test_boxed_prefilters_agree_exactly_with_the_bare_scan():
    """The bbox PRUNES, the exact test DECIDES - so the prefiltered answer must equal the naive
    one at EVERY point, especially in the near-edge band the pad exists for.

    This is the ratchet behind "the pool regenerates byte-identical" (2026-08-03): the tempting
    way to speed a scatter up is to COARSEN it - a tighter pad, a bbox-only answer, fewer sample
    points - and the loss would show up not here but as silently-moved ground cover on some map
    nobody re-renders for a month. Coarsening fails this test instead.
    """
    polys = [
        [(100.0, 100.0), (200.0, 100.0), (200.0, 180.0), (100.0, 180.0)],
        [(220.0, 40.0), (300.0, 90.0), (250.0, 160.0)],  # a triangle: bbox and shape differ a lot
    ]
    corr = [([(0.0, 0.0), (400.0, 300.0)], 9.0), ([(50.0, 250.0), (350.0, 250.0)], 4.0)]
    boxed0, boxed10 = settlement.boxed_polys(polys), settlement.boxed_polys(polys, 10.0)
    segs = settlement.boxed_segs(corr)
    rng = random.Random(7)
    hits = 0
    for _ in range(4000):
        px, py = rng.uniform(-20, 420), rng.uniform(-20, 320)
        naive_in = any(settlement.point_in_poly(px, py, p) for p in polys)
        naive_pad = any(settlement.point_in_poly(px, py, p) or settlement.edge_dist(px, py, p) < 10.0 for p in polys)
        naive_seg = any(any(seg_dist(px, py, pl[i], pl[i + 1]) < hw for i in range(len(pl) - 1)) for pl, hw in corr)
        assert settlement.boxed_hit(px, py, boxed0) == naive_in, (px, py)
        assert settlement.boxed_hit(px, py, boxed10, 10.0) == naive_pad, (px, py)
        assert settlement.boxed_seg_hit(px, py, segs) == naive_seg, (px, py)
        hits += naive_in or naive_pad or naive_seg
    assert 200 < hits < 3800, f"the sample must straddle both answers to have teeth, got {hits}/4000"


def test_union_area_empty_and_overlapping_spans():
    # empty (or all-degenerate) rects -> zero area; and a rect fully shadowed by a taller one in the
    # same x-slab must be counted ONCE (the y1 <= cy skip), not double-counted.
    assert settlement._union_area([]) == 0.0
    assert settlement._union_area([(0, 0, 2, 2)]) == 4.0  # single rect
    assert settlement._union_area([(0, 0, 10, 10), (0, 2, 10, 5)]) == 100.0  # inner rect adds nothing


def test_main_tree_guard_blocks_main_allows_clones_and_gm_override(monkeypatch):
    monkeypatch.delenv("GM_ASSISTANT_ALLOW_MAIN", raising=False)
    # running from the MAIN integration tree aborts with the CLAUDE.md reminder
    with pytest.raises(SystemExit, match="Session clones"):
        settlement._assert_not_main_tree("/gm-assistant/.claude/skills/diagram/settlement.py")
    # a session clone under .clones/ is the sanctioned workspace
    settlement._assert_not_main_tree("/gm-assistant/.clones/x/.claude/skills/diagram/settlement.py")
    # any tree outside /gm-assistant (the GM's laptop checkout) is not main
    settlement._assert_not_main_tree("/home/eli/l7r/gm-assistant/.claude/skills/diagram/settlement.py")
    # the GM's deliberate override opens main
    monkeypatch.setenv("GM_ASSISTANT_ALLOW_MAIN", "1")
    settlement._assert_not_main_tree("/gm-assistant/.claude/skills/diagram/settlement.py")


def test_fillet_polyline_rounds_a_square_corner_into_a_sweep():
    # a right-angle elbow becomes a swept bend: no vertex still turns anywhere near 90 degrees, the
    # ends are untouched (a snapped pond/moat mouth must stay exactly where it was), and the corner
    # itself is gone from the line
    pts = [(0.0, 0.0), (200.0, 0.0), (200.0, 200.0)]
    out = settlement.fillet_polyline(pts, 25.0)
    assert out[0] == (0.0, 0.0) and out[-1] == (200.0, 200.0)
    assert (200.0, 0.0) not in out
    assert _max_turn_deg(out) < 20  # was 90
    assert len(out) == 9  # the two ends plus the arc's 7 samples


def test_fillet_polyline_caps_the_bend_on_short_segments():
    # the cut-back never exceeds 35% of either leg, so two corners cannot eat the segment between
    # them and a short stub keeps its shape (radius 500 asked for on 100px legs)
    out = settlement.fillet_polyline([(0.0, 0.0), (100.0, 0.0), (100.0, 100.0)], 500.0)
    assert min(x for x, _ in out[1:-1]) >= 64.9  # 100 - 35% of the leg
    assert max(y for _, y in out[:-1]) <= 35.1


def test_fillet_polyline_leaves_gentle_bends_and_degenerate_input_alone():
    gentle = [(0.0, 0.0), (100.0, 2.0), (200.0, 4.0)]  # ~0 degrees of turn: nothing to round
    assert settlement.fillet_polyline(gentle, 25.0) == gentle
    assert settlement.fillet_polyline([(0.0, 0.0), (10.0, 0.0)], 25.0) == [(0.0, 0.0), (10.0, 0.0)]  # too few points
    assert settlement.fillet_polyline([(0.0, 0.0), (10.0, 0.0), (20.0, 0.0)], 0.0) == [(0.0, 0.0), (10.0, 0.0), (20.0, 0.0)]  # no radius
    dup = [(0.0, 0.0), (100.0, 0.0), (100.0, 0.0), (100.0, 100.0)]  # a repeated vertex bends nothing
    assert settlement.fillet_polyline(dup, 25.0)[0] == (0.0, 0.0)


def test_region_blocked_catches_a_keepout_against_a_cell_EDGE():
    """The bug this exists to stop: a keep-out sitting against the middle of a cell EDGE touches
    neither the center nor any corner, so center-plus-corner sampling passes it. That is how a
    wellhead ended up 1 px inside a hatake plot with every sample point clear."""
    cell = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
    assert not settlement.region_blocked(cell, [], [], [], [])
    # a small circle hugging the middle of the LEFT edge - no corner is near it, the center is 50 away
    assert settlement.region_blocked(cell, [], [(-4.0, 50.0, 6.0)], [], [])
    assert not settlement.region_blocked(cell, [], [(-40.0, 50.0, 6.0)], [], [])
    assert settlement.region_blocked(cell, [(-4.0, 50.0, 6.0)], [], [], [])  # same, as a pond
    # a ditch threading across the cell's middle, touching no corner
    assert settlement.region_blocked(cell, [], [], [([(-20.0, 50.0), (120.0, 50.0)], 1.0)], [])
    assert not settlement.region_blocked(cell, [], [], [([(-20.0, 300.0), (120.0, 300.0)], 1.0)], [])
    # a polygon overlapping a corner
    assert settlement.region_blocked(cell, [], [], [], [[(90.0, 90.0), (150.0, 90.0), (150.0, 150.0), (90.0, 150.0)]])
    assert not settlement.region_blocked(cell, [], [], [], [[(300.0, 300.0), (350.0, 300.0), (350.0, 350.0), (300.0, 350.0)]])


def test_quad_hits_seg_covers_all_three_ways_a_line_can_meet_a_cell():
    """A stroked line meets a cell in three distinct ways, and each needs its own test: an ENDPOINT
    lying in (or near) the cell, the line CROSSING an edge, and the line merely GRAZING a corner
    without crossing anything. The third is the one that point sampling misses."""
    cell = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
    assert settlement.quad_hits_seg(cell, (50.0, 50.0), (300.0, 50.0), 1.0)  # endpoint INSIDE
    assert settlement.quad_hits_seg(cell, (-50.0, 50.0), (150.0, 50.0), 1.0)  # CROSSES both edges
    assert settlement.quad_hits_seg(cell, (-50.0, -5.0), (150.0, -5.0), 8.0)  # GRAZES the top corners
    assert not settlement.quad_hits_seg(cell, (-50.0, -5.0), (150.0, -5.0), 2.0)  # ...same line, too thin to reach
    assert not settlement.quad_hits_seg(cell, (-50.0, 500.0), (150.0, 500.0), 8.0)  # nowhere near


def test_point_quad_dist_is_zero_inside_and_grows_outside():
    cell = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    assert settlement.point_quad_dist(5, 5, cell) == 0.0
    assert 2.9 < settlement.point_quad_dist(-3, 5, cell) < 3.1


def test_ward_interior_returns_none_on_a_zero_perimeter_wall():
    # a "ring" of coincident points has zero perimeter - nothing to walk an arc along
    assert settlement.ward_interior([(400, 945), (400, 400)], [(7, 7), (7, 7), (7, 7)]) is None


# ---- angled-building captions (GM 2026-08-02): a label tilts with the feature it names ----------
def test_label_tilt_folds_to_the_nearest_horizontal_edge_family():
    assert [settlement.label_tilt(r) for r in (0, 90, 180, 270, -90)] == [0.0] * 5
    assert settlement.label_tilt(-16) == -16.0
    assert settlement.label_tilt(150) == -30.0  # the Hoshizora forge: reads along its long side
    assert settlement.label_tilt(102) == 12.0  # the Ubame tanning yard: the other edge family
    assert settlement.label_tilt(67.1) == -22.9  # the Tango tanning yard
    assert settlement.label_tilt(-104) == -14.0
    assert settlement.label_tilt(90.02) == 0.0  # float noise snaps level


def test_linear_tilt_clamps_where_label_tilt_folds():
    # A LINE has one axis, not a box's two edge families (GM 2026-08-08). Past 45deg a linear
    # caption goes LEVEL - the GM's north-south convention - where the fold would swing it onto a
    # cross direction nothing is drawn at. The pair below is the whole distinction.
    assert settlement.linear_tilt(0) == 0.0
    assert settlement.linear_tilt(-26.6) == -26.6  # Hoshizora's Imperial Road
    assert settlement.linear_tilt(153.4) == -26.6  # ...the same line stored the other way round
    assert settlement.linear_tilt(90) == 0.0  # due north-south: the caption still reads left-to-right
    assert settlement.linear_tilt(72) == 0.0  # Nagahara's approach - too steep to tilt with
    assert settlement.label_tilt(72) == -18.0  # ...which is exactly what a BOX subject wants, and would be wrong here
    assert settlement.linear_tilt(45) == 45.0  # the cutoff is inclusive
    assert settlement.linear_tilt(45.1) == 0.0
    assert settlement.linear_tilt(180.02) == 0.0  # float noise snaps level


def test_label_ladder_seats_a_tilted_caption_by_its_THICKNESS_not_its_rotated_aabb():
    # The defect this pins (GM 2026-08-08): probing the rotated AABB made a diagonal caption reach
    # by most of its own LENGTH in the one direction it does not extend, so "Imperial Road" seated
    # 64px off a clear roadbed. The support is exact in every direction, so a tilted caption tucks
    # in at the same LABEL_MIN_AIR a level one gets.
    s = _ladder_map()
    box = (400.0, 480.0, 600.0, 520.0)
    seat = s._best_label_spot(box, "Imperial Road", 12, tilt=-26.6)
    quad = settlement.label_quad([*s._label_box(*seat, "Imperial Road", 12), 0, "Imperial Road", None, -26.6])
    corners = [(box[0], box[1]), (box[2], box[1]), (box[2], box[3]), (box[0], box[3])]
    assert settlement.poly_gap(quad, corners) < settlement.LABEL_MIN_AIR + 1


def test_label_quad_and_aabb_rotate_the_record_about_its_center():
    lvl = [0.0, 0.0, 100.0, 10.0, 1, "x"]
    assert settlement.label_quad(lvl) == [(0.0, 0.0), (100.0, 0.0), (100.0, 10.0), (0.0, 10.0)]
    assert settlement.label_aabb([*lvl, None]) == (0.0, 0.0, 100.0, 10.0)  # a ref-carrying level record reads the same
    tl = [*lvl, None, 30.0]
    q = settlement.label_quad(tl)
    c30, s30 = math.cos(math.radians(30)), math.sin(math.radians(30))
    assert q[0] == pytest.approx((50 - 50 * c30 + 5 * s30, 5 - 50 * s30 - 5 * c30))
    a = settlement.label_aabb(tl)
    assert a[3] - a[1] > 10 and a[2] - a[0] < 100  # taller and narrower, as a tilted run must be


def test_tilt_caption_seat_picks_the_perpendicular_half_extent_by_fold_family():
    a = math.radians(-30.0)
    # rot=150 folds to -30 with the footprint's LOCAL h perpendicular to the baseline
    assert settlement.tilt_caption_seat(0, 0, 150, -30.0, 50, 10, 11) == pytest.approx((-math.sin(a) * 21, math.cos(a) * 21))
    # rot=102 folds to 12: the other family - the local w lies perpendicular
    b = math.radians(12.0)
    assert settlement.tilt_caption_seat(0, 0, 102, 12.0, 50, 10, 11) == pytest.approx((-math.sin(b) * 61, math.cos(b) * 61))
    # above=True mirrors the seat to the upper edge
    assert settlement.tilt_caption_seat(0, 0, 150, -30.0, 50, 10, 11, above=True) == pytest.approx((math.sin(a) * 21, -math.cos(a) * 21))


def test_servant_ranges_keeps_every_range_inside_the_fence():
    # a house hard against the ward fence must not be ranged out through it
    s = _ward_city_with_samurai((412, 600, "samurai", 0.0))
    s.servant_ranges()
    for r in [b for b in s.M["buildings"] if b["kind"] == "servant"]:
        assert settlement.point_in_poly(r["x"], r["y"], s._samurai_ward_interiors[0])
        assert min(settlement.seg_dist(r["x"], r["y"], (400, 795), (400, 400)), settlement.seg_dist(r["x"], r["y"], (400, 400), (795, 400))) > s._WARD_STROKE


def test_poly_gap_measures_true_clearance_and_zero_on_overlap():
    # the exact vertex-to-edge minimum, and 0.0 the moment two quads intersect - the measurement
    # servant_ranges uses to refuse a seat that touches a non-host more closely than its own host
    a = settlement.rot_rect(0, 0, 10, 10, 0)
    assert settlement.poly_gap(a, settlement.rot_rect(20, 0, 10, 10, 0)) == pytest.approx(10.0)
    assert settlement.poly_gap(a, settlement.rot_rect(10, 0, 10, 10, 0)) == pytest.approx(0.0)  # touching
    assert settlement.poly_gap(a, settlement.rot_rect(5, 0, 10, 10, 0)) == 0.0  # overlapping


def test_seat_memo_forgets_when_a_registry_is_rebound_or_truncated():
    # `placed` is rebound to a filtered copy in two places in this engine, and that is precisely
    # what defeated the previous attempt at an incremental index over it
    s, memo = _memo_city()
    memo.level("laborer", 10, 6, 7).add((100.0, 200.0))
    s.placed = settlement.Indexed()
    memo.sync()
    assert (100.0, 200.0) not in memo.level("laborer", 10, 6, 7)

    s2, memo2 = _memo_city()
    s2.M["buildings"].append({"x": 1, "y": 2, "w": 3, "h": 4, "kind": "laborer"})
    memo2.sync()
    memo2.level("laborer", 10, 6, 7).add((100.0, 200.0))
    s2.M["buildings"].clear()  # a plain list has only identity + length as a witness; length is enough here
    memo2.sync()
    assert (100.0, 200.0) not in memo2.level("laborer", 10, 6, 7)


def test_full_tilt_lays_a_row_caption_along_the_row():
    """GM 2026-08-09: linear subjects may carry the FULL tilt (linear_tilt_full), past the
    45-degree go-level clamp the road captions keep - a -54 deg granary row's caption lies
    along the row, and a bearing and its reverse caption identically."""
    assert settlement.linear_tilt_full(-54) == -54.0
    assert settlement.linear_tilt_full(126) == -54.0
    assert settlement.linear_tilt_full(0) == 0.0
    s = _cap020()
    s.granary(700, 700, n=3, w=20, h=12, gap=8, label="domain granaries", append=True, rot=-54)
    assert "rotate(-54" in "".join(s.out)  # the caption carries the row's own angle


def test_a_rolled_cluster_band_is_sized_in_REAL_FEET_at_the_map_s_grain():
    """THE RATCHET for the other half of that fix (see `roll_village`).

    A cluster band is sized per homestead BUNDLE - house plus its yard and dooryard garden, ~92 ft
    of pitch once the placer's collision circles are paid for - and that is a REAL-FEET quantity, so
    the band must shrink with the map's grain. It used to convert through `bscale`, which every tier
    pins to 1/ftpx except villages, which pin it to 1.0 for legacy reasons; a village band was
    therefore asked for twice the ground its (half-size) bundles occupy and strung its cluster thin
    over a hollow hull. The failure mode of the ORIGINAL 56 ft figure is nastier and is why this is
    pinned: too small does not show up as a shortfall, because the caller keeps seeding until the
    quota is met - it shows up as a cluster too solid to seat a wellhead in."""
    hamlet, village = Settlement(900, 900, seed=1), Settlement(900, 900, seed=1)
    hamlet.meta(scale="hamlet", ftpx=1)
    village.meta(scale="village", ftpx=2)
    assert hamlet.px(settlement.BUNDLE_PITCH_FT) == pytest.approx(settlement.BUNDLE_PITCH_FT)
    assert village.px(settlement.BUNDLE_PITCH_FT) == pytest.approx(settlement.BUNDLE_PITCH_FT / 2)
