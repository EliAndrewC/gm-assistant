"""Gate segments (work yards and matrix; keys 0052-0096) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from l7r.diagram.settlement import sat_overlap

from .common_01_geometry import (
    _MATRIX_OUTSTANDING,
    _MX_NOT_GEOMETRY,
    _OVERLAP_STRUCTS,
    OVERLAP_CLASS,
    _struct_rect,
    edge_gap,
    kiln_quarters,
    point_in_poly,
    rect_corners,
    seg_dist,
    segments_cross,
    solid_structs,
)
from .common_02_overlap_policy import matrix_violations
from .common_03_capacity import (
    _UNBOUND,
    DWELLING_KINDS,
    _kept,
)

# `_fr_gap` is gone: it was feature 016's own exact footprint-gap helper, written before
# `edge_gap` existed and doing the same job by the same method. Two correct helpers for one
# question is how the three WRONG conventions got started, so the call sites now use edge_gap
# and take records rather than pre-built corner lists (GM, 2026-07-27). The only behavioral
# difference is that an overlap now reads 0.0 instead of -1.0, which every call site - all of
# them `< some_positive_gap` - treats identically.


def _seg_0052___fr_orphan(*, _fr_all: Any = _UNBOUND, _fr_ftpx: Any = _UNBOUND, _fr_stables: Any = _UNBOUND, b_: Any = _UNBOUND, f_: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 52 (_fr_orphan, b_, f_) - body verbatim from the legacy gate() (feature 022)."""
    _fr_orphan = [(round(f_["x"]), round(f_["y"])) for f_ in _fr_all if not _fr_stables or min(math.hypot(f_["x"] - b_["x"], f_["y"] - b_["y"]) for b_ in _fr_stables) > 250.0 / _fr_ftpx]
    return _kept(locals(), ('_fr_orphan', 'b_', 'f_'))


def _seg_0053__farrier_serves_a_stables(*, _fr_orphan: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 53 (farrier_serves_a_stables) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "farrier_serves_a_stables",
        not _fr_orphan,
        f"farrier(s) with no stables within ~250 real ft at {_fr_orphan[:3]} - a shoeing forge earns its own premises ONLY where horses concentrate (a gate caravan yard, an Imperial-road relay town); an ordinary smith who also shoes stays inside the generic shop rows (s.farrier; settlements.md 'TRADE WORKS' -> FARRIERY)",
    )
    return _kept(locals(), ())


def _seg_0054___fr_tight() -> dict[str, Any]:
    """Gate segment 54 (_fr_tight) - body verbatim from the legacy gate() (feature 022)."""
    _fr_tight = []  # type: ignore[var-annotated]
    return _kept(locals(), ('_fr_tight',))


