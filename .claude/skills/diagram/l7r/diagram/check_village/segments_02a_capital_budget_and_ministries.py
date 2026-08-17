"""Gate segments (capital budget and ministries; keys 0097-0106_026) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from l7r.diagram.settlement import KIDO_TOWER_KEEPCLEAR, WALL_DEFENSE, rail_quad, sat_overlap, trough_quad, wellhead_quad

from .common_01_geometry import poly_area, seg_dist, solid_structs
from .common_02_overlap_policy import check_ring_road_clear
from .common_03_capacity import (
    _UNBOUND,
    BUDGET_TOL_OVER,
    BUDGET_TOL_UNDER,
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
