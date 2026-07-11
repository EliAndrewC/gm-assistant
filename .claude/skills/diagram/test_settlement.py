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


def test_png_width_env_overrides_render_resolution(monkeypatch):
    # DIAGRAM_PNG_WIDTH renders at a lower resolution for a quick iteration eyeball (raster cost is
    # ~quadratic in width); DIAGRAM_SKIP_RENDER skips it entirely (the test suite's default - the gate
    # reads the JSON, never the PNG). Committed maps still render at the full default width.
    from PIL import Image
    with tempfile.TemporaryDirectory() as d:
        base = os.path.join(d, "t")
        monkeypatch.setenv("DIAGRAM_PNG_WIDTH", "400")
        _town().finish(base)                              # render=True + env width -> the int(env_w) branch
        assert Image.open(base + ".png").width == 400
        base2 = os.path.join(d, "u")
        monkeypatch.setenv("DIAGRAM_SKIP_RENDER", "1")
        _town().finish(base2)                             # skip env -> no raster even though render=True
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
        svg = open(base + ".svg").read()
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
    assert pops <= {200, 250, 300, 350, 400, 450, 500}               # only the seven allowed sizes
    assert village_population(random.Random(3)) == village_population(random.Random(3))   # deterministic from the seed
    c = Counter(village_population(random.Random(i)) for i in range(4000))
    assert c.most_common(1)[0][0] == 350                             # 350 is the mode


def test_crop_to_content_frames_hard_features_with_margin():
    s = _crop_settlement()
    s.M["houses"] = [{"x": 500, "y": 500, "w": 40, "h": 30}]
    s.crop_to_content(margin=20)
    assert s.view == (460, 465, 80, 70)                              # house 500 +/- (20/2) +/- 20 margin


def test_crop_to_content_covers_fields_pond_and_poly_features():
    s = _crop_settlement()
    s.M["houses"] = [{"x": 500, "y": 500, "w": 20, "h": 20}]         # w/h branch
    s.M["village_groves"] = [{"poly": [[300, 300], [350, 300], [350, 350], [300, 350]], "role": "windbreak"}]   # poly branch
    s.M["fields"] = [{"outline": [[400, 400], [600, 400], [600, 600], [400, 600]], "vis_bbox": [420, 420, 580, 580]}]   # vis_bbox branch
    s.M["pond"] = [700, 700, 50, 40]                                 # pond branch
    s.crop_to_content(margin=0)
    assert s.view == (300, 300, 450, 440)                           # grove W/N, pond E/S


def test_crop_to_content_uses_field_outline_when_no_vis_bbox():
    s = _crop_settlement()
    s.M["houses"] = [{"x": 500, "y": 500, "w": 20, "h": 20}]
    s.M["fields"] = [{"outline": [[400, 400], [900, 400], [900, 900], [400, 900]]}]   # no vis_bbox -> falls back to outline
    s.crop_to_content(margin=0)
    assert s.view == (400, 400, 500, 500)


def test_crop_ignores_the_commons_which_just_clips_at_the_frame():
    # the commons scrub does NOT set the frame - it is drawn and simply CLIPS at the edge, so even a huge
    # commons overhanging the hard core on every side leaves the frame tight to the hard content + margin.
    # (The GM wants the frame tight to real content - the pond, a back-slope graveyard - never held open by
    # empty grazing: the Ueda-east grazing band past the lone pond used to bloat the frame ~130px.)
    s = _crop_settlement()
    s.M["houses"] = [{"x": 500, "y": 500, "w": 20, "h": 20}]         # hard core 490..510
    s.M["commons"] = [{"poly": [[200, 200], [800, 200], [800, 800], [200, 800]]}]   # huge, overhangs ALL four sides
    s.crop_to_content(margin=10)
    assert s.view == (480, 480, 40, 40)                             # hard 490..510 + 10 margin; commons ignored


