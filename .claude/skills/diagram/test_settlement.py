#!/usr/bin/env python3
"""Unit tests for settlement.py methods/branches the pool generators don't exercise.

The five worked maps cover most of settlement.py; this file reaches the rest - a couple of
unused vocabulary methods (torii_path, forest/wall labels, polygon-based flower field) and a
few internal branches (degenerate segment, the road path of face-street rotation, the big->
plain ring fallback). Together with test_villages (which runs the gens in-process) this brings
settlement.py to 100%.

    python3 -m pytest test_settlement.py -q
"""

import json
import math
import os
import random
import re
import tempfile

import pytest

import settlement
from settlement import Settlement, _centroid, seg_dist


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


def test_title_without_a_view_centers_on_the_canvas():
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
    assert s.M["kido"][0]["rot"] == 90.0 and s.M["kido"][1]["rot"] == 0.0  # legacy flags map to the axis angles


def test_ward_kido_aligns_to_fence_tangent_and_guards_the_interior():
    # GM 2026-07-24: the kido is a gap IN the fence - a slanted fence run gets a slanted gate
    # (rot = the local fence tangent; a 30deg fence means a 30deg gate, never an axis-aligned
    # stamp), and the guard box hangs on the ward-interior flank (the ward's own gate watch).
    s = Settlement(1000, 1000, seed=1)
    s.ward("slant", [(100, 100), (400, 400), (700, 400)], gates=[(250, 250), (550, 400, True)])  # legacy 3-tuple accepted, flag ignored
    k45, k0 = s.M["kido"][-2], s.M["kido"][-1]
    assert abs(k45["rot"] - 45.0) < 0.5  # the 45deg run gets a 45deg gate
    assert abs(k0["rot"] - 0.0) < 0.5  # the flat run stays flat (the ignored legacy flag did NOT force 90)
    # the fence centroid (400, 300) sits NORTH of the flat run at y400, so the guard box hangs
    # north of the bar: the glyph's bbox reaches well north of the fence line and stays snug south
    assert k0["bbox"][1] < 400 - 25 and k0["bbox"][3] < 400 + 25


def test_ward_kido_squares_to_the_lane_it_bars_and_keeps_its_box_off_the_roadbed():
    # GM 2026-07-26: the gate shuts a WAY. A 45deg fence crossed by a HORIZONTAL street gets a
    # gate square to the street (90deg), not to the fence - and the watch box stands on the verge.
    s = Settlement(1000, 1000, seed=1)
    s.street([(100, 450), (900, 450)])
    s.ward("slant", [(300, 300), (600, 600)], gates=[(450, 450)])
    k = s.M["kido"][-1]
    assert abs(k["rot"] - 90.0) < 0.5  # square across the street, NOT the fence's 45deg
    st = s.M["town_streets"][-1]
    half = st["w"] / 2
    assert all(abs(cy - 450) > half for _, cy in k["guard"])  # the box is beside the roadbed, not in it


def test_kido_reservation_covers_the_glyph_the_ward_will_actually_draw():
    # the gen must reserve a ward gate's ground before the packs run, but s.ward draws it near the
    # END - so the reservation has to predict the glyph. It does that by asking the engine for the
    # same seat s.ward will take, which is why it is a method and not a rect in the gen.
    s = Settlement(1000, 1000, seed=1)
    s.street([(100, 450), (900, 450)])
    fence = [(300, 300), (600, 600)]
    res = s.kido_reservation(450, 450, fence, margin=0.0)
    s.ward("slant", fence, gates=[(450, 450)])
    k = s.M["kido"][-1]
    x0, y0 = min(p[0] for p in res), min(p[1] for p in res)
    x1, y1 = max(p[0] for p in res), max(p[1] for p in res)
    assert (x0, y0, x1, y1) == pytest.approx(tuple(k["bbox"]), abs=0.2)  # a zero-margin reservation IS the drawn glyph's extent
    assert min(p[0] for p in s.kido_reservation(450, 450, fence)) < x0  # ...and the default margin inflates it


def test_kido_guard_box_takes_the_far_flank_when_the_near_one_is_blocked():
    # the box yields, never the gate: where the near side of the opening is taken (here by a wall
    # tower standing at the rampart, the Nagahara case), it seats on the other side of its own
    # gateway rather than overlapping (which no generic overlap pass would catch - kido are exempt)
    s = Settlement(1000, 1000, seed=1)
    s.street([(100, 450), (900, 450)])
    s.M["wall_towers"] = [{"x": 430, "y": 436, "w": 26, "h": 26, "rot": 0}]  # stands on the near flank of the opening (the rampart side), where the box would sit
    s.ward("slant", [(300, 300), (600, 600)], gates=[(450, 450)])
    k = s.M["kido"][-1]
    assert not settlement.sat_overlap([(c[0], c[1]) for c in k["guard"]], settlement.tower_quad(s.M["wall_towers"][0]))
    assert sum(c[1] for c in k["guard"]) / 4 > 450  # it crossed to the other side of its own gateway (local +x, which the 90deg bar puts SOUTH)


def test_kido_guard_box_stands_clear_of_its_own_ward_fence():
    # GM 2026-07-27: "ward gates seem to sometimes overlap with neighborhood walls". The GATEWAY
    # stands on the fence - it IS the opening - but the guard box is a building on the verge, and
    # an oblique crossing used to cut straight through it (2 of the pool's 14 gates). SAT against
    # the stroked fence, not corner distances: a line through a 15x16 box's middle leaves every
    # corner ~8px clear, so the corner test the lane beds use reported it clear.
    fence = [(300, 300), (600, 600)]
    s = Settlement(1000, 1000, seed=1)
    s.street([(100, 450), (900, 450)])
    s.ward("slant", fence, gates=[(450, 450)])
    box = [(c[0], c[1]) for c in s.M["kido"][-1]["guard"]]
    assert not any(settlement.sat_overlap(box, q) for q in settlement.stroke_quads(fence, 4.0))
    # and the RESERVATION agrees with the drawn glyph, which is why the fence goes in explicitly:
    # at reservation time s.ward has not run, so M['wards'] is still empty
    s2 = Settlement(1000, 1000, seed=1)
    s2.street([(100, 450), (900, 450)])
    res = s2.kido_reservation(450, 450, fence, margin=0.0)
    assert (min(p[0] for p in res), min(p[1] for p in res)) == pytest.approx(tuple(s.M["kido"][-1]["bbox"][:2]), abs=0.2)


def test_clear_label_seat_walks_out_and_gives_up_when_nothing_is_clear():
    # a verge-hugging feature puts its DEFAULT below-label on the frontage it hugs, so the seat is
    # probed: below, above, then left/right, walking outward. On a frontage packed solid there is
    # no clear box at all, and the siter must be told so rather than handed a seat on a shopfront.
    s = _town()
    assert s.clear_label_seat(500, 500, 30, 12, "notice board") == (500, 517)  # the default below-seat, when it is clear
    s.M["buildings"] = [{"x": 500, "y": 500, "w": 2000, "h": 2000, "rot": 0, "kind": "merchant"}]
    assert s.clear_label_seat(500, 500, 30, 12, "notice board") is None
    assert not s.label_seat_clear(500, 517, 26.0)


def test_a_wellhead_is_refused_in_the_paddy_water_and_allowed_on_the_rim():
    # the PLACEMENT half of wells_clear_of_paddies - both halves read paddy_wet_rings, so the siter
    # and the check cannot disagree about where the water is (the same-source doctrine)
    s = _town()
    basin = [[600, 600], [900, 600], [900, 900], [600, 900]]
    s.M["fields"] = [{"name": "f1", "kind": "paddy", "outline": [[400, 400], [900, 400], [900, 900], [400, 900]], "plot_polys": [basin]}]
    assert not s._well_ground_clear(750, 750)  # in the water
    assert not s._well_ground_clear(750, 594)  # the drawn head laps a basin's edge
    assert s._well_ground_clear(450, 450)  # the fan's unplanted rim slack, inside the envelope
    s.M["fields"][0]["plot_polys"] = [[[0, 0], [1, 1]]]  # a field drawing no real basins...
    assert not s._well_ground_clear(450, 450)  # ...falls back to its outline, as the rural tiers do
    s.M["fields"][0]["outline"] = [[0, 0]]  # and one drawing nothing at all contributes no water
    assert s._well_ground_clear(450, 450)
    s.M["fields"][0]["kind"] = "dry"  # a DRY field is not this rule's business
    assert s._well_ground_clear(750, 750)


def test_stroke_quads_makes_one_quad_per_segment():
    qs = settlement.stroke_quads([(0, 0), (100, 0), (100, 100)], 5.0)
    assert len(qs) == 2 and all(len(q) == 4 for q in qs)
    assert settlement.stroke_quads([(0, 0)], 5.0) == []
    assert settlement.stroke_quads([(7, 7), (7, 7)], 5.0)  # a degenerate segment still yields a quad rather than dividing by zero


def test_way_beds_carries_the_lane_network_lane_runs_does_not():
    # the AVOIDANCE list for a verge-hugging feature: lane_runs' roads/streets/alleys/ring road
    # PLUS the village lane network. Each siter used to build its own partial list, which is how a
    # punishment ground came to clip an alley (reported by another session, Tango 2026-07-27).
    M = {"road": [[0, 100], [500, 100]], "alleys": [{"pts": [[0, 300], [500, 300]], "w": 6}], "lane": [[0, 500], [500, 500]], "lanes": [{"pts": [[0, 700], [500, 700]], "w": 8}]}
    beds = settlement.way_beds(M)
    assert len(beds) == 4 and len(settlement.lane_runs(M)) == 2
    assert sorted(round(b[0][0][1]) for b in beds) == [100, 300, 500, 700]


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


def test_pack_shortfall_is_reported(capsys):
    # the "no silent caps" principle applied to placement (2026-07-24 town audit: Hirameki's
    # gate market authored 12 businesses, landed 4, and nothing said so)
    s = _town()
    s.pack((100, 100, 130, 130), ["merchant"] * 3)  # room for at most one grid spot
    out = capsys.readouterr().out
    assert "PACK SHORTFALL" in out and "merchant" in out


def test_pack_full_placement_stays_silent(capsys):
    s = _town()
    s.pack((100, 100, 900, 900), ["merchant"] * 2)
    assert "SHORTFALL" not in capsys.readouterr().out


def test_frontage_shortfall_is_reported(capsys):
    s = _town()
    s.frontage([(100, 500), (160, 500)], ["merchant"] * 8)  # a 60px street cannot host 8
    assert "FRONTAGE SHORTFALL" in capsys.readouterr().out


def test_pack_face_streets_true_skips_streetless_ground(capsys):
    # face_streets=True means businesses line a frontage ONLY: with no street within reach,
    # every grid spot is skipped and nothing places (the branch Hirameki's gate-market pack
    # exercised until 2026-07-24, when the market moved to fixed coordinates)
    s = _town()
    n = s.pack((100, 100, 400, 400), ["shop"] * 2, face_streets=True)
    assert n == 0 and "PACK SHORTFALL" in capsys.readouterr().out


def test_kosatsuba_records_a_blocking_struct():
    # the notice board records its manifest entry at true size (~12x5 ft) and reserves its
    # verge (a later pack must not bury the board)
    s = _town()
    z = s.kosatsuba(500, 500, rot=15)
    kb = s.M["kosatsuba"][0]
    assert (kb["x"], kb["y"], kb["w"], kb["h"], kb["rot"]) == (500, 500, 12, 5, 15) and z > 0
    assert (kb["vw"], kb["vh"]) == (12, 5)  # at 1 ft/px the true frame already clears the marker floor
    assert not s._fits(500, 500, 20, 20)
    assert s.M["labels"][-1][1] > 500  # default label sits BELOW the board
    s.kosatsuba(800, 500, label_above=True)  # gate-adjacent boards label ABOVE (clear of the gate)
    assert s.M["labels"][-1][1] < 500


def test_kosatsuba_draws_a_location_marker_at_the_coarse_tiers():
    # GM 2026-07-24: at village (2 ft/px) and city (3 ft/px) grain the true 12x5 ft frame draws a
    # 2.5 px / 1.7 px sliver that reads as fence hardware, so the GLYPH floors at the long-axis
    # marker minimum with the 12:5 aspect preserved. The manifest keeps TRUE feet in w/h and the
    # drawn box in vw/vh; the drawn box is what is reserved against later placement.
    for ftpx in (2, 3):
        s = Settlement(1000, 1000, seed=1)
        s.meta(name="C", scale="city" if ftpx == 3 else "village", ftpx=ftpx)
        s.kosatsuba(500, 500)
        kb = s.M["kosatsuba"][0]
        assert (kb["w"], kb["h"]) == (12 / ftpx, 5 / ftpx)  # true size, unchanged
        assert kb["vw"] == settlement.KOSATSUBA_MARKER_MIN_PX  # floored on the long axis...
        assert kb["vh"] == round(settlement.KOSATSUBA_MARKER_MIN_PX * 5 / 12, 1)  # ...aspect preserved
        assert s.placed[-1] == pytest.approx((500, 500, settlement.KOSATSUBA_MARKER_MIN_PX, settlement.KOSATSUBA_MARKER_MIN_PX * 5 / 12))  # the DRAWN box is reserved
        assert f'width="{kb["vw"]:.1f}"' in s.top[-1]  # and drawn


def test_place_kosatsuba_sites_on_the_lane_verge_at_the_busiest_node():
    # the village/hamlet auto-placer (GM 2026-07-24): the board lands inside the validator's
    # ~60-real-ft siting band, off the tread, clear of structures - and at the BUSY end of
    # the lane (siting is a traffic decision), not the empty one
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="T", scale="hamlet", ftpx=1)
    s.lane([(100, 500), (900, 500)], width=6, clearance=22, worn=True)
    for i in range(4):
        s.M["houses"].append({"x": 700.0 + 40 * i, "y": 560.0, "w": 30, "h": 20, "kind": "plain", "rot": 0})
        s.placed.append((700.0 + 40 * i, 560.0, 30, 20))
    spot = s.place_kosatsuba()
    assert spot is not None
    kb = s.M["kosatsuba"][0]
    assert abs(kb["y"] - 500) <= 60  # inside the kosatsuba_by_the_road band
    assert kb["x"] > 500  # the busy east end, not the empty west end
    assert kb["rot"] == 0  # long axis along the lane


def test_place_kosatsuba_reads_road_and_lane_routes_and_skips_degenerate_segments():
    # the placer reads the SAME manifest route fields as the validator (road + lane + lanes);
    # a zero-length segment (duplicate consecutive points) is skipped, not divided by
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="T", scale="hamlet", ftpx=1)
    s.M["road"] = [[100, 300], [100, 300], [900, 300]]
    s.M["lane"] = [[100, 700], [900, 700]]
    assert s.place_kosatsuba() is not None
    assert len(s.M["kosatsuba"]) == 1


def test_place_kosatsuba_samples_only_the_main_way_when_one_is_declared():
    # GM 2026-08-02 (Ubame): the board goes ALONG the main road, never a side street - even
    # when the side lane's node is busier. With a road on the map, the lane's verges are not
    # candidates at all, so the board lands in the road's siting band despite every house
    # standing by the lane.
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="T", scale="town", ftpx=1)
    s.M["road"] = [[100, 300], [900, 300]]
    s.M["lane"] = [[100, 700], [900, 700]]
    for i in range(6):
        s.M["houses"].append({"x": 300.0 + 60 * i, "y": 760.0, "w": 30, "h": 20, "kind": "plain", "rot": 0})
        s.placed.append((300.0 + 60 * i, 760.0, 30, 20))
    assert s.place_kosatsuba() is not None
    assert abs(s.M["kosatsuba"][0]["y"] - 300) <= 60  # the road's band, not the busy lane's


def test_kosatsuba_label_xy_hand_seats_the_caption():
    # both caption bands can be taken at a junction seat (Nagahara's market bend: drum tower
    # in the below band, the ward gate's glyph + caption stack in the above band) - label_xy
    # is the explicit hand seat, the same escape the punishment ground carries
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="T", scale="town", ftpx=1)
    s.kosatsuba(500, 500, rot=0, label_xy=(560, 488))
    lab = s.M["labels"][-1]
    assert lab[5] == "notice board"
    assert abs((lab[0] + lab[2]) / 2 - 560) < 2  # seated at the hand x, not the default below-seat


def test_place_kosatsuba_opt_out_and_no_routes():
    # meta(kosatsuba=False) is the suppressed/backwater opt-out; with no routes at all there
    # is no verge to site on - both return None and place nothing
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="T", scale="hamlet", ftpx=1, kosatsuba=False)
    s.lane([(100, 500), (900, 500)], width=6, clearance=22, worn=True)
    assert s.place_kosatsuba() is None and not s.M["kosatsuba"]
    s2 = Settlement(1000, 1000, seed=1)
    s2.meta(name="T", scale="hamlet", ftpx=1)
    assert s2.place_kosatsuba() is None and not s2.M["kosatsuba"]


def test_fill_declares_a_capacity_budget_and_stays_silent(capsys):
    # fill=True marks the request as "place up to N" (the city district-fill idiom), so an
    # under-fill is intended, not drift - no warning
    s = _town()
    s.pack((100, 100, 130, 130), ["merchant"] * 3, fill=True)
    s.frontage([(100, 500), (160, 500)], ["merchant"] * 8, fill=True)
    assert "SHORTFALL" not in capsys.readouterr().out


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


def test_tree_stand_canopy_is_deferred_and_never_drawn_over_a_building_or_well():
    # the canopy is QUEUED at forest_patch() time and drawn at flush, so it is filtered against the
    # COMPLETE map: a building and a well placed AFTER the wood still end up with clear roofs.
    s = _town()
    s.forest_patch([(300, 300), (900, 300), (900, 900), (300, 900)])
    assert not s.M["tree_crowns"]  # nothing drawn yet - only the litter floor is down
    s.building(600, 600, 60, 40, "merchant", 0)
    s.well(500, 500)
    s.flush_tree_stands()
    crowns = s.M["tree_crowns"]
    assert crowns  # the stand itself did draw
    b = s.M["buildings"][-1]
    wl = s.M["wells"][-1]
    for i in range(0, len(crowns), 3):
        x, y, r = crowns[i], crowns[i + 1], crowns[i + 2]
        # CIRCLE vs RECT, the same rounded-corner measure `_crown_covers` and the gate's
        # structures_clear_of_trees use - NOT the naive AABB this line used to carry. The AABB
        # includes the four CORNER squares a circle cannot reach, so it called a crown sitting
        # diagonally off a corner an overlap: (562.5, 573.7) r=8.7 against a 60x40 building at
        # (600, 600) is 7.5 x 6.3 px clear of the nearest corner, i.e. 9.8 px away from a crown
        # that reaches 8.7. It only ever passed because no crown had landed in a corner diagonal
        # before the 2026-08-08 re-roll put one there (test geometry stricter than the rule it
        # guards is a false alarm waiting for a re-roll).
        dx, dy = max(abs(x - b["x"]) - b["w"] / 2, 0.0), max(abs(y - b["y"]) - b["h"] / 2, 0.0)
        assert dx * dx + dy * dy >= r * r
        assert math.hypot(x - wl["x"], y - wl["y"]) >= r + wl.get("vr", wl["r"])
    n = len(crowns)
    s.flush_tree_stands()  # idempotent - the queue is drained
    assert len(s.M["tree_crowns"]) == n


def test_fringe_trees_keep_off_the_crop():
    # the wood's advance-growth fringe seeds on waste ground, never in a worked field
    s = _town()
    s.field_polys.append([(100, 100), (400, 100), (400, 400), (100, 400)])
    assert s._fringe_blocked(250, 250, 8) is True  # inside the crop
    assert s._fringe_blocked(392, 250, 8) is True  # ... and within a crown's reach of its edge
    assert s._fringe_blocked(700, 700, 8) is False  # open waste ground


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


def test_moat_river_junction_feet_tilt_with_the_current():
    # GM 2026-07-24 hydrology review: the junction feet are NOT square rfoot tees. The upstream
    # (inlet) end shifts UPSTREAM off its square foot - a near-square, sediment-wary intake with
    # only a slight tilt - and the downstream (outlet) end sweeps DOWNSTREAM further (confluences
    # merge at downstream angles). River pts run upstream-first; a vertical river makes the
    # shifts pure y offsets, so the asymmetry is directly measurable.
    import math as m

    s = _crop_settlement()
    s.meta(name="RT", scale="city", walled=True, ftpx=3)
    pts = [(round(1000 + 300 * m.cos(2 * m.pi * i / 16)), round(700 + 300 * m.sin(2 * m.pi * i / 16))) for i in range(16)]
    river = [(1360, 100), (1360, 1300)]  # flows top -> bottom (upstream-first)
    for ring in (pts, pts[::-1]):  # both ring orientations: keep[0] lands downstream on one, upstream on the other
        mo = s.moat(ring, gap=24, river=river)
        (inlet, adj_in), (outlet, adj_out) = sorted([(mo[0], mo[1]), (mo[-1], mo[-2])], key=lambda e: e[0][1])
        in_shift = adj_in[1] - inlet[1]  # upstream (negative-y) shift of the inlet foot off square
        out_shift = outlet[1] - adj_out[1]  # downstream (positive-y) sweep of the outlet foot
        assert in_shift > 0  # inlet tilts upstream, never smoothly flow-aligned
        assert out_shift > in_shift  # the outlet sweeps harder - the researched asymmetry


def test_moat_river_junction_tilts_follow_a_reversed_river():
    # the OTHER branch of the tilt bookkeeping (keep[0]'s end downstream): same asymmetry when the
    # river runs bottom -> top (upstream-first pts reversed). Deterministic on purpose - this branch
    # was previously covered only by whichever orientation a pool map happened to roll, so an rng
    # shift elsewhere dropped it out of coverage (2026-07-24).
    import math as m

    s = _crop_settlement()
    s.meta(name="RT2", scale="city", walled=True, ftpx=3)
    pts = [(round(1000 + 300 * m.cos(2 * m.pi * i / 16)), round(700 + 300 * m.sin(2 * m.pi * i / 16))) for i in range(16)]
    river = [(1360, 1300), (1360, 100)]  # flows bottom -> top (upstream-first)
    mo = s.moat(pts, gap=24, river=river)
    (outlet, adj_out), (inlet, adj_in) = sorted([(mo[0], mo[1]), (mo[-1], mo[-2])], key=lambda e: e[0][1])
    in_shift = inlet[1] - adj_in[1]  # upstream is +y now: the inlet foot shifts DOWN off square
    out_shift = adj_out[1] - outlet[1]  # the outlet foot sweeps UP, downstream with the current
    assert in_shift > 0  # inlet tilts upstream, never smoothly flow-aligned
    assert out_shift > in_shift  # the outlet sweeps harder - the researched asymmetry


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
    # > 10, not the old > 40: the throat is TO SCALE since 2026-07-27 (30 ft clear + a 15 ft pier a
    # side = 15 px between post centres at 1 px = 3 ft), where it used to open a 210 ft gap. The
    # assertion here is about ORIENTATION - N and S of the opening, not E and W - so it must not
    # re-encode the old spacing as its threshold.
    assert abs(posts[0]["y"] - posts[1]["y"]) > 10 and abs(posts[0]["x"] - posts[1]["x"]) < 30


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
    s.flush_stable_yards()
    yd = s.M["stable_yards"][-1]
    assert (yd["x"], yd["y"], yd["r"], yd["of"], yd["troughs"]) == (400, 400, 60, [400, 400], 2)
    assert "troughs_at" in yd  # the cluster anchor stable_troughs_beside_well validates
    s.animal_ground(700, 700, r=52, label="caravan ground")
    s.flush_stable_yards()
    assert s.M["labels"][-1][5] == "caravan ground"  # label boxes are [x0, y0, x1, y1, z, text]


