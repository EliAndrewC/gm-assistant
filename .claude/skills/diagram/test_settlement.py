#!/usr/bin/env python3
"""Unit tests for settlement.py methods/branches the pool generators don't exercise.

The five worked maps cover most of settlement.py; this file reaches the rest - a couple of
unused vocabulary methods (torii_path, forest/wall labels, polygon-based flower field) and a
few internal branches (degenerate segment, the road path of face-street rotation, the big->
plain ring fallback). Together with test_villages (which runs the gens in-process) this brings
settlement.py to 100%.

    python3 -m pytest test_settlement.py -q
"""
import os
import tempfile

import settlement
from settlement import Settlement


def _town():
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="T", scale="town")
    return s


def test_finish_writes_svg_json_and_renders_png():
    # finish() must pair a .png with the .svg automatically (the render step that used to be a
    # forgettable manual command); render=False writes only the source files.
    with tempfile.TemporaryDirectory() as d:
        base = os.path.join(d, "t")
        s = _town()
        s.finish(base, render=False)
        assert os.path.exists(base + ".svg") and os.path.exists(base + ".json")
        assert not os.path.exists(base + ".png")
        s.finish(base)                   # default render=True -> rsvg-convert produces the PNG
        assert os.path.exists(base + ".png")


def test_set_view_records_meta_and_crops_viewbox():
    # a city map crops tight to the walls: set_view records the window in meta (the checks read
    # it as the map edge) and finish() rewrites the SVG viewBox to that window. title/compass
    # follow the view so they stay on-canvas.
    with tempfile.TemporaryDirectory() as d:
        base = os.path.join(d, "t")
        s = Settlement(3000, 2000, seed=1)
        s.set_view(500, 400, 1000, 800)
        assert s.M["meta"]["view"] == [500, 400, 1000, 800]
        s.title("Edo")
        s.compass()
        s.finish(base, render=False)
        svg = open(base + ".svg").read()
        assert 'viewBox="500 400 1000 800"' in svg and 'viewBox="0 0 3000 2000"' not in svg


def test_mausoleum_yields_walls_to_abutting_ward_fences():
    # a wall that runs along a ward fence is re-stamped (the fence renders ON TOP - the wall runs
    # underneath); exercises both the horizontal- and vertical-fence branches of _ward_fence_cap
    s = Settlement(2000, 2000, seed=1)
    s.meta(name="C", scale="city")
    s.ward("a", [(400, 600), (900, 600)], [])            # horizontal fence at y=600
    s.mausoleum(600, 627, 54, 40, gate_dir="south")      # north wall y0=607 runs along it -> yields north
    assert s.M["mausoleums"][-1]["ward_walls"] == ["north"]
    s.ward("b", [(1200, 400), (1200, 900)], [])          # vertical fence at x=1200
    s.mausoleum(1227, 650, 54, 40, gate_dir="east")      # west wall x0=1200 runs along it -> yields west
    assert "west" in s.M["mausoleums"][-1]["ward_walls"]
    # a fence that is parallel + aligned but does NOT overlap the wall's extent -> no yield (both axes)
    s.ward("c", [(100, 200), (200, 200)], [])            # horizontal fence far left of...
    s.mausoleum(700, 227, 54, 40, gate_dir="south")      # ...this north wall (no x-overlap)
    assert "north" not in s.M["mausoleums"][-1]["ward_walls"]
    s.ward("d", [(1500, 100), (1500, 250)], [])          # vertical fence high above...
    s.mausoleum(1527, 650, 54, 40, gate_dir="east")      # ...this west wall (no y-overlap)
    assert "west" not in s.M["mausoleums"][-1]["ward_walls"]


def test_kido_records_ward_gates_in_both_orientations():
    s = Settlement(1000, 1000, seed=1)
    s.kido(500, 300, horizontal=True)        # E-W street gate
    s.kido(300, 500, horizontal=False)       # N-S street gate
    assert len(s.M["kido"]) == 2
    assert s.M["kido"][0]["horizontal"] and not s.M["kido"][1]["horizontal"]


