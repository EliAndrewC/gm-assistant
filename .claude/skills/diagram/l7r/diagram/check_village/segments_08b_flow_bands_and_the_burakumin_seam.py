"""Gate segments (flow bands and the burakumin seam; keys 0523_019-0543_010) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from l7r.diagram.waterfields import BANK_MARGIN, polyline_cum, supply_bank_clearance

from .common_01_geometry import Poly, point_in_poly, pt_to_rect, seg_dist
from .common_02_overlap_policy import GridIndex
from .common_03_capacity import _UNBOUND, _kept


def _seg_0523_019__paddy_bunds_clear_the_collector(*, _dd: Any = _UNBOUND, _field_dd: Any = _UNBOUND, check: Any = _UNBOUND, thru: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0523.019 (paddy_bunds_clear_the_collector) - body verbatim from _seg_0523__drain_flows_downhill (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if _dd is not None or _field_dd:
        check(
            "paddy_bunds_clear_the_collector",
            not thru,
            f"{len(thru)} paddy bund vertex/vertices {thru[:4]} are drawn INSIDE the drainage collector's stroke or past its centerline - a paddy's low bund IS the ditch's bank, so the field must hem onto the collector (bunds running WITH it), never across it",
        )
    return _kept(locals(), ())


# AN AZEMAME BEAD SITS ON A VISIBLE BUND, NEVER IN OPEN WATER (GM 2026-08-15, on Inashiro:
# "random green dots that appear to be scattered in the middle of flooded rice paddies ...
# it should be impossible for those green dots to be placed anywhere except on top of
# earthen bunds"). The defect was PAINT ORDER, not a bad scatter: `_fill_wedges`' filler
# plots deliberately lap up to ~12 real ft onto a neighbor and are appended LAST, so the
# lapped stretch of the neighbor's bund stroke is buried under the filler's water fill -
# and the bead line `_bund_beans` had already laid along that stretch draws AFTER every
# plot, so its dots surfaced floating in the filler's paddy (49 of Inashiro's 777 beads,
# 3-10 px deep). The field record carries `plot_rings` in draw order precisely so this is
# judgeable from the manifest: a bead is legal iff some ring's edge passes within _BB_TOL
# of it AND no ring painted after that one buries the bead deeper than _BB_TOL. Placement
# (`waterfields._bund_beans`) enforces the same rule at half this tolerance, so a bead the
# placer allowed cannot false-fire here through 1dp manifest rounding. Pre-2026-08-15
# manifests record neither key and skip; the recording itself is unconditional at the one
# draw site (draw_comb_field), pinned by test_draw_comb_field_records_rings_and_beads.
# ... and the same rule against WATER paint (GM 2026-08-15, second pass: "fix the water-buried
# beads so the record stays honest"; settlement-review found 40 of Inashiro's 727 recorded
# beads invisible under channel/pond paint - opposite polarity from the plot burial, bund and
# bead buried together, but the record was attesting beads nobody can see). The painted truth
# is read from the manifest's paint records, not re-derived: `drawn_channels` carries the
# post-clip stroke geometry + widths (late strokes paint after the beads and bury them),
# `pond` and `field_ponds` the water ellipses. A bead inside any of those is wrong whichever
# way the z goes - buried ink under late water, or a green dot floating ON the water for
# paint that runs under the beads - so the test is position, not stacking.


def _seg_0524___BB_TOL() -> dict[str, Any]:
    """Gate segment 524 (_BB_TOL) - body verbatim from the legacy gate() (feature 022)."""
    _BB_TOL = 2.0
    return _kept(locals(), ('_BB_TOL',))


def _seg_0525___bb_wet() -> dict[str, Any]:
    """Gate segment 525 (_bb_wet) - body verbatim from the legacy gate() (feature 022)."""
    _bb_wet: list[tuple[float, float, float, float]] = []  # water ellipses (cx, cy, rx, ry), shrunk by the tolerance at use
    return _kept(locals(), ('_bb_wet',))


def _seg_0526___bb_wet_1(*, M: Any = _UNBOUND, _bb_wet: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 526 (_bb_wet) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("pond"):
        _bb_wet.append((float(M["pond"][0]), float(M["pond"][1]), float(M["pond"][2]), float(M["pond"][3])))
    return _kept(locals(), ('_bb_wet',))


def _seg_0527___bb_fp(*, M: Any = _UNBOUND, _bb_fp: Any = _UNBOUND, _bb_wet: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 527 (_bb_fp, _bb_wet) - body verbatim from the legacy gate() (feature 022)."""
    for _bb_fp in M.get("field_ponds") or []:
        _bb_wet.append((float(_bb_fp["x"]), float(_bb_fp["y"]), float(_bb_fp["rx"]), float(_bb_fp["ry"])))
    return _kept(locals(), ('_bb_fp', '_bb_wet'))


