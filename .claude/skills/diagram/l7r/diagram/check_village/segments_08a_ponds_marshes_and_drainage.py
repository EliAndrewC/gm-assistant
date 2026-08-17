"""Gate segments (ponds marshes and drainage; keys 0513-0523_018) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from l7r.diagram.waterfields import drain_bank_clearance, polyline_cum

from .common_01_geometry import Pt, point_in_poly, seg_dist
from .common_02_overlap_policy import in_ellipse
from .common_03_capacity import _UNBOUND, _kept

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
