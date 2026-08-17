"""Split from test_settlement.py by feature 025 - see tests/settlement/CLAUDE.md for the index."""

import math
import random

import pytest

from l7r.diagram.settlement import Settlement
from tests.settlement._builders import _crop_settlement, _nuc_village, _town, _village


def test_nucleated_cluster_is_grove_less_with_yards_and_gardens():

    s = _nuc_village()
    s.lane([(300, 180), (322, 620)], width=5, clearance=11, worn=True)  # the WORN (unpaved) lane branch
    s.headman(560, 300)  # headman = a LARGER plain farmhouse
    rng, n = random.Random(3), 1
    for _ in range(80):
        if n >= 14:
            break
        if s.try_place(500 + rng.uniform(-120, 120), 460 + rng.uniform(-200, 200), "plain"):
            n += 1
    drawn = s.farmsteads()
    assert drawn >= 10
    assert s.M["lanes"] and s.M["lanes"][0]["worn"] is True  # worn lane recorded
    assert not s.M["groves"]  # nucleated -> NO per-house grove
    assert len(s.M["threshing_yards"]) >= drawn - 1  # each homestead keeps a yard
    assert len(s.M["gardens"]) >= drawn - 1  # ... and an (adaptive-side) garden
    hm = [h for h in s.M["houses"] if h.get("role") == "headman"][0]
    assert hm["kind"] == "plain" and hm["w"] >= 40  # the headman is a plain, larger house
    assert all(h["w"] <= hm["w"] for h in s.M["houses"])  # ... and the largest


def test_rect_hits_detects_a_pure_edge_crossing():
    # the _rect_hits edge-cross arm: a plus-sign where neither shape has a corner/vertex inside the
    # other, but their edges cross - the corner-in / vertex-in fast paths both miss, so only the
    # per-edge segments_cross catches it. Plus a bbox-disjoint poly to exercise the early reject.
    s = _crop_settlement()
    assert s._rect_hits((500, 500, 200, 40), [[(480, 400), (520, 400), (520, 600), (480, 600)]])
    assert not s._rect_hits((500, 500, 40, 40), [[(900, 900), (950, 900), (950, 950), (900, 950)]])


def test_farmsteads_legacy_skips_grove_for_a_city_intramural_farm():
    # the legacy farmsteads inwall-grove skip: a farm INSIDE a city wall (scale=city, inwall_groves off)
    # gets no windward grove (intramural land is too precious and the urban fabric shelters it). Uses the
    # legacy house-first path (city is not to-scale), with a wall enclosing the whole ring of farms.
    s = Settlement(1200, 900, seed=3)
    s.meta(name="C", scale="city")  # city + not toscale -> legacy path
    fld = (300, 300, 620, 560)
    s.paddy_field(fld, "", "f", amp=20)
    s.ring(fld, 8, 16, ["plain"])
    s.M["wall"] = [(120, 120), (760, 120), (760, 720), (120, 720)]  # encloses the whole ring of farms
    n = s.farmsteads()
    assert n > 0 and not s.M["groves"]  # every intramural farm skipped its grove


def test_rect_on_water_blocks_a_solid_part_on_an_irrigation_line():
    # the homestead solver rejects a house/yard/garden that lands on a channel/ditch/stream, but NOT the grove
    s = _crop_settlement()
    s.M["field_ditches"] = [{"poly": [(400, 300), (400, 500)], "role": "drain", "w": 6, "field": "f"}]
    s.M["channels"] = [{"poly": [(600, 300), (600, 500)], "w": 2.5}]
    s.M["streams"] = [{"poly": [(800, 300), (800, 500)], "w": 9}]
    assert s._rect_on_water((400, 400, 24, 16)) is True  # garden straddling the drain -> seg_dist branch
    assert s._rect_on_water((360, 400, 100, 10)) is True  # a wide rect an edge of which the ditch CROSSES far from any corner -> segments_cross branch
    assert s._rect_on_water((600, 400, 20, 14)) is True  # on the feeder channel
    assert s._rect_on_water((800, 400, 20, 14)) is True  # on the stream
    assert s._rect_on_water((500, 400, 24, 16)) is False  # dry ground between them -> clear
    # the grove (fields=False) is exempt - it may hug a bund/ditch; the solid parts (fields=True) are not
    assert s._rect_blocked((400, 400, 24, 16), fields=False) is False
    assert s._rect_blocked((400, 400, 24, 16), fields=True) is True


