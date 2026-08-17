"""Gate segments (capital ways and burial; keys 0106_027-0123) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from .common_01_geometry import _struct_rect, point_in_poly, rect_corners, seg_dist
from .common_03_capacity import (
    _UNBOUND,
    BURIAL_AC_BAND,
    CREMATION_FT_MAX_CITY,
    CREMATION_FT_MAX_TOWN,
    CREMATION_FT_MIN,
    DOOR_CLEAR_FT,
    GATE_FT_MAX,
    GATE_FT_MIN,
    OSSUARY_FT_MAX,
    OSSUARY_FT_MIN,
    WALL_FT_MAX,
    WALL_FT_MIN,
    _kept,
)

# A CITY ESTATE'S CAPTION LIVES INSIDE ITS WALLS (GM 2026-08-09): the court is blank by
# doctrine (its contents belong to the Mode A sheet), so the empty court is the label's
# ground - a caption hung outside sits where 021's fabric must flow. Judged on the
# recorded label box vs the compound footprint; a manor whose caption is recorded
# elsewhere on the sheet fires, a manor with no matching caption record is skipped
# (label() always records, so that never happens on a generated map).


def _seg_0106_027__cap_lbl_out(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.027 (cap_lbl_out) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        cap_lbl_out = []  # type: ignore[var-annotated]
    return _kept(locals(), ('cap_lbl_out',))


def _seg_0106_028__cap_L(*, M: Any = _UNBOUND, cap_L: Any = _UNBOUND, cap_lbl_out: Any = _UNBOUND, cmn2: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.028 (cap_L, cap_lbl_out, cmn2) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        for cmn2 in M.get("manors", []):
            if not cmn2.get("label"):
                continue
            for cap_L in M.get("labels", []):
                if (
                    len(cap_L) > 5
                    and cap_L[5] == cmn2["label"]
                    and not (
                        cmn2["x"] - cmn2["w"] / 2 - 1 <= cap_L[0]
                        and cap_L[2] <= cmn2["x"] + cmn2["w"] / 2 + 1
                        and cmn2["y"] - cmn2["h"] / 2 - 1 <= cap_L[1]
                        and cap_L[3] <= cmn2["y"] + cmn2["h"] / 2 + 1
                    )
                ):
                    cap_lbl_out.append(cmn2["label"])
    return _kept(locals(), ('cap_L', 'cap_lbl_out', 'cmn2'))


def _seg_0106_029__capital_estate_labels_inside(*, cap_lbl_out: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.029 (capital_estate_labels_inside) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        check(
            "capital_estate_labels_inside",
            not cap_lbl_out,
            f"estate caption(s) outside their own walls: {sorted(set(cap_lbl_out))[:4]} - a city estate's court is blank by doctrine, so the caption lives INSIDE it (manor(label_inside=True)), sized to clear the walls",
        )
    return _kept(locals(), ())


# A RIVER GETS A TOWPATH, NOT A ROAD (GM 2026-08-08; research/cities/capitals.md): water
# carried bulk far more cheaply than carts, so a trunk road shadowing a navigable river is
# redundant - a way may CROSS the river (bridged), never run along its bank. Judged
# centerline-to-centerline (ASSOCIATION family: the band dwarfs both widths, and the
# question is "does this way live on the bank", not a clearance).


def _seg_0106_030__cap_riv(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.030 (cap_riv) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        cap_riv = M.get("river")
    return _kept(locals(), ('cap_riv',))


def _seg_0106_031__capital_no_road_parallels_river(
    *,
    CAP_BANK: Any = _UNBOUND,
    CAP_RUN: Any = _UNBOUND,
    cap_best: Any = _UNBOUND,
    cap_dm: Any = _UNBOUND,
    cap_ex: Any = _UNBOUND,
    cap_ey: Any = _UNBOUND,
    cap_k: Any = _UNBOUND,
    cap_qx: Any = _UNBOUND,
    cap_qy: Any = _UNBOUND,
    cap_riv: Any = _UNBOUND,
    cap_rpts: Any = _UNBOUND,
    cap_run: Any = _UNBOUND,
    cap_shadow: Any = _UNBOUND,
    cap_slen: Any = _UNBOUND,
    cap_steps: Any = _UNBOUND,
    cap_sx: Any = _UNBOUND,
    cap_sy: Any = _UNBOUND,
    cap_t: Any = _UNBOUND,
    cap_ways: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cpts: Any = _UNBOUND,
    i: Any = _UNBOUND,
    j: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0106.031 (capital_no_road_parallels_river) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital' and isinstance(cap_riv, dict) and (cap_riv.get("pts") or cap_riv.get("poly")):
        cap_rpts = cap_riv.get("pts") or cap_riv["poly"]
        CAP_BANK = cap_riv.get("w", 40) / 2 + 45  # inside this band a way is ON the bank
        CAP_RUN = 280  # px of contiguous bank-riding; a perpendicular (bridged) crossing stays in-band far less
        cap_shadow = []
        for cpts, _cwid in cap_ways:
            cap_best = cap_run = 0.0
            for i in range(len(cpts) - 1):
                cap_sx, cap_sy = cpts[i]
                cap_ex, cap_ey = cpts[i + 1]
                cap_slen = math.hypot(cap_ex - cap_sx, cap_ey - cap_sy)
                cap_steps = max(1, int(cap_slen / 20))
                for cap_k in range(cap_steps):
                    cap_t = (cap_k + 0.5) / cap_steps
                    cap_qx, cap_qy = cap_sx + (cap_ex - cap_sx) * cap_t, cap_sy + (cap_ey - cap_sy) * cap_t
                    cap_dm = min(seg_dist(cap_qx, cap_qy, cap_rpts[j], cap_rpts[j + 1]) for j in range(len(cap_rpts) - 1))
                    if cap_dm < CAP_BANK:
                        cap_run += cap_slen / cap_steps
                        cap_best = max(cap_best, cap_run)
                    else:
                        cap_run = 0.0
            if cap_best > CAP_RUN:
                cap_shadow.append(f"a way rides the bank for {cap_best:.0f}px")
        check(
            "capital_no_road_parallels_river",
            not cap_shadow,
            f"{cap_shadow} - no trunk road parallels a navigable river; the bank carries a towpath (s.towpath), and the roads leave in the directions the water does not serve",
        )
    return _kept(
        locals(),
        (
            'CAP_BANK',
            'CAP_RUN',
            '_cwid',
            'cap_best',
            'cap_dm',
            'cap_ex',
            'cap_ey',
            'cap_k',
            'cap_qx',
            'cap_qy',
            'cap_rpts',
            'cap_run',
            'cap_shadow',
            'cap_slen',
            'cap_steps',
            'cap_sx',
            'cap_sy',
            'cap_t',
            'cpts',
            'i',
            'j',
        ),
    )


# THE AQUEDUCT (GM 2026-08-08): a capital outgrows what wells alone can supply, so it
# carries a supply channel - open OUTSIDE the wall, buried inside, the GATE as the
# boundary (Edo's josui, Odawara's sosui; research/cities/capitals.md).


def _seg_0106_032__cap_aqs(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.032 (cap_aqs) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        cap_aqs = M.get("aqueducts", [])
    return _kept(locals(), ('cap_aqs',))


def _seg_0106_033__capital_has_aqueduct(*, cap_aqs: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.033 (capital_has_aqueduct) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        check(
            "capital_has_aqueduct",
            bool(cap_aqs),
            "no aqueduct - draw s.aqueduct(...) from a river intake to a city gate; the wells stay (the conduit supplements them, it does not replace them)",
        )
    return _kept(locals(), ())


def _seg_0106_034__cap_gates(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.034 (cap_gates) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        cap_gates = M.get("gates") or []
    return _kept(locals(), ('cap_gates',))


def _seg_0106_035__capital_aqueduct_terminates_at_a_gate(
    *,
    M: Any = _UNBOUND,
    cap_ain: Any = _UNBOUND,
    cap_apoly: Any = _UNBOUND,
    cap_aq: Any = _UNBOUND,
    cap_aqs: Any = _UNBOUND,
    cap_gates: Any = _UNBOUND,
    cap_tx: Any = _UNBOUND,
    cap_ty: Any = _UNBOUND,
    cap_wallp: Any = _UNBOUND,
    cgx: Any = _UNBOUND,
    cgy: Any = _UNBOUND,
    check: Any = _UNBOUND,
    p: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0106.035 (capital_aqueduct_stays_outside_the_wall, capital_aqueduct_terminates_at_a_gate) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        for cap_aq in cap_aqs:
            cap_apoly = cap_aq.get("poly") or []
            if not cap_apoly:
                continue
            cap_tx, cap_ty = cap_apoly[-1]
            check(
                "capital_aqueduct_terminates_at_a_gate",
                any(math.hypot(cgx - cap_tx, cgy - cap_ty) < 90 for cgx, cgy in cap_gates),
                f"aqueduct terminus ({cap_tx:.0f},{cap_ty:.0f}) is at no city gate - the gate is the open/buried boundary; past it the conduit is buried and only its draw-basins show",
            )
            cap_wallp = M.get("wall") or []
            cap_ain = [p for p in cap_apoly if len(cap_wallp) >= 3 and point_in_poly(p[0], p[1], cap_wallp)]
            check(
                "capital_aqueduct_stays_outside_the_wall",
                not cap_ain,
                f"aqueduct has {len(cap_ain)} vertex/vertices inside the wall - no open watercourse threads the walled interior (inside, the conduit is honestly buried; its draw-basins are the visible part)",
            )
    return _kept(locals(), ('cap_ain', 'cap_apoly', 'cap_aq', 'cap_tx', 'cap_ty', 'cap_wallp', 'cgx', 'cgy', 'p'))


# DOORS OPEN OUTWARD; ROWS STACK AT MOST TWO DEEP (GM, 2026-07-18). An urban building's door
# glyph sits on its local +h/2 side (rotated by `rot` - settlement.building), so the door's
# world direction derives from the manifest alone. A door must open onto WALKABLE ground
# (street, roji, court, open space) - never into the back of another house an eave-gap away.
# FARMHOUSES ARE EXEMPT EVERYWHERE: a farmhouse always faces SOUTH (its garden and threshing
# ground need the sunlight - the orientation is canon); a city house has no sun constraint,
# so it must face open ground instead. The pair rule follows from the same fact: contiguous
# rows stack at most TWO deep (back-to-back, both fronts outward), because the middle row of
# a 3-stack has walls hard against BOTH long faces - those households would be trapped.
# Separations in real feet: an eave/drainage gap is ~3-6 ft (drainage, not an entrance), a
# walkable roji/court is >= ~10 ft; DOOR_CLEAR_FT = 7 sits cleanly between them at every
# map scale (ftpx converts to drawn px).


def _seg_0107__city_house_doors_unblocked(
    *,
    M: Any = _UNBOUND,
    _face_blocked: Any = _UNBOUND,
    b: Any = _UNBOUND,
    bad_doors: Any = _UNBOUND,
    bcorn: Any = _UNBOUND,
    bdiag: Any = _UNBOUND,
    blockers: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d: Any = _UNBOUND,
    door_clear: Any = _UNBOUND,
    fx: Any = _UNBOUND,
    fy: Any = _UNBOUND,
    h: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    o: Any = _UNBOUND,
    oc: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    sgn: Any = _UNBOUND,
    subj: Any = _UNBOUND,
    t: Any = _UNBOUND,
    th: Any = _UNBOUND,
    trapped: Any = _UNBOUND,
    ux: Any = _UNBOUND,
    uy: Any = _UNBOUND,
    vx: Any = _UNBOUND,
    vy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 107 (city_house_doors_unblocked, city_rows_max_two_deep) - body verbatim from the legacy gate() (feature 022)."""
    if scale in ("town", "city", "capital"):
        door_clear = DOOR_CLEAR_FT / meta.get("ftpx", 1)
        subj = [b for b in M.get("buildings", []) if "w" in b]
        blockers = subj + [h for h in M.get("houses", []) if "w" in h]
        bcorn = [rect_corners(_struct_rect(b)) for b in blockers]
        # PREFILTER RADII, not a verdict (family: prefilter - see edge_gap). The circumscribed
        # radius is the right tool here precisely because it over-states an extent: over-stating can
        # only admit a candidate the exact `point_in_poly` below then rejects, so the index prunes
        # and never decides. Do NOT "fix" these to true extents - that would start rejecting pairs
        # before the exact test sees them.
        bdiag = [math.hypot(b["w"], b["h"]) / 2 for b in blockers]

        def _face_blocked(b: dict[str, Any], sgn: float) -> bool:
            th = math.radians(b.get("rot", 0))
            ux, uy = -math.sin(th) * sgn, math.cos(th) * sgn  # outward normal of the (sgn=+1) door face
            vx, vy = -uy, ux  # lateral, along the face
            fx, fy = b["x"] + ux * b["h"] / 2, b["y"] + uy * b["h"] / 2  # face center
            rr = math.hypot(b["w"], b["h"]) / 2 + door_clear + 1
            for o, oc, od in zip(blockers, bcorn, bdiag, strict=True):
                if o is b or math.hypot(o["x"] - b["x"], o["y"] - b["y"]) > rr + od:
                    continue
                for d in (0.8, door_clear * 0.55, door_clear):
                    for t in (-0.3 * b["w"], 0.0, 0.3 * b["w"]):
                        if point_in_poly(fx + ux * d + vx * t, fy + uy * d + vy * t, oc):
                            return True
            return False

        bad_doors = [b for b in subj if _face_blocked(b, 1.0)]
        check(
            "city_house_doors_unblocked",
            not bad_doors,
            f"{len(bad_doors)} building(s) whose DOOR opens into another structure within ~{DOOR_CLEAR_FT:.0f} real ft "
            f"(an eave gap, not an entrance): {[(round(b['x']), round(b['y']), b.get('kind')) for b in bad_doors[:5]]} - a city house faces "
            f"open ground (street/roji/court); in a back-to-back pair both doors face OUTWARD (rot the row 180), never into a neighbor's back wall",
        )
        trapped = [b for b in subj if _face_blocked(b, 1.0) and _face_blocked(b, -1.0)]
        check(
            "city_rows_max_two_deep",
            not trapped,
            f"{len(trapped)} building(s) walled on BOTH long faces - the trapped middle of a 3-deep row stack: "
            f"{[(round(b['x']), round(b['y']), b.get('kind')) for b in trapped[:5]]} - rows/columns stack at most TWO deep (back-to-back); "
            f"after every pair leave a walkable roji/court (>= ~10 real ft), so every household fronts open ground",
        )
    return _kept(locals(), ('_face_blocked', 'b', 'bad_doors', 'bcorn', 'bdiag', 'blockers', 'door_clear', 'h', 'subj', 'trapped'))


