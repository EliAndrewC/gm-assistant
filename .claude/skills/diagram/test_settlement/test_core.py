"""Split from test_settlement.py by feature 025 - see test_settlement/CLAUDE.md for the index."""

import math
import os
import random
import tempfile

import pytest

from settlement import Settlement, roll_merchant_estate_count, roll_torii_count, village_population
from test_settlement._builders import _cap020, _castle_map, _city, _crop_settlement, _max_turn_deg, _memo_city, _shoelace, _torii_city, _town
from waterfields import polyline_cum, supply_bank_clearance


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


def test_village_population_draws_from_the_weighted_distribution():
    import random
    from collections import Counter

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


def test_shrine_hall_rolls_torii_count_per_temple():
    # the 2026-07-23 full re-roll: torii=[...] is avenue GEOMETRY; the COUNT is a seeded
    # per-temple roll on the tier's TORII_WEIGHTS column, recorded on the religious rec
    import random as _rr

    expect = roll_torii_count("city", _rr.Random(9 * 977 + 600 * 31 + 500 * 57))
    s = _torii_city()
    assert s.M["religious"][-1]["torii_count"] == expect
    assert len(s.M["torii"]) == expect


def test_roll_torii_count_distributions():
    # the GM's tier weights (2026-07-21): 1/3/7 only, village 60/30/10, town 30/60/10,
    # city 30/40/30, capital 10/60/30; unknown scales roll the conservative village column
    import collections
    import random as _random

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


def test_build_comb_supply_banks_hems_bunds_onto_the_channel_banks():
    # GM 2026-08-15 (Inashiro): a bund bordering the irrigated channel is the channel's BANK - it
    # runs parallel to and along the water's edge, never down the middle of the water.
    # supply_banks=True holds every carved corner off every supply stroke by its local half-width
    # + BANK_MARGIN*grain, perpendicular to the stroke; the default (False) keeps the legacy carve
    # so the hand-authored pool re-runs byte-identical.
    from waterfields import BANK_MARGIN, build_comb

    def buried_corners(net, line_off):
        n = 0
        for c in net["channels"]:
            if c.get("role") == "drain":
                continue
            pts = [(float(p[0]), float(p[1])) for p in c["pts"]]
            if len(pts) < 2:
                continue
            cum = polyline_cum(pts)
            w0, w1 = float(c["w"]), float(c.get("w_tail", c["w"]))
            for pl in net["plots"]:
                for q in pl["poly"]:
                    gap, halfw, past, _foot, _nrm = supply_bank_clearance(q, pts, w0, w1, cum)
                    if not past and gap < halfw + line_off:
                        n += 1
        return n

    kw = dict(down_deg=90, field_fall=1260, offtakes_a=(0.32, 0.7), offtakes_b=(0.5,))
    net = build_comb(1900, 2680, (760, 320), 5, supply_banks=True, **kw)
    assert any(c.get("role") != "drain" for c in net["channels"])  # the comb drew supply strokes
    assert buried_corners(net, BANK_MARGIN - 0.15) == 0  # every corner clear of every bank (the gate's own line)
    # ... and the legacy default really is the legacy carve: the same comb without the flag lays
    # sector-boundary bunds ON the thread centerlines, i.e. inside the drawn water. If this half
    # ever goes green, the fix has become the default and the flag (plus this guard) can retire.
    assert buried_corners(build_comb(1900, 2680, (760, 320), 5, **kw), -0.15) > 0


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


def test_roll_merchant_estate_count_distribution():
    # 30/40/30 for 1/2/3 at city scale - the granted-privilege distribution (MERCHANT_ESTATE_WEIGHTS)
    import collections
    import random as _rr

    from settlement import MERCHANT_ESTATE_WEIGHTS

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


def test_near_ring_paddy_skips_cells_over_the_orientation_cap():
    # ~300px+ cells exceed the 80000px bbox cap and are skipped by the size guard; coarser cells therefore
    # place fewer basins than fine ones (the oversized ones drop out)
    coarse = _town().near_ring_paddy((0, 0, 1000, 1000), seed=8, cell_ft=320)
    fine = _town().near_ring_paddy((0, 0, 1000, 1000), seed=8, cell_ft=150)
    assert isinstance(coarse, int) and fine > coarse


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
    s4 = _cap020()
    n4 = len(s4.top)
    s4.sluice_gate(500, 500, span=26)  # a 66 ft leat: the frame spans bank to bank
    assert 'x="-13.0"' in "".join(s4.top[n4:])  # the posts stand on the abutments, not mid-water


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