def test_rect_on_water_skips_a_degenerate_course_and_far_ones():
    # the collision pre-filter: a degenerate (<2-point) course is dropped from _water_obstacles (it has no
    # segment and would crash the bbox min/max on an empty poly), and a course whose bbox is nowhere near
    # the rect is skipped without any seg_dist / crossing math.
    s = _crop_settlement()
    s.M["streams"] = [
        {"poly": [(100, 100)], "w": 9},  # degenerate: single point -> skipped
        {"poly": [(1500, 1300), (1500, 1400)], "w": 9},
    ]  # real, but far from the probe rect
    assert s._water_obstacles() == [(s.M["streams"][1]["poly"], 9 / 2 + 5, (1500, 1300, 1500, 1400))]
    assert s._rect_on_water((400, 400, 24, 16)) is False  # far course bbox-rejected -> clear


def test_slide_nuc_stops_when_already_at_target():
    # a target function returning the current point -> distance 0 < 1.5 -> the immediate-break branch
    s = _nuc_village()
    assert s._slide_nuc(500, 500, 23, 14, lambda cx, cy: (cx, cy)) == (500, 500)


def test_garden_shaded_detects_a_house_to_the_south():
    s = _nuc_village()
    s.M["houses"].append({"x": 400, "y": 470, "w": 23, "h": 14})  # a house just SOUTH of the garden
    assert s._garden_shaded((400, 450, 22, 12)) is True  # shaded
    assert s._garden_shaded((900, 450, 22, 12)) is False  # open sky to the south -> not shaded


def test_headman_refuses_a_non_toscale_map():
    # the legacy (pre-to-scale) headman rec branch was dead code after the Hikari fix and is gone
    s = Settlement(800, 800, seed=5)
    s.meta(name="T", scale="town")
    with pytest.raises(ValueError):
        s.headman(400, 400)


def test_garden_beds_clear_rejects_a_bed_on_a_neighbor():
    # the neighbor-footprint hit branch: a shifted bed landing on an actual drawn structure is rejected
    s = Settlement(800, 800, seed=5)
    s.meta(name="B", scale="village", ftpx=2, toscale=True)
    assert s._garden_beds_clear([(100, 100, 20, 14)], others=[(104, 102, 20, 14)]) is False
    assert s._garden_beds_clear([(100, 100, 20, 14)], others=[(300, 300, 20, 14)]) is True


def test_closest_on_seg_degenerate_segment():
    # a zero-length segment returns its own endpoint (no division by zero)
    assert Settlement._closest_on_seg(0, 0, 5, 5, 5, 5) == (5, 5)


def test_bundle_fits_rejects_a_bundle_spilling_outside_the_bound():
    # a homestead bundle whose grove/garden corner falls outside the settlement bound is rejected
    s = _village()
    s.bound = [(100, 100), (500, 100), (500, 500), (100, 500)]
    assert s._bundle_fits(s._bundle_geom(120, 120, 40, 26)) is False


def test_slide_stops_on_no_target_and_on_arrival():
    # _slide halts when the target function yields None (nowhere to go) and when it is already on target
    s = _village()
    assert s._slide(200, 200, 40, 26, lambda x, y: None, True) == (200, 200)
    assert s._slide(200, 200, 40, 26, lambda x, y: (x, y), True) == (200, 200)


