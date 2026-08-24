"""Split from test_checks.py by feature 025 - see tests/check_village/CLAUDE.md for the index."""

from tests.check_village._builders import (
    _bridge_map,
    _cap_water,
    _channel,
    _confluence,
    _drain_ditch,
    _farmhouse,
    _field,
    _footbridge_map,
    _iw_manifest,
    _mj_map,
    _moat_city,
    _moat_map,
    _paddy_f,
    _sink_channel,
    _water_map,
    bldg,
    f,
)


def test_channels_flow_downhill_fires_when_channel_runs_uphill():
    # downhill is south (+y); a channel whose field-end is NORTH of its stream-tap runs uphill
    M = {"meta": {"downhill": "south"}, "channels": [_channel([200, 500], [260, 320])]}
    assert "channels_flow_downhill" in f(M)


def test_channels_flow_downhill_passes_when_channel_runs_downhill():
    M = {"meta": {"downhill": "south"}, "channels": [_channel([200, 320], [260, 500])]}
    assert "channels_flow_downhill" not in f(M)


def test_channels_join_streams_at_confluence_fires_when_the_mouth_dies_short():
    # the stream runs N-S at x=400 (w 9 -> half-width 4.5); a culvert ending 20px from the
    # centerline passes the 30px anchor but never reaches the water - no confluence
    M = {"meta": {}, "streams": [{"poly": [[400, 100], [400, 900]], "w": 9}], "channels": [_sink_channel([380, 500])]}
    assert "channels_join_streams_at_confluence" in f(M)


def test_channels_join_streams_at_confluence_passes_when_the_mouth_reaches_the_bed():
    M = {"meta": {}, "streams": [{"poly": [[400, 100], [400, 900]], "w": 9}], "channels": [_sink_channel([400, 500])]}
    assert "channels_join_streams_at_confluence" not in f(M)


# ---- lanes: houses must FRONT a lane (not sit on it); a CONNECTOR must run off the edge -------
def test_houses_clear_of_lanes_fires_when_a_house_sits_on_the_tread():
    M = {"lanes": [{"pts": [[100, 500], [900, 500]], "worn": True, "w": 6, "connector": False}], "houses": [{"x": 500, "y": 500, "w": 23, "h": 14, "rot": 0, "kind": "plain"}]}  # centered ON the lane
    assert "houses_clear_of_lanes" in f(M)


def test_houses_clear_of_lanes_reads_the_RAKE_the_house_is_drawn_at():
    """A farmhouse is drawn raked (`_house_rot`, +/-5 deg), and this check built its own
    axis-aligned corner list instead of using `rect_corners`, which has read `rot` all along
    (feature 121). So the gate measured a square-on rect while the map drew a raked one - and it
    disagreed with the PLACER, which is how a seat the placer had cleared came back from the gate
    as a house standing on a lane.

    The seat below is clear of the tread square-on and ON it once raked, so the axis-aligned
    version of this check cannot pass this test."""
    lane = {"pts": [[100, 500], [900, 500]], "worn": True, "w": 6, "connector": False}
    house = {"x": 500, "y": 521.5, "w": 62, "h": 30, "kind": "plain"}  # a LONG minka (the 1.35x length jitter)
    assert "houses_clear_of_lanes" not in f({"lanes": [lane], "houses": [{**house, "rot": 0}]}), "square-on it clears, so the rake is the only thing under test"
    assert "houses_clear_of_lanes" in f({"lanes": [lane], "houses": [{**house, "rot": -5}]}), "RAKED, the same house overhangs the tread and the gate must say so"


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


def test_pond_fed_from_edge_fires_when_the_feeder_starts_mid_map():
    # a brook whose pond end is in the pond but whose FAR end sits mid-map (water out of nowhere)
    M = {"pond": [400, 300, 150, 90], "streams": [{"poly": [[600, 600], [420, 320]], "frm": {"kind": "offmap"}, "to": {"kind": "pond"}, "w": 9}]}
    assert "pond_fed_from_edge" in f(M)


def test_pond_fed_from_edge_passes_when_the_feeder_comes_from_the_edge():
    M = {"pond": [400, 300, 150, 90], "streams": [{"poly": [[10, 10], [420, 320]], "frm": {"kind": "offmap"}, "to": {"kind": "pond"}, "w": 9}]}
    assert "pond_fed_from_edge" not in f(M)


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


def test_moat_channels_flow_with_current_fires_when_against():
    # moat flows south; this channel taps the moat at (350,300) and runs NORTH to a field at (350,150)
    # - the field is upstream of the tap, so water would run field->moat (backwards)
    assert "moat_channels_flow_with_current" in f(_moat_city([[350, 300], [350, 150]]))


def test_moat_channels_flow_with_current_passes_when_downstream():
    # same moat, but the channel runs SOUTH (with the current) to a field below its tap
    assert "moat_channels_flow_with_current" not in f(_moat_city([[350, 700], [350, 850]]))


def test_bridges_span_their_water_fires_on_a_short_deck():
    """A deck must FULLY cross its water - both ends past the bank onto dry ground (GM
    2026-08-09: the towpath's hand-placed plank stopped mid-channel and read as a bridge
    hanging over the water). roads_bridge_water is satisfied by ANY deck within 40px, so a
    stub deck passes it - this rule is what catches the stub."""
    M = _bridge_map([{"x": 500, "y": 500, "rot": 0, "span": 4, "w": 26}])  # a 4px stub deck on a 9px stream
    assert "bridges_span_their_water" in f(M)
    M["bridges"] = [{"x": 500, "y": 500, "rot": 0, "span": 37, "w": 26}]
    assert "bridges_span_their_water" not in f(M)