def test_box_clear_detects_rect_poly_and_line_obstacles():
    s = _crop_settlement()
    s.M["houses"] = [{"x": 500, "y": 500, "w": 40, "h": 30}]                          # rect obstacle
    s.M["dry_plots"] = [{"poly": [[300, 300], [340, 300], [340, 340], [300, 340]]}]   # poly -> bbox'd into rects
    s.M["fields"] = [{"outline": [[600, 600], [800, 600], [800, 800], [600, 800]]}]   # polygon obstacle
    s.M["village_groves"] = [{"poly": [[1000, 1000], [1050, 1000], [1050, 1050], [1000, 1050]], "role": "copse"}]
    s.M["commons"] = [{"poly": [[50, 50], [80, 50], [80, 80], [50, 80]]}]
    s.M["streams"] = [{"poly": [[900, 100], [900, 900]]}]                             # line obstacle
    s.M["lanes"] = [{"pts": [[1200, 100], [1200, 500]]}]
    obs = s._title_obstacles()
    assert s._box_clear(150, 150, 200, 180, obs) is True                             # a blank patch
    assert s._box_clear(485, 490, 515, 510, obs) is False                            # on the house (rect)
    assert s._box_clear(650, 650, 750, 750, obs) is False                            # inside the field (poly)
    assert s._box_clear(880, 400, 920, 440, obs) is False                            # across the stream (line)


def test_title_lands_over_blank_space_avoiding_the_field():
    s = _crop_settlement()
    s.set_view(0, 0, 2000, 1500)
    s.M["fields"] = [{"outline": [[200, 200], [1800, 200], [1800, 1300], [200, 1300]], "vis_bbox": [200, 200, 1800, 1300]}]
    s.M["houses"] = [{"x": 100, "y": 100, "w": 40, "h": 30}]
    s.title("Testville")
    tb = s.M["title"]["bbox"]
    assert tb[2] <= 200 or tb[0] >= 1800 or tb[3] <= 200 or tb[1] >= 1300              # clear of the field blob


def test_title_falls_back_to_the_corner_when_no_blank_space():
    s = _crop_settlement()
    s.set_view(0, 0, 200, 150)                                                        # a tiny window...
    s.M["fields"] = [{"outline": [[-10, -10], [210, -10], [210, 160], [-10, 160]]}]   # ...covered entirely
    s.title("X")
    assert s.M["title"]["bbox"][0] == 30                                             # fell back to view left + 30


def test_title_without_a_view_centres_on_the_canvas():
    s = _crop_settlement()                                                            # no set_view -> self.view is None
    s.M["fields"] = [{"outline": [[-10, -10], [2010, -10], [2010, 1510], [-10, 1510]]}]   # full-canvas cover -> no gap
    s.title("Y")
    tb = s.M["title"]["bbox"]
    assert abs((tb[0] + tb[2]) / 2 - 1000) < 2                                        # centred on W/2 = 1000


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


def test_village_grove_fills_an_irregular_polygon_and_records_it():
    s = _nuc_village()                                                 # field to the EAST (x >= 640)
    poly = [(150, 350), (260, 330), (280, 640), (160, 660)]           # an irregular quad WEST of the field (open ground)
    n = s.village_grove(poly, role="windbreak")                       # dense belt -> many overlapping clumps
    assert n > 0
    vg = s.M["village_groves"]
    assert len(vg) == 1 and vg[0]["role"] == "windbreak" and len(vg[0]["poly"]) == 4


def test_village_grove_over_the_paddy_draws_and_records_nothing():
    s = _nuc_village()                                                 # field at [(640,150),(1120,150),(1120,780),(640,780)]
    poly = [(700, 250), (900, 250), (900, 450), (700, 450)]          # a footprint ENTIRELY inside the paddy
    assert s.village_grove(poly, role="copse", dense=False) == 0     # every clump skipped (on crops) -> nothing
    assert s.M["village_groves"] == []                                # ... and nothing recorded


def test_village_grove_scatter_skips_houses_and_fills_the_open_gaps():
    s = _nuc_village()
    s.M["houses"] = [{"x": 300, "y": 400, "w": 46, "h": 29}]         # one house inside the scatter region
    n = s.village_grove([(200, 300), (500, 300), (500, 500), (200, 500)], role="copse", dense=False)
    assert n >= 1                                                     # bamboo/fruit clumps settle into the gaps
    assert s.M["village_groves"][0]["role"] == "copse"


def test_village_grove_skips_clumps_on_a_lane():
    s = _nuc_village()
    s.M["lanes"] = [{"pts": [[300, 300], [300, 600]], "w": 6}]        # a lane straight down x=300
    s.village_grove([(250, 300), (350, 300), (350, 600), (250, 600)], role="copse", dense=False)
    vg = s.M["village_groves"][0]
    assert vg["clumps"]                                              # drew clumps in the gaps beside the lane
    for cx, cy in vg["clumps"]:                                      # ... but none on the lane tread + clump radius (mirrors the check)
        assert abs(cx - 300) >= 3 + vg["r"]


