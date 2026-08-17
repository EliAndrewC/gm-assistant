"""Gate segments (ways and bridges) - bodies verbatim from check_village.py (feature 024 package split; registry order preserved)."""

import collections
import math
from typing import Any

from l7r.diagram.settlement import bridge_carried_ways, bridge_crossed_waters, machi_mouths

from .common_01_geometry import Pt, point_in_poly, seg_closest, seg_dist, seg_intersect, segments_cross
from .common_02_overlap_policy import GridIndex
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


# A DECK LANDS PAST ITS BANKS (GM 2026-08-09, tightened from ends-reach-the-edge): every
# CORNER of the deck clears the crossed water's edge onto dry ground. The ends-based rule
# let an oblique deck pass with a corner sitting exactly AT the water's edge (the capital's
# east deck landed 0.0 ft), which reads structurally impossible - a real abutment sill sits
# BACK from the channel edge so scour cannot undercut the bearing (settlement.LANDING_FT
# holds the research). s.bridges() draws LANDING_FT (10 real ft) of landing per side; the
# floor here is 6 ft so local water curvature under a deck does not flap the gate. A
# standalone FOOTPLANK keeps its deliberately short PLANK_ABUTMENT (GM 2026-07-22) and is
# floored at 2 ft. Real feet, converted via meta.ftpx. The crossed water is the WIDEST
# watercourse under the deck's seat, from the same shared source both bridging sides read;
# footprint family: gap VERDICT, measured on the deck's four real corners.


