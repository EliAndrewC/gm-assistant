#!/usr/bin/env python3
"""Negative-fixture unit tests for the check_village GATE itself.

`test_villages.py` confirms the real pool maps PASS every check (integration). This file
confirms each check actually FIRES on a deliberately-broken synthetic manifest (unit) - so a
refactor that silently neuters a check (e.g. a `bad = []` left always-empty) is caught, which
`test_villages` cannot: every real map would still pass and the suite would stay green while
the check sat dead. Each fixture is a minimal manifest dict (`gate()` fills the rest from
`DEFAULT_MANIFEST`) that should trip ONE named check; we assert the name IS in the failures,
and where a paired 'good' variant exists, that it is NOT - guarding against a check that fires
on everything. Other checks failing on a sparse fixture is fine; we only assert the target.

Add a fixture here whenever you add or tighten a check. The act of writing "here is a map that
SHOULD fail" forces you to enumerate the ways the thing can be wrong - which is how the gap
that motivated this file (a lane "served" by a building fronting the perpendicular street) gets
caught next time.

    python3 -m pytest test_checks.py -q
    python3 test_checks.py
"""
import check_village
import settlement

WALL = [[50, 50], [950, 50], [950, 950], [50, 950]]   # a simple square enclosure


def f(M):
    return set(check_village.gate(M, verbose=False))


def bldg(x, y, kind="merchant", rot=0, w=40, h=28):
    return {"x": x, "y": y, "w": w, "h": h, "rot": rot, "kind": kind}


# ---- streets_have_buildings: the case that motivated this file ----------------------------
# A building beside a north-south lane but FRONTING the east-west cross-street (it is nearer
# the cross) must NOT count as serving the lane - so a lane with only such neighbors reads as
# empty. The old proximity-only check missed this; this fixture pins the fix.
def test_streets_have_buildings_fires_when_building_fronts_the_other_street():
    M = {
        "meta": {"scale": "town", "walled": True}, "wall": WALL,
        "town_streets": [
            {"pts": [[700, 380], [700, 620]], "w": 18},                  # the lane (should read empty)
            {"pts": [[200, 500], [950, 500]], "w": 22, "main": True},    # the cross it actually fronts
        ],
        "buildings": [bldg(760, 500)],   # nearest the cross, not the lane
    }
    assert "streets_have_buildings" in f(M)


def test_streets_have_buildings_passes_when_a_building_fronts_the_street():
    M = {
        "meta": {"scale": "town", "walled": True}, "wall": WALL,
        "town_streets": [{"pts": [[700, 400], [700, 600]], "w": 18, "main": True}],
        "buildings": [bldg(720, 500)],   # nearest THIS street, covers its short length
    }
    assert "streets_have_buildings" not in f(M)


# ---- wall_hugs_the_town: a wall that encloses large empty corner space ---------------------
# Walls are expensive; one should hug the built town. A single building tucked in one corner of
# a big square enclosure leaves three faces running over empty space - that must fire. A town
# whose buildings sit near every face must NOT. (The hill, when present, counts as occupancy -
# a wall may legitimately climb/skirt terrain rather than levelling it.)
def test_wall_hugs_the_town_fires_on_empty_corner_space():
    M = {"meta": {"scale": "town", "walled": True}, "wall": WALL,
         "buildings": [bldg(120, 120)]}   # one building, far from the right/bottom faces
    assert "wall_hugs_the_town" in f(M)


def test_wall_hugs_the_town_passes_when_buildings_line_every_face():
    near = [bldg(x, y) for x in (120, 500, 880) for y in (120, 500, 880)]   # a 3x3 grid hugging all faces
    M = {"meta": {"scale": "town", "walled": True}, "wall": WALL, "buildings": near}
    assert "wall_hugs_the_town" not in f(M)


# ---- a feature-footprint overlap check ----------------------------------------------------
def test_no_structure_on_wall_fires():
    # on the TOP rampart segment - note the wall is an OPEN polyline (the closing edge is not
    # a real wall segment, since a real rampart is an arc anchored to a hill), so the building
    # must sit on one of its drawn segments, not the implicit closure.
    M = {"meta": {"scale": "town", "walled": True}, "wall": WALL,
         "buildings": [bldg(400, 50)]}
    assert "no_structure_on_wall" in f(M)


# ---- channels_flow_downhill: a channel running uphill against the declared slope -----------
def _channel(start, end):
    return {"poly": [start, end], "frm": {"kind": "stream"}, "to": {"kind": "field", "name": "x"}}


def test_channels_flow_downhill_fires_when_channel_runs_uphill():
    # downhill is south (+y); a channel whose field-end is NORTH of its stream-tap runs uphill
    M = {"meta": {"downhill": "south"}, "channels": [_channel([200, 500], [260, 320])]}
    assert "channels_flow_downhill" in f(M)


def test_channels_flow_downhill_passes_when_channel_runs_downhill():
    M = {"meta": {"downhill": "south"}, "channels": [_channel([200, 320], [260, 500])]}
    assert "channels_flow_downhill" not in f(M)


# ---- monastery_torii_scale_with_space + approach_span ------------------------------------
def test_approach_span_terminates_at_each_barrier():
    # March south (0,1) from (500,100) with half-depth 20 (front edge at y132). Each barrier
    # type must stop the march; with none in range it caps near 600. Buildings are not barriers.
    cv = check_village
    base = {"meta": {}}
    street = cv.approach_span(500, 100, 20, 0, 1, {**base, "town_streets": [{"pts": [[0, 300], [1000, 300]], "w": 24}]}, None, 1000, 1000)
    field = cv.approach_span(500, 100, 20, 0, 1, {**base, "flower_fields": [{"outline": [[400, 250], [600, 250], [600, 450], [400, 450]]}]}, None, 1000, 1000)
    walled = cv.approach_span(500, 100, 20, 0, 1, base, [[400, 0], [600, 0], [600, 280], [400, 280]], 1000, 1000)
    edge = cv.approach_span(500, 100, 20, 0, 1, base, None, 1000, 300)
    capped = cv.approach_span(500, 100, 20, 0, 1, base, None, 5000, 5000)
    assert 150 <= street <= 170 and 110 <= field <= 130
    assert 140 <= walled <= 160 and 160 <= edge <= 180 and capped >= 595


def _mon(label, x, y, w=60, h=40):
    return {"kind": "monastery", "label": f"Monastery of {label}", "x": x, "y": y, "w": w, "h": h}


def test_monastery_torii_scale_fires_when_an_avenue_does_not_fit_its_space():
    # Two monasteries, but every torii clusters at A: A's single arch underfills its long clear
    # approach, and B has no arch at all. Both ways of mismatching count-to-space must fire.
    M = {"meta": {"scale": "town", "walled": True, "W": 1000, "H": 1000}, "wall": WALL,
         "religious": [_mon("A", 200, 200), _mon("B", 800, 800)], "torii": [[200, 320]]}
    assert "monastery_torii_scale_with_space" in f(M)


# ---- walled_town_has_gate_market: the extramural guan-xiang -------------------------------
def test_walled_town_has_gate_market_fires_when_no_market_outside():
    # the only business sits INSIDE the wall, so there is no extramural market at the gate
    M = {"meta": {"scale": "town", "walled": True}, "wall": WALL, "gate": [500, 950],
         "buildings": [bldg(500, 500, kind="merchant")]}
    assert "walled_town_has_gate_market" in f(M)


def test_walled_town_gate_market_opt_out_suppresses_the_check():
    # meta(gate_market=False) - a purely military or suppressed gate - skips the requirement
    M = {"meta": {"scale": "town", "walled": True, "gate_market": False}, "wall": WALL,
         "gate": [500, 950], "buildings": [bldg(500, 500, kind="merchant")]}
    assert "walled_town_has_gate_market" not in f(M)


# ---- town_has_granary: the opt-in rice-transit granary (default OFF) -----------------------
def test_town_has_granary_off_by_default():
    # a standard county seat keeps grain in the yamen - no granary declared, no check
    assert "town_has_granary" not in f({"meta": {"scale": "town"}})


def test_town_has_granary_fires_when_declared_but_not_drawn():
    assert "town_has_granary" in f({"meta": {"scale": "town", "granary": True}})


def test_town_has_granary_passes_when_drawn():
    M = {"meta": {"scale": "town", "granary": True},
         "granary": {"x": 500, "y": 500, "n": 3, "stores": [], "label": "granary"}}
    assert "town_has_granary" not in f(M)


# ---- town_has_merchant_storehouses: several attached kura expected -------------------------
def test_town_has_merchant_storehouses_fires_when_too_few():
    assert "town_has_merchant_storehouses" in f({"meta": {"scale": "town"}})   # 0 < 3


def test_town_has_merchant_storehouses_passes_with_several():
    M = {"meta": {"scale": "town"}, "storehouses": [{"x": i, "y": 0} for i in range(4)]}
    assert "town_has_merchant_storehouses" not in f(M)


# ---- town_has_flophouse: cheap market-day lodging (default-on, opt-in to more) --------------
def test_town_has_flophouse_fires_when_absent_by_default():
    assert "town_has_flophouse" in f({"meta": {"scale": "town"}})              # 0 < default 1


def test_town_has_flophouse_requires_more_when_declared():
    M = {"meta": {"scale": "town", "flophouses": 2},
         "flophouses": [{"x": 500, "y": 500, "w": 104, "h": 46, "rot": 0}]}
    assert "town_has_flophouse" in f(M)                                        # 1 < 2


def test_flophouse_on_road_overlaps_like_any_structure():
    # a standalone civic building (flophouse) is now checked for overlaps too: one sitting on
    # the road must trip no_structure_on_road, exactly as a shop would.
    M = {"meta": {"scale": "town"}, "road": [[100, 500], [900, 500]], "road_width": 26,
         "flophouses": [{"x": 500, "y": 500, "w": 104, "h": 46, "rot": 0}]}
    assert "no_structure_on_road" in f(M)                                        # 1 < 2


def test_town_has_flophouse_opt_out_with_zero():
    assert "town_has_flophouse" not in f({"meta": {"scale": "town", "flophouses": 0}})


# ---- town_monasteries_dedicated: wrong patron fortunes for the clan ------------------------
def _monastery(fortune):
    return {"kind": "monastery", "label": f"Monastery of {fortune}", "x": 0, "y": 0, "w": 10, "h": 10}


def test_town_monasteries_dedicated_fires_on_wrong_fortune():
    # Lion's patrons are Bishamon + Daikoku; a Benten monastery is wrong (no override declared)
    M = {"meta": {"scale": "town", "clan": "Lion"},
         "religious": [_monastery("Bishamon"), _monastery("Benten")]}
    assert "town_monasteries_dedicated" in f(M)


def test_town_monasteries_dedicated_passes_with_correct_fortunes():
    M = {"meta": {"scale": "town", "clan": "Lion"},
         "religious": [_monastery("Bishamon"), _monastery("Daikoku")]}
    assert "town_monasteries_dedicated" not in f(M)


# ---- a meta-driven scale rule -------------------------------------------------------------
def test_hamlet_has_no_headman_fires_when_a_hamlet_has_one():
    M = {"meta": {"scale": "hamlet"},
         "houses": [{"x": 100, "y": 100, "w": 108, "h": 68, "kind": "big", "rot": 0, "role": "headman"}]}
    assert "hamlet_has_no_headman" in f(M)


# ---- module-level helper branches (direct calls) ------------------------------------------
def test_helper_edge_branches():
    cv = check_village
    assert cv.sat_overlap([(0, 0), (10, 0), (10, 10), (0, 10)], [(5, 5), (15, 5), (15, 15), (5, 15)])
    assert not cv.sat_overlap([(0, 0), (10, 0), (10, 10), (0, 10)], [(20, 20), (30, 20), (30, 30), (20, 30)])
    assert cv.seg_closest(0, 0, (5, 5), (5, 5)) == (5, 5)               # degenerate (zero-length) segment
    assert cv.unit_dir(None) is None                                   # no slope declared
    assert cv.unit_dir("nonsense") is None                             # unknown cardinal name
    assert cv.unit_dir([3, 4]) == (0.6, 0.8)                           # raw vector, normalized
    assert cv.poly_dist(5, 5, [(0, 0), (10, 0), (10, 10), (0, 10)]) == 0.0   # point inside the polygon


# ---- the on_<feature> overlap helpers: a structure that CONTAINS a feature vertex
# (point_in_poly path) and one the feature CROSSES (segments_cross path) ---------------------
FEAT = [[100, 500], [500, 500], [900, 500]]


def _feature_overlap(meta_extra, key, value, extra=None):
    A = bldg(500, 500, w=200, h=200)   # the feature's (500,500) vertex sits inside A (point_in_poly path)
    B = bldg(300, 500, w=16, h=300)    # the feature crosses B's edge (segments_cross path)
    C = bldg(200, 500, w=40, h=8)      # C's corner sits right on the feature (seg_dist path)
    M = {"meta": {"scale": "town", **meta_extra}, "buildings": [A, B, C], key: value}
    if extra:
        M.update(extra)
    return f(M)


def test_no_structure_on_road_branches():
    assert "no_structure_on_road" in _feature_overlap({}, "road", FEAT, {"road_width": 26})


def test_no_structure_on_stream_branches():
    assert "no_structure_on_stream" in _feature_overlap({}, "streams", [{"poly": FEAT}])


def test_no_structure_on_wall_branches():
    assert "no_structure_on_wall" in _feature_overlap({"walled": True}, "wall", FEAT)


def test_no_structure_on_street_branch():
    assert "no_structure_on_street" in _feature_overlap({"walled": True}, "town_streets", [{"pts": FEAT, "w": 24}])


def test_no_structure_on_channel_branches():
    # an irrigation channel got the same footprint test as streams (a corner clipping it must
    # fire, not just a center on it) - the old houses_off_corridors center-test missed corners.
    ch = {"poly": FEAT, "frm": {"kind": "stream"}, "to": {"kind": "field", "name": "x"}}
    assert "no_structure_on_channel" in _feature_overlap({}, "channels", [ch])


# ---- town street-layout FAIL branches -----------------------------------------------------
def test_businesses_front_streets_fires():
    M = {"meta": {"scale": "town", "walled": True}, "wall": WALL,
         "town_streets": [{"pts": [[120, 120], [120, 400]], "w": 20}],
         "buildings": [bldg(800, 800, kind="shop")]}   # a shop nowhere near the street
    assert "businesses_front_streets" in f(M)


def test_housing_off_main_street_fires():
    M = {"meta": {"scale": "town", "walled": True}, "wall": WALL,
         "town_streets": [{"pts": [[500, 120], [500, 800]], "w": 20, "main": True}],
         "buildings": [bldg(540, 500, kind="laborer", rot=-90)]}   # a dwelling on the MAIN frontage
    assert "housing_off_main_street" in f(M)


def test_roads_drawn_under_overlays_fires():
    M = {"meta": {"scale": "town"}, "road": [[100, 500], [900, 500]], "road_width": 26, "road_z": 1000,
         "labels": [[480, 480, 520, 520, 5],     # a label (z=5) the road (z=1000) is painted OVER
                    [100, 100, 140, 140, 5]]}     # a low-z label the road does NOT touch (the no-hit path)
    assert "roads_drawn_under_overlays" in f(M)


# ---- field/water/channel FAIL branches ----------------------------------------------------
def _field(name, x0, y0, x1, y1):
    return {"name": name, "kind": "paddy", "bbox": [x0, y0, x1, y1],
            "outline": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]}


def test_channel_source_anchored_fires_on_bad_anchor():
    M = {"channels": [{"poly": [[100, 100], [110, 120], [120, 140]],
                       "frm": {"kind": "bogus"}, "to": {"kind": "offmap"}}]}
    assert "channel_source_anchored[0]" in f(M)


def test_streams_avoid_fields_fires():
    M = {"fields": [_field("f", 100, 100, 400, 400)],
         "streams": [{"poly": [[200, 200], [200, 500]]}]}   # first point sits inside the field
    assert "streams_avoid_fields" in f(M)


def test_fields_clear_of_road_fires():
    M = {"fields": [_field("f", 100, 100, 400, 400)], "road": [[50, 250], [500, 250]], "road_width": 26}
    assert "fields_clear_of_road" in f(M)


def test_fields_clear_of_wall_fires():
    M = {"meta": {"scale": "town", "walled": True}, "wall": [[250, 50], [250, 500], [260, 500]],
         "fields": [_field("f", 100, 100, 400, 400)], "gate": [250, 500]}
    assert "fields_clear_of_wall" in f(M)


def test_fields_show_water_source_branches():
    abut = _field("a", 100, 100, 300, 300)             # abuts the stream at x95 -> watered
    ponded = {"name": "p", "kind": "paddy", "bbox": [680, 180, 720, 220],
              "outline": [[680, 180], [720, 180], [720, 220], [680, 220]]}   # over the pond -> watered
    dry = _field("d", 100, 600, 300, 800)              # no channel/stream/pond -> dry, fires
    M = {"fields": [abut, ponded, dry], "streams": [{"poly": [[95, 90], [95, 310]]}], "pond": [700, 200, 80, 60]}
    assert "fields_show_water_source" in f(M)


def test_edge_features_run_off_map_fires_each_direction():
    M = {"meta": {"W": 1000, "H": 1000}, "pastures": [
        [[960, 400], [990, 400], [990, 460], [960, 460]],   # right edge, stops short
        [[10, 400], [40, 400], [40, 460], [10, 460]],       # left
        [[400, 960], [460, 960], [460, 990], [400, 990]],   # bottom
        [[400, 10], [460, 10], [460, 40], [400, 40]]]}      # top
    assert "edge_features_run_off_map" in f(M)


def test_house_count_in_range_target_houses_fires():
    houses = [{"x": i * 30, "y": 100, "w": 44, "h": 29, "kind": "plain", "rot": 0} for i in range(10)]
    M = {"meta": {"scale": "village", "target_houses": 60}, "houses": houses}   # 10 vs ~60
    assert "house_count_in_range" in f(M)


# ---- water-width ladder: ditch < creek < moat, with honest gaps ---------------------------
# Real wet-rice water systems are a tiered hierarchy (~2-4x per tier); the rendered map log-
# compresses that but must keep the ordering. A ditch is the thinnest line; a creek clearly
# beats it; the city moat dwarfs it and out-widths every natural stream (a feeder may equal it).
_CHAN = [[100, 100], [110, 120], [120, 140]]
_STRM = [[400, 100], [400, 300]]


def test_irrigation_channels_hairline_fires_on_a_fat_ditch():
    M = {"channels": [{"poly": _CHAN, "frm": {"kind": "offmap"}, "to": {"kind": "field", "name": "f"}, "w": 4.2}]}
    assert "irrigation_channels_hairline" in f(M)   # the OLD 4.2 px stout ditch must now trip


def test_irrigation_channels_hairline_passes_at_the_floor():
    M = {"channels": [{"poly": _CHAN, "frm": {"kind": "offmap"}, "to": {"kind": "field", "name": "f"}, "w": 2.5}]}
    assert "irrigation_channels_hairline" not in f(M)


def test_watercourses_wider_than_ditches_fires_when_a_creek_reads_like_a_ditch():
    M = {"channels": [{"poly": _CHAN, "frm": {"kind": "offmap"}, "to": {"kind": "field", "name": "f"}, "w": 2.5}],
         "streams": [{"poly": _STRM, "frm": None, "to": None, "w": 5}]}   # 5 < 2.5x2.5 -> too close to the ditch
    assert "watercourses_wider_than_ditches" in f(M)


def test_watercourses_wider_than_ditches_passes_for_a_proper_creek():
    M = {"channels": [{"poly": _CHAN, "frm": {"kind": "offmap"}, "to": {"kind": "field", "name": "f"}, "w": 2.5}],
         "streams": [{"poly": _STRM, "frm": None, "to": None, "w": 9}]}   # 9 >= 6.25
    assert "watercourses_wider_than_ditches" not in f(M)


def test_moat_is_heaviest_watercourse_fires_when_a_stream_out_widths_it():
    M = {"streams": [{"poly": _STRM, "frm": None, "to": None, "w": 30}], "moat_width": 26}   # stream > moat
    assert "moat_is_heaviest_watercourse" in f(M)


def test_moat_is_heaviest_watercourse_passes_when_a_feeder_equals_it():
    M = {"streams": [{"poly": _STRM, "frm": None, "to": None, "w": 26}], "moat_width": 26}   # equal is allowed
    assert "moat_is_heaviest_watercourse" not in f(M)


