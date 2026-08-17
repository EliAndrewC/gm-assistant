"""Gate segments (streams and field ditches; keys 0306-0324) - bodies verbatim, registry order preserved."""

import math
from collections.abc import Sequence
from typing import Any

from l7r.diagram.settlement import sat_overlap

from .common_01_geometry import Poly, Pt, point_in_poly, rect_corners, seg_dist, segments_cross
from .common_02_overlap_policy import GridIndex
from .common_03_capacity import _UNBOUND, _kept

# natural streams: those that declare anchors must connect them (e.g. a forest
# brook into a pond); and NO stream may run through a farm field


def _seg_0306__stream_through_field(
    *,
    e: Any = _UNBOUND,
    frm: Any = _UNBOUND,
    i: Any = _UNBOUND,
    k: Any = _UNBOUND,
    n: Any = _UNBOUND,
    poly: Any = _UNBOUND,
    pt: Any = _UNBOUND,
    pts: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    to: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 306 (stream_through_field) - body verbatim from the legacy gate() (feature 022)."""

    def stream_through_field(poly: Poly, outline: Poly, frm: Any, to: Any) -> bool:
        # A stream ANCHORED to the field's drain/outfall (a drain-fed brook carrying the runoff off-map) or to
        # the field itself legitimately CONNECTS there, so it starts (or ends) inside the field envelope. Trim
        # the run from that anchored end up to where it first LEAVES the field, then check only the rest - so the
        # legitimate connection is allowed, but a stream that RE-ENTERS or cuts across the crop still fires.
        # ON the outline counts as anchored, not merely INSIDE it (2026-08-12). A comb's collector
        # ends where the planted extent does, so its outfall routinely lands within a pixel of the
        # field's own boundary - inside by the geometry, outside by the rounding. Trimming only the
        # strictly-inside case leaves such a brook measured from its anchor point, and then NO route
        # out of it can pass: the collector runs ALONG the boundary there, so every bearing within
        # `drainage_junction_smooth`'s 65 degrees of it clips the crop and every bearing that clears
        # the crop is a hairpin. Measured on the case that found this: the clear bearings began 73
        # degrees off the drain's heading. The rule this check exists for - a stream RE-ENTERING or
        # cutting across the crop - is untouched; only the anchor's own tolerance moves.
        ANCHOR_TOL = 2.0

        def _anchored_end(pt: Pt) -> bool:
            return point_in_poly(pt[0], pt[1], outline) or min(seg_dist(pt[0], pt[1], outline[i], outline[(i + 1) % len(outline)]) for i in range(len(outline))) <= ANCHOR_TOL

        pts = list(poly)
        if frm and frm.get("kind") in ("drain", "field"):
            while len(pts) > 1 and _anchored_end(pts[0]):
                pts = pts[1:]
        if to and to.get("kind") in ("drain", "field"):
            while len(pts) > 1 and _anchored_end(pts[-1]):
                pts = pts[:-1]
        if any(point_in_poly(px, py, outline) for px, py in pts):
            return True
        n = len(outline)
        return any(segments_cross(pts[k], pts[k + 1], outline[e], outline[(e + 1) % n]) for k in range(len(pts) - 1) for e in range(n))

    return _kept(locals(), ('stream_through_field',))


def _seg_0307__through() -> dict[str, Any]:
    """Gate segment 307 (through) - body verbatim from the legacy gate() (feature 022)."""
    through = []  # type: ignore[var-annotated]
    return _kept(locals(), ('through',))


def _seg_0308__stream_source_anchored(
    *,
    M: Any = _UNBOUND,
    anchored: Any = _UNBOUND,
    check: Any = _UNBOUND,
    f: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    frm: Any = _UNBOUND,
    idx: Any = _UNBOUND,
    poly: Any = _UNBOUND,
    st: Any = _UNBOUND,
    stream_through_field: Any = _UNBOUND,
    through: Any = _UNBOUND,
    to: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 308 (stream_end_anchored, stream_source_anchored) - body verbatim from the legacy gate() (feature 022)."""
    for idx, st in enumerate(M.get("streams", [])):
        poly, frm, to = st["poly"], st.get("frm"), st.get("to")
        if frm and to:
            check(f"stream_source_anchored[{idx}]", anchored(poly[0], frm), f"start {poly[0]} not anchored to {frm}")
            check(f"stream_end_anchored[{idx}]", anchored(poly[-1], to), f"end {poly[-1]} not anchored to {to}")
        through += [f["name"] for f in fields if stream_through_field(poly, f["outline"], frm, to)]
    return _kept(locals(), ('f', 'frm', 'idx', 'poly', 'st', 'through', 'to'))


def _seg_0309__streams_avoid_fields(*, check: Any = _UNBOUND, through: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 309 (streams_avoid_fields) - body verbatim from the legacy gate() (feature 022)."""
    check("streams_avoid_fields", not through, f"stream(s) run through field(s): {sorted(set(through))}")
    return _kept(locals(), ())


# WATER CHANNELS TURN ONLY THROUGH OBTUSE ANGLES (>90 deg). A canal/ditch does not make an acute hairpin
# without bizarre topology, so at every interior vertex the incoming and outgoing segments must not fold
# back on each other (dot >= 0 => turn <= 90 deg => interior angle >= 90 deg). Applies to every recorded
# watercourse: irrigation channels, natural streams, and the in-field irrigation ditches.


def _seg_0310__acute_turns(
    *, ax: Any = _UNBOUND, ay: Any = _UNBOUND, bad: Any = _UNBOUND, bx: Any = _UNBOUND, by: Any = _UNBOUND, i: Any = _UNBOUND, la: Any = _UNBOUND, lb: Any = _UNBOUND, poly: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 310 (acute_turns, bad) - body verbatim from the legacy gate() (feature 022)."""

    def acute_turns(poly: Poly) -> list[tuple[int, int]]:
        bad: list[tuple[int, int]] = []
        for i in range(1, len(poly) - 1):
            ax, ay = poly[i][0] - poly[i - 1][0], poly[i][1] - poly[i - 1][1]
            bx, by = poly[i + 1][0] - poly[i][0], poly[i + 1][1] - poly[i][1]
            la, lb = math.hypot(ax, ay), math.hypot(bx, by)
            if la < 3 or lb < 3:
                continue  # ignore jitter-length segments
            if (ax * bx + ay * by) / (la * lb) < -0.02:  # cos(turn) < 0 => turn > 90 deg => acute interior angle (1 deg tol)
                bad.append((round(poly[i][0]), round(poly[i][1])))
        return bad

    return _kept(locals(), ('acute_turns', 'bad'))


def _seg_0311__acute() -> dict[str, Any]:
    """Gate segment 311 (acute) - body verbatim from the legacy gate() (feature 022)."""
    acute = []  # type: ignore[var-annotated]
    return _kept(locals(), ('acute',))


def _seg_0312__acute_1(*, M: Any = _UNBOUND, acute: Any = _UNBOUND, acute_turns: Any = _UNBOUND, c: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 312 (acute, c) - body verbatim from the legacy gate() (feature 022)."""
    for c in M.get("channels", []):
        acute += acute_turns(c["poly"])
    return _kept(locals(), ('acute', 'c'))


def _seg_0313__acute_2(*, M: Any = _UNBOUND, acute: Any = _UNBOUND, acute_turns: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 313 (acute, st) - body verbatim from the legacy gate() (feature 022)."""
    for st in M.get("streams", []):
        acute += acute_turns(st["poly"])
    return _kept(locals(), ('acute', 'st'))


def _seg_0314__acute_3(*, M: Any = _UNBOUND, acute: Any = _UNBOUND, acute_turns: Any = _UNBOUND, fdt: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 314 (acute, fdt) - body verbatim from the legacy gate() (feature 022)."""
    for fdt in M.get("field_ditches", []):
        acute += acute_turns(fdt["poly"])
    return _kept(locals(), ('acute', 'fdt'))


def _seg_0315__water_channels_obtuse_turns(*, acute: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 315 (water_channels_obtuse_turns) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "water_channels_obtuse_turns",
        not acute,
        f"water channel(s) make an ACUTE (<90 deg) turn at {sorted(set(acute))[:5]} - a ditch/canal only bends through obtuse angles; an acute hairpin implies impossible topology",
    )
    return _kept(locals(), ())


# DRY-FIELD FURROWS vary PER PLOT - no two EDGE-ADJACENT dry plots may run their ridges the SAME way.
# Fragmented dry holdings were a mosaic of family strips, each plowed to its OWN orientation (the patchwork-
# quilt look); ridge-along-contour is a STEEP-slope erosion measure, NOT forced on a gentle valley margin.
# A furrow is an undirected LINE, so "same direction" is compared mod pi. WHY: settlements.md 'Water-first v2' crop.
# A steep / terraced village may declare CONTOUR furrows (meta.dry_furrows_vary=False - the rows converge
# onto the contour for erosion control), in which case aligned rows are correct and variation is NOT required.


def _seg_0316__dry_plots(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 316 (dry_plots) - body verbatim from the legacy gate() (feature 022)."""
    dry_plots = M.get("dry_plots", [])
    return _kept(locals(), ('dry_plots',))


def _seg_0317__dry_plot_furrows_vary(
    *,
    M: Any = _UNBOUND,
    _a: Any = _UNBOUND,
    _dv_rad: Any = _UNBOUND,
    _dv_sides: Any = _UNBOUND,
    ai: Any = _UNBOUND,
    bi: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d: Any = _UNBOUND,
    dcen: Any = _UNBOUND,
    dry_plots: Any = _UNBOUND,
    i: Any = _UNBOUND,
    p: Any = _UNBOUND,
    pp: Any = _UNBOUND,
    same: Any = _UNBOUND,
    v: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 317 (dry_plot_furrows_vary) - body verbatim from the legacy gate() (feature 022)."""
    if len(dry_plots) >= 4 and M.get("meta", {}).get("dry_furrows_vary", True):
        dcen = [(sum(v[0] for v in p["poly"]) / len(p["poly"]), sum(v[1] for v in p["poly"]) / len(p["poly"])) for p in dry_plots]
        # edge-adjacency radius derives from the plots' OWN size (mean side length x1.25), capped at the
        # legacy 50px: a fixed radius is secretly a plot-size assumption, and the grain-scaled city plots
        # (~27px sides) made 50px lasso plots two rows apart while a hamlet's 1 ft/px plots sit right at
        # the old tuning - the cap keeps every fine-grain map's behavior byte-for-byte identical (2026-07-21)
        _dv_sides = []
        for p in dry_plots:
            pp = p["poly"]
            _a = abs(sum(pp[i][0] * pp[(i + 1) % len(pp)][1] - pp[(i + 1) % len(pp)][0] * pp[i][1] for i in range(len(pp)))) / 2
            _dv_sides.append(_a**0.5)
        _dv_rad = min(50.0, 1.25 * (sum(_dv_sides) / len(_dv_sides)))
        same = []
        for ai in range(len(dry_plots)):
            for bi in range(ai + 1, len(dry_plots)):
                if (dcen[ai][0] - dcen[bi][0]) ** 2 + (dcen[ai][1] - dcen[bi][1]) ** 2 >= _dv_rad**2:
                    continue  # only EDGE-adjacent plots (a shared boundary; see _dv_rad above)
                d = abs(dry_plots[ai]["theta"] - dry_plots[bi]["theta"]) % math.pi
                if min(d, math.pi - d) <= 0.10:  # within ~6 deg reads as the SAME row direction
                    same.append((round(dcen[ai][0]), round(dcen[ai][1])))
        check(
            "dry_plot_furrows_vary",
            not same,
            f"neighboring dry-field plot(s) run their furrows the SAME way {same[:3]} - fragmented family strips "
            f"were each plowed to their own orientation, so adjacent plots must differ in row direction",
        )
    return _kept(locals(), ('_a', '_dv_rad', '_dv_sides', 'ai', 'bi', 'd', 'dcen', 'i', 'p', 'pp', 'same', 'v'))


# DRY-PLOT SEAMS ARE SHARED LINES: the hem tiles its plots column by column along the supply canal,
# so the boundary between two neighboring plots is ONE line both quads lie on. A generator that
# offsets each column along its own chord's normal instead opens a wedge at every canal bend - bare
# ground on a convex bend, a lap on a concave one - growing with upslope depth (GM caught it on
# Inashiro, 2026-08-16: "A few of them seem to overlap slightly, and a few of them seem to have
# little bits of space between them because the borders of those crop fields are not exactly at the
# same angle"; the worst Inashiro pair lapped 245 sq ft). Two clauses, both manifest-only:
# (a) LAP - no two dry plots overlap once each is shrunk a hair about its centroid (the shrink
#     absorbs the 0.1 px manifest rounding; a real lap wedge is px-wide and survives it);
# (b) GAP - where two plots MEET at a shared corner with same-heading edges, those edges must be
#     collinear: the shorter edge's far end may not diverge laterally off the longer edge's line.
# Ragged OUTER edges (per-column depth) are untouched - raggedness lives at the ENDS of seams as
# steps along the shared line, never as daylight or lap between plots. Family: gap VERDICT - both
# clauses measure real plot corners/edges, no centers, no aggregates.


def _seg_0596__dry_plot_seams_shared(*, check: Any = _UNBOUND, dry_plots: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 596 (dry_plot_seams_shared) - hand-added 2026-08-16 (numbered past the legacy
    range like _seg_0595; registered between 0317 and 0318, beside the dry-plot checks whose
    `dry_plots` binding it shares). New-style: temps stay function-local, writes=()."""
    _ds_corner2 = 1.5**2  # corners this close (px^2) are the SAME seam endpoint, drawn twice
    _ds_lat_tol = 1.2  # px of lateral divergence at the far end - manifest rounding is ~0.15
    bad: list[tuple[str, int, int]] = []
    if len(dry_plots) >= 2:
        polys: list[list[tuple[float, float]]] = [[(float(v[0]), float(v[1])) for v in p["poly"]] for p in dry_plots]
        shrunk: list[list[tuple[float, float]]] = []
        for pp in polys:
            cx = sum(q[0] for q in pp) / len(pp)
            cy = sum(q[1] for q in pp) / len(pp)
            shrunk.append([(cx + (q[0] - cx) * 0.985, cy + (q[1] - cy) * 0.985) for q in pp])
        boxes = [(min(q[0] for q in pp), min(q[1] for q in pp), max(q[0] for q in pp), max(q[1] for q in pp)) for pp in polys]
        for ai in range(len(polys)):
            for bi in range(ai + 1, len(polys)):
                if boxes[ai][2] < boxes[bi][0] - 2 or boxes[bi][2] < boxes[ai][0] - 2 or boxes[ai][3] < boxes[bi][1] - 2 or boxes[bi][3] < boxes[ai][1] - 2:
                    continue
                if sat_overlap(shrunk[ai], shrunk[bi]):
                    bad.append(("lap", round((boxes[ai][0] + boxes[bi][2]) / 2), round((boxes[ai][1] + boxes[bi][3]) / 2)))
                    continue
                pa, pb = polys[ai], polys[bi]
                for ci in range(len(pa)):
                    for cj in range(len(pb)):
                        a, b = pa[ci], pb[cj]
                        if (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 > _ds_corner2:
                            continue
                        # the two edges emanating from each plot's copy of the shared corner
                        for ea in (pa[(ci + 1) % len(pa)], pa[ci - 1]):
                            ax, ay = ea[0] - a[0], ea[1] - a[1]
                            al = math.hypot(ax, ay) or 1.0
                            for eb in (pb[(cj + 1) % len(pb)], pb[cj - 1]):
                                bx, by = eb[0] - b[0], eb[1] - b[1]
                                bl = math.hypot(bx, by) or 1.0
                                if (ax * bx + ay * by) / (al * bl) < 0.9:
                                    continue  # not the same heading - a corner where unrelated edges meet
                                ln = min(al, bl)
                                # lateral offset of b's edge at arc-length ln off a's edge line
                                px, py = b[0] + bx / bl * ln - a[0], b[1] + by / bl * ln - a[1]
                                if abs(px * ay / al - py * ax / al) > _ds_lat_tol:
                                    bad.append(("gap", round(a[0]), round(a[1])))
    check(
        "dry_plot_seams_shared",
        not bad,
        f"dry-plot seam defect(s) {sorted(set(bad))[:5]} - hem plots tiled along one canal must share their seams as single straight lines: a 'lap' is two plots overlapping, a 'gap' is a bare wedge opening between same-heading edges from a shared corner; both mean the columns were offset along different normals (waterfields._miter_normals is the shared-seam mechanism)",
    )
    return _kept(locals(), ())


# BUILDINGS AND WORK YARDS STAY OFF THE DRY PLOTS: a hem of barley/soy strips (or an urban
# vegetable tract) is CROPLAND, not building ground - a farmstead may ABUT a plot, never stand
# on it. The dry plots were classified in the overlap registry but no check actually TESTED
# structures against them, and placement guarded them center-only (block_polys), so a house
# nudged for its yard - or a ring house at the envelope gap - could stand half its footprint
# on a hem strip (GM caught farmsteads on Tango's fn1/nw1 hems, 2026-07). Footprints are
# shrunk ~6% so a plot ABUTTING a wall does not false-fire; real overlap does.


def _seg_0318__dp(*, M: Any = _UNBOUND, dp: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 318 (dp, dry_polys_c) - body verbatim from the legacy gate() (feature 022)."""
    dry_polys_c = [dp["poly"] for dp in M.get("dry_plots", [])]
    return _kept(locals(), ('dp', 'dry_polys_c'))


def _seg_0319__structures_clear_of_dry_plots(
    *,
    M: Any = _UNBOUND,
    _dp: Any = _UNBOUND,
    _dp_grid: Any = _UNBOUND,
    _dxs: Any = _UNBOUND,
    _dys: Any = _UNBOUND,
    check: Any = _UNBOUND,
    dry_polys_c: Any = _UNBOUND,
    fc: Any = _UNBOUND,
    g: Any = _UNBOUND,
    gr: Any = _UNBOUND,
    gro_dry: Any = _UNBOUND,
    gx_: Any = _UNBOUND,
    gy_: Any = _UNBOUND,
    i: Any = _UNBOUND,
    it: Any = _UNBOUND,
    j: Any = _UNBOUND,
    mkey: Any = _UNBOUND,
    on_dry: Any = _UNBOUND,
    poly: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    q: Any = _UNBOUND,
    qx: Any = _UNBOUND,
    qy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 319 (groves_clear_of_dry_plots, structures_clear_of_dry_plots) - body verbatim from the legacy gate() (feature 022)."""
    if dry_polys_c:
        on_dry = []
        # INDEXED like _hq_covered (2026-07-25): this was every structure against every dry plot with
        # a full corner/crossing test - 3.5M segments_cross calls on a city, the gate's #2 cost after
        # the head-band sampler. The grid prunes to plots whose bbox can reach the footprint; the
        # exact test below is unchanged, so the verdicts are identical.
        _dp_grid = GridIndex(64.0)
        for _dp in dry_polys_c:
            _dxs = [q[0] for q in _dp]
            _dys = [q[1] for q in _dp]
            _dp_grid.add(min(_dxs), min(_dys), max(_dxs), max(_dys), _dp)
        for mkey in ("houses", "buildings", "threshing_yards", "flophouses", "storehouses", "cemeteries", "cremation_grounds", "ossuaries", "mausoleums"):
            for it in M.get(mkey, []) or []:
                fc = rect_corners({"x": it["x"], "y": it["y"], "w": it.get("w", 20), "h": it.get("h", 14), "rot": it.get("rot", 0)})
                fc = [(it["x"] + (px - it["x"]) * 0.94, it["y"] + (py - it["y"]) * 0.94) for px, py in fc]
                for poly in _dp_grid.near_rect(min(q[0] for q in fc), min(q[1] for q in fc), max(q[0] for q in fc), max(q[1] for q in fc)):
                    if (
                        any(point_in_poly(px, py, poly) for px, py in fc)
                        or any(point_in_poly(qx, qy, fc) for qx, qy in poly)
                        or any(segments_cross(fc[i], fc[(i + 1) % 4], poly[j], poly[(j + 1) % len(poly)]) for i in range(4) for j in range(len(poly)))
                    ):
                        on_dry.append((round(it["x"]), round(it["y"])))
                        break
        check(
            "structures_clear_of_dry_plots",
            not on_dry,
            f"building(s)/work yard(s) standing ON a dry crop plot: {sorted(set(on_dry))[:6]} - the hem strips and garden tracts are cropland; a farmstead may abut a plot but never overlap it",
        )
        # ... and the WINDBREAK TREES stay off the crops too: a homestead grove hugs the paddy bund
        # but its canopy clumps must not stand in a dry plot (same rule as groves_clear_of_lanes)
        gro_dry = []
        for g in M.get("village_groves", []):
            gr = g.get("r", 10)
            for gx_, gy_ in g.get("clumps", []):
                if any(point_in_poly(gx_, gy_, poly) or min(seg_dist(gx_, gy_, poly[j], poly[(j + 1) % len(poly)]) for j in range(len(poly))) < gr * 0.75 for poly in dry_polys_c):
                    gro_dry.append((round(gx_), round(gy_)))
        check(
            "groves_clear_of_dry_plots",
            not gro_dry,
            f"windbreak canopy clump(s) standing in a dry crop plot: {sorted(set(gro_dry))[:6]} - a grove may hug a plot's edge, but its trees do not grow in the crop",
        )
    return _kept(locals(), ('_dp', '_dp_grid', '_dxs', '_dys', 'fc', 'g', 'gr', 'gro_dry', 'gx_', 'gy_', 'i', 'it', 'j', 'mkey', 'on_dry', 'poly', 'px', 'py', 'q', 'qx', 'qy'))


# FUNERARY GROUNDS STAND CLEAR OF THE FIELDS: a burial / cremation ground sits in open ground
# BESIDE the farmland, never ON a paddy's body or its irrigation ditches (GM, 2026-07: Nagahara's
# cremation ground sat on the far-bank comb's main ditch AND its dry plots). funerary_set_back_from_water
# keeps graves off open WATER + a creek-margin off field EDGES, and the cremation ground is exempt
# from that water rule (a fire site) - but a funerary footprint sitting IN a field interior or ON a
# field ditch is wrong for every funerary kind, cremation included. Field-EDGE abutment is fine
# (that is the set-back's job); this catches the footprint standing inside the cropped field.


def _seg_0320__f_1(*, M: Any = _UNBOUND, f: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 320 (f, fld_outlines) - body verbatim from the legacy gate() (feature 022)."""
    fld_outlines = [f["outline"] for f in M.get("fields", [])]
    return _kept(locals(), ('f', 'fld_outlines'))


def _seg_0321__d(*, M: Any = _UNBOUND, d: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 321 (d, fdit) - body verbatim from the legacy gate() (feature 022)."""
    fdit = [d["poly"] for d in M.get("field_ditches", [])]
    return _kept(locals(), ('d', 'fdit'))


def _seg_0322__funerary_clear_of_fields(
    *,
    M: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    dp: Any = _UNBOUND,
    fc: Any = _UNBOUND,
    fdit: Any = _UNBOUND,
    fld_outlines: Any = _UNBOUND,
    inside_field: Any = _UNBOUND,
    it: Any = _UNBOUND,
    k: Any = _UNBOUND,
    mkey: Any = _UNBOUND,
    ol: Any = _UNBOUND,
    on_ditch: Any = _UNBOUND,
    on_field: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 322 (funerary_clear_of_fields) - body verbatim from the legacy gate() (feature 022)."""
    if fld_outlines or fdit:
        on_field = []
        for mkey in ("cemeteries", "cremation_grounds", "ossuaries", "mausoleums"):
            for it in M.get(mkey, []) or []:
                fc = rect_corners({"x": it["x"], "y": it["y"], "w": it.get("w", 40), "h": it.get("h", 28), "rot": it.get("rot", 0)})
                fc = [(it["x"] + (px - it["x"]) * 0.9, it["y"] + (py - it["y"]) * 0.9) for px, py in fc]
                inside_field = any(point_in_poly(px, py, ol) for ol in fld_outlines for px, py in fc)
                on_ditch = any(seg_dist(cx, cy, dp[k], dp[k + 1]) < 8 for dp in fdit for (cx, cy) in fc for k in range(len(dp) - 1))
                if inside_field or on_ditch:
                    on_field.append((round(it["x"]), round(it["y"])))
        check(
            "funerary_clear_of_fields",
            not on_field,
            f"funerary ground(s) standing on a field or its ditches: {sorted(set(on_field))[:4]} - a burial / "
            f"cremation ground sits in open ground BESIDE the farmland, not on the paddy body or its irrigation ditches",
        )
    return _kept(locals(), ('cx', 'cy', 'dp', 'fc', 'inside_field', 'it', 'k', 'mkey', 'ol', 'on_ditch', 'on_field', 'px', 'py'))


# EVERY IN-FIELD IRRIGATION DITCH TERMINATES AT A DITCH THAT LEAVES THE FIELD - no channel runs to the
# middle of a field and dead-ends. Concretely: each LATERAL's two ends sit on the MAIN or the DRAIN (which
# in turn is fed by a pond channel / emptied by an off-map or cascade channel, so the whole net exits to
# the pond or the map edge). Off-map fields are exempt (their water is implied beyond the frame).


def _seg_0323__ditches(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 323 (ditches) - body verbatim from the legacy gate() (feature 022)."""
    ditches = M.get("field_ditches", [])
    return _kept(locals(), ('ditches',))


def _seg_0324__field_ditches_terminate(
    *,
    M: Any = _UNBOUND,
    _by_field: Any = _UNBOUND,
    _deg: Any = _UNBOUND,
    _ds: Any = _UNBOUND,
    _forks: Any = _UNBOUND,
    _grounds: Any = _UNBOUND,
    _tip_off: Any = _UNBOUND,
    _tip_slack: Any = _UNBOUND,
    _tip_trunks: Any = _UNBOUND,
    blunt: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d: Any = _UNBOUND,
    d0: Any = _UNBOUND,
    dangling: Any = _UNBOUND,
    ditches: Any = _UNBOUND,
    e: Any = _UNBOUND,
    end: Any = _UNBOUND,
    fd: Any = _UNBOUND,
    find: Any = _UNBOUND,
    fname: Any = _UNBOUND,
    fork_deliveries: Any = _UNBOUND,
    frm: Any = _UNBOUND,
    fx: Any = _UNBOUND,
    fy: Any = _UNBOUND,
    grounded: Any = _UNBOUND,
    has_sink: Any = _UNBOUND,
    has_source: Any = _UNBOUND,
    i: Any = _UNBOUND,
    j: Any = _UNBOUND,
    k: Any = _UNBOUND,
    lat: Any = _UNBOUND,
    m: Any = _UNBOUND,
    members: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    n: Any = _UNBOUND,
    near_any: Any = _UNBOUND,
    pa: Any = _UNBOUND,
    parent: Any = _UNBOUND,
    pb: Any = _UNBOUND,
    pl: Any = _UNBOUND,
    pond_is_source: Any = _UNBOUND,
    pt: Any = _UNBOUND,
    r: Any = _UNBOUND,
    role: Any = _UNBOUND,
    segs: Any = _UNBOUND,
    st: Any = _UNBOUND,
    supply: Any = _UNBOUND,
    th: Any = _UNBOUND,
    to: Any = _UNBOUND,
    tol: Any = _UNBOUND,
    touch: Any = _UNBOUND,
    tp: Any = _UNBOUND,
    trunks: Any = _UNBOUND,
    ungrounded: Any = _UNBOUND,
    v: Any = _UNBOUND,
    w: Any = _UNBOUND,
    wt: Any = _UNBOUND,
    x: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 324 (channels_join_not_cross_at_fork, delivery_ditches_taper, field_ditch_tips_land_on_the_trunk, field_ditches_reach_source_and_sink, field_ditches_terminate) - body verbatim from the legacy gate() (feature 022)."""
    if ditches:

        def near_any(pt: Pt, polys: Sequence[Poly], tol: float = 13) -> bool:
            return any(seg_dist(pt[0], pt[1], pl[i], pl[i + 1]) < tol for pl in polys for i in range(len(pl) - 1))

        dangling: list[tuple[int, int]] = []  # type: ignore[no-redef]
        for fname in {d["field"] for d in ditches}:
            trunks = [d["poly"] for d in ditches if d["field"] == fname and d["role"] in ("main", "drain")]
            for lat in [d["poly"] for d in ditches if d["field"] == fname and d["role"] == "lateral"]:
                for end in (lat[0], lat[-1]):
                    if not near_any(end, trunks):
                        dangling.append((round(end[0]), round(end[1])))
        check(
            "field_ditches_terminate",
            not dangling,
            f"irrigation channel(s) dead-end / overshoot inside a field at {sorted(set(dangling))[:5]} - every "
            f"lateral must END on the main canal or the drain (not stop, and not stub past it toward the edge)",
        )

        # ...and it must END ON the trunk, not merely NEAR it. near_any's 13px tolerance above answers
        # "is this lateral tied into the net at all"; a lateral whose tip stops (or overruns) several px
        # off the trunk CENTERLINE is tied in topologically but draws wrong - a visible gap short of the
        # canal, or a stub through it. The tip must land inside the trunk's own drawn band (its stroke
        # half-width, +1px for the 0.1px coordinate rounding and the round linecap). Measured across the
        # pool this spared every map: outside the two polders every lateral tip already sat at distance
        # 0.00 from its trunk, and the polders' 3.5-5.3px residuals are exactly the warp error the
        # build_polder xy-snap now removes.
        _tip_off: list[tuple[int, int]] = []  # type: ignore[no-redef]
        for fname in {d["field"] for d in ditches}:
            _tip_trunks = [(d["poly"], max(d.get("w", 3.0), d.get("w_tail", 3.0)) / 2) for d in ditches if d["field"] == fname and d["role"] in ("main", "drain")]
            for lat in [d["poly"] for d in ditches if d["field"] == fname and d["role"] == "lateral"]:
                for end in (lat[0], lat[-1]):
                    _tip_slack = [min(seg_dist(end[0], end[1], tp[i], tp[i + 1]) for i in range(len(tp) - 1)) - th for tp, th in _tip_trunks]
                    if _tip_slack and min(_tip_slack) > 1.0:
                        _tip_off.append((round(end[0]), round(end[1])))
        check(
            "field_ditch_tips_land_on_the_trunk",
            not _tip_off,
            f"lateral tip(s) landing off the trunk canal's drawn band at {sorted(set(_tip_off))[:5]} - a lateral "
            f"must end ON the main/drain centerline, so it reads as a T-junction rather than a ditch stopping "
            f"short of the canal or poking a stub through it",
        )

        # DELIVERY DITCHES TAPER: a delivery ditch (role "branch") sheds its water into the paddies all
        # along its length, so its flow dwindles and it must NARROW toward the point where it stops - not
        # end abruptly at full width, which reads as a jarring blunt stub. Where head/tail widths are
        # recorded (w / w_tail), each delivery ditch must taper: w_tail < ~0.85*w. Maps that do not record
        # widths (the older water_field engine) are exempt - no width to judge.
        blunt: list[list[int]] = []  # type: ignore[no-redef]
        for fd in ditches:
            if fd.get("role") != "branch":
                continue
            w, wt = fd.get("w"), fd.get("w_tail")
            if w is None or wt is None:
                continue
            if wt > 0.85 * w:
                blunt.append([round(fd["poly"][-1][0]), round(fd["poly"][-1][1])])
        check(
            "delivery_ditches_taper",
            not blunt,
            f"delivery ditch(es) stop at nearly full width {blunt[:3]} - a ditch feeding paddies sheds its water along the way, so it must TAPER to a thread at its stopping point (w_tail < ~0.85*w)",
        )

        # a DELIVERY ditch takes off WELL DOWNSTREAM of the head fork (the bunsuiguchi division where the
        # head-race splits into the two supply canals) - a delivery sprouting AT the fork turns the clean
        # 3-way division into a 4-way STAR that reads as a crossroads, not water feeding the next channel
        # (GM 2026-07-22: Tango's nw1 / Hoshizora's west field - a short canal B whose offtake landed ~0px
        # from the fork). A fork is a node where >= 3 SUPPLY (main) ditch ends meet; the two offenders sat
        # 0-1px out while every legitimate delivery took off >= 76px downstream, so 40px is a clean cut.
        _by_field: dict[Any, list[Any]] = {}  # type: ignore[no-redef]
        for d in ditches:
            _by_field.setdefault(d.get("field"), []).append(d)
        fork_deliveries = []
        for _ds in _by_field.values():
            _deg: dict[tuple[int, int], int] = {}  # type: ignore[no-redef]
            for d in _ds:
                if d.get("role") == "main":
                    for e in (d["poly"][0], d["poly"][-1]):
                        _deg[(round(e[0]), round(e[1]))] = _deg.get((round(e[0]), round(e[1])), 0) + 1
            _forks = [n for n, c in _deg.items() if c >= 3]
            if not _forks:
                continue
            for d in _ds:
                if d.get("role") == "branch" and min(min(math.hypot(e[0] - fx, e[1] - fy) for fx, fy in _forks) for e in (d["poly"][0], d["poly"][-1])) < 40:
                    fork_deliveries.append((round(d["poly"][0][0]), round(d["poly"][0][1])))
        check(
            "channels_join_not_cross_at_fork",
            not fork_deliveries,
            f"delivery ditch(es) taking off AT the head fork {fork_deliveries[:4]} - a delivery must branch off a supply canal well DOWNSTREAM of the bunsuiguchi division (>= 40px), else the fork reads as a 4-way crossroads instead of the head-race feeding two canals",
        )

        # CONNECTIVITY: every in-field ditch must trace to BOTH an external SOURCE (a pond feed) and a runoff
        # SINK (an off-map drain or a stream). Build the watercourse graph - channels + streams + field ditches,
        # joined where their polylines come within tol (crossing-aware) - and require each ditch's component to
        # contain a pond-grounded segment AND a sink-grounded one; else the ditch is tied to nothing outside.
        def touch(pa: Poly, pb: Poly, tol: float = 16) -> bool:
            return any(seg_dist(v[0], v[1], pb[k], pb[k + 1]) < tol for v in pa for k in range(len(pb) - 1)) or any(
                seg_dist(v[0], v[1], pa[k], pa[k + 1]) < tol for v in pb for k in range(len(pa) - 1)
            )

        # a pond is the SOURCE by default (it feeds the field); meta(pond_role="drainage") makes it the SINK
        # (the field drains into it - a reservoir below the fields). Grounding is then DIRECTIONAL: the frm side
        # brings water FROM a source (an inflow brook / off-map / a source pond), the to side carries it OUT to
        # a sink (off-map / a stream / a drainage pond). Streams follow the same rule (a feeder brook grounds a
        # source, a drain brook grounds a sink) instead of the old assume-sink.
        pond_is_source = meta.get("pond_role", "source") == "source"

        def _grounds(frm: Any, to: Any) -> tuple[bool, bool]:
            # the MOAT grounds both ways: it is a fed watercourse (a moated city's fields tap it -
            # city_moat_irrigates_fields), and it is the city's storm drain (an outside field's
            # collector may empty into it), so frm=moat is a source and to=moat is a sink
            fk, tk = (frm or {}).get("kind"), (to or {}).get("kind")
            # frm=drain + to=field is the CASCADE-REUSE link (余水 reuse): a channel carrying an
            # UPSTREAM field's collector surplus down into the next field's head. The upstream
            # collector always runs when its field is irrigated, so it is a legitimate supply
            # source for the downstream net (role-aware grounding otherwise keeps a comb's supply
            # and drain as separate components, which would strand every cascade-fed field).
            src = fk in ("offmap", "forest", "stream", "moat") or (fk == "drain" and tk == "field") or (fk == "pond" and pond_is_source) or (tk == "pond" and pond_is_source)
            snk = tk in ("offmap", "stream", "moat") or (tk == "pond" and not pond_is_source) or (fk == "pond" and not pond_is_source)
            return src, snk

        segs = [(c["poly"], *_grounds(c["frm"], c["to"])) for c in M.get("channels", [])]
        segs += [(st["poly"], *_grounds(st.get("frm"), st.get("to"))) for st in M.get("streams", [])]
        d0 = len(segs)
        segs += [(d["poly"], False, False) for d in ditches]
        parent = list(range(len(segs)))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for i in range(len(segs)):
            for j in range(i + 1, len(segs)):
                if touch(segs[i][0], segs[j][0]):
                    parent[find(i)] = find(j)
        grounded = {}
        for r in {find(i) for i in range(len(segs))}:
            members = [m for m in range(len(segs)) if find(m) == r]
            grounded[r] = (any(segs[m][1] for m in members), any(segs[m][2] for m in members))
        # ROLE-AWARE grounding, so BOTH water models pass: a SUPPLY ditch (main/branch/lateral) must trace to
        # the pond SOURCE; the DRAIN must trace to a runoff SINK. They need NOT be one component - in the
        # tagoshi CASCADE model the delivery ditches END mid-field and the water flows plot-to-plot to the
        # drain (which sits offset below them), so supply and drain are separate networks bridged by the
        # cascade, not by a ditch. (In the older end-on-drain model they are one component, which still
        # satisfies both.) A ditch missing its required grounding is tied to nothing outside the field.
        supply = ("main", "branch", "lateral", "feed")
        ungrounded = []
        for m in range(d0, len(segs)):
            role = ditches[m - d0]["role"]
            has_source, has_sink = grounded[find(m)]
            if (role in supply and not has_source) or (role == "drain" and not has_sink):
                ungrounded.append((role, ditches[m - d0]["field"]))
        ungrounded = sorted(set(ungrounded))
        check(
            "field_ditches_reach_source_and_sink",
            not ungrounded,
            f"in-field ditch(es) not grounded: {ungrounded[:4]} - a SUPPLY ditch (main/branch/lateral) must trace to the pond source; the DRAIN must trace to a runoff sink (off-map / stream / brook)",
        )
    return _kept(
        locals(),
        (
            '_by_field',
            '_deg',
            '_ds',
            '_forks',
            '_grounds',
            '_tip_off',
            '_tip_slack',
            '_tip_trunks',
            'blunt',
            'c',
            'd',
            'd0',
            'dangling',
            'e',
            'end',
            'fd',
            'find',
            'fname',
            'fork_deliveries',
            'fx',
            'fy',
            'grounded',
            'has_sink',
            'has_source',
            'i',
            'j',
            'lat',
            'm',
            'members',
            'n',
            'near_any',
            'parent',
            'pond_is_source',
            'r',
            'role',
            'segs',
            'st',
            'supply',
            'th',
            'touch',
            'tp',
            'trunks',
            'ungrounded',
            'w',
            'wt',
        ),
    )
