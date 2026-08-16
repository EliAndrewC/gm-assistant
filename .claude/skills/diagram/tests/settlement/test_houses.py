"""Split from test_settlement.py by feature 025 - see tests/settlement/CLAUDE.md for the index."""

import json
import random

import pytest

import settlement
from settlement import Settlement
from tests.settlement._builders import _crop_settlement, _ladder_map, _nuc_village, _pos_where, _town, _village


def test_frontage_runs_out_of_items_mid_row():
    # rows=2 but a single item: the first row places it, the second row hits the `break` when
    # `items` is already empty (a multi-row frontage stub with an odd remainder).
    s = _town()
    s.frontage([(100, 500), (900, 500)], ["merchant"], rows=2)
    assert sum(1 for b in s.M["buildings"] if b["kind"] == "merchant") == 1


def test_frontage_shortfall_is_reported(capsys):
    s = _town()
    s.frontage([(100, 500), (160, 500)], ["merchant"] * 8)  # a 60px street cannot host 8
    assert "FRONTAGE SHORTFALL" in capsys.readouterr().out


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


def test_dry_polys_block_a_footprint_margin_not_just_the_center():
    # dry crop plots are FOOTPRINT-aware no-build cropland: block_polys test only a candidate's
    # CENTER, which let a house centered just off a hem strip stand half its footprint on the crop
    s = _crop_settlement()
    s.dry_polys.append([(300, 300), (500, 300), (500, 380), (300, 380)])
    assert not s._fits(400, 340, 20, 14)  # centered inside the strip -> blocked
    assert not s._fits(510, 340, 20, 14)  # centered 10px OUTSIDE: the footprint would overlap -> still blocked
    assert s._fits(560, 340, 20, 14)  # well clear of the 12px margin -> fits


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


def test_bundle_geom_nucleated_records_a_gardens_list_spanning_the_bbox():
    s = _nuc_village()
    x, y = _pos_where(lambda x, y: Settlement._hjit(x, y, 8.0) < 0.26 and Settlement._hjit(x, y, 9.0) < 0.5)
    geom = s._bundle_geom(x, y, 46, 28, "E")  # a big house so the flank split clears its gate
    assert len(geom["gardens"]) == 2
    bx, by, bw, bh = geom["bbox"]
    for gx, _gy, gw, _gh in geom["gardens"]:  # every bed lies inside the bundle bbox
        assert bx - bw / 2 - 1 <= gx - gw / 2 and gx + gw / 2 <= bx + bw / 2 + 1


def test_nucleated_bundle_returns_none_when_boxed_in():
    # a bound admitting the seed but no room for even the compact house+yard+garden bundle -> no placement
    s = _nuc_village()
    s.bound = [(495, 495), (505, 495), (505, 505), (495, 505)]
    assert s.try_place(500, 500, "plain") is False


def test_fits_steers_off_a_grove():
    # groves are out of `placed` (so they may merge), but `_fits` still keeps the wells off them
    s = Settlement(1000, 1000, seed=1)
    s.grove_rects.append((500, 500, 40, 40))
    assert s._fits(505, 505, 20, 20) is False


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


# ---- try_place: an abandoned ruin that does not FIT is rejected ----------------------------
def test_try_place_abandoned_rejects_a_ruin_off_the_canvas_edge():
    s = _nuc_village()
    assert s.try_place(20, 300, "abandoned") is False  # x < 55 -> _fits fails, no ruin placed
    assert not [h for h in s.M["houses"] if h["kind"] == "abandoned"]


def test_lane_skeleton_method_draws_lanes_and_records_axis():
    s = Settlement(1200, 1400, seed=3)
    s.meta(name="Sk", scale="village")
    before = len(s.M.get("lanes", []))  # 'lanes' is created lazily on the first lane() call
    lay = s.lane_skeleton("T", 400, 700, 120, 210)
    assert s.M["meta"]["lane_skeleton"] == "T"  # recorded for the twin-detector
    assert len(s.M["lanes"]) == before + 2  # a T lays two lanes (spine + crossbar)
    assert lay["headman"] == (400, 700 - 210 * 0.4)  # derived focal point returned


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