def test_kura_side_flips_to_the_north_wall_when_the_west_is_taken():
    # A legacy farmstead reserves its base rect but DRAWS its west kura past it, so the side is
    # chosen at flush time against the neighbors actually on the ground (Minami 2026-08-08, a farm
    # shed drawn on a garden). West by default, north when the west is taken - and when BOTH are
    # taken the west stands, so the overlap matrix reports a homestead with no room for its kura
    # rather than the engine hiding it.
    s = Settlement(600, 600, seed=1)
    s.meta(name="V", scale="village", ftpx=2)
    rec = {"x": 300.0, "y": 300.0, "w": 44.0, "h": 29.0, "rot": 0.0, "shed": True}
    assert s._kura_side(rec, 44.0, 29.0) == "W"
    s.M["gardens"].append({"x": 300 - 0.64 * 44, "y": 300.0, "w": 10.0, "h": 10.0})  # a neighbor's bed on the west wall
    assert s._kura_side(rec, 44.0, 29.0) == "N"
    s.M["gardens"].append({"x": 300.0, "y": 300 - 0.60 * 29, "w": 10.0, "h": 10.0})  # ...and one on the back wall too
    assert s._kura_side(rec, 44.0, 29.0) == "W"


def test_legacy_dispersed_farmstead_path_still_covered():
    # every POOL map is now to-scale, so keep the legacy (non-to-scale) DISPERSED path covered here: an old-style
    # hamlet (scale!=village, no toscale -> _toscale() False) rings its field with houses and draws farmsteads
    # via _try_place_legacy + _farmsteads_legacy (the pre-bundle path Moritono used before it was redone).
    s = Settlement(1200, 900, seed=3)
    s.meta(name="L", scale="hamlet")
    fld = (300, 300, 620, 560)
    s.paddy_field(fld, "", "f", amp=20)
    s.ring(fld, 8, 16, ["plain"])
    n = s.farmsteads()
    assert n > 0


def test_relax_gardens_south_skips_a_bundle_without_gardens():
    # defensive: a homestead bundle whose geom carries no garden beds is simply skipped (no shift, no error)
    s = Settlement(800, 800, seed=1)
    s.meta(name="V", scale="village", ftpx=2)
    rec = {"x": 100, "y": 100, "w": 23, "h": 14, "geom": {"house": (100, 100, 23, 14), "yard": (100, 120, 20, 16)}}  # no "gardens" key
    s._relax_gardens_south([rec])
    assert "gardens" not in rec["geom"]


def test_relax_gardens_south_nudges_an_east_shaded_garden_south():
    # a garden on the E lee side with a neighbor grove hard against its east, open ground south -> it shifts S
    s = Settlement(800, 800, seed=1)
    s.meta(name="V", scale="village", ftpx=2)
    s.grove_rects = [(340, 300, 16, 40)]  # a neighbor grove arm just east of the garden
    beds = [(320, 300, 12, 12)]  # garden east edge x=326; tree west edge=332 (in band)
    rec = {"x": 300, "y": 300, "w": 23, "h": 14, "geom": {"house": (300, 300, 23, 14), "yard": (300, 322, 20, 12), "gardens": list(beds)}}
    s._relax_gardens_south([rec])
    assert rec["geom"]["gardens"][0][1] > 300  # the bed moved SOUTH to clear the east tree


# ---- _rect_blocked: the hill/pond ELLIPSE branch -------------------------------------------
def test_rect_blocked_by_a_hill_or_pond_ellipse():
    s = _village()
    s.ellipses.append((300, 300, 80, 60))  # a hill/pond footprint
    assert s._rect_blocked((300, 300, 40, 26), fields=False) is True  # bed center inside the ellipse


# ---- _bundle_side_fits: the OUT-OF-BOUNDS bbox branch --------------------------------------
def test_bundle_side_fits_rejects_a_bbox_running_off_the_canvas():
    s = _village()
    geom = {"bbox": (5, 300, 40, 26), "gardens": []}  # cx - W/2 = -15 < 6 -> spills off the west edge
    assert s._bundle_side_fits(geom) is False


# ---- _garden_beds_clear: a bed landing on a paddy ------------------------------------------
def test_garden_beds_clear_rejects_a_bed_on_a_paddy():
    s = _nuc_village()  # field_polys carries a paddy over the east half (x >= 640)
    assert s._garden_beds_clear([(880, 400, 30, 20)], []) is False  # bed sits in the paddy


