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

import json
import pathlib

import check_village
import settlement

WALL = [[50, 50], [950, 50], [950, 950], [50, 950]]  # a simple square enclosure


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


# ---- a feature-footprint overlap check ----------------------------------------------------
def test_no_structure_on_wall_fires():
    # on the TOP rampart segment - note the wall is an OPEN polyline (the closing edge is not
    # a real wall segment, since a real rampart is an arc anchored to a hill), so the building
    # must sit on one of its drawn segments, not the implicit closure.
    M = {"meta": {"scale": "town", "walled": True}, "wall": WALL, "buildings": [bldg(400, 50)]}
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


# ---- channels_join_streams_at_confluence (a drain culvert reaches INTO the receiving bed) ----
def _sink_channel(end):
    return {"poly": [[end[0] - 60, end[1] - 40], end], "frm": {"kind": "drain"}, "to": {"kind": "stream"}}


def test_channels_join_streams_at_confluence_fires_when_the_mouth_dies_short():
    # the stream runs N-S at x=400 (w 9 -> half-width 4.5); a culvert ending 20px from the
    # centerline passes the 30px anchor but never reaches the water - no confluence
    M = {"meta": {}, "streams": [{"poly": [[400, 100], [400, 900]], "w": 9}], "channels": [_sink_channel([380, 500])]}
    assert "channels_join_streams_at_confluence" in f(M)


def test_channels_join_streams_at_confluence_passes_when_the_mouth_reaches_the_bed():
    M = {"meta": {}, "streams": [{"poly": [[400, 100], [400, 900]], "w": 9}], "channels": [_sink_channel([400, 500])]}
    assert "channels_join_streams_at_confluence" not in f(M)


# ---- field_ditches_reach_source_and_sink (role-aware: supply->source, drain->sink) ----------
def test_field_ditches_reach_source_and_sink_fires_when_ungrounded():
    # a supply ditch with no pond source AND a drain with no runoff sink - both dangle (the failure
    # path of the role-aware grounding). The GOOD case is covered by the real maps (kikuta passes with
    # its full pond->canal->cascade->drain->off-map network; the wip Hoshigaoka likewise).
    M = {"field_ditches": [{"poly": [[300, 300], [500, 300]], "role": "main", "field": "f"}, {"poly": [[300, 600], [500, 600]], "role": "drain", "field": "f"}]}
    assert "field_ditches_reach_source_and_sink" in f(M)


def test_structures_clear_of_dry_plots_fires_when_a_farmstead_stands_on_a_hem_strip():
    # GM 2026-07: farmsteads (house + threshing yard) stood on Tango's fn1/nw1 dry hems - the
    # plots were guarded center-only, so a footprint could overlap a strip edge
    M = {"dry_plots": [{"poly": [[300, 300], [500, 300], [500, 380], [300, 380]], "crop": "barley", "theta": 0.5}], "houses": [{"x": 480, "y": 372, "w": 46, "h": 28, "rot": 0, "kind": "plain"}]}
    assert "structures_clear_of_dry_plots" in f(M)


def test_structures_clear_of_dry_plots_passes_when_the_farmstead_abuts_the_strip():
    # abutting is fine (a hem may run right up to a wall) - only real overlap fires
    M = {"dry_plots": [{"poly": [[300, 300], [500, 300], [500, 380], [300, 380]], "crop": "barley", "theta": 0.5}], "houses": [{"x": 400, "y": 396, "w": 46, "h": 28, "rot": 0, "kind": "plain"}]}
    assert "structures_clear_of_dry_plots" not in f(M)


def test_groves_clear_of_dry_plots_fires_when_a_clump_stands_in_the_crop():
    M = {
        "dry_plots": [{"poly": [[300, 300], [500, 300], [500, 380], [300, 380]], "crop": "soy", "theta": 1.2}],
        "village_groves": [{"role": "belt", "r": 11, "clumps": [[400, 340]], "poly": [[380, 320], [420, 320], [420, 360], [380, 360]]}],
    }
    assert "groves_clear_of_dry_plots" in f(M)


def test_groves_clear_of_dry_plots_passes_when_the_belt_hugs_the_edge():
    M = {
        "dry_plots": [{"poly": [[300, 300], [500, 300], [500, 380], [300, 380]], "crop": "soy", "theta": 1.2}],
        "village_groves": [{"role": "belt", "r": 11, "clumps": [[400, 396]], "poly": [[380, 384], [420, 384], [420, 408], [380, 408]]}],
    }
    assert "groves_clear_of_dry_plots" not in f(M)


def test_field_ditches_ground_via_the_moat():
    # a MOATED city's combs ground at the moat both ways: the supply taps it (frm=moat is a SOURCE -
    # it is a fed watercourse, per city_moat_irrigates_fields) and a collector may empty into it
    # (to=moat is a SINK - the moat is the city's storm drain). Added for Tango's comb-field port.
    M = {
        "field_ditches": [{"poly": [[300, 300], [500, 300]], "role": "main", "field": "f"}, {"poly": [[300, 600], [500, 600]], "role": "drain", "field": "f"}],
        "channels": [
            {"poly": [[290, 296], [304, 308]], "frm": {"kind": "moat"}, "to": {"kind": "field", "name": "f"}, "w": 2.5},
            {"poly": [[494, 596], [520, 612]], "frm": {"kind": "drain"}, "to": {"kind": "moat"}, "w": 2.5},
        ],
    }
    assert "field_ditches_reach_source_and_sink" not in f(M)


# ---- lanes: houses must FRONT a lane (not sit on it); a CONNECTOR must run off the edge -------
def test_houses_clear_of_lanes_fires_when_a_house_sits_on_the_tread():
    M = {"lanes": [{"pts": [[100, 500], [900, 500]], "worn": True, "w": 6, "connector": False}], "houses": [{"x": 500, "y": 500, "w": 23, "h": 14, "rot": 0, "kind": "plain"}]}  # centered ON the lane
    assert "houses_clear_of_lanes" in f(M)


def test_houses_clear_of_lanes_passes_when_the_house_fronts_the_lane():
    M = {
        "lanes": [{"pts": [[100, 500], [900, 500]], "worn": True, "w": 6, "connector": False}],
        "houses": [{"x": 500, "y": 460, "w": 23, "h": 14, "rot": 0, "kind": "plain"}],
    }  # 40px off = fronting, clear
    assert "houses_clear_of_lanes" not in f(M)


def test_groves_clear_of_lanes_fires_when_a_copse_sits_on_a_lane():
    M = {
        "lanes": [{"pts": [[300, 100], [300, 700]], "w": 6}],
        "village_groves": [{"role": "copse", "r": 11, "clumps": [[302, 400]], "poly": [[290, 390], [314, 390], [314, 410], [290, 410]]}],
    }  # clump ON the lane
    assert "groves_clear_of_lanes" in f(M)


def test_groves_clear_of_lanes_passes_when_clumps_avoid_the_lane():
    M = {"lanes": [{"pts": [[300, 100], [300, 700]], "w": 6}], "village_groves": [{"role": "copse", "r": 11, "clumps": [[500, 400]], "poly": [[490, 390], [514, 390], [514, 410], [490, 410]]}]}
    assert "groves_clear_of_lanes" not in f(M)


def test_groves_clear_of_lanes_fires_when_a_per_house_grove_sits_on_a_road():
    # covers the per-house grove (rect) branch AND the road corridor
    M = {"road": [[100, 400], [900, 400]], "road_width": 26, "groves": [{"x": 500, "y": 400, "w": 40, "h": 30, "rot": 0, "of": [500, 360]}]}
    assert "groves_clear_of_lanes" in f(M)


def test_connector_lane_runs_off_edge_fires_when_it_stops_short():
    M = {"lanes": [{"pts": [[500, 500], [500, 700]], "worn": True, "w": 6, "connector": True}]}  # both ends interior
    assert any(c.startswith("connector_lane_runs_off_edge") for c in f(M))


def test_connector_lane_runs_off_edge_passes_when_it_reaches_the_edge():
    M = {"lanes": [{"pts": [[500, 500], [500, 1165]], "worn": True, "w": 6, "connector": True}]}  # runs off the bottom
    assert not any(c.startswith("connector_lane_runs_off_edge") for c in f(M))


# ---- drainage flows downhill (matches meta.down_deg); a COLLECTOR may run cross-slope, but not uphill ----
def _drain(poly, stream=None):
    M = {"meta": {"down_deg": 45}, "field_ditches": [{"poly": poly, "role": "drain", "field": "f"}]}
    if stream:
        M["streams"] = [{"poly": stream, "frm": {"kind": "drain"}, "to": {"kind": "offmap"}, "w": 9}]
    return M


def test_marsh_on_low_ground_fires_when_marsh_is_uphill():
    # down_deg=45 -> fall = x+y. The field centroid is (1300,1300); a marsh far NW (300,300) has LOWER fall
    # (higher ground) than the field -> it is uphill of the paddy -> fires.
    M = {"meta": {"scale": "village", "down_deg": 45}, "fields": [_field("p", 1000, 1000, 1600, 1600)], "marshes": [{"x": 300, "y": 300, "w": 100, "h": 100}]}
    assert "marsh_on_low_ground" in f(M)


def test_marsh_on_low_ground_passes_when_marsh_is_downhill():
    M = {"meta": {"scale": "village", "down_deg": 45}, "fields": [_field("p", 1000, 1000, 1600, 1600)], "marshes": [{"x": 2000, "y": 2000, "w": 100, "h": 100}]}  # SE, downhill of the field
    assert "marsh_on_low_ground" not in f(M)


def test_marsh_on_low_ground_ignores_a_pond_fringe():
    # a pond-fringe reed marsh sits at the pond (uphill of the field) but is a WATER-EDGE fringe, not the valley
    # toe, so it is exempt from the low-ground rule
    M = {
        "meta": {"scale": "village", "down_deg": 45},
        "fields": [_field("p", 1000, 1000, 1600, 1600)],
        "marshes": [{"x": 300, "y": 300, "w": 100, "h": 100, "role": "pond_fringe"}],
    }  # uphill, but exempt
    assert "marsh_on_low_ground" not in f(M)


def test_drain_flows_downhill_fires_when_outfall_is_uphill():
    # down_deg=45 -> fall = x+y. The brook meets the drain at (300,300) [low fall], so that is the OUTFALL,
    # but the head (700,700) is further downhill -> the outfall sits UPHILL of the head -> water runs backwards.
    assert "drain_flows_downhill" in f(_drain([[300, 300], [700, 700]], stream=[[300, 300], [40, 40]]))


def test_drain_flows_downhill_passes_when_outfall_is_downhill():
    assert "drain_flows_downhill" not in f(_drain([[300, 300], [700, 700]], stream=[[700, 700], [950, 950]]))


def test_drain_flows_downhill_defaults_to_the_lower_end_with_no_brook():
    # no brook and neither end at the edge -> the outfall defaults to the downhill end, so it never reads uphill
    assert "drain_flows_downhill" not in f(_drain([[300, 300], [700, 700]]))


def test_drainage_discharges_downhill_fires_when_the_brook_runs_uphill():
    # brook from the outfall (700,700 = high fall) up to (400,400 = lower fall) - carries runoff UPHILL
    assert "drainage_discharges_downhill" in f(_drain([[300, 300], [700, 700]], stream=[[700, 700], [400, 400]]))


def test_delivery_ditches_taper_fires_on_a_blunt_ditch():
    # a delivery ditch (role "branch") ending at nearly full width - it should have shed its water
    M = {"field_ditches": [{"poly": [[300, 300], [500, 500]], "role": "branch", "field": "f", "w": 4.0, "w_tail": 4.0}]}
    assert "delivery_ditches_taper" in f(M)


def test_delivery_ditches_taper_passes_when_it_narrows():
    M = {"field_ditches": [{"poly": [[300, 300], [500, 500]], "role": "branch", "field": "f", "w": 4.0, "w_tail": 1.5}]}
    assert "delivery_ditches_taper" not in f(M)


def test_delivery_ditches_taper_exempts_ditches_without_recorded_widths():
    # the older water_field engine records no head/tail width - nothing to judge, so it is skipped
    M = {"field_ditches": [{"poly": [[300, 300], [500, 500]], "role": "branch", "field": "f"}]}
    assert "delivery_ditches_taper" not in f(M)


def _dryplot(x, theta):
    # a full ~40x36 parcel (one corner nipped): the furrows-vary adjacency radius now derives from the
    # plots' own mean size (1.25x side length, capped 50px), so the fixture plots must be REAL parcels -
    # the old sliver trapezoid (~790px^2) read as sub-30px plots whose radius no longer paired them
    return {"poly": [[x, 300], [x + 40, 300], [x + 40, 336], [x + 4, 336]], "theta": theta, "crop": "barley"}


def test_dry_plot_furrows_vary_fires_when_two_neighbours_share_an_angle():
    # 4 dry plots in a row; the first two are edge-adjacent AND run their furrows the same way -> fires
    dp = [_dryplot(300, 0.2), _dryplot(340, 0.2), _dryplot(380, 0.9), _dryplot(420, 0.4)]
    assert "dry_plot_furrows_vary" in f({"dry_plots": dp})


def test_dry_plot_furrows_vary_passes_when_neighbours_differ():
    # adjacent plots alternate orientation, so no neighboring pair shares a row direction
    dp = [_dryplot(300, 0.2), _dryplot(340, 0.9), _dryplot(380, 0.2), _dryplot(420, 0.9)]
    assert "dry_plot_furrows_vary" not in f({"dry_plots": dp})


def test_dry_plot_furrows_vary_skipped_for_a_contour_village():
    # a STEEP / terraced village declares contour furrows (meta.dry_furrows_vary=False) - the rows converge on
    # the contour for erosion control, so identical adjacent angles are CORRECT and the check does not fire
    dp = [_dryplot(300, 0.2), _dryplot(340, 0.2), _dryplot(380, 0.2), _dryplot(420, 0.2)]  # all aligned
    assert "dry_plot_furrows_vary" not in f({"meta": {"dry_furrows_vary": False}, "dry_plots": dp})


def test_drainage_junction_smooth_fires_on_a_hard_corner():
    # drain arrives heading EAST; the brook leaves heading SOUTH = a hard ~90 deg corner off the collector
    M = {
        "field_ditches": [{"poly": [[300, 500], [700, 500]], "role": "drain", "field": "f"}],
        "streams": [{"poly": [[700, 500], [700, 900]], "frm": {"kind": "drain"}, "to": {"kind": "offmap"}, "w": 9}],
    }
    assert "drainage_junction_smooth" in f(M)


def test_drainage_junction_smooth_passes_when_the_brook_curves_out():
    # the brook leaves roughly CONTINUING the drain's eastward heading -> a smooth bend, not a corner
    M = {
        "field_ditches": [{"poly": [[300, 500], [700, 500]], "role": "drain", "field": "f"}],
        "streams": [{"poly": [[700, 500], [1000, 600]], "frm": {"kind": "drain"}, "to": {"kind": "offmap"}, "w": 9}],
    }
    assert "drainage_junction_smooth" not in f(M)


def test_drainage_junction_smooth_skips_a_brook_with_no_drain():
    # a drain-fed brook but no drain ditch present -> nothing to measure the junction against, so it is skipped
    M = {"streams": [{"poly": [[700, 500], [1000, 600]], "frm": {"kind": "drain"}, "to": {"kind": "offmap"}, "w": 9}]}
    assert "drainage_junction_smooth" not in f(M)


def test_drain_runs_cross_slope_fires_when_it_runs_downhill():
    # down_deg=45 (fall = SE). A drain running straight down the fall collects nothing - not a collector.
    assert "drain_runs_cross_slope" in f(_drain([[300, 300], [700, 700]]))


def test_drain_runs_cross_slope_passes_for_a_contour_collector():
    # a drain running along the contour (perpendicular to the fall) is a proper cross-slope collector
    assert "drain_runs_cross_slope" not in f(_drain([[300, 700], [700, 300]]))


def test_drain_flows_downhill_skips_non_drain_ditches():
    # a SUPPLY (main) ditch is not a collector - the drainage-direction check ignores it (only 'drain' role)
    M = {"meta": {"down_deg": 45}, "field_ditches": [{"poly": [[100, 100], [200, 200]], "role": "main", "field": "f"}, {"poly": [[300, 300], [700, 700]], "role": "drain", "field": "f"}]}
    assert "drain_flows_downhill" not in f(M)


def test_pond_fed_from_edge_fires_when_the_feeder_starts_mid_map():
    # a brook whose pond end is in the pond but whose FAR end sits mid-map (water out of nowhere)
    M = {"pond": [400, 300, 150, 90], "streams": [{"poly": [[600, 600], [420, 320]], "frm": {"kind": "offmap"}, "to": {"kind": "pond"}, "w": 9}]}
    assert "pond_fed_from_edge" in f(M)


def test_pond_fed_from_edge_passes_when_the_feeder_comes_from_the_edge():
    M = {"pond": [400, 300, 150, 90], "streams": [{"poly": [[10, 10], [420, 320]], "frm": {"kind": "offmap"}, "to": {"kind": "pond"}, "w": 9}]}
    assert "pond_fed_from_edge" not in f(M)


def test_pond_connected_to_field_fires_when_a_drainage_pond_drain_stops_short():
    # a DRAINAGE pond must be reached by the field's drain; a drain that stops short of the pond fires
    M = {
        "meta": {"scale": "hamlet", "toscale": True, "pond_role": "drainage"},
        "pond": [400, 700, 120, 74],
        "field_ditches": [{"poly": [[300, 300], [300, 500]], "role": "drain", "field": "f", "w": 3}],
    }
    assert "pond_connected_to_field" in f(M)


def test_pond_connected_to_field_passes_when_the_drain_reaches_the_drainage_pond():
    M = {
        "meta": {"scale": "hamlet", "toscale": True, "pond_role": "drainage"},
        "pond": [400, 700, 120, 74],
        "field_ditches": [{"poly": [[300, 500], [400, 700]], "role": "drain", "field": "f", "w": 3}],
    }  # end IN the pond
    assert "pond_connected_to_field" not in f(M)


def test_pond_connected_to_field_fires_when_a_source_pond_has_no_feed_channel():
    # a SOURCE pond (the default) must feed the field through an irrigation channel touching the pond
    M = {"meta": {"scale": "village"}, "pond": [400, 300, 150, 90], "channels": [{"poly": [[600, 600], [700, 700]], "frm": {"kind": "offmap"}, "to": {"kind": "field", "name": "f"}, "w": 2.5}]}
    assert "pond_connected_to_field" in f(M)


_FIELD_400 = {"name": "f", "kind": "paddy", "outline": [[300, 300], [500, 300], [500, 500], [300, 500]], "bbox": [300, 300, 500, 500], "vis_bbox": [300, 300, 500, 500]}
_POND_FEED = {"poly": [[400, 400], [450, 450]], "frm": {"kind": "pond"}, "to": {"kind": "field", "name": "f"}, "w": 2.5}


def test_pond_clear_of_field_fires_when_the_pond_sits_on_the_paddies():
    # an IRRIGATION pond (wired to the field) laid OVER it fires - a pond is beside/below the crop, not on it
    M = {"pond": [400, 400, 120, 80], "fields": [_FIELD_400], "channels": [_POND_FEED]}
    assert "pond_clear_of_field" in f(M)


def test_pond_clear_of_field_passes_when_the_pond_is_below_the_field():
    M = {"pond": [400, 750, 120, 74], "fields": [_FIELD_400], "channels": [_POND_FEED]}  # pond clear, below
    assert "pond_clear_of_field" not in f(M)


def test_pond_clear_of_field_exempts_a_decorative_pond_not_wired_to_a_field():
    # a city garden pond overlapping a farmland sample, with NO channel wiring it to the field, is exempt
    M = {"pond": [400, 400, 120, 80], "fields": [_FIELD_400]}  # no pond channel -> not an irrigation pond
    assert "pond_clear_of_field" not in f(M)


def test_brook_from_drain_outfall_runs_off_edge():
    # a natural BROOK that STARTS at the field drain's outfall (frm=drain) and runs off the map edge is
    # valid - exercises the "drain" anchor kind (the akusui empties into a valley brook, water OUT).
    M = {
        "field_ditches": [{"poly": [[300, 600], [700, 600]], "role": "drain", "field": "f"}],
        "streams": [{"poly": [[700, 600], [1200, 850], [1815, 1120]], "frm": {"kind": "drain"}, "to": {"kind": "offmap"}, "w": 9}],
    }
    fails = f(M)
    assert "stream_source_anchored[0]" not in fails and "stream_runs_off_edge[0]" not in fails


def test_stream_diverted_into_a_channel_passes_and_open_ended_brook_fires():
    # a BROOK flowing in from the top edge and artificially DIVERTED into the head-race at the field head
    # (frm=offmap, no `to`) is valid: it hands off to the irrigation net rather than running on over the
    # paddies. Exercises the at_ditch allowance - one end at the edge, the other ON an irrigation ditch.
    diverted = {
        "meta": {"W": 1000, "H": 1000},
        "field_ditches": [{"poly": [[500, 300], [500, 700]], "role": "main", "field": "f"}],
        "streams": [{"poly": [[500, 8], [500, 160], [500, 300]], "frm": {"kind": "offmap"}}],
    }
    assert "stream_runs_off_edge[0]" not in f(diverted)
    # TEETH: the same brook ending in OPEN ground (no edge/ditch/field/pond/moat/drain at its foot) must FIRE.
    open_ended = {"meta": {"W": 1000, "H": 1000}, "streams": [{"poly": [[500, 8], [500, 160], [500, 500]], "frm": {"kind": "offmap"}}]}
    assert "stream_runs_off_edge[0]" in f(open_ended)


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
    M = {"meta": {"scale": "town", "walled": True, "W": 1000, "H": 1000}, "wall": WALL, "religious": [_mon("A", 200, 200), _mon("B", 800, 800)], "torii": [[200, 320]]}
    assert "monastery_torii_scale_with_space" in f(M)


# ---- walled_town_has_gate_market: the extramural guan-xiang -------------------------------
def test_walled_town_has_gate_market_fires_when_no_market_outside():
    # the only business sits INSIDE the wall, so there is no extramural market at the gate
    M = {"meta": {"scale": "town", "walled": True}, "wall": WALL, "gate": [500, 950], "buildings": [bldg(500, 500, kind="merchant")]}
    assert "walled_town_has_gate_market" in f(M)


def test_walled_town_gate_market_opt_out_suppresses_the_check():
    # meta(gate_market=False) - a purely military or suppressed gate - skips the requirement
    M = {"meta": {"scale": "town", "walled": True, "gate_market": False}, "wall": WALL, "gate": [500, 950], "buildings": [bldg(500, 500, kind="merchant")]}
    assert "walled_town_has_gate_market" not in f(M)


# ---- town_has_granary: the opt-in rice-transit granary (default OFF) -----------------------
def test_town_has_granary_off_by_default():
    # a standard county seat keeps grain in the yamen - no granary declared, no check
    assert "town_has_granary" not in f({"meta": {"scale": "town"}})


def test_town_has_granary_fires_when_declared_but_not_drawn():
    assert "town_has_granary" in f({"meta": {"scale": "town", "granary": True}})


def test_town_has_granary_passes_when_drawn():
    M = {"meta": {"scale": "town", "granary": True}, "granary": {"x": 500, "y": 500, "n": 3, "stores": [], "label": "granary"}}
    assert "town_has_granary" not in f(M)


# ---- town_has_merchant_storehouses: several attached kura expected -------------------------
def test_town_has_merchant_storehouses_fires_when_too_few():
    assert "town_has_merchant_storehouses" in f({"meta": {"scale": "town"}})  # 0 < 3


def test_town_has_merchant_storehouses_passes_with_several():
    M = {"meta": {"scale": "town"}, "storehouses": [{"x": i, "y": 0} for i in range(4)]}
    assert "town_has_merchant_storehouses" not in f(M)


# ---- town_has_flophouse: cheap market-day lodging (default-on, opt-in to more) --------------
def test_town_has_flophouse_fires_when_absent_by_default():
    assert "town_has_flophouse" in f({"meta": {"scale": "town"}})  # 0 < default 1


def test_town_has_flophouse_requires_more_when_declared():
    M = {"meta": {"scale": "town", "flophouses": 2}, "flophouses": [{"x": 500, "y": 500, "w": 104, "h": 46, "rot": 0}]}
    assert "town_has_flophouse" in f(M)  # 1 < 2


def test_flophouse_on_road_overlaps_like_any_structure():
    # a standalone civic building (flophouse) is now checked for overlaps too: one sitting on
    # the road must trip no_structure_on_road, exactly as a shop would.
    M = {"meta": {"scale": "town"}, "road": [[100, 500], [900, 500]], "road_width": 26, "flophouses": [{"x": 500, "y": 500, "w": 104, "h": 46, "rot": 0}]}
    assert "no_structure_on_road" in f(M)  # 1 < 2


def test_town_has_flophouse_opt_out_with_zero():
    assert "town_has_flophouse" not in f({"meta": {"scale": "town", "flophouses": 0}})


# ---- town_monasteries_dedicated: wrong patron fortunes for the clan ------------------------
def _monastery(fortune):
    return {"kind": "monastery", "label": f"Monastery of {fortune}", "x": 0, "y": 0, "w": 10, "h": 10}


def test_town_monasteries_dedicated_fires_on_wrong_fortune():
    # Lion's patrons are Bishamon + Daikoku; a Benten monastery is wrong (no override declared)
    M = {"meta": {"scale": "town", "clan": "Lion"}, "religious": [_monastery("Bishamon"), _monastery("Benten")]}
    assert "town_monasteries_dedicated" in f(M)


def test_town_monasteries_dedicated_passes_with_correct_fortunes():
    M = {"meta": {"scale": "town", "clan": "Lion"}, "religious": [_monastery("Bishamon"), _monastery("Daikoku")]}
    assert "town_monasteries_dedicated" not in f(M)


# ---- a meta-driven scale rule -------------------------------------------------------------
def test_hamlet_has_no_headman_fires_when_a_hamlet_has_one():
    M = {"meta": {"scale": "hamlet"}, "houses": [{"x": 100, "y": 100, "w": 108, "h": 68, "kind": "big", "rot": 0, "role": "headman"}]}
    assert "hamlet_has_no_headman" in f(M)


# ---- module-level helper branches (direct calls) ------------------------------------------
def test_helper_edge_branches():
    cv = check_village
    assert cv.sat_overlap([(0, 0), (10, 0), (10, 10), (0, 10)], [(5, 5), (15, 5), (15, 15), (5, 15)])
    assert not cv.sat_overlap([(0, 0), (10, 0), (10, 10), (0, 10)], [(20, 20), (30, 20), (30, 30), (20, 30)])
    assert cv.seg_closest(0, 0, (5, 5), (5, 5)) == (5, 5)  # degenerate (zero-length) segment
    assert cv.unit_dir(None) is None  # no slope declared
    assert cv.unit_dir("nonsense") is None  # unknown cardinal name
    assert cv.unit_dir([3, 4]) == (0.6, 0.8)  # raw vector, normalized
    assert cv.poly_dist(5, 5, [(0, 0), (10, 0), (10, 10), (0, 10)]) == 0.0  # point inside the polygon


# ---- the on_<feature> overlap helpers: a structure that CONTAINS a feature vertex
# (point_in_poly path) and one the feature CROSSES (segments_cross path) ---------------------
FEAT = [[100, 500], [500, 500], [900, 500]]


def _feature_overlap(meta_extra, key, value, extra=None):
    A = bldg(500, 500, w=200, h=200)  # the feature's (500,500) vertex sits inside A (point_in_poly path)
    B = bldg(300, 500, w=16, h=300)  # the feature crosses B's edge (segments_cross path)
    C = bldg(200, 500, w=40, h=8)  # C's corner sits right on the feature (seg_dist path)
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


# ---- field/water/channel FAIL branches ----------------------------------------------------
def _field(name, x0, y0, x1, y1):
    return {"name": name, "kind": "paddy", "bbox": [x0, y0, x1, y1], "outline": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]}


def test_channel_source_anchored_fires_on_bad_anchor():
    M = {"channels": [{"poly": [[100, 100], [110, 120], [120, 140]], "frm": {"kind": "bogus"}, "to": {"kind": "offmap"}}]}
    assert "channel_source_anchored[0]" in f(M)


def test_streams_avoid_fields_fires():
    M = {"fields": [_field("f", 100, 100, 400, 400)], "streams": [{"poly": [[200, 200], [200, 500]]}]}  # first point sits inside the field
    assert "streams_avoid_fields" in f(M)


def test_streams_avoid_fields_allows_a_drain_fed_brook():
    # a brook anchored to the field's DRAIN starts at the outfall (inside the envelope) and runs off-map - legit
    M = {"fields": [_field("f", 100, 100, 400, 400)], "streams": [{"poly": [[300, 380], [300, 550], [300, 700]], "frm": {"kind": "drain"}, "to": {"kind": "offmap"}}]}
    assert "streams_avoid_fields" not in f(M)


def test_streams_avoid_fields_still_fires_when_a_drain_brook_reenters_the_field():
    # a drain-fed brook that leaves then CUTS BACK across the crop is still a defect
    M = {"fields": [_field("f", 100, 100, 400, 400)], "streams": [{"poly": [[300, 380], [300, 600], [250, 250]], "frm": {"kind": "drain"}, "to": {"kind": "offmap"}}]}  # last leg re-enters the field
    assert "streams_avoid_fields" in f(M)


def test_streams_avoid_fields_allows_a_stream_that_ends_at_the_field():
    # a stream anchored INTO the field (to=field) ends inside it - the connection is legitimate
    M = {
        "fields": [_field("f", 100, 100, 400, 400)],
        "streams": [{"poly": [[300, 700], [300, 500], [300, 300]], "frm": {"kind": "offmap"}, "to": {"kind": "field", "name": "f"}}],
    }  # ends inside the field
    assert "streams_avoid_fields" not in f(M)


def test_fields_clear_of_road_fires():
    M = {"fields": [_field("f", 100, 100, 400, 400)], "road": [[50, 250], [500, 250]], "road_width": 26}
    assert "fields_clear_of_road" in f(M)


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


def test_taxfree_plots_not_required_when_absent():
    M = {"meta": {"scale": "village"}, "fields": [_field("f", 100, 100, 400, 400)], "houses": [_farmhouse(60, 250)]}
    assert "taxfree_plots_in_range" not in f(M)  # a village that does not denote them is fine


def test_taxfree_plots_range_validated_when_present():
    M = {"meta": {"scale": "village"}, "fields": [_field("f", 100, 100, 400, 400)], "houses": [_farmhouse(60, 250)], "taxfree": [[200, 200]]}  # 1 present, law wants 2-3
    assert "taxfree_plots_in_range" in f(M)


def test_fields_clear_of_wall_fires():
    M = {"meta": {"scale": "town", "walled": True}, "wall": [[250, 50], [250, 500], [260, 500]], "fields": [_field("f", 100, 100, 400, 400)], "gate": [250, 500]}
    assert "fields_clear_of_wall" in f(M)


def test_fields_show_water_source_branches():
    abut = _field("a", 100, 100, 300, 300)  # abuts the stream at x95 -> watered
    ponded = {"name": "p", "kind": "paddy", "bbox": [680, 180, 720, 220], "outline": [[680, 180], [720, 180], [720, 220], [680, 220]]}  # over the pond -> watered
    dry = _field("d", 100, 600, 300, 800)  # no channel/stream/pond -> dry, fires
    M = {"fields": [abut, ponded, dry], "streams": [{"poly": [[95, 90], [95, 310]]}], "pond": [700, 200, 80, 60]}
    assert "fields_show_water_source" in f(M)


def test_edge_features_run_off_map_fires_each_direction():
    M = {
        "meta": {"W": 1000, "H": 1000},
        "pastures": [
            [[960, 400], [990, 400], [990, 460], [960, 460]],  # right edge, stops short
            [[10, 400], [40, 400], [40, 460], [10, 460]],  # left
            [[400, 960], [460, 960], [460, 990], [400, 990]],  # bottom
            [[400, 10], [460, 10], [460, 40], [400, 40]],
        ],
    }  # top
    assert "edge_features_run_off_map" in f(M)


def test_house_count_in_range_target_houses_fires():
    houses = [{"x": i * 30, "y": 100, "w": 44, "h": 29, "kind": "plain", "rot": 0} for i in range(10)]
    M = {"meta": {"scale": "village", "target_houses": 60}, "houses": houses}  # 10 vs ~60
    assert "house_count_in_range" in f(M)


# ---- water-width ladder: ditch < creek < moat, with honest gaps ---------------------------
# Real wet-rice water systems are a tiered hierarchy (~2-4x per tier); the rendered map log-
# compresses that but must keep the ordering. A ditch is the thinnest line; a creek clearly
# beats it; the city moat dwarfs it and out-widths every natural stream (a feeder may equal it).
_CHAN = [[100, 100], [110, 120], [120, 140]]
_STRM = [[400, 100], [400, 300]]