def test_seg_closest_degenerate_segment():
    assert settlement.seg_closest(0, 0, (5, 5), (5, 5)) == (5, 5)


def test_torii_path_places_one_torii_per_interior_vertex():
    s = _town()
    s.torii_path([(0, 0), (50, 50), (100, 0)])
    assert len(s.M["torii"]) == 1


def test_torii_even_runs():
    s = _town()
    s.torii_even([(0, 0), (100, 0), (100, 100)], 4)
    assert len(s.M["torii"]) == 4


def test_face_street_rot_without_streets_and_with_a_road():
    s = _town()
    r, d = s._face_street_rot(500, 500)          # no streets at all
    assert r is None and d > 1e17
    s.M["road"] = [[100, 500], [900, 500]]        # the road branch
    r, d = s._face_street_rot(500, 480)
    assert r is not None and d < 100


def test_frontage_runs_out_of_items_mid_row():
    # rows=2 but a single item: the first row places it, the second row hits the `break` when
    # `items` is already empty (a multi-row frontage stub with an odd remainder).
    s = _town()
    s.frontage([(100, 500), (900, 500)], ["merchant"], rows=2)
    assert sum(1 for b in s.M["buildings"] if b["kind"] == "merchant") == 1


def test_granary_draws_a_storehouse_row():
    # opt-in rice-transit granary: a row of n fireproof kura, recorded for town_has_granary
    s = _town()
    stores = s.granary(500, 500, n=3)
    assert len(stores) == 3 and s.M["granary"]["n"] == 3 and s.M["granary"]["label"] == "granary"


def test_merchant_storehouses_attaches_behind_shops_and_skips_corridors():
    # a kura is tucked behind a merchant's shopfront (its back, opposite the awning) unless that
    # back would land on a street - then it is skipped. rot=0 -> awning faces +y, back faces -y.
    s = _town()
    s.street([(100, 470), (900, 470)], width=24)     # sits just behind shop A's back -> A skipped
    s.building(500, 500, 40, 28, "merchant", rot=0)   # back (-y) runs into the street corridor
    s.building(300, 800, 40, 28, "merchant", rot=0)   # back faces open ground -> kura attached
    n = s.merchant_storehouses(count=6)
    assert n == 1 and len(s.M["storehouses"]) == 1


def test_forest_patch_uses_default_label_position():
    s = _town()
    s.forest_patch([(100, 100), (300, 120), (320, 300), (110, 280)], label="copse")   # no label_xy -> default
    assert s.M["forest_patches"]


def test_wall_with_a_label():
    s = _town()
    s.wall([(100, 100), (200, 300), (150, 500)], label="rampart")
    assert s.M["wall"]


def test_flower_field_from_a_polygon_base():
    s = _town()
    s.flower_field([(100, 100), (300, 120), (320, 300), (110, 280)], "chrysanthemums", amp=10)
    assert s.M["flower_fields"]


def test_ring_big_falls_back_to_plain_when_capped():
    s = _town()
    s.paddy_field((200, 200, 600, 600), "", "f", amp=20)
    s.ring(("poly", s.field_polys[0]), 20, 30, ["big"], max_big=2)   # >2 'big' requests -> the rest become 'plain'
    assert sum(1 for h in s.M["houses"] if h["kind"] == "big") <= 2


def test_gapped_ring_merges_when_first_vertex_is_not_a_gate():
    # a closed wall ring whose FIRST vertex is not a gate: the run after the last gap must merge back
    # into the first, leaving one continuous subpath (not a spurious break at the start point)
    s = Settlement(1000, 1000, seed=1)
    ring = [(100, 100), (300, 100), (300, 300), (100, 300), (100, 100)]   # closed square
    d = s._gapped_ring(ring, [(300, 100)], gap=20, closed=True)           # one gate, at a NON-first vertex
    assert d.count("M") == 1


