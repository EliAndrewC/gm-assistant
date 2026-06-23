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


def test_city_civic_amenity_checks_fire_on_an_empty_city():
    fails = f({"meta": {"scale": "city"}})
    for name in ("city_has_merchant_storehouses", "city_has_flophouse", "city_has_amphitheater"):
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


def test_city_amphitheater_larger_than_town_fires_when_small():
    # a town-sized amphitheater (radius 70) in a city - a city's is ~50% larger
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]], "amphitheater": {"x": 500, "y": 500, "r": 70}}
    assert "city_amphitheater_larger_than_town" in f(M)


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