def test_irrigation_channels_hairline_fires_on_a_fat_ditch():
    M = {"channels": [{"poly": _CHAN, "frm": {"kind": "offmap"}, "to": {"kind": "field", "name": "f"}, "w": 4.2}]}
    assert "irrigation_channels_hairline" in f(M)  # the OLD 4.2 px stout ditch must now trip


def test_irrigation_channels_hairline_passes_at_the_floor():
    M = {"channels": [{"poly": _CHAN, "frm": {"kind": "offmap"}, "to": {"kind": "field", "name": "f"}, "w": 2.5}]}
    assert "irrigation_channels_hairline" not in f(M)


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
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(500, 500)], "gardens": [{"x": 520, "y": 455, "w": 24, "h": 16, "rot": 0, "of": [500, 500]}]}  # y=455 is north of 500
    assert "gardens_on_sunny_side" in f(M)


def test_gardens_smaller_than_farmhouse_fires_on_an_oversize_garden():
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(500, 500)], "gardens": [{"x": 545, "y": 500, "w": 60, "h": 40, "rot": 0, "of": [500, 500]}]}  # bigger than the house
    assert "gardens_smaller_than_farmhouse" in f(M)


def test_gardens_clear_of_paddies_fires_on_a_garden_in_a_field():
    M = {
        "meta": {"scale": "village"},
        "houses": [_farmhouse(500, 500)],
        "fields": [_field("p", 480, 480, 600, 600)],
        "gardens": [{"x": 530, "y": 530, "w": 24, "h": 16, "rot": 0, "of": [500, 500]}],
    }  # sits inside the paddy
    assert "gardens_clear_of_paddies" in f(M)


def test_gardens_clear_of_structures_fires_when_a_garden_covers_another_building():
    M = {
        "meta": {"scale": "village"},
        "houses": [_farmhouse(500, 500)],
        "buildings": [bldg(545, 500, "shop")],
        "gardens": [{"x": 545, "y": 500, "w": 24, "h": 16, "rot": 0, "of": [500, 500]}],
    }  # on the shop, not its own house
    assert "gardens_clear_of_structures" in f(M)


def test_gardens_clear_of_sheds_fires_when_a_garden_covers_the_shed():
    # a farm's kura is a recorded annex in M['farm_sheds']; a garden placed on top of it overlaps it.
    M = {
        "meta": {"scale": "village"},
        "houses": [{"x": 500, "y": 500, "w": 44, "h": 29, "kind": "plain", "rot": 0}],
        "farm_sheds": [{"x": 500, "y": 476, "w": 20, "h": 9, "rot": 0, "of": [500, 500]}],  # kura on the north wall
        "gardens": [{"x": 500, "y": 478, "w": 24, "h": 16, "rot": 0, "of": [500, 500]}],
    }  # on the shed
    assert "gardens_clear_of_sheds" in f(M)


def test_gardens_clear_of_channels_fires_when_a_garden_sits_on_a_ditch():
    # a drain ditch runs straight through the garden's footprint - a raised-bed saien in a running ditch
    M = {
        "meta": {"scale": "village"},
        "houses": [{"x": 500, "y": 500, "w": 44, "h": 29, "kind": "plain", "rot": 0}],
        "gardens": [{"x": 540, "y": 500, "w": 24, "h": 16, "rot": 0, "of": [500, 500]}],
        "field_ditches": [{"poly": [[540, 480], [540, 520]], "role": "drain", "w": 6, "field": "f"}],
    }
    assert "gardens_clear_of_channels" in f(M)


def test_farm_sheds_attached_fires_on_a_stranded_kura():
    # a kura recorded far from every farmhouse (a move-procedure stranded it in the open courtyard) must trip
    M = {"meta": {"scale": "village"}, "houses": [{"x": 500, "y": 500, "w": 44, "h": 29, "kind": "plain", "rot": 0}], "farm_sheds": [{"x": 800, "y": 800, "w": 20, "h": 9, "rot": 0, "of": [500, 500]}]}
    assert "farm_sheds_attached" in f(M)


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


def test_wells_clear_of_shrine_and_torii_fires_when_a_well_sits_under_the_torii():
    # a well scattered under the torii arch (its disc overlaps the arch box) reads as a wellhead in the gateway
    M = {"meta": {"scale": "village"}, "torii": [[500, 500, 1]], "wells": [{"x": 505, "y": 502, "r": 8}]}
    assert "wells_clear_of_shrine_and_torii" in f(M)


# ---- SOFT ADVISORY: crop-limiting relocatable singleton ----
# a village that crops to content, with a pond stuck far EAST (sole east feature) and empty room between the
# NW houses and the SE paddy to move it into -> moving that one pond would crop the image much smaller
_POND_OUTLIER = {
    "meta": {"scale": "village", "view": [0, 0, 1400, 1000]},
    "houses": [{"x": 200, "y": 200, "w": 60, "h": 40, "rot": 0, "kind": "plain"}],
    "fields": [{"name": "f", "kind": "paddy", "vis_bbox": [600, 500, 1000, 900], "bbox": [600, 500, 1000, 900], "outline": [[600, 500], [1000, 500], [1000, 900], [600, 900]]}],
    "pond": [1300, 400, 90, 60],
}


def test_crop_advisory_flags_an_outlying_pond():
    adv = check_village.crop_relocatable_singletons(_POND_OUTLIER)
    assert len(adv) == 1 and adv[0]["kind"] == "pond" and adv[0]["edge"] == "E" and adv[0]["shrink"] >= 150


def test_crop_advisory_exempts_a_pond_that_sources_a_field():
    # a pond feeding a field (channel frm=pond -> to=field) is a valley-head reservoir: hydrologically anchored
    # uphill of the field, so the advisory does NOT flag it (moving it in would drop it below the field intake)
    M = {**_POND_OUTLIER, "channels": [{"poly": [[1300, 400], [900, 600]], "frm": {"kind": "pond"}, "to": {"kind": "field", "name": "f"}}]}
    assert check_village.crop_relocatable_singletons(M) == []


def test_crop_advisory_occupancy_includes_hill_forest_and_marsh():
    # the empty-landing search must AVOID a hill / forest / marsh too (all placed SE, clear of the NW landing);
    # the pond still fires (it lands NW, clear of them). Exercises the solid-occupancy accounting.
    M = {**_POND_OUTLIER, "hill": [850, 750, 80, 60], "forest": [{"poly": [[900, 600], [1000, 700]]}], "marshes": [{"poly": [[650, 850], [750, 950]]}]}
    adv = check_village.crop_relocatable_singletons(M)
    assert len(adv) == 1 and adv[0]["kind"] == "pond"


def test_crop_advisory_skips_a_city():
    assert check_village.crop_relocatable_singletons({**_POND_OUTLIER, "meta": {"scale": "city", "view": [0, 0, 1400, 1000]}}) == []


def test_crop_advisory_skips_an_uncropped_map():
    assert check_village.crop_relocatable_singletons({**_POND_OUTLIER, "meta": {"scale": "village"}}) == []  # no view


def test_crop_advisory_empty_without_content():
    assert check_village.crop_relocatable_singletons({"meta": {"scale": "village", "view": [0, 0, 100, 100]}}) == []


def test_crop_advisory_ignores_a_pond_that_barely_extends():
    # pond east=1030 vs field east=1000 -> shrink ~30px, below the 150px "significant" floor
    assert check_village.crop_relocatable_singletons({**_POND_OUTLIER, "pond": [1010, 400, 20, 20]}) == []


def test_crop_advisory_needs_an_empty_landing():
    # the field FILLS the tighter frame (and has NO vis_bbox -> the outline path), so a moved pond has nowhere to go
    M = {"meta": {"scale": "village", "view": [0, 0, 1400, 1000]}, "fields": [{"name": "f", "outline": [[100, 100], [800, 100], [800, 800], [100, 800]]}], "pond": [1100, 400, 90, 60]}
    assert check_village.crop_relocatable_singletons(M) == []


def test_crop_advisory_skips_a_hill_anchored_shrine():
    # the shrine sits ON the hill, so it is terrain-anchored - it cannot move to flat empty ground
    M = {
        "meta": {"scale": "village", "view": [0, 0, 1400, 1000]},
        "houses": [{"x": 200, "y": 200, "w": 60, "h": 40, "rot": 0}],
        "shrines": [{"x": 900, "y": 200, "w": 60, "h": 48}],
        "hill": [900, 200, 200, 150],
    }
    assert check_village.crop_relocatable_singletons(M) == []


def test_crop_advisory_pond_only_map_has_nothing_to_tighten_against():
    # removing the pond leaves NO other frame drivers, so there is no tighter frame to move into
    assert check_village.crop_relocatable_singletons({"meta": {"scale": "village", "view": [0, 0, 400, 400]}, "pond": [200, 200, 90, 60]}) == []


def test_gate_crop_advisory_is_soft_not_a_failure():
    fails = check_village.gate(_POND_OUTLIER, verbose=True)  # prints the ADVISORY line but must NOT gate the map
    assert "crop_could_tighten" not in fails


def test_gate_crop_advisory_can_be_silenced():
    M = {**_POND_OUTLIER, "meta": {"scale": "village", "view": [0, 0, 1400, 1000], "crop_advisory": False}}
    check_village.gate(M, verbose=True)  # meta(crop_advisory=False) -> the advisory block is skipped
    assert check_village.crop_relocatable_singletons(M)  # ... though the detector itself still finds it


# ---- SOFT ADVISORY: a SHRINE + its churchyard GRAVEYARD move as one relocatable GROUP ----
# The Hikari-no-Sato case: a village Bishamon shrine and the graveyard it is responsible for both sit at the
# far SW corner, so together they hold the S crop edge out. Removing the shrine ALONE leaves the graveyard
# pinning that edge (and vice versa) -> neither reads as a relocatable singleton; only weighed TOGETHER does
# the precinct free the corner, letting the image crop much smaller. The `shrines`/`religious` mirror pair,
# the cemetery, and the ablution well all move as one unit.
_SHRINE_GRAVEYARD_GROUP = {
    "meta": {"scale": "village", "view": [0, 0, 1400, 1200]},
    "houses": [{"x": 300, "y": 250, "w": 60, "h": 40, "rot": 0, "kind": "plain"}],
    "fields": [{"name": "f", "kind": "paddy", "vis_bbox": [500, 300, 1000, 700], "bbox": [500, 300, 1000, 700], "outline": [[500, 300], [1000, 300], [1000, 700], [500, 700]]}],
    "religious": [{"kind": "shrine", "x": 300, "y": 1050, "w": 90, "h": 60}],
    "shrines": [{"x": 300, "y": 1050, "w": 90, "h": 60}],
    "cemeteries": [{"x": 300, "y": 940, "w": 80, "h": 70, "rot": 0}],
    "wells": [{"x": 380, "y": 1050, "r": 8}],
}


def test_crop_advisory_flags_a_shrine_and_graveyard_as_a_movable_group():
    adv = check_village.crop_relocatable_singletons(_SHRINE_GRAVEYARD_GROUP)
    grp = [a for a in adv if a["kind"] == "shrine+churchyard"]
    assert len(grp) == 1
    assert grp[0]["members"] >= 3  # shrine + its `shrines` mirror + cemetery (+ well)
    assert grp[0]["edge"] == "S" and grp[0]["shrink"] >= 150
    assert grp[0]["landing"] is not None  # an empty, dry, appropriate spot exists inside the tighter frame


def test_crop_advisory_group_beats_the_silent_singletons():
    # neither the shrine NOR the graveyard qualifies ALONE (each leaves the other holding the S edge), so the
    # ONLY qualifying candidate is the group - proving the group logic, not a lucky singleton, is what fires
    adv = check_village.crop_relocatable_singletons(_SHRINE_GRAVEYARD_GROUP)
    assert adv and all(a["kind"] == "shrine+churchyard" for a in adv)


def test_crop_advisory_group_landing_avoids_the_marsh():
    # a marsh filling the empty S landing forces the group to land on DRY ground (the N gap above the field);
    # exercises marsh inclusion in the group's solid-occupancy so a churchyard never lands in a bog
    M = {**_SHRINE_GRAVEYARD_GROUP, "marshes": [{"role": "toe", "poly": [[100, 800], [450, 800], [450, 1150], [100, 1150]]}]}
    adv = [a for a in check_village.crop_relocatable_singletons(M) if a["kind"] == "shrine+churchyard"]
    assert len(adv) == 1
    lx, ly = adv[0]["landing"]
    assert not (100 <= lx <= 450 and 800 <= ly <= 1150)  # not inside the bog


def test_crop_advisory_lone_shrine_is_not_a_group():
    # a shrine with no attached graveyard/well/torii is a bare singleton, not a group - no shrine+churchyard entry
    M = {
        "meta": {"scale": "village", "view": [0, 0, 1400, 1000]},
        "houses": [{"x": 300, "y": 250, "w": 60, "h": 40, "rot": 0}],
        "fields": [{"name": "f", "kind": "paddy", "vis_bbox": [500, 300, 1000, 700], "bbox": [500, 300, 1000, 700], "outline": [[500, 300], [1000, 300], [1000, 700], [500, 700]]}],
        "religious": [{"kind": "shrine", "x": 300, "y": 900, "w": 90, "h": 60}],
        "shrines": [{"x": 300, "y": 900, "w": 90, "h": 60}],
    }
    adv = check_village.crop_relocatable_singletons(M)
    assert all(a["kind"] != "shrine+churchyard" for a in adv)


def test_gate_prints_the_group_advisory_phrasing():
    # the verbose gate line phrases a GROUP differently from a lone feature ("a N-feature group, moved as one unit")
    import contextlib
    import io

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fails = check_village.gate(_SHRINE_GRAVEYARD_GROUP, verbose=True)
    out = buf.getvalue()
    assert "shrine+churchyard" in out and "group, moved as one unit" in out
    assert "crop_could_tighten" not in fails  # still a SOFT advisory, never a gate failure


def test_hikari_bishamon_precinct_no_longer_limits_the_crop():
    # the GM's actual case: Hikari-no-Sato's Bishamon shrine + its churchyard graveyard USED to sit at the far
    # SW, holding the S crop edge out ~200px over empty ground - the group advisory (proved by the synthetic
    # _SHRINE_GRAVEYARD_GROUP fixture above) flagged it. It has since been RELOCATED into the dry pocket below
    # the E block, so the shipped map's advisory is now SILENT. This guards against a regression that re-parks
    # the precinct (or any shrine group) where it needlessly limits the crop. See settlements.md 'Crop advisory'.
    here = pathlib.Path(__file__).parent
    M = json.loads((here / "pool" / "villages" / "hikari-no-sato.json").read_text())
    assert check_village.crop_relocatable_singletons(M) == []


def test_hard_features_within_frame_fires_on_a_feature_clipped_by_the_crop():
    # a set-apart graveyard placed past the tight WEST frame edge (its west edge x=310 < the view's x0=400).
    # the torii (list branch) and well (radius branch) sit INSIDE the frame - only the graveyard is clipped.
    M = {
        "meta": {"scale": "village", "view": [400, 100, 1000, 800]},
        "torii": [[500, 300, 1]],
        "wells": [{"x": 600, "y": 300, "r": 8}],
        "cemeteries": [{"x": 360, "y": 500, "w": 100, "h": 70, "rot": 0}],
    }
    assert "hard_features_within_frame" in f(M)


def test_garden_plots_are_quads_fires_on_a_non_quad_poly():
    # a garden whose recorded footprint poly has 3 vertices (a triangle, not a quadrilateral)
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(500, 500)], "gardens": [{"x": 520, "y": 520, "w": 24, "h": 16, "rot": 0, "of": [500, 500], "poly": [[509, 513], [531, 513], [520, 527]]}]}
    assert "garden_plots_are_quads" in f(M)


def test_garden_plots_are_quads_fires_when_poly_pokes_outside_its_rect():
    # a 4-gon whose first corner (x=560) sits well OUTSIDE the recorded w x h bounds (x in [508, 532]); the
    # jitter only pulls corners INWARD, so an outside vertex means the overlap checks cleared the wrong rect
    M = {
        "meta": {"scale": "village"},
        "houses": [_farmhouse(500, 500)],
        "gardens": [{"x": 520, "y": 520, "w": 24, "h": 16, "rot": 0, "of": [500, 500], "poly": [[560, 513], [531, 513], [530, 527], [510, 527]]}],
    }
    assert "garden_plots_are_quads" in f(M)


def test_garden_plots_are_quads_passes_on_a_valid_inscribed_quad():
    M = {
        "meta": {"scale": "village"},
        "houses": [_farmhouse(500, 500)],
        "gardens": [{"x": 520, "y": 520, "w": 24, "h": 16, "rot": 0, "of": [500, 500], "poly": [[509, 513], [531, 512], [530, 527], [510, 528]]}],
    }
    assert "garden_plots_are_quads" not in f(M)


def test_garden_area_within_norms_fires_on_an_oversize_garden():
    # a single bed the size of a field (~60x60 px = 3600 px^2 ~ 1338 m^2 at 2 ft/px), far above a saien's band
    M = {
        "meta": {"scale": "village"},
        "houses": [_farmhouse(500, 500)],
        "gardens": [{"x": 560, "y": 500, "w": 60, "h": 60, "rot": 0, "of": [500, 500], "poly": [[530, 470], [590, 470], [590, 530], [530, 530]]}],
    }
    assert "garden_area_within_norms" in f(M)


def test_garden_area_within_norms_fires_on_a_tiny_garden():
    # a bed under ~10 m^2 (~27 px^2 at 2 ft/px): a 5x4 poly is ~20 px^2 ~ 7.4 m^2
    M = {
        "meta": {"scale": "village"},
        "houses": [_farmhouse(500, 500)],
        "gardens": [{"x": 520, "y": 500, "w": 5, "h": 4, "rot": 0, "of": [500, 500], "poly": [[517.5, 498], [522.5, 498], [522.5, 502], [517.5, 502]]}],
    }
    assert "garden_area_within_norms" in f(M)


def test_garden_area_within_norms_passes_and_sums_fragmented_beds():
    # two beds of ONE household, each ~120 px^2 (~45 m^2), summing ~89 m^2 - the fragmented-plot total is in band
    beds = [
        {"x": 512, "y": 500, "w": 12, "h": 10, "rot": 0, "of": [500, 500], "poly": [[506, 495], [518, 495], [518, 505], [506, 505]]},
        {"x": 530, "y": 500, "w": 12, "h": 10, "rot": 0, "of": [500, 500], "poly": [[524, 495], [536, 495], [536, 505], [524, 505]]},
    ]
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(500, 500)], "gardens": beds}
    assert "garden_area_within_norms" not in f(M)


def _grove(x, y, ofx, ofy, w=30, h=24):
    return {"x": x, "y": y, "w": w, "h": h, "rot": 0, "of": [ofx, ofy], "face": [-1, -1]}


def test_groves_on_windward_side_fires_on_a_lee_grove():
    # default windward NW; a grove on the SE (lee/sunny) side of its house is backwards
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(500, 500)], "groves": [_grove(540, 540, 500, 500)]}  # SE of the house, not the windward NW
    assert "groves_on_windward_side" in f(M)


def test_groves_on_windward_side_respects_meta_windward():
    # with the wind keyed to the NE, a grove on the SW is on the lee side and fires
    M = {"meta": {"scale": "village", "windward": "NE"}, "houses": [_farmhouse(500, 500)], "groves": [_grove(460, 540, 500, 500)]}  # SW, but windward is NE
    assert "groves_on_windward_side" in f(M)


def test_groves_on_windward_side_passes_on_a_nw_grove():
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(500, 500)], "groves": [_grove(465, 470, 500, 500)]}  # NW of the house - windward
    assert "groves_on_windward_side" not in f(M)


def test_groves_clear_of_paddies_fires_on_a_grove_in_a_field():
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(500, 500)], "fields": [_field("p", 440, 440, 600, 600)], "groves": [_grove(465, 470, 500, 500)]}  # NW corner sits inside the paddy
    assert "groves_clear_of_paddies" in f(M)


def test_groves_clear_of_structures_fires_when_a_grove_covers_another_building():
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(500, 500)], "buildings": [bldg(460, 470, "shop")], "groves": [_grove(460, 470, 500, 500)]}  # on the shop, not its own house
    assert "groves_clear_of_structures" in f(M)


def test_groves_where_possible_fires_when_a_clear_windward_farm_has_none():
    # 12 farmhouses with open windward sides (no fields/structs/corridors) and no groves -> the generator
    # would have placed groves; a grove-less farm with clear windward room is flagged
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(300 + 60 * i, 400) for i in range(12)], "groves": []}
    assert "groves_where_possible" in f(M)


def test_groves_where_possible_passes_when_windward_is_blocked():
    # the same farms, but a field hugs every windward (N + W) side -> no room -> no grove required
    houses = [_farmhouse(300 + 60 * i, 400) for i in range(12)]
    fields = [_field(f"f{i}", 280 + 60 * i, 330, 340 + 60 * i, 395) for i in range(12)]  # field just N of each house
    M = {"meta": {"scale": "village", "windward": "N"}, "houses": houses, "fields": fields, "groves": []}
    assert "groves_where_possible" not in f(M)


def _nuc_grid(n=12):
    return [_farmhouse(300 + 40 * (i % 6), 400 + 40 * (i // 6)) for i in range(n)]


def test_groves_where_possible_skipped_for_a_nucleated_village():
    # a NUCLEATED village shelters behind the COMMUNAL windbreak, not per-house groves, so bare farms with
    # clear windward room must NOT fire groves_where_possible - though the SAME setup DOES fire when dispersed
    houses = [_farmhouse(300 + 60 * i, 400) for i in range(12)]
    assert "groves_where_possible" in f({"meta": {"scale": "village"}, "houses": houses, "groves": []})
    assert "groves_where_possible" not in f({"meta": {"scale": "village", "nucleated": True}, "houses": houses, "groves": []})


def _nuc_village_M(houses, vgroves=None, **extra):
    M = {"meta": {"scale": "village", "nucleated": True}, "houses": houses}
    if vgroves is not None:
        M["village_groves"] = vgroves
    M.update(extra)
    return M


def test_village_windbreak_present_fires_when_a_nucleated_village_has_none():
    assert "village_windbreak_present" in f(_nuc_village_M(_nuc_grid(), []))


def test_village_windbreak_present_passes_with_a_back_grove_on_the_windward_side():
    houses = _nuc_grid()
    ccx = sum(h["x"] for h in houses) / len(houses)
    ccy = sum(h["y"] for h in houses) / len(houses)
    wb = [{"x": ccx - 150, "y": ccy - 150, "w": 72, "h": 300, "rot": 0, "role": "windbreak"}]  # NW of the centroid
    fails = f(_nuc_village_M(houses, wb))
    assert "village_windbreak_present" not in fails and "village_windbreak_on_windward_side" not in fails


def test_village_windbreak_on_windward_side_fires_on_a_lee_belt():
    houses = _nuc_grid()
    ccx = sum(h["x"] for h in houses) / len(houses)
    ccy = sum(h["y"] for h in houses) / len(houses)
    wb = [{"x": ccx + 150, "y": ccy + 150, "w": 72, "h": 300, "rot": 0, "role": "windbreak"}]  # SE = the sunny lee
    assert "village_windbreak_on_windward_side" in f(_nuc_village_M(houses, wb))


def test_village_groves_clear_of_paddies_fires_on_a_grove_in_a_field():
    M = _nuc_village_M(_nuc_grid(), [{"x": 600, "y": 600, "w": 40, "h": 40, "rot": 0, "role": "copse"}], fields=[_field("p", 540, 540, 700, 700)])
    assert "village_groves_clear_of_paddies" in f(M)


def test_commons_clear_of_paddies_fires_when_scrub_sits_in_a_field():
    # The check tests the DRAWN OUTCOME, not the patch's bbox CENTER (the scatter skips every paddy point by
    # construction, so a center-over-water test was only a proxy). It fires when a patch can clothe NOTHING:
    M = _nuc_village_M(_nuc_grid(), fields=[_field("p", 540, 540, 700, 700)])
    M["commons"] = [{"x": 600, "y": 600, "w": 60, "h": 60, "rot": 0, "poly": [[570, 570], [630, 570], [630, 630], [570, 630]]}]  # wholly inside the paddy -> draws nothing
    assert "commons_clear_of_paddies" in f(M)
    # ...but an INTERIOR FILL - the patch that clothes the voids an irregular field leaves inside its own bbox -
    # legitimately has its CENTER on the crop while every glyph it draws lands in the open ground around it.
    # Scoring the center failed this correct patch, which is why the rule changed (GM, 2026-07: Akagahara's fan
    # void rendered as bare clay because nothing was allowed to cover it).
    fill = _nuc_village_M(_nuc_grid(), fields=[_field("p", 540, 540, 700, 700)])
    fill["commons"] = [{"x": 600, "y": 600, "w": 400, "h": 400, "rot": 0, "poly": [[400, 400], [800, 400], [800, 800], [400, 800]]}]
    assert "commons_clear_of_paddies" not in f(fill)
    # a patch with no recorded polygon is skipped rather than crashing
    nopoly = _nuc_village_M(_nuc_grid(), fields=[_field("p", 540, 540, 700, 700)])
    nopoly["commons"] = [{"x": 600, "y": 600, "w": 60, "h": 60, "rot": 0}]
    assert "commons_clear_of_paddies" not in f(nopoly)


def _nuc_with_windbreak():
    houses = _nuc_grid()
    ccx = sum(h["x"] for h in houses) / len(houses)
    ccy = sum(h["y"] for h in houses) / len(houses)
    wb = [{"x": ccx - 160, "y": ccy - 160, "w": 72, "h": 300, "rot": 0, "role": "windbreak"}]  # NW back grove
    return houses, ccx, ccy, _nuc_village_M(houses, wb)


def test_commons_beyond_the_windbreak_fires_when_between_grove_and_village():
    houses, ccx, ccy, M = _nuc_with_windbreak()
    M["commons"] = [{"x": ccx - 70, "y": ccy - 70, "w": 80, "h": 200, "rot": 0}]  # NOT past the grove
    assert "commons_beyond_the_windbreak" in f(M)


def test_commons_beyond_the_windbreak_passes_when_past_the_grove():
    houses, ccx, ccy, M = _nuc_with_windbreak()
    M["commons"] = [{"x": ccx - 280, "y": ccy - 280, "w": 80, "h": 200, "rot": 0}]  # well beyond the belt
    assert "commons_beyond_the_windbreak" not in f(M)


def test_commons_beyond_the_windbreak_exempts_general_hinterland_land():
    # the general marginal hill land types - 'grazing' scrub, open 'pasture', coppice 'woodland' - are the
    # hinterland catena (any dry flank), NOT the windward fuel commons, so each is exempt even when NOT beyond
    # the windbreak; only the default fuel/fodder commons follows the toposequence rule.
    for role in ("grazing", "pasture", "woodland"):
        houses, ccx, ccy, M = _nuc_with_windbreak()
        M["commons"] = [{"x": ccx - 70, "y": ccy - 70, "w": 80, "h": 200, "rot": 0, "role": role}]
        assert "commons_beyond_the_windbreak" not in f(M)


def test_commons_beyond_check_skipped_without_a_windbreak():
    # nucleated + commons but NO windbreak grove -> the beyond-the-windbreak check cannot run (wbs empty)
    M = _nuc_village_M(_nuc_grid())
    M["commons"] = [{"x": 100, "y": 100, "w": 60, "h": 60, "rot": 0}]
    assert "commons_beyond_the_windbreak" not in f(M)


def test_poly_gap_overlap_containment_edgecross_and_separated():
    # poly_gap: 0 when one contains the other, 0 when edges CROSS with no vertex inside, else the min distance.
    sq = [[0, 0], [10, 0], [10, 10], [0, 10]]
    assert check_village.poly_gap(sq, [[3, 3], [5, 3], [5, 5], [3, 5]]) == 0.0  # containment
    bar1 = [[0, 4], [10, 4], [10, 6], [0, 6]]  # a + cross: edges cross,
    bar2 = [[4, 0], [6, 0], [6, 10], [4, 10]]  # no vertex inside the other
    assert check_village.poly_gap(bar1, bar2) == 0.0
    assert check_village.poly_gap(sq, [[20, 0], [30, 0], [30, 10], [20, 10]]) == 10.0  # separated by 10


def test_woodland_clear_of_crops_fires_on_overlap_and_shade_passes_when_set_back_north():
    # a managed-woodland patch must NOT overlap a crop NOR shade it from the sunny SOUTH side (trees cast
    # shadows north, maps are north-up); a patch set back to the NORTH is fine. Covers paddy + dry_plots.
    p = _field("p", 400, 400, 700, 600)
    base = {"meta": {"scale": "village"}, "fields": [p]}

    def wood(poly):
        cx = sum(v[0] for v in poly) / len(poly)
        cy = sum(v[1] for v in poly) / len(poly)
        return {"x": cx, "y": cy, "w": 100, "h": 100, "rot": 0, "role": "woodland", "poly": poly}

    over = {**base, "commons": [wood([[500, 450], [600, 450], [600, 550], [500, 550]])]}  # sits ON the paddy
    assert "woodland_clear_of_crops" in f(over)
    shade = {**base, "commons": [wood([[500, 612], [640, 612], [640, 660], [500, 660]])]}  # just SOUTH -> shades it
    assert "woodland_clear_of_crops" in f(shade)
    ok = {**base, "commons": [wood([[500, 300], [640, 300], [640, 344], [500, 344]])]}  # well NORTH -> clear
    assert "woodland_clear_of_crops" not in f(ok)
    dry = {
        **base,
        "dry_plots": [{"poly": [[800, 400], [900, 400], [900, 500], [800, 500]], "crop": "soy", "theta": 0.0}],
        "commons": [wood([[840, 420], [940, 420], [940, 520], [840, 520]])],
    }  # overlaps a DRY plot
    assert "woodland_clear_of_crops" in f(dry)


def test_woodland_clear_of_grove_fires_when_on_the_fengshui_grove():
    # a coppice woodland patch and the protected fengshui grove are DISTINCT woods - a patch sitting on a grove
    # clump fires; one on its own ground does not.
    p = _field("p", 400, 400, 700, 600)
    patch = {"x": 200, "y": 200, "w": 100, "h": 100, "rot": 0, "role": "woodland", "poly": [[150, 150], [250, 150], [250, 250], [150, 250]]}
    base = {"meta": {"scale": "village"}, "fields": [p], "commons": [patch]}
    on = {**base, "village_groves": [{"role": "windbreak", "x": 200, "y": 200, "r": 14, "clumps": [[200, 200]]}]}  # clump inside the patch
    assert "woodland_clear_of_grove" in f(on)
    off = {**base, "village_groves": [{"role": "windbreak", "x": 900, "y": 900, "r": 14, "clumps": [[900, 900]]}]}  # grove far away
    assert "woodland_clear_of_grove" not in f(off)


def test_gardens_clear_of_groves_fires_when_a_garden_is_buried():
    M = {
        "meta": {"scale": "village"},
        "houses": [_farmhouse(500, 500)],
        "gardens": [{"x": 540, "y": 500, "w": 24, "h": 16, "rot": 0, "of": [500, 500]}],
        "groves": [_grove(540, 500, 700, 700)],
    }  # grove sits squarely on the garden
    assert "gardens_clear_of_groves" in f(M)


def _big_grove(x, y, ofx, ofy):
    return _grove(x, y, ofx, ofy, w=44, h=34)  # area 1496 vs a 44x29=1276 house -> ~1.17x (substantial)


def test_groves_are_substantial_fires_on_tiny_groves():
    houses = [_farmhouse(300 + 60 * i, 300) for i in range(6)]
    groves = [_grove(285 + 60 * i, 270, 300 + 60 * i, 300, w=10, h=10) for i in range(6)]  # clumps, ~0.08x the house
    assert "groves_are_substantial" in f({"meta": {"scale": "village"}, "houses": houses, "groves": groves})


def test_groves_are_substantial_passes_with_belts():
    houses = [_farmhouse(300 + 60 * i, 300) for i in range(6)]
    groves = [_big_grove(300 + 60 * i, 300, 300 + 60 * i, 300) for i in range(6)]
    assert "groves_are_substantial" not in f({"meta": {"scale": "village"}, "houses": houses, "groves": groves})


_CITY_WALL = [[100, 100], [900, 100], [900, 900], [100, 900]]  # a closed square wall


def test_no_groves_inside_walls_fires():
    M = {"meta": {"scale": "city", "walled": True}, "wall": _CITY_WALL, "houses": [_farmhouse(500, 500)], "groves": [_grove(465, 470, 500, 500)]}  # of (500,500) is inside the wall
    assert "no_groves_inside_walls" in f(M)


def test_no_groves_inside_walls_passes_for_an_outside_farm():
    M = {"meta": {"scale": "city", "walled": True}, "wall": _CITY_WALL, "houses": [_farmhouse(1200, 500)], "groves": [_grove(1165, 470, 1200, 500)]}  # of (1200,500) is outside
    assert "no_groves_inside_walls" not in f(M)


def test_yards_unshaded_by_groves_fires():
    # a grove in the strip directly south of a threshing yard would shade its drying ground
    M = {
        "meta": {"scale": "village"},
        "houses": [_farmhouse(500, 500)],
        "threshing_yards": [{"x": 500, "y": 540, "w": 32, "h": 20, "rot": 0, "of": [500, 500]}],
        "groves": [_grove(500, 562, 700, 700)],
    }  # grove just south of the yard (its south edge ~550)
    assert "yards_unshaded_by_groves" in f(M)


def test_village_trees_unshade_fires_when_a_clump_is_south_of_a_yard():
    M = {
        "meta": {"scale": "village"},
        "threshing_yards": [{"x": 300, "y": 400, "w": 40, "h": 24, "rot": 0, "of": [300, 380]}],
        "village_groves": [{"role": "copse", "r": 11, "clumps": [[300, 430]], "poly": [[280, 415], [320, 415], [320, 445], [280, 445]]}],
    }  # clump S of the yard
    assert "village_trees_unshade_yards_and_gardens" in f(M)


def test_village_trees_unshade_fires_when_a_clump_is_south_of_a_garden():
    M = {
        "meta": {"scale": "village"},
        "gardens": [{"x": 300, "y": 400, "w": 30, "h": 20, "rot": 0, "of": [300, 380]}],
        "village_groves": [{"role": "copse", "r": 11, "clumps": [[300, 425]], "poly": [[280, 410], [320, 410], [320, 440], [280, 440]]}],
    }  # clump S of the garden
    assert "village_trees_unshade_yards_and_gardens" in f(M)


def test_village_trees_unshade_passes_when_the_clump_is_north():
    M = {
        "meta": {"scale": "village"},
        "threshing_yards": [{"x": 300, "y": 400, "w": 40, "h": 24, "rot": 0, "of": [300, 380]}],
        "village_groves": [
            {
                "role": "copse",
                "r": 11,
                "clumps": [[300, 300]],  # NORTH of the yard
                "poly": [[280, 285], [320, 285], [320, 315], [280, 315]],
            }
        ],
    }
    assert "village_trees_unshade_yards_and_gardens" not in f(M)


def test_farmhouse_sizes_vary_fires_when_flat():
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(300 + 60 * i, 300) for i in range(12)]}
    assert "farmhouse_sizes_vary" in f(M)  # _farmhouse has no wealth -> all at the baseline tier


def test_farmhouse_sizes_vary_passes_with_a_spread():
    houses = []
    for i in range(12):
        h = _farmhouse(300 + 60 * i, 300)
        h["wealth"] = 0.9 if i % 3 == 0 else (1.12 if i % 3 == 1 else 1.0)
        houses.append(h)
    assert "farmhouse_sizes_vary" not in f({"meta": {"scale": "village"}, "houses": houses})


# ---- provincial-city checks (scale="city"); tango.gen.py is the passing integration ---------
WALLSQ = [[200, 200], [800, 200], [800, 800], [200, 800]]  # a closed city ring


def test_city_required_structures_all_fire_on_an_empty_city():
    fails = f({"meta": {"scale": "city"}})
    for name in (
        "city_has_governor_mansion",
        "city_has_six_ministries",
        "city_has_ministry_of_rites",
        "city_has_samurai_neighborhood",
        "city_has_merchant_district",
        "city_has_laborer_neighborhoods",
        "city_has_outside_farmland",
    ):
        assert name in fails


def test_city_ministry_of_rites_fires_when_six_but_none_are_rites():
    mins = [{"x": i * 30, "y": 50, "w": 80, "h": 50, "name": f"Ministry {i}"} for i in range(6)]
    assert "city_has_ministry_of_rites" in f({"meta": {"scale": "city"}, "ministries": mins})


def _city_with_samurai(label_box):
    sam = [bldg(400, 400, kind="samurai"), bldg(440, 400, kind="samurai"), bldg(420, 440, kind="samurai")]
    return {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "buildings": sam, "labels": [label_box]}


def test_city_labels_placed_with_subject_fires_when_label_is_across_the_wall():
    # the samurai cluster is INSIDE the wall but its label floats OUTSIDE (over the moat) - misleading
    M = _city_with_samurai([850, 492, 950, 508, 0, "samurai neighborhood"])  # center (900,500), outside WALLSQ
    assert "city_labels_placed_with_subject" in f(M)


def test_city_labels_placed_with_subject_fires_when_label_far_from_cluster():
    # label inside the wall but nowhere near its samurai houses (they are at ~(420,420), label at (730,720))
    M = _city_with_samurai([680, 712, 780, 728, 0, "samurai neighborhood"])
    assert "city_labels_placed_with_subject" in f(M)


def test_city_labels_placed_with_subject_fires_when_label_over_a_field():
    # burakumin houses sit just south, but the label floats over a paddy to their north
    field = {"name": "f", "kind": "paddy", "bbox": [360, 360, 520, 520], "outline": [[360, 360], [520, 360], [520, 520], [360, 520]]}
    bur = [bldg(420, 540, kind="burakumin"), bldg(460, 540, kind="burakumin"), bldg(440, 500, kind="burakumin")]
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "buildings": bur,
        "fields": [field],
        "labels": [[390, 442, 490, 458, 0, "burakumin neighborhood"]],
    }  # center (440,450), inside field f
    assert "city_labels_placed_with_subject" in f(M)


