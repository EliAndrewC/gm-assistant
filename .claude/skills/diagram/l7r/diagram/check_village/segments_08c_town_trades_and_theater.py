"""Gate segments (town trades and theater; keys 0543_011-0543_057) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from .common_01_geometry import CLAN_FORTUNES, point_in_poly, seg_closest, seg_dist, within_edge_gap
from .common_02_overlap_policy import check_fire_features, check_theater_stage
from .common_03_capacity import _UNBOUND, DWELLING_KINDS, _fronts_route, _kept


def _seg_0543_011__b_1(*, M: Any = _UNBOUND, b: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.011 (b, bur_t) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        bur_t = [b for b in M.get("buildings", []) if b.get("kind") == "burakumin"]
    return _kept(locals(), ('b', 'bur_t'))


def _seg_0543_012__b_2(*, M: Any = _UNBOUND, b: Any = _UNBOUND, houses: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.012 (b, oth_t) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        oth_t = [b for b in M.get("buildings", []) if b.get("kind") in ("laborer", "laborer_large", "servant", "merchant", "merchant_house", "merchant_large", "samurai", "samurai_large")] + houses
    return _kept(locals(), ('b', 'oth_t'))


def _seg_0543_013__burakumin_quarter_segregated(
    *,
    BURAKUMIN_SEAM_FT: Any = _UNBOUND,
    _seam: Any = _UNBOUND,
    b: Any = _UNBOUND,
    bur_t: Any = _UNBOUND,
    check: Any = _UNBOUND,
    close_t: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    o: Any = _UNBOUND,
    oth_t: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0543.013 (burakumin_quarter_segregated) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town' and bur_t and oth_t:
        _seam = BURAKUMIN_SEAM_FT / float(meta.get("ftpx") or 1)
        close_t = [(round(b["x"]), round(b["y"])) for b in bur_t if any(within_edge_gap(b, o, _seam) for o in oth_t)]
        check(
            "burakumin_quarter_segregated",
            not close_t,
            f"burakumin dwelling(s) mixed among other castes at {close_t[:3]} - the quarter is SEGREGATED: open ground separates it from every other caste's housing",
        )
    return _kept(locals(), ('_seam', 'b', 'close_t', 'o'))


def _seg_0543_014__non_farmer_max(*, caste_n: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.014 (non_farmer_max) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        non_farmer_max = max(caste_n.values(), default=0)
    return _kept(locals(), ('non_farmer_max',))


# WHY (farmers are the overwhelming majority caste): settlements.md "Historical grounding"


def _seg_0543_015__town_farmers_plurality(*, check: Any = _UNBOUND, farmhouses: Any = _UNBOUND, non_farmer_max: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.015 (town_farmers_plurality) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        check("town_farmers_plurality", farmhouses >= non_farmer_max, f"farmhouses {farmhouses} should be the largest single group (max other {non_farmer_max})")
    return _kept(locals(), ())


# MERCHANT and LABORER housing varies in SIZE by wealth, like a provincial city's (budgets.md
# Town wealth tiers): a MINORITY of merchants are very-rich / rich and live in large homes
# (~5 of ~24), and a few laborers are 'master/rich' (~2-3 of ~29); the rest live in small/standard
# dwellings. Require the larger homes (kind merchant_large / laborer_large) to be PRESENT and a
# CLEAR MINORITY - not that every house is one uniform size.


def _seg_0543_016__m_small(*, bk: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.016 (m_small) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        m_small = bk.get("merchant", 0) + bk.get("merchant_house", 0)
    return _kept(locals(), ('m_small',))


def _seg_0543_017__m_big(*, bk: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.017 (m_big) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        m_big = bk.get("merchant_large", 0)
    return _kept(locals(), ('m_big',))


def _seg_0543_018__town_merchant_housing_varied(*, check: Any = _UNBOUND, m_big: Any = _UNBOUND, m_small: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.018 (town_merchant_housing_varied) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town' and m_small + m_big:
        check(
            "town_merchant_housing_varied",
            m_big >= 2 and m_small > m_big,
            f"town merchant housing lacks size variety (budgets.md: ~5 of ~24 merchants are very-rich/rich): "
            f"{m_big} large of {m_small + m_big} - give the wealthy merchants larger homes (kind 'merchant_large'), a clear minority",
        )
    return _kept(locals(), ())


def _seg_0543_019__l_small(*, bk: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.019 (l_small) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        l_small = bk.get("laborer", 0)
    return _kept(locals(), ('l_small',))


def _seg_0543_020__l_big(*, bk: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.020 (l_big) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        l_big = bk.get("laborer_large", 0)
    return _kept(locals(), ('l_big',))


def _seg_0543_021__town_laborer_housing_varied(*, check: Any = _UNBOUND, l_big: Any = _UNBOUND, l_small: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.021 (town_laborer_housing_varied) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town' and l_small + l_big:
        check(
            "town_laborer_housing_varied",
            l_big >= 2 and l_small > l_big,
            f"town laborer housing lacks size variety (budgets.md: ~2-3 'master/rich' of ~29 laborers): "
            f"{l_big} large of {l_small + l_big} - give the wealthier laborers larger homes (kind 'laborer_large'), a clear minority",
        )
    return _kept(locals(), ())


# MERCHANT RESIDENCES sit BEHIND the merchant BUSINESSES, and CLOSER to the road than the
# LABORER housing - a clean radial band: shops front the road, the merchant homes directly
# behind them, then a gap, then the laborers set further back. Scoped to road-fronted towns
# (those with a trunk M["road"], e.g. unwalled Hoshizora); a walled town's interior grid is laid
# out around cross-streets, not one radial axis, so this single-axis test does not apply there.
# droad = perpendicular distance from a building to the nearest road segment.


def _seg_0543_022__rd(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.022 (rd) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        rd = M.get("road")
    return _kept(locals(), ('rd',))


def _seg_0543_023__housing_aligned_behind_storefronts(
    *,
    ALONG_TOL: Any = _UNBOUND,
    ANG_TOL: Any = _UNBOUND,
    DEPTH_MAX: Any = _UNBOUND,
    DEPTH_MIN: Any = _UNBOUND,
    GAP: Any = _UNBOUND,
    M: Any = _UNBOUND,
    _along: Any = _UNBOUND,
    _droad: Any = _UNBOUND,
    askew: Any = _UNBOUND,
    b: Any = _UNBOUND,
    biz: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    d: Any = _UNBOUND,
    h: Any = _UNBOUND,
    homes: Any = _UNBOUND,
    in_biz_band: Any = _UNBOUND,
    k: Any = _UNBOUND,
    ki: Any = _UNBOUND,
    labs: Any = _UNBOUND,
    maxbiz: Any = _UNBOUND,
    maxres: Any = _UNBOUND,
    mh_problems: Any = _UNBOUND,
    minlab: Any = _UNBOUND,
    mres: Any = _UNBOUND,
    nsh: Any = _UNBOUND,
    rcum: Any = _UNBOUND,
    rd: Any = _UNBOUND,
    s: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    shops: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0543.023 (housing_aligned_behind_storefronts, merchant_residences_behind_businesses) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town' and rd:

        def _droad(b: dict[str, Any]) -> float:
            return min(seg_dist(b["x"], b["y"], rd[k], rd[k + 1]) for k in range(len(rd) - 1))

        biz = [b for b in M.get("buildings", []) if b.get("kind") in ("shop", "merchant")]
        mres = [b for b in M.get("buildings", []) if b.get("kind") in ("merchant_house", "merchant_large")]
        labs = [b for b in M.get("buildings", []) if b.get("kind") in ("laborer", "laborer_large")]
        mh_problems = []
        if biz and mres:
            maxbiz = max(_droad(b) for b in biz)
            in_biz_band = [b for b in mres if _droad(b) <= maxbiz]
            if in_biz_band:
                mh_problems.append(f"{len(in_biz_band)} merchant residence(s) sit within the storefront band, not behind it")
            maxres = max(_droad(b) for b in mres)
            if labs:
                GAP = 35  # min radial gap (px, center-to-center depth) between the merchant-home band and the laborer warren
                minlab = min(_droad(b) for b in labs)
                if minlab < maxres + GAP:
                    mh_problems.append(
                        f"laborer housing not set back beyond the merchant residences with a gap "
                        f"(nearest laborer {round(minlab)}px from road vs merchant residences out to {round(maxres)}px; want >= {GAP}px clear)"
                    )
            check(
                "merchant_residences_behind_businesses",
                not mh_problems,
                f"a road-fronted town's merchant residences must sit directly BEHIND the shops, with the laborer housing set FURTHER back and a gap between the two bands: {mh_problems}",
            )
        # HOUSING DIRECTLY BEHIND A STOREFRONT shares the storefront's ORIENTATION: a home tucked
        # right behind a shop (a merchant family over/behind its own premises) must lie PARALLEL to
        # that shop, not askew to it - the block reads as one aligned unit, shopfront then dwelling.
        # "Directly behind" is judged in ROAD coordinates, not raw distance: project each building onto
        # the road to get (along, droad). A home H sits directly behind its nearest shop S when it is at
        # nearly the SAME position ALONG the road (|along_H - along_S| <= ALONG_TOL = in S's radial shadow)
        # AND one building DEEPER (DEPTH_MIN < droad_H - droad_S <= DEPTH_MAX, i.e. immediately behind S,
        # not way back in the warren and not merely beside it). This isolates the home-over-its-shop case
        # from pack-edge dwellings that happen to lie near a shop. Angles compared mod 180 (a 180deg-flipped
        # footprint is still parallel). Road-fronted only - same single-axis scoping as the band check above.
        rcum = [0.0]
        for ki in range(len(rd) - 1):
            rcum.append(rcum[-1] + math.hypot(rd[ki + 1][0] - rd[ki][0], rd[ki + 1][1] - rd[ki][1]))

        def _along(b: dict[str, Any]) -> float:
            bestd, bestt = float("inf"), 0.0
            for k in range(len(rd) - 1):
                cx, cy = seg_closest(b["x"], b["y"], rd[k], rd[k + 1])
                d = math.hypot(cx - b["x"], cy - b["y"])
                if d < bestd:
                    bestd, bestt = d, rcum[k] + math.hypot(cx - rd[k][0], cy - rd[k][1])
            return bestt

        shops = [b for b in M.get("buildings", []) if b.get("kind") in ("shop", "merchant")]
        homes = [b for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS and b.get("kind") != "merchant"]
        ALONG_TOL, DEPTH_MIN, DEPTH_MAX, ANG_TOL = 42, 15, 74, 15
        askew = []
        for h in homes:
            nsh = min(shops, key=lambda s: math.hypot(s["x"] - h["x"], s["y"] - h["y"]), default=None)
            if nsh is None:
                continue
            if abs(_along(h) - _along(nsh)) > ALONG_TOL:  # not in the shop's radial shadow
                continue
            if not (DEPTH_MIN < _droad(h) - _droad(nsh) <= DEPTH_MAX):  # beside / far back, not directly behind
                continue
            d = abs(h.get("rot", 0) - nsh.get("rot", 0)) % 180
            d = min(d, 180 - d)
            if d > ANG_TOL:
                askew.append((round(h["x"]), round(h["y"]), round(d)))
        check(
            "housing_aligned_behind_storefronts",
            not askew,
            f"housing tucked directly behind a storefront must lie PARALLEL to it (orientation within {ANG_TOL}deg, mod 180); these homes are askew (x, y, mismatch deg): {askew}",
        )
    return _kept(
        locals(),
        (
            'ALONG_TOL',
            'ANG_TOL',
            'DEPTH_MAX',
            'DEPTH_MIN',
            'GAP',
            '_along',
            '_droad',
            'askew',
            'b',
            'biz',
            'd',
            'h',
            'homes',
            'in_biz_band',
            'ki',
            'labs',
            'maxbiz',
            'maxres',
            'mh_problems',
            'minlab',
            'mres',
            'nsh',
            'rcum',
            'shops',
        ),
    )


def _seg_0543_024__town_has_magistrate_manor(*, M: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.024 (town_has_magistrate_manor) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        check("town_has_magistrate_manor", len(M.get("manors", [])) >= 1, "a county-seat town must have the magistrate's manor")
    return _kept(locals(), ())


# a town has hundreds of farmers - we never show all the farmland, so at least
# one field must run off the map edge (implying more farmland beyond what's drawn)


def _seg_0543_025__f(*, f: Any = _UNBOUND, fields: Any = _UNBOUND, runs_off_edge: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.025 (f, off_edge) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        off_edge = [f["name"] for f in fields if runs_off_edge(f["outline"])]
    return _kept(locals(), ('f', 'off_edge'))


def _seg_0543_026__town_has_field_off_edge(*, check: Any = _UNBOUND, off_edge: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.026 (town_has_field_off_edge) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        check("town_has_field_off_edge", off_edge, "a town must have at least one field running off the map edge (more farmland implied)")
    return _kept(locals(), ())


# a rice-TRANSIT town (meta(granary=True)) shows a distinct tax-rice granary - a row of
# fireproof kura where grain gathered from many counties is forwarded up the kick-up
# chain. A standard county seat does NOT draw one: its grain sits inside the magistrate's
# yamen, implied by the manor. Opt-in, so the default is no check (unlike the gate
# market, theater stage, and monasteries, which are opt-OUT defaults).


def _seg_0543_027__town_has_granary(*, M: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.027 (town_has_granary) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town' and meta.get("granary"):
        check("town_has_granary", bool(M.get("granary")), "meta(granary=True) declares a rice-transit town - it must draw a granary via s.granary(...)")
    return _kept(locals(), ())


# a noticeable MINORITY of merchant houses keep a fireproof storehouse (kura) for their
# (often absentee) landlords' rent-rice and bulk goods - more than a token 1-2, beyond a
# shop's ordinary inventory. Draw them with s.merchant_storehouses(...).


def _seg_0543_028__town_has_merchant_storehouses(*, M: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.028 (town_has_merchant_storehouses) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        check(
            "town_has_merchant_storehouses",
            len(M.get("storehouses", [])) >= 3,
            f"{len(M.get('storehouses', []))} merchant storehouses - a town's merchant quarter should show several attached kura (call s.merchant_storehouses(...))",
        )
    return _kept(locals(), ())


# a county seat is a market center: peasants from the far edge of its catchment stay
# over on market eve in a cheap communal flophouse (kichin-yado) where travelers arrive
# - the gate market of a walled town, the road of an unwalled one. Default-on (>= 1);
# meta(flophouses=N) requires more (a busy hub); meta(flophouses=0) opts out.


def _seg_0543_029__want_flop(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.029 (want_flop) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        want_flop = meta.get("flophouses", 1)
    return _kept(locals(), ('want_flop',))


def _seg_0543_030__town_has_flophouse(*, M: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND, want_flop: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.030 (town_has_flophouse) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        check(
            "town_has_flophouse",
            len(M.get("flophouses", [])) >= want_flop,
            f"{len(M.get('flophouses', []))} flophouses, expected >= {want_flop} (cheap market-day lodging via s.flophouse(...); meta(flophouses=N) to change)",
        )
    return _kept(locals(), ())


# a county town is a stop on the trade route: it needs ONE caravan INN (s.inn) with a STABLES
# (s.stables) next to it and OPEN GROUND beside the stables - a pasture for the wagon-train oxen
# and horses - exactly like a provincial city's gate caravan facilities, but a single one. The
# inn must sit ALONG the road (the Imperial road, or a town street) - the caravans pull up to it -
# NOT buried behind the shop rows. A WALLED town keeps it INSIDE the rampart (caravans enter the gate).


def _seg_0543_031__b_3(*, M: Any = _UNBOUND, b: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.031 (b, inns) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        inns = [b for b in M.get("buildings", []) if b.get("kind") == "inn"]
    return _kept(locals(), ('b', 'inns'))


def _seg_0543_032__b_4(*, M: Any = _UNBOUND, b: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.032 (b, stbl) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        stbl = [b for b in M.get("buildings", []) if b.get("kind") == "stables"]
    return _kept(locals(), ('b', 'stbl'))


def _seg_0543_033__cwall(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.033 (cwall) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        cwall = M.get("wall")
    return _kept(locals(), ('cwall',))


def _seg_0543_034__routes(*, M: Any = _UNBOUND, s: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.034 (routes, s) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        routes = ([M["road"]] if M.get("road") else []) + [s["pts"] for s in M.get("town_streets", [])]
    return _kept(locals(), ('routes', 's'))


def _seg_0543_035__b_5(*, M: Any = _UNBOUND, b: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.035 (b, others) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        others = [b for b in M.get("buildings", []) if b.get("kind") not in ("inn", "stables")]
    return _kept(locals(), ('b', 'others'))


def _seg_0543_036__b_6(*, M: Any = _UNBOUND, b: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.036 (b, dwell_t) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        dwell_t = [b for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS] + M.get("houses", [])
    return _kept(locals(), ('b', 'dwell_t'))


def _seg_0543_037__caravan_ok(*, inns: Any = _UNBOUND, scale: Any = _UNBOUND, stbl: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.037 (caravan_ok, why) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        caravan_ok, why = False, f"inn={len(inns)} stables={len(stbl)}"
    return _kept(locals(), ('caravan_ok', 'why'))


def _seg_0543_038__caravan_ok_1(
    *,
    crowd: Any = _UNBOUND,
    cwall: Any = _UNBOUND,
    d: Any = _UNBOUND,
    dwell_t: Any = _UNBOUND,
    inn: Any = _UNBOUND,
    inns: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    near_st: Any = _UNBOUND,
    others: Any = _UNBOUND,
    routes: Any = _UNBOUND,
    s: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    st: Any = _UNBOUND,
    stbl: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0543.038 (caravan_ok, crowd, d, inn) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        for inn in inns:
            near_st = [s for s in stbl if math.hypot(s["x"] - inn["x"], s["y"] - inn["y"]) <= 150]
            if not near_st:
                why = "the inn has no stables beside it"
                continue
            st = near_st[0]
            if meta.get("walled") and cwall and not (point_in_poly(inn["x"], inn["y"], cwall) and point_in_poly(st["x"], st["y"], cwall)):
                why = "the caravan inn + stables must be INSIDE the walls"
                continue
            crowd = sum(1 for d in dwell_t if math.hypot(d["x"] - st["x"], d["y"] - st["y"]) < 75)
            if crowd > 4:
                why = f"the stables is hemmed in by {crowd} dwellings (it needs open ground - a pasture for the animals)"
                continue
            if routes and not _fronts_route(inn["x"], inn["y"], routes, others):
                why = "the inn sits BEHIND the shop rows - it must front the road/main street (caravans pull up to it)"
                continue
            caravan_ok = True
            break
    return _kept(locals(), ('caravan_ok', 'crowd', 'd', 'inn', 'near_st', 's', 'st', 'why'))


def _seg_0543_039__town_has_caravan_inn(*, caravan_ok: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND, why: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.039 (town_has_caravan_inn) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        check(
            "town_has_caravan_inn",
            caravan_ok,
            f"a county town needs ONE caravan INN with a STABLES beside it, OPEN GROUND for the wagon-train animals, and "
            f"FRONTING the road (inside the walls if walled): {why} - add s.inn(...) + s.stables(...), like a provincial city's gate facilities but a single one",
        )
    return _kept(locals(), ())


# the inn FACES the road and lies PARALLEL to it - the caravans pull straight up to it - so its
# noren front (the +y edge after the inn's `rot`) must point at the nearest route point, which also
# makes its long frontage edge run along the road. A diagonal road needs a tilted inn.


def _seg_0543_040__unaligned(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.040 (unaligned) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        unaligned = []  # type: ignore[var-annotated]
    return _kept(locals(), ('unaligned',))


def _seg_0543_041__bd(
    *,
    bd: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    d: Any = _UNBOUND,
    dx: Any = _UNBOUND,
    dy: Any = _UNBOUND,
    fn: Any = _UNBOUND,
    inn: Any = _UNBOUND,
    inns: Any = _UNBOUND,
    ki: Any = _UNBOUND,
    npt: Any = _UNBOUND,
    r: Any = _UNBOUND,
    routes: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    th: Any = _UNBOUND,
    unaligned: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0543.041 (bd, cx, cy, d) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        for inn in inns:
            npt, bd = None, 1e18
            for r in routes:
                for ki in range(len(r) - 1):
                    cx, cy = seg_closest(inn["x"], inn["y"], r[ki], r[ki + 1])
                    d = math.hypot(cx - inn["x"], cy - inn["y"])
                    if d < bd:
                        bd, npt = d, (cx, cy)
            if npt is None or bd < 1:
                continue
            dx, dy = (npt[0] - inn["x"]) / bd, (npt[1] - inn["y"]) / bd
            th = math.radians(inn.get("rot", 0))
            fn = (-math.sin(th), math.cos(th))  # the +y front's outward normal after rot
            if fn[0] * dx + fn[1] * dy < 0.88:  # within ~28deg of facing the nearest road point
                unaligned.append((round(inn["x"]), round(inn["y"])))
    return _kept(locals(), ('bd', 'cx', 'cy', 'd', 'dx', 'dy', 'fn', 'inn', 'ki', 'npt', 'r', 'th', 'unaligned'))


def _seg_0543_042__inn_faces_the_road(*, check: Any = _UNBOUND, routes: Any = _UNBOUND, scale: Any = _UNBOUND, unaligned: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.042 (inn_faces_the_road) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town' and routes:
        check(
            "inn_faces_the_road",
            not unaligned,
            f"caravan inn(s) not oriented to FACE the road and lie parallel to it: {unaligned[:3]} - tilt the inn "
            f"(s.inn(x, y, rot=...)) so its noren front faces the roadbed and its long edge runs along the road",
        )
    return _kept(locals(), ())


# every town has a THEATER STAGE unless meta(theater_stage=False); for a walled town
# it sits INSIDE the walls unless meta(theater_stage="outside")


def _seg_0543_043__ts_meta(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.043 (ts_meta) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        ts_meta = meta.get("theater_stage", True)
    return _kept(locals(), ('ts_meta',))


def _seg_0543_044__amph_raw(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.044 (amph_raw) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        amph_raw = M.get("theater_stage")
    return _kept(locals(), ('amph_raw',))


def _seg_0543_045__amph_all(*, amph_raw: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.045 (amph_all) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        amph_all = amph_raw if isinstance(amph_raw, list) else ([amph_raw] if amph_raw else [])
    return _kept(locals(), ('amph_all',))


def _seg_0543_046__amph(*, a9: Any = _UNBOUND, amph_all: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.046 (amph) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        amph = max(amph_all, key=lambda a9: a9.get("w", 0)) if amph_all else None
    return _kept(locals(), ('amph',))


def _seg_0543_047__town_has_theater_stage(*, amph: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND, ts_meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.047 (town_has_theater_stage) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town' and ts_meta is not False:
        check("town_has_theater_stage", bool(amph), "a town must have a theater stage (set meta(theater_stage=False) to omit)")
    return _kept(locals(), ())


def _seg_0543_048__theater_stage_inside_wall(
    *, M: Any = _UNBOUND, amph: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, ts_meta: Any = _UNBOUND, w: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0543.048 (theater_stage_inside_wall) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town' and amph and meta.get("walled") and ts_meta != "outside":
        w = M.get("wall") or []
        check(
            "theater_stage_inside_wall",
            len(w) >= 3 and point_in_poly(amph["x"], amph["y"], w),
            "a walled town's theater stage belongs inside the walls (set meta(theater_stage='outside') to allow outside)",
        )
    return _kept(locals(), ('w',))


def _seg_0543_049__theater_stage_by_temple(*, M: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.049 (theater_stage_by_temple, theater_stage_clear, theater_stage_faces_temple) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        check_theater_stage(M, check)
    return _kept(locals(), ())


def _seg_0543_050__fire_tower_amid_its_district(*, M: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.050 (fire_tower_amid_its_district, fire_tower_clear_of_fields, fire_tower_clear_of_graveyards, fire_tower_clear_of_wells, fire_tower_in_commoner_quarter, fire_tower_standoff, fire_towers_dispersed) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        check_fire_features(M, check)  # geometry of any fire towers (presence required only for a WALLED town, below)
    return _kept(locals(), ())


# a town's monasteries: by default 2, dedicated to the patron fortunes of the clan
# whose holdings include it (meta(clan=...)). Override with an explicit list -
# meta(monastery_fortunes=[...]) - for a town that changed hands, or a 1-monastery town.


def _seg_0543_051__monks(*, M: Any = _UNBOUND, r: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.051 (monks, r) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        monks = [r for r in M.get("religious", []) if r.get("kind") == "monastery"]
    return _kept(locals(), ('monks', 'r'))


def _seg_0543_052___fortune(*, lab: Any = _UNBOUND, r: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.052 (_fortune) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':

        def _fortune(r: dict[str, Any]) -> str:
            lab = (r.get("label") or "").strip()
            return lab.rsplit(" of ", 1)[-1].strip() if " of " in lab else lab

    return _kept(locals(), ('_fortune',))


def _seg_0543_053__declared(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.053 (declared) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        declared = meta.get("monastery_fortunes")
    return _kept(locals(), ('declared',))


def _seg_0543_054__clan(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.054 (clan) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        clan = meta.get("clan")
    return _kept(locals(), ('clan',))


def _seg_0543_055__town_clan_known(*, cf: Any = _UNBOUND, check: Any = _UNBOUND, clan: Any = _UNBOUND, declared: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.055 (town_clan_known) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town' and declared is None and clan:
        cf = CLAN_FORTUNES.get(clan.lower())
        check("town_clan_known", cf is not None, f"unknown clan {clan!r} - no patron fortunes")
        declared = sorted(cf) if cf else None
    return _kept(locals(), ('cf', 'declared'))


def _seg_0543_056__town_declares_monasteries(*, check: Any = _UNBOUND, declared: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.056 (town_declares_monasteries) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        check("town_declares_monasteries", declared is not None, "a town must declare its monasteries via meta(clan=...) or meta(monastery_fortunes=[...])")
    return _kept(locals(), ())


def _seg_0543_057__town_monastery_count(
    *, _fortune: Any = _UNBOUND, check: Any = _UNBOUND, declared: Any = _UNBOUND, got: Any = _UNBOUND, monks: Any = _UNBOUND, r: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0543.057 (town_monasteries_dedicated, town_monastery_count) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town' and declared is not None:
        check("town_monastery_count", len(monks) == len(declared), f"{len(monks)} monasteries, expected {len(declared)} for {sorted(declared)}")
        got = sorted(_fortune(r) for r in monks)
        check("town_monasteries_dedicated", got == sorted(declared), f"monasteries dedicated to {got}, expected {sorted(declared)}")
    return _kept(locals(), ('got', 'r'))
