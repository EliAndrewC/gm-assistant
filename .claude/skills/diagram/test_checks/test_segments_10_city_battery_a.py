"""Split from test_checks.py by feature 025 - see test_checks/CLAUDE.md for the index."""

import math

from test_checks._builders import (
    _DIAMOND,
    _STAGE,
    WALLSQ,
    _block,
    _caste_city,
    _field,
    _fort_city,
    _gate_furn,
    _lanes,
    _martial_city,
    _merchant_city,
    _road_city,
    _samurai_varied_city,
    _tower,
    _unwalled_road_city,
    _ward_lane,
    _warren,
    _well_city,
    bldg,
    f,
)


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


def test_city_samurai_housing_sufficient_fires_when_too_few():
    # a 3,000-pop city is ~300 samurai (~60 households); ~10 token houses is far too few - it must
    # depict the bulk of the samurai cohort, not a handful (this was Tango's 22).
    sam = [bldg(300 + i * 12, 300, kind="samurai") for i in range(10)]
    M = {"meta": {"scale": "city", "walled": True, "population": 3000, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "buildings": sam}
    assert "city_samurai_housing_sufficient" in f(M)


def test_merchant_estates_match_roll_fires_when_drawn_undershoots_the_grant():
    # the seeded roll granted 2 compounds but only 1 was drawn (a stale hand count / short seat list)
    M = _merchant_city([bldg(300, 300, kind="merchant_house")], estates=[{"x": 500, "y": 600, "w": 62, "h": 46}])
    M["meta"]["merchant_estate_roll"] = 2
    assert "merchant_estates_match_roll" in f(M)


def test_merchant_estates_match_roll_passes_on_the_rolled_count_and_skips_unrolled_maps():
    M = _merchant_city([bldg(300, 300, kind="merchant_house")], estates=[{"x": 500, "y": 600, "w": 62, "h": 46}])
    M["meta"]["merchant_estate_roll"] = 1
    assert "merchant_estates_match_roll" not in f(M)
    M2 = _merchant_city([bldg(300, 300, kind="merchant_house")], estates=[{"x": 500, "y": 600, "w": 62, "h": 46}])
    assert "merchant_estates_match_roll" not in f(M2)  # no recorded roll (a hand-placed town) - skipped


def test_city_merchant_housing_varied_fires_when_uniform():
    # a merchant quarter of nothing but small uniform houses - no large houses, no walled estates
    M = _merchant_city([bldg(300 + i * 30, 300, kind="merchant_house") for i in range(10)])
    assert "city_merchant_housing_varied" in f(M)


def test_city_merchant_housing_varied_passes_with_a_mix():
    blds = [bldg(300 + i * 30, 300, kind="merchant_large") for i in range(4)] + [bldg(300 + i * 30, 400, kind="merchant_house") for i in range(6)]
    M = _merchant_city(blds, estates=[{"x": 500, "y": 600, "w": 78, "h": 58}])
    assert "city_merchant_housing_varied" not in f(M)


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


def test_city_imperial_road_has_commerce_generic_for_an_unwalled_city_fires_when_bare():
    # the rule applies to ANY city with an Imperial road, walled or not - here an unwalled one runs bare
    assert "city_imperial_road_has_commerce" in f(_unwalled_road_city([]))


def test_city_imperial_road_has_commerce_generic_for_an_unwalled_city_passes_when_lined():
    shops = [bldg(540, y, kind="shop") for y in range(260, 760, 60)]  # a commercial ribbon along the road
    assert "city_imperial_road_has_commerce" not in f(_unwalled_road_city(shops))


def test_city_lanes_meet_when_aligned_fires_through_the_gate():
    M = _lanes(streets=[[[500, 300], [500, 480]]], alleys=[[[500, 510], [500, 700]]], meta={"scale": "city"})
    assert "city_lanes_meet_when_aligned" in f(M)


def test_city_lanes_reach_ward_gates_fires_through_the_gate():
    M = _ward_lane(alleys=[[[500, 300], [500, 460]]], meta={"scale": "city"})
    assert "city_lanes_reach_ward_gates" in f(M)


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


def test_kido_aligned_with_ward_fence_fires_when_axis_aligned_on_a_slant_and_passes_when_rotated():
    # GM 2026-07-24 (live on both cities, frozen in pool/regressions/: Nagahara's ~159deg SW
    # ring-road kido, Tango's ~44deg S jog kido): the kido's roofed bar spans the gap IN the
    # fence, so it rotates with the local fence tangent; axis-aligned-on-a-slant is the defect.
    ward = [{"name": "w", "boundary": [[300, 300], [600, 600]], "z": 1, "wall_caps": []}]
    stamp = _fort_city(wards=ward, kido=[{"x": 450, "y": 450, "horizontal": True, "bbox": [430, 430, 470, 470]}])  # legacy flag: a 90deg gate on a 45deg fence
    assert "kido_aligned_with_ward_fence" in f(stamp)
    turned = _fort_city(wards=ward, kido=[{"x": 450, "y": 450, "rot": 45.0, "bbox": [430, 430, 470, 470]}])
    assert "kido_aligned_with_ward_fence" not in f(turned)
    free = _fort_city(wards=ward, kido=[{"x": 100, "y": 900, "horizontal": True, "bbox": [80, 880, 120, 920]}])  # far from any fence - nothing to align to
    assert "kido_aligned_with_ward_fence" not in f(free)


def test_kido_aligned_squares_to_the_lane_it_bars_not_the_oblique_fence_it_hangs_in():
    # GM 2026-07-26: a kido shuts a WAY, so where a lane runs through the seat the bar stands
    # SQUARE ACROSS THE LANE, and the fence meets it at whatever angle the fence runs. Tango's SW
    # ring-road gate followed its ~44deg fence jog while the road it barred ran at ~172deg - 38deg
    # off square to its own roadbed. Here: a 45deg fence, a HORIZONTAL street through the gate, so
    # the bar wants 90deg (vertical, across the street), NOT the fence's 45.
    ward = [{"name": "w", "boundary": [[300, 300], [600, 600]], "z": 1, "wall_caps": []}]
    street = [{"pts": [[300, 450], [600, 450]], "w": 18}]
    fenced = _fort_city(wards=ward, town_streets=street, kido=[{"x": 450, "y": 450, "rot": 45.0, "bbox": [430, 430, 470, 470]}])
    assert "kido_aligned_with_ward_fence" in f(fenced)  # square to the FENCE is now the defect, because a lane runs through
    squared = _fort_city(wards=ward, town_streets=street, kido=[{"x": 450, "y": 450, "rot": 90.0, "bbox": [430, 430, 470, 470]}])
    assert "kido_aligned_with_ward_fence" not in f(squared)
    # a street laid ALONGSIDE the fence is not something the gate bars, so it must not be what the
    # gate squares to - the fence tangent still rules there
    along = _fort_city(wards=ward, town_streets=[{"pts": [[300, 290], [600, 590]], "w": 18}], kido=[{"x": 450, "y": 450, "rot": 45.0, "bbox": [430, 430, 470, 470]}])
    assert "kido_aligned_with_ward_fence" not in f(along)


def test_kido_guard_box_clear_of_lanes_fires_when_the_watch_box_stands_in_the_roadbed():
    # GM 2026-07-26 (Tango's two ring-road ward gates): the gate's watch box is a small BUILDING on
    # the verge beside the way - the bar spans the road, the box does not stand in it. The whole
    # kido group is overlap-exempt (the bar must cross the lane and the fence), so this is the one
    # rule that protects the box, and it needs the box's own recorded footprint: the group bbox
    # cannot tell the bar from the shack.
    ward = [{"name": "w", "boundary": [[300, 450], [600, 450]], "z": 1, "wall_caps": []}]
    ring = [[200, 500], [800, 500]]
    inbed = _fort_city(wards=ward, ring_road=ring, ring_road_width=20, kido=[{"x": 450, "y": 450, "rot": 0.0, "bbox": [430, 430, 470, 510], "guard": [[440, 492], [460, 492], [460, 508], [440, 508]]}])
    assert "kido_guard_box_clear_of_lanes" in f(inbed)
    verge = _fort_city(wards=ward, ring_road=ring, ring_road_width=20, kido=[{"x": 450, "y": 450, "rot": 0.0, "bbox": [430, 430, 470, 470], "guard": [[440, 452], [460, 452], [460, 468], [440, 468]]}])
    assert "kido_guard_box_clear_of_lanes" not in f(verge)
    legacy = _fort_city(wards=ward, ring_road=ring, ring_road_width=20, kido=[{"x": 450, "y": 450, "rot": 0.0, "bbox": [430, 430, 470, 510]}])  # a manifest from before the box was recorded
    assert "kido_guard_box_clear_of_lanes" not in f(legacy)


def test_city_caste_shift_must_be_declared_documented_and_live():
    """GM 2026-08-05, on Minami: Fox temples hold much of the commerce that merchant houses conduct
    in other clans' cities, so its merchant households run about a third under the budgets.md share
    while the population is unchanged. The generic +/-30% band cannot tell that from drift - Minami
    was passing at a ratio of exactly 0.700, one household from a failure whose message would have
    said "mix is off" and taught the reader nothing. So the shift is DECLARED, with the same three
    obligations a waiver carries: it widens the band, it must give a real reason, and it must
    describe something that is actually happening.
    """

    def city(merchants, **extra):
        buildings = [
            {"x": 300 + 3 * i, "y": 300 + 3 * j, "w": 10, "h": 8, "rot": 0, "kind": kind}
            for j, (kind, n) in enumerate((("laborer", 40), ("servant", 20), ("merchant_house", merchants), ("samurai", 10), ("burakumin", 5)))
            for i in range(n)
        ]
        M = _fort_city(buildings=buildings)
        M["meta"].update({"population": 500, **extra})  # 100 households -> merchant target 25
        return M

    why = (
        "Fox temples hold much of the commerce that merchant houses conduct in other clans' cities, so merchant "
        "households run under the budgets.md share and hereditary temple families stand in their place."
    )
    assert "city_caste_counts_in_band" in f(city(15))  # 0.60 of target, undeclared - ordinary drift, fails
    assert "city_caste_counts_in_band" not in f(city(15, caste_shifts={"merchant": why}))  # ... declared, allowed
    assert "city_caste_counts_in_band" in f(city(9, caste_shifts={"merchant": why}))  # 0.36 - past even the declared band
    assert "city_caste_shifts_are_live" in f(city(25, caste_shifts={"merchant": why}))  # on target: the declaration is stale
    assert "city_caste_shifts_are_documented" in f(city(15, caste_shifts={"merchant": "by design"}))


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

    towers = [{"x": 500 + 300 * math.cos(i * math.pi / 5), "y": 500 + 300 * math.sin(i * math.pi / 5)} for i in range(10)]
    assert "city_wall_towers_spaced" not in f(_fort_city(wall_towers=towers))


def test_city_wall_towers_aligned_fires_when_axis_aligned_on_a_slanted_wall():
    M = _fort_city(wall=_DIAMOND, wall_towers=[{"x": 650, "y": 350, "rot": 0}, {"x": 350, "y": 650, "rot": 0}])
    assert "city_wall_towers_aligned" in f(M)


def test_city_wall_towers_aligned_passes_when_square_to_the_wall():
    # both towers sit on a 45 deg wall edge and are rotated 45 deg to match it
    M = _fort_city(wall=_DIAMOND, wall_towers=[{"x": 650, "y": 350, "rot": 45}, {"x": 350, "y": 650, "rot": 45}])
    assert "city_wall_towers_aligned" not in f(M)


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


def test_city_gate_furniture_at_throat_passes_when_hard_by_the_gate():
    # guard house + inspection station flanking the road right at each gate opening (~45px in)
    M = _fort_city(
        gate_structs=[
            {"x": 480, "y": 240, "w": 11, "h": 7, "kind": "guardhouse"},
            {"x": 520, "y": 240, "w": 15, "h": 7, "kind": "inspection"},
            {"x": 480, "y": 760, "w": 11, "h": 7, "kind": "guardhouse"},
            {"x": 520, "y": 760, "w": 15, "h": 7, "kind": "inspection"},
        ],
        inspection_stations=[{"x": 520, "y": 240, "w": 15, "h": 7}, {"x": 520, "y": 760, "w": 15, "h": 7}],
    )
    assert "city_gate_furniture_at_throat" not in f(M)


def test_city_gate_furniture_at_throat_fires_when_walked_back_along_the_wall():
    # the north-gate guard house (~85px) and inspection (~146px) walked back along the wall: the looser
    # 160/180px gate radii still PASS (no teeth), but the ~70px throat check catches the far placement
    M = _fort_city(
        gate_structs=[
            {"x": 440, "y": 260, "w": 11, "h": 7, "kind": "guardhouse"},
            {"x": 360, "y": 240, "w": 15, "h": 7, "kind": "inspection"},
            {"x": 480, "y": 760, "w": 11, "h": 7, "kind": "guardhouse"},
            {"x": 520, "y": 760, "w": 15, "h": 7, "kind": "inspection"},
        ],
        inspection_stations=[{"x": 360, "y": 240, "w": 15, "h": 7}, {"x": 520, "y": 760, "w": 15, "h": 7}],
    )
    fails = f(M)
    assert "city_gate_furniture_at_throat" in fails
    assert "city_inspection_station_at_each_gate" not in fails  # the loose radii wave the far placement through...
    assert "city_gate_has_guardhouse" not in fails  # ...which is exactly why the throat check exists


def test_city_gate_tower_at_its_gate_passes_when_the_tower_is_closest():
    # each gate's own tower (a gate_structs "tower") is the CLOSEST tower to its opening; mural bastions sit further
    M = _fort_city(
        gate_structs=[{"x": 500, "y": 280, "w": 17, "h": 10, "kind": "tower"}, {"x": 500, "y": 720, "w": 17, "h": 10, "kind": "tower"}],
        wall_towers=[{"x": 500, "y": 280, "w": 17, "h": 10}, {"x": 420, "y": 250, "w": 21, "h": 13}, {"x": 500, "y": 720, "w": 17, "h": 10}, {"x": 420, "y": 750, "w": 21, "h": 13}],
    )
    assert "city_gate_tower_at_its_gate" not in f(M)


def test_city_gate_tower_at_its_gate_fires_when_a_mural_is_closer():
    # the N gate's own tower is marooned out (dist 140) while a mural bastion sits closer (dist 90)
    M = _fort_city(
        gate_structs=[{"x": 500, "y": 340, "w": 17, "h": 10, "kind": "tower"}, {"x": 500, "y": 720, "w": 17, "h": 10, "kind": "tower"}],
        wall_towers=[{"x": 500, "y": 340, "w": 17, "h": 10}, {"x": 500, "y": 290, "w": 21, "h": 13}, {"x": 500, "y": 720, "w": 17, "h": 10}, {"x": 420, "y": 750, "w": 21, "h": 13}],
    )
    assert "city_gate_tower_at_its_gate" in f(M)


def test_city_merchant_housing_spread_fires_when_jammed():
    # merchant homes jammed as tight as the laborers (same ~16px spacing) - not more spread out
    homes = [bldg(300 + i * 16, 300, kind="merchant_house") for i in range(8)]
    labor = [bldg(300 + i * 16, 500, kind="laborer") for i in range(8)]
    assert "city_merchant_housing_spread" in f(_merchant_city(homes + labor))


def test_city_merchant_housing_spread_passes_when_roomier():
    homes = [bldg(300 + i * 44, 300, kind="merchant_house") for i in range(8)]  # 44px apart
    labor = [bldg(300 + i * 16, 500, kind="laborer") for i in range(8)]  # 16px apart (dense)
    assert "city_merchant_housing_spread" not in f(_merchant_city(homes + labor))


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
    assert "city_samurai_estates_outside" in fails  # 0 estates, want 1-3
    assert "city_imperial_road_through" in fails


def test_city_civic_amenity_checks_fire_on_an_empty_city():
    fails = f({"meta": {"scale": "city"}})
    for name in ("city_has_merchant_storehouses", "city_has_flophouse", "city_has_theater_stage"):
        assert name in fails


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


def test_city_martial_hall_is_required_exactly_once_and_inside_the_walls():
    # a provincial city is the first tier that supports a dojo at all, and the STATE hall is a
    # program item rather than a roll - exactly one, inside the rampart, in its own compound
    assert "city_has_martial_hall" not in f(_martial_city())
    assert "city_has_martial_hall" in f(_martial_city(halls=0))  # a county town has none; a city must
    assert "city_has_martial_hall" in f(_martial_city(halls=2))  # the state institution is singular
    assert "city_has_martial_hall" in f(_martial_city(hall_xy=(50, 500), sam_xy=(60, 520)))  # outside the wall


def test_city_martial_hall_keeps_a_full_length_archery_lane():
    # the lane covers the kyudo standard 28 m / 92 ft shot (floored at the ~90 ft clear lane the
    # Mode A azuchi uses); a lane shorter than that is not a shooting ground
    assert "city_martial_hall_has_archery_range" not in f(_martial_city(range_ft=100.0))
    assert "city_martial_hall_has_archery_range" not in f(_martial_city(range_ft=90.0))
    assert "city_martial_hall_has_archery_range" in f(_martial_city(range_ft=60.0))


def test_city_dojo_count_follows_the_samurai_cohort_formula():
    # GM formula 2026-07-25: 1 private dojo per full 200 samurai (a city's ~10% share) + a
    # remainder-fraction chance of one extra, floored at 1; a recorded roll must match the drawn
    # count. 2,000 -> 200 samurai -> exactly 1; 3,000 -> 300 -> 1 or 2; 4,000 -> 400 -> exactly 2.
    assert "city_dojo_count_follows_samurai" not in f(_martial_city(pop=2000, dojos=1))
    assert "city_dojo_count_follows_samurai" in f(_martial_city(pop=2000, dojos=2))
    assert "city_dojo_count_follows_samurai" not in f(_martial_city(pop=3000, dojos=1))
    assert "city_dojo_count_follows_samurai" not in f(_martial_city(pop=3000, dojos=2))
    assert "city_dojo_count_follows_samurai" in f(_martial_city(pop=3000, dojos=3))
    assert "city_dojo_count_follows_samurai" in f(_martial_city(pop=4000, dojos=1))
    assert "city_dojo_count_follows_samurai" in f(_martial_city(pop=3000, dojos=1, roll=2))  # stale hand count
    assert "city_dojo_count_follows_samurai" not in f(_martial_city(pop=3000, dojos=1, roll=1))


def test_city_dojos_stand_among_the_samurai_they_serve():
    # a dojo serves samurai and nobody else, so both the state hall and the private halls sit in
    # or against the samurai neighborhood - not out among the merchant rows or laborer warrens
    assert "city_dojos_among_samurai" not in f(_martial_city())
    assert "city_dojos_among_samurai" in f(_martial_city(dojo_xy=(830, 850)))  # a private hall adrift
    assert "city_dojos_among_samurai" in f(_martial_city(hall_xy=(830, 180)))  # the state hall adrift


def test_theater_stage_checks_run_per_stage_and_kind_gates_the_temple_rules():
    """List-shaped theater_stage (the post-clobber-fix record): every stage gets the clear
    check, but only a MONZEN (temple) stage owes temple adjacency - a machi-kind stage is the
    entertainment quarter's commercial theater and sits in the fabric, not at a hall."""
    far_machi = {"x": 500, "y": 500, "w": 190, "h": 120, "rot": 0, "kind": "machi"}
    hall = [{"x": 1200, "y": 1200, "w": 132, "h": 86, "rot": 0, "kind": "monastery"}]
    # EVERY stage owes its temple: the `machi` kind was briefly exempted on the research finding
    # that a capital's entertainment district is commercial, and the GM (2026-08-10) ruled the
    # older setting rule governs - a stage belongs to a hall whoever pays for the troupe.
    assert "theater_stage_by_temple" in f({"meta": {"scale": "town"}, "theater_stage": [far_machi], "religious": hall})
    far_monzen = dict(far_machi, kind="monzen")
    assert "theater_stage_by_temple" in f({"meta": {"scale": "town"}, "theater_stage": [far_monzen], "religious": hall})
    near = {"x": 1160, "y": 1080, "w": 190, "h": 120, "rot": 0, "kind": "machi"}
    assert "theater_stage_by_temple" not in f({"meta": {"scale": "town"}, "theater_stage": [near], "religious": hall})


def test_well_density_uses_a_higher_ceiling_for_outcast_rows():
    """GM 2026-08-10: a burakumin quarter at ~2x machi density cannot reach 1-per-20 without
    knotting 5-7 wellheads in one 150 ft radius. Historically those quarters were the last
    served by communal water, so they carry their own ceiling - but the REACH rule still binds."""
    base = {"meta": {"scale": "city", "walled": True, "W": 2000, "H": 2000, "ftpx": 3}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]]}
    well = [{"x": 500, "y": 500, "kind": None}]
    outcast = {**base, "wells": well, "buildings": [{"x": 480 + (i % 8) * 6, "y": 480 + (i // 8) * 6, "w": 8, "h": 6, "rot": 0, "kind": "burakumin"} for i in range(40)]}
    assert "city_well_density_sufficient" not in f(outcast)
    machi = {**base, "wells": well, "buildings": [{"x": 480 + (i % 8) * 6, "y": 480 + (i // 8) * 6, "w": 8, "h": 6, "rot": 0, "kind": "laborer"} for i in range(40)]}
    assert "city_well_density_sufficient" in f(machi)
    far = {
        **base,
        "wells": well,
        "buildings": [{"x": 740 + (i % 8) * 6, "y": 740 + (i // 8) * 6, "w": 8, "h": 6, "rot": 0, "kind": "burakumin"} for i in range(40)],
    }  # inside the wall, 340px+ from the only well
    assert "city_neighborhoods_have_wells" in f(far)  # the reach rule still binds on outcast rows
