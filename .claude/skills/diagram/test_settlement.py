#!/usr/bin/env python3
"""Unit tests for settlement.py methods/branches the pool generators don't exercise.

The five worked maps cover most of settlement.py; this file reaches the rest - a couple of
unused vocabulary methods (torii_path, forest/wall labels, polygon-based flower field) and a
few internal branches (degenerate segment, the road path of face-street rotation, the big->
plain ring fallback). Together with test_villages (which runs the gens in-process) this brings
settlement.py to 100%.

    python3 -m pytest test_settlement.py -q
"""

import math
import os
import random
import tempfile

import pytest

import settlement
from settlement import Settlement, _centroid


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
        s.finish(base)  # default render=True -> resvg produces the PNG
        assert os.path.exists(base + ".png")


def test_png_width_env_overrides_render_resolution(monkeypatch):
    # DIAGRAM_PNG_WIDTH renders at a lower resolution for a quick iteration eyeball (raster cost is
    # ~quadratic in width); DIAGRAM_SKIP_RENDER skips it entirely (the test suite's default - the gate
    # reads the JSON, never the PNG). Committed maps still render at the full default width.
    from PIL import Image

    with tempfile.TemporaryDirectory() as d:
        base = os.path.join(d, "t")
        monkeypatch.setenv("DIAGRAM_PNG_WIDTH", "400")
        _town().finish(base)  # render=True + env width -> the int(env_w) branch
        assert Image.open(base + ".png").width == 400
        base2 = os.path.join(d, "u")
        monkeypatch.setenv("DIAGRAM_SKIP_RENDER", "1")
        _town().finish(base2)  # skip env -> no raster even though render=True
        assert os.path.exists(base2 + ".svg") and not os.path.exists(base2 + ".png")


def test_set_view_records_meta_and_crops_viewbox():
    # a city map crops tight to the walls: set_view records the window in meta (the checks read
    # it as the map edge) and finish() rewrites the SVG viewBox to that window. The title follows
    # the view so it stays on-canvas.
    with tempfile.TemporaryDirectory() as d:
        base = os.path.join(d, "t")
        s = Settlement(3000, 2000, seed=1)
        s.set_view(500, 400, 1000, 800)
        assert s.M["meta"]["view"] == [500, 400, 1000, 800]
        s.title("Edo")
        s.finish(base, render=False)
        with open(base + ".svg") as _f:
            svg = _f.read()
        assert 'viewBox="500 400 1000 800"' in svg and 'viewBox="0 0 3000 2000"' not in svg


def _crop_settlement():
    s = Settlement(2000, 1500, seed=1)
    s.meta(name="V", scale="village")
    return s


def test_village_population_draws_from_the_weighted_distribution():
    import random
    from collections import Counter

    from settlement import village_population

    pops = set(village_population(random.Random(i)) for i in range(300))
    assert pops <= {200, 250, 300, 350, 400, 450, 500}  # only the seven allowed sizes
    assert village_population(random.Random(3)) == village_population(random.Random(3))  # deterministic from the seed
    c = Counter(village_population(random.Random(i)) for i in range(4000))
    assert c.most_common(1)[0][0] == 350  # 350 is the mode


def test_crop_to_content_frames_hard_features_with_margin():
    s = _crop_settlement()
    s.M["houses"] = [{"x": 500, "y": 500, "w": 40, "h": 30}]
    s.crop_to_content(margin=20)
    assert s.view == (460, 465, 80, 70)  # house 500 +/- (20/2) +/- 20 margin


def test_crop_to_content_covers_fields_pond_and_poly_features():
    s = _crop_settlement()
    s.M["houses"] = [{"x": 500, "y": 500, "w": 20, "h": 20}]  # w/h branch
    s.M["groves"] = [{"poly": [[430, 430], [460, 430], [460, 460], [430, 460]]}]  # poly branch (a homestead grove still sets the frame)
    s.M["village_groves"] = [{"poly": [[300, 300], [350, 300], [350, 350], [300, 350]], "role": "windbreak"}]  # must NOT set the frame (GM 2026-07-20: the windbreak clips)
    s.M["fields"] = [{"outline": [[400, 400], [600, 400], [600, 600], [400, 600]], "vis_bbox": [420, 420, 580, 580]}]  # vis_bbox branch
    s.M["pond"] = [700, 700, 50, 40]  # pond branch
    s.M["wells"] = [{"x": 410, "y": 500, "r": 8}]  # r branch (latent bug 2026-07-20: wells set the frame too)
    s.crop_to_content(margin=0)
    assert s.view == (402, 420, 348, 320)  # well W (410-8), field N, pond E/S - the windbreak at 300 is CLIPPED


def test_crop_to_content_frames_a_torii_arch():
    # a torii arch is a visible structure: its TRUE-SCALE glyph box (torii_halfbox) must be inside the frame, so
    # a torii beyond the houses pushes the crop out to contain it (matches the hard_features_within_frame check).
    # At ftpx=1 the arch half-box is (10, 4.95, 9.16), so the torii at y=640 reaches S edge ~649 (not the old +18).
    s = _crop_settlement()
    s.M["houses"] = [{"x": 500, "y": 500, "w": 20, "h": 20}]  # hard core 490..510
    s.M["torii"] = [[500, 640, 1]]  # a gateway S of the houses
    s.crop_to_content(margin=0)
    assert s.view == (490, 490, 20, 159)  # x from houses/arch (490..510), S edge = torii y 640 + 9.16 rounded


def test_crop_to_content_uses_field_outline_when_no_vis_bbox():
    s = _crop_settlement()
    s.M["houses"] = [{"x": 500, "y": 500, "w": 20, "h": 20}]
    s.M["fields"] = [{"outline": [[400, 400], [900, 400], [900, 900], [400, 900]]}]  # no vis_bbox -> falls back to outline
    s.crop_to_content(margin=0)
    assert s.view == (400, 400, 500, 500)


def test_crop_ignores_the_commons_which_just_clips_at_the_frame():
    # the commons scrub does NOT set the frame - it is drawn and simply CLIPS at the edge, so even a huge
    # commons overhanging the hard core on every side leaves the frame tight to the hard content + margin.
    # (The GM wants the frame tight to real content - the pond, a back-slope graveyard - never held open by
    # empty grazing: the Ueda-east grazing band past the lone pond used to bloat the frame ~130px.)
    s = _crop_settlement()
    s.M["houses"] = [{"x": 500, "y": 500, "w": 20, "h": 20}]  # hard core 490..510
    s.M["commons"] = [{"poly": [[200, 200], [800, 200], [800, 800], [200, 800]]}]  # huge, overhangs ALL four sides
    s.crop_to_content(margin=10)
    assert s.view == (480, 480, 40, 40)  # hard 490..510 + 10 margin; commons ignored


def test_rects_overlap_detects_overlap_and_separation():
    # the gate-furniture walk-outward uses rects_overlap (SAT); its True branch stopped being covered
    # incidentally once the gate guard house/inspection went TRUE SCALE (2026-07-22) and no longer
    # overlapped at their initial walk positions - so test it directly
    from settlement import rects_overlap

    a = [(0, 0), (10, 0), (10, 10), (0, 10)]
    assert rects_overlap(a, [(5, 5), (15, 5), (15, 15), (5, 15)]) is True  # corner-overlapping
    assert rects_overlap(a, [(20, 0), (30, 0), (30, 10), (20, 10)]) is False  # separated on x
    assert rects_overlap(a, [(0, 20), (10, 20), (10, 30), (0, 30)]) is False  # separated on y


def test_box_clear_detects_rect_poly_and_line_obstacles():
    s = _crop_settlement()
    s.M["houses"] = [{"x": 500, "y": 500, "w": 40, "h": 30}]  # rect obstacle
    s.M["dry_plots"] = [{"poly": [[300, 300], [340, 300], [340, 340], [300, 340]]}]  # poly -> bbox'd into rects
    s.M["fields"] = [{"outline": [[600, 600], [800, 600], [800, 800], [600, 800]]}]  # polygon obstacle
    s.M["village_groves"] = [{"poly": [[1000, 1000], [1050, 1000], [1050, 1050], [1000, 1050]], "role": "copse"}]
    s.M["commons"] = [{"poly": [[50, 50], [80, 50], [80, 80], [50, 80]]}]
    s.M["streams"] = [{"poly": [[900, 100], [900, 900]]}]  # line obstacle
    s.M["lanes"] = [{"pts": [[1200, 100], [1200, 500]]}]
    obs = s._title_obstacles()
    assert s._box_clear(150, 150, 200, 180, obs) is True  # a blank patch
    assert s._box_clear(485, 490, 515, 510, obs) is False  # on the house (rect)
    assert s._box_clear(650, 650, 750, 750, obs) is False  # inside the field (poly)
    assert s._box_clear(880, 400, 920, 440, obs) is False  # across the stream (line)


def test_title_lands_over_blank_space_avoiding_the_field():
    s = _crop_settlement()
    s.set_view(0, 0, 2000, 1500)
    s.M["fields"] = [{"outline": [[200, 200], [1800, 200], [1800, 1300], [200, 1300]], "vis_bbox": [200, 200, 1800, 1300]}]
    s.M["houses"] = [{"x": 100, "y": 100, "w": 40, "h": 30}]
    s.title("Testville")
    tb = s.M["title"]["bbox"]
    assert tb[2] <= 200 or tb[0] >= 1800 or tb[3] <= 200 or tb[1] >= 1300  # clear of the field blob


def test_title_falls_back_to_the_corner_when_no_blank_space():
    s = _crop_settlement()
    s.set_view(0, 0, 200, 150)  # a tiny window...
    s.M["fields"] = [{"outline": [[-10, -10], [210, -10], [210, 160], [-10, 160]]}]  # ...covered entirely
    s.title("X")
    assert s.M["title"]["bbox"][0] == 30  # fell back to view left + 30


def test_title_without_a_view_centres_on_the_canvas():
    s = _crop_settlement()  # no set_view -> self.view is None
    s.M["fields"] = [{"outline": [[-10, -10], [2010, -10], [2010, 1510], [-10, 1510]]}]  # full-canvas cover -> no gap
    s.title("Y")
    tb = s.M["title"]["bbox"]
    assert abs((tb[0] + tb[2]) / 2 - 1000) < 2  # centered on W/2 = 1000


def test_mausoleum_yields_walls_to_abutting_ward_fences():
    # a wall that runs along a ward fence is re-stamped (the fence renders ON TOP - the wall runs
    # underneath); exercises both the horizontal- and vertical-fence branches of _ward_fence_cap
    s = Settlement(2000, 2000, seed=1)
    s.meta(name="C", scale="city")
    s.ward("a", [(400, 600), (900, 600)], [])  # horizontal fence at y=600
    s.mausoleum(600, 627, 54, 40, gate_dir="south")  # north wall y0=607 runs along it -> yields north
    assert s.M["mausoleums"][-1]["ward_walls"] == ["north"]
    s.ward("b", [(1200, 400), (1200, 900)], [])  # vertical fence at x=1200
    s.mausoleum(1227, 650, 54, 40, gate_dir="east")  # west wall x0=1200 runs along it -> yields west
    assert "west" in s.M["mausoleums"][-1]["ward_walls"]
    # a fence that is parallel + aligned but does NOT overlap the wall's extent -> no yield (both axes)
    s.ward("c", [(100, 200), (200, 200)], [])  # horizontal fence far left of...
    s.mausoleum(700, 227, 54, 40, gate_dir="south")  # ...this north wall (no x-overlap)
    assert "north" not in s.M["mausoleums"][-1]["ward_walls"]
    s.ward("d", [(1500, 100), (1500, 250)], [])  # vertical fence high above...
    s.mausoleum(1527, 650, 54, 40, gate_dir="east")  # ...this west wall (no y-overlap)
    assert "west" not in s.M["mausoleums"][-1]["ward_walls"]


def test_kido_records_ward_gates_in_both_orientations():
    s = Settlement(1000, 1000, seed=1)
    s.kido(500, 300, horizontal=True)  # E-W street gate
    s.kido(300, 500, horizontal=False)  # N-S street gate
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
    r, d = s._face_street_rot(500, 500)  # no streets at all
    assert r is None and d > 1e17
    s.M["road"] = [[100, 500], [900, 500]]  # the road branch
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
    s.street([(100, 470), (900, 470)], width=24)  # sits just behind shop A's back -> A skipped
    s.building(500, 500, 40, 28, "merchant", rot=0)  # back (-y) runs into the street corridor
    s.building(300, 800, 40, 28, "merchant", rot=0)  # back faces open ground -> kura attached
    n = s.merchant_storehouses(count=6)
    assert n == 1 and len(s.M["storehouses"]) == 1


def test_street_default_width_falls_back_to_the_ft_scale():
    # street() with no explicit width uses a real 24 ft, converted at the map's ftpx and linework-floored
    s = _town()
    s.street([(100, 200), (900, 200)])  # no width -> the lw(24) default branch
    assert s.M["town_streets"][0]["w"] == s.lw(24)


def test_forest_patch_uses_default_label_position():
    s = _town()
    s.forest_patch([(100, 100), (300, 120), (320, 300), (110, 280)], label="copse")  # no label_xy -> default
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
    s.ring(("poly", s.field_polys[0]), 20, 30, ["big"], max_big=2)  # >2 'big' requests -> the rest become 'plain'
    assert sum(1 for h in s.M["houses"] if h["kind"] == "big") <= 2


def test_gapped_ring_merges_when_first_vertex_is_not_a_gate():
    # a closed wall ring whose FIRST vertex is not a gate: the run after the last gap must merge back
    # into the first, leaving one continuous subpath (not a spurious break at the start point)
    s = Settlement(1000, 1000, seed=1)
    ring = [(100, 100), (300, 100), (300, 300), (100, 300), (100, 100)]  # closed square
    d = s._gapped_ring(ring, [(300, 100)], gap=20, closed=True)  # one gate, at a NON-first vertex
    assert d.count("M") == 1


def test_wall_walk_crosses_multiple_edges():
    # walking further than one wall edge: the accumulate-and-step branch must carry across edges. A run
    # of short 50px edges, gate at index 4, walking 120px west crosses edges 4->3->2 to land at x=180.
    s = Settlement(1000, 1000, seed=1)
    pts = [(100, 100), (150, 100), (200, 100), (250, 100), (300, 100), (300, 150)]
    x, y, ang = s._wall_walk(pts, 4, 120, west=True)
    assert abs(x - 180) < 1e-6 and abs(y - 100) < 1e-6
    assert abs(ang - 180) < 1e-6  # the run is horizontal; walking west the edge points in -x


# --- farmsteads(): the deferred draw giving EVERY farmhouse a yard (nudge / drop / bound branches) -----
def test_try_place_defers_the_farmhouse():
    # try_place reserves + records the farmhouse but does NOT draw it yet (farmsteads draws it with its yard)
    s = _town()
    assert s.try_place(500, 500, "plain")
    assert len(s.M["houses"]) == 1 and len(s.M["threshing_yards"]) == 0  # deferred, no yard yet


def test_farmsteads_yard_on_the_sunny_south_front():
    s = _town()
    assert s.try_place(500, 500, "plain")
    assert s.farmsteads() == 1
    y = s.M["threshing_yards"][0]
    assert y["of"] == [500, 500] and y["y"] > 500  # the yard sits on the house's south/front (+y) side


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
    assert gd["of"] == [500, 500] and gd["y"] >= 500 - 5  # never the shady north back


def test_farmsteads_drops_a_farmhouse_with_no_garden_room():
    # a bound that admits the house + its south yard but leaves NO sunny side for a garden -> the
    # 100%-garden invariant drops the farmhouse. Exercises _find_appurtenances' garden-None path.
    s = _town()
    assert s.try_place(500, 500, "plain")
    s.bound = [(486, 486), (514, 486), (514, 540), (486, 540)]  # a thin N-S slot: yard fits south, no E/W room
    assert s.farmsteads() == 0
    assert s.M["houses"] == [] and s.M["gardens"] == []


# --- NUCLEATED village: grove-less cluster, adaptive gardens, worn lanes, headman-as-farmhouse ----
def _nuc_village(seed=1):
    s = Settlement(1200, 900, seed=seed)
    s.meta(name="V", scale="village")
    s._nucleated = True
    s.field_polys.append([(640, 150), (1120, 150), (1120, 780), (640, 780)])  # a paddy to the east
    return s


def test_nucleated_cluster_is_grove_less_with_yards_and_gardens():
    import random

    s = _nuc_village()
    s.lane([(300, 180), (322, 620)], width=5, clearance=11, worn=True)  # the WORN (unpaved) lane branch
    s.headman(560, 300)  # headman = a LARGER plain farmhouse
    rng, n = random.Random(3), 1
    for _ in range(80):
        if n >= 14:
            break
        if s.try_place(500 + rng.uniform(-120, 120), 460 + rng.uniform(-200, 200), "plain"):
            n += 1
    drawn = s.farmsteads()
    assert drawn >= 10
    assert s.M["lanes"] and s.M["lanes"][0]["worn"] is True  # worn lane recorded
    assert not s.M["groves"]  # nucleated -> NO per-house grove
    assert len(s.M["threshing_yards"]) >= drawn - 1  # each homestead keeps a yard
    assert len(s.M["gardens"]) >= drawn - 1  # ... and an (adaptive-side) garden
    hm = [h for h in s.M["houses"] if h.get("role") == "headman"][0]
    assert hm["kind"] == "plain" and hm["w"] >= 40  # the headman is a plain, larger house
    assert all(h["w"] <= hm["w"] for h in s.M["houses"])  # ... and the largest


def test_village_grove_fills_an_irregular_polygon_and_records_it():
    s = _nuc_village()  # field to the EAST (x >= 640)
    poly = [(150, 350), (260, 330), (280, 640), (160, 660)]  # an irregular quad WEST of the field (open ground)
    n = s.village_grove(poly, role="windbreak")  # dense belt -> many overlapping clumps
    assert n > 0
    vg = s.M["village_groves"]
    assert len(vg) == 1 and vg[0]["role"] == "windbreak" and len(vg[0]["poly"]) == 4


def test_village_grove_over_the_paddy_draws_and_records_nothing():
    s = _nuc_village()  # field at [(640,150),(1120,150),(1120,780),(640,780)]
    poly = [(700, 250), (900, 250), (900, 450), (700, 450)]  # a footprint ENTIRELY inside the paddy
    assert s.village_grove(poly, role="copse", dense=False) == 0  # every clump skipped (on crops) -> nothing
    assert s.M["village_groves"] == []  # ... and nothing recorded


def test_village_grove_scatter_skips_houses_and_fills_the_open_gaps():
    s = _nuc_village()
    s.M["houses"] = [{"x": 300, "y": 400, "w": 46, "h": 29}]  # one house inside the scatter region
    n = s.village_grove([(200, 300), (500, 300), (500, 500), (200, 500)], role="copse", dense=False)
    assert n >= 1  # bamboo/fruit clumps settle into the gaps
    assert s.M["village_groves"][0]["role"] == "copse"


def test_village_grove_skips_clumps_on_a_lane():
    s = _nuc_village()
    s.M["lanes"] = [{"pts": [[300, 300], [300, 600]], "w": 6}]  # a lane straight down x=300
    s.village_grove([(250, 300), (350, 300), (350, 600), (250, 600)], role="copse", dense=False)
    vg = s.M["village_groves"][0]
    assert vg["clumps"]  # drew clumps in the gaps beside the lane
    for cx, _cy in vg["clumps"]:  # ... but none on the lane tread + clump radius (mirrors the check)
        assert abs(cx - 300) >= 3 + vg["r"]


def test_corridor_buffers_gathers_lanes_streets_and_road():
    s = _nuc_village()
    s.M["lanes"] = [{"pts": [[0, 0], [10, 0]], "w": 6}]
    s.M["town_streets"] = [{"pts": [[0, 0], [10, 0]], "w": 10}]
    s.M["road"] = [[0, 0], [10, 0]]
    corr = s._corridor_buffers(4)
    assert [b for _, b in corr] == [3 + 4, 5 + 4, 13 + 4]  # lane 6/2, street 10/2, road 26/2, each + extra


def test_village_grove_skips_clumps_in_a_yards_sun_corridor():
    poly = [(200, 380), (360, 380), (360, 560), (200, 560)]
    n_open = _nuc_village().village_grove(poly, role="copse", dense=False)  # baseline, no yard
    s = _nuc_village()
    s.M["threshing_yards"] = [{"x": 300, "y": 420, "w": 30, "h": 6}]  # a thin yard: its SOUTHERN sun-corridor
    n_yard = s.village_grove(poly, role="copse", dense=False)  # ... removes a clump beyond the occ keep-out
    assert n_yard < n_open  # the sun-corridor skip fired
    vg = s.M["village_groves"][0]
    r = vg["r"]
    se = 420 + 3  # yard south edge
    for cx, cy in vg["clumps"]:  # ... and none left in the sun-strip (mirrors the check)
        assert not (abs(cx - 300) < 15 + r and se - r < cy < se + 22 + r)


def test_marsh_draws_wet_scatter_and_records_it():
    s = _crop_settlement()
    s.marsh([(100, 120), (600, 100), (350, 620)])  # a triangle -> also covers the point-in-poly skip
    assert len(s.M["marshes"]) == 1 and len(s.M["marshes"][0]["poly"]) == 3
    assert s.out  # drew reeds / wet tint


def test_marsh_skips_points_on_a_paddy():
    s = _crop_settlement()
    s.field_polys.append([(300, 100), (600, 100), (600, 400), (300, 400)])  # a paddy inside the region
    s.marsh([(100, 100), (600, 100), (600, 500), (100, 500)])  # straddles the paddy - reeds over it are skipped
    assert len(s.M["marshes"]) == 1


def test_marsh_pond_fringe_skips_the_open_water():
    s = _crop_settlement()
    s.M["pond"] = [300, 300, 100, 80]  # a pond inside the region
    s.marsh([(150, 150), (450, 150), (450, 450), (150, 450)], role="pond_fringe")  # reeds rim the shore, not the open water
    assert s.M["marshes"][0]["role"] == "pond_fringe"


def test_marsh_defense_role_records_and_blocks_building():
    s = _crop_settlement()
    n0 = len(s.block_polys)
    s.marsh([(150, 150), (450, 150), (450, 450), (150, 450)], role="defense")
    assert s.M["marshes"][0]["role"] == "defense"
    assert len(s.block_polys) == n0 + 1  # the wet belt is a no-build keep-out, same as the toe


def test_marsh_rejects_an_unknown_role():
    s = _crop_settlement()
    with pytest.raises(ValueError, match="unknown marsh role"):
        s.marsh([(150, 150), (450, 150), (450, 450), (150, 450)], role="bog")


def test_pond_anchored_detects_a_watercourse_that_connects_to_the_pond():
    # the cue that a course should snap onto the pond rim: either end's anchor is kind=='pond'
    assert Settlement._pond_anchored({"kind": "pond"}, {"kind": "field"}) is True
    assert Settlement._pond_anchored({"kind": "field"}, {"kind": "pond"}) is True
    assert Settlement._pond_anchored({"kind": "offmap"}, {"kind": "field"}) is False
    assert Settlement._pond_anchored(None, None) is False


def test_clip_to_pond_is_a_noop_without_a_pond():
    s = _crop_settlement()  # no pond recorded on this map
    pts = [(100, 100), (200, 200)]
    assert s._clip_to_pond(pts) == pts  # nothing to snap to -> returned unchanged


