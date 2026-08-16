"""Split from test_checks.py by feature 025 - see test_checks/CLAUDE.md for the index."""

import check_village
from tests.check_village._builders import (
    _CITY_WALL,
    _CITY_WALL_SMALL,
    _FULL_Q,
    _capital_manifest,
    _crop_map,
    _diamond_city,
    _dwell_grid,
    _farrier_map,
    _forge_map,
    _fuel_map,
    _gate_parts,
    _kiln_map,
    _mx_map,
    _pop_city,
    _qcity,
    bldg,
    f,
    garden,
    house,
    manifest,
    yard,
)


def test_a_paid_matrix_debt_fires_so_the_line_gets_deleted(monkeypatch):
    """An _MATRIX_OUTSTANDING line is WORK OWED. Once the defect is fixed the line does not just rot -
    it goes on tolerating that many real overlaps of that pair for ever. Minami's five were fixed
    while the entry recording them stayed behind."""
    monkeypatch.setitem(check_village._MATRIX_OUTSTANDING, "Nowhere", {("dry_plots", "manors"): 2})
    M = manifest(meta={"scale": "village", "ftpx": 1, "W": 1000, "H": 1000, "name": "Nowhere"})
    assert "matrix_debts_still_owed" in f(M)  # the map draws neither, so the debt is paid


def test_an_unpaid_matrix_debt_stays_quiet(monkeypatch):
    monkeypatch.setitem(check_village._MATRIX_OUTSTANDING, "Nowhere", {})
    M = manifest(meta={"scale": "village", "ftpx": 1, "W": 1000, "H": 1000, "name": "Nowhere"})
    assert "matrix_debts_still_owed" not in f(M)


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


def test_crop_hugs_content_reveals_only_a_band_of_a_canvas_filling_forest():
    # a wood drawn to the canvas edge is frame-setting only to FOREST_REVEAL_FT past its TREE LINE
    # (deeper in it is identical crowns), so a frame that stops there is snug, not "held open"...
    # (deeper in it is identical crowns), so a view opened 190px past the tree line is HELD OPEN
    M = {
        "meta": {"scale": "hamlet", "ftpx": 1, "W": 1000, "H": 500, "view": [150, 45, 550, 110]},
        "houses": [{"x": 200, "y": 100, "w": 40, "h": 30, "rot": 0, "kind": "plain"}],
        "forest": [[400, 0], [400, 500], [1000, 500], [1000, 0]],
        "forest_edge": [[400, 0], [400, 500]],
    }
    assert "crop_hugs_content" in f(M)
    assert "crop_hugs_content" not in f({**M, "meta": {**M["meta"], "view": [150, 45, 360, 110]}})  # snug: the reveal band exactly
    # a wood recorded WITHOUT its tree line keeps the legacy rule - the whole clamped polygon is
    # frame-setting, so the same wide view reads as snug
    assert "crop_hugs_content" not in f({**M, "forest_edge": None})


def test_crop_hugs_content_is_not_excused_by_a_forest_running_off_both_canvas_ends():
    # the wood's N-S tree line runs off BOTH ends of the canvas - it is running ALONG that axis, not
    # bounding anything, so it cannot excuse a frame held open to the canvas top (GM 2026-07-25: this
    # is what pinned Moritono's north edge 127px past the northernmost real content). The house is the
    # only vertical content, so a full-height view is loose and a snug one passes.
    M = {
        "meta": {"scale": "hamlet", "ftpx": 1, "W": 1000, "H": 500, "view": [150, 0, 360, 500]},
        "houses": [{"x": 200, "y": 300, "w": 40, "h": 30, "rot": 0, "kind": "plain"}],
        "forest": [[400, -10], [400, 510], [1000, 510], [1000, -10]],
        "forest_edge": [[400, -10], [400, 510]],
    }
    assert "crop_hugs_content" in f(M)
    assert "crop_hugs_content" not in f({**M, "meta": {**M["meta"], "view": [150, 255, 360, 90]}})


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


def test_guard_box_on_the_ward_fence_is_a_defect_though_the_gateway_on_it_is_not():
    # GM 2026-07-27: "ward gates seem to sometimes overlap with neighborhood walls". The GATEWAY
    # stands on the fence - the gate IS the opening. The guard box is a building on the verge and
    # rides no such permission, so a fence drawn through it is a defect.
    thru_gateway = {"meta": {"scale": "city"}, "kido": [_gate_parts()], "wards": [{"name": "samurai", "boundary": [[400, 300], [400, 700]]}]}
    assert not [v for v in check_village.matrix_violations(thru_gateway) if "kido_guard_box" in (v[0], v[1])]
    thru_box = {"meta": {"scale": "city"}, "kido": [_gate_parts()], "wards": [{"name": "samurai", "boundary": [[300, 520], [700, 520]]}]}
    assert [v for v in check_village.matrix_violations(thru_box) if "kido_guard_box" in (v[0], v[1])]
    assert "features_do_not_overlap" in f(thru_box)


def test_stable_troughs_beside_well_fires_when_the_cluster_is_far_from_every_well():
    # the pre-fix Nagahara defect: a trough cluster a real bucket-CARRY (>40 real ft) from every
    # well - watering is a relay at the wellhead, the bucket poured straight into the trough
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000, "ftpx": 3},
        "stable_yards": [{"x": 500, "y": 500, "r": 72.0, "of": [500, 500], "troughs": 2, "troughs_at": [530.0, 500.0]}],
        "wells": [{"x": 700, "y": 500, "r": 8, "vr": 4.0}],  # 170 px = 510 real ft from the cluster
    }
    assert "stable_troughs_beside_well" in f(M)