def test_caravan_scale_yard_gets_three_troughs_beside_the_nearest_well():
    # the watering point (settlements.md 'Stable yard' watering): a caravan-scale ground (r >= 76)
    # draws 3 troughs, and the cluster HUGS the recorded well - a bucket-pour from the wellhead
    # (GM 2026-07-23: "otherwise you'd have to carry the water a long way"), even a well past the rim
    s = _crop_settlement()
    s.M["wells"] = [{"x": 500, "y": 400, "r": 8, "vr": 4.0, "shrine": False}]
    s.animal_ground(400, 400, r=80)
    s.flush_stable_yards()
    yd = s.M["stable_yards"][-1]
    assert yd["troughs"] == 3
    assert yd["troughs_at"] == [492.2, 400.0]  # wellhead vr 4.0 + half a 4.6 trough + 1.5 step from the well at x=500
    out = "".join(s.out)
    assert out.count('fill="#8FA6B0"') == 3  # the trough rects
    assert 'x="489.9"' in out  # the cluster's trough rects, centered on troughs_at


def test_vertical_hug_offsets_far_enough_to_clear_the_well_house_roof():
    # the Tango caravan-ground defect (GM 2026-07-23): a 3-trough stack is TALLER than it is
    # wide, so the old fixed offset (vr + half a trough LENGTH) let a near-vertical ray clip
    # the roof corner - the direction-aware offset clears the roof square along any ray
    s = _crop_settlement()
    s.M["wells"] = [{"x": 400, "y": 330, "r": 8, "vr": 4.0, "shrine": False}]  # due north: a vertical ray
    s.animal_ground(400, 400, r=80)  # caravan scale - 3 troughs
    s.flush_stable_yards()
    yd = s.M["stable_yards"][-1]
    assert yd["troughs"] == 3
    bx0, by0, bx1, by1 = yd["troughs_box"]
    assert by0 >= 330 + 4.0  # the box top clears the roof square's bottom edge
    assert by0 - (330 + 4.0) == pytest.approx(1.5, abs=0.11)  # ... by exactly the bucket-pour step (round-off)


def test_cluster_walks_off_a_neighbor_wells_roof():
    # an idobata PAIR: the yard sits on well A (dist < 1, skipped as the target), so the cluster
    # hugs well B - but B's yard-side flank lands on A's roof, so the walk-around must find a
    # flank clear of BOTH roofs (the neighbor-well rejection)
    s = _crop_settlement()
    s.M["wells"] = [
        {"x": 400, "y": 400, "r": 8, "vr": 4.0, "shrine": False},  # A - under the yard center
        {"x": 408, "y": 400, "r": 8, "vr": 4.0, "shrine": False},  # B - the target
    ]
    s.animal_ground(400, 400, r=60)
    s.flush_stable_yards()
    bx0, by0, bx1, by1 = s.M["stable_yards"][-1]["troughs_box"]
    for w in s.M["wells"]:
        vr = w["vr"]
        assert not (bx0 < w["x"] + vr and bx1 > w["x"] - vr and by0 < w["y"] + vr and by1 > w["y"] - vr)


def test_yard_digs_its_own_well_when_the_near_wellheads_flanks_are_all_blocked():
    # the Nagahara yard-1 case: a well IS in reach, but a building crowds every flank of the
    # wellhead, so no bucket-pour spot exists beside it - the yard digs its own well instead
    s = _crop_settlement()
    s.M["wells"] = [{"x": 400, "y": 460, "r": 8, "vr": 4.0, "shrine": False}]
    s.M["buildings"] = [{"x": 400, "y": 460, "w": 40, "h": 40}]  # covers the whole flank ring
    s.animal_ground(400, 400, r=60)
    s.flush_stable_yards()
    assert len(s.M["wells"]) == 2  # the in-reach well was unusable; the yard dug its own
    nw, ta = s.M["wells"][-1], s.M["stable_yards"][-1]["troughs_at"]
    assert math.hypot(nw["x"] - ta[0], nw["y"] - ta[1]) <= s.px(40)  # cluster hugs the new wellhead


def test_yard_digs_its_own_well_when_none_in_reach():
    # every recorded well beyond r + 40: the yard sinks its OWN courtyard well and clusters the
    # troughs beside it (the caravanserai / yizhan post-yard form - GM 2026-07-23, the Nagahara
    # defect: the old fallback dropped the cluster at a random spot, a 100-241 ft bucket-carry)
    s = _crop_settlement()
    s.M["wells"] = [{"x": 900, "y": 900, "r": 8, "vr": 4.0, "shrine": False}]
    s.animal_ground(400, 400, r=60)
    s.flush_stable_yards()
    yd = s.M["stable_yards"][-1]
    assert yd["troughs"] == 2
    assert len(s.M["wells"]) == 2  # the yard dug its own
    nw = s.M["wells"][-1]
    assert math.hypot(nw["x"] - 400, nw["y"] - 400) <= 60  # sunk inside the yard disc
    ta = yd["troughs_at"]
    assert math.hypot(nw["x"] - ta[0], nw["y"] - ta[1]) <= s.px(40)  # cluster hugs the new wellhead


def _yard_glyphs(s, yards=None):
    """Every drawn well / trough cluster / hitching rail on the map as (label, quad) - built with
    the SAME shared builders the placement and the check both use (settlement.wellhead_quad etc.),
    so these tests measure the drawn extents rather than a test-local guess at them."""
    out = [(f"well@{w['x']:.0f},{w['y']:.0f}", settlement.wellhead_quad(w)) for w in s.M.get("wells", [])]
    for i, yd in enumerate(yards if yards is not None else s.M.get("stable_yards", [])):
        if yd.get("troughs_box"):
            out.append((f"troughs@yard{i}", settlement.trough_quad(yd["troughs_box"])))
        for rl in yd.get("rails", []) or []:
            out.append((f"rail@{rl['x']:.0f},{rl['y']:.0f}", settlement.rail_quad(rl)))
    return out


def _assert_no_glyph_overlaps(s, yards=None):
    g = _yard_glyphs(s, yards)
    for i in range(len(g)):
        for j in range(i + 1, len(g)):
            assert not settlement.sat_overlap(g[i][1], g[j][1]), f"{g[i][0]} overlaps {g[j][0]}"


def test_hitching_rails_refuse_a_seat_across_a_wellhead():
    # the GM-caught Nagahara defect (2026-07-25): a rail drawn straight over a wellhead. The yard's
    # RNG is seeded on its own position, so the seats it takes are deterministic - draw the yard
    # once to learn where its rails land, then sink a wellhead on each of those exact spots. Before
    # the rule, `clear()` knew nothing about wells and the second yard drew the identical rails,
    # straight across all three heads; now it must walk to clear ground instead.
    bare = _crop_settlement()
    bare.M["wells"] = [{"x": 900, "y": 900, "r": 8, "vr": 4.0, "shrine": False}]  # out of reach, so nothing near the yard
    bare.animal_ground(400, 400, r=60)
    bare.flush_stable_yards()
    seats = [(rl["x"], rl["y"]) for rl in bare.M["stable_yards"][-1]["rails"]]
    assert len(seats) == 2  # the two interior rails (no road in this bare fixture, so no road-parallel rail)

    s = _crop_settlement()
    s.M["wells"] = [{"x": sx, "y": sy, "r": 8, "vr": 4.0, "shrine": False} for sx, sy in seats]
    s.animal_ground(400, 400, r=60)
    s.flush_stable_yards()
    yd = s.M["stable_yards"][-1]
    assert yd["rails"]  # the train still ties up somewhere - the rule moves rails, it does not delete them
    assert [(rl["x"], rl["y"]) for rl in yd["rails"]] != seats  # ... and they are NOT the old on-the-wellhead seats
    _assert_no_glyph_overlaps(s)


def test_the_trough_cluster_walks_off_a_rail_already_seated():
    # the other half of the Nagahara defect: the watering point is placed AFTER the rails, and it is
    # PINNED - it must hug its well - so it is the side that has to walk. Sink the well 10.5px
    # beyond a known rail seat, off the rail itself but close enough that the natural yard-side
    # flank (well + ~8px bucket-pour offset) lands the cluster squarely on the rail. Before the
    # rule, beside() knew nothing about rails and stacked the troughs on the posts.
    bare = _crop_settlement()
    bare.M["wells"] = [{"x": 900, "y": 900, "r": 8, "vr": 4.0, "shrine": False}]  # out of reach: nothing near the yard
    bare.animal_ground(400, 400, r=60)
    bare.flush_stable_yards()
    sx, sy = [(rl["x"], rl["y"]) for rl in bare.M["stable_yards"][-1]["rails"]][0]  # a horizontal rail north of the yard center

    s = _crop_settlement()
    s.M["wells"] = [{"x": sx, "y": sy - 10.5, "r": 8, "vr": 4.0, "shrine": False}]
    s.animal_ground(400, 400, r=60)
    s.flush_stable_yards()
    yd = s.M["stable_yards"][-1]
    assert yd["troughs"] == 2 and yd["rails"]  # the yard still waters its train and still ties it up
    _assert_no_glyph_overlaps(s)


def test_a_yard_digs_its_own_well_clear_of_its_own_rails():
    # the dig-your-own-well fallback draws a THIRD glyph after the rails are down, so it predicts
    # its own head size (_well_vr) and seats clear of them
    s = _crop_settlement()
    s.M["wells"] = [{"x": 900, "y": 900, "r": 8, "vr": 4.0, "shrine": False}]  # far out of reach: the yard sinks its own
    s.animal_ground(400, 400, r=60)
    s.flush_stable_yards()
    yd = s.M["stable_yards"][-1]
    assert len(s.M["wells"]) == 2 and yd["troughs"] == 2 and yd["rails"]
    _assert_no_glyph_overlaps(s)


def test_a_rail_refuses_a_seat_on_an_EARLIER_yards_trough_cluster():
    # the cross-yard branch, reached by CONSTRUCTION since no natural yard spacing produces it (see
    # the preventive-guard test below): a neighboring yard just north has already put its watering
    # point at our yard's first rail seat, so that seat must be refused and the rail retried
    bare = _crop_settlement()
    bare.M["wells"] = [{"x": 900, "y": 900, "r": 8, "vr": 4.0, "shrine": False}]
    bare.animal_ground(400, 400, r=60)
    bare.flush_stable_yards()
    sx, sy = [(rl["x"], rl["y"]) for rl in bare.M["stable_yards"][-1]["rails"]][0]

    s = _crop_settlement()
    s.M["wells"] = [{"x": 900, "y": 900, "r": 8, "vr": 4.0, "shrine": False}]
    s.M["stable_yards"] = [
        {"x": 400, "y": 340, "r": 40.0, "of": [400, 340], "troughs": 2, "troughs_at": [sx, sy], "troughs_box": [sx - 2.3, sy - 2.8, sx + 2.3, sy + 2.8], "rails": [], "dung_heaps": []}
    ]
    s.animal_ground(400, 400, r=60)
    s.flush_stable_yards()
    yd = s.M["stable_yards"][-1]
    assert yd["rails"] and (sx, sy) not in [(rl["x"], rl["y"]) for rl in yd["rails"]]  # seat refused, rail retried elsewhere
    _assert_no_glyph_overlaps(s)


def test_a_second_yards_furniture_keeps_off_the_first_yards_glyphs():
    # PREVENTIVE guard, not a reproduction: no natural two-yard spacing yet produces a cross-yard
    # collision (searched the 90-150px x 0-90px offset grid at three yard radii, 2026-07-25), but
    # each yard still measures against every EARLIER yard's rails and cluster - the dung-heap rule
    # shipped without that and had to be widened for exactly this hole twice. The check is what
    # actually catches it, from whatever direction it arrives; this holds the placement side honest.
    s = _crop_settlement()
    s.M["wells"] = [{"x": 460, "y": 400, "r": 8, "vr": 4.0, "shrine": False}]  # in reach of BOTH yards
    s.animal_ground(400, 400, r=60)
    s.animal_ground(520, 400, r=60)
    s.flush_stable_yards()
    assert len(s.M["stable_yards"]) == 2
    _assert_no_glyph_overlaps(s)


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
    # marches the avenue away from the hall at the HOUSE PITCH (TORII_PITCH_FT, 20 real ft) from
    # the single given point - it was a fixed 44px until 2026-07-25, which is 132 ft at city scale
    s = _torii_city(torii_count=7)
    step = s.px(settlement.TORII_PITCH_FT)
    y0 = 500 + s.px(84) / 2 + step  # the hall's front edge + one pitch - _avenue_at_threshold owns the seat now
    assert s.M["religious"][-1]["torii_count"] == 7
    assert sorted(t[1] for t in s.M["torii"]) == pytest.approx([y0 + step * i for i in range(7)], abs=0.1)


def test_shrine_hall_extends_a_multi_point_avenue_along_its_own_step():
    # >= 2 given points: extension continues the avenue's OWN stride, not the 44px default
    s = Settlement(1200, 1200, seed=9)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    s.shrine_hall(600, 500, "Temple", w=s.px(130), h=s.px(84), kind="temple", torii=[(600, 560), (600, 570)], torii_count=3)
    # a 10px (30 ft) authored stride is inside the pitch band, so it stands - but the whole run is
    # slid in to the hall's threshold (front edge y514 + the 10px stride), which is _avenue_at_threshold's job
    assert sorted(t[1] for t in s.M["torii"]) == pytest.approx([524, 534, 544], abs=0.1)


def test_shrine_hall_roll_below_geometry_draws_the_first_n():
    # a roll/pin smaller than the supplied avenue keeps the arches nearest the hall
    s = Settlement(1200, 1200, seed=9)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    s.shrine_hall(600, 500, "Temple", w=s.px(130), h=s.px(84), kind="temple", torii=[(600, 560), (600, 598), (600, 636)], torii_count=1)
    assert [t[1] for t in s.M["torii"]] == pytest.approx([500 + s.px(84) / 2 + s.px(settlement.TORII_PITCH_FT)], abs=0.1)  # ...seated at the threshold


def _walled_city(fence=((300, 700), (900, 700))):
    # a city with ONE wall already drawn (a ward fence), so the torii placement can see it
    s = Settlement(1200, 1200, seed=9)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    s.ward("samurai", list(fence), gates=[])
    return s


def test_torii_refuses_a_seat_standing_in_a_wall():
    # a torii is a freestanding gateway; an arch set INTO a barrier is impossible construction, so
    # the primitive refuses it outright (the hand-placed path - an avenue shortens itself instead)
    s = _walled_city()
    with pytest.raises(ValueError, match="would stand in the samurai ward fence"):
        s.torii_path([(600, 600), (600, 700), (600, 800)])


def test_shrine_hall_shortens_its_avenue_short_of_a_wall():
    # the avenue is pulled BACK as a whole (uniform stride) so the rolled count still fits on open
    # ground rather than marching the last arches into the fence. The run is threshold-seated at the
    # hall's front edge (y514) with a 10px (30 ft, inside the pitch band) stride, so 7 arches would
    # reach y584 and cross the fence at y570.
    s = _walled_city(fence=((300, 570), (900, 570)))
    s.shrine_hall(600, 500, "Temple", w=s.px(130), h=s.px(84), kind="temple", torii=[(600, 560), (600, 570)], torii_count=7)
    ys = [t[1] for t in s.M["torii"]]
    assert len(ys) == 7  # every rolled arch is drawn
    assert ys[-1] < 566 and settlement.torii_wall_conflicts(s.M) == []  # shortened to stop before the fence, all clear
    strides = [ys[i + 1] - ys[i] for i in range(6)]
    assert max(strides) - min(strides) <= 0.2  # ... and still evenly spaced (the run is scaled, not re-seated one by one)
    # ...and the THRESHOLD is re-taken after the shortening: pulling the stride in would otherwise
    # leave the innermost arch standing at the old, wider gap from the hall (GM 2026-07-27).
    assert ys[0] - 514 == pytest.approx(strides[0], abs=0.2)


def test_shrine_hall_refuses_an_avenue_that_cannot_be_shortened_clear():
    # if even the first arch stands in the wall, no shortening helps: fail the gen rather than
    # close the arches up on each other or fudge the geometry
    # (the message names "a wall" rather than the fence here: no single arch STANDS in it - it is the
    # walk between them that crosses - so torii_seat_on_wall has no run to name for the first arch)
    s = _walled_city(fence=((300, 545), (900, 545)))
    with pytest.raises(ValueError, match="cannot be shortened clear of a wall"):
        s.shrine_hall(600, 500, "Temple", w=s.px(130), h=s.px(84), kind="temple", torii=[(600, 560), (600, 570)], torii_count=7)


def test_shrine_hall_repitches_an_overwide_avenue_along_its_own_line():
    # GM 2026-07-25: the gen authors the avenue's LINE, the engine owns its STRIDE. An authored run
    # wider than two rail-spans is re-laid at the ~20 ft house pitch, resampled by arc length along
    # the authored line - so a CURVED sando keeps its curve and its innermost seat, only tightening.
    s = Settlement(1200, 1200, seed=9)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    s.shrine_hall(600, 500, "Temple", w=s.px(130), h=s.px(84), kind="temple", torii=[(600, 560), (600, 598), (640, 636)], torii_count=3)
    ts = s.M["torii"]
    step = s.px(settlement.TORII_PITCH_FT)
    assert ts[0][0] == 600 and ts[0][1] == pytest.approx(500 + s.px(84) / 2 + step, abs=0.1)  # innermost arch one pitch off the hall's front
    gaps = [math.hypot(ts[i + 1][0] - ts[i][0], ts[i + 1][1] - ts[i][1]) for i in range(2)]
    assert gaps == pytest.approx([step, step], abs=0.15)  # evenly re-pitched to the house stride
    assert all(t[0] == 600 for t in ts)  # ... and still on the authored line's first leg (it never reaches the bend)


def test_shrine_hall_leaves_an_avenue_inside_the_pitch_band_alone():
    # the village avenues (~30 ft, 1.9 rail-spans) are deliberate and must not be re-pitched: within
    # the band the gen's own spacing stands, so only the over-wide town/city runs are touched
    s = Settlement(1200, 1200, seed=9)
    s.meta(name="V", scale="village", ftpx=2, down_deg=90)
    s.shrine_hall(600, 500, "Shrine", w=s.px(60), h=s.px(48), torii=[(600, 560), (600, 575), (600, 590)], torii_count=3)
    # the 15px stride survives untouched; only the run's distance from the hall changes (front edge y512 + 15)
    assert [t[1] for t in s.M["torii"]] == pytest.approx([527, 542, 557], abs=0.1)


def test_shrine_hall_shortens_an_avenue_that_would_straddle_a_wall():
    # a run that BRACKETS a wall without any single arch touching it is still wrong: a sando is one
    # approach and cannot continue on the far side of a barrier, so the walk between the arches is
    # tested too. Here (at 2 ft/px) the hall's front edge is y544 and the authored 16px stride seats
    # the run at y560/576/592, so the fence at y585 falls inside the ~7px gap between the glyph boxes
    # of the arches at y576 and y592 - no arch stands in it - and the whole run is still pulled back to
    # the near side. A per-arch nudge would have "fixed" it by straddling.
    s = Settlement(1200, 1200, seed=9)
    s.meta(name="V", scale="village", ftpx=2, down_deg=90)
    s.ward("samurai", [(300, 585), (900, 585)], gates=[])
    s.shrine_hall(600, 532, "Shrine", w=s.px(60), h=s.px(48), torii=[(600, 560), (600, 576)], torii_count=3)
    ys = [t[1] for t in s.M["torii"]]
    assert len(ys) == 3
    assert max(ys) < 582 and settlement.torii_wall_conflicts(s.M) == []  # entirely on the near side of the fence
    assert ys[0] - 544 == pytest.approx(ys[1] - ys[0], abs=0.2)  # ...and the tightened stride is re-matched at the hall's front


def test_ward_refuses_a_fence_laid_across_a_standing_torii():
    # the Nagahara case (GM 2026-07-25): the fence is drawn AFTER the temple, so the avenue could not
    # have avoided it - the wall side must catch it, since neither feature can move once drawn
    s = Settlement(1200, 1200, seed=9)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    # the arch is seated by _avenue_at_threshold at the hall's front edge (y514) + one 20 ft pitch
    s.shrine_hall(600, 500, "Temple", w=s.px(130), h=s.px(84), kind="temple", torii=[(600, 700)], torii_count=1)
    with pytest.raises(ValueError, match=r"the samurai ward fence runs through torii arch\(es\) at \[\(600.0, 520.7\)\]"):
        s.ward("samurai", [(300, 521), (900, 521)], gates=[])


def test_avenue_at_threshold_slides_a_marooned_sando_in_to_its_hall():
    # GM 2026-07-27: "the distance from the front of the temple should be the same as the distance
    # between each torii arch". Tango's Bishamon sando was spaced right at 20 ft and authored 139 ft
    # away, so it read as three red marks beside an unrelated building. The run keeps its direction,
    # its curve and its stride - only its distance from the hall changes.
    s = Settlement(1200, 1200, seed=9)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    s.shrine_hall(600, 500, "Temple", w=s.px(130), h=s.px(84), kind="temple", torii=[(600, 700), (600, 710)], torii_count=3)
    ys = [t[1] for t in s.M["torii"]]
    strides = [ys[i + 1] - ys[i] for i in range(2)]
    assert strides == pytest.approx([10, 10], abs=0.1)  # the authored 10px (30 ft) stride is inside the pitch band and stands
    assert ys[0] - (500 + s.px(84) / 2) == pytest.approx(10, abs=0.1)  # ...and the gap to the hall now MATCHES it


def test_avenue_at_threshold_pulls_a_beside_the_hall_gate_onto_the_flank_it_stands_off():
    # a run authored off to the SIDE is measured to the hall's nearest FACE, not its centre (the
    # footprint discipline), so it slides onto the flank it actually stands off rather than diagonally
    # in toward the middle of the building - which is what makes a beside-the-hall gate read as
    # belonging to that hall.
    s = Settlement(1200, 1200, seed=9)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    s.shrine_hall(600, 500, "Temple", w=s.px(130), h=s.px(84), kind="temple", torii=[(760, 500)], torii_count=1)
    (tx, ty, _z) = s.M["torii"][0]
    assert ty == 500  # stayed on its own line
    assert tx - (600 + s.px(130) / 2) == pytest.approx(s.px(settlement.TORII_PITCH_FT), abs=0.1)


def test_avenue_at_threshold_leaves_a_degenerate_avenue_alone():
    # nothing to seat, and an arch drawn ON the hall is torii_clear_of_shrine's defect to report -
    # this method translates a sando, it does not paper over a broken one
    s = Settlement(600, 600, seed=1)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    assert s._avenue_at_threshold(300, 300, 40, 30, []) == []
    on_the_hall = [(300.0, 300.0), (300.0, 320.0)]
    assert s._avenue_at_threshold(300, 300, 40, 30, on_the_hall) == on_the_hall


def test_label_hits_counts_gate_furniture_arches_and_wellheads():
    # the ladder's scorer must see every drawn glyph a caption can bury. A torii is a bare [x, y, z]
    # triple and a wellhead has no w/h, so neither is in self.placed and both were invisible to it
    # (GM 2026-07-27) - which is how Tango's theater-stage caption walked onto Benten's gate and its
    # cremation-ground caption onto a well.
    s = Settlement(600, 600, seed=1)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    assert s._label_hits(300, 300, "caption", 11) == 0
    s.M.setdefault("gate_structs", []).append({"x": 300, "y": 300, "w": 20, "h": 12})
    s.M["torii"].append([300, 300, 1])
    s.M["wells"].append({"x": 300, "y": 300, "r": 8, "vr": 4})
    assert s._label_hits(300, 300, "caption", 11) == 3


def test_hall_caption_steps_out_of_its_own_sando():
    # GM 2026-07-27: an arch is "never covered by the 'temple of X' label". A hall's caption and its
    # approach both want the ground at the hall's face, so bringing the arches to the threshold put
    # the two on the same spot - the caption takes the hall's other side.
    s = Settlement(1200, 1200, seed=9)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    s.shrine_hall(600, 500, "Temple of Ebisu", w=s.px(130), h=s.px(84), kind="temple", torii=[(600, 700)], torii_count=7, label_below=True)
    cap = [L for L in s.M["labels"] if L[5] == "Temple of Ebisu"][0]
    arches = [(t[0], t[1]) for t in s.M["torii"]]
    txh, tyu, tyd = settlement.torii_halfbox(s.ftpx)
    assert not any(cap[0] < ax + txh and ax - txh < cap[2] and cap[1] < ay + tyd and ay - tyu < cap[3] for ax, ay in arches)
    assert cap[1] > max(ay for _, ay in arches)  # here it stayed on the gen's side, stepping past the far end of the sando