def test_a_homestead_may_not_stand_in_a_neighbours_drying_sun():
    """THE RATCHET for the sun corridor (GM 2026-08-13, researched in research/homesteads.md).

    A minka's ~20 ft ridge throws 39 ft of shadow by 9am in the threshing month, so a farmhouse
    that close south of a yard takes its drying day. Three things are pinned: the rule is OFF by
    default (the whole hand-authored pool depends on that - turning it on re-packs every nucleated
    map), it refuses a bundle in BOTH directions once on, and it lets a homestead sit clear."""

    def bed():
        s = Settlement(1400, 1400, seed=3)
        s.meta(name="Sun", scale="hamlet", ftpx=1, toscale=True, households=12, nucleated=True)
        s._nucleated = True
        return s

    off = bed()
    assert off._sun_corridor_ok({"house": (700, 700, 46, 28), "yard": (700, 745, 37, 26)}), "OFF by default - the legacy pool depends on it"

    on = bed()
    on.sun_corridor(39)
    # a yard standing 20 ft north of this candidate house: the candidate would shade it
    on.M["houses"].append({"x": 700, "y": 600, "w": 46, "h": 28, "geom": {"yard": (700, 645, 37, 26)}})
    assert not on._sun_corridor_ok({"house": (700, 700, 46, 28), "yard": (700, 745, 37, 26)}), "a house may not shade a yard already placed"
    # ...and the mirror: a house already standing, and the candidate's own yard in its shadow
    on2 = bed()
    on2.sun_corridor(39)
    on2.M["houses"].append({"x": 700, "y": 800, "w": 46, "h": 28, "geom": None})
    assert not on2._sun_corridor_ok({"house": (700, 700, 46, 28), "yard": (700, 745, 37, 26)}), "a yard may not sit in a standing house's shadow"
    # ...and a homestead well clear of both is allowed
    on3 = bed()
    on3.sun_corridor(39)
    on3.M["houses"].append({"x": 700, "y": 900, "w": 46, "h": 28, "geom": {"yard": (700, 945, 37, 26)}})
    assert on3._sun_corridor_ok({"house": (700, 700, 46, 28), "yard": (700, 745, 37, 26)}), "clear ground must still be offered"


def test_bund_beans_drop_beads_buried_by_a_later_plot():
    # two overlapping squares: the filler (appended last, like _fill_wedges' tiles) laps 60px
    # onto the host, burying the host's east bund (x=400) under its fill. Beads laid along that
    # stretch must be dropped (GM 2026-08-15: Inashiro's green dots floating mid-paddy), while
    # the filler's own beads over the host's interior survive - the filler's stroke paints last,
    # so it IS the visible bund. Seed 0 is pinned because it beads the host's east edge both runs
    # (the R stream is positional per plot, so the pin is stable).
    import random as _random

    from waterfields import _bund_beans, _seg_d

    host = {"poly": [(200.0, 200.0), (400.0, 200.0), (400.0, 400.0), (200.0, 400.0)]}
    filler = {"poly": [(340.0, 150.0), (500.0, 150.0), (500.0, 450.0), (340.0, 450.0)]}
    alone = _bund_beans(_random.Random(0), [host], frac=1.0)
    both = _bund_beans(_random.Random(0), [host, filler], frac=1.0)
    assert [b for b in alone if b[0] == 400.0 and 205 < b[1] < 395]  # host east edge WAS beaded
    assert not [b for b in both if b[0] == 400.0 and 205 < b[1] < 395]  # ...and dropped when buried
    assert [b for b in both if b not in alone]  # the filler's own beads survive
    # the segment-distance helper's degenerate branch: a zero-length segment is a point
    assert _seg_d(5.0, 5.0, (1.0, 1.0), (1.0, 1.0)) == pytest.approx(math.hypot(4.0, 4.0))


def test_bund_beans_drop_beads_under_the_ditch_net():
    # a channel running down the host's east bund (x=400): its stroke draws late, over every
    # plot and bead, so the beads along that edge are buried under water paint and dropped -
    # the record-honesty half of the azemame fix (GM 2026-08-15). The 1-point channel is
    # unpaintable and must be skipped, not crash.
    import random as _random

    from waterfields import _bund_beans

    host = {"poly": [(200.0, 200.0), (400.0, 200.0), (400.0, 400.0), (200.0, 400.0)]}
    chan = {"pts": [(400.0, 190.0), (400.0, 410.0)], "w": 8.0, "w_tail": 4.0}
    alone = _bund_beans(_random.Random(0), [host], frac=1.0)
    both = _bund_beans(_random.Random(0), [host], frac=1.0, channels=[chan, {"pts": [(0.0, 0.0)], "w": 4.0}])
    assert [b for b in alone if b[0] == 400.0]  # the east edge was beaded
    assert not [b for b in both if b[0] == 400.0]  # ...and dropped under the stroke
    assert [b for b in both if b[0] != 400.0] == [b for b in alone if b[0] != 400.0]  # others untouched
