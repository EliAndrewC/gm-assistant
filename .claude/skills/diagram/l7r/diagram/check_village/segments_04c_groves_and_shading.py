"""Gate segments (groves and shading; keys 0285_066-0598) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from l7r.diagram.settlement import sat_overlap

from .common_01_geometry import (
    _box_hits_poly,
    _struct_rect,
    point_in_poly,
    pt_to_rect,
    rect_corners,
    seg_dist,
    segments_cross,
)
from .common_02_overlap_policy import edge_dist, in_ellipse
from .common_03_capacity import _UNBOUND, _kept


def _seg_0285_066__gr_fouled(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.066 (gr_fouled) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        gr_fouled = []  # type: ignore[var-annotated]
    return _kept(locals(), ('gr_fouled',))


def _seg_0285_067__gc(
    *,
    gc: Any = _UNBOUND,
    gci: Any = _UNBOUND,
    gr_fouled: Any = _UNBOUND,
    groves: Any = _UNBOUND,
    gv: Any = _UNBOUND,
    others: Any = _UNBOUND,
    par: Any = _UNBOUND,
    s: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.067 (gc, gci, gr_fouled, gv) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for gv in groves:
            gci = dict(gv)
            gci["w"] = gv["w"] * 0.7
            gci["h"] = gv["h"] * 0.7  # inset: tolerate abutting
            gc = rect_corners(_struct_rect(gci))
            par = (round(gv["of"][0]), round(gv["of"][1]))
            for s in others:
                if (round(s["x"]), round(s["y"])) == par:
                    continue
                if abs(s["x"] - gv["x"]) + abs(s["y"] - gv["y"]) > 140:
                    continue
                if sat_overlap(gc, rect_corners(_struct_rect(s))):
                    gr_fouled.append((round(gv["x"]), round(gv["y"])))
                    break
    return _kept(locals(), ('gc', 'gci', 'gr_fouled', 'gv', 'par', 's'))


def _seg_0285_068__groves_clear_of_structures(*, check: Any = _UNBOUND, gr_fouled: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.068 (groves_clear_of_structures) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check("groves_clear_of_structures", not gr_fouled, f"homestead grove(s) overlap a building other than their own farmhouse: {gr_fouled[:3]} - a grove abuts only its own house")
    return _kept(locals(), ())


# SUN: a threshing yard dries rice in the SOUTHERN sun, so no grove may sit in the strip directly
# SOUTH of a yard (a neighbor's grove there would shade it). A grove is N/W of its OWN house, far
# from its own yard's southern corridor, so this only catches a grove shading a NEIGHBOR's yard.


def _seg_0285_069__shaded(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.069 (shaded) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        shaded = []  # type: ignore[var-annotated]
    return _kept(locals(), ('shaded',))


def _seg_0285_070__cyx(
    *, cyx: Any = _UNBOUND, cyy: Any = _UNBOUND, groves: Any = _UNBOUND, gv: Any = _UNBOUND, scale: Any = _UNBOUND, shaded: Any = _UNBOUND, yards: Any = _UNBOUND, yd: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0285.070 (cyx, cyy, gv, shaded) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for yd in yards:
            cyx, cyy = yd["x"], yd["y"] + yd["h"] / 2 + 11  # the ~22px sun-corridor just south of the yard
            if any(abs(gv["x"] - cyx) < (gv["w"] + yd["w"]) / 2 and abs(gv["y"] - cyy) < (gv["h"] + 22) / 2 for gv in groves):
                shaded.append((round(yd["x"]), round(yd["y"])))
    return _kept(locals(), ('cyx', 'cyy', 'gv', 'shaded', 'yd'))


# ...AND NOT BY A NEIGHBOR'S FARMHOUSE, which is the taller obstacle and was never
# tested (GM 2026-08-13: "would the shadow from the farmhouse directly to the south
# block too much light?"). Researched in research/homesteads.md, "The threshing yard's
# sun": thatch is pitched 45 deg or steeper, so the 46x28 ft minka's ridge stands ~20 ft
# up, and at 38N in the 10th month that throws 21 ft of shadow at noon and 39 ft by 9am.
# 39 ft is the rule, because the drying day that matters is 9-to-3.
#
# GATED ON `meta.generated_by`, and that gate IS the GM's decision (2026-08-13). Every
# hand-authored nucleated map in the pool breaks this - Ueda has 45 of 85 yards shaded at
# noon, Hoshigaoka 31 of 70, Ubame 21 of 36, with neighbors' walls 2-8 ft off the yard
# edge - and re-packing them all was judged the wrong trade. Instead the rule binds the
# SCRIPTED path, and each legacy map inherits it at the moment it is converted to a
# generator. The exemption therefore cannot rot: it is not a list anyone has to prune,
# it is the absence of a tag that conversion adds.


def _seg_0285_071__yards_unshaded_by_neighbors(
    *,
    check: Any = _UNBOUND,
    gap: Any = _UNBOUND,
    hh_: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    nshade: Any = _UNBOUND,
    par: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    sun_ft: Any = _UNBOUND,
    sun_ftpx: Any = _UNBOUND,
    yards: Any = _UNBOUND,
    yd: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.071 (yards_unshaded_by_neighbors) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city') and meta.get("generated_by"):
        sun_ft = 39.0
        sun_ftpx = float(meta.get("ftpx") or 1)  # derived locally: `ftpx` is bound conditionally in this scope
        nshade = []
        for yd in yards:
            par = yd.get("of")
            for hh_ in houses:
                if par and abs(hh_["x"] - par[0]) < 1 and abs(hh_["y"] - par[1]) < 1:
                    continue  # its own house is NORTH of it by construction
                if abs(hh_["x"] - yd["x"]) >= (hh_["w"] + yd["w"]) / 2:
                    continue  # not in the yard's sun corridor
                gap = ((hh_["y"] - hh_["h"] / 2) - (yd["y"] + yd["h"] / 2)) * sun_ftpx
                if 0 < gap < sun_ft:
                    nshade.append((round(yd["x"]), round(yd["y"])))
                    break
        check(
            "yards_unshaded_by_neighbors",
            not nshade,
            f"threshing yard(s) {nshade[:3]} stand within {sun_ft:.0f} ft of a NEIGHBOR's farmhouse to their "
            f"SOUTH - a minka's ~20 ft ridge throws 21 ft of shadow at noon in the threshing month and 39 ft by "
            f"9am, so that yard loses the drying day. Keep the sun corridor south of every yard clear of houses "
            f"(the placer does it with s.sun_corridor(39)); a yard may also stagger east or west out of the shadow",
        )
    return _kept(locals(), ('gap', 'hh_', 'nshade', 'par', 'sun_ft', 'sun_ftpx', 'yd'))


def _seg_0285_072__yards_unshaded_by_groves(*, check: Any = _UNBOUND, scale: Any = _UNBOUND, shaded: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.072 (yards_unshaded_by_groves) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "yards_unshaded_by_groves",
            not shaded,
            f"threshing yard(s) {shaded[:3]} have a grove in the sun-corridor just to their SOUTH - it would shade the drying ground; keep groves out of the strip south of any yard",
        )
    return _kept(locals(), ())


# SAME sun rule for the COMMUNAL fengshui trees: no village-grove CLUMP may sit in the southern sun-
# corridor of a threshing yard OR a kitchen garden (both need the drying/growing sun from the south).
# The scatter records its real clumps, so test those, not the bounding poly. WHY: settlements.md 'Village windbreak'.


def _seg_0285_073__cx_1(*, M: Any = _UNBOUND, cx: Any = _UNBOUND, cy: Any = _UNBOUND, g: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.073 (cx, cy, g, vg_clumps) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        vg_clumps = [(cx, cy, g.get("r", 6)) for g in M.get("village_groves", []) for cx, cy in g.get("clumps", [])]
    return _kept(locals(), ('cx', 'cy', 'g', 'vg_clumps'))


def _seg_0285_074__vg_shaded(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.074 (vg_shaded) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        vg_shaded = []  # type: ignore[var-annotated]
    return _kept(locals(), ('vg_shaded',))


def _seg_0285_075__cx_2(
    *,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    f: Any = _UNBOUND,
    gardens: Any = _UNBOUND,
    r: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    se: Any = _UNBOUND,
    vg_clumps: Any = _UNBOUND,
    vg_shaded: Any = _UNBOUND,
    yards: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.075 (cx, cy, f, r) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for f in yards + gardens:
            se = f["y"] + f["h"] / 2
            if any(abs(cx - f["x"]) < f["w"] / 2 + r and se - r < cy < se + 22 + r for cx, cy, r in vg_clumps):
                vg_shaded.append((round(f["x"]), round(f["y"])))
    return _kept(locals(), ('cx', 'cy', 'f', 'r', 'se', 'vg_shaded'))


def _seg_0285_076__village_trees_unshade_yards_and_gardens(*, check: Any = _UNBOUND, scale: Any = _UNBOUND, vg_shaded: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.076 (village_trees_unshade_yards_and_gardens) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "village_trees_unshade_yards_and_gardens",
            not vg_shaded,
            f"a village-grove tree sits in the southern sun-corridor of yard/garden(s) {vg_shaded[:3]} - it would "
            f"shade the drying/growing ground; keep the scatter + belts out of the strip south of any yard or garden",
        )
    return _kept(locals(), ())


# EAST SUN (option): a kitchen garden on a house's lee/EAST side loses its MORNING sun if a neighbor's
# grove arm (or a copse) stands hard against its east. Where a small SOUTHWARD nudge into open ground
# would clear it (the tree then falls to the garden's NE), the placement takes it (_relax_gardens_south).
# This fires ONLY on an AVOIDABLE case - a garden still east-shaded though a clear south-shift existed -
# so a garden genuinely boxed in to the south (paddy/lane/neighbor) is exempt. WHY: settlements.md 'gardens'.
# scoped to the BUNDLE-path farmsteads (villages + to-scale hamlets), where _relax_gardens_south runs;
# a town/city places its outside farms on the legacy path (no south-nudge), so the rule does not apply.


def _seg_0285_077__gardens_unshaded_from_east(
    *,
    M: Any = _UNBOUND,
    _band: Any = _UNBOUND,
    _bed_clear: Any = _UNBOUND,
    _bog: Any = _UNBOUND,
    _e_iv: Any = _UNBOUND,
    _fol: Any = _UNBOUND,
    _hh: Any = _UNBOUND,
    _hill: Any = _UNBOUND,
    _lanes: Any = _UNBOUND,
    _pond: Any = _UNBOUND,
    _shaded: Any = _UNBOUND,
    _water: Any = _UNBOUND,
    a: Any = _UNBOUND,
    b: Any = _UNBOUND,
    box: Any = _UNBOUND,
    bx: Any = _UNBOUND,
    by: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    dy: Any = _UNBOUND,
    east_bad: Any = _UNBOUND,
    f: Any = _UNBOUND,
    gardens: Any = _UNBOUND,
    gd: Any = _UNBOUND,
    gh: Any = _UNBOUND,
    groves: Any = _UNBOUND,
    gv: Any = _UNBOUND,
    gw: Any = _UNBOUND,
    gx: Any = _UNBOUND,
    gy: Any = _UNBOUND,
    h: Any = _UNBOUND,
    hh: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    iv: Any = _UNBOUND,
    k: Any = _UNBOUND,
    ln: Any = _UNBOUND,
    m: Any = _UNBOUND,
    maxshift: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    ol: Any = _UNBOUND,
    own: Any = _UNBOUND,
    p: Any = _UNBOUND,
    r: Any = _UNBOUND,
    s: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    st: Any = _UNBOUND,
    vg_clumps: Any = _UNBOUND,
    wp: Any = _UNBOUND,
    yards: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.077 (gardens_unshaded_from_east) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city') and groves and meta.get("toscale", scale == "village"):
        _band = 22
        _hh = {(round(h["x"]), round(h["y"])): h["h"] for h in houses}
        _lanes = M.get("lanes", [])
        _bog = [m["poly"] for m in M.get("marshes", []) if m.get("role") != "pond_fringe" and m.get("poly")]
        _water = [c["poly"] for c in M.get("channels", [])] + [st["poly"] for st in M.get("streams", [])]
        _fol = [f["outline"] for f in M.get("fields", []) if f.get("outline")]
        _hill, _pond = M.get("hill"), M.get("pond")

        def _e_iv(ge: float, own: tuple[float, ...]) -> list[tuple[float, float]]:
            iv = [(gv["y"] - gv["h"] / 2, gv["y"] + gv["h"] / 2) for gv in groves if tuple(gv.get("of", [])) != own and ge - 2 <= gv["x"] - gv["w"] / 2 < ge + _band]
            iv += [(cy - r, cy + r) for cx, cy, r in vg_clumps if ge - 2 <= cx - r < ge + _band]
            return iv

        def _shaded(lane: tuple[float, float], iv: list[tuple[float, float]]) -> bool:
            return any(a < lane[1] and lane[0] < b for a, b in iv)

        def _bed_clear(bx: float, by: float, bw: float, bh: float, own: tuple[float, ...]) -> bool:
            box = (bx - bw / 2, by - bh / 2, bx + bw / 2, by + bh / 2)
            for h in houses:
                if (round(h["x"]), round(h["y"])) != (round(own[0]), round(own[1])) and abs(bx - h["x"]) < (bw + h["w"]) / 2 and abs(by - h["y"]) < (bh + h["h"]) / 2:
                    return False
            for s in yards + groves + gardens + M.get("farm_sheds", []) + M.get("byres", []):
                if tuple(s.get("of", [])) == own:  # skip the garden's OWN yard/grove/beds/shed
                    continue
                if abs(bx - s["x"]) < (bw + s["w"]) / 2 and abs(by - s["y"]) < (bh + s["h"]) / 2:
                    return False
            if any(_box_hits_poly(box, ol) for ol in _fol) or any(_box_hits_poly(box, p) for p in _bog):
                return False
            for ln in _lanes:
                p = ln["pts"]
                if any(seg_dist(bx, by, p[k], p[k + 1]) < ln.get("w", 6) / 2 + 2 for k in range(len(p) - 1)):
                    return False
            for wp in _water:
                if any(seg_dist(bx, by, wp[k], wp[k + 1]) < 6 for k in range(len(wp) - 1)):
                    return False
            return not ((_hill and in_ellipse(bx, by, _hill)) or (_pond and in_ellipse(bx, by, _pond)))

        east_bad = []
        for gd in gardens:
            gx, gy, gw, gh = gd["x"], gd["y"], gd["w"], gd["h"]
            own = tuple(gd.get("of", []))
            iv = _e_iv(gx + gw / 2, own)
            if not _shaded((gy - gh / 2, gy + gh / 2), iv):
                continue  # not currently east-shaded
            hh = _hh.get((round(own[0]), round(own[1])), gh) if own else gh
            maxshift, dy = gh + hh + 6, 4
            while dy <= maxshift:
                if not _shaded((gy + dy - gh / 2, gy + dy + gh / 2), iv) and _bed_clear(gx, gy + dy, gw, gh, own):
                    east_bad.append((round(gx), round(gy)))  # a clear south-shift existed -> avoidable
                    break
                dy += 4
        check(
            "gardens_unshaded_from_east",
            not east_bad,
            f"kitchen garden(s) {east_bad[:4]} sit with a tree hard against their EAST (losing the morning sun) "
            f"though a small SOUTHWARD shift into open ground would clear it - nudge the garden south of the "
            f"tree (the placement's _relax_gardens_south does this; a garden truly boxed in south is exempt)",
        )
    return _kept(
        locals(),
        (
            '_band',
            '_bed_clear',
            '_bog',
            '_e_iv',
            '_fol',
            '_hh',
            '_hill',
            '_lanes',
            '_pond',
            '_shaded',
            '_water',
            'c',
            'dy',
            'east_bad',
            'f',
            'gd',
            'gh',
            'gw',
            'gx',
            'gy',
            'h',
            'hh',
            'iv',
            'm',
            'maxshift',
            'own',
            'st',
        ),
    )


# SCALE: the typical grove must read as the LARGEST homestead appurtenance - a real stand of dozens
# of trees, not a clump. The median grove's total footprint (its arms) must be >= ~0.75x the house
# it shelters (the spacious farms run well above; a single-arm grove on a cramped farm pulls the
# median but stays substantial). This catches a regression that shrinks groves back to a few trees.


def _seg_0285_078__groves_are_substantial(
    *,
    a: Any = _UNBOUND,
    check: Any = _UNBOUND,
    gk: Any = _UNBOUND,
    grove_of: Any = _UNBOUND,
    groves: Any = _UNBOUND,
    gsz: Any = _UNBOUND,
    gv: Any = _UNBOUND,
    h: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    hsz: Any = _UNBOUND,
    med: Any = _UNBOUND,
    ratios: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.078 (groves_are_substantial) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city') and len(grove_of) >= 6:
        hsz = {(round(h["x"]), round(h["y"])): h["w"] * h["h"] for h in houses}
        gsz: dict[tuple[int, int], float] = {}  # type: ignore[no-redef]
        for gv in groves:
            gk = (round(gv["of"][0]), round(gv["of"][1]))
            gsz[gk] = gsz.get(gk, 0) + gv["w"] * gv["h"]
        ratios = sorted(a / hsz[gk] for gk, a in gsz.items() if gk in hsz and hsz[gk])
        med = ratios[len(ratios) // 2]
        check(
            "groves_are_substantial",
            med >= 0.5,
            f"the typical homestead grove is too small (median {med:.2f}x its house) - the spacious farms must "
            f"carry a real stand (a yashikirin is the LARGEST homestead feature); small clumps on cramped farms "
            f"are fine, but a median below half the house means groves shrank back to a few trees everywhere",
        )
    return _kept(locals(), ('a', 'gk', 'gsz', 'gv', 'h', 'hsz', 'med', 'ratios'))


# VISIBLE: the dooryard garden must not be buried under a grove (the homestead solver spaces the
# garden to the LEE side and the grove to the windward, so they never stack). A garden substantially
# overlapped by a grove arm is a regression. WHY: settlements.md "Homestead groves".


def _seg_0285_079__g_buried(*, gardens: Any = _UNBOUND, gd: Any = _UNBOUND, groves: Any = _UNBOUND, gv: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.079 (g_buried, gd, gv) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        g_buried = [
            (round(gd["x"]), round(gd["y"])) for gd in gardens if any(abs(gd["x"] - gv["x"]) < (gd["w"] + gv["w"]) / 2 - 3 and abs(gd["y"] - gv["y"]) < (gd["h"] + gv["h"]) / 2 - 3 for gv in groves)
        ]
    return _kept(locals(), ('g_buried', 'gd', 'gv'))


def _seg_0285_080__gardens_clear_of_groves(*, check: Any = _UNBOUND, g_buried: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.080 (gardens_clear_of_groves) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "gardens_clear_of_groves",
            not g_buried,
            f"kitchen garden(s) {g_buried[:3]} sit under a homestead grove - the solver spaces the garden to the LEE side and the grove to the windward; they must not overlap",
        )
    return _kept(locals(), ())


# WHERE POSSIBLE: a grove is drawn on EVERY farmhouse that has windward room - the yashikirin ringed
# every dispersed farmstead - so a grove-LESS farm must be one whose windward side is genuinely blocked
# (a paddy, a neighbor, or the sun-corridor south of a yard). If a grove-less farm has CLEAR windward
# room, the generator omitted a grove it could have placed. Replaces the old blunt presence floor.


def _seg_0285_081__groves_where_possible(
    *,
    B: Any = _UNBOUND,
    Hm: Any = _UNBOUND,
    M: Any = _UNBOUND,
    WF: Any = _UNBOUND,
    Wm: Any = _UNBOUND,
    avoid: Any = _UNBOUND,
    c: Any = _UNBOUND,
    ch: Any = _UNBOUND,
    check: Any = _UNBOUND,
    clump_clear: Any = _UNBOUND,
    corridors: Any = _UNBOUND,
    crop_ol: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    dpl: Any = _UNBOUND,
    e: Any = _UNBOUND,
    fdx: Any = _UNBOUND,
    fdy: Any = _UNBOUND,
    fields_ol: Any = _UNBOUND,
    gardens: Any = _UNBOUND,
    grove_of: Any = _UNBOUND,
    hh_: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    hw: Any = _UNBOUND,
    hx: Any = _UNBOUND,
    hy: Any = _UNBOUND,
    k: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    min_clump: Any = _UNBOUND,
    n: Any = _UNBOUND,
    ol: Any = _UNBOUND,
    omitted: Any = _UNBOUND,
    others: Any = _UNBOUND,
    par: Any = _UNBOUND,
    perp: Any = _UNBOUND,
    poly: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    s: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    vx: Any = _UNBOUND,
    vy: Any = _UNBOUND,
    windward: Any = _UNBOUND,
    yards: Any = _UNBOUND,
    yd: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.081 (groves_where_possible) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city') and scale in ("town", "village", "hamlet") and len(houses) >= 10 and not meta.get("nucleated"):
        WF = {
            "N": [((0, -1), 0)],
            "S": [((0, 1), 0)],
            "E": [((1, 0), 0)],
            "W": [((-1, 0), 0)],
            "NW": [((0, -1), -1), ((-1, 0), 0)],
            "NE": [((0, -1), 1), ((1, 0), 0)],
            "SW": [((0, 1), -1), ((-1, 0), 0)],
            "SE": [((0, 1), 1), ((1, 0), 0)],
        }
        avoid = others + gardens + yards + M.get("manors", []) + M.get("religious", [])
        corridors = [c for c in [M.get("lane"), M.get("road")] if c]
        corridors += [(c.get("poly", c) if isinstance(c, dict) else c) for c in M.get("channels", [])]
        corridors += [(s.get("poly", s) if isinstance(s, dict) else s) for s in M.get("streams", [])]
        # a town RAMPART blocks a grove belt exactly like a road: a farm hugging the wall has a
        # wall-shaded windward side (the placement side refuses via the wall's no-build corridor)
        corridors += [M["wall"]] if M.get("wall") else []
        Wm, Hm = meta.get("W", 1820), meta.get("H", 1180)

        def min_clump(hh_: dict[str, Any], fdx: float, fdy: float, perp: float) -> tuple[float, float, float, float]:
            hx, hy, hw, hz = hh_["x"], hh_["y"], hh_["w"], hh_["h"]
            dm = 13 * hw / 44.0  # minimal-clump depth (44 = base house width / bscale)
            if fdy:
                return hx + perp * dm / 2, hy + fdy * (hz / 2 + dm / 2 + 1.5), (hw + dm) * 0.5, dm
            return hx + fdx * (hw / 2 + dm / 2 + 1.5), hy, dm, hz * 0.5

        # B is a CONSERVATIVE margin: the check only claims "room" when the windward side is CLEARLY
        # open (room + B px), so it fires on a gross omission (a farm with plenty of space and no grove)
        # but tolerates the borderline cases where this check can't perfectly mirror the placement test.
        B = 7
        # ALL cropland blocks a grove clump, not just the flooded paddy: the dry hem strips /
        # garden tracts are barley, and trees do not grow in the barley either (the placement
        # side refuses them via dry_polys in _grove_fits) - so a hem-shadowed windward side
        # legitimately leaves a farm grove-less, same as a paddy-shadowed one. LOCAL to this
        # check: the shared fields_ol stays paddy-only (its other uses mean "in the rice").
        crop_ol = fields_ol + [dpl["poly"] for dpl in M.get("dry_plots", [])]

        def clump_clear(cx: float, cy: float, cw: float, ch: float, par: tuple[int, int]) -> bool:
            if cx < 55 or cx > Wm - 55 or cy < 88 or cy > Hm - 26:
                return False
            rc = rect_corners({"x": cx, "y": cy, "w": cw, "h": ch, "rot": 0})
            for ol in crop_ol:
                n = len(ol)
                if (
                    point_in_poly(cx, cy, ol)
                    or edge_dist(cx, cy, ol) < 14 + B  # mirror settlement._in_blocked
                    or any(point_in_poly(px, py, ol) for px, py in rc)
                    or any(point_in_poly(vx, vy, rc) for vx, vy in ol)
                    or any(segments_cross(rc[e], rc[(e + 1) % 4], ol[k], ol[(k + 1) % n]) for e in range(4) for k in range(n))
                ):
                    return False
            for s in avoid:
                if (round(s["x"]), round(s["y"])) == par:
                    continue
                if abs(cx - s["x"]) < (cw + s["w"]) / 2 + B and abs(cy - s["y"]) < (ch + s["h"]) / 2 + B:
                    return False
            for yd in yards:
                if abs(cx - yd["x"]) < (cw + yd["w"]) / 2 + B and abs(cy - (yd["y"] + yd["h"] / 2 + 11)) < (ch + 22) / 2 + B:
                    return False
            return all(not (len(poly) >= 2 and any(seg_dist(cx, cy, poly[k], poly[k + 1]) < 20 + B for k in range(len(poly) - 1))) for poly in corridors)

        omitted = []
        for hh_ in houses:
            if hh_.get("role") == "headman" or hh_.get("kind") == "abandoned":
                continue
            par = (round(hh_["x"]), round(hh_["y"]))
            if par in grove_of:
                continue
            if any(clump_clear(*min_clump(hh_, fdx, fdy, perp), par) for (fdx, fdy), perp in WF.get(windward, WF["NW"])):
                omitted.append(par)
        check(
            "groves_where_possible",
            not omitted,
            f"farm(s) {omitted[:4]} have clear windward room but no grove - a yashikirin is drawn on every farm "
            f"that can host one; only a paddy/neighbor/yard-shaded windward side may leave a farm grove-less",
        )
    return _kept(locals(), ('B', 'Hm', 'WF', 'Wm', 'avoid', 'c', 'clump_clear', 'corridors', 'crop_ol', 'dpl', 'fdx', 'fdy', 'hh_', 'min_clump', 'omitted', 'par', 'perp', 's'))


# NUCLEATED villages shelter behind a COMMUNAL fengshui WINDBREAK (风水林), NOT per-house groves: a
# dense grove belt on the high WINDWARD back edge (the winter-monsoon wall + sacred back-village
# grove), a smaller cluster at the low water-mouth entrance, and scattered bamboo/fruit copses. So a
# nucleated village is NOT required to grove every farm (groves_where_possible is skipped above for
# meta.nucleated); instead it MUST carry the village windbreak, on the windward side, off the paddies.
# WHY (the fengshui-forest research - ~2 groves/village, a ~1-2 ha back grove at ~3,400 stems/ha, a
# water-mouth cluster, kept off the crops and the road): settlements.md 'Village windbreak'.


def _seg_0285_082__vgroves(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.082 (vgroves) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        vgroves = M.get("village_groves", [])
    return _kept(locals(), ('vgroves',))


def _seg_0285_083__village_windbreak_present(
    *,
    M: Any = _UNBOUND,
    c: Any = _UNBOUND,
    canopy: Any = _UNBOUND,
    ccx: Any = _UNBOUND,
    ccy: Any = _UNBOUND,
    check: Any = _UNBOUND,
    fline: Any = _UNBOUND,
    fnear: Any = _UNBOUND,
    forest_shelters: Any = _UNBOUND,
    g: Any = _UNBOUND,
    h: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    i: Any = _UNBOUND,
    lee: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    nestle_d: Any = _UNBOUND,
    roofs: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    subst_wb: Any = _UNBOUND,
    vgroves: Any = _UNBOUND,
    windbreaks: Any = _UNBOUND,
    windward: Any = _UNBOUND,
    wvx: Any = _UNBOUND,
    wvy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.083 (village_windbreak_embraces_cluster, village_windbreak_on_windward_side, village_windbreak_present, village_windbreak_scales_with_cluster) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city') and meta.get("nucleated") and len(houses) >= 10:
        windbreaks = [g for g in vgroves if g.get("role") == "windbreak"]
        check(
            "village_windbreak_present",
            bool(windbreaks),
            "a nucleated village shelters behind a COMMUNAL windbreak (a fengshui back-village grove), but "
            "no role='windbreak' village grove is present - add s.village_grove(..., role='windbreak') on the "
            "high windward edge",
        )
        # the belt backs the cluster on the WINDWARD/high side (default NW) - its centroid must lie
        # windward of the house-cluster centroid, so the wall faces the cold wind, not the sunny field side
        ccx = sum(h["x"] for h in houses) / len(houses)
        ccy = sum(h["y"] for h in houses) / len(houses)
        lee = [(round(g["x"]), round(g["y"])) for g in windbreaks if (g["x"] - ccx) * wvx + (g["y"] - ccy) * wvy <= 0]
        # THE BELT EMBRACES THE CLUSTER - the doctrine's "nestles against and embraces"
        # (GM 2026-07), automated via a form-aware ADJACENCY metric after the windward-
        # canopy-fraction metric failed calibration (approved Kikuta scores 4-18% on it):
        # at least one SUBSTANTIAL windbreak grove (>= 12 clumps) must stand within 150px
        # of a farmhouse. Far corner forest masses are welcome extras; a map with ONLY far
        # masses is decoration, not a wind wall. Calibrated 2026-07: approved maps nestle
        # at 37-131px (Kikuta's ribbon belt is the 131 outlier).
        # a map whose wood is a REAL FOREST (M["forest"], the edge-feature wood) can let that
        # forest BE the windbreak - the strongest wind wall of all - but ONLY where the wood
        # actually shelters THIS cluster: its tree line must come within the same NESTLE
        # distance of a farmhouse AND stand WINDWARD of the cluster centroid. A blanket
        # "has a forest -> exempt" is what let Moritono pass with an 11-clump belt while its
        # Shirin Forest sat 1,089 ft away on the LEE (E) side under an NW wind (GM 2026-07-25):
        # a wood downwind and a fifth of a mile off breaks no wind. Small forest_patches do NOT exempt.
        fline = M.get("forest") or []
        fnear = min(((seg_dist(h["x"], h["y"], fline[i], fline[i + 1]), fline[i]) for h in houses for i in range(len(fline) - 1)), default=None)
        forest_shelters = fnear is not None and fnear[0] <= 150 and (fnear[1][0] - ccx) * wvx + (fnear[1][1] - ccy) * wvy > 0
        subst_wb = [] if forest_shelters else [g for g in windbreaks if len(g.get("clumps", [])) >= 12]
        nestle_d = min((min(math.hypot(c[0] - h["x"], c[1] - h["y"]) for c in g["clumps"] for h in houses) for g in subst_wb), default=None)
        check(
            "village_windbreak_embraces_cluster",
            forest_shelters or (bool(subst_wb) and nestle_d is not None and nestle_d <= 150),
            f"no substantial windbreak belt (>= 12 clumps) nestles against the farm cluster (nearest {None if nestle_d is None else round(nestle_d)}px; want <= 150) - "
            f"the back-village grove EMBRACES the houses' windward fringe; far corner masses alone are decoration",
        )
        check(
            "village_windbreak_on_windward_side",
            not lee,
            f"the village windbreak sits on the LEE/sunny side of the cluster, not the windward {windward}: "
            f"{lee[:2]} - the back-village grove shelters the high windward edge and leaves the sunny field side open",
        )
        # THE BELT SCALES WITH THE CLUSTER (GM 2026-07-25, after Moritono's belt read as a few
        # blobs behind 16 farmhouses). The >= 12-clump embrace test above is a FIXED floor, so a
        # belt sized for a 5-house corner passes unchanged behind a whole hamlet. Measure the
        # SHELTER the map actually draws - the windbreak's canopy disks plus any per-house
        # yashikirin footprints (a map may do both, e.g. Hikari-no-Sato) - against the ROOF area
        # it shelters. Both sides are px^2, so the ratio is scale-free (a 2 ft/px village draws
        # smaller roofs AND, per meta()'s village bscale exemption, larger clumps; the ratio is
        # unaffected). WHY this framing: the doctrine (settlements.md 'Village windbreak') wants
        # the belt to be the settlement's LARGEST vegetation feature, and the research figure -
        # a modest village back grove under 1 ha, ~1,800 sq ft per household - sits near ratio
        # ~1.3 at our house sizes. So 0.40 is a floor against absurdity, not a target: a wind
        # wall covering less than half the ground its own roofs do is decoration. Calibrated on
        # the pool 2026-07-25: approved maps run 0.45 (Hoshizora, a town whose farm zone is a
        # thin wedge) through 7.27 (Hikari-no-Sato); Moritono's belt scored 0.30.
        canopy = sum(len(g.get("clumps", [])) * math.pi * g.get("r", 14) ** 2 for g in windbreaks)
        canopy += sum(g.get("w", 0) * g.get("h", 0) for g in M.get("groves", []))
        roofs = sum(h.get("w", 0) * h.get("h", 0) for h in houses)
        check(
            "village_windbreak_scales_with_cluster",
            forest_shelters or canopy >= 0.40 * roofs,
            f"the windbreak is too small for the cluster it shelters: {round(canopy)}px^2 of canopy over "
            f"{len(houses)} farmhouses covering {round(roofs)}px^2 of roof (ratio {canopy / roofs if roofs else 0:.2f}; want >= 0.40) - "
            f"the back-village grove is the settlement's LARGEST vegetation feature, so deepen the belt "
            f"(more clump rows) or wrap it further around the windward faces",
        )
    return _kept(locals(), ('c', 'canopy', 'ccx', 'ccy', 'fline', 'fnear', 'forest_shelters', 'g', 'h', 'i', 'lee', 'nestle_d', 'roofs', 'subst_wb', 'windbreaks'))


# every village grove (of any role) is DRY woodland - no TREE may stand in a flooded paddy. Test the
# DRAWN CLUMPS, not the recorded bbox center (GM 2026-07-25, same correction commons_clear_of_paddies
# already took): a back-village belt is a long crescent hugging the field edge, so the center of the
# box around it can sit over the crop while every tree in it stands on dry ground - Ueda's 87-clump
# belt scored exactly that. Testing the clumps also gives the check MORE teeth, not less: it now
# measures the same thing the placement does (village_grove skips a clump landing in a field), so a
# gen whose engine-side field list is empty - the recurring trap - is caught here instead of hidden.
# A grove that records no clumps at all falls back to its center, for older maps; one that records
# neither (a bare poly, as some check fixtures carry) contributes no test point rather than raising.


def _seg_0285_084__c_1(*, c: Any = _UNBOUND, g: Any = _UNBOUND, scale: Any = _UNBOUND, vgroves: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.084 (c, g, vg_pts) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        vg_pts = [c for g in vgroves for c in (g.get("clumps") or ([[g["x"], g["y"]]] if "x" in g and "y" in g else []))]
    return _kept(locals(), ('c', 'g', 'vg_pts'))


def _seg_0285_085__c_2(*, c: Any = _UNBOUND, fields_ol: Any = _UNBOUND, ol: Any = _UNBOUND, scale: Any = _UNBOUND, vg_pts: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.085 (c, ol, vg_in_paddy) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        vg_in_paddy = [(round(c[0]), round(c[1])) for c in vg_pts if any(point_in_poly(c[0], c[1], ol) for ol in fields_ol)]
    return _kept(locals(), ('c', 'ol', 'vg_in_paddy'))


def _seg_0285_086__village_groves_clear_of_paddies(*, check: Any = _UNBOUND, scale: Any = _UNBOUND, vg_in_paddy: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.086 (village_groves_clear_of_paddies) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "village_groves_clear_of_paddies",
            not vg_in_paddy,
            f"village grove tree(s) stand IN a flooded paddy: {vg_in_paddy[:3]} - the fengshui windbreak stands on dry ground at the cluster's back and entrance, never out in the paddy",
        )
    return _kept(locals(), ())


# A grove clump (a tree blob, radius r) may abut a farmstead - trees stand right up against a house
# wall - but it must NOT OVERLAP a building/yard/garden footprint (a tree drawn ON the roof reads
# wrong). Both the placement (the village_grove keep-out uses the clump's FULL radius) and this check
# enforce it. The nominal blob radius is the measure; canopy leaves spilling a few px onto the eaves
# are "adjacent," which is fine. Covers the whole homestead: house, threshing yard, kitchen garden,
# draft byre, farm shed. WHY (trees beside, not on, the buildings): settlements.md 'Village windbreak'.


def _seg_0285_087___clm(*, cx: Any = _UNBOUND, cy: Any = _UNBOUND, g: Any = _UNBOUND, scale: Any = _UNBOUND, vgroves: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.087 (_clm, cx, cy, g) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        _clm = [(cx, cy, g.get("r", 6)) for g in vgroves for cx, cy in g.get("clumps", [])]
    return _kept(locals(), ('_clm', 'cx', 'cy', 'g'))


def _seg_0285_088__on_struct(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.088 (on_struct) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        on_struct = []  # type: ignore[var-annotated]
    return _kept(locals(), ('on_struct',))


def _seg_0285_089__cx_3(
    *,
    M: Any = _UNBOUND,
    _clm: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    k: Any = _UNBOUND,
    o: Any = _UNBOUND,
    on_struct: Any = _UNBOUND,
    r: Any = _UNBOUND,
    rect: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.089 (cx, cy, k, o) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for k in ("houses", "threshing_yards", "gardens", "byres", "farm_sheds"):
            for o in M.get(k, []):
                rect = _struct_rect(o)
                for cx, cy, r in _clm:
                    if pt_to_rect(cx, cy, rect) < r - 1:  # real penetration (just-touching is allowed)
                        on_struct.append((k, round(o["x"]), round(o["y"])))
                        break
    return _kept(locals(), ('cx', 'cy', 'k', 'o', 'on_struct', 'r', 'rect'))


def _seg_0285_090__grove_clumps_clear_of_structures(*, check: Any = _UNBOUND, on_struct: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.090 (grove_clumps_clear_of_structures) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "grove_clumps_clear_of_structures",
            not on_struct,
            f"{len(on_struct)} farmstead footprint(s) have a grove-clump tree drawn OVER them: {on_struct[:4]} - "
            f"a copse/windbreak clump may stand right beside a house but never ON it; widen the village_grove "
            f"keep-out to the clump's full radius so the blob settles into the open ground beside the buildings",
        )
    return _kept(locals(), ())


# FUEL-AND-FODDER COMMONS - the degraded open grazing/scrub on the far side, BEYOND the back-grove.
# South China's hills were stripped for fuel/timber over a millennium (open pine + grass + erosion),
# so past the protected grove is NON-ARABLE waste: coarse grass, brush, scraggly pines - a commons,
# not a field, and never the flooded paddy. The land toposequence is village -> back-grove -> fuel
# commons, so the commons sits on the WINDWARD/high side and FURTHER out than the windbreak. WHY (the
# denuded hills + back-slope waste; graves + dry hill-crops also live here): settlements.md 'Village windbreak'.
# Test the DRAWN OUTCOME, not the patch's bbox CENTER. `commons()` skips every paddy point when it
# scatters, so scrub can never actually be drawn on a flooded field - "is the center over water" was
# only ever a PROXY for that, and a wrong one: an INTERIOR fill (the patch that clothes the voids an
# irregular field leaves inside its own bbox) legitimately has its center on the crop while every
# glyph it draws falls in the voids around it. Scoring the center would fail a correct patch, which
# is the same bbox-stands-in-for-real-geometry mistake as the phantom field tail. What genuinely
# goes wrong is a patch placed where it can clothe NOTHING - it silently draws nothing at all - so
# that is what we test: sample each patch and require real open (non-crop) ground under it.


def _seg_0285_091__commons(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.091 (commons) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        commons = M.get("commons", [])
    return _kept(locals(), ('commons',))


def _seg_0598__nucleated_records_cluster_seeding(*, M: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 598 (settlement_records_cluster_seeding) - hand-added 2026-08-16 past the
    legacy range (see _seg_0595 in segments_08 for the numbering convention). New-style:
    writes=()."""
    # A KNOB THAT CAN SILENTLY NOT-RECORD IS THE "CHECK THAT NEVER RUNS" SHAPE (known-open
    # ledger 2026-08-16, Kashikawa: the front rows + lane frontage seated all 20 houses, the
    # cluster-seeds cloud never ran, and the rolled cluster_shape knob went unhonored with
    # no trace on the manifest - the twin-detector axis silently fell back to the bbox
    # aspect). The declaration-exists ratchet (settlement_declares_a_land_fall is the
    # model): a nucleated scripted map must record either the honored knob
    # (meta.cluster_shape, written by cluster_seeds when the cloud runs) or the seeding
    # mode that replaced it (meta.cluster_seeding, written by stage_homesteads).
    if M["meta"].get("generated_by") and M["meta"].get("nucleated"):
        _cs_ok = ("cluster_shape" in M["meta"]) or ("cluster_seeding" in M["meta"])
        check(
            "settlement_records_cluster_seeding",
            _cs_ok,
            "a nucleated scripted map records neither meta.cluster_shape (the cluster-seeds cloud ran and honored the knob) nor meta.cluster_seeding (the rows/frontage passes seated every house and the rolled shape went unhonored) - a rolled knob must leave a trace either way, or it can silently not-record with nothing warning; stage_homesteads records the seeding mode",
        )
    return _kept(locals(), ())