def test_city_labels_placed_with_subject_skips_labels_with_no_known_subject():
    # a zone-suffix label whose subject we can't identify ("potters district" - no such building kind)
    # cannot be verified, so it is skipped rather than flagged
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "labels": [[850, 492, 950, 508, 0, "potters district"]]}
    assert "city_labels_placed_with_subject" not in f(M)


def test_city_labels_placed_with_subject_passes_when_among_the_cluster():
    # label inside the wall AND among its samurai houses (center ~(420,410)) - the correct placement
    M = _city_with_samurai([370, 402, 470, 418, 0, "samurai neighborhood"])
    assert "city_labels_placed_with_subject" not in f(M)


def test_city_samurai_housing_sufficient_fires_when_too_few():
    # a 3,000-pop city is ~300 samurai (~60 households); ~10 token houses is far too few - it must
    # depict the bulk of the samurai cohort, not a handful (this was Tango's 22).
    sam = [bldg(300 + i * 12, 300, kind="samurai") for i in range(10)]
    M = {"meta": {"scale": "city", "walled": True, "population": 3000, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "buildings": sam}
    assert "city_samurai_housing_sufficient" in f(M)


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


def test_city_flophouse_in_humble_quarter_fires_next_to_merchants():
    # an in-wall flophouse cheek-by-jowl with a merchant house - a doss-house does not belong in the
    # nicer quarter
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "flophouses": [{"x": 500, "y": 500, "w": 92, "h": 42, "rot": 0}],
        "buildings": [bldg(560, 500, kind="merchant")],
    }  # merchant 60px away
    assert "city_flophouse_in_humble_quarter" in f(M)


def test_city_flophouse_in_humble_quarter_fires_next_to_burakumin():
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "flophouses": [{"x": 500, "y": 500, "w": 92, "h": 42, "rot": 0}],
        "buildings": [bldg(580, 500, kind="burakumin")],
    }  # burakumin 80px away (in/beside the quarter)
    assert "city_flophouse_in_humble_quarter" in f(M)


def test_city_flophouse_in_humble_quarter_passes_when_humble_and_clear():
    # in-wall flophouse with only laborers nearby - the humble sector, correctly placed
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "flophouses": [{"x": 500, "y": 500, "w": 92, "h": 42, "rot": 0}],
        "buildings": [bldg(560, 500, kind="laborer"), bldg(540, 560, kind="laborer")],
    }
    assert "city_flophouse_in_humble_quarter" not in f(M)


def _merchant_city(buildings, estates=None):
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "buildings": buildings}
    if estates is not None:
        M["merchant_estates"] = estates
    return M


def test_city_merchant_housing_varied_fires_when_uniform():
    # a merchant quarter of nothing but small uniform houses - no large houses, no walled estates
    M = _merchant_city([bldg(300 + i * 30, 300, kind="merchant_house") for i in range(10)])
    assert "city_merchant_housing_varied" in f(M)


def test_city_merchant_housing_varied_passes_with_a_mix():
    blds = [bldg(300 + i * 30, 300, kind="merchant_large") for i in range(4)] + [bldg(300 + i * 30, 400, kind="merchant_house") for i in range(6)]
    M = _merchant_city(blds, estates=[{"x": 500, "y": 600, "w": 78, "h": 58}])
    assert "city_merchant_housing_varied" not in f(M)


def _samurai_varied_city(buildings, manors=None):
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "buildings": buildings}
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
    blds = [bldg(300 + i * 30, 300, kind="samurai_large") for i in range(4)] + [bldg(300 + i * 30, 400, kind="samurai") for i in range(8)]
    M = _samurai_varied_city(blds, manors=[{"x": 500, "y": 500, "w": 80, "h": 60}])  # inside WALLSQ
    assert "city_samurai_housing_varied" in f(M)


def test_city_samurai_housing_varied_passes_with_a_mix_and_estates_outside():
    blds = [bldg(300 + i * 30, 300, kind="samurai_large") for i in range(4)] + [bldg(300 + i * 30, 400, kind="samurai") for i in range(8)]
    M = _samurai_varied_city(blds, manors=[{"x": 900, "y": 500, "w": 80, "h": 60}])  # outside WALLSQ
    assert "city_samurai_housing_varied" not in f(M)


def _agri_city(houses, agri=True):
    # a city with an in-wall AGRICULTURAL field (the unusual jokamachi that farms inside the walls)
    field = {"name": "nw1", "kind": "paddy", "bbox": [350, 350, 550, 550], "outline": [[350, 350], [550, 350], [550, 550], [350, 550]]}  # ~800px perimeter, all in-wall
    hs = [{"kind": "plain", "rot": 0, "w": 18, "h": 12, **h} for h in houses]
    return {"meta": {"scale": "city", "walled": True, "agricultural_district": agri, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "fields": [field], "houses": hs}


def test_city_interior_fields_farmhouse_density_fires_when_under_farmed():
    # a real in-wall field with a single token farmhouse beside it - far below village density
    M = _agri_city([{"x": 360, "y": 320, "w": 18, "h": 12, "rot": 0}])
    assert "city_interior_fields_farmhouse_density" in f(M)


def test_city_interior_fields_farmhouse_density_passes_when_densely_ringed():
    # a dense ring wrapping the WHOLE perimeter (top, bottom, both sides) - a worked in-wall field
    houses = (
        [{"x": x, "y": 330} for x in range(360, 545, 30)]
        + [{"x": x, "y": 570} for x in range(360, 545, 30)]
        + [{"y": y, "x": 330} for y in range(380, 525, 30)]
        + [{"y": y, "x": 570} for y in range(380, 525, 30)]
    )
    M = _agri_city(houses)
    assert "city_interior_fields_farmhouse_density" not in f(M)


def test_city_interior_fields_farmhouse_density_skipped_without_agricultural_district():
    # an ordinary city (no in-wall farming declared) is not held to the rule even if a field strays inside
    M = _agri_city([], agri=False)
    assert "city_interior_fields_farmhouse_density" not in f(M)


def test_city_interior_fields_farmhouse_density_skips_a_tiny_field_sliver():
    # an in-wall field too small to merit its own farmhouse ring (edge < 120px) is skipped, not flagged
    tiny = {"name": "tiny", "kind": "paddy", "bbox": [480, 480, 505, 505], "outline": [[480, 480], [505, 480], [505, 505], [480, 505]]}  # ~100px perimeter
    M = {"meta": {"scale": "city", "walled": True, "agricultural_district": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "fields": [tiny], "houses": []}
    assert "city_interior_fields_farmhouse_density" not in f(M)


def _road_city(buildings, road=True):
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "buildings": buildings}
    if road:
        M["road"] = [[500, -40], [500, 500], [500, 1040]]  # runs off both edges, through the walls
    return M


def test_city_imperial_road_has_commerce_fires_when_road_frontage_is_bare():
    # the Imperial road runs through, but only housing lines it - no shops on the prime road frontage
    M = _road_city([bldg(300, 400, kind="laborer")])
    assert "city_imperial_road_has_commerce" in f(M)


def test_city_imperial_road_has_commerce_passes_when_road_is_lined():
    shops = [bldg(540, y, kind="shop") for y in range(300, 760, 70)]  # a commercial ribbon along the road
    M = _road_city(shops)
    assert "city_imperial_road_has_commerce" not in f(M)


def test_city_imperial_road_has_commerce_skipped_without_a_road():
    # a city with no Imperial road has no road-ribbon rule (its commerce stays in the market district)
    M = _road_city([bldg(540, y, kind="shop") for y in range(300, 760, 70)], road=False)
    assert "city_imperial_road_has_commerce" not in f(M)


def _unwalled_road_city(buildings):
    # an UNWALLED city: no wall, so the road's through-extent is the urban footprint (the building bbox)
    spread = [bldg(300 + i * 60, 250, kind="laborer") for i in range(8)] + [bldg(300 + i * 60, 750, kind="laborer") for i in range(8)]  # housing spanning the road on both sides
    return {"meta": {"scale": "city", "W": 1000, "H": 1000}, "gates": [], "road": [[500, -40], [500, 500], [500, 1040]], "buildings": spread + buildings}


def test_city_imperial_road_has_commerce_generic_for_an_unwalled_city_fires_when_bare():
    # the rule applies to ANY city with an Imperial road, walled or not - here an unwalled one runs bare
    assert "city_imperial_road_has_commerce" in f(_unwalled_road_city([]))


def test_city_imperial_road_has_commerce_generic_for_an_unwalled_city_passes_when_lined():
    shops = [bldg(540, y, kind="shop") for y in range(260, 760, 60)]  # a commercial ribbon along the road
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
    M = _lanes(streets=[[[500, 300], [500, 500]]], alleys=[[[500, 500], [500, 700]]])  # meet at (500,500)
    assert not check_village.lane_near_misses(M)


def test_lane_near_misses_ignores_parallel_ends_not_heading_at_each_other():
    # two parallel lanes whose ends sit side by side - neither points AT the other, so not a near-miss
    M = _lanes(streets=[[[300, 400], [500, 400]], [[300, 440], [500, 440]]])
    assert not check_village.lane_near_misses(M)


def test_lane_near_misses_respects_a_building_blocking_the_gap():
    M = _lanes(streets=[[[500, 300], [500, 480]]], alleys=[[[500, 510], [500, 700]]], buildings=[bldg(500, 495, kind="laborer")])
    assert not check_village.lane_near_misses(M)


def test_lane_near_misses_respects_a_ward_fence_blocking_the_gap():
    M = _lanes(streets=[[[500, 300], [500, 480]]], alleys=[[[500, 510], [500, 700]]], wards=[{"boundary": [[400, 495], [600, 495]]}])
    assert not check_village.lane_near_misses(M)


def test_lane_near_misses_respects_the_wall_blocking_the_gap():
    M = _lanes(streets=[[[500, 300], [500, 480]]], alleys=[[[500, 510], [500, 700]]], wall=[[400, 495], [600, 495], [600, 800], [400, 800]])  # top edge crosses the gap
    assert not check_village.lane_near_misses(M)


def test_lane_near_misses_skips_an_endpoint_meeting_the_wide_road():
    # a street ending against the Imperial road is CONNECTED (the road's job, not a near-miss)
    M = _lanes(streets=[[[300, 500], [485, 500]]], alleys=[[[600, 500], [800, 500]]], road=[[500, -40], [500, 1040]])
    assert not check_village.lane_near_misses(M)


def test_city_lanes_meet_when_aligned_fires_through_the_gate():
    M = _lanes(streets=[[[500, 300], [500, 480]]], alleys=[[[500, 510], [500, 700]]], meta={"scale": "city"})
    assert "city_lanes_meet_when_aligned" in f(M)


# --- city_lanes_reach_ward_gates (lanes at a neighborhood wall extend to it and end at a gate) ---
def _ward_lane(alleys=None, streets=None, fence=None, gov=(500, 640), **extra):
    M = {"wards": [{"boundary": fence or [[300, 500], [700, 500]]}]}  # a horizontal ward fence at y500
    if gov:
        M["governor_mansion"] = {"x": gov[0], "y": gov[1]}  # interior anchor, SOUTH of the fence
    if alleys is not None:
        M["alleys"] = [{"pts": p} for p in alleys]
    if streets is not None:
        M["town_streets"] = [{"pts": p, "w": 18} for p in streets]
    M.update(extra)
    return M


def test_lane_ward_shortfalls_flags_a_lane_stopping_short():
    M = _ward_lane(alleys=[[[500, 300], [500, 460]]])  # heads down at the fence, stops 40px short, no gate
    assert check_village.lane_ward_shortfalls(M)


def test_lane_ward_shortfalls_clear_when_lane_reaches_a_gate():
    M = _ward_lane(alleys=[[[500, 300], [500, 500]]], kido=[{"x": 500, "y": 500}])
    assert not check_village.lane_ward_shortfalls(M)


def test_lane_ward_shortfalls_flags_a_lane_meeting_the_fence_without_a_gate():
    M = _ward_lane(alleys=[[[500, 300], [500, 500]]])  # reaches the fence but no kido there
    assert check_village.lane_ward_shortfalls(M)


def test_lane_ward_shortfalls_respects_a_building_blocking_the_approach():
    M = _ward_lane(alleys=[[[500, 300], [500, 460]]], buildings=[bldg(500, 480, kind="laborer")])
    assert not check_village.lane_ward_shortfalls(M)


def test_lane_ward_shortfalls_respects_the_main_wall_between_lane_and_fence():
    M = _ward_lane(alleys=[[[500, 300], [500, 460]]], wall=[[300, 480], [700, 480], [700, 800], [300, 800]])
    assert not check_village.lane_ward_shortfalls(M)


def test_lane_ward_shortfalls_ignores_an_interior_ward_lane():
    M = _ward_lane(alleys=[[[500, 700], [500, 540]]])  # endpoint (500,540) is SOUTH of the fence - inside the ward
    assert not check_village.lane_ward_shortfalls(M)


def test_lane_ward_shortfalls_ignores_a_lane_running_parallel_to_the_fence():
    M = _ward_lane(alleys=[[[300, 460], [600, 460]]])  # parallel, above the fence - not heading at it
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
    M = {"meta": {"scale": "city"}, "wall": [[200, 200], [800, 200], [800, 800], [200, 800]], "wall_z": 10, "gates": [[500, 200]]}
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


# --- labels_render_on_top (label text is never covered) ---
def test_labels_render_on_top_fires_when_a_kido_covers_a_label():
    M = {"labels": [[100, 100, 300, 120, 5, "Ministry of Retainers"]], "kido": [{"x": 200, "y": 110, "z": 1000, "bbox": [150, 90, 250, 130]}]}
    assert "labels_render_on_top" in f(M)


def test_labels_render_on_top_fires_when_a_gate_structure_covers_a_label():
    M = {"labels": [[150, 100, 250, 120, 5, "gate label"]], "gate_structs": [{"x": 200, "y": 110, "w": 100, "h": 40, "z": 1000}]}
    assert "labels_render_on_top" in f(M)


def test_labels_render_on_top_fires_when_a_torii_covers_a_label():
    M = {"labels": [[185, 95, 215, 120, 5, "shrine"]], "torii": [[200, 110, 1000]]}
    assert "labels_render_on_top" in f(M)


def test_labels_render_on_top_passes_when_the_label_is_above():
    # same overlap, but the label's draw-z is higher than the structure's - it renders on top, readable
    M = {"labels": [[100, 100, 300, 120, 9999, "Ministry of Retainers"]], "kido": [{"x": 200, "y": 110, "z": 1000, "bbox": [150, 90, 250, 130]}]}
    assert "labels_render_on_top" not in f(M)


def test_labels_render_on_top_handles_a_textless_label():
    M = {
        "labels": [[150, 100, 250, 120, 5]],  # a field label recorded without text
        "kido": [{"x": 200, "y": 110, "z": 1000, "bbox": [150, 90, 250, 130]}],
    }
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


def test_margins_form_continuous_ring_passes_when_the_frame_is_clothed():
    # one commons band + the field cover the whole (small) view - only feathered seams left
    M = {
        "meta": {"scale": "village", "view": [0, 0, 400, 300]},
        "fields": [_field("p", 0, 0, 400, 150)],
        "commons": [{"poly": [[0, 140], [400, 140], [400, 300], [0, 300]], "role": "grazing"}],
    }
    assert "margins_form_continuous_ring" not in f(M)


def test_margins_form_continuous_ring_fires_on_bare_open_plain():
    # the real Ueda defect in miniature: the ring bands sit OFF-FRAME (west of the cropped view),
    # so the framed map is mostly bare open tan around a small field
    M = {
        "meta": {"scale": "village", "view": [500, 0, 400, 300]},
        "fields": [_field("p", 500, 0, 650, 150)],
        "commons": [{"poly": [[0, 0], [480, 0], [480, 300], [0, 300]], "role": "grazing"}],
    }
    assert "margins_form_continuous_ring" in f(M)


def test_margins_form_continuous_ring_ignores_town_and_city_sheets():
    # urban sheets cover the ground with streets/wards/walls these feature sets do not model -
    # the satoyama-ring doctrine is village/hamlet scope only
    M = {"meta": {"scale": "town", "view": [0, 0, 400, 300]}}
    assert "margins_form_continuous_ring" not in f(M)


def test_scatter_respects_swept_clearings_fires_on_cover_before_the_collar():
    # the real Ueda graveyard defect in miniature: the grazing band (seq 1) drew BEFORE the grave
    # collar was registered (clearing seq 1 = one cover already drawn), so tufts landed on swept ground
    M = {
        "meta": {"scale": "village"},
        "commons": [{"poly": [[50, 50], [400, 50], [400, 400], [50, 400]], "role": "grazing", "seq": 1}],
        "clearings": [{"poly": [[100, 100], [200, 100], [200, 200], [100, 200]], "seq": 1}],
    }
    assert "scatter_respects_swept_clearings" in f(M)


def test_scatter_respects_swept_clearings_passes_when_the_ground_was_reserved():
    # the documented reserve_clearing pattern: the collar is reserved (seq 0, before any cover), the
    # band draws (seq 1, skips it), then the cemetery registers its own duplicate collar late (seq 1) -
    # harmless, because a pre-cover guard clearing already protected every point of it
    M = {
        "meta": {"scale": "village"},
        "commons": [{"poly": [[50, 50], [400, 50], [400, 400], [50, 400]], "role": "grazing", "seq": 1}],
        "clearings": [
            {"poly": [[100, 100], [200, 100], [200, 200], [100, 200]], "seq": 0},
            {"poly": [[100, 100], [200, 100], [200, 200], [100, 200]], "seq": 1},
        ],
    }
    assert "scatter_respects_swept_clearings" not in f(M)


def test_scatter_respects_swept_clearings_passes_when_the_cover_draws_after():
    # normal order: clearing registered first (seq 0), the band draws after (seq 1) and skips it
    M = {
        "meta": {"scale": "village"},
        "commons": [{"poly": [[50, 50], [400, 50], [400, 400], [50, 400]], "role": "grazing", "seq": 1}],
        "clearings": [{"poly": [[100, 100], [200, 100], [200, 200], [100, 200]], "seq": 0}],
    }
    assert "scatter_respects_swept_clearings" not in f(M)


def test_crop_hugs_content_fires_when_the_frame_is_held_open():
    # Kikuta's defect in miniature: the north view edge sits ~385px above the northernmost
    # frame-setting content because the crop was holding the windbreak grove fully in frame
    M = {
        "meta": {"scale": "village", "view": [150, -300, 120, 455]},
        "houses": [{"x": 200, "y": 100, "w": 40, "h": 30, "rot": 0, "kind": "plain"}],
        "village_groves": [{"poly": [[100, -290], [300, -290], [300, 60], [100, 60]], "role": "windbreak"}],
    }
    assert "crop_hugs_content" in f(M)


def test_crop_hugs_content_passes_on_a_snug_frame():
    M = {
        "meta": {"scale": "village", "view": [150, 45, 120, 110]},
        "houses": [{"x": 200, "y": 100, "w": 40, "h": 30, "rot": 0, "kind": "plain"}],
    }
    assert "crop_hugs_content" not in f(M)


def test_hard_features_within_frame_lets_the_windbreak_clip_but_not_vanish():
    # a windbreak POKING past the frame edge is fine (part visible = "the wood continues";
    # the crop no longer holds the frame open for it) ...
    M = {
        "meta": {"scale": "village", "view": [0, 0, 400, 300]},
        "village_groves": [{"poly": [[100, -200], [300, -200], [300, 80], [100, 80]], "role": "windbreak"}],
    }
    assert "hard_features_within_frame" not in f(M)
    # ... but one ENTIRELY outside the view is a lost feature and still fires
    M2 = {
        "meta": {"scale": "village", "view": [0, 0, 400, 300]},
        "village_groves": [{"poly": [[100, -200], [300, -200], [300, -40], [100, -40]], "role": "windbreak"}],
    }
    assert "hard_features_within_frame" in f(M2)


def test_harvest_and_garden_checks_cover_the_headman():
    # the headman is a FARMSTEAD, not an exception to farmstead anatomy (GM 2026-07-21, caught on
    # Hikari no Sato): the old role=="headman" carve-out in occ_h existed only because the dispersed
    # headman() predated the homestead bundle and drew a lone house - a headman with no yard and no
    # garden now fires BOTH universal checks
    M = {
        "meta": {"scale": "village"},
        "houses": [{"x": 500, "y": 500, "w": 46, "h": 28, "rot": 0, "kind": "plain", "role": "headman"}],
    }
    fails = f(M)
    assert "harvest_yards_present" in fails
    assert "gardens_present" in fails


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


def test_wells_sized_to_population_bands():
    # the Rokugan prosperity liberty, banded (GM 2026-07-21): villages 8-26 hh/well, hamlets 2-20;
    # shrine temizu wells are excluded from the count
    base = {"meta": {"scale": "village", "households": 70}}
    M = {**base, "wells": [{"x": 100 * i, "y": 100, "r": 8, "shrine": False} for i in range(5)]}
    assert "wells_sized_to_population" not in f(M)  # 14 hh/well - in band
    M = {**base, "wells": [{"x": 100, "y": 100, "r": 8, "shrine": False}]}
    assert "wells_sized_to_population" in f(M)  # 70 hh/well - parched
    M = {**base, "wells": [{"x": 60 * i, "y": 100, "r": 8, "shrine": False} for i in range(12)]}
    assert "wells_sized_to_population" in f(M)  # 5.8 hh/well - urban-tenement density in a village
    M = {**base, "wells": [{"x": 100 * i, "y": 100, "r": 8, "shrine": False} for i in range(5)] + [{"x": 900, "y": 900, "r": 8, "shrine": True}] * 9}
    assert "wells_sized_to_population" not in f(M)  # shrine wells do not tip the band
    H = {"meta": {"scale": "hamlet", "households": 16}, "wells": [{"x": 100 * i, "y": 100, "r": 8, "shrine": False} for i in range(6)]}
    assert "wells_sized_to_population" not in f(H)  # 2.7 hh/well - per-farmstead hamlet pattern, in band
    H["wells"] = []
    assert "wells_sized_to_population" in f(H)  # a settlement with no draw-well at all


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
    return {"meta": {"scale": "city", "population": 300}, "buildings": blds}  # ~60 households


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


def test_no_structure_on_canal_fires_and_passes():
    # GM 2026-07 (Nagahara, first city with a cargo canal): a merchant house in the canal water
    canal = [{"poly": [[300, 500], [700, 500]], "w": 14}]
    fire = {"canals": canal, "buildings": [{"x": 500, "y": 500, "w": 24, "h": 18, "rot": 0, "kind": "merchant_house"}]}
    assert "no_structure_on_canal" in f(fire)
    ok = {"canals": canal, "buildings": [{"x": 500, "y": 440, "w": 24, "h": 18, "rot": 0, "kind": "merchant_house"}]}
    assert "no_structure_on_canal" not in f(ok)


def test_city_canal_reaches_dock_fires_when_short_and_passes_when_it_feeds_the_basin():
    # the canal must connect the river to the dock basin (like a street reaching the road)
    river = {"pts": [[900, 100], [900, 900]], "w": 40}
    dock = [{"x": 400, "y": 500, "w": 54, "h": 34, "rot": 0}]
    short = _fort_city(river=river, docks=dock, canals=[{"poly": [[884, 500], [460, 500]], "w": 14}])  # stops 33px short of the dock
    assert "city_canal_reaches_dock" in f(short)
    reach = _fort_city(river=river, docks=dock, canals=[{"poly": [[884, 500], [418, 500]], "w": 14}])  # end sits in the basin
    assert "city_canal_reaches_dock" not in f(reach)


def test_city_wharf_jetties_on_bank_fires_when_floating_and_passes_on_the_bank():
    # a jetty is a finger from the near bank into the water, not a bar floating mid-stream
    river = {"pts": [[900, 100], [900, 900]], "w": 40}  # centerline x900, near (city) bank x880
    fire = _fort_city(river=river, jetties=[{"x": 860, "y": 500, "rot": 0, "len": 80}])
    assert "city_wharf_jetties_on_bank" in f(fire)
    ok = _fort_city(river=river, jetties=[{"x": 876, "y": 500, "rot": 0, "len": 18}])  # root at the bank, tip in the near water
    assert "city_wharf_jetties_on_bank" not in f(ok)


def test_funerary_clear_of_fields_fires_when_a_cremation_ground_sits_on_a_field():
    # GM 2026-07 (Nagahara): a cremation ground on the far-bank comb's crop + ditch
    field = [{"name": "fe1", "kind": "paddy", "outline": [[300, 300], [700, 300], [700, 700], [300, 700]], "bbox": [300, 300, 700, 700]}]
    fire = {"fields": field, "cremation_grounds": [{"x": 500, "y": 500, "w": 116, "h": 80, "rot": 0}]}
    assert "funerary_clear_of_fields" in f(fire)
    ok = {"fields": field, "cremation_grounds": [{"x": 500, "y": 850, "w": 116, "h": 80, "rot": 0}]}
    assert "funerary_clear_of_fields" not in f(ok)


def test_city_estates_clear_of_roads_fires_when_an_estate_straddles_the_road():
    # GM 2026-07 (Nagahara): a samurai estate on the bridge road out of the city
    base = dict(roads=[{"pts": [[850, 850], [1200, 1100]], "w": 26}], road_width=26)
    fire = _fort_city(manors=[{"x": 1000, "y": 965, "w": 90, "h": 60, "rot": 0, "gate_dir": "south"}], **base)
    assert "city_estates_clear_of_roads" in f(fire)
    ok = _fort_city(manors=[{"x": 1000, "y": 700, "w": 90, "h": 60, "rot": 0, "gate_dir": "south"}], **base)
    assert "city_estates_clear_of_roads" not in f(ok)


def test_city_estates_toward_capital_respects_the_declared_direction():
    # GM 2026-07: estates cluster toward Otosan Uchi - per-city (Tango SE, Nagahara NE)
    ne = [{"x": 900, "y": 100, "w": 90, "h": 60, "rot": 0, "gate_dir": "south"}]  # NE of the wall centroid (500,500)
    M = _fort_city(manors=ne)
    M["meta"]["capital_dir"] = "northeast"
    assert "city_estates_toward_capital" not in f(M)
    M2 = _fort_city(manors=ne)
    M2["meta"]["capital_dir"] = "southeast"  # they are NOT to the SE
    assert "city_estates_toward_capital" in f(M2)


def test_city_temples_dedicated_requires_the_clan_patron_fortunes():
    # GM 2026-07 (Nagahara, Crab): a great Temple of Suitengu is wrong - Crab patrons are Bishamon + Ebisu
    def temples(*names):
        return [{"x": 300 + 40 * i, "y": 300, "w": 100, "h": 64, "rot": 0, "kind": "temple", "label": f"Temple of {n}"} for i, n in enumerate(names)]

    stray = _fort_city(religious=temples("Bishamon", "Ebisu", "Suitengu"))
    stray["meta"]["clan"] = "Crab"
    assert "city_temples_dedicated" in f(stray)
    good = _fort_city(religious=temples("Bishamon", "Ebisu"))
    good["meta"]["clan"] = "Crab"
    assert "city_temples_dedicated" not in f(good)
    missing = _fort_city(religious=temples("Bishamon"))
    missing["meta"]["clan"] = "Crab"  # only one patron present
    assert "city_temples_dedicated" in f(missing)


def test_kido_clear_of_buildings_fires_when_a_row_house_sits_under_the_guard_box():
    # GM 2026-07: both fence-end kido guard boxes had row houses under them - the packs run long
    # before s.ward draws the gates, so the gen must reserve each kido's ground up front
    M = _fort_city(kido=[{"x": 400, "y": 500, "horizontal": False, "bbox": [385, 480, 415, 520]}], buildings=[{"x": 390, "y": 505, "w": 20, "h": 14, "rot": 0, "kind": "samurai"}])
    assert "kido_clear_of_buildings" in f(M)


def test_kido_clear_of_buildings_passes_when_the_gate_ground_is_open():
    M = _fort_city(kido=[{"x": 400, "y": 500, "horizontal": False, "bbox": [385, 480, 415, 520]}], buildings=[{"x": 390, "y": 560, "w": 20, "h": 14, "rot": 0, "kind": "samurai"}])
    assert "kido_clear_of_buildings" not in f(M)


def test_kido_clear_of_wall_towers_fires_when_a_ward_gate_hugs_a_tower():
    # GM 2026-07: the E ward-fence kido's guard box sat inside the mural tower at the wall vertex
    # below the samurai neighborhood gate (both classes are overlap-EXEMPT, so nothing caught it)
    M = _fort_city(kido=[{"x": 210, "y": 500, "horizontal": False, "bbox": [195, 480, 225, 520]}], wall_towers=[{"x": 205, "y": 505, "w": 38, "h": 38, "rot": 0}])
    assert "kido_clear_of_wall_towers" in f(M)


def test_kido_clear_of_wall_towers_passes_when_the_tower_stands_off():
    M = _fort_city(kido=[{"x": 210, "y": 500, "horizontal": False, "bbox": [195, 480, 225, 520]}], wall_towers=[{"x": 205, "y": 570, "w": 38, "h": 38, "rot": 0}])
    assert "kido_clear_of_wall_towers" not in f(M)


def test_city_wall_furniture_clear_of_moat_fires_when_a_tower_stands_in_the_bed():
    # a tower centered on the wall line pokes its outer face into a close-set moat's bed (GM 2026-07:
    # every Tango tower did - the gap=24 moat leaves a 13px berm vs a 19-20px tower half-width)
    moat = [[176, 176], [824, 176], [824, 824], [176, 824], [176, 176]]
    M = _fort_city(moat=moat, moat_width=22, wall_towers=[{"x": 200, "y": 500, "w": 38, "h": 38, "rot": 0}])
    assert "city_wall_furniture_clear_of_moat" in f(M)


def test_city_wall_furniture_clear_of_moat_passes_when_nudged_onto_the_berm():
    # the placement fix: the tower nudged inward so only ~8px of its face projects past the wall line
    moat = [[176, 176], [824, 176], [824, 824], [176, 824], [176, 176]]
    M = _fort_city(moat=moat, moat_width=22, wall_towers=[{"x": 212, "y": 500, "w": 38, "h": 38, "rot": 0}])
    assert "city_wall_furniture_clear_of_moat" not in f(M)


def test_city_wall_towers_spaced_fires_with_only_gate_towers():
    M = _fort_city(wall_towers=[{"x": 500, "y": 200}, {"x": 500, "y": 800}])  # only the 2 gate towers
    assert "city_wall_towers_spaced" in f(M)


def test_city_wall_towers_spaced_passes_when_ringed():
    import math

    towers = [{"x": 500 + 300 * math.cos(i * math.pi / 5), "y": 500 + 300 * math.sin(i * math.pi / 5)} for i in range(10)]
    assert "city_wall_towers_spaced" not in f(_fort_city(wall_towers=towers))


_DIAMOND = [[500, 200], [800, 500], [500, 800], [200, 500]]  # a wall whose edges run at 45 deg


def test_city_wall_towers_aligned_fires_when_axis_aligned_on_a_slanted_wall():
    M = _fort_city(wall=_DIAMOND, wall_towers=[{"x": 650, "y": 350, "rot": 0}, {"x": 350, "y": 650, "rot": 0}])
    assert "city_wall_towers_aligned" in f(M)


def test_city_wall_towers_aligned_passes_when_square_to_the_wall():
    # both towers sit on a 45 deg wall edge and are rotated 45 deg to match it
    M = _fort_city(wall=_DIAMOND, wall_towers=[{"x": 650, "y": 350, "rot": 45}, {"x": 350, "y": 650, "rot": 45}])
    assert "city_wall_towers_aligned" not in f(M)


def _gate_furn(rot, wall=None, gates=None):
    return _fort_city(
        wall=wall or WALLSQ,
        gates=gates or [[500, 200], [500, 800]],
        gate_structs=[{"x": 420, "y": 256, "w": 66, "h": 44, "rot": rot, "kind": "guardhouse", "z": 1}, {"x": 360, "y": 256, "w": 60, "h": 44, "rot": rot, "kind": "inspection", "z": 1}],
    )


def test_city_gate_furniture_aligned_fires_when_axis_aligned_on_a_slanted_wall():
    # guard house + inspection station left axis-aligned (rot 0) on a 45 deg wall edge
    M = _gate_furn(0, wall=_DIAMOND, gates=[[650, 350], [350, 650]])
    M["gate_structs"] = [{"x": 640, "y": 360, "w": 66, "h": 44, "rot": 0, "kind": "guardhouse", "z": 1}, {"x": 610, "y": 390, "w": 60, "h": 44, "rot": 0, "kind": "inspection", "z": 1}]
    assert "city_gate_furniture_aligned" in f(M)


def test_city_gate_furniture_aligned_passes_when_square_to_the_wall():
    M = _gate_furn(45, wall=_DIAMOND, gates=[[650, 350], [350, 650]])
    M["gate_structs"] = [{"x": 640, "y": 360, "w": 66, "h": 44, "rot": 45, "kind": "guardhouse", "z": 1}, {"x": 610, "y": 390, "w": 60, "h": 44, "rot": 45, "kind": "inspection", "z": 1}]
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
    M = _fort_city(road=[[500, 100], [500, 900]], road_width=26, town_streets=[{"pts": [[300, 500], [470, 500]], "w": 18}])
    assert "city_streets_meet_through_lanes" in f(M)


def test_city_streets_meet_through_lanes_passes_when_it_meets_the_bed():
    assert "city_streets_meet_through_lanes" not in f(_ring_city([[[400, 500], [248, 500]]]))  # ends in the ring bed


def test_city_streets_meet_through_lanes_fires_when_an_alley_undershoots_the_ring():
    # the check covers gravel ALLEYS too, not just paved streets - the laborer-warren case the GM caught:
    # an alley running straight at the ring and stopping ~40px short
    M = _fort_city(ring_road=_RING, ring_road_width=15, alleys=[{"pts": [[400, 500], [280, 500]]}])
    assert "city_streets_meet_through_lanes" in f(M)


def test_city_streets_meet_through_lanes_passes_when_an_alley_meets_the_ring():
    M = _fort_city(ring_road=_RING, ring_road_width=15, alleys=[{"pts": [[400, 500], [246, 500]]}])  # ends in the ring bed
    assert "city_streets_meet_through_lanes" not in f(M)


# --- ring_road_kept_clear (no building/civic/field footprint overlaps the ring road bed) ---
def _on_ring_bldg():  # a 40px dwelling straddling the west ring leg (x=240)
    return {"kind": "samurai", "x": 240, "y": 500, "w": 40, "h": 40, "rot": 0}


def test_ring_road_kept_clear_fires_on_a_building_on_the_ring():
    assert "ring_road_kept_clear" in f(_fort_city(ring_road=_RING, ring_road_width=15, buildings=[_on_ring_bldg()]))


def test_ring_road_kept_clear_fires_on_a_ministry_on_the_ring():
    M = _fort_city(ring_road=_RING, ring_road_width=15, ministries=[{"name": "Ministry of Rites", "x": 760, "y": 500, "w": 50, "h": 50}])
    assert "ring_road_kept_clear" in f(M)


def test_ring_road_kept_clear_fires_on_a_field_on_the_ring():
    field = {"name": "f1", "kind": "dry", "bbox": [220, 480, 260, 520], "outline": [[220, 480], [260, 480], [260, 520], [220, 520]]}  # straddles the west leg
    assert "ring_road_kept_clear" in f(_fort_city(ring_road=_RING, ring_road_width=15, fields=[field]))


def test_ring_road_kept_clear_passes_when_clear():
    # a dwelling parked in the city center, well inside the ring
    M = _fort_city(ring_road=_RING, ring_road_width=15, buildings=[{"kind": "samurai", "x": 500, "y": 500, "w": 40, "h": 40, "rot": 0}])
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
    return {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "religious": religious}


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
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "merchant_estates": estates}
    M.update(extra)
    return M


