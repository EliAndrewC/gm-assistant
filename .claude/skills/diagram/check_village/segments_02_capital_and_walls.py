"""Gate segments (capital and walls) - bodies verbatim from check_village.py (feature 024 package split; registry order preserved)."""

import math
from typing import Any

from settlement import KIDO_TOWER_KEEPCLEAR, WALL_DEFENSE, rail_quad, sat_overlap, trough_quad, wellhead_quad

from .common_01_geometry import Poly, _struct_rect, point_in_poly, poly_area, poly_dist, rect_corners, seg_closest, seg_dist, solid_structs
from .common_02_overlap_policy import GridIndex, check_ring_road_clear, onmap_field_edge
from .common_03_capacity import (
    _UNBOUND,
    BUDGET_TOL_OVER,
    BUDGET_TOL_UNDER,
    BURIAL_AC_BAND,
    BUSINESS_KINDS,
    CREMATION_FT_MAX_CITY,
    CREMATION_FT_MAX_TOWN,
    CREMATION_FT_MIN,
    DOOR_CLEAR_FT,
    DWELLING_KINDS,
    GATE_FT_MAX,
    GATE_FT_MIN,
    OSSUARY_FT_MAX,
    OSSUARY_FT_MIN,
    WALL_FT_MAX,
    WALL_FT_MIN,
    _kept,
)

# WELLS, TROUGHS, AND HITCHING POSTS NEVER OVERLAP ONE ANOTHER (GM 2026-07-25). The motivating
# defect was Nagahara's flophouse yard: a hitching rail drawn straight ACROSS a wellhead, with
# the trough cluster stacked on both - three glyphs on one spot, where a reader can no longer
# tell which is which, and the layout it implies is nonsense (nobody draws water through a rail,
# and no yard ties its animals over its own draw-point). They collide because they are placed at
# three different moments - the wells long before the yard exists, the rails when it draws, the
# cluster after - so nothing had ever measured the pair. This check is deliberately GEOMETRIC
# and glyph-level: it demands only that the DRAWN extents not intersect, not any working
# clearance, because the troughs are SUPPOSED to hug their well (the bucket-pour relay,
# stable_troughs_beside_well) and animals are supposed to stand between rail and trough. Near is
# right; on top of is not. Extents come from the shared quad builders in settlement.py, the same
# ones s._stable_yard places against (with YARD_GLYPH_SLACK of margin), so placement and check
# can never drift apart. Every pair on the map is tested, ACROSS yards as well as within one -
# the cross-yard hole is what the dung-heap rule had to be widened for twice.


def _seg_0097___wtr() -> dict[str, Any]:
    """Gate segment 97 (_wtr) - body verbatim from the legacy gate() (feature 022)."""
    _wtr: list[tuple[str, list[tuple[float, float]], float, float, float]] = []
    return _kept(locals(), ('_wtr',))