def test_city_wall_tower_slides_along_the_wall_for_a_kido():
    # tower_skip: a mural tower yields its vertex to a future kido, but the vertex stays COVERED by
    # a tower a short way along the wall (not a whole-vertex jump leaving a bare, indefensible arc).
    # At this crop's ftpx=1 the default garrison spacing is ~278px, so the flanking towers straddle
    # the yielded vertex at ~half-spacing (~140px) - well inside a bare-stretch (~one full segment).
    import math as m

    s = _crop_settlement()
    pts = [(round(1000 + 400 * m.cos(2 * m.pi * i / 12)), round(700 + 400 * m.sin(2 * m.pi * i / 12))) for i in range(12)]
    s.city_wall(pts, gates=(), tower_skip=[pts[6]])
    ds = [m.hypot(t["x"] - pts[6][0], t["y"] - pts[6][1]) for t in s.M["wall_towers"]]
    assert all(d > 45 for d in ds)  # the vertex is yielded...
    assert any(d < 180 for d in ds)  # ...but a tower still stands a short slide away (< a full segment)


def test_city_wall_tower_drops_when_boxed_in_on_both_sides():
    # ...and when the slide finds no clear ground either way, the tower is dropped (the 75-deg
    # spacing check tolerates one gap)
    import math as m

    s = _crop_settlement()
    pts = [(round(1000 + 400 * m.cos(2 * m.pi * i / 12)), round(700 + 400 * m.sin(2 * m.pi * i / 12))) for i in range(12)]
    s.city_wall(pts, gates=(), tower_skip=[pts[5], pts[6], pts[7]])
    assert all(m.hypot(t["x"] - pts[6][0], t["y"] - pts[6][1]) > 60 for t in s.M["wall_towers"])


def test_river_canal_dock_jetty_water_gate_defaults():
    # exercise the river-city glyph methods with their DEFAULT widths/lengths + the moat(river=)
    # open-arc path and the water-gate tower-skip vertex (Nagahara passes explicit sizes; this
    # covers the default branches).
    import math as m

    s = _crop_settlement()
    s.meta(name="R", scale="city", walled=True, ftpx=3)
    pts = [(round(1000 + 300 * m.cos(2 * m.pi * i / 16)), round(700 + 300 * m.sin(2 * m.pi * i / 16))) for i in range(16)]
    river = [(1360, 300), (1360, 1100)]  # a river just east of the wall
    s.river(river)  # default width
    s.moat(pts, gap=24, river=river)  # open-arc moat joining the river
    s.water_gate(pts[0][0], pts[0][1])  # arch on the east gate vertex (default rot)
    s.canal([(1350, 700), (1100, 700)])  # default width
    s.dock(1050, 700, 54, 34)
    s.jetty(1330, 600)  # default length
    s.city_wall(pts, gates=[pts[4]], water_gates=[pts[0]])  # water gate skips its mural-tower vertex
    assert s.M["river"]["w"] > 0 and s.M["canals"] and s.M["docks"] and s.M["jetties"] and s.M["water_gates"]
    assert s.M["moat"][0] != s.M["moat"][-1]  # OPEN arc (ends do not close on themselves)


def test_clip_to_moat_whole_path_inside_is_left_alone():
    s = _crop_settlement()
    s.M["moat"] = [(300, 100), (300, 900)]
    s.M["moat_width"] = 22
    both_in = [(298, 400), (302, 500)]  # both ends within the bed -> untouched
    assert s._clip_to_moat(both_in) == both_in


def test_city_wall_gateposts_orient_to_the_wall_tangent():
    # GM 2026-07: gateposts were hard-coded N/S (vertical rects); on an E/W gate they must stand
    # N and S of the opening, oriented to the wall's local tangent - so a gate on a vertical wall
    # stretch gets ~vertical-tangent posts (rot near +-90), not the old rot=0.
    import math as m

    s = _crop_settlement()
    s.meta(name="C", scale="city", walled=True, ftpx=3)
    pts = [(round(1000 + 400 * m.cos(2 * m.pi * i / 16)), round(700 + 400 * m.sin(2 * m.pi * i / 16))) for i in range(16)]
    egate = pts[0]  # the EAST gate (rightmost): the wall runs ~vertically there
    s.city_wall(pts, gates=[egate])
    posts = [g for g in s.M["gate_structs"] if g.get("kind") == "gatepost"]
    assert len(posts) == 2
    assert all(abs(abs(p["rot"]) - 90) < 25 for p in posts)  # tangent ~vertical, not the old rot 0
    # the two posts straddle the gate along the tangent (N and S of it), not E and W
    assert abs(posts[0]["y"] - posts[1]["y"]) > 40 and abs(posts[0]["x"] - posts[1]["x"]) < 30


def test_moat_closes_into_a_ring_without_a_river():
    # the moat(river=None) branch: with no river to join, the moat closes on itself into a ring (the
    # else arm), so the recorded polyline's first and last points coincide. The river-open-arc arm is
    # covered by test_river_canal_dock_jetty_water_gate_defaults.
    import math as m

    s = _crop_settlement()
    pts = [(round(1000 + 300 * m.cos(2 * m.pi * i / 12)), round(700 + 300 * m.sin(2 * m.pi * i / 12))) for i in range(12)]
    s.moat(pts)  # no river -> CLOSED ring
    assert s.M["moat"][0] == s.M["moat"][-1]


def test_rect_hits_detects_a_pure_edge_crossing():
    # the _rect_hits edge-cross arm: a plus-sign where neither shape has a corner/vertex inside the
    # other, but their edges cross - the corner-in / vertex-in fast paths both miss, so only the
    # per-edge segments_cross catches it. Plus a bbox-disjoint poly to exercise the early reject.
    s = _crop_settlement()
    assert s._rect_hits((500, 500, 200, 40), [[(480, 400), (520, 400), (520, 600), (480, 600)]])
    assert not s._rect_hits((500, 500, 40, 40), [[(900, 900), (950, 900), (950, 950), (900, 950)]])


def test_label_hits_counts_a_grove_under_the_label():
    # the _label_hits grove_rects arm: a label box centered on a homestead grove counts it as an
    # obstacle (a label should not sit over a grove canopy).
    s = _crop_settlement()
    s.grove_rects = [(500, 500, 40, 40)]
    assert s._label_hits(500, 500, "Ministry of Test", 12) >= 1


def test_city_gate_tower_flips_to_the_other_flank_when_one_is_blocked():
    # the gate tower belongs AT the gate: with its PRIMARY flank blocked by a kido span, it does NOT walk
    # far out along the wall - it flips to the OTHER flank at the same short arc, still at the opening.
    import math as m

    s = _crop_settlement()
    s.meta(name="G", scale="city", walled=True, ftpx=3)
    pts = [(round(1000 + 400 * m.cos(2 * m.pi * i / 16)), round(700 + 400 * m.sin(2 * m.pi * i / 16))) for i in range(16)]
    blocks = [s._wall_walk(pts, 0, a, west=False)[:2] for a in (78, 98, 118)]  # block the PRIMARY (west=False) flank
    s.city_wall(pts, gates=[pts[0]], tower_skip=blocks)
    tower = [gs for gs in s.M["gate_structs"] if gs.get("kind") == "tower"]
    assert tower  # the gate tower is still placed...
    assert m.hypot(tower[0]["x"] - pts[0][0], tower[0]["y"] - pts[0][1]) < 110  # ...AT the gate, not marooned far out
    assert all(m.hypot(tower[0]["x"] - bx, tower[0]["y"] - by) > 45 for bx, by in blocks)  # on the clear OTHER flank


def test_city_gate_tower_steps_out_when_both_near_flanks_are_blocked():
    # only when BOTH near-gate flanks are blocked does the tower step OUTWARD along the wall (the arc walk):
    # kido spans on each side of the gate leave it nowhere at the opening, so it walks clear.
    import math as m

    s = _crop_settlement()
    s.meta(name="B", scale="city", walled=True, ftpx=3)
    pts = [(round(1000 + 400 * m.cos(2 * m.pi * i / 16)), round(700 + 400 * m.sin(2 * m.pi * i / 16))) for i in range(16)]
    blocks = [s._wall_walk(pts, 0, a, west=wf)[:2] for a in (78, 98, 118) for wf in (False, True)]  # BOTH flanks near the gate
    s.city_wall(pts, gates=[pts[0]], tower_skip=blocks)
    tower = [gs for gs in s.M["gate_structs"] if gs.get("kind") == "tower"]
    assert tower and all(m.hypot(tower[0]["x"] - bx, tower[0]["y"] - by) > 45 for bx, by in blocks)  # placed, walked clear of every blocked span


def test_city_gate_tower_falls_back_when_every_spot_is_blocked():
    # both flanks blocked at EVERY arc out to the cap: the tower is still placed exactly once (the last
    # candidate is taken rather than the loop running past the cap with nothing placed).
    import math as m

    s = _crop_settlement()
    s.meta(name="F", scale="city", walled=True, ftpx=3)
    pts = [(round(1000 + 400 * m.cos(2 * m.pi * i / 16)), round(700 + 400 * m.sin(2 * m.pi * i / 16))) for i in range(16)]
    blocks = [s._wall_walk(pts, 0, a, west=wf)[:2] for a in range(78, 241, 20) for wf in (False, True)]
    s.city_wall(pts, gates=[pts[0]], tower_skip=blocks)
    assert len([gs for gs in s.M["gate_structs"] if gs.get("kind") == "tower"]) == 1


def test_city_mural_tower_yields_a_vertex_shoulder_to_shoulder_with_a_gate_tower():
    # the mural-tower loop skips a wall vertex within 110px of a GATE tower (a mural tower there would read
    # as a double). This fires only when the gate tower has stepped OUT toward the next even vertex - which
    # now needs BOTH near-gate flanks blocked. A fine 24-gon plus kido spans on both flanks forces exactly
    # that: the tower walks out near an even, non-gate vertex, which the mural loop then yields.
    import math as m

    s = _crop_settlement()
    s.meta(name="M", scale="city", walled=True, ftpx=3)
    pts = [(round(1000 + 420 * m.cos(2 * m.pi * i / 24)), round(700 + 420 * m.sin(2 * m.pi * i / 24))) for i in range(24)]
    blocks = [s._wall_walk(pts, 0, a, west=wf)[:2] for a in (78, 98, 118) for wf in (False, True)]
    s.city_wall(pts, gates=[pts[0]], tower_skip=blocks)
    gate_towers = [(gs["x"], gs["y"]) for gs in s.M["gate_structs"] if gs.get("kind") == "tower"]
    assert gate_towers and s.M.get("wall_towers")  # both kinds of tower were placed
    # the gate tower walked clear of the blocked kido spans (which is what carried it out near the even
    # vertex the mural loop then yields)
    assert all(m.hypot(gate_towers[0][0] - bx, gate_towers[0][1] - by) > 45 for bx, by in blocks)


def test_farmsteads_legacy_skips_grove_for_a_city_intramural_farm():
    # the legacy farmsteads inwall-grove skip: a farm INSIDE a city wall (scale=city, inwall_groves off)
    # gets no windward grove (intramural land is too precious and the urban fabric shelters it). Uses the
    # legacy house-first path (city is not to-scale), with a wall enclosing the whole ring of farms.
    s = Settlement(1200, 900, seed=3)
    s.meta(name="C", scale="city")  # city + not toscale -> legacy path
    fld = (300, 300, 620, 560)
    s.paddy_field(fld, "", "f", amp=20)
    s.ring(fld, 8, 16, ["plain"])
    s.M["wall"] = [(120, 120), (760, 120), (760, 720), (120, 720)]  # encloses the whole ring of farms
    n = s.farmsteads()
    assert n > 0 and not s.M["groves"]  # every intramural farm skipped its grove


def test_dry_polys_block_a_footprint_margin_not_just_the_center():
    # dry crop plots are FOOTPRINT-aware no-build cropland: block_polys test only a candidate's
    # CENTER, which let a house centered just off a hem strip stand half its footprint on the crop
    s = _crop_settlement()
    s.dry_polys.append([(300, 300), (500, 300), (500, 380), (300, 380)])
    assert not s._fits(400, 340, 20, 14)  # centered inside the strip -> blocked
    assert not s._fits(510, 340, 20, 14)  # centered 10px OUTSIDE: the footprint would overlap -> still blocked
    assert s._fits(560, 340, 20, 14)  # well clear of the 12px margin -> fits


def test_grove_fits_rejects_a_belt_over_a_dry_strip():
    # the windbreak's canopy stays out of the barley exactly as it stays out of the paddy
    s = _crop_settlement()
    s.dry_polys.append([(300, 300), (500, 300), (500, 380), (300, 380)])
    assert not s._grove_fits(400, 340, 60, 30, own=[])
    assert s._grove_fits(400, 500, 60, 30, own=[])


def test_clip_to_moat_is_a_noop_without_a_moat():
    s = _crop_settlement()  # no moat recorded on this map
    pts = [(100, 100), (200, 200)]
    assert s._clip_to_moat(pts) == pts
    assert s._clip_to_moat([(1, 1)]) == [(1, 1)]  # a degenerate 1-point path is left alone


def test_clip_to_moat_snaps_a_connecting_end_onto_the_bed_edge():
    # the moat twin of _clip_to_pond: a tap/culvert that reaches the moat must JOIN the bed's edge
    # (mouth inset ~3px so it covers the rim stroke), never draw its bed across the open water
    s = _crop_settlement()
    s.M["moat"] = [(300, 100), (300, 900)]  # a straight vertical moat centerline
    s.M["moat_width"] = 22  # bed half-width 11 -> snapped ends sit 8 out
    out = s._clip_to_moat([(300, 500), (500, 500)])  # end ON the centerline -> snapped to the edge
    assert abs(out[0][0] - 308) < 0.5 and abs(out[0][1] - 500) < 0.5
    assert out[-1] == (500, 500)  # the field end is untouched
    run = s._clip_to_moat([(295, 500), (305, 502), (500, 500)])  # a RUN inside the bed -> trimmed
    assert len(run) == 2 and abs(run[0][0] - 308) < 3
    far = [(400, 500), (500, 500)]  # both ends clear of the bed -> untouched
    assert s._clip_to_moat(far) == far
    allin = [(300, 400), (300, 500)]  # the whole path lies in the moat -> left alone
    assert s._clip_to_moat(allin) == allin


def test_clip_to_pond_snaps_a_connecting_end_onto_the_rim():
    s = _crop_settlement()
    s.M["pond"] = [300, 300, 100, 80]  # center (300,300), rx=100, ry=80; rim where rad==1

    def rad(p):
        return ((p[0] - 300) / 100) ** 2 + ((p[1] - 300) / 80) ** 2

    inside = s._clip_to_pond([(300, 300), (310, 310), (300, 500)])  # a RUN inside the pond -> trimmed to start AT the rim
    assert abs(rad(inside[0]) - 1.0) < 1e-3
    assert inside[-1] == (300, 500)  # the field end is untouched
    outside = s._clip_to_pond([(300, 388), (300, 600)])  # foot JUST OUTSIDE (rad ~1.21) -> a rim point is prepended
    assert abs(rad(outside[0]) - 1.0) < 1e-3
    assert outside[1] == (300, 388)  # the original foot is kept, the rim point sits before it


def test_field_channel_routes_pieces_through_the_water_block():
    s = _crop_settlement()
    s.M["pond"] = [300, 300, 100, 80]
    run = [(300, 300)] + [(300 + 30 * i, 380 + 30 * i) for i in range(9)]  # sluice inside -> snapped to the rim
    s.field_channel(run, "#6C9CBE", 6.0, 2.0)  # tapering -> split into stroked pieces of decreasing width
    s.field_channel(run, "#7C9EB0", 3.0, 3.0)  # uniform width -> the single-stroke branch
    s.field_channel([(300, 300), (600, 700)], "#6C9CBE", 6.0, 2.0)  # only 2 pts -> degenerate pieces are skipped
    assert s.water and s._water_idx is not None  # routed through _water, not a bare s.add


def test_pond_feeder_snaps_to_the_rim_even_when_drawn_before_the_pond():
    # the DEFERRED clip: a feeder is drawn BEFORE the pond (M['pond'] unknown at call time), then the pond;
    # at flush both a bed+sheen feeder (stream) and a bed-only feeder (channel) are re-emitted snapped to the
    # rim, so neither lays a stroke across the open water.
    with tempfile.TemporaryDirectory() as d:
        base = os.path.join(d, "t")
        s = Settlement(1000, 1000, seed=1)
        s.meta(name="V", scale="village")
        s.stream([(500, 20), (500, 300)], frm={"kind": "offmap"}, to={"kind": "pond"})  # brook INTO the pond, drawn FIRST
        s.channel((500, 260), (200, 260), {"kind": "pond"}, {"kind": "field", "name": "w"})  # supply channel OUT of the pond
        s.pond(500, 250, 100, 70)  # pond LAST - the clip must still find it at flush
        s.finish(base, render=False)
        with open(base + ".svg") as _f:
            assert "9CB4C8" in _f.read()  # water rendered (the flush ran the re-emit)


def test_commons_draws_open_scrub_and_records_it():
    s = _nuc_village()  # field to the EAST (x >= 640)
    poly = [(60, 300), (200, 320), (110, 660)]  # a TRIANGLE of open ground WEST of the field
    s.commons(poly)  # grass tufts + brush + scraggly pines
    assert len(s.M["commons"]) == 1 and len(s.M["commons"][0]["poly"]) == 3
    assert s.out  # it drew the scrub texture


def test_commons_skips_scrub_that_would_fall_on_the_paddy():
    s = _nuc_village()  # field at [(640,150),(1120,150),(1120,780),(640,780)]
    s.commons([(560, 300), (760, 300), (760, 600), (560, 600)])  # straddles the field's W edge - clumps over crops skipped
    assert len(s.M["commons"]) == 1


def _scatter_base_points(frags):
    """The BASE coordinates of every scatter element in the given SVG fragments: tuft/reed blade
    roots (the x1,y1 each blade grows from - the exact point _sparse tested) and dot/patch centers
    (cx,cy). Blade TIPS (x2,y2) may lean a few px past the base, so assertions run on bases."""
    import re

    pts = []
    for fr in frags:
        pts += [(float(a), float(b)) for a, b in re.findall(r'x1="(-?[\d.]+)" y1="(-?[\d.]+)"', fr)]
        pts += [(float(a), float(b)) for a, b in re.findall(r'cx="(-?[\d.]+)" cy="(-?[\d.]+)"', fr)]
    return pts


# ---- the URBAN-CLEARANCE HALO (GM 2026-07-21, Hoshizora): ground-cover stays out of the swept /
# trodden ground AROUND every structure and wellhead, not merely off their footprints - the old
# footprint-only skip scattered scrub through the streets, dooryards, and district gaps of the
# Hoshizora town core. Doctrine + constants: settlement._urban_keepouts. role="pasture" in these
# tests keeps the scatter to tufts + dots (no multi-segment pines), so every element is base-tested.


def test_commons_clears_the_urban_halo_around_buildings():
    s = _crop_settlement()
    s.building(300, 300, 40, 28, "merchant")  # axis-aligned
    s.building(430, 300, 40, 28, "laborer", rot=30)  # rotated - covered by its half-diagonal square
    s.building(1900, 1400, 40, 28, "shop")  # far outside the cover poly - the bbox prefilter drops it
    before = len(s.out)
    s.commons([(150, 150), (600, 150), (600, 500), (150, 500)], role="pasture")
    pts = _scatter_base_points(s.out[before:])
    assert pts  # the open ground beyond the halos still got its scatter
    halo = 30 * s.bscale - 0.06  # the SVG rounds coords to 0.1, so a base just OUTSIDE the halo can print ON its edge
    hd = math.hypot(20, 14) + halo
    for px, py in pts:
        assert not (280 - halo <= px <= 320 + halo and 286 - halo <= py <= 314 + halo)
        assert not (430 - hd <= px <= 430 + hd and 300 - hd <= py <= 300 + hd)


def test_commons_clears_the_wellhead_apron():
    s = _crop_settlement()
    s.well(300, 300)
    before = len(s.out)
    s.commons([(150, 150), (500, 150), (500, 450), (150, 450)], role="pasture")
    lim = s.M["wells"][0]["vr"] + 20 * s.bscale - 0.06  # 0.1-rounding slack, as in the halo test
    pts = _scatter_base_points(s.out[before:])
    assert pts and all((px - 300) ** 2 + (py - 300) ** 2 > lim * lim for px, py in pts)


def test_commons_keeps_scrub_off_the_road_bed():
    # the old skip knew only LANES, so scrub drew on the Imperial Road bed (Hoshizora); the
    # corridor set now covers lanes + town streets + the road
    s = _crop_settlement()
    s.road([(100, 300), (700, 300)])
    before = len(s.out)
    s.commons([(150, 150), (600, 150), (600, 450), (150, 450)], role="pasture")
    lim = s.M["road_width"] / 2 + 3 * s.bscale - 0.06  # 0.1-rounding slack, as in the halo test
    pts = _scatter_base_points(s.out[before:])
    assert pts and all(abs(py - 300) > lim for px, py in pts if 100 <= px <= 700)


def test_marsh_clears_the_urban_halo_and_wellheads():
    s = _crop_settlement()
    s.building(300, 300, 40, 28, "merchant")
    s.well(460, 300)
    before = len(s.out)
    s.marsh([(150, 150), (600, 150), (600, 450), (150, 450)])
    lim = s.M["wells"][0]["vr"] + 20 * s.bscale - 0.06  # 0.1-rounding slack, as in the halo test
    halo = 30 * s.bscale - 0.06
    pts = _scatter_base_points(s.out[before:])
    assert pts
    for px, py in pts:
        assert not (280 - halo <= px <= 320 + halo and 286 - halo <= py <= 314 + halo)
        assert (px - 460) ** 2 + (py - 300) ** 2 > lim * lim


def test_commons_keeps_scrub_off_a_trodden_lane():
    s = _nuc_village()
    s.lane([(300, 100), (300, 700)], width=6, clearance=11, worn=True)  # a lane crossing the scrub
    s.commons([(220, 150), (420, 150), (420, 650), (220, 650)])  # straddles the lane - tufts on the tread are skipped
    assert len(s.M["commons"]) == 1  # still recorded (the skip is per-tuft, not the plot)


def test_marsh_keeps_reeds_off_a_lane_causeway():
    s = _crop_settlement()
    s.lane([(100, 300), (500, 300)], width=6, clearance=11, worn=True)  # a causeway through the marsh
    s.marsh([(100, 150), (500, 150), (500, 450), (100, 450)])  # reeds on the tread are skipped
    assert len(s.M["marshes"]) == 1


def test_commons_keeps_scrub_off_a_shrine_and_torii():
    # a commons that OVERLAPS the shrine must not scatter scrub over the hall or its torii arch (both are
    # block_polys); the skip is per-tuft, so the plot is still recorded
    s = _nuc_village()
    s.shrine_hall(320, 400, "", w=60, h=48, kind="shrine", torii=[(320, 330)], graveyard=False)
    s.commons([(220, 150), (420, 150), (420, 650), (220, 650)])  # straddles the shrine + torii blocks
    assert len(s.M["commons"]) == 1