def test_city_merchant_estates_clear_of_wall_moat_fires():
    # an estate COURT straddling the TOP wall (not just the house inside)
    assert "city_merchant_estates_clear_of_wall_moat" in f(_estate_city([{"x": 500, "y": 210, "w": 78, "h": 58}]))


def test_city_merchant_estates_clear_of_buildings_fires_on_a_temple():
    # an estate court over a temple whose CENTER is outside the court (so it is not its own inner house)
    M = _estate_city([{"x": 500, "y": 500, "w": 78, "h": 58}], religious=[{"x": 500, "y": 560, "w": 80, "h": 80, "kind": "temple", "label": "Temple"}])
    assert "city_merchant_estates_clear_of_buildings" in f(M)


def test_city_merchant_estates_clear_of_buildings_fires_on_another_estate():
    # two estate courts overlapping each other (the for-else estate-vs-estate path)
    M = _estate_city([{"x": 500, "y": 500, "w": 78, "h": 58}, {"x": 540, "y": 500, "w": 78, "h": 58}])
    assert "city_merchant_estates_clear_of_buildings" in f(M)


def test_city_merchant_estate_gate_clear_fires_when_gate_into_a_temple():
    # the estate wall abuts a temple below it (fine), but its gate opens SOUTH straight into the temple
    M = _estate_city([{"x": 500, "y": 500, "w": 78, "h": 58, "gate": [500, 529], "gate_dir": "south"}], religious=[{"x": 500, "y": 560, "w": 80, "h": 60, "kind": "temple", "label": "T"}])
    assert "city_merchant_estate_gate_clear" in f(M)


def test_city_merchant_estate_gate_clear_passes_when_gate_points_away():
    # same abutting temple, but the gate opens NORTH onto open ground
    M = _estate_city([{"x": 500, "y": 500, "w": 78, "h": 58, "gate": [500, 471], "gate_dir": "north"}], religious=[{"x": 500, "y": 560, "w": 80, "h": 60, "kind": "temple", "label": "T"}])
    assert "city_merchant_estate_gate_clear" not in f(M)


def test_city_merchant_estates_clear_passes_when_well_placed():
    M = _estate_city([{"x": 500, "y": 500, "w": 78, "h": 58}], buildings=[{"x": 500, "y": 500, "w": 36, "h": 25, "rot": 0, "kind": "merchant_large"}])
    assert "city_merchant_estates_clear_of_wall_moat" not in f(M)
    assert "city_merchant_estates_clear_of_buildings" not in f(M)


def test_city_merchant_housing_spread_passes_when_roomier():
    homes = [bldg(300 + i * 44, 300, kind="merchant_house") for i in range(8)]  # 44px apart
    labor = [bldg(300 + i * 16, 500, kind="laborer") for i in range(8)]  # 16px apart (dense)
    assert "city_merchant_housing_spread" not in f(_merchant_city(homes + labor))


def _ward_city(boundary):
    return {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "wards": [{"name": "x", "boundary": boundary}]}


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
    return {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": [[320, 320], [680, 320], [680, 680], [320, 680]],
        "moat": [[300, 300], [700, 300], [700, 700], [300, 700]],
        "streams": [{"poly": [[500, 40], [500, 300]], "frm": {"kind": "offmap"}, "to": {"kind": "moat"}}],
        "channels": [{"poly": channel_poly, "frm": {"kind": "moat"}, "to": {"kind": "field", "name": "f"}}],
        "gates": [[500, 300], [500, 700]],
    }


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
    field = {"name": "f1", "kind": "paddy", "bbox": [300, 300, 700, 700], "outline": [[300, 300], [700, 300], [700, 700], [300, 700]]}
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
    field = {"name": "f1", "kind": "paddy", "bbox": [-400, -400, 50, 50], "outline": [[-400, -400], [50, -400], [50, 50], [-400, 50]]}  # only a ~50x50 corner shows
    M = {"meta": {"scale": "town", "W": 1000, "H": 1000}, "fields": [field], "houses": []}
    assert "outside_fields_farmhouse_density" not in f(M)


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


def test_city_samurai_partly_front_streets_fires_when_all_set_back():
    # plenty of samurai houses but every one buried far from the street: a samurai quarter LINES its
    # streets, so an all-interior cluster (none within 90px of a lane) trips the check.
    sam = [bldg(300 + (i % 8) * 30, 300 + (i // 8) * 30, kind="samurai") for i in range(40)]  # all up in the NW corner
    M = {
        "meta": {"scale": "city", "walled": True, "population": 3000, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "town_streets": [{"pts": [[600, 600], [800, 600]], "w": 18}],  # the only street is far from the cluster
        "buildings": sam,
    }
    assert "city_samurai_partly_front_streets" in f(M)


def test_walled_city_structural_checks_fire():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200]]}  # only ONE gate, no stations / burakumin / estates / road
    fails = f(M)
    assert "walled_city_has_wall_and_gates" in fails
    assert "city_inspection_station_at_each_gate" in fails
    assert "walled_city_has_burakumin_inside" in fails
    assert "city_samurai_estates_outside" in fails  # 0 estates, want 5-15
    assert "city_imperial_road_through" in fails


def test_city_samurai_estates_vary_in_size_fires_when_uniform():
    estates = [{"x": 900 + i * 12, "y": 900, "w": 100, "h": 80} for i in range(6)]  # 6 (in range), all identical
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "manors": estates}
    fails = f(M)
    assert "city_samurai_estates_vary_in_size" in fails
    assert "city_samurai_estates_outside" not in fails  # 6 IS in the 5-15 range


def test_city_streets_have_buildings_fires_on_an_empty_city_street():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "town_streets": [{"pts": [[300, 300], [700, 300]], "w": 20}]}
    assert "city_streets_have_buildings" in f(M)


def test_city_streets_have_buildings_ignores_frontage_across_a_ward_fence():
    # the buildings hug the street (60px away) but a ward fence runs BETWEEN them and it: they front
    # whatever lies on their own side, not this street, so the street still reads as empty and fires.
    # (This is the Tango government-avenue bug: gap-band housing across the ward fence papered over a
    # bare avenue. A building walled off from a street cannot count as fronting it.)
    blds = [bldg(320 + i * 40, 440, kind="laborer") for i in range(9)]  # y440: 60px N of the street, N of the fence
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "town_streets": [{"pts": [[300, 500], [700, 500]], "w": 20}],
        "wards": [{"name": "x", "boundary": [[280, 470], [720, 470]]}],  # fence between the houses and the street
        "buildings": blds,
    }
    assert "city_streets_have_buildings" in f(M)


def _street_city(streets, **extra):
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "town_streets": streets}
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
    M = _street_city([{"pts": [[300, 500], [700, 500]], "w": 18}], ministries=[{"name": "A", "x": 400, "y": 565, "w": 88, "h": 58}, {"name": "B", "x": 620, "y": 565, "w": 88, "h": 58}])
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
    M = _caravan_city(
        flophouses=[{"x": 450, "y": 300, "w": 88, "h": 42, "rot": 0}],
        buildings=[{"x": 520, "y": 320, "w": 66, "h": 48, "kind": "inn", "rot": 0}, {"x": 470, "y": 380, "w": 92, "h": 44, "kind": "stables", "rot": 0}],
    )
    assert "city_gate_caravan_facilities" not in f(M)


def test_city_gate_caravan_facilities_fires_when_stables_hemmed_in():
    # the full cluster is present, but the stables is hemmed in by dwellings (no open ground for animals)
    blds = [{"x": 470, "y": 380, "w": 92, "h": 44, "kind": "stables", "rot": 0}, {"x": 520, "y": 320, "w": 66, "h": 48, "kind": "inn", "rot": 0}]
    blds += [bldg(440 + i * 22, 380, kind="samurai") for i in range(6)]  # dwellings crowd the stables
    M = _caravan_city(flophouses=[{"x": 450, "y": 300, "w": 88, "h": 42, "rot": 0}], buildings=blds)
    assert "city_gate_caravan_facilities" in f(M)


def test_city_theater_stage_larger_than_town_fires_when_small():
    # a town-sized theater stage (viewing ground 150 wide) in a city - a city's is larger (>= 185)
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "theater_stage": {"x": 500, "y": 500, "w": 150, "h": 105, "rot": 0},
        "religious": [{"x": 540, "y": 540, "w": 120, "h": 80, "rot": 0, "kind": "temple"}],
    }
    assert "city_theater_stage_larger_than_town" in f(M)


def test_theater_stage_by_temple_fires_when_far_from_any_hall():
    # a town theater stage sited off on its own, far from any temple/monastery - it was a temple/shrine
    # performance stage, so it must sit ADJACENT to a religious hall
    M = {"meta": {"scale": "town"}, "theater_stage": {"x": 500, "y": 500, "w": 150, "h": 105, "rot": 0}, "religious": [{"x": 1200, "y": 1200, "w": 132, "h": 86, "rot": 0, "kind": "monastery"}]}
    assert "theater_stage_by_temple" in f(M)


def test_theater_stage_by_temple_passes_when_adjacent():
    M = {"meta": {"scale": "town"}, "theater_stage": {"x": 500, "y": 500, "w": 150, "h": 105, "rot": 0}, "religious": [{"x": 540, "y": 620, "w": 132, "h": 86, "rot": 0, "kind": "monastery"}]}
    assert "theater_stage_by_temple" not in f(M)


def test_theater_stage_faces_temple_fires_when_back_to_the_hall():
    # adjacent to the monastery (NORTH) but the stage's viewing ground opens SOUTH (rot=0) - its BACK is to
    # the hall, the audience facing away. This is the Hoshizora bug the check is meant to catch.
    M = {"meta": {"scale": "town"}, "theater_stage": {"x": 500, "y": 500, "w": 150, "h": 105, "rot": 0}, "religious": [{"x": 510, "y": 380, "w": 132, "h": 86, "rot": 0, "kind": "monastery"}]}
    assert "theater_stage_faces_temple" in f(M)


def test_theater_stage_faces_temple_passes_when_open_toward_hall():
    # the hall is SOUTH and the ground opens SOUTH (rot=0) - the stage faces the hall, audience between
    M = {"meta": {"scale": "town"}, "theater_stage": {"x": 500, "y": 500, "w": 150, "h": 105, "rot": 0}, "religious": [{"x": 510, "y": 640, "w": 132, "h": 86, "rot": 0, "kind": "monastery"}]}
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
    M = {"meta": {"scale": "town"}, "theater_stage": dict(_STAGE), "religious": [{"x": 510, "y": 640, "w": 132, "h": 86, "rot": 0, "kind": "monastery"}]}
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
    M = _lbl_city(labels=[[470, 490, 560, 510, 1, "gate guard house + inspection"]], flophouses=[{"x": 500, "y": 500, "w": 90, "h": 42, "rot": 0}])
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
    M = {
        "meta": {"scale": "city"},
        "ministries": [{"name": "Ministry of Works", "x": 500, "y": 500, "w": 88, "h": 58}, {"name": "Ministry of Justice", "x": 500, "y": 640, "w": 88, "h": 58}],
        "labels": [[470, 490, 560, 510, 1, "Ministry of Justice"]],
    }
    assert "city_civic_label_on_its_own_building" in f(M)
    assert "labels_clear_of_other_buildings" not in f(M)  # the coarse check is fooled by the shared group


def test_city_civic_label_on_its_own_building_passes_over_its_own():
    M = {"meta": {"scale": "city"}, "ministries": [{"name": "Ministry of Works", "x": 500, "y": 500, "w": 88, "h": 58}], "labels": [[470, 490, 560, 510, 1, "Ministry of Works"]]}
    assert "city_civic_label_on_its_own_building" not in f(M)


# --- city_government_offices_dont_abut (a ministry / the yamen must stand clear of its neighbors) ---
def test_city_government_offices_dont_abut_fires_when_two_ministries_touch():
    M = {
        "meta": {"scale": "city"},
        "ministries": [{"name": "Ministry of Works", "x": 500, "y": 500, "w": 88, "h": 58}, {"name": "Ministry of Justice", "x": 500, "y": 560, "w": 88, "h": 58}],
    }  # 2px gap
    assert "city_government_offices_dont_abut" in f(M)


def test_city_government_offices_dont_abut_passes_when_clear():
    M = {
        "meta": {"scale": "city"},
        "ministries": [{"name": "Ministry of Works", "x": 500, "y": 500, "w": 88, "h": 58}, {"name": "Ministry of Justice", "x": 500, "y": 640, "w": 88, "h": 58}],
    }  # 82px gap
    assert "city_government_offices_dont_abut" not in f(M)


def test_city_government_offices_dont_abut_ignores_ordinary_houses():
    # ordinary city houses MAY touch - only government offices must stand clear
    M = {"meta": {"scale": "city"}, "buildings": [{"kind": "laborer", "x": 500, "y": 500, "w": 14, "h": 10, "rot": 0}, {"kind": "laborer", "x": 512, "y": 500, "w": 14, "h": 10, "rot": 0}]}
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
    M = _well_city(wall=WALLSQ, buildings=[{"kind": "samurai", "x": 500, "y": 500, "w": 56, "h": 40, "rot": 0}, {"kind": "merchant", "x": 980, "y": 980, "w": 40, "h": 30, "rot": 0}])
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
    M = _well_city(
        buildings=[
            {"kind": "samurai", "x": 510, "y": 505, "w": 24, "h": 17, "rot": 0},
            {"kind": "samurai", "x": 480, "y": 520, "w": 24, "h": 17, "rot": 0},
            {"kind": "laborer", "x": 900, "y": 900, "w": 14, "h": 10, "rot": 0},
        ]
    )
    assert "city_samurai_quarter_has_no_public_wells" in f(M)


def test_city_samurai_quarter_has_no_public_wells_passes_among_commoners():
    # the same well, but it sits among commoner dwellings (a samurai house is a block away) - fine
    M = _well_city(
        buildings=[
            {"kind": "laborer", "x": 510, "y": 505, "w": 14, "h": 10, "rot": 0},
            {"kind": "laborer", "x": 480, "y": 520, "w": 14, "h": 10, "rot": 0},
            {"kind": "samurai", "x": 900, "y": 900, "w": 24, "h": 17, "rot": 0},
        ]
    )
    assert "city_samurai_quarter_has_no_public_wells" not in f(M)


def test_city_streets_connected_and_empty_space_fire():
    # two town streets far apart with no road -> two disconnected groups; the interior is almost
    # all empty (no buildings/fields), and a pond sits on a grid point (the pond-as-occupancy path)
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": [[100, 100], [900, 100], [900, 900], [100, 900]],
        "gates": [[500, 100], [500, 900]],
        "town_streets": [{"pts": [[200, 200], [200, 400]], "w": 18}, {"pts": [[700, 600], [700, 800]], "w": 18}],
        "pond": [400, 400, 80, 60],
    }
    fails = f(M)
    assert "city_streets_connected" in fails
    assert "city_no_large_empty_space" in fails


def test_city_streets_connected_fires_on_a_gap_wider_than_45px():
    # two parallel streets 60px apart: the old 95px tolerance bridged them, the tightened 45px
    # does not - a grid that stops short of the road reads as a separated network, not connected
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "town_streets": [{"pts": [[400, 300], [400, 700]], "w": 18}, {"pts": [[460, 300], [460, 700]], "w": 18}],
    }  # 60px apart, no road bridge
    assert "city_streets_connected" in f(M)


def test_city_streets_connected_requires_beds_to_actually_overlap():
    # a cross-street whose end stops 30px short of the through-street: under the old flat 45px
    # tolerance this "connected", but the two paved beds (half-widths 9+9) do not touch, so you
    # cannot walk between them - it is a separate network. This is the Tango laborer-grid bug.
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "town_streets": [
            {"pts": [[300, 400], [700, 400]], "w": 18},  # the through-street
            {"pts": [[400, 430], [400, 700]], "w": 18},
        ],
    }  # ends 30px below it: beds 18px apart
    assert "city_streets_connected" in f(M)


def test_city_flophouse_inside_walls_fires_when_only_outside():
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "flophouses": [{"x": 500, "y": 120, "w": 92, "h": 42, "rot": 0}, {"x": 500, "y": 880, "w": 92, "h": 42, "rot": 0}],
    }
    assert "city_flophouse_inside_walls" in f(M)


def test_city_flophouse_outside_each_gate_fires_when_a_gate_lacks_one():
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "flophouses": [
            {"x": 500, "y": 500, "w": 92, "h": 42, "rot": 0},  # inside
            {"x": 500, "y": 120, "w": 92, "h": 42, "rot": 0},
        ],
    }  # outside the north gate only
    assert "city_flophouse_outside_each_gate" in f(M)


def test_city_estates_multiple_shown_fires_when_only_one_in_view():
    M = {
        "meta": {"scale": "city", "walled": True, "W": 3000, "H": 3000, "view": [0, 0, 1000, 1000]},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "manors": [
            {"x": 600, "y": 600, "w": 100, "h": 80},  # inside the view
            {"x": 2000, "y": 2000, "w": 100, "h": 80},
        ],
    }  # off the cropped view
    assert "city_estates_multiple_shown" in f(M)


def test_city_road_label_outside_walls_fires_when_inside():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "road_label": [500, 500]}  # dead center, inside the walls
    assert "city_road_label_outside_walls" in f(M)


def test_city_streets_no_near_miss_fires_on_a_sliver_gap():
    # two street segments ~18px apart that do NOT cross - they almost touch but never meet
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "town_streets": [
            {"pts": [[300, 400], [500, 400]], "w": 18},  # ends at (500, 400)
            {"pts": [[515, 410], [515, 700]], "w": 18},
        ],
    }  # top at (515, 410): an ~18px gap
    assert "city_streets_no_near_miss" in f(M)


def test_city_ministries_front_a_street_fires_when_floating():
    # a ministry with the nearest street ~290px away - it floats mid-block, fronting nothing
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "ministries": [{"x": 500, "y": 500, "w": 88, "h": 58, "name": "Ministry of War"}],
        "town_streets": [{"pts": [[250, 250], [350, 250]], "w": 18}],
    }
    assert "city_ministries_front_a_street" in f(M)


def test_city_ministries_front_a_street_passes_when_on_a_street():
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "ministries": [{"x": 500, "y": 500, "w": 88, "h": 58, "name": "Ministry of War"}],
        "town_streets": [{"pts": [[300, 560], [700, 560]], "w": 18}],
    }  # an avenue 60px from the office
    assert "city_ministries_front_a_street" not in f(M)


def test_city_streets_no_intersection_stub_fires_on_a_short_overshoot():
    # a vertical street crosses a horizontal one and then stops 25px past it - a dangling stub
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "town_streets": [
            {"pts": [[300, 500], [700, 500]], "w": 18},  # horizontal cross-street
            {"pts": [[450, 300], [450, 525]], "w": 18},
        ],
    }  # crosses at y500, stops at 525 (25px past)
    assert "city_streets_no_intersection_stub" in f(M)


def test_city_streets_no_intersection_stub_passes_when_streets_run_well_past():
    # the same crossing, but the vertical street continues well past (to 700) - a real grid line
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "town_streets": [{"pts": [[300, 500], [700, 500]], "w": 18}, {"pts": [[450, 300], [450, 700]], "w": 18}],
    }
    assert "city_streets_no_intersection_stub" not in f(M)


def test_population_consistent_with_housing_fires_when_dwellings_too_few():
    # population is dwellings x5, not total buildings x5; 10 dwellings imply ~50 residents, not 3000
    M = {"meta": {"scale": "town", "walled": False, "population": 3000}, "buildings": [bldg(120 + i * 60, 120, kind="laborer") for i in range(10)]}
    assert "population_consistent_with_housing" in f(M)


def test_businesses_front_streets_fires_when_shops_are_interior():
    M = {
        "meta": {"scale": "city", "walled": True},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "town_streets": [{"pts": [[250, 250], [750, 250]], "w": 18}],  # the only street, along the top
        "buildings": [bldg(300 + i * 50, 550, kind="shop") for i in range(6)],
    }  # shops marooned in the interior
    assert "businesses_front_streets" in f(M)


def test_poor_housing_mostly_interior_fires_when_laborers_on_the_street():
    M = {
        "meta": {"scale": "city", "walled": True},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "town_streets": [{"pts": [[250, 500], [750, 500]], "w": 18}],
        "buildings": [bldg(300 + i * 40, 512, kind="laborer") for i in range(8)],
    }  # all jammed ONTO the street
    assert "poor_housing_mostly_interior" in f(M)


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


def test_no_isolated_dwelling_cluster_fires_on_a_cut_off_block():
    # a 36-house block whose only street is far away - a giant cluster with no street OR alley near it
    blds = [bldg(380 + (i % 6) * 26, 380 + (i // 6) * 26, kind="laborer") for i in range(36)]
    M = {
        "meta": {"scale": "city", "walled": True},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "town_streets": [{"pts": [[210, 210], [790, 210]], "w": 18}],  # only street, along the top edge
        "buildings": blds,
    }
    assert "no_isolated_dwelling_cluster" in f(M)


def test_no_isolated_dwelling_cluster_passes_when_an_alley_reaches_it():
    blds = [bldg(380 + (i % 6) * 26, 380 + (i // 6) * 26, kind="laborer") for i in range(36)]
    M = {
        "meta": {"scale": "city", "walled": True},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "town_streets": [{"pts": [[210, 210], [790, 210]], "w": 18}],
        "alleys": [{"pts": [[380, 360], [380, 540]], "w": 10}, {"pts": [[510, 360], [510, 540]], "w": 10}],  # alleys lace the block
        "buildings": blds,
    }
    assert "no_isolated_dwelling_cluster" not in f(M)


def test_city_samurai_quarter_gated_fires_when_no_ward_gates():
    M = {
        "meta": {"scale": "city", "walled": True},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "governor_mansion": {"x": 600, "y": 600, "w": 120, "h": 90},
        "town_streets": [{"pts": [[400, 600], [800, 600]], "w": 18}],
        "kido": [],
    }  # the quarter has no ward gates
    assert "city_samurai_quarter_gated" in f(M)


def test_city_samurai_quarter_gated_passes_with_two_gates_on_streets():
    M = {
        "meta": {"scale": "city", "walled": True},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "governor_mansion": {"x": 600, "y": 600, "w": 120, "h": 90},
        "town_streets": [{"pts": [[400, 600], [800, 600]], "w": 18}, {"pts": [[600, 400], [600, 800]], "w": 18}],
        "kido": [{"x": 500, "y": 600, "horizontal": True}, {"x": 600, "y": 500, "horizontal": False}],
    }
    assert "city_samurai_quarter_gated" not in f(M)


def test_seg_intersect_parallel_returns_none():
    assert check_village.seg_intersect((0, 0), (10, 0), (0, 5), (10, 5)) is None


def test_city_samurai_ward_sealed_fires_on_ungated_crossing():
    # a street pierces the ward fence with no kido at the crossing - the gate can be walked around
    M = {
        "meta": {"scale": "city", "walled": True},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "governor_mansion": {"x": 600, "y": 600, "w": 120, "h": 90},
        "wards": [{"name": "samurai", "boundary": [[400, 800], [400, 400], [800, 400]]}],
        "town_streets": [{"pts": [[300, 500], [700, 500]], "w": 18}],  # crosses the W fence at (400,500)
        "kido": [],
    }
    assert "city_samurai_ward_sealed" in f(M)


def test_city_samurai_ward_sealed_fires_on_open_fence_end():
    # the fence has an end floating in the interior (not abutting the wall) - you walk around it
    M = {
        "meta": {"scale": "city", "walled": True},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "governor_mansion": {"x": 600, "y": 600, "w": 120, "h": 90},
        "wards": [{"name": "samurai", "boundary": [[400, 500], [400, 400], [800, 400]]}],  # (400,500) floats
        "town_streets": [],
        "kido": [],
    }
    assert "city_samurai_ward_sealed" in f(M)


def test_city_torii_over_streets_fires_when_torii_under_street():
    # a torii on the street but with a LOWER draw-z than the street -> the street paints over it
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "torii": [[500, 500, 50]],  # z = 50
        "town_streets": [{"pts": [[300, 500], [700, 500]], "w": 18, "z": 100}],
    }  # z = 100 > torii -> torii underneath
    assert "city_torii_over_streets" in f(M)


def test_city_temple_approach_has_torii_fires_when_street_runs_up_without_one():
    # a street terminates right at the temple front but there is no torii arch on it
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "religious": [{"kind": "temple", "label": "T", "x": 500, "y": 500, "w": 100, "h": 80}],
        "town_streets": [{"pts": [[500, 700], [500, 545]], "w": 18}],
    }  # runs up to the south edge (540)
    assert "city_temple_approach_has_torii" in f(M)


def _torii_fill_city(temple_xy, torii, streets=None, **extra):
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "religious": [{"kind": "temple", "label": "T", "x": temple_xy[0], "y": temple_xy[1], "w": 100, "h": 80}],
        "torii": [[t[0], t[1], 1] for t in torii],
    }
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
    M = _torii_fill_city((500, 300), [(500, 400)], streets=[[[500, 380], [500, 700]]], buildings=[{"kind": "laborer", "x": 500, "y": 446, "w": 40, "h": 30, "rot": 0}])
    assert "city_temple_torii_fill_approach" not in f(M)


def test_city_temple_torii_fill_approach_ignores_torii_off_any_street():
    # the torii isn't on a street, so there's no clear approach axis to extend - exempt
    M = _torii_fill_city((500, 300), [(500, 400)])
    assert "city_temple_torii_fill_approach" not in f(M)


def test_city_temple_torii_fill_approach_stops_at_the_map_edge():
    M = _torii_fill_city((500, 80), [(500, 40)], streets=[[[500, 60], [500, 10]]])  # next slot runs off the top edge
    assert "city_temple_torii_fill_approach" not in f(M)


def test_city_temple_torii_fill_approach_stops_at_the_wall():
    M = _torii_fill_city((500, 500), [(500, 760)], streets=[[[500, 500], [500, 860]]])  # next slot is outside the rampart
    assert "city_temple_torii_fill_approach" not in f(M)


def test_city_temple_torii_fill_approach_stops_at_a_field():
    fld = {"name": "f", "kind": "dry", "bbox": [470, 420, 530, 480], "outline": [[470, 420], [530, 420], [530, 480], [470, 480]]}
    M = _torii_fill_city((500, 300), [(500, 400)], streets=[[[500, 380], [500, 700]]], fields=[fld])
    assert "city_temple_torii_fill_approach" not in f(M)


def test_city_temples_clear_of_wall_branches():
    # three temples hitting the three footprint-vs-barrier paths: A contains a wall vertex
    # (point_in_poly), B is crossed by a wall edge (segments_cross), C's corner sits on it (seg_dist)
    rel = [
        {"kind": "temple", "label": "A", "x": 500, "y": 500, "w": 200, "h": 200},
        {"kind": "temple", "label": "B", "x": 300, "y": 500, "w": 16, "h": 300},
        {"kind": "temple", "label": "C", "x": 200, "y": 500, "w": 40, "h": 8},
    ]
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": [[100, 500], [500, 500], [900, 500]], "gates": [[500, 500], [500, 800]], "religious": rel}
    assert "city_temples_clear_of_wall_moat" in f(M)


def test_city_government_clear_of_wall_moat_fires():
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "governor_mansion": {"x": 800, "y": 500, "w": 120, "h": 90, "label": "Gov"},
    }  # straddles the right wall edge
    assert "city_government_clear_of_wall_moat" in f(M)


def test_city_streets_clear_of_wall_fires():
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "town_streets": [{"pts": [[500, 500], [990, 500]], "w": 18}],
    }  # a vertex outside the wall
    assert "city_streets_clear_of_wall" in f(M)


def test_city_streets_clear_of_moat_fires_on_alley():
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "moat": [[150, 150], [850, 150], [850, 850], [150, 850], [150, 150]],
        "town_streets": [],
        "alleys": [{"pts": [[500, 700], [500, 900]], "w": 10}],
    }  # alley crosses the moat ring
    assert "city_streets_clear_of_moat" in f(M)


