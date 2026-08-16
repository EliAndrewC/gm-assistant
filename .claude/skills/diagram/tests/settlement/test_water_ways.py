"""Split from test_settlement.py by feature 025 - see tests/settlement/CLAUDE.md for the index."""

import math
import os
import tempfile

import pytest

import settlement
from settlement import Settlement
from tests.settlement._builders import _crop_settlement, _nuc_village, _town, _village, _walled, _zoned_city


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


def test_street_default_width_falls_back_to_the_ft_scale():
    # street() with no explicit width uses a real 24 ft, converted at the map's ftpx and linework-floored
    s = _town()
    s.street([(100, 200), (900, 200)])  # no width -> the lw(24) default branch
    assert s.M["town_streets"][0]["w"] == s.lw(24)


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


def test_clip_to_moat_whole_path_inside_is_left_alone():
    s = _crop_settlement()
    s.M["moat"] = [(300, 100), (300, 900)]
    s.M["moat_width"] = 22
    both_in = [(298, 400), (302, 500)]  # both ends within the bed -> untouched
    assert s._clip_to_moat(both_in) == both_in


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


def test_bridges_spans_a_lane_where_it_crosses_a_canal():
    s = _crop_settlement()
    s.lane([(100, 300), (500, 300)], width=6, worn=True)  # a lane running E-W
    s.M["field_ditches"] = [{"poly": [[300, 150], [300, 450]], "w": 5}]  # a canal crossing it at (300, 300)
    n = s.bridges()
    assert n == 1 and len(s.M["bridges"]) == 1
    assert abs(s.M["bridges"][0]["x"] - 300) < 2 and abs(s.M["bridges"][0]["y"] - 300) < 2


def test_bridges_solves_the_oblique_span_and_lands_every_corner():
    """The span solves the crossing angle exactly (GM 2026-08-09: the old flat +28px slack was
    eaten by obliquity and left deck corners AT the water's edge): along the deck the water is
    w/sin wide, the deck's own width adds rw*|cos|/sin before a corner clears, and past that
    each side runs LANDING_FT (10 real ft) of dry landing."""
    s = _crop_settlement()
    s.lane([(100, 500), (900, 500)], width=6, worn=True)
    s.M["field_ditches"] = [{"poly": [[300, 700], [700, 300]], "w": 10}]  # crosses the lane at 45 deg
    assert s.bridges() == 1
    c45 = math.cos(math.radians(45))
    exp = (10 + 6 * c45) / c45 + 20.0  # sin 45 == cos 45; + 2 * LANDING_FT at ftpx 1
    assert abs(s.M["bridges"][0]["span"] - exp) < 0.6
    s2 = _crop_settlement()
    s2.lane([(100, 300), (500, 300)], width=6, worn=True)
    s2.M["field_ditches"] = [{"poly": [[300, 150], [300, 450]], "w": 5}]
    assert s2.bridges() == 1
    assert abs(s2.M["bridges"][0]["span"] - 25.0) < 0.1  # perpendicular: water + two 10 ft landings, nothing more


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


# ---- lane: the UNWORN (paved/dashed) branch ------------------------------------------------
def test_lane_unworn_draws_a_dashed_causeway():
    s = _village()
    s.lane([(100, 300), (500, 300)], width=6, worn=False)
    assert s.M["lanes"][-1]["worn"] is False
    assert 'stroke-dasharray="8,8"' in "".join(s.out)  # the dashed centerline of a paved lane


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


def test_intake_cut_refuses_a_reach_outside_the_sane_band():
    # Clamp, not stretch: water 300px out is not this yard's water, and a cut drawn to it would be a
    # 300px blue spear across the map. Out-of-band falls back to the stock length like the None case.
    s = _town()
    s.field_channel([(300, 90), (500, 90)], "#9CB4C8", 2.0, 2.0)  # ~290px ahead, far past the px(40) ceiling
    s.tanning_yard(400, 400, rot=0, pits=4, water="ditch")
    assert 'height="11.0"' in "".join(s.out)


def test_flow_record_tags_direction_and_derives_the_bearing():
    s = _town()
    s.stream([(100, 100), (100, 400)])  # authored upstream-first: runs due south
    s.stream([(300, 400), (300, 100)], flow="reverse")  # stored south-first, water runs NORTH
    a, b = s.M["streams"]
    assert (a["flow"], a["flow_deg"]) == ("forward", 90.0)
    assert (b["flow"], b["flow_deg"]) == ("reverse", 90.0)  # reversed -> also flows south


def test_flow_record_rejects_an_unknown_direction():
    s = _town()
    with pytest.raises(ValueError, match="forward"):
        s.stream([(0, 0), (10, 10)], flow="downhill-ish")


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


def test_ward_fails_loudly_on_a_commoner_already_inside():
    # the ordering guard: a commoner standing inside when the fence goes up means the gen ran a
    # commoner pack before s.ward - fail at gen time, not at the gate
    s = Settlement(1000, 1000, seed=1)
    s.M["wall"] = [[200, 200], [800, 200], [800, 800], [200, 800]]
    s.building(600, 600, 16, 11, "merchant")
    with pytest.raises(ValueError, match="already inside the samurai ward"):
        s.ward("samurai", [(400, 795), (400, 400), (795, 400)], gates=[])