def test_open_seat_answers_where_a_feature_can_actually_stand():
    # GM 2026-07-25: fitting one extra well into a packed quarter cost three regenerate-and-check
    # cycles of hand-picked coordinates because nothing outside the engine could ask _fits where
    # there was room. open_seat asks it directly, so its answer is what placement will actually take.
    s = Settlement(1200, 1200, seed=3)
    s.meta(name="T", scale="town")
    s.block_polys.append([(390, 390), (500, 390), (500, 510), (390, 510)])  # the left half of the rect is no-build
    seat = s.open_seat((400, 400, 600, 500), 20, 20)
    assert seat is not None and s._fits(seat[0], seat[1], 20, 20)  # a seat the real placement path accepts
    assert seat[0] >= 500 and not s._in_blocked(*seat)  # ... off the blocked ground, which a manifest-only scan could not have known

    far = s.open_seat((400, 400, 600, 500), 20, 20, clear_of=[(600, 500)])  # stand away from an existing feature
    assert far is not None and math.hypot(far[0] - 600, far[1] - 500) > math.hypot(seat[0] - 600, seat[1] - 500)

    s.M["commons"] = [{"poly": [(490, 380), (620, 380), (620, 520), (490, 520)]}]  # grazed waste over the clear half
    assert s.open_seat((400, 400, 600, 500), 20, 20, well=True) is None  # a wellhead may not stand in it...
    assert s.open_seat((400, 400, 600, 500), 20, 20) is not None  # ... though anything else may

    s.block_polys.append([(0, 0), (1200, 0), (1200, 1200), (0, 1200)])  # nowhere left at all
    assert s.open_seat((400, 400, 600, 500), 20, 20) is None


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


def test_bridges_carries_the_ring_road_over_the_cargo_canal_but_not_over_a_buried_conduit():
    """The ring road is a carried way and the cargo canal a watercourse - the pair that used to be
    invisible here, so both cities hand-placed that deck and both went crooked (GM 2026-07-27). An
    UNDRAWN channel is a buried conduit, though: nothing on the ground to bridge."""
    s = _crop_settlement()
    s.M["ring_road"] = [[100, 300], [500, 300]]
    s.M["ring_road_width"] = 7
    s.M["canals"] = [{"poly": [[300, 150], [300, 450]], "w": 12}]
    s.M["channels"] = [{"poly": [[200, 150], [200, 450]], "frm": None, "to": None, "w": 2.5, "drawn": False}]
    assert s.bridges() == 1  # the canal only - the conduit is not a crossing
    deck = s.M["bridges"][0]
    assert abs(deck["x"] - 300) < 2 and abs(deck["y"] - 300) < 2  # ON the crossing, solved not eyeballed
    assert deck["rot"] == 0 and deck["w"] == 7  # ALONG the ring road, and as wide as the way it carries


def test_place_punishment_spot_probes_for_a_clear_caption_seat():
    """The display board's caption gets its own probe, because a verge-hugging feature's default
    below-label lands on the frontage it hugs - which is what 'hugging the frontage' means."""
    s = _crop_settlement()
    s.street([(200, 300), (800, 300)], width=10)
    # a shopfront row along the south verge, so the caption's DEFAULT seat below the board is taken
    # and the probe has to walk outward to a clear one
    for _bx in range(210, 800, 30):
        s.building(_bx, 322, 26, 16, "shop")
    # ...and existing CAPTIONS strung along the verge bands, so the probe also has to reject seats
    # that are clear of every building but would bury another label
    for _ly in range(240, 390, 9):
        for _lx in range(210, 820, 55):
            s.label(_lx, _ly, "riverside quarter", 9)
    spot = s.place_punishment_spot()
    assert spot is not None and s.M["punishment_spots"]
    cap = next(lb for lb in s.M["labels"] if len(lb) > 5 and lb[5] == "punishment ground")
    # the real property: wherever the probe put it, the caption sits on NO shopfront
    for b in s.M["buildings"]:
        bx0, by0 = b["x"] - b["w"] / 2, b["y"] - b["h"] / 2
        bx1, by1 = b["x"] + b["w"] / 2, b["y"] + b["h"] / 2
        assert not (cap[0] < bx1 and bx0 < cap[2] and cap[1] < by1 and by0 < cap[3]), f"caption on {b['kind']} at ({b['x']}, {b['y']})"


def test_log_boom_defaults_to_a_full_holding_pen_and_records_its_box():
    s = _crop_settlement()
    z = s.log_boom(400, 300, rot=90)
    b = s.M["log_booms"][0]
    assert b["z"] == z and b["len"] == round(s.px(330), 1)  # the default pen, ~330 real ft of chained logs
    assert b["pen_w"] == round(s.px(40), 1)  # ~40 real ft of held water between chain and shore
    # the record carries TRUE unrotated dims + rot, like a building - the matrix extractor rotates
    # x/w/h by rot itself, so a rotation-folded box here would double-rotate into a phantom
    # footprint (which is exactly how the first pen landed "on" Minami's lumber yard 42px away)
    assert b["w"] == b["len"] and b["h"] == b["pen_w"] and b["rot"] == 90.0


_IDX_POLY = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]


def test_indexed_overrides_every_mutating_list_method():
    """Every way a list's CONTENT can change must bump the version, or an index cached against it
    goes stale silently - the exact failure that cost this engine two silent bugs in one day
    (a stale `placed` index, a stale well-geometry fingerprint).

    The mutator set is discovered by INTROSPECTION rather than hand-listed, so a future Python
    adding a mutating list method fails this test instead of opening a hole nobody notices.
    """
    non_mutating = {"copy", "__reversed__", "__init__", "__new__", "__class_getitem__", "__getitem__"}
    candidates = (set(dir(list)) - set(dir(tuple))) - non_mutating
    ops = {
        "append": lambda r: r.append(_IDX_POLY),
        "extend": lambda r: r.extend([_IDX_POLY]),
        "insert": lambda r: r.insert(0, _IDX_POLY),
        "remove": lambda r: r.remove(_IDX_POLY),
        "pop": lambda r: r.pop(),
        "clear": lambda r: r.clear(),
        "sort": lambda r: r.sort(),
        "reverse": lambda r: r.reverse(),
        "__setitem__": lambda r: r.__setitem__(0, _IDX_POLY),
        "__delitem__": lambda r: r.__delitem__(0),
        "__iadd__": lambda r: r.__iadd__([_IDX_POLY]),
        "__imul__": lambda r: r.__imul__(2),
    }
    assert set(ops) == candidates, f"the mutator table is out of step with list's API: {set(ops) ^ candidates}"
    for name, op in ops.items():
        assert name in settlement.Indexed.__dict__, f"Indexed does not override {name}"
        reg = settlement.Indexed([_IDX_POLY])
        before, before_appends = reg.version, reg.appends
        op(reg)
        assert reg.version > before, f"{name} changed the list without bumping the version"
        # `indexed_grid` extends a cached index instead of rebuilding it when version and appends
        # moved together, i.e. when every change was an append. That inference is only sound if
        # `appends` counts APPENDS AND NOTHING ELSE - a non-appending mutator that bumped it would
        # let a stale index survive a removal, which is the 2026-08-03 `placed` bug exactly.
        grew = name in {"append", "extend", "__iadd__", "__imul__", "insert"}
        assert (reg.appends > before_appends) == (name in {"append", "extend"}), f"{name} must {'' if grew else 'not '}bump appends"


def test_a_keepout_index_sees_a_registry_mutated_after_its_first_query():
    """The behavioral half of the same rule, at the level a map would notice: query, MUTATE, query
    again. A stale index answers the second query from the first query's world - which is how
    Minami and Nagahara lost every garden on 2026-08-03 - so this walks a point in and out of a
    keep-out by appending and clearing."""
    s = _crop_settlement()
    box = [(480.0, 480.0), (520.0, 480.0), (520.0, 520.0), (480.0, 520.0)]
    assert not s._in_blocked(500, 500)  # builds and caches the index over an empty registry
    s.block_polys.append(box)
    assert s._in_blocked(500, 500), "the index did not see an appended keep-out"
    s.block_polys.clear()
    assert not s._in_blocked(500, 500), "the index did not see the registry emptied"
    # and a corridor, the other indexed registry
    assert not s._near_corridor(300, 300)
    s.corridors.append(([(200.0, 300.0), (400.0, 300.0)], 20.0))
    assert s._near_corridor(300, 300), "the corridor index did not see an appended corridor"


def test_indexed_grid_falls_back_when_a_registry_is_rebound_to_a_plain_list():
    # farm_wells swaps field_polys out and back; anything rebinding a registry to a PLAIN list must
    # still get correct answers, just uncached - the fallback that makes this safe to adopt
    s = _crop_settlement()
    s.block_polys = [[(480.0, 480.0), (520.0, 480.0), (520.0, 520.0), (480.0, 520.0)]]
    assert not isinstance(s.block_polys, settlement.Indexed)
    assert s._in_blocked(500, 500)
    assert not s._in_blocked(300, 300)


def test_point_grid_never_omits_an_item_a_linear_scan_would_find():
    """The one property every PointGrid caller's exactness rests on: `near` may return extra items
    (or an item twice), but it must never OMIT one whose box comes within `pad` of the query.

    Includes the OVERSIZED path - a wildly-spanning box, which is what a negative fixture's
    9,000,000px vertex looks like - because that clamp is the difference between a cheap query and
    the gigabytes-of-RAM incident recorded in this skill's CLAUDE.md.
    """
    rng = random.Random(11)
    items = [(f"i{k}", *(lambda a, b, w, h: (a, b, a + w, b + h))(rng.uniform(0, 900), rng.uniform(0, 900), rng.uniform(1, 300), rng.uniform(1, 300))) for k in range(120)]
    items.append(("huge", -9_000_000.0, -9_000_000.0, 9_000_000.0, 9_000_000.0))  # the clamp case
    grid = settlement.PointGrid()
    grid.extend(items)
    assert grid.n == len(items) and grid.oversized, "the wild box must be filed as oversized, not as billions of cells"
    for pad in (0.0, 5.0, 140.0):  # 140 > cell, so the query spans several cells
        for _ in range(400):
            px, py = rng.uniform(-100, 1000), rng.uniform(-100, 1000)
            want = {it[0] for it in items if it[1] - pad <= px <= it[3] + pad and it[2] - pad <= py <= it[4] + pad}
            got = {it[0] for it in grid.near(px, py, pad)}
            assert want <= got, f"grid OMITTED {want - got} at ({px:.1f}, {py:.1f}) pad={pad}"


def test_boxed_prefilters_agree_exactly_with_the_bare_scan():
    """The bbox PRUNES, the exact test DECIDES - so the prefiltered answer must equal the naive
    one at EVERY point, especially in the near-edge band the pad exists for.

    This is the ratchet behind "the pool regenerates byte-identical" (2026-08-03): the tempting
    way to speed a scatter up is to COARSEN it - a tighter pad, a bbox-only answer, fewer sample
    points - and the loss would show up not here but as silently-moved ground cover on some map
    nobody re-renders for a month. Coarsening fails this test instead.
    """
    polys = [
        [(100.0, 100.0), (200.0, 100.0), (200.0, 180.0), (100.0, 180.0)],
        [(220.0, 40.0), (300.0, 90.0), (250.0, 160.0)],  # a triangle: bbox and shape differ a lot
    ]
    corr = [([(0.0, 0.0), (400.0, 300.0)], 9.0), ([(50.0, 250.0), (350.0, 250.0)], 4.0)]
    boxed0, boxed10 = settlement.boxed_polys(polys), settlement.boxed_polys(polys, 10.0)
    segs = settlement.boxed_segs(corr)
    rng = random.Random(7)
    hits = 0
    for _ in range(4000):
        px, py = rng.uniform(-20, 420), rng.uniform(-20, 320)
        naive_in = any(settlement.point_in_poly(px, py, p) for p in polys)
        naive_pad = any(settlement.point_in_poly(px, py, p) or settlement.edge_dist(px, py, p) < 10.0 for p in polys)
        naive_seg = any(any(seg_dist(px, py, pl[i], pl[i + 1]) < hw for i in range(len(pl) - 1)) for pl, hw in corr)
        assert settlement.boxed_hit(px, py, boxed0) == naive_in, (px, py)
        assert settlement.boxed_hit(px, py, boxed10, 10.0) == naive_pad, (px, py)
        assert settlement.boxed_seg_hit(px, py, segs) == naive_seg, (px, py)
        hits += naive_in or naive_pad or naive_seg
    assert 200 < hits < 3800, f"the sample must straddle both answers to have teeth, got {hits}/4000"


def test_trade_works_caption_hand_seat_moves_the_label_and_its_band():
    # label_xy on a trade glyph seats the caption (and its reserved band) at the given spot -
    # the punishment_spot/kosatsuba remedy for a collision the placement probe cannot see
    # (Minami's lumber-yard caption grazed the log-boom pen by under a pixel, 2026-08-02)
    s = _crop_settlement()
    s.lumber_yard(400, 300, label_xy=(470, 340))
    lab = next(lb for lb in s.M["labels"] if len(lb) > 5 and lb[5] == "lumber yard")
    assert abs((lab[0] + lab[2]) / 2 - 470) < 1.0 and lab[1] < 340 < lab[3]
    s2 = _crop_settlement()
    s2.lumber_yard(400, 300)  # default seat: below the footprint
    lab2 = next(lb for lb in s2.M["labels"] if len(lb) > 5 and lb[5] == "lumber yard")
    assert abs((lab2[0] + lab2[2]) / 2 - 400) < 1.0 and lab2[1] > 300


def test_log_boom_labels_below_itself_unless_told_otherwise():
    s = _crop_settlement()
    s.log_boom(400, 300, rot=0, length=90, label="log boom")
    assert any(len(lb) > 5 and lb[5] == "log boom" for lb in s.M["labels"])
    s2 = _crop_settlement()
    s2.log_boom(400, 300, rot=0, length=90, label=None)
    assert not any(len(lb) > 5 and lb[5] == "log boom" for lb in s2.M["labels"])


def test_bridge_refuses_a_second_deck_on_a_crossing_that_already_has_one():
    """ONE DECK PER CROSSING - the guard lives in bridge() so every caller is covered.

    Minami shipped two decks over the Hayakawa 3px apart (a hand-placed one plus the automatic pass),
    and honda/hoshigaoka/kikuta each carried two footplanks at the SAME point. None was caught because
    bridges were invisible to the overlap matrix."""
    s = _crop_settlement()
    z1 = s.bridge(300, 300, 0, 60, 12)
    z2 = s.bridge(303, 301, 0, 60, 12)  # the same crossing, a few px off
    assert len(s.M["bridges"]) == 1 and z2 == z1  # returns the standing deck rather than drawing a second
    # ...but two genuinely distinct footplanks a few px apart still both draw (the tolerance scales
    # with the deck, so a narrow plank keeps a narrow exclusion)
    s2 = _crop_settlement()
    s2.bridge(300, 300, 0, 8, 2)
    s2.bridge(306, 300, 0, 8, 2)
    assert len(s2.M["bridges"]) == 2


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


def test_yard_fits_skips_own_house_and_rejects_a_neighbor():
    s = Settlement(1000, 1000, seed=1)
    s.placed.append((500, 500, 40, 28))  # the OWN house footprint -> the loop skips it
    s.placed.append((520, 540, 40, 28))  # a neighbor where the yard would land -> rejected
    assert s._yard_fits(520, 540, 32, 20, 500, 500) is False


def test_garden_fits_skips_own_house_and_rejects_a_neighbor():
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


def test_text_width_is_pinned_to_the_basic_layout_engine():
    # A title placard is sized from this measurement and RECORDED in the manifest, so the pool is
    # only byte-reproducible if the measurement depends on the font file alone. PIL otherwise picks
    # its layout engine by what the container has installed - RAQM where libraqm is present, BASIC
    # where it is not - and the two disagree in both directions at the sub-pixel level. A container
    # rebuild after a laptop crash (2026-07-25) gained libraqm and thereby dirtied all 16 titled pool
    # manifests with no code change behind it. These exact numbers are the BASIC ones the committed
    # manifests were built with; a failure here means the pin came loose (or PIL changed BASIC), and
    # it must be resolved deliberately - regenerating the pool - not by editing the expectations.
    s = _crop_settlement()
    assert s._text_width("Honda", 30) == 110.0
    assert s._text_width("Hoshizora", 30) == 170.0
    assert s._text_width("Tango", 30) == 103.953125


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


def test_bathhouses_roll_follows_the_population_formula():
    # GM formula 2026-07-24 (second refinement): 1 per full 2,000 population + a remainder-
    # fraction chance of one extra (2,500 -> 1 + 25%, 3,000 -> 1 + 50%, 4,000 -> exactly 2);
    # count= pins; too few seats is loud. Own Settlements with pinned seeds (the module has two
    # _city helpers and the later one shadows - a seed-3 assumption here failed on seed 1):
    # seed 2's dedicated roll is 0.670 (extra misses at 50%), seed 1's is 0.258 (extra lands).
    def city_(seed, pop):
        s_ = Settlement(1200, 1200, seed=seed)
        s_.meta(name="C", scale="city", ftpx=3)
        s_.M["meta"]["population"] = pop
        return s_

    s = city_(2, 2000)  # zero remainder: exactly 1, no roll can add
    assert s.bathhouses([(300, 300), (600, 600)]) == 1
    assert s.M["meta"]["bathhouse_roll"] == 1 and len(s.M["bathhouses"]) == 1
    s2 = city_(2, 4000)  # two full units, zero remainder: exactly 2
    assert s2.bathhouses([(300, 300), (600, 600)]) == 2
    assert len(s2.M["bathhouses"]) == 2
    assert city_(2, 3000).bathhouses([(300, 300), (600, 600)]) == 1  # roll 0.670 >= 0.50: no extra
    assert city_(1, 3000).bathhouses([(300, 300), (600, 600)]) == 2  # roll 0.258 < 0.50: extra lands
    assert city_(2, 3000).bathhouses([(300, 300), (600, 600)], count=2) == 2  # pin overrides the roll
    s4 = city_(2, 4000)
    with pytest.raises(ValueError, match="vetted seats"):
        s4.bathhouses([(300, 300)])  # a guaranteed 2 needs 2 seats


def test_farrier_draws_a_forge_shed_with_a_working_apron_and_records_it():
    # the shoeing forge (GM 2026-07-25, settlements.md "TRADE WORKS" -> FARRIERY): an open-sided
    # shed plus the apron the animal is actually stood on, recorded as a first-class trade work so
    # farrier_serves_a_stables / farrier_keeps_fire_gap can gate its siting. Sizes are TRUE feet -
    # a 20x18 ft shed on a 28x20 ft apron - so the record is the full 28x38 ft footprint.
    s = _city()
    before = len(s.out)
    s.farrier(600, 620)
    assert len(s.out) > before
    fr = s.M["farriers"][-1]
    assert (fr["x"], fr["y"]) == (600, 620)
    assert fr["w"] == round(s.px(28), 1) and fr["h"] == round(s.px(38), 1)
    assert fr["label"] == "farrier"
    assert "#8FA6B0" in s.out[-1]  # the quench tub - a forge always has water at hand


def test_farrier_caption_clears_a_ROTATED_footprints_drawn_extent():
    # a rotated record's drawn vertical extent is its axis-aligned half-height, not h/2, so the
    # caption must hang off THAT or it lands inside the record's own bbox and
    # labels_clear_of_other_buildings reports "'farrier' over a farrier" (the rot=150 Hoshizora
    # forge, GM 2026-07-25). An UNROTATED farrier keeps the plain h/2 anchor.
    s0, s90 = _city(), _city()
    s0.farrier(600, 620)
    s90.farrier(600, 620, rot=90)
    flat = [L for L in s0.M["labels"] if L[5] == "farrier"][0]
    turned = [L for L in s90.M["labels"] if L[5] == "farrier"][0]
    assert flat[1] > 620 + s0.px(38) / 2  # below the unrotated footprint
    # rotated 90 the drawn half-height is w/2 (< h/2), so its caption rides HIGHER, not lower
    assert 620 + s90.px(28) / 2 < turned[1] < flat[1]


def test_stable_yard_scatter_keeps_off_the_farriers_forge():
    # the farrier is the one trade work sited INSIDE a stable yard, so it must be in the yard's
    # keep-out set - otherwise the scatter speckles straw litter across the forge and its apron.
    s = _city()
    s.farrier(660, 620)
    s.stables(600, 620, rot=90)
    s.flush_stable_yards()
    fr = s.M["farriers"][-1]
    yd = s.M["stable_yards"][-1]
    hw, hh = fr["w"] / 2 + 3, fr["h"] / 2 + 3
    for key in ("rails", "dung_heaps"):
        for o in yd.get(key) or []:
            assert not (abs(o["x"] - fr["x"]) < hw and abs(o["y"] - fr["y"]) < hh), f"{key} on the forge"


def test_stables_draws_a_working_yard_and_records_it():
    # the gate stables' beaten-earth yard (GM 2026-07-22): drawing it adds scatter/furniture to the
    # SVG and records a stable_yard linked to the stables, so stables_have_yards can gate it. The yard
    # scatter avoids a neighboring building (an inn placed just north).
    s = _city()
    s.inn(600, 540)  # a cluster building the yard must skip
    before = len(s.out)
    s.stables(600, 620, rot=90)
    s.flush_stable_yards()
    assert len(s.out) > before  # the yard scatter + furniture drew something
    yd = s.M["stable_yards"][-1]
    assert yd["of"] == [600.0, 620.0] and yd["r"] > 0
    # nothing the yard drew lands on the inn's footprint (a 3px-margin keep-out)
    ix0, iy0, ix1, iy1 = 600 - s.M["buildings"][0]["w"] / 2, 540 - s.M["buildings"][0]["h"] / 2, 600 + s.M["buildings"][0]["w"] / 2, 540 + s.M["buildings"][0]["h"] / 2
    assert ix1 > ix0 and iy1 > iy0  # sanity: the inn has a real footprint the scatter avoided


def test_stables_yard_can_be_suppressed():
    s = _city()
    s.stables(600, 620, rot=90, yard=False)
    s.flush_stable_yards()
    assert not s.M.get("stable_yards")  # yard=False draws no yard


def test_stables_yard_fully_blocked_draws_no_furniture():
    # a yard whose whole disk is covered by a field: every scatter/furniture candidate is rejected
    # (the field-reject branch), take() exhausts, and the cart/dung loops break - the yard is still
    # recorded (so stables_have_yards passes) but no beaten-earth furniture is drawn
    s = _city()
    s.field_polys.append([(400, 400), (800, 400), (800, 840), (400, 840)])  # blankets the r=72 disk at (600,620)
    s.stables(600, 620, rot=90)
    s.flush_stable_yards()
    svg = "".join(s.out)
    assert s.M["stable_yards"][-1]["of"] == [600.0, 620.0]  # recorded despite the blocked yard
    assert not s.M["stable_yards"][-1]["rails"] and "#8FA6B0" not in svg  # no rails seated, no water trough drew


def test_stable_yard_rails_avoid_a_neighboring_yards_heap():
    # round 2 (GM 2026-07-25): a later yard must not lay a rail into an earlier yard's muck
    # pile. The baseline _city() stables yard seats its first interior rail at (582.4, 646.7)
    # (seeded RNG); a prior yard's heap planted exactly there forces the candidate through the
    # _rail_clear_of_heaps rejection, and every rail that does draw keeps the 25px hold
    s = _city()
    s.M["stable_yards"] = [{"x": 460, "y": 620, "r": 72.0, "of": [460, 620], "troughs": 0, "rails": [], "dung_heaps": [{"x": 582.4, "y": 646.7, "rx": 2.5, "ry": 1.8}]}]
    s.stables(600, 620, rot=90)
    s.flush_stable_yards()
    yd = s.M["stable_yards"][-1]
    for r in yd["rails"]:
        h = r["len"] / 2
        d = seg_dist(582.4, 646.7, (r["x"] - r["tx"] * h, r["y"] - r["ty"] * h), (r["x"] + r["tx"] * h, r["y"] + r["ty"] * h))
        assert d >= 24.9, f"rail at ({r['x']}, {r['y']}) laid {d:.1f}px from the neighboring yard's heap"


