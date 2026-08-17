"""Gate segments (city labels and works; keys 0563_252-0563_308) - bodies verbatim, registry order preserved."""

import math
from collections.abc import Sequence
from typing import Any

from .common_01_geometry import point_in_poly, poly_dist, seg_dist
from .common_02_overlap_policy import footprint_on_line
from .common_03_capacity import _UNBOUND, DWELLING_KINDS, _kept

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