def test_corridor_buffers_gathers_lanes_streets_and_road():
    s = _nuc_village()
    s.M["lanes"] = [{"pts": [[0, 0], [10, 0]], "w": 6}]
    s.M["town_streets"] = [{"pts": [[0, 0], [10, 0]], "w": 10}]
    s.M["road"] = [[0, 0], [10, 0]]
    corr = s._corridor_buffers(4)
    assert [b for _, b in corr] == [3 + 4, 5 + 4, 13 + 4]            # lane 6/2, street 10/2, road 26/2, each + extra


def test_village_grove_skips_clumps_in_a_yards_sun_corridor():
    poly = [(200, 380), (360, 380), (360, 560), (200, 560)]
    n_open = _nuc_village().village_grove(poly, role="copse", dense=False)   # baseline, no yard
    s = _nuc_village()
    s.M["threshing_yards"] = [{"x": 300, "y": 420, "w": 30, "h": 6}]        # a thin yard: its SOUTHERN sun-corridor
    n_yard = s.village_grove(poly, role="copse", dense=False)               # ... removes a clump beyond the occ keep-out
    assert n_yard < n_open                                                 # the sun-corridor skip fired
    vg = s.M["village_groves"][0]
    r = vg["r"]
    se = 420 + 3                                                           # yard south edge
    for cx, cy in vg["clumps"]:                                            # ... and none left in the sun-strip (mirrors the check)
        assert not (abs(cx - 300) < 15 + r and se - r < cy < se + 22 + r)


def test_marsh_draws_wet_scatter_and_records_it():
    s = _crop_settlement()
    s.marsh([(100, 120), (600, 100), (350, 620)])                         # a triangle -> also covers the point-in-poly skip
    assert len(s.M["marshes"]) == 1 and len(s.M["marshes"][0]["poly"]) == 3
    assert s.out                                                          # drew reeds / wet tint


def test_marsh_skips_points_on_a_paddy():
    s = _crop_settlement()
    s.field_polys.append([(300, 100), (600, 100), (600, 400), (300, 400)])   # a paddy inside the region
    s.marsh([(100, 100), (600, 100), (600, 500), (100, 500)])                # straddles the paddy - reeds over it are skipped
    assert len(s.M["marshes"]) == 1


def test_marsh_pond_fringe_skips_the_open_water():
    s = _crop_settlement()
    s.M["pond"] = [300, 300, 100, 80]                                        # a pond inside the region
    s.marsh([(150, 150), (450, 150), (450, 450), (150, 450)], role="pond_fringe")   # reeds rim the shore, not the open water
    assert s.M["marshes"][0]["role"] == "pond_fringe"


def test_pond_anchored_detects_a_watercourse_that_connects_to_the_pond():
    # the cue that a course should snap onto the pond rim: either end's anchor is kind=='pond'
    assert Settlement._pond_anchored({"kind": "pond"}, {"kind": "field"}) is True
    assert Settlement._pond_anchored({"kind": "field"}, {"kind": "pond"}) is True
    assert Settlement._pond_anchored({"kind": "offmap"}, {"kind": "field"}) is False
    assert Settlement._pond_anchored(None, None) is False


def test_clip_to_pond_is_a_noop_without_a_pond():
    s = _crop_settlement()                                  # no pond recorded on this map
    pts = [(100, 100), (200, 200)]
    assert s._clip_to_pond(pts) == pts                      # nothing to snap to -> returned unchanged


def test_clip_to_pond_snaps_a_connecting_end_onto_the_rim():
    s = _crop_settlement()
    s.M["pond"] = [300, 300, 100, 80]                       # centre (300,300), rx=100, ry=80; rim where rad==1

    def rad(p):
        return ((p[0] - 300) / 100) ** 2 + ((p[1] - 300) / 80) ** 2

    inside = s._clip_to_pond([(300, 300), (310, 310), (300, 500)])   # a RUN inside the pond -> trimmed to start AT the rim
    assert abs(rad(inside[0]) - 1.0) < 1e-3
    assert inside[-1] == (300, 500)                         # the field end is untouched
    outside = s._clip_to_pond([(300, 388), (300, 600)])     # foot JUST OUTSIDE (rad ~1.21) -> a rim point is prepended
    assert abs(rad(outside[0]) - 1.0) < 1e-3
    assert outside[1] == (300, 388)                         # the original foot is kept, the rim point sits before it