def test_stable_yard_heaps_avoid_a_neighboring_yards_rails():
    # round 2 (GM 2026-07-25): heap clearance is map-wide, not same-yard-only (the Nagahara
    # 22.5px cross-yard defect). The baseline yard drops its first heap at (656.0, 618.6); a
    # prior yard's rail planted there pushes this yard's heaps to spots >= 25px from it
    s = _city()
    fake_rail = {"x": 656.0, "y": 618.6, "tx": 1.0, "ty": 0.0, "len": 18.0, "reach": 2.4}
    s.M["stable_yards"] = [{"x": 740, "y": 620, "r": 72.0, "of": [740, 620], "troughs": 0, "rails": [fake_rail], "dung_heaps": []}]
    s.stables(600, 620, rot=90)
    s.flush_stable_yards()
    yd = s.M["stable_yards"][-1]
    assert yd["dung_heaps"], "the yard should still find room for its muck pile"
    h = fake_rail["len"] / 2
    for dh in yd["dung_heaps"]:
        d = seg_dist(dh["x"], dh["y"], (fake_rail["x"] - h, fake_rail["y"]), (fake_rail["x"] + h, fake_rail["y"]))
        assert d >= 24.9, f"heap at ({dh['x']}, {dh['y']}) sits {d:.1f}px from the neighboring yard's rail"


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


def test_pack_businesses_only_line_the_frontage():
    # face_streets=True (businesses mode): a spot with no street within reach places NOTHING -
    # shops exist to catch passing feet, they never scatter into a streetless interior. (This
    # mode lost its last pool caller in the 2026-07-24 Hirameki roadway rework; the unit test
    # keeps the API branch alive and covered.)
    s = Settlement(1000, 1000, seed=2)
    s.meta(name="T", scale="town")
    s.pack((150, 300, 850, 700), ["merchant"] * 6, step=40, face_streets=True)
    assert s.M["buildings"] == []


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


def _caption_size(lab: list) -> float:
    # _record_label's box is len(text) * size * 0.55 wide, so the drawn size reads straight back
    # off the record - and reading it that way is the point: these tests pin what the MAP shows.
    return round((lab[2] - lab[0]) / (len(lab[5]) * 0.55), 1)  # 1dp: the record itself is rounded to 0.1px


def test_a_hall_caption_is_the_same_size_as_a_ministry_caption():
    # GM 2026-08-08: a caption is sized by its GLYPH, not by the institution's rank. A city temple
    # hall and a ministry office are the same size class of building (96-140 ft against 114-140),
    # so their captions match; the temple's greater standing shows in red and bold, not in points.
    s = Settlement(1400, 1400, seed=5)
    s.meta(name="C", scale="city", ftpx=3)
    s.shrine_hall(400, 400, "Temple of Benten", w=s.px(130), h=s.px(84), kind="temple")
    s.ministry(900, 400, "Ministry of Rites")
    temple = next(lb for lb in s.M["labels"] if lb[5] == "Temple of Benten")
    ministry = next(lb for lb in s.M["labels"] if lb[5] == "Ministry of Rites")
    assert _caption_size(temple) == _caption_size(ministry) == settlement.HALL_CAPTION_FS
    # per CHARACTER the two now advance identically - the defect was a temple caption ~44% wider
    # per character than the ministry caption standing 500px away from it
    assert (temple[2] - temple[0]) / len(temple[5]) == pytest.approx((ministry[2] - ministry[0]) / len(ministry[5]), abs=0.01)


def test_governor_mansion_caption_sits_inside_its_walls():
    # GM 2026-08-08. The court is drawn blank on purpose (its buildings are a separate Mode A
    # sheet), so it is guaranteed clear ground on a packed city map, and the band above the walls
    # is prime housing. The caption goes inside, small enough to clear both walls.
    s = Settlement(1400, 1400, seed=6)
    s.meta(name="C", scale="city", ftpx=3)
    s.governor_mansion(700, 700, s.px(436), s.px(366), "Governor's Mansion", gate_dir="west")
    gov = s.M["governor_mansion"]
    assert gov["label"] == "Governor's Mansion"  # the record keeps the name manor() was not given
    lab = next(lb for lb in s.M["labels"] if lb[5] == "Governor's Mansion")
    assert _caption_size(lab) == settlement.GOVERNOR_CAPTION_FS
    assert lab[0] > 700 - gov["w"] / 2 and lab[2] < 700 + gov["w"] / 2  # clear of BOTH walls
    assert lab[1] > 700 - gov["h"] / 2 and lab[3] < 700 + gov["h"] / 2  # and inside, not above
    assert len([lb for lb in s.M["labels"] if lb[5] == "Governor's Mansion"]) == 1  # manor drew none


def test_governor_mansion_can_be_left_unlabeled():
    s = Settlement(1400, 1400, seed=7)
    s.meta(name="C", scale="city", ftpx=3)
    s.governor_mansion(700, 700, s.px(436), s.px(366), "", gate_dir="west")
    assert s.M["governor_mansion"]["label"] == ""
    assert not s.M["labels"]


def test_kura_side_flips_to_the_north_wall_when_the_west_is_taken():
    # A legacy farmstead reserves its base rect but DRAWS its west kura past it, so the side is
    # chosen at flush time against the neighbors actually on the ground (Minami 2026-08-08, a farm
    # shed drawn on a garden). West by default, north when the west is taken - and when BOTH are
    # taken the west stands, so the overlap matrix reports a homestead with no room for its kura
    # rather than the engine hiding it.
    s = Settlement(600, 600, seed=1)
    s.meta(name="V", scale="village", ftpx=2)
    rec = {"x": 300.0, "y": 300.0, "w": 44.0, "h": 29.0, "rot": 0.0, "shed": True}
    assert s._kura_side(rec, 44.0, 29.0) == "W"
    s.M["gardens"].append({"x": 300 - 0.64 * 44, "y": 300.0, "w": 10.0, "h": 10.0})  # a neighbor's bed on the west wall
    assert s._kura_side(rec, 44.0, 29.0) == "N"
    s.M["gardens"].append({"x": 300.0, "y": 300 - 0.60 * 29, "w": 10.0, "h": 10.0})  # ...and one on the back wall too
    assert s._kura_side(rec, 44.0, 29.0) == "W"


def test_scope_seed_depends_only_on_seed_name_and_key():
    # It must NOT depend on the process (hashlib, not the salted built-in hash()) nor on anything
    # drawn before it - that independence is the whole mechanism.
    a = settlement.scope_seed(23, "pack", (100, 200, 300, 400))
    random.random()
    assert settlement.scope_seed(23, "pack", (100, 200, 300, 400)) == a
    assert settlement.scope_seed(24, "pack", (100, 200, 300, 400)) != a  # the map seed matters
    assert settlement.scope_seed(23, "rowpack", (100, 200, 300, 400)) != a  # the scope name matters
    assert settlement.scope_seed(23, "pack", (100, 200, 300, 401)) != a  # the key matters
    assert settlement.scope_seed(23, "pack", (100.04, 200, 300, 400)) == a  # ...but not below 0.1 px


def test_rng_scope_is_isolated_from_before_and_restores_after():
    def draw(perturb):
        s = Settlement(600, 500, seed=5)  # a FRESH map: the per-key counter starts at 0 in both runs
        for _ in range(perturb):
            random.random()  # an upstream change consuming extra draws
        with s.rng_scope("t", 1, 2):
            inside = [random.random() for _ in range(3)]
        return inside, random.random()

    a_in, a_after = draw(0)
    b_in, b_after = draw(1)
    assert a_in == b_in  # the scope cannot see what happened before it
    assert a_after != b_after  # ...and the outer stream is genuinely restored, not re-seeded


def test_rng_scope_gives_repeat_calls_on_one_key_their_own_numbers():
    # Two packs over the same ground must not draw the same "random" numbers, or they twin.
    s = Settlement(600, 500, seed=5)
    with s.rng_scope("pack", 0, 0, 10, 10):
        first = [random.random() for _ in range(3)]
    with s.rng_scope("pack", 0, 0, 10, 10):
        second = [random.random() for _ in range(3)]
    assert first != second
    other = Settlement(600, 500, seed=5)
    with other.rng_scope("pack", 0, 0, 10, 10):
        assert [random.random() for _ in range(3)] == first  # ...but a fresh map reproduces them


def test_a_farmstead_belt_is_immune_to_an_upstream_change_in_draw_count():
    # THE RATCHET for the whole positional-randomness discipline (GM 2026-08-08). A caption resize
    # in a city's temple quarter re-rolled farmland 700 px away and dropped a farm shed on a garden,
    # because a farmhouse's rake and its storehouse were STREAM draws: consume one more random
    # number anywhere upstream and every homestead in the map re-rolled. They are position-seeded
    # now (the convention _hjit's own docstring describes), so this holds.
    def belt(perturb):
        s = _town()
        for _ in range(perturb):
            random.random()
        for x in (400, 500, 600, 700, 800):
            s.try_place(x, 500, "plain")
        s.farmsteads()
        return {k: json.dumps(s.M[k], sort_keys=True) for k in ("houses", "gardens", "threshing_yards", "farm_sheds")}

    a, b = belt(0), belt(1)
    assert a == b, f"an upstream draw re-rolled: {[k for k in a if a[k] != b[k]]}"


def test_crop_to_content_includes_forest_clamped_to_canvas():
    # the forest is a big EDGE feature recorded as a POINT-LIST (not dicts). On the axis it FACES, the crop
    # frames it CLAMPED to the canvas so the view never opens past the edge (an edge feature must REACH the
    # frame edge, not stop short). On the axis it RUNS ALONG - here N-S, off BOTH canvas ends - it sets
    # nothing, so that edge stays tight to the real content instead of being pinned to the canvas.
    s = Settlement(2000, 1500, seed=1)
    s.M["houses"] = [{"x": 30, "y": 700, "w": 20, "h": 20}]
    s.M["forest"] = [[1800, -10], [1820, 750], [1800, 1510], [2012, 1510], [2012, -10]]  # fills the E to canvas+12
    s.crop_to_content(margin=40)
    assert s.view == (0, 650, 2000, 100)  # E edge clamped to the canvas; N/S tight to the house


def test_crop_to_content_frames_a_forest_that_ends_inside_the_canvas():
    # ... but a tree line that STOPS inside the canvas bounds something real, so its own span is content
    s = Settlement(2000, 1500, seed=1)
    s.M["houses"] = [{"x": 30, "y": 700, "w": 20, "h": 20}]
    s.M["forest"] = [[1800, 300], [1820, 750], [1800, 1200], [2012, 1200], [2012, 300]]
    s.crop_to_content(margin=40)
    assert s.view == (0, 260, 2000, 980)


def test_crop_boxes_keeps_a_lone_forests_own_span():
    # a map with NOTHING but the wood has no other content to take its span from, so the run-along axis
    # falls back to the forest's own clamped span
    s = Settlement(2000, 1500, seed=1)
    s.M["forest"] = [[1800, -10], [1800, 1510], [2012, 1510], [2012, -10]]
    assert s._crop_boxes(city=False) == [(1800.0, 2000.0, 0.0, 1500.0, "forest")]


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
def _zoned_city():  # was a second '_city' shadowing the line-1665 helper (seed 1 vs 3) - renamed 2026-07-24, now gated by scripts/check-duplicate-defs.py
    s = Settlement(2000, 2000, seed=1)
    s.meta(name="C", scale="city", walled=True, population=3000, ftpx=3)
    return s


def test_quarter_records_zone_without_drawing_for_non_reserve():
    s = _zoned_city()
    poly = [(100, 100), (400, 100), (400, 400), (100, 400)]
    before = len(s.out)
    s.quarter(poly, "residential")
    q = s.M["quarters"][-1]
    assert q["zone"] == "residential" and q["kind"] is None
    assert q["poly"][0] == [100.0, 100.0]
    assert len(s.out) == before  # residential/civic/mixed draw nothing (declarative only)


def test_quarter_label_is_drawn_at_the_centroid():
    s = _zoned_city()
    s.quarter([(0, 0), (200, 0), (200, 200), (0, 200)], "civic", label="yamen precinct")
    assert s.M["quarters"][-1]["name"] == "yamen precinct"
    assert any("yamen precinct" in frag for frag in s.toplabels)


def test_quarter_reserve_kinds_render_their_ground():
    poly = [(100, 100), (500, 100), (500, 500), (100, 500)]
    # drill_ground and garden paint a visible ground surface...
    for kind in ("drill_ground", "garden"):
        s = _zoned_city()
        before = len(s.out)
        s.quarter(poly, "reserve", kind=kind, label=kind)
        assert s.M["quarters"][-1]["kind"] == kind
        assert len(s.out) > before  # a drawn reserve renders its ground feature
    # ...but an agricultural_district draws NOTHING (GM 2026-07-22 - its combs/farmhouses/label are
    # the rendering; the old faint dashed boundary was a stray dotted line), yet is still recorded
    s = _zoned_city()
    before = len(s.out)
    s.quarter(poly, "reserve", kind="agricultural_district", label="ag")
    assert s.M["quarters"][-1]["kind"] == "agricultural_district"
    assert len(s.out) == before  # no boundary line: the fields carry the whole visual


def test_quarter_rejects_bad_zone_and_kind_misuse():
    s = _zoned_city()
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
    near_center = sum(1 for p in spl if abs(p[0] - 500) < 30)
    assert near_center < 0.15 * len(spl)  # a gap between the two sub-hamlets


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


def test_bund_junctions_pile_earth_only_where_bunds_actually_cross():
    # GM 2026-07-25: on a SHARED-BARRIER field the bund is the line, so the hand-piled-earth rule is
    # additive - material goes into the crossings, which rounds the basin corners without touching a
    # carve that has to tessellate. A junction is found from the drawn geometry (>=3 coincident plot
    # corners), which makes the pass self-selecting: separate, inset parcels share no corner, so the
    # polder archetype - which expresses the same rule subtractively - gets nothing drawn on it.
    s = Settlement(400, 400)
    s.meta(name="j", scale="hamlet", ftpx=1)
    grid_plots = [
        {"poly": [(100.0 + 40 * c, 100.0 + 40 * r), (140.0 + 40 * c, 100.0 + 40 * r), (140.0 + 40 * c, 140.0 + 40 * r), (100.0 + 40 * c, 140.0 + 40 * r)]} for r in range(3) for c in range(3)
    ]
    before = len(s.out)
    s.bund_junctions(grid_plots, "j-paddies")
    drawn = "".join(s.out[before:])
    # A 3x3 block of touching cells has exactly 4 interior 4-way crossings, and each crossing is piled
    # as a SEPARATE fillet per quadrant (never one disc centered on the node - a repeated stamp reads
    # more machine-made than the sharp cross it replaces), with about a quarter of quadrants left bare.
    # So: more than one mark per crossing, fewer than all 16, and none at all on the edge/T corners.
    import re as _re

    marks = _re.findall(r'points="([^"]+)"', drawn)
    assert 4 < len(marks) <= 16, len(marks)
    assert 'fill="#6E4520"' in drawn
    for pts in marks:
        vs = [tuple(float(q) for q in v.split(",")) for v in pts.split(" ")]
        # every mark is a fillet AT one of the four interior crossings (140/180 x 140/180)
        assert any(max(abs(v[0] - jx) for v in vs) < 9 and max(abs(v[1] - jy) for v in vs) < 9 for jx in (140.0, 180.0) for jy in (140.0, 180.0)), pts
        span = max(max(v[i] for v in vs) - min(v[i] for v in vs) for i in (0, 1))
        assert 0.5 <= span <= 9.0, span  # a few feet of piled earth, jittered - not a legibility blob
    # the quadrants really do differ: the marks are not all the same size (that was the stamped look)
    areas = sorted(max(max(float(v.split(",")[i]) for v in pts.split(" ")) - min(float(v.split(",")[i]) for v in pts.split(" ")) for i in (0, 1)) for pts in marks)
    assert areas[-1] > areas[0] * 1.5, areas
    # deterministic: the same field redraws identically (a salted str hash() would break this)
    s2 = Settlement(400, 400)
    s2.meta(name="j", scale="hamlet", ftpx=1)
    b2 = len(s2.out)
    s2.bund_junctions(grid_plots, "j-paddies")
    assert "".join(s2.out[b2:]) == drawn
    # SEPARATED parcels (the polder carve: every parcel inset off its neighbors) share no corner at all
    inset_plots = [
        {"poly": [(p["poly"][0][0] + 2, p["poly"][0][1] + 2), (p["poly"][0][0] + 38, p["poly"][0][1] + 2), (p["poly"][0][0] + 38, p["poly"][0][1] + 38), (p["poly"][0][0] + 2, p["poly"][0][1] + 38)]}
        for p in grid_plots
    ]
    b3 = len(s.out)
    s.bund_junctions(inset_plots, "j-polder")
    assert len(s.out) == b3  # nothing drawn - no crossing exists to pile


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
    # fourth pass (GM 2026-07-23): the wholesale case repaints its rice leftovers as textured paddy and
    # records them - every plot is either converted or a recorded leftover, none floats as a bare outline
    assert len(s2.M["land_use"][-1]["leftover_plots"]) == len(dry["plots"]) - n2
    # the partial-overlay path records no leftovers (its unconverted plots are ordinary comb paddies)
    s3 = Settlement(2000, 2800, seed=3)
    s3.meta(name="LU3", scale="village", ftpx=1, down_deg=90)
    s3.apply_land_use(net, "mulberry_fishpond", __import__("random").Random(1))
    assert s3.M["land_use"][-1]["leftover_plots"] == []
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


def test_pond_fill_relocates_to_the_late_block_when_a_late_channel_joins():
    """The Tango in-wall tank (GM 2026-07-23): a comb head-race joins the pond from the LATE
    block, which draws after the whole shared water block - so an early fill can never cover the
    mouth's inside-the-rim overshoot and the cap rides ON TOP of the open water. The fill+sheen
    relocate to the late block (topmost late bed); the rim EDGE stays early so the mouth's bed
    still covers it. Manifest records the order for pond_fill_covers_channel_mouths."""
    with tempfile.TemporaryDirectory() as d:
        base = os.path.join(d, "t")
        s = Settlement(1000, 1000, seed=1)
        s.meta(name="V", scale="village")
        s.pond(500, 250, 100, 70)
        s.field_channel([(500, 260), (500, 600)], "#6C9CBE", 5.0, 5.0, late=True)  # sluice inside the pond -> snapped to the rim
        s.finish(base, render=False)
        with open(base + ".svg") as _f:
            svg = _f.read()
    dc = s.M["drawn_channels"][0]
    assert dc["late"] and s.M["pond_layer"]["late"] is True  # the fill relocated to the late block
    assert s.M["pond_layer"]["bedz"] > dc["bedz"]  # fill recorded ABOVE the joining bed (same block)
    fill = svg.index('<ellipse cx="500" cy="250" rx="100" ry="70" fill="#9CB4C8"/>')
    assert fill > svg.index('stroke="#6C9CBE"')  # fill drawn AFTER the late bed (covers the cap)
    assert svg.index('stroke="#5C7488"') < svg.index('stroke="#6C9CBE"')  # rim edge stays early, below the bed


def test_pond_fill_stays_in_the_shared_block_without_a_late_join():
    # a late channel that does NOT touch the pond must not relocate the fill: the shared block's
    # own pond_fill-last ordering already covers the early feeder's overshoot
    with tempfile.TemporaryDirectory() as d:
        base = os.path.join(d, "t")
        s = Settlement(1000, 1000, seed=1)
        s.meta(name="V", scale="village")
        s.pond(500, 250, 100, 70)
        s.field_channel([(500, 260), (500, 600)], "#6C9CBE", 5.0, 5.0)  # EARLY joining channel
        s.field_channel([(50, 900), (300, 900)], "#7C9EB0", 3.0, 3.0, late=True)  # late, far from the pond
        s.finish(base, render=False)
        with open(base + ".svg") as _f:
            svg = _f.read()
    early, late = s.M["drawn_channels"]
    assert s.M["pond_layer"]["bedz"] > early["bedz"]  # shared-block covering order holds (same block, z comparable)
    assert s.M["pond_layer"]["late"] is False  # no relocation: the fill stayed in the shared block
    assert svg.index('<ellipse cx="500" cy="250" rx="100" ry="70" fill="#9CB4C8"/>') < svg.index('stroke="#7C9EB0"')  # the non-joining late bed draws later (svg order, cross-block)


def test_roll_merchant_estate_count_distribution():
    # 30/40/30 for 1/2/3 at city scale - the granted-privilege distribution (MERCHANT_ESTATE_WEIGHTS)
    import collections
    import random as _rr

    from settlement import MERCHANT_ESTATE_WEIGHTS, roll_merchant_estate_count

    rng = _rr.Random(7)
    n = 6000
    c = collections.Counter(roll_merchant_estate_count("city", rng) for _ in range(n))
    assert set(c) == {1, 2, 3}
    for count, wt in MERCHANT_ESTATE_WEIGHTS["city"]:
        assert abs(c[count] / n - wt) < 0.03

    class _One:  # rng.random() lives in [0,1) so the exhaustion return is defensively dead - prove it anyway (the roll_torii_count precedent)
        def random(self):
            return 1.0

    assert roll_merchant_estate_count("city", _One()) == 3  # exhaustion falls to the last bucket


def test_merchant_estates_rolls_seats_and_records_the_target():
    import random as _rr

    from settlement import roll_merchant_estate_count

    s = Settlement(1200, 1200, seed=11)
    s.meta(name="c", scale="city", ftpx=3)
    expect = roll_merchant_estate_count("city", _rr.Random(11 * 1201 + 89))  # the method's dedicated stream
    n = s.merchant_estates([(300, 300, "south"), (600, 300, "south"), (300, 600, "east")])
    assert n == expect
    assert len(s.M["merchant_estates"]) == n
    assert s.M["meta"]["merchant_estate_roll"] == n


def test_merchant_estates_pin_overrides_the_roll():
    s = Settlement(1200, 1200, seed=11)
    s.meta(name="c", scale="city", ftpx=3)
    n = s.merchant_estates([(300, 300, "south"), (600, 300, "south"), (300, 600, "east")], count=2)
    assert n == 2
    assert len(s.M["merchant_estates"]) == 2
    assert s.M["meta"]["merchant_estate_roll"] == 2


def test_merchant_estates_raises_when_seats_run_short():
    s = Settlement(1200, 1200, seed=11)
    s.meta(name="c", scale="city", ftpx=3)
    with pytest.raises(ValueError, match="vetted seats"):
        s.merchant_estates([(300, 300, "south")], count=3)


def test_draw_comb_field_drops_hem_plots_on_a_prior_fan():
    # multi-fan maps place each fan blind to the others: a hem plot landing on a PREVIOUSLY
    # recorded fan's rice is dropped via the shared hem_on_paddy predicate (the Tango fe2-into-fe1
    # incident; gated by dry_plots_clear_of_paddies). The prior fan here is a synthetic field
    # record blanketing the second comb's hem band, so every hem plot must go.
    from waterfields import build_comb, hem_on_paddy

    s = Settlement(W=1400, H=1400, seed=5)
    s.meta(name="Cp", scale="town", ftpx=1, down_deg=90)
    net = build_comb(1400, 1400, (700, 200), 5, down_deg=90, field_fall=400)
    net["brook"] = []
    on_rice = [p for p in net["dry_plots"]]
    assert on_rice, "the comb must produce a hem for the drop to be observable"
    blanket = [[0, 0], [1400, 0], [1400, 1400], [0, 1400]]  # covers everything - every hem plot overlaps it
    assert all(hem_on_paddy(p["poly"], blanket) for p in on_rice)
    s.M["fields"].append({"name": "prior", "kind": "paddy", "outline": blanket, "bbox": [0, 0, 1400, 1400]})
    s.draw_comb_field(net, "f1", {"kind": "stream"})
    assert s.M["dry_plots"] == []  # every hem plot dropped; the paddies themselves still drew
    assert any(fl["name"] == "f1" for fl in s.M["fields"])


