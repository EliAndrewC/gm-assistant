"""Split from test_checks.py by feature 025 - see tests/check_village/CLAUDE.md for the index."""

import pytest

import check_village
from tests.check_village._builders import WALL, WALLSQ, _agri_city, _budget_city, _cap_gov, _cap_water, _capital_manifest, _door_city, _fort_city, _mest_city, _ring_towers, _scaled_city, bldg, f


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


def test_wall_towers_evenly_spaced_fires_on_a_doubled_tower():
    # a remediation-style tower squeezed 40px from its 100px-rhythm neighbor (the Tango east-curtain artifact)
    tw = _ring_towers(100) + [{"x": 240, "y": 200}]
    assert "wall_towers_evenly_spaced" in f(_fort_city(wall_towers=tw))


def test_wall_towers_evenly_spaced_passes_on_an_even_ring():
    assert "wall_towers_evenly_spaced" not in f(_fort_city(wall_towers=_ring_towers(100)))


def test_city_wall_tower_coverage_exempts_the_kido_keepclear_band():
    # a 300px tower hole in a dense 30px ring on the west curtain: mid-hole, points lose their 2nd tower
    # (garrison R ~121: the 2nd comes from 30px beyond a hole edge, so the thin band is y~441-559) and the
    # check fires - unless the hole is a recorded ward-junction keep-clear (wall_tower_keepclears), the
    # band placement itself refuses to tower (the kido chokepoint; check keep-outs mirror placement
    # keep-outs, same as the water-gate exemption)
    tw = [t for t in _ring_towers(30) if not (t["x"] == 200 and 350 < t["y"] < 650)]
    assert "city_wall_tower_coverage" in f(_fort_city(wall_towers=tw))
    assert "city_wall_tower_coverage" not in f(_fort_city(wall_towers=tw, wall_tower_keepclears=[[200, 500]]))


def test_city_wall_tower_coverage_fires_when_sparse():
    # only the 2 gate towers: the whole curtain between them sits out of flanking range of a 2nd tower
    M = _fort_city(wall_towers=[{"x": 500, "y": 200}, {"x": 500, "y": 800}])
    assert "city_wall_tower_coverage" in f(M)


def test_city_wall_tower_coverage_passes_when_densely_ringed():
    # a 60px-spaced ring keeps every curtain point within garrison range (328 ft / ~121 px) of >= 2 towers
    assert "city_wall_tower_coverage" not in f(_fort_city(wall_towers=_ring_towers(60)))


def test_city_wall_tower_coverage_siege_tier_demands_more_than_garrison():
    # the SAME 100px-spaced ring passes garrison (R~121) but fails siege (R~78, still >=2): the tier tightens it
    ring = _ring_towers(100)
    assert "city_wall_tower_coverage" not in f(_fort_city(wall_towers=ring))
    siege = _fort_city(wall_towers=ring)
    siege["meta"] = {**siege["meta"], "wall_defense": "siege"}
    assert "city_wall_tower_coverage" in f(siege)


def test_outside_fields_farmhouse_density_fires_on_a_bare_shown_field():
    # a field showing a long on-map edge (fully inside the canvas) but with NO farmhouses beside it:
    # a worked field carries farmhouses at ~village density on its shown portion. This is the partial-
    # field gap - the old per-field ">=2 anywhere" let an on-map field edge sit bare.
    field = {"name": "f1", "kind": "paddy", "bbox": [300, 300, 700, 700], "outline": [[300, 300], [700, 300], [700, 700], [300, 700]]}
    M = {"meta": {"scale": "town", "W": 1000, "H": 1000}, "fields": [field], "houses": []}
    assert "outside_fields_farmhouse_density" in f(M)


