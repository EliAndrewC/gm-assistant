"""Split from test_settlement.py by feature 025 - see tests/settlement/CLAUDE.md for the index."""

import math
import os
import random
import re
import tempfile

import pytest

from settlement import Settlement, _centroid
from tests.settlement._builders import _inwall_settlement, _town, _village
from waterfields import hem_on_paddy


def test_ring_big_falls_back_to_plain_when_capped():
    s = _town()
    s.paddy_field((200, 200, 600, 600), "", "f", amp=20)
    s.ring(("poly", s.field_polys[0]), 20, 30, ["big"], max_big=2)  # >2 'big' requests -> the rest become 'plain'
    assert sum(1 for h in s.M["houses"] if h["kind"] == "big") <= 2


def test_taxfree_plots_with_no_interior_cells():
    # no interior plots -> _taxfree_plots is a no-op (a field whose cells all fell outside the outline)
    s = _village()
    s._taxfree_plots([], 2)
    assert s.M["taxfree"] == []


def test_water_field_accepts_a_polygon_shape():
    # water_field is normally handed a bbox 4-tuple; a POLYGON shape (list of vertices) takes the other
    # branch - the outline is grown from the poly and the bbox derived from it. The field is still recorded
    # with its irrigation ditches.
    s = _village()
    s.water_field([(150, 150), (360, 150), (360, 360), (150, 360)], "", "f", (150, 150), (360, 360), amp=10, plot=34)
    assert any(f["name"] == "f" and f["kind"] == "paddy" for f in s.M["fields"])
    assert any(d["field"] == "f" for d in s.M["field_ditches"])


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


# ---- water_field: a lateral column too SHORT to carry a ditch is skipped -------------------
def test_water_field_skips_a_lateral_column_too_short_for_a_ditch():
    # a shallow field at a COARSE plot grain: some interior columns span less than ~2.1 plots
    # between the high main and the low drain, so no lateral ditch fits there and it is skipped.
    s = Settlement(900, 900, seed=3)
    s.meta(name="V", scale="village")
    s.water_field((150, 150, 400, 320), "P", "f", (150, 150), (400, 320), amp=10, plot=100)
    assert any(fd["name"] == "f" for fd in s.M["fields"])
    assert any(d["role"] == "main" for d in s.M["field_ditches"])  # the main/drain still run


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


def test_paddy_features_cover_every_archetype_branch():
    """Feature 012: exercise _paddy_features across archetypes + many seeds so every placement branch fires
    (pond / rock / grave-island each both ways), plus the dike-pond early return. Also confirms each glyph
    draws and records its manifest key. Synthetic net: 6 plots, the first 3 flagged low
    (44 x 34 px - roomy enough that the fit-to-polygon shrink in _plot_pond accepts them)."""
    net = {"plots": [{"poly": [(float(i * 50), 0.0), (float(i * 50 + 44), 0.0), (float(i * 50 + 44), 34.0), (float(i * 50), 34.0)], "low": i < 3, "fill": "#A6C398"} for i in range(6)]}
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


def test_paddy_field_polygon_shape_records_the_field():
    # the legacy paddy_field's POLYGON branch: kept exercised here now that no pool map draws a
    # legacy quilt anymore (the towns moved to build_comb; only ad-hoc callers use this path)
    s = Settlement(W=1200, H=1200, seed=3)
    s.meta(name="Pf", scale="town", ftpx=1)
    s.paddy_field([(200, 200), (500, 220), (520, 500), (240, 520)], "", "poly-paddy", amp=14, plot=58)
    f = [f for f in s.M["fields"] if f["name"] == "poly-paddy"]
    assert f and len(f[0]["outline"]) >= 4


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


def test_draw_comb_field_drops_hem_plots_on_a_prior_fan():
    # multi-fan maps place each fan blind to the others: a hem plot landing on a PREVIOUSLY
    # recorded fan's rice is dropped via the shared hem_on_paddy predicate (the Tango fe2-into-fe1
    # incident; gated by dry_plots_clear_of_paddies). The prior fan here is a synthetic field
    # record blanketing the second comb's hem band, so every hem plot must go.
    from waterfields import build_comb

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


def test_draw_comb_field_trims_an_inwall_drain_through_the_helper():
    from waterfields import build_comb

    s = _inwall_settlement()
    net = build_comb(1000, 1000, (500, 200), 5, down_deg=90, field_fall=300)
    net["brook"] = []
    s.draw_comb_field(net, "f1", {"kind": "stream"}, inwall_drain_moat_bias=(0, 0))
    assert any((c.get("frm") or {}).get("kind") == "drain" and (c.get("to") or {}).get("kind") == "moat" and c.get("drawn") is False for c in s.M["channels"])
    assert s.M["sluice_gates"]


