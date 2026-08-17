"""Gate segments (city castes and dojos; keys 0563_000-0563_044) - bodies verbatim, registry order preserved."""

import math
from collections.abc import Sequence
from typing import Any

from .common_01_geometry import Pt, point_in_poly, seg_dist
from .common_02_overlap_policy import DOJO_PER_SAMURAI, DOJO_QUARTER_PX, DOJO_RANGE_FT, DOJO_SAMURAI_FRAC
from .common_03_capacity import _UNBOUND, HOUSEHOLD, _kept


def _seg_0563_000__bk(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.000 (bk) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        bk = {}  # type: ignore[var-annotated]
    return _kept(locals(), ('bk',))


def _seg_0563_001__b(*, M: Any = _UNBOUND, b: Any = _UNBOUND, bk: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.001 (b, bk) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        for b in M.get("buildings", []):
            bk[b.get("kind")] = bk.get(b.get("kind"), 0) + 1
    return _kept(locals(), ('b', 'bk'))


# every provincial city's interior carries the provincial government:


def _seg_0563_002__city_has_governor_mansion(*, M: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.002 (city_has_governor_mansion) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and scale == "city":
        # a CAPITAL has no governor - the daimyo's court IS the government (020 doctrine,
        # "Rules that INVERT"); the castle carries what the mansion carries provincially
        check("city_has_governor_mansion", bool(M.get("governor_mansion")), "a provincial city must have the governor's mansion (s.governor_mansion(...))")
    return _kept(locals(), ())


def _seg_0563_003__mins(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.003 (mins) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        mins = M.get("ministries", [])
    return _kept(locals(), ('mins',))


def _seg_0563_004__city_has_six_ministries(*, check: Any = _UNBOUND, mins: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.004 (city_has_six_ministries) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        check("city_has_six_ministries", len(mins) == 6, f"{len(mins)} provincial ministry offices, expected exactly 6 (s.ministry(...))")
    return _kept(locals(), ())


def _seg_0563_005__m(*, m: Any = _UNBOUND, mins: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.005 (m, rites) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        rites = [m for m in mins if "rites" in (m.get("name") or "").lower()]
    return _kept(locals(), ('m', 'rites'))


def _seg_0563_006__city_has_ministry_of_rites(*, check: Any = _UNBOUND, rites: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.006 (city_has_ministry_of_rites) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        check("city_has_ministry_of_rites", len(rites) == 1, f"{len(rites)} Ministry of Rites office(s), expected exactly 1 (sited in the temple neighborhood)")
    return _kept(locals(), ())


def _seg_0563_007__sam_n(*, bk: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.007 (sam_n) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        sam_n = bk.get("samurai", 0) + bk.get("samurai_large", 0)
    return _kept(locals(), ('sam_n',))


def _seg_0563_008__city_has_samurai_neighborhood(*, check: Any = _UNBOUND, sam_n: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.008 (city_has_samurai_neighborhood) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        check("city_has_samurai_neighborhood", sam_n >= 8, f"{sam_n} samurai houses - a provincial city needs a samurai neighborhood")
    return _kept(locals(), ())


# a provincial city is ~10% samurai (~300 of ~3,000, budgets.md) - about pop/50 households.
# Most are housed in the samurai neighborhood as individual houses; the governor's compound
# and the extramural estates hold the rest. Require the neighborhood to depict at least ~65%
# of that expected household count, so it is a real quarter, not a token cluster of a few.


def _seg_0563_009__b_1(*, M: Any = _UNBOUND, b: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.009 (b, samurai_h) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        samurai_h = [b for b in M.get("buildings", []) if b.get("kind") in ("samurai", "samurai_large")]
    return _kept(locals(), ('b', 'samurai_h'))


def _seg_0563_010__pop(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.010 (pop) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        pop = meta.get("population", 0)
    return _kept(locals(), ('pop',))


def _seg_0563_011__city_samurai_housing_sufficient(
    *, URBAN: Any = _UNBOUND, check: Any = _UNBOUND, need: Any = _UNBOUND, pop: Any = _UNBOUND, samurai_h: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.011 (city_samurai_housing_sufficient) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and pop and URBAN:
        # CITY-ONLY: at the capital the samurai cohort is majority-HOUSED IN OTHER FORMS
        # (walled yashiki recorded as manors, retainer terraces as unit ranges), and
        # capital_housing_matches_band_targets pins every band to the budget - a detached
        # house count floor would just re-litigate that with the wrong denominator.
        need = round(0.65 * (0.10 * pop / HOUSEHOLD))
        check(
            "city_samurai_housing_sufficient",
            len(samurai_h) >= need,
            f"only {len(samurai_h)} samurai houses for a ~{round(0.10 * pop)}-samurai city (~{round(0.10 * pop / HOUSEHOLD)} households); "
            f"expect >= {need} in the neighborhood (the governor's compound + extramural estates hold the rest)",
        )
    return _kept(locals(), ('need',))


# samurai (unlike the poor, who sit in the deep block cores) LINE their streets - many houses
# front a street even if deeper lots sit behind. Require at least a third near a street/road.


def _seg_0563_012__city_samurai_partly_front_streets(
    *,
    M: Any = _UNBOUND,
    b: Any = _UNBOUND,
    check: Any = _UNBOUND,
    i: Any = _UNBOUND,
    near_ct: Any = _UNBOUND,
    samurai_h: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    slines: Any = _UNBOUND,
    sp: Any = _UNBOUND,
    st: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.012 (city_samurai_partly_front_streets) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and samurai_h:
        slines = [st["pts"] for st in M.get("town_streets", [])] + ([M["road"]] if M.get("road") else [])
        near_ct = sum(1 for b in samurai_h if any(seg_dist(b["x"], b["y"], sp[i], sp[i + 1]) < 90 for sp in slines for i in range(len(sp) - 1)))
        check("city_samurai_partly_front_streets", near_ct >= len(samurai_h) / 3, f"only {near_ct}/{len(samurai_h)} samurai houses front a street (want >= 1/3) - a samurai quarter lines its streets")
    return _kept(locals(), ('b', 'i', 'near_ct', 'slines', 'sp', 'st'))


# SAMURAI HOUSING varies in size by rank, UNLIKE a uniform cluster. budgets.md's provincial-city
# rank table puts ~25% of resident samurai in the senior ranks (R5-7) and the rest in R1-4; so the
# in-city neighborhood mixes a MINORITY of large houses (senior) among many small ones (junior).
# Crucially, samurai walled ESTATES are OUTSIDE the walls (rural goshi) - the only walled samurai
# compound inside the city is the governor's mansion - so NO manor may sit inside the wall ring.


def _seg_0563_013__b_2(*, M: Any = _UNBOUND, b: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.013 (b, slarge) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        slarge = [b for b in M.get("buildings", []) if b.get("kind") == "samurai_large"]
    return _kept(locals(), ('b', 'slarge'))


def _seg_0563_014__b_3(*, M: Any = _UNBOUND, b: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.014 (b, ssmall) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        ssmall = [b for b in M.get("buildings", []) if b.get("kind") == "samurai"]
    return _kept(locals(), ('b', 'ssmall'))


def _seg_0563_015__city_samurai_housing_varied(
    *, M: Any = _UNBOUND, check: Any = _UNBOUND, in_est: Any = _UNBOUND, m: Any = _UNBOUND, scale: Any = _UNBOUND, slarge: Any = _UNBOUND, ssmall: Any = _UNBOUND, w: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.015 (city_samurai_housing_varied) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and (slarge or ssmall):
        w = M.get("wall") or []
        in_est = [m for m in M.get("manors", []) if len(w) >= 3 and point_in_poly(m["x"], m["y"], w)]
        if scale == "capital":
            # INVERTED at the capital (020 doctrine): karo and chancellors live in walled
            # yashiki INSIDE the wall - that is the defining jokamachi texture - and the
            # senior-heavy mix is policed by capital_housing_matches_band_targets instead
            in_est = []
        check(
            "city_samurai_housing_varied",
            len(slarge) >= 3 and len(ssmall) > len(slarge) and not in_est,
            f"samurai housing lacks size variety or has in-wall estates (large city houses={len(slarge)}, "
            f"small={len(ssmall)}, walled estates inside the city={len(in_est)}) - senior ranks get large city "
            f"houses, juniors small ones, and samurai walled estates sit OUTSIDE the walls (only the "
            f"governor's mansion is walled within)",
        )
    return _kept(locals(), ('in_est', 'm', 'w'))


# MARTIAL TRAINING (GM 2026-07-25; settlements.md "Historical grounding: martial training in
# a provincial city"). The provincial city is the FIRST tier that supports a dojo at all -
# a county town's ~20 resident samurai are no student body and no living for a sensei, which
# is why the county magistracy draws a practice ground and no dojo (buildings.md). It
# supports two kinds, and both are required here:
#   - EXACTLY ONE state PROVINCIAL MARTIAL HALL, inside the walls. Historically the hanko's
#     bugeijo, and hanko were built in castle towns for the domain's own retainers - the
#     tier that seats a governor and ~225 working samurai is the tier that seats the hall.
#     It is its OWN compound, not a wing of the governor's yamen.
#   - PRIVATE dojos, count rolled from the samurai cohort (s.dojos): 1 per full 200 samurai
#     plus a remainder-fraction chance of one extra, floored at 1. A ~3,000 city is ~10%
#     samurai = ~300, so 1 + a 50% roll. Total martial establishments therefore land at 2-3,
#     matching the ~1 per ~100 resident samurai the research put a provincial city at.
# The ARCHERY LANE is the state hall's alone and sits INSIDE its compound wall: 90 ft is the
# kyudo standard 28 m shot (the same clear lane the Mode A azuchi uses), and a private lot
# has no room for it. A recorded roll must match the drawn count, so a stale hand count
# cannot ship - the bathhouse ratchet, applied to a samurai-driven institution.


def _seg_0563_016___mhalls(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.016 (_mhalls) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        _mhalls = M.get("martial_halls", [])
    return _kept(locals(), ('_mhalls',))


def _seg_0563_017___mhwall(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.017 (_mhwall) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        _mhwall = M.get("wall") or []
    return _kept(locals(), ('_mhwall',))


def _seg_0563_018___mhout(*, _mhalls: Any = _UNBOUND, _mhwall: Any = _UNBOUND, mh_: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.018 (_mhout, mh_) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        _mhout = [(round(mh_["x"]), round(mh_["y"])) for mh_ in _mhalls if len(_mhwall) >= 3 and not point_in_poly(mh_["x"], mh_["y"], _mhwall)]
    return _kept(locals(), ('_mhout', 'mh_'))


def _seg_0563_019__city_has_martial_hall(*, _mhalls: Any = _UNBOUND, _mhout: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.019 (city_has_martial_hall) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        check(
            "city_has_martial_hall",
            len(_mhalls) == 1 and not _mhout,
            f"{len(_mhalls)} provincial martial hall(s), outside the walls at {_mhout} - every provincial city keeps "
            f"exactly ONE state martial hall in its own compound inside the rampart (s.martial_hall: the martial wing "
            f"of the provincial school, where the province's youth are schooled and the officer cohort drills; the "
            f"hanko's bugeijo, built in castle towns for the domain's own retainers - a county town has none)",
        )
    return _kept(locals(), ())


# the HANKO's court is deliberately BLANK (synced doctrine, GM 2026-08-09: a real
# hanko is building-dense, so its faithful interior - bugeijo and archery lane
# included - lives on its Mode A sheet); only provincially-drawn halls owe the lane


def _seg_0563_020___mhshort(*, _mhalls: Any = _UNBOUND, mh_: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.020 (_mhshort, mh_) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        _mhshort = [(round(mh_["x"]), round(mh_["y"]), mh_.get("range_ft", 0)) for mh_ in _mhalls if mh_.get("kind") != "hanko" and mh_.get("range_ft", 0) < DOJO_RANGE_FT]
    return _kept(locals(), ('_mhshort', 'mh_'))


def _seg_0563_021__city_martial_hall_has_archery_range(*, _mhshort: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.021 (city_martial_hall_has_archery_range) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        check(
            "city_martial_hall_has_archery_range",
            not _mhshort,
            f"martial hall(s) whose archery lane is shorter than the {DOJO_RANGE_FT:.0f} ft standard shot: {_mhshort} - "
            f"the hall's yard carries a full-length lane with an azuchi butt at its head (kyudo shoots at 28 m / 92 ft), "
            f"drawn inside the compound wall where a shooting lane belongs",
        )
    return _kept(locals(), ())


def _seg_0563_022___cdojos(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.022 (_cdojos) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        _cdojos = M.get("dojos", [])
    return _kept(locals(), ('_cdojos',))


def _seg_0563_023___dj_sam(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.023 (_dj_sam) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        _dj_sam = round((meta.get("population") or 3000) * DOJO_SAMURAI_FRAC)
    return _kept(locals(), ('_dj_sam',))


def _seg_0563_024___dj_floor(*, _dj_sam: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.024 (_dj_floor) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        _dj_floor = max(1, _dj_sam // DOJO_PER_SAMURAI)
    return _kept(locals(), ('_dj_floor',))


def _seg_0563_025___dj_allowed(*, _dj_floor: Any = _UNBOUND, _dj_sam: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.025 (_dj_allowed) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        _dj_allowed = {_dj_floor} if _dj_sam % DOJO_PER_SAMURAI == 0 else {_dj_floor, _dj_floor + 1}
    return _kept(locals(), ('_dj_allowed',))


def _seg_0563_026___dj_roll(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.026 (_dj_roll) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        _dj_roll = meta.get("dojo_roll")
    return _kept(locals(), ('_dj_roll',))


def _seg_0563_027__city_dojo_count_follows_samurai(
    *, _cdojos: Any = _UNBOUND, _dj_allowed: Any = _UNBOUND, _dj_roll: Any = _UNBOUND, _dj_sam: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.027 (city_dojo_count_follows_samurai) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        check(
            "city_dojo_count_follows_samurai",
            len(_cdojos) in _dj_allowed and (_dj_roll is None or len(_cdojos) == _dj_roll),
            f"{len(_cdojos)} private dojo(s) for a ~{_dj_sam}-samurai city (rolled {_dj_roll}) - the count follows the "
            f"GM formula (s.dojos: 1 per full {DOJO_PER_SAMURAI} samurai + a remainder-fraction chance of one extra, "
            f"floored at 1, so ~300 samurai -> 1 + 50% and ~400 -> exactly 2), and a recorded roll must match the drawn "
            f"count. The countryside cohort is deliberately not counted - a city's size already scales with the "
            f"countryside that feeds it",
        )
    return _kept(locals(), ())


def _seg_0563_028___dj_far(*, _cdojos: Any = _UNBOUND, _mhalls: Any = _UNBOUND, b_: Any = _UNBOUND, o_: Any = _UNBOUND, samurai_h: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.028 (_dj_far, b_, o_) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        _dj_far = [(round(o_["x"]), round(o_["y"])) for o_ in _mhalls + _cdojos if not any(math.hypot(o_["x"] - b_["x"], o_["y"] - b_["y"]) < DOJO_QUARTER_PX for b_ in samurai_h)]
    return _kept(locals(), ('_dj_far', 'b_', 'o_'))


def _seg_0563_029__city_dojos_among_samurai(*, _dj_far: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.029 (city_dojos_among_samurai) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        check(
            "city_dojos_among_samurai",
            not _dj_far,
            f"martial hall / dojo(s) with no samurai housing within {DOJO_QUARTER_PX:.0f}px: {_dj_far} - a dojo serves "
            f"samurai and nobody else, so both the state hall and the private halls stand in or against the samurai "
            f"neighborhood, not out among the merchant rows or the laborer warrens",
        )
    return _kept(locals(), ())


def _seg_0563_030__city_has_merchant_district(*, bk: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.030 (city_has_merchant_district) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        check("city_has_merchant_district", bk.get("merchant", 0) >= 12, f"{bk.get('merchant', 0)} merchant houses - a provincial city needs a merchant district")
    return _kept(locals(), ())


def _seg_0563_031__city_has_laborer_neighborhoods(*, bk: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.031 (city_has_laborer_neighborhoods) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        check(
            "city_has_laborer_neighborhoods",
            bk.get("laborer", 0) + bk.get("laborer_large", 0) >= 12,
            f"{bk.get('laborer', 0) + bk.get('laborer_large', 0)} laborer dwellings - a provincial city needs laborer neighborhoods",
        )
    return _kept(locals(), ())


# LABORER HOUSING VARIES BY WEALTH, like the samurai and merchant tiers: budgets.md's provincial-city
# laborer cohort is ~12.5% "master" (rich) laborers, the rest standard - so a MINORITY of larger homes
# (kind "laborer_large", the wealthier hinin who line the prime back-street frontage, with room around
# them) among the overwhelming majority of small standard dwellings. The exact share is room-limited
# (the big homes need street frontage), so the band is generous around the 12.5% target; the point is
# that the variety is PRESENT and a clear minority, not that every laborer dwelling is identical.


def _seg_0563_032__lab_big(*, bk: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.032 (lab_big, lab_std) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        lab_std, lab_big = bk.get("laborer", 0), bk.get("laborer_large", 0)
    return _kept(locals(), ('lab_big', 'lab_std'))


def _seg_0563_033__city_laborer_housing_varied(*, big_frac: Any = _UNBOUND, check: Any = _UNBOUND, lab_big: Any = _UNBOUND, lab_std: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.033 (city_laborer_housing_varied) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and lab_std + lab_big:
        big_frac = lab_big / (lab_std + lab_big)
        check(
            "city_laborer_housing_varied",
            0.06 <= big_frac <= 0.20 and lab_std > lab_big,
            f"laborer houses don't vary by wealth the way budgets.md expects (~12.5% larger 'master/rich' homes, "
            f"the rest standard): {lab_big} large of {lab_std + lab_big} ({big_frac:.0%}; want a clear minority, "
            f"~6-20%) - give the wealthier laborers (the ones fronting the back streets, with room) larger homes "
            f"(kind 'laborer_large')",
        )
    return _kept(locals(), ('big_frac',))


# the city's CASTE MIX must match budgets.md, not just the total head-count: a provincial city is
# ~40% laborer / 20% servant / 25% merchant / 10% samurai / 5% burakumin of its ~600 households.
# The total-population check alone lets the mix DRIFT (e.g. laborers absorbing everyone else's
# slots, servants starved to near-zero because they were appended to the END of a pack list), so
# each caste is held within +/-30% of its target. Servants live among the merchants/samurai they
# serve - INTERLEAVE them into those packs rather than tacking them on the end.


def _seg_0563_034__cpop(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.034 (cpop) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        cpop = meta.get("population", 0)
    return _kept(locals(), ('cpop',))


def _seg_0563_035__city_caste_counts_in_band(
    *,
    M: Any = _UNBOUND,
    bk: Any = _UNBOUND,
    caste: Any = _UNBOUND,
    check: Any = _UNBOUND,
    ck: Any = _UNBOUND,
    cpop: Any = _UNBOUND,
    fr: Any = _UNBOUND,
    frac: Any = _UNBOUND,
    hh: Any = _UNBOUND,
    hi: Any = _UNBOUND,
    k: Any = _UNBOUND,
    lo: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    off: Any = _UNBOUND,
    ratio: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    shifts: Any = _UNBOUND,
    stale: Any = _UNBOUND,
    tgt: Any = _UNBOUND,
    v: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.035 (city_caste_counts_in_band, city_caste_shifts_are_documented, city_caste_shifts_are_live) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and cpop:
        caste = {
            "laborer": bk.get("laborer", 0) + bk.get("laborer_large", 0),
            "servant": bk.get("servant", 0),
            "merchant": bk.get("merchant", 0) + bk.get("merchant_house", 0) + bk.get("merchant_large", 0) + len(M.get("merchant_estates", [])),
            "samurai": bk.get("samurai", 0) + bk.get("samurai_large", 0) + len(M.get("manors", [])),
            "burakumin": bk.get("burakumin", 0),
        }
        frac = {"laborer": 0.40, "servant": 0.20, "merchant": 0.25, "samurai": 0.10, "burakumin": 0.05}
        hh = cpop / HOUSEHOLD
        # A DECLARED CASTE SHIFT (GM 2026-08-05, on Minami's merchants). The generic +/-30% band
        # is a drift guard, and a clan whose economy genuinely differs will sit against its edge
        # for a REASON rather than by drift: Fox temples hold much of the commerce other clans
        # leave to merchants, so Minami's merchant households are fewer and its temple families
        # more. That map was passing at a ratio of exactly 0.700 - one household from a failure
        # whose message would have said "mix is off" and taught the reader nothing.
        # So a shift is DECLARED, the same discipline as a waiver: meta(caste_shifts={caste:
        # reason}) widens that caste's band to +/-45%, and the two meta-checks below keep the
        # hatch honest - the reason must be real prose, and the shift must actually be happening.
        shifts = meta.get("caste_shifts") or {}
        off, stale = [], []
        for ck, fr in frac.items():
            tgt = fr * hh
            ratio = caste[ck] / tgt if tgt else 1.0
            lo, hi = (0.55, 1.45) if ck in shifts else (0.70, 1.30)
            if not (lo <= ratio <= hi):
                off.append(f"{ck} {caste[ck]} (want ~{round(tgt)}{', declared shift' if ck in shifts else ''})")
            elif ck in shifts and 0.80 <= ratio <= 1.20:
                stale.append(f"{ck} sits at {ratio:.2f} of target")
        check(
            "city_caste_counts_in_band",
            not off,
            f"city caste mix is off the budgets.md targets - each caste should be within +/-30% of "
            f"~40% laborer / 20% servant / 25% merchant / 10% samurai / 5% burakumin of {round(hh)} households: {off}"
            f" - if a caste is deliberately shifted by this clan's economy, declare it with meta(caste_shifts=...) and its reason",
        )
        check(
            "city_caste_shifts_are_documented",
            all(isinstance(v, str) and len(v.strip()) >= 60 for v in shifts.values()),
            "a declared caste shift must carry 60+ characters of actual REASON (what about this clan's economy moves "
            f"these households), not True or 'by design': {[k for k, v in shifts.items() if not (isinstance(v, str) and len(v.strip()) >= 60)]}",
        )
        check(
            "city_caste_shifts_are_live",
            not stale,
            f"declared caste shift(s) that are not actually happening: {stale} - a shift within 20% of target is "
            f"ordinary drift, so the declaration is stale and must be dropped rather than left to widen a band nobody needs widened",
        )
    return _kept(locals(), ('caste', 'ck', 'fr', 'frac', 'hh', 'hi', 'k', 'lo', 'off', 'ratio', 'shifts', 'stale', 'tgt', 'v'))


# MERCHANT HOUSING is varied and roomy, UNLIKE the uniform, jammed laborer warren. Behind the
# storefronts the homes mix sizes by wealth band (budgets.md: very rich -> walled ESTATES, rich
# -> LARGE houses, the rest -> small houses) and are SPREAD OUT - more room between them than the
# densely-packed laborers (a few denser merchant blocks are fine; the median is robust to those).
# ROW-PACKING doctrine (GM, 2026-07): city commoner housing is CONTIGUOUS - the
# machiya/nagaya fabric of party walls and touching eaves, not detached-with-yard.
# Real urban commoners packed into terraces (street frontage was taxed and precious;
# a back-lot nagaya was one roof over a row of family units; Chinese county-seat
# courtyard housing shared party walls in continuous street walls). Measured on the
# pre-doctrine Tango: median nearest-neighbor gap was 12px (~31 ft) with ZERO
# touching pairs - a suburb, not a city quarter. Gaps allowed: a hairline seam
# (<=1.2px, touching), the ~3-6 ft eave gap between back-to-back rows, courts,
# and street/roji breaks - but the QUARTER-WIDE stats must read as terraces.


def _seg_0563_036__b_4(*, M: Any = _UNBOUND, b: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.036 (b, rowk) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        rowk = [b for b in M.get("buildings", []) if b.get("kind") in ("laborer", "servant", "burakumin", "merchant_house")]
    return _kept(locals(), ('b', 'rowk'))


def _seg_0563_037__city_row_housing_touches(
    *,
    _egap: Any = _UNBOUND,
    _gaps: Any = _UNBOUND,
    _med: Any = _UNBOUND,
    _touch: Any = _UNBOUND,
    a: Any = _UNBOUND,
    b: Any = _UNBOUND,
    check: Any = _UNBOUND,
    dx: Any = _UNBOUND,
    dy: Any = _UNBOUND,
    g: Any = _UNBOUND,
    i: Any = _UNBOUND,
    j: Any = _UNBOUND,
    rowk: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.037 (city_row_housing_gap, city_row_housing_touches) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and len(rowk) >= 20:

        def _egap(a: dict[str, Any], b: dict[str, Any]) -> float:
            dx = abs(a["x"] - b["x"]) - (a["w"] + b["w"]) / 2
            dy = abs(a["y"] - b["y"]) - (a["h"] + b["h"]) / 2
            return float(max(dx, dy))

        _gaps = sorted(min(_egap(a, b) for j, b in enumerate(rowk) if j != i) for i, a in enumerate(rowk))
        _touch = sum(1 for g in _gaps if g <= 1.2)
        check(
            "city_row_housing_touches",
            _touch >= 0.55 * len(rowk),
            f"only {_touch}/{len(rowk)} row-class dwellings (laborer/servant/burakumin/merchant_house) TOUCH a "
            f"neighbor - city commoner housing is contiguous terraces (party walls), not detached houses",
        )
        _med = _gaps[len(_gaps) // 2]
        check(
            "city_row_housing_gap",
            _med <= 2.0,
            f"median nearest-neighbor edge gap among row-class dwellings is {_med:.1f}px - the quarter reads as scattered houses, not terraces (want <= 2px: a party wall or a ~3-6 ft eave gap)",
        )
    return _kept(locals(), ('_egap', '_gaps', '_med', '_touch', 'a', 'b', 'g', 'i', 'j'))


def _seg_0563_038__b_5(*, M: Any = _UNBOUND, b: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.038 (b, mlarge) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        mlarge = [b for b in M.get("buildings", []) if b.get("kind") == "merchant_large"]
    return _kept(locals(), ('b', 'mlarge'))


def _seg_0563_039__b_6(*, M: Any = _UNBOUND, b: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.039 (b, msmall) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        msmall = [b for b in M.get("buildings", []) if b.get("kind") == "merchant_house"]
    return _kept(locals(), ('b', 'msmall'))


def _seg_0563_040__mest(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.040 (mest) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        mest = M.get("merchant_estates", [])
    return _kept(locals(), ('mest',))


# DRAWN COMPOUND COUNT MATCHES THE ROLL (GM 2026-07-23, mirroring torii_match_roll): a
# walled/gated compound is a PRIVILEGE explicitly granted to a merchant family - most very
# rich merchants can afford one but lack the legal standing to build it (the Edo pattern of
# individually granted merchant rights: a New Year's audience with the daimyo, a hereditary
# surname, etc. - see MERCHANT_ESTATE_WEIGHTS in settlement.py and settlements.md). The gen
# rolls 1-3 grants per city (30/40/30, seeded on the map seed), records the target in
# meta['merchant_estate_roll'], and this gates drawn == target - so the pre-roll state
# (both cities hand-coding exactly 1, a copied pattern) can never silently return.


def _seg_0563_041___mroll(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.041 (_mroll) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        _mroll = meta.get("merchant_estate_roll")
    return _kept(locals(), ('_mroll',))


def _seg_0563_042__merchant_estates_match_roll(*, _mroll: Any = _UNBOUND, check: Any = _UNBOUND, mest: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.042 (merchant_estates_match_roll) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and _mroll is not None:
        check(
            "merchant_estates_match_roll",
            len(mest) == _mroll,
            f"{len(mest)} walled merchant estate(s) drawn but the seeded roll granted {_mroll} - place exactly the rolled count "
            f"(the merchant_estates() seat list must carry enough vetted seats; pin with count= only with a recorded reason)",
        )
    return _kept(locals(), ())


def _seg_0563_043__city_merchant_housing_varied(
    *,
    M: Any = _UNBOUND,
    b: Any = _UNBOUND,
    check: Any = _UNBOUND,
    homes: Any = _UNBOUND,
    i: Any = _UNBOUND,
    j: Any = _UNBOUND,
    labor: Any = _UNBOUND,
    lh: Any = _UNBOUND,
    med_nn: Any = _UNBOUND,
    mest: Any = _UNBOUND,
    mh: Any = _UNBOUND,
    mlarge: Any = _UNBOUND,
    msmall: Any = _UNBOUND,
    p: Any = _UNBOUND,
    pts: Any = _UNBOUND,
    q: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.043 (city_merchant_housing_spread, city_merchant_housing_varied) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and (mlarge or msmall):  # a merchant district whose homes are drawn
        check(
            "city_merchant_housing_varied",
            len(mest) >= 1 and len(mlarge) >= 3 and len(msmall) >= 1,
            f"merchant housing lacks variety (walled estates={len(mest)}, large houses={len(mlarge)}, small houses={len(msmall)}) - "
            f"a merchant quarter mixes small/average houses, LARGE (rich) houses and a few WALLED ESTATES, not one uniform size",
        )
        homes = [(b["x"], b["y"]) for b in mlarge + msmall]
        labor = [(b["x"], b["y"]) for b in M.get("buildings", []) if b.get("kind") == "laborer"]
        if len(homes) >= 5 and len(labor) >= 5:

            def med_nn(pts: Sequence[Pt]) -> float:
                nn = sorted(min(math.hypot(p[0] - q[0], p[1] - q[1]) for j, q in enumerate(pts) if j != i) for i, p in enumerate(pts))
                return nn[len(nn) // 2]

            mh, lh = med_nn(homes), med_nn(labor)
            check(
                "city_merchant_housing_spread",
                mh >= 1.3 * lh,
                f"merchant homes are not more SPREAD OUT than the laborers (median neighbor gap {mh:.0f}px vs laborer {lh:.0f}px; want >= 1.3x) - "
                f"give merchant houses more room between them; the laborer warren is the dense, uniform contrast",
            )
    return _kept(locals(), ('b', 'homes', 'labor', 'lh', 'med_nn', 'mh'))


# CAPITAL-INVERTED (021): a capital is fed BY THE RIVER, not its outskirts - the whole
# wharf/granary doctrine (stipend rice arrives from the six provinces by boat, and the
# frame shows that supply chain: wharf, granaries, towpath), and its sheet frames only
# the walled city and its suburbs. A provincial city's identity IS its farm country, so
# the comb stays mandatory there. (capitals.md; audit 2026-08-10)


def _seg_0563_044__city_has_outside_farmland(*, check: Any = _UNBOUND, f: Any = _UNBOUND, fields: Any = _UNBOUND, runs_off_edge: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.044 (city_has_outside_farmland) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and scale == "city":
        check(
            "city_has_outside_farmland",
            bool([f for f in fields if runs_off_edge(f["outline"])]),
            "a city has extensive farmland outside its walls - at least one field must run off the map edge",
        )
    return _kept(locals(), ('f',))
