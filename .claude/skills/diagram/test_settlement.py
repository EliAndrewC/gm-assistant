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


# --- threshing_yards: branches the rural gens (which all have plain houses + fields) never hit ----
def test_threshing_yards_returns_zero_without_plain_farmhouses():
    s = _town()
    s.M["houses"] = [{"x": 500, "y": 500, "w": 40, "h": 28, "rot": 0, "kind": "big"}]   # no 'plain' farmstead
    assert s.threshing_yards() == 0


def test_threshing_yards_without_fields_tucks_north():
    # no fields -> the away-from-paddy direction defaults to north; the yard still attaches
    s = _town()
    s.M["houses"] = [{"x": 500, "y": 500, "w": 40, "h": 28, "rot": 0, "kind": "plain"}]
    s.placed.append((500, 500, 40, 28))
    assert s.threshing_yards() == 1
    y = s.M["threshing_yards"][0]
    assert y["of"] == [500, 500] and y["y"] < 500


def test_threshing_yards_skips_a_yard_outside_the_bound():
    # with a bounding ring (a city wall), a yard that would land outside it is skipped
    s = _town()
    s.bound = [(400, 400), (600, 400), (600, 600), (400, 600)]
    s.field_polys = [[(400, 400), (600, 400), (600, 600), (400, 600)]]
    s.M["houses"] = [{"x": 590, "y": 500, "w": 40, "h": 28, "rot": 0, "kind": "plain"}]
    assert s.threshing_yards() == 0   # the only candidate's yard tucks east, past the bound


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