def test_moat_dwarfs_ditches_fires_on_a_skimpy_moat():
    M = {"channels": [{"poly": _CHAN, "frm": {"kind": "offmap"}, "to": {"kind": "field", "name": "f"}, "w": 2.5}],
         "moat_width": 8}   # 8 < 4x2.5
    assert "moat_dwarfs_ditches" in f(M)


def test_moat_dwarfs_ditches_passes_for_a_real_city_moat():
    M = {"channels": [{"poly": _CHAN, "frm": {"kind": "offmap"}, "to": {"kind": "field", "name": "f"}, "w": 2.5}],
         "moat_width": 26}   # 26 >= 10
    assert "moat_dwarfs_ditches" not in f(M)


# ---- dooryard kitchen garden: every farmstead has a saien on a sunny side -------------------
# Each fixture trips ONE garden check: the work yard was universal and so was the kitchen garden,
# so the gate enforces a garden per farmhouse, smaller than the house, on a sunny (not north) side,
# on dry ground, abutting only its own house.
def _farmhouse(x, y):
    return {"x": x, "y": y, "w": 44, "h": 29, "kind": "plain", "rot": 0}


def test_gardens_present_fires_when_a_farmhouse_has_none():
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(500, 500)], "gardens": []}
    assert "gardens_present" in f(M)


def test_gardens_on_sunny_side_fires_on_a_north_garden():
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(500, 500)],
         "gardens": [{"x": 520, "y": 455, "w": 24, "h": 16, "rot": 0, "of": [500, 500]}]}   # y=455 is north of 500
    assert "gardens_on_sunny_side" in f(M)


def test_gardens_smaller_than_farmhouse_fires_on_an_oversize_garden():
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(500, 500)],
         "gardens": [{"x": 545, "y": 500, "w": 60, "h": 40, "rot": 0, "of": [500, 500]}]}   # bigger than the house
    assert "gardens_smaller_than_farmhouse" in f(M)


def test_gardens_clear_of_paddies_fires_on_a_garden_in_a_field():
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(500, 500)],
         "fields": [_field("p", 480, 480, 600, 600)],
         "gardens": [{"x": 530, "y": 530, "w": 24, "h": 16, "rot": 0, "of": [500, 500]}]}   # sits inside the paddy
    assert "gardens_clear_of_paddies" in f(M)


def test_gardens_clear_of_structures_fires_when_a_garden_covers_another_building():
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(500, 500)],
         "buildings": [bldg(545, 500, "shop")],
         "gardens": [{"x": 545, "y": 500, "w": 24, "h": 16, "rot": 0, "of": [500, 500]}]}   # on the shop, not its own house
    assert "gardens_clear_of_structures" in f(M)


def test_gardens_clear_of_sheds_fires_when_a_garden_covers_the_west_side_shed():
    # a plain farmhouse with shed=True carries a storehouse on its WEST side (centre ~ x-0.64w); a garden
    # placed there overlaps it. The shed is derived from the house record, not a separate struct.
    M = {"meta": {"scale": "village"},
         "houses": [{"x": 500, "y": 500, "w": 44, "h": 29, "kind": "plain", "rot": 0, "shed": True}],
         "gardens": [{"x": 472, "y": 500, "w": 24, "h": 16, "rot": 0, "of": [500, 500]}]}   # on the west-side shed
    assert "gardens_clear_of_sheds" in f(M)


# ---- provincial-city checks (scale="city"); tango.gen.py is the passing integration ---------
WALLSQ = [[200, 200], [800, 200], [800, 800], [200, 800]]   # a closed city ring


def test_city_required_structures_all_fire_on_an_empty_city():
    fails = f({"meta": {"scale": "city"}})
    for name in ("city_has_governor_mansion", "city_has_six_ministries", "city_has_ministry_of_rites",
                 "city_has_samurai_neighborhood", "city_has_merchant_district",
                 "city_has_laborer_neighborhoods", "city_has_outside_farmland"):
        assert name in fails


def test_city_ministry_of_rites_fires_when_six_but_none_are_rites():
    mins = [{"x": i * 30, "y": 50, "w": 80, "h": 50, "name": f"Ministry {i}"} for i in range(6)]
    assert "city_has_ministry_of_rites" in f({"meta": {"scale": "city"}, "ministries": mins})


def _city_with_samurai(label_box):
    sam = [bldg(400, 400, kind="samurai"), bldg(440, 400, kind="samurai"), bldg(420, 440, kind="samurai")]
    return {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
            "gates": [[500, 200], [500, 800]], "buildings": sam, "labels": [label_box]}


def test_city_labels_placed_with_subject_fires_when_label_is_across_the_wall():
    # the samurai cluster is INSIDE the wall but its label floats OUTSIDE (over the moat) - misleading
    M = _city_with_samurai([850, 492, 950, 508, 0, "samurai neighborhood"])   # center (900,500), outside WALLSQ
    assert "city_labels_placed_with_subject" in f(M)


def test_city_labels_placed_with_subject_fires_when_label_far_from_cluster():
    # label inside the wall but nowhere near its samurai houses (they are at ~(420,420), label at (730,720))
    M = _city_with_samurai([680, 712, 780, 728, 0, "samurai neighborhood"])
    assert "city_labels_placed_with_subject" in f(M)


def test_city_labels_placed_with_subject_fires_when_label_over_a_field():
    # burakumin houses sit just south, but the label floats over a paddy to their north
    field = {"name": "f", "kind": "paddy", "bbox": [360, 360, 520, 520],
             "outline": [[360, 360], [520, 360], [520, 520], [360, 520]]}
    bur = [bldg(420, 540, kind="burakumin"), bldg(460, 540, kind="burakumin"), bldg(440, 500, kind="burakumin")]
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]], "buildings": bur, "fields": [field],
         "labels": [[390, 442, 490, 458, 0, "burakumin neighborhood"]]}   # center (440,450), inside field f
    assert "city_labels_placed_with_subject" in f(M)


def test_city_labels_placed_with_subject_skips_labels_with_no_known_subject():
    # a zone-suffix label whose subject we can't identify ("potters district" - no such building kind)
    # cannot be verified, so it is skipped rather than flagged
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]], "labels": [[850, 492, 950, 508, 0, "potters district"]]}
    assert "city_labels_placed_with_subject" not in f(M)


def test_city_labels_placed_with_subject_passes_when_among_the_cluster():
    # label inside the wall AND among its samurai houses (center ~(420,410)) - the correct placement
    M = _city_with_samurai([370, 402, 470, 418, 0, "samurai neighborhood"])
    assert "city_labels_placed_with_subject" not in f(M)


def test_city_samurai_housing_sufficient_fires_when_too_few():
    # a 3,000-pop city is ~300 samurai (~60 households); ~10 token houses is far too few - it must
    # depict the bulk of the samurai cohort, not a handful (this was Tango's 22).
    sam = [bldg(300 + i * 12, 300, kind="samurai") for i in range(10)]
    M = {"meta": {"scale": "city", "walled": True, "population": 3000, "W": 1000, "H": 1000},
         "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "buildings": sam}
    assert "city_samurai_housing_sufficient" in f(M)


def test_city_lanes_layered_by_width_fires_when_narrow_over_wide():
    # the wide Imperial road (26) is drawn EARLY (low z) and a narrow street (18) that crosses it is
    # drawn later (high z): the narrow lane paints over the wider road - the wider must be on top.
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
         "wall": WALLSQ, "gates": [[500, 200], [500, 800]],
         "road": [[500, 150], [500, 850]], "road_width": 26, "road_z": 5,
         "town_streets": [{"pts": [[300, 500], [700, 500]], "w": 18, "z": 50}]}   # crosses the road at (500,500)
    assert "city_lanes_layered_by_width" in f(M)


def test_city_flophouse_in_humble_quarter_fires_next_to_merchants():
    # an in-wall flophouse cheek-by-jowl with a merchant house - a doss-house does not belong in the
    # nicer quarter
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]], "flophouses": [{"x": 500, "y": 500, "w": 92, "h": 42, "rot": 0}],
         "buildings": [bldg(560, 500, kind="merchant")]}   # merchant 60px away
    assert "city_flophouse_in_humble_quarter" in f(M)


def test_city_flophouse_in_humble_quarter_fires_next_to_burakumin():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]], "flophouses": [{"x": 500, "y": 500, "w": 92, "h": 42, "rot": 0}],
         "buildings": [bldg(580, 500, kind="burakumin")]}   # burakumin 80px away (in/beside the quarter)
    assert "city_flophouse_in_humble_quarter" in f(M)


def test_city_flophouse_in_humble_quarter_passes_when_humble_and_clear():
    # in-wall flophouse with only laborers nearby - the humble sector, correctly placed
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]], "flophouses": [{"x": 500, "y": 500, "w": 92, "h": 42, "rot": 0}],
         "buildings": [bldg(560, 500, kind="laborer"), bldg(540, 560, kind="laborer")]}
    assert "city_flophouse_in_humble_quarter" not in f(M)


def _merchant_city(buildings, estates=None):
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]], "buildings": buildings}
    if estates is not None:
        M["merchant_estates"] = estates
    return M


def test_city_merchant_housing_varied_fires_when_uniform():
    # a merchant quarter of nothing but small uniform houses - no large houses, no walled estates
    M = _merchant_city([bldg(300 + i * 30, 300, kind="merchant_house") for i in range(10)])
    assert "city_merchant_housing_varied" in f(M)


def test_city_merchant_housing_varied_passes_with_a_mix():
    blds = [bldg(300 + i * 30, 300, kind="merchant_large") for i in range(4)] + \
           [bldg(300 + i * 30, 400, kind="merchant_house") for i in range(6)]
    M = _merchant_city(blds, estates=[{"x": 500, "y": 600, "w": 78, "h": 58}])
    assert "city_merchant_housing_varied" not in f(M)


def _samurai_varied_city(buildings, manors=None):
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]], "buildings": buildings}
    if manors is not None:
        M["manors"] = manors
    return M


def test_city_samurai_housing_varied_fires_when_uniform():
    # a samurai quarter of nothing but small uniform houses - no large senior houses to vary it
    M = _samurai_varied_city([bldg(300 + i * 30, 300, kind="samurai") for i in range(10)])
    assert "city_samurai_housing_varied" in f(M)


def test_city_samurai_housing_varied_fires_when_estate_inside_the_wall():
    # a proper small/large mix, but a samurai walled ESTATE sits INSIDE the city wall - those belong
    # outside the rampart (only the governor's mansion is walled within)
    blds = [bldg(300 + i * 30, 300, kind="samurai_large") for i in range(4)] + \
           [bldg(300 + i * 30, 400, kind="samurai") for i in range(8)]
    M = _samurai_varied_city(blds, manors=[{"x": 500, "y": 500, "w": 80, "h": 60}])   # inside WALLSQ
    assert "city_samurai_housing_varied" in f(M)


def test_city_samurai_housing_varied_passes_with_a_mix_and_estates_outside():
    blds = [bldg(300 + i * 30, 300, kind="samurai_large") for i in range(4)] + \
           [bldg(300 + i * 30, 400, kind="samurai") for i in range(8)]
    M = _samurai_varied_city(blds, manors=[{"x": 900, "y": 500, "w": 80, "h": 60}])   # outside WALLSQ
    assert "city_samurai_housing_varied" not in f(M)


def _agri_city(houses, agri=True):
    # a city with an in-wall AGRICULTURAL field (the unusual jokamachi that farms inside the walls)
    field = {"name": "nw1", "kind": "paddy", "bbox": [350, 350, 550, 550],
             "outline": [[350, 350], [550, 350], [550, 550], [350, 550]]}   # ~800px perimeter, all in-wall
    hs = [{"kind": "plain", "rot": 0, "w": 18, "h": 12, **h} for h in houses]
    return {"meta": {"scale": "city", "walled": True, "agricultural_district": agri, "W": 1000, "H": 1000},
            "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "fields": [field], "houses": hs}


def test_city_interior_fields_farmhouse_density_fires_when_under_farmed():
    # a real in-wall field with a single token farmhouse beside it - far below village density
    M = _agri_city([{"x": 360, "y": 320, "w": 18, "h": 12, "rot": 0}])
    assert "city_interior_fields_farmhouse_density" in f(M)


def test_city_interior_fields_farmhouse_density_passes_when_densely_ringed():
    # a dense ring wrapping the WHOLE perimeter (top, bottom, both sides) - a worked in-wall field
    houses = [{"x": x, "y": 330} for x in range(360, 545, 30)] + [{"x": x, "y": 570} for x in range(360, 545, 30)] \
        + [{"y": y, "x": 330} for y in range(380, 525, 30)] + [{"y": y, "x": 570} for y in range(380, 525, 30)]
    M = _agri_city(houses)
    assert "city_interior_fields_farmhouse_density" not in f(M)


def test_city_interior_fields_farmhouse_density_skipped_without_agricultural_district():
    # an ordinary city (no in-wall farming declared) is not held to the rule even if a field strays inside
    M = _agri_city([], agri=False)
    assert "city_interior_fields_farmhouse_density" not in f(M)


def test_city_interior_fields_farmhouse_density_skips_a_tiny_field_sliver():
    # an in-wall field too small to merit its own farmhouse ring (edge < 120px) is skipped, not flagged
    tiny = {"name": "tiny", "kind": "paddy", "bbox": [480, 480, 505, 505],
            "outline": [[480, 480], [505, 480], [505, 505], [480, 505]]}   # ~100px perimeter
    M = {"meta": {"scale": "city", "walled": True, "agricultural_district": True, "W": 1000, "H": 1000},
         "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "fields": [tiny], "houses": []}
    assert "city_interior_fields_farmhouse_density" not in f(M)


def _road_city(buildings, road=True):
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]], "buildings": buildings}
    if road:
        M["road"] = [[500, -40], [500, 500], [500, 1040]]   # runs off both edges, through the walls
    return M


def test_city_imperial_road_has_commerce_fires_when_road_frontage_is_bare():
    # the Imperial road runs through, but only housing lines it - no shops on the prime road frontage
    M = _road_city([bldg(300, 400, kind="laborer")])
    assert "city_imperial_road_has_commerce" in f(M)


def test_city_imperial_road_has_commerce_passes_when_road_is_lined():
    shops = [bldg(540, y, kind="shop") for y in range(300, 760, 70)]   # a commercial ribbon along the road
    M = _road_city(shops)
    assert "city_imperial_road_has_commerce" not in f(M)


def test_city_imperial_road_has_commerce_skipped_without_a_road():
    # a city with no Imperial road has no road-ribbon rule (its commerce stays in the market district)
    M = _road_city([bldg(540, y, kind="shop") for y in range(300, 760, 70)], road=False)
    assert "city_imperial_road_has_commerce" not in f(M)


def _unwalled_road_city(buildings):
    # an UNWALLED city: no wall, so the road's through-extent is the urban footprint (the building bbox)
    spread = [bldg(300 + i * 60, 250, kind="laborer") for i in range(8)] \
        + [bldg(300 + i * 60, 750, kind="laborer") for i in range(8)]   # housing spanning the road on both sides
    return {"meta": {"scale": "city", "W": 1000, "H": 1000}, "gates": [],
            "road": [[500, -40], [500, 500], [500, 1040]], "buildings": spread + buildings}


def test_city_imperial_road_has_commerce_generic_for_an_unwalled_city_fires_when_bare():
    # the rule applies to ANY city with an Imperial road, walled or not - here an unwalled one runs bare
    assert "city_imperial_road_has_commerce" in f(_unwalled_road_city([]))


def test_city_imperial_road_has_commerce_generic_for_an_unwalled_city_passes_when_lined():
    shops = [bldg(540, y, kind="shop") for y in range(260, 760, 60)]   # a commercial ribbon along the road
    assert "city_imperial_road_has_commerce" not in f(_unwalled_road_city(shops))


# --- city_lanes_meet_when_aligned (two lanes heading at each other should connect) ---
def _lanes(streets=None, alleys=None, **extra):
    M = {}
    if streets is not None:
        M["town_streets"] = [{"pts": p, "w": 18} for p in streets]
    if alleys is not None:
        M["alleys"] = [{"pts": p} for p in alleys]
    M.update(extra)
    return M


def test_lane_near_misses_flags_a_collinear_clear_gap():
    # a street and an alley on the same line, heading at each other, a clear 30px gap - should connect
    M = _lanes(streets=[[[500, 300], [500, 480]]], alleys=[[[500, 510], [500, 700]]])
    assert check_village.lane_near_misses(M)


def test_lane_near_misses_clear_when_lanes_actually_touch():
    M = _lanes(streets=[[[500, 300], [500, 500]]], alleys=[[[500, 500], [500, 700]]])   # meet at (500,500)
    assert not check_village.lane_near_misses(M)


def test_lane_near_misses_ignores_parallel_ends_not_heading_at_each_other():
    # two parallel lanes whose ends sit side by side - neither points AT the other, so not a near-miss
    M = _lanes(streets=[[[300, 400], [500, 400]], [[300, 440], [500, 440]]])
    assert not check_village.lane_near_misses(M)


def test_lane_near_misses_respects_a_building_blocking_the_gap():
    M = _lanes(streets=[[[500, 300], [500, 480]]], alleys=[[[500, 510], [500, 700]]],
               buildings=[bldg(500, 495, kind="laborer")])
    assert not check_village.lane_near_misses(M)


def test_lane_near_misses_respects_a_ward_fence_blocking_the_gap():
    M = _lanes(streets=[[[500, 300], [500, 480]]], alleys=[[[500, 510], [500, 700]]],
               wards=[{"boundary": [[400, 495], [600, 495]]}])
    assert not check_village.lane_near_misses(M)


def test_lane_near_misses_respects_the_wall_blocking_the_gap():
    M = _lanes(streets=[[[500, 300], [500, 480]]], alleys=[[[500, 510], [500, 700]]],
               wall=[[400, 495], [600, 495], [600, 800], [400, 800]])   # top edge crosses the gap
    assert not check_village.lane_near_misses(M)


def test_lane_near_misses_skips_an_endpoint_meeting_the_wide_road():
    # a street ending against the Imperial road is CONNECTED (the road's job, not a near-miss)
    M = _lanes(streets=[[[300, 500], [485, 500]]], alleys=[[[600, 500], [800, 500]]],
               road=[[500, -40], [500, 1040]])
    assert not check_village.lane_near_misses(M)


def test_city_lanes_meet_when_aligned_fires_through_the_gate():
    M = _lanes(streets=[[[500, 300], [500, 480]]], alleys=[[[500, 510], [500, 700]]], meta={"scale": "city"})
    assert "city_lanes_meet_when_aligned" in f(M)


# --- city_lanes_reach_ward_gates (lanes at a neighborhood wall extend to it and end at a gate) ---
def _ward_lane(alleys=None, streets=None, fence=None, gov=(500, 640), **extra):
    M = {"wards": [{"boundary": fence or [[300, 500], [700, 500]]}]}   # a horizontal ward fence at y500
    if gov:
        M["governor_mansion"] = {"x": gov[0], "y": gov[1]}             # interior anchor, SOUTH of the fence
    if alleys is not None:
        M["alleys"] = [{"pts": p} for p in alleys]
    if streets is not None:
        M["town_streets"] = [{"pts": p, "w": 18} for p in streets]
    M.update(extra)
    return M


def test_lane_ward_shortfalls_flags_a_lane_stopping_short():
    M = _ward_lane(alleys=[[[500, 300], [500, 460]]])   # heads down at the fence, stops 40px short, no gate
    assert check_village.lane_ward_shortfalls(M)


def test_lane_ward_shortfalls_clear_when_lane_reaches_a_gate():
    M = _ward_lane(alleys=[[[500, 300], [500, 500]]], kido=[{"x": 500, "y": 500}])
    assert not check_village.lane_ward_shortfalls(M)


def test_lane_ward_shortfalls_flags_a_lane_meeting_the_fence_without_a_gate():
    M = _ward_lane(alleys=[[[500, 300], [500, 500]]])   # reaches the fence but no kido there
    assert check_village.lane_ward_shortfalls(M)


def test_lane_ward_shortfalls_respects_a_building_blocking_the_approach():
    M = _ward_lane(alleys=[[[500, 300], [500, 460]]], buildings=[bldg(500, 480, kind="laborer")])
    assert not check_village.lane_ward_shortfalls(M)