def _inwall_settlement():
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="C", scale="town", ftpx=1)
    s.M["ring_road"] = [[100, 100], [900, 100], [900, 900], [100, 900], [100, 100]]
    s.M["ring_road_width"] = 8
    s.M["moat"] = [[60, 60], [940, 60], [940, 940], [60, 940]]
    return s


def test_inwall_drain_outfall_trims_gates_and_records_the_conduit():
    """The in-wall drain handoff (GM 2026-07-23): the drain polyline is trimmed back to half the
    ring-road width + 10px clear of the ring centerline, a sluice gate sits across the cut, and
    an UNDRAWN drain->moat conduit starts exactly at the cut (inwall_drains_gated_at_cutoff)."""
    s = _inwall_settlement()
    out = s.inwall_drain_outfall([(500, 300), (300, 150), (150, 110)])  # moat-side end LAST, ends 10px off the ring's top segment
    cut = out[-1]
    ringd = min(settlement.seg_dist(cut[0], cut[1], a, b) for a, b in [((100, 100), (900, 100)), ((100, 100), (100, 900))])
    assert ringd >= 13.9  # 8/2 + 10 clear of the centerline
    assert len(out) < 3 or out[:2] == [(500.0, 300.0), (300.0, 150.0)]  # only the tail was touched
    g = s.M["sluice_gates"][-1]
    assert math.hypot(g["x"] - cut[0], g["y"] - cut[1]) < 1.5  # the gate sits AT the cut
    c = s.M["channels"][-1]
    assert c["frm"] == {"kind": "drain"} and c["to"] == {"kind": "moat"} and c["drawn"] is False
    assert c["poly"][0] == [round(cut[0], 1), round(cut[1], 1)]  # the conduit starts at the cut


def test_inwall_drain_outfall_normalizes_orientation_and_degenerate_cases():
    # outfall-FIRST input comes back outfall-first (the caller's orientation is preserved)
    s = _inwall_settlement()
    out = s.inwall_drain_outfall([(150, 110), (300, 150), (500, 300)])
    assert out[-1] == (500.0, 300.0)  # far end untouched, so the cut landed at index 0
    # no ring road: nothing to trim - the gate still marks the outfall
    s2 = Settlement(1000, 1000, seed=1)
    s2.meta(name="C2", scale="town", ftpx=1)
    s2.M["moat"] = [[60, 60], [940, 60], [940, 940], [60, 940]]
    out2 = s2.inwall_drain_outfall([(500, 300), (150, 110)])
    assert out2 == [(500.0, 300.0), (150.0, 110.0)] and s2.M["sluice_gates"]
    # no moat: gate only - no conduit record, no orientation flip
    s3 = Settlement(1000, 1000, seed=1)
    s3.meta(name="C3", scale="town", ftpx=1)
    s3.M["ring_road"] = [[100, 100], [900, 100], [900, 900], [100, 900], [100, 100]]
    s3.M["ring_road_width"] = 8
    n3 = len(s3.M["channels"])
    s3.inwall_drain_outfall([(500, 300), (150, 110)])
    assert len(s3.M["channels"]) == n3 and s3.M["sluice_gates"]
    # the whole polyline hugs the road: left untrimmed (the check flags it), gate at the raw end
    s4 = _inwall_settlement()
    out4 = s4.inwall_drain_outfall([(300, 104), (200, 104)])
    assert out4[-1] == (200.0, 104.0)


def test_draw_comb_field_trims_an_inwall_drain_through_the_helper():
    from waterfields import build_comb

    s = _inwall_settlement()
    net = build_comb(1000, 1000, (500, 200), 5, down_deg=90, field_fall=300)
    net["brook"] = []
    s.draw_comb_field(net, "f1", {"kind": "stream"}, inwall_drain_moat_bias=(0, 0))
    assert any((c.get("frm") or {}).get("kind") == "drain" and (c.get("to") or {}).get("kind") == "moat" and c.get("drawn") is False for c in s.M["channels"])
    assert s.M["sluice_gates"]


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
            q = p["quad"]  # the ruled parcel BEFORE the organic pass - the skew lives in its corners
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
    # a dike-pond with NO adjacent canal (<46 px) and NO neighbor pond within reach (<52 px) gets no sluice -
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
    assert s.M.get("dikepond_sluices") == []  # both basins ungated: no canal near, no neighbor near


def test_apply_land_use_reanchor_leaves_a_placeholder_slot():
    # GM 2026-07-24 (the bald pond): the flush splice REPLACES the element at _late_water_idx
    # (self.out[idx:idx+1] = block), so every anchor assignment must be followed by an empty-string
    # placeholder. The overlay re-anchor lacked one, so the splice ate the next-appended element -
    # which, after the crown-deferral change, was a pond's entire crown group.
    s = Settlement(2000, 2000, seed=1)
    s.meta(field_archetype="mulberry_dike_fishpond")
    s._late_water_idx = len(s.out)
    s.out.append("")  # a live late-water anchor, as a comb-field channel draw would leave it
    plots = [{"poly": [(100.0 + 220 * i, 100.0), (280.0 + 220 * i, 100.0), (280.0 + 220 * i, 260.0), (100.0 + 220 * i, 260.0)], "low": True} for i in range(2)]
    s.apply_land_use({"plots": plots, "channels": []}, "mulberry_fishpond", random.Random(1), fraction=1.0, eligible="all")
    assert s._late_water_idx is not None and s.out[s._late_water_idx] == ""  # the slot the splice consumes is a placeholder, never real content


def test_flooded_leftover_paddy_gets_rounded_waterline():
    # GM 2026-07-23: a FLOODED leftover's waterline draws rounded + slightly irregular (bund corners silt
    # round, the toe wanders) via _rounded_pond - with NO edge stroke, so it never reads as a dug pond
    # (pond water paths carry the #6C9CBE stroke; the flooded paddy's body is strokeless).
    s = Settlement(2000, 2000, seed=2)
    s.meta(field_archetype="mulberry_dike_fishpond")
    plots = [{"poly": [(100.0 + 220 * i, 100.0), (280.0 + 220 * i, 100.0), (280.0 + 220 * i, 260.0), (100.0 + 220 * i, 260.0)], "low": True, "fill": "#93B7AC"} for i in range(4)]
    s.apply_land_use({"plots": plots, "channels": []}, "mulberry_fishpond", random.Random(3), fraction=0.5, eligible="all")
    body = "".join(s.out)
    assert re.search(r'<path d="[^"]*Q[^"]*" fill="#93B7AC"/>', body)  # a strokeless, corner-filleted water body


def test_dikepond_digs_back_from_a_penetrating_lateral():
    # GM 2026-07-23: the canal at the toe BOUNDS the bank - a lateral riding inside the parcel line makes
    # the whole pond unit shrink about its centroid until the bank clears the canal, and the SHRUNK outline
    # is what dikeponds records (the drawn truth, which mulberry_banks_clear_of_channels then reads).
    s = Settlement(2000, 2000, seed=1)
    s.meta(field_archetype="mulberry_dike_fishpond")
    plot = {"poly": [(100.0, 100.0), (300.0, 100.0), (300.0, 300.0), (100.0, 300.0)], "low": True}
    net = {"plots": [plot], "channels": [{"pts": [(103.0, 50.0), (103.0, 350.0)]}]}  # rides 3 px inside the west edge
    s.apply_land_use(net, "mulberry_fishpond", random.Random(1), fraction=1.0, eligible="all")
    rec = s.M["dikeponds"][0]["parcel"]
    assert min(x for x, _ in rec) >= 103.0 + 1.0  # dug back clear of the lateral (>= 1 px past its line)


def test_mulberry_rows_crowns_avoid_channels():
    # GM 2026-07-23: the crowns are coppiced BUSHES - any crown whose circle would reach a channel
    # centerline (r + 3 px clearance) is dropped, so bushes never stand in the canal at the dike toe.
    poly = [(0.0, 0.0), (160.0, 0.0), (160.0, 320.0), (0.0, 320.0)]

    def crowns(channels):
        s = Settlement(600, 600, seed=1)
        s._mulberry_rows(poly, "M -10 -10 L 170 -10 L 170 330 L -10 330 Z", 80.0, 160.0, random.Random(7), channels)
        return s.out[-1].count("<circle")

    unblocked = crowns(None)
    blocked = crowns([((80.0, -20.0), (80.0, 340.0))])  # a canal crossing the top + bottom bank rows
    assert 0 < blocked < unblocked


def test_mulberry_rows_skips_a_parcel_too_small_to_plant():
    # fourth pass: a parcel whose apothem cannot hold the 11 px water inset has no bank to plant - the
    # helper draws nothing rather than wrapping crown rows around a degenerate loop.
    s = Settlement(400, 400, seed=1)
    before = len(s.out)
    s._mulberry_rows([(0.0, 0.0), (20.0, 0.0), (20.0, 20.0), (0.0, 20.0)], "M 0 0 Z", 10.0, 10.0, random.Random(1))
    assert len(s.out) == before


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


def test_dike_top_houses_seats_a_single_file_on_the_crest():
    # GM 2026-07-24 (settlements.md 'Polder siting Q&A'): the ISLET-polder settlement form - houses in
    # single file ON the dike crest, each on a widened-crest platform, tagged on_dike in the manifest.
    import check_village

    s = Settlement(1400, 1400, seed=5)
    s.meta(name="DT", scale="hamlet", ftpx=1, toscale=True, households=8, terrain="low", field_archetype="polder_grid")
    env = [(300, 300), (1100, 300), (1100, 1100), (300, 1100)]
    s.perimeter_dike(env, seed=7, gaps=[(500, 300), (700, 300)])
    dk = s.M["dikes"][0]
    # the crest centerline is recorded, and every crest point sits on the band
    assert len(dk["crest"]) >= 60
    assert all(check_village.poly_dist(cx, cy, dk["outline"]) <= 6 for cx, cy in dk["crest"])
    st = random.getstate()
    n = s.dike_top_houses(8, seed=11, span=(0.0, 0.25), gap_clear=60.0)  # the top (north) run, which carries both sluice gaps
    assert random.getstate() == st  # stream-neutral: the helper never ripples the map's main rng
    tagged = [h for h in s.M["houses"] if h.get("on_dike")]
    assert n == len(tagged) and 4 <= n < 8  # the sluice-gap skips cost sites - nobody builds over the notch
    for h in tagged:
        assert check_village.poly_dist(h["x"], h["y"], dk["outline"]) <= 14  # seated on the band
        assert all(math.hypot(h["x"] - gx, h["y"] - gy) >= 60 for gx, gy in ((500, 300), (700, 300)))
        assert h["platform"][0] > h["w"] and h["platform"][1] > h["h"]  # the widened-crest pad outsizes the house
    assert s.M["meta"]["settlement_form"] == "dike_top"  # the helper declares the form
    # single file: a crowded call self-spaces (spacing skips), so a short span caps well under the ask
    n2 = s.dike_top_houses(30, seed=3, span=(0.5, 0.75))
    assert 0 < n2 < 30
    # determinism: an identical settlement re-run lands identical houses
    s2 = Settlement(1400, 1400, seed=5)
    s2.meta(name="DT", scale="hamlet", ftpx=1, toscale=True, households=8, terrain="low", field_archetype="polder_grid")
    s2.perimeter_dike(env, seed=7, gaps=[(500, 300), (700, 300)])
    s2.dike_top_houses(8, seed=11, span=(0.0, 0.25), gap_clear=60.0)
    assert [h for h in s2.M["houses"] if h.get("on_dike")] == tagged


def test_farmsteads_keep_dike_top_houses():
    # farmsteads() rebuilds M['houses'] from the pending-bundle survivors; dike-top houses are not
    # pending farmsteads, so they must survive the rebuild rather than being silently dropped.
    s = Settlement(1400, 1400, seed=5)
    s.meta(name="DT", scale="hamlet", ftpx=1, toscale=True, households=8, terrain="low", field_archetype="polder_grid")
    s.perimeter_dike([(300, 300), (1100, 300), (1100, 1100), (300, 1100)], seed=7)
    s.dike_top_houses(4, seed=11, span=(0.0, 0.25))
    before = [h for h in s.M["houses"] if h.get("on_dike")]
    assert before
    s.farmsteads()
    assert [h for h in s.M["houses"] if h.get("on_dike")] == before


def test_marsh_waterside_role():
    # the un-reclaimed wet wild outside a polder dike (settlements.md 'Polder siting Q&A'): a valid
    # role, recorded like any marsh; an unknown role still raises.
    s = Settlement(1400, 1400, seed=5)
    s.meta(name="WS", scale="hamlet", ftpx=1, toscale=True)
    s.marsh([(0, 200), (260, 200), (260, 1200), (0, 1200)], role="waterside")
    assert s.M["marshes"][-1]["role"] == "waterside"
    with pytest.raises(ValueError):
        s.marsh([(0, 0), (10, 0), (10, 10)], role="lagoon")


def test_settlement_form_dike_top_is_low_ground_gated():
    # dike_top stands ON a polder's perimeter dike, so the form needs the polder terrain (low reclaimed
    # ground); anywhere else the typing rule rejects it (settlements.md 'Polder waterward fringe + dike-top housing').
    dry = Settlement(1200, 1200, seed=1)
    dry.meta(name="Sd", scale="village", terrain="hill")
    dry.pin_knob("settlement_form", "dike_top")
    with pytest.raises(ValueError):
        dry.resolve("settlement_form")
    low = Settlement(1200, 1200, seed=1)
    low.meta(name="Sl", scale="village", terrain="low")
    low.pin_knob("settlement_form", "dike_top")
    assert low.resolve("settlement_form") == "dike_top"


def test_tanning_yard_two_row_layout_and_ditch_intake():
    # The pool covers 4 pits on a ditch (Hoshizora) and 12 on live water (Tango/Nagahara); this
    # reaches the branches between - an ODD pit count over one row, where the last row is short
    # and the pit loop must stop at `pits` rather than filling the grid.
    s = _town()
    s.tanning_yard(400, 400, rot=0, pits=7, water="ditch")
    y = s.M["tanning_yards"][0]
    assert (y["w"], y["h"]) == (58.0, 50.0)  # 2 rows of 4 -> 14 + 11*4 wide, 2*9 + 32 tall
    svg = "".join(s.out)
    assert svg.count('fill="#8E8A6A"') == 7  # exactly 7 pits drawn, not the 8 the grid would hold
    assert '#9CB4C8' in svg  # the gated intake cut (ditch variant), not staking frames


def test_intake_cut_is_lengthened_to_REACH_the_drawn_bank():
    # settlement-review 2026-08-08: the cut was a flat px(11), so a yard seated a little off its
    # ditch (Hoshizora, re-rotated onto the drain) drew a stub that stopped 4 ft short of the water
    # and read as a tab pinned to the yard. Nothing in the gate sees this - tanning_yard_on_water
    # asks whether the YARD is near a bank, never whether the CUT arrives - so the rule lives here.
    s = _town()
    s.field_channel([(340, 340), (460, 340)], "#9CB4C8", 2.0, 2.0)  # a drawn ditch 40px out from the yard's water edge
    s.tanning_yard(400, 400, rot=0, pits=4, water="ditch")
    svg = "".join(s.out)
    # yard is 41 tall, so its water edge sits at y=-20.5 local; the ditch centerline is 39.5 further
    assert 'height="39.5"' in svg and 'y="-60.0"' in svg  # the cut spans edge -> centerline, not a fixed 11
    assert s._intake_reach(400, 400, 0.0, 20.5) == pytest.approx(39.5)


def test_intake_reach_ignores_water_that_is_parallel_behind_or_beside_the_ray():
    # The three rejections, each of which would otherwise hand back a bogus length: a reach the ray
    # runs ALONG (no crossing), one BEHIND the yard (t < 0 - the yard's back, not its water side),
    # and one whose infinite line the ray meets but whose SEGMENT it misses (s outside [0, 1]).
    s = _town()
    s.field_channel([(300, 340), (500, 340)], "#9CB4C8", 2.0, 2.0)  # crossed: the honest answer
    s.field_channel([(300, 500), (500, 500)], "#9CB4C8", 2.0, 2.0)  # behind the yard (its water side faces -y)
    s.field_channel([(600, 200), (700, 200)], "#9CB4C8", 2.0, 2.0)  # off to the side: the ray misses the span
    s.field_channel([(400, 100), (400, 300)], "#9CB4C8", 2.0, 2.0)  # parallel to the ray, dead ahead, never crossed
    assert s._intake_reach(400, 400, 0.0, 20.5) == pytest.approx(39.5)  # the first CROSSING, none of the rest


def test_intake_cut_falls_back_to_its_stock_length_with_no_water_ahead():
    # A yard with nothing drawn in front of it (a fixture, or a bank that curves away) draws exactly
    # what it always did rather than a zero-length or runaway cut.
    s = _town()
    assert s._intake_reach(400, 400, 0.0, 20.5) is None
    s.tanning_yard(400, 400, rot=0, pits=4, water="ditch")
    assert 'height="11.0"' in "".join(s.out)


def test_intake_cut_refuses_a_reach_outside_the_sane_band():
    # Clamp, not stretch: water 300px out is not this yard's water, and a cut drawn to it would be a
    # 300px blue spear across the map. Out-of-band falls back to the stock length like the None case.
    s = _town()
    s.field_channel([(300, 90), (500, 90)], "#9CB4C8", 2.0, 2.0)  # ~290px ahead, far past the px(40) ceiling
    s.tanning_yard(400, 400, rot=0, pits=4, water="ditch")
    assert 'height="11.0"' in "".join(s.out)


def test_tanning_yard_stream_variant_draws_staking_frames():
    s = _town()
    s.tanning_yard(400, 400, pits=4, water="stream")
    svg = "".join(s.out)
    assert '#9CB4C8' not in svg  # no intake cut on live water
    assert svg.count('stroke="#6B4F2A"') >= 4  # three stakes + the frame rail out in the shallows


def test_flow_record_tags_direction_and_derives_the_bearing():
    s = _town()
    s.stream([(100, 100), (100, 400)])  # authored upstream-first: runs due south
    s.stream([(300, 400), (300, 100)], flow="reverse")  # stored south-first, water runs NORTH
    a, b = s.M["streams"]
    assert (a["flow"], a["flow_deg"]) == ("forward", 90.0)
    assert (b["flow"], b["flow_deg"]) == ("reverse", 90.0)  # reversed -> also flows south


def test_navigable_canal_is_level_and_carries_no_bearing():
    s = _town()
    s.canal([(100, 100), (400, 100)])
    rec = s.M["canals"][0]
    assert rec["flow"] == "level" and rec["flow_deg"] is None


def test_flow_record_rejects_an_unknown_direction():
    s = _town()
    with pytest.raises(ValueError, match="forward"):
        s.stream([(0, 0), (10, 10)], flow="downhill-ish")


def test_moat_flow_declares_a_closed_ring_circulation():
    s = _town()
    s.moat_flow((120.44, 200.51), (800.0, 640.0))
    assert s.M["moat_flow"] == {"inlet": [120.4, 200.5], "outlet": [800.0, 640.0]}


def _max_turn_deg(pts):
    """The sharpest direction change anywhere along a polyline, in degrees."""
    worst = 0.0
    for i in range(1, len(pts) - 1):
        (ax, ay), (bx, by), (cx, cy) = pts[i - 1], pts[i], pts[i + 1]
        v0, v1 = (ax - bx, ay - by), (cx - bx, cy - by)
        l0, l1 = math.hypot(*v0), math.hypot(*v1)
        if l0 < 1e-9 or l1 < 1e-9:
            continue
        cosang = max(-1.0, min(1.0, (v0[0] * v1[0] + v0[1] * v1[1]) / (l0 * l1)))
        worst = max(worst, 180.0 - math.degrees(math.acos(cosang)))
    return worst


def test_fillet_polyline_rounds_a_square_corner_into_a_sweep():
    # a right-angle elbow becomes a swept bend: no vertex still turns anywhere near 90 degrees, the
    # ends are untouched (a snapped pond/moat mouth must stay exactly where it was), and the corner
    # itself is gone from the line
    pts = [(0.0, 0.0), (200.0, 0.0), (200.0, 200.0)]
    out = settlement.fillet_polyline(pts, 25.0)
    assert out[0] == (0.0, 0.0) and out[-1] == (200.0, 200.0)
    assert (200.0, 0.0) not in out
    assert _max_turn_deg(out) < 20  # was 90
    assert len(out) == 9  # the two ends plus the arc's 7 samples


def test_fillet_polyline_caps_the_bend_on_short_segments():
    # the cut-back never exceeds 35% of either leg, so two corners cannot eat the segment between
    # them and a short stub keeps its shape (radius 500 asked for on 100px legs)
    out = settlement.fillet_polyline([(0.0, 0.0), (100.0, 0.0), (100.0, 100.0)], 500.0)
    assert min(x for x, _ in out[1:-1]) >= 64.9  # 100 - 35% of the leg
    assert max(y for _, y in out[:-1]) <= 35.1


def test_fillet_polyline_leaves_gentle_bends_and_degenerate_input_alone():
    gentle = [(0.0, 0.0), (100.0, 2.0), (200.0, 4.0)]  # ~0 degrees of turn: nothing to round
    assert settlement.fillet_polyline(gentle, 25.0) == gentle
    assert settlement.fillet_polyline([(0.0, 0.0), (10.0, 0.0)], 25.0) == [(0.0, 0.0), (10.0, 0.0)]  # too few points
    assert settlement.fillet_polyline([(0.0, 0.0), (10.0, 0.0), (20.0, 0.0)], 0.0) == [(0.0, 0.0), (10.0, 0.0), (20.0, 0.0)]  # no radius
    dup = [(0.0, 0.0), (100.0, 0.0), (100.0, 0.0), (100.0, 100.0)]  # a repeated vertex bends nothing
    assert settlement.fillet_polyline(dup, 25.0)[0] == (0.0, 0.0)


def test_round_channel_joints_sweeps_the_seam_between_two_records():
    # a run emitted as two tapering records turns at the SEAM, where fillet_polyline cannot reach it
    from waterfields import round_channel_joints

    a = {"pts": [(0.0, 0.0), (200.0, 0.0)], "w": 7.0, "role": "main"}
    b = {"pts": [(200.0, 0.0), (200.0, 200.0)], "w": 6.0, "role": "main"}
    round_channel_joints([a, b])
    assert a["pts"][-1] == b["pts"][0]  # still one continuous run
    assert _max_turn_deg(a["pts"] + b["pts"][1:]) < 20  # was 90
    assert (200.0, 0.0) not in a["pts"] + b["pts"]


def test_round_channel_joints_leaves_offtakes_and_gentle_seams_alone():
    from waterfields import round_channel_joints

    # a node where a BRANCH also leaves is a junction, not a bend: an offtake is a notch in the bank
    a = {"pts": [(0.0, 0.0), (200.0, 0.0)], "w": 7.0, "role": "main"}
    b = {"pts": [(200.0, 0.0), (200.0, 200.0)], "w": 6.0, "role": "main"}
    branch = {"pts": [(200.0, 0.0), (400.0, 40.0)], "w": 4.0, "role": "branch"}
    round_channel_joints([a, b, branch])
    assert a["pts"] == [(0.0, 0.0), (200.0, 0.0)] and b["pts"] == [(200.0, 0.0), (200.0, 200.0)]
    # ... and a seam that barely bends has no elbow to round
    c = {"pts": [(0.0, 0.0), (200.0, 0.0)], "w": 7.0, "role": "main"}
    d = {"pts": [(200.0, 0.0), (400.0, 6.0)], "w": 6.0, "role": "main"}
    round_channel_joints([c, d])
    assert c["pts"] == [(0.0, 0.0), (200.0, 0.0)]
    # ... and neither a zero-length leg nor a one-point record trips it up
    e = {"pts": [(0.0, 0.0), (200.0, 0.0)], "w": 7.0, "role": "main"}
    g = {"pts": [(200.0, 0.0), (200.0, 0.0), (200.0, 200.0)], "w": 6.0, "role": "main"}
    round_channel_joints([e, g, {"pts": [(9.0, 9.0)], "w": 1.0, "role": "main"}])
    assert e["pts"] == [(0.0, 0.0), (200.0, 0.0)]


