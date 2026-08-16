"""Split from test_checks.py by feature 025 - see test_checks/CLAUDE.md for the index."""

import json
import pathlib

import check_village
from test_checks._builders import _CITY_WALL_SMALL, _FULL_Q, _POND_OUTLIER, _SHRINE_GRAVEYARD_GROUP, _diamond_city, _dwell_grid, _lanes, _pop_city, _ward_lane, bldg


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


def test_gate_crop_advisory_can_be_silenced():
    M = {**_POND_OUTLIER, "meta": {"scale": "village", "view": [0, 0, 1400, 1000], "crop_advisory": False}}
    check_village.gate(M, verbose=True)  # meta(crop_advisory=False) -> the advisory block is skipped
    assert check_village.crop_relocatable_singletons(M)  # ... though the detector itself still finds it


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


def test_hikari_bishamon_precinct_no_longer_limits_the_crop():
    # the GM's actual case: Hikari-no-Sato's Bishamon shrine + its churchyard graveyard USED to sit at the far
    # SW, holding the S crop edge out ~200px over empty ground - the group advisory (proved by the synthetic
    # _SHRINE_GRAVEYARD_GROUP fixture above) flagged it. It has since been RELOCATED into the dry pocket below
    # the E block, so the shipped map's advisory is now SILENT. This guards against a regression that re-parks
    # the precinct (or any shrine group) where it needlessly limits the crop. See settlements.md 'Crop advisory'.
    here = pathlib.Path(__file__).parent.parent
    M = json.loads((here / "pool" / "villages" / "hikari-no-sato.json").read_text())
    assert check_village.crop_relocatable_singletons(M) == []


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


# ---- feature 006: reworked capacity verdict (usable residential ground + reserve) ------------
def test_city_capacity_counts_only_in_wall_dwellings():
    # extramural dwellings do not inflate the placed count
    wall = _CITY_WALL_SMALL
    inside = [bldg(300 + (i % 10) * 20, 300, "laborer") for i in range(20)]
    M = {"meta": {"scale": "city", "population": 100}, "wall": wall, "buildings": inside + [bldg(50, 500, "laborer")]}
    assert check_village.city_capacity(M)["placed"] == 20  # the outside one is not counted


def test_city_capacity_per_quarter_table_lists_residential_quarters():
    q = {"poly": _FULL_Q, "zone": "residential", "kind": None, "name": "warren"}
    civic = {"poly": [[600, 600], [790, 600], [790, 790], [600, 790]], "zone": "civic", "kind": None, "name": "yamen"}
    M = _pop_city(_dwell_grid(210, 560, 210, 560, 12), population=400, quarters=[q, civic])
    rep = check_village.city_capacity(M)
    names = {pq["name"] for pq in rep["per_quarter"]}
    assert "warren" in names and "yamen" not in names  # residential listed; pure civic not in the density table