def test_field_channel_routes_pieces_through_the_water_block():
    s = _crop_settlement()
    s.M["pond"] = [300, 300, 100, 80]
    run = [(300, 300)] + [(300 + 30 * i, 380 + 30 * i) for i in range(9)]   # sluice inside -> snapped to the rim
    s.field_channel(run, "#6C9CBE", 6.0, 2.0)              # tapering -> split into stroked pieces of decreasing width
    s.field_channel(run, "#7C9EB0", 3.0, 3.0)             # uniform width -> the single-stroke branch
    s.field_channel([(300, 300), (600, 700)], "#6C9CBE", 6.0, 2.0)   # only 2 pts -> degenerate pieces are skipped
    assert s.water and s._water_idx is not None            # routed through _water, not a bare s.add


def test_pond_feeder_snaps_to_the_rim_even_when_drawn_before_the_pond():
    # the DEFERRED clip: a feeder is drawn BEFORE the pond (M['pond'] unknown at call time), then the pond;
    # at flush both a bed+sheen feeder (stream) and a bed-only feeder (channel) are re-emitted snapped to the
    # rim, so neither lays a stroke across the open water.
    with tempfile.TemporaryDirectory() as d:
        base = os.path.join(d, "t")
        s = Settlement(1000, 1000, seed=1)
        s.meta(name="V", scale="village")
        s.stream([(500, 20), (500, 300)], frm={"kind": "offmap"}, to={"kind": "pond"})       # brook INTO the pond, drawn FIRST
        s.channel((500, 260), (200, 260), {"kind": "pond"}, {"kind": "field", "name": "w"})  # supply channel OUT of the pond
        s.pond(500, 250, 100, 70)                          # pond LAST - the clip must still find it at flush
        s.finish(base, render=False)
        assert "9CB4C8" in open(base + ".svg").read()      # water rendered (the flush ran the re-emit)


def test_commons_draws_open_scrub_and_records_it():
    s = _nuc_village()                                                # field to the EAST (x >= 640)
    poly = [(60, 300), (200, 320), (110, 660)]                       # a TRIANGLE of open ground WEST of the field
    s.commons(poly)                                                  # grass tufts + brush + scraggly pines
    assert len(s.M["commons"]) == 1 and len(s.M["commons"][0]["poly"]) == 3
    assert s.out                                                     # it drew the scrub texture


def test_commons_skips_scrub_that_would_fall_on_the_paddy():
    s = _nuc_village()                                                # field at [(640,150),(1120,150),(1120,780),(640,780)]
    s.commons([(560, 300), (760, 300), (760, 600), (560, 600)])     # straddles the field's W edge - clumps over crops skipped
    assert len(s.M["commons"]) == 1


def test_on_lane_flags_the_tread_and_clears_off_it():
    s = _nuc_village()
    s.lane([(300, 100), (300, 700)], width=6, clearance=11, worn=True)   # a vertical lane at x=300
    assert s._on_lane(300, 400, 3) is True                              # dead on the tread
    assert s._on_lane(360, 400, 3) is False                             # well off to the side


def test_commons_keeps_scrub_off_a_trodden_lane():
    s = _nuc_village()
    s.lane([(300, 100), (300, 700)], width=6, clearance=11, worn=True)   # a lane crossing the scrub
    s.commons([(220, 150), (420, 150), (420, 650), (220, 650)])          # straddles the lane - tufts on the tread are skipped
    assert len(s.M["commons"]) == 1                                      # still recorded (the skip is per-tuft, not the plot)


def test_marsh_keeps_reeds_off_a_lane_causeway():
    s = _crop_settlement()
    s.lane([(100, 300), (500, 300)], width=6, clearance=11, worn=True)   # a causeway through the marsh
    s.marsh([(100, 150), (500, 150), (500, 450), (100, 450)])            # reeds on the tread are skipped
    assert len(s.M["marshes"]) == 1