def test_wall_walk_crosses_multiple_edges():
    # walking further than one wall edge: the accumulate-and-step branch must carry across edges. A run
    # of short 50px edges, gate at index 4, walking 120px west crosses edges 4->3->2 to land at x=180.
    s = Settlement(1000, 1000, seed=1)
    pts = [(100, 100), (150, 100), (200, 100), (250, 100), (300, 100), (300, 150)]
    x, y, ang = s._wall_walk(pts, 4, 120, west=True)
    assert abs(x - 180) < 1e-6 and abs(y - 100) < 1e-6
    assert abs(ang - 180) < 1e-6   # the run is horizontal; walking west the edge points in -x


# --- farmsteads(): the deferred draw giving EVERY farmhouse a yard (nudge / drop / bound branches) -----
def test_try_place_defers_the_farmhouse():
    # try_place reserves + records the farmhouse but does NOT draw it yet (farmsteads draws it with its yard)
    s = _town()
    assert s.try_place(500, 500, "plain")
    assert len(s.M["houses"]) == 1 and len(s.M["threshing_yards"]) == 0   # deferred, no yard yet


def test_farmsteads_yard_on_the_sunny_south_front():
    s = _town()
    assert s.try_place(500, 500, "plain")
    assert s.farmsteads() == 1
    y = s.M["threshing_yards"][0]
    assert y["of"] == [500, 500] and y["y"] > 500   # the yard sits on the house's south/front (+y) side


def test_farmsteads_drops_a_farmhouse_with_no_yard_room():
    # a tiny bounding ring around the house leaves no room for a yard on any side (even nudged), so the
    # farmhouse is dropped - keeping the firm 100%-have-a-yard invariant. Exercises the bound, nudge-None,
    # and drop branches.
    s = _town()
    assert s.try_place(500, 500, "plain")
    s.bound = [(490, 490), (510, 490), (510, 510), (490, 510)]
    assert s.farmsteads() == 0
    assert s.M["houses"] == [] and s.M["threshing_yards"] == []


# --- dooryard kitchen garden: every farmstead also gets a saien on a sunny side --------------
def test_farmsteads_garden_on_a_sunny_side():
    s = _town()
    assert s.try_place(500, 500, "plain")
    assert s.farmsteads() == 1
    gd = s.M["gardens"][0]
    assert gd["of"] == [500, 500] and gd["y"] >= 500 - 5   # never the shady north back


def test_farmsteads_drops_a_farmhouse_with_no_garden_room():
    # a bound that admits the house + its south yard but leaves NO sunny side for a garden -> the
    # 100%-garden invariant drops the farmhouse. Exercises _find_appurtenances' garden-None path.
    s = _town()
    assert s.try_place(500, 500, "plain")
    s.bound = [(486, 486), (514, 486), (514, 540), (486, 540)]   # a thin N-S slot: yard fits south, no E/W room
    assert s.farmsteads() == 0
    assert s.M["houses"] == [] and s.M["gardens"] == []


# --- NUCLEATED village: grove-less cluster, adaptive gardens, worn lanes, headman-as-farmhouse ----
def _nuc_village(seed=1):
    s = Settlement(1200, 900, seed=seed)
    s.meta(name="V", scale="village")
    s._nucleated = True
    s.field_polys.append([(640, 150), (1120, 150), (1120, 780), (640, 780)])   # a paddy to the east
    return s


def test_nucleated_cluster_is_grove_less_with_yards_and_gardens():
    import random
    s = _nuc_village()
    s.lane([(300, 180), (322, 620)], width=5, clearance=11, worn=True)   # the WORN (unpaved) lane branch
    s.headman(560, 300)                                                  # headman = a LARGER plain farmhouse
    rng, n = random.Random(3), 1
    for _ in range(80):
        if n >= 14:
            break
        if s.try_place(500 + rng.uniform(-120, 120), 460 + rng.uniform(-200, 200), "plain"):
            n += 1
    drawn = s.farmsteads()
    assert drawn >= 10
    assert s.M["lanes"] and s.M["lanes"][0]["worn"] is True             # worn lane recorded
    assert not s.M["groves"]                                            # nucleated -> NO per-house grove
    assert len(s.M["threshing_yards"]) >= drawn - 1                     # each homestead keeps a yard
    assert len(s.M["gardens"]) >= drawn - 1                             # ... and an (adaptive-side) garden
    hm = [h for h in s.M["houses"] if h.get("role") == "headman"][0]
    assert hm["kind"] == "plain" and hm["w"] >= 40                      # the headman is a plain, larger house
    assert all(h["w"] <= hm["w"] for h in s.M["houses"])               # ... and the largest