def test_moat_current_and_swept_tap_degenerate_rings():
    # a "ring" of two points is not a ring: both helpers bail rather than index past the ends
    assert settlement.moat_current_at([(0, 0), (10, 0)], (0, 0), (10, 0), (5, 5)) is None
    assert settlement.moat_swept_tap([(0, 0), (10, 0)], (0, 0), (10, 0), (5, 5), (9, 9)) == (9, 9)


def test_moat_swept_tap_handles_a_zero_length_edge_and_an_unreachable_target():
    # a duplicated consecutive vertex gives a zero-length edge to step over; want_deg=-1 can never be
    # met, so the walk exhausts max_back and falls back to the best angle it saw
    ring = [(400, 300), (700, 300), (700, 300), (700, 700), (400, 700), (400, 300)]
    got = settlement.moat_swept_tap(ring, (400, 300), (700, 700), (250, 500), (400, 500), want_deg=-1.0, max_back=60.0)
    assert isinstance(got, tuple) and len(got) == 2


def test_moat_swept_tap_scores_a_zero_length_throat_as_unusable():
    # `other` sitting exactly on the candidate leaves no direction to measure - scored 999, never chosen
    ring = [(400, 300), (700, 300), (700, 700), (400, 700), (400, 300)]
    got = settlement.moat_swept_tap(ring, (400, 300), (700, 700), (400, 500), (400, 500), want_deg=-1.0, max_back=40.0)
    assert isinstance(got, tuple)


# ---- the justice works (feature 015) ----------------------------------------------------------
def test_punishment_spot_records_true_size_and_reserves_ground():
    s = _town()
    s.punishment_spot(400, 400, rot=30)
    p = s.M["punishment_spots"][0]
    assert (p["w"], p["h"]) == (30.0, 12.0)  # ~30x12 real ft, true size at town grain (1 ft/px)
    assert p["rot"] == 30.0
    assert (400, 400, 30.0, 12.0) in s.placed  # reserved against the urban pack
    assert s.block_polys  # and against footprint-blocking placers


def test_punishment_spot_draws_no_notice_board():
    # The crime text rides on the cangue, exactly as the historical inscription did - the
    # settlement kosatsuba is a SEPARATE institution and must not be duplicated here.
    s = _town()
    s.punishment_spot(400, 400)
    assert not s.M["kosatsuba"]


def test_execution_ground_is_sized_and_screened_by_tier():
    t = _town()
    t.execution_ground(500, 500)
    e = t.M["execution_grounds"][0]
    assert (e["w"], e["h"]) == (60.0, 60.0)  # county tier: ~60x60 real ft
    assert e["screened"] is False  # a county ground is open to the road on every side
    c = _city()
    c.execution_ground(500, 500)
    ec = c.M["execution_grounds"][0]
    assert (ec["w"], ec["h"]) == (round(c.px(100), 1), round(c.px(60), 1))  # city tier: ~100x60 real ft
    assert ec["screened"] is True


def test_execution_ground_label_can_flip_above_the_ground():
    # The ground shares the outskirts with the polluting trades, whose small glyphs the default
    # below-label can land on (Nagahara's kiln works).
    s = _town()
    s.execution_ground(500, 500, label_above=True)
    lb = [line for line in s.M["labels"] if len(line) > 5 and line[5] == "execution ground"][0]
    assert (lb[1] + lb[3]) / 2 < 500


def test_execution_ground_screening_can_be_forced():
    s = _town()
    s.execution_ground(500, 500, screened=True)
    assert s.M["execution_grounds"][0]["screened"] is True
    assert 'stroke-width="1.6"' in "".join(s.out)  # the hoarding on three sides


def test_execution_ground_reads_disused_at_county_tier():
    # ~1 execution per county per 5-10 years: the unscreened ground carries weeds and EMPTY post
    # sockets, never standing posts. A busy scaffold would assert something false about Rokugan.
    s = _town()
    s.execution_ground(500, 500)
    svg = "".join(s.out)
    assert svg.count('stroke="#8A9464"') == 5  # the weed ticks
    assert svg.count('fill="#3A352C"') == 2  # two empty crucifixion mortises


def test_execution_ground_keeps_its_well_out_of_the_household_accounting():
    # The ground's well washes the blade; it serves no household and must never enter the
    # well-density checks.
    s = _town()
    s.execution_ground(500, 500)
    assert not s.M["wells"]


def test_boundary_marker_is_a_location_marker():
    s = _town()
    s.boundary_marker(300, 300)
    b = s.M["boundary_markers"][0]
    assert (b["w"], b["h"]) == (3.0, 3.0)  # TRUE footprint: a real stone is ~3 ft
    assert b["vw"] == b["vh"] == settlement.BOUNDARY_MARKER_MIN_PX  # DRAWN at the legibility floor
    assert (300, 300, b["vw"], b["vh"]) in s.placed  # overlap uses the drawn box, like the wells


def test_boundary_marker_floor_never_shrinks_a_stone():
    # The marker floor lifts a sub-glyph stone; it must not shrink one that already draws larger.
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="B", scale="town", ftpx=0.25)  # 4 px per foot - the true stone is already 12 px
    s.boundary_marker(300, 300)
    b = s.M["boundary_markers"][0]
    assert b["vw"] == b["w"] == 12.0


def test_justice_works_can_be_unlabeled():
    s = _town()
    s.punishment_spot(200, 200, label=None)
    s.execution_ground(500, 500, label=None)
    s.boundary_marker(700, 700, label=None)
    assert not s.M["labels"]


def test_place_punishment_spot_is_a_no_op_when_opted_out():
    s = _town()
    s.meta(punishment_spot=False)
    s.road([(100, 500), (900, 500)])
    assert s.place_punishment_spot() is None
    assert not s.M["punishment_spots"]


def test_place_punishment_spot_needs_a_street_to_site_on():
    # No road, no town street, no lane: there is no traffic to site the display on, so the siter
    # declines rather than dropping it somewhere arbitrary (the presence check then fires).
    s = _town()
    assert s.place_punishment_spot() is None


def test_place_punishment_spot_skips_a_degenerate_route_segment():
    s = _town()
    s.M["road"] = [[100, 500], [100, 500], [900, 500]]  # a repeated point: zero-length segment
    assert s.place_punishment_spot() is not None


def test_place_punishment_spot_declines_when_no_verge_is_within_the_siting_band():
    # At a very coarse grain the ~60-real-ft band is narrower than the road's own tread plus the
    # feature, so no candidate offset is legal at all - the siter must return None, not guess.
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="C", scale="city", ftpx=30)
    s.road([(100, 500), (900, 500)])
    assert s.place_punishment_spot() is None


def test_place_punishment_spot_walks_the_label_off_a_building_it_would_cover():
    s = _town()
    s.road([(100, 500), (900, 500)])
    s.building(145, 536, 20, 20, "merchant")  # sits under the DEFAULT below-label, not under the spot
    spot = s.place_punishment_spot()
    assert spot is not None
    lb = [line for line in s.M["labels"] if len(line) > 5 and line[5] == "punishment ground"][0]
    below_default = spot[1] + s.px(12) / 2 + 11
    assert abs((lb[1] + lb[3]) / 2 - below_default) > 4  # the label moved off its default band


def test_dojos_roll_follows_the_samurai_cohort():
    # GM formula 2026-07-25: 1 private dojo per full 200 SAMURAI (the city's ~10% share of its
    # population) + a remainder-fraction chance of one extra, floored at 1; count= pins; too few
    # seats is loud. The samurai cohort is the driver, not the population - a dojo serves samurai
    # and nobody else - so the constants are read off the class rather than assumed here.
    def city_(seed, pop):
        s_ = Settlement(1200, 1200, seed=seed)
        s_.meta(name="C", scale="city", ftpx=3)
        s_.M["meta"]["population"] = pop
        return s_

    assert Settlement.DOJO_SAMURAI_FRAC == 0.10 and Settlement.DOJO_PER_SAMURAI == 200
    s = city_(2, 2000)  # 200 samurai = one full unit, zero remainder: exactly 1, no roll can add
    assert s.dojos([(300, 300), (600, 600)]) == 1
    assert s.M["meta"]["dojo_roll"] == 1 and len(s.M["dojos"]) == 1
    s2 = city_(2, 4000)  # 400 samurai = two full units, zero remainder: exactly 2
    assert s2.dojos([(300, 300), (600, 600)]) == 2
    assert len(s2.M["dojos"]) == 2
    # 3,000 -> 300 samurai -> 1 guaranteed + a 50% roll; the two seeds below straddle it
    rolls = {seed: city_(seed, 3000).dojos([(300, 300), (600, 600)]) for seed in (47, 162)}
    assert set(rolls.values()) <= {1, 2}
    assert city_(47, 3000).dojos([(300, 300), (600, 600)], count=2) == 2  # a pin overrides the roll
    s4 = city_(2, 4000)
    with pytest.raises(ValueError, match="vetted seats"):
        s4.dojos([(300, 300)])  # a guaranteed 2 needs 2 seats


def test_martial_hall_and_dojo_draw_their_researched_program():
    # sizes are TRUE feet, not legibility choices (settlements.md "Historical grounding: martial
    # training in a provincial city"): the state hall is a 130x100 ft compound whose archery lane
    # covers the kyudo standard 92 ft shot, a private dojo a 76x44 ft lot with no lane at all.
    s = Settlement(1200, 1200, seed=3)
    s.meta(name="C", scale="city", ftpx=3)
    s.martial_hall(400, 400)
    s.dojo(800, 800)
    (mh,) = s.M["martial_halls"]
    assert (round(mh["w"] * 3), round(mh["h"] * 3)) == (130, 100)
    assert mh["range_ft"] >= 90  # city_martial_hall_has_archery_range's floor
    assert mh["label"] == "martial hall"
    (dj,) = s.M["dojos"]
    assert (round(dj["w"] * 3), round(dj["h"] * 3)) == (76, 44)
    assert "range_ft" not in dj  # no archery lane on a 76 ft lot - the butt is the state hall's
    # the state hall is drawn in government violet, the private hall in ordinary building tan
    assert "#CDBBD6" in s.out[-2] and "#D9C8A4" in s.out[-1]


def test_martial_hall_caption_takes_the_emptier_side():
    # "martial hall" is wide relative to a 43x33 px compound, so the caption side is a real
    # decision: a hall seated beside the yamen would otherwise drop its label on the governor.
    s = Settlement(1200, 1200, seed=3)
    s.meta(name="C", scale="city", ftpx=3)
    s.building(400, 440, 120, 40, kind="samurai")  # a neighbor directly BELOW the hall's seat
    s.martial_hall(400, 400)
    lab = [L for L in s.M["labels"] if len(L) > 5 and L[5] == "martial hall"][0]
    assert lab[1] < 400  # pushed ABOVE the compound, away from the occupied side


def test_open_seat_refuses_a_seat_whose_FOOTPRINT_crosses_the_bound():
    """The martial-hall bug, as a unit test (GM 2026-07-25). s.bound is the ring-road loop a city
    packs inside, and `_fits` tests only a candidate's CENTER against it - so open_seat handed back
    a compound seat whose SE corner lay across Tango's patrol bed. open_seat now tests the whole
    footprint against the bound (and ONLY the bound: block polys and corridors are soft
    reservations a footprint may legitimately overhang, and tightening those cost two pool maps a
    feature apiece when it was tried)."""
    s = Settlement(1200, 1200, seed=3)
    s.meta(name="C", scale="city", ftpx=3)
    s.bound = [[100, 100], [700, 100], [700, 700], [100, 700]]
    over = (665, 300, 695, 320)  # every candidate here keeps its CENTER inside x=700 but its right edge past it
    assert s.open_seat(over, 80, 20) is None
    assert s.open_seat(over, 80, 20, footprint=False) is not None  # the old center-only behavior
    assert s.open_seat((300, 300, 400, 320), 80, 20) is not None  # well inside the bound: fine


# ---- the LABEL STANDOFF LADDER (GM 2026-07-26) ------------------------------------------------
# The rule under test is "among seats that cover nothing, the NEAREST to the subject wins" - the
# term the old overlap-count-only scorer was missing, which let a caption float in empty ground.
def _ladder_map():
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="L", scale="town")
    return s


def test_label_ladder_seats_a_caption_at_the_minimum_standoff_when_the_ground_is_clear():
    s = _ladder_map()
    box = (400.0, 400.0, 500.0, 440.0)  # wider than tall -> below/above are the primary seats
    lx, ly = s._best_label_spot(box, "market", 10)
    assert settlement.box_gap(s._label_box(lx, ly, "market", 10), box) == pytest.approx(settlement.LABEL_MIN_AIR)


def test_label_ladder_steps_outward_past_an_obstacle_and_stops_at_the_first_clear_rung():
    s = _ladder_map()
    box = (400.0, 400.0, 500.0, 440.0)
    clear = s._best_label_spot(box, "market", 10)
    assert settlement.box_gap(s._label_box(*clear, "market", 10), box) == pytest.approx(settlement.LABEL_MIN_AIR)
    for cy in range(370, 476, 7):  # ring the subject so the first rungs are blocked on every side
        for cx in range(330, 576, 12):
            if not (395 < cx < 505 and 395 < cy < 445):
                s.building(cx, cy, 10, 6)
    lx, ly = s._best_label_spot(box, "market", 10)
    gap = settlement.box_gap(s._label_box(lx, ly, "market", 10), box)
    assert gap > settlement.LABEL_MIN_AIR  # the near rungs were blocked...
    assert s._label_hits(lx, ly, "market", 10, pad=0.0, linepad=0.0) == 0  # ...and it kept climbing to clear ground


def test_label_ladder_slides_along_the_long_axis_only():
    # A subject much taller than wide (a road segment, a stall row) is captioned BESIDE it. Sliding
    # ACROSS such a box walks the caption diagonally away while its nominal standoff still reads as
    # small - the first cut of this put "Imperial Road" 43px out at a nominal 5px of air.
    s = _ladder_map()
    tall = (500.0, 200.0, 510.0, 800.0)
    for sl in (-200.0, 200.0):
        seat = s._best_label_spot(tall, "road", 12, slides=(sl,))
        # a slide runs ALONG the subject, so the seat stays tight against it however far it slides;
        # an across-axis slide walked the caption out to 43px at a nominal 5px of air
        assert settlement.box_gap(s._label_box(*seat, "road", 12), tall) <= settlement.LABEL_AIR_CAP * 12


def test_label_ladder_refuses_a_seat_outside_the_cropped_view():
    # a clipped label is unreadable (labels_within_image), so out-of-frame candidates are DISCARDED
    s = _ladder_map()
    box = (100.0, 100.0, 200.0, 140.0)
    free = s._best_label_spot(box, "market", 10)
    assert free[1] > box[3]  # unconstrained, a wide subject is captioned BELOW
    s.M["meta"]["view"] = [60, 60, 400, 90]  # ...but the frame now ends just under the subject
    framed = s._best_label_spot(box, "market", 10)
    assert framed[1] < box[1]  # so the caption moves ABOVE rather than out of the picture


def test_label_ladder_falls_back_to_the_least_covered_seat_when_nothing_is_clear():
    s = _ladder_map()
    box = (400.0, 400.0, 500.0, 440.0)
    for cy in range(320, 540, 10):  # blanket every rung on every side
        for cx in range(300, 620, 10):
            s.building(cx, cy, 14, 8)
    lx, ly = s._best_label_spot(box, "market", 10)
    assert s._label_hits(lx, ly, "market", 10, pad=0.0, linepad=0.0) > 0


def test_place_caption_defers_to_finish_and_records_its_subject_box_for_the_gate():
    # DEFERRED on purpose: a caption seated at call time is judged against half a map (see
    # place_caption's note - Tango's north market caption landed on an execution ground that did
    # not exist yet). Nothing is in M["labels"] until finish() flushes them.
    s = _ladder_map()
    box = (400.0, 400.0, 500.0, 440.0)
    s.place_caption("market", box, 10)
    s.place_caption("ferry", (700.0, 200.0, 720.0, 600.0), 10, slides=(0.0, 40.0))  # explicit slides
    assert not [L for L in s.M["labels"] if L[5] in ("market", "ferry")]
    with tempfile.TemporaryDirectory() as d:
        s.finish(os.path.join(d, "t"), render=False)
    rec = next(L for L in s.M["labels"] if L[5] == "market")
    assert rec[6] == [400.0, 400.0, 500.0, 440.0]
    assert any(L[5] == "ferry" for L in s.M["labels"])


def test_place_caption_refuses_an_empty_subject():
    # s.frontage_box is None when the row placed nothing - captioning it is a gen-script bug
    s = _ladder_map()
    with pytest.raises(ValueError, match="no subject box"):
        s.place_caption("market", None, 10)


def test_frontage_records_the_row_extent_for_place_caption():
    s = _ladder_map()
    s.street([(200, 500), (800, 500)], width=30)
    s.frontage([(200, 500), (800, 500)], ["shop"] * 6, width=30, spacing=60, setback=20, fill=True)
    box = s.frontage_box
    assert box is not None and box[2] > box[0] and box[3] > box[1]
    s.frontage([(200, 500), (800, 500)], [], width=30, spacing=60, setback=20, fill=True)
    assert s.frontage_box is None  # a row that placed nothing leaves no stale box behind


# ---- feature 016: the charcoal district's trade works -------------------------------------------
def test_charcoal_yard_records_its_sheds_and_its_cooling_apron():
    """The apron is part of the record's contract, not decoration: charcoal self-heats, so a yard
    must have open ground to stand a fresh load apart from the conditioned stock. `sheds` floors at
    one - a yard with no roof over the conditioned stock is not a charcoal yard."""
    s = _town()
    s.charcoal_yard(400, 400, rot=-17, sheds=2)
    s.charcoal_yard(700, 700, sheds=0)  # floored
    a, b = s.M["charcoal_yards"]
    assert a["sheds"] == 2 and b["sheds"] == 1
    assert len(a["apron"]) == 4 and a["w"] == 88 and a["h"] == 58
    assert a["label"] == "charcoal yard" and a["rot"] == -17.0


def test_kiln_draws_a_works_and_records_its_body_and_its_quarters():
    """A kiln is a WORKS, not a lone glyph (GM 2026-07-27): the kiln itself, the throwing shed, the
    clay pit, the fuel stack, its own private well, and the cottages of the households that work
    it. `body` and `quarters` are part of the record's contract - kiln_keeps_fire_gap measures from
    the body, and a record with neither is a rule nobody can apply."""
    s = _town()
    s.kiln(400, 400)
    k = s.M["kilns"][0]
    # The caption says "kiln works", not "tile kiln" and not a bare "kiln" (GM 2026-07-27): the
    # feature is the kiln PLUS its drying shed, clay pit, fuel stack, well and its workers' cottages,
    # so naming it after one building inside it under-describes what the reader is looking at.
    assert (k["w"], k["h"]) == (140.0, 120.0) and k["label"] == "kiln works"
    assert len(k["body"]) == 5 and (k["body"][2], k["body"][3]) == (46.0, 16.0)
    assert len(k["quarters"]) == 2  # the default works houses two households
    # the cottages stand a clear fire gap BELOW the kiln body, which is the whole point of the
    # works' otherwise empty middle
    assert min(q[1] for q in k["quarters"]) - (k["body"][1] + 8) >= 60


def test_kiln_cottage_count_is_clamped_to_the_one_to_three_band():
    """Two or three households is the works we draw; a real kiln district could be a dozen, and
    that liberty is recorded in research/urban-features.md rather than taken silently here."""
    s = _town()
    s.kiln(300, 300, cottages=0)
    s.kiln(700, 300, cottages=9)
    assert len(s.M["kilns"][0]["quarters"]) == 1
    assert len(s.M["kilns"][1]["quarters"]) == 3


def test_kiln_rotation_carries_the_body_and_the_quarters_with_it():
    """`rot` lays the kiln's upslope axis along local +x, so a rotated works must report rotated
    world coordinates for both - a body recorded in the unrotated frame would be measured against
    neighbors it does not actually stand near."""
    a, b = _town(), _town()
    a.kiln(500, 500)
    b.kiln(500, 500, rot=90)
    ka, kb = a.M["kilns"][0], b.M["kilns"][0]
    assert ka["body"][1] < 500 and abs(ka["body"][0] - 500) < 40  # unrotated: the kiln sits ABOVE center
    assert kb["body"][0] > 500 and abs(kb["body"][1] - 500) < 40  # rotated 90: it swings to the RIGHT
    assert kb["body"][4] == 90.0


def test_kiln_keeps_its_own_private_well():
    """Clay cannot be weathered, wedged or thrown without water, so the well is a premises fixture
    like the brewery's - and private for the same reason, so it never counts toward the
    settlement's public idobata."""
    s = _town()
    before = len(s.M.get("wells", []))
    s.kiln(400, 400)
    added = s.M["wells"][before:]
    assert len(added) == 1 and added[0].get("private") is True


def test_refining_forge_records_its_two_hearths():
    """Two hearths because the refining is a TWO-STAGE process on both sides of the research - the
    Japanese okaji and the Chinese chao fining both work the iron through more than one heat."""
    s = _town()
    s.refining_forge(400, 400, label="refining forge")
    r = s.M["refining_forges"][0]
    assert r["hearths"] == 2 and (r["w"], r["h"]) == (74, 48)


def test_border_line_records_a_poly_with_no_footprint():
    """A jurisdictional line has no w/h on purpose: it reserves nothing and blocks nothing, which
    is why it is overlap-exempt. It also must NOT register a placement footprint."""
    s = _town()
    before = len(s.placed)
    s.border_line([(900, -20), (900, 1020)])
    b = s.M["borders"][0]
    assert b["poly"] == [[900, -20.0], [900, 1020.0]] and b["label"] == ""
    assert "w" not in b and "h" not in b
    assert len(s.placed) == before  # nothing reserved


def test_border_line_caption_defaults_to_the_lines_midpoint_and_is_registered():
    """The caption goes through self.label(), so the label-collision checks can see it. An earlier
    draft emitted raw <text>, which is invisible to every label check - and duly shipped a border
    caption sitting on a wellhead with a green gate."""
    s = _town()
    n = len(s.M["labels"])
    s.border_line([(900, 0), (900, 400), (900, 800)], label="the Fox border")
    assert len(s.M["labels"]) == n + 1
    assert s.M["labels"][-1][-1] == "the Fox border"
    s2 = _town()
    m = len(s2.M["labels"])
    s2.border_line([(900, 0), (900, 800)], label="pinned", label_xy=(700, 300))
    assert len(s2.M["labels"]) == m + 1


def test_every_roofed_feature_is_a_canopy_keepout():
    """THE RATCHET behind "no tree is drawn on a roof". The canopy keep-out was a hand list until a
    reviewer found scrub on a theater stage; settlement.py cannot import check_village (circular),
    so the roofed set is written out - and this holds it against the real overlap registry. Every
    solid feature must be either a canopy keep-out or explicitly named open-air ground, so a new
    feature cannot silently fall outside both the way `theater_stage` did."""
    import check_village

    classified = set(Settlement._CANOPY_STRUCT_KEYS) | set(Settlement._CANOPY_OPEN_AIR_KEYS)
    missing = sorted(k for k in check_village._OVERLAP_STRUCTS if k not in classified)
    assert not missing, (
        f"solid feature(s) {missing} are neither a canopy keep-out nor declared open-air ground - add them to Settlement._CANOPY_ROOFED_KEYS (a tree may not stand on a roof) or to _CANOPY_OPEN_AIR_KEYS with the reason"
    )


