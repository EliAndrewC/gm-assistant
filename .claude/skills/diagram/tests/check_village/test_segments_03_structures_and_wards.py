"""Split from test_checks.py by feature 025 - see tests/check_village/CLAUDE.md for the index."""

import math
import sys

import check_village
from tests.check_village._builders import (
    _CHAN,
    _MOAT,
    _STRM,
    FEAT,
    WALL,
    WALLSQ,
    _capital_manifest,
    _farmhouse,
    _feature_overlap,
    _field,
    _fort_city,
    _label_map,
    _maus_ward,
    _paddy_field_rec,
    _road_map,
    _tower,
    _walled,
    _ward_wall,
    bldg,
    f,
)


# ---- a feature-footprint overlap check ----------------------------------------------------
def test_no_structure_on_wall_fires():
    # on the TOP rampart segment - note the wall is an OPEN polyline (the closing edge is not
    # a real wall segment, since a real rampart is an arc anchored to a hill), so the building
    # must sit on one of its drawn segments, not the implicit closure.
    M = {"meta": {"scale": "town", "walled": True}, "wall": WALL, "buildings": [bldg(400, 50)]}
    assert "no_structure_on_wall" in f(M)


def test_flophouse_on_road_overlaps_like_any_structure():
    # a standalone civic building (flophouse) is now checked for overlaps too: one sitting on
    # the road must trip no_structure_on_road, exactly as a shop would.
    M = {"meta": {"scale": "town"}, "road": [[100, 500], [900, 500]], "road_width": 26, "flophouses": [{"x": 500, "y": 500, "w": 104, "h": 46, "rot": 0}]}
    assert "no_structure_on_road" in f(M)  # 1 < 2


# ---- a meta-driven scale rule -------------------------------------------------------------
def test_hamlet_has_no_headman_fires_when_a_hamlet_has_one():
    M = {"meta": {"scale": "hamlet"}, "houses": [{"x": 100, "y": 100, "w": 108, "h": 68, "kind": "big", "rot": 0, "role": "headman"}]}
    assert "hamlet_has_no_headman" in f(M)


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
    M = {
        "meta": {"scale": "town", "walled": True},
        "wall": WALL,
        "town_streets": [{"pts": [[120, 120], [120, 400]], "w": 20}],
        "buildings": [bldg(800, 800, kind="shop")],
    }  # a shop nowhere near the street
    assert "businesses_front_streets" in f(M)


def test_housing_off_main_street_fires():
    M = {
        "meta": {"scale": "town", "walled": True},
        "wall": WALL,
        "town_streets": [{"pts": [[500, 120], [500, 800]], "w": 20, "main": True}],
        "buildings": [bldg(540, 500, kind="laborer", rot=-90)],
    }  # a dwelling on the MAIN frontage
    assert "housing_off_main_street" in f(M)


def test_roads_drawn_under_overlays_fires():
    M = {
        "meta": {"scale": "town"},
        "road": [[100, 500], [900, 500]],
        "road_width": 26,
        "road_z": 1000,
        "labels": [
            [480, 480, 520, 520, 5],  # a label (z=5) the road (z=1000) is painted OVER
            [100, 100, 140, 140, 5],
        ],
    }  # a low-z label the road does NOT touch (the no-hit path)
    assert "roads_drawn_under_overlays" in f(M)


def test_all_houses_field_adjacent_dispersed_fires_on_a_remote_house():
    M = {"meta": {"scale": "village"}, "fields": [_field("f", 100, 100, 400, 400)], "houses": [_farmhouse(430, 250), _farmhouse(1200, 250)]}
    assert "all_houses_field_adjacent" in f(M)  # the x=1200 house is way off its fields


def test_all_houses_field_adjacent_dispersed_passes_when_close():
    M = {"meta": {"scale": "village"}, "fields": [_field("f", 100, 100, 400, 400)], "houses": [_farmhouse(430, 250), _farmhouse(60, 250)]}
    assert "all_houses_field_adjacent" not in f(M)  # both within 165px of the field


def test_nucleated_cluster_abuts_fields_passes_with_interior_houses_set_back():
    # a tight cluster whose EAST edge touches the field; interior houses sit a cluster-span back (fine)
    houses = [_farmhouse(x, 250) for x in (60, 130, 200, 270, 340, 410)]
    M = {"meta": {"scale": "village", "nucleated": True}, "fields": [_field("f", 430, 150, 700, 400)], "houses": houses}
    assert "cluster_abuts_fields" not in f(M)
    assert "all_houses_field_adjacent" not in f(M)  # the per-house check does NOT run for nucleated


def test_nucleated_cluster_abuts_fields_fires_when_the_village_floats_off_its_land():
    houses = [_farmhouse(x, 250) for x in (60, 130, 200, 270)]
    M = {"meta": {"scale": "village", "nucleated": True}, "fields": [_field("f", 1400, 150, 1700, 400)], "houses": houses}  # fields ~1000px from the whole cluster
    assert "cluster_abuts_fields" in f(M)


def test_irrigation_channels_hairline_fires_on_a_fat_ditch():
    M = {"channels": [{"poly": _CHAN, "frm": {"kind": "offmap"}, "to": {"kind": "field", "name": "f"}, "w": 4.2}]}
    assert "irrigation_channels_hairline" in f(M)  # the OLD 4.2 px stout ditch must now trip


def test_irrigation_channels_hairline_passes_at_the_floor():
    M = {"channels": [{"poly": _CHAN, "frm": {"kind": "offmap"}, "to": {"kind": "field", "name": "f"}, "w": 2.5}]}
    assert "irrigation_channels_hairline" not in f(M)


def test_irrigation_channels_hairline_allows_a_drain_outfall_culvert_at_four():
    # a drain-outfall culvert carries the fan's whole runoff and matches the drain's outfall width
    # (4.0 at the city grain) - it is not a field ditch, so its ceiling is 4.5 (GM 2026-07-23)
    M = {"channels": [{"poly": _CHAN, "frm": {"kind": "drain"}, "to": {"kind": "moat"}, "w": 4.0}]}
    assert "irrigation_channels_hairline" not in f(M)


def test_irrigation_channels_hairline_still_fires_on_a_fat_drain_culvert():
    M = {"channels": [{"poly": _CHAN, "frm": {"kind": "drain"}, "to": {"kind": "moat"}, "w": 5.0}]}
    assert "irrigation_channels_hairline" in f(M)