def test_no_structure_on_street_fires_on_alley_over_building():
    M = {
        "meta": {"scale": "town", "walled": False},
        "wall": WALL,
        "alleys": [{"pts": [[400, 500], [600, 500]], "w": 10}],
        "buildings": [bldg(500, 500, kind="laborer")],
    }  # the alley runs straight over the dwelling
    assert "no_structure_on_street" in f(M)


def test_city_fields_clear_of_wall_moat_fires():
    ff = {"name": "ff", "kind": "paddy", "bbox": [700, 400, 900, 600], "outline": [[700, 400], [900, 400], [900, 600], [700, 600]]}  # straddles the right wall edge
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "fields": [ff]}
    assert "city_fields_clear_of_wall_moat" in f(M)


def test_city_governor_mansion_large_fires_when_small():
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "governor_mansion": {"x": 500, "y": 500, "w": 80, "h": 60, "label": "Gov"},  # tiny
        "manors": [{"x": 990, "y": 990, "w": 200, "h": 150}],
    }  # an estate grander than the governor
    assert "city_governor_mansion_large" in f(M)


def test_city_ministries_cluster_fires_on_stray_ministry():
    M = {
        "meta": {"scale": "city", "walled": True, "W": 2000, "H": 2000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "governor_mansion": {"x": 500, "y": 500, "w": 200, "h": 150, "label": "Gov"},
        "ministries": [{"x": 1800, "y": 1800, "w": 80, "h": 50, "name": "Ministry of War"}],
    }  # far from the yamen
    assert "city_ministries_cluster_at_government" in f(M)


def test_city_estates_toward_capital_fires_on_the_wrong_side():
    # renamed from city_estates_in_southeast: the direction is per-city (meta capital_dir),
    # defaulting to SE. A NW estate is on the wrong side of a default (SE-capital) city.
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "manors": [{"x": 60, "y": 60, "w": 100, "h": 80, "rot": 0}]}  # NW, not SE
    assert "city_estates_toward_capital" in f(M)


def test_view_treats_the_crop_as_the_map_edge():
    # the Imperial road must run off the map edge through both gates. With a cropped city view,
    # "the edge" is the view, not the full canvas - a road that exits the view (but not the
    # canvas) counts as running through.
    base = {
        "meta": {"scale": "city", "walled": True, "W": 3000, "H": 2000},
        "wall": [[1300, 300], [1700, 300], [1700, 1700], [1300, 1700]],
        "gates": [[1500, 300], [1500, 1700]],
        "road": [[1500, 250], [1500, 1750]],
    }  # exits y250..1750, well inside the 0..2000 canvas
    assert "city_imperial_road_through" in f(base)  # no view: road stops short of the canvas edge
    base["meta"]["view"] = [1250, 280, 500, 1440]  # crop to y280..1720
    assert "city_imperial_road_through" not in f(base)  # road now exits the view -> runs through


def test_city_pond_clear_of_wall_moat_fires():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "pond": [800, 500, 60, 40]}  # ellipse straddling the right wall edge
    assert "city_pond_clear_of_wall_moat" in f(M)


def test_city_civic_clear_of_streets_fires():
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "ministries": [{"x": 500, "y": 500, "w": 90, "h": 60, "name": "Ministry of War"}],
        "town_streets": [{"pts": [[300, 500], [700, 500]], "w": 20}],
    }  # the street runs through the ministry
    assert "city_civic_clear_of_streets" in f(M)


def test_city_temples_inside_walls_fires_on_outside_temple():
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "religious": [{"kind": "temple", "label": "T", "x": 990, "y": 500, "w": 60, "h": 40}],
    }
    assert "city_temples_inside_walls" in f(M)


def test_city_estates_overlap_and_barrier_fire():
    est = [{"x": 810, "y": 500, "w": 80, "h": 60}, {"x": 822, "y": 512, "w": 80, "h": 60}]  # overlap + on the wall edge
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "manors": est}
    fails = f(M)
    assert "city_estates_no_overlap" in fails
    assert "city_estates_clear_of_wall_moat" in fails


def test_city_outside_field_and_gate_market_fire():
    ff = {"name": "ff", "kind": "paddy", "bbox": [1500, 1500, 1800, 1800], "outline": [[1500, 1500], [1800, 1500], [1800, 1800], [1500, 1800]]}
    M = {"meta": {"scale": "city", "walled": True, "W": 2000, "H": 2000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "fields": [ff]}
    fails = f(M)
    assert "city_outside_fields_have_farmhouses" in fails
    assert "city_fields_close_to_city" in fails
    assert "city_has_gate_market" in fails


def test_city_gate_guardhouse_and_moat_irrigation_fire():
    bigf = {"name": "bf", "kind": "paddy", "bbox": [960, 200, 1180, 900], "outline": [[960, 200], [1180, 200], [1180, 900], [960, 900]]}
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1300, "H": 1100},
        "wall": [[100, 100], [900, 100], [900, 900], [100, 900]],
        "gates": [[500, 100], [500, 900]],
        "moat": [[80, 80], [920, 80], [920, 920], [80, 920], [80, 80]],
        "fields": [bigf],
    }
    fails = f(M)
    assert "city_gate_has_guardhouse" in fails  # no gate structures
    assert "city_moat_irrigates_fields" in fails  # big outside field, no channel feeds it


def test_city_no_inwall_farms_fires_without_agricultural_district():
    # a field whose centroid sits inside the wall, and no meta(agricultural_district=True)
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "fields": [_field("f", 400, 400, 600, 600)]}
    assert "city_no_inwall_farms" in f(M)


def test_city_no_inwall_farms_allowed_with_agricultural_district():
    M = {"meta": {"scale": "city", "walled": True, "agricultural_district": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "fields": [_field("f", 400, 400, 600, 600)]}
    assert "city_no_inwall_farms" not in f(M)


def test_city_moat_checks_fire_when_moat_neither_surrounds_nor_is_fed():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "moat": [[400, 400], [600, 400], [600, 600], [400, 600]]}
    fails = f(M)
    assert "city_moat_surrounds_wall" in fails  # a tiny moat INSIDE the wall does not encircle it
    assert "city_moat_fed_offmap" in fails  # no stream feeds it


_MOAT = [[160, 160], [840, 160], [840, 840], [160, 840], [160, 160]]  # encircles WALLSQ (200-800)


def _feeder_city(stream_w):
    return {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "moat": _MOAT,
        "moat_width": 22,
        "streams": [{"poly": [[80, 500], [165, 500]], "frm": None, "to": None, "w": stream_w}],
    }


def test_city_moat_feeder_matches_width_fires_when_narrow():
    # a 9px trickle reaching a 22px moat - too thin to keep it supplied
    assert "city_moat_feeder_matches_width" in f(_feeder_city(9))


def test_city_moat_feeder_matches_width_passes_when_matched():
    assert "city_moat_feeder_matches_width" not in f(_feeder_city(22))


# --- settlement wells (town/village/hamlet water access) ---
def _rural(scale, houses, wells, **extra):
    M = {"meta": {"scale": scale}, "houses": [{"x": x, "y": y, "w": 40, "h": 28, "rot": 0, "kind": "plain"} for (x, y) in houses], "wells": [{"x": x, "y": y, "r": 8} for (x, y) in wells]}
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


def test_remote_shrine_has_own_well_fires_when_a_set_apart_shrine_has_none():
    # the shrine sits far from the houses AND far from the one well -> it must keep its OWN well close by
    M = _rural("village", [(300, 300)], [(310, 305)], religious=[{"x": 1200, "y": 1200, "w": 30, "h": 24, "kind": "shrine"}])
    assert "remote_shrine_has_own_well" in f(M)


def test_remote_shrine_has_own_well_passes_with_a_well_close_by():
    M = _rural(
        "village",
        [(300, 300)],
        [(310, 305), (1210, 1205)],  # a second well right beside the remote shrine
        religious=[{"x": 1200, "y": 1200, "w": 30, "h": 24, "kind": "shrine"}],
    )
    assert "remote_shrine_has_own_well" not in f(M)


def test_remote_shrine_own_well_not_required_when_a_ditch_is_near():
    # a ditch/pond is NOT an ablution source - a set-apart shrine still needs its own WELL, so a nearby ditch does not save it
    M = _rural(
        "village",
        [(300, 300)],
        [(310, 305)],
        religious=[{"x": 1200, "y": 1200, "w": 30, "h": 24, "kind": "shrine"}],
        field_ditches=[{"poly": [[1180, 1180], [1220, 1220]], "w": 5, "role": "main", "field": "p"}],
    )
    assert "remote_shrine_has_own_well" in f(M)  # the ditch by the shrine does not count


def test_remote_shrine_among_the_houses_is_exempt():
    # a shrine near the dwellings shares the village wells - no own well required
    M = _rural("village", [(300, 300)], [(310, 305)], religious=[{"x": 360, "y": 340, "w": 30, "h": 24, "kind": "shrine"}])
    assert "remote_shrine_has_own_well" not in f(M)


def test_wells_among_dwellings_fires_on_a_stray_well():
    # a well far out in open country, no house beside it
    assert "wells_among_dwellings" in f(_rural("village", [(300, 300)], [(900, 900)]))


def test_wells_among_dwellings_passes_when_beside_a_house():
    assert "wells_among_dwellings" not in f(_rural("village", [(300, 300)], [(340, 300)]))


def _well_size_city(vr):
    # two 44px farmhouses with a well of drawn radius `vr` beside them
    return {
        "meta": {"scale": "village"},
        "houses": [{"x": 300, "y": 300, "w": 44, "h": 29, "rot": 0, "kind": "plain"}, {"x": 344, "y": 300, "w": 44, "h": 29, "rot": 0, "kind": "plain"}],
        "wells": [{"x": 322, "y": 300, "r": 8, "vr": vr}],
    }


def test_wells_sized_to_buildings_fires_when_too_small():
    # a 10px wellhead (the dense-city size) beside 44px village farmhouses - far too small
    assert "wells_sized_to_buildings" in f(_well_size_city(5.0))


def test_wells_sized_to_buildings_passes_when_proportional():
    # scaled to the village grain (~24px), about half a farmhouse
    assert "wells_sized_to_buildings" not in f(_well_size_city(11.9))


# --- bridges where a road crosses water ---
def _bridge_map(bridges):
    # a country road (E-W) crossing a stream (N-S) at (500, 500); `bridges` is the recorded list
    return {"meta": {"scale": "village", "W": 1000, "H": 1000}, "road": [[100, 500], [900, 500]], "streams": [{"poly": [[500, 100], [500, 900]], "frm": None, "to": None, "w": 9}], "bridges": bridges}


def test_roads_bridge_water_fires_when_unbridged():
    # the road runs straight through the stream with no bridge
    assert "roads_bridge_water" in f(_bridge_map([]))


def test_roads_bridge_water_passes_when_bridged():
    assert "roads_bridge_water" not in f(_bridge_map([{"x": 500, "y": 500, "rot": 0, "span": 37, "w": 26}]))


def test_seg_intersect_returns_point_for_a_crossing_and_none_for_parallel():
    # the geometry helper that bridges() uses to find the crossing point
    p = settlement.seg_intersect((0, 0), (10, 0), (5, -5), (5, 5))
    assert p == (5.0, 0.0)
    assert settlement.seg_intersect((0, 0), (10, 0), (0, 4), (10, 4)) is None  # parallel - no crossing
    assert settlement.segments_cross((0, 0), (10, 0), (5, -5), (5, 5))
    assert not settlement.segments_cross((0, 0), (10, 0), (0, 4), (10, 4))


def test_roads_bridge_water_passes_when_road_runs_alongside_water():
    # a road parallel to a stream, never intersecting it, needs no bridge
    M = {"meta": {"scale": "village", "W": 1000, "H": 1000}, "road": [[100, 480], [900, 480]], "streams": [{"poly": [[100, 520], [900, 520]], "frm": None, "to": None, "w": 9}], "bridges": []}
    assert "roads_bridge_water" not in f(M)


def test_roads_bridge_water_fires_on_an_unbridged_lane_over_a_canal():
    # a village LANE crossing an irrigation ditch must be bridged too (not only roads/streets)
    M = {
        "meta": {"scale": "village", "W": 1000, "H": 1000},
        "lanes": [{"pts": [[100, 500], [900, 500]], "w": 6}],
        "field_ditches": [{"poly": [[500, 100], [500, 900]], "w": 5, "role": "main", "field": "p"}],
        "bridges": [],
    }
    assert "roads_bridge_water" in f(M)
    M["bridges"] = [{"x": 500, "y": 500, "rot": 0, "span": 32, "w": 6}]
    assert "roads_bridge_water" not in f(M)


def _footbridge_map(bridges, footbridges=True):
    return {
        "meta": {"scale": "village", **({"field_footbridges": True} if footbridges else {})},
        "field_ditches": [
            {"poly": [[100, 200], [800, 200]], "w": 5, "role": "main", "field": "p"},
            {"poly": [[100, 600], [180, 600]], "w": 4, "role": "branch", "field": "p"},
        ],  # short stub -> below min, skipped
        "bridges": bridges,
    }


def test_long_ditches_have_a_footbridge_fires_when_a_long_ditch_is_planless():
    assert "long_ditches_have_a_footbridge" in f(_footbridge_map([]))
    assert "long_ditches_have_a_footbridge" not in f(_footbridge_map([{"x": 450, "y": 200, "rot": 90, "span": 20, "w": 5}]))


def test_long_ditches_footbridge_check_is_opt_in():
    # without meta.field_footbridges the check does not run at all (a planless ditch is fine)
    assert "long_ditches_have_a_footbridge" not in f(_footbridge_map([], footbridges=False))


def test_bridges_clear_of_houses_fires_when_a_plank_sits_on_a_farmhouse():
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(400, 300)], "bridges": [{"x": 400, "y": 300, "rot": 0, "span": 24, "w": 6}]}  # a plank ON the house
    assert "bridges_clear_of_houses" in f(M)


def test_bridges_clear_of_houses_passes_when_a_plank_is_off_the_houses():
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(400, 300)], "bridges": [{"x": 600, "y": 300, "rot": 0, "span": 24, "w": 6}]}  # a plank well clear of the house
    assert "bridges_clear_of_houses" not in f(M)


# --- harvest processing (per-farmstead threshing/drying yards) ---
_PADDY_SQ = [[400, 400], [600, 400], [600, 600], [400, 600]]


def _harvest(houses, yards, fields=None):
    M = {
        "meta": {"scale": "village"},
        "houses": [{"x": x, "y": y, "w": 40, "h": 28, "rot": 0, "kind": "plain"} for (x, y) in houses],
        "wells": [{"x": x, "y": y, "r": 8, "vr": 11.9} for (x, y) in houses],  # a well by each house so the water checks pass
        "threshing_yards": yards,
    }
    if fields:
        M["fields"] = fields
    return M


def _yard(of, dx=44, dy=0, w=32, h=20):
    # a small yard beside the farmhouse at `of`, recording its parent farmhouse center
    return {"x": of[0] + dx, "y": of[1] + dy, "w": w, "h": h, "rot": 0, "of": [of[0], of[1]]}


_SIX = [(300, 300), (380, 300), (460, 300), (540, 300), (620, 300), (700, 300)]  # the work yard is UNIVERSAL: need all 6


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
    # +y is south; a yard ABOVE its house center sits on the shady north/back side
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
    M["buildings"] = [{"x": 700, "y": 700, "w": 44, "h": 30, "rot": 0, "kind": "shop"}]  # far away
    assert "harvest_yards_clear_of_structures" not in f(M)


