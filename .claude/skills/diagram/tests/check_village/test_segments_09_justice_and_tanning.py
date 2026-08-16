"""Split from test_checks.py by feature 025 - see tests/check_village/CLAUDE.md for the index."""

import check_village
from tests.check_village._builders import _TY_DIAG, _WHY, WALL, _dw, _fall_map, _justice_town, _side_map, _tower, _ty_map, _waived_map, _wf_map, bldg, bstone, exground, f, house, pspot


# ---- streets_have_buildings: the case that motivated this file ----------------------------
# A building beside a north-south lane but FRONTING the east-west cross-street (it is nearer
# the cross) must NOT count as serving the lane - so a lane with only such neighbors reads as
# empty. The old proximity-only check missed this; this fixture pins the fix.
def test_streets_have_buildings_fires_when_building_fronts_the_other_street():
    M = {
        "meta": {"scale": "town", "walled": True},
        "wall": WALL,
        "town_streets": [
            {"pts": [[700, 380], [700, 620]], "w": 18},  # the lane (should read empty)
            {"pts": [[200, 500], [950, 500]], "w": 22, "main": True},  # the cross it actually fronts
        ],
        "buildings": [bldg(760, 500)],  # nearest the cross, not the lane
    }
    assert "streets_have_buildings" in f(M)


def test_streets_have_buildings_passes_when_a_building_fronts_the_street():
    M = {
        "meta": {"scale": "town", "walled": True},
        "wall": WALL,
        "town_streets": [{"pts": [[700, 400], [700, 600]], "w": 18, "main": True}],
        "buildings": [bldg(720, 500)],  # nearest THIS street, covers its short length
    }
    assert "streets_have_buildings" not in f(M)


# ---- wall_hugs_the_town: a wall that encloses large empty corner space ---------------------
# Walls are expensive; one should hug the built town. A single building tucked in one corner of
# a big square enclosure leaves three faces running over empty space - that must fire. A town
# whose buildings sit near every face must NOT. (The hill, when present, counts as occupancy -
# a wall may legitimately climb/skirt terrain rather than leveling it.)
def test_wall_hugs_the_town_fires_on_empty_corner_space():
    M = {"meta": {"scale": "town", "walled": True}, "wall": WALL, "buildings": [bldg(120, 120)]}  # one building, far from the right/bottom faces
    assert "wall_hugs_the_town" in f(M)


def test_wall_hugs_the_town_passes_when_buildings_line_every_face():
    near = [bldg(x, y) for x in (120, 500, 880) for y in (120, 500, 880)]  # a 3x3 grid hugging all faces
    M = {"meta": {"scale": "town", "walled": True}, "wall": WALL, "buildings": near}
    assert "wall_hugs_the_town" not in f(M)


def test_walled_town_has_gate_market_fires_when_no_market_outside():
    # the only business sits INSIDE the wall, so there is no extramural market at the gate
    M = {"meta": {"scale": "town", "walled": True}, "wall": WALL, "gate": [500, 950], "buildings": [bldg(500, 500, kind="merchant")]}
    assert "walled_town_has_gate_market" in f(M)


def test_walled_town_gate_market_opt_out_suppresses_the_check():
    # meta(gate_market=False) - a purely military or suppressed gate - skips the requirement
    M = {"meta": {"scale": "town", "walled": True, "gate_market": False}, "wall": WALL, "gate": [500, 950], "buildings": [bldg(500, 500, kind="merchant")]}
    assert "walled_town_has_gate_market" not in f(M)


def test_walled_town_commoners_inside_walls_fires_on_an_outside_laborer():
    M = {
        "meta": {"scale": "town", "walled": True},
        "wall": [[300, 300], [700, 300], [700, 700], [300, 700]],
        "gate": [500, 700],
        "buildings": [_dw(900, 500, "laborer")],
        "fire_towers": [_tower(500, 500)],
    }
    assert "walled_town_commoners_inside_walls" in f(M)