def test_outside_fields_farmhouse_density_passes_when_edge_is_a_tiny_sliver():
    # a field whose only on-map edge is a tiny corner (< 120px) is too small a sliver to require
    # farmhouses - its workers are off-map with the rest of the field. Must NOT fire.
    field = {"name": "f1", "kind": "paddy", "bbox": [-400, -400, 50, 50], "outline": [[-400, -400], [50, -400], [50, 50], [-400, 50]]}  # only a ~50x50 corner shows
    M = {"meta": {"scale": "town", "W": 1000, "H": 1000}, "fields": [field], "houses": []}
    assert "outside_fields_farmhouse_density" not in f(M)


def test_wells_troughs_rails_clear_of_each_other_fires_on_nagaharas_rail_across_its_well():
    # the real GM-caught defect (2026-07-25), verbatim geometry: an 18px rail laid straight over a
    # wellhead roof square AND over the trough cluster hugging it - three glyphs on one spot
    M = {
        "meta": {"scale": "city", "W": 2000, "H": 2000, "ftpx": 3},
        "stable_yards": [
            {
                "x": 1390,
                "y": 1020,
                "r": 72.0,
                "of": [1390, 1020],
                "troughs": 2,
                "troughs_at": [1388.8, 1018.7],
                "troughs_box": [1386.5, 1015.9, 1391.1, 1021.5],
                "rails": [{"x": 1386.0, "y": 1016.2, "tx": 1.0, "ty": 0.0, "len": 18.0, "reach": 2.4}],
            }
        ],
        "wells": [{"x": 1381.0, "y": 1019.0, "r": 8, "vr": 4.0}],
    }
    fails = f(M)
    assert "wells_troughs_rails_clear_of_each_other" in fails


def test_wells_troughs_rails_clear_of_each_other_fires_when_a_rail_reaches_a_NEIGHBOR_yards_troughs():
    # the cross-yard hole the dung-heap rule had to be widened for twice: two yards sit close
    # enough that yard A's rail lies over yard B's trough cluster - a pair no within-one-yard
    # loop would ever measure. Rail spans x 491-509; B's cluster starts at 503.7.
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000, "ftpx": 3},
        "stable_yards": [
            {"x": 480, "y": 500, "r": 72.0, "of": [480, 500], "troughs": 0, "rails": [{"x": 500, "y": 500, "tx": 1.0, "ty": 0.0, "len": 18.0, "reach": 2.4}]},
            {"x": 560, "y": 500, "r": 72.0, "of": [560, 500], "troughs": 2, "troughs_at": [506.0, 500.0], "troughs_box": [503.7, 497.2, 508.3, 502.8], "rails": []},
        ],
        "wells": [{"x": 512, "y": 500, "r": 8, "vr": 4.0}],
    }
    assert "wells_troughs_rails_clear_of_each_other" in f(M)


def test_wells_troughs_rails_clear_of_each_other_fires_on_two_wellheads_sunk_on_one_spot():
    # wells are placed by machinery that predates the yards entirely, so the rule has to cover the
    # well/well pair too - two roof squares 5px apart are one unreadable blob
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000, "ftpx": 3},
        "wells": [{"x": 800, "y": 800, "r": 8, "vr": 4.0}, {"x": 805, "y": 803, "r": 8, "vr": 4.0}],
    }
    assert "wells_troughs_rails_clear_of_each_other" in f(M)


def test_wells_troughs_rails_clear_of_each_other_passes_when_the_three_stand_side_by_side():
    # the rule is GLYPH-level, not a working clearance: the troughs are SUPPOSED to hug their well
    # (the bucket-pour relay) and animals stand between rail and trough, so a cluster 1.6px off the
    # roof square and a rail a short walk away are all correct. Near is right; on top of is not.
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000, "ftpx": 3},
        "stable_yards": [
            {
                "x": 500,
                "y": 500,
                "r": 72.0,
                "of": [500, 500],
                "troughs": 2,
                "troughs_at": [492.1, 500.0],
                "troughs_box": [489.8, 497.2, 494.4, 502.8],
                "rails": [{"x": 500, "y": 540, "tx": 1.0, "ty": 0.0, "len": 18.0, "reach": 2.4}],
                "dung_heaps": [],
            }
        ],
        "wells": [{"x": 500, "y": 500, "r": 8, "vr": 4.0}, {"x": 470, "y": 500, "r": 8, "vr": 4.0}],
    }
    assert "wells_troughs_rails_clear_of_each_other" not in f(M)