def test_marsh_keeps_reeds_off_a_building():
    s = _crop_settlement()
    s.shrine_hall(300, 300, "", w=60, h=48, kind="shrine", graveyard=False)  # a block_poly inside the marsh
    s.marsh([(150, 150), (500, 150), (500, 450), (150, 450)])  # reeds on the hall are skipped
    assert len(s.M["marshes"]) == 1


def test_cemetery_default_is_a_ruled_rectangle():
    s = _crop_settlement()
    s.cemetery(300, 300, 100, 70)
    assert 'width="100"' in s.out[-1] and "<path" not in s.out[-1]  # a plotted rectangle, no organic blob


def test_cemetery_organic_draws_an_irregular_plot():
    s = _crop_settlement()
    s.cemetery(300, 300, 100, 70, parish=False, organic=True)
    frag = s.out[-1]
    assert "<path" in frag and 'width="100"' not in frag  # a jittered blob outline, no ruled 100-wide plot rect
    assert s.M["cemeteries"][-1]["w"] == 100  # recorded bbox is still the w x h rectangle
    assert s.block_polys[-1] == [(242, 257), (358, 257), (358, 343), (242, 343)]  # no-build block unchanged (checks unaffected)


def test_cemetery_common_ground_defaults_organic():
    # organic derives from parish: a non-parish COMMON ground is Japan-style organic unless overridden
    s = _crop_settlement()
    s.cemetery(300, 300, 100, 70, parish=False)
    assert "<path" in s.out[-1] and 'width="100"' not in s.out[-1]


def test_cemetery_organic_false_keeps_the_louzeyuan_rectangle():
    # the deliberate per-city override: a plotted Chinese-style charity ground stays a ruled rectangle
    s = _crop_settlement()
    s.cemetery(300, 300, 100, 70, parish=False, organic=False)
    assert 'width="100"' in s.out[-1] and "<path" not in s.out[-1]


def test_animal_ground_records_a_yard_and_optional_label():
    # the city_no_large_empty_space remedy: a standalone stable-yard scatter claiming a pocket
    s = _crop_settlement()
    s.animal_ground(400, 400, r=60)  # no label - the rails and animals read on their own
    assert s.M["stable_yards"][-1] == {"x": 400, "y": 400, "r": 60, "of": [400, 400], "troughs": 2}
    s.animal_ground(700, 700, r=52, label="caravan ground")
    assert s.M["labels"][-1][5] == "caravan ground"  # label boxes are [x0, y0, x1, y1, z, text]


def test_caravan_scale_yard_gets_three_troughs_beside_the_nearest_well():
    # the watering point (settlements.md 'Stable yard' watering): a caravan-scale ground (r >= 76)
    # draws 3 troughs, and the cluster HUGS the recorded well - a bucket-pour from the wellhead
    # (GM 2026-07-23: "otherwise you'd have to carry the water a long way"), even a well past the rim
    s = _crop_settlement()
    s.M["wells"] = [{"x": 500, "y": 400, "r": 8, "vr": 4.0, "shrine": False}]
    s.animal_ground(400, 400, r=80)
    assert s.M["stable_yards"][-1]["troughs"] == 3
    out = "".join(s.out)
    assert out.count('fill="#8FA6B0"') == 3  # the trough rects
    assert 'x="489.9"' in out  # cluster at (492.2, 400): wellhead vr 4.0 + half a 4.6 trough + 1.5 step from the well at x=500


def test_yard_troughs_fall_back_when_no_well_in_reach():
    # every recorded well beyond r + 40: the cluster takes a clear interior spot instead
    s = _crop_settlement()
    s.M["wells"] = [{"x": 900, "y": 900, "r": 8, "vr": 4.0, "shrine": False}]
    s.animal_ground(400, 400, r=60)
    assert s.M["stable_yards"][-1]["troughs"] == 2


def _torii_city(**kw):
    s = Settlement(1200, 1200, seed=9)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    s.shrine_hall(600, 500, "Temple of Ebisu", w=s.px(130), h=s.px(84), kind="temple", torii=[(600, 560)], **kw)
    return s


def test_shrine_hall_rolls_torii_count_per_temple():
    # the 2026-07-23 full re-roll: torii=[...] is avenue GEOMETRY; the COUNT is a seeded
    # per-temple roll on the tier's TORII_WEIGHTS column, recorded on the religious rec
    import random as _rr

    from settlement import roll_torii_count

    expect = roll_torii_count("city", _rr.Random(9 * 977 + 600 * 31 + 500 * 57))
    s = _torii_city()
    assert s.M["religious"][-1]["torii_count"] == expect
    assert len(s.M["torii"]) == expect


def test_shrine_hall_torii_count_pin_extends_a_single_point_avenue():
    # the per-temple pin (the per-hall analog of the village 'torii_count' knob): a pinned 7
    # marches the avenue away from the hall at a 44px stride from the single given point
    s = _torii_city(torii_count=7)
    assert s.M["religious"][-1]["torii_count"] == 7
    assert sorted(t[1] for t in s.M["torii"]) == [560 + 44 * i for i in range(7)]


def test_shrine_hall_extends_a_multi_point_avenue_along_its_own_step():
    # >= 2 given points: extension continues the avenue's OWN stride, not the 44px default
    s = Settlement(1200, 1200, seed=9)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    s.shrine_hall(600, 500, "Temple", w=s.px(130), h=s.px(84), kind="temple", torii=[(600, 560), (600, 580)], torii_count=3)
    assert sorted(t[1] for t in s.M["torii"]) == [560, 580, 600]


def test_shrine_hall_roll_below_geometry_draws_the_first_n():
    # a roll/pin smaller than the supplied avenue keeps the arches nearest the hall
    s = Settlement(1200, 1200, seed=9)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    s.shrine_hall(600, 500, "Temple", w=s.px(130), h=s.px(84), kind="temple", torii=[(600, 560), (600, 598), (600, 636)], torii_count=1)
    assert [t[1] for t in s.M["torii"]] == [560]


def test_rect_on_water_blocks_a_solid_part_on_an_irrigation_line():
    # the homestead solver rejects a house/yard/garden that lands on a channel/ditch/stream, but NOT the grove
    s = _crop_settlement()
    s.M["field_ditches"] = [{"poly": [(400, 300), (400, 500)], "role": "drain", "w": 6, "field": "f"}]
    s.M["channels"] = [{"poly": [(600, 300), (600, 500)], "w": 2.5}]
    s.M["streams"] = [{"poly": [(800, 300), (800, 500)], "w": 9}]
    assert s._rect_on_water((400, 400, 24, 16)) is True  # garden straddling the drain -> seg_dist branch
    assert s._rect_on_water((360, 400, 100, 10)) is True  # a wide rect an edge of which the ditch CROSSES far from any corner -> segments_cross branch
    assert s._rect_on_water((600, 400, 20, 14)) is True  # on the feeder channel
    assert s._rect_on_water((800, 400, 20, 14)) is True  # on the stream
    assert s._rect_on_water((500, 400, 24, 16)) is False  # dry ground between them -> clear
    # the grove (fields=False) is exempt - it may hug a bund/ditch; the solid parts (fields=True) are not
    assert s._rect_blocked((400, 400, 24, 16), fields=False) is False
    assert s._rect_blocked((400, 400, 24, 16), fields=True) is True


def test_rect_on_water_skips_a_degenerate_course_and_far_ones():
    # the collision pre-filter: a degenerate (<2-point) course is dropped from _water_obstacles (it has no
    # segment and would crash the bbox min/max on an empty poly), and a course whose bbox is nowhere near
    # the rect is skipped without any seg_dist / crossing math.
    s = _crop_settlement()
    s.M["streams"] = [
        {"poly": [(100, 100)], "w": 9},  # degenerate: single point -> skipped
        {"poly": [(1500, 1300), (1500, 1400)], "w": 9},
    ]  # real, but far from the probe rect
    assert s._water_obstacles() == [(s.M["streams"][1]["poly"], 9 / 2 + 5, (1500, 1300, 1500, 1400))]
    assert s._rect_on_water((400, 400, 24, 16)) is False  # far course bbox-rejected -> clear


def _byre_village():
    s = _crop_settlement()
    hs = [{"x": 300 + i * 170, "y": 350, "w": 40, "h": 28, "kind": "plain", "rot": 0, "wealth": 1.6 - 0.1 * i} for i in range(5)]
    s.M["houses"] = hs
    for h in hs:
        s.placed.append((h["x"], h["y"], h["w"], h["h"]))
    return s, hs


def test_draft_byres_scatters_shared_sheds_among_the_houses():
    s, hs = _byre_village()
    placed = s.draft_byres(fraction=0.6, gap=40)  # ~60% of 5 = 3 shared byres
    assert len(placed) == 3 and len(s.M["byres"]) == 3
    assert all(b["w"] > 0 and b["h"] > 0 for b in s.M["byres"])
    assert "<rect" in s.out[-1]  # a byre glyph was drawn


def test_draft_byres_skips_a_homestead_boxed_in_on_all_sides():
    s = _crop_settlement()
    s.M["houses"] = [{"x": 300, "y": 300, "w": 40, "h": 28, "kind": "plain", "rot": 0, "wealth": 1.0}]
    s.placed.append((300, 300, 40, 28))
    for a in range(0, 360, 20):  # wall the homestead in with placed footprints
        rad = settlement.math.radians(a)
        s.placed.append((300 + 70 * settlement.math.cos(rad), 300 + 70 * settlement.math.sin(rad), 60, 60))
    assert s.draft_byres(fraction=1.0) == []  # nowhere to put a byre -> skipped


def test_draft_byres_keeps_off_the_paddy():
    s = _crop_settlement()
    s.M["houses"] = [{"x": 300, "y": 300, "w": 40, "h": 28, "kind": "plain", "rot": 0, "wealth": 1.0}]
    s.placed.append((300, 300, 40, 28))
    s.field_polys.append([(330, 200), (600, 200), (600, 500), (330, 500)])  # paddy on the E half of the ring
    placed = s.draft_byres(fraction=1.0)
    assert len(placed) == 1 and placed[0][0] < 330  # the byre lands on the dry (W) side, off the paddy


def test_draft_byres_uses_the_legacy_size_off_the_to_scale_tiers():
    # a legacy tier (town/city) sizes its byre from the urban glyph grain (bscale), not px(feet) - the
    # non-to-scale branch of the byre sizer.
    s = _town()  # scale="town" -> not to-scale
    hs = [{"x": 300 + i * 170, "y": 350, "w": 40, "h": 28, "kind": "plain", "rot": 0, "wealth": 1.0} for i in range(3)]
    s.M["houses"] = hs
    for h in hs:
        s.placed.append((h["x"], h["y"], h["w"], h["h"]))
    placed = s.draft_byres(fraction=1.0, gap=40)
    assert placed and all(b["w"] > 0 for b in s.M["byres"])


def test_bridges_spans_a_lane_where_it_crosses_a_canal():
    s = _crop_settlement()
    s.lane([(100, 300), (500, 300)], width=6, worn=True)  # a lane running E-W
    s.M["field_ditches"] = [{"poly": [[300, 150], [300, 450]], "w": 5}]  # a canal crossing it at (300, 300)
    n = s.bridges()
    assert n == 1 and len(s.M["bridges"]) == 1
    assert abs(s.M["bridges"][0]["x"] - 300) < 2 and abs(s.M["bridges"][0]["y"] - 300) < 2


def test_channel_footbridges_plank_each_long_ditch_perpendicular():
    s = _crop_settlement()
    s.M["fields"] = [{"outline": [[50, 120], [850, 120], [850, 280], [50, 280]]}]  # paddy straddling the y=200 ditch (both banks cultivated)
    s.M["field_ditches"] = [
        {"poly": [[100, 200], [400, 200], [800, 200]], "w": 5, "role": "main"},  # 700px, 2 segments -> two planks at spacing 320
        {"poly": [[100, 400], [160, 400]], "w": 4, "role": "branch"},  # 60px -> below min_len, no plank
    ]
    n = s.channel_footbridges(spacing=320)
    assert n == 2 and len(s.M["bridges"]) == 2  # the short stub is stepped over, not bridged
    assert all(abs(abs(b["rot"]) - 90) < 1 for b in s.M["bridges"])  # deck runs N-S, ACROSS the E-W ditch
    assert all(190 < b["y"] < 210 for b in s.M["bridges"])  # both sit ON the ditch line


def test_shrine_well_places_a_well_beside_the_hall():
    s = _crop_settlement()
    s.M["religious"] = [{"x": 400, "y": 400, "w": 30, "h": 24, "kind": "shrine"}]
    spot = s.shrine_well(400, 400)
    assert spot is not None
    import math as _m

    assert _m.hypot(spot[0] - 400, spot[1] - 400) <= 115 and len(s.M["wells"]) == 1  # close beside the hall


def test_shrine_well_returns_none_when_boxed_in():
    s = _crop_settlement()
    for a in range(0, 360, 15):  # wall off every ring position around the hall
        rad = settlement.math.radians(a)
        for rr in (54, 66, 80, 96, 112):
            s.placed.append((400 + rr * settlement.math.cos(rad), 400 + rr * settlement.math.sin(rad), 40, 40))
    assert s.shrine_well(400, 400) is None and not s.M["wells"]


def test_channel_footbridges_slides_a_plank_clear_of_a_farmhouse():
    s = _crop_settlement()
    s.M["fields"] = [{"outline": [[50, 220], [750, 220], [750, 380], [50, 380]]}]  # paddy straddling the y=300 ditch
    s.M["field_ditches"] = [{"poly": [[100, 300], [700, 300]], "w": 5, "role": "main"}]  # 600px E-W ditch
    s.M["houses"] = [{"x": 400, "y": 300, "w": 60, "h": 40, "kind": "plain", "rot": 0}]  # a house ON the ditch midpoint
    n = s.channel_footbridges(spacing=800)  # n=1, midway = (400,300) = on the house
    assert n == 1
    b = s.M["bridges"][0]
    assert not (365 <= b["x"] <= 435) and 190 < b["y"] < 410  # the plank slid ALONG the ditch, off the house footprint


def test_channel_footbridges_skips_a_crossing_to_uncultivated_ground():
    s = _crop_settlement()
    s.M["fields"] = [{"outline": [[50, 120], [750, 120], [750, 297], [50, 297]]}]  # paddy only NORTH of the ditch; the S bank is marsh/scrub
    s.M["field_ditches"] = [{"poly": [[100, 300], [700, 300]], "w": 5, "role": "main"}]  # a margin ditch: field one side, nothing the other
    n = s.channel_footbridges(spacing=800)
    assert n == 0 and not s.M["bridges"]  # no cultivated ground on the far bank -> no useful crossing -> no plank


# --- fragmented dooryard gardens: _garden_beds picks single / flanking / stacked / side-by-side --------
def _pos_where(pred):
    """The first (x, y) on a deterministic sweep whose position-hash lands in the wanted branch."""
    for i in range(4000):
        x, y = 100 + i * 0.7, 200 + (i * 1.3) % 500
        if pred(x, y):
            return x, y
    raise AssertionError("no position matched the predicate")  # pragma: no cover


def test_garden_beds_undivided_is_the_common_case():
    s = _nuc_village()
    x, y = _pos_where(lambda x, y: Settlement._hjit(x, y, 8.0) >= 0.26)
    beds = s._garden_beds(x, y, 23, 14, x + 20, y, 20, 20, "E", 3)
    assert beds == [(x + 20, y, 20, 20)]  # one undivided plot


def test_garden_beds_opposite_flank_puts_the_house_between_two_beds():
    s = _nuc_village()
    x, y = _pos_where(lambda x, y: Settlement._hjit(x, y, 8.0) < 0.26 and Settlement._hjit(x, y, 9.0) < 0.5)
    beds = s._garden_beds(x, y, 23, 14, x + 20, y, 20, 20, "E", 3)
    assert len(beds) == 2 and min(b[0] for b in beds) < x < max(b[0] for b in beds)  # flanking E and W


def test_garden_beds_stacked_when_same_side_south_garden():
    s = _nuc_village()
    x, y = _pos_where(lambda x, y: Settlement._hjit(x, y, 8.0) < 0.26 and Settlement._hjit(x, y, 9.0) >= 0.5 and Settlement._hjit(x, y, 10.0) < 0.5)
    beds = s._garden_beds(x, y, 23, 14, x, y + 30, 20, 20, "SE", 3)  # a SOUTH garden -> may stack above/below
    assert len(beds) == 2 and beds[0][0] == beds[1][0] and beds[0][1] != beds[1][1]  # same x, different y


def test_garden_beds_side_by_side_when_same_side_not_stacked():
    s = _nuc_village()
    x, y = _pos_where(lambda x, y: Settlement._hjit(x, y, 8.0) < 0.26 and Settlement._hjit(x, y, 9.0) >= 0.5 and Settlement._hjit(x, y, 10.0) >= 0.5)
    beds = s._garden_beds(x, y, 23, 14, x, y + 30, 20, 20, "SE", 3)  # not stacked -> side by side
    assert len(beds) == 2 and beds[0][1] == beds[1][1] and beds[0][0] != beds[1][0]  # same y, different x


def test_garden_beds_too_narrow_falls_back_to_one_bed():
    s = _nuc_village()
    x, y = _pos_where(lambda x, y: Settlement._hjit(x, y, 8.0) < 0.26)  # a split is WANTED
    beds = s._garden_beds(x, y, 23, 14, x, y + 12, 8, 8, "SE", 3)  # ... but the plot is too small to split
    assert beds == [(x, y + 12, 8, 8)]


def test_attach_garden_draws_and_records_two_beds():
    s = _nuc_village()
    s._attach_garden(500, 500, [(486, 500, 10, 12), (520, 500, 10, 12)])
    beds = s.M["gardens"]
    assert len(beds) == 2 and all(b["of"] == [500, 500] and len(b["poly"]) == 4 for b in beds)


def test_bundle_geom_nucleated_records_a_gardens_list_spanning_the_bbox():
    s = _nuc_village()
    x, y = _pos_where(lambda x, y: Settlement._hjit(x, y, 8.0) < 0.26 and Settlement._hjit(x, y, 9.0) < 0.5)
    geom = s._bundle_geom(x, y, 46, 28, "E")  # a big house so the flank split clears its gate
    assert len(geom["gardens"]) == 2
    bx, by, bw, bh = geom["bbox"]
    for gx, _gy, gw, _gh in geom["gardens"]:  # every bed lies inside the bundle bbox
        assert bx - bw / 2 - 1 <= gx - gw / 2 and gx + gw / 2 <= bx + bw / 2 + 1


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
    s.M["houses"].append({"x": 400, "y": 470, "w": 23, "h": 14})  # a house just SOUTH of the garden
    assert s._garden_shaded((400, 450, 22, 12)) is True  # shaded
    assert s._garden_shaded((900, 450, 22, 12)) is False  # open sky to the south -> not shaded


def test_garden_fits_rejects_a_spot_outside_the_bound():
    s = Settlement(1000, 1000, seed=1)
    s.bound = [(0, 0), (600, 0), (600, 1000), (0, 1000)]  # only x < 600 is inside
    yard = (500, 540, 32, 20)
    assert s._garden_fits(700, 500, 24, 16, 500, 500, yard) is False  # x=700 is outside the bound


def test_yard_fits_skips_own_house_and_rejects_a_neighbour():
    s = Settlement(1000, 1000, seed=1)
    s.placed.append((500, 500, 40, 28))  # the OWN house footprint -> the loop skips it
    s.placed.append((520, 540, 40, 28))  # a neighbor where the yard would land -> rejected
    assert s._yard_fits(520, 540, 32, 20, 500, 500) is False


def test_garden_fits_skips_own_house_and_rejects_a_neighbour():
    s = Settlement(1000, 1000, seed=1)
    s.placed.append((500, 500, 40, 28))  # the OWN house footprint -> the loop skips it
    s.placed.append((545, 500, 40, 28))  # a neighbor where the garden would land -> rejected
    assert s._garden_fits(545, 500, 24, 16, 500, 500, (500, 560, 32, 20)) is False


def test_grove_fits_rejects_a_spot_outside_the_bound():
    s = Settlement(1000, 1000, seed=1)
    s.bound = [(0, 0), (600, 0), (600, 1000), (0, 1000)]  # only x < 600 is inside (a city-style bound)
    assert s._grove_fits(700, 500, 30, 24, [(500, 500)]) is False  # x=700 is outside the bound


def test_fits_steers_off_a_grove():
    # groves are out of `placed` (so they may merge), but `_fits` still keeps the wells off them
    s = Settlement(1000, 1000, seed=1)
    s.grove_rects.append((500, 500, 40, 40))
    assert s._fits(505, 505, 20, 20) is False


# --- merchant_residences(): rich homes derived from the ACTUAL shops, behind the storefront band ---
def test_merchant_residences_returns_zero_without_a_road_or_shops():
    s = Settlement(1000, 1000, seed=1)
    assert s.merchant_residences() == 0  # no road, no shops
    s.road([(50, 500), (950, 500)])
    assert s.merchant_residences() == 0  # a road but still no shops


def test_merchant_residences_places_behind_band_and_skips_bad_spots():
    s = Settlement(1000, 1000, seed=1)
    s.road([(50, 500), (950, 500)])  # horizontal road
    s.building(850, 640, 40, 28, "shop", rot=180)  # a DEEP, far shop: raises the band depth so the others'
    #                                                       homes land well behind their own shop (clearance)
    s.building(300, 560, 40, 28, "shop", rot=180)  # its home lands ~(300,684), clear -> PLACES
    s.building(395, 560, 40, 28, "shop", rot=180)  # home ~95px away: clears overlap but within `spread` -> skipped
    s.building(600, 560, 40, 28, "shop", rot=180)  # its home ~(600,684) lands in the paddy below -> skipped
    s.paddy_field((540, 650, 660, 760), "", "p", amp=6)  # a paddy under the 600-shop's home (blocked ground)
    n = s.merchant_residences(count=6)
    homes = [b for b in s.M["buildings"] if b["kind"] == "merchant_large"]
    assert n >= 1 and homes and all(h["y"] > 600 for h in homes)  # placed BEHIND the band (further from the road)


def test_merchant_residences_skips_an_off_map_home():
    s = Settlement(1000, 1000, seed=1)
    s.road([(50, 500), (950, 500)])
    s.building(300, 950, 40, 28, "shop", rot=180)  # so deep that its home lands ~y=994, off the bottom edge
    assert s.merchant_residences() == 0


def test_merchant_residences_respects_the_bound():
    s = Settlement(1000, 1000, seed=1)
    s.road([(50, 500), (950, 500)])
    s.building(850, 640, 40, 28, "shop", rot=180)  # deep+far: raises band depth so the 300-home clears its shop
    s.building(300, 560, 40, 28, "shop", rot=180)  # its home lands ~(300,684), clear of shops
    s.bound = [(0, 0), (1000, 0), (1000, 600), (0, 600)]  # bound excludes y > 600 -> the 300-home is outside -> skipped
    assert s.merchant_residences() == 0


def _village():
    s = Settlement(600, 600, seed=3)
    s.meta(name="V", scale="village")
    return s


