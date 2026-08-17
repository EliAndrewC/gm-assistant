"""Gate segments (channels and bridge spans; keys 0410-0438_010) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from l7r.diagram.settlement import sat_overlap

from .common_01_geometry import Poly, Pt, _struct_rect, point_in_poly, poly_dist, rect_corners, seg_dist, seg_intersect, segments_cross
from .common_02_overlap_policy import FOOT_BANK_REACH, _ditch_plankable, _footbridge_useful_ground, in_ellipse
from .common_03_capacity import _UNBOUND, _kept

# WATER-SERVICE FURNITURE SITS ON ITS WATER (GM 2026-08-10, four features caught beached
# on the shipped first pass: the river's course was re-routed during the wall re-derivation
# and the shore furniture kept its old seats). A towpath EXISTS to walk the hauling line
# along the bank; a sluice gate regulates a flow it must stand in; an aqueduct taps its
# river at the intake and its settling basin lands on DRY ground (one ended in the moat);
# a tannery needs its wash water at the door. All measured to real watercourse geometry,
# so a re-routed channel drags its furniture red instead of leaving it beached - the
# placement fix is always: recompute the seat from the CURRENT water polyline, never keep
# a coordinate that predates a re-route.
# every WATERCOURSE counts, irrigation channels included - a sluice on a field ditch is the
# commonest form of the feature, and omitting channels read three shipped maps as "dry"


def _seg_0410__ch9_1(*, M: Any = _UNBOUND, ch9: Any = _UNBOUND, cn9: Any = _UNBOUND, w9: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 410 (ch9, cn9, w9, wsf_waters) - body verbatim from the legacy gate() (feature 022)."""
    wsf_waters = (
        [(w9["poly"], float(w9.get("w", 9))) for w9 in M.get("streams", [])]
        + [(cn9["poly"], float(cn9.get("w", 12))) for cn9 in M.get("canals", [])]
        + [(ch9["poly"], float(ch9.get("w", 2.5))) for ch9 in M.get("channels", []) if ch9.get("poly")]
    )
    return _kept(locals(), ('ch9', 'cn9', 'w9', 'wsf_waters'))