def test_poor_housing_mostly_interior_fires_when_laborers_on_the_street():
    M = {
        "meta": {"scale": "city", "walled": True},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "town_streets": [{"pts": [[250, 500], [750, 500]], "w": 18}],
        "buildings": [bldg(300 + i * 40, 512, kind="laborer") for i in range(8)],
    }  # all jammed ONTO the street
    assert "poor_housing_mostly_interior" in f(M)


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
    # an ~800-person district drawing 0.64 acre (200x140 ft) - ~2x the 0.15-0.30 acre district band, larger than a town's
    M = {"meta": {"scale": "village", "ftpx": 2}, "cemeteries": [{"x": 500, "y": 500, "w": 100, "h": 70, "rot": 0}]}
    assert "burial_grounds_sized_to_population" in f(M)
    # a 120x88 ft district ground (60x44px at 2 ft/px) = ~0.24 acre - in band
    ok = {"meta": {"scale": "village", "ftpx": 2}, "cemeteries": [{"x": 500, "y": 500, "w": 60, "h": 44, "rot": 0}]}
    assert "burial_grounds_sized_to_population" not in f(ok)


def test_burial_grounds_sized_to_population_fires_on_a_village_only_undersized_ground():
    # 60x40 ft (30x20px) = ~0.055 acre - sized as if the central village's ~350 buried alone; the ground
    # serves the whole ~800-person district (hamlets carry their urns here), so the 0.12 floor flags it
    M = {"meta": {"scale": "village", "ftpx": 2}, "cemeteries": [{"x": 500, "y": 500, "w": 30, "h": 20, "rot": 0}]}
    assert "burial_grounds_sized_to_population" in f(M)


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


@pytest.mark.parametrize(
    "frac,fires",
    [
        (1.00, False),  # exactly on budget
        (1.07, False),  # inside the +8% tolerance
        (0.96, False),  # inside the -5% tolerance
        (1.20, True),  # over-enclosed: the empty-space defect
        (0.80, True),  # the wall cannot hold the program
    ],
)
def test_capital_wall_matches_budget_fires_only_outside_the_declared_tolerances(frac, fires):
    fired = "capital_wall_matches_budget" in check_village.gate(_capital_manifest(interior_frac=frac))
    assert fired is fires


def test_capital_wall_matches_budget_reuses_the_provincial_tolerances():
    """Inherited deliberately - they are pinned by the shipped-Tango / rejected-Nagahara pair, and
    nothing about a capital argues for different slack."""
    assert check_village.BUDGET_TOL_OVER == 0.08
    assert check_village.BUDGET_TOL_UNDER == 0.05


def test_a_capital_that_declares_no_budget_FAILS_rather_than_skipping_the_conformance_check():
    """The FR-015 ratchet. Without it the map would skip capital_wall_matches_budget entirely and
    show green - and a check that never RUNS looks exactly like a check that passes."""
    failures = check_village.gate(_capital_manifest(budget=False))
    assert "capital_declares_a_budget" in failures
    assert "capital_wall_matches_budget" not in failures  # it has nothing to compare against


def test_a_capital_that_declares_a_budget_passes_the_ratchet():
    assert "capital_declares_a_budget" not in check_village.gate(_capital_manifest())


@pytest.mark.parametrize("scale", ["village", "town", "city"])
def test_neither_capital_check_runs_on_any_other_scale(scale):
    failures = check_village.gate(_capital_manifest(budget=False, scale=scale))
    assert "capital_declares_a_budget" not in failures
    assert "capital_wall_matches_budget" not in failures


