"""Gate segments (quarters and civic reserve; keys 0038-0051) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from .common_01_geometry import (
    _struct_rect,
    largest_empty_gap,
    point_in_poly,
    poly_area,
    rect_corners,
    seg_dist,
    sweep_hi,
)
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