def test_comb_base_fill_noops_on_an_empty_net():
    """comb_base_fill draws and records nothing when the net has no plots (a degenerate field) -
    the guard that keeps a plotless comb from emitting a zero-area floor polygon."""
    s = Settlement(600, 600, seed=1)
    s.meta(name="Cb", scale="village", ftpx=2)
    s.comb_base_fill({"plots": [], "envelope": [(0, 0), (10, 0), (10, 10)]}, "empty")
    assert "empty" not in s.M.get("comb_floors", {})


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


def test_a_comb_hem_is_registered_as_CROPLAND_not_only_as_no_build_ground():
    """THE RATCHET for the 2026-08-11 engine fix (see `draw_comb_field`).

    The engine keeps two registries for cropland and they are read by different things:
    `block_polys` stops a FARMSTEAD, `dry_polys` stops a TREE, a lane, a threshing yard and the
    ground-cover scatters. `draw_comb_field` used to append to the first only, so a map built
    through it had hem plots that a house respected and a grove did not - invisible for as long as
    the clusters happened to sit away from the hem, and three simultaneous gate failures the moment
    one did not. Every hand-authored comb gen carries its own `s.dry_polys.append(...)` to
    compensate; this holds the line for the ones that do not."""
    from waterfields import build_comb

    s = Settlement(1800, 1800, seed=5)
    s.meta(name="Hem", scale="hamlet", ftpx=1, toscale=True, households=12, down_deg=90, water_flow=90)
    net = build_comb(1800, 1800, (700.0, 380.0), 5, down_deg=90, field_fall=800)
    s.draw_comb_field(net, "hem-paddies", {"kind": "stream", "stream": [(700.0, -40.0), (700.0, 380.0)]})
    assert s.M["dry_plots"], "the fixture must actually draw a dry hem, or it proves nothing"
    assert len(s.dry_polys) == len(s.M["dry_plots"]), "every DRAWN hem plot is registered as cropland"
    assert all(any(abs(v[0] - p[0]) < 0.05 and abs(v[1] - p[1]) < 0.05 for p in poly) for rec, poly in zip(s.M["dry_plots"], s.dry_polys, strict=True) for v in [rec["poly"][0]]), (
        "the registered polygon is the one that was drawn, not a re-derivation of it"
    )


def test_draw_comb_field_records_rings_and_beads():
    # the field record carries every plot ring IN DRAW ORDER plus the azemame bead points - the
    # recording bund_beans_on_bunds reads (pdims compacts a plot to extents-and-a-centroid, which
    # cannot express "this plot paints over that one's bund"). Recording is unconditional at this
    # one draw site, which is what lets the check skip legacy manifests without going silently
    # toothless on regenerated ones (GM 2026-08-15).
    from waterfields import build_comb

    s = Settlement(W=1400, H=1400, seed=5)
    s.meta(name="Rb", scale="town", ftpx=1, down_deg=90)
    net = build_comb(1400, 1400, (700, 200), 5, down_deg=90, field_fall=400)
    net["brook"] = []
    s.draw_comb_field(net, "f1", {"kind": "stream"})
    fld = s.M["fields"][-1]
    assert len(fld["plot_rings"]) == len(net["plots"])
    assert fld["plot_rings"][0] == [[round(x, 1), round(y, 1)] for x, y in net["plots"][0]["poly"]]
    assert fld["bund_beans"] == [[round(x, 1), round(y, 1)] for x, y in net["bund_beans"]]


def test_draw_comb_field_drops_beads_in_pond_water():
    # the draw-site half of the water-honesty rule: beads inside the source pond's ellipse or a
    # pocket pond's are dropped BEFORE the bead line draws and records, so dots and manifest agree
    from waterfields import build_comb

    s = Settlement(W=1400, H=1400, seed=7)
    s.meta(name="Pw", scale="town", ftpx=1, down_deg=90)
    net = build_comb(1400, 1400, (700, 200), 7, down_deg=90, field_fall=400)
    net["brook"] = []
    net["bund_beans"] = [(700.0, 1000.0), (300.0, 300.0), (500.0, 180.0)]
    s.M["field_ponds"] = [{"x": 300.0, "y": 300.0, "rx": 20.0, "ry": 15.0}]
    s.draw_comb_field(net, "f1", {"kind": "pond", "pond": (700, 1000, 60, 40)})
    assert s.M["fields"][-1]["bund_beans"] == [[500.0, 180.0]]


# --- feature 112: the composed FieldsMixin surface -----------------------------------------------
# settlement/fields.py became a package of four sub-mixins composed in fields/__init__.py. The
# guard below is the whole safety property of that split: core.py imports ONE name and the class
# must keep contributing exactly what it contributed before. Two failure modes it exists for -
# a member dropped in the move (the composed class silently loses a method, and only a generator
# that happens to call it notices), and a member defined by TWO sub-mixins (MRO picks one and
# orphans the other, with no import error, no type error, and no test failure anywhere else).
# Proven to fire against both before it was trusted - see specs/112-fields-package/tasks.md T005.