def test_slide_nuc_stops_when_already_at_target():
    # a target function returning the current point -> distance 0 < 1.5 -> the immediate-break branch
    s = _nuc_village()
    assert s._slide_nuc(500, 500, 23, 14, lambda cx, cy: (cx, cy)) == (500, 500)


def test_nucleated_bundle_returns_none_when_boxed_in():
    # a bound admitting the seed but no room for even the compact house+yard+garden bundle -> no placement
    s = _nuc_village()
    s.bound = [(495, 495), (505, 495), (505, 505), (495, 505)]
    assert s.try_place(500, 500, "plain") is False


def test_garden_shaded_detects_a_house_to_the_south():
    s = _nuc_village()
    s.M["houses"].append({"x": 400, "y": 470, "w": 23, "h": 14})       # a house just SOUTH of the garden
    assert s._garden_shaded((400, 450, 22, 12)) is True                # shaded
    assert s._garden_shaded((900, 450, 22, 12)) is False               # open sky to the south -> not shaded


def test_garden_fits_rejects_a_spot_outside_the_bound():
    s = Settlement(1000, 1000, seed=1)
    s.bound = [(0, 0), (600, 0), (600, 1000), (0, 1000)]   # only x < 600 is inside
    yard = (500, 540, 32, 20)
    assert s._garden_fits(700, 500, 24, 16, 500, 500, yard) is False   # x=700 is outside the bound


def test_yard_fits_skips_own_house_and_rejects_a_neighbour():
    s = Settlement(1000, 1000, seed=1)
    s.placed.append((500, 500, 40, 28))                       # the OWN house footprint -> the loop skips it
    s.placed.append((520, 540, 40, 28))                       # a neighbour where the yard would land -> rejected
    assert s._yard_fits(520, 540, 32, 20, 500, 500) is False


def test_garden_fits_skips_own_house_and_rejects_a_neighbour():
    s = Settlement(1000, 1000, seed=1)
    s.placed.append((500, 500, 40, 28))                       # the OWN house footprint -> the loop skips it
    s.placed.append((545, 500, 40, 28))                       # a neighbour where the garden would land -> rejected
    assert s._garden_fits(545, 500, 24, 16, 500, 500, (500, 560, 32, 20)) is False


def test_grove_fits_rejects_a_spot_outside_the_bound():
    s = Settlement(1000, 1000, seed=1)
    s.bound = [(0, 0), (600, 0), (600, 1000), (0, 1000)]   # only x < 600 is inside (a city-style bound)
    assert s._grove_fits(700, 500, 30, 24, [(500, 500)]) is False   # x=700 is outside the bound


def test_fits_steers_off_a_grove():
    # groves are out of `placed` (so they may merge), but `_fits` still keeps the wells off them
    s = Settlement(1000, 1000, seed=1)
    s.grove_rects.append((500, 500, 40, 40))
    assert s._fits(505, 505, 20, 20) is False


# --- merchant_residences(): rich homes derived from the ACTUAL shops, behind the storefront band ---
def test_merchant_residences_returns_zero_without_a_road_or_shops():
    s = Settlement(1000, 1000, seed=1)
    assert s.merchant_residences() == 0          # no road, no shops
    s.road([(50, 500), (950, 500)])
    assert s.merchant_residences() == 0          # a road but still no shops