def _seg_0411__wsf_bank(
    *, best: Any = _UNBOUND, d9: Any = _UNBOUND, i9: Any = _UNBOUND, wp9: Any = _UNBOUND, wsf_waters: Any = _UNBOUND, ww9: Any = _UNBOUND, x9: Any = _UNBOUND, y9: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 411 (wsf_bank) - body verbatim from the legacy gate() (feature 022)."""

    def wsf_bank(x9: float, y9: float) -> float:
        """Distance past the nearest watercourse's bank (<=0 means on/over the water)."""
        best = 1e9
        for wp9, ww9 in wsf_waters:
            d9 = min(seg_dist(x9, y9, wp9[i9], wp9[i9 + 1]) for i9 in range(len(wp9) - 1))
            best = min(best, d9 - ww9 / 2)
        return best

    return _kept(locals(), ('wsf_bank',))


def _seg_0412__towpath_hugs_the_bank(
    *,
    M: Any = _UNBOUND,
    ap9: Any = _UNBOUND,
    aq9: Any = _UNBOUND,
    aq_bad: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d9: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    mo9: Any = _UNBOUND,
    p9: Any = _UNBOUND,
    sg9: Any = _UNBOUND,
    sl_bad: Any = _UNBOUND,
    sl_waters: Any = _UNBOUND,
    tow_bad: Any = _UNBOUND,
    tp9: Any = _UNBOUND,
    ty9: Any = _UNBOUND,
    ty_bad: Any = _UNBOUND,
    wp9: Any = _UNBOUND,
    wsf_bank: Any = _UNBOUND,
    wsf_waters: Any = _UNBOUND,
    ww9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 412 (aqueduct_taps_water_lands_dry, sluice_gates_on_water, tanning_yards_on_water, towpath_hugs_the_bank) - body verbatim from the legacy gate() (feature 022)."""
    if wsf_waters:
        tow_bad = []
        for tp9 in M.get("towpaths", []):
            for p9 in tp9.get("pts", tp9.get("poly", [])):
                d9 = wsf_bank(p9[0], p9[1])
                if d9 > 30 or d9 < -6:
                    tow_bad.append((round(p9[0]), round(p9[1]), round(d9)))
        check(
            "towpath_hugs_the_bank",
            not tow_bad,
            f"towpath vertex(es) off the river bank (px past the bank, want -6..30): {tow_bad[:4]} - a towpath IS the hauling line's bank walk, so it runs alongside the water for its whole length; re-derive the polyline by offsetting the CURRENT river centerline ~(w/2+10) landward, never keep pre-re-route coordinates",
        )
        sl_waters = wsf_waters + ([(M["moat"], float(M.get("moat_width", 22)))] if M.get("moat") else [])
        sl_bad = []
        for sg9 in M.get("sluice_gates", []):
            d9 = min(min(seg_dist(sg9["x"], sg9["y"], wp9[i9], wp9[i9 + 1]) for i9 in range(len(wp9) - 1)) - ww9 / 2 for wp9, ww9 in sl_waters)
            if d9 > 6:
                sl_bad.append((round(sg9["x"]), round(sg9["y"]), round(d9)))
        check(
            "sluice_gates_on_water",
            not sl_bad,
            f"sluice gate(s) standing on dry ground (px past the nearest bank): {sl_bad[:4]} - a sluice regulates a flow it must stand IN; re-seat it on the current watercourse centerline (snap to the nearest polyline point), never keep a seat that predates a re-route",
        )
        aq_bad = []
        for aq9 in M.get("aqueducts", []):
            ap9 = aq9.get("poly", [])
            if len(ap9) >= 2:
                d9 = wsf_bank(ap9[0][0], ap9[0][1])
                # BOUNDED ON BOTH SIDES (GM 2026-08-10: "the aqueduct begins in the middle of the
                # river instead of at the edge"). The first cut only capped the intake from above,
                # so a head works standing mid-channel - which is not a thing anyone builds; you
                # cannot maintain a screen or a sluice board you cannot stand at - measured as
                # NEGATIVE distance-past-the-bank and passed. An intake sits AT the bank: on it,
                # or a step or two of dry ground behind it.
                if d9 > 10 or d9 < -4:
                    aq_bad.append(("intake", round(ap9[0][0]), round(ap9[0][1]), round(d9)))
                if M.get("moat"):
                    mo9 = min(seg_dist(ap9[-1][0], ap9[-1][1], M["moat"][i9], M["moat"][i9 + 1]) for i9 in range(len(M["moat"]) - 1))
                    if mo9 < float(M.get("moat_width", 22)) / 2 + 8:
                        aq_bad.append(("terminus-in-moat", round(ap9[-1][0]), round(ap9[-1][1]), round(mo9)))
        check(
            "aqueduct_taps_water_lands_dry",
            not aq_bad,
            f"aqueduct end(s) mis-seated: {aq_bad[:4]} - the intake taps the river (within ~10px of the bank) and the terminus/settling basin lands on DRY ground clear of the moat; trim or extend the polyline against the CURRENT water and moat geometry",
        )
        ty_bad = []
        for ty9 in M.get("tanning_yards", []):
            d9 = wsf_bank(ty9["x"], ty9["y"])
            if d9 * float(meta.get("ftpx", 1) or 1) > 90.0:  # 90 real ft - the yard's own working ground, not a field between it and the water (the pool sits at 18-48 ft)
                ty_bad.append((round(ty9["x"]), round(ty9["y"]), round(d9)))
        check(
            "tanning_yards_on_water",
            not ty_bad,
            f"tanning yard(s) off their water (px past the nearest bank, want <= 90 real ft): {ty_bad[:4]} - tanning is a WASH trade: the yard stands AT the bank it draws from and drains to, its long side along the water (downwind/downstream arc still applies)",
        )
    return _kept(locals(), ('ap9', 'aq9', 'aq_bad', 'd9', 'i9', 'mo9', 'p9', 'sg9', 'sl_bad', 'sl_waters', 'tow_bad', 'tp9', 'ty9', 'ty_bad', 'wp9', 'ww9'))


def _seg_0413__bridges_seat_on_water(*, b_dry: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 413 (bridges_seat_on_water) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "bridges_seat_on_water",
        not b_dry,
        f"deck(s) seated on NO watercourse: {sorted(set(b_dry))[:4]} - the way's crossing moved and the deck kept "
        f"its old seat; recompute the way x water segment intersection and re-seat the deck there (or delete it)",
    )
    return _kept(locals(), ())


def _seg_0414__bridges_span_their_water(*, b_short: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 414 (bridges_span_their_water) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "bridges_span_their_water",
        not b_short,
        f"deck(s) with a corner at or short of dry ground past the bank - the abutment would stand in the water: {sorted(set(b_short))[:4]}; "
        f"an oblique crossing needs (width + deck_w*|cos|)/sin plus a landing each side; let s.bridges() size it, or lengthen the hand-placed span",
    )
    return _kept(locals(), ())


# STANDALONE plank FOOTBRIDGES on the irrigation ditches (opt-in via meta.field_footbridges): field-workers
# cross a ditch on a plank while walking the bunds, so any long ditch stretch carries at least one plank
# about midway (these are NOT lane crossings - no path leads to them). Fires if a long ditch has none near it.
# EXEMPT the polder ring's UNSETTLED sides (research 2026-07-22, settlements.md 'Polder ring canal'):
# crossings cluster on the settlement (east) toe, and the feeder / far toe / drain are walked on the DIKE
# CREST, crossed (if at all) at a sluice/culvert, NOT a plank - so those tagged segs need no footbridge.


def _seg_0415__long_ditches_have_a_footbridge(
    *,
    FB_MIN: Any = _UNBOUND,
    M: Any = _UNBOUND,
    _fa: Any = _UNBOUND,
    _no_plank_segs: Any = _UNBOUND,
    _plank_good: Any = _UNBOUND,
    b: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d: Any = _UNBOUND,
    i: Any = _UNBOUND,
    length: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    pts: Any = _UNBOUND,
    reach: Any = _UNBOUND,
    stranded: Any = _UNBOUND,
    unplanked: Any = _UNBOUND,
    ux: Any = _UNBOUND,
    uy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 415 (footbridges_reach_useful_ground, long_ditches_have_a_footbridge) - body verbatim from the legacy gate() (feature 022)."""
    if meta.get("field_footbridges"):
        FB_MIN = 140
        _no_plank_segs = {"feeder", "w_toe", "drain"}
        _plank_good = _footbridge_useful_ground(M)
        unplanked = []
        for d in M.get("field_ditches", []):
            if d.get("seg") in _no_plank_segs:
                continue
            pts = d["poly"]
            length = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
            if length < FB_MIN:
                continue
            # ...and `_ditch_plankable` now also asks whether the water is wide enough to be worth a
            # board AT THE SAME POINT it finds useful ground, which is the pair of conditions the
            # placer has to satisfy at a seat. One test, not two independent ones - see its docstring.
            if not _ditch_plankable(pts, d.get("w", 4.2), _plank_good, float(d.get("w_tail", d.get("w", 4.2))), meta.get("ftpx", 1.0)):
                continue  # a margin/toe ditch with nothing to cross TO needs no plank (footbridges_reach_useful_ground)
            if not any(poly_dist(b["x"], b["y"], pts) <= 20 for b in M.get("bridges", [])):
                unplanked.append((round(pts[0][0]), round(pts[0][1])))
        check(
            "long_ditches_have_a_footbridge",
            not unplanked,
            f"{len(unplanked)} long irrigation ditch(es) with no plank footbridge near {unplanked[:4]} - a long ditch stretch needs a plank about midway (call s.channel_footbridges())",
        )

        # A standalone plank FOOTBRIDGE (tagged 'foot') is only worth building if BOTH banks reach ground a
        # field-worker walks to - cultivated field, the village, or a dike. A plank whose far bank opens onto
        # reed marsh / scrub / off-map connects the fields to nowhere (GM 2026-07-22, Hikari no Sato: drain-toe
        # planks that stepped straight into the marsh). Lane-carried crossings (s.bridges(), untagged) are
        # exempt - a path leads to them by construction. The deck spans the ditch along `rot`, so its ends are
        # the two banks; each is sampled a short reach past its abutment.
        stranded = []
        for b in M.get("bridges", []):
            if not b.get("foot"):
                continue
            _fa = math.radians(b.get("rot", 0.0))
            ux, uy = math.cos(_fa), math.sin(_fa)
            reach = b["span"] / 2 + FOOT_BANK_REACH
            if not (_plank_good(b["x"] + ux * reach, b["y"] + uy * reach) and _plank_good(b["x"] - ux * reach, b["y"] - uy * reach)):
                stranded.append((round(b["x"]), round(b["y"])))
        check(
            "footbridges_reach_useful_ground",
            not stranded,
            f"{len(stranded)} plank footbridge(s) cross to non-cultivated ground (marsh/scrub/off-map) at {stranded[:4]} - a standalone footplank must reach field/village/dike on BOTH banks; drop it or slide it onto a useful crossing",
        )
    return _kept(locals(), ('FB_MIN', '_fa', '_no_plank_segs', '_plank_good', 'b', 'd', 'i', 'length', 'pts', 'reach', 'stranded', 'unplanked', 'ux', 'uy'))


# A plank bridge is overlap-EXEMPT in general (it intentionally sits ON the water it spans), but it must
# never land on a FARMHOUSE - a plank crosses a ditch, it does not sit on a home. Rotated-rect SAT of each
# bridge deck (span x deck-width) against every house footprint.


def _seg_0416__h_3(*, M: Any = _UNBOUND, h: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 416 (h, house_corners) - body verbatim from the legacy gate() (feature 022)."""
    house_corners = [rect_corners(_struct_rect(h)) for h in M.get("houses", [])]
    return _kept(locals(), ('h', 'house_corners'))


def _seg_0417__on_house() -> dict[str, Any]:
    """Gate segment 417 (on_house) - body verbatim from the legacy gate() (feature 022)."""
    on_house = []  # type: ignore[var-annotated]
    return _kept(locals(), ('on_house',))


def _seg_0418__b_2(*, M: Any = _UNBOUND, b: Any = _UNBOUND, deck: Any = _UNBOUND, hc: Any = _UNBOUND, house_corners: Any = _UNBOUND, on_house: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 418 (b, deck, hc, on_house) - body verbatim from the legacy gate() (feature 022)."""
    for b in M.get("bridges", []):
        deck = rect_corners({"x": b["x"], "y": b["y"], "w": b["span"], "h": b["w"], "rot": b.get("rot", 0)})
        if any(sat_overlap(deck, hc) for hc in house_corners):
            on_house.append((round(b["x"]), round(b["y"])))
    return _kept(locals(), ('b', 'deck', 'hc', 'on_house'))


def _seg_0419__bridges_clear_of_houses(*, check: Any = _UNBOUND, on_house: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 419 (bridges_clear_of_houses) - body verbatim from the legacy gate() (feature 022)."""
    check("bridges_clear_of_houses", not on_house, f"{len(on_house)} plank bridge(s) overlap a farmhouse at {on_house[:4]} - a plank spans a ditch, it must not sit on a home")
    return _kept(locals(), ())


# WHERE WATERCOURSES MEET they must MERGE like a confluence, not stack opacity into a dark seam.
# All water BEDS render below all water SHEENS (the shared-opacity bed group composites first, the
# lighter mid-current group on top), exactly as road beds merge at a crossroads - so at every place
# two courses CROSS or one FEEDS INTO another, the higher-drawn course's opaque bed must not paint
# over the other's sheen. Checked via the recorded bed/sheen draw positions (bedz / sheenz).


def _seg_0420__s(*, M: Any = _UNBOUND, s: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 420 (s, ways) - body verbatim from the legacy gate() (feature 022)."""
    ways = [(s["poly"], s.get("bedz"), s.get("sheenz")) for s in M.get("streams", [])]
    return _kept(locals(), ('s', 'ways'))


def _seg_0421__c_4(*, M: Any = _UNBOUND, c: Any = _UNBOUND, ways: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 421 (c, ways) - body verbatim from the legacy gate() (feature 022)."""
    ways += [(c["poly"], c.get("bedz"), c.get("sheenz")) for c in M.get("channels", [])]
    return _kept(locals(), ('c', 'ways'))


def _seg_0422__ml(*, M: Any = _UNBOUND, ml: Any = _UNBOUND, ways: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 422 (ml, ways) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("moat") and M.get("moat_layer"):
        ml = M["moat_layer"]
        ways.append((M["moat"], ml.get("bedz"), ml.get("sheenz")))
    return _kept(locals(), ('ml', 'ways'))


def _seg_0423___water_meet(*, i: Any = _UNBOUND, j: Any = _UNBOUND, pa: Any = _UNBOUND, pb: Any = _UNBOUND, pt: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 423 (_water_meet) - body verbatim from the legacy gate() (feature 022)."""

    def _water_meet(pa: Poly, pb: Poly) -> Pt | None:
        for i in range(len(pa) - 1):
            for j in range(len(pb) - 1):
                if segments_cross(pa[i], pa[i + 1], pb[j], pb[j + 1]):
                    return seg_intersect(pa[i], pa[i + 1], pb[j], pb[j + 1])
        for pt in (pa[0], pa[-1]):  # a feeder's endpoint sitting ON the other course
            if poly_dist(pt[0], pt[1], pb) <= 12:
                return pt
        for pt in (pb[0], pb[-1]):
            if poly_dist(pt[0], pt[1], pa) <= 12:
                return pt
        return None

    return _kept(locals(), ('_water_meet',))


def _seg_0424__seams() -> dict[str, Any]:
    """Gate segment 424 (seams) - body verbatim from the legacy gate() (feature 022)."""
    seams = []  # type: ignore[var-annotated]
    return _kept(locals(), ('seams',))


def _seg_0425__ba(
    *,
    _water_meet: Any = _UNBOUND,
    ba: Any = _UNBOUND,
    bb: Any = _UNBOUND,
    i: Any = _UNBOUND,
    j: Any = _UNBOUND,
    pa: Any = _UNBOUND,
    pb: Any = _UNBOUND,
    pt: Any = _UNBOUND,
    sa: Any = _UNBOUND,
    sb: Any = _UNBOUND,
    seams: Any = _UNBOUND,
    sheens: Any = _UNBOUND,
    ways: Any = _UNBOUND,
    z: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 425 (ba, bb, i, j) - body verbatim from the legacy gate() (feature 022)."""
    for i in range(len(ways)):
        for j in range(i + 1, len(ways)):
            pa, ba, sa = ways[i]
            pb, bb, sb = ways[j]
            if ba is None or bb is None:
                continue
            pt = _water_meet(pa, pb)
            sheens = [z for z in (sa, sb) if z is not None]
            if pt is not None and sheens and max(ba, bb) > min(sheens):
                seams.append((round(pt[0]), round(pt[1])))
    return _kept(locals(), ('ba', 'bb', 'i', 'j', 'pa', 'pb', 'pt', 'sa', 'sb', 'seams', 'sheens', 'z'))


def _seg_0426__waterways_merge_at_crossings(*, check: Any = _UNBOUND, seams: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 426 (waterways_merge_at_crossings) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "waterways_merge_at_crossings",
        not seams,
        f"watercourses overlap instead of merging at {sorted(set(seams))} - a higher-drawn bed paints over "
        f"another course's sheen (stacking into a dark seam); route all water through s.stream / s.channel / "
        f"s.moat so the shared bed and sheen groups composite it as one confluence",
    )
    return _kept(locals(), ())


# A CHANNEL MEETS ITS STREAM AT A CONFLUENCE - waterways join like roads do, at BOTH ends. A
# channel declaring to={"kind":"stream"} (a drain culvert) must actually REACH the receiving
# bed, and one declaring frm={"kind":"stream"} (an intake/offtake) must actually START in the
# feeding bed: the recorded endpoint within the stream's half-width (+2px) of the centerline,
# so the mouth sits in the water. The anchor test alone allows 30px, which let a culvert die in
# the grass beside the stream (GM caught the drain side on Hirameki, then the intake side on
# Hoshizora, 2026-07). Extend/snap the recorded polyline to the centerline; `_clip_to_stream`
# trims the DRAWN mouth back onto the bed edge so it never paints a tongue across the current.


def _seg_0427___bed_reach(*, M: Any = _UNBOUND, i: Any = _UNBOUND, pt: Any = _UNBOUND, sp: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 427 (_bed_reach) - body verbatim from the legacy gate() (feature 022)."""

    def _bed_reach(pt: Pt) -> float | None:
        return min(
            (seg_dist(pt[0], pt[1], sp[i], sp[i + 1]) - st.get("w", 9) / 2 for st in M.get("streams", []) for sp in [st["poly"]] for i in range(len(sp) - 1)),
            default=None,
        )

    return _kept(locals(), ('_bed_reach',))


def _seg_0428__dry_mouths() -> dict[str, Any]:
    """Gate segment 428 (dry_mouths) - body verbatim from the legacy gate() (feature 022)."""
    dry_mouths = []  # type: ignore[var-annotated]
    return _kept(locals(), ('dry_mouths',))


def _seg_0429__anc(
    *, M: Any = _UNBOUND, _bed_reach: Any = _UNBOUND, anc: Any = _UNBOUND, c: Any = _UNBOUND, chan_ends: Any = _UNBOUND, dry_mouths: Any = _UNBOUND, pt: Any = _UNBOUND, reach: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 429 (anc, c, chan_ends, dry_mouths) - body verbatim from the legacy gate() (feature 022)."""
    for c in M.get("channels", []):
        chan_ends: list[tuple[dict[str, Any], Any]] = [(c.get("to") or {}, c["poly"][-1]), (c.get("frm") or {}, c["poly"][0])]  # type: ignore[no-redef]
        for anc, pt in chan_ends:
            if anc.get("kind") != "stream":
                continue
            reach = _bed_reach(pt)
            if reach is None or reach > 2:
                dry_mouths.append((round(pt[0]), round(pt[1])))
    return _kept(locals(), ('anc', 'c', 'chan_ends', 'dry_mouths', 'pt', 'reach'))


# A DRAIN COLLECTOR'S FREE END REACHES WATER. A collector endpoint may sit among its own
# plots (the lo-end begins at the westmost delivery's bottom) or run off-map - but an on-map
# drain end OUTSIDE the planted extent that touches no other watercourse is runoff dying in
# bare ground (GM, Hirameki 2026-07: w2's collector ended mid-air beside the stream). Scoped
# to role='drain' (delivery tails END mid-crop by tagoshi doctrine; supply-canal tails taper
# past their last offtake) with the planted extent grown 14px and a 12px touch tolerance.


def _seg_0430__fdef(*, M: Any = _UNBOUND, fdef: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 430 (fdef, vis_by_field) - body verbatim from the legacy gate() (feature 022)."""
    vis_by_field = {fdef["name"]: fdef.get("vis_bbox") or fdef["bbox"] for fdef in M.get("fields", [])}
    return _kept(locals(), ('fdef', 'vis_by_field'))


def _seg_0431__all_ways(*, M: Any = _UNBOUND, c: Any = _UNBOUND, dd: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 431 (all_ways, c, dd, st) - body verbatim from the legacy gate() (feature 022)."""
    all_ways = [st["poly"] for st in M.get("streams", [])] + [c["poly"] for c in M.get("channels", [])] + [dd["poly"] for dd in M.get("field_ditches", [])] + ([M["moat"]] if M.get("moat") else [])
    return _kept(locals(), ('all_ways', 'c', 'dd', 'st'))


def _seg_0432__dry_drains() -> dict[str, Any]:
    """Gate segment 432 (dry_drains) - body verbatim from the legacy gate() (feature 022)."""
    dry_drains = []  # type: ignore[var-annotated]
    return _kept(locals(), ('dry_drains',))


def _seg_0433__dd(
    *,
    EX0: Any = _UNBOUND,
    EX1: Any = _UNBOUND,
    EY0: Any = _UNBOUND,
    EY1: Any = _UNBOUND,
    M: Any = _UNBOUND,
    all_ways: Any = _UNBOUND,
    dd: Any = _UNBOUND,
    dgap: Any = _UNBOUND,
    dry_drains: Any = _UNBOUND,
    endp: Any = _UNBOUND,
    k: Any = _UNBOUND,
    pl: Any = _UNBOUND,
    vb: Any = _UNBOUND,
    vis_by_field: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 433 (dd, dgap, dry_drains, endp) - body verbatim from the legacy gate() (feature 022)."""
    for dd in M.get("field_ditches", []):
        if dd.get("role") not in ("drain", "main"):
            continue  # delivery/lateral tails END mid-crop by tagoshi doctrine
        vb = vis_by_field.get(dd["field"])
        for endp in (dd["poly"][0], dd["poly"][-1]):
            if not (12 < endp[0] < EX1 - 12 and 12 < endp[1] < EY1 - 12) or endp[0] < EX0 + 12 or endp[1] < EY0 + 12:
                continue  # an off-map (or map-edge) end discharges beyond the frame
            if vb and vb[0] - 18 <= endp[0] <= vb[2] + 18 and vb[1] - 18 <= endp[1] <= vb[3] + 18:
                continue  # at/among the planted plots: an in-crop end. A canal tail past its last
                # offtake legitimately dies at the crop edge; margin 18 calibrated so the approved
                # honda/shimizu/kikuta/hikari-east tails stay legal (GM audit 2026-07 widened this
                # check from drain-only to main pieces too)
            dgap: float | None = min(  # type: ignore[no-redef]
                (min(seg_dist(endp[0], endp[1], pl[k], pl[k + 1]) for k in range(len(pl) - 1)) for pl in all_ways if pl is not dd["poly"]),
                default=None,
            )
            if dgap is None or dgap > 12:
                dry_drains.append((round(endp[0]), round(endp[1])))
    return _kept(locals(), ('dd', 'dgap', 'dry_drains', 'endp', 'k', 'pl', 'vb'))


# TOWN MARGINS ARE CLOTHED TOO (GM audit 2026-07). The village satoyama rule
# (margins_form_continuous_ring) deliberately excludes towns because its cover model knows
# nothing of urban fabric - so this TOWN variant counts the urban features as cover: every
# structure box, road/street/lane verges, watercourses, the hill, the pond, and ALL ground
# INSIDE the rampart (a walled town's open interior is squares and yards - urban floor, not
# wasteland). What remains must be clothed (fields, hems, pastures, marsh, groves, grazing
# commons scrub) to within a laxer allowance than a village's 12% - open worked commons
# around a county seat are real. Sampled on a 25px grid like the village check.


def _seg_0434__town_margins_clothed(
    *,
    EX0: Any = _UNBOUND,
    EX1: Any = _UNBOUND,
    EY0: Any = _UNBOUND,
    EY1: Any = _UNBOUND,
    M: Any = _UNBOUND,
    bx0: Any = _UNBOUND,
    bx1: Any = _UNBOUND,
    by0: Any = _UNBOUND,
    by1: Any = _UNBOUND,
    c2_: Any = _UNBOUND,
    c_: Any = _UNBOUND,
    check: Any = _UNBOUND,
    covered: Any = _UNBOUND,
    d_: Any = _UNBOUND,
    f_: Any = _UNBOUND,
    g_: Any = _UNBOUND,
    hw_: Any = _UNBOUND,
    i_: Any = _UNBOUND,
    k_: Any = _UNBOUND,
    ln_: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    o_: Any = _UNBOUND,
    p_: Any = _UNBOUND,
    pl_: Any = _UNBOUND,
    road: Any = _UNBOUND,
    s_: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    st_: Any = _UNBOUND,
    tm_bare: Any = _UNBOUND,
    tm_boxes: Any = _UNBOUND,
    tm_frac: Any = _UNBOUND,
    tm_halo: Any = _UNBOUND,
    tm_hill: Any = _UNBOUND,
    tm_lines: Any = _UNBOUND,
    tm_polys: Any = _UNBOUND,
    tm_pond: Any = _UNBOUND,
    tm_total: Any = _UNBOUND,
    tm_wall: Any = _UNBOUND,
    tx: Any = _UNBOUND,
    ty: Any = _UNBOUND,
    v_: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 434 (town_margins_clothed) - body verbatim from the legacy gate() (feature 022)."""
    if scale == "town":
        tm_polys = [f_["outline"] for f_ in M.get("fields", [])] + [f_["outline"] for f_ in M.get("flower_fields", [])]
        for k_ in ("commons", "marshes", "village_groves", "dry_plots", "pastures", "forest_patches"):
            for o_ in M.get(k_, []) or []:
                p_ = o_.get("poly") if isinstance(o_, dict) else o_
                if p_ is not None and len(p_) >= 3:
                    tm_polys.append(p_)
        tm_boxes = []
        # structure boxes grow by the URBAN-CLEARANCE halo (30 ft, converted at the map's grain), not a
        # token 8px: the swept/trodden ground around every occupied structure - dooryards, alleys, drying
        # ground - is URBAN FLOOR, the unwalled-town equivalent of the walled case's inside-the-rampart
        # exemption. Without this, forbidding scrub over the built-up area (scrub_clear_of_urban_fabric
        # below) would re-count all that working ground as "bare" and the two checks would fight.
        tm_halo = 30.0 / (meta.get("ftpx") or 1)
        for v_ in M.values():
            if isinstance(v_, list) and v_ and isinstance(v_[0], dict) and "x" in v_[0] and "w" in v_[0] and "h" in v_[0]:
                for o_ in v_:
                    tm_boxes.append((o_["x"] - o_["w"] / 2 - tm_halo, o_["y"] - o_["h"] / 2 - tm_halo, o_["x"] + o_["w"] / 2 + tm_halo, o_["y"] + o_["h"] / 2 + tm_halo))
        for g_ in M.get("village_groves", []):
            for c_ in g_.get("clumps", []):
                tm_boxes.append((c_[0] - 16, c_[1] - 16, c_[0] + 16, c_[1] + 16))
        tm_lines = []
        if road:
            tm_lines.append((road, 60.0))
        tm_lines += [(st_["pts"], st_["w"] / 2 + 40) for st_ in M.get("town_streets", [])]
        tm_lines += [(ln_["pts"], 30.0) for ln_ in M.get("lanes", [])]
        tm_lines += [(s_["poly"], 30.0) for s_ in M.get("streams", [])] + [(c2_["poly"], 24.0) for c2_ in M.get("channels", [])] + [(d_["poly"], 20.0) for d_ in M.get("field_ditches", [])]
        tm_wall = M.get("wall")
        if tm_wall:
            tm_lines.append((tm_wall, 40.0))
        tm_hill = M.get("hill")
        tm_pond = M.get("pond")
        tm_bare = tm_total = 0
        ty = EY0 + 12.5
        while ty < EY1:
            tx = EX0 + 12.5
            while tx < EX1:
                tm_total += 1
                covered = (
                    any(bx0 <= tx <= bx1 and by0 <= ty <= by1 for bx0, by0, bx1, by1 in tm_boxes)
                    or (tm_wall is not None and len(tm_wall) >= 3 and point_in_poly(tx, ty, tm_wall))
                    or any(point_in_poly(tx, ty, p_) for p_ in tm_polys)
                    or any(any(seg_dist(tx, ty, pl_[i_], pl_[i_ + 1]) < hw_ for i_ in range(len(pl_) - 1)) for pl_, hw_ in tm_lines)
                    or (tm_hill is not None and in_ellipse(tx, ty, tm_hill, 1.45))
                    or (tm_pond is not None and in_ellipse(tx, ty, [tm_pond[0], tm_pond[1], tm_pond[2] + 30, tm_pond[3] + 30]))
                )
                if not covered:
                    tm_bare += 1
                tx += 25
            ty += 25
        tm_frac = tm_bare / tm_total if tm_total else 1.0
        check(
            "town_margins_clothed",
            tm_frac <= 0.20,
            f"{tm_frac:.0%} of the town sheet is bare open ground (over the 20% allowance) - a county seat's margins are worked land: clothe the aprons in grazing commons scrub / pasture / marsh / coppice (s.commons(..., role='grazing') bands; the ground inside the rampart counts as urban floor)",
        )
    return _kept(
        locals(),
        (
            'bx0',
            'bx1',
            'by0',
            'by1',
            'c2_',
            'c_',
            'covered',
            'd_',
            'f_',
            'g_',
            'hw_',
            'i_',
            'k_',
            'ln_',
            'o_',
            'p_',
            'pl_',
            's_',
            'st_',
            'tm_bare',
            'tm_boxes',
            'tm_frac',
            'tm_halo',
            'tm_hill',
            'tm_lines',
            'tm_polys',
            'tm_pond',
            'tm_total',
            'tm_wall',
            'tx',
            'ty',
            'v_',
        ),
    )


# SCRUB STAYS OUT OF THE BUILT-UP FABRIC (GM 2026-07-21, Hoshizora). The old doctrine let a gen
# draw GENEROUS scrub polys over the town and trust the scatter's per-point skips - but those
# skips only cleared building FOOTPRINTS, so scrub speckled the streets, dooryards, and gaps
# between the shops, merchant houses, laborer housing, and the burakumin quarter, and crowded
# right up to the wellheads. The rule: settlement ground is CLEARED - the daily traffic, sweeping,
# and fuel/fodder-gathering pressure of the inhabitants strips brush from the built-up area first,
# so scrub survives only on the OUTSKIRTS, beyond the last dwellings. The recorded poly must
# therefore itself trace the outskirts: no occupied structure's or wellhead's CENTER may lie inside
# a commons cover poly (any role - grazing scrub, pasture, coppice woodland). The engine's draw-time
# urban-clearance halo additionally keeps the scatter off fringe features that merely ABUT an
# apron; this check governs the claimed REGION, and is order-blind, so a structure drawn AFTER the
# scrub fires all the same. Field BARNS are exempt: a hay barn stands in the grazed ground it
# serves (Hoshizora's SE pasture barns are the canonical case). SCOPED TO town/city: at
# village/hamlet scale the satoyama doctrine deliberately interleaves the settlement with its
# marginal scrub - dispersed farmsteads stand ON the unirrigated waste (Akagahara), the
# water-mouth shrine sits IN its commons (Ueda), and the margin ring spans whole map edges -
# so there only the engine halo applies (every feature's curtilage stays clear, but the polys
# legitimately contain features).


def _seg_0435__scrub_urban() -> dict[str, Any]:
    """Gate segment 435 (scrub_urban) - body verbatim from the legacy gate() (feature 022)."""
    scrub_urban = []  # type: ignore[var-annotated]
    return _kept(locals(), ('scrub_urban',))


def _seg_0436__cp_(*, M: Any = _UNBOUND, cp_: Any = _UNBOUND, cv_: Any = _UNBOUND, o_: Any = _UNBOUND, scale: Any = _UNBOUND, scrub_urban: Any = _UNBOUND, uk_: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 436 (cp_, cv_, o_, scrub_urban) - body verbatim from the legacy gate() (feature 022)."""
    for cv_ in M.get("commons", []) if scale in ("town", "city") else []:
        cp_ = cv_.get("poly")
        if not cp_ or len(cp_) < 3:
            continue
        for uk_ in ("houses", "buildings", "wells", "storehouses", "flophouses", "religious", "shrines", "manors", "ministries"):
            for o_ in M.get(uk_, []) or []:
                if uk_ == "buildings" and o_.get("kind") == "barn":
                    continue  # a field barn stands in its pasture/commons - that is where hay barns live
                if point_in_poly(o_["x"], o_["y"], cp_):
                    scrub_urban.append((uk_, o_.get("kind", ""), round(o_["x"]), round(o_["y"])))
    return _kept(locals(), ('cp_', 'cv_', 'o_', 'scrub_urban', 'uk_'))


def _seg_0437__scrub_clear_of_urban_fabric(*, check: Any = _UNBOUND, scrub_urban: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 437 (scrub_clear_of_urban_fabric) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "scrub_clear_of_urban_fabric",
        not scrub_urban,
        f"{len(scrub_urban)} urban feature(s) stand INSIDE a scrub/pasture/coppice cover poly (key, kind, x, y): {scrub_urban[:6]} - "
        "settlement ground is cleared; scrub lives on the OUTSKIRTS only. Redraw the commons poly to hug the "
        "built-up edge (the engine's urban-clearance halo protects fringe features that abut an apron; a poly "
        "that CONTAINS a dwelling/shop/well is claiming grazed waste where the town stands)",
    )
    return _kept(locals(), ())


# NEAR-RING FARMLAND DENSITY (feature 013). A well-sited town/city sits in the middle of its BEST
# land, and the near ring the frame shows is the part worked HARDEST (site selection + the von
# Thünen intensity gradient; the labor-limited fallow lives at the FAR margins, not hugging the
# town). So the flat, waterable near-ring ground must read as PACKED cultivation, not bare scrub.
# This measures the fraction of flat, uncommitted near-ring ground that is CULTIVATED (paddy +
# vegetable fields, dry hem/hatake plots, gardens) - the mirror of town_margins_clothed above, but
# counting only CROPLAND, not "any cover". The denominator EXCLUDES ground already committed to a
# non-arable use (the settlement + its urban halo, roads/streets, water, the hill, the wet marsh
# toe, graves/cremation/ossuary, pasture/coppice, groves) and, on a walled city, everything INSIDE
# the wall (urban, not near-ring farmland). What remains is the flat ground that COULD be cropped;
# bare scrub (commons) on it counts AGAINST the fraction, so the tier threshold is < 1.0 to leave
# room for the genuine fallow/margin scrub. Tunable per map via meta(near_ring_density=...): "dense"
# (well-sited default) demands a packed ring, "thin" (a dry rain-shadow / marginal locale) permits a
# scrubbier one - the calibrated-liberty range (settlements.md "Near-ring farmland density"). WHY the
# thresholds: today's undensified Hirameki sits at ~33% and Tango's outside-wall band at ~7%, both
# declared dense - so the dense floor is set well above them to have teeth. Grounded in budgets.md
# "Rice and arable-land math" (the ~4% figure is a domain-wide average, the wrong number for the
# immediate hinterland). Town + city only; villages/hamlets keep the satoyama scrub-interleave rule.


def _seg_0438_000__NRD_THRESHOLD(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.000 (NRD_THRESHOLD) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        NRD_THRESHOLD = {
            "dense": {"town": 0.28, "city": 0.12},
            "medium": {"town": 0.18, "city": 0.08},
            "thin": {"town": 0.12, "city": 0.05},
        }
    return _kept(locals(), ('NRD_THRESHOLD',))


def _seg_0438_001__nrd_tier(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.001 (nrd_tier) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nrd_tier = meta.get("near_ring_density", "dense")
    return _kept(locals(), ('nrd_tier',))


def _seg_0438_002__nr_thr(*, NRD_THRESHOLD: Any = _UNBOUND, nrd_tier: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.002 (nr_thr) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_thr = NRD_THRESHOLD.get(nrd_tier, NRD_THRESHOLD["dense"])[scale]
    return _kept(locals(), ('nr_thr',))


def _seg_0438_003__nr_halo(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.003 (nr_halo) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_halo = 30.0 / (meta.get("ftpx") or 1)
    return _kept(locals(), ('nr_halo',))


# cultivated cover: paddy + vegetable fields, the chrysanthemum flower field, dry plots, gardens


def _seg_0438_004__f_(*, M: Any = _UNBOUND, f_: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.004 (f_, nr_cult) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_cult = [f_["outline"] for f_ in M.get("fields", [])] + [f_["outline"] for f_ in M.get("flower_fields", [])]
    return _kept(locals(), ('f_', 'nr_cult'))


def _seg_0438_005__k_(*, M: Any = _UNBOUND, k_: Any = _UNBOUND, nr_cult: Any = _UNBOUND, o_: Any = _UNBOUND, p_: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.005 (k_, nr_cult, o_, p_) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        for k_ in ("dry_plots", "gardens"):
            for o_ in M.get(k_, []) or []:
                p_ = o_.get("poly") if isinstance(o_, dict) else o_
                if p_ is not None and len(p_) >= 3:
                    nr_cult.append(p_)
    return _kept(locals(), ('k_', 'nr_cult', 'o_', 'p_'))


# committed non-arable cover -> a cell here is NOT eligible near-ring ground (excluded from the
# denominator entirely, so a graveyard / pasture / coppice is neither cultivated nor counted as bare)


def _seg_0438_006__nr_skip(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.006 (nr_skip) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_skip = []  # type: ignore[var-annotated]
    return _kept(locals(), ('nr_skip',))


def _seg_0438_007__k__1(*, M: Any = _UNBOUND, k_: Any = _UNBOUND, nr_skip: Any = _UNBOUND, o_: Any = _UNBOUND, p_: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.007 (k_, nr_skip, o_, p_) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        for k_ in ("marshes", "pastures", "forest_patches", "cemeteries", "cremation_grounds", "ossuaries", "village_groves", "groves"):
            for o_ in M.get(k_, []) or []:
                p_ = o_.get("poly") if isinstance(o_, dict) else o_
                if p_ is not None and len(p_) >= 3:
                    nr_skip.append(p_)
    return _kept(locals(), ('k_', 'nr_skip', 'o_', 'p_'))


def _seg_0438_008__nr_boxes(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.008 (nr_boxes) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_boxes = []  # type: ignore[var-annotated]
    return _kept(locals(), ('nr_boxes',))


def _seg_0438_009__nr_boxes_1(*, M: Any = _UNBOUND, nr_boxes: Any = _UNBOUND, nr_halo: Any = _UNBOUND, o_: Any = _UNBOUND, scale: Any = _UNBOUND, v_: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.009 (nr_boxes, o_, v_) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        for v_ in M.values():
            if isinstance(v_, list) and v_ and isinstance(v_[0], dict) and "x" in v_[0] and "w" in v_[0] and "h" in v_[0]:
                for o_ in v_:
                    nr_boxes.append((o_["x"] - o_["w"] / 2 - nr_halo, o_["y"] - o_["h"] / 2 - nr_halo, o_["x"] + o_["w"] / 2 + nr_halo, o_["y"] + o_["h"] / 2 + nr_halo))
    return _kept(locals(), ('nr_boxes', 'o_', 'v_'))


def _seg_0438_010__nr_lines(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.010 (nr_lines) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_lines = []  # type: ignore[var-annotated]
    return _kept(locals(), ('nr_lines',))