def test_stable_troughs_beside_well_fires_when_the_cluster_went_unrecorded():
    # troughs > 0 with no troughs_at: the anchor is part of the record's contract - an
    # unrecorded cluster cannot be validated, so it fails rather than passing silently
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000, "ftpx": 3},
        "stable_yards": [{"x": 500, "y": 500, "r": 72.0, "of": [500, 500], "troughs": 2}],
        "wells": [{"x": 505, "y": 500, "r": 8, "vr": 4.0}],
    }
    assert "stable_troughs_beside_well" in f(M)


def test_stable_troughs_beside_well_passes_beside_a_well_and_skips_troughless_yards():
    # a cluster hugging a wellhead (~24 real ft, the placement's own offset) passes; a yard that
    # drew no troughs (fully blocked ground) has nothing to anchor and is skipped
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000, "ftpx": 3},
        "stable_yards": [
            {"x": 500, "y": 500, "r": 72.0, "of": [500, 500], "troughs": 2, "troughs_at": [492.1, 500.0], "troughs_box": [489.8, 497.2, 494.4, 502.8]},
            {"x": 800, "y": 800, "r": 60.0, "of": [800, 800], "troughs": 0},
        ],
        "wells": [{"x": 500, "y": 500, "r": 8, "vr": 4.0}],  # 7.9 px = 24 real ft from the cluster
    }
    fails = f(M)
    assert "stable_troughs_beside_well" not in fails
    assert "stable_troughs_clear_of_buildings" not in fails  # box clear of the roof square too


def test_stable_troughs_clear_of_buildings_fires_when_a_trough_clips_a_well_roof():
    # the Tango caravan-ground defect: a 3-trough stack hugging its well on a near-vertical ray -
    # the box bottom reaches into the well-house roof square
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000, "ftpx": 3},
        "stable_yards": [{"x": 500, "y": 500, "r": 80.0, "of": [500, 500], "troughs": 3, "troughs_at": [502.0, 492.4], "troughs_box": [499.7, 487.8, 504.3, 497.0]}],
        "wells": [{"x": 500, "y": 500, "r": 8, "vr": 4.0}],  # roof top edge at y=496 < box bottom 497
    }
    assert "stable_troughs_clear_of_buildings" in f(M)


def test_stable_troughs_clear_of_buildings_fires_when_a_trough_clips_a_building():
    # the cluster is a bucket-pour from its well, but the drawn rects land on a building footprint
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000, "ftpx": 3},
        "stable_yards": [{"x": 500, "y": 500, "r": 72.0, "of": [500, 500], "troughs": 2, "troughs_at": [502.0, 492.4], "troughs_box": [499.7, 489.6, 504.3, 495.2]}],
        "wells": [{"x": 510, "y": 492, "r": 8, "vr": 4.0}],  # beside_well is satisfied
        "buildings": [{"x": 500, "y": 486, "w": 20, "h": 8}],  # footprint bottom at y=490 > box top 489.6
    }
    assert "stable_troughs_clear_of_buildings" in f(M)


def test_stable_troughs_clear_of_buildings_fires_when_the_box_went_unrecorded():
    # troughs > 0 with no troughs_box: the drawn extent is part of the record's contract
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000, "ftpx": 3},
        "stable_yards": [{"x": 500, "y": 500, "r": 72.0, "of": [500, 500], "troughs": 2, "troughs_at": [492.1, 500.0]}],
        "wells": [{"x": 500, "y": 500, "r": 8, "vr": 4.0}],
    }
    assert "stable_troughs_clear_of_buildings" in f(M)


def test_stable_yard_furniture_fires_when_a_rail_tip_reaches_the_road():
    # the center-only placement bug (GM 2026-07-24): rail center 12px off the road centerline
    # clears the ~4.3px tread, but the 18px rail's tip (len/2 + 2.4 post reach = 11.4) lands on it
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000, "ftpx": 3},
        "road": [[500, 0], [500, 1000]],
        "road_width": 8.667,
        "stable_yards": [
            {
                "x": 560,
                "y": 500,
                "r": 72.0,
                "of": [560, 500],
                "troughs": 0,
                "rails": [{"x": 512, "y": 500, "tx": 1.0, "ty": 0.0, "len": 18.0, "reach": 2.4}],
                "dung_heaps": [],
            }
        ],
    }
    assert "stable_yard_furniture_clear_of_roads_walls" in f(M)


def test_stable_yard_furniture_fires_when_a_dung_heap_lies_against_the_wall():
    # a heap whose drawn edge (rx 2.5) reaches inside the rampart's ~5px clearance stroke
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000, "ftpx": 3},
        "wall": [[100, 100], [900, 100], [900, 900], [100, 900]],
        "stable_yards": [
            {
                "x": 500,
                "y": 160,
                "r": 72.0,
                "of": [500, 160],
                "troughs": 0,
                "rails": [],
                "dung_heaps": [{"x": 500, "y": 106, "rx": 2.5, "ry": 1.8}],
            }
        ],
    }
    assert "stable_yard_furniture_clear_of_roads_walls" in f(M)


def test_stable_yard_furniture_passes_clear_and_skips_unrecorded_legacy_yards():
    # a rail 30px off the road and a heap in open ground pass; a legacy yard record with no
    # rails/dung_heaps keys (the pre-2026-07-24 pinned fixtures) is skipped, never retro-failed
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000, "ftpx": 3},
        "road": [[500, 0], [500, 1000]],
        "road_width": 8.667,
        "stable_yards": [
            {
                "x": 560,
                "y": 500,
                "r": 72.0,
                "of": [560, 500],
                "troughs": 0,
                "rails": [{"x": 530, "y": 500, "tx": 0.0, "ty": 1.0, "len": 18.0, "reach": 2.4}],
                "dung_heaps": [{"x": 585, "y": 520, "rx": 2.5, "ry": 1.8}],
            },
            {"x": 300, "y": 300, "r": 60.0, "of": [300, 300], "troughs": 0},
        ],
    }
    assert "stable_yard_furniture_clear_of_roads_walls" not in f(M)


