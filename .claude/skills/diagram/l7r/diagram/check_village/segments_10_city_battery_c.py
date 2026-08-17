"""Gate segments (city battery c) - bodies verbatim from check_village.py (feature 024 package split; registry order preserved)."""

import math
from collections.abc import Sequence
from typing import Any

from .common_01_geometry import Pt, point_in_poly, poly_dist, seg_closest, seg_dist, segments_cross
from .common_02_overlap_policy import footprint_on_line, in_ellipse
from .common_03_capacity import _UNBOUND, DWELLING_KINDS, _kept, empty_street_runs

# internal streets must not run THROUGH the civic compounds (ministries, governor, temples,
# gate furniture) any more than they may through ordinary buildings


def _seg_0563_252__civic_3(*, M: Any = _UNBOUND, gov: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.252 (civic) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        civic = M.get("ministries", []) + M.get("religious", []) + M.get("inspection_stations", []) + ([gov] if gov else [])
    return _kept(locals(), ('civic',))


def _seg_0563_253__c_1(
    *, M: Any = _UNBOUND, c: Any = _UNBOUND, civic: Any = _UNBOUND, meta: Any = _UNBOUND, rect_corners_xywh: Any = _UNBOUND, scale: Any = _UNBOUND, st: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.253 (c, civic_on_street, st) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        civic_on_street = [
            c.get("name") or c.get("label") or "compound" for st in M.get("town_streets", []) for c in civic if footprint_on_line(rect_corners_xywh(c, 0), st["pts"], st.get("w", 24) / 2 + 2)
        ]
    return _kept(locals(), ('c', 'civic_on_street', 'st'))


def _seg_0563_254__city_civic_clear_of_streets(*, check: Any = _UNBOUND, civic_on_street: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.254 (city_civic_clear_of_streets) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_civic_clear_of_streets", not civic_on_street, f"city street(s) running through a civic compound: {civic_on_street}")
    return _kept(locals(), ())


# ZONE / NEIGHBORHOOD labels must sit WITH the cluster they name: ENTIRELY on the same side
# of the city wall as that cluster, AMONG its buildings, and not floating over a foreign field.
# A label over the moat, a neighboring compound, or a paddy misleads the reader about what it
# names (the "laborer neighborhoods" label drifted outside the wall, "samurai neighborhood"
# sat over a ministry, "burakumin neighborhood" sat over a field).


def _seg_0563_255__subject_of(
    *,
    M: Any = _UNBOUND,
    b: Any = _UNBOUND,
    c: Any = _UNBOUND,
    f: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    inwall: Any = _UNBOUND,
    key: Any = _UNBOUND,
    m: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    r: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    t: Any = _UNBOUND,
    txt: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.255 (subject_of) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):

        def subject_of(txt: str) -> tuple[list[tuple[float, float]], float, bool]:
            t = txt.lower()
            if "estate" in t:
                return [(m["x"], m["y"]) for m in M.get("manors", [])], 230, True
            if "agricultur" in t:  # the in-wall agricultural district, NOT the extramural farmland
                return [c for c in (((f["bbox"][0] + f["bbox"][2]) / 2, (f["bbox"][1] + f["bbox"][3]) / 2) for f in fields) if inwall(*c)], 260, True
            if "temple" in t:
                return [(r["x"], r["y"]) for r in M.get("religious", [])], 230, True
            for key, kinds in (
                ("samurai", {"samurai", "samurai_large"}),
                ("laborer", {"laborer", "laborer_large"}),
                ("burakumin", {"burakumin"}),
                ("merchant", {"merchant", "merchant_house", "merchant_large"}),
            ):
                if key in t:
                    return [(b["x"], b["y"]) for b in M.get("buildings", []) if b.get("kind") in kinds], 130, False
            return [], 0, True

    return _kept(locals(), ('subject_of',))


def _seg_0563_256__bad_lab(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.256 (bad_lab) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        bad_lab = []  # type: ignore[var-annotated]
    return _kept(locals(), ('bad_lab',))


def _seg_0563_257___z(
    *,
    M: Any = _UNBOUND,
    area_subj: Any = _UNBOUND,
    bad_lab: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    f: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    inwall: Any = _UNBOUND,
    lab: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    pts: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    reach: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    subj_in: Any = _UNBOUND,
    subject_of: Any = _UNBOUND,
    txt: Any = _UNBOUND,
    x0: Any = _UNBOUND,
    x1: Any = _UNBOUND,
    y0: Any = _UNBOUND,
    y1: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.257 (_z, area_subj, bad_lab, cx) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for lab in M.get("labels", []):
            if len(lab) <= 5 or not (lab[5].lower().endswith(("neighborhood", "neighborhoods", "district")) or "estates" in lab[5].lower()):
                continue
            x0, y0, x1, y1, _z, txt = lab[:6]
            pts, reach, area_subj = subject_of(txt)
            if not pts:
                continue  # nothing of that kind drawn - can't verify
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            subj_in = sum(1 for px, py in pts if inwall(px, py)) * 2 >= len(pts)
            if not all(inwall(px, py) == subj_in for px, py in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))):
                bad_lab.append(f"{txt!r} not entirely {'inside' if subj_in else 'outside'} the wall (its cluster is)")
            elif min(math.hypot(px - cx, py - cy) for px, py in pts) > reach:
                bad_lab.append(f"{txt!r} sits >{reach}px from any of its buildings - place it among them")
            elif not area_subj and any(point_in_poly(cx, cy, f["outline"]) for f in fields):
                bad_lab.append(f"{txt!r} floats over a farm field, not its own houses")
    return _kept(locals(), ('_z', 'area_subj', 'bad_lab', 'cx', 'cy', 'f', 'lab', 'pts', 'px', 'py', 'reach', 'subj_in', 'txt', 'x0', 'x1', 'y0', 'y1'))


def _seg_0563_258__city_labels_placed_with_subject(*, bad_lab: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.258 (city_labels_placed_with_subject) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_labels_placed_with_subject", not bad_lab, f"neighborhood/zone label(s) misplaced relative to what they name: {bad_lab}")
    return _kept(locals(), ())


# the surrounding farmland: every OUTSIDE field (even off-edge) has farmhouses, and the
# fields sit close to the city (cities grow up around fertile land)


def _seg_0563_259__f_1(*, f: Any = _UNBOUND, fields: Any = _UNBOUND, inwall: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.259 (f, out_fields) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        out_fields = [f for f in fields if not inwall((f["bbox"][0] + f["bbox"][2]) / 2, (f["bbox"][1] + f["bbox"][3]) / 2)]
    return _kept(locals(), ('f', 'out_fields'))


def _seg_0563_260__f_2(*, ADJ: Any = _UNBOUND, f: Any = _UNBOUND, h: Any = _UNBOUND, houses: Any = _UNBOUND, meta: Any = _UNBOUND, out_fields: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.260 (f, h, no_farm) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        no_farm = [f["name"] for f in out_fields if sum(1 for h in houses if poly_dist(h["x"], h["y"], f["outline"]) <= ADJ) < 2]
    return _kept(locals(), ('f', 'h', 'no_farm'))


def _seg_0563_261__city_outside_fields_have_farmhouses(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, no_farm: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.261 (city_outside_fields_have_farmhouses) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_outside_fields_have_farmhouses", not no_farm, f"outside field(s) with < 2 farmhouses (even off-edge fields are worked by nearby villagers): {no_farm}")
    return _kept(locals(), ())


def _seg_0563_262__f_3(*, f: Any = _UNBOUND, meta: Any = _UNBOUND, out_fields: Any = _UNBOUND, p: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.262 (f, far, p) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        far = [f["name"] for f in out_fields if len(w) >= 3 and min(poly_dist(p[0], p[1], w) for p in f["outline"]) > 520]
    return _kept(locals(), ('f', 'far', 'p'))


def _seg_0563_263__city_fields_close_to_city(*, check: Any = _UNBOUND, far: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.263 (city_fields_close_to_city) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_fields_close_to_city", not far, f"outside field(s) too far from the city (cities grow up around fertile land, fields stay close): {far}")
    return _kept(locals(), ())


# a MOATED city irrigates several large fields from the moat


def _seg_0563_264__city_moat_irrigates_fields(
    *,
    M: Any = _UNBOUND,
    big_out: Any = _UNBOUND,
    c: Any = _UNBOUND,
    chans: Any = _UNBOUND,
    check: Any = _UNBOUND,
    e: Any = _UNBOUND,
    ends: Any = _UNBOUND,
    f: Any = _UNBOUND,
    fed: Any = _UNBOUND,
    fo: Any = _UNBOUND,
    i: Any = _UNBOUND,
    in_field: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    moat: Any = _UNBOUND,
    moat_fed: Any = _UNBOUND,
    out_fields: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.264 (city_moat_irrigates_fields) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and moat:
        chans = M.get("channels", [])
        big_out = [f for f in out_fields if (f["bbox"][2] - f["bbox"][0]) * (f["bbox"][3] - f["bbox"][1]) > 55000]

        def moat_fed(fo: dict[str, Any]) -> bool:
            for c in chans:
                ends = (c["poly"][0], c["poly"][-1])
                near_moat = any(any(seg_dist(e[0], e[1], moat[i], moat[i + 1]) < 34 for i in range(len(moat) - 1)) for e in ends)
                in_field = any(point_in_poly(e[0], e[1], fo["outline"]) for e in ends)
                if near_moat and in_field:
                    return True
            return False

        fed = [f["name"] for f in big_out if moat_fed(f)]
        # CAPITAL-INVERTED (021): a capital walls its farms out and is fed BY the river
        # (the wharf/granary doctrine), and its sheet frames only the city and suburbs -
        # the domain's farmland is off-sheet, so this asks for ground the map never shows
        if scale == "city":
            check("city_moat_irrigates_fields", len(fed) >= 3, f"{len(fed)} large outside fields fed by moat irrigation, expected >= 3 (a moated city irrigates its farmland from the moat)")
    return _kept(locals(), ('big_out', 'chans', 'f', 'fed', 'moat_fed'))


# a gate market (guan-xiang) OUTSIDE EVERY MAIN-ROAD gate (GM decision 2026-07-22,
# flophouse-research.md): the extramural gate-suburb formed along the road at each
# trafficked gate - Beijing's gates all carried one, varying in scale (大关厢 vs small).
# `M["gates"]` holds only the MAIN (road/river-route) gates, so iterating it IS "every
# main-road gate": a purely military SALLY gate opens onto empty field with no traffic
# and carries no market, so it is NOT recorded in `gates` (it would live in its own
# structure if/when the sally-gate knob is added). Mirrors city_flophouse_outside_each_gate.
# FLOOR RAISED 3 -> 6 (GM 2026-07-24): the researched guan-xiang ran 10-40 structures
# per trafficked gate (Beijing's 大关厢 the high end); our belt is a SLICE like the
# samurai estates and the farmland - the drawn shops string along the approach road and
# the outermost may be CUT by the frame, the truncation itself saying "more beyond the
# map". >= 6 shown per gate keeps the slice reading like a suburb instead of a shed row.


def _seg_0563_265__b_13(*, M: Any = _UNBOUND, b: Any = _UNBOUND, inwall: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.265 (b, biz_out) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        biz_out = [b for b in M.get("buildings", []) if b.get("kind") in ("shop", "merchant") and not inwall(b["x"], b["y"])]
    return _kept(locals(), ('b', 'biz_out'))


def _seg_0563_266__b_14(*, b: Any = _UNBOUND, biz_out: Any = _UNBOUND, g: Any = _UNBOUND, gates: Any = _UNBOUND, i: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.266 (b, g, gates_wo_market, i) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        gates_wo_market = [i for i, g in enumerate(gates) if sum(1 for b in biz_out if math.hypot(b["x"] - g[0], b["y"] - g[1]) <= 520) < 6]
    return _kept(locals(), ('b', 'g', 'gates_wo_market', 'i'))


def _seg_0563_267__city_has_gate_market(*, check: Any = _UNBOUND, gates_wo_market: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.267 (city_has_gate_market) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):
            check(
                "city_has_gate_market",
                not gates_wo_market,
                f"main-road gate(s) with a too-thin gate market (guan-xiang): {gates_wo_market} - a market suburb forms outside EVERY main-road city gate (research: 10-40 structures per trafficked gate; the map draws a >= 6-shop slice within ~520px, outermost may run off the frame; a sally gate, being traffic-free, is exempt and not in M['gates'])",
            )
    return _kept(locals(), ())


# TRADE WORKS (GM 2026-07-24; settlements.md "TRADE WORKS" - the trades whose premises
# outgrow the generic shop glyph are first-class features; the long tail of trades,
# including the ordinary SMITH, stays in the shop rows - Rokugan DOES shoe horses in
# iron, but that changes his repertoire, not his footprint, so only a horse
# CONCENTRATION earns a drawn farrier). Every provincial city keeps: >= 1 BREWERY
# in-wall (the town's
# largest commercial building; sake/miso/soy; draws its own well); >= 1 DYE WORKS
# whose drying/rinsing yard sits ON WATER (a stream/channel/canal, the pond, or the
# moat - dyers need vat-fill and rinsing water, NOT bulk water transport, so a
# landlocked city keeps dyers too, per the GM); >= 1 OIL PRESS; >= 1 PAWNSHOP (a
# shopfront with a walled kura court); >= 1 BATHHOUSE (China-first: commercial baths
# attested from the Song). A KILN stands strictly OUTSIDE the walls (fire law +
# smoke); a RIVER-PORT city (meta river_port) also keeps >= 1 LUMBER YARD on the
# bank - timber moves by water at scale, so a landlocked city has none.


def _seg_0563_268___tw_brews(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.268 (_tw_brews) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        _tw_brews = M.get("breweries", [])
    return _kept(locals(), ('_tw_brews',))


def _seg_0563_269__city_has_brewery(*, _tw_brews: Any = _UNBOUND, b_: Any = _UNBOUND, check: Any = _UNBOUND, inwall: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.269 (city_has_brewery) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):
            check(
                "city_has_brewery",
                any(inwall(b_["x"], b_["y"]) for b_ in _tw_brews),
                f"{len(_tw_brews)} brewery compound(s) in-wall - every provincial city keeps at least one sake/miso/soy brewery (s.brewery: vat hall + shopfront + rice kura + its own well; the town's largest commercial building)",
            )
    return _kept(locals(), ('b_',))


def _seg_0563_270___tw_water(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.270 (_tw_water) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        _tw_water: list[tuple[list[Any], float]] = []  # type: ignore[no-redef,unused-ignore]
    return _kept(locals(), ('_tw_water',))


def _seg_0563_271___tw_water_1(*, M: Any = _UNBOUND, _tw_water: Any = _UNBOUND, _tw_wc: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.271 (_tw_water, _tw_wc) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for _tw_wc in M.get("streams", []) + M.get("channels", []) + M.get("canals", []):
            _tw_water.append((_tw_wc["poly"], _tw_wc.get("w", 6) / 2))
    return _kept(locals(), ('_tw_water', '_tw_wc'))


def _seg_0563_272___tw_water_2(*, M: Any = _UNBOUND, _tw_water: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.272 (_tw_water) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and M.get("moat"):
        _tw_water.append((M["moat"], M.get("moat_width", 22) / 2))
    return _kept(locals(), ('_tw_water',))


def _seg_0563_273___tw_pond(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.273 (_tw_pond) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        _tw_pond = M.get("pond")
    return _kept(locals(), ('_tw_pond',))


def _seg_0563_274___tw_on_water(
    *,
    _hw: Any = _UNBOUND,
    _pl: Any = _UNBOUND,
    _tw_pond: Any = _UNBOUND,
    _tw_water: Any = _UNBOUND,
    i: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    o_: Any = _UNBOUND,
    r_: Any = _UNBOUND,
    reach: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.274 (_tw_on_water) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):

        def _tw_on_water(o_: dict[str, Any], reach: float) -> bool:
            r_ = max(o_["w"], o_["h"]) / 2  # family: ASSOCIATION/REACH, as _ty_on_water above
            if any(seg_dist(o_["x"], o_["y"], _pl[i], _pl[i + 1]) < _hw + r_ + reach for _pl, _hw in _tw_water for i in range(len(_pl) - 1)):
                return True
            return _tw_pond is not None and math.hypot(o_["x"] - _tw_pond[0], o_["y"] - _tw_pond[1]) < max(_tw_pond[2], _tw_pond[3]) + r_ + reach

    return _kept(locals(), ('_tw_on_water',))


def _seg_0563_275___tw_dyes(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.275 (_tw_dyes) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        _tw_dyes = M.get("dye_yards", [])
    return _kept(locals(), ('_tw_dyes',))


def _seg_0563_276__city_has_dye_works(
    *, _tw_dyes: Any = _UNBOUND, _tw_on_water: Any = _UNBOUND, check: Any = _UNBOUND, d_: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.276 (city_has_dye_works) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):
            check(
                "city_has_dye_works",
                bool(_tw_dyes) and all(_tw_on_water(d_, 40) for d_ in _tw_dyes),
                f"{len(_tw_dyes)} dye works, on water: {[bool(_tw_dyes) and _tw_on_water(d_, 40) for d_ in _tw_dyes]} - every city keeps a dyer (s.dye_yard), and the drying/rinsing yard must sit ON water (within ~40px of a stream/channel/canal/pond/moat; dyers need rinsing water, not bulk transport, so landlocked cities keep them too)",
            )
    return _kept(locals(), ('d_',))


def _seg_0563_277__city_has_oil_press(*, M: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.277 (city_has_oil_press) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_has_oil_press", bool(M.get("oil_presses")), "no oil press - every city keeps a presser's barn (s.oil_press: wedge-and-beam press + ox-driven mill ring, toward the edge)")
    return _kept(locals(), ())


def _seg_0563_278__city_has_pawnshop(*, M: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.278 (city_has_pawnshop) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_has_pawnshop", bool(M.get("pawnshops")), "no pawnshop - every city keeps one (s.pawnshop: shopfront + 2 pledge kura in a walled rear court)")
    return _kept(locals(), ())


# BATHHOUSE COUNT FOLLOWS THE GM FORMULA (2026-07-24, second refinement): ONE per
# full 2,000 population + a remainder-fraction chance of one extra (2,500 -> 1 + 25%,
# 3,000 -> 1 + 50%, 4,000 -> exactly 2; floored at 1) - Edo's own peak ratio was ~1
# per ~2,100 residents (1808: 523 sento for ~1.1M), which is where the 2,000 divisor
# comes from. A recorded roll (meta bathhouse_roll, s.bathhouses) must also match the
# drawn count, so a stale hand count cannot ship.


def _seg_0563_279___bh_n(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.279 (_bh_n) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        _bh_n = len(M.get("bathhouses", []))
    return _kept(locals(), ('_bh_n',))


def _seg_0563_280___bh_pop(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.280 (_bh_pop) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        _bh_pop = int(meta.get("population") or 3000)
    return _kept(locals(), ('_bh_pop',))


def _seg_0563_281___bh_floor(*, _bh_pop: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.281 (_bh_floor) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        _bh_floor = max(1, _bh_pop // 2000)
    return _kept(locals(), ('_bh_floor',))


def _seg_0563_282___bh_allowed(*, _bh_floor: Any = _UNBOUND, _bh_pop: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.282 (_bh_allowed) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        _bh_allowed = {_bh_floor} if _bh_pop % 2000 == 0 else {_bh_floor, _bh_floor + 1}
    return _kept(locals(), ('_bh_allowed',))


def _seg_0563_283___bh_roll(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.283 (_bh_roll) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        _bh_roll = meta.get("bathhouse_roll")
    return _kept(locals(), ('_bh_roll',))


def _seg_0563_284__city_has_bathhouse(
    *, _bh_allowed: Any = _UNBOUND, _bh_n: Any = _UNBOUND, _bh_pop: Any = _UNBOUND, _bh_roll: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.284 (city_has_bathhouse) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_has_bathhouse",
            _bh_n in _bh_allowed and (_bh_roll is None or _bh_n == _bh_roll),
            f"{_bh_n} bathhouse(s) at population {_bh_pop} (rolled {_bh_roll}) - the sento count follows the "
            f"GM formula (s.bathhouses: 1 per full 2,000 population + a remainder-fraction chance of one "
            f"extra, so 2,500 -> 1 + 25%, 3,000 -> 1 + 50%, 4,000 -> exactly 2; Edo's peak ratio was ~1 per "
            f"~2,100 residents), and a recorded roll must match the drawn count",
        )
    return _kept(locals(), ())


def _seg_0563_285___tw_kilns(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.285 (_tw_kilns) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        _tw_kilns = M.get("kilns", [])
    return _kept(locals(), ('_tw_kilns',))


def _seg_0563_286__city_kiln_outside_walls(
    *, _tw_kilns: Any = _UNBOUND, check: Any = _UNBOUND, inwall: Any = _UNBOUND, k_: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.286 (city_kiln_outside_walls) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):
            check(
                "city_kiln_outside_walls",
                bool(_tw_kilns) and all(not inwall(k_["x"], k_["y"]) for k_ in _tw_kilns),
                f"{len(_tw_kilns)} kiln(s), all outside the walls: {all(not inwall(k_['x'], k_['y']) for k_ in _tw_kilns) if _tw_kilns else False} - a city keeps a kiln works at its periphery, and fire law + smoke put every kiln strictly OUTSIDE the walls (s.kiln). Its WORKERS' cottages go outside with it, which is a fact about where the clay and the days-long firing are, not a banishment - see kiln_works_houses_its_workers",
            )
    return _kept(locals(), ('k_',))


def _seg_0563_287__city_river_port_has_lumber_yard(
    *, L_: Any = _UNBOUND, M: Any = _UNBOUND, _tw_lys: Any = _UNBOUND, _tw_on_water: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.287 (city_river_port_has_lumber_yard) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):  # noqa: SIM102
            if meta.get("river_port"):
                _tw_lys = M.get("lumber_yards", [])
                check(
                    "city_river_port_has_lumber_yard",
                    bool(_tw_lys) and all(_tw_on_water(L_, 60) for L_ in _tw_lys),
                    f"{len(_tw_lys)} lumber yard(s) on the bank - a river-port city keeps a riverside zaimokuya (s.lumber_yard within ~60px of a stream/canal); timber moves by water at scale (a landlocked city has none and skips this check)",
                )
    return _kept(locals(), ('L_', '_tw_lys'))


# ... AND A LUMBER YARD NEVER OVERLAPS THE WATER (GM 2026-07-24, second pass): the
# yard ABUTS the bank - stock arrives by water - but stacked timber stands on DRY
# ground (logs in the current float away; the landing is the jetty's job). The
# generic no_structure_on_stream check cannot see this defect: it tests a fixed ~6px
# half-width tuned for village brooks, and Nagahara's 40px river swallowed a yard
# corner without tripping it (the pinned real fixture). Tested here against every
# watercourse's REAL half-width (streams/channels/canals + the moat via _tw_water),
# sampling the yard rect's corners, edge midpoints, and center (records are axis-
# aligned; rot stays 0 in s.lumber_yard).


def _seg_0563_288___ly_wet(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.288 (_ly_wet) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        _ly_wet = []  # type: ignore[var-annotated]
    return _kept(locals(), ('_ly_wet',))


def _seg_0563_289__L_(
    *,
    L_: Any = _UNBOUND,
    M: Any = _UNBOUND,
    _hw: Any = _UNBOUND,
    _ldx: Any = _UNBOUND,
    _ldy: Any = _UNBOUND,
    _lh2: Any = _UNBOUND,
    _lpts: Any = _UNBOUND,
    _lw2: Any = _UNBOUND,
    _ly_wet: Any = _UNBOUND,
    _pl: Any = _UNBOUND,
    _qx: Any = _UNBOUND,
    _qy: Any = _UNBOUND,
    _tw_water: Any = _UNBOUND,
    i: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.289 (L_, _hw, _ldx, _ldy) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for L_ in M.get("lumber_yards", []):
            _lw2, _lh2 = L_["w"] / 2, L_["h"] / 2
            _lpts = [(L_["x"] + _ldx, L_["y"] + _ldy) for _ldx in (-_lw2, 0.0, _lw2) for _ldy in (-_lh2, 0.0, _lh2)]
            if any(seg_dist(_qx, _qy, _pl[i], _pl[i + 1]) < _hw for _qx, _qy in _lpts for _pl, _hw in _tw_water for i in range(len(_pl) - 1)):
                _ly_wet.append((round(L_["x"]), round(L_["y"])))
    return _kept(locals(), ('L_', '_hw', '_ldx', '_ldy', '_lh2', '_lpts', '_lw2', '_ly_wet', '_pl', '_qx', '_qy', 'i'))


def _seg_0563_290__lumber_yard_clear_of_water(*, _ly_wet: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.290 (lumber_yard_clear_of_water) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):
            check(
                "lumber_yard_clear_of_water",
                not _ly_wet,
                f"lumber yard(s) overlapping open water at {_ly_wet} - the yard abuts the bank but its stacks stand on dry ground (logs in the current float away); pull the yard back to the waterline, tested at each watercourse's real half-width",
            )
    return _kept(locals(), ())


# market-day lodging: a flophouse INSIDE the walls, and one OUTSIDE each gate (for
# travelers arriving from either direction, who reach the gate after it has shut)


def _seg_0563_291__flops(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.291 (flops) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        flops = M.get("flophouses", [])
    return _kept(locals(), ('flops',))


def _seg_0563_292__city_flophouse_inside_walls(
    *, check: Any = _UNBOUND, fl: Any = _UNBOUND, flops: Any = _UNBOUND, inwall: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.292 (city_flophouse_inside_walls) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_flophouse_inside_walls", any(inwall(fl["x"], fl["y"]) for fl in flops), "a city needs market-day lodging inside the walls (a flophouse)")
    return _kept(locals(), ('fl',))


def _seg_0563_293__fl(
    *, fl: Any = _UNBOUND, flops: Any = _UNBOUND, g: Any = _UNBOUND, gates: Any = _UNBOUND, i: Any = _UNBOUND, inwall: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.293 (fl, g, gates_wo_flop, i) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        gates_wo_flop = [i for i, g in enumerate(gates) if not any((not inwall(fl["x"], fl["y"])) and math.hypot(fl["x"] - g[0], fl["y"] - g[1]) <= 520 for fl in flops)]
    return _kept(locals(), ('fl', 'g', 'gates_wo_flop', 'i'))


def _seg_0563_294__city_flophouse_outside_each_gate(*, check: Any = _UNBOUND, gates_wo_flop: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.294 (city_flophouse_outside_each_gate) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_flophouse_outside_each_gate",
            not gates_wo_flop,
            f"every city gate needs a flophouse just outside it (travelers who arrive after the gate shuts sleep there); gate(s) without one: {gates_wo_flop}",
        )
    return _kept(locals(), ())


# a flophouse is a humble doss-house (a sen a night, on straw): inside the walls it belongs
# in a HUMBLE quarter (the laborer section, or Tango's agrarian sector), NEVER cheek-by-jowl
# with the nicer neighborhoods (temples, merchants, samurai), and never in or up against the
# burakumin quarter. Only the in-wall flophouse is judged (the gate ones sit by the gate market).


def _seg_0563_295__b_15(*, M: Any = _UNBOUND, b: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.295 (b, nice) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        nice = [b for b in M.get("buildings", []) if b.get("kind") in ("merchant", "samurai", "samurai_large")] + M.get("religious", [])
    return _kept(locals(), ('b', 'nice'))


def _seg_0563_296__b_16(*, M: Any = _UNBOUND, b: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.296 (b, bura) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        bura = [b for b in M.get("buildings", []) if b.get("kind") == "burakumin"]
    return _kept(locals(), ('b', 'bura'))


def _seg_0563_297__b_17(*, M: Any = _UNBOUND, b: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.297 (b, inns) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        inns = [b for b in M.get("buildings", []) if b.get("kind") == "inn"]
    return _kept(locals(), ('b', 'inns'))


def _seg_0563_298__b_18(*, M: Any = _UNBOUND, b: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.298 (b, stbl) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        stbl = [b for b in M.get("buildings", []) if b.get("kind") == "stables"]
    return _kept(locals(), ('b', 'stbl'))


def _seg_0563_299__bad_flop(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.299 (bad_flop) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        bad_flop = []  # type: ignore[var-annotated]
    return _kept(locals(), ('bad_flop',))


# a flop within reach of a GATE is the caravan flop - it serves the wagon crews
# at the gate quarter wherever that quarter's caste sits (021: the capital's bands
# abut its gates); the humble-quarter rule governs the market doss-houses only


def _seg_0563_300__b_19(
    *,
    b: Any = _UNBOUND,
    bad_flop: Any = _UNBOUND,
    bura: Any = _UNBOUND,
    fl: Any = _UNBOUND,
    flops: Any = _UNBOUND,
    inns: Any = _UNBOUND,
    inwall: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    nice: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    stbl: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.300 (b, bad_flop, fl) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for fl in flops:
            if not inwall(fl["x"], fl["y"]):
                continue
            # a CARAVAN flophouse (one paired with an inn AND a stables, a gate transit cluster) is
            # exempt from the humble-quarter rule - the gate is a transit zone, not a nice neighborhood
            if any(math.hypot(b["x"] - fl["x"], b["y"] - fl["y"]) < 170 for b in inns) and any(math.hypot(b["x"] - fl["x"], b["y"] - fl["y"]) < 170 for b in stbl):
                continue
            if any(math.hypot(b["x"] - fl["x"], b["y"] - fl["y"]) < 110 for b in nice):
                bad_flop.append((round(fl["x"]), round(fl["y"]), "next to a temple/merchant/samurai"))
            elif any(math.hypot(b["x"] - fl["x"], b["y"] - fl["y"]) < 150 for b in bura):
                bad_flop.append((round(fl["x"]), round(fl["y"]), "in/next to the burakumin quarter"))
    return _kept(locals(), ('b', 'bad_flop', 'fl'))


# a flop within reach of a GATE is the caravan flop even if its inn/stables pair sits
# slightly past 170px - it serves the wagon crews at the gate quarter wherever that
# quarter's caste sits (021: the capital's bands abut its gates); the humble-quarter
# rule governs the market doss-houses only. (Filter AFTER the loop that fills bad_flop;
# the first version ran it against the empty list and was dead code, 2026-08-10.)


def _seg_0563_301___g21(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.301 (_g21) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        _g21 = M.get("gates") or []
    return _kept(locals(), ('_g21',))


def _seg_0563_302__bad_flop_1(*, _g21: Any = _UNBOUND, bad_flop: Any = _UNBOUND, bf: Any = _UNBOUND, g21: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.302 (bad_flop, bf, g21) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        bad_flop = [bf for bf in bad_flop if not any(math.hypot(bf[0] - g21[0], bf[1] - g21[1]) <= 250 for g21 in _g21)]
    return _kept(locals(), ('bad_flop', 'bf', 'g21'))


def _seg_0563_303__city_flophouse_in_humble_quarter(*, bad_flop: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.303 (city_flophouse_in_humble_quarter) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_flophouse_in_humble_quarter",
            not bad_flop,
            f"in-wall flophouse(s) sited in/beside a nicer or burakumin neighborhood (a doss-house belongs in the laborer/agrarian sector): {bad_flop}",
        )
    return _kept(locals(), ())


# CARAVAN facilities: just INSIDE each gate a wagon-train needs a prominent INN and a large
# STABLES (dozens of draft animals + crew) close to its flophouse, with OPEN GROUND around the
# stables for the animals to be tied up / penned. Three buildings near each gate, not just one.


def _seg_0563_304__caravan_bad(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.304 (caravan_bad) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        caravan_bad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('caravan_bad',))


def _seg_0563_305__b_20(
    *,
    M: Any = _UNBOUND,
    b: Any = _UNBOUND,
    caravan_bad: Any = _UNBOUND,
    crowd: Any = _UNBOUND,
    flops: Any = _UNBOUND,
    g: Any = _UNBOUND,
    gates: Any = _UNBOUND,
    gf: Any = _UNBOUND,
    gi: Any = _UNBOUND,
    gnear: Any = _UNBOUND,
    gs: Any = _UNBOUND,
    inns: Any = _UNBOUND,
    inwall: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    r: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    stbl: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.305 (b, caravan_bad, crowd, g) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for g in gates:

            def gnear(items: Sequence[dict[str, Any]], r: float = 340, g: Any = g) -> list[dict[str, Any]]:  # bind loop var (used within this iteration)
                return [b for b in items if inwall(b["x"], b["y"]) and math.hypot(b["x"] - g[0], b["y"] - g[1]) <= r]

            gi, gs, gf = gnear(inns), gnear(stbl), gnear(flops)
            if not (gi and gs and gf):
                caravan_bad.append((g, f"inn={len(gi)} stables={len(gs)} flophouse={len(gf)}"))
                continue
            crowd = sum(1 for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS and math.hypot(b["x"] - gs[0]["x"], b["y"] - gs[0]["y"]) < 75)
            if crowd > 4:
                caravan_bad.append((g, f"stables hemmed in by {crowd} dwellings (needs open ground for animals)"))
    return _kept(locals(), ('b', 'caravan_bad', 'crowd', 'g', 'gf', 'gi', 'gnear', 'gs'))


def _seg_0563_306__city_gate_caravan_facilities(*, caravan_bad: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.306 (city_gate_caravan_facilities) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_gate_caravan_facilities",
            not caravan_bad,
            f"city gate(s) lacking inside caravan facilities (a prominent inn + large stables + flophouse + open ground close to the gate): {caravan_bad}",
        )
    return _kept(locals(), ())


# PADDY-FIRST estate doctrine (GM 2026-07-23, superseding the old >=2 floor): the rice
# paddies claim the near ring FIRST, and the samurai country estates take only what is
# left - most estates sit farther out in the rural district, so a city map showing just
# ONE estate (even a fraction running off the frame edge) is the more historically
# accurate signal; the rest are implied off-map. At least one must still show.


def _seg_0563_307___shown(
    *, EX0: Any = _UNBOUND, EX1: Any = _UNBOUND, EY0: Any = _UNBOUND, EY1: Any = _UNBOUND, hh: Any = _UNBOUND, hw: Any = _UNBOUND, m: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.307 (_shown) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):

        def _shown(m: dict[str, Any]) -> bool:
            hw, hh = m["w"] / 2, m["h"] / 2
            return bool(m["x"] + hw > EX0 and m["x"] - hw < EX1 and m["y"] + hh > EY0 and m["y"] - hh < EY1)

    return _kept(locals(), ('_shown',))


def _seg_0563_308__m_3(*, M: Any = _UNBOUND, _shown: Any = _UNBOUND, m: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.308 (m, shown_est) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        shown_est = [m for m in M.get("manors", []) if _shown(m)]
    return _kept(locals(), ('m', 'shown_est'))


def _seg_0563_309__city_estates_multiple_shown(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, shown_est: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.309 (city_estates_multiple_shown) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_estates_multiple_shown",
            len(shown_est) >= 1,
            f"{len(shown_est)} samurai estates fall inside the map window - show at least 1 (a fraction cropped at the edge is fine); the rest of the gentry sit farther out, implied off-map",
        )
    return _kept(locals(), ())


# the Imperial-road label must sit OUTSIDE the walls (inside, the roadway is a city street)


def _seg_0563_310__rlab(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.310 (rlab) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        rlab = M.get("road_label")
    return _kept(locals(), ('rlab',))


def _seg_0563_311__city_road_label_outside_walls(*, check: Any = _UNBOUND, inwall: Any = _UNBOUND, meta: Any = _UNBOUND, rlab: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.311 (city_road_label_outside_walls) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and rlab:
        check(
            "city_road_label_outside_walls",
            not inwall(rlab[0], rlab[1]),
            "the 'Imperial Road' label must sit outside the walls - inside the gates the same roadway is a city street, a city (not Imperial) responsibility",
        )
    return _kept(locals(), ())


def _seg_0563_312__empty_city_streets(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.312 (empty_city_streets) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        empty_city_streets = empty_street_runs(M, w)
    return _kept(locals(), ('empty_city_streets',))


def _seg_0563_313__city_streets_have_buildings(*, check: Any = _UNBOUND, empty_city_streets: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.313 (city_streets_have_buildings) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_streets_have_buildings",
            not empty_city_streets,
            f"city street(s) with a stretch inside the walls with no building fronting it (a street network earns its length from the buildings it serves): {empty_city_streets}",
        )
    return _kept(locals(), ())


# ROADSIDE LAND on a larger city street is PRIME real estate: a paved through-street in a
# commercial/residential quarter must be LINED with buildings (houses, shops, civic halls)
# close to it, not left with a long bare margin. This is stricter than city_streets_have_buildings
# (which tolerates a building up to ~105px away): here a building must sit WITHIN ~58px of the
# street, the way storefronts and house-fronts actually line a road. Only the narrow gravel
# ALLEYS that thread the block interiors are exempt (those are the "small streets" that need no
# frontage), and so is the GOVERNMENT avenue - its frontage is the spaced ministry compounds,
# governed by city_ministries_front_a_street, not shops/houses. (The merchant avenue once read
# bare because its storefront frontage was silently blocked by the avenue's own corridor.)


def _seg_0563_314__line_blds(*, M: Any = _UNBOUND, gov: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.314 (line_blds) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        line_blds = M.get("buildings", []) + M.get("religious", []) + M.get("ministries", []) + M.get("flophouses", []) + ([gov] if gov else [])
    return _kept(locals(), ('line_blds',))


def _seg_0563_315__gov_pts(*, M: Any = _UNBOUND, gov: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.315 (gov_pts) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        gov_pts = M.get("ministries", []) + ([gov] if gov else [])
    return _kept(locals(), ('gov_pts',))


def _seg_0563_316__LINE_D(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.316 (LINE_D, LINE_RUN) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        LINE_D, LINE_RUN = 58, 140
    return _kept(locals(), ('LINE_D', 'LINE_RUN'))


def _seg_0563_317__bare_streets(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.317 (bare_streets) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        bare_streets = []  # type: ignore[var-annotated]
    return _kept(locals(), ('bare_streets',))


def _seg_0563_318___lg_open(
    *,
    LINE_D: Any = _UNBOUND,
    LINE_RUN: Any = _UNBOUND,
    M: Any = _UNBOUND,
    _lg_open: Any = _UNBOUND,
    a: Any = _UNBOUND,
    b: Any = _UNBOUND,
    bare_streets: Any = _UNBOUND,
    bl: Any = _UNBOUND,
    cg9: Any = _UNBOUND,
    gov_pts: Any = _UNBOUND,
    gp9: Any = _UNBOUND,
    i: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    j: Any = _UNBOUND,
    ki: Any = _UNBOUND,
    line_blds: Any = _UNBOUND,
    m: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    pts: Any = _UNBOUND,
    run: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    st: Any = _UNBOUND,
    steps: Any = _UNBOUND,
    t: Any = _UNBOUND,
    w: Any = _UNBOUND,
    worst: Any = _UNBOUND,
    x: Any = _UNBOUND,
    y: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.318 (_lg_open, a, b, bare_streets) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for st in M.get("town_streets", []):
            pts = st["pts"]
            if sum(1 for m in gov_pts if min(seg_dist(m["x"], m["y"], pts[i], pts[i + 1]) for i in range(len(pts) - 1)) < 70) >= 2:
                continue  # a government avenue - lined by ministry compounds
            worst = run = 0
            for ki in range(len(pts) - 1):
                a, b = pts[ki], pts[ki + 1]
                steps = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) // 20))
                for j in range(steps):
                    t = j / steps
                    x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                    _lg_open = any(
                        point_in_poly(x, y, gp9) or min(seg_dist(x, y, gp9[i9], gp9[(i9 + 1) % len(gp9)]) for i9 in range(len(gp9))) < 70
                        for gp9 in (cg9["poly"] for cg9 in M.get("commons", []) if cg9.get("poly"))
                    )  # open-ground frontage (commons/pasture): same exemption as empty_street_runs (021)
                    if not point_in_poly(x, y, w) or any((bl["x"] - x) ** 2 + (bl["y"] - y) ** 2 < LINE_D * LINE_D for bl in line_blds) or _lg_open:
                        run = 0
                    else:
                        run += 20
                        worst = max(worst, run)
            if worst > LINE_RUN:
                bare_streets.append(("main" if st.get("main") else f"@{(round(pts[0][0]), round(pts[0][1]))}", worst))
    return _kept(locals(), ('_lg_open', 'a', 'b', 'bare_streets', 'bl', 'cg9', 'gp9', 'i', 'i9', 'j', 'ki', 'm', 'pts', 'run', 'st', 'steps', 't', 'worst', 'x', 'y'))


def _seg_0563_319__city_larger_streets_lined(*, bare_streets: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.319 (city_larger_streets_lined) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_larger_streets_lined",
            not bare_streets,
            f"larger city street(s) with a long bare stretch of roadside land - a commercial/residential through-street should be "
            f"LINED with buildings close to it (only narrow alleys may run unlined): {bare_streets}",
        )
    return _kept(locals(), ())


def _seg_0563_320__road_1(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.320 (road) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        road = M.get("road") or []
    return _kept(locals(), ('road',))


def _seg_0563_321__city_imperial_road_through(
    *,
    EX0: Any = _UNBOUND,
    EX1: Any = _UNBOUND,
    EY0: Any = _UNBOUND,
    EY1: Any = _UNBOUND,
    M: Any = _UNBOUND,
    check: Any = _UNBOUND,
    dead: Any = _UNBOUND,
    e: Any = _UNBOUND,
    exits: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    offend: Any = _UNBOUND,
    p: Any = _UNBOUND,
    r: Any = _UNBOUND,
    rds: Any = _UNBOUND,
    road: Any = _UNBOUND,
    road_through: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.321 (city_imperial_road_through, city_roads_run_offmap) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        if meta.get("imperial_road", True):
            road_through = bool(road) and any(p[1] < EY0 for p in road) and any(p[1] > EY1 for p in road)
            check("city_imperial_road_through", road_through, "the Imperial road must run N-S through a walled city - off both the top and bottom edges, via the gates")
        else:
            # NO Imperial road (it passes miles away): the city still lives on through-traffic,
            # so its road net must leave the map in at least TWO directions (one polyline
            # bending through the city - off-map N, through the gates, off-map SE - counts
            # as two; a dead-end road serves nobody)
            rds = [r["pts"] for r in M.get("roads", [])] or ([road] if road else [])

            def offend(p: Pt) -> bool:
                return p[0] < EX0 or p[0] > EX1 or p[1] < EY0 or p[1] > EY1  # type: ignore[no-any-return]

            exits = sum(1 for r in rds for e in (r[0], r[-1]) if offend(e))
            dead = [(round(e[0]), round(e[1])) for r in rds for e in (r[0], r[-1]) if not offend(e)]
            check(
                "city_roads_run_offmap",
                exits >= 2 and not dead,
                f"{exits} off-map road end(s), dead end(s) at {dead[:3]} - a provincial city without an Imperial spine still connects to the wider world in >= 2 directions, and no road stops dead",
            )
    return _kept(locals(), ('dead', 'e', 'exits', 'offend', 'p', 'r', 'rds', 'road_through'))


def _seg_0563_322__city_no_inwall_farms(
    *, check: Any = _UNBOUND, f: Any = _UNBOUND, fields: Any = _UNBOUND, inwall: Any = _UNBOUND, inwall_fields: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.322 (city_no_inwall_farms) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and not meta.get("agricultural_district"):
        inwall_fields = [f["name"] for f in fields if inwall((f["bbox"][0] + f["bbox"][2]) / 2, (f["bbox"][1] + f["bbox"][3]) / 2)]
        check("city_no_inwall_farms", not inwall_fields, f"farms inside a city wall are uncharacteristic - set meta(agricultural_district=True) to allow them: {inwall_fields}")
    return _kept(locals(), ('f', 'inwall_fields'))


# INTRAMURAL groves OFF: a farm inside the wall carries NO windbreak grove - an in-wall plot is not
# an isolated farmstead (the urban fabric already breaks the wind) and sits on land too precious for
# a tree belt. So the in-wall agricultural district stays grove-free. WHY: settlements.md "Homestead groves".


def _seg_0563_323__no_groves_inside_walls(
    *, M: Any = _UNBOUND, check: Any = _UNBOUND, gv: Any = _UNBOUND, inwall: Any = _UNBOUND, inwall_groves: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.323 (no_groves_inside_walls) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and not meta.get("inwall_groves"):
        inwall_groves = sorted({(round(gv["of"][0]), round(gv["of"][1])) for gv in M.get("groves", []) if inwall(gv["of"][0], gv["of"][1])})
        check(
            "no_groves_inside_walls",
            not inwall_groves,
            f"farm(s) inside the city wall carry a windbreak grove {inwall_groves[:3]} - an intramural plot is "
            f"sheltered by the urban fabric and on land too precious for one (meta(inwall_groves=True) to allow)",
        )
    return _kept(locals(), ('gv', 'inwall_groves'))


def _seg_0563_324__moat_2(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.324 (moat) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        moat = M.get("moat")
    return _kept(locals(), ('moat',))


def _seg_0563_325__city_moat_feeder_matches_width(
    *,
    EX0: Any = _UNBOUND,
    EX1: Any = _UNBOUND,
    EY0: Any = _UNBOUND,
    EY1: Any = _UNBOUND,
    M: Any = _UNBOUND,
    bare: Any = _UNBOUND,
    check: Any = _UNBOUND,
    disp_a: Any = _UNBOUND,
    disp_b: Any = _UNBOUND,
    e: Any = _UNBOUND,
    e0: Any = _UNBOUND,
    e1: Any = _UNBOUND,
    feeders: Any = _UNBOUND,
    has_outfall: Any = _UNBOUND,
    i: Any = _UNBOUND,
    inlet_disp: Any = _UNBOUND,
    j: Any = _UNBOUND,
    j_arc: Any = _UNBOUND,
    loose: Any = _UNBOUND,
    mcx: Any = _UNBOUND,
    mcy: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    moat: Any = _UNBOUND,
    moat_is_fed: Any = _UNBOUND,
    mw: Any = _UNBOUND,
    narrow: Any = _UNBOUND,
    outlet_disp: Any = _UNBOUND,
    p: Any = _UNBOUND,
    q: Any = _UNBOUND,
    rcum: Any = _UNBOUND,
    rdist: Any = _UNBOUND,
    ri2: Any = _UNBOUND,
    rpts: Any = _UNBOUND,
    rv: Any = _UNBOUND,
    s: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    taps: Any = _UNBOUND,
    w: Any = _UNBOUND,
    wx: Any = _UNBOUND,
    wy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.325 (city_moat_fed_offmap, city_moat_feeder_matches_width, city_moat_has_outfall, city_moat_joins_river, city_moat_junction_angles, city_moat_surrounds_wall) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):  # noqa: SIM102
            if moat:
                rv = M.get("river")
                if rv:
                    # a river-bank city's moat is an OPEN arc: the river closes the water ring on its
                    # flank (Xiangyang/Pingyao pattern). Coverage: every wall vertex stands behind
                    # water - within ~72px of the moat arc OR ~200px of the river (the wharf strip
                    # sits between wall and bank, so the river runs further out than a dug moat) -
                    # and BOTH open moat ends must actually JOIN the river (inlet upstream, outlet
                    # downstream, the current flushing the ring).
                    # READ THE RIVER'S RECORDED FLOW rather than assuming its point order (GM
                    # 2026-07-25). Everything below - the arc-length ordering that decides which moat
                    # foot is the upstream INLET and which the downstream OUTLET, and the junction
                    # tilts keyed on it - takes increasing arc length to mean "downstream". That IS
                    # the upstream-first authoring convention, but hard-coding it means a river tagged
                    # flow="reverse" would be measured exactly backwards with nothing to catch it.
                    # Reverse the points when the record says so, and the convention becomes an
                    # assertion instead of an assumption.
                    rpts = rv["pts"][::-1] if rv.get("flow") == "reverse" else rv["pts"]

                    def rdist(q: Pt) -> float:
                        return min(seg_dist(q[0], q[1], rpts[i], rpts[i + 1]) for i in range(len(rpts) - 1))

                    bare = [(round(wx), round(wy)) for wx, wy in w if min(seg_dist(wx, wy, moat[i], moat[i + 1]) for i in range(len(moat) - 1)) > 72 and rdist((wx, wy)) > 200]
                    check(
                        "city_moat_surrounds_wall",
                        not bare,
                        f"wall stretch(es) behind neither the moat arc nor the river: {bare[:4]} - a river-bank city's dug moat covers the landward faces and the river covers its own flank",
                    )
                    loose = [(round(e[0]), round(e[1])) for e in (moat[0], moat[-1]) if rdist(e) > rv["w"] / 2 + 12]
                    if (
                        scale == "city"
                    ):  # CAPITAL-INVERTED (021): the capital moat is a complete RING with sluiced leats (the Chinese form, 020 research) - the leat checks validate its water, not the provincial open-arc model
                        check(
                            "city_moat_joins_river",
                            not loose,
                            f"open moat end(s) not joining the river: {loose} - the moat taps the river upstream and returns downstream (the current flushes it); extend the ends onto the river",
                        )
                    # JUNCTION ANGLES FOLLOW THE CURRENT (GM 2026-07-24 hydrology review; the old
                    # square tees were an rfoot-projection artifact, not a decision - settlements.md
                    # river-cities "junction angles follow the current"): the OUTLET (downstream
                    # junction) sweeps visibly downstream - junction angle is a primary confluence
                    # flow control, a square tee drives the exit jet across the river, and natural
                    # tributaries / drainage returns join pointing downstream - while the INLET
                    # stays square or tilts upstream, never smoothly flow-aligned (an offtake
                    # aligned with the current drinks the river's bedload and silts the ring;
                    # classical headworks kept intakes near-square under sluice control). Measured
                    # as each junction's arclength displacement off its adjacent kept vertex's
                    # square foot. CONVENTION: river pts run upstream-first (s.moat documents it).
                    if len(moat) >= 3:
                        rcum = [0.0]
                        for ri2 in range(len(rpts) - 1):
                            rcum.append(rcum[-1] + math.hypot(rpts[ri2 + 1][0] - rpts[ri2][0], rpts[ri2 + 1][1] - rpts[ri2][1]))

                        def j_arc(q: Any) -> float:
                            kj = min(range(len(rpts) - 1), key=lambda i7: seg_dist(q[0], q[1], rpts[i7], rpts[i7 + 1]))
                            fxj, fyj = seg_closest(q[0], q[1], rpts[kj], rpts[kj + 1])
                            return rcum[kj] + math.hypot(fxj - rpts[kj][0], fyj - rpts[kj][1])  # type: ignore[no-any-return]

                        disp_a = j_arc(moat[0]) - j_arc(moat[1])
                        disp_b = j_arc(moat[-1]) - j_arc(moat[-2])
                        inlet_disp, outlet_disp = (disp_a, disp_b) if j_arc(moat[0]) <= j_arc(moat[-1]) else (disp_b, disp_a)
                        if scale == "city":  # CAPITAL-INVERTED (021): ring-with-leats form; the leat junctions are validated by moat_junctions_swept_with_the_current
                            check(
                                "city_moat_junction_angles",
                                outlet_disp >= 12 and inlet_disp <= 4,
                                f"moat-river junction angles fight the current (inlet downstream-shift {inlet_disp:.0f}px, outlet {outlet_disp:.0f}px): "
                                f"the outlet must SWEEP DOWNSTREAM (>= 12px off the square foot - a square tee drives the exit jet across the river) "
                                f"and the inlet must stay square or tilt upstream (<= 4px - a flow-aligned intake drinks the river's bedload); "
                                f"tune river_inlet_tilt/river_outlet_tilt on s.moat()",
                            )
                else:
                    check("city_moat_surrounds_wall", len(w) >= 3 and all(point_in_poly(wx, wy, moat) for wx, wy in w), "the moat must encircle the wall (every wall point inside the moat ring)")
                moat_is_fed = any(
                    any(p[0] < EX0 or p[0] > EX1 or p[1] < EY0 or p[1] > EY1 for p in (s["poly"][0], s["poly"][-1])) and min(poly_dist(q[0], q[1], moat) for q in s["poly"]) <= 32
                    for s in M.get("streams", [])
                )
                if scale == "city":  # CAPITAL-INVERTED (021): the ring is fed by its sluiced river leat, validated by the leat battery
                    check("city_moat_fed_offmap", moat_is_fed, "the moat must be fed from an off-map water source (a stream from a map edge reaching the moat)")
                # the FEEDER must carry the moat's flow: a stream filling the moat is as WIDE as the moat
                # itself (a trickle cannot keep a full moat supplied) - so any stream reaching the moat must
                # match its width (within ~25%).
                mw = M.get("moat_width", 22)
                feeders = [s for s in M.get("streams", []) if min(poly_dist(q[0], q[1], moat) for q in s["poly"]) <= 32]
                narrow = [s.get("w", 9) for s in feeders if s.get("w", 9) < 0.75 * mw]
                check(
                    "city_moat_feeder_matches_width",
                    not narrow,
                    f"the stream feeding the moat is too narrow ({narrow} px vs the {mw}px moat) - a moat's water source "
                    f"must be about as wide as the moat it supplies (pass s.stream(..., width=<moat width>))",
                )
                # A FED CLOSED (non-river) MOAT MUST ALSO DRAIN. A moat with a live feeder but no outfall
                # would overflow: conservation of flow - a perennial stream cannot be held in a wet-rice-
                # climate moat as a terminal pond (evaporation + seepage cannot absorb a live stream; that
                # balance belongs to an arid, spring/rain-fed moat). The historical norm is a FLOW-THROUGH
                # ring - feeder in on the high side, outfall off the LOW side to a lower watercourse, the
                # current flushing corner-to-corner (Beijing's gated water-passes; the Forbidden City's
                # NW-in / SE-out moat). The river-moat case is already covered by city_moat_joins_river
                # (inlet upstream, outlet downstream), so this guards the closed-moat case. See settlements.md.
                if not rv and moat_is_fed:
                    mcx, mcy = sum(p[0] for p in moat) / len(moat), sum(p[1] for p in moat) / len(moat)
                    taps = []  # the moat-rim end of each stream that reaches the moat AND runs off-map: feeder + any outfall
                    for s in M.get("streams", []):
                        e0, e1 = s["poly"][0], s["poly"][-1]
                        if any(e[0] < EX0 or e[0] > EX1 or e[1] < EY0 or e[1] > EY1 for e in (e0, e1)) and min(poly_dist(q[0], q[1], moat) for q in (e0, e1)) <= 32:
                            taps.append(min((e0, e1), key=lambda e: poly_dist(e[0], e[1], moat)))
                    # feeder + outfall must attach on OPPOSITE faces (centroid-radials pointing apart, dot < 0)
                    # so the ring genuinely flushes rather than two inlets crowding one arc
                    has_outfall = any((taps[i][0] - mcx) * (taps[j][0] - mcx) + (taps[i][1] - mcy) * (taps[j][1] - mcy) < 0 for i in range(len(taps)) for j in range(i + 1, len(taps)))
                    check(
                        "city_moat_has_outfall",
                        has_outfall,
                        "a fed closed city moat has no outfall - a moat with a live feeder must also DRAIN "
                        "(conservation of flow: the surplus overflows if it cannot leave), so an outfall stream "
                        "leaves the LOW rim and runs off-map opposite the feeder to flush the ring; add s.stream(moat rim -> off-map edge)",
                    )
    return _kept(
        locals(),
        (
            'bare',
            'disp_a',
            'disp_b',
            'e',
            'e0',
            'e1',
            'feeders',
            'has_outfall',
            'i',
            'inlet_disp',
            'j',
            'j_arc',
            'loose',
            'mcx',
            'mcy',
            'moat_is_fed',
            'mw',
            'narrow',
            'outlet_disp',
            'p',
            'q',
            'rcum',
            'rdist',
            'ri2',
            'rpts',
            'rv',
            's',
            'taps',
            'wx',
            'wy',
        ),
    )


# RIVER-CITY WATERWORKS (a cargo canal + wharf; only where they are drawn):


def _seg_0563_326__river_c(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.326 (river_c) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        river_c: Any = M.get("river")  # type: ignore[no-redef,unused-ignore]
    return _kept(locals(), ('river_c',))


def _seg_0563_327__canals_c(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.327 (canals_c) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        canals_c = M.get("canals", [])
    return _kept(locals(), ('canals_c',))


def _seg_0563_328__docks_c(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.328 (docks_c) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        docks_c = M.get("docks", [])
    return _kept(locals(), ('docks_c',))


# (1) THE CANAL CONNECTS THE DOCK TO THE WATER, like a street reaching the road: one end
# taps the river OR hands off to the moat (the Suzhou shared-mouth pattern - the city's
# canals communicate with the MOAT, and the moat's own downstream river junction is the
# navigation entrance), the other feeds the in-city dock basin - a canal that stops short
# of the dock is a ditch to nowhere (GM, 2026-07: Nagahara's canal left a visible gap to
# the dock). "Reaches" = the end's bed physically meets the target (within the target's
# half-extent + the canal half-width + a small tolerance).


def _seg_0563_329__city_canal_reaches_dock(
    *,
    M: Any = _UNBOUND,
    _end_near_dock: Any = _UNBOUND,
    _end_near_moat: Any = _UNBOUND,
    _end_near_river: Any = _UNBOUND,
    c: Any = _UNBOUND,
    canal_second_mouths: Any = _UNBOUND,
    canals_c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    chw: Any = _UNBOUND,
    d: Any = _UNBOUND,
    docks_c: Any = _UNBOUND,
    e: Any = _UNBOUND,
    ends: Any = _UNBOUND,
    i: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    moat_for_canal: Any = _UNBOUND,
    mw_for_canal: Any = _UNBOUND,
    river_c: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    unreached: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.329 (city_canal_reaches_dock, city_canal_shares_moat_mouth) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and canals_c:
        moat_for_canal = M.get("moat") or []
        mw_for_canal = M.get("moat_width", 22)

        def _end_near_river(e: Pt) -> bool:
            return bool(river_c) and min(seg_dist(e[0], e[1], river_c["pts"][i], river_c["pts"][i + 1]) for i in range(len(river_c["pts"]) - 1)) <= river_c["w"] / 2 + 14

        def _end_near_moat(e: Pt, chw: float) -> bool:
            # the handoff confluence: the canal end sits ON the moat's stroke (bed meets bed)
            return len(moat_for_canal) >= 2 and poly_dist(e[0], e[1], moat_for_canal) <= mw_for_canal / 2 + chw + 4

        def _end_near_dock(e: Pt, chw: float) -> bool:
            # the canal MOUTH opens into the basin: the endpoint sits at the quay edge or
            # inside it (a visible gap to the dock = not connected), so no slack beyond ~3px
            return any(abs(e[0] - d["x"]) <= d["w"] / 2 + 3 and abs(e[1] - d["y"]) <= d["h"] / 2 + 3 for d in docks_c)

        unreached = []
        for c in canals_c:
            chw = c.get("w", 12) / 2
            ends = (c["poly"][0], c["poly"][-1])
            if not (any(_end_near_river(e) or _end_near_moat(e, chw) for e in ends) and (not docks_c or any(_end_near_dock(e, chw) for e in ends))):
                unreached.append([round(c["poly"][0][0]), round(c["poly"][0][1])])
        check(
            "city_canal_reaches_dock",
            not unreached,
            f"cargo canal(s) not connecting the water to the dock basin: {unreached[:3]} - one end taps the "
            f"river or hands off to the moat (at the water gate), the other must feed the in-city dock "
            f"(extend it to the quay, like a street reaching the road)",
        )
        # (1b) ONE MOUTH ON THE RIVER, NOT TWO (GM 2026-07-23, Nagahara's water-gate corner):
        # where a moat is drawn, a canal must not open its OWN river mouth inside the moat's
        # stroke corridor - Nagahara's canal tapped the river 36 real ft beside the moat's
        # downstream junction and rode collinearly inside the moat arm across the whole bank
        # strip, a smeared doubled channel with a sliver fork at the mouth. Historically the
        # mouths MERGE: the canal hands off to the moat and the moat's junction is the single
        # navigation entrance (see settlements.md river-cities, "one mouth on the river").
        # A canal mouth on open bank AWAY from the moat remains legitimate (real cities had
        # water gates on the river face itself); only the near-duplicate mouth is the defect.
        canal_second_mouths = []
        for c in canals_c:
            chw = c.get("w", 12) / 2
            for e in (c["poly"][0], c["poly"][-1]):
                if _end_near_river(e) and len(moat_for_canal) >= 2 and poly_dist(e[0], e[1], moat_for_canal) <= mw_for_canal / 2 + chw + 8:
                    canal_second_mouths.append([round(e[0]), round(e[1])])
        check(
            "city_canal_shares_moat_mouth",
            not canal_second_mouths,
            f"cargo canal end(s) opening a second river mouth alongside the moat's junction: {canal_second_mouths[:3]} - "
            f"the canal and the moat share ONE mouth (the Suzhou pattern: end the canal ON the moat and let the "
            f"moat's downstream junction be the navigation entrance)",
        )
    return _kept(locals(), ('_end_near_dock', '_end_near_moat', '_end_near_river', 'c', 'canal_second_mouths', 'chw', 'e', 'ends', 'moat_for_canal', 'mw_for_canal', 'unreached'))


# (2) THE WHARF JETTIES REACH THE BANK: a jetty is a finger running out from the river's
# near bank into the water - its landward end must TOUCH the bank, not float mid-stream
# (GM, 2026-07: Nagahara's jetties floated in the middle of the river). The near bank is
# the river centerline offset by half its width toward the city; a jetty's nearest end
# must sit within ~14px of it.


def _seg_0563_330__jetties_c(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.330 (jetties_c) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        jetties_c = M.get("jetties", [])
    return _kept(locals(), ('jetties_c',))


def _seg_0563_331__city_wharf_jetties_on_bank(
    *,
    EX0: Any = _UNBOUND,
    EY0: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cityward_dist: Any = _UNBOUND,
    cx_r: Any = _UNBOUND,
    cy_r: Any = _UNBOUND,
    d: Any = _UNBOUND,
    dc: Any = _UNBOUND,
    e: Any = _UNBOUND,
    floats: Any = _UNBOUND,
    fx: Any = _UNBOUND,
    fy: Any = _UNBOUND,
    i: Any = _UNBOUND,
    j: Any = _UNBOUND,
    jends: Any = _UNBOUND,
    jetties_c: Any = _UNBOUND,
    k: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    p: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    rhw: Any = _UNBOUND,
    river_c: Any = _UNBOUND,
    root: Any = _UNBOUND,
    rp: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    tip: Any = _UNBOUND,
    w: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.331 (city_wharf_jetties_on_bank) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and jetties_c and river_c:
        rp = river_c["pts"]
        rhw = river_c["w"] / 2
        cx_r = sum(p[0] for p in w) / len(w) if len(w) >= 3 else EX0
        cy_r = sum(p[1] for p in w) / len(w) if len(w) >= 3 else EY0
        floats = []
        for j in jetties_c:
            jends = [(j["x"], j["y"]), (j["x"] + math.cos(math.radians(j["rot"])) * j["len"], j["y"] + math.sin(math.radians(j["rot"])) * j["len"])]

            # a jetty runs out from the CITYWARD bank into the water. At least one end must
            # sit on that near bank: within ~14px of the bank line (|dist-to-centerline - rhw|
            # small) AND on the city's side of the centerline (dot of (end - foot) with the
            # direction to the wall centroid is positive).
            def cityward_dist(px: float, py: float) -> tuple[float, bool]:
                # (distance to the river centerline, is-it-on-the-city-side-of-the-centerline)
                k = min(range(len(rp) - 1), key=lambda i: seg_dist(px, py, rp[i], rp[i + 1]))
                fx, fy = seg_closest(px, py, rp[k], rp[k + 1])
                d = math.hypot(px - fx, py - fy)
                cityward = (px - fx) * (cx_r - fx) + (py - fy) * (cy_r - fy) > 0
                return d, cityward

            # a jetty is a FINGER: its ROOT sits at the near bank or just onto land (cityward,
            # >= rhw-6 from the centerline - so the plank visibly connects to the shore, not
            # floating a stride out in the water), and its TIP runs INTO the near-half water
            # (cityward, <= rhw - it neither floats mid-stream nor spans past the far bank).
            root = any((lambda dc: dc[1] and dc[0] >= rhw - 6)(cityward_dist(*e)) for e in jends)
            tip = any((lambda dc: dc[1] and dc[0] <= rhw)(cityward_dist(*e)) for e in jends)
            if not (root and tip):
                floats.append([round(jends[0][0]), round(jends[0][1])])
        check(
            "city_wharf_jetties_on_bank",
            not floats,
            f"wharf jetties floating off the bank: {floats[:3]} - a jetty's landward end must touch the river's near bank, running out into the water from there, not float mid-stream",
        )
    return _kept(locals(), ('cityward_dist', 'cx_r', 'cy_r', 'e', 'floats', 'j', 'jends', 'p', 'rhw', 'root', 'rp', 'tip'))


# (3) THE LOG BOOM IS A SHORE-FAST PEN, NOT STICKS IN THE STREAM (GM 2026-08-02, "it
# just looks like a bunch of logs in the middle of the river"; the research is in
# research/urban-features.md "The log boom"). A boom is a floating fence - anchored to
# nothing it holds nothing. Attested booms anchor to the bank and run ALONG a navigated
# river, the pen between chain and shore (Susquehanna: seven miles along one side;
# St. Croix: log channels beside a navigation channel kept clear by statute); only a
# loose-log CATCH boom on an unnavigated reach ever spans the water (the Kiso tsunaba
# at the gorge mouth), never a port's holding pen. GAP-VERDICT family: both rules below
# measure the pen's DERIVED CORNERS (x/y/rot/len/pen_w, the same local frame the glyph
# draws - bank on local +y) against the river's stroked centerline; a center measure
# would condemn the good bank-hugging pen and pass the mid-stream chain (see the test
# pair). pen_w defaults to the ~14px the pre-2026-08 chain glyph drew.


def _seg_0563_332__booms_c(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.332 (booms_c) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        booms_c = M.get("log_booms", [])
    return _kept(locals(), ('booms_c',))


def _seg_0563_333__log_boom_moored_to_the_bank(
    *,
    M: Any = _UNBOUND,
    adrift_lb: Any = _UNBOUND,
    bmx: Any = _UNBOUND,
    bmy: Any = _UNBOUND,
    bo: Any = _UNBOUND,
    bod_: Any = _UNBOUND,
    boom_off: Any = _UNBOUND,
    booms_c: Any = _UNBOUND,
    box_: Any = _UNBOUND,
    boy_: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cthb: Any = _UNBOUND,
    damming_lb: Any = _UNBOUND,
    fx: Any = _UNBOUND,
    fy: Any = _UNBOUND,
    hlb: Any = _UNBOUND,
    hpb: Any = _UNBOUND,
    i: Any = _UNBOUND,
    k: Any = _UNBOUND,
    lx: Any = _UNBOUND,
    ly: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    moored_lb: Any = _UNBOUND,
    nxb: Any = _UNBOUND,
    nyb: Any = _UNBOUND,
    px_: Any = _UNBOUND,
    py_: Any = _UNBOUND,
    qd_lb: Any = _UNBOUND,
    qdx_lb: Any = _UNBOUND,
    qdy_lb: Any = _UNBOUND,
    quadb: Any = _UNBOUND,
    qx_lb: Any = _UNBOUND,
    qy_lb: Any = _UNBOUND,
    rhwb: Any = _UNBOUND,
    river_c: Any = _UNBOUND,
    rpb: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    sthb: Any = _UNBOUND,
    stray_b: Any = _UNBOUND,
    thb: Any = _UNBOUND,
    yards_b: Any = _UNBOUND,
    yd: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.333 (log_boom_leaves_the_fairway, log_boom_moored_to_the_bank, log_boom_serves_the_lumber_yard) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):  # noqa: SIM102
            if booms_c and river_c:
                rpb = river_c["pts"]
                rhwb = river_c["w"] / 2

                def boom_off(px_: float, py_: float) -> tuple[float, float, float]:
                    # a corner's offset from the river centerline: (dx, dy, distance)
                    k = min(range(len(rpb) - 1), key=lambda i: seg_dist(px_, py_, rpb[i], rpb[i + 1]))
                    fx, fy = seg_closest(px_, py_, rpb[k], rpb[k + 1])
                    return px_ - fx, py_ - fy, math.hypot(px_ - fx, py_ - fy)

                adrift_lb, damming_lb = [], []
                for bo in booms_c:
                    thb = math.radians(float(bo.get("rot", 0.0)))
                    cthb, sthb = math.cos(thb), math.sin(thb)
                    hlb, hpb = float(bo["len"]) / 2, float(bo.get("pen_w", 14.0)) / 2
                    quadb = [(bo["x"] + lx * cthb - ly * sthb, bo["y"] + lx * sthb + ly * cthb) for lx, ly in ((-hlb, hpb), (hlb, hpb), (hlb, -hpb), (-hlb, -hpb))]  # bank-side pair first
                    # the shoreward normal, from the bank-side edge's midpoint
                    bmx, bmy = (quadb[0][0] + quadb[1][0]) / 2, (quadb[0][1] + quadb[1][1]) / 2
                    box_, boy_, bod_ = boom_off(bmx, bmy)
                    nxb, nyb = (box_ / bod_, boy_ / bod_) if bod_ > 0.5 else (0.0, 0.0)
                    # moored_lb: both bank corners ride ON the bank line (centerline + half-width),
                    # shoreward, within ~5px - the pen holds timber between chain and bank
                    moored_lb = bod_ > 0.5
                    for qx_lb, qy_lb in quadb[:2]:
                        qdx_lb, qdy_lb, qd_lb = boom_off(qx_lb, qy_lb)
                        if abs(qd_lb - rhwb) > 5.0 or qdx_lb * nxb + qdy_lb * nyb <= 0:
                            moored_lb = False
                    if not moored_lb:
                        adrift_lb.append([round(bo["x"]), round(bo["y"])])
                    # the fairway is judged even for an adrift boom - the two defects are
                    # independent (the pre-fix Minami chain was both), and the shoreward normal
                    # still points at the boom's own nearest side
                    # fairway: no corner reaches deeper than 40% of the channel off its own bank,
                    # so a clear majority of the width stays open to the wharf traffic
                    for qx_lb, qy_lb in quadb:
                        qdx_lb, qdy_lb, qd_lb = boom_off(qx_lb, qy_lb)
                        if rhwb - (qdx_lb * nxb + qdy_lb * nyb) > 0.8 * rhwb:
                            damming_lb.append([round(bo["x"]), round(bo["y"])])
                            break
                check(
                    "log_boom_moored_to_the_bank",
                    not adrift_lb,
                    f"log boom(s) adrift_lb off the bank: {adrift_lb[:3]} - a boom is a floating fence anchored to fixed ground; its bank edge (local +y) must ride ON the shore line so the pen holds timber between chain and bank, not a chain loose in mid-stream",
                )
                check(
                    "log_boom_leaves_the_fairway",
                    not damming_lb,
                    f"log boom(s) crowding the channel: {damming_lb[:3]} - a holding pen takes at most ~40% of the river's width off its own bank; booms were barred from obstructing navigation, and the full-span catch boom belongs on an unnavigated reach upstream, not at the port",
                )
                # association family (center, deliberately - the ~120px block-scale tolerance
                # dwarfs both footprints): the pen is the timber trade's waterside holding
                # ground, so it rides off the lumber yard's own frontage
                yards_b = M.get("lumber_yards", [])
                if yards_b:
                    stray_b = [[round(bo["x"]), round(bo["y"])] for bo in booms_c if min(math.hypot(bo["x"] - yd["x"], bo["y"] - yd["y"]) for yd in yards_b) > 120.0]
                    check(
                        "log_boom_serves_the_lumber_yard",
                        not stray_b,
                        f"log boom(s) far from any lumber yard: {stray_b[:3]} - boom and zaimokuya are one works; moor the pen off the yard's own bank frontage",
                    )
    return _kept(
        locals(),
        (
            'adrift_lb',
            'bmx',
            'bmy',
            'bo',
            'bod_',
            'boom_off',
            'box_',
            'boy_',
            'cthb',
            'damming_lb',
            'hlb',
            'hpb',
            'lx',
            'ly',
            'moored_lb',
            'nxb',
            'nyb',
            'qd_lb',
            'qdx_lb',
            'qdy_lb',
            'quadb',
            'qx_lb',
            'qy_lb',
            'rhwb',
            'rpb',
            'sthb',
            'stray_b',
            'thb',
            'yards_b',
            'yd',
        ),
    )


# the street network must be CONNECTED - one coherent grid wired to the Imperial
# road, not isolated stubs (ported from the town "no street to nowhere" thinking).


def _seg_0563_334__streets(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.334 (streets) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        streets = M.get("town_streets", [])
    return _kept(locals(), ('streets',))


def _seg_0563_335__city_streets_connected(
    *,
    M: Any = _UNBOUND,
    _w21: Any = _UNBOUND,
    a: Any = _UNBOUND,
    ai: Any = _UNBOUND,
    beds_meet: Any = _UNBOUND,
    bi: Any = _UNBOUND,
    check: Any = _UNBOUND,
    comps: Any = _UNBOUND,
    end: Any = _UNBOUND,
    find2: Any = _UNBOUND,
    i: Any = _UNBOUND,
    ia: Any = _UNBOUND,
    ib: Any = _UNBOUND,
    k: Any = _UNBOUND,
    ki: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    nbr: Any = _UNBOUND,
    near_miss: Any = _UNBOUND,
    parent: Any = _UNBOUND,
    q21: Any = _UNBOUND,
    sa: Any = _UNBOUND,
    sb: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    seg_seg_dist: Any = _UNBOUND,
    slines: Any = _UNBOUND,
    sseg: Any = _UNBOUND,
    st: Any = _UNBOUND,
    streets: Any = _UNBOUND,
    stub: Any = _UNBOUND,
    tol: Any = _UNBOUND,
    widths: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.335 (city_streets_connected, city_streets_no_intersection_stub, city_streets_no_near_miss) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):  # noqa: SIM102
            if streets:
                # at the CAPITAL the suburb streets (wholly outside the rampart - the kashi
                # quay street) are their own lawful networks reached through the gates; the
                # connectivity rule binds the IN-WALL grid (021)
                if scale == "capital" and len(M.get("wall") or []) >= 3:
                    _w21 = M["wall"]
                    streets = [st for st in streets if any(point_in_poly(q21[0], q21[1], _w21) for q21 in st["pts"])]
                sseg = [st["pts"] for st in streets] + ([M["road"]] if M.get("road") else [])
                # width of each segment's paved bed (the road counts as a street here): two streets
                # are CONNECTED only if you can walk between them, i.e. their beds actually overlap -
                # centerline gap < the sum of their half-widths. A street whose end stops even a roadbed
                # short of the next one is a SEPARATE network (you cannot step from one to the other),
                # which is exactly the laborer grid that ended 40px shy of the Imperial road. (Kido ward
                # gates do NOT break this: the street centerline runs on under the gate, uninterrupted.)
                widths = [st.get("w", 18) for st in streets] + ([M.get("road_width", 26)] if M.get("road") else [])
                parent = list(range(len(sseg)))

                def find2(a: int) -> int:
                    while parent[a] != a:
                        parent[a] = parent[parent[a]]
                        a = parent[a]
                    return a

                def beds_meet(ia: int, ib: int) -> bool:  # beds overlap: segments cross, or a centerline endpoint lies
                    sa, sb = sseg[ia], sseg[ib]  # within the two beds' combined half-widths (+2px slack)
                    tol = widths[ia] / 2 + widths[ib] / 2 + 2
                    for i in range(len(sa) - 1):
                        for k in range(len(sb) - 1):
                            if segments_cross(sa[i], sa[i + 1], sb[k], sb[k + 1]):
                                return True
                            if (
                                seg_dist(sa[i][0], sa[i][1], sb[k], sb[k + 1]) < tol
                                or seg_dist(sa[i + 1][0], sa[i + 1][1], sb[k], sb[k + 1]) < tol
                                or seg_dist(sb[k][0], sb[k][1], sa[i], sa[i + 1]) < tol
                                or seg_dist(sb[k + 1][0], sb[k + 1][1], sa[i], sa[i + 1]) < tol
                            ):
                                return True
                    return False

                for ai in range(len(sseg)):
                    for bi in range(ai + 1, len(sseg)):
                        if beds_meet(ai, bi):
                            parent[find2(ai)] = find2(bi)
                comps = {find2(i) for i in range(len(streets))}
                check(
                    "city_streets_connected",
                    len(comps) == 1,
                    f"the city streets form {len(comps)} disconnected groups - a street whose bed does not actually reach another's is a separate network; wire every grid to the Imperial road (extend it until the beds overlap)",
                )

                # two streets that come ALMOST together without meeting read as a mistake - they
                # should either JOIN (cross/touch) or stay clearly apart, never leave a sliver gap
                def seg_seg_dist(a0: Pt, a1: Pt, b0: Pt, b1: Pt) -> float:
                    return min(seg_dist(a0[0], a0[1], b0, b1), seg_dist(a1[0], a1[1], b0, b1), seg_dist(b0[0], b0[1], a0, a1), seg_dist(b1[0], b1[1], a0, a1))

                slines = [st["pts"] for st in streets]
                near_miss = set()
                for ia in range(len(slines)):
                    for ib in range(ia + 1, len(slines)):
                        for i in range(len(slines[ia]) - 1):
                            for ki in range(len(slines[ib]) - 1):
                                if segments_cross(slines[ia][i], slines[ia][i + 1], slines[ib][ki], slines[ib][ki + 1]):
                                    continue
                                if 2 < seg_seg_dist(slines[ia][i], slines[ia][i + 1], slines[ib][ki], slines[ib][ki + 1]) < 30:
                                    near_miss.add((ia, ib))
                check(
                    "city_streets_no_near_miss",
                    not near_miss,
                    f"city street pair(s) that come within a sliver of each other without meeting - close the gap so they join, or separate them: {sorted(near_miss)}",
                )
                # a street that crosses another and then STOPS a little way past it leaves an ugly
                # dangling stub. Fine to cross and keep going (to the next block/edge), or to
                # terminate AT the junction (an L/T corner), but not to overshoot it by a sliver.
                stub = set()
                for ia, sa in enumerate(slines):
                    for end, nbr in ((sa[0], sa[1]), (sa[-1], sa[-2])):
                        for ib, sb in enumerate(slines):
                            if ib == ia:
                                continue
                            for ki in range(len(sb) - 1):
                                if segments_cross(nbr, end, sb[ki], sb[ki + 1]) and 3 < seg_dist(end[0], end[1], sb[ki], sb[ki + 1]) < 50:
                                    stub.add((ia, ib))
                check(
                    "city_streets_no_intersection_stub",
                    not stub,
                    f"city street(s) that cross another and then stop just past it, leaving a dangling stub - end them AT the junction or run them on: {sorted(stub)}",
                )
    return _kept(
        locals(),
        (
            '_w21',
            'ai',
            'beds_meet',
            'bi',
            'comps',
            'end',
            'find2',
            'i',
            'ia',
            'ib',
            'ki',
            'nbr',
            'near_miss',
            'parent',
            'q21',
            'sa',
            'sb',
            'seg_seg_dist',
            'slines',
            'sseg',
            'st',
            'streets',
            'stub',
            'widths',
        ),
    )


# a temple a city street runs UP TO (a street that terminates at its front) marks a
# sacred approach - it needs torii arches on that street, just in front of the temple


def _seg_0563_336__torii(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.336 (torii) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        torii = M.get("torii", [])
    return _kept(locals(), ('torii',))


def _seg_0563_337__pt_rect(*, dx: Any = _UNBOUND, dy: Any = _UNBOUND, meta: Any = _UNBOUND, px: Any = _UNBOUND, py: Any = _UNBOUND, scale: Any = _UNBOUND, t: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.337 (pt_rect) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):

        def pt_rect(px: float, py: float, t: dict[str, Any]) -> float:
            dx = max(t["x"] - t["w"] / 2 - px, 0, px - t["x"] - t["w"] / 2)
            dy = max(t["y"] - t["h"] / 2 - py, 0, py - t["y"] - t["h"] / 2)
            return math.hypot(dx, dy)

    return _kept(locals(), ('pt_rect',))


def _seg_0563_338__no_torii(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.338 (no_torii) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        no_torii = []  # type: ignore[var-annotated]
    return _kept(locals(), ('no_torii',))


def _seg_0563_339__e_2(
    *,
    M: Any = _UNBOUND,
    e: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    no_torii: Any = _UNBOUND,
    pt_rect: Any = _UNBOUND,
    r: Any = _UNBOUND,
    runs_up: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    st: Any = _UNBOUND,
    t: Any = _UNBOUND,
    to: Any = _UNBOUND,
    torii: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.339 (e, no_torii, r, runs_up) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for t in [r for r in M.get("religious", []) if r.get("kind") == "temple"]:
            runs_up = any(min(pt_rect(e[0], e[1], t) for e in (st["pts"][0], st["pts"][-1])) < 28 for st in M.get("town_streets", []))
            if runs_up and not any(math.hypot(to[0] - t["x"], to[1] - t["y"]) < 95 for to in torii):
                no_torii.append(t.get("label"))
    return _kept(locals(), ('e', 'no_torii', 'r', 'runs_up', 'st', 't', 'to'))


def _seg_0563_340__city_temple_approach_has_torii(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, no_torii: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.340 (city_temple_approach_has_torii) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_temple_approach_has_torii", not no_torii, f"temple(s) a city street runs straight up to, with no torii arch in front: {no_torii}")
    return _kept(locals(), ())


# (RETIRED 2026-07-24: city_temple_torii_fill_approach - "an avenue with open room takes
# another arch" - is superseded by the per-temple seeded ROLL: shrine_hall now rolls each
# hall's count on the tier's TORII_WEIGHTS column and records the target on the religious
# rec, so avenue completeness is defined by the roll, not by remaining street room. A
# rolled 1 beside an open street is a hall with one patron gate, not an unfinished avenue.
# torii_match_roll (with torii_count_canonical) now carries the teeth. Same precedent as
# torii_full_avenue_is_seven's retirement when the numerology rule landed.)
# a torii arch stands OVER the street it spans - the street passes beneath it - so a
# torii sitting on a street must be drawn after (higher z than) that street, not under it


def _seg_0563_341__to_under(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.341 (to_under) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        to_under = []  # type: ignore[var-annotated]
    return _kept(locals(), ('to_under',))


def _seg_0563_342__i_5(
    *, M: Any = _UNBOUND, i: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, sp: Any = _UNBOUND, st: Any = _UNBOUND, t: Any = _UNBOUND, to_under: Any = _UNBOUND, torii: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.342 (i, sp, st, t) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for t in torii:
            for st in M.get("town_streets", []):
                sp = st["pts"]
                if any(seg_dist(t[0], t[1], sp[i], sp[i + 1]) <= st.get("w", 24) / 2 + 12 for i in range(len(sp) - 1)) and t[2] <= st.get("z", 0):
                    to_under.append((t[0], t[1]))
    return _kept(locals(), ('i', 'sp', 'st', 't', 'to_under'))


def _seg_0563_343__city_torii_over_streets(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, to_under: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.343 (city_torii_over_streets) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_torii_over_streets", not to_under, f"torii arch(es) drawn UNDER a street they span (the street must pass beneath the arch): {to_under}")
    return _kept(locals(), ())


# no LARGE empty swath inside the walls (ported from wall_hugs_the_town; REBUILT
# footprint-aware, GM 2026-07-23, after Tango shipped a ~230x95px bare pocket just
# inside its north gate that read fully green). The old detector sampled an 80px grid
# and called a cell "used" within 120px of any building CENTER - a single house
# sanitized a 240px-wide disc, so only vast voids could ever fire. Now every claiming
# feature counts with its real FOOTPRINT: building/compound/grove rects, field and
# ground polys, well / stable-yard / torii discs, the road / street / alley / ring-road
# / water rights-of-way, ward fences, the rampart + its patrol strip, and the pond. A
# 32px grid marks cells >= 20px clear of ALL of them as dead ground; any contiguous
# dead cluster >= 4,000 px2 of core fails. Calibration (2026-07-23, pool-wide dry-run,
# settlements.md): Tango's north-gate pocket measures 6,144 px2 of core; the largest
# LEGITIMATE opens anywhere else measure 2,048 (Tango) / 1,024 (Nagahara), so the
# threshold sits between with ~2x headroom both ways. A city keeps SOME open ground,
# but every deliberate open is CLAIMED by a feature record (a working stable yard /
# animal ground, a right-of-way, a field); ground claimed by nothing, at
# wall-protected premium, would not have been left bare.


def _seg_0563_344__ES_MARGIN(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.344 (ES_MARGIN, ES_MIN, ES_STEP) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        ES_STEP, ES_MARGIN, ES_MIN = 32, 20.0, 4000
    return _kept(locals(), ('ES_MARGIN', 'ES_MIN', 'ES_STEP'))


def _seg_0563_345__es_rects(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.345 (es_rects) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_rects: list[tuple[float, float, float, float]] = []  # type: ignore[no-redef,unused-ignore]
    return _kept(locals(), ('es_rects',))


def _seg_0563_346__es_s(*, M: Any = _UNBOUND, es_s: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.346 (es_s, es_singles) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_singles = [es_s for es_s in [M.get("governor_mansion"), *(M.get("theater_stage") or [])] if isinstance(es_s, dict)]
    return _kept(locals(), ('es_s', 'es_singles'))


def _seg_0563_347__es_grp(
    *,
    M: Any = _UNBOUND,
    es_grp: Any = _UNBOUND,
    es_hh: Any = _UNBOUND,
    es_hw: Any = _UNBOUND,
    es_k: Any = _UNBOUND,
    es_o: Any = _UNBOUND,
    es_rects: Any = _UNBOUND,
    es_singles: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.347 (es_grp, es_hh, es_hw, es_k) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for es_grp in [
            M.get(es_k, []) or []
            for es_k in (
                "buildings",
                "flophouses",
                "storehouses",
                "manors",
                "ministries",
                "religious",
                "inspection_stations",
                "byres",
                "cemeteries",
                "mausoleums",
                "merchant_estates",
                "farm_sheds",
                "gardens",
                "threshing_yards",
                "fire_towers",
                "drum_towers",
                "gate_structs",
                "groves",
                "breweries",
                "dye_yards",
                "lumber_yards",
                "oil_presses",
                "pawnshops",
                "bathhouses",
                "kilns",
                "tanning_yards",
                "martial_halls",
                "dojos",
            )
        ] + [houses, es_singles]:
            for es_o in es_grp:
                es_hw, es_hh = es_o["w"] / 2, es_o["h"] / 2
                if es_o.get("rot"):
                    es_hw = es_hh = math.hypot(es_hw, es_hh)
                es_rects.append((es_o["x"], es_o["y"], es_hw, es_hh))
    return _kept(locals(), ('es_grp', 'es_hh', 'es_hw', 'es_k', 'es_o', 'es_rects'))


def _seg_0563_348__es_discs(*, M: Any = _UNBOUND, es_o: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.348 (es_discs, es_o) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_discs = [(es_o["x"], es_o["y"], es_o.get("r", 8.0)) for es_o in M.get("wells", []) + M.get("stable_yards", [])]
    return _kept(locals(), ('es_discs', 'es_o'))


def _seg_0563_349__es_discs_1(*, M: Any = _UNBOUND, es_discs: Any = _UNBOUND, es_t: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.349 (es_discs, es_t) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_discs += [(es_t[0], es_t[1], 14.0) for es_t in M.get("torii", [])]
    return _kept(locals(), ('es_discs', 'es_t'))


def _seg_0563_350__es_polys(*, M: Any = _UNBOUND, f: Any = _UNBOUND, fields: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.350 (es_polys, f) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_polys = [f["outline"] for f in fields] + list((M.get("comb_floors") or {}).values())
    return _kept(locals(), ('es_polys', 'f'))


def _seg_0563_351__es_k(*, M: Any = _UNBOUND, es_k: Any = _UNBOUND, es_o: Any = _UNBOUND, es_polys: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.351 (es_k, es_o, es_polys) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for es_k in ("dry_plots", "pastures", "commons", "marshes", "forest_patches", "village_groves", "clearings"):
            es_polys += [es_o["poly"] for es_o in M.get(es_k, []) or []]
    return _kept(locals(), ('es_k', 'es_o', 'es_polys'))


def _seg_0563_352__es_lines(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.352 (es_lines) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_lines: list[tuple[list[Any], float]] = [(w, 20.0)]  # type: ignore[no-redef,unused-ignore]  # the rampart + its patrol strip is claimed ground
    return _kept(locals(), ('es_lines',))


def _seg_0563_353__es_lines_1(*, M: Any = _UNBOUND, es_lines: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.353 (es_lines) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and M.get("road"):
        es_lines.append((M["road"], M.get("road_width", 30) / 2))
    return _kept(locals(), ('es_lines',))


def _seg_0563_354__es_lines_2(*, M: Any = _UNBOUND, es_lines: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.354 (es_lines) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and M.get("ring_road"):
        es_lines.append((M["ring_road"], M.get("ring_road_width", 24) / 2))
    return _kept(locals(), ('es_lines',))


def _seg_0563_355__es_dw(
    *, M: Any = _UNBOUND, es_dw: Any = _UNBOUND, es_grp2: Any = _UNBOUND, es_lines: Any = _UNBOUND, es_o: Any = _UNBOUND, es_pk: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.355 (es_dw, es_grp2, es_lines, es_o) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for es_grp2, es_pk, es_dw in (
            (M.get("roads", []), "pts", 24),
            (M.get("town_streets", []), "pts", 24),
            (M.get("alleys", []), "pts", 12),
            (M.get("streams", []), "poly", 12),
            (M.get("channels", []), "poly", 8),
        ):
            es_lines += [(es_o[es_pk], es_o.get("w", es_dw) / 2) for es_o in es_grp2 or []]
    return _kept(locals(), ('es_dw', 'es_grp2', 'es_lines', 'es_o', 'es_pk'))


def _seg_0563_356__es_lines_3(*, M: Any = _UNBOUND, es_lines: Any = _UNBOUND, es_o: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.356 (es_lines, es_o) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_lines += [(es_o["boundary"], 8.0) for es_o in M.get("wards", [])]
    return _kept(locals(), ('es_lines', 'es_o'))


def _seg_0563_357__es_pond(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.357 (es_pond) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_pond = M.get("pond")
    return _kept(locals(), ('es_pond',))


def _seg_0563_358__es_wx0(*, meta: Any = _UNBOUND, p: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.358 (es_wx0, es_wy0, p) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_wx0, es_wy0 = min(p[0] for p in w), min(p[1] for p in w)
    return _kept(locals(), ('es_wx0', 'es_wy0', 'p'))


def _seg_0563_359__es_wx1(*, meta: Any = _UNBOUND, p: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.359 (es_wx1, es_wy1, p) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_wx1, es_wy1 = max(p[0] for p in w), max(p[1] for p in w)
    return _kept(locals(), ('es_wx1', 'es_wy1', 'p'))


def _seg_0563_360__es_ci0(*, ES_STEP: Any = _UNBOUND, es_wx0: Any = _UNBOUND, es_wy0: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.360 (es_ci0, es_cj0) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_ci0, es_cj0 = int(es_wx0 // ES_STEP), int(es_wy0 // ES_STEP)
    return _kept(locals(), ('es_ci0', 'es_cj0'))


def _seg_0563_361__es_ci1(*, ES_STEP: Any = _UNBOUND, es_wx1: Any = _UNBOUND, es_wy1: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.361 (es_ci1, es_cj1) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_ci1, es_cj1 = int(es_wx1 // ES_STEP) + 1, int(es_wy1 // ES_STEP) + 1
    return _kept(locals(), ('es_ci1', 'es_cj1'))


def _seg_0563_362__es_cells(
    *,
    ES_STEP: Any = _UNBOUND,
    bx0: Any = _UNBOUND,
    bx1: Any = _UNBOUND,
    by0: Any = _UNBOUND,
    by1: Any = _UNBOUND,
    es_ci0: Any = _UNBOUND,
    es_ci1: Any = _UNBOUND,
    es_cj0: Any = _UNBOUND,
    es_cj1: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.362 (es_cells) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):

        def es_cells(bx0: float, by0: float, bx1: float, by1: float) -> list[tuple[int, int]]:
            """Grid cells whose sample point falls inside the bbox (clamped to the wall window)."""
            return [
                (eci, ecj)
                for eci in range(max(es_ci0, math.ceil(bx0 / ES_STEP)), min(es_ci1, math.floor(bx1 / ES_STEP)) + 1)
                for ecj in range(max(es_cj0, math.ceil(by0 / ES_STEP)), min(es_cj1, math.floor(by1 / ES_STEP)) + 1)
            ]

    return _kept(locals(), ('es_cells',))


def _seg_0563_363__es_covered(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.363 (es_covered) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_covered: set[tuple[int, int]] = set()  # type: ignore[no-redef,unused-ignore]
    return _kept(locals(), ('es_covered',))


def _seg_0563_364__es_covered_1(
    *,
    ES_MARGIN: Any = _UNBOUND,
    es_cells: Any = _UNBOUND,
    es_covered: Any = _UNBOUND,
    es_rects: Any = _UNBOUND,
    es_rhh: Any = _UNBOUND,
    es_rhw: Any = _UNBOUND,
    es_rx: Any = _UNBOUND,
    es_ry: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.364 (es_covered, es_rhh, es_rhw, es_rx) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for es_rx, es_ry, es_rhw, es_rhh in es_rects:
            es_covered.update(es_cells(es_rx - es_rhw - ES_MARGIN, es_ry - es_rhh - ES_MARGIN, es_rx + es_rhw + ES_MARGIN, es_ry + es_rhh + ES_MARGIN))
    return _kept(locals(), ('es_covered', 'es_rhh', 'es_rhw', 'es_rx', 'es_ry'))


def _seg_0563_365__c_2(
    *,
    ES_MARGIN: Any = _UNBOUND,
    ES_STEP: Any = _UNBOUND,
    c: Any = _UNBOUND,
    es_cells: Any = _UNBOUND,
    es_covered: Any = _UNBOUND,
    es_discs: Any = _UNBOUND,
    es_dr: Any = _UNBOUND,
    es_dx: Any = _UNBOUND,
    es_dy: Any = _UNBOUND,
    es_rr: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.365 (c, es_covered, es_dr, es_dx) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for es_dx, es_dy, es_dr in es_discs:
            es_rr = es_dr + ES_MARGIN
            es_covered.update([c for c in es_cells(es_dx - es_rr, es_dy - es_rr, es_dx + es_rr, es_dy + es_rr) if (c[0] * ES_STEP - es_dx) ** 2 + (c[1] * ES_STEP - es_dy) ** 2 <= es_rr * es_rr])
    return _kept(locals(), ('c', 'es_covered', 'es_dr', 'es_dx', 'es_dy', 'es_rr'))


def _seg_0563_366__c_3(
    *,
    ES_MARGIN: Any = _UNBOUND,
    ES_STEP: Any = _UNBOUND,
    c: Any = _UNBOUND,
    es_a: Any = _UNBOUND,
    es_b: Any = _UNBOUND,
    es_cells: Any = _UNBOUND,
    es_covered: Any = _UNBOUND,
    es_hwid: Any = _UNBOUND,
    es_i: Any = _UNBOUND,
    es_lines: Any = _UNBOUND,
    es_pts: Any = _UNBOUND,
    es_rr: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.366 (c, es_a, es_b, es_covered) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for es_pts, es_hwid in es_lines:
            es_rr = es_hwid + ES_MARGIN
            for es_i in range(len(es_pts) - 1):
                es_a, es_b = es_pts[es_i], es_pts[es_i + 1]
                es_covered.update(
                    [
                        c
                        for c in es_cells(min(es_a[0], es_b[0]) - es_rr, min(es_a[1], es_b[1]) - es_rr, max(es_a[0], es_b[0]) + es_rr, max(es_a[1], es_b[1]) + es_rr)
                        if c not in es_covered and seg_dist(c[0] * ES_STEP, c[1] * ES_STEP, es_a, es_b) <= es_rr
                    ]
                )
    return _kept(locals(), ('c', 'es_a', 'es_b', 'es_covered', 'es_hwid', 'es_i', 'es_pts', 'es_rr'))


def _seg_0563_367__c_4(
    *,
    ES_STEP: Any = _UNBOUND,
    c: Any = _UNBOUND,
    es_cells: Any = _UNBOUND,
    es_covered: Any = _UNBOUND,
    es_p: Any = _UNBOUND,
    es_polys: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    q: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.367 (c, es_covered, es_p, q) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for es_p in es_polys:
            es_covered.update(
                [
                    c
                    for c in es_cells(min(q[0] for q in es_p), min(q[1] for q in es_p), max(q[0] for q in es_p), max(q[1] for q in es_p))
                    if c not in es_covered and point_in_poly(c[0] * ES_STEP, c[1] * ES_STEP, es_p)
                ]
            )
    return _kept(locals(), ('c', 'es_covered', 'es_p', 'q'))


def _seg_0563_368__c_5(
    *, ES_STEP: Any = _UNBOUND, c: Any = _UNBOUND, es_cells: Any = _UNBOUND, es_covered: Any = _UNBOUND, es_pond: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.368 (c, es_covered) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and es_pond:
        es_covered.update(
            [
                c
                for c in es_cells(es_pond[0] - es_pond[2] * 1.2, es_pond[1] - es_pond[3] * 1.2, es_pond[0] + es_pond[2] * 1.2, es_pond[1] + es_pond[3] * 1.2)
                if c not in es_covered and in_ellipse(c[0] * ES_STEP, c[1] * ES_STEP, es_pond, 1.15)
            ]
        )
    return _kept(locals(), ('c', 'es_covered'))


# the CITADEL claims its ground (021): a castle court is deliberately BLANK (the
# sync doctrine) - blank is not unclaimed, and its moat band goes with it


def _seg_0563_369__es_ca(*, M: Any = _UNBOUND, es_ca: Any = _UNBOUND, es_cells: Any = _UNBOUND, es_covered: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.369 (es_ca, es_covered) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for es_ca in M.get("castles", []):
            es_covered.update(es_cells(es_ca["x"] - es_ca["w"] / 2 - 45, es_ca["y"] - es_ca["h"] / 2 - 45, es_ca["x"] + es_ca["w"] / 2 + 45, es_ca["y"] + es_ca["h"] / 2 + 45))
    return _kept(locals(), ('es_ca', 'es_covered'))


def _seg_0563_370__c_6(
    *,
    ES_STEP: Any = _UNBOUND,
    c: Any = _UNBOUND,
    es_cells: Any = _UNBOUND,
    es_covered: Any = _UNBOUND,
    es_wx0: Any = _UNBOUND,
    es_wx1: Any = _UNBOUND,
    es_wy0: Any = _UNBOUND,
    es_wy1: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    w: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.370 (c, es_empty) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_empty = {c for c in es_cells(es_wx0, es_wy0, es_wx1, es_wy1) if c not in es_covered and point_in_poly(c[0] * ES_STEP, c[1] * ES_STEP, w)}
    return _kept(locals(), ('c', 'es_empty'))


def _seg_0563_371__es_seen(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.371 (es_seen) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_seen: set[tuple[int, int]] = set()  # type: ignore[no-redef,unused-ignore]
    return _kept(locals(), ('es_seen',))


def _seg_0563_372__es_flagged(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.372 (es_flagged) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_flagged: list[tuple[int, tuple[int, int]]] = []  # type: ignore[no-redef,unused-ignore]
    return _kept(locals(), ('es_flagged',))


def _seg_0563_373__c_7(
    *,
    ES_MIN: Any = _UNBOUND,
    ES_STEP: Any = _UNBOUND,
    c: Any = _UNBOUND,
    es_area: Any = _UNBOUND,
    es_c: Any = _UNBOUND,
    es_cell: Any = _UNBOUND,
    es_comp: Any = _UNBOUND,
    es_di: Any = _UNBOUND,
    es_dj: Any = _UNBOUND,
    es_empty: Any = _UNBOUND,
    es_flagged: Any = _UNBOUND,
    es_nb: Any = _UNBOUND,
    es_seen: Any = _UNBOUND,
    es_stack: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.373 (c, es_area, es_c, es_cell) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for es_cell in es_empty:
            if es_cell in es_seen:
                continue
            es_stack, es_comp = [es_cell], []
            es_seen.add(es_cell)
            while es_stack:
                es_c = es_stack.pop()
                es_comp.append(es_c)
                for es_di, es_dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    es_nb = (es_c[0] + es_di, es_c[1] + es_dj)
                    if es_nb in es_empty and es_nb not in es_seen:
                        es_seen.add(es_nb)
                        es_stack.append(es_nb)
            es_area = len(es_comp) * ES_STEP * ES_STEP
            if es_area >= ES_MIN:
                es_flagged.append((es_area, (sum(c[0] for c in es_comp) * ES_STEP // len(es_comp), sum(c[1] for c in es_comp) * ES_STEP // len(es_comp))))
    return _kept(locals(), ('c', 'es_area', 'es_c', 'es_cell', 'es_comp', 'es_di', 'es_dj', 'es_flagged', 'es_nb', 'es_seen', 'es_stack'))


def _seg_0563_374__es_flagged_1(*, es_flagged: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.374 (es_flagged) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_flagged.sort(reverse=True)
    return _kept(locals(), ('es_flagged',))


def _seg_0563_375__es_ftpx(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.375 (es_ftpx) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        es_ftpx = meta.get("ftpx", 3)
    return _kept(locals(), ('es_ftpx',))


def _seg_0563_376__city_no_large_empty_space(
    *, check: Any = _UNBOUND, ea: Any = _UNBOUND, ec: Any = _UNBOUND, es_flagged: Any = _UNBOUND, es_ftpx: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.376 (city_no_large_empty_space) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):
            check(
                "city_no_large_empty_space",
                not es_flagged,
                "contiguous UNCLAIMED open ground inside the walls: "
                + "; ".join(f"~{ea} px2 of dead core (~{ea * es_ftpx * es_ftpx / 43560:.1f} ac) centered {ec}" for ea, ec in es_flagged[:3])
                + " - land inside a wall is at a premium; fill it (extend a quarter / drop in a neighborhood) or claim it as deliberate working ground, e.g. s.animal_ground(...) for extra caravan hitching space near a gate (settlements.md)",
            )
    return _kept(locals(), ('ea', 'ec'))