def test_watercourses_wider_than_ditches_fires_when_a_creek_reads_like_a_ditch():
    M = {
        "channels": [{"poly": _CHAN, "frm": {"kind": "offmap"}, "to": {"kind": "field", "name": "f"}, "w": 2.5}],
        "streams": [{"poly": _STRM, "frm": None, "to": None, "w": 5}],
    }  # 5 < 2.5x2.5 -> too close to the ditch
    assert "watercourses_wider_than_ditches" in f(M)


def test_watercourses_wider_than_ditches_passes_for_a_proper_creek():
    M = {"channels": [{"poly": _CHAN, "frm": {"kind": "offmap"}, "to": {"kind": "field", "name": "f"}, "w": 2.5}], "streams": [{"poly": _STRM, "frm": None, "to": None, "w": 9}]}  # 9 >= 6.25
    assert "watercourses_wider_than_ditches" not in f(M)


def test_moat_is_heaviest_watercourse_fires_when_a_stream_out_widths_it():
    M = {"streams": [{"poly": _STRM, "frm": None, "to": None, "w": 30}], "moat_width": 26}  # stream > moat
    assert "moat_is_heaviest_watercourse" in f(M)


def test_moat_is_heaviest_watercourse_passes_when_a_feeder_equals_it():
    M = {"streams": [{"poly": _STRM, "frm": None, "to": None, "w": 26}], "moat_width": 26}  # equal is allowed
    assert "moat_is_heaviest_watercourse" not in f(M)


def test_moat_dwarfs_ditches_fires_on_a_skimpy_moat():
    M = {"channels": [{"poly": _CHAN, "frm": {"kind": "offmap"}, "to": {"kind": "field", "name": "f"}, "w": 2.5}], "moat_width": 8}  # 8 < 4x2.5
    assert "moat_dwarfs_ditches" in f(M)


def test_moat_dwarfs_ditches_passes_for_a_real_city_moat():
    M = {"channels": [{"poly": _CHAN, "frm": {"kind": "offmap"}, "to": {"kind": "field", "name": "f"}, "w": 2.5}], "moat_width": 26}  # 26 >= 10
    assert "moat_dwarfs_ditches" not in f(M)


def test_shrine_clear_of_grove_trees_fires_when_a_clump_covers_the_hall():
    # a fengshui-grove tree clump whose center sits on the shrine hall's footprint reads as buried in the wood
    M = {
        "meta": {"scale": "village"},
        "religious": [{"kind": "shrine", "x": 500, "y": 500, "w": 30, "h": 24, "label": "Shrine"}],
        "village_groves": [{"role": "water_mouth", "r": 14, "clumps": [[502, 498]]}],
    }
    assert "shrine_clear_of_grove_trees" in f(M)


def test_shrine_clear_of_grove_trees_uses_the_canopy_radius_not_the_nominal_clump():
    # a clump 18px off the hall's east edge: its NOMINAL r=14 does not reach, but the drawn CANOPY (~1.7x = 24)
    # does - the check uses the canopy radius, so it fires (the crown overhang is what the eye sees overlapping)
    M = {
        "meta": {"scale": "village"},
        "religious": [{"kind": "shrine", "x": 500, "y": 500, "w": 30, "h": 24, "label": "Shrine"}],  # east edge x=515
        "village_groves": [{"role": "water_mouth", "r": 14, "clumps": [[533, 500]]}],
    }  # 18px off -> canopy overlaps
    assert "shrine_clear_of_grove_trees" in f(M)


def test_torii_clear_of_grove_trees_fires_when_a_clump_covers_the_arch():
    # a fengshui-grove tree clump sitting on a torii arch reads as the arch buried in the wood
    M = {"meta": {"scale": "village"}, "torii": [[500, 500, 1]], "village_groves": [{"role": "water_mouth", "r": 14, "clumps": [[505, 504]]}]}
    assert "torii_clear_of_grove_trees" in f(M)


def test_dry_plots_clear_of_paddies_fires_on_a_hem_plot_in_the_rice():
    # a neighboring fan's hem quilt punched into this fan's envelope (the Tango fe2-into-fe1 incident)
    M = {"fields": [_field("p", 440, 440, 600, 600)], "dry_plots": [{"poly": [[560, 560], [640, 560], [640, 640], [560, 640]], "crop": "millet", "theta": 0.4}]}  # NW corner ~40px deep in the paddy
    assert "dry_plots_clear_of_paddies" in f(M)


def test_dry_plots_clear_of_paddies_passes_when_the_hem_abuts_the_bund():
    # a hem plot legitimately KISSES the envelope across the berm - only real interpenetration fires
    M = {
        "fields": [_field("p", 440, 440, 600, 600)],
        "dry_plots": [{"poly": [[440, 600], [600, 600], [600, 660], [440, 660]], "crop": "barley", "theta": 0.4}],
    }  # shares the paddy's south edge exactly
    assert "dry_plots_clear_of_paddies" not in f(M)


def test_city_lanes_layered_by_width_fires_when_narrow_over_wide():
    # the wide Imperial road (26) is drawn EARLY (low z) and a narrow street (18) that crosses it is
    # drawn later (high z): the narrow lane paints over the wider road - the wider must be on top.
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "road": [[500, 150], [500, 850]],
        "road_width": 26,
        "road_z": 5,
        "town_streets": [{"pts": [[300, 500], [700, 500]], "w": 18, "z": 50}],
    }  # crosses the road at (500,500)
    assert "city_lanes_layered_by_width" in f(M)


def test_city_lane_under_wall_fires_when_a_street_touches_the_wall():
    # a street whose end reaches the wall (z above the rampart's) renders OVER it - away from any gate
    M = _walled(streets=[{"pts": [[300, 300], [300, 205]], "w": 18, "z": 100}])
    assert "city_lane_under_wall" in f(M)


def test_city_lane_under_wall_fires_when_a_street_crosses_the_wall():
    M = _walled(streets=[{"pts": [[300, 150], [300, 300]], "w": 18, "z": 100}])  # crosses the top edge off-gate
    assert "city_lane_under_wall" in f(M)


def test_city_lane_under_wall_passes_at_a_gate_opening():
    # a road through the gate crosses the wall ring there, but the gate is a genuine opening - exempt
    M = _walled(streets=[{"pts": [[500, 400], [500, 150]], "w": 18, "z": 100}])  # crosses at the gate (500,200)
    assert "city_lane_under_wall" not in f(M)