def test_merchant_residences_places_behind_band_and_skips_bad_spots():
    s = Settlement(1000, 1000, seed=1)
    s.road([(50, 500), (950, 500)])                       # horizontal road
    s.building(850, 640, 40, 28, "shop", rot=180)         # a DEEP, far shop: raises the band depth so the others'
    #                                                       homes land well behind their own shop (clearance)
    s.building(300, 560, 40, 28, "shop", rot=180)         # its home lands ~(300,684), clear -> PLACES
    s.building(395, 560, 40, 28, "shop", rot=180)         # home ~95px away: clears overlap but within `spread` -> skipped
    s.building(600, 560, 40, 28, "shop", rot=180)         # its home ~(600,684) lands in the paddy below -> skipped
    s.paddy_field((540, 650, 660, 760), "", "p", amp=6)   # a paddy under the 600-shop's home (blocked ground)
    n = s.merchant_residences(count=6)
    homes = [b for b in s.M["buildings"] if b["kind"] == "merchant_large"]
    assert n >= 1 and homes and all(h["y"] > 600 for h in homes)   # placed BEHIND the band (further from the road)


def test_merchant_residences_skips_an_off_map_home():
    s = Settlement(1000, 1000, seed=1)
    s.road([(50, 500), (950, 500)])
    s.building(300, 950, 40, 28, "shop", rot=180)         # so deep that its home lands ~y=994, off the bottom edge
    assert s.merchant_residences() == 0


def test_merchant_residences_respects_the_bound():
    s = Settlement(1000, 1000, seed=1)
    s.road([(50, 500), (950, 500)])
    s.building(850, 640, 40, 28, "shop", rot=180)         # deep+far: raises band depth so the 300-home clears its shop
    s.building(300, 560, 40, 28, "shop", rot=180)         # its home lands ~(300,684), clear of shops
    s.bound = [(0, 0), (1000, 0), (1000, 600), (0, 600)]   # bound excludes y > 600 -> the 300-home is outside -> skipped
    assert s.merchant_residences() == 0


def _village():
    s = Settlement(600, 600, seed=3)
    s.meta(name="V", scale="village")
    return s


def test_union_area_empty_and_overlapping_spans():
    # empty (or all-degenerate) rects -> zero area; and a rect fully shadowed by a taller one in the
    # same x-slab must be counted ONCE (the y1 <= cy skip), not double-counted.
    assert settlement._union_area([]) == 0.0
    assert settlement._union_area([(0, 0, 2, 2)]) == 4.0                        # single rect
    assert settlement._union_area([(0, 0, 10, 10), (0, 2, 10, 5)]) == 100.0     # inner rect adds nothing


def test_taxfree_plots_with_no_interior_cells():
    # no interior plots -> _taxfree_plots is a no-op (a field whose cells all fell outside the outline)
    s = _village()
    s._taxfree_plots([], 2)
    assert s.M["taxfree"] == []


def test_closest_on_seg_degenerate_segment():
    # a zero-length segment returns its own endpoint (no division by zero)
    assert Settlement._closest_on_seg(0, 0, 5, 5, 5, 5) == (5, 5)


def test_water_field_accepts_a_polygon_shape():
    # water_field is normally handed a bbox 4-tuple; a POLYGON shape (list of vertices) takes the other
    # branch - the outline is grown from the poly and the bbox derived from it. The field is still recorded
    # with its irrigation ditches.
    s = _village()
    s.water_field([(150, 150), (360, 150), (360, 360), (150, 360)], "", "f",
                  (150, 150), (360, 360), amp=10, plot=34)
    assert any(f["name"] == "f" and f["kind"] == "paddy" for f in s.M["fields"])
    assert any(d["field"] == "f" for d in s.M["field_ditches"])


def test_bundle_fits_rejects_a_bundle_spilling_outside_the_bound():
    # a homestead bundle whose grove/garden corner falls outside the settlement bound is rejected
    s = _village()
    s.bound = [(100, 100), (500, 100), (500, 500), (100, 500)]
    assert s._bundle_fits(s._bundle_geom(120, 120, 40, 26)) is False


def test_slide_stops_on_no_target_and_on_arrival():
    # _slide halts when the target function yields None (nowhere to go) and when it is already on target
    s = _village()
    assert s._slide(200, 200, 40, 26, lambda x, y: None, True) == (200, 200)
    assert s._slide(200, 200, 40, 26, lambda x, y: (x, y), True) == (200, 200)


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