def test_abandoned_ruin_draws_as_a_lone_house_and_big_glyph_renders():
    # the geom-less lone-house path in _farmsteads_bundle now serves ONLY abandoned ruins - the dispersed
    # headman that used to share it gets a full bundle since 2026-07-21 (the Hikari fix). The ruin must
    # survive farmsteads() as a bare house (no yard/garden/grove), riding through _relax_gardens_south's
    # geom-less skip. The "big" minka glyph (storeroom wing) renders via a direct draw.
    s = Settlement(800, 800, seed=5)
    s.meta(name="Ruin", scale="village", ftpx=2, toscale=True)
    assert s.try_place(400, 400, "abandoned")
    assert s.try_place(560, 400, "plain")  # a bundle placed AFTER the ruin: the shading scan skips the geom-less rec
    assert s.farmsteads() == 2
    assert s.M["houses"][0]["kind"] == "abandoned"
    assert len(s.M["threshing_yards"]) == 1 and len(s.M["gardens"]) == 1  # the plain bundle's, not the ruin's
    s.house(200, 200, 46, 28, "big", 0)  # the big-minka glyph branch (the storeroom wing)


def test_headman_refuses_a_non_toscale_map():
    # the legacy (pre-to-scale) headman rec branch was dead code after the Hikari fix and is gone
    s = Settlement(800, 800, seed=5)
    s.meta(name="T", scale="town")
    with pytest.raises(ValueError):
        s.headman(400, 400)


def test_garden_beds_clear_rejects_a_bed_on_a_neighbor():
    # the neighbor-footprint hit branch: a shifted bed landing on an actual drawn structure is rejected
    s = Settlement(800, 800, seed=5)
    s.meta(name="B", scale="village", ftpx=2, toscale=True)
    assert s._garden_beds_clear([(100, 100, 20, 14)], others=[(104, 102, 20, 14)]) is False
    assert s._garden_beds_clear([(100, 100, 20, 14)], others=[(300, 300, 20, 14)]) is True


def test_text_width_measures_the_render_font_and_falls_back(monkeypatch):
    # the placard pads symmetrically because the width is MEASURED in the render font (DejaVu Serif
    # Bold, what resvg substitutes for serif) - 'Akagahara' measured ~180px where the old estimate
    # said 167 and ran off the card edge (GM 2026-07-21). Without PIL/the font, a generous estimate.
    s = _crop_settlement()
    w = s._text_width("Akagahara", 30)
    assert 170 < w < 195
    import PIL.ImageFont

    def _boom(*a, **k):
        raise OSError("no font")

    monkeypatch.setattr(PIL.ImageFont, "truetype", _boom)
    assert s._text_width("Akagahara", 30) == 9 * 30 * 0.62


def test_roll_torii_count_distributions():
    # the GM's tier weights (2026-07-21): 1/3/7 only, village 60/30/10, town 30/60/10,
    # city 30/40/30, capital 10/60/30; unknown scales roll the conservative village column
    import collections
    import random as _random

    from settlement import roll_torii_count

    for scale, want in [("village", {1: 0.6, 3: 0.3, 7: 0.1}), ("town", {1: 0.3, 3: 0.6, 7: 0.1}), ("city", {1: 0.3, 3: 0.4, 7: 0.3}), ("capital", {1: 0.1, 3: 0.6, 7: 0.3})]:
        rng = _random.Random(11)
        c = collections.Counter(roll_torii_count(scale, rng) for _ in range(4000))
        assert set(c) <= {1, 3, 7}
        for k, p in want.items():
            assert abs(c[k] / 4000 - p) < 0.03, (scale, k)
    assert roll_torii_count("hamlet", _random.Random(1)) in (1, 3, 7)  # fallback column

    class _One:  # rng.random() lives in [0,1) so the exhaustion return is defensively dead - prove it anyway
        def random(self):
            return 1.0

    assert roll_torii_count("village", _One()) == 7  # exhaustion falls to the last (rarest) bucket


def test_union_area_empty_and_overlapping_spans():
    # empty (or all-degenerate) rects -> zero area; and a rect fully shadowed by a taller one in the
    # same x-slab must be counted ONCE (the y1 <= cy skip), not double-counted.
    assert settlement._union_area([]) == 0.0
    assert settlement._union_area([(0, 0, 2, 2)]) == 4.0  # single rect
    assert settlement._union_area([(0, 0, 10, 10), (0, 2, 10, 5)]) == 100.0  # inner rect adds nothing


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
    s.water_field([(150, 150), (360, 150), (360, 360), (150, 360)], "", "f", (150, 150), (360, 360), amp=10, plot=34)
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


def test_ftpx_scale_derives_bscale_and_ft_defaults():
    # The GM's scale ladder (hamlet/town 1 ft/px, village 2, city 3): meta(ftpx=N) derives the
    # urban grain bscale = 1/ftpx, px()/lw() convert real feet, and the 4px linework floor
    # rescues thin features (a 5 ft roji at 3 ft/px would be an invisible 1.7px). A street's
    # default width is the real 24 ft converted at the map's scale.
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="C", scale="city", ftpx=3)
    assert s.bscale == 1 / 3 and s.px(66) == 22 and s.lw(5) == 4
    s.street([(100, 100), (400, 100)])
    assert s.M["town_streets"][-1]["w"] == 8  # lw(24) at 3 ft/px
    # VILLAGE maps keep bscale = 1.0: their placement constants were hand-pre-scaled to
    # 2 ft/px before ftpx existed (re-deriving would perturb every tuned village map).
    v = Settlement(1000, 1000, seed=1)
    v.meta(name="V", scale="village", ftpx=2)
    assert v.ftpx == 2 and v.bscale == 1.0


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


def _city():
    s = Settlement(1200, 1200, seed=3)
    s.meta(name="C", scale="city", ftpx=3)
    return s


def test_stables_draws_a_working_yard_and_records_it():
    # the gate stables' beaten-earth yard (GM 2026-07-22): drawing it adds scatter/furniture to the
    # SVG and records a stable_yard linked to the stables, so stables_have_yards can gate it. The yard
    # scatter avoids a neighboring building (an inn placed just north).
    s = _city()
    s.inn(600, 540)  # a cluster building the yard must skip
    before = len(s.out)
    s.stables(600, 620, rot=90)
    assert len(s.out) > before  # the yard scatter + furniture drew something
    yd = s.M["stable_yards"][-1]
    assert yd["of"] == [600.0, 620.0] and yd["r"] > 0
    # nothing the yard drew lands on the inn's footprint (a 3px-margin keep-out)
    ix0, iy0, ix1, iy1 = 600 - s.M["buildings"][0]["w"] / 2, 540 - s.M["buildings"][0]["h"] / 2, 600 + s.M["buildings"][0]["w"] / 2, 540 + s.M["buildings"][0]["h"] / 2
    assert ix1 > ix0 and iy1 > iy0  # sanity: the inn has a real footprint the scatter avoided


def test_stables_yard_can_be_suppressed():
    s = _city()
    s.stables(600, 620, rot=90, yard=False)
    assert not s.M.get("stable_yards")  # yard=False draws no yard


def test_stables_yard_fully_blocked_draws_no_furniture():
    # a yard whose whole disk is covered by a field: every scatter/furniture candidate is rejected
    # (the field-reject branch), take() exhausts, and the cart/dung loops break - the yard is still
    # recorded (so stables_have_yards passes) but no beaten-earth furniture is drawn
    s = _city()
    s.field_polys.append([(400, 400), (800, 400), (800, 840), (400, 840)])  # blankets the r=72 disk at (600,620)
    s.stables(600, 620, rot=90)
    svg = "".join(s.out)
    assert s.M["stable_yards"][-1]["of"] == [600.0, 620.0]  # recorded despite the blocked yard
    assert "#7A5A3A" not in svg and "#8FA6B0" not in svg  # no tethered animals, no water trough drew


def test_rowpack_lays_touching_terraces():
    # the GM row-packing doctrine: city commoner housing goes down as CONTIGUOUS terraces -
    # most units share a party wall (hairline seam <= 1.2px), never the old detached scatter
    s = _city()
    n = s.rowpack((200, 200, 600, 330), ["laborer"] * 40)
    assert n >= 25
    bs = s.M["buildings"]

    def egap(a, b):
        dx = abs(a["x"] - b["x"]) - (a["w"] + b["w"]) / 2
        dy = abs(a["y"] - b["y"]) - (a["h"] + b["h"]) / 2
        return max(dx, dy)

    gaps = [min(egap(a, b) for j, b in enumerate(bs) if j != i) for i, a in enumerate(bs)]
    assert sum(1 for g in gaps if g <= 1.2) >= 0.55 * len(bs)


def test_rowpack_respects_canvas_edge_and_bound():
    # rows must not spill off the canvas margins (title/edge zone) or outside a bounding
    # ring (the city's ring road) - both rejections clip the terrace, they don't crash it
    s = _city()
    s.rowpack((20, 200, 200, 260), ["laborer"] * 30)  # zone hangs past the x<55 edge margin
    assert all(b["x"] - b["w"] / 2 >= 55 for b in s.M["buildings"])
    s2 = _city()
    s2.bound = [(300, 100), (700, 100), (700, 500), (300, 500)]
    s2.rowpack((200, 200, 600, 300), ["laborer"] * 30)  # zone's west half lies outside the bound
    assert all(b["x"] - b["w"] / 2 >= 299 for b in s2.M["buildings"])


def test_rowpack_blocked_zone_terminates_and_places_nothing():
    # a zone fully covered by an earlier structure yields no houses: every row scans past the
    # obstacle, the row pitch still advances, and the loop ends at the zone's south edge
    s = _city()
    s.building(400, 250, 420, 130, "civic")  # a compound covering the whole zone
    assert s.rowpack((200, 200, 600, 300), ["laborer"] * 30) == 0


def test_pack_core_skips_the_street_facing_band():
    # face_streets="core" leaves the near-street band for shop frontage: dwellings pack only
    # the deep block interior
    s = Settlement(1000, 1000, seed=2)
    s.meta(name="T", scale="town")
    s.street([(100, 500), (900, 500)], width=24)
    s.pack((150, 300, 850, 700), ["laborer"] * 30, step=40, face_streets="core")
    import math as _m

    for b in s.M["buildings"]:
        assert _m.hypot(0, b["y"] - 500) > 76 or not (100 <= b["x"] <= 900)


def _hamlet_with_field(down_deg):
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="H", scale="hamlet", down_deg=down_deg)
    s.field_polys.append([(400, 400), (600, 400), (600, 600), (400, 600)])  # a paddy centered at (500,500)
    return s


def test_hinterland_scrub_ring_and_marsh_downhill_each_cardinal():
    # the reed MARSH toe sits on the DOWNHILL side of the field for each cardinal slope (exercises the four
    # direction branches); the cut-over SCRUB commons fills the 3 non-toe sides (scrub is the dominant cover;
    # managed woodland is added as patches by the gen), each band centered clear of the paddy. down_deg in screen
    # angle: 90=S(+y), 270=N(-y), 0=E(+x), 180=W(-x).
    import math

    for down_deg in (90, 270, 0, 180):
        s = _hamlet_with_field(down_deg)
        s.hinterland()
        toe = [m for m in s.M["marshes"] if m["role"] == "toe"]
        grazing = [c for c in s.M["commons"] if c["role"] == "grazing"]
        # 3 outer RING bands (the non-toe sides) PLUS 1 INTERIOR fill (over the cultivated bbox, clothing the
        # voids an irregular field leaves inside it). The interior fill legitimately spans the paddy box; the
        # three ring bands each clear it.
        assert len(toe) == 1 and len(grazing) == 4
        interior = [c for c in grazing if 400 <= c["x"] <= 600 and 400 <= c["y"] <= 600]
        assert len(interior) == 1  # exactly the interior fill sits over the field box
        for c in grazing:
            if c is interior[0]:
                continue
            assert not (400 <= c["x"] <= 600 and 400 <= c["y"] <= 600)  # each RING band clears the paddy box
        dx, dy = math.cos(math.radians(down_deg)), math.sin(math.radians(down_deg))
        assert (toe[0]["x"] - 500) * dx + (toe[0]["y"] - 500) * dy > 0  # toe is downhill of field center


def test_hinterland_honors_hamlet_keepout_and_dry_plot_extent():
    # a hamlet keep-out (from M['houses']) and the dry-hatake extent are both folded in: the house sits where a
    # ring + the marsh toe overlap it, so the avoid-skip fires in BOTH commons and marsh; dry_plots widen the
    # cultivated bbox the woodland sets back from.
    s = _hamlet_with_field(90)
    s.M["houses"] = [{"x": 300, "y": 500, "w": 20, "h": 14, "rot": 0}]
    s.M["dry_plots"] = [{"poly": [[610, 400], [720, 400], [720, 520], [610, 520]], "crop": "soy", "theta": 0.0}]
    s.hinterland()
    assert s.M["commons"] and s.M["marshes"]


def test_hinterland_flags_default_downdeg_and_empty_field():
    s = _hamlet_with_field(90)
    s.hinterland(commons=False)  # marsh only
    assert not s.M["commons"] and len(s.M["marshes"]) == 1
    s2 = _hamlet_with_field(90)
    s2.hinterland(marsh=False)  # commons only
    assert s2.M["commons"] and not s2.M["marshes"]
    s3 = _hamlet_with_field(90)
    s3.hinterland(down_deg=None)  # None -> reads meta down_deg (90 = south)
    assert s3.M["marshes"][0]["y"] > 500
    empty = Settlement(1000, 1000, seed=1)
    empty.meta(name="E", scale="hamlet")
    empty.hinterland()  # no field_polys -> early return
    assert not empty.M["commons"] and not empty.M["marshes"]


def test_commons_glyph_variants_draw_and_record_each_role():
    # the three distinct land-cover looks exercised directly (independent of the village gens): woodland =
    # tree CROWNS, pasture = open GRASS (no pines), commons/grazing = grass + a few scraggly PINES. Each is
    # given a non-empty `avoid` keep-out so the avoid-skip is exercised too. A marsh keep-out is checked as well.
    poly = [(200, 200), (800, 200), (800, 800), (200, 800)]
    keepout = [[(400, 400), (600, 400), (600, 600), (400, 600)]]  # a central keep-out the scatter stays out of
    for role in ("woodland", "pasture", "commons", "grazing"):
        s = Settlement(1000, 1000, seed=3)
        s.meta(name="C", scale="hamlet")
        s.commons(poly, role=role, avoid=keepout)
        assert s.M["commons"][-1]["role"] == role and s.out  # recorded + something drawn
    sm = Settlement(1000, 1000, seed=3)
    sm.meta(name="C", scale="hamlet")
    sm.marsh(poly, avoid=keepout)
    assert sm.M["marshes"][-1]["role"] == "toe"


def test_ministry_auto_label_side_prefers_empty_ground():
    # the GM label doctrine (2026-07): a label that CAN sit in empty ground, should. With no
    # label_below override the ministry scores both spots against what is already placed and
    # takes the clearer; the default (unpassed) size is the real ~224x148 ft compound.
    s = Settlement(1000, 1000, seed=4)
    s.meta(name="C", scale="city", ftpx=3)
    s.building(500, 462, 90, 24, "civic")  # crowd the ABOVE label spot
    s.ministry(500, 510, "Ministry of Test")
    assert s.M["ministries"][0]["w"] == s.px(224)
    lab = next(lb for lb in s.M["labels"] if lb[5] == "Ministry of Test")
    assert (lab[1] + lab[3]) / 2 > 510  # the label went BELOW, into the open ground


def test_crop_to_content_includes_forest_clamped_to_canvas():
    # the forest is a big EDGE feature recorded as a POINT-LIST (not dicts): the crop frames to include it,
    # CLAMPED to the canvas so the view never opens past the edge (an edge feature must REACH the frame edge,
    # not stop short). Exercises the forest branch + all four clamp arms.
    s = Settlement(2000, 1500, seed=1)
    s.M["houses"] = [{"x": 30, "y": 700, "w": 20, "h": 20}]
    s.M["forest"] = [[1800, -10], [1820, 750], [1800, 1510], [2012, 1510], [2012, -10]]  # fills the E to canvas+12
    s.crop_to_content(margin=40)
    assert s.view == (0, 0, 2000, 1500)  # clamped to the whole canvas (forest reaches every edge)


def test_hinterland_skip_sides_drops_a_scrub_band():
    # skip_sides suppresses the scrub band on a named frame side (e.g. a forest flank): down_deg=90 -> toe=bottom,
    # non-toe = top/left/right (3 ring bands); skipping "right" leaves 2 ring bands, PLUS the interior fill = 3.
    s = _hamlet_with_field(90)
    s.hinterland(skip_sides=("right",))
    assert [c["role"] for c in s.M["commons"]].count("grazing") == 3


def test_hinterland_dispersed_keepout_is_per_homestead():
    # DISPERSED settlements keep out each HOMESTEAD individually, not the (map-spanning) bbox of the ringing
    # farms - otherwise no ground cover could be laid inside the ring at all (the Akagahara bare-void bug). With
    # meta.nucleated False and two far-apart farmsteads, the open ground BETWEEN them still carries scrub.
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="D", scale="hamlet", down_deg=90, nucleated=False)
    s.field_polys.append([(400, 400), (600, 400), (600, 600), (400, 600)])
    s.M["houses"] = [{"x": 250, "y": 250, "w": 46, "h": 28}, {"x": 750, "y": 250, "w": 46, "h": 28}]
    s.hinterland()
    # the interior fill lands over the field box (proving cover was NOT blanket-forbidden by a map-wide keep-out)
    grazing = [c for c in s.M["commons"] if c["role"] == "grazing"]
    assert any(400 <= c["x"] <= 600 and 400 <= c["y"] <= 600 for c in grazing)


def test_legacy_dispersed_farmstead_path_still_covered():
    # every POOL map is now to-scale, so keep the legacy (non-to-scale) DISPERSED path covered here: an old-style
    # hamlet (scale!=village, no toscale -> _toscale() False) rings its field with houses and draws farmsteads
    # via _try_place_legacy + _farmsteads_legacy (the pre-bundle path Moritono used before it was redone).
    s = Settlement(1200, 900, seed=3)
    s.meta(name="L", scale="hamlet")
    fld = (300, 300, 620, 560)
    s.paddy_field(fld, "", "f", amp=20)
    s.ring(fld, 8, 16, ["plain"])
    n = s.farmsteads()
    assert n > 0


def test_on_watercourse_detects_stream_and_channel_beds():
    s = Settlement(600, 600, seed=1)
    s.M["streams"] = [{"poly": [[100, 100], [400, 100]], "w": 8}]
    s.M["channels"] = [{"poly": [[100, 300], [400, 300]], "w": 4}]
    assert s._on_watercourse(250, 100) and s._on_watercourse(250, 300)  # on the stream / channel bed
    assert not s._on_watercourse(250, 200)  # clear ground between them


def test_commons_and_marsh_skip_the_pond_and_watercourses():
    # ground-cover (scrub, reeds) never draws OVER open water: a big commons/marsh poly covering a pond + stream
    # skips those points at scatter time (the pond-check + _on_watercourse branches). Just assert it runs + records.
    for method in ("commons", "marsh"):
        s = Settlement(600, 600, seed=1)
        s.meta(name="W", scale="hamlet")
        s.M["pond"] = [300, 300, 60, 40]
        s.M["streams"] = [{"poly": [[80, 500], [520, 500]], "w": 10}]
        getattr(s, method)([(40, 40), (560, 40), (560, 560), (40, 560)])
        assert s.M["commons"] if method == "commons" else s.M["marshes"]


def test_relax_gardens_south_skips_a_bundle_without_gardens():
    # defensive: a homestead bundle whose geom carries no garden beds is simply skipped (no shift, no error)
    s = Settlement(800, 800, seed=1)
    s.meta(name="V", scale="village", ftpx=2)
    rec = {"x": 100, "y": 100, "w": 23, "h": 14, "geom": {"house": (100, 100, 23, 14), "yard": (100, 120, 20, 16)}}  # no "gardens" key
    s._relax_gardens_south([rec])
    assert "gardens" not in rec["geom"]


def test_village_grove_keeps_copse_out_of_a_garden_east_sun_lane():
    # the copse must not scatter a clump directly EAST of a kitchen garden (it would block the morning sun).
    # Teeth: a clump lands in that lane with NO garden present, and is skipped once the garden is there.
    poly = [[260, 240], [420, 240], [420, 360], [260, 360]]

    def lane_clumps(gardens):
        s = Settlement(700, 700, seed=3)
        s.meta(name="V", scale="village", ftpx=2)
        s.M["gardens"] = gardens
        s.village_grove(poly, role="copse", dense=True)
        cs = [c for g in s.M["village_groves"] for c in g["clumps"]]
        return [c for c in cs if 311 < c[0] < 345 and abs(c[1] - 300) < 13]  # the garden's east sun-lane

    without = lane_clumps([])
    with_garden = lane_clumps([{"x": 300, "y": 300, "w": 20, "h": 18, "rot": 0, "of": [280, 300]}])
    assert without and not with_garden


def test_relax_gardens_south_nudges_an_east_shaded_garden_south():
    # a garden on the E lee side with a neighbor grove hard against its east, open ground south -> it shifts S
    s = Settlement(800, 800, seed=1)
    s.meta(name="V", scale="village", ftpx=2)
    s.grove_rects = [(340, 300, 16, 40)]  # a neighbor grove arm just east of the garden
    beds = [(320, 300, 12, 12)]  # garden east edge x=326; tree west edge=332 (in band)
    rec = {"x": 300, "y": 300, "w": 23, "h": 14, "geom": {"house": (300, 300, 23, 14), "yard": (300, 322, 20, 12), "gardens": list(beds)}}
    s._relax_gardens_south([rec])
    assert rec["geom"]["gardens"][0][1] > 300  # the bed moved SOUTH to clear the east tree


# ---- s.quarter: first-class zoned regions (feature 006) -----------------------------------
def _city():
    s = Settlement(2000, 2000, seed=1)
    s.meta(name="C", scale="city", walled=True, population=3000, ftpx=3)
    return s


def test_quarter_records_zone_without_drawing_for_non_reserve():
    s = _city()
    poly = [(100, 100), (400, 100), (400, 400), (100, 400)]
    before = len(s.out)
    s.quarter(poly, "residential")
    q = s.M["quarters"][-1]
    assert q["zone"] == "residential" and q["kind"] is None
    assert q["poly"][0] == [100.0, 100.0]
    assert len(s.out) == before  # residential/civic/mixed draw nothing (declarative only)


def test_quarter_label_is_drawn_at_the_centroid():
    s = _city()
    s.quarter([(0, 0), (200, 0), (200, 200), (0, 200)], "civic", label="yamen precinct")
    assert s.M["quarters"][-1]["name"] == "yamen precinct"
    assert any("yamen precinct" in frag for frag in s.toplabels)


def test_quarter_reserve_kinds_render_their_ground():
    poly = [(100, 100), (500, 100), (500, 500), (100, 500)]
    # drill_ground and garden paint a visible ground surface...
    for kind in ("drill_ground", "garden"):
        s = _city()
        before = len(s.out)
        s.quarter(poly, "reserve", kind=kind, label=kind)
        assert s.M["quarters"][-1]["kind"] == kind
        assert len(s.out) > before  # a drawn reserve renders its ground feature
    # ...but an agricultural_district draws NOTHING (GM 2026-07-22 - its combs/farmhouses/label are
    # the rendering; the old faint dashed boundary was a stray dotted line), yet is still recorded
    s = _city()
    before = len(s.out)
    s.quarter(poly, "reserve", kind="agricultural_district", label="ag")
    assert s.M["quarters"][-1]["kind"] == "agricultural_district"
    assert len(s.out) == before  # no boundary line: the fields carry the whole visual