# ---- ring: a BIG house whose placement FAILS is un-counted ---------------------------------
def test_ring_decrements_the_big_count_when_a_placement_fails():
    # every candidate lands on paddy (whole map is a field), so try_place fails; each 'big' that was
    # counted up must be counted back down, leaving the tally at zero.
    s = _nuc_village()
    s.field_polys.append([(0, 0), (1200, 0), (1200, 900), (0, 900)])  # the entire canvas is flooded paddy
    s._nbig = 0
    s.ring((100, 100, 500, 500), 8, 30, ["big"], max_big=10)
    assert s._nbig == 0  # each big incremented then decremented on its failed placement
    assert not s.M["houses"]  # nothing could be placed


def test_roll_village_is_deterministic_and_seed_varies_the_combination():
    # US2 (SC-004): the same seed rolls the SAME combination (byte-identical), a different seed rolls a
    # DIFFERENT one, and a rolled map is populated with no hand-placed coordinates.
    def roll(seed):
        s = Settlement(W=2000, H=2600, seed=seed)
        s.meta(name="R", scale="hamlet", ftpx=1, toscale=True, households=18, field_footbridges=True)
        return s, s.roll_village("R", households=18, down_deg=90, water_kind="pond", field_fall=1260)

    s7a, k7a = roll(7)
    _s7b, k7b = roll(7)
    assert k7a == k7b  # same seed -> identical roll
    _s8, k8 = roll(8)
    combo = ("cluster_position", "cluster_shape", "lane_skeleton", "water_source_position")
    assert tuple(k7a[c] for c in combo) != tuple(k8[c] for c in combo)  # different seeds -> different combination
    assert 15 <= len(s7a.M["houses"]) <= 19 and s7a.M["fields"] and s7a.view  # a populated, framed map


def test_waterfront_seeds_line_both_banks_of_a_canal():
    import random as _r

    s = Settlement(1600, 1600, seed=1)
    s.meta(name="Wt", scale="village")
    canal = [(200, 200), (200, 700), (500, 1200)]  # a BENT canal (2 segments) so later seeds fall past the first
    seeds = s.waterfront_seeds(canal, 20, 60.0, _r.Random(3))
    assert len(seeds) == 20 and s.M["meta"]["settlement_form"] == "water_town"
    # seeds sit on BOTH banks (both sides of x=200), offset ~60px
    xs = [p[0] for p in seeds]
    assert any(x > 250 for x in xs) and any(x < 150 for x in xs)
    # record=False leaves meta untouched
    s2 = Settlement(1600, 1600, seed=1)
    s2.meta(name="Wt2", scale="village")
    s2.waterfront_seeds(canal, 6, 60.0, _r.Random(1), record=False)
    assert "settlement_form" not in s2.M["meta"]


def test_roll_village_stream_fed_with_a_pinned_water_source():
    # exercises the STREAM water path (a brook entering from a canvas edge) and a PINNED water_source_position
    # (edge_N is a legal stream source for a south-falling field). Covers the stream branches in roll_village +
    # draw_comb_field that the pond-fed demos do not.
    s = Settlement(W=2000, H=2600, seed=7)
    s.meta(name="Sr", scale="hamlet", ftpx=1, toscale=True, households=18, field_footbridges=True)
    s.pin_knob("water_source_position", "edge_N")
    k = s.roll_village("Sr", households=18, down_deg=90, water_kind="stream", field_fall=1260)
    assert k["water_source_position"] == "edge_N" and s.M["meta"]["water_kind"] == "stream"
    assert s.M["houses"] and any(st for st in s.M["streams"])  # a stream source was drawn


def test_roll_village_honors_a_pinned_knob():
    # a pinned knob overrides the roll (US3 determinism surface, exercised through the roll entrypoint)
    s = Settlement(W=2000, H=2600, seed=7)
    s.meta(name="P", scale="hamlet", ftpx=1, toscale=True, households=18, field_footbridges=True)
    s.pin_knob("cluster_shape", "elongated")
    s.pin_knob("lane_skeleton", "spine")
    k = s.roll_village("P", households=18, down_deg=90, water_kind="pond", field_fall=1260)
    assert k["cluster_shape"] == "elongated" and k["lane_skeleton"] == "spine"


