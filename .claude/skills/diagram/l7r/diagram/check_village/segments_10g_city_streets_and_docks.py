"""Gate segments (city streets and docks; keys 0563_309-0563_333) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from .common_01_geometry import Pt, point_in_poly, poly_dist, seg_closest, seg_dist
from .common_03_capacity import _UNBOUND, _kept, empty_street_runs


def _seg_0563_309__city_estates_multiple_shown(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, shown_est: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.309 (city_estates_multiple_shown) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_estates_multiple_shown",
            len(shown_est) >= 1,
            f"{len(shown_est)} samurai estates fall inside the map window - show at least 1 (a fraction cropped at the edge is fine); the rest of the gentry sit farther out, implied off-map",
        )
    return _kept(locals(), ())


# the Imperial-road label must sit OUTSIDE the walls (inside, the roadway is a city street)


def _seg_0563_310__rlab(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.310 (rlab) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        rlab = M.get("road_label")
    return _kept(locals(), ('rlab',))


def _seg_0563_311__city_road_label_outside_walls(*, check: Any = _UNBOUND, inwall: Any = _UNBOUND, meta: Any = _UNBOUND, rlab: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.311 (city_road_label_outside_walls) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and rlab:
        check(
            "city_road_label_outside_walls",
            not inwall(rlab[0], rlab[1]),
            "the 'Imperial Road' label must sit outside the walls - inside the gates the same roadway is a city street, a city (not Imperial) responsibility",
        )
    return _kept(locals(), ())


def _seg_0563_312__empty_city_streets(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.312 (empty_city_streets) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        empty_city_streets = empty_street_runs(M, w)
    return _kept(locals(), ('empty_city_streets',))


def _seg_0563_313__city_streets_have_buildings(*, check: Any = _UNBOUND, empty_city_streets: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.313 (city_streets_have_buildings) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_streets_have_buildings",
            not empty_city_streets,
            f"city street(s) with a stretch inside the walls with no building fronting it (a street network earns its length from the buildings it serves): {empty_city_streets}",
        )
    return _kept(locals(), ())


# ROADSIDE LAND on a larger city street is PRIME real estate: a paved through-street in a
# commercial/residential quarter must be LINED with buildings (houses, shops, civic halls)
# close to it, not left with a long bare margin. This is stricter than city_streets_have_buildings
# (which tolerates a building up to ~105px away): here a building must sit WITHIN ~58px of the
# street, the way storefronts and house-fronts actually line a road. Only the narrow gravel
# ALLEYS that thread the block interiors are exempt (those are the "small streets" that need no
# frontage), and so is the GOVERNMENT avenue - its frontage is the spaced ministry compounds,
# governed by city_ministries_front_a_street, not shops/houses. (The merchant avenue once read
# bare because its storefront frontage was silently blocked by the avenue's own corridor.)


def _seg_0563_314__line_blds(*, M: Any = _UNBOUND, gov: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.314 (line_blds) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        line_blds = M.get("buildings", []) + M.get("religious", []) + M.get("ministries", []) + M.get("flophouses", []) + ([gov] if gov else [])
    return _kept(locals(), ('line_blds',))


def _seg_0563_315__gov_pts(*, M: Any = _UNBOUND, gov: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.315 (gov_pts) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        gov_pts = M.get("ministries", []) + ([gov] if gov else [])
    return _kept(locals(), ('gov_pts',))


def _seg_0563_316__LINE_D(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.316 (LINE_D, LINE_RUN) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        LINE_D, LINE_RUN = 58, 140
    return _kept(locals(), ('LINE_D', 'LINE_RUN'))


def _seg_0563_317__bare_streets(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.317 (bare_streets) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        bare_streets = []  # type: ignore[var-annotated]
    return _kept(locals(), ('bare_streets',))


def _seg_0563_318___lg_open(
    *,
    LINE_D: Any = _UNBOUND,
    LINE_RUN: Any = _UNBOUND,
    M: Any = _UNBOUND,
    _lg_open: Any = _UNBOUND,
    a: Any = _UNBOUND,
    b: Any = _UNBOUND,
    bare_streets: Any = _UNBOUND,
    bl: Any = _UNBOUND,
    cg9: Any = _UNBOUND,
    gov_pts: Any = _UNBOUND,
    gp9: Any = _UNBOUND,
    i: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    j: Any = _UNBOUND,
    ki: Any = _UNBOUND,
    line_blds: Any = _UNBOUND,
    m: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    pts: Any = _UNBOUND,
    run: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    st: Any = _UNBOUND,
    steps: Any = _UNBOUND,
    t: Any = _UNBOUND,
    w: Any = _UNBOUND,
    worst: Any = _UNBOUND,
    x: Any = _UNBOUND,
    y: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.318 (_lg_open, a, b, bare_streets) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for st in M.get("town_streets", []):
            pts = st["pts"]
            if sum(1 for m in gov_pts if min(seg_dist(m["x"], m["y"], pts[i], pts[i + 1]) for i in range(len(pts) - 1)) < 70) >= 2:
                continue  # a government avenue - lined by ministry compounds
            worst = run = 0
            for ki in range(len(pts) - 1):
                a, b = pts[ki], pts[ki + 1]
                steps = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) // 20))
                for j in range(steps):
                    t = j / steps
                    x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                    _lg_open = any(
                        point_in_poly(x, y, gp9) or min(seg_dist(x, y, gp9[i9], gp9[(i9 + 1) % len(gp9)]) for i9 in range(len(gp9))) < 70
                        for gp9 in (cg9["poly"] for cg9 in M.get("commons", []) if cg9.get("poly"))
                    )  # open-ground frontage (commons/pasture): same exemption as empty_street_runs (021)
                    if not point_in_poly(x, y, w) or any((bl["x"] - x) ** 2 + (bl["y"] - y) ** 2 < LINE_D * LINE_D for bl in line_blds) or _lg_open:
                        run = 0
                    else:
                        run += 20
                        worst = max(worst, run)
            if worst > LINE_RUN:
                bare_streets.append(("main" if st.get("main") else f"@{(round(pts[0][0]), round(pts[0][1]))}", worst))
    return _kept(locals(), ('_lg_open', 'a', 'b', 'bare_streets', 'bl', 'cg9', 'gp9', 'i', 'i9', 'j', 'ki', 'm', 'pts', 'run', 'st', 'steps', 't', 'worst', 'x', 'y'))


def _seg_0563_319__city_larger_streets_lined(*, bare_streets: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.319 (city_larger_streets_lined) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_larger_streets_lined",
            not bare_streets,
            f"larger city street(s) with a long bare stretch of roadside land - a commercial/residential through-street should be "
            f"LINED with buildings close to it (only narrow alleys may run unlined): {bare_streets}",
        )
    return _kept(locals(), ())


def _seg_0563_320__road_1(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.320 (road) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        road = M.get("road") or []
    return _kept(locals(), ('road',))


def _seg_0563_321__city_imperial_road_through(
    *,
    EX0: Any = _UNBOUND,
    EX1: Any = _UNBOUND,
    EY0: Any = _UNBOUND,
    EY1: Any = _UNBOUND,
    M: Any = _UNBOUND,
    check: Any = _UNBOUND,
    dead: Any = _UNBOUND,
    e: Any = _UNBOUND,
    exits: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    offend: Any = _UNBOUND,
    p: Any = _UNBOUND,
    r: Any = _UNBOUND,
    rds: Any = _UNBOUND,
    road: Any = _UNBOUND,
    road_through: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.321 (city_imperial_road_through, city_roads_run_offmap) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        if meta.get("imperial_road", True):
            road_through = bool(road) and any(p[1] < EY0 for p in road) and any(p[1] > EY1 for p in road)
            check("city_imperial_road_through", road_through, "the Imperial road must run N-S through a walled city - off both the top and bottom edges, via the gates")
        else:
            # NO Imperial road (it passes miles away): the city still lives on through-traffic,
            # so its road net must leave the map in at least TWO directions (one polyline
            # bending through the city - off-map N, through the gates, off-map SE - counts
            # as two; a dead-end road serves nobody)
            rds = [r["pts"] for r in M.get("roads", [])] or ([road] if road else [])

            def offend(p: Pt) -> bool:
                return p[0] < EX0 or p[0] > EX1 or p[1] < EY0 or p[1] > EY1  # type: ignore[no-any-return]

            exits = sum(1 for r in rds for e in (r[0], r[-1]) if offend(e))
            dead = [(round(e[0]), round(e[1])) for r in rds for e in (r[0], r[-1]) if not offend(e)]
            check(
                "city_roads_run_offmap",
                exits >= 2 and not dead,
                f"{exits} off-map road end(s), dead end(s) at {dead[:3]} - a provincial city without an Imperial spine still connects to the wider world in >= 2 directions, and no road stops dead",
            )
    return _kept(locals(), ('dead', 'e', 'exits', 'offend', 'p', 'r', 'rds', 'road_through'))


def _seg_0563_322__city_no_inwall_farms(
    *, check: Any = _UNBOUND, f: Any = _UNBOUND, fields: Any = _UNBOUND, inwall: Any = _UNBOUND, inwall_fields: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.322 (city_no_inwall_farms) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and not meta.get("agricultural_district"):
        inwall_fields = [f["name"] for f in fields if inwall((f["bbox"][0] + f["bbox"][2]) / 2, (f["bbox"][1] + f["bbox"][3]) / 2)]
        check("city_no_inwall_farms", not inwall_fields, f"farms inside a city wall are uncharacteristic - set meta(agricultural_district=True) to allow them: {inwall_fields}")
    return _kept(locals(), ('f', 'inwall_fields'))


# INTRAMURAL groves OFF: a farm inside the wall carries NO windbreak grove - an in-wall plot is not
# an isolated farmstead (the urban fabric already breaks the wind) and sits on land too precious for
# a tree belt. So the in-wall agricultural district stays grove-free. WHY: settlements.md "Homestead groves".


def _seg_0563_323__no_groves_inside_walls(
    *, M: Any = _UNBOUND, check: Any = _UNBOUND, gv: Any = _UNBOUND, inwall: Any = _UNBOUND, inwall_groves: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.323 (no_groves_inside_walls) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and not meta.get("inwall_groves"):
        inwall_groves = sorted({(round(gv["of"][0]), round(gv["of"][1])) for gv in M.get("groves", []) if inwall(gv["of"][0], gv["of"][1])})
        check(
            "no_groves_inside_walls",
            not inwall_groves,
            f"farm(s) inside the city wall carry a windbreak grove {inwall_groves[:3]} - an intramural plot is "
            f"sheltered by the urban fabric and on land too precious for one (meta(inwall_groves=True) to allow)",
        )
    return _kept(locals(), ('gv', 'inwall_groves'))


def _seg_0563_324__moat_2(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.324 (moat) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        moat = M.get("moat")
    return _kept(locals(), ('moat',))


def _seg_0563_325__city_moat_feeder_matches_width(
    *,
    EX0: Any = _UNBOUND,
    EX1: Any = _UNBOUND,
    EY0: Any = _UNBOUND,
    EY1: Any = _UNBOUND,
    M: Any = _UNBOUND,
    bare: Any = _UNBOUND,
    check: Any = _UNBOUND,
    disp_a: Any = _UNBOUND,
    disp_b: Any = _UNBOUND,
    e: Any = _UNBOUND,
    e0: Any = _UNBOUND,
    e1: Any = _UNBOUND,
    feeders: Any = _UNBOUND,
    has_outfall: Any = _UNBOUND,
    i: Any = _UNBOUND,
    inlet_disp: Any = _UNBOUND,
    j: Any = _UNBOUND,
    j_arc: Any = _UNBOUND,
    loose: Any = _UNBOUND,
    mcx: Any = _UNBOUND,
    mcy: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    moat: Any = _UNBOUND,
    moat_is_fed: Any = _UNBOUND,
    mw: Any = _UNBOUND,
    narrow: Any = _UNBOUND,
    outlet_disp: Any = _UNBOUND,
    p: Any = _UNBOUND,
    q: Any = _UNBOUND,
    rcum: Any = _UNBOUND,
    rdist: Any = _UNBOUND,
    ri2: Any = _UNBOUND,
    rpts: Any = _UNBOUND,
    rv: Any = _UNBOUND,
    s: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    taps: Any = _UNBOUND,
    w: Any = _UNBOUND,
    wx: Any = _UNBOUND,
    wy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.325 (city_moat_fed_offmap, city_moat_feeder_matches_width, city_moat_has_outfall, city_moat_joins_river, city_moat_junction_angles, city_moat_surrounds_wall) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):  # noqa: SIM102
            if moat:
                rv = M.get("river")
                if rv:
                    # a river-bank city's moat is an OPEN arc: the river closes the water ring on its
                    # flank (Xiangyang/Pingyao pattern). Coverage: every wall vertex stands behind
                    # water - within ~72px of the moat arc OR ~200px of the river (the wharf strip
                    # sits between wall and bank, so the river runs further out than a dug moat) -
                    # and BOTH open moat ends must actually JOIN the river (inlet upstream, outlet
                    # downstream, the current flushing the ring).
                    # READ THE RIVER'S RECORDED FLOW rather than assuming its point order (GM
                    # 2026-07-25). Everything below - the arc-length ordering that decides which moat
                    # foot is the upstream INLET and which the downstream OUTLET, and the junction
                    # tilts keyed on it - takes increasing arc length to mean "downstream". That IS
                    # the upstream-first authoring convention, but hard-coding it means a river tagged
                    # flow="reverse" would be measured exactly backwards with nothing to catch it.
                    # Reverse the points when the record says so, and the convention becomes an
                    # assertion instead of an assumption.
                    rpts = rv["pts"][::-1] if rv.get("flow") == "reverse" else rv["pts"]

                    def rdist(q: Pt) -> float:
                        return min(seg_dist(q[0], q[1], rpts[i], rpts[i + 1]) for i in range(len(rpts) - 1))

                    bare = [(round(wx), round(wy)) for wx, wy in w if min(seg_dist(wx, wy, moat[i], moat[i + 1]) for i in range(len(moat) - 1)) > 72 and rdist((wx, wy)) > 200]
                    check(
                        "city_moat_surrounds_wall",
                        not bare,
                        f"wall stretch(es) behind neither the moat arc nor the river: {bare[:4]} - a river-bank city's dug moat covers the landward faces and the river covers its own flank",
                    )
                    loose = [(round(e[0]), round(e[1])) for e in (moat[0], moat[-1]) if rdist(e) > rv["w"] / 2 + 12]
                    if (
                        scale == "city"
                    ):  # CAPITAL-INVERTED (021): the capital moat is a complete RING with sluiced leats (the Chinese form, 020 research) - the leat checks validate its water, not the provincial open-arc model
                        check(
                            "city_moat_joins_river",
                            not loose,
                            f"open moat end(s) not joining the river: {loose} - the moat taps the river upstream and returns downstream (the current flushes it); extend the ends onto the river",
                        )
                    # JUNCTION ANGLES FOLLOW THE CURRENT (GM 2026-07-24 hydrology review; the old
                    # square tees were an rfoot-projection artifact, not a decision - settlements.md
                    # river-cities "junction angles follow the current"): the OUTLET (downstream
                    # junction) sweeps visibly downstream - junction angle is a primary confluence
                    # flow control, a square tee drives the exit jet across the river, and natural
                    # tributaries / drainage returns join pointing downstream - while the INLET
                    # stays square or tilts upstream, never smoothly flow-aligned (an offtake
                    # aligned with the current drinks the river's bedload and silts the ring;
                    # classical headworks kept intakes near-square under sluice control). Measured
                    # as each junction's arclength displacement off its adjacent kept vertex's
                    # square foot. CONVENTION: river pts run upstream-first (s.moat documents it).
                    if len(moat) >= 3:
                        rcum = [0.0]
                        for ri2 in range(len(rpts) - 1):
                            rcum.append(rcum[-1] + math.hypot(rpts[ri2 + 1][0] - rpts[ri2][0], rpts[ri2 + 1][1] - rpts[ri2][1]))

                        def j_arc(q: Any) -> float:
                            kj = min(range(len(rpts) - 1), key=lambda i7: seg_dist(q[0], q[1], rpts[i7], rpts[i7 + 1]))
                            fxj, fyj = seg_closest(q[0], q[1], rpts[kj], rpts[kj + 1])
                            return rcum[kj] + math.hypot(fxj - rpts[kj][0], fyj - rpts[kj][1])  # type: ignore[no-any-return]

                        disp_a = j_arc(moat[0]) - j_arc(moat[1])
                        disp_b = j_arc(moat[-1]) - j_arc(moat[-2])
                        inlet_disp, outlet_disp = (disp_a, disp_b) if j_arc(moat[0]) <= j_arc(moat[-1]) else (disp_b, disp_a)
                        if scale == "city":  # CAPITAL-INVERTED (021): ring-with-leats form; the leat junctions are validated by moat_junctions_swept_with_the_current
                            check(
                                "city_moat_junction_angles",
                                outlet_disp >= 12 and inlet_disp <= 4,
                                f"moat-river junction angles fight the current (inlet downstream-shift {inlet_disp:.0f}px, outlet {outlet_disp:.0f}px): "
                                f"the outlet must SWEEP DOWNSTREAM (>= 12px off the square foot - a square tee drives the exit jet across the river) "
                                f"and the inlet must stay square or tilt upstream (<= 4px - a flow-aligned intake drinks the river's bedload); "
                                f"tune river_inlet_tilt/river_outlet_tilt on s.moat()",
                            )
                else:
                    check("city_moat_surrounds_wall", len(w) >= 3 and all(point_in_poly(wx, wy, moat) for wx, wy in w), "the moat must encircle the wall (every wall point inside the moat ring)")
                moat_is_fed = any(
                    any(p[0] < EX0 or p[0] > EX1 or p[1] < EY0 or p[1] > EY1 for p in (s["poly"][0], s["poly"][-1])) and min(poly_dist(q[0], q[1], moat) for q in s["poly"]) <= 32
                    for s in M.get("streams", [])
                )
                if scale == "city":  # CAPITAL-INVERTED (021): the ring is fed by its sluiced river leat, validated by the leat battery
                    check("city_moat_fed_offmap", moat_is_fed, "the moat must be fed from an off-map water source (a stream from a map edge reaching the moat)")
                # the FEEDER must carry the moat's flow: a stream filling the moat is as WIDE as the moat
                # itself (a trickle cannot keep a full moat supplied) - so any stream reaching the moat must
                # match its width (within ~25%).
                mw = M.get("moat_width", 22)
                feeders = [s for s in M.get("streams", []) if min(poly_dist(q[0], q[1], moat) for q in s["poly"]) <= 32]
                narrow = [s.get("w", 9) for s in feeders if s.get("w", 9) < 0.75 * mw]
                check(
                    "city_moat_feeder_matches_width",
                    not narrow,
                    f"the stream feeding the moat is too narrow ({narrow} px vs the {mw}px moat) - a moat's water source "
                    f"must be about as wide as the moat it supplies (pass s.stream(..., width=<moat width>))",
                )
                # A FED CLOSED (non-river) MOAT MUST ALSO DRAIN. A moat with a live feeder but no outfall
                # would overflow: conservation of flow - a perennial stream cannot be held in a wet-rice-
                # climate moat as a terminal pond (evaporation + seepage cannot absorb a live stream; that
                # balance belongs to an arid, spring/rain-fed moat). The historical norm is a FLOW-THROUGH
                # ring - feeder in on the high side, outfall off the LOW side to a lower watercourse, the
                # current flushing corner-to-corner (Beijing's gated water-passes; the Forbidden City's
                # NW-in / SE-out moat). The river-moat case is already covered by city_moat_joins_river
                # (inlet upstream, outlet downstream), so this guards the closed-moat case. See settlements.md.
                if not rv and moat_is_fed:
                    mcx, mcy = sum(p[0] for p in moat) / len(moat), sum(p[1] for p in moat) / len(moat)
                    taps = []  # the moat-rim end of each stream that reaches the moat AND runs off-map: feeder + any outfall
                    for s in M.get("streams", []):
                        e0, e1 = s["poly"][0], s["poly"][-1]
                        if any(e[0] < EX0 or e[0] > EX1 or e[1] < EY0 or e[1] > EY1 for e in (e0, e1)) and min(poly_dist(q[0], q[1], moat) for q in (e0, e1)) <= 32:
                            taps.append(min((e0, e1), key=lambda e: poly_dist(e[0], e[1], moat)))
                    # feeder + outfall must attach on OPPOSITE faces (centroid-radials pointing apart, dot < 0)
                    # so the ring genuinely flushes rather than two inlets crowding one arc
                    has_outfall = any((taps[i][0] - mcx) * (taps[j][0] - mcx) + (taps[i][1] - mcy) * (taps[j][1] - mcy) < 0 for i in range(len(taps)) for j in range(i + 1, len(taps)))
                    check(
                        "city_moat_has_outfall",
                        has_outfall,
                        "a fed closed city moat has no outfall - a moat with a live feeder must also DRAIN "
                        "(conservation of flow: the surplus overflows if it cannot leave), so an outfall stream "
                        "leaves the LOW rim and runs off-map opposite the feeder to flush the ring; add s.stream(moat rim -> off-map edge)",
                    )
    return _kept(
        locals(),
        (
            'bare',
            'disp_a',
            'disp_b',
            'e',
            'e0',
            'e1',
            'feeders',
            'has_outfall',
            'i',
            'inlet_disp',
            'j',
            'j_arc',
            'loose',
            'mcx',
            'mcy',
            'moat_is_fed',
            'mw',
            'narrow',
            'outlet_disp',
            'p',
            'q',
            'rcum',
            'rdist',
            'ri2',
            'rpts',
            'rv',
            's',
            'taps',
            'wx',
            'wy',
        ),
    )


# RIVER-CITY WATERWORKS (a cargo canal + wharf; only where they are drawn):


def _seg_0563_326__river_c(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.326 (river_c) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        river_c: Any = M.get("river")  # type: ignore[no-redef,unused-ignore]
    return _kept(locals(), ('river_c',))


def _seg_0563_327__canals_c(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.327 (canals_c) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        canals_c = M.get("canals", [])
    return _kept(locals(), ('canals_c',))


def _seg_0563_328__docks_c(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.328 (docks_c) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        docks_c = M.get("docks", [])
    return _kept(locals(), ('docks_c',))


# (1) THE CANAL CONNECTS THE DOCK TO THE WATER, like a street reaching the road: one end
# taps the river OR hands off to the moat (the Suzhou shared-mouth pattern - the city's
# canals communicate with the MOAT, and the moat's own downstream river junction is the
# navigation entrance), the other feeds the in-city dock basin - a canal that stops short
# of the dock is a ditch to nowhere (GM, 2026-07: Nagahara's canal left a visible gap to
# the dock). "Reaches" = the end's bed physically meets the target (within the target's
# half-extent + the canal half-width + a small tolerance).


def _seg_0563_329__city_canal_reaches_dock(
    *,
    M: Any = _UNBOUND,
    _end_near_dock: Any = _UNBOUND,
    _end_near_moat: Any = _UNBOUND,
    _end_near_river: Any = _UNBOUND,
    c: Any = _UNBOUND,
    canal_second_mouths: Any = _UNBOUND,
    canals_c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    chw: Any = _UNBOUND,
    d: Any = _UNBOUND,
    docks_c: Any = _UNBOUND,
    e: Any = _UNBOUND,
    ends: Any = _UNBOUND,
    i: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    moat_for_canal: Any = _UNBOUND,
    mw_for_canal: Any = _UNBOUND,
    river_c: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    unreached: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.329 (city_canal_reaches_dock, city_canal_shares_moat_mouth) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and canals_c:
        moat_for_canal = M.get("moat") or []
        mw_for_canal = M.get("moat_width", 22)

        def _end_near_river(e: Pt) -> bool:
            return bool(river_c) and min(seg_dist(e[0], e[1], river_c["pts"][i], river_c["pts"][i + 1]) for i in range(len(river_c["pts"]) - 1)) <= river_c["w"] / 2 + 14

        def _end_near_moat(e: Pt, chw: float) -> bool:
            # the handoff confluence: the canal end sits ON the moat's stroke (bed meets bed)
            return len(moat_for_canal) >= 2 and poly_dist(e[0], e[1], moat_for_canal) <= mw_for_canal / 2 + chw + 4

        def _end_near_dock(e: Pt, chw: float) -> bool:
            # the canal MOUTH opens into the basin: the endpoint sits at the quay edge or
            # inside it (a visible gap to the dock = not connected), so no slack beyond ~3px
            return any(abs(e[0] - d["x"]) <= d["w"] / 2 + 3 and abs(e[1] - d["y"]) <= d["h"] / 2 + 3 for d in docks_c)

        unreached = []
        for c in canals_c:
            chw = c.get("w", 12) / 2
            ends = (c["poly"][0], c["poly"][-1])
            if not (any(_end_near_river(e) or _end_near_moat(e, chw) for e in ends) and (not docks_c or any(_end_near_dock(e, chw) for e in ends))):
                unreached.append([round(c["poly"][0][0]), round(c["poly"][0][1])])
        check(
            "city_canal_reaches_dock",
            not unreached,
            f"cargo canal(s) not connecting the water to the dock basin: {unreached[:3]} - one end taps the "
            f"river or hands off to the moat (at the water gate), the other must feed the in-city dock "
            f"(extend it to the quay, like a street reaching the road)",
        )
        # (1b) ONE MOUTH ON THE RIVER, NOT TWO (GM 2026-07-23, Nagahara's water-gate corner):
        # where a moat is drawn, a canal must not open its OWN river mouth inside the moat's
        # stroke corridor - Nagahara's canal tapped the river 36 real ft beside the moat's
        # downstream junction and rode collinearly inside the moat arm across the whole bank
        # strip, a smeared doubled channel with a sliver fork at the mouth. Historically the
        # mouths MERGE: the canal hands off to the moat and the moat's junction is the single
        # navigation entrance (see settlements.md river-cities, "one mouth on the river").
        # A canal mouth on open bank AWAY from the moat remains legitimate (real cities had
        # water gates on the river face itself); only the near-duplicate mouth is the defect.
        canal_second_mouths = []
        for c in canals_c:
            chw = c.get("w", 12) / 2
            for e in (c["poly"][0], c["poly"][-1]):
                if _end_near_river(e) and len(moat_for_canal) >= 2 and poly_dist(e[0], e[1], moat_for_canal) <= mw_for_canal / 2 + chw + 8:
                    canal_second_mouths.append([round(e[0]), round(e[1])])
        check(
            "city_canal_shares_moat_mouth",
            not canal_second_mouths,
            f"cargo canal end(s) opening a second river mouth alongside the moat's junction: {canal_second_mouths[:3]} - "
            f"the canal and the moat share ONE mouth (the Suzhou pattern: end the canal ON the moat and let the "
            f"moat's downstream junction be the navigation entrance)",
        )
    return _kept(locals(), ('_end_near_dock', '_end_near_moat', '_end_near_river', 'c', 'canal_second_mouths', 'chw', 'e', 'ends', 'moat_for_canal', 'mw_for_canal', 'unreached'))


# (2) THE WHARF JETTIES REACH THE BANK: a jetty is a finger running out from the river's
# near bank into the water - its landward end must TOUCH the bank, not float mid-stream
# (GM, 2026-07: Nagahara's jetties floated in the middle of the river). The near bank is
# the river centerline offset by half its width toward the city; a jetty's nearest end
# must sit within ~14px of it.


def _seg_0563_330__jetties_c(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.330 (jetties_c) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        jetties_c = M.get("jetties", [])
    return _kept(locals(), ('jetties_c',))


def _seg_0563_331__city_wharf_jetties_on_bank(
    *,
    EX0: Any = _UNBOUND,
    EY0: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cityward_dist: Any = _UNBOUND,
    cx_r: Any = _UNBOUND,
    cy_r: Any = _UNBOUND,
    d: Any = _UNBOUND,
    dc: Any = _UNBOUND,
    e: Any = _UNBOUND,
    floats: Any = _UNBOUND,
    fx: Any = _UNBOUND,
    fy: Any = _UNBOUND,
    i: Any = _UNBOUND,
    j: Any = _UNBOUND,
    jends: Any = _UNBOUND,
    jetties_c: Any = _UNBOUND,
    k: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    p: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    rhw: Any = _UNBOUND,
    river_c: Any = _UNBOUND,
    root: Any = _UNBOUND,
    rp: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    tip: Any = _UNBOUND,
    w: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.331 (city_wharf_jetties_on_bank) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and jetties_c and river_c:
        rp = river_c["pts"]
        rhw = river_c["w"] / 2
        cx_r = sum(p[0] for p in w) / len(w) if len(w) >= 3 else EX0
        cy_r = sum(p[1] for p in w) / len(w) if len(w) >= 3 else EY0
        floats = []
        for j in jetties_c:
            jends = [(j["x"], j["y"]), (j["x"] + math.cos(math.radians(j["rot"])) * j["len"], j["y"] + math.sin(math.radians(j["rot"])) * j["len"])]

            # a jetty runs out from the CITYWARD bank into the water. At least one end must
            # sit on that near bank: within ~14px of the bank line (|dist-to-centerline - rhw|
            # small) AND on the city's side of the centerline (dot of (end - foot) with the
            # direction to the wall centroid is positive).
            def cityward_dist(px: float, py: float) -> tuple[float, bool]:
                # (distance to the river centerline, is-it-on-the-city-side-of-the-centerline)
                k = min(range(len(rp) - 1), key=lambda i: seg_dist(px, py, rp[i], rp[i + 1]))
                fx, fy = seg_closest(px, py, rp[k], rp[k + 1])
                d = math.hypot(px - fx, py - fy)
                cityward = (px - fx) * (cx_r - fx) + (py - fy) * (cy_r - fy) > 0
                return d, cityward

            # a jetty is a FINGER: its ROOT sits at the near bank or just onto land (cityward,
            # >= rhw-6 from the centerline - so the plank visibly connects to the shore, not
            # floating a stride out in the water), and its TIP runs INTO the near-half water
            # (cityward, <= rhw - it neither floats mid-stream nor spans past the far bank).
            root = any((lambda dc: dc[1] and dc[0] >= rhw - 6)(cityward_dist(*e)) for e in jends)
            tip = any((lambda dc: dc[1] and dc[0] <= rhw)(cityward_dist(*e)) for e in jends)
            if not (root and tip):
                floats.append([round(jends[0][0]), round(jends[0][1])])
        check(
            "city_wharf_jetties_on_bank",
            not floats,
            f"wharf jetties floating off the bank: {floats[:3]} - a jetty's landward end must touch the river's near bank, running out into the water from there, not float mid-stream",
        )
    return _kept(locals(), ('cityward_dist', 'cx_r', 'cy_r', 'e', 'floats', 'j', 'jends', 'p', 'rhw', 'root', 'rp', 'tip'))


# (3) THE LOG BOOM IS A SHORE-FAST PEN, NOT STICKS IN THE STREAM (GM 2026-08-02, "it
# just looks like a bunch of logs in the middle of the river"; the research is in
# research/urban-features.md "The log boom"). A boom is a floating fence - anchored to
# nothing it holds nothing. Attested booms anchor to the bank and run ALONG a navigated
# river, the pen between chain and shore (Susquehanna: seven miles along one side;
# St. Croix: log channels beside a navigation channel kept clear by statute); only a
# loose-log CATCH boom on an unnavigated reach ever spans the water (the Kiso tsunaba
# at the gorge mouth), never a port's holding pen. GAP-VERDICT family: both rules below
# measure the pen's DERIVED CORNERS (x/y/rot/len/pen_w, the same local frame the glyph
# draws - bank on local +y) against the river's stroked centerline; a center measure
# would condemn the good bank-hugging pen and pass the mid-stream chain (see the test
# pair). pen_w defaults to the ~14px the pre-2026-08 chain glyph drew.


def _seg_0563_332__booms_c(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.332 (booms_c) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        booms_c = M.get("log_booms", [])
    return _kept(locals(), ('booms_c',))


def _seg_0563_333__log_boom_moored_to_the_bank(
    *,
    M: Any = _UNBOUND,
    adrift_lb: Any = _UNBOUND,
    bmx: Any = _UNBOUND,
    bmy: Any = _UNBOUND,
    bo: Any = _UNBOUND,
    bod_: Any = _UNBOUND,
    boom_off: Any = _UNBOUND,
    booms_c: Any = _UNBOUND,
    box_: Any = _UNBOUND,
    boy_: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cthb: Any = _UNBOUND,
    damming_lb: Any = _UNBOUND,
    fx: Any = _UNBOUND,
    fy: Any = _UNBOUND,
    hlb: Any = _UNBOUND,
    hpb: Any = _UNBOUND,
    i: Any = _UNBOUND,
    k: Any = _UNBOUND,
    lx: Any = _UNBOUND,
    ly: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    moored_lb: Any = _UNBOUND,
    nxb: Any = _UNBOUND,
    nyb: Any = _UNBOUND,
    px_: Any = _UNBOUND,
    py_: Any = _UNBOUND,
    qd_lb: Any = _UNBOUND,
    qdx_lb: Any = _UNBOUND,
    qdy_lb: Any = _UNBOUND,
    quadb: Any = _UNBOUND,
    qx_lb: Any = _UNBOUND,
    qy_lb: Any = _UNBOUND,
    rhwb: Any = _UNBOUND,
    river_c: Any = _UNBOUND,
    rpb: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    sthb: Any = _UNBOUND,
    stray_b: Any = _UNBOUND,
    thb: Any = _UNBOUND,
    yards_b: Any = _UNBOUND,
    yd: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.333 (log_boom_leaves_the_fairway, log_boom_moored_to_the_bank, log_boom_serves_the_lumber_yard) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):  # noqa: SIM102
            if booms_c and river_c:
                rpb = river_c["pts"]
                rhwb = river_c["w"] / 2

                def boom_off(px_: float, py_: float) -> tuple[float, float, float]:
                    # a corner's offset from the river centerline: (dx, dy, distance)
                    k = min(range(len(rpb) - 1), key=lambda i: seg_dist(px_, py_, rpb[i], rpb[i + 1]))
                    fx, fy = seg_closest(px_, py_, rpb[k], rpb[k + 1])
                    return px_ - fx, py_ - fy, math.hypot(px_ - fx, py_ - fy)

                adrift_lb, damming_lb = [], []
                for bo in booms_c:
                    thb = math.radians(float(bo.get("rot", 0.0)))
                    cthb, sthb = math.cos(thb), math.sin(thb)
                    hlb, hpb = float(bo["len"]) / 2, float(bo.get("pen_w", 14.0)) / 2
                    quadb = [(bo["x"] + lx * cthb - ly * sthb, bo["y"] + lx * sthb + ly * cthb) for lx, ly in ((-hlb, hpb), (hlb, hpb), (hlb, -hpb), (-hlb, -hpb))]  # bank-side pair first
                    # the shoreward normal, from the bank-side edge's midpoint
                    bmx, bmy = (quadb[0][0] + quadb[1][0]) / 2, (quadb[0][1] + quadb[1][1]) / 2
                    box_, boy_, bod_ = boom_off(bmx, bmy)
                    nxb, nyb = (box_ / bod_, boy_ / bod_) if bod_ > 0.5 else (0.0, 0.0)
                    # moored_lb: both bank corners ride ON the bank line (centerline + half-width),
                    # shoreward, within ~5px - the pen holds timber between chain and bank
                    moored_lb = bod_ > 0.5
                    for qx_lb, qy_lb in quadb[:2]:
                        qdx_lb, qdy_lb, qd_lb = boom_off(qx_lb, qy_lb)
                        if abs(qd_lb - rhwb) > 5.0 or qdx_lb * nxb + qdy_lb * nyb <= 0:
                            moored_lb = False
                    if not moored_lb:
                        adrift_lb.append([round(bo["x"]), round(bo["y"])])
                    # the fairway is judged even for an adrift boom - the two defects are
                    # independent (the pre-fix Minami chain was both), and the shoreward normal
                    # still points at the boom's own nearest side
                    # fairway: no corner reaches deeper than 40% of the channel off its own bank,
                    # so a clear majority of the width stays open to the wharf traffic
                    for qx_lb, qy_lb in quadb:
                        qdx_lb, qdy_lb, qd_lb = boom_off(qx_lb, qy_lb)
                        if rhwb - (qdx_lb * nxb + qdy_lb * nyb) > 0.8 * rhwb:
                            damming_lb.append([round(bo["x"]), round(bo["y"])])
                            break
                check(
                    "log_boom_moored_to_the_bank",
                    not adrift_lb,
                    f"log boom(s) adrift_lb off the bank: {adrift_lb[:3]} - a boom is a floating fence anchored to fixed ground; its bank edge (local +y) must ride ON the shore line so the pen holds timber between chain and bank, not a chain loose in mid-stream",
                )
                check(
                    "log_boom_leaves_the_fairway",
                    not damming_lb,
                    f"log boom(s) crowding the channel: {damming_lb[:3]} - a holding pen takes at most ~40% of the river's width off its own bank; booms were barred from obstructing navigation, and the full-span catch boom belongs on an unnavigated reach upstream, not at the port",
                )
                # association family (center, deliberately - the ~120px block-scale tolerance
                # dwarfs both footprints): the pen is the timber trade's waterside holding
                # ground, so it rides off the lumber yard's own frontage
                yards_b = M.get("lumber_yards", [])
                if yards_b:
                    stray_b = [[round(bo["x"]), round(bo["y"])] for bo in booms_c if min(math.hypot(bo["x"] - yd["x"], bo["y"] - yd["y"]) for yd in yards_b) > 120.0]
                    check(
                        "log_boom_serves_the_lumber_yard",
                        not stray_b,
                        f"log boom(s) far from any lumber yard: {stray_b[:3]} - boom and zaimokuya are one works; moor the pen off the yard's own bank frontage",
                    )
    return _kept(
        locals(),
        (
            'adrift_lb',
            'bmx',
            'bmy',
            'bo',
            'bod_',
            'boom_off',
            'box_',
            'boy_',
            'cthb',
            'damming_lb',
            'hlb',
            'hpb',
            'lx',
            'ly',
            'moored_lb',
            'nxb',
            'nyb',
            'qd_lb',
            'qdx_lb',
            'qdy_lb',
            'quadb',
            'qx_lb',
            'qy_lb',
            'rhwb',
            'rpb',
            'sthb',
            'stray_b',
            'thb',
            'yards_b',
            'yd',
        ),
    )