def test_bridges_span_their_water_fires_on_an_oblique_underspan():
    """An OBLIQUE crossing needs a longer deck - and the verdict is on the deck's CORNERS (GM
    2026-08-09): a span whose centerline ends cleared the banks still left a corner sitting AT
    the water's edge, structurally impossible for an abutment that must stand back from scour.
    A carried deck's corners need >= 6 ft of dry landing (the drawn LANDING_FT is 10)."""
    M = _bridge_map([{"x": 500, "y": 500, "rot": 45, "span": 8, "w": 6}])
    assert "bridges_span_their_water" in f(M)
    M["bridges"] = [{"x": 500, "y": 500, "rot": 45, "span": 20, "w": 6}]  # ends clear, corners do not
    assert "bridges_span_their_water" in f(M)
    M["bridges"] = [{"x": 500, "y": 500, "rot": 45, "span": 38, "w": 6}]
    assert "bridges_span_their_water" not in f(M)


def test_footplanks_keep_their_short_abutment_but_a_flush_plank_fires():
    """A standalone footplank's SHORT abutment stands (GM 2026-07-22: PLANK_ABUTMENT, ~3px of
    bank rest per side) - so its floor is 2 ft, not the carried deck's 6 - but a plank whose
    corner sits at the water's edge still fires."""
    M = _bridge_map([{"x": 500, "y": 500, "rot": 0, "span": 15, "w": 2, "foot": True}])
    assert "bridges_span_their_water" not in f(M)
    M["bridges"] = [{"x": 500, "y": 500, "rot": 0, "span": 10, "w": 2, "foot": True}]
    assert "bridges_span_their_water" in f(M)


def test_long_ditches_have_a_footbridge_fires_when_a_long_ditch_is_planless():
    assert "long_ditches_have_a_footbridge" in f(_footbridge_map([]))
    assert "long_ditches_have_a_footbridge" not in f(_footbridge_map([{"x": 450, "y": 200, "rot": 90, "span": 20, "w": 5}]))


def test_long_ditches_footbridge_check_is_opt_in():
    # without meta.field_footbridges the check does not run at all (a planless ditch is fine)
    assert "long_ditches_have_a_footbridge" not in f(_footbridge_map([], footbridges=False))


def test_long_ditches_footbridge_exempts_a_margin_ditch():
    # a long ditch with cultivation on only ONE side (marsh/scrub the other) is not plankable -> no plank needed
    M = _footbridge_map([])
    M["fields"] = [{"name": "p", "kind": "paddy", "outline": [[50, 90], [850, 90], [850, 190], [50, 190]], "bbox": [50, 90, 850, 190]}]  # entirely N of the y=200 ditch
    assert "long_ditches_have_a_footbridge" not in f(M)


# ---- footbridges_reach_useful_ground: a standalone plank must land on field/village/dike both banks ----
def test_footbridges_reach_useful_ground_fires_when_a_plank_crosses_to_nothing():
    # a foot-tagged plank on the field's EDGE ditch: paddy on the N bank, bare ground (marsh/scrub) on the S
    M = _footbridge_map([{"x": 450, "y": 200, "rot": 90, "span": 11, "w": 2, "foot": True}])
    M["fields"] = [{"name": "p", "kind": "paddy", "outline": [[50, 90], [850, 90], [850, 190], [50, 190]], "bbox": [50, 90, 850, 190]}]  # only N of the ditch
    assert "footbridges_reach_useful_ground" in f(M)


def test_footbridges_reach_useful_ground_passes_when_a_plank_reaches_field_both_banks():
    # the field straddles the ditch -> both banks cultivated -> the plank is useful
    assert "footbridges_reach_useful_ground" not in f(_footbridge_map([{"x": 450, "y": 200, "rot": 90, "span": 11, "w": 2, "foot": True}]))


def test_footbridges_reach_useful_ground_exempts_untagged_lane_bridges():
    # a lane-carried crossing (no 'foot' tag) is exempt even with nothing on the far bank - a path leads to it
    M = _footbridge_map([{"x": 450, "y": 200, "rot": 90, "span": 11, "w": 5}])
    M["fields"] = [{"name": "p", "kind": "paddy", "outline": [[50, 90], [850, 90], [850, 190], [50, 190]], "bbox": [50, 90, 850, 190]}]
    assert "footbridges_reach_useful_ground" not in f(M)


def test_bridges_clear_of_houses_fires_when_a_plank_sits_on_a_farmhouse():
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(400, 300)], "bridges": [{"x": 400, "y": 300, "rot": 0, "span": 24, "w": 6}]}  # a plank ON the house
    assert "bridges_clear_of_houses" in f(M)


def test_bridges_clear_of_houses_passes_when_a_plank_is_off_the_houses():
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(400, 300)], "bridges": [{"x": 600, "y": 300, "rot": 0, "span": 24, "w": 6}]}  # a plank well clear of the house
    assert "bridges_clear_of_houses" not in f(M)


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


def test_channels_join_streams_at_confluence_fires_when_the_intake_starts_short():
    # the SYMMETRIC (frm side) case: an intake declared frm={stream} starting 20px from the
    # centerline never actually taps the water - no confluence at the offtake either
    M = {"meta": {}, "streams": [{"poly": [[400, 100], [400, 900]], "w": 9}], "channels": [{"poly": [[380, 500], [440, 560]], "frm": {"kind": "stream"}, "to": {"kind": "field", "name": "x"}}]}
    assert "channels_join_streams_at_confluence" in f(M)


def test_channels_join_streams_at_confluence_passes_when_the_intake_taps_the_bed():
    M = {"meta": {}, "streams": [{"poly": [[400, 100], [400, 900]], "w": 9}], "channels": [{"poly": [[400, 500], [460, 560]], "frm": {"kind": "stream"}, "to": {"kind": "field", "name": "x"}}]}
    assert "channels_join_streams_at_confluence" not in f(M)


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