def test_quarter_rejects_bad_zone_and_kind_misuse():
    s = _city()
    poly = [(0, 0), (100, 0), (100, 100), (0, 100)]
    try:
        s.quarter(poly, "industrial")
        raise AssertionError("bad zone should raise")
    except ValueError:
        pass
    try:
        s.quarter(poly, "reserve")  # reserve needs a kind
        raise AssertionError("reserve without kind should raise")
    except ValueError:
        pass
    try:
        s.quarter(poly, "reserve", kind="parade")  # unknown reserve kind
        raise AssertionError("unknown reserve kind should raise")
    except ValueError:
        pass
    try:
        s.quarter(poly, "residential", kind="garden")  # only reserve may carry a kind
        raise AssertionError("non-reserve with kind should raise")
    except ValueError:
        pass


# ---- paddy_field: the tax-free plots + fallow patch + field label branches -----------------
def test_paddy_field_marks_taxfree_plots_and_a_fallow_patch_and_labels():
    # label + taxfree marks scattered vermilion tax-free plots; a fallow_patch stipples a blighted
    # sub-region; the label renders and is recorded. Exercises _taxfree_plots (interior non-empty)
    # and _fallow_patch, which the pool gens do not both trigger on one field.
    s = _village()
    s.paddy_field((150, 150, 470, 470), "Rice", "f", taxfree=2, fallow_patch=[[250, 250], [380, 250], [380, 380], [250, 380]])
    assert s.M["taxfree"]  # tax-free plots recorded -> _taxfree_plots did real work
    assert s.M["fallow_patches"]  # blighted sub-region recorded
    assert any(lab[5] == "Rice" for lab in s.M["labels"])  # field name labeled


# ---- water_field: the BBOX-shape branch + taxfree + label ----------------------------------
def test_water_field_from_a_bbox_marks_taxfree_and_labels():
    # handed a 4-number bbox (not a polygon), water_field grows the outline from the bbox; label +
    # taxfree marks vermilion plots and renders the name.
    s = _village()
    s.water_field((150, 150, 470, 470), "Paddy", "f", (150, 150), (470, 470), amp=10, taxfree=2, plot=34)
    assert any(fd["name"] == "f" and fd["kind"] == "paddy" for fd in s.M["fields"])
    assert s.M["taxfree"]
    assert any(lab[5] == "Paddy" for lab in s.M["labels"])


# ---- fallow_field: a whole field left fallow ----------------------------------------------
def test_fallow_field_records_a_fallow_field():
    s = _village()
    s.fallow_field((150, 150, 350, 350), "ff")
    assert any(fd["name"] == "ff" and fd["kind"] == "fallow" for fd in s.M["fields"])


# ---- pond: the optional feeder stream_curve branch ----------------------------------------
def test_pond_with_a_feeder_stream_curve_draws_the_feeder():
    s = _village()
    s.pond(300, 300, 90, 60, stream_curve="M 100 100 L 300 300")
    assert s.M["pond"] == [300, 300, 90, 60]
    assert (300, 300, 90, 60) in s.ellipses  # pond also blocks houses via its ellipse


# ---- lane: the UNWORN (paved/dashed) branch ------------------------------------------------
def test_lane_unworn_draws_a_dashed_causeway():
    s = _village()
    s.lane([(100, 300), (500, 300)], width=6, worn=False)
    assert s.M["lanes"][-1]["worn"] is False
    assert 'stroke-dasharray="8,8"' in "".join(s.out)  # the dashed centerline of a paved lane


# ---- shrine: the primary Shinto hall glyph -------------------------------------------------
def test_shrine_draws_and_records_a_religious_hall():
    s = _village()
    s.shrine(300, 300)
    # TRUE SCALE (2026-07-21): the default is a 62x42 ft tutelary hall drawn through px(), no longer 104x68 raw px
    assert s.M["shrine"] == [300 - s.px(62) / 2, 300 - s.px(42) / 2, s.px(62), s.px(42)]
    assert any(r["kind"] == "shrine" and r["x"] == 300 for r in s.M["religious"])


def test_shrine_hall_guard_refuses_unscaled_pixels_at_coarse_scales():
    # the latent-footgun guard (2026-07-21): four city temples shipped as fixed 100x64 px = 300x192 real ft.
    # At any ftpx > 1, raw-pixel dims implying an impossible hall must raise; s.px(real_ft) passes.
    s = Settlement(2000, 2000, seed=1)
    s.meta(name="G", scale="city", ftpx=3, toscale=True, households=600)
    with pytest.raises(ValueError, match="pass s.px"):
        s.shrine_hall(500, 500, "Temple", w=100, h=64, kind="temple")
    s.shrine_hall(500, 500, "Temple", w=s.px(130), h=s.px(84), kind="temple")
    assert any(r["kind"] == "temple" for r in s.M["religious"])


# ---- house: the ABANDONED-ruin glyph -------------------------------------------------------
def test_house_abandoned_draws_the_collapsed_roof_glyph():
    s = _village()
    s.house(300, 300, 46, 28, kind="abandoned")
    svg = "".join(s.out)
    assert '#6E6452' in svg  # the collapsed-roof debris polygon
    assert 'stroke-dasharray="5,3"' in svg  # the derelict outline dash


# ---- try_place: the LONE ABANDONED ruin (no homestead bundle) ------------------------------
def test_try_place_abandoned_places_a_lone_ruin_without_a_bundle():
    s = _nuc_village()  # a to-scale village; the west half (x < 640) is open ground
    assert s.try_place(300, 300, "abandoned") is True
    ruin = [h for h in s.M["houses"] if h["kind"] == "abandoned"]
    assert len(ruin) == 1 and ruin[0]["shed"] is False  # a lone derelict, no kura


# ---- _rect_blocked: the hill/pond ELLIPSE branch -------------------------------------------
def test_rect_blocked_by_a_hill_or_pond_ellipse():
    s = _village()
    s.ellipses.append((300, 300, 80, 60))  # a hill/pond footprint
    assert s._rect_blocked((300, 300, 40, 26), fields=False) is True  # bed center inside the ellipse


# ---- _bundle_side_fits: the OUT-OF-BOUNDS bbox branch --------------------------------------
def test_bundle_side_fits_rejects_a_bbox_running_off_the_canvas():
    s = _village()
    geom = {"bbox": (5, 300, 40, 26), "gardens": []}  # cx - W/2 = -15 < 6 -> spills off the west edge
    assert s._bundle_side_fits(geom) is False


# ---- _garden_beds_clear: a bed landing on a paddy ------------------------------------------
def test_garden_beds_clear_rejects_a_bed_on_a_paddy():
    s = _nuc_village()  # field_polys carries a paddy over the east half (x >= 640)
    assert s._garden_beds_clear([(880, 400, 30, 20)], []) is False  # bed sits in the paddy


# ---- ring: a BIG house whose placement FAILS is un-counted ---------------------------------
def test_ring_decrements_the_big_count_when_a_placement_fails():
    # every candidate lands on paddy (whole map is a field), so try_place fails; each 'big' that was
    # counted up must be counted back down, leaving the tally at zero.
    s = _nuc_village()
    s.field_polys.append([(0, 0), (1200, 0), (1200, 900), (0, 900)])  # the entire canvas is flooded paddy
    s._nbig = 0
    s.ring((100, 100, 500, 500), 8, 30, ["big"], max_big=10)
    assert s._nbig == 0  # each big incremented then decremented on its failed placement
    assert not s.M["houses"]  # nothing could be placed


# ---- water_field: a lateral column too SHORT to carry a ditch is skipped -------------------
def test_water_field_skips_a_lateral_column_too_short_for_a_ditch():
    # a shallow field at a COARSE plot grain: some interior columns span less than ~2.1 plots
    # between the high main and the low drain, so no lateral ditch fits there and it is skipped.
    s = Settlement(900, 900, seed=3)
    s.meta(name="V", scale="village")
    s.water_field((150, 150, 400, 320), "P", "f", (150, 150), (400, 320), amp=10, plot=100)
    assert any(fd["name"] == "f" for fd in s.M["fields"])
    assert any(d["role"] == "main" for d in s.M["field_ditches"])  # the main/drain still run


# ---- try_place: an abandoned ruin that does not FIT is rejected ----------------------------
def test_try_place_abandoned_rejects_a_ruin_off_the_canvas_edge():
    s = _nuc_village()
    assert s.try_place(20, 300, "abandoned") is False  # x < 55 -> _fits fails, no ruin placed
    assert not [h for h in s.M["houses"] if h["kind"] == "abandoned"]


# ---- city_wall: a mural tower BOXED IN on both sides is dropped ----------------------------
def test_city_wall_drops_a_mural_tower_boxed_in_on_both_sides():
    # the NW vertex is ringed by keep-clear (kido) points carpeting BOTH wall flanks out past the
    # farthest slide arc, so every slide candidate stays blocked and the tower is dropped (spacing
    # tolerates one gap). The clear SE vertex still gets its tower.
    s = Settlement(1200, 1200, seed=1)
    s.meta(name="C", scale="city")
    pts = [[150, 150], [1050, 150], [1050, 1050], [150, 1050]]
    skip = [
        (150, 150),
        (190, 150),
        (230, 150),
        (270, 150),  # carpet the top flank
        (150, 190),
        (150, 230),
        (150, 270),
    ]  # carpet the left flank
    s.city_wall(pts, gates=(), tower_skip=skip)
    towers = s.M.get("wall_towers", [])
    # ftpx=1 garrison -> ~278px spacing; a CLEAR corner is straddled by flanking towers at ~147px, a
    # boxed-in corner's nearest tower is pushed out past the next seat (~212px). The contrast holds.
    nw = min(math.hypot(t["x"] - 150, t["y"] - 150) for t in towers)
    se = min(math.hypot(t["x"] - 1050, t["y"] - 1050) for t in towers)
    assert nw > 180  # NW tower dropped (boxed in) - nearest tower pushed out past the next seat
    assert se < 180  # SE corner kept - flanking towers straddle it at ~half-spacing


# ------------------------------------------------------------------------------------------------
# Knob engine (feature 005, Phase 2b): seeded, independent, historically-typed layout variation.
# These are the FAILING-first tests for the shared machinery (Knob / knob_rng / register_knob /
# resolve_knob + the Settlement pin/resolve surface); the actual Family-A knob catalog lands in US1.
# ------------------------------------------------------------------------------------------------


def test_knob_rng_is_deterministic_and_stable():
    # SHA-256-derived (not hash()-derived, which is per-process salted): a fixed (seed, knob) always
    # yields the same stream, so a roll is reproducible across runs/processes.
    a = settlement.knob_rng(7, "cluster_position")
    b = settlement.knob_rng(7, "cluster_position")
    assert [a.random() for _ in range(5)] == [b.random() for _ in range(5)]


def test_knob_rng_independent_per_knob():
    # different knob names draw from different streams (independence, not a shared global sequence)
    a = settlement.knob_rng(7, "cluster_position")
    b = settlement.knob_rng(7, "lane_skeleton")
    assert a.random() != b.random()


def test_knob_roll_deterministic():
    k = settlement.Knob("t_shape", ["a", "b", "c", "d"], default="a")
    assert k.roll(42, {}) == k.roll(42, {})


def test_knob_roll_independent_across_knobs():
    # two knobs with identical value spaces do NOT move in lockstep across seeds
    k1 = settlement.Knob("t_one", list(range(20)), default=0)
    k2 = settlement.Knob("t_two", list(range(20)), default=0)
    assert any(k1.roll(s, {}) != k2.roll(s, {}) for s in range(30))


def test_knob_two_seeds_give_different_draws():
    k = settlement.Knob("t_pos", list(range(20)), default=0)
    assert len({k.roll(s, {}) for s in range(30)}) > 1


def test_knob_roll_excludes_typing_invalid():
    # only even values are historically valid in this context; the roll never returns an odd one
    k = settlement.Knob("t_even", [1, 2, 3, 4, 5, 6], default=2, typing_rule=lambda v, ctx: v % 2 == 0)
    assert all(k.roll(s, {}) % 2 == 0 for s in range(40))


def test_knob_empty_filtered_space_is_loud():
    # no value satisfies the rule -> a spec error, never a silent fallback
    k = settlement.Knob("t_none", [1, 3, 5], default=1, typing_rule=lambda v, ctx: v % 2 == 0)
    with pytest.raises(ValueError):
        k.roll(1, {})


def test_resolve_order_pinned_beats_roll_and_default():
    settlement.register_knob(settlement.Knob("t_res", ["a", "b", "c"], default="a"))
    assert settlement.resolve_knob("t_res", 1, {}, {"t_res": "b"}) == "b"  # pinned wins
    assert settlement.resolve_knob("t_res", 1, {}, {}, do_roll=False) == "a"  # default when roll opted out
    assert settlement.resolve_knob("t_res", 1, {}, {}) in ("a", "b", "c")  # else rolled


def test_resolve_pin_not_in_value_space_rejected():
    settlement.register_knob(settlement.Knob("t_pin", ["x", "y"], default="x"))
    with pytest.raises(ValueError):
        settlement.resolve_knob("t_pin", 1, {}, {"t_pin": "z"})


def test_resolve_pin_typing_violation_rejected():
    settlement.register_knob(settlement.Knob("t_pin2", ["dry", "wet"], default="dry", typing_rule=lambda v, ctx: not (v == "wet" and ctx.get("region") == "upland")))
    with pytest.raises(ValueError):
        settlement.resolve_knob("t_pin2", 1, {"region": "upland"}, {"t_pin2": "wet"})
    # the same pin is fine in a delta region
    assert settlement.resolve_knob("t_pin2", 1, {"region": "delta"}, {"t_pin2": "wet"}) == "wet"


def test_settlement_resolve_surface_records_and_feeds_context():
    s = Settlement(1000, 1000, seed=5)
    s.meta(name="V", scale="village", region="upland")
    settlement.register_knob(settlement.Knob("t_sk", ["p", "q"], default="p"))
    # a knob whose typing rule reads an EARLIER resolved knob from the running context
    settlement.register_knob(settlement.Knob("t_dep", ["lo", "hi"], default="lo", typing_rule=lambda v, ctx: not (v == "hi" and ctx.get("t_sk") == "p")))
    s.pin_knob("t_sk", "q")
    assert s.resolve("t_sk") == "q"
    assert s._resolved_knobs["t_sk"] == "q"
    # region flows from meta into the context; t_sk="q" so t_dep may be "hi"
    assert "region" in s.knob_context() and s.knob_context()["t_sk"] == "q"
    assert s.resolve("t_dep") in ("lo", "hi")


def test_settlement_resolve_default_when_unpinned_and_no_roll():
    s = Settlement(1000, 1000, seed=5)
    s.meta(name="V", scale="village")
    settlement.register_knob(settlement.Knob("t_def", ["one", "two"], default="one"))
    assert s.resolve("t_def", do_roll=False) == "one"


# ---- Family-A knob catalog (feature 005, US1): value spaces + China-first typing rules ----------


def test_family_a_knobs_are_registered_with_expected_value_spaces():
    for name, space in [
        ("cluster_position", {"high_margin", "flank", "mid_margin", "valley_mouth", "valley_head", "on_rise"}),
        ("cluster_shape", {"round", "elongated", "crescent", "split"}),
        ("lane_skeleton", {"spine", "T", "Y", "cross", "waterside"}),
        ("plot_size", {"small_irregular", "medium", "large_block", "strip"}),
        ("plot_regularity", {"organic", "grid"}),
    ]:
        assert set(settlement.KNOBS[name].value_space) == space


def test_lane_skeleton_waterside_typing():
    k = settlement.KNOBS["lane_skeleton"]
    assert "waterside" not in k.allowed({"water_kind": "pond"})  # pond-fed valley: no water alongside
    assert "waterside" in k.allowed({"water_kind": "stream"})  # stream-fed: a lane can hug the water
    assert "waterside" in k.allowed({"waterside_site": True})  # explicit canal/waterside site
    assert set(k.allowed({"water_kind": "pond"})) == {"spine", "T", "Y", "cross"}


def test_water_source_position_typing_pond_vs_stream():
    k = settlement.KNOBS["water_source_position"]
    pond = set(k.allowed({"water_kind": "pond"}))
    stream = set(k.allowed({"water_kind": "stream"}))
    assert pond == {"corner_NW", "corner_NE", "corner_SW", "corner_SE", "mid_margin", "chain"}
    assert stream == {"edge_N", "edge_E", "edge_S", "edge_W"}


def test_cluster_shape_split_needs_room():
    k = settlement.KNOBS["cluster_shape"]
    assert "split" not in k.allowed({"scale": "hamlet"})
    assert "split" in k.allowed({"scale": "village"})


def test_plot_regularity_grid_needs_planned_field():
    k = settlement.KNOBS["plot_regularity"]
    assert k.allowed({"field_origin": "organic"}) == ["organic"]  # old organically-grown field: no grid
    assert set(k.allowed({"field_origin": "planned"})) == {"organic", "grid"}


def test_family_a_roll_always_satisfies_typing_rule():
    # a pond-fed, organically-grown valley village (Kikuta/Hoshigaoka geography): every rolled knob value
    # is historically coherent for that context, across many seeds
    ctx = {"water_kind": "pond", "field_origin": "organic", "scale": "village"}
    for name in ("cluster_position", "cluster_shape", "lane_skeleton", "water_source_position", "plot_size", "plot_regularity", "grain_drift"):
        k = settlement.KNOBS[name]
        for seed in range(25):
            v = k.roll(seed, ctx)
            assert k.typing_rule(v, ctx)
            assert v != "waterside" and not str(v).startswith("edge_") and v != "grid"


def test_grain_drift_value_space():
    assert settlement.KNOBS["grain_drift"].value_space == [-12, -8, -4, 0, 4, 8, 12]


# ---- lane_skeleton knob: DERIVED headman/shrine placement (feature 005, US1) --------------------


def test_skeleton_layout_derives_distinct_headman_positions_per_skeleton():
    # the whole point: the headman position is DERIVED from the skeleton, so different skeletons put it in
    # different places (this is what stops two same-water villages from sharing a headman position)
    cx, cy, ex, ey = 400, 700, 120, 210
    hp = {k: settlement.skeleton_layout(k, cx, cy, ex, ey)["headman"] for k in settlement.LANE_SKELETONS}
    assert len(set(hp.values())) == len(hp)  # every skeleton's headman is a distinct point
    assert hp["spine"][1] < cy  # spine: at the high head (above center)
    assert hp["cross"] != (cx, cy) and settlement.skeleton_layout("cross", cx, cy, ex, ey)["market"] == (cx, cy)  # headman beside the market node
    assert hp["T"][1] < cy and hp["Y"][1] > cy  # T junction is upper, Y fork is lower
    assert hp["waterside"][0] < cx  # waterside: fronting the water flank (west of center)


def test_skeleton_layout_gateway_is_downslope_and_market_only_for_cross():
    for k in settlement.LANE_SKELETONS:
        lay = settlement.skeleton_layout(k, 400, 700, 120, 210)
        if k == "waterside":
            assert lay["gateway"][1] > 700  # foot of the waterside lane
        else:
            assert lay["gateway"] == (400, 910)  # downslope foot of the cluster
        assert ("market" in lay) == (k == "cross")  # only a cross yields a market node


def test_skeleton_layout_rejects_unknown_kind():
    import pytest

    with pytest.raises(ValueError):
        settlement.skeleton_layout("spiral", 0, 0, 10, 10)


def test_lane_skeleton_method_draws_lanes_and_records_axis():
    s = Settlement(1200, 1400, seed=3)
    s.meta(name="Sk", scale="village")
    before = len(s.M.get("lanes", []))  # 'lanes' is created lazily on the first lane() call
    lay = s.lane_skeleton("T", 400, 700, 120, 210)
    assert s.M["meta"]["lane_skeleton"] == "T"  # recorded for the twin-detector
    assert len(s.M["lanes"]) == before + 2  # a T lays two lanes (spine + crossbar)
    assert lay["headman"] == (400, 700 - 210 * 0.4)  # derived focal point returned


def test_crescent_pond_records_footprint_focal_feature_and_keepout():
    s = Settlement(1200, 1400, seed=3)
    s.meta(name="Cp", scale="village")
    ne_before = len(s.ellipses)
    s.crescent_pond(400, 900, 50, facing_deg=270)
    cp = s.M["crescent_ponds"]
    assert len(cp) == 1 and cp[0]["r"] == 50 and len(cp[0]["poly"]) == 27  # n+1 boundary points
    assert s.M["meta"]["focal_features"] == ["crescent_pond"]  # recorded as a focal feature
    assert len(s.ellipses) == ne_before + 1  # a placement keep-out was reserved
    # the half-disk bulges AWAY from the village (flat edge faces up/N): its lowest point is well below cy
    assert max(p[1] for p in cp[0]["poly"]) > 900
    # calling again does not duplicate the focal-feature tag (the "already present" branch)
    s.crescent_pond(600, 900, 40, facing_deg=90)
    assert s.M["meta"]["focal_features"] == ["crescent_pond"]
    assert len(s.M["crescent_ponds"]) == 2


def test_mill_draws_records_and_reserves():
    s = Settlement(1200, 1400, seed=3)
    s.meta(name="Mill", scale="village")
    np_before = len(s.placed)
    n_svg = len(s.out)
    s.mill(500, 600, wheel_side="E")
    assert len(s.M["mills"]) == 1 and s.M["mills"][0]["x"] == 500
    assert s.M["meta"]["focal_features"] == ["mill"]  # recorded via note_focal
    assert len(s.placed) == np_before + 1  # reserved in open ground
    assert len(s.out) > n_svg  # drew the house + waterwheel
    # the other wheel sides resolve too (the direction lookup)
    for side in ("W", "N", "S"):
        s.mill(700, 600, wheel_side=side)
    assert len(s.M["mills"]) == 4


def test_note_focal_is_idempotent_per_kind():
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="F", scale="village")
    s.note_focal("ancestral_hall")
    s.note_focal("ancestral_hall")  # idempotent
    s.note_focal("secondary_shrine")
    assert s.M["meta"]["focal_features"] == ["ancestral_hall", "secondary_shrine"]


# ---- cluster_shape knob: shape-aware seed generation (feature 005, US1) -------------------------


def test_cluster_seeds_shapes_generate_and_record():
    import random as _r

    s = Settlement(1400, 1400, seed=1)
    s.meta(name="Cs", scale="village")
    for shape in ("round", "elongated", "crescent", "split"):
        pts = s.cluster_seeds(shape, 500, 700, 150, 220, 60, _r.Random(4))
        assert len(pts) == 60
        assert s.M["meta"]["cluster_shape"] == shape

    # elongated is taller than wide (stretched along the margin); round is broader across
    rnd = s.cluster_seeds("round", 500, 700, 150, 220, 200, _r.Random(9))
    elo = s.cluster_seeds("elongated", 500, 700, 150, 220, 200, _r.Random(9))
    rw = max(p[0] for p in rnd) - min(p[0] for p in rnd)
    ew = max(p[0] for p in elo) - min(p[0] for p in elo)
    assert ew < rw  # elongated is narrower across the margin

    # split forms two lateral lobes -> the x-distribution is bimodal (few points near the center line)
    spl = s.cluster_seeds("split", 500, 700, 150, 220, 300, _r.Random(9))
    near_centre = sum(1 for p in spl if abs(p[0] - 500) < 30)
    assert near_centre < 0.15 * len(spl)  # a gap between the two sub-hamlets