def test_commons_keeps_scrub_off_a_shrine_and_torii():
    # a commons that OVERLAPS the shrine must not scatter scrub over the hall or its torii arch (both are
    # block_polys); the skip is per-tuft, so the plot is still recorded
    s = _nuc_village()
    s.shrine_hall(320, 400, "", w=60, h=48, kind="shrine", torii=[(320, 330)], graveyard=False)
    s.commons([(220, 150), (420, 150), (420, 650), (220, 650)])          # straddles the shrine + torii blocks
    assert len(s.M["commons"]) == 1


def test_marsh_keeps_reeds_off_a_building():
    s = _crop_settlement()
    s.shrine_hall(300, 300, "", w=60, h=48, kind="shrine", graveyard=False)   # a block_poly inside the marsh
    s.marsh([(150, 150), (500, 150), (500, 450), (150, 450)])            # reeds on the hall are skipped
    assert len(s.M["marshes"]) == 1


def test_cemetery_default_is_a_ruled_rectangle():
    s = _crop_settlement()
    s.cemetery(300, 300, 100, 70)
    assert 'width="100"' in s.out[-1] and "<path" not in s.out[-1]        # a plotted rectangle, no organic blob


def test_cemetery_organic_draws_an_irregular_plot():
    s = _crop_settlement()
    s.cemetery(300, 300, 100, 70, parish=False, organic=True)
    frag = s.out[-1]
    assert "<path" in frag and 'width="100"' not in frag                  # a jittered blob outline, no ruled 100-wide plot rect
    assert s.M["cemeteries"][-1]["w"] == 100                              # recorded bbox is still the w x h rectangle
    assert s.block_polys[-1] == [(242, 257), (358, 257), (358, 343), (242, 343)]   # no-build block unchanged (checks unaffected)


def test_rect_on_water_blocks_a_solid_part_on_an_irrigation_line():
    # the homestead solver rejects a house/yard/garden that lands on a channel/ditch/stream, but NOT the grove
    s = _crop_settlement()
    s.M["field_ditches"] = [{"poly": [(400, 300), (400, 500)], "role": "drain", "w": 6, "field": "f"}]
    s.M["channels"] = [{"poly": [(600, 300), (600, 500)], "w": 2.5}]
    s.M["streams"] = [{"poly": [(800, 300), (800, 500)], "w": 9}]
    assert s._rect_on_water((400, 400, 24, 16)) is True                   # garden straddling the drain -> seg_dist branch
    assert s._rect_on_water((360, 400, 100, 10)) is True                   # a wide rect an edge of which the ditch CROSSES far from any corner -> segments_cross branch
    assert s._rect_on_water((600, 400, 20, 14)) is True                   # on the feeder channel
    assert s._rect_on_water((800, 400, 20, 14)) is True                   # on the stream
    assert s._rect_on_water((500, 400, 24, 16)) is False                  # dry ground between them -> clear
    # the grove (fields=False) is exempt - it may hug a bund/ditch; the solid parts (fields=True) are not
    assert s._rect_blocked((400, 400, 24, 16), fields=False) is False
    assert s._rect_blocked((400, 400, 24, 16), fields=True) is True


def test_rect_on_water_skips_a_degenerate_course_and_far_ones():
    # the collision pre-filter: a degenerate (<2-point) course is dropped from _water_obstacles (it has no
    # segment and would crash the bbox min/max on an empty poly), and a course whose bbox is nowhere near
    # the rect is skipped without any seg_dist / crossing math.
    s = _crop_settlement()
    s.M["streams"] = [{"poly": [(100, 100)], "w": 9},                       # degenerate: single point -> skipped
                      {"poly": [(1500, 1300), (1500, 1400)], "w": 9}]       # real, but far from the probe rect
    assert s._water_obstacles() == [(s.M["streams"][1]["poly"], 9 / 2 + 5, (1500, 1300, 1500, 1400))]
    assert s._rect_on_water((400, 400, 24, 16)) is False                    # far course bbox-rejected -> clear


def _byre_village():
    s = _crop_settlement()
    hs = [{"x": 300 + i * 170, "y": 350, "w": 40, "h": 28, "kind": "plain", "rot": 0, "wealth": 1.6 - 0.1 * i}
          for i in range(5)]
    s.M["houses"] = hs
    for h in hs:
        s.placed.append((h["x"], h["y"], h["w"], h["h"]))
    return s, hs