# --- waterways merge at crossings (confluence layering) ---
def _confluence(ch_bedz):
    # a stream (bed+sheen) crossed by a channel; ch_bedz is the channel's bed draw position
    return {
        "meta": {"scale": "village"},
        "streams": [{"poly": [[100, 500], [900, 500]], "frm": None, "to": None, "w": 9, "bedz": 10, "sheenz": 20}],
        "channels": [{"poly": [[500, 100], [500, 900]], "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}, "bedz": ch_bedz}],
    }


def test_waterways_merge_at_crossings_fires_when_bed_over_sheen():
    # the channel bed is drawn AFTER the stream sheen (the old per-course order) - an opaque bed cuts it
    assert "waterways_merge_at_crossings" in f(_confluence(25))


def test_waterways_merge_at_crossings_passes_when_beds_below_sheens():
    assert "waterways_merge_at_crossings" not in f(_confluence(11))


def test_waterways_merge_at_crossings_passes_when_no_crossing():
    M = _confluence(25)
    M["channels"][0]["poly"] = [[500, 100], [500, 300]]  # stops short, never reaches the stream
    assert "waterways_merge_at_crossings" not in f(M)


def test_waterways_merge_at_crossings_passes_when_neither_has_sheen():
    # two channels crossing - same-color beds merge regardless of order, no sheen to cut
    M = {
        "meta": {"scale": "village"},
        "channels": [
            {"poly": [[100, 500], [900, 500]], "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}, "bedz": 30},
            {"poly": [[500, 100], [500, 900]], "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}, "bedz": 10},
        ],
    }
    assert "waterways_merge_at_crossings" not in f(M)


def test_waterways_merge_at_crossings_fires_at_a_feeder_junction():
    # a channel FEEDS INTO a stream (its endpoint sits on it), drawn over the stream's sheen
    M = {
        "meta": {"scale": "village"},
        "streams": [{"poly": [[100, 500], [900, 500]], "frm": None, "to": None, "w": 9, "bedz": 10, "sheenz": 20}],
        "channels": [{"poly": [[500, 505], [500, 900]], "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}, "bedz": 25}],
    }
    assert "waterways_merge_at_crossings" in f(M)


def test_waterways_merge_at_crossings_fires_when_stream_ends_on_a_channel():
    # the stream's own endpoint sits on a channel (the pa-endpoint junction branch)
    M = {
        "meta": {"scale": "village"},
        "streams": [{"poly": [[505, 500], [900, 500]], "frm": None, "to": None, "w": 9, "bedz": 25, "sheenz": 30}],
        "channels": [{"poly": [[500, 100], [500, 900]], "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}, "bedz": 10, "sheenz": 5}],
    }
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


def test_cemetery_clear_of_shrine_fires_when_on_the_hall():
    # graves fill the shrine's YARD but never sit ON the sacred hall itself (this grave overlaps it)
    assert "cemetery_clear_of_shrine" in f(_dead("village", [{"x": 540, "y": 520, "w": 80, "h": 56, "rot": 0}], religious=_SHR))


def test_cemetery_clear_of_shrine_passes_when_off_the_hall():
    assert "cemetery_clear_of_shrine" not in f(_dead("village", [{"x": 900, "y": 900, "w": 80, "h": 56, "rot": 0}], religious=_SHR))


def test_cemetery_clear_of_shrine_allows_a_grave_in_the_precinct():
    # NEW (L7R): the shrine is Shinseist and its monk tends the dead, so a grave NEAR the shrine (in the yard,
    # off the hall) is FINE - the old kegare-distance rule is gone; only the sacred hall + torii stay clear
    M = {
        "meta": {"scale": "village"},
        "cemeteries": [{"x": 615, "y": 500, "w": 80, "h": 56, "rot": 0}],
        "religious": _SHR,
    }  # 115px from the shrine center (old rule would fire) but clear of the hall's east edge
    assert "cemetery_clear_of_shrine" not in f(M)


def test_cemetery_clear_of_shrine_fires_on_a_grave_under_the_torii():
    # the sacred GATEWAY stays clear too - a grave on the torii arch fires (hall placed far off, so it is the torii)
    M = {
        "meta": {"scale": "village"},
        "cemeteries": [{"x": 500, "y": 504, "w": 60, "h": 40, "rot": 0}],
        "religious": [{"kind": "shrine", "x": 500, "y": 760, "w": 30, "h": 24}],
        "torii": [[500, 500, 1]],
    }
    assert "cemetery_clear_of_shrine" in f(M)


def test_village_graveyard_by_shrine_fires_when_set_apart():
    # L7R: the village shrine's monk performs the funerary rites, so the graveyard sits in its precinct
    assert "village_graveyard_by_shrine" in f(_dead("village", [{"x": 1200, "y": 1200, "w": 80, "h": 56, "rot": 0}], religious=_SHR))


def test_village_graveyard_by_shrine_passes_when_in_precinct():
    assert "village_graveyard_by_shrine" not in f(_dead("village", [{"x": 640, "y": 500, "w": 80, "h": 56, "rot": 0}], religious=_SHR))


def test_village_graveyard_by_shrine_exempts_a_hilltop_shrine():
    # a hilltop shrine is exempt (graves do not climb the sacred hill); with no flat shrine the ground is by-eye
    M = _dead("village", [{"x": 1200, "y": 1200, "w": 80, "h": 56, "rot": 0}], religious=[{"kind": "shrine", "x": 500, "y": 500, "w": 100, "h": 68}])
    M["hill"] = [500, 500, 200, 150]
    assert "village_graveyard_by_shrine" not in f(M)


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


def test_cemetery_clear_of_shrine_fires_on_a_mausoleum_on_the_hall():
    # the off-the-hall rule covers MAUSOLEA too, not just graveyards (this one overlaps the shrine hall)
    M = {"meta": {"scale": "village"}, "mausoleums": [{"x": 540, "y": 520, "w": 74, "h": 58, "rot": 0}], "religious": [{"kind": "shrine", "x": 500, "y": 500, "w": 100, "h": 68}]}
    assert "cemetery_clear_of_shrine" in f(M)


# --- the full city funerary geography ---
def _city_dead(**kw):
    WALLSQ = [[200, 200], [800, 200], [800, 800], [200, 800]]  # inside = 200..800
    d = dict(
        cems=[(300, 300), (700, 300), (100, 100)],  # 2 inside + 1 outside
        temples=[(320, 320, "A", True), (680, 320, "B", True)],
        maus=[(520, 520)],
        crem=[(100, 900)],
        oss=[(140, 900)],
        gov=(500, 500),
        shrines=[],
    )
    d.update(kw)

    def _cem(c):
        x, y = c[0], c[1]
        if len(c) >= 4:
            w, h = c[2], c[3]
        else:  # outside cemeteries default bigger than inside
            outside = not (200 < x < 800 and 200 < y < 800)
            w, h = (104, 74) if outside else (70, 50)
        parish = c[4] if len(c) >= 5 else True
        return {"x": x, "y": y, "w": w, "h": h, "rot": 0, "parish": parish}

    return {
        "meta": {"scale": "city"},
        "wall": WALLSQ,
        "cemeteries": [_cem(c) for c in d["cems"]],
        "mausoleums": [{"x": x, "y": y, "w": 74, "h": 58, "rot": 0} for (x, y) in d["maus"]],
        "cremation_grounds": [{"x": x, "y": y, "w": 116, "h": 80, "rot": 0} for (x, y) in d["crem"]],
        "ossuaries": [{"x": x, "y": y, "w": 92, "h": 60, "rot": 0} for (x, y) in d["oss"]],
        "religious": [{"kind": "temple", "x": tx, "y": ty, "w": 80, "h": 60, "label": lbl, "graveyard": gv} for (tx, ty, lbl, gv) in d["temples"]]
        + [{"kind": "small_shrine", "x": sx, "y": sy, "w": 30, "h": 24} for (sx, sy) in d["shrines"]],
        "governor_mansion": {"x": d["gov"][0], "y": d["gov"][1], "w": 120, "h": 90} if d["gov"] else None,
    }


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
    assert "funerary_set_back_from_water" not in f(_water_grave({"streams": [{"poly": [[300, 600], [600, 600]], "frm": None, "to": None, "w": 9}], "pond": [900, 900, 60, 40]}))


def test_water_setback_scales_with_waterway_width():
    assert check_village.water_setback(4) == 75  # any small open water -> the floor (graves flood out)
    assert check_village.water_setback(9) == 75  # a narrow stream still gets the full floor
    assert check_village.water_setback(22) == 110  # moat -> moderate/large
    assert check_village.water_setback(40) == 140  # river / canal -> capped
    assert check_village.water_setback(9) < check_village.water_setback(22)  # wider water, more set-back


def test_funerary_set_back_scales_grave_ok_by_a_stream_fails_by_a_moat():
    # a graveyard whose nearest corner is 90px from the watercourse: fine by a narrow stream (floor 75),
    # too close to a moat (set-back 110)
    def M(width):
        return {
            "meta": {"scale": "village"},
            "cemeteries": [{"x": 300, "y": 270, "w": 50, "h": 36, "rot": 0, "parish": True}],
            "streams": [{"poly": [[200, 378], [600, 378]], "frm": None, "to": None, "w": width}],
        }

    assert "funerary_set_back_from_water" not in f(M(6))  # narrow stream: floor 75, corner 90px away -> ok
    assert "funerary_set_back_from_water" in f(M(22))  # moat-width: set-back 110 -> 90px too close


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
    M = {"meta": {"scale": "city"}, "wall": WALLSQ, "moat": _MOAT, "moat_width": 22, "cemeteries": [{"x": 230, "y": 500, "w": 50, "h": 36, "rot": 0, "parish": True}]}
    assert "funerary_set_back_from_water" not in f(M)


def test_funerary_set_back_outside_wall_grave_subject_to_moat():
    WALLSQ = [[200, 200], [800, 200], [800, 800], [200, 800]]
    M = {"meta": {"scale": "city"}, "wall": WALLSQ, "moat": _MOAT, "moat_width": 22, "cemeteries": [{"x": 120, "y": 500, "w": 50, "h": 36, "rot": 0, "parish": True}]}
    assert "funerary_set_back_from_water" in f(M)


_PADDY = {"name": "a", "kind": "paddy", "bbox": [300, 330, 500, 500], "outline": [[300, 330], [500, 330], [500, 500], [300, 500]]}


def test_funerary_set_back_fires_near_a_rice_paddy():
    # a burial ground hard against a flood-prone paddy edge
    M = {"meta": {"scale": "village"}, "fields": [_PADDY], "cemeteries": [{"x": 300, "y": 300, "w": 50, "h": 36, "rot": 0, "parish": True}]}
    assert "funerary_set_back_from_water" in f(M)


def test_funerary_set_back_paddy_needs_more_than_creek_distance():
    # ~35px from a paddy edge: fine for a creek, but a flooded paddy needs a real margin -> still fires
    near = {"meta": {"scale": "village"}, "fields": [_PADDY], "cemeteries": [{"x": 300, "y": 277, "w": 50, "h": 36, "rot": 0, "parish": True}]}  # corner ~35px from the paddy
    assert "funerary_set_back_from_water" in f(near)
    far = {"meta": {"scale": "village"}, "fields": [_PADDY], "cemeteries": [{"x": 300, "y": 255, "w": 50, "h": 36, "rot": 0, "parish": True}]}  # corner ~57px -> clear
    assert "funerary_set_back_from_water" not in f(far)


def test_funerary_set_back_cremation_may_sit_by_a_paddy():
    # the cremation ground is exempt from the paddy set-back (a fire site, not flood-sensitive graves)
    M = {"meta": {"scale": "village"}, "fields": [_PADDY], "cremation_grounds": [{"x": 300, "y": 280, "w": 116, "h": 80, "rot": 0}]}
    assert "funerary_set_back_from_water" not in f(M)


def _city_estates(gate_dirs):
    WALLSQ = [[200, 200], [800, 200], [800, 800], [200, 800]]  # estates sit OUTSIDE, to the SE
    return {
        "meta": {"scale": "city", "walled": True},
        "wall": WALLSQ,
        "manors": [{"x": 900 + (i % 3) * 220, "y": 900 + (i // 3) * 220, "w": 120, "h": 90, "gate_dir": gd} for i, gd in enumerate(gate_dirs)],
    }


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
    M["road"] = [[100, 500], [900, 500]]  # the inn (y560) fronts the road (y500), nothing between
    assert "town_has_caravan_inn" not in f(M)


def test_town_has_caravan_inn_fires_when_inn_behind_shops():
    M = _town_caravan(inn_xy=(500, 560), st_xy=(500, 640))
    M["road"] = [[100, 500], [900, 500]]
    M["buildings"].append({"x": 500, "y": 525, "w": 60, "h": 30, "kind": "merchant", "rot": 0})  # a shop between inn and road
    assert "town_has_caravan_inn" in f(M)


def test_town_has_caravan_inn_fires_when_inn_far_from_any_road():
    M = _town_caravan(inn_xy=(500, 560), st_xy=(500, 640))
    M["road"] = [[100, 200], [900, 200]]  # the road is far away - the inn is not along it
    assert "town_has_caravan_inn" in f(M)


def test_inn_faces_the_road_fires_when_back_to_the_road():
    # inn at rot 0 (noren faces south) but the road is to its NORTH -> back to the road
    M = _town_caravan(inn_xy=(500, 560), st_xy=(500, 640))
    M["road"] = [[100, 500], [900, 500]]
    assert "inn_faces_the_road" in f(M)


def test_inn_faces_the_road_passes_when_facing():
    M = _town_caravan(inn_xy=(500, 560), st_xy=(500, 640))
    M["road"] = [[100, 500], [900, 500]]
    M["buildings"][0]["rot"] = 180  # the inn (buildings[0]) turns its noren north, toward the road
    assert "inn_faces_the_road" not in f(M)


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
        b.append(bldg(150, 100 + i * 60, "shop"))  # businesses at droad ~50
    for i in range(3):
        b.append(bldg(res_x, 150 + i * 80, "merchant_large", w=86, h=60))  # merchant residences
    for i in range(6):
        b.append(bldg(lab_x, 120 + i * 50, "laborer"))  # laborer warren
    return {"meta": {"scale": "town"}, "houses": [], "fields": [], "road": [[100, 0], [100, 1000]], "road_width": 26, "buildings": b}


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
            b.append(bldg(140, 100 + i * 60, "shop", rot=0))  # storefronts at droad 40
    b.append(bldg(home_x, home_y, "merchant_large", rot=home_rot, w=86, h=60))
    return {"meta": {"scale": "town"}, "houses": [], "fields": [], "road": [[100, 0], [100, 1000]], "road_width": 26, "buildings": b}


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
    return {
        "meta": {"scale": "city", "walled": True},
        "wall": [[100, 100], [3000, 100], [3000, 2500], [100, 2500]],
        "wards": [{"name": "samurai", "boundary": [[1620, 1535], [2401, 1535]], "z": 5}],
        "mausoleums": [{"x": 2246, "y": maus_cy, "w": 54, "h": 40, "rot": 0, "gate_dir": "west", "ward_walls": ward_walls}],
    }


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


def _town_manor(gate_dir, rot=0, road=None):
    # a magistrate manor at (300,300); the "town" (houses) is to the SE at ~(950,933)
    M = {
        "meta": {"scale": "town"},
        "houses": [{"x": x, "y": y, "w": 40, "h": 28, "rot": 0, "kind": "plain"} for x, y in [(900, 900), (1000, 900), (950, 1000)]],
        "manors": [{"x": 300, "y": 300, "w": 120, "h": 90, "rot": rot, "gate_dir": gate_dir, "gate": [300, 300]}],
    }
    if road:
        M["road"] = road
    return M


def test_manor_gate_faces_town_passes_facing_the_town():
    assert "manor_gate_faces_town" not in f(_town_manor("south"))  # town is SE -> south gate faces it


def test_manor_gate_faces_town_fires_facing_away():
    assert "manor_gate_faces_town" in f(_town_manor("north"))  # north gate faces away from the SE town


def test_manor_gate_faces_town_passes_facing_the_road():
    # town centroid is SE, but a north gate faces an Imperial road to the manor's north -> ok
    assert "manor_gate_faces_town" not in f(_town_manor("north", road=[[100, 150], [600, 150]]))


def test_manor_rotation_records_rot_and_tilts_the_footprint():
    s = settlement.Settlement()
    s.manor(500, 500, 200, 120, "M", gate_dir="south", rot=30)
    mn = s.M["manors"][0]
    assert mn["rot"] == 30
    c = check_village.rect_corners(mn)
    assert abs(c[0][1] - c[1][1]) > 1  # the top edge is no longer horizontal -> the compound is tilted


def _crem_cem(crem_xy, cem_xy, walled=False):
    M = {
        "meta": {"scale": "town"},
        "cremation_grounds": [{"x": crem_xy[0], "y": crem_xy[1], "w": 116, "h": 80, "rot": 0}],
        "cemeteries": [{"x": cem_xy[0], "y": cem_xy[1], "w": 100, "h": 72, "rot": 0, "parish": True}],
    }
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
    return {
        "meta": {"scale": "town"},
        "road": [[100, 200], [900, 200]],
        "cremation_grounds": [{"x": crem_xy[0], "y": crem_xy[1], "w": 116, "h": 80, "rot": 0}],
        "cemeteries": [{"x": cem_xy[0], "y": cem_xy[1], "w": 100, "h": 72, "rot": 0, "parish": True}],
    }


def test_cremation_set_back_from_road_fires_when_on_the_road():
    assert "cremation_ground_set_back_from_main_road" in f(_crem_road((300, 260), (300, 360)))  # 60px off the road


def test_cremation_set_back_from_road_passes_when_far():
    assert "cremation_ground_set_back_from_main_road" not in f(_crem_road((300, 500), (300, 600)))


def test_cremation_set_back_from_road_passes_when_no_main_road():
    M = _crem_road((300, 260), (300, 360))
    del M["road"]  # a settlement on minor streets only - nothing to be set back from
    assert "cremation_ground_set_back_from_main_road" not in f(M)


def _crem_temple(crem_xy, mon_xy=(300, 500)):
    # a monastery + a cremation ground (with an adjacent cemetery), beside a main road along y=200.
    # The monastery at y=500 sits 300px back from the road; "behind" it means >= 260px back.
    return {
        "meta": {"scale": "town"},
        "road": [[100, 200], [900, 200]],
        "religious": [{"x": mon_xy[0], "y": mon_xy[1], "w": 132, "h": 86, "rot": 0, "kind": "monastery"}],
        "cremation_grounds": [{"x": crem_xy[0], "y": crem_xy[1], "w": 116, "h": 80, "rot": 0}],
        "cemeteries": [{"x": crem_xy[0], "y": crem_xy[1] + 110, "w": 100, "h": 72, "rot": 0, "parish": True}],
    }


def test_cremation_not_between_temple_and_road_fires_when_between():
    # cremation on the road side of its monastery (closer to the road than the temple), yet still
    # clear of the road's own set-back floor - only the between-temple-and-road rule should object
    fails = f(_crem_temple((300, 360)))
    assert "cremation_ground_not_between_temple_and_road" in fails
    assert "cremation_ground_set_back_from_main_road" not in fails  # isolates the new rule


def test_cremation_not_between_temple_and_road_passes_when_behind():
    assert "cremation_ground_not_between_temple_and_road" not in f(_crem_temple((300, 640)))


def test_cremation_not_between_temple_and_road_passes_when_no_temple_nearby():
    # no temple within association range -> nothing to be "in front of"
    assert "cremation_ground_not_between_temple_and_road" not in f(_crem_temple((300, 360), mon_xy=(300, 1500)))


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
    return {
        "meta": {"scale": "town"},
        "houses": [{"x": x, "y": y, "w": 40, "h": 28, "rot": 0, "kind": "plain"} for (x, y) in dwell],
        "cemeteries": [{"x": 300, "y": 360, "w": 70, "h": 50, "rot": 0}],
        "religious": [{"kind": "monastery", "x": 300, "y": 300, "w": 80, "h": 60, "label": "M", "graveyard": True}],
        "cremation_grounds": [{"x": x, "y": y, "w": 116, "h": 80, "rot": 0} for (x, y) in crem],
    }


def test_town_has_cremation_ground_fires_when_missing():
    assert "town_has_cremation_ground" in f(_town_dead([]))


def test_town_has_cremation_ground_fires_when_among_dwellings():
    assert "town_has_cremation_ground" in f(_town_dead([(320, 300)]))


def test_town_has_cremation_ground_passes_when_at_the_edge():
    assert "town_has_cremation_ground" not in f(_town_dead([(900, 900)]))


# ---- fire-watch towers (hinomi-yagura) & fire-break plazas (hiyokechi/hirokoji) ----


def _tower(x, y):
    return {"x": x, "y": y, "w": 26, "h": 26, "rot": 0}


def test_town_has_fire_tower_fires_when_absent():
    # EVERY town now (GM audit 2026-07 widened this from walled-only): unwalled county seats too
    assert "town_has_fire_tower" in f({"meta": {"scale": "town", "walled": True}})
    assert "town_has_fire_tower" in f({"meta": {"scale": "town", "walled": False}})


def test_town_has_fire_tower_passes_with_one():
    assert "town_has_fire_tower" not in f({"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(500, 500)]})


def test_town_has_fire_tower_opt_out():
    assert "town_has_fire_tower" not in f({"meta": {"scale": "town", "walled": True, "fire_tower": False}})


def test_unwalled_town_needs_no_fire_tower():
    # an OPEN road-town relies on its road and field gaps; the presence check is walled-only
    fails = f({"meta": {"scale": "town", "walled": False}})
    assert "walled_town_has_fire_tower" not in fails


def test_city_has_fire_towers_fires_with_one():
    assert "city_has_fire_towers" in f({"meta": {"scale": "city"}, "fire_towers": [_tower(500, 500)]})


def test_city_has_fire_towers_passes_with_two():
    assert "city_has_fire_towers" not in f({"meta": {"scale": "city"}, "fire_towers": [_tower(500, 500), _tower(700, 700)]})


def test_city_has_fire_towers_opt_out():
    assert "city_has_fire_towers" not in f({"meta": {"scale": "city", "fire_tower": False}})


def test_fire_tower_in_commoner_quarter_fires_in_samurai_quarter():
    # a tower whose nearest neighbors are all samurai sits in the samurai quarter, not the warren
    M = {"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(500, 500)], "buildings": [bldg(520, 510, "samurai"), bldg(480, 515, "samurai"), bldg(510, 480, "samurai_large")]}
    assert "fire_tower_in_commoner_quarter" in f(M)


def test_fire_tower_in_commoner_quarter_fires_when_isolated():
    M = {"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(500, 500)], "buildings": [bldg(900, 900, "laborer")]}  # nearest dwelling > 230px away
    assert "fire_tower_in_commoner_quarter" in f(M)


def test_fire_tower_in_commoner_quarter_passes_among_commoners():
    M = {"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(500, 500)], "buildings": [bldg(520, 510, "laborer"), bldg(480, 515, "servant"), bldg(510, 480, "merchant")]}
    assert "fire_tower_in_commoner_quarter" not in f(M)


def test_fire_tower_on_wall_overlaps_like_any_structure():
    # fire_towers are in _OVERLAP_STRUCTS, so a tower on the wall trips no_structure_on_wall
    M = {"meta": {"scale": "town", "walled": True}, "wall": [[100, 500], [900, 500]], "gate": [500, 500], "fire_towers": [_tower(500, 500)]}
    assert "no_structure_on_wall" in f(M)


def test_fire_towers_dispersed_fires_when_bunched():
    # two towers 100 px apart (< one 230 px watch radius) watch the same rooftops twice
    M = {"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(500, 500), _tower(600, 500)]}
    assert "fire_towers_dispersed" in f(M)


def test_fire_towers_dispersed_passes_when_spread():
    M = {"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(400, 500), _tower(900, 500)]}
    assert "fire_towers_dispersed" not in f(M)


def test_fire_towers_dispersed_ignores_a_single_tower():
    M = {"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(500, 500)]}
    assert "fire_towers_dispersed" not in f(M)


def _block(cx, cy, kind="laborer", n=4, step=30):
    return [bldg(cx + i * step, cy + j * step, kind) for i in range(n) for j in range(n)]


def test_fire_tower_amid_its_district_fires_when_towers_share_a_quarter():
    # both towers by the west block (though > one watch radius apart, so dispersal passes): the
    # second tower inherits the whole east block as its "district" and stands far off its centroid
    M = {"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(470, 545), _tower(775, 545)], "buildings": _block(400, 500) + _block(1400, 500)}
    fails = f(M)
    assert "fire_tower_amid_its_district" in fails
    assert "fire_towers_dispersed" not in fails  # 305px apart - the old check alone misses this


def test_fire_tower_amid_its_district_passes_with_one_tower_per_quarter():
    M = {"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(445, 545), _tower(1445, 545)], "buildings": _block(400, 500) + _block(1400, 500)}
    assert "fire_tower_amid_its_district" not in f(M)


def test_fire_tower_amid_its_district_ignores_extramural_rows():
    # with a wall drawn, the gate-market rows OUTSIDE it are not part of any tower's district -
    # counting them would drag the east tower's centroid out and false-fire
    M = {
        "meta": {"scale": "town", "walled": True},
        "wall": [[100, 100], [1900, 100], [1900, 1000], [100, 1000]],
        "fire_towers": [_tower(445, 545), _tower(1445, 545)],
        "buildings": _block(400, 500) + _block(1400, 500) + _block(1400, 1200),
    }
    assert "fire_tower_amid_its_district" not in f(M)


def test_fire_tower_standoff_fires_when_flush_with_a_building():
    # tower half-width 13 + shop half-width 20 -> centers 536 apart leave a 3px gap: too tight
    # (the far building exercises the distance prefilter)
    M = {"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(500, 500)], "buildings": [bldg(536, 500, "laborer", w=40, h=28), bldg(900, 900, "laborer")]}
    fails = f(M)
    assert "fire_tower_standoff" in fails
    assert "no_structure_overlaps" not in fails  # a 3px gap is NOT an overlap - only the new check sees it


def test_fire_tower_standoff_fires_on_true_overlap_too():
    M = {"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(500, 500)], "buildings": [bldg(510, 500, "laborer", w=40, h=28)]}
    assert "fire_tower_standoff" in f(M)


def test_fire_tower_standoff_passes_with_daylight():
    # 6px gap (centers 539 apart) clears the 5px rule
    M = {"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(500, 500)], "buildings": [bldg(539, 500, "laborer", w=40, h=28)]}
    assert "fire_tower_standoff" not in f(M)


def test_fire_tower_amid_its_district_skips_a_district_less_tower():
    # two coincident towers: all dwellings assign to the first, the second has no district to be
    # off-center of (dispersal is what catches the stacking)
    M = {"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(500, 500), _tower(500, 500)], "buildings": _block(455, 455)}
    fails = f(M)
    assert "fire_tower_amid_its_district" not in fails
    assert "fire_towers_dispersed" in fails


def test_fire_tower_clear_of_fields_fires_on_a_field():
    # a hinomi-yagura standing ON cultivated ground (e.g. an in-wall agricultural district) is nonsense
    M = {"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(250, 250)], "fields": [_field("paddy", 100, 100, 400, 400)]}
    assert "fire_tower_clear_of_fields" in f(M)


def test_fire_tower_clear_of_fields_fires_on_flower_field():
    M = {"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(250, 250)], "flower_fields": [{"outline": [[100, 100], [400, 100], [400, 400], [100, 400]]}]}
    assert "fire_tower_clear_of_fields" in f(M)


def test_fire_tower_clear_of_fields_passes_when_clear():
    M = {"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(800, 800)], "fields": [_field("paddy", 100, 100, 400, 400)]}
    assert "fire_tower_clear_of_fields" not in f(M)


def test_fire_tower_clear_of_wells_fires_on_a_wellhead():
    # wells are overlap-EXEMPT, so only the dedicated check catches a tower footing on the well court
    M = {"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(500, 500)], "wells": [{"x": 505, "y": 500, "r": 8}]}
    fails = f(M)
    assert "fire_tower_clear_of_wells" in fails
    assert "no_structure_overlaps" not in fails  # the exemption means the blanket pass misses this


def test_fire_tower_clear_of_wells_fires_within_the_standoff():
    # tower half-width 13 + well r 8 + 5px daylight rule -> a well center 25px away is still too close
    M = {"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(500, 500)], "wells": [{"x": 525, "y": 500, "r": 8}]}
    assert "fire_tower_clear_of_wells" in f(M)


def test_fire_tower_clear_of_wells_passes_with_daylight():
    # 26px of clearance (center 500 -> well 539: 13 + 8 + 18) is comfortably clear of the 5px rule
    M = {"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(500, 500)], "wells": [{"x": 539, "y": 500, "r": 8}]}
    assert "fire_tower_clear_of_wells" not in f(M)


# ---- grove_clumps_clear_of_structures: a tree blob may abut but not overlap a farmstead ----
def test_grove_clumps_clear_of_structures_fires_on_a_clump_over_a_house():
    on = {
        "meta": {"scale": "village"},
        "houses": [{"x": 500, "y": 500, "w": 40, "h": 30, "rot": 0, "kind": "plain"}],
        "village_groves": [{"role": "copse", "r": 11, "clumps": [[515, 505]]}],
    }  # blob center inside the house
    assert "grove_clumps_clear_of_structures" in f(on)
    beside = {**on, "village_groves": [{"role": "copse", "r": 11, "clumps": [[560, 505]]}]}  # abuts, off the wall
    assert "grove_clumps_clear_of_structures" not in f(beside)


def test_grove_clumps_clear_of_structures_covers_a_garden_and_a_shed():
    # the check sweeps the whole homestead, not just houses - a clump on a garden or a farm shed also fires
    gd = {"meta": {"scale": "village"}, "gardens": [{"x": 500, "y": 500, "w": 20, "h": 18, "rot": 0, "of": [500, 470]}], "village_groves": [{"role": "copse", "r": 11, "clumps": [[500, 500]]}]}
    assert "grove_clumps_clear_of_structures" in f(gd)
    sh = {"meta": {"scale": "village"}, "farm_sheds": [{"x": 500, "y": 500, "w": 24, "h": 20, "rot": 0, "of": [470, 500]}], "village_groves": [{"role": "copse", "r": 11, "clumps": [[500, 500]]}]}
    assert "grove_clumps_clear_of_structures" in f(sh)


# ---- shrine_halls_clear_of_lanes: a hall stands beside the road, torii may straddle it ----
def test_shrine_halls_clear_of_lanes_fires_on_a_hall_on_a_lane_exempts_torii():
    on = {
        "meta": {"scale": "village"},
        "religious": [{"x": 500, "y": 500, "w": 96, "h": 64, "kind": "shrine"}],
        "torii": [[500, 600, 1]],
        "lanes": [{"pts": [[500, 300], [500, 700]], "w": 6}],
    }  # lane threads through hall + torii
    assert "shrine_halls_clear_of_lanes" in f(on)  # the HALL on the lane fires
    off = {**on, "religious": [{"x": 600, "y": 500, "w": 96, "h": 64, "kind": "shrine"}]}  # hall to the side, torii still ON the lane
    assert "shrine_halls_clear_of_lanes" not in f(off)  # torii are exempt (road runs under the arch)


def test_shrine_halls_clear_of_lanes_fires_when_a_lane_ends_inside_the_hall():
    # a lane TERMINATING inside the hall footprint - exercises seg_to_rect_dist's endpoint-in-rect branch
    M = {"meta": {"scale": "village"}, "religious": [{"x": 500, "y": 500, "w": 96, "h": 64, "kind": "shrine"}], "lanes": [{"pts": [[500, 500], [500, 300]], "w": 6}]}
    assert "shrine_halls_clear_of_lanes" in f(M)


def test_seg_to_rect_dist_zero_on_corner_touch_and_positive_when_apart():
    r = {"x": 100, "y": 100, "w": 40, "h": 20, "rot": 0}  # x 80..120, y 90..110
    assert check_village.seg_to_rect_dist((100, 60), (100, 200), r) == 0.0  # vertical segment crosses the rect
    assert check_village.seg_to_rect_dist((90, 100), (110, 100), r) == 0.0  # segment lies fully INSIDE (endpoint-in branch)
    assert check_village.seg_to_rect_dist((200, 100), (260, 100), r) > 0  # a segment well to the east


# ---- gardens_unshaded_from_east: nudge an E-side garden S of a shading tree WHERE POSSIBLE ----
# a house with its garden on the E, a NEIGHBOR grove hard against the garden's east, open ground to the S
_EAST_SHADE = {
    "meta": {"scale": "village"},
    "houses": [{"x": 300, "y": 300, "w": 23, "h": 14, "rot": 0, "kind": "plain"}],
    "gardens": [{"x": 320, "y": 300, "w": 10, "h": 11, "rot": 0, "of": [300, 300]}],
    "groves": [{"x": 340, "y": 300, "w": 16, "h": 24, "rot": 0, "of": [380, 300], "face": [-1, 0]}],
}


def test_gardens_unshaded_from_east_fires_when_avoidable():
    assert "gardens_unshaded_from_east" in f(_EAST_SHADE)  # clear ground to the S -> the garden should have moved


def test_gardens_unshaded_from_east_exempts_a_south_boxed_garden():
    # each obstacle type to the S boxes the garden in -> unavoidable -> exempt (exercises every _bed_clear branch)
    house_s = {**_EAST_SHADE, "houses": _EAST_SHADE["houses"] + [{"x": 320, "y": 325, "w": 44, "h": 44, "rot": 0, "kind": "plain"}]}
    assert "gardens_unshaded_from_east" not in f(house_s)
    yard_s = {**_EAST_SHADE, "threshing_yards": [{"x": 320, "y": 325, "w": 44, "h": 44, "rot": 0, "of": [999, 999]}]}
    assert "gardens_unshaded_from_east" not in f(yard_s)
    lane_s = {**_EAST_SHADE, "lanes": [{"pts": [[280, 325], [360, 325]], "w": 40}]}  # a wide lane bars the whole shift band
    assert "gardens_unshaded_from_east" not in f(lane_s)
    water_s = {**_EAST_SHADE, "channels": [{"poly": [[280, 325], [360, 325]], "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}}]}
    assert "gardens_unshaded_from_east" not in f(water_s)
    hill_s = {**_EAST_SHADE, "hill": [320, 325, 30, 30]}
    assert "gardens_unshaded_from_east" not in f(hill_s)


def test_gardens_unshaded_from_east_skips_when_no_per_house_groves():
    # the rule is scoped to villages whose farms carry per-house windward groves; with none, it does not run
    assert "gardens_unshaded_from_east" not in f({k: v for k, v in _EAST_SHADE.items() if k != "groves"})


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


def test_vegetable_tracts_skip_the_farmstead_ring_checks():
    # kind="vegetable" in-wall garden tracts are worked by the surrounding quarters (well/
    # night-soil fed urban plots), so neither field_ringed nor the in-wall agricultural
    # farmhouse-density ring applies to them - only paddy carries farmsteads
    M = {
        "meta": {"scale": "city", "walled": True, "agricultural_district": True, "ftpx": 3, "W": 1000, "H": 1000},
        "wall": WALL + [WALL[0]],
        "fields": [{"name": "vg1", "kind": "vegetable", "bbox": [400, 400, 600, 600], "outline": [[400, 400], [600, 400], [600, 600], [400, 600]]}],
        "houses": [],
    }
    fails = f(M)
    assert "field_ringed[vg1]" not in fails
    assert "city_interior_fields_farmhouse_density" not in fails


def test_wells_clear_of_trees_fires_on_grove_forest_woodland_grect_but_passes_when_clear():
    # a wellhead is a clean draw-point: it must not sit under ANY tree - the fengshui grove clumps, the
    # per-house grove rects, a forest, or a coppice-woodland patch. Each type fires; a well on open ground does not.
    base = {"meta": {"scale": "village"}, "houses": [bldg(300, 300, "laborer")]}
    well = {"x": 500, "y": 500, "r": 8, "vr": 12}
    on_grove = {**base, "wells": [well], "village_groves": [{"role": "windbreak", "x": 505, "y": 505, "r": 14, "clumps": [[505, 505]]}]}
    assert "wells_clear_of_trees" in f(on_grove)
    on_forest = {**base, "wells": [well], "forest": [[400, 400], [600, 400], [600, 600], [400, 600]]}
    assert "wells_clear_of_trees" in f(on_forest)
    on_wood = {**base, "wells": [well], "commons": [{"x": 500, "y": 500, "role": "woodland", "poly": [[440, 440], [560, 440], [560, 560], [440, 560]]}]}
    assert "wells_clear_of_trees" in f(on_wood)
    on_grect = {**base, "wells": [well], "groves": [{"x": 505, "y": 505, "w": 40, "h": 30, "of": [300, 300], "face": [0, -1]}]}
    assert "wells_clear_of_trees" in f(on_grect)
    clear = {**base, "wells": [well], "village_groves": [{"role": "windbreak", "x": 900, "y": 900, "r": 14, "clumps": [[900, 900]]}]}
    assert "wells_clear_of_trees" not in f(clear)


def test_sacred_and_graves_off_marsh_fires_and_passes_on_dry_ground():
    # a shrine hall or a graveyard must NOT sit on a reed marsh (the wet valley toe) - only on dry ground.
    marsh = [[400, 400], [700, 400], [700, 700], [400, 700]]  # a toe marsh
    base = {"meta": {"scale": "village"}, "houses": [bldg(200, 200, "laborer")], "marshes": [{"x": 550, "y": 550, "w": 300, "h": 300, "role": "toe", "poly": marsh}]}
    on_shrine = {**base, "religious": [{"x": 550, "y": 550, "w": 96, "h": 64, "kind": "shrine"}]}
    assert "sacred_and_graves_off_marsh" in f(on_shrine)
    on_grave = {**base, "cemeteries": [{"x": 560, "y": 560, "w": 82, "h": 58, "rot": 0}]}
    assert "sacred_and_graves_off_marsh" in f(on_grave)
    dry = {**base, "religious": [{"x": 900, "y": 900, "w": 96, "h": 64, "kind": "shrine"}], "cemeteries": [{"x": 1000, "y": 1000, "w": 82, "h": 58, "rot": 0}]}
    assert "sacred_and_graves_off_marsh" not in f(dry)
    # a pond_fringe (thin decorative shore ring) is exempt - a shrine may sit beside a pond
    fringe = {**base, "marshes": [{"x": 550, "y": 550, "w": 300, "h": 300, "role": "pond_fringe", "poly": marsh}], "religious": [{"x": 550, "y": 550, "w": 96, "h": 64, "kind": "shrine"}]}
    assert "sacred_and_graves_off_marsh" not in f(fringe)


# ---- city_capacity: the wall-sizing space-budget analysis --------------------------------
# These pin the four verdicts, the ASCII interior map (each cell-class branch), and the
# _rects skip for a footprint-less item. city_capacity is called directly (it is analysis,
# not a gate check) - the gate wrapper only surfaces its too_small/too_big verdict via
# city_wall_sized_to_population.
def _diamond_city(pop, dwellings=0, **extra):
    # a diamond wall so the bbox corners fall OUTSIDE the polygon (covers the "outside" cell
    # branch); 400px across -> ~160000px^2 interior.
    wall = [[200, 0], [400, 200], [200, 400], [0, 200]]
    houses = [bldg(200 + (i % 20) * 3, 200 + (i // 20) * 3, "laborer", w=3, h=3) for i in range(dwellings)]
    M = {"meta": {"scale": "city", "population": pop}, "wall": wall, "buildings": houses}
    M.update(extra)
    return M


def test_city_capacity_too_small_when_wall_cannot_hold_target():
    # a 400px diamond holds ~200 well-packed; declaring 3000 (target 600) is far too small.
    rep = check_village.city_capacity(_diamond_city(3000))
    assert rep["verdict"] == "enlarge"
    assert rep["suggested_wall_scale"] > 1  # enlarge
    # and the gate check surfaces it
    assert "city_wall_sized_to_population" in f(_diamond_city(3000))


def test_city_capacity_too_big_when_wall_dwarfs_target():
    rep = check_village.city_capacity(_diamond_city(100))  # target 20, inherent ~200
    assert rep["verdict"] == "shrink"
    assert rep["suggested_wall_scale"] < 1  # shrink
    assert "city_wall_sized_to_population" in f(_diamond_city(100))


def test_city_capacity_underpacked_when_wall_right_but_placement_sparse():
    # target 100 (pop 500) sits inside the inherent band (~118 at RHO 1.49/1000), but only 10
    # dwellings placed -> the WALL is fine, the PLACEMENT is sparse (below the 7% population
    # line). Not a resize.
    rep = check_village.city_capacity(_diamond_city(500, dwellings=10))
    assert rep["verdict"] == "densify"
    # underpacked is NOT a wall-size fault, so the gate check stays silent
    assert "city_wall_sized_to_population" not in f(_diamond_city(500, dwellings=10))


def test_city_capacity_about_right_when_sized_and_packed():
    rep = check_village.city_capacity(_diamond_city(500, dwellings=95))
    assert rep["verdict"] == "sized_and_packed"
    assert "city_wall_sized_to_population" not in f(_diamond_city(500, dwellings=95))


def test_city_capacity_ascii_map_classes_every_cell_kind():
    # one manifest carrying a cell of each class, sampled fine enough to hit each branch.
    M = _diamond_city(
        185,
        dwellings=1,
        buildings=[
            bldg(200, 100, "laborer", w=34, h=34),  # D
            bldg(100, 220, "shop", w=34, h=34),
        ],  # C (civic list)
        canals=[{"poly": [[140, 300], [260, 300]], "w": 40}],  # ~ water
        fields=[{"outline": [[280, 180], [320, 180], [320, 220], [280, 220]], "bbox": [280, 180, 320, 220]}],  # F
        road=[[200, 140], [200, 260]],
        road_width=26,  # # trunk
        town_streets=[{"pts": [[120, 160], [180, 160]], "w": 12}],  # + res_st
    )
    rep = check_village.city_capacity(M, grid_step=20)
    flat = "".join(rep["grid"])
    for sym in "DC~F#+. ":  # every class incl. OPEN and OUTSIDE
        assert sym in flat, f"class {sym!r} never sampled"
    assert rep["grid_step"] == 20 and rep["grid_origin"] == (0, 0)


def test_city_capacity_skips_footprintless_item():
    # a dwelling dict with no "w" is skipped by _rects (no rect to sample) but still COUNTS
    # toward placed D - exercises the "if 'w' not in it: continue" guard without crashing.
    M = _diamond_city(185)
    M["buildings"] = [{"x": 200, "y": 200, "kind": "laborer"}]  # footprint-less
    rep = check_village.city_capacity(M)
    assert rep["placed"] == 1


# ---- feature 006: in-wall population + extramural commoners ------------------------------
_CITY_WALL = [[200, 200], [800, 200], [800, 800], [200, 800]]  # 600x600 box


def _pop_city(buildings, population=100, **extra):
    M = {"meta": {"scale": "city", "population": population}, "wall": _CITY_WALL, "buildings": buildings}
    M.update(extra)
    return M


def test_population_counts_only_in_wall_dwellings_for_a_walled_city():
    # 20 dwellings inside -> ~100 residents, passes.
    inside = [bldg(300 + (i % 10) * 20, 300, "laborer") for i in range(20)]
    assert "population_consistent_with_housing" not in f(_pop_city(inside))
    # 15 inside + 5 spilled OUTSIDE (x=50) = 20 total: the OLD count (all 20) would pass, but only
    # the 15 in-wall now count -> ~75 residents -> fails. The spill cannot rescue the figure.
    spilled = [bldg(300 + (i % 10) * 20, 300, "laborer") for i in range(15)] + [bldg(50, 300 + i * 20, "laborer") for i in range(5)]
    assert "population_consistent_with_housing" in f(_pop_city(spilled))


def test_city_commoner_dwellings_inside_walls_fires_on_a_spilled_commoner():
    inside = [bldg(300 + (i % 10) * 20, 300, "laborer") for i in range(20)]
    assert "city_commoner_dwellings_inside_walls" not in f(_pop_city(inside))
    # one laborer outside the wall -> fires (hard zero)
    leaky = inside + [bldg(50, 500, "laborer")]
    assert "city_commoner_dwellings_inside_walls" in f(_pop_city(leaky))


def test_city_commoner_dwellings_exempts_samurai_and_shops_outside():
    # samurai country estate + a gate-market shop OUTSIDE the wall are legitimate; not flagged.
    inside = [bldg(300 + (i % 10) * 20, 300, "laborer") for i in range(20)]
    exempt_outside = inside + [bldg(50, 300, "samurai"), bldg(50, 400, "samurai_large"), bldg(900, 500, "shop")]
    assert "city_commoner_dwellings_inside_walls" not in f(_pop_city(exempt_outside))


# ---- feature 006: declared quarters, per-quarter density, civic-open, reserve-cap ---------
def _qcity(quarters, buildings=None, **extra):
    M = {"meta": {"scale": "city"}, "wall": _CITY_WALL, "quarters": quarters, "buildings": buildings or []}
    M.update(extra)
    return M


_FULL_Q = [[200, 200], [800, 200], [800, 800], [200, 800]]  # a quarter covering the whole interior


def _dwell_grid(x0, x1, y0, y1, n, kind="laborer"):
    return [bldg(x0 + (x1 - x0) * i / (n - 1), y0 + (y1 - y0) * j / (n - 1), kind) for i in range(n) for j in range(n)]


def test_city_quarters_declared_fires_when_absent_passes_when_present():
    assert "city_quarters_declared" in f({"meta": {"scale": "city"}, "wall": _CITY_WALL, "buildings": []})
    ok = _qcity([{"poly": _FULL_Q, "zone": "residential", "kind": None, "name": "q"}])
    assert "city_quarters_declared" not in f(ok)


def test_city_quarters_tile_interior_passes_on_a_clean_two_half_tiling():
    left = {"poly": [[200, 200], [500, 200], [500, 800], [200, 800]], "zone": "residential", "kind": None, "name": "L"}
    right = {"poly": [[500, 200], [800, 200], [800, 800], [500, 800]], "zone": "residential", "kind": None, "name": "R"}
    # both packed enough to pass density, so we isolate the tiling result
    b = _dwell_grid(230, 470, 230, 770, 12) + _dwell_grid(530, 770, 230, 770, 12)
    assert "city_quarters_tile_interior" not in f(_qcity([left, right], b))


def test_city_quarters_tile_interior_fires_on_gap_overlap_and_spill():
    half = {"poly": [[200, 200], [500, 200], [500, 800], [200, 800]], "zone": "civic", "kind": None, "name": "half"}
    assert "city_quarters_tile_interior" in f(_qcity([half]))  # only half covered -> gap
    dup = {"poly": _FULL_Q, "zone": "civic", "kind": None, "name": "a"}
    dup2 = {"poly": _FULL_Q, "zone": "civic", "kind": None, "name": "b"}
    assert "city_quarters_tile_interior" in f(_qcity([dup, dup2]))  # doubled -> overlap
    spill = {"poly": [[50, 200], [800, 200], [800, 800], [50, 800]], "zone": "civic", "kind": None, "name": "s"}
    assert "city_quarters_tile_interior" in f(_qcity([spill]))  # extends past the wall


def test_city_residential_density_passes_in_band():
    q = {"poly": _FULL_Q, "zone": "residential", "kind": None, "name": "warren"}
    b = _dwell_grid(210, 790, 210, 790, 17)  # 289 dwellings evenly spread -> in band, no dead zone
    assert "city_residential_quarters_dense_enough" not in f(_qcity([q], b))


def test_city_residential_density_fires_below_floor_and_above_ceil():
    q = {"poly": _FULL_Q, "zone": "residential", "kind": None, "name": "warren"}
    sparse = _dwell_grid(210, 790, 210, 790, 6)  # 36 dwellings -> below floor
    assert "city_residential_quarters_dense_enough" in f(_qcity([q], sparse))
    crammed = _dwell_grid(210, 790, 210, 790, 30)  # 900 dwellings -> above ceil
    assert "city_residential_quarters_dense_enough" in f(_qcity([q], crammed))


def test_city_residential_density_fires_on_a_dead_zone_despite_a_good_average():
    # in-band average, but every dwelling is jammed into one corner - the far half is a dead zone.
    q = {"poly": _FULL_Q, "zone": "residential", "kind": None, "name": "lopsided"}
    corner = _dwell_grid(210, 400, 210, 400, 16)  # ~256 dwellings, density over the whole quarter in band
    assert "city_residential_quarters_dense_enough" in f(_qcity([q], corner))


def test_city_civic_quarter_passes_with_a_compound_fires_when_bare():
    civic = {"poly": _FULL_Q, "zone": "civic", "kind": None, "name": "yamen precinct"}
    with_compound = _qcity([civic], governor_mansion={"x": 500, "y": 500, "w": 400, "h": 300, "rot": 0})
    assert "city_civic_quarter_not_mostly_open" not in f(with_compound)
    bare = _qcity([civic], ministries=[{"x": 500, "y": 500, "w": 130, "h": 90, "rot": 0}])  # tiny building in a big quarter
    assert "city_civic_quarter_not_mostly_open" in f(bare)


def test_city_reserve_within_cap_passes_under_and_fires_over():
    small = {"poly": [[250, 250], [500, 250], [500, 500], [250, 500]], "zone": "reserve", "kind": "drill_ground", "name": "drill"}
    assert "city_reserve_within_cap" not in f(_qcity([small]))  # 62500/360000 = 17% <= 20%
    big = {"poly": [[250, 250], [550, 250], [550, 550], [250, 550]], "zone": "reserve", "kind": "drill_ground", "name": "drill"}
    assert "city_reserve_within_cap" in f(_qcity([big]))  # 90000/360000 = 25% > 20%


# ---- feature 006: reworked capacity verdict (usable residential ground + reserve) ------------
def test_city_capacity_counts_only_in_wall_dwellings():
    # extramural dwellings do not inflate the placed count
    wall = _CITY_WALL
    inside = [bldg(300 + (i % 10) * 20, 300, "laborer") for i in range(20)]
    M = {"meta": {"scale": "city", "population": 100}, "wall": wall, "buildings": inside + [bldg(50, 500, "laborer")]}
    assert check_village.city_capacity(M)["placed"] == 20  # the outside one is not counted


def test_city_capacity_shrinks_when_reserve_over_cap():
    # a city whose empty ground is declared reserve beyond the cap reads SHRINK, never sized_and_packed
    over = {"poly": [[250, 250], [560, 250], [560, 560], [250, 560]], "zone": "reserve", "kind": "drill_ground", "name": "drill"}
    b = _dwell_grid(210, 790, 210, 790, 17)
    M = _pop_city(b, population=400, quarters=[over])
    rep = check_village.city_capacity(M)
    assert rep["verdict"] == "shrink"  # reserve_frac over the 20% cap forces shrink
    assert rep["reserve_frac"] > check_village.RESERVE_CAP_FRAC
    # and the gate check surfaces it
    assert "city_wall_sized_to_population" in f(M)


def test_city_capacity_per_quarter_table_lists_residential_quarters():
    q = {"poly": _FULL_Q, "zone": "residential", "kind": None, "name": "warren"}
    civic = {"poly": [[600, 600], [790, 600], [790, 790], [600, 790]], "zone": "civic", "kind": None, "name": "yamen"}
    M = _pop_city(_dwell_grid(210, 560, 210, 560, 12), population=400, quarters=[q, civic])
    rep = check_village.city_capacity(M)
    names = {pq["name"] for pq in rep["per_quarter"]}
    assert "warren" in names and "yamen" not in names  # residential listed; pure civic not in the density table


# ---- feature 006: defensive-branch coverage (empty pts, degenerate quarter) ----------------
def test_largest_empty_gap_is_infinite_with_no_points():
    assert check_village.largest_empty_gap([[0, 0], [10, 0], [10, 10], [0, 10]], []) == float("inf")


def test_quarter_checks_skip_a_degenerate_zero_area_quarter():
    # collinear (zero-area) quarters are skipped by the residential-density and civic-open loops
    # rather than dividing by zero.
    good = {"poly": _FULL_Q, "zone": "residential", "kind": None, "name": "warren"}
    degen_res = {"poly": [[400, 400], [500, 400], [600, 400]], "zone": "residential", "kind": None, "name": "res-sliver"}
    degen_civ = {"poly": [[400, 500], [500, 500], [600, 500]], "zone": "civic", "kind": None, "name": "civ-sliver"}
    b = _dwell_grid(210, 790, 210, 790, 17)
    M = _pop_city(b, population=400, quarters=[good, degen_res, degen_civ])
    fails = f(M)
    assert "city_residential_quarters_dense_enough" not in fails  # good quarter passes; degenerate skipped
    assert "city_civic_quarter_not_mostly_open" not in fails  # zero-area civic quarter skipped, no crash
    check_village.city_capacity(M)  # does not crash on a degenerate quarter


# ---- overlap rules (2026-07-13): gate towers, ward fence, kido on fence -------------------
def test_city_gate_towers_clear_of_gate_furniture():
    wall = _CITY_WALL
    base = {
        "meta": {"scale": "city", "walled": True},
        "wall": wall,
        "gates": [[500, 200]],
        "gate_structs": [{"x": 500, "y": 230, "w": 40, "h": 40, "kind": "tower"}, {"x": 560, "y": 230, "w": 60, "h": 44, "kind": "inspection"}],
    }
    assert "city_gate_towers_clear_of_gate_furniture" not in f(base)  # 60px apart, clear
    over = {**base, "gate_structs": [{"x": 500, "y": 230, "w": 40, "h": 40, "kind": "tower"}, {"x": 530, "y": 230, "w": 60, "h": 44, "kind": "inspection"}]}
    assert "city_gate_towers_clear_of_gate_furniture" in f(over)  # 30px -> footprints overlap


def _ward006(**extra):
    # a walled city with a sealed rectangular ward whose fence ends abut the wall
    wall = _CITY_WALL
    bnd = [[200, 500], [500, 500], [500, 700], [200, 700]]  # a fence with ends on the W wall (x=200)
    M = {
        "meta": {"scale": "city", "walled": True},
        "wall": wall,
        "gates": [[500, 200]],
        "wards": [{"name": "samurai", "boundary": bnd, "z": 10}],
        "kido": [{"x": 500, "y": 600, "horizontal": False, "bbox": [490, 590, 510, 610]}],
    }
    M.update(extra)
    return M


def test_city_ward_fence_clear_of_structures_fires_on_a_building_on_the_fence():
    clear = _ward006(buildings=[bldg(350, 550, "samurai")])  # inside the ward, off the fence
    assert "city_ward_fence_clear_of_structures" not in f(clear)
    onfence = _ward006(buildings=[bldg(350, 500, "samurai")])  # centered ON the top fence line
    assert "city_ward_fence_clear_of_structures" in f(onfence)
    maus = _ward006(mausoleums=[{"x": 500, "y": 600, "w": 44, "h": 32, "rot": 0}])  # the E fence passes through it
    assert "city_ward_fence_clear_of_structures" in f(maus)


def test_city_kido_on_ward_fence_fires_when_the_gate_is_beside_the_fence():
    on = _ward006()  # kido at (500,600) is ON the E fence (x=500)
    assert "city_kido_on_ward_fence" not in f(on)
    beside = _ward006(kido=[{"x": 470, "y": 600, "horizontal": False, "bbox": [460, 590, 480, 610]}])  # 30px inside
    assert "city_kido_on_ward_fence" in f(beside)


def test_city_ward_fence_clear_fires_when_two_ward_fences_cross():
    wall = _CITY_WALL
    a = {"name": "a", "boundary": [[200, 400], [600, 400], [600, 401]], "z": 10}
    b = {"name": "b", "boundary": [[400, 200], [400, 600], [401, 600]], "z": 10}  # crosses a's fence at (400,400)
    M = {"meta": {"scale": "city", "walled": True}, "wall": wall, "gates": [[500, 200]], "wards": [a, b], "kido": []}
    assert "city_ward_fence_clear_of_structures" in f(M)


# ---- robustness: bounded sweeps + geometry sanity (2026-07-14, hang on malformed input) ----
def test_sweep_hi_clamps_a_runaway_bound_but_not_a_normal_one():
    assert check_village.sweep_hi(0, 3000, 8) == 3000  # a normal map span is untouched
    assert check_village.sweep_hi(0, 9_000_000, 8) == 8 * 500  # a runaway bound is clamped to cap*step


def test_city_geometry_within_canvas_fires_on_a_stray_vertex():
    good = _qcity([{"poly": _FULL_Q, "zone": "residential", "kind": None, "name": "q"}], meta={"scale": "city", "W": 3200, "H": 2700})
    assert "city_geometry_within_canvas" not in f(good)
    bad = {
        "meta": {"scale": "city", "W": 3200, "H": 2700},
        "wall": _CITY_WALL + [[9_000_000, 9_000_000]],
        "quarters": [{"poly": _FULL_Q, "zone": "residential", "kind": None, "name": "q"}],
        "buildings": [],
    }
    assert "city_geometry_within_canvas" in f(bad)  # a vertex millions of px off is flagged


def test_gate_does_not_hang_on_a_runaway_quarter_vertex():
    # the sweeps must terminate on garbage geometry (the whole point of sweep_hi) - if this test
    # runs to completion at all, the sweep did not loop forever.
    M = {
        "meta": {"scale": "city", "walled": True, "population": 3000, "W": 3200, "H": 2700},
        "wall": _CITY_WALL,
        "buildings": [bldg(300 + (i % 10) * 20, 300, "laborer") for i in range(20)],
        "quarters": [{"poly": [[200, 200], [9_000_000, 200], [9_000_000, 9_000_000], [200, 9_000_000]], "zone": "residential", "kind": None, "name": "runaway"}],
    }
    fails = f(M)
    assert "city_geometry_within_canvas" in fails


# ---- households_consistent: the LEGACY (extended-family) band on an off-scale tier -----------
# On a to-scale tier (village/hamlet, or meta.toscale) the map depicts ~every household 1:1
# (~0.85-1.05x). A tier that is NOT to-scale (a town/city carrying a `households` meta, or an
# explicit toscale:False) falls to the legacy ~0.68-0.9x extended-family band. This pins that
# branch: a town declaring 100 households but depicting zero farmhouses is out of even the
# looser legacy band and must fire.
def test_households_consistent_uses_legacy_band_when_not_to_scale():
    M = {"meta": {"scale": "town", "households": 100}}  # town => scale != "village", no toscale => legacy band
    assert "households_consistent" in f(M)


# ---- channel_source_anchored: a channel that claims a FOREST source ------------------------
# A watercourse anchor of kind "forest" is grounded iff a forest polygon exists AND the anchor
# point lies inside it. A channel declaring a forest source whose tap sits OUTSIDE the drawn
# forest is ungrounded and must fire (exercises the forest branch of anchored()).
def test_channel_source_anchored_fires_when_forest_tap_is_outside_the_forest():
    M = {
        "forest": [[100, 100], [300, 100], [300, 300], [100, 300]],
        "channels": [{"poly": [[500, 500], [510, 400], [520, 300]], "frm": {"kind": "forest"}, "to": {"kind": "offmap"}}],
    }
    assert "channel_source_anchored[0]" in f(M)


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


# ---- gardens_unshaded_from_east: a garden truly boxed in to the SOUTH by a bog is EXEMPT ----
# The east-shade relaxer only fires when a small SOUTHWARD nudge into OPEN ground would clear
# the morning-sun shadow. When every candidate shift lands the garden bed on a bog/marsh (or a
# field outline), no clear shift exists, so the garden is exempt and the check must NOT fire.
# This pins the field-outline / bog clause of the internal _bed_clear helper.
def test_gardens_unshaded_from_east_exempt_when_south_shift_blocked_by_a_bog():
    M = {
        "meta": {"scale": "village"},
        "houses": [{"x": 500, "y": 500, "w": 40, "h": 30, "rot": 0, "kind": "plain"}],
        "gardens": [{"x": 500, "y": 500, "w": 30, "h": 30, "of": [500, 500]}],
        "groves": [{"x": 545, "y": 500, "w": 40, "h": 30, "of": [999, 999]}],  # neighbor grove hard against the garden's east
        "marshes": [{"poly": [[480, 510], [520, 510], [520, 600], [480, 600]]}],  # bog fills the whole southward corridor
    }
    assert "gardens_unshaded_from_east" not in f(M)


# ---- Pool-level twin-detector (feature 005) -----------------------------------------------------
# The cross-map check that mechanically guards the distinctiveness goal: two same-down_deg villages must
# differ on >= TWIN_MIN_DIFF of the 7 structural axes, or they read as copies (the Kikuta/Hoshigaoka twin).


def _tv(**over):
    """A minimal village manifest with the fields twin_axes reads; `over` merges (meta merges nested)."""
    M = {
        "meta": {"scale": "village", "down_deg": 45},
        "houses": [
            {"x": 380, "y": 620, "role": "plain"},
            {"x": 420, "y": 700, "role": "plain"},
            {"x": 400, "y": 560, "role": "headman"},
            {"x": 440, "y": 660, "role": "plain"},
        ],
        "fields": [{"bbox": [566, 313, 2122, 1392]}],
        "pond": [420, 210, 145, 92],
        "dry_plots": [{"theta": -0.8}, {"theta": -0.9}, {"theta": -0.7}],
    }
    for k, v in over.items():
        if k == "meta":
            M["meta"] = {**M["meta"], **v}
        else:
            M[k] = v
    return M


def test_twin_detector_fires_on_twinned_pair():
    # two structurally-identical villages (the Kikuta/Hoshigaoka situation) -> zero axes differ -> TWINNED
    rep = check_village.twin_report([_tv(meta={"name": "A"}), _tv(meta={"name": "B"})])
    assert len(rep) == 1
    assert rep[0]["verdict"] == "TWINNED" and rep[0]["diffs"] == 0 and rep[0]["pair"] == ("A", "B")


def test_twin_detector_passes_distinct_pair():
    a = _tv(meta={"name": "A", "cluster_shape": "round", "lane_skeleton": "spine", "water_source_position": "corner_NW", "focal_features": []})
    b = _tv(meta={"name": "B", "cluster_shape": "crescent", "lane_skeleton": "cross", "water_source_position": "chain", "focal_features": ["mill"]})
    rep = check_village.twin_report([a, b])
    assert len(rep) == 1 and rep[0]["verdict"] == "PASS" and rep[0]["diffs"] >= 4


def test_twin_detector_skips_different_or_missing_down_deg():
    a = _tv(meta={"name": "A", "down_deg": 45})
    b = _tv(meta={"name": "B", "down_deg": 135})
    c = _tv(meta={"name": "C"})
    c["meta"].pop("down_deg")
    assert check_village.twin_report([a, b]) == []  # different water direction -> not compared
    assert check_village.twin_report([a, c]) == []  # one map lacks down_deg -> not compared


def test_twin_axes_geometric_fallbacks_no_meta_knobs():
    ax = check_village.twin_axes(_tv(meta={"name": "G"}))
    assert ax["cluster_region"] == "W"  # cluster sits W of the field center
    assert ax["cluster_shape"] == "tall"  # bbox 60 wide x 140 tall -> r < 0.7
    assert ax["headman_side"] == "N"  # headman N of the cluster centroid
    assert ax["water_source"] == "NW"  # pond NW of the field center
    assert ax["lane_skeleton"] is None  # no declared knob, no geometric fallback
    assert ax["focal_set"] == frozenset()
    assert isinstance(ax["grain_orient"], int)


def test_twin_axes_round_cluster_center_headman_and_dir8_deadzone():
    # a square cluster CENTERED on the field center: round shape, headman AT the centroid (center),
    # and cluster_region hits _dir8's zero-vector dead zone -> None
    houses = [
        {"x": 300, "y": 300, "role": "plain"},
        {"x": 400, "y": 300, "role": "plain"},
        {"x": 300, "y": 400, "role": "plain"},
        {"x": 400, "y": 400, "role": "plain"},
        {"x": 350, "y": 350, "role": "headman"},
    ]
    ax = check_village.twin_axes({"meta": {"name": "R", "down_deg": 45}, "houses": houses, "fields": [{"bbox": [0, 0, 700, 700]}]})
    assert ax["cluster_shape"] == "round"  # w == h
    assert ax["headman_side"] == "center"  # headman at the cluster center
    assert ax["cluster_region"] is None  # centroid == field center -> dead zone
    assert ax["water_source"] is None and ax["grain_orient"] is None  # no pond, no dry_plots


def test_twin_axes_wide_cluster_and_bare_manifest():
    wide = [{"x": 100, "y": 300, "role": "plain"}, {"x": 500, "y": 300, "role": "plain"}, {"x": 300, "y": 320, "role": "plain"}]
    axw = check_village.twin_axes({"meta": {"name": "W", "down_deg": 45}, "houses": wide, "fields": [{"bbox": [0, 0, 700, 700]}]})
    assert axw["cluster_shape"] == "wide"  # 400 wide x 20 tall -> r > 1.4
    # a bare manifest: every geometric axis is 'no evidence'
    ax = check_village.twin_axes({"meta": {"name": "bare", "down_deg": 45}})
    assert ax["cluster_region"] is None and ax["cluster_shape"] is None and ax["headman_side"] is None
    assert ax["water_source"] is None and ax["grain_orient"] is None and ax["focal_set"] == frozenset()


def test_twin_report_none_axes_are_no_evidence_not_a_diff():
    # a fully-featured map vs a bare one: the bare map's None axes must NOT count as differences (a data
    # gap cannot manufacture distinctiveness) -> the pair stays TWINNED, not spuriously PASS
    rep = check_village.twin_report([_tv(meta={"name": "A"}), {"meta": {"name": "B", "down_deg": 45}}])
    assert len(rep) == 1 and rep[0]["verdict"] == "TWINNED"


def test_twin_report_uses_index_when_unnamed():
    rep = check_village.twin_report([{"meta": {"down_deg": 45}}, {"meta": {"down_deg": 45}}])
    assert rep and rep[0]["pair"] == ("0", "1")


def test_twin_settlement_form_is_an_axis():
    # nucleated blob vs linear ribbon - the biggest structural read - is a twin-detector axis; it defaults
    # to 'nucleated' when a map does not declare it (so an undeclared map is not spuriously "different")
    assert "settlement_form" in check_village.TWIN_AXES
    a = _tv(meta={"name": "A", "settlement_form": "nucleated"})
    b = _tv(meta={"name": "B", "settlement_form": "linear"})
    ax, bx = check_village.twin_axes(a), check_village.twin_axes(b)
    assert ax["settlement_form"] == "nucleated" and bx["settlement_form"] == "linear"
    assert check_village.twin_axes(_tv(meta={"name": "C"}))["settlement_form"] == "nucleated"  # default
    assert check_village.twin_diff_count(ax, bx) == 1  # differ on settlement_form alone (otherwise identical)


# ---- dwellings must not sit in the WET low toe below the field's drainage ditch (feature 005 / GM 2026-07) ----


def test_contour_terraces_require_stepped_cross_slope_bands():
    # a field declared field_archetype=contour_terraces must show >=8 cross-slope terrace bunds; too few, or bunds
    # that run downhill (channels, not terrace lips), fires.
    base = {"meta": {"scale": "hamlet", "down_deg": 90, "field_archetype": "contour_terraces"}}
    good = {**base, "terrace_bunds": [*([[100, 200 + i * 80], [900, 200 + i * 80]] for i in range(10)), [[500, 900]]]}  # 10 wide E-W bands + a degenerate 1-pt bund (skipped)
    assert "contour_terraces_are_stepped_bands" not in f(good)
    few = {**base, "terrace_bunds": [[[100, 200 + i * 80], [900, 200 + i * 80]] for i in range(4)]}  # only 4
    assert "contour_terraces_are_stepped_bands" in f(few)
    downhill = {**base, "terrace_bunds": [[[100 + i * 40, 200], [100 + i * 40, 900]] for i in range(10)]}  # bunds run N-S (downhill)
    assert "contour_terraces_are_stepped_bands" in f(downhill)


def test_polder_field_must_fill_its_bbox():
    # a field declared field_archetype=polder_grid must FILL its bounding box (a surveyed rectangle); a fan-shaped
    # outline covering only a fraction of its bbox fires.
    base = {"meta": {"scale": "hamlet", "field_archetype": "polder_grid"}}
    rect = {**base, "fields": [{"name": "p", "kind": "paddy", "outline": [[100, 100], [900, 100], [900, 1300], [100, 1300]], "bbox": [100, 100, 900, 1300]}]}
    assert "polder_fills_its_bbox" not in f(rect)
    fan = {**base, "fields": [{"name": "p", "kind": "paddy", "outline": [[500, 100], [900, 1300], [100, 1300]], "bbox": [100, 100, 900, 1300]}]}  # a triangle covers ~half its bbox
    assert "polder_fills_its_bbox" in f(fan)


def test_polder_parcel_fabric_must_vary():
    # a polder's parcels must be a PATCHWORK (varied oblongs), never identical cells: the surveyed
    # chessboard was the canal grid, the parcels inside were private-tenure fragments (grounding in
    # build_polder's docstring). The uniform 66x [142,142] block is the real pre-fix Kuwabata/Enokida
    # geometry. Applies to both polder-geometry archetypes; a polder manifest with NO recorded parcel
    # geometry fires too (no passing by omission).
    field = {"name": "p", "kind": "paddy", "outline": [[100, 100], [900, 100], [900, 1300], [100, 1300]], "bbox": [100, 100, 900, 1300]}
    varied = [[142, 68], [142, 66], [75, 142], [44, 142], [142, 142], [290, 142]] * 11
    for arch in ("polder_grid", "mulberry_dike_fishpond"):
        base = {"meta": {"scale": "hamlet", "field_archetype": arch}}
        assert "polder_parcels_vary" in f({**base, "fields": [{**field, "plots": [[142.0, 142.0]] * 66}]})
        assert "polder_parcels_vary" in f({**base, "fields": [field]})  # no parcel geometry recorded
        assert "polder_parcels_vary" in f({**base, "fields": [{**field, "plots": varied[:6]}]})  # too few to judge
        assert "polder_parcels_vary" not in f({**base, "fields": [{**field, "plots": varied}]})
    # a non-polder archetype never trips it, plots or not
    assert "polder_parcels_vary" not in f({"meta": {"scale": "hamlet", "field_archetype": "valley_paddy"}, "fields": [{**field, "plots": [[142.0, 142.0]] * 66}]})


def test_torii_full_avenue_is_seven():
    # GM numerology canon (2026-07-21): a torii approach is 1-2 (modest entrance) or EXACTLY 7 (full
    # avenue); 3-6 and 8+ fire. Arches assign to their nearest religious feature.
    hall = {"kind": "monastery", "x": 500, "y": 500, "w": 50, "h": 33, "label": "Monastery of Bishamon"}

    def m(n, kind="monastery"):
        return {"meta": {"scale": "town"}, "religious": [{**hall, "kind": kind}], "torii": [[500, 560 + 40 * i, 9] for i in range(n)]}

    assert "torii_full_avenue_is_seven" in f(m(4))  # the Hirameki defect
    assert "torii_full_avenue_is_seven" in f(m(3, kind="shrine"))
    assert "torii_full_avenue_is_seven" in f(m(8))
    for ok in (1, 2, 7):
        assert "torii_full_avenue_is_seven" not in f(m(ok))
    # no religious features -> the check has nothing to assign to and stays silent
    assert "torii_full_avenue_is_seven" not in f({"meta": {"scale": "town"}, "torii": [[500, 560, 9]] * 4})


def test_polder_parcels_must_front_a_ditch():
    # every polder parcel must sit within reach of a supply/drain ditch (the jingbang creek-and-ditch
    # interior): parcels far from every ditch fire, parcels without recorded centroids (pre-fix format)
    # fire, and a laterals-served fabric passes. GM-flagged on the original Kuwabata (floating ponds).
    field = {"name": "p", "kind": "paddy", "outline": [[100, 100], [900, 100], [900, 1300], [100, 1300]], "bbox": [100, 100, 900, 1300]}
    lat = {"poly": [[500, 88], [500, 1312]], "role": "lateral", "field": "p", "w": 3.2, "w_tail": 2.4}
    # varied 4-tuple parcels hugging the x=500 lateral: centroids at x 430/570, spans ~140 -> reach ~103
    served = [[140, 70, 430, 100 + 90 * i] for i in range(7)] + [[140, 140, 570, 100 + 160 * i] for i in range(7)]
    for arch in ("polder_grid", "mulberry_dike_fishpond"):
        base = {"meta": {"scale": "hamlet", "field_archetype": arch}, "field_ditches": [lat]}
        assert "polder_parcels_front_water" not in f({**base, "fields": [{**field, "plots": served}]})
        adrift = [*served, [140, 140, 880, 1280]]  # one parcel ~380px from the lateral
        assert "polder_parcels_front_water" in f({**base, "fields": [{**field, "plots": adrift}]})
        no_cent = [*served, [140.0, 140.0]]  # pre-fix 2-tuple record: no centroid = no frontage
        assert "polder_parcels_front_water" in f({**base, "fields": [{**field, "plots": no_cent}]})
        # no ditches recorded at all -> everything is unfronted
        assert "polder_parcels_front_water" in f({"meta": base["meta"], "fields": [{**field, "plots": served}]})


def test_ribbon_valley_must_be_long_and_narrow():
    base = {"meta": {"scale": "hamlet", "down_deg": 90, "field_archetype": "ribbon_valley"}}
    thin = {**base, "fields": [{"name": "r", "kind": "paddy", "outline": [[400, 100], [700, 100], [700, 2000], [400, 2000]], "bbox": [400, 100, 700, 2000]}]}  # 300 wide x 1900 long
    assert "ribbon_is_long_and_narrow" not in f(thin)
    squat = {**base, "fields": [{"name": "r", "kind": "paddy", "outline": [[100, 100], [1400, 100], [1400, 900], [100, 900]], "bbox": [100, 100, 1400, 900]}]}  # 1300 x 800, too broad
    assert "ribbon_is_long_and_narrow" in f(squat)


def test_mulberry_dike_fishpond_needs_a_block_of_ponds():
    base = {"meta": {"scale": "hamlet", "field_archetype": "mulberry_dike_fishpond"}}
    rect_ol = [[100, 100], [900, 100], [900, 1300], [100, 1300]]
    good = {**base, "fields": [{"name": "p", "kind": "paddy", "outline": rect_ol, "bbox": [100, 100, 900, 1300]}], "land_use": [{"overlay": "mulberry_fishpond", "count": 40}]}
    assert "dikepond_is_ponds_in_a_block" not in f(good)
    no_ponds = {**base, "fields": [{"name": "p", "kind": "paddy", "outline": rect_ol, "bbox": [100, 100, 900, 1300]}]}  # a block but no fishponds
    assert "dikepond_is_ponds_in_a_block" in f(no_ponds)


def test_overlays_must_sit_on_the_low_wet_ground():
    """Feature 010. A plot-based land-use overlay is sited by TOPOGRAPHY, not chance: deep-water lotus
    (30-50cm) cannot sit on ground that grows rice at 5-9cm, and dike-ponds were dug out of the low
    flood-prone hollows. The teeth come from `wet_plots` being written by the FIELD pass while
    `land_use[].plots` is written by the OVERLAY pass - two independent records, not a self-report."""
    base = {"meta": {"scale": "village", "land_use_overlay": "lotus"}, "wet_plots": [[100, 100], [140, 100], [180, 100]]}
    good = {**base, "land_use": [{"overlay": "lotus", "count": 2, "plots": [[100, 100], [140, 100]]}]}
    assert "overlays_on_wet_ground_only" not in f(good)
    off = {**base, "land_use": [{"overlay": "lotus", "count": 2, "plots": [[100, 100], [900, 900]]}]}  # one plot up on dry rice ground
    assert "overlays_on_wet_ground_only" in f(off)
    # the ORIGINAL defect this feature fixed: a uniform random sample over ALL plots, so nothing lands on wet ground
    random_sample = {**base, "land_use": [{"overlay": "lotus", "count": 3, "plots": [[500, 220], [730, 640], [910, 480]]}]}
    assert "overlays_on_wet_ground_only" in f(random_sample)
    # the NAMED wholesale-conversion opt-out (the dike-pond ARCHETYPE) is exempt by design, not by accident
    archetype = {**base, "land_use": [{"overlay": "lotus", "count": 2, "eligible": "all", "plots": [[900, 900]]}]}
    assert "overlays_on_wet_ground_only" not in f(archetype)


def test_land_use_overlay_drawn_tolerates_having_no_eligible_ground():
    """Feature 010. Drawing nothing is the HONEST outcome when a field has no low/wet ground, so that must
    not trip the gate - but a declared overlay that simply never called apply_land_use still must."""
    base = {"meta": {"scale": "village", "land_use_overlay": "lotus"}}
    no_ground = {**base, "wet_plots": [], "land_use": [{"overlay": "lotus", "count": 0, "plots": []}]}
    assert "land_use_overlay_drawn" not in f(no_ground)
    never_called = {**base, "wet_plots": [[100, 100]], "land_use": []}
    assert "land_use_overlay_drawn" in f(never_called)
    had_ground_but_empty = {**base, "wet_plots": [[100, 100]], "land_use": [{"overlay": "lotus", "count": 0, "plots": []}]}
    assert "land_use_overlay_drawn" in f(had_ground_but_empty)


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


# ---- feature 009: the wall must match the declared space budget -----------------------------
def _budget_city(budget=None):
    # a walled city whose square wall encloses 600x600 = 360,000 px^2
    M = {"meta": {"scale": "city", "walled": True}, "wall": [[200, 200], [800, 200], [800, 800], [200, 800]]}
    if budget is not None:
        M["meta"]["budget"] = budget
    return M


def test_city_wall_matches_budget_fires_when_no_budget_is_declared():
    # budget-first is the city workflow: a walled city without meta.budget is unsized by construction
    assert "city_wall_matches_budget" in f(_budget_city())


def test_city_wall_matches_budget_fires_on_over_enclosure():
    # required 300k, enclosed 360k = +20% - the empty-space defect (unjustified open ground)
    assert "city_wall_matches_budget" in f(_budget_city({"required_interior_px2": 300_000.0}))


def test_city_wall_matches_budget_fires_on_under_enclosure():
    # required 400k, enclosed 360k = -10% - the wall cannot hold the program
    assert "city_wall_matches_budget" in f(_budget_city({"required_interior_px2": 400_000.0}))


def test_city_wall_matches_budget_passes_within_tolerance():
    # required 350k, enclosed 360k = +2.9% - inside +8%/-5%
    assert "city_wall_matches_budget" not in f(_budget_city({"required_interior_px2": 350_000.0}))


def test_city_wall_matches_budget_is_scoped_to_walled_cities_only():
    town = {"meta": {"scale": "town", "walled": True}, "wall": [[200, 200], [800, 200], [800, 800], [200, 800]]}
    assert "city_wall_matches_budget" not in f(town)
    unwalled = {"meta": {"scale": "city"}, "wall": [[200, 200], [800, 200], [800, 800], [200, 800]]}
    assert "city_wall_matches_budget" not in f(unwalled)


# ---- doors face open ground + rows max 2-deep (GM feedback 2026-07-18) ----------------------
# The door glyph draws on a building's local +h/2 side (settlement.building), so the door's
# world position/direction derive from x,y,w,h,rot alone. At rot=0 the door faces +y (down).
def _door_city(buildings, scale="city"):
    return {"meta": {"scale": scale, "ftpx": 3}, "wall": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]], "buildings": buildings}


def test_city_house_doors_unblocked_fires_when_a_door_opens_into_a_back_wall():
    # two rot=0 rows 1.5px apart (an eave gap): the TOP row's door (facing down) opens straight
    # into the bottom row's back wall - the defect the GM flagged on the shipped cities
    top = [bldg(300 + i * 41, 300, "laborer", w=40, h=24) for i in range(3)]
    bot = [bldg(300 + i * 41, 300 + 24 + 1.5, "laborer", w=40, h=24) for i in range(3)]
    assert "city_house_doors_unblocked" in f(_door_city(top + bot))


def test_city_house_doors_unblocked_passes_back_to_back_pair_facing_outward():
    # the SAME two rows with the top row rotated 180 (door up, into open ground): a proper
    # back-to-back nagaya pair - both doors open outward
    top = [bldg(300 + i * 41, 300, "laborer", rot=180, w=40, h=24) for i in range(3)]
    bot = [bldg(300 + i * 41, 300 + 24 + 1.5, "laborer", w=40, h=24) for i in range(3)]
    assert "city_house_doors_unblocked" not in f(_door_city(top + bot))


def test_city_house_doors_unblocked_passes_across_a_walkable_roji():
    # facing rows separated by a walkable lane (>= ~10 real ft): doors open onto the roji, fine
    top = [bldg(300 + i * 41, 300, "laborer", w=40, h=24) for i in range(3)]  # door down
    bot = [bldg(300 + i * 41, 300 + 24 + 5.0, "laborer", rot=180, w=40, h=24) for i in range(3)]  # door up
    assert "city_house_doors_unblocked" not in f(_door_city(top + bot))


def test_city_house_doors_unblocked_respects_rotation_axes():
    # a west-facing house (rot=90: door toward -x) with a neighbor tight on its WEST is blocked;
    # the same neighbor on its EAST, facing EAST itself (rot=270), is a proper back-to-back
    # partner - fine (both doors outward on the E-W axis)
    house = bldg(300, 300, "laborer", rot=90, w=40, h=24)
    west = bldg(300 - 24 / 2 - 1.5 - 12, 300, "laborer", rot=90, w=40, h=24)
    east = bldg(300 + 24 / 2 + 1.5 + 12, 300, "laborer", rot=270, w=40, h=24)
    assert "city_house_doors_unblocked" in f(_door_city([house, west]))
    assert "city_house_doors_unblocked" not in f(_door_city([house, east]))


def test_city_house_doors_scope_excludes_villages_and_farmhouses():
    # villages/farmhouses keep the south-facing sunlight canon - out of scope entirely
    top = [bldg(300 + i * 41, 300, "laborer", w=40, h=24) for i in range(3)]
    bot = [bldg(300 + i * 41, 300 + 24 + 1.5, "laborer", w=40, h=24) for i in range(3)]
    assert "city_house_doors_unblocked" not in f({"meta": {"scale": "village"}, "buildings": top + bot})


def test_city_rows_max_two_deep_fires_on_a_three_deep_stack():
    # three eave-gapped rows: the middle row has walls hard against BOTH long faces - trapped
    rows = []
    for r in range(3):
        rows += [bldg(300 + i * 41, 300 + r * (24 + 1.5), "laborer", rot=(180 if r == 0 else 0), w=40, h=24) for i in range(3)]
    assert "city_rows_max_two_deep" in f(_door_city(rows))


def test_city_rows_max_two_deep_passes_pairs_split_by_roji():
    # 2 rows + walkable gap + 2 rows: nobody is trapped (the canonical pair cadence)
    rows = []
    y = 300.0
    for r in range(4):
        rows += [bldg(300 + i * 41, y, "laborer", rot=(180 if r % 2 == 0 else 0), w=40, h=24) for i in range(3)]
        y += 24 + (5.0 if r % 2 else 1.5)
    assert "city_rows_max_two_deep" not in f(_door_city(rows))


def test_city_rows_max_two_deep_ignores_side_by_side_terraces():
    # a long terrace of party-wall units (touching along w) is the doctrine, not a violation
    row = [bldg(300 + i * 40.4, 300, "laborer", w=40, h=24) for i in range(8)]
    assert "city_rows_max_two_deep" not in f(_door_city(row))


# ---- merchant-estate walls clear of water + fire towers (GM feedback 2026-07-19) ------------
def _mest_city(**extra):
    M = {"meta": {"scale": "city"}, "merchant_estates": [{"x": 500, "y": 500, "w": 62.0, "h": 46.0, "gate": [500, 523.0], "gate_dir": "south"}]}
    M.update(extra)
    return M


def test_merchant_estate_wall_fires_on_a_dock_overlap():
    # dock basin footprint under the estate's east wall (the shipped-Nagahara defect)
    assert "merchant_estate_wall_clear_of_water" in f(_mest_city(docks=[{"x": 540, "y": 490, "w": 54, "h": 34, "rot": 0}]))


def test_merchant_estate_wall_fires_on_a_canal_crossing():
    # canal centerline passes through the north wall
    assert "merchant_estate_wall_clear_of_water" in f(_mest_city(canals=[{"poly": [[400, 477], [600, 477]], "w": 12.0}]))


def test_merchant_estate_wall_fires_on_a_pond_and_a_moat():
    assert "merchant_estate_wall_clear_of_water" in f(_mest_city(pond=[469, 500, 20, 14]))  # pond ellipse reaching the west wall
    assert "merchant_estate_wall_clear_of_water" in f(_mest_city(moat=[[531, 400], [531, 600]], moat_width=22.0))  # moat band over the east wall


def test_merchant_estate_wall_passes_with_water_at_a_distance():
    clear = _mest_city(
        docks=[{"x": 620, "y": 490, "w": 54, "h": 34, "rot": 0}],
        canals=[{"poly": [[400, 440], [600, 440]], "w": 12.0}],
        pond=[420, 500, 20, 14],
    )
    assert "merchant_estate_wall_clear_of_water" not in f(clear)


def test_merchant_estate_wall_fires_on_a_fire_tower_and_passes_when_clear():
    # tower footprint straddling the south wall (the shipped-Nagahara defect)
    on_wall = _mest_city(fire_towers=[{"x": 490, "y": 523, "w": 8.7, "h": 8.7, "rot": 0}])
    assert "merchant_estate_wall_clear_of_fire_towers" in f(on_wall)
    clear = _mest_city(fire_towers=[{"x": 490, "y": 545, "w": 8.7, "h": 8.7, "rot": 0}])
    assert "merchant_estate_wall_clear_of_fire_towers" not in f(clear)


def test_merchant_estate_wall_checks_skip_maps_without_estates():
    assert "merchant_estate_wall_clear_of_water" not in f({"meta": {"scale": "city"}, "docks": [{"x": 540, "y": 490, "w": 54, "h": 34, "rot": 0}]})


def test_merchant_estate_wall_fires_on_a_street_crossing():
    # a city street's band running under the estate's west wall (GM 2026-07-19 follow-up)
    hit = _mest_city(town_streets=[{"pts": [[470, 400], [470, 600]], "w": 6.0}])
    assert "merchant_estate_wall_clear_of_streets" in f(hit)
    # the trunk road under the south wall is the same error
    road = _mest_city(road=[[400, 523], [600, 523]], road_width=8.7)
    assert "merchant_estate_wall_clear_of_streets" in f(road)


def test_merchant_estate_wall_passes_streets_at_a_distance():
    clear = _mest_city(town_streets=[{"pts": [[440, 400], [440, 600]], "w": 6.0}], road=[[400, 560], [600, 560]], road_width=8.7)
    assert "merchant_estate_wall_clear_of_streets" not in f(clear)


def test_merchant_estate_fires_when_a_fire_tower_is_enclosed_in_the_court():
    # wall-line clear but the municipal tower trapped INSIDE the private court - same siting error
    inside = _mest_city(fire_towers=[{"x": 500, "y": 505, "w": 8.7, "h": 8.7, "rot": 0}])
    assert "merchant_estate_wall_clear_of_fire_towers" in f(inside)


# ---- to-scale gates/walls + funerary features (GM feedback 2026-07-19) ----------------------
def _scaled_city(**extra):
    M = {"meta": {"scale": "city", "ftpx": 3}}
    M.update(extra)
    return M


def test_compound_gates_to_scale_fires_on_a_wall_wide_opening():
    # a 204 real-ft gate opening (the old fixed +-34px at 3 ft/px) - most of the wall missing
    m = {"x": 500, "y": 500, "w": 90, "h": 60, "rot": 0, "label": "", "gate_dir": "south", "gate": [500, 530], "gate_w": 68.0, "wall_w": 6.0}
    assert "compound_gates_to_scale" in f(_scaled_city(manors=[m]))


def test_compound_gates_to_scale_fires_when_gate_size_unrecorded():
    # a pre-doctrine manifest (no gate_w) cannot prove its gates - regenerate with the engine that records them
    m = {"x": 500, "y": 500, "w": 90, "h": 60, "rot": 0, "label": "", "gate_dir": "south", "gate": [500, 530]}
    assert "compound_gates_to_scale" in f(_scaled_city(manors=[m]))


def test_compound_gates_to_scale_passes_a_real_gate():
    # a 12 real-ft opening (4px at 3 ft/px) in a 2 ft wall drawn at the 2px legibility floor
    m = {"x": 500, "y": 500, "w": 90, "h": 60, "rot": 0, "label": "", "gate_dir": "south", "gate": [500, 530], "gate_w": 4.0, "wall_w": 2.0}
    gov = {"x": 800, "y": 500, "w": 150, "h": 100, "rot": 0, "gate_dir": "west", "gate": [725, 500], "gate_w": 6.0, "wall_w": 2.0}
    assert "compound_gates_to_scale" not in f(_scaled_city(manors=[m], governor_mansion=gov))


def test_cremation_ground_to_scale_fires_oversized_passes_in_band():
    # the old fixed 116x80px glyph at 3 ft/px = 348x240 ft - bigger than the crematory serving metropolitan Edo
    assert "cremation_ground_to_scale" in f(_scaled_city(cremation_grounds=[{"x": 500, "y": 500, "w": 116, "h": 80, "rot": 0}]))
    # a 129x90 ft city ground (43x30px) is inside the 80-160 ft city band
    assert "cremation_ground_to_scale" not in f(_scaled_city(cremation_grounds=[{"x": 500, "y": 500, "w": 43, "h": 30, "rot": 0}]))


def test_ossuary_to_scale_fires_oversized_passes_in_band():
    # the old fixed mound = 276x180 ft - kofun-sized; a pauper bone mound is 10-30 ft. The band top is
    # 32 ft (tightened 2026-07-21): the earlier legibility-sized glyph (9px floor -> 54 real ft at city
    # scale, w=18px) must now FIRE; the true-size glyph (4.5px floor -> 27 ft, w=9px) passes.
    assert "ossuary_to_scale" in f(_scaled_city(ossuaries=[{"x": 500, "y": 500, "w": 92, "h": 60, "rot": 0}]))
    assert "ossuary_to_scale" in f(_scaled_city(ossuaries=[{"x": 500, "y": 500, "w": 18, "h": 12, "rot": 0}]))
    assert "ossuary_to_scale" not in f(_scaled_city(ossuaries=[{"x": 500, "y": 500, "w": 9, "h": 5.6, "rot": 0}]))


def test_burial_grounds_sized_to_population_fires_on_an_oversized_village_ground():
    # a 350-person village drawing 0.64 acre (200x140 ft) - 2-3x the 0.1-0.25 acre band, larger than a town's
    M = {"meta": {"scale": "village", "ftpx": 2}, "cemeteries": [{"x": 500, "y": 500, "w": 100, "h": 70, "rot": 0}]}
    assert "burial_grounds_sized_to_population" in f(M)
    # a 92x64 ft ground (46x32px at 2 ft/px) = ~0.135 acre - in band
    ok = {"meta": {"scale": "village", "ftpx": 2}, "cemeteries": [{"x": 500, "y": 500, "w": 46, "h": 32, "rot": 0}]}
    assert "burial_grounds_sized_to_population" not in f(ok)


def test_burial_grounds_sized_to_population_passes_the_city_split():
    # ~1.8 acres split across common ground + parish yards is inside the 0.4-2.2 acre city band
    M = _scaled_city(cemeteries=[{"x": 500, "y": 500, "w": 90, "h": 64, "rot": 0}, {"x": 800, "y": 500, "w": 44, "h": 32, "rot": 0}, {"x": 900, "y": 700, "w": 44, "h": 32, "rot": 0}])
    assert "burial_grounds_sized_to_population" not in f(M)


def test_compound_gates_to_scale_fires_on_gate_fraction_and_wall_thickness():
    # an in-band 21 ft opening that still swallows over 40% of a tiny compound's wall side
    frac = {"x": 500, "y": 500, "w": 15, "h": 10, "rot": 0, "label": "", "gate_dir": "south", "gate": [500, 505], "gate_w": 7.0, "wall_w": 0.7}
    assert "compound_gates_to_scale" in f(_scaled_city(manors=[frac]))
    # a good gate in a 15 ft rampart-thick wall - a residence wall is ~2 ft, not fortress masonry
    thick = {"x": 500, "y": 500, "w": 90, "h": 60, "rot": 0, "label": "", "gate_dir": "south", "gate": [500, 530], "gate_w": 4.0, "wall_w": 5.0}
    assert "compound_gates_to_scale" in f(_scaled_city(manors=[thick]))


def test_village_cluster_compact_fires_on_a_hollow_cluster():
    """A nucleated village whose houses ring a big HOLLOW hull (an over-wide cluster stranding houses far
    from the fields) must fire; the same houses packed into a compact blob must not. The teeth: it measures
    built COVERAGE of the house convex hull, which `cluster_abuts_fields` (a per-house span allowance) misses.
    Village scale + >=12 houses only."""
    import math

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


def test_convex_hull_degenerate_point_clouds():
    """The hull helper returns <3 unique points as-is (a degenerate, zero-area hull) - the guard the pool
    maps never reach (the compactness check needs >=12 houses) but that must not crash on a stray call."""
    import check_village as cv

    assert cv.convex_hull([]) == []
    assert cv.convex_hull([(1.0, 2.0)]) == [(1.0, 2.0)]
    assert cv.convex_hull([(1.0, 2.0), (3.0, 4.0), (1.0, 2.0)]) == [(1.0, 2.0), (3.0, 4.0)]  # 2 unique
    assert cv.poly_area(cv.convex_hull([(0.0, 0.0), (1.0, 1.0)])) == 0.0


def test_paddy_features_match_archetype_fires_on_wrong_type():
    """Feature 012: an in-field feature on the wrong paddy type must fire (rock on polder; anything on
    dike-pond), and a right-type placement must not. Ponds must also sit on low/wet ground."""
    base = {"meta": {"scale": "village", "field_archetype": "polder_grid"}, "fields": [{"name": "p", "kind": "paddy", "outline": [[0, 0], [500, 0], [500, 500], [0, 500]], "bbox": [0, 0, 500, 500]}]}
    # rock outcrop on a polder (alluvial silt, no bedrock) - wrong
    assert "paddy_features_match_archetype" in f({**base, "field_rocks": [{"x": 100, "y": 100}]})
    # a pond on a polder is fine (borrow-pit) IF on low ground
    good = {**base, "wet_plots": [[100, 100]], "field_ponds": [{"x": 100, "y": 100, "rx": 20, "ry": 14}]}
    assert "paddy_features_match_archetype" not in f(good)
    assert "field_ponds_on_low_ground" not in f(good)
    # a pond NOT on low ground fires the placement check
    offlow = {**base, "wet_plots": [[100, 100]], "field_ponds": [{"x": 400, "y": 400, "rx": 20, "ry": 14}]}
    assert "field_ponds_on_low_ground" in f(offlow)
    # NOTHING is allowed on a dike-pond map (open water is its fabric)
    dp = {**base, "meta": {"scale": "village", "field_archetype": "mulberry_dike_fishpond"}, "field_ponds": [{"x": 100, "y": 100, "rx": 20, "ry": 14}], "wet_plots": [[100, 100]]}
    assert "paddy_features_match_archetype" in f(dp)


def test_paddy_fan_gapless_credits_ditches_and_fires_on_holes():
    """The white-spots gate: a bare strip inside the fan fires; the SAME gap over a recorded
    field ditch is covered ground (drawn water), and must not - that credit is what lets the
    plot tolerance sit at bund scale (6 real ft) without flagging delivery-ditch strips."""
    outline = [[0, 0], [400, 0], [400, 400], [0, 400]]
    plots = [[[0, 0], [180, 0], [180, 400], [0, 400]], [[220, 0], [400, 0], [400, 400], [220, 400]]]
    base = {"meta": {"scale": "village", "ftpx": 2}, "fields": [{"name": "t", "kind": "paddy", "outline": outline, "bbox": [0, 0, 400, 400], "plot_polys": plots}]}
    assert "paddy_fan_gapless" in f(base)
    ditched = {**base, "field_ditches": [{"field": "t", "poly": [[200, -10], [200, 410]], "w": 40, "role": "branch"}]}
    assert "paddy_fan_gapless" not in f(ditched)


def test_channels_join_streams_at_confluence_fires_when_the_intake_starts_short():
    # the SYMMETRIC (frm side) case: an intake declared frm={stream} starting 20px from the
    # centerline never actually taps the water - no confluence at the offtake either
    M = {"meta": {}, "streams": [{"poly": [[400, 100], [400, 900]], "w": 9}], "channels": [{"poly": [[380, 500], [440, 560]], "frm": {"kind": "stream"}, "to": {"kind": "field", "name": "x"}}]}
    assert "channels_join_streams_at_confluence" in f(M)


def test_channels_join_streams_at_confluence_passes_when_the_intake_taps_the_bed():
    M = {"meta": {}, "streams": [{"poly": [[400, 100], [400, 900]], "w": 9}], "channels": [{"poly": [[400, 500], [460, 560]], "frm": {"kind": "stream"}, "to": {"kind": "field", "name": "x"}}]}
    assert "channels_join_streams_at_confluence" not in f(M)


# ---- roads_clear_of_marsh / pond_clear_of_paddies / no_structure_on_paddy (GM, Hoshizora 2026-07) ----
def test_roads_clear_of_marsh_fires_when_the_road_runs_through_a_reed_fringe():
    M = {"meta": {}, "road": [[100, 500], [900, 500]], "marshes": [{"x": 500, "y": 500, "w": 120, "h": 80, "poly": [[440, 460], [560, 460], [560, 540], [440, 540]]}]}
    assert "roads_clear_of_marsh" in f(M)


def test_roads_clear_of_marsh_passes_when_the_marsh_sits_off_the_road():
    M = {"meta": {}, "road": [[100, 500], [900, 500]], "marshes": [{"x": 500, "y": 700, "w": 120, "h": 80, "poly": [[440, 660], [560, 660], [560, 740], [440, 740]]}]}
    assert "roads_clear_of_marsh" not in f(M)


def _paddy_field_rec(name="p1", x0=300, y0=300, x1=700, y1=700):
    ol = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
    return {"name": name, "kind": "paddy", "outline": ol, "bbox": [x0, y0, x1, y1], "vis_bbox": [x0, y0, x1, y1]}


def test_pond_clear_of_paddies_fires_when_the_pond_laps_the_crop():
    M = {"meta": {}, "pond": [320, 320, 80, 60], "fields": [_paddy_field_rec()]}
    assert "pond_clear_of_paddies" in f(M)


def test_pond_clear_of_paddies_passes_when_the_pond_sits_beside_the_crop():
    M = {"meta": {}, "pond": [120, 120, 60, 40], "fields": [_paddy_field_rec()]}
    assert "pond_clear_of_paddies" not in f(M)


def test_no_structure_on_paddy_fires_when_a_farmhouse_sinks_a_corner_into_the_crop():
    # house center 10px outside the paddy edge, 44px wide -> its corner reaches ~12px inside
    M = {"meta": {}, "fields": [_paddy_field_rec()], "houses": [{"x": 290, "y": 500, "w": 44, "h": 29, "kind": "plain", "rot": 0}]}
    assert "no_structure_on_paddy" in f(M)


def test_no_structure_on_paddy_passes_when_the_farmhouse_abuts_the_bund():
    M = {"meta": {}, "fields": [_paddy_field_rec()], "houses": [{"x": 276, "y": 500, "w": 44, "h": 29, "kind": "plain", "rot": 0}]}
    assert "no_structure_on_paddy" not in f(M)


def test_roads_clear_of_marsh_skips_a_degenerate_marsh_poly():
    # a marsh record whose poly is a bare 2-point sliver carries no area to test - skipped, no crash
    M = {"meta": {}, "road": [[100, 500], [900, 500]], "marshes": [{"x": 500, "y": 500, "w": 10, "h": 10, "poly": [[490, 495], [510, 505]]}]}
    assert "roads_clear_of_marsh" not in f(M)


# ---- drain_ends_reach_water (a collector's free end never dangles in bare ground) ----
def _drain_ditch(pts, field="f1"):
    return {"poly": pts, "role": "drain", "field": field, "w": 6, "w_tail": 6}


def test_watercourse_ends_reach_water_fires_when_the_collector_dangles():
    # the collector's east end stops 50px short of the stream, outside the planted bbox
    M = {
        "meta": {},
        "fields": [{"name": "f1", "kind": "paddy", "outline": [[100, 300], [300, 300], [300, 600], [100, 600]], "bbox": [100, 300, 300, 600], "vis_bbox": [100, 300, 300, 600]}],
        "streams": [{"poly": [[430, 100], [430, 900]], "w": 9}],
        "field_ditches": [_drain_ditch([[120, 590], [370, 610]])],
    }
    assert "watercourse_ends_reach_water" in f(M)


def test_watercourse_ends_reach_water_passes_when_a_culvert_carries_it_on():
    M = {
        "meta": {},
        "fields": [{"name": "f1", "kind": "paddy", "outline": [[100, 300], [300, 300], [300, 600], [100, 600]], "bbox": [100, 300, 300, 600], "vis_bbox": [100, 300, 300, 600]}],
        "streams": [{"poly": [[430, 100], [430, 900]], "w": 9}],
        "field_ditches": [_drain_ditch([[120, 590], [370, 610]])],
        "channels": [{"poly": [[370, 610], [430, 628]], "frm": {"kind": "drain"}, "to": {"kind": "stream"}, "w": 2.5}],
    }
    assert "watercourse_ends_reach_water" not in f(M)


def test_city_fan_heads_quilted_moat_exclusion_and_degenerate_segments():
    """Branch coverage for the head-band sampler: a duplicated main vertex (zero-length segment)
    is skipped, and flank samples inside the moat corridor are excluded rather than counted bare
    (the moat legitimately borders a city fan's head where the sluice taps it)."""
    M = {
        "meta": {"scale": "village", "ftpx": 2},
        "moat": [[100, -50], [100, 450]],
        "moat_width": 30,
        "fields": [{"name": "t", "kind": "paddy", "outline": [[0, 0], [400, 0], [400, 400], [0, 400]], "bbox": [0, 0, 400, 400], "plot_polys": [[[60, 0], [400, 0], [400, 400], [60, 400]]]}],
        "field_ditches": [{"field": "t", "poly": [[112, 0], [112, 200], [112, 200], [112, 400]], "w": 6, "role": "main"}],
    }
    f(M)  # execution is the point: west flank samples sit in the moat corridor, the duplicate vertex is skipped


# ---- the town-scale audit batch (GM 2026-07): checks adapted from the city suite ----
def _dw(x, y, kind):
    return {"x": x, "y": y, "w": 30, "h": 20, "kind": kind, "rot": 0}


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


def test_town_monasteries_have_graveyards_fires_when_unserved():
    M = {"meta": {"scale": "town"}, "religious": [{"x": 500, "y": 500, "w": 100, "h": 70, "kind": "monastery"}]}
    assert "town_monasteries_have_graveyards" in f(M)


def test_town_monasteries_have_graveyards_passes_with_precinct_ground_or_opt_out():
    M = {"meta": {"scale": "town"}, "religious": [{"x": 500, "y": 500, "w": 100, "h": 70, "kind": "monastery"}], "cemeteries": [{"x": 560, "y": 420, "w": 80, "h": 60, "rot": 0}]}
    assert "town_monasteries_have_graveyards" not in f(M)
    M2 = {"meta": {"scale": "town"}, "religious": [{"x": 500, "y": 500, "w": 100, "h": 70, "kind": "monastery", "graveyard": False}]}
    assert "town_monasteries_have_graveyards" not in f(M2)


def test_town_has_ossuary_fires_when_missing():
    M = {"meta": {"scale": "town"}, "cremation_grounds": [{"x": 200, "y": 800, "w": 75, "h": 52, "rot": 0}]}
    assert "town_has_ossuary" in f(M)


def test_town_has_ossuary_passes_beside_the_cremation_ground():
    M = {"meta": {"scale": "town"}, "cremation_grounds": [{"x": 200, "y": 800, "w": 75, "h": 52, "rot": 0}], "ossuaries": [{"x": 260, "y": 860, "w": 20, "h": 20, "rot": 0}]}
    assert "town_has_ossuary" not in f(M)


def test_town_samurai_housing_varied_fires_on_uniform_small_houses():
    M = {"meta": {"scale": "town", "population": 100}, "buildings": [_dw(400 + i * 60, 400, "samurai") for i in range(6)]}
    assert "town_samurai_housing_varied" in f(M)


def test_town_samurai_housing_varied_passes_with_a_senior_house():
    M = {"meta": {"scale": "town", "population": 100}, "buildings": [_dw(400, 340, "samurai_large")] + [_dw(400 + i * 60, 400, "samurai") for i in range(5)]}
    assert "town_samurai_housing_varied" not in f(M)


def test_burakumin_quarter_segregated_fires_when_interleaved():
    M = {"meta": {"scale": "town", "population": 100}, "buildings": [_dw(500, 500, "burakumin"), _dw(530, 510, "laborer")]}
    assert "burakumin_quarter_segregated" in f(M)


def test_burakumin_quarter_segregated_passes_with_open_ground_between():
    M = {"meta": {"scale": "town", "population": 100}, "buildings": [_dw(500, 500, "burakumin"), _dw(700, 500, "laborer")]}
    assert "burakumin_quarter_segregated" not in f(M)


def test_village_windbreak_embraces_cluster_fires_on_far_corner_masses_only():
    # a substantial belt exists but stands 400px from the nearest farmhouse - decoration, not a wall
    houses = [{"x": 500 + i * 30, "y": 500, "w": 23, "h": 14, "kind": "plain", "rot": 0} for i in range(12)]
    far = {"x": 900, "y": 100, "w": 120, "h": 60, "role": "windbreak", "clumps": [[880 + j * 6, 100] for j in range(14)]}
    M = {"meta": {"scale": "village", "nucleated": True}, "houses": houses, "village_groves": [far]}
    assert "village_windbreak_embraces_cluster" in f(M)


def test_village_windbreak_embraces_cluster_passes_when_the_belt_nestles():
    houses = [{"x": 500 + i * 30, "y": 500, "w": 23, "h": 14, "kind": "plain", "rot": 0} for i in range(12)]
    belt = {"x": 590, "y": 420, "w": 300, "h": 50, "role": "windbreak", "clumps": [[470 + j * 22, 425] for j in range(14)]}
    M = {"meta": {"scale": "village", "nucleated": True}, "houses": houses, "village_groves": [belt]}
    assert "village_windbreak_embraces_cluster" not in f(M)


def test_geometry_within_canvas_fires_on_a_stray_town_wall_vertex():
    M = {"meta": {"scale": "town", "W": 2000, "H": 1300}, "wall": [[300, 300], [9999999, 300], [700, 700]]}
    assert "geometry_within_canvas" in f(M)


def test_canopy_clear_of_watercourses_fires_on_a_clump_in_the_stream():
    M = {"meta": {}, "streams": [{"poly": [[400, 100], [400, 900]], "w": 9}], "village_groves": [{"x": 400, "y": 500, "w": 60, "h": 40, "role": "copse", "clumps": [[402, 500]]}]}
    assert "canopy_clear_of_watercourses" in f(M)


def test_canopy_clear_of_watercourses_passes_beside_the_bank():
    M = {"meta": {}, "streams": [{"poly": [[400, 100], [400, 900]], "w": 9}], "village_groves": [{"x": 440, "y": 500, "w": 60, "h": 40, "role": "copse", "clumps": [[440, 500]]}]}
    assert "canopy_clear_of_watercourses" not in f(M)


def test_watercourse_ends_reach_water_fires_on_a_dangling_main_canal():
    # a supply canal's free end far past the crop with no join - the hikari-east class
    M = {
        "meta": {},
        "fields": [{"name": "f1", "kind": "paddy", "outline": [[100, 300], [300, 300], [300, 600], [100, 600]], "bbox": [100, 300, 300, 600], "vis_bbox": [100, 300, 300, 600]}],
        "field_ditches": [{"poly": [[120, 310], [450, 340]], "role": "main", "field": "f1", "w": 6, "w_tail": 6}],
    }
    assert "watercourse_ends_reach_water" in f(M)


def test_watercourse_ends_reach_water_allows_a_canal_tail_at_the_crop_edge():
    M = {
        "meta": {},
        "fields": [{"name": "f1", "kind": "paddy", "outline": [[100, 300], [300, 300], [300, 600], [100, 600]], "bbox": [100, 300, 300, 600], "vis_bbox": [100, 300, 300, 600]}],
        "field_ditches": [{"poly": [[120, 310], [314, 330]], "role": "main", "field": "f1", "w": 6, "w_tail": 6}],
    }
    assert "watercourse_ends_reach_water" not in f(M)


def test_town_margins_clothed_fires_on_a_bare_sheet():
    M = {"meta": {"scale": "town", "W": 1000, "H": 1000}}
    assert "town_margins_clothed" in f(M)


def test_town_margins_clothed_passes_when_the_ground_is_worked():
    M = {"meta": {"scale": "town", "W": 1000, "H": 1000}, "commons": [{"x": 500, "y": 500, "w": 1000, "h": 1000, "role": "grazing", "poly": [[-10, -10], [1010, -10], [1010, 1010], [-10, 1010]]}]}
    assert "town_margins_clothed" not in f(M)


# ---- scrub_clear_of_urban_fabric (GM 2026-07-21, Hoshizora): settlement ground is CLEARED - a
# commons/pasture/coppice cover poly that CONTAINS an occupied structure or a wellhead is claiming
# grazed waste where the town stands. Scrub lives on the outskirts only; field barns are exempt
# (a hay barn stands in the grazed ground it serves).
def test_scrub_clear_of_urban_fabric_fires_when_scrub_claims_the_town():
    M = {
        "meta": {"scale": "town"},
        "commons": [{"x": 500, "y": 500, "w": 400, "h": 400, "rot": 0, "role": "grazing", "seq": 1, "poly": [[300, 300], [700, 300], [700, 700], [300, 700]]}],
        "buildings": [bldg(500, 500)],  # a merchant house deep inside the claimed scrub
        "wells": [{"x": 400, "y": 400, "r": 8, "vr": 12}],  # a wellhead inside it too
    }
    assert "scrub_clear_of_urban_fabric" in f(M)


def test_scrub_clear_of_urban_fabric_fires_on_a_farmhouse_in_the_scrub():
    # the check is order-blind and covers farmhouses: a house drawn after the cover fires too
    # (town scale - at village/hamlet scale dispersed farms legitimately stand on the marginal
    # scrub, so the check is scoped out there and only the engine halo applies)
    M = {
        "meta": {"scale": "town"},
        "commons": [{"x": 500, "y": 500, "w": 400, "h": 400, "rot": 0, "role": "pasture", "seq": 1, "poly": [[300, 300], [700, 300], [700, 700], [300, 700]]}],
        "houses": [{"x": 450, "y": 520, "w": 44, "h": 29, "rot": 0, "kind": "plain"}],
    }
    assert "scrub_clear_of_urban_fabric" in f(M)


def test_scrub_clear_of_urban_fabric_passes_when_scrub_hugs_the_outskirts():
    M = {
        "meta": {"scale": "town"},
        "commons": [
            {"x": 500, "y": 500, "w": 400, "h": 400, "rot": 0, "role": "grazing", "seq": 1, "poly": [[300, 300], [700, 300], [700, 700], [300, 700]]},
            {"x": 0, "y": 0, "w": 0, "h": 0, "rot": 0, "role": "grazing", "seq": 2, "poly": [[0, 0], [1, 0]]},  # degenerate record - skipped, never a crash
        ],
        "buildings": [bldg(500, 500, kind="barn"), bldg(900, 900)],  # the hay barn IN the grazing is legal; the merchant stands outside
        "wells": [{"x": 800, "y": 300, "r": 8, "vr": 12}],  # outside the poly
    }
    assert "scrub_clear_of_urban_fabric" not in f(M)
