"""Gate segments (city frame and yards) - bodies verbatim from check_village.py (feature 024 package split; registry order preserved)."""

import math
from typing import Any

from settlement import crop_boxes, forest_frame_span, sat_overlap

from .common_01_geometry import (
    _MATRIX_OUTSTANDING,
    _MX_NOT_GEOMETRY,
    _OVERLAP_STRUCTS,
    OVERLAP_CLASS,
    _struct_rect,
    edge_gap,
    kiln_quarters,
    largest_empty_gap,
    point_in_poly,
    poly_area,
    rect_corners,
    seg_dist,
    segments_cross,
    solid_structs,
    sweep_hi,
)
from .common_02_overlap_policy import CANOPY_STRUCT_KEYS, FOREST_REVEAL_FT, GridIndex, forest_reveal_x, matrix_extents, matrix_violations, torii_halfbox
from .common_03_capacity import (
    _UNBOUND,
    CIVIC_OPEN_TOL,
    COMMONER_KINDS,
    DEAD_ZONE_MAX,
    DWELLING_KINDS,
    EXTRAMURAL_COMMONER_MAX,
    HOUSEHOLD,
    QUARTER_DENSITY_CEIL,
    QUARTER_DENSITY_FLOOR,
    RESERVE_CAP_FRAC,
    _kept,
    city_capacity,
)


