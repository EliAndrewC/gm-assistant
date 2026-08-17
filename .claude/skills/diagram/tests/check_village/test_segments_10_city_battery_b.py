"""Split from test_checks.py by feature 025 - see tests/check_village/CLAUDE.md for the index."""

from l7r.diagram import check_village
from tests.check_village._builders import (
    _CITY_WALL,
    _CITY_WALL_SMALL,
    _RING,
    WALL,
    WALLSQ,
    _cap_gov,
    _city_estates,
    _estate_city,
    _fort_city,
    _haz_base,
    _n_temples,
    _on_ring_bldg,
    _ring_city,
    _temple_city,
    _ward006,
    _ward_city,
    _ward_residents_city,
    _ward_servant_city,
    bldg,
    f,
    manifest,
)


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


def test_city_has_ring_road_fires_when_missing():
    assert "city_has_ring_road" in f(_fort_city())


def test_city_has_ring_road_passes_when_present():
    assert "city_has_ring_road" not in f(_fort_city(ring_road=_RING))


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


# --- city_graveyard_clear_of_ring_road (burial grounds keep off the ring's FULL drawn width) ---
def test_city_graveyard_clear_of_ring_road_fires_inside_the_eaves_forgiveness():
    # the Tango gap: a NARROW city-scale ring (20ft = ~6.7px) with a graveyard edge 2px off the
    # centerline - deep inside the drawn bed, but ring_road_kept_clear's (width - 6) / 2 forgiven
    # bed collapses to ~0.33px and waves it through; the graveyard check must still fire
    M = _fort_city(ring_road=_RING, ring_road_width=20 / 3, cemeteries=[{"x": 218, "y": 500, "w": 40, "h": 30, "rot": 0}])
    fails = f(M)
    assert "city_graveyard_clear_of_ring_road" in fails
    assert "ring_road_kept_clear" not in fails  # the gap this check exists to close


def test_city_graveyard_clear_of_ring_road_fires_on_a_mausoleum():
    M = _fort_city(ring_road=_RING, ring_road_width=15, mausoleums=[{"x": 760, "y": 500, "w": 44, "h": 32, "rot": 0}])
    assert "city_graveyard_clear_of_ring_road" in f(M)


def test_city_graveyard_clear_of_ring_road_passes_when_clear():
    M = _fort_city(ring_road=_RING, ring_road_width=20 / 3, cemeteries=[{"x": 210, "y": 500, "w": 40, "h": 30, "rot": 0}])
    assert "city_graveyard_clear_of_ring_road" not in f(M)


def test_city_graveyard_clear_of_ring_road_passes_without_a_ring():
    assert "city_graveyard_clear_of_ring_road" not in f(_fort_city(cemeteries=[{"x": 240, "y": 500, "w": 40, "h": 30, "rot": 0}]))


def test_city_multi_temple_exception_fires_on_a_third_temple_with_nothing_declared():
    """religion-and-death.md has always said >2 major temples is the MARKED exception, but until
    feature 016 nothing enforced it - a city could draw six temples and ship green."""
    M = _temple_city(_n_temples(3))
    assert "city_multi_temple_exception_declared" in f(M)


def test_city_multi_temple_exception_passes_once_a_recognized_reason_is_declared():
    M = _temple_city(_n_temples(3))
    M["meta"]["temple_exception"] = "changed_hands"
    assert "city_multi_temple_exception_declared" not in f(M)


def test_city_multi_temple_exception_passes_for_the_fox_eight_precinct_program():
    M = _temple_city(_n_temples(8))
    M["meta"]["temple_exception"] = "fox_structure"
    assert "city_multi_temple_exception_declared" not in f(M)


def test_city_multi_temple_exception_rejects_an_unrecognized_reason():
    """A fixed vocabulary, not free text: an unrecognized reason must FAIL rather than pass by
    virtue of being non-empty, or the declaration stops meaning anything."""
    M = _temple_city(_n_temples(3))
    M["meta"]["temple_exception"] = "because the GM said so"
    assert "city_multi_temple_exception_declared" in f(M)


def test_city_multi_temple_exception_leaves_the_ordinary_two_temple_city_alone():
    M = _temple_city(_n_temples(2))
    assert "city_multi_temple_exception_declared" not in f(M)


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