# ---- near_ring_cultivated_fraction (feature 013): a well-sited town/city sits in packed farmland,
# so the flat, uncommitted near-ring ground must be CULTIVATED (paddy/veg fields, dry plots, gardens)
# to the near_ring_density tier's floor. Bare scrub on that ground counts against; the sub-100%
# threshold leaves room for the genuine fallow/margin scrub. Town + city only.
def test_near_ring_cultivated_fraction_fires_on_a_sparse_town():
    M = {"meta": {"scale": "town", "W": 1000, "H": 1000}}  # bare sheet, 0% cultivated
    assert "near_ring_cultivated_fraction" in f(M)


def test_near_ring_cultivated_fraction_passes_when_the_near_ring_is_cropped():
    # dry cropland over ~62% of the flat frame clears the dense town floor (0.28, combs-only doctrine)
    M = {"meta": {"scale": "town", "W": 1000, "H": 1000}, "dry_plots": [{"poly": [[0, 0], [1000, 0], [1000, 620], [0, 620]], "crop": "soy", "theta": 0.0}]}
    assert "near_ring_cultivated_fraction" not in f(M)


def test_near_ring_cultivated_fraction_thin_tier_tolerates_a_scrubbier_ring():
    # ~26% cultivated: fires when declared 'dense' (floor 0.28), passes when declared 'thin' (floor 0.12)
    cover = [{"poly": [[0, 0], [1000, 0], [1000, 260], [0, 260]], "crop": "soy", "theta": 0.0}]
    dense = {"meta": {"scale": "town", "W": 1000, "H": 1000}, "dry_plots": cover}
    thin = {"meta": {"scale": "town", "W": 1000, "H": 1000, "near_ring_density": "thin"}, "dry_plots": cover}
    assert "near_ring_cultivated_fraction" in f(dense)
    assert "near_ring_cultivated_fraction" not in f(thin)


def test_near_ring_cultivated_fraction_ignores_village_and_hamlet_sheets():
    for sc in ("village", "hamlet"):
        M = {"meta": {"scale": sc, "W": 1000, "H": 1000}}  # bare, but the near-ring rule is town/city only
        assert "near_ring_cultivated_fraction" not in f(M)


def test_near_ring_paddy_dominant_fires_when_dry_grain_dominates():
    # a big dry-grain field, only a sliver of paddy -> dry dominates -> fires
    M = {"meta": {"scale": "town", "W": 1000, "H": 1000}, "fields": [_paddy_f(0, 0, 120, 120)], "dry_plots": [{"poly": [[0, 300], [1000, 300], [1000, 900], [0, 900]], "crop": "soy", "theta": 0.0}]}
    assert "near_ring_paddy_dominant" in f(M)


def test_near_ring_paddy_dominant_passes_when_paddy_dominates():
    M = {"meta": {"scale": "town", "W": 1000, "H": 1000}, "fields": [_paddy_f(0, 0, 1000, 700)], "dry_plots": [{"poly": [[0, 800], [200, 800], [200, 900], [0, 900]], "crop": "soy", "theta": 0.0}]}
    assert "near_ring_paddy_dominant" not in f(M)


def test_near_ring_paddy_dominant_ignores_gardens_as_dry_grain():
    # a large GARDEN dry area is NOT dry-grain; a modest paddy still dominates the grain (there is none)
    M = {"meta": {"scale": "town", "W": 1000, "H": 1000}, "fields": [_paddy_f(0, 0, 300, 300)], "dry_plots": [{"poly": [[0, 400], [1000, 400], [1000, 900], [0, 900]], "crop": "garden", "theta": 0.0}]}
    assert "near_ring_paddy_dominant" not in f(M)


def test_near_ring_paddy_dominant_excludes_a_paddy_combs_own_dry_hem():
    # a paddy field's dry HEM (a dry plot within the paddy field's envelope) is part of the paddy system,
    # not competing dry grain: a big paddy field whose only dry plot sits inside it stays paddy-dominant
    M = {
        "meta": {"scale": "town", "W": 1000, "H": 1000},
        "fields": [{"name": "comb", "kind": "paddy", "outline": [[0, 0], [900, 0], [900, 700], [0, 700]], "bbox": [0, 0, 900, 700]}],
        "dry_plots": [{"poly": [[100, 100], [800, 100], [800, 300], [100, 300]], "crop": "barley", "theta": 0.0}],  # a hem INSIDE the paddy bbox
    }
    assert "near_ring_paddy_dominant" not in f(M)


def test_near_ring_paddy_dominant_ignores_village_and_hamlet_sheets():
    for sc in ("village", "hamlet"):
        M = {"meta": {"scale": sc, "W": 1000, "H": 1000}, "dry_plots": [{"poly": [[0, 300], [1000, 300], [1000, 900], [0, 900]], "crop": "soy", "theta": 0.0}]}
        assert "near_ring_paddy_dominant" not in f(M)


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


