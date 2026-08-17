"""Gate segments (field cover and cremation; keys 0285_092-0286_024) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from l7r.diagram.settlement import sat_overlap

from .common_01_geometry import _struct_rect, point_in_poly, poly_dist, rect_corners, seg_dist
from .common_02_overlap_policy import in_ellipse, poly_gap, water_setback
from .common_03_capacity import _UNBOUND, _kept


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