def test_lane_ward_shortfalls_respects_the_main_wall_between_lane_and_fence():
    M = _ward_lane(alleys=[[[500, 300], [500, 460]]], wall=[[300, 480], [700, 480], [700, 800], [300, 800]])
    assert not check_village.lane_ward_shortfalls(M)


def test_lane_ward_shortfalls_ignores_an_interior_ward_lane():
    M = _ward_lane(alleys=[[[500, 700], [500, 540]]])   # endpoint (500,540) is SOUTH of the fence - inside the ward
    assert not check_village.lane_ward_shortfalls(M)


def test_lane_ward_shortfalls_ignores_a_lane_running_parallel_to_the_fence():
    M = _ward_lane(alleys=[[[300, 460], [600, 460]]])   # parallel, above the fence - not heading at it
    assert not check_village.lane_ward_shortfalls(M)


def test_lane_ward_shortfalls_uses_fence_centroid_when_no_governor_mansion():
    # with no yamen to anchor the interior, the fence's own centroid stands in (an L-fence, centroid inside)
    M = _ward_lane(alleys=[[[500, 300], [500, 460]]], fence=[[300, 500], [700, 500], [700, 700]], gov=None)
    assert check_village.lane_ward_shortfalls(M)


def test_city_lanes_reach_ward_gates_fires_through_the_gate():
    M = _ward_lane(alleys=[[[500, 300], [500, 460]]], meta={"scale": "city"})
    assert "city_lanes_reach_ward_gates" in f(M)


# --- city_lane_under_wall / city_lanes_under_ward_fences (lanes render UNDER walls) ---
def _walled(streets=None, alleys=None, **extra):
    M = {"meta": {"scale": "city"}, "wall": [[200, 200], [800, 200], [800, 800], [200, 800]],
         "wall_z": 10, "gates": [[500, 200]]}
    if streets is not None:
        M["town_streets"] = streets
    if alleys is not None:
        M["alleys"] = alleys
    M.update(extra)
    return M


def test_city_lane_under_wall_fires_when_a_street_touches_the_wall():
    # a street whose end reaches the wall (z above the rampart's) renders OVER it - away from any gate
    M = _walled(streets=[{"pts": [[300, 300], [300, 205]], "w": 18, "z": 100}])
    assert "city_lane_under_wall" in f(M)


def test_city_lane_under_wall_fires_when_a_street_crosses_the_wall():
    M = _walled(streets=[{"pts": [[300, 150], [300, 300]], "w": 18, "z": 100}])   # crosses the top edge off-gate
    assert "city_lane_under_wall" in f(M)


def test_city_lane_under_wall_passes_at_a_gate_opening():
    # a road through the gate crosses the wall ring there, but the gate is a genuine opening - exempt
    M = _walled(streets=[{"pts": [[500, 400], [500, 150]], "w": 18, "z": 100}])   # crosses at the gate (500,200)
    assert "city_lane_under_wall" not in f(M)


def test_city_lane_under_wall_passes_when_lane_already_under():
    M = _walled(streets=[{"pts": [[300, 300], [300, 205]], "w": 18, "z": 5}])     # z below wall_z (10)
    assert "city_lane_under_wall" not in f(M)


def test_city_lane_under_wall_handles_an_open_town_wall():
    # a town wall is an open arc (not a closed ring); a street touching it off-gate still fires
    M = {"meta": {"scale": "town"}, "wall": [[200, 500], [500, 200], [800, 500]], "wall_z": 10,
         "gate": [500, 200], "town_streets": [{"pts": [[300, 600], [352, 352]], "w": 18, "z": 100}]}
    assert "city_lane_under_wall" in f(M)


def test_city_lanes_under_ward_fences_fires_when_a_lane_renders_over_a_fence():
    M = {"meta": {"scale": "city"}, "wards": [{"name": "samurai", "boundary": [[300, 500], [700, 500]], "z": 10}],
         "alleys": [{"pts": [[400, 300], [400, 505]], "w": 10, "z": 100}]}
    assert "city_lanes_under_ward_fences" in f(M)


def test_city_lanes_under_ward_fences_passes_when_crossing_at_a_kido():
    M = {"meta": {"scale": "city"}, "wards": [{"name": "samurai", "boundary": [[300, 500], [700, 500]], "z": 10}],
         "kido": [{"x": 400, "y": 500}], "alleys": [{"pts": [[400, 300], [400, 505]], "w": 10, "z": 100}]}
    assert "city_lanes_under_ward_fences" not in f(M)


# --- labels_render_on_top (label text is never covered) ---
def test_labels_render_on_top_fires_when_a_kido_covers_a_label():
    M = {"labels": [[100, 100, 300, 120, 5, "Ministry of Retainers"]],
         "kido": [{"x": 200, "y": 110, "z": 1000, "bbox": [150, 90, 250, 130]}]}
    assert "labels_render_on_top" in f(M)


def test_labels_render_on_top_fires_when_a_gate_structure_covers_a_label():
    M = {"labels": [[150, 100, 250, 120, 5, "gate label"]],
         "gate_structs": [{"x": 200, "y": 110, "w": 100, "h": 40, "z": 1000}]}
    assert "labels_render_on_top" in f(M)


def test_labels_render_on_top_fires_when_a_torii_covers_a_label():
    M = {"labels": [[185, 95, 215, 120, 5, "shrine"]], "torii": [[200, 110, 1000]]}
    assert "labels_render_on_top" in f(M)


def test_labels_render_on_top_passes_when_the_label_is_above():
    # same overlap, but the label's draw-z is higher than the structure's - it renders on top, readable
    M = {"labels": [[100, 100, 300, 120, 9999, "Ministry of Retainers"]],
         "kido": [{"x": 200, "y": 110, "z": 1000, "bbox": [150, 90, 250, 130]}]}
    assert "labels_render_on_top" not in f(M)


def test_labels_render_on_top_handles_a_textless_label():
    M = {"labels": [[150, 100, 250, 120, 5]],   # a field label recorded without text
         "kido": [{"x": 200, "y": 110, "z": 1000, "bbox": [150, 90, 250, 130]}]}
    assert "labels_render_on_top" in f(M)


# --- labels_within_image (a label must not run off the edge of the rendered frame) ---
def test_labels_within_image_fires_when_a_label_runs_off_the_edge():
    # the default canvas is 1820x1180; this label pokes past the right edge
    M = {"meta": {}, "labels": [[1750, 500, 1900, 512, 1, "off the right edge"]]}
    assert "labels_within_image" in f(M)


def test_labels_within_image_passes_when_inside():
    M = {"meta": {}, "labels": [[100, 100, 300, 112, 1, "comfortably inside"]]}
    assert "labels_within_image" not in f(M)


# --- no_label_overlaps (two body labels must not overlap) ---
def test_no_label_overlaps_fires_when_glyphs_cross():
    # two same-line labels whose boxes cross by >2px (x) and >4px (y) - the glyphs touch (the real
    # Hoshizora "cremation ground" / "Monastery of Bishamon" collision: 3px x, 10px y)
    M = {"meta": {}, "labels": [[40, 740, 143, 752, 1, "cremation ground"],
                                [140, 736, 290, 750, 2, "Monastery of Bishamon"]]}
    assert "no_label_overlaps" in f(M)


def test_no_label_overlaps_passes_when_stacked_boxes_only_kiss():
    # two STACKED labels whose boxes merely kiss vertically (2.2px, the descender allowance) but are
    # cleanly separated lines (the real Tango "Mausoleum" / "Ministry of Works") - must NOT flag
    M = {"meta": {}, "labels": [[2216, 1580, 2276, 1593, 1, "Mausoleum"],
                                [2168, 1591, 2252, 1600, 2, "Ministry of Works"]]}
    assert "no_label_overlaps" not in f(M)


def test_no_label_overlaps_passes_when_clear():
    M = {"meta": {}, "labels": [[40, 740, 130, 752, 1, "a"], [200, 740, 300, 752, 2, "b"]]}
    assert "no_label_overlaps" not in f(M)


def test_labels_within_image_uses_the_cropped_view():
    # with a crop set, the frame is the viewBox - a label inside the full canvas but WEST of the crop
    # (a city map crops tight to the walls) is clipped and fires
    M = {"meta": {"view": [658, 448, 1884, 1764]}, "labels": [[300, 690, 500, 702, 1, "west of the crop"]]}
    assert "labels_within_image" in f(M)


# --- city_caste_counts_in_band (the caste MIX, not just the total, matches budgets.md) ---
def _caste_city(**counts):
    blds = []
    for kind, n in counts.items():
        blds += [bldg(300 + i * 10, 300 + (i % 5) * 10, kind=kind) for i in range(n)]
    return {"meta": {"scale": "city", "population": 300}, "buildings": blds}   # ~60 households


def test_city_caste_counts_in_band_fires_when_a_caste_is_off():
    # ~50 laborers is far over the ~24 target for a 60-household city (and the other castes are absent)
    assert "city_caste_counts_in_band" in f(_caste_city(laborer=50))


def test_city_caste_counts_in_band_passes_with_a_balanced_mix():
    # ~40% laborer / 20% servant / 25% merchant / 10% samurai / 5% burakumin of ~60 households
    M = _caste_city(laborer=24, servant=12, merchant_house=15, samurai=6, burakumin=3)
    assert "city_caste_counts_in_band" not in f(M)


def test_city_laborer_housing_varied_fires_when_uniform():
    # every laborer identical - no wealthy 'master' tier (0 large homes)
    assert "city_laborer_housing_varied" in f(_caste_city(laborer=30))


def test_city_laborer_housing_varied_passes_with_a_minority_of_large():
    # ~12.5% of the laborers are larger 'master/rich' homes, the rest standard (budgets.md)
    assert "city_laborer_housing_varied" not in f(_caste_city(laborer=28, laborer_large=4))


def test_city_laborer_housing_varied_fires_when_too_many_large():
    # half the laborers large - not "a clear minority"
    assert "city_laborer_housing_varied" in f(_caste_city(laborer=15, laborer_large=15))


# --- wall guard towers, ring road, streets reaching the ring road (fortification) ---
def _fort_city(**extra):
    M = {"meta": {"scale": "city", "walled": True}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]]}
    M.update(extra)
    return M


def test_city_wall_towers_spaced_fires_with_only_gate_towers():
    M = _fort_city(wall_towers=[{"x": 500, "y": 200}, {"x": 500, "y": 800}])   # only the 2 gate towers
    assert "city_wall_towers_spaced" in f(M)


def test_city_wall_towers_spaced_passes_when_ringed():
    import math
    towers = [{"x": 500 + 300 * math.cos(i * math.pi / 5), "y": 500 + 300 * math.sin(i * math.pi / 5)} for i in range(10)]
    assert "city_wall_towers_spaced" not in f(_fort_city(wall_towers=towers))


_DIAMOND = [[500, 200], [800, 500], [500, 800], [200, 500]]   # a wall whose edges run at 45 deg


def test_city_wall_towers_aligned_fires_when_axis_aligned_on_a_slanted_wall():
    M = _fort_city(wall=_DIAMOND, wall_towers=[{"x": 650, "y": 350, "rot": 0}, {"x": 350, "y": 650, "rot": 0}])
    assert "city_wall_towers_aligned" in f(M)


def test_city_wall_towers_aligned_passes_when_square_to_the_wall():
    # both towers sit on a 45 deg wall edge and are rotated 45 deg to match it
    M = _fort_city(wall=_DIAMOND, wall_towers=[{"x": 650, "y": 350, "rot": 45}, {"x": 350, "y": 650, "rot": 45}])
    assert "city_wall_towers_aligned" not in f(M)


def _gate_furn(rot, wall=None, gates=None):
    return _fort_city(wall=wall or WALLSQ, gates=gates or [[500, 200], [500, 800]],
                      gate_structs=[{"x": 420, "y": 256, "w": 66, "h": 44, "rot": rot, "kind": "guardhouse", "z": 1},
                                    {"x": 360, "y": 256, "w": 60, "h": 44, "rot": rot, "kind": "inspection", "z": 1}])


def test_city_gate_furniture_aligned_fires_when_axis_aligned_on_a_slanted_wall():
    # guard house + inspection station left axis-aligned (rot 0) on a 45 deg wall edge
    M = _gate_furn(0, wall=_DIAMOND, gates=[[650, 350], [350, 650]])
    M["gate_structs"] = [{"x": 640, "y": 360, "w": 66, "h": 44, "rot": 0, "kind": "guardhouse", "z": 1},
                         {"x": 610, "y": 390, "w": 60, "h": 44, "rot": 0, "kind": "inspection", "z": 1}]
    assert "city_gate_furniture_aligned" in f(M)


def test_city_gate_furniture_aligned_passes_when_square_to_the_wall():
    M = _gate_furn(45, wall=_DIAMOND, gates=[[650, 350], [350, 650]])
    M["gate_structs"] = [{"x": 640, "y": 360, "w": 66, "h": 44, "rot": 45, "kind": "guardhouse", "z": 1},
                         {"x": 610, "y": 390, "w": 60, "h": 44, "rot": 45, "kind": "inspection", "z": 1}]
    assert "city_gate_furniture_aligned" not in f(M)


def test_city_gate_furniture_aligned_fires_on_a_90_degree_turn():
    # on the horizontal top wall a guard house turned 90 deg stands across the road the wrong way
    assert "city_gate_furniture_aligned" in f(_gate_furn(90))


def test_city_gate_furniture_aligned_passes_when_along_the_wall():
    assert "city_gate_furniture_aligned" not in f(_gate_furn(0))


def test_city_has_ring_road_fires_when_missing():
    assert "city_has_ring_road" in f(_fort_city())


_RING = [[240, 240], [760, 240], [760, 760], [240, 760], [240, 240]]


def test_city_has_ring_road_passes_when_present():
    assert "city_has_ring_road" not in f(_fort_city(ring_road=_RING))


def _ring_city(streets, **extra):
    return _fort_city(ring_road=_RING, ring_road_width=15, town_streets=[{"pts": p, "w": 18} for p in streets], **extra)


def test_city_streets_meet_through_lanes_fires_when_a_street_undershoots_the_ring():
    # a street ending 40px short of the ring (its left side sits at x=240), heading at it
    assert "city_streets_meet_through_lanes" in f(_ring_city([[[400, 500], [280, 500]]]))


def test_city_streets_meet_through_lanes_fires_when_a_street_overshoots_the_ring():
    # a street poking ~6px PAST the ring (ending at x=234, the ring is at x=240) - a stub through the far side
    assert "city_streets_meet_through_lanes" in f(_ring_city([[[400, 500], [234, 500]]]))


def test_city_streets_meet_through_lanes_fires_at_the_imperial_road():
    # a street stopping short of the Imperial road (road centerline x=500; the street ends at x=470)
    M = _fort_city(road=[[500, 100], [500, 900]], road_width=26,
                   town_streets=[{"pts": [[300, 500], [470, 500]], "w": 18}])
    assert "city_streets_meet_through_lanes" in f(M)


def test_city_streets_meet_through_lanes_passes_when_it_meets_the_bed():
    assert "city_streets_meet_through_lanes" not in f(_ring_city([[[400, 500], [248, 500]]]))   # ends in the ring bed


def test_city_streets_meet_through_lanes_fires_when_an_alley_undershoots_the_ring():
    # the check covers gravel ALLEYS too, not just paved streets - the laborer-warren case the GM caught:
    # an alley running straight at the ring and stopping ~40px short
    M = _fort_city(ring_road=_RING, ring_road_width=15, alleys=[{"pts": [[400, 500], [280, 500]]}])
    assert "city_streets_meet_through_lanes" in f(M)


def test_city_streets_meet_through_lanes_passes_when_an_alley_meets_the_ring():
    M = _fort_city(ring_road=_RING, ring_road_width=15, alleys=[{"pts": [[400, 500], [246, 500]]}])   # ends in the ring bed
    assert "city_streets_meet_through_lanes" not in f(M)


# --- ring_road_kept_clear (no building/civic/field footprint overlaps the ring road bed) ---
def _on_ring_bldg():   # a 40px dwelling straddling the west ring leg (x=240)
    return {"kind": "samurai", "x": 240, "y": 500, "w": 40, "h": 40, "rot": 0}


def test_ring_road_kept_clear_fires_on_a_building_on_the_ring():
    assert "ring_road_kept_clear" in f(_fort_city(ring_road=_RING, ring_road_width=15, buildings=[_on_ring_bldg()]))


def test_ring_road_kept_clear_fires_on_a_ministry_on_the_ring():
    M = _fort_city(ring_road=_RING, ring_road_width=15,
                   ministries=[{"name": "Ministry of Rites", "x": 760, "y": 500, "w": 50, "h": 50}])
    assert "ring_road_kept_clear" in f(M)


def test_ring_road_kept_clear_fires_on_a_field_on_the_ring():
    field = {"name": "f1", "kind": "dry", "bbox": [220, 480, 260, 520], "outline": [[220, 480], [260, 480], [260, 520], [220, 520]]}   # straddles the west leg
    assert "ring_road_kept_clear" in f(_fort_city(ring_road=_RING, ring_road_width=15, fields=[field]))


def test_ring_road_kept_clear_passes_when_clear():
    # a dwelling parked in the city center, well inside the ring
    M = _fort_city(ring_road=_RING, ring_road_width=15,
                   buildings=[{"kind": "samurai", "x": 500, "y": 500, "w": 40, "h": 40, "rot": 0}])
    assert "ring_road_kept_clear" not in f(M)


def test_ring_road_kept_clear_passes_without_a_ring():
    assert "ring_road_kept_clear" not in f(_fort_city(buildings=[_on_ring_bldg()]))


# --- intersections_are_crossroads (lane beds merge, no edge line across a junction) ---
def test_intersections_are_crossroads_fires_when_edges_over_beds():
    assert "intersections_are_crossroads" in f({"ground_edge_zmax": 50, "ground_bed_zmin": 20})


def test_intersections_are_crossroads_passes_when_edges_under_beds():
    assert "intersections_are_crossroads" not in f({"ground_edge_zmax": 19, "ground_bed_zmin": 20})


def test_city_merchant_housing_spread_fires_when_jammed():
    # merchant homes jammed as tight as the laborers (same ~16px spacing) - not more spread out
    homes = [bldg(300 + i * 16, 300, kind="merchant_house") for i in range(8)]
    labor = [bldg(300 + i * 16, 500, kind="laborer") for i in range(8)]
    assert "city_merchant_housing_spread" in f(_merchant_city(homes + labor))


def _temple_city(religious):
    return {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
            "gates": [[500, 200], [500, 800]], "religious": religious}


def test_city_temple_neighborhood_has_shrines_fires_when_bare():
    rel = [{"kind": "temple", "x": 400, "y": 400, "w": 80, "h": 60}, {"kind": "temple", "x": 550, "y": 420, "w": 80, "h": 60}]
    assert "city_temple_neighborhood_has_shrines" in f(_temple_city(rel))


def test_city_temple_neighborhood_has_shrines_passes_with_shrines():
    rel = [{"kind": "temple", "x": 400, "y": 400, "w": 80, "h": 60}, {"kind": "temple", "x": 550, "y": 420, "w": 80, "h": 60}]
    rel += [{"kind": "small_shrine", "x": 450 + i * 20, "y": 480, "w": 32, "h": 24, "rot": 0} for i in range(3)]
    assert "city_temple_neighborhood_has_shrines" not in f(_temple_city(rel))


def test_city_temple_neighborhood_has_shrines_skips_a_lone_temple():
    # a single temple (e.g. the warrior-fortune temple among the samurai) is not a neighborhood
    assert "city_temple_neighborhood_has_shrines" not in f(_temple_city([{"kind": "temple", "x": 400, "y": 400, "w": 80, "h": 60}]))


def _estate_city(estates, **extra):
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]], "merchant_estates": estates}
    M.update(extra)
    return M


def test_city_merchant_estates_clear_of_wall_moat_fires():
    # an estate COURT straddling the TOP wall (not just the house inside)
    assert "city_merchant_estates_clear_of_wall_moat" in f(_estate_city([{"x": 500, "y": 210, "w": 78, "h": 58}]))


def test_city_merchant_estates_clear_of_buildings_fires_on_a_temple():
    # an estate court over a temple whose CENTRE is outside the court (so it is not its own inner house)
    M = _estate_city([{"x": 500, "y": 500, "w": 78, "h": 58}],
                     religious=[{"x": 500, "y": 560, "w": 80, "h": 80, "kind": "temple", "label": "Temple"}])
    assert "city_merchant_estates_clear_of_buildings" in f(M)