def _seg_0528___bb_c(*, M: Any = _UNBOUND, _bb_c: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 528 (_bb_c, _bb_wchan) - body verbatim from the legacy gate() (feature 022)."""
    _bb_wchan = [_bb_c for _bb_c in (M.get("drawn_channels") or []) if _bb_c.get("late") and len(_bb_c.get("pts") or []) >= 2]
    return _kept(locals(), ('_bb_c', '_bb_wchan'))


def _seg_0529___bb_in_water(
    *,
    _BB_TOL: Any = _UNBOUND,
    _bb_wchan: Any = _UNBOUND,
    _bb_wet: Any = _UNBOUND,
    _wcx: Any = _UNBOUND,
    _wcy: Any = _UNBOUND,
    _wi: Any = _UNBOUND,
    _wtot: Any = _UNBOUND,
    _wx: Any = _UNBOUND,
    _wy: Any = _UNBOUND,
    q: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 529 (_bb_in_water) - body verbatim from the legacy gate() (feature 022)."""

    def _bb_in_water(_wx: float, _wy: float) -> bool:
        for _wcx, _wcy, _wrx, _wry in _bb_wet:
            if _wrx > _BB_TOL and _wry > _BB_TOL and ((_wx - _wcx) / (_wrx - _BB_TOL)) ** 2 + ((_wy - _wcy) / (_wry - _BB_TOL)) ** 2 <= 1.0:
                return True
        for _wc in _bb_wchan:
            _wp = _wc["pts"]
            _wcum = polyline_cum([(float(q[0]), float(q[1])) for q in _wp])
            _wtot = _wcum[-1] or 1.0
            for _wi in range(len(_wp) - 1):
                _wd = seg_dist(_wx, _wy, _wp[_wi], _wp[_wi + 1])
                _wt = _wcum[_wi] / _wtot  # width taper measured at the segment head - within a segment the taper moves less than the tolerance
                if _wd < (float(_wc["w0"]) + (float(_wc["w1"]) - float(_wc["w0"])) * _wt) / 2 - 1.0:
                    return True
        return False

    return _kept(locals(), ('_bb_in_water',))


def _seg_0530___bb_stray() -> dict[str, Any]:
    """Gate segment 530 (_bb_stray) - body verbatim from the legacy gate() (feature 022)."""
    _bb_stray: list[list[float]] = []
    return _kept(locals(), ('_bb_stray',))


def _seg_0531___bb_b(
    *,
    Hd: Any = _UNBOUND,
    Wd: Any = _UNBOUND,
    _BB_TOL: Any = _UNBOUND,
    _bb_b: Any = _UNBOUND,
    _bb_beans: Any = _UNBOUND,
    _bb_buried: Any = _UNBOUND,
    _bb_d: Any = _UNBOUND,
    _bb_edge: Any = _UNBOUND,
    _bb_fld: Any = _UNBOUND,
    _bb_gi: Any = _UNBOUND,
    _bb_in_water: Any = _UNBOUND,
    _bb_j: Any = _UNBOUND,
    _bb_k: Any = _UNBOUND,
    _bb_ring: Any = _UNBOUND,
    _bb_rings: Any = _UNBOUND,
    _bb_stray: Any = _UNBOUND,
    _bb_x: Any = _UNBOUND,
    _bb_xs: Any = _UNBOUND,
    _bb_y: Any = _UNBOUND,
    _bb_ys: Any = _UNBOUND,
    _bx0: Any = _UNBOUND,
    _bx1: Any = _UNBOUND,
    _by0: Any = _UNBOUND,
    _by1: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    i: Any = _UNBOUND,
    q: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 531 (_bb_b, _bb_beans, _bb_buried, _bb_d) - body verbatim from the legacy gate() (feature 022)."""
    for _bb_fld in fields:
        _bb_beans = _bb_fld.get("bund_beans") or []
        _bb_rings = _bb_fld.get("plot_rings") or []
        if not _bb_beans or not _bb_rings:
            continue
        _bb_gi = GridIndex(64)
        for _bb_j, _bb_ring in enumerate(_bb_rings):
            _bb_xs = [float(q[0]) for q in _bb_ring]
            _bb_ys = [float(q[1]) for q in _bb_ring]
            # clamp the index box to the canvas (generously): negative fixtures carry deliberately
            # insane geometry, and an unclamped box allocates a dict entry per 120px cell of it
            _bx0, _by0 = max(min(_bb_xs) - _BB_TOL, -Wd), max(min(_bb_ys) - _BB_TOL, -Hd)
            _bx1, _by1 = min(max(_bb_xs) + _BB_TOL, 2 * Wd), min(max(_bb_ys) + _BB_TOL, 2 * Hd)
            if _bx0 <= _bx1 and _by0 <= _by1:
                _bb_gi.add(_bx0, _by0, _bx1, _by1, (_bb_j, _bb_ring))
        for _bb_b in _bb_beans:
            _bb_x, _bb_y = float(_bb_b[0]), float(_bb_b[1])
            _bb_edge: dict[int, float] = {}  # type: ignore[no-redef]  # ring index -> its nearest-edge distance to the bead
            _bb_buried: list[int] = []  # type: ignore[no-redef]  # rings whose fill buries the bead (inside, deeper than tol)
            for _bb_j, _bb_ring in _bb_gi.near(_bb_x, _bb_y):
                _bb_d = min(seg_dist(_bb_x, _bb_y, _bb_ring[i], _bb_ring[(i + 1) % len(_bb_ring)]) for i in range(len(_bb_ring)))
                _bb_edge[_bb_j] = _bb_d
                if _bb_d > _BB_TOL and point_in_poly(_bb_x, _bb_y, _bb_ring):
                    _bb_buried.append(_bb_j)
            if _bb_in_water(_bb_x, _bb_y) or not any(_bb_d <= _BB_TOL and all(_bb_k <= _bb_j for _bb_k in _bb_buried) for _bb_j, _bb_d in _bb_edge.items()):
                _bb_stray.append([round(_bb_x), round(_bb_y)])
    return _kept(
        locals(),
        (
            '_bb_b',
            '_bb_beans',
            '_bb_buried',
            '_bb_d',
            '_bb_edge',
            '_bb_fld',
            '_bb_gi',
            '_bb_j',
            '_bb_k',
            '_bb_ring',
            '_bb_rings',
            '_bb_stray',
            '_bb_x',
            '_bb_xs',
            '_bb_y',
            '_bb_ys',
            '_bx0',
            '_bx1',
            '_by0',
            '_by1',
            'i',
            'q',
        ),
    )


def _seg_0532__bund_beans_on_bunds(*, _bb_stray: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 532 (bund_beans_on_bunds) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "bund_beans_on_bunds",
        not _bb_stray,
        f"{len(_bb_stray)} azemame bead(s) {_bb_stray[:4]} do not sit on a bund the finished paint shows - a bund stroke buried under a later-drawn plot's fill (the wedge fillers lap their neighbors on purpose) or under WATER paint (a late ditch stroke, the source pond, a pocket pond) is not visible ground; `waterfields._bund_beans` / `draw_comb_field`'s pond filter must drop the beads laid there so the record carries no invisible ink",
    )
    return _kept(locals(), ())


def _seg_0595__paddy_bunds_clear_the_supply_channels(*, M: Any = _UNBOUND, check: Any = _UNBOUND, fields: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 595 (paddy_bunds_clear_the_supply_channels) - the first check ADDED by hand
    after feature 022 retired the transformer. Numbered past the legacy range (0000-0594) but
    REGISTERED between segments 0532 and 0533, beside the bead checks whose `fields` binding it
    shares (the registry TUPLE is the execution order; the number is only a label). New-style:
    its temps stay function-local - no legacy leak parity to keep - so writes=()."""
    # A PADDY'S CANAL-SIDE BUND IS THE SUPPLY CHANNEL'S BANK - NEVER DRAWN DOWN THE MIDDLE OF THE
    # WATER (GM 2026-08-15, on Inashiro: "the earth bunds which border the irrigated channel ...
    # are actually in the middle of the water instead of along the water's edge. I think they are
    # supposed to be along the water's edge"). The supply half of paddy_bunds_clear_the_collector,
    # and the same physical rule: the bund holds the basin's water IN and the channel carries other
    # water PAST, so the two can only ABUT at the bank - and a bund hemmed onto the bank runs
    # parallel to and along the water's edge, which is exactly the read the GM asked for.
    #
    # The defect was construction, not a stray plot: `_carve`'s `bnd` returns thread CENTERLINES,
    # and the supply strokes (the tapering canal pieces, the delivery ditches) are drawn centered
    # on those same lines - so the first and last column of every sector, and the head wedge's
    # boundary where `bnd` falls back onto canal A's own path, carried bunds running down the
    # middle of the drawn water. Measured on the pre-fix Inashiro: 266 sampled bund-edge points
    # inside a supply stroke, the worst 6.1 px deep in a ~12 px channel - i.e. ON its centerline.
    #
    # POSITION, not angle, for the reasons the collector check records above; measured
    # perpendicular to the stroke with its taper honored, and vertices projecting past a stroke's
    # ends skipped (ground beyond the span is not governed by it - a delivery ditch's takeoff sits
    # ON its parent canal, which governs there in its own right). The predicate is
    # `supply_bank_clearance`, imported from the engine and NOT restated - the same call `_carve`'s
    # `clear_supply` makes when it lays the bund. The placer holds a corner at halfw +
    # BANK_MARGIN * grain and this fires below halfw + BANK_MARGIN - 0.15 (the collector check's
    # 1dp-rounding slack), so a bund the placer allowed cannot false-fire here.
    #
    # GATED ON `meta.generated_by` (the migration doctrine, GM 2026-08-13, same gate as the
    # sun-corridor rule above): the legacy comb maps carry this defect pool-wide - measured
    # 2026-08-15 by this same predicate over their recorded plot_polys: kikuta 524 buried bund
    # vertices, minami 208, honda 203, tango 190, nagahara 121, shimizu 90, hirameki 33, ubame 17,
    # yatsuda 15, hoshizora 11, tanada 9, enokida 1 - re-carving them all was judged the wrong
    # trade once already.
    # The rule binds the SCRIPTED path (`build_comb(supply_banks=True)`); each legacy map inherits
    # it at the moment it is converted. Manifests that record no plot_rings (pre-2026-08-15) skip,
    # the same line the bead checks hold.
    if M["meta"].get("generated_by"):
        _sb_thru: dict[tuple[int, int], None] = {}  # dedupe: a corner is shared by up to 4 rings
        for _sb_fld in fields:
            _sb_rings = _sb_fld.get("plot_rings") or []
            if not _sb_rings:
                continue
            for _sb_fd in M.get("field_ditches", []):
                if _sb_fd.get("role") not in ("main", "branch") or _sb_fd.get("field") != _sb_fld.get("name"):
                    continue
                _sb_pts = [(float(p[0]), float(p[1])) for p in _sb_fd.get("poly") or []]
                if len(_sb_pts) < 2:
                    continue
                _sb_cum = polyline_cum(_sb_pts)
                _sb_w0 = float(_sb_fd.get("w", 2.0))
                _sb_w1 = float(_sb_fd.get("w_tail", _sb_w0))
                # bbox prefilter (prunes only): a vertex outside the stroke's box grown by its
                # widest half-width + margin cannot be inside the stroke
                _sb_reach = max(_sb_w0, _sb_w1) / 2 + BANK_MARGIN + 1.0
                _sb_x0 = min(p[0] for p in _sb_pts) - _sb_reach
                _sb_x1 = max(p[0] for p in _sb_pts) + _sb_reach
                _sb_y0 = min(p[1] for p in _sb_pts) - _sb_reach
                _sb_y1 = max(p[1] for p in _sb_pts) + _sb_reach
                # EDGES, not just vertices (settlement-review, Sawada 2026-08-15): a junction wedge
                # can keep every corner dry while its two long edges converge THROUGH the canal, so
                # each bund edge is walked at a 3 px step - bbox-gated, so only near-stroke edges pay
                for _sb_ring in _sb_rings:
                    for _sb_i in range(len(_sb_ring)):
                        _sb_a, _sb_b = _sb_ring[_sb_i], _sb_ring[(_sb_i + 1) % len(_sb_ring)]
                        _sb_ax, _sb_ay = float(_sb_a[0]), float(_sb_a[1])
                        _sb_bx, _sb_by = float(_sb_b[0]), float(_sb_b[1])
                        if max(_sb_ax, _sb_bx) < _sb_x0 or min(_sb_ax, _sb_bx) > _sb_x1 or max(_sb_ay, _sb_by) < _sb_y0 or min(_sb_ay, _sb_by) > _sb_y1:
                            continue
                        _sb_nstep = max(1, int(math.hypot(_sb_bx - _sb_ax, _sb_by - _sb_ay) / 3.0))
                        for _sb_k in range(_sb_nstep + 1):
                            _sb_t = _sb_k / _sb_nstep
                            _sb_x = _sb_ax + _sb_t * (_sb_bx - _sb_ax)
                            _sb_y = _sb_ay + _sb_t * (_sb_by - _sb_ay)
                            _sb_gap, _sb_halfw, _sb_past, _sb_foot, _sb_nrm = supply_bank_clearance((_sb_x, _sb_y), _sb_pts, _sb_w0, _sb_w1, _sb_cum)
                            if not _sb_past and _sb_gap < _sb_halfw + BANK_MARGIN - 0.15:
                                _sb_thru[(round(_sb_x), round(_sb_y))] = None
                                break
        check(
            "paddy_bunds_clear_the_supply_channels",
            not _sb_thru,
            f"{len(_sb_thru)} paddy bund vertex/vertices {[list(_sb_k) for _sb_k in list(_sb_thru)[:4]]} are drawn inside a SUPPLY channel's stroke - a bund bordering the irrigated channel is the channel's BANK, so it runs parallel to and along the water's edge, never down the middle of the water; carve with build_comb(supply_banks=True) so the bunds hem onto the drawn strokes",
        )
    return _kept(locals(), ())


# A drainage brook LEAVES the collector as a smooth BEND, not a hard right-angle corner - a contour
# collector turns down the valley INTO the stream, it does not meet it at 90 deg. For each drain-fed
# brook, compare the drain's ARRIVAL heading (into the shared outfall) with the brook's DEPARTURE
# heading (each averaged over ~40px, so short jittery segments do not fool it); the turn must be < 65 deg.


def _seg_0533___flow_dir(*, end: Any = _UNBOUND, poly: Any = _UNBOUND, q: Any = _UNBOUND, span: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 533 (_flow_dir) - body verbatim from the legacy gate() (feature 022)."""

    def _flow_dir(poly: Poly, at_start: bool, span: float = 40.0) -> tuple[float, float]:
        end = poly[0] if at_start else poly[-1]
        ref = end
        for q in poly[1:] if at_start else poly[-2::-1]:
            ref = q
            if math.hypot(q[0] - end[0], q[1] - end[1]) >= span:
                break
        return (ref[0] - end[0], ref[1] - end[1]) if at_start else (end[0] - ref[0], end[1] - ref[1])

    return _kept(locals(), ('_flow_dir',))


def _seg_0534___drains(*, M: Any = _UNBOUND, fd: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 534 (_drains, fd) - body verbatim from the legacy gate() (feature 022)."""
    _drains = [fd["poly"] for fd in M.get("field_ditches", []) if fd.get("role") == "drain"]
    return _kept(locals(), ('_drains', 'fd'))


def _seg_0535__sharp() -> dict[str, Any]:
    """Gate segment 535 (sharp) - body verbatim from the legacy gate() (feature 022)."""
    sharp = []  # type: ignore[var-annotated]
    return _kept(locals(), ('sharp',))


def _seg_0536__ang(
    *,
    M: Any = _UNBOUND,
    _drains: Any = _UNBOUND,
    _flow_dir: Any = _UNBOUND,
    ang: Any = _UNBOUND,
    arr: Any = _UNBOUND,
    bp: Any = _UNBOUND,
    dep: Any = _UNBOUND,
    dp: Any = _UNBOUND,
    e: Any = _UNBOUND,
    la: Any = _UNBOUND,
    ld: Any = _UNBOUND,
    near_drain: Any = _UNBOUND,
    sharp: Any = _UNBOUND,
    st: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 536 (ang, arr, bp, dep) - body verbatim from the legacy gate() (feature 022)."""
    for st in M.get("streams", []):
        if (st.get("frm") or {}).get("kind") != "drain" or len(st["poly"]) < 2:
            continue
        bp = st["poly"]
        near_drain = min(
            (
                (math.hypot(bp[0][0] - dp[e][0], bp[0][1] - dp[e][1]), dp, e)  # the drain it leaves:
                for dp in _drains
                for e in (0, -1)
            ),
            default=None,
        )  # nearest drain endpoint
        if near_drain is None or near_drain[0] > 40 or len(near_drain[1]) < 2:
            continue
        arr, dep = _flow_dir(near_drain[1], at_start=(near_drain[2] == 0)), _flow_dir(bp, at_start=True)
        la, ld = math.hypot(*arr), math.hypot(*dep)
        if la < 1 or ld < 1:  # pragma: no cover - real drains/brooks span the field; guards 0-length polys
            continue
        ang = math.degrees(math.acos(max(-1.0, min(1.0, (arr[0] * dep[0] + arr[1] * dep[1]) / (la * ld)))))
        if ang > 65:
            sharp.append(round(ang))
    return _kept(locals(), ('ang', 'arr', 'bp', 'dep', 'dp', 'e', 'la', 'ld', 'near_drain', 'sharp', 'st'))


def _seg_0537__drainage_junction_smooth(*, check: Any = _UNBOUND, sharp: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 537 (drainage_junction_smooth) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "drainage_junction_smooth",
        not sharp,
        f"a drainage brook leaves the collector at a sharp {sharp[:3]} deg corner - it must CURVE out of "
        f"the drain's heading (a collector turns down the valley into the stream, not a hard right angle)",
    )
    return _kept(locals(), ())


# torii (if any): clear of the shrine and spread out (universal)


def _seg_0538__torii(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 538 (torii) - body verbatim from the legacy gate() (feature 022)."""
    torii = M.get("torii", [])
    return _kept(locals(), ('torii',))


def _seg_0539__torii_spread_out(
    *,
    M: Any = _UNBOUND,
    _al: Any = _UNBOUND,
    _ax: Any = _UNBOUND,
    _axis_off: Any = _UNBOUND,
    _ay: Any = _UNBOUND,
    _ftpx: Any = _UNBOUND,
    _gap_max: Any = _UNBOUND,
    _in_field: Any = _UNBOUND,
    _set_out: Any = _UNBOUND,
    _tfloor: Any = _UNBOUND,
    check: Any = _UNBOUND,
    f: Any = _UNBOUND,
    far: Any = _UNBOUND,
    i: Any = _UNBOUND,
    j: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    mine: Any = _UNBOUND,
    near: Any = _UNBOUND,
    off: Any = _UNBOUND,
    r: Any = _UNBOUND,
    sh: Any = _UNBOUND,
    shrine: Any = _UNBOUND,
    spread: Any = _UNBOUND,
    sw: Any = _UNBOUND,
    sx: Any = _UNBOUND,
    sy: Any = _UNBOUND,
    t: Any = _UNBOUND,
    torii: Any = _UNBOUND,
    under: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 539 (shrine_avenue_fronts_the_hall, torii_clear_of_fields, torii_clear_of_shrine, torii_spread_out) - body verbatim from the legacy gate() (feature 022)."""
    if torii:
        shrine = M.get("shrine")
        if shrine:
            sx, sy, sw, sh = shrine
            under = [t for t in torii if sx - 6 <= t[0] <= sx + sw + 6 and sy - 6 <= t[1] <= sy + sh + 6]
            check("torii_clear_of_shrine", not under, f"{len(under)} torii under the shrine")
        # No two arches closer than one rail-span (16 ft): a dense senbon-style AVENUE may pack the arches
        # close, but they must not overlap into a vermilion blob. Scale-aware (was a fixed 25px, tuned to the
        # pre-true-scale 38px glyph - too coarse now the arch is ~8px/16ft at village scale; GM 2026-07-22).
        _tfloor = 16.0 / meta.get("ftpx", 1)
        spread = all(math.hypot(torii[i][0] - torii[j][0], torii[i][1] - torii[j][1]) > _tfloor for i in range(len(torii)) for j in range(i + 1, len(torii)))
        check("torii_spread_out", spread, f"torii closer than one arch-span (~{_tfloor:.0f}px) apart - they overlap into a blob rather than reading as distinct gateways")
        # NO ARCH STANDS IN A CROP (torii_clear_of_fields, 2026-07-24): caught during the torii
        # re-roll when Hirameki's Benten rolled 7 and the naive single-point avenue extension
        # marched five arches straight through the Imperial chrysanthemum field - torii are
        # overlap-EXEMPT structures (they legitimately stand over streets), so no generic pass
        # guarded them against fields. A sando is a cleared processional way: it may run BESIDE
        # a field (route the avenue's geometry around the crop), never through the planting.
        _in_field = [(round(t[0]), round(t[1])) for t in torii if any(point_in_poly(t[0], t[1], f["outline"]) for f in M.get("fields", []) + M.get("flower_fields", []))]
        check(
            "torii_clear_of_fields",
            not _in_field,
            f"torii arch(es) standing IN a field/flower-field at {_in_field[:4]} - a sando runs beside the crop, never through it; route the avenue geometry around the field",
        )

        # A village-shrine SANDO (>= 3 arches marching to the hall) puts its INNERMOST arch at the hall's
        # THRESHOLD, directly in front, not set out with a gap (GM 2026-07-22, "village shrines only"). Exempt the
        # modest 1-2 arch entrance (not a processional avenue) and the gateway-BESIDE-the-hall pattern (Hikari:
        # the hall stands aside the entrance track while the arches straddle the track, so it sits well OFF the
        # avenue axis). Village-scoped by kind=='shrine' (towns get monasteries, cities temples - a large-temple
        # sando with a courtyard between the outer arch and the main hall stays legitimate).
        _ftpx = meta.get("ftpx", 1)
        _gap_max = 36.0 / _ftpx  # innermost arch within ~36 ft of the hall front
        _axis_off = 50.0 / _ftpx  # hall >~50 ft off the avenue axis = a gateway beside it, not a sando to it
        _set_out = []
        for r in M.get("religious", []):
            if r.get("kind") != "shrine":
                continue
            mine = [t for t in torii if min(M["religious"], key=lambda rr: math.hypot(rr["x"] - t[0], rr["y"] - t[1])) is r]
            if len(mine) < 3:
                continue  # a 1-2 arch entrance is not a processional sando
            near = min(mine, key=lambda t: pt_to_rect(t[0], t[1], r))
            far = max(mine, key=lambda t: math.hypot(t[0] - r["x"], t[1] - r["y"]))
            _ax, _ay = near[0] - far[0], near[1] - far[1]
            _al = math.hypot(_ax, _ay) or 1.0
            _ax, _ay = _ax / _al, _ay / _al
            off = abs((r["x"] - near[0]) * (-_ay) + (r["y"] - near[1]) * _ax)  # hall's perpendicular offset from the axis
            if off > _axis_off:
                continue  # gateway beside the hall (Hikari), arches lining the track - not a sando to the hall
            if pt_to_rect(near[0], near[1], r) > _gap_max:
                _set_out.append((round(r["x"]), round(r["y"])))
        check(
            "shrine_avenue_fronts_the_hall",
            not _set_out,
            f"{len(_set_out)} village shrine(s) whose torii avenue stands off from the hall at {_set_out[:4]} - the innermost arch of a sando sits at the hall's threshold, directly in front, not set out with a gap",
        )
    return _kept(
        locals(),
        (
            '_al',
            '_ax',
            '_axis_off',
            '_ay',
            '_ftpx',
            '_gap_max',
            '_in_field',
            '_set_out',
            '_tfloor',
            'f',
            'far',
            'i',
            'j',
            'mine',
            'near',
            'off',
            'r',
            'sh',
            'shrine',
            'spread',
            'sw',
            'sx',
            'sy',
            't',
            'under',
        ),
    )


# ---- village-specific expectations (from meta) ---------------------------


def _seg_0540__abandoned(*, h: Any = _UNBOUND, houses: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 540 (abandoned, h) - body verbatim from the legacy gate() (feature 022)."""
    abandoned = sum(1 for h in houses if h["kind"] == "abandoned")
    return _kept(locals(), ('abandoned', 'h'))


def _seg_0541__occupied(*, abandoned: Any = _UNBOUND, houses: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 541 (occupied) - body verbatim from the legacy gate() (feature 022)."""
    occupied = len(houses) - abandoned
    return _kept(locals(), ('occupied',))


def _seg_0542__households_consistent(
    *,
    abandoned: Any = _UNBOUND,
    check: Any = _UNBOUND,
    hh: Any = _UNBOUND,
    hi: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    lo: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    occupied: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    t: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 542 (house_count_in_range, households_consistent) - body verbatim from the legacy gate() (feature 022)."""
    if meta.get("households"):
        # occupied farmhouses must portray the declared households ~1:1. A ~5-person
        # home is one nuclear/stem family per roof, and population / 5 = households =
        # farmhouses (GM: "population ~350 so there should be ~70 farmhouses"), so the
        # map DEPICTS close to the full household count - ~0.85-1.05x, allowing a few
        # off-frame homesteads or the odd shared roof. (Supersedes the earlier ~0.7x
        # extended-family assumption: the target is to depict every household.)
        hh = meta["households"]
        if meta.get("toscale", scale == "village"):  # to-scale tiers (village + hamlet) depict ~every household 1:1
            lo, hi = round(0.85 * hh), round(1.05 * hh)
        else:  # legacy tiers still depict ~0.7-0.9 (extended-family sharing, off-frame)
            lo, hi = round(0.68 * hh), round(0.9 * hh)
        check("households_consistent", lo <= occupied <= hi, f"{occupied} occupied houses for ~{hh} households (expect {lo}-{hi}; +{abandoned} abandoned)")
    elif meta.get("target_houses"):
        t = meta["target_houses"]
        lo, hi = round(0.85 * t), round(1.15 * t)
        check("house_count_in_range", lo <= len(houses) <= hi, f"{len(houses)} houses (expect ~{t})")
    elif scale in ("village", "hamlet"):
        lo, hi = (40, 80) if scale == "village" else (10, 30)
        check("house_count_in_range", lo <= len(houses) <= hi, f"{len(houses)} houses (expect {lo}-{hi} for a {scale})")
    return _kept(locals(), ('hh', 'hi', 'lo', 't'))


def _seg_0543_000__bk(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.000 (bk) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        bk: dict[str, int] = {}  # type: ignore[no-redef,unused-ignore]
    return _kept(locals(), ('bk',))


def _seg_0543_001__b(*, M: Any = _UNBOUND, b: Any = _UNBOUND, bk: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.001 (b, bk) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        for b in M.get("buildings", []):
            bk[b["kind"]] = bk.get(b["kind"], 0) + 1
    return _kept(locals(), ('b', 'bk'))


def _seg_0543_002__farmhouses(*, houses: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.002 (farmhouses) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        farmhouses = len(houses)
    return _kept(locals(), ('farmhouses',))


def _seg_0543_003__bands(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.003 (bands) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        bands = {"merchant": (20, 28), "laborer": (25, 35), "servant": (9, 17), "burakumin": (10, 14), "samurai": (5, 10)}
    return _kept(locals(), ('bands',))


# a caste's homes come in size variants (the wealthy get larger houses); count them together


def _seg_0543_004__VARIANTS(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.004 (VARIANTS) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        VARIANTS = {"merchant": ("merchant", "merchant_house", "merchant_large"), "laborer": ("laborer", "laborer_large"), "samurai": ("samurai", "samurai_large")}
    return _kept(locals(), ('VARIANTS',))


def _seg_0543_005__caste_n(*, VARIANTS: Any = _UNBOUND, bands: Any = _UNBOUND, bk: Any = _UNBOUND, k: Any = _UNBOUND, kind: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.005 (caste_n, k, kind) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        caste_n = {kind: sum(bk.get(k, 0) for k in VARIANTS.get(kind, (kind,))) for kind in bands}
    return _kept(locals(), ('caste_n', 'k', 'kind'))


def _seg_0543_006__town_caste_count(
    *, bands: Any = _UNBOUND, c: Any = _UNBOUND, caste_n: Any = _UNBOUND, check: Any = _UNBOUND, hi: Any = _UNBOUND, kind: Any = _UNBOUND, lo: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0543.006 (town_caste_count) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        for kind, (lo, hi) in bands.items():
            c = caste_n[kind]
            check(f"town_caste_count[{kind}]", lo <= c <= hi, f"{kind} buildings {c} outside budgets.md band [{lo},{hi}]")
    return _kept(locals(), ('c', 'hi', 'kind', 'lo'))


# SENIOR SAMURAI GET LARGER HOUSES at the county seat too (budgets.md's rank mix; the town
# analog of city_samurai_housing_varied - GM audit 2026-07): at least one samurai_large
# among a majority of small houses.


def _seg_0543_007__sl_t(*, bk: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.007 (sl_t) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        sl_t = bk.get("samurai_large", 0)
    return _kept(locals(), ('sl_t',))


def _seg_0543_008__ss_t(*, bk: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.008 (ss_t) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        ss_t = bk.get("samurai", 0)
    return _kept(locals(), ('ss_t',))


def _seg_0543_009__town_samurai_housing_varied(*, check: Any = _UNBOUND, scale: Any = _UNBOUND, sl_t: Any = _UNBOUND, ss_t: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.009 (town_samurai_housing_varied) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town' and (sl_t or ss_t):
        check(
            "town_samurai_housing_varied",
            sl_t >= 1 and ss_t > sl_t,
            f"samurai housing lacks rank variety (large={sl_t}, small={ss_t}) - the senior official(s) at a county seat keep a larger house among the juniors' small ones",
        )
    return _kept(locals(), ())


# THE BURAKUMIN QUARTER IS SEGREGATED - the doctrine word on every map, previously enforced
# nowhere (GM audit 2026-07): a band of OPEN GROUND separates it from every other caste's
# housing. TOWN-scoped: a city's ward system zones quarters wall-to-wall, so its
# segregation is zoning, not open ground (Tango/Nagahara adjacent-quarter seams run ~10px).
#
# 60 REAL FT BETWEEN THE WALLS, and both halves of that were wrong before 2026-07-27.
# It read "within 40px" measured CENTER TO CENTER, and 40 ft is less than the two
# half-diagonals of the houses it separates (44-51 ft here), so two roofs could touch and
# still pass a check whose message promised open ground. Hoshizora duly sat at a 23.6 ft
# seam, green. WHY 60: the rule has to distinguish a separate quarter from a dense one, and
# dwellings inside a quarter pack at ~10-30 ft, so the seam must be several times that to
# read as a gap at all rather than as a wide lane. Deliberately WELL BELOW the 120 ft
# pollution separation, because this is a zoning statement about who lives beside whom, not
# a buffer against kegare - the burakumin quarter is set apart, not held at arm's length,
# and the historical eta hamlet sits at the village edge or across its stream rather than a
# fixed distance out.


def _seg_0543_010__BURAKUMIN_SEAM_FT(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.010 (BURAKUMIN_SEAM_FT) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        BURAKUMIN_SEAM_FT = 60.0
    return _kept(locals(), ('BURAKUMIN_SEAM_FT',))