def test_city_lane_under_wall_passes_when_lane_already_under():
    M = _walled(streets=[{"pts": [[300, 300], [300, 205]], "w": 18, "z": 5}])  # z below wall_z (10)
    assert "city_lane_under_wall" not in f(M)


def test_city_lane_under_wall_handles_an_open_town_wall():
    # a town wall is an open arc (not a closed ring); a street touching it off-gate still fires
    M = {"meta": {"scale": "town"}, "wall": [[200, 500], [500, 200], [800, 500]], "wall_z": 10, "gate": [500, 200], "town_streets": [{"pts": [[300, 600], [352, 352]], "w": 18, "z": 100}]}
    assert "city_lane_under_wall" in f(M)


def test_city_lanes_under_ward_fences_fires_when_a_lane_renders_over_a_fence():
    M = {"meta": {"scale": "city"}, "wards": [{"name": "samurai", "boundary": [[300, 500], [700, 500]], "z": 10}], "alleys": [{"pts": [[400, 300], [400, 505]], "w": 10, "z": 100}]}
    assert "city_lanes_under_ward_fences" in f(M)


def test_city_lanes_under_ward_fences_passes_when_crossing_at_a_kido():
    M = {
        "meta": {"scale": "city"},
        "wards": [{"name": "samurai", "boundary": [[300, 500], [700, 500]], "z": 10}],
        "kido": [{"x": 400, "y": 500}],
        "alleys": [{"pts": [[400, 300], [400, 505]], "w": 10, "z": 100}],
    }
    assert "city_lanes_under_ward_fences" not in f(M)


# --- no_label_overlaps (two body labels must not overlap) ---
def test_no_label_overlaps_fires_when_glyphs_cross():
    # two same-line labels whose boxes cross by >2px (x) and >4px (y) - the glyphs touch (the real
    # Hoshizora "cremation ground" / "Monastery of Bishamon" collision: 3px x, 10px y)
    M = {"meta": {}, "labels": [[40, 740, 143, 752, 1, "cremation ground"], [140, 736, 290, 750, 2, "Monastery of Bishamon"]]}
    assert "no_label_overlaps" in f(M)


def test_no_label_overlaps_passes_when_stacked_boxes_only_kiss():
    # two STACKED labels whose boxes merely kiss vertically (2.2px, the descender allowance) but are
    # cleanly separated lines (the real Tango "Mausoleum" / "Ministry of Works") - must NOT flag
    M = {"meta": {}, "labels": [[2216, 1580, 2276, 1593, 1, "Mausoleum"], [2168, 1591, 2252, 1600, 2, "Ministry of Works"]]}
    assert "no_label_overlaps" not in f(M)


def test_no_label_overlaps_passes_when_clear():
    M = {"meta": {}, "labels": [[40, 740, 130, 752, 1, "a"], [200, 740, 300, 752, 2, "b"]]}
    assert "no_label_overlaps" not in f(M)


# --- label_hugs_its_referent (a caption must sit against the feature it names) ---
# Element [6] of a label record is the subject box, written only by the standoff-ladder path. The
# real defect: Tango's "Imperial Road" 55px off the roadway with nothing but bare ground between,
# which the overlap-only scorer scored as perfect. Box heights below are ascent+descender = 1.05x
# the font size, which is how the check recovers the size to scale its cap.
def test_label_hugs_its_referent_fires_on_a_caption_adrift_in_empty_ground():
    M = {"meta": {}, "labels": [[400, 500, 486, 512.6, 1, "Imperial Road", [540, 400, 549, 700]]]}
    assert "label_hugs_its_referent" in f(M)


def test_label_hugs_its_referent_passes_a_caption_tucked_against_its_subject():
    M = {"meta": {}, "labels": [[400, 500, 486, 512.6, 1, "Imperial Road", [491, 400, 500, 700]]]}
    assert "label_hugs_its_referent" not in f(M)


def test_label_hugs_its_referent_skips_a_caption_with_no_subject():
    # a district caption names an AREA, not a feature, so it records no referent and is exempt
    # (city_labels_placed_with_subject governs those instead)
    M = {"meta": {}, "labels": [[400, 500, 560, 512.6, 1, "samurai neighborhood"]]}
    assert "label_hugs_its_referent" not in f(M)


def test_road_label_tilts_with_the_roadway_fires_on_level_text_beside_a_diagonal_road():
    # the motivating map: Hoshizora's "Imperial Road" set square to the page beside a -26.6deg roadbed
    assert "road_label_tilts_with_the_roadway" in f(_road_map([[1000, 1000], [1400, 800]]))


def test_road_label_tilts_with_the_roadway_passes_a_caption_running_along_the_road():
    assert "road_label_tilts_with_the_roadway" not in f(_road_map([[1000, 1000], [1400, 800]], tilt=-26.6))


def test_road_label_stays_LEVEL_on_a_north_south_road():
    # the GM's own convention, and the reason linear_tilt clamps rather than folds: past 45deg the
    # caption reads left-to-right, so LEVEL is what passes here and a tilt is what fires
    assert "road_label_tilts_with_the_roadway" not in f(_road_map([[1200, 800], [1200, 1200]]))
    assert "road_label_tilts_with_the_roadway" in f(_road_map([[1200, 800], [1200, 1200]], tilt=-26.6))


def test_road_label_tilts_with_the_roadway_fires_when_no_caption_was_drawn():
    # a recorded road_label with no label record behind it is a caption that never reached the
    # sheet - the check reports rather than silently skipping (a check that never runs looks
    # exactly like a check that passes)
    M = _road_map([[1000, 1000], [1400, 800]])
    M["labels"] = []
    assert "road_label_tilts_with_the_roadway" in f(M)


def test_title_clear_of_features_passes_over_blank_space():
    M = {"meta": {"scale": "village"}, "houses": [{"x": 300, "y": 300, "w": 60, "h": 40, "rot": 0, "kind": "plain"}], "title": {"name": "V", "bbox": [800, 50, 900, 90]}}
    assert "title_clear_of_features" not in f(M)


def test_title_clear_of_features_fires_on_a_house():
    M = {"meta": {"scale": "village"}, "houses": [{"x": 300, "y": 300, "w": 60, "h": 40, "rot": 0, "kind": "plain"}], "title": {"name": "V", "bbox": [280, 285, 340, 315]}}  # box on the house
    assert "title_clear_of_features" in f(M)


def test_title_clear_of_features_fires_over_a_field():
    M = {"meta": {"scale": "village"}, "fields": [_field("p", 200, 200, 600, 600)], "title": {"name": "V", "bbox": [300, 300, 450, 340]}}
    assert "title_clear_of_features" in f(M)