def test_dung_heaps_clear_of_hitch_rails_fires_across_yards_within_24px():
    # round 2 (GM 2026-07-25): the heap sits 20px from a NEIGHBORING yard's rail - inside the
    # 24px floor, yet round 1's same-yard-only pairing (and its 14px floor) passed exactly this
    # shape (the real Nagahara round-2 capture: 16.4px same-yard, 22.5px cross-yard)
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000, "ftpx": 3},
        "stable_yards": [
            {
                "x": 400,
                "y": 500,
                "r": 72.0,
                "of": [400, 500],
                "troughs": 0,
                "rails": [],
                "dung_heaps": [{"x": 480, "y": 500, "rx": 2.5, "ry": 1.8}],
            },
            {
                "x": 560,
                "y": 500,
                "r": 72.0,
                "of": [560, 500],
                "troughs": 0,
                "rails": [{"x": 500, "y": 500, "tx": 0.0, "ty": 1.0, "len": 18.0, "reach": 2.4}],
                "dung_heaps": [],
            },
        ],
    }
    assert "dung_heaps_clear_of_hitch_rails" in f(M)


def test_dung_heaps_clear_of_hitch_rails_passes_at_24px_or_more():
    # the muck pile belongs NEAR the yard's working edge - 30px off the rail line is fine
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000, "ftpx": 3},
        "stable_yards": [
            {
                "x": 500,
                "y": 500,
                "r": 72.0,
                "of": [500, 500],
                "troughs": 0,
                "rails": [{"x": 500, "y": 500, "tx": 0.0, "ty": 1.0, "len": 18.0, "reach": 2.4}],
                "dung_heaps": [{"x": 530, "y": 500, "rx": 2.5, "ry": 1.8}],
            }
        ],
    }
    assert "dung_heaps_clear_of_hitch_rails" not in f(M)


def test_farrier_serves_a_stables_fires_on_a_forge_with_no_stables_in_reach():
    # a shoeing forge earns its own premises ONLY where horses concentrate (settlements.md
    # "TRADE WORKS" -> FARRIERY): the ordinary smith who also shoes stays inside the shop rows,
    # so a forge on a random street corner is the European coaching-inn image, not a Rokugani seat
    assert "farrier_serves_a_stables" in f(_farrier_map(800, 800))
    M = _farrier_map(800, 800)
    M["buildings"] = []  # ... and a map with NO stables at all fails the same way
    assert "farrier_serves_a_stables" in f(M)


def test_farrier_serves_a_stables_passes_beside_the_caravan_yard():
    # 250 real ft is the reach; at ftpx=1 a forge 120px off its stables is well inside it
    assert "farrier_serves_a_stables" not in f(_farrier_map(320, 200))


def test_farrier_keeps_fire_gap_fires_on_a_forge_against_the_stall_range():
    # an OPEN forge against a hay-and-timber stall range is the fire a stable yard does not
    # survive, so the smithy stands across the ground, never attached. Both an overlapping forge
    # and one merely crowding the wall are the same defect.
    assert "farrier_keeps_fire_gap" in f(_farrier_map(200, 200))  # squarely on top of the stables
    assert "farrier_keeps_fire_gap" in f(_farrier_map(200, 240))  # 5 ft of daylight - not enough


def test_farrier_keeps_fire_gap_passes_at_a_real_fire_gap():
    # ~6 real ft clear of every footprint (buildings.md's wooden-service fire gap) is the floor
    assert "farrier_keeps_fire_gap" not in f(_farrier_map(200, 250))


def test_city_has_farrier_fires_on_a_city_with_no_shoeing_forge():
    # a provincial city's gate caravan yard concentrates enough horses to keep a dedicated forge
    M = _farrier_map(320, 200, scale="city", walled=True)
    M["farriers"] = []
    M["wall"] = [[100, 100], [900, 100], [900, 900], [100, 900]]
    M["gates"] = [[500, 100]]
    assert "city_has_farrier" in f(M)


def test_imperial_road_town_farrier_is_gated_on_the_declaration():
    # the deliberate Hoshizora/Hirameki split: a relay/post town ON the Imperial Road works
    # courier and caravan horses hard enough to keep a forge; a market town off the road does not,
    # so the check is gated on meta(imperial_road=True) rather than on town scale alone
    M = _farrier_map(320, 200, imperial_road=True)
    M["farriers"] = []
    assert "imperial_road_town_has_farrier" in f(M)
    off_road = _farrier_map(320, 200)
    off_road["farriers"] = []
    assert "imperial_road_town_has_farrier" not in f(off_road)


def test_population_consistent_with_housing_fires_when_dwellings_too_few():
    # population is dwellings x5, not total buildings x5; 10 dwellings imply ~50 residents, not 3000
    M = {"meta": {"scale": "town", "walled": False, "population": 3000}, "buildings": [bldg(120 + i * 60, 120, kind="laborer") for i in range(10)]}
    assert "population_consistent_with_housing" in f(M)


def test_structures_clear_of_trees_fires_when_a_crown_is_drawn_over_a_building():
    # a tree drawn on a roof erases the building - no drawn crown may overlap any ROOFED footprint,
    # and a ROTATED building is covered conservatively by its half-diagonal (as at placement).
    base = manifest(meta={"scale": "town"}, houses=[bldg(300, 300, "laborer")])
    assert "structures_clear_of_trees" in f({**base, "buildings": [bldg(600, 600, "servant")], "tree_crowns": [618, 600, 8]})
    assert "structures_clear_of_trees" not in f({**base, "buildings": [bldg(600, 600, "servant")], "tree_crowns": [660, 600, 8]})
    # ... every roofed kind counts, not just dwellings (here a storehouse), and a crown that only
    # reaches the OPEN yard beside a building is fine - yards have their own sun rules
    assert "structures_clear_of_trees" in f({**base, "storehouses": [{"x": 800, "y": 800, "w": 40, "h": 30, "rot": 0}], "tree_crowns": [822, 800, 6]})
    assert "structures_clear_of_trees" not in f({**base, "threshing_yards": [yard(800, 800, of=(300, 300))], "tree_crowns": [800, 800, 6]})


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


