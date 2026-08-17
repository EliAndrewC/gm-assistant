"""Gate segments (yards gardens and sheds; keys 0285_006-0285_065) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from l7r.diagram.settlement import FARMHOUSE_EAVE_GAP_FT, sat_overlap, surface_water_dist

from .common_01_geometry import (
    _OVERLAP_STRUCTS,
    _struct_rect,
    point_in_poly,
    poly_area,
    rect_corners,
    seg_dist,
    segments_cross,
    within_edge_gap,
)
from .common_02_overlap_policy import in_ellipse
from .common_03_capacity import _UNBOUND, _kept


def _seg_0285_006__settlement_has_wells(
    *,
    M: Any = _UNBOUND,
    REACH: Any = _UNBOUND,
    SHRINE_FAR: Any = _UNBOUND,
    SHRINE_WELL_GAP: Any = _UNBOUND,
    b: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d: Any = _UNBOUND,
    dry: Any = _UNBOUND,
    dwell: Any = _UNBOUND,
    h: Any = _UNBOUND,
    i: Any = _UNBOUND,
    lines: Any = _UNBOUND,
    ln: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    pond: Any = _UNBOUND,
    r: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    shrine_hill: Any = _UNBOUND,
    st: Any = _UNBOUND,
    wellless: Any = _UNBOUND,
    wells: Any = _UNBOUND,
    wl: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.006 (remote_shrine_has_own_well, settlement_dwellings_watered, settlement_has_wells) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and dwell:
        check(
            "settlement_has_wells",
            len(wells) >= max(1, round(len(dwell) / 25)),
            f"a {scale} of {len(dwell)} households has only {len(wells)} communal well(s) - every settlement "
            f"keeps wells (about one per 20-25 households); scatter them among the dwellings with s.place_wells(...)",
        )
        lines = [c["poly"] for c in M.get("channels", [])] + [st["poly"] for st in M.get("streams", [])] + ([M["moat"]] if M.get("moat") else [])
        pond = M.get("pond")
        REACH = round(760 / float(meta.get("ftpx") or meta.get("ft_per_px") or 2.0))  # ~760 ft, in px at this map's scale (380 at 2 ft/px)
        dry = []
        for h in dwell:
            # the surface-water half is the SHARED predicate `settlement.surface_water_dist` -
            # the same call hamletgen.place_wells makes when deciding which houses need a well
            # (known-open ledger 2026-08-16: two definitions of "needs a well" had drifted).
            # `lines`/`pond` above stay bound for downstream-segment parity; the verdict reads
            # the helper.
            d = min((math.hypot(h["x"] - wl["x"], h["y"] - wl["y"]) for wl in wells), default=1e9)
            d = min(d, surface_water_dist(M, h["x"], h["y"]))
            if d > REACH:
                dry.append((round(h["x"]), round(h["y"])))
        check(
            "settlement_dwellings_watered",
            not dry,
            f"{len(dry)} household(s) more than {REACH}px from any water source - a well, or an irrigation channel / pond / stream / moat: {dry[:4]} - put a well within reach",
        )

        # A shrine/temple set sufficiently APART from the village keeps its OWN WELL close by for purification
        # (temizu): too far to walk to the village's shared wells, it needs a dedicated draw-point right beside
        # it - and specifically a WELL, not just any water (a ditch/pond is not an ablution source). A shrine
        # AMONG or near the houses shares the village wells (exempt). "Set apart" = the nearest dwelling is more
        # than SHRINE_FAR px away; "close by" = a well within SHRINE_WELL_NEAR px.
        SHRINE_FAR, SHRINE_WELL_GAP = 150, 70
        shrine_hill = M.get("hill")
        wellless = []
        for r in M.get("religious", []):
            if shrine_hill and in_ellipse(r["x"], r["y"], shrine_hill):
                continue  # a hilltop/mountain shrine draws from a spring/basin, not a dug well
            if min((math.hypot(r["x"] - b["x"], r["y"] - b["y"]) for b in dwell), default=1e9) <= SHRINE_FAR:
                continue  # among/near the houses -> shares the village wells
            if not any(within_edge_gap(r, wl, SHRINE_WELL_GAP) for wl in wells):  # the TRUE gap to the hall's edge (a big monastery's well sits further out)
                wellless.append((round(r["x"]), round(r["y"])))
        check(
            "remote_shrine_has_own_well",
            not wellless,
            f"{len(wellless)} shrine/temple(s) set apart from the village (>{SHRINE_FAR}px from any house) with no well beside them - a remote shrine keeps its own well for ablution: {wellless[:4]}",
        )
    return _kept(locals(), ('REACH', 'SHRINE_FAR', 'SHRINE_WELL_GAP', 'b', 'c', 'd', 'dry', 'h', 'i', 'lines', 'ln', 'pond', 'r', 'shrine_hill', 'st', 'wellless', 'wl'))


def _seg_0285_007__fdef(*, fdef: Any = _UNBOUND, fields: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.007 (fdef, fields_ol) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        fields_ol = [fdef["outline"] for fdef in fields]
    return _kept(locals(), ('fdef', 'fields_ol'))


def _seg_0285_008__yards(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.008 (yards) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        yards = M.get("threshing_yards", [])
    return _kept(locals(), ('yards',))


# the HEADMAN is NOT exempt (GM 2026-07-21, caught on Hikari no Sato): the old role=="headman"
# carve-out here existed only because the dispersed-style headman() predated the homestead
# bundle and drew a lone house - the check was written around the bug. The headman is the
# LARGEST farmstead in the village and threshes its own rice like every other household.


def _seg_0285_009__h(*, h: Any = _UNBOUND, houses: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.009 (h, occ_h) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        occ_h = [h for h in houses if h.get("kind") != "abandoned"]
    return _kept(locals(), ('h', 'occ_h'))


# the work yard (niwa) was UNIVERSAL: EVERY farmhouse threshed and dried its own rice on its own
# yard, so EVERY farmhouse must have one (a firm 100%). The generator guarantees this by making
# the yard integral to farmstead placement - a house is only sited where its yard also fits
# (nudging it as needed) - so a farmhouse without a yard is a generator bug, not a density limit.


def _seg_0285_010__h_1(*, h: Any = _UNBOUND, occ_h: Any = _UNBOUND, scale: Any = _UNBOUND, t: Any = _UNBOUND, yards: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.010 (h, t, without) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        without = [(round(h["x"]), round(h["y"])) for h in occ_h if not any(t["of"][0] == h["x"] and t["of"][1] == h["y"] for t in yards)]
    return _kept(locals(), ('h', 't', 'without'))


def _seg_0285_011__harvest_yards_present(*, check: Any = _UNBOUND, occ_h: Any = _UNBOUND, scale: Any = _UNBOUND, without: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.011 (harvest_yards_present) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "harvest_yards_present",
            not without,
            f"a {scale} threshes and dries its rice at the farmstead, and the work yard was universal: "
            f"{len(without)} of {len(occ_h)} farmhouses have NO threshing/drying yard {without[:3]} - every "
            f"farmhouse must have one (placement makes the yard integral to the farmstead)",
        )
    return _kept(locals(), ())


# the yard is the farmstead's own dry work apron, SMALLER than the house it serves (not a
# second dwelling). Each yard records `of` = its parent farmhouse center.


def _seg_0285_012__h_2(*, h: Any = _UNBOUND, houses: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.012 (h, hmap) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        hmap = {(round(h["x"]), round(h["y"])): h["w"] * h["h"] for h in houses}
    return _kept(locals(), ('h', 'hmap'))


def _seg_0285_013__oversize(*, hmap: Any = _UNBOUND, scale: Any = _UNBOUND, t: Any = _UNBOUND, yards: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.013 (oversize, t) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        oversize = [(round(t["x"]), round(t["y"])) for t in yards if t["w"] * t["h"] >= hmap.get((round(t["of"][0]), round(t["of"][1])), 0)]
    return _kept(locals(), ('oversize', 't'))


def _seg_0285_014__harvest_yards_smaller_than_farmhouse(*, check: Any = _UNBOUND, oversize: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.014 (harvest_yards_smaller_than_farmhouse) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check("harvest_yards_smaller_than_farmhouse", not oversize, f"threshing yard(s) are not smaller than their farmhouse: {oversize[:3]} - the niwa is a small dry apron beside the house")
    return _kept(locals(), ())


# the yard is the maeniwa - the SOUTH-facing front work yard. Rice must dry in the SUN and
# minka face south, so the yard sits on the house's south/front side (or, if the paddy blocks
# that, a side), but NEVER the shady NORTH back. +y is south here, so a yard must not sit
# meaningfully north of (above) its own farmhouse center (`of[1]`).


def _seg_0285_015__shady(*, scale: Any = _UNBOUND, t: Any = _UNBOUND, yards: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.015 (shady, t) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        shady = [(round(t["x"]), round(t["y"])) for t in yards if t["y"] < t["of"][1] - 5]
    return _kept(locals(), ('shady', 't'))


def _seg_0285_016__harvest_yards_on_sunny_side(*, check: Any = _UNBOUND, scale: Any = _UNBOUND, shady: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.016 (harvest_yards_on_sunny_side) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "harvest_yards_on_sunny_side",
            not shady,
            f"threshing yard(s) sit on the shady NORTH/back side of their farmhouse: {shady[:3]} - the niwa is the "
            f"south-facing front work yard (rice must dry in the sun), so it belongs on the house's south/front side",
        )
    return _kept(locals(), ())


# the yard is a DRY tamped floor: its whole footprint must stay out of the flooded paddies.


def _seg_0285_017__in_paddy(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.017 (in_paddy) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        in_paddy = []  # type: ignore[var-annotated]
    return _kept(locals(), ('in_paddy',))


def _seg_0285_018__e(
    *,
    e: Any = _UNBOUND,
    fc: Any = _UNBOUND,
    fields_ol: Any = _UNBOUND,
    in_paddy: Any = _UNBOUND,
    k: Any = _UNBOUND,
    ol: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    t: Any = _UNBOUND,
    vx: Any = _UNBOUND,
    vy: Any = _UNBOUND,
    yards: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.018 (e, fc, in_paddy, k) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for t in yards:
            fc = rect_corners(_struct_rect(t))
            if any(
                any(point_in_poly(px, py, ol) for px, py in fc)
                or any(point_in_poly(vx, vy, fc) for vx, vy in ol)
                or any(segments_cross(fc[e], fc[(e + 1) % 4], ol[k], ol[(k + 1) % len(ol)]) for e in range(4) for k in range(len(ol)))
                for ol in fields_ol
            ):
                in_paddy.append((round(t["x"]), round(t["y"])))
    return _kept(locals(), ('e', 'fc', 'in_paddy', 'k', 'ol', 'px', 'py', 't', 'vx', 'vy'))


def _seg_0285_019__harvest_yards_clear_of_paddies(*, check: Any = _UNBOUND, in_paddy: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.019 (harvest_yards_clear_of_paddies) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "harvest_yards_clear_of_paddies",
            not in_paddy,
            f"threshing yard footprint(s) sit IN a flooded paddy: {in_paddy[:3]} - the yard is dry ground; keep its whole footprint clear of every field outline",
        )
    return _kept(locals(), ())


# the yard abuts its OWN farmhouse (intentional, overlap-exempt) but must touch NOTHING else -
# not another farmhouse, a shop, a civic building, or a kura (parent matched by `of`). This is
# the dedicated guard the exemption would otherwise skip - a feature placed before the yard
# (a shop) OR after it (a hand-placed building) must not end up under it.


def _seg_0285_020__k(*, M: Any = _UNBOUND, k: Any = _UNBOUND, s: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.020 (k, others, s) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        others = [s for k in _OVERLAP_STRUCTS for s in M.get(k, [])] + M.get("storehouses", []) + M.get("merchant_estates", [])
    return _kept(locals(), ('k', 'others', 's'))


def _seg_0285_021__fouled(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.021 (fouled) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        fouled = []  # type: ignore[var-annotated]
    return _kept(locals(), ('fouled',))


def _seg_0285_022__fouled_1(
    *, fouled: Any = _UNBOUND, others: Any = _UNBOUND, par: Any = _UNBOUND, s: Any = _UNBOUND, scale: Any = _UNBOUND, t: Any = _UNBOUND, tc: Any = _UNBOUND, yards: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0285.022 (fouled, par, s, t) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for t in yards:
            tc = rect_corners(_struct_rect(t))
            par = (round(t["of"][0]), round(t["of"][1]))
            for s in others:
                if (round(s["x"]), round(s["y"])) == par:
                    continue
                if abs(s["x"] - t["x"]) + abs(s["y"] - t["y"]) > 140:
                    continue
                if sat_overlap(tc, rect_corners(_struct_rect(s))):
                    fouled.append((round(t["x"]), round(t["y"])))
                    break
    return _kept(locals(), ('fouled', 'par', 's', 't', 'tc'))


def _seg_0285_023__harvest_yards_clear_of_structures(*, check: Any = _UNBOUND, fouled: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.023 (harvest_yards_clear_of_structures) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check("harvest_yards_clear_of_structures", not fouled, f"threshing yard(s) overlap a building other than their own farmhouse: {fouled[:3]} - a yard abuts only its own house")
    return _kept(locals(), ())


# ATTACHED KURA STOREHOUSE: a farm's fireproof grain store is drawn as an annex on the house's back
# wall, so every one that exists must ABUT a farmhouse - never float detached in the courtyard (that
# reads as a shed nobody owns). ~30% of farms carry one (a wealth marker), so it is not REQUIRED, but
# any present must be attached. Guards the regression where a move-procedure strands the shed.


def _seg_0285_024__sheds(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.024 (sheds) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        sheds = M.get("farm_sheds", [])
    return _kept(locals(), ('sheds',))


def _seg_0285_025__farm_sheds_attached(
    *, M: Any = _UNBOUND, check: Any = _UNBOUND, h: Any = _UNBOUND, scale: Any = _UNBOUND, sd: Any = _UNBOUND, sheds: Any = _UNBOUND, stranded: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0285.025 (farm_sheds_attached) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city') and sheds and M.get("houses"):
        stranded = []
        for sd in sheds:
            if not any(within_edge_gap(sd, h, 10) for h in M["houses"]):  # 10 px of true daylight; two half-diagonals used to stand in for the two extents
                stranded.append((round(sd["x"]), round(sd["y"])))
        check(
            "farm_sheds_attached",
            not stranded,
            f"{len(stranded)} farm storehouse(s) detached from any farmhouse at {stranded[:4]} - a kura is an annex on the house's back wall; draw it WITH the house so a move cannot strand it",
        )
    return _kept(locals(), ('h', 'sd', 'stranded'))


# DOORYARD KITCHEN GARDEN (saien). Every farmstead kept a small intensive vegetable plot for
# the household's daily greens - as universal as the work yard, so EVERY farmhouse must have one
# (a firm 100%, guaranteed by making the garden integral to farmstead placement). It sits on a
# sunny SIDE (preferring the east kitchen end), NOT the north shade and NOT the south front (the
# threshing apron's ground), is SMALLER than the farmhouse, stays on DRY ground off the paddies,
# and abuts only its own house. (Why a side, not the south front: settlements.md "Dooryard gardens".)


def _seg_0285_026__gardens(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.026 (gardens) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        gardens = M.get("gardens", [])
    return _kept(locals(), ('gardens',))


def _seg_0285_027__g_without(*, gardens: Any = _UNBOUND, gd: Any = _UNBOUND, h: Any = _UNBOUND, occ_h: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.027 (g_without, gd, h) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        g_without = [(round(h["x"]), round(h["y"])) for h in occ_h if not any(gd["of"][0] == h["x"] and gd["of"][1] == h["y"] for gd in gardens)]
    return _kept(locals(), ('g_without', 'gd', 'h'))


def _seg_0285_028__gardens_present(*, check: Any = _UNBOUND, g_without: Any = _UNBOUND, occ_h: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.028 (gardens_present) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "gardens_present",
            not g_without,
            f"a {scale} farmstead kept a dooryard kitchen garden for the household's vegetables, and it "
            f"was universal: {len(g_without)} of {len(occ_h)} farmhouses have NO garden {g_without[:3]} - "
            f"every farmhouse must have one (placement makes the garden integral to the farmstead)",
        )
    return _kept(locals(), ())


def _seg_0285_029__g_oversize(*, gardens: Any = _UNBOUND, gd: Any = _UNBOUND, hmap: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.029 (g_oversize, gd) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        g_oversize = [(round(gd["x"]), round(gd["y"])) for gd in gardens if gd["w"] * gd["h"] >= hmap.get((round(gd["of"][0]), round(gd["of"][1])), 0)]
    return _kept(locals(), ('g_oversize', 'gd'))


def _seg_0285_030__gardens_smaller_than_farmhouse(*, check: Any = _UNBOUND, g_oversize: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.030 (gardens_smaller_than_farmhouse) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check("gardens_smaller_than_farmhouse", not g_oversize, f"kitchen garden(s) are not smaller than their farmhouse: {g_oversize[:3]} - the saien is a small dooryard plot, not a field")
    return _kept(locals(), ())


def _seg_0285_031__g_shady(*, gardens: Any = _UNBOUND, gd: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.031 (g_shady, gd) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        g_shady = [(round(gd["x"]), round(gd["y"])) for gd in gardens if gd["y"] < gd["of"][1] - 5]
    return _kept(locals(), ('g_shady', 'gd'))


def _seg_0285_032__gardens_on_sunny_side(*, check: Any = _UNBOUND, g_shady: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.032 (gardens_on_sunny_side) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "gardens_on_sunny_side",
            not g_shady,
            f"kitchen garden(s) sit on the shady NORTH/back side of their farmhouse: {g_shady[:3]} - the saien belongs on a SUNNY side (the east kitchen end, or west), never the cold north back",
        )
    return _kept(locals(), ())


def _seg_0285_033__g_in_paddy(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.033 (g_in_paddy) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        g_in_paddy = []  # type: ignore[var-annotated]
    return _kept(locals(), ('g_in_paddy',))


def _seg_0285_034__e_1(
    *,
    e: Any = _UNBOUND,
    fc: Any = _UNBOUND,
    fields_ol: Any = _UNBOUND,
    g_in_paddy: Any = _UNBOUND,
    gardens: Any = _UNBOUND,
    gd: Any = _UNBOUND,
    k: Any = _UNBOUND,
    ol: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    vx: Any = _UNBOUND,
    vy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.034 (e, fc, g_in_paddy, gd) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for gd in gardens:
            fc = rect_corners(_struct_rect(gd))
            if any(
                any(point_in_poly(px, py, ol) for px, py in fc)
                or any(point_in_poly(vx, vy, fc) for vx, vy in ol)
                or any(segments_cross(fc[e], fc[(e + 1) % 4], ol[k], ol[(k + 1) % len(ol)]) for e in range(4) for k in range(len(ol)))
                for ol in fields_ol
            ):
                g_in_paddy.append((round(gd["x"]), round(gd["y"])))
    return _kept(locals(), ('e', 'fc', 'g_in_paddy', 'gd', 'k', 'ol', 'px', 'py', 'vx', 'vy'))


def _seg_0285_035__gardens_clear_of_paddies(*, check: Any = _UNBOUND, g_in_paddy: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.035 (gardens_clear_of_paddies) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "gardens_clear_of_paddies",
            not g_in_paddy,
            f"kitchen garden footprint(s) sit IN a flooded paddy: {g_in_paddy[:3]} - the saien is dry ground; keep its whole footprint clear of every field outline",
        )
    return _kept(locals(), ())


# ... and off the IRRIGATION LINES too: the feeder CHANNELS, the in-field/drain DITCHES, and any
# STREAM. A raised-bed vegetable plot cannot sit in a running ditch; `gardens_clear_of_paddies`
# covers the flooded basin, but a feeder channel or the drain ditch threads the DRY village margin
# where the gardens are, so test each garden footprint against every water polyline (its own
# half-width + a little). Same full-footprint test used for structures vs a channel/stream.


def _seg_0285_036__c(*, M: Any = _UNBOUND, c: Any = _UNBOUND, d: Any = _UNBOUND, scale: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.036 (c, d, st, waterlines) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        waterlines = (
            [(c["poly"], c.get("w", 2.5) / 2 + 3) for c in M.get("channels", [])]
            + [(d["poly"], d.get("w", 7) / 2 + 3) for d in M.get("field_ditches", [])]
            + [(st["poly"], st.get("w", 9) / 2 + 3) for st in M.get("streams", [])]
        )
    return _kept(locals(), ('c', 'd', 'st', 'waterlines'))


def _seg_0285_037__g_on_water(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.037 (g_on_water) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        g_on_water = []  # type: ignore[var-annotated]
    return _kept(locals(), ('g_on_water',))


def _seg_0285_038__cx(
    *,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    e: Any = _UNBOUND,
    g_on_water: Any = _UNBOUND,
    gardens: Any = _UNBOUND,
    gc: Any = _UNBOUND,
    gd: Any = _UNBOUND,
    k: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    waterlines: Any = _UNBOUND,
    whw: Any = _UNBOUND,
    wp: Any = _UNBOUND,
    wx: Any = _UNBOUND,
    wy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.038 (cx, cy, e, g_on_water) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for gd in gardens:
            gc = rect_corners(_struct_rect(gd))
            for wp, whw in waterlines:
                if (
                    any(seg_dist(cx, cy, wp[k], wp[k + 1]) < whw for cx, cy in gc for k in range(len(wp) - 1))
                    or any(point_in_poly(wx, wy, gc) for wx, wy in wp)
                    or any(segments_cross(wp[k], wp[k + 1], gc[e], gc[(e + 1) % 4]) for k in range(len(wp) - 1) for e in range(4))
                ):
                    g_on_water.append((round(gd["x"]), round(gd["y"])))
                    break
    return _kept(locals(), ('cx', 'cy', 'e', 'g_on_water', 'gc', 'gd', 'k', 'whw', 'wp', 'wx', 'wy'))


def _seg_0285_039__gardens_clear_of_channels(*, check: Any = _UNBOUND, g_on_water: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.039 (gardens_clear_of_channels) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "gardens_clear_of_channels",
            not g_on_water,
            f"kitchen garden(s) overlap an irrigation channel/ditch: {g_on_water[:3]} - a raised-bed saien sits on dry ground, never in a running feeder channel, field ditch, or stream",
        )
    return _kept(locals(), ())


def _seg_0285_040__g_fouled(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.040 (g_fouled) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        g_fouled = []  # type: ignore[var-annotated]
    return _kept(locals(), ('g_fouled',))


def _seg_0285_041__g_fouled_1(
    *, g_fouled: Any = _UNBOUND, gardens: Any = _UNBOUND, gc: Any = _UNBOUND, gd: Any = _UNBOUND, others: Any = _UNBOUND, par: Any = _UNBOUND, s: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0285.041 (g_fouled, gc, gd, par) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for gd in gardens:
            gc = rect_corners(_struct_rect(gd))
            par = (round(gd["of"][0]), round(gd["of"][1]))
            for s in others:
                if (round(s["x"]), round(s["y"])) == par:
                    continue
                if abs(s["x"] - gd["x"]) + abs(s["y"] - gd["y"]) > 140:
                    continue
                if sat_overlap(gc, rect_corners(_struct_rect(s))):
                    g_fouled.append((round(gd["x"]), round(gd["y"])))
                    break
    return _kept(locals(), ('g_fouled', 'gc', 'gd', 'par', 's'))


def _seg_0285_042__gardens_clear_of_structures(*, check: Any = _UNBOUND, g_fouled: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.042 (gardens_clear_of_structures) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check("gardens_clear_of_structures", not g_fouled, f"kitchen garden(s) overlap a building other than their own farmhouse: {g_fouled[:3]} - a garden abuts only its own house")
    return _kept(locals(), ())


# the garden and the farmhouse's STOREHOUSE/shed must never overlap - the shed sits on a wall the
# garden does not use (west for a dispersed farm, the shaded north for a nucleated one). The shed is
# a recorded annex (M['farm_sheds']), so read its actual footprint straight from there.


def _seg_0285_043__sheds_1(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.043 (sheds) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        sheds = M.get("farm_sheds", [])
    return _kept(locals(), ('sheds',))


def _seg_0285_044__g_on_shed(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.044 (g_on_shed) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        g_on_shed = []  # type: ignore[var-annotated]
    return _kept(locals(), ('g_on_shed',))


def _seg_0285_045__g_on_shed_1(
    *, g_on_shed: Any = _UNBOUND, gardens: Any = _UNBOUND, gc: Any = _UNBOUND, gd: Any = _UNBOUND, scale: Any = _UNBOUND, sd: Any = _UNBOUND, sheds: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0285.045 (g_on_shed, gc, gd, sd) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for gd in gardens:
            gc = rect_corners(_struct_rect(gd))
            for sd in sheds:
                if abs(sd["x"] - gd["x"]) + abs(sd["y"] - gd["y"]) > 120:
                    continue
                if sat_overlap(gc, rect_corners(sd)):
                    g_on_shed.append((round(gd["x"]), round(gd["y"])))
                    break
    return _kept(locals(), ('g_on_shed', 'gc', 'gd', 'sd'))


def _seg_0285_046__gardens_clear_of_sheds(*, check: Any = _UNBOUND, g_on_shed: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.046 (gardens_clear_of_sheds) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "gardens_clear_of_sheds",
            not g_on_shed,
            f"kitchen garden(s) overlap a farmhouse's storehouse/shed: {g_on_shed[:3]} - the shed sits on the "
            f"house's WEST side and the garden on a sunny (east-preferred) side, so the two must never collide",
        )
    return _kept(locals(), ())


# A dooryard bed and a threshing yard were HAND-worked plots bent to paths and soil, not surveyed
# rectangles - the generator draws each as a slightly-irregular 4-sided quad (a garden more irregular,
# a swept work yard near-square). Validate the SHAPE it records: every garden/yard with a `poly` must
# carry exactly 4 vertices, be non-degenerate (real area), and stay INSCRIBED in its recorded w x h
# bounds (the jitter only pulls corners INWARD, so a poly poking outside its rect means the overlap
# checks - which use that rect - were cleared against the wrong footprint). WHY quads: settlements.md
# "Dooryard kitchen gardens" / "Threshing yards" (irregular-plot grounding).


def _seg_0285_047__bad_quad(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.047 (bad_quad) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        bad_quad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('bad_quad',))


def _seg_0285_048__bad_quad_1(
    *,
    bad_quad: Any = _UNBOUND,
    gardens: Any = _UNBOUND,
    hh: Any = _UNBOUND,
    hw: Any = _UNBOUND,
    inside: Any = _UNBOUND,
    pg: Any = _UNBOUND,
    pl: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    yards: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.048 (bad_quad, hh, hw, inside) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for pl in gardens + yards:
            pg = pl.get("poly")
            if pg is None:
                continue  # legacy rect-only record (dispersed maps predate poly)
            hw, hh = pl["w"] / 2 + 0.6, pl["h"] / 2 + 0.6  # small tolerance for rounding
            inside = all(abs(px - pl["x"]) <= hw and abs(py - pl["y"]) <= hh for px, py in pg)
            if len(pg) != 4 or poly_area(pg) < 0.20 * pl["w"] * pl["h"] or not inside:
                bad_quad.append((round(pl["x"]), round(pl["y"])))
    return _kept(locals(), ('bad_quad', 'hh', 'hw', 'inside', 'pg', 'pl', 'px', 'py'))


def _seg_0285_049__garden_plots_are_quads(*, bad_quad: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.049 (garden_plots_are_quads) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "garden_plots_are_quads",
            not bad_quad,
            f"garden/yard footprint(s) are not valid inscribed 4-gons: {bad_quad[:3]} - each is a slightly-irregular quadrilateral (4 vertices, real area) that stays within its reserved w x h rect",
        )
    return _kept(locals(), ())


# GARDEN AREA is held to a HISTORICAL band. Unlike the house/yard (drawn oversized against the
# fields for legibility), a dooryard kitchen garden at 1 px = 2 ft is near its TRUE size, so its area
# is a real quantity we can check against the ground a household could hand-work. The saien is the
# small intensive daily-greens bed by the kitchen (the bulk vegetable growing was out in the hatake
# dry fields, not here): historically a few tsubo up to ~1.4 se - roughly 10-140 m^2 (1 tsubo = 3.31
# m^2; 1 se = 30 tsubo ~ 99 m^2). We sum ALL of a household's garden beds (a fragmented plot is still
# one household's garden) and require the TOTAL in that band. WHY the numbers: settlements.md "Dooryard
# kitchen gardens" (area grounding). Scale override via meta.ft_per_px for any non-standard map.


def _seg_0285_050__ft_per_px(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.050 (ft_per_px) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        ft_per_px = float(meta.get("ftpx") or meta.get("ft_per_px") or 2.0)  # the map's real scale (village 2, hamlet 1)
    return _kept(locals(), ('ft_per_px',))


def _seg_0285_051__m2_per_px2(*, ft_per_px: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.051 (m2_per_px2) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        m2_per_px2 = (ft_per_px * 0.3048) ** 2  # ft/px -> m per px, squared -> m^2 per px^2
    return _kept(locals(), ('m2_per_px2',))


def _seg_0285_052__GARDEN_M2_MAX(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.052 (GARDEN_M2_MAX, GARDEN_M2_MIN) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        GARDEN_M2_MIN, GARDEN_M2_MAX = 10.0, 140.0
    return _kept(locals(), ('GARDEN_M2_MAX', 'GARDEN_M2_MIN'))


def _seg_0285_053__by_house(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.053 (by_house) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        by_house: dict[tuple[int, int], float] = {}  # type: ignore[no-redef,unused-ignore]
    return _kept(locals(), ('by_house',))


def _seg_0285_054__a_px(
    *, a_px: Any = _UNBOUND, by_house: Any = _UNBOUND, gardens: Any = _UNBOUND, gd: Any = _UNBOUND, key: Any = _UNBOUND, pg: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0285.054 (a_px, by_house, gd, key) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for gd in gardens:
            pg = gd.get("poly")
            a_px = poly_area(pg) if pg else gd["w"] * gd["h"]
            key = (round(gd["of"][0]), round(gd["of"][1]))
            by_house[key] = by_house.get(key, 0.0) + a_px
    return _kept(locals(), ('a_px', 'by_house', 'gd', 'key', 'pg'))


def _seg_0285_055__a_px_1(
    *,
    GARDEN_M2_MAX: Any = _UNBOUND,
    GARDEN_M2_MIN: Any = _UNBOUND,
    a_px: Any = _UNBOUND,
    by_house: Any = _UNBOUND,
    hx: Any = _UNBOUND,
    hy: Any = _UNBOUND,
    m2_per_px2: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.055 (a_px, g_area_bad, hx, hy) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        g_area_bad = [(hx, hy, round(a_px * m2_per_px2)) for (hx, hy), a_px in by_house.items() if not (GARDEN_M2_MIN <= a_px * m2_per_px2 <= GARDEN_M2_MAX)]
    return _kept(locals(), ('a_px', 'g_area_bad', 'hx', 'hy'))


def _seg_0285_056__garden_area_within_norms(
    *, GARDEN_M2_MAX: Any = _UNBOUND, GARDEN_M2_MIN: Any = _UNBOUND, check: Any = _UNBOUND, g_area_bad: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0285.056 (garden_area_within_norms) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "garden_area_within_norms",
            not g_area_bad,
            f"household kitchen-garden total area out of the historical band "
            f"[{GARDEN_M2_MIN:.0f}-{GARDEN_M2_MAX:.0f} m^2]: {g_area_bad[:3]} (x, y, m^2) - a saien is the small "
            f"intensive daily-greens bed by the kitchen, ~a few tsubo up to ~1.4 se; bigger reads as a field, "
            f"tinier as no garden at all",
        )
    return _kept(locals(), ())


# HOMESTEAD GROVE (yashikirin) - the farmhouse windbreak. A dense L-BELT of shelter trees on the
# WINDWARD side(s) of the house (one record per belt ARM), blocking the cold prevailing wind while
# leaving the SUNNY lee open. Default windward NW: the East Asian winter monsoon blows NW across
# China and Japan alike, so N+W is windward, S/E the sheltered sunny side - a map keys it off its
# own geography with meta(windward=...). The grove is NEAR-UNIVERSAL (meta.grove_prevalence) and
# the LARGEST homestead appurtenance - bigger than the house. We gate GEOMETRY per arm (windward,
# off the paddy, off other buildings), the typical grove's SCALE (groves_are_substantial), a
# presence FLOOR scaled to the knob, and (city) that NO intramural farm carries one. WHY (the ~30-40
# tree stand, the windward rule, the firewood/timber/bamboo it gave): settlements.md "Homestead groves".


def _seg_0285_057__groves(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.057 (groves) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        groves = M.get("groves", [])
    return _kept(locals(), ('groves',))


def _seg_0285_058__grove_of(*, groves: Any = _UNBOUND, gv: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.058 (grove_of, gv) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        grove_of = {(round(gv["of"][0]), round(gv["of"][1])) for gv in groves}  # distinct farms with a grove
    return _kept(locals(), ('grove_of', 'gv'))


def _seg_0285_059__WINDV(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.059 (WINDV) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        WINDV = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0), "NW": (-1, -1), "NE": (1, -1), "SW": (-1, 1), "SE": (1, 1)}
    return _kept(locals(), ('WINDV',))


def _seg_0285_060__windward(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.060 (windward) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        windward = str(meta.get("windward", "NW")).upper().strip()
    return _kept(locals(), ('windward',))


def _seg_0285_061__wvx(*, WINDV: Any = _UNBOUND, scale: Any = _UNBOUND, windward: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.061 (wvx, wvy) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        wvx, wvy = WINDV.get(windward, (-1, -1))
    return _kept(locals(), ('wvx', 'wvy'))


def _seg_0285_062__g_lee(*, groves: Any = _UNBOUND, gv: Any = _UNBOUND, scale: Any = _UNBOUND, wvx: Any = _UNBOUND, wvy: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.062 (g_lee, gv) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        g_lee = [(round(gv["x"]), round(gv["y"])) for gv in groves if (gv["x"] - gv["of"][0]) * wvx + (gv["y"] - gv["of"][1]) * wvy <= 0]
    return _kept(locals(), ('g_lee', 'gv'))


def _seg_0285_063__groves_on_windward_side(*, check: Any = _UNBOUND, g_lee: Any = _UNBOUND, scale: Any = _UNBOUND, windward: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.063 (groves_on_windward_side) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "groves_on_windward_side",
            not g_lee,
            f"homestead grove(s) sit on the LEE/sunny side of their farmhouse, not the windward {windward}: "
            f"{g_lee[:3]} - a yashikirin shelters the windward wall (default N/W) and leaves the sunny lee open",
        )
    return _kept(locals(), ())


def _seg_0285_064__g_in_paddy_1(*, fields_ol: Any = _UNBOUND, groves: Any = _UNBOUND, gv: Any = _UNBOUND, ol: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.064 (g_in_paddy, gv, ol) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        g_in_paddy = [(round(gv["x"]), round(gv["y"])) for gv in groves if any(point_in_poly(gv["x"], gv["y"], ol) for ol in fields_ol)]
    return _kept(locals(), ('g_in_paddy', 'gv', 'ol'))


def _seg_0285_065__groves_clear_of_paddies(*, check: Any = _UNBOUND, g_in_paddy: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.065 (groves_clear_of_paddies) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "groves_clear_of_paddies",
            not g_in_paddy,
            f"homestead grove(s) sit squarely IN a flooded paddy (center over water): {g_in_paddy[:3]} - the "
            f"windbreak HUGS the bund (abutting/overlapping the field edge is correct) but must not be planted "
            f"out in the paddy itself",
        )
    return _kept(locals(), ())


# TWO FARMHOUSES MUST SHED SEPARATELY. A minka carries a steep kayabuki thatch (45 deg or steeper -
# thatch has to shed hard or it rots), so each roof throws its own drip line, and two of them set a
# couple of feet apart pool their runoff against each other's walls. `research/buildings.md` already
# records the principle for a building standing against a compound wall - "rear wall a foot or two
# off it so the two roofs shed separately" - and the same physics governs two houses.
#
# THE DEFECT IT CATCHES, and why a rule was needed at all (settlement-review on Mizuguchi,
# 2026-08-17): a re-pack flipped one house's rake from -4.0 to +4.4 deg so a neighbouring pair
# diverged instead of running parallel, and their raked-corner gap fell 3.6 -> 2.0 ft. At 1 px = 1 ft
# that is two pixels between two dark roof strokes; at fit zoom they merge and read as ONE long
# building rather than two households. Nothing caught it, because house-to-house separation had no
# rule at all - `no_structure_overlaps` only fires at zero.
#
# THE NUMBER, and its headroom. 8 ft: two drip lines plus a footpath between them, which is the
# least ground that reads as a gap rather than a seam. It is deliberately far below what the pool
# actually does - the scripted hamlets sit at 23-29 ft minimum - so this fires on a merge, never on
# a tight-but-honest nucleus. A denser tier may legitimately approach it; it may not cross it.
#
# IN FEET, NOT PIXELS. The rule is a physical clearance, so it converts through `meta.ftpx` rather
# than being a raw px literal that would silently mean 8 ft at a hamlet and 16 ft at a village.
# GAP VERDICT family: `within_edge_gap` on real rotated corners, never centers (dev/placement.md).


def _seg_0606__farmhouses_shed_separately(*, M: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0606 (farmhouses_shed_separately) - added 2026-08-17, see the note above.

    Numbered past the legacy range (the number is a LABEL; the registry tuple is the execution
    order). It binds only M/check/scale, all established long before any homestead segment, so its
    position carries no dependency."""
    if scale in ('town', 'village', 'hamlet'):
        _fh = [h for h in M.get("houses", []) if h.get("kind") != "abandoned"]
        _lim = FARMHOUSE_EAVE_GAP_FT / float(M["meta"].get("ftpx", 1) or 1)
        _merged = []
        for _i in range(len(_fh)):
            for _j in range(_i + 1, len(_fh)):
                if within_edge_gap(_fh[_i], _fh[_j], _lim):
                    _merged.append((round(_fh[_i]["x"]), round(_fh[_i]["y"])))
        check(
            "farmhouses_shed_separately",
            not _merged,
            f"{len(_merged)} farmhouse pair(s) stand closer than {FARMHOUSE_EAVE_GAP_FT:.0f} ft wall to wall, at {_merged[:4]} - "
            f"two steep thatched roofs need their own drip lines and a way between them; at this range the pair merges into one long building on the sheet",
        )
    return _kept(locals(), ())