def test_city_samurai_estates_vary_in_size_fires_when_uniform():
    estates = [{"x": x, "y": y, "w": 100, "h": 80} for x, y in [(880, 600), (900, 880), (620, 880)]]  # 3 (in range), spread apart, all identical
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "manors": estates}
    fails = f(M)
    assert "city_samurai_estates_vary_in_size" in fails
    assert "city_samurai_estates_outside" not in fails  # 3 IS in the 1-3 range
    assert "city_samurai_estates_dispersed" not in fails  # spread >= 200px apart


def test_city_samurai_estates_outside_fires_when_too_many():
    # 4 estates shown - more than the 1-3 a city map should show (the rest are dispersed off-map, miles out)
    estates = [{"x": x, "y": y, "w": 90 + i * 6, "h": 60} for i, (x, y) in enumerate([(880, 560), (900, 820), (620, 880), (860, 700)])]
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "manors": estates}
    assert "city_samurai_estates_outside" in f(M)


def test_city_samurai_estates_dispersed_fires_on_a_tight_cluster():
    # 3 estates packed together (< 200px apart) - a cluster ringing the wall, not dispersed country seats
    estates = [{"x": x, "y": y, "w": 90 + i * 6, "h": 60} for i, (x, y) in enumerate([(860, 840), (900, 900), (960, 870)])]
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "manors": estates}
    fails = f(M)
    assert "city_samurai_estates_dispersed" in fails
    assert "city_samurai_estates_outside" not in fails  # 3 is a valid count; it is the CLUSTERING that fires


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


def test_city_pond_clear_of_wall_moat_fires():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "pond": [800, 500, 60, 40]}  # ellipse straddling the right wall edge
    assert "city_pond_clear_of_wall_moat" in f(M)


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


def test_city_estate_gates_vary_fires_when_all_identical():
    assert "city_estate_gates_vary" in f(_city_estates(["west"] * 5))


def test_city_estate_gates_vary_passes_when_mixed():
    assert "city_estate_gates_vary" not in f(_city_estates(["south", "west", "north", "south", "west"]))


# ---- overlap rules (2026-07-13): gate towers, ward fence, kido on fence -------------------
def test_city_gate_towers_clear_of_gate_furniture():
    wall = _CITY_WALL_SMALL
    base = {
        "meta": {"scale": "city", "walled": True},
        "wall": wall,
        "gates": [[500, 200]],
        "gate_structs": [{"x": 500, "y": 230, "w": 40, "h": 40, "kind": "tower"}, {"x": 560, "y": 230, "w": 60, "h": 44, "kind": "inspection"}],
    }
    assert "city_gate_towers_clear_of_gate_furniture" not in f(base)  # 60px apart, clear
    over = {**base, "gate_structs": [{"x": 500, "y": 230, "w": 40, "h": 40, "kind": "tower"}, {"x": 530, "y": 230, "w": 60, "h": 44, "kind": "inspection"}]}
    assert "city_gate_towers_clear_of_gate_furniture" in f(over)  # 30px -> footprints overlap


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


def test_granary_stores_are_solid_structs_for_every_keep_clear_rule():
    """A granary's kura are solid buildings like any other, but the manifest nests them under
    M['granary']['stores'] instead of a top-level list key, so the _OVERLAP_STRUCTS loop cannot
    reach them - solid_structs splices them in by hand. This holds that splice: without it a
    tax granary could be built across the patrol road and nothing would say so."""
    M = _haz_base()
    M["ring_road"] = [[400, 500], [600, 500]]
    M["granary"] = {"x": 500, "y": 500, "w": 60, "h": 40, "stores": [{"x": 500, "y": 500, "w": 18, "h": 14, "rot": 0}]}
    assert "ring_road_kept_clear" in f(M)
    M["granary"]["stores"][0]["y"] = 300  # ...and off the lane it is fine
    assert "ring_road_kept_clear" not in f(M)


def test_city_samurai_ward_residents_only_fires_on_commoners_inside_the_ward():
    # the Minami defect (GM 2026-08-02) in synthetic form: commoner dwellings/commerce standing
    # on the samurai side of the ward fence
    for kind in ("laborer", "merchant_house", "shop", "burakumin"):
        assert "city_samurai_ward_residents_only" in f(_ward_residents_city(bldg(600, 600, kind=kind)))


def test_city_samurai_ward_residents_only_passes_residents_and_outsiders():
    # samurai + their live-in servant inside; a laborer OUTSIDE the fence; a monk_house inside
    # (a temple's clergy row may stand in the ward - Tango's Bishamon precinct)
    M = _ward_residents_city(bldg(600, 600, kind="samurai"), bldg(620, 660, kind="servant"), bldg(200, 200, kind="laborer"), bldg(700, 700, kind="monk_house"))
    assert "city_samurai_ward_residents_only" not in f(M)


