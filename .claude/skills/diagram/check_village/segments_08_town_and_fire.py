"""Gate segments (town and fire) - bodies verbatim from check_village.py (feature 024 package split; registry order preserved)."""

import math
from typing import Any

from waterfields import BANK_MARGIN, drain_bank_clearance, polyline_cum, supply_bank_clearance

from .common_01_geometry import CLAN_FORTUNES, Poly, Pt, point_in_poly, pt_to_rect, seg_closest, seg_dist, within_edge_gap
from .common_02_overlap_policy import GridIndex, check_fire_features, check_theater_stage, in_ellipse
from .common_03_capacity import _UNBOUND, DWELLING_KINDS, _fronts_route, _kept

# THE POND CONNECTS TO THE FIELD's WATER, matching its role. A SOURCE pond (the default) must FEED the
# field through an irrigation channel that touches the pond; a DRAINAGE pond (meta pond_role="drainage",
# a reservoir below the fields) must be REACHED BY the field's drain - the drain must actually run into
# the pond, not stop short of it (the disconnected-drain bug). Either way SOME watercourse endpoint sits
# in the pond.


def _seg_0513__pond_connected_to_field(
    *,
    M: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    connected: Any = _UNBOUND,
    d: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    p: Any = _UNBOUND,
    poly: Any = _UNBOUND,
    pond: Any = _UNBOUND,
    wc: Any = _UNBOUND,
    why: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 513 (pond_connected_to_field) - body verbatim from the legacy gate() (feature 022)."""
    if pond:
        if pond and meta.get("pond_role", "source") == "source":
            wc = [c["poly"] for c in M.get("channels", []) if "pond" in ((c["frm"] or {}).get("kind"), (c["to"] or {}).get("kind"))]
            why = "a source pond must FEED the field through an irrigation channel, but none connects to the pond"
        else:
            wc = [d["poly"] for d in M.get("field_ditches", []) if d.get("role") == "drain"] + [
                c["poly"] for c in M.get("channels", []) if "pond" in ((c["frm"] or {}).get("kind"), (c["to"] or {}).get("kind"))
            ]
            why = "a drainage pond is fed by the field's DRAIN, but the drain does not reach the pond (it stops short of the water)"
        connected = any(in_ellipse(p[0], p[1], pond, 1.12) for poly in wc for p in (poly[0], poly[-1]))
        check("pond_connected_to_field", connected, why)
    return _kept(locals(), ('c', 'connected', 'd', 'p', 'poly', 'wc', 'why'))


# AN IRRIGATION POND DOES NOT SIT ON THE PADDIES. A pond WIRED to the field's water (a source reservoir at
# the head, or a drainage tameike at the low foot) is a distinct body of water BESIDE or BELOW the field,
# joined to the crop by a channel - never laid OVER the paddies. So its ellipse must not overlap the field
# envelope (no rim point inside a field, no field vertex inside it). A DECORATIVE pond not connected to the
# field's water (a city garden pond) is exempt - it is not part of the irrigation system.


def _seg_0514___pond_wired(*, M: Any = _UNBOUND, c: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 514 (_pond_wired, c) - body verbatim from the legacy gate() (feature 022)."""
    _pond_wired = any("pond" in ((c.get("frm") or {}).get("kind"), (c.get("to") or {}).get("kind")) for c in M.get("channels", []))
    return _kept(locals(), ('_pond_wired', 'c'))


def _seg_0515__pond_clear_of_field(
    *,
    _peri: Any = _UNBOUND,
    _pond_wired: Any = _UNBOUND,
    a: Any = _UNBOUND,
    check: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    fo: Any = _UNBOUND,
    i: Any = _UNBOUND,
    pond: Any = _UNBOUND,
    pond_on_field: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    v: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 515 (pond_clear_of_field) - body verbatim from the legacy gate() (feature 022)."""
    if pond and fields and _pond_wired:
        _peri = [(pond[0] + pond[2] * math.cos(a), pond[1] + pond[3] * math.sin(a)) for a in [i * math.pi / 12 for i in range(24)]]
        pond_on_field = any(point_in_poly(px, py, fo["outline"]) for px, py in _peri for fo in fields) or any(in_ellipse(v[0], v[1], pond, 1.0) for fo in fields for v in fo["outline"])
        check(
            "pond_clear_of_field",
            not pond_on_field,
            "the pond overlaps the paddy field - a pond is a distinct water body beside/below the field, joined to it by a channel, not laid over the crop (site the pond clear of the field envelope)",
        )
    return _kept(locals(), ('_peri', 'a', 'fo', 'i', 'pond_on_field', 'px', 'py', 'v'))


# DEFENSIVE MARSHLAND GIRDS A FORTIFIED PERIMETER (role="defense"; settlements.md 'Defensive marshland').
# An engineered wet belt is military ground (the Song Hebei frontier marsh-pond belt, numajiro "marsh
# castles", the flooded-paddy glacis around castle towns): it exists to deny an attacker footing AT THE
# WALL, so it (1) only appears on a map that HAS a wall or moat, (2) stays OUTSIDE the wall circuit (the
# inundation protects the wall - inside is the town), and (3) ABUTS the perimeter, within ~60px of the
# wall or moat line (~180 ft at city scale: the moat's outer bank + a patrol berm) - a wet belt DETACHED
# from the fortification defends nothing. Degenerate (<3-point) polys carry no area to test - skipped.


def _seg_0516__defense_marshes(*, M: Any = _UNBOUND, m: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 516 (defense_marshes, m) - body verbatim from the legacy gate() (feature 022)."""
    defense_marshes = [m for m in M.get("marshes", []) if m.get("role") == "defense" and len(m.get("poly") or []) >= 3]
    return _kept(locals(), ('defense_marshes', 'm'))


def _seg_0517__defense_marsh_girds_the_walls(
    *,
    M: Any = _UNBOUND,
    bad_def: Any = _UNBOUND,
    check: Any = _UNBOUND,
    defense_marshes: Any = _UNBOUND,
    i: Any = _UNBOUND,
    loc_: Any = _UNBOUND,
    m: Any = _UNBOUND,
    mp_: Any = _UNBOUND,
    perim_: Any = _UNBOUND,
    pl: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 517 (defense_marsh_girds_the_walls) - body verbatim from the legacy gate() (feature 022)."""
    if defense_marshes:
        perim_ = [pl for pl in (M.get("wall"), M.get("moat")) if pl]
        bad_def = []
        for m in defense_marshes:
            mp_ = m["poly"]
            loc_ = (round(m["x"]), round(m["y"]))
            if not perim_:
                bad_def.append((loc_, "map has no wall or moat - a defensive inundation defends a fortified perimeter"))
            elif M.get("wall") and any(point_in_poly(px, py, M["wall"]) for px, py in mp_):
                bad_def.append((loc_, "reaches INSIDE the wall circuit"))
            elif min(seg_dist(px, py, pl[i], pl[i + 1]) for pl in perim_ for px, py in mp_ for i in range(len(pl) - 1)) > 60:
                bad_def.append((loc_, "detached from the perimeter - the belt begins at the moat's outer bank / wall foot"))
        check(
            "defense_marsh_girds_the_walls",
            not bad_def,
            f"defensive marsh misplaced: {bad_def[:3]} - an engineered wet belt lies OUTSIDE the walls, hugging the moat/wall perimeter it defends",
        )
    return _kept(locals(), ('bad_def', 'i', 'loc_', 'm', 'mp_', 'perim_', 'pl', 'px', 'py'))


# DRAINAGE FLOWS DOWNHILL (matches the map's configured slope). We do NOT require the drain to RUN
# downhill - a collector (akusui) legitimately runs ACROSS the low margin, ~perpendicular to the fall,
# to gather runoff from every cascade column; a downhill-running drain would collect nothing. What we
# DO require is that the water never runs UPHILL: the drain's OUTFALL (the end that discharges to the
# brook / off-map) must be the lower-ground end, and the discharge brook must head downhill. `fall` =
# projection onto the downhill unit vector (meta.down_deg); higher fall = further downhill = lower ground.


def _seg_0518___dd(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 518 (_dd) - body verbatim from the legacy gate() (feature 022)."""
    _dd = M["meta"].get("down_deg")
    return _kept(locals(), ('_dd',))


# PER-FIELD FALL (GM 2026-07-25). A settlement ringed by farmland genuinely drains SEVERAL WAYS
# AT ONCE - Tango's fans fall across a 210 deg spread (15 to 225), Nagahara's across 170 - so no
# single map-level down_deg can describe it, and a sweep of every bearing at 10 deg steps found
# none that satisfied these checks on either city. Each drain is therefore judged against ITS OWN
# field's fall, which `field_ditches` already makes possible (every ditch records its `field`).
# Maps that declare a map-level down_deg and no per-field slopes are UNCHANGED: the lookup simply
# falls back to the map value, so every hamlet/village/town behaves exactly as before.


def _seg_0519___field_dd(*, M: Any = _UNBOUND, f: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 519 (_field_dd, f) - body verbatim from the legacy gate() (feature 022)."""
    _field_dd = {f.get("name"): f["down_deg"] for f in M.get("fields", []) if f.get("down_deg") is not None}
    return _kept(locals(), ('_field_dd', 'f'))


def _seg_0520___dv(*, _dd: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 520 (_dv) - body verbatim from the legacy gate() (feature 022)."""
    _dv = (math.cos(math.radians(_dd)), math.sin(math.radians(_dd))) if _dd is not None else (0.0, 0.0)
    return _kept(locals(), ('_dv',))


def _seg_0521___dvec_of() -> dict[str, Any]:
    """Gate segment 521 (_dvec_of) - body verbatim from the legacy gate() (feature 022)."""

    def _dvec_of(deg: float) -> tuple[float, float]:
        return (math.cos(math.radians(deg)), math.sin(math.radians(deg)))

    return _kept(locals(), ('_dvec_of',))


def _seg_0522___ditch_dv(*, _d: Any = _UNBOUND, _dd: Any = _UNBOUND, _dvec_of: Any = _UNBOUND, _field_dd: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 522 (_ditch_dv) - body verbatim from the legacy gate() (feature 022)."""

    def _ditch_dv(fd_: dict[str, Any]) -> tuple[float, float] | None:
        """The fall vector to judge THIS ditch by: its own field's, else the map's, else none."""
        _d = _field_dd.get(fd_.get("field"), _dd)
        return None if _d is None else _dvec_of(_d)

    return _kept(locals(), ('_ditch_dv',))


def _seg_0523_000__fall(*, _dd: Any = _UNBOUND, _dv: Any = _UNBOUND, _field_dd: Any = _UNBOUND, p: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0523.000 (fall) - body verbatim from _seg_0523__drain_flows_downhill (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if _dd is not None or _field_dd:

        def fall(p: Pt) -> float:
            return p[0] * _dv[0] + p[1] * _dv[1]  # type: ignore[no-any-return]

    return _kept(locals(), ('fall',))


# REED MARSH sits on the LOW, downhill ground below the paddy (wet rice is reclaimed FROM marsh; the un-
# reclaimed valley toe stays wetland). So a marsh must lie DOWNHILL of the field it borders - its centroid's
# fall must exceed the field centroid's; a marsh on the high/dry side would read wrong. WHY: settlements.md 'Marsh'.


def _seg_0523_001__m(*, M: Any = _UNBOUND, _dd: Any = _UNBOUND, _field_dd: Any = _UNBOUND, m: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0523.001 (m, marshes_) - body verbatim from _seg_0523__drain_flows_downhill (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if _dd is not None or _field_dd:
        marshes_ = [
            m for m in M.get("marshes", []) if m.get("role") not in ("pond_fringe", "defense", "waterside")
        ]  # a pond's reedy MARGIN is a water fringe, a DEFENSIVE belt hugs the fortified perimeter wherever the wall runs (defense_marsh_girds_the_walls owns it), and a polder's WATERSIDE fringe surrounds the dike regardless of fall (the polder floor is below the outside water level; polder_waterward_flanks_wet owns it) - none of these is the low valley toe
    return _kept(locals(), ('m', 'marshes_'))


def _seg_0523_002__marsh_on_low_ground(
    *,
    M: Any = _UNBOUND,
    _dd: Any = _UNBOUND,
    _field_dd: Any = _UNBOUND,
    check: Any = _UNBOUND,
    fall: Any = _UNBOUND,
    fcen: Any = _UNBOUND,
    fol: Any = _UNBOUND,
    high_marsh: Any = _UNBOUND,
    m: Any = _UNBOUND,
    marshes_: Any = _UNBOUND,
    p: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0523.002 (marsh_on_low_ground) - body verbatim from _seg_0523__drain_flows_downhill (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if (_dd is not None or _field_dd) and marshes_ and M.get("fields"):
        fol = M["fields"][0]["outline"]
        fcen = (sum(p[0] for p in fol) / len(fol), sum(p[1] for p in fol) / len(fol))
        high_marsh = [(round(m["x"]), round(m["y"])) for m in marshes_ if fall((m["x"], m["y"])) <= fall(fcen)]
        check(
            "marsh_on_low_ground",
            not high_marsh,
            f"reed marsh {high_marsh[:2]} sits UPHILL of the paddy - marsh is the LOW, undrained valley toe below the field (wet rice is reclaimed from marsh), so it must lie downhill (higher fall)",
        )
    return _kept(locals(), ('fcen', 'fol', 'high_marsh', 'm', 'p'))


# A WELLHEAD IS NOT SUNK IN A BOG (settlement-review, 2026-08-12: Akagahara's SE well stood among
# the drawn reed glyphs, ~50 ft from the drainage pond). You do not dig a draw-well in standing
# surface water - a well wants a water TABLE under dry ground you can stand a curb and a windlass
# on; in the bog the water is already at the surface and foul with it.
#
# MEASURED AGAINST THE GROUND BELOW ALL CULTIVATION, not against the toe polygon, and the
# difference is the whole check. `hinterland()`'s band deliberately starts `pad` (90 px) ABOVE the
# crop's lowest point so the reeds tuck under the field - so the polygon's uphill lip overlaps
# ground that is farmed, built on, and drawn with no reeds at all (the scatter skips paddy and the
# settlement halo). Testing the polygon alone would flag every wellhead on that lip, the same
# phantom-geometry trap `fields_clear_of_road` fell into against a fan's invisible envelope tail.
# Below the crop's lowest point there is no ambiguity: that ground is reed flat and drawn as one.
#
# AND IT LIVES HERE, at every scale, beside `marsh_on_low_ground`. It was first written inside the
# village-scale burial-ground section, where a HAMLET never reaches it - so it sat green on the
# very map it was written for. "A check that never runs looks exactly like a check that passes"
# (this skill's CLAUDE.md), demonstrated on the day the entry was re-read.


def _seg_0523_003__m_1(*, M: Any = _UNBOUND, _dd: Any = _UNBOUND, _field_dd: Any = _UNBOUND, m: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0523.003 (m, wet_toe) - body verbatim from _seg_0523__drain_flows_downhill (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if _dd is not None or _field_dd:
        wet_toe = [m["poly"] for m in M.get("marshes", []) if m.get("role") == "toe" and m.get("poly")]
    return _kept(locals(), ('m', 'wet_toe'))


def _seg_0523_004__wells_off_the_wet_toe(
    *,
    M: Any = _UNBOUND,
    _dd: Any = _UNBOUND,
    _dv: Any = _UNBOUND,
    _field_dd: Any = _UNBOUND,
    _wt_cult: Any = _UNBOUND,
    _wt_low: Any = _UNBOUND,
    _wt_reedy: Any = _UNBOUND,
    _wt_u: Any = _UNBOUND,
    _wt_uhi: Any = _UNBOUND,
    _wt_ulo: Any = _UNBOUND,
    _wt_us: Any = _UNBOUND,
    check: Any = _UNBOUND,
    dp: Any = _UNBOUND,
    f: Any = _UNBOUND,
    fall: Any = _UNBOUND,
    p: Any = _UNBOUND,
    sunk: Any = _UNBOUND,
    u: Any = _UNBOUND,
    w: Any = _UNBOUND,
    wet_toe: Any = _UNBOUND,
    wx: Any = _UNBOUND,
    wy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0523.004 (wells_off_the_wet_toe) - body verbatim from _seg_0523__drain_flows_downhill (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if (_dd is not None or _field_dd) and wet_toe and M.get("fields"):
        _wt_cult = [p for f in M["fields"] for p in f["outline"]] + [p for dp in M.get("dry_plots", []) for p in dp["poly"]]
        _wt_low = max(fall((p[0], p[1])) for p in _wt_cult)  # the fall of the crop's lowest point
        # ...and the crop datum is only good WHERE THE CROP IS (settlement-review, 2026-08-12).
        # The relaxation exists because the band's uphill lip tucks under the field and carries no
        # reeds - but that is true only across the field's own cross-slope span. Out at the flanks
        # the lip is exposed and IS reeded from its very edge, so measuring by the crop's lowest
        # point there tolerated a well up to ~82 ft inside visible reeds; Akagahara's own west
        # well stands 12 ft above the reed line and passed with 94 ft of nominal headroom. Beyond
        # the crop's span the toe polygon itself is the datum, which is what a reader sees.
        _wt_u = (-_dv[1], _dv[0])  # across the slope
        _wt_us = [p[0] * _wt_u[0] + p[1] * _wt_u[1] for p in _wt_cult]
        _wt_ulo, _wt_uhi = min(_wt_us), max(_wt_us)

        def _wt_reedy(wx: float, wy: float) -> bool:
            if not any(point_in_poly(wx, wy, mp) for mp in wet_toe):
                return False
            u = wx * _wt_u[0] + wy * _wt_u[1]
            return not (_wt_ulo <= u <= _wt_uhi) or fall((wx, wy)) > _wt_low

        sunk = [(round(w["x"]), round(w["y"])) for w in M.get("wells", []) if _wt_reedy(w["x"], w["y"])]
        check(
            "wells_off_the_wet_toe",
            not sunk,
            f"wellhead(s) {sorted(set(sunk))[:3]} stand in the reed TOE, below the crop's lowest ground - a draw-well is "
            f"sunk on DRY ground with a water table under it, not in standing surface water. Site it up among the dwellings "
            f"it serves (the toe is derivable before it is drawn: see Settlement.toe_band)",
        )
    return _kept(locals(), ('_wt_cult', '_wt_low', '_wt_reedy', '_wt_u', '_wt_uhi', '_wt_ulo', '_wt_us', 'dp', 'f', 'p', 'sunk', 'w'))


def _seg_0523_005__streams_(*, M: Any = _UNBOUND, _dd: Any = _UNBOUND, _field_dd: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0523.005 (streams_) - body verbatim from _seg_0523__drain_flows_downhill (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if _dd is not None or _field_dd:
        streams_ = M.get("streams", [])
    return _kept(locals(), ('streams_',))


def _seg_0523_006___near_stream(
    *, _dd: Any = _UNBOUND, _field_dd: Any = _UNBOUND, i: Any = _UNBOUND, pt: Any = _UNBOUND, sp: Any = _UNBOUND, st: Any = _UNBOUND, streams_: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0523.006 (_near_stream) - body verbatim from _seg_0523__drain_flows_downhill (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if _dd is not None or _field_dd:

        def _near_stream(pt: Pt) -> bool:
            return any(seg_dist(pt[0], pt[1], sp[i], sp[i + 1]) < 30 for st in streams_ for sp in [st["poly"]] for i in range(len(sp) - 1))

    return _kept(locals(), ('_near_stream',))


# WHICH END DISCHARGES IS RECORDED, NOT GUESSED (GM 2026-07-25). Every drain->sink topology
# channel NAMES its field, so a drain is matched to its OWN discharge channels exactly -
# proximity matching was unreliable (Hirameki carries seven such channels and several sit on
# top of a different field's drain). Each named channel indicates the drain END it leaves
# from; a collector may have SEVERAL culverts along it, and the discharge the check cares
# about is the LOWEST of them. The check keeps its teeth on the case that matters: when the
# only recorded discharge sits at the drain's HIGH end, the water is running backwards.
# Read each channel's SINK end, not its on-drain end: a discharge channel may leave from a
# point PARTWAY along the collector (Hirameki's w2 runs off-map west from x=35, mid-drain),
# so matching its on-drain point to a drain endpoint misses it. The sink is whichever of the
# channel's two ends lies FARTHER from the drain line; when both lie on it - a 2-point drain
# whose discharge channel IS the drain, which is what Tango's fans carve - the polyline's
# last point is the sink by construction.


def _seg_0523_007___drain_topo(*, _dd: Any = _UNBOUND, _field_dd: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0523.007 (_drain_topo) - body verbatim from _seg_0523__drain_flows_downhill (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if _dd is not None or _field_dd:
        _drain_topo: dict[str, list[Any]] = {}  # type: ignore[no-redef,unused-ignore]
    return _kept(locals(), ('_drain_topo',))


def _seg_0523_008___drain_topo_1(*, M: Any = _UNBOUND, _dd: Any = _UNBOUND, _drain_topo: Any = _UNBOUND, _field_dd: Any = _UNBOUND, _tc: Any = _UNBOUND, _tfr: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0523.008 (_drain_topo, _tc, _tfr) - body verbatim from _seg_0523__drain_flows_downhill (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if _dd is not None or _field_dd:
        for _tc in M.get("channels", []):
            _tfr = _tc.get("frm") or {}
            if _tfr.get("kind") == "drain" and _tfr.get("name") and _tc.get("poly"):
                _drain_topo.setdefault(_tfr["name"], []).append(_tc["poly"])
    return _kept(locals(), ('_drain_topo', '_tc', '_tfr'))


def _seg_0523_009__up_disch(*, _dd: Any = _UNBOUND, _field_dd: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0523.009 (up_disch, up_drain) - body verbatim from _seg_0523__drain_flows_downhill (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if _dd is not None or _field_dd:
        up_drain, up_disch = [], []  # type: ignore[var-annotated]
    return _kept(locals(), ('up_disch', 'up_drain'))


def _seg_0523_010___a_(
    *,
    M: Any = _UNBOUND,
    _a_: Any = _UNBOUND,
    _b_: Any = _UNBOUND,
    _ce: Any = _UNBOUND,
    _da_: Any = _UNBOUND,
    _db_: Any = _UNBOUND,
    _dd: Any = _UNBOUND,
    _de: Any = _UNBOUND,
    _dfall: Any = _UNBOUND,
    _ditch_dv: Any = _UNBOUND,
    _dl: Any = _UNBOUND,
    _dline: Any = _UNBOUND,
    _drain_topo: Any = _UNBOUND,
    _field_dd: Any = _UNBOUND,
    _fv: Any = _UNBOUND,
    _hits: Any = _UNBOUND,
    _ind: Any = _UNBOUND,
    _near_stream: Any = _UNBOUND,
    _off_drain: Any = _UNBOUND,
    _sink: Any = _UNBOUND,
    _tp: Any = _UNBOUND,
    _v: Any = _UNBOUND,
    at_edge: Any = _UNBOUND,
    e0: Any = _UNBOUND,
    e1: Any = _UNBOUND,
    e_: Any = _UNBOUND,
    fd: Any = _UNBOUND,
    head: Any = _UNBOUND,
    i_: Any = _UNBOUND,
    out: Any = _UNBOUND,
    p: Any = _UNBOUND,
    up_drain: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0523.010 (_a_, _b_, _ce, _da_) - body verbatim from _seg_0523__drain_flows_downhill (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if _dd is not None or _field_dd:
        for fd in M.get("field_ditches", []):
            if fd.get("role") != "drain":
                continue
            _fv = _ditch_dv(fd)
            if _fv is None:
                continue

            def _dfall(p: Pt, _v: tuple[float, float] = _fv) -> float:
                """Fall projected on THIS drain's own field, not the map-level bearing."""
                return p[0] * _v[0] + p[1] * _v[1]

            p = fd["poly"]
            e0, e1 = p[0], p[-1]

            # the OUTFALL is the end that meets a brook or runs off-map (else default to the lower end)
            _dline = fd["poly"]

            def _off_drain(q_: Any, _dl: Any = _dline) -> float:
                return min(seg_dist(q_[0], q_[1], _dl[i_], _dl[i_ + 1]) for i_ in range(len(_dl) - 1))

            # Pool ALL the evidence for "this end discharges" - a named discharge channel, a brook
            # alongside, the frame edge - then take the LOWEST such end. A collector legitimately
            # carries several sinks (Hirameki's w2 runs off-map west AND tees a relief culvert back
            # to the stream at its east end; s1 runs off BOTH ends past the bottom edge), so any one
            # signal alone mis-reads. The check keeps its teeth on the case that matters: when every
            # piece of evidence puts the discharge at the drain's HIGH end, the water runs backwards.
            _ind: list[Any] = []  # type: ignore[no-redef]
            for _tp in _drain_topo.get(fd.get("field")) or []:
                _a_, _b_ = _tp[0], _tp[-1]
                # If exactly ONE culvert end sits on exactly ONE drain ENDPOINT, that endpoint is
                # where it leaves from - read it directly. The sink-end fallback below is for a
                # culvert leaving PARTWAY along the collector (Hirameki's w2 at x=35), where no
                # endpoint coincides; but preferring the sink there would mis-read a culvert that
                # doubles back, since its far end can land nearer the drain's other end (Nagahara's
                # fnn2 leaves its tail and runs west, ending 151px from the head and 182 from the
                # tail). On a 2-point drain whose culvert IS the drain both ends coincide, which is
                # ambiguous - fall through to the sink rule, which reads it correctly.
                _hits = [_de for _ce in (_a_, _b_) for _de in (e0, e1) if math.hypot(_ce[0] - _de[0], _ce[1] - _de[1]) < 15]
                if len(_hits) == 1:
                    _ind.append(_hits[0])
                    continue
                _sink: Any = _b_ if _off_drain(_b_) >= _off_drain(_a_) - 1.0 else _a_  # type: ignore[no-redef]
                _da_ = math.hypot(e0[0] - _sink[0], e0[1] - _sink[1])
                _db_ = math.hypot(e1[0] - _sink[0], e1[1] - _sink[1])
                _ind.append(e1 if _db_ < _da_ else e0)
            _ind += [e_ for e_ in (e0, e1) if _near_stream(e_) or at_edge(e_)]
            if _ind:  # the manifest names this drain's discharge(s): take the LOWEST one
                out = max(_ind, key=_dfall)
                head = e0 if out is e1 else e1
            else:
                out, head = (e1, e0) if _dfall(e1) >= _dfall(e0) else (e0, e1)
            if _dfall(out) < _dfall(head) - 8:  # outfall is UPHILL of the head - water runs backwards
                up_drain.append([round(out[0]), round(out[1])])
    return _kept(
        locals(), ('_a_', '_b_', '_ce', '_da_', '_db_', '_de', '_dfall', '_dline', '_fv', '_hits', '_ind', '_off_drain', '_sink', '_tp', 'e0', 'e1', 'e_', 'fd', 'head', 'out', 'p', 'up_drain')
    )


def _seg_0523_011__p(
    *, _dd: Any = _UNBOUND, _field_dd: Any = _UNBOUND, fall: Any = _UNBOUND, p: Any = _UNBOUND, st: Any = _UNBOUND, streams_: Any = _UNBOUND, up_disch: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0523.011 (p, st, up_disch) - body verbatim from _seg_0523__drain_flows_downhill (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if _dd is not None or _field_dd:
        for st in streams_:  # a drainage brook must head downhill off the field
            if (st.get("frm") or {}).get("kind") == "drain":
                p = st["poly"]
                if fall(p[-1]) < fall(p[0]) - 8:
                    up_disch.append([round(p[-1][0]), round(p[-1][1])])
    return _kept(locals(), ('p', 'st', 'up_disch'))


def _seg_0523_012__drain_flows_downhill(*, _dd: Any = _UNBOUND, _field_dd: Any = _UNBOUND, check: Any = _UNBOUND, up_drain: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0523.012 (drain_flows_downhill) - body verbatim from _seg_0523__drain_flows_downhill (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if _dd is not None or _field_dd:
        check(
            "drain_flows_downhill",
            not up_drain,
            f"a drain's OUTFALL {up_drain[:3]} sits UPHILL of its head - water would run backwards; the discharge end of a collector must be its lowest point (per meta.down_deg)",
        )
    return _kept(locals(), ())


def _seg_0523_013__drainage_discharges_downhill(*, _dd: Any = _UNBOUND, _field_dd: Any = _UNBOUND, check: Any = _UNBOUND, up_disch: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0523.013 (drainage_discharges_downhill) - body verbatim from _seg_0523__drain_flows_downhill (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if _dd is not None or _field_dd:
        check(
            "drainage_discharges_downhill",
            not up_disch,
            f"a drainage brook {up_disch[:3]} runs UPHILL from the drain outfall - it must carry the runoff DOWNHILL (toward the fall direction, meta.down_deg), matching the water flow elsewhere",
        )
    return _kept(locals(), ())


# a collector runs CROSS-SLOPE (roughly along the contour), because it must gather runoff from every
# cascade column - a drain running with the fall would follow one column and collect nothing. So its
# direction must be more PERPENDICULAR to the fall than parallel: the along-fall fraction of its
# head->outfall vector stays below ~0.65 (angle to the fall > ~50 deg). It may descend to carry water
# to the discharge, but must not run straight downhill like a delivery ditch.


def _seg_0523_014__crossy(*, _dd: Any = _UNBOUND, _field_dd: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0523.014 (crossy) - body verbatim from _seg_0523__drain_flows_downhill (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if _dd is not None or _field_dd:
        crossy = []  # type: ignore[var-annotated]
    return _kept(locals(), ('crossy',))


def _seg_0523_015___cv(
    *,
    M: Any = _UNBOUND,
    _cv: Any = _UNBOUND,
    _dd: Any = _UNBOUND,
    _ditch_dv: Any = _UNBOUND,
    _field_dd: Any = _UNBOUND,
    a: Any = _UNBOUND,
    along: Any = _UNBOUND,
    b: Any = _UNBOUND,
    crossy: Any = _UNBOUND,
    fd: Any = _UNBOUND,
    vlen: Any = _UNBOUND,
    vx: Any = _UNBOUND,
    vy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0523.015 (_cv, a, along, b) - body verbatim from _seg_0523__drain_flows_downhill (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if _dd is not None or _field_dd:
        for fd in M.get("field_ditches", []):
            if fd.get("role") != "drain":
                continue
            if fd.get("trimmed"):
                # an IN-WALL drain is cut off short of the patrol ring and sluice-gated into an
                # underground conduit to the moat, so what survives is the last leg to that outfall -
                # a stub, not a collector spanning the field's low edge. Judging its bearing against
                # "must run along the contour" is a category error: Tango's nw1 is 2 points and 134px
                # where every untrimmed drain on the map runs 159-231px.
                continue
            a, b = fd["poly"][0], fd["poly"][-1]
            vx, vy = b[0] - a[0], b[1] - a[1]
            vlen = math.hypot(vx, vy)
            if vlen < 1:  # pragma: no cover - a real drain spans the field's low edge; guards a 0-length poly
                continue
            _cv = _ditch_dv(fd)
            if _cv is None:
                continue
            along = abs(vx * _cv[0] + vy * _cv[1]) / vlen  # |cos(angle to THIS field's fall)|
            if along > 0.65:
                crossy.append(round(math.degrees(math.acos(min(1.0, along)))))
    return _kept(locals(), ('_cv', 'a', 'along', 'b', 'crossy', 'fd', 'vlen', 'vx', 'vy'))


def _seg_0523_016__drain_runs_cross_slope(*, _dd: Any = _UNBOUND, _field_dd: Any = _UNBOUND, check: Any = _UNBOUND, crossy: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0523.016 (drain_runs_cross_slope) - body verbatim from _seg_0523__drain_flows_downhill (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if _dd is not None or _field_dd:
        check(
            "drain_runs_cross_slope",
            not crossy,
            f"a drain runs too nearly WITH the slope (only {crossy[:3]} deg off the fall) - a collector must run roughly PERPENDICULAR to the flow (along the contour) to gather every column's runoff",
        )
    return _kept(locals(), ())


# A PADDY'S LOW BUND IS THE COLLECTOR'S BANK - IT IS NEVER DRAWN THROUGH THE DITCH (GM
# 2026-08-08, on Hoshizora: "the dark brown earthen bunds appear to overlap with the
# drainage ditch instead of aligning with it ... I would expect the earthen bunds bordering
# the ditch to be at the same angle as it"). A paddy is a level basin whose lowest side is
# the ditch's top-of-bank: the two ABUT. They cannot interpenetrate, because the bund is
# what holds the water in and the ditch is what takes it away, so a bund drawn across the
# collector is a basin with its wall in the drain.
#
# The defect it caught was geometric, not a stray plot. `_carve`'s hem pass laid its quads
# on the CONTOUR - one constant fall for the top edge, one for the bottom - while the
# collector is fitted as f = a + b*u and so runs at atan(b) to the contour (b is clamped to
# 0.35, i.e. up to ~19 deg). Every hem bund therefore started above the ditch and ended
# below it, and on Hoshizora the hem WAS the drain-side edge (14 of the west fan's 31
# plots, against 4 from the closing rank), so the whole field met its ditch as a sawtooth
# with brown ticks poking out into bare ground.
#
# ANGLE is how it reads, but angle is the wrong thing to test: a correct straight bund laid
# against a deliberately-wandering ditch sits a few degrees off its local segment (~9 deg on
# Hoshizora's NE pocket), and a contour-laid bund on a gently-fitted drain is only ~3 deg
# off - the two bands overlap, so an angle threshold would have to be either toothless or
# wrong. What is unambiguous is POSITION, so that is what this measures: no vertex of a
# drain-side plot may lie inside the collector's DRAWN stroke (which tapers, hence the
# per-point width) or past its centerline. Vertices whose nearest point on the collector is
# one of its two ENDS are skipped - ground beyond the drain's span is not governed by it.
# The predicate is `drain_bank_clearance`, imported from the engine and NOT restated here -
# it is the same call `hem_to_bank` makes when it lays a bund, so the placer and the gate
# cannot drift into disagreeing about which side of a ditch a point is on. `_pb`-prefixed
# locals: gate() is one huge scope and short geometry names are bound several times in it.


def _seg_0523_017__thru(*, _dd: Any = _UNBOUND, _field_dd: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0523.017 (thru) - body verbatim from _seg_0523__drain_flows_downhill (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if _dd is not None or _field_dd:
        thru: list[list[int]] = []  # type: ignore[no-redef,unused-ignore]
    return _kept(locals(), ('thru',))


def _seg_0523_018___pb_cum(
    *,
    M: Any = _UNBOUND,
    _dd: Any = _UNBOUND,
    _ditch_dv: Any = _UNBOUND,
    _field_dd: Any = _UNBOUND,
    _pb_cum: Any = _UNBOUND,
    _pb_dl: Any = _UNBOUND,
    _pb_drn: Any = _UNBOUND,
    _pb_dv: Any = _UNBOUND,
    _pb_fld: Any = _UNBOUND,
    _pb_gap: Any = _UNBOUND,
    _pb_hem: Any = _UNBOUND,
    _pb_lean: Any = _UNBOUND,
    _pb_need: Any = _UNBOUND,
    _pb_past: Any = _UNBOUND,
    _pb_q: Any = _UNBOUND,
    _pb_ring: Any = _UNBOUND,
    _pb_w0: Any = _UNBOUND,
    _pb_w1: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    p: Any = _UNBOUND,
    thru: Any = _UNBOUND,
    x: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0523.018 (_pb_cum, _pb_dl, _pb_drn, _pb_dv) - body verbatim from _seg_0523__drain_flows_downhill (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if _dd is not None or _field_dd:
        for _pb_fld in fields:
            _pb_hem = _pb_fld.get("drain_hem") or []
            _pb_drn = next((x for x in M.get("field_ditches", []) if x.get("role") == "drain" and x.get("field") == _pb_fld.get("name") and len(x.get("poly") or []) >= 2), None)
            if not _pb_hem or _pb_drn is None:
                continue
            _pb_dv = _ditch_dv(_pb_drn)
            if _pb_dv is None:
                continue
            _pb_dl = [(float(p[0]), float(p[1])) for p in _pb_drn["poly"]]
            _pb_cum = polyline_cum(_pb_dl)
            _pb_w0 = float(_pb_drn.get("w", 2.0))
            _pb_w1 = float(_pb_drn.get("w_tail", _pb_w0))
            for _pb_ring in _pb_hem:
                for _pb_q in _pb_ring:
                    _pb_gap, _pb_need, _pb_lean, _pb_past = drain_bank_clearance((_pb_q[0], _pb_q[1]), _pb_dl, _pb_dv, _pb_w0, _pb_w1, _pb_cum)
                    # 0.15px of float slack. A bund laid exactly ON the bank is recorded to 1dp
                    # (up to ~0.07px of perpendicular error) and reaches the bank through a fall
                    # interpolation, so an exactly-compliant edge must not read as a breach. The
                    # defect this exists for runs 2-8px, so the slack costs it nothing.
                    if not _pb_past and _pb_lean >= 0.2 and _pb_gap < _pb_need - 0.15:
                        thru.append([round(_pb_q[0]), round(_pb_q[1])])
    return _kept(locals(), ('_pb_cum', '_pb_dl', '_pb_drn', '_pb_dv', '_pb_fld', '_pb_gap', '_pb_hem', '_pb_lean', '_pb_need', '_pb_past', '_pb_q', '_pb_ring', '_pb_w0', '_pb_w1', 'p', 'thru', 'x'))


def _seg_0523_019__paddy_bunds_clear_the_collector(*, _dd: Any = _UNBOUND, _field_dd: Any = _UNBOUND, check: Any = _UNBOUND, thru: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0523.019 (paddy_bunds_clear_the_collector) - body verbatim from _seg_0523__drain_flows_downhill (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if _dd is not None or _field_dd:
        check(
            "paddy_bunds_clear_the_collector",
            not thru,
            f"{len(thru)} paddy bund vertex/vertices {thru[:4]} are drawn INSIDE the drainage collector's stroke or past its centerline - a paddy's low bund IS the ditch's bank, so the field must hem onto the collector (bunds running WITH it), never across it",
        )
    return _kept(locals(), ())


# AN AZEMAME BEAD SITS ON A VISIBLE BUND, NEVER IN OPEN WATER (GM 2026-08-15, on Inashiro:
# "random green dots that appear to be scattered in the middle of flooded rice paddies ...
# it should be impossible for those green dots to be placed anywhere except on top of
# earthen bunds"). The defect was PAINT ORDER, not a bad scatter: `_fill_wedges`' filler
# plots deliberately lap up to ~12 real ft onto a neighbor and are appended LAST, so the
# lapped stretch of the neighbor's bund stroke is buried under the filler's water fill -
# and the bead line `_bund_beans` had already laid along that stretch draws AFTER every
# plot, so its dots surfaced floating in the filler's paddy (49 of Inashiro's 777 beads,
# 3-10 px deep). The field record carries `plot_rings` in draw order precisely so this is
# judgeable from the manifest: a bead is legal iff some ring's edge passes within _BB_TOL
# of it AND no ring painted after that one buries the bead deeper than _BB_TOL. Placement
# (`waterfields._bund_beans`) enforces the same rule at half this tolerance, so a bead the
# placer allowed cannot false-fire here through 1dp manifest rounding. Pre-2026-08-15
# manifests record neither key and skip; the recording itself is unconditional at the one
# draw site (draw_comb_field), pinned by test_draw_comb_field_records_rings_and_beads.
# ... and the same rule against WATER paint (GM 2026-08-15, second pass: "fix the water-buried
# beads so the record stays honest"; settlement-review found 40 of Inashiro's 727 recorded
# beads invisible under channel/pond paint - opposite polarity from the plot burial, bund and
# bead buried together, but the record was attesting beads nobody can see). The painted truth
# is read from the manifest's paint records, not re-derived: `drawn_channels` carries the
# post-clip stroke geometry + widths (late strokes paint after the beads and bury them),
# `pond` and `field_ponds` the water ellipses. A bead inside any of those is wrong whichever
# way the z goes - buried ink under late water, or a green dot floating ON the water for
# paint that runs under the beads - so the test is position, not stacking.


def _seg_0524___BB_TOL() -> dict[str, Any]:
    """Gate segment 524 (_BB_TOL) - body verbatim from the legacy gate() (feature 022)."""
    _BB_TOL = 2.0
    return _kept(locals(), ('_BB_TOL',))


def _seg_0525___bb_wet() -> dict[str, Any]:
    """Gate segment 525 (_bb_wet) - body verbatim from the legacy gate() (feature 022)."""
    _bb_wet: list[tuple[float, float, float, float]] = []  # water ellipses (cx, cy, rx, ry), shrunk by the tolerance at use
    return _kept(locals(), ('_bb_wet',))


def _seg_0526___bb_wet_1(*, M: Any = _UNBOUND, _bb_wet: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 526 (_bb_wet) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("pond"):
        _bb_wet.append((float(M["pond"][0]), float(M["pond"][1]), float(M["pond"][2]), float(M["pond"][3])))
    return _kept(locals(), ('_bb_wet',))


def _seg_0527___bb_fp(*, M: Any = _UNBOUND, _bb_fp: Any = _UNBOUND, _bb_wet: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 527 (_bb_fp, _bb_wet) - body verbatim from the legacy gate() (feature 022)."""
    for _bb_fp in M.get("field_ponds") or []:
        _bb_wet.append((float(_bb_fp["x"]), float(_bb_fp["y"]), float(_bb_fp["rx"]), float(_bb_fp["ry"])))
    return _kept(locals(), ('_bb_fp', '_bb_wet'))


def _seg_0528___bb_c(*, M: Any = _UNBOUND, _bb_c: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 528 (_bb_c, _bb_wchan) - body verbatim from the legacy gate() (feature 022)."""
    _bb_wchan = [_bb_c for _bb_c in (M.get("drawn_channels") or []) if _bb_c.get("late") and len(_bb_c.get("pts") or []) >= 2]
    return _kept(locals(), ('_bb_c', '_bb_wchan'))


def _seg_0529___bb_in_water(
    *,
    _BB_TOL: Any = _UNBOUND,
    _bb_wchan: Any = _UNBOUND,
    _bb_wet: Any = _UNBOUND,
    _wcx: Any = _UNBOUND,
    _wcy: Any = _UNBOUND,
    _wi: Any = _UNBOUND,
    _wtot: Any = _UNBOUND,
    _wx: Any = _UNBOUND,
    _wy: Any = _UNBOUND,
    q: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 529 (_bb_in_water) - body verbatim from the legacy gate() (feature 022)."""

    def _bb_in_water(_wx: float, _wy: float) -> bool:
        for _wcx, _wcy, _wrx, _wry in _bb_wet:
            if _wrx > _BB_TOL and _wry > _BB_TOL and ((_wx - _wcx) / (_wrx - _BB_TOL)) ** 2 + ((_wy - _wcy) / (_wry - _BB_TOL)) ** 2 <= 1.0:
                return True
        for _wc in _bb_wchan:
            _wp = _wc["pts"]
            _wcum = polyline_cum([(float(q[0]), float(q[1])) for q in _wp])
            _wtot = _wcum[-1] or 1.0
            for _wi in range(len(_wp) - 1):
                _wd = seg_dist(_wx, _wy, _wp[_wi], _wp[_wi + 1])
                _wt = _wcum[_wi] / _wtot  # width taper measured at the segment head - within a segment the taper moves less than the tolerance
                if _wd < (float(_wc["w0"]) + (float(_wc["w1"]) - float(_wc["w0"])) * _wt) / 2 - 1.0:
                    return True
        return False

    return _kept(locals(), ('_bb_in_water',))


def _seg_0530___bb_stray() -> dict[str, Any]:
    """Gate segment 530 (_bb_stray) - body verbatim from the legacy gate() (feature 022)."""
    _bb_stray: list[list[float]] = []
    return _kept(locals(), ('_bb_stray',))


def _seg_0531___bb_b(
    *,
    Hd: Any = _UNBOUND,
    Wd: Any = _UNBOUND,
    _BB_TOL: Any = _UNBOUND,
    _bb_b: Any = _UNBOUND,
    _bb_beans: Any = _UNBOUND,
    _bb_buried: Any = _UNBOUND,
    _bb_d: Any = _UNBOUND,
    _bb_edge: Any = _UNBOUND,
    _bb_fld: Any = _UNBOUND,
    _bb_gi: Any = _UNBOUND,
    _bb_in_water: Any = _UNBOUND,
    _bb_j: Any = _UNBOUND,
    _bb_k: Any = _UNBOUND,
    _bb_ring: Any = _UNBOUND,
    _bb_rings: Any = _UNBOUND,
    _bb_stray: Any = _UNBOUND,
    _bb_x: Any = _UNBOUND,
    _bb_xs: Any = _UNBOUND,
    _bb_y: Any = _UNBOUND,
    _bb_ys: Any = _UNBOUND,
    _bx0: Any = _UNBOUND,
    _bx1: Any = _UNBOUND,
    _by0: Any = _UNBOUND,
    _by1: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    i: Any = _UNBOUND,
    q: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 531 (_bb_b, _bb_beans, _bb_buried, _bb_d) - body verbatim from the legacy gate() (feature 022)."""
    for _bb_fld in fields:
        _bb_beans = _bb_fld.get("bund_beans") or []
        _bb_rings = _bb_fld.get("plot_rings") or []
        if not _bb_beans or not _bb_rings:
            continue
        _bb_gi = GridIndex(64)
        for _bb_j, _bb_ring in enumerate(_bb_rings):
            _bb_xs = [float(q[0]) for q in _bb_ring]
            _bb_ys = [float(q[1]) for q in _bb_ring]
            # clamp the index box to the canvas (generously): negative fixtures carry deliberately
            # insane geometry, and an unclamped box allocates a dict entry per 120px cell of it
            _bx0, _by0 = max(min(_bb_xs) - _BB_TOL, -Wd), max(min(_bb_ys) - _BB_TOL, -Hd)
            _bx1, _by1 = min(max(_bb_xs) + _BB_TOL, 2 * Wd), min(max(_bb_ys) + _BB_TOL, 2 * Hd)
            if _bx0 <= _bx1 and _by0 <= _by1:
                _bb_gi.add(_bx0, _by0, _bx1, _by1, (_bb_j, _bb_ring))
        for _bb_b in _bb_beans:
            _bb_x, _bb_y = float(_bb_b[0]), float(_bb_b[1])
            _bb_edge: dict[int, float] = {}  # type: ignore[no-redef]  # ring index -> its nearest-edge distance to the bead
            _bb_buried: list[int] = []  # type: ignore[no-redef]  # rings whose fill buries the bead (inside, deeper than tol)
            for _bb_j, _bb_ring in _bb_gi.near(_bb_x, _bb_y):
                _bb_d = min(seg_dist(_bb_x, _bb_y, _bb_ring[i], _bb_ring[(i + 1) % len(_bb_ring)]) for i in range(len(_bb_ring)))
                _bb_edge[_bb_j] = _bb_d
                if _bb_d > _BB_TOL and point_in_poly(_bb_x, _bb_y, _bb_ring):
                    _bb_buried.append(_bb_j)
            if _bb_in_water(_bb_x, _bb_y) or not any(_bb_d <= _BB_TOL and all(_bb_k <= _bb_j for _bb_k in _bb_buried) for _bb_j, _bb_d in _bb_edge.items()):
                _bb_stray.append([round(_bb_x), round(_bb_y)])
    return _kept(
        locals(),
        (
            '_bb_b',
            '_bb_beans',
            '_bb_buried',
            '_bb_d',
            '_bb_edge',
            '_bb_fld',
            '_bb_gi',
            '_bb_j',
            '_bb_k',
            '_bb_ring',
            '_bb_rings',
            '_bb_stray',
            '_bb_x',
            '_bb_xs',
            '_bb_y',
            '_bb_ys',
            '_bx0',
            '_bx1',
            '_by0',
            '_by1',
            'i',
            'q',
        ),
    )


def _seg_0532__bund_beans_on_bunds(*, _bb_stray: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 532 (bund_beans_on_bunds) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "bund_beans_on_bunds",
        not _bb_stray,
        f"{len(_bb_stray)} azemame bead(s) {_bb_stray[:4]} do not sit on a bund the finished paint shows - a bund stroke buried under a later-drawn plot's fill (the wedge fillers lap their neighbors on purpose) or under WATER paint (a late ditch stroke, the source pond, a pocket pond) is not visible ground; `waterfields._bund_beans` / `draw_comb_field`'s pond filter must drop the beads laid there so the record carries no invisible ink",
    )
    return _kept(locals(), ())


def _seg_0595__paddy_bunds_clear_the_supply_channels(*, M: Any = _UNBOUND, check: Any = _UNBOUND, fields: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 595 (paddy_bunds_clear_the_supply_channels) - the first check ADDED by hand
    after feature 022 retired the transformer. Numbered past the legacy range (0000-0594) but
    REGISTERED between segments 0532 and 0533, beside the bead checks whose `fields` binding it
    shares (the registry TUPLE is the execution order; the number is only a label). New-style:
    its temps stay function-local - no legacy leak parity to keep - so writes=()."""
    # A PADDY'S CANAL-SIDE BUND IS THE SUPPLY CHANNEL'S BANK - NEVER DRAWN DOWN THE MIDDLE OF THE
    # WATER (GM 2026-08-15, on Inashiro: "the earth bunds which border the irrigated channel ...
    # are actually in the middle of the water instead of along the water's edge. I think they are
    # supposed to be along the water's edge"). The supply half of paddy_bunds_clear_the_collector,
    # and the same physical rule: the bund holds the basin's water IN and the channel carries other
    # water PAST, so the two can only ABUT at the bank - and a bund hemmed onto the bank runs
    # parallel to and along the water's edge, which is exactly the read the GM asked for.
    #
    # The defect was construction, not a stray plot: `_carve`'s `bnd` returns thread CENTERLINES,
    # and the supply strokes (the tapering canal pieces, the delivery ditches) are drawn centered
    # on those same lines - so the first and last column of every sector, and the head wedge's
    # boundary where `bnd` falls back onto canal A's own path, carried bunds running down the
    # middle of the drawn water. Measured on the pre-fix Inashiro: 266 sampled bund-edge points
    # inside a supply stroke, the worst 6.1 px deep in a ~12 px channel - i.e. ON its centerline.
    #
    # POSITION, not angle, for the reasons the collector check records above; measured
    # perpendicular to the stroke with its taper honored, and vertices projecting past a stroke's
    # ends skipped (ground beyond the span is not governed by it - a delivery ditch's takeoff sits
    # ON its parent canal, which governs there in its own right). The predicate is
    # `supply_bank_clearance`, imported from the engine and NOT restated - the same call `_carve`'s
    # `clear_supply` makes when it lays the bund. The placer holds a corner at halfw +
    # BANK_MARGIN * grain and this fires below halfw + BANK_MARGIN - 0.15 (the collector check's
    # 1dp-rounding slack), so a bund the placer allowed cannot false-fire here.
    #
    # GATED ON `meta.generated_by` (the migration doctrine, GM 2026-08-13, same gate as the
    # sun-corridor rule above): the legacy comb maps carry this defect pool-wide - measured
    # 2026-08-15 by this same predicate over their recorded plot_polys: kikuta 524 buried bund
    # vertices, minami 208, honda 203, tango 190, nagahara 121, shimizu 90, hirameki 33, ubame 17,
    # yatsuda 15, hoshizora 11, tanada 9, enokida 1 - re-carving them all was judged the wrong
    # trade once already.
    # The rule binds the SCRIPTED path (`build_comb(supply_banks=True)`); each legacy map inherits
    # it at the moment it is converted. Manifests that record no plot_rings (pre-2026-08-15) skip,
    # the same line the bead checks hold.
    if M["meta"].get("generated_by"):
        _sb_thru: dict[tuple[int, int], None] = {}  # dedupe: a corner is shared by up to 4 rings
        for _sb_fld in fields:
            _sb_rings = _sb_fld.get("plot_rings") or []
            if not _sb_rings:
                continue
            for _sb_fd in M.get("field_ditches", []):
                if _sb_fd.get("role") not in ("main", "branch") or _sb_fd.get("field") != _sb_fld.get("name"):
                    continue
                _sb_pts = [(float(p[0]), float(p[1])) for p in _sb_fd.get("poly") or []]
                if len(_sb_pts) < 2:
                    continue
                _sb_cum = polyline_cum(_sb_pts)
                _sb_w0 = float(_sb_fd.get("w", 2.0))
                _sb_w1 = float(_sb_fd.get("w_tail", _sb_w0))
                # bbox prefilter (prunes only): a vertex outside the stroke's box grown by its
                # widest half-width + margin cannot be inside the stroke
                _sb_reach = max(_sb_w0, _sb_w1) / 2 + BANK_MARGIN + 1.0
                _sb_x0 = min(p[0] for p in _sb_pts) - _sb_reach
                _sb_x1 = max(p[0] for p in _sb_pts) + _sb_reach
                _sb_y0 = min(p[1] for p in _sb_pts) - _sb_reach
                _sb_y1 = max(p[1] for p in _sb_pts) + _sb_reach
                # EDGES, not just vertices (settlement-review, Sawada 2026-08-15): a junction wedge
                # can keep every corner dry while its two long edges converge THROUGH the canal, so
                # each bund edge is walked at a 3 px step - bbox-gated, so only near-stroke edges pay
                for _sb_ring in _sb_rings:
                    for _sb_i in range(len(_sb_ring)):
                        _sb_a, _sb_b = _sb_ring[_sb_i], _sb_ring[(_sb_i + 1) % len(_sb_ring)]
                        _sb_ax, _sb_ay = float(_sb_a[0]), float(_sb_a[1])
                        _sb_bx, _sb_by = float(_sb_b[0]), float(_sb_b[1])
                        if max(_sb_ax, _sb_bx) < _sb_x0 or min(_sb_ax, _sb_bx) > _sb_x1 or max(_sb_ay, _sb_by) < _sb_y0 or min(_sb_ay, _sb_by) > _sb_y1:
                            continue
                        _sb_nstep = max(1, int(math.hypot(_sb_bx - _sb_ax, _sb_by - _sb_ay) / 3.0))
                        for _sb_k in range(_sb_nstep + 1):
                            _sb_t = _sb_k / _sb_nstep
                            _sb_x = _sb_ax + _sb_t * (_sb_bx - _sb_ax)
                            _sb_y = _sb_ay + _sb_t * (_sb_by - _sb_ay)
                            _sb_gap, _sb_halfw, _sb_past, _sb_foot, _sb_nrm = supply_bank_clearance((_sb_x, _sb_y), _sb_pts, _sb_w0, _sb_w1, _sb_cum)
                            if not _sb_past and _sb_gap < _sb_halfw + BANK_MARGIN - 0.15:
                                _sb_thru[(round(_sb_x), round(_sb_y))] = None
                                break
        check(
            "paddy_bunds_clear_the_supply_channels",
            not _sb_thru,
            f"{len(_sb_thru)} paddy bund vertex/vertices {[list(_sb_k) for _sb_k in list(_sb_thru)[:4]]} are drawn inside a SUPPLY channel's stroke - a bund bordering the irrigated channel is the channel's BANK, so it runs parallel to and along the water's edge, never down the middle of the water; carve with build_comb(supply_banks=True) so the bunds hem onto the drawn strokes",
        )
    return _kept(locals(), ())


# A drainage brook LEAVES the collector as a smooth BEND, not a hard right-angle corner - a contour
# collector turns down the valley INTO the stream, it does not meet it at 90 deg. For each drain-fed
# brook, compare the drain's ARRIVAL heading (into the shared outfall) with the brook's DEPARTURE
# heading (each averaged over ~40px, so short jittery segments do not fool it); the turn must be < 65 deg.


def _seg_0533___flow_dir(*, end: Any = _UNBOUND, poly: Any = _UNBOUND, q: Any = _UNBOUND, span: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 533 (_flow_dir) - body verbatim from the legacy gate() (feature 022)."""

    def _flow_dir(poly: Poly, at_start: bool, span: float = 40.0) -> tuple[float, float]:
        end = poly[0] if at_start else poly[-1]
        ref = end
        for q in poly[1:] if at_start else poly[-2::-1]:
            ref = q
            if math.hypot(q[0] - end[0], q[1] - end[1]) >= span:
                break
        return (ref[0] - end[0], ref[1] - end[1]) if at_start else (end[0] - ref[0], end[1] - ref[1])

    return _kept(locals(), ('_flow_dir',))


def _seg_0534___drains(*, M: Any = _UNBOUND, fd: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 534 (_drains, fd) - body verbatim from the legacy gate() (feature 022)."""
    _drains = [fd["poly"] for fd in M.get("field_ditches", []) if fd.get("role") == "drain"]
    return _kept(locals(), ('_drains', 'fd'))


def _seg_0535__sharp() -> dict[str, Any]:
    """Gate segment 535 (sharp) - body verbatim from the legacy gate() (feature 022)."""
    sharp = []  # type: ignore[var-annotated]
    return _kept(locals(), ('sharp',))


def _seg_0536__ang(
    *,
    M: Any = _UNBOUND,
    _drains: Any = _UNBOUND,
    _flow_dir: Any = _UNBOUND,
    ang: Any = _UNBOUND,
    arr: Any = _UNBOUND,
    bp: Any = _UNBOUND,
    dep: Any = _UNBOUND,
    dp: Any = _UNBOUND,
    e: Any = _UNBOUND,
    la: Any = _UNBOUND,
    ld: Any = _UNBOUND,
    near_drain: Any = _UNBOUND,
    sharp: Any = _UNBOUND,
    st: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 536 (ang, arr, bp, dep) - body verbatim from the legacy gate() (feature 022)."""
    for st in M.get("streams", []):
        if (st.get("frm") or {}).get("kind") != "drain" or len(st["poly"]) < 2:
            continue
        bp = st["poly"]
        near_drain = min(
            (
                (math.hypot(bp[0][0] - dp[e][0], bp[0][1] - dp[e][1]), dp, e)  # the drain it leaves:
                for dp in _drains
                for e in (0, -1)
            ),
            default=None,
        )  # nearest drain endpoint
        if near_drain is None or near_drain[0] > 40 or len(near_drain[1]) < 2:
            continue
        arr, dep = _flow_dir(near_drain[1], at_start=(near_drain[2] == 0)), _flow_dir(bp, at_start=True)
        la, ld = math.hypot(*arr), math.hypot(*dep)
        if la < 1 or ld < 1:  # pragma: no cover - real drains/brooks span the field; guards 0-length polys
            continue
        ang = math.degrees(math.acos(max(-1.0, min(1.0, (arr[0] * dep[0] + arr[1] * dep[1]) / (la * ld)))))
        if ang > 65:
            sharp.append(round(ang))
    return _kept(locals(), ('ang', 'arr', 'bp', 'dep', 'dp', 'e', 'la', 'ld', 'near_drain', 'sharp', 'st'))


def _seg_0537__drainage_junction_smooth(*, check: Any = _UNBOUND, sharp: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 537 (drainage_junction_smooth) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "drainage_junction_smooth",
        not sharp,
        f"a drainage brook leaves the collector at a sharp {sharp[:3]} deg corner - it must CURVE out of "
        f"the drain's heading (a collector turns down the valley into the stream, not a hard right angle)",
    )
    return _kept(locals(), ())


# torii (if any): clear of the shrine and spread out (universal)


def _seg_0538__torii(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 538 (torii) - body verbatim from the legacy gate() (feature 022)."""
    torii = M.get("torii", [])
    return _kept(locals(), ('torii',))


def _seg_0539__torii_spread_out(
    *,
    M: Any = _UNBOUND,
    _al: Any = _UNBOUND,
    _ax: Any = _UNBOUND,
    _axis_off: Any = _UNBOUND,
    _ay: Any = _UNBOUND,
    _ftpx: Any = _UNBOUND,
    _gap_max: Any = _UNBOUND,
    _in_field: Any = _UNBOUND,
    _set_out: Any = _UNBOUND,
    _tfloor: Any = _UNBOUND,
    check: Any = _UNBOUND,
    f: Any = _UNBOUND,
    far: Any = _UNBOUND,
    i: Any = _UNBOUND,
    j: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    mine: Any = _UNBOUND,
    near: Any = _UNBOUND,
    off: Any = _UNBOUND,
    r: Any = _UNBOUND,
    sh: Any = _UNBOUND,
    shrine: Any = _UNBOUND,
    spread: Any = _UNBOUND,
    sw: Any = _UNBOUND,
    sx: Any = _UNBOUND,
    sy: Any = _UNBOUND,
    t: Any = _UNBOUND,
    torii: Any = _UNBOUND,
    under: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 539 (shrine_avenue_fronts_the_hall, torii_clear_of_fields, torii_clear_of_shrine, torii_spread_out) - body verbatim from the legacy gate() (feature 022)."""
    if torii:
        shrine = M.get("shrine")
        if shrine:
            sx, sy, sw, sh = shrine
            under = [t for t in torii if sx - 6 <= t[0] <= sx + sw + 6 and sy - 6 <= t[1] <= sy + sh + 6]
            check("torii_clear_of_shrine", not under, f"{len(under)} torii under the shrine")
        # No two arches closer than one rail-span (16 ft): a dense senbon-style AVENUE may pack the arches
        # close, but they must not overlap into a vermilion blob. Scale-aware (was a fixed 25px, tuned to the
        # pre-true-scale 38px glyph - too coarse now the arch is ~8px/16ft at village scale; GM 2026-07-22).
        _tfloor = 16.0 / meta.get("ftpx", 1)
        spread = all(math.hypot(torii[i][0] - torii[j][0], torii[i][1] - torii[j][1]) > _tfloor for i in range(len(torii)) for j in range(i + 1, len(torii)))
        check("torii_spread_out", spread, f"torii closer than one arch-span (~{_tfloor:.0f}px) apart - they overlap into a blob rather than reading as distinct gateways")
        # NO ARCH STANDS IN A CROP (torii_clear_of_fields, 2026-07-24): caught during the torii
        # re-roll when Hirameki's Benten rolled 7 and the naive single-point avenue extension
        # marched five arches straight through the Imperial chrysanthemum field - torii are
        # overlap-EXEMPT structures (they legitimately stand over streets), so no generic pass
        # guarded them against fields. A sando is a cleared processional way: it may run BESIDE
        # a field (route the avenue's geometry around the crop), never through the planting.
        _in_field = [(round(t[0]), round(t[1])) for t in torii if any(point_in_poly(t[0], t[1], f["outline"]) for f in M.get("fields", []) + M.get("flower_fields", []))]
        check(
            "torii_clear_of_fields",
            not _in_field,
            f"torii arch(es) standing IN a field/flower-field at {_in_field[:4]} - a sando runs beside the crop, never through it; route the avenue geometry around the field",
        )

        # A village-shrine SANDO (>= 3 arches marching to the hall) puts its INNERMOST arch at the hall's
        # THRESHOLD, directly in front, not set out with a gap (GM 2026-07-22, "village shrines only"). Exempt the
        # modest 1-2 arch entrance (not a processional avenue) and the gateway-BESIDE-the-hall pattern (Hikari:
        # the hall stands aside the entrance track while the arches straddle the track, so it sits well OFF the
        # avenue axis). Village-scoped by kind=='shrine' (towns get monasteries, cities temples - a large-temple
        # sando with a courtyard between the outer arch and the main hall stays legitimate).
        _ftpx = meta.get("ftpx", 1)
        _gap_max = 36.0 / _ftpx  # innermost arch within ~36 ft of the hall front
        _axis_off = 50.0 / _ftpx  # hall >~50 ft off the avenue axis = a gateway beside it, not a sando to it
        _set_out = []
        for r in M.get("religious", []):
            if r.get("kind") != "shrine":
                continue
            mine = [t for t in torii if min(M["religious"], key=lambda rr: math.hypot(rr["x"] - t[0], rr["y"] - t[1])) is r]
            if len(mine) < 3:
                continue  # a 1-2 arch entrance is not a processional sando
            near = min(mine, key=lambda t: pt_to_rect(t[0], t[1], r))
            far = max(mine, key=lambda t: math.hypot(t[0] - r["x"], t[1] - r["y"]))
            _ax, _ay = near[0] - far[0], near[1] - far[1]
            _al = math.hypot(_ax, _ay) or 1.0
            _ax, _ay = _ax / _al, _ay / _al
            off = abs((r["x"] - near[0]) * (-_ay) + (r["y"] - near[1]) * _ax)  # hall's perpendicular offset from the axis
            if off > _axis_off:
                continue  # gateway beside the hall (Hikari), arches lining the track - not a sando to the hall
            if pt_to_rect(near[0], near[1], r) > _gap_max:
                _set_out.append((round(r["x"]), round(r["y"])))
        check(
            "shrine_avenue_fronts_the_hall",
            not _set_out,
            f"{len(_set_out)} village shrine(s) whose torii avenue stands off from the hall at {_set_out[:4]} - the innermost arch of a sando sits at the hall's threshold, directly in front, not set out with a gap",
        )
    return _kept(
        locals(),
        (
            '_al',
            '_ax',
            '_axis_off',
            '_ay',
            '_ftpx',
            '_gap_max',
            '_in_field',
            '_set_out',
            '_tfloor',
            'f',
            'far',
            'i',
            'j',
            'mine',
            'near',
            'off',
            'r',
            'sh',
            'shrine',
            'spread',
            'sw',
            'sx',
            'sy',
            't',
            'under',
        ),
    )


# ---- village-specific expectations (from meta) ---------------------------


def _seg_0540__abandoned(*, h: Any = _UNBOUND, houses: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 540 (abandoned, h) - body verbatim from the legacy gate() (feature 022)."""
    abandoned = sum(1 for h in houses if h["kind"] == "abandoned")
    return _kept(locals(), ('abandoned', 'h'))


def _seg_0541__occupied(*, abandoned: Any = _UNBOUND, houses: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 541 (occupied) - body verbatim from the legacy gate() (feature 022)."""
    occupied = len(houses) - abandoned
    return _kept(locals(), ('occupied',))


def _seg_0542__households_consistent(
    *,
    abandoned: Any = _UNBOUND,
    check: Any = _UNBOUND,
    hh: Any = _UNBOUND,
    hi: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    lo: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    occupied: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    t: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 542 (house_count_in_range, households_consistent) - body verbatim from the legacy gate() (feature 022)."""
    if meta.get("households"):
        # occupied farmhouses must portray the declared households ~1:1. A ~5-person
        # home is one nuclear/stem family per roof, and population / 5 = households =
        # farmhouses (GM: "population ~350 so there should be ~70 farmhouses"), so the
        # map DEPICTS close to the full household count - ~0.85-1.05x, allowing a few
        # off-frame homesteads or the odd shared roof. (Supersedes the earlier ~0.7x
        # extended-family assumption: the target is to depict every household.)
        hh = meta["households"]
        if meta.get("toscale", scale == "village"):  # to-scale tiers (village + hamlet) depict ~every household 1:1
            lo, hi = round(0.85 * hh), round(1.05 * hh)
        else:  # legacy tiers still depict ~0.7-0.9 (extended-family sharing, off-frame)
            lo, hi = round(0.68 * hh), round(0.9 * hh)
        check("households_consistent", lo <= occupied <= hi, f"{occupied} occupied houses for ~{hh} households (expect {lo}-{hi}; +{abandoned} abandoned)")
    elif meta.get("target_houses"):
        t = meta["target_houses"]
        lo, hi = round(0.85 * t), round(1.15 * t)
        check("house_count_in_range", lo <= len(houses) <= hi, f"{len(houses)} houses (expect ~{t})")
    elif scale in ("village", "hamlet"):
        lo, hi = (40, 80) if scale == "village" else (10, 30)
        check("house_count_in_range", lo <= len(houses) <= hi, f"{len(houses)} houses (expect {lo}-{hi} for a {scale})")
    return _kept(locals(), ('hh', 'hi', 'lo', 't'))


def _seg_0543_000__bk(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.000 (bk) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        bk: dict[str, int] = {}  # type: ignore[no-redef,unused-ignore]
    return _kept(locals(), ('bk',))


def _seg_0543_001__b(*, M: Any = _UNBOUND, b: Any = _UNBOUND, bk: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.001 (b, bk) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        for b in M.get("buildings", []):
            bk[b["kind"]] = bk.get(b["kind"], 0) + 1
    return _kept(locals(), ('b', 'bk'))


def _seg_0543_002__farmhouses(*, houses: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.002 (farmhouses) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        farmhouses = len(houses)
    return _kept(locals(), ('farmhouses',))


def _seg_0543_003__bands(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.003 (bands) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        bands = {"merchant": (20, 28), "laborer": (25, 35), "servant": (9, 17), "burakumin": (10, 14), "samurai": (5, 10)}
    return _kept(locals(), ('bands',))


# a caste's homes come in size variants (the wealthy get larger houses); count them together


def _seg_0543_004__VARIANTS(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.004 (VARIANTS) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        VARIANTS = {"merchant": ("merchant", "merchant_house", "merchant_large"), "laborer": ("laborer", "laborer_large"), "samurai": ("samurai", "samurai_large")}
    return _kept(locals(), ('VARIANTS',))


def _seg_0543_005__caste_n(*, VARIANTS: Any = _UNBOUND, bands: Any = _UNBOUND, bk: Any = _UNBOUND, k: Any = _UNBOUND, kind: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.005 (caste_n, k, kind) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        caste_n = {kind: sum(bk.get(k, 0) for k in VARIANTS.get(kind, (kind,))) for kind in bands}
    return _kept(locals(), ('caste_n', 'k', 'kind'))


def _seg_0543_006__town_caste_count(
    *, bands: Any = _UNBOUND, c: Any = _UNBOUND, caste_n: Any = _UNBOUND, check: Any = _UNBOUND, hi: Any = _UNBOUND, kind: Any = _UNBOUND, lo: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0543.006 (town_caste_count) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        for kind, (lo, hi) in bands.items():
            c = caste_n[kind]
            check(f"town_caste_count[{kind}]", lo <= c <= hi, f"{kind} buildings {c} outside budgets.md band [{lo},{hi}]")
    return _kept(locals(), ('c', 'hi', 'kind', 'lo'))


# SENIOR SAMURAI GET LARGER HOUSES at the county seat too (budgets.md's rank mix; the town
# analog of city_samurai_housing_varied - GM audit 2026-07): at least one samurai_large
# among a majority of small houses.


def _seg_0543_007__sl_t(*, bk: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.007 (sl_t) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        sl_t = bk.get("samurai_large", 0)
    return _kept(locals(), ('sl_t',))


def _seg_0543_008__ss_t(*, bk: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.008 (ss_t) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        ss_t = bk.get("samurai", 0)
    return _kept(locals(), ('ss_t',))


def _seg_0543_009__town_samurai_housing_varied(*, check: Any = _UNBOUND, scale: Any = _UNBOUND, sl_t: Any = _UNBOUND, ss_t: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.009 (town_samurai_housing_varied) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town' and (sl_t or ss_t):
        check(
            "town_samurai_housing_varied",
            sl_t >= 1 and ss_t > sl_t,
            f"samurai housing lacks rank variety (large={sl_t}, small={ss_t}) - the senior official(s) at a county seat keep a larger house among the juniors' small ones",
        )
    return _kept(locals(), ())


# THE BURAKUMIN QUARTER IS SEGREGATED - the doctrine word on every map, previously enforced
# nowhere (GM audit 2026-07): a band of OPEN GROUND separates it from every other caste's
# housing. TOWN-scoped: a city's ward system zones quarters wall-to-wall, so its
# segregation is zoning, not open ground (Tango/Nagahara adjacent-quarter seams run ~10px).
#
# 60 REAL FT BETWEEN THE WALLS, and both halves of that were wrong before 2026-07-27.
# It read "within 40px" measured CENTER TO CENTER, and 40 ft is less than the two
# half-diagonals of the houses it separates (44-51 ft here), so two roofs could touch and
# still pass a check whose message promised open ground. Hoshizora duly sat at a 23.6 ft
# seam, green. WHY 60: the rule has to distinguish a separate quarter from a dense one, and
# dwellings inside a quarter pack at ~10-30 ft, so the seam must be several times that to
# read as a gap at all rather than as a wide lane. Deliberately WELL BELOW the 120 ft
# pollution separation, because this is a zoning statement about who lives beside whom, not
# a buffer against kegare - the burakumin quarter is set apart, not held at arm's length,
# and the historical eta hamlet sits at the village edge or across its stream rather than a
# fixed distance out.


def _seg_0543_010__BURAKUMIN_SEAM_FT(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0543.010 (BURAKUMIN_SEAM_FT) - body verbatim from _seg_0543__town_farmers_plurality (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale == 'town':
        BURAKUMIN_SEAM_FT = 60.0
    return _kept(locals(), ('BURAKUMIN_SEAM_FT',))


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


# A magistrate's manor sits at the EDGE of its settlement; its gate faces what it fronts - the
# town/hamlet it administers (the built-up centroid) OR the Imperial road it sits beside. There is
# no fixed default direction (it depends where the town is); SOUTH is the formal fallback. (At CITY
# scale M['manors'] are the scattered country estates, which face their own lanes - city_estate_gates_vary.)


def _seg_0544__manor_gate_faces_town(
    *,
    GATE_OUT: Any = _UNBOUND,
    M: Any = _UNBOUND,
    ang: Any = _UNBOUND,
    b: Any = _UNBOUND,
    bad_mg: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d: Any = _UNBOUND,
    dirs: Any = _UNBOUND,
    dwell_all: Any = _UNBOUND,
    k: Any = _UNBOUND,
    mn: Any = _UNBOUND,
    mroad: Any = _UNBOUND,
    o: Any = _UNBOUND,
    ovec: Any = _UNBOUND,
    rl: Any = _UNBOUND,
    rp: Any = _UNBOUND,
    rvx: Any = _UNBOUND,
    rvy: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    tl: Any = _UNBOUND,
    tvx: Any = _UNBOUND,
    tvy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 544 (manor_gate_faces_town) - body verbatim from the legacy gate() (feature 022)."""
    if scale in ("hamlet", "town") and M.get("manors"):
        GATE_OUT = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
        dwell_all = M.get("houses", []) + M.get("buildings", [])
        mroad = M.get("road")
        bad_mg = []
        for mn in M.get("manors", []):
            o = GATE_OUT.get(mn.get("gate_dir"), (0, 0))
            ang = math.radians(mn.get("rot", 0))
            ovec = (o[0] * math.cos(ang) - o[1] * math.sin(ang), o[0] * math.sin(ang) + o[1] * math.cos(ang))
            dirs = []
            if dwell_all:
                tvx = sum(b["x"] for b in dwell_all) / len(dwell_all) - mn["x"]
                tvy = sum(b["y"] for b in dwell_all) / len(dwell_all) - mn["y"]
                tl = math.hypot(tvx, tvy) or 1
                dirs.append((tvx / tl, tvy / tl))
            if mroad:
                rp = min((seg_closest(mn["x"], mn["y"], mroad[k], mroad[k + 1]) for k in range(len(mroad) - 1)), key=lambda c: (c[0] - mn["x"]) ** 2 + (c[1] - mn["y"]) ** 2)
                rvx, rvy = rp[0] - mn["x"], rp[1] - mn["y"]
                rl = math.hypot(rvx, rvy) or 1
                dirs.append((rvx / rl, rvy / rl))
            if dirs and max(ovec[0] * d[0] + ovec[1] * d[1] for d in dirs) < 0.45:
                bad_mg.append(mn.get("gate_dir"))
        check(
            "manor_gate_faces_town",
            not bad_mg,
            f"a magistrate's manor gate {bad_mg} faces neither the town it administers nor the road it fronts - "
            f"it sits at the settlement's edge, so its gate should open toward the town/road (no fixed default; south is the formal fallback)",
        )
    return _kept(locals(), ('GATE_OUT', 'ang', 'b', 'bad_mg', 'd', 'dirs', 'dwell_all', 'k', 'mn', 'mroad', 'o', 'ovec', 'rl', 'rp', 'rvx', 'rvy', 'tl', 'tvx', 'tvy'))


def _seg_0545__walled_town_has_fire_tower(*, M: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 545 (walled_town_has_fire_tower) - body verbatim from the legacy gate() (feature 022)."""
    if scale == "town" and meta.get("walled") and meta.get("fire_tower", True):
        # WALLED towns only (GM 2026-07-24, REVERTING the 2026-07 audit widening to all towns).
        # The audit argued an unwalled seat's "packed road-front core burns just the same", but an
        # unwalled town is drawn at detached village grain (bscale 1.0, field gaps for natural
        # breaks) - not the contiguous row fabric the hinomi-yagura historically watched - and
        # real unwalled administrative seats (jin'ya/daikansho towns) kept fire BELLS, stored
        # water, and fireproof kura, not watch towers; the freestanding rural tower is a
        # Meiji-and-later institution. WHY: settlements.md "Fire towers". Opt out per-map with
        # meta(fire_tower=False).
        check("walled_town_has_fire_tower", len(M.get("fire_towers", [])) >= 1, "a walled town's dense wooden core needs a fire-watch tower (s.fire_tower(...); meta(fire_tower=False) to omit)")
    return _kept(locals(), ())


def _seg_0546__hamlet_has_kosatsuba(
    *,
    M: Any = _UNBOUND,
    URBAN: Any = _UNBOUND,
    b: Any = _UNBOUND,
    b_kb: Any = _UNBOUND,
    check: Any = _UNBOUND,
    devs_kb: Any = _UNBOUND,
    edgeon_kb: Any = _UNBOUND,
    face_deg_kb: Any = _UNBOUND,
    far_kb: Any = _UNBOUND,
    floor_kb: Any = _UNBOUND,
    g: Any = _UNBOUND,
    k: Any = _UNBOUND,
    kbs: Any = _UNBOUND,
    lim_gate_kb: Any = _UNBOUND,
    lim_kb: Any = _UNBOUND,
    ln: Any = _UNBOUND,
    mains_kb: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    off_main_kb: Any = _UNBOUND,
    r: Any = _UNBOUND,
    routes_kb: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    st: Any = _UNBOUND,
    uncovered_kb: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 546 (capital_has_kosatsuba, city_has_kosatsuba, city_kosatsuba_per_gate, hamlet_has_kosatsuba, kosatsuba_by_the_road, kosatsuba_faces_the_road, kosatsuba_on_a_main_way, town_has_kosatsuba, village_has_kosatsuba) - body verbatim from the legacy gate() (feature 022)."""
    if scale in ("town", "city", "village", "hamlet") and meta.get("kosatsuba", True):
        # THE OFFICIAL NOTICE BOARD (kosatsuba), default-on at EVERY settlement tier
        # (GM 2026-07-24, from the town deep audit; ported to cities, then to villages
        # and hamlets, the same day). Every Edo settlement down to the hamlet kept the
        # state's edict board - the ofuregaki circulars reached the peasantry through it,
        # via the headman, who was REQUIRED to be functionally literate (he received,
        # copied, and relayed the circulars); one reader per settlement makes the board
        # work, and officials also read notices aloud, so peasant literacy is no
        # objection. Siting was a TRAFFIC decision, not an administrative one: highway
        # frontage, main street by the gate, bridgehead, market corner, the village's
        # main lane - the state talking at everyone who passes (Edo's principal board
        # stood at Nihonbashi). A CITY posted MANY boards, so a city DRAWS the set - the
        # principal board at its central market node PLUS one per main-gate approach
        # corridor (floor = gates + 1; city_kosatsuba_per_gate covers the corridors) -
        # and LABELS only one, whichever board has room for the label (GM 2026-07-24:
        # the same one-label convention as the fire towers and gate markets; an
        # unlabeled board also fits the tight gate verges a labeled one cannot).
        # DISTINCT from the magistrate's manor-gate board (Mode A program, buildings.md):
        # that one posts the bench's OUTPUT (verdicts, bounties) for people who come TO
        # the court, while this one posts standing law - and the manor/yamen deliberately
        # sits away from the busy frontage, so the settlement board must never default
        # there. WHY: settlements.md "Notice board (kosatsuba)". Opt out for a
        # suppressed/backwater seat with meta(kosatsuba=False).
        kbs = M.get("kosatsuba") or []
        floor_kb = (len(M.get("gates") or []) + 1) if scale == "city" else 1
        check(
            f"{scale}_has_kosatsuba",
            len(kbs) >= floor_kb,
            f"a city posts the SET: {floor_kb} boards - the principal at the central market node + one per main gate (s.kosatsuba(...); meta(kosatsuba=False) to omit)"
            if URBAN
            else "the settlement posts the state's standing law on an official notice board (s.kosatsuba(...) or s.place_kosatsuba(); meta(kosatsuba=False) to omit)",
        )
        routes_kb = ([M["road"]] if M.get("road") else []) + [st["pts"] for st in M.get("town_streets", [])] + ([M["lane"]] if M.get("lane") else []) + [ln["pts"] for ln in M.get("lanes", [])]
        lim_kb = 60.0 / float(meta.get("ftpx") or 1)  # ~60 REAL feet at any scale
        if kbs and routes_kb:
            far_kb = [(round(b["x"]), round(b["y"])) for b in kbs if min(seg_dist(b["x"], b["y"], r[k], r[k + 1]) for r in routes_kb for k in range(len(r) - 1)) > lim_kb]
            check("kosatsuba_by_the_road", not far_kb, f"notice board(s) at {far_kb} stand more than ~60 real ft from every road/main street - a kosatsu is read where people pass")
            # ON A MAIN WAY, not merely ON A WAY (GM 2026-08-02, from Ubame: the board stood a
            # legal 49 ft off a side lane while the high street - the road, 23 structures on
            # its frontage - ran 200 ft away; "it should be along the main road, in order to
            # be more noticed"). The kosatsu is the state talking at everyone who passes, and
            # on a map with a way HIERARCHY "everyone" walks the main way: every `roads` entry
            # is a major road by construction (road() draws Imperial trunks and their like)
            # and a `main: True` town street is the gate-to-yamen avenue - so where a map
            # declares either, the board must stand in the siting band of one of THOSE, and a
            # side street or lane within 60 ft satisfies kosatsuba_by_the_road while still
            # burying the institution. Maps whose network is undifferentiated (village/hamlet
            # lane webs, towns with no flagged main street) declare no hierarchy to violate
            # and are exempt - there place_kosatsuba's busiest-node scoring stands in for
            # "main". DELIBERATELY narrower than the punishment ground's siting (GM
            # 2026-08-02: "other map features like punishment grounds don't always need to be
            # along a main road, but a notice board must be" - the ground is a display for
            # locals who already know where justice is done; the board must AMBUSH the eye).
            mains_kb = ([r["pts"] for r in M.get("roads") or []] or ([M["road"]] if M.get("road") else [])) + [st["pts"] for st in M.get("town_streets", []) if st.get("main")]
            if mains_kb:
                off_main_kb = [(round(b["x"]), round(b["y"])) for b in kbs if min(seg_dist(b["x"], b["y"], r[k], r[k + 1]) for r in mains_kb for k in range(len(r) - 1)) > lim_kb]
                check(
                    "kosatsuba_on_a_main_way",
                    not off_main_kb,
                    f"notice board(s) at {off_main_kb} stand off every MAIN way - the board is posted to be noticed, so it goes on the main street/road (a road, or a main: True town street), never a side street or lane (GM 2026-08-02)",
                )
            # ORIENTATION, the other half of siting (GM 2026-07-27, catching Nagahara's third
            # board). A kosatsu is a BROADSIDE signboard: a 7x3 ft face under a little roof,
            # read by someone walking past without leaving the road. Standing it PERPENDICULAR
            # to the road turns the face edge-on to everyone approaching, so the traffic the
            # siting check fought for sees the board's ~6 in of thickness - the institution
            # fails while both the presence and distance checks stay green. Historically the
            # boards stood square to the highway frontage (the post-town kosatsuba, Edo's
            # Nihonbashi high-board) for exactly that reason. The glyph's LONG axis (`rot`) is
            # the board's face, so the rule is: rot must run within FACE_DEG of some route
            # SEGMENT inside the siting band. Any segment in the band counts, not merely the
            # nearest - a board at a junction or on a bend legitimately faces one of the two
            # ways that meet there (Nagahara's north board fronts a cross street 19px off
            # while a perpendicular one passes 15px away; the road-bend boards sit 12-18deg
            # off their nearest segment). 30deg keeps ~87% of the face presented to traffic
            # and leaves ~12deg of headroom over the worst legitimate case in the pool.
            face_deg_kb = 30.0
            edgeon_kb = []
            for b_kb in kbs:
                devs_kb = [
                    abs((float(b_kb.get("rot") or 0.0) - math.degrees(math.atan2(r[k + 1][1] - r[k][1], r[k + 1][0] - r[k][0])) + 90) % 180 - 90)
                    for r in routes_kb
                    for k in range(len(r) - 1)
                    if seg_dist(b_kb["x"], b_kb["y"], r[k], r[k + 1]) <= lim_kb
                ]
                if devs_kb and min(devs_kb) > face_deg_kb:
                    edgeon_kb.append((round(b_kb["x"]), round(b_kb["y"]), round(min(devs_kb))))
            check(
                "kosatsuba_faces_the_road",
                not edgeon_kb,
                f"notice board(s) at {edgeon_kb} (x, y, degrees off) stand edge-on to the way they front - a kosatsu is a broadside signboard, so its long axis runs ALONG the road (rot = the road's bearing), never across it",
            )
        if URBAN and kbs and M.get("gates"):
            # every trafficked gate's approach corridor carries a board (~800 real ft of the
            # gate - the corridor, not the furnished throat itself)
            lim_gate_kb = 800.0 / float(meta.get("ftpx") or 1)
            uncovered_kb = [[round(g[0]), round(g[1])] for g in M["gates"] if min(math.hypot(b["x"] - g[0], b["y"] - g[1]) for b in kbs) > lim_gate_kb]
            check(
                "city_kosatsuba_per_gate",
                not uncovered_kb,
                f"main gate(s) at {uncovered_kb} have no notice board on their approach corridor - a city posted a board at every trafficked gate (draw them all, label ONE)",
            )
    return _kept(
        locals(),
        ('b', 'b_kb', 'devs_kb', 'edgeon_kb', 'face_deg_kb', 'far_kb', 'floor_kb', 'g', 'k', 'kbs', 'lim_gate_kb', 'lim_kb', 'ln', 'mains_kb', 'off_main_kb', 'r', 'routes_kb', 'st', 'uncovered_kb'),
    )


# ===== THE JUSTICE WORKS: the punishment ground (in town) and the execution ground (outside) =====
# Two separate institutions, used at wildly different frequencies and sited by OPPOSITE logics, so
# conflating them would be a modeling error. WHY (all of it): settlements.md "Punishment spot",
# "Execution ground", "Boundary marker". The short version: a county seat HAS an execution ground
# because the Chinese confirmation chain sends the sentence back down to be carried out where the
# crime happened (which is also why the canon county budget funds a jail but no execution line -
# the jail holds the condemned while the warrant travels); Japanese kegare then pushes the ground
# past the built edge. The punishment ground stays in the core because its governing variable is
# foot traffic - it is a DISPLAY, and the beating itself is a court act inside the magistracy.


def _seg_0547__psp_j(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 547 (psp_j) - body verbatim from the legacy gate() (feature 022)."""
    psp_j = M.get("punishment_spots") or []
    return _kept(locals(), ('psp_j',))


def _seg_0548__exg_j(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 548 (exg_j) - body verbatim from the legacy gate() (feature 022)."""
    exg_j = M.get("execution_grounds") or []
    return _kept(locals(), ('exg_j',))


def _seg_0549__bms_j(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 549 (bms_j) - body verbatim from the legacy gate() (feature 022)."""
    bms_j = M.get("boundary_markers") or []
    return _kept(locals(), ('bms_j',))


def _seg_0550__ftpx_j(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 550 (ftpx_j) - body verbatim from the legacy gate() (feature 022)."""
    ftpx_j = float(meta.get("ftpx") or 1)
    return _kept(locals(), ('ftpx_j',))


def _seg_0551__b_3(*, M: Any = _UNBOUND, b: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 551 (b, dwell_j) - body verbatim from the legacy gate() (feature 022)."""
    dwell_j = M.get("houses", []) + [b for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS]
    return _kept(locals(), ('b', 'dwell_j'))


def _seg_0552__wall_j(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 552 (wall_j) - body verbatim from the legacy gate() (feature 022)."""
    wall_j: Poly = M.get("wall") or []
    return _kept(locals(), ('wall_j',))


def _seg_0553___inwall_j(*, px: Any = _UNBOUND, py: Any = _UNBOUND, wall_j: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 553 (_inwall_j) - body verbatim from the legacy gate() (feature 022)."""

    def _inwall_j(px: float, py: float) -> bool:
        return len(wall_j) >= 3 and point_in_poly(px, py, wall_j)

    return _kept(locals(), ('_inwall_j',))


def _seg_0554__punishment_spot_only_at_a_seat_of_justice(*, check: Any = _UNBOUND, exg_j: Any = _UNBOUND, psp_j: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 554 (execution_ground_only_at_a_seat_of_justice, punishment_spot_only_at_a_seat_of_justice) - body verbatim from the legacy gate() (feature 022)."""
    if scale in ("hamlet", "village"):
        # Village authority topped out at banishment, and capital sentences were confirmed far above
        # the county. A settlement with no magistrate's court has neither institution.
        check("punishment_spot_only_at_a_seat_of_justice", not psp_j, f"a {scale} has no magistrate and no court - the punishment ground belongs to a county seat and above")
        check("execution_ground_only_at_a_seat_of_justice", not exg_j, f"a {scale} has no magistrate and no court - the execution ground belongs to a county seat and above")
    return _kept(locals(), ())
