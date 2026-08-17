"""Gate segments (city governor and quarters; keys 0563_195-0563_251) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from l7r.diagram.settlement import sat_overlap

from .common_01_geometry import (
    Poly,
    _struct_rect,
    edge_gap,
    point_in_poly,
    rect_corners,
    seg_dist,
    seg_intersect,
    segments_cross,
    unit_dir,
)
from .common_02_overlap_policy import _ward_interior, edge_dist, footprint_on_line
from .common_03_capacity import _UNBOUND, _kept


def _seg_0563_195__cc(
    *,
    GDIR: Any = _UNBOUND,
    cc: Any = _UNBOUND,
    civics: Any = _UNBOUND,
    compounds: Any = _UNBOUND,
    g: Any = _UNBOUND,
    gate_bad: Any = _UNBOUND,
    i: Any = _UNBOUND,
    j: Any = _UNBOUND,
    mest: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    ox: Any = _UNBOUND,
    oy: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    tcx: Any = _UNBOUND,
    tcy: Any = _UNBOUND,
    th: Any = _UNBOUND,
    thr: Any = _UNBOUND,
    tw: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.195 (cc, g, gate_bad, i) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for i in range(len(mest)):
            g = mest[i].get("gate")
            if not g:
                continue
            ox, oy = GDIR.get(mest[i].get("gate_dir", "south"), (0, 1))
            tcx, tcy = g[0] + ox * 11, g[1] + oy * 11  # a threshold box just OUTSIDE the gate
            tw, th = (24, 22) if ox == 0 else (22, 24)
            thr = [(tcx - tw / 2, tcy - th / 2), (tcx + tw / 2, tcy - th / 2), (tcx + tw / 2, tcy + th / 2), (tcx - tw / 2, tcy + th / 2)]
            for j, cc in enumerate(compounds):
                if j == len(civics) + i:  # skip the estate's OWN court
                    continue
                if sat_overlap(thr, cc):
                    gate_bad.append((round(mest[i]["x"]), round(mest[i]["y"])))
                    break
    return _kept(locals(), ('cc', 'g', 'gate_bad', 'i', 'j', 'ox', 'oy', 'tcx', 'tcy', 'th', 'thr', 'tw'))


def _seg_0563_196__city_merchant_estate_gate_clear(*, check: Any = _UNBOUND, gate_bad: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.196 (city_merchant_estate_gate_clear) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_merchant_estate_gate_clear",
            not gate_bad,
            f"walled merchant estate gate(s) opening INTO a building (a temple/compound/another estate) - point the gate at open ground: {gate_bad}",
        )
    return _kept(locals(), ())


# the government compounds (governor's mansion + ministry offices) sit inside, clear of the
# barriers. (The governor's YAMEN is legitimately a large walled compound - a whole city block,
# dozens of buildings inside, drawn here as walls-only - so its size is fine; it must just not
# cross the rampart.)


def _seg_0563_197__gov(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.197 (gov) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        gov = M.get("governor_mansion")
    return _kept(locals(), ('gov',))


def _seg_0563_198__gov_items(*, M: Any = _UNBOUND, gov: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.198 (gov_items) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        gov_items = ([gov] if gov else []) + M.get("ministries", [])
    return _kept(locals(), ('gov_items',))


def _seg_0563_199__g_5(
    *, g: Any = _UNBOUND, gov_items: Any = _UNBOUND, meta: Any = _UNBOUND, moat: Any = _UNBOUND, rect_corners_xywh: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.199 (g, gov_bad) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        gov_bad = [
            g.get("name") or g.get("label") or "governor's mansion"
            for g in gov_items
            if footprint_on_line(rect_corners_xywh(g, 0), w, 9) or (moat and footprint_on_line(rect_corners_xywh(g, 0), moat, 13))
        ]
    return _kept(locals(), ('g', 'gov_bad'))


def _seg_0563_200__city_government_clear_of_wall_moat(*, check: Any = _UNBOUND, gov_bad: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.200 (city_government_clear_of_wall_moat) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_government_clear_of_wall_moat", not gov_bad, f"government compound(s) overlapping the wall or moat: {gov_bad}")
    return _kept(locals(), ())


# the governor's mansion is the GRANDEST compound - a city-block yamen, at least as large
# as any samurai estate and several times any single ministry office


def _seg_0563_201__city_governor_mansion_large(
    *,
    M: Any = _UNBOUND,
    _floor: Any = _UNBOUND,
    big_other: Any = _UNBOUND,
    check: Any = _UNBOUND,
    est_out: Any = _UNBOUND,
    far_min: Any = _UNBOUND,
    ga: Any = _UNBOUND,
    gov: Any = _UNBOUND,
    m: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    mn: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.201 (city_governor_mansion_large, city_ministries_cluster_at_government) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and gov:
        ga = gov["w"] * gov["h"]
        # the absolute floor is REAL area (~1.4 ha): 24000px2 was tuned at the pre-ladder
        # ~2.55 ft/px grain and would demand a 2 ha yamen at 3 ft/px
        _floor = round(24000 * (2.55 / meta.get("ftpx", 2.55)) ** 2)
        big_other = max([mn["w"] * mn["h"] for mn in est_out] + [3 * m["w"] * m["h"] for m in M.get("ministries", [])] + [_floor])
        check(
            "city_governor_mansion_large",
            ga >= big_other,
            f"the governor's mansion ({ga:.0f}px2) must be the grandest compound - a city-block yamen at least as large as any estate and >= 3x any ministry (need >= {big_other:.0f})",
        )
        # the ministries cluster around the yamen (the government district), threading into the
        # samurai quarter; only the Ministry of Rites sits apart, with the temples it oversees
        far_min = [m.get("name") for m in M.get("ministries", []) if "rites" not in (m.get("name") or "").lower() and math.hypot(m["x"] - gov["x"], m["y"] - gov["y"]) > 480]
        check(
            "city_ministries_cluster_at_government",
            not far_min,
            f"ministry office(s) far from the governor's mansion - the ministries belong around the yamen / in the samurai quarter (only Rites sits with the temples): {far_min}",
        )
    return _kept(locals(), ('_floor', 'big_other', 'far_min', 'ga', 'm', 'mn'))


# a planned city's government offices FRONT its streets - the yamen sits where the main
# streets cross and the bureaus line the avenues around it (Chinese official street /
# jokamachi grid), so every ministry must sit on a street, not float mid-block


def _seg_0563_202__r23(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, r23: Any = _UNBOUND, scale: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.202 (r23, st, st_pts) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        st_pts = (
            [st["pts"] for st in M.get("town_streets", [])] + ([M["road"]] if M.get("road") else []) + [r23["pts"] for r23 in M.get("roads", [])]
        )  # the ote-suji IS the avenue (021: capital ministries front the road)
    return _kept(locals(), ('r23', 'st', 'st_pts'))


def _seg_0563_203__i_2(*, M: Any = _UNBOUND, i: Any = _UNBOUND, m: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, sp: Any = _UNBOUND, st_pts: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.203 (i, m, no_front, sp) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        no_front = [m.get("name") for m in M.get("ministries", []) if not any(seg_dist(m["x"], m["y"], sp[i], sp[i + 1]) < 85 for sp in st_pts for i in range(len(sp) - 1))]
    return _kept(locals(), ('i', 'm', 'no_front', 'sp'))


def _seg_0563_204__city_ministries_front_a_street(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, no_front: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.204 (city_ministries_front_a_street) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_ministries_front_a_street",
            not no_front,
            f"ministry office(s) not fronting any city street - government offices line the avenues around the yamen, they do not float mid-block: {no_front}",
        )
    return _kept(locals(), ())


# a walled city SEALS its samurai/government quarter off the commoner streets with kido
# (wooden ward gates), not internal ramparts: full walled wards are a great-capital / Tang
# feature, over-scaled here, so a provincial city gates the quarter's street entries instead


def _seg_0563_205__i_3(*, M: Any = _UNBOUND, i: Any = _UNBOUND, k: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.205 (i, k, on_st_kido, st) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        on_st_kido = [
            k
            for k in M.get("kido", [])
            if any(seg_dist(k["x"], k["y"], st["pts"][i], st["pts"][i + 1]) < st.get("w", 18) / 2 + 8 for st in M.get("town_streets", []) for i in range(len(st["pts"]) - 1))
        ]
    return _kept(locals(), ('i', 'k', 'on_st_kido', 'st'))


def _seg_0563_206__gated(*, gov: Any = _UNBOUND, k: Any = _UNBOUND, meta: Any = _UNBOUND, on_st_kido: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.206 (gated, k) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        gated = [k for k in on_st_kido if gov and math.hypot(k["x"] - gov["x"], k["y"] - gov["y"]) < 480]
    return _kept(locals(), ('gated', 'k'))


# CAPITAL-INVERTED (021): the capital adopts the ward MESH (kido at machi mouths;
# yashiki walls seal the samurai streets). Either form is the interior-gate doctrine,
# which meta(ward_gates=False) turns off for a city that does not use it - there is
# then nothing to seal with (GM 2026-08-10).


def _seg_0563_207__city_samurai_quarter_gated(*, URBAN: Any = _UNBOUND, check: Any = _UNBOUND, gated: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.207 (city_samurai_quarter_gated) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):  # noqa: SIM102
            if URBAN and meta.get("ward_gates", True):
                check(
                    "city_samurai_quarter_gated",
                    len(gated) >= 2,
                    f"a walled city seals its samurai/government quarter with kido ward gates across the streets entering it (s.kido), not walls - {len(gated)} gate(s) bar the quarter's street entries near the yamen, need >= 2",
                )
    return _kept(locals(), ())


# ...and that ward must be SEALED: a continuous fence whose ends abut the city wall, that
# a street pierces ONLY at a kido gate. Otherwise the gates can just be walked around, and
# the road network connects samurai to commoner with no gate between them.


def _seg_0563_208__wards(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.208 (wards) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        wards = M.get("wards", [])
    return _kept(locals(), ('wards',))


def _seg_0563_209__kido(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.209 (kido) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        kido = M.get("kido", [])
    return _kept(locals(), ('kido',))


def _seg_0563_210__a_1(*, M: Any = _UNBOUND, a: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.210 (a, netlines, st) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        netlines = [st["pts"] for st in M.get("town_streets", [])] + ([M["road"]] if M.get("road") else []) + [a["pts"] for a in M.get("alleys", [])] + ([M["ring_road"]] if M.get("ring_road") else [])
    return _kept(locals(), ('a', 'netlines', 'st'))


def _seg_0563_211__bad_cross(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.211 (bad_cross, open_end) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        bad_cross, open_end = [], []  # type: ignore[var-annotated]
    return _kept(locals(), ('bad_cross', 'open_end'))


def _seg_0563_212__bad_cross_1(
    *,
    bad_cross: Any = _UNBOUND,
    bnd: Any = _UNBOUND,
    e: Any = _UNBOUND,
    g: Any = _UNBOUND,
    i: Any = _UNBOUND,
    ip: Any = _UNBOUND,
    ki: Any = _UNBOUND,
    kido: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    netlines: Any = _UNBOUND,
    open_end: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    sp: Any = _UNBOUND,
    w: Any = _UNBOUND,
    wards: Any = _UNBOUND,
    wd: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.212 (bad_cross, bnd, e, g) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for wd in wards:
            bnd = wd["boundary"]
            for sp in netlines:
                for i in range(len(sp) - 1):
                    for ki in range(len(bnd) - 1):
                        if segments_cross(sp[i], sp[i + 1], bnd[ki], bnd[ki + 1]):
                            ip = seg_intersect(sp[i], sp[i + 1], bnd[ki], bnd[ki + 1])
                            if ip and not any(math.hypot(g["x"] - ip[0], g["y"] - ip[1]) < 32 for g in kido):
                                bad_cross.append((round(ip[0]), round(ip[1])))
            for e in (bnd[0], bnd[-1]):
                if len(w) >= 3 and edge_dist(e[0], e[1], w) > 45:
                    open_end.append((round(e[0]), round(e[1])))
    return _kept(locals(), ('bad_cross', 'bnd', 'e', 'g', 'i', 'ip', 'ki', 'open_end', 'sp', 'wd'))


# ...same mesh doctrine, same knob


def _seg_0563_213__city_samurai_ward_sealed(
    *, URBAN: Any = _UNBOUND, bad_cross: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, open_end: Any = _UNBOUND, scale: Any = _UNBOUND, wards: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.213 (city_samurai_ward_sealed) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):  # noqa: SIM102
            if URBAN and meta.get("ward_gates", True):
                check(
                    "city_samurai_ward_sealed",
                    bool(wards) and not bad_cross and not open_end,
                    f"the samurai/government ward is not SEALED (s.ward): wards={len(wards)}, ungated street crossings={bad_cross}, fence ends not meeting the wall={open_end} - a kido gate can be walked around unless the fence is continuous, ends at the wall, and a street pierces it only at a gate",
                )
    return _kept(locals(), ())


# ...and the fence ends must actually TOUCH the wall - a gap (even a small one, which the
# coarse 45px seal tolerance lets slide) means commoners can simply walk AROUND the end of
# the fence. The end must abut the rampart within ~10px (about the wall's own half-width).


def _seg_0563_214__fence_gap(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.214 (fence_gap) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        fence_gap = []  # type: ignore[var-annotated]
    return _kept(locals(), ('fence_gap',))


def _seg_0563_215__bnd(
    *,
    bnd: Any = _UNBOUND,
    e: Any = _UNBOUND,
    fence_gap: Any = _UNBOUND,
    g: Any = _UNBOUND,
    gates: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    w: Any = _UNBOUND,
    wards: Any = _UNBOUND,
    wd: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.215 (bnd, e, fence_gap, g) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for wd in wards:
            bnd = wd["boundary"]
            for e in (bnd[0], bnd[-1]):
                if len(w) >= 3 and edge_dist(e[0], e[1], w) > 10:
                    fence_gap.append((round(e[0]), round(e[1]), "gap to the wall"))
                elif any(math.hypot(e[0] - g[0], e[1] - g[1]) < 45 for g in gates):
                    fence_gap.append((round(e[0]), round(e[1]), "lands in a gate OPENING (the wall is cut there, so the fence meets nothing)"))
    return _kept(locals(), ('bnd', 'e', 'fence_gap', 'g', 'wd'))


def _seg_0563_216__city_ward_fence_meets_wall(*, check: Any = _UNBOUND, fence_gap: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.216 (city_ward_fence_meets_wall) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_ward_fence_meets_wall",
            not fence_gap,
            f"ward-fence end(s) not abutting SOLID city wall (commoners could walk around the fence end): {fence_gap} - extend the fence to solid rampart, clear of any gate opening",
        )
    return _kept(locals(), ())


# THE FENCE SEALS COMMONERS OUT - so nobody it seals out may LIVE inside it (GM
# 2026-08-02, on Minami: 2 laborer houses in the middle of the samurai neighborhood
# and a merchant row hugging the inside of the west fence, leaked in by whole-interior
# top-up sweeps whose rectangles overlap the ward). Historical grounding: an Edo-era
# jokamachi zoned samurai and chonin ground apart as a matter of LAW (bukechi vs
# chonin-chi), and a Chinese provincial seat likewise kept commerce off the yamen
# quarter - a laborer terrace between two samurai houses inside the palisade is not
# variety, it contradicts the fence around it. Only samurai dwellings, their live-in
# domestics (servant - the gens interleave them deliberately) and government ground
# belong inside. monk_house is deliberately NOT barred: a temple may stand inside the
# ward (Tango's Bishamon precinct - the warrior fortune beside the garrison quarter)
# and its clergy row belongs with its temple, held there by the temple-neighborhood
# checks. Classification family: CENTER-tested on purpose (a building belongs to ONE
# ward; see "Centers, footprints, and aggregates" in the skill CLAUDE.md).


def _seg_0563_217__barred(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.217 (barred) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        barred = ("laborer", "laborer_large", "merchant", "merchant_house", "merchant_large", "burakumin", "shop", "inn")
    return _kept(locals(), ('barred',))


def _seg_0563_218__commoner_in(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.218 (commoner_in) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        commoner_in = []  # type: ignore[var-annotated]
    return _kept(locals(), ('commoner_in',))


def _seg_0563_219__b_10(
    *,
    M: Any = _UNBOUND,
    b: Any = _UNBOUND,
    barred: Any = _UNBOUND,
    commoner_in: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    region: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    w: Any = _UNBOUND,
    wards: Any = _UNBOUND,
    wd: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.219 (b, commoner_in, region, wd) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for wd in wards:
            if wd.get("name") != "samurai":
                continue
            region = _ward_interior(wd["boundary"], w)
            for b in M.get("buildings", []):
                if region and b.get("kind") in barred and point_in_poly(b["x"], b["y"], region):
                    commoner_in.append((b["kind"], round(b["x"]), round(b["y"])))
    return _kept(locals(), ('b', 'commoner_in', 'region', 'wd'))


# ...and the residents who ARE admitted must be housed the way the ward houses them.
# A samurai household's domestics lived in the perimeter nagaya that forms the plot's
# street boundary, in the nagayamon gate rooms, or in nando off the kitchen - never in
# a freestanding house in the buke-chi; a Chinese elite compound puts them in the
# daozuofang, the south row whose blank back IS the street wall. Ranks of small uniform
# dwellings are real, but they are ashigaru kumi-yashiki on the town FRINGE. So every
# servant inside the fence must carry `of` (its master's house), ABUT that house, and
# be a RANGE rather than a cottage. GM 2026-08-02, after the barred kinds were evicted
# and the packs refilled the same ground with servants: "I swear I'm seeing way MORE
# commoner houses in the samurai neighborhood now!" - the servant glyph is a laborer
# glyph with a 4 ft trim, so detached-and-ranked reads as exactly what the fence
# excludes. The COUNT is canon and is not what this polices (budgets.md: 72 of a
# provincial city's 120 servant families are attached to its 60 samurai households);
# the ARRANGEMENT is. Research: research/cities/government.md.


def _seg_0563_220__loose_servants(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.220 (loose_servants) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        loose_servants = []  # type: ignore[var-annotated]
    return _kept(locals(), ('loose_servants',))


def _seg_0563_221__b_11(
    *,
    M: Any = _UNBOUND,
    b: Any = _UNBOUND,
    host: Any = _UNBOUND,
    hosts: Any = _UNBOUND,
    loose_servants: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    of: Any = _UNBOUND,
    region: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    w: Any = _UNBOUND,
    wards: Any = _UNBOUND,
    wd: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.221 (b, host, hosts, loose_servants) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for wd in wards:
            if wd.get("name") != "samurai":
                continue
            region = _ward_interior(wd["boundary"], w)
            if not region:
                continue
            hosts = {(round(b["x"], 1), round(b["y"], 1)): b for b in M.get("buildings", []) if b.get("kind") in ("samurai", "samurai_large")}
            for b in M.get("buildings", []):
                if b.get("kind") != "servant" or "w" not in b or not point_in_poly(b["x"], b["y"], region):
                    continue
                of = b.get("of")
                host = hosts.get((round(of[0], 1), round(of[1], 1))) if of else None
                if host is None:
                    loose_servants.append((round(b["x"]), round(b["y"]), "freestanding - no samurai household"))
                elif edge_gap(b, host) > 2.5:
                    loose_servants.append((round(b["x"]), round(b["y"]), f"detached from its household by {edge_gap(b, host):.0f}px"))
                elif max(b["w"], b["h"]) < 2.2 * min(b["w"], b["h"]):
                    loose_servants.append((round(b["x"]), round(b["y"]), "drawn as a cottage, not a range"))
    return _kept(locals(), ('b', 'host', 'hosts', 'loose_servants', 'of', 'region', 'wd'))


def _seg_0563_222__city_ward_servants_housed_as_ranges(*, check: Any = _UNBOUND, loose_servants: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.222 (city_ward_servants_housed_as_ranges) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_ward_servants_housed_as_ranges",
            not loose_servants,
            f"servant dwelling(s) inside the samurai ward not drawn as their household's RANGE: {loose_servants[:6]} - a samurai household's "
            f"domestics live in the nagaya along its own frontage, not in a freestanding cottage among the compounds (which reads as the very "
            f"commoner fabric the fence excludes); place them with s.servant_ranges() AFTER the ward's samurai houses, and put any genuinely "
            f"ranked small housing outside the fence, where ashigaru kumi-yashiki belong",
        )
    return _kept(locals(), ())


def _seg_0563_223__city_samurai_ward_residents_only(*, check: Any = _UNBOUND, commoner_in: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.223 (city_samurai_ward_residents_only) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):
            check(
                "city_samurai_ward_residents_only",
                not commoner_in,
                f"commoner dwelling(s)/commerce INSIDE the samurai ward fence: {commoner_in[:8]} - the ward exists to seal the samurai/government quarter off the commoners; only samurai houses, their live-in servants and government ground belong inside (s.building refuses these seats once s.ward has run - hoist s.ward ahead of the commoner packs and re-seat the leaked households outside the fence)",
            )
    return _kept(locals(), ())


# the ward FENCE runs in OPEN ground - it must not pass THROUGH a building, a mausoleum, or
# another ward's fence (GM, 2026-07). The packs keep off the fence via s.ward's corridor, but
# a hand-placed compound (the mausoleum) or a diagonal fence segment can still cut through one.


def _seg_0563_224__fence_hit(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.224 (fence_hit) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        fence_hit = []  # type: ignore[var-annotated]
    return _kept(locals(), ('fence_hit',))


def _seg_0563_225___ftargets(*, M: Any = _UNBOUND, b: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.225 (_ftargets, b) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        _ftargets = [b for b in (M.get("buildings", []) + M.get("houses", []) + M.get("mausoleums", [])) if "w" in b]
    return _kept(locals(), ('_ftargets', 'b'))


def _seg_0563_226__b_12(
    *,
    _ftargets: Any = _UNBOUND,
    b: Any = _UNBOUND,
    b2: Any = _UNBOUND,
    bc: Any = _UNBOUND,
    bnd: Any = _UNBOUND,
    fence_hit: Any = _UNBOUND,
    i: Any = _UNBOUND,
    j: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    wards: Any = _UNBOUND,
    wd: Any = _UNBOUND,
    wd2: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.226 (b, b2, bc, bnd) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for wd in wards:
            bnd = wd["boundary"]
            for b in _ftargets:
                bc = rect_corners({"x": b["x"], "y": b["y"], "w": b["w"], "h": b.get("h", b["w"]), "rot": b.get("rot", 0)})
                if footprint_on_line(bc, bnd, 4):
                    fence_hit.append((round(b["x"]), round(b["y"])))
            for wd2 in wards:
                if wd2 is wd:
                    continue
                b2 = wd2["boundary"]
                if any(segments_cross(bnd[i], bnd[i + 1], b2[j], b2[j + 1]) for i in range(len(bnd) - 1) for j in range(len(b2) - 1)):
                    fence_hit.append(("ward-x-ward", round(bnd[0][0])))
    return _kept(locals(), ('b', 'b2', 'bc', 'bnd', 'fence_hit', 'i', 'j', 'wd', 'wd2'))


def _seg_0563_227__city_ward_fence_clear_of_structures(*, check: Any = _UNBOUND, fence_hit: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.227 (city_ward_fence_clear_of_structures) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_ward_fence_clear_of_structures",
            not fence_hit,
            f"ward fence passing THROUGH a structure (building / mausoleum / another fence): {sorted(set(fence_hit))[:4]} - "
            f"the fence runs in open ground; move the structure clear of the fence line or reroute the fence",
        )
    return _kept(locals(), ())


# a KIDO is a gate THROUGH the fence, so it must sit ON the fence (overlap it), not beside it
# (GM, 2026-07: a gate next to rather than part of the wall does not work). Its crossing point
# must lie within ~8px of a fence segment so the gate visibly straddles the fence.


def _seg_0563_228__off_fence(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.228 (off_fence) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        off_fence = []  # type: ignore[var-annotated]
    return _kept(locals(), ('off_fence',))


def _seg_0563_229__i_4(
    *, i: Any = _UNBOUND, kd: Any = _UNBOUND, kido: Any = _UNBOUND, meta: Any = _UNBOUND, off_fence: Any = _UNBOUND, scale: Any = _UNBOUND, wards: Any = _UNBOUND, wd: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.229 (i, kd, off_fence, wd) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for kd in kido:
            if wards and min((seg_dist(kd["x"], kd["y"], wd["boundary"][i], wd["boundary"][i + 1]) for wd in wards for i in range(len(wd["boundary"]) - 1)), default=999) > 8:
                off_fence.append((round(kd["x"]), round(kd["y"])))
    return _kept(locals(), ('i', 'kd', 'off_fence', 'wd'))


def _seg_0563_230__city_kido_on_ward_fence(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, off_fence: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.230 (city_kido_on_ward_fence) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_kido_on_ward_fence",
            not off_fence,
            f"ward gate(s) sitting BESIDE the fence, not on it: {off_fence[:4]} - a kido gates a crossing THROUGH the "
            f"fence, so its point must lie ON the fence line (overlap it), not offset into the ward",
        )
    return _kept(locals(), ())


# ...and where the fence meets the wall, the city WALL must render ON TOP (the fence runs
# UNDER the rampart). The fence is drawn late (high z), so without a wall cap on top of the
# junction it paints over the wall stroke. s.ward records the fence z and the wall cap it
# lays over each end; the cap's z must be above the fence's.


def _seg_0563_231__not_under(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.231 (not_under) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        not_under = []  # type: ignore[var-annotated]
    return _kept(locals(), ('not_under',))


def _seg_0563_232__c(
    *,
    c: Any = _UNBOUND,
    caps: Any = _UNBOUND,
    e: Any = _UNBOUND,
    fz: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    not_under: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    w: Any = _UNBOUND,
    wards: Any = _UNBOUND,
    wd: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.232 (c, caps, e, fz) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for wd in wards:
            fz = wd.get("z")
            caps = wd.get("wall_caps", [])
            if fz is None:
                continue
            for e in (wd["boundary"][0], wd["boundary"][-1]):
                if len(w) >= 3 and edge_dist(e[0], e[1], w) <= 15 and not any(c.get("z", -1) > fz and math.hypot(c["x"] - e[0], c["y"] - e[1]) < 30 for c in caps):
                    not_under.append((round(e[0]), round(e[1])))
    return _kept(locals(), ('c', 'caps', 'e', 'fz', 'not_under', 'wd'))


def _seg_0563_233__city_ward_fence_under_wall(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, not_under: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.233 (city_ward_fence_under_wall) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_ward_fence_under_wall",
            not not_under,
            f"ward-fence end(s) NOT rendered under the city wall - no wall cap on top of the junction, so the fence paints over the rampart: {not_under}",
        )
    return _kept(locals(), ())


# the extramural samurai estates all lie TOWARD OTOSAN UCHI (the Imperial capital) - a
# samurai builds his country seat on the capital-facing side, so the direction is
# per-city: meta(capital_dir=<cardinal>) (Tango SE, Nagahara NE). Each estate must sit in
# the correct half-plane(s) for that direction (a diagonal requires BOTH axes).


def _seg_0563_234__cx(*, meta: Any = _UNBOUND, p: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.234 (cx, cy, p) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        cx, cy = sum(p[0] for p in w) / len(w), sum(p[1] for p in w) / len(w)
    return _kept(locals(), ('cx', 'cy', 'p'))


def _seg_0563_235__cap(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.235 (cap) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        cap = meta.get("capital_dir", "southeast")
    return _kept(locals(), ('cap',))


def _seg_0563_236__cd(*, cap: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.236 (cd) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        cd = unit_dir(cap)
    return _kept(locals(), ('cd',))


def _seg_0563_237__city_capital_dir_valid(*, cap: Any = _UNBOUND, cd: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.237 (city_capital_dir_valid) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_capital_dir_valid", cd is not None, f"meta(capital_dir={cap!r}) is not a cardinal direction")
    return _kept(locals(), ())


def _seg_0563_238__city_estates_toward_capital(
    *,
    cap: Any = _UNBOUND,
    cd: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    est_out: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    mn: Any = _UNBOUND,
    not_cap: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    toward: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.238 (city_estates_toward_capital) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and cd:

        def toward(mn: dict[str, Any]) -> bool:
            okx = (mn["x"] > cx) if cd[0] > 0.3 else (mn["x"] < cx) if cd[0] < -0.3 else True
            oky = (mn["y"] > cy) if cd[1] > 0.3 else (mn["y"] < cy) if cd[1] < -0.3 else True
            return okx and oky

        not_cap = [(round(mn["x"]), round(mn["y"])) for mn in est_out if not toward(mn)]
        check(
            "city_estates_toward_capital",
            not not_cap,
            f"{len(not_cap)} samurai estate(s) not toward the capital ({cap}): {not_cap[:3]} - a city's extramural estates cluster on the Otosan-Uchi-facing side (meta(capital_dir=...))",
        )
    return _kept(locals(), ('mn', 'not_cap', 'toward'))


# ... and clear of the ROADS leaving the city (an estate straddling the highway blocks it -
# GM, 2026-07: a Nagahara estate sat on the bridge road). Test each outside estate footprint
# against every recorded road.


def _seg_0563_239__r_3(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, r: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.239 (r, roads_all) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        roads_all = [r["pts"] for r in M.get("roads", [])] or ([M["road"]] if M.get("road") else [])
    return _kept(locals(), ('r', 'roads_all'))


def _seg_0563_240__est_on_road(
    *, M: Any = _UNBOUND, est_out: Any = _UNBOUND, meta: Any = _UNBOUND, mn: Any = _UNBOUND, roads_all: Any = _UNBOUND, rp: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.240 (est_on_road, mn, rp) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        est_on_road = [(round(mn["x"]), round(mn["y"])) for mn in est_out if any(footprint_on_line(rect_corners(_struct_rect(mn)), rp, (M.get("road_width", 26) / 2 + 4)) for rp in roads_all)]
    return _kept(locals(), ('est_on_road', 'mn', 'rp'))


def _seg_0563_241__city_estates_clear_of_roads(*, check: Any = _UNBOUND, est_on_road: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.241 (city_estates_clear_of_roads) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_estates_clear_of_roads",
            not est_on_road,
            f"samurai estate(s) straddling a road out of the city: {est_on_road[:3]} - an estate fronts its own approach lane but must not sit ON the highway",
        )
    return _kept(locals(), ())


# the ground circulation (streets + alleys; NOT the Imperial road, which exits at the
# gates) must stay INSIDE the wall and clear of the moat - separate checks, since a lane
# can poke through the rampart, the moat, or both (the elliptical wall curves in, so a
# lane run to the block edge can spill outside even with its vertices nominally interior)


def _seg_0563_242__a_2(*, M: Any = _UNBOUND, a: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.242 (a, lanes_pts, st) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        lanes_pts = [st["pts"] for st in M.get("town_streets", [])] + [a["pts"] for a in M.get("alleys", [])]
    return _kept(locals(), ('a', 'lanes_pts', 'st'))


def _seg_0563_243__crosses_ring(*, i: Any = _UNBOUND, k: Any = _UNBOUND, meta: Any = _UNBOUND, pts: Any = _UNBOUND, ring: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.243 (crosses_ring) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):

        def crosses_ring(pts: Poly, ring: Poly, closed: bool) -> bool:
            rng = range(len(ring)) if closed else range(len(ring) - 1)
            return any(segments_cross(pts[k], pts[k + 1], ring[i], ring[(i + 1) % len(ring)]) for k in range(len(pts) - 1) for i in rng)

    return _kept(locals(), ('crosses_ring',))


# a way WHOLLY outside the rampart is the SUBURB's own circulation (021: the kashi
# belt and guan-xiang wards keep streets and roji like any machi) - only a way that
# CROSSES the wall, or an inside way poking out, is the defect


def _seg_0563_244__p_2(
    *, crosses_ring: Any = _UNBOUND, inwall: Any = _UNBOUND, lanes_pts: Any = _UNBOUND, meta: Any = _UNBOUND, p: Any = _UNBOUND, pts: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.244 (p, pts, wall_hit) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        wall_hit = [pts[0] for pts in lanes_pts if crosses_ring(pts, w, True) or (any(not inwall(p[0], p[1]) for p in pts) and any(inwall(p[0], p[1]) for p in pts))]
    return _kept(locals(), ('p', 'pts', 'wall_hit'))


def _seg_0563_245__city_streets_clear_of_wall(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, wall_hit: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.245 (city_streets_clear_of_wall) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_streets_clear_of_wall", not wall_hit, f"{len(wall_hit)} street/alley(s) crossing the city wall (a lane running outside the rampart): {wall_hit}")
    return _kept(locals(), ())


def _seg_0563_246__moat_1(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.246 (moat) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        moat = M.get("moat")
    return _kept(locals(), ('moat',))


def _seg_0563_247__city_streets_clear_of_moat(
    *, check: Any = _UNBOUND, crosses_ring: Any = _UNBOUND, lanes_pts: Any = _UNBOUND, meta: Any = _UNBOUND, moat: Any = _UNBOUND, moat_hit: Any = _UNBOUND, pts: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.247 (city_streets_clear_of_moat) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and moat:
        moat_hit = [pts[0] for pts in lanes_pts if crosses_ring(pts, moat, False)]
        check("city_streets_clear_of_moat", not moat_hit, f"{len(moat_hit)} street/alley(s) crossing the moat: {moat_hit}")
    return _kept(locals(), ('moat_hit', 'pts'))


# farm fields (in-wall plots OR the surrounding farmland) must not cut across the wall stroke
# or the moat - the moat sits between the wall and the close-in fields, so they abut, not overlap


def _seg_0563_248__f(*, f: Any = _UNBOUND, fields: Any = _UNBOUND, meta: Any = _UNBOUND, moat: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.248 (f, fld_bad) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        fld_bad = [f["name"] for f in fields if footprint_on_line(f["outline"], w, 10) or (moat and footprint_on_line(f["outline"], moat, 13))]
    return _kept(locals(), ('f', 'fld_bad'))


def _seg_0563_249__city_fields_clear_of_wall_moat(*, check: Any = _UNBOUND, fld_bad: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.249 (city_fields_clear_of_wall_moat) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_fields_clear_of_wall_moat", not fld_bad, f"field(s) overlapping the city wall or moat: {fld_bad}")
    return _kept(locals(), ())


# the in-wall pond is a water source, not a moat - it must not touch the wall or moat


def _seg_0563_250__pnd(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.250 (pnd) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        pnd = M.get("pond")
    return _kept(locals(), ('pnd',))


def _seg_0563_251__city_pond_clear_of_wall_moat(
    *,
    check: Any = _UNBOUND,
    k: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    moat: Any = _UNBOUND,
    p_out: Any = _UNBOUND,
    pcx: Any = _UNBOUND,
    pcy: Any = _UNBOUND,
    pnd: Any = _UNBOUND,
    prx: Any = _UNBOUND,
    pry: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    w: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.251 (city_pond_clear_of_wall_moat) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and pnd:
        pcx, pcy, prx, pry = pnd
        p_out = [(pcx + math.cos(math.tau * k / 28) * prx, pcy + math.sin(math.tau * k / 28) * pry) for k in range(28)]
        check("city_pond_clear_of_wall_moat", not (footprint_on_line(p_out, w, 9) or (moat and footprint_on_line(p_out, moat, 13))), "the in-wall pond overlaps the city wall or moat")
    return _kept(locals(), ('k', 'p_out', 'pcx', 'pcy', 'prx', 'pry'))