def test_city_samurai_ward_residents_only_skips_unnamed_wards_and_degenerate_geometry():
    # legacy ward records carry no name - nothing to adjudicate against
    M = manifest(wall=WALL, wall_stroke=11.0, gates=[[500, 50], [500, 950]], wards=[{"boundary": [[400, 945], [400, 400], [945, 400]], "stroke": 5.0}], buildings=[bldg(600, 600, kind="laborer")])
    M["meta"].update(scale="city", walled=True)
    assert "city_samurai_ward_residents_only" not in f(M)
    # and a fence/wall too degenerate to close yields no interior at all
    assert check_village._ward_interior([[400, 400]], WALL) is None
    assert check_village._ward_interior([[400, 945], [400, 400]], []) is None
    # a "ring" of coincident points has zero perimeter - nothing to walk an arc along
    assert check_village._ward_interior([[400, 945], [400, 400]], [[7, 7], [7, 7], [7, 7]]) is None


def test_city_ward_servants_housed_as_ranges_fires_on_a_freestanding_cottage():
    # the GM 2026-08-02 defect: barring the commoner kinds handed their ground to the servant
    # packs, and a detached servant cottage inside the fence reads as the fabric the fence excludes
    M = _ward_servant_city(bldg(600, 600, kind="samurai", w=19, h=13), bldg(700, 700, kind="servant", w=10, h=7))
    assert "city_ward_servants_housed_as_ranges" in f(M)


def test_city_ward_servants_housed_as_ranges_fires_when_detached_from_its_named_host():
    # it names a host, but stands 40px off it - service accommodation that serves nothing
    M = _ward_servant_city(bldg(600, 600, kind="samurai", w=19, h=13), bldg(700, 600, kind="servant", w=19, h=5, of=[600, 600]))
    assert "city_ward_servants_housed_as_ranges" in f(M)


def test_city_ward_servants_housed_as_ranges_fires_on_a_range_drawn_as_a_cottage():
    # abutting its host, but square - the nagaya read comes from the PROPORTION, not the position
    M = _ward_servant_city(bldg(600, 600, kind="samurai", w=19, h=13), bldg(613, 600, kind="servant", w=7, h=7, of=[600, 600]))
    assert "city_ward_servants_housed_as_ranges" in f(M)


def test_city_ward_servants_housed_as_ranges_passes_an_attached_range():
    # the shipped arrangement: a 19x5 range abutting its master's flank, flush with the frontage
    M = _ward_servant_city(bldg(600, 600, kind="samurai", w=19, h=13), bldg(619.6, 604, kind="servant", w=19, h=5, of=[600, 600]))
    assert "city_ward_servants_housed_as_ranges" not in f(M)
    # ...and a servant OUTSIDE the fence is none of this check's business
    M2 = _ward_servant_city(bldg(600, 600, kind="samurai", w=19, h=13), bldg(200, 200, kind="servant", w=10, h=7))
    assert "city_ward_servants_housed_as_ranges" not in f(M2)


def test_city_ward_servants_housed_as_ranges_skips_a_ward_that_cannot_be_closed():
    # a degenerate fence yields no interior polygon - nothing to adjudicate servants against
    M = _ward_servant_city(bldg(600, 600, kind="samurai", w=19, h=13), bldg(700, 700, kind="servant", w=10, h=7))
    M["wards"] = [{"name": "samurai", "boundary": [[400, 945]], "stroke": 5.0}]
    assert "city_ward_servants_housed_as_ranges" not in f(M)


def test_ring_road_kept_clear_fires_on_a_manor_and_runs_at_capital_scale():
    """Two stacked gaps (GM 2026-08-09, 'estates should not overlap with the ring-road'): manors
    are overlap TARGETS, so the registry-driven victim list never included them - and the whole
    check lived under scale=="city", so a capital never ran it at all. Four lineage estates stood
    on the capital's patrol road with a green gate."""
    M = _cap_gov()
    M["ring_road"] = [[100, 500], [900, 500]]
    M["ring_road_width"] = 15
    M["manors"][0]["x"], M["manors"][0]["y"] = 500, 500  # squarely on the patrol road
    assert "ring_road_kept_clear" in f(M)