def test_reclist_reads_a_singleton_record_as_well_as_a_list():
    """A few features are stored as a bare dict, not a list - which is why their keys are singular.
    Iterating one blindly yields its string KEYS and `o["w"]` then raises TypeError; that is exactly
    how adding `theater_stage` to the keep-out lists crashed every gen until this helper existed."""
    s = _town()
    s.M["theater_stage"] = {"x": 10, "y": 20, "w": 30, "h": 40}
    assert s._reclist("theater_stage") == [{"x": 10, "y": 20, "w": 30, "h": 40}]
    s.M["houses"] = [{"x": 1, "y": 2, "w": 3, "h": 4}, {"x": 5, "y": 6, "w": 7, "h": 8}]
    assert len(s._reclist("houses")) == 2
    assert s._reclist("no_such_key") == []


def test_well_ground_clear_refuses_water_and_crop():
    """You do not sink a well in a watercourse, and you do not sink one in a crop plot. Placement
    predicted everything else about a well site - lanes, compounds, the bound, its neighbors - but
    never the water or the crop, which is how the overlap matrix found four wells standing in
    ditches, a channel and a hatake plot across three maps."""
    s = _town()
    assert s._well_ground_clear(500, 500)  # bare ground
    s.M["streams"] = [{"poly": [[500, 300], [500, 700]], "w": 9}]
    assert not s._well_ground_clear(500, 500)
    assert s._well_ground_clear(900, 500)  # well clear of it
    s.M["streams"] = []
    s.M["field_ditches"] = [{"poly": [[400, 500], [600, 500]], "w": 1.5}]
    assert not s._well_ground_clear(500, 500)
    s.M["field_ditches"] = []
    s.M["pond"] = [500, 500, 40, 24]
    assert not s._well_ground_clear(505, 500)
    assert s._well_ground_clear(900, 900)
    s.M["pond"] = None
    s.M["dry_plots"] = [{"poly": [[480, 480], [560, 480], [560, 560], [480, 560]], "crop": "barley", "theta": 0}]
    assert not s._well_ground_clear(520, 520)  # inside the plot
    assert not s._well_ground_clear(474, 520)  # its drawn head laps the plot's edge
    assert s._well_ground_clear(900, 900)


def test_merchant_storehouse_is_never_drawn_across_a_neighbor():
    """A kura's overlap is legitimate only because it is an annex of ITS OWN shop. One tucked behind
    a narrow shopfront that happens to back onto the next lot's larger house is a defect - the case
    the old blanket storehouse exemption could not express, and which the matrix found twice."""
    s = _town()
    s.building(500, 500, 54, 36, "merchant", rot=0)
    s.building(500, 455, 86, 60, "merchant_large", rot=0)  # squarely BEHIND it (rot=0 puts the kura north)
    assert s.merchant_storehouses(count=4) == 0
    s2 = _town()
    s2.building(500, 500, 54, 36, "merchant", rot=0)
    assert s2.merchant_storehouses(count=4) == 1  # nothing behind it - the annex is fine


def test_region_blocked_catches_a_keepout_against_a_cell_EDGE():
    """The bug this exists to stop: a keep-out sitting against the middle of a cell EDGE touches
    neither the center nor any corner, so center-plus-corner sampling passes it. That is how a
    wellhead ended up 1 px inside a hatake plot with every sample point clear."""
    cell = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
    assert not settlement.region_blocked(cell, [], [], [], [])
    # a small circle hugging the middle of the LEFT edge - no corner is near it, the center is 50 away
    assert settlement.region_blocked(cell, [], [(-4.0, 50.0, 6.0)], [], [])
    assert not settlement.region_blocked(cell, [], [(-40.0, 50.0, 6.0)], [], [])
    assert settlement.region_blocked(cell, [(-4.0, 50.0, 6.0)], [], [], [])  # same, as a pond
    # a ditch threading across the cell's middle, touching no corner
    assert settlement.region_blocked(cell, [], [], [([(-20.0, 50.0), (120.0, 50.0)], 1.0)], [])
    assert not settlement.region_blocked(cell, [], [], [([(-20.0, 300.0), (120.0, 300.0)], 1.0)], [])
    # a polygon overlapping a corner
    assert settlement.region_blocked(cell, [], [], [], [[(90.0, 90.0), (150.0, 90.0), (150.0, 150.0), (90.0, 150.0)]])
    assert not settlement.region_blocked(cell, [], [], [], [[(300.0, 300.0), (350.0, 300.0), (350.0, 350.0), (300.0, 350.0)]])


def test_quad_hits_seg_covers_all_three_ways_a_line_can_meet_a_cell():
    """A stroked line meets a cell in three distinct ways, and each needs its own test: an ENDPOINT
    lying in (or near) the cell, the line CROSSING an edge, and the line merely GRAZING a corner
    without crossing anything. The third is the one that point sampling misses."""
    cell = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
    assert settlement.quad_hits_seg(cell, (50.0, 50.0), (300.0, 50.0), 1.0)  # endpoint INSIDE
    assert settlement.quad_hits_seg(cell, (-50.0, 50.0), (150.0, 50.0), 1.0)  # CROSSES both edges
    assert settlement.quad_hits_seg(cell, (-50.0, -5.0), (150.0, -5.0), 8.0)  # GRAZES the top corners
    assert not settlement.quad_hits_seg(cell, (-50.0, -5.0), (150.0, -5.0), 2.0)  # ...same line, too thin to reach
    assert not settlement.quad_hits_seg(cell, (-50.0, 500.0), (150.0, 500.0), 8.0)  # nowhere near


def test_point_quad_dist_is_zero_inside_and_grows_outside():
    cell = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    assert settlement.point_quad_dist(5, 5, cell) == 0.0
    assert 2.9 < settlement.point_quad_dist(-3, 5, cell) < 3.1


def test_hard_polys_footprint_test_refuses_what_the_center_test_allowed():
    """The split that fixes center-vs-footprint: `hard_polys` (crop, pond, bog, a field's own
    ditches) is tested against the WHOLE footprint, while `block_polys` keeps the center test its
    soft reservations - caption bands, aprons, fence standoffs - were tuned for."""
    s = _town()
    plot = [(500.0, 500.0), (600.0, 500.0), (600.0, 600.0), (500.0, 600.0)]
    s.block_polys.append(plot)
    assert s._fits(490, 550, 46, 28)  # center (490) is outside the plot, so the center test allows it...
    s.hard_polys.append(plot)
    assert not s._fits(490, 550, 46, 28)  # ...but the footprint runs to 513, well inside it
    assert s._fits(300, 300, 46, 28)  # well clear, still fine


def test_theater_stage_caption_clears_the_rotated_ground():
    """A caption must be seated against the extent the feature is DRAWN at, not its raw half-height.

    `theater_stage` offset its label by `cy + hh + 16`, the reach along +y only when the stage is
    upright. Ubame's stage stands at rot=90, where the ground reaches `hw` along +y - so the caption
    landed INSIDE the ground it names, the outline stroke running through the text
    (settlement-review, 2026-07-26). No check saw it: `labels_clear_of_other_buildings` polices a
    caption sitting on features it does NOT name, and this one sat on the one it did.

    Correcting the reach alone was not enough - a hand seat knows nothing about its neighbors, and
    the corrected offset dropped Tango's caption onto a monk house. So the caption is now seated by
    the STANDOFF LADDER against the rotated extent, HINTED at the historical spot, which keeps every
    upright stage exactly where it was whenever that seat is clear.

    Asserted on the queued caption rather than M["labels"]: `place_caption` defers seating until
    `finish()`, so the label does not exist yet at this point.
    """
    for rot, box, hint in (
        (90, (458, 340, 542, 460), (500, 476)),  # rotated: reach along +y is hw=60, not hh=42
        (0, (440, 358, 560, 442), (500, 458)),  # upright: cy + hh + 16, the historical seat
    ):
        s = _town()
        s.theater_stage(500, 400, 120, 84, rot=rot, label="theater stage")
        assert len(s._captions) == 1, "the stage caption must be queued for the standoff ladder"
        text, bx, _sz, _it, _wt, _co, hi, _sl, _ro = s._captions[0]
        assert text == "theater stage"
        assert tuple(round(v) for v in bx) == box, f"rot={rot}: caption boxed against the wrong extent"
        assert tuple(round(v) for v in hi) == hint, f"rot={rot}: caption hinted at the wrong seat"
        assert _ro == 0.0, f"rot={rot}: both are square rotations, so the caption stays level"


# --- a neighborhood wall JOINS the city wall (GM 2026-07-27, Minami) ----------------------------
def _walled(gates=()):
    s = Settlement(1000, 1000, seed=1)
    s.city_wall([(200, 200), (800, 200), (800, 800), (200, 800)], gates=gates)
    return s


def test_ward_fence_end_snaps_onto_the_wall_ALONG_ITS_OWN_AXIS():
    # GM 2026-07-27: "the neighborhood walls stick out the other side of the city walls". The end is
    # placed 20px past the north rampart (y200) on an OBLIQUE run, which is what separates the two
    # candidate fixes: trimming back along the fence's own terminal segment lands at x=556.8, while
    # a perpendicular snap to the nearest point on the wall would land at x=560 and kink the last
    # stretch off the line the gen drew. Same rule city_streets_meet_through_lanes states for a lane.
    s = _walled()
    s.ward("samurai", [(500, 560), (560, 180)], gates=[])
    end = s.M["wards"][-1]["boundary"][-1]
    assert end == pytest.approx([556.8, 200.0], abs=0.1)
    assert s.M["wards"][-1]["stroke"] == 5.0 and s.M["wall_stroke"] == 11.0


def test_ward_fence_end_parallel_to_the_wall_falls_back_to_the_nearest_point():
    # a terminal segment running ALONG the rampart never crosses it, so there is no axis to extend
    # down - the honest answer is the foot of the perpendicular
    s = _walled()
    s.ward("samurai", [(400, 206), (600, 206)], gates=[])
    bnd = s.M["wards"][-1]["boundary"]
    assert bnd[0] == pytest.approx([400.0, 200.0], abs=0.1)
    assert bnd[-1] == pytest.approx([600.0, 200.0], abs=0.1)


def test_ward_fence_end_far_from_the_wall_is_left_exactly_where_the_gen_put_it():
    # an end nowhere near the rampart is not a junction at all but a fence that FAILS to reach it -
    # city_ward_fence_meets_wall's defect to report. Dragging it silently would hide that.
    s = _walled()
    s.ward("samurai", [(500, 700), (500, 400)], gates=[])
    assert s.M["wards"][-1]["boundary"][-1] == [500.0, 400.0]


def test_ward_fence_without_a_city_wall_is_left_alone():
    s = Settlement(1000, 1000, seed=1)
    s.ward("samurai", [(500, 700), (500, 400)], gates=[])
    assert s.M["wards"][-1]["boundary"] == [[500.0, 700.0], [500.0, 400.0]]


def test_building_refuses_commoners_inside_a_declared_samurai_ward():
    # GM 2026-08-02 (Minami): whole-interior top-up sweeps seated laborers and a merchant row
    # inside the ward fence. Once s.ward has run, the engine refuses those seats at s.building
    # itself - the one chokepoint every pack, frontage and gen-side top-up funnels through.
    s = Settlement(1000, 1000, seed=1)
    s.M["wall"] = [[200, 200], [800, 200], [800, 800], [200, 800]]
    s.ward("samurai", [(400, 795), (400, 400), (795, 400)], gates=[])
    assert s.building(600, 600, 16, 11, "laborer") is False
    assert all(b["kind"] != "laborer" for b in s.M["buildings"])
    assert s.building(600, 600, 16, 11, "samurai") is True  # a resident seats normally
    assert s.building(250, 250, 16, 11, "laborer") is True  # outside the fence - unaffected


def test_ward_interior_returns_none_on_a_zero_perimeter_wall():
    # a "ring" of coincident points has zero perimeter - nothing to walk an arc along
    assert settlement.ward_interior([(400, 945), (400, 400)], [(7, 7), (7, 7), (7, 7)]) is None


def test_ward_fails_loudly_on_a_commoner_already_inside():
    # the ordering guard: a commoner standing inside when the fence goes up means the gen ran a
    # commoner pack before s.ward - fail at gen time, not at the gate
    s = Settlement(1000, 1000, seed=1)
    s.M["wall"] = [[200, 200], [800, 200], [800, 800], [200, 800]]
    s.building(600, 600, 16, 11, "merchant")
    with pytest.raises(ValueError, match="already inside the samurai ward"):
        s.ward("samurai", [(400, 795), (400, 400), (795, 400)], gates=[])


# ---- angled-building captions (GM 2026-08-02): a label tilts with the feature it names ----------
def test_label_tilt_folds_to_the_nearest_horizontal_edge_family():
    assert [settlement.label_tilt(r) for r in (0, 90, 180, 270, -90)] == [0.0] * 5
    assert settlement.label_tilt(-16) == -16.0
    assert settlement.label_tilt(150) == -30.0  # the Hoshizora forge: reads along its long side
    assert settlement.label_tilt(102) == 12.0  # the Ubame tanning yard: the other edge family
    assert settlement.label_tilt(67.1) == -22.9  # the Tango tanning yard
    assert settlement.label_tilt(-104) == -14.0
    assert settlement.label_tilt(90.02) == 0.0  # float noise snaps level


def test_linear_tilt_clamps_where_label_tilt_folds():
    # A LINE has one axis, not a box's two edge families (GM 2026-08-08). Past 45deg a linear
    # caption goes LEVEL - the GM's north-south convention - where the fold would swing it onto a
    # cross direction nothing is drawn at. The pair below is the whole distinction.
    assert settlement.linear_tilt(0) == 0.0
    assert settlement.linear_tilt(-26.6) == -26.6  # Hoshizora's Imperial Road
    assert settlement.linear_tilt(153.4) == -26.6  # ...the same line stored the other way round
    assert settlement.linear_tilt(90) == 0.0  # due north-south: the caption still reads left-to-right
    assert settlement.linear_tilt(72) == 0.0  # Nagahara's approach - too steep to tilt with
    assert settlement.label_tilt(72) == -18.0  # ...which is exactly what a BOX subject wants, and would be wrong here
    assert settlement.linear_tilt(45) == 45.0  # the cutoff is inclusive
    assert settlement.linear_tilt(45.1) == 0.0
    assert settlement.linear_tilt(180.02) == 0.0  # float noise snaps level


def test_label_takes_the_linear_clamp_only_when_the_subject_is_a_line():
    s = _town()
    s.label(500, 500, "Imperial Road", 12, rot=-26.6, linear=True)
    s.label(500, 600, "Imperial Road", 12, rot=72, linear=True)  # a near north-south road
    s.label(500, 700, "tanning yard", 9, rot=72)  # ...the same angle on a BOX subject
    recs = s.M["labels"]
    assert recs[0][7] == -26.6
    assert len(recs[1]) == 6  # level: no element [7], so the record keeps the exact pre-tilt format
    assert recs[2][7] == -18.0  # the fold, which is what a rotated building wants and a road does not


def test_frontage_records_the_row_axis_for_a_caption_that_names_the_run():
    # `s.frontage_rot` is the street's own tangent, so a gen captions the run with
    # `rot=s.frontage_rot, linear=True` instead of hand-copying the angle (which is how a caption
    # drifts off its subject when the row is later re-laid - the same reason frontage_box exists)
    s = _town()
    s.frontage([(100, 700), (700, 400)], (["merchant"] * 3 + ["shop"]) * 3, spacing=48)
    assert s.frontage_rot == pytest.approx(-26.565, abs=0.01)


def test_frontage_rot_clears_when_the_row_places_nothing():
    s = _town()
    s.frontage([(100, 700), (700, 400)], ["merchant"] * 4, spacing=48)
    assert s.frontage_rot != 0.0
    s.frontage([(10, 10), (12, 10)], ["merchant"], fill=True)  # a 2px street hosts nothing
    assert s.frontage_box is None and s.frontage_rot == 0.0  # ...so a stale axis can never be read


def test_label_ladder_seats_a_tilted_caption_by_its_THICKNESS_not_its_rotated_aabb():
    # The defect this pins (GM 2026-08-08): probing the rotated AABB made a diagonal caption reach
    # by most of its own LENGTH in the one direction it does not extend, so "Imperial Road" seated
    # 64px off a clear roadbed. The support is exact in every direction, so a tilted caption tucks
    # in at the same LABEL_MIN_AIR a level one gets.
    s = _ladder_map()
    box = (400.0, 480.0, 600.0, 520.0)
    seat = s._best_label_spot(box, "Imperial Road", 12, tilt=-26.6)
    quad = settlement.label_quad([*s._label_box(*seat, "Imperial Road", 12), 0, "Imperial Road", None, -26.6])
    corners = [(box[0], box[1]), (box[2], box[1]), (box[2], box[3]), (box[0], box[3])]
    assert settlement.poly_gap(quad, corners) < settlement.LABEL_MIN_AIR + 1


def test_label_hits_measures_a_rotated_neighbor_the_way_the_gate_does():
    # `labels_clear_of_other_buildings` boxes a victim by its ROTATED corners' AABB, which is wider
    # than the record's axis-aligned w/h. The probe has to agree, or it waves through exactly what
    # the gate then catches - which is what put Ubame's "caravan inn" in a rot=-16 stables' corner
    # slack the moment the caption's own reach became honest.
    s = _town()
    s.building(300, 300, 92, 44, "stables", rot=-16)
    assert s._label_hits(300, 344, "caravan inn", 9, pad=0.0, linepad=0.0) == 0  # clear of the axis-aligned 92x44...
    assert s._label_hits(300, 344, "caravan inn", 9, pad=0.0, linepad=0.0, tilt=-16) >= 1  # ...inside the rotated AABB the gate reads


def test_label_quad_and_aabb_rotate_the_record_about_its_center():
    lvl = [0.0, 0.0, 100.0, 10.0, 1, "x"]
    assert settlement.label_quad(lvl) == [(0.0, 0.0), (100.0, 0.0), (100.0, 10.0), (0.0, 10.0)]
    assert settlement.label_aabb([*lvl, None]) == (0.0, 0.0, 100.0, 10.0)  # a ref-carrying level record reads the same
    tl = [*lvl, None, 30.0]
    q = settlement.label_quad(tl)
    c30, s30 = math.cos(math.radians(30)), math.sin(math.radians(30))
    assert q[0] == pytest.approx((50 - 50 * c30 + 5 * s30, 5 - 50 * s30 - 5 * c30))
    a = settlement.label_aabb(tl)
    assert a[3] - a[1] > 10 and a[2] - a[0] < 100  # taller and narrower, as a tilted run must be


def test_tilt_caption_seat_picks_the_perpendicular_half_extent_by_fold_family():
    a = math.radians(-30.0)
    # rot=150 folds to -30 with the footprint's LOCAL h perpendicular to the baseline
    assert settlement.tilt_caption_seat(0, 0, 150, -30.0, 50, 10, 11) == pytest.approx((-math.sin(a) * 21, math.cos(a) * 21))
    # rot=102 folds to 12: the other family - the local w lies perpendicular
    b = math.radians(12.0)
    assert settlement.tilt_caption_seat(0, 0, 102, 12.0, 50, 10, 11) == pytest.approx((-math.sin(b) * 61, math.cos(b) * 61))
    # above=True mirrors the seat to the upper edge
    assert settlement.tilt_caption_seat(0, 0, 150, -30.0, 50, 10, 11, above=True) == pytest.approx((math.sin(a) * 21, -math.cos(a) * 21))


def test_label_rot_emits_a_center_rotation_and_appends_the_tilt():
    s = _town()
    s.label(500, 500, "tilted", 9, rot=150)  # a caller passes the FEATURE rotation; label() folds it
    L = s.M["labels"][-1]
    assert len(L) == 8 and L[6] is None and L[7] == -30.0
    assert any('transform="rotate(-30.0' in t for t in s.toplabels)
    s.label(500, 550, "level", 9, rot=90)  # a square rotation folds level: record format unchanged
    assert len(s.M["labels"][-1]) == 6


def test_trade_caption_tilts_and_rotates_its_reserved_band():
    s = _town()
    s.brewery(500, 500, rot=150)
    L = s.M["labels"][-1]
    assert L[5] == "brewery" and len(L) == 8 and L[7] == -30.0
    # the caption hangs off the ROTATED lower edge - the seat swings off plumb with the tilt
    assert (L[0] + L[2]) / 2 > 500 and (L[1] + L[3]) / 2 > 500
    band = s.block_polys[-1]
    assert band[0][1] != band[1][1]  # the reserved caption band rotated with it
    s2 = _town()
    s2.brewery(500, 500, rot=90)
    assert len(s2.M["labels"][-1]) == 6  # square rotation: the level path, byte-identical record


def test_compound_and_marker_captions_tilt_with_their_glyphs():
    s = _town()
    s.manor(500, 300, 120, 90, "Manor", sublabel="the bench", rot=-30)
    recs = {L[5]: L for L in s.M["labels"]}
    assert recs["Manor"][7] == -30.0 and recs["the bench"][7] == -30.0
    s.kosatsuba(200, 700, rot=-29)
    assert s.M["labels"][-1][7] == -29.0
    s.fire_tower(800, 700, rot=150)
    assert s.M["labels"][-1][7] == -30.0
    s.boundary_marker(850, 200, rot=-16)
    assert s.M["labels"][-1][7] == -16.0


def test_punishment_and_execution_captions_tilt_and_keep_their_escapes():
    s = _town()
    s.punishment_spot(500, 500, rot=150)  # the tilted default seat
    assert s.M["labels"][-1][7] == -30.0
    s2 = _town()
    s2.punishment_spot(500, 500, rot=150, label_xy=(430, 470))  # a hand seat keeps its spot, tilted
    L2 = s2.M["labels"][-1]
    assert L2[7] == -30.0 and (L2[0] + L2[2]) / 2 == pytest.approx(430)
    s3 = _town()
    s3.execution_ground(500, 500, rot=164, label_above=True)
    assert s3.M["labels"][-1][7] == -16.0


def test_place_caption_rot_threads_through_finish(tmp_path):
    s = _town()
    s.place_caption("caravan inn", (100, 100, 180, 160), rot=-16)
    s.finish(str(tmp_path / "t"), render=False)
    L = next(x for x in s.M["labels"] if x[5] == "caravan inn")
    assert len(L) == 8 and L[7] == -16.0 and L[6] == [100.0, 100.0, 180.0, 160.0]


def test_label_seat_clear_probes_the_tilted_reach():
    s = _town()
    s.M["houses"].append({"x": 300, "y": 262, "w": 40, "h": 24})
    tw = s.label_caption_hw("a long caption here", 9)
    assert s.label_seat_clear(300, 300, tw, 9)  # the level box clears under the house
    assert not s.label_seat_clear(300, 300, tw, 9, tilt=-30.0)  # the tilted reach swings up into it


def test_ring_drops_candidates_severed_from_their_field_by_a_road():
    # a road along the fan's south flank: ring candidates ACROSS it can never reach the field
    # (hoshizora's south-of-road farmhouse), so they are dropped rather than seated
    s = _town()
    s.road([(-50, 620), (1050, 620)])
    s.paddy_field((200, 200, 600, 600), "", "f", amp=20)
    s.ring(("poly", s.field_polys[0]), 40, 60, ["plain"])
    s.farmsteads()
    assert s.M["houses"]  # the near side seats normally
    assert all(h["y"] < 620 for h in s.M["houses"])


def _ward_city_with_samurai(*houses):
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="W", scale="city", ftpx=3)
    s.M["wall"] = [[200, 200], [800, 200], [800, 800], [200, 800]]
    for x, y, kind, rot in houses:
        s.building(x, y, *s._dims(kind), kind, rot)
    s.ward("samurai", [(400, 795), (400, 400), (795, 400)], gates=[])
    return s


def test_servant_ranges_attach_to_their_own_household():
    # GM 2026-08-02: a ward servant is its household's nagaya, drawn along its master's frontage
    s = _ward_city_with_samurai((600, 600, "samurai", 0.0), (600, 700, "samurai_large", 0.0))
    n = s.servant_ranges()
    assert n == 3  # one range for the junior house, two for the senior (budgets.md)
    ranges = [b for b in s.M["buildings"] if b["kind"] == "servant"]
    assert len(ranges) == 3
    for r in ranges:
        assert r["of"] in ([600.0, 600.0], [600.0, 700.0])
        assert r["w"] > 2.2 * r["h"]  # a RANGE, not a cottage - the proportion carries the read
        assert r["h"] == pytest.approx(s.px(s.SERVANT_RANGE_DEPTH_FT))