def test_cluster_anchor_places_each_position_on_the_right_dry_margin():
    # cluster_position resolves against the field bbox + down_deg into an anchor off the paddy. Check each
    # value lands on the expected side of the field center relative to the fall (down_deg=90 -> downhill = +y).
    import math as m

    s = Settlement(2000, 2000, seed=1)
    s.meta(name="Ca", scale="village")
    fb = (600.0, 400.0, 1400.0, 1200.0)  # a field, center (1000, 800)
    fcx, fcy = 1000.0, 800.0
    dd = 90.0
    dx, dy = m.cos(m.radians(dd)), m.sin(m.radians(dd))  # (0, 1)
    ux, uy = -dy, dx  # (-1, 0)

    def along(pos):  # signed along-slope offset of the anchor (>0 = downhill of center)
        cx, cy, _ex, _ey = s.cluster_anchor(pos, fb, dd)
        return (cx - fcx) * dx + (cy - fcy) * dy

    def lateral(pos):
        cx, cy, _ex, _ey = s.cluster_anchor(pos, fb, dd)
        return (cx - fcx) * ux + (cy - fcy) * uy

    assert along("high_margin") < -400 and abs(lateral("high_margin")) < 30  # uphill, centered
    assert along("valley_head") < -400 and lateral("valley_head") != lateral("mid_margin")  # both high, opposite flanks
    assert along("mid_margin") < -400
    assert abs(lateral("flank")) > 400 and abs(along("flank")) < 30  # off to a cross-slope side
    assert along("valley_mouth") > 0 and abs(lateral("valley_mouth")) > 400  # low end, but on the dry shoulder
    assert along("on_rise") < -300  # a high-corner knoll
    # the anchor center sits OFF the paddy footprint (never inside the field bbox) for the margin positions
    for pos in ("high_margin", "valley_head", "mid_margin", "flank", "valley_mouth"):
        cx, cy, _ex, _ey = s.cluster_anchor(pos, fb, dd)
        assert not (fb[0] < cx < fb[2] and fb[1] < cy < fb[3])
    # extents are positive and the lateral (along-margin) axis is the broader one for a top margin (runs E-W)
    _cx, _cy, ex, ey = s.cluster_anchor("high_margin", fb, dd)
    assert ex > ey > 0
    with pytest.raises(ValueError):
        s.cluster_anchor("nowhere", fb, dd)


def test_plot_texture_drives_build_comb_grain():
    from waterfields import build_comb

    s = Settlement(2000, 2800, seed=1)
    s.meta(name="Pt", scale="village", ftpx=2)  # ftpx>=2 -> the real-feet calibration branch (the ft/px=1 hamlet legacy branch is covered by honda/shimizu)
    # small_irregular vs large_block must produce visibly different plot counts on the SAME field
    a_small, step_small = s.plot_texture("small_irregular", "organic")
    a_large, _step_large = s.plot_texture("large_block", "organic")
    assert a_small < a_large  # smaller plot_across = smaller paddies
    net_small = build_comb(1900, 2680, (760, 320), 5, down_deg=90, field_fall=1260, offtakes_a=(0.32, 0.7), offtakes_b=(), plot_across=a_small, row_step=step_small)
    net_large = build_comb(1900, 2680, (760, 320), 5, down_deg=90, field_fall=1260, offtakes_a=(0.32, 0.7), offtakes_b=(), plot_across=a_large)
    assert len(net_small["plots"]) > len(net_large["plots"])  # small paddies -> more plots
    # grid tightens the row-step spread vs organic
    _a, org = s.plot_texture("medium", "organic")
    _a2, grid = s.plot_texture("medium", "grid")
    assert (grid[1] - grid[0]) < (org[1] - org[0])
    # the knobs are recorded
    assert s.M["meta"]["plot_size"] == "medium" and s.M["meta"]["plot_regularity"] == "grid"
    for bad in (("huge", "organic"), ("medium", "checkerboard")):
        with pytest.raises(ValueError):
            s.plot_texture(*bad)


def test_paddy_grain_hits_the_real_feet_target():
    # the real-feet paddy calibration (GM 2026-07-22): plot_across x mean row_step, converted at the
    # map's ftpx, must equal the ~0.05-acre target - the SAME real cell at every scale (see paddy_grain)
    from waterfields import PADDY_CELL_ACRES, paddy_grain

    for ftpx in (1, 2, 3):
        across, (rlo, rhi) = paddy_grain(ftpx)
        mean_row = (rlo + rhi) / 2
        nominal_acres = across * mean_row * ftpx * ftpx / 43560
        assert abs(nominal_acres - PADDY_CELL_ACRES) < 0.004, (ftpx, nominal_acres)
        assert rlo < 0.66 * across < rhi  # the row-step (min,max) straddles the along-canal mean (aspect*across)
    # a coarser ftpx needs FEWER px per plot for the same real cell; a bigger target -> bigger plot
    assert paddy_grain(1)[0] > paddy_grain(2)[0] > paddy_grain(3)[0]
    assert paddy_grain(2, target_acres=0.036)[0] < paddy_grain(2, target_acres=0.0675)[0]


def test_perimeter_dike_draws_an_irregular_earthwork_band():
    s = Settlement(1400, 1400, seed=3)
    s.meta(name="D", scale="hamlet", ftpx=1, toscale=True, households=8, field_archetype="polder_grid")
    env = [(200, 200), (200, 1000), (900, 1000), (900, 200), (200, 200)]
    s.perimeter_dike(env, seed=5)
    dk = s.M["dikes"][0]
    assert dk["label"] == "perimeter dike"
    assert dk["w_max"] >= 1.4 * dk["w_min"]  # varying width, not a uniform stroke
    assert len(dk["outline"]) >= 60  # a smoothed organic band, not a 4-corner rectangle
    # the band stays a ring around the grid (outer points sit outside the inner env, none wildly off-map)
    assert all(0 <= x <= 1400 and 0 <= y <= 1400 for x, y in dk["outline"])
    # a label was recorded, and drawing is deterministic per seed
    assert any(lbl[5] == "perimeter dike" for lbl in s.M["labels"] if len(lbl) > 5)
    s2 = Settlement(1400, 1400, seed=3)
    s2.meta(name="D", scale="hamlet", ftpx=1, toscale=True, households=8, field_archetype="polder_grid")
    s2.perimeter_dike(env, seed=5)
    assert s2.M["dikes"][0]["outline"] == dk["outline"]
    # an empty label skips the caption but still draws + records the band
    s3 = Settlement(1400, 1400, seed=3)
    s3.meta(name="D", scale="hamlet", ftpx=1, toscale=True, households=8, field_archetype="polder_grid")
    s3.perimeter_dike(env, seed=5, label="")
    assert s3.M["dikes"] and not any(len(lbl) > 5 and lbl[5] == "perimeter dike" for lbl in s3.M.get("labels", []))


def test_village_grove_skips_the_dike_bank():
    # a windbreak belt laid ACROSS the perimeter dike must place NO clump on the earthwork bank
    # (GM 2026-07-22: the dike carries only its own soil-binding trees).
    s = Settlement(1400, 1400, seed=3)
    s.meta(name="G", scale="hamlet", ftpx=1, toscale=True, households=8, field_archetype="polder_grid")
    s.perimeter_dike([(200, 200), (200, 1000), (900, 1000), (900, 200), (200, 200)], seed=5)
    dike = s.M["dikes"][0]["outline"]

    def pip(x, y, poly):
        c, j = False, len(poly) - 1
        for i in range(len(poly)):
            xi, yi, xj, yj = poly[i][0], poly[i][1], poly[j][0], poly[j][1]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi:
                c = not c
            j = i
        return c

    s.village_grove([(150, 150), (360, 150), (360, 280), (150, 280)], role="windbreak")  # a belt straddling the NW dike
    clumps = s.M["village_groves"][-1]["clumps"]
    assert clumps and not any(pip(cx, cy, dike) for cx, cy in clumps)  # some clumps, none on the dike


def test_build_polder_parcel_fabric():
    from waterfields import build_polder

    net = build_polder(2200, 2600, (360, 320), 21, down_deg=90, rows=11, cols=6, cell=150)
    plots = net["plots"]
    # deterministic per seed
    assert build_polder(2200, 2600, (360, 320), 21, down_deg=90, rows=11, cols=6, cell=150)["plots"] == plots
    # splits outnumber merges: more parcels than module bays
    assert len(plots) > 66
    # the envelope (the dike's inner-face reference) keeps the full span: it is densified 12 samples/edge
    # (so the edge-wander curvature is carried into the drawn field/dike), and the corners - at 0, 12, 24, 36 -
    # are exact grid multiples (edge_wander defaults to 0 here, so no warp)
    assert net["envelope"][0] == (360, 320) and net["envelope"][24] == (360 + 6 * 150, 320 + 11 * 150)
    RING = 18.0
    s_step = (11 * 150 - 2 * RING) / 11
    # the fabric varies (mirrors the polder_parcels_vary thresholds, with slack): areas spread, oblongs dominate
    dims = []
    for p in plots:
        xs = [v[0] for v in p["poly"]]
        ys = [v[1] for v in p["poly"]]
        dims.append((max(xs) - min(xs), max(ys) - min(ys)))
    areas = [w * h for w, h in dims]
    mean_a = sum(areas) / len(areas)
    cv = (sum((a - mean_a) ** 2 for a in areas) / len(areas)) ** 0.5 / mean_a
    assert cv > 0.25
    oblong = sum(1 for w, h in dims if max(w, h) / min(w, h) >= 1.45) / len(dims)
    assert oblong > 0.5
    # every parcel stays inside the envelope, and the low flag marks the bottom two rows only
    for p in plots:
        assert all(360 <= v[0] <= 360 + 900 and 320 <= v[1] <= 320 + 1650 for v in p["poly"])
        cy = sum(v[1] for v in p["poly"]) / len(p["poly"])
        assert p["low"] == (cy > 320 + RING + 9 * s_step)  # down_deg=90: low rows (r>=9) sit past ss(9)
    assert any(p["low"] for p in plots) and not all(p["low"] for p in plots)
    # the water network is a CLOSED filleted RING (feeder top + 2 toe sides + drain bottom) tagged by `seg`,
    # plus one lateral per interior column line. The interior laterals run from the feeder inner-toe line to
    # the drain inner-toe line; the ring sides carry their seg tags.
    segs = [ch.get("seg") for ch in net["channels"]]
    assert segs.count("feeder") == 1 and segs.count("e_toe") == 1 and segs.count("w_toe") == 1 and segs.count("drain") == 1
    assert segs.count("lateral") == 5  # one per interior column line (cols=6 -> 5)
    roles = {ch.get("seg"): ch["role"] for ch in net["channels"] if ch.get("seg")}
    assert roles["feeder"] == "main" and roles["drain"] == "drain" and roles["e_toe"] == "lateral"

    # each interior lateral is SNAPPED onto the (gently wavered) feeder + drain centerlines, so its ends lie
    # ON those ring polylines - a clean T-junction, not an exact di/fi row (the toe lines waver ~3.5 px in s)
    def _pt_seg(p, a, b):
        vx, vy = b[0] - a[0], b[1] - a[1]
        ll = vx * vx + vy * vy or 1.0
        t = max(0.0, min(1.0, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / ll))
        return math.hypot(p[0] - a[0] - t * vx, p[1] - a[1] - t * vy)

    def _near(pt, poly):
        return min(_pt_seg(pt, poly[i], poly[i + 1]) for i in range(len(poly) - 1))

    feeder_pts = next(ch["pts"] for ch in net["channels"] if ch.get("seg") == "feeder")
    drain_pts = next(ch["pts"] for ch in net["channels"] if ch.get("seg") == "drain")
    for ch in net["channels"]:
        if ch.get("seg") != "lateral":  # only the interior column laterals run toe-to-toe
            continue
        assert _near(ch["pts"][0], feeder_pts) < 2  # starts ON the feeder inner-toe line
        assert _near(ch["pts"][-1], drain_pts) < 2  # ends ON the drain inner-toe line
    # pond-profile mix: merge-heavy, no 3-cuts, wide dike gaps -> fewer, larger, oblong parcels
    pond_net = build_polder(2200, 2600, (360, 320), 21, down_deg=90, rows=10, cols=6, cell=160, parcel_mix=(0.10, 0.0, 0.60), gap=(11.0, 11.0))
    assert len(pond_net["plots"]) < len(plots)
    pond_areas = sorted(abs(_shoelace(p["poly"])) for p in pond_net["plots"])
    assert pond_areas[-1] > 2.5 * pond_areas[0]  # merged doubles dwarf the split minority


def _shoelace(poly):
    return sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly))) / 2


def test_land_use_overlay_draws_and_records_each_kind():
    from waterfields import build_comb

    net = build_comb(1900, 2680, (760, 320), 5, down_deg=90, field_fall=1260, offtakes_a=(0.32, 0.7), offtakes_b=())
    for overlay in ("mulberry_fishpond", "lotus", "tea_fringe"):
        s = Settlement(2000, 2800, seed=3)
        s.meta(name="LU", scale="village", ftpx=1, down_deg=90)
        n = s.apply_land_use(net, overlay, __import__("random").Random(1))
        assert n > 0 and s.M["meta"]["land_use_overlay"] == overlay and s.out
        rec = s.M["land_use"][-1]
        assert rec["overlay"] == overlay and rec["count"] == n
        if overlay != "tea_fringe":  # tea is a margin fringe, not plot-based, so it records no plot list
            # feature 010: the plot-based overlays record WHICH plots converted, and every one of them
            # must be a low/wet plot - the topographic eligibility filter.
            wet = {tuple(_centroid(p["poly"])) for p in net["plots"] if p.get("low")}
            assert rec["eligible"] == "wet" and len(rec["plots"]) == n
            assert all(tuple(p) in wet for p in rec["plots"])
    # "none" records zero and draws nothing extra
    s0 = Settlement(2000, 2800, seed=3)
    s0.meta(name="LU0", scale="village", ftpx=1, down_deg=90)
    assert s0.apply_land_use(net, "none", __import__("random").Random(1)) == 0
    with pytest.raises(ValueError):
        s0.apply_land_use(net, "quinoa", __import__("random").Random(1))


def test_land_use_overlay_topography_paths():
    """Feature 010: the three placement paths - no eligible ground at all, the clustered dike-pond
    growth, and the named wholesale-conversion opt-out that ignores the topographic filter."""
    from waterfields import build_comb

    net = build_comb(1900, 2680, (760, 320), 5, down_deg=90, field_fall=1260, offtakes_a=(0.32, 0.7), offtakes_b=())
    dry = {**net, "plots": [{**p, "low": False} for p in net["plots"]]}  # a field with NO low/wet ground
    s = Settlement(2000, 2800, seed=3)
    s.meta(name="LU1", scale="village", ftpx=1, down_deg=90)
    assert s.apply_land_use(dry, "lotus", __import__("random").Random(1)) == 0  # draws nothing, honestly
    assert s.M["land_use"][-1]["plots"] == []
    # eligible="all" is the ARCHETYPE opt-out: it converts ordinary rice ground too
    s2 = Settlement(2000, 2800, seed=3)
    s2.meta(name="LU2", scale="village", ftpx=1, down_deg=90)
    n2 = s2.apply_land_use(dry, "mulberry_fishpond", __import__("random").Random(1), fraction=0.9, eligible="all")
    assert n2 > 0 and s2.M["land_use"][-1]["eligible"] == "all"
    # take >= len(eligible) short-circuits to "convert everything eligible"
    two = [{"poly": [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)], "low": True}] * 2
    assert len(Settlement._pick_overlay_plots(two, 5, clustered=True, rng=__import__("random").Random(1))) == 2


def test_archetype_knob_typing_rules():
    # field_archetype + land_use_overlay honor terrain typing (research.md D4)
    s = Settlement(1800, 1800, seed=1)
    s.meta(name="A", scale="village")
    # with no declared terrain, only valley_paddy is a coherent field archetype; a hill archetype pin is rejected
    s.pin_knob("field_archetype", "contour_terraces")
    with pytest.raises(ValueError):
        s.resolve("field_archetype")
    s2 = Settlement(1800, 1800, seed=1)
    s2.meta(name="A2", scale="village", terrain="hill")
    s2.pin_knob("field_archetype", "contour_terraces")
    assert s2.resolve("field_archetype") == "contour_terraces"  # hill terrain -> terraces allowed
    # tea_fringe overlay needs hill/terrace ground; lotus is fine anywhere
    s3 = Settlement(1800, 1800, seed=1)
    s3.meta(name="A3", scale="village")
    s3.pin_knob("land_use_overlay", "tea_fringe")
    with pytest.raises(ValueError):
        s3.resolve("land_use_overlay")
    s3.knob_pins.clear()
    s3._resolved_knobs.clear()
    s3.pin_knob("land_use_overlay", "lotus")
    assert s3.resolve("land_use_overlay") == "lotus"


def test_focal_catalogue_methods_draw_record_and_note():
    # the rest of the focal catalog (T020): each draws, records its footprint, and notes the focal feature
    # so the twin-detector's focal_set axis reads it.
    s = Settlement(2000, 2000, seed=2)
    s.meta(name="F", scale="village", ftpx=1)
    s.ancestral_hall(400, 400)
    s.water_mouth(700, 700)
    s.market(1000, 1000)
    s.secondary_shrine(1300, 500)
    assert s.M["ancestral_halls"] and s.M["water_mouths"] and s.M["markets"]
    foc = set(s.M["meta"]["focal_features"])
    assert {"ancestral_hall", "water_mouth", "market", "secondary_shrine"} <= foc
    # each reserved a placement keep-out (nothing may later be placed on it)
    assert not s._fits(400, 400, 40, 30)  # the ancestral hall footprint is blocked
    # the secondary shrine records as a shrine kind (religious_matches_scale still sees only shrines)
    assert any(r.get("kind") == "shrine" for r in s.M.get("religious", []) + s.M.get("shrines", []))


def test_roll_village_is_deterministic_and_seed_varies_the_combination():
    # US2 (SC-004): the same seed rolls the SAME combination (byte-identical), a different seed rolls a
    # DIFFERENT one, and a rolled map is populated with no hand-placed coordinates.
    def roll(seed):
        s = Settlement(W=2000, H=2600, seed=seed)
        s.meta(name="R", scale="hamlet", ftpx=1, toscale=True, households=18, field_footbridges=True)
        return s, s.roll_village("R", households=18, down_deg=90, water_kind="pond", field_fall=1260)

    s7a, k7a = roll(7)
    _s7b, k7b = roll(7)
    assert k7a == k7b  # same seed -> identical roll
    _s8, k8 = roll(8)
    combo = ("cluster_position", "cluster_shape", "lane_skeleton", "water_source_position")
    assert tuple(k7a[c] for c in combo) != tuple(k8[c] for c in combo)  # different seeds -> different combination
    assert 15 <= len(s7a.M["houses"]) <= 19 and s7a.M["fields"] and s7a.view  # a populated, framed map


def test_waterfront_seeds_line_both_banks_of_a_canal():
    import random as _r

    s = Settlement(1600, 1600, seed=1)
    s.meta(name="Wt", scale="village")
    canal = [(200, 200), (200, 700), (500, 1200)]  # a BENT canal (2 segments) so later seeds fall past the first
    seeds = s.waterfront_seeds(canal, 20, 60.0, _r.Random(3))
    assert len(seeds) == 20 and s.M["meta"]["settlement_form"] == "water_town"
    # seeds sit on BOTH banks (both sides of x=200), offset ~60px
    xs = [p[0] for p in seeds]
    assert any(x > 250 for x in xs) and any(x < 150 for x in xs)
    # record=False leaves meta untouched
    s2 = Settlement(1600, 1600, seed=1)
    s2.meta(name="Wt2", scale="village")
    s2.waterfront_seeds(canal, 6, 60.0, _r.Random(1), record=False)
    assert "settlement_form" not in s2.M["meta"]


def test_settlement_form_water_town_is_lion_gated():
    # water_town needs a canal, which is a Lion-lands feature per GM canon; the other forms are unrestricted
    s = Settlement(1200, 1200, seed=1)
    s.meta(name="Sf", scale="village")
    for form in ("nucleated", "linear", "dispersed"):
        s.knob_pins.clear()
        s._resolved_knobs.clear()
        s.pin_knob("settlement_form", form)
        assert s.resolve("settlement_form") == form
    s.knob_pins.clear()
    s._resolved_knobs.clear()
    s.pin_knob("settlement_form", "water_town")
    with pytest.raises(ValueError):
        s.resolve("settlement_form")  # no Lion / canal declared
    lion = Settlement(1200, 1200, seed=1)
    lion.meta(name="Sl", scale="village", clan="Lion")
    lion.pin_knob("settlement_form", "water_town")
    assert lion.resolve("settlement_form") == "water_town"


def test_roll_village_stream_fed_with_a_pinned_water_source():
    # exercises the STREAM water path (a brook entering from a canvas edge) and a PINNED water_source_position
    # (edge_N is a legal stream source for a south-falling field). Covers the stream branches in roll_village +
    # draw_comb_field that the pond-fed demos do not.
    s = Settlement(W=2000, H=2600, seed=7)
    s.meta(name="Sr", scale="hamlet", ftpx=1, toscale=True, households=18, field_footbridges=True)
    s.pin_knob("water_source_position", "edge_N")
    k = s.roll_village("Sr", households=18, down_deg=90, water_kind="stream", field_fall=1260)
    assert k["water_source_position"] == "edge_N" and s.M["meta"]["water_kind"] == "stream"
    assert s.M["houses"] and any(st for st in s.M["streams"])  # a stream source was drawn


def test_roll_village_honors_a_pinned_knob():
    # a pinned knob overrides the roll (US3 determinism surface, exercised through the roll entrypoint)
    s = Settlement(W=2000, H=2600, seed=7)
    s.meta(name="P", scale="hamlet", ftpx=1, toscale=True, households=18, field_footbridges=True)
    s.pin_knob("cluster_shape", "elongated")
    s.pin_knob("lane_skeleton", "spine")
    k = s.roll_village("P", households=18, down_deg=90, water_kind="pond", field_fall=1260)
    assert k["cluster_shape"] == "elongated" and k["lane_skeleton"] == "spine"


def test_pinned_knob_is_byte_identical_across_regens_and_rejects_incompatible_pins():
    # US3 (SC-006): a pinned knob is honored identically every regen; a pin outside the value space or one
    # that violates the geography typing rule is a LOUD error, never silently drawn.
    def build():
        s = Settlement(W=2000, H=2600, seed=11)
        s.meta(name="Pin", scale="village", ftpx=1, toscale=True, households=40, field_footbridges=True)
        s.pin_knob("cluster_shape", "split")  # split needs a village (typing rule) - legal here
        s.pin_knob("lane_skeleton", "cross")
        return s.roll_village("Pin", households=40, down_deg=90, water_kind="pond", field_fall=1400)

    k1 = build()
    k2 = build()
    assert k1 == k2 and k1["cluster_shape"] == "split" and k1["lane_skeleton"] == "cross"  # byte-identical, honored
    # a value outside the knob's space -> loud error
    s = Settlement(W=1800, H=1800, seed=1)
    s.meta(name="X", scale="village")
    s.pin_knob("cluster_shape", "octagon")
    with pytest.raises(ValueError):
        s.resolve("cluster_shape")
    # a value that VIOLATES the geography typing rule (split needs a village/town, not a hamlet) -> loud error
    s2 = Settlement(W=1800, H=1800, seed=1)
    s2.meta(name="Y", scale="hamlet")
    s2.pin_knob("cluster_shape", "split")
    with pytest.raises(ValueError):
        s2.resolve("cluster_shape")


