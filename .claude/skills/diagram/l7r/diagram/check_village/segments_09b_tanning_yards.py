"""Gate segments (tanning yards; keys 0562_000-0562_042) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from .common_01_geometry import edge_gap, point_in_poly, pt_to_rect, rect_corners, seg_dist, seg_to_rect_dist, segments_cross
from .common_03_capacity import _UNBOUND, DWELLING_KINDS, _kept

# TANNING YARDS (GM 2026-07-24; the "why" lives in settlements.md "TANNING YARDS"). Unlike the
# other trade works these are NOT a city-only feature: a county town's burakumin hold the whole
# county's carcass rights (danna-ba), so the town tans too - just at ~4 pits rather than ~12.
# WATER, not settlement size, is the gate: tanning is a water process (shironameshi stakes hides
# in the river for 1-2 weeks before de-hairing) and every attested tannery sits on a watercourse
# at the settlement's edge - the caste's own name for itself was kawaramono, "riverbed people".


def _seg_0562_000___ty_ftpx(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.000 (_ty_ftpx) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        _ty_ftpx = float(meta.get("ftpx") or 1.0)
    return _kept(locals(), ('_ty_ftpx',))


def _seg_0562_001___ty_px(*, _ty_ftpx: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.001 (_ty_px) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):

        def _ty_px(ft: float) -> float:
            return ft / _ty_ftpx  # type: ignore[no-any-return]

    return _kept(locals(), ('_ty_px',))


def _seg_0562_002___ty_water(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.002 (_ty_water) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        _ty_water: list[tuple[list[Any], float]] = []  # type: ignore[no-redef,unused-ignore]
    return _kept(locals(), ('_ty_water',))


def _seg_0562_003___ty_poly(*, M: Any = _UNBOUND, _ty_poly: Any = _UNBOUND, _ty_water: Any = _UNBOUND, _ty_wc: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.003 (_ty_poly, _ty_water, _ty_wc) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        for _ty_wc in (M.get("streams") or []) + (M.get("channels") or []) + (M.get("canals") or []):
            _ty_poly = _ty_wc.get("poly") or _ty_wc.get("pts")
            if _ty_poly:
                _ty_water.append((_ty_poly, _ty_wc.get("w", 6) / 2))
    return _kept(locals(), ('_ty_poly', '_ty_water', '_ty_wc'))


def _seg_0562_004___ty_water_1(*, M: Any = _UNBOUND, _ty_water: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.004 (_ty_water) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and M.get("moat"):
        _ty_water.append((M["moat"], M.get("moat_width", 22) / 2))
    return _kept(locals(), ('_ty_water',))


def _seg_0562_005___ty_yards(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.005 (_ty_yards) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        _ty_yards = M.get("tanning_yards") or []
    return _kept(locals(), ('_ty_yards',))


def _seg_0562_006___ty_bur(*, M: Any = _UNBOUND, b: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.006 (_ty_bur, b) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        _ty_bur = [b for b in (M.get("buildings") or []) if b.get("kind") == "burakumin"]
    return _kept(locals(), ('_ty_bur', 'b'))


def _seg_0562_007___ty_on_water(
    *, _hw: Any = _UNBOUND, _pl: Any = _UNBOUND, _ty_px: Any = _UNBOUND, _ty_water: Any = _UNBOUND, i: Any = _UNBOUND, o_: Any = _UNBOUND, r_: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0562.007 (_ty_on_water) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):

        def _ty_on_water(o_: dict[str, Any], reach_ft: float) -> bool:
            # Family: ASSOCIATION/REACH - "does this yard stand on the water", not "how many feet of
            # daylight are between them". The reach tolerance is tens of feet against a yard's own
            # extent, so the radius is a fair stand-in and the question is neighborhood membership
            # rather than a gap. Deliberately left on centers (GM audit, 2026-07-27).
            r_ = max(o_["w"], o_["h"]) / 2
            return any(seg_dist(o_["x"], o_["y"], _pl[i], _pl[i + 1]) < _hw + r_ + _ty_px(reach_ft) for _pl, _hw in _ty_water for i in range(len(_pl) - 1))

    return _kept(locals(), ('_ty_on_water',))


# A settlement with BOTH a burakumin quarter and running water tans its own hides; one with
# no watercourse at all keeps no tannery, whatever its size, and is exempt.
# meta(tannery=False) is the documented opt-out for a settlement that HAS water but no
# legitimate site on it - the same "declare the deliberate exception" pattern as
# monastery_fortunes. Tango is the case: its only downstream watercourse is tapped for
# irrigation ~100 px below the moat, and the sole ground below that tap drags the frame
# far enough south to strand other off-map features. A dry inland seat sends its hides
# away, exactly as it buys its timber elsewhere for want of navigable water.


def _seg_0562_008__settlement_has_tanning_yard(
    *, _ty_bur: Any = _UNBOUND, _ty_water: Any = _UNBOUND, _ty_yards: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0562.008 (settlement_has_tanning_yard) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_bur and _ty_water and meta.get("tannery") is not False:
        check(
            "settlement_has_tanning_yard",
            bool(_ty_yards),
            "no tanning yard - a town or city with a burakumin quarter AND a watercourse works its territory's fallen "
            "draft stock into leather (s.tanning_yard: soaking pits + drying racks + work shed on the bank). Water is "
            "the gate, not size: a settlement with no running water keeps none and is exempt from this check",
        )
    return _kept(locals(), ())


def _seg_0562_009__tanning_yard_on_water(*, _ty_on_water: Any = _UNBOUND, _ty_yards: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND, t_: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.009 (tanning_yard_on_water) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        check(
            "tanning_yard_on_water",
            all(_ty_on_water(t_, 20.0) for t_ in _ty_yards),
            f"tanning yard(s) on water: {[_ty_on_water(t_, 20.0) for t_ in _ty_yards]} - tanning is a WATER process (hides soak "
            f"1-2 weeks before de-hairing), so the yard must ABUT a stream/channel/canal/moat (within ~20 ft of the bank); "
            f"a yard set back on dry ground could not work",
        )
    return _kept(locals(), ('t_',))


# DOWNSTREAM OF EVERY DRAW (GM 2026-07-25). The rule tanneries actually turn on: the
# foul water must not reach anything anyone draws from. This is NOT testable by
# projecting onto the map's drainage bearing - Hoshizora's yard sits on a watercourse
# hydrologically separate from the town's, so a single-bearing projection calls it
# "upstream" of a town it cannot reach. It IS testable now that flow direction is
# recorded, in two clauses against the yard's OWN course:
#   (a) that course must not DISCHARGE into anything drawn from - a pond, a field, the
#       moat, an irrigation ditch. Emptying to off-map (or into a field drain that
#       does) is the only honest ending for a tannery's water.
#   (b) no intake may sit DOWNSTREAM of the yard along that same course. Graph
#       topology alone cannot see this - a channel tapping the river 200 ft below the
#       yard and one tapping it 200 ft above are the same edge - so this clause
#       compares ARC POSITION along the course, oriented by the recorded flow.


def _seg_0562_010___ty_arc(
    *,
    _ty_yards: Any = _UNBOUND,
    at: Any = _UNBOUND,
    ax: Any = _UNBOUND,
    ay: Any = _UNBOUND,
    best: Any = _UNBOUND,
    bx: Any = _UNBOUND,
    by: Any = _UNBOUND,
    d: Any = _UNBOUND,
    i: Any = _UNBOUND,
    poly: Any = _UNBOUND,
    run: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    x: Any = _UNBOUND,
    y: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0562.010 (_ty_arc, run) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:

        def _ty_arc(poly: Any, x: float, y: float) -> tuple[float, float]:
            """(arc length to the closest point on `poly`, total length)."""
            best, run, at = None, 0.0, 0.0
            for i in range(len(poly) - 1):
                ax, ay, bx, by = poly[i][0], poly[i][1], poly[i + 1][0], poly[i + 1][1]
                seg = math.hypot(bx - ax, by - ay)
                d = seg_dist(x, y, poly[i], poly[i + 1])
                if best is None or d < best:
                    t_par = 0.0 if seg == 0 else max(0.0, min(1.0, ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / (seg * seg)))
                    best, at = d, run + t_par * seg
                run += seg
            return at, run

    return _kept(locals(), ('_ty_arc', 'run'))


def _seg_0562_011___ty_bad_sink(*, _ty_yards: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.011 (_ty_bad_sink, _ty_below) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        _ty_bad_sink, _ty_below = [], []  # type: ignore[var-annotated]
    return _kept(locals(), ('_ty_bad_sink', '_ty_below'))


def _seg_0562_012___(
    *,
    M: Any = _UNBOUND,
    _at: Any = _UNBOUND,
    _cands: Any = _UNBOUND,
    _co: Any = _UNBOUND,
    _da: Any = _UNBOUND,
    _dr: Any = _UNBOUND,
    _draw_at: Any = _UNBOUND,
    _is_stream: Any = _UNBOUND,
    _rev: Any = _UNBOUND,
    _sink: Any = _UNBOUND,
    _tot: Any = _UNBOUND,
    _ty_arc: Any = _UNBOUND,
    _ty_bad_sink: Any = _UNBOUND,
    _ty_below: Any = _UNBOUND,
    _ty_yards: Any = _UNBOUND,
    _yard_at: Any = _UNBOUND,
    c: Any = _UNBOUND,
    g: Any = _UNBOUND,
    i: Any = _UNBOUND,
    o: Any = _UNBOUND,
    oc: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    t_: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0562.012 (_, _at, _cands, _co) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        for t_ in _ty_yards:
            # a yard's course may be a natural stream OR a dug channel (Hoshizora's sits on an
            # irrigation drain), so both are candidates. A channel is directional by its own
            # frm->to; only a stream carries a flow tag that can reverse the polyline's sense.
            _cands = [(o, False) for o in (M.get("channels") or []) if o.get("poly")] + [(o, True) for o in (M.get("streams") or []) if o.get("poly")]
            if not _cands:
                continue
            _co, _is_stream = min(_cands, key=lambda oc: min(seg_dist(t_["x"], t_["y"], oc[0]["poly"][i], oc[0]["poly"][i + 1]) for i in range(len(oc[0]["poly"]) - 1)))
            _rev = _is_stream and _co.get("flow") == "reverse"
            # frm/to are anchored by POLYLINE ORDER, so flow decides which is downstream
            _sink = (_co.get("to") if not _rev else _co.get("frm")) or {}
            if _sink.get("kind") not in ("offmap", "drain"):
                _ty_bad_sink.append((round(t_["x"]), round(t_["y"]), _sink.get("kind")))
            _at, _tot = _ty_arc(_co["poly"], t_["x"], t_["y"])
            _yard_at = (_tot - _at) if _rev else _at
            for _dr in [c["poly"][0] for c in (M.get("channels") or []) if (c.get("frm") or {}).get("kind") in ("stream", "river")] + [[g["x"], g["y"]] for g in (M.get("sluice_gates") or [])]:
                if min(seg_dist(_dr[0], _dr[1], _co["poly"][i], _co["poly"][i + 1]) for i in range(len(_co["poly"]) - 1)) > 34:
                    continue  # not on THIS course
                _da, _ = _ty_arc(_co["poly"], _dr[0], _dr[1])
                _draw_at = (_tot - _da) if _rev else _da
                if _draw_at > _yard_at + 8:
                    _ty_below.append((round(t_["x"]), round(t_["y"]), round(_dr[0]), round(_dr[1])))
    return _kept(locals(), ('_', '_at', '_cands', '_co', '_da', '_dr', '_draw_at', '_is_stream', '_rev', '_sink', '_tot', '_ty_bad_sink', '_ty_below', '_yard_at', 'c', 'g', 'i', 'o', 't_'))


def _seg_0562_013__tanning_yard_discharges_to_nothing_drawn_from(*, _ty_bad_sink: Any = _UNBOUND, _ty_yards: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.013 (tanning_yard_discharges_to_nothing_drawn_from) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        check(
            "tanning_yard_discharges_to_nothing_drawn_from",
            not _ty_bad_sink,
            f"tanning yard(s) on a watercourse that empties into something people draw from (x, y, sink): {_ty_bad_sink} - "
            f"a tannery's water may end off-map or in a field drain that does, never in a supply pond, an irrigation "
            f"ditch, a field or the moat",
        )
    return _kept(locals(), ())


def _seg_0562_014__tanning_yard_below_every_intake(*, _ty_below: Any = _UNBOUND, _ty_yards: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.014 (tanning_yard_below_every_intake) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        check(
            "tanning_yard_below_every_intake",
            not _ty_below,
            f"tanning yard(s) with a water intake DOWNSTREAM of them on the same course (yard x, y, intake x, y): {_ty_below} - "
            f"every sluice, weir and channel head on the yard's own watercourse must lie UPSTREAM of it, or it is fouling "
            f"water that is drawn below",
        )
    return _kept(locals(), ())


def _seg_0562_015__tanning_yard_outside_walls(
    *, M: Any = _UNBOUND, _ty_in: Any = _UNBOUND, _ty_yards: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, t_: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0562.015 (tanning_yard_outside_walls) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards and meta.get("walled") and M.get("wall"):
        _ty_in = [(round(t_["x"]), round(t_["y"])) for t_ in _ty_yards if point_in_poly(t_["x"], t_["y"], M["wall"])]
        check(
            "tanning_yard_outside_walls",
            not _ty_in,
            f"tanning yard(s) INSIDE the walls: {_ty_in} - the stench and the death-pollution put the tanning ground strictly outside, with the kiln (the workers may live in-wall; the WORK may not)",
        )
    return _kept(locals(), ('_ty_in', 't_'))


# Stench separation from ordinary dwellings. The burakumin's OWN houses are exempt by
# design, not by oversight: kawaramono lived on the ground they worked, and that
# adjacency is what the segregated quarter IS. The floor is the crematory's existing
# 120 ft (town_has_cremation_ground) - the established project figure for "a nuisance
# kept off the houses" - rather than a fresh invented number.


def _seg_0562_016___ty_burxy(*, _ty_bur: Any = _UNBOUND, _ty_yards: Any = _UNBOUND, b: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.016 (_ty_burxy, b) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        _ty_burxy = {(round(b["x"], 2), round(b["y"], 2)) for b in _ty_bur}
    return _kept(locals(), ('_ty_burxy', 'b'))


def _seg_0562_017___ty_dwell(*, M: Any = _UNBOUND, _ty_yards: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.017 (_ty_dwell) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        _ty_dwell = list(M.get("houses") or [])
    return _kept(locals(), ('_ty_dwell',))


def _seg_0562_018___ty_dwell_1(*, M: Any = _UNBOUND, _ty_burxy: Any = _UNBOUND, _ty_dwell: Any = _UNBOUND, _ty_yards: Any = _UNBOUND, b: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.018 (_ty_dwell, b) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        _ty_dwell += [b for b in (M.get("buildings") or []) if b.get("kind") not in ("shop", "stables", "barn") and (round(b["x"], 2), round(b["y"], 2)) not in _ty_burxy]
    return _kept(locals(), ('_ty_dwell', 'b'))


def _seg_0562_019___ty_close(*, _ty_yards: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.019 (_ty_close) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        _ty_close = []  # type: ignore[var-annotated]
    return _kept(locals(), ('_ty_close',))


def _seg_0562_020___ty_close_1(
    *,
    _ty_close: Any = _UNBOUND,
    _ty_dwell: Any = _UNBOUND,
    _ty_ftpx: Any = _UNBOUND,
    _ty_near: Any = _UNBOUND,
    _ty_px: Any = _UNBOUND,
    _ty_yards: Any = _UNBOUND,
    h_: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    t_: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0562.020 (_ty_close, _ty_near, h_, t_) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        for t_ in _ty_yards:
            # WALL TO WALL. This kept its center-to-center form through the 2026-07-27 sweep
            # because that sweep grepped for two `["x"]` in one call and this compared a record
            # against an unpacked (x, y) tuple - so the audit's own method had the same shape of
            # blind spot as the bug it was hunting. Tango's yard read 150 ft and stood 76.
            _ty_near = min((edge_gap(t_, h_) for h_ in _ty_dwell), default=1e9)
            if _ty_near < _ty_px(120.0):
                _ty_close.append((round(t_["x"]), round(t_["y"]), round(_ty_near * _ty_ftpx)))
    return _kept(locals(), ('_ty_close', '_ty_near', 'h_', 't_'))


def _seg_0562_021__tanning_yard_clear_of_dwellings(*, _ty_close: Any = _UNBOUND, _ty_yards: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.021 (tanning_yard_clear_of_dwellings) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        check(
            "tanning_yard_clear_of_dwellings",
            not _ty_close,
            f"tanning yard(s) too close to ordinary dwellings (x, y, ft): {_ty_close} - a continuously-stinking works "
            f"stands off the houses by at least the crematory's 120 ft. Burakumin dwellings are deliberately EXEMPT: "
            f"they live on the ground they work, which is what the segregated quarter is",
        )
    return _kept(locals(), ())


# ---- THE YARD SHARES THE QUARTER'S SIDE OF THE SETTLEMENT (GM 2026-07-27) --------------
# The rule kegare actually follows is DIRECTIONAL, not metric: pollution leaves a
# settlement ONE way, and the outcast quarter is the marker of which way that is. Edo
# stacked the Asakusa outcast community, the Kozukappara execution ground and the
# Yoshiwara at the northeast kimon; Kyoto put its communities on the riverbeds and the
# southern roads out. So this is deliberately NOT a distance rule, and an earlier draft
# that measured feet was WRONG: a walled city legitimately keeps its quarter inside at
# the margin (siege labor, night soil, corpse and execution duty, and the leather CRAFT -
# sandals, drum heads, armor lacing - which is clean, quiet work done at home) while the
# wet, stinking phase of the trade (soak, unhair, dry) goes out to the water. Nagahara's
# yard stands ~1,390 ft from its quarter and is correct. What is NOT correct is the yard
# facing the opposite way out of town from the quarter, which puts the tanners' daily
# carcass haul straight through the rest of the settlement - the traffic real castle
# towns routed around with designated carcass ways.
# Same form and same threshold as execution_ground_on_the_outcast_side, whose rule this
# simply extends to the other burakumin-run works: a dot product against the quarter's
# bearing from the core, i.e. "within the same half of the compass". The CREMATION ground
# is deliberately NOT covered - it is monk-run and follows the temple/funerary complex,
# which need not be the outcast side at all (Hoshizora's stands 130 ft from its monastery
# and almost exactly opposite the quarter, and that is a correct map).


def _seg_0562_022___ty_dwell_all(*, M: Any = _UNBOUND, _ty_yards: Any = _UNBOUND, b: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.022 (_ty_dwell_all, b) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        _ty_dwell_all = (M.get("houses") or []) + [b for b in (M.get("buildings") or []) if b.get("kind") in DWELLING_KINDS]
    return _kept(locals(), ('_ty_dwell_all', 'b'))


def _seg_0562_023___ty_core(*, _ty_dwell_all: Any = _UNBOUND, _ty_yards: Any = _UNBOUND, h: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.023 (_ty_core, h) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        _ty_core = (sum(h["x"] for h in _ty_dwell_all) / len(_ty_dwell_all), sum(h["y"] for h in _ty_dwell_all) / len(_ty_dwell_all)) if _ty_dwell_all else None
    return _kept(locals(), ('_ty_core', 'h'))


# The core counts EVERY dwelling including the quarter's own (the same population
# execution_ground_on_the_outcast_side measures from - the quarter is part of the
# settlement). That makes the test meaningless when the quarter is ALL there is: the
# core lands on the quarter and no bearing exists. A settlement with nothing but
# burakumin dwellings has no "rest of town" for the works to be on the far side of, so
# the rule abstains rather than firing on a degenerate vector.


def _seg_0562_024__tanning_yard_on_the_outcast_side(
    *,
    _ty_bcx: Any = _UNBOUND,
    _ty_bcy: Any = _UNBOUND,
    _ty_bur: Any = _UNBOUND,
    _ty_core: Any = _UNBOUND,
    _ty_dwell_all: Any = _UNBOUND,
    _ty_wrong: Any = _UNBOUND,
    _ty_yards: Any = _UNBOUND,
    b: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    t_: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0562.024 (tanning_yard_on_the_outcast_side) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards and _ty_core and any(d.get("kind") != "burakumin" for d in _ty_dwell_all):
        _ty_bcx = sum(b["x"] for b in _ty_bur) / len(_ty_bur)
        _ty_bcy = sum(b["y"] for b in _ty_bur) / len(_ty_bur)
        _ty_wrong = [
            (
                round(t_["x"]),
                round(t_["y"]),
                round(math.degrees(abs((math.atan2(t_["y"] - _ty_core[1], t_["x"] - _ty_core[0]) - math.atan2(_ty_bcy - _ty_core[1], _ty_bcx - _ty_core[0]) + math.pi) % (2 * math.pi) - math.pi))),
            )
            for t_ in _ty_yards
            if (t_["x"] - _ty_core[0]) * (_ty_bcx - _ty_core[0]) + (t_["y"] - _ty_core[1]) * (_ty_bcy - _ty_core[1]) <= 0
        ]
        check(
            "tanning_yard_on_the_outcast_side",
            not _ty_wrong,
            f"tanning yard(s) facing the opposite way out of the settlement from the burakumin quarter "
            f"(x, y, degrees off the quarter's bearing): {_ty_wrong} - kegare leaves a settlement ONE way, and "
            f"the quarter marks which way. A yard on the far side sends the tanners' carcass haul back through "
            f"the whole settlement every day. Distance is fine (a city quarter stays in-wall while the works go "
            f"out to the water); the BEARING is not. Where a specific place overrides this on purpose, waive it "
            f"with meta(waivers=...) and say why",
        )
    return _kept(locals(), ('_ty_bcx', '_ty_bcy', '_ty_wrong', 'b', 'd', 't_'))


# ... AND THE YARD'S GROUND NEVER OVERLAPS THE WATER (GM 2026-07-25, after the real
# Tango yard drifted ~10 ft into its stream and the Hoshizora yard landed on a drain
# ditch; both frozen in pool/regressions/). Same doctrine as lumber_yard_clear_of_water:
# tanning_yard_on_water demands the bank within ~20 ft, but the tamped ground itself
# stays DRY - the soaking pits are dug earth (a pit dug below the waterline is just
# more stream) and the racks cure hides for 2-4 months, which standing water would rot.
# The staking frames are the ONE sanctioned in-water element: s.tanning_yard draws them
# BEYOND the ground rect, out in the shallows, so this check never sees them - a yard
# that reads as "a platform over the water" is this defect, not a design. Tested with
# the rect's true rotation against every watercourse's REAL half-width (the lumber-yard
# lesson: the generic ~6px check misses a wide river), via seg_to_rect_dist so a thin
# field ditch THREADING UNDER the rect between its corners is caught too (the Hoshizora
# capture; corner-sampling cannot see it). Exact abutment of the bank line is legal.


def _seg_0562_025___ty_water_all(*, _ty_water: Any = _UNBOUND, _ty_yards: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.025 (_ty_water_all) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        _ty_water_all = list(_ty_water)
    return _kept(locals(), ('_ty_water_all',))


def _seg_0562_026___ty_riv(*, M: Any = _UNBOUND, _ty_yards: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.026 (_ty_riv) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        _ty_riv = M.get("river") or {}
    return _kept(locals(), ('_ty_riv',))


def _seg_0562_027___ty_rp(*, _ty_riv: Any = _UNBOUND, _ty_yards: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.027 (_ty_rp) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        _ty_rp = _ty_riv.get("poly") or _ty_riv.get("pts")
    return _kept(locals(), ('_ty_rp',))


def _seg_0562_028___ty_water_all_1(*, _ty_riv: Any = _UNBOUND, _ty_rp: Any = _UNBOUND, _ty_water_all: Any = _UNBOUND, _ty_yards: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.028 (_ty_water_all) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards and _ty_rp:
        _ty_water_all.append((_ty_rp, _ty_riv.get("w", 40) / 2))
    return _kept(locals(), ('_ty_water_all',))


def _seg_0562_029___ty_d(*, M: Any = _UNBOUND, _ty_d: Any = _UNBOUND, _ty_water_all: Any = _UNBOUND, _ty_yards: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.029 (_ty_d, _ty_water_all) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        for _ty_d in M.get("field_ditches") or []:
            _ty_water_all.append((_ty_d["poly"], max(_ty_d.get("w", 4), _ty_d.get("w_tail", 0)) / 2))
    return _kept(locals(), ('_ty_d', '_ty_water_all'))


def _seg_0562_030___ty_pond(*, M: Any = _UNBOUND, _ty_yards: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.030 (_ty_pond) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        _ty_pond = M.get("pond")
    return _kept(locals(), ('_ty_pond',))


def _seg_0562_031___ty_wet(*, _ty_yards: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.031 (_ty_wet) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        _ty_wet = []  # type: ignore[var-annotated]
    return _kept(locals(), ('_ty_wet',))


def _seg_0562_032___hw(
    *,
    _hw: Any = _UNBOUND,
    _pl: Any = _UNBOUND,
    _ty_a: Any = _UNBOUND,
    _ty_hit: Any = _UNBOUND,
    _ty_pond: Any = _UNBOUND,
    _ty_water_all: Any = _UNBOUND,
    _ty_wet: Any = _UNBOUND,
    _ty_yards: Any = _UNBOUND,
    i: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    t_: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0562.032 (_hw, _pl, _ty_a, _ty_hit) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        for t_ in _ty_yards:
            _ty_hit = any(seg_to_rect_dist((_pl[i][0], _pl[i][1]), (_pl[i + 1][0], _pl[i + 1][1]), t_) < _hw - 1e-6 for _pl, _hw in _ty_water_all for i in range(len(_pl) - 1))
            if not _ty_hit and _ty_pond:
                # center-in-rect + BOUNDARY sampling, not corner-in-ellipse alone: the pond
                # can lap over a rect EDGE between two corners (same blind spot the ditch
                # case has for corner-sampling, just with the shapes' roles swapped)
                _ty_hit = pt_to_rect(_ty_pond[0], _ty_pond[1], t_) == 0 or any(
                    pt_to_rect(_ty_pond[0] + _ty_pond[2] * math.cos(_ty_a * math.tau / 32), _ty_pond[1] + _ty_pond[3] * math.sin(_ty_a * math.tau / 32), t_) == 0 for _ty_a in range(32)
                )
            if _ty_hit:
                _ty_wet.append((round(t_["x"]), round(t_["y"])))
    return _kept(locals(), ('_hw', '_pl', '_ty_a', '_ty_hit', '_ty_wet', 'i', 't_'))


def _seg_0562_033__tanning_yard_clear_of_water(*, _ty_wet: Any = _UNBOUND, _ty_yards: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.033 (tanning_yard_clear_of_water) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        check(
            "tanning_yard_clear_of_water",
            not _ty_wet,
            f"tanning yard ground overlapping open water at {_ty_wet} - the yard ABUTS the bank (the pits and "
            f"intake want the water within ~20 ft) but its tamped ground stays DRY: pits dug below the waterline "
            f"are just more stream, and hides curing 2-4 months on the racks rot if the ground floods. Only the "
            f"staking frames stand in the water, and they are drawn BEYOND the ground rect. Tested at each "
            f"watercourse's real half-width (streams/channels/canals/river/moat/field ditches/pond), rotation-aware",
        )
    return _kept(locals(), ())


# ... NOR CROPLAND. The trade's whole siting logic is MARGINAL riverbank ground - the
# caste's own name, kawaramono ("riverbed people"), records that they worked the
# unplowable floodway edges precisely because taxed, producing land was never theirs
# to take. A paddy is a flooded basin (no tamped work floor stands in one), and the
# pits' lime and bate liquor poison the soil for cropping - so a yard drawn on a field
# asserts ground that is simultaneously worked by a farmer and ruined for farming.


def _seg_0562_034___ty_cropolys(*, M: Any = _UNBOUND, _ty_yards: Any = _UNBOUND, f_: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.034 (_ty_cropolys, f_) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        _ty_cropolys = [f_["outline"] for f_ in M.get("fields") or [] if f_.get("outline")]
    return _kept(locals(), ('_ty_cropolys', 'f_'))


def _seg_0562_035___ty_cropolys_1(*, M: Any = _UNBOUND, _ty_cropolys: Any = _UNBOUND, _ty_yards: Any = _UNBOUND, p_: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.035 (_ty_cropolys, p_) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        _ty_cropolys += [p_["poly"] for p_ in M.get("dry_plots") or [] if p_.get("poly")]
    return _kept(locals(), ('_ty_cropolys', 'p_'))


def _seg_0562_036___ty_cropolys_2(*, M: Any = _UNBOUND, _ty_cropolys: Any = _UNBOUND, _ty_yards: Any = _UNBOUND, f_: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.036 (_ty_cropolys, f_) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        _ty_cropolys += [f_["outline"] for f_ in M.get("flower_fields") or [] if f_.get("outline")]
    return _kept(locals(), ('_ty_cropolys', 'f_'))


def _seg_0562_037___ty_on_crop(*, _ty_yards: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.037 (_ty_on_crop) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        _ty_on_crop = []  # type: ignore[var-annotated]
    return _kept(locals(), ('_ty_on_crop',))


def _seg_0562_038___ty_ol(
    *,
    _ty_cropolys: Any = _UNBOUND,
    _ty_ol: Any = _UNBOUND,
    _ty_on_crop: Any = _UNBOUND,
    _ty_sc: Any = _UNBOUND,
    _ty_yards: Any = _UNBOUND,
    cx_: Any = _UNBOUND,
    cy_: Any = _UNBOUND,
    e_: Any = _UNBOUND,
    k_: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    t_: Any = _UNBOUND,
    vx_: Any = _UNBOUND,
    vy_: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0562.038 (_ty_ol, _ty_on_crop, _ty_sc, cx_) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        for t_ in _ty_yards:
            _ty_sc = rect_corners(t_)
            for _ty_ol in _ty_cropolys:
                if (
                    any(point_in_poly(cx_, cy_, _ty_ol) for cx_, cy_ in _ty_sc)
                    or any(pt_to_rect(vx_, vy_, t_) == 0 for vx_, vy_ in _ty_ol)
                    or any(
                        segments_cross((_ty_ol[k_][0], _ty_ol[k_][1]), (_ty_ol[(k_ + 1) % len(_ty_ol)][0], _ty_ol[(k_ + 1) % len(_ty_ol)][1]), _ty_sc[e_], _ty_sc[(e_ + 1) % 4])
                        for k_ in range(len(_ty_ol))
                        for e_ in range(4)
                    )
                ):
                    _ty_on_crop.append((round(t_["x"]), round(t_["y"])))
                    break
    return _kept(locals(), ('_ty_ol', '_ty_on_crop', '_ty_sc', 'cx_', 'cy_', 'e_', 'k_', 't_', 'vx_', 'vy_'))


def _seg_0562_039__tanning_yard_clear_of_fields(*, _ty_on_crop: Any = _UNBOUND, _ty_yards: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.039 (tanning_yard_clear_of_fields) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        check(
            "tanning_yard_clear_of_fields",
            not _ty_on_crop,
            f"tanning yard(s) on cropland at {_ty_on_crop} - the yard sits on MARGINAL bank ground (kawaramono, "
            f"'riverbed people', worked the unplowable floodway edges), never on a field: a paddy is a flooded "
            f"basin that cannot carry a tamped work floor, and the pits' lime and bate liquor poison cropping "
            f"soil. Tested against field outlines, dry plots, and flower fields, rotation-aware",
        )
    return _kept(locals(), ())


# ... AND IT LIES ALONG THE BANK IT WORKS (GM 2026-07-26). A tanning yard is a working
# FRONTAGE, not a building: the soaking pits and the intake sit on the water side
# (local -y), the drying racks stand behind them, and every hide crosses from one to
# the other. So the yard's long axis runs WITH the watercourse - a stream at 30 deg
# takes a yard at 30 deg. Set the yard square to the map instead and the near corner
# goes in the water while the far corner strands a yard-length inland: the pits at one
# end sit on the bank and the pits at the other end do not, which is the one thing this
# layout cannot absorb, since the whole point of the ground is that the pit rank and
# the staking frames share a single edge of water. Riverside works follow their bank
# for the same reason a wharf does. Shape is city_wall_towers_aligned's: compare the
# RECORDED rot against the bearing of the water it fronts, mod 180 (a 180 deg flip is
# the same yard; a 90 deg turn stands it ACROSS the bank instead of along it).
#
# WHICH course is "its water" is decided by REACH, not by nearest. A yard at a
# confluence legitimately fronts either course that meets there, and the
# nearest-by-centerline answer is not even stable: Hoshizora's yard sits 3 px from a
# drain ditch bearing 43 deg and 5 px from the channel its intake cut actually taps at
# 83 deg, so by centerline the ditch wins and by intent the channel does. The reference
# set is therefore every course whose BANK - centerline distance minus that course's
# REAL half-width, the same measure tanning_yard_clear_of_water uses, since a 40px
# river's centerline is 20px from a yard that abuts it - falls inside the same ~20 ft
# reach tanning_yard_on_water calls "on the water", and the yard need only be square to
# ONE of them. A yard with NO bank in that reach is already failing
# tanning_yard_on_water, so this check abstains rather than reporting one defect twice.
#
# TOLERANCE is 15 deg - the wall-towers figure, not the gate furniture's 6 - because
# rot is set by hand against a hand-drawn meandering polyline, so a correct yard sits a
# few degrees off whichever segment it happens to be measured against (Hoshizora's own
# fronting channel bends from 83 to 56 deg within 50 px). It still separates cleanly,
# because the failure mode is not a small wobble but an AXIS-ALIGNED yard on a diagonal
# bank, which is 20-45 deg off: the pool's three good yards sit at 2.1, 3.8 and 7.2 deg
# while the pre-fix Tango yard sat at 22.9 (frozen in pool/regressions/).


def _seg_0562_040___ty_skew(*, _ty_yards: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.040 (_ty_skew) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        _ty_skew = []  # type: ignore[var-annotated]
    return _kept(locals(), ('_ty_skew',))


def _seg_0562_041___ty_a(
    *,
    _ty_a: Any = _UNBOUND,
    _ty_b: Any = _UNBOUND,
    _ty_da: Any = _UNBOUND,
    _ty_fronts: Any = _UNBOUND,
    _ty_hw: Any = _UNBOUND,
    _ty_off: Any = _UNBOUND,
    _ty_pl: Any = _UNBOUND,
    _ty_px: Any = _UNBOUND,
    _ty_skew: Any = _UNBOUND,
    _ty_water_all: Any = _UNBOUND,
    _ty_yards: Any = _UNBOUND,
    i: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    t_: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0562.041 (_ty_a, _ty_b, _ty_da, _ty_fronts) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        for t_ in _ty_yards:
            _ty_off, _ty_fronts = 90.0, False
            for _ty_pl, _ty_hw in _ty_water_all:
                for i in range(len(_ty_pl) - 1):
                    _ty_a = (_ty_pl[i][0], _ty_pl[i][1])
                    _ty_b = (_ty_pl[i + 1][0], _ty_pl[i + 1][1])
                    # a repeated point carries no bearing - skip it rather than read it as 0 deg
                    if _ty_a == _ty_b or max(0.0, seg_to_rect_dist(_ty_a, _ty_b, t_) - _ty_hw) > _ty_px(20.0):
                        continue
                    _ty_fronts = True
                    _ty_da = (t_.get("rot", 0) - math.degrees(math.atan2(_ty_b[1] - _ty_a[1], _ty_b[0] - _ty_a[0]))) % 180
                    _ty_off = min(_ty_off, _ty_da, 180 - _ty_da)
            if _ty_fronts and _ty_off > 15.0:
                _ty_skew.append((round(t_["x"]), round(t_["y"]), round(_ty_off)))
    return _kept(locals(), ('_ty_a', '_ty_b', '_ty_da', '_ty_fronts', '_ty_hw', '_ty_off', '_ty_pl', '_ty_skew', 'i', 't_'))


def _seg_0562_042__tanning_yard_square_to_its_water(*, _ty_skew: Any = _UNBOUND, _ty_yards: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0562.042 (tanning_yard_square_to_its_water) - body verbatim from _seg_0562__settlement_has_tanning_yard (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and _ty_yards:
        check(
            "tanning_yard_square_to_its_water",
            not _ty_skew,
            f"tanning yard(s) set askew to the bank they work (x, y, degrees off): {_ty_skew} - the yard's long "
            f"axis runs WITH its watercourse, so a stream at 30 deg takes a yard at 30 deg (s.tanning_yard's rot "
            f"lays the water side, local -y, against the bank). Square to the map on a diagonal bank puts one "
            f"corner in the water and strands the far end inland, so half the pit rank loses the edge of water "
            f"the whole ground exists to share. Judged against ANY course whose bank lies within the ~20 ft "
            f"on-water reach - a yard at a confluence may follow either - within 15 deg",
        )
    return _kept(locals(), ())