def test_city_merchant_estates_clear_of_buildings_fires_on_another_estate():
    # two estate courts overlapping each other (the for-else estate-vs-estate path)
    M = _estate_city([{"x": 500, "y": 500, "w": 78, "h": 58}, {"x": 540, "y": 500, "w": 78, "h": 58}])
    assert "city_merchant_estates_clear_of_buildings" in f(M)


def test_city_merchant_estate_gate_clear_fires_when_gate_into_a_temple():
    # the estate wall abuts a temple below it (fine), but its gate opens SOUTH straight into the temple
    M = _estate_city([{"x": 500, "y": 500, "w": 78, "h": 58, "gate": [500, 529], "gate_dir": "south"}],
                     religious=[{"x": 500, "y": 560, "w": 80, "h": 60, "kind": "temple", "label": "T"}])
    assert "city_merchant_estate_gate_clear" in f(M)


def test_city_merchant_estate_gate_clear_passes_when_gate_points_away():
    # same abutting temple, but the gate opens NORTH onto open ground
    M = _estate_city([{"x": 500, "y": 500, "w": 78, "h": 58, "gate": [500, 471], "gate_dir": "north"}],
                     religious=[{"x": 500, "y": 560, "w": 80, "h": 60, "kind": "temple", "label": "T"}])
    assert "city_merchant_estate_gate_clear" not in f(M)


def test_city_merchant_estates_clear_passes_when_well_placed():
    M = _estate_city([{"x": 500, "y": 500, "w": 78, "h": 58}],
                     buildings=[{"x": 500, "y": 500, "w": 36, "h": 25, "rot": 0, "kind": "merchant_large"}])
    assert "city_merchant_estates_clear_of_wall_moat" not in f(M)
    assert "city_merchant_estates_clear_of_buildings" not in f(M)


def test_city_merchant_housing_spread_passes_when_roomier():
    homes = [bldg(300 + i * 44, 300, kind="merchant_house") for i in range(8)]   # 44px apart
    labor = [bldg(300 + i * 16, 500, kind="laborer") for i in range(8)]          # 16px apart (dense)
    assert "city_merchant_housing_spread" not in f(_merchant_city(homes + labor))


def _ward_city(boundary):
    return {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
            "gates": [[500, 200], [500, 800]], "wards": [{"name": "x", "boundary": boundary}]}


def test_city_ward_fence_meets_wall_fires_on_a_gap():
    # a fence end floating 100px inside the wall, nowhere near it - a clear walk-around gap
    assert "city_ward_fence_meets_wall" in f(_ward_city([[300, 795], [300, 400]]))


def test_city_ward_fence_meets_wall_fires_when_end_in_a_gate_opening():
    # the end sits ON the wall polygon but right at a gate, where the wall is cut - it meets nothing
    assert "city_ward_fence_meets_wall" in f(_ward_city([[500, 205], [795, 500]]))


def test_city_ward_fence_meets_wall_passes_when_ends_abut_solid_wall():
    # both ends on solid rampart, clear of the gate openings
    assert "city_ward_fence_meets_wall" not in f(_ward_city([[300, 205], [795, 500]]))


def test_city_ward_fence_under_wall_fires_without_a_cap():
    # the fence ends abut the wall but no wall cap is drawn on top (z), so the fence paints over it
    M = _ward_city([[300, 205], [795, 500]])
    M["wards"][0].update({"z": 100, "wall_caps": []})
    assert "city_ward_fence_under_wall" in f(M)


def test_city_ward_fence_under_wall_passes_with_caps_on_top():
    # a wall cap (higher z) over each end -> the rampart renders on top, the fence runs under it
    M = _ward_city([[300, 205], [795, 500]])
    M["wards"][0].update({"z": 100, "wall_caps": [{"x": 300, "y": 200, "z": 150}, {"x": 800, "y": 500, "z": 151}]})
    assert "city_ward_fence_under_wall" not in f(M)


def _moat_city(channel_poly):
    # square moat fed by a stream entering its NORTH edge from off the top -> the moat flows SOUTH
    return {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
            "wall": [[320, 320], [680, 320], [680, 680], [320, 680]],
            "moat": [[300, 300], [700, 300], [700, 700], [300, 700]],
            "streams": [{"poly": [[500, 40], [500, 300]], "frm": {"kind": "offmap"}, "to": {"kind": "moat"}}],
            "channels": [{"poly": channel_poly, "frm": {"kind": "moat"}, "to": {"kind": "field", "name": "f"}}],
            "gates": [[500, 300], [500, 700]]}


def test_moat_channels_flow_with_current_fires_when_against():
    # moat flows south; this channel taps the moat at (350,300) and runs NORTH to a field at (350,150)
    # - the field is upstream of the tap, so water would run field->moat (backwards)
    assert "moat_channels_flow_with_current" in f(_moat_city([[350, 300], [350, 150]]))


def test_moat_channels_flow_with_current_passes_when_downstream():
    # same moat, but the channel runs SOUTH (with the current) to a field below its tap
    assert "moat_channels_flow_with_current" not in f(_moat_city([[350, 700], [350, 850]]))


def test_outside_fields_farmhouse_density_fires_on_a_bare_shown_field():
    # a field showing a long on-map edge (fully inside the canvas) but with NO farmhouses beside it:
    # a worked field carries farmhouses at ~village density on its shown portion. This is the partial-
    # field gap - the old per-field ">=2 anywhere" let an on-map field edge sit bare.
    field = {"name": "f1", "kind": "paddy", "bbox": [300, 300, 700, 700],
             "outline": [[300, 300], [700, 300], [700, 700], [300, 700]]}
    M = {"meta": {"scale": "town", "W": 1000, "H": 1000}, "fields": [field], "houses": []}
    assert "outside_fields_farmhouse_density" in f(M)


def test_clip_and_onmap_edge_handle_a_fully_offmap_field():
    # a field lying entirely outside the map rect clips to nothing and contributes no on-map edge
    poly = [[-500, -500], [-300, -500], [-300, -300], [-500, -300]]
    assert check_village.clip_poly_rect(poly, 0, 0, 1000, 1000) == []
    assert check_village.onmap_field_edge(poly, 0, 0, 1000, 1000) == 0.0


def test_outside_fields_farmhouse_density_passes_when_edge_is_a_tiny_sliver():
    # a field whose only on-map edge is a tiny corner (< 120px) is too small a sliver to require
    # farmhouses - its workers are off-map with the rest of the field. Must NOT fire.
    field = {"name": "f1", "kind": "paddy", "bbox": [-400, -400, 50, 50],
             "outline": [[-400, -400], [50, -400], [50, 50], [-400, 50]]}   # only a ~50x50 corner shows
    M = {"meta": {"scale": "town", "W": 1000, "H": 1000}, "fields": [field], "houses": []}
    assert "outside_fields_farmhouse_density" not in f(M)


def test_city_lane_under_wall_fires_when_street_crosses_wall_off_gate():
    # an E-W street punched clean through the wall (crossing both side faces, far from the N/S gates)
    # and drawn OVER it: a lane must run UNDER the rampart except at a gate.
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
         "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "wall_z": 5,
         "town_streets": [{"pts": [[100, 500], [900, 500]], "w": 18, "z": 50}]}   # crosses x=200 and x=800, far from gates
    assert "city_lane_under_wall" in f(M)


def test_city_samurai_partly_front_streets_fires_when_all_set_back():
    # plenty of samurai houses but every one buried far from the street: a samurai quarter LINES its
    # streets, so an all-interior cluster (none within 90px of a lane) trips the check.
    sam = [bldg(300 + (i % 8) * 30, 300 + (i // 8) * 30, kind="samurai") for i in range(40)]   # all up in the NW corner
    M = {"meta": {"scale": "city", "walled": True, "population": 3000, "W": 1000, "H": 1000},
         "wall": WALLSQ, "gates": [[500, 200], [500, 800]],
         "town_streets": [{"pts": [[600, 600], [800, 600]], "w": 18}],   # the only street is far from the cluster
         "buildings": sam}
    assert "city_samurai_partly_front_streets" in f(M)


def test_walled_city_structural_checks_fire():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
         "wall": WALLSQ, "gates": [[500, 200]]}   # only ONE gate, no stations / burakumin / estates / road
    fails = f(M)
    assert "walled_city_has_wall_and_gates" in fails
    assert "city_inspection_station_at_each_gate" in fails
    assert "walled_city_has_burakumin_inside" in fails
    assert "city_samurai_estates_outside" in fails        # 0 estates, want 5-15
    assert "city_imperial_road_through" in fails


def test_city_samurai_estates_vary_in_size_fires_when_uniform():
    estates = [{"x": 900 + i * 12, "y": 900, "w": 100, "h": 80} for i in range(6)]   # 6 (in range), all identical
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
         "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "manors": estates}
    fails = f(M)
    assert "city_samurai_estates_vary_in_size" in fails
    assert "city_samurai_estates_outside" not in fails    # 6 IS in the 5-15 range


def test_city_streets_have_buildings_fires_on_an_empty_city_street():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]], "town_streets": [{"pts": [[300, 300], [700, 300]], "w": 20}]}
    assert "city_streets_have_buildings" in f(M)


def test_city_streets_have_buildings_ignores_frontage_across_a_ward_fence():
    # the buildings hug the street (60px away) but a ward fence runs BETWEEN them and it: they front
    # whatever lies on their own side, not this street, so the street still reads as empty and fires.
    # (This is the Tango government-avenue bug: gap-band housing across the ward fence papered over a
    # bare avenue. A building walled off from a street cannot count as fronting it.)
    blds = [bldg(320 + i * 40, 440, kind="laborer") for i in range(9)]   # y440: 60px N of the street, N of the fence
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]],
         "town_streets": [{"pts": [[300, 500], [700, 500]], "w": 20}],
         "wards": [{"name": "x", "boundary": [[280, 470], [720, 470]]}],   # fence between the houses and the street
         "buildings": blds}
    assert "city_streets_have_buildings" in f(M)


def _street_city(streets, **extra):
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]], "town_streets": streets}
    M.update(extra)
    return M


def test_city_larger_streets_lined_fires_on_a_bare_street():
    # a main avenue through open ground inside the wall, no buildings within ~58px of it
    assert "city_larger_streets_lined" in f(_street_city([{"pts": [[300, 500], [700, 500]], "w": 22, "main": True}]))


def test_city_larger_streets_lined_passes_when_lined():
    # the same avenue, shophouses lining it ~32px off on both sides
    blds = [bldg(x, 500 + s * 32, kind="shop", w=20, h=14) for x in range(320, 701, 40) for s in (-1, 1)]
    assert "city_larger_streets_lined" not in f(_street_city([{"pts": [[300, 500], [700, 500]], "w": 22, "main": True}], buildings=blds))


def test_city_larger_streets_lined_exempts_a_government_avenue():
    # a bare avenue, but two ministry compounds front it -> a government avenue, exempt (its frontage
    # is the spaced ministries, governed by city_ministries_front_a_street, not shops/houses)
    M = _street_city([{"pts": [[300, 500], [700, 500]], "w": 18}],
                     ministries=[{"name": "A", "x": 400, "y": 565, "w": 88, "h": 58},
                                 {"name": "B", "x": 620, "y": 565, "w": 88, "h": 58}])
    assert "city_larger_streets_lined" not in f(M)


def test_city_civic_amenity_checks_fire_on_an_empty_city():
    fails = f({"meta": {"scale": "city"}})
    for name in ("city_has_merchant_storehouses", "city_has_flophouse", "city_has_theater_stage"):
        assert name in fails


def _caravan_city(**extra):
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200]]}
    M.update(extra)
    return M


def test_city_gate_caravan_facilities_fires_without_inn_and_stables():
    # a gate with only a flophouse - no prominent inn, no large stables for the wagon-trains' animals
    M = _caravan_city(flophouses=[{"x": 500, "y": 300, "w": 88, "h": 42, "rot": 0}])
    assert "city_gate_caravan_facilities" in f(M)


def test_city_gate_caravan_facilities_passes_with_the_full_cluster():
    M = _caravan_city(flophouses=[{"x": 450, "y": 300, "w": 88, "h": 42, "rot": 0}],
                      buildings=[{"x": 520, "y": 320, "w": 66, "h": 48, "kind": "inn", "rot": 0},
                                 {"x": 470, "y": 380, "w": 92, "h": 44, "kind": "stables", "rot": 0}])
    assert "city_gate_caravan_facilities" not in f(M)


def test_city_gate_caravan_facilities_fires_when_stables_hemmed_in():
    # the full cluster is present, but the stables is hemmed in by dwellings (no open ground for animals)
    blds = [{"x": 470, "y": 380, "w": 92, "h": 44, "kind": "stables", "rot": 0},
            {"x": 520, "y": 320, "w": 66, "h": 48, "kind": "inn", "rot": 0}]
    blds += [bldg(440 + i * 22, 380, kind="samurai") for i in range(6)]   # dwellings crowd the stables
    M = _caravan_city(flophouses=[{"x": 450, "y": 300, "w": 88, "h": 42, "rot": 0}], buildings=blds)
    assert "city_gate_caravan_facilities" in f(M)


def test_city_theater_stage_larger_than_town_fires_when_small():
    # a town-sized theater stage (viewing ground 150 wide) in a city - a city's is larger (>= 185)
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]], "theater_stage": {"x": 500, "y": 500, "w": 150, "h": 105, "rot": 0},
         "religious": [{"x": 540, "y": 540, "w": 120, "h": 80, "rot": 0, "kind": "temple"}]}
    assert "city_theater_stage_larger_than_town" in f(M)


def test_theater_stage_by_temple_fires_when_far_from_any_hall():
    # a town theater stage sited off on its own, far from any temple/monastery - it was a temple/shrine
    # performance stage, so it must sit ADJACENT to a religious hall
    M = {"meta": {"scale": "town"}, "theater_stage": {"x": 500, "y": 500, "w": 150, "h": 105, "rot": 0},
         "religious": [{"x": 1200, "y": 1200, "w": 132, "h": 86, "rot": 0, "kind": "monastery"}]}
    assert "theater_stage_by_temple" in f(M)


def test_theater_stage_by_temple_passes_when_adjacent():
    M = {"meta": {"scale": "town"}, "theater_stage": {"x": 500, "y": 500, "w": 150, "h": 105, "rot": 0},
         "religious": [{"x": 540, "y": 620, "w": 132, "h": 86, "rot": 0, "kind": "monastery"}]}
    assert "theater_stage_by_temple" not in f(M)


def test_theater_stage_faces_temple_fires_when_back_to_the_hall():
    # adjacent to the monastery (NORTH) but the stage's viewing ground opens SOUTH (rot=0) - its BACK is to
    # the hall, the audience facing away. This is the Hoshizora bug the check is meant to catch.
    M = {"meta": {"scale": "town"}, "theater_stage": {"x": 500, "y": 500, "w": 150, "h": 105, "rot": 0},
         "religious": [{"x": 510, "y": 380, "w": 132, "h": 86, "rot": 0, "kind": "monastery"}]}
    assert "theater_stage_faces_temple" in f(M)


def test_theater_stage_faces_temple_passes_when_open_toward_hall():
    # the hall is SOUTH and the ground opens SOUTH (rot=0) - the stage faces the hall, audience between
    M = {"meta": {"scale": "town"}, "theater_stage": {"x": 500, "y": 500, "w": 150, "h": 105, "rot": 0},
         "religious": [{"x": 510, "y": 640, "w": 132, "h": 86, "rot": 0, "kind": "monastery"}]}
    assert "theater_stage_faces_temple" not in f(M)


# ---- theater_stage_clear: the stage footprint overlaps NOTHING (the Hirameki-on-the-wall bug) ----------
_STAGE = {"x": 500, "y": 500, "w": 150, "h": 105, "rot": 0}


def test_theater_stage_clear_fires_on_a_wall():
    M = {"meta": {"scale": "town"}, "theater_stage": dict(_STAGE), "wall": [[500, 380], [500, 620]]}
    assert "theater_stage_clear" in f(M)


def test_theater_stage_clear_fires_on_a_building():
    M = {"meta": {"scale": "town"}, "theater_stage": dict(_STAGE), "buildings": [bldg(500, 500, "merchant")]}
    assert "theater_stage_clear" in f(M)


def test_theater_stage_clear_fires_on_a_field():
    M = {"meta": {"scale": "town"}, "theater_stage": dict(_STAGE), "fields": [_field("f", 400, 400, 600, 600)]}
    assert "theater_stage_clear" in f(M)


def test_theater_stage_clear_fires_on_the_pond():
    M = {"meta": {"scale": "town"}, "theater_stage": dict(_STAGE), "pond": [500, 500, 80, 60]}
    assert "theater_stage_clear" in f(M)


def test_theater_stage_clear_passes_in_open_ground():
    M = {"meta": {"scale": "town"}, "theater_stage": dict(_STAGE),
         "religious": [{"x": 510, "y": 640, "w": 132, "h": 86, "rot": 0, "kind": "monastery"}]}
    assert "theater_stage_clear" not in f(M)


# --- labels_clear_of_other_buildings (a label may cover only the thing it names) ---
def _bldg(kind, x=500, y=500, w=40, h=30):
    return {"kind": kind, "x": x, "y": y, "w": w, "h": h, "rot": 0}


def _lbl_city(**extra):
    M = {"meta": {"scale": "city"}, "labels": [[480, 490, 520, 510, 1, "flophouse"]]}
    M.update(extra)
    return M


def test_labels_clear_of_other_buildings_fires_when_label_over_a_foreign_building():
    # a "flophouse" label spilling onto a merchant house next door
    assert "labels_clear_of_other_buildings" in f(_lbl_city(buildings=[_bldg("merchant_house")]))


def test_labels_clear_of_other_buildings_fires_when_guard_label_over_a_flophouse():
    M = _lbl_city(labels=[[470, 490, 560, 510, 1, "gate guard house + inspection"]],
                  flophouses=[{"x": 500, "y": 500, "w": 90, "h": 42, "rot": 0}])
    assert "labels_clear_of_other_buildings" in f(M)


def test_labels_clear_of_other_buildings_passes_over_its_own_building():
    assert "labels_clear_of_other_buildings" not in f(_lbl_city(flophouses=[{"x": 500, "y": 500, "w": 90, "h": 42, "rot": 0}]))


def test_labels_clear_of_other_buildings_passes_over_a_fronting_shop():
    # a market/zone label may clip a street-fronting shop (shops line every quarter)
    M = _lbl_city(labels=[[480, 490, 520, 510, 1, "gate market"]], buildings=[_bldg("shop")])
    assert "labels_clear_of_other_buildings" not in f(M)


def test_labels_clear_of_other_buildings_passes_for_a_zone_label_over_its_cluster():
    M = _lbl_city(labels=[[480, 490, 520, 510, 1, "samurai neighborhood"]], buildings=[_bldg("samurai", w=56, h=40)])
    assert "labels_clear_of_other_buildings" not in f(M)


# --- the check also runs at TOWN scale (the monastery/graveyard cross-overlap the GM hit) ---
def _lbl_town(label_text, **extra):
    M = {"meta": {"scale": "town"}, "labels": [[480, 490, 520, 510, 1, label_text]]}
    M.update(extra)
    return M


def test_labels_clear_town_monastery_label_over_graveyard_fires():
    M = _lbl_town("Monastery of Bishamon", cemeteries=[{"x": 500, "y": 500, "w": 80, "h": 50, "rot": 0, "parish": True}])
    assert "labels_clear_of_other_buildings" in f(M)


def test_labels_clear_town_graveyard_label_over_temple_fires():
    M = _lbl_town("graveyard", religious=[{"kind": "monastery", "x": 500, "y": 500, "w": 80, "h": 50, "label": "M"}])
    assert "labels_clear_of_other_buildings" in f(M)


def test_labels_clear_town_funerary_label_over_funerary_passes():
    # the funerary structures cluster, so a funerary label may cover any of them
    M = _lbl_town("cremation ground", cemeteries=[{"x": 500, "y": 500, "w": 80, "h": 50, "rot": 0, "parish": True}])
    assert "labels_clear_of_other_buildings" not in f(M)