def _seg_0098___wtr_1(*, _wtr: Any = _UNBOUND, cx: Any = _UNBOUND, cy: Any = _UNBOUND, kind: Any = _UNBOUND, qx: Any = _UNBOUND, qy: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 98 (_wtr, _wtr_add) - body verbatim from the legacy gate() (feature 022)."""

    def _wtr_add(kind: str, quad: list[tuple[float, float]], cx: float, cy: float) -> None:
        _wtr.append((kind, quad, cx, cy, max(math.hypot(qx - cx, qy - cy) for qx, qy in quad)))

    return _kept(locals(), ('_wtr', '_wtr_add'))


def _seg_0099___wtr_2(*, M: Any = _UNBOUND, _wtr: Any = _UNBOUND, _wtr_add: Any = _UNBOUND, _wtr_w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 99 (_wtr, _wtr_w) - body verbatim from the legacy gate() (feature 022)."""
    for _wtr_w in M.get("wells", []) or []:
        _wtr_add("well", wellhead_quad(_wtr_w), _wtr_w["x"], _wtr_w["y"])
    return _kept(locals(), ('_wtr', '_wtr_w'))


def _seg_0100___wtr_3(*, M: Any = _UNBOUND, _wtr: Any = _UNBOUND, _wtr_add: Any = _UNBOUND, _wtr_box: Any = _UNBOUND, _wtr_rl: Any = _UNBOUND, _wtr_yd: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 100 (_wtr, _wtr_box, _wtr_rl, _wtr_yd) - body verbatim from the legacy gate() (feature 022)."""
    for _wtr_yd in M.get("stable_yards", []) or []:
        _wtr_box = _wtr_yd.get("troughs_box")
        if _wtr_box:
            _wtr_add("troughs", trough_quad(_wtr_box), (_wtr_box[0] + _wtr_box[2]) / 2, (_wtr_box[1] + _wtr_box[3]) / 2)
        for _wtr_rl in _wtr_yd.get("rails", []) or []:
            _wtr_add("hitching rail", rail_quad(_wtr_rl), _wtr_rl["x"], _wtr_rl["y"])
    return _kept(locals(), ('_wtr', '_wtr_box', '_wtr_rl', '_wtr_yd'))


def _seg_0101___wtr_bad() -> dict[str, Any]:
    """Gate segment 101 (_wtr_bad) - body verbatim from the legacy gate() (feature 022)."""
    _wtr_bad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('_wtr_bad',))


def _seg_0102___ax(
    *,
    _ax: Any = _UNBOUND,
    _ay: Any = _UNBOUND,
    _bx: Any = _UNBOUND,
    _by: Any = _UNBOUND,
    _ka: Any = _UNBOUND,
    _kb: Any = _UNBOUND,
    _qa: Any = _UNBOUND,
    _qb: Any = _UNBOUND,
    _ra: Any = _UNBOUND,
    _rb: Any = _UNBOUND,
    _wtr: Any = _UNBOUND,
    _wtr_bad: Any = _UNBOUND,
    _wtr_i: Any = _UNBOUND,
    _wtr_j: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 102 (_ax, _ay, _bx, _by) - body verbatim from the legacy gate() (feature 022)."""
    for _wtr_i in range(len(_wtr)):
        _ka, _qa, _ax, _ay, _ra = _wtr[_wtr_i]
        for _wtr_j in range(_wtr_i + 1, len(_wtr)):
            _kb, _qb, _bx, _by, _rb = _wtr[_wtr_j]
            if math.hypot(_ax - _bx, _ay - _by) > _ra + _rb:  # circumradii cannot reach: no overlap possible
                continue
            if sat_overlap(_qa, _qb):
                _wtr_bad.append((f"{_ka}/{_kb}", round(_ax), round(_ay)))
    return _kept(locals(), ('_ax', '_ay', '_bx', '_by', '_ka', '_kb', '_qa', '_qb', '_ra', '_rb', '_wtr_bad', '_wtr_i', '_wtr_j'))


def _seg_0103__wells_troughs_rails_clear_of_each_other(*, _wtr_bad: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 103 (wells_troughs_rails_clear_of_each_other) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "wells_troughs_rails_clear_of_each_other",
        not _wtr_bad,
        f"wellhead/trough/hitching-rail glyphs drawn on top of each other at {_wtr_bad[:4]} - these three "
        f"stand SIDE BY SIDE at a watering point (the troughs hug their well, the animals stand between rail "
        f"and trough), but their drawn extents must not intersect: stacked, they read as one unidentifiable "
        f"smear and imply a yard that ties its stock across its own draw-point (s._stable_yard's _glyph_free "
        f"places all three; settlements.md 'Stable yard' watering)",
    )
    return _kept(locals(), ())


# WALL TOWER COVERAGE by the city's DEFENSE POSTURE (GM 2026-07-22): the interlocking-flanking-fire rule
# (侧射; Shen Kuo's 11th-c. 矢石相及 - adjacent mamian's fields of fire overlap so an attacker at the base
# is hit from >=2 towers). TUNABLE per city (meta wall_defense): `siege` = aimed-lethal bowshot (60 m /
# 197 ft), >=2 towers everywhere; `garrison` = full war-bow reach (100 m / 328 ft), >=2; `peaceful` = the
# sparser Xi'an spacing, >=1 flanking tower within aimed-lethal range everywhere (midpoints get 2). Every
# point on the wall CURTAIN must have >= the tier's min-count of towers within the tier's arrow range;
# the gate OPENING itself is exempt (a defended chokepoint with its own gate tower + guard, not open
# curtain). Both mural and gate towers count. See settlements.md 'Historical grounding'.


def _seg_0104__city_wall_tower_coverage(
    *,
    M: Any = _UNBOUND,
    URBAN: Any = _UNBOUND,
    _R: Any = _UNBOUND,
    _a: Any = _UNBOUND,
    _arc_of: Any = _UNBOUND,
    _b: Any = _UNBOUND,
    _barb: Any = _UNBOUND,
    _cnt: Any = _UNBOUND,
    _cum: Any = _UNBOUND,
    _dd: Any = _UNBOUND,
    _dx: Any = _UNBOUND,
    _dy: Any = _UNBOUND,
    _fx: Any = _UNBOUND,
    _fy: Any = _UNBOUND,
    _g: Any = _UNBOUND,
    _gate_skip: Any = _UNBOUND,
    _gates: Any = _UNBOUND,
    _gmed: Any = _UNBOUND,
    _gsort: Any = _UNBOUND,
    _gx: Any = _UNBOUND,
    _gy: Any = _UNBOUND,
    _i: Any = _UNBOUND,
    _kx: Any = _UNBOUND,
    _ky: Any = _UNBOUND,
    _mincov: Any = _UNBOUND,
    _mur_tw: Any = _UNBOUND,
    _ns: Any = _UNBOUND,
    _nw: Any = _UNBOUND,
    _p: Any = _UNBOUND,
    _px: Any = _UNBOUND,
    _py: Any = _UNBOUND,
    _q: Any = _UNBOUND,
    _rng_ft: Any = _UNBOUND,
    _s: Any = _UNBOUND,
    _sl: Any = _UNBOUND,
    _t: Any = _UNBOUND,
    _tgaps: Any = _UNBOUND,
    _thin: Any = _UNBOUND,
    _tier: Any = _UNBOUND,
    _tight: Any = _UNBOUND,
    _tpos: Any = _UNBOUND,
    _tw: Any = _UNBOUND,
    _tx: Any = _UNBOUND,
    _tx2: Any = _UNBOUND,
    _ty: Any = _UNBOUND,
    _ty2: Any = _UNBOUND,
    _wall: Any = _UNBOUND,
    _wg: Any = _UNBOUND,
    _wx: Any = _UNBOUND,
    _wy: Any = _UNBOUND,
    best_d: Any = _UNBOUND,
    check: Any = _UNBOUND,
    g: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    t: Any = _UNBOUND,
    w: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 104 (city_wall_tower_coverage, wall_towers_evenly_spaced) - body verbatim from the legacy gate() (feature 022)."""
    if URBAN and M.get("wall"):
        _wall = M["wall"]
        _tier = meta.get("wall_defense", "garrison")
        _rng_ft, _mincov = WALL_DEFENSE.get(_tier, WALL_DEFENSE["garrison"])
        _R = _rng_ft / float(meta.get("ftpx") or 3.0) + 12.0  # +12 px: a mamian's half-footprint - an archer shoots from the tower's parapet span, not its center point
        _tw = [(t["x"], t["y"]) for t in M.get("wall_towers", [])] + [(g["x"], g["y"]) for g in M.get("gate_structs", []) if g.get("kind") == "tower"]
        _gates = M.get("gates", [])
        _barb = [(g["x"], g["y"]) for g in M.get("gate_structs", []) if g.get("kind") in ("guardhouse", "inspection")]  # barbican guard structures
        _wg = [(w["x"], w["y"]) for w in M.get("water_gates", [])]  # shuimen arches - fortified openings, flanked by their own two towers
        _gate_skip = (
            130.0  # px around a gate to exclude from the curtain sample: the gate is a BARBICAN - the most fortified point (gate tower + guard house + inspection + gateposts), not open curtain
        )
        _thin = []
        _nw = len(_wall)
        for _i in range(_nw):
            _a, _b = _wall[_i], _wall[(_i + 1) % _nw]
            _sl = math.hypot(_b[0] - _a[0], _b[1] - _a[1])
            _ns = max(1, int(_sl / 18))
            for _s in range(_ns):
                _t = (_s + 0.5) / _ns
                _px, _py = _a[0] + (_b[0] - _a[0]) * _t, _a[1] + (_b[1] - _a[1]) * _t
                if any(math.hypot(_px - _gx, _py - _gy) < _gate_skip for _gx, _gy in _gates) or any(math.hypot(_px - _fx, _py - _fy) < 55 for _fx, _fy in _barb):
                    continue  # inside the gate barbican (gate + its guard house + inspection) - a defended complex, not open curtain
                if any(math.hypot(_px - _wx, _py - _wy) < 45 for _wx, _wy in _wg):
                    continue  # abutting a water gate: a fortified shuimen opening flanked by its own two towers - the placement code (_seat_mural) will not tower this 40px keep-out, so the check must not demand it (check keep-outs mirror placement keep-outs)
                if any(math.hypot(_px - _kx, _py - _ky) < KIDO_TOWER_KEEPCLEAR for _kx, _ky in M.get("wall_tower_keepclears", [])):
                    continue  # a ward-fence junction on the rampart (its kido ward-gate is a manned chokepoint): placement keeps towers KIDO_TOWER_KEEPCLEAR clear of it, so demanding 2-coverage here forces a doubled tower just outside the band (the wall_towers_evenly_spaced artifact) - same mirror-the-keep-out doctrine as the water gate above
                _cnt = sum(1 for _tx, _ty in _tw if math.hypot(_px - _tx, _py - _ty) <= _R)
                if _cnt < _mincov:
                    _thin.append((round(_px), round(_py), _cnt))
        check(
            "city_wall_tower_coverage",
            not _thin,
            f"{len(_thin)} wall point(s) covered by fewer than {_mincov} tower(s) within the {_tier} arrow range ({_rng_ft:.0f} ft): {_thin[:4]} (x, y, towers-in-range) - a {_tier} city's rampart must keep every curtain point under flanking fire from {_mincov} tower(s); tower the wall closer (meta wall_defense sets the spacing; settlements.md 'Historical grounding')",
        )

        # EVEN TOWER RHYTHM (GM 2026-07-23): Tango's east curtain ran ...54, 76, 32, 54... - two mamian
        # nearly touching in one spot on an otherwise even ring, visually distracting and historically
        # wrong (mural towers were built at REGULAR flanking intervals - the same doctrine the coverage
        # rule above encodes - so a doubled tower reads as an error, not a defensive choice). Cause: the
        # coverage-remediation pass's old 28px min-separation let a hole-filling tower seat right beside
        # a neighbor instead of at the local span midpoint. Placement now floors mural separation at
        # 0.75x the tier's spacing cap (strictly tighter than this gate, since the median gap never
        # exceeds the cap - so placement and check cannot disagree); this gates the RESULT: no
        # consecutive mural gap along the curtain may fall under 0.7x the map's median gap. Gate and
        # water-gate flanking towers are exempt (a barbican pair is legitimately tight). Calibration
        # 2026-07-23: the three defective pairs sat at 0.58-0.60x median; every legitimate gap in the
        # pool sat at >= 0.87x - 0.7 splits the bands with margin on both sides.
        _mur_tw = [
            (t["x"], t["y"])
            for t in M.get("wall_towers", [])
            if not any(math.hypot(t["x"] - _gx, t["y"] - _gy) < _gate_skip for _gx, _gy in _gates) and not any(math.hypot(t["x"] - _wx, t["y"] - _wy) < 130 for _wx, _wy in _wg)
        ]
        if len(_mur_tw) >= 8:
            _cum = [0.0]
            for _i in range(_nw):
                _a, _b = _wall[_i], _wall[(_i + 1) % _nw]
                _cum.append(_cum[-1] + math.hypot(_b[0] - _a[0], _b[1] - _a[1]))

            def _arc_of(px: float, py: float) -> float:
                best_d, best_arc = float("inf"), 0.0
                for _i in range(_nw):
                    _a, _b = _wall[_i], _wall[(_i + 1) % _nw]
                    _dx, _dy = _b[0] - _a[0], _b[1] - _a[1]
                    _sl = _dx * _dx + _dy * _dy
                    _t = max(0.0, min(1.0, ((px - _a[0]) * _dx + (py - _a[1]) * _dy) / _sl)) if _sl else 0.0
                    _dd = math.hypot(px - _a[0] - _t * _dx, py - _a[1] - _t * _dy)
                    if _dd < best_d:
                        best_d, best_arc = _dd, _cum[_i] + _t * math.sqrt(_sl)
                return best_arc

            _tpos = sorted((_arc_of(_tx2, _ty2), _tx2, _ty2) for _tx2, _ty2 in _mur_tw)
            _tgaps = [(_tpos[_i + 1][0] - _tpos[_i][0], _tpos[_i], _tpos[_i + 1]) for _i in range(len(_tpos) - 1)]
            _tgaps.append((_cum[-1] - _tpos[-1][0] + _tpos[0][0], _tpos[-1], _tpos[0]))  # the wrap gap
            _gsort = sorted(_g for _g, _p, _q in _tgaps)
            _gmed = _gsort[len(_gsort) // 2]
            _tight = [(round(_g), (round(_p[1]), round(_p[2])), (round(_q[1]), round(_q[2]))) for _g, _p, _q in _tgaps if _g < 0.7 * _gmed]
            check(
                "wall_towers_evenly_spaced",
                not _tight,
                f"mural tower pair(s) far closer than the wall's rhythm (gap px, tower, tower; median gap {_gmed:.0f}): {_tight[:3]} - "
                f"mamian stand at regular flanking intervals, so no open-curtain gap may fall under 0.7x the median; a doubled tower "
                f"is a remediation-seat artifact, not a defensive choice (gate/water-gate flanking pairs are exempt)",
            )
    return _kept(
        locals(),
        (
            '_R',
            '_a',
            '_arc_of',
            '_b',
            '_barb',
            '_cnt',
            '_cum',
            '_fx',
            '_fy',
            '_g',
            '_gate_skip',
            '_gates',
            '_gmed',
            '_gsort',
            '_gx',
            '_gy',
            '_i',
            '_kx',
            '_ky',
            '_mincov',
            '_mur_tw',
            '_ns',
            '_nw',
            '_p',
            '_px',
            '_py',
            '_q',
            '_rng_ft',
            '_s',
            '_sl',
            '_t',
            '_tgaps',
            '_thin',
            '_tier',
            '_tight',
            '_tpos',
            '_tw',
            '_tx',
            '_tx2',
            '_ty',
            '_ty2',
            '_wall',
            '_wg',
            '_wx',
            '_wy',
            'g',
            't',
            'w',
        ),
    )


def _seg_0105__city_wall_matches_budget(
    *,
    M: Any = _UNBOUND,
    URBAN: Any = _UNBOUND,
    bud: Any = _UNBOUND,
    bud_over: Any = _UNBOUND,
    bud_under: Any = _UNBOUND,
    check: Any = _UNBOUND,
    measured: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    req: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 105 (city_wall_matches_budget) - body verbatim from the legacy gate() (feature 022)."""
    if URBAN and meta.get("walled") and M.get("wall"):
        bud = meta.get("budget")
        if not bud:
            check(
                "city_wall_matches_budget",
                False,
                "no space budget declared - a walled city is sized budget-first: compute citybudget.plan_city(program), take the wall from budget.wall, and record s.meta(budget=budget_to_manifest(budget)) (specs/009-city-area-budget)",
            )
        else:
            measured = poly_area(M["wall"])
            req = float(bud["required_interior_px2"])
            bud_over = measured > req * (1 + BUDGET_TOL_OVER)
            bud_under = measured < req * (1 - BUDGET_TOL_UNDER)
            check(
                "city_wall_matches_budget",
                not (bud_over or bud_under),
                f"the wall encloses {measured:.0f} px^2 vs the budget's required {req:.0f} ({measured / req - 1:+.1%}, tolerance +{BUDGET_TOL_OVER:.0%}/-{BUDGET_TOL_UNDER:.0%}) - "
                + (
                    "unjustified open ground (the empty-space defect): shrink the wall to the budget, or declare+draw the extra ground as reserve/extras lines"
                    if bud_over
                    else "the wall cannot hold the program: enlarge to the budget, or trim the program"
                ),
            )
    return _kept(locals(), ('bud', 'bud_over', 'bud_under', 'measured', 'req'))


# THE CAPITAL TIER IS SIZED BUDGET-FIRST TOO (feature 018, specs/018-capital-space-budget).
# The sibling of city_wall_matches_budget above, at the SAME tolerances - inherited
# deliberately rather than re-derived, because they are pinned by the shipped-Tango /
# rejected-Nagahara pair and nothing about a capital argues for different slack.


def _seg_0106_000__cap_bud(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.000 (cap_bud) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        cap_bud = meta.get("budget")
    return _kept(locals(), ('cap_bud',))


# THE RATCHET (FR-015). A rule gated on an optional declaration is optional in practice:
# three separate times in this engine's history a check silently never RAN while the gate
# stayed green, because the map declared nothing. So a capital that declares no budget
# FAILS here rather than skipping its conformance check. Model: settlement_declares_a_land_fall.


def _seg_0106_001__capital_declares_a_budget(*, cap_bud: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.001 (capital_declares_a_budget) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        check(
            "capital_declares_a_budget",
            bool(cap_bud),
            "no space budget declared - a capital is sized budget-first: compute citybudget.plan_capital(program), take the wall from budget.wall, and record s.meta(budget=budget_to_manifest(budget)). "
            "Without it capital_wall_matches_budget has nothing to compare against and would SKIP, which looks exactly like passing (specs/018-capital-space-budget)",
        )
    return _kept(locals(), ())


def _seg_0106_002__capital_wall_matches_budget(
    *,
    M: Any = _UNBOUND,
    cap_bud: Any = _UNBOUND,
    cap_measured: Any = _UNBOUND,
    cap_over: Any = _UNBOUND,
    cap_req: Any = _UNBOUND,
    cap_under: Any = _UNBOUND,
    check: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0106.002 (capital_wall_matches_budget) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital' and cap_bud and M.get("wall"):
        cap_measured = poly_area(M["wall"])
        cap_req = float(cap_bud["required_interior_px2"])
        cap_over = cap_measured > cap_req * (1 + BUDGET_TOL_OVER)
        cap_under = cap_measured < cap_req * (1 - BUDGET_TOL_UNDER)
        check(
            "capital_wall_matches_budget",
            not (cap_over or cap_under),
            f"the wall encloses {cap_measured:.0f} px^2 vs the budget's required {cap_req:.0f} ({cap_measured / cap_req - 1:+.1%}, tolerance +{BUDGET_TOL_OVER:.0%}/-{BUDGET_TOL_UNDER:.0%}) - "
            + (
                "unjustified open ground (the empty-space defect): shrink the wall to the budget, or declare+draw the extra ground as extras lines"
                if cap_over
                else "the wall cannot hold the program: enlarge to the budget, or trim the program"
            ),
        )
    return _kept(locals(), ('cap_measured', 'cap_over', 'cap_req', 'cap_under'))


# ---- feature 020: the ground-reserving layer ------------------------------------------
# THE GOVERNMENT WARD. Both anchor traditions put the domain ministries OUTSIDE the
# castle, flanking the ceremonial approach: Beijing's Six Ministries lined the Corridor of
# a Thousand Steps outside Chengtianmen, and a jokamachi's offices spilled out of the
# ninomaru into the town as they grew. So a capital shows its six ministries fronting the
# ote-suji - the avenue from the castle's front gate to the through-road - with the House
# Chancellery and the domain school on the same axis (settlements/capitals.md, "The
# government ward"; the research trail is research/cities/capitals.md).


def _seg_0106_003__CAP_SIX(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.003 (CAP_SIX) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        CAP_SIX = ("Rites", "Revenue", "Retainers", "War", "Works", "Justice")
    return _kept(locals(), ('CAP_SIX',))


def _seg_0106_004__cap_mins(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.004 (cap_mins) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        cap_mins = M.get("ministries", [])
    return _kept(locals(), ('cap_mins',))


def _seg_0106_005__cap_by_name(*, cap_mins: Any = _UNBOUND, mi: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.005 (cap_by_name, mi) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        cap_by_name = {(mi.get("name") or ""): mi for mi in cap_mins}
    return _kept(locals(), ('cap_by_name', 'mi'))


def _seg_0106_006__cap_missing(*, CAP_SIX: Any = _UNBOUND, cap_by_name: Any = _UNBOUND, cap_nm: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.006 (cap_missing, cap_nm) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        cap_missing = [f"Ministry of {cap_nm}" for cap_nm in CAP_SIX if f"Ministry of {cap_nm}" not in cap_by_name]
    return _kept(locals(), ('cap_missing', 'cap_nm'))


def _seg_0106_007__capital_has_six_ministries(*, cap_missing: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.007 (capital_has_six_ministries) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        check(
            "capital_has_six_ministries",
            not cap_missing,
            f"missing domain ministries: {cap_missing} - the six domain ministries stand outside the castle flanking the ote-suji (s.ministry(...))",
        )
    return _kept(locals(), ())


# NO House Chancellery compound: the council of lineage representatives meets IN the
# castle (GM 2026-08-09, researched: Edo's Hyojosho and the Roju council sat within Edo
# castle, and China's Grand Secretariat sat inside the palace - the split both anchors
# agree on is EXECUTIVE ministries out, the ruler's COUNCIL in). A chancellery compound
# outside is therefore a defect, not a requirement; the council chamber is part of the
# castle's implied goten. research/cities/capitals.md, "The chancellery meets IN the castle".


def _seg_0106_008__cap_chanc(*, cap_mins: Any = _UNBOUND, mi: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.008 (cap_chanc, mi) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        cap_chanc = [mi for mi in cap_mins if "chancellery" in (mi.get("name") or "").lower()]
    return _kept(locals(), ('cap_chanc', 'mi'))


def _seg_0106_009__capital_chancellery_meets_in_the_castle(*, cap_chanc: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.009 (capital_chancellery_meets_in_the_castle) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        check(
            "capital_chancellery_meets_in_the_castle",
            not cap_chanc,
            f"{len(cap_chanc)} House Chancellery compound(s) drawn outside the castle - the council meets in the goten (implied, never drawn); only the executive ministries stand outside",
        )
    return _kept(locals(), ())


def _seg_0106_010__cap_school(*, M: Any = _UNBOUND, cap_mins: Any = _UNBOUND, mh: Any = _UNBOUND, mi: Any = _UNBOUND, scale: Any = _UNBOUND, wd: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.010 (cap_school, mh, mi, wd) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        cap_school = [mi for mi in cap_mins if any(wd in (mi.get("name") or "").lower() for wd in ("school", "hanko"))] + [
            mh for mh in M.get("martial_halls", []) if mh.get("kind") == "hanko" or any(wd in (mh.get("label") or "").lower() for wd in ("school", "hanko"))
        ]
    return _kept(locals(), ('cap_school', 'mh', 'mi', 'wd'))


def _seg_0106_011__capital_has_domain_school(*, cap_school: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.011 (capital_has_domain_school) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        check(
            "capital_has_domain_school",
            len(cap_school) == 1,
            f"{len(cap_school)} domain school record(s), expected exactly 1 - the hanko is why samurai families across the domain send their children here (s.hanko)",
        )
    return _kept(locals(), ())


def _seg_0106_012__ring_road_kept_clear(*, M: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.012 (ring_road_kept_clear) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        check_ring_road_clear(M, check)  # the capital's patrol road is as real as a city's (GM 2026-08-09)
    return _kept(locals(), ())


# The approach avenue: the way that leaves the castle's front gate. Membership questions
# below are judged center-to-line with tolerances that dwarf the footprints - the
# ASSOCIATION/reach family (CLAUDE.md, "Centers, footprints, and aggregates").


def _seg_0106_013__cap_ways(*, M: Any = _UNBOUND, r: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.013 (cap_ways, r) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        cap_ways = ([(M["road"], M.get("road_width") or 26.0)] if M.get("road") else []) + [(r["pts"], r.get("w", 26.0)) for r in M.get("roads", [])]
    return _kept(locals(), ('cap_ways', 'r'))


def _seg_0106_014__cap_avenue(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.014 (cap_avenue) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        cap_avenue = None
    return _kept(locals(), ('cap_avenue',))


def _seg_0106_015__cap_avenue_1(
    *, M: Any = _UNBOUND, cap_ways: Any = _UNBOUND, cca: Any = _UNBOUND, ccg: Any = _UNBOUND, cpts: Any = _UNBOUND, cwid: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0106.015 (cap_avenue, cca, ccg, cpts) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        for cca in M.get("castles", []):
            ccg = cca.get("gate")
            if not ccg:
                continue
            for cpts, cwid in cap_ways:
                if min(math.hypot(cpts[0][0] - ccg[0], cpts[0][1] - ccg[1]), math.hypot(cpts[-1][0] - ccg[0], cpts[-1][1] - ccg[1])) < 60:
                    cap_avenue = (cpts, cwid)
    return _kept(locals(), ('cap_avenue', 'cca', 'ccg', 'cpts', 'cwid'))


def _seg_0106_016__capital_castle_has_approach_avenue(*, cap_avenue: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.016 (capital_castle_has_approach_avenue) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        check(
            "capital_castle_has_approach_avenue",
            cap_avenue is not None,
            "no way starts at the castle's front gate - the ote-suji runs from the ote-mon to the through-road (the jokamachi rule: the main road passes the castle's FRONT, 'to indicate the glory of the ruler')",
        )
    return _kept(locals(), ())


def _seg_0106_017__capital_ministries_front_the_avenue(
    *,
    CAP_SIX: Any = _UNBOUND,
    cap_alen: Any = _UNBOUND,
    cap_apts: Any = _UNBOUND,
    cap_avenue: Any = _UNBOUND,
    cap_aw: Any = _UNBOUND,
    cap_ax: Any = _UNBOUND,
    cap_ay: Any = _UNBOUND,
    cap_bx: Any = _UNBOUND,
    cap_by: Any = _UNBOUND,
    cap_by_name: Any = _UNBOUND,
    cap_d: Any = _UNBOUND,
    cap_dl: Any = _UNBOUND,
    cap_far: Any = _UNBOUND,
    cap_missing: Any = _UNBOUND,
    cap_nm: Any = _UNBOUND,
    cap_off: Any = _UNBOUND,
    cap_school: Any = _UNBOUND,
    check: Any = _UNBOUND,
    i: Any = _UNBOUND,
    mi: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0106.017 (capital_ministries_front_the_avenue, capital_school_on_the_axis) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital' and cap_avenue is not None:
        cap_apts, cap_aw = cap_avenue
        if not cap_missing:
            cap_far = []
            for cap_nm in CAP_SIX:
                mi = cap_by_name[f"Ministry of {cap_nm}"]
                cap_d = min(seg_dist(mi["x"], mi["y"], cap_apts[i], cap_apts[i + 1]) for i in range(len(cap_apts) - 1))
                if cap_d > max(mi["w"], mi["h"]) / 2 + cap_aw / 2 + 45:
                    cap_far.append(f"Ministry of {cap_nm}")
            check(
                "capital_ministries_front_the_avenue",
                not cap_far,
                f"ministries not fronting the ote-suji: {cap_far} - all six flank the approach avenue (Beijing's corridor pattern); none sits off in the fabric",
            )
        if cap_school:
            (cap_ax, cap_ay), (cap_bx, cap_by) = cap_apts[0], cap_apts[-1]
            cap_alen = math.hypot(cap_bx - cap_ax, cap_by - cap_ay) or 1.0
            cap_off = []
            for mi in cap_school:
                cap_dl = abs((cap_bx - cap_ax) * (cap_ay - mi["y"]) - (cap_ax - mi["x"]) * (cap_by - cap_ay)) / cap_alen
                if cap_dl > max(mi["w"], mi["h"]) / 2 + cap_aw / 2 + 45:
                    cap_off.append(mi.get("name") or mi.get("label"))
            check(
                "capital_school_on_the_axis",
                not cap_off,
                f"off the government axis: {cap_off} - the domain school stands on the ote-suji's LINE, continuing the ward past the through-road",
            )
    return _kept(locals(), ('cap_alen', 'cap_apts', 'cap_aw', 'cap_ax', 'cap_ay', 'cap_bx', 'cap_by', 'cap_d', 'cap_dl', 'cap_far', 'cap_nm', 'cap_off', 'i', 'mi'))


# A government office stands in its own ground - the provincial rule restated at this
# tier, because the scale=="city" block does not run here and a capital has no governor's
# yamen. Same 14px standoff, same funerary exclusion (a clan crypt against a bureau is a
# real adjacency), same registry-driven victim list.


def _seg_0106_018__CAP_OFFICE_GAP(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.018 (CAP_OFFICE_GAP) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        CAP_OFFICE_GAP = 14
    return _kept(locals(), ('CAP_OFFICE_GAP',))


def _seg_0106_019__cap_others(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.019 (cap_others) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        cap_others = solid_structs(M, "religious", "merchant_estates", exclude=("cemeteries", "mausoleums", "cremation_grounds", "ossuaries"))
    return _kept(locals(), ('cap_others',))


def _seg_0106_020__cap_abut(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.020 (cap_abut) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        cap_abut = []  # type: ignore[var-annotated]
    return _kept(locals(), ('cap_abut',))


def _seg_0106_021__cap_abut_1(
    *,
    CAP_OFFICE_GAP: Any = _UNBOUND,
    cap_abut: Any = _UNBOUND,
    cap_gx: Any = _UNBOUND,
    cap_gy: Any = _UNBOUND,
    cap_mins: Any = _UNBOUND,
    cap_others: Any = _UNBOUND,
    cst: Any = _UNBOUND,
    mi: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0106.021 (cap_abut, cap_gx, cap_gy, cst) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        for mi in cap_mins:
            for cst in cap_others:
                if cst is mi or "w" not in cst or "h" not in cst or "x" not in cst:
                    continue
                cap_gx = max(0.0, (mi["x"] - mi["w"] / 2) - (cst["x"] + cst["w"] / 2), (cst["x"] - cst["w"] / 2) - (mi["x"] + mi["w"] / 2))
                cap_gy = max(0.0, (mi["y"] - mi["h"] / 2) - (cst["y"] + cst["h"] / 2), (cst["y"] - cst["h"] / 2) - (mi["y"] + mi["h"] / 2))
                if math.hypot(cap_gx, cap_gy) < CAP_OFFICE_GAP:
                    cap_abut.append(f"{mi.get('name') or 'a ministry'!r} abuts {(cst.get('name') or cst.get('label') or cst.get('kind') or 'a building')!r}")
    return _kept(locals(), ('cap_abut', 'cap_gx', 'cap_gy', 'cst', 'mi'))


def _seg_0106_022__capital_government_offices_dont_abut(*, CAP_OFFICE_GAP: Any = _UNBOUND, cap_abut: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.022 (capital_government_offices_dont_abut) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        check(
            "capital_government_offices_dont_abut",
            not cap_abut,
            f"government office(s) abutting another structure ({CAP_OFFICE_GAP}px standoff): {sorted(set(cap_abut))}",
        )
    return _kept(locals(), ())


# THE LINEAGE COMPOUNDS are what make a capital read as a SPECIFIC domain's seat: named
# walled yashiki whose size tracks how many of each lineage actually LIVE here - never the
# rank of its head (the kurogi rule: a full chancellor on a visibly smaller plot because
# his people are out in his province). The ruling lineage gets NO compound - its seat IS
# the castle. settlements/capitals.md, "Shiro Daika's lineage compounds".


def _seg_0106_023__cap_lin(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.023 (cap_lin) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        cap_lin = meta.get("lineages") or {}
    return _kept(locals(), ('cap_lin',))


def _seg_0106_024__cap_ruling(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.024 (cap_ruling) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        cap_ruling = meta.get("ruling_lineage")
    return _kept(locals(), ('cap_ruling',))


# The FR-015 ratchet again: without the declaration every lineage check below SKIPS while
# showing green, so the missing declaration is itself the failure.


def _seg_0106_025__capital_declares_lineages(*, cap_lin: Any = _UNBOUND, cap_ruling: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.025 (capital_declares_lineages) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        check(
            "capital_declares_lineages",
            bool(cap_lin) and bool(cap_ruling),
            "meta(lineages={name: band}, ruling_lineage=...) not declared - bands are 'grand'/'estate'/'house', tracking the chargen household weights; without it the lineage checks have nothing to verify",
        )
    return _kept(locals(), ())


def _seg_0106_026__capital_lineage_compounds_labeled(
    *,
    CAP_BAND_ORDER: Any = _UNBOUND,
    CAP_BAND_STEP: Any = _UNBOUND,
    M: Any = _UNBOUND,
    cap_areas: Any = _UNBOUND,
    cap_hi: Any = _UNBOUND,
    cap_lbad: Any = _UNBOUND,
    cap_lin: Any = _UNBOUND,
    cap_lm: Any = _UNBOUND,
    cap_lo: Any = _UNBOUND,
    cap_rec: Any = _UNBOUND,
    cap_recs: Any = _UNBOUND,
    cap_ruling: Any = _UNBOUND,
    cap_weak: Any = _UNBOUND,
    cband: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cln: Any = _UNBOUND,
    cmn: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0106.026 (capital_lineage_bands_visibly_distinct, capital_lineage_compounds_labeled, capital_ruling_lineage_seat_is_the_castle) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital' and cap_lin and cap_ruling:
        cap_lm: dict[str, list[Any]] = {}  # type: ignore[no-redef]
        for cmn in M.get("manors", []):
            if cmn.get("lineage"):
                cap_lm.setdefault(cmn["lineage"], []).append(cmn)
        cap_lbad = []
        for cln in cap_lin:
            if cln == cap_ruling:
                continue
            cap_recs = cap_lm.get(cln, [])
            if len(cap_recs) != 1:
                cap_lbad.append(f"{cln}: {len(cap_recs)} compound(s)")
            elif cln.lower() not in (cap_recs[0].get("label") or "").lower():
                cap_lbad.append(f"{cln}: compound unlabeled")
        check(
            "capital_lineage_compounds_labeled",
            not cap_lbad,
            f"lineage compounds missing or unlabeled: {cap_lbad} - every declared lineage but the ruling one holds exactly one NAMED walled yashiki",
        )
        check(
            "capital_ruling_lineage_seat_is_the_castle",
            cap_ruling not in cap_lm,
            f"the ruling {cap_ruling!r} lineage has its own compound - its seat IS the castle, and a separate yashiki double-counts it",
        )
        # Bands must be VISIBLY distinct, not merely numerically different (SC-002): each
        # band's smallest footprint stands a clear step above the next band's largest. 1.5x
        # in area is ~1.22x linear - the point where two walled boxes read as different SIZES
        # at a glance rather than as drawing variation.
        CAP_BAND_ORDER = ("grand", "estate", "house")
        CAP_BAND_STEP = 1.5
        cap_areas: dict[str, list[float]] = {}  # type: ignore[no-redef]
        for cln, cband in cap_lin.items():
            for cap_rec in cap_lm.get(cln, []):
                cap_areas.setdefault(cband, []).append(cap_rec["w"] * cap_rec["h"])
        cap_weak = []
        for cap_hi, cap_lo in zip(CAP_BAND_ORDER, CAP_BAND_ORDER[1:], strict=False):
            if cap_areas.get(cap_hi) and cap_areas.get(cap_lo) and min(cap_areas[cap_hi]) < CAP_BAND_STEP * max(cap_areas[cap_lo]):
                cap_weak.append(f"{cap_hi} (min {min(cap_areas[cap_hi]):.0f} px^2) vs {cap_lo} (max {max(cap_areas[cap_lo]):.0f} px^2)")
        check(
            "capital_lineage_bands_visibly_distinct",
            not cap_weak,
            f"adjacent size bands are not visibly distinct (want >= {CAP_BAND_STEP}x area steps): {cap_weak}",
        )
    return _kept(locals(), ('CAP_BAND_ORDER', 'CAP_BAND_STEP', 'cap_areas', 'cap_hi', 'cap_lbad', 'cap_lm', 'cap_lo', 'cap_rec', 'cap_recs', 'cap_weak', 'cband', 'cln', 'cmn'))


# A CITY ESTATE'S CAPTION LIVES INSIDE ITS WALLS (GM 2026-08-09): the court is blank by
# doctrine (its contents belong to the Mode A sheet), so the empty court is the label's
# ground - a caption hung outside sits where 021's fabric must flow. Judged on the
# recorded label box vs the compound footprint; a manor whose caption is recorded
# elsewhere on the sheet fires, a manor with no matching caption record is skipped
# (label() always records, so that never happens on a generated map).


def _seg_0106_027__cap_lbl_out(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.027 (cap_lbl_out) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        cap_lbl_out = []  # type: ignore[var-annotated]
    return _kept(locals(), ('cap_lbl_out',))


def _seg_0106_028__cap_L(*, M: Any = _UNBOUND, cap_L: Any = _UNBOUND, cap_lbl_out: Any = _UNBOUND, cmn2: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.028 (cap_L, cap_lbl_out, cmn2) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        for cmn2 in M.get("manors", []):
            if not cmn2.get("label"):
                continue
            for cap_L in M.get("labels", []):
                if (
                    len(cap_L) > 5
                    and cap_L[5] == cmn2["label"]
                    and not (
                        cmn2["x"] - cmn2["w"] / 2 - 1 <= cap_L[0]
                        and cap_L[2] <= cmn2["x"] + cmn2["w"] / 2 + 1
                        and cmn2["y"] - cmn2["h"] / 2 - 1 <= cap_L[1]
                        and cap_L[3] <= cmn2["y"] + cmn2["h"] / 2 + 1
                    )
                ):
                    cap_lbl_out.append(cmn2["label"])
    return _kept(locals(), ('cap_L', 'cap_lbl_out', 'cmn2'))


def _seg_0106_029__capital_estate_labels_inside(*, cap_lbl_out: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.029 (capital_estate_labels_inside) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        check(
            "capital_estate_labels_inside",
            not cap_lbl_out,
            f"estate caption(s) outside their own walls: {sorted(set(cap_lbl_out))[:4]} - a city estate's court is blank by doctrine, so the caption lives INSIDE it (manor(label_inside=True)), sized to clear the walls",
        )
    return _kept(locals(), ())


# A RIVER GETS A TOWPATH, NOT A ROAD (GM 2026-08-08; research/cities/capitals.md): water
# carried bulk far more cheaply than carts, so a trunk road shadowing a navigable river is
# redundant - a way may CROSS the river (bridged), never run along its bank. Judged
# centerline-to-centerline (ASSOCIATION family: the band dwarfs both widths, and the
# question is "does this way live on the bank", not a clearance).


def _seg_0106_030__cap_riv(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.030 (cap_riv) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        cap_riv = M.get("river")
    return _kept(locals(), ('cap_riv',))


def _seg_0106_031__capital_no_road_parallels_river(
    *,
    CAP_BANK: Any = _UNBOUND,
    CAP_RUN: Any = _UNBOUND,
    cap_best: Any = _UNBOUND,
    cap_dm: Any = _UNBOUND,
    cap_ex: Any = _UNBOUND,
    cap_ey: Any = _UNBOUND,
    cap_k: Any = _UNBOUND,
    cap_qx: Any = _UNBOUND,
    cap_qy: Any = _UNBOUND,
    cap_riv: Any = _UNBOUND,
    cap_rpts: Any = _UNBOUND,
    cap_run: Any = _UNBOUND,
    cap_shadow: Any = _UNBOUND,
    cap_slen: Any = _UNBOUND,
    cap_steps: Any = _UNBOUND,
    cap_sx: Any = _UNBOUND,
    cap_sy: Any = _UNBOUND,
    cap_t: Any = _UNBOUND,
    cap_ways: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cpts: Any = _UNBOUND,
    i: Any = _UNBOUND,
    j: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0106.031 (capital_no_road_parallels_river) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital' and isinstance(cap_riv, dict) and (cap_riv.get("pts") or cap_riv.get("poly")):
        cap_rpts = cap_riv.get("pts") or cap_riv["poly"]
        CAP_BANK = cap_riv.get("w", 40) / 2 + 45  # inside this band a way is ON the bank
        CAP_RUN = 280  # px of contiguous bank-riding; a perpendicular (bridged) crossing stays in-band far less
        cap_shadow = []
        for cpts, _cwid in cap_ways:
            cap_best = cap_run = 0.0
            for i in range(len(cpts) - 1):
                cap_sx, cap_sy = cpts[i]
                cap_ex, cap_ey = cpts[i + 1]
                cap_slen = math.hypot(cap_ex - cap_sx, cap_ey - cap_sy)
                cap_steps = max(1, int(cap_slen / 20))
                for cap_k in range(cap_steps):
                    cap_t = (cap_k + 0.5) / cap_steps
                    cap_qx, cap_qy = cap_sx + (cap_ex - cap_sx) * cap_t, cap_sy + (cap_ey - cap_sy) * cap_t
                    cap_dm = min(seg_dist(cap_qx, cap_qy, cap_rpts[j], cap_rpts[j + 1]) for j in range(len(cap_rpts) - 1))
                    if cap_dm < CAP_BANK:
                        cap_run += cap_slen / cap_steps
                        cap_best = max(cap_best, cap_run)
                    else:
                        cap_run = 0.0
            if cap_best > CAP_RUN:
                cap_shadow.append(f"a way rides the bank for {cap_best:.0f}px")
        check(
            "capital_no_road_parallels_river",
            not cap_shadow,
            f"{cap_shadow} - no trunk road parallels a navigable river; the bank carries a towpath (s.towpath), and the roads leave in the directions the water does not serve",
        )
    return _kept(
        locals(),
        (
            'CAP_BANK',
            'CAP_RUN',
            '_cwid',
            'cap_best',
            'cap_dm',
            'cap_ex',
            'cap_ey',
            'cap_k',
            'cap_qx',
            'cap_qy',
            'cap_rpts',
            'cap_run',
            'cap_shadow',
            'cap_slen',
            'cap_steps',
            'cap_sx',
            'cap_sy',
            'cap_t',
            'cpts',
            'i',
            'j',
        ),
    )


# THE AQUEDUCT (GM 2026-08-08): a capital outgrows what wells alone can supply, so it
# carries a supply channel - open OUTSIDE the wall, buried inside, the GATE as the
# boundary (Edo's josui, Odawara's sosui; research/cities/capitals.md).


def _seg_0106_032__cap_aqs(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.032 (cap_aqs) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        cap_aqs = M.get("aqueducts", [])
    return _kept(locals(), ('cap_aqs',))


def _seg_0106_033__capital_has_aqueduct(*, cap_aqs: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.033 (capital_has_aqueduct) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        check(
            "capital_has_aqueduct",
            bool(cap_aqs),
            "no aqueduct - draw s.aqueduct(...) from a river intake to a city gate; the wells stay (the conduit supplements them, it does not replace them)",
        )
    return _kept(locals(), ())


def _seg_0106_034__cap_gates(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0106.034 (cap_gates) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        cap_gates = M.get("gates") or []
    return _kept(locals(), ('cap_gates',))


def _seg_0106_035__capital_aqueduct_terminates_at_a_gate(
    *,
    M: Any = _UNBOUND,
    cap_ain: Any = _UNBOUND,
    cap_apoly: Any = _UNBOUND,
    cap_aq: Any = _UNBOUND,
    cap_aqs: Any = _UNBOUND,
    cap_gates: Any = _UNBOUND,
    cap_tx: Any = _UNBOUND,
    cap_ty: Any = _UNBOUND,
    cap_wallp: Any = _UNBOUND,
    cgx: Any = _UNBOUND,
    cgy: Any = _UNBOUND,
    check: Any = _UNBOUND,
    p: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0106.035 (capital_aqueduct_stays_outside_the_wall, capital_aqueduct_terminates_at_a_gate) - body verbatim from _seg_0106__capital_declares_a_budget (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'capital':
        for cap_aq in cap_aqs:
            cap_apoly = cap_aq.get("poly") or []
            if not cap_apoly:
                continue
            cap_tx, cap_ty = cap_apoly[-1]
            check(
                "capital_aqueduct_terminates_at_a_gate",
                any(math.hypot(cgx - cap_tx, cgy - cap_ty) < 90 for cgx, cgy in cap_gates),
                f"aqueduct terminus ({cap_tx:.0f},{cap_ty:.0f}) is at no city gate - the gate is the open/buried boundary; past it the conduit is buried and only its draw-basins show",
            )
            cap_wallp = M.get("wall") or []
            cap_ain = [p for p in cap_apoly if len(cap_wallp) >= 3 and point_in_poly(p[0], p[1], cap_wallp)]
            check(
                "capital_aqueduct_stays_outside_the_wall",
                not cap_ain,
                f"aqueduct has {len(cap_ain)} vertex/vertices inside the wall - no open watercourse threads the walled interior (inside, the conduit is honestly buried; its draw-basins are the visible part)",
            )
    return _kept(locals(), ('cap_ain', 'cap_apoly', 'cap_aq', 'cap_tx', 'cap_ty', 'cap_wallp', 'cgx', 'cgy', 'p'))


# DOORS OPEN OUTWARD; ROWS STACK AT MOST TWO DEEP (GM, 2026-07-18). An urban building's door
# glyph sits on its local +h/2 side (rotated by `rot` - settlement.building), so the door's
# world direction derives from the manifest alone. A door must open onto WALKABLE ground
# (street, roji, court, open space) - never into the back of another house an eave-gap away.
# FARMHOUSES ARE EXEMPT EVERYWHERE: a farmhouse always faces SOUTH (its garden and threshing
# ground need the sunlight - the orientation is canon); a city house has no sun constraint,
# so it must face open ground instead. The pair rule follows from the same fact: contiguous
# rows stack at most TWO deep (back-to-back, both fronts outward), because the middle row of
# a 3-stack has walls hard against BOTH long faces - those households would be trapped.
# Separations in real feet: an eave/drainage gap is ~3-6 ft (drainage, not an entrance), a
# walkable roji/court is >= ~10 ft; DOOR_CLEAR_FT = 7 sits cleanly between them at every
# map scale (ftpx converts to drawn px).


def _seg_0107__city_house_doors_unblocked(
    *,
    M: Any = _UNBOUND,
    _face_blocked: Any = _UNBOUND,
    b: Any = _UNBOUND,
    bad_doors: Any = _UNBOUND,
    bcorn: Any = _UNBOUND,
    bdiag: Any = _UNBOUND,
    blockers: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d: Any = _UNBOUND,
    door_clear: Any = _UNBOUND,
    fx: Any = _UNBOUND,
    fy: Any = _UNBOUND,
    h: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    o: Any = _UNBOUND,
    oc: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    sgn: Any = _UNBOUND,
    subj: Any = _UNBOUND,
    t: Any = _UNBOUND,
    th: Any = _UNBOUND,
    trapped: Any = _UNBOUND,
    ux: Any = _UNBOUND,
    uy: Any = _UNBOUND,
    vx: Any = _UNBOUND,
    vy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 107 (city_house_doors_unblocked, city_rows_max_two_deep) - body verbatim from the legacy gate() (feature 022)."""
    if scale in ("town", "city", "capital"):
        door_clear = DOOR_CLEAR_FT / meta.get("ftpx", 1)
        subj = [b for b in M.get("buildings", []) if "w" in b]
        blockers = subj + [h for h in M.get("houses", []) if "w" in h]
        bcorn = [rect_corners(_struct_rect(b)) for b in blockers]
        # PREFILTER RADII, not a verdict (family: prefilter - see edge_gap). The circumscribed
        # radius is the right tool here precisely because it over-states an extent: over-stating can
        # only admit a candidate the exact `point_in_poly` below then rejects, so the index prunes
        # and never decides. Do NOT "fix" these to true extents - that would start rejecting pairs
        # before the exact test sees them.
        bdiag = [math.hypot(b["w"], b["h"]) / 2 for b in blockers]

        def _face_blocked(b: dict[str, Any], sgn: float) -> bool:
            th = math.radians(b.get("rot", 0))
            ux, uy = -math.sin(th) * sgn, math.cos(th) * sgn  # outward normal of the (sgn=+1) door face
            vx, vy = -uy, ux  # lateral, along the face
            fx, fy = b["x"] + ux * b["h"] / 2, b["y"] + uy * b["h"] / 2  # face center
            rr = math.hypot(b["w"], b["h"]) / 2 + door_clear + 1
            for o, oc, od in zip(blockers, bcorn, bdiag, strict=True):
                if o is b or math.hypot(o["x"] - b["x"], o["y"] - b["y"]) > rr + od:
                    continue
                for d in (0.8, door_clear * 0.55, door_clear):
                    for t in (-0.3 * b["w"], 0.0, 0.3 * b["w"]):
                        if point_in_poly(fx + ux * d + vx * t, fy + uy * d + vy * t, oc):
                            return True
            return False

        bad_doors = [b for b in subj if _face_blocked(b, 1.0)]
        check(
            "city_house_doors_unblocked",
            not bad_doors,
            f"{len(bad_doors)} building(s) whose DOOR opens into another structure within ~{DOOR_CLEAR_FT:.0f} real ft "
            f"(an eave gap, not an entrance): {[(round(b['x']), round(b['y']), b.get('kind')) for b in bad_doors[:5]]} - a city house faces "
            f"open ground (street/roji/court); in a back-to-back pair both doors face OUTWARD (rot the row 180), never into a neighbor's back wall",
        )
        trapped = [b for b in subj if _face_blocked(b, 1.0) and _face_blocked(b, -1.0)]
        check(
            "city_rows_max_two_deep",
            not trapped,
            f"{len(trapped)} building(s) walled on BOTH long faces - the trapped middle of a 3-deep row stack: "
            f"{[(round(b['x']), round(b['y']), b.get('kind')) for b in trapped[:5]]} - rows/columns stack at most TWO deep (back-to-back); "
            f"after every pair leave a walkable roji/court (>= ~10 real ft), so every household fronts open ground",
        )
    return _kept(locals(), ('_face_blocked', 'b', 'bad_doors', 'bcorn', 'bdiag', 'blockers', 'door_clear', 'h', 'subj', 'trapped'))


# A MERCHANT ESTATE'S WALL STANDS ON DRY, PRIVATE GROUND (GM, 2026-07-19). The walled
# compound of a very-rich urban merchant must not run its perimeter wall through WATER
# (a wall footed in a canal/dock basin is undermined, and the working quay/towpath must
# stay open to the boats and porters that make the merchant rich) or through a FIRE TOWER
# (the fire watch is municipal - it needs its own footing, daylight around the frame, and
# access for the watch; it cannot be embedded in a private compound wall). The whole
# perimeter is walked, gate gap included - a courtyard gate opening straight onto water
# or into the tower frame is the same siting error.


def _seg_0108__merchant_estate_wall_clear_of_water(
    *,
    M: Any = _UNBOUND,
    WMARG: Any = _UNBOUND,
    _in_grown_rect: Any = _UNBOUND,
    _near_line: Any = _UNBOUND,
    _tower_conflict: Any = _UNBOUND,
    _wall_hits: Any = _UNBOUND,
    _wall_pts: Any = _UNBOUND,
    al: Any = _UNBOUND,
    cc: Any = _UNBOUND,
    check: Any = _UNBOUND,
    dk: Any = _UNBOUND,
    e: Any = _UNBOUND,
    est: Any = _UNBOUND,
    est_ftowers: Any = _UNBOUND,
    est_on_st: Any = _UNBOUND,
    est_streets: Any = _UNBOUND,
    est_waters: Any = _UNBOUND,
    est_wet: Any = _UNBOUND,
    ew: Any = _UNBOUND,
    fn: Any = _UNBOUND,
    gc: Any = _UNBOUND,
    hw: Any = _UNBOUND,
    it: Any = _UNBOUND,
    k: Any = _UNBOUND,
    name: Any = _UNBOUND,
    pcx: Any = _UNBOUND,
    pcy: Any = _UNBOUND,
    prx: Any = _UNBOUND,
    pry: Any = _UNBOUND,
    pts: Any = _UNBOUND,
    px_: Any = _UNBOUND,
    py_: Any = _UNBOUND,
    rd: Any = _UNBOUND,
    rv: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    si: Any = _UNBOUND,
    st: Any = _UNBOUND,
    steps: Any = _UNBOUND,
    t: Any = _UNBOUND,
    towered: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 108 (merchant_estate_wall_clear_of_fire_towers, merchant_estate_wall_clear_of_streets, merchant_estate_wall_clear_of_water) - body verbatim from the legacy gate() (feature 022)."""
    if scale in ("town", "city") and M.get("merchant_estates"):
        WMARG = 1.5  # px of daylight demanded beyond the drawn footprints/line widths

        def _near_line(pts: Any, hw: float) -> Any:
            return lambda px_, py_: any(seg_dist(px_, py_, pts[k], pts[k + 1]) < hw for k in range(len(pts) - 1))

        def _in_grown_rect(it: dict[str, Any]) -> Any:
            gc = rect_corners(_struct_rect({**it, "w": it["w"] + 2 * WMARG, "h": it["h"] + 2 * WMARG}))
            return lambda px_, py_: point_in_poly(px_, py_, gc)

        est_waters: list[tuple[str, Any]] = [("canal", _near_line(cc["poly"], cc.get("w", 12) / 2 + WMARG)) for cc in M.get("canals", [])]  # type: ignore[no-redef]
        if M.get("moat"):
            est_waters.append(("moat", _near_line(M["moat"], M.get("moat_width", 22) / 2 + WMARG)))
        rv = M.get("river")
        if rv:
            est_waters.append(("river", _near_line(rv["pts"], rv.get("w", 40) / 2 + WMARG)))
        est_waters += [("dock", _in_grown_rect(dk)) for dk in M.get("docks", [])]
        if M.get("pond"):
            pcx, pcy, prx, pry = M["pond"]
            est_waters.append(("pond", lambda px_, py_: ((px_ - pcx) / (prx + WMARG)) ** 2 + ((py_ - pcy) / (pry + WMARG)) ** 2 <= 1))
        est_ftowers: list[tuple[str, Any]] = [("fire tower", _in_grown_rect(t)) for t in M.get("fire_towers", []) if "w" in t]  # type: ignore[no-redef]

        def _wall_pts(est: dict[str, Any]) -> list[tuple[float, float]]:
            ex0, ey0, ex1, ey1 = est["x"] - est["w"] / 2, est["y"] - est["h"] / 2, est["x"] + est["w"] / 2, est["y"] + est["h"] / 2
            pts = []
            for p0, p1 in [((ex0, ey0), (ex1, ey0)), ((ex1, ey0), (ex1, ey1)), ((ex1, ey1), (ex0, ey1)), ((ex0, ey1), (ex0, ey0))]:
                steps = max(2, int(math.hypot(p1[0] - p0[0], p1[1] - p0[1]) / 3))
                pts += [(p0[0] + (p1[0] - p0[0]) * si / steps, p0[1] + (p1[1] - p0[1]) * si / steps) for si in range(steps + 1)]
            return pts

        def _wall_hits(est: dict[str, Any], targets: list[tuple[str, Any]]) -> list[str]:
            pts = _wall_pts(est)
            return [name for name, fn in targets if any(fn(px_, py_) for px_, py_ in pts)]

        est_wet = [(round(e["x"]), round(e["y"]), _wall_hits(e, est_waters)) for e in M["merchant_estates"]]
        est_wet = [ew for ew in est_wet if ew[2]]
        check(
            "merchant_estate_wall_clear_of_water",
            not est_wet,
            f"merchant-estate wall(s) running through open water: {est_wet} - a compound wall stands on dry ground; "
            f"the canal/dock/moat/pond edge is working waterfront (boats, porters, the towpath), not private wall footing - move the estate clear",
        )

        # a tower ENCLOSED in the private court (wall-line clear, tower trapped inside) is the
        # same siting error as a wall through it - the watch must reach its tower from public ground
        def _tower_conflict(e: dict[str, Any]) -> bool:
            if _wall_hits(e, est_ftowers):
                return True
            return any(abs(t["x"] - e["x"]) < e["w"] / 2 and abs(t["y"] - e["y"]) < e["h"] / 2 for t in M.get("fire_towers", []) if "w" in t)

        towered = [(round(e["x"]), round(e["y"])) for e in M["merchant_estates"] if _tower_conflict(e)]
        check(
            "merchant_estate_wall_clear_of_fire_towers",
            not towered,
            f"merchant-estate wall(s) running through - or enclosing - a fire tower: {towered} - the fire watch is municipal; the tower needs its own "
            f"footing, daylight around the braced frame, and watch access from public ground - it cannot be embedded in (or walled inside) a private compound; move the estate or the tower",
        )

        # THE SAME WALLS STAY OFF THE STREETS (GM follow-up, 2026-07-19): a compound wall
        # standing in a street bed blocks the public way - the wall may LINE a street (that is
        # what a walled compound on a block looks like) but never stand IN its cleared band.
        est_streets: list[tuple[str, Any]] = [("street", _near_line(st["pts"], st.get("w", 12) / 2 + WMARG)) for st in M.get("town_streets", [])]  # type: ignore[no-redef]
        est_streets += [("alley", _near_line(al["pts"], al.get("w", 8) / 2 + WMARG)) for al in M.get("alleys", [])]
        est_streets += [("road", _near_line(rd["pts"], rd["w"] / 2 + WMARG)) for rd in M.get("roads", [])]
        if M.get("road"):
            est_streets.append(("road", _near_line(M["road"], M.get("road_width", 26) / 2 + WMARG)))
        if M.get("ring_road"):
            est_streets.append(("ring road", _near_line(M["ring_road"], M.get("ring_road_width", 7) / 2 + WMARG)))
        est_on_st = [(round(e["x"]), round(e["y"]), _wall_hits(e, est_streets)) for e in M["merchant_estates"]]
        est_on_st = [ew for ew in est_on_st if ew[2]]
        check(
            "merchant_estate_wall_clear_of_streets",
            not est_on_st,
            f"merchant-estate wall(s) standing IN a street/alley/road bed: {est_on_st} - the public way stays open; "
            f"a compound wall may line a street but never stand in its cleared band - move the estate off the street",
        )
    return _kept(
        locals(),
        (
            'WMARG',
            '_in_grown_rect',
            '_near_line',
            '_tower_conflict',
            '_wall_hits',
            '_wall_pts',
            'al',
            'cc',
            'dk',
            'e',
            'est_ftowers',
            'est_on_st',
            'est_streets',
            'est_waters',
            'est_wet',
            'ew',
            'pcx',
            'pcy',
            'prx',
            'pry',
            'pts',
            'rd',
            'rv',
            'st',
            't',
            'towered',
        ),
    )


# COMPOUND GATES AND WALLS TO SCALE (GM, 2026-07-19). The walled compounds (samurai country
# estates/manors, the governor's yamen, merchant estates, the mausoleum) draw only walls +
# gate + a deliberately BLANK court (the interior is its own Mode A diagram) - so the wall
# and gate ARE the feature, and they must be honest: a samurai residence gate (nagayamon /
# yakuimon) opens ~9-12 real ft (cart + palanquin), a grand yamen gatehouse up to ~24 ft;
# the old fixed-pixel gap (+-34px) drew a 204 ft opening at city scale - most of a wall
# missing. Walls (dobei/tsuijibei) run ~1.5-2 ft thick, drawn true-width-or-floored (the
# 2px cartographic floor = 6 ft at city scale; band top 8 allows it). A manifest that
# records no gate_w predates the to-scale engine and cannot prove its gates - regenerate.


def _seg_0109___gcomp(*, M: Any = _UNBOUND, me: Any = _UNBOUND, mn: Any = _UNBOUND, mu: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 109 (_gcomp, me, mn, mu) - body verbatim from the legacy gate() (feature 022)."""
    _gcomp = [("manor", mn) for mn in M.get("manors", [])] + [("merchant estate", me) for me in M.get("merchant_estates", [])] + [("mausoleum", mu) for mu in M.get("mausoleums", [])]
    return _kept(locals(), ('_gcomp', 'me', 'mn', 'mu'))


def _seg_0110___gcomp_1(*, M: Any = _UNBOUND, _gcomp: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 110 (_gcomp) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("governor_mansion"):
        _gcomp.append(("governor's mansion", M["governor_mansion"]))
    return _kept(locals(), ('_gcomp',))


def _seg_0111__compound_gates_to_scale(
    *,
    _gcomp: Any = _UNBOUND,
    _gftpx: Any = _UNBOUND,
    check: Any = _UNBOUND,
    gc: Any = _UNBOUND,
    gcomp_bad: Any = _UNBOUND,
    gft: Any = _UNBOUND,
    gkind: Any = _UNBOUND,
    gw: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    side: Any = _UNBOUND,
    wallft: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 111 (compound_gates_to_scale) - body verbatim from the legacy gate() (feature 022)."""
    if _gcomp:
        _gftpx = meta.get("ftpx", 1)
        gcomp_bad = []
        for gkind, gc in _gcomp:
            gw = gc.get("gate_w")
            if gw is None:
                gcomp_bad.append((gkind, round(gc["x"]), round(gc["y"]), "gate unrecorded - regenerate with the to-scale engine"))
                continue
            gft = gw * _gftpx
            side = gc["w"] if gc.get("gate_dir", "south") in ("north", "south") else gc["h"]
            wallft = gc.get("wall_w", 0) * _gftpx
            if not GATE_FT_MIN <= gft <= GATE_FT_MAX:
                gcomp_bad.append((gkind, round(gc["x"]), round(gc["y"]), f"gate opening {gft:.0f} ft outside [{GATE_FT_MIN:.0f},{GATE_FT_MAX:.0f}]"))
            elif gw > 0.4 * side:
                gcomp_bad.append((gkind, round(gc["x"]), round(gc["y"]), f"gate is {gw / side:.0%} of its wall side - reads as a missing wall, not a gate"))
            elif not WALL_FT_MIN <= wallft <= WALL_FT_MAX:
                gcomp_bad.append((gkind, round(gc["x"]), round(gc["y"]), f"wall drawn {wallft:.0f} ft thick, outside [{WALL_FT_MIN:.0f},{WALL_FT_MAX:.0f}]"))
        check(
            "compound_gates_to_scale",
            not gcomp_bad,
            f"walled compound(s) with out-of-scale gates/walls: {gcomp_bad[:4]} - a residence gate opens ~9-12 real ft (a grand "
            f"yamen gatehouse up to ~24), walls run ~2 ft thick (2px cartographic floor); the blank court is deliberate (the interior is its own diagram) so the wall+gate must carry the realism",
        )
    return _kept(locals(), ('_gftpx', 'gc', 'gcomp_bad', 'gft', 'gkind', 'gw', 'side', 'wallft'))


# FUNERARY FEATURES TO SCALE (GM, 2026-07-19; anchors in settlements.md "Historical
# grounding"). The old glyphs were FIXED-PIXEL and silently tripled at city scale.


def _seg_0112___fftpx(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 112 (_fftpx) - body verbatim from the legacy gate() (feature 022)."""
    _fftpx = meta.get("ftpx", 1)
    return _kept(locals(), ('_fftpx',))


def _seg_0113__crem_bad() -> dict[str, Any]:
    """Gate segment 113 (crem_bad) - body verbatim from the legacy gate() (feature 022)."""
    crem_bad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('crem_bad',))


def _seg_0114__cg(
    *, M: Any = _UNBOUND, _fftpx: Any = _UNBOUND, cg: Any = _UNBOUND, crem_bad: Any = _UNBOUND, crem_cap: Any = _UNBOUND, long_ft: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 114 (cg, crem_bad, crem_cap, long_ft) - body verbatim from the legacy gate() (feature 022)."""
    for cg in M.get("cremation_grounds", []):
        long_ft = max(cg["w"], cg["h"]) * _fftpx
        crem_cap = CREMATION_FT_MAX_CITY if scale in ("city", "capital") else CREMATION_FT_MAX_TOWN  # a capital cremates a city's dead (GM 2026-08-10)
        if not CREMATION_FT_MIN <= long_ft <= crem_cap:
            crem_bad.append((round(cg["x"]), round(cg["y"]), f"{long_ft:.0f} ft across vs [{CREMATION_FT_MIN:.0f},{crem_cap:.0f}]"))
    return _kept(locals(), ('cg', 'crem_bad', 'crem_cap', 'long_ft'))


def _seg_0115__cremation_ground_to_scale(*, M: Any = _UNBOUND, check: Any = _UNBOUND, crem_bad: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 115 (cremation_ground_to_scale) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("cremation_grounds"):
        check(
            "cremation_ground_to_scale",
            not crem_bad,
            f"cremation ground(s) out of scale: {crem_bad} - a sanmai's working core (7 ft hearth, shelter, bone platform, mourner ground) "
            f"clears 30-80 ft for a village/town and ~80-160 ft for a provincial city; even the crematory serving metropolitan Edo was ~180 ft square",
        )
    return _kept(locals(), ())


def _seg_0116__o(*, M: Any = _UNBOUND, _fftpx: Any = _UNBOUND, o: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 116 (o, oss_bad) - body verbatim from the legacy gate() (feature 022)."""
    oss_bad = [(round(o["x"]), round(o["y"]), f"{max(o['w'], o['h']) * _fftpx:.0f} ft") for o in M.get("ossuaries", []) if not OSSUARY_FT_MIN <= max(o["w"], o["h"]) * _fftpx <= OSSUARY_FT_MAX]
    return _kept(locals(), ('o', 'oss_bad'))


def _seg_0117__ossuary_to_scale(*, M: Any = _UNBOUND, check: Any = _UNBOUND, oss_bad: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 117 (ossuary_to_scale) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("ossuaries"):
        check(
            "ossuary_to_scale",
            not oss_bad,
            f"pauper ossuary mound(s) out of scale: {oss_bad} (band [{OSSUARY_FT_MIN:.0f},{OSSUARY_FT_MAX:.0f}] ft) - a muenzuka is a 10-30 ft mound "
            f"(cremated bone takes almost no volume; even Kyoto's monumental state-built Mimizuka is ~50 ft at the base); the band top allows the small-glyph legibility floor",
        )
    return _kept(locals(), ())


def _seg_0118__burial_grounds_sized_to_population(
    *, M: Any = _UNBOUND, _fftpx: Any = _UNBOUND, c: Any = _UNBOUND, check: Any = _UNBOUND, hi: Any = _UNBOUND, lo: Any = _UNBOUND, scale: Any = _UNBOUND, total_ac: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 118 (burial_grounds_sized_to_population) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("cemeteries") and scale in ("village", "town", "city"):
        total_ac = sum(c["w"] * c["h"] for c in M["cemeteries"]) * _fftpx * _fftpx / 43_560
        lo, hi = BURIAL_AC_BAND[scale]
        check(
            "burial_grounds_sized_to_population",
            lo <= total_ac <= hi,
            f"total burial ground {total_ac:.2f} acres vs the {scale} band [{lo},{hi}] - size the grounds to the population SERVED "
            f"(cremation-then-inter culture, ~1 generation of active plots before reuse: village ~0.15-0.30 ac for the ~800-person DISTRICT it buries - "
            f"hamlets carry their urns here and draw no ground; town ~0.25-0.75, city ~0.75-2 split across yards); "
            f"the ladder must read MONOTONE with population served - a village ground must never dwarf a town's",
        )
    return _kept(locals(), ('c', 'hi', 'lo', 'total_ac'))


# FARMSTEADS ARE WITHIN REACH OF A WELL (town/city): the farm belt drinks daily too, and
# Rokugan's unusually well-run domains sink wells liberally (the same liberty behind the
# literal urban idobata count) - so no farmhouse stands more than 500 REAL FEET from a
# well (a ~2-minute bucket walk; a real farmstead would often have its own). Farmhouses
# within 150 real ft of the VIEW edge are exempt: their fields already run off-map, and
# their well is presumed just off the edge with the rest of their steading (GM rule,
# 2026-07-21). Villages are not gated here - their wells already sit among the houses
# (wells_among_dwellings). WHY: settlements.md wells entry.


def _seg_0119__farm_wells_within_reach(
    *,
    M: Any = _UNBOUND,
    _fw_edge: Any = _UNBOUND,
    _fw_far: Any = _UNBOUND,
    _fw_ftpx: Any = _UNBOUND,
    _fw_h: Any = _UNBOUND,
    _fw_reach: Any = _UNBOUND,
    _fw_view: Any = _UNBOUND,
    _fw_w: Any = _UNBOUND,
    check: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 119 (farm_wells_within_reach) - body verbatim from the legacy gate() (feature 022)."""
    if scale in ("town", "city") and M.get("houses"):
        _fw_ftpx = float(meta.get("ftpx", 1) or 1)
        _fw_reach = 500.0 / _fw_ftpx
        _fw_edge = 150.0 / _fw_ftpx
        _fw_view = meta.get("view") or [0, 0, meta.get("W", 10**9), meta.get("H", 10**9)]
        _fw_far = []
        for _fw_h in M["houses"]:
            if min(_fw_h["x"] - _fw_view[0], _fw_h["y"] - _fw_view[1], _fw_view[0] + _fw_view[2] - _fw_h["x"], _fw_view[1] + _fw_view[3] - _fw_h["y"]) < _fw_edge:
                continue
            if not any((_fw_h["x"] - _fw_w["x"]) ** 2 + (_fw_h["y"] - _fw_w["y"]) ** 2 <= _fw_reach**2 for _fw_w in M.get("wells", [])):
                _fw_far.append((round(_fw_h["x"]), round(_fw_h["y"])))
        check(
            "farm_wells_within_reach",
            not _fw_far,
            f"{len(_fw_far)} farmhouse(s) further than 500 real ft from any well {_fw_far[:5]} - the farm belt "
            f"drinks daily too; call s.farm_wells() after s.farmsteads() (map-edge farmsteads are exempt - their "
            f"well is presumed just off the edge)",
        )
    return _kept(locals(), ('_fw_edge', '_fw_far', '_fw_ftpx', '_fw_h', '_fw_reach', '_fw_view', '_fw_w'))


# DRY-CROP PLOTS ARE TO SCALE: a hem parcel is a smallholder's strip (~1 mu / ~0.17 acre
# mean in Buck's surveys - the same grain the paddy plots and the polder parcels obey), so
# the map-wide MEAN dry-plot area must stay under 0.25 real acres. The tiling constants in
# _dry_fields (plot width 46px, row depth 36px) are real-feet quantities tuned at 2 ft/px:
# unscaled at the 3 ft/px city grain they doubled every parcel's area (0.34-0.38 acre
# means), dry cells visibly dwarfing the ~78 ft rice plots beside them - "set a number of
# pixels, not a number of feet" (the GM's exact catch, 2026-07-21). WHY: settlements.md.


def _seg_0120___ds_dps(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 120 (_ds_dps) - body verbatim from the legacy gate() (feature 022)."""
    _ds_dps = M.get("dry_plots", [])
    return _kept(locals(), ('_ds_dps',))


def _seg_0121__dry_plots_to_scale(
    *,
    _ds_a: Any = _UNBOUND,
    _ds_areas: Any = _UNBOUND,
    _ds_d: Any = _UNBOUND,
    _ds_dps: Any = _UNBOUND,
    _ds_ftpx: Any = _UNBOUND,
    _ds_max: Any = _UNBOUND,
    _ds_mean: Any = _UNBOUND,
    _ds_p: Any = _UNBOUND,
    _vs_a: Any = _UNBOUND,
    _vs_big: Any = _UNBOUND,
    _vs_d: Any = _UNBOUND,
    _vs_p: Any = _UNBOUND,
    _vs_veg: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d: Any = _UNBOUND,
    i: Any = _UNBOUND,
    meta: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 121 (dry_plots_to_scale, vegetable_beds_are_intensive) - body verbatim from the legacy gate() (feature 022)."""
    if _ds_dps:
        _ds_ftpx = float(meta.get("ftpx", 1) or 1)
        _ds_areas = []
        for _ds_d in _ds_dps:
            _ds_p = _ds_d["poly"]
            _ds_a = abs(sum(_ds_p[i][0] * _ds_p[(i + 1) % len(_ds_p)][1] - _ds_p[(i + 1) % len(_ds_p)][0] * _ds_p[i][1] for i in range(len(_ds_p)))) / 2
            _ds_areas.append(_ds_a * _ds_ftpx * _ds_ftpx / 43560)
        _ds_mean = sum(_ds_areas) / len(_ds_areas)
        # the MEAN alone let a small oversized subpopulation hide behind many right-sized hem
        # parcels (Tango's vegetable tract at 0.3-0.5 acre diluted to a passing mean by ~70
        # hem plots, 2026-07-21) - so the largest single parcel is capped too: pool-wide the
        # honest maximum is ~0.30 acre (biggest hem parcel), villages max ~0.26
        _ds_max = max(_ds_areas)
        # a garden VEGETABLE bed (daikon/greens/onions/beans - VEG_CROPS, in-wall intensive
        # tracts) is hand-worked ground, distinctly SMALLER than a grain-field hem strip: cap
        # each such plot at 0.15 real acres (fixed beds ~0.10; the pre-fix uneven column split
        # left 0.24-acre veg slabs, the biggest dry parcels on the map - backwards for a kitchen
        # garden; GM 2026-07-22). Only fires where veg crops exist (cities with a veg tract).
        _vs_veg = [d for d in _ds_dps if d.get("crop") in {"daikon", "greens", "onions", "beans"}]
        if _vs_veg:
            _vs_big = []
            for _vs_d in _vs_veg:
                _vs_p = _vs_d["poly"]
                _vs_a = abs(sum(_vs_p[i][0] * _vs_p[(i + 1) % len(_vs_p)][1] - _vs_p[(i + 1) % len(_vs_p)][0] * _vs_p[i][1] for i in range(len(_vs_p)))) / 2 * _ds_ftpx * _ds_ftpx / 43560
                if _vs_a > 0.15:
                    _vs_big.append(round(_vs_a, 3))
            check(
                "vegetable_beds_are_intensive",
                not _vs_big,
                f"{len(_vs_big)} vegetable-garden bed(s) larger than 0.15 real acres {sorted(_vs_big, reverse=True)[:4]} - "
                f"an in-wall kitchen-garden tract is INTENSIVE hand-worked ground, its beds smaller than a grain-field "
                f"hem strip, not the biggest dry parcels on the map (split the tract into even ~55 ft beds)",
            )
        check(
            "dry_plots_to_scale",
            _ds_mean <= 0.25 and _ds_max <= 0.35,
            f"mean dry-crop plot area {_ds_mean:.2f} real acres (want <= 0.25), largest {_ds_max:.2f} (want <= 0.35) - a hem parcel is a smallholder strip "
            f"(~1 mu / ~0.17 acre, Buck); oversized cells mean the _dry_fields tiling constants were used as raw px "
            f"at a coarser grain instead of real feet (pass/scale them by grain)",
        )
    return _kept(locals(), ('_ds_a', '_ds_areas', '_ds_d', '_ds_ftpx', '_ds_max', '_ds_mean', '_ds_p', '_vs_a', '_vs_big', '_vs_d', '_vs_p', '_vs_veg', 'd', 'i'))


# EVERY COMB PADDY FAN HAS A FIELD FLOOR so its canal-JUNCTION triangles (the head-race fork,
# the outfall corner where a supply canal dies at the drain, the confluence wedges) are not bare
# parchment - the "blank bits on the paddies" the GM circled across cities AND villages/hamlets
# (2026-07-22). The comb carve tessellates its plots but cannot fill those wedges; a base-fill
# polygon (s.comb_base_fill, recorded in M['comb_floors'][name]) draws under the plots so the
# gaps read as field ground, not a hole. Villages/hamlets that draw via draw_comb_field or inline
# both route through the helper now. Any paddy fan (a field with field_ditches, i.e. an irrigated
# comb) must therefore have a floor. paddy_fan_gapless's 2% tolerance let the small junctions slip;
# this pins the floor at every scale.


def _seg_0122__paddy_fan_has_floor(
    *, M: Any = _UNBOUND, _ditched: Any = _UNBOUND, _floors: Any = _UNBOUND, _pf_bad: Any = _UNBOUND, check: Any = _UNBOUND, d: Any = _UNBOUND, f: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 122 (paddy_fan_has_floor) - body verbatim from the legacy gate() (feature 022)."""
    if scale in ("hamlet", "village", "town", "city"):
        _floors = M.get("comb_floors", {})
        _ditched = {d.get("field") for d in M.get("field_ditches", [])}
        _pf_bad = [f.get("name") for f in M.get("fields", []) if f.get("kind") == "paddy" and f.get("name") in _ditched and f.get("name") not in _floors]
        check(
            "paddy_fan_has_floor",
            not _pf_bad,
            f"comb paddy fan(s) with no field floor: {_pf_bad} - the carve leaves bare parchment triangles at the "
            f"canal junctions (head-race fork, outfall corner, confluences); call s.comb_base_fill(net, name) "
            f"before drawing the plots so it draws a floor under them and records M['comb_floors'][name]",
        )
    return _kept(locals(), ('_ditched', '_floors', '_pf_bad', 'd', 'f'))


# A COMB'S HEAD GROUND IS QUILTED (city-scale): the supply canals run THROUGH cultivated
# land - paddy below, dry-crop hem above - never through bare parchment. The fan head (the
# band along the mains and the fork triangle between the arms) is uncommanded by gravity,
# so the carve correctly never plants RICE there; the HEM system is what fills it (villages
# add scrub besides, so they read full either way). paddy_fan_gapless deliberately samples
# only the commanded interior - which is exactly why the bare-head regression (the GM's
# circled screenshot, 2026-07-21) sailed through green. This check owns that band: sample
# both flanks of every recorded MAIN channel beyond the hem berm, skip the sluice mouth and
# moat/ring corridors, and require the map-wide bare fraction under 20% (calibrated: the
# pre-fix manifest reads ~25%, the quilted maps ~13-16%). Fields recording plot_polys (the
# city gens) are gated; a village opts in by recording them.


def _seg_0123___hq_ftpx(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 123 (_hq_ftpx) - body verbatim from the legacy gate() (feature 022)."""
    _hq_ftpx = float(meta.get("ftpx", 1) or 1)
    return _kept(locals(), ('_hq_ftpx',))


def _seg_0124___hq_tol(*, _hq_ftpx: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 124 (_hq_tol) - body verbatim from the legacy gate() (feature 022)."""
    _hq_tol = 8.0 / _hq_ftpx
    return _kept(locals(), ('_hq_tol',))


def _seg_0125___hq_bare() -> dict[str, Any]:
    """Gate segment 125 (_hq_bare, _hq_total) - body verbatim from the legacy gate() (feature 022)."""
    _hq_bare = _hq_total = 0
    return _kept(locals(), ('_hq_bare', '_hq_total'))


def _seg_0126___hq_fields(*, M: Any = _UNBOUND, f: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 126 (_hq_fields, f) - body verbatim from the legacy gate() (feature 022)."""
    _hq_fields = [f for f in M.get("fields", []) if f.get("kind") == "paddy" and f.get("plot_polys")]
    return _kept(locals(), ('_hq_fields', 'f'))


def _seg_0127__city_fan_heads_quilted(
    *,
    M: Any = _UNBOUND,
    _hq_a: Any = _UNBOUND,
    _hq_b: Any = _UNBOUND,
    _hq_bare: Any = _UNBOUND,
    _hq_covered: Any = _UNBOUND,
    _hq_covers: Any = _UNBOUND,
    _hq_cp: Any = _UNBOUND,
    _hq_cxs: Any = _UNBOUND,
    _hq_cys: Any = _UNBOUND,
    _hq_excluded: Any = _UNBOUND,
    _hq_fields: Any = _UNBOUND,
    _hq_ftpx: Any = _UNBOUND,
    _hq_grid: Any = _UNBOUND,
    _hq_k: Any = _UNBOUND,
    _hq_lines: Any = _UNBOUND,
    _hq_lp: Any = _UNBOUND,
    _hq_lw: Any = _UNBOUND,
    _hq_mains: Any = _UNBOUND,
    _hq_moat: Any = _UNBOUND,
    _hq_off: Any = _UNBOUND,
    _hq_r: Any = _UNBOUND,
    _hq_ring: Any = _UNBOUND,
    _hq_ringw: Any = _UNBOUND,
    _hq_sluice: Any = _UNBOUND,
    _hq_tol: Any = _UNBOUND,
    _hq_total: Any = _UNBOUND,
    _pp: Any = _UNBOUND,
    ax: Any = _UNBOUND,
    ay: Any = _UNBOUND,
    bx: Any = _UNBOUND,
    by: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d: Any = _UNBOUND,
    dpts_: Any = _UNBOUND,
    f: Any = _UNBOUND,
    f2: Any = _UNBOUND,
    hw: Any = _UNBOUND,
    i: Any = _UNBOUND,
    ll: Any = _UNBOUND,
    p: Any = _UNBOUND,
    px_: Any = _UNBOUND,
    py_: Any = _UNBOUND,
    q: Any = _UNBOUND,
    qx: Any = _UNBOUND,
    qy: Any = _UNBOUND,
    sgn: Any = _UNBOUND,
    stp: Any = _UNBOUND,
    t: Any = _UNBOUND,
    ux: Any = _UNBOUND,
    uy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 127 (city_fan_heads_quilted) - body verbatim from the legacy gate() (feature 022)."""
    if _hq_fields:
        _hq_covers: list[list[tuple[float, float]]] = []  # type: ignore[no-redef]
        for f2 in M.get("fields", []):
            _hq_covers += [[(q[0], q[1]) for q in p] for p in f2.get("plot_polys", [])]
        _hq_covers += [[(q[0], q[1]) for q in d["poly"]] for d in M.get("dry_plots", [])]
        _hq_lines = [([(q[0], q[1]) for q in d["poly"]], float(d.get("w", 4))) for d in M.get("field_ditches", [])]
        _hq_lines += [([(q[0], q[1]) for q in c["poly"]], float(c.get("w", 3))) for c in M.get("channels", [])]
        _hq_moat = M.get("moat")
        _hq_ring = M.get("ring_road")
        _hq_ringw = float(M.get("ring_road_width", 7))

        def _hq_excluded(qx: float, qy: float) -> bool:
            if _hq_moat and min(seg_dist(qx, qy, _hq_moat[i2], _hq_moat[i2 + 1]) for i2 in range(len(_hq_moat) - 1)) < float(M.get("moat_width", 20)) / 2 + 12 / _hq_ftpx:
                return True
            rr_ = _hq_ring
            return rr_ is not None and min(seg_dist(qx, qy, rr_[i2], rr_[i2 + 1]) for i2 in range(len(rr_) - 1)) < _hq_ringw / 2 + 12 / _hq_ftpx

        # INDEXED (2026-07-25): this ran ~3,000 sample points against every plot polygon and every
        # ditch on the map - 14M seg_dist calls, ~58% of a city gate. Same test, pruned to the local
        # cell. A polygon is indexed by its bbox GROWN by the tolerance (so an edge-proximity hit is
        # never missed), a ditch/channel by each segment's bbox grown by its own half-width + tol.
        _hq_grid = GridIndex(max(4 * _hq_tol, 24.0 / _hq_ftpx))
        for _hq_cp in _hq_covers:
            _hq_cxs = [q[0] for q in _hq_cp]
            _hq_cys = [q[1] for q in _hq_cp]
            _hq_grid.add(min(_hq_cxs) - _hq_tol, min(_hq_cys) - _hq_tol, max(_hq_cxs) + _hq_tol, max(_hq_cys) + _hq_tol, ("p", _hq_cp, 0.0))
        for _hq_lp, _hq_lw in _hq_lines:
            _hq_r = _hq_lw / 2 + _hq_tol
            for _hq_k in range(len(_hq_lp) - 1):
                _hq_a, _hq_b = _hq_lp[_hq_k], _hq_lp[_hq_k + 1]
                _hq_grid.add(min(_hq_a[0], _hq_b[0]) - _hq_r, min(_hq_a[1], _hq_b[1]) - _hq_r, max(_hq_a[0], _hq_b[0]) + _hq_r, max(_hq_a[1], _hq_b[1]) + _hq_r, ("s", _hq_a, _hq_b, _hq_r))

        def _hq_covered(qx: float, qy: float) -> bool:
            for _it in _hq_grid.near(qx, qy):
                if _it[0] == "p":
                    _pp = _it[1]
                    if point_in_poly(qx, qy, _pp) or any(seg_dist(qx, qy, _pp[_j], _pp[(_j + 1) % len(_pp)]) < _hq_tol for _j in range(len(_pp))):
                        return True
                elif seg_dist(qx, qy, _it[1], _it[2]) < _it[3]:
                    return True
            return False

        for f in _hq_fields:
            _hq_mains = [d for d in M.get("field_ditches", []) if d.get("field") == f.get("name") and d.get("role") == "main"]
            if not _hq_mains:
                continue
            _hq_sluice = _hq_mains[0]["poly"][0]
            for d in _hq_mains:
                dpts_ = d["poly"]
                hw = float(d.get("w", 4)) / 2
                for i in range(len(dpts_) - 1):
                    ax, ay = dpts_[i]
                    bx, by = dpts_[i + 1]
                    ll = math.hypot(bx - ax, by - ay)
                    if ll < 1:
                        continue
                    ux, uy = (bx - ax) / ll, (by - ay) / ll
                    stp = 12.0 / _hq_ftpx
                    t = stp / 2
                    while t < ll:
                        px_, py_ = ax + ux * t, ay + uy * t
                        if math.hypot(px_ - _hq_sluice[0], py_ - _hq_sluice[1]) >= 90.0 / _hq_ftpx:
                            for _hq_off in (hw + 20 / _hq_ftpx, hw + 34 / _hq_ftpx, hw + 48 / _hq_ftpx):
                                for sgn in (1, -1):
                                    qx, qy = px_ - uy * _hq_off * sgn, py_ + ux * _hq_off * sgn
                                    if not _hq_excluded(qx, qy):
                                        _hq_total += 1
                                        if not _hq_covered(qx, qy):
                                            _hq_bare += 1
                        t += stp
        if _hq_total:
            check(
                "city_fan_heads_quilted",
                _hq_bare <= 0.20 * _hq_total,
                f"{_hq_bare}/{_hq_total} head-band samples along the supply canals are bare parchment (>20%) - the fan head "
                f"is uncommanded ground the DRY-CROP HEM must quilt (village-real dry_band, the fork-triangle b-side band, "
                f"the grain-scaled berm); rice cannot grow there but barley does, and bare heads are the white-gaps regression",
            )
    return _kept(
        locals(),
        (
            '_hq_a',
            '_hq_b',
            '_hq_bare',
            '_hq_covered',
            '_hq_covers',
            '_hq_cp',
            '_hq_cxs',
            '_hq_cys',
            '_hq_excluded',
            '_hq_grid',
            '_hq_k',
            '_hq_lines',
            '_hq_lp',
            '_hq_lw',
            '_hq_mains',
            '_hq_moat',
            '_hq_off',
            '_hq_r',
            '_hq_ring',
            '_hq_ringw',
            '_hq_sluice',
            '_hq_total',
            'ax',
            'ay',
            'bx',
            'by',
            'c',
            'd',
            'dpts_',
            'f',
            'f2',
            'hw',
            'i',
            'll',
            'p',
            'px_',
            'py_',
            'q',
            'qx',
            'qy',
            'sgn',
            'stp',
            't',
            'ux',
            'uy',
        ),
    )


# PADDY FANS ARE GAPLESS inside their command area: bare parchment inside a comb fan is
# ground the water commands that nobody planted - the "white spots" bug. The carve's minimum
# plot/sector/closer thresholds are REAL-FEET quantities (build_comb's `grain` scales them:
# tuned at 2 ft/px, a 3 ft/px city passes grain=2/3); left unscaled they silently drop
# sectors, head plots and gap-closers a village would plant (Tango/Nagahara re-exposed
# exactly this at the city grain, 2026-07-21 - the frozen fixture). Only fields that record
# their drawn "plot_polys" are gated (the city gens do; a village gen can opt in by recording
# them). The rim is inset away (canal berms / drain set-backs legitimately live there) and
# the tolerance covers bunds and the delivery-ditch strips between plot columns.


def _seg_0128___gpx(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 128 (_gpx) - body verbatim from the legacy gate() (feature 022)."""
    _gpx = float(meta.get("ftpx", 1) or 1)
    return _kept(locals(), ('_gpx',))


def _seg_0129___g_inset(*, _gpx: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 129 (_g_inset, _g_step, _g_tol) - body verbatim from the legacy gate() (feature 022)."""
    _g_inset, _g_tol, _g_step = 56.0 / _gpx, 6.0 / _gpx, 24.0 / _gpx
    return _kept(locals(), ('_g_inset', '_g_step', '_g_tol'))


# the plot tolerance is BUND-scale (6 real ft): anything wider than a bund must be planted
# or be WATER - the field's recorded ditches count as covered ground (they draw over the
# fan), so the delivery-ditch strips between plot columns never read as bare


def _seg_0130__gap_fields() -> dict[str, Any]:
    """Gate segment 130 (gap_fields) - body verbatim from the legacy gate() (feature 022)."""
    gap_fields = []  # type: ignore[var-annotated]
    return _kept(locals(), ('gap_fields',))


def _seg_0131__bx0(
    *,
    M: Any = _UNBOUND,
    _g_inset: Any = _UNBOUND,
    _g_step: Any = _UNBOUND,
    _g_tol: Any = _UNBOUND,
    _gpx: Any = _UNBOUND,
    bx0: Any = _UNBOUND,
    bx1: Any = _UNBOUND,
    by0: Any = _UNBOUND,
    by1: Any = _UNBOUND,
    d: Any = _UNBOUND,
    dp: Any = _UNBOUND,
    f: Any = _UNBOUND,
    fditch: Any = _UNBOUND,
    gap_fields: Any = _UNBOUND,
    gbare: Any = _UNBOUND,
    gout: Any = _UNBOUND,
    gp: Any = _UNBOUND,
    gplots: Any = _UNBOUND,
    gtotal: Any = _UNBOUND,
    gx: Any = _UNBOUND,
    gy: Any = _UNBOUND,
    hw: Any = _UNBOUND,
    i: Any = _UNBOUND,
    ok_pt: Any = _UNBOUND,
    pboxes: Any = _UNBOUND,
    px0: Any = _UNBOUND,
    px1: Any = _UNBOUND,
    py0: Any = _UNBOUND,
    py1: Any = _UNBOUND,
    q: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 131 (bx0, bx1, by0, by1) - body verbatim from the legacy gate() (feature 022)."""
    for f in M.get("fields", []):
        if f.get("kind") != "paddy" or not f.get("plot_polys") or not f.get("outline"):
            continue
        gout = [(q[0], q[1]) for q in f["outline"]]
        gplots = [[(q[0], q[1]) for q in gp] for gp in f["plot_polys"]]
        pboxes = [(min(q[0] for q in gp) - _g_tol, min(q[1] for q in gp) - _g_tol, max(q[0] for q in gp) + _g_tol, max(q[1] for q in gp) + _g_tol) for gp in gplots]
        fditch = [d for d in M.get("field_ditches", []) if d.get("field") == f.get("name")]
        bx0, by0 = min(q[0] for q in gout), min(q[1] for q in gout)
        bx1, by1 = max(q[0] for q in gout), max(q[1] for q in gout)
        gbare = gtotal = 0
        gy = by0
        while gy <= by1:
            gx = bx0
            while gx <= bx1:
                if point_in_poly(gx, gy, gout) and all(seg_dist(gx, gy, gout[i], gout[(i + 1) % len(gout)]) > _g_inset for i in range(len(gout))):
                    gtotal += 1
                    ok_pt = False
                    for gp, (px0, py0, px1, py1) in zip(gplots, pboxes, strict=True):
                        if not (px0 <= gx <= px1 and py0 <= gy <= py1):
                            continue
                        if point_in_poly(gx, gy, gp) or any(seg_dist(gx, gy, gp[i], gp[(i + 1) % len(gp)]) < _g_tol for i in range(len(gp))):
                            ok_pt = True
                            break
                    if not ok_pt:
                        for d in fditch:
                            hw = float(d.get("w", 4)) / 2 + 6.0 / _gpx
                            dp = d["poly"]
                            if any(seg_dist(gx, gy, dp[i], dp[i + 1]) < hw for i in range(len(dp) - 1)):
                                ok_pt = True
                                break
                    if not ok_pt:
                        gbare += 1
                gx += _g_step
            gy += _g_step
        if gtotal and gbare > max(2, 0.02 * gtotal):
            gap_fields.append(f"{f.get('name')} ({gbare}/{gtotal} bare)")
    return _kept(
        locals(),
        ('bx0', 'bx1', 'by0', 'by1', 'd', 'dp', 'f', 'fditch', 'gap_fields', 'gbare', 'gout', 'gp', 'gplots', 'gtotal', 'gx', 'gy', 'hw', 'i', 'ok_pt', 'pboxes', 'px0', 'px1', 'py0', 'py1', 'q'),
    )


def _seg_0132__paddy_fan_gapless(*, M: Any = _UNBOUND, check: Any = _UNBOUND, f: Any = _UNBOUND, gap_fields: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 132 (paddy_fan_gapless) - body verbatim from the legacy gate() (feature 022)."""
    if any(f.get("plot_polys") for f in M.get("fields", [])):
        check(
            "paddy_fan_gapless",
            not gap_fields,
            f"unplanted holes inside the paddy fan(s): {gap_fields} - bare parchment inside the comb's command "
            f"area means the carve dropped sectors/head plots/closers there; pass build_comb grain=2/ftpx so its "
            f"real-feet minimum-size thresholds match this map's scale",
        )
    return _kept(locals(), ('f',))


# ALMOST all shops front a street (commerce wants the street); POOR housing (laborer/burakumin)
# mostly packs the block INTERIOR, reached by alleys, not the paved street frontage. (The towns
# set the template: businesses on the frontage via s.frontage, dwellings interior via s.pack.)


def _seg_0133_000__r22(*, M: Any = _UNBOUND, r22: Any = _UNBOUND, scale: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.000 (r22, st, st_lines) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        st_lines = (
            [(st["pts"], st.get("w", 18)) for st in M.get("town_streets", [])]
            + ([(M["road"], M.get("road_width", 26))] if M.get("road") else [])
            + [(r22["pts"], r22.get("width") or 26) for r22 in M.get("roads", [])]
        )  # trunk roads carry frontage too (021: the guan-xiang wards string their shops along them)
    return _kept(locals(), ('r22', 'st', 'st_lines'))


def _seg_0133_001__on_a_street(*, b: Any = _UNBOUND, i: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, sp: Any = _UNBOUND, st_lines: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.001 (on_a_street) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):

        def on_a_street(b: dict[str, Any]) -> bool:
            # 85 REAL FEET of the street's BED EDGE (bed half-width + 85ft at the declared
            # scale): a shopfront hugs the edge of the paving, so the reach must grow with the
            # lane's width - measured from the CENTERLINE alone, the capital's 26ft Imperial
            # road put its own lawful gate-market shops (standing 2ft off the bed) "off-street"
            # by one pixel (021, 2026-08-10). The fixed 85px before that was tuned at the
            # towns' 1 ft/px grain and would call most of a 3 ft/px city "on a street".
            return any(seg_dist(b["x"], b["y"], sp[i], sp[i + 1]) < wq2 / 2 + 85 / meta.get("ftpx", 1) for sp, wq2 in st_lines for i in range(len(sp) - 1))

    return _kept(locals(), ('on_a_street',))


def _seg_0133_002__b(*, M: Any = _UNBOUND, b: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.002 (b, biz) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        biz = [b for b in M.get("buildings", []) if b.get("kind") in BUSINESS_KINDS]
    return _kept(locals(), ('b', 'biz'))


def _seg_0133_003__businesses_front_streets(
    *, b: Any = _UNBOUND, biz: Any = _UNBOUND, check: Any = _UNBOUND, off: Any = _UNBOUND, on_a_street: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0133.003 (businesses_front_streets) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):  # noqa: SIM102 - comment bank under the guard; combining would orphan it (023 convention)
        if biz:
            off = [b for b in biz if not on_a_street(b)]
            # WHY (commerce takes the valuable street frontage; dwellings sit behind/interior): settlements.md "Historical grounding"
            check(
                "businesses_front_streets",
                len(off) <= 0.15 * len(biz),
                f"{len(off)}/{len(biz)} shops/merchant houses are NOT on a street - almost every business fronts a street (the more mercantile a quarter, the more streets); only dwellings fill the block interior",
            )
    return _kept(locals(), ('b', 'off'))


def _seg_0133_004__b_1(*, M: Any = _UNBOUND, b: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.004 (b, poor) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        poor = [b for b in M.get("buildings", []) if b.get("kind") in ("laborer", "burakumin")]
    return _kept(locals(), ('b', 'poor'))


def _seg_0133_005__poor_housing_mostly_interior(
    *, b: Any = _UNBOUND, check: Any = _UNBOUND, on_a_street: Any = _UNBOUND, onst: Any = _UNBOUND, poor: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0133.005 (poor_housing_mostly_interior) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital') and poor:
        onst = [b for b in poor if on_a_street(b)]
        check(
            "poor_housing_mostly_interior",
            len(onst) <= 0.5 * len(poor),
            f"{len(onst)}/{len(poor)} laborer/burakumin dwellings sit ON a street - most poor housing jams the block INTERIOR (reached by alleys), behind the street-facing businesses",
        )
    return _kept(locals(), ('b', 'onst'))


# surrounding farmland must be WORKED: the part of each outside field that SHOWS on the map
# carries farmhouses at roughly the village/hamlet linear density (~12 per 1000px of field edge,
# min ~4). Off-map field portions have their farmhouses off-screen (fine, expected), but a field
# presenting a real on-map edge with almost no farmhouses beside it is wrong - farmers build
# close to the fields they work. We count only IN-VIEW houses against the on-map field edge, so
# a partially-rendered field is held to its SHOWN extent (the gap the old per-field >=2 missed).


def _seg_0133_006__ADJ(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.006 (ADJ) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        ADJ = 165
    return _kept(locals(), ('ADJ',))


def _seg_0133_007__FARM_LD(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.007 (FARM_LD) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        FARM_LD = 7.0  # houses per 1000px of shown edge - a floor: village fields run ~4-19, the bad ones ~0
    return _kept(locals(), ('FARM_LD',))


def _seg_0133_008__sparse(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.008 (sparse) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        sparse = []  # type: ignore[var-annotated]
    return _kept(locals(), ('sparse',))


def _seg_0133_009__cx(
    *,
    ADJ: Any = _UNBOUND,
    EX0: Any = _UNBOUND,
    EX1: Any = _UNBOUND,
    EY0: Any = _UNBOUND,
    EY1: Any = _UNBOUND,
    FARM_LD: Any = _UNBOUND,
    M: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    edge: Any = _UNBOUND,
    f: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    h: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    nv: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    sparse: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0133.009 (cx, cy, edge, f) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        for f in fields:
            cx, cy = (f["bbox"][0] + f["bbox"][2]) / 2, (f["bbox"][1] + f["bbox"][3]) / 2
            if M.get("wall") and point_in_poly(cx, cy, M["wall"]):
                continue  # in-wall plots are not surrounding farmland
            edge = onmap_field_edge(f["outline"], EX0, EY0, EX1, EY1)
            if edge < 120:
                continue  # only a tiny sliver shows - too little to require farmhouses
            nv = sum(1 for h in houses if EX0 <= h["x"] <= EX1 and EY0 <= h["y"] <= EY1 and poly_dist(h["x"], h["y"], f["outline"]) <= ADJ)
            if nv < FARM_LD * edge / 1000:
                sparse.append((f["name"], nv, round(FARM_LD * edge / 1000, 1)))
    return _kept(locals(), ('cx', 'cy', 'edge', 'f', 'h', 'nv', 'sparse'))


def _seg_0133_010__outside_fields_farmhouse_density(*, check: Any = _UNBOUND, scale: Any = _UNBOUND, sparse: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.010 (outside_fields_farmhouse_density) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        check("outside_fields_farmhouse_density", not sparse, f"shown field edge(s) with too few farmhouses beside the on-map portion (farmers build close; expect ~village density): {sparse}")
    return _kept(locals(), ())


# the IN-WALL agricultural district (the unusual city that farms inside its walls) is REAL
# farmland too. Unlike the SURROUNDING fields above - mostly off the cropped map, so only a
# FLOOR (7) is enforceable on their shown sliver - an in-wall field sits ENTIRELY in view, so
# its WHOLE perimeter must read as worked: ring it DENSELY all the way round, not a sparse few
# on one side leaving long bare edges. Held to a much higher density (the dense end of village
# ringing). Only bites when meta(agricultural_district=True) - most cities have no in-wall fields.


def _seg_0133_011__FARM_LD_INWALL(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.011 (FARM_LD_INWALL) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        FARM_LD_INWALL = 16.0  # houses per 1000px of edge - a full, all-round ring, not the off-map floor
    return _kept(locals(), ('FARM_LD_INWALL',))


def _seg_0133_012__city_interior_fields_farmhouse_density(
    *,
    ADJ: Any = _UNBOUND,
    EX0: Any = _UNBOUND,
    EX1: Any = _UNBOUND,
    EY0: Any = _UNBOUND,
    EY1: Any = _UNBOUND,
    FARM_LD_INWALL: Any = _UNBOUND,
    M: Any = _UNBOUND,
    URBAN: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    edge: Any = _UNBOUND,
    f: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    h: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    nv: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    thin: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0133.012 (city_interior_fields_farmhouse_density) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital') and URBAN and meta.get("agricultural_district") and M.get("wall"):
        thin = []
        for f in fields:
            cx, cy = (f["bbox"][0] + f["bbox"][2]) / 2, (f["bbox"][1] + f["bbox"][3]) / 2
            if not point_in_poly(cx, cy, M["wall"]):
                continue  # only the in-wall plots
            # VEGETABLE tracts are exempt from the farmstead ring: urban garden ground is
            # worked by the residents of the surrounding quarters (well/night-soil fed
            # intensive plots), not by dedicated in-wall farm households - only in-wall
            # PADDY carries the village-density farmhouse ring
            if f.get("kind") != "paddy":
                continue
            edge = onmap_field_edge(f["outline"], EX0, EY0, EX1, EY1)
            if edge < 120:
                continue
            nv = sum(1 for h in houses if poly_dist(h["x"], h["y"], f["outline"]) <= ADJ)
            if nv < FARM_LD_INWALL * edge / 1000:
                thin.append((f["name"], nv, round(FARM_LD_INWALL * edge / 1000, 1)))
        check(
            "city_interior_fields_farmhouse_density",
            not thin,
            f"in-wall agricultural field(s) too sparsely farmed - an in-wall field shows its WHOLE perimeter, so ring it densely all the way round (no long bare edges), not a token few: {thin}",
        )
    return _kept(locals(), ('cx', 'cy', 'edge', 'f', 'h', 'nv', 'thin'))


# housing packs DEEP, but no GIANT cluster may be cut off from circulation: a big block of
# dwellings with no street OR alley anywhere near it has no way in or out. Deep blocks must
# be laced with gravel alleys (s.alley) so every dwelling is reachable.


def _seg_0133_013__a(*, M: Any = _UNBOUND, a: Any = _UNBOUND, r9: Any = _UNBOUND, s: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.013 (a, acc, r9, s) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        acc = (
            [s["pts"] for s in M.get("town_streets", [])] + ([M["road"]] if M.get("road") else []) + [r9["pts"] for r9 in M.get("roads", [])] + [a["pts"] for a in M.get("alleys", [])]
        )  # trunk roads serve their roadside wards (the guan-xiang suburbs string along them)
    return _kept(locals(), ('a', 'acc', 'r9', 's'))


def _seg_0133_014__cut_off(*, acc: Any = _UNBOUND, b: Any = _UNBOUND, i: Any = _UNBOUND, ln: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.014 (cut_off) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):

        def cut_off(b: dict[str, Any]) -> bool:
            return not any(seg_dist(b["x"], b["y"], ln[i], ln[i + 1]) < 95 for ln in acc for i in range(len(ln) - 1))

    return _kept(locals(), ('cut_off',))


def _seg_0133_015__b_2(*, M: Any = _UNBOUND, b: Any = _UNBOUND, cut_off: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.015 (b, iso) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        iso = [b for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS and cut_off(b)]
    return _kept(locals(), ('b', 'iso'))


def _seg_0133_016__seen(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.016 (seen) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        seen: set[int] = set()  # type: ignore[no-redef,unused-ignore]
    return _kept(locals(), ('seen',))


def _seg_0133_017__biggest(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.017 (biggest) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        biggest = 0
    return _kept(locals(), ('biggest',))


def _seg_0133_018__biggest_1(
    *, biggest: Any = _UNBOUND, i: Any = _UNBOUND, iso: Any = _UNBOUND, j: Any = _UNBOUND, kk: Any = _UNBOUND, n: Any = _UNBOUND, scale: Any = _UNBOUND, seen: Any = _UNBOUND, stack: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0133.018 (biggest, i, j, kk) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        for i in range(len(iso)):
            if i in seen:
                continue
            stack, n = [i], 0
            seen.add(i)
            while stack:
                j = stack.pop()
                n += 1
                for kk in range(len(iso)):
                    if kk not in seen and abs(iso[j]["x"] - iso[kk]["x"]) < 46 and abs(iso[j]["y"] - iso[kk]["y"]) < 46:
                        seen.add(kk)
                        stack.append(kk)
            biggest = max(biggest, n)
    return _kept(locals(), ('biggest', 'i', 'j', 'kk', 'n', 'seen', 'stack'))


def _seg_0133_019__no_isolated_dwelling_cluster(*, biggest: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.019 (no_isolated_dwelling_cluster) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        check(
            "no_isolated_dwelling_cluster",
            biggest <= 30,
            f"a contiguous cluster of {biggest} dwellings sits >95px from any street OR alley - a giant block of houses with no way in or out; lace deep blocks with gravel alleys (s.alley) so every block is reachable",
        )
    return _kept(locals(), ())


# an alley must EARN its length by UNIQUELY serving dwellings. A building is credited to its
# NEAREST lane only (the one it actually fronts), exactly as empty_street_runs scores streets -
# so a lane counts only what no other lane already reaches. This catches BOTH a lane running off
# into a half-empty corner (a "lane to nowhere") AND a redundant lane laid beside or across one
# that already serves the same block (a perpendicular arm the block's spine already reaches, or a
# second lane shadowing a parallel street). Scaled to the buildings (~1 dwelling per 30px of its
# own length), so it holds at the city's dense small-footprint grain, not a fixed town pixel gap.


def _seg_0133_020__alley_blds(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.020 (alley_blds) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        alley_blds = M.get("buildings", []) + M.get("houses", [])
    return _kept(locals(), ('alley_blds',))


def _seg_0133_021__a_1(*, M: Any = _UNBOUND, a: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.021 (a, alleys) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        alleys = [a["pts"] for a in M.get("alleys", [])]
    return _kept(locals(), ('a', 'alleys'))


def _seg_0133_022__other(*, M: Any = _UNBOUND, s: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.022 (other, s) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        other = [s["pts"] for s in M.get("town_streets", [])] + ([M["road"]] if M.get("road") else [])
    return _kept(locals(), ('other', 's'))


def _seg_0133_023__kido(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.023 (kido) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        kido = M.get("kido", [])
    return _kept(locals(), ('kido',))


def _seg_0133_024__lane_dist(*, b: Any = _UNBOUND, i: Any = _UNBOUND, pts: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.024 (lane_dist) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):

        def lane_dist(b: dict[str, Any], pts: Poly) -> float:
            return min(seg_dist(b["x"], b["y"], pts[i], pts[i + 1]) for i in range(len(pts) - 1))

    return _kept(locals(), ('lane_dist',))


def _seg_0133_025__foot(*, b: Any = _UNBOUND, c: Any = _UNBOUND, i: Any = _UNBOUND, pts: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.025 (foot) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):

        def foot(b: dict[str, Any], pts: Poly) -> tuple[float, float]:
            return min((seg_closest(b["x"], b["y"], pts[i], pts[i + 1]) for i in range(len(pts) - 1)), key=lambda c: math.hypot(b["x"] - c[0], b["y"] - c[1]))

    return _kept(locals(), ('foot',))


def _seg_0133_026__gate_spur(
    *,
    E: Any = _UNBOUND,
    alley_blds: Any = _UNBOUND,
    b: Any = _UNBOUND,
    c: Any = _UNBOUND,
    foot: Any = _UNBOUND,
    g: Any = _UNBOUND,
    kido: Any = _UNBOUND,
    lane_dist: Any = _UNBOUND,
    pts: Any = _UNBOUND,
    reach: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0133.026 (gate_spur) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):

        def gate_spur(pts: Poly) -> float:
            # a terminal stretch running OUT to a ward GATE past the last served building is a legitimate
            # gate-access spur (the lane pulls in to a kido), NOT a lane-to-nowhere - so it does not count
            # toward the serve ratio. Trim it from each gated end (distance from the gate to the nearest
            # building the lane fronts, measured along the lane).
            spur = 0.0
            for E in (pts[0], pts[-1]):
                if not any(math.hypot(E[0] - g["x"], E[1] - g["y"]) < 20 for g in kido):
                    continue
                reach = [math.hypot(E[0] - (c := foot(b, pts))[0], E[1] - c[1]) for b in alley_blds if lane_dist(b, pts) < 60]
                if reach:
                    spur += min(reach)
            return spur

    return _kept(locals(), ('gate_spur',))


def _seg_0133_027__uniq(*, alleys: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.027 (uniq) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        uniq = [0] * len(alleys)
    return _kept(locals(), ('uniq',))


def _seg_0133_028__b_3(
    *,
    alley_blds: Any = _UNBOUND,
    alleys: Any = _UNBOUND,
    b: Any = _UNBOUND,
    best_d: Any = _UNBOUND,
    best_i: Any = _UNBOUND,
    d: Any = _UNBOUND,
    lane_dist: Any = _UNBOUND,
    li: Any = _UNBOUND,
    other: Any = _UNBOUND,
    pts: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    uniq: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0133.028 (b, best_d, best_i, d) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        for b in alley_blds:
            best_d, best_i = 60.0, None  # only buildings within a frontage band count for any lane
            for li, pts in enumerate(alleys):
                d = lane_dist(b, pts)
                if d < best_d:
                    best_d, best_i = d, li
            if best_i is None:
                continue
            if all(lane_dist(b, pts) > best_d for pts in other):  # no street/road is closer - this alley owns it
                uniq[best_i] += 1
    return _kept(locals(), ('b', 'best_d', 'best_i', 'd', 'li', 'pts', 'uniq'))


def _seg_0133_029__thin(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.029 (thin) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        thin = []  # type: ignore[var-annotated]
    return _kept(locals(), ('thin',))


def _seg_0133_030__i(
    *,
    alleys: Any = _UNBOUND,
    gate_spur: Any = _UNBOUND,
    i: Any = _UNBOUND,
    length: Any = _UNBOUND,
    li: Any = _UNBOUND,
    pts: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    thin: Any = _UNBOUND,
    uniq: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0133.030 (i, length, li, pts) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        for li, pts in enumerate(alleys):
            length = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
            length -= gate_spur(pts)  # the run out to a ward gate is access, not block-service
            if uniq[li] * 30 < length:
                thin.append((pts[0], uniq[li], round(length)))
    return _kept(locals(), ('i', 'length', 'li', 'pts', 'thin'))