# A MERCHANT ESTATE'S WALL STANDS ON DRY, PRIVATE GROUND (GM, 2026-07-19). The walled
# compound of a very-rich urban merchant must not run its perimeter wall through WATER
# (a wall footed in a canal/dock basin is undermined, and the working quay/towpath must
# stay open to the boats and porters that make the merchant rich) or through a FIRE TOWER
# (the fire watch is municipal - it needs its own footing, daylight around the frame, and
# access for the watch; it cannot be embedded in a private compound wall). The whole
# perimeter is walked, gate gap included - a courtyard gate opening straight onto water
# or into the tower frame is the same siting error.


def _seg_0108__merchant_estate_wall_clear_of_water(
    *,
    M: Any = _UNBOUND,
    WMARG: Any = _UNBOUND,
    _in_grown_rect: Any = _UNBOUND,
    _near_line: Any = _UNBOUND,
    _tower_conflict: Any = _UNBOUND,
    _wall_hits: Any = _UNBOUND,
    _wall_pts: Any = _UNBOUND,
    al: Any = _UNBOUND,
    cc: Any = _UNBOUND,
    check: Any = _UNBOUND,
    dk: Any = _UNBOUND,
    e: Any = _UNBOUND,
    est: Any = _UNBOUND,
    est_ftowers: Any = _UNBOUND,
    est_on_st: Any = _UNBOUND,
    est_streets: Any = _UNBOUND,
    est_waters: Any = _UNBOUND,
    est_wet: Any = _UNBOUND,
    ew: Any = _UNBOUND,
    fn: Any = _UNBOUND,
    gc: Any = _UNBOUND,
    hw: Any = _UNBOUND,
    it: Any = _UNBOUND,
    k: Any = _UNBOUND,
    name: Any = _UNBOUND,
    pcx: Any = _UNBOUND,
    pcy: Any = _UNBOUND,
    prx: Any = _UNBOUND,
    pry: Any = _UNBOUND,
    pts: Any = _UNBOUND,
    px_: Any = _UNBOUND,
    py_: Any = _UNBOUND,
    rd: Any = _UNBOUND,
    rv: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    si: Any = _UNBOUND,
    st: Any = _UNBOUND,
    steps: Any = _UNBOUND,
    t: Any = _UNBOUND,
    towered: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 108 (merchant_estate_wall_clear_of_fire_towers, merchant_estate_wall_clear_of_streets, merchant_estate_wall_clear_of_water) - body verbatim from the legacy gate() (feature 022)."""
    if scale in ("town", "city") and M.get("merchant_estates"):
        WMARG = 1.5  # px of daylight demanded beyond the drawn footprints/line widths

        def _near_line(pts: Any, hw: float) -> Any:
            return lambda px_, py_: any(seg_dist(px_, py_, pts[k], pts[k + 1]) < hw for k in range(len(pts) - 1))

        def _in_grown_rect(it: dict[str, Any]) -> Any:
            gc = rect_corners(_struct_rect({**it, "w": it["w"] + 2 * WMARG, "h": it["h"] + 2 * WMARG}))
            return lambda px_, py_: point_in_poly(px_, py_, gc)

        est_waters: list[tuple[str, Any]] = [("canal", _near_line(cc["poly"], cc.get("w", 12) / 2 + WMARG)) for cc in M.get("canals", [])]  # type: ignore[no-redef]
        if M.get("moat"):
            est_waters.append(("moat", _near_line(M["moat"], M.get("moat_width", 22) / 2 + WMARG)))
        rv = M.get("river")
        if rv:
            est_waters.append(("river", _near_line(rv["pts"], rv.get("w", 40) / 2 + WMARG)))
        est_waters += [("dock", _in_grown_rect(dk)) for dk in M.get("docks", [])]
        if M.get("pond"):
            pcx, pcy, prx, pry = M["pond"]
            est_waters.append(("pond", lambda px_, py_: ((px_ - pcx) / (prx + WMARG)) ** 2 + ((py_ - pcy) / (pry + WMARG)) ** 2 <= 1))
        est_ftowers: list[tuple[str, Any]] = [("fire tower", _in_grown_rect(t)) for t in M.get("fire_towers", []) if "w" in t]  # type: ignore[no-redef]

        def _wall_pts(est: dict[str, Any]) -> list[tuple[float, float]]:
            ex0, ey0, ex1, ey1 = est["x"] - est["w"] / 2, est["y"] - est["h"] / 2, est["x"] + est["w"] / 2, est["y"] + est["h"] / 2
            pts = []
            for p0, p1 in [((ex0, ey0), (ex1, ey0)), ((ex1, ey0), (ex1, ey1)), ((ex1, ey1), (ex0, ey1)), ((ex0, ey1), (ex0, ey0))]:
                steps = max(2, int(math.hypot(p1[0] - p0[0], p1[1] - p0[1]) / 3))
                pts += [(p0[0] + (p1[0] - p0[0]) * si / steps, p0[1] + (p1[1] - p0[1]) * si / steps) for si in range(steps + 1)]
            return pts

        def _wall_hits(est: dict[str, Any], targets: list[tuple[str, Any]]) -> list[str]:
            pts = _wall_pts(est)
            return [name for name, fn in targets if any(fn(px_, py_) for px_, py_ in pts)]

        est_wet = [(round(e["x"]), round(e["y"]), _wall_hits(e, est_waters)) for e in M["merchant_estates"]]
        est_wet = [ew for ew in est_wet if ew[2]]
        check(
            "merchant_estate_wall_clear_of_water",
            not est_wet,
            f"merchant-estate wall(s) running through open water: {est_wet} - a compound wall stands on dry ground; "
            f"the canal/dock/moat/pond edge is working waterfront (boats, porters, the towpath), not private wall footing - move the estate clear",
        )

        # a tower ENCLOSED in the private court (wall-line clear, tower trapped inside) is the
        # same siting error as a wall through it - the watch must reach its tower from public ground
        def _tower_conflict(e: dict[str, Any]) -> bool:
            if _wall_hits(e, est_ftowers):
                return True
            return any(abs(t["x"] - e["x"]) < e["w"] / 2 and abs(t["y"] - e["y"]) < e["h"] / 2 for t in M.get("fire_towers", []) if "w" in t)

        towered = [(round(e["x"]), round(e["y"])) for e in M["merchant_estates"] if _tower_conflict(e)]
        check(
            "merchant_estate_wall_clear_of_fire_towers",
            not towered,
            f"merchant-estate wall(s) running through - or enclosing - a fire tower: {towered} - the fire watch is municipal; the tower needs its own "
            f"footing, daylight around the braced frame, and watch access from public ground - it cannot be embedded in (or walled inside) a private compound; move the estate or the tower",
        )

        # THE SAME WALLS STAY OFF THE STREETS (GM follow-up, 2026-07-19): a compound wall
        # standing in a street bed blocks the public way - the wall may LINE a street (that is
        # what a walled compound on a block looks like) but never stand IN its cleared band.
        est_streets: list[tuple[str, Any]] = [("street", _near_line(st["pts"], st.get("w", 12) / 2 + WMARG)) for st in M.get("town_streets", [])]  # type: ignore[no-redef]
        est_streets += [("alley", _near_line(al["pts"], al.get("w", 8) / 2 + WMARG)) for al in M.get("alleys", [])]
        est_streets += [("road", _near_line(rd["pts"], rd["w"] / 2 + WMARG)) for rd in M.get("roads", [])]
        if M.get("road"):
            est_streets.append(("road", _near_line(M["road"], M.get("road_width", 26) / 2 + WMARG)))
        if M.get("ring_road"):
            est_streets.append(("ring road", _near_line(M["ring_road"], M.get("ring_road_width", 7) / 2 + WMARG)))
        est_on_st = [(round(e["x"]), round(e["y"]), _wall_hits(e, est_streets)) for e in M["merchant_estates"]]
        est_on_st = [ew for ew in est_on_st if ew[2]]
        check(
            "merchant_estate_wall_clear_of_streets",
            not est_on_st,
            f"merchant-estate wall(s) standing IN a street/alley/road bed: {est_on_st} - the public way stays open; "
            f"a compound wall may line a street but never stand in its cleared band - move the estate off the street",
        )
    return _kept(
        locals(),
        (
            'WMARG',
            '_in_grown_rect',
            '_near_line',
            '_tower_conflict',
            '_wall_hits',
            '_wall_pts',
            'al',
            'cc',
            'dk',
            'e',
            'est_ftowers',
            'est_on_st',
            'est_streets',
            'est_waters',
            'est_wet',
            'ew',
            'pcx',
            'pcy',
            'prx',
            'pry',
            'pts',
            'rd',
            'rv',
            'st',
            't',
            'towered',
        ),
    )


# COMPOUND GATES AND WALLS TO SCALE (GM, 2026-07-19). The walled compounds (samurai country
# estates/manors, the governor's yamen, merchant estates, the mausoleum) draw only walls +
# gate + a deliberately BLANK court (the interior is its own Mode A diagram) - so the wall
# and gate ARE the feature, and they must be honest: a samurai residence gate (nagayamon /
# yakuimon) opens ~9-12 real ft (cart + palanquin), a grand yamen gatehouse up to ~24 ft;
# the old fixed-pixel gap (+-34px) drew a 204 ft opening at city scale - most of a wall
# missing. Walls (dobei/tsuijibei) run ~1.5-2 ft thick, drawn true-width-or-floored (the
# 2px cartographic floor = 6 ft at city scale; band top 8 allows it). A manifest that
# records no gate_w predates the to-scale engine and cannot prove its gates - regenerate.


def _seg_0109___gcomp(*, M: Any = _UNBOUND, me: Any = _UNBOUND, mn: Any = _UNBOUND, mu: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 109 (_gcomp, me, mn, mu) - body verbatim from the legacy gate() (feature 022)."""
    _gcomp = [("manor", mn) for mn in M.get("manors", [])] + [("merchant estate", me) for me in M.get("merchant_estates", [])] + [("mausoleum", mu) for mu in M.get("mausoleums", [])]
    return _kept(locals(), ('_gcomp', 'me', 'mn', 'mu'))


def _seg_0110___gcomp_1(*, M: Any = _UNBOUND, _gcomp: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 110 (_gcomp) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("governor_mansion"):
        _gcomp.append(("governor's mansion", M["governor_mansion"]))
    return _kept(locals(), ('_gcomp',))


def _seg_0111__compound_gates_to_scale(
    *,
    _gcomp: Any = _UNBOUND,
    _gftpx: Any = _UNBOUND,
    check: Any = _UNBOUND,
    gc: Any = _UNBOUND,
    gcomp_bad: Any = _UNBOUND,
    gft: Any = _UNBOUND,
    gkind: Any = _UNBOUND,
    gw: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    side: Any = _UNBOUND,
    wallft: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 111 (compound_gates_to_scale) - body verbatim from the legacy gate() (feature 022)."""
    if _gcomp:
        _gftpx = meta.get("ftpx", 1)
        gcomp_bad = []
        for gkind, gc in _gcomp:
            gw = gc.get("gate_w")
            if gw is None:
                gcomp_bad.append((gkind, round(gc["x"]), round(gc["y"]), "gate unrecorded - regenerate with the to-scale engine"))
                continue
            gft = gw * _gftpx
            side = gc["w"] if gc.get("gate_dir", "south") in ("north", "south") else gc["h"]
            wallft = gc.get("wall_w", 0) * _gftpx
            if not GATE_FT_MIN <= gft <= GATE_FT_MAX:
                gcomp_bad.append((gkind, round(gc["x"]), round(gc["y"]), f"gate opening {gft:.0f} ft outside [{GATE_FT_MIN:.0f},{GATE_FT_MAX:.0f}]"))
            elif gw > 0.4 * side:
                gcomp_bad.append((gkind, round(gc["x"]), round(gc["y"]), f"gate is {gw / side:.0%} of its wall side - reads as a missing wall, not a gate"))
            elif not WALL_FT_MIN <= wallft <= WALL_FT_MAX:
                gcomp_bad.append((gkind, round(gc["x"]), round(gc["y"]), f"wall drawn {wallft:.0f} ft thick, outside [{WALL_FT_MIN:.0f},{WALL_FT_MAX:.0f}]"))
        check(
            "compound_gates_to_scale",
            not gcomp_bad,
            f"walled compound(s) with out-of-scale gates/walls: {gcomp_bad[:4]} - a residence gate opens ~9-12 real ft (a grand "
            f"yamen gatehouse up to ~24), walls run ~2 ft thick (2px cartographic floor); the blank court is deliberate (the interior is its own diagram) so the wall+gate must carry the realism",
        )
    return _kept(locals(), ('_gftpx', 'gc', 'gcomp_bad', 'gft', 'gkind', 'gw', 'side', 'wallft'))


# FUNERARY FEATURES TO SCALE (GM, 2026-07-19; anchors in settlements.md "Historical
# grounding"). The old glyphs were FIXED-PIXEL and silently tripled at city scale.


def _seg_0112___fftpx(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 112 (_fftpx) - body verbatim from the legacy gate() (feature 022)."""
    _fftpx = meta.get("ftpx", 1)
    return _kept(locals(), ('_fftpx',))


def _seg_0113__crem_bad() -> dict[str, Any]:
    """Gate segment 113 (crem_bad) - body verbatim from the legacy gate() (feature 022)."""
    crem_bad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('crem_bad',))


def _seg_0114__cg(
    *, M: Any = _UNBOUND, _fftpx: Any = _UNBOUND, cg: Any = _UNBOUND, crem_bad: Any = _UNBOUND, crem_cap: Any = _UNBOUND, long_ft: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 114 (cg, crem_bad, crem_cap, long_ft) - body verbatim from the legacy gate() (feature 022)."""
    for cg in M.get("cremation_grounds", []):
        long_ft = max(cg["w"], cg["h"]) * _fftpx
        crem_cap = CREMATION_FT_MAX_CITY if scale in ("city", "capital") else CREMATION_FT_MAX_TOWN  # a capital cremates a city's dead (GM 2026-08-10)
        if not CREMATION_FT_MIN <= long_ft <= crem_cap:
            crem_bad.append((round(cg["x"]), round(cg["y"]), f"{long_ft:.0f} ft across vs [{CREMATION_FT_MIN:.0f},{crem_cap:.0f}]"))
    return _kept(locals(), ('cg', 'crem_bad', 'crem_cap', 'long_ft'))


def _seg_0115__cremation_ground_to_scale(*, M: Any = _UNBOUND, check: Any = _UNBOUND, crem_bad: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 115 (cremation_ground_to_scale) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("cremation_grounds"):
        check(
            "cremation_ground_to_scale",
            not crem_bad,
            f"cremation ground(s) out of scale: {crem_bad} - a sanmai's working core (7 ft hearth, shelter, bone platform, mourner ground) "
            f"clears 30-80 ft for a village/town and ~80-160 ft for a provincial city; even the crematory serving metropolitan Edo was ~180 ft square",
        )
    return _kept(locals(), ())


def _seg_0116__o(*, M: Any = _UNBOUND, _fftpx: Any = _UNBOUND, o: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 116 (o, oss_bad) - body verbatim from the legacy gate() (feature 022)."""
    oss_bad = [(round(o["x"]), round(o["y"]), f"{max(o['w'], o['h']) * _fftpx:.0f} ft") for o in M.get("ossuaries", []) if not OSSUARY_FT_MIN <= max(o["w"], o["h"]) * _fftpx <= OSSUARY_FT_MAX]
    return _kept(locals(), ('o', 'oss_bad'))


def _seg_0117__ossuary_to_scale(*, M: Any = _UNBOUND, check: Any = _UNBOUND, oss_bad: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 117 (ossuary_to_scale) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("ossuaries"):
        check(
            "ossuary_to_scale",
            not oss_bad,
            f"pauper ossuary mound(s) out of scale: {oss_bad} (band [{OSSUARY_FT_MIN:.0f},{OSSUARY_FT_MAX:.0f}] ft) - a muenzuka is a 10-30 ft mound "
            f"(cremated bone takes almost no volume; even Kyoto's monumental state-built Mimizuka is ~50 ft at the base); the band top allows the small-glyph legibility floor",
        )
    return _kept(locals(), ())


def _seg_0118__burial_grounds_sized_to_population(
    *, M: Any = _UNBOUND, _fftpx: Any = _UNBOUND, c: Any = _UNBOUND, check: Any = _UNBOUND, hi: Any = _UNBOUND, lo: Any = _UNBOUND, scale: Any = _UNBOUND, total_ac: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 118 (burial_grounds_sized_to_population) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("cemeteries") and scale in ("village", "town", "city"):
        total_ac = sum(c["w"] * c["h"] for c in M["cemeteries"]) * _fftpx * _fftpx / 43_560
        lo, hi = BURIAL_AC_BAND[scale]
        check(
            "burial_grounds_sized_to_population",
            lo <= total_ac <= hi,
            f"total burial ground {total_ac:.2f} acres vs the {scale} band [{lo},{hi}] - size the grounds to the population SERVED "
            f"(cremation-then-inter culture, ~1 generation of active plots before reuse: village ~0.15-0.30 ac for the ~800-person DISTRICT it buries - "
            f"hamlets carry their urns here and draw no ground; town ~0.25-0.75, city ~0.75-2 split across yards); "
            f"the ladder must read MONOTONE with population served - a village ground must never dwarf a town's",
        )
    return _kept(locals(), ('c', 'hi', 'lo', 'total_ac'))


# FARMSTEADS ARE WITHIN REACH OF A WELL (town/city): the farm belt drinks daily too, and
# Rokugan's unusually well-run domains sink wells liberally (the same liberty behind the
# literal urban idobata count) - so no farmhouse stands more than 500 REAL FEET from a
# well (a ~2-minute bucket walk; a real farmstead would often have its own). Farmhouses
# within 150 real ft of the VIEW edge are exempt: their fields already run off-map, and
# their well is presumed just off the edge with the rest of their steading (GM rule,
# 2026-07-21). Villages are not gated here - their wells already sit among the houses
# (wells_among_dwellings). WHY: settlements.md wells entry.


def _seg_0119__farm_wells_within_reach(
    *,
    M: Any = _UNBOUND,
    _fw_edge: Any = _UNBOUND,
    _fw_far: Any = _UNBOUND,
    _fw_ftpx: Any = _UNBOUND,
    _fw_h: Any = _UNBOUND,
    _fw_reach: Any = _UNBOUND,
    _fw_view: Any = _UNBOUND,
    _fw_w: Any = _UNBOUND,
    check: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 119 (farm_wells_within_reach) - body verbatim from the legacy gate() (feature 022)."""
    if scale in ("town", "city") and M.get("houses"):
        _fw_ftpx = float(meta.get("ftpx", 1) or 1)
        _fw_reach = 500.0 / _fw_ftpx
        _fw_edge = 150.0 / _fw_ftpx
        _fw_view = meta.get("view") or [0, 0, meta.get("W", 10**9), meta.get("H", 10**9)]
        _fw_far = []
        for _fw_h in M["houses"]:
            if min(_fw_h["x"] - _fw_view[0], _fw_h["y"] - _fw_view[1], _fw_view[0] + _fw_view[2] - _fw_h["x"], _fw_view[1] + _fw_view[3] - _fw_h["y"]) < _fw_edge:
                continue
            if not any((_fw_h["x"] - _fw_w["x"]) ** 2 + (_fw_h["y"] - _fw_w["y"]) ** 2 <= _fw_reach**2 for _fw_w in M.get("wells", [])):
                _fw_far.append((round(_fw_h["x"]), round(_fw_h["y"])))
        check(
            "farm_wells_within_reach",
            not _fw_far,
            f"{len(_fw_far)} farmhouse(s) further than 500 real ft from any well {_fw_far[:5]} - the farm belt "
            f"drinks daily too; call s.farm_wells() after s.farmsteads() (map-edge farmsteads are exempt - their "
            f"well is presumed just off the edge)",
        )
    return _kept(locals(), ('_fw_edge', '_fw_far', '_fw_ftpx', '_fw_h', '_fw_reach', '_fw_view', '_fw_w'))


# DRY-CROP PLOTS ARE TO SCALE: a hem parcel is a smallholder's strip (~1 mu / ~0.17 acre
# mean in Buck's surveys - the same grain the paddy plots and the polder parcels obey), so
# the map-wide MEAN dry-plot area must stay under 0.25 real acres. The tiling constants in
# _dry_fields (plot width 46px, row depth 36px) are real-feet quantities tuned at 2 ft/px:
# unscaled at the 3 ft/px city grain they doubled every parcel's area (0.34-0.38 acre
# means), dry cells visibly dwarfing the ~78 ft rice plots beside them - "set a number of
# pixels, not a number of feet" (the GM's exact catch, 2026-07-21). WHY: settlements.md.


def _seg_0120___ds_dps(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 120 (_ds_dps) - body verbatim from the legacy gate() (feature 022)."""
    _ds_dps = M.get("dry_plots", [])
    return _kept(locals(), ('_ds_dps',))


def _seg_0121__dry_plots_to_scale(
    *,
    _ds_a: Any = _UNBOUND,
    _ds_areas: Any = _UNBOUND,
    _ds_d: Any = _UNBOUND,
    _ds_dps: Any = _UNBOUND,
    _ds_ftpx: Any = _UNBOUND,
    _ds_max: Any = _UNBOUND,
    _ds_mean: Any = _UNBOUND,
    _ds_p: Any = _UNBOUND,
    _vs_a: Any = _UNBOUND,
    _vs_big: Any = _UNBOUND,
    _vs_d: Any = _UNBOUND,
    _vs_p: Any = _UNBOUND,
    _vs_veg: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d: Any = _UNBOUND,
    i: Any = _UNBOUND,
    meta: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 121 (dry_plots_to_scale, vegetable_beds_are_intensive) - body verbatim from the legacy gate() (feature 022)."""
    if _ds_dps:
        _ds_ftpx = float(meta.get("ftpx", 1) or 1)
        _ds_areas = []
        for _ds_d in _ds_dps:
            _ds_p = _ds_d["poly"]
            _ds_a = abs(sum(_ds_p[i][0] * _ds_p[(i + 1) % len(_ds_p)][1] - _ds_p[(i + 1) % len(_ds_p)][0] * _ds_p[i][1] for i in range(len(_ds_p)))) / 2
            _ds_areas.append(_ds_a * _ds_ftpx * _ds_ftpx / 43560)
        _ds_mean = sum(_ds_areas) / len(_ds_areas)
        # the MEAN alone let a small oversized subpopulation hide behind many right-sized hem
        # parcels (Tango's vegetable tract at 0.3-0.5 acre diluted to a passing mean by ~70
        # hem plots, 2026-07-21) - so the largest single parcel is capped too: pool-wide the
        # honest maximum is ~0.30 acre (biggest hem parcel), villages max ~0.26
        _ds_max = max(_ds_areas)
        # a garden VEGETABLE bed (daikon/greens/onions/beans - VEG_CROPS, in-wall intensive
        # tracts) is hand-worked ground, distinctly SMALLER than a grain-field hem strip: cap
        # each such plot at 0.15 real acres (fixed beds ~0.10; the pre-fix uneven column split
        # left 0.24-acre veg slabs, the biggest dry parcels on the map - backwards for a kitchen
        # garden; GM 2026-07-22). Only fires where veg crops exist (cities with a veg tract).
        _vs_veg = [d for d in _ds_dps if d.get("crop") in {"daikon", "greens", "onions", "beans"}]
        if _vs_veg:
            _vs_big = []
            for _vs_d in _vs_veg:
                _vs_p = _vs_d["poly"]
                _vs_a = abs(sum(_vs_p[i][0] * _vs_p[(i + 1) % len(_vs_p)][1] - _vs_p[(i + 1) % len(_vs_p)][0] * _vs_p[i][1] for i in range(len(_vs_p)))) / 2 * _ds_ftpx * _ds_ftpx / 43560
                if _vs_a > 0.15:
                    _vs_big.append(round(_vs_a, 3))
            check(
                "vegetable_beds_are_intensive",
                not _vs_big,
                f"{len(_vs_big)} vegetable-garden bed(s) larger than 0.15 real acres {sorted(_vs_big, reverse=True)[:4]} - "
                f"an in-wall kitchen-garden tract is INTENSIVE hand-worked ground, its beds smaller than a grain-field "
                f"hem strip, not the biggest dry parcels on the map (split the tract into even ~55 ft beds)",
            )
        check(
            "dry_plots_to_scale",
            _ds_mean <= 0.25 and _ds_max <= 0.35,
            f"mean dry-crop plot area {_ds_mean:.2f} real acres (want <= 0.25), largest {_ds_max:.2f} (want <= 0.35) - a hem parcel is a smallholder strip "
            f"(~1 mu / ~0.17 acre, Buck); oversized cells mean the _dry_fields tiling constants were used as raw px "
            f"at a coarser grain instead of real feet (pass/scale them by grain)",
        )
    return _kept(locals(), ('_ds_a', '_ds_areas', '_ds_d', '_ds_ftpx', '_ds_max', '_ds_mean', '_ds_p', '_vs_a', '_vs_big', '_vs_d', '_vs_p', '_vs_veg', 'd', 'i'))


# EVERY COMB PADDY FAN HAS A FIELD FLOOR so its canal-JUNCTION triangles (the head-race fork,
# the outfall corner where a supply canal dies at the drain, the confluence wedges) are not bare
# parchment - the "blank bits on the paddies" the GM circled across cities AND villages/hamlets
# (2026-07-22). The comb carve tessellates its plots but cannot fill those wedges; a base-fill
# polygon (s.comb_base_fill, recorded in M['comb_floors'][name]) draws under the plots so the
# gaps read as field ground, not a hole. Villages/hamlets that draw via draw_comb_field or inline
# both route through the helper now. Any paddy fan (a field with field_ditches, i.e. an irrigated
# comb) must therefore have a floor. paddy_fan_gapless's 2% tolerance let the small junctions slip;
# this pins the floor at every scale.


def _seg_0122__paddy_fan_has_floor(
    *, M: Any = _UNBOUND, _ditched: Any = _UNBOUND, _floors: Any = _UNBOUND, _pf_bad: Any = _UNBOUND, check: Any = _UNBOUND, d: Any = _UNBOUND, f: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 122 (paddy_fan_has_floor) - body verbatim from the legacy gate() (feature 022)."""
    if scale in ("hamlet", "village", "town", "city"):
        _floors = M.get("comb_floors", {})
        _ditched = {d.get("field") for d in M.get("field_ditches", [])}
        _pf_bad = [f.get("name") for f in M.get("fields", []) if f.get("kind") == "paddy" and f.get("name") in _ditched and f.get("name") not in _floors]
        check(
            "paddy_fan_has_floor",
            not _pf_bad,
            f"comb paddy fan(s) with no field floor: {_pf_bad} - the carve leaves bare parchment triangles at the "
            f"canal junctions (head-race fork, outfall corner, confluences); call s.comb_base_fill(net, name) "
            f"before drawing the plots so it draws a floor under them and records M['comb_floors'][name]",
        )
    return _kept(locals(), ('_ditched', '_floors', '_pf_bad', 'd', 'f'))


# A COMB'S HEAD GROUND IS QUILTED (city-scale): the supply canals run THROUGH cultivated
# land - paddy below, dry-crop hem above - never through bare parchment. The fan head (the
# band along the mains and the fork triangle between the arms) is uncommanded by gravity,
# so the carve correctly never plants RICE there; the HEM system is what fills it (villages
# add scrub besides, so they read full either way). paddy_fan_gapless deliberately samples
# only the commanded interior - which is exactly why the bare-head regression (the GM's
# circled screenshot, 2026-07-21) sailed through green. This check owns that band: sample
# both flanks of every recorded MAIN channel beyond the hem berm, skip the sluice mouth and
# moat/ring corridors, and require the map-wide bare fraction under 20% (calibrated: the
# pre-fix manifest reads ~25%, the quilted maps ~13-16%). Fields recording plot_polys (the
# city gens) are gated; a village opts in by recording them.


def _seg_0123___hq_ftpx(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 123 (_hq_ftpx) - body verbatim from the legacy gate() (feature 022)."""
    _hq_ftpx = float(meta.get("ftpx", 1) or 1)
    return _kept(locals(), ('_hq_ftpx',))