def test_walled_town_commoners_inside_walls_allows_burakumin_and_gate_merchants():
    M = {
        "meta": {"scale": "town", "walled": True},
        "wall": [[300, 300], [700, 300], [700, 700], [300, 700]],
        "gate": [500, 700],
        "buildings": [_dw(900, 500, "burakumin"), _dw(520, 780, "merchant"), _dw(500, 500, "laborer")],
        "fire_towers": [_tower(500, 500)],
    }
    assert "walled_town_commoners_inside_walls" not in f(M)


def test_settlement_has_tanning_yard_fires_when_a_watered_town_keeps_none():
    M = _ty_map()
    M.pop("tanning_yards")
    assert "settlement_has_tanning_yard" in f(M)


def test_settlement_has_tanning_yard_passes_when_the_settlement_has_no_water():
    M = _ty_map(streams=[])  # no watercourse -> no tannery is CORRECT, not a defect
    M.pop("tanning_yards")
    assert "settlement_has_tanning_yard" not in f(M)


def test_settlement_has_tanning_yard_passes_when_there_is_no_burakumin_quarter():
    M = _ty_map(buildings=[bldg(200, 200)])
    M.pop("tanning_yards")
    assert "settlement_has_tanning_yard" not in f(M)


def test_tanning_yard_on_water_fires_when_the_yard_sits_on_dry_ground():
    M = _ty_map(tanning_yards=[{"x": 180, "y": 500, "w": 58, "h": 41, "rot": 0, "label": "tanning yard"}])
    assert "tanning_yard_on_water" in f(M)


def test_tanning_yard_on_water_passes_on_the_bank():
    assert "tanning_yard_on_water" not in f(_ty_map())


def test_tanning_yard_outside_walls_fires_when_the_work_is_inside():
    M = _ty_map(
        meta={"scale": "city", "walled": True, "ftpx": 3},
        wall=WALL,
        tanning_yards=[{"x": 500, "y": 500, "w": 27, "h": 17, "rot": 0, "label": "tanning yard"}],
    )
    assert "tanning_yard_outside_walls" in f(M)


def test_tanning_yard_outside_walls_passes_beyond_the_rampart():
    M = _ty_map(
        meta={"scale": "city", "walled": True, "ftpx": 3},
        wall=WALL,
        streams=[{"poly": [[500, 100], [500, 1300]], "w": 8}],
        tanning_yards=[{"x": 500, "y": 1100, "w": 27, "h": 17, "rot": 0, "label": "tanning yard"}],
    )
    assert "tanning_yard_outside_walls" not in f(M)


def test_tanning_yard_clear_of_dwellings_fires_when_a_house_stands_beside_it():
    M = _ty_map(buildings=[bldg(200, 200, kind="burakumin"), bldg(466, 560)])  # a merchant 60 ft away
    assert "tanning_yard_clear_of_dwellings" in f(M)


def test_tanning_yard_clear_of_dwellings_exempts_the_burakumin_quarter():
    # the same 60 ft gap, but the neighbor is burakumin: they live on the ground they work
    M = _ty_map(buildings=[bldg(466, 560, kind="burakumin")])
    assert "tanning_yard_clear_of_dwellings" not in f(M)


def test_tanning_yard_clear_of_water_fires_when_the_ground_crosses_the_bank():
    # the yard edge 10 px past the stream's drawn edge - the real Tango defect: the tamped
    # ground read as a platform over the water
    M = _ty_map(tanning_yards=[{"x": 476, "y": 500, "w": 58, "h": 41, "rot": 0, "label": "tanning yard"}])
    assert "tanning_yard_clear_of_water" in f(M)


def test_tanning_yard_clear_of_water_fires_when_a_ditch_threads_under_the_rect():
    # a thin field drain crossing UNDER the yard between its corners - the real Hoshizora
    # defect; corner-sampling cannot see this, seg_to_rect_dist can
    M = _ty_map(field_ditches=[{"poly": [[400, 300], [466, 500], [530, 700]], "role": "drain", "field": "t-ne", "w": 2.2, "w_tail": 2.2}])
    assert "tanning_yard_clear_of_water" in f(M)