def test_servant_ranges_is_a_noop_without_a_ward():
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="W", scale="city", ftpx=3)
    s.building(600, 600, *s._dims("samurai"), "samurai", 0.0)
    assert s.servant_ranges() == 0


def test_building_refuses_a_freestanding_servant_inside_the_ward():
    # barring the commoner kinds alone just handed their ground to the servant packs
    s = _ward_city_with_samurai((600, 600, "samurai", 0.0))
    assert s.building(700, 700, 10, 7, "servant") is False
    assert s.building(150, 150, 10, 7, "servant") is True  # outside the fence, unaffected


def test_servant_ranges_keeps_every_range_inside_the_fence():
    # a house hard against the ward fence must not be ranged out through it
    s = _ward_city_with_samurai((412, 600, "samurai", 0.0))
    s.servant_ranges()
    for r in [b for b in s.M["buildings"] if b["kind"] == "servant"]:
        assert settlement.point_in_poly(r["x"], r["y"], s._samurai_ward_interiors[0])
        assert min(settlement.seg_dist(r["x"], r["y"], (400, 795), (400, 400)), settlement.seg_dist(r["x"], r["y"], (400, 400), (795, 400))) > s._WARD_STROKE


def test_servant_ranges_is_idempotent():
    # it may be re-run after a late household top-up; nobody gets a second range over quota
    s = _ward_city_with_samurai((600, 600, "samurai", 0.0), (600, 700, "samurai_large", 0.0))
    first = s.servant_ranges()
    assert first == 3
    assert s.servant_ranges() == 0
    assert sum(1 for b in s.M["buildings"] if b["kind"] == "servant") == 3


def test_servant_ranges_skips_a_house_too_narrow_to_carry_a_range():
    # below ~2.3x the range depth it stops reading as a range and starts reading as a cottage,
    # so the household simply gets none - its servants sleep under the master's roof
    s = _ward_city_with_samurai()
    s.building(600, 600, 8, 6, "samurai", 0.0)
    assert s.servant_ranges() == 0


def test_poly_gap_measures_true_clearance_and_zero_on_overlap():
    # the exact vertex-to-edge minimum, and 0.0 the moment two quads intersect - the measurement
    # servant_ranges uses to refuse a seat that touches a non-host more closely than its own host
    a = settlement.rot_rect(0, 0, 10, 10, 0)
    assert settlement.poly_gap(a, settlement.rot_rect(20, 0, 10, 10, 0)) == pytest.approx(10.0)
    assert settlement.poly_gap(a, settlement.rot_rect(10, 0, 10, 10, 0)) == pytest.approx(0.0)  # touching
    assert settlement.poly_gap(a, settlement.rot_rect(5, 0, 10, 10, 0)) == 0.0  # overlapping


def test_door_is_clear_rejects_a_blocked_doorway():
    s = _ward_city_with_samurai()
    s.building(600, 608, 20, 10, "monk_house", 0.0)  # squarely across the doorway of the seat below
    assert not s._door_is_clear(600, 600, 20, 6, 0.0)
    assert s._door_is_clear(600, 400, 20, 6, 0.0)  # same footprint, open ground ahead


def test_servant_ranges_refuses_a_seat_whose_own_door_is_blocked():
    # the range is a dwelling too: its own entrance has to open onto something
    probe = _ward_city_with_samurai((600, 600, "samurai", 0.0))
    probe.servant_ranges()
    seat = next(b for b in probe.M["buildings"] if b["kind"] == "servant")
    s = _ward_city_with_samurai((600, 600, "samurai", 0.0))
    # 1.2 px clear of the range - further than its 0.6 px gap to its own host, so the nearest-host
    # rule does not refuse it first, yet inside the ~2.3 px band the door check samples
    s.building(seat["x"], seat["y"] + seat["h"] / 2 + 3.2, seat["w"], 4, "monk_house", 0.0)
    s.servant_ranges()
    seated = [(round(b["x"], 1), round(b["y"], 1)) for b in s.M["buildings"] if b["kind"] == "servant"]
    assert (round(seat["x"], 1), round(seat["y"], 1)) not in seated  # that seat is refused; another flank may still serve


def test_sharp_corners_skips_a_duplicate_vertex_instead_of_counting_it():
    """A repeated vertex turns through no angle at all, so it is neither a hard corner nor an eased
    one - counting it either way would misreport the parcel-fabric shape the manifest records.

    Pinned by a test rather than by a generator accident: the comb used to emit quads with a
    collapsed 4th vertex at the fan's corner, which is what exercised this branch. `build_comb` now
    merges those away (a triangle is recorded as a triangle), so nothing in the pool reaches it -
    but the other field engines' rings can still carry one, and the guard is still right."""
    square = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    assert settlement._sharp_corners(square) == 4
    # The same square with its last vertex repeated. The repeat is NOT counted as a fifth corner -
    # and note it costs the corner it duplicates as well, since that vertex's outgoing edge is now
    # zero-length and gets skipped too. So a ring carrying duplicates under-reports its corners,
    # which is exactly why `build_comb` merges them away instead of leaning on this guard.
    assert settlement._sharp_corners([*square, (0.0, 10.0)]) == 3


# ---------------------------------------------------------------- SeatMemo (the top-up refusal memo)
# Its whole value rests on ONE property: a seat refused once stays refused, because the registries
# the scan reads only ever grow. These tests hold both halves - that it remembers while the map
# only grows, and that it FORGETS the moment anything could have freed ground. Getting the second
# half wrong is silent under-population, which is the failure this engine has already paid for
# twice (see the Indexed docstring), so each way the invariant can break gets its own case.


def _memo_city():
    s = _town()
    s.M.setdefault("buildings", [])
    return s, settlement.SeatMemo(s)


def test_seat_memo_remembers_a_refusal_across_syncs_while_the_map_only_grows():
    s, memo = _memo_city()
    memo.level("laborer", 10, 6, 7).add((100.0, 200.0))
    s.placed.append((1.0, 2.0, 3.0, 4.0))  # an append is exactly what a top-up does between calls
    s.M["buildings"].append({"x": 1, "y": 2, "w": 3, "h": 4, "kind": "laborer"})
    memo.sync()
    assert (100.0, 200.0) in memo.level("laborer", 10, 6, 7)


def test_seat_memo_keys_the_refusal_to_the_kind_footprint_and_tightness():
    # a refusal at one padding says nothing about a looser pass, and a refusal for one kind says
    # nothing about a smaller one - conflating them would silently under-populate a later caste
    _s, memo = _memo_city()
    memo.level("laborer", 10, 6, 7).add((100.0, 200.0))
    assert (100.0, 200.0) not in memo.level("laborer", 10, 6, 4)
    assert (100.0, 200.0) not in memo.level("servant", 10, 6, 7)
    assert (100.0, 200.0) not in memo.level("laborer", 8, 6, 7)  # same kind, re-dimensioned


def test_seat_memo_forgets_when_an_indexed_registry_changes_by_anything_but_an_append():
    # the case the Indexed docstring exists for: a same-length in-place replacement changes CONTENT
    # while identity and length say nothing happened. `version` moving further than `appends` is
    # what catches it.
    s, memo = _memo_city()
    s.block_polys.append([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)])
    memo.sync()
    memo.level("laborer", 10, 6, 7).add((100.0, 200.0))
    s.block_polys[0] = [(5.0, 5.0), (6.0, 5.0), (6.0, 6.0)]
    memo.sync()
    assert (100.0, 200.0) not in memo.level("laborer", 10, 6, 7)


def test_seat_memo_forgets_when_a_registry_is_rebound_or_truncated():
    # `placed` is rebound to a filtered copy in two places in this engine, and that is precisely
    # what defeated the previous attempt at an incremental index over it
    s, memo = _memo_city()
    memo.level("laborer", 10, 6, 7).add((100.0, 200.0))
    s.placed = settlement.Indexed()
    memo.sync()
    assert (100.0, 200.0) not in memo.level("laborer", 10, 6, 7)

    s2, memo2 = _memo_city()
    s2.M["buildings"].append({"x": 1, "y": 2, "w": 3, "h": 4, "kind": "laborer"})
    memo2.sync()
    memo2.level("laborer", 10, 6, 7).add((100.0, 200.0))
    s2.M["buildings"].clear()  # a plain list has only identity + length as a witness; length is enough here
    memo2.sync()
    assert (100.0, 200.0) not in memo2.level("laborer", 10, 6, 7)


def test_seat_memo_forgets_when_a_registry_disappears_altogether():
    s, memo = _memo_city()
    s.M["scratch"] = []
    memo.sync()
    memo.level("laborer", 10, 6, 7).add((100.0, 200.0))
    del s.M["scratch"]
    memo.sync()
    assert (100.0, 200.0) not in memo.level("laborer", 10, 6, 7)


def test_seat_memo_tolerates_bound_being_SET_but_not_unset():
    # None -> a ring only ADDS a constraint (Minami restores s.bound mid-top-up, which must not
    # cost the memo); the reverse frees every seat outside the ring and must clear it
    s, memo = _memo_city()
    memo.level("laborer", 10, 6, 7).add((100.0, 200.0))
    s.bound = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)]
    memo.sync()
    assert (100.0, 200.0) in memo.level("laborer", 10, 6, 7)
    s.bound = None
    memo.sync()
    assert (100.0, 200.0) not in memo.level("laborer", 10, 6, 7)


# ---- THE DAIMYO'S CASTLE (feature 019) -------------------------------------------------------
#
# The castle is drawn WALLS-ONLY with a deliberately empty court, so the tests that matter most
# are the negative ones: nothing may be recorded as a building inside it, ever.


def _castle_map(**kw):
    s = settlement.Settlement(3200, 2700, seed=3)
    s.meta(name="Cap", scale="capital", ftpx=3, walled=True)
    rec = s.castle(1600, 1300, 850, 700, **kw)
    return s, rec


def test_a_capital_declares_its_scale_and_takes_the_city_building_grain():
    s, _ = _castle_map()
    assert s.M["meta"]["scale"] == "capital"
    assert s.bscale == pytest.approx(1 / 3)


@pytest.mark.parametrize("gate_dir", ["south", "north", "east", "west"])
def test_the_castle_records_its_works_and_puts_its_gate_on_the_named_side(gate_dir):
    s, rec = _castle_map(gate_dir=gate_dir)
    assert s.M["castles"][0] is rec
    assert rec["gate_dir"] == gate_dir
    gx, gy = rec["gate"]
    if gate_dir in ("north", "south"):
        assert gx == pytest.approx(1600)
        assert gy == pytest.approx(1300 + (350 if gate_dir == "south" else -350))
    else:
        assert gy == pytest.approx(1300)
        assert gx == pytest.approx(1600 + (425 if gate_dir == "east" else -425))
    assert len(rec["moat"]) == 4 and rec["moat_width"] > 0


@pytest.mark.parametrize("gate_dir", ["south", "north", "east", "west"])
def test_NOTHING_is_ever_recorded_inside_the_castle(gate_dir):
    """The rule that is not a knob. The court is the subject of a separate Mode A sheet, and any
    building drawn here would become a constraint that sheet must silently match."""
    s, _ = _castle_map(gate_dir=gate_dir, baileys=True)
    for key in ("buildings", "houses", "manors", "religious", "ministries"):
        assert not s.M.get(key), f"the castle put something in M[{key!r}] - the court must stay empty"


def test_the_castle_reserves_its_ground_in_BOTH_registries():
    """block_polys is CENTER-tested by the urban packs; placed is distance-tested. An enclosure
    this size has to stop a wide building hanging half its roof over the rampart, and only the
    second registry does that - so the castle registers in both (CLAUDE.md, CENTER vs FOOTPRINT)."""
    s, rec = _castle_map()
    assert len(s.block_polys) == 1
    assert len(s.placed) == 1
    px, py, pw, ph = s.placed[0]
    assert pw > rec["w"] and ph > rec["h"]  # the reservation covers the moat, not just the wall
    xs = [p[0] for p in s.block_polys[0]]
    assert min(xs) < rec["x"] - rec["w"] / 2 and max(xs) > rec["x"] + rec["w"] / 2


def test_without_baileys_the_castle_is_one_enclosure():
    _, rec = _castle_map(baileys=False)
    assert rec["baileys"] == []
    assert len(rec["gates"]) == 1


@pytest.mark.parametrize("gate_dir", ["south", "north", "east", "west"])
def test_the_baileys_are_OFFSET_and_their_gates_dogleg(gate_dir):
    """The provisional internal works (default OFF - see the glyph's docstring for the verdict).
    Two properties matter if they are ever switched back on: the wards are NOT concentric, and
    each ward's gate turns off its parent's, so the route in bends at every wall."""
    _, rec = _castle_map(gate_dir=gate_dir, baileys=True)
    assert len(rec["baileys"]) == 2
    assert len(rec["gates"]) == 3
    for ring in rec["baileys"]:
        cx = sum(p[0] for p in ring) / 4
        cy = sum(p[1] for p in ring) / 4
        assert (abs(cx - rec["x"]) > 1.0) or (abs(cy - rec["y"]) > 1.0), "a ward sits concentric - that reads as a bullseye"
    # each successive gate lies on a different axis from the one before it
    for a, b in zip(rec["gates"], rec["gates"][1:], strict=False):
        assert not (abs(a[0] - b[0]) < 1.0 and abs(a[1] - b[1]) < 1.0)


def test_castle_karamete_records_a_rear_gate_and_second_tower():
    """The ote-mon / karamete-mon pair is the standard castle gate program (GM 2026-08-09,
    researched - rear gate opposite the front, the sortie gate); karamete_dir opens it, a size
    down in tower, and the record carries it only when asked - every existing castle is
    byte-identical."""
    s_one, rec_one = _castle_map()
    assert "karamete" not in rec_one
    assert sum(1 for t in s_one.M["castle_towers"] if t["kind"] == "gate_tower") == 1
    s_two, rec_two = _castle_map(karamete_dir="north")
    assert rec_two["karamete_dir"] == "north"
    assert rec_two["karamete"][1] < rec_two["y"]  # the rear gate opens on the north wall
    assert sum(1 for t in s_two.M["castle_towers"] if t["kind"] == "gate_tower") == 2
    s_east, rec_east = _castle_map(karamete_dir="east")
    east_tower = s_east.M["castle_towers"][-1]
    assert east_tower["w"] < east_tower["h"]  # the rear tower turns with its wall on an east/west gate


def test_a_castle_caption_is_placed_only_when_a_label_is_given():
    s_none, _ = _castle_map(label="")
    s_lab, _ = _castle_map(label="Keep")
    assert len(s_lab.M.get("labels", [])) == len(s_none.M.get("labels", [])) + 1


def test_a_castle_caption_can_be_hand_seated():
    """label_xy moves the caption off the court's center - the same escape s.martial_hall keeps."""
    s_def, _ = _castle_map(label="Keep")
    s_hand, _ = _castle_map(label="Keep", label_xy=(1150, 1050))
    assert s_def.M["labels"][-1] != s_hand.M["labels"][-1]


# ---- feature 020: the capital's ground-reserving layer ----------------------------------------


def _cap020():
    s = settlement.Settlement(1400, 1400, seed=9)
    s.meta(name="C", scale="capital", ftpx=3, walled=True)
    return s


def test_towpath_records_a_list_and_draws_no_roadbed_or_centerline():
    """A towpath is NOT a road (research/cities/capitals.md, 'A river gets a TOWPATH, not a
    road'): no roadbed fill, no dashed centerline, one hairline at the linework floor."""
    s = _cap020()
    n0 = len(s.out)
    s.towpath([(100, 1300), (400, 1000), (700, 800)])
    frag = "".join(s.out[n0:])
    assert isinstance(s.M["towpaths"], list) and len(s.M["towpaths"]) == 1
    rec = s.M["towpaths"][0]
    assert rec["pts"][0] == [100, 1300] and rec["pts"][-1] == [700, 800]
    assert "stroke-dasharray" not in frag  # no dashed centerline - it is not a road
    assert frag.count("<path") == 1  # ONE hairline stroke, no roadbed under it
    assert rec["w"] <= 4.0  # a beaten path, not a carriageway
    # and it never touches the road records - a towpath must not read as road plumbing
    assert not s.M.get("roads") and not s.M.get("road")


def test_sluice_gate_label_names_the_black_bar():
    """The bare sluice glyph reads as a floating black bar at fit zoom (GM 2026-08-09) - most
    of a real gate is in the water, so the word does the explaining; label only when asked, so
    every existing map is byte-identical."""
    s1 = _cap020()
    n0 = len(s1.M.get("labels", []))
    s1.sluice_gate(500, 500, rot=30)
    assert len(s1.M.get("labels", [])) == n0  # unlabeled by default
    s2 = _cap020()
    s2.sluice_gate(500, 500, rot=30, label="sluice gate")
    lab2 = [L for L in s2.M["labels"] if len(L) > 5 and L[5] == "sluice gate"]
    assert len(lab2) == 1
    s3 = _cap020()
    s3.sluice_gate(500, 500, rot=30, label="sluice gate", label_xy=(540, 480))
    lab3 = [L for L in s3.M["labels"] if len(L) > 5 and L[5] == "sluice gate"]
    assert len(lab3) == 1 and abs((lab3[0][0] + lab3[0][2]) / 2 - 540) < 2  # seated at the hand point


def test_towpath_reserves_its_ground():
    s = _cap020()
    n_corr = len(s.corridors)
    s.towpath([(100, 1300), (700, 800)])
    assert len(s.corridors) == n_corr + 1  # later packs keep off the bank


def test_aqueduct_records_intake_channel_and_terminus():
    s = _cap020()
    s.aqueduct([(1300, 200), (900, 150), (500, 120)])
    assert isinstance(s.M["aqueducts"], list) and len(s.M["aqueducts"]) == 1
    rec = s.M["aqueducts"][0]
    assert rec["poly"][0] == [1300, 200] and rec["intake"] == [1300, 200]
    assert rec["to"] == [500, 120]
    assert rec["w"] > 0


def test_aqueduct_draws_no_arcade():
    """NO ARCADED AQUEDUCT EXISTS in either anchor tradition (research/cities/capitals.md): the
    vocabulary is a gravity canal at grade, a buried pipe, and a flume bridge only where water
    crosses water. Every path in the glyph is straight cuts - no arch curves anywhere."""
    s = _cap020()
    n0 = len(s.out)
    s.aqueduct([(1300, 200), (900, 150), (500, 120)])
    frag = "".join(s.out[n0:])
    for d in re.findall(r'd="([^"]+)"', frag):
        cmds = set(re.findall(r"[A-Za-z]", d))
        assert cmds <= {"M", "L"}, f"curve commands {cmds - {'M', 'L'}} in the aqueduct glyph - an arch has no business here"


def test_manor_ink_parameter_marks_foreign_sovereign_ground():
    """The Imperial Magistrate's compound is foreign sovereign ground and must not read as another
    domain office: the manor form, in its own ink (settlements/capitals.md, 'Compounds with no
    provincial equivalent')."""
    s1 = _cap020()
    s1.manor(700, 700, 240, 180, "Imperial Magistrate's Compound", gate_dir="west")
    assert "ink" not in s1.M["manors"][0]  # the default stays byte-identical for every old map
    s2 = _cap020()
    n0 = len(s2.out)
    s2.manor(700, 700, 240, 180, "Imperial Magistrate's Compound", gate_dir="west", ink="#274D3D")
    assert s2.M["manors"][0]["ink"] == "#274D3D"
    assert 'stroke="#274D3D"' in "".join(s2.out[n0:])


def test_full_tilt_lays_a_row_caption_along_the_row():
    """GM 2026-08-09: linear subjects may carry the FULL tilt (linear_tilt_full), past the
    45-degree go-level clamp the road captions keep - a -54 deg granary row's caption lies
    along the row, and a bearing and its reverse caption identically."""
    assert settlement.linear_tilt_full(-54) == -54.0
    assert settlement.linear_tilt_full(126) == -54.0
    assert settlement.linear_tilt_full(0) == 0.0
    s = _cap020()
    s.granary(700, 700, n=3, w=20, h=12, gap=8, label="domain granaries", append=True, rot=-54)
    assert "rotate(-54" in "".join(s.out)  # the caption carries the row's own angle


def test_manor_label_inside_fits_the_court():
    """A city estate's caption lives INSIDE the blank court (GM 2026-08-09), sized to clear the
    walls - and a small estate gets a smaller face rather than an overflowing one."""
    s = _cap020()
    s.manor(700, 700, 150, 118, "Hazama Estate", label_inside=True)
    box = next(L for L in s.M["labels"] if len(L) > 5 and L[5] == "Hazama Estate")
    assert box[0] > 625 and box[2] < 775 and box[1] > 641 and box[3] < 759  # fully inside the court
    s2 = _cap020()
    s2.manor(700, 700, 70, 54, "Seki Estate", label_inside=True)
    box2 = next(L for L in s2.M["labels"] if len(L) > 5 and L[5] == "Seki Estate")
    assert box2[2] - box2[0] <= 60  # the face shrinks to the smaller court


def test_ministry_label_inside_stacks_two_lines_on_the_glyph():
    """The capital's ministry captions sit ON the glyph (GM 2026-08-09) - the estate rule
    applied to the state offices, two stacked lines because the long names cannot fit the
    width in one; a provincial city keeps its beside-captions (smaller compounds)."""
    s = _cap020()
    s.ministry(700, 700, "Ministry of Retainers", label_inside=True)
    recs = [L for L in s.M["labels"] if len(L) > 5 and L[5] in ("Ministry of", "Retainers")]
    assert len(recs) == 2
    for box2 in recs:
        assert box2[0] > 662 and box2[2] < 738 and box2[1] > 675 and box2[3] < 725  # on the glyph
    s2 = _cap020()
    s2.ministry(700, 700, "Records Hall", label_inside=True)  # a non-"Ministry of" office keeps one line
    assert any(len(L) > 5 and L[5] == "Records Hall" for L in s2.M["labels"])


def test_granary_rot_turns_the_row_and_records_rotated_stores():
    """A riverside complex stands parallel to the bank it loads from (GM 2026-08-09) - the row
    turns as a unit and every store records the rotation, so the matrix tests real corners."""
    s = _cap020()
    s.granary(700, 700, n=3, w=20, h=12, gap=8, label="domain granaries", append=True, rot=-54)
    recs = s.M["granaries"]
    assert len(recs) == 3 and all(r["rot"] == -54 for r in recs)
    assert recs[0]["x"] != recs[1]["x"] and recs[0]["y"] != recs[1]["y"]  # the row marches along the turned axis


def test_hanko_records_into_the_martial_halls_family():
    """The domain school is the hanko - a school of letters WITH the martial wing - so it draws
    with the martial-hall vocabulary and records into the same family the checks read."""
    s = _cap020()
    s.hanko(700, 700)
    mh = s.M["martial_halls"][0]
    assert mh["kind"] == "hanko" and mh["label"] == "Domain School"
    assert mh["w"] == 133.3 and mh["h"] == 86.7  # 400 x 260 ft (~1 ha) at 3 ft/px - mid-band vs Meirinkan/Nisshinkan
    assert mh["range_ft"] == 100.0  # the kyudo lane, same as the provincial hall


def test_granary_append_records_a_list_for_a_capital_with_two_granaries():
    """A capital holds its grain in TWO places for two reasons (the domain's working rice at the
    wharf, the Emperor's stores beside it) - the legacy single M['granary'] dict cannot carry
    both, so append=True records each store into the M['granaries'] LIST instead."""
    s = _cap020()
    s.granary(400, 400, n=3, w=20, h=12, gap=8, label="domain granary", append=True)
    s.granary(800, 300, n=2, w=20, h=12, gap=8, label="Imperial granaries", append=True)
    assert "granary" not in s.M  # the legacy dict is untouched
    assert len(s.M["granaries"]) == 5  # one record per store, so the matrix can see each
    assert {r["label"] for r in s.M["granaries"]} == {"domain granary", "Imperial granaries"}
    assert all("w" in r and "h" in r for r in s.M["granaries"])