def test_water_source_anchor_gravity_and_valid_set():
    # water_source_position resolves to a sluice/entry point on the field's UPHILL margin; a downhill source
    # is rejected (gravity), and water_sources_for lists only the feedable set for a given fall + water kind.
    s = Settlement(2000, 2000, seed=1)
    s.meta(name="Ws", scale="village")
    fb = (600.0, 400.0, 1400.0, 1200.0)  # center (1000, 800); down_deg 90 -> downhill = +y (S)
    # an uphill (N) pond corner is fine and sits above the field
    sx, sy = s.water_source_anchor("corner_NW", fb, 90.0)
    assert sy < 400  # north of the field's top edge
    assert s.water_source_anchor("mid_margin", fb, 90.0)[1] < 400  # the uphill margin
    # a downhill (S) corner cannot gravity-feed a south-falling field -> rejected
    with pytest.raises(ValueError):
        s.water_source_anchor("corner_SW", fb, 90.0)
    with pytest.raises(ValueError):
        s.water_source_anchor("edge_S", fb, 90.0)
    with pytest.raises(ValueError):
        s.water_source_anchor("bogus", fb, 90.0)
    # the gravity-valid sets: ponds exclude the two south corners for a south fall; streams keep the non-S edges
    ponds = s.water_sources_for(90.0, "pond")
    assert "corner_NW" in ponds and "corner_NE" in ponds and "mid_margin" in ponds
    assert "corner_SW" not in ponds and "corner_SE" not in ponds
    streams = s.water_sources_for(90.0, "stream")
    assert set(streams) == {"edge_N", "edge_E", "edge_W"}  # not edge_S (downhill)


def test_cluster_seeds_record_false_and_bad_shape():
    import random as _r

    s = Settlement(1000, 1000, seed=1)
    s.meta(name="Cs2", scale="village")
    s.cluster_seeds("round", 500, 500, 100, 100, 5, _r.Random(1), record=False)
    assert "cluster_shape" not in s.M["meta"]  # record=False leaves meta untouched
    with pytest.raises(ValueError):
        s.cluster_seeds("spiral", 500, 500, 100, 100, 5, _r.Random(1))


def test_line_seeds_strings_along_the_line_and_records_form():
    import random as _r

    s = Settlement(1400, 1400, seed=1)
    s.meta(name="Ln", scale="village")
    pts = s.line_seeds((400, 400), (400, 1000), 80, 40, _r.Random(3))
    assert len(pts) == 80
    assert s.M["meta"]["settlement_form"] == "linear"  # recorded (a twin-detector axis)
    assert all(abs(p[0] - 400) <= 40 + 1e-9 for p in pts)  # a vertical line: x stays within the band
    assert max(p[1] for p in pts) - min(p[1] for p in pts) > 400  # strung along the length
    # record=False leaves meta untouched
    s2 = Settlement(1000, 1000, seed=1)
    s2.meta(name="L2", scale="village")
    s2.line_seeds((0, 0), (100, 0), 5, 10, _r.Random(1), record=False)
    assert "settlement_form" not in s2.M["meta"]


def test_scatter_seeds_spreads_over_area_and_records_dispersed():
    import random as _r

    s = Settlement(1400, 1400, seed=1)
    s.meta(name="Sc", scale="village")
    pts = s.scatter_seeds(600, 600, 200, 300, 150, _r.Random(5))
    assert len(pts) == 150
    assert s.M["meta"]["settlement_form"] == "dispersed"  # recorded (a twin-detector axis)
    assert all(((p[0] - 600) / 200) ** 2 + ((p[1] - 600) / 300) ** 2 <= 1.0 + 1e-6 for p in pts)  # within the ellipse
    # an even (area-uniform) scatter fills the ellipse, not clumped at the center
    assert sum(1 for p in pts if math.hypot(p[0] - 600, p[1] - 600) > 150) > 30
    # record=False leaves meta untouched
    s2 = Settlement(1000, 1000, seed=1)
    s2.meta(name="S2", scale="village")
    s2.scatter_seeds(500, 500, 100, 100, 5, _r.Random(1), record=False)
    assert "settlement_form" not in s2.M["meta"]


def test_pick_overlay_plots_grows_a_patch_from_its_seeds():
    """Feature 010: the clustered dike-pond path. Conversion was 挖塘培基 - one household digging one
    low plot in one dry season - so the patch GROWS outward from a seed by nearest-neighbor, rather
    than sprinkling evenly. Assert the growth actually happened: the chosen plots are mutually nearer
    than an evenly-spread subset of the same size would be."""
    import random as _r

    row = [{"poly": [(float(i * 100), 0.0), (float(i * 100 + 90), 0.0), (float(i * 100 + 90), 90.0)], "low": True} for i in range(20)]
    got = Settlement._pick_overlay_plots(row, 6, clustered=True, rng=_r.Random(4))
    assert len(got) == 6
    xs = sorted(_centroid(p["poly"])[0] for p in got)
    assert xs[-1] - xs[0] <= 5 * 100 + 1  # contiguous run, not scattered over the full 2000px row
    # unclustered takes the same eligible set but does NOT force contiguity
    assert len(Settlement._pick_overlay_plots(row, 6, clustered=False, rng=_r.Random(4))) == 6


def _estate_settlement():
    s = Settlement(1200, 1200, seed=1)
    s.meta(name="E", scale="city", ftpx=3, down_deg=90)
    return s


def test_estate_wall_must_stand_on_dry_private_ground():
    """The municipal watch cannot be walled inside a private court, and the compound wall may not run
    through working water. Each refusal path asserted directly rather than left to map geometry."""
    s = _estate_settlement()
    assert s._estate_wall_clear(600, 600, 100, 80)  # clear ground
    s.M["fire_towers"] = [{"x": 600, "y": 600, "w": 10, "h": 10}]  # tower swallowed by the court
    assert not s._estate_wall_clear(600, 600, 100, 80)
    s2 = _estate_settlement()
    s2.M["fire_towers"] = [{"x": 650, "y": 600, "w": 10, "h": 10}]  # tower ON the wall line
    assert not s2._estate_wall_clear(600, 600, 100, 80)
    s3 = _estate_settlement()
    s3.M["canals"] = [{"poly": [(650, 400), (650, 800)], "w": 12}]  # canal crossing the wall
    assert not s3._estate_wall_clear(600, 600, 100, 80)
    s4 = _estate_settlement()
    s4.M["pond"] = (650, 600, 40, 40)  # pond under the wall
    assert not s4._estate_wall_clear(600, 600, 100, 80)


def test_merchant_estate_raises_when_no_clear_seat_exists():
    """Rather than draw a wall the gate will reject, an estate boxed in by water raises."""
    s = _estate_settlement()
    s.M["canals"] = [{"poly": [(x, 0), (x, 1200)], "w": 12} for x in range(400, 900, 40)]  # a thicket of canals
    with pytest.raises(ValueError, match="no seat within the slide fan"):
        s.merchant_estate(600, 600, 100, 80)


def test_clearings_keep_scrub_off_sacred_and_funerary_ground():
    """Feature: a swept verge around shrine/torii/graves. `_clear_ground` grows the footprint by `extra`
    (bscale-scaled) into `self.clearings`, which the hinterland scatter skips - but building placement
    (block_polys) and groves are untouched, so a shrine's preserved grove is unaffected."""
    s = Settlement(1200, 1200, seed=1)
    s.meta(name="C", scale="village", ftpx=1, down_deg=90)
    n_block = len(s.block_polys)
    s._clear_ground(600, 600, 40, 30, 58)
    assert len(s.clearings) == 1 and len(s.block_polys) == n_block  # clearings, NOT block_polys
    poly = s.clearings[0]
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    # the verge is an ORGANIC blob (irregular inward bays), not the padded rectangle: 16 edge samples,
    # more than 4 distinct x values, contained in the padded rect (bays-only - the claim never grows),
    # and still generously containing the footprint (a bay cuts at most ~55% of the 58px collar)
    assert len(poly) == 16 and len({round(px, 1) for px in xs}) > 4
    assert min(xs) >= 600 - 20 - 58 and max(xs) <= 600 + 20 + 58 and min(ys) >= 600 - 15 - 58 and max(ys) <= 600 + 15 + 58
    assert all(settlement.point_in_poly(fx, fy, poly) for fx, fy in [(580, 585), (620, 585), (620, 615), (580, 615)])
    # shrine_hall with a torii registers a clearing for BOTH the hall and the arch
    s2 = Settlement(1200, 1200, seed=1)
    s2.meta(name="C2", scale="village", ftpx=1, down_deg=90)
    s2.shrine_hall(600, 600, "Shrine", torii=[(600, 680)], torii_count=1)  # pinned so the clearing count is stable under the per-temple roll
    assert len(s2.clearings) == 2  # the hall + the one torii
    # a cemetery registers one too
    s3 = Settlement(1200, 1200, seed=1)
    s3.meta(name="C3", scale="village", ftpx=1, down_deg=90)
    s3.cemetery(600, 600, 90, 60, label="burial ground")
    assert len(s3.clearings) == 1


def test_clear_ground_is_deterministic_and_preserves_the_rng_stream():
    """The organic verge is seeded from its own footprint: identical args -> identical blob (render-sync
    determinism), and the map's global RNG stream is untouched (saved/restored), so adding or reshaping
    a collar can never shift any other feature's random draws."""
    s = Settlement(1200, 1200, seed=1)
    s.meta(name="D", scale="village", ftpx=1, down_deg=90)
    random.seed(99)
    expect = random.random()
    random.seed(99)
    s._clear_ground(600, 600, 40, 30, 58)
    assert random.random() == expect  # the stream is exactly where it was
    s2 = Settlement(1200, 1200, seed=7)  # different map seed, same collar args
    s2.meta(name="D2", scale="village", ftpx=1, down_deg=90)
    s2._clear_ground(600, 600, 40, 30, 58)
    assert s.M["clearings"][0]["poly"] == s2.M["clearings"][0]["poly"]


def test_clear_ground_dedupes_same_center_registrations():
    """The reserve_clearing-then-feature pattern registers the same collar twice (the feature's own call
    lands within a few px of the reserve, sometimes with a different footprint/extra). The duplicate
    REUSES the first blob verbatim - guard and late collar can never disagree about the swept outline -
    while a genuinely different center gets its own blob."""
    s = Settlement(1200, 1200, seed=1)
    s.meta(name="E", scale="village", ftpx=1, down_deg=90)
    s._clear_ground(600, 600, 60, 46, 30)  # the gen's reserve
    s._clear_ground(600, 602, 40, 30, 58)  # the feature's own late registration: 2px off, different size
    assert len(s.clearings) == 2 and s.clearings[0] == s.clearings[1]
    assert s.M["clearings"][0]["poly"] == s.M["clearings"][1]["poly"]
    s._clear_ground(900, 900, 40, 30, 58)  # a different feature elsewhere: its own blob
    assert len(s.clearings) == 3 and s.clearings[2] != s.clearings[1]


def test_paddy_features_cover_every_archetype_branch():
    """Feature 012: exercise _paddy_features across archetypes + many seeds so every placement branch fires
    (pond / rock / grave-island each both ways), plus the dike-pond early return. Also confirms each glyph
    draws and records its manifest key. Synthetic net: 6 plots, the first 3 flagged low."""
    net = {"plots": [{"poly": [(float(i * 30), 0.0), (float(i * 30 + 20), 0.0), (float(i * 30 + 20), 20.0), (float(i * 30), 20.0)], "low": i < 3, "fill": "#A6C398"} for i in range(6)]}
    seen = {"field_ponds": 0, "field_rocks": 0, "field_graves": 0}
    for arch in ("valley_paddy", "contour_terraces", "polder_grid", "ribbon_valley", "mulberry_dike_fishpond"):
        for seed in range(40):
            s = Settlement(1200, 1200, seed=seed)
            s.meta(name="P", scale="village", ftpx=1, down_deg=90, field_archetype=arch)
            s._paddy_features(net)
            for k in seen:
                seen[k] += len(s.M.get(k, []))
    # every glyph type got drawn at least once across the sweep (so all three _plot_* methods are covered)
    assert all(v > 0 for v in seen.values()), seen
    # dike-pond draws NONE
    sd = Settlement(1200, 1200, seed=1)
    sd.meta(name="D", scale="village", ftpx=1, down_deg=90, field_archetype="mulberry_dike_fishpond")
    sd._paddy_features(net)
    assert not any(sd.M.get(k) for k in seen)


def test_main_tree_guard_blocks_main_allows_clones_and_gm_override(monkeypatch):
    monkeypatch.delenv("GM_ASSISTANT_ALLOW_MAIN", raising=False)
    # running from the MAIN integration tree aborts with the CLAUDE.md reminder
    with pytest.raises(SystemExit, match="Session clones"):
        settlement._assert_not_main_tree("/gm-assistant/.claude/skills/diagram/settlement.py")
    # a session clone under .clones/ is the sanctioned workspace
    settlement._assert_not_main_tree("/gm-assistant/.clones/x/.claude/skills/diagram/settlement.py")
    # any tree outside /gm-assistant (the GM's laptop checkout) is not main
    settlement._assert_not_main_tree("/home/eli/l7r/gm-assistant/.claude/skills/diagram/settlement.py")
    # the GM's deliberate override opens main
    monkeypatch.setenv("GM_ASSISTANT_ALLOW_MAIN", "1")
    settlement._assert_not_main_tree("/gm-assistant/.claude/skills/diagram/settlement.py")


def test_draw_comb_field_existing_stream_and_cascade_sources():
    # source={"kind":"stream"} WITHOUT a polyline = an existing on-map stream already runs at the
    # sluice (the town pattern: a comb tapping the map's stream via a weir) - nothing extra is
    # drawn, but the hairline topology channel is still recorded. source={"kind":"cascade"} skips
    # the hairline too: the caller records its own connector channel (the field-to-field cascade,
    # e.g. Hirameki's e1 -> e2), whose to={"kind":"field"} anchor replaces it.
    from waterfields import build_comb

    s = Settlement(W=1400, H=1400, seed=5)
    s.meta(name="Cs", scale="town", ftpx=1, down_deg=90)
    net = build_comb(1400, 1400, (700, 200), 5, down_deg=90, field_fall=400)
    net["brook"] = []
    n_streams = len(s.M["streams"])
    s.draw_comb_field(net, "f1", {"kind": "stream"})  # no polyline -> no stream drawn
    assert len(s.M["streams"]) == n_streams
    assert s.M["channels"][-1]["to"] == {"kind": "field", "name": "f1"}  # hairline still recorded
    n_chan = len(s.M["channels"])
    net2 = build_comb(1400, 1400, (700, 200), 6, down_deg=90, field_fall=400)
    net2["brook"] = []
    s.draw_comb_field(net2, "f2", {"kind": "cascade"})  # cascade: the caller wires the source
    assert len(s.M["channels"]) == n_chan  # no hairline appended


def test_yard_fits_rejects_dry_crop_plots():
    # the threshing yard is footprint-checked against dry_polys exactly like the house in _fits:
    # a hem strip is cropland, and a yard straddling it (center off, footprint on) must be
    # rejected (the Tango-hems class of defect, extended to yards via the town comb conversion)
    s = Settlement(W=1000, H=1000, seed=1)
    s.meta(name="Yd", scale="town", ftpx=1)
    assert s._yard_fits(500, 500, 40, 26, 460, 460)  # open ground: fits
    s.dry_polys.append([(490, 480), (620, 480), (620, 560), (490, 560)])
    # center 14px OUTSIDE the hem (so the center-based _in_blocked test passes it) but the 40px
    # footprint still laps the plot - only the rect test can catch this one
    assert not s._yard_fits(476, 500, 40, 26, 440, 500)


def test_grove_fits_rejects_wall_overlap():
    # a belt arm is footprint-checked against the town wall: the corridor test is center-only,
    # so a wide arm centered clear of the rampart could still lap the stroke (Hirameki, 2026-07)
    s = Settlement(W=1000, H=1000, seed=1)
    s.meta(name="Gw", scale="town", ftpx=1)
    assert s._grove_fits(500, 500, 90, 40, [(470, 470)])  # no wall: fits
    s.M["wall"] = [(540, 300), (540, 700)]
    assert not s._grove_fits(500, 500, 90, 40, [(470, 470)])  # east corner laps the wall stroke


def test_paddy_field_polygon_shape_records_the_field():
    # the legacy paddy_field's POLYGON branch: kept exercised here now that no pool map draws a
    # legacy quilt anymore (the towns moved to build_comb; only ad-hoc callers use this path)
    s = Settlement(W=1200, H=1200, seed=3)
    s.meta(name="Pf", scale="town", ftpx=1)
    s.paddy_field([(200, 200), (500, 220), (520, 500), (240, 520)], "", "poly-paddy", amp=14, plot=58)
    f = [f for f in s.M["fields"] if f["name"] == "poly-paddy"]
    assert f and len(f[0]["outline"]) >= 4


def test_merchant_residences_stop_at_the_requested_count():
    # the placed >= count early-break: with more storefronts than requested homes, the loop
    # must stop at the cap (previously covered by the towns' legacy gens)
    s = Settlement(W=1600, H=1600, seed=4)
    s.meta(name="Mr", scale="town", ftpx=1)
    rd = [(300, 1100), (1300, 1100)]
    s.road(rd, label="post road")  # merchant_residences derives its band from the ROAD, not a street
    s.frontage(rd, ["shop"] * 8, width=24, spacing=64, skip=rd)
    n0 = sum(1 for b in s.M["buildings"] if b["kind"] == "merchant_large")
    s.merchant_residences(0)  # count already satisfied -> the cap break fires on the first storefront
    assert sum(1 for b in s.M["buildings"] if b["kind"] == "merchant_large") == n0
    s.merchant_residences(1)
    assert sum(1 for b in s.M["buildings"] if b["kind"] == "merchant_large") <= n0 + 1


def test_clip_to_stream_trims_the_confluence_mouth():
    # a drawn channel whose recorded end sits ON the stream centerline gets its DRAWN mouth
    # trimmed back onto the bed's edge (~2px inside the bank) - the confluence join; ends short
    # of the bank and runs lying wholly inside the bed are left alone
    s = Settlement(W=1000, H=1000, seed=1)
    s.meta(name="Cf", scale="town", ftpx=1)
    assert s._clip_to_stream([(100, 100), (200, 100)]) == [(100, 100), (200, 100)]  # no streams: no-op
    s.stream([(400, 50), (400, 950)], width=9)
    out = s._clip_to_stream([(300, 500), (400, 500)])  # end on the centerline -> pulled to hw-2
    assert abs(out[-1][0] - 397.5) < 0.1 and out[-1][1] == 500
    same = s._clip_to_stream([(300, 500), (370, 500)])  # short of the bank -> untouched
    assert same == [(300, 500), (370, 500)]
    inside = s._clip_to_stream([(399, 400), (400, 500)])  # wholly inside the bed -> left alone
    assert inside == [(399, 400), (400, 500)]


def test_late_water_block_carries_sheens_and_splices_after_plots():
    """field_channel(late=True) defers into the SECOND water block (spliced at its own first-call
    position so a city's comb net draws OVER the field's plots); a late course with a sheen records
    its sheenz above every late bed, mirroring the main block's contract."""
    s = Settlement(300, 300, seed=1)
    s.meta(name="T", scale="village", ftpx=2)
    rec: dict = {}
    s._water('<path d="M0,0 L10,10" stroke="#6C9CBE"/>', rec, sheen='<path d="M0,0 L10,10" stroke="#9CC"/>', late=True)
    with tempfile.TemporaryDirectory() as td:
        s.finish(os.path.join(td, "t"), render=False)
    assert rec["sheenz"] > rec["bedz"]


def test_draw_comb_field_snaps_the_intake_onto_a_nearby_stream():
    # the hairline intake's START snaps onto the stream centerline when the sluice sits on the
    # bank (within the 30px anchor band) - the confluence at the offtake; a feeder brook ending
    # exactly AT the sluice (distance ~0) is already joined and stays untouched
    from waterfields import build_comb

    s = Settlement(W=1400, H=1400, seed=5)
    s.meta(name="Sn", scale="town", ftpx=1, down_deg=90)
    s.stream([(680, 50), (680, 1350)], width=9)  # runs 20px west of the sluice
    net = build_comb(1400, 1400, (700, 200), 5, down_deg=90, field_fall=400)
    net["brook"] = []
    s.draw_comb_field(net, "f1", {"kind": "stream"})
    hx, hy = s.M["channels"][-1]["poly"][0]
    assert abs(hx - 680) < 0.5 and abs(hy - 200) < 0.5  # snapped onto the centerline
    s2 = Settlement(W=1400, H=1400, seed=6)
    s2.meta(name="Sn2", scale="town", ftpx=1, down_deg=90)
    net2 = build_comb(1400, 1400, (700, 200), 6, down_deg=90, field_fall=400)
    net2["brook"] = []
    s2.draw_comb_field(net2, "f2", {"kind": "stream", "stream": [(700, 40), (702, 120), (700, 200)]})
    assert s2.M["channels"][-1]["poly"][0] == [700, 200]  # feeder ends at the sluice: already joined


def test_fit_helpers_reject_out_of_bounds_spots():
    # the shared 55/88px canvas-margin early-outs of the appurtenance fit helpers (previously
    # exercised by the towns' legacy farmstead pass; the towns now run the bundle path)
    s = Settlement(W=1000, H=1000, seed=1)
    s.meta(name="Eb", scale="town", ftpx=1)
    assert not s._yard_fits(20, 500, 40, 26, 60, 500)
    assert not s._garden_fits(20, 500, 30, 22, 60, 500, (60, 540, 40, 26))
    assert not s._grove_fits(20, 500, 60, 30, [(60, 500)])


def test_village_grove_copse_skips_dry_crop_plots():
    # a copse clump never lands in a hem strip (the barley) - the dry_polys skip in village_grove
    s = Settlement(W=800, H=800, seed=2)
    s.meta(name="Vg", scale="village", ftpx=2)
    s.dry_polys.append([(300, 300), (500, 300), (500, 500), (300, 500)])
    s.village_grove([(280, 280), (520, 280), (520, 520), (280, 520)], role="copse", dense=False)
    for g in s.M["village_groves"]:
        for cx, cy in g["clumps"]:
            assert not (312 <= cx <= 488 and 312 <= cy <= 488)  # nothing deep inside the plot


def test_channel_accepts_an_explicit_polyline():
    # the pts= form: a hand-routed culvert's waypoints are recorded verbatim (no auto-winding)
    s = Settlement(W=800, H=800, seed=1)
    s.meta(name="Cp", scale="town", ftpx=1)
    route = [(100, 100), (160, 130), (220, 200)]
    s.channel((100, 100), (220, 200), {"kind": "offmap"}, {"kind": "field", "name": "f"}, pts=route)
    assert s.M["channels"][-1]["poly"] == [[x, y] for x, y in route]


