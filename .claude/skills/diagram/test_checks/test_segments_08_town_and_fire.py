"""Split from test_checks.py by feature 025 - see test_checks/CLAUDE.md for the index."""

import check_village
from test_checks._builders import (
    _BB_FILLER,
    _BB_HOST,
    _FIELD_400,
    _POND_FEED,
    _bb_M,
    _drain,
    _drain_map,
    _dw,
    _field,
    _hem_M,
    _kosatsuba,
    _monastery,
    _shrine_avenue,
    _sup_M,
    _tower,
    _town_align,
    _town_behind,
    _town_caravan,
    _town_housing,
    _town_manor,
    bldg,
    exground,
    f,
    manifest,
    pspot,
)


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


def test_marsh_on_low_ground_ignores_a_defense_belt():
    # a defensive wet belt hugs the fortified perimeter wherever the wall runs - here uphill (NW) of the
    # field; defense_marsh_girds_the_walls owns its placement, so the valley-toe rule leaves it alone
    M = {
        "meta": {"scale": "village", "down_deg": 45},
        "fields": [_field("p", 1000, 1000, 1600, 1600)],
        "marshes": [{"x": 300, "y": 300, "w": 100, "h": 100, "role": "defense", "poly": [[250, 250], [350, 250], [350, 350], [250, 350]]}],
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


def test_paddy_bunds_clear_the_collector_fires_on_a_bund_drawn_across_the_ditch():
    # a basin straddling the collector: two vertices above the line, two below it - the contour-laid
    # hem plot the GM caught, whose bottom bund starts on one bank and ends on the other
    assert "paddy_bunds_clear_the_collector" in f(_hem_M([[480, 480], [520, 440], [560, 480], [520, 520]]))


def test_paddy_bunds_clear_the_collector_fires_on_a_bund_inside_the_ditchs_stroke():
    # entirely on the field side of the centerline, but the lower edge sits ~1px off it - inside the
    # collector's DRAWN stroke, which reaches 6px wide at the outfall. This is the half of the defect
    # a centerline test alone would miss.
    assert "paddy_bunds_clear_the_collector" in f(_hem_M([[440, 440], [480, 400], [520, 479], [480, 519]]))


def test_paddy_bunds_clear_the_collector_passes_when_the_field_hems_onto_the_bank():
    # the same basin held off to the bank: every vertex is well up-fall of the ditch
    assert "paddy_bunds_clear_the_collector" not in f(_hem_M([[440, 440], [480, 400], [500, 460], [460, 500]]))


def test_paddy_bunds_clear_the_collector_skips_ground_past_the_collectors_ends():
    # downhill of the drain's LINE but off the tail of the drain itself (every vertex projects past
    # its far end) - the collector does not reach this ground, so it hems onto something else
    assert "paddy_bunds_clear_the_collector" not in f(_hem_M([[760, 240], [800, 280], [760, 320], [720, 280]]))


def test_paddy_bunds_clear_the_collector_skips_a_field_with_no_recorded_hem():
    # a non-comb paddy records no drain_hem: nothing to judge (and no silent pass claimed for it)
    M = _hem_M([[480, 480], [520, 440], [560, 480], [520, 520]])
    M["fields"][0].pop("drain_hem")
    assert "paddy_bunds_clear_the_collector" not in f(M)


def test_paddy_bunds_clear_the_supply_channels_fires_on_a_bund_down_the_channels_centerline():
    # the pre-fix Inashiro shape: a sector-boundary bund laid exactly ON the supply thread's line
    assert "paddy_bunds_clear_the_supply_channels" in f(_sup_M([[500, 300], [500, 400], [540, 400], [540, 300]]))


def test_paddy_bunds_clear_the_supply_channels_fires_on_a_bund_inside_the_stroke():
    # on the field side of the centerline but still inside the drawn water (gap 3 < 4.6)
    assert "paddy_bunds_clear_the_supply_channels" in f(_sup_M([[503, 300], [503, 400], [540, 400], [540, 300]]))


def test_paddy_bunds_clear_the_supply_channels_fires_on_a_branch_ditch_too():
    # delivery ditches are supply strokes exactly like the canal pieces
    assert "paddy_bunds_clear_the_supply_channels" in f(_sup_M([[500, 300], [500, 400], [540, 400], [540, 300]], role="branch"))


def test_paddy_bunds_clear_the_supply_channels_passes_when_the_bund_sits_on_the_bank():
    # held off past halfw + BANK_MARGIN: the bund ABUTS the water's edge and runs along it
    assert "paddy_bunds_clear_the_supply_channels" not in f(_sup_M([[505.5, 300], [505.5, 400], [540, 400], [540, 300]]))


def test_paddy_bunds_clear_the_supply_channels_fires_on_an_edge_through_the_water_with_dry_corners():
    # the Sawada junction wedge (settlement-review 2026-08-15): every corner projects past the
    # stroke's ends (governed by nothing) but the long edges run straight down the channel - the
    # drawn bund crosses the water even though a vertex-only test sees nothing
    assert "paddy_bunds_clear_the_supply_channels" in f(_sup_M([[498, 150], [502, 150], [502, 850], [498, 850]]))


def test_paddy_bunds_clear_the_supply_channels_skips_ground_past_the_strokes_ends():
    # inside the stroke's bbox but projecting past its tail: that ground is not governed by it
    assert "paddy_bunds_clear_the_supply_channels" not in f(_sup_M([[500, 803], [503, 804], [540, 850], [540, 900]]))


def test_paddy_bunds_clear_the_supply_channels_does_not_govern_the_drain():
    # the drain side is the collector rule's business (its bunds hem onto the bank IN FALL)
    assert "paddy_bunds_clear_the_supply_channels" not in f(_sup_M([[500, 300], [500, 400], [540, 400], [540, 300]], role="drain"))


def test_paddy_bunds_clear_the_supply_channels_skips_legacy_maps():
    # no meta.generated_by = a legacy comb map; it inherits the rule when converted (migration doctrine)
    assert "paddy_bunds_clear_the_supply_channels" not in f(_sup_M([[500, 300], [500, 400], [540, 400], [540, 300]], gen=None))


def test_paddy_bunds_clear_the_supply_channels_skips_a_field_with_no_recorded_rings():
    # pre-2026-08-15 manifests record no plot_rings: nothing to judge (same line the bead checks hold)
    M = _sup_M([[500, 300], [500, 400], [540, 400], [540, 300]])
    M["fields"][0].pop("plot_rings")
    assert "paddy_bunds_clear_the_supply_channels" not in f(M)


def test_paddy_bunds_clear_the_supply_channels_skips_a_degenerate_ditch_record():
    # a 1-point poly has no stroke to govern with
    assert "paddy_bunds_clear_the_supply_channels" not in f(_sup_M([[500, 300], [500, 400], [540, 400], [540, 300]], ditch={"poly": [[500, 200]], "role": "main", "field": "f", "w": 8.0}))


def test_paddy_bunds_clear_the_collector_skips_a_hem_whose_field_declares_no_fall():
    # the block runs (another field declares a fall) but THIS field's drain has no fall to judge by,
    # so "which side is downhill" is unanswerable - settlement_declares_a_land_fall is what catches that
    M = _hem_M([[480, 480], [520, 440], [560, 480], [520, 520]])
    del M["meta"]["down_deg"]
    M["fields"].append({**_field("other", 100, 100, 200, 200), "down_deg": 45})
    assert "paddy_bunds_clear_the_collector" not in f(M)


def test_drain_flows_downhill_skips_non_drain_ditches():
    # a SUPPLY (main) ditch is not a collector - the drainage-direction check ignores it (only 'drain' role)
    M = {"meta": {"down_deg": 45}, "field_ditches": [{"poly": [[100, 100], [200, 200]], "role": "main", "field": "f"}, {"poly": [[300, 300], [700, 700]], "role": "drain", "field": "f"}]}
    assert "drain_flows_downhill" not in f(M)


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


def test_town_has_flophouse_opt_out_with_zero():
    assert "town_has_flophouse" not in f({"meta": {"scale": "town", "flophouses": 0}})


def test_town_monasteries_dedicated_fires_on_wrong_fortune():
    # Lion's patrons are Bishamon + Daikoku; a Benten monastery is wrong (no override declared)
    M = {"meta": {"scale": "town", "clan": "Lion"}, "religious": [_monastery("Bishamon"), _monastery("Benten")]}
    assert "town_monasteries_dedicated" in f(M)


def test_town_monasteries_dedicated_passes_with_correct_fortunes():
    M = {"meta": {"scale": "town", "clan": "Lion"}, "religious": [_monastery("Bishamon"), _monastery("Daikoku")]}
    assert "town_monasteries_dedicated" not in f(M)


def test_house_count_in_range_target_houses_fires():
    houses = [{"x": i * 30, "y": 100, "w": 44, "h": 29, "kind": "plain", "rot": 0} for i in range(10)]
    M = {"meta": {"scale": "village", "target_houses": 60}, "houses": houses}  # 10 vs ~60
    assert "house_count_in_range" in f(M)


# ---- torii_spread_out: scale-aware floor of one arch-span (16 ft), so dense senbon avenues are legal --------
def test_torii_spread_out_fires_when_arches_overlap():
    # two arches closer than one rail-span (16 ft = 8px at village 2 ft/px) collapse into a blob
    M = {"meta": {"scale": "village", "ftpx": 2}, "torii": [[400, 440, 1], [400, 445, 2]]}
    assert "torii_spread_out" in f(M)


def test_torii_spread_out_passes_a_dense_avenue():
    # a dense senbon-style avenue (~14px/28ft apart) is fine - denser than the old fixed 25px floor allowed
    M = {"meta": {"scale": "village", "ftpx": 2}, "torii": [[400, 440 + i * 14, i] for i in range(7)]}
    assert "torii_spread_out" not in f(M)


def test_shrine_avenue_fronts_the_hall_fires_when_the_arch_is_set_out():
    # the innermost arch stands well out from the hall front (96 ft > the 36 ft ceiling)
    assert "shrine_avenue_fronts_the_hall" in f(_shrine_avenue(400, 460))


def test_shrine_avenue_fronts_the_hall_passes_at_the_threshold():
    # innermost arch at the hall's front (24 ft gap)
    assert "shrine_avenue_fronts_the_hall" not in f(_shrine_avenue(400, 424))


def test_shrine_avenue_fronts_the_hall_exempts_a_gateway_beside_the_hall():
    # Hikari pattern: the hall stands aside the entrance track (200 ft off the avenue axis), arches straddle the track
    assert "shrine_avenue_fronts_the_hall" not in f(_shrine_avenue(300, 460))


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


def test_town_merchant_housing_varied_fires_when_uniform():
    assert "town_merchant_housing_varied" in f(_town_housing(m_large=0, l_large=3))


def test_town_merchant_housing_varied_passes_when_mixed():
    assert "town_merchant_housing_varied" not in f(_town_housing(m_large=4, l_large=3))


def test_town_laborer_housing_varied_fires_when_uniform():
    assert "town_laborer_housing_varied" in f(_town_housing(m_large=4, l_large=0))


def test_town_laborer_housing_varied_passes_when_mixed():
    assert "town_laborer_housing_varied" not in f(_town_housing(m_large=4, l_large=3))


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


def test_manor_gate_faces_town_passes_facing_the_town():
    assert "manor_gate_faces_town" not in f(_town_manor("south"))  # town is SE -> south gate faces it


def test_manor_gate_faces_town_fires_facing_away():
    assert "manor_gate_faces_town" in f(_town_manor("north"))  # north gate faces away from the SE town


def test_manor_gate_faces_town_passes_facing_the_road():
    # town centroid is SE, but a north gate faces an Imperial road to the manor's north -> ok
    assert "manor_gate_faces_town" not in f(_town_manor("north", road=[[100, 150], [600, 150]]))


def test_walled_town_has_fire_tower_fires_when_absent():
    # WALLED towns only (GM 2026-07-24, reverting the 2026-07 audit widening): an unwalled seat
    # keeps fire bells and kura, not a tower - see settlements.md "Fire towers"
    assert "walled_town_has_fire_tower" in f({"meta": {"scale": "town", "walled": True}})


def test_walled_town_has_fire_tower_passes_with_one():
    assert "walled_town_has_fire_tower" not in f({"meta": {"scale": "town", "walled": True}, "fire_towers": [_tower(500, 500)]})


def test_walled_town_has_fire_tower_opt_out():
    assert "walled_town_has_fire_tower" not in f({"meta": {"scale": "town", "walled": True, "fire_tower": False}})


def test_unwalled_town_needs_no_fire_tower():
    # an OPEN town's detached fabric has its own natural breaks; the presence check is walled-only
    # (and the widened town_has_fire_tower name must stay gone)
    fails = f({"meta": {"scale": "town", "walled": False}})
    assert "walled_town_has_fire_tower" not in fails
    assert "town_has_fire_tower" not in fails


def test_town_has_kosatsuba_fires_when_absent():
    # every town, walled or not (GM 2026-07-24): the state's edict board stood in every
    # Edo town and village
    assert "town_has_kosatsuba" in f({"meta": {"scale": "town", "walled": False}})
    assert "town_has_kosatsuba" in f({"meta": {"scale": "town", "walled": True}})


def test_town_kosatsuba_passes_by_a_main_street():
    # sited on the traffic artery: within ~60 ft of a road or main street (town_streets branch)
    M = {"meta": {"scale": "town"}, "kosatsuba": [_kosatsuba(500, 530)], "town_streets": [{"pts": [[0, 500], [1000, 500]], "w": 28}]}
    fails = f(M)
    assert "town_has_kosatsuba" not in fails and "kosatsuba_by_the_road" not in fails


def test_kosatsuba_by_the_road_fires_when_marooned():
    # a board deep in the back blocks defeats the institution (road branch of the routes)
    M = {"meta": {"scale": "town"}, "kosatsuba": [_kosatsuba(500, 900)], "road": [[0, 500], [1000, 500]]}
    assert "kosatsuba_by_the_road" in f(M)


def test_kosatsuba_on_a_main_way_fires_on_a_side_lane_board():
    # GM 2026-08-02 (Ubame): the board sat a legal 49 ft off a side lane while the high street
    # ran 200 ft away. Where the map declares a way hierarchy, only a MAIN way seats the board -
    # the side lane satisfies the old distance check, which is exactly why this check exists.
    M = {
        "meta": {"scale": "town"},
        "kosatsuba": [_kosatsuba(500, 830)],
        "road": [[0, 500], [1000, 500]],
        "lanes": [{"pts": [[0, 800], [1000, 800]], "w": 5}],
    }
    fails = f(M)
    assert "kosatsuba_by_the_road" not in fails
    assert "kosatsuba_on_a_main_way" in fails
    on_road = f({**M, "kosatsuba": [_kosatsuba(500, 530)]})
    assert "kosatsuba_on_a_main_way" not in on_road


def test_kosatsuba_on_a_main_way_reads_the_main_street_flag():
    # a main: True town street is a main way; an unflagged one is a side street
    main_st = {"pts": [[0, 500], [1000, 500]], "w": 28, "main": True}
    side_st = {"pts": [[0, 800], [1000, 800]], "w": 22, "main": False}
    on_side = f({"meta": {"scale": "town"}, "kosatsuba": [_kosatsuba(500, 830)], "town_streets": [main_st, side_st]})
    assert "kosatsuba_on_a_main_way" in on_side
    on_main = f({"meta": {"scale": "town"}, "kosatsuba": [_kosatsuba(500, 530)], "town_streets": [main_st, side_st]})
    assert "kosatsuba_on_a_main_way" not in on_main


def test_kosatsuba_on_a_main_way_exempts_maps_with_no_declared_hierarchy():
    # a village whose network is all lanes (and a town whose streets are all unflagged) has no
    # main/side distinction to violate - the check would be unsatisfiable there, so the
    # busiest-node scoring in place_kosatsuba stands in for "main" instead
    lanes_only = f({"meta": {"scale": "village", "ftpx": 2}, "kosatsuba": [_kosatsuba(500, 512)], "lanes": [{"pts": [[0, 500], [1000, 500]], "w": 5}]})
    assert "kosatsuba_on_a_main_way" not in lanes_only
    unflagged = f({"meta": {"scale": "town"}, "kosatsuba": [_kosatsuba(500, 530)], "town_streets": [{"pts": [[0, 500], [1000, 500]], "w": 28}]})
    assert "kosatsuba_on_a_main_way" not in unflagged


def test_town_kosatsuba_opt_out():
    # a suppressed or backwater seat may omit it
    assert "town_has_kosatsuba" not in f({"meta": {"scale": "town", "kosatsuba": False}})


def test_kosatsuba_routeless_map_skips_the_siting_check():
    # no road/street recorded: presence still gates, the siting check stays quiet
    fails = f({"meta": {"scale": "town"}, "kosatsuba": [_kosatsuba(500, 900)]})
    assert "kosatsuba_by_the_road" not in fails
    # ... and so does the ORIENTATION check: with no route in the band there is nothing to face
    assert "kosatsuba_faces_the_road" not in fails
    marooned = f({"meta": {"scale": "town"}, "kosatsuba": [dict(_kosatsuba(500, 900), rot=90)], "road": [[0, 500], [1000, 500]]})
    assert "kosatsuba_by_the_road" in marooned and "kosatsuba_faces_the_road" not in marooned


def test_kosatsuba_faces_the_road_fires_when_edge_on():
    # GM 2026-07-27: a kosatsu is a BROADSIDE signboard - stood across the road it fronts, its
    # face goes edge-on to the traffic the siting check fought for, and both the presence and
    # distance checks stay green. The glyph's long axis IS the face, so rot = the road's bearing.
    road = [[0, 500], [1000, 500]]
    across = f({"meta": {"scale": "town"}, "kosatsuba": [dict(_kosatsuba(500, 530), rot=90)], "road": road})
    assert "kosatsuba_by_the_road" not in across and "kosatsuba_faces_the_road" in across
    along = f({"meta": {"scale": "town"}, "kosatsuba": [dict(_kosatsuba(500, 530), rot=0)], "road": road})
    assert "kosatsuba_faces_the_road" not in along
    # a board on a BEND takes the bend's bearing, so a few degrees off its nearest segment is fine
    assert "kosatsuba_faces_the_road" not in f({"meta": {"scale": "town"}, "kosatsuba": [dict(_kosatsuba(500, 530), rot=18)], "road": road})


def test_kosatsuba_at_a_junction_may_face_either_way():
    # ANY route segment inside the siting band counts, not merely the nearest: a board at a
    # crossing legitimately fronts one of the two ways that meet there (the real case -
    # Nagahara's north-ward board sits nearer a cross street than the ward street it fronts)
    M = {
        "meta": {"scale": "town"},
        "kosatsuba": [dict(_kosatsuba(500, 480), rot=90)],
        "town_streets": [{"pts": [[0, 500], [1000, 500]], "w": 28}, {"pts": [[540, 0], [540, 1000]], "w": 28}],
    }
    assert "kosatsuba_faces_the_road" not in f(M)


def test_city_has_kosatsuba_fires_when_absent():
    # cities port the institution up (GM 2026-07-24): a city DRAWS the set
    assert "city_has_kosatsuba" in f({"meta": {"scale": "city"}})
    assert "city_has_kosatsuba" not in f({"meta": {"scale": "city", "kosatsuba": False}})


def test_city_kosatsuba_floor_is_gates_plus_central():
    # the principal central board + one per main gate (GM 2026-07-24): 2 gates -> floor 3
    road = [[0, 500], [2000, 500]]
    gates = [[520, 500], [1900, 500]]
    two = f({"meta": {"scale": "city", "ftpx": 3}, "kosatsuba": [_kosatsuba(500, 520), _kosatsuba(1880, 520)], "road": road, "gates": gates})
    assert "city_has_kosatsuba" in two
    three = f({"meta": {"scale": "city", "ftpx": 3}, "kosatsuba": [_kosatsuba(500, 520), _kosatsuba(1880, 520), _kosatsuba(1200, 515)], "road": road, "gates": gates})
    assert "city_has_kosatsuba" not in three


def test_village_and_hamlet_have_kosatsuba():
    # the ofuregaki reached the peasantry through the village/hamlet board via the literate
    # headman (GM 2026-07-24); siting works off the LANE network at these tiers
    assert "village_has_kosatsuba" in f({"meta": {"scale": "village"}})
    assert "hamlet_has_kosatsuba" in f({"meta": {"scale": "hamlet"}})
    assert "hamlet_has_kosatsuba" not in f({"meta": {"scale": "hamlet", "kosatsuba": False}})
    ok = f({"meta": {"scale": "village", "ftpx": 2}, "kosatsuba": [_kosatsuba(500, 512)], "lanes": [{"pts": [[0, 500], [1000, 500]], "w": 5}]})
    assert "village_has_kosatsuba" not in ok and "kosatsuba_by_the_road" not in ok
    marooned = f({"meta": {"scale": "hamlet"}, "kosatsuba": [_kosatsuba(500, 700)], "lane": [[0, 500], [1000, 500]]})
    assert "kosatsuba_by_the_road" in marooned


def test_city_kosatsuba_per_gate_fires_on_an_uncovered_gate():
    # draw the SET: every main gate's approach corridor carries a board (~800 real ft);
    # one gate covered, the other bare -> fires and names the bare gate's coordinates
    M = {
        "meta": {"scale": "city", "ftpx": 3},
        "kosatsuba": [_kosatsuba(500, 520)],
        "road": [[0, 500], [2000, 500]],
        "gates": [[520, 500], [1900, 500]],
    }
    assert "city_kosatsuba_per_gate" in f(M)


def test_city_kosatsuba_per_gate_passes_when_every_gate_is_covered():
    M = {
        "meta": {"scale": "city", "ftpx": 3},
        "kosatsuba": [_kosatsuba(500, 520), _kosatsuba(1880, 520)],
        "road": [[0, 500], [2000, 500]],
        "gates": [[520, 500], [1900, 500]],
    }
    assert "city_kosatsuba_per_gate" not in f(M)


def test_city_kosatsuba_siting_threshold_is_scale_aware():
    # the ~60 ft siting limit is REAL feet: 30 px off the road passes at town grain (30 ft)
    # but fires at city grain (1 px = 3 ft -> 90 ft)
    road = [[0, 500], [1000, 500]]
    assert "kosatsuba_by_the_road" not in f({"meta": {"scale": "town"}, "kosatsuba": [_kosatsuba(500, 530)], "road": road})
    assert "kosatsuba_by_the_road" in f({"meta": {"scale": "city", "ftpx": 3}, "kosatsuba": [_kosatsuba(500, 530)], "road": road})
    ok = f({"meta": {"scale": "city", "ftpx": 3}, "kosatsuba": [_kosatsuba(500, 515)], "road": road})
    assert "kosatsuba_by_the_road" not in ok and "city_has_kosatsuba" not in ok


# ---- households_consistent: the LEGACY (extended-family) band on an off-scale tier -----------
# On a to-scale tier (village/hamlet, or meta.toscale) the map depicts ~every household 1:1
# (~0.85-1.05x). A tier that is NOT to-scale (a town/city carrying a `households` meta, or an
# explicit toscale:False) falls to the legacy ~0.68-0.9x extended-family band. This pins that
# branch: a town declaring 100 households but depicting zero farmhouses is out of even the
# looser legacy band and must fire.
def test_households_consistent_uses_legacy_band_when_not_to_scale():
    M = {"meta": {"scale": "town", "households": 100}}  # town => scale != "village", no toscale => legacy band
    assert "households_consistent" in f(M)


# ---- defense_marsh_girds_the_walls (the engineered defensive wet belt, GM 2026-07-23) ----------
def test_defense_marsh_girds_the_walls_needs_a_fortified_perimeter():
    # a defensive inundation on a map with NO wall or moat defends nothing
    M = {"meta": {}, "marshes": [{"x": 500, "y": 500, "w": 100, "h": 100, "role": "defense", "poly": [[450, 450], [550, 450], [550, 550], [450, 550]]}]}
    assert "defense_marsh_girds_the_walls" in f(M)


def test_defense_marsh_girds_the_walls_fires_inside_the_circuit():
    # the wet belt reaches INSIDE the wall - the inundation protects the wall; inside is the town
    M = {
        "meta": {},
        "wall": [[300, 300], [700, 300], [700, 700], [300, 700]],
        "marshes": [{"x": 500, "y": 500, "w": 100, "h": 100, "role": "defense", "poly": [[450, 450], [550, 450], [550, 550], [450, 550]]}],
    }
    assert "defense_marsh_girds_the_walls" in f(M)


def test_defense_marsh_girds_the_walls_fires_when_detached():
    # outside the wall but nowhere near it - a bog detached from the fortification defends nothing
    M = {
        "meta": {},
        "wall": [[300, 300], [700, 300], [700, 700], [300, 700]],
        "marshes": [{"x": 940, "y": 940, "w": 80, "h": 80, "role": "defense", "poly": [[900, 900], [980, 900], [980, 980], [900, 980]]}],
    }
    assert "defense_marsh_girds_the_walls" in f(M)


def test_defense_marsh_girds_the_walls_passes_hugging_the_moat():
    # the belt lies just beyond the moat's outer bank, east of the circuit - the historical form
    M = {
        "meta": {},
        "wall": [[300, 300], [700, 300], [700, 700], [300, 700]],
        "moat": [[280, 280], [720, 280], [720, 720], [280, 720], [280, 280]],
        "marshes": [{"x": 760, "y": 500, "w": 60, "h": 400, "role": "defense", "poly": [[730, 300], [790, 300], [790, 700], [730, 700]]}],
    }
    assert "defense_marsh_girds_the_walls" not in f(M)


def test_defense_marsh_girds_the_walls_skips_a_degenerate_poly():
    # a 2-point sliver carries no area to test - skipped, no crash (and no wall demanded for it)
    M = {"meta": {}, "marshes": [{"x": 500, "y": 500, "w": 10, "h": 10, "role": "defense", "poly": [[490, 495], [510, 505]]}]}
    assert "defense_marsh_girds_the_walls" not in f(M)


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


def test_marsh_on_low_ground_exempts_the_waterside_fringe():
    # a polder's waterside fringe surrounds the dike regardless of the fall direction (the polder floor
    # sits BELOW the outside water level) - only the valley-toe role must lie downhill of the paddy.
    base = {
        "meta": {"scale": "hamlet", "down_deg": 90},
        "fields": [{"name": "p", "kind": "paddy", "outline": [[300, 300], [1100, 300], [1100, 1100], [300, 1100]], "bbox": [300, 300, 1100, 1100]}],
    }
    west_fringe = {**base, "marshes": [{"x": 200, "y": 700, "w": 200, "h": 900, "rot": 0, "role": "waterside", "poly": [[100, 250], [300, 250], [300, 1150], [100, 1150]]}]}
    assert "marsh_on_low_ground" not in f(west_fringe)  # same fall as the field centroid - exempt
    uphill_toe = {**base, "marshes": [{"x": 700, "y": 200, "w": 800, "h": 200, "rot": 0, "role": "toe", "poly": [[300, 100], [1100, 100], [1100, 300], [300, 300]]}]}
    assert "marsh_on_low_ground" in f(uphill_toe)  # a TOE marsh uphill of the paddy still fires


def test_drain_runs_cross_slope_fires_on_a_drain_running_with_the_fall():
    assert "drain_runs_cross_slope" in f(_drain_map())


def test_drain_runs_cross_slope_uses_the_FIELD_s_own_fall_not_the_map_s():
    # same drain, but this field falls EAST (0 deg) - so the drain now runs across its own contour
    # and is correct. A city ringed by farmland drains several ways at once; one map-level constant
    # cannot describe it (Tango's fans span 210 deg).
    M = _drain_map()
    M["fields"][0]["down_deg"] = 0
    assert "drain_runs_cross_slope" not in f(M)


def test_drain_runs_cross_slope_exempts_a_trimmed_inwall_drain():
    # an in-wall drain is cut short of the patrol ring and sluice-gated into a conduit to the moat,
    # so what remains is the last leg to the outfall - a stub, not a contour collector
    M = _drain_map()
    M["field_ditches"][0]["trimmed"] = True
    assert "drain_runs_cross_slope" not in f(M)


def test_drain_flows_downhill_reads_the_NAMED_discharge_channel_over_an_uphill_edge():
    # Nagahara's fnn2 exactly: the drain's HEAD sits inside the 32px at_edge tolerance of the frame's
    # TOP (upslope), so the edge signal alone called the high end the outfall and reported the water
    # running backwards. A discharge channel NAMING this field puts the real outfall at the tail, and
    # pooling the evidence and taking the LOWEST end resolves it.
    M = _drain_map(
        field_ditches=[{"role": "drain", "field": "f1", "poly": [[400, 20], [700, 300]], "w": 1.5}],
        channels=[{"poly": [[700, 300], [780, 360]], "frm": {"kind": "drain", "name": "f1"}, "to": {"kind": "offmap"}, "w": 2.5}],
    )
    assert "drain_flows_downhill" not in f(M)


def test_drain_flows_downhill_ignores_a_discharge_channel_naming_ANOTHER_field():
    # the whole point of naming: Hirameki carries seven discharge channels and several sit on top of
    # a different field's drain, so proximity matching mis-attributed them
    M = _drain_map(
        field_ditches=[{"role": "drain", "field": "f1", "poly": [[400, 20], [700, 300]], "w": 1.5}],
        channels=[{"poly": [[700, 300], [780, 360]], "frm": {"kind": "drain", "name": "SOMEWHERE-ELSE"}, "to": {"kind": "offmap"}, "w": 2.5}],
    )
    assert "drain_flows_downhill" in f(M)


def test_drain_flows_downhill_still_fires_on_a_genuinely_backwards_drain():
    # outfall on a stream at the HIGH end: the evidence is a real sink, so the check must still bite
    M = _drain_map(
        streams=[{"poly": [[300, 250], [900, 250]], "w": 8, "flow": "forward", "flow_deg": 0.0, "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}}],
        field_ditches=[{"role": "drain", "field": "f1", "poly": [[400, 260], [430, 800]], "w": 1.5}],
    )
    assert "drain_flows_downhill" in f(M)


def test_drainage_slope_checks_skip_a_drain_whose_field_declares_no_fall():
    # a city declares no map-level down_deg (no single bearing can describe a settlement whose fans
    # fall 210 deg apart), so a drain belonging to a field WITHOUT its own slope has nothing to be
    # judged against - it is skipped rather than measured against a fiction
    M = {
        "meta": {"scale": "city", "ftpx": 3, "W": 3200, "H": 2700},
        "fields": [
            {"name": "has_slope", "kind": "paddy", "outline": [[200, 200], [900, 200], [900, 900], [200, 900]], "bbox": [200, 200, 900, 900], "vis_bbox": [200, 200, 900, 900], "down_deg": 90},
            {"name": "no_slope", "kind": "paddy", "outline": [[1200, 200], [1900, 200], [1900, 900], [1200, 900]], "bbox": [1200, 200, 1900, 900], "vis_bbox": [1200, 200, 1900, 900]},
        ],
        "field_ditches": [{"role": "drain", "field": "no_slope", "poly": [[1300, 300], [1330, 800]], "w": 1.5}],
    }
    fails = f(M)
    assert "drain_flows_downhill" not in fails
    assert "drain_runs_cross_slope" not in fails


def test_the_justice_works_are_forbidden_below_a_seat_of_justice():
    M = manifest(punishment_spots=[pspot(500, 500)], execution_grounds=[exground(900, 900)])
    bad = f(M)  # manifest() is a VILLAGE - no magistrate, no court
    assert "punishment_spot_only_at_a_seat_of_justice" in bad
    assert "execution_ground_only_at_a_seat_of_justice" in bad


def test_burakumin_quarter_segregated_passes_across_a_real_seam():
    # The control for the ratchet entry: 60 ft of open ground between the walls is the rule met.
    M = manifest(meta={"scale": "town", "ftpx": 1, "W": 2000, "H": 2000}, buildings=[bldg(500, 500, kind="burakumin", w=38, h=26), bldg(500 + 19 + 17 + 61, 500, kind="laborer", w=34, h=24)])
    assert "burakumin_quarter_segregated" not in f(M)


def test_bund_beans_on_bunds_fires_on_a_bead_buried_by_a_later_plot():
    # a bead on the host's east bund (x=400) sits 100px inside the filler, which paints after
    # its host - the bund stroke under it is not visible ground on the finished map
    assert "bund_beans_on_bunds" in f(_bb_M([[400, 300]], [_BB_HOST, _BB_FILLER]))


def test_bund_beans_on_bunds_fires_on_a_bead_in_open_ground():
    # a bead near no bund at all (the bare fan floor)
    assert "bund_beans_on_bunds" in f(_bb_M([[700, 700]], [_BB_HOST, _BB_FILLER]))


def test_bund_beans_on_bunds_passes_beads_on_visible_bunds():
    # the host's west bund (x=200) stands clear of the filler; and a bead on the FILLER's own
    # west bund (x=300), though it lies deep inside the host, is legal - the filler paints
    # last, so its stroke is the visible one and the bead reads as sitting on that seam
    assert "bund_beans_on_bunds" not in f(_bb_M([[200, 300], [300, 300]], [_BB_HOST, _BB_FILLER]))


def test_bund_beans_on_bunds_skips_manifests_without_the_recording():
    # pre-2026-08-15 manifests record no plot_rings; regeneration adds them (the recording is
    # unconditional at the one draw site - see test_draw_comb_field_records_rings_and_beads)
    assert "bund_beans_on_bunds" not in f(_bb_M([[400, 300]], []))


def test_bund_beans_on_bunds_survives_geometry_far_off_the_canvas():
    # negative fixtures carry deliberately insane geometry; the index box is clamped to the
    # canvas on insert, so an off-map ring is skipped (it is not visible ground - a bead
    # claiming to sit on it still fires) instead of allocating billions of grid cells
    assert "bund_beans_on_bunds" in f(_bb_M([[9000000, 300]], [[[8999900, 200], [9000100, 200], [9000100, 400], [8999900, 400]]]))


def test_bund_beans_on_bunds_fires_on_a_bead_under_the_ditch_nets_stroke():
    # the ditch net draws LATE - over bund and bead alike - so a bead inside a late stroke's
    # drawn band is buried ink: the record attests a bead nobody can see
    M = {**_bb_M([[200, 300]], [_BB_HOST]), "drawn_channels": [{"pts": [[200, 180], [200, 420]], "late": True, "w0": 8.0, "w1": 8.0}]}
    assert "bund_beans_on_bunds" in f(M)


def test_bund_beans_on_bunds_ignores_early_water_and_the_banks():
    # a non-late stroke composites UNDER the plots, so it cannot bury a bead; a 1-point stroke
    # is unpaintable; and a bead 5px off an 8px stroke's centerline rides the BANK, not the water
    M = {
        **_bb_M([[200, 300]], [_BB_HOST]),
        "drawn_channels": [
            {"pts": [[200, 180], [200, 420]], "late": False, "w0": 8.0, "w1": 8.0},
            {"pts": [[205, 180]], "late": True, "w0": 8.0, "w1": 8.0},
            {"pts": [[205, 180], [205, 420]], "late": True, "w0": 8.0, "w1": 8.0},
        ],
    }
    assert "bund_beans_on_bunds" not in f(M)


def test_bund_beans_on_bunds_fires_on_a_bead_in_pond_water():
    # the source pond and a pocket pond both paint water over the bead's ground; a degenerate
    # pond thinner than the tolerance cannot bury anything (the guard, not a verdict)
    assert "bund_beans_on_bunds" in f({**_bb_M([[200, 300]], [_BB_HOST]), "pond": [200, 300, 30, 20]})
    assert "bund_beans_on_bunds" in f({**_bb_M([[200, 300]], [_BB_HOST]), "field_ponds": [{"x": 200, "y": 300, "rx": 30, "ry": 20}]})
    assert "bund_beans_on_bunds" not in f({**_bb_M([[200, 300]], [_BB_HOST]), "pond": [200, 300, 1.5, 1.5]})


# ---- comb_floor_ends_at_the_collector: floor past the (flat-extended) drain line -------------
def _floor_M(outline, dd=90.0, fork=(400.0, 200.0), drain=None, gen="hamletgen"):
    """Fall straight down-screen (dd=90): u = x, f = y; the collector crosses the low side at
    y=800 (thin head at x=300, outfall at x=700), plus a main channel so the role filter is
    exercised on every run."""
    M = {
        "meta": {"scale": "hamlet", "down_deg": 90, "W": 1200, "H": 1200},
        "fields": [{**_field("f", 200, 200, 900, 900), "outline": outline, "down_deg": dd, "plot_rings": []}],
        "field_ditches": [
            {"poly": [[200, 250], [900, 250]], "role": "main", "field": "f", "w": 8.0, "w_tail": 3.0},
            drain or {"poly": [[300, 800], [700, 800]], "role": "drain", "field": "f", "w": 3.0, "w_tail": 12.0},
        ],
    }
    if fork:
        M["fields"][0]["fork"] = list(fork)
    if gen:
        M["meta"]["generated_by"] = gen
    return M


def _floor_f(M):
    return check_village.gate(M, verbose=False, only={"comb_floor_ends_at_the_collector"})


def test_comb_floor_fires_on_an_outline_vertex_below_the_collector_line():
    # inside the drain's u-span, 30 px down-fall of the interpolated line
    assert "comb_floor_ends_at_the_collector" in _floor_f(_floor_M([[300, 300], [700, 300], [500, 830]]))


def test_comb_floor_fires_on_the_needle_beyond_the_drains_thin_head():
    # the Mizuguchi shape: past the head end the boundary continues LEVEL, and the outline
    # dips 100 px below it - a bare needle no plot can ever occupy
    assert "comb_floor_ends_at_the_collector" in _floor_f(_floor_M([[250, 900], [700, 300], [300, 300]]))


def test_comb_floor_passes_when_the_outline_hugs_the_collector():
    assert "comb_floor_ends_at_the_collector" not in _floor_f(_floor_M([[300, 300], [700, 300], [700, 800], [300, 800]]))


def test_comb_floor_tolerates_the_drawn_water_width():
    # 12 px past the centerline is inside the 16 px tolerance (max drain halfw 6 + slack): the
    # outline's low edge IS the drain polyline, so near-line vertices must never fire
    assert "comb_floor_ends_at_the_collector" not in _floor_f(_floor_M([[300, 300], [700, 300], [500, 812]]))


def test_comb_floor_only_governs_comb_fans():
    # no `fork` = not a build_comb fan: a polder's floor legitimately runs past its inner ring
    # drain to the dike, so the rule cannot bind there
    assert "comb_floor_ends_at_the_collector" not in _floor_f(_floor_M([[300, 300], [700, 300], [500, 900]], fork=None))


def test_comb_floor_skips_a_field_with_no_outline():
    M = _floor_M([[300, 300], [700, 300], [500, 900]])
    del M["fields"][0]["outline"]
    assert "comb_floor_ends_at_the_collector" not in _floor_f(M)


def test_comb_floor_skips_legacy_maps():
    # no meta.generated_by = a legacy comb; it inherits the rule when converted (migration doctrine)
    assert "comb_floor_ends_at_the_collector" not in _floor_f(_floor_M([[300, 300], [700, 300], [500, 900]], gen=None))


def test_comb_floor_skips_a_degenerate_drain_poly():
    M = _floor_M([[300, 300], [700, 300], [500, 900]], drain={"poly": [[300, 800]], "role": "drain", "field": "f", "w": 3.0, "w_tail": 12.0})
    assert "comb_floor_ends_at_the_collector" not in _floor_f(M)


def test_comb_floor_ignores_another_fields_drain():
    M = _floor_M([[300, 300], [700, 300], [500, 900]])
    M["field_ditches"][1]["field"] = "other"
    assert "comb_floor_ends_at_the_collector" not in _floor_f(M)


def test_comb_floor_reads_the_map_fall_when_the_field_has_none():
    M = _floor_M([[300, 300], [700, 300], [500, 830]])
    del M["fields"][0]["down_deg"]
    assert "comb_floor_ends_at_the_collector" in _floor_f(M)


# ---- flooded_plots_read_as_basins: a pointed blue sliver reads as a pond -----------------------
def _basin_M(rings, flooded, gen="hamletgen"):
    M = {
        "meta": {"scale": "hamlet", "down_deg": 90, "W": 1200, "H": 1200},
        "fields": [{**_field("f", 200, 200, 900, 900), "plot_rings": rings}],
        "flooded_plots": flooded,
    }
    if gen:
        M["meta"]["generated_by"] = gen
    return M


def _basin_f(M):
    return check_village.gate(M, verbose=False, only={"flooded_plots_read_as_basins"})


_NEEDLE = [[300, 300], [500, 308], [500, 300]]  # ~2.3 deg apex
_STRIP = [[300, 400], [500, 400], [500, 418], [300, 418]]  # a bunded rectangle


def _cent(r):
    return [sum(p[0] for p in r) / len(r), sum(p[1] for p in r) / len(r)]


def test_flooded_basins_fires_on_a_pointed_blue_sliver():
    # the Sawada fan-seam capture: a needle apex carrying the water tint reads as a tiny pond
    assert "flooded_plots_read_as_basins" in _basin_f(_basin_M([_NEEDLE, _STRIP], [_cent(_NEEDLE)]))


def test_flooded_basins_passes_a_rectangular_flooded_strip():
    assert "flooded_plots_read_as_basins" not in _basin_f(_basin_M([_NEEDLE, _STRIP], [_cent(_STRIP)]))


def test_flooded_basins_gives_the_carve_its_borderline_band():
    # ~19.8 deg apex: demoted by the carve at 25 deg, but the gate holds its fire at 15 - a
    # borderline plot the carve let through must not false-fire
    mid = [[300, 500], [500, 572], [500, 500]]
    assert "flooded_plots_read_as_basins" not in _basin_f(_basin_M([mid], [_cent(mid)]))


def test_flooded_basins_skips_an_unmatched_centroid():
    # a tint record with no ring near it (a fill path with no recorded ring) is not judgeable
    assert "flooded_plots_read_as_basins" not in _basin_f(_basin_M([_STRIP], [[50.0, 50.0]]))


def test_flooded_basins_skips_a_manifest_with_no_tint_record():
    M = _basin_M([_NEEDLE], [_cent(_NEEDLE)])
    del M["flooded_plots"]
    assert "flooded_plots_read_as_basins" not in _basin_f(M)


def test_flooded_basins_skips_legacy_maps():
    assert "flooded_plots_read_as_basins" not in _basin_f(_basin_M([_NEEDLE], [_cent(_NEEDLE)], gen=None))