def test_tanning_yard_clear_of_water_fires_when_the_yard_sits_in_the_pond():
    M = _ty_map(pond=[466, 530, 30, 20])
    assert "tanning_yard_clear_of_water" in f(M)


def test_tanning_yard_clear_of_water_fires_when_the_river_swallows_a_corner():
    # tested at the river's REAL half-width (the lumber-yard lesson): a 60 px river's edge reaches
    # 30 px out and swallows the yard's corner while its CENTERLINE stands 23 px clear of the
    # ground - far past the generic ~6 px stroke the village checks assume
    M = _ty_map(river={"pts": [[510, 100], [510, 900]], "w": 60})
    assert "tanning_yard_clear_of_water" in f(M)


def test_tanning_yard_clear_of_water_passes_on_the_bank():
    # the baseline yard abuts the stream's edge with the frames overhanging - the design
    assert "tanning_yard_clear_of_water" not in f(_ty_map())


def test_tanning_yard_clear_of_fields_fires_on_a_paddy():
    M = _ty_map(fields=[{"name": "t-ne", "kind": "paddy", "outline": [[300, 400], [480, 400], [480, 600], [300, 600]], "bbox": [300, 400, 480, 600]}])
    assert "tanning_yard_clear_of_fields" in f(M)


def test_tanning_yard_clear_of_fields_fires_on_a_dry_plot():
    M = _ty_map(dry_plots=[{"poly": [[430, 480], [470, 480], [470, 520], [430, 520]], "crop": "millet"}])
    assert "tanning_yard_clear_of_fields" in f(M)


def test_tanning_yard_clear_of_fields_fires_when_the_yard_engulfs_a_flower_patch():
    # the poly entirely inside the rect: no edges cross, only the vertex-in-rect test sees it
    M = _ty_map(flower_fields=[{"kind": "chrysanthemum", "outline": [[460, 495], [470, 495], [470, 505], [460, 505]]}])
    assert "tanning_yard_clear_of_fields" in f(M)


def test_tanning_yard_clear_of_fields_passes_beside_the_field():
    # abutting cropland is fine - marginal bank ground borders the fields; only OVERLAP fires
    M = _ty_map(fields=[{"name": "t-ne", "kind": "paddy", "outline": [[300, 400], [430, 400], [430, 600], [300, 600]], "bbox": [300, 400, 430, 600]}])
    assert "tanning_yard_clear_of_fields" not in f(M)