def test_title_clear_of_features_tolerates_scrub_but_not_grove_or_marsh():
    # The scrub commons is sparse GROUND COVER (a feathered grass scatter), not a feature with a footprint, and
    # a bold place name reads fine over it - so it does NOT block a title. This changed when the commons began
    # clothing the field's interior voids too (GM, 2026-07): scrub then covers nearly the whole map, and
    # treating it as an obstacle would leave the title nowhere at all to sit. Must stay in step with
    # `Settlement._title_obstacles`.
    scrub = {"meta": {"scale": "village"}, "commons": [{"poly": [[200, 200], [400, 200], [400, 400], [200, 400]]}], "title": {"name": "V", "bbox": [250, 250, 350, 300]}}
    assert "title_clear_of_features" not in f(scrub)
    # the GROVE (dense closed canopy) and the MARSH (a distinct wetland) DO still block it
    for k in ("village_groves", "marshes"):
        M = {"meta": {"scale": "village"}, k: [{"poly": [[200, 200], [400, 200], [400, 400], [200, 400]]}], "title": {"name": "V", "bbox": [250, 250, 350, 300]}}
        assert "title_clear_of_features" in f(M), k


def test_title_clear_of_features_fires_over_the_pond():
    M = {"meta": {"scale": "village"}, "pond": [400, 400, 100, 80], "title": {"name": "V", "bbox": [380, 380, 450, 420]}}
    assert "title_clear_of_features" in f(M)


def test_scalebar_matches_declared_scale_passes():
    M = {"meta": {"scale": "village", "ftpx": 2}, "title": {"name": "V", "bbox": [800, 50, 900, 132]}, "scalebar": {"ft": 200, "ftpx": 2, "bbox": [800, 93, 900, 132]}}
    assert "scalebar_matches_declared_scale" not in f(M)


def test_scalebar_matches_declared_scale_fires_when_missing():
    # a manifest with a title but no scalebar predates the bar (GM 2026-07-20) - regenerate the map
    M = {"meta": {"scale": "village", "ftpx": 2}, "title": {"name": "V", "bbox": [800, 50, 900, 90]}}
    assert "scalebar_matches_declared_scale" in f(M)


def test_scalebar_matches_declared_scale_fires_on_a_wrong_distance():
    # a village map (2 ft/px) whose bar claims the hamlet distance - the 100 map-px bar must read 200 ft
    M = {"meta": {"scale": "village", "ftpx": 2}, "title": {"name": "V", "bbox": [800, 50, 900, 132]}, "scalebar": {"ft": 100, "ftpx": 1, "bbox": [800, 93, 900, 132]}}
    assert "scalebar_matches_declared_scale" in f(M)


def test_headman_has_kura_fires_on_a_bare_headman_and_passes_with_one():
    # the shoya always has a fireproof kura (GM 2026-07-21): prosperity by definition, plus the office's
    # ledgers and tax rice need fireproof storage - the ~30% wealth dice are for ordinary plains only
    M = {"meta": {"scale": "village"}, "houses": [{"x": 500, "y": 500, "w": 46, "h": 28, "rot": 0, "kind": "plain", "role": "headman", "shed": False}]}
    assert "headman_has_kura" in f(M)
    M["houses"][0]["shed"] = True
    assert "headman_has_kura" not in f(M)


def test_village_shrine_footprint_within_norms_fires_on_a_monastery_sized_hall():
    # Hikari's defect in miniature: a 236x164 ft hall is a small monastery, not a village kami shrine
    M = {"meta": {"scale": "village", "ftpx": 2}, "religious": [{"x": 500, "y": 500, "w": 118, "h": 82, "kind": "shrine"}]}
    assert "village_shrine_footprint_within_norms" in f(M)
    # ... while the showcase Benten class (~490 m^2) passes with headroom under the 600 m^2 ceiling
    M2 = {"meta": {"scale": "village", "ftpx": 2}, "religious": [{"x": 500, "y": 500, "w": 44, "h": 30, "kind": "shrine"}]}
    assert "village_shrine_footprint_within_norms" not in f(M2)


def test_trees_clear_of_fengshui_ponds_fires_on_an_overhanging_clump():
    # Hoshigaoka's defect in miniature: a grove clump's canopy (1.7x nominal r) crossing the half-moon
    # pond's water fires; a clump standing clear passes. Pond poly = a simple half-disk stand-in.
    pond = {"cx": 300, "cy": 300, "r": 40, "facing": 270, "poly": [[340, 300], [300, 340], [260, 300]]}
    M = {
        "meta": {"scale": "village"},
        "crescent_ponds": [pond],
        "village_groves": [{"poly": [[200, 200], [400, 200], [400, 400], [200, 400]], "role": "windbreak", "r": 10, "clumps": [[310, 315]]}],
        "labels": [[270, 350, 340, 362, 1, "geomantic pond"]],
    }
    assert "trees_clear_of_fengshui_ponds" in f(M)
    M["village_groves"][0]["clumps"] = [[500, 500]]
    assert "trees_clear_of_fengshui_ponds" not in f(M)


def test_crescent_pond_labeled_fires_when_the_label_is_missing():
    # the banyuetang is culturally specific and does not read by itself (the GM asked "what is that?")
    pond = {"cx": 300, "cy": 300, "r": 40, "facing": 270, "poly": [[340, 300], [300, 340], [260, 300]]}
    M = {"meta": {"scale": "village"}, "crescent_ponds": [pond]}
    assert "crescent_pond_labeled" in f(M)
    M["labels"] = [[270, 350, 340, 362, 1, "geomantic pond"]]
    assert "crescent_pond_labeled" not in f(M)


def test_title_has_placard_fires_on_a_pre_placard_manifest():
    # the parchment card under the title + scale bar (GM 2026-07-21, legibility over scrub) is drawn
    # by s.title() - a manifest without the record predates the card and needs regeneration
    M = {"meta": {"scale": "village"}, "title": {"name": "V", "bbox": [800, 50, 900, 132]}}
    assert "title_has_placard" in f(M)
    M["title"]["placard"] = [800, 50, 900, 132]
    assert "title_has_placard" not in f(M)