def test_labels_clear_town_street_label_over_merchant_passes():
    # a street/road label runs along its frontage, so it may clip the storefronts it lines
    M = _lbl_town("main street", buildings=[_bldg("merchant", w=60, h=40)])
    assert "labels_clear_of_other_buildings" not in f(M)


# --- city_civic_label_on_its_own_building (a named civic label may sit only on ITS OWN building) ---
def test_city_civic_label_on_its_own_building_fires_over_a_sibling_ministry():
    # the "Ministry of Justice" label drifts onto the "Ministry of Works" office - same group, so
    # labels_clear_of_other_buildings misses it, but this finer check catches it
    M = {"meta": {"scale": "city"},
         "ministries": [{"name": "Ministry of Works", "x": 500, "y": 500, "w": 88, "h": 58},
                        {"name": "Ministry of Justice", "x": 500, "y": 640, "w": 88, "h": 58}],
         "labels": [[470, 490, 560, 510, 1, "Ministry of Justice"]]}
    assert "city_civic_label_on_its_own_building" in f(M)
    assert "labels_clear_of_other_buildings" not in f(M)   # the coarse check is fooled by the shared group


def test_city_civic_label_on_its_own_building_passes_over_its_own():
    M = {"meta": {"scale": "city"},
         "ministries": [{"name": "Ministry of Works", "x": 500, "y": 500, "w": 88, "h": 58}],
         "labels": [[470, 490, 560, 510, 1, "Ministry of Works"]]}
    assert "city_civic_label_on_its_own_building" not in f(M)


# --- city_government_offices_dont_abut (a ministry / the yamen must stand clear of its neighbours) ---
def test_city_government_offices_dont_abut_fires_when_two_ministries_touch():
    M = {"meta": {"scale": "city"},
         "ministries": [{"name": "Ministry of Works", "x": 500, "y": 500, "w": 88, "h": 58},
                        {"name": "Ministry of Justice", "x": 500, "y": 560, "w": 88, "h": 58}]}   # 2px gap
    assert "city_government_offices_dont_abut" in f(M)


def test_city_government_offices_dont_abut_passes_when_clear():
    M = {"meta": {"scale": "city"},
         "ministries": [{"name": "Ministry of Works", "x": 500, "y": 500, "w": 88, "h": 58},
                        {"name": "Ministry of Justice", "x": 500, "y": 640, "w": 88, "h": 58}]}   # 82px gap
    assert "city_government_offices_dont_abut" not in f(M)


def test_city_government_offices_dont_abut_ignores_ordinary_houses():
    # ordinary city houses MAY touch - only government offices must stand clear
    M = {"meta": {"scale": "city"},
         "buildings": [{"kind": "laborer", "x": 500, "y": 500, "w": 14, "h": 10, "rot": 0},
                       {"kind": "laborer", "x": 512, "y": 500, "w": 14, "h": 10, "rot": 0}]}
    assert "city_government_offices_dont_abut" not in f(M)


# --- city wells: water access + block-interior placement ---
def _well_city(**extra):
    M = {"meta": {"scale": "city"}, "wells": [{"x": 500, "y": 500, "r": 8}]}
    M.update(extra)
    return M


def test_city_neighborhoods_have_wells_fires_when_a_dwelling_is_dry():
    # a laborer dwelling 990px from the only well - the water network forgot its neighborhood
    M = _well_city(buildings=[{"kind": "laborer", "x": 1200, "y": 1200, "w": 28, "h": 18, "rot": 0}])
    assert "city_neighborhoods_have_wells" in f(M)


def test_city_neighborhoods_have_wells_passes_when_in_reach():
    M = _well_city(buildings=[{"kind": "laborer", "x": 560, "y": 540, "w": 28, "h": 18, "rot": 0}])
    assert "city_neighborhoods_have_wells" not in f(M)


def test_city_neighborhoods_have_wells_ignores_samurai_and_outside_dwellings():
    # samurai have private wells; a dwelling OUTSIDE the wall (a gate market) is not a residential
    # neighborhood - neither demands a public well even when far from one
    M = _well_city(wall=WALLSQ, buildings=[{"kind": "samurai", "x": 500, "y": 500, "w": 56, "h": 40, "rot": 0},
                                           {"kind": "merchant", "x": 980, "y": 980, "w": 40, "h": 30, "rot": 0}])
    assert "city_neighborhoods_have_wells" not in f(M)


def test_city_wells_in_block_interiors_fires_on_a_lane():
    M = _well_city(town_streets=[{"pts": [[400, 500], [600, 500]], "w": 18}])
    assert "city_wells_in_block_interiors" in f(M)


def test_city_wells_in_block_interiors_fires_on_a_building():
    M = _well_city(buildings=[{"kind": "laborer", "x": 505, "y": 505, "w": 40, "h": 30, "rot": 0}])
    assert "city_wells_in_block_interiors" in f(M)


def test_city_wells_in_block_interiors_passes_when_clear():
    assert "city_wells_in_block_interiors" not in f(_well_city())


def _warren(nwells):
    # 30 laborer dwellings in a tight cluster, served by `nwells` wells spread across it
    blds = [{"kind": "laborer", "x": 500 + (i % 6) * 15, "y": 500 + (i // 6) * 15, "w": 14, "h": 10, "rot": 0} for i in range(30)]
    wells = [{"x": 500 + i * (75 // max(1, nwells - 1) if nwells > 1 else 0), "y": 530, "r": 8} for i in range(nwells)]
    return {"meta": {"scale": "city"}, "buildings": blds, "wells": wells}


def test_city_well_density_sufficient_fires_when_a_well_is_overburdened():
    # 30 households all nearest a single well -> it is the nearest for far more than 26
    assert "city_well_density_sufficient" in f(_warren(1))


def test_city_well_density_sufficient_passes_with_enough_wells():
    # three wells split the 30 households -> ~10 each, none over-burdened
    assert "city_well_density_sufficient" not in f(_warren(3))


def test_city_samurai_quarter_has_no_public_wells_fires_among_samurai():
    # a wellhead embedded among samurai dwellings - the samurai quarter has no communal wells
    M = _well_city(buildings=[{"kind": "samurai", "x": 510, "y": 505, "w": 24, "h": 17, "rot": 0},
                              {"kind": "samurai", "x": 480, "y": 520, "w": 24, "h": 17, "rot": 0},
                              {"kind": "laborer", "x": 900, "y": 900, "w": 14, "h": 10, "rot": 0}])
    assert "city_samurai_quarter_has_no_public_wells" in f(M)


def test_city_samurai_quarter_has_no_public_wells_passes_among_commoners():
    # the same well, but it sits among commoner dwellings (a samurai house is a block away) - fine
    M = _well_city(buildings=[{"kind": "laborer", "x": 510, "y": 505, "w": 14, "h": 10, "rot": 0},
                              {"kind": "laborer", "x": 480, "y": 520, "w": 14, "h": 10, "rot": 0},
                              {"kind": "samurai", "x": 900, "y": 900, "w": 24, "h": 17, "rot": 0}])
    assert "city_samurai_quarter_has_no_public_wells" not in f(M)


def test_city_streets_connected_and_empty_space_fire():
    # two town streets far apart with no road -> two disconnected groups; the interior is almost
    # all empty (no buildings/fields), and a pond sits on a grid point (the pond-as-occupancy path)
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
         "wall": [[100, 100], [900, 100], [900, 900], [100, 900]], "gates": [[500, 100], [500, 900]],
         "town_streets": [{"pts": [[200, 200], [200, 400]], "w": 18}, {"pts": [[700, 600], [700, 800]], "w": 18}],
         "pond": [400, 400, 80, 60]}
    fails = f(M)
    assert "city_streets_connected" in fails
    assert "city_no_large_empty_space" in fails


def test_city_streets_connected_fires_on_a_gap_wider_than_45px():
    # two parallel streets 60px apart: the old 95px tolerance bridged them, the tightened 45px
    # does not - a grid that stops short of the road reads as a separated network, not connected
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
         "wall": WALLSQ, "gates": [[500, 200], [500, 800]],
         "town_streets": [{"pts": [[400, 300], [400, 700]], "w": 18},
                          {"pts": [[460, 300], [460, 700]], "w": 18}]}   # 60px apart, no road bridge
    assert "city_streets_connected" in f(M)


def test_city_streets_connected_requires_beds_to_actually_overlap():
    # a cross-street whose end stops 30px short of the through-street: under the old flat 45px
    # tolerance this "connected", but the two paved beds (half-widths 9+9) do not touch, so you
    # cannot walk between them - it is a separate network. This is the Tango laborer-grid bug.
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
         "wall": WALLSQ, "gates": [[500, 200], [500, 800]],
         "town_streets": [{"pts": [[300, 400], [700, 400]], "w": 18},   # the through-street
                          {"pts": [[400, 430], [400, 700]], "w": 18}]}   # ends 30px below it: beds 18px apart
    assert "city_streets_connected" in f(M)


def test_city_flophouse_inside_walls_fires_when_only_outside():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]],
         "flophouses": [{"x": 500, "y": 120, "w": 92, "h": 42, "rot": 0}, {"x": 500, "y": 880, "w": 92, "h": 42, "rot": 0}]}
    assert "city_flophouse_inside_walls" in f(M)


def test_city_flophouse_outside_each_gate_fires_when_a_gate_lacks_one():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]],
         "flophouses": [{"x": 500, "y": 500, "w": 92, "h": 42, "rot": 0},     # inside
                        {"x": 500, "y": 120, "w": 92, "h": 42, "rot": 0}]}    # outside the north gate only
    assert "city_flophouse_outside_each_gate" in f(M)


def test_city_estates_multiple_shown_fires_when_only_one_in_view():
    M = {"meta": {"scale": "city", "walled": True, "W": 3000, "H": 3000, "view": [0, 0, 1000, 1000]},
         "wall": WALLSQ, "gates": [[500, 200], [500, 800]],
         "manors": [{"x": 600, "y": 600, "w": 100, "h": 80},        # inside the view
                    {"x": 2000, "y": 2000, "w": 100, "h": 80}]}     # off the cropped view
    assert "city_estates_multiple_shown" in f(M)


def test_city_road_label_outside_walls_fires_when_inside():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]], "road_label": [500, 500]}   # dead center, inside the walls
    assert "city_road_label_outside_walls" in f(M)


def test_city_streets_no_near_miss_fires_on_a_sliver_gap():
    # two street segments ~18px apart that do NOT cross - they almost touch but never meet
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]],
         "town_streets": [{"pts": [[300, 400], [500, 400]], "w": 18},     # ends at (500, 400)
                          {"pts": [[515, 410], [515, 700]], "w": 18}]}    # top at (515, 410): an ~18px gap
    assert "city_streets_no_near_miss" in f(M)


def test_city_ministries_front_a_street_fires_when_floating():
    # a ministry with the nearest street ~290px away - it floats mid-block, fronting nothing
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]],
         "ministries": [{"x": 500, "y": 500, "w": 88, "h": 58, "name": "Ministry of War"}],
         "town_streets": [{"pts": [[250, 250], [350, 250]], "w": 18}]}
    assert "city_ministries_front_a_street" in f(M)


def test_city_ministries_front_a_street_passes_when_on_a_street():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]],
         "ministries": [{"x": 500, "y": 500, "w": 88, "h": 58, "name": "Ministry of War"}],
         "town_streets": [{"pts": [[300, 560], [700, 560]], "w": 18}]}   # an avenue 60px from the office
    assert "city_ministries_front_a_street" not in f(M)


def test_city_streets_no_intersection_stub_fires_on_a_short_overshoot():
    # a vertical street crosses a horizontal one and then stops 25px past it - a dangling stub
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]],
         "town_streets": [{"pts": [[300, 500], [700, 500]], "w": 18},     # horizontal cross-street
                          {"pts": [[450, 300], [450, 525]], "w": 18}]}    # crosses at y500, stops at 525 (25px past)
    assert "city_streets_no_intersection_stub" in f(M)


def test_city_streets_no_intersection_stub_passes_when_streets_run_well_past():
    # the same crossing, but the vertical street continues well past (to 700) - a real grid line
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]],
         "town_streets": [{"pts": [[300, 500], [700, 500]], "w": 18},
                          {"pts": [[450, 300], [450, 700]], "w": 18}]}
    assert "city_streets_no_intersection_stub" not in f(M)


def test_population_consistent_with_housing_fires_when_dwellings_too_few():
    # population is dwellings x5, not total buildings x5; 10 dwellings imply ~50 residents, not 3000
    M = {"meta": {"scale": "town", "walled": False, "population": 3000},
         "buildings": [bldg(120 + i * 60, 120, kind="laborer") for i in range(10)]}
    assert "population_consistent_with_housing" in f(M)


def test_businesses_front_streets_fires_when_shops_are_interior():
    M = {"meta": {"scale": "city", "walled": True}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]],
         "town_streets": [{"pts": [[250, 250], [750, 250]], "w": 18}],          # the only street, along the top
         "buildings": [bldg(300 + i * 50, 550, kind="shop") for i in range(6)]}  # shops marooned in the interior
    assert "businesses_front_streets" in f(M)


def test_poor_housing_mostly_interior_fires_when_laborers_on_the_street():
    M = {"meta": {"scale": "city", "walled": True}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]],
         "town_streets": [{"pts": [[250, 500], [750, 500]], "w": 18}],
         "buildings": [bldg(300 + i * 40, 512, kind="laborer") for i in range(8)]}  # all jammed ONTO the street
    assert "poor_housing_mostly_interior" in f(M)


def test_alleys_serve_buildings_fires_on_a_lane_to_nowhere():
    # a 400px alley serving only two dwellings - a lane running off into empty space
    M = {"meta": {"scale": "city", "walled": True}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]],
         "alleys": [{"pts": [[500, 300], [500, 700]], "w": 10}],
         "buildings": [bldg(530, 320, kind="laborer"), bldg(530, 360, kind="laborer")]}
    assert "alleys_serve_buildings" in f(M)


def test_alleys_serve_buildings_fires_on_a_redundant_lane_beside_a_street():
    # an alley laid parallel and CLOSE to a street it duplicates: every dwellling fronts the
    # street (it is nearer), so the alley uniquely serves nothing - a redundant lane. Buildings
    # are within the alley's band but closer to the street, so nearest-lane assignment credits
    # them to the street and the alley reads empty.
    blds = [bldg(330 + i * 40, 415, kind="laborer") for i in range(9)]   # y415: 15px from street, 35px from alley
    M = {"meta": {"scale": "city", "walled": True}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]],
         "town_streets": [{"pts": [[300, 400], [700, 400]], "w": 18}],
         "alleys": [{"pts": [[300, 450], [700, 450]], "w": 10}],   # parallel, 50px south of the street
         "buildings": blds}
    assert "alleys_serve_buildings" in f(M)


def test_no_isolated_dwelling_cluster_fires_on_a_cut_off_block():
    # a 36-house block whose only street is far away - a giant cluster with no street OR alley near it
    blds = [bldg(380 + (i % 6) * 26, 380 + (i // 6) * 26, kind="laborer") for i in range(36)]
    M = {"meta": {"scale": "city", "walled": True}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]],
         "town_streets": [{"pts": [[210, 210], [790, 210]], "w": 18}],   # only street, along the top edge
         "buildings": blds}
    assert "no_isolated_dwelling_cluster" in f(M)


def test_no_isolated_dwelling_cluster_passes_when_an_alley_reaches_it():
    blds = [bldg(380 + (i % 6) * 26, 380 + (i // 6) * 26, kind="laborer") for i in range(36)]
    M = {"meta": {"scale": "city", "walled": True}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]],
         "town_streets": [{"pts": [[210, 210], [790, 210]], "w": 18}],
         "alleys": [{"pts": [[380, 360], [380, 540]], "w": 10}, {"pts": [[510, 360], [510, 540]], "w": 10}],   # alleys lace the block
         "buildings": blds}
    assert "no_isolated_dwelling_cluster" not in f(M)


def test_city_samurai_quarter_gated_fires_when_no_ward_gates():
    M = {"meta": {"scale": "city", "walled": True}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]],
         "governor_mansion": {"x": 600, "y": 600, "w": 120, "h": 90},
         "town_streets": [{"pts": [[400, 600], [800, 600]], "w": 18}],
         "kido": []}   # the quarter has no ward gates
    assert "city_samurai_quarter_gated" in f(M)


def test_city_samurai_quarter_gated_passes_with_two_gates_on_streets():
    M = {"meta": {"scale": "city", "walled": True}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]],
         "governor_mansion": {"x": 600, "y": 600, "w": 120, "h": 90},
         "town_streets": [{"pts": [[400, 600], [800, 600]], "w": 18}, {"pts": [[600, 400], [600, 800]], "w": 18}],
         "kido": [{"x": 500, "y": 600, "horizontal": True}, {"x": 600, "y": 500, "horizontal": False}]}
    assert "city_samurai_quarter_gated" not in f(M)


def test_seg_intersect_parallel_returns_none():
    assert check_village.seg_intersect((0, 0), (10, 0), (0, 5), (10, 5)) is None


def test_city_samurai_ward_sealed_fires_on_ungated_crossing():
    # a street pierces the ward fence with no kido at the crossing - the gate can be walked around
    M = {"meta": {"scale": "city", "walled": True}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]],
         "governor_mansion": {"x": 600, "y": 600, "w": 120, "h": 90},
         "wards": [{"name": "samurai", "boundary": [[400, 800], [400, 400], [800, 400]]}],
         "town_streets": [{"pts": [[300, 500], [700, 500]], "w": 18}],   # crosses the W fence at (400,500)
         "kido": []}
    assert "city_samurai_ward_sealed" in f(M)


def test_city_samurai_ward_sealed_fires_on_open_fence_end():
    # the fence has an end floating in the interior (not abutting the wall) - you walk around it
    M = {"meta": {"scale": "city", "walled": True}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]],
         "governor_mansion": {"x": 600, "y": 600, "w": 120, "h": 90},
         "wards": [{"name": "samurai", "boundary": [[400, 500], [400, 400], [800, 400]]}],   # (400,500) floats
         "town_streets": [], "kido": []}
    assert "city_samurai_ward_sealed" in f(M)


def test_city_torii_over_streets_fires_when_torii_under_street():
    # a torii on the street but with a LOWER draw-z than the street -> the street paints over it
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]],
         "torii": [[500, 500, 50]],                                       # z = 50
         "town_streets": [{"pts": [[300, 500], [700, 500]], "w": 18, "z": 100}]}   # z = 100 > torii -> torii underneath
    assert "city_torii_over_streets" in f(M)


def test_city_temple_approach_has_torii_fires_when_street_runs_up_without_one():
    # a street terminates right at the temple front but there is no torii arch on it
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]],
         "religious": [{"kind": "temple", "label": "T", "x": 500, "y": 500, "w": 100, "h": 80}],
         "town_streets": [{"pts": [[500, 700], [500, 545]], "w": 18}]}    # runs up to the south edge (540)
    assert "city_temple_approach_has_torii" in f(M)


def _torii_fill_city(temple_xy, torii, streets=None, **extra):
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]],
         "religious": [{"kind": "temple", "label": "T", "x": temple_xy[0], "y": temple_xy[1], "w": 100, "h": 80}],
         "torii": [[t[0], t[1], 1] for t in torii]}
    if streets is not None:
        M["town_streets"] = [{"pts": p, "w": 18} for p in streets]
    M.update(extra)
    return M


def test_city_temple_torii_fill_approach_fires_when_room_for_more():
    # one torii on a street running up to the temple, with clear open street beyond - room for more arches
    M = _torii_fill_city((500, 300), [(500, 400)], streets=[[[500, 700], [500, 420]]])
    assert "city_temple_torii_fill_approach" in f(M)


def test_city_temple_torii_fill_approach_passes_when_built_up():
    # the next arch-slot is blocked by a building - the approach is built up, leave it alone
    M = _torii_fill_city((500, 300), [(500, 400)], streets=[[[500, 380], [500, 700]]],
                         buildings=[{"kind": "laborer", "x": 500, "y": 446, "w": 40, "h": 30, "rot": 0}])
    assert "city_temple_torii_fill_approach" not in f(M)


def test_city_temple_torii_fill_approach_ignores_torii_off_any_street():
    # the torii isn't on a street, so there's no clear approach axis to extend - exempt
    M = _torii_fill_city((500, 300), [(500, 400)])
    assert "city_temple_torii_fill_approach" not in f(M)