def test_pinned_knob_is_byte_identical_across_regens_and_rejects_incompatible_pins():
    # US3 (SC-006): a pinned knob is honored identically every regen; a pin outside the value space or one
    # that violates the geography typing rule is a LOUD error, never silently drawn.
    def build():
        s = Settlement(W=2000, H=2600, seed=11)
        s.meta(name="Pin", scale="village", ftpx=1, toscale=True, households=40, field_footbridges=True)
        s.pin_knob("cluster_shape", "split")  # split needs a village (typing rule) - legal here
        s.pin_knob("lane_skeleton", "cross")
        return s.roll_village("Pin", households=40, down_deg=90, water_kind="pond", field_fall=1400)

    k1 = build()
    k2 = build()
    assert k1 == k2 and k1["cluster_shape"] == "split" and k1["lane_skeleton"] == "cross"  # byte-identical, honored
    # a value outside the knob's space -> loud error
    s = Settlement(W=1800, H=1800, seed=1)
    s.meta(name="X", scale="village")
    s.pin_knob("cluster_shape", "octagon")
    with pytest.raises(ValueError):
        s.resolve("cluster_shape")
    # a value that VIOLATES the geography typing rule (split needs a village/town, not a hamlet) -> loud error
    s2 = Settlement(W=1800, H=1800, seed=1)
    s2.meta(name="Y", scale="hamlet")
    s2.pin_knob("cluster_shape", "split")
    with pytest.raises(ValueError):
        s2.resolve("cluster_shape")


def test_line_seeds_strings_along_the_line_and_records_form():
    import random as _r

    s = Settlement(1400, 1400, seed=1)
    s.meta(name="Ln", scale="village")
    pts = s.line_seeds((400, 400), (400, 1000), 80, 40, _r.Random(3))
    assert len(pts) == 80
    assert s.M["meta"]["settlement_form"] == "linear"  # recorded (a twin-detector axis)
    assert all(abs(p[0] - 400) <= 40 + 1e-9 for p in pts)  # a vertical line: x stays within the band
    assert max(p[1] for p in pts) - min(p[1] for p in pts) > 400  # strung along the length
    # record=False leaves meta untouched
    s2 = Settlement(1000, 1000, seed=1)
    s2.meta(name="L2", scale="village")
    s2.line_seeds((0, 0), (100, 0), 5, 10, _r.Random(1), record=False)
    assert "settlement_form" not in s2.M["meta"]


def test_scatter_seeds_spreads_over_area_and_records_dispersed():
    import random as _r

    s = Settlement(1400, 1400, seed=1)
    s.meta(name="Sc", scale="village")
    pts = s.scatter_seeds(600, 600, 200, 300, 150, _r.Random(5))
    assert len(pts) == 150
    assert s.M["meta"]["settlement_form"] == "dispersed"  # recorded (a twin-detector axis)
    assert all(((p[0] - 600) / 200) ** 2 + ((p[1] - 600) / 300) ** 2 <= 1.0 + 1e-6 for p in pts)  # within the ellipse
    # an even (area-uniform) scatter fills the ellipse, not clumped at the center
    assert sum(1 for p in pts if math.hypot(p[0] - 600, p[1] - 600) > 150) > 30
    # record=False leaves meta untouched
    s2 = Settlement(1000, 1000, seed=1)
    s2.meta(name="S2", scale="village")
    s2.scatter_seeds(500, 500, 100, 100, 5, _r.Random(1), record=False)
    assert "settlement_form" not in s2.M["meta"]


def test_ring_drops_candidates_severed_from_their_field_by_a_road():
    # a road along the fan's south flank: ring candidates ACROSS it can never reach the field
    # (hoshizora's south-of-road farmhouse), so they are dropped rather than seated
    s = _town()
    s.road([(-50, 620), (1050, 620)])
    s.paddy_field((200, 200, 600, 600), "", "f", amp=20)
    s.ring(("poly", s.field_polys[0]), 40, 60, ["plain"])
    s.farmsteads()
    assert s.M["houses"]  # the near side seats normally
    assert all(h["y"] < 620 for h in s.M["houses"])


