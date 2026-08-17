"""Split from test_settlement.py by feature 025 - see tests/settlement/CLAUDE.md for the index."""

from l7r.diagram import check_village
from l7r.diagram.settlement import Settlement
from tests.settlement._builders import _crop_settlement, _nuc_village, _scatter_base_points, _town


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


def test_grove_fits_rejects_a_belt_over_a_dry_strip():
    # the windbreak's canopy stays out of the barley exactly as it stays out of the paddy
    s = _crop_settlement()
    s.dry_polys.append([(300, 300), (500, 300), (500, 380), (300, 380)])
    assert not s._grove_fits(400, 340, 60, 30, own=[])
    assert s._grove_fits(400, 500, 60, 30, own=[])


def test_commons_keeps_scrub_off_dry_plots_and_the_crop_margin():
    # GM 2026-08-15: scrub scattered over dry hatake plots and right up against crop edges. The
    # scatter must skip DRY PLOTS (read from dry_polys, which every dry-crop path registers) as
    # well as paddies, and keep _CROP_MARGIN_FT of clearance off EVERY crop edge - the bund/balk
    # plus one cut swath (settlements/vegetation.md "Scrub stands off the crops"). Tall glyphs
    # (scraggly pines, woodland crowns) stand their own drawn reach further back, so no tip leans
    # over the crop; base points alone are asserted here (the lean is engine-side headroom).
    s = _nuc_village()  # paddy at [(640,150),(1120,150),(1120,780),(640,780)]
    quad = [(200, 300), (400, 300), (400, 500), (200, 500)]
    s.dry_polys.append(quad)
    s.block_polys.append(quad)  # both registries, as every dry-crop path does
    clr = s.px(s._CROP_MARGIN_FT) - 0.06  # 0.1-rounding slack, as in the halo tests
    for role in ("grazing", "woodland"):
        before = len(s.out)
        s.commons([(100, 150), (700, 150), (700, 650), (100, 650)], role=role)  # over the dry plot AND the paddy's W edge
        pts = _scatter_base_points(s.out[before:])
        assert pts
        for gx, gy in pts:
            assert not (200 - clr <= gx <= 400 + clr and 300 - clr <= gy <= 500 + clr), (role, gx, gy)  # dry plot + margin
            assert gx < 640 - clr, (role, gx, gy)  # paddy edge + margin


def test_commons_keeps_scrub_off_drawn_channels():
    # GM 2026-08-16 (Inashiro): grass tufts stood ON the open water of the comb's head-race.
    # _on_watercourse read M['channels'] - the hairline TOPOLOGY connectors (w 2.5) - while the
    # comb's real drawn laterals live in M['drawn_channels'], up to 14 wide on their own filleted
    # post-clip polylines. The "same manifest source" trap: the scatter must skip the DRAWN water
    # band - uniform strokes at w0, tapered runs at each piece's own width (field_channel's 7-piece
    # w0 -> w1 ladder). Base points asserted, as in the crop-margin test above.
    def _clear_of(pts, poly, half):  # min point-to-polyline distance stays outside half + pad
        for gx, gy in pts:
            for (ax, ay), (bx, by) in zip(poly, poly[1:], strict=False):
                dx, dy = bx - ax, by - ay
                t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((gx - ax) * dx + (gy - ay) * dy) / (dx * dx + dy * dy)))
                assert ((gx - ax - t * dx) ** 2 + (gy - ay - t * dy) ** 2) ** 0.5 >= half + 2 - 0.15, (gx, gy)

    s = _nuc_village()
    s.field_channel([(300, 100), (310, 700)], "#6C9CBE", 14.0, 14.0)  # a wide UNIFORM supply lateral
    s.field_channel([(120, 120), (200, 680)], "#6C9CBE", 14.0, 5.0)  # a TAPERED head-race
    uniform, taper = (ch["pts"] for ch in s.M["drawn_channels"])
    before = len(s.out)
    # role="pasture" keeps the scatter to tufts + dots (no pines/crowns, whose highlight/shadow ink
    # is offset from the base point _sparse tests) so every element is base-tested - the same idiom
    # as the urban-halo tests.
    s.commons([(60, 60), (560, 60), (560, 760), (60, 760)], role="pasture")  # laid over both laterals
    pts = _scatter_base_points(s.out[before:])
    assert pts
    _clear_of(pts, uniform, 14.0 / 2)
    _clear_of(pts, taper, 5.0 / 2)  # conservative: every piece of the taper is at least w1 wide