def test_frontage_records_the_row_extent_for_place_caption():
    s = _ladder_map()
    s.street([(200, 500), (800, 500)], width=30)
    s.frontage([(200, 500), (800, 500)], ["shop"] * 6, width=30, spacing=60, setback=20, fill=True)
    box = s.frontage_box
    assert box is not None and box[2] > box[0] and box[3] > box[1]
    s.frontage([(200, 500), (800, 500)], [], width=30, spacing=60, setback=20, fill=True)
    assert s.frontage_box is None  # a row that placed nothing leaves no stale box behind


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


def test_the_way_a_row_FRONTS_does_not_refuse_it_its_own_tread():
    """`skip` means the same thing to the tread test as it does to `_near_corridor`, and for the same
    reason: a frontage row lines the way it fronts, so that way's own surface must not be what
    refuses it. Matched by GEOMETRY as well as identity - a frontage written as a fresh two-point
    list over a sub-stretch is the shape that once cost the pool two thirds of its shop frontage."""
    s = Settlement(1400, 1400, seed=3)
    s.meta(name="Front", scale="hamlet", ftpx=1, toscale=True, households=12)
    way = [[200.0, 700.0], [1200.0, 700.0]]
    s.lane(way, width=16, clearance=22)
    x, y, w, h = 700.0, 706.0, 62.0, 56.0  # a footprint squarely over the tread
    assert s._on_a_tread(x, y, w, h), "the fixture must actually sit on the tread, or it proves nothing"
    assert not s._on_a_tread(x, y, w, h, skip=way), "the very polyline registered must be skipped"
    assert not s._on_a_tread(x, y, w, h, skip=[[400.0, 700.0], [900.0, 700.0]]), "a SUB-STRETCH of the way is the same ground"
    assert not s._on_a_tread(x, y, w, h, skip=[[[400.0, 700.0], [900.0, 700.0]]]), "a LIST of fronted stretches is accepted too"
    assert not s._on_a_tread(x, y, w, h, skip=[[100.0, 700.0], [1300.0, 700.0]]), "a stretch LONGER than the way is the same ground too"
    assert s._on_a_tread(x, y, w, h, skip=[[700.0, 200.0], [700.0, 1200.0]]), "a way merely CROSSING must still refuse"
    assert s._on_a_tread(x, y, w, h, skip=[[700.0, 700.0]]), "a degenerate one-point skip excuses nothing"


def test_a_house_is_refused_a_seat_whose_DRAWN_corner_lands_on_a_lane():
    """THE RATCHET for the engine's "placement tests a different footprint than the one drawn" debt,
    at the lane (this skill's CLAUDE.md, "CENTER vs FOOTPRINT" item 3).

    `_near_corridor` measures a candidate's CENTRE against a way's soft clearance, so a homestead
    whose drawn steading is wider than the placer assumed could stand a legal distance off by its
    centre and still put a corner on the road - which `houses_clear_of_lanes` reports as a house in
    the lane. The tread is now tested against the FOOTPRINT, so the same centre is legal for a
    narrow building and refused for a wide one. Both halves are asserted: a test that refuses
    everything decides nothing."""
    s = Settlement(1400, 1400, seed=3)
    s.meta(name="Tread", scale="hamlet", ftpx=1, toscale=True, households=12)
    s.lane([[200.0, 700.0], [1200.0, 700.0]], width=16, clearance=22)
    cx, cy = 700.0, 734.0  # 34 px off the centreline: clear of the 22 px clearance by its centre
    assert s._fits(cx, cy, 46.0, 28.0), "the base footprint stands clear of the lane and must be allowed"
    assert not s._fits(cx, cy, 62.0, 56.0), "the DRAWN footprint puts a corner on the tread and must be refused"