def _seg_0055___fo(
    *, M: Any = _UNBOUND, _fo: Any = _UNBOUND, _fr: Any = _UNBOUND, _fr_all: Any = _UNBOUND, _fr_ftpx: Any = _UNBOUND, _fr_tight: Any = _UNBOUND, _frk: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 55 (_fo, _fr, _fr_tight, _frk) - body verbatim from the legacy gate() (feature 022)."""
    for _fr in _fr_all:
        if any(edge_gap(_fr, _fo) < 6.0 / _fr_ftpx for _frk in _OVERLAP_STRUCTS + ("manors", "religious") if _frk != "farriers" for _fo in M.get(_frk, []) or []):
            _fr_tight.append((round(_fr["x"]), round(_fr["y"])))
    return _kept(locals(), ('_fo', '_fr', '_fr_tight', '_frk'))


def _seg_0056__farrier_keeps_fire_gap(*, _fr_tight: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 56 (farrier_keeps_fire_gap) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "farrier_keeps_fire_gap",
        not _fr_tight,
        f"farrier(s) crowding a neighboring structure at {_fr_tight[:3]} - an OPEN forge against a hay-and-timber stall range is the fire a stable yard does not survive, so the smithy stands across the ground, never attached (>= ~6 real ft clear of every footprint; buildings.md's wooden-service fire gap)",
    )
    return _kept(locals(), ())


def _seg_0057__city_has_farrier(*, URBAN: Any = _UNBOUND, _fr_all: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 57 (city_has_farrier, imperial_road_town_has_farrier) - body verbatim from the legacy gate() (feature 022)."""
    if URBAN:
        check(
            "city_has_farrier",
            bool(_fr_all),
            "no farrier - a provincial city's gate caravan yard concentrates enough horses to keep a dedicated shoeing forge (s.farrier beside the stables; the Imperial relay + cheap continental iron are why Rokugan shoes in iron at all)",
        )
    elif meta.get("imperial_road"):
        check(
            "imperial_road_town_has_farrier",
            bool(_fr_all),
            "no farrier in an Imperial-road town - a relay/post town on the Imperial road works courier and caravan horses hard enough to keep a shoeing forge at its stables (s.farrier); a town OFF the Imperial road does not declare meta(imperial_road=True) and is exempt, which is the deliberate Hoshizora/Hirameki split",
        )
    return _kept(locals(), ())


# ===== THE OVERLAP MATRIX (feature 017) - one general rule in place of per-pair whack-a-mole.
# Every geometric key has a class; a class-by-class policy forbids by default; conditional
# permissions (an annex on its own parent, a canal serving its own hem) live in
# matrix_violations. Adding a feature = one line in OVERLAP_CLASS and it is protected against
# everything, which is the entire point (GM 2026-07-26).


def _seg_0058___mx_name(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 58 (_mx_name) - body verbatim from the legacy gate() (feature 022)."""
    _mx_name = str(meta.get("name") or "")
    return _kept(locals(), ('_mx_name',))


def _seg_0059___mx_known(*, _mx_name: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 59 (_mx_known) - body verbatim from the legacy gate() (feature 022)."""
    _mx_known = _MATRIX_OUTSTANDING.get(_mx_name, {})
    return _kept(locals(), ('_mx_known',))


def _seg_0060___mx_seen() -> dict[str, Any]:
    """Gate segment 60 (_mx_seen) - body verbatim from the legacy gate() (feature 022)."""
    _mx_seen: dict[tuple[str, str], list[tuple[str, str, float, float]]] = {}
    return _kept(locals(), ('_mx_seen',))


def _seg_0061___mx_key(*, M: Any = _UNBOUND, _mx_key: Any = _UNBOUND, _mx_seen: Any = _UNBOUND, _v: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 61 (_mx_key, _mx_seen, _v) - body verbatim from the legacy gate() (feature 022)."""
    for _v in matrix_violations(M):
        _mx_key: tuple[str, str] = (min(_v[0], _v[1]), max(_v[0], _v[1]))  # type: ignore[no-redef]
        _mx_seen.setdefault(_mx_key, []).append(_v)
    return _kept(locals(), ('_mx_key', '_mx_seen', '_v'))


def _seg_0062___mx_bad(*, _mx_known: Any = _UNBOUND, _mx_seen: Any = _UNBOUND, pair: Any = _UNBOUND, v: Any = _UNBOUND, vs: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 62 (_mx_bad, pair, v, vs) - body verbatim from the legacy gate() (feature 022)."""
    _mx_bad = [v for pair, vs in _mx_seen.items() for v in vs[_mx_known.get(pair, 0) :]]
    return _kept(locals(), ('_mx_bad', 'pair', 'v', 'vs'))


def _seg_0063__features_do_not_overlap(*, _mx_bad: Any = _UNBOUND, a: Any = _UNBOUND, b: Any = _UNBOUND, check: Any = _UNBOUND, x: Any = _UNBOUND, y: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 63 (features_do_not_overlap) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "features_do_not_overlap",
        not _mx_bad,
        f"overlapping feature(s) whose classes forbid it: {[(a, b, x, y) for a, b, x, y in _mx_bad[:4]]} - the overlap MATRIX decides every pair from one classification (OVERLAP_CLASS + the policy above), so this is not a missing per-pair rule. Either the drawing is wrong, or the pair genuinely may overlap and needs a permission WITH ITS REASON in _MATRIX_PERMISSIVE / _MATRIX_SAME_KEY_OK / _MATRIX_ALLOWED_PAIRS / _MATRIX_ALLOWED_KEYS",
    )
    return _kept(locals(), ('a', 'b', 'x', 'y'))


# ...and the ratchet on the ratchet. An _MATRIX_OUTSTANDING line is WORK OWED, so once the defect
# it records is fixed the line does not merely rot - it goes on TOLERATING that many real
# overlaps of that pair on that map for ever, which is exactly the hole a debt register is
# supposed to close. (Minami's five outstanding pairs were fixed by the 016 session while the
# entry recording them stayed behind, so the map could have silently regressed on any of them.)
# Same rule, and same reason, as waivers_are_live.


def _seg_0064___mx_stale(*, _mx_known: Any = _UNBOUND, _mx_seen: Any = _UNBOUND, allow: Any = _UNBOUND, pair: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 64 (_mx_stale, allow, pair) - body verbatim from the legacy gate() (feature 022)."""
    _mx_stale = sorted(pair for pair, allow in _mx_known.items() if len(_mx_seen.get(pair, [])) < allow)
    return _kept(locals(), ('_mx_stale', 'allow', 'pair'))


def _seg_0065__matrix_debts_still_owed(*, _mx_name: Any = _UNBOUND, _mx_stale: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 65 (matrix_debts_still_owed) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "matrix_debts_still_owed",
        not _mx_stale,
        f"_MATRIX_OUTSTANDING still records {_mx_stale} for {_mx_name!r}, but the map no longer draws that many - the debt is PAID. Delete the line: left there it tolerates that many real overlaps of the pair for ever, which is the opposite of what a debt register is for",
    )
    return _kept(locals(), ())


# the ratchet: a drawn geometric key nobody classified
# DERIVED from the manifest, not from a hand list - a ratchet that enumerates its own keys is
# the same defect this feature exists to abolish, and it showed: the hand-listed version passed
# an unseen river city silently while TEN of its keys (bridges, jetties, kido, sluice_gates,
# wall_towers, water_gates, docks, inspection_stations, gate_structs, stable_yards) had no class
# at all. A key counts as drawn geometry when its records carry a position or an outline.


def _seg_0066___mx_unclassified(*, M: Any = _UNBOUND, c: Any = _UNBOUND, k: Any = _UNBOUND, v: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 66 (_mx_unclassified, c, k, v) - body verbatim from the legacy gate() (feature 022)."""
    _mx_unclassified = sorted(
        {
            k
            for k, v in M.items()
            if k not in OVERLAP_CLASS
            and k not in _MX_NOT_GEOMETRY
            and isinstance(v, list)
            and v
            and (
                (isinstance(v[0], dict) and ("x" in v[0] or "poly" in v[0] or "pts" in v[0]))
                # ...OR a bare POLYLINE / point list - how the wall, moat, ring road and torii are
                # stored. The first cut inspected only DICT records and so passed five unclassified
                # keys in silence: a ratchet that enumerates one record shape has the same blindness
                # this feature exists to abolish.
                or (isinstance(v[0], (list, tuple)) and len(v[0]) >= 2 and all(isinstance(c, (int, float)) for c in v[0][:2]))
            )
        }
    )
    return _kept(locals(), ('_mx_unclassified', 'c', 'k', 'v'))


def _seg_0067__every_feature_classified_for_matrix(*, _mx_unclassified: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 67 (every_feature_classified_for_matrix) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "every_feature_classified_for_matrix",
        not _mx_unclassified,
        f"drawn feature key(s) {_mx_unclassified} have no entry in OVERLAP_CLASS - give each one a class (SOLID / GROUND / WATER / WAY / ANNEX, or a permissive class WITH its reason) and it is governed against every other feature at once",
    )
    return _kept(locals(), ())


# ===== A COMPOUND'S OWN WALL KEEPS OFF THE WAYS (found by the settlement-review agent, 2026-07-26).
# `manors` sits in _OVERLAP_TARGETS - the registry of things OTHER features must avoid - and never
# in _OVERLAP_STRUCTS, so the whole no_structure_on_* battery reads a manor as a hazard and nothing
# reads it as a candidate. The compound's own wall was therefore ungoverned against the roadbed,
# and a trunk road duly ran 18 px inside a magistracy's south wall, 80 ft from its own gate, with
# the gate fully green. A wall standing in a public carriageway is the same defect as a house
# standing in one; it just had nobody watching for it.


def _seg_0068___mw_ways() -> dict[str, Any]:
    """Gate segment 68 (_mw_ways) - body verbatim from the legacy gate() (feature 022)."""
    _mw_ways: list[tuple[list[Any], float]] = []
    return _kept(locals(), ('_mw_ways',))


def _seg_0069___mw_rd(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 69 (_mw_rd) - body verbatim from the legacy gate() (feature 022)."""
    _mw_rd = M.get("road") or []
    return _kept(locals(), ('_mw_rd',))


def _seg_0070___mw_ways_1(*, M: Any = _UNBOUND, _mw_rd: Any = _UNBOUND, _mw_ways: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 70 (_mw_ways) - body verbatim from the legacy gate() (feature 022)."""
    if _mw_rd:
        _mw_ways.append((_mw_rd, float(M.get("road_width") or 26.0) / 2.0))
    return _kept(locals(), ('_mw_ways',))


def _seg_0071___mw_st(*, M: Any = _UNBOUND, _mw_st: Any = _UNBOUND, _mw_ways: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 71 (_mw_st, _mw_ways) - body verbatim from the legacy gate() (feature 022)."""
    for _mw_st in M.get("town_streets", []) or []:
        _mw_ways.append((_mw_st["pts"], float(_mw_st.get("w", 20)) / 2.0))
    return _kept(locals(), ('_mw_st', '_mw_ways'))


def _seg_0072___mw_gap(*, best: Any = _UNBOUND, i: Any = _UNBOUND, j: Any = _UNBOUND, rect: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 72 (_mw_gap) - body verbatim from the legacy gate() (feature 022)."""

    def _mw_gap(rect: list[tuple[float, float]], seg_a: Any, seg_b: Any) -> float:
        """Clear distance between a (possibly rotated) footprint and one way segment; 0 if they meet."""
        if point_in_poly(seg_a[0], seg_a[1], rect) or point_in_poly(seg_b[0], seg_b[1], rect):
            return 0.0
        best = min(seg_dist(rect[i][0], rect[i][1], seg_a, seg_b) for i in range(len(rect)))
        for i in range(len(rect)):
            j = (i + 1) % len(rect)
            if segments_cross(rect[i], rect[j], seg_a, seg_b):
                return 0.0
            best = min(best, seg_dist(seg_a[0], seg_a[1], rect[i], rect[j]), seg_dist(seg_b[0], seg_b[1], rect[i], rect[j]))
        return best

    return _kept(locals(), ('_mw_gap',))


def _seg_0073___mw_bad() -> dict[str, Any]:
    """Gate segment 73 (_mw_bad) - body verbatim from the legacy gate() (feature 022)."""
    _mw_bad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('_mw_bad',))


def _seg_0074___mw_bad_1(
    *,
    M: Any = _UNBOUND,
    _fr_poly: Any = _UNBOUND,
    _mw_bad: Any = _UNBOUND,
    _mw_gap: Any = _UNBOUND,
    _mw_hw: Any = _UNBOUND,
    _mw_mn: Any = _UNBOUND,
    _mw_pl: Any = _UNBOUND,
    _mw_rect: Any = _UNBOUND,
    _mw_ways: Any = _UNBOUND,
    i: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 74 (_mw_bad, _mw_hw, _mw_mn, _mw_pl) - body verbatim from the legacy gate() (feature 022)."""
    for _mw_mn in M.get("manors", []) or []:
        _mw_rect = _fr_poly(_mw_mn)
        for _mw_pl, _mw_hw in _mw_ways:
            if any(_mw_gap(_mw_rect, _mw_pl[i], _mw_pl[i + 1]) < _mw_hw for i in range(len(_mw_pl) - 1)):
                _mw_bad.append((round(_mw_mn["x"]), round(_mw_mn["y"])))
                break
    return _kept(locals(), ('_mw_bad', '_mw_hw', '_mw_mn', '_mw_pl', '_mw_rect', 'i'))


def _seg_0075__manor_walls_clear_of_ways(*, _mw_bad: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 75 (manor_walls_clear_of_ways) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "manor_walls_clear_of_ways",
        not _mw_bad,
        f"compound wall(s) standing in a roadbed at {_mw_bad[:3]} - a manor is a footprint like any other where a WAY is concerned, and a carriageway running through the compound's own wall is a drawing error, not a right of way. Move the road off the wall (or the compound off the road); the gate is always green here otherwise, because `manors` is an overlap TARGET and never a candidate",
    )
    return _kept(locals(), ())


# ===== NOTHING IS BUILT ON THE FAR SIDE OF A DRAWN BORDER (found by the settlement-review agent,
# 2026-07-26). A border is deliberately overlap-EXEMPT - a frontier magistracy stands its wall ON
# the line by design - but "the wall may sit on the line" is not "the settlement may build across
# it." Water and roads cross a jurisdiction freely; buildings, yards and gardens do not, because
# the ground on the far side belongs to somebody else. Ubame's own notes promised its cover was
# "kept west of the border" while three kitchen gardens and two commons reached 43 px past it.
# The test is on the CENTER, which is what keeps the deliberate case legal: the magistracy's
# center is on its own side and only its wall touches the line.


def _seg_0076___bd_lines(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 76 (_bd_lines) - body verbatim from the legacy gate() (feature 022)."""
    _bd_lines = M.get("borders", []) or []
    return _kept(locals(), ('_bd_lines',))


def _seg_0077__structures_stay_on_their_side_of_a_border(
    *,
    M: Any = _UNBOUND,
    _b: Any = _UNBOUND,
    _bd_bad: Any = _UNBOUND,
    _bd_cx: Any = _UNBOUND,
    _bd_cy: Any = _UNBOUND,
    _bd_homes: Any = _UNBOUND,
    _bd_k: Any = _UNBOUND,
    _bd_lines: Any = _UNBOUND,
    _bd_ours: Any = _UNBOUND,
    _bd_pl: Any = _UNBOUND,
    _bd_poly: Any = _UNBOUND,
    _bd_r: Any = _UNBOUND,
    _bd_side: Any = _UNBOUND,
    _h: Any = _UNBOUND,
    best_d: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d_: Any = _UNBOUND,
    i: Any = _UNBOUND,
    px_: Any = _UNBOUND,
    py_: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 77 (structures_stay_on_their_side_of_a_border) - body verbatim from the legacy gate() (feature 022)."""
    if _bd_lines:
        _bd_homes = M.get("houses", []) + [_b for _b in M.get("buildings", []) if _b.get("kind") in DWELLING_KINDS]
        if _bd_homes:
            _bd_cx = sum(_h["x"] for _h in _bd_homes) / len(_bd_homes)
            _bd_cy = sum(_h["y"] for _h in _bd_homes) / len(_bd_homes)

            def _bd_side(px_: float, py_: float, poly_: list[Any]) -> float:
                """Signed side of the border polyline, taken at its nearest segment."""
                best_d, best_s = float("inf"), 0.0
                for i in range(len(poly_) - 1):
                    ax_, ay_ = poly_[i]
                    bx_, by_ = poly_[i + 1]
                    d_ = seg_dist(px_, py_, poly_[i], poly_[i + 1])
                    if d_ < best_d:
                        best_d = d_
                        best_s = (bx_ - ax_) * (py_ - ay_) - (by_ - ay_) * (px_ - ax_)
                return best_s

            _bd_bad = []
            for _bd_poly in _bd_lines:
                _bd_pl = _bd_poly["poly"]
                _bd_ours = _bd_side(_bd_cx, _bd_cy, _bd_pl)
                if _bd_ours == 0:
                    continue  # pragma: no cover - a settlement centered exactly on its own border has no near side
                for _bd_k in ("houses", "buildings", "gardens", "threshing_yards", "farm_sheds", "byres", "storehouses") + _OVERLAP_STRUCTS:
                    for _bd_r in M.get(_bd_k, []) or []:
                        if not isinstance(_bd_r, dict) or "x" not in _bd_r:
                            continue  # pragma: no cover - defensive: every listed key stores dicts
                        if _bd_side(_bd_r["x"], _bd_r["y"], _bd_pl) * _bd_ours < 0:
                            _bd_bad.append((_bd_k, round(_bd_r["x"]), round(_bd_r["y"])))
            _bd_bad = sorted(set(_bd_bad))
            check(
                "structures_stay_on_their_side_of_a_border",
                not _bd_bad,
                f"feature(s) built on the FAR side of a drawn border at {_bd_bad[:4]} - the ground over the line belongs to the neighboring clan, so a settlement's buildings, yards and gardens stop at it. Water and roads may cross freely, and a compound may stand its WALL on the line (the test is on the center, so that case stays legal) - but building across it is a jurisdictional claim the map should not make",
            )
    return _kept(locals(), ('_b', '_bd_bad', '_bd_cx', '_bd_cy', '_bd_homes', '_bd_k', '_bd_ours', '_bd_pl', '_bd_poly', '_bd_r', '_bd_side', '_h'))


# ===== THE CHARCOAL DISTRICT'S TRADE WORKS (feature 016; full grounding in
# settlements/urban-features.md "CHARCOAL YARDS" and "REFINING FORGES", research in
# research/urban-features.md).
#
# The SEPARATION LADDER these two join, and why each rung sits where it does. Every figure is
# placed against the ones this project already uses rather than invented, because the whole
# value of a magic number is that a later reader can see what it was reasoned against:
#
#     ~6 ft   farrier from a stall range   sparks from an ATTENDED open forge onto hay
#      30 ft  charcoal yard from anything  a stack that self-heats UNATTENDED
#      60 ft  refining forge from homes    a live worked fire under forced blast, + noise/smoke
#      60 ft  kiln from anything           a days-long ATTENDED firing (see "THE KILN WORKS")
#     120 ft  crematory / tanning yard     putrefaction and smoke carried on the air
#
# NOTE THE SCOPING ASYMMETRY, which is deliberate. The two PRESENCE checks are gated on an
# opt-in meta knob (only a fuel or iron county should own one of these). The three SITING checks
# are gated on the FEATURE's presence instead, so a yard or forge drawn on ANY map - declared or
# not - is still fully validated. That is the mitigation for this file's standing hazard: "a
# check that never RUNS looks exactly like a check that passes."


def _seg_0078___cy_all(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 78 (_cy_all) - body verbatim from the legacy gate() (feature 022)."""
    _cy_all = M.get("charcoal_yards", [])
    return _kept(locals(), ('_cy_all',))


def _seg_0079___rf_all(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 79 (_rf_all) - body verbatim from the legacy gate() (feature 022)."""
    _rf_all = M.get("refining_forges", [])
    return _kept(locals(), ('_rf_all',))


def _seg_0080___cd_ftpx(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 80 (_cd_ftpx) - body verbatim from the legacy gate() (feature 022)."""
    _cd_ftpx = float(meta.get("ftpx") or 1.0)
    return _kept(locals(), ('_cd_ftpx',))


def _seg_0081__settlement_has_charcoal_yard(*, _cy_all: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 81 (settlement_has_charcoal_yard) - body verbatim from the legacy gate() (feature 022)."""
    if meta.get("charcoal_district"):
        check(
            "settlement_has_charcoal_yard",
            bool(_cy_all),
            "meta(charcoal_district=True) declares a fuel district - it must draw a wholesaler's charcoal yard (s.charcoal_yard: roofed stacking sheds + an OPEN cooling apron set apart from them + a weighing floor)",
        )
    return _kept(locals(), ())


# THE FIRE GAP. Charcoal self-heats: fresh charcoal absorbs oxygen fast enough to raise its own
# temperature to ignition, worst of all as tightly-packed fines, which is why the documented
# handling rule stands new stock in the open away from conditioned stock for at least 24 hours.
# The hazard is therefore an UNATTENDED ignition inside a large fuel mass - which is why 30 ft
# sits an order above the attended-forge figure and well below the nuisance figures: it is about
# one flame-height clear of a fully-involved 10-12 ft stack, the usual rule of thumb for radiant
# ignition of adjacent timber. It is emphatically NOT the 120 ft nuisance figure - that defends
# against smell carried on air, and borrowing it here would push the yard off the cart route
# that is its entire reason for existing.


def _seg_0082___cy_tight() -> dict[str, Any]:
    """Gate segment 82 (_cy_tight) - body verbatim from the legacy gate() (feature 022)."""
    _cy_tight = []  # type: ignore[var-annotated]
    return _kept(locals(), ('_cy_tight',))


def _seg_0083___cy(
    *, M: Any = _UNBOUND, _cd_ftpx: Any = _UNBOUND, _cy: Any = _UNBOUND, _cy_all: Any = _UNBOUND, _cy_near: Any = _UNBOUND, _cy_tight: Any = _UNBOUND, _o: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 83 (_cy, _cy_near, _cy_tight, _o) - body verbatim from the legacy gate() (feature 022)."""
    for _cy in _cy_all:
        _cy_near = [_o for _o in solid_structs(M, "manors", "religious", exclude=("charcoal_yards",)) if edge_gap(_cy, _o) < 30.0 / _cd_ftpx]
        if _cy_near:
            _cy_tight.append((round(_cy["x"]), round(_cy["y"])))
    return _kept(locals(), ('_cy', '_cy_near', '_cy_tight', '_o'))


def _seg_0084__charcoal_yard_keeps_fire_gap(*, _cy_tight: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 84 (charcoal_yard_keeps_fire_gap) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "charcoal_yard_keeps_fire_gap",
        not _cy_tight,
        f"charcoal yard(s) crowding a neighboring structure at {_cy_tight[:3]} - a charcoal stack self-heats and can ignite with nobody watching it, so the yard stands >= ~30 real ft clear of every footprint (about one flame-height off a fully-involved stack); settlements/urban-features.md 'CHARCOAL YARDS'",
    )
    return _kept(locals(), ())


# THE COOLING APRON is part of the record's contract, not decoration: a yard that put arriving
# loads straight under cover with the conditioned stock is the yard that burns down. A yard
# drawn without one is recording a layout nobody would build.


def _seg_0085___cy_1(*, _cy: Any = _UNBOUND, _cy_all: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 85 (_cy, _cy_noapron) - body verbatim from the legacy gate() (feature 022)."""
    _cy_noapron = [(round(_cy["x"]), round(_cy["y"])) for _cy in _cy_all if not _cy.get("apron") or not _cy.get("sheds")]
    return _kept(locals(), ('_cy', '_cy_noapron'))


def _seg_0086__charcoal_yard_has_cooling_ground(*, _cy_noapron: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 86 (charcoal_yard_has_cooling_ground) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "charcoal_yard_has_cooling_ground",
        not _cy_noapron,
        f"charcoal yard(s) with no open cooling apron or no roofed shed at {_cy_noapron[:3]} - fresh charcoal must stand in the OPEN, apart from conditioned stock, before it goes under cover (the 24-hour rule), and the conditioned stock must be ROOFED because a damp burn loses the premium the trade exists for",
    )
    return _kept(locals(), ())


def _seg_0087__settlement_has_refining_forge(*, _rf_all: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 87 (settlement_has_refining_forge) - body verbatim from the legacy gate() (feature 022)."""
    if meta.get("iron_district"):
        check(
            "settlement_has_refining_forge",
            bool(_rf_all),
            "meta(iron_district=True) declares an iron district - it must draw the refinery that turns hill-smelted pig into bar (s.refining_forge: an open-sided two-hearth okajiba + charcoal store + slag heap). The SMELTING furnaces are never drawn: a kiln reduces six parts wood to one of charcoal, so the furnace follows the fuel out into the hills",
        )
    return _kept(locals(), ())


def _seg_0088__refining_forge_stands_off_dwellings(
    *,
    M: Any = _UNBOUND,
    _RF_WINDV: Any = _UNBOUND,
    _b: Any = _UNBOUND,
    _cd_ftpx: Any = _UNBOUND,
    _h: Any = _UNBOUND,
    _p: Any = _UNBOUND,
    _r: Any = _UNBOUND,
    _rf2: Any = _UNBOUND,
    _rf_all: Any = _UNBOUND,
    _rf_close: Any = _UNBOUND,
    _rf_cx: Any = _UNBOUND,
    _rf_cy2: Any = _UNBOUND,
    _rf_dwell_pts: Any = _UNBOUND,
    _rf_homes: Any = _UNBOUND,
    _rf_upwind: Any = _UNBOUND,
    _rf_wind: Any = _UNBOUND,
    _rf_wx: Any = _UNBOUND,
    _rf_wy: Any = _UNBOUND,
    check: Any = _UNBOUND,
    meta: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 88 (refining_forge_downwind, refining_forge_stands_off_dwellings) - body verbatim from the legacy gate() (feature 022)."""
    if _rf_all:
        _rf_homes = M.get("houses", []) + [_b for _b in M.get("buildings", []) if _b.get("kind") in DWELLING_KINDS]
        # THE STANDOFF. A fining hearth is an OPEN fire under a forced blast, worked with a rod
        # while the iron is semi-molten - so the sparks, the noise and the smoke are not incidental
        # to the process, they ARE the process. 60 ft is half the putrefaction figure (this does not
        # rot) and double the charcoal yard's (a live attended fire is a worse ignition source than
        # a fuel stack, but somebody is standing at it).
        _rf_close = []
        for _rf2 in _rf_all:
            if any(edge_gap(_rf2, _h) < 60.0 / _cd_ftpx for _h in _rf_homes):
                _rf_close.append((round(_rf2["x"]), round(_rf2["y"])))
        check(
            "refining_forge_stands_off_dwellings",
            not _rf_close,
            f"refining forge(s) among the housing at {_rf_close[:3]} - an open charcoal hearth under a forced blast throws sparks, noise and smoke all season, so it stands >= ~60 real ft off every dwelling (half the crematory/tannery nuisance figure, double the charcoal yard's fire gap)",
        )
        # SMOKE GOES DOWNWIND, FILTH GOES DOWNSTREAM - two separate axes, and this is the rule for
        # the first of them. Keyed off the map's own meta(windward=...) (default NW, the East Asian
        # winter monsoon), so a map with a different exposure gets a different answer rather than a
        # hardcoded corner. On a map where downwind and downstream point the same way this looks
        # redundant; on one where they diverge it is the only thing placing the forge.
        _RF_WINDV = {"N": (0.0, -1.0), "S": (0.0, 1.0), "E": (1.0, 0.0), "W": (-1.0, 0.0), "NW": (-1.0, -1.0), "NE": (1.0, -1.0), "SW": (-1.0, 1.0), "SE": (1.0, 1.0)}
        _rf_wind = str(meta.get("windward", "NW")).upper().strip()
        _rf_wx, _rf_wy = _RF_WINDV.get(_rf_wind, (-1.0, -1.0))
        _rf_dwell_pts = [(_h["x"], _h["y"]) for _h in _rf_homes]
        if _rf_dwell_pts:
            _rf_cx = sum(_p[0] for _p in _rf_dwell_pts) / len(_rf_dwell_pts)
            _rf_cy2 = sum(_p[1] for _p in _rf_dwell_pts) / len(_rf_dwell_pts)
            # downwind is the direction the wind BLOWS TOWARD, i.e. away from the windward quarter
            _rf_upwind = [(round(_r["x"]), round(_r["y"])) for _r in _rf_all if (_r["x"] - _rf_cx) * -_rf_wx + (_r["y"] - _rf_cy2) * -_rf_wy <= 0]
            check(
                "refining_forge_downwind",
                not _rf_upwind,
                f"refining forge(s) UPWIND of the housing at {_rf_upwind[:3]} - the prevailing wind is declared {_rf_wind}, so the forge's smoke must be carried away from the dwellings, not over them; put it on the downwind side of the settlement's center of housing",
            )
    return _kept(locals(), ('_RF_WINDV', '_b', '_h', '_p', '_r', '_rf2', '_rf_close', '_rf_cx', '_rf_cy2', '_rf_dwell_pts', '_rf_homes', '_rf_upwind', '_rf_wind', '_rf_wx', '_rf_wy'))


# ===== THE KILN WORKS (GM 2026-07-27; grounding in settlements/urban-features.md "KILN WORKS",
# research record in research/urban-features.md). The GM's two questions - "would whoever works
# the kiln also live next to it?" and "why is it specifically a tile kiln?" - turned a lone
# mound glyph into a works. The short answers the checks below enforce:
#
#   - THE WORKERS LIVE AT THE KILN. A firing runs for DAYS, stoked in shifts round the clock,
#     and the works stands at its CLAY rather than at its customers, so digging, weathering,
#     throwing, drying and firing all happen at one spot. China first: Song/Ming kiln districts
#     were worked by registered kiln households living at their kilns (Jingdezhen is a city
#     grown around them); Japan corroborates with Seto, Tokoname, Imado, Awataguchi.
#   - THE HOUSING IS NOT BANISHED WITH THE WORK. Fire law puts the kiln outside the wall
#     (city_kiln_outside_walls) to keep the risk out of the dense blocks; it says nothing
#     against the households whose trade it is. They keep the ordinary fire gap, no more.
#
# THE 60 FT RUNG on the separation ladder above is deliberate rather than new. A firing is a
# very large fire, but an ATTENDED one - somebody is stoking it, which is the whole reason it
# runs in shifts - so it sits with the refining forge (a live worked fire) and not with the
# unattended charcoal stack at 30 ft or the nuisance figures at 120 ft, where a smell carried
# on air is the hazard. Duration here does the work the forced blast does there.
#
# SCOPED ON THE FEATURE, NOT THE SCALE, like the charcoal-district siting checks and for the
# same reason: a kiln drawn on any map is validated, whatever it declares.


def _seg_0089___kn_all(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 89 (_kn_all) - body verbatim from the legacy gate() (feature 022)."""
    _kn_all = M.get("kilns", [])
    return _kept(locals(), ('_kn_all',))


def _seg_0090___kn_ftpx(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 90 (_kn_ftpx) - body verbatim from the legacy gate() (feature 022)."""
    _kn_ftpx = float(meta.get("ftpx") or 1.0)
    return _kept(locals(), ('_kn_ftpx',))


def _seg_0091__kiln_works_houses_its_workers(
    *,
    M: Any = _UNBOUND,
    _kn: Any = _UNBOUND,
    _kn_all: Any = _UNBOUND,
    _kn_b: Any = _UNBOUND,
    _kn_ftpx: Any = _UNBOUND,
    _kn_homeless: Any = _UNBOUND,
    _kn_near: Any = _UNBOUND,
    _kn_o: Any = _UNBOUND,
    _kn_rec: Any = _UNBOUND,
    _kn_tight: Any = _UNBOUND,
    check: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 91 (kiln_keeps_fire_gap, kiln_works_houses_its_workers) - body verbatim from the legacy gate() (feature 022)."""
    if _kn_all:
        _kn_homeless = [(round(_kn["x"]), round(_kn["y"])) for _kn in _kn_all if not _kn.get("quarters")]
        check(
            "kiln_works_houses_its_workers",
            not _kn_homeless,
            f"kiln(s) with no quarters recorded at {_kn_homeless[:3]} - a kiln is not premises somebody commutes to: a firing is stoked in shifts for days on end and the works stands at its clay, so the households that work it LIVE there. Draw the works, not a lone kiln (s.kiln records `quarters`); settlements/urban-features.md 'KILN WORKS'",
        )
        # The gap is measured from the KILN BODY, not from the works' bounding ground - the whole
        # point of a works is that its own cottages stand inside that ground, so a bounding-rect
        # test could only ever measure the fire gap to somebody else's house. A record with no
        # `body` FAILS rather than skipping: an unmeasurable rule that reports nothing looks
        # exactly like a rule that passed (this file's standing hazard).
        _kn_tight = []
        for _kn in _kn_all:
            _kn_b = _kn.get("body")
            if not _kn_b:
                _kn_tight.append((round(_kn["x"]), round(_kn["y"])))
                continue
            _kn_rec = {"x": _kn_b[0], "y": _kn_b[1], "w": _kn_b[2], "h": _kn_b[3], "rot": _kn_b[4]}
            _kn_near = kiln_quarters(_kn)
            _kn_near += solid_structs(M, "manors", "religious", exclude=("kilns",))
            if any(edge_gap(_kn_rec, _kn_o) < 60.0 / _kn_ftpx for _kn_o in _kn_near):
                _kn_tight.append((round(_kn["x"]), round(_kn["y"])))
        check(
            "kiln_keeps_fire_gap",
            not _kn_tight,
            f"kiln(s) crowding a dwelling or a neighboring structure at {_kn_tight[:3]} - a firing is a very large fire burning for days, so the kiln stands >= ~60 real ft clear of every footprint INCLUDING its own workers' cottages (the attended-fire rung of the separation ladder, with the refining forge; a record carrying no `body` fails here because the gap cannot be measured at all)",
        )
    return _kept(locals(), ('_kn', '_kn_b', '_kn_homeless', '_kn_near', '_kn_o', '_kn_rec', '_kn_tight'))


# TROUGH RECTS DRAW ON OPEN GROUND - the cluster's drawn BOX must not clip any structure (GM
# 2026-07-23, after Tango's caravan cluster hugged its well on a near-vertical ray and the
# bottom trough clipped the well-house roof corner: the old fixed offset only guaranteed
# HORIZONTAL clearance - the stack is taller than it is wide - and only the cluster CENTER was
# point-checked, so the rects themselves could land on footprints). Placement records the
# drawn extent as `troughs_box`; it is tested against every solid footprint (the yard's own
# keep kinds + houses, rotation-exact via SAT) and every wellhead roof square (vr). A yard
# with troughs but no recorded box fails - the extent is part of the record's contract.


def _seg_0092___tb_bad() -> dict[str, Any]:
    """Gate segment 92 (_tb_bad) - body verbatim from the legacy gate() (feature 022)."""
    _tb_bad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('_tb_bad',))


def _seg_0093___tb(
    *,
    M: Any = _UNBOUND,
    _tb: Any = _UNBOUND,
    _tb_b: Any = _UNBOUND,
    _tb_bad: Any = _UNBOUND,
    _tb_hit: Any = _UNBOUND,
    _tb_k: Any = _UNBOUND,
    _tb_poly: Any = _UNBOUND,
    _tb_w: Any = _UNBOUND,
    _tb_yd: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 93 (_tb, _tb_b, _tb_bad, _tb_hit) - body verbatim from the legacy gate() (feature 022)."""
    for _tb_yd in M.get("stable_yards", []):
        if not _tb_yd.get("troughs"):
            continue
        _tb = _tb_yd.get("troughs_box")
        if not _tb:
            _tb_bad.append((round(_tb_yd["x"]), round(_tb_yd["y"])))
            continue
        _tb_poly = [(_tb[0], _tb[1]), (_tb[2], _tb[1]), (_tb[2], _tb[3]), (_tb[0], _tb[3])]
        _tb_hit = any(
            "w" in _tb_b and "h" in _tb_b and sat_overlap(_tb_poly, rect_corners(_struct_rect(_tb_b)))
            for _tb_k in ("buildings", "flophouses", "storehouses", "merchant_estates", "ministries", "religious", "manors", "cemeteries", "mausoleums", "cremation_grounds", "ossuaries", "houses")
            for _tb_b in M.get(_tb_k, []) or []
        ) or any(
            _tb[0] < _tb_w["x"] + _tb_w.get("vr", 4.0) and _tb[2] > _tb_w["x"] - _tb_w.get("vr", 4.0) and _tb[1] < _tb_w["y"] + _tb_w.get("vr", 4.0) and _tb[3] > _tb_w["y"] - _tb_w.get("vr", 4.0)
            for _tb_w in M.get("wells", [])
        )
        if _tb_hit:
            _tb_bad.append((round(_tb_yd["x"]), round(_tb_yd["y"])))
    return _kept(locals(), ('_tb', '_tb_b', '_tb_bad', '_tb_hit', '_tb_k', '_tb_poly', '_tb_w', '_tb_yd'))


def _seg_0094__stable_troughs_clear_of_buildings(*, _tb_bad: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 94 (stable_troughs_clear_of_buildings) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "stable_troughs_clear_of_buildings",
        not _tb_bad,
        f"stable-yard trough rects clip a structure (or went unrecorded) at yards {_tb_bad[:3]} - the drawn cluster box (troughs_box) must sit on open ground, clear of every building footprint and wellhead roof; s._stable_yard's direction-aware offset + box corner-check places it (settlements.md 'Stable yard' watering)",
    )
    return _kept(locals(), ())


# HITCHING RAILS + DUNG HEAPS keep off the ROADS and the WALL (GM 2026-07-24). The road-side
# rail's whole PURPOSE is keeping tethered stock off the through-road, so a rail whose drawn
# extent (posts included) reaches the roadbed defeats itself and bars the public way; a dung
# heap on the tread fouls it, and either against the rampart sits in the wall's patrol
# clearance. The old placement tested only each glyph's CENTER point, so an 18px rail could
# lay its tip on a road or against the wall; s._stable_yard now probes the full extent AND
# records the furniture ('rails' / 'dung_heaps' on each M['stable_yards'] entry) so this
# check can hold the drawn geometry to it.


def _seg_0095___sy_yards(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 95 (_sy_yards) - body verbatim from the legacy gate() (feature 022)."""
    _sy_yards = M.get("stable_yards", [])
    return _kept(locals(), ('_sy_yards',))


def _seg_0096__dung_heaps_clear_of_hitch_rails(
    *,
    M: Any = _UNBOUND,
    _FW_WALL_HALF: Any = _UNBOUND,
    _al: Any = _UNBOUND,
    _dh: Any = _UNBOUND,
    _dh2: Any = _UNBOUND,
    _dh_all_rails: Any = _UNBOUND,
    _dh_bad2: Any = _UNBOUND,
    _fw_bad: Any = _UNBOUND,
    _fw_hit: Any = _UNBOUND,
    _fw_wall: Any = _UNBOUND,
    _fw_ways: Any = _UNBOUND,
    _half: Any = _UNBOUND,
    _hw: Any = _UNBOUND,
    _pl: Any = _UNBOUND,
    _rh2: Any = _UNBOUND,
    _rl: Any = _UNBOUND,
    _rl2: Any = _UNBOUND,
    _st: Any = _UNBOUND,
    _sy_yards: Any = _UNBOUND,
    _t: Any = _UNBOUND,
    _yd: Any = _UNBOUND,
    _yd2: Any = _UNBOUND,
    check: Any = _UNBOUND,
    i: Any = _UNBOUND,
    pad: Any = _UNBOUND,
    qx: Any = _UNBOUND,
    qy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 96 (dung_heaps_clear_of_hitch_rails, stable_yard_furniture_clear_of_roads_walls) - body verbatim from the legacy gate() (feature 022)."""
    if _sy_yards:
        _fw_ways: list[tuple[list[Any], float]] = []  # type: ignore[no-redef]
        if M.get("road"):
            _fw_ways.append((M["road"], M.get("road_width", 26) / 2))
        if M.get("ring_road"):
            _fw_ways.append((M["ring_road"], M.get("ring_road_width", 20) / 2))
        for _st in M.get("town_streets", []) or []:
            _fw_ways.append((_st["pts"], _st.get("w", 6) / 2))
        for _al in M.get("alleys", []) or []:
            _fw_ways.append((_al["pts"], _al.get("w", 4) / 2))
        _fw_wall = M.get("wall")
        _FW_WALL_HALF = 5.0  # the rampart stroke + a hair of patrol clearance

        def _fw_hit(qx: float, qy: float, pad: float) -> bool:
            for _pl, _hw in _fw_ways:
                if any(seg_dist(qx, qy, _pl[i], _pl[i + 1]) < _hw + pad for i in range(len(_pl) - 1)):
                    return True
            return _fw_wall is not None and any(seg_dist(qx, qy, _fw_wall[i], _fw_wall[i + 1]) < _FW_WALL_HALF + pad for i in range(len(_fw_wall) - 1))

        _fw_bad: list[tuple[float, float]] = []  # type: ignore[no-redef]
        for _yd in _sy_yards:
            for _rl in _yd.get("rails", []) or []:
                _half = _rl["len"] / 2 + _rl.get("reach", 2.4)
                if any(_fw_hit(_rl["x"] + _rl["tx"] * _t, _rl["y"] + _rl["ty"] * _t, 0.0) for _t in (-_half, -_half / 2, 0.0, _half / 2, _half)):
                    _fw_bad.append((round(_rl["x"]), round(_rl["y"])))
            for _dh in _yd.get("dung_heaps", []) or []:
                if _fw_hit(_dh["x"], _dh["y"], max(_dh.get("rx", 2.5), _dh.get("ry", 1.8))):
                    _fw_bad.append((round(_dh["x"]), round(_dh["y"])))
        # ... AND DUNG HEAPS KEEP CLEAR OF THE HITCHING RAILS (GM 2026-07-25, two render
        # reviews): both flanks of a rail are working tie-up space - a heap dumped against it
        # sits where the animals stand and blocks one side. Round 1 floored at 14px (42 ft),
        # "just beyond the ~9px animal row" - the GM still read the result as directly against
        # the posts (a heap edge ~8 ft off the animals' rumps IS the working row), and the loop
        # paired each heap only with its OWN yard's rails, so Nagahara carried a heap 22.5px
        # from a NEIGHBORING yard's rail that nothing measured. Round 2: floor 24px (72 ft)
        # from EVERY rail on the map (placement holds 25 for slack) - the heap's edge ends
        # ~38 ft past the animal row, clearly out of the tie-up space, still close enough to
        # read as the yard's muck pile. Fixtures: the pinned Tango (7.9px) + Nagahara (12.6px)
        # round-1 captures, plus the round-2 Nagahara capture (16.4px same-yard + 22.5px
        # cross-yard) that PASSED the round-1 floor.
        _dh_all_rails = [_rl2 for _yd2 in _sy_yards for _rl2 in _yd2.get("rails", []) or []]
        _dh_bad2 = []
        for _yd2 in _sy_yards:
            for _dh2 in _yd2.get("dung_heaps", []) or []:
                for _rl2 in _dh_all_rails:
                    _rh2 = _rl2["len"] / 2
                    if seg_dist(_dh2["x"], _dh2["y"], (_rl2["x"] - _rl2["tx"] * _rh2, _rl2["y"] - _rl2["ty"] * _rh2), (_rl2["x"] + _rl2["tx"] * _rh2, _rl2["y"] + _rl2["ty"] * _rh2)) < 24.0:
                        _dh_bad2.append((round(_dh2["x"]), round(_dh2["y"])))
                        break
        check(
            "dung_heaps_clear_of_hitch_rails",
            not _dh_bad2,
            f"dung heap(s) against a hitching rail at {_dh_bad2} - both flanks of every rail on the map are tie-up "
            f"space, so a heap keeps ~24px (72 ft) clear of each rail line, its edge well past the row where the "
            f"animals stand (the 14px round-1 floor still read as touching); near the yard's working edge is "
            f"right, in the tie-up row is not",
        )
        check(
            "stable_yard_furniture_clear_of_roads_walls",
            not _fw_bad,
            f"hitching rail(s)/dung heap(s) overlapping a road or the wall at {_fw_bad[:4]} - yard furniture "
            f"keeps off the public tread and the rampart's clearance (the road-side rail exists to keep stock "
            f"OFF the through-road); s._stable_yard probes each rail's full extent and each heap's edge",
        )
    return _kept(
        locals(), ('_FW_WALL_HALF', '_al', '_dh', '_dh2', '_dh_all_rails', '_dh_bad2', '_fw_bad', '_fw_hit', '_fw_wall', '_fw_ways', '_half', '_rh2', '_rl', '_rl2', '_st', '_t', '_yd', '_yd2')
    )