def test_commons_keeps_scrub_a_cut_bank_off_the_channels_but_not_the_streams():
    # GM 2026-08-16 (Inashiro, second pass): after the drawn-width fix above, tufts still seeded in
    # the 10-16 ft berm strip between the dry hem plots and the supply channels - legal under the
    # drawn-width skip (2 px pad) + the 6 ft crop margin, which between them left a bare sliver
    # mid-strip. Decision: IRRIGATION channels (M['channels'] + M['drawn_channels']) hold a
    # maintained CUT-BANK margin of _BANK_MARGIN_FT beyond the drawn water edge - the bank is
    # walked for sluice work and scythed for fodder, the same economics as the crop margin
    # (research/vegetation.md "The cut bank"). STREAMS deliberately get NO margin: a natural bank
    # is vegetated to the water's edge, and a sterile halo on the brook is the defect the
    # settlement-review pass warned against. Base points asserted, as in the tests above.
    def _min_dist(gx, gy, poly):
        best = 1e18
        for (ax, ay), (bx, by) in zip(poly, poly[1:], strict=False):
            dx, dy = bx - ax, by - ay
            t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((gx - ax) * dx + (gy - ay) * dy) / (dx * dx + dy * dy)))
            best = min(best, ((gx - ax - t * dx) ** 2 + (gy - ay - t * dy) ** 2) ** 0.5)
        return best

    s = _nuc_village()
    s.field_channel([(300, 100), (310, 700)], "#6C9CBE", 14.0, 14.0)  # a wide UNIFORM supply lateral
    s.field_channel([(120, 120), (200, 680)], "#6C9CBE", 14.0, 5.0)  # a TAPERED head-race
    uniform, taper = (ch["pts"] for ch in s.M["drawn_channels"])
    m = s.px(s._BANK_MARGIN_FT)
    before = len(s.out)
    s.commons([(60, 60), (560, 60), (560, 760), (60, 760)], role="pasture")  # laid over both laterals
    pts = _scatter_base_points(s.out[before:])
    assert pts
    for gx, gy in pts:  # every base clears drawn half-width + the cut-bank margin (w1 conservative on the taper)
        assert _min_dist(gx, gy, uniform) >= 14.0 / 2 + m - 0.15, (gx, gy)
        assert _min_dist(gx, gy, taper) >= 5.0 / 2 + m - 0.15, (gx, gy)

    s2 = _nuc_village()  # ... and the SAME scatter over a natural stream keeps grass to the bank
    stream = [[300, 100], [310, 700]]
    s2.M["streams"] = [{"poly": stream, "w": 8}]
    before = len(s2.out)
    s2.commons([(60, 60), (560, 60), (560, 760), (60, 760)], role="pasture")
    pts2 = _scatter_base_points(s2.out[before:])
    assert pts2
    assert all(_min_dist(gx, gy, [tuple(p) for p in stream]) >= 8 / 2 + 2 - 0.15 for gx, gy in pts2)  # still off the water itself
    assert any(_min_dist(gx, gy, [tuple(p) for p in stream]) < 8 / 2 + 2 + m for gx, gy in pts2), "no tuft near the stream bank - the no-margin-on-streams half of the rule has lost its witness"


def test_attach_garden_draws_and_records_two_beds():
    s = _nuc_village()
    s._attach_garden(500, 500, [(486, 500, 10, 12), (520, 500, 10, 12)])
    beds = s.M["gardens"]
    assert len(beds) == 2 and all(b["of"] == [500, 500] and len(b["poly"]) == 4 for b in beds)


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


def test_on_watercourse_detects_stream_and_channel_beds():
    s = Settlement(600, 600, seed=1)
    s.M["streams"] = [{"poly": [[100, 100], [400, 100]], "w": 8}]
    s.M["channels"] = [{"poly": [[100, 300], [400, 300]], "w": 4}]
    assert s._on_watercourse(250, 100) and s._on_watercourse(250, 300)  # on the stream / channel bed
    assert not s._on_watercourse(250, 200)  # clear ground between them


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


def test_every_roofed_feature_is_a_canopy_keepout():
    """THE RATCHET behind "no tree is drawn on a roof". The canopy keep-out was a hand list until a
    reviewer found scrub on a theater stage; settlement.py cannot import check_village (circular),
    so the roofed set is written out - and this holds it against the real overlap registry. Every
    solid feature must be either a canopy keep-out or explicitly named open-air ground, so a new
    feature cannot silently fall outside both the way `theater_stage` did."""

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
