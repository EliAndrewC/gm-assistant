"""Gate checks for ponds, marshes, drainage, flow bands, the burakumin seam and the town battery (test_segments_08_town_and_fire split by feature 122; tests verbatim)."""

from tests.check_village._builders import (
    _FIELD_400,
    _POND_FEED,
    _drain,
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
    f,
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