def _seg_0000__city_is_ringed_by_farmland(
    *,
    M: Any = _UNBOUND,
    _cf: Any = _UNBOUND,
    _cfa: Any = _UNBOUND,
    _cfh: Any = _UNBOUND,
    _cshare: Any = _UNBOUND,
    _f: Any = _UNBOUND,
    _flanks: Any = _UNBOUND,
    _fx: Any = _UNBOUND,
    _fy: Any = _UNBOUND,
    _i: Any = _UNBOUND,
    _o: Any = _UNBOUND,
    _wcx: Any = _UNBOUND,
    _wcy: Any = _UNBOUND,
    check: Any = _UNBOUND,
    f: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    q: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0 (city_is_ringed_by_farmland) - body verbatim from the legacy gate() (feature 022)."""
    if str(meta.get("scale")) in ("city", "capital") and M.get("wall"):
        _cf = [f for f in (M.get("fields") or []) if f.get("outline")]
        _wcx = sum(q[0] for q in M["wall"]) / len(M["wall"])
        _wcy = sum(q[1] for q in M["wall"]) / len(M["wall"])
        _flanks = set()
        for _f in _cf:
            _fx = sum(q[0] for q in _f["outline"]) / len(_f["outline"])
            _fy = sum(q[1] for q in _f["outline"]) / len(_f["outline"])
            _flanks.add(("e" if _fx > _wcx else "w") if abs(_fx - _wcx) > abs(_fy - _wcy) else ("s" if _fy > _wcy else "n"))
        # COUNT IS NOT ENOUGH - the first cut of this rule passed a capital carrying four token
        # fields on 1.3% of its sheet (GM 2026-08-11: "look at how much empty space there is! The
        # entire southwest of the city is an open field with no land... only one rice field between
        # the entire north gate and southwest gate?!"). What separates a ringed city from a
        # decorated one is AREA: Tango farms 3.8% of its sheet, Minami 3.0%, Nagahara 2.3%. 2.0% is
        # the floor, with 6+ fields across 3+ flanks, and the farmhouses that work them counted too
        # - fields without households are scenery, not agriculture.
        _cfa = 0.0
        for _f in _cf:
            _o = _f["outline"]
            _cfa += abs(sum(_o[_i][0] * _o[(_i + 1) % len(_o)][1] - _o[(_i + 1) % len(_o)][0] * _o[_i][1] for _i in range(len(_o)))) / 2
        _cshare = 100.0 * _cfa / max(1.0, float(meta.get("W", 1)) * float(meta.get("H", 1)))
        _cfh = len(M.get("houses") or [])
        check(
            "city_is_ringed_by_farmland",
            len(_cf) >= 6 and len(_flanks) >= 3 and _cshare >= 2.0 and _cfh >= 8 * len(_cf),
            f"a city must be RINGED by its farmland, and this is a token ring: {len(_cf)} field(s) on {len(_flanks)} flank(s) ({sorted(_flanks)}), farming {_cshare:.1f}% of the sheet with {_cfh} farmhouse(s) - want 6+ fields across 3+ flanks, 2.0%+ of the sheet, and 8+ farmhouses per field. The pool is the standard: Tango farms 3.8% over 11 fields with 266 farmhouses, Minami 3.0% over 6 with 149, Nagahara 2.3% over 7 with 141. Cities grow up around fertile land - keep adding paddies and the households that work them until the ground genuinely runs out",
        )
    return _kept(locals(), ('_cf', '_cfa', '_cfh', '_cshare', '_f', '_flanks', '_fx', '_fy', '_i', '_o', '_wcx', '_wcy', 'f', 'q'))


# NO SINGLE CAPTION MAY HOLD THE FRAME OPEN (GM 2026-08-11: "I am surprised that our cropping
# algorithm has not more aggressively cropped along the southern side... there should only be
# about one hundred feet between the southernmost map feature and the edge"). The crop was
# working exactly as specified - the margin is ~110 ft - but it frames CONTENT, and a caption
# counts as content. Two words floating in open ground 305 ft past the last structure were
# holding the whole south edge out, so the map read as badly cropped when it was in fact
# correctly cropped around a badly placed label. Measured per side: how far past the last
# STRUCTURE a label reaches. A caption naming a long linear feature may sit anywhere along it,
# so this costs nothing to satisfy - it just has to sit where the drawing is.
# 120 ft: the crop then adds its own ~110 ft margin on top, so a caption at the limit leaves
# ~230 ft of apparent emptiness past the last building - already generous. The capital's road
# and towpath words sat 180 ft out and read as a badly cropped map.


def _seg_0001___cf_pad() -> dict[str, Any]:
    """Gate segment 1 (_cf_pad) - body verbatim from the legacy gate() (feature 022)."""
    _cf_pad = 120.0
    return _kept(locals(), ('_cf_pad',))


def _seg_0002___cffx(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 2 (_cffx) - body verbatim from the legacy gate() (feature 022)."""
    _cffx = float(meta.get("ftpx") or 1.0)
    return _kept(locals(), ('_cffx',))


def _seg_0003___(*, M: Any = _UNBOUND, _k: Any = _UNBOUND, q: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 3 (_, _cf_struct, _k, q) - body verbatim from the legacy gate() (feature 022)."""
    _cf_struct = [q for _k, q, *_ in matrix_extents(M) if q and _k not in ("roads", "road", "streams", "channels", "aqueducts", "towpaths", "quays", "canals", "field_ditches")]
    return _kept(locals(), ('_', '_cf_struct', '_k', 'q'))


# CANOPY IS CONTENT: a wood's caption sits over the wood, and a forest is drawn as individual
# crowns rather than as a footprint - so without them Moritono's "Shirin Forest" scored as a
# word floating in emptiness when it is sitting on the very thing it names.


def _seg_0004___cf_tc(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 4 (_cf_tc) - body verbatim from the legacy gate() (feature 022)."""
    _cf_tc = M.get("tree_crowns") or []
    return _kept(locals(), ('_cf_tc',))


def _seg_0005___cf_struct(*, _cf_struct: Any = _UNBOUND, _cf_tc: Any = _UNBOUND, _ci: Any = _UNBOUND, _cr: Any = _UNBOUND, _cx: Any = _UNBOUND, _cy: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 5 (_cf_struct, _ci, _cr, _cx) - body verbatim from the legacy gate() (feature 022)."""
    for _ci in range(0, len(_cf_tc) - 2, 3):
        _cx, _cy, _cr = _cf_tc[_ci], _cf_tc[_ci + 1], _cf_tc[_ci + 2]
        _cf_struct.append([(_cx - _cr, _cy - _cr), (_cx + _cr, _cy - _cr), (_cx + _cr, _cy + _cr), (_cx - _cr, _cy + _cr)])
    return _kept(locals(), ('_cf_struct', '_ci', '_cr', '_cx', '_cy'))


def _seg_0006___cf_bad() -> dict[str, Any]:
    """Gate segment 6 (_cf_bad) - body verbatim from the legacy gate() (feature 022)."""
    _cf_bad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('_cf_bad',))


def _seg_0007___cf_bad_1(
    *,
    M: Any = _UNBOUND,
    _cf_bad: Any = _UNBOUND,
    _cf_pad: Any = _UNBOUND,
    _cf_struct: Any = _UNBOUND,
    _cffx: Any = _UNBOUND,
    _lb: Any = _UNBOUND,
    _over: Any = _UNBOUND,
    _sx0: Any = _UNBOUND,
    _sx1: Any = _UNBOUND,
    _sy0: Any = _UNBOUND,
    _sy1: Any = _UNBOUND,
    p: Any = _UNBOUND,
    q: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 7 (_cf_bad, _lb, _over, _sx0) - body verbatim from the legacy gate() (feature 022)."""
    if _cf_struct and M.get("labels"):
        _sx0 = min(min(p[0] for p in q) for q in _cf_struct)
        _sy0 = min(min(p[1] for p in q) for q in _cf_struct)
        _sx1 = max(max(p[0] for p in q) for q in _cf_struct)
        _sy1 = max(max(p[1] for p in q) for q in _cf_struct)
        for _lb in M["labels"]:
            if len(_lb) < 6:
                continue
            _over = max((_sx0 - _lb[0]), (_lb[2] - _sx1), (_sy0 - _lb[1]), (_lb[3] - _sy1)) * _cffx
            if _over > _cf_pad:
                _cf_bad.append((str(_lb[5]), round(_over)))
    return _kept(locals(), ('_cf_bad', '_lb', '_over', '_sx0', '_sx1', '_sy0', '_sy1', 'p', 'q'))


def _seg_0008__no_caption_holds_the_frame_open(*, _cf_bad: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 8 (no_caption_holds_the_frame_open) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "no_caption_holds_the_frame_open",
        not _cf_bad,
        f"caption(s) reaching far past the last STRUCTURE on their side, which drags the crop out with them (name, ft beyond): {sorted(_cf_bad)[:4]} - the crop frames content and a label IS content, so a word left floating in open ground reads as a badly cropped map; slide the caption along its subject to where the drawing is",
    )
    return _kept(locals(), ())


# A ROADSIDE WORK STANDS ON ITS ROAD, AND LIES ALONG IT (GM 2026-08-11: "the flophouse near
# the southwest city gate is absurdly far from the road - about three hundred feet - and it
# should be oriented to face the road... the two kiln works should be aligned with the road
# too"). Both halves are the same fact: these are features DEFINED by the way they serve. A
# doss-house exists to catch travelers arriving on that road; a kiln hauls fuel and clay by
# cart and stands on its haul road. Measured in real feet against the CURRENT ways, so a
# re-routed road drags them red rather than leaving them adrift.
# Distances calibrated from the pool, not guessed: doss-houses sit 84-420 ft off their road
# across the shipped maps, and the GM called ~300 ft "absurd" - 200 ft is comfortably past
# every reasonable one and short of every complaint. A KILN carries no distance rule at all: a
# nuisance works belongs OUT of town by its nature, and the GM's ask for it was alignment ("the
# two kiln works should be aligned with the road"), not proximity. None means angle-only.


def _seg_0009___rw_reg() -> dict[str, Any]:
    """Gate segment 9 (_rw_reg) - body verbatim from the legacy gate() (feature 022)."""
    _rw_reg: dict[str, Any] = {"flophouses": 200.0, "kilns": None}
    return _kept(locals(), ('_rw_reg',))


def _seg_0010___k(*, M: Any = _UNBOUND, _k: Any = _UNBOUND, r: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 10 (_k, _rw_polys, r) - body verbatim from the legacy gate() (feature 022)."""
    _rw_polys = [r["pts"] for _k in ("roads", "streets", "town_streets", "lanes", "alleys") for r in (M.get(_k) or []) if isinstance(r, dict) and r.get("pts")]
    return _kept(locals(), ('_k', '_rw_polys', 'r'))


def _seg_0011___rw_polys(*, M: Any = _UNBOUND, _rw_polys: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 11 (_rw_polys) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("road"):
        _rw_polys.append(M["road"])
    return _kept(locals(), ('_rw_polys',))


def _seg_0012___rw_bad() -> dict[str, Any]:
    """Gate segment 12 (_rw_bad) - body verbatim from the legacy gate() (feature 022)."""
    _rw_bad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('_rw_bad',))


def _seg_0013___d(
    *,
    M: Any = _UNBOUND,
    _d: Any = _UNBOUND,
    _i: Any = _UNBOUND,
    _pp: Any = _UNBOUND,
    _r: Any = _UNBOUND,
    _rbear: Any = _UNBOUND,
    _rbest: Any = _UNBOUND,
    _rerr: Any = _UNBOUND,
    _rgap: Any = _UNBOUND,
    _rk: Any = _UNBOUND,
    _rmax: Any = _UNBOUND,
    _rw_bad: Any = _UNBOUND,
    _rw_polys: Any = _UNBOUND,
    _rw_reg: Any = _UNBOUND,
    _rwf: Any = _UNBOUND,
    meta: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 13 (_d, _i, _pp, _r) - body verbatim from the legacy gate() (feature 022)."""
    if _rw_polys:
        _rwf = float(meta.get("ftpx") or 1.0)
        for _rk, _rmax in _rw_reg.items():
            for _r in M.get(_rk) or []:
                # no coordinate guard: both keys are in _OVERLAP_STRUCTS, so _struct_rect has
                # already demanded x/y of every record long before this check runs
                _rbest, _rbear = float("inf"), 0.0
                for _pp in _rw_polys:
                    for _i in range(len(_pp) - 1):
                        _d = seg_dist(_r["x"], _r["y"], _pp[_i], _pp[_i + 1])
                        if _d < _rbest:
                            _rbest, _rbear = _d, math.degrees(math.atan2(_pp[_i + 1][1] - _pp[_i][1], _pp[_i + 1][0] - _pp[_i][0])) % 180.0
                _rgap = (_rbest - max(_r.get("w", 0), _r.get("h", 0)) / 2.0) * _rwf
                _rerr = abs((float(_r.get("rot", 0.0)) % 180.0) - _rbear)
                _rerr = min(_rerr, 180.0 - _rerr)
                if _rmax is not None and _rgap > _rmax:
                    _rw_bad.append((_rk, round(_r["x"]), round(_r["y"]), f"{round(_rgap)}ft"))
                elif _rerr > 12.0 and _rgap < 400.0:
                    _rw_bad.append((_rk, round(_r["x"]), round(_r["y"]), f"{round(_rerr)}deg"))
    return _kept(locals(), ('_d', '_i', '_pp', '_r', '_rbear', '_rbest', '_rerr', '_rgap', '_rk', '_rmax', '_rw_bad', '_rwf'))


def _seg_0014__roadside_works_stand_on_their_road(*, _rw_bad: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 14 (roadside_works_stand_on_their_road) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "roadside_works_stand_on_their_road",
        not _rw_bad,
        f"roadside work(s) adrift from the way they serve, or square to it while it runs at an angle: {sorted(_rw_bad)[:5]} - a doss-house catches travelers off that road and a kiln carts its fuel along it; derive the seat and the angle from the way (settlement._way_bearing_near) instead of pinning them",
    )
    return _kept(locals(), ())


# A CAPTION NAMING A POINT ON A WATERCOURSE MUST STAND AT THAT POINT (GM 2026-08-11: "the
# aqueduct labels are still really far away from the things that they are labeling... look at
# how much empty space exists between the intake weir and the label that labels it"). The
# standoff ladder seats a caption at LABEL_MIN_AIR and `label_hugs_its_referent` measures the
# finished gap - but BOTH only govern a caption that declares a subject, and these are placed
# by hand with no referent, so they escaped the pair of them. Here the subject is not declared,
# it is DERIVED: the manifest records where the intake and the terminus are, so the check reads
# the current geometry and a re-routed duct drags its words along instead of stranding them.


def _seg_0015___wwsub() -> dict[str, Any]:
    """Gate segment 15 (_wwsub) - body verbatim from the legacy gate() (feature 022)."""
    _wwsub: list[tuple[str, tuple[float, float]]] = []
    return _kept(locals(), ('_wwsub',))


def _seg_0016___aq(*, M: Any = _UNBOUND, _aq: Any = _UNBOUND, _term: Any = _UNBOUND, _wwsub: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 16 (_aq, _term, _wwsub) - body verbatim from the legacy gate() (feature 022)."""
    for _aq in M.get("aqueducts") or []:
        if _aq.get("intake"):
            _wwsub.append(("intake weir", (float(_aq["intake"][0]), float(_aq["intake"][1]))))
        _term = _aq.get("to") or ((_aq.get("poly") or [[None, None]]) or [[None, None]])[-1]
        if _term and len(_term) >= 2 and _term[0] is not None:
            _wwsub.append(("settling basin", (float(_term[0]), float(_term[1]))))
    return _kept(locals(), ('_aq', '_term', '_wwsub'))


def _seg_0017___sg(*, M: Any = _UNBOUND, _sg: Any = _UNBOUND, _wwsub: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 17 (_sg, _wwsub) - body verbatim from the legacy gate() (feature 022)."""
    for _sg in M.get("sluice_gates") or []:
        if isinstance(_sg, dict) and "x" in _sg and "y" in _sg:
            _wwsub.append(("sluice gate", (float(_sg["x"]), float(_sg["y"]))))
    return _kept(locals(), ('_sg', '_wwsub'))


def _seg_0018___ww_bad() -> dict[str, Any]:
    """Gate segment 18 (_ww_bad) - body verbatim from the legacy gate() (feature 022)."""
    _ww_bad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('_ww_bad',))


def _seg_0019___g(
    *,
    M: Any = _UNBOUND,
    _g: Any = _UNBOUND,
    _lb: Any = _UNBOUND,
    _txt: Any = _UNBOUND,
    _ww_bad: Any = _UNBOUND,
    _wwf: Any = _UNBOUND,
    _wwnear: Any = _UNBOUND,
    _wwsub: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    nm: Any = _UNBOUND,
    pt: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 19 (_g, _lb, _txt, _ww_bad) - body verbatim from the legacy gate() (feature 022)."""
    for _lb in M["labels"]:
        if len(_lb) < 6:  # a degenerate record carries no text, so it names nothing
            continue
        _txt = str(_lb[5]).lower()
        _wwnear = [pt for nm, pt in _wwsub if nm in _txt]
        if not _wwnear:
            continue
        _g = min(math.hypot(max(0.0, max(pt[0] - _lb[2], _lb[0] - pt[0])), max(0.0, max(pt[1] - _lb[3], _lb[1] - pt[1]))) for pt in _wwnear)
        _wwf = float(meta.get("ftpx") or 1.0)
        if _g * _wwf > 90.0:
            _ww_bad.append((_lb[5], round(_g * _wwf)))
    return _kept(locals(), ('_g', '_lb', '_txt', '_ww_bad', '_wwf', '_wwnear', 'nm', 'pt'))


def _seg_0020__waterworks_captions_stand_at_their_point(*, _ww_bad: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 20 (waterworks_captions_stand_at_their_point) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "waterworks_captions_stand_at_their_point",
        not _ww_bad,
        f"caption(s) naming a point on a watercourse, drawn far from it with open ground between (name, ft): {sorted(_ww_bad)} - derive the seat from the point the manifest records (a hand-placed label carries no referent, so neither the standoff ladder nor label_hugs_its_referent governs it)",
    )
    return _kept(locals(), ())


# A placement run that lands far under its ask is authored-vs-landed DRIFT, and _shortfall
# RECORDING it (GM 2026-08-05, "we definitely want that to be visible") turned out not to be
# enough on its own: the capital authored 283 frontage seats, drew 129, and the gate stayed
# green because nothing read the record back. 60% is the line because the only two runs in the
# pool that miss an AUTHORED count miss it by a hair - Ubame 21/23, Hirameki 13/14 - while
# every genuine drift sits far below it. A run that MEANS "place up to N" declares itself with
# fill=True and is never recorded here at all, so the check governs authored counts only.
# A SMALL ask is not judged by a percentage. A four-house monk terrace that seats two is one
# seat of rounding in a pocket, and chasing it just oscillates: trim to two, the neighbour's
# trim frees a hair, it seats three, and round it goes. Under eight the rule is simply that
# SOMETHING landed - a run that draws nothing at all is a real hole in the map either way.


def _seg_0021___ask_bad(*, M: Any = _UNBOUND, s: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 21 (_ask_bad, s) - body verbatim from the legacy gate() (feature 022)."""
    _ask_bad = [
        f"{s.get('by')}@{s.get('at')} {s.get('placed')}/{s.get('wanted')}"
        for s in (M.get("shortfalls") or [])
        if s.get("wanted") and (s.get("placed", 0) == 0 if s["wanted"] < 8 else s.get("placed", 0) < 0.6 * s["wanted"])
    ]
    return _kept(locals(), ('_ask_bad', 's'))


def _seg_0022__placement_runs_meet_their_ask(*, _ask_bad: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 22 (placement_runs_meet_their_ask) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "placement_runs_meet_their_ask",
        not _ask_bad,
        f"{len(_ask_bad)} placement run(s) landed under 60% of the gen's ask: {_ask_bad[:6]} - make room for them, TRIM the ask to what the ground really holds, or pass fill=True where the number is a capacity budget ('place up to N') rather than an authored count",
    )
    return _kept(locals(), ())


# EVERY canopy crown the map draws, as (x, y, r) - forest/copse stands, their fringes, the fengshui
# grove clumps and the per-house yashikirin belts all record here (settlement._record_crowns). Stored
# flat because a to-scale map draws thousands. This is the DRAWN geometry, not the reserved area, so
# it is what the "nothing is drawn under a tree" checks measure.


def _seg_0023___tc(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 23 (_tc) - body verbatim from the legacy gate() (feature 022)."""
    _tc = M.get("tree_crowns") or []
    return _kept(locals(), ('_tc',))


def _seg_0024__crowns(*, _tc: Any = _UNBOUND, i: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 24 (crowns, i) - body verbatim from the legacy gate() (feature 022)."""
    crowns = [(_tc[i], _tc[i + 1], _tc[i + 2]) for i in range(0, len(_tc) - 2, 3)]
    return _kept(locals(), ('crowns', 'i'))


# INDEXED for the same reason _hq_covered is: a to-scale map draws thousands of crowns and
# carries hundreds of structures, and every "is anything under a tree" question is local. Each
# crown is indexed by its own disc bbox; a caller queries the rect it cares about grown by the
# LARGEST crown radius, so no overlap can be pruned away. Cell = 4x the mean crown.


def _seg_0025___cr_max(*, c: Any = _UNBOUND, crowns: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 25 (_cr_max, c) - body verbatim from the legacy gate() (feature 022)."""
    _cr_max = max((c[2] for c in crowns), default=0.0)
    return _kept(locals(), ('_cr_max', 'c'))


def _seg_0026__c(*, c: Any = _UNBOUND, crowns: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 26 (c, crown_grid) - body verbatim from the legacy gate() (feature 022)."""
    crown_grid = GridIndex(max(4 * (sum(c[2] for c in crowns) / len(crowns)) if crowns else 1.0, 8.0))
    return _kept(locals(), ('c', 'crown_grid'))


def _seg_0027___c(*, _c: Any = _UNBOUND, crown_grid: Any = _UNBOUND, crowns: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 27 (_c, crown_grid) - body verbatim from the legacy gate() (feature 022)."""
    for _c in crowns:
        crown_grid.add(_c[0] - _c[2], _c[1] - _c[2], _c[0] + _c[2], _c[1] + _c[2], _c)
    return _kept(locals(), ('_c', 'crown_grid'))


# NO TREE IS DRAWN ON A ROOF (GM 2026-07-25). A crown over a building hides the building - the map
# loses a structure the reader is meant to see - so no drawn crown may overlap any ROOFED footprint.
# This is stricter than the old reserved-area rules, which let a grove "hug the eaves": the fix at
# placement is per-crown (the stand THINS around a building rather than retreating from it), so the
# check has to read the crowns too. Open-air yards/gardens are deliberately out of scope - they have
# their own sun-corridor rules, and a crown over a yard corner is a real thing.


def _seg_0028__structures_clear_of_trees(
    *,
    M: Any = _UNBOUND,
    _cr_max: Any = _UNBOUND,
    check: Any = _UNBOUND,
    crown_grid: Any = _UNBOUND,
    crowns: Any = _UNBOUND,
    dx: Any = _UNBOUND,
    dy: Any = _UNBOUND,
    hh: Any = _UNBOUND,
    hw: Any = _UNBOUND,
    k: Any = _UNBOUND,
    o: Any = _UNBOUND,
    tr: Any = _UNBOUND,
    tx: Any = _UNBOUND,
    ty: Any = _UNBOUND,
    under: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 28 (structures_clear_of_trees) - body verbatim from the legacy gate() (feature 022)."""
    if crowns:
        under = []
        for k in CANOPY_STRUCT_KEYS:
            for o in M.get(k) or []:
                hw, hh = o.get("vw", o["w"]) / 2, o.get("vh", o["h"]) / 2  # the DRAWN box
                if o.get("rot"):
                    hw = hh = math.hypot(hw, hh)  # mirrors settlement._canopy_keepouts
                for tx, ty, tr in crown_grid.near_rect(o["x"] - hw - _cr_max, o["y"] - hh - _cr_max, o["x"] + hw + _cr_max, o["y"] + hh + _cr_max):
                    dx, dy = max(abs(tx - o["x"]) - hw, 0.0), max(abs(ty - o["y"]) - hh, 0.0)
                    if dx * dx + dy * dy < tr * tr:
                        under.append((k, round(o["x"]), round(o["y"])))
                        break
        check(
            "structures_clear_of_trees",
            not under,
            f"{len(under)} building(s) sit UNDER a drawn tree crown: {under[:4]} - a tree drawn on a roof "
            f"erases the building; the grove/stand must THIN around it (settlement._crown_covers filters "
            f"every crown at draw time, and a wood drawn BEFORE the buildings blocks its canopy reach so "
            f"later placement stays out from under it)",
        )
    return _kept(locals(), ('dx', 'dy', 'hh', 'hw', 'k', 'o', 'tr', 'tx', 'ty', 'under'))


def _seg_0029___fanft(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 29 (_fanft) - body verbatim from the legacy gate() (feature 022)."""
    _fanft = float(meta.get("ftpx") or 1)
    return _kept(locals(), ('_fanft',))


# FARMS REACH THEIR FIELDS (GM 2026-08-02: hoshizora's lone farmhouse across the Imperial Road,
# alone inside the merchant block). Every farmstead with cultivated ground in reach must be able to
# walk to SOME of it without crossing a ROAD: if every reachable field/dry plot lies across a road,
# the steading is on the wrong side of the highway. ROADS only - streams are crossed by footbridges
# (the NW-bank pattern is deliberate) and lanes/streets are village grain. FAMILY: association/
# reach, deliberately center-based (the question is which side of the highway the steading lives
# on, not a clearance); reach = 500 real ft, generous enough that the pool's true farm belts all
# qualify (calibrated pool-wide 2026-08-03: exactly one house fires, the motivating defect).


def _seg_0030___rdpls(*, M: Any = _UNBOUND, r: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 30 (_rdpls, r) - body verbatim from the legacy gate() (feature 022)."""
    _rdpls = [r.get("pts") or [] for r in (M.get("roads") or [])]
    return _kept(locals(), ('_rdpls', 'r'))


def _seg_0031___rdpls_1(*, _rdpls: Any = _UNBOUND, r: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 31 (_rdpls, r) - body verbatim from the legacy gate() (feature 022)."""
    _rdpls = [r for r in _rdpls if len(r) >= 2]
    return _kept(locals(), ('_rdpls', 'r'))


def _seg_0032__farmsteads_reach_their_fields_unsevered(
    *,
    M: Any = _UNBOUND,
    _cverts: Any = _UNBOUND,
    _dp: Any = _UNBOUND,
    _fanft: Any = _UNBOUND,
    _ff: Any = _UNBOUND,
    _hh: Any = _UNBOUND,
    _rdpls: Any = _UNBOUND,
    _reach: Any = _UNBOUND,
    _rp: Any = _UNBOUND,
    _sever: Any = _UNBOUND,
    _svnear: Any = _UNBOUND,
    _vv: Any = _UNBOUND,
    check: Any = _UNBOUND,
    i: Any = _UNBOUND,
    p: Any = _UNBOUND,
    vx: Any = _UNBOUND,
    vy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 32 (farmsteads_reach_their_fields_unsevered) - body verbatim from the legacy gate() (feature 022)."""
    if _rdpls and M.get("houses"):
        _cverts = [(p[0], p[1]) for _ff in M.get("fields", []) if _ff.get("kind") == "paddy" for p in _ff["outline"]]
        _cverts += [(p[0], p[1]) for _dp in M.get("dry_plots", []) for p in _dp["poly"]]
        _reach = 500.0 / _fanft
        _sever = []
        for _hh in M["houses"]:
            # _svnear, not _near: gate() is one huge scope and `_near` is already bound (tuple) far below - the documented mypy name-collision gotcha
            _svnear = [(vx, vy) for vx, vy in _cverts if (vx - _hh["x"]) ** 2 + (vy - _hh["y"]) ** 2 <= _reach * _reach]
            if _svnear and all(any(segments_cross((_hh["x"], _hh["y"]), _vv, _rp[i], _rp[i + 1]) for _rp in _rdpls for i in range(len(_rp) - 1)) for _vv in _svnear):
                _sever.append((round(_hh["x"]), round(_hh["y"])))
        check(
            "farmsteads_reach_their_fields_unsevered",
            not _sever,
            f"farmstead(s) severed from every reachable field by a road: {_sever} - a farmhouse lives on "
            f"its fields' side of the highway (settlement.ring drops severed candidates; hand seats must "
            f"honor the same rule)",
        )
    return _kept(locals(), ('_cverts', '_dp', '_ff', '_hh', '_reach', '_rp', '_sever', '_svnear', '_vv', 'i', 'p', 'vx', 'vy'))


# Every HARD feature the frame is meant to CONTAIN must actually lie INSIDE the rendered window. A deferred
# feature placed AFTER crop_to_content - a set-apart back-slope graveyard, an outlying shrine, the wells -
# can land outside the tight frame and be silently CLIPPED (caught the Ueda west graveyard, which the crop
# never framed because it was drawn after the crop). Scoped to the crop-to-content scales; a town/city is
# framed bespoke (tight to walls, fields run off-edge) so its "off-frame is intentional" is not a bug here.


def _seg_0033__hard_features_within_frame(
    *,
    ALLOW: Any = _UNBOUND,
    EX0: Any = _UNBOUND,
    EX1: Any = _UNBOUND,
    EY0: Any = _UNBOUND,
    EY1: Any = _UNBOUND,
    Hd: Any = _UNBOUND,
    M: Any = _UNBOUND,
    Wd: Any = _UNBOUND,
    _FRAME_SET: Any = _UNBOUND,
    _HARD_IN_FRAME: Any = _UNBOUND,
    _edge_loose: Any = _UNBOUND,
    _edge_slack: Any = _UNBOUND,
    _fsx: Any = _UNBOUND,
    _fsy: Any = _UNBOUND,
    _fx: Any = _UNBOUND,
    _fy: Any = _UNBOUND,
    _txh: Any = _UNBOUND,
    _tyd: Any = _UNBOUND,
    _tyu: Any = _UNBOUND,
    _vw: Any = _UNBOUND,
    check: Any = _UNBOUND,
    clipped: Any = _UNBOUND,
    fd: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    fp: Any = _UNBOUND,
    fsx: Any = _UNBOUND,
    fsy: Any = _UNBOUND,
    fx0: Any = _UNBOUND,
    fx1: Any = _UNBOUND,
    fy0: Any = _UNBOUND,
    fy1: Any = _UNBOUND,
    k: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    o: Any = _UNBOUND,
    p: Any = _UNBOUND,
    pcx: Any = _UNBOUND,
    pcy: Any = _UNBOUND,
    prx: Any = _UNBOUND,
    pry: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    side: Any = _UNBOUND,
    t: Any = _UNBOUND,
    v: Any = _UNBOUND,
    vb: Any = _UNBOUND,
    xs: Any = _UNBOUND,
    ys: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 33 (crop_hugs_content, hard_features_within_frame) - body verbatim from the legacy gate() (feature 022)."""
    if scale in ("hamlet", "village", "town") and _vw:
        # the village/hamlet hard features (a town/city carries urban/funerary kinds recorded as lists that this
        # per-scale check does not model). Each carries EITHER a torii list [x,y,z], a `poly`, a well `r`, or w/h.
        # `village_groves` is NOT held to containment (GM 2026-07-20): the communal windbreak may CLIP at the
        # frame edge - part of the belt in view reads as "the wood continues", and the crop is no longer held
        # open for it (crop_hugs_content below gates that). It must still be PARTLY visible: a windbreak
        # entirely outside the view is a lost feature, so it fires here like any fully-clipped hard feature.
        _HARD_IN_FRAME = ("houses", "gardens", "threshing_yards", "village_groves", "groves", "dry_plots", "manors", "religious", "shrines", "farm_sheds", "wells", "cemeteries", "torii")
        clipped = []
        for k in _HARD_IN_FRAME:
            for o in M.get(k, []):
                if k == "torii":  # recorded [x, y, z]; framed at the true glyph half-box (see torii_halfbox)
                    _txh, _tyu, _tyd = torii_halfbox(meta.get("ftpx", 1))
                    fx0, fy0, fx1, fy1 = o[0] - _txh, o[1] - _tyu, o[0] + _txh, o[1] + _tyd
                elif o.get("poly"):
                    xs = [p[0] for p in o["poly"]]
                    ys = [p[1] for p in o["poly"]]
                    fx0, fy0, fx1, fy1 = min(xs), min(ys), max(xs), max(ys)
                elif "r" in o:  # a well carries a radius, not w/h
                    fx0, fy0, fx1, fy1 = o["x"] - o["r"], o["y"] - o["r"], o["x"] + o["r"], o["y"] + o["r"]
                else:  # every other hard feature carries w/h
                    fx0, fy0, fx1, fy1 = o["x"] - o["w"] / 2, o["y"] - o["h"] / 2, o["x"] + o["w"] / 2, o["y"] + o["h"] / 2
                if k == "village_groves":
                    if fx1 < EX0 - 1 or fx0 > EX1 + 1 or fy1 < EY0 - 1 or fy0 > EY1 + 1:  # ENTIRELY outside
                        clipped.append((k, round((fx0 + fx1) / 2), round((fy0 + fy1) / 2)))
                elif fx0 < EX0 - 1 or fy0 < EY0 - 1 or fx1 > EX1 + 1 or fy1 > EY1 + 1:
                    clipped.append((k, round((fx0 + fx1) / 2), round((fy0 + fy1) / 2)))
        check(
            "hard_features_within_frame",
            not clipped,
            f"{len(clipped)} hard feature(s) run OUTSIDE the cropped frame and get clipped: {clipped[:4]} - a "
            f"feature the frame must contain (esp. a set-apart graveyard/shrine placed AFTER crop_to_content) "
            f"must sit inside the view; place it BEFORE the crop so the frame includes it",
        )

        # ... and the frame must be TIGHT to that content (GM 2026-07-20): prefer the SMALLER crop - a view
        # edge held open where the only content in the extra band is the communal windbreak (already partly
        # visible) or nothing at all is wasted image. On each side, the view edge must sit within ALLOW px of
        # the outermost frame-setting content - everything crop_to_content counts EXCEPT village_groves (the
        # windbreak clips): structures, homestead plots/groves, dry plots, torii, the fields' VISIBLE extent,
        # the pond. ALLOW = 56: the biggest crop margin in use is 44 (hamlets; villages 30-40) plus a little
        # slack, so a conforming crop passes on every side while a grove-held edge (Kikuta's north sat ~200px
        # past the houses to contain the windbreak) fires.
        # mirrors settlement.py _CROP_HARD minus village_groves (keep the two in step), plus the torii /
        # field-vis / pond / forest extras crop_to_content adds - Moritono taught the hard way that a partial
        # mirror reads a legitimately forest-framed hamlet edge as "held open"
        _FRAME_SET = (
            "houses",
            "gardens",
            "threshing_yards",
            "groves",
            "dry_plots",
            "buildings",
            "manors",
            "religious",
            "shrines",
            "flophouses",
            "storehouses",
            "farm_sheds",
            "merchant_estates",
            "wells",
            "fire_towers",
            "ministries",
            "inspection_stations",
            "cemeteries",
            "mausoleums",
            "cremation_grounds",
            "ossuaries",
            "forest_patches",
            "pastures",
        )
        fsx: list[float] = []  # type: ignore[no-redef]
        fsy: list[float] = []  # type: ignore[no-redef]
        for k in _FRAME_SET:
            for o in M.get(k, []):
                if o.get("poly"):
                    fsx += [p[0] for p in o["poly"]]
                    fsy += [p[1] for p in o["poly"]]
                elif "r" in o:
                    fsx += [o["x"] - o["r"], o["x"] + o["r"]]
                    fsy += [o["y"] - o["r"], o["y"] + o["r"]]
                elif "w" in o and "h" in o:
                    fsx += [o["x"] - o["w"] / 2, o["x"] + o["w"] / 2]
                    fsy += [o["y"] - o["h"] / 2, o["y"] + o["h"] / 2]
        _txh, _tyu, _tyd = torii_halfbox(meta.get("ftpx", 1))
        for t in M.get("torii", []):
            fsx += [t[0] - _txh, t[0] + _txh]
            fsy += [t[1] - _tyu, t[1] + _tyd]
        for fd in fields:
            vb = fd.get("vis_bbox")
            if vb:
                fsx += [vb[0], vb[2]]
                fsy += [vb[1], vb[3]]
        if M.get("pond"):
            pcx, pcy, prx, pry = M["pond"]
            fsx += [pcx - prx, pcx + prx]
            fsy += [pcy - pry, pcy + pry]
        if M.get("forest"):  # the big EDGE forest is frame-setting exactly as the crop counts it:
            # revealed only a band deep on the axis it FACES, and not frame-setting at all on the
            # axis it RUNS ALONG (a tree line off both canvas ends bounds nothing) - forest_frame_span.
            _fx = forest_reveal_x(M["forest"], M.get("forest_edge"), FOREST_REVEAL_FT / meta.get("ftpx", 1), Wd)
            _fy = [min(max(fp[1], 0), Hd) for fp in M["forest"]]
            _fsx, _fsy = forest_frame_span(_fx, Wd, fsx), forest_frame_span(_fy, Hd, fsy)
            fsx += list(_fsx)
            fsy += list(_fsy)
        if fsx:
            ALLOW = 56
            _edge_slack = {
                "west": min(fsx) - EX0,
                "north": min(fsy) - EY0,
                "east": EX1 - max(fsx),
                "south": EY1 - max(fsy),
            }
            _edge_loose = {side: round(v) for side, v in _edge_slack.items() if v > ALLOW}
            check(
                "crop_hugs_content",
                not _edge_loose,
                f"view edge(s) held open past the frame-setting content by more than {ALLOW}px: {_edge_loose} - prefer the smaller crop; a band whose only extra content is more windbreak grove (or open ground) is wasted image, so let the grove clip at the edge (crop_to_content no longer counts village_groves)",
            )
    return _kept(
        locals(),
        (
            'ALLOW',
            '_FRAME_SET',
            '_HARD_IN_FRAME',
            '_edge_loose',
            '_edge_slack',
            '_fsx',
            '_fsy',
            '_fx',
            '_fy',
            '_txh',
            '_tyd',
            '_tyu',
            'clipped',
            'fd',
            'fp',
            'fsx',
            'fsy',
            'fx0',
            'fx1',
            'fy0',
            'fy1',
            'k',
            'o',
            'p',
            'pcx',
            'pcy',
            'prx',
            'pry',
            'side',
            't',
            'v',
            'vb',
            'xs',
            'ys',
        ),
    )


# ONE FEATURE MUST NOT HOLD THE WHOLE FRAME OPEN (GM 2026-07-25). crop_hugs_content asks
# whether the MARGIN is generous; this asks the opposite question - whether a single element,
# standing far outside everything else, is by itself forcing a bigger image. Move it and the
# whole map crops tighter, so it is worth knowing about.
#
# THE DISCRIMINATOR IS THE RATIO, NOT THE GAP. A pond or a forest that extends the frame IS
# the outlying content: big, and meant to be out there. Measured across the pool, every
# legitimate case has a gap roughly equal to the feature's own size (ponds 1.03-1.35x,
# moritono's forest 1.14x), while Tango's tanning-yard caption stood 178 px past everything
# with a 10 px box of its own - 17.8x. So the rule is "further than its own size", with a
# 60 px floor so a trivial shift is not worth reporting. Reads crop_boxes(), the SAME
# contributor list the crop itself uses, so the two cannot drift apart.


def _seg_0034___cb(*, Hd: Any = _UNBOUND, M: Any = _UNBOUND, Wd: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 34 (_cb) - body verbatim from the legacy gate() (feature 022)."""
    _cb = crop_boxes(M, scale == "city", meta.get("ftpx", 1), Wd, Hd)
    return _kept(locals(), ('_cb',))


# (outer-most value, that feature's own extent on this axis, what it is) - built with
# LITERAL indices per side so each value stays a float rather than a tuple-union


def _seg_0035___sides(*, _cb: Any = _UNBOUND, b: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 35 (_sides, b) - body verbatim from the legacy gate() (feature 022)."""
    _sides = (
        ("west", [(-b[0], b[1] - b[0], b[4]) for b in _cb]),
        ("east", [(b[1], b[1] - b[0], b[4]) for b in _cb]),
        ("north", [(-b[2], b[3] - b[2], b[4]) for b in _cb]),
        ("south", [(b[3], b[3] - b[2], b[4]) for b in _cb]),
    )
    return _kept(locals(), ('_sides', 'b'))


def _seg_0036___lone() -> dict[str, Any]:
    """Gate segment 36 (_lone) - body verbatim from the legacy gate() (feature 022)."""
    _lone = []  # type: ignore[var-annotated]
    return _kept(locals(), ('_lone',))


def _seg_0037___gap(
    *,
    _gap: Any = _UNBOUND,
    _lone: Any = _UNBOUND,
    _own: Any = _UNBOUND,
    _r: Any = _UNBOUND,
    _side: Any = _UNBOUND,
    _sides: Any = _UNBOUND,
    _vals: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    v: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 37 (_gap, _lone, _own, _r) - body verbatim from the legacy gate() (feature 022)."""
    for _side, _vals in _sides:
        if len(_vals) < 2:
            continue
        _r = sorted(_vals, key=lambda v: -v[0])
        _gap, _own = _r[0][0] - _r[1][0], _r[0][1]
        if _gap > max(60.0, 3.0 * _own) and not meta.get("crop_outlier_ok"):
            _lone.append(f"{_side}: {_r[0][2]} stands {_gap:.0f}px past the next feature in (its own extent is only {_own:.0f}px)")
    return _kept(locals(), ('_gap', '_lone', '_own', '_r', '_side', '_vals'))


def _seg_0038__crop_not_held_open_by_one_feature(*, _lone: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 38 (crop_not_held_open_by_one_feature) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "crop_not_held_open_by_one_feature",
        not _lone,
        f"a single feature is holding the frame open: {_lone} - move it inward and the whole map crops tighter. "
        f"If it genuinely belongs out there (a rule forces it, or the far ground is the point), declare "
        f"meta(crop_outlier_ok=True) with the reason",
    )
    return _kept(locals(), ())


# population is DWELLINGS x ~5, NEVER total buildings: a town/city's shops, government
# offices, flophouses, kura and gate furniture house no one, so counting them as housing
# would inflate the population. Farmhouses + urban dwellings are the only residences.


def _seg_0039__population_consistent_with_housing(
    *,
    M: Any = _UNBOUND,
    URBAN: Any = _UNBOUND,
    _t6: Any = _UNBOUND,
    _wall: Any = _UNBOUND,
    _yp6: Any = _UNBOUND,
    b: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d6: Any = _UNBOUND,
    dwellings: Any = _UNBOUND,
    est: Any = _UNBOUND,
    farm_note: Any = _UNBOUND,
    h: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    inwall_farms: Any = _UNBOUND,
    m6: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    p6: Any = _UNBOUND,
    pop: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    tol: Any = _UNBOUND,
    urban: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 39 (population_consistent_with_housing) - body verbatim from the legacy gate() (feature 022)."""
    if scale in ("town", "city", "capital") and meta.get("population"):
        # a CITY's declared population (~3,000) is its URBAN castes ONLY - servants, laborers, merchants,
        # burakumin, samurai (budgets.md caste tables list ZERO farmers for a city). FARMERS do not count
        # at all: not the surrounding villagers, and not even the unusual IN-WALL agricultural district's
        # farmers - so a city's farmhouses (M["houses"]) are excluded entirely from the figure. A TOWN's
        # depicted farmhouses ARE its (partial) county farmer cohort, so they DO count there.
        # a WALLED city's people shelter INSIDE the rampart, so only in-wall dwellings count toward
        # the declared figure (feature 006). Counting extramural dwellings too let a generator hit
        # the target by spilling houses into the fields while the interior sat half-empty - the exact
        # leak that passed the broken Nagahara (525 in-wall + 35 spilled = 560 ~ target).
        _wall = M.get("wall")
        if scale == "capital":
            # the capital's declared figure covers the WHOLE cohort - in-wall fabric plus the
            # legitimate suburbs (the kashi wharf suburb and the guan-xiang gate wards, the
            # lawful outside categories city_commoner_dwellings_inside_walls names). WHERE an
            # out-wall dwelling may stand is that check's business; the census counts every
            # household the map draws. Cities keep the strict in-wall count (the Tango rule).
            urban = sum(1 for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS)
            # a terrace range is ONE roof over `units` households (021) - count the units
            urban += sum(int(_t6.get("units", 0)) for _t6 in M.get("terraces", []))
            # the yashiki band's walled compounds ARE dwellings (Ranks 8-12 households),
            # recorded as manors rather than buildings; membership via the declared districts
            _yp6 = [d6["poly"] for d6 in M.get("districts", []) if d6.get("rank_band") == "yashiki"]
            urban += sum(1 for m6 in M.get("manors", []) if any(point_in_poly(m6["x"], m6["y"], p6) for p6 in _yp6))
        elif URBAN and _wall:
            urban = sum(1 for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS and point_in_poly(b["x"], b["y"], _wall))
            urban += sum(int(_t6.get("units", 0)) for _t6 in M.get("terraces", []) if point_in_poly(_t6["x"], _t6["y"], _wall))
        else:
            urban = sum(1 for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS)
            urban += sum(int(_t6.get("units", 0)) for _t6 in M.get("terraces", []))
        if URBAN and meta.get("agricultural_district") and M.get("wall"):
            # the unusual agricultural-district city (Tango's canon deviation) HOUSES its in-wall
            # farmers: they are walled residents and count toward the declared figure - the
            # budgets' zero-farmer assumption is precisely what agricultural_district overrides.
            # Surrounding (extramural) farmhouses still do not count.
            inwall_farms = sum(1 for h in houses if point_in_poly(h["x"], h["y"], M["wall"]))
            dwellings = urban + inwall_farms
        elif scale in ("city", "capital"):
            dwellings = urban
        else:
            dwellings = len(houses) + urban
        est = dwellings * HOUSEHOLD
        pop = meta["population"]
        # NO ALLOWANCE (GM 2026-07-26). This was 7%, and the slack is exactly how a map ends up
        # quietly smaller than the figure it declares: Minami was signed off at 486 dwellings against
        # a 520 target and read as green. The GM's rule is direct - "if we have a target population
        # with math indicating a target number of dwellings we must ALWAYS meet that number EXACTLY".
        # A declared population is a promise about what the map CONTAINS, so the arithmetic has to
        # close: population / HOUSEHOLD dwellings, no band. When the ground cannot take them the
        # answer is a bigger wall from the budget, never a smaller declared figure.
        tol = meta.get("population_tol", 0.0)
        farm_note = "" if scale == "city" else "farmhouses + "
        check(
            "population_consistent_with_housing",
            abs(est - pop) <= tol * pop,
            f"{dwellings} dwellings x{HOUSEHOLD} = ~{est} residents, but meta population is {pop} "
            f"(>{tol:.0%} off) - count ONLY dwellings ({farm_note}laborer/servant/burakumin/samurai/merchant), "
            f"never the shops, government offices, flophouses, kura, gate furniture{' or any farmhouses (city farmers are not in the ~3,000)' if scale == 'city' else ''}; "
            f"place enough dwellings to hit the declared figure",
        )
    return _kept(locals(), ('_t6', '_wall', '_yp6', 'b', 'd6', 'dwellings', 'est', 'farm_note', 'h', 'inwall_farms', 'm6', 'p6', 'pop', 'tol', 'urban'))


# COMMONER DWELLINGS SHELTER INSIDE THE WALLS (feature 006). A walled city's ordinary
# population (laborers, artisans, servants, merchants) lived intramurally - the wall exists to
# protect them. Only four categories sat legitimately outside: samurai country estates,
# farmhouses, the riverside wharf suburb, and the gate/approach-road (guan-xiang) market shops.
# So ANY commoner DWELLING outside the wall is the anomaly (it defeats the wall and has no
# economic anchor); hard-zero. Samurai are exempt (their country seats are a legitimate
# extramural category); shops are businesses, not dwellings, so they are not in COMMONER_KINDS.


def _seg_0040_000__wall_p(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.000 (wall_p) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall'):
        wall_p = M["wall"]
    return _kept(locals(), ('wall_p',))


# THE WHARF SUBURB IS THE EXEMPTION THE MESSAGE ALWAYS PROMISED (021): a bank-quay city
# (the kashi form - Shiro Daika) keeps its landing OUTSIDE the wall, and the kashi's own
# brokers and warehouse folk live at the landing; a commoner dwelling within reach of the
# wharf works (a jetty, the quay granary rows) IS that suburb. Cities whose wharf is an
# in-wall dock basin (Minami, Nagahara) have no extramural commoners, so nothing changes
# for them. 300px =~ the drawn wharf suburb's own extent.


def _seg_0040_001___wf_pts(*, M: Any = _UNBOUND, j8: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.001 (_wf_pts, j8) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall'):
        _wf_pts = [(j8["x"], j8["y"]) if isinstance(j8, dict) else (j8[0], j8[1]) for j8 in M.get("jetties", [])]
    return _kept(locals(), ('_wf_pts', 'j8'))


def _seg_0040_002___wf_segs(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.002 (_wf_segs) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall'):
        _wf_segs = []  # type: ignore[var-annotated]  # the haulage shore is wharf ground - its porters' rows are the suburb too;
    return _kept(locals(), ('_wf_segs',))


# measured to towpath SEGMENTS, not vertices (a 2-point towpath left its mid-run porters
# "outside" when the vertices were 350px apart - the point-vs-footprint trap, again)


def _seg_0040_003___tp8(*, M: Any = _UNBOUND, _tp8: Any = _UNBOUND, _tp8p: Any = _UNBOUND, _wf_segs: Any = _UNBOUND, i8: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.003 (_tp8, _tp8p, _wf_segs, i8) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall'):
        for _tp8 in M.get("towpaths", []):
            _tp8p = _tp8.get("poly", _tp8.get("pts", []))
            _wf_segs += [(_tp8p[i8], _tp8p[i8 + 1]) for i8 in range(len(_tp8p) - 1)]
    return _kept(locals(), ('_tp8', '_tp8p', '_wf_segs', 'i8'))


def _seg_0040_004___wf_pts_1(*, M: Any = _UNBOUND, _wf_pts: Any = _UNBOUND, g8: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.004 (_wf_pts, g8) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall'):
        _wf_pts += [(g8["x"], g8["y"]) for g8 in M.get("granaries", []) if isinstance(g8, dict) and "x" in g8]
    return _kept(locals(), ('_wf_pts', 'g8'))


def _seg_0040_005___sa8(
    *,
    M: Any = _UNBOUND,
    _sa8: Any = _UNBOUND,
    _sb8: Any = _UNBOUND,
    _wf_pts: Any = _UNBOUND,
    _wf_segs: Any = _UNBOUND,
    _wx: Any = _UNBOUND,
    _wy: Any = _UNBOUND,
    b: Any = _UNBOUND,
    g9: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    wall_p: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0040.005 (_sa8, _sb8, _wx, _wy) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall'):
        outside_com = [
            (round(b["x"]), round(b["y"]))
            for b in M.get("buildings", [])
            if b.get("kind") in COMMONER_KINDS
            and not point_in_poly(b["x"], b["y"], wall_p)
            and not any(math.hypot(b["x"] - _wx, b["y"] - _wy) <= 300 for _wx, _wy in _wf_pts)
            and not any(seg_dist(b["x"], b["y"], _sa8, _sb8) <= 300 for _sa8, _sb8 in _wf_segs)
            # ...and the guan-xiang gate wards: commoner rows strung along the approach road
            # within reach of a gate are the OTHER lawful outside category (021 research)
            # the guan-xiang wards were LINEAR - Chinese gate suburbs strung up to a li
            # (~1,800 ft) along the approach; 1,500 real ft is the adopted reach (research 021)
            and not any(math.hypot(b["x"] - g9[0], b["y"] - g9[1]) <= 1500.0 / float(meta.get("ftpx", 1) or 1) for g9 in M.get("gates", []))
        ]
    return _kept(locals(), ('_sa8', '_sb8', '_wx', '_wy', 'b', 'g9', 'outside_com'))


def _seg_0040_006__city_commoner_dwellings_inside_walls(*, M: Any = _UNBOUND, check: Any = _UNBOUND, outside_com: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.006 (city_commoner_dwellings_inside_walls) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall'):
        check(
            "city_commoner_dwellings_inside_walls",
            len(outside_com) <= EXTRAMURAL_COMMONER_MAX,
            f"{len(outside_com)} commoner dwelling(s) sit OUTSIDE the walls {sorted(set(outside_com))[:4]} - a walled "
            f"city's commoners shelter inside the rampart; only samurai country estates, farmhouses, the wharf suburb, "
            f"and gate-market shops belong outside. Move these dwellings inside the wall.",
        )
    return _kept(locals(), ())


# DECLARED QUARTERS + PER-QUARTER DENSITY (feature 006). A walled city is a set of zoned
# quarters tiling its interior; density is judged PER QUARTER (residential/mixed against a
# band + a dead-zone guard), civic quarters must actually hold civic ground, and reserve
# ground is capped. This is what a global aggregate could not see: a dense east + empty west
# averages to "fine" (measured: Tango and the broken Nagahara share the same block-density
# median; the difference is WHERE the empty ground sits).


def _seg_0040_007__quarters(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.007 (quarters) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall'):
        quarters = M.get("quarters", [])
    return _kept(locals(), ('quarters',))


# a MALFORMED manifest (a wall or quarter vertex millions of px off the map) must FAIL, not
# hang - the grid sweeps are bounded by sweep_hi so they cannot loop forever, and this flags
# the bad geometry so the validator reports it instead of silently sweeping garbage. A real
# settlement's features lie within one canvas-width of margin of the drawn canvas.


def _seg_0040_008___Wd(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.008 (_Wd) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall'):
        _Wd = meta.get("W") or 3200
    return _kept(locals(), ('_Wd',))


def _seg_0040_009___Hd(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.009 (_Hd) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall'):
        _Hd = meta.get("H") or 2700
    return _kept(locals(), ('_Hd',))


def _seg_0040_010___oob(
    *,
    M: Any = _UNBOUND,
    _Hd: Any = _UNBOUND,
    _Wd: Any = _UNBOUND,
    p: Any = _UNBOUND,
    q: Any = _UNBOUND,
    quarters: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    v: Any = _UNBOUND,
    vx: Any = _UNBOUND,
    vy: Any = _UNBOUND,
    wall_p: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0040.010 (_oob, p, q, v) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall'):
        _oob = [(round(vx), round(vy)) for vx, vy in ([tuple(p) for p in wall_p] + [tuple(v) for q in quarters for v in q["poly"]]) if not (-_Wd <= vx <= 2 * _Wd and -_Hd <= vy <= 2 * _Hd)]
    return _kept(locals(), ('_oob', 'p', 'q', 'v', 'vx', 'vy'))


def _seg_0040_011__city_geometry_within_canvas(*, M: Any = _UNBOUND, _Hd: Any = _UNBOUND, _Wd: Any = _UNBOUND, _oob: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.011 (city_geometry_within_canvas) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall'):
        check(
            "city_geometry_within_canvas",
            not _oob,
            f"wall/quarter vertex(es) far outside the canvas ({_Wd}x{_Hd}): {sorted(set(_oob))[:4]} - a coordinate "
            f"millions of px off the map is malformed input; a valid settlement's geometry lies near the drawn canvas",
        )
    return _kept(locals(), ())


def _seg_0040_012__city_quarters_declared(*, M: Any = _UNBOUND, check: Any = _UNBOUND, quarters: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.012 (city_quarters_declared) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall'):
        check(
            "city_quarters_declared",
            bool(quarters),
            "a walled city must declare its quarters - s.quarter(poly, zone, kind=...) - so density is judged per "
            "quarter, not by a global aggregate a lopsided city can satisfy (a dense half plus an empty half averages fine)",
        )
    return _kept(locals(), ())


def _seg_0040_013__interior_area(*, M: Any = _UNBOUND, quarters: Any = _UNBOUND, scale: Any = _UNBOUND, wall_p: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.013 (interior_area) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters:
        interior_area = poly_area(wall_p)
    return _kept(locals(), ('interior_area',))


def _seg_0040_014__b(*, M: Any = _UNBOUND, b: Any = _UNBOUND, quarters: Any = _UNBOUND, scale: Any = _UNBOUND, wall_p: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.014 (b, dwell_pts) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters:
        dwell_pts = [(b["x"], b["y"]) for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS and point_in_poly(b["x"], b["y"], wall_p)]
    return _kept(locals(), ('b', 'dwell_pts'))


def _seg_0040_015___yq(
    *,
    M: Any = _UNBOUND,
    _yq: Any = _UNBOUND,
    d9: Any = _UNBOUND,
    dwell_pts: Any = _UNBOUND,
    m9: Any = _UNBOUND,
    p9: Any = _UNBOUND,
    quarters: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    t9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0040.015 (_yq, d9, dwell_pts, m9) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters and scale == "capital":
        # capital fabric counts its OTHER dwelling forms (021, same arithmetic as the
        # population check): yashiki-band manors are households, and a terrace range is
        # `units` households at one seat - without them the samurai quarters read empty
        # to the density rule while being fully built.
        _yq = [d9["poly"] for d9 in M.get("districts", []) if d9.get("rank_band") == "yashiki"]
        dwell_pts += [(m9["x"], m9["y"]) for m9 in M.get("manors", []) if any(point_in_poly(m9["x"], m9["y"], p9) for p9 in _yq)]
        for t9 in M.get("terraces", []):
            dwell_pts += [(t9["x"], t9["y"])] * int(t9.get("units", 0))
    return _kept(locals(), ('_yq', 'd9', 'dwell_pts', 'm9', 'p9', 't9'))


def _seg_0040_016___civic(*, M: Any = _UNBOUND, quarters: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.016 (_civic) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters:
        _civic = (
            M.get("ministries", [])
            + M.get("religious", [])
            + M.get("cemeteries", [])
            + M.get("mausoleums", [])
            + M.get("storehouses", [])
            + ([M["governor_mansion"]] if M.get("governor_mansion") else [])
        )
    return _kept(locals(), ('_civic',))


def _seg_0040_017__c(*, M: Any = _UNBOUND, _civic: Any = _UNBOUND, c: Any = _UNBOUND, quarters: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.017 (c, civic_rects) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters:
        civic_rects = [_struct_rect(c) for c in _civic if "w" in c]
    return _kept(locals(), ('c', 'civic_rects'))


# TILING: sweep the wall-plus-quarters bbox once (so a quarter that spills OUTSIDE the
# wall is sampled too) - quarters must cover the interior (>=85%), not overlap (<=5%),
# and not spill outside the wall (<=3% of interior-equivalent cells).


def _seg_0040_018__p(*, M: Any = _UNBOUND, p: Any = _UNBOUND, q: Any = _UNBOUND, quarters: Any = _UNBOUND, scale: Any = _UNBOUND, v: Any = _UNBOUND, wall_p: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.018 (p, q, v, wxs) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters:
        wxs = [p[0] for p in wall_p] + [v[0] for q in quarters for v in q["poly"]]
    return _kept(locals(), ('p', 'q', 'v', 'wxs'))


def _seg_0040_019__p_1(*, M: Any = _UNBOUND, p: Any = _UNBOUND, q: Any = _UNBOUND, quarters: Any = _UNBOUND, scale: Any = _UNBOUND, v: Any = _UNBOUND, wall_p: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.019 (p, q, v, wys) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters:
        wys = [p[1] for p in wall_p] + [v[1] for q in quarters for v in q["poly"]]
    return _kept(locals(), ('p', 'q', 'v', 'wys'))


def _seg_0040_020__interior_cells(*, M: Any = _UNBOUND, quarters: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.020 (interior_cells, overlapped, spill_cells, uncovered) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters:
        interior_cells = uncovered = overlapped = spill_cells = 0
    return _kept(locals(), ('interior_cells', 'overlapped', 'spill_cells', 'uncovered'))


def _seg_0040_021___hx(*, M: Any = _UNBOUND, quarters: Any = _UNBOUND, scale: Any = _UNBOUND, wxs: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.021 (_hx) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters:
        _hx = sweep_hi(min(wxs), max(wxs), 40)  # bounded so a malformed vertex cannot hang the sweep
    return _kept(locals(), ('_hx',))


def _seg_0040_022___hy(*, M: Any = _UNBOUND, quarters: Any = _UNBOUND, scale: Any = _UNBOUND, wys: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.022 (_hy) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters:
        _hy = sweep_hi(min(wys), max(wys), 40)
    return _kept(locals(), ('_hy',))


def _seg_0040_023__gx(*, M: Any = _UNBOUND, quarters: Any = _UNBOUND, scale: Any = _UNBOUND, wxs: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.023 (gx) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters:
        gx = min(wxs)
    return _kept(locals(), ('gx',))


def _seg_0040_024__gx_1(
    *,
    M: Any = _UNBOUND,
    _hx: Any = _UNBOUND,
    _hy: Any = _UNBOUND,
    gx: Any = _UNBOUND,
    gy: Any = _UNBOUND,
    interior_cells: Any = _UNBOUND,
    n_in: Any = _UNBOUND,
    overlapped: Any = _UNBOUND,
    q: Any = _UNBOUND,
    quarters: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    spill_cells: Any = _UNBOUND,
    uncovered: Any = _UNBOUND,
    wall_p: Any = _UNBOUND,
    wys: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0040.024 (gx, gy, interior_cells, n_in) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters:
        while gx <= _hx:
            gy = min(wys)
            while gy <= _hy:
                n_in = sum(1 for q in quarters if point_in_poly(gx, gy, q["poly"]))
                if point_in_poly(gx, gy, wall_p):
                    interior_cells += 1
                    if n_in == 0:
                        uncovered += 1
                    elif n_in > 1:
                        overlapped += 1
                elif n_in >= 1:
                    spill_cells += 1
                gy += 40
            gx += 40
    return _kept(locals(), ('gx', 'gy', 'interior_cells', 'n_in', 'overlapped', 'q', 'spill_cells', 'uncovered'))


def _seg_0040_025__ic(*, M: Any = _UNBOUND, interior_cells: Any = _UNBOUND, quarters: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.025 (ic) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters:
        ic = max(interior_cells, 1)
    return _kept(locals(), ('ic',))


def _seg_0040_026__covered(*, M: Any = _UNBOUND, ic: Any = _UNBOUND, quarters: Any = _UNBOUND, scale: Any = _UNBOUND, uncovered: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.026 (covered) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters:
        covered = 1 - uncovered / ic
    return _kept(locals(), ('covered',))


def _seg_0040_027__city_quarters_tile_interior(
    *, M: Any = _UNBOUND, check: Any = _UNBOUND, covered: Any = _UNBOUND, ic: Any = _UNBOUND, overlapped: Any = _UNBOUND, quarters: Any = _UNBOUND, scale: Any = _UNBOUND, spill_cells: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0040.027 (city_quarters_tile_interior) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters:
        check(
            "city_quarters_tile_interior",
            covered >= 0.85 and overlapped / ic <= 0.05 and spill_cells / ic <= 0.03,
            f"declared quarters must tile the walled interior without overlap or spill - covered {covered:.0%} "
            f"(need >=85%), overlapped {overlapped / ic:.0%} (<=5%), outside-wall {spill_cells / ic:.0%} (<=3%)",
        )
    return _kept(locals(), ())


# PER-QUARTER DENSITY + DEAD ZONE (residential + mixed quarters)


def _seg_0040_028__thin_q(*, M: Any = _UNBOUND, quarters: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.028 (thin_q) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters:
        thin_q = []  # type: ignore[var-annotated]
    return _kept(locals(), ('thin_q',))


def _seg_0040_029__civic_in_q(
    *,
    M: Any = _UNBOUND,
    civic_in_q: Any = _UNBOUND,
    civic_rects: Any = _UNBOUND,
    dens: Any = _UNBOUND,
    dwell_pts: Any = _UNBOUND,
    eff_area: Any = _UNBOUND,
    nm: Any = _UNBOUND,
    p: Any = _UNBOUND,
    q: Any = _UNBOUND,
    qarea: Any = _UNBOUND,
    qd: Any = _UNBOUND,
    qpoly: Any = _UNBOUND,
    quarters: Any = _UNBOUND,
    r: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    thin_q: Any = _UNBOUND,
    w: Any = _UNBOUND,
    x: Any = _UNBOUND,
    y: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0040.029 (civic_in_q, dens, eff_area, nm) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters:
        for q in quarters:
            if q.get("zone") not in ("residential", "mixed"):
                continue
            qpoly = q["poly"]
            qarea = poly_area(qpoly)
            if qarea <= 0:
                continue
            qd = [(x, y) for x, y in dwell_pts if point_in_poly(x, y, qpoly)]
            # density is measured over HOUSING-AVAILABLE ground: subtract any civic compound
            # footprint sitting in the quarter (a government ward or a temple in a merchant
            # district eats area that was never going to be housing), so a mixed quarter is not
            # wrongly flagged under-built for the ground its compounds occupy.
            civic_in_q = sum(r["w"] * r["h"] for r in civic_rects if point_in_poly(r["x"], r["y"], qpoly))
            eff_area = max(qarea - civic_in_q, 1.0)
            dens = len(qd) / eff_area
            nm = q.get("name") or f"quarter@({round(sum(p[0] for p in qpoly) / len(qpoly))},{round(sum(p[1] for p in qpoly) / len(qpoly))})"
            if dens < QUARTER_DENSITY_FLOOR:
                thin_q.append((nm, f"{len(qd)} dwellings, density {dens * 1000:.2f}/1000px^2 < floor {QUARTER_DENSITY_FLOOR * 1000:.2f} (under-built)"))
            elif dens > QUARTER_DENSITY_CEIL:
                thin_q.append((nm, f"density {dens * 1000:.2f}/1000px^2 > ceil {QUARTER_DENSITY_CEIL * 1000:.2f} (implausibly crammed)"))
            elif (
                q.get("zone") == "residential"
                and largest_empty_gap(
                    qpoly, qd + [(w["x"], w["y"]) for w in M.get("wells", []) if point_in_poly(w["x"], w["y"], qpoly)], occupied=[r for r in civic_rects if point_in_poly(r["x"], r["y"], qpoly)]
                )
                > DEAD_ZONE_MAX
            ):
                # the dead-zone guard applies to PURE residential quarters (uniform housing, no
                # empty blocks); a MIXED quarter legitimately holds a civic forecourt/plaza, so it
                # is judged on the density AVERAGE only. An all-empty region declared to dodge this
                # still fails: as residential it fires here, as civic it fires city_civic_quarter,
                # as mixed its average density is too low.
                thin_q.append((nm, f"dead zone: an empty pocket wider than a firebreak ({DEAD_ZONE_MAX:.0f}px) inside a residential quarter"))
    return _kept(locals(), ('civic_in_q', 'dens', 'eff_area', 'nm', 'p', 'q', 'qarea', 'qd', 'qpoly', 'r', 'thin_q', 'w', 'x', 'y'))


def _seg_0040_030__city_residential_quarters_dense_enough(*, M: Any = _UNBOUND, check: Any = _UNBOUND, quarters: Any = _UNBOUND, scale: Any = _UNBOUND, thin_q: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.030 (city_residential_quarters_dense_enough) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters:
        check(
            "city_residential_quarters_dense_enough",
            not thin_q,
            f"residential/mixed quarter(s) not evenly built up (per-quarter density band "
            f"[{QUARTER_DENSITY_FLOOR * 1000:.2f}, {QUARTER_DENSITY_CEIL * 1000:.2f}]/1000px^2 + no dead zone): {thin_q[:4]}",
        )
    return _kept(locals(), ())


# CIVIC quarters must actually hold civic ground (not be emptiness labeled civic)


def _seg_0040_031__open_civic(*, M: Any = _UNBOUND, quarters: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.031 (open_civic) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters:
        open_civic = []  # type: ignore[var-annotated]
    return _kept(locals(), ('open_civic',))


def _seg_0040_032___civ_tol(
    *,
    M: Any = _UNBOUND,
    _civ_tol: Any = _UNBOUND,
    built: Any = _UNBOUND,
    civic_rects: Any = _UNBOUND,
    nm: Any = _UNBOUND,
    open_civic: Any = _UNBOUND,
    open_share: Any = _UNBOUND,
    q: Any = _UNBOUND,
    qarea: Any = _UNBOUND,
    qpoly: Any = _UNBOUND,
    quarters: Any = _UNBOUND,
    r: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0040.032 (_civ_tol, built, nm, open_civic) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters:
        for q in quarters:
            if q.get("zone") != "civic":
                continue
            qpoly = q["poly"]
            qarea = poly_area(qpoly)
            if qarea <= 0:
                continue
            built = sum(r["w"] * r["h"] for r in civic_rects if point_in_poly(r["x"], r["y"], qpoly))
            open_share = 1 - min(built / qarea, 1.0)
            # A CAPITAL'S civic band is CEREMONIAL ground (research 021): Beijing's Corridor
            # of a Thousand Steps was a vast open axis flanked by files of offices, and the
            # jokamachi ote-suji keeps the same breadth with its 14px office standoffs - so
            # the capital tolerates 90% open where a provincial yamen precinct keeps 70%.
            _civ_tol = 0.90 if scale == "capital" else CIVIC_OPEN_TOL
            if open_share > _civ_tol:
                nm = q.get("name") or "civic quarter"
                open_civic.append((nm, f"{open_share:.0%} open > {_civ_tol:.0%}; holds little civic building"))
    return _kept(locals(), ('_civ_tol', 'built', 'nm', 'open_civic', 'open_share', 'q', 'qarea', 'qpoly', 'r'))


def _seg_0040_033__city_civic_quarter_not_mostly_open(*, M: Any = _UNBOUND, check: Any = _UNBOUND, open_civic: Any = _UNBOUND, quarters: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.033 (city_civic_quarter_not_mostly_open) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters:
        check(
            "city_civic_quarter_not_mostly_open",
            not open_civic,
            f"civic quarter(s) that are mostly empty rather than a real precinct - a yamen/temple precinct is majority-open but STRUCTURED (it holds its compounds); flag: {open_civic[:3]}",
        )
    return _kept(locals(), ())


# RESERVE ground capped


def _seg_0040_034__q(*, M: Any = _UNBOUND, q: Any = _UNBOUND, quarters: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.034 (q, reserve_area) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters:
        reserve_area = sum(poly_area(q["poly"]) for q in quarters if q.get("zone") == "reserve")
    return _kept(locals(), ('q', 'reserve_area'))


def _seg_0040_035__rfrac(*, M: Any = _UNBOUND, interior_area: Any = _UNBOUND, quarters: Any = _UNBOUND, reserve_area: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.035 (rfrac) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters:
        rfrac = reserve_area / max(interior_area, 1)
    return _kept(locals(), ('rfrac',))


def _seg_0040_036__city_reserve_within_cap(*, M: Any = _UNBOUND, check: Any = _UNBOUND, quarters: Any = _UNBOUND, rfrac: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0040.036 (city_reserve_within_cap) - body verbatim from _seg_0040__city_commoner_dwellings_inside_walls (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('city', 'capital') and M.get('wall') and quarters:
        check(
            "city_reserve_within_cap",
            rfrac <= RESERVE_CAP_FRAC,
            f"declared reserve ground is {rfrac:.0%} of the interior, over the {RESERVE_CAP_FRAC:.0%} cap - "
            f"a wall enclosing this much deliberately-open ground is too big for the residential program (shrink it, "
            f"or convert reserve to housing)",
        )
    return _kept(locals(), ())


# IS THE WALL THE RIGHT SIZE FOR THE POPULATION? A space-budget analysis, so "the wall is
# too big / too small" becomes a first-class, automated judgment instead of trial and error.
# city_capacity() grid-samples the interior, subtracts the fixed overhead (government, temples,
# wharf, gates, water, trunk roads + ring road + berm, committed fields), and asks whether the
# residential-capable ground - at a well-packed quarter's canonical density - can hold the
# target. TOO_SMALL / TOO_BIG are WALL faults (resize by the suggested scale); UNDERPACKED means
# the wall is right but the placement is sparse (densify - population_consistent catches that
# separately). See settlements.md "Sizing the wall to the population".
# ...CITY ONLY: a capital's wall is an OUTPUT of plan_capital (capital_wall_matches_budget +
# capital_interior_slack_in_band judge it against the declared program, castle included), and
# this generic capacity model does not know a castle takes ~40% of the interior - it reads the
# keep's ground as residential-capable and demands the wall shrink (GM 2026-08-10).


def _seg_0041__city_wall_sized_to_population(*, M: Any = _UNBOUND, cap: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 41 (city_wall_sized_to_population) - body verbatim from the legacy gate() (feature 022)."""
    if scale == "city" and meta.get("population"):
        cap = city_capacity(M)
        if cap:
            check(
                "city_wall_sized_to_population",
                cap["verdict"] not in ("enlarge", "shrink"),
                f"the wall wants to {cap['verdict']} for a population of {meta['population']} "
                f"(target {cap['target_dwellings']} dwellings; the ring holds ~{cap['inherent_capacity']} well-packed, "
                f"reserve fraction {cap['reserve_frac']}) - resize the wall by the suggested scale x{cap['suggested_wall_scale']} "
                f"(>1 enlarge, <1 shrink), then re-run; do NOT grind placements against a mis-sized wall",
            )
    return _kept(locals(), ('cap',))


# THE WALL MATCHES THE DECLARED SPACE BUDGET (feature 009). Budget-first is the city
# workflow: the gen computes citybudget.plan_city(...) BEFORE drawing anything, takes the
# wall from budget.wall, and records the promise at meta.budget - this check holds the
# drawn map to it. Enclosing MORE ground than the budget justifies is the empty-space
# defect (the pre-feature Nagahara read fully green while ~17% of its interior was
# unaccounted open ground); enclosing less starves the program. Open ground is credited
# only as itemized budget lines (reserve/agri/extras) - never as ambient slack.
# every gate STABLES carries its drawn beaten-earth YARD (GM 2026-07-22): the open ground around a gate
# stables is deliberate (a wagon-train marshalling yard - carts parked, oxen unyoked and tethered at
# rails, teamsters waiting), but left as blank parchment it read as forgotten emptiness. s._stable_yard
# fills it with a feathered scatter (scuff, straw, hitching rails, trough, dung
# heaps); this gates that no stables reverts to a blank yard. Each yard links to its stables via `of`.


def _seg_0042__stables_have_yards(
    *, M: Any = _UNBOUND, URBAN: Any = _UNBOUND, _yardless: Any = _UNBOUND, _yards: Any = _UNBOUND, b: Any = _UNBOUND, check: Any = _UNBOUND, yd: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 42 (stables_have_yards) - body verbatim from the legacy gate() (feature 022)."""
    if URBAN:
        _yards = M.get("stable_yards", [])
        _yardless = [
            (round(b["x"]), round(b["y"])) for b in M.get("buildings", []) if b.get("kind") == "stables" and not any(abs(yd["of"][0] - b["x"]) < 1 and abs(yd["of"][1] - b["y"]) < 1 for yd in _yards)
        ]
        check(
            "stables_have_yards",
            not _yardless,
            f"gate stables with no drawn working yard at {_yardless[:3]} - the open ground around a gate stables is a deliberate wagon-train marshalling yard (hitching rails, littered beaten earth), not blank parchment; s.stables(...) draws it (yard=True; settlements.md 'Stable yard')",
        )
    return _kept(locals(), ('_yardless', '_yards', 'b', 'yd'))


# STABLE-YARD TROUGHS SIT BESIDE A WELL (GM 2026-07-23: "so that the water doesn't need to be
# carried a considerable distance"). The watering point works by RELAY at a fixed draw-point -
# a wagon-train drinks 300-600 gal in a session, poured by bucket straight from the wellhead
# into the troughs (settlements.md 'Stable yard' watering) - so the cluster must hug a
# wellhead: placement offsets it by the wellhead edge + half a trough + a step (~24 real ft
# center-to-center at city scale); 40 real ft is that worst case + slack, and any genuine
# carry (the pre-fix Nagahara yards sat 100/241 ft out) blows far past it. A yard with no
# well in reach digs its OWN courtyard well (the caravanserai / yizhan post-yard form), so
# "no well nearby" is never a valid layout; a yard whose trough cluster went unrecorded
# (troughs > 0 without troughs_at) fails too - the anchor is part of the contract. Not
# scale-gated: wherever a stable yard records troughs, its water is drawn at a well.


def _seg_0043___tr_ftpx(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 43 (_tr_ftpx) - body verbatim from the legacy gate() (feature 022)."""
    _tr_ftpx = float(meta.get("ftpx") or 3.0)
    return _kept(locals(), ('_tr_ftpx',))


def _seg_0044___tr_wells(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 44 (_tr_wells) - body verbatim from the legacy gate() (feature 022)."""
    _tr_wells = M.get("wells", [])
    return _kept(locals(), ('_tr_wells',))


def _seg_0045___tr_far() -> dict[str, Any]:
    """Gate segment 45 (_tr_far) - body verbatim from the legacy gate() (feature 022)."""
    _tr_far = []  # type: ignore[var-annotated]
    return _kept(locals(), ('_tr_far',))


def _seg_0046___tr_at(
    *, M: Any = _UNBOUND, _tr_at: Any = _UNBOUND, _tr_far: Any = _UNBOUND, _tr_ftpx: Any = _UNBOUND, _tr_wells: Any = _UNBOUND, _tr_yd: Any = _UNBOUND, w: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 46 (_tr_at, _tr_far, _tr_yd, w) - body verbatim from the legacy gate() (feature 022)."""
    for _tr_yd in M.get("stable_yards", []):
        if not _tr_yd.get("troughs"):
            continue
        _tr_at = _tr_yd.get("troughs_at")
        if not _tr_at or not _tr_wells or min(math.hypot(w["x"] - _tr_at[0], w["y"] - _tr_at[1]) for w in _tr_wells) > 40.0 / _tr_ftpx:
            _tr_far.append((round(_tr_yd["x"]), round(_tr_yd["y"])))
    return _kept(locals(), ('_tr_at', '_tr_far', '_tr_yd', 'w'))


def _seg_0047__stable_troughs_beside_well(*, _tr_far: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 47 (stable_troughs_beside_well) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "stable_troughs_beside_well",
        not _tr_far,
        f"stable-yard trough clusters not beside a well at {_tr_far[:3]} - animals are watered by relay at a fixed draw-point, the bucket poured straight from the wellhead, so the cluster hugs a well within ~40 real ft; a yard with no well in reach digs its own courtyard well (s._stable_yard does both; settlements.md 'Stable yard' watering)",
    )
    return _kept(locals(), ())


# THE FARRIER'S FORGE STANDS BESIDE A STABLES, AND KEEPS ITS FIRE GAP (GM 2026-07-25, the
# iron-horseshoe decision; full grounding in settlements.md "TRADE WORKS" -> FARRIERY). Rokugan
# shoes horses in IRON where Edo Japan used woven straw, but that changes an ordinary smith's
# REPERTOIRE, not his premises - a town kaji-ya still fits the generic shop glyph. A drawn
# farrier is therefore only correct where horses CONCENTRATE, which in map terms is the
# caravan/relay stable yard: a shoeing forge on a random street corner is the European
# coaching-inn image the trade research warned about, not a Rokugani seat. And it must NOT abut
# the stall range - an open forge against hay and timber is the fire a yard does not survive,
# so real yards kept the smithy across the ground. The gap anchor is buildings.md's ~6-8 ft
# wooden-service fire gap; the measure runs from the WHOLE recorded footprint (shed + apron),
# which is deliberately conservative, since the shed sits at the apron's far end.


def _seg_0048___fr_all(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 48 (_fr_all) - body verbatim from the legacy gate() (feature 022)."""
    _fr_all = M.get("farriers", [])
    return _kept(locals(), ('_fr_all',))


def _seg_0049___fr_ftpx(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 49 (_fr_ftpx) - body verbatim from the legacy gate() (feature 022)."""
    _fr_ftpx = float(meta.get("ftpx") or 3.0)
    return _kept(locals(), ('_fr_ftpx',))


def _seg_0050___fr_stables(*, M: Any = _UNBOUND, b: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 50 (_fr_stables, b) - body verbatim from the legacy gate() (feature 022)."""
    _fr_stables = [b for b in M.get("buildings", []) if b.get("kind") == "stables"]
    return _kept(locals(), ('_fr_stables', 'b'))


def _seg_0051___fr_poly(*, o_: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 51 (_fr_poly) - body verbatim from the legacy gate() (feature 022)."""

    def _fr_poly(o_: dict[str, Any]) -> list[tuple[float, float]]:
        return rect_corners(_struct_rect(o_))

    return _kept(locals(), ('_fr_poly',))


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