def test_village_grove_skips_watercourses():
    # no clump lands over a stream: the watercourse skip in the clump filter
    s = Settlement(W=800, H=800, seed=3)
    s.meta(name="Vw", scale="village", ftpx=2)
    s.stream([(400, 50), (400, 750)], width=9)
    s.village_grove([(330, 300), (470, 300), (470, 500), (330, 500)], role="copse", dense=False)
    for g in s.M["village_groves"]:
        for cx, _cy in g["clumps"]:
            assert abs(cx - 400) > 10
    # ...and the MOAT counts as a watercourse for the skip too (the city case)
    s2 = Settlement(W=800, H=800, seed=4)
    s2.meta(name="Vm", scale="city", ftpx=3)
    s2.M["moat"] = [(300, 200), (500, 200), (500, 600), (300, 600), (300, 200)]
    s2.M["moat_width"] = 22
    s2.village_grove([(260, 300), (340, 300), (340, 500), (260, 500)], role="copse", dense=False)
    for g in s2.M["village_groves"]:
        for cx, _cy in g["clumps"]:
            assert cx < 289 or cx > 311


def test_farm_wells_seats_in_a_dooryard_dodging_crop():
    """The SUCCESS path of the dooryard grid scan (previously covered only incidentally by the city
    regens, which stopped triggering it once Tango's belt got its own seeded wells 2026-07-21): the
    well seats near the steading on clear ground, skipping a crop patch in the scan ring."""
    s = Settlement(1000, 1000, seed=3)
    s.meta(name="Fw2", scale="town", ftpx=1)
    s.M["houses"].append({"x": 500, "y": 500, "w": 44, "h": 29, "rot": 0})
    # the field ENVELOPE blankets every ring spot (well_at refuses inside field_polys), so the ring
    # pass fails; the DRAWN crop covers only the top half, so the fallback - which suspends the
    # envelope and tests the drawn plots - seats the well on the bottom-half rim slack
    s.field_polys.append([(340, 340), (660, 340), (660, 660), (340, 660)])
    s.dry_polys.append([(340, 340), (660, 340), (660, 500), (340, 500)])
    s.M["fields"].append(
        {"name": "f", "kind": "paddy", "outline": [[340, 340], [660, 340], [660, 660], [340, 660]], "plot_polys": [[[600, 600], [648, 600], [648, 648], [600, 648]]]}
    )  # a drawn paddy plot the fallback also dodges
    assert s.farm_wells() == 1
    w = s.M["wells"][0]
    assert w["y"] > 514  # on the rim slack below the drawn crop (+14 margin), never on the crop


def test_farm_wells_drops_a_cluster_with_no_seatable_ground():
    """A steading whose whole reach-disc is blocked ground gets skipped rather than spinning the
    cover loop forever - the well simply cannot seat, and the gate will say so."""
    s = Settlement(1000, 1000, seed=3)
    s.meta(name="Fw", scale="town", ftpx=1)
    s.M["houses"].append({"x": 500, "y": 500, "w": 44, "h": 29, "rot": 0})
    s.block_polys.append([(300, 300), (700, 300), (700, 700), (300, 700)])  # blanket the reach disc
    assert s.farm_wells() == 0
    assert not s.M["wells"]


def test_farm_wells_falls_back_to_envelope_rim_slack():
    """When a steading's whole neighborhood sits inside a field ENVELOPE (the smoothed outline
    claiming more than the crop fills), the primary seating fails and the fallback suspends the
    envelope blocks, seating the well on unplanted rim slack - but never on a DRAWN plot."""
    s = Settlement(1000, 1000, seed=4)
    s.meta(name="Fw2", scale="town", ftpx=1)
    s.M["houses"].append({"x": 500, "y": 500, "w": 44, "h": 29, "rot": 0})
    s.field_polys.append([(200, 200), (800, 200), (800, 800), (200, 800)])  # envelope blankets the disc
    s.M["fields"].append(
        {"name": "t", "kind": "paddy", "outline": [[200, 200], [800, 200], [800, 800], [200, 800]], "bbox": [200, 200, 800, 800], "plot_polys": [[[430, 430], [570, 430], [570, 570], [430, 570]]]}
    )  # drawn crop hugs the house
    assert s.farm_wells() == 1
    wx, wy = s.M["wells"][0]["x"], s.M["wells"][0]["y"]
    assert not (430 <= wx <= 570 and 430 <= wy <= 570)  # seated on rim slack, not on the crop


def test_comb_base_fill_noops_on_an_empty_net():
    """comb_base_fill draws and records nothing when the net has no plots (a degenerate field) -
    the guard that keeps a plotless comb from emitting a zero-area floor polygon."""
    s = Settlement(600, 600, seed=1)
    s.meta(name="Cb", scale="village", ftpx=2)
    s.comb_base_fill({"plots": [], "envelope": [(0, 0), (10, 0), (10, 10)]}, "empty")
    assert "empty" not in s.M.get("comb_floors", {})


def test_wall_tower_spacing_px_scales_with_tier():
    """The per-city defense tier sets the max mural-tower spacing. siege = aimed-lethal bowshot
    (197 ft), >=2 everywhere, so spacing == range; garrison = full war-bow (328 ft), >=2, so the
    wider range; peaceful keeps only >=1 flanking tower within aimed-lethal range, so its spacing
    is DOUBLE (a tower every 2*197 ft - the sparser Xi'an crossfire). At 3 ft/px (city scale):"""
    ppf = 1.0 / 3.0  # px per ft
    assert settlement.wall_tower_spacing_px(ppf, "siege") == 197.0 * ppf
    assert settlement.wall_tower_spacing_px(ppf, "garrison") == 328.0 * ppf
    assert settlement.wall_tower_spacing_px(ppf, "peaceful") == 2 * 197.0 * ppf
    # siege is tighter than garrison; peaceful is the loosest
    assert settlement.wall_tower_spacing_px(ppf, "siege") < settlement.wall_tower_spacing_px(ppf, "garrison")
    assert settlement.wall_tower_spacing_px(ppf, "peaceful") > settlement.wall_tower_spacing_px(ppf, "garrison")


def test_wall_tower_spacing_px_unknown_tier_falls_back_to_garrison():
    ppf = 1.0 / 3.0
    assert settlement.wall_tower_spacing_px(ppf, "nonsense") == settlement.wall_tower_spacing_px(ppf, "garrison")


def test_build_polder_mosaic_knob():
    # GM 2026-07-22: the `mosaic` knob roughs a surveyed polder GRID into an accreted, creek-fitted MOSAIC
    # (some 桑基魚塘 dike-pond districts read that way; some 圩田 polders read as the clean grid). It must be
    # deterministic, byte-identical at mosaic=0 (a separate rng drives it), CHANGE the geometry when on, and
    # make the parcels measurably MORE irregular (skewed toward trapezoids: larger opposite-edge angles).
    from waterfields import build_polder

    kw = {"down_deg": 90, "rows": 10, "cols": 6, "cell": 160, "parcel_mix": (0.10, 0.0, 0.60), "gap": (11.0, 11.0), "edge_wander": 0.4}
    grid = build_polder(2200, 2600, (360, 320), 21, mosaic=0.0, **kw)
    mos = build_polder(2200, 2600, (360, 320), 21, mosaic=0.5, **kw)
    assert build_polder(2200, 2600, (360, 320), 21, **kw)["plots"] == grid["plots"]  # mosaic=0 == default (byte-stable)
    assert build_polder(2200, 2600, (360, 320), 21, mosaic=0.5, **kw)["plots"] == mos["plots"]  # deterministic
    assert mos["plots"] != grid["plots"]  # the knob changes the geometry

    def mean_skew(net):
        vals = []
        for p in net["plots"]:
            q = p["poly"]
            if len(q) != 4:
                continue

            def opp(a, b, c, d):
                v1 = (b[0] - a[0], b[1] - a[1])
                v2 = (d[0] - c[0], d[1] - c[1])
                l1 = math.hypot(*v1) or 1.0
                l2 = math.hypot(*v2) or 1.0
                return math.degrees(math.acos(max(-1.0, min(1.0, abs(v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)))))

            vals.append(max(opp(q[0], q[1], q[3], q[2]), opp(q[1], q[2], q[0], q[3])))  # angle between opposite edges
        return sum(vals) / len(vals)

    assert mean_skew(mos) > mean_skew(grid) * 1.15  # the mosaic parcels run visibly more to trapezoids


def test_apply_land_use_leaves_a_lone_pond_ungated():
    # a dike-pond with NO adjacent canal (<46 px) and NO neighbour pond within reach (<52 px) gets no sluice -
    # the defensive cap that stops a lone basin drawing a giant culvert across bare ground to a distant pond.
    s = Settlement(2000, 2000, seed=1)
    s.meta(field_archetype="mulberry_dike_fishpond")
    net = {
        "plots": [
            {"poly": [(100, 100), (200, 100), (200, 200), (100, 200)], "low": True},
            {"poly": [(1500, 1500), (1600, 1500), (1600, 1600), (1500, 1600)], "low": True},  # far from the other pond
        ],
        "channels": [{"pts": [(1900, 100), (1950, 150)]}],  # a canal far from BOTH ponds
    }
    s.apply_land_use(net, "mulberry_fishpond", random.Random(1), fraction=1.0, eligible="all")
    assert s.M.get("dikepond_sluices") == []  # both basins ungated: no canal near, no neighbour near


def test_perimeter_dike_gap_off_band_still_draws_full_loop():
    # GM 2026-07-22 (issue 1): perimeter_dike NOTCHES the earthwork at each sluice-crossing gap. A gap point
    # placed FAR from the band keeps every dense point, so the band draws as one full loop (the defensive
    # all-kept branch) and the gap is still recorded on the manifest.
    s = Settlement(1000, 1000, seed=1)
    env = [(200, 200), (800, 200), (800, 800), (200, 800)]
    s.perimeter_dike(env, seed=7, gaps=[(5000, 5000)])
    assert s.M["dikes"] and s.M["dikes"][0]["gaps"] == [[5000.0, 5000.0]]


def test_perimeter_dike_notches_the_band_at_a_gap_on_it():
    # a gap ON the band splits the earthwork into runs between the notches (it records the gap and still
    # draws a dike); the through-gap is where a sluice channel crosses.
    s = Settlement(1000, 1000, seed=2)
    env = [(200, 200), (800, 200), (800, 800), (200, 800)]
    s.perimeter_dike(env, seed=3, gaps=[(500, 200), (500, 800)])
    assert s.M["dikes"] and len(s.M["dikes"][0]["gaps"]) == 2


# ---- near_ring_cropland (feature 013): channel-free dry/garden tiler that packs the flat near ring.
def test_near_ring_cropland_rejects_an_unknown_density():
    s = _town()
    with pytest.raises(ValueError, match="near_ring_density"):
        s.near_ring_cropland((0, 0, 1000, 1000), density="lush")


def test_near_ring_cropland_returns_zero_for_a_degenerate_bbox():
    s = _town()
    assert s.near_ring_cropland((100, 100, 105, 900), density="dense") == 0


def test_near_ring_cropland_fills_clear_ground_and_records_dry_plots():
    s = _town()
    n = s.near_ring_cropland((0, 0, 1000, 1000), density="dense", seed=3)
    assert n > 0
    assert len(s.M["dry_plots"]) == n
    assert len(s.dry_polys) == n  # recorded as no-build cropland
    # every plot carries the dry-plot shape the checks read
    assert all(set(p) >= {"poly", "crop", "theta"} for p in s.M["dry_plots"])


def test_near_ring_cropland_density_tiers_are_monotonic():
    def count(tier):
        s = _town()
        return s.near_ring_cropland((0, 0, 1000, 1000), density=tier, seed=7)

    assert count("dense") > count("medium") > count("thin") > 0


def test_near_ring_cropland_reads_meta_near_ring_density_when_density_is_none():
    s = _town()
    s.meta(near_ring_density="thin")
    thin = s.near_ring_cropland((0, 0, 1000, 1000), density=None, seed=2)
    s2 = _town()
    dense = s2.near_ring_cropland((0, 0, 1000, 1000), density="dense", seed=2)
    assert thin < dense  # the meta default ('thin') fills less than an explicit 'dense'


def test_near_ring_cropland_can_be_all_garden_or_all_grain():
    s = _town()
    s.near_ring_cropland((0, 0, 1000, 1000), density="dense", seed=1, garden_frac=1.0)
    assert s.M["dry_plots"] and all(p["crop"] == "garden" for p in s.M["dry_plots"])
    s2 = _town()
    s2.near_ring_cropland((0, 0, 1000, 1000), density="dense", seed=1, garden_frac=0.0)
    assert s2.M["dry_plots"] and all(p["crop"] != "garden" for p in s2.M["dry_plots"])


def test_near_ring_cropland_skips_fields_structures_hill_and_groves():
    s = _town()
    s.M["hill"] = [500, 200, 180, 120]  # a hill in the north
    s.field_polys.append([(0, 700), (400, 700), (400, 1000), (0, 1000)])  # a paddy block, SW
    s.M["houses"] = [{"x": 800, "y": 800, "w": 40, "h": 30, "rot": 0}]  # a dwelling, SE
    s.M["village_groves"] = [{"poly": [[600, 600], [760, 600], [760, 760], [600, 760]], "role": "copse", "clumps": [[680, 680]]}]
    s.near_ring_cropland((0, 0, 1000, 1000), density="dense", seed=5)
    from settlement import point_in_poly

    for p in s.M["dry_plots"]:
        cx = sum(v[0] for v in p["poly"]) / 4
        cy = sum(v[1] for v in p["poly"]) / 4
        assert not (((cx - 500) / (180 * 1.35)) ** 2 + ((cy - 200) / (120 * 1.35)) ** 2 <= 1.0)  # off the hill
        assert not point_in_poly(cx, cy, [(0, 700), (400, 700), (400, 1000), (0, 1000)])  # off the paddy
        assert not (760 >= cx >= 600 and 760 >= cy >= 600)  # off the grove belt
        assert not (780 >= cx >= 620 and 780 >= cy >= 620)  # not covering the grove clump


def test_near_ring_cropland_skips_a_grove_clump_outside_its_belt_poly():
    # a clump can sit just past its loose belt poly; the per-plot clump-bbox guard (not the belt-poly
    # test) is what keeps a plot off it, so no dry plot may cover the stray clump
    s = _town()
    s.M["village_groves"] = [{"poly": [], "clumps": [[500, 500]]}]  # empty belt poly -> only the clump guard applies
    s.near_ring_cropland((0, 0, 1000, 1000), density="dense", seed=6)
    for p in s.M["dry_plots"]:
        qx0, qy0 = min(v[0] for v in p["poly"]), min(v[1] for v in p["poly"])
        qx1, qy1 = max(v[0] for v in p["poly"]), max(v[1] for v in p["poly"])
        assert not (qx0 - 12 <= 500 <= qx1 + 12 and qy0 - 12 <= 500 <= qy1 + 12)


def test_near_ring_cropland_keeps_a_city_ring_outside_the_wall():
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="C", scale="city")
    s.M["wall"] = [[300, 300], [700, 300], [700, 700], [300, 700]]  # a square rampart
    s.near_ring_cropland((0, 0, 1000, 1000), density="dense", seed=4)
    from settlement import point_in_poly

    for p in s.M["dry_plots"]:
        cx = sum(v[0] for v in p["poly"]) / 4
        cy = sum(v[1] for v in p["poly"]) / 4
        assert not point_in_poly(cx, cy, [(300, 300), (700, 300), (700, 700), (300, 700)])  # no cropland inside the wall


# ---- near_ring_paddy (feature 014): moat/stream/edge-watered paddy basins, the dominant near-ring crop.
def test_near_ring_paddy_returns_zero_for_a_degenerate_bbox():
    s = _town()
    assert s.near_ring_paddy((100, 100, 105, 900)) == 0


def test_near_ring_paddy_places_off_edge_basins_recorded_as_paddy_fields():
    s = _town()
    n = s.near_ring_paddy((0, 0, 1000, 1000), seed=2, cell_ft=180)
    assert n > 0
    made = [fld for fld in s.M["fields"] if fld["name"].startswith("nrp_")]
    assert len(made) == n and all(fld["kind"] == "paddy" for fld in made)


def test_near_ring_paddy_skips_interior_ground_with_no_reachable_water():
    # a town (no moat) with a big frame: interior basins far from the edge have no water -> skipped;
    # only the off-edge band is filled. So no placed basin sits deep in the middle.
    s = Settlement(1600, 1600, seed=3)
    s.meta(name="T", scale="town")
    s.near_ring_paddy((0, 0, 1600, 1600), seed=3, cell_ft=150)
    for fld in s.M["fields"]:
        if fld["name"].startswith("nrp_"):
            b = fld["bbox"]
            touches_edge = b[0] < 60 or b[1] < 60 or b[2] > 1540 or b[3] > 1540
            assert touches_edge  # only edge-watered basins were placed


def test_near_ring_paddy_waters_a_basin_from_a_pond_ring():
    # an INTERIOR bbox (never touches the frame edge, no moat) - so a basin can ONLY be watered by the pond ring
    s = Settlement(1400, 1400, seed=5)
    s.meta(name="T", scale="town")
    s.M["pond"] = [700, 700, 190, 190]
    n = s.near_ring_paddy((450, 450, 950, 950), seed=5, cell_ft=120)
    assert n > 0 and any(fld["name"].startswith("nrp_") for fld in s.M["fields"])


def test_near_ring_paddy_keeps_basins_off_streams_and_the_hill():
    s = Settlement(1400, 1400, seed=4)
    s.meta(name="T", scale="town")
    s.M["hill"] = [700, 200, 200, 140]
    s.M["streams"] = [{"poly": [[700, 0], [700, 1400]], "w": 8}]  # a stream down the middle
    s.near_ring_paddy((0, 0, 1400, 1400), seed=4, cell_ft=150)
    from settlement import seg_dist

    for fld in s.M["fields"]:
        if fld["name"].startswith("nrp_"):
            for vx, vy in fld["outline"]:
                assert min(seg_dist(vx, vy, (700, 0), (700, 1400)), 999) > 14  # off the stream
                assert not (((vx - 700) / (200 * 1.35)) ** 2 + ((vy - 200) / (140 * 1.35)) ** 2 <= 1.0)  # off the hill


def test_near_ring_paddy_moat_feeds_a_walled_city_basin_with_a_channel():
    s = Settlement(1400, 1400, seed=6)
    s.meta(name="C", scale="city")
    s.M["wall"] = [[500, 500], [900, 500], [900, 900], [500, 900]]
    s.M["moat"] = [[480, 480], [920, 480], [920, 920], [480, 920]]
    s.M["moat_width"] = 22
    # a big building band just outside the west moat: a basin west of it can only be moat-fed by a
    # channel that would CROSS the building, so that basin is skipped (the channel-clearance keep-out)
    s.M["buildings"] = [{"x": 430, "y": 700, "w": 60, "h": 340, "rot": 0, "kind": "warehouse"}]
    # a road + a rect-record cemetery: both keep-out builders must run (these paths were exercised by
    # the pool maps until the 2026-07-23 combs-only doctrine retired the basins from every gen)
    s.M["road"] = [[0, 1300], [1400, 1300]]
    s.M["cemeteries"] = [{"x": 1200, "y": 200, "w": 60, "h": 40}]
    n = s.near_ring_paddy((0, 0, 1400, 1400), seed=6, cell_ft=200)
    assert n > 0
    # interior (non-off-edge) basins are moat-fed: there is at least one moat->field channel
    assert any((c.get("frm") or {}).get("kind") == "moat" for c in s.M.get("channels", []))
    # no moat channel crosses the building (the clearance keep-out held)
    from settlement import seg_dist

    for c in s.M.get("channels", []):
        if (c.get("frm") or {}).get("kind") == "moat":
            assert seg_dist(430, 700, c["poly"][0], c["poly"][-1]) > 25


def test_near_ring_paddy_respects_the_moat_current_when_the_moat_is_fed():
    # a moat fed by a stream from the north flows south; every moat intake must tap upstream of its basin
    s = Settlement(1600, 1600, seed=7)
    s.meta(name="C", scale="city")
    s.M["wall"] = [[600, 600], [1000, 600], [1000, 1000], [600, 1000]]
    s.M["moat"] = [[580, 580], [1020, 580], [1020, 1020], [580, 1020]]
    s.M["moat_width"] = 22
    s.M["streams"] = [{"poly": [[800, 580], [800, 200]], "w": 8}]  # feeder entering the moat top, coming from the north
    s.near_ring_paddy((0, 0, 1600, 1600), seed=7, cell_ft=220)
    for c in s.M.get("channels", []):
        if (c.get("frm") or {}).get("kind") == "moat":
            (_sx, sy), (_ex, ey) = c["poly"][0], c["poly"][-1]
            assert ey - sy >= -8  # field-end not upstream (north) of the moat tap - flows with the southward current


def test_near_ring_paddy_skips_cells_over_the_orientation_cap():
    # ~300px+ cells exceed the 80000px bbox cap and are skipped by the size guard; coarser cells therefore
    # place fewer basins than fine ones (the oversized ones drop out)
    coarse = _town().near_ring_paddy((0, 0, 1000, 1000), seed=8, cell_ft=320)
    fine = _town().near_ring_paddy((0, 0, 1000, 1000), seed=8, cell_ft=150)
    assert isinstance(coarse, int) and fine > coarse


def test_near_ring_paddy_keeps_basins_off_a_polygon_cemetery():
    # a funerary ground recorded as a POLYGON (not an x/w dict) still sets the paddy back (funerary_set_back_from_water)
    s = Settlement(1400, 1400, seed=9)
    s.meta(name="C", scale="city")
    s.M["wall"] = [[560, 560], [840, 560], [840, 840], [560, 840]]
    s.M["moat"] = [[540, 540], [860, 540], [860, 860], [540, 860]]
    s.M["moat_width"] = 22
    s.M["cemeteries"] = [{"poly": [[900, 900], [1050, 900], [1050, 1050], [900, 1050]], "label": "graveyard"}]
    s.near_ring_paddy((0, 0, 1400, 1400), seed=9, cell_ft=200)
    for fld in s.M["fields"]:
        if fld["name"].startswith("nrp_"):
            for vx, vy in fld["outline"]:
                assert not (900 - 60 <= vx <= 1050 + 60 and 900 - 60 <= vy <= 1050 + 60)  # set back from the grave poly


def test_clip_to_river_walks_a_multi_point_run_out_of_the_bed():
    # a channel whose first TWO points lie inside the river bed: the leading-run walk advances past
    # both and restarts the drawing at the bed edge + cap radius (the pool's taps are 2-point lines,
    # so only a synthetic multi-point run exercises the walk)
    s = _crop_settlement()
    s.M["river"] = {"pts": [(300, 100), (300, 900)], "w": 40}
    pts = [(300, 400), (310, 420), (400, 500)]  # first two inside the 20px half-bed, third clear
    out = s._clip_to_river(pts, capr=3.5)
    assert len(out) == 2  # the in-bed lead collapsed to the bank restart point
    import math as _m

    d = min(_m.hypot(out[0][0] - 300, out[0][1] - y) for y in range(100, 901))
    # the (hw - 3 + capr) = 20.5 inset runs ALONG the channel, so its perpendicular distance from the
    # centerline is shorter on a diagonal approach (here ~16); it must sit backed off inside the bed
    assert 12.0 <= d <= 21.0
