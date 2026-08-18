"""Gate segments (moats drains and edges; keys 0465-0512) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from l7r.diagram.settlement import moat_current_at

from .common_01_geometry import Pt, _struct_rect, point_in_poly, poly_dist, rect_corners, seg_dist, seg_to_rect_dist, segments_cross
from .common_02_overlap_policy import in_ellipse
from .common_03_capacity import _UNBOUND, _kept


def _seg_0465___mjf(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 465 (_mjf) - body verbatim from the legacy gate() (feature 022)."""
    _mjf = M.get("moat_flow") or {}
    return _kept(locals(), ('_mjf',))


def _seg_0466__moat_junctions_swept_with_the_current(
    *,
    M: Any = _UNBOUND,
    _along: Any = _UNBOUND,
    _cur: Any = _UNBOUND,
    _head: Any = _UNBOUND,
    _hl: Any = _UNBOUND,
    _mfr: Any = _UNBOUND,
    _mj_bad: Any = _UNBOUND,
    _mj_current: Any = _UNBOUND,
    _mjc: Any = _UNBOUND,
    _mjf: Any = _UNBOUND,
    _mjp: Any = _UNBOUND,
    _mjr: Any = _UNBOUND,
    _mto: Any = _UNBOUND,
    _role: Any = _UNBOUND,
    _tap: Any = _UNBOUND,
    _who: Any = _UNBOUND,
    check: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 466 (moat_junctions_swept_with_the_current) - body verbatim from the legacy gate() (feature 022)."""
    if _mjr and len(_mjr) >= 3 and _mjf.get("inlet") and _mjf.get("outlet"):
        _mjn = len(_mjr)

        def _mj_current(tap_: Any) -> tuple[float, float] | None:
            return moat_current_at(_mjr, _mjf["inlet"], _mjf["outlet"], tap_)

        _mj_bad = []
        for _mjc in M.get("channels", []):
            _mjp = _mjc.get("poly") or []
            if len(_mjp) < 2:
                continue
            _mfr, _mto = (_mjc.get("frm") or {}), (_mjc.get("to") or {})
            if _mfr.get("kind") == "moat":  # an OFFTAKE leaves the ring: its mouth is the first step
                _tap, _head, _who, _role = _mjp[0], (_mjp[1][0] - _mjp[0][0], _mjp[1][1] - _mjp[0][1]), _mto.get("name", "?"), "offtake"
            elif _mto.get("kind") == "moat":  # a DRAIN arrives: its last step is the entry
                _tap, _head, _who, _role = _mjp[-1], (_mjp[-1][0] - _mjp[-2][0], _mjp[-1][1] - _mjp[-2][1]), _mfr.get("name", "?"), "drain"
            else:
                continue
            _cur = _mj_current(_tap)
            _hl = math.hypot(*_head)
            if _cur is None or _hl == 0:
                continue
            _along = (_head[0] * _cur[0] + _head[1] * _cur[1]) / _hl
            # A SQUARE TAP IS THE DEFECT, not merely an upstream-facing one. Canal practice: the best
            # offtake alignment is 0 deg to the parent, separating out in transition, and the studied
            # optimum for water and sediment is 15-45 deg - explicitly "30 or 45 INSTEAD OF 90". A
            # perpendicular junction sheds sediment into its own mouth and, on the page, says nothing
            # about which way the water goes. 75 deg is the generous line for "clearly swept": well
            # outside the textbook band, and the engine's two correct junctions (nw1 35, fn1 41) sit
            # comfortably inside it.
            if _along <= math.cos(math.radians(75.0)):
                _mj_bad.append(f"{_who} ({_role}, {math.degrees(math.acos(max(-1.0, min(1.0, _along)))):.0f} deg)")
        check(
            "moat_junctions_swept_with_the_current",
            not _mj_bad,
            f"moat junction(s) not swept downstream: {_mj_bad} - where a channel meets the moat its local heading at "
            f"the junction must carry a DOWNSTREAM component. A tributary joins pointing downstream and an offtake "
            f"takes off downstream; a junction angled back up the current reads as water doubling on itself. Flip the "
            f"offtake tee's along-rim step (or the drain culvert's landing point) to the downstream side",
        )
    return _kept(locals(), ('_along', '_cur', '_head', '_hl', '_mfr', '_mj_bad', '_mj_current', '_mjc', '_mjn', '_mjp', '_mto', '_role', '_tap', '_who'))


# WATER JOINS WATER AT A CONFLUENCE, NEVER CROSSES IT (GM 2026-07-23, feature 014 endgame: "I can
# visually see the intersection where ditches and channels just run into the moat... they just keep
# going and aren't intersecting at the edge"). A channel/ditch segment that strictly CROSSES the
# moat or river centerline mid-run reads as a line painted straight over the open water - a mouth
# must END at the bank instead (the engine's _clip_to_moat/_clip_to_river trim the DRAWING to the
# bed edge + cap radius, and taps/culverts wear the receiving water's own color). The RECORDED
# topology legitimately ends ON the centerline (the anchor checks demand it), so a crossing on a
# polyline's first/last segment whose terminal vertex sits near the crossed water segment is the
# sanctioned confluence touch; anything else is a crossing.


def _seg_0467__xing_w() -> dict[str, Any]:
    """Gate segment 467 (xing_w) - body verbatim from the legacy gate() (feature 022)."""
    xing_w = []  # type: ignore[var-annotated]
    return _kept(locals(), ('xing_w',))


def _seg_0468___wbodies() -> dict[str, Any]:
    """Gate segment 468 (_wbodies) - body verbatim from the legacy gate() (feature 022)."""
    _wbodies = []  # type: ignore[var-annotated]
    return _kept(locals(), ('_wbodies',))


def _seg_0469___wbodies_1(*, M: Any = _UNBOUND, _wbodies: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 469 (_wbodies) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("moat") and len(M["moat"]) >= 3:
        _wbodies.append(("moat", M["moat"]))
    return _kept(locals(), ('_wbodies',))


def _seg_0470___wbodies_2(*, M: Any = _UNBOUND, _wbodies: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 470 (_wbodies) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("river") and (M["river"].get("pts") if isinstance(M.get("river"), dict) else None):
        _wbodies.append(("river", M["river"]["pts"]))
    return _kept(locals(), ('_wbodies',))


def _seg_0471___a(
    *,
    M: Any = _UNBOUND,
    _a: Any = _UNBOUND,
    _b: Any = _UNBOUND,
    _ch: Any = _UNBOUND,
    _conf: Any = _UNBOUND,
    _i: Any = _UNBOUND,
    _k: Any = _UNBOUND,
    _nm: Any = _UNBOUND,
    _pl: Any = _UNBOUND,
    _wb: Any = _UNBOUND,
    _wbodies: Any = _UNBOUND,
    xing_w: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 471 (_a, _b, _ch, _conf) - body verbatim from the legacy gate() (feature 022)."""
    if _wbodies:
        for _ch in M.get("channels", []) + M.get("field_ditches", []):
            _pl = _ch.get("poly") or []  # a short/absent poly simply yields no segments
            for _i in range(len(_pl) - 1):
                _a, _b = _pl[_i], _pl[_i + 1]
                for _nm, _wb in _wbodies:
                    for _k in range(len(_wb) - 1):
                        if not segments_cross(_a, _b, _wb[_k], _wb[_k + 1]):
                            continue
                        _conf = (_i == 0 and seg_dist(_pl[0][0], _pl[0][1], _wb[_k], _wb[_k + 1]) < 20) or (_i == len(_pl) - 2 and seg_dist(_pl[-1][0], _pl[-1][1], _wb[_k], _wb[_k + 1]) < 20)
                        if not _conf:
                            xing_w.append((_nm, round(_a[0]), round(_a[1])))
    return _kept(locals(), ('_a', '_b', '_ch', '_conf', '_i', '_k', '_nm', '_pl', '_wb', 'xing_w'))


def _seg_0472__channels_join_water_not_cross(*, check: Any = _UNBOUND, xing_w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 472 (channels_join_water_not_cross) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "channels_join_water_not_cross",
        not xing_w,
        f"channel/ditch segment(s) CROSS a moat/river centerline mid-run at {sorted(set(xing_w))[:4]} - water joins "
        "water at a CONFLUENCE (the mouth ends at the bank, engine-trimmed and water-colored), it never runs "
        "straight across the open water like a painted line; end the polyline at the centerline (the anchor "
        "convention) instead of passing through",
    )
    return _kept(locals(), ())


# THE POND FILL COVERS EVERY JOINING MOUTH (GM 2026-07-23, Tango's in-wall tank: the comb
# head-race's round end-cap rendered ON TOP of the pond and the channel read as INTERSECTING
# the open water instead of joining it). Doctrine (settlements.md "A pond JOINS its feeders at
# the rim"): a joining course must overshoot the rim so its bed covers the rim stroke at the
# mouth - the clean gap - which in turn requires the POND FILL to paint over that overshoot.
# That is a Z-ORDER property, so it is checked via recorded draw positions like
# waterways_merge_at_crossings: the engine records every drawn comb/field channel stroke in
# M['drawn_channels'] (post-clip geometry + bedz + late flag) and the pond fill's position in
# M['pond_layer'] (relocated into the LATE water block when a late-block channel joins - the
# Tango case: the late block draws after the shared block, so an early fill can never cover a
# late mouth). bedz values are offsets within their OWN splice block, NOT globally comparable -
# cross-block draw order is carried by the (late, bedz) PAIR, compared lexicographically (the
# late block always renders after the whole shared block; streams/channels are always early).
# Three clauses: (a) a pond join with NO layering records is exactly the uncovered cap (fires
# the frozen pre-fix Tango fixture); (b) every z-recorded joining bed must sit BELOW the fill
# in (late, bedz) order; (c) a drawn stroke must never run THROUGH the open water mid-run
# (mouths, not crossings - the pond sibling of channels_join_water_not_cross). Undrawn
# (drawn=False) topology conduits are exempt: nothing rendered, nothing to cover.


def _seg_0473__pond_e(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 473 (pond_e) - body verbatim from the legacy gate() (feature 022)."""
    pond_e = M.get("pond")
    return _kept(locals(), ('pond_e',))


def _seg_0474__pond_fill_covers_channel_mouths(
    *,
    M: Any = _UNBOUND,
    _ditch_joins: Any = _UNBOUND,
    _pjz: Any = _UNBOUND,
    _pl: Any = _UNBOUND,
    _pz: Any = _UNBOUND,
    blate: Any = _UNBOUND,
    bz: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    dc: Any = _UNBOUND,
    dd: Any = _UNBOUND,
    k: Any = _UNBOUND,
    pond_bad: Any = _UNBOUND,
    pond_e: Any = _UNBOUND,
    pt: Any = _UNBOUND,
    q: Any = _UNBOUND,
    st: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 474 (pond_fill_covers_channel_mouths) - body verbatim from the legacy gate() (feature 022)."""
    if pond_e:
        _pjz: list[tuple[Any, Any, bool]] = []  # type: ignore[no-redef]  # (endpoint, bedz, late) of every z-recorded course touching the rim zone
        for dc in M.get("drawn_channels", []):
            for pt in (dc["pts"][0], dc["pts"][-1]):
                if in_ellipse(pt[0], pt[1], pond_e, scale=1.06):
                    _pjz.append((pt, dc.get("bedz"), bool(dc.get("late"))))
        for st in M.get("streams", []):
            for pt in (st["poly"][0], st["poly"][-1]):
                if in_ellipse(pt[0], pt[1], pond_e, scale=1.06):
                    _pjz.append((pt, st.get("bedz"), False))
        for c in M.get("channels", []):
            # drawn=False marks an implied underground conduit; a record with NO bedz is a gen-side
            # TOPOLOGY entry (its visible stroke, if any, is recorded separately in drawn_channels -
            # Hoshigaoka's head-race). Only a bed s.channel actually drew (bedz recorded) can cover
            # or fail to cover anything.
            if c.get("drawn") is False or c.get("bedz") is None:
                continue
            for pt in (c["poly"][0], c["poly"][-1]):
                if in_ellipse(pt[0], pt[1], pond_e, scale=1.06):
                    _pjz.append((pt, c.get("bedz"), False))
        # a comb ditch is always drawn: a joining ditch record demands a matching drawn stroke record
        _ditch_joins = any(in_ellipse(pt[0], pt[1], pond_e, scale=1.06) for dd in M.get("field_ditches", []) for pt in (dd["poly"][0], dd["poly"][-1]))
        _pl = M.get("pond_layer") or {}
        _pz = _pl.get("bedz")
        pond_bad: list[str] = []  # type: ignore[no-redef]
        if (_pjz or _ditch_joins) and _pz is None:
            pond_bad.append("a course joins the pond but M['pond_layer'] records no fill position")
        if _ditch_joins and not any(in_ellipse(dc["pts"][k][0], dc["pts"][k][1], pond_e, scale=1.06) for dc in M.get("drawn_channels", []) for k in (0, -1)):
            pond_bad.append("a field ditch joins the pond but no drawn stroke is recorded in M['drawn_channels']")
        pond_bad += [f"bed at {(round(pt[0]), round(pt[1]))} not under the fill" for pt, bz, blate in _pjz if _pz is not None and (bz is None or (blate, bz) >= (bool(_pl.get("late")), _pz))]
        pond_bad += [
            f"drawn stroke runs THROUGH the open water at {(round(q[0]), round(q[1]))}" for dc in M.get("drawn_channels", []) for q in dc["pts"][1:-1] if in_ellipse(q[0], q[1], pond_e, scale=0.9)
        ]
        check(
            "pond_fill_covers_channel_mouths",
            not pond_bad,
            "a channel INTERSECTS the pond instead of joining it: " + "; ".join(sorted(set(pond_bad))[:4]) + " - a mouth overshoots the rim (covering the rim stroke) and the pond FILL "
            "must draw over that overshoot; route the stroke through s.field_channel/s.channel/s.stream and let the engine relocate the fill to the late block when a late course joins",
        )
    return _kept(locals(), ('_ditch_joins', '_pjz', '_pl', '_pz', 'blate', 'bz', 'c', 'dc', 'dd', 'k', 'pond_bad', 'pt', 'q', 'st'))


# A WATER-TO-WATER HANDOFF SHOWS ITS CONTROL GATE (GM 2026-07-23, the junction-seams pass): where a
# moat/river tap hands off to the comb's own canal (the sluice - the palette seam sits exactly there)
# and where a field drain hands off to its outfall culvert into the moat, a sluice_gate glyph must
# mark the junction - the control board is what makes the color/direction change read as engineered
# plumbing rather than two strokes crossing. The tap's recorded poly is [water-vertex, sluice, plot],
# so the gate belongs near poly[1]; a drain culvert's is [drain-end, moat-vertex], gate near poly[0].


def _seg_0475__gateless() -> dict[str, Any]:
    """Gate segment 475 (gateless) - body verbatim from the legacy gate() (feature 022)."""
    gateless = []  # type: ignore[var-annotated]
    return _kept(locals(), ('gateless',))


def _seg_0476___sgs(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 476 (_sgs) - body verbatim from the legacy gate() (feature 022)."""
    _sgs = M.get("sluice_gates", [])
    return _kept(locals(), ('_sgs',))


def _seg_0477___ch(
    *, M: Any = _UNBOUND, _ch: Any = _UNBOUND, _fk: Any = _UNBOUND, _g: Any = _UNBOUND, _jp: Any = _UNBOUND, _pl: Any = _UNBOUND, _sgs: Any = _UNBOUND, _tk: Any = _UNBOUND, gateless: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 477 (_ch, _fk, _g, _jp) - body verbatim from the legacy gate() (feature 022)."""
    for _ch in M.get("channels", []):
        _fk = (_ch.get("frm") or {}).get("kind")
        _tk = (_ch.get("to") or {}).get("kind")
        _pl = _ch.get("poly") or []
        _jp = None
        if _fk in ("moat", "river") and _tk == "field" and len(_pl) >= 2:
            _jp = _pl[1]  # the sluice point
        elif _fk == "drain" and _tk == "moat" and _pl and _ch.get("drawn"):
            _jp = _pl[0]  # the drain -> culvert handoff (drawn culverts only: an UNDROWN record is an
            # implied underground conduit - Tango's in-wall nw1 drain drops beneath the rampart - with
            # no visible seam to gate)
        if _jp is not None and not any(math.hypot(_g["x"] - _jp[0], _g["y"] - _jp[1]) <= 16 for _g in _sgs):
            gateless.append((round(_jp[0]), round(_jp[1])))
    return _kept(locals(), ('_ch', '_fk', '_g', '_jp', '_pl', '_tk', 'gateless'))


def _seg_0478__channel_gates_at_water_junctions(*, check: Any = _UNBOUND, gateless: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 478 (channel_gates_at_water_junctions) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "channel_gates_at_water_junctions",
        not gateless,
        f"water-to-water handoff(s) with no sluice gate at {sorted(set(gateless))[:4]} - a moat/river tap "
        "hands off to the comb canal (and a drain to its outfall culvert) through a CONTROL GATE; draw "
        "s.sluice_gate(x, y, rot=<channel heading + 90>) at the junction so the palette seam reads as "
        "engineered plumbing, not two strokes crossing",
    )
    return _kept(locals(), ())


# AN IN-WALL DRAIN CUTS OFF AT A GATE BEFORE THE RING ROAD (GM 2026-07-23, Tango's in-wall
# nw1 drain: the visible runoff ditch ran up to the patrol road's verge and simply STOPPED -
# a bare cut end, unfinished linework). Doctrine: a walled city's in-wall drainage never
# visibly pierces road, rampart or moat - the water leaves through an UNDERGROUND stone
# culvert, recorded as an undrawn drain->moat conduit (channel_gates_at_water_junctions
# deliberately exempts that conduit's invisible moat-side seam). But the DROP into the
# culvert is a real engineered structure and the map must say so: the visible ditch is
# TRIMMED back to a cut point clear of the ring road and wears a sluice_gate glyph there
# (the gate is what tells the reader the ditch drains into artificial plumbing connected to
# the moat, even though the connection itself is invisible). The conduit's START is that cut
# point - where the water goes underground. For every undrawn drain->moat conduit starting
# INSIDE the wall: (a) a drawn stroke must END at the conduit's start (the visible ditch
# reaches the drop - within 8px); (b) the cut point stays >= half the ring-road width + 4px
# off the ring-road centerline, and no drawn stroke touching it crosses the centerline (the
# pre-fix Tango stub lapped 3px PAST it); (c) a sluice_gate sits within 16px of the cut
# point (the gate tolerance channel_gates_at_water_junctions uses). Engine helper:
# s.inwall_drain_outfall() trims the drain, places the gate, and records the conduit.


def _seg_0479__inwall_bad() -> dict[str, Any]:
    """Gate segment 479 (inwall_bad) - body verbatim from the legacy gate() (feature 022)."""
    inwall_bad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('inwall_bad',))


def _seg_0480___ch_1(
    *,
    M: Any = _UNBOUND,
    _ch: Any = _UNBOUND,
    _co: Any = _UNBOUND,
    _irhw: Any = _UNBOUND,
    _iring: Any = _UNBOUND,
    _iw_touch: Any = _UNBOUND,
    _spts: Any = _UNBOUND,
    dc: Any = _UNBOUND,
    g: Any = _UNBOUND,
    i: Any = _UNBOUND,
    inwall_bad: Any = _UNBOUND,
    j: Any = _UNBOUND,
    k: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 480 (_ch, _co, _irhw, _iring) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("wall"):
        _iring = M.get("ring_road") or []
        _irhw = (M.get("ring_road_width") or 20) / 2
        for _ch in M.get("channels", []):
            if (_ch.get("frm") or {}).get("kind") != "drain" or (_ch.get("to") or {}).get("kind") != "moat" or _ch.get("drawn"):
                continue  # drawn culverts carry their gate at the drain handoff (checked above)
            _co = _ch["poly"][0]
            if not point_in_poly(_co[0], _co[1], M["wall"]):
                continue  # an outside-the-wall conduit has no rampart to pass under
            _iw_touch = [dc["pts"] for dc in M.get("drawn_channels", []) if any(math.hypot(dc["pts"][k][0] - _co[0], dc["pts"][k][1] - _co[1]) <= 8 for k in (0, -1))]
            if not _iw_touch:
                inwall_bad.append(f"no visible ditch reaches the drop at {(round(_co[0]), round(_co[1]))}")
            if _iring and min(seg_dist(_co[0], _co[1], _iring[i], _iring[i + 1]) for i in range(len(_iring) - 1)) < _irhw + 4:
                inwall_bad.append(f"cut point {(round(_co[0]), round(_co[1]))} rides the ring road - trim the ditch off short of the patrol road")
            for _spts in _iw_touch:
                if any(segments_cross(_spts[i], _spts[i + 1], _iring[j], _iring[j + 1]) for i in range(len(_spts) - 1) for j in range(len(_iring) - 1)):
                    inwall_bad.append(f"the ditch at {(round(_co[0]), round(_co[1]))} CROSSES the ring road - it must stop before it")
            if not any(math.hypot(g["x"] - _co[0], g["y"] - _co[1]) <= 16 for g in M.get("sluice_gates", [])):
                inwall_bad.append(f"no sluice gate at the cutoff {(round(_co[0]), round(_co[1]))}")
    return _kept(locals(), ('_ch', '_co', '_irhw', '_iring', '_iw_touch', '_spts', 'dc', 'g', 'i', 'inwall_bad', 'j', 'k'))


def _seg_0481__inwall_drains_gated_at_cutoff(*, check: Any = _UNBOUND, inwall_bad: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 481 (inwall_drains_gated_at_cutoff) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "inwall_drains_gated_at_cutoff",
        not inwall_bad,
        "; ".join(sorted(set(inwall_bad))[:4]) + " - an in-wall drain cuts off short of the ring road and drops through a "
        "sluice gate into the underground culvert to the moat (the gate glyph is what makes the bare cut end read as "
        "engineered plumbing); trim the drain through s.inwall_drain_outfall()",
    )
    return _kept(locals(), ())


# large area features (forests, pastures) near a map edge must run OFF it - implying
# they continue beyond what's drawn. Bounded farm fields are exempt.


def _seg_0482__NEAR() -> dict[str, Any]:
    """Gate segment 482 (NEAR) - body verbatim from the legacy gate() (feature 022)."""
    NEAR = 55
    return _kept(locals(), ('NEAR',))


def _seg_0483__area_feats(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 483 (area_feats) - body verbatim from the legacy gate() (feature 022)."""
    area_feats = [("forest", M["forest"])] if M.get("forest") else []
    return _kept(locals(), ('area_feats',))


def _seg_0484__area_feats_1(*, M: Any = _UNBOUND, area_feats: Any = _UNBOUND, fp: Any = _UNBOUND, i: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 484 (area_feats, fp, i) - body verbatim from the legacy gate() (feature 022)."""
    area_feats += [(f"forest_patch[{i}]", fp) for i, fp in enumerate(M.get("forest_patches", []))]
    return _kept(locals(), ('area_feats', 'fp', 'i'))


def _seg_0485__area_feats_2(*, M: Any = _UNBOUND, area_feats: Any = _UNBOUND, i: Any = _UNBOUND, ps: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 485 (area_feats, i, ps) - body verbatim from the legacy gate() (feature 022)."""
    area_feats += [(f"pasture[{i}]", ps) for i, ps in enumerate(M.get("pastures", []))]
    return _kept(locals(), ('area_feats', 'i', 'ps'))


def _seg_0486__edge_bad() -> dict[str, Any]:
    """Gate segment 486 (edge_bad) - body verbatim from the legacy gate() (feature 022)."""
    edge_bad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('edge_bad',))


def _seg_0487__edge_bad_1(
    *,
    EX0: Any = _UNBOUND,
    EX1: Any = _UNBOUND,
    EY0: Any = _UNBOUND,
    EY1: Any = _UNBOUND,
    NEAR: Any = _UNBOUND,
    area_feats: Any = _UNBOUND,
    edge_bad: Any = _UNBOUND,
    nm: Any = _UNBOUND,
    ol: Any = _UNBOUND,
    p: Any = _UNBOUND,
    xs: Any = _UNBOUND,
    ys: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 487 (edge_bad, nm, ol, p) - body verbatim from the legacy gate() (feature 022)."""
    for nm, ol in area_feats:
        xs, ys = [p[0] for p in ol], [p[1] for p in ol]
        if EX1 - NEAR <= max(xs) < EX1:
            edge_bad.append(f"{nm}:right")
        if EX0 < min(xs) <= EX0 + NEAR:
            edge_bad.append(f"{nm}:left")
        if EY1 - NEAR <= max(ys) < EY1:
            edge_bad.append(f"{nm}:bottom")
        if EY0 < min(ys) <= EY0 + NEAR:
            edge_bad.append(f"{nm}:top")
    return _kept(locals(), ('edge_bad', 'nm', 'ol', 'p', 'xs', 'ys'))


def _seg_0488__edge_features_run_off_map(*, check: Any = _UNBOUND, edge_bad: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 488 (edge_features_run_off_map) - body verbatim from the legacy gate() (feature 022)."""
    check("edge_features_run_off_map", not edge_bad, f"edge feature(s) stop short of the edge: {edge_bad}")
    return _kept(locals(), ())


# roads and streams must run off the map edge (a stream may instead end in a pond
# at one end; irrigation channels are exempt - they connect ponds/fields)


def _seg_0489__EDGE() -> dict[str, Any]:
    """Gate segment 489 (EDGE) - body verbatim from the legacy gate() (feature 022)."""
    EDGE = 30
    return _kept(locals(), ('EDGE',))


def _seg_0490__at_edge(*, EDGE: Any = _UNBOUND, EX0: Any = _UNBOUND, EX1: Any = _UNBOUND, EY0: Any = _UNBOUND, EY1: Any = _UNBOUND, pt: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 490 (at_edge) - body verbatim from the legacy gate() (feature 022)."""

    def at_edge(pt: Pt) -> bool:
        return pt[0] <= EX0 + EDGE or pt[0] >= EX1 - EDGE or pt[1] <= EY0 + EDGE or pt[1] >= EY1 - EDGE  # type: ignore[no-any-return]

    return _kept(locals(), ('at_edge',))


def _seg_0491__road_runs_off_edge(*, at_edge: Any = _UNBOUND, check: Any = _UNBOUND, road: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 491 (road_runs_off_edge) - body verbatim from the legacy gate() (feature 022)."""
    if road:
        check("road_runs_off_edge", at_edge(road[0]) and at_edge(road[-1]), f"a road must reach the map edge at both ends (ends {road[0]}, {road[-1]})")
    return _kept(locals(), ())


# a CONNECTOR lane (the trodden path leaving the village for the wider world) must run OFF the map
# edge - it links to a district/Imperial road (or a canal landing) beyond the frame, so it must not
# stop mid-landscape. Internal lanes (the spine, field spurs) are exempt: they legitimately end in
# the cluster or at the paddy. See settlements.md 'Village lanes and connecting paths'.


def _seg_0492__connector_lane_runs_off_edge(*, M: Any = _UNBOUND, at_edge: Any = _UNBOUND, check: Any = _UNBOUND, i: Any = _UNBOUND, ln: Any = _UNBOUND, p: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 492 (connector_lane_runs_off_edge) - body verbatim from the legacy gate() (feature 022)."""
    for i, ln in enumerate(M.get("lanes", [])):
        if ln.get("connector"):
            p = ln["pts"]
            check(
                f"connector_lane_runs_off_edge[{i}]",
                at_edge(p[0]) or at_edge(p[-1]),
                f"the connector path (lane {i}) must run OFF the map edge (ends {p[0]}, {p[-1]}) - it leaves the village for the wider world and must not stop mid-landscape",
            )
    return _kept(locals(), ('i', 'ln', 'p'))


# FARMHOUSES must not sit ON a village lane - a lane lays a no-build corridor and houses FRONT it,
# never overlap the tread (place lanes BEFORE the houses). Fires if any house footprint corner/center
# falls within the lane's tread half-width.


def _seg_0493___house_pts(*, h: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 493 (_house_pts) - body verbatim from the legacy gate() (feature 022)."""

    def _house_pts(h: dict[str, Any]) -> list[tuple[float, float]]:
        # THE RAKE IS PART OF THE FOOTPRINT (feature 121). This built its own axis-aligned corner
        # list, while `rect_corners` - already imported, already used by the overlap checks - has
        # read `rot` all along. A farmhouse is DRAWN raked by +/-5 deg, so the square-on version
        # measured a rect the map does not draw, and disagreed with the placer's own tread test:
        # a seat `_house_on_a_tread` had cleared came back from the gate as a house on a lane.
        # ONE MEASUREMENT, NOT SEVERAL - the duplicate is why the two could drift apart at all.
        # GAP VERDICT family: real rotated corners. The centre stays in the list because a lane
        # narrower than a house would otherwise thread between its corners.
        return [*rect_corners({**h, "rot": h.get("rot", 0.0)}), (h["x"], h["y"])]

    return _kept(locals(), ('_house_pts',))


def _seg_0494__lane_hits() -> dict[str, Any]:
    """Gate segment 494 (lane_hits) - body verbatim from the legacy gate() (feature 022)."""
    lane_hits = []  # type: ignore[var-annotated]
    return _kept(locals(), ('lane_hits',))


def _seg_0495__cx(
    *,
    M: Any = _UNBOUND,
    _house_pts: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    h: Any = _UNBOUND,
    half: Any = _UNBOUND,
    k: Any = _UNBOUND,
    lane_hits: Any = _UNBOUND,
    ln: Any = _UNBOUND,
    p: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 495 (cx, cy, h, half) - body verbatim from the legacy gate() (feature 022)."""
    for h in M.get("houses", []):
        for ln in M.get("lanes", []):
            half = ln.get("w", 5) / 2 + 2  # tread half-width + a hair
            p = ln["pts"]
            if any(seg_dist(cx, cy, p[k], p[k + 1]) < half for cx, cy in _house_pts(h) for k in range(len(p) - 1)):
                lane_hits.append((round(h["x"]), round(h["y"])))
                break
    return _kept(locals(), ('cx', 'cy', 'h', 'half', 'k', 'lane_hits', 'ln', 'p'))


def _seg_0496__houses_clear_of_lanes(*, check: Any = _UNBOUND, lane_hits: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 496 (houses_clear_of_lanes) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "houses_clear_of_lanes",
        not lane_hits,
        f"farmhouse(s) sit ON a village lane at {lane_hits[:5]} - a lane is a no-build corridor; houses FRONT it, never overlap the tread (lay lanes BEFORE the houses so they pack around it)",
    )
    return _kept(locals(), ())


# A shrine/temple HALL must not sit ON a lane/street/road: a building stands BESIDE the way, not in it. The
# TORII is the deliberate exception - a gateway arch straddles the approach path and the road runs UNDER it
# (a real, common feature), so torii are NOT checked here. The road may run up to and through the torii to a
# hall set just off the way. Covers religious halls (shrine/monastery/temple). WHY: settlements.md 'Shrines'.


def _seg_0497__hall_on_lane() -> dict[str, Any]:
    """Gate segment 497 (hall_on_lane) - body verbatim from the legacy gate() (feature 022)."""
    hall_on_lane = []  # type: ignore[var-annotated]
    return _kept(locals(), ('hall_on_lane',))


def _seg_0498___hcorr(*, M: Any = _UNBOUND, ln: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 498 (_hcorr, ln) - body verbatim from the legacy gate() (feature 022)."""
    _hcorr = [(ln["pts"], ln.get("w", 6) / 2 + 2) for ln in M.get("lanes", [])]
    return _kept(locals(), ('_hcorr', 'ln'))


def _seg_0499___hcorr_1(*, M: Any = _UNBOUND, _hcorr: Any = _UNBOUND, s: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 499 (_hcorr, s) - body verbatim from the legacy gate() (feature 022)."""
    _hcorr += [(s["pts"], s.get("w", 10) / 2 + 2) for s in M.get("town_streets", [])]
    return _kept(locals(), ('_hcorr', 's'))


def _seg_0500___hcorr_2(*, M: Any = _UNBOUND, _hcorr: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 500 (_hcorr) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("road"):
        _hcorr.append((M["road"], M.get("road_width", 26) / 2 + 2))
    return _kept(locals(), ('_hcorr',))


def _seg_0501__half(
    *, M: Any = _UNBOUND, _hcorr: Any = _UNBOUND, half: Any = _UNBOUND, hall: Any = _UNBOUND, hall_on_lane: Any = _UNBOUND, k: Any = _UNBOUND, p: Any = _UNBOUND, rect: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 501 (half, hall, hall_on_lane, k) - body verbatim from the legacy gate() (feature 022)."""
    for hall in M.get("religious", []):
        rect = _struct_rect(hall)
        if any(seg_to_rect_dist(p[k], p[k + 1], rect) < half for p, half in _hcorr for k in range(len(p) - 1)):
            hall_on_lane.append((round(hall["x"]), round(hall["y"])))
    return _kept(locals(), ('half', 'hall', 'hall_on_lane', 'k', 'p', 'rect'))


def _seg_0502__shrine_halls_clear_of_lanes(*, check: Any = _UNBOUND, hall_on_lane: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 502 (shrine_halls_clear_of_lanes) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "shrine_halls_clear_of_lanes",
        not hall_on_lane,
        f"shrine/temple hall(s) sit ON a lane/street/road at {hall_on_lane[:4]} - a HALL stands beside the way, "
        f"not in it (place it off the corridor); the road may pass UNDER the shrine's TORII (arches are exempt), "
        f"but never through the hall itself",
    )
    return _kept(locals(), ())


# TREES must not be drawn ON a lane / street / road - a path is bare trodden earth, not planted over. Covers
# BOTH the communal fengshui grove (village_groves: each records its actual drawn clump centers + radius) and
# the per-house windbreak grove (groves: a rect footprint). Every corridor (lanes, town streets, the road) is
# a keep-out; the generator skips any clump within it, and this verifies nothing slipped through.


def _seg_0503__corridors(*, M: Any = _UNBOUND, ln: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 503 (corridors, ln) - body verbatim from the legacy gate() (feature 022)."""
    corridors = [(ln["pts"], ln.get("w", 6) / 2) for ln in M.get("lanes", [])]
    return _kept(locals(), ('corridors', 'ln'))


def _seg_0504__corridors_1(*, M: Any = _UNBOUND, corridors: Any = _UNBOUND, s: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 504 (corridors, s) - body verbatim from the legacy gate() (feature 022)."""
    corridors += [(s["pts"], s.get("w", 10) / 2) for s in M.get("town_streets", [])]
    return _kept(locals(), ('corridors', 's'))


def _seg_0505__corridors_2(*, M: Any = _UNBOUND, corridors: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 505 (corridors) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("road"):
        corridors.append((M["road"], M.get("road_width", 26) / 2))
    return _kept(locals(), ('corridors',))


def _seg_0506__tree_on_path() -> dict[str, Any]:
    """Gate segment 506 (tree_on_path) - body verbatim from the legacy gate() (feature 022)."""
    tree_on_path = []  # type: ignore[var-annotated]
    return _kept(locals(), ('tree_on_path',))


def _seg_0507__cx_1(
    *,
    M: Any = _UNBOUND,
    corridors: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    g: Any = _UNBOUND,
    half: Any = _UNBOUND,
    k: Any = _UNBOUND,
    p: Any = _UNBOUND,
    r: Any = _UNBOUND,
    tree_on_path: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 507 (cx, cy, g, half) - body verbatim from the legacy gate() (feature 022)."""
    for g in M.get("village_groves", []):
        r = g.get("r", 6)
        for cx, cy in g.get("clumps", []):
            if any(seg_dist(cx, cy, p[k], p[k + 1]) < half + r for p, half in corridors for k in range(len(p) - 1)):
                tree_on_path.append((round(cx), round(cy)))
                break
    return _kept(locals(), ('cx', 'cy', 'g', 'half', 'k', 'p', 'r', 'tree_on_path'))


def _seg_0508__cx_2(
    *,
    M: Any = _UNBOUND,
    corridors: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    g: Any = _UNBOUND,
    gc: Any = _UNBOUND,
    half: Any = _UNBOUND,
    k: Any = _UNBOUND,
    p: Any = _UNBOUND,
    tree_on_path: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 508 (cx, cy, g, gc) - body verbatim from the legacy gate() (feature 022)."""
    for g in M.get("groves", []):
        gc = rect_corners(_struct_rect(g)) + [(g["x"], g["y"])]
        if any(seg_dist(cx, cy, p[k], p[k + 1]) < half for cx, cy in gc for p, half in corridors for k in range(len(p) - 1)):
            tree_on_path.append((round(g["x"]), round(g["y"])))
    return _kept(locals(), ('cx', 'cy', 'g', 'gc', 'half', 'k', 'p', 'tree_on_path'))


def _seg_0509__groves_clear_of_lanes(*, check: Any = _UNBOUND, tree_on_path: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 509 (groves_clear_of_lanes) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "groves_clear_of_lanes",
        not tree_on_path,
        f"tree/grove clump(s) sit ON a lane/street/road at {tree_on_path[:4]} - a path is bare trodden earth; keep vegetation off every corridor (the generator skips clumps within a lane's keep-out)",
    )
    return _kept(locals(), ())


def _seg_0510__moat_ring_1(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 510 (moat_ring) - body verbatim from the legacy gate() (feature 022)."""
    moat_ring = M.get("moat")
    return _kept(locals(), ('moat_ring',))


def _seg_0511__stream_runs_off_edge(
    *,
    M: Any = _UNBOUND,
    anchored: Any = _UNBOUND,
    at_ditch: Any = _UNBOUND,
    at_drain: Any = _UNBOUND,
    at_edge: Any = _UNBOUND,
    at_moat: Any = _UNBOUND,
    at_river: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d: Any = _UNBOUND,
    dp: Any = _UNBOUND,
    e: Any = _UNBOUND,
    e0: Any = _UNBOUND,
    e1: Any = _UNBOUND,
    f: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    i: Any = _UNBOUND,
    idx: Any = _UNBOUND,
    in_field: Any = _UNBOUND,
    in_pond: Any = _UNBOUND,
    moat_ring: Any = _UNBOUND,
    ok: Any = _UNBOUND,
    p: Any = _UNBOUND,
    pond: Any = _UNBOUND,
    st: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 511 (stream_runs_off_edge) - body verbatim from the legacy gate() (feature 022)."""
    for idx, st in enumerate(M.get("streams", [])):
        e0, e1 = st["poly"][0], st["poly"][-1]

        def in_pond(p: Pt) -> bool:
            return bool(pond) and in_ellipse(p[0], p[1], pond, 1.05)

        def at_moat(p: Pt) -> bool:
            return bool(moat_ring) and poly_dist(p[0], p[1], moat_ring) <= 32  # a city stream may feed the moat

        def at_drain(p: Pt) -> bool:
            return anchored(p, {"kind": "drain"})  # type: ignore[no-any-return]  # a brook may START at the field drain's outfall

        def in_field(p: Pt) -> bool:
            return any(point_in_poly(p[0], p[1], f["outline"]) for f in fields)  # a SOURCE brook may END at the field head

        def at_ditch(p: Pt) -> bool:
            return any(
                seg_dist(p[0], p[1], dp[i], dp[i + 1]) < 22  # a brook DIVERTED into an irrigation channel
                for d in (M.get("field_ditches", []) + M.get("channels", []))
                for dp in [d["poly"]]
                for i in range(len(dp) - 1)
            )

        def at_river(p: Pt) -> bool:
            # a sluiced moat FEEDER taps the trunk river (feature 020's capital: the ring stands
            # ~200px off the bank, so the connection Minami/Nagahara get from their moat feet is
            # drawn as a short leat instead). The river is itself edge-sourced, so a stream rooted
            # on it inherits a real source the way an edge end does.
            riv_ = M.get("river")
            rp_ = (riv_ or {}).get("pts") or (riv_ or {}).get("poly")
            if not rp_:
                return False
            return any(seg_dist(p[0], p[1], rp_[i], rp_[i + 1]) <= (riv_ or {}).get("w", 40) / 2 + 12 for i in range(len(rp_) - 1))

        ok = all(at_edge(e) or in_pond(e) or at_moat(e) or at_drain(e) or in_field(e) or at_ditch(e) or at_river(e) for e in (e0, e1)) and (at_edge(e0) or at_edge(e1) or at_river(e0) or at_river(e1))
        check(f"stream_runs_off_edge[{idx}]", ok, f"stream {idx} ends {e0},{e1} must run off the edge (one end may be a pond, the moat, the field drain, the field head, or a trunk-river tap)")
    return _kept(locals(), ('at_ditch', 'at_drain', 'at_moat', 'at_river', 'e', 'e0', 'e1', 'idx', 'in_field', 'in_pond', 'ok', 'st'))


# WATER SOURCES COME FROM THE MAP EDGE: a pond does not generate water, so any brook FEEDING it (a
# stream with one end in the pond) must ORIGINATE off-map - it flows in from the edge, not out of
# nowhere. (A sole-storage / rain-fed pond with no feeder stream is exempt - no inflow to check.)


def _seg_0512__pond_fed_from_edge(
    *,
    M: Any = _UNBOUND,
    at_edge: Any = _UNBOUND,
    check: Any = _UNBOUND,
    far: Any = _UNBOUND,
    near: Any = _UNBOUND,
    p: Any = _UNBOUND,
    pond: Any = _UNBOUND,
    st: Any = _UNBOUND,
    unsourced: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 512 (pond_fed_from_edge) - body verbatim from the legacy gate() (feature 022)."""
    if pond:
        unsourced = []
        for st in M.get("streams", []):
            p = st["poly"]
            for near, far in ((p[0], p[-1]), (p[-1], p[0])):
                if in_ellipse(near[0], near[1], pond, 1.05) and not at_edge(far):
                    unsourced.append([round(far[0]), round(far[1])])
        check(
            "pond_fed_from_edge",
            not unsourced,
            f"a stream feeds the pond but its far end {unsourced[:3]} is not at the map edge - a pond's feeder brook must flow IN from off-map (the water source comes from the edge, not nowhere)",
        )
    return _kept(locals(), ('far', 'near', 'p', 'st', 'unsourced'))


# A LANE MUST REACH SOMETHING. A lane exists to be fronted: it serves houses, meets another way, or
# leaves for the wider world. An internal arm that ends far from all three is a blunt tread stopping
# in bare grass - it reads as a drafting artifact, and where it runs alongside a way it has already
# met, the pair reads as one doubled track rather than a fork. Measured before the fix: five such
# ends across the four scripted hamlets, and more on the frozen pool (honda, ubame x4, kikuta x2,
# tanada, hoshizora). The engine's own note already had the principle - "shortening the arm is the
# honest fix: the lane simply ends where the crop starts" - but an arm meeting neither crop nor water
# had nothing to stop it, because lanes are laid BEFORE the houses they serve. `trim_lane_stubs`
# closes that after the flush; this holds it closed.
#
# THE CONNECTOR IS EXEMPT and must stay whole: it is the track OUT of the settlement, and
# `connector_lane_runs_off_edge` requires it to reach the frame. This is that rule's internal
# counterpart - both say a way must go somewhere, and they cover the two different somewheres.
#
# GATED ON `meta.generated_by`, the migration doctrine: the rule binds the scripted path, and each
# legacy map inherits it at the moment it is converted rather than being retrofitted.
_LANE_WAY_REACH = 40.0  # a lane end this close to another way has MET it
_LANE_HOUSE_REACH = 90.0  # ...or it stops at a homestead it fronts


# THE REACH A FARMHOUSE IS ENTITLED TO, in feet. This is `BUNDLE_PITCH` - the ground one homestead
# occupies - restated here rather than imported, because the gate does not import the generators it
# gates (a check that reads a generator's constant cannot catch that constant being wrong). The
# hamlet generator's `WEB_REACH_FT` is the same number and `tests/hamletgen/test_consts.py` asserts
# the two agree, which is where the coupling is allowed to live.
#
# WHY A HOUSE IS ENTITLED TO ONE AT ALL (research/homesteads.md, "Is every farmhouse reached by a
# lane, and in what FORM?"): the record is decisive that a house in a nucleated cluster is reached -
# "every house in the nucleated village is accessible via the interconnected system of narrow lanes
# and alleys". The earlier reading, that a back rank is walked to along unfigured footpaths, was
# defensible-sounding with nothing behind it, and it left 25 of the four pool hamlets' 66 farmhouses
# more than 120 ft from any way. WHY THIS DISTANCE: one bundle pitch is the distance at which a lane
# passes your own plot or your immediate neighbor's, which is what the sources describe when they
# say a lateral is "colonized as semi-private space by the adjoining house".
_WEB_REACH = 100.0

# How close two drawn treads must come to count as ONE network. Same figure `lanes_reach_something`
# uses for "this end has met another way", deliberately: the two rules are about the same fact from
# opposite ends, and letting them disagree would let a lane be connected for one and isolated for
# the other.
_LANE_JOIN = 40.0


# TWO LANE ENDS MAY NOT FRONT THE SAME FARMHOUSE FROM THE SAME SIDE.
#
# `_LANE_HOUSE_REACH` lets a lane end discharge its obligation by stopping at a farmhouse. Nothing
# said the farmhouse could only do that once - so three ends standing within 40 ft of each other, all
# claiming the same house at 66.9, 55.1 and 40.0 ft, all passed, and a settlement-review read the
# result at 3x zoom as a broom: not three ways, one way drawn three times with the ends fanned.
#
# TWO NUMBERS, and they are doing different jobs. `_FAN_SPREAD_FT` is how close two ends must be
# before they are the same arrival rather than two arrivals; `_FAN_BEARING_DEG` is how nearly they
# must point the same way. The bearing clause is what keeps a genuine CROSSROADS legal - two lanes
# reaching one house from opposite quarters is a house on a corner, which is a real thing and reads
# as one. It is only when they arrive alongside each other that the eye merges them.
# Below this divergence an end has not MET the way it is near, it is running alongside it - the
# engine's `_FRAY_DEG`, restated here because the gate does not import the generator it gates.
_FAN_FRAY_DEG = 20.0

# Treads this close have physically met, whatever angle they meet at.
_FAN_TOUCH_FT = 6.0

_FAN_SPREAD_FT = 60.0
_FAN_BEARING_DEG = 25.0


# ONE WAY DRAWN AS TWO. Two non-connector ends that point AT each other across a short gap are not
# two arms - they are one street with a hole in the middle of the built-up frontage, and both read as
# rounded caps dying in bare grass. `lanes_reach_something` passes them because it tests each end
# independently and an end 83 ft from a house CENTRE counts as fronting it, even when that is 55 ft
# from the wall, i.e. out past the dooryard.
#
# THE GAP HAS TO BE EMPTY for this to be a defect, and that is the whole distinction: two ends with a
# wellhead or a garden bed between them are honestly interrupted - the way stops because something is
# there. The check cannot see the generator's obstacle sets, so it approximates "empty" with the
# manifest's own solid features; anything it can see in the gap earns the break.
_BREAK_GAP_FT = 150.0
_BREAK_ANGLE_DEG = 15.0


def _seg_0612__lanes_do_not_break_mid_run(*, M: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0612 (lanes_do_not_break_mid_run) - added 2026-08-18, feature 125."""
    _br_ways = [[(float(x), float(y)) for x, y in (_br_l.get("pts") or [])] for _br_l in (M.get("lanes") or [])]
    _br_solid = []
    _br_small = []
    for _br_key in ("houses", "farm_sheds", "byres"):
        for _br_r in M.get(_br_key) or []:
            _br_small.append(rect_corners(_br_r))
    _br_solid.extend(_br_small)
    for _br_key in ("threshing_yards", "gardens"):
        for _br_r in M.get(_br_key) or []:
            if _br_r.get("poly"):
                _br_bed = [(float(_a), float(_b)) for _a, _b in _br_r["poly"]]
                _br_solid.append(_br_bed)
                _br_small.append(_br_bed)
    # TREE COVER AND OPEN COMMONS DO NOT BLOCK A LANE, and listing them here is what made this
    # check silent on the break it was written for: the motivating gap lies inside a homestead
    # grove, so all three corridors read as blocked and the hole was excused. A cart track runs
    # through a copse perfectly well, and a yashikirin grove is PLANTED AROUND the way rather than
    # across it - the trees arrive after the lane, not before. Marsh stays: wet ground genuinely
    # stops a lane, which is why it is the one member of that group kept.
    for _br_key in ("marshes",):
        _br_solid.extend([(float(_a), float(_b)) for _a, _b in _br_r["poly"]] for _br_r in (M.get(_br_key) or []) if _br_r.get("poly"))
    # ...and the GROUND, not only the built things. A break with the paddy, a ditch or a stream in it
    # is honest - a lane cannot be drawn there, so the way stops and resumes on the far side, and the
    # generator is right to leave it. Leaving crop and water out of this list made the check fire on
    # exactly the gaps its own fix is forbidden to close, which is a check demanding the impossible.
    for _br_p in M.get("dry_plots") or []:
        if _br_p.get("poly"):
            _br_solid.append([(float(_a), float(_b)) for _a, _b in _br_p["poly"]])
    for _br_f in M.get("fields") or []:
        if _br_f.get("outline"):
            _br_solid.append([(float(_a), float(_b)) for _a, _b in _br_f["outline"]])
    for _br_key in ("field_ditches", "channels", "streams"):
        for _br_c in M.get(_br_key) or []:
            if _br_c.get("poly"):
                _br_solid.append([(float(_a), float(_b)) for _a, _b in _br_c["poly"]])
    for _br_w in M.get("wells") or []:
        _br_rad = max(float(_br_w.get("r", 8.0)), float(_br_w.get("vr", 0.0)))
        _br_ring = [(float(_br_w["x"]) + _br_rad * math.cos(math.pi * _k / 4), float(_br_w["y"]) + _br_rad * math.sin(math.pi * _k / 4)) for _k in range(8)]
        _br_solid.append(_br_ring)
        _br_small.append(_br_ring)
    _br_bad = []
    for _br_i, _br_li in enumerate(M.get("lanes") or []):
        if _br_li.get("connector") or len(_br_ways[_br_i]) < 2:
            continue
        for _br_j, _br_lj in enumerate(M.get("lanes") or []):
            if _br_j <= _br_i or _br_lj.get("connector") or len(_br_ways[_br_j]) < 2:
                continue
            for _br_ta, _br_pa in ((_br_ways[_br_i][0], _br_ways[_br_i][1]), (_br_ways[_br_i][-1], _br_ways[_br_i][-2])):
                for _br_tb, _br_pb in ((_br_ways[_br_j][0], _br_ways[_br_j][1]), (_br_ways[_br_j][-1], _br_ways[_br_j][-2])):
                    _br_gap = math.dist(_br_ta, _br_tb)
                    if not (_LANE_JOIN < _br_gap <= _BREAK_GAP_FT):
                        continue

                    # EACH END MUST AIM AT THE OTHER. Comparing the two outward headings for
                    # SIMILARITY tests the wrong thing - two ends facing across a gap have opposite
                    # outward headings - so it selected parallel arms and missed the collinear break
                    # this rule is named for.
                    def _aim(_p: Any, _tip: Any, _to: Any) -> float:
                        _o = math.degrees(math.atan2(_tip[1] - _p[1], _tip[0] - _p[0]))
                        _m = math.degrees(math.atan2(_to[1] - _tip[1], _to[0] - _tip[0]))
                        return abs((_o - _m + 180.0) % 360.0 - 180.0)

                    if _aim(_br_pa, _br_ta, _br_tb) > _BREAK_ANGLE_DEG or _aim(_br_pb, _br_tb, _br_ta) > _BREAK_ANGLE_DEG:
                        continue  # two arms, not one way
                    # SOMETHING IN THE GAP, NOT MERELY NEAR IT. Testing "is any vertex of any solid
                    # within 14 ft of the gap line" is far too loose once the FIELD is in the list:
                    # these lanes run along the field margin, so almost every gap has the paddy's
                    # outline nearby and every break was excused as honest - the motivating fixture
                    # stopped firing, which is how this was caught. The gap is honest only if
                    # something actually occupies it, so the line is SAMPLED and each sample tested
                    # for being inside an area or up against a small solid.
                    # HONEST MEANS NO LANE COULD PASS, not that something is standing in the way.
                    # A wellhead in the middle of a 110 ft hole does not justify the hole - a lane
                    # goes ROUND a wellhead. So three parallel corridors are tested, the straight
                    # line and one either side of it, and the break is excused only if ALL of them
                    # are blocked. With only the straight line tested, the motivating fixture stopped
                    # firing because a single wellhead sat on it, and the check lost its teeth on the
                    # very defect it was written for.
                    _br_ux, _br_uy = (_br_tb[0] - _br_ta[0]) / max(_br_gap, 1e-6), (_br_tb[1] - _br_ta[1]) / max(_br_gap, 1e-6)
                    _br_open = False
                    for _br_off in (0.0, 22.0, -22.0):
                        _br_pts = [
                            (
                                _br_ta[0] + (_br_tb[0] - _br_ta[0]) * _k / 12.0 - _br_uy * _br_off,
                                _br_ta[1] + (_br_tb[1] - _br_ta[1]) * _k / 12.0 + _br_ux * _br_off,
                            )
                            for _k in range(1, 12)
                        ]
                        if any(point_in_poly(_br_s[0], _br_s[1], list(_br_o)) for _br_s in _br_pts for _br_o in _br_solid):
                            continue
                        if any(min(seg_dist(_br_s[0], _br_s[1], _br_o[_br_m], _br_o[(_br_m + 1) % len(_br_o)]) for _br_m in range(len(_br_o))) <= 10.0 for _br_s in _br_pts for _br_o in _br_small):
                            continue
                        _br_open = True
                        break
                    if not _br_open:
                        continue  # every corridor is blocked; the interruption is honest
                    # ...AND THE GAP MUST NOT ALREADY BE SPANNED. A third way running from one end to
                    # the other has closed the break, and the two ends are joined THROUGH it - which
                    # is exactly what the generator draws when it heals one. Without this clause the
                    # check fires on the very repair that fixes it.
                    if any(
                        _br_k not in (_br_i, _br_j)
                        and len(_br_o2) >= 2
                        and min(seg_dist(_br_ta[0], _br_ta[1], _a2, _b2) for _a2, _b2 in zip(_br_o2, _br_o2[1:], strict=False)) <= _LANE_JOIN
                        and min(seg_dist(_br_tb[0], _br_tb[1], _a2, _b2) for _a2, _b2 in zip(_br_o2, _br_o2[1:], strict=False)) <= _LANE_JOIN
                        for _br_k, _br_o2 in enumerate(_br_ways)
                    ):
                        continue
                    _br_bad.append((round(_br_ta[0]), round(_br_ta[1]), round(_br_gap)))
    check(
        "lanes_do_not_break_mid_run",
        not _br_bad,
        f"{len(_br_bad)} lane(s) stop and resume across empty ground, at {_br_bad[:4]} (x, y, gap ft) - "
        f"two ends pointing at each other across nothing are ONE way drawn as two, and both of them read as a rounded cap dying in bare grass. "
        f"An interruption with a wellhead or a garden bed in it is honest and is not flagged; an interruption with nothing in it is a hole",
    )
    return _kept(locals(), ())


def _seg_0611__lane_ends_front_different_houses(*, M: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0611 (lane_ends_front_different_houses) - added 2026-08-18, feature 124."""
    # ONLY BLUNT ENDS CAN FAN. An end that MEETS another way is a junction, and a junction beside a
    # junction is a crossroads however tightly they sit - the defect is specifically an end with no
    # reason to exist except a house that another end is already fronting. Leaving this clause out
    # made the rule flag every close pair of real junctions, which is most of a nucleated cluster's
    # middle.
    _fd_ways = [[(float(x), float(y)) for x, y in (_fd_l.get("pts") or [])] for _fd_l in (M.get("lanes") or [])]
    _fd_ends = []
    for _fd_i, _fd_ln in enumerate(M.get("lanes") or []):
        if _fd_ln.get("connector"):
            continue
        _fd_p = _fd_ways[_fd_i]
        if len(_fd_p) < 2:
            continue
        for _fd_tip, _fd_prev in ((_fd_p[0], _fd_p[1]), (_fd_p[-1], _fd_p[-2])):
            _fd_met = False
            for _fd_k, _fd_o in enumerate(_fd_ways):
                if _fd_k == _fd_i or len(_fd_o) < 2:
                    continue
                _fd_seg = min(zip(_fd_o, _fd_o[1:], strict=False), key=lambda _ab: seg_dist(_fd_tip[0], _fd_tip[1], _ab[0], _ab[1]))
                if seg_dist(_fd_tip[0], _fd_tip[1], _fd_seg[0], _fd_seg[1]) > _LANE_WAY_REACH:
                    continue
                # PROXIMITY IS NOT ARRIVAL - the engine's own rule, and it is the whole reason this
                # check exists. The ends a review read as a broom stood 21.6 and 24.3 ft from another
                # way, i.e. INSIDE the 40 ft reach, and were near-parallel to it: they had not met
                # that way, they were running alongside it. Counting them as junctions is exactly the
                # mistake `lanes_reach_something` made before `_FRAY_DEG` was added to it.
                _fd_ang = abs(
                    (math.degrees(math.atan2(_fd_tip[1] - _fd_prev[1], _fd_tip[0] - _fd_prev[0])) - math.degrees(math.atan2(_fd_seg[1][1] - _fd_seg[0][1], _fd_seg[1][0] - _fd_seg[0][0])) + 90.0)
                    % 180.0
                    - 90.0
                )
                # A TOUCH IS A JUNCTION AT ANY ANGLE. The fray rule is about a way running ALONGSIDE
                # another at a distance; where the two treads actually MEET, they are joined however
                # shallow the angle - which is what a bridged break looks like, and what a street
                # continuing into the next street looks like. Without this the bridge drawn to close
                # a hole in a spine reads as two fresh tines, and closing a gap makes the map fail.
                if _fd_ang >= _FAN_FRAY_DEG or seg_dist(_fd_tip[0], _fd_tip[1], _fd_seg[0], _fd_seg[1]) <= _FAN_TOUCH_FT:
                    _fd_met = True
                    break
            if _fd_met:
                continue  # it crossed a way at a real angle; that is a junction, not a tine
            _fd_h = min(((math.hypot(_fd_tip[0] - _fd_q["x"], _fd_tip[1] - _fd_q["y"]), (round(float(_fd_q["x"]), 1), round(float(_fd_q["y"]), 1))) for _fd_q in M.get("houses") or []), default=None)
            if _fd_h is not None and _fd_h[0] <= _LANE_HOUSE_REACH:
                _fd_ends.append((_fd_tip, math.degrees(math.atan2(_fd_tip[1] - _fd_prev[1], _fd_tip[0] - _fd_prev[0])), _fd_h[1]))
    _fd_fans = []
    for _fd_i in range(len(_fd_ends)):
        for _fd_j in range(_fd_i + 1, len(_fd_ends)):
            _fd_a, _fd_b = _fd_ends[_fd_i], _fd_ends[_fd_j]
            if _fd_a[2] != _fd_b[2] or math.dist(_fd_a[0], _fd_b[0]) > _FAN_SPREAD_FT:
                continue
            _fd_turn = abs((_fd_a[1] - _fd_b[1] + 180.0) % 360.0 - 180.0)
            if _fd_turn <= _FAN_BEARING_DEG:
                _fd_fans.append((round(_fd_a[0][0]), round(_fd_a[0][1]), round(_fd_turn)))
    check(
        "lane_ends_front_different_houses",
        not _fd_fans,
        f"{len(_fd_fans)} pair(s) of lane ends front the SAME farmhouse from the same side, at {_fd_fans[:4]} (x, y, degrees apart) - "
        f"a farmhouse discharges one lane end's obligation, not three. Ends standing within {_FAN_SPREAD_FT:.0f} ft of each other and pointing "
        f"within {_FAN_BEARING_DEG:.0f} degrees the same way read as one way drawn twice with its tip frayed, not as two ways; a house reached "
        f"from OPPOSITE quarters is a corner and is fine",
    )
    return _kept(locals(), ())


def _seg_0610__farmhouses_reach_a_way(*, M: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0610 (farmhouses_reach_a_way) - added 2026-08-18, feature 123.

    Numbered 0610, and it moved twice: a peer landed `paddy_basins_are_worth_their_bund` on 0608 in
    `segments_08d` while this was unpushed, and then took 0609 for the byre-form checks - on my own
    advice, since I had told them 0608 was mine and then quietly moved onto 0609 myself. A duplicate
    numeric key is at least a loud derivation error rather than a silent reorder. It still runs directly after 0607 `lanes_reach_something`, which is
    what matters - the two are converses and belong together.

    The CONVERSE of `lanes_reach_something`, and the half that was missing: that check asks whether
    each lane serves something, this one asks whether each house is served. A map can pass the first
    with every lane busy and still strand a third of its houses, which is exactly what the four pool
    hamlets did."""
    if M["meta"].get("generated_by"):
        _fw_ways = [[(float(x), float(y)) for x, y in (_fw_ln.get("pts") or [])] for _fw_ln in (M.get("lanes") or [])]
        # THE NETWORK, NOT ANY LINE ON THE GROUND. "Every house in the nucleated village is
        # accessible via the INTERCONNECTED system of narrow lanes and alleys" - so a house served
        # only by an isolated stub is not served, and the first version of this check could not tell
        # the difference, because it measured distance to any drawn polyline. Two settlement-reviews
        # found the same thing independently: 4 of Sawada's 6 web lanes touched nothing, and 7 of its
        # 19 houses were "reached" only by an island whose nearest real lane was 136-296 ft away -
        # exactly where they had been before the feature. A check satisfiable by an island rewards
        # drawing an island.
        #
        # The component is grown from the ways that are the settlement's connection to the world:
        # the connector if one is drawn, else the longest lane. Two lanes are in the same component
        # when their drawn treads come within _LANE_JOIN, which is the same distance
        # `lanes_reach_something` treats as one way having met another.
        _fw_lanes = M.get("lanes") or []
        _fw_seed = next((_fw_i for _fw_i, _fw_l in enumerate(_fw_lanes) if _fw_l.get("connector")), None)
        if _fw_seed is None and _fw_ways:
            _fw_seed = max(range(len(_fw_ways)), key=lambda _fw_i: sum(math.dist(_fw_a, _fw_b) for _fw_a, _fw_b in zip(_fw_ways[_fw_i], _fw_ways[_fw_i][1:], strict=False)))

        def _fw_touch(_fw_p: Any, _fw_q: Any) -> bool:
            return any(seg_dist(_fw_v[0], _fw_v[1], _fw_a, _fw_b) <= _LANE_JOIN for _fw_v in _fw_p for _fw_a, _fw_b in zip(_fw_q, _fw_q[1:], strict=False)) or any(
                seg_dist(_fw_v[0], _fw_v[1], _fw_a, _fw_b) <= _LANE_JOIN for _fw_v in _fw_q for _fw_a, _fw_b in zip(_fw_p, _fw_p[1:], strict=False)
            )

        _fw_main = set() if _fw_seed is None else {_fw_seed}
        _fw_grew = True
        while _fw_grew:
            _fw_grew = False
            for _fw_i, _fw_p in enumerate(_fw_ways):
                if _fw_i in _fw_main or len(_fw_p) < 2:
                    continue
                if any(_fw_touch(_fw_p, _fw_ways[_fw_j]) for _fw_j in _fw_main if len(_fw_ways[_fw_j]) >= 2):
                    _fw_main.add(_fw_i)
                    _fw_grew = True
        _fw_segs = [(_fw_a, _fw_b) for _fw_i in sorted(_fw_main) for _fw_a, _fw_b in zip(_fw_ways[_fw_i], _fw_ways[_fw_i][1:], strict=False)]
        _fw_far = []
        if _fw_segs:
            for _fw_h in M.get("houses") or []:
                _fw_c = (float(_fw_h["x"]), float(_fw_h["y"]))  # x, y ARE the center here - same convention as rect_corners
                _fw_d = min(seg_dist(_fw_c[0], _fw_c[1], _fw_a, _fw_b) for _fw_a, _fw_b in _fw_segs)
                if _fw_d > _WEB_REACH:
                    _fw_far.append((round(_fw_c[0]), round(_fw_c[1]), round(_fw_d)))
        check(
            "farmhouses_reach_a_way",
            not _fw_far,
            f"{len(_fw_far)} farmhouse(s) stand more than {_WEB_REACH:.0f} ft from any drawn way, worst {max((_f[2] for _f in _fw_far), default=0)} ft, at {_fw_far[:4]} - "
            f"every house in a nucleated cluster is reached by the lane network; that is what compactness is for, and a house the web does not touch is not a back rank, it is an omission",
        )
    return _kept(locals(), ())


def _seg_0607__lanes_reach_something(*, M: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0607 (lanes_reach_something) - added 2026-08-17, see the note above."""
    if M["meta"].get("generated_by"):
        _lr_lanes = M.get("lanes") or []
        _lr_houses = M.get("houses") or []
        _lr_dangling = []
        for _lr_i, _lr_ln in enumerate(_lr_lanes):
            if _lr_ln.get("connector"):
                continue
            _lr_pts = [(float(x), float(y)) for x, y in _lr_ln.get("pts") or []]
            if len(_lr_pts) < 2:
                continue
            for _lr_end in (_lr_pts[0], _lr_pts[-1]):
                _lr_way = 1e9
                for _lr_k, _lr_o in enumerate(_lr_lanes):
                    _lr_op = [(float(x), float(y)) for x, y in _lr_o.get("pts") or []]
                    if _lr_k == _lr_i or len(_lr_op) < 2:
                        continue
                    _lr_way = min(_lr_way, min(seg_dist(_lr_end[0], _lr_end[1], _lr_a, _lr_b) for _lr_a, _lr_b in zip(_lr_op, _lr_op[1:], strict=False)))
                _lr_house = min((math.hypot(_lr_end[0] - _lr_h["x"], _lr_end[1] - _lr_h["y"]) for _lr_h in _lr_houses), default=1e9)
                if _lr_way > _LANE_WAY_REACH and _lr_house > _LANE_HOUSE_REACH:
                    _lr_dangling.append((round(_lr_end[0]), round(_lr_end[1])))
        check(
            "lanes_reach_something",
            not _lr_dangling,
            f"{len(_lr_dangling)} internal lane end(s) reach neither another way ({_LANE_WAY_REACH:.0f} ft) nor a farmhouse ({_LANE_HOUSE_REACH:.0f} ft), at {_lr_dangling[:4]} - "
            f"a lane exists to be fronted; a tread that stops in bare grass serves no house, reaches no field and connects to nothing (the connector is exempt - it leaves the map)",
        )
    return _kept(locals(), ())
