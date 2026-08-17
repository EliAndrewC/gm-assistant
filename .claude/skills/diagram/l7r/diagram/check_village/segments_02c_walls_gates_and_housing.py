"""Gate segments (walls gates and housing; keys 0124-0133_030) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from .common_01_geometry import Poly, point_in_poly, poly_dist, seg_closest, seg_dist
from .common_02_overlap_policy import GridIndex, onmap_field_edge
from .common_03_capacity import (
    _UNBOUND,
    BUSINESS_KINDS,
    DWELLING_KINDS,
    _kept,
)


def _seg_0124___hq_tol(*, _hq_ftpx: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 124 (_hq_tol) - body verbatim from the legacy gate() (feature 022)."""
    _hq_tol = 8.0 / _hq_ftpx
    return _kept(locals(), ('_hq_tol',))


def _seg_0125___hq_bare() -> dict[str, Any]:
    """Gate segment 125 (_hq_bare, _hq_total) - body verbatim from the legacy gate() (feature 022)."""
    _hq_bare = _hq_total = 0
    return _kept(locals(), ('_hq_bare', '_hq_total'))


def _seg_0126___hq_fields(*, M: Any = _UNBOUND, f: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 126 (_hq_fields, f) - body verbatim from the legacy gate() (feature 022)."""
    _hq_fields = [f for f in M.get("fields", []) if f.get("kind") == "paddy" and f.get("plot_polys")]
    return _kept(locals(), ('_hq_fields', 'f'))


def _seg_0127__city_fan_heads_quilted(
    *,
    M: Any = _UNBOUND,
    _hq_a: Any = _UNBOUND,
    _hq_b: Any = _UNBOUND,
    _hq_bare: Any = _UNBOUND,
    _hq_covered: Any = _UNBOUND,
    _hq_covers: Any = _UNBOUND,
    _hq_cp: Any = _UNBOUND,
    _hq_cxs: Any = _UNBOUND,
    _hq_cys: Any = _UNBOUND,
    _hq_excluded: Any = _UNBOUND,
    _hq_fields: Any = _UNBOUND,
    _hq_ftpx: Any = _UNBOUND,
    _hq_grid: Any = _UNBOUND,
    _hq_k: Any = _UNBOUND,
    _hq_lines: Any = _UNBOUND,
    _hq_lp: Any = _UNBOUND,
    _hq_lw: Any = _UNBOUND,
    _hq_mains: Any = _UNBOUND,
    _hq_moat: Any = _UNBOUND,
    _hq_off: Any = _UNBOUND,
    _hq_r: Any = _UNBOUND,
    _hq_ring: Any = _UNBOUND,
    _hq_ringw: Any = _UNBOUND,
    _hq_sluice: Any = _UNBOUND,
    _hq_tol: Any = _UNBOUND,
    _hq_total: Any = _UNBOUND,
    _pp: Any = _UNBOUND,
    ax: Any = _UNBOUND,
    ay: Any = _UNBOUND,
    bx: Any = _UNBOUND,
    by: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d: Any = _UNBOUND,
    dpts_: Any = _UNBOUND,
    f: Any = _UNBOUND,
    f2: Any = _UNBOUND,
    hw: Any = _UNBOUND,
    i: Any = _UNBOUND,
    ll: Any = _UNBOUND,
    p: Any = _UNBOUND,
    px_: Any = _UNBOUND,
    py_: Any = _UNBOUND,
    q: Any = _UNBOUND,
    qx: Any = _UNBOUND,
    qy: Any = _UNBOUND,
    sgn: Any = _UNBOUND,
    stp: Any = _UNBOUND,
    t: Any = _UNBOUND,
    ux: Any = _UNBOUND,
    uy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 127 (city_fan_heads_quilted) - body verbatim from the legacy gate() (feature 022)."""
    if _hq_fields:
        _hq_covers: list[list[tuple[float, float]]] = []  # type: ignore[no-redef]
        for f2 in M.get("fields", []):
            _hq_covers += [[(q[0], q[1]) for q in p] for p in f2.get("plot_polys", [])]
        _hq_covers += [[(q[0], q[1]) for q in d["poly"]] for d in M.get("dry_plots", [])]
        _hq_lines = [([(q[0], q[1]) for q in d["poly"]], float(d.get("w", 4))) for d in M.get("field_ditches", [])]
        _hq_lines += [([(q[0], q[1]) for q in c["poly"]], float(c.get("w", 3))) for c in M.get("channels", [])]
        _hq_moat = M.get("moat")
        _hq_ring = M.get("ring_road")
        _hq_ringw = float(M.get("ring_road_width", 7))

        def _hq_excluded(qx: float, qy: float) -> bool:
            if _hq_moat and min(seg_dist(qx, qy, _hq_moat[i2], _hq_moat[i2 + 1]) for i2 in range(len(_hq_moat) - 1)) < float(M.get("moat_width", 20)) / 2 + 12 / _hq_ftpx:
                return True
            rr_ = _hq_ring
            return rr_ is not None and min(seg_dist(qx, qy, rr_[i2], rr_[i2 + 1]) for i2 in range(len(rr_) - 1)) < _hq_ringw / 2 + 12 / _hq_ftpx

        # INDEXED (2026-07-25): this ran ~3,000 sample points against every plot polygon and every
        # ditch on the map - 14M seg_dist calls, ~58% of a city gate. Same test, pruned to the local
        # cell. A polygon is indexed by its bbox GROWN by the tolerance (so an edge-proximity hit is
        # never missed), a ditch/channel by each segment's bbox grown by its own half-width + tol.
        _hq_grid = GridIndex(max(4 * _hq_tol, 24.0 / _hq_ftpx))
        for _hq_cp in _hq_covers:
            _hq_cxs = [q[0] for q in _hq_cp]
            _hq_cys = [q[1] for q in _hq_cp]
            _hq_grid.add(min(_hq_cxs) - _hq_tol, min(_hq_cys) - _hq_tol, max(_hq_cxs) + _hq_tol, max(_hq_cys) + _hq_tol, ("p", _hq_cp, 0.0))
        for _hq_lp, _hq_lw in _hq_lines:
            _hq_r = _hq_lw / 2 + _hq_tol
            for _hq_k in range(len(_hq_lp) - 1):
                _hq_a, _hq_b = _hq_lp[_hq_k], _hq_lp[_hq_k + 1]
                _hq_grid.add(min(_hq_a[0], _hq_b[0]) - _hq_r, min(_hq_a[1], _hq_b[1]) - _hq_r, max(_hq_a[0], _hq_b[0]) + _hq_r, max(_hq_a[1], _hq_b[1]) + _hq_r, ("s", _hq_a, _hq_b, _hq_r))

        def _hq_covered(qx: float, qy: float) -> bool:
            for _it in _hq_grid.near(qx, qy):
                if _it[0] == "p":
                    _pp = _it[1]
                    if point_in_poly(qx, qy, _pp) or any(seg_dist(qx, qy, _pp[_j], _pp[(_j + 1) % len(_pp)]) < _hq_tol for _j in range(len(_pp))):
                        return True
                elif seg_dist(qx, qy, _it[1], _it[2]) < _it[3]:
                    return True
            return False

        for f in _hq_fields:
            _hq_mains = [d for d in M.get("field_ditches", []) if d.get("field") == f.get("name") and d.get("role") == "main"]
            if not _hq_mains:
                continue
            _hq_sluice = _hq_mains[0]["poly"][0]
            for d in _hq_mains:
                dpts_ = d["poly"]
                hw = float(d.get("w", 4)) / 2
                for i in range(len(dpts_) - 1):
                    ax, ay = dpts_[i]
                    bx, by = dpts_[i + 1]
                    ll = math.hypot(bx - ax, by - ay)
                    if ll < 1:
                        continue
                    ux, uy = (bx - ax) / ll, (by - ay) / ll
                    stp = 12.0 / _hq_ftpx
                    t = stp / 2
                    while t < ll:
                        px_, py_ = ax + ux * t, ay + uy * t
                        if math.hypot(px_ - _hq_sluice[0], py_ - _hq_sluice[1]) >= 90.0 / _hq_ftpx:
                            for _hq_off in (hw + 20 / _hq_ftpx, hw + 34 / _hq_ftpx, hw + 48 / _hq_ftpx):
                                for sgn in (1, -1):
                                    qx, qy = px_ - uy * _hq_off * sgn, py_ + ux * _hq_off * sgn
                                    if not _hq_excluded(qx, qy):
                                        _hq_total += 1
                                        if not _hq_covered(qx, qy):
                                            _hq_bare += 1
                        t += stp
        if _hq_total:
            check(
                "city_fan_heads_quilted",
                _hq_bare <= 0.20 * _hq_total,
                f"{_hq_bare}/{_hq_total} head-band samples along the supply canals are bare parchment (>20%) - the fan head "
                f"is uncommanded ground the DRY-CROP HEM must quilt (village-real dry_band, the fork-triangle b-side band, "
                f"the grain-scaled berm); rice cannot grow there but barley does, and bare heads are the white-gaps regression",
            )
    return _kept(
        locals(),
        (
            '_hq_a',
            '_hq_b',
            '_hq_bare',
            '_hq_covered',
            '_hq_covers',
            '_hq_cp',
            '_hq_cxs',
            '_hq_cys',
            '_hq_excluded',
            '_hq_grid',
            '_hq_k',
            '_hq_lines',
            '_hq_lp',
            '_hq_lw',
            '_hq_mains',
            '_hq_moat',
            '_hq_off',
            '_hq_r',
            '_hq_ring',
            '_hq_ringw',
            '_hq_sluice',
            '_hq_total',
            'ax',
            'ay',
            'bx',
            'by',
            'c',
            'd',
            'dpts_',
            'f',
            'f2',
            'hw',
            'i',
            'll',
            'p',
            'px_',
            'py_',
            'q',
            'qx',
            'qy',
            'sgn',
            'stp',
            't',
            'ux',
            'uy',
        ),
    )


# PADDY FANS ARE GAPLESS inside their command area: bare parchment inside a comb fan is
# ground the water commands that nobody planted - the "white spots" bug. The carve's minimum
# plot/sector/closer thresholds are REAL-FEET quantities (build_comb's `grain` scales them:
# tuned at 2 ft/px, a 3 ft/px city passes grain=2/3); left unscaled they silently drop
# sectors, head plots and gap-closers a village would plant (Tango/Nagahara re-exposed
# exactly this at the city grain, 2026-07-21 - the frozen fixture). Only fields that record
# their drawn "plot_polys" are gated (the city gens do; a village gen can opt in by recording
# them). The rim is inset away (canal berms / drain set-backs legitimately live there) and
# the tolerance covers bunds and the delivery-ditch strips between plot columns.


def _seg_0128___gpx(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 128 (_gpx) - body verbatim from the legacy gate() (feature 022)."""
    _gpx = float(meta.get("ftpx", 1) or 1)
    return _kept(locals(), ('_gpx',))


def _seg_0129___g_inset(*, _gpx: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 129 (_g_inset, _g_step, _g_tol) - body verbatim from the legacy gate() (feature 022)."""
    _g_inset, _g_tol, _g_step = 56.0 / _gpx, 6.0 / _gpx, 24.0 / _gpx
    return _kept(locals(), ('_g_inset', '_g_step', '_g_tol'))


# the plot tolerance is BUND-scale (6 real ft): anything wider than a bund must be planted
# or be WATER - the field's recorded ditches count as covered ground (they draw over the
# fan), so the delivery-ditch strips between plot columns never read as bare


def _seg_0130__gap_fields() -> dict[str, Any]:
    """Gate segment 130 (gap_fields) - body verbatim from the legacy gate() (feature 022)."""
    gap_fields = []  # type: ignore[var-annotated]
    return _kept(locals(), ('gap_fields',))


def _seg_0131__bx0(
    *,
    M: Any = _UNBOUND,
    _g_inset: Any = _UNBOUND,
    _g_step: Any = _UNBOUND,
    _g_tol: Any = _UNBOUND,
    _gpx: Any = _UNBOUND,
    bx0: Any = _UNBOUND,
    bx1: Any = _UNBOUND,
    by0: Any = _UNBOUND,
    by1: Any = _UNBOUND,
    d: Any = _UNBOUND,
    dp: Any = _UNBOUND,
    f: Any = _UNBOUND,
    fditch: Any = _UNBOUND,
    gap_fields: Any = _UNBOUND,
    gbare: Any = _UNBOUND,
    gout: Any = _UNBOUND,
    gp: Any = _UNBOUND,
    gplots: Any = _UNBOUND,
    gtotal: Any = _UNBOUND,
    gx: Any = _UNBOUND,
    gy: Any = _UNBOUND,
    hw: Any = _UNBOUND,
    i: Any = _UNBOUND,
    ok_pt: Any = _UNBOUND,
    pboxes: Any = _UNBOUND,
    px0: Any = _UNBOUND,
    px1: Any = _UNBOUND,
    py0: Any = _UNBOUND,
    py1: Any = _UNBOUND,
    q: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 131 (bx0, bx1, by0, by1) - body verbatim from the legacy gate() (feature 022)."""
    for f in M.get("fields", []):
        if f.get("kind") != "paddy" or not f.get("plot_polys") or not f.get("outline"):
            continue
        gout = [(q[0], q[1]) for q in f["outline"]]
        gplots = [[(q[0], q[1]) for q in gp] for gp in f["plot_polys"]]
        pboxes = [(min(q[0] for q in gp) - _g_tol, min(q[1] for q in gp) - _g_tol, max(q[0] for q in gp) + _g_tol, max(q[1] for q in gp) + _g_tol) for gp in gplots]
        fditch = [d for d in M.get("field_ditches", []) if d.get("field") == f.get("name")]
        bx0, by0 = min(q[0] for q in gout), min(q[1] for q in gout)
        bx1, by1 = max(q[0] for q in gout), max(q[1] for q in gout)
        gbare = gtotal = 0
        gy = by0
        while gy <= by1:
            gx = bx0
            while gx <= bx1:
                if point_in_poly(gx, gy, gout) and all(seg_dist(gx, gy, gout[i], gout[(i + 1) % len(gout)]) > _g_inset for i in range(len(gout))):
                    gtotal += 1
                    ok_pt = False
                    for gp, (px0, py0, px1, py1) in zip(gplots, pboxes, strict=True):
                        if not (px0 <= gx <= px1 and py0 <= gy <= py1):
                            continue
                        if point_in_poly(gx, gy, gp) or any(seg_dist(gx, gy, gp[i], gp[(i + 1) % len(gp)]) < _g_tol for i in range(len(gp))):
                            ok_pt = True
                            break
                    if not ok_pt:
                        for d in fditch:
                            hw = float(d.get("w", 4)) / 2 + 6.0 / _gpx
                            dp = d["poly"]
                            if any(seg_dist(gx, gy, dp[i], dp[i + 1]) < hw for i in range(len(dp) - 1)):
                                ok_pt = True
                                break
                    if not ok_pt:
                        gbare += 1
                gx += _g_step
            gy += _g_step
        if gtotal and gbare > max(2, 0.02 * gtotal):
            gap_fields.append(f"{f.get('name')} ({gbare}/{gtotal} bare)")
    return _kept(
        locals(),
        ('bx0', 'bx1', 'by0', 'by1', 'd', 'dp', 'f', 'fditch', 'gap_fields', 'gbare', 'gout', 'gp', 'gplots', 'gtotal', 'gx', 'gy', 'hw', 'i', 'ok_pt', 'pboxes', 'px0', 'px1', 'py0', 'py1', 'q'),
    )


def _seg_0132__paddy_fan_gapless(*, M: Any = _UNBOUND, check: Any = _UNBOUND, f: Any = _UNBOUND, gap_fields: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 132 (paddy_fan_gapless) - body verbatim from the legacy gate() (feature 022)."""
    if any(f.get("plot_polys") for f in M.get("fields", [])):
        check(
            "paddy_fan_gapless",
            not gap_fields,
            f"unplanted holes inside the paddy fan(s): {gap_fields} - bare parchment inside the comb's command "
            f"area means the carve dropped sectors/head plots/closers there; pass build_comb grain=2/ftpx so its "
            f"real-feet minimum-size thresholds match this map's scale",
        )
    return _kept(locals(), ('f',))


# ALMOST all shops front a street (commerce wants the street); POOR housing (laborer/burakumin)
# mostly packs the block INTERIOR, reached by alleys, not the paved street frontage. (The towns
# set the template: businesses on the frontage via s.frontage, dwellings interior via s.pack.)


def _seg_0133_000__r22(*, M: Any = _UNBOUND, r22: Any = _UNBOUND, scale: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.000 (r22, st, st_lines) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        st_lines = (
            [(st["pts"], st.get("w", 18)) for st in M.get("town_streets", [])]
            + ([(M["road"], M.get("road_width", 26))] if M.get("road") else [])
            + [(r22["pts"], r22.get("width") or 26) for r22 in M.get("roads", [])]
        )  # trunk roads carry frontage too (021: the guan-xiang wards string their shops along them)
    return _kept(locals(), ('r22', 'st', 'st_lines'))


def _seg_0133_001__on_a_street(*, b: Any = _UNBOUND, i: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, sp: Any = _UNBOUND, st_lines: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.001 (on_a_street) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):

        def on_a_street(b: dict[str, Any]) -> bool:
            # 85 REAL FEET of the street's BED EDGE (bed half-width + 85ft at the declared
            # scale): a shopfront hugs the edge of the paving, so the reach must grow with the
            # lane's width - measured from the CENTERLINE alone, the capital's 26ft Imperial
            # road put its own lawful gate-market shops (standing 2ft off the bed) "off-street"
            # by one pixel (021, 2026-08-10). The fixed 85px before that was tuned at the
            # towns' 1 ft/px grain and would call most of a 3 ft/px city "on a street".
            return any(seg_dist(b["x"], b["y"], sp[i], sp[i + 1]) < wq2 / 2 + 85 / meta.get("ftpx", 1) for sp, wq2 in st_lines for i in range(len(sp) - 1))

    return _kept(locals(), ('on_a_street',))


def _seg_0133_002__b(*, M: Any = _UNBOUND, b: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.002 (b, biz) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        biz = [b for b in M.get("buildings", []) if b.get("kind") in BUSINESS_KINDS]
    return _kept(locals(), ('b', 'biz'))


def _seg_0133_003__businesses_front_streets(
    *, b: Any = _UNBOUND, biz: Any = _UNBOUND, check: Any = _UNBOUND, off: Any = _UNBOUND, on_a_street: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0133.003 (businesses_front_streets) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):  # noqa: SIM102 - comment bank under the guard; combining would orphan it (023 convention)
        if biz:
            off = [b for b in biz if not on_a_street(b)]
            # WHY (commerce takes the valuable street frontage; dwellings sit behind/interior): settlements.md "Historical grounding"
            check(
                "businesses_front_streets",
                len(off) <= 0.15 * len(biz),
                f"{len(off)}/{len(biz)} shops/merchant houses are NOT on a street - almost every business fronts a street (the more mercantile a quarter, the more streets); only dwellings fill the block interior",
            )
    return _kept(locals(), ('b', 'off'))


def _seg_0133_004__b_1(*, M: Any = _UNBOUND, b: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.004 (b, poor) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        poor = [b for b in M.get("buildings", []) if b.get("kind") in ("laborer", "burakumin")]
    return _kept(locals(), ('b', 'poor'))


def _seg_0133_005__poor_housing_mostly_interior(
    *, b: Any = _UNBOUND, check: Any = _UNBOUND, on_a_street: Any = _UNBOUND, onst: Any = _UNBOUND, poor: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0133.005 (poor_housing_mostly_interior) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital') and poor:
        onst = [b for b in poor if on_a_street(b)]
        check(
            "poor_housing_mostly_interior",
            len(onst) <= 0.5 * len(poor),
            f"{len(onst)}/{len(poor)} laborer/burakumin dwellings sit ON a street - most poor housing jams the block INTERIOR (reached by alleys), behind the street-facing businesses",
        )
    return _kept(locals(), ('b', 'onst'))


# surrounding farmland must be WORKED: the part of each outside field that SHOWS on the map
# carries farmhouses at roughly the village/hamlet linear density (~12 per 1000px of field edge,
# min ~4). Off-map field portions have their farmhouses off-screen (fine, expected), but a field
# presenting a real on-map edge with almost no farmhouses beside it is wrong - farmers build
# close to the fields they work. We count only IN-VIEW houses against the on-map field edge, so
# a partially-rendered field is held to its SHOWN extent (the gap the old per-field >=2 missed).


def _seg_0133_006__ADJ(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.006 (ADJ) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        ADJ = 165
    return _kept(locals(), ('ADJ',))


def _seg_0133_007__FARM_LD(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.007 (FARM_LD) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        FARM_LD = 7.0  # houses per 1000px of shown edge - a floor: village fields run ~4-19, the bad ones ~0
    return _kept(locals(), ('FARM_LD',))


def _seg_0133_008__sparse(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.008 (sparse) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        sparse = []  # type: ignore[var-annotated]
    return _kept(locals(), ('sparse',))


def _seg_0133_009__cx(
    *,
    ADJ: Any = _UNBOUND,
    EX0: Any = _UNBOUND,
    EX1: Any = _UNBOUND,
    EY0: Any = _UNBOUND,
    EY1: Any = _UNBOUND,
    FARM_LD: Any = _UNBOUND,
    M: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    edge: Any = _UNBOUND,
    f: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    h: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    nv: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    sparse: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0133.009 (cx, cy, edge, f) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        for f in fields:
            cx, cy = (f["bbox"][0] + f["bbox"][2]) / 2, (f["bbox"][1] + f["bbox"][3]) / 2
            if M.get("wall") and point_in_poly(cx, cy, M["wall"]):
                continue  # in-wall plots are not surrounding farmland
            edge = onmap_field_edge(f["outline"], EX0, EY0, EX1, EY1)
            if edge < 120:
                continue  # only a tiny sliver shows - too little to require farmhouses
            nv = sum(1 for h in houses if EX0 <= h["x"] <= EX1 and EY0 <= h["y"] <= EY1 and poly_dist(h["x"], h["y"], f["outline"]) <= ADJ)
            if nv < FARM_LD * edge / 1000:
                sparse.append((f["name"], nv, round(FARM_LD * edge / 1000, 1)))
    return _kept(locals(), ('cx', 'cy', 'edge', 'f', 'h', 'nv', 'sparse'))


def _seg_0133_010__outside_fields_farmhouse_density(*, check: Any = _UNBOUND, scale: Any = _UNBOUND, sparse: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.010 (outside_fields_farmhouse_density) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        check("outside_fields_farmhouse_density", not sparse, f"shown field edge(s) with too few farmhouses beside the on-map portion (farmers build close; expect ~village density): {sparse}")
    return _kept(locals(), ())


# the IN-WALL agricultural district (the unusual city that farms inside its walls) is REAL
# farmland too. Unlike the SURROUNDING fields above - mostly off the cropped map, so only a
# FLOOR (7) is enforceable on their shown sliver - an in-wall field sits ENTIRELY in view, so
# its WHOLE perimeter must read as worked: ring it DENSELY all the way round, not a sparse few
# on one side leaving long bare edges. Held to a much higher density (the dense end of village
# ringing). Only bites when meta(agricultural_district=True) - most cities have no in-wall fields.


def _seg_0133_011__FARM_LD_INWALL(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.011 (FARM_LD_INWALL) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        FARM_LD_INWALL = 16.0  # houses per 1000px of edge - a full, all-round ring, not the off-map floor
    return _kept(locals(), ('FARM_LD_INWALL',))


def _seg_0133_012__city_interior_fields_farmhouse_density(
    *,
    ADJ: Any = _UNBOUND,
    EX0: Any = _UNBOUND,
    EX1: Any = _UNBOUND,
    EY0: Any = _UNBOUND,
    EY1: Any = _UNBOUND,
    FARM_LD_INWALL: Any = _UNBOUND,
    M: Any = _UNBOUND,
    URBAN: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    edge: Any = _UNBOUND,
    f: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    h: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    nv: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    thin: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0133.012 (city_interior_fields_farmhouse_density) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital') and URBAN and meta.get("agricultural_district") and M.get("wall"):
        thin = []
        for f in fields:
            cx, cy = (f["bbox"][0] + f["bbox"][2]) / 2, (f["bbox"][1] + f["bbox"][3]) / 2
            if not point_in_poly(cx, cy, M["wall"]):
                continue  # only the in-wall plots
            # VEGETABLE tracts are exempt from the farmstead ring: urban garden ground is
            # worked by the residents of the surrounding quarters (well/night-soil fed
            # intensive plots), not by dedicated in-wall farm households - only in-wall
            # PADDY carries the village-density farmhouse ring
            if f.get("kind") != "paddy":
                continue
            edge = onmap_field_edge(f["outline"], EX0, EY0, EX1, EY1)
            if edge < 120:
                continue
            nv = sum(1 for h in houses if poly_dist(h["x"], h["y"], f["outline"]) <= ADJ)
            if nv < FARM_LD_INWALL * edge / 1000:
                thin.append((f["name"], nv, round(FARM_LD_INWALL * edge / 1000, 1)))
        check(
            "city_interior_fields_farmhouse_density",
            not thin,
            f"in-wall agricultural field(s) too sparsely farmed - an in-wall field shows its WHOLE perimeter, so ring it densely all the way round (no long bare edges), not a token few: {thin}",
        )
    return _kept(locals(), ('cx', 'cy', 'edge', 'f', 'h', 'nv', 'thin'))


# housing packs DEEP, but no GIANT cluster may be cut off from circulation: a big block of
# dwellings with no street OR alley anywhere near it has no way in or out. Deep blocks must
# be laced with gravel alleys (s.alley) so every dwelling is reachable.


def _seg_0133_013__a(*, M: Any = _UNBOUND, a: Any = _UNBOUND, r9: Any = _UNBOUND, s: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.013 (a, acc, r9, s) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        acc = (
            [s["pts"] for s in M.get("town_streets", [])] + ([M["road"]] if M.get("road") else []) + [r9["pts"] for r9 in M.get("roads", [])] + [a["pts"] for a in M.get("alleys", [])]
        )  # trunk roads serve their roadside wards (the guan-xiang suburbs string along them)
    return _kept(locals(), ('a', 'acc', 'r9', 's'))


def _seg_0133_014__cut_off(*, acc: Any = _UNBOUND, b: Any = _UNBOUND, i: Any = _UNBOUND, ln: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.014 (cut_off) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):

        def cut_off(b: dict[str, Any]) -> bool:
            return not any(seg_dist(b["x"], b["y"], ln[i], ln[i + 1]) < 95 for ln in acc for i in range(len(ln) - 1))

    return _kept(locals(), ('cut_off',))


def _seg_0133_015__b_2(*, M: Any = _UNBOUND, b: Any = _UNBOUND, cut_off: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.015 (b, iso) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        iso = [b for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS and cut_off(b)]
    return _kept(locals(), ('b', 'iso'))


def _seg_0133_016__seen(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.016 (seen) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        seen: set[int] = set()  # type: ignore[no-redef,unused-ignore]
    return _kept(locals(), ('seen',))


def _seg_0133_017__biggest(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.017 (biggest) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        biggest = 0
    return _kept(locals(), ('biggest',))


def _seg_0133_018__biggest_1(
    *, biggest: Any = _UNBOUND, i: Any = _UNBOUND, iso: Any = _UNBOUND, j: Any = _UNBOUND, kk: Any = _UNBOUND, n: Any = _UNBOUND, scale: Any = _UNBOUND, seen: Any = _UNBOUND, stack: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0133.018 (biggest, i, j, kk) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        for i in range(len(iso)):
            if i in seen:
                continue
            stack, n = [i], 0
            seen.add(i)
            while stack:
                j = stack.pop()
                n += 1
                for kk in range(len(iso)):
                    if kk not in seen and abs(iso[j]["x"] - iso[kk]["x"]) < 46 and abs(iso[j]["y"] - iso[kk]["y"]) < 46:
                        seen.add(kk)
                        stack.append(kk)
            biggest = max(biggest, n)
    return _kept(locals(), ('biggest', 'i', 'j', 'kk', 'n', 'seen', 'stack'))


def _seg_0133_019__no_isolated_dwelling_cluster(*, biggest: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.019 (no_isolated_dwelling_cluster) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        check(
            "no_isolated_dwelling_cluster",
            biggest <= 30,
            f"a contiguous cluster of {biggest} dwellings sits >95px from any street OR alley - a giant block of houses with no way in or out; lace deep blocks with gravel alleys (s.alley) so every block is reachable",
        )
    return _kept(locals(), ())


# an alley must EARN its length by UNIQUELY serving dwellings. A building is credited to its
# NEAREST lane only (the one it actually fronts), exactly as empty_street_runs scores streets -
# so a lane counts only what no other lane already reaches. This catches BOTH a lane running off
# into a half-empty corner (a "lane to nowhere") AND a redundant lane laid beside or across one
# that already serves the same block (a perpendicular arm the block's spine already reaches, or a
# second lane shadowing a parallel street). Scaled to the buildings (~1 dwelling per 30px of its
# own length), so it holds at the city's dense small-footprint grain, not a fixed town pixel gap.


def _seg_0133_020__alley_blds(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.020 (alley_blds) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        alley_blds = M.get("buildings", []) + M.get("houses", [])
    return _kept(locals(), ('alley_blds',))


def _seg_0133_021__a_1(*, M: Any = _UNBOUND, a: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.021 (a, alleys) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        alleys = [a["pts"] for a in M.get("alleys", [])]
    return _kept(locals(), ('a', 'alleys'))


def _seg_0133_022__other(*, M: Any = _UNBOUND, s: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.022 (other, s) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        other = [s["pts"] for s in M.get("town_streets", [])] + ([M["road"]] if M.get("road") else [])
    return _kept(locals(), ('other', 's'))


def _seg_0133_023__kido(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.023 (kido) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        kido = M.get("kido", [])
    return _kept(locals(), ('kido',))


def _seg_0133_024__lane_dist(*, b: Any = _UNBOUND, i: Any = _UNBOUND, pts: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.024 (lane_dist) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):

        def lane_dist(b: dict[str, Any], pts: Poly) -> float:
            return min(seg_dist(b["x"], b["y"], pts[i], pts[i + 1]) for i in range(len(pts) - 1))

    return _kept(locals(), ('lane_dist',))


def _seg_0133_025__foot(*, b: Any = _UNBOUND, c: Any = _UNBOUND, i: Any = _UNBOUND, pts: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.025 (foot) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):

        def foot(b: dict[str, Any], pts: Poly) -> tuple[float, float]:
            return min((seg_closest(b["x"], b["y"], pts[i], pts[i + 1]) for i in range(len(pts) - 1)), key=lambda c: math.hypot(b["x"] - c[0], b["y"] - c[1]))

    return _kept(locals(), ('foot',))


def _seg_0133_026__gate_spur(
    *,
    E: Any = _UNBOUND,
    alley_blds: Any = _UNBOUND,
    b: Any = _UNBOUND,
    c: Any = _UNBOUND,
    foot: Any = _UNBOUND,
    g: Any = _UNBOUND,
    kido: Any = _UNBOUND,
    lane_dist: Any = _UNBOUND,
    pts: Any = _UNBOUND,
    reach: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0133.026 (gate_spur) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):

        def gate_spur(pts: Poly) -> float:
            # a terminal stretch running OUT to a ward GATE past the last served building is a legitimate
            # gate-access spur (the lane pulls in to a kido), NOT a lane-to-nowhere - so it does not count
            # toward the serve ratio. Trim it from each gated end (distance from the gate to the nearest
            # building the lane fronts, measured along the lane).
            spur = 0.0
            for E in (pts[0], pts[-1]):
                if not any(math.hypot(E[0] - g["x"], E[1] - g["y"]) < 20 for g in kido):
                    continue
                reach = [math.hypot(E[0] - (c := foot(b, pts))[0], E[1] - c[1]) for b in alley_blds if lane_dist(b, pts) < 60]
                if reach:
                    spur += min(reach)
            return spur

    return _kept(locals(), ('gate_spur',))


def _seg_0133_027__uniq(*, alleys: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.027 (uniq) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        uniq = [0] * len(alleys)
    return _kept(locals(), ('uniq',))


def _seg_0133_028__b_3(
    *,
    alley_blds: Any = _UNBOUND,
    alleys: Any = _UNBOUND,
    b: Any = _UNBOUND,
    best_d: Any = _UNBOUND,
    best_i: Any = _UNBOUND,
    d: Any = _UNBOUND,
    lane_dist: Any = _UNBOUND,
    li: Any = _UNBOUND,
    other: Any = _UNBOUND,
    pts: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    uniq: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0133.028 (b, best_d, best_i, d) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        for b in alley_blds:
            best_d, best_i = 60.0, None  # only buildings within a frontage band count for any lane
            for li, pts in enumerate(alleys):
                d = lane_dist(b, pts)
                if d < best_d:
                    best_d, best_i = d, li
            if best_i is None:
                continue
            if all(lane_dist(b, pts) > best_d for pts in other):  # no street/road is closer - this alley owns it
                uniq[best_i] += 1
    return _kept(locals(), ('b', 'best_d', 'best_i', 'd', 'li', 'pts', 'uniq'))


def _seg_0133_029__thin(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.029 (thin) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        thin = []  # type: ignore[var-annotated]
    return _kept(locals(), ('thin',))


def _seg_0133_030__i(
    *,
    alleys: Any = _UNBOUND,
    gate_spur: Any = _UNBOUND,
    i: Any = _UNBOUND,
    length: Any = _UNBOUND,
    li: Any = _UNBOUND,
    pts: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    thin: Any = _UNBOUND,
    uniq: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0133.030 (i, length, li, pts) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        for li, pts in enumerate(alleys):
            length = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
            length -= gate_spur(pts)  # the run out to a ward gate is access, not block-service
            if uniq[li] * 30 < length:
                thin.append((pts[0], uniq[li], round(length)))
    return _kept(locals(), ('i', 'length', 'li', 'pts', 'thin'))