def test_city_temple_torii_fill_approach_stops_at_the_map_edge():
    M = _torii_fill_city((500, 80), [(500, 40)], streets=[[[500, 60], [500, 10]]])   # next slot runs off the top edge
    assert "city_temple_torii_fill_approach" not in f(M)


def test_city_temple_torii_fill_approach_stops_at_the_wall():
    M = _torii_fill_city((500, 500), [(500, 760)], streets=[[[500, 500], [500, 860]]])   # next slot is outside the rampart
    assert "city_temple_torii_fill_approach" not in f(M)


def test_city_temple_torii_fill_approach_stops_at_a_field():
    fld = {"name": "f", "kind": "dry", "bbox": [470, 420, 530, 480], "outline": [[470, 420], [530, 420], [530, 480], [470, 480]]}
    M = _torii_fill_city((500, 300), [(500, 400)], streets=[[[500, 380], [500, 700]]], fields=[fld])
    assert "city_temple_torii_fill_approach" not in f(M)


def test_city_temples_clear_of_wall_branches():
    # three temples hitting the three footprint-vs-barrier paths: A contains a wall vertex
    # (point_in_poly), B is crossed by a wall edge (segments_cross), C's corner sits on it (seg_dist)
    rel = [{"kind": "temple", "label": "A", "x": 500, "y": 500, "w": 200, "h": 200},
           {"kind": "temple", "label": "B", "x": 300, "y": 500, "w": 16, "h": 300},
           {"kind": "temple", "label": "C", "x": 200, "y": 500, "w": 40, "h": 8}]
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
         "wall": [[100, 500], [500, 500], [900, 500]], "gates": [[500, 500], [500, 800]], "religious": rel}
    assert "city_temples_clear_of_wall_moat" in f(M)


def test_city_government_clear_of_wall_moat_fires():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]],
         "governor_mansion": {"x": 800, "y": 500, "w": 120, "h": 90, "label": "Gov"}}   # straddles the right wall edge
    assert "city_government_clear_of_wall_moat" in f(M)


def test_city_streets_clear_of_wall_fires():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]],
         "town_streets": [{"pts": [[500, 500], [990, 500]], "w": 18}]}   # a vertex outside the wall
    assert "city_streets_clear_of_wall" in f(M)


def test_city_streets_clear_of_moat_fires_on_alley():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]], "moat": [[150, 150], [850, 150], [850, 850], [150, 850], [150, 150]],
         "town_streets": [], "alleys": [{"pts": [[500, 700], [500, 900]], "w": 10}]}   # alley crosses the moat ring
    assert "city_streets_clear_of_moat" in f(M)


def test_no_structure_on_street_fires_on_alley_over_building():
    M = {"meta": {"scale": "town", "walled": False}, "wall": WALL,
         "alleys": [{"pts": [[400, 500], [600, 500]], "w": 10}],
         "buildings": [bldg(500, 500, kind="laborer")]}   # the alley runs straight over the dwelling
    assert "no_structure_on_street" in f(M)


def test_city_fields_clear_of_wall_moat_fires():
    ff = {"name": "ff", "kind": "paddy", "bbox": [700, 400, 900, 600],
          "outline": [[700, 400], [900, 400], [900, 600], [700, 600]]}   # straddles the right wall edge
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]], "fields": [ff]}
    assert "city_fields_clear_of_wall_moat" in f(M)


def test_city_governor_mansion_large_fires_when_small():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]],
         "governor_mansion": {"x": 500, "y": 500, "w": 80, "h": 60, "label": "Gov"},   # tiny
         "manors": [{"x": 990, "y": 990, "w": 200, "h": 150}]}   # an estate grander than the governor
    assert "city_governor_mansion_large" in f(M)


def test_city_ministries_cluster_fires_on_stray_ministry():
    M = {"meta": {"scale": "city", "walled": True, "W": 2000, "H": 2000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]],
         "governor_mansion": {"x": 500, "y": 500, "w": 200, "h": 150, "label": "Gov"},
         "ministries": [{"x": 1800, "y": 1800, "w": 80, "h": 50, "name": "Ministry of War"}]}   # far from the yamen
    assert "city_ministries_cluster_at_government" in f(M)


def test_city_estates_in_southeast_fires_on_northwest_estate():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]], "manors": [{"x": 60, "y": 60, "w": 100, "h": 80}]}   # NW, not SE
    assert "city_estates_in_southeast" in f(M)


def test_view_treats_the_crop_as_the_map_edge():
    # the Imperial road must run off the map edge through both gates. With a cropped city view,
    # "the edge" is the view, not the full canvas - a road that exits the view (but not the
    # canvas) counts as running through.
    base = {"meta": {"scale": "city", "walled": True, "W": 3000, "H": 2000},
            "wall": [[1300, 300], [1700, 300], [1700, 1700], [1300, 1700]],
            "gates": [[1500, 300], [1500, 1700]],
            "road": [[1500, 250], [1500, 1750]]}    # exits y250..1750, well inside the 0..2000 canvas
    assert "city_imperial_road_through" in f(base)                       # no view: road stops short of the canvas edge
    base["meta"]["view"] = [1250, 280, 500, 1440]                        # crop to y280..1720
    assert "city_imperial_road_through" not in f(base)                   # road now exits the view -> runs through


def test_city_pond_clear_of_wall_moat_fires():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]], "pond": [800, 500, 60, 40]}   # ellipse straddling the right wall edge
    assert "city_pond_clear_of_wall_moat" in f(M)


def test_city_civic_clear_of_streets_fires():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]],
         "ministries": [{"x": 500, "y": 500, "w": 90, "h": 60, "name": "Ministry of War"}],
         "town_streets": [{"pts": [[300, 500], [700, 500]], "w": 20}]}   # the street runs through the ministry
    assert "city_civic_clear_of_streets" in f(M)


def test_city_temples_inside_walls_fires_on_outside_temple():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]],
         "religious": [{"kind": "temple", "label": "T", "x": 990, "y": 500, "w": 60, "h": 40}]}
    assert "city_temples_inside_walls" in f(M)


def test_city_estates_overlap_and_barrier_fire():
    est = [{"x": 810, "y": 500, "w": 80, "h": 60}, {"x": 822, "y": 512, "w": 80, "h": 60}]   # overlap + on the wall edge
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]], "manors": est}
    fails = f(M)
    assert "city_estates_no_overlap" in fails
    assert "city_estates_clear_of_wall_moat" in fails


def test_city_outside_field_and_gate_market_fire():
    ff = {"name": "ff", "kind": "paddy", "bbox": [1500, 1500, 1800, 1800],
          "outline": [[1500, 1500], [1800, 1500], [1800, 1800], [1500, 1800]]}
    M = {"meta": {"scale": "city", "walled": True, "W": 2000, "H": 2000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]], "fields": [ff]}
    fails = f(M)
    assert "city_outside_fields_have_farmhouses" in fails
    assert "city_fields_close_to_city" in fails
    assert "city_has_gate_market" in fails


def test_city_gate_guardhouse_and_moat_irrigation_fire():
    bigf = {"name": "bf", "kind": "paddy", "bbox": [960, 200, 1180, 900],
            "outline": [[960, 200], [1180, 200], [1180, 900], [960, 900]]}
    M = {"meta": {"scale": "city", "walled": True, "W": 1300, "H": 1100},
         "wall": [[100, 100], [900, 100], [900, 900], [100, 900]], "gates": [[500, 100], [500, 900]],
         "moat": [[80, 80], [920, 80], [920, 920], [80, 920], [80, 80]], "fields": [bigf]}
    fails = f(M)
    assert "city_gate_has_guardhouse" in fails        # no gate structures
    assert "city_moat_irrigates_fields" in fails       # big outside field, no channel feeds it


def test_city_no_inwall_farms_fires_without_agricultural_district():
    # a field whose centroid sits inside the wall, and no meta(agricultural_district=True)
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
         "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "fields": [_field("f", 400, 400, 600, 600)]}
    assert "city_no_inwall_farms" in f(M)


def test_city_no_inwall_farms_allowed_with_agricultural_district():
    M = {"meta": {"scale": "city", "walled": True, "agricultural_district": True, "W": 1000, "H": 1000},
         "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "fields": [_field("f", 400, 400, 600, 600)]}
    assert "city_no_inwall_farms" not in f(M)


def test_city_moat_checks_fire_when_moat_neither_surrounds_nor_is_fed():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]], "moat": [[400, 400], [600, 400], [600, 600], [400, 600]]}
    fails = f(M)
    assert "city_moat_surrounds_wall" in fails     # a tiny moat INSIDE the wall does not encircle it
    assert "city_moat_fed_offmap" in fails          # no stream feeds it


_MOAT = [[160, 160], [840, 160], [840, 840], [160, 840], [160, 160]]   # encircles WALLSQ (200-800)


def _feeder_city(stream_w):
    return {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
            "gates": [[500, 200], [500, 800]], "moat": _MOAT, "moat_width": 22,
            "streams": [{"poly": [[80, 500], [165, 500]], "frm": None, "to": None, "w": stream_w}]}


def test_city_moat_feeder_matches_width_fires_when_narrow():
    # a 9px trickle reaching a 22px moat - too thin to keep it supplied
    assert "city_moat_feeder_matches_width" in f(_feeder_city(9))


def test_city_moat_feeder_matches_width_passes_when_matched():
    assert "city_moat_feeder_matches_width" not in f(_feeder_city(22))


# --- settlement wells (town/village/hamlet water access) ---
def _rural(scale, houses, wells, **extra):
    M = {"meta": {"scale": scale}, "houses": [{"x": x, "y": y, "w": 40, "h": 28, "rot": 0, "kind": "plain"} for (x, y) in houses],
         "wells": [{"x": x, "y": y, "r": 8} for (x, y) in wells]}
    M.update(extra)
    return M


def test_settlement_has_wells_fires_when_too_few():
    # 40 farm households, no wells at all
    assert "settlement_has_wells" in f(_rural("village", [(300 + i * 10, 300) for i in range(40)], []))


def test_settlement_dwellings_watered_fires_when_a_house_is_dry():
    # one house 600px from the only well, with no irrigation nearby
    assert "settlement_dwellings_watered" in f(_rural("village", [(300, 300), (300, 900)], [(300, 300)]))


def test_settlement_dwellings_watered_passes_via_irrigation():
    # the far house has no well within reach but sits beside a stream
    M = _rural("hamlet", [(300, 900)], [(300, 300)], streams=[{"poly": [[200, 880], [400, 880]], "frm": None, "to": None, "w": 9}])
    assert "settlement_dwellings_watered" not in f(M)


def test_wells_among_dwellings_fires_on_a_stray_well():
    # a well far out in open country, no house beside it
    assert "wells_among_dwellings" in f(_rural("village", [(300, 300)], [(900, 900)]))


def test_wells_among_dwellings_passes_when_beside_a_house():
    assert "wells_among_dwellings" not in f(_rural("village", [(300, 300)], [(340, 300)]))


def _well_size_city(vr):
    # two 44px farmhouses with a well of drawn radius `vr` beside them
    return {"meta": {"scale": "village"},
            "houses": [{"x": 300, "y": 300, "w": 44, "h": 29, "rot": 0, "kind": "plain"},
                       {"x": 344, "y": 300, "w": 44, "h": 29, "rot": 0, "kind": "plain"}],
            "wells": [{"x": 322, "y": 300, "r": 8, "vr": vr}]}


def test_wells_sized_to_buildings_fires_when_too_small():
    # a 10px wellhead (the dense-city size) beside 44px village farmhouses - far too small
    assert "wells_sized_to_buildings" in f(_well_size_city(5.0))


def test_wells_sized_to_buildings_passes_when_proportional():
    # scaled to the village grain (~24px), about half a farmhouse
    assert "wells_sized_to_buildings" not in f(_well_size_city(11.9))


# --- bridges where a road crosses water ---
def _bridge_map(bridges):
    # a country road (E-W) crossing a stream (N-S) at (500, 500); `bridges` is the recorded list
    return {"meta": {"scale": "village", "W": 1000, "H": 1000},
            "road": [[100, 500], [900, 500]],
            "streams": [{"poly": [[500, 100], [500, 900]], "frm": None, "to": None, "w": 9}],
            "bridges": bridges}


def test_roads_bridge_water_fires_when_unbridged():
    # the road runs straight through the stream with no bridge
    assert "roads_bridge_water" in f(_bridge_map([]))


def test_roads_bridge_water_passes_when_bridged():
    assert "roads_bridge_water" not in f(_bridge_map([{"x": 500, "y": 500, "rot": 0, "span": 37, "w": 26}]))


def test_seg_intersect_returns_point_for_a_crossing_and_none_for_parallel():
    # the geometry helper that bridges() uses to find the crossing point
    p = settlement.seg_intersect((0, 0), (10, 0), (5, -5), (5, 5))
    assert p == (5.0, 0.0)
    assert settlement.seg_intersect((0, 0), (10, 0), (0, 4), (10, 4)) is None   # parallel - no crossing
    assert settlement.segments_cross((0, 0), (10, 0), (5, -5), (5, 5))
    assert not settlement.segments_cross((0, 0), (10, 0), (0, 4), (10, 4))


def test_roads_bridge_water_passes_when_road_runs_alongside_water():
    # a road parallel to a stream, never intersecting it, needs no bridge
    M = {"meta": {"scale": "village", "W": 1000, "H": 1000},
         "road": [[100, 480], [900, 480]],
         "streams": [{"poly": [[100, 520], [900, 520]], "frm": None, "to": None, "w": 9}],
         "bridges": []}
    assert "roads_bridge_water" not in f(M)


# --- harvest processing (per-farmstead threshing/drying yards) ---
_PADDY_SQ = [[400, 400], [600, 400], [600, 600], [400, 600]]


def _harvest(houses, yards, fields=None):
    M = {"meta": {"scale": "village"},
         "houses": [{"x": x, "y": y, "w": 40, "h": 28, "rot": 0, "kind": "plain"} for (x, y) in houses],
         "wells": [{"x": x, "y": y, "r": 8, "vr": 11.9} for (x, y) in houses],   # a well by each house so the water checks pass
         "threshing_yards": yards}
    if fields:
        M["fields"] = fields
    return M


def _yard(of, dx=44, dy=0, w=32, h=20):
    # a small yard beside the farmhouse at `of`, recording its parent farmhouse centre
    return {"x": of[0] + dx, "y": of[1] + dy, "w": w, "h": h, "rot": 0, "of": [of[0], of[1]]}


_SIX = [(300, 300), (380, 300), (460, 300), (540, 300), (620, 300), (700, 300)]   # the work yard is UNIVERSAL: need all 6


def test_harvest_yards_present_fires_when_any_farmhouse_lacks_one():
    # 5 of 6 yards - even one farmhouse without a yard fails (the work yard was universal)
    assert "harvest_yards_present" in f(_harvest(_SIX, [_yard(h) for h in _SIX[:5]]))


def test_harvest_yards_present_passes_when_every_farmhouse_has_one():
    assert "harvest_yards_present" not in f(_harvest(_SIX, [_yard(h) for h in _SIX]))


def test_harvest_yards_smaller_than_farmhouse_fires_when_oversize():
    assert "harvest_yards_smaller_than_farmhouse" in f(_harvest([(300, 300)], [_yard((300, 300), w=60, h=44)]))


def test_harvest_yards_smaller_than_farmhouse_passes_when_small():
    assert "harvest_yards_smaller_than_farmhouse" not in f(_harvest([(300, 300)], [_yard((300, 300))]))


def test_harvest_yards_on_sunny_side_fires_when_north_of_house():
    # +y is south; a yard ABOVE its house centre sits on the shady north/back side
    y = {"x": 300, "y": 260, "w": 32, "h": 20, "rot": 0, "of": [300, 300]}
    assert "harvest_yards_on_sunny_side" in f(_harvest([(300, 300)], [y]))


def test_harvest_yards_on_sunny_side_passes_when_south_of_house():
    y = {"x": 300, "y": 340, "w": 32, "h": 20, "rot": 0, "of": [300, 300]}
    assert "harvest_yards_on_sunny_side" not in f(_harvest([(300, 300)], [y]))


def test_harvest_yards_clear_of_paddies_fires_when_in_a_paddy():
    # the yard footprint sits inside the field (400,400)-(600,600) - a dry floor in the flooded paddy
    y = {"x": 500, "y": 500, "w": 32, "h": 20, "rot": 0, "of": [460, 460]}
    M = _harvest([(460, 460)], [y], fields=[{"name": "a", "kind": "paddy", "bbox": [400, 400, 600, 600], "outline": _PADDY_SQ}])
    assert "harvest_yards_clear_of_paddies" in f(M)


def test_harvest_yards_clear_of_paddies_passes_when_clear():
    y = {"x": 720, "y": 300, "w": 32, "h": 20, "rot": 0, "of": [676, 300]}
    M = _harvest([(676, 300)], [y], fields=[{"name": "a", "kind": "paddy", "bbox": [400, 400, 600, 600], "outline": _PADDY_SQ}])
    assert "harvest_yards_clear_of_paddies" not in f(M)


def test_harvest_yards_clear_of_structures_fires_on_another_building():
    # the yard (344,300) overlaps a shop - only its OWN farmhouse (300,300) may underlie it
    M = _harvest([(300, 300)], [_yard((300, 300))])
    M["buildings"] = [{"x": 352, "y": 300, "w": 44, "h": 30, "rot": 0, "kind": "shop"}]
    assert "harvest_yards_clear_of_structures" in f(M)


def test_harvest_yards_clear_of_structures_passes_when_only_on_its_own_house():
    M = _harvest([(300, 300)], [_yard((300, 300))])
    M["buildings"] = [{"x": 700, "y": 700, "w": 44, "h": 30, "rot": 0, "kind": "shop"}]   # far away
    assert "harvest_yards_clear_of_structures" not in f(M)