def test_no_structure_on_canal_fires_and_passes():
    # GM 2026-07 (Nagahara, first city with a cargo canal): a merchant house in the canal water
    canal = [{"poly": [[300, 500], [700, 500]], "w": 14}]
    fire = {"canals": canal, "buildings": [{"x": 500, "y": 500, "w": 24, "h": 18, "rot": 0, "kind": "merchant_house"}]}
    assert "no_structure_on_canal" in f(fire)
    ok = {"canals": canal, "buildings": [{"x": 500, "y": 440, "w": 24, "h": 18, "rot": 0, "kind": "merchant_house"}]}
    assert "no_structure_on_canal" not in f(ok)


def test_city_ward_cap_flush_to_wall_fires_when_a_cap_juts():
    # a straight cap whose far vertex juts 30px off the wall face (the corner-stub artifact)
    ward = {"name": "samurai", "boundary": [[200, 500], [500, 500]], "wall_caps": [{"x": 200, "y": 500, "pts": [[200, 500], [230, 500]]}]}
    assert "city_ward_cap_flush_to_wall" in f(_fort_city(wards=[ward]))


def test_city_ward_cap_flush_to_wall_passes_when_flush():
    # a cap that lies ALONG the west wall face (x=200): both vertices sit on the wall
    ward = {"name": "samurai", "boundary": [[200, 500], [500, 500]], "wall_caps": [{"x": 200, "y": 500, "pts": [[200, 484], [200, 516]]}]}
    assert "city_ward_cap_flush_to_wall" not in f(_fort_city(wards=[ward]))


# --- intersections_are_crossroads (lane beds merge, no edge line across a junction) ---
def test_intersections_are_crossroads_fires_when_edges_over_beds():
    assert "intersections_are_crossroads" in f({"ground_edge_zmax": 50, "ground_bed_zmin": 20})


def test_intersections_are_crossroads_passes_when_edges_under_beds():
    assert "intersections_are_crossroads" not in f({"ground_edge_zmax": 19, "ground_bed_zmin": 20})


def test_city_lane_under_wall_fires_when_street_crosses_wall_off_gate():
    # an E-W street punched clean through the wall (crossing both side faces, far from the N/S gates)
    # and drawn OVER it: a lane must run UNDER the rampart except at a gate.
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "wall_z": 5,
        "town_streets": [{"pts": [[100, 500], [900, 500]], "w": 18, "z": 50}],
    }  # crosses x=200 and x=800, far from gates
    assert "city_lane_under_wall" in f(M)


def test_businesses_front_streets_fires_when_shops_are_interior():
    M = {
        "meta": {"scale": "city", "walled": True},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "town_streets": [{"pts": [[250, 250], [750, 250]], "w": 18}],  # the only street, along the top
        "buildings": [bldg(300 + i * 50, 550, kind="shop") for i in range(6)],
    }  # shops marooned in the interior
    assert "businesses_front_streets" in f(M)


def test_alleys_serve_buildings_fires_on_a_lane_to_nowhere():
    # a 400px alley serving only two dwellings - a lane running off into empty space
    M = {
        "meta": {"scale": "city", "walled": True},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "alleys": [{"pts": [[500, 300], [500, 700]], "w": 10}],
        "buildings": [bldg(530, 320, kind="laborer"), bldg(530, 360, kind="laborer")],
    }
    assert "alleys_serve_buildings" in f(M)


def test_alleys_serve_buildings_fires_on_a_redundant_lane_beside_a_street():
    # an alley laid parallel and CLOSE to a street it duplicates: every dwellling fronts the
    # street (it is nearer), so the alley uniquely serves nothing - a redundant lane. Buildings
    # are within the alley's band but closer to the street, so nearest-lane assignment credits
    # them to the street and the alley reads empty.
    blds = [bldg(330 + i * 40, 415, kind="laborer") for i in range(9)]  # y415: 15px from street, 35px from alley
    M = {
        "meta": {"scale": "city", "walled": True},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "town_streets": [{"pts": [[300, 400], [700, 400]], "w": 18}],
        "alleys": [{"pts": [[300, 450], [700, 450]], "w": 10}],  # parallel, 50px south of the street
        "buildings": blds,
    }
    assert "alleys_serve_buildings" in f(M)


def test_no_structure_on_street_fires_on_alley_over_building():
    M = {
        "meta": {"scale": "town", "walled": False},
        "wall": WALL,
        "alleys": [{"pts": [[400, 500], [600, 500]], "w": 10}],
        "buildings": [bldg(500, 500, kind="laborer")],
    }  # the alley runs straight over the dwelling
    assert "no_structure_on_street" in f(M)


def test_every_feature_classified_for_overlap_fires_on_unknown_feature():
    # a new footprint feature nobody added to the _OVERLAP_* registry trips the completeness guard
    M = {"meta": {"scale": "village"}, "watchtowers": [{"x": 100, "y": 100, "w": 20, "h": 20, "rot": 0}]}
    assert "every_feature_classified_for_overlap" in f(M)


def test_every_feature_classified_for_overlap_passes_for_known_features():
    M = {"meta": {"scale": "village"}, "houses": [{"x": 100, "y": 100, "w": 20, "h": 20, "rot": 0, "kind": "plain"}]}
    assert "every_feature_classified_for_overlap" not in f(M)


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
    M = {
        "meta": {"scale": "city", "walled": True},
        "wall": [[100, 100], [3000, 100], [3000, 2500], [100, 2500]],
        "wards": [{"name": "samurai", "boundary": [[1535, 1200], [1535, 1900]], "z": 5}],
        "mausoleums": [{"x": 1508, "y": 1556, "w": 54, "h": 40, "rot": 0, "gate_dir": "west", "ward_walls": []}],
    }
    assert "walled_structure_yields_to_ward_wall" in f(M)


def test_walled_structure_yields_to_ward_wall_skips_compounds_outside_the_wall():
    # a compound OUTSIDE the city wall is not held to the rule (wards are an intramural feature)
    M = _maus_ward([])
    M["mausoleums"][0]["x"], M["mausoleums"][0]["y"] = 50, 50  # west of the wall (x >= 100): outside
    assert "walled_structure_yields_to_ward_wall" not in f(M)


def test_walled_structure_yields_to_ward_wall_skips_tilted_compounds():
    # a tilted compound is not axis-aligned to a fence, so the rule does not apply
    M = _maus_ward([])
    M["mausoleums"][0]["rot"] = 30
    assert "walled_structure_yields_to_ward_wall" not in f(M)