def _seg_0360__b_ftpx(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 360 (b_ftpx) - body verbatim from the legacy gate() (feature 022)."""
    b_ftpx = float(meta.get("ftpx", 1) or 1)
    return _kept(locals(), ('b_ftpx',))


def _seg_0361__b_short() -> dict[str, Any]:
    """Gate segment 361 (b_short) - body verbatim from the legacy gate() (feature 022)."""
    b_short = []  # type: ignore[var-annotated]
    return _kept(locals(), ('b_short',))


def _seg_0362__b_dry() -> dict[str, Any]:
    """Gate segment 362 (b_dry) - body verbatim from the legacy gate() (feature 022)."""
    b_dry: list[str] = []
    return _kept(locals(), ('b_dry',))


def _seg_0363__b_1(
    *,
    M: Any = _UNBOUND,
    b: Any = _UNBOUND,
    b_crossed: Any = _UNBOUND,
    b_cw: Any = _UNBOUND,
    b_cx: Any = _UNBOUND,
    b_cy: Any = _UNBOUND,
    b_d: Any = _UNBOUND,
    b_dry: Any = _UNBOUND,
    b_floor: Any = _UNBOUND,
    b_ftpx: Any = _UNBOUND,
    b_hl: Any = _UNBOUND,
    b_hw: Any = _UNBOUND,
    b_pts: Any = _UNBOUND,
    b_short: Any = _UNBOUND,
    b_su: Any = _UNBOUND,
    b_sv: Any = _UNBOUND,
    b_th: Any = _UNBOUND,
    b_ux: Any = _UNBOUND,
    b_uy: Any = _UNBOUND,
    b_wid: Any = _UNBOUND,
    i: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 363 (b, b_crossed, b_cw, b_cx) - body verbatim from the legacy gate() (feature 022)."""
    for b in M.get("bridges", []):
        b_th = math.radians(b.get("rot", 0.0))
        b_ux, b_uy = math.cos(b_th), math.sin(b_th)
        b_hl, b_hw = b["span"] / 2, b["w"] / 2
        b_crossed: Any = None  # type: ignore[no-redef]
        b_cw = 0.0
        for b_pts, b_wid in bridge_crossed_waters(M):
            b_d = min(seg_dist(b["x"], b["y"], b_pts[i], b_pts[i + 1]) for i in range(len(b_pts) - 1))
            if b_d <= b_wid / 2 + 2 and b_wid > b_cw:
                b_crossed, b_cw = b_pts, b_wid
        if b_crossed is None:
            b_dry.append(f"({round(b['x'])},{round(b['y'])}) span {b['span']:.0f}")
            continue  # no water under the seat: bridges_seat_on_water fires below; the span rule has nothing to measure
        b_floor = (2.0 if b.get("foot") else 6.0) / b_ftpx
        for b_su, b_sv in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            b_cx = b["x"] + b_su * b_ux * b_hl - b_sv * b_uy * b_hw
            b_cy = b["y"] + b_su * b_uy * b_hl + b_sv * b_ux * b_hw
            if min(seg_dist(b_cx, b_cy, b_crossed[i], b_crossed[i + 1]) for i in range(len(b_crossed) - 1)) < b_cw / 2 + b_floor:
                b_short.append(f"({round(b['x'])},{round(b['y'])}) span {b['span']:.0f} on ~{b_cw:.0f}px water")
                break
    return _kept(locals(), ('b', 'b_crossed', 'b_cw', 'b_cx', 'b_cy', 'b_d', 'b_dry', 'b_floor', 'b_hl', 'b_hw', 'b_pts', 'b_short', 'b_su', 'b_sv', 'b_th', 'b_ux', 'b_uy', 'b_wid', 'i'))


# A DECK MUST SIT ON WATER AT ALL (settlement-review 2026-08-10): Shiro Daika's towpath
# plank kept its seat when the drain's re-route moved the ford, and it lay on bare bank for
# a whole feature - bridges_span_their_water silently skipped it (nothing to measure) and no
# other rule owned the case. A check that never runs looks exactly like a check that passes.
# BANK-PARALLEL WORKS FOLLOW THEIR BANK (GM 2026-08-10: "when we originally rendered the
# domain granaries and the imperial granary, they were aligned with the river. However, at
# a certain point, it looks like the angle of the river changed slightly, but the angle of
# the granaries did not"). A quay granary row is laid ALONG the water it loads from, and a
# jetty runs ACROSS it - both angles are properties of the bank, not constants, so a
# re-routed river must drag them or they read as a row built by someone who could not see
# the water. Same family as towpath_hugs_the_bank: derive the angle from the CURRENT
# polyline, never keep a rot that was right before the re-route.


def _seg_0364__bp_riv(*, M: Any = _UNBOUND, cn9: Any = _UNBOUND, w9: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 364 (bp_riv, cn9, w9) - body verbatim from the legacy gate() (feature 022)."""
    bp_riv = [w9["poly"] for w9 in M.get("streams", [])] + [cn9["poly"] for cn9 in M.get("canals", [])]
    return _kept(locals(), ('bp_riv', 'cn9', 'w9'))


def _seg_0365__waterside_works_follow_the_bank(
    *,
    M: Any = _UNBOUND,
    bp_bad: Any = _UNBOUND,
    bp_bear: Any = _UNBOUND,
    bp_bearing: Any = _UNBOUND,
    bp_d: Any = _UNBOUND,
    bp_f: Any = _UNBOUND,
    bp_key: Any = _UNBOUND,
    bp_off: Any = _UNBOUND,
    bp_riv: Any = _UNBOUND,
    bp_want: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d9: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    wp9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 365 (waterside_works_follow_the_bank) - body verbatim from the legacy gate() (feature 022)."""
    if bp_riv:

        def bp_bearing(px: float, py: float) -> tuple[float, float]:
            bp_best = (1e9, 0.0)
            for wp9 in bp_riv:
                for i9 in range(len(wp9) - 1):
                    d9 = seg_dist(px, py, wp9[i9], wp9[i9 + 1])
                    if d9 < bp_best[0]:
                        bp_best = (d9, math.degrees(math.atan2(wp9[i9 + 1][1] - wp9[i9][1], wp9[i9 + 1][0] - wp9[i9][0])))
            return bp_best

        bp_bad = []
        for bp_key, bp_want in (("granaries", 0.0), ("jetties", 90.0), ("tanning_yards", 0.0), ("dye_yards", 0.0)):  # rows and wash yards lie ALONG the bank; stages run ACROSS it
            for bp_f in M.get(bp_key, []):  # both keys hold records, never raw polygons
                bp_d, bp_bear = bp_bearing(bp_f["x"], bp_f["y"])
                if bp_d > 140:
                    continue  # not a waterside instance (an inland store is not bank-parallel)
                bp_off = abs((float(bp_f.get("rot", 0.0)) - bp_bear - bp_want) % 180.0)
                bp_off = min(bp_off, 180.0 - bp_off)
                if bp_off > 4.0:
                    bp_bad.append((bp_key, round(bp_f["x"]), round(bp_f["y"]), round(bp_off, 1)))
        check(
            "waterside_works_follow_the_bank",
            not bp_bad,
            f"waterside work(s) off their bank's angle (key, x, y, degrees off): {sorted(set(bp_bad))[:4]} - a quay granary row lies "
            f"ALONG the water and a jetty runs ACROSS it; recompute the rot from the CURRENT river polyline at that point (a bank "
            f"angle is derived geometry, not a constant that survives a re-route)",
        )
    return _kept(locals(), ('bp_bad', 'bp_bear', 'bp_bearing', 'bp_d', 'bp_f', 'bp_key', 'bp_off', 'bp_want'))


# A CAPTION SITS BY WHAT IT NAMES (GM 2026-08-10: "the aqueduct labels are no longer
# correctly placed - the settling basin one is not even really next to the actual feature,
# it is on top of the city walls, and the intake weir label is way far away from the actual
# thing it is labeling"). `labels_clear_of_other_buildings` stops a caption COVERING the
# wrong thing; nothing stopped one drifting away from the RIGHT thing. Point-feature
# captions (the water furniture, the works) are checked against the feature their text
# names, because those are the ones a standoff ladder can push far from their subject.


def _seg_0366__lb_named() -> dict[str, Any]:
    """Gate segment 366 (lb_named) - body verbatim from the legacy gate() (feature 022)."""
    lb_named: list[tuple[str, list[tuple[float, float]]]] = []
    return _kept(locals(), ('lb_named',))


def _seg_0367__a9(
    *,
    M: Any = _UNBOUND,
    a9: Any = _UNBOUND,
    f9: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    lb_key: Any = _UNBOUND,
    lb_named: Any = _UNBOUND,
    lb_pts: Any = _UNBOUND,
    lb_word: Any = _UNBOUND,
    p1_9: Any = _UNBOUND,
    p2_9: Any = _UNBOUND,
    t9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 367 (a9, f9, i9, lb_key) - body verbatim from the legacy gate() (feature 022)."""
    for lb_key, lb_word in (("sluice_gates", "sluice"), ("aqueducts", "aqueduct"), ("kilns", "kiln"), ("dye_yards", "dye"), ("tanning_yards", "tanning")):
        lb_pts = [(f9["x"], f9["y"]) for f9 in M.get(lb_key, []) if isinstance(f9, dict) and "x" in f9]
        if lb_key == "aqueducts":  # a LINE's caption may sit anywhere along it, so sample the run
            for a9 in M.get("aqueducts", []):
                for i9 in range(len(a9.get("poly", [])) - 1):
                    p1_9, p2_9 = a9["poly"][i9], a9["poly"][i9 + 1]
                    for t9 in range(0, 11):
                        lb_pts.append((p1_9[0] + (p2_9[0] - p1_9[0]) * t9 / 10, p1_9[1] + (p2_9[1] - p1_9[1]) * t9 / 10))
        if lb_pts:
            lb_named.append((lb_word, lb_pts))
    return _kept(locals(), ('a9', 'f9', 'i9', 'lb_key', 'lb_named', 'lb_pts', 'lb_word', 'p1_9', 'p2_9', 't9'))


def _seg_0368__captions_sit_by_their_feature(
    *,
    M: Any = _UNBOUND,
    check: Any = _UNBOUND,
    lb: Any = _UNBOUND,
    lb_bad: Any = _UNBOUND,
    lb_cx: Any = _UNBOUND,
    lb_cy: Any = _UNBOUND,
    lb_d: Any = _UNBOUND,
    lb_extra: Any = _UNBOUND,
    lb_named: Any = _UNBOUND,
    lb_pts: Any = _UNBOUND,
    lb_text: Any = _UNBOUND,
    lb_word: Any = _UNBOUND,
    px9: Any = _UNBOUND,
    py9: Any = _UNBOUND,
    w9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 368 (captions_sit_by_their_feature) - body verbatim from the legacy gate() (feature 022)."""
    if lb_named:
        lb_extra = {"aqueduct": ("intake", "weir", "basin", "settling")}
        lb_bad = []
        for lb in M.get("labels", []):
            if len(lb) < 6:
                continue  # legacy fixture labels predate the text field
            lb_text = str(lb[5]).lower()
            lb_cx, lb_cy = (float(lb[0]) + float(lb[2])) / 2, (float(lb[1]) + float(lb[3])) / 2
            for lb_word, lb_pts in lb_named:
                if lb_word in lb_text or any(w9 in lb_text for w9 in lb_extra.get(lb_word, ())):
                    lb_d = min(math.hypot(lb_cx - px9, lb_cy - py9) for px9, py9 in lb_pts)
                    if lb_d > 90:  # 270 real ft at city grain - past that a caption reads as naming its neighbor
                        lb_bad.append((str(lb[5]), round(lb_cx), round(lb_cy), round(lb_d)))
                    break
        check(
            "captions_sit_by_their_feature",
            not lb_bad,
            f"caption(s) far from the feature they name (text, x, y, px): {lb_bad[:3]} - a caption that has drifted off its subject "
            f"names whatever it lands on instead; give it an explicit label_xy at the feature, or shorten the standoff ladder",
        )
    return _kept(locals(), ('lb', 'lb_bad', 'lb_cx', 'lb_cy', 'lb_d', 'lb_extra', 'lb_pts', 'lb_text', 'lb_word', 'px9', 'py9', 'w9'))


# ...AND NOT ON THE RAMPART (GM 2026-08-10: the settling-basin caption "is on top of the
# city walls"). A caption laid across the wall or the moat reads as naming the defenses,
# and the wall's own ink swallows the text. The label battery protects FOOTPRINTS from
# captions; the wall is a polyline, so nothing covered it.


def _seg_0369__cd_lines() -> dict[str, Any]:
    """Gate segment 369 (cd_lines) - body verbatim from the legacy gate() (feature 022)."""
    cd_lines = []  # type: ignore[var-annotated]
    return _kept(locals(), ('cd_lines',))


def _seg_0370__cd_lines_1(*, M: Any = _UNBOUND, cd_lines: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 370 (cd_lines) - body verbatim from the legacy gate() (feature 022)."""
    if len(M.get("wall") or []) >= 3:
        cd_lines.append((list(M["wall"]) + [M["wall"][0]], 9.0))
    return _kept(locals(), ('cd_lines',))


def _seg_0371__cd_lines_2(*, M: Any = _UNBOUND, cd_lines: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 371 (cd_lines) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("moat"):
        cd_lines.append((list(M["moat"]) + [M["moat"][0]], float(M.get("moat_width", 22)) / 2))
    return _kept(locals(), ('cd_lines',))


def _seg_0372__captions_clear_of_the_defenses(
    *,
    M: Any = _UNBOUND,
    cd_bad: Any = _UNBOUND,
    cd_hit: Any = _UNBOUND,
    cd_hw: Any = _UNBOUND,
    cd_lines: Any = _UNBOUND,
    cd_pts: Any = _UNBOUND,
    cd_quad: Any = _UNBOUND,
    check: Any = _UNBOUND,
    e9: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    lb: Any = _UNBOUND,
    qx9: Any = _UNBOUND,
    qy9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 372 (captions_clear_of_the_defenses) - body verbatim from the legacy gate() (feature 022)."""
    if cd_lines:
        cd_bad = []
        for lb in M.get("labels", []):
            if len(lb) < 6:
                continue  # ...same legacy shape
            cd_quad = [(float(lb[0]), float(lb[1])), (float(lb[2]), float(lb[1])), (float(lb[2]), float(lb[3])), (float(lb[0]), float(lb[3]))]
            for cd_pts, cd_hw in cd_lines:
                # corners AND edges: a caption box wider than the wall's band straddles the line
                # with every corner clear of it, which a corner-only test calls fine (the same
                # point-vs-footprint trap the skill has paid for before)
                cd_hit = any(seg_dist(qx9, qy9, cd_pts[i9], cd_pts[i9 + 1]) < cd_hw for qx9, qy9 in cd_quad for i9 in range(len(cd_pts) - 1)) or any(
                    segments_cross(cd_quad[e9], cd_quad[(e9 + 1) % 4], cd_pts[i9], cd_pts[i9 + 1]) for e9 in range(4) for i9 in range(len(cd_pts) - 1)
                )
                if cd_hit:
                    cd_bad.append((str(lb[5]), round((float(lb[0]) + float(lb[2])) / 2), round((float(lb[1]) + float(lb[3])) / 2)))
                    break
        check(
            "captions_clear_of_the_defenses",
            not cd_bad,
            f"caption(s) lying across the wall or moat: {cd_bad[:3]} - the rampart's ink swallows the text and the caption reads as "
            f"naming the defenses; move the label off the wall band (label_xy), keeping it beside the feature it names",
        )
    return _kept(locals(), ('cd_bad', 'cd_hit', 'cd_hw', 'cd_pts', 'cd_quad', 'e9', 'i9', 'lb', 'qx9', 'qy9'))


# WORKER HOUSING SITS WITH THE WORK (GM 2026-08-10: "I would expect the housing for those
# facilities to be close to those businesses and granaries... since the whole point of those
# houses being outside the city instead of inside of it is that those are the housing for
# the workers who work those facilities"). An extramural dwelling exists BECAUSE something
# outside needs hands on it - the quay, the granaries, the gate market's inns and stables.
# A row across the channel from all of it is a suburb with no reason, and the ruling that
# allowed extramural housing at all (2026-08-10, the wharf hamlet) was granted on exactly
# that basis. Measured to the nearest workplace, not to the wall.


def _seg_0373__extramural_housing_serves_its_work(
    *,
    M: Any = _UNBOUND,
    URBAN: Any = _UNBOUND,
    b9: Any = _UNBOUND,
    check: Any = _UNBOUND,
    eh_bad: Any = _UNBOUND,
    eh_ftpx: Any = _UNBOUND,
    eh_reach: Any = _UNBOUND,
    eh_wall: Any = _UNBOUND,
    eh_work: Any = _UNBOUND,
    k9: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    s9: Any = _UNBOUND,
    w9: Any = _UNBOUND,
    wx9: Any = _UNBOUND,
    wy9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 373 (extramural_housing_serves_its_work) - body verbatim from the legacy gate() (feature 022)."""
    if URBAN and len(M.get("wall") or []) >= 3:
        eh_wall = M["wall"]
        eh_ftpx = float(meta.get("ftpx", 1) or 1)
        eh_work = [
            (w9["x"], w9["y"])
            for k9 in ("granaries", "jetties", "storehouses", "stables", "inns", "kilns", "dye_yards", "tanning_yards", "lumber_yards")
            for w9 in M.get(k9, [])
            if isinstance(w9, dict) and "x" in w9
        ]
        eh_work += [(s9["x"], s9["y"]) for s9 in M.get("buildings", []) if s9.get("kind") in ("shop", "merchant", "inn", "stables")]
        if eh_work:
            eh_reach = 400.0 / eh_ftpx
            eh_bad = []
            for b9 in M.get("buildings", []):
                if b9.get("kind") not in DWELLING_KINDS or point_in_poly(b9["x"], b9["y"], eh_wall):
                    continue
                if min(math.hypot(b9["x"] - wx9, b9["y"] - wy9) for wx9, wy9 in eh_work) > eh_reach:
                    eh_bad.append((round(b9["x"]), round(b9["y"])))
            check(
                "extramural_housing_serves_its_work",
                len(eh_bad) <= 2,
                f"{len(eh_bad)} extramural dwelling(s) more than 400 ft from any workplace, e.g. {sorted(set(eh_bad))[:3]} - housing outside "
                f"the wall exists to put hands next to the quay, the granaries or the gate market; move the rows to the works they serve "
                f"(or the households belong inside the wall)",
            )
    return _kept(locals(), ('b9', 'eh_bad', 'eh_ftpx', 'eh_reach', 'eh_wall', 'eh_work', 'k9', 's9', 'w9', 'wx9', 'wy9'))


# THE FUNERARY GROUND STARTS AT THE WALL AND RUNS OUTWARD (GM 2026-08-10, researched; the
# why and the sources are in research/cities/capitals.md "How far outside the wall does the
# funerary ground sit?"). Nothing in the record holds it far off: ritual pollution is a
# BINARY satisfied by being outside at all (Kyoto's Injo-ji stood ON the Odoi rampart and
# marked the boundary of the living), fire is worth 50 ft by code and was never a siting
# driver at all (Edo cremated on open pyres inside its own temple precincts for 250 years
# and moved them in 1873 for the STENCH), and what actually set the distance was worthless
# ground on the road out of the gate. In every attested case the complex's ENTRANCE is at or
# just past the wall and the field runs outward - so a compact feature at 900+ ft is drawing
# the FAR end of a historical site at its NEAR end, which is what made the capital's read
# unmotivated.


def _seg_0374__funerary_ground_within_reach(
    *,
    M: Any = _UNBOUND,
    URBAN: Any = _UNBOUND,
    c9: Any = _UNBOUND,
    check: Any = _UNBOUND,
    f9: Any = _UNBOUND,
    fg_bad: Any = _UNBOUND,
    fg_cem: Any = _UNBOUND,
    fg_crem: Any = _UNBOUND,
    fg_d: Any = _UNBOUND,
    fg_edge: Any = _UNBOUND,
    fg_f: Any = _UNBOUND,
    fg_ftpx: Any = _UNBOUND,
    fg_k: Any = _UNBOUND,
    fg_max: Any = _UNBOUND,
    fg_min: Any = _UNBOUND,
    fg_oss: Any = _UNBOUND,
    fg_out: Any = _UNBOUND,
    fg_sites: Any = _UNBOUND,
    fg_split: Any = _UNBOUND,
    fg_wall: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    k9: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 374 (funerary_complex_is_one_ground, funerary_ground_within_reach) - body verbatim from the legacy gate() (feature 022)."""
    if URBAN and len(M.get("wall") or []) >= 3:
        fg_wall = M["wall"]
        fg_ftpx = float(meta.get("ftpx", 1) or 1)
        fg_max = (900.0 / fg_ftpx) if scale == "capital" else 1e9  # GM 2026-08-10 scoped the cap to capitals; the provincial spread is recorded, not enforced
        fg_min = 150.0 / fg_ftpx
        fg_sites = [(k9, f9) for k9 in ("cemeteries", "cremation_grounds", "ossuaries") for f9 in M.get(k9, []) if isinstance(f9, dict) and "x" in f9]
        fg_out = [(k9, f9) for k9, f9 in fg_sites if not point_in_poly(f9["x"], f9["y"], fg_wall)]
        fg_bad = []
        for fg_k, fg_f in fg_out:
            fg_d = min(seg_dist(fg_f["x"], fg_f["y"], fg_wall[i9], fg_wall[(i9 + 1) % len(fg_wall)]) for i9 in range(len(fg_wall)))
            fg_edge = fg_d - max(float(fg_f.get("w", 0)), float(fg_f.get("h", 0))) / 2  # the NEAR edge, not the centre
            if fg_edge > fg_max or fg_edge < fg_min:
                fg_bad.append((fg_k, round(fg_f["x"]), round(fg_f["y"]), round(fg_edge * fg_ftpx)))
        check(
            "funerary_ground_within_reach",
            not fg_bad,
            f"funerary feature(s) at the wrong reach (key, x, y, ft from the wall; want {round(fg_min * fg_ftpx)}-{round(fg_max * fg_ftpx)}): {fg_bad[:4]} - "
            f"the complex BEGINS just past the wall on the road out of a gate and runs outward; nothing holds it further off "
            f"(pollution is satisfied by being outside at all, and a pyre's codified setback is 50 ft)",
        )
        # ...and the three sit as ONE complex: Edo's north gate held burial ground, crematory and
        # pauper mound within ~290 ft of each other, entered through one gate-temple.
        fg_crem = [f9 for k9, f9 in fg_out if k9 == "cremation_grounds"]
        fg_oss = [f9 for k9, f9 in fg_out if k9 == "ossuaries"]
        fg_cem = [f9 for k9, f9 in fg_out if k9 == "cemeteries"]
        if fg_crem and fg_cem:
            fg_split = []
            for fg_f in fg_crem + fg_oss:
                if min(math.hypot(fg_f["x"] - c9["x"], fg_f["y"] - c9["y"]) for c9 in fg_cem) > 600.0 / fg_ftpx:
                    fg_split.append((round(fg_f["x"]), round(fg_f["y"])))
            check(
                "funerary_complex_is_one_ground",
                not fg_split,
                f"crematory/ossuary standing apart from the burial ground it serves: {fg_split[:3]} - the three are ONE complex on one "
                f"outbound road (Kozukappara held all three within ~290 ft); draw them together with the marker temple at the near end",
            )
    return _kept(
        locals(), ('c9', 'f9', 'fg_bad', 'fg_cem', 'fg_crem', 'fg_d', 'fg_edge', 'fg_f', 'fg_ftpx', 'fg_k', 'fg_max', 'fg_min', 'fg_oss', 'fg_out', 'fg_sites', 'fg_split', 'fg_wall', 'i9', 'k9')
    )


# A STREET EARNS ITS LENGTH ON BOTH SIDES (GM 2026-08-10: "several city streets extend out
# into empty space with nothing on either side of them and also not leading to anywhere...
# this is essentially a road to nowhere check"). `city_streets_have_buildings` measures ONE
# side and excuses frontage onto claimed open ground, which is right for a street along a
# drill ground or a firebreak - but a long stretch bare on BOTH sides is a street nobody
# walks, and the GM accepts that placement order may lay one down before that is knowable,
# so the CHECK is the backstop. Claimed ground does not excuse this one: the point is that
# the street serves nothing, not that the ground beside it is spoken for.


def _seg_0375__city_streets_serve_both_sides(
    *,
    M: Any = _UNBOUND,
    URBAN: Any = _UNBOUND,
    a9: Any = _UNBOUND,
    b9: Any = _UNBOUND,
    b9p: Any = _UNBOUND,
    bs_bad: Any = _UNBOUND,
    bs_blds: Any = _UNBOUND,
    bs_grid: Any = _UNBOUND,
    bs_len: Any = _UNBOUND,
    bs_run: Any = _UNBOUND,
    bs_worst: Any = _UNBOUND,
    bx9: Any = _UNBOUND,
    by9: Any = _UNBOUND,
    check: Any = _UNBOUND,
    j9: Any = _UNBOUND,
    k9: Any = _UNBOUND,
    pts9: Any = _UNBOUND,
    st9: Any = _UNBOUND,
    t9: Any = _UNBOUND,
    x9: Any = _UNBOUND,
    y9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 375 (city_streets_serve_both_sides) - body verbatim from the legacy gate() (feature 022)."""
    if URBAN and M.get("town_streets"):
        bs_blds = [
            b9
            for k9 in (
                "buildings",
                "shops",
                "flophouses",
                "inns",
                "manors",
                "ministries",
                "religious",
                "storehouses",
                "bathhouses",
                "breweries",
                "stables",
                "kura",
                "precincts",
                "castles",
                "mausoleums",
                "granaries",
            )
            for b9 in M.get(k9, [])
            if isinstance(b9, dict) and "x" in b9
        ]
        bs_grid = GridIndex(120.0)
        for b9 in bs_blds:
            bs_grid.add(b9["x"] - 60, b9["y"] - 60, b9["x"] + 60, b9["y"] + 60, (b9["x"], b9["y"]))
        bs_bad = []
        for st9 in M["town_streets"]:
            pts9 = st9["pts"]
            bs_worst = bs_run = 0.0
            for j9 in range(len(pts9) - 1):
                a9, b9p = pts9[j9], pts9[j9 + 1]
                bs_len = math.hypot(b9p[0] - a9[0], b9p[1] - a9[1])
                for k9 in range(max(1, int(bs_len // 20)) + 1):
                    t9 = k9 / max(1, int(bs_len // 20))
                    x9, y9 = a9[0] + (b9p[0] - a9[0]) * t9, a9[1] + (b9p[1] - a9[1]) * t9
                    if any((bx9 - x9) ** 2 + (by9 - y9) ** 2 < 60 * 60 for bx9, by9 in bs_grid.near(x9, y9)):
                        bs_run = 0.0
                    else:
                        bs_run += 20.0
                        bs_worst = max(bs_worst, bs_run)
            if bs_worst >= 300:
                bs_bad.append((round(pts9[0][0]), round(pts9[0][1]), round(bs_worst)))
        check(
            "city_streets_serve_both_sides",
            not bs_bad,
            f"city street(s) with a long stretch bare on BOTH sides (start x, y, px): {bs_bad[:4]} - a street nobody fronts is a "
            f"road to nowhere; shorten it to the fabric it serves, or fill the block it opens (claimed open ground does not excuse "
            f"this one - the objection is that the street serves nothing)",
        )
    return _kept(locals(), ('a9', 'b9', 'b9p', 'bs_bad', 'bs_blds', 'bs_grid', 'bs_len', 'bs_run', 'bs_worst', 'bx9', 'by9', 'j9', 'k9', 'pts9', 'st9', 't9', 'x9', 'y9'))


# A SHOP FACES THE WAY IT FRONTS (GM 2026-08-10: "at the northern gate market there is a row
# of several merchant shops, and then just one of those shops is oriented facing away from
# the road"). A storefront IS its street face - the noren, the counter and the goods are on
# that side - so a shop within a frontage band of a way must open toward it. The glyph's
# front is local +y, as with the theater stage, so after `rot` it points (-sin, cos).
# Placement gets this right when it seats the file; what it cannot see is a LATER re-lay
# that moves the way, or a hand-placed file whose setback sign flips one seat.


def _seg_0376__r9(*, M: Any = _UNBOUND, r9: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 376 (r9, sf_ways) - body verbatim from the legacy gate() (feature 022)."""
    sf_ways = ([("road", M["road"], float(M.get("road_width", 26)))] if M.get("road") else []) + [
        ("road", r9["pts"] if isinstance(r9, dict) else r9, float(r9.get("w", 20)) if isinstance(r9, dict) else 20.0) for r9 in M.get("roads", [])
    ]
    return _kept(locals(), ('r9', 'sf_ways'))


def _seg_0377__s9(*, M: Any = _UNBOUND, s9: Any = _UNBOUND, sf_ways: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 377 (s9, sf_ways) - body verbatim from the legacy gate() (feature 022)."""
    sf_ways += [("street", s9["pts"], float(s9.get("w", 18))) for s9 in M.get("town_streets", [])]
    return _kept(locals(), ('s9', 'sf_ways'))


def _seg_0378__frontage_shops_face_their_way(
    *,
    M: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d9: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    sf_b: Any = _UNBOUND,
    sf_bad: Any = _UNBOUND,
    sf_best: Any = _UNBOUND,
    sf_cp: Any = _UNBOUND,
    sf_d: Any = _UNBOUND,
    sf_l: Any = _UNBOUND,
    sf_ox: Any = _UNBOUND,
    sf_oy: Any = _UNBOUND,
    sf_pts: Any = _UNBOUND,
    sf_th: Any = _UNBOUND,
    sf_vx: Any = _UNBOUND,
    sf_vy: Any = _UNBOUND,
    sf_w: Any = _UNBOUND,
    sf_ways: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 378 (frontage_shops_face_their_way) - body verbatim from the legacy gate() (feature 022)."""
    if sf_ways:
        sf_bad = []
        for sf_b in M.get("buildings", []) + M.get("shops", []):
            if not isinstance(sf_b, dict) or sf_b.get("kind") not in ("shop", "merchant"):
                continue
            sf_best = (1e9, (0.0, 0.0), 0.0)
            for _sf_kind, sf_pts, sf_w in sf_ways:
                for i9 in range(len(sf_pts) - 1):
                    d9 = seg_dist(sf_b["x"], sf_b["y"], sf_pts[i9], sf_pts[i9 + 1])
                    if d9 < sf_best[0]:
                        sf_best = (d9, seg_closest(sf_b["x"], sf_b["y"], sf_pts[i9], sf_pts[i9 + 1]), sf_w)
            sf_d, sf_cp, sf_w = sf_best
            if sf_d > sf_w / 2 + 40:
                continue  # not a frontage shop - an interior stall owes the way nothing
            sf_th = math.radians(float(sf_b.get("rot", 0.0)))
            sf_ox, sf_oy = -math.sin(sf_th), math.cos(sf_th)
            sf_vx, sf_vy = sf_cp[0] - sf_b["x"], sf_cp[1] - sf_b["y"]
            sf_l = math.hypot(sf_vx, sf_vy) or 1.0
            if (sf_ox * sf_vx + sf_oy * sf_vy) / sf_l < -0.3:
                sf_bad.append((round(sf_b["x"]), round(sf_b["y"])))
        check(
            "frontage_shops_face_their_way",
            not sf_bad,
            f"shop(s) turned away from the way they front (x, y): {sorted(set(sf_bad))[:4]} - a storefront IS its street face "
            f"(noren, counter, goods); flip the seat's rot by 180 deg, or move the shop off the frontage band if it is meant to be an interior stall",
        )
    return _kept(locals(), ('_sf_kind', 'd9', 'i9', 'sf_b', 'sf_bad', 'sf_best', 'sf_cp', 'sf_d', 'sf_l', 'sf_ox', 'sf_oy', 'sf_pts', 'sf_th', 'sf_vx', 'sf_vy', 'sf_w'))


# A SLUICE GATE SITS ON ITS CHANNEL'S CENTERLINE (GM 2026-08-10, after the same defect
# recurred across several re-lays: "the northern sluice gate is still misaligned with the
# irrigated channel that it is gating... I know we have automated checks for this, so I'm
# not sure how this keeps happening over and over again"). It kept happening because
# `sluice_gates_on_water` measures to the BANK: a gate 15.8px from the centerline of a 22px
# channel sits 4.8px past the bank, inside that rule's 6px tolerance, and passed - while
# reading as a frame floating beside the water. A sluice's frame spans BANK TO BANK, so the
# only correct seat is the centerline itself. Tolerance is a fraction of the channel's own
# half-width (a wide river's gate may sit a little off; a narrow ditch's may not) with a
# small absolute floor for the linework.


def _seg_0379__cn9(*, M: Any = _UNBOUND, cn9: Any = _UNBOUND, w9: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 379 (cn9, sc_waters, w9) - body verbatim from the legacy gate() (feature 022)."""
    sc_waters = [(w9["poly"], float(w9.get("w", 9))) for w9 in M.get("streams", [])] + [(cn9["poly"], float(cn9.get("w", 12))) for cn9 in M.get("canals", [])]
    return _kept(locals(), ('cn9', 'sc_waters', 'w9'))


def _seg_0380__ch9(*, M: Any = _UNBOUND, ch9: Any = _UNBOUND, sc_waters: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 380 (ch9, sc_waters) - body verbatim from the legacy gate() (feature 022)."""
    sc_waters += [(ch9["poly"], float(ch9.get("w", 2.5))) for ch9 in M.get("channels", []) if ch9.get("poly")]
    return _kept(locals(), ('ch9', 'sc_waters'))


def _seg_0381__sc_waters(*, M: Any = _UNBOUND, sc_waters: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 381 (sc_waters) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("moat"):
        sc_waters.append((list(M["moat"]) + [M["moat"][0]], float(M.get("moat_width", 22))))
    return _kept(locals(), ('sc_waters',))


def _seg_0382__sluice_gates_centered_on_their_channel(
    *,
    M: Any = _UNBOUND,
    check: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    sc_bad: Any = _UNBOUND,
    sc_best: Any = _UNBOUND,
    sc_d: Any = _UNBOUND,
    sc_w: Any = _UNBOUND,
    sc_waters: Any = _UNBOUND,
    sg9: Any = _UNBOUND,
    wp9: Any = _UNBOUND,
    ww9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 382 (sluice_gates_centered_on_their_channel) - body verbatim from the legacy gate() (feature 022)."""
    if sc_waters and M.get("sluice_gates"):
        sc_bad = []
        for sg9 in M["sluice_gates"]:
            sc_best = min((min(seg_dist(sg9["x"], sg9["y"], wp9[i9], wp9[i9 + 1]) for i9 in range(len(wp9) - 1)), ww9) for wp9, ww9 in sc_waters)
            sc_d, sc_w = sc_best
            if sc_d > max(3.0, sc_w * 0.3):
                sc_bad.append((round(sg9["x"]), round(sg9["y"]), round(sc_d, 1)))
        check(
            "sluice_gates_centered_on_their_channel",
            not sc_bad,
            f"sluice gate(s) off their channel's CENTERLINE (x, y, px off): {sc_bad[:4]} - the frame spans bank to bank, so the "
            f"gate's center belongs ON the centerline; snap it to the nearest point of the watercourse polyline (being merely "
            f"inside the water's band is what let this recur - sluice_gates_on_water measures to the bank)",
        )
    return _kept(locals(), ('i9', 'sc_bad', 'sc_best', 'sc_d', 'sc_w', 'sg9', 'wp9', 'ww9'))


# A ROAD DOES NOT SIMPLY STOP (GM 2026-08-10: "the road leading to the southwest gate comes a
# little way into the city and then just stops... we expect that caravans coming into the city
# would need to be able to take this road in order to reach the castle keep"). A trunk road
# exists to carry traffic THROUGH: each end must leave the map, meet another road, or join a
# street/ring bed a wagon can turn onto. An end that dies in open ground is a road to nowhere.


def _seg_0383__roads_join_the_network(
    *,
    M: Any = _UNBOUND,
    b9: Any = _UNBOUND,
    bh9: Any = _UNBOUND,
    cg9: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cs9: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    j9: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    o9: Any = _UNBOUND,
    r9: Any = _UNBOUND,
    rj_E: Any = _UNBOUND,
    rj_H: Any = _UNBOUND,
    rj_W: Any = _UNBOUND,
    rj_bad: Any = _UNBOUND,
    rj_beds: Any = _UNBOUND,
    rj_i: Any = _UNBOUND,
    rj_pts: Any = _UNBOUND,
    rj_ways: Any = _UNBOUND,
    s9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 383 (roads_join_the_network) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("roads") or M.get("road"):
        rj_ways = [r9["pts"] if isinstance(r9, dict) else r9 for r9 in M.get("roads", [])] + ([M["road"]] if M.get("road") else [])
        rj_beds = [(s9["pts"], float(s9.get("w", 18)) / 2) for s9 in M.get("town_streets", [])]
        if M.get("ring_road"):
            rj_beds.append((list(M["ring_road"]) + [M["ring_road"][0]], float(M.get("ring_road_width", 15)) / 2))
        rj_W, rj_H = float(meta.get("W", 1820)), float(meta.get("H", 1180))
        rj_bad = []
        for rj_i, rj_pts in enumerate(rj_ways):
            if len(rj_pts) < 2:
                continue
            for rj_E in (rj_pts[0], rj_pts[-1]):
                if rj_E[0] <= 8 or rj_E[1] <= 8 or rj_E[0] >= rj_W - 8 or rj_E[1] >= rj_H - 8:
                    continue  # leaves the map
                if any(min(seg_dist(rj_E[0], rj_E[1], o9[i9], o9[i9 + 1]) for i9 in range(len(o9) - 1)) <= 20 for j9, o9 in enumerate(rj_ways) if j9 != rj_i and len(o9) >= 2):
                    continue  # meets another road
                if any(min(seg_dist(rj_E[0], rj_E[1], b9[i9], b9[i9 + 1]) for i9 in range(len(b9) - 1)) <= bh9 + 14 for b9, bh9 in rj_beds if len(b9) >= 2):
                    continue  # joins a street or the ring
                # ...and a castle approach legitimately ENDS at the gate it serves: the ote-suji
                # stops at the ote-mon and the karamete road at the postern tower, exactly as a
                # real approach does. That is a terminus with a reason, not a road to nowhere.
                if any(
                    math.hypot(rj_E[0] - cg9[0], rj_E[1] - cg9[1]) <= 60 for cs9 in M.get("castles", []) for cg9 in (list(cs9.get("gates") or []) + ([cs9["karamete"]] if cs9.get("karamete") else []))
                ):
                    continue
                rj_bad.append((round(rj_E[0]), round(rj_E[1])))
        check(
            "roads_join_the_network",
            not rj_bad,
            f"road end(s) stopping in open ground (x, y): {sorted(set(rj_bad))[:4]} - a trunk road carries traffic THROUGH: run it "
            f"off the map, into another road, or onto a street/ring bed a wagon can turn from (a gate road must reach the network "
            f"that serves the castle and the markets)",
        )
    return _kept(locals(), ('b9', 'bh9', 'cg9', 'cs9', 'i9', 'j9', 'o9', 'r9', 'rj_E', 'rj_H', 'rj_W', 'rj_bad', 'rj_beds', 'rj_i', 'rj_pts', 'rj_ways', 's9'))


# NO WAY STANDS IN WATER WITHOUT A DECK (GM 2026-08-10: "roads should not overlap with water
# without a bridge present"). `roads_bridge_water` already demands a deck wherever a CARRIED
# way's centerline CROSSES a watercourse's centerline - but it reads only the ways
# bridge_carried_ways names (the trunk roads, streets and the ring), and it tests crossings
# rather than OVERLAP. So an alley whose bed laps a stream's bed, or a way that runs into the
# water and stops, sails past it: the capital's wharf shore path lay in the moat drain for
# 40 px with no plank. This one samples EVERY drawn way against every watercourse using both
# BEDS' widths - the question a reader asks of the picture is whether the paving and the water
# occupy the same ground, not whether two abstract centerlines intersect.


def _seg_0384__cn9_1(*, M: Any = _UNBOUND, cn9: Any = _UNBOUND, w9: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 384 (cn9, w9, wd_waters) - body verbatim from the legacy gate() (feature 022)."""
    wd_waters = [(w9["poly"], float(w9.get("w", 9))) for w9 in M.get("streams", [])] + [(cn9["poly"], float(cn9.get("w", 12))) for cn9 in M.get("canals", [])]
    return _kept(locals(), ('cn9', 'w9', 'wd_waters'))


def _seg_0385__wd_waters(*, M: Any = _UNBOUND, wd_waters: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 385 (wd_waters) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("moat"):
        wd_waters.append((list(M["moat"]) + [M["moat"][0]], float(M.get("moat_width", 22))))
    return _kept(locals(), ('wd_waters',))


def _seg_0386__cs9(*, M: Any = _UNBOUND, cs9: Any = _UNBOUND, wd_waters: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 386 (cs9, wd_waters) - body verbatim from the legacy gate() (feature 022)."""
    for cs9 in M.get("castles", []):
        if cs9.get("moat"):
            wd_waters.append((list(cs9["moat"]) + [cs9["moat"][0]], float(cs9.get("moat_width", 22))))
    return _kept(locals(), ('cs9', 'wd_waters'))


def _seg_0387__ways_cross_water_on_a_deck(
    *,
    M: Any = _UNBOUND,
    a9: Any = _UNBOUND,
    a9p: Any = _UNBOUND,
    b9: Any = _UNBOUND,
    b9p: Any = _UNBOUND,
    check: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    j9: Any = _UNBOUND,
    k9: Any = _UNBOUND,
    l9: Any = _UNBOUND,
    r9: Any = _UNBOUND,
    s9: Any = _UNBOUND,
    t9: Any = _UNBOUND,
    wd_bad: Any = _UNBOUND,
    wd_bridges: Any = _UNBOUND,
    wd_kind: Any = _UNBOUND,
    wd_len: Any = _UNBOUND,
    wd_pts: Any = _UNBOUND,
    wd_w: Any = _UNBOUND,
    wd_waters: Any = _UNBOUND,
    wd_ways: Any = _UNBOUND,
    wp9: Any = _UNBOUND,
    ww9: Any = _UNBOUND,
    x9: Any = _UNBOUND,
    y9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 387 (ways_cross_water_on_a_deck) - body verbatim from the legacy gate() (feature 022)."""
    if wd_waters:
        wd_ways = ([("road", M["road"], float(M.get("road_width", 26)))] if M.get("road") else []) + [
            ("road", r9["pts"] if isinstance(r9, dict) else r9, float(r9.get("w", 20)) if isinstance(r9, dict) else 20.0) for r9 in M.get("roads", [])
        ]
        wd_ways += [("street", s9["pts"], float(s9.get("w", 18))) for s9 in M.get("town_streets", [])]
        wd_ways += [("alley", a9["pts"], float(a9.get("w", 10))) for a9 in M.get("alleys", [])]
        wd_ways += [("lane", l9["pts"] if isinstance(l9, dict) else l9, float(l9.get("w", 8)) if isinstance(l9, dict) else 8.0) for l9 in M.get("lanes", [])]
        if M.get("ring_road"):
            wd_ways.append(("ring road", list(M["ring_road"]) + [M["ring_road"][0]], float(M.get("ring_road_width", 15))))
        wd_bridges = M.get("bridges", [])
        wd_bad = []
        for wd_kind, wd_pts, wd_w in wd_ways:
            if len(wd_pts) < 2:
                continue
            for i9 in range(len(wd_pts) - 1):
                a9p, b9p = wd_pts[i9], wd_pts[i9 + 1]
                wd_len = math.hypot(b9p[0] - a9p[0], b9p[1] - a9p[1])
                for k9 in range(max(1, int(wd_len // 8)) + 1):
                    t9 = k9 / max(1, int(wd_len // 8))
                    x9, y9 = a9p[0] + (b9p[0] - a9p[0]) * t9, a9p[1] + (b9p[1] - a9p[1]) * t9
                    for wp9, ww9 in wd_waters:
                        if min(seg_dist(x9, y9, wp9[j9], wp9[j9 + 1]) for j9 in range(len(wp9) - 1)) < ww9 / 2 + wd_w / 2 - 3 and not any(
                            math.hypot(b9["x"] - x9, b9["y"] - y9) <= max(46.0, float(b9.get("span", 30))) for b9 in wd_bridges
                        ):
                            wd_bad.append((wd_kind, round(x9), round(y9)))
                        break
        check(
            "ways_cross_water_on_a_deck",
            not wd_bad,
            f"way(s) standing in water with no deck under them: {sorted(set(wd_bad))[:4]} - paving and water cannot share ground; "
            f"carry the way over on a bridge (s.bridges() after all ways and water, or a hand plank at the computed crossing), or route it clear of the bank",
        )
    return _kept(locals(), ('a9', 'a9p', 'b9', 'b9p', 'i9', 'j9', 'k9', 'l9', 'r9', 's9', 't9', 'wd_bad', 'wd_bridges', 'wd_kind', 'wd_len', 'wd_pts', 'wd_w', 'wd_ways', 'wp9', 'ww9', 'x9', 'y9'))


# A CAPITAL'S TRADES SCALE - IN FOUR DIFFERENT WAYS (GM question 2026-08-10, researched;
# the WHY, with sources, is in research/cities/capitals.md "Do a capital's trades and
# funerary program scale from a provincial city's?"). Nothing here is "same as a city":
#   LINEAR (multiply, same size): bathhouses at Edo's attested 1-per-2,000 sento ratio;
#     pawnshops at 1-per-400 (drawn representatively - 2-3 with their pledge-kura courts,
#     the rest implied in the shop rows); fire towers, linear in AREA on a fixed watch
#     radius (Kaifeng posted one every 300 paces from 1023).
#   SUBLINEAR (works consolidate): kilns cluster into a quarter beside each other, not
#     scattered; ONE cremation ground however big the city (Edo ran a million residents'
#     cremation through a handful of temple kasoba).
#   SUPERLINEAR (capital-only): permanent theater - Kaifeng's 50+ goulan against a
#     provincial town's touring stage - and the domain school.
#   FIXED (one per SEAT): the pauper's ossuary, by Song edict of 1104 (a louzeyuan in every
#     prefecture and county, regardless of size), and the primary mausoleum.
# INFERENCE, flagged: the kiln count of 2, the dyers'-row lot count, the oil-press band.


def _seg_0388__capital_trade_counts_scaled(
    *,
    M: Any = _UNBOUND,
    b: Any = _UNBOUND,
    check: Any = _UNBOUND,
    k: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    tc_bad: Any = _UNBOUND,
    tc_bldg: Any = _UNBOUND,
    tc_have: Any = _UNBOUND,
    tc_pop: Any = _UNBOUND,
    tc_want: Any = _UNBOUND,
    v: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 388 (capital_trade_counts_scaled) - body verbatim from the legacy gate() (feature 022)."""
    if scale == "capital" and meta.get("population"):
        tc_pop = float(meta["population"])
        tc_bldg = collections.Counter(b.get("kind") for b in M.get("buildings", []))
        tc_have = {
            "bathhouses": len(M.get("bathhouses", [])) + tc_bldg.get("bathhouse", 0),
            "pawnshops": len(M.get("pawnshops", [])) + tc_bldg.get("pawnshop", 0),
            "breweries": len(M.get("breweries", [])) + tc_bldg.get("brewery", 0),
            "kilns": len(M.get("kilns", [])),
            "dye_yards": len(M.get("dye_yards", [])),
            "fire_towers": len(M.get("fire_towers", [])),
        }
        tc_want = {
            "bathhouses": (max(3, round(tc_pop / 2400)), "Edo's 523 sento per 1.1M - LINEAR, same size, more of them"),
            "pawnshops": (2, "Edo's 1-per-400 drawn representatively: 2-3 with pledge-kura courts, the rest implied in the rows"),
            "breweries": (2, "capacity is linear but brewing scaled by adding houses, not by doubling the hall (Takayama's 56 licensed brewers were mostly shopfronts)"),
            "kilns": (2, "a kiln is a QUARTER - the capital's second works stands beside the first, sharing the clay pit and fuel road (INFERENCE: the count of 2; the cluster form is attested)"),
            "dye_yards": (3, "a castle town lays out a Konya-machi: 3-5 contiguous dyer lots on one downstream bank, not one bigger yard (INFERENCE: the lot count)"),
            "fire_towers": (max(6, round(tc_pop / 1200)), "a fixed watch radius over a bigger built area (Kaifeng: a tower every 300 paces)"),
        }
        tc_bad = [f"{k}: {tc_have[k]} vs >= {v[0]} ({v[1]})" for k, v in tc_want.items() if tc_have[k] < v[0]]
        check(
            "capital_trade_counts_scaled",
            not tc_bad,
            f"capital trade counts below the researched floor: {tc_bad[:3]} - a capital is not a provincial city with a bigger wall; "
            f"see research/cities/capitals.md for which trades multiply, which consolidate, and which are capital-only",
        )
    return _kept(locals(), ('b', 'k', 'tc_bad', 'tc_bldg', 'tc_have', 'tc_pop', 'tc_want', 'v'))


# THE FRAME HUGS THE CONTENT (GM 2026-08-10: "it doesn't look like we're doing [cropping] on
# the south or east sides, especially the south"). A crop override outlives the feature it
# was added for - Shiro Daika carried south=240/east=700 from a layout three re-lays old -
# and dead margin reads as a map that forgot to finish. Each side of the view must have real
# DRAWN CONTENT within a reasonable band of the edge; linear features running off-map (the
# river, a road) do not count as content for this - they leave whether or not the frame follows.


def _seg_0389__fr_view(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 389 (fr_view) - body verbatim from the legacy gate() (feature 022)."""
    fr_view = meta.get("view")
    return _kept(locals(), ('fr_view',))


def _seg_0390__map_frame_hugs_its_content(
    *,
    M: Any = _UNBOUND,
    check: Any = _UNBOUND,
    fr_bad: Any = _UNBOUND,
    fr_band: Any = _UNBOUND,
    fr_h: Any = _UNBOUND,
    fr_hh: Any = _UNBOUND,
    fr_hw: Any = _UNBOUND,
    fr_k: Any = _UNBOUND,
    fr_pts: Any = _UNBOUND,
    fr_r: Any = _UNBOUND,
    fr_v: Any = _UNBOUND,
    fr_view: Any = _UNBOUND,
    fr_w: Any = _UNBOUND,
    fr_x: Any = _UNBOUND,
    fr_y: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    p: Any = _UNBOUND,
    q: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 390 (map_frame_hugs_its_content) - body verbatim from the legacy gate() (feature 022)."""
    if fr_view and len(fr_view) == 4:
        fr_x, fr_y, fr_w, fr_h = fr_view
        fr_band = 150.0 / float(meta.get("ftpx", 1) or 1)  # 150 real ft: the GM's ~100 ft target plus the crop margin's own slack (2026-08-10)
        fr_pts: list[tuple[float, float]] = []  # type: ignore[no-redef]
        for fr_k, fr_v in M.items():
            if fr_k in ("meta", "title", "scalebar", "districts") or not isinstance(fr_v, list):
                continue
            for fr_r in fr_v:
                if isinstance(fr_r, dict) and isinstance(fr_r.get("x"), (int, float)):
                    # the EXTENT, not the centre: a kiln's yard reaches 20px past its record, and
                    # the crop frames boxes - measuring centres reads a tight frame as loose
                    fr_hw = float(fr_r.get("w", 0) or fr_r.get("r", 0) * 2 or 0) / 2
                    fr_hh = float(fr_r.get("h", 0) or fr_r.get("r", 0) * 2 or 0) / 2
                    fr_pts += [(fr_r["x"] - fr_hw, fr_r["y"] - fr_hh), (fr_r["x"] + fr_hw, fr_r["y"] + fr_hh)]
                elif fr_k == "labels" and isinstance(fr_r, (list, tuple)) and len(fr_r) >= 4:
                    # a CAPTION is drawn ink and the frame must contain it (labels_within_image),
                    # so a label box legitimately sets an edge - the crop's own box list includes it
                    fr_pts += [(float(fr_r[0]), float(fr_r[1])), (float(fr_r[2]), float(fr_r[3]))]
                elif fr_k in ("alleys", "town_streets", "torii") and isinstance(fr_r, dict) and fr_r.get("pts"):
                    # a drawn WAY inside the frame is content (its end is a real place); the
                    # river/road polylines are not - they leave the map whatever the frame does,
                    # and districts are declarations, not ink
                    fr_pts += [(q[0], q[1]) for q in fr_r["pts"] if fr_x <= q[0] <= fr_x + fr_w and fr_y <= q[1] <= fr_y + fr_h]
        if fr_pts:
            fr_bad = []
            if not any(p[1] > fr_y + fr_h - fr_band for p in fr_pts):
                fr_bad.append("south")
            if not any(p[1] < fr_y + fr_band for p in fr_pts):
                fr_bad.append("north")
            if not any(p[0] > fr_x + fr_w - fr_band for p in fr_pts):
                fr_bad.append("east")
            if not any(p[0] < fr_x + fr_band for p in fr_pts):
                fr_bad.append("west")
            check(
                "map_frame_hugs_its_content",
                not fr_bad,
                f"map frame carrying dead margin on the {fr_bad} side(s) - no drawn feature within 150 ft of the edge; "
                f"drop the stale per-side crop override (s.crop_city(south=..., east=...)) and let the frame follow the content",
            )
    return _kept(locals(), ('fr_bad', 'fr_band', 'fr_h', 'fr_hh', 'fr_hw', 'fr_k', 'fr_pts', 'fr_r', 'fr_v', 'fr_w', 'fr_x', 'fr_y', 'p', 'q'))


# NO DUNG AT A SAMURAI'S FRONT DOOR (GM 2026-08-10: "cattle yards should NOT go directly in
# front of the gates of samurai estates. No samurai wants literal piles of dung outside
# their front door. I'd expect that oxen yard to be next to the caravan inn anyway.")
# A stable/ox yard is a working animal ground - straw, dung, flies, noise - and the ONE
# place it may not stand is the approach a walled compound's gate opens onto. The rule
# measures to the GATE POINT (gate_dir names the side), not the compound's center, because
# the offense is the approach, not the neighborhood: a yard behind an estate's back wall
# is ordinary city ground. Yards belong with the traffic they serve - the caravan inn and
# its relay stables - which is where every other yard on this map already sits.


def _seg_0391__ay_bad() -> dict[str, Any]:
    """Gate segment 391 (ay_bad) - body verbatim from the legacy gate() (feature 022)."""
    ay_bad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('ay_bad',))


def _seg_0392__ay_reach(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 392 (ay_reach) - body verbatim from the legacy gate() (feature 022)."""
    ay_reach = 240.0 / float(meta.get("ftpx", 1) or 1)  # 240 real ft of clear approach
    return _kept(locals(), ('ay_reach',))


def _seg_0393__ay_bad_1(
    *,
    M: Any = _UNBOUND,
    ay_bad: Any = _UNBOUND,
    ay_c: Any = _UNBOUND,
    ay_g: Any = _UNBOUND,
    ay_gd: Any = _UNBOUND,
    ay_h: Any = _UNBOUND,
    ay_key: Any = _UNBOUND,
    ay_r: Any = _UNBOUND,
    ay_reach: Any = _UNBOUND,
    ay_w: Any = _UNBOUND,
    ay_y: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 393 (ay_bad, ay_c, ay_g, ay_gd) - body verbatim from the legacy gate() (feature 022)."""
    for ay_c in M.get("manors", []) + M.get("merchant_estates", []):
        ay_gd = ay_c.get("gate_dir")
        if not ay_gd:
            continue
        ay_w, ay_h = ay_c.get("w", 0), ay_c.get("h", 0)
        ay_g = {
            "west": (ay_c["x"] - ay_w / 2, ay_c["y"]),
            "east": (ay_c["x"] + ay_w / 2, ay_c["y"]),
            "north": (ay_c["x"], ay_c["y"] - ay_h / 2),
            "south": (ay_c["x"], ay_c["y"] + ay_h / 2),
        }.get(ay_gd)
        if ay_g is None:
            continue
        for ay_key in ("stable_yards", "byres", "animal_grounds"):
            for ay_y in M.get(ay_key, []):  # every yard key holds records, never raw polygons
                ay_r = float(ay_y.get("r", 0) or max(ay_y.get("w", 0), ay_y.get("h", 0)) / 2)
                if math.hypot(ay_y["x"] - ay_g[0], ay_y["y"] - ay_g[1]) - ay_r < ay_reach:
                    ay_bad.append((ay_key, round(ay_y["x"]), round(ay_y["y"]), ay_c.get("label") or "a walled compound"))
    return _kept(locals(), ('ay_bad', 'ay_c', 'ay_g', 'ay_gd', 'ay_h', 'ay_key', 'ay_r', 'ay_w', 'ay_y'))


def _seg_0394__animal_yards_clear_of_compound_gates(*, ay_bad: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 394 (animal_yards_clear_of_compound_gates) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "animal_yards_clear_of_compound_gates",
        not ay_bad,
        f"animal yard(s) standing on a walled compound's gate approach: {sorted(set(ay_bad))[:4]} - straw, dung and flies do not "
        f"belong at a samurai's front door; move the yard to the caravan inn and relay stables it serves, or behind the compound's back wall",
    )
    return _kept(locals(), ())


# EXTRAMURAL FEATURES STAY TETHERED TO THE CITY (GM 2026-08-10: "the kiln works is wayyyyy
# out in the middle of nowhere... the gate markets look pretty far from the actual gates").
# Everything outside a wall belongs to something: a gate's market strings along its
# approach road FROM the gate, the nuisance works sit on the near ground the city can still
# police and reach, and the wharf trades belong to the landing. So an outside feature must
# be within reach of a GATE, of the WHARF works, or of a road it stands on - a feature that
# is near none of the three is floating, whatever its bearing from the city.


def _seg_0395__extramural_features_tethered(
    *,
    M: Any = _UNBOUND,
    b: Any = _UNBOUND,
    check: Any = _UNBOUND,
    g: Any = _UNBOUND,
    gm_allow: Any = _UNBOUND,
    gm_bad: Any = _UNBOUND,
    gm_g: Any = _UNBOUND,
    gm_near: Any = _UNBOUND,
    gm_shops: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    j: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    r: Any = _UNBOUND,
    rp: Any = _UNBOUND,
    wx: Any = _UNBOUND,
    wy: Any = _UNBOUND,
    xm_bad: Any = _UNBOUND,
    xm_f: Any = _UNBOUND,
    xm_ftpx: Any = _UNBOUND,
    xm_gate_reach: Any = _UNBOUND,
    xm_key: Any = _UNBOUND,
    xm_road_reach: Any = _UNBOUND,
    xm_roads: Any = _UNBOUND,
    xm_wall: Any = _UNBOUND,
    xm_wharf: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 395 (extramural_features_tethered, gate_markets_start_at_their_gate) - body verbatim from the legacy gate() (feature 022)."""
    if len(M.get("wall") or []) >= 3 and M.get("gates"):
        xm_wall = M["wall"]
        xm_ftpx = float(meta.get("ftpx", 1) or 1)
        xm_gate_reach = 900.0 / xm_ftpx  # 900 real ft: the gate market's own strip
        xm_road_reach = 150.0 / xm_ftpx  # a works ON its haul road, not adrift beside it
        xm_wharf = [(j["x"], j["y"]) if isinstance(j, dict) else (j[0], j[1]) for j in M.get("jetties", [])]
        xm_wharf += [(g["x"], g["y"]) for g in M.get("granaries", []) if isinstance(g, dict) and "x" in g]
        xm_roads = ([M["road"]] if M.get("road") else []) + [r["pts"] if isinstance(r, dict) else r for r in M.get("roads", [])]
        xm_bad = []
        for xm_key in ("kilns", "dye_yards", "tanning_yards", "lumber_yards", "shops", "inns", "stables", "flophouses"):
            for xm_f in M.get(xm_key, []):
                if not isinstance(xm_f, dict) or "x" not in xm_f or point_in_poly(xm_f["x"], xm_f["y"], xm_wall):
                    continue
                if min(math.hypot(xm_f["x"] - g[0], xm_f["y"] - g[1]) for g in M["gates"]) <= xm_gate_reach:
                    continue
                if xm_wharf and min(math.hypot(xm_f["x"] - wx, xm_f["y"] - wy) for wx, wy in xm_wharf) <= 300:
                    continue
                if xm_roads and min(min(seg_dist(xm_f["x"], xm_f["y"], rp[i9], rp[i9 + 1]) for i9 in range(len(rp) - 1)) for rp in xm_roads if len(rp) >= 2) <= xm_road_reach:
                    continue
                # ...or simply CLOSE TO THE WALL it serves. A works on the near farm ground is
                # tethered by the city's own edge even with no road under it - which is where
                # every shipped map's nuisance works actually sits: 225-1,382 ft from the wall
                # across Tango, Minami, Nagahara and the capital (measured 2026-08-10). The kiln
                # that prompted this rule stood at 1,563 ft with nothing around it, so the band
                # is drawn from the attested spread rather than picked.
                if min(seg_dist(xm_f["x"], xm_f["y"], xm_wall[i9], xm_wall[(i9 + 1) % len(xm_wall)]) for i9 in range(len(xm_wall))) <= 1450.0 / xm_ftpx:
                    continue
                xm_bad.append((xm_key, round(xm_f["x"]), round(xm_f["y"])))
        check(
            "extramural_features_tethered",
            not xm_bad,
            f"outside feature(s) adrift - not within 900 ft of a gate, on a road, or at the wharf: {sorted(set(xm_bad))[:4]} - "
            f"every extramural feature belongs to something; pull it onto its approach road (a works hauls on the road it uses), "
            f"into the gate's market strip, or to the landing",
        )
        # ...and a GATE MARKET starts AT its gate. A market strip that begins hundreds of feet
        # down the road reads as an unrelated hamlet: the stalls crowd the gate mouth because
        # that is where the toll, the inspection and the traffic are.
        gm_bad = []
        for gm_g in M["gates"]:
            gm_shops = [
                b
                for b in M.get("buildings", []) + M.get("shops", [])
                if isinstance(b, dict) and b.get("kind") in ("shop", "merchant") and not point_in_poly(b["x"], b["y"], xm_wall) and math.hypot(b["x"] - gm_g[0], b["y"] - gm_g[1]) <= xm_gate_reach
            ]
            if len(gm_shops) >= 3:
                gm_near = min(math.hypot(b["x"] - gm_g[0], b["y"] - gm_g[1]) for b in gm_shops)
                # a MOAT pushes the head of the strip out by its own width plus the bridge's
                # landing - stalls cannot stand on the crossing - so the allowance grows by the
                # moat band where one runs past this gate (the capital's N gate, 2026-08-10)
                # THE POOL'S OWN SPREAD IS THE WHOLE ANSWER (GM 2026-08-10, twice): the nearest
                # stall sits 157-273 ft from the gate at Tango, Minami and Nagahara - and those
                # are walled, moated cities with the same gate program, bridge and guard works.
                # So the moat and the furniture are ALREADY inside that figure, and the first
                # cut's mistake was adding them again on top: a 260 ft blocked band plus a
                # 280 ft market allowance let the capital's markets start 540 ft out, which is
                # exactly the 300-ish feet the GM was still seeing. One flat band, no addition.
                gm_allow = 300.0 / xm_ftpx
                if gm_near > gm_allow:
                    gm_bad.append((round(gm_g[0]), round(gm_g[1]), round(gm_near)))
        check(
            "gate_markets_start_at_their_gate",
            not gm_bad,
            f"gate market(s) whose nearest stall is far down the road (gate x, y, px): {gm_bad[:4]} - a gate market crowds the "
            f"gate mouth where the toll and the traffic are, then strings outward; move the head of the strip up to the gate",
        )
    return _kept(
        locals(),
        (
            'b',
            'g',
            'gm_allow',
            'gm_bad',
            'gm_g',
            'gm_near',
            'gm_shops',
            'i9',
            'j',
            'r',
            'rp',
            'wx',
            'wy',
            'xm_bad',
            'xm_f',
            'xm_ftpx',
            'xm_gate_reach',
            'xm_key',
            'xm_road_reach',
            'xm_roads',
            'xm_wall',
            'xm_wharf',
        ),
    )


# PUBLIC WELLS DO NOT KNOT UP (GM 2026-08-10: "several places with 4-6 wells clustered
# right next to each other... not how wells are positioned on any other map"). A public
# well serves a neighborhood, so wellheads spread out - and the whole pool agrees: every
# settled map from hamlet to provincial city maxes at FOUR wells inside a 150 real-ft
# radius (measured across all 14, 2026-08-10), while the capital's density-chasing had
# piled up NINE. The failure mode is accretion - each new well is added to fix a local
# household count, none is added against the wells already there - so the rule is a
# neighborhood CAP, not a pairwise spacing floor (a tight PAIR at a big junction is fine).


def _seg_0396__w9(*, M: Any = _UNBOUND, w9: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 396 (w9, wk_ws) - body verbatim from the legacy gate() (feature 022)."""
    wk_ws = [w9 for w9 in M.get("wells", []) if isinstance(w9, dict)]
    return _kept(locals(), ('w9', 'wk_ws'))


def _seg_0397__wells_not_clustered(
    *, check: Any = _UNBOUND, meta: Any = _UNBOUND, o9: Any = _UNBOUND, w9: Any = _UNBOUND, wk_bad: Any = _UNBOUND, wk_n: Any = _UNBOUND, wk_r: Any = _UNBOUND, wk_ws: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 397 (wells_not_clustered) - body verbatim from the legacy gate() (feature 022)."""
    if len(wk_ws) >= 5:
        wk_r = 150.0 / float(meta.get("ftpx", 1) or 1)
        wk_bad = []
        for w9 in wk_ws:
            wk_n = sum(1 for o9 in wk_ws if (w9["x"] - o9["x"]) ** 2 + (w9["y"] - o9["y"]) ** 2 <= wk_r * wk_r)
            if wk_n > 4:
                wk_bad.append((round(w9["x"]), round(w9["y"]), wk_n))
        check(
            "wells_not_clustered",
            not wk_bad,
            f"well knot(s) - more than 4 public wells inside a 150 ft radius (x, y, count): {sorted(set(wk_bad))[:4]} - a wellhead serves a NEIGHBORHOOD, so they spread; this is accretion from chasing a local household count. Widen the grid spacing over that quarter instead of stacking wells, and gate any top-up on there being no well already within the radius",
        )
    return _kept(locals(), ('o9', 'w9', 'wk_bad', 'wk_n', 'wk_r'))


# A WAY DOES NOT RUN INSIDE A ROAD'S BED (GM 2026-08-10: a service lane sat fully inside
# the Imperial road's kagi leg - two ways drawn where one exists on the ground). Sampled
# run-length of any lane/street/alley inside a road's half-width; short crossings pass.


def _seg_0398__r9_1(*, M: Any = _UNBOUND, r9: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 398 (r9, rb_roads) - body verbatim from the legacy gate() (feature 022)."""
    rb_roads = ([{"pts": M["road"], "w": M.get("road_width", 26)}] if M.get("road") else []) + [r9 if isinstance(r9, dict) else {"pts": r9, "w": 20} for r9 in M.get("roads", [])]
    return _kept(locals(), ('r9', 'rb_roads'))


def _seg_0399__rb_bad() -> dict[str, Any]:
    """Gate segment 399 (rb_bad) - body verbatim from the legacy gate() (feature 022)."""
    rb_bad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('rb_bad',))


def _seg_0400__a9_1(
    *,
    M: Any = _UNBOUND,
    a9: Any = _UNBOUND,
    b9: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    inside9: Any = _UNBOUND,
    j9: Any = _UNBOUND,
    k9: Any = _UNBOUND,
    rb_bad: Any = _UNBOUND,
    rb_kind: Any = _UNBOUND,
    rb_list: Any = _UNBOUND,
    rb_pts: Any = _UNBOUND,
    rb_roads: Any = _UNBOUND,
    rb_run: Any = _UNBOUND,
    rb_w: Any = _UNBOUND,
    rp9: Any = _UNBOUND,
    seg_len9: Any = _UNBOUND,
    steps9: Any = _UNBOUND,
    t9: Any = _UNBOUND,
    x9: Any = _UNBOUND,
    y9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 400 (a9, b9, i9, inside9) - body verbatim from the legacy gate() (feature 022)."""
    for rb_kind, rb_list in (("street", M.get("town_streets", [])), ("alley", M.get("alleys", [])), ("lane", M.get("lanes", []))):
        for rb_w in rb_list:
            rb_pts = rb_w["pts"] if isinstance(rb_w, dict) else rb_w
            rb_run = 0.0
            for i9 in range(len(rb_pts) - 1):
                a9, b9 = rb_pts[i9], rb_pts[i9 + 1]
                seg_len9 = math.hypot(b9[0] - a9[0], b9[1] - a9[1])
                steps9 = max(1, int(seg_len9 // 15))
                for j9 in range(steps9 + 1):
                    t9 = j9 / steps9
                    x9, y9 = a9[0] + (b9[0] - a9[0]) * t9, a9[1] + (b9[1] - a9[1]) * t9
                    inside9 = any(min(seg_dist(x9, y9, rp9["pts"][k9], rp9["pts"][k9 + 1]) for k9 in range(len(rp9["pts"]) - 1)) < rp9["w"] / 2 for rp9 in rb_roads if len(rp9["pts"]) >= 2)
                    rb_run = rb_run + 15 if inside9 else 0.0
                    if rb_run > 45:
                        rb_bad.append((rb_kind, round(rb_pts[0][0]), round(rb_pts[0][1])))
                        break
                if rb_run > 45:
                    break
    return _kept(locals(), ('a9', 'b9', 'i9', 'inside9', 'j9', 'k9', 'rb_bad', 'rb_kind', 'rb_list', 'rb_pts', 'rb_run', 'rb_w', 'rp9', 'seg_len9', 'steps9', 't9', 'x9', 'y9'))


# (per-way: first offense reports, rest of the way skipped)


def _seg_0401__ways_not_inside_road_beds(*, check: Any = _UNBOUND, rb_bad: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 401 (ways_not_inside_road_beds) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "ways_not_inside_road_beds",
        not rb_bad,
        f"way(s) running INSIDE a road's paved bed for 45+px: {sorted(set(rb_bad))[:4]} - two ways drawn where the ground has one; delete the duplicate (the road itself serves the frontage), or move the lane clear of the bed",
    )
    return _kept(locals(), ())


# A STREET REACHES THE NEIGHBOR IT POINTS AT (GM 2026-08-10: several street ends stopped
# a visible gap short of a crossing street - past the near-miss check's 30px cap but well
# inside "obviously meant to join"). An END whose direction of travel points (align > 0.6)
# at another street's bed within 65px must reach it.


def _seg_0402__sr_sts(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 402 (sr_sts) - body verbatim from the legacy gate() (feature 022)."""
    sr_sts = M.get("town_streets", [])
    return _kept(locals(), ('sr_sts',))


def _seg_0403__sr_bad() -> dict[str, Any]:
    """Gate segment 403 (sr_bad) - body verbatim from the legacy gate() (feature 022)."""
    sr_bad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('sr_bad',))


# alley ENDS answer to the same rule - the S band's roji visibly dangled short of (and
# past) the band street they aim at (GM 2026-08-10, the render's most repeated defect)
# LANES were absent from this list entirely (GM 2026-08-11, reporting the same near-miss a
# second time), so a lane's ends were never examined by any of the tests below - which looks
# exactly like a lane that passes. Alleys were here; lanes, the wider of the two, were not.


def _seg_0404__al9(*, M: Any = _UNBOUND, al9: Any = _UNBOUND, ln9: Any = _UNBOUND, sr_sts: Any = _UNBOUND, st9: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 404 (al9, ln9, sr_enders, st9) - body verbatim from the legacy gate() (feature 022)."""
    sr_enders = (
        [(st9, st9.get("w", 18) / 2, True) for st9 in sr_sts]
        + [(al9, al9.get("w", 10) / 2, False) for al9 in M.get("alleys", [])]
        + [(ln9, ln9.get("w", 10) / 2, False) for ln9 in M.get("lanes", []) if isinstance(ln9, dict)]
    )
    return _kept(locals(), ('al9', 'ln9', 'sr_enders', 'st9'))


def _seg_0405__E9(
    *,
    E9: Any = _UNBOUND,
    a9: Any = _UNBOUND,
    align9: Any = _UNBOUND,
    ang_self: Any = _UNBOUND,
    b9: Any = _UNBOUND,
    cp9: Any = _UNBOUND,
    cp9c: Any = _UNBOUND,
    cross9: Any = _UNBOUND,
    d9: Any = _UNBOUND,
    dl9: Any = _UNBOUND,
    gap9: Any = _UNBOUND,
    gd9: Any = _UNBOUND,
    k9: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    nb9: Any = _UNBOUND,
    ot9: Any = _UNBOUND,
    ot_bear9: Any = _UNBOUND,
    otw9: Any = _UNBOUND,
    perp9: Any = _UNBOUND,
    q9: Any = _UNBOUND,
    sr_bad: Any = _UNBOUND,
    sr_bear: Any = _UNBOUND,
    sr_best: Any = _UNBOUND,
    sr_crossed: Any = _UNBOUND,
    sr_enders: Any = _UNBOUND,
    sr_hw2: Any = _UNBOUND,
    sr_is_street: Any = _UNBOUND,
    sr_len9: Any = _UNBOUND,
    sr_myhw: Any = _UNBOUND,
    sr_ot9: Any = _UNBOUND,
    sr_sts: Any = _UNBOUND,
    st9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 405 (E9, a9, align9, ang_self) - body verbatim from the legacy gate() (feature 022)."""
    for st9, sr_myhw, sr_is_street in sr_enders:
        if len(st9.get("pts") or []) < 2:
            continue  # a one-vertex way has no direction of travel to aim with
        for E9, nb9 in ((st9["pts"][0], st9["pts"][1]), (st9["pts"][-1], st9["pts"][-2])):
            sr_best: tuple[float, float, Pt, float] = (1e9, 0.0, (0.0, 0.0), 0.0)  # type: ignore[no-redef]
            for ot9 in sr_sts:
                if ot9 is st9:
                    continue
                for k9 in range(len(ot9["pts"]) - 1):
                    d9 = seg_dist(E9[0], E9[1], ot9["pts"][k9], ot9["pts"][k9 + 1])
                    if d9 < sr_best[0]:
                        cp9c = seg_closest(E9[0], E9[1], ot9["pts"][k9], ot9["pts"][k9 + 1])
                        sr_bear = math.degrees(math.atan2(ot9["pts"][k9 + 1][1] - ot9["pts"][k9][1], ot9["pts"][k9 + 1][0] - ot9["pts"][k9][0]))
                        sr_best = (d9, ot9.get("w", 18) / 2, (float(cp9c[0]), float(cp9c[1])), sr_bear)
            if sr_best[0] >= 1e9:
                continue
            d9, otw9, cp9, ot_bear9 = sr_best
            gap9 = d9 - sr_myhw - otw9
            if not (gap9 > 2 and d9 < 95):
                continue
            dl9 = math.hypot(E9[0] - nb9[0], E9[1] - nb9[1]) or 1.0
            gd9 = math.hypot(cp9[0] - E9[0], cp9[1] - E9[1]) or 1.0
            align9 = ((E9[0] - nb9[0]) / dl9) * ((cp9[0] - E9[0]) / gd9) + ((E9[1] - nb9[1]) / dl9) * ((cp9[1] - E9[1]) / gd9)
            # ALIGNMENT IS NOT THE ONLY TELL (GM 2026-08-10: "two city streets which approach
            # each other... generally should intersect"). A street ending a short way off
            # another it meets at a CORNER angle is a junction that failed to close, whatever
            # its end happens to point at - which is how a slightly slanted run slipped past the
            # aligned-only test. So: aligned and close, OR near-perpendicular and very close.
            perp9 = False
            if gd9 > 1:
                ang_self = math.degrees(math.atan2(E9[1] - nb9[1], E9[0] - nb9[0]))
                cross9 = abs((ang_self - ot_bear9) % 180.0)
                # only for a STREET: an alley legitimately dead-ends inside a block (a roji
                # serves the core it threads and stops), so a blind alley near a parallel street
                # is not a failed junction. A STREET carries through-traffic and should close.
                # ...and only if the two do not ALREADY cross somewhere: a street's free end
                # often lies near a perpendicular street it met 70px back, and calling that a
                # failed junction is how this rule first tried to truncate five sound streets
                sr_crossed = False
                for sr_ot9 in sr_sts:
                    if sr_ot9 is st9:
                        continue
                    if min(seg_dist(E9[0], E9[1], sr_ot9["pts"][k9], sr_ot9["pts"][k9 + 1]) for k9 in range(len(sr_ot9["pts"]) - 1)) > d9 + 1:
                        continue
                    # CONNECTED, not merely crossing: a pair that meets at an ENDPOINT (a T) never
                    # registers as a segment crossing, and treating those as failed junctions is
                    # how this rule first proposed truncating five sound streets
                    sr_hw2 = sr_myhw + sr_ot9.get("w", 18) / 2 + 3
                    if (
                        any(
                            segments_cross(tuple(st9["pts"][a9]), tuple(st9["pts"][a9 + 1]), tuple(sr_ot9["pts"][b9]), tuple(sr_ot9["pts"][b9 + 1]))
                            for a9 in range(len(st9["pts"]) - 1)
                            for b9 in range(len(sr_ot9["pts"]) - 1)
                        )
                        or any(seg_dist(q9[0], q9[1], sr_ot9["pts"][b9], sr_ot9["pts"][b9 + 1]) < sr_hw2 for q9 in (st9["pts"][0], st9["pts"][-1]) for b9 in range(len(sr_ot9["pts"]) - 1))
                        or any(
                            # ...and SYMMETRICALLY: the other street's end may be the one lying on
                            # this street's body, which is the commoner T of the two
                            seg_dist(q9[0], q9[1], st9["pts"][a9], st9["pts"][a9 + 1]) < sr_hw2
                            for q9 in (sr_ot9["pts"][0], sr_ot9["pts"][-1])
                            for a9 in range(len(st9["pts"]) - 1)
                        )
                    ):
                        sr_crossed = True
                        break
                # A LONG lane is a through-way, not a roji (GM 2026-08-11, reporting the same
                # defect twice: "it stops just short of intersecting"). The alley exemption above
                # is right for a short service thread that dies inside the block it serves, and
                # WRONG for a 470 px lane that runs the depth of a quarter and halts 90 ft off a
                # major street. Measured in real feet so it means the same thing at every tier.
                sr_len9 = sum(math.dist(st9["pts"][k9], st9["pts"][k9 + 1]) for k9 in range(len(st9["pts"]) - 1)) * float(meta.get("ftpx", 1))
                perp9 = (sr_is_street or sr_len9 > 600.0) and not sr_crossed and 45.0 < min(cross9, 180.0 - cross9) <= 90.0 and d9 < 80.0
            if (align9 > 0.6 and d9 < 65.0) or perp9:
                sr_bad.append((round(E9[0]), round(E9[1]), round(d9)))
    return _kept(
        locals(),
        (
            'E9',
            'a9',
            'align9',
            'ang_self',
            'b9',
            'cp9',
            'cp9c',
            'cross9',
            'd9',
            'dl9',
            'gap9',
            'gd9',
            'k9',
            'nb9',
            'ot9',
            'ot_bear9',
            'otw9',
            'perp9',
            'q9',
            'sr_bad',
            'sr_bear',
            'sr_best',
            'sr_crossed',
            'sr_hw2',
            'sr_is_street',
            'sr_len9',
            'sr_myhw',
            'sr_ot9',
            'st9',
        ),
    )


def _seg_0406__city_streets_reach_their_neighbors(*, check: Any = _UNBOUND, sr_bad: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 406 (city_streets_reach_their_neighbors) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "city_streets_reach_their_neighbors",
        not sr_bad,
        f"street end(s) stopping a visible gap short of the street they point at (x, y, px): {sorted(set(sr_bad))[:4]} - extend the end to the exact junction (compute the segment intersection), or turn/shorten it so it clearly is not aiming there",
    )
    return _kept(locals(), ())


# WAYS CLEAR OF THE CASTLE'S OWN MOAT (GM 2026-08-10: a city street started 6px off the
# castle moat's channel line - the CITY moat battery never read the castle record).


def _seg_0407__cm_bad() -> dict[str, Any]:
    """Gate segment 407 (cm_bad) - body verbatim from the legacy gate() (feature 022)."""
    cm_bad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('cm_bad',))


def _seg_0408__cm9(
    *,
    M: Any = _UNBOUND,
    cm9: Any = _UNBOUND,
    cm_bad: Any = _UNBOUND,
    cm_defw: Any = _UNBOUND,
    cm_kind: Any = _UNBOUND,
    cm_list: Any = _UNBOUND,
    cmw9: Any = _UNBOUND,
    cs9: Any = _UNBOUND,
    cw9: Any = _UNBOUND,
    cw_pts: Any = _UNBOUND,
    cw_w: Any = _UNBOUND,
    d9: Any = _UNBOUND,
    k9: Any = _UNBOUND,
    p9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 408 (cm9, cm_bad, cm_defw, cm_kind) - body verbatim from the legacy gate() (feature 022)."""
    for cs9 in M.get("castles", []):
        cm9 = cs9.get("moat")
        if not cm9 or len(cm9) < 3:
            continue
        cmw9 = float(cs9.get("moat_width", 22))
        for cm_kind, cm_list, cm_defw in (("street", M.get("town_streets", []), 18), ("alley", M.get("alleys", []), 10), ("lane", M.get("lanes", []), 10)):
            for cw9 in cm_list:
                cw_pts = cw9["pts"] if isinstance(cw9, dict) else cw9
                cw_w = cw9.get("w", cm_defw) if isinstance(cw9, dict) else cm_defw
                for p9 in cw_pts:
                    d9 = min(seg_dist(p9[0], p9[1], cm9[k9], cm9[(k9 + 1) % len(cm9)]) for k9 in range(len(cm9)))
                    if d9 < cmw9 / 2 + cw_w / 2:
                        cm_bad.append((cm_kind, round(p9[0]), round(p9[1])))
                        break
    return _kept(locals(), ('cm9', 'cm_bad', 'cm_defw', 'cm_kind', 'cm_list', 'cmw9', 'cs9', 'cw9', 'cw_pts', 'cw_w', 'd9', 'k9', 'p9'))


def _seg_0409__ways_clear_of_castle_moat(*, check: Any = _UNBOUND, cm_bad: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 409 (ways_clear_of_castle_moat) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "ways_clear_of_castle_moat",
        not cm_bad,
        f"way vertex(es) in the castle moat's channel: {sorted(set(cm_bad))[:4]} - the keep's moat is water like any other; start/route the way clear of the channel band (only the castle's own gate bridges cross it)",
    )
    return _kept(locals(), ())
