"""Gate segments (bridges and gate roads; keys 0334-0359) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from l7r.diagram.settlement import bridge_carried_ways, bridge_crossed_waters, machi_mouths

from .common_01_geometry import point_in_poly, seg_closest, seg_dist, seg_intersect, segments_cross
from .common_03_capacity import _UNBOUND, DWELLING_KINDS, _kept, _poly_area

# WHERE A WAY CROSSES A WATERCOURSE, a bridge must carry it over - a way does not simply run
# through open water. Crossings are road / RING ROAD / street / lane segments intersecting a
# stream, an irrigation channel, a field ditch, the navigable cargo canal, or the city moat (a
# walled city's approach road crosses the moat at each gate). Every such crossing must have a
# recorded bridge near the intersection point. (A way merely running ALONGSIDE water, never
# intersecting it, needs no bridge - only true crossings count.)
#
# The way and water sets here MIRROR settlement.bridges(), which draws from the same two lists -
# they must stay in step or the engine places decks the gate does not ask for, or (worse) the
# gate stays silent about a crossing the engine never saw. The ring road and the cargo canal were
# missing from BOTH until 2026-07-27, which is why Minami's and Nagahara's canal crossings were
# hand-placed and both went crooked (see bridges_align_with_their_way, below).
#
# An UNDRAWN channel (`drawn: False`, from topo_channel) is a buried conduit recorded for water
# topology only - there is no seam on the ground, so a way crossing its line crosses nothing and
# needs no deck. Tango's ring road runs over three of them.


def _seg_0334__bridges(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 334 (bridges) - body verbatim from the legacy gate() (feature 022)."""
    bridges = M.get("bridges", [])
    return _kept(locals(), ('bridges',))


# ONE SOURCE, shared with settlement.bridges() (feature 020). These sets used to be built
# separately here and in the generator, and both omitted M["roads"], the river and a castle's
# own moat - so the two agreed perfectly and were both wrong, leaving four of six crossings on
# the first capital unbridged with a green gate. "Placement and its check read the SAME source"
# guarantees they cannot DISAGREE; it does not make either correct, so they now read one
# function rather than two lists that happen to match.