def test_capital_has_six_ministries_fires_when_one_is_missing():
    M = _cap_gov()
    M["ministries"] = [m for m in M["ministries"] if m["name"] != "Ministry of War"]
    assert "capital_has_six_ministries" in f(M)


def test_capital_school_check_fires_when_absent():
    M = _cap_gov()
    M["ministries"] = [m for m in M["ministries"] if m["name"].startswith("Ministry of")]
    assert "capital_has_domain_school" in f(M)


def test_capital_chancellery_fires_when_a_compound_is_drawn():
    """The council of lineage representatives meets IN the castle (GM 2026-08-09, researched:
    Edo's Hyojosho/Roju within the castle, China's Grand Secretariat inside the palace) - a
    chancellery compound outside is the defect, not the requirement."""
    M = _cap_gov()
    M["ministries"].append({"x": 435, "y": 800, "w": 70, "h": 48, "name": "House Chancellery"})
    assert "capital_chancellery_meets_in_the_castle" in f(M)


def test_capital_domain_school_may_be_the_hanko_record():
    M = _cap_gov()
    M["ministries"] = [m for m in M["ministries"] if m["name"] != "Domain School"]
    M["martial_halls"] = [{"x": 565, "y": 800, "w": 80, "h": 50, "rot": 0, "label": "Domain School", "range_ft": 100, "kind": "hanko"}]
    fails = f(M)
    assert "capital_has_domain_school" not in fails
    assert "capital_school_on_the_axis" not in fails


def test_capital_castle_approach_fires_when_no_way_leaves_the_castle_gate():
    M = _cap_gov()
    M["roads"] = [{"pts": [[500, 700], [500, 1000]], "w": 26}]
    fails = f(M)
    assert "capital_castle_has_approach_avenue" in fails
    # ...and the checks that need the avenue SKIP rather than crash or misfire
    assert "capital_ministries_front_the_avenue" not in fails


def test_capital_ministries_front_the_avenue_fires_on_a_strayed_ministry():
    M = _cap_gov()
    war = next(m for m in M["ministries"] if m["name"] == "Ministry of War")
    war["x"], war["y"] = 850, 700  # off in the samurai ground, nowhere near the ote-suji
    assert "capital_ministries_front_the_avenue" in f(M)


def test_capital_school_on_the_axis_fires_when_it_strays():
    M = _cap_gov()
    sc = next(m for m in M["ministries"] if m["name"] == "Domain School")
    sc["x"] = 200  # far off the avenue's extended line
    assert "capital_school_on_the_axis" in f(M)


def test_capital_government_offices_dont_abut_fires_on_touching_offices():
    M = _cap_gov()
    works = next(m for m in M["ministries"] if m["name"] == "Ministry of Works")
    works["y"] = 455  # 5px above War's footprint - inside the 14px standoff
    assert "capital_government_offices_dont_abut" in f(M)


def test_capital_declares_lineages_fires_when_the_declaration_is_missing():
    """The FR-015 ratchet again: without the declaration every lineage check would SKIP while
    showing green, so the missing declaration is itself the failure."""
    M = _cap_gov()
    del M["meta"]["lineages"]
    fails = f(M)
    assert "capital_declares_lineages" in fails
    assert "capital_lineage_compounds_labeled" not in fails
    assert "capital_lineage_bands_visibly_distinct" not in fails


def test_capital_lineage_compounds_labeled_fires_on_a_missing_lineage():
    M = _cap_gov()
    M["manors"] = [m for m in M["manors"] if m.get("lineage") != "kurogi"]
    assert "capital_lineage_compounds_labeled" in f(M)


def test_capital_lineage_compounds_labeled_fires_on_an_unlabeled_compound():
    M = _cap_gov()
    M["manors"][0]["label"] = ""  # the compound stands but nothing names it
    assert "capital_lineage_compounds_labeled" in f(M)