# ---- feature 118: the composed RollingMixin surface ----------------------------------------------
# The one thing a package split can break SILENTLY. A member dropped by the transformer yields a
# package that imports cleanly, type-checks cleanly under mypy --strict, and draws nothing - it
# surfaces only when whichever generator calls that member happens to run. A member defined TWICE
# yields a working import, a clean typecheck, and one silently dead implementation, because the MRO
# just picks the first base. Contract: specs/118-rolling-package/contracts/mixin-surface.md.

_ROLLING_SURFACE = frozenset(
    {
        # public - called from pool gens, wip/, other engine modules and tests
        "farmsteads",
        "headman",
        "line_seeds",
        "ring",
        "roll_village",
        "scatter_seeds",
        "sun_corridor",
        "waterfront_seeds",
        # private - reached through self., including from OUTSIDE the package
        "_bbox_of",
        "_bundle_common_fits",
        "_bundle_fits",
        "_bundle_geom",
        "_bundle_side_fits",
        "_closest_on_seg",
        "_east_trees",
        "_farmsteads_bundle",
        "_farmsteads_legacy",
        "_field_adjacent",
        "_field_dist",
        "_fits_any_side",
        "_garden_beds",
        "_garden_beds_clear",
        "_garden_shaded",
        "_kura_side",
        "_nearest_field_point",
        "_nearest_placed_point",
        "_perim_bbox",
        "_perim_poly",
        "_place_bundle",
        "_place_bundle_nucleated",
        "_poly_bboxes",
        "_rect_blocked",
        "_rect_corners",
        "_rect_hits",
        "_rect_on_water",
        "_relax_gardens_south",
        "_slide",
        "_slide_nuc",
        "_solve_homestead",
        "_sun_corridor_ok",
        "_water_obstacles",
        "_yard_sun_conflict",
        # class-level DATA, not a callable - a callable-only census would not notice it going
        # missing, which is the extra test feature 112 had to write after the fact
        "_NUC_SIDES",
    }
)


def _own_members(cls: type) -> set[str]:
    """Every non-dunder name this class body defines - data attributes included, not just callables."""
    return {k for k in vars(cls) if not k.startswith("__")}


def _rolling_sub_mixins() -> list[type]:
    from l7r.diagram.settlement.rolling import RollingMixin

    return [c for c in RollingMixin.__mro__ if c is not RollingMixin and c is not object]


def test_no_member_of_the_pre_split_rolling_surface_is_lost():
    # SUPERSET, not equality, deliberately: a later decomposition legitimately adds named private
    # helpers, and equality would turn every such change into a contract edit - training a reader to
    # bump the frozenset without thinking, which is the reflex that lets a real subtraction through.
    # This feature is itself that case: the roll_village stage split adds seven _roll_* members.
    from l7r.diagram.settlement.rolling import RollingMixin

    composed = set().union(*(_own_members(c) for c in RollingMixin.__mro__))
    assert composed >= _ROLLING_SURFACE, f"missing={sorted(_ROLLING_SURFACE - composed)}"


def test_no_rolling_member_is_defined_in_two_sub_mixins():
    # C1 cannot see this: a name defined in two bases still appears in the union, so a duplicate
    # passes C1, passes the import, passes mypy --strict, and runs whichever definition the MRO
    # reaches first - leaving the other as dead code a future reader will edit believing it is live.
    # The transformer refuses such a partition, but the transformer is a one-shot script; this test
    # outlives it and covers the member somebody adds by hand later.
    seen: dict[str, str] = {}
    dupes: list[str] = []
    for cls in _rolling_sub_mixins():
        for name in _own_members(cls):
            if name in seen:
                dupes.append(f"{name} in both {seen[name]} and {cls.__name__}")
            seen[name] = cls.__name__
    assert not dupes, f"defined twice: {sorted(dupes)}"