def test_tanning_yard_square_to_its_water_fires_on_an_axis_aligned_yard_on_a_diagonal_bank():
    M = _ty_map(
        streams=[{"poly": _TY_DIAG, "w": 8, "flow": "forward", "flow_deg": 56.3, "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}}],
        tanning_yards=[{"x": 466, "y": 473, "w": 58, "h": 41, "rot": 0, "label": "tanning yard"}],
    )
    assert "tanning_yard_square_to_its_water" in f(M)


def test_tanning_yard_square_to_its_water_passes_when_the_yard_follows_the_bank():
    M = _ty_map(
        streams=[{"poly": _TY_DIAG, "w": 8, "flow": "forward", "flow_deg": 56.3, "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}}],
        tanning_yards=[{"x": 476, "y": 466, "w": 58, "h": 41, "rot": 56.3, "label": "tanning yard"}],
    )
    assert "tanning_yard_square_to_its_water" not in f(M)


def test_tanning_yard_square_to_its_water_accepts_a_180_degree_flip():
    # the same ground with the water side on the other long edge is the same alignment
    M = _ty_map(
        streams=[{"poly": _TY_DIAG, "w": 8, "flow": "forward", "flow_deg": 56.3, "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}}],
        tanning_yards=[{"x": 476, "y": 466, "w": 58, "h": 41, "rot": 236.3, "label": "tanning yard"}],
    )
    assert "tanning_yard_square_to_its_water" not in f(M)


def test_tanning_yard_square_to_its_water_passes_at_a_confluence_when_square_to_either_course():
    # the yard follows the vertical stream; the 40 deg course also runs past it, and being 50 deg
    # off THAT one is not a defect - a yard on two banks legitimately lies along one of them
    M = _ty_map(
        streams=[
            {"poly": [[500, 100], [500, 900]], "w": 8, "flow": "forward", "flow_deg": 90.0, "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}},
            {"poly": [[361, 470], [552, 630]], "w": 8, "flow": "forward", "flow_deg": 39.9, "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}},
        ],
        tanning_yards=[{"x": 466, "y": 500, "w": 58, "h": 41, "rot": 90, "label": "tanning yard"}],
    )
    assert "tanning_yard_square_to_its_water" not in f(M)


def test_tanning_yard_square_to_its_water_abstains_when_no_bank_is_in_reach():
    # a yard on dry ground is tanning_yard_on_water's defect; do not report it twice
    M = _ty_map(tanning_yards=[{"x": 180, "y": 500, "w": 58, "h": 41, "rot": 0, "label": "tanning yard"}])
    assert "tanning_yard_on_water" in f(M)
    assert "tanning_yard_square_to_its_water" not in f(M)


def test_tanning_yard_square_to_its_water_measures_a_wide_course_from_its_BANK():
    # a 80 ft river's centerline is 50 px from this yard - out of the 20 ft reach - but its bank is
    # 10 px away, which is the edge the yard actually works. Read from the centerline the check
    # would abstain here; read from the bank it catches the yard sitting 56 deg across it.
    M = _ty_map(
        river={"poly": [[216, 342], [354, 550]], "w": 80},
        tanning_yards=[{"x": 200, "y": 473, "w": 58, "h": 41, "rot": 0, "label": "tanning yard"}],
    )
    assert "tanning_yard_square_to_its_water" in f(M)


def test_tanning_yard_square_to_its_water_ignores_a_repeated_polyline_point():
    # a duplicated vertex has no bearing - read as 0 deg it would wave this axis-aligned yard
    # through, since the point itself is the nearest bit of water to the rect
    M = _ty_map(
        streams=[{"poly": [[400, 300], [500, 450], [500, 450], [600, 600]], "w": 8, "flow": "forward", "flow_deg": 56.3, "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}}],
        tanning_yards=[{"x": 466, "y": 473, "w": 58, "h": 41, "rot": 0, "label": "tanning yard"}],
    )
    assert "tanning_yard_square_to_its_water" in f(M)


def test_water_flow_declared_fires_when_a_watered_map_declares_no_bearing():
    M = _wf_map(meta={"scale": "town", "walled": False, "ftpx": 1, "down_deg": 90})
    assert "water_flow_declared" in f(M)


def test_water_flow_consistent_with_slope_fires_when_water_would_run_uphill():
    # 90 deg or more off the fall = a net uphill component, which gravity forbids
    M = _wf_map(meta={"scale": "town", "walled": False, "ftpx": 1, "down_deg": 90, "water_flow": 270})
    assert "water_flow_consistent_with_slope" in f(M)


def test_water_flow_consistent_with_slope_passes_a_near_contour_divergence():
    # 85 deg off the fall is a CONTOUR work (a canal is built near-parallel to the contours),
    # realistic and must not be flagged - only crossing 90 is impossible
    M = _wf_map(meta={"scale": "town", "walled": False, "ftpx": 1, "down_deg": 90, "water_flow": 5})
    assert "water_flow_consistent_with_slope" not in f(M)


def test_watercourses_declare_flow_fires_on_an_untagged_course():
    M = _wf_map(streams=[{"poly": [[500, 100], [500, 900]], "w": 8}])
    assert "watercourses_declare_flow" in f(M)


def test_watercourses_declare_flow_accepts_a_level_canal():
    M = _wf_map(canals=[{"poly": [[100, 500], [900, 500]], "w": 12, "flow": "level", "flow_deg": None}])
    assert "watercourses_declare_flow" not in f(M)


def test_watercourses_flow_downstream_fires_on_a_course_running_against_the_bearing():
    M = _wf_map(streams=[{"poly": [[500, 900], [500, 100]], "w": 8, "flow": "forward", "flow_deg": 270.0}])
    assert "watercourses_flow_downstream" in f(M)


def test_watercourses_flow_downstream_exempts_the_level_canal():
    # Nagahara's cargo canal runs against the drainage and is CORRECT - it is a navigation cut
    M = _wf_map(canals=[{"poly": [[900, 500], [100, 500]], "w": 12, "flow": "level", "flow_deg": None}])
    assert "watercourses_flow_downstream" not in f(M)


def test_moat_declares_circulation_fires_on_a_moat_with_no_inlet_or_outlet():
    M = _wf_map(meta={"scale": "city", "walled": True, "ftpx": 3, "water_flow": 90}, wall=WALL, moat=WALL)
    assert "moat_declares_circulation" in f(M)


def test_settlement_has_tanning_yard_honors_the_declared_opt_out():
    # meta(tannery=False): a settlement with water but no legitimate site on it (Tango)
    M = _ty_map(meta={"scale": "city", "walled": False, "ftpx": 3, "tannery": False})
    M.pop("tanning_yards")
    assert "settlement_has_tanning_yard" not in f(M)


def test_tanning_yard_discharges_to_nothing_drawn_from_fires_on_a_course_feeding_a_pond():
    M = _ty_map(streams=[{"poly": [[500, 100], [500, 900]], "w": 8, "flow": "forward", "flow_deg": 90.0, "frm": {"kind": "offmap"}, "to": {"kind": "pond"}}])
    assert "tanning_yard_discharges_to_nothing_drawn_from" in f(M)


def test_tanning_yard_discharges_to_nothing_drawn_from_passes_when_it_ends_off_map():
    assert "tanning_yard_discharges_to_nothing_drawn_from" not in f(_ty_map())


def test_tanning_yard_discharges_reads_the_sink_by_FLOW_not_polyline_order():
    # stored downstream-first: frm is the SINK. Reading frm/to by position would call this clean.
    M = _ty_map(streams=[{"poly": [[500, 900], [500, 100]], "w": 8, "flow": "reverse", "flow_deg": 270.0, "frm": {"kind": "pond"}, "to": {"kind": "offmap"}}])
    assert "tanning_yard_discharges_to_nothing_drawn_from" in f(M)


def test_tanning_yard_below_every_intake_fires_on_a_tap_downstream_of_the_yard():
    # the real Tango defect: a field taps the yard's own course BELOW it
    M = _ty_map(channels=[{"poly": [[500, 700], [700, 720]], "frm": {"kind": "stream"}, "to": {"kind": "field", "name": "f1"}, "w": 2.5}])
    assert "tanning_yard_below_every_intake" in f(M)


def test_tanning_yard_below_every_intake_passes_when_the_tap_is_upstream():
    M = _ty_map(channels=[{"poly": [[500, 300], [700, 320]], "frm": {"kind": "stream"}, "to": {"kind": "field", "name": "f1"}, "w": 2.5}])
    assert "tanning_yard_below_every_intake" not in f(M)


def test_tanning_yard_downstream_checks_skip_a_yard_with_no_watercourse_at_all():
    # degenerate but the guard is real: no course to reason about means no downstream verdict
    M = _ty_map(streams=[])
    assert "tanning_yard_discharges_to_nothing_drawn_from" not in f(M)
    assert "tanning_yard_below_every_intake" not in f(M)


def test_tanning_yard_below_every_intake_ignores_an_intake_on_a_DIFFERENT_course():
    # Hoshizora's real situation: the town's intakes are on a watercourse the yard's water never
    # reaches, so they must not be charged against it
    M = _ty_map(channels=[{"poly": [[100, 700], [180, 720]], "frm": {"kind": "stream"}, "to": {"kind": "field", "name": "f1"}, "w": 2.5}])
    assert "tanning_yard_below_every_intake" not in f(M)


def test_settlement_declares_a_land_fall_fires_when_nothing_declares_a_slope():
    # the hole that let both provincial cities skip every drainage-slope rule behind a green gate
    assert "settlement_declares_a_land_fall" in f(_fall_map())


def test_settlement_declares_a_land_fall_accepts_a_map_level_bearing():
    M = _fall_map()
    M["meta"]["down_deg"] = 90
    assert "settlement_declares_a_land_fall" not in f(M)


def test_settlement_declares_a_land_fall_accepts_per_field_falls_with_no_map_bearing():
    # what a settlement ringed by farmland needs: its fans drain several ways, so no single bearing
    M = _fall_map()
    M["fields"][0]["down_deg"] = 90
    assert "settlement_declares_a_land_fall" not in f(M)


def test_settlement_declares_a_land_fall_is_not_satisfied_by_water_flow_alone():
    # water_flow is where the water GOES; down_deg is how the land LIES. Different facts.
    M = _fall_map()
    M["meta"]["water_flow"] = 90
    assert "settlement_declares_a_land_fall" in f(M)


def test_town_has_punishment_spot_fires_when_the_seat_keeps_none():
    assert "town_has_punishment_spot" in f(_justice_town(punishment_spots=[]))


def test_town_has_punishment_spot_can_be_opted_out():
    M = _justice_town(punishment_spots=[])
    M["meta"] = {**M["meta"], "punishment_spot": False}
    assert "town_has_punishment_spot" not in f(M)


def test_town_has_execution_ground_fires_when_the_seat_keeps_none():
    assert "town_has_execution_ground" in f(_justice_town(execution_grounds=[]))


def test_town_has_execution_ground_can_be_opted_out():
    M = _justice_town(execution_grounds=[])
    M["meta"] = {**M["meta"], "execution_ground": False}
    assert "town_has_execution_ground" not in f(M)


def test_punishment_spot_in_the_core_fires_on_a_spot_out_in_the_fields():
    # Out by the execution ground, where nobody passes it - a display nobody sees is not a display.
    assert "punishment_spot_in_the_core" in f(_justice_town(punishment_spots=[pspot(1600, 1300)]))


def test_punishment_spot_in_the_core_fires_outside_a_rampart():
    M = _justice_town(wall=WALL, punishment_spots=[pspot(520, 1020)])
    assert "punishment_spot_in_the_core" in f(M)  # the core sits outside this fixture's square wall


def test_punishment_spot_by_the_traffic_fires_on_a_spot_off_the_street():
    # In among the houses but ~150 ft back from the road: shaming is sited on foot traffic.
    assert "punishment_spot_by_the_traffic" in f(_justice_town(punishment_spots=[pspot(520, 850)]))


def test_execution_ground_outside_the_settlement_fires_on_a_ground_among_the_dwellings():
    assert "execution_ground_outside_the_settlement" in f(_justice_town(execution_grounds=[exground(520, 1000)]))


def test_execution_ground_outside_the_settlement_fires_inside_a_wall():
    M = _justice_town(wall=WALL, execution_grounds=[exground(500, 500)], boundary_markers=[bstone(480, 480)])
    assert "execution_ground_outside_the_settlement" in f(M)


def test_execution_ground_by_the_road_fires_on_a_ground_hidden_off_the_highway():
    # The posts are meant to be read from the road; 400 ft back into a field deters nobody.
    M = _justice_town(execution_grounds=[exground(1500, 1400)], boundary_markers=[bstone(1100, 1200)])
    assert "execution_ground_by_the_road" in f(M)


def test_execution_ground_past_the_boundary_marker_fires_when_the_stone_is_missing():
    assert "execution_ground_past_the_boundary_marker" in f(_justice_town(boundary_markers=[]))


def test_execution_ground_past_the_boundary_marker_fires_when_the_stone_is_beyond_the_ground():
    # A stone further out than the ground marks nothing - the ground would sit INSIDE the boundary.
    assert "execution_ground_past_the_boundary_marker" in f(_justice_town(boundary_markers=[bstone(1800, 1060)]))


def test_execution_ground_past_the_boundary_marker_fires_when_the_stone_is_off_the_road():
    # Between the settlement and the ground, but sitting in open field 300 ft off the highway. The
    # between-ness arithmetic alone accepted this and it is still wrong: sae blocks pollution where
    # the ROAD leaves clean ground, so a stone that marks no road marks nothing. (Found by eye on a
    # rendered Nagahara while every check was green - hence this fixture.)
    assert "execution_ground_past_the_boundary_marker" in f(_justice_town(boundary_markers=[bstone(1100, 1300)]))


def test_execution_ground_past_the_boundary_marker_fires_when_the_stone_stands_among_the_dwellings():
    # On the road and correctly between core and ground, but 67 real ft from the nearest house - a
    # dosojin inside the built edge marks nothing, exactly like one inside a rampart. This is the
    # UNWALLED case, and it is the one that shipped: "outside" was tested as `not _inwall_j(...)`,
    # which is False for every point on a map with no wall, so the clause passed anything at all and
    # Ubame's stone stood among the west-end shops with a green gate (GM, 2026-07-26).
    assert "execution_ground_past_the_boundary_marker" in f(_justice_town(boundary_markers=[bstone(620, 1000)]))


def test_execution_ground_past_the_boundary_marker_accepts_a_walled_towns_stone_beside_the_suburb():
    # The deliberate divergence from the GROUND's version of "outside", pinned so nobody unifies
    # them: where there is a rampart the wall IS the edge, so a stone beyond it is past the line
    # even with roadside suburb against it (Hirameki's stands 104 ft from an extramural laborer
    # row). The ground keeps both clauses because kegare is a separation from people wherever they
    # live; the stone only has to say where clean ground ends.
    M = _justice_town(wall=WALL, buildings=[bldg(1000, 1010, kind="burakumin"), bldg(1210, 1010, kind="laborer")])
    assert "execution_ground_past_the_boundary_marker" not in f(M)


def test_execution_ground_clear_of_the_dead_fires_beside_the_burial_ground():
    M = _justice_town(cemeteries=[{"x": 1560, "y": 1060, "w": 100, "h": 80, "rot": 0, "parish": False}])
    assert "execution_ground_clear_of_the_dead" in f(M)


def test_execution_ground_clear_of_the_dead_fires_beside_a_cremation_ground():
    # The rule covers the whole funerary family, not the cemetery alone.
    M = _justice_town(cremation_grounds=[{"x": 1540, "y": 1100, "w": 75, "h": 52, "rot": 0}])
    assert "execution_ground_clear_of_the_dead" in f(M)


def test_execution_ground_off_the_farmland_fires_on_a_ground_in_a_paddy():
    M = _justice_town(fields=[{"name": "north", "kind": "paddy", "outline": [[1400, 960], [1700, 960], [1700, 1200], [1400, 1200]], "bbox": [1400, 960, 1700, 1200], "plots": [], "down_deg": 90}])
    assert "execution_ground_off_the_farmland" in f(M)


def test_execution_ground_on_the_outcast_side_fires_on_the_opposite_side():
    # West of the core while the burakumin quarter lies east - pollution runs ONE way out of a town.
    M = _justice_town(execution_grounds=[exground(-600, 1060)], boundary_markers=[bstone(0, 1020)])
    assert "execution_ground_on_the_outcast_side" in f(M)


def test_execution_ground_on_the_outcast_side_is_skipped_without_a_quarter():
    # A settlement with no burakumin dwellings has no outcast side to measure against.
    M = _justice_town(buildings=[], execution_grounds=[exground(-600, 1060)], boundary_markers=[bstone(0, 1020)])
    assert "execution_ground_on_the_outcast_side" not in f(M)


def test_tanning_yard_on_the_outcast_side_fires_when_the_yard_faces_the_other_way():
    # core ~(290,410) sits BETWEEN the quarter (northwest) and the yard at (466,500) to the southeast
    assert "tanning_yard_on_the_outcast_side" in f(_side_map([(200, 200), (240, 200)], [(360, 620), (360, 620)]))


def test_tanning_yard_on_the_outcast_side_passes_when_far_but_on_the_same_side():
    """The Nagahara case: ~300px of separation is FINE as long as the bearing agrees - the rule is
    directional, and a metric rule here would condemn a correct city map."""
    assert "tanning_yard_on_the_outcast_side" not in f(_side_map([(380, 800), (420, 800)], [(200, 200), (240, 200)]))


def test_tanning_yard_on_the_outcast_side_abstains_with_no_ordinary_dwellings():
    """All-burakumin fixture: the core lands ON the quarter, so no bearing exists and the rule has
    nothing to say. It must abstain rather than fire on a degenerate zero-length vector."""
    assert "tanning_yard_on_the_outcast_side" not in f(_ty_map())


def test_a_waiver_excuses_the_named_check():
    assert "tanning_yard_on_the_outcast_side" not in f(_waived_map({"tanning_yard_on_the_outcast_side": _WHY}))


def test_waivers_are_documented_fires_on_a_reason_too_thin_to_be_one():
    assert "waivers_are_documented" in f(_waived_map({"tanning_yard_on_the_outcast_side": "by design"}))


def test_waivers_are_documented_fires_when_the_reason_is_not_even_text():
    assert "waivers_are_documented" in f(_waived_map({"tanning_yard_on_the_outcast_side": True}))


def test_waivers_are_live_fires_on_a_waiver_whose_check_now_passes():
    """The rot this prevents: a map keeps collecting waivers for defects it no longer has, and ends
    up exempt from rules nobody remembers it was ever breaking."""
    M = _waived_map({"tanning_yard_on_the_outcast_side": _WHY, "tanning_yard_on_water": _WHY})
    assert "waivers_are_live" in f(M)


def test_waivers_are_live_fires_on_a_name_no_check_has():
    assert "waivers_are_live" in f(_waived_map({"tanning_yard_on_the_outcast_side": _WHY, "tanning_yard_on_watr": _WHY}))


def test_a_waived_check_prints_WAIVE_and_a_closing_summary(capsys):
    """A waiver must never read as a PASS in the gate output - the whole point is that the override
    is visible to whoever runs it."""
    check_village.gate(_waived_map({"tanning_yard_on_the_outcast_side": _WHY}), verbose=True)
    out = capsys.readouterr().out
    assert "WAIVE tanning_yard_on_the_outcast_side" in out
    assert "WAIVED tanning_yard_on_the_outcast_side: The Emperor lies southeast" in out


def test_execution_ground_no_nearer_the_houses_than_its_stone_fires_when_the_ground_is_further_in():
    """The GM's formulation, 2026-07-27: the stone should be closer to the town's edge than the
    ground. The between-ness test above cannot see this - it compares two distances to the core
    CENTROID, which orders the pair radially about one point while a settlement is not a disc. Here
    the ground keeps its 126 px of kegare clearance and is still 10 px further IN than the stone that
    is supposed to bound it, so both of the older rules are satisfied and the map is still wrong."""
    M = _justice_town(boundary_markers=[bstone(1160, 1010)], execution_grounds=[exground(1500, 1060)], houses=[house(440 + 30 * i, 940) for i in range(6)] + [house(1500, 1230)])
    assert "execution_ground_past_the_boundary_marker" not in f(M)  # the centroid arithmetic is satisfied...
    assert "execution_ground_no_nearer_the_houses_than_its_stone" in f(M)  # ...and the ground is still inside the line


def test_execution_ground_no_nearer_the_houses_than_its_stone_measures_a_walled_seat_to_its_RAMPART():
    """And the settlement edge is the WALL where there is one. Measuring a walled city to its
    nearest dwelling lets an isolated farmstead in the hinterland stand for the town - Tango's
    ground sits in the extramural fields with a farmhouse further out than itself, which read as
    'nearer the town' than a stone plainly between the city and it."""
    M = _justice_town(wall=WALL, boundary_markers=[bstone(1000, 1010)], execution_grounds=[exground(1500, 1060)], houses=[house(440 + 30 * i, 940) for i in range(6)] + [house(1620, 1060)])
    assert "execution_ground_no_nearer_the_houses_than_its_stone" not in f(M)