def test_no_structure_on_moat_fires_when_a_structure_sits_on_it():
    M = {
        "meta": {"scale": "city"},
        "wall": [[200, 200], [800, 200], [800, 800], [200, 800]],
        "moat": _MOAT,
        "moat_width": 22,
        "buildings": [
            {"x": 168, "y": 500, "w": 44, "h": 30, "rot": 0, "kind": "laborer"},  # a corner within the moat band
            {"x": 160, "y": 160, "w": 70, "h": 70, "rot": 0, "kind": "laborer"},
        ],
    }  # a moat vertex inside the footprint
    assert "no_structure_on_moat" in f(M)


def test_no_structure_on_pond_fires_when_a_structure_stands_in_it():
    # the Tango west-tower case: a struct corner dipping into the pond ellipse; and the engulfment
    # branch: a footprint swallowing the pond center outright
    M = {
        "meta": {"scale": "village"},
        "pond": [500, 500, 74, 46],
        "houses": [{"x": 545, "y": 530, "w": 30, "h": 22, "rot": 0, "kind": "plain"}],
        "buildings": [{"x": 500, "y": 500, "w": 200, "h": 140, "rot": 0, "kind": "laborer"}],
    }
    assert "no_structure_on_pond" in f(M)


def test_no_structure_on_pond_passes_when_clear():
    M = {"meta": {"scale": "village"}, "pond": [500, 500, 74, 46], "houses": [{"x": 640, "y": 620, "w": 30, "h": 22, "rot": 0, "kind": "plain"}]}
    assert "no_structure_on_pond" not in f(M)


def test_fire_tower_on_wall_overlaps_like_any_structure():
    # fire_towers are in _OVERLAP_STRUCTS, so a tower on the wall trips no_structure_on_wall
    M = {"meta": {"scale": "town", "walled": True}, "wall": [[100, 500], [900, 500]], "gate": [500, 500], "fire_towers": [_tower(500, 500)]}
    assert "no_structure_on_wall" in f(M)