def test_capital_ruling_lineage_gets_no_compound():
    M = _cap_gov()
    M["manors"][3]["lineage"] = "daika"
    M["manors"][3]["label"] = "Daika Estate"
    assert "capital_ruling_lineage_seat_is_the_castle" in f(M)


def test_capital_castle_without_a_gate_record_is_skipped_by_the_avenue_scan():
    M = _cap_gov()
    del M["castles"][0]["gate"]
    assert "capital_castle_has_approach_avenue" in f(M)  # no gate to anchor an avenue on


def test_capital_ruling_lineage_may_be_declared_in_the_band_map():
    """A gen may declare all nine lineages with bands, the ruling one among them - it is skipped
    rather than demanded a compound (its seat is the castle)."""
    M = _cap_gov()
    M["meta"]["lineages"] = {**M["meta"]["lineages"], "daika": "grand"}
    fails = f(M)
    assert "capital_lineage_compounds_labeled" not in fails
    assert "capital_ruling_lineage_seat_is_the_castle" not in fails


def test_capital_aqueduct_with_no_recorded_channel_is_skipped():
    M = _cap_water()
    M["aqueducts"] = [{"poly": [], "w": 8}]  # an empty channel - nothing to judge
    assert "capital_aqueduct_terminates_at_a_gate" not in f(M)


def test_capital_estate_labels_inside_fires_on_an_outside_caption():
    """A city estate's caption lives INSIDE its blank court (GM 2026-08-09) - hung outside it
    sits where 021's fabric must flow."""
    M = _cap_gov()
    M["labels"] = [[80, 120, 220, 136, 5, "Hazama Estate"]]  # above the walls, the old convention
    assert "capital_estate_labels_inside" in f(M)
    M["labels"] = [[110, 195, 190, 209, 5, "Hazama Estate"]]  # within the court
    assert "capital_estate_labels_inside" not in f(M)


def test_capital_lineage_bands_visibly_distinct_fires_on_a_band_size_collision():
    M = _cap_gov()
    kurogi = next(m for m in M["manors"] if m["lineage"] == "kurogi")
    kurogi["w"], kurogi["h"] = 145, 114  # numerically below the grand band, visually identical
    assert "capital_lineage_bands_visibly_distinct" in f(M)


def test_capital_waterfront_checks_pass_on_the_fixture():
    fails = f(_cap_water())
    for c in ("capital_has_aqueduct", "capital_aqueduct_terminates_at_a_gate", "capital_aqueduct_stays_outside_the_wall", "capital_no_road_parallels_river"):
        assert c not in fails, c


def test_capital_has_aqueduct_fires_when_absent():
    M = _cap_water()
    M["aqueducts"] = []
    assert "capital_has_aqueduct" in f(M)


def test_capital_aqueduct_terminates_at_a_gate_fires_far_from_any_gate():
    M = _cap_water()
    M["aqueducts"][0]["poly"][-1] = [1030, 800]
    assert "capital_aqueduct_terminates_at_a_gate" in f(M)


def test_capital_aqueduct_stays_outside_the_wall_fires_on_an_interior_channel():
    M = _cap_water()
    M["aqueducts"][0]["poly"].append([500, 500])  # an open cut through the walled interior
    assert "capital_aqueduct_stays_outside_the_wall" in f(M)


def test_capital_no_road_parallels_river_fires_on_a_shadowing_road():
    M = _cap_water()
    M["roads"] = [{"pts": [[1180, 0], [1180, 1000]], "w": 26}]  # a trunk road hugging the bank end to end
    assert "capital_no_road_parallels_river" in f(M)


def test_capital_no_road_parallels_river_passes_a_bridged_crossing():
    M = _cap_water()
    M["roads"] = [{"pts": [[900, 500], [1400, 500]], "w": 26}]  # ACROSS the river, not along it
    M["bridges"] = [{"x": 1200, "y": 500, "rot": 0, "span": 68, "w": 26}]
    assert "capital_no_road_parallels_river" not in f(M)