def test_city_quarters_declared_fires_when_absent_passes_when_present():
    assert "city_quarters_declared" in f({"meta": {"scale": "city"}, "wall": _CITY_WALL_SMALL, "buildings": []})
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


def test_city_geometry_within_canvas_fires_on_a_stray_vertex():
    good = _qcity([{"poly": _FULL_Q, "zone": "residential", "kind": None, "name": "q"}], meta={"scale": "city", "W": 3200, "H": 2700})
    assert "city_geometry_within_canvas" not in f(good)
    bad = {
        "meta": {"scale": "city", "W": 3200, "H": 2700},
        "wall": _CITY_WALL_SMALL + [[9_000_000, 9_000_000]],
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


def test_crop_not_held_open_fires_on_a_lone_small_feature_far_out():
    # one 28px-tall building ~400px south of everything else: it alone makes the image taller
    M = _crop_map(buildings=[bldg(500, 500), bldg(540, 500), bldg(520, 900)])
    assert "crop_not_held_open_by_one_feature" in f(M)


def test_crop_not_held_open_spares_a_LARGE_outlying_feature():
    # a pond out on its own is the outlying CONTENT - big, and meant to be there. This is the
    # case that made the rule a RATIO rather than a flat gap (ponds measured 1.03-1.35x in the pool)
    M = _crop_map(pond=[520, 900, 200, 200])
    assert "crop_not_held_open_by_one_feature" not in f(M)


def test_crop_not_held_open_honors_the_declared_opt_out():
    M = _crop_map(buildings=[bldg(500, 500), bldg(540, 500), bldg(520, 900)])
    M["meta"]["crop_outlier_ok"] = True
    assert "crop_not_held_open_by_one_feature" not in f(M)


def test_charcoal_yard_keeps_fire_gap_fires_on_a_crowded_yard():
    """Charcoal self-heats: freshly-made charcoal absorbs oxygen fast enough to raise its own
    temperature to ignition, worst of all as tightly-packed fines. The hazard is therefore an
    UNATTENDED ignition inside a large fuel mass, which is why the gap (30 real ft, about one
    flame-height off a fully-involved stack) is an order above the attended-forge figure and well
    below the crematory's smell-carried-on-air figure."""
    tight = _fuel_map(houses=[house(500, 500 + 29 + 14 + 20)])  # 20 real ft off the yard
    clear = _fuel_map(houses=[house(500, 500 + 29 + 14 + 60)])  # 60 real ft off it
    assert "charcoal_yard_keeps_fire_gap" in f(tight)
    assert "charcoal_yard_keeps_fire_gap" not in f(clear)


def test_charcoal_yard_keeps_fire_gap_measures_in_REAL_feet_not_pixels():
    """The threshold converts through meta.ftpx, so 30 ft means the same distance at every tier -
    a pixel constant would silently become 90 ft on a 3 ft/px city sheet."""
    M = _fuel_map(houses=[house(500, 500 + 29 + 14 + 20)])
    M["meta"]["ftpx"] = 3  # the same PIXEL gap is now 60 real ft, which clears
    assert "charcoal_yard_keeps_fire_gap" not in f(M)


def test_charcoal_yard_has_cooling_ground_fires_on_a_covered_only_yard():
    """A yard with no open apron has nowhere to stand a fresh load apart from the conditioned
    stock, which is the documented handling rule (24 hours in the open; 8 days of air clears it).
    A roofed shed is equally required - the county's premium good is bought for a dry burn."""
    assert "charcoal_yard_has_cooling_ground" in f(_fuel_map(charcoal_yards=[{"x": 500, "y": 500, "w": 88, "h": 58, "rot": 0, "label": "charcoal yard", "sheds": 2}]))
    assert "charcoal_yard_has_cooling_ground" in f(_fuel_map(charcoal_yards=[{"x": 500, "y": 500, "w": 88, "h": 58, "rot": 0, "label": "charcoal yard", "sheds": 0, "apron": [0, 0, 30, 20]}]))
    assert "charcoal_yard_has_cooling_ground" not in f(_fuel_map())


def test_settlement_has_charcoal_yard_fires_only_when_the_district_is_declared():
    """Opt-in, like meta(granary=True): an ordinary county seat declares nothing and is exempt."""
    M = manifest(meta={"scale": "town", "ftpx": 1, "W": 1000, "H": 1000, "charcoal_district": True})
    assert "settlement_has_charcoal_yard" in f(M)
    del M["meta"]["charcoal_district"]
    assert "settlement_has_charcoal_yard" not in f(M)


def test_settlement_has_refining_forge_fires_only_when_the_district_is_declared():
    M = manifest(meta={"scale": "town", "ftpx": 1, "W": 1000, "H": 1000, "iron_district": True})
    assert "settlement_has_refining_forge" in f(M)
    del M["meta"]["iron_district"]
    assert "settlement_has_refining_forge" not in f(M)


def test_refining_forge_stands_off_dwellings():
    """A fining hearth is an OPEN fire under a forced blast, worked with a rod while the iron is
    semi-molten - the sparks, noise and smoke are the process, not a side effect. 60 real ft: half
    the crematory's nuisance figure (this does not rot), double the fuel stack's (this one is a
    live ignition source, but somebody is standing at it)."""
    close = _forge_map(homes=[(500, 500 + 24 + 14 + 30)])
    clear = _forge_map(homes=[(500, 500 + 24 + 14 + 70)])
    assert "refining_forge_stands_off_dwellings" in f(close)
    assert "refining_forge_stands_off_dwellings" not in f(clear)


def test_refining_forge_downwind_reads_the_maps_own_windward_declaration():
    """SMOKE goes downwind, FILTH goes downstream - two separate axes. This is the first: keyed off
    meta(windward=...), so a map with a different exposure gets a different answer instead of a
    hardcoded corner. Under the default NW monsoon the forge belongs SE of the housing."""
    homes = [(300, 300), (360, 300), (300, 360)]
    assert "refining_forge_downwind" not in f(_forge_map(700, 700, homes))  # SE of the housing
    assert "refining_forge_downwind" in f(_forge_map(60, 60, homes))  # NW of it - straight upwind
    # ...and reversing the declared wind reverses the verdict, which is the whole point of the knob
    assert "refining_forge_downwind" in f(_forge_map(700, 700, homes, windward="SE"))
    assert "refining_forge_downwind" not in f(_forge_map(60, 60, homes, windward="SE"))


def test_refining_forge_downwind_abstains_when_the_map_has_no_dwellings():
    """Nothing to smoke over, nothing to judge - the rule must not divide by an empty centroid."""
    assert "refining_forge_downwind" not in f(_forge_map(60, 60, ()))


def test_kiln_works_houses_its_workers_fires_on_a_lone_kiln():
    """The GM's question, 2026-07-27: "would whoever works the kiln also live next to it?" Yes, for
    three independent reasons - a firing is stoked in shifts for DAYS, the works stands at its CLAY
    rather than at its customers, and the trade was organized in kiln households living at their
    kilns (Song/Ming kiln districts first, Seto/Tokoname/Imado corroborating). So a kiln drawn as a
    lone glyph is recording a place nobody could work."""
    assert "kiln_works_houses_its_workers" in f(_kiln_map(quarters=()))
    assert "kiln_works_houses_its_workers" not in f(_kiln_map())


def test_kiln_keeps_fire_gap_fires_on_a_cottage_against_the_kiln():
    """The housing is not banished with the work, but it does keep the ordinary gap. 60 real ft is
    the ATTENDED-fire rung of the separation ladder, shared with the refining forge: a firing is a
    very large fire, but somebody is stoking it, so it does not belong with the UNATTENDED charcoal
    stack at 30 ft nor with the 120 ft figures that defend against a smell carried on air."""
    # kiln body bottom edge is at 470 + 8; cottage half-height is 9
    tight = _kiln_map(quarters=((500.0, 470 + 8 + 20 + 9),))
    clear = _kiln_map(quarters=((500.0, 470 + 8 + 70 + 9),))
    assert "kiln_keeps_fire_gap" in f(tight)
    assert "kiln_keeps_fire_gap" not in f(clear)


def test_kiln_keeps_fire_gap_also_measures_the_settlements_own_structures():
    """Not just the works' own cottages - the gap is owed to every footprint on the map. A works
    whose own quarters stand clear but which crowds a neighbor's house is the same hazard."""
    assert "kiln_keeps_fire_gap" in f(_kiln_map(houses=[house(500, 470 - 8 - 20 - 9)]))
    assert "kiln_keeps_fire_gap" not in f(_kiln_map(houses=[house(500, 470 - 8 - 70 - 9)]))


def test_kiln_keeps_fire_gap_fails_a_record_that_cannot_be_measured():
    """A record with no `body` FAILS rather than skipping. This file's standing hazard is that a
    check which never runs looks exactly like a check that passes - and a kiln whose body is not
    recorded is precisely a fire gap nobody can measure, which is the worse of the two states."""
    assert "kiln_keeps_fire_gap" in f(_kiln_map(body=None))


def test_kiln_keeps_fire_gap_measures_in_REAL_feet_not_pixels():
    """The threshold converts through meta.ftpx, so 60 ft means the same distance at every tier
    rather than silently becoming 180 ft on a 3 ft/px city sheet."""
    M = _kiln_map(quarters=((500.0, 470 + 8 + 20 + 9),), ftpx=3)  # the same PIXEL gap is now 60 real ft
    assert "kiln_keeps_fire_gap" not in f(M)


def test_kiln_keeps_fire_gap_is_measured_on_the_ROTATED_cottage():
    """The bug this guards: with the cottage recorded unrotated, a works turned on its side reports
    a gap that is wrong by the difference between the cottage's own width and height. Placed so the
    two readings straddle the 60 ft rule - the unrotated read passes and the true one fails."""
    # At rot=90 the body's drawn half-height is 23 (its 46 ft length now runs N-S), so its lower
    # edge is y=493; the cottage's is 14 read correctly and 9 read unrotated. y=564 therefore gives
    # a TRUE gap of 57 ft - which must fire - and a mis-read gap of 62 ft, which would not. Any
    # seat outside [562, 567) is read the same way by both and proves nothing; the first draft of
    # this test used one, passed under the revert, and was worthless.
    tight = _kiln_map(quarters=((500.0, 564.0),), rot=90.0)
    assert "kiln_keeps_fire_gap" in f(tight)


# ---- found by the settlement-review agent, 2026-07-26 -------------------------------------------
def test_manor_walls_clear_of_ways_fires_on_a_road_through_the_compound():
    """`manors` lives in _OVERLAP_TARGETS - the registry of things others must avoid - and never in
    _OVERLAP_STRUCTS, so the whole no_structure_on_* battery reads a manor as a hazard and nothing
    reads it as a candidate. The compound's own wall was ungoverned against the roadbed, and a trunk
    road ran 18 px inside a magistracy's south wall with the gate fully green."""
    M = manifest(meta={"scale": "town", "ftpx": 1, "W": 1200, "H": 1200})
    M["manors"] = [{"x": 600, "y": 300, "w": 290, "h": 200, "rot": 0, "label": "Magistrate's Manor"}]
    M["road"], M["road_width"] = [[0, 395], [1200, 395]], 26  # north edge 382, INSIDE the south wall at 400
    assert "manor_walls_clear_of_ways" in f(M)
    M["road"] = [[0, 460], [1200, 460]]  # north edge 447, clear of it
    assert "manor_walls_clear_of_ways" not in f(M)


def test_structures_stay_on_their_side_of_a_border():
    """A border is overlap-EXEMPT so a frontier compound may stand its WALL on the line - but that
    is not licence to build ACROSS it. The test is on the CENTER, which is exactly what keeps the
    deliberate case legal while catching a garden that wandered onto the neighbor's ground."""

    def bmap(*extra_buildings, **kw):
        M = manifest(meta={"scale": "town", "ftpx": 1, "W": 1200, "H": 1200})
        M["borders"] = [{"poly": [[900, 0], [900, 1200]], "label": "the Fox border"}]
        M["houses"] = [house(400, 400), house(460, 400), house(400, 460)]  # the settlement is WEST
        M.update(kw)
        M["buildings"] = list(extra_buildings)
        return M

    assert "structures_stay_on_their_side_of_a_border" not in f(bmap(bldg(600, 400)))
    assert "structures_stay_on_their_side_of_a_border" in f(bmap(bldg(1000, 400)))  # over the line
    # a garden or a yard counts too - it is our ground being claimed, not just our roofs
    assert "structures_stay_on_their_side_of_a_border" in f(bmap(gardens=[garden(1020, 500)]))
    # ...and a compound whose WALL sits on the line but whose CENTER is ours stays legal
    assert "structures_stay_on_their_side_of_a_border" not in f(bmap(manors=[{"x": 755, "y": 300, "w": 290, "h": 200, "rot": 0, "label": "M"}]))


def test_border_checks_abstain_when_there_is_no_border_or_no_housing():
    """A map with no drawn border has no side to be on, and one with no dwellings has no side to
    judge from - neither may raise a finding, and neither may crash."""
    M = manifest(meta={"scale": "town", "ftpx": 1, "W": 1200, "H": 1200}, buildings=[bldg(1000, 400)])
    assert "structures_stay_on_their_side_of_a_border" not in f(M)
    M["borders"] = [{"poly": [[900, 0], [900, 1200]], "label": "b"}]
    M["buildings"] = []
    assert "structures_stay_on_their_side_of_a_border" not in f(M)


def test_features_do_not_overlap_catches_a_crop_plot_in_a_watercourse():
    """The defect this feature was opened for, caught by the GENERAL rule with no pair-specific code."""
    plot = [[500, 500], [560, 500], [560, 560], [500, 560]]
    M = _mx_map(dry_plots=[{"poly": plot, "crop": "barley", "theta": 0}], streams=[{"poly": [[530, 400], [530, 700]], "w": 9}])
    assert "features_do_not_overlap" in f(M)
    M["streams"] = [{"poly": [[900, 400], [900, 700]], "w": 9}]  # moved clear
    assert "features_do_not_overlap" not in f(M)


def test_matrix_permits_an_annex_on_its_OWN_parent_only():
    """Strictly stronger than the blanket exemption it replaces: a kura behind its own shop is fine,
    the same kura drawn across a NEIGHBOR's building is a defect - which the blanket form could not
    express, and which the first pool run duly found twice."""
    own = _mx_map(buildings=[bldg(500, 500)], storehouses=[{"x": 500, "y": 512, "w": 20, "h": 14, "of": [500, 500]}])
    other = _mx_map(buildings=[bldg(500, 500), bldg(560, 500)], storehouses=[{"x": 556, "y": 500, "w": 20, "h": 14, "of": [500, 500]}])
    assert "features_do_not_overlap" not in f(own)
    assert "features_do_not_overlap" in f(other)


def test_matrix_permits_two_annexes_of_one_household_to_abut():
    M = _mx_map(
        houses=[house(500, 500)],
        threshing_yards=[yard(500, 540, of=(500, 500))],
        gardens=[garden(500, 552, of=(500, 500))],
    )
    assert "features_do_not_overlap" not in f(M)


def test_matrix_permits_a_ditch_on_its_own_field_but_not_another():
    M = _mx_map(
        fields=[
            {
                "name": "west",
                "kind": "paddy",
                "outline": [[400, 400], [700, 400], [700, 700], [400, 700]],
                "bbox": [400, 400, 700, 700],
                "vis_bbox": [400, 400, 700, 700],
                "plots": [[60, 60, 550, 550, 4, 4]],
            }
        ],
        field_ditches=[{"poly": [[550, 400], [550, 700]], "w": 1.5, "field": "west", "role": "main"}],
        houses=[house(551, 480)],
    )
    fails = f(M)
    assert "features_do_not_overlap" in fails  # the HOUSE is on the ditch, and it is nobody's annex


def test_every_feature_classified_for_matrix_is_the_ratchet(monkeypatch):
    """A drawn key with no class must fail BY NAME - the whole promise is 'add one line and you are
    protected', which only holds if forgetting the line is loud."""
    M = _mx_map(houses=[house(500, 500)])
    assert "every_feature_classified_for_matrix" not in f(M)
    monkeypatch.delitem(check_village.OVERLAP_CLASS, "houses")
    assert "every_feature_classified_for_matrix" in f(M)


def test_matrix_reads_drawn_extents_not_envelopes():
    """A commons is an ENVELOPE around a sparse scatter and is permissive besides, so it is never
    even extracted; testing envelopes is what made the motivating survey over-report ~2x."""
    M = _mx_map(commons=[{"x": 500, "y": 500, "w": 400, "h": 400, "rot": 0, "role": "grazing", "poly": [[300, 300], [700, 300], [700, 700], [300, 700]]}], houses=[house(500, 500)])
    assert "features_do_not_overlap" not in f(M)
    assert not [e for e in check_village.matrix_extents(M) if e[0] == "commons"]


def test_farmsteads_reach_their_fields_unsevered_fires_across_a_road():
    # every reachable field vertex lies across the road from the house -> severed (hoshizora's
    # lone south-of-road farmhouse inside the merchant block, GM 2026-08-02)
    field = {"name": "f1", "kind": "paddy", "bbox": [300, 550, 450, 650], "outline": [[300, 550], [450, 550], [450, 650], [300, 650]]}
    M = {
        "meta": {"scale": "town", "ftpx": 1, "W": 1000, "H": 1000},
        "fields": [field],
        "roads": [{"pts": [[0, 675], [1000, 675]], "w": 26}],
        "houses": [house(500, 700)],
    }
    assert "farmsteads_reach_their_fields_unsevered" in f(M)
    # a second field on the house's own side of the road un-severs it
    M["fields"].append({"name": "f2", "kind": "paddy", "bbox": [600, 700, 750, 800], "outline": [[600, 700], [750, 700], [750, 800], [600, 800]]})
    assert "farmsteads_reach_their_fields_unsevered" not in f(M)


def test_population_consistency_runs_at_capital_and_counts_terrace_units():
    """T006: the housing battery binds the capital too - and a terrace range houses `units`
    households under its one roof, so units count as dwellings toward the declared figure."""
    M = _capital_manifest()
    M["meta"]["population"] = 100
    assert "population_consistent_with_housing" in f(M)  # zero dwellings vs 100 declared
    M["terraces"] = [
        {"x": 300, "y": 300, "w": 108, "h": 7, "rot": 0, "units": 10, "z": 1},
        {"x": 600, "y": 300, "w": 108, "h": 7, "rot": 0, "units": 10, "z": 1},
    ]
    M["districts"] = [{"name": "castle foot", "kind": "terrace", "rank_band": "terrace", "poly": [[0, 0], [1000, 0], [1000, 1000], [0, 1000]]}]
    assert "population_consistent_with_housing" not in f(M)  # 20 units x 5 = 100


def test_capital_population_counts_yashiki_manors_and_outwall_samurai():
    """T006 arithmetic: the capital's declared figure covers the WHOLE cohort - yashiki-band
    households are manors (not buildings), and the out-wall 15% of the samurai cohort
    (CAPITAL_SAMURAI_INWALL_FRAC) are the capital's people too, unlike a provincial city's
    estate samurai (the Tango rule counts those rural)."""
    M = _capital_manifest()
    M["meta"]["population"] = 30
    M["districts"] = [{"name": "castle foot", "kind": "yashiki", "rank_band": "yashiki", "poly": [[0, 0], [1000, 0], [1000, 1000], [0, 1000]]}]
    M["manors"] = [{"x": 300, "y": 300, "w": 60, "h": 40, "label": "Hazama Estate"}, {"x": 500, "y": 300, "w": 60, "h": 40, "label": "Utsuro Estate"}]
    M["buildings"] = [
        {"x": 700, "y": 700, "w": 15, "h": 10, "kind": "samurai", "rot": 0},
        {"x": 1500, "y": 500, "w": 15, "h": 10, "kind": "samurai", "rot": 0},
        {"x": 720, "y": 740, "w": 12, "h": 9, "kind": "laborer", "rot": 0},
        {"x": 1500, "y": 900, "w": 12, "h": 9, "kind": "laborer", "rot": 0},
    ]
    M["terraces"] = [{"x": 400, "y": 700, "w": 36, "h": 7, "rot": 0, "units": 2, "z": 1}]
    # the capital census counts the WHOLE cohort, suburbs included: 2 manors + 2 samurai +
    # 2 laborers + 2 terrace units = 8 dwellings = 40 people (WHERE the out-wall pair may
    # stand is city_commoner_dwellings_inside_walls' business, not the census's):
    assert "population_consistent_with_housing" in f(M)  # declared 30 - off by two houses
    M["meta"]["population"] = 40  # ...and 40 closes the arithmetic exactly
    assert "population_consistent_with_housing" not in f(M)


def test_capital_civic_quarter_tolerates_ceremonial_breadth():
    """Research 021: the Corridor of a Thousand Steps is a vast open axis flanked by office
    files - a capital's civic band legitimately runs to 90% open where a provincial yamen
    precinct keeps 70%. Same manifest, city fires, capital does not."""
    base = {
        "wall": [[0, 0], [1000, 0], [1000, 1000], [0, 1000]],
        "quarters": [
            {"poly": [[100, 100], [400, 100], [400, 500], [100, 500]], "zone": "civic", "name": "civic quarter"},
            {"poly": [[400, 100], [900, 100], [900, 900], [100, 900], [100, 500], [400, 500]], "zone": "mixed"},
        ],
        "ministries": [{"x": 250, "y": 300, "w": 100, "h": 170, "name": "Ministry of Rites"}],  # ~14% built - clear of the capital tolerance, inside the city one
    }
    Mc = _capital_manifest()
    Mc.update({k: v for k, v in base.items()})
    assert "city_civic_quarter_not_mostly_open" not in f(Mc)
    Mp = _capital_manifest(scale="city")
    Mp.update({k: v for k, v in base.items()})
    assert "city_civic_quarter_not_mostly_open" in f(Mp)


def test_commoner_dwellings_at_the_wharf_suburb_are_exempt():
    """021, the kashi form: a bank-quay city keeps its landing OUTSIDE the wall and the
    brokers/warehouse folk live at it - a commoner dwelling within ~300px of the wharf works
    (jetty, dock, quay granaries) is the wharf suburb, not a defect. Beyond that reach the
    hard-zero rule stands."""
    M = _capital_manifest()
    M["buildings"] = [{"x": 1500, "y": 500, "w": 12, "h": 9, "kind": "merchant", "rot": 0}]
    assert "city_commoner_dwellings_inside_walls" in f(M)  # extramural, no wharf near
    M["jetties"] = [{"x": 1520, "y": 560, "rot": 0, "len": 13, "z": 1}]
    assert "city_commoner_dwellings_inside_walls" not in f(M)  # the same house IS the quay suburb


def test_placement_runs_meet_their_ask_fires_on_a_run_that_landed_short():
    """A placer that drops most of what it was asked for is authored-vs-landed drift, and the
    record _shortfall writes is only worth writing if something reads it back (the capital drew
    129 of 283 requested frontage seats behind a green gate)."""
    M = manifest()
    M["shortfalls"] = [{"by": "frontage", "at": [10, 10, 200, 10], "placed": 3, "wanted": 20, "dropped": "shop x17"}]
    assert "placement_runs_meet_their_ask" in check_village.gate(M, verbose=False)


def test_placement_runs_meet_their_ask_spares_a_run_that_missed_by_a_hair():
    """A row that seats all but a couple has met its ask - the two pool towns that record a
    shortfall at all (Ubame 21/23, Hirameki 13/14) are exactly this case and must stay green."""
    M = manifest()
    M["shortfalls"] = [{"by": "pack", "at": [10, 10, 200, 200], "placed": 21, "wanted": 23, "dropped": "servant x2"}]
    assert "placement_runs_meet_their_ask" not in check_village.gate(M, verbose=False)


def test_placement_runs_meet_their_ask_is_silent_when_the_ask_is_a_declared_budget():
    """fill=True means "place up to N" - the engine records no shortfall at all, so a district
    fill that seats a fraction of its budget is not drift and the check never sees it."""
    M = manifest()
    M["shortfalls"] = []
    assert "placement_runs_meet_their_ask" not in check_village.gate(M, verbose=False)


def test_waterworks_captions_stand_at_their_point():
    """A caption naming the intake weir, the settling basin or a sluice gate names a POINT the
    manifest records - so the check derives the subject instead of waiting for the gen to declare
    one. These captions are placed by hand with no referent, which is how they escaped both the
    standoff ladder and label_hugs_its_referent and ended up 195 and 348 ft from what they name."""
    M = manifest()
    M["aqueducts"] = [{"poly": [[100, 100], [300, 300]], "w": 3.0, "intake": [100, 100], "to": [300, 300]}]
    M["labels"] = [[900, 900, 980, 910, 5, "intake weir"]]
    assert "waterworks_captions_stand_at_their_point" in check_village.gate(M, verbose=False)


def test_waterworks_caption_beside_its_point_is_fine():
    """Beside it, not on it - a caption that touched its subject would read as part of the glyph."""
    M = manifest()
    M["aqueducts"] = [{"poly": [[100, 100], [300, 300]], "w": 3.0, "intake": [100, 100], "to": [300, 300]}]
    M["labels"] = [[104, 88, 170, 98, 5, "intake weir"]]
    assert "waterworks_captions_stand_at_their_point" not in check_village.gate(M, verbose=False)


def test_roadside_works_stand_on_their_road():
    """A doss-house exists to catch travelers off a particular road, and a kiln carts its fuel
    along one - so both stand on that way and lie along it. Nine flophouses on the capital came out
    level while their roads ran at 138-167 degrees, and one sat ~300 ft off the road entirely."""
    M = manifest()
    M["town_streets"] = [{"pts": [[100, 100], [900, 100]], "w": 18}]
    M["flophouses"] = [{"x": 500, "y": 130, "w": 34, "h": 15, "rot": 90, "label": "flophouse"}]
    assert "roadside_works_stand_on_their_road" in check_village.gate(M, verbose=False)


def test_roadside_work_lying_along_its_road_is_fine():
    M = manifest()
    M["town_streets"] = [{"pts": [[100, 100], [900, 100]], "w": 18}]
    M["flophouses"] = [{"x": 500, "y": 130, "w": 34, "h": 15, "rot": 0, "label": "flophouse"}]
    assert "roadside_works_stand_on_their_road" not in check_village.gate(M, verbose=False)


def test_a_kiln_carries_no_distance_rule_only_an_angle():
    """A nuisance works belongs OUT of town by its nature - the rule for it is alignment, not
    proximity (the pool's kilns sit 482-1517 ft from the nearest way, correctly)."""
    M = manifest()
    M["town_streets"] = [{"pts": [[100, 100], [900, 100]], "w": 18}]
    M["kilns"] = [{"x": 500, "y": 900, "w": 46, "h": 40, "rot": 0, "label": "kiln works"}]
    assert "roadside_works_stand_on_their_road" not in check_village.gate(M, verbose=False)


def test_manor_walls_fire_when_a_way_ENDS_inside_the_compound():
    """The _mw_gap helper returns 0.0 the moment a way SEGMENT ENDPOINT lies inside the wall
    rect - the crossing loop never runs. Before feature 022 this branch was only reached
    incidentally by regression fixtures' full-gate replays; the targeted replay no longer runs it
    there, so the branch gets the deterministic unit test it always deserved: a road DEAD-ENDING
    in the court is as illegal as one passing through."""
    M = manifest(meta={"scale": "town", "ftpx": 1, "W": 1200, "H": 1200})
    M["manors"] = [{"x": 600, "y": 300, "w": 290, "h": 200, "rot": 0, "label": "Magistrate's Manor"}]
    M["road"], M["road_width"] = [[0, 300], [600, 300]], 26  # terminates ON the manor center
    assert "manor_walls_clear_of_ways" in f(M)
