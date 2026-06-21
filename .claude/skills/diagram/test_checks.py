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
# the cross) must NOT count as serving the lane - so a lane with only such neighbours reads as
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
    # fire, not just a centre on it) - the old houses_off_corridors centre-test missed corners.
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
                 "city_has_samurai_neighbourhood", "city_has_merchant_district",
                 "city_has_laborer_neighbourhoods", "city_has_outside_farmland"):
        assert name in fails


def test_city_ministry_of_rites_fires_when_six_but_none_are_rites():
    mins = [{"x": i * 30, "y": 50, "w": 80, "h": 50, "name": f"Ministry {i}"} for i in range(6)]
    assert "city_has_ministry_of_rites" in f({"meta": {"scale": "city"}, "ministries": mins})


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


def test_city_civic_amenity_checks_fire_on_an_empty_city():
    fails = f({"meta": {"scale": "city"}})
    for name in ("city_has_merchant_storehouses", "city_has_flophouse", "city_has_amphitheater"):
        assert name in fails


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


def test_city_streets_clear_of_wall_moat_fires():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ,
         "gates": [[500, 200], [500, 800]],
         "town_streets": [{"pts": [[500, 500], [990, 500]], "w": 18}]}   # a vertex outside the wall
    assert "city_streets_clear_of_wall_moat" in f(M)


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