def test_draft_byres_scatters_shared_sheds_among_the_houses():
    s, hs = _byre_village()
    placed = s.draft_byres(fraction=0.6, gap=40)                          # ~60% of 5 = 3 shared byres
    assert len(placed) == 3 and len(s.M["byres"]) == 3
    assert all(b["w"] > 0 and b["h"] > 0 for b in s.M["byres"])
    assert "<rect" in s.out[-1]                                           # a byre glyph was drawn


def test_draft_byres_skips_a_homestead_boxed_in_on_all_sides():
    s = _crop_settlement()
    s.M["houses"] = [{"x": 300, "y": 300, "w": 40, "h": 28, "kind": "plain", "rot": 0, "wealth": 1.0}]
    s.placed.append((300, 300, 40, 28))
    for a in range(0, 360, 20):                                           # wall the homestead in with placed footprints
        rad = settlement.math.radians(a)
        s.placed.append((300 + 70 * settlement.math.cos(rad), 300 + 70 * settlement.math.sin(rad), 60, 60))
    assert s.draft_byres(fraction=1.0) == []                             # nowhere to put a byre -> skipped


def test_draft_byres_keeps_off_the_paddy():
    s = _crop_settlement()
    s.M["houses"] = [{"x": 300, "y": 300, "w": 40, "h": 28, "kind": "plain", "rot": 0, "wealth": 1.0}]
    s.placed.append((300, 300, 40, 28))
    s.field_polys.append([(330, 200), (600, 200), (600, 500), (330, 500)])   # paddy on the E half of the ring
    placed = s.draft_byres(fraction=1.0)
    assert len(placed) == 1 and placed[0][0] < 330                       # the byre lands on the dry (W) side, off the paddy


def test_bridges_spans_a_lane_where_it_crosses_a_canal():
    s = _crop_settlement()
    s.lane([(100, 300), (500, 300)], width=6, worn=True)                  # a lane running E-W
    s.M["field_ditches"] = [{"poly": [[300, 150], [300, 450]], "w": 5}]   # a canal crossing it at (300, 300)
    n = s.bridges()
    assert n == 1 and len(s.M["bridges"]) == 1
    assert abs(s.M["bridges"][0]["x"] - 300) < 2 and abs(s.M["bridges"][0]["y"] - 300) < 2


def test_channel_footbridges_plank_each_long_ditch_perpendicular():
    s = _crop_settlement()
    s.M["field_ditches"] = [
        {"poly": [[100, 200], [400, 200], [800, 200]], "w": 5, "role": "main"},   # 700px, 2 segments -> two planks at spacing 320
        {"poly": [[100, 400], [160, 400]], "w": 4, "role": "branch"},     # 60px -> below min_len, no plank
    ]
    n = s.channel_footbridges(spacing=320)
    assert n == 2 and len(s.M["bridges"]) == 2                            # the short stub is stepped over, not bridged
    assert all(abs(abs(b["rot"]) - 90) < 1 for b in s.M["bridges"])       # deck runs N-S, ACROSS the E-W ditch
    assert all(190 < b["y"] < 210 for b in s.M["bridges"])               # both sit ON the ditch line


def test_shrine_well_places_a_well_beside_the_hall():
    s = _crop_settlement()
    s.M["religious"] = [{"x": 400, "y": 400, "w": 30, "h": 24, "kind": "shrine"}]
    spot = s.shrine_well(400, 400)
    assert spot is not None
    import math as _m
    assert _m.hypot(spot[0] - 400, spot[1] - 400) <= 115 and len(s.M["wells"]) == 1   # close beside the hall


def test_shrine_well_returns_none_when_boxed_in():
    s = _crop_settlement()
    for a in range(0, 360, 15):                                          # wall off every ring position around the hall
        rad = settlement.math.radians(a)
        for rr in (54, 66, 80, 96, 112):
            s.placed.append((400 + rr * settlement.math.cos(rad), 400 + rr * settlement.math.sin(rad), 40, 40))
    assert s.shrine_well(400, 400) is None and not s.M["wells"]