def test_fire_tower_standoff_fires_when_flush_with_a_building():
    # tower half-width 13 + shop half-width 20 -> centers 536 apart leave a 3px gap: too tight
    # (the far building exercises the distance prefilter)
    M = {"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(500, 500)], "buildings": [bldg(536, 500, "laborer", w=40, h=28), bldg(900, 900, "laborer")]}
    fails = f(M)
    assert "fire_tower_standoff" in fails
    assert "no_structure_overlaps" not in fails  # a 3px gap is NOT an overlap - only the new check sees it


# ---- no_structure_on_canal: a canal VERTEX sitting inside a building footprint --------------
# The canal-vs-structure test catches not only a footprint corner near the water but also a
# canal polyline vertex landing INSIDE a (large) footprint while every corner stays clear of the
# thin canal segments. A merchant house straddling the canal's bend must fire.
def test_no_structure_on_canal_fires_when_canal_vertex_inside_footprint():
    M = {
        "buildings": [bldg(500, 500, "merchant_large", w=200, h=200)],
        "canals": [{"poly": [[500, 500], [490, 300]], "w": 4}],  # the [500,500] vertex sits inside the footprint
    }
    assert "no_structure_on_canal" in f(M)


def test_torii_and_religious_clear_of_works_and_ring():
    # GM placement rules (2026-07-21, caught on Tango): torii keep clear of halls/towers/the ring
    # road; religious footprints keep clear of towers/the ring road. An ordinary street through a
    # torii stays legal (only the RING corridor counts), so no street data appears here.
    base = {"meta": {"scale": "city", "ftpx": 3}, "ring_road": [[100, 900], [900, 900]], "ring_road_width": 8, "wall_towers": [{"x": 500, "y": 500, "w": 38, "h": 38}]}
    hall = {"kind": "temple", "x": 300, "y": 300, "w": 43, "h": 28, "label": "Temple of Ebisu"}
    # torii: on the hall / on the tower / on the ring -> fire; standing clear -> pass
    assert "torii_clear_of_halls_towers_ring" in f({**base, "religious": [hall], "torii": [[305, 310, 9]]})
    assert "torii_clear_of_halls_towers_ring" in f({**base, "religious": [hall], "torii": [[505, 512, 9]]})
    assert "torii_clear_of_halls_towers_ring" in f({**base, "religious": [hall], "torii": [[400, 902, 9]]})
    assert "torii_clear_of_halls_towers_ring" not in f({**base, "religious": [hall], "torii": [[300, 380, 9]]})
    # religious: the Tango defect (shrine on a wall tower) and a hall on the ring -> fire; clear -> pass
    shrine_on_tower = {"kind": "small_shrine", "x": 521, "y": 509, "w": 11, "h": 8}
    assert "religious_clear_of_ring_and_towers" in f({**base, "religious": [shrine_on_tower]})
    assert "religious_clear_of_ring_and_towers" in f({**base, "religious": [{**hall, "y": 890}]})
    # ...and a hall standing ON THE EDGE of the roadbed without crossing its centerline: entirely
    # south of y=900 but lapping the bed's 896-904 span. Crossing and proximity are separate
    # branches of the corridor test and this is the one only proximity catches.
    assert "religious_clear_of_ring_and_towers" in f({**base, "religious": [{**hall, "y": 916}]})
    assert "religious_clear_of_ring_and_towers" not in f({**base, "religious": [hall]})


def test_torii_clear_of_walls():
    # GM 2026-07-25, caught on Nagahara: the 7th arch of the Ebisu sando stood IN the samurai ward
    # fence. A torii is a FREESTANDING gateway and a wall is a continuous barrier, so an arch never
    # stands in one - a way through a wall is a GATE. Every wall counts: the city rampart, a ward
    # fence (and its wall-cap), and the perimeter of a walled compound.
    base = {"meta": {"scale": "city", "ftpx": 3}}
    fence = {"name": "samurai", "boundary": [[300, 700], [900, 700]], "z": 10, "wall_caps": []}
    manor = {"x": 400, "y": 400, "w": 60, "h": 40, "rot": 0, "wall_w": 2}
    assert "torii_clear_of_walls" in f({**base, "wards": [fence], "torii": [[600, 699, 9]]})  # the Nagahara defect
    assert "torii_clear_of_walls" not in f({**base, "wards": [fence], "torii": [[600, 680, 9]]})  # the sando stops short
    assert "torii_clear_of_walls" in f({**base, "wall": WALL, "torii": [[500, 52, 9]]})  # standing in the rampart
    assert "torii_clear_of_walls" in f({**base, "wards": [{**fence, "wall_caps": [{"x": 300, "y": 700, "z": 3, "pts": [[290, 690], [290, 760]]}]}], "torii": [[290, 730, 9]]})
    assert "torii_clear_of_walls" in f({**base, "manors": [manor], "torii": [[400, 420, 9]]})  # in a compound wall
    assert "torii_clear_of_walls" not in f({**base, "manors": [manor], "torii": [[400, 460, 9]]})
    assert "torii_clear_of_walls" in f({**base, "governor_mansion": {**manor, "x": 700}, "torii": [[700, 420, 9]]})
    assert "torii_clear_of_walls" in f({**base, "merchant_estates": [{**manor, "y": 200}], "torii": [[430, 200, 9]]})
    assert "torii_clear_of_walls" in f({**base, "mausoleums": [{**manor, "y": 900}], "torii": [[370, 900, 9]]})
    # a run that ENDS inside the arch box, crossing none of its edges, still counts as standing in it
    assert "torii_clear_of_walls" in f({**base, "wards": [{**fence, "boundary": [[599, 700], [601, 701]]}], "torii": [[600, 700, 9]]})


def test_field_outline_matches_planting_fires_on_a_phantom_tail():
    # A DISPERSED map whose field OUTLINE runs 200px past the planted crop (`vis_bbox`) - the over-declared
    # `field_fall` defect. The point of the fixture: `all_houses_field_adjacent` PASSES on this manifest (the
    # farm hugs the phantom tail, so it measures as adjacent) while the farm sits out beyond the last rice.
    # That is the blindness the check exists to cover, so assert BOTH facts.
    base = {
        "meta": {"scale": "hamlet", "down_deg": 90},
        "fields": [{"name": "tail-test", "kind": "paddy", "outline": [[400, 400], [800, 400], [800, 800], [400, 800]], "bbox": [400, 400, 800, 800], "vis_bbox": [400, 400, 800, 600]}],
        "houses": [{"x": 600, "y": 760, "w": 46, "h": 28, "rot": 0, "kind": "plain"}],
    }
    assert "field_outline_matches_planting" in f(base)
    assert "all_houses_field_adjacent" not in f(base)  # the old gate is blind here - that is the whole point
    # outline == planting: the honest field, no tail -> does NOT fire
    good = {**base, "fields": [{**base["fields"][0], "vis_bbox": [400, 400, 800, 800]}]}
    assert "field_outline_matches_planting" not in f(good)
    # a rounding-scale rim (smoothing over irregular plots) is tolerated -> does NOT fire
    rim = {**base, "fields": [{**base["fields"][0], "vis_bbox": [410, 420, 790, 760]}]}
    assert "field_outline_matches_planting" not in f(rim)
    # NUCLEATED is scoped OUT: the cluster never rides the envelope, so a tail is inert there
    nuc = {**base, "meta": {**base["meta"], "nucleated": True}}
    assert "field_outline_matches_planting" not in f(nuc)
    # a field with no vis_bbox recorded is skipped rather than crashing
    novis = {**base, "fields": [{k: v for k, v in base["fields"][0].items() if k != "vis_bbox"}]}
    assert "field_outline_matches_planting" not in f(novis)


def test_dwellings_above_field_drain_fires_on_a_toe_farm():
    # a DISPERSED map (no meta.nucleated), downhill = due S (down_deg=90); a drain runs cross-slope (E-W) at
    # the field's low edge. The first drain segment is DEGENERATE (a repeated point) to exercise that branch.
    base = {
        "meta": {"scale": "hamlet", "down_deg": 90},
        "field_ditches": [{"role": "drain", "field": "toe-test", "poly": [[400, 600], [400, 600], [800, 600]], "w": 4}],
        "fields": [{"name": "toe-test", "kind": "paddy", "outline": [[380, 560], [820, 560], [820, 640], [380, 640]], "bbox": [380, 560, 820, 640]}],
    }
    # a farm 110px DOWNSLOPE (S) of the drain, projecting onto the drain's interior -> in the wet toe -> FIRES
    bad = {**base, "houses": [{"x": 600, "y": 710, "w": 46, "h": 28, "rot": 0, "kind": "plain"}]}
    assert "dwellings_above_field_drain" in f(bad)
    # the same farm UPSLOPE (N) of the drain is on dry ground -> does NOT fire
    good = {**base, "houses": [{"x": 600, "y": 490, "w": 46, "h": 28, "rot": 0, "kind": "plain"}]}
    assert "dwellings_above_field_drain" not in f(good)
    # a flank farm off the drain's END (W of its start) is a legit homestead beside the field -> does NOT fire
    flank = {**base, "houses": [{"x": 250, "y": 710, "w": 46, "h": 28, "rot": 0, "kind": "plain"}]}
    assert "dwellings_above_field_drain" not in f(flank)
    # a NUCLEATED cluster is scoped OUT (governed by cluster_abuts_fields), even sitting downslope
    nuc = {**base, "meta": {**base["meta"], "nucleated": True}, "houses": [{"x": 600, "y": 710, "w": 46, "h": 28, "rot": 0, "kind": "plain"}]}
    assert "dwellings_above_field_drain" not in f(nuc)


def test_village_cluster_compact_fires_on_a_hollow_cluster():
    """A nucleated village whose houses ring a big HOLLOW hull (an over-wide cluster stranding houses far
    from the fields) must fire; the same houses packed into a compact blob must not. The teeth: it measures
    built COVERAGE of the house convex hull, which `cluster_abuts_fields` (a per-house span allowance) misses.
    Village scale + >=12 houses only."""

    base = {
        "meta": {"scale": "village", "nucleated": True},
        "fields": [{"name": "p", "kind": "paddy", "outline": [[0, 400], [800, 400], [800, 900], [0, 900]], "bbox": [0, 400, 800, 900]}],
    }
    ring = [{"x": 400 + 300 * math.cos(t), "y": 200 + 300 * math.sin(t), "w": 24, "h": 18, "rot": 0, "kind": "plain"} for t in [i * 2 * math.pi / 16 for i in range(16)]]
    assert "village_cluster_compact" in f({**base, "houses": ring})
    grid = [{"x": 360 + 26 * (i % 4), "y": 160 + 26 * (i // 4), "w": 24, "h": 18, "rot": 0, "kind": "plain"} for i in range(16)]
    assert "village_cluster_compact" not in f({**base, "houses": grid})
    # a HAMLET (or a small cluster) is legitimately loose - the check is village-scale + >=12 houses only
    assert "village_cluster_compact" not in f({**base, "meta": {"scale": "hamlet", "nucleated": True}, "houses": ring})
    assert "village_cluster_compact" not in f({**base, "houses": ring[:8]})


def test_no_structure_on_paddy_fires_when_a_farmhouse_sinks_a_corner_into_the_crop():
    # house center 10px outside the paddy edge, 44px wide -> its corner reaches ~12px inside
    M = {"meta": {}, "fields": [_paddy_field_rec()], "houses": [{"x": 290, "y": 500, "w": 44, "h": 29, "kind": "plain", "rot": 0}]}
    assert "no_structure_on_paddy" in f(M)


def test_no_structure_on_paddy_passes_when_the_farmhouse_abuts_the_bund():
    M = {"meta": {}, "fields": [_paddy_field_rec()], "houses": [{"x": 276, "y": 500, "w": 44, "h": 29, "kind": "plain", "rot": 0}]}
    assert "no_structure_on_paddy" not in f(M)


def test_every_solid_feature_classified_for_labels_fires_on_an_unclassified_key(monkeypatch):
    """The ratchet: a new solid feature must declare the caption group that may cover it, or be
    excused in _LABEL_EXEMPT. Without this, forgetting is silent - which is exactly how the list
    this replaced fell behind twice."""
    M = _label_map("Temple of Benten", "martial_halls")
    assert "every_solid_feature_classified_for_labels" not in f(M)
    # since feature 024 the gate is a package: each submodule that imported _OVERLAP_STRUCTS holds
    # its own binding, so patch every holder, not just the package namespace
    _new = check_village._OVERLAP_STRUCTS + ("hawk_mews",)
    for _m in [m for m in list(sys.modules.values()) if getattr(m, "__name__", "").startswith("check_village") and hasattr(m, "_OVERLAP_STRUCTS")]:
        monkeypatch.setattr(_m, "_OVERLAP_STRUCTS", _new)
    assert "every_solid_feature_classified_for_labels" in f(M)


def test_city_ward_fence_joins_wall_not_crosses_fires_on_an_end_poking_through():
    # the fence runs up to the north rampart (y50) and out the far side by 10px
    M = _ward_wall([[500, 400], [500, 40]])
    assert "city_ward_fence_joins_wall_not_crosses" in f(M)


def test_city_ward_fence_joins_wall_not_crosses_clear_when_the_end_lands_on_the_centerline():
    # ending ON the wall line is the JOIN: the 2.5px linecap tip stays inside the 5.5px rampart band
    M = _ward_wall([[500, 400], [500, 50]])
    assert "city_ward_fence_joins_wall_not_crosses" not in f(M)


def test_city_ward_fence_joins_wall_not_crosses_reads_the_INK_not_the_vertex():
    # the Minami shape, and the reason the defect shipped green: the end vertex sits only 4px
    # outside the wall - well inside city_ward_fence_meets_wall's 10px tolerance, so THAT check
    # passes - but the fence's round linecap inks 2.5px further, putting 1px of palisade past the
    # rampart's 5.5px half-width. Testing the recorded coordinate alone would see nothing here.
    M = _ward_wall([[500, 400], [500, 46]])
    assert "city_ward_fence_meets_wall" not in f(M)
    assert "city_ward_fence_joins_wall_not_crosses" in f(M)


def test_city_ward_fence_joins_wall_not_crosses_fires_on_a_crossing_mid_run():
    # both ENDS are inside; the fence dives out through the north rampart and back mid-run
    M = _ward_wall([[400, 400], [500, 20], [600, 400]])
    assert "city_ward_fence_joins_wall_not_crosses" in f(M)


def test_city_ward_fence_joins_wall_not_crosses_ignores_a_degenerate_boundary():
    M = _ward_wall([[500, 400]])
    assert "city_ward_fence_joins_wall_not_crosses" not in f(M)


# --- angled-building captions (GM 2026-08-02): tilted label records carry the tilt at [7] -------
def test_no_label_overlaps_judges_tilted_pairs_by_their_quads():
    # two captions along the same -30 deg lane: their AABBs cross massively, their glyph runs lie
    # parallel 14px apart - the box test would false-flag what the reader sees as two clean lines
    M = {"meta": {}, "labels": [[100, 100, 200, 110, 1, "a", None, -30.0], [100, 114, 200, 124, 2, "b", None, -30.0]]}
    assert "no_label_overlaps" not in f(M)


def test_no_label_overlaps_fires_when_tilted_glyphs_actually_cross():
    M = {"meta": {}, "labels": [[100, 100, 200, 110, 1, "a", None, -30.0], [100, 102, 200, 112, 2, "b", None, -30.0]]}
    assert "no_label_overlaps" in f(M)


def test_label_hugs_its_referent_measures_the_tilted_quad():
    # the tilted run's low corner dips to ~4px off the subject box - hugging - where its own
    # pre-tilt box floats 38px above the subject
    hug = [100, 100, 240, 112, 1, "gate market", [90, 150, 150, 190], -30.0]
    assert "label_hugs_its_referent" not in f({"meta": {}, "labels": [hug]})
    adrift = [100, 100, 240, 112, 1, "gate market", [600, 600, 700, 650], -30.0]
    assert "label_hugs_its_referent" in f({"meta": {}, "labels": [adrift]})


def test_religious_matches_scale_capital_takes_temples():
    """A capital is the city tier at 4x - temples, same as a provincial city. The scale map did
    not know 'capital' and demanded NO religious building at all (feature 020)."""
    M = _capital_manifest()
    M["religious"] = [{"kind": "temple", "label": "Temple of Benten", "x": 500, "y": 500, "w": 50, "h": 33, "torii_count": 1}]
    M["torii"] = [[500, 560, 1]]
    assert "religious_matches_scale" not in f(M)


def test_businesses_on_street_measured_from_bed_edge():
    """021: the on-street reach is bed half-width + 85 real ft - a shop hugging a wide trunk
    road's paving edge is ON the street; one two blocks out is not."""
    M = _capital_manifest(scale="city")
    M["road"] = [[500, 0], [500, 1000]]
    M["road_width"] = 26
    M["buildings"] = [{"kind": "shop", "x": 530, "y": 400, "w": 8, "h": 6}]  # 30px out: edge-hugging
    assert "businesses_front_streets" not in f(M)
    M["buildings"] = [{"kind": "shop", "x": 620, "y": 400, "w": 8, "h": 6}]  # 120px out: interior
    assert "businesses_front_streets" in f(M)
