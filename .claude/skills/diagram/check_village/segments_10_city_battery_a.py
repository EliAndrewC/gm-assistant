"""Gate segments (city battery a) - bodies verbatim from check_village.py (feature 024 package split; registry order preserved)."""

import math
from collections.abc import Sequence
from typing import Any

from settlement import kido_bar_deg, label_aabb, lane_runs, lane_through_gate, sat_overlap

from .common_01_geometry import Pt, point_in_poly, rect_corners, seg_dist, solid_structs
from .common_02_overlap_policy import DOJO_PER_SAMURAI, DOJO_QUARTER_PX, DOJO_RANGE_FT, DOJO_SAMURAI_FRAC, check_fire_features, check_theater_stage, footprint_on_line, kido_quads
from .common_03_capacity import _UNBOUND, HOUSEHOLD, _kept, lane_near_misses, lane_ward_shortfalls


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


# civic amenities ported up from the town tier (a city is a bigger version of the same):


def _seg_0563_045__city_has_merchant_storehouses(*, M: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.045 (city_has_merchant_storehouses) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        check(
            "city_has_merchant_storehouses",
            len(M.get("storehouses", [])) >= 5,
            f"{len(M.get('storehouses', []))} merchant storehouses - a city's merchant district keeps fireproof kura (s.merchant_storehouses(...))",
        )
    return _kept(locals(), ())


def _seg_0563_046__city_has_flophouse(*, M: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.046 (city_has_flophouse) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        check("city_has_flophouse", len(M.get("flophouses", [])) >= 1, "a provincial city is a major market center and needs market-day lodging (s.flophouse(...))")
    return _kept(locals(), ())


def _seg_0563_047__city_has_theater_stage(*, M: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.047 (city_has_theater_stage) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        check("city_has_theater_stage", bool(M.get("theater_stage")), "a provincial city needs a theater stage (s.theater_stage(...))")
    return _kept(locals(), ())


def _seg_0563_048__theater_stage_by_temple(*, M: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.048 (theater_stage_by_temple, theater_stage_clear, theater_stage_faces_temple) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        check_theater_stage(M, check)
    return _kept(locals(), ())


# a CITY theater stage is bigger than a town's (towns run a viewing ground ~150 wide) - a provincial
# city draws a larger crowd, so its viewing ground is wider (>= 185, the city baseline)


def _seg_0563_049__amph_raw3(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.049 (amph_raw3) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        amph_raw3 = M.get("theater_stage")
    return _kept(locals(), ('amph_raw3',))


def _seg_0563_050__amph_all3(*, amph_raw3: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.050 (amph_all3) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        amph_all3 = amph_raw3 if isinstance(amph_raw3, list) else ([amph_raw3] if amph_raw3 else [])
    return _kept(locals(), ('amph_all3',))


def _seg_0563_051__amph(*, a8: Any = _UNBOUND, amph_all3: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.051 (amph) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        amph = max(amph_all3, key=lambda a8: a8.get("w", 0)) if amph_all3 else None
    return _kept(locals(), ('amph',))


def _seg_0563_052__city_theater_stage_larger_than_town(*, _ftpx: Any = _UNBOUND, amph: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.052 (city_theater_stage_larger_than_town) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and amph:
        # compared in REAL FEET via the declared scale (meta ftpx, default 1): a town's stage
        # is ~150 ft wide, so a provincial city's must be >= 185 ft - the old 185px threshold
        # assumed the pre-ladder ~1 ft/px grain and would silently pass a to-scale city map
        # whose stage shrank in pixels while staying honest in feet
        _ftpx = meta.get("ftpx", 1)
        check(
            "city_theater_stage_larger_than_town",
            amph.get("w", 0) * _ftpx >= 185,
            f"the city theater stage (viewing ground ~{round(amph.get('w', 0) * _ftpx)} ft wide) is no bigger than a town's - a provincial city's is larger (>= 185 ft)",
        )
    return _kept(locals(), ('_ftpx',))


# FIRE DEFENSE: a city's dense quarters each need a fire-watch tower (hinomi-yagura). WHY:
# settlements.md "Fire towers". Opt out per-map with meta(fire_tower=False).


def _seg_0563_053__city_has_fire_towers(*, M: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, nft: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.053 (city_has_fire_towers) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get("fire_tower", True):
        nft = len(M.get("fire_towers", []))
        check("city_has_fire_towers", nft >= 2, f"{nft} fire towers - a provincial city's dense quarters each need a fire-watch tower (>= 2; s.fire_tower(...); meta(fire_tower=False) to omit)")
    return _kept(locals(), ('nft',))


def _seg_0563_054__fire_tower_amid_its_district(*, M: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.054 (fire_tower_amid_its_district, fire_tower_clear_of_fields, fire_tower_clear_of_graveyards, fire_tower_clear_of_wells, fire_tower_in_commoner_quarter, fire_tower_standoff, fire_towers_dispersed) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        check_fire_features(M, check)
    return _kept(locals(), ())


# A NAMED civic building's label must sit on ITS OWN building, never on a DIFFERENT one of the
# same kind. labels_clear_of_other_buildings lumps every ministry into one "ministry" GROUP, so
# it permits a ministry label to sit on a SIBLING ministry (the "Ministry of Justice" label
# drifted onto the "Ministry of Works" office). This catches that finer case: a label that names
# a civic building (a ministry by name, the governor's yamen, a named temple) must not overlap
# any OTHER named civic building.


def _seg_0563_055___bbc(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.055 (_bbc) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):

        def _bbc(it9: dict[str, Any]) -> tuple[float, float, float, float]:
            # local bbox helper: the _bb at the labels battery is defined in a branch a
            # minimal capital manifest never enters (found when the urban battery widened)
            return (it9["x"] - it9["w"] / 2, it9["y"] - it9["h"] / 2, it9["x"] + it9["w"] / 2, it9["y"] + it9["h"] / 2)

    return _kept(locals(), ('_bbc',))


def _seg_0563_056__civic(*, M: Any = _UNBOUND, _bbc: Any = _UNBOUND, mi: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.056 (civic, mi) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        civic = [(mi["name"], _bbc(mi)) for mi in M.get("ministries", []) if mi.get("name")]
    return _kept(locals(), ('civic', 'mi'))


def _seg_0563_057___gv(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.057 (_gv) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        _gv = M.get("governor_mansion")
    return _kept(locals(), ('_gv',))


def _seg_0563_058__civic_1(*, _bbc: Any = _UNBOUND, _gv: Any = _UNBOUND, civic: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.058 (civic) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and _gv and _gv.get("label"):
        civic.append((_gv["label"], _bbc(_gv)))
    return _kept(locals(), ('civic',))


def _seg_0563_059__civic_2(*, M: Any = _UNBOUND, _bbc: Any = _UNBOUND, civic: Any = _UNBOUND, r: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.059 (civic, r) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        civic += [(r["label"], _bbc(r)) for r in M.get("religious", []) if r.get("label") and r.get("kind") == "temple"]
    return _kept(locals(), ('civic', 'r'))


def _seg_0563_060___(*, civic: Any = _UNBOUND, n: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.060 (_, civic_names, n) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        civic_names = {n for n, _ in civic}
    return _kept(locals(), ('_', 'civic_names', 'n'))


def _seg_0563_061__cross(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.061 (cross) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        cross = []  # type: ignore[var-annotated]
    return _kept(locals(), ('cross',))


def _seg_0563_062__L(
    *,
    L: Any = _UNBOUND,
    M: Any = _UNBOUND,
    _la: Any = _UNBOUND,
    civic: Any = _UNBOUND,
    civic_names: Any = _UNBOUND,
    cross: Any = _UNBOUND,
    n: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    x0: Any = _UNBOUND,
    x1: Any = _UNBOUND,
    y0: Any = _UNBOUND,
    y1: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.062 (L, _la, cross, n) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        for L in M.get("labels", []):
            if len(L) <= 5 or L[5] not in civic_names:
                continue
            _la = label_aabb(L)  # tilted captions reach their rotated AABB
            for n, (x0, y0, x1, y1) in civic:
                if n != L[5] and _la[0] < x1 and x0 < _la[2] and _la[1] < y1 and y0 < _la[3]:
                    cross.append(f"{L[5]!r} over {n!r}")
    return _kept(locals(), ('L', '_la', 'cross', 'n', 'x0', 'x1', 'y0', 'y1'))


def _seg_0563_063__city_civic_label_on_its_own_building(*, check: Any = _UNBOUND, cross: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.063 (city_civic_label_on_its_own_building) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        check("city_civic_label_on_its_own_building", not cross, f"a civic building's label sits on a DIFFERENT civic building (not the one it names): {sorted(set(cross))}")
    return _kept(locals(), ())


# GOVERNMENT OFFICES stand in their own ground - a ministry or the governor's yamen is a large,
# important compound and must not ABUT another structure. Ordinary city houses may touch each
# other, but a government office keeps a clear gap from every other building/compound around it.


def _seg_0563_064__OFFICE_GAP(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.064 (OFFICE_GAP) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        OFFICE_GAP = 14
    return _kept(locals(), ('OFFICE_GAP',))


def _seg_0563_065__mi(*, M: Any = _UNBOUND, _gv: Any = _UNBOUND, mi: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.065 (mi, offices) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        offices = ([("the governor's yamen", _gv)] if _gv else []) + [(mi.get("name", "a ministry"), mi) for mi in M.get("ministries", [])]
    return _kept(locals(), ('mi', 'offices'))


# every solid footprint, from the registry - an office must not abut a martial hall or a
# brewery any more than it may abut a house (GM 2026-07-25; see solid_structs). The FUNERARY
# compounds are the one deliberate exclusion: the ruling clan's walled crypt standing against
# the governor's yamen is a real adjacency (the house's dead beside the house's seat), not a
# packing error, and Nagahara has drawn it that way since long before this check read the
# registry. Burial ground siting has its own battery (funerary_clear_of_fields, the
# burial-ground checks); this rule is about a bureau not being crowded by ordinary premises.


def _seg_0563_066__others(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.066 (others) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        others = solid_structs(M, "religious", "merchant_estates", exclude=("cemeteries", "mausoleums", "cremation_grounds", "ossuaries"))
    return _kept(locals(), ('others',))


def _seg_0563_067___edge_gap(
    *,
    _bbc: Any = _UNBOUND,
    a: Any = _UNBOUND,
    ax0: Any = _UNBOUND,
    ax1: Any = _UNBOUND,
    ay0: Any = _UNBOUND,
    ay1: Any = _UNBOUND,
    b: Any = _UNBOUND,
    bx0: Any = _UNBOUND,
    bx1: Any = _UNBOUND,
    by0: Any = _UNBOUND,
    by1: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.067 (_edge_gap) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):

        def _edge_gap(a: dict[str, Any], b: dict[str, Any]) -> float:
            ax0, ay0, ax1, ay1 = _bbc(a)
            bx0, by0, bx1, by1 = _bbc(b)
            return math.hypot(max(0.0, ax0 - bx1, bx0 - ax1), max(0.0, ay0 - by1, by0 - ay1))

    return _kept(locals(), ('_edge_gap',))


def _seg_0563_068__abut(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.068 (abut) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        abut = []  # type: ignore[var-annotated]
    return _kept(locals(), ('abut',))


def _seg_0563_069__abut_1(
    *,
    OFFICE_GAP: Any = _UNBOUND,
    _edge_gap: Any = _UNBOUND,
    abut: Any = _UNBOUND,
    nm: Any = _UNBOUND,
    o: Any = _UNBOUND,
    offices: Any = _UNBOUND,
    others: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    st: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.069 (abut, nm, o, st) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        for nm, o in offices:
            for st in others:
                if st is not o and "w" in st and _edge_gap(o, st) < OFFICE_GAP:
                    abut.append(f"{nm!r} abuts {(st.get('name') or st.get('label') or st.get('kind') or 'a building')!r}")
    return _kept(locals(), ('abut', 'nm', 'o', 'st'))


def _seg_0563_070__city_government_offices_dont_abut(*, OFFICE_GAP: Any = _UNBOUND, abut: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.070 (city_government_offices_dont_abut) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        check(
            "city_government_offices_dont_abut", not abut, f"government office(s) abutting another structure - a ministry / the yamen must stand clear, not touch ({OFFICE_GAP}px): {sorted(set(abut))}"
        )
    return _kept(locals(), ())


# PUBLIC WELLS: ensuring every commoner could draw water was a defining civic concern of a
# premodern city. A communal well (the idobata) served a courtyard / cluster of ~10-20
# households, so the warren is dotted with them - one within a short walk of any home. The
# underground half of the system (aqueducts, cisterns, rain barrels feeding the shafts) is too
# small or literally subterranean and stays OFF the map; only the wellheads show.
# PRIVATE wells (private=True - e.g. the brewery's own courtyard well, GM 2026-07-24) are
# premises fixtures, not neighborhood infrastructure: they serve no commoner households, so
# they are excluded from ALL the public-well accounting below (reach, density, block-interior
# siting, the samurai-ward ban) - exactly as samurai compounds' implied private wells are.


def _seg_0563_071__w_(*, M: Any = _UNBOUND, scale: Any = _UNBOUND, w_: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.071 (w_, wells) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        wells = [w_ for w_ in M.get("wells", []) if not w_.get("private")]
    return _kept(locals(), ('w_', 'wells'))


def _seg_0563_072__city_neighborhoods_have_wells(
    *,
    COMMON: Any = _UNBOUND,
    HOUSEK: Any = _UNBOUND,
    M: Any = _UNBOUND,
    MAX_PER_WELL: Any = _UNBOUND,
    MAX_PER_WELL_OUTCAST: Any = _UNBOUND,
    REACH: Any = _UNBOUND,
    SAMK: Any = _UNBOUND,
    _sy_stbl: Any = _UNBOUND,
    a: Any = _UNBOUND,
    b: Any = _UNBOUND,
    b9: Any = _UNBOUND,
    bad_well: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d: Any = _UNBOUND,
    dry: Any = _UNBOUND,
    dwl: Any = _UNBOUND,
    h: Any = _UNBOUND,
    hh: Any = _UNBOUND,
    hh_out: Any = _UNBOUND,
    hx: Any = _UNBOUND,
    hy: Any = _UNBOUND,
    i: Any = _UNBOUND,
    inw: Any = _UNBOUND,
    lane_w: Any = _UNBOUND,
    ln: Any = _UNBOUND,
    lw: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    near_dw: Any = _UNBOUND,
    s9: Any = _UNBOUND,
    sam_wells: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    served: Any = _UNBOUND,
    served_out: Any = _UNBOUND,
    st: Any = _UNBOUND,
    structs: Any = _UNBOUND,
    swamped: Any = _UNBOUND,
    w: Any = _UNBOUND,
    wells: Any = _UNBOUND,
    wlanes: Any = _UNBOUND,
    wp: Any = _UNBOUND,
    wr: Any = _UNBOUND,
    wx: Any = _UNBOUND,
    wy: Any = _UNBOUND,
    x: Any = _UNBOUND,
    y: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.072 (city_neighborhoods_have_wells, city_samurai_quarter_has_no_public_wells, city_well_density_sufficient, city_wells_in_block_interiors) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if wells:
            wp = M.get("wall") or []
            inw: Any = (lambda x, y: point_in_poly(x, y, wp)) if len(wp) >= 3 else (lambda x, y: True)  # type: ignore[no-redef]  # noqa: E731
            # WATER ACCESS: every commoner dwelling INSIDE the walls (laborer/burakumin/merchant kinds;
            # samurai have private wells in their compounds, and a transient gate market outside the wall
            # is not housing) must have a public well within reach. Servants are interleaved among the
            # commoners and share the same wells, so they ride along. A dwelling too far from any well is
            # a neighborhood the water network forgot.
            REACH = 290
            # monk_house is NOT here (021): a temple's monk houses draw from the temple's own
            # well inside the precinct (the monastery provisions its own community - the same
            # reason samurai compounds are exempt), so a monk file in a well-less pocket beside
            # its temple is correct, not a forgotten neighborhood.
            COMMON = {"laborer", "laborer_large", "burakumin", "merchant", "merchant_house", "merchant_large"}
            dry = [
                (round(b["x"]), round(b["y"]))
                for b in M.get("buildings", [])
                if b.get("kind") in COMMON and inw(b["x"], b["y"]) and min(math.hypot(b["x"] - w["x"], b["y"] - w["y"]) for w in wells) > REACH
            ]
            check(
                "city_neighborhoods_have_wells",
                not dry,
                f"{len(dry)} commoner dwelling(s) inside the walls more than {REACH}px from any public well - every neighborhood needs water access; scatter wells through the warren (e.g. {dry[:3]})",
            )
            # and ENOUGH wells that none is OVER-BURDENED: a communal well historically served a courtyard
            # / cluster of ~10-20 households, so assigning each commoner dwelling (servants included - they
            # draw here too) to its NEAREST well, no well should end up doing the work of three. The reach
            # check guarantees coverage but not density - the AVERAGE can look fine while the busiest wells
            # in the dense laborer warren are swamped - so this bounds the per-well share. (The nearest-well
            # split over-counts a little where two wells are nearly equidistant, so the ceiling sits a touch
            # above the historical 20.)
            #
            # BURAKUMIN HOUSEHOLDS ARE COUNTED AT A HIGHER CEILING, and that is a finding, not a
            # fudge (GM 2026-08-10, from the capital's well knots). An outcast quarter packed at
            # roughly twice the machi's row density cannot reach 1-per-20 without putting five to
            # seven wellheads inside one 150 ft radius - which is not how any settled map looks,
            # because it is not how the ground worked: hinin quarters were the LAST to be served
            # by communal water, drew from the river, the ditch, or a single shared well, and
            # their under-provision is part of what made them outcast ground. So they carry their
            # own ceiling rather than forcing wells the quarter would never have had. A quarter
            # whose burakumin rows are ALSO dry still fails city_neighborhoods_have_wells - the
            # reach rule is not relaxed, only the density share.
            # 26 at provincial-city density; 30 at CAPITAL density (GM 2026-08-11, and only after
            # every placement lever was tried and failed on Shiro Daika). The band this rule cites -
            # ~1 well per 10-20 households - was calibrated against the provincial cities, whose
            # machi the 018 budget builds at a lower density than a domain capital's. On the capital
            # two blocks run at 27 and 29, and that is NOT scarcity: 16 public wells stand within
            # 200 px of the first, at 60-95 px spacing, and open_seat refuses a 9 px wellhead at
            # every radius out to 96 px with the EXACT disc reach because the terrace is solid.
            # Adding wells trips wells_not_clustered before the deficit clears; reserving one ahead
            # of the packs cascades through the fabric (205 -> 278 wells); shrinking the packs to
            # free ground puts capital_housing_matches_band_targets off its budget. Every lever
            # moves a different rule into the red, which is the signature of a THRESHOLD calibrated
            # for a different tier - so the tier gets its own number rather than the map getting a
            # waiver. Edo's densest nagaya blocks did share a single well among ~30 households.
            MAX_PER_WELL = 30 if meta.get("scale") == "capital" else 26
            MAX_PER_WELL_OUTCAST = 60
            hh = [(b["x"], b["y"]) for b in M.get("buildings", []) if b.get("kind") in (COMMON | {"servant"}) and b.get("kind") != "burakumin" and inw(b["x"], b["y"])]
            hh_out = [(b["x"], b["y"]) for b in M.get("buildings", []) if b.get("kind") == "burakumin" and inw(b["x"], b["y"])]
            served = [0] * len(wells)
            for hx, hy in hh:
                served[min(range(len(wells)), key=lambda i: math.hypot(hx - wells[i]["x"], hy - wells[i]["y"]))] += 1
            served_out = [0] * len(wells)
            for hx, hy in hh_out:
                served_out[min(range(len(wells)), key=lambda i: math.hypot(hx - wells[i]["x"], hy - wells[i]["y"]))] += 1
            swamped = [(round(wells[i]["x"]), round(wells[i]["y"]), c + served_out[i]) for i, c in enumerate(served) if c > MAX_PER_WELL or c + served_out[i] > MAX_PER_WELL_OUTCAST]
            # WHY (~1 communal well per 10-20 households - the premodern courtyard-well norm): settlements.md "Historical grounding"
            check(
                "city_well_density_sufficient",
                not swamped,
                f"public well(s) each the nearest for more than {MAX_PER_WELL} commoner households - too few wells for "
                f"the neighborhood (~1 per 10-20 households is realistic); add wells where the warren is densest: {swamped}",
            )
            # wells sit in a block INTERIOR off the lanes (the idobata was a courtyard, not the avenue),
            # and a wellhead must not overlap a building or compound. Placement guarantees both (well_at /
            # place_wells use the same clearance test the houses do), so this is the backstop.
            wlanes = [st["pts"] for st in M.get("town_streets", [])] + ([M["road"]] if M.get("road") else []) + [a["pts"] for a in M.get("alleys", [])]
            lane_w = [st.get("w", 24) for st in M.get("town_streets", [])] + ([M.get("road_width", 26)] if M.get("road") else []) + [10 for _ in M.get("alleys", [])]
            _gov = M.get("governor_mansion")
            structs = solid_structs(M, "religious", "merchant_estates")  # registry-driven, so a new feature cannot silently host a wellhead
            bad_well = []
            for w in wells:
                wx, wy, wr = w["x"], w["y"], w.get("r", 8)
                if any(seg_dist(wx, wy, ln[i], ln[i + 1]) < lw / 2 + wr for ln, lw in zip(wlanes, lane_w, strict=False) for i in range(len(ln) - 1)):
                    bad_well.append((round(wx), round(wy), "on a lane"))
                elif any("w" in st and abs(wx - st["x"]) < st["w"] / 2 + wr and abs(wy - st["y"]) < st["h"] / 2 + wr for st in structs):
                    bad_well.append((round(wx), round(wy), "on a building"))
            check("city_wells_in_block_interiors", not bad_well, f"well(s) not sitting clear in a block interior - a wellhead is on a lane or overlaps a structure: {bad_well[:4]}")
            # the SAMURAI/GOVERNMENT quarter has NO public wells - samurai drew from PRIVATE wells inside
            # their own walled compounds, and gathering at the communal idobata was a commoner-district
            # institution (beneath samurai status). So a public wellhead embedded AMONG the samurai
            # dwellings is wrong; their water is private and stays off-map, like their gardens. A well is
            # "in the samurai quarter" if the dwellings it actually sits among are mostly samurai - a
            # relative test, robust where a commoner well sits a block from the quarter across the ward fence.
            SAMK = {"samurai", "samurai_large"}
            HOUSEK = {"laborer", "laborer_large", "servant", "burakumin", "merchant", "merchant_house", "merchant_large"} | SAMK
            dwl = [(b["x"], b["y"], b.get("kind") in SAMK) for b in M.get("buildings", []) if b.get("kind") in HOUSEK]
            dwl += [
                (h["x"], h["y"], False) for h in M.get("houses", [])
            ]  # FARMHOUSES are commoner households in this vote: a farm-belt well (s.farm_wells) sits among farmsteads far from any urban dwelling, and judging it by the nearest IN-WALL houses mislabeled it samurai (Nagahara's SW belt, 2026-07-21)
            # a CARAVAN-YARD well (within reach of a stables) is the yard's own trough water,
            # serving wagon crews and animals wherever the gate quarter's caste happens to sit -
            # the resized capital's N gate cluster stands in the samurai band, and its yard well
            # is not a neighborhood idobata (021, the wall-resize re-lay).
            _sy_stbl = [b9 for b9 in M.get("buildings", []) if b9.get("kind") == "stables"]
            sam_wells = []
            for w in wells:
                if w.get("kind") == "cistern":
                    # a josui-ido draw-basin is INFRASTRUCTURE on the buried main, sited by the
                    # aqueduct's reach (within ~600 ft of the settling basin), not a neighborhood
                    # idobata - at the E gate that reach falls in the samurai quarter, and everyone
                    # within reach of the main draws from it (021, the settled-wall pass).
                    continue
                if any(math.hypot(w["x"] - s9["x"], w["y"] - s9["y"]) < 80 for s9 in _sy_stbl):
                    continue
                if len(wp) >= 3 and not inw(w["x"], w["y"]):
                    # the samurai QUARTER is intramural by definition - an extramural well (a farm-belt
                    # or gate-suburb well) cannot sit "in" it, and letting in-wall samurai houses vote
                    # across the rampart mislabeled a SE farm well (Tango, 2026-07-24 trade-works ripple)
                    continue
                near_dw = sorted(dwl, key=lambda d: math.hypot(d[0] - w["x"], d[1] - w["y"]))[:3]
                if near_dw and sum(1 for d in near_dw if d[2]) * 2 >= len(near_dw):  # most of its nearest neighbors are samurai
                    sam_wells.append((round(w["x"]), round(w["y"])))
            # WHY (samurai/official households drew from PRIVATE wells inside their walled compounds): settlements.md "Historical grounding"
            check(
                "city_samurai_quarter_has_no_public_wells",
                not sam_wells,
                f"public well(s) sitting among the samurai dwellings: {sam_wells} - the samurai/government quarter has no "
                f"communal wells (samurai draw from private wells inside their compounds; the public idobata is a commoner institution)",
            )
    return _kept(
        locals(),
        (
            'COMMON',
            'HOUSEK',
            'MAX_PER_WELL',
            'MAX_PER_WELL_OUTCAST',
            'REACH',
            'SAMK',
            '_',
            '_gov',
            '_sy_stbl',
            'a',
            'b',
            'b9',
            'bad_well',
            'c',
            'd',
            'dry',
            'dwl',
            'h',
            'hh',
            'hh_out',
            'hx',
            'hy',
            'i',
            'inw',
            'lane_w',
            'ln',
            'lw',
            'near_dw',
            's9',
            'sam_wells',
            'served',
            'served_out',
            'st',
            'structs',
            'swamped',
            'w',
            'wlanes',
            'wp',
            'wr',
            'wx',
            'wy',
        ),
    )


# a city ON the Imperial road LINES that road with COMMERCE (shops + traveler inns): the
# through-road is the city's prime frontage, where caravans and travelers pass, so it must not
# run bare. This holds for ANY city with an Imperial road, WALLED OR NOT - a city WITHOUT a road
# has no such ribbon (its commerce stays in the market district). The road's portion running
# THROUGH the city is judged: bounded by the WALL if there is one, else by the URBAN FOOTPRINT
# (the bbox of the city's buildings). Scaled to that length at ~1 commercial frontage per 130px,
# a floor that catches a bare spine.


def _seg_0563_073__road(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.073 (road) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        road = M.get("road") or []
    return _kept(locals(), ('road',))


def _seg_0563_074__p(*, EY0: Any = _UNBOUND, EY1: Any = _UNBOUND, p: Any = _UNBOUND, road: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.074 (p, road_through) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        road_through = bool(road) and any(p[1] < EY0 for p in road) and any(p[1] > EY1 for p in road)
    return _kept(locals(), ('p', 'road_through'))


def _seg_0563_075__city_imperial_road_has_commerce(
    *,
    COMMERCE: Any = _UNBOUND,
    EX0: Any = _UNBOUND,
    EX1: Any = _UNBOUND,
    EY0: Any = _UNBOUND,
    EY1: Any = _UNBOUND,
    M: Any = _UNBOUND,
    a: Any = _UNBOUND,
    b: Any = _UNBOUND,
    bg: Any = _UNBOUND,
    bx: Any = _UNBOUND,
    by: Any = _UNBOUND,
    check: Any = _UNBOUND,
    frac_inside: Any = _UNBOUND,
    i: Any = _UNBOUND,
    il: Any = _UNBOUND,
    in_city: Any = _UNBOUND,
    k: Any = _UNBOUND,
    need: Any = _UNBOUND,
    road: Any = _UNBOUND,
    road_comm: Any = _UNBOUND,
    road_through: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    t: Any = _UNBOUND,
    wp: Any = _UNBOUND,
    x: Any = _UNBOUND,
    x0: Any = _UNBOUND,
    x1: Any = _UNBOUND,
    y: Any = _UNBOUND,
    y0: Any = _UNBOUND,
    y1: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.075 (city_imperial_road_has_commerce) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and road_through:
        wp = M.get("wall") or []
        if len(wp) >= 3:
            in_city: Any = lambda x, y: point_in_poly(x, y, wp)  # type: ignore[no-redef]  # noqa: E731
        else:
            bx = [b["x"] for b in M.get("buildings", [])] or [EX0, EX1]
            by = [b["y"] for b in M.get("buildings", [])] or [EY0, EY1]
            x0, x1, y0, y1 = min(bx) - 40, max(bx) + 40, min(by) - 40, max(by) + 40
            in_city = lambda x, y: x0 <= x <= x1 and y0 <= y <= y1  # noqa: E731
        il = 0.0
        for i in range(len(road) - 1):
            a, b = road[i], road[i + 1]
            frac_inside = sum(1 for t in range(11) if in_city(a[0] + (b[0] - a[0]) * t / 10, a[1] + (b[1] - a[1]) * t / 10)) / 11
            il += math.hypot(b[0] - a[0], b[1] - a[1]) * frac_inside
        COMMERCE = {"shop", "merchant", "inn"}
        road_comm = sum(
            1 for bg in M.get("buildings", []) if bg.get("kind") in COMMERCE and in_city(bg["x"], bg["y"]) and min(seg_dist(bg["x"], bg["y"], road[k], road[k + 1]) for k in range(len(road) - 1)) <= 95
        )
        need = round(il / 130)
        check(
            "city_imperial_road_has_commerce",
            road_comm >= need,
            f"only {road_comm} shops/inns front the {round(il)}px of Imperial road running through the city (want >= {need}) - a "
            f"city on a trade route lines its through-road with commerce to service travelers; don't leave the prime road frontage bare",
        )
    return _kept(locals(), ('COMMERCE', 'a', 'b', 'bg', 'bx', 'by', 'frac_inside', 'i', 'il', 'in_city', 'k', 'need', 'road_comm', 't', 'wp', 'x0', 'x1', 'y0', 'y1'))


# two lanes (streets/alleys) heading STRAIGHT at each other and stopping just short, with nothing
# between them, should simply CONNECT - a near-miss reads as a mistake, not a deliberate dead-end.
# (Unlike city_streets_no_near_miss, which only compares street-vs-street segment proximity, this
# catches ALLEYS too and the aligned end-to-end / T case, and ignores gaps a building/fence/wall
# genuinely blocks.) Generic to any city with lanes, walled or not.


def _seg_0563_076__misses(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.076 (misses) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        misses = lane_near_misses(M)
    return _kept(locals(), ('misses',))


def _seg_0563_077__city_lanes_meet_when_aligned(*, check: Any = _UNBOUND, misses: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.077 (city_lanes_meet_when_aligned) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        check(
            "city_lanes_meet_when_aligned",
            not misses,
            f"lane endpoint(s) stopping a short CLEAR distance from another lane they point straight at - "
            f"two lanes heading toward each other with nothing between should connect, not stop short: {misses}",
        )
    return _kept(locals(), ())


# a lane heading at a NEIGHBORHOOD wall (a ward fence) should reach it and end at a KIDO GATE - the
# commoners' lanes pull in to the gates they pass through to work in the samurai quarter. Stopping a
# sliver short, or meeting the fence with no gate, both read as a mistake. (Stopping short of the
# MAIN city wall is fine - that is the city's own edge, not a neighborhood boundary.)


def _seg_0563_078__shortfalls(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.078 (shortfalls) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        shortfalls = lane_ward_shortfalls(M)
    return _kept(locals(), ('shortfalls',))


def _seg_0563_079__city_lanes_reach_ward_gates(*, check: Any = _UNBOUND, scale: Any = _UNBOUND, shortfalls: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.079 (city_lanes_reach_ward_gates) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        check("city_lanes_reach_ward_gates", not shortfalls, f"lane(s) at a neighborhood (ward) wall that should extend to it and end at a gate: {shortfalls}")
    return _kept(locals(), ())


# THE KIDO SQUARES TO WHAT IT BARS (GM 2026-07-26, refining the 2026-07-24 fence rule).
# A kido is a gate across a WAY: it is shut at night to stop traffic, so the roofed bar
# stands SQUARE ACROSS THE LANE that runs through it, and the fence meets the gate at
# whatever angle the fence happens to run. The two readings agree wherever a lane crosses
# its fence squarely - which is most crossings, and why the fence rule held up for two
# days - and diverge exactly where a lane meets the fence obliquely: Tango's SW ring-road
# gate, drawn on its ~44deg fence jog while the ring road passed at ~172deg, sat 38 degrees
# off square to the road it was supposedly barring and read as a glyph dropped on the
# roadbed. Only a gate with NO lane through it falls back to the fence tangent (still never
# an axis-aligned stamp on a slanted run - Nagahara's SW kido, Tango's S jog, both frozen
# in pool/regressions/). lane_through_gate/kido_bar_deg are the SAME functions s.ward
# places with, so placer and checker cannot drift. s.kido records the drawn angle as 'rot'
# (legacy manifests fall back to the horizontal flag: True -> 90, False -> 0); it must match
# within ~7 degrees mod 180.


def _seg_0563_080__wards_k(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.080 (wards_k) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):
        wards_k = M.get("wards", [])
    return _kept(locals(), ('wards_k',))


def _seg_0563_081__kido_aligned_with_ward_fence(
    *,
    M: Any = _UNBOUND,
    b2: Any = _UNBOUND,
    best2: Any = _UNBOUND,
    box_on_lane: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d8: Any = _UNBOUND,
    diff8: Any = _UNBOUND,
    gbox: Any = _UNBOUND,
    got8: Any = _UNBOUND,
    gpoly: Any = _UNBOUND,
    half: Any = _UNBOUND,
    i8: Any = _UNBOUND,
    kd2: Any = _UNBOUND,
    kd3: Any = _UNBOUND,
    kido_off: Any = _UNBOUND,
    lane8: Any = _UNBOUND,
    pts: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    want8: Any = _UNBOUND,
    wards_k: Any = _UNBOUND,
    wd2: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.081 (kido_aligned_with_ward_fence, kido_guard_box_clear_of_lanes) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and wards_k:
        kido_off = []
        for kd2 in M.get("kido", []):
            best2 = None  # (distance, tangent angle) of the nearest ward-fence segment
            for wd2 in wards_k:
                b2 = wd2["boundary"]
                for i8 in range(len(b2) - 1):
                    d8 = seg_dist(kd2["x"], kd2["y"], b2[i8], b2[i8 + 1])
                    if best2 is None or d8 < best2[0]:
                        best2 = (d8, math.degrees(math.atan2(b2[i8 + 1][1] - b2[i8][1], b2[i8 + 1][0] - b2[i8][0])))
            if best2 is None or best2[0] > 16:
                continue  # a free-standing kido (nothing near enough to align to)
            lane8 = lane_through_gate(M, kd2["x"], kd2["y"], best2[1])
            want8 = (kido_bar_deg(lane8[0], best2[1]) if lane8 else best2[1]) % 180.0
            got8 = float(kd2["rot"]) % 180.0 if "rot" in kd2 else (90.0 if kd2.get("horizontal") else 0.0)
            diff8 = abs(got8 - want8)
            diff8 = min(diff8, 180.0 - diff8)
            if diff8 > 7.0:
                kido_off.append([round(kd2["x"]), round(kd2["y"]), round(diff8), "lane" if lane8 else "fence"])
        check(
            "kido_aligned_with_ward_fence",
            not kido_off,
            f"ward gate(s) not square to what they bar (x, y, degrees off, what it should follow): {kido_off} - a kido "
            f"shuts a WAY, so its roofed bar stands SQUARE ACROSS the lane running through it; only a gate with no lane "
            f"through it follows the local fence tangent (s.ward computes both; pass rot= to s.kido for a hand-placed gate)",
        )
        # ...AND THE GUARD BOX STANDS ON THE VERGE, NOT IN THE ROAD (GM 2026-07-26). The watch
        # box beside the gate is a small building - the one solid thing in the kido group - and
        # a patrol road or street with a shack in its bed is not passable. It is not covered by
        # the overlap registry (the whole kido group is deliberately overlap-exempt, since the
        # bar MUST span the lane and the fence), so it needs this one rule of its own. The
        # placement side slides the box out until it clears every bed by a ~12 ft verge; this
        # fires only on an actual encroachment of the drawn bed, leaving that verge as slack.
        box_on_lane = []
        for kd3 in M.get("kido", []):
            gbox = kd3.get("guard")
            if not gbox:
                continue  # a legacy manifest that never recorded the box
            gpoly = [(float(c[0]), float(c[1])) for c in gbox]
            if any(footprint_on_line(gpoly, pts, half) for pts, half in lane_runs(M)):
                box_on_lane.append([round(kd3["x"]), round(kd3["y"])])
        check(
            "kido_guard_box_clear_of_lanes",
            not box_on_lane,
            f"ward gate(s) whose guard box stands IN a roadbed: {box_on_lane} - the gate's watch box is a building on the "
            f"verge beside the way, never an obstruction in it (s.kido slides it clear; a curving ring road is the case "
            f"straight-line arithmetic misses)",
        )
    return _kept(locals(), ('b2', 'best2', 'box_on_lane', 'c', 'd8', 'diff8', 'gbox', 'got8', 'gpoly', 'half', 'i8', 'kd2', 'kd3', 'kido_off', 'lane8', 'pts', 'want8', 'wd2'))


def _seg_0563_082__w(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.082 (w) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        w = M.get("wall") or []
    return _kept(locals(), ('w',))


def _seg_0563_083__gates(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.083 (gates) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        gates = M.get("gates", [])
    return _kept(locals(), ('gates',))


def _seg_0563_084__inwall(*, meta: Any = _UNBOUND, px: Any = _UNBOUND, py: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.084 (inwall) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):

        def inwall(px: float, py: float) -> bool:
            return len(w) >= 3 and point_in_poly(px, py, w)

    return _kept(locals(), ('inwall',))


def _seg_0563_085__walled_city_has_wall_and_gates(*, check: Any = _UNBOUND, gates: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.085 (walled_city_has_wall_and_gates) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("walled_city_has_wall_and_gates", len(w) >= 3 and len(gates) >= 2, f"a walled city needs a closed wall and >= 2 gates (wall={len(w)} pts, {len(gates)} gates)")
    return _kept(locals(), ())


def _seg_0563_086__ins(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.086 (ins) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        ins = M.get("inspection_stations", [])
    return _kept(locals(), ('ins',))


def _seg_0563_087__g(*, g: Any = _UNBOUND, gates: Any = _UNBOUND, ins: Any = _UNBOUND, meta: Any = _UNBOUND, s: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.087 (g, no_station, s) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        no_station = [g for g in gates if not any(math.hypot(s["x"] - g[0], s["y"] - g[1]) <= 160 for s in ins)]
    return _kept(locals(), ('g', 'no_station', 's'))


def _seg_0563_088__city_inspection_station_at_each_gate(*, check: Any = _UNBOUND, gates: Any = _UNBOUND, meta: Any = _UNBOUND, no_station: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.088 (city_inspection_station_at_each_gate) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_inspection_station_at_each_gate", len(gates) >= 2 and not no_station, f"every city gate needs an inspection station within ~160px ({len(no_station)} gate(s) without one)")
    return _kept(locals(), ())


def _seg_0563_089__gstructs(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.089 (gstructs) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        gstructs = M.get("gate_structs", [])
    return _kept(locals(), ('gstructs',))


def _seg_0563_090__g_1(*, g: Any = _UNBOUND, gates: Any = _UNBOUND, gstructs: Any = _UNBOUND, meta: Any = _UNBOUND, s: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.090 (g, no_guard, s) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        no_guard = [g for g in gates if sum(1 for s in gstructs if math.hypot(s["x"] - g[0], s["y"] - g[1]) <= 180) < 2]
    return _kept(locals(), ('g', 'no_guard', 's'))


def _seg_0563_091__city_gate_has_guardhouse(*, check: Any = _UNBOUND, gates: Any = _UNBOUND, meta: Any = _UNBOUND, no_guard: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.091 (city_gate_has_guardhouse) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_gate_has_guardhouse", len(gates) >= 2 and not no_guard, f"every city gate needs a guard house + guard tower (>= 2 gate structures within ~180px): {len(no_guard)} gate(s) short")
    return _kept(locals(), ())


# ... and the guard house + inspection station sit AT THE GATE THROAT - hard by the opening,
# flanking the road as it enters - not walked back along the wall. Historically decisive (see
# settlements.md 'Historical grounding'): an inspection/tax barrier only works where traffic
# is forced single-file, and the gate passage is that one chokepoint in the whole wall; set
# the station back along the wall and arrivals disperse into the streets before ever reaching
# it. So each must sit within ~70px of its gate vertex (the built placement lands ~35-45px in).
# The looser city_inspection_station_at_each_gate / city_gate_has_guardhouse radii (160/180)
# deliberately have SLACK for the barbican, and would wave through the old far placement that
# walked the pair 80/144px along the wall - THIS check is what gives that rule teeth.


def _seg_0563_092__THROAT(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.092 (THROAT) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        THROAT = 70
    return _kept(locals(), ('THROAT',))


def _seg_0563_093__throat_bad(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.093 (throat_bad) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        throat_bad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('throat_bad',))


def _seg_0563_094__g_2(
    *,
    THROAT: Any = _UNBOUND,
    g: Any = _UNBOUND,
    gates: Any = _UNBOUND,
    gstructs: Any = _UNBOUND,
    has_gh: Any = _UNBOUND,
    has_in: Any = _UNBOUND,
    ins: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    s: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    throat_bad: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.094 (g, has_gh, has_in, s) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for g in gates:
            has_gh = any(s.get("kind") == "guardhouse" and math.hypot(s["x"] - g[0], s["y"] - g[1]) <= THROAT for s in gstructs)
            has_in = any(math.hypot(s["x"] - g[0], s["y"] - g[1]) <= THROAT for s in ins)
            if not (has_gh and has_in):
                throat_bad.append((round(g[0]), round(g[1])))
    return _kept(locals(), ('g', 'has_gh', 'has_in', 's', 'throat_bad'))


def _seg_0563_095__city_gate_furniture_at_throat(
    *, THROAT: Any = _UNBOUND, check: Any = _UNBOUND, gates: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, throat_bad: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.095 (city_gate_furniture_at_throat) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_gate_furniture_at_throat",
            len(gates) >= 2 and not throat_bad,
            f"gate(s) whose guard house + inspection station are not at the throat (each within {THROAT}px of the opening, flanking the road): {throat_bad} - "
            f"the checkpoint sits AT the gate so all traffic passes through it, not walked back along the wall",
        )
    return _kept(locals(), ())


# the gate's own (smaller) TOWER must sit AT its gate - the CLOSEST tower to the opening, not
# marooned out along the curtain with a mural bastion seated nearer (GM 2026-07-22: the S gate's
# tower had walked to arc 118 to dodge a ward-gate kido, reading as a random small tower
# mid-wall while a mamian sat at the gate). A gate tower is a gate_structs "tower"; every other
# wall_tower is a mamian. When one flank of the gate is blocked the tower takes the OTHER flank
# at the opening (city_wall does this), so it should never be out-distanced by a mural.


def _seg_0563_096__g_3(*, g: Any = _UNBOUND, gstructs: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.096 (g, gate_towers_xy) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        gate_towers_xy = [(g["x"], g["y"]) for g in gstructs if g.get("kind") == "tower"]
    return _kept(locals(), ('g', 'gate_towers_xy'))


def _seg_0563_097__gtx(
    *, M: Any = _UNBOUND, gate_towers_xy: Any = _UNBOUND, gtx: Any = _UNBOUND, gty: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, t: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.097 (gtx, gty, murals_xy, t) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        murals_xy = [(t["x"], t["y"]) for t in M.get("wall_towers", []) if not any(abs(t["x"] - gtx) < 2 and abs(t["y"] - gty) < 2 for gtx, gty in gate_towers_xy)]
    return _kept(locals(), ('gtx', 'gty', 'murals_xy', 't'))


def _seg_0563_098__stranded(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.098 (stranded) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        stranded = []  # type: ignore[var-annotated]
    return _kept(locals(), ('stranded',))


def _seg_0563_099__d_gate_tower(
    *,
    d_gate_tower: Any = _UNBOUND,
    d_nearest_mural: Any = _UNBOUND,
    g: Any = _UNBOUND,
    gate_towers_xy: Any = _UNBOUND,
    gates: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    murals_xy: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    stranded: Any = _UNBOUND,
    tx: Any = _UNBOUND,
    ty: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.099 (d_gate_tower, d_nearest_mural, g, stranded) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for g in gates:
            if not gate_towers_xy:
                continue
            d_gate_tower = min(math.hypot(tx - g[0], ty - g[1]) for tx, ty in gate_towers_xy)
            d_nearest_mural = min((math.hypot(tx - g[0], ty - g[1]) for tx, ty in murals_xy), default=1e9)
            if d_nearest_mural + 12 < d_gate_tower:  # a mamian sits meaningfully closer to the gate than the gate's own tower
                stranded.append((round(g[0]), round(g[1])))
    return _kept(locals(), ('d_gate_tower', 'd_nearest_mural', 'g', 'stranded', 'tx', 'ty'))


def _seg_0563_100__city_gate_tower_at_its_gate(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, stranded: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.100 (city_gate_tower_at_its_gate) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_gate_tower_at_its_gate",
            not stranded,
            f"gate(s) whose own tower is marooned out along the wall while a mural bastion sits closer to the opening: {stranded} - "
            f"the gate tower belongs AT the gate (place it on the gate's OTHER flank when one side is blocked, not walked far along the curtain)",
        )
    return _kept(locals(), ())


# a fortified city is TOWERED for enfilading fire along the wall face: guard towers spaced
# at regular intervals around the whole rampart (a bowshot apart), not only at the gates -
# so no long bare arc of wall sits uncovered. Spacing is judged by the widest angular gap
# between consecutive towers around the wall centroid.


def _seg_0563_101__towers(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.101 (towers) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        towers = M.get("wall_towers", [])
    return _kept(locals(), ('towers',))


def _seg_0563_102__p_1(*, meta: Any = _UNBOUND, p: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.102 (p, wcx, wcy) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        wcx, wcy = sum(p[0] for p in w) / len(w), sum(p[1] for p in w) / len(w)
    return _kept(locals(), ('p', 'wcx', 'wcy'))


def _seg_0563_103__angs(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND, t: Any = _UNBOUND, towers: Any = _UNBOUND, wcx: Any = _UNBOUND, wcy: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.103 (angs, t) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        angs = sorted(math.atan2(t["y"] - wcy, t["x"] - wcx) for t in towers)
    return _kept(locals(), ('angs', 't'))


def _seg_0563_104__i(*, angs: Any = _UNBOUND, i: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.104 (i, maxgap) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        maxgap = max([angs[i + 1] - angs[i] for i in range(len(angs) - 1)] + [angs[0] + 2 * math.pi - angs[-1]]) if angs else 2 * math.pi
    return _kept(locals(), ('i', 'maxgap'))


def _seg_0563_105__city_wall_towers_spaced(*, check: Any = _UNBOUND, maxgap: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, towers: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.105 (city_wall_towers_spaced) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):
            check(
                "city_wall_towers_spaced",
                len(towers) >= 6 and maxgap < math.radians(75),
                f"a fortified city needs guard towers spaced around the wall, not just at the gates ({len(towers)} towers, widest bare arc {round(math.degrees(maxgap))} deg, want < 75) - place towers at regular intervals (s.city_wall does this automatically)",
            )
    return _kept(locals(), ())


# guard towers sit SQUARE to the wall (rotated to its tangent) rather than all axis-aligned -
# a tower on a slanted stretch slants with it. Each tower's recorded rotation must match the
# angle of the nearest wall edge (mod 90, since a square reads the same every 90 degrees).


def _seg_0563_106__ring2(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.106 (ring2) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        ring2: Any = list(w) + [w[0]]  # type: ignore[no-redef,unused-ignore]
    return _kept(locals(), ('ring2',))


def _seg_0563_107__misaligned(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.107 (misaligned) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        misaligned = []  # type: ignore[var-annotated]
    return _kept(locals(), ('misaligned',))


def _seg_0563_108__d(
    *,
    d: Any = _UNBOUND,
    edge_ang: Any = _UNBOUND,
    ek: Any = _UNBOUND,
    k: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    misaligned: Any = _UNBOUND,
    order: Any = _UNBOUND,
    ring2: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    t: Any = _UNBOUND,
    towers: Any = _UNBOUND,
    twr_off: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.108 (d, edge_ang, ek, misaligned) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for t in towers:
            # THE TWO NEAREST EDGES, not just the nearest (GM 2026-07-25). A tower seated near a
            # VERTEX of the wall N-gon is legitimately square to EITHER of the runs that meet
            # there - placement takes its tangent from one side, and which side `seg_dist` calls
            # "nearest" can flip on a sub-pixel move. That is exactly what happened when the
            # martial hall's budget line grew Nagahara's derived ring by 1px: an untouched tower
            # at (1909, 1200) kept its rot of 80.4 while the nearest-edge lookup crossed from the
            # 80.4 deg run to the 61.3 deg one, and a correct tower failed. Scoring the best of
            # the two nearest edges makes the check read the geometry the way placement wrote it;
            # it does NOT weaken the rule, because an axis-aligned tower on a slanted stretch is
            # still off BOTH adjacent runs by more than the tolerance.
            order = sorted(range(len(ring2) - 1), key=lambda k: seg_dist(t["x"], t["y"], ring2[k], ring2[k + 1]))
            twr_off = 90.0
            for ek in order[:2]:
                edge_ang = math.degrees(math.atan2(ring2[ek + 1][1] - ring2[ek][1], ring2[ek + 1][0] - ring2[ek][0]))
                d = (t.get("rot", 0) - edge_ang) % 90
                twr_off = min(twr_off, d, 90 - d)
            if twr_off > 15:
                misaligned.append((round(t["x"]), round(t["y"])))
    return _kept(locals(), ('d', 'edge_ang', 'ek', 'misaligned', 'order', 't', 'twr_off'))


def _seg_0563_109__city_wall_towers_aligned(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, misaligned: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.109 (city_wall_towers_aligned) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_wall_towers_aligned", not misaligned, f"guard tower(s) not square to the wall - a tower should rotate to the wall's tangent there, not stay axis-aligned: {misaligned}")
    return _kept(locals(), ())


# the GATE FURNITURE - the guard house + inspection station that sit along the ring road just
# inside each gate - is likewise SQUARE TO THE WALL: rotated to the wall's LOCAL tangent at its
# own position (NOT the gate vertex's - the wall has already curved away by then), so the ring
# road runs lengthwise through it. Each is a rectangle (its long axis runs ALONG the wall), so
# its rotation must match the nearest wall edge angle mod 180 (a 180 deg flip is the same, a 90
# deg turn would stand it the wrong way across the road). Tolerance is TIGHTER than the towers'
# (6 vs 15 deg): the furniture rotation is set from the exact local edge angle, not the towers'
# chord-through-neighbors approximation, so a correctly-placed piece matches near-exactly - and
# the gates sit on shallow wall stretches (~8 deg), which a 15 deg window would wave through.


def _seg_0563_110__furn(*, M: Any = _UNBOUND, g: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.110 (furn, g) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        furn = [g for g in M.get("gate_structs", []) if g.get("kind") in ("guardhouse", "inspection")]
    return _kept(locals(), ('furn', 'g'))


def _seg_0563_111__fmis(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.111 (fmis) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        fmis = []  # type: ignore[var-annotated]
    return _kept(locals(), ('fmis',))


def _seg_0563_112__d_1(
    *,
    d: Any = _UNBOUND,
    edge_ang: Any = _UNBOUND,
    ek: Any = _UNBOUND,
    fmis: Any = _UNBOUND,
    furn: Any = _UNBOUND,
    gstruct: Any = _UNBOUND,
    k: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    ring2: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.112 (d, edge_ang, ek, fmis) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for gstruct in furn:
            ek = min(range(len(ring2) - 1), key=lambda k: seg_dist(gstruct["x"], gstruct["y"], ring2[k], ring2[k + 1]))
            edge_ang = math.degrees(math.atan2(ring2[ek + 1][1] - ring2[ek][1], ring2[ek + 1][0] - ring2[ek][0]))
            d = (gstruct.get("rot", 0) - edge_ang) % 180
            if min(d, 180 - d) > 6:
                fmis.append((round(gstruct["x"]), round(gstruct["y"])))
    return _kept(locals(), ('d', 'edge_ang', 'ek', 'fmis', 'gstruct'))


def _seg_0563_113__city_gate_furniture_aligned(*, check: Any = _UNBOUND, fmis: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.113 (city_gate_furniture_aligned) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):
            check(
                "city_gate_furniture_aligned",
                not fmis,
                f"gate guard house / inspection station(s) not square to the wall - they should rotate to the wall's LOCAL tangent where they sit (so the ring road runs through them lengthwise), not stay flat: {fmis}",
            )
    return _kept(locals(), ())


# ... and the guard house + inspection station are SEPARATE buildings: walked along a
# tightly-curving wall the two arcs can converge, and an inspection annex drawn through
# its guard house reads as a collision (GM, 2026-07)


def _seg_0563_114__gpairs(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.114 (gpairs) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        gpairs = []  # type: ignore[var-annotated]
    return _kept(locals(), ('gpairs',))


def _seg_0563_115__g_4(*, M: Any = _UNBOUND, g: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.115 (g, ghs) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        ghs = [g for g in M.get("gate_structs", []) if g.get("kind") == "guardhouse"]
    return _kept(locals(), ('g', 'ghs'))


def _seg_0563_116__gh(*, M: Any = _UNBOUND, gh: Any = _UNBOUND, ghs: Any = _UNBOUND, gpairs: Any = _UNBOUND, ins: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.116 (gh, gpairs, ins) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for ins in M.get("inspection_stations", []):
            for gh in ghs:
                if math.hypot(ins["x"] - gh["x"], ins["y"] - gh["y"]) < 160 and sat_overlap(
                    rect_corners({"x": ins["x"], "y": ins["y"], "w": ins["w"], "h": ins["h"], "rot": ins.get("rot", 0)}),
                    rect_corners({"x": gh["x"], "y": gh["y"], "w": gh["w"], "h": gh["h"], "rot": gh.get("rot", 0)}),
                ):
                    gpairs.append((round(ins["x"]), round(ins["y"])))
    return _kept(locals(), ('gh', 'gpairs', 'ins'))


def _seg_0563_117__city_gate_guard_inspection_separate(*, check: Any = _UNBOUND, gpairs: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.117 (city_gate_guard_inspection_separate) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_gate_guard_inspection_separate",
            not gpairs,
            f"gate inspection station(s) overlapping their guard house: {gpairs} - the two are separate buildings on the ring road; space them along the wall until they clear",
        )
    return _kept(locals(), ())


# WALL FURNITURE STAYS OUT OF THE MOAT: a guard tower straddles the wall and may PROJECT a
# stride past its outer face (the horse-face bastion), but its footing must stand on the
# BERM, never in the water - a tight moat gap leaves a narrow berm, so a tower centered on
# the wall line pokes its outer face into the bed. Same for the gate towers and the guard
# house / inspection station. (Bridges are exempt - they span the moat by design.)


def _seg_0563_118__mo_f(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.118 (mo_f) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        mo_f = M.get("moat")
    return _kept(locals(), ('mo_f',))


def _seg_0563_119__city_wall_furniture_clear_of_moat(
    *,
    M: Any = _UNBOUND,
    check: Any = _UNBOUND,
    fc: Any = _UNBOUND,
    furn_wet: Any = _UNBOUND,
    it: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    mhw_f: Any = _UNBOUND,
    mo_f: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.119 (city_wall_furniture_clear_of_moat) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and mo_f:
        mhw_f = M.get("moat_width", 22) / 2
        furn_wet: list[tuple[int, int]] = []  # type: ignore[no-redef]
        for it in M.get("wall_towers", []) + M.get("gate_structs", []) + M.get("inspection_stations", []):
            fc = rect_corners({"x": it["x"], "y": it["y"], "w": it.get("w", 26), "h": it.get("h", 26), "rot": it.get("rot", 0)})
            if footprint_on_line(fc, mo_f, mhw_f + 1):
                furn_wet.append((round(it["x"]), round(it["y"])))
        check(
            "city_wall_furniture_clear_of_moat",
            not furn_wet,
            f"guard tower(s) / gate furniture standing IN the moat: {sorted(set(furn_wet))[:6]} - wall furniture "
            f"footings stay on the berm; nudge them inward so only a small outer projection passes the wall face",
        )
    return _kept(locals(), ('fc', 'furn_wet', 'it', 'mhw_f'))


# THE WARD GATES STAND CLEAR OF THE WALL TOWERS: a kido hangs on the ward fence where a
# lane or the ring road crosses it, and the fence ends abut the rampart - so the LAST
# kido can land against a mural tower's footprint (its guard box read as "a small square
# building" inside the tower - GM, 2026-07). Both are overlap-EXEMPT classes (each sits
# on its own wall), so no generic pass catches the pair. The kido cannot move (it gates
# a fixed crossing), so the TOWER yields - city_wall(tower_skip=[...]) relocates it to
# the neighboring wall vertex.


def _seg_0563_120__k_hit(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.120 (k_hit) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        k_hit = []  # type: ignore[var-annotated]
    return _kept(locals(), ('k_hit',))


def _seg_0563_121__g_(
    *, M: Any = _UNBOUND, g_: Any = _UNBOUND, k_hit: Any = _UNBOUND, kc: Any = _UNBOUND, kd: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, t: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.121 (g_, k_hit, kc, kd) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for kd in M.get("kido", []):
            for kc in kido_quads(kd):
                if any(
                    sat_overlap(kc, rect_corners({"x": t["x"], "y": t["y"], "w": t.get("w", 38), "h": t.get("h", 38), "rot": t.get("rot", 0)}))
                    for t in M.get("wall_towers", []) + [g_ for g_ in M.get("gate_structs", []) if g_.get("kind") == "tower"]
                ):
                    k_hit.append((round(kd["x"]), round(kd["y"])))
                    break
    return _kept(locals(), ('g_', 'k_hit', 'kc', 'kd', 't'))


def _seg_0563_122__kido_clear_of_wall_towers(*, check: Any = _UNBOUND, k_hit: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.122 (kido_clear_of_wall_towers) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "kido_clear_of_wall_towers",
            not k_hit,
            f"ward gate(s) overlapping a guard tower: {sorted(set(k_hit))[:4]} - where the ward fence meets the "
            f"rampart the kido keeps its ground (it gates a fixed crossing); slide the tower along the wall "
            f"(city_wall tower_skip)",
        )
    return _kept(locals(), ())


# a GATE TOWER (a gate's guard tower, or a mural tower) must not OVERLAP the gate's
# INSPECTION STATION or GUARD HOUSE (GM, 2026-07). The gate complex packs tight (guardhouse
# + inspection + tower + gateposts at each gate) and inspection stations are overlap-EXEMPT
# against the gate furniture, which had let a tower footprint STACK on the inspection post -
# each is a distinct building and they must sit CLEAR of one another, abutting not stacked.


def _seg_0563_123___gtowers(*, M: Any = _UNBOUND, g: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, x: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.123 (_gtowers, g, x) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        _gtowers = [g for g in (M.get("wall_towers", []) + [x for x in M.get("gate_structs", []) if x.get("kind") == "tower"]) if "w" in g]
    return _kept(locals(), ('_gtowers', 'g', 'x'))


def _seg_0563_124___gfurn(*, M: Any = _UNBOUND, g: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, x: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.124 (_gfurn, g, x) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        _gfurn = [g for g in ([x for x in M.get("gate_structs", []) if x.get("kind") in ("inspection", "guardhouse")] + M.get("inspection_stations", [])) if "w" in g]
    return _kept(locals(), ('_gfurn', 'g', 'x'))


def _seg_0563_125__gf_hit(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.125 (gf_hit) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        gf_hit = []  # type: ignore[var-annotated]
    return _kept(locals(), ('gf_hit',))