def test_quarter_accepts_the_capital_zones():
    """021: "castle" and "samurai" are legal quarter zones (capital vocabulary) - the citadel
    and the senior bands tile the interior without entering the residential density body."""
    s = _crop_settlement()
    s.quarter([(100, 100), (400, 100), (400, 400), (100, 400)], "castle")
    s.quarter([(400, 100), (700, 100), (700, 400), (400, 400)], "samurai")
    assert [q["zone"] for q in s.M["quarters"]] == ["castle", "samurai"]


def test_kido_mesh_reserves_and_gates_every_machi_mouth():
    """kido_mesh derives its gates from the SAME machi_mouths source the validator reads and
    reserves each gate's ground before the packs (021; the wip capital was its only exerciser)."""
    s = Settlement(1000, 1000, seed=3)
    s.street([(200, 500), (800, 500)])
    s.district("test machi", "machi", [(300, 400), (700, 400), (700, 600), (300, 600)], rank_band=None)
    before = len(s.block_polys)
    n = s.kido_mesh()
    assert n == len(s.M.get("kido", []))
    if n:
        assert len(s.block_polys) > before  # each kido reserved its ground


def test_a_dense_row_seats_shops_closer_than_a_default_row():
    """A machiya row is a CONTINUOUS street wall - shops share party walls and the frontage reads
    as one built edge. The default row measures its neighbors with the rotation-invariant collision
    circle, which forces a 46x28 shop 57.8 px from the next where the true touching distance is 28,
    so a commercial street comes out as a dotted line of boxes. dense=True measures row mates edge
    to edge along the row's own axis instead. Opt-in, because it re-rolls any map that takes it."""
    street = [(200, 100), (200, 900)]

    def run(dense):
        s = settlement.Settlement(1000, 1000, seed=7)
        s.meta(scale="city", ftpx=3)
        s.street(street, width=s.lw(18))
        # both=False puts every seat in ONE file, which is where the two rules differ: an 18x12
        # merchant needs 25.6 px of pitch under the collision circle and 19.5 px measured edge to
        # edge, so a 20 px pitch is refused by the first and accepted by the second.
        return s.frontage(street, ["merchant"] * 40, width=8, spacing=20, setback=14, both=False, dense=dense)

    loose, tight = run(False), run(True)
    assert tight > loose, f"a dense row should seat MORE shops on the same street ({tight} vs {loose})"


def test_a_dense_row_sits_inside_the_band_of_the_way_it_lines():
    """The shops LINING a street stand inside that street's own cleared band - the band exists to
    keep OTHER things off the way. A dense row skips the fronted stretch even when the gen wrote it
    as its own two-point list rather than passing the registered street object (the identity match
    that silently cost the pool two thirds of its commercial frontage)."""
    street = [(200, 100), (200, 900)]

    def run(dense):
        s = settlement.Settlement(1000, 1000, seed=3)
        s.meta(scale="city", ftpx=3)
        s.street(street, width=s.lw(30))  # a wide way: its band reaches past a short setback
        return s.frontage([(200, 150), (200, 850)], ["merchant"] * 24, width=6, spacing=26, setback=2, both=False, dense=dense)

    assert run(True) > run(False), "a row must not be refused by the cleared band of the way it fronts"


def test_a_dense_row_refuses_a_mate_that_would_overlap_it():
    """Measuring row mates edge to edge is a RELAXATION of the collision circle, not an abdication:
    two seats in one file still may not interpenetrate, or a tight commercial pitch draws shops
    through each other."""
    street = [(200, 100), (200, 900)]
    s = settlement.Settlement(1000, 1000, seed=5)
    s.meta(scale="city", ftpx=3)
    s.street(street, width=s.lw(18))
    n = s.frontage(street, ["merchant"] * 40, width=8, spacing=9, setback=14, both=False, dense=True)
    B = [b for b in s.M["buildings"] if b["kind"] == "merchant"]
    assert n < 40, "a pitch below the footprint width must refuse seats, not stack them"
    for i, a in enumerate(B):
        for b in B[i + 1 :]:
            assert not (abs(a["x"] - b["x"]) < (a["w"] + b["w"]) / 2 - 0.5 and abs(a["y"] - b["y"]) < (a["h"] + b["h"]) / 2 - 0.5), "row mates interpenetrate"


def test_a_dense_row_still_leaves_the_mouth_of_a_crossing_street_clear():
    """The relaxation is scoped to the way being LINED. A street crossing the row is a different
    way with its own cleared band, and the row must break at the junction - a shop built across the
    mouth of a side street is exactly what the corridor rule exists to prevent."""
    spine = [(200, 100), (200, 900)]
    cross = [(60, 500), (940, 500)]  # long, so its midpoint is nowhere near the spine
    s = settlement.Settlement(1000, 1000, seed=13)
    s.meta(scale="city", ftpx=3)
    s.street(spine, width=s.lw(18))
    s.street(cross, width=s.lw(24))
    s.frontage(spine, ["merchant"] * 30, width=6, spacing=20, setback=4, both=False, dense=True)
    at_mouth = [b for b in s.M["buildings"] if b["kind"] == "merchant" and abs(b["y"] - 500) < 16]
    assert not at_mouth, f"the row built across the crossing street's mouth: {[(b['x'], b['y']) for b in at_mouth]}"
