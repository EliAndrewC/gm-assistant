"""Gate segments (fields and funerary) - bodies verbatim from check_village.py (feature 024 package split; registry order preserved)."""

import math
from collections.abc import Sequence
from typing import Any

from settlement import sat_overlap

from .common_01_geometry import Poly, Pt, _struct_rect, point_in_poly, poly_dist, rect_corners, seg_dist, seg_intersect, segments_cross, within_edge_gap
from .common_02_overlap_policy import GridIndex, edge_dist, in_ellipse, poly_gap, polyline_len, water_setback
from .common_03_capacity import _UNBOUND, DWELLING_KINDS, _kept


def _seg_0285_092__barren(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.092 (barren) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        barren = []  # type: ignore[var-annotated]
    return _kept(locals(), ('barren',))


def _seg_0285_093__barren_1(
    *,
    barren: Any = _UNBOUND,
    c: Any = _UNBOUND,
    commons: Any = _UNBOUND,
    fields_ol: Any = _UNBOUND,
    gx: Any = _UNBOUND,
    gy: Any = _UNBOUND,
    n_inside: Any = _UNBOUND,
    n_open: Any = _UNBOUND,
    ol: Any = _UNBOUND,
    p: Any = _UNBOUND,
    poly: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    step: Any = _UNBOUND,
    xs: Any = _UNBOUND,
    ys: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.093 (barren, c, gx, gy) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for c in commons:
            poly = c.get("poly")
            if not poly:
                continue
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            n_inside: int = 0  # type: ignore[no-redef]
            n_open: int = 0  # type: ignore[no-redef]
            step = max(6.0, min(max(xs) - min(xs), max(ys) - min(ys)) / 12.0)
            gy = min(ys)
            while gy <= max(ys):
                gx = min(xs)
                while gx <= max(xs):
                    if point_in_poly(gx, gy, poly):
                        n_inside += 1
                        if not any(point_in_poly(gx, gy, ol) for ol in fields_ol):
                            n_open += 1
                    gx += step
                gy += step
            if n_inside and not n_open:
                barren.append((round(c["x"]), round(c["y"])))
    return _kept(locals(), ('barren', 'c', 'gx', 'gy', 'n_inside', 'n_open', 'ol', 'p', 'poly', 'step', 'xs', 'ys'))


def _seg_0285_094__commons_clear_of_paddies(*, barren: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.094 (commons_clear_of_paddies) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet'):  # noqa: SIM102 - comment bank under the guard; combining would orphan it (023 convention)
        if scale in ('town', 'village', 'hamlet', 'city'):
            check(
                "commons_clear_of_paddies",
                not barren,
                f"fuel/fodder commons patch(es) lie ENTIRELY over flooded paddy, so they clothe nothing and draw nothing: {barren[:3]} - the commons is NON-arable degraded grazing, never the productive wet paddy; put the patch where there is open ground",
            )
    return _kept(locals(), ())


# MANAGED-WOODLAND patches must not OVERLAP the crops nor BLOCK THEIR LIGHT (GM). Both the placement and
# this check enforce it. A tree canopy over a crop competes for root/light; and the sun is to the SOUTH
# (maps are north-up), so a tree casts its shadow toward the NORTH - a patch may sit just north/beside a
# crop, but on the crop's SOUTH (sunny) side it must stand well back (a canopy's shadow reach) or it
# shades the field. Covers BOTH the paddy and the dry hatake plots. Distances: a fixed crown-radius
# no-overhang CLEAR, plus a real-world shadow reach on the south side (feet -> px at the map's ftpx).


def _seg_0285_095__c_3(*, c: Any = _UNBOUND, commons: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.095 (c, woodland) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        woodland = [c for c in commons if c.get("role") == "woodland"]
    return _kept(locals(), ('c', 'woodland'))


def _seg_0285_096__woodland_clear_of_crops(
    *,
    CLEAR: Any = _UNBOUND,
    M: Any = _UNBOUND,
    SHADE: Any = _UNBOUND,
    _fp: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    crop: Any = _UNBOUND,
    crops: Any = _UNBOUND,
    cx0: Any = _UNBOUND,
    cx1: Any = _UNBOUND,
    cy1: Any = _UNBOUND,
    dp: Any = _UNBOUND,
    f: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    g: Any = _UNBOUND,
    gap: Any = _UNBOUND,
    gx: Any = _UNBOUND,
    gy: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    p: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    south: Any = _UNBOUND,
    tag: Any = _UNBOUND,
    w_on_grove: Any = _UNBOUND,
    w_over: Any = _UNBOUND,
    w_shade: Any = _UNBOUND,
    woodland: Any = _UNBOUND,
    wp: Any = _UNBOUND,
    wx0: Any = _UNBOUND,
    wx1: Any = _UNBOUND,
    wy0: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.096 (woodland_clear_of_crops, woodland_clear_of_grove) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city') and woodland:
        _fp = float(meta.get("ftpx") or meta.get("ft_per_px") or 2.0)
        CLEAR = 14  # ~a crown radius: the canopy must not overhang the crop
        SHADE = 14 + round(55 / _fp)  # ... plus a shadow reach (~55 ft) on the crop's SUNNY south side
        crops = [f["outline"] for f in fields if f.get("kind") == "paddy"]
        crops += [dp["poly"] for dp in M.get("dry_plots", [])]
        w_over, w_shade = [], []
        for c in woodland:
            wp = c.get("poly")
            if not wp:
                continue
            tag = (round(c["x"]), round(c["y"]))
            wy0 = min(p[1] for p in wp)
            wx0 = min(p[0] for p in wp)
            wx1 = max(p[0] for p in wp)
            for crop in crops:
                gap = poly_gap(wp, crop)
                if gap <= 0:
                    w_over.append(tag)
                    break
                cx0 = min(p[0] for p in crop)
                cx1 = max(p[0] for p in crop)
                cy1 = max(p[1] for p in crop)
                south = wy0 >= cy1 - CLEAR and wx0 < cx1 and cx0 < wx1  # patch sits south of the crop, in its shadow column
                if gap < (SHADE if south else CLEAR):
                    w_shade.append(tag)
                    break
        check(
            "woodland_clear_of_crops",
            not w_over and not w_shade,
            f"managed-woodland patch(es) overlap {sorted(set(w_over))[:3]} or shade {sorted(set(w_shade))[:3]} the "
            f"crops - a coppice patch must stand clear of the paddy + dry hatake (a canopy over crops competes; a "
            f"tree on the crop's SOUTH/sunny side blocks its light). Set it back on the high ground, north/beside the fields",
        )
        # a coppice WOODLAND patch is a DISTINCT wood from the protected fengshui GROVE (village_groves) -
        # the two must not overlap, or they merge into one indistinct green mass (GM). Keep each patch off
        # every grove clump (its drawn radius). Place the coppice on its OWN stretch of the high ground.
        w_on_grove = []
        for c in woodland:
            wp = c.get("poly")
            if not wp:
                continue
            if any(point_in_poly(gx, gy, wp) or poly_dist(gx, gy, wp) < g.get("r", 6) for g in M.get("village_groves", []) for gx, gy in g.get("clumps", [])):
                w_on_grove.append((round(c["x"]), round(c["y"])))
        check(
            "woodland_clear_of_grove",
            not w_on_grove,
            f"managed-woodland patch(es) {sorted(set(w_on_grove))[:3]} overlap the fengshui GROVE - the coppice "
            f"commons and the protected village grove are DISTINCT woods; keep the patch off the grove clumps",
        )
    return _kept(
        locals(),
        ('CLEAR', 'SHADE', '_fp', 'c', 'crop', 'crops', 'cx0', 'cx1', 'cy1', 'dp', 'f', 'g', 'gap', 'gx', 'gy', 'p', 'south', 'tag', 'w_on_grove', 'w_over', 'w_shade', 'wp', 'wx0', 'wx1', 'wy0'),
    )


def _seg_0285_097__commons_beyond_the_windbreak(
    *,
    c: Any = _UNBOUND,
    ccx: Any = _UNBOUND,
    ccy: Any = _UNBOUND,
    check: Any = _UNBOUND,
    commons: Any = _UNBOUND,
    g: Any = _UNBOUND,
    h: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    near: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    vgroves: Any = _UNBOUND,
    wb_proj: Any = _UNBOUND,
    wbs: Any = _UNBOUND,
    wvx: Any = _UNBOUND,
    wvy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.097 (commons_beyond_the_windbreak) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city') and meta.get("nucleated") and commons and len(houses) >= 10:
        wbs = [g for g in vgroves if g.get("role") == "windbreak"]
        if wbs:
            ccx = sum(h["x"] for h in houses) / len(houses)
            ccy = sum(h["y"] for h in houses) / len(houses)
            wb_proj = max((g["x"] - ccx) * wvx + (g["y"] - ccy) * wvy for g in wbs)
            # only the fuel/fodder COMMONS proper (role 'commons') must lie on the windward back-slope;
            # the general marginal hill land types - 'grazing' scrub, open 'pasture', coppice 'woodland' -
            # can sit on ANY dry flank (the NE upland, the SW corner, the uphill head) and are exempt from
            # the beyond-the-windbreak toposequence rule (they are the hinterland catena, not the fuel commons)
            near = [
                (round(c["x"]), round(c["y"])) for c in commons if c.get("role", "commons") not in ("grazing", "pasture", "woodland") and (c["x"] - ccx) * wvx + (c["y"] - ccy) * wvy <= wb_proj + 5
            ]
            check(
                "commons_beyond_the_windbreak",
                not near,
                f"fuel/fodder commons {near[:2]} sit between the village and its back-grove (or on the field "
                f"side), not BEYOND the windbreak - the toposequence is village -> back-grove -> commons, so the "
                f"degraded grazing lies on the far windward side, past the protected wood",
            )
    return _kept(locals(), ('c', 'ccx', 'ccy', 'g', 'h', 'near', 'wb_proj', 'wbs'))


# WEALTH VARIATION: farmhouses are not one uniform size - a modest wealth tier (recorded as `wealth`)
# scales the rendered house and, with it, the grove, so holdings read as ranging from the landless
# mizunomi to a honbyakushO landholder. Verify the tiers are ACTIVE so a regression that flattens
# them to one size is caught. (Only the house + grove carry the signal; the yard/garden/shed stay
# uniform - scaling them coupled into farmstead placement and dropped houses.) WHY: settlements.md.


def _seg_0285_098__h_3(*, h: Any = _UNBOUND, houses: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.098 (h, plain) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        plain = [h for h in houses if h.get("role") != "headman"]
    return _kept(locals(), ('h', 'plain'))


def _seg_0285_099__farmhouse_sizes_vary(
    *,
    _eff: Any = _UNBOUND,
    areas: Any = _UNBOUND,
    check: Any = _UNBOUND,
    h: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    lop: Any = _UNBOUND,
    med: Any = _UNBOUND,
    plain: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    varied: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.099 (farmhouse_aspect_in_range, farmhouse_sizes_vary) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city') and len(plain) >= 10:
        # measure the ACTUAL rendered-footprint spread, which is carried TWO ways: the DISPERSED path
        # keeps a uniform base w x h and scales the drawn house by a `wealth` tier (0.9/1.0/1.12), while
        # the NUCLEATED path jitters the base w x h (length/depth) directly at wealth 1.0. Fold both in
        # via effective area = w * h * wealth^2 (the wealth factor scales each dimension), so a regression
        # that flattens houses to one size is caught under EITHER encoding.
        def _eff(h: dict[str, Any]) -> float:
            return float(h["w"] * h["h"] * (h.get("wealth", 1.0) ** 2))

        areas = sorted(_eff(h) for h in plain)
        med = areas[len(areas) // 2] or 1
        varied = sum(1 for h in plain if abs(_eff(h) - med) > 0.05 * med)
        check(
            "farmhouse_sizes_vary",
            varied >= 0.2 * len(plain),
            f"farmhouses show no size variation ({varied}/{len(plain)} off the median footprint) - a modest spread of homestead sizes is expected (they look flattened to one size)",
        )
        # a minka is rectangular but within the ~1.3-2.5:1 norm - a house grew by adding bays
        # (longer), never into a 4:1 shed. Guard the aspect so the length jitter stays plausible.
        lop = [[round(h["x"]), round(h["y"])] for h in houses if min(h["w"], h["h"]) > 0 and max(h["w"], h["h"]) / min(h["w"], h["h"]) > 2.7]
        check("farmhouse_aspect_in_range", not lop, f"farmhouse(s) {lop[:3]} are more than 2.7:1 long-to-wide - a minka stays roughly 1.3-2.5:1 (it lengthened by bays, it did not become a shed)")
    return _kept(locals(), ('_eff', 'areas', 'h', 'lop', 'med', 'varied'))


# THE DEAD - a full funerary geography. Every settlement above a hamlet buries its cremated dead
# (a hamlet's go to the village district's ground, just as it has no shrine or headman). GRAVEYARDS
# are temple parish grounds: the state merged Shinsei and Fortune worship, so ANY temple may host
# one (a temple opts out with graveyard=False - a new or special-purpose hall). A Shinto SHRINE
# keeps death-pollution (kegare) at arm's length, so no grave site sits hard against a shrine. A
# CITY additionally shows 2-4 graveyards split inside/outside the walls, the ruling clan's walled
# MAUSOLEUM by the samurai quarter, an extramural CREMATION GROUND, and a pauper OSSUARY beside it.


def _seg_0286_000__cems(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0286.000 (cems) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital'):
        cems = M.get("cemeteries", [])
    return _kept(locals(), ('cems',))


def _seg_0286_001__maus(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0286.001 (maus) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital'):
        maus = M.get("mausoleums", [])
    return _kept(locals(), ('maus',))


def _seg_0286_002__crem(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0286.002 (crem) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital'):
        crem = M.get("cremation_grounds", [])
    return _kept(locals(), ('crem',))


def _seg_0286_003__oss(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0286.003 (oss) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital'):
        oss = M.get("ossuaries", [])
    return _kept(locals(), ('oss',))


def _seg_0286_004__relig(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0286.004 (relig) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital'):
        relig = M.get("religious", [])
    return _kept(locals(), ('relig',))


def _seg_0286_005__r(*, r: Any = _UNBOUND, relig: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0286.005 (r, shrines) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital'):
        shrines = [r for r in relig if r.get("kind") in ("shrine", "small_shrine")]
    return _kept(locals(), ('r', 'shrines'))


def _seg_0286_006__r_1(*, r: Any = _UNBOUND, relig: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0286.006 (r, temples) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital'):
        temples = [r for r in relig if r.get("kind") in ("monastery", "temple")]
    return _kept(locals(), ('r', 'temples'))


def _seg_0286_007__wall(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0286.007 (wall) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital'):
        wall = M.get("wall")
    return _kept(locals(), ('wall',))


def _seg_0286_008___inside(*, px: Any = _UNBOUND, py: Any = _UNBOUND, scale: Any = _UNBOUND, wall: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0286.008 (_inside) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital'):

        def _inside(px: float, py: float) -> bool:
            return bool(wall) and point_in_poly(px, py, wall)

    return _kept(locals(), ('_inside',))


# PRESENCE: a village/town has >=1 graveyard; a city shows 2-4 (a few parish grounds,
# consolidated over the centuries - not one, not a dozen)


def _seg_0286_009__city_graveyard_count(*, cems: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0286.009 (city_graveyard_count, settlement_has_cemetery) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital'):
        if scale == "city":
            check("city_graveyard_count", 2 <= len(cems) <= 4, f"a provincial city should show 2-4 temple graveyards; found {len(cems)}")
        else:
            check(
                "settlement_has_cemetery",
                len(cems) >= 1,
                f"a {scale} buries its dead but has no graveyard - add s.cemetery(...) (a hamlet is exempt; its dead go to the village district's burial ground)",
            )
    return _kept(locals(), ())


# CHURCHYARD (L7R): a village SHRINE is officially Shinseist and its monk performs the funerary rites, so
# the graveyard sits IN the shrine's precinct - like a Buddhist-temple parish ground - NOT held away from
# it (real-Japan Shinto kegare does NOT apply: the shrine IS the death-handling institution). Only the
# sacred HALL + its TORII gateway stay clear: graves fill the yard AROUND them, never ON them. WHY:
# settlements.md "Historical grounding" (Brotherhood of Shinsei monks tend the country shrines and the dead).


def _seg_0286_010___on_shrine_building(
    *, M: Any = _UNBOUND, r: Any = _UNBOUND, sc: Any = _UNBOUND, scale: Any = _UNBOUND, shrines: Any = _UNBOUND, site: Any = _UNBOUND, t: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0286.010 (_on_shrine_building) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital'):

        def _on_shrine_building(site: dict[str, Any]) -> bool:
            sc = rect_corners(_struct_rect(site))
            for r in shrines:
                if sat_overlap(sc, rect_corners({"x": r["x"], "y": r["y"], "w": r["w"] + 20, "h": r["h"] + 20, "rot": 0})):
                    return True
            return any(sat_overlap(sc, rect_corners({"x": t[0], "y": t[1] + 4, "w": 58, "h": 48, "rot": 0})) for t in M.get("torii", []))

    return _kept(locals(), ('_on_shrine_building',))


def _seg_0286_011__on_bldg(*, _on_shrine_building: Any = _UNBOUND, cems: Any = _UNBOUND, maus: Any = _UNBOUND, s: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0286.011 (on_bldg, s) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital'):
        on_bldg = [(round(s["x"]), round(s["y"])) for s in cems + maus if _on_shrine_building(s)]
    return _kept(locals(), ('on_bldg', 's'))


def _seg_0286_012__cemetery_clear_of_shrine(*, check: Any = _UNBOUND, on_bldg: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0286.012 (cemetery_clear_of_shrine) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital'):
        check(
            "cemetery_clear_of_shrine",
            not on_bldg,
            f"grave site(s) sit ON the shrine hall or its torii gateway: {on_bldg[:3]} - the monk tends the graves "
            f"so they fill the shrine's yard, but the sacred hall + gateway themselves stay clear of burials",
        )
    return _kept(locals(), ())


# MARSH is unbuildable wet ground: no SACRED hall and no BURIAL ground sits on a reed marsh - you would
# never raise a shrine or dig graves in a bog (they belong on DRY ground, the spur / high ground). The
# `toe` marsh is the wet valley floor; a `pond_fringe` (a thin decorative shore ring) is exempt. GM 2026-07.


def _seg_0286_013__bog(*, M: Any = _UNBOUND, m: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0286.013 (bog, m) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital'):
        bog = [m["poly"] for m in M.get("marshes", []) if m.get("role") != "pond_fringe" and m.get("poly")]
    return _kept(locals(), ('bog', 'm'))


def _seg_0286_014__sacred_and_graves_off_marsh(
    *,
    _on_marsh: Any = _UNBOUND,
    bog: Any = _UNBOUND,
    cems: Any = _UNBOUND,
    check: Any = _UNBOUND,
    crem: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    marshy: Any = _UNBOUND,
    maus: Any = _UNBOUND,
    oss: Any = _UNBOUND,
    relig: Any = _UNBOUND,
    s: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    site: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0286.014 (sacred_and_graves_off_marsh) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital') and bog:

        def _on_marsh(site: dict[str, Any]) -> bool:
            return any(point_in_poly(site["x"], site["y"], mp) for mp in bog) or any(point_in_poly(cx, cy, mp) for cx, cy in rect_corners(_struct_rect(site)) for mp in bog)

        marshy = [(round(s["x"]), round(s["y"])) for s in relig + cems + maus + crem + oss if _on_marsh(s)]
        check(
            "sacred_and_graves_off_marsh",
            not marshy,
            f"shrine/temple or grave site(s) {sorted(set(marshy))[:3]} sit on a reed MARSH - a hall is not "
            f"raised and graves are not dug in a bog; site them on DRY ground (the spur / high ground), off the marsh",
        )
    return _kept(locals(), ('_on_marsh', 'marshy', 's'))


# PRECINCT (village): the village graveyard sits BY the shrine (the Shinsei monk's funerary ground),
# mirroring the town/city temple-precinct rule. A HILLTOP shrine is exempt (graves do not climb the
# sacred hill, and a prominent hill-shrine is not the humble earth-god monk's funerary base - as with
# remote_shrine_has_own_well); if every shrine is hilltop, the ground is placed by eye. A hamlet has no
# shrine at all (its dead go to the village district's ground).


def _seg_0286_015__flat_shrines(*, M: Any = _UNBOUND, r: Any = _UNBOUND, scale: Any = _UNBOUND, shrines: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0286.015 (flat_shrines, r) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital'):
        flat_shrines = [r for r in shrines if not (M.get("hill") and in_ellipse(r["x"], r["y"], M["hill"]))]
    return _kept(locals(), ('flat_shrines', 'r'))


def _seg_0286_016__village_graveyard_by_shrine(
    *, c: Any = _UNBOUND, cems: Any = _UNBOUND, check: Any = _UNBOUND, far: Any = _UNBOUND, flat_shrines: Any = _UNBOUND, r: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0286.016 (village_graveyard_by_shrine) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital') and scale == "village" and cems and flat_shrines:
        far = [(round(c["x"]), round(c["y"])) for c in cems if not any(math.hypot(c["x"] - r["x"], c["y"] - r["y"]) < 250 for r in flat_shrines)]
        check(
            "village_graveyard_by_shrine",
            not far,
            f"village graveyard(s) set apart from the shrine: {far[:3]} - the village shrine is Shinseist and its monk performs the funerary rites, so the graveyard sits IN the shrine's precinct",
        )
    return _kept(locals(), ('c', 'far', 'r'))


# WATER SET-BACK: burial grounds keep a clear margin from OPEN WATER (the moat, a stream, or a
# pond), and that margin SCALES WITH THE WATERWAY'S SIZE (water_setback() - a creek needs little,
# a moat/river much more) because a burial ground by big water floods out. The CREMATION ground
# may sit NEARER the water (fire/ritual), so the graveyard naturally lands beyond it. Non-overlap
# is not enough. (Thin irrigation channels are NOT open water and don't trigger this.)
# the moat is OUTSIDE the wall, so an INSIDE-wall ground is shielded from it by the rampart and is
# exempt from the moat term (streams/ponds apply regardless of which side they sit on).


def _seg_0286_017__line_waters(*, M: Any = _UNBOUND, s: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0286.017 (line_waters, s) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital'):
        line_waters = ([(M["moat"], M.get("moat_width", 22), True)] if M.get("moat") else []) + [(s["poly"], s.get("w", 9), False) for s in M.get("streams", [])]
    return _kept(locals(), ('line_waters', 's'))


def _seg_0286_018__pond(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0286.018 (pond) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital'):
        pond = M.get("pond")
    return _kept(locals(), ('pond',))


def _seg_0286_019__f(*, M: Any = _UNBOUND, f: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0286.019 (f, field_outlines) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital'):
        field_outlines = [f["outline"] for f in M.get("fields", [])] + [f["outline"] for f in M.get("flower_fields", [])]
    return _kept(locals(), ('f', 'field_outlines'))


def _seg_0286_020__FIELD_SETBACK(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0286.020 (FIELD_SETBACK) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital'):
        FIELD_SETBACK = 50  # a RICE PADDY is standing water when flooded - a real flood hazard, not a
    return _kept(locals(), ('FIELD_SETBACK',))


#                      trickle - so a burial ground keeps a clear margin from its edge (more than a creek)


def _seg_0286_021__crowded(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0286.021 (crowded) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital'):
        crowded = []  # type: ignore[var-annotated]
    return _kept(locals(), ('crowded',))


def _seg_0286_022__c(
    *,
    FIELD_SETBACK: Any = _UNBOUND,
    c: Any = _UNBOUND,
    cems: Any = _UNBOUND,
    cor: Any = _UNBOUND,
    cr: Any = _UNBOUND,
    crem: Any = _UNBOUND,
    crowded: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    field_outlines: Any = _UNBOUND,
    inside_wall: Any = _UNBOUND,
    is_crem: Any = _UNBOUND,
    is_moat: Any = _UNBOUND,
    k: Any = _UNBOUND,
    line_waters: Any = _UNBOUND,
    near_water: Any = _UNBOUND,
    o: Any = _UNBOUND,
    ol: Any = _UNBOUND,
    oss: Any = _UNBOUND,
    poly: Any = _UNBOUND,
    pond: Any = _UNBOUND,
    sb: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    site: Any = _UNBOUND,
    wall: Any = _UNBOUND,
    width: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0286.022 (c, cor, cr, crowded) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital'):
        for site, is_crem in [(c, False) for c in cems] + [(o, False) for o in oss] + [(cr, True) for cr in crem]:
            cor = rect_corners(site)
            inside_wall = bool(wall) and point_in_poly(site["x"], site["y"], wall)
            near_water = False
            for poly, width, is_moat in line_waters:
                if is_moat and inside_wall:
                    continue
                sb = 30 if is_crem else water_setback(width)  # cremation may sit near water; burials scale
                if min(seg_dist(cx, cy, poly[k], poly[k + 1]) for cx, cy in cor for k in range(len(poly) - 1)) < width / 2 + sb:
                    near_water = True
                    break
            if not near_water and pond:
                sb = 30 if is_crem else 55
                if min(math.hypot(cx - pond[0], cy - pond[1]) for cx, cy in cor) < max(pond[2], pond[3]) + sb:
                    near_water = True
            # RICE PADDIES flood, so a BURIAL ground keeps a creek-level set-back from any field edge too
            # (treat the field boundary like a small watercourse). The cremation ground is exempt (a fire
            # site, not flood-sensitive graves).
            if not near_water and not is_crem:
                for ol in field_outlines:
                    if min(poly_dist(cx, cy, ol) for cx, cy in cor) < FIELD_SETBACK:
                        near_water = True
                        break
            if near_water:
                crowded.append((round(site["x"]), round(site["y"])))
    return _kept(locals(), ('c', 'cor', 'cr', 'crowded', 'cx', 'cy', 'inside_wall', 'is_crem', 'is_moat', 'k', 'near_water', 'o', 'ol', 'poly', 'sb', 'site', 'width'))


def _seg_0286_023__funerary_set_back_from_water(*, check: Any = _UNBOUND, crowded: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0286.023 (funerary_set_back_from_water) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital'):
        check(
            "funerary_set_back_from_water",
            not crowded,
            f"grave site(s) crowd open water OR a flood-prone rice paddy - a burial ground's set-back scales with "
            f"the waterway (a moat/river needs far more room than a creek; field edges count as creeks): {crowded[:3]}",
        )
    return _kept(locals(), ())


# THE CREMATORY ADJOINS AN EXTERNAL BURIAL GROUND: the body is burned and its cremated bones
# interred next door, so a cremation ground sits ADJACENT to an EXTERNAL (outside-the-walls)
# cemetery - together they form the extramural funerary complex beyond a gate. (An unwalled
# settlement has no walls, so any of its cemeteries counts as external.)


def _seg_0286_024__cremation_ground_by_external_cemetery(
    *,
    M: Any = _UNBOUND,
    ROAD_SETBACK: Any = _UNBOUND,
    _edge_gap: Any = _UNBOUND,
    _rdist: Any = _UNBOUND,
    a: Any = _UNBOUND,
    b: Any = _UNBOUND,
    between: Any = _UNBOUND,
    c: Any = _UNBOUND,
    cems: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cr: Any = _UNBOUND,
    crem: Any = _UNBOUND,
    crem_on_road: Any = _UNBOUND,
    ext_cems: Any = _UNBOUND,
    gx: Any = _UNBOUND,
    gy: Any = _UNBOUND,
    k: Any = _UNBOUND,
    lonely: Any = _UNBOUND,
    mainroad: Any = _UNBOUND,
    near_t: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    t: Any = _UNBOUND,
    temples_r: Any = _UNBOUND,
    wall: Any = _UNBOUND,
    x: Any = _UNBOUND,
    y: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0286.024 (cremation_ground_by_external_cemetery, cremation_ground_not_between_temple_and_road, cremation_ground_set_back_from_main_road) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital') and crem:
        ext_cems = [c for c in cems if not (wall and point_in_poly(c["x"], c["y"], wall))]

        def _edge_gap(a: dict[str, Any], b: dict[str, Any]) -> float:
            gx = max(0.0, abs(a["x"] - b["x"]) - (a["w"] + b["w"]) / 2)
            gy = max(0.0, abs(a["y"] - b["y"]) - (a["h"] + b["h"]) / 2)
            return math.hypot(gx, gy)

        lonely = [(round(cr["x"]), round(cr["y"])) for cr in crem if not any(_edge_gap(cr, c) <= 70 for c in ext_cems)]
        check(
            "cremation_ground_by_external_cemetery",
            not lonely,
            f"cremation ground(s) not adjacent to an external (outside-the-walls) burial ground: {lonely[:3]} - "
            f"the body is cremated and its bones interred next door, so the crematory adjoins an extramural cemetery",
        )

        # SET BACK FROM THE MAIN ROAD: the crematory is marginal, polluting land reached by a minor
        # funeral path, NOT the high street - so it keeps clear of the Imperial / trunk road (town
        # streets and minor lanes don't count; only the main road). The temple's own parish graveyard
        # may sit by the temple wherever it is, but the smoking pyre stays off the main thoroughfare.
        ROAD_SETBACK = 130
        mainroad = M.get("road")
        if mainroad:

            def _rdist(x: float, y: float) -> float:
                return min(seg_dist(x, y, mainroad[k], mainroad[k + 1]) for k in range(len(mainroad) - 1))

            crem_on_road = [(round(cr["x"]), round(cr["y"])) for cr in crem if _rdist(cr["x"], cr["y"]) < ROAD_SETBACK]
            check(
                "cremation_ground_set_back_from_main_road",
                not crem_on_road,
                f"cremation ground(s) crowd the main road: {crem_on_road[:3]} - a crematory is marginal land reached "
                f"by a minor funeral path, not high-street frontage; keep it >= {ROAD_SETBACK}px off the trunk road",
            )
            # NOT BETWEEN its temple and the road: you should not walk past the pyre to reach the
            # monastery. The crematory sits BEHIND or beside its nearest temple (at least as far from
            # the road as that temple, less a small tolerance), never on the road-side approach to it.
            # (The temple's own graveyard may still sit road-side by the temple - this is the pyre only.)
            temples_r = [t for t in M.get("religious", []) if t.get("kind") in ("monastery", "temple")]
            between = []
            for cr in crem:
                near_t = [t for t in temples_r if math.hypot(t["x"] - cr["x"], t["y"] - cr["y"]) <= 400]
                if near_t:
                    t = min(near_t, key=lambda t: math.hypot(t["x"] - cr["x"], t["y"] - cr["y"]))
                    if _rdist(cr["x"], cr["y"]) < _rdist(t["x"], t["y"]) - 40:
                        between.append((round(cr["x"]), round(cr["y"])))
            check(
                "cremation_ground_not_between_temple_and_road",
                not between,
                f"cremation ground(s) sit between a temple and the road: {between[:3]} - you should not walk past "
                f"the pyre to reach the monastery; put the crematory BEHIND or beside its temple, off the road side",
            )
    return _kept(locals(), ('ROAD_SETBACK', '_edge_gap', '_rdist', 'between', 'c', 'cr', 'crem_on_road', 'ext_cems', 'lonely', 'mainroad', 'near_t', 't', 'temples_r'))


# PRECINCT: a graveyard is a temple parish ground - it sits by a temple. (At CITY scale only an
# INSIDE-wall graveyard must; an OUTSIDE-wall one is the extramural common burial ground, exempt.)


def _seg_0286_025__cemetery_in_temple_precinct(
    *,
    _inside: Any = _UNBOUND,
    c: Any = _UNBOUND,
    cems: Any = _UNBOUND,
    check: Any = _UNBOUND,
    r: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    stray: Any = _UNBOUND,
    temples: Any = _UNBOUND,
    wall: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0286.025 (cemetery_in_temple_precinct) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital') and scale in ("town", "city") and cems and temples:
        # a graveyard must be by a temple UNLESS it is outside a walled settlement's wall (then it
        # is the extramural common burial ground - exempt). An unwalled town has no outside, so all
        # its graveyards are parish grounds and must sit by a monastery.
        stray = [
            (round(c["x"]), round(c["y"]))
            for c in cems
            if c.get("parish", True) and (not wall or _inside(c["x"], c["y"])) and not any(math.hypot(c["x"] - r["x"], c["y"] - r["y"]) < 230 for r in temples)
        ]
        check(
            "cemetery_in_temple_precinct",
            not stray,
            f"graveyard(s) not in any temple precinct: {stray[:3]} - a parish ground sits by its temple (a walled settlement's extramural common ground, and any parish=False plot, are exempt)",
        )
    return _kept(locals(), ('c', 'r', 'stray'))


# SPLIT: any WALLED settlement (town or city) keeps a graveyard both inside AND outside the
# walls - and the EXTERIOR common ground is noticeably larger than the cramped intramural one
# (there is room beyond the walls; inside, the temple grounds are hemmed in by the city).


def _seg_0286_026__walled_graveyards_inside_and_outside(
    *,
    _inside: Any = _UNBOUND,
    bi: Any = _UNBOUND,
    bo: Any = _UNBOUND,
    c: Any = _UNBOUND,
    cems: Any = _UNBOUND,
    check: Any = _UNBOUND,
    ins: Any = _UNBOUND,
    out: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    wall: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0286.026 (walled_exterior_cemetery_larger, walled_graveyards_inside_and_outside) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital') and wall and cems:
        ins = [c for c in cems if _inside(c["x"], c["y"])]
        out = [c for c in cems if not _inside(c["x"], c["y"])]
        check(
            "walled_graveyards_inside_and_outside",
            bool(ins) and bool(out),
            f"a walled settlement keeps a graveyard both inside AND outside the walls (inside {len(ins)}, outside {len(out)}) - keep at least one of each",
        )
        if ins and out:
            bi = max(c["w"] * c["h"] for c in ins)
            bo = max(c["w"] * c["h"] for c in out)
            check(
                "walled_exterior_cemetery_larger",
                bo >= 1.3 * bi,
                f"the exterior common burial ground should be noticeably larger than the cramped intramural "
                f"ground (outside {bo:.0f}px2 vs inside {bi:.0f}px2; want >= 1.3x) - there is room beyond the walls",
            )
    return _kept(locals(), ('bi', 'bo', 'c', 'ins', 'out'))


# BELL-AND-DRUM TOWER (GM 2026-07-24; settlements.md "The bell-and-drum tower"). The
# morning-bell/evening-drum institution followed the WALL, not the population: the tower
# signaled dawn gate-opening, the dusk gate-closing that began the street curfew, and the
# five night watches - so every WALLED seat (city or walled town) keeps EXACTLY ONE
# combined tower at the main street crossing (the county-seat kit; a paired gulou/zhonglou
# on an axis is capital grammar - Pingyao, a wealthy county seat, has exactly one). An
# UNWALLED town has no gates to close: its time signal is the monastery's bell (the Edo
# toki-no-kane pattern, usually a contracted temple bell), implied within the precinct -
# no tower, no glyph. Fire watch was a SEPARATE institution in both reference cultures
# (Song Kaifeng ran dedicated fire-lookout towers; Edo split the licensed time bell from
# the hinomi-yagura), so the fire towers do not satisfy this check and the drum tower is
# not fire watch. "At the main crossing" = within ~80px of two NON-PARALLEL road/street
# segments (a corner of the central crossroads).


def _seg_0286_027__walled_settlement_has_drum_tower(
    *,
    M: Any = _UNBOUND,
    _dt_at_crossing: Any = _UNBOUND,
    _inside: Any = _UNBOUND,
    a: Any = _UNBOUND,
    angs: Any = _UNBOUND,
    b: Any = _UNBOUND,
    check: Any = _UNBOUND,
    dts: Any = _UNBOUND,
    i: Any = _UNBOUND,
    ok_dt: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    st: Any = _UNBOUND,
    t: Any = _UNBOUND,
    wall: Any = _UNBOUND,
    ways: Any = _UNBOUND,
    wy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0286.027 (walled_settlement_has_drum_tower) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital') and wall and scale in ("town", "city"):
        dts = M.get("drum_towers", [])
        ways = ([M["road"]] if M.get("road") else []) + [st.get("pts", []) for st in M.get("town_streets", [])]

        def _dt_at_crossing(t: dict[str, Any]) -> bool:
            angs = []
            for wy in ways:
                for i in range(len(wy) - 1):
                    if seg_dist(t["x"], t["y"], wy[i], wy[i + 1]) < 80:
                        angs.append(math.atan2(wy[i + 1][1] - wy[i][1], wy[i + 1][0] - wy[i][0]) % math.pi)
            return any(min(abs(a - b), math.pi - abs(a - b)) > 0.5 for a in angs for b in angs)

        ok_dt = len(dts) == 1 and _inside(dts[0]["x"], dts[0]["y"]) and _dt_at_crossing(dts[0])
        check(
            "walled_settlement_has_drum_tower",
            ok_dt,
            f"{len(dts)} bell-and-drum tower(s) at the main crossing - every walled seat keeps EXACTLY ONE "
            f"combined bell-and-drum tower (s.drum_tower) inside the walls at the main street crossing "
            f"(within ~80px of two non-parallel road/street segments); it signals the gate curfew and the "
            f"night watches, which the fire towers do not cover; an unwalled town is exempt (its time "
            f"signal is the monastery's bell)",
        )
    return _kept(locals(), ('_dt_at_crossing', 'angs', 'dts', 'ok_dt', 'st', 'ways'))


def _seg_0286_028__town_monasteries_have_graveyards(
    *, c: Any = _UNBOUND, cems: Any = _UNBOUND, check: Any = _UNBOUND, needy_t: Any = _UNBOUND, r: Any = _UNBOUND, scale: Any = _UNBOUND, temples: Any = _UNBOUND, unserved_t: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0286.028 (town_monasteries_have_graveyards) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital') and scale == "town":
        # every monastery that CAN host a graveyard keeps one in its precinct (the town analog
        # of city_temples_have_graveyards - GM audit 2026-07; graveyard=False opts out, e.g. a
        # small relic monastery whose dead go to the parish ground)
        needy_t = [r for r in temples if r.get("graveyard", True)]
        unserved_t = [r.get("label", (round(r["x"]), round(r["y"]))) for r in needy_t if not any(math.hypot(c["x"] - r["x"], c["y"] - r["y"]) < 230 for c in cems)]
        check(
            "town_monasteries_have_graveyards",
            not unserved_t,
            f"monastery(ies) with no graveyard in their precinct: {unserved_t[:3]} - a town monastery keeps the parish (danka) burial ground unless it opts out (graveyard=False)",
        )
    return _kept(locals(), ('c', 'needy_t', 'r', 'unserved_t'))


def _seg_0286_029__city_temples_have_graveyards(
    *,
    M: Any = _UNBOUND,
    URBAN: Any = _UNBOUND,
    _inside: Any = _UNBOUND,
    anchor: Any = _UNBOUND,
    b: Any = _UNBOUND,
    c: Any = _UNBOUND,
    cems: Any = _UNBOUND,
    check: Any = _UNBOUND,
    crem: Any = _UNBOUND,
    crem_out: Any = _UNBOUND,
    gov: Any = _UNBOUND,
    m2: Any = _UNBOUND,
    maus: Any = _UNBOUND,
    maus_ok: Any = _UNBOUND,
    needy: Any = _UNBOUND,
    o: Any = _UNBOUND,
    oss: Any = _UNBOUND,
    oss_ok: Any = _UNBOUND,
    r: Any = _UNBOUND,
    sam: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    temples: Any = _UNBOUND,
    unserved: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0286.029 (city_has_cremation_ground, city_has_mausoleum, city_has_ossuary, city_temples_have_graveyards) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital') and URBAN:
        # every temple that CAN host a graveyard has one in its precinct (graveyard=False opts out)
        needy = [r for r in temples if r.get("graveyard", True)]
        unserved = [r.get("label", (round(r["x"]), round(r["y"]))) for r in needy if not any(math.hypot(c["x"] - r["x"], c["y"] - r["y"]) < 230 for c in cems)]
        check(
            "city_temples_have_graveyards",
            not unserved,
            f"temple(s) with no graveyard in their precinct: {unserved[:3]} - Shinsei and Fortune worship are merged, so every temple keeps a burial ground unless it opts out (graveyard=False)",
        )
        # CLAN MAUSOLEUM: a walled crypt precinct inside the walls, by the samurai/government quarter
        gov = M.get("governor_mansion")
        sam = [b for b in M.get("buildings", []) if b.get("kind") in ("samurai", "samurai_large")]
        if gov:
            anchor = (gov["x"], gov["y"])
        elif sam:
            anchor = (sum(b["x"] for b in sam) / len(sam), sum(b["y"] for b in sam) / len(sam))
        else:
            anchor = None
        maus_ok = bool(maus) and any(_inside(m2["x"], m2["y"]) for m2 in maus) and (anchor is None or any(math.hypot(m2["x"] - anchor[0], m2["y"] - anchor[1]) < 640 for m2 in maus))
        check(
            "city_has_mausoleum",
            maus_ok,
            "a provincial city needs the ruling clan's ancestral MAUSOLEUM (s.mausoleum) inside the walls, by the samurai/government quarter - a walled crypt precinct for the elite dead",
        )
        # CREMATION GROUND: smoke, fire, and pollution push the crematory OUTSIDE the walls
        crem_out = [c for c in crem if not _inside(c["x"], c["y"])]
        check(
            "city_has_cremation_ground",
            bool(crem_out),
            "a city cremates its dead at a CREMATION GROUND (s.cremation_ground) OUTSIDE the walls - monk-run with burakumin assistants; smoke and fire keep it beyond a gate",
        )
        # PAUPER OSSUARY: outside the walls, beside the cremation ground
        oss_ok = any(not _inside(o["x"], o["y"]) and any(math.hypot(o["x"] - c["x"], o["y"] - c["y"]) < 320 for c in crem) for o in oss)
        check(
            "city_has_ossuary",
            oss_ok,
            "a city needs a pauper OSSUARY mound (s.ossuary) outside the walls by the cremation ground - the communal bones of the poor and the unconnected dead (muenbotoke)",
        )
    return _kept(locals(), ('anchor', 'b', 'c', 'crem_out', 'gov', 'm2', 'maus_ok', 'needy', 'o', 'oss_ok', 'r', 'sam', 'unserved'))


def _seg_0286_030__town_has_cremation_ground(
    *,
    M: Any = _UNBOUND,
    _crem_lim: Any = _UNBOUND,
    b: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    crem: Any = _UNBOUND,
    dwell_t: Any = _UNBOUND,
    far_crem: Any = _UNBOUND,
    h: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    o: Any = _UNBOUND,
    oss: Any = _UNBOUND,
    oss_t: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    wall_oss: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0286.030 (town_has_cremation_ground, town_has_ossuary) - body verbatim from _seg_0286__cemetery_clear_of_shrine (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('village', 'town', 'city', 'capital') and scale == "town":
        # a county town cremates too - a cremation ground at the edge, clear of the dwellings
        dwell_t = M.get("houses", []) + [b for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS]
        # 120 real ft to the DWELLING'S EDGE, not to its center - the standing pollution
        # separation, measured the way it would be paced out. (Converted 2026-07-27: this was
        # the third instance of the center-distance defect, and the one nobody had noticed,
        # since a cremation ground is drawn large enough that the two forms differ by ~50 ft.)
        _crem_lim = 120.0 / float(meta.get("ftpx") or 1)
        far_crem = [c for c in crem if not any(within_edge_gap(c, h, _crem_lim) for h in dwell_t)] if dwell_t else crem
        check(
            "town_has_cremation_ground",
            bool(far_crem),
            "a county town cremates its dead at a CREMATION GROUND (s.cremation_ground) at the edge, clear of the dwellings - monk-run with burakumin assistants",
        )
        # PAUPER OSSUARY: the county town's muenzuka stands by its cremation ground (the town
        # analog of city_has_ossuary - GM audit 2026-07); outside the rampart when walled
        wall_oss = M.get("wall")
        oss_t = [o for o in oss if not (wall_oss and len(wall_oss) >= 3 and point_in_poly(o["x"], o["y"], wall_oss))]
        check(
            "town_has_ossuary",
            any(any(math.hypot(o["x"] - c["x"], o["y"] - c["y"]) < 320 for c in crem) for o in oss_t),
            "a county town needs a pauper OSSUARY mound (s.ossuary) beside its cremation ground - the communal bones of the poor and the unconnected dead (muenbotoke)",
        )
    return _kept(locals(), ('_crem_lim', 'b', 'c', 'dwell_t', 'far_crem', 'h', 'o', 'oss_t', 'wall_oss'))


# GEOMETRY SANITY AT EVERY SCALE (GM audit 2026-07: this only ran for cities): a wall vertex
# millions of px off the canvas is malformed input at any scale - towns have walls too.


def _seg_0287__geometry_within_canvas(
    *,
    M: Any = _UNBOUND,
    _Hg: Any = _UNBOUND,
    _Wg: Any = _UNBOUND,
    _oobg: Any = _UNBOUND,
    _wallg: Any = _UNBOUND,
    check: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    p: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    vx: Any = _UNBOUND,
    vy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 287 (geometry_within_canvas) - body verbatim from the legacy gate() (feature 022)."""
    if scale != "city":
        _Wg = meta.get("W") or 3200
        _Hg = meta.get("H") or 2700
        _wallg = M.get("wall") or []
        _oobg = [(round(vx), round(vy)) for vx, vy in [tuple(p) for p in _wallg] if not (-_Wg <= vx <= 2 * _Wg and -_Hg <= vy <= 2 * _Hg)]
        check(
            "geometry_within_canvas",
            not _oobg,
            f"wall vertex(es) far outside the canvas ({_Wg}x{_Hg}): {sorted(set(_oobg))[:4]} - malformed input; a valid settlement's geometry lies near the drawn canvas",
        )
    return _kept(locals(), ('_Hg', '_Wg', '_oobg', '_wallg', 'p', 'vx', 'vy'))


# LABEL TEXT renders ON TOP of everything: no part of a label may be covered. Labels live in the
# topmost layer (s.add_label), above the TOP-layer structures (gate furniture, kido, torii); the
# check guards it - a label overlapped by any structure drawn OVER it (higher draw-z) is covered.


def _seg_0288__occluders() -> dict[str, Any]:
    """Gate segment 288 (occluders) - body verbatim from the legacy gate() (feature 022)."""
    occluders = []  # type: ignore[var-annotated]
    return _kept(locals(), ('occluders',))


def _seg_0289__gs_1(*, M: Any = _UNBOUND, gs: Any = _UNBOUND, occluders: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 289 (gs, occluders) - body verbatim from the legacy gate() (feature 022)."""
    for gs in M.get("gate_structs", []):
        if gs.get("z") is not None:
            occluders.append((gs["x"] - gs["w"] / 2, gs["y"] - gs["h"] / 2, gs["x"] + gs["w"] / 2, gs["y"] + gs["h"] / 2, gs["z"]))
    return _kept(locals(), ('gs', 'occluders'))


def _seg_0290__kd(*, M: Any = _UNBOUND, kd: Any = _UNBOUND, occluders: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 290 (kd, occluders) - body verbatim from the legacy gate() (feature 022)."""
    for kd in M.get("kido", []):
        if kd.get("z") is not None and kd.get("bbox"):
            occluders.append((kd["bbox"][0], kd["bbox"][1], kd["bbox"][2], kd["bbox"][3], kd["z"]))
    return _kept(locals(), ('kd', 'occluders'))


def _seg_0291__occluders_1(*, M: Any = _UNBOUND, occluders: Any = _UNBOUND, t: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 291 (occluders, t) - body verbatim from the legacy gate() (feature 022)."""
    for t in M.get("torii", []):
        if len(t) >= 3:
            occluders.append((t[0] - 22, t[1] - 28, t[0] + 22, t[1] + 12, t[2]))  # the arch's drawn extent
    return _kept(locals(), ('occluders', 't'))


def _seg_0292__covered_labels() -> dict[str, Any]:
    """Gate segment 292 (covered_labels) - body verbatim from the legacy gate() (feature 022)."""
    covered_labels = []  # type: ignore[var-annotated]
    return _kept(locals(), ('covered_labels',))


def _seg_0293__L_2(
    *,
    L: Any = _UNBOUND,
    covered_labels: Any = _UNBOUND,
    labels: Any = _UNBOUND,
    lx0: Any = _UNBOUND,
    lx1: Any = _UNBOUND,
    ly0: Any = _UNBOUND,
    ly1: Any = _UNBOUND,
    lz: Any = _UNBOUND,
    occluders: Any = _UNBOUND,
    ox0: Any = _UNBOUND,
    ox1: Any = _UNBOUND,
    oy0: Any = _UNBOUND,
    oy1: Any = _UNBOUND,
    oz: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 293 (L, covered_labels, lx0, lx1) - body verbatim from the legacy gate() (feature 022)."""
    for L in labels:
        lx0, ly0, lx1, ly1, lz = L[0], L[1], L[2], L[3], L[4]
        for ox0, oy0, ox1, oy1, oz in occluders:
            if oz > lz and lx0 < ox1 and ox0 < lx1 and ly0 < oy1 and oy0 < ly1:
                covered_labels.append(L[5] if len(L) > 5 else "label")
                break
    return _kept(locals(), ('L', 'covered_labels', 'lx0', 'lx1', 'ly0', 'ly1', 'lz', 'ox0', 'ox1', 'oy0', 'oy1', 'oz'))


def _seg_0294__labels_render_on_top(*, check: Any = _UNBOUND, covered_labels: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 294 (labels_render_on_top) - body verbatim from the legacy gate() (feature 022)."""
    check("labels_render_on_top", not covered_labels, f"label text covered by a structure drawn over it (a label must render on top of everything, fully readable): {sorted(set(covered_labels))}")
    return _kept(locals(), ())


def _seg_0295__hill(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 295 (hill) - body verbatim from the legacy gate() (feature 022)."""
    hill = M.get("hill")
    return _kept(locals(), ('hill',))


def _seg_0296__no_field_on_hill(
    *,
    M: Any = _UNBOUND,
    check: Any = _UNBOUND,
    dp: Any = _UNBOUND,
    dp_onhill: Any = _UNBOUND,
    f: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    hill: Any = _UNBOUND,
    onhill: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    v: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 296 (dry_plots_off_hill, no_field_on_hill) - body verbatim from the legacy gate() (feature 022)."""
    if hill:
        onhill = [f["name"] for f in fields if any(in_ellipse(px, py, hill) for px, py in f["outline"])]
        check("no_field_on_hill", not onhill, f"on hill: {onhill}")
        # DRY PLOTS OBEY THE SAME RULE (feature 013): a hill slope carries dry crops / tea / woodland /
        # scrub, never flooded paddy - but a near-ring dry-field tiler (near_ring_cropland) could stray
        # onto the slope. no_field_on_hill reads only M["fields"] (paddy/veg envelopes), so this closes
        # the dry-plot half. A plot may TOUCH the toe; only a plot whose CENTROID sits on the hill fires
        # (the tiler's own guard keeps plots off the slope, so a centroid on the hill means the guard broke).
        dp_onhill = [
            [round(sum(v[0] for v in dp["poly"]) / len(dp["poly"])), round(sum(v[1] for v in dp["poly"]) / len(dp["poly"]))]
            for dp in M.get("dry_plots", [])
            if dp.get("poly") and len(dp["poly"]) >= 3 and in_ellipse(sum(v[0] for v in dp["poly"]) / len(dp["poly"]), sum(v[1] for v in dp["poly"]) / len(dp["poly"]), hill)
        ]
        check("dry_plots_off_hill", not dp_onhill, f"dry crop plot(s) centered on the hill (paddy/field needs flat ground; a slope carries dry hill-crops/tea/woodland/scrub only): {dp_onhill[:5]}")
    return _kept(locals(), ('dp', 'dp_onhill', 'f', 'onhill', 'px', 'py', 'v'))


# every watercourse - irrigation channel OR natural stream - must connect what it
# claims to: each end anchored to its pond / off-map edge / field / forest


def _seg_0297__pond(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 297 (pond) - body verbatim from the legacy gate() (feature 022)."""
    pond = M.get("pond")
    return _kept(locals(), ('pond',))


def _seg_0298__forest(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 298 (forest) - body verbatim from the legacy gate() (feature 022)."""
    forest = M.get("forest")
    return _kept(locals(), ('forest',))


def _seg_0299__anchored(
    *,
    EX0: Any = _UNBOUND,
    EX1: Any = _UNBOUND,
    EY0: Any = _UNBOUND,
    EY1: Any = _UNBOUND,
    M: Any = _UNBOUND,
    anchor: Any = _UNBOUND,
    dp: Any = _UNBOUND,
    fd: Any = _UNBOUND,
    field_by: Any = _UNBOUND,
    fo: Any = _UNBOUND,
    forest: Any = _UNBOUND,
    i: Any = _UNBOUND,
    k: Any = _UNBOUND,
    pond: Any = _UNBOUND,
    pt: Any = _UNBOUND,
    sp: Any = _UNBOUND,
    st: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 299 (anchored) - body verbatim from the legacy gate() (feature 022)."""

    def anchored(pt: Pt, anchor: dict[str, Any]) -> bool:
        k = anchor["kind"]
        if k == "pond":
            return bool(pond) and in_ellipse(pt[0], pt[1], pond, 1.02)
        if k == "offmap":
            return bool(min(pt[0] - EX0, EX1 - pt[0], pt[1] - EY0, EY1 - pt[1]) <= 32)
        if k == "forest":
            return bool(forest) and point_in_poly(pt[0], pt[1], forest)
        if k == "stream":
            return any(seg_dist(pt[0], pt[1], sp[i], sp[i + 1]) < 30 for st in M.get("streams", []) for sp in [st["poly"]] for i in range(len(sp) - 1))
        if k == "field":
            fo: Any = field_by.get(anchor["name"])
            return bool(fo) and point_in_poly(pt[0], pt[1], fo["outline"]) and edge_dist(pt[0], pt[1], fo["outline"]) >= 10
        if k == "moat":
            mo: Any = M.get("moat")
            return bool(mo) and any(seg_dist(pt[0], pt[1], mo[i], mo[i + 1]) < 34 for i in range(len(mo) - 1))
        if k == "river":  # a fan tapped straight off a river (Nagahara's Hayakawa far bank, 2026-07-23)
            rv2: Any = M.get("river")
            return bool(rv2) and any(seg_dist(pt[0], pt[1], rv2["pts"][i], rv2["pts"][i + 1]) < rv2.get("w", 40) / 2 + 14 for i in range(len(rv2["pts"]) - 1))
        if k == "drain":  # a brook empties FROM the field drain (akusui outfall)
            return any(seg_dist(pt[0], pt[1], dp[i], dp[i + 1]) < 30 for fd in M.get("field_ditches", []) if fd.get("role") == "drain" for dp in [fd["poly"]] for i in range(len(dp) - 1))
        if k == "ditch":
            # a weir/intake HANDS OFF to the irrigation works (a head-race, a canal): the mirror of
            # the stream-diverted-into-a-channel clause in stream_runs_off_edge (GM audit 2026-07)
            return any(seg_dist(pt[0], pt[1], dp[i], dp[i + 1]) < 22 for d2 in (M.get("field_ditches", []) + M.get("channels", [])) for dp in [d2["poly"]] for i in range(len(dp) - 1))
        return False

    return _kept(locals(), ('anchored',))


def _seg_0300__channel_source_anchored(
    *,
    M: Any = _UNBOUND,
    anchored: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    dev: Any = _UNBOUND,
    end: Any = _UNBOUND,
    frm: Any = _UNBOUND,
    idx: Any = _UNBOUND,
    p: Any = _UNBOUND,
    poly: Any = _UNBOUND,
    start: Any = _UNBOUND,
    straight: Any = _UNBOUND,
    tag: Any = _UNBOUND,
    to: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 300 (channel_directness, channel_field_anchored, channel_source_anchored, channel_winds_gently) - body verbatim from the legacy gate() (feature 022)."""
    for idx, c in enumerate(M["channels"]):
        poly, frm, to = c["poly"], c["frm"], c["to"]
        start, end = poly[0], poly[-1]
        tag = to.get("name", idx)
        check(f"channel_source_anchored[{tag}]", anchored(start, frm), f"start {start} not anchored to {frm}")
        check(f"channel_field_anchored[{tag}]", anchored(end, to), f"end {end} not anchored to {to}")
        dev = max((seg_dist(p[0], p[1], start, end) for p in poly[1:-1]), default=0)
        check(f"channel_winds_gently[{tag}]", 5 <= dev <= 50, f"deviation {dev:.0f}px (want 5-50)")
        straight = math.hypot(end[0] - start[0], end[1] - start[1])
        check(f"channel_directness[{tag}]", straight == 0 or polyline_len(poly) <= 1.6 * straight, f"len {polyline_len(poly):.0f} vs straight {straight:.0f}")
    return _kept(locals(), ('c', 'dev', 'end', 'frm', 'idx', 'p', 'poly', 'start', 'straight', 'tag', 'to'))


# A SUPPLY CONDUIT FEEDING A PADDY MUST BE VISIBLY SOURCED (GM 2026-07-24, Tango fs3): an
# irrigation canal can never just START in the middle of nowhere - it must tap on-map water
# or come in from the view edge (presumed to continue off-map). channel_source_anchored
# already checks the RECORDED topology, but a `drawn: False` conduit (an implied underground
# channel whose visual is carried by the comb's own drawn head-race) can lie visually: Tango's
# fs3 recorded its tap on a stream vertex, drew nothing between stream and comb, and the main
# canal's head hung in open ground 38px from the bank. So for every UNDRAWN supply conduit,
# the point where visible water actually starts - the comb origin, i.e. the fed field's
# main-ditch head nearest the recorded source - must itself (a) sit at/past the view edge,
# (b) sit on source water (stream/moat/pond/river/cargo-canal bed, or another comb's ditch -
# tail-water cascade, the standard way a city's drainage waters the fields below it), or
# (c) be joined to such a point by a DRAWN tap stroke. Tap strokes are read from
# M['drawn_channels'] (post-clip geometry - the check reads what was actually drawn, per the
# same-manifest rule in the dev-loop doc); a drawn stroke whose far end lies in or along the
# fed field's own outline is the comb's own canal heading downstream, not a tap.


def _seg_0301___on_source_water(
    *, M: Any = _UNBOUND, cp: Any = _UNBOUND, dp: Any = _UNBOUND, i: Any = _UNBOUND, own: Any = _UNBOUND, pond: Any = _UNBOUND, pt: Any = _UNBOUND, sp: Any = _UNBOUND, st: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 301 (_on_source_water) - body verbatim from the legacy gate() (feature 022)."""

    def _on_source_water(pt: Pt, own: Any) -> bool:
        if any(seg_dist(pt[0], pt[1], sp[i], sp[i + 1]) <= st.get("w", 9) / 2 + 4 for st in M.get("streams", []) for sp in [st["poly"]] for i in range(len(sp) - 1)):
            return True
        mo3: Any = M.get("moat")
        if mo3 and any(seg_dist(pt[0], pt[1], mo3[i], mo3[(i + 1) % len(mo3)]) <= M.get("moat_width", 26) / 2 + 4 for i in range(len(mo3))):
            return True
        if pond and in_ellipse(pt[0], pt[1], pond, 1.05):
            return True
        rv3: Any = M.get("river")
        if rv3 and any(seg_dist(pt[0], pt[1], rv3["pts"][i], rv3["pts"][i + 1]) <= rv3.get("w", 40) / 2 + 4 for i in range(len(rv3["pts"]) - 1)):
            return True
        if any(seg_dist(pt[0], pt[1], cp[i], cp[i + 1]) <= cn.get("w", 12) / 2 + 4 for cn in M.get("canals", []) for cp in [cn["poly"]] for i in range(len(cp) - 1)):
            return True
        return any(
            seg_dist(pt[0], pt[1], dp[i], dp[i + 1]) <= fd2.get("w", 4) / 2 + 4 for fd2 in M.get("field_ditches", []) if fd2.get("field") != own for dp in [fd2["poly"]] for i in range(len(dp) - 1)
        )

    return _kept(locals(), ('_on_source_water',))


def _seg_0302___at_view_edge(*, EX0: Any = _UNBOUND, EX1: Any = _UNBOUND, EY0: Any = _UNBOUND, EY1: Any = _UNBOUND, pt: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 302 (_at_view_edge) - body verbatim from the legacy gate() (feature 022)."""

    def _at_view_edge(pt: Pt) -> bool:
        return bool(min(pt[0] - EX0, EX1 - pt[0], pt[1] - EY0, EY1 - pt[1]) <= 32)

    return _kept(locals(), ('_at_view_edge',))


def _seg_0303__supply_mains() -> dict[str, Any]:
    """Gate segment 303 (supply_mains) - body verbatim from the legacy gate() (feature 022)."""
    supply_mains: dict[Any, list[Poly]] = {}
    return _kept(locals(), ('supply_mains',))


def _seg_0304__fd3(*, M: Any = _UNBOUND, fd3: Any = _UNBOUND, supply_mains: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 304 (fd3, supply_mains) - body verbatim from the legacy gate() (feature 022)."""
    for fd3 in M.get("field_ditches", []):
        if fd3.get("role") == "main":
            supply_mains.setdefault(fd3.get("field"), []).append(fd3["poly"])
    return _kept(locals(), ('fd3', 'supply_mains'))


def _seg_0305__field_supply_visibly_sourced(
    *,
    M: Any = _UNBOUND,
    _at_view_edge: Any = _UNBOUND,
    _on_source_water: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    csrc: Any = _UNBOUND,
    cto: Any = _UNBOUND,
    dcr: Any = _UNBOUND,
    dpts: Any = _UNBOUND,
    e: Any = _UNBOUND,
    far: Any = _UNBOUND,
    field_by: Any = _UNBOUND,
    fld: Any = _UNBOUND,
    fmains: Any = _UNBOUND,
    fo3: Any = _UNBOUND,
    h: Any = _UNBOUND,
    i: Any = _UNBOUND,
    m: Any = _UNBOUND,
    ok: Any = _UNBOUND,
    origin: Any = _UNBOUND,
    supply_mains: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 305 (field_supply_visibly_sourced) - body verbatim from the legacy gate() (feature 022)."""
    for c in M["channels"]:
        cto = c.get("to") or {}
        if cto.get("kind") != "field" or c.get("drawn", True) is not False:
            continue  # a DRAWN supply channel carries its own visual continuity (ends anchor-checked above)
        fld = cto.get("name")
        fmains = supply_mains.get(fld)
        if not fmains:
            continue
        csrc = c["poly"][0]
        origin = min((m[0] for m in fmains), key=lambda h: math.hypot(h[0] - csrc[0], h[1] - csrc[1]))
        ok = _at_view_edge(origin) or _on_source_water(origin, fld)
        fo3: Any = field_by.get(fld)  # type: ignore[no-redef]
        if not ok and fo3:
            for dcr in M.get("drawn_channels", []):
                dpts = dcr["pts"]
                if len(dpts) < 2 or min(seg_dist(origin[0], origin[1], dpts[i], dpts[i + 1]) for i in range(len(dpts) - 1)) > 4:
                    continue
                far = max((dpts[0], dpts[-1]), key=lambda e: math.hypot(e[0] - origin[0], e[1] - origin[1]))
                if point_in_poly(far[0], far[1], fo3["outline"]) or edge_dist(far[0], far[1], fo3["outline"]) <= 8:
                    continue  # the comb's own canal heading INTO the field, not a tap
                if _on_source_water(far, fld) or _at_view_edge(far):
                    ok = True
                    break
        check(
            f"field_supply_visibly_sourced[{fld}]",
            ok,
            f"comb origin {origin} hangs in open ground: no on-map water source, no view-edge entry, no drawn tap stroke (an irrigation canal cannot start in the middle of nowhere)",
        )
    return _kept(locals(), ('c', 'csrc', 'cto', 'dcr', 'dpts', 'far', 'fld', 'fmains', 'fo3', 'i', 'm', 'ok', 'origin'))


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


# WATERCOURSES JOIN, THEY DO NOT CROSS (GM 2026-07-24, Enokida: "many of the irrigated channels
# intersect rather than joining"). Where two irrigation strokes meet, one of them must END there -
# a T (a lateral delivering into the ring trunk) or a Y (a delivery taking off downstream) - never a
# 4-way X with a stub poking out the far side. Real wet-rice hydrology has no crossings to draw: a
# ditch either feeds another ditch or is fed by it, and where two courses genuinely had to pass at
# different levels the builders put in an aqueduct or a siphon, which is a distinct structure this
# vocabulary does not have. So any X on these maps is a drawing error.
#
# HOW A JOIN IS TOLD FROM A CROSSING: at every crossing point, take each stroke's endpoint nearest
# that point and ask whether that TIP sits inside the OTHER stroke's drawn band (perpendicular
# distance to its centerline <= its stroke half-width). If either tip is buried in the other's
# band, the meeting is a junction and the overrun is invisible under the ink. If NEITHER is, the
# stub shows and it reads as a crossing.
#
# The measure is PERPENDICULAR TO THE OTHER STROKE rather than run-length along the stub's own
# line, and that is the whole trick: a delivery ditch taking off at a shallow angle runs several px
# past the crossing yet stays under the trunk's stroke the entire way (correct, and it looks it),
# while the same overrun on a near-perpendicular T pokes straight out the far side. A run-length
# rule cannot separate those; the perpendicular one is exactly "does the stub show". Swept over
# every pool map it flagged Enokida's polder laterals (tips 2.0-2.8px outside the ring's band) and
# nothing else - Honda's, Ikegami's, Nagahara's and Hoshizora's comb offtakes overrun by a similar
# 4-8px along their own line but stay inside the canal band, and all four read as clean Y-junctions.
# The 1px slack absorbs the 0.1px coordinate rounding and the round linecap.
#
# Read from drawn_channels (the post-clip record of what was actually STROKED, widths included),
# not from field_ditches/channels: those carry pre-clip geometry, so a mouth snapped onto a pond or
# a stream would be judged at a position it is never drawn at.


# THE HEAD-RACE FORKS AND SUPPLY COMMANDS BOTH FLANKS (GM caught Inashiro's bare west margin
# 2026-08-16; researched - research/water.md "The head-race forks - supply commands both flanks").
# A gravity canal waters only ground BELOW it (Chinese canal doctrine: every tier sits on the high
# ground of ITS OWN command area; Minuma-dai 1728 divides its head into TWO canals along the two
# elevated margins with the drain down the center), and build_comb carves paddy on BOTH sides of
# the bunsuiguchi division - so a fan whose drawn supply runs down one margin only has a whole
# flank of modeled-as-watered plots with no visible water. Measured on the motivating map: ~255 ft
# of planted paddy west of Inashiro's fork against 0 ft of drawn supply. The check reads the fork
# build_comb records on the field (legacy manifests carry none, so the frozen pool skips it -
# conversion, not retrofit, is their fix per the migration doctrine) and compares each flank's
# planted cross-slope extent against the drawn main/branch reach on that flank. Thresholds are
# real feet (scaled by ftpx): a flank with more than ~150 ft of paddy needs drawn supply reaching
# at least 80 ft, or 30% of that flank's extent, whichever is greater - calibrated so a genuinely
# lopsided fan (a sliver of ground past the fork) demands nothing, while a flank the carve
# actually planted must show the arm that waters it.


def _seg_0324_500__comb_supply_commands_both_flanks(
    *,
    M: Any = _UNBOUND,
    _csf_bad: Any = _UNBOUND,
    _csf_c: Any = _UNBOUND,
    _csf_d: Any = _UNBOUND,
    _csf_deg: Any = _UNBOUND,
    _csf_ext: Any = _UNBOUND,
    _csf_f: Any = _UNBOUND,
    _csf_fork: Any = _UNBOUND,
    _csf_ftpx: Any = _UNBOUND,
    _csf_i: Any = _UNBOUND,
    _csf_reach: Any = _UNBOUND,
    _csf_ring: Any = _UNBOUND,
    _csf_s: Any = _UNBOUND,
    _csf_seen: Any = _UNBOUND,
    _csf_v: Any = _UNBOUND,
    check: Any = _UNBOUND,
    meta: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0324.500 (comb_supply_commands_both_flanks) - new check 2026-08-16, see the comment bank above."""
    _csf_bad = []
    _csf_ftpx = float(meta.get("ftpx") or 1.0)
    _csf_seen = False
    for _csf_f in M.get("fields") or []:
        _csf_fork = _csf_f.get("fork")
        _csf_deg = _csf_f.get("down_deg", meta.get("down_deg"))
        if _csf_fork is None or _csf_deg is None or _csf_f.get("kind") != "paddy":
            continue
        _csf_seen = True
        # cross-slope unit vector: fall d = (cos, sin), c = d rotated 90 deg - flank membership is
        # the SIGN of a point's cross-slope offset from the fork (an AGGREGATE bearing question is
        # fine on vertices; every quantity here is an extent, not a gap verdict)
        _csf_c = (-math.sin(math.radians(float(_csf_deg))), math.cos(math.radians(float(_csf_deg))))
        _csf_ext = [0.0, 0.0]
        for _csf_ring in _csf_f.get("plot_rings") or []:
            for _csf_v in _csf_ring:
                _csf_s = (_csf_v[0] - _csf_fork[0]) * _csf_c[0] + (_csf_v[1] - _csf_fork[1]) * _csf_c[1]
                _csf_i = 0 if _csf_s >= 0 else 1
                _csf_ext[_csf_i] = max(_csf_ext[_csf_i], abs(_csf_s))
        _csf_reach = [0.0, 0.0]
        for _csf_d in M.get("field_ditches") or []:
            if _csf_d.get("field") != _csf_f.get("name") or _csf_d.get("role") not in ("main", "branch"):
                continue
            for _csf_v in _csf_d["poly"]:
                _csf_s = (_csf_v[0] - _csf_fork[0]) * _csf_c[0] + (_csf_v[1] - _csf_fork[1]) * _csf_c[1]
                _csf_i = 0 if _csf_s >= 0 else 1
                _csf_reach[_csf_i] = max(_csf_reach[_csf_i], abs(_csf_s))
        for _csf_i in (0, 1):
            if _csf_ext[_csf_i] > 150.0 / _csf_ftpx and _csf_reach[_csf_i] < max(80.0 / _csf_ftpx, 0.3 * _csf_ext[_csf_i]):
                _csf_bad.append(
                    f"{_csf_f.get('name')}: the {'+cross' if _csf_i == 0 else '-cross'} flank has ~{round(_csf_ext[_csf_i] * _csf_ftpx)} ft "
                    f"of paddy but its drawn supply reaches only ~{round(_csf_reach[_csf_i] * _csf_ftpx)} ft from the fork"
                )
    if _csf_seen:
        check(
            "comb_supply_commands_both_flanks",
            not _csf_bad,
            "a gravity canal commands only the ground BELOW it, so a comb fan planted on both sides of its "
            "bunsuiguchi fork must DRAW supply down both margins - canal A along one, canal B partway down the "
            "other, tapering (the Minuma-dai split; research/water.md 'The head-race forks - supply commands "
            f"both flanks'). Give the fan a canal-B offtake (hamletgen OFFTAKE_LADDER offtakes_b) so the second "
            f"arm is inked: {_csf_bad}",
        )
    return _kept(
        locals(),
        (
            '_csf_bad',
            '_csf_c',
            '_csf_d',
            '_csf_deg',
            '_csf_ext',
            '_csf_f',
            '_csf_fork',
            '_csf_ftpx',
            '_csf_i',
            '_csf_reach',
            '_csf_ring',
            '_csf_s',
            '_csf_seen',
            '_csf_v',
        ),
    )


def _seg_0325___wj_strokes(*, M: Any = _UNBOUND, c: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 325 (_wj_strokes, c) - body verbatim from the legacy gate() (feature 022)."""
    _wj_strokes = [c for c in M.get("drawn_channels", []) or [] if len(c.get("pts") or []) >= 2]
    return _kept(locals(), ('_wj_strokes', 'c'))


def _seg_0326__water_channels_join_not_cross(
    *,
    _wj_band: Any = _UNBOUND,
    _wj_bbox: Any = _UNBOUND,
    _wj_boxes: Any = _UNBOUND,
    _wj_cross: Any = _UNBOUND,
    _wj_strokes: Any = _UNBOUND,
    _wj_stub: Any = _UNBOUND,
    _wj_tip_outside: Any = _UNBOUND,
    _wj_worst: Any = _UNBOUND,
    at: Any = _UNBOUND,
    ax0: Any = _UNBOUND,
    ax1: Any = _UNBOUND,
    ay0: Any = _UNBOUND,
    ay1: Any = _UNBOUND,
    bx0: Any = _UNBOUND,
    bx1: Any = _UNBOUND,
    by0: Any = _UNBOUND,
    by1: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    e: Any = _UNBOUND,
    ha: Any = _UNBOUND,
    hb: Any = _UNBOUND,
    i: Any = _UNBOUND,
    ia: Any = _UNBOUND,
    ib: Any = _UNBOUND,
    j: Any = _UNBOUND,
    other: Any = _UNBOUND,
    p: Any = _UNBOUND,
    pa: Any = _UNBOUND,
    pb: Any = _UNBOUND,
    pts: Any = _UNBOUND,
    tip: Any = _UNBOUND,
    xs: Any = _UNBOUND,
    ys: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 326 (water_channels_join_not_cross) - body verbatim from the legacy gate() (feature 022)."""
    if _wj_strokes:

        def _wj_band(c: Any) -> float:
            return max(float(c.get("w0", 3.0)), float(c.get("w1", 3.0))) / 2

        def _wj_bbox(pts: Poly) -> tuple[float, float, float, float]:
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            return min(xs), min(ys), max(xs), max(ys)

        def _wj_tip_outside(pts: Poly, other: Poly, other_half: float, at: Pt) -> float:
            """How far the end of `pts` NEAREST the crossing sits OUTSIDE `other`'s drawn band."""
            tip = min((pts[0], pts[-1]), key=lambda e: math.hypot(e[0] - at[0], e[1] - at[1]))
            return min(seg_dist(tip[0], tip[1], other[i], other[i + 1]) for i in range(len(other) - 1)) - other_half

        _wj_boxes = [_wj_bbox(c["pts"]) for c in _wj_strokes]
        _wj_cross: list[tuple[int, int]] = []  # type: ignore[no-redef]
        for ia in range(len(_wj_strokes)):
            for ib in range(ia + 1, len(_wj_strokes)):
                ax0, ay0, ax1, ay1 = _wj_boxes[ia]
                bx0, by0, bx1, by1 = _wj_boxes[ib]
                if ax1 < bx0 or bx1 < ax0 or ay1 < by0 or by1 < ay0:
                    continue
                pa, pb = _wj_strokes[ia]["pts"], _wj_strokes[ib]["pts"]
                ha, hb = _wj_band(_wj_strokes[ia]), _wj_band(_wj_strokes[ib])
                _wj_worst: tuple[float, Pt] | None = None  # type: ignore[no-redef]
                for i in range(len(pa) - 1):
                    for j in range(len(pb) - 1):
                        if not segments_cross(pa[i], pa[i + 1], pb[j], pb[j + 1]):
                            continue
                        at = seg_intersect(pa[i], pa[i + 1], pb[j], pb[j + 1])
                        if at is None:
                            continue  # pragma: no cover - segments_cross already excludes the parallel case
                        _wj_stub = min(_wj_tip_outside(pa, pb, hb, at), _wj_tip_outside(pb, pa, ha, at))
                        if _wj_worst is None or _wj_stub > _wj_worst[0]:
                            _wj_worst = (_wj_stub, at)
                if _wj_worst is not None and _wj_worst[0] > 1.0:
                    _wj_cross.append((round(_wj_worst[1][0]), round(_wj_worst[1][1])))
        check(
            "water_channels_join_not_cross",
            not _wj_cross,
            f"irrigation channel(s) CROSSING rather than joining at {sorted(set(_wj_cross))[:5]} - where two "
            f"watercourses meet, one must END at the junction (a T feeding the trunk, or a Y taking off from it); "
            f"neither tip lands inside the other's drawn band here, so a stub pokes out the far side and the pair "
            f"reads as a 4-way intersection. Snap the joining stroke's tip onto the other's drawn centerline",
        )
    return _kept(
        locals(),
        (
            '_wj_band',
            '_wj_bbox',
            '_wj_boxes',
            '_wj_cross',
            '_wj_stub',
            '_wj_tip_outside',
            '_wj_worst',
            'at',
            'ax0',
            'ax1',
            'ay0',
            'ay1',
            'bx0',
            'bx1',
            'by0',
            'by1',
            'c',
            'ha',
            'hb',
            'i',
            'ia',
            'ib',
            'j',
            'pa',
            'pb',
        ),
    )


# no farm field overlaps a road OR a town street (the roadbed/street band must not clip
# a field) - the road leading into town must not run through a farm field
# EVERY DRAWN WAY, not just the road and the streets (GM 2026-08-12: "Inashiro has village paths
# overlapping with rice paddies... I also think there's supposed to be a rule that paths don't
# pass through marshland"). Both rules below were written for roads and duly never saw a village
# LANE or an alley - the same shape as `ring_road_kept_clear`'s hand-written key list, and it
# looks exactly like a passing check. A lane is a narrower way, not a different KIND of thing:
# its tread is trodden earth that a farmer walks in the dry, so it belongs on the baulk between
# plots and on dry ground, never in the standing water of a paddy or across a reed marsh.


def _seg_0327__roadways() -> dict[str, Any]:
    """Gate segment 327 (roadways) - body verbatim from the legacy gate() (feature 022)."""
    roadways = []  # type: ignore[var-annotated]
    return _kept(locals(), ('roadways',))


def _seg_0328__roadways_1(*, M: Any = _UNBOUND, road: Any = _UNBOUND, roadways: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 328 (roadways) - body verbatim from the legacy gate() (feature 022)."""
    if road:
        roadways.append((road, M.get("road_width", 26) / 2 + 2))
    return _kept(locals(), ('roadways',))


def _seg_0329__roadways_2(*, M: Any = _UNBOUND, roadways: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 329 (roadways, st) - body verbatim from the legacy gate() (feature 022)."""
    roadways += [(st["pts"], st["w"] / 2 + 2) for st in M.get("town_streets", [])]
    return _kept(locals(), ('roadways', 'st'))


def _seg_0330__ln(*, M: Any = _UNBOUND, ln: Any = _UNBOUND, roadways: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 330 (ln, roadways) - body verbatim from the legacy gate() (feature 022)."""
    roadways += [(ln["pts"], ln.get("w", 5) / 2 + 2) for ln in M.get("lanes", [])]
    return _kept(locals(), ('ln', 'roadways'))


def _seg_0331__al(*, M: Any = _UNBOUND, al: Any = _UNBOUND, roadways: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 331 (al, roadways) - body verbatim from the legacy gate() (feature 022)."""
    roadways += [(al["pts"], al.get("w", 10) / 2 + 2) for al in M.get("alleys", [])]
    return _kept(locals(), ('al', 'roadways'))


def _seg_0332__fields_clear_of_road(
    *,
    M: Any = _UNBOUND,
    _b: Any = _UNBOUND,
    _drawn: Any = _UNBOUND,
    bad_fr: Any = _UNBOUND,
    check: Any = _UNBOUND,
    e: Any = _UNBOUND,
    f: Any = _UNBOUND,
    fcr_a: Any = _UNBOUND,
    fcr_b: Any = _UNBOUND,
    fcr_hit: Any = _UNBOUND,
    fcr_k: Any = _UNBOUND,
    fcr_k2: Any = _UNBOUND,
    fcr_n: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    hw: Any = _UNBOUND,
    k: Any = _UNBOUND,
    m: Any = _UNBOUND,
    mpoly: Any = _UNBOUND,
    nmp: Any = _UNBOUND,
    ol: Any = _UNBOUND,
    poly: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    roadways: Any = _UNBOUND,
    rx: Any = _UNBOUND,
    ry: Any = _UNBOUND,
    t: Any = _UNBOUND,
    vx0: Any = _UNBOUND,
    vx1: Any = _UNBOUND,
    vy0: Any = _UNBOUND,
    vy1: Any = _UNBOUND,
    wet_road: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 332 (fields_clear_of_road, roads_clear_of_marsh) - body verbatim from the legacy gate() (feature 022)."""
    if roadways:
        # MEASURED AGAINST THE DRAWN CROP, not the whole envelope (settlement-review, 2026-08-12).
        # A field's `outline` is not all rice: a comb fan's envelope carries a tail past the last
        # plot that exists only to block house placement, and Ueda's gen says so in as many words.
        # Testing the raw outline therefore reported a lane "in the paddy" where the render shows
        # bare parchment with ten farmhouses standing on it - and the cure for that phantom broke a
        # village spine in two, stranded 25 homesteads, and collapsed a shrine's seven-arch sando to
        # one when the re-pack moved it. `vis_bbox` is the bbox of the drawn plot vertices and every
        # field records it, so both sides can read the same thing: a way is only in the rice where
        # it is inside the outline AND inside the drawn extent. The GM sees ink, not envelopes.
        bad_fr = []
        for f in fields:
            ol = f["outline"]
            n = len(ol)
            vx0, vy0, vx1, vy1 = f.get("vis_bbox") or f.get("bbox") or (-1e9, -1e9, 1e9, 1e9)

            def _drawn(px: float, py: float, _ol: Any = ol, _b: Any = (vx0, vy0, vx1, vy1)) -> bool:
                return _b[0] <= px <= _b[2] and _b[1] <= py <= _b[3] and point_in_poly(px, py, _ol)

            for poly, hw in roadways:
                # local names are suffixed: `gate()` is one enormous scope and `a`/`b`/`k`/`i` are
                # all bound to other things in it (this skill's CLAUDE.md warns about exactly this).
                fcr_hit = False
                for fcr_k in range(len(poly) - 1):
                    fcr_a, fcr_b = poly[fcr_k], poly[fcr_k + 1]
                    fcr_n = max(2, int(math.hypot(fcr_b[0] - fcr_a[0], fcr_b[1] - fcr_a[1]) / 6.0))
                    if any(_drawn(fcr_a[0] + (fcr_b[0] - fcr_a[0]) * t / fcr_n, fcr_a[1] + (fcr_b[1] - fcr_a[1]) * t / fcr_n) for t in range(fcr_n + 1)):
                        fcr_hit = True
                        break
                if not fcr_hit:  # ...and the way's own tread may not reach a DRAWN plot edge either
                    fcr_hit = any(_drawn(px, py) and seg_dist(px, py, poly[fcr_k2], poly[fcr_k2 + 1]) < hw for px, py in ol for fcr_k2 in range(len(poly) - 1))
                if fcr_hit:
                    bad_fr.append(f["name"])
                    break
        check(
            "fields_clear_of_road",
            not bad_fr,
            f"field(s) run under a way: {sorted(set(bad_fr))} - a road, street, lane or alley is trodden ground and a "
            f"paddy is standing water; a farm track runs on the BAULK between plots or round the field's margin, never through it",
        )

        # ROADS STAY CLEAR OF MARSHLAND (GM, Hoshizora 2026-07: the tameike's reed fringe ran under
        # the Imperial Road). A roadbed is engineered dry ground; none of these maps draw a causeway,
        # so a road/street entering a marsh patch is a placement error, not a feature.
        wet_road = []
        for m in M.get("marshes", []):
            if m.get("role") == "defense":
                continue  # an approach road THROUGH the defensive wet belt is a CAUSEWAY (the renderer keeps the tread bare via the corridor skip) - few, constricted approaches are the belt's military purpose, not a placement error
            mpoly = m.get("poly") or []
            nmp = len(mpoly)
            if nmp < 3:
                continue
            for poly, hw in roadways:
                if (
                    any(seg_dist(px, py, poly[k], poly[k + 1]) < hw for px, py in mpoly for k in range(len(poly) - 1))
                    or any(point_in_poly(rx, ry, mpoly) for rx, ry in poly)
                    or any(segments_cross(poly[k], poly[k + 1], mpoly[e], mpoly[(e + 1) % nmp]) for k in range(len(poly) - 1) for e in range(nmp))
                ):
                    wet_road.append((round(m["x"]), round(m["y"])))
                    break
        check(
            "roads_clear_of_marsh",
            not wet_road,
            f"a way runs through marshland at {sorted(set(wet_road))[:4]} - a roadbed is engineered dry ground and a "
            f"village lane is trodden earth; neither survives a reed marsh without a causeway, and none of these maps "
            f"draws one. Route the way round the wet ground, or put the marsh where the way is not",
        )
    return _kept(
        locals(),
        (
            '_drawn',
            'bad_fr',
            'e',
            'f',
            'fcr_a',
            'fcr_b',
            'fcr_hit',
            'fcr_k',
            'fcr_k2',
            'fcr_n',
            'hw',
            'k',
            'm',
            'mpoly',
            'n',
            'nmp',
            'ol',
            'poly',
            'px',
            'py',
            'rx',
            'ry',
            't',
            'vx0',
            'vx1',
            'vy0',
            'vy1',
            'wet_road',
        ),
    )


# THE POND STAYS CLEAR OF THE RICE PADDIES (GM, Hoshizora 2026-07). A pond is a distinct water
# body BESIDE the crop - a reservoir above the field or a drainage tameike below it - joined by a
# channel, never overlapping the planted paddy itself.


def _seg_0333__pond_clear_of_paddies(
    *,
    a: Any = _UNBOUND,
    check: Any = _UNBOUND,
    f: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    i: Any = _UNBOUND,
    ol: Any = _UNBOUND,
    pcx_: Any = _UNBOUND,
    pcy_: Any = _UNBOUND,
    pond: Any = _UNBOUND,
    prx_: Any = _UNBOUND,
    pry_: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    rim_pts: Any = _UNBOUND,
    vx: Any = _UNBOUND,
    vy: Any = _UNBOUND,
    wet_paddy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 333 (pond_clear_of_paddies) - body verbatim from the legacy gate() (feature 022)."""
    if pond and fields:
        pcx_, pcy_, prx_, pry_ = pond
        rim_pts = [(pcx_ + prx_ * math.cos(a), pcy_ + pry_ * math.sin(a)) for a in [i * math.pi / 12 for i in range(24)]]
        wet_paddy = []
        for f in fields:
            if f.get("kind") != "paddy":
                continue
            ol = f["outline"]
            if any(in_ellipse(vx, vy, pond) for vx, vy in ol) or any(point_in_poly(px, py, ol) for px, py in rim_pts) or point_in_poly(pcx_, pcy_, ol):
                wet_paddy.append(f["name"])
        check(
            "pond_clear_of_paddies",
            not wet_paddy,
            f"the pond overlaps rice paddy field(s) {sorted(set(wet_paddy))} - a pond sits BESIDE the crop (a reservoir above it or a tameike below it), joined by a channel, never over the planted paddy",
        )
    return _kept(locals(), ('a', 'f', 'i', 'ol', 'pcx_', 'pcy_', 'prx_', 'pry_', 'px', 'py', 'rim_pts', 'vx', 'vy', 'wet_paddy'))