def _seg_0335____1(*, M: Any = _UNBOUND, w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 335 (_, w, waters_b) - body verbatim from the legacy gate() (feature 022)."""
    waters_b = [w for w, _ in bridge_crossed_waters(M)]
    return _kept(locals(), ('_', 'w', 'waters_b'))


def _seg_0336____2(*, M: Any = _UNBOUND, c: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 336 (_, c, carried_b) - body verbatim from the legacy gate() (feature 022)."""
    carried_b = [c for c, _ in bridge_carried_ways(M)]
    return _kept(locals(), ('_', 'c', 'carried_b'))


def _seg_0337__xings_b() -> dict[str, Any]:
    """Gate segment 337 (xings_b) - body verbatim from the legacy gate() (feature 022)."""
    xings_b = []  # type: ignore[var-annotated]  # (point, way heading in degrees) for every way x water crossing on the map
    return _kept(locals(), ('xings_b',))


def _seg_0338__i_3(
    *,
    carried_b: Any = _UNBOUND,
    i: Any = _UNBOUND,
    j: Any = _UNBOUND,
    p: Any = _UNBOUND,
    ra: Any = _UNBOUND,
    rb: Any = _UNBOUND,
    rpts: Any = _UNBOUND,
    waters_b: Any = _UNBOUND,
    wpts: Any = _UNBOUND,
    xings_b: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 338 (i, j, p, ra) - body verbatim from the legacy gate() (feature 022)."""
    for rpts in carried_b:
        for i in range(len(rpts) - 1):
            ra, rb = rpts[i], rpts[i + 1]
            for wpts in waters_b:
                for j in range(len(wpts) - 1):
                    if segments_cross(ra, rb, wpts[j], wpts[j + 1]):
                        p = seg_intersect(ra, rb, wpts[j], wpts[j + 1])
                        if p is not None:
                            xings_b.append((p, math.degrees(math.atan2(rb[1] - ra[1], rb[0] - ra[0]))))
    return _kept(locals(), ('i', 'j', 'p', 'ra', 'rb', 'rpts', 'wpts', 'xings_b'))


def _seg_0339____3(*, b: Any = _UNBOUND, bridges: Any = _UNBOUND, p: Any = _UNBOUND, xings_b: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 339 (_, b, p, unbridged) - body verbatim from the legacy gate() (feature 022)."""
    unbridged = [(round(p[0]), round(p[1])) for p, _ in xings_b if not any(math.hypot(b["x"] - p[0], b["y"] - p[1]) <= 40 for b in bridges)]
    return _kept(locals(), ('_', 'b', 'p', 'unbridged'))


def _seg_0340__roads_bridge_water(*, check: Any = _UNBOUND, unbridged: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 340 (roads_bridge_water) - body verbatim from the legacy gate() (feature 022)."""
    check("roads_bridge_water", not unbridged, f"a road/street crosses water with no bridge at {sorted(set(unbridged))} - carry it over (call s.bridges() after laying all roads and water)")
    return _kept(locals(), ())


# A BRIDGE MUST LIE ON ITS CROSSING AND RUN ALONG THE WAY IT CARRIES (GM 2026-07-27, Minami's
# cargo-basin bridge). The rule above only asks that SOME deck be within 40px of each crossing,
# which a deck sitting beside the crossing at a wrong angle satisfies - and the eye reads that as
# the road running straight through the water with a crooked plank next to it, which is exactly
# what the GM saw. So each carried deck is paired with the nearest crossing and must sit ON it
# (within BRIDGE_SEAT_TOL) and share its bearing (within BRIDGE_ROT_TOL, mod 180 - a deck has no
# forward direction). EVIDENCE for the tolerances: every deck s.bridges() solves lands 0.0-1.0 px
# and 0.0-1.0 deg off its crossing (rounding only), while the two hand-placed canal decks were
# 17px/39deg (Minami) and 15px/24deg (Nagahara) off - two orders of magnitude adrift, so a tight
# tolerance separates them cleanly with room to spare.
#
# A deck with NO crossing under it at all fails the same check: it carries nothing, so either the
# way or the watercourse it was drawn for is not in the manifest.
#
# STANDALONE plank footbridges (`foot`) are exempt: no way carries them, they cross the ditch
# PERPENDICULAR by construction, and their own rules are long_ditches_have_a_footbridge /
# footbridges_reach_useful_ground.


def _seg_0341__BRIDGE_ROT_TOL() -> dict[str, Any]:
    """Gate segment 341 (BRIDGE_ROT_TOL, BRIDGE_SEAT_TOL) - body verbatim from the legacy gate() (feature 022)."""
    BRIDGE_SEAT_TOL, BRIDGE_ROT_TOL = 8.0, 8.0
    return _kept(locals(), ('BRIDGE_ROT_TOL', 'BRIDGE_SEAT_TOL'))


def _seg_0342__crooked() -> dict[str, Any]:
    """Gate segment 342 (crooked) - body verbatim from the legacy gate() (feature 022)."""
    crooked = []  # type: ignore[var-annotated]
    return _kept(locals(), ('crooked',))


def _seg_0343__b(
    *,
    BRIDGE_ROT_TOL: Any = _UNBOUND,
    BRIDGE_SEAT_TOL: Any = _UNBOUND,
    b: Any = _UNBOUND,
    bridges: Any = _UNBOUND,
    crooked: Any = _UNBOUND,
    deck_skew: Any = _UNBOUND,
    heading: Any = _UNBOUND,
    near_x: Any = _UNBOUND,
    px_: Any = _UNBOUND,
    py_: Any = _UNBOUND,
    seat_off: Any = _UNBOUND,
    xings_b: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 343 (b, crooked, deck_skew, heading) - body verbatim from the legacy gate() (feature 022)."""
    for b in bridges:
        if b.get("foot"):
            continue
        near_x = min(xings_b, key=lambda pv: math.hypot(pv[0][0] - b["x"], pv[0][1] - b["y"]), default=None)
        if near_x is None:
            crooked.append(f"({round(b['x'])},{round(b['y'])}) carries no way over any water")
            continue
        (px_, py_), heading = near_x
        seat_off = math.hypot(px_ - b["x"], py_ - b["y"])
        deck_skew = abs((b.get("rot", 0.0) - heading + 90) % 180 - 90)
        if seat_off > BRIDGE_SEAT_TOL:
            crooked.append(f"({round(b['x'])},{round(b['y'])}) sits {seat_off:.0f}px off its crossing at ({round(px_)},{round(py_)})")
        elif deck_skew > BRIDGE_ROT_TOL:
            crooked.append(f"({round(b['x'])},{round(b['y'])}) is rot {b.get('rot', 0.0):.0f} but its way bears {heading:.0f} ({deck_skew:.0f} deg askew)")
    return _kept(locals(), ('b', 'crooked', 'deck_skew', 'heading', 'near_x', 'px_', 'py_', 'seat_off'))


def _seg_0344__bridges_align_with_their_way(*, check: Any = _UNBOUND, crooked: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 344 (bridges_align_with_their_way) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "bridges_align_with_their_way",
        not crooked,
        f"{len(crooked)} bridge(s) not seated on the crossing they carry: {crooked[:3]} - a deck lies ON the intersection and runs ALONG the way, or the way runs through the water beside it; solve it with s.bridges() instead of hand-placing coordinates",
    )
    return _kept(locals(), ())


# A WATERCOURSE PIERCES A RAMPART ONLY AT A WATER GATE (GM 2026-08-09). Nagahara's cargo
# canal anchored its east end to a moat vertex BY INDEX; a past ring re-derivation moved the
# vertex, the approach leg slid 40px off the shuimen gap, and the canal shipped running
# UNDER the wall - placement and the wall's gap had no shared source and nothing compared
# the crossing to the gate. The doctrine was already prose (inwall_drain_outfall: "never
# draw a ditch running through the city wall"); this makes it a check for every DRAWN
# canal/channel/stream against a closed rampart. Buried conduits (drawn=False) pierce
# nothing; the moat is the ring outside and never crosses.


def _seg_0345___wg_wall(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 345 (_wg_wall) - body verbatim from the legacy gate() (feature 022)."""
    _wg_wall = M.get("wall") or []
    return _kept(locals(), ('_wg_wall',))


def _seg_0346__watercourse_crosses_wall_at_water_gate(
    *,
    M: Any = _UNBOUND,
    _wg_bad: Any = _UNBOUND,
    _wg_courses: Any = _UNBOUND,
    _wg_gates: Any = _UNBOUND,
    _wg_i: Any = _UNBOUND,
    _wg_j: Any = _UNBOUND,
    _wg_p: Any = _UNBOUND,
    _wg_ring: Any = _UNBOUND,
    _wg_wall: Any = _UNBOUND,
    _wg_x: Any = _UNBOUND,
    c3: Any = _UNBOUND,
    check: Any = _UNBOUND,
    g3: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 346 (watercourse_crosses_wall_at_water_gate) - body verbatim from the legacy gate() (feature 022)."""
    if len(_wg_wall) >= 3:
        _wg_gates = M.get("water_gates", [])
        _wg_bad = []
        _wg_ring = list(_wg_wall) + [_wg_wall[0]]
        _wg_courses = [c3["poly"] for c3 in M.get("canals", []) if c3.get("drawn", True)]
        _wg_courses += [c3["poly"] for c3 in M.get("channels", []) if c3.get("drawn", True)]
        _wg_courses += [c3["poly"] for c3 in M.get("streams", [])]
        for _wg_p in _wg_courses:
            for _wg_i in range(len(_wg_p) - 1):
                for _wg_j in range(len(_wg_ring) - 1):
                    if not segments_cross(_wg_p[_wg_i], _wg_p[_wg_i + 1], _wg_ring[_wg_j], _wg_ring[_wg_j + 1]):
                        continue  # seg_intersect alone is the INFINITE-line answer - the guard bounds it
                    _wg_x = seg_intersect(_wg_p[_wg_i], _wg_p[_wg_i + 1], _wg_ring[_wg_j], _wg_ring[_wg_j + 1])
                    if _wg_x is None:
                        continue  # pragma: no cover - crossing segments are never parallel; defensive only
                    if min((math.hypot(_wg_x[0] - g3["x"], _wg_x[1] - g3["y"]) for g3 in _wg_gates), default=1e9) > 16:
                        _wg_bad.append((round(_wg_x[0]), round(_wg_x[1])))
        check(
            "watercourse_crosses_wall_at_water_gate",
            not _wg_bad,
            f"watercourse(s) running UNDER the rampart away from any water gate (x, y): {sorted(set(_wg_bad))[:4]} - water passes a wall only through its shuimen gap "
            f"(s.water_gate + city_wall(water_gates=[...])); route the crossing leg through the gate along the wall's normal",
        )
    return _kept(locals(), ('_wg_bad', '_wg_courses', '_wg_gates', '_wg_i', '_wg_j', '_wg_p', '_wg_ring', '_wg_x', 'c3', 'g3'))


# ---- feature 021: the capital housing layer -------------------------------------------
# FABRIC DECLARES ITS DISTRICTS (T003): once dwellings stand, the capital records which
# named district each pack filled - the districts are the rank-gradient check's ground
# truth and the reader's map of intent. The bare 020 state (no fabric) stays legal, so
# this is a declaration-existence rule on the HOUSED capital only ("a check that never
# RUNS looks exactly like a check that passes").


def _seg_0347__capital_districts_declared(*, M: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 347 (capital_districts_declared) - body verbatim from the legacy gate() (feature 022)."""
    if meta.get("scale") == "capital" and (M.get("houses") or M.get("terraces")):
        check(
            "capital_districts_declared",
            bool(M.get("districts")),
            "housing stands but no districts are declared - s.district(name, kind, poly, rank_band=...) per pack region; capital_rank_gradient reads them",
        )
    return _kept(locals(), ())


# RANK GRADES WITH DISTANCE FROM THE CASTLE (T004; research 021 item 1): the jokamachi
# law - senior walled yashiki nearest the castle, detached houses next, retainer
# terraces at the band edge. Footprint family: CLASSIFICATION (members assigned by
# center to the band district containing them) + an ordering on band MEAN distances;
# 12px slack absorbs band-boundary geometry. Bands without members are skipped, so a
# mid-build map stays legal.


def _seg_0348__capital_rank_gradient(
    *,
    M: Any = _UNBOUND,
    cg_a: Any = _UNBOUND,
    cg_b: Any = _UNBOUND,
    cg_bad: Any = _UNBOUND,
    cg_bands: Any = _UNBOUND,
    cg_c: Any = _UNBOUND,
    cg_cx: Any = _UNBOUND,
    cg_cy: Any = _UNBOUND,
    cg_d: Any = _UNBOUND,
    cg_i: Any = _UNBOUND,
    cg_j: Any = _UNBOUND,
    cg_ma: Any = _UNBOUND,
    cg_mc: Any = _UNBOUND,
    cg_members: Any = _UNBOUND,
    cg_order: Any = _UNBOUND,
    cg_x: Any = _UNBOUND,
    cg_y: Any = _UNBOUND,
    check: Any = _UNBOUND,
    h4: Any = _UNBOUND,
    m: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    t4: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 348 (capital_rank_gradient) - body verbatim from the legacy gate() (feature 022)."""
    if meta.get("scale") == "capital" and M.get("castles") and M.get("districts"):
        cg_cx, cg_cy = M["castles"][0]["x"], M["castles"][0]["y"]
        cg_members = [(m["x"], m["y"]) for m in M.get("manors", [])] + [(h4["x"], h4["y"]) for h4 in M.get("houses", [])] + [(t4["x"], t4["y"]) for t4 in M.get("terraces", [])]
        cg_bands: dict[str, list[float]] = {}  # type: ignore[no-redef]
        for cg_d in M["districts"]:
            cg_b = cg_d.get("rank_band")
            if not cg_b:
                continue
            for cg_x, cg_y in cg_members:
                if point_in_poly(cg_x, cg_y, cg_d["poly"]):
                    cg_bands.setdefault(cg_b, []).append(math.hypot(cg_x - cg_cx, cg_y - cg_cy))
        cg_bad = []
        cg_order = ["yashiki", "detached", "terrace"]
        # EVERY ordered pair, not only adjacent ones: with the middle band empty (a mid-build
        # map) adjacent-only left yashiki-vs-terrace uncompared and the inversion invisible -
        # caught by this check's own red test before it ever gated a map.
        for cg_i in range(len(cg_order)):
            for cg_j in range(cg_i + 1, len(cg_order)):
                cg_a, cg_c = cg_order[cg_i], cg_order[cg_j]
                if not (cg_bands.get(cg_a) and cg_bands.get(cg_c)):
                    continue
                cg_ma = sum(cg_bands[cg_a]) / len(cg_bands[cg_a])
                cg_mc = sum(cg_bands[cg_c]) / len(cg_bands[cg_c])
                if cg_ma > cg_mc + 12:
                    cg_bad.append(f"{cg_a} (mean {cg_ma:.0f}px from the castle) sits beyond {cg_c} (mean {cg_mc:.0f}px)")
        check(
            "capital_rank_gradient",
            not cg_bad,
            f"rank bands out of order from the castle: {cg_bad} - the jokamachi law grades proximity by rank (yashiki nearest, then detached, then terraces)",
        )
    return _kept(locals(), ('cg_a', 'cg_b', 'cg_bad', 'cg_bands', 'cg_c', 'cg_cx', 'cg_cy', 'cg_d', 'cg_i', 'cg_j', 'cg_ma', 'cg_mc', 'cg_members', 'cg_order', 'cg_x', 'cg_y', 'h4', 'm', 't4'))


# THE WALL SETTLES FIRST (GM process rule, 2026-08-10): fine iteration on a capital is
# forbidden until the interior's OPEN share is inside the band, because every fine
# adjustment is downstream of the wall and a wall re-derivation invalidates them all.
# Measured the day the rule was made: 41% of the walled interior stood as claimed-open
# commons after two wall sizings, and hours of junction/well/kido tuning had been spent
# against a rampart that was about to move. Claimed-open ground (commons of any role)
# inside the wall must stay under ~15% of the interior - beyond that, the wall is
# oversized for its fabric: RE-DERIVE RX/RY (citybudget) before touching anything else.


def _seg_0349__capital_interior_slack_in_band(
    *,
    M: Any = _UNBOUND,
    _sl_c: Any = _UNBOUND,
    _sl_interior: Any = _UNBOUND,
    _sl_open: Any = _UNBOUND,
    _sl_p: Any = _UNBOUND,
    _sl_wall: Any = _UNBOUND,
    check: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    q: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 349 (capital_interior_slack_in_band) - body verbatim from the legacy gate() (feature 022)."""
    if meta.get("scale") == "capital" and len(M.get("wall") or []) >= 3:
        _sl_wall = M["wall"]
        _sl_interior = _poly_area(_sl_wall)
        _sl_open = 0.0
        for _sl_c in M.get("commons", []) or []:
            _sl_p = _sl_c.get("poly") or []
            if len(_sl_p) >= 3 and point_in_poly(sum(q[0] for q in _sl_p) / len(_sl_p), sum(q[1] for q in _sl_p) / len(_sl_p), _sl_wall):
                _sl_open += _poly_area(_sl_p)
        check(
            "capital_interior_slack_in_band",
            _sl_open <= 0.15 * _sl_interior,
            f"THE WALL IS OVERSIZED FOR ITS FABRIC: {_sl_open / _sl_interior:.0%} of the walled interior is claimed-open ground "
            f"({_sl_open:,.0f} of {_sl_interior:,.0f} px^2; the band is <= 15%). Do NOT fine-tune anything against this rampart - "
            f"re-derive RX/RY from the fabric's real density (citybudget) and re-lay the rim FIRST (the wall settles before fine "
            f"iteration; every junction/well/kido adjustment made now dies with the resize).",
        )
    return _kept(locals(), ('_sl_c', '_sl_interior', '_sl_open', '_sl_p', '_sl_wall', 'q'))


# SOVEREIGN PRECINCT INTERIORS (T017, research item 7): once a precinct reservation is
# DECLARED (M['precincts'], the 021 engine path), its head-house program must actually be
# drawn - >= 5 halls, every one fully inside the reserved rect (a dormitory overhanging the
# reservation is a pack-collision waiting to happen; the reserve is the contract).


def _seg_0350__pr_list(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 350 (pr_list) - body verbatim from the legacy gate() (feature 022)."""
    pr_list = M.get("precincts") or []
    return _kept(locals(), ('pr_list',))


def _seg_0351__precinct_interiors_within_reservation(
    *,
    M: Any = _UNBOUND,
    _mz_floor: Any = _UNBOUND,
    _mz_t: Any = _UNBOUND,
    bz: Any = _UNBOUND,
    cg8: Any = _UNBOUND,
    check: Any = _UNBOUND,
    comm: Any = _UNBOUND,
    dz: Any = _UNBOUND,
    hh: Any = _UNBOUND,
    mine: Any = _UNBOUND,
    mz_bad: Any = _UNBOUND,
    pg_bad: Any = _UNBOUND,
    pr: Any = _UNBOUND,
    pr_bad: Any = _UNBOUND,
    pr_list: Any = _UNBOUND,
    px0: Any = _UNBOUND,
    px1: Any = _UNBOUND,
    py0: Any = _UNBOUND,
    py1: Any = _UNBOUND,
    rg: Any = _UNBOUND,
    rg9: Any = _UNBOUND,
    tor_in: Any = _UNBOUND,
    tp: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 351 (monzen_fronts_the_approach, precinct_graveyard_claims_closed, precinct_interiors_within_reservation) - body verbatim from the legacy gate() (feature 022)."""
    if pr_list:
        pr_bad: list[str] = []  # type: ignore[no-redef]
        for pr in pr_list:
            px0, py0, px1, py1 = pr["x"] - pr["w"] / 2, pr["y"] - pr["h"] / 2, pr["x"] + pr["w"] / 2, pr["y"] + pr["h"] / 2
            mine = [hh for hh in M.get("precinct_halls", []) if abs(hh["precinct"][0] - pr["x"]) < 2 and abs(hh["precinct"][1] - pr["y"]) < 2]
            if len(mine) < 5:
                pr_bad.append(f"precinct ({pr['x']:.0f},{pr['y']:.0f}) draws only {len(mine)} interior halls (want >= 5: residence, administration, library, dormitories, kitchen)")
            for hh in mine:
                if hh["x"] - hh["w"] / 2 < px0 - 0.5 or hh["x"] + hh["w"] / 2 > px1 + 0.5 or hh["y"] - hh["h"] / 2 < py0 - 0.5 or hh["y"] + hh["h"] / 2 > py1 + 0.5:
                    pr_bad.append(f"{hh['kind']} at ({hh['x']:.0f},{hh['y']:.0f}) overhangs its precinct reservation")
        check(
            "precinct_interiors_within_reservation",
            not pr_bad,
            f"sovereign precinct interior(s) missing or overhanging the reserved ground: {pr_bad} - the 020 reservation is the contract; draw the program inside it",
        )
        # the 020 graveyard CLAIMS close when the precincts are drawn: a temple recorded with
        # graveyard=True must have a burial plot on the ground (claimed but undrawn ground is
        # exactly the debt 021 exists to pay)
        pg_bad = [
            str(rg.get("label") or rg.get("name") or "temple")
            for rg in M.get("religious", [])
            if rg.get("graveyard") and not any(math.hypot(cg8["x"] - rg["x"], cg8["y"] - rg["y"]) <= 230 for cg8 in M.get("cemeteries", []))
        ]
        check(
            "precinct_graveyard_claims_closed",
            not pg_bad,
            f"temple(s) claiming a graveyard (graveyard=True) with no burial plot drawn within 230px: {pg_bad} - close the 020 claim (draw the parish plot) or drop the claim",
        )
        # MONZEN fronts the APPROACH (T018, research item 8): a monzen district is the lay
        # commercial quarter at the temple's GATE, so its rows stand on the side the torii
        # face - a monzen on the temple's blind side reads as a generic machi mislabeled.
        mz_bad = []
        for dz in M.get("districts", []):
            if dz.get("kind") != "monzen":
                continue
            tor_in = sum(1 for tp in M.get("torii", []) if point_in_poly(tp[0], tp[1], dz["poly"]))
            comm = sum(1 for bz in M.get("buildings", []) if bz.get("kind") in ("shop", "merchant", "merchant_house") and point_in_poly(bz["x"], bz["y"], dz["poly"]))
            # the monzen's size follows the approach's grandeur (the torii numerology canon:
            # an avenue is 1-2 arches or EXACTLY 7): a full 7-arch sando commands a full lay
            # quarter (>= 6 commercial); a 1-2 arch approach carries a modest one (>= 3) -
            # Jurojin's north stub between hall and the kagi road holds ~3 stalls lawfully
            _mz_t = min(
                (rg9 for rg9 in M.get("religious", []) if rg9.get("kind") == "temple"),
                key=lambda rg9: (rg9["x"] - dz["poly"][0][0]) ** 2 + (rg9["y"] - dz["poly"][0][1]) ** 2,
                default=None,
            )
            _mz_floor = 6 if (_mz_t or {}).get("torii_count", 0) >= 7 else 3
            if tor_in == 0:
                mz_bad.append(f"{dz.get('name', 'monzen')}: no torii inside the district (it does not front the approach)")
            elif comm < _mz_floor:
                mz_bad.append(f"{dz.get('name', 'monzen')}: only {comm} commercial buildings (a monzen is a lay COMMERCIAL quarter; want >= {_mz_floor})")
        check(
            "monzen_fronts_the_approach",
            not mz_bad,
            f"monzen district(s) not doing a monzen's job: {mz_bad} - the lay quarter stands at the temple's gate, on the side the torii face",
        )
    return _kept(locals(), ('_mz_floor', '_mz_t', 'bz', 'cg8', 'comm', 'dz', 'hh', 'mine', 'mz_bad', 'pg_bad', 'pr', 'pr_bad', 'px0', 'px1', 'py0', 'py1', 'rg', 'rg9', 'tor_in', 'tp'))


# TERAMACHI BACKSTRIP stays LEAN (T019, research item 9, capitals only): the rim temples
# are part of the defensive belt, and the strip BEHIND each (between temple and rampart)
# is the temples' own back ground + the patrol strip - never packed housing. Monk houses
# are the temples' own and may stand there.


def _seg_0352__teramachi_backstrip_lean(
    *,
    M: Any = _UNBOUND,
    _tb_wall: Any = _UNBOUND,
    bz: Any = _UNBOUND,
    check: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    rg: Any = _UNBOUND,
    t9: Any = _UNBOUND,
    tb_bad: Any = _UNBOUND,
    tb_d: Any = _UNBOUND,
    tb_wp: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 352 (teramachi_backstrip_lean) - body verbatim from the legacy gate() (feature 022)."""
    if meta.get("scale") == "capital" and len(M.get("wall") or []) >= 3:
        tb_bad = []
        _tb_wall = M["wall"]
        for rg in M.get("religious", []):
            if rg.get("kind") != "temple":
                continue
            tb_d, tb_wp = min(
                (
                    (seg_dist(rg["x"], rg["y"], _tb_wall[i9], _tb_wall[(i9 + 1) % len(_tb_wall)]), seg_closest(rg["x"], rg["y"], _tb_wall[i9], _tb_wall[(i9 + 1) % len(_tb_wall)]))
                    for i9 in range(len(_tb_wall))
                ),
                key=lambda t9: t9[0],
            )
            if tb_d > 190:
                continue  # not a rim temple
            for bz in M.get("buildings", []):
                if (
                    bz.get("kind") in DWELLING_KINDS
                    and bz.get("kind") != "monk_house"
                    and seg_dist(bz["x"], bz["y"], (rg["x"], rg["y"]), tb_wp) < rg.get("w", 30) / 2
                    and math.hypot(bz["x"] - rg["x"], bz["y"] - rg["y"]) < tb_d + 40
                ):
                    tb_bad.append((round(bz["x"]), round(bz["y"])))
        check(
            "teramachi_backstrip_lean",
            not tb_bad,
            f"packed dwelling(s) silting the teramachi backstrip (between a rim temple and the rampart): {sorted(set(tb_bad))[:4]} - the strip is the temples' back ground and the patrol zone, not housing depth",
        )
    return _kept(locals(), ('_tb_wall', 'bz', 'i9', 'rg', 'tb_bad', 'tb_d', 'tb_wp'))


# THE FABRIC HITS THE BUDGET'S BAND TARGETS (T006): the 018 budget is the housing
# authority, so each band's drawn count lands on its dwelling_target - yashiki compounds
# and detached samurai houses by record count, terraces by their UNIT count (one roof,
# `units` households), packed rows by dwelling-kind buildings in the machi-family
# districts. Tolerance max(2, 5%) absorbs seat jitter without permitting a quietly-short
# band (the Minami sign-off lesson, applied at band granularity).


def _seg_0353__cb_tgt(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 353 (cb_tgt) - body verbatim from the legacy gate() (feature 022)."""
    cb_tgt = (meta.get("budget") or {}).get("dwelling_target")
    return _kept(locals(), ('cb_tgt',))


def _seg_0354__capital_housing_matches_band_targets(
    *,
    M: Any = _UNBOUND,
    _cb_dens: Any = _UNBOUND,
    _cb_inw: Any = _UNBOUND,
    _cb_marea: Any = _UNBOUND,
    _cb_packed: Any = _UNBOUND,
    _cb_pin: Any = _UNBOUND,
    _cb_pout: Any = _UNBOUND,
    _cb_tin: Any = _UNBOUND,
    _cb_tout: Any = _UNBOUND,
    _cb_wall: Any = _UNBOUND,
    b6: Any = _UNBOUND,
    cb_bad: Any = _UNBOUND,
    cb_in: Any = _UNBOUND,
    cb_k: Any = _UNBOUND,
    cb_msg: Any = _UNBOUND,
    cb_n: Any = _UNBOUND,
    cb_pairs: Any = _UNBOUND,
    cb_tgt: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d6: Any = _UNBOUND,
    m6: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    p6: Any = _UNBOUND,
    q6: Any = _UNBOUND,
    t6: Any = _UNBOUND,
    x9: Any = _UNBOUND,
    y9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 354 (capital_housing_matches_band_targets) - body verbatim from the legacy gate() (feature 022)."""
    if meta.get("scale") == "capital" and cb_tgt and M.get("districts"):

        def cb_in(kinds: set[str]) -> list[Any]:
            return [d6["poly"] for d6 in M["districts"] if d6.get("rank_band") in kinds or d6.get("kind") in kinds]

        # the packed cohort is validated as TWO bands, in-wall and suburban, never as one total
        # (the wall-resize lesson, GM 2026-08-10): validating only the total let a wall sized
        # with a provincial density constant silently spill 57% of the cohort into suburbs
        # against a researched 30% share - the one number that would have caught it
        # (packed_suburb) was computed, recorded in the budget, and never enforced.
        _cb_wall = M.get("wall") or []

        def _cb_inw(x9: float, y9: float) -> bool:
            return bool(point_in_poly(x9, y9, _cb_wall)) if len(_cb_wall) >= 3 else True

        _cb_packed = [
            b6
            for b6 in M.get("buildings", [])
            if b6.get("kind") in DWELLING_KINDS
            and not str(b6.get("kind", "")).startswith("samurai")
            and any(bool(point_in_poly(b6["x"], b6["y"], p6)) for p6 in cb_in({"machi", "monzen", "entertainment"}))
        ]
        _cb_pin = sum(1 for b6 in _cb_packed if _cb_inw(b6["x"], b6["y"]))
        _cb_pout = len(_cb_packed) - _cb_pin
        _cb_tin = int(cb_tgt.get("packed", 0)) - int(cb_tgt.get("packed_suburb", 0))
        cb_pairs = [
            ("samurai_yashiki", sum(1 for m6 in M.get("manors", []) if any(bool(point_in_poly(m6["x"], m6["y"], p6)) for p6 in cb_in({"yashiki"})))),
            (
                "samurai_detached",
                sum(1 for b6 in M.get("buildings", []) if str(b6.get("kind", "")).startswith("samurai") and any(bool(point_in_poly(b6["x"], b6["y"], p6)) for p6 in cb_in({"detached"}))),
            ),
            ("samurai_terrace", sum(int(t6.get("units", 0)) for t6 in M.get("terraces", []) if any(bool(point_in_poly(t6["x"], t6["y"], p6)) for p6 in cb_in({"terrace"})))),
        ]
        cb_bad = [f"{cb_k}: drawn {cb_n} vs target {int(cb_tgt.get(cb_k, 0))}" for cb_k, cb_n in cb_pairs if abs(cb_n - int(cb_tgt.get(cb_k, 0))) > max(2, round(0.05 * int(cb_tgt.get(cb_k, 0))))]
        if abs(_cb_pin - _cb_tin) > max(2, round(0.05 * _cb_tin)):
            cb_bad.append(f"packed_inwall: drawn {_cb_pin} vs target {_cb_tin}")
        _cb_tout = int(cb_tgt.get("packed_suburb", 0))
        if abs(_cb_pout - _cb_tout) > max(2, round(0.05 * _cb_tout)):
            cb_bad.append(f"packed_suburb: drawn {_cb_pout} vs target {_cb_tout}")
        # the SPECIFIC failure that motivated the split gets its own unmissable diagnosis: when
        # the in-wall band is short AND the suburbs are over, no amount of seat-jiggling can fix
        # it - the wall itself is undersized for the fabric's real density.
        cb_msg = f"band(s) off the budget's dwelling_target: {cb_bad} - the 018 budget is the housing authority; seat the shortfall (or fix the district declaration hiding it)"
        if _cb_pin < _cb_tin - max(2, round(0.05 * _cb_tin)) and _cb_pout > _cb_tout + max(2, round(0.05 * _cb_tout)):
            _cb_dens = None
            _cb_marea = sum(
                _poly_area(d6["poly"])
                for d6 in M.get("districts", [])
                if (d6.get("rank_band") in ("machi", "monzen", "entertainment") or d6.get("kind") in ("machi", "monzen", "entertainment"))
                and _cb_inw(sum(q6[0] for q6 in d6["poly"]) / len(d6["poly"]), sum(q6[1] for q6 in d6["poly"]) / len(d6["poly"]))
            )
            if _cb_pin:
                _cb_dens = _cb_marea / _cb_pin
            cb_msg = (
                f"THIS CANNOT WORK WITHOUT RESIZING THE WALL: the in-wall packed band is short ({_cb_pin} vs {_cb_tin}) while the suburbs are over "
                f"({_cb_pout} vs {_cb_tout}) - the rampart as drawn cannot hold the in-wall cohort at the fabric's real density"
                + (f" (as-built ~{_cb_dens:.0f} px^2/family across {_cb_marea:,.0f} px^2 of in-wall machi ground)" if _cb_dens else "")
                + ". Do NOT keep seating the overflow outside: re-derive required_interior from the measured density (C_PACKED_CAPITAL in citybudget.py), "
                "re-pin RX/RY, and re-lay the rim. Spilling the shortfall into suburbs is how a 57%-extramural capital shipped past a total-only check (GM 2026-08-10)."
            )
        check("capital_housing_matches_band_targets", not cb_bad, cb_msg)
    return _kept(
        locals(),
        (
            '_cb_dens',
            '_cb_inw',
            '_cb_marea',
            '_cb_packed',
            '_cb_pin',
            '_cb_pout',
            '_cb_tin',
            '_cb_tout',
            '_cb_wall',
            'b6',
            'cb_bad',
            'cb_in',
            'cb_k',
            'cb_msg',
            'cb_n',
            'cb_pairs',
            'd6',
            'm6',
            'p6',
            'q6',
            't6',
        ),
    )


# A TERRACE IS A RANGE (T005): the record models ONE roof over several household cells;
# a single-cell "terrace" is a detached house miscoded, and would double-count against
# the band targets. Runs wherever the record appears.


def _seg_0355__terraces_are_ranges(*, M: Any = _UNBOUND, check: Any = _UNBOUND, t5: Any = _UNBOUND, tr_bad: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 355 (terraces_are_ranges) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("terraces"):
        tr_bad = [(round(t5["x"]), round(t5["y"])) for t5 in M["terraces"] if int(t5.get("units", 0)) < 2]
        check(
            "terraces_are_ranges",
            not tr_bad,
            f"terrace range(s) with fewer than 2 units at {tr_bad[:4]} - a one-unit terrace is a detached house; use the house vocabulary",
        )
    return _kept(locals(), ('t5', 'tr_bad'))


# A JOSUI-IDO SITS ON THE BURIED MAIN (research 021 item 4): from the settling basin at
# the gate the mokuhi trunk mains run under the WAYS and the laterals under the roji -
# Edo branched its pipes under the tenement alleys to the josui-ido courts - so a
# cistern-well stands within the band (900 real ft of the terminus; the DISCLOSED
# calibrated liberty - Edo's mains ran kilometers, a young domain system serves its two
# gate-quarter blocks) and within 30px of some way. A dug draw-well (no kind) is untouched.


def _seg_0356__cw21(*, M: Any = _UNBOUND, w21: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 356 (cw21, w21) - body verbatim from the legacy gate() (feature 022)."""
    cw21 = [w21 for w21 in M.get("wells", []) if isinstance(w21, dict) and w21.get("kind") == "cistern"]
    return _kept(locals(), ('cw21', 'w21'))


def _seg_0357__cistern_wells_in_service_band(
    *,
    M: Any = _UNBOUND,
    al21: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cw21: Any = _UNBOUND,
    cw_aq: Any = _UNBOUND,
    cw_bad: Any = _UNBOUND,
    cw_reach: Any = _UNBOUND,
    cw_sts: Any = _UNBOUND,
    cw_to: Any = _UNBOUND,
    i21: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    p21: Any = _UNBOUND,
    r21: Any = _UNBOUND,
    st21: Any = _UNBOUND,
    w21: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 357 (cistern_wells_in_service_band) - body verbatim from the legacy gate() (feature 022)."""
    if cw21:
        cw_aq = M.get("aqueducts", [])
        cw_bad = []
        if not cw_aq:
            cw_bad = [(round(w21["x"]), round(w21["y"]), "no aqueduct to tap") for w21 in cw21]
        else:
            cw_to = cw_aq[0].get("to")
            cw_reach = 900.0 / float(meta.get("ftpx", 1) or 1)
            # the mains run under the WAYS from the gate - streets, and the trunk road that
            # enters it (the east quarter's only paved way is the gate road itself)
            cw_sts = (
                [st21["pts"] for st21 in M.get("town_streets", [])]
                + ([M["road"]] if M.get("road") else [])
                + [r21["pts"] for r21 in M.get("roads", [])]
                + [al21["pts"] for al21 in M.get("alleys", [])]
            )
            for w21 in cw21:
                if math.hypot(w21["x"] - cw_to[0], w21["y"] - cw_to[1]) > cw_reach:
                    cw_bad.append((round(w21["x"]), round(w21["y"]), "beyond the main's ~600 ft reach"))
                elif not any(seg_dist(w21["x"], w21["y"], tuple(p21[i21]), tuple(p21[i21 + 1])) <= 30 for p21 in cw_sts for i21 in range(len(p21) - 1)):
                    cw_bad.append((round(w21["x"]), round(w21["y"]), "off the street the main runs under"))
        check(
            "cistern_wells_in_service_band",
            not cw_bad,
            f"josui-ido out of the service band: {cw_bad[:4]} - a cistern-well taps the buried main under a STREET within ~600 real ft of the settling basin (s.place_wells(kind='cistern'))",
        )
    return _kept(locals(), ('al21', 'cw_aq', 'cw_bad', 'cw_reach', 'cw_sts', 'cw_to', 'i21', 'p21', 'r21', 'st21', 'w21'))


# THE KIDO MESH BARS THE MACHI MOUTHS (research 021 item 6): every street mouth into an
# in-wall machi district carries its night-barred kido. The mouths come from settlement.
# machi_mouths - the SAME source the placer reads - so placement and validation cannot
# disagree (the bridge_carried_ways doctrine).
# ...and the mesh is a KNOB, not a law (GM 2026-08-10): interior ward gates may be right
# for one city and wrong for the next, so meta(ward_gates=False) turns the whole doctrine
# off for a map that does not use them. It is an explicit declaration, never an absence -
# a map that simply forgot its kido still fails.


def _seg_0358__kido_close_the_machi_mouths(
    *,
    M: Any = _UNBOUND,
    check: Any = _UNBOUND,
    k21: Any = _UNBOUND,
    kkx: Any = _UNBOUND,
    kky: Any = _UNBOUND,
    km_bad: Any = _UNBOUND,
    km_kido: Any = _UNBOUND,
    kmx: Any = _UNBOUND,
    kmy: Any = _UNBOUND,
    meta: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 358 (kido_close_the_machi_mouths) - body verbatim from the legacy gate() (feature 022)."""
    if meta.get("scale") == "capital" and M.get("districts") and meta.get("ward_gates", True):
        km_kido = [(k21["x"], k21["y"]) if isinstance(k21, dict) else (k21[0], k21[1]) for k21 in M.get("kido", [])]
        km_bad = [(round(kmx), round(kmy)) for kmx, kmy in machi_mouths(M) if not any(math.hypot(kmx - kkx, kmy - kky) <= 70 for kkx, kky in km_kido)]
        check(
            "kido_close_the_machi_mouths",
            not km_bad,
            f"machi street mouth(s) with no kido within 70px: {km_bad[:4]} - the ward MESH bars every block mouth at night (s.kido_mesh(); ward_style='mesh')",
        )
    return _kept(locals(), ('k21', 'kkx', 'kky', 'km_bad', 'km_kido', 'kmx', 'kmy'))


# EVERY GATE'S ROAD JOINS THE RING ROAD (GM 2026-08-09, the capital's side gates: both
# trunk-road polylines STARTED at the gate point on the wall, so the road reached the gate
# from outside while inside the gate opened onto 90 ft of bare ground 30px short of the
# ring - a door to nowhere, and invisible because no check watched gate-to-ring
# connectivity. A walled city's gate traffic distributes along the ring, so SOME way (the
# Imperial road, a trunk road, or a street) must pass the gate AND meet the ring - by a
# vertex near it or by crossing it outright.


def _seg_0359__gate_roads_join_the_ring(
    *,
    M: Any = _UNBOUND,
    check: Any = _UNBOUND,
    gr_bad: Any = _UNBOUND,
    gr_g: Any = _UNBOUND,
    gr_ok: Any = _UNBOUND,
    gr_pts: Any = _UNBOUND,
    gr_ring: Any = _UNBOUND,
    gr_ways: Any = _UNBOUND,
    gr_x: Any = _UNBOUND,
    gr_y: Any = _UNBOUND,
    i: Any = _UNBOUND,
    j: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    r: Any = _UNBOUND,
    s: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 359 (gate_roads_join_the_ring) - body verbatim from the legacy gate() (feature 022)."""
    if meta.get("scale") in ("city", "capital") and M.get("ring_road") and M.get("gates"):
        gr_ring = M["ring_road"]
        gr_ways = ([M["road"]] if M.get("road") else []) + [r["pts"] for r in M.get("roads", [])] + [s["pts"] for s in M.get("town_streets", [])]
        gr_bad = []
        for gr_g in M["gates"]:
            gr_x, gr_y = gr_g[0], gr_g[1]
            gr_ok = False
            for gr_pts in gr_ways:
                if min(seg_dist(gr_x, gr_y, gr_pts[i], gr_pts[i + 1]) for i in range(len(gr_pts) - 1)) > 8:
                    continue  # this way does not serve this gate
                if any(seg_dist(gr_pts[i][0], gr_pts[i][1], gr_ring[j], gr_ring[j + 1]) <= 8 for i in range(len(gr_pts)) for j in range(len(gr_ring) - 1)) or any(
                    segments_cross(tuple(gr_pts[i]), tuple(gr_pts[i + 1]), tuple(gr_ring[j]), tuple(gr_ring[j + 1])) for i in range(len(gr_pts) - 1) for j in range(len(gr_ring) - 1)
                ):
                    gr_ok = True
                    break
            if not gr_ok:
                gr_bad.append((round(gr_x), round(gr_y)))
        check(
            "gate_roads_join_the_ring",
            not gr_bad,
            f"gate(s) whose way stops short of the ring road (x, y): {gr_bad[:4]} - a gate's road must JOIN the ring (extend the polyline ~30px inward to the ring's inset), not stop on the sill",
        )
    return _kept(locals(), ('gr_bad', 'gr_g', 'gr_ok', 'gr_pts', 'gr_ring', 'gr_ways', 'gr_x', 'gr_y', 'i', 'j', 'r', 's'))