_FIELDS_SURFACE = frozenset(
    {
        # public entry points, called from pool gens, hamletgen, other engine modules and checks
        "apply_land_use",
        "bund_junctions",
        "comb_base_fill",
        "crescent_pond",
        "draw_comb_field",
        "fallow_field",
        "paddy_field",
        "pond",
        "water_field",
        # private helpers, reached through self. (several also called on an instance from tests
        # and from settlement/land/nearring.py, which is why they are part of the surface)
        "_draw_furrows",
        "_fallow_patch",
        "_mulberry_rows",
        "_paddy_features",
        "_paddy_plots",
        "_paddy_surface",
        "_pick_overlay_plots",
        "_plot_center_span",
        "_plot_grave_island",
        "_plot_pond",
        "_plot_rock",
        "_rounded_pond",
        "_rows",
        "_split_convex",
        "_taxfree_plots",
    }
)


def _fields_submixins():
    from settlement.fields.comb import CombMixin
    from settlement.fields.features import FieldFeaturesMixin
    from settlement.fields.landuse import LandUseMixin
    from settlement.fields.paddy import PaddyMixin

    return [PaddyMixin, CombMixin, LandUseMixin, FieldFeaturesMixin]


def _own_callables(cls):
    return {k for k, v in vars(cls).items() if callable(v) or isinstance(v, staticmethod)}


def test_no_pre_split_fields_member_was_lost_in_the_move():
    # SUBSET, not equality, and the reason is worth stating. Stage 2 of feature 112 decomposed the
    # three oversized methods into named private helpers, so the composed class legitimately holds
    # MORE than the pre-split 24, and will hold more again the next time a method is split. What
    # must never happen is a pre-split member going MISSING: an addition is visible in review,
    # while a subtraction is silent until whichever generator calls it happens to run. The
    # assertion therefore guards the direction that hides. The red proof still holds - deleting a
    # member names it in `missing` (specs/112-fields-package/tasks.md T005).
    composed = set().union(*(_own_callables(c) for c in _fields_submixins()))
    assert composed >= _FIELDS_SURFACE, f"missing={sorted(_FIELDS_SURFACE - composed)}"


def test_no_two_fields_submixins_define_the_same_name():
    subs = _fields_submixins()
    for i, a in enumerate(subs):
        for b in subs[i + 1 :]:
            overlap = _own_callables(a) & _own_callables(b)
            assert not overlap, f"{a.__name__} and {b.__name__} both define {sorted(overlap)} - MRO would orphan one"


def test_every_fields_member_resolves_on_settlement_itself():
    # what consumers actually rely on: the name reaching Settlement, not merely FieldsMixin
    unreachable = sorted(n for n in _FIELDS_SURFACE if not hasattr(Settlement, n))
    assert not unreachable, f"not resolvable on Settlement: {unreachable}"


def test_feature_012_archetype_constants_survived_the_split():
    # the three class-level tuples gating the in-field pond / rock / grave island. They are class
    # ATTRIBUTES, not methods, so the surface test above cannot see them - and a transformer that
    # slices a class body by its function definitions is exactly what would drop them.
    for name in ("_PADDY_POND_KINDS", "_PADDY_ROCK_KINDS", "_PADDY_GRAVE_KINDS"):
        assert isinstance(getattr(Settlement, name), tuple), name
    assert "valley_paddy" in Settlement._PADDY_POND_KINDS


def test_plot_pond_fits_the_polygon_not_the_bbox():
    """Inashiro 2026-08-16: a fan-toe WEDGE has a bounding box several times the wedge itself, and the
    bbox-sized pond spilled across neighboring plots with spoke bunds drawn through open water. A thin
    wedge must REFUSE the pond (False, nothing drawn or recorded); a roomy rectangle must take one
    whose rim stays inside the plot polygon."""
    s = Settlement(600, 600, seed=1)
    s.meta(name="W", scale="village", ftpx=1, down_deg=90)
    wedge = {"poly": [(0.0, 0.0), (90.0, 55.0), (96.0, 65.0), (0.0, 8.0)]}  # ~8 px wide sliver, 96 x 65 bbox
    assert s._plot_pond(wedge, [wedge["poly"]]) is False
    assert not s.M.get("field_ponds")
    rect = {"poly": [(100.0, 100.0), (190.0, 100.0), (190.0, 170.0), (100.0, 170.0)]}
    # a foreign ring bisecting the plot (rings OVERLAP at fan/grid seams) must refuse the pond too
    bisector = [(145.0, 90.0), (145.0, 180.0), (150.0, 180.0), (150.0, 90.0)]
    assert s._plot_pond(rect, [rect["poly"], bisector]) is False
    assert not s.M.get("field_ponds")
    assert s._plot_pond(rect, [rect["poly"]]) is True
    (fp,) = s.M["field_ponds"]
    for a in [i * math.pi / 12 for i in range(24)]:
        px, py = fp["x"] + fp["rx"] * math.cos(a), fp["y"] + fp["ry"] * math.sin(a)
        assert 100 <= px <= 190 and 100 <= py <= 170  # every rim point inside the plot