def test_channel_footbridges_slides_a_plank_clear_of_a_farmhouse():
    s = _crop_settlement()
    s.M["field_ditches"] = [{"poly": [[100, 300], [700, 300]], "w": 5, "role": "main"}]   # 600px E-W ditch
    s.M["houses"] = [{"x": 400, "y": 300, "w": 60, "h": 40, "kind": "plain", "rot": 0}]   # a house ON the ditch midpoint
    n = s.channel_footbridges(spacing=800)                                # n=1, midway = (400,300) = on the house
    assert n == 1
    b = s.M["bridges"][0]
    assert not (365 <= b["x"] <= 435) and 190 < b["y"] < 410            # the plank slid ALONG the ditch, off the house footprint


# --- fragmented dooryard gardens: _garden_beds picks single / flanking / stacked / side-by-side --------
def _pos_where(pred):
    """The first (x, y) on a deterministic sweep whose position-hash lands in the wanted branch."""
    for i in range(4000):
        x, y = 100 + i * 0.7, 200 + (i * 1.3) % 500
        if pred(x, y):
            return x, y
    raise AssertionError("no position matched the predicate")   # pragma: no cover


def test_garden_beds_undivided_is_the_common_case():
    s = _nuc_village()
    x, y = _pos_where(lambda x, y: Settlement._hjit(x, y, 8.0) >= 0.26)
    beds = s._garden_beds(x, y, 23, 14, x + 20, y, 20, 20, "E", 3)
    assert beds == [(x + 20, y, 20, 20)]                                # one undivided plot


def test_garden_beds_opposite_flank_puts_the_house_between_two_beds():
    s = _nuc_village()
    x, y = _pos_where(lambda x, y: Settlement._hjit(x, y, 8.0) < 0.26 and Settlement._hjit(x, y, 9.0) < 0.5)
    beds = s._garden_beds(x, y, 23, 14, x + 20, y, 20, 20, "E", 3)
    assert len(beds) == 2 and min(b[0] for b in beds) < x < max(b[0] for b in beds)   # flanking E and W


def test_garden_beds_stacked_when_same_side_south_garden():
    s = _nuc_village()
    x, y = _pos_where(lambda x, y: Settlement._hjit(x, y, 8.0) < 0.26 and Settlement._hjit(x, y, 9.0) >= 0.5
                      and Settlement._hjit(x, y, 10.0) < 0.5)
    beds = s._garden_beds(x, y, 23, 14, x, y + 30, 20, 20, "SE", 3)     # a SOUTH garden -> may stack above/below
    assert len(beds) == 2 and beds[0][0] == beds[1][0] and beds[0][1] != beds[1][1]   # same x, different y


def test_garden_beds_side_by_side_when_same_side_not_stacked():
    s = _nuc_village()
    x, y = _pos_where(lambda x, y: Settlement._hjit(x, y, 8.0) < 0.26 and Settlement._hjit(x, y, 9.0) >= 0.5
                      and Settlement._hjit(x, y, 10.0) >= 0.5)
    beds = s._garden_beds(x, y, 23, 14, x, y + 30, 20, 20, "SE", 3)     # not stacked -> side by side
    assert len(beds) == 2 and beds[0][1] == beds[1][1] and beds[0][0] != beds[1][0]   # same y, different x


def test_garden_beds_too_narrow_falls_back_to_one_bed():
    s = _nuc_village()
    x, y = _pos_where(lambda x, y: Settlement._hjit(x, y, 8.0) < 0.26)   # a split is WANTED
    beds = s._garden_beds(x, y, 23, 14, x, y + 12, 8, 8, "SE", 3)        # ... but the plot is too small to split
    assert beds == [(x, y + 12, 8, 8)]


def test_attach_garden_draws_and_records_two_beds():
    s = _nuc_village()
    s._attach_garden(500, 500, [(486, 500, 10, 12), (520, 500, 10, 12)])
    beds = s.M["gardens"]
    assert len(beds) == 2 and all(b["of"] == [500, 500] and len(b["poly"]) == 4 for b in beds)


def test_bundle_geom_nucleated_records_a_gardens_list_spanning_the_bbox():
    s = _nuc_village()
    x, y = _pos_where(lambda x, y: Settlement._hjit(x, y, 8.0) < 0.26 and Settlement._hjit(x, y, 9.0) < 0.5)
    geom = s._bundle_geom(x, y, 46, 28, "E")                            # a big house so the flank split clears its gate
    assert len(geom["gardens"]) == 2
    bx, by, bw, bh = geom["bbox"]
    for gx, gy, gw, gh in geom["gardens"]:                             # every bed lies inside the bundle bbox
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