# ---- channels_join_water_not_cross (GM 2026-07-23): a channel/ditch never runs straight ACROSS the
# moat/river centerline - water joins water at a confluence (the mouth ends at the bank; the recorded
# topology ends ON the centerline, so first/last-segment touches at the crossed water segment are the
# sanctioned join).
def test_channels_join_water_not_cross_fires_on_a_channel_through_the_moat():
    M = {
        "meta": {"scale": "town", "W": 500, "H": 500},
        "moat": [[50, 100], [450, 100], [450, 110]],
        "channels": [{"poly": [[100, 30], [100, 180]], "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}, "w": 2.5}],
    }
    assert "channels_join_water_not_cross" in f(M)


def test_channels_join_water_not_cross_exempts_a_tap_ending_on_the_centerline():
    M = {
        "meta": {"scale": "town", "W": 500, "H": 500},
        "moat": [[50, 100], [450, 100], [450, 110]],
        "channels": [{"poly": [[100, 100], [100, 180]], "frm": {"kind": "moat"}, "to": {"kind": "offmap"}, "w": 2.5}],
    }
    assert "channels_join_water_not_cross" not in f(M)


def test_channels_join_water_not_cross_fires_on_a_ditch_through_the_river():
    M = {
        "meta": {"scale": "town", "W": 500, "H": 500},
        "river": {"pts": [[200, 20], [200, 480]], "w": 40},
        "field_ditches": [{"poly": [[80, 300], [350, 300]], "role": "main", "field": "f1", "w": 4, "w_tail": 4}],
    }
    assert "channels_join_water_not_cross" in f(M)


# ---- channel_gates_at_water_junctions (GM 2026-07-23): a moat/river tap hands off to the comb canal
# (and a field drain to its outfall culvert) through a visible sluice gate at the junction.
def test_channel_gates_at_water_junctions_fires_on_a_gateless_tap():
    M = {
        "meta": {"scale": "town", "W": 500, "H": 500},
        "moat": [[50, 100], [450, 100], [450, 110]],
        "channels": [{"poly": [[100, 100], [100, 140], [110, 200]], "frm": {"kind": "moat"}, "to": {"kind": "offmap"}, "w": 2.5}],
    }
    M["channels"][0]["to"] = {"kind": "field", "name": "f1"}
    M["fields"] = [{"name": "f1", "kind": "paddy", "outline": [[60, 160], [160, 160], [160, 260], [60, 260]], "bbox": [60, 160, 160, 260]}]
    assert "channel_gates_at_water_junctions" in f(M)


def test_channel_gates_at_water_junctions_passes_with_a_gate_at_the_sluice():
    M = {
        "meta": {"scale": "town", "W": 500, "H": 500},
        "moat": [[50, 100], [450, 100], [450, 110]],
        "channels": [{"poly": [[100, 100], [100, 140], [110, 200]], "frm": {"kind": "moat"}, "to": {"kind": "field", "name": "f1"}, "w": 2.5}],
        "fields": [{"name": "f1", "kind": "paddy", "outline": [[60, 160], [160, 160], [160, 260], [60, 260]], "bbox": [60, 160, 160, 260]}],
        "sluice_gates": [{"x": 100, "y": 141, "rot": 90, "z": 1}],
    }
    assert "channel_gates_at_water_junctions" not in f(M)


def test_channel_gates_at_water_junctions_fires_on_a_gateless_drain_culvert():
    M = {
        "meta": {"scale": "town", "W": 500, "H": 500},
        "moat": [[50, 100], [450, 100], [450, 110]],
        "channels": [{"poly": [[200, 300], [200, 105]], "frm": {"kind": "drain"}, "to": {"kind": "moat"}, "w": 3.2, "drawn": True}],
    }
    assert "channel_gates_at_water_junctions" in f(M)


def test_channel_gates_at_water_junctions_exempts_an_underground_conduit():
    # an UNDROWN drain record is an implied underground conduit (Tango's in-wall nw1 drain drops
    # beneath the ring road, rampart and moat) - no visible seam, no gate demanded
    M = {
        "meta": {"scale": "town", "W": 500, "H": 500},
        "moat": [[50, 100], [450, 100], [450, 110]],
        "channels": [{"poly": [[200, 300], [200, 105]], "frm": {"kind": "drain"}, "to": {"kind": "moat"}, "w": 2.5}],
    }
    assert "channel_gates_at_water_junctions" not in f(M)


# ---- pond_fill_covers_channel_mouths: the Tango in-wall tank (GM 2026-07-23) ----------------
# The comb head-race joined the pond from the LATE water block, whose beds draw after the whole
# shared block - so the pond fill could not cover the mouth's inside-the-rim overshoot and the
# channel's round end-cap rode ON TOP of the open water, reading as an intersection rather than
# a join. The check verifies the RECORDED z-order: pond fill above every joining bed.
def test_pond_fill_covers_channel_mouths_fires_when_a_joining_bed_draws_over_the_fill():
    # bedz values are block-relative offsets, so the LATE joining bed's raw number (8) is SMALLER
    # than the early fill's (9) even though it draws after - the (late, bedz) pair carries the
    # real order, and a raw-z comparison would falsely pass exactly this broken-engine shape
    M = {
        "meta": {"scale": "village"},
        "pond": [500, 500, 40, 25],
        "pond_layer": {"bedz": 9, "sheenz": 10, "late": False},
        "drawn_channels": [{"pts": [[462.5, 505.0], [380.0, 560.0]], "late": True, "bedz": 8}],  # mouth at the rim, bed ABOVE the fill
    }
    assert "pond_fill_covers_channel_mouths" in f(M)


def test_pond_fill_covers_channel_mouths_fires_when_the_layering_is_unrecorded():
    # the pre-fix Tango shape (frozen in pool/regressions/): a comb ditch joins the pond but the
    # manifest carries no pond_layer / drawn_channels records - the uncovered cap, undetectable by
    # z-comparison, so the ABSENCE of the records must itself fire
    M = {
        "meta": {"scale": "village"},
        "pond": [500, 500, 40, 25],
        "field_ditches": [{"poly": [[462.5, 505.0], [380.0, 560.0]], "role": "main", "field": "f1", "w": 5.0}],
    }
    assert "pond_fill_covers_channel_mouths" in f(M)


def test_pond_fill_covers_channel_mouths_fires_when_a_stroke_crosses_the_open_water():
    # mouths, not crossings (the pond sibling of channels_join_water_not_cross): a drawn stroke
    # whose INTERIOR vertex sits deep inside the pond runs straight through the open water
    M = {
        "meta": {"scale": "village"},
        "pond": [500, 500, 40, 25],
        "pond_layer": {"bedz": 300, "sheenz": 301},
        "drawn_channels": [{"pts": [[430.0, 460.0], [500.0, 500.0], [570.0, 540.0]], "late": False, "bedz": 100}],
    }
    assert "pond_fill_covers_channel_mouths" in f(M)


def test_pond_fill_covers_channel_mouths_passes_when_the_fill_covers_the_mouth():
    # the fixed engine shape: a late channel joins, so the fill RELOCATED to the late block
    # (late: True) and draws above the joining bed within it
    M = {
        "meta": {"scale": "village"},
        "pond": [500, 500, 40, 25],
        "pond_layer": {"bedz": 300, "sheenz": 301, "late": True},
        "drawn_channels": [{"pts": [[462.5, 505.0], [380.0, 560.0]], "late": True, "bedz": 100}],
        "field_ditches": [{"poly": [[462.5, 505.0], [380.0, 560.0]], "role": "main", "field": "f1", "w": 5.0}],
    }
    assert "pond_fill_covers_channel_mouths" not in f(M)


def test_inwall_drains_gated_at_cutoff_fires_when_the_cutoff_is_ungated():
    M = _iw_manifest([300, 300], stroke=[[500, 300], [300, 300]])  # ditch reaches the drop, road clear, NO gate
    assert "inwall_drains_gated_at_cutoff" in f(M)


def test_inwall_drains_gated_at_cutoff_fires_when_the_ditch_rides_the_ring_road():
    # cut point 5px off the ring centerline (< half width 4 + 4) and the stroke crosses it
    M = _iw_manifest([300, 95], stroke=[[300, 300], [300, 95]], gates=((300, 95),))
    assert "inwall_drains_gated_at_cutoff" in f(M)


def test_inwall_drains_gated_at_cutoff_fires_when_no_ditch_reaches_the_drop():
    M = _iw_manifest([300, 300], stroke=[[500, 300], [400, 300]], gates=((300, 300),))  # nearest stroke end 100px away
    assert "inwall_drains_gated_at_cutoff" in f(M)


def test_inwall_drains_gated_at_cutoff_passes_when_gated_and_clear():
    M = _iw_manifest([300, 300], stroke=[[500, 300], [300, 300]], gates=((302, 301),))
    assert "inwall_drains_gated_at_cutoff" not in f(M)


def test_inwall_drains_gated_at_cutoff_exempts_drawn_culverts_and_outside_conduits():
    # a DRAWN drain culvert is the outside-the-wall kind (gated at the drain handoff by
    # channel_gates_at_water_junctions), and an undrawn conduit STARTING outside the wall has
    # no rampart to pass under - neither is this check's business
    assert "inwall_drains_gated_at_cutoff" not in f(_iw_manifest([300, 300], drawn=True))
    outside = _iw_manifest([980, 500])
    assert "inwall_drains_gated_at_cutoff" not in f(outside)


# ---- one direction model, not three (GM 2026-07-25) -----------------------------------------
def test_channels_flow_downhill_runs_from_down_deg_without_the_legacy_downhill_tag():
    # it used to be gated on meta(downhill), which only 2 of 17 maps declared - so 15 maps, both
    # cities among them, skipped it entirely behind a green gate
    M = {
        "meta": {"scale": "town", "walled": False, "ftpx": 1, "W": 1200, "H": 1200, "down_deg": 90},
        "fields": [{"name": "f1", "kind": "paddy", "outline": [[100, 100], [500, 100], [500, 500], [100, 500]], "bbox": [100, 100, 500, 500], "vis_bbox": [100, 100, 500, 500]}],
        "channels": [{"poly": [[300, 600], [300, 300]], "frm": {"kind": "stream"}, "to": {"kind": "field", "name": "f1"}, "w": 2.5}],  # runs NORTH, i.e. uphill
    }
    assert "channels_flow_downhill" in f(M)


def test_channels_flow_downhill_judges_a_channel_by_the_FIELD_it_feeds():
    # same channel, but this field's own fall is north - so the channel now runs downhill INTO it.
    # A settlement ringed by farmland drains several ways, so the target field is the authority.
    M = {
        "meta": {"scale": "town", "walled": False, "ftpx": 1, "W": 1200, "H": 1200, "down_deg": 90},
        "fields": [{"name": "f1", "kind": "paddy", "outline": [[100, 100], [500, 100], [500, 500], [100, 500]], "bbox": [100, 100, 500, 500], "vis_bbox": [100, 100, 500, 500], "down_deg": 270}],
        "channels": [{"poly": [[300, 600], [300, 300]], "frm": {"kind": "stream"}, "to": {"kind": "field", "name": "f1"}, "w": 2.5}],
    }
    assert "channels_flow_downhill" not in f(M)


def test_moat_channels_flow_with_current_takes_the_current_from_moat_flow():
    # a southward-heading offtake agrees with an inlet-NW/outlet-SE circulation
    assert "moat_channels_flow_with_current" not in f(_moat_map())


def test_moat_channels_flow_with_current_fires_on_an_offtake_back_upstream():
    # the same moat, but the field lies NORTH of the tap - water would run from the field INTO the moat
    M = _moat_map(
        fields=[{"name": "fn", "kind": "paddy", "outline": [[300, 60], [600, 60], [600, 200], [300, 200]], "bbox": [300, 60, 600, 200], "vis_bbox": [300, 60, 600, 200]}],
        channels=[{"poly": [[500, 300], [480, 100]], "frm": {"kind": "moat"}, "to": {"kind": "field", "name": "fn"}, "w": 2.5}],
    )
    assert "moat_channels_flow_with_current" in f(M)


def test_moat_junction_fires_on_a_SQUARE_offtake():
    # a tap leaving at 90 deg is the defect canal practice warns about ("30 or 45 instead of 90") -
    # it sheds sediment into its own mouth and says nothing about which way the water runs
    M = _mj_map({"poly": [[400, 500], [340, 500], [250, 850]], "frm": {"kind": "moat"}, "to": {"kind": "field", "name": "f1"}, "w": 2.5})
    assert "moat_junctions_swept_with_the_current" in f(M)


def test_moat_junction_passes_an_offtake_swept_downstream():
    # same tap, but the throat leaves angled WITH the current (the west arc runs south here)
    M = _mj_map({"poly": [[400, 450], [340, 520], [250, 850]], "frm": {"kind": "moat"}, "to": {"kind": "field", "name": "f1"}, "w": 2.5})
    assert "moat_junctions_swept_with_the_current" not in f(M)


def test_moat_junction_fires_on_a_drain_arriving_against_the_current():
    # Tango's fn2: the culvert doubled back to meet the rim pointing upstream
    M = _mj_map({"poly": [[250, 850], [340, 700], [400, 620]], "frm": {"kind": "drain", "name": "f1"}, "to": {"kind": "moat"}, "w": 2.5})
    assert "moat_junctions_swept_with_the_current" in f(M)


def test_moat_junction_skips_degenerate_channels():
    # a one-point poly has no heading, and a zero-length first step has no direction: both are
    # skipped rather than crashing or being scored
    for poly in ([[400, 500]], [[400, 500], [400, 500]]):
        M = _mj_map({"poly": poly, "frm": {"kind": "moat"}, "to": {"kind": "field", "name": "f1"}, "w": 2.5})
        assert "moat_junctions_swept_with_the_current" not in f(M)


def test_stream_runs_off_edge_accepts_a_trunk_river_tap():
    """A sluiced moat feeder taps the trunk river (feature 020's capital) - the river is itself
    edge-sourced, so a stream rooted on it inherits a real source the way an edge end does."""
    M = _cap_water()
    M["moat"] = [[900, 100], [900, 900]]
    M["streams"].append({"poly": [[1180, 300], [1000, 350], [905, 400]], "frm": {"kind": "river"}, "to": {"kind": "moat"}, "w": 16})
    assert "stream_runs_off_edge[1]" not in f(M)


def test_bridges_seat_on_water_fires_on_a_dry_deck():
    """A deck seated on NO water at all - the floating towpath plank (settlement-review
    2026-08-10): the drain's re-route moved the ford and the deck kept its old seat, and
    bridges_span_their_water silently skipped it (no crossed water -> continue), so a plank
    lying on bare bank shipped green. A check that never runs looks exactly like a check that
    passes."""
    M = _bridge_map([{"x": 500, "y": 500, "rot": 0, "span": 37, "w": 26}])
    assert "bridges_seat_on_water" not in f(M)  # this deck IS on its stream
    M["bridges"] = [{"x": 800, "y": 200, "rot": 0, "span": 37, "w": 26, "foot": True}]  # far from every water
    assert "bridges_seat_on_water" in f(M)


def test_towpath_hugs_the_bank():
    """GM 2026-08-10: the river was re-routed and the towpath kept its old seat, running 100+px
    inland. A towpath is the hauling line's bank walk - every vertex stays on the bank."""
    assert "towpath_hugs_the_bank" not in f(_water_map(towpaths=[{"pts": [[100, 522], [900, 524]], "w": 3}]))
    assert "towpath_hugs_the_bank" in f(_water_map(towpaths=[{"pts": [[100, 522], [900, 640]], "w": 3}]))


def test_sluice_gates_on_water():
    """A sluice regulates a flow it must stand in - one stood 245px from any water after the
    re-route (GM 2026-08-10)."""
    assert "sluice_gates_on_water" not in f(_water_map(sluice_gates=[{"x": 500, "y": 508, "rot": 0}]))
    assert "sluice_gates_on_water" in f(_water_map(sluice_gates=[{"x": 500, "y": 700, "rot": 0}]))


def test_aqueduct_taps_water_lands_dry():
    """The intake must touch its river; the terminus (settling basin) must land clear of the
    moat - the capital's ended IN the moat (GM 2026-08-10)."""
    ok = _water_map(aqueducts=[{"poly": [[500, 512], [700, 300]], "w": 3}])
    assert "aqueduct_taps_water_lands_dry" not in f(ok)
    dry_intake = _water_map(aqueducts=[{"poly": [[500, 460], [700, 300]], "w": 3}])
    assert "aqueduct_taps_water_lands_dry" in f(dry_intake)
    in_moat = _water_map(aqueducts=[{"poly": [[500, 512], [700, 255]], "w": 3}], moat=[[600, 250], [800, 250], [800, 350], [600, 350]], moat_width=22)  # terminus lands in the moat channel itself
    assert "aqueduct_taps_water_lands_dry" in f(in_moat)


def test_tanning_yards_on_water():
    """Tanning is a wash trade - the yard stands at its water; one of two yards was beached
    189px inland (GM 2026-08-10)."""
    assert "tanning_yards_on_water" not in f(_water_map(tanning_yards=[{"x": 500, "y": 550, "w": 26, "h": 17, "rot": 0, "kind": "tanning yard"}]))
    assert "tanning_yards_on_water" in f(_water_map(tanning_yards=[{"x": 500, "y": 720, "w": 26, "h": 17, "rot": 0, "kind": "tanning yard"}]))


# ---- a lane must reach something (the internal counterpart of connector_lane_runs_off_edge) ----
def _lane_map(lanes, houses=(), gen="hamletgen"):
    return {"meta": {"scale": "hamlet", "ftpx": 1, "generated_by": gen}, "lanes": lanes, "houses": list(houses)}


def test_lanes_reach_something_fires_on_a_tread_that_stops_in_bare_grass():
    """A lane exists to be fronted. An internal arm ending far from every other way AND every
    farmhouse serves no house, reaches no field and connects to nothing - a blunt tread stopping in
    open ground. Measured before the fix: five such ends across the four scripted hamlets, because
    lanes are laid BEFORE the houses they serve and an arm meeting neither crop nor water had
    nothing to stop it."""
    M = _lane_map(
        [{"pts": [[500, 500], [500, 900]], "w": 5, "connector": False}],
        [{"x": 500, "y": 500, "w": 46, "h": 28, "rot": 0, "kind": "plain"}],  # serves the START only
    )
    assert "lanes_reach_something" in f(M)  # the far end is 400 ft from that house and there is no other way


def test_lanes_reach_something_passes_when_the_end_meets_another_way_or_a_house():
    served = _lane_map(
        [{"pts": [[500, 500], [500, 900]], "w": 5, "connector": False}],
        [{"x": 500, "y": 500, "w": 46, "h": 28, "rot": 0, "kind": "plain"}, {"x": 540, "y": 890, "w": 46, "h": 28, "rot": 0, "kind": "plain"}],
    )
    assert "lanes_reach_something" not in f(served), "a house at the far end is something to reach"
    met = _lane_map(
        # the crossing lane is kept SHORT on purpose: a long one would dangle at its own far end and
        # the check would fire for that instead, which is the check being right and the fixture wrong
        [{"pts": [[500, 500], [500, 900]], "w": 5, "connector": False}, {"pts": [[480, 905], [560, 905]], "w": 5, "connector": False}],
        [{"x": 500, "y": 500, "w": 46, "h": 28, "rot": 0, "kind": "plain"}, {"x": 540, "y": 890, "w": 46, "h": 28, "rot": 0, "kind": "plain"}],
    )
    assert "lanes_reach_something" not in f(met), "meeting another way is something to reach"


def test_lanes_reach_something_exempts_the_connector_and_skips_a_degenerate_lane():
    """The connector is the track OUT of the settlement and `connector_lane_runs_off_edge` REQUIRES
    it to reach the frame, so its far end is meant to serve nothing - exempting it is what stops the
    two rules contradicting each other. A one-point lane has no end to judge."""
    conn = _lane_map(
        [{"pts": [[500, 500], [500, 3000]], "w": 5, "connector": True}],
        [{"x": 500, "y": 500, "w": 46, "h": 28, "rot": 0, "kind": "plain"}],
    )
    assert "lanes_reach_something" not in f(conn)
    degenerate = _lane_map([{"pts": [[500, 500]], "w": 5, "connector": False}], [{"x": 900, "y": 900, "w": 46, "h": 28, "rot": 0, "kind": "plain"}])
    assert "lanes_reach_something" not in f(degenerate)


def test_lanes_reach_something_is_gated_on_generated_by():
    """The migration doctrine: the rule binds the scripted path, and a frozen hand-authored map
    inherits it at the moment it is CONVERTED rather than being retrofitted."""
    legacy = _lane_map([{"pts": [[500, 500], [500, 900]], "w": 5, "connector": False}], [{"x": 500, "y": 500, "w": 46, "h": 28, "rot": 0, "kind": "plain"}], gen=None)
    legacy["meta"].pop("generated_by")
    assert "lanes_reach_something" not in f(legacy)


# ---- every farmhouse is reached by a way (the converse of lanes_reach_something) ----------------
def test_farmhouses_reach_a_way_fires_on_a_house_the_web_does_not_touch():
    """The research is decisive that a house in a nucleated cluster is reached - "every house in the
    nucleated village is accessible via the interconnected system of narrow lanes and alleys". The
    earlier reading, that a back rank is walked to along unfigured footpaths, was defensible-sounding
    with nothing behind it, and it left 29 of the four pool hamlets' 66 farmhouses out of reach.

    Note this is the CONVERSE of `lanes_reach_something`, and a map can pass that one with every
    lane busy while still stranding a third of its houses - which is exactly what the pool did."""
    M = _lane_map(
        [{"pts": [[500, 500], [500, 900]], "w": 5, "connector": False}],
        [{"x": 500, "y": 600, "w": 46, "h": 28, "rot": 0, "kind": "plain"}, {"x": 900, "y": 700, "w": 46, "h": 28, "rot": 0, "kind": "plain"}],
    )
    assert "farmhouses_reach_a_way" in f(M), "the second house is 400 ft from the only lane"


def test_farmhouses_reach_a_way_passes_when_every_house_is_within_a_bundle_pitch():
    """The threshold is one BUNDLE_PITCH - the ground a single homestead occupies, which is the
    distance at which a lane passes your own plot or your neighbor's. Derived rather than chosen:
    the number it replaced was flagged in future-work/ as one nobody had justified."""
    M = _lane_map(
        [{"pts": [[500, 500], [500, 900]], "w": 5, "connector": False}],
        [{"x": 560, "y": 600, "w": 46, "h": 28, "rot": 0, "kind": "plain"}, {"x": 440, "y": 800, "w": 46, "h": 28, "rot": 0, "kind": "plain"}],
    )
    assert "farmhouses_reach_a_way" not in f(M)


def test_farmhouses_reach_a_way_measures_from_the_house_CENTER():
    """x, y ARE the center in this manifest, not the top-left corner - `rect_corners` reads them
    that way. Measuring from x + w/2 instead shifts every house half its own size, which is a real
    mistake this check made before it was caught: it moved the baseline count by three."""
    M = _lane_map(
        [{"pts": [[500, 400], [500, 600]], "w": 5, "connector": False}],
        [{"x": 590, "y": 500, "w": 100, "h": 28, "rot": 0, "kind": "plain"}],
    )
    assert "farmhouses_reach_a_way" not in f(M), "center is 90 ft off the lane; a corner-read would call it 140"


def test_farmhouses_reach_a_way_is_silent_on_a_map_with_no_ways_or_no_houses():
    """Scoped to scripted maps, and it makes no claim about a manifest that has nothing to measure."""
    assert "farmhouses_reach_a_way" not in f(_lane_map([], [{"x": 900, "y": 900, "w": 46, "h": 28, "rot": 0, "kind": "plain"}]))
    assert "farmhouses_reach_a_way" not in f(_lane_map([{"pts": [[500, 500], [500, 900]], "w": 5, "connector": False}], []))
    hand = _lane_map([{"pts": [[500, 500], [500, 900]], "w": 5, "connector": False}], [{"x": 2000, "y": 2000, "w": 46, "h": 28, "rot": 0, "kind": "plain"}], gen="")
    assert "farmhouses_reach_a_way" not in f(hand), "hand-authored maps are not gated by this rule"


# ---- two lane ends may not front the same farmhouse from the same side --------------------------
def test_lane_ends_front_different_houses_fires_on_a_fan_of_blunt_tines():
    """A farmhouse discharges ONE lane end's obligation, not three. A settlement-review read three
    ways leaving one node within 23 degrees, two ending blunt and all three claiming the same house
    at 66.9 / 55.1 / 40.0 ft, as a broom at 3x zoom: not three ways, one way drawn three times with
    the ends fanned. `lanes_reach_something` was silent because each end could point at the house."""
    M = _lane_map(
        [
            {"pts": [[500, 500], [700, 505]], "w": 5, "connector": False},
            {"pts": [[500, 540], [700, 549]], "w": 5, "connector": False},
        ],
        [{"x": 740, "y": 525, "w": 46, "h": 28, "rot": 0, "kind": "plain"}],
    )
    assert "lane_ends_front_different_houses" in f(M)


def test_lane_ends_front_different_houses_allows_a_house_on_a_CORNER():
    """Two lanes reaching one house from OPPOSITE quarters is a corner - a real thing that reads as
    one. The bearing clause is what keeps that legal; without it the rule would flag most of a
    nucleated cluster's middle."""
    M = _lane_map(
        [
            {"pts": [[500, 525], [700, 525]], "w": 5, "connector": False},
            {"pts": [[980, 525], [780, 525]], "w": 5, "connector": False},
        ],
        [{"x": 740, "y": 525, "w": 46, "h": 28, "rot": 0, "kind": "plain"}],
    )
    assert "lane_ends_front_different_houses" not in f(M)


def test_lane_ends_front_different_houses_exempts_an_end_that_MET_a_way():
    """An end that crosses another way at a real angle is a junction, and a junction beside a
    junction is a crossroads however tightly they sit. Only a BLUNT end can be a tine."""
    M = _lane_map(
        [
            {"pts": [[500, 500], [700, 505]], "w": 5, "connector": False},
            {"pts": [[500, 540], [700, 549]], "w": 5, "connector": False},
            {"pts": [[700, 460], [700, 600]], "w": 5, "connector": False},  # crosses both, squarely
        ],
        [{"x": 740, "y": 525, "w": 46, "h": 28, "rot": 0, "kind": "plain"}],
    )
    assert "lane_ends_front_different_houses" not in f(M)


def test_lane_ends_front_different_houses_is_silent_without_lanes_or_houses():
    assert "lane_ends_front_different_houses" not in f(_lane_map([], []))
    assert "lane_ends_front_different_houses" not in f(_lane_map([{"pts": [[500, 500]], "w": 5, "connector": False}], []))


# ---- one way drawn as two --------------------------------------------------------------------
def test_lanes_do_not_break_mid_run_fires_on_a_hole_in_a_street():
    """Two ends pointing AT each other across empty ground are one street with a hole in it, and both
    read as a rounded cap dying in bare grass. `lanes_reach_something` passes them because it tests
    each end independently, and an end 83 ft from a house CENTRE counts as fronting it even when that
    is 55 ft from the wall - out past the dooryard."""
    M = _lane_map(
        [
            {"pts": [[500, 500], [700, 500]], "w": 5, "connector": False},
            {"pts": [[810, 500], [1010, 500]], "w": 5, "connector": False},
        ],
        [{"x": 600, "y": 560, "w": 46, "h": 28, "rot": 0, "kind": "plain"}],
    )
    assert "lanes_do_not_break_mid_run" in f(M)


def test_lanes_do_not_break_mid_run_allows_a_break_with_something_IN_it():
    """An interruption with a wellhead in it is honest - the way stops because something is there."""
    M = _lane_map(
        [
            {"pts": [[500, 500], [700, 500]], "w": 5, "connector": False},
            {"pts": [[810, 500], [1010, 500]], "w": 5, "connector": False},
        ],
        [{"x": 600, "y": 560, "w": 46, "h": 28, "rot": 0, "kind": "plain"}],
    )
    M["wells"] = [{"x": 755, "y": 500, "r": 9, "vr": 14}]
    assert "lanes_do_not_break_mid_run" not in f(M)


def test_lanes_do_not_break_mid_run_allows_a_gap_a_third_way_already_spans():
    """Closing a break leaves the two original ends where they were, joined THROUGH the new lane.
    Without this the check fires on the very repair that fixes it."""
    M = _lane_map(
        [
            {"pts": [[500, 500], [700, 500]], "w": 5, "connector": False},
            {"pts": [[810, 500], [1010, 500]], "w": 5, "connector": False},
            {"pts": [[700, 500], [810, 500]], "w": 5, "connector": False},
        ],
        [{"x": 600, "y": 560, "w": 46, "h": 28, "rot": 0, "kind": "plain"}],
    )
    assert "lanes_do_not_break_mid_run" not in f(M)


def test_lanes_do_not_break_mid_run_ignores_ends_that_do_not_point_at_each_other():
    """Two arms leaving a cluster in different directions are two arms, however near their tips."""
    M = _lane_map(
        [
            {"pts": [[500, 500], [700, 500]], "w": 5, "connector": False},
            {"pts": [[790, 620], [790, 820]], "w": 5, "connector": False},
        ],
        [{"x": 600, "y": 560, "w": 46, "h": 28, "rot": 0, "kind": "plain"}],
    )
    assert "lanes_do_not_break_mid_run" not in f(M)
