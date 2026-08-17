"""Gate segments (city torii and estate grounds; keys 0563_334-0563_376) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from .common_01_geometry import Pt, point_in_poly, seg_dist, segments_cross
from .common_02_overlap_policy import in_ellipse
from .common_03_capacity import _UNBOUND, _kept

# the street network must be CONNECTED - one coherent grid wired to the Imperial
# road, not isolated stubs (ported from the town "no street to nowhere" thinking).


def _seg_0563_334__streets(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.334 (streets) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        streets = M.get("town_streets", [])
    return _kept(locals(), ('streets',))


def _seg_0563_335__city_streets_connected(
    *,
    M: Any = _UNBOUND,
    _w21: Any = _UNBOUND,
    a: Any = _UNBOUND,
    ai: Any = _UNBOUND,
    beds_meet: Any = _UNBOUND,
    bi: Any = _UNBOUND,
    check: Any = _UNBOUND,
    comps: Any = _UNBOUND,
    end: Any = _UNBOUND,
    find2: Any = _UNBOUND,
    i: Any = _UNBOUND,
    ia: Any = _UNBOUND,
    ib: Any = _UNBOUND,
    k: Any = _UNBOUND,
    ki: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    nbr: Any = _UNBOUND,
    near_miss: Any = _UNBOUND,
    parent: Any = _UNBOUND,
    q21: Any = _UNBOUND,
    sa: Any = _UNBOUND,
    sb: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    seg_seg_dist: Any = _UNBOUND,
    slines: Any = _UNBOUND,
    sseg: Any = _UNBOUND,
    st: Any = _UNBOUND,
    streets: Any = _UNBOUND,
    stub: Any = _UNBOUND,
    tol: Any = _UNBOUND,
    widths: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.335 (city_streets_connected, city_streets_no_intersection_stub, city_streets_no_near_miss) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):  # noqa: SIM102
            if streets:
                # at the CAPITAL the suburb streets (wholly outside the rampart - the kashi
                # quay street) are their own lawful networks reached through the gates; the
                # connectivity rule binds the IN-WALL grid (021)
                if scale == "capital" and len(M.get("wall") or []) >= 3:
                    _w21 = M["wall"]
                    streets = [st for st in streets if any(point_in_poly(q21[0], q21[1], _w21) for q21 in st["pts"])]
                sseg = [st["pts"] for st in streets] + ([M["road"]] if M.get("road") else [])
                # width of each segment's paved bed (the road counts as a street here): two streets
                # are CONNECTED only if you can walk between them, i.e. their beds actually overlap -
                # centerline gap < the sum of their half-widths. A street whose end stops even a roadbed
                # short of the next one is a SEPARATE network (you cannot step from one to the other),
                # which is exactly the laborer grid that ended 40px shy of the Imperial road. (Kido ward
                # gates do NOT break this: the street centerline runs on under the gate, uninterrupted.)
                widths = [st.get("w", 18) for st in streets] + ([M.get("road_width", 26)] if M.get("road") else [])
                parent = list(range(len(sseg)))

                def find2(a: int) -> int:
                    while parent[a] != a:
                        parent[a] = parent[parent[a]]
                        a = parent[a]
                    return a

                def beds_meet(ia: int, ib: int) -> bool:  # beds overlap: segments cross, or a centerline endpoint lies
                    sa, sb = sseg[ia], sseg[ib]  # within the two beds' combined half-widths (+2px slack)
                    tol = widths[ia] / 2 + widths[ib] / 2 + 2
                    for i in range(len(sa) - 1):
                        for k in range(len(sb) - 1):
                            if segments_cross(sa[i], sa[i + 1], sb[k], sb[k + 1]):
                                return True
                            if (
                                seg_dist(sa[i][0], sa[i][1], sb[k], sb[k + 1]) < tol
                                or seg_dist(sa[i + 1][0], sa[i + 1][1], sb[k], sb[k + 1]) < tol
                                or seg_dist(sb[k][0], sb[k][1], sa[i], sa[i + 1]) < tol
                                or seg_dist(sb[k + 1][0], sb[k + 1][1], sa[i], sa[i + 1]) < tol
                            ):
                                return True
                    return False

                for ai in range(len(sseg)):
                    for bi in range(ai + 1, len(sseg)):
                        if beds_meet(ai, bi):
                            parent[find2(ai)] = find2(bi)
                comps = {find2(i) for i in range(len(streets))}
                check(
                    "city_streets_connected",
                    len(comps) == 1,
                    f"the city streets form {len(comps)} disconnected groups - a street whose bed does not actually reach another's is a separate network; wire every grid to the Imperial road (extend it until the beds overlap)",
                )

                # two streets that come ALMOST together without meeting read as a mistake - they
                # should either JOIN (cross/touch) or stay clearly apart, never leave a sliver gap
                def seg_seg_dist(a0: Pt, a1: Pt, b0: Pt, b1: Pt) -> float:
                    return min(seg_dist(a0[0], a0[1], b0, b1), seg_dist(a1[0], a1[1], b0, b1), seg_dist(b0[0], b0[1], a0, a1), seg_dist(b1[0], b1[1], a0, a1))

                slines = [st["pts"] for st in streets]
                near_miss = set()
                for ia in range(len(slines)):
                    for ib in range(ia + 1, len(slines)):
                        for i in range(len(slines[ia]) - 1):
                            for ki in range(len(slines[ib]) - 1):
                                if segments_cross(slines[ia][i], slines[ia][i + 1], slines[ib][ki], slines[ib][ki + 1]):
                                    continue
                                if 2 < seg_seg_dist(slines[ia][i], slines[ia][i + 1], slines[ib][ki], slines[ib][ki + 1]) < 30:
                                    near_miss.add((ia, ib))
                check(
                    "city_streets_no_near_miss",
                    not near_miss,
                    f"city street pair(s) that come within a sliver of each other without meeting - close the gap so they join, or separate them: {sorted(near_miss)}",
                )
                # a street that crosses another and then STOPS a little way past it leaves an ugly
                # dangling stub. Fine to cross and keep going (to the next block/edge), or to
                # terminate AT the junction (an L/T corner), but not to overshoot it by a sliver.
                stub = set()
                for ia, sa in enumerate(slines):
                    for end, nbr in ((sa[0], sa[1]), (sa[-1], sa[-2])):
                        for ib, sb in enumerate(slines):
                            if ib == ia:
                                continue
                            for ki in range(len(sb) - 1):
                                if segments_cross(nbr, end, sb[ki], sb[ki + 1]) and 3 < seg_dist(end[0], end[1], sb[ki], sb[ki + 1]) < 50:
                                    stub.add((ia, ib))
                check(
                    "city_streets_no_intersection_stub",
                    not stub,
                    f"city street(s) that cross another and then stop just past it, leaving a dangling stub - end them AT the junction or run them on: {sorted(stub)}",
                )
    return _kept(
        locals(),
        (
            '_w21',
            'ai',
            'beds_meet',
            'bi',
            'comps',
            'end',
            'find2',
            'i',
            'ia',
            'ib',
            'ki',
            'nbr',
            'near_miss',
            'parent',
            'q21',
            'sa',
            'sb',
            'seg_seg_dist',
            'slines',
            'sseg',
            'st',
            'streets',
            'stub',
            'widths',
        ),
    )


# a temple a city street runs UP TO (a street that terminates at its front) marks a
# sacred approach - it needs torii arches on that street, just in front of the temple


def _seg_0563_336__torii(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.336 (torii) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        torii = M.get("torii", [])
    return _kept(locals(), ('torii',))


def _seg_0563_337__pt_rect(*, dx: Any = _UNBOUND, dy: Any = _UNBOUND, meta: Any = _UNBOUND, px: Any = _UNBOUND, py: Any = _UNBOUND, scale: Any = _UNBOUND, t: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.337 (pt_rect) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):

        def pt_rect(px: float, py: float, t: dict[str, Any]) -> float:
            dx = max(t["x"] - t["w"] / 2 - px, 0, px - t["x"] - t["w"] / 2)
            dy = max(t["y"] - t["h"] / 2 - py, 0, py - t["y"] - t["h"] / 2)
            return math.hypot(dx, dy)

    return _kept(locals(), ('pt_rect',))


def _seg_0563_338__no_torii(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.338 (no_torii) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        no_torii = []  # type: ignore[var-annotated]
    return _kept(locals(), ('no_torii',))


def _seg_0563_339__e_2(
    *,
    M: Any = _UNBOUND,
    e: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    no_torii: Any = _UNBOUND,
    pt_rect: Any = _UNBOUND,
    r: Any = _UNBOUND,
    runs_up: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    st: Any = _UNBOUND,
    t: Any = _UNBOUND,
    to: Any = _UNBOUND,
    torii: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.339 (e, no_torii, r, runs_up) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for t in [r for r in M.get("religious", []) if r.get("kind") == "temple"]:
            runs_up = any(min(pt_rect(e[0], e[1], t) for e in (st["pts"][0], st["pts"][-1])) < 28 for st in M.get("town_streets", []))
            if runs_up and not any(math.hypot(to[0] - t["x"], to[1] - t["y"]) < 95 for to in torii):
                no_torii.append(t.get("label"))
    return _kept(locals(), ('e', 'no_torii', 'r', 'runs_up', 'st', 't', 'to'))


def _seg_0563_340__city_temple_approach_has_torii(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, no_torii: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.340 (city_temple_approach_has_torii) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_temple_approach_has_torii", not no_torii, f"temple(s) a city street runs straight up to, with no torii arch in front: {no_torii}")
    return _kept(locals(), ())


# (RETIRED 2026-07-24: city_temple_torii_fill_approach - "an avenue with open room takes
# another arch" - is superseded by the per-temple seeded ROLL: shrine_hall now rolls each
# hall's count on the tier's TORII_WEIGHTS column and records the target on the religious
# rec, so avenue completeness is defined by the roll, not by remaining street room. A
# rolled 1 beside an open street is a hall with one patron gate, not an unfinished avenue.
# torii_match_roll (with torii_count_canonical) now carries the teeth. Same precedent as
# torii_full_avenue_is_seven's retirement when the numerology rule landed.)
# a torii arch stands OVER the street it spans - the street passes beneath it - so a
# torii sitting on a street must be drawn after (higher z than) that street, not under it


def _seg_0563_341__to_under(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.341 (to_under) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        to_under = []  # type: ignore[var-annotated]
    return _kept(locals(), ('to_under',))


def _seg_0563_342__i_5(
    *, M: Any = _UNBOUND, i: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, sp: Any = _UNBOUND, st: Any = _UNBOUND, t: Any = _UNBOUND, to_under: Any = _UNBOUND, torii: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.342 (i, sp, st, t) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for t in torii:
            for st in M.get("town_streets", []):
                sp = st["pts"]
                if any(seg_dist(t[0], t[1], sp[i], sp[i + 1]) <= st.get("w", 24) / 2 + 12 for i in range(len(sp) - 1)) and t[2] <= st.get("z", 0):
                    to_under.append((t[0], t[1]))
    return _kept(locals(), ('i', 'sp', 'st', 't', 'to_under'))


def _seg_0563_343__city_torii_over_streets(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, to_under: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.343 (city_torii_over_streets) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_torii_over_streets", not to_under, f"torii arch(es) drawn UNDER a street they span (the street must pass beneath the arch): {to_under}")
    return _kept(locals(), ())


# no LARGE empty swath inside the walls (ported from wall_hugs_the_town; REBUILT
# footprint-aware, GM 2026-07-23, after Tango shipped a ~230x95px bare pocket just
# inside its north gate that read fully green). The old detector sampled an 80px grid
# and called a cell "used" within 120px of any building CENTER - a single house
# sanitized a 240px-wide disc, so only vast voids could ever fire. Now every claiming
# feature counts with its real FOOTPRINT: building/compound/grove rects, field and
# ground polys, well / stable-yard / torii discs, the road / street / alley / ring-road
# / water rights-of-way, ward fences, the rampart + its patrol strip, and the pond. A
# 32px grid marks cells >= 20px clear of ALL of them as dead ground; any contiguous
# dead cluster >= 4,000 px2 of core fails. Calibration (2026-07-23, pool-wide dry-run,
# settlements.md): Tango's north-gate pocket measures 6,144 px2 of core; the largest
# LEGITIMATE opens anywhere else measure 2,048 (Tango) / 1,024 (Nagahara), so the
# threshold sits between with ~2x headroom both ways. A city keeps SOME open ground,
# but every deliberate open is CLAIMED by a feature record (a working stable yard /
# animal ground, a right-of-way, a field); ground claimed by nothing, at
# wall-protected premium, would not have been left bare.


def _seg_0563_344__ES_MARGIN(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.344 (ES_MARGIN, ES_MIN, ES_STEP) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        ES_STEP, ES_MARGIN, ES_MIN = 32, 20.0, 4000
    return _kept(locals(), ('ES_MARGIN', 'ES_MIN', 'ES_STEP'))


def _seg_0563_345__es_rects(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.345 (es_rects) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_rects: list[tuple[float, float, float, float]] = []  # type: ignore[no-redef,unused-ignore]
    return _kept(locals(), ('es_rects',))


def _seg_0563_346__es_s(*, M: Any = _UNBOUND, es_s: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.346 (es_s, es_singles) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_singles = [es_s for es_s in [M.get("governor_mansion"), *(M.get("theater_stage") or [])] if isinstance(es_s, dict)]
    return _kept(locals(), ('es_s', 'es_singles'))


def _seg_0563_347__es_grp(
    *,
    M: Any = _UNBOUND,
    es_grp: Any = _UNBOUND,
    es_hh: Any = _UNBOUND,
    es_hw: Any = _UNBOUND,
    es_k: Any = _UNBOUND,
    es_o: Any = _UNBOUND,
    es_rects: Any = _UNBOUND,
    es_singles: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.347 (es_grp, es_hh, es_hw, es_k) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for es_grp in [
            M.get(es_k, []) or []
            for es_k in (
                "buildings",
                "flophouses",
                "storehouses",
                "manors",
                "ministries",
                "religious",
                "inspection_stations",
                "byres",
                "cemeteries",
                "mausoleums",
                "merchant_estates",
                "farm_sheds",
                "gardens",
                "threshing_yards",
                "fire_towers",
                "drum_towers",
                "gate_structs",
                "groves",
                "breweries",
                "dye_yards",
                "lumber_yards",
                "oil_presses",
                "pawnshops",
                "bathhouses",
                "kilns",
                "tanning_yards",
                "martial_halls",
                "dojos",
            )
        ] + [houses, es_singles]:
            for es_o in es_grp:
                es_hw, es_hh = es_o["w"] / 2, es_o["h"] / 2
                if es_o.get("rot"):
                    es_hw = es_hh = math.hypot(es_hw, es_hh)
                es_rects.append((es_o["x"], es_o["y"], es_hw, es_hh))
    return _kept(locals(), ('es_grp', 'es_hh', 'es_hw', 'es_k', 'es_o', 'es_rects'))


def _seg_0563_348__es_discs(*, M: Any = _UNBOUND, es_o: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.348 (es_discs, es_o) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_discs = [(es_o["x"], es_o["y"], es_o.get("r", 8.0)) for es_o in M.get("wells", []) + M.get("stable_yards", [])]
    return _kept(locals(), ('es_discs', 'es_o'))


def _seg_0563_349__es_discs_1(*, M: Any = _UNBOUND, es_discs: Any = _UNBOUND, es_t: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.349 (es_discs, es_t) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_discs += [(es_t[0], es_t[1], 14.0) for es_t in M.get("torii", [])]
    return _kept(locals(), ('es_discs', 'es_t'))


def _seg_0563_350__es_polys(*, M: Any = _UNBOUND, f: Any = _UNBOUND, fields: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.350 (es_polys, f) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_polys = [f["outline"] for f in fields] + list((M.get("comb_floors") or {}).values())
    return _kept(locals(), ('es_polys', 'f'))


def _seg_0563_351__es_k(*, M: Any = _UNBOUND, es_k: Any = _UNBOUND, es_o: Any = _UNBOUND, es_polys: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.351 (es_k, es_o, es_polys) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for es_k in ("dry_plots", "pastures", "commons", "marshes", "forest_patches", "village_groves", "clearings"):
            es_polys += [es_o["poly"] for es_o in M.get(es_k, []) or []]
    return _kept(locals(), ('es_k', 'es_o', 'es_polys'))


def _seg_0563_352__es_lines(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.352 (es_lines) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_lines: list[tuple[list[Any], float]] = [(w, 20.0)]  # type: ignore[no-redef,unused-ignore]  # the rampart + its patrol strip is claimed ground
    return _kept(locals(), ('es_lines',))


def _seg_0563_353__es_lines_1(*, M: Any = _UNBOUND, es_lines: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.353 (es_lines) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and M.get("road"):
        es_lines.append((M["road"], M.get("road_width", 30) / 2))
    return _kept(locals(), ('es_lines',))


def _seg_0563_354__es_lines_2(*, M: Any = _UNBOUND, es_lines: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.354 (es_lines) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and M.get("ring_road"):
        es_lines.append((M["ring_road"], M.get("ring_road_width", 24) / 2))
    return _kept(locals(), ('es_lines',))


def _seg_0563_355__es_dw(
    *, M: Any = _UNBOUND, es_dw: Any = _UNBOUND, es_grp2: Any = _UNBOUND, es_lines: Any = _UNBOUND, es_o: Any = _UNBOUND, es_pk: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.355 (es_dw, es_grp2, es_lines, es_o) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for es_grp2, es_pk, es_dw in (
            (M.get("roads", []), "pts", 24),
            (M.get("town_streets", []), "pts", 24),
            (M.get("alleys", []), "pts", 12),
            (M.get("streams", []), "poly", 12),
            (M.get("channels", []), "poly", 8),
        ):
            es_lines += [(es_o[es_pk], es_o.get("w", es_dw) / 2) for es_o in es_grp2 or []]
    return _kept(locals(), ('es_dw', 'es_grp2', 'es_lines', 'es_o', 'es_pk'))


def _seg_0563_356__es_lines_3(*, M: Any = _UNBOUND, es_lines: Any = _UNBOUND, es_o: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.356 (es_lines, es_o) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_lines += [(es_o["boundary"], 8.0) for es_o in M.get("wards", [])]
    return _kept(locals(), ('es_lines', 'es_o'))


def _seg_0563_357__es_pond(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.357 (es_pond) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_pond = M.get("pond")
    return _kept(locals(), ('es_pond',))


def _seg_0563_358__es_wx0(*, meta: Any = _UNBOUND, p: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.358 (es_wx0, es_wy0, p) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_wx0, es_wy0 = min(p[0] for p in w), min(p[1] for p in w)
    return _kept(locals(), ('es_wx0', 'es_wy0', 'p'))


def _seg_0563_359__es_wx1(*, meta: Any = _UNBOUND, p: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.359 (es_wx1, es_wy1, p) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_wx1, es_wy1 = max(p[0] for p in w), max(p[1] for p in w)
    return _kept(locals(), ('es_wx1', 'es_wy1', 'p'))


def _seg_0563_360__es_ci0(*, ES_STEP: Any = _UNBOUND, es_wx0: Any = _UNBOUND, es_wy0: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.360 (es_ci0, es_cj0) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_ci0, es_cj0 = int(es_wx0 // ES_STEP), int(es_wy0 // ES_STEP)
    return _kept(locals(), ('es_ci0', 'es_cj0'))


def _seg_0563_361__es_ci1(*, ES_STEP: Any = _UNBOUND, es_wx1: Any = _UNBOUND, es_wy1: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.361 (es_ci1, es_cj1) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_ci1, es_cj1 = int(es_wx1 // ES_STEP) + 1, int(es_wy1 // ES_STEP) + 1
    return _kept(locals(), ('es_ci1', 'es_cj1'))


def _seg_0563_362__es_cells(
    *,
    ES_STEP: Any = _UNBOUND,
    bx0: Any = _UNBOUND,
    bx1: Any = _UNBOUND,
    by0: Any = _UNBOUND,
    by1: Any = _UNBOUND,
    es_ci0: Any = _UNBOUND,
    es_ci1: Any = _UNBOUND,
    es_cj0: Any = _UNBOUND,
    es_cj1: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.362 (es_cells) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):

        def es_cells(bx0: float, by0: float, bx1: float, by1: float) -> list[tuple[int, int]]:
            """Grid cells whose sample point falls inside the bbox (clamped to the wall window)."""
            return [
                (eci, ecj)
                for eci in range(max(es_ci0, math.ceil(bx0 / ES_STEP)), min(es_ci1, math.floor(bx1 / ES_STEP)) + 1)
                for ecj in range(max(es_cj0, math.ceil(by0 / ES_STEP)), min(es_cj1, math.floor(by1 / ES_STEP)) + 1)
            ]

    return _kept(locals(), ('es_cells',))


def _seg_0563_363__es_covered(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.363 (es_covered) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_covered: set[tuple[int, int]] = set()  # type: ignore[no-redef,unused-ignore]
    return _kept(locals(), ('es_covered',))


def _seg_0563_364__es_covered_1(
    *,
    ES_MARGIN: Any = _UNBOUND,
    es_cells: Any = _UNBOUND,
    es_covered: Any = _UNBOUND,
    es_rects: Any = _UNBOUND,
    es_rhh: Any = _UNBOUND,
    es_rhw: Any = _UNBOUND,
    es_rx: Any = _UNBOUND,
    es_ry: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.364 (es_covered, es_rhh, es_rhw, es_rx) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for es_rx, es_ry, es_rhw, es_rhh in es_rects:
            es_covered.update(es_cells(es_rx - es_rhw - ES_MARGIN, es_ry - es_rhh - ES_MARGIN, es_rx + es_rhw + ES_MARGIN, es_ry + es_rhh + ES_MARGIN))
    return _kept(locals(), ('es_covered', 'es_rhh', 'es_rhw', 'es_rx', 'es_ry'))


def _seg_0563_365__c_2(
    *,
    ES_MARGIN: Any = _UNBOUND,
    ES_STEP: Any = _UNBOUND,
    c: Any = _UNBOUND,
    es_cells: Any = _UNBOUND,
    es_covered: Any = _UNBOUND,
    es_discs: Any = _UNBOUND,
    es_dr: Any = _UNBOUND,
    es_dx: Any = _UNBOUND,
    es_dy: Any = _UNBOUND,
    es_rr: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.365 (c, es_covered, es_dr, es_dx) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for es_dx, es_dy, es_dr in es_discs:
            es_rr = es_dr + ES_MARGIN
            es_covered.update([c for c in es_cells(es_dx - es_rr, es_dy - es_rr, es_dx + es_rr, es_dy + es_rr) if (c[0] * ES_STEP - es_dx) ** 2 + (c[1] * ES_STEP - es_dy) ** 2 <= es_rr * es_rr])
    return _kept(locals(), ('c', 'es_covered', 'es_dr', 'es_dx', 'es_dy', 'es_rr'))


def _seg_0563_366__c_3(
    *,
    ES_MARGIN: Any = _UNBOUND,
    ES_STEP: Any = _UNBOUND,
    c: Any = _UNBOUND,
    es_a: Any = _UNBOUND,
    es_b: Any = _UNBOUND,
    es_cells: Any = _UNBOUND,
    es_covered: Any = _UNBOUND,
    es_hwid: Any = _UNBOUND,
    es_i: Any = _UNBOUND,
    es_lines: Any = _UNBOUND,
    es_pts: Any = _UNBOUND,
    es_rr: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.366 (c, es_a, es_b, es_covered) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for es_pts, es_hwid in es_lines:
            es_rr = es_hwid + ES_MARGIN
            for es_i in range(len(es_pts) - 1):
                es_a, es_b = es_pts[es_i], es_pts[es_i + 1]
                es_covered.update(
                    [
                        c
                        for c in es_cells(min(es_a[0], es_b[0]) - es_rr, min(es_a[1], es_b[1]) - es_rr, max(es_a[0], es_b[0]) + es_rr, max(es_a[1], es_b[1]) + es_rr)
                        if c not in es_covered and seg_dist(c[0] * ES_STEP, c[1] * ES_STEP, es_a, es_b) <= es_rr
                    ]
                )
    return _kept(locals(), ('c', 'es_a', 'es_b', 'es_covered', 'es_hwid', 'es_i', 'es_pts', 'es_rr'))


def _seg_0563_367__c_4(
    *,
    ES_STEP: Any = _UNBOUND,
    c: Any = _UNBOUND,
    es_cells: Any = _UNBOUND,
    es_covered: Any = _UNBOUND,
    es_p: Any = _UNBOUND,
    es_polys: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    q: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.367 (c, es_covered, es_p, q) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for es_p in es_polys:
            es_covered.update(
                [
                    c
                    for c in es_cells(min(q[0] for q in es_p), min(q[1] for q in es_p), max(q[0] for q in es_p), max(q[1] for q in es_p))
                    if c not in es_covered and point_in_poly(c[0] * ES_STEP, c[1] * ES_STEP, es_p)
                ]
            )
    return _kept(locals(), ('c', 'es_covered', 'es_p', 'q'))


def _seg_0563_368__c_5(
    *, ES_STEP: Any = _UNBOUND, c: Any = _UNBOUND, es_cells: Any = _UNBOUND, es_covered: Any = _UNBOUND, es_pond: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.368 (c, es_covered) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and es_pond:
        es_covered.update(
            [
                c
                for c in es_cells(es_pond[0] - es_pond[2] * 1.2, es_pond[1] - es_pond[3] * 1.2, es_pond[0] + es_pond[2] * 1.2, es_pond[1] + es_pond[3] * 1.2)
                if c not in es_covered and in_ellipse(c[0] * ES_STEP, c[1] * ES_STEP, es_pond, 1.15)
            ]
        )
    return _kept(locals(), ('c', 'es_covered'))


# the CITADEL claims its ground (021): a castle court is deliberately BLANK (the
# sync doctrine) - blank is not unclaimed, and its moat band goes with it


def _seg_0563_369__es_ca(*, M: Any = _UNBOUND, es_ca: Any = _UNBOUND, es_cells: Any = _UNBOUND, es_covered: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.369 (es_ca, es_covered) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for es_ca in M.get("castles", []):
            es_covered.update(es_cells(es_ca["x"] - es_ca["w"] / 2 - 45, es_ca["y"] - es_ca["h"] / 2 - 45, es_ca["x"] + es_ca["w"] / 2 + 45, es_ca["y"] + es_ca["h"] / 2 + 45))
    return _kept(locals(), ('es_ca', 'es_covered'))


def _seg_0563_370__c_6(
    *,
    ES_STEP: Any = _UNBOUND,
    c: Any = _UNBOUND,
    es_cells: Any = _UNBOUND,
    es_covered: Any = _UNBOUND,
    es_wx0: Any = _UNBOUND,
    es_wx1: Any = _UNBOUND,
    es_wy0: Any = _UNBOUND,
    es_wy1: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    w: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.370 (c, es_empty) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_empty = {c for c in es_cells(es_wx0, es_wy0, es_wx1, es_wy1) if c not in es_covered and point_in_poly(c[0] * ES_STEP, c[1] * ES_STEP, w)}
    return _kept(locals(), ('c', 'es_empty'))


def _seg_0563_371__es_seen(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.371 (es_seen) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_seen: set[tuple[int, int]] = set()  # type: ignore[no-redef,unused-ignore]
    return _kept(locals(), ('es_seen',))


def _seg_0563_372__es_flagged(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.372 (es_flagged) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_flagged: list[tuple[int, tuple[int, int]]] = []  # type: ignore[no-redef,unused-ignore]
    return _kept(locals(), ('es_flagged',))


def _seg_0563_373__c_7(
    *,
    ES_MIN: Any = _UNBOUND,
    ES_STEP: Any = _UNBOUND,
    c: Any = _UNBOUND,
    es_area: Any = _UNBOUND,
    es_c: Any = _UNBOUND,
    es_cell: Any = _UNBOUND,
    es_comp: Any = _UNBOUND,
    es_di: Any = _UNBOUND,
    es_dj: Any = _UNBOUND,
    es_empty: Any = _UNBOUND,
    es_flagged: Any = _UNBOUND,
    es_nb: Any = _UNBOUND,
    es_seen: Any = _UNBOUND,
    es_stack: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.373 (c, es_area, es_c, es_cell) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for es_cell in es_empty:
            if es_cell in es_seen:
                continue
            es_stack, es_comp = [es_cell], []
            es_seen.add(es_cell)
            while es_stack:
                es_c = es_stack.pop()
                es_comp.append(es_c)
                for es_di, es_dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    es_nb = (es_c[0] + es_di, es_c[1] + es_dj)
                    if es_nb in es_empty and es_nb not in es_seen:
                        es_seen.add(es_nb)
                        es_stack.append(es_nb)
            es_area = len(es_comp) * ES_STEP * ES_STEP
            if es_area >= ES_MIN:
                es_flagged.append((es_area, (sum(c[0] for c in es_comp) * ES_STEP // len(es_comp), sum(c[1] for c in es_comp) * ES_STEP // len(es_comp))))
    return _kept(locals(), ('c', 'es_area', 'es_c', 'es_cell', 'es_comp', 'es_di', 'es_dj', 'es_flagged', 'es_nb', 'es_seen', 'es_stack'))


def _seg_0563_374__es_flagged_1(*, es_flagged: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.374 (es_flagged) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_flagged.sort(reverse=True)
    return _kept(locals(), ('es_flagged',))


def _seg_0563_375__es_ftpx(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.375 (es_ftpx) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_ftpx = meta.get("ftpx", 3)
    return _kept(locals(), ('es_ftpx',))


def _seg_0563_376__city_no_large_empty_space(
    *, check: Any = _UNBOUND, ea: Any = _UNBOUND, ec: Any = _UNBOUND, es_flagged: Any = _UNBOUND, es_ftpx: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.376 (city_no_large_empty_space) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):
            check(
                "city_no_large_empty_space",
                not es_flagged,
                "contiguous UNCLAIMED open ground inside the walls: "
                + "; ".join(f"~{ea} px2 of dead core (~{ea * es_ftpx * es_ftpx / 43560:.1f} ac) centered {ec}" for ea, ec in es_flagged[:3])
                + " - land inside a wall is at a premium; fill it (extend a quarter / drop in a neighborhood) or claim it as deliberate working ground, e.g. s.animal_ground(...) for extra caravan hitching space near a gate (settlements.md)",
            )
    return _kept(locals(), ('ea', 'ec'))