# --- waterways merge at crossings (confluence layering) ---
def _confluence(ch_bedz):
    # a stream (bed+sheen) crossed by a channel; ch_bedz is the channel's bed draw position
    return {"meta": {"scale": "village"},
            "streams": [{"poly": [[100, 500], [900, 500]], "frm": None, "to": None, "w": 9, "bedz": 10, "sheenz": 20}],
            "channels": [{"poly": [[500, 100], [500, 900]], "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}, "bedz": ch_bedz}]}


def test_waterways_merge_at_crossings_fires_when_bed_over_sheen():
    # the channel bed is drawn AFTER the stream sheen (the old per-course order) - an opaque bed cuts it
    assert "waterways_merge_at_crossings" in f(_confluence(25))


def test_waterways_merge_at_crossings_passes_when_beds_below_sheens():
    assert "waterways_merge_at_crossings" not in f(_confluence(11))


def test_waterways_merge_at_crossings_passes_when_no_crossing():
    M = _confluence(25)
    M["channels"][0]["poly"] = [[500, 100], [500, 300]]   # stops short, never reaches the stream
    assert "waterways_merge_at_crossings" not in f(M)


def test_waterways_merge_at_crossings_passes_when_neither_has_sheen():
    # two channels crossing - same-colour beds merge regardless of order, no sheen to cut
    M = {"meta": {"scale": "village"},
         "channels": [{"poly": [[100, 500], [900, 500]], "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}, "bedz": 30},
                      {"poly": [[500, 100], [500, 900]], "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}, "bedz": 10}]}
    assert "waterways_merge_at_crossings" not in f(M)


def test_waterways_merge_at_crossings_fires_at_a_feeder_junction():
    # a channel FEEDS INTO a stream (its endpoint sits on it), drawn over the stream's sheen
    M = {"meta": {"scale": "village"},
         "streams": [{"poly": [[100, 500], [900, 500]], "frm": None, "to": None, "w": 9, "bedz": 10, "sheenz": 20}],
         "channels": [{"poly": [[500, 505], [500, 900]], "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}, "bedz": 25}]}
    assert "waterways_merge_at_crossings" in f(M)


def test_waterways_merge_at_crossings_fires_when_stream_ends_on_a_channel():
    # the stream's own endpoint sits on a channel (the pa-endpoint junction branch)
    M = {"meta": {"scale": "village"},
         "streams": [{"poly": [[505, 500], [900, 500]], "frm": None, "to": None, "w": 9, "bedz": 25, "sheenz": 30}],
         "channels": [{"poly": [[500, 100], [500, 900]], "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}, "bedz": 10, "sheenz": 5}]}
    assert "waterways_merge_at_crossings" in f(M)


# --- the dead (cemeteries) ---
_MON = [{"kind": "monastery", "x": 500, "y": 500, "w": 120, "h": 80}]
_SHR = [{"kind": "shrine", "x": 500, "y": 500, "w": 100, "h": 68}]


def _dead(scale, cems, religious=None):
    M = {"meta": {"scale": scale}, "cemeteries": cems}
    if religious is not None:
        M["religious"] = religious
    return M


def test_settlement_has_cemetery_fires_when_missing():
    assert "settlement_has_cemetery" in f(_dead("village", []))


def test_settlement_has_cemetery_exempts_hamlet():
    assert "settlement_has_cemetery" not in f(_dead("hamlet", []))


def test_settlement_has_cemetery_passes_when_present():
    assert "settlement_has_cemetery" not in f(_dead("village", [{"x": 300, "y": 300, "w": 80, "h": 56, "rot": 0}]))


def test_cemetery_clear_of_shrine_fires_when_adjacent():
    # a graveyard hard against a Shinto shrine - kegare/death-pollution
    assert "cemetery_clear_of_shrine" in f(_dead("village", [{"x": 540, "y": 520, "w": 80, "h": 56, "rot": 0}], religious=_SHR))


def test_cemetery_clear_of_shrine_passes_when_far():
    assert "cemetery_clear_of_shrine" not in f(_dead("village", [{"x": 900, "y": 900, "w": 80, "h": 56, "rot": 0}], religious=_SHR))


def test_cemetery_in_temple_precinct_fires_when_far_from_hall():
    assert "cemetery_in_temple_precinct" in f(_dead("town", [{"x": 1500, "y": 1500, "w": 80, "h": 56, "rot": 0}], religious=_MON))


def test_cemetery_in_temple_precinct_passes_when_by_hall():
    assert "cemetery_in_temple_precinct" not in f(_dead("town", [{"x": 560, "y": 520, "w": 80, "h": 56, "rot": 0}], religious=_MON))


def test_mausoleum_draws_with_either_gate_orientation():
    # exercises both the horizontal-wall (south) and vertical-wall (west) gate branches + the default
    # (above) label position
    s = settlement.Settlement()
    s.mausoleum(900, 900, 120, 90, label="Mausoleum", gate_dir="south")
    s.mausoleum(600, 600, 120, 90, gate_dir="west")
    assert len(s.M["mausoleums"]) == 2


def test_cemetery_clear_of_shrine_fires_on_a_mausoleum_by_a_shrine():
    # the kegare rule covers MAUSOLEA too, not just graveyards
    M = {"meta": {"scale": "village"}, "mausoleums": [{"x": 540, "y": 520, "w": 74, "h": 58, "rot": 0}],
         "religious": [{"kind": "shrine", "x": 500, "y": 500, "w": 100, "h": 68}]}
    assert "cemetery_clear_of_shrine" in f(M)


# --- the full city funerary geography ---
def _city_dead(**kw):
    WALLSQ = [[200, 200], [800, 200], [800, 800], [200, 800]]   # inside = 200..800
    d = dict(cems=[(300, 300), (700, 300), (100, 100)],         # 2 inside + 1 outside
             temples=[(320, 320, "A", True), (680, 320, "B", True)],
             maus=[(520, 520)], crem=[(100, 900)], oss=[(140, 900)], gov=(500, 500), shrines=[])
    d.update(kw)

    def _cem(c):
        x, y = c[0], c[1]
        if len(c) >= 4:
            w, h = c[2], c[3]
        else:                                              # outside cemeteries default bigger than inside
            outside = not (200 < x < 800 and 200 < y < 800)
            w, h = (104, 74) if outside else (70, 50)
        parish = c[4] if len(c) >= 5 else True
        return {"x": x, "y": y, "w": w, "h": h, "rot": 0, "parish": parish}
    return {"meta": {"scale": "city"}, "wall": WALLSQ,
            "cemeteries": [_cem(c) for c in d["cems"]],
            "mausoleums": [{"x": x, "y": y, "w": 74, "h": 58, "rot": 0} for (x, y) in d["maus"]],
            "cremation_grounds": [{"x": x, "y": y, "w": 116, "h": 80, "rot": 0} for (x, y) in d["crem"]],
            "ossuaries": [{"x": x, "y": y, "w": 92, "h": 60, "rot": 0} for (x, y) in d["oss"]],
            "religious": [{"kind": "temple", "x": tx, "y": ty, "w": 80, "h": 60, "label": lbl, "graveyard": gv}
                          for (tx, ty, lbl, gv) in d["temples"]]
                         + [{"kind": "small_shrine", "x": sx, "y": sy, "w": 30, "h": 24} for (sx, sy) in d["shrines"]],
            "governor_mansion": {"x": d["gov"][0], "y": d["gov"][1], "w": 120, "h": 90} if d["gov"] else None}


def test_city_graveyard_count_fires_when_too_few():
    assert "city_graveyard_count" in f(_city_dead(cems=[(300, 300)]))


def test_city_graveyard_count_fires_when_too_many():
    assert "city_graveyard_count" in f(_city_dead(cems=[(300, 300), (350, 300), (400, 300), (700, 300), (100, 100)]))


def test_city_graveyard_count_passes_at_three():
    assert "city_graveyard_count" not in f(_city_dead())


def test_walled_graveyards_inside_and_outside_fires_when_all_inside():
    assert "walled_graveyards_inside_and_outside" in f(_city_dead(cems=[(300, 300), (700, 300)]))


def test_walled_graveyards_inside_and_outside_passes_when_mixed():
    assert "walled_graveyards_inside_and_outside" not in f(_city_dead())


def test_walled_exterior_cemetery_larger_fires_when_not_larger():
    # the outside common ground is no bigger than the cramped intramural one
    assert "walled_exterior_cemetery_larger" in f(_city_dead(cems=[(300, 300), (700, 300), (100, 100, 60, 40)]))


def test_walled_exterior_cemetery_larger_passes_when_larger():
    assert "walled_exterior_cemetery_larger" not in f(_city_dead())


def test_cemetery_in_temple_precinct_exempts_a_nonparish_grave():
    # an inside graveyard far from any temple is exempt when parish=False (a non-parish plot)
    assert "cemetery_in_temple_precinct" not in f(_city_dead(cems=[(300, 300), (700, 300), (100, 100), (500, 500, 60, 44, False)]))


def test_cemetery_in_temple_precinct_fires_on_an_inside_parish_grave_off_temple():
    assert "cemetery_in_temple_precinct" in f(_city_dead(cems=[(300, 300), (700, 300), (100, 100), (500, 500, 60, 44, True)]))


def _water_grave(water):
    M = {"meta": {"scale": "village"}, "cemeteries": [{"x": 300, "y": 300, "w": 60, "h": 44, "rot": 0, "parish": True}]}
    M.update(water)
    return M


def test_funerary_set_back_from_water_fires_near_a_stream():
    assert "funerary_set_back_from_water" in f(_water_grave({"streams": [{"poly": [[300, 340], [600, 340]], "frm": None, "to": None, "w": 9}]}))


def test_funerary_set_back_from_water_fires_near_a_pond():
    assert "funerary_set_back_from_water" in f(_water_grave({"pond": [400, 300, 60, 40]}))


def test_funerary_set_back_from_water_passes_when_clear_of_water():
    assert "funerary_set_back_from_water" not in f(_water_grave({"streams": [{"poly": [[300, 600], [600, 600]], "frm": None, "to": None, "w": 9}],
                                                                 "pond": [900, 900, 60, 40]}))


def test_water_setback_scales_with_waterway_width():
    assert check_village.water_setback(4) == 75            # any small open water -> the floor (graves flood out)
    assert check_village.water_setback(9) == 75            # a narrow stream still gets the full floor
    assert check_village.water_setback(22) == 110          # moat -> moderate/large
    assert check_village.water_setback(40) == 140          # river / canal -> capped
    assert check_village.water_setback(9) < check_village.water_setback(22)   # wider water, more set-back


def test_funerary_set_back_scales_grave_ok_by_a_stream_fails_by_a_moat():
    # a graveyard whose nearest corner is 90px from the watercourse: fine by a narrow stream (floor 75),
    # too close to a moat (set-back 110)
    def M(width):
        return {"meta": {"scale": "village"},
                "cemeteries": [{"x": 300, "y": 270, "w": 50, "h": 36, "rot": 0, "parish": True}],
                "streams": [{"poly": [[200, 378], [600, 378]], "frm": None, "to": None, "w": width}]}
    assert "funerary_set_back_from_water" not in f(M(6))    # narrow stream: floor 75, corner 90px away -> ok
    assert "funerary_set_back_from_water" in f(M(22))       # moat-width: set-back 110 -> 90px too close


def test_funerary_set_back_cremation_may_sit_nearer_than_a_grave():
    # at the SAME 50px corner distance from a wide watercourse: the cremation ground passes, a graveyard fires
    base = {"meta": {"scale": "village"}, "streams": [{"poly": [[200, 378], [600, 378]], "frm": None, "to": None, "w": 22}]}
    grave = {**base, "cemeteries": [{"x": 300, "y": 310, "w": 50, "h": 36, "rot": 0, "parish": True}]}
    crem = {**base, "cremation_grounds": [{"x": 300, "y": 288, "w": 116, "h": 80, "rot": 0}]}
    assert "funerary_set_back_from_water" in f(grave)
    assert "funerary_set_back_from_water" not in f(crem)


def test_funerary_set_back_inside_wall_grave_exempt_from_moat():
    # a graveyard just inside the wall is shielded from the (outside) moat by the rampart -> exempt
    WALLSQ = [[200, 200], [800, 200], [800, 800], [200, 800]]
    M = {"meta": {"scale": "city"}, "wall": WALLSQ, "moat": _MOAT, "moat_width": 22,
         "cemeteries": [{"x": 230, "y": 500, "w": 50, "h": 36, "rot": 0, "parish": True}]}
    assert "funerary_set_back_from_water" not in f(M)


def test_funerary_set_back_outside_wall_grave_subject_to_moat():
    WALLSQ = [[200, 200], [800, 200], [800, 800], [200, 800]]
    M = {"meta": {"scale": "city"}, "wall": WALLSQ, "moat": _MOAT, "moat_width": 22,
         "cemeteries": [{"x": 120, "y": 500, "w": 50, "h": 36, "rot": 0, "parish": True}]}
    assert "funerary_set_back_from_water" in f(M)


_PADDY = {"name": "a", "kind": "paddy", "bbox": [300, 330, 500, 500],
          "outline": [[300, 330], [500, 330], [500, 500], [300, 500]]}


def test_funerary_set_back_fires_near_a_rice_paddy():
    # a burial ground hard against a flood-prone paddy edge
    M = {"meta": {"scale": "village"}, "fields": [_PADDY],
         "cemeteries": [{"x": 300, "y": 300, "w": 50, "h": 36, "rot": 0, "parish": True}]}
    assert "funerary_set_back_from_water" in f(M)


def test_funerary_set_back_paddy_needs_more_than_creek_distance():
    # ~35px from a paddy edge: fine for a creek, but a flooded paddy needs a real margin -> still fires
    near = {"meta": {"scale": "village"}, "fields": [_PADDY],
            "cemeteries": [{"x": 300, "y": 277, "w": 50, "h": 36, "rot": 0, "parish": True}]}   # corner ~35px from the paddy
    assert "funerary_set_back_from_water" in f(near)
    far = {"meta": {"scale": "village"}, "fields": [_PADDY],
           "cemeteries": [{"x": 300, "y": 255, "w": 50, "h": 36, "rot": 0, "parish": True}]}    # corner ~57px -> clear
    assert "funerary_set_back_from_water" not in f(far)


def test_funerary_set_back_cremation_may_sit_by_a_paddy():
    # the cremation ground is exempt from the paddy set-back (a fire site, not flood-sensitive graves)
    M = {"meta": {"scale": "village"}, "fields": [_PADDY],
         "cremation_grounds": [{"x": 300, "y": 280, "w": 116, "h": 80, "rot": 0}]}
    assert "funerary_set_back_from_water" not in f(M)


def _city_estates(gate_dirs):
    WALLSQ = [[200, 200], [800, 200], [800, 800], [200, 800]]   # estates sit OUTSIDE, to the SE
    return {"meta": {"scale": "city", "walled": True}, "wall": WALLSQ,
            "manors": [{"x": 900 + (i % 3) * 220, "y": 900 + (i // 3) * 220, "w": 120, "h": 90, "gate_dir": gd}
                       for i, gd in enumerate(gate_dirs)]}


def test_city_estate_gates_vary_fires_when_all_identical():
    assert "city_estate_gates_vary" in f(_city_estates(["west"] * 5))


def test_city_estate_gates_vary_passes_when_mixed():
    assert "city_estate_gates_vary" not in f(_city_estates(["south", "west", "north", "south", "west"]))


def test_every_feature_classified_for_overlap_fires_on_unknown_feature():
    # a new footprint feature nobody added to the _OVERLAP_* registry trips the completeness guard
    M = {"meta": {"scale": "village"}, "watchtowers": [{"x": 100, "y": 100, "w": 20, "h": 20, "rot": 0}]}
    assert "every_feature_classified_for_overlap" in f(M)


def test_every_feature_classified_for_overlap_passes_for_known_features():
    M = {"meta": {"scale": "village"}, "houses": [{"x": 100, "y": 100, "w": 20, "h": 20, "rot": 0, "kind": "plain"}]}
    assert "every_feature_classified_for_overlap" not in f(M)


# --- town_has_caravan_inn -------------------------------------------------------------------------
def _town_caravan(inn=True, stables=True, walled=False, inn_xy=(500, 500), st_xy=(500, 560)):
    M = {"meta": {"scale": "town", "walled": walled}, "houses": [], "fields": [], "buildings": []}
    if inn:
        M["buildings"].append({"x": inn_xy[0], "y": inn_xy[1], "w": 66, "h": 48, "kind": "inn", "rot": 0})
    if stables:
        M["buildings"].append({"x": st_xy[0], "y": st_xy[1], "w": 92, "h": 44, "kind": "stables", "rot": 0})
    if walled:
        M["wall"] = [[100, 100], [2000, 100], [2000, 2000], [100, 2000]]
    return M


def test_town_has_caravan_inn_passes_with_inn_stables_open_ground():
    assert "town_has_caravan_inn" not in f(_town_caravan())


def test_town_has_caravan_inn_fires_without_stables():
    assert "town_has_caravan_inn" in f(_town_caravan(stables=False))


def test_town_has_caravan_inn_fires_when_outside_the_walls():
    assert "town_has_caravan_inn" in f(_town_caravan(walled=True, inn_xy=(40, 40), st_xy=(40, 100)))


def test_town_has_caravan_inn_fires_when_stables_hemmed_in():
    # the stables needs open ground (a pasture) - >4 dwellings crowding it fails
    M = _town_caravan()
    M["buildings"] += [{"x": 500 + i * 8, "y": 560, "w": 20, "h": 16, "kind": "laborer", "rot": 0} for i in range(5)]
    assert "town_has_caravan_inn" in f(M)


def test_town_has_caravan_inn_passes_when_inn_fronts_road():
    M = _town_caravan(inn_xy=(500, 560), st_xy=(500, 640))
    M["road"] = [[100, 500], [900, 500]]   # the inn (y560) fronts the road (y500), nothing between
    assert "town_has_caravan_inn" not in f(M)


def test_town_has_caravan_inn_fires_when_inn_behind_shops():
    M = _town_caravan(inn_xy=(500, 560), st_xy=(500, 640))
    M["road"] = [[100, 500], [900, 500]]
    M["buildings"].append({"x": 500, "y": 525, "w": 60, "h": 30, "kind": "merchant", "rot": 0})  # a shop between inn and road
    assert "town_has_caravan_inn" in f(M)


def test_town_has_caravan_inn_fires_when_inn_far_from_any_road():
    M = _town_caravan(inn_xy=(500, 560), st_xy=(500, 640))
    M["road"] = [[100, 200], [900, 200]]   # the road is far away - the inn is not along it
    assert "town_has_caravan_inn" in f(M)


def test_inn_faces_the_road_fires_when_back_to_the_road():
    # inn at rot 0 (noren faces south) but the road is to its NORTH -> back to the road
    M = _town_caravan(inn_xy=(500, 560), st_xy=(500, 640))
    M["road"] = [[100, 500], [900, 500]]
    assert "inn_faces_the_road" in f(M)


def test_inn_faces_the_road_passes_when_facing():
    M = _town_caravan(inn_xy=(500, 560), st_xy=(500, 640))
    M["road"] = [[100, 500], [900, 500]]
    M["buildings"][0]["rot"] = 180   # the inn (buildings[0]) turns its noren north, toward the road
    assert "inn_faces_the_road" not in f(M)


# --- compass_clear (the N/S compass overlay must sit in empty space) ------------------------------
def test_compass_clear_passes_in_an_empty_corner():
    M = {"meta": {"scale": "village"}, "compass": {"x": 1700, "y": 100},
         "houses": [{"x": 300, "y": 300, "w": 30, "h": 20, "rot": 0, "kind": "plain"}]}
    assert "compass_clear" not in f(M)


def test_compass_clear_fires_over_a_building():
    M = {"meta": {"scale": "village"}, "compass": {"x": 300, "y": 300},
         "houses": [{"x": 300, "y": 300, "w": 40, "h": 30, "rot": 0, "kind": "plain"}]}
    assert "compass_clear" in f(M)


def test_compass_clear_fires_over_a_road():
    M = {"meta": {"scale": "village"}, "compass": {"x": 300, "y": 300}, "road": [[100, 300], [900, 300]], "road_width": 26}
    assert "compass_clear" in f(M)


def test_compass_clear_fires_over_terrain():
    M = {"meta": {"scale": "village"}, "compass": {"x": 300, "y": 300},
         "fields": [{"outline": [[260, 260], [340, 260], [340, 340], [260, 340]], "bbox": [260, 260, 340, 340], "name": "a", "kind": "paddy"}]}
    assert "compass_clear" in f(M)


def test_compass_clear_fires_over_a_label():
    M = {"meta": {"scale": "village"}, "compass": {"x": 300, "y": 300},
         "labels": [[280, 290, 380, 310, 5, "somewhere"]]}
    assert "compass_clear" in f(M)


# --- town merchant/laborer house-size variety -----------------------------------------------------
def _town_housing(m_large, l_large, m_small=12, l_small=22):
    b = []
    for i in range(m_small):
        b.append(bldg(120 + i * 60, 120, "merchant"))
    for i in range(m_large):
        b.append(bldg(120 + i * 100, 240, "merchant_large", w=86, h=60))
    for i in range(l_small):
        b.append(bldg(120 + i * 50, 360, "laborer"))
    for i in range(l_large):
        b.append(bldg(120 + i * 70, 480, "laborer_large", w=50, h=34))
    return {"meta": {"scale": "town"}, "houses": [], "fields": [], "buildings": b}


def test_town_merchant_housing_varied_fires_when_uniform():
    assert "town_merchant_housing_varied" in f(_town_housing(m_large=0, l_large=3))


def test_town_merchant_housing_varied_passes_when_mixed():
    assert "town_merchant_housing_varied" not in f(_town_housing(m_large=4, l_large=3))


def test_town_laborer_housing_varied_fires_when_uniform():
    assert "town_laborer_housing_varied" in f(_town_housing(m_large=4, l_large=0))


def test_town_laborer_housing_varied_passes_when_mixed():
    assert "town_laborer_housing_varied" not in f(_town_housing(m_large=4, l_large=3))


# --- merchant_residences_behind_businesses (road-fronted towns: shops -> homes -> gap -> laborers) -
# A vertical trunk road at x=100; droad = |x - 100|. Shops front it, merchant homes sit behind, then
# the laborer warren further back with a gap.
def _town_behind(res_x=230, lab_x=300):
    b = []
    for i in range(7):
        b.append(bldg(150, 100 + i * 60, "shop"))          # businesses at droad ~50
    for i in range(3):
        b.append(bldg(res_x, 150 + i * 80, "merchant_large", w=86, h=60))   # merchant residences
    for i in range(6):
        b.append(bldg(lab_x, 120 + i * 50, "laborer"))     # laborer warren
    return {"meta": {"scale": "town"}, "houses": [], "fields": [],
            "road": [[100, 0], [100, 1000]], "road_width": 26, "buildings": b}


def test_merchant_residences_behind_businesses_passes_when_banded():
    assert "merchant_residences_behind_businesses" not in f(_town_behind(res_x=230, lab_x=320))


def test_merchant_residences_behind_businesses_fires_when_residence_in_storefront_band():
    # a merchant home sitting at droad 40 (within the shops' droad ~50 band), not behind it
    assert "merchant_residences_behind_businesses" in f(_town_behind(res_x=140, lab_x=320))


def test_merchant_residences_behind_businesses_fires_when_laborers_crowd_the_homes():
    # laborers at droad 140, only ~10px behind the merchant homes at droad 130 - no gap
    assert "merchant_residences_behind_businesses" in f(_town_behind(res_x=230, lab_x=240))


def test_merchant_residences_behind_businesses_skipped_without_a_road():
    # a walled town has no trunk M["road"]; the single-axis test must not run
    M = _town_behind(res_x=140, lab_x=240)
    del M["road"]
    assert "merchant_residences_behind_businesses" not in f(M)


# --- housing_aligned_behind_storefronts (a home tucked behind a shop lies parallel to it) ----------
# A vertical trunk road at x=100; along = y, droad = |x - 100|. Shops front it (rot 0); a home is
# "directly behind" a shop when it shares the shop's along-road position and sits one building deeper.
def _town_align(home_rot=0, home_x=200, home_y=280, with_shops=True):
    b = []
    if with_shops:
        for i in range(7):
            b.append(bldg(140, 100 + i * 60, "shop", rot=0))        # storefronts at droad 40
    b.append(bldg(home_x, home_y, "merchant_large", rot=home_rot, w=86, h=60))
    return {"meta": {"scale": "town"}, "houses": [], "fields": [],
            "road": [[100, 0], [100, 1000]], "road_width": 26, "buildings": b}


def test_housing_aligned_behind_storefronts_passes_when_parallel():
    # a home directly behind a shop (droad 100 vs 40 -> depth 60), same orientation -> fine
    assert "housing_aligned_behind_storefronts" not in f(_town_align(home_rot=0))


def test_housing_aligned_behind_storefronts_fires_when_askew():
    # same spot, but rotated 35deg off the storefront -> askew
    assert "housing_aligned_behind_storefronts" in f(_town_align(home_rot=35))


def test_housing_aligned_behind_storefronts_skips_a_home_far_back():
    # droad 240 -> depth 200 (> DEPTH_MAX): deep in the warren, not "directly behind" a shop
    assert "housing_aligned_behind_storefronts" not in f(_town_align(home_rot=35, home_x=340))


def test_housing_aligned_behind_storefronts_skips_a_home_beside_a_shop():
    # droad 50 -> depth 10 (< DEPTH_MIN): level with the shop row, not behind it
    assert "housing_aligned_behind_storefronts" not in f(_town_align(home_rot=35, home_x=150, home_y=310))


def test_housing_aligned_behind_storefronts_skips_a_laterally_offset_home():
    # proper depth but 240px away ALONG the road (outside any shop's radial shadow)
    assert "housing_aligned_behind_storefronts" not in f(_town_align(home_rot=35, home_y=700))


def test_housing_aligned_behind_storefronts_skips_when_no_storefronts():
    # homes but no shops at all -> nothing is "behind a storefront"
    assert "housing_aligned_behind_storefronts" not in f(_town_align(home_rot=35, with_shops=False))


def _maus_ward(ward_walls, maus_cy=1556):
    # a mausoleum (gate west) whose NORTH wall (y0 = cy-20) runs along a ward fence at y=1535,
    # inside a city wall - "ward_walls" records the sides the compound yielded to the fence
    return {"meta": {"scale": "city", "walled": True},
            "wall": [[100, 100], [3000, 100], [3000, 2500], [100, 2500]],
            "wards": [{"name": "samurai", "boundary": [[1620, 1535], [2401, 1535]], "z": 5}],
            "mausoleums": [{"x": 2246, "y": maus_cy, "w": 54, "h": 40, "rot": 0, "gate_dir": "west", "ward_walls": ward_walls}]}


def test_walled_structure_yields_to_ward_wall_fires_when_unyielded():
    # north wall abuts the fence but the compound drew its own wall there (not recorded)
    assert "walled_structure_yields_to_ward_wall" in f(_maus_ward([]))


def test_walled_structure_yields_to_ward_wall_passes_when_yielded():
    assert "walled_structure_yields_to_ward_wall" not in f(_maus_ward(["north"]))


def test_walled_structure_yields_to_ward_wall_passes_when_not_abutting():
    # the mausoleum sits well clear of the fence - nothing to yield
    assert "walled_structure_yields_to_ward_wall" not in f(_maus_ward([], maus_cy=2000))


def test_walled_structure_yields_to_ward_wall_fires_on_a_vertical_fence():
    # the mausoleum's EAST wall (x = cx+27 = 1535) runs along a VERTICAL ward fence at x=1535
    M = {"meta": {"scale": "city", "walled": True},
         "wall": [[100, 100], [3000, 100], [3000, 2500], [100, 2500]],
         "wards": [{"name": "samurai", "boundary": [[1535, 1200], [1535, 1900]], "z": 5}],
         "mausoleums": [{"x": 1508, "y": 1556, "w": 54, "h": 40, "rot": 0, "gate_dir": "west", "ward_walls": []}]}
    assert "walled_structure_yields_to_ward_wall" in f(M)


def test_walled_structure_yields_to_ward_wall_skips_compounds_outside_the_wall():
    # a compound OUTSIDE the city wall is not held to the rule (wards are an intramural feature)
    M = _maus_ward([])
    M["mausoleums"][0]["x"], M["mausoleums"][0]["y"] = 50, 50   # west of the wall (x >= 100): outside
    assert "walled_structure_yields_to_ward_wall" not in f(M)


def test_walled_structure_yields_to_ward_wall_skips_tilted_compounds():
    # a tilted compound is not axis-aligned to a fence, so the rule does not apply
    M = _maus_ward([])
    M["mausoleums"][0]["rot"] = 30
    assert "walled_structure_yields_to_ward_wall" not in f(M)


def _town_manor(gate_dir, rot=0, road=None):
    # a magistrate manor at (300,300); the "town" (houses) is to the SE at ~(950,933)
    M = {"meta": {"scale": "town"},
         "houses": [{"x": x, "y": y, "w": 40, "h": 28, "rot": 0, "kind": "plain"} for x, y in [(900, 900), (1000, 900), (950, 1000)]],
         "manors": [{"x": 300, "y": 300, "w": 120, "h": 90, "rot": rot, "gate_dir": gate_dir, "gate": [300, 300]}]}
    if road:
        M["road"] = road
    return M


def test_manor_gate_faces_town_passes_facing_the_town():
    assert "manor_gate_faces_town" not in f(_town_manor("south"))   # town is SE -> south gate faces it


def test_manor_gate_faces_town_fires_facing_away():
    assert "manor_gate_faces_town" in f(_town_manor("north"))       # north gate faces away from the SE town


def test_manor_gate_faces_town_passes_facing_the_road():
    # town centroid is SE, but a north gate faces an Imperial road to the manor's north -> ok
    assert "manor_gate_faces_town" not in f(_town_manor("north", road=[[100, 150], [600, 150]]))


def test_manor_rotation_records_rot_and_tilts_the_footprint():
    s = settlement.Settlement()
    s.manor(500, 500, 200, 120, "M", gate_dir="south", rot=30)
    mn = s.M["manors"][0]
    assert mn["rot"] == 30
    c = check_village.rect_corners(mn)
    assert abs(c[0][1] - c[1][1]) > 1   # the top edge is no longer horizontal -> the compound is tilted


def _crem_cem(crem_xy, cem_xy, walled=False):
    M = {"meta": {"scale": "town"},
         "cremation_grounds": [{"x": crem_xy[0], "y": crem_xy[1], "w": 116, "h": 80, "rot": 0}],
         "cemeteries": [{"x": cem_xy[0], "y": cem_xy[1], "w": 100, "h": 72, "rot": 0, "parish": True}]}
    if walled:
        M["wall"] = [[200, 200], [800, 200], [800, 800], [200, 800]]
    return M


def test_cremation_ground_by_external_cemetery_passes_when_adjacent():
    assert "cremation_ground_by_external_cemetery" not in f(_crem_cem((300, 300), (300, 420)))


def test_cremation_ground_by_external_cemetery_fires_when_far():
    assert "cremation_ground_by_external_cemetery" in f(_crem_cem((300, 300), (900, 900)))


def test_cremation_ground_by_external_cemetery_fires_when_only_internal_cemetery():
    # walled: cremation outside, but the only cemetery is INSIDE the wall (even adjacent) -> not external -> fires
    assert "cremation_ground_by_external_cemetery" in f(_crem_cem((150, 500), (250, 500), walled=True))


def test_cremation_ground_by_external_cemetery_passes_walled_with_external():
    # walled: cremation + cemetery both outside the wall, adjacent -> ok
    assert "cremation_ground_by_external_cemetery" not in f(_crem_cem((150, 500), (150, 620), walled=True))


def _crem_road(crem_xy, cem_xy):
    # a cremation ground + an adjacent external cemetery, beside a main road along y=200
    return {"meta": {"scale": "town"}, "road": [[100, 200], [900, 200]],
            "cremation_grounds": [{"x": crem_xy[0], "y": crem_xy[1], "w": 116, "h": 80, "rot": 0}],
            "cemeteries": [{"x": cem_xy[0], "y": cem_xy[1], "w": 100, "h": 72, "rot": 0, "parish": True}]}


def test_cremation_set_back_from_road_fires_when_on_the_road():
    assert "cremation_ground_set_back_from_main_road" in f(_crem_road((300, 260), (300, 360)))   # 60px off the road


def test_cremation_set_back_from_road_passes_when_far():
    assert "cremation_ground_set_back_from_main_road" not in f(_crem_road((300, 500), (300, 600)))


def test_cremation_set_back_from_road_passes_when_no_main_road():
    M = _crem_road((300, 260), (300, 360))
    del M["road"]   # a settlement on minor streets only - nothing to be set back from
    assert "cremation_ground_set_back_from_main_road" not in f(M)


def _crem_temple(crem_xy, mon_xy=(300, 500)):
    # a monastery + a cremation ground (with an adjacent cemetery), beside a main road along y=200.
    # The monastery at y=500 sits 300px back from the road; "behind" it means >= 260px back.
    return {"meta": {"scale": "town"}, "road": [[100, 200], [900, 200]],
            "religious": [{"x": mon_xy[0], "y": mon_xy[1], "w": 132, "h": 86, "rot": 0, "kind": "monastery"}],
            "cremation_grounds": [{"x": crem_xy[0], "y": crem_xy[1], "w": 116, "h": 80, "rot": 0}],
            "cemeteries": [{"x": crem_xy[0], "y": crem_xy[1] + 110, "w": 100, "h": 72, "rot": 0, "parish": True}]}


def test_cremation_not_between_temple_and_road_fires_when_between():
    # cremation on the road side of its monastery (closer to the road than the temple), yet still
    # clear of the road's own set-back floor - only the between-temple-and-road rule should object
    fails = f(_crem_temple((300, 360)))
    assert "cremation_ground_not_between_temple_and_road" in fails
    assert "cremation_ground_set_back_from_main_road" not in fails   # isolates the new rule


def test_cremation_not_between_temple_and_road_passes_when_behind():
    assert "cremation_ground_not_between_temple_and_road" not in f(_crem_temple((300, 640)))


def test_cremation_not_between_temple_and_road_passes_when_no_temple_nearby():
    # no temple within association range -> nothing to be "in front of"
    assert "cremation_ground_not_between_temple_and_road" not in f(_crem_temple((300, 360), mon_xy=(300, 1500)))


def test_no_structure_on_moat_fires_when_a_structure_sits_on_it():
    M = {"meta": {"scale": "city"}, "wall": [[200, 200], [800, 200], [800, 800], [200, 800]],
         "moat": _MOAT, "moat_width": 22,
         "buildings": [{"x": 168, "y": 500, "w": 44, "h": 30, "rot": 0, "kind": "laborer"},   # a corner within the moat band
                       {"x": 160, "y": 160, "w": 70, "h": 70, "rot": 0, "kind": "laborer"}]}  # a moat vertex inside the footprint
    assert "no_structure_on_moat" in f(M)


def test_city_temples_have_graveyards_fires_when_a_temple_unserved():
    assert "city_temples_have_graveyards" in f(_city_dead(temples=[(320, 320, "A", True), (680, 700, "B", True)]))


def test_city_temples_have_graveyards_exempts_a_flagged_temple():
    assert "city_temples_have_graveyards" not in f(_city_dead(temples=[(320, 320, "A", True), (680, 700, "B", False)]))


def test_city_has_mausoleum_fires_when_missing():
    assert "city_has_mausoleum" in f(_city_dead(maus=[]))


def test_city_has_mausoleum_fires_when_outside_walls():
    assert "city_has_mausoleum" in f(_city_dead(maus=[(100, 100)]))


def test_city_has_mausoleum_fires_when_far_from_quarter():
    assert "city_has_mausoleum" in f(_city_dead(maus=[(260, 740)], gov=(740, 260)))


def test_city_has_mausoleum_passes_when_by_quarter():
    assert "city_has_mausoleum" not in f(_city_dead())


def test_city_has_cremation_ground_fires_when_inside_walls():
    assert "city_has_cremation_ground" in f(_city_dead(crem=[(500, 400)]))


def test_city_has_cremation_ground_passes_when_outside():
    assert "city_has_cremation_ground" not in f(_city_dead())


def test_city_has_ossuary_fires_when_far_from_cremation():
    assert "city_has_ossuary" in f(_city_dead(oss=[(900, 100)]))


def test_city_has_ossuary_passes_when_by_cremation():
    assert "city_has_ossuary" not in f(_city_dead())


def _town_dead(crem, dwell=((300, 300),)):
    return {"meta": {"scale": "town"},
            "houses": [{"x": x, "y": y, "w": 40, "h": 28, "rot": 0, "kind": "plain"} for (x, y) in dwell],
            "cemeteries": [{"x": 300, "y": 360, "w": 70, "h": 50, "rot": 0}],
            "religious": [{"kind": "monastery", "x": 300, "y": 300, "w": 80, "h": 60, "label": "M", "graveyard": True}],
            "cremation_grounds": [{"x": x, "y": y, "w": 116, "h": 80, "rot": 0} for (x, y) in crem]}


def test_town_has_cremation_ground_fires_when_missing():
    assert "town_has_cremation_ground" in f(_town_dead([]))


def test_town_has_cremation_ground_fires_when_among_dwellings():
    assert "town_has_cremation_ground" in f(_town_dead([(320, 300)]))


def test_town_has_cremation_ground_passes_when_at_the_edge():
    assert "town_has_cremation_ground" not in f(_town_dead([(900, 900)]))


# ---- fire-watch towers (hinomi-yagura) & fire-break plazas (hiyokechi/hirokoji) ----

def _tower(x, y):
    return {"x": x, "y": y, "w": 26, "h": 26, "rot": 0}


def _break(x, y, w=150, h=110):
    return {"x": x, "y": y, "w": w, "h": h, "rot": 0}


def test_walled_town_has_fire_tower_fires_when_absent():
    assert "walled_town_has_fire_tower" in f({"meta": {"scale": "town", "walled": True}})


def test_walled_town_has_fire_tower_passes_with_one():
    assert "walled_town_has_fire_tower" not in f({"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(500, 500)]})


def test_walled_town_has_fire_tower_opt_out():
    assert "walled_town_has_fire_tower" not in f({"meta": {"scale": "town", "walled": True, "fire_tower": False}})


def test_walled_town_has_firebreak_fires_when_absent():
    assert "walled_town_has_firebreak" in f({"meta": {"scale": "town", "walled": True}})


def test_walled_town_has_firebreak_passes_with_one():
    assert "walled_town_has_firebreak" not in f({"meta": {"scale": "town", "walled": True}, "firebreaks": [_break(500, 500)]})


def test_walled_town_has_firebreak_opt_out():
    assert "walled_town_has_firebreak" not in f({"meta": {"scale": "town", "walled": True, "firebreak": False}})


def test_unwalled_town_needs_no_fire_tower_or_break():
    # an OPEN road-town relies on its road and field gaps; the presence checks are walled-only
    fails = f({"meta": {"scale": "town", "walled": False}})
    assert "walled_town_has_fire_tower" not in fails and "walled_town_has_firebreak" not in fails


def test_city_has_fire_towers_fires_with_one():
    assert "city_has_fire_towers" in f({"meta": {"scale": "city"}, "fire_towers": [_tower(500, 500)]})


def test_city_has_fire_towers_passes_with_two():
    assert "city_has_fire_towers" not in f({"meta": {"scale": "city"}, "fire_towers": [_tower(500, 500), _tower(700, 700)]})


def test_city_has_fire_towers_opt_out():
    assert "city_has_fire_towers" not in f({"meta": {"scale": "city", "fire_tower": False}})


def test_city_has_firebreak_fires_when_absent():
    assert "city_has_firebreak" in f({"meta": {"scale": "city"}})


def test_city_has_firebreak_passes_with_one():
    assert "city_has_firebreak" not in f({"meta": {"scale": "city"}, "firebreaks": [_break(500, 500)]})


def test_fire_tower_in_commoner_quarter_fires_in_samurai_quarter():
    # a tower whose nearest neighbours are all samurai sits in the samurai quarter, not the warren
    M = {"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(500, 500)],
         "buildings": [bldg(520, 510, "samurai"), bldg(480, 515, "samurai"), bldg(510, 480, "samurai_large")]}
    assert "fire_tower_in_commoner_quarter" in f(M)


def test_fire_tower_in_commoner_quarter_fires_when_isolated():
    M = {"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(500, 500)],
         "buildings": [bldg(900, 900, "laborer")]}   # nearest dwelling > 230px away
    assert "fire_tower_in_commoner_quarter" in f(M)


def test_fire_tower_in_commoner_quarter_passes_among_commoners():
    M = {"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(500, 500)],
         "buildings": [bldg(520, 510, "laborer"), bldg(480, 515, "servant"), bldg(510, 480, "merchant")]}
    assert "fire_tower_in_commoner_quarter" not in f(M)


def test_firebreak_hosts_amusements_fires_in_dead_space():
    assert "firebreak_hosts_amusements" in f({"meta": {"scale": "town", "walled": True}, "firebreaks": [_break(500, 500)]})


def test_firebreak_hosts_amusements_passes_by_the_stage():
    M = {"meta": {"scale": "town", "walled": True}, "firebreaks": [_break(500, 500)],
         "theater_stage": {"x": 560, "y": 520, "w": 150, "h": 105, "rot": 0}}
    assert "firebreak_hosts_amusements" not in f(M)


def test_firebreak_hosts_amusements_passes_by_shops():
    M = {"meta": {"scale": "town", "walled": True}, "firebreaks": [_break(500, 500)],
         "buildings": [bldg(540, 520, "shop"), bldg(470, 530, "shop"), bldg(520, 470, "merchant")]}
    assert "firebreak_hosts_amusements" not in f(M)


def test_firebreak_clear_of_dwellings_fires():
    M = {"meta": {"scale": "town", "walled": True}, "firebreaks": [_break(500, 500)],
         "buildings": [bldg(500, 500, "laborer")]}   # a dwelling sitting ON the plaza
    assert "firebreak_clear_of_dwellings" in f(M)


def test_firebreak_clear_of_dwellings_passes_when_clear():
    M = {"meta": {"scale": "town", "walled": True}, "firebreaks": [_break(500, 500)],
         "buildings": [bldg(750, 750, "laborer")]}
    assert "firebreak_clear_of_dwellings" not in f(M)


def test_fire_tower_on_wall_overlaps_like_any_structure():
    # fire_towers are in _OVERLAP_STRUCTS, so a tower on the wall trips no_structure_on_wall
    M = {"meta": {"scale": "town", "walled": True}, "wall": [[100, 500], [900, 500]], "gate": [500, 500],
         "fire_towers": [_tower(500, 500)]}
    assert "no_structure_on_wall" in f(M)


if __name__ == "__main__":
    import sys
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    rc = 0
    for t in tests:
        try:
            t()
            print("PASS " + t.__name__)
        except AssertionError as e:
            print("FAIL " + t.__name__ + ("  " + str(e) if str(e) else ""))
            rc = 1
    sys.exit(rc)
