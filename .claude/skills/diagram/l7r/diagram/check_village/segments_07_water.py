"""Gate segments (water) - bodies verbatim from check_village.py (feature 024 package split; registry order preserved)."""

import math
from typing import Any

from l7r.diagram.settlement import moat_current_at, sat_overlap

from .common_01_geometry import Poly, Pt, _struct_rect, point_in_poly, poly_dist, rect_corners, seg_dist, seg_intersect, seg_to_rect_dist, segments_cross, unit_dir
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


def _seg_0438_011__nr_lines_1(*, nr_lines: Any = _UNBOUND, road: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.011 (nr_lines) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and road:
        nr_lines.append((road, 60.0))
    return _kept(locals(), ('nr_lines',))


def _seg_0438_012__nr_lines_2(*, M: Any = _UNBOUND, nr_lines: Any = _UNBOUND, scale: Any = _UNBOUND, st_: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.012 (nr_lines, st_) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_lines += [(st_["pts"], st_["w"] / 2 + 40) for st_ in M.get("town_streets", [])]
    return _kept(locals(), ('nr_lines', 'st_'))


def _seg_0438_013__ln_(*, M: Any = _UNBOUND, ln_: Any = _UNBOUND, nr_lines: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.013 (ln_, nr_lines) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_lines += [(ln_["pts"], 30.0) for ln_ in M.get("lanes", [])]
    return _kept(locals(), ('ln_', 'nr_lines'))


def _seg_0438_014__c2_(*, M: Any = _UNBOUND, c2_: Any = _UNBOUND, d_: Any = _UNBOUND, nr_lines: Any = _UNBOUND, s_: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.014 (c2_, d_, nr_lines, s_) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_lines += [(s_["poly"], 30.0) for s_ in M.get("streams", [])] + [(c2_["poly"], 24.0) for c2_ in M.get("channels", [])] + [(d_["poly"], 20.0) for d_ in M.get("field_ditches", [])]
    return _kept(locals(), ('c2_', 'd_', 'nr_lines', 's_'))


def _seg_0438_015__nr_moat(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.015 (nr_moat) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_moat = M.get("moat")
    return _kept(locals(), ('nr_moat',))


def _seg_0438_016__nr_lines_3(*, M: Any = _UNBOUND, nr_lines: Any = _UNBOUND, nr_moat: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.016 (nr_lines) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and nr_moat:
        nr_lines.append((nr_moat, M.get("moat_width", 22) / 2 + 8))
    return _kept(locals(), ('nr_lines',))


def _seg_0438_017__nr_wall(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.017 (nr_wall) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_wall = M.get("wall")
    return _kept(locals(), ('nr_wall',))


def _seg_0438_018__nr_hill(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.018 (nr_hill) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_hill = M.get("hill")
    return _kept(locals(), ('nr_hill',))


def _seg_0438_019__nr_pond(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.019 (nr_pond) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_pond = M.get("pond")
    return _kept(locals(), ('nr_pond',))


# NEAR-RING BAND CAP (2026-07-23): on a WALLED CITY the near ring is the ground within ~800 real ft
# of the rampart (a few minutes' walk out the gates - wide enough to take in the moat-fed fans' plot mass, since the first ~500 ft is structurally moat + farmstead rings + gate suburbs) - NOT
# everything the frame happens to show. The thresholds were calibrated on a tight crop whose visible
# extramural WAS that band ("the countryside proper runs off-frame" above); when the frame widened to
# show the comb deltas as countryside (GM 2026-07-23, Tango), an uncapped sampler silently redefined
# "near ring" as "all visible countryside" and diluted the fraction with ground the check was never
# meant to judge. Capping by real distance keeps the check meaning the same at ANY frame size.
# Towns (no wall) keep their tight frames; unchanged there.


def _seg_0438_020__nr_band(*, URBAN: Any = _UNBOUND, meta: Any = _UNBOUND, nr_wall: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.020 (nr_band) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_band = (800.0 / (meta.get("ftpx") or 1)) if (URBAN and nr_wall is not None and len(nr_wall) >= 3) else None
    return _kept(locals(), ('nr_band',))


# SAMPLING WINDOW: for a walled city the band is sampled in CANVAS space (the wall bbox expanded
# by the band), NOT the view - the manifest records full-canvas geometry, so the near ring exists
# whether or not the crop shows it, and the metric must not shift when the frame is tightened
# (caught 2026-07-23: the aggressive Nagahara crop clipped band cells and dropped the fraction
# below the floor with not one field changed). Towns keep the view window (no wall, no band).


def _seg_0438_021__SX0(
    *,
    EX0: Any = _UNBOUND,
    EX1: Any = _UNBOUND,
    EY0: Any = _UNBOUND,
    EY1: Any = _UNBOUND,
    Hd: Any = _UNBOUND,
    Wd: Any = _UNBOUND,
    _wxs: Any = _UNBOUND,
    _wys: Any = _UNBOUND,
    nr_band: Any = _UNBOUND,
    nr_wall: Any = _UNBOUND,
    p_: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0438.021 (SX0, SX1, SY0, SY1) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        if nr_band is not None and nr_wall is not None:
            _wxs = [p_[0] for p_ in nr_wall]
            _wys = [p_[1] for p_ in nr_wall]
            SX0, SY0 = max(0.0, min(_wxs) - nr_band - 25), max(0.0, min(_wys) - nr_band - 25)
            SX1, SY1 = min(float(Wd), max(_wxs) + nr_band + 25), min(float(Hd), max(_wys) + nr_band + 25)
        else:
            SX0, SY0, SX1, SY1 = EX0, EY0, EX1, EY1
    return _kept(locals(), ('SX0', 'SX1', 'SY0', 'SY1', '_wxs', '_wys', 'p_'))


def _seg_0438_022__nr_cultc(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.022 (nr_cultc, nr_elig) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_elig = nr_cultc = 0
    return _kept(locals(), ('nr_cultc', 'nr_elig'))


def _seg_0438_023__gy(*, SY0: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.023 (gy) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        gy = SY0 + 12.5
    return _kept(locals(), ('gy',))


def _seg_0438_024__bx0(
    *,
    SX0: Any = _UNBOUND,
    SX1: Any = _UNBOUND,
    SY1: Any = _UNBOUND,
    bx0: Any = _UNBOUND,
    bx1: Any = _UNBOUND,
    by0: Any = _UNBOUND,
    by1: Any = _UNBOUND,
    committed: Any = _UNBOUND,
    gx: Any = _UNBOUND,
    gy: Any = _UNBOUND,
    hw_: Any = _UNBOUND,
    i_: Any = _UNBOUND,
    nr_band: Any = _UNBOUND,
    nr_boxes: Any = _UNBOUND,
    nr_cult: Any = _UNBOUND,
    nr_cultc: Any = _UNBOUND,
    nr_elig: Any = _UNBOUND,
    nr_hill: Any = _UNBOUND,
    nr_lines: Any = _UNBOUND,
    nr_pond: Any = _UNBOUND,
    nr_skip: Any = _UNBOUND,
    nr_wall: Any = _UNBOUND,
    p_: Any = _UNBOUND,
    pl_: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0438.024 (bx0, bx1, by0, by1) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        while gy < SY1:
            gx = SX0 + 12.5
            while gx < SX1:
                # a cell inside the rampart of a walled town/city is URBAN FLOOR, not near-ring farmland
                # (same reading as town_margins_clothed's inside-the-rampart exemption) - the near ring is
                # the EXTRAMURAL flat ground; the intramural chrysanthemum field / open squares are the town
                committed = (
                    (nr_wall is not None and len(nr_wall) >= 3 and point_in_poly(gx, gy, nr_wall))
                    or (nr_band is not None and nr_wall is not None and poly_dist(gx, gy, nr_wall) > nr_band)  # beyond the near ring: countryside, not judged here
                    or (nr_hill is not None and in_ellipse(gx, gy, nr_hill, 1.45))
                    or (nr_pond is not None and in_ellipse(gx, gy, [nr_pond[0], nr_pond[1], nr_pond[2] + 20, nr_pond[3] + 20]))
                    or any(bx0 <= gx <= bx1 and by0 <= gy <= by1 for bx0, by0, bx1, by1 in nr_boxes)
                    or any(any(seg_dist(gx, gy, pl_[i_], pl_[i_ + 1]) < hw_ for i_ in range(len(pl_) - 1)) for pl_, hw_ in nr_lines)
                    or any(point_in_poly(gx, gy, p_) for p_ in nr_skip)
                )
                if committed:
                    gx += 25
                    continue
                nr_elig += 1
                if any(point_in_poly(gx, gy, p_) for p_ in nr_cult):
                    nr_cultc += 1
                gx += 25
            gy += 25
    return _kept(locals(), ('bx0', 'bx1', 'by0', 'by1', 'committed', 'gx', 'gy', 'hw_', 'i_', 'nr_cultc', 'nr_elig', 'p_', 'pl_'))


def _seg_0438_025__nr_frac(*, nr_cultc: Any = _UNBOUND, nr_elig: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.025 (nr_frac) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_frac = nr_cultc / nr_elig if nr_elig else 1.0
    return _kept(locals(), ('nr_frac',))


def _seg_0438_026__near_ring_cultivated_fraction(*, check: Any = _UNBOUND, nr_frac: Any = _UNBOUND, nr_thr: Any = _UNBOUND, nrd_tier: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.026 (near_ring_cultivated_fraction) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        check(
            "near_ring_cultivated_fraction",
            nr_frac >= nr_thr,
            f"only {nr_frac:.0%} of the flat near-ring ground is cultivated (below the {nr_thr:.0%} floor for near_ring_density='{nrd_tier}') - "
            "a well-sited town/city sits in packed farmland: fill the flat clear ground with s.near_ring_cropland(...) "
            "(dry/garden cropland needs no water source) and keep scrub commons to the frame margins; or, for a genuinely "
            "dry/marginal locale, declare meta(near_ring_density='medium'|'thin')",
        )
    return _kept(locals(), ())


# NEAR-RING PADDY DOMINANCE (feature 014). Feature 013 packed the near ring but filled it with
# DRY grain (dry cropland needs no plumbed water, the cheap fill) - historically backwards: a town
# sits in the fertile basin BECAUSE of the wet rice, so its flat waterable near ring is PADDY-
# dominant. Dry grain is the SECONDARY use on the drier/higher margins; vegetable/market gardens
# (crop=="garden") hug the town. This reuses the exact 25px near-ring band + `committed` mask above
# and tallies PADDY-covered cells vs DRY-GRAIN-covered cells (dry_plots whose crop != garden;
# gardens are the legitimate near-town dry use, not the thing demoted), requiring paddy to DOMINATE
# - scaled by tier so a dialed-down map is paddy-LED but sparser, never dry-dominant. REJECTED (per
# Constitution XII, recorded so it is never reinvented): the dry-grain-dominant near ring 013 shipped;
# the flat waterable valley floor of a wet-rice county seat is paddy, not dryland grain. Grounded in
# settlements.md "Near-ring farmland density" + budgets.md (the ~1/3-paddy figure is a DOMAIN-wide
# average over hills+margins - the near ring is the most waterable flat ground, so paddy-heavy).
# WHY the ratios: a dense well-sited basin reads clearly paddy-led (paddy >= 1.2x dry-grain); a thin
# grazing/relay locale need only keep paddy at least TYING dry-grain (paddy >= dry-grain), so the
# honest lower-tier answer (a thinner ring where little water reaches) is not forced to dense.
# NOTE: what counts as dry-grain EXCLUDES a paddy comb's own dry hem (below), so a moated city whose
# extramural is an open GLACIS - moat-fed paddy + a thin garden fringe, the rest kept clear for defense
# (Tango) - passes as long as its paddy out-covers the FREE-STANDING dry grain (of which a glacis has
# little). That is the honest read: the immediate glacis is not packed dry farmland.


def _seg_0438_027__NRPD_RATIO(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.027 (NRPD_RATIO) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        NRPD_RATIO = {"dense": 1.2, "medium": 1.1, "thin": 1.0}
    return _kept(locals(), ('NRPD_RATIO',))


def _seg_0438_028__nrpd_ratio(*, NRPD_RATIO: Any = _UNBOUND, nrd_tier: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.028 (nrpd_ratio) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nrpd_ratio = NRPD_RATIO.get(nrd_tier, NRPD_RATIO["dense"])
    return _kept(locals(), ('nrpd_ratio',))


def _seg_0438_029__f__1(*, M: Any = _UNBOUND, f_: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.029 (f_, nrp_paddy) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nrp_paddy = [f_["outline"] for f_ in M.get("fields", []) if f_.get("kind") == "paddy"]
    return _kept(locals(), ('f_', 'nrp_paddy'))


# a paddy comb's own DRY HEM (the barley/soy upslope margin of the flooded field) is part of the
# paddy system, not a competing dry-grain crop - exclude any dry plot sitting within OR HUGGING a
# paddy field's envelope, so only FREE-STANDING dryland grain (the 013 blanket) counts against
# paddy dominance. The hem quilt RINGS the envelope - at the head/flanks it sits OUTSIDE the
# recorded bbox by up to the dry_band (~88px city / ~132px village), so the test expands the bbox
# by that band; a bare in-bbox test miscounted every comb's head hem as free-standing grain
# (caught 2026-07-23 when the near ring became combs-only and the "dry grain" was all hems).


def _seg_0438_030___HEM(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.030 (_HEM) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        _HEM = 135.0
    return _kept(locals(), ('_HEM',))


def _seg_0438_031__f__2(*, M: Any = _UNBOUND, f_: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.031 (f_, nrp_pbbox) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nrp_pbbox = [f_["bbox"] for f_ in M.get("fields", []) if f_.get("kind") == "paddy" and f_.get("bbox")]
    return _kept(locals(), ('f_', 'nrp_pbbox'))


def _seg_0438_032__nrp_drygrain(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.032 (nrp_drygrain) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nrp_drygrain = []  # type: ignore[var-annotated]
    return _kept(locals(), ('nrp_drygrain',))


def _seg_0438_033__bx0_(
    *,
    M: Any = _UNBOUND,
    _HEM: Any = _UNBOUND,
    bx0_: Any = _UNBOUND,
    bx1_: Any = _UNBOUND,
    by0_: Any = _UNBOUND,
    by1_: Any = _UNBOUND,
    dcx_: Any = _UNBOUND,
    dcy_: Any = _UNBOUND,
    nrp_drygrain: Any = _UNBOUND,
    nrp_pbbox: Any = _UNBOUND,
    o_: Any = _UNBOUND,
    p_: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    v_: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0438.033 (bx0_, bx1_, by0_, by1_) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        for o_ in M.get("dry_plots", []) or []:
            p_ = o_.get("poly") if isinstance(o_, dict) else o_
            if p_ is not None and len(p_) >= 3 and (not isinstance(o_, dict) or o_.get("crop") != "garden"):
                dcx_ = sum(v_[0] for v_ in p_) / len(p_)
                dcy_ = sum(v_[1] for v_ in p_) / len(p_)
                if not any(bx0_ - _HEM <= dcx_ <= bx1_ + _HEM and by0_ - _HEM <= dcy_ <= by1_ + _HEM for bx0_, by0_, bx1_, by1_ in nrp_pbbox):
                    nrp_drygrain.append(p_)
    return _kept(locals(), ('bx0_', 'bx1_', 'by0_', 'by1_', 'dcx_', 'dcy_', 'nrp_drygrain', 'o_', 'p_', 'v_'))


def _seg_0438_034__nrp_dc(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.034 (nrp_dc, nrp_pc) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nrp_pc = nrp_dc = 0
    return _kept(locals(), ('nrp_dc', 'nrp_pc'))


def _seg_0438_035__gy_1(*, SY0: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.035 (gy) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        gy = SY0 + 12.5  # the same canvas-space band window as the fraction sampler above
    return _kept(locals(), ('gy',))


def _seg_0438_036__bx0_1(
    *,
    SX0: Any = _UNBOUND,
    SX1: Any = _UNBOUND,
    SY1: Any = _UNBOUND,
    bx0: Any = _UNBOUND,
    bx1: Any = _UNBOUND,
    by0: Any = _UNBOUND,
    by1: Any = _UNBOUND,
    committed: Any = _UNBOUND,
    gx: Any = _UNBOUND,
    gy: Any = _UNBOUND,
    hw_: Any = _UNBOUND,
    i_: Any = _UNBOUND,
    nr_band: Any = _UNBOUND,
    nr_boxes: Any = _UNBOUND,
    nr_hill: Any = _UNBOUND,
    nr_lines: Any = _UNBOUND,
    nr_pond: Any = _UNBOUND,
    nr_skip: Any = _UNBOUND,
    nr_wall: Any = _UNBOUND,
    nrp_dc: Any = _UNBOUND,
    nrp_drygrain: Any = _UNBOUND,
    nrp_paddy: Any = _UNBOUND,
    nrp_pc: Any = _UNBOUND,
    p_: Any = _UNBOUND,
    pl_: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0438.036 (bx0, bx1, by0, by1) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        while gy < SY1:
            gx = SX0 + 12.5
            while gx < SX1:
                committed = (
                    (nr_wall is not None and len(nr_wall) >= 3 and point_in_poly(gx, gy, nr_wall))
                    or (nr_band is not None and nr_wall is not None and poly_dist(gx, gy, nr_wall) > nr_band)  # beyond the near ring: countryside (same cap as the fraction sampler above)
                    or (nr_hill is not None and in_ellipse(gx, gy, nr_hill, 1.45))
                    or (nr_pond is not None and in_ellipse(gx, gy, [nr_pond[0], nr_pond[1], nr_pond[2] + 20, nr_pond[3] + 20]))
                    or any(bx0 <= gx <= bx1 and by0 <= gy <= by1 for bx0, by0, bx1, by1 in nr_boxes)
                    or any(any(seg_dist(gx, gy, pl_[i_], pl_[i_ + 1]) < hw_ for i_ in range(len(pl_) - 1)) for pl_, hw_ in nr_lines)
                    or any(point_in_poly(gx, gy, p_) for p_ in nr_skip)
                )
                if not committed and any(point_in_poly(gx, gy, p_) for p_ in nrp_paddy):
                    nrp_pc += 1
                elif any(point_in_poly(gx, gy, p_) for p_ in nrp_drygrain):
                    nrp_dc += 1
                gx += 25
            gy += 25
    return _kept(locals(), ('bx0', 'bx1', 'by0', 'by1', 'committed', 'gx', 'gy', 'hw_', 'i_', 'nrp_dc', 'nrp_pc', 'p_', 'pl_'))


def _seg_0438_037__near_ring_paddy_dominant(
    *, check: Any = _UNBOUND, nrd_tier: Any = _UNBOUND, nrp_dc: Any = _UNBOUND, nrp_pc: Any = _UNBOUND, nrpd_ratio: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0438.037 (near_ring_paddy_dominant) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        check(
            "near_ring_paddy_dominant",
            nrp_pc >= nrpd_ratio * nrp_dc,
            f"near-ring paddy does not dominate: {nrp_pc} paddy cells vs {nrp_dc} dry-grain cells "
            f"(need paddy >= {nrpd_ratio:g}x dry-grain for near_ring_density='{nrd_tier}') - a wet-rice county seat's "
            "flat near ring is PADDY, not dryland grain: add near-ring paddy where water reaches (s.near_ring_paddy(...), "
            "or enlarge the combs), demote the dry grain to the drier/higher margins + a garden band by the town, or - "
            "where the near ring genuinely lacks water - draw it at a lower near_ring_density tier",
        )
    return _kept(locals(), ())


# NO CANOPY STANDS OVER OPEN WATER (GM audit 2026-07): a village-grove clump drawn across a
# stream / channel / moat reads as trees growing in the current. The fengshui-pond rule
# (trees_clear_of_fengshui_ponds) covered only ponds; this closes the running-water half.
# village_grove now skips watercourse corridors at draw time; this is the ratchet.


def _seg_0439__wet_canopy() -> dict[str, Any]:
    """Gate segment 439 (wet_canopy) - body verbatim from the legacy gate() (feature 022)."""
    wet_canopy = []  # type: ignore[var-annotated]
    return _kept(locals(), ('wet_canopy',))


def _seg_0440__canopy_lines(*, M: Any = _UNBOUND, st_c: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 440 (canopy_lines, st_c) - body verbatim from the legacy gate() (feature 022)."""
    canopy_lines = [(st_c["poly"], st_c.get("w", 9) / 2) for st_c in M.get("streams", [])]
    return _kept(locals(), ('canopy_lines', 'st_c'))


def _seg_0441__canopy_lines_1(*, M: Any = _UNBOUND, canopy_lines: Any = _UNBOUND, cc_c: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 441 (canopy_lines, cc_c) - body verbatim from the legacy gate() (feature 022)."""
    canopy_lines += [(cc_c["poly"], cc_c.get("w", 2.5) / 2) for cc_c in M.get("channels", [])]
    return _kept(locals(), ('canopy_lines', 'cc_c'))


def _seg_0442__canopy_lines_2(*, M: Any = _UNBOUND, canopy_lines: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 442 (canopy_lines) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("moat"):
        canopy_lines.append((M["moat"], M.get("moat_width", 22) / 2))
    return _kept(locals(), ('canopy_lines',))


def _seg_0443__cl_c(
    *, M: Any = _UNBOUND, canopy_lines: Any = _UNBOUND, cl_c: Any = _UNBOUND, k: Any = _UNBOUND, vg_c: Any = _UNBOUND, wet_canopy: Any = _UNBOUND, whw: Any = _UNBOUND, wl: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 443 (cl_c, k, vg_c, wet_canopy) - body verbatim from the legacy gate() (feature 022)."""
    for vg_c in M.get("village_groves", []):
        for cl_c in vg_c.get("clumps", []):
            if any(min(seg_dist(cl_c[0], cl_c[1], wl[k], wl[k + 1]) for k in range(len(wl) - 1)) < whw + 6 for wl, whw in canopy_lines):
                wet_canopy.append((round(cl_c[0]), round(cl_c[1])))
    return _kept(locals(), ('cl_c', 'k', 'vg_c', 'wet_canopy', 'whw', 'wl'))


def _seg_0444__canopy_clear_of_watercourses(*, check: Any = _UNBOUND, wet_canopy: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 444 (canopy_clear_of_watercourses) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "canopy_clear_of_watercourses",
        not wet_canopy,
        f"grove canopy clump(s) stand over open water at {sorted(set(wet_canopy))[:4]} - trees do not grow in a stream, channel, or moat; keep the belt polys (and the clump filter) clear of every watercourse",
    )
    return _kept(locals(), ())


def _seg_0445__watercourse_ends_reach_water(*, check: Any = _UNBOUND, dry_drains: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 445 (watercourse_ends_reach_water) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "watercourse_ends_reach_water",
        not dry_drains,
        f"canal/collector end(s) dangle in bare ground at {sorted(set(dry_drains))[:4]} - an on-map main or drain end outside the crop must JOIN a watercourse (a culvert, the stream, another ditch, the moat) or run off the frame; water never just stops",
    )
    return _kept(locals(), ())


def _seg_0446__channels_join_streams_at_confluence(*, check: Any = _UNBOUND, dry_mouths: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 446 (channels_join_streams_at_confluence) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "channels_join_streams_at_confluence",
        not dry_mouths,
        f"channel mouth(s) declared frm/to={{stream}} stop short of the bed at {sorted(set(dry_mouths))[:4]} - "
        f"an intake or drain culvert joins its stream at a CONFLUENCE (the mouth reaches into the water, like a "
        f"road junction), never dying in the grass beside the bank; snap the recorded polyline to the stream centerline",
    )
    return _kept(locals(), ())


# no field overlaps the town wall: a field may ABUT the wall but must stay on one
# side of it (the chrysanthemum field inside the walls touches but never crosses)


def _seg_0447__wall_1(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 447 (wall) - body verbatim from the legacy gate() (feature 022)."""
    wall = M.get("wall")
    return _kept(locals(), ('wall',))


def _seg_0448__fields_clear_of_wall(
    *,
    M: Any = _UNBOUND,
    bad_fw: Any = _UNBOUND,
    check: Any = _UNBOUND,
    e: Any = _UNBOUND,
    f: Any = _UNBOUND,
    ff: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    i: Any = _UNBOUND,
    k: Any = _UNBOUND,
    n: Any = _UNBOUND,
    nm: Any = _UNBOUND,
    ol: Any = _UNBOUND,
    wall: Any = _UNBOUND,
    walled_fields: Any = _UNBOUND,
    wx: Any = _UNBOUND,
    wy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 448 (fields_clear_of_wall) - body verbatim from the legacy gate() (feature 022)."""
    if wall:
        walled_fields = [(f["name"], f["outline"]) for f in fields] + [(f"flower[{i}]", ff["outline"]) for i, ff in enumerate(M.get("flower_fields", []))]
        bad_fw = []
        for nm, ol in walled_fields:
            n = len(ol)
            if any(segments_cross(wall[k], wall[k + 1], ol[e], ol[(e + 1) % n]) for k in range(len(wall) - 1) for e in range(n)) or any(point_in_poly(wx, wy, ol) for wx, wy in wall):
                bad_fw.append(nm)
        check("fields_clear_of_wall", not bad_fw, f"field(s) overlap the wall: {sorted(set(bad_fw))}")
    return _kept(locals(), ('bad_fw', 'e', 'f', 'ff', 'i', 'k', 'n', 'nm', 'ol', 'walled_fields', 'wx', 'wy'))


# EVERY fully-on-map paddy field must SHOW a source of water: a channel feeding it, or
# the field directly abutting a stream or pond (its bank at the water). A field merely
# NEAR water without a visible connection does not count. Fields that run off the map
# edge are exempt (their water source may be off-map too).


def _seg_0449__channels(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 449 (channels) - body verbatim from the legacy gate() (feature 022)."""
    channels = M.get("channels", [])
    return _kept(locals(), ('channels',))


def _seg_0450__streams_m(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 450 (streams_m) - body verbatim from the legacy gate() (feature 022)."""
    streams_m = M.get("streams", [])
    return _kept(locals(), ('streams_m',))


def _seg_0451__watered(
    *,
    c: Any = _UNBOUND,
    channels: Any = _UNBOUND,
    k: Any = _UNBOUND,
    ol: Any = _UNBOUND,
    pond: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    sp: Any = _UNBOUND,
    st: Any = _UNBOUND,
    streams_m: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 451 (watered) - body verbatim from the legacy gate() (feature 022)."""

    def watered(ol: Poly) -> bool:
        if any(point_in_poly(c["poly"][-1][0], c["poly"][-1][1], ol) for c in channels):
            return True  # a channel ends inside it
        if any(
            seg_dist(px, py, sp[k], sp[k + 1]) < 18  # the field bank abuts a stream
            for st in streams_m
            for sp in [st["poly"]]
            for px, py in ol
            for k in range(len(sp) - 1)
        ):
            return True
        return bool(pond and any(in_ellipse(px, py, pond, 1.10) for px, py in ol))  # ...or the pond

    return _kept(locals(), ('watered',))


def _seg_0452__dry(*, f: Any = _UNBOUND, fields: Any = _UNBOUND, runs_off_edge: Any = _UNBOUND, watered: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 452 (dry, f) - body verbatim from the legacy gate() (feature 022)."""
    dry = [f["name"] for f in fields if f["kind"] == "paddy" and not runs_off_edge(f["outline"]) and not watered(f["outline"])]
    return _kept(locals(), ('dry', 'f'))


def _seg_0453__fields_show_water_source(*, check: Any = _UNBOUND, dry: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 453 (fields_show_water_source) - body verbatim from the legacy gate() (feature 022)."""
    check("fields_show_water_source", not dry, f"on-map field(s) with no visible water source (channel or abutting stream/pond): {sorted(set(dry))}")
    return _kept(locals(), ())


# water flows DOWNHILL. If the map declares its slope (meta(downhill=<dir>)), every
# channel must run with it: the source (tap on the stream/pond, poly[0]) sits uphill of
# where it feeds the field (poly[-1]). A channel angled the other way would carry the
# stream's water away from the field, not into it. <dir> is a cardinal name or [dx,dy]
# vector in map coords (+y = south). Maps without the tag are exempt (slope unknown).
# ONE DIRECTION MODEL, NOT THREE (GM 2026-07-25). These two were gated on the LEGACY
# meta(downhill) - a cardinal name or vector - which only 2 of 17 maps ever declared, so 15 maps
# (both provincial cities among them) skipped them entirely behind a green gate: the same
# silent-skip that hid the drainage-slope rules. The fall now comes from `downhill` where a map
# declares it, else meta(down_deg), and per-channel from the TARGET FIELD's own fall when it has
# one - a settlement ringed by farmland drains several ways at once, so the field a channel feeds
# is the right authority for whether that channel runs downhill into it.


def _seg_0454__downhill(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 454 (downhill) - body verbatim from the legacy gate() (feature 022)."""
    downhill = meta.get("downhill")
    return _kept(locals(), ('downhill',))


def _seg_0455___dh_dd(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 455 (_dh_dd) - body verbatim from the legacy gate() (feature 022)."""
    _dh_dd = meta.get("down_deg")
    return _kept(locals(), ('_dh_dd',))


def _seg_0456___dh_fields(*, M: Any = _UNBOUND, f: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 456 (_dh_fields, f) - body verbatim from the legacy gate() (feature 022)."""
    _dh_fields = {f.get("name"): f["down_deg"] for f in M.get("fields", []) if f.get("down_deg") is not None}
    return _kept(locals(), ('_dh_fields', 'f'))


def _seg_0457___dh_vec() -> dict[str, Any]:
    """Gate segment 457 (_dh_vec) - body verbatim from the legacy gate() (feature 022)."""

    def _dh_vec(deg: float) -> tuple[float, float]:
        return (math.cos(math.radians(deg)), math.sin(math.radians(deg)))

    return _kept(locals(), ('_dh_vec',))


def _seg_0458___dh_map(*, _dh_dd: Any = _UNBOUND, _dh_vec: Any = _UNBOUND, downhill: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 458 (_dh_map) - body verbatim from the legacy gate() (feature 022)."""
    _dh_map = unit_dir(downhill) if downhill else (_dh_vec(_dh_dd) if _dh_dd is not None else None)
    return _kept(locals(), ('_dh_map',))


def _seg_0459__downhill_direction_valid(*, check: Any = _UNBOUND, downhill: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 459 (downhill_direction_valid) - body verbatim from the legacy gate() (feature 022)."""
    if downhill:
        check("downhill_direction_valid", bool(unit_dir(downhill)), f"meta(downhill={downhill!r}) is not a cardinal name or [dx,dy] vector")
    return _kept(locals(), ())


def _seg_0460__channels_flow_downhill(
    *,
    L: Any = _UNBOUND,
    _cdd: Any = _UNBOUND,
    _cto: Any = _UNBOUND,
    _dh_fields: Any = _UNBOUND,
    _dh_map: Any = _UNBOUND,
    _dh_vec: Any = _UNBOUND,
    c: Any = _UNBOUND,
    channels: Any = _UNBOUND,
    check: Any = _UNBOUND,
    dvec: Any = _UNBOUND,
    ex: Any = _UNBOUND,
    ey: Any = _UNBOUND,
    sx: Any = _UNBOUND,
    sy: Any = _UNBOUND,
    uphill: Any = _UNBOUND,
    vx: Any = _UNBOUND,
    vy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 460 (channels_flow_downhill) - body verbatim from the legacy gate() (feature 022)."""
    if (_dh_map or _dh_fields) and channels:
        uphill = []
        for c in channels:
            _cto = (c.get("to") or {}).get("name")
            _cdd = _dh_fields.get(_cto) if _cto else None
            dvec = _dh_vec(_cdd) if _cdd is not None else _dh_map
            if dvec is None:
                continue  # neither this channel's field nor the map declares a fall - nothing to judge it by
            (sx, sy), (ex, ey) = c["poly"][0], c["poly"][-1]
            vx, vy = ex - sx, ey - sy
            L = math.hypot(vx, vy)
            if L > 0 and (vx * dvec[0] + vy * dvec[1]) < 0.2 * L:  # not clearly running downhill
                uphill.append(c["to"].get("name", "?"))
        check("channels_flow_downhill", not uphill, f"channel(s) not running downhill (source must be uphill of the field it feeds): {sorted(set(uphill))}")
    return _kept(locals(), ('L', '_cdd', '_cto', 'c', 'dvec', 'ex', 'ey', 'sx', 'sy', 'uphill', 'vx', 'vy'))


# the same flow logic applies to a city MOAT: the moat is fed by a stream entering from one
# side (the source), so the moat water heads that-source-to-the-far-side direction (Tango's
# feeder enters from the north, so the moat water heads SOUTH). A moat-fed irrigation channel
# must run WITH that current - its field-end downstream of its moat-tap. A channel whose field
# is UPSTREAM of the tap reads as water flowing from the field INTO the moat (backwards).


def _seg_0461__moat_ring(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 461 (moat_ring) - body verbatim from the legacy gate() (feature 022)."""
    moat_ring: Any = M.get("moat")
    return _kept(locals(), ('moat_ring',))


def _seg_0462__c_5(*, c: Any = _UNBOUND, channels: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 462 (c, mfed) - body verbatim from the legacy gate() (feature 022)."""
    mfed = [c for c in channels if (c.get("frm") or {}).get("kind") == "moat"]
    return _kept(locals(), ('c', 'mfed'))


def _seg_0463__moat_channels_flow_with_current(
    *,
    M: Any = _UNBOUND,
    _mdx: Any = _UNBOUND,
    _mdy: Any = _UNBOUND,
    _mfl: Any = _UNBOUND,
    _mi: Any = _UNBOUND,
    _mo: Any = _UNBOUND,
    against: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    dx: Any = _UNBOUND,
    dy: Any = _UNBOUND,
    e: Any = _UNBOUND,
    ends: Any = _UNBOUND,
    ends_on_moat: Any = _UNBOUND,
    entry: Any = _UNBOUND,
    ex: Any = _UNBOUND,
    ey: Any = _UNBOUND,
    feeder: Any = _UNBOUND,
    flow: Any = _UNBOUND,
    mfed: Any = _UNBOUND,
    moat_ring: Any = _UNBOUND,
    origin: Any = _UNBOUND,
    st: Any = _UNBOUND,
    streams_m: Any = _UNBOUND,
    sx: Any = _UNBOUND,
    sy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 463 (moat_channels_flow_with_current) - body verbatim from the legacy gate() (feature 022)."""
    if moat_ring and len(moat_ring) >= 3 and mfed:
        # READ THE RECORDED CIRCULATION (GM 2026-07-25). This used to re-derive the moat's current by
        # taking the FIRST stream whose end touches the ring and snapping its entry heading to a
        # cardinal - fragile twice over: on a river-cut city BOTH the feeder and the outfall touch the
        # ring, so the answer depended on which the gen happened to draw first, and the cardinal snap
        # threw away up to 45 degrees. s.moat_flow / s.moat now record the inlet and outlet outright,
        # so the current is simply inlet -> outlet. Falls back to the old derivation for a moat with
        # no recorded circulation (moat_declares_circulation is what stops that being silent).
        # THE CURRENT COMES FROM THE RECORDED CIRCULATION (GM 2026-07-25), snapped to a cardinal as
        # this check has always done. Two fragilities in the old derivation are gone: it took the
        # FIRST stream whose end touched the ring, so on a river-cut city the answer depended on
        # draw order; and it required a stream END within 35px of the ring, which Nagahara's river
        # (ends off-map, the MOAT's ends meeting IT) never satisfies - so the check silently never
        # ran there at all. inlet -> outlet is the moat's net travel and needs no guessing.
        # The cardinal snap is deliberate and load-bearing: an irrigation offtake leaves the ring
        # roughly PERPENDICULAR, so its component along a precisely-measured tangent is near
        # arbitrary. The coarse hemisphere is what makes the test mean "the field is not back
        # upstream", rather than a coin flip on the along-ring component.
        flow = None
        _mfl = M.get("moat_flow") or {}
        if _mfl.get("inlet") and _mfl.get("outlet"):
            _mi, _mo = _mfl["inlet"], _mfl["outlet"]
            _mdx, _mdy = _mo[0] - _mi[0], _mo[1] - _mi[1]
            flow = (0, 1 if _mdy > 0 else -1) if abs(_mdy) >= abs(_mdx) else (1 if _mdx > 0 else -1, 0)
        feeder = None
        for st in streams_m:
            ends = (st["poly"][0], st["poly"][-1])
            ends_on_moat = [e for e in ends if poly_dist(e[0], e[1], moat_ring) <= 35]
            if ends_on_moat:
                entry = ends_on_moat[0]
                feeder = (entry, ends[1] if ends[0] == entry else ends[0])
                break
        if flow is None and feeder:
            entry, origin = feeder
            dx, dy = entry[0] - origin[0], entry[1] - origin[1]  # the heading the feeder water enters on
            flow = (0, 1 if dy > 0 else -1) if abs(dy) >= abs(dx) else (1 if dx > 0 else -1, 0)  # snapped to a cardinal
        if flow is not None:
            against = []
            for c in mfed:
                (sx, sy), (ex, ey) = c["poly"][0], c["poly"][-1]  # frm=moat, so poly[0] is the moat tap
                if (ex - sx) * flow[0] + (ey - sy) * flow[1] < -8:  # field clearly upstream of the tap
                    against.append(c["to"].get("name", "?"))
            check(
                "moat_channels_flow_with_current",
                not against,
                f"moat-fed channel(s) running against the moat current (field is upstream of the tap; the feeder makes the moat flow {flow}): {sorted(set(against))}",
            )
    return _kept(locals(), ('_mdx', '_mdy', '_mfl', '_mi', '_mo', 'against', 'c', 'dx', 'dy', 'e', 'ends', 'ends_on_moat', 'entry', 'ex', 'ey', 'feeder', 'flow', 'origin', 'st', 'sx', 'sy'))


# A MOAT JUNCTION IS SWEPT WITH THE CURRENT (GM 2026-07-25). Where a channel meets the moat, its
# LOCAL heading at the junction must carry a downstream component - a tributary joins a trunk
# pointing downstream, and an irrigation offtake takes off downstream so the water turns in
# smoothly instead of doubling back on itself. The engine already holds moat<->RIVER junctions to
# exactly this (city_moat_junction_angles: inlet near-square, outlet swept downstream); this
# extends it to moat<->CHANNEL junctions, which nothing checked.
#
# NOTE the quantity: the LOCAL segment at the junction, NOT the channel's net vector to its field.
# The net vector is near-arbitrary for an offtake that leaves the ring roughly perpendicular (that
# is why moat_channels_flow_with_current above keeps a coarse cardinal test and is NOT this check).
# The current is the ring TANGENT at the tap, in the direction of travel along that tap's own arc -
# a ring has no single downstream side, since water entering the inlet runs BOTH ways round to the
# outlet. WHAT IT CAUGHT (GM's eye, then this check): every offtake on BOTH cities stepped upstream,
# because the offtake tee was drawn as mirrored geometry whose along-rim step was never oriented to
# the local flow; plus Tango's fn2 drain culvert doubling back to enter at 138 deg and Nagahara's
# fnn1 at 115 deg. Fixtures: the pre-fix Tango and Nagahara manifests in pool/regressions/.


def _seg_0464___mjr(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 464 (_mjr) - body verbatim from the legacy gate() (feature 022)."""
    _mjr: Any = M.get("moat")
    return _kept(locals(), ('_mjr',))


def _seg_0465___mjf(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 465 (_mjf) - body verbatim from the legacy gate() (feature 022)."""
    _mjf = M.get("moat_flow") or {}
    return _kept(locals(), ('_mjf',))


def _seg_0466__moat_junctions_swept_with_the_current(
    *,
    M: Any = _UNBOUND,
    _along: Any = _UNBOUND,
    _cur: Any = _UNBOUND,
    _head: Any = _UNBOUND,
    _hl: Any = _UNBOUND,
    _mfr: Any = _UNBOUND,
    _mj_bad: Any = _UNBOUND,
    _mj_current: Any = _UNBOUND,
    _mjc: Any = _UNBOUND,
    _mjf: Any = _UNBOUND,
    _mjp: Any = _UNBOUND,
    _mjr: Any = _UNBOUND,
    _mto: Any = _UNBOUND,
    _role: Any = _UNBOUND,
    _tap: Any = _UNBOUND,
    _who: Any = _UNBOUND,
    check: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 466 (moat_junctions_swept_with_the_current) - body verbatim from the legacy gate() (feature 022)."""
    if _mjr and len(_mjr) >= 3 and _mjf.get("inlet") and _mjf.get("outlet"):
        _mjn = len(_mjr)

        def _mj_current(tap_: Any) -> tuple[float, float] | None:
            return moat_current_at(_mjr, _mjf["inlet"], _mjf["outlet"], tap_)

        _mj_bad = []
        for _mjc in M.get("channels", []):
            _mjp = _mjc.get("poly") or []
            if len(_mjp) < 2:
                continue
            _mfr, _mto = (_mjc.get("frm") or {}), (_mjc.get("to") or {})
            if _mfr.get("kind") == "moat":  # an OFFTAKE leaves the ring: its mouth is the first step
                _tap, _head, _who, _role = _mjp[0], (_mjp[1][0] - _mjp[0][0], _mjp[1][1] - _mjp[0][1]), _mto.get("name", "?"), "offtake"
            elif _mto.get("kind") == "moat":  # a DRAIN arrives: its last step is the entry
                _tap, _head, _who, _role = _mjp[-1], (_mjp[-1][0] - _mjp[-2][0], _mjp[-1][1] - _mjp[-2][1]), _mfr.get("name", "?"), "drain"
            else:
                continue
            _cur = _mj_current(_tap)
            _hl = math.hypot(*_head)
            if _cur is None or _hl == 0:
                continue
            _along = (_head[0] * _cur[0] + _head[1] * _cur[1]) / _hl
            # A SQUARE TAP IS THE DEFECT, not merely an upstream-facing one. Canal practice: the best
            # offtake alignment is 0 deg to the parent, separating out in transition, and the studied
            # optimum for water and sediment is 15-45 deg - explicitly "30 or 45 INSTEAD OF 90". A
            # perpendicular junction sheds sediment into its own mouth and, on the page, says nothing
            # about which way the water goes. 75 deg is the generous line for "clearly swept": well
            # outside the textbook band, and the engine's two correct junctions (nw1 35, fn1 41) sit
            # comfortably inside it.
            if _along <= math.cos(math.radians(75.0)):
                _mj_bad.append(f"{_who} ({_role}, {math.degrees(math.acos(max(-1.0, min(1.0, _along)))):.0f} deg)")
        check(
            "moat_junctions_swept_with_the_current",
            not _mj_bad,
            f"moat junction(s) not swept downstream: {_mj_bad} - where a channel meets the moat its local heading at "
            f"the junction must carry a DOWNSTREAM component. A tributary joins pointing downstream and an offtake "
            f"takes off downstream; a junction angled back up the current reads as water doubling on itself. Flip the "
            f"offtake tee's along-rim step (or the drain culvert's landing point) to the downstream side",
        )
    return _kept(locals(), ('_along', '_cur', '_head', '_hl', '_mfr', '_mj_bad', '_mj_current', '_mjc', '_mjn', '_mjp', '_mto', '_role', '_tap', '_who'))


# WATER JOINS WATER AT A CONFLUENCE, NEVER CROSSES IT (GM 2026-07-23, feature 014 endgame: "I can
# visually see the intersection where ditches and channels just run into the moat... they just keep
# going and aren't intersecting at the edge"). A channel/ditch segment that strictly CROSSES the
# moat or river centerline mid-run reads as a line painted straight over the open water - a mouth
# must END at the bank instead (the engine's _clip_to_moat/_clip_to_river trim the DRAWING to the
# bed edge + cap radius, and taps/culverts wear the receiving water's own color). The RECORDED
# topology legitimately ends ON the centerline (the anchor checks demand it), so a crossing on a
# polyline's first/last segment whose terminal vertex sits near the crossed water segment is the
# sanctioned confluence touch; anything else is a crossing.


def _seg_0467__xing_w() -> dict[str, Any]:
    """Gate segment 467 (xing_w) - body verbatim from the legacy gate() (feature 022)."""
    xing_w = []  # type: ignore[var-annotated]
    return _kept(locals(), ('xing_w',))


def _seg_0468___wbodies() -> dict[str, Any]:
    """Gate segment 468 (_wbodies) - body verbatim from the legacy gate() (feature 022)."""
    _wbodies = []  # type: ignore[var-annotated]
    return _kept(locals(), ('_wbodies',))


def _seg_0469___wbodies_1(*, M: Any = _UNBOUND, _wbodies: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 469 (_wbodies) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("moat") and len(M["moat"]) >= 3:
        _wbodies.append(("moat", M["moat"]))
    return _kept(locals(), ('_wbodies',))


def _seg_0470___wbodies_2(*, M: Any = _UNBOUND, _wbodies: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 470 (_wbodies) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("river") and (M["river"].get("pts") if isinstance(M.get("river"), dict) else None):
        _wbodies.append(("river", M["river"]["pts"]))
    return _kept(locals(), ('_wbodies',))


def _seg_0471___a(
    *,
    M: Any = _UNBOUND,
    _a: Any = _UNBOUND,
    _b: Any = _UNBOUND,
    _ch: Any = _UNBOUND,
    _conf: Any = _UNBOUND,
    _i: Any = _UNBOUND,
    _k: Any = _UNBOUND,
    _nm: Any = _UNBOUND,
    _pl: Any = _UNBOUND,
    _wb: Any = _UNBOUND,
    _wbodies: Any = _UNBOUND,
    xing_w: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 471 (_a, _b, _ch, _conf) - body verbatim from the legacy gate() (feature 022)."""
    if _wbodies:
        for _ch in M.get("channels", []) + M.get("field_ditches", []):
            _pl = _ch.get("poly") or []  # a short/absent poly simply yields no segments
            for _i in range(len(_pl) - 1):
                _a, _b = _pl[_i], _pl[_i + 1]
                for _nm, _wb in _wbodies:
                    for _k in range(len(_wb) - 1):
                        if not segments_cross(_a, _b, _wb[_k], _wb[_k + 1]):
                            continue
                        _conf = (_i == 0 and seg_dist(_pl[0][0], _pl[0][1], _wb[_k], _wb[_k + 1]) < 20) or (_i == len(_pl) - 2 and seg_dist(_pl[-1][0], _pl[-1][1], _wb[_k], _wb[_k + 1]) < 20)
                        if not _conf:
                            xing_w.append((_nm, round(_a[0]), round(_a[1])))
    return _kept(locals(), ('_a', '_b', '_ch', '_conf', '_i', '_k', '_nm', '_pl', '_wb', 'xing_w'))


def _seg_0472__channels_join_water_not_cross(*, check: Any = _UNBOUND, xing_w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 472 (channels_join_water_not_cross) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "channels_join_water_not_cross",
        not xing_w,
        f"channel/ditch segment(s) CROSS a moat/river centerline mid-run at {sorted(set(xing_w))[:4]} - water joins "
        "water at a CONFLUENCE (the mouth ends at the bank, engine-trimmed and water-colored), it never runs "
        "straight across the open water like a painted line; end the polyline at the centerline (the anchor "
        "convention) instead of passing through",
    )
    return _kept(locals(), ())


# THE POND FILL COVERS EVERY JOINING MOUTH (GM 2026-07-23, Tango's in-wall tank: the comb
# head-race's round end-cap rendered ON TOP of the pond and the channel read as INTERSECTING
# the open water instead of joining it). Doctrine (settlements.md "A pond JOINS its feeders at
# the rim"): a joining course must overshoot the rim so its bed covers the rim stroke at the
# mouth - the clean gap - which in turn requires the POND FILL to paint over that overshoot.
# That is a Z-ORDER property, so it is checked via recorded draw positions like
# waterways_merge_at_crossings: the engine records every drawn comb/field channel stroke in
# M['drawn_channels'] (post-clip geometry + bedz + late flag) and the pond fill's position in
# M['pond_layer'] (relocated into the LATE water block when a late-block channel joins - the
# Tango case: the late block draws after the shared block, so an early fill can never cover a
# late mouth). bedz values are offsets within their OWN splice block, NOT globally comparable -
# cross-block draw order is carried by the (late, bedz) PAIR, compared lexicographically (the
# late block always renders after the whole shared block; streams/channels are always early).
# Three clauses: (a) a pond join with NO layering records is exactly the uncovered cap (fires
# the frozen pre-fix Tango fixture); (b) every z-recorded joining bed must sit BELOW the fill
# in (late, bedz) order; (c) a drawn stroke must never run THROUGH the open water mid-run
# (mouths, not crossings - the pond sibling of channels_join_water_not_cross). Undrawn
# (drawn=False) topology conduits are exempt: nothing rendered, nothing to cover.


def _seg_0473__pond_e(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 473 (pond_e) - body verbatim from the legacy gate() (feature 022)."""
    pond_e = M.get("pond")
    return _kept(locals(), ('pond_e',))


def _seg_0474__pond_fill_covers_channel_mouths(
    *,
    M: Any = _UNBOUND,
    _ditch_joins: Any = _UNBOUND,
    _pjz: Any = _UNBOUND,
    _pl: Any = _UNBOUND,
    _pz: Any = _UNBOUND,
    blate: Any = _UNBOUND,
    bz: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    dc: Any = _UNBOUND,
    dd: Any = _UNBOUND,
    k: Any = _UNBOUND,
    pond_bad: Any = _UNBOUND,
    pond_e: Any = _UNBOUND,
    pt: Any = _UNBOUND,
    q: Any = _UNBOUND,
    st: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 474 (pond_fill_covers_channel_mouths) - body verbatim from the legacy gate() (feature 022)."""
    if pond_e:
        _pjz: list[tuple[Any, Any, bool]] = []  # type: ignore[no-redef]  # (endpoint, bedz, late) of every z-recorded course touching the rim zone
        for dc in M.get("drawn_channels", []):
            for pt in (dc["pts"][0], dc["pts"][-1]):
                if in_ellipse(pt[0], pt[1], pond_e, scale=1.06):
                    _pjz.append((pt, dc.get("bedz"), bool(dc.get("late"))))
        for st in M.get("streams", []):
            for pt in (st["poly"][0], st["poly"][-1]):
                if in_ellipse(pt[0], pt[1], pond_e, scale=1.06):
                    _pjz.append((pt, st.get("bedz"), False))
        for c in M.get("channels", []):
            # drawn=False marks an implied underground conduit; a record with NO bedz is a gen-side
            # TOPOLOGY entry (its visible stroke, if any, is recorded separately in drawn_channels -
            # Hoshigaoka's head-race). Only a bed s.channel actually drew (bedz recorded) can cover
            # or fail to cover anything.
            if c.get("drawn") is False or c.get("bedz") is None:
                continue
            for pt in (c["poly"][0], c["poly"][-1]):
                if in_ellipse(pt[0], pt[1], pond_e, scale=1.06):
                    _pjz.append((pt, c.get("bedz"), False))
        # a comb ditch is always drawn: a joining ditch record demands a matching drawn stroke record
        _ditch_joins = any(in_ellipse(pt[0], pt[1], pond_e, scale=1.06) for dd in M.get("field_ditches", []) for pt in (dd["poly"][0], dd["poly"][-1]))
        _pl = M.get("pond_layer") or {}
        _pz = _pl.get("bedz")
        pond_bad: list[str] = []  # type: ignore[no-redef]
        if (_pjz or _ditch_joins) and _pz is None:
            pond_bad.append("a course joins the pond but M['pond_layer'] records no fill position")
        if _ditch_joins and not any(in_ellipse(dc["pts"][k][0], dc["pts"][k][1], pond_e, scale=1.06) for dc in M.get("drawn_channels", []) for k in (0, -1)):
            pond_bad.append("a field ditch joins the pond but no drawn stroke is recorded in M['drawn_channels']")
        pond_bad += [f"bed at {(round(pt[0]), round(pt[1]))} not under the fill" for pt, bz, blate in _pjz if _pz is not None and (bz is None or (blate, bz) >= (bool(_pl.get("late")), _pz))]
        pond_bad += [
            f"drawn stroke runs THROUGH the open water at {(round(q[0]), round(q[1]))}" for dc in M.get("drawn_channels", []) for q in dc["pts"][1:-1] if in_ellipse(q[0], q[1], pond_e, scale=0.9)
        ]
        check(
            "pond_fill_covers_channel_mouths",
            not pond_bad,
            "a channel INTERSECTS the pond instead of joining it: " + "; ".join(sorted(set(pond_bad))[:4]) + " - a mouth overshoots the rim (covering the rim stroke) and the pond FILL "
            "must draw over that overshoot; route the stroke through s.field_channel/s.channel/s.stream and let the engine relocate the fill to the late block when a late course joins",
        )
    return _kept(locals(), ('_ditch_joins', '_pjz', '_pl', '_pz', 'blate', 'bz', 'c', 'dc', 'dd', 'k', 'pond_bad', 'pt', 'q', 'st'))


# A WATER-TO-WATER HANDOFF SHOWS ITS CONTROL GATE (GM 2026-07-23, the junction-seams pass): where a
# moat/river tap hands off to the comb's own canal (the sluice - the palette seam sits exactly there)
# and where a field drain hands off to its outfall culvert into the moat, a sluice_gate glyph must
# mark the junction - the control board is what makes the color/direction change read as engineered
# plumbing rather than two strokes crossing. The tap's recorded poly is [water-vertex, sluice, plot],
# so the gate belongs near poly[1]; a drain culvert's is [drain-end, moat-vertex], gate near poly[0].


def _seg_0475__gateless() -> dict[str, Any]:
    """Gate segment 475 (gateless) - body verbatim from the legacy gate() (feature 022)."""
    gateless = []  # type: ignore[var-annotated]
    return _kept(locals(), ('gateless',))


def _seg_0476___sgs(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 476 (_sgs) - body verbatim from the legacy gate() (feature 022)."""
    _sgs = M.get("sluice_gates", [])
    return _kept(locals(), ('_sgs',))


def _seg_0477___ch(
    *, M: Any = _UNBOUND, _ch: Any = _UNBOUND, _fk: Any = _UNBOUND, _g: Any = _UNBOUND, _jp: Any = _UNBOUND, _pl: Any = _UNBOUND, _sgs: Any = _UNBOUND, _tk: Any = _UNBOUND, gateless: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 477 (_ch, _fk, _g, _jp) - body verbatim from the legacy gate() (feature 022)."""
    for _ch in M.get("channels", []):
        _fk = (_ch.get("frm") or {}).get("kind")
        _tk = (_ch.get("to") or {}).get("kind")
        _pl = _ch.get("poly") or []
        _jp = None
        if _fk in ("moat", "river") and _tk == "field" and len(_pl) >= 2:
            _jp = _pl[1]  # the sluice point
        elif _fk == "drain" and _tk == "moat" and _pl and _ch.get("drawn"):
            _jp = _pl[0]  # the drain -> culvert handoff (drawn culverts only: an UNDROWN record is an
            # implied underground conduit - Tango's in-wall nw1 drain drops beneath the rampart - with
            # no visible seam to gate)
        if _jp is not None and not any(math.hypot(_g["x"] - _jp[0], _g["y"] - _jp[1]) <= 16 for _g in _sgs):
            gateless.append((round(_jp[0]), round(_jp[1])))
    return _kept(locals(), ('_ch', '_fk', '_g', '_jp', '_pl', '_tk', 'gateless'))


def _seg_0478__channel_gates_at_water_junctions(*, check: Any = _UNBOUND, gateless: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 478 (channel_gates_at_water_junctions) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "channel_gates_at_water_junctions",
        not gateless,
        f"water-to-water handoff(s) with no sluice gate at {sorted(set(gateless))[:4]} - a moat/river tap "
        "hands off to the comb canal (and a drain to its outfall culvert) through a CONTROL GATE; draw "
        "s.sluice_gate(x, y, rot=<channel heading + 90>) at the junction so the palette seam reads as "
        "engineered plumbing, not two strokes crossing",
    )
    return _kept(locals(), ())


# AN IN-WALL DRAIN CUTS OFF AT A GATE BEFORE THE RING ROAD (GM 2026-07-23, Tango's in-wall
# nw1 drain: the visible runoff ditch ran up to the patrol road's verge and simply STOPPED -
# a bare cut end, unfinished linework). Doctrine: a walled city's in-wall drainage never
# visibly pierces road, rampart or moat - the water leaves through an UNDERGROUND stone
# culvert, recorded as an undrawn drain->moat conduit (channel_gates_at_water_junctions
# deliberately exempts that conduit's invisible moat-side seam). But the DROP into the
# culvert is a real engineered structure and the map must say so: the visible ditch is
# TRIMMED back to a cut point clear of the ring road and wears a sluice_gate glyph there
# (the gate is what tells the reader the ditch drains into artificial plumbing connected to
# the moat, even though the connection itself is invisible). The conduit's START is that cut
# point - where the water goes underground. For every undrawn drain->moat conduit starting
# INSIDE the wall: (a) a drawn stroke must END at the conduit's start (the visible ditch
# reaches the drop - within 8px); (b) the cut point stays >= half the ring-road width + 4px
# off the ring-road centerline, and no drawn stroke touching it crosses the centerline (the
# pre-fix Tango stub lapped 3px PAST it); (c) a sluice_gate sits within 16px of the cut
# point (the gate tolerance channel_gates_at_water_junctions uses). Engine helper:
# s.inwall_drain_outfall() trims the drain, places the gate, and records the conduit.


def _seg_0479__inwall_bad() -> dict[str, Any]:
    """Gate segment 479 (inwall_bad) - body verbatim from the legacy gate() (feature 022)."""
    inwall_bad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('inwall_bad',))


def _seg_0480___ch_1(
    *,
    M: Any = _UNBOUND,
    _ch: Any = _UNBOUND,
    _co: Any = _UNBOUND,
    _irhw: Any = _UNBOUND,
    _iring: Any = _UNBOUND,
    _iw_touch: Any = _UNBOUND,
    _spts: Any = _UNBOUND,
    dc: Any = _UNBOUND,
    g: Any = _UNBOUND,
    i: Any = _UNBOUND,
    inwall_bad: Any = _UNBOUND,
    j: Any = _UNBOUND,
    k: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 480 (_ch, _co, _irhw, _iring) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("wall"):
        _iring = M.get("ring_road") or []
        _irhw = (M.get("ring_road_width") or 20) / 2
        for _ch in M.get("channels", []):
            if (_ch.get("frm") or {}).get("kind") != "drain" or (_ch.get("to") or {}).get("kind") != "moat" or _ch.get("drawn"):
                continue  # drawn culverts carry their gate at the drain handoff (checked above)
            _co = _ch["poly"][0]
            if not point_in_poly(_co[0], _co[1], M["wall"]):
                continue  # an outside-the-wall conduit has no rampart to pass under
            _iw_touch = [dc["pts"] for dc in M.get("drawn_channels", []) if any(math.hypot(dc["pts"][k][0] - _co[0], dc["pts"][k][1] - _co[1]) <= 8 for k in (0, -1))]
            if not _iw_touch:
                inwall_bad.append(f"no visible ditch reaches the drop at {(round(_co[0]), round(_co[1]))}")
            if _iring and min(seg_dist(_co[0], _co[1], _iring[i], _iring[i + 1]) for i in range(len(_iring) - 1)) < _irhw + 4:
                inwall_bad.append(f"cut point {(round(_co[0]), round(_co[1]))} rides the ring road - trim the ditch off short of the patrol road")
            for _spts in _iw_touch:
                if any(segments_cross(_spts[i], _spts[i + 1], _iring[j], _iring[j + 1]) for i in range(len(_spts) - 1) for j in range(len(_iring) - 1)):
                    inwall_bad.append(f"the ditch at {(round(_co[0]), round(_co[1]))} CROSSES the ring road - it must stop before it")
            if not any(math.hypot(g["x"] - _co[0], g["y"] - _co[1]) <= 16 for g in M.get("sluice_gates", [])):
                inwall_bad.append(f"no sluice gate at the cutoff {(round(_co[0]), round(_co[1]))}")
    return _kept(locals(), ('_ch', '_co', '_irhw', '_iring', '_iw_touch', '_spts', 'dc', 'g', 'i', 'inwall_bad', 'j', 'k'))


def _seg_0481__inwall_drains_gated_at_cutoff(*, check: Any = _UNBOUND, inwall_bad: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 481 (inwall_drains_gated_at_cutoff) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "inwall_drains_gated_at_cutoff",
        not inwall_bad,
        "; ".join(sorted(set(inwall_bad))[:4]) + " - an in-wall drain cuts off short of the ring road and drops through a "
        "sluice gate into the underground culvert to the moat (the gate glyph is what makes the bare cut end read as "
        "engineered plumbing); trim the drain through s.inwall_drain_outfall()",
    )
    return _kept(locals(), ())


# large area features (forests, pastures) near a map edge must run OFF it - implying
# they continue beyond what's drawn. Bounded farm fields are exempt.


def _seg_0482__NEAR() -> dict[str, Any]:
    """Gate segment 482 (NEAR) - body verbatim from the legacy gate() (feature 022)."""
    NEAR = 55
    return _kept(locals(), ('NEAR',))


def _seg_0483__area_feats(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 483 (area_feats) - body verbatim from the legacy gate() (feature 022)."""
    area_feats = [("forest", M["forest"])] if M.get("forest") else []
    return _kept(locals(), ('area_feats',))


def _seg_0484__area_feats_1(*, M: Any = _UNBOUND, area_feats: Any = _UNBOUND, fp: Any = _UNBOUND, i: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 484 (area_feats, fp, i) - body verbatim from the legacy gate() (feature 022)."""
    area_feats += [(f"forest_patch[{i}]", fp) for i, fp in enumerate(M.get("forest_patches", []))]
    return _kept(locals(), ('area_feats', 'fp', 'i'))


def _seg_0485__area_feats_2(*, M: Any = _UNBOUND, area_feats: Any = _UNBOUND, i: Any = _UNBOUND, ps: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 485 (area_feats, i, ps) - body verbatim from the legacy gate() (feature 022)."""
    area_feats += [(f"pasture[{i}]", ps) for i, ps in enumerate(M.get("pastures", []))]
    return _kept(locals(), ('area_feats', 'i', 'ps'))


def _seg_0486__edge_bad() -> dict[str, Any]:
    """Gate segment 486 (edge_bad) - body verbatim from the legacy gate() (feature 022)."""
    edge_bad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('edge_bad',))


def _seg_0487__edge_bad_1(
    *,
    EX0: Any = _UNBOUND,
    EX1: Any = _UNBOUND,
    EY0: Any = _UNBOUND,
    EY1: Any = _UNBOUND,
    NEAR: Any = _UNBOUND,
    area_feats: Any = _UNBOUND,
    edge_bad: Any = _UNBOUND,
    nm: Any = _UNBOUND,
    ol: Any = _UNBOUND,
    p: Any = _UNBOUND,
    xs: Any = _UNBOUND,
    ys: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 487 (edge_bad, nm, ol, p) - body verbatim from the legacy gate() (feature 022)."""
    for nm, ol in area_feats:
        xs, ys = [p[0] for p in ol], [p[1] for p in ol]
        if EX1 - NEAR <= max(xs) < EX1:
            edge_bad.append(f"{nm}:right")
        if EX0 < min(xs) <= EX0 + NEAR:
            edge_bad.append(f"{nm}:left")
        if EY1 - NEAR <= max(ys) < EY1:
            edge_bad.append(f"{nm}:bottom")
        if EY0 < min(ys) <= EY0 + NEAR:
            edge_bad.append(f"{nm}:top")
    return _kept(locals(), ('edge_bad', 'nm', 'ol', 'p', 'xs', 'ys'))


def _seg_0488__edge_features_run_off_map(*, check: Any = _UNBOUND, edge_bad: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 488 (edge_features_run_off_map) - body verbatim from the legacy gate() (feature 022)."""
    check("edge_features_run_off_map", not edge_bad, f"edge feature(s) stop short of the edge: {edge_bad}")
    return _kept(locals(), ())


# roads and streams must run off the map edge (a stream may instead end in a pond
# at one end; irrigation channels are exempt - they connect ponds/fields)


def _seg_0489__EDGE() -> dict[str, Any]:
    """Gate segment 489 (EDGE) - body verbatim from the legacy gate() (feature 022)."""
    EDGE = 30
    return _kept(locals(), ('EDGE',))


def _seg_0490__at_edge(*, EDGE: Any = _UNBOUND, EX0: Any = _UNBOUND, EX1: Any = _UNBOUND, EY0: Any = _UNBOUND, EY1: Any = _UNBOUND, pt: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 490 (at_edge) - body verbatim from the legacy gate() (feature 022)."""

    def at_edge(pt: Pt) -> bool:
        return pt[0] <= EX0 + EDGE or pt[0] >= EX1 - EDGE or pt[1] <= EY0 + EDGE or pt[1] >= EY1 - EDGE  # type: ignore[no-any-return]

    return _kept(locals(), ('at_edge',))


def _seg_0491__road_runs_off_edge(*, at_edge: Any = _UNBOUND, check: Any = _UNBOUND, road: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 491 (road_runs_off_edge) - body verbatim from the legacy gate() (feature 022)."""
    if road:
        check("road_runs_off_edge", at_edge(road[0]) and at_edge(road[-1]), f"a road must reach the map edge at both ends (ends {road[0]}, {road[-1]})")
    return _kept(locals(), ())


# a CONNECTOR lane (the trodden path leaving the village for the wider world) must run OFF the map
# edge - it links to a district/Imperial road (or a canal landing) beyond the frame, so it must not
# stop mid-landscape. Internal lanes (the spine, field spurs) are exempt: they legitimately end in
# the cluster or at the paddy. See settlements.md 'Village lanes and connecting paths'.


def _seg_0492__connector_lane_runs_off_edge(*, M: Any = _UNBOUND, at_edge: Any = _UNBOUND, check: Any = _UNBOUND, i: Any = _UNBOUND, ln: Any = _UNBOUND, p: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 492 (connector_lane_runs_off_edge) - body verbatim from the legacy gate() (feature 022)."""
    for i, ln in enumerate(M.get("lanes", [])):
        if ln.get("connector"):
            p = ln["pts"]
            check(
                f"connector_lane_runs_off_edge[{i}]",
                at_edge(p[0]) or at_edge(p[-1]),
                f"the connector path (lane {i}) must run OFF the map edge (ends {p[0]}, {p[-1]}) - it leaves the village for the wider world and must not stop mid-landscape",
            )
    return _kept(locals(), ('i', 'ln', 'p'))


# FARMHOUSES must not sit ON a village lane - a lane lays a no-build corridor and houses FRONT it,
# never overlap the tread (place lanes BEFORE the houses). Fires if any house footprint corner/center
# falls within the lane's tread half-width.


def _seg_0493___house_pts(*, h: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 493 (_house_pts) - body verbatim from the legacy gate() (feature 022)."""

    def _house_pts(h: dict[str, Any]) -> list[tuple[float, float]]:
        hw2, hh2 = h["w"] / 2, h["h"] / 2
        return [(h["x"] - hw2, h["y"] - hh2), (h["x"] + hw2, h["y"] - hh2), (h["x"] + hw2, h["y"] + hh2), (h["x"] - hw2, h["y"] + hh2), (h["x"], h["y"])]

    return _kept(locals(), ('_house_pts',))


def _seg_0494__lane_hits() -> dict[str, Any]:
    """Gate segment 494 (lane_hits) - body verbatim from the legacy gate() (feature 022)."""
    lane_hits = []  # type: ignore[var-annotated]
    return _kept(locals(), ('lane_hits',))


def _seg_0495__cx(
    *,
    M: Any = _UNBOUND,
    _house_pts: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    h: Any = _UNBOUND,
    half: Any = _UNBOUND,
    k: Any = _UNBOUND,
    lane_hits: Any = _UNBOUND,
    ln: Any = _UNBOUND,
    p: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 495 (cx, cy, h, half) - body verbatim from the legacy gate() (feature 022)."""
    for h in M.get("houses", []):
        for ln in M.get("lanes", []):
            half = ln.get("w", 5) / 2 + 2  # tread half-width + a hair
            p = ln["pts"]
            if any(seg_dist(cx, cy, p[k], p[k + 1]) < half for cx, cy in _house_pts(h) for k in range(len(p) - 1)):
                lane_hits.append((round(h["x"]), round(h["y"])))
                break
    return _kept(locals(), ('cx', 'cy', 'h', 'half', 'k', 'lane_hits', 'ln', 'p'))


def _seg_0496__houses_clear_of_lanes(*, check: Any = _UNBOUND, lane_hits: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 496 (houses_clear_of_lanes) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "houses_clear_of_lanes",
        not lane_hits,
        f"farmhouse(s) sit ON a village lane at {lane_hits[:5]} - a lane is a no-build corridor; houses FRONT it, never overlap the tread (lay lanes BEFORE the houses so they pack around it)",
    )
    return _kept(locals(), ())


# A shrine/temple HALL must not sit ON a lane/street/road: a building stands BESIDE the way, not in it. The
# TORII is the deliberate exception - a gateway arch straddles the approach path and the road runs UNDER it
# (a real, common feature), so torii are NOT checked here. The road may run up to and through the torii to a
# hall set just off the way. Covers religious halls (shrine/monastery/temple). WHY: settlements.md 'Shrines'.


def _seg_0497__hall_on_lane() -> dict[str, Any]:
    """Gate segment 497 (hall_on_lane) - body verbatim from the legacy gate() (feature 022)."""
    hall_on_lane = []  # type: ignore[var-annotated]
    return _kept(locals(), ('hall_on_lane',))


def _seg_0498___hcorr(*, M: Any = _UNBOUND, ln: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 498 (_hcorr, ln) - body verbatim from the legacy gate() (feature 022)."""
    _hcorr = [(ln["pts"], ln.get("w", 6) / 2 + 2) for ln in M.get("lanes", [])]
    return _kept(locals(), ('_hcorr', 'ln'))


def _seg_0499___hcorr_1(*, M: Any = _UNBOUND, _hcorr: Any = _UNBOUND, s: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 499 (_hcorr, s) - body verbatim from the legacy gate() (feature 022)."""
    _hcorr += [(s["pts"], s.get("w", 10) / 2 + 2) for s in M.get("town_streets", [])]
    return _kept(locals(), ('_hcorr', 's'))


def _seg_0500___hcorr_2(*, M: Any = _UNBOUND, _hcorr: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 500 (_hcorr) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("road"):
        _hcorr.append((M["road"], M.get("road_width", 26) / 2 + 2))
    return _kept(locals(), ('_hcorr',))


def _seg_0501__half(
    *, M: Any = _UNBOUND, _hcorr: Any = _UNBOUND, half: Any = _UNBOUND, hall: Any = _UNBOUND, hall_on_lane: Any = _UNBOUND, k: Any = _UNBOUND, p: Any = _UNBOUND, rect: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 501 (half, hall, hall_on_lane, k) - body verbatim from the legacy gate() (feature 022)."""
    for hall in M.get("religious", []):
        rect = _struct_rect(hall)
        if any(seg_to_rect_dist(p[k], p[k + 1], rect) < half for p, half in _hcorr for k in range(len(p) - 1)):
            hall_on_lane.append((round(hall["x"]), round(hall["y"])))
    return _kept(locals(), ('half', 'hall', 'hall_on_lane', 'k', 'p', 'rect'))


def _seg_0502__shrine_halls_clear_of_lanes(*, check: Any = _UNBOUND, hall_on_lane: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 502 (shrine_halls_clear_of_lanes) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "shrine_halls_clear_of_lanes",
        not hall_on_lane,
        f"shrine/temple hall(s) sit ON a lane/street/road at {hall_on_lane[:4]} - a HALL stands beside the way, "
        f"not in it (place it off the corridor); the road may pass UNDER the shrine's TORII (arches are exempt), "
        f"but never through the hall itself",
    )
    return _kept(locals(), ())


# TREES must not be drawn ON a lane / street / road - a path is bare trodden earth, not planted over. Covers
# BOTH the communal fengshui grove (village_groves: each records its actual drawn clump centers + radius) and
# the per-house windbreak grove (groves: a rect footprint). Every corridor (lanes, town streets, the road) is
# a keep-out; the generator skips any clump within it, and this verifies nothing slipped through.


def _seg_0503__corridors(*, M: Any = _UNBOUND, ln: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 503 (corridors, ln) - body verbatim from the legacy gate() (feature 022)."""
    corridors = [(ln["pts"], ln.get("w", 6) / 2) for ln in M.get("lanes", [])]
    return _kept(locals(), ('corridors', 'ln'))


def _seg_0504__corridors_1(*, M: Any = _UNBOUND, corridors: Any = _UNBOUND, s: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 504 (corridors, s) - body verbatim from the legacy gate() (feature 022)."""
    corridors += [(s["pts"], s.get("w", 10) / 2) for s in M.get("town_streets", [])]
    return _kept(locals(), ('corridors', 's'))


def _seg_0505__corridors_2(*, M: Any = _UNBOUND, corridors: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 505 (corridors) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("road"):
        corridors.append((M["road"], M.get("road_width", 26) / 2))
    return _kept(locals(), ('corridors',))


def _seg_0506__tree_on_path() -> dict[str, Any]:
    """Gate segment 506 (tree_on_path) - body verbatim from the legacy gate() (feature 022)."""
    tree_on_path = []  # type: ignore[var-annotated]
    return _kept(locals(), ('tree_on_path',))


def _seg_0507__cx_1(
    *,
    M: Any = _UNBOUND,
    corridors: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    g: Any = _UNBOUND,
    half: Any = _UNBOUND,
    k: Any = _UNBOUND,
    p: Any = _UNBOUND,
    r: Any = _UNBOUND,
    tree_on_path: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 507 (cx, cy, g, half) - body verbatim from the legacy gate() (feature 022)."""
    for g in M.get("village_groves", []):
        r = g.get("r", 6)
        for cx, cy in g.get("clumps", []):
            if any(seg_dist(cx, cy, p[k], p[k + 1]) < half + r for p, half in corridors for k in range(len(p) - 1)):
                tree_on_path.append((round(cx), round(cy)))
                break
    return _kept(locals(), ('cx', 'cy', 'g', 'half', 'k', 'p', 'r', 'tree_on_path'))


def _seg_0508__cx_2(
    *,
    M: Any = _UNBOUND,
    corridors: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    g: Any = _UNBOUND,
    gc: Any = _UNBOUND,
    half: Any = _UNBOUND,
    k: Any = _UNBOUND,
    p: Any = _UNBOUND,
    tree_on_path: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 508 (cx, cy, g, gc) - body verbatim from the legacy gate() (feature 022)."""
    for g in M.get("groves", []):
        gc = rect_corners(_struct_rect(g)) + [(g["x"], g["y"])]
        if any(seg_dist(cx, cy, p[k], p[k + 1]) < half for cx, cy in gc for p, half in corridors for k in range(len(p) - 1)):
            tree_on_path.append((round(g["x"]), round(g["y"])))
    return _kept(locals(), ('cx', 'cy', 'g', 'gc', 'half', 'k', 'p', 'tree_on_path'))


def _seg_0509__groves_clear_of_lanes(*, check: Any = _UNBOUND, tree_on_path: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 509 (groves_clear_of_lanes) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "groves_clear_of_lanes",
        not tree_on_path,
        f"tree/grove clump(s) sit ON a lane/street/road at {tree_on_path[:4]} - a path is bare trodden earth; keep vegetation off every corridor (the generator skips clumps within a lane's keep-out)",
    )
    return _kept(locals(), ())


def _seg_0510__moat_ring_1(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 510 (moat_ring) - body verbatim from the legacy gate() (feature 022)."""
    moat_ring = M.get("moat")
    return _kept(locals(), ('moat_ring',))


def _seg_0511__stream_runs_off_edge(
    *,
    M: Any = _UNBOUND,
    anchored: Any = _UNBOUND,
    at_ditch: Any = _UNBOUND,
    at_drain: Any = _UNBOUND,
    at_edge: Any = _UNBOUND,
    at_moat: Any = _UNBOUND,
    at_river: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d: Any = _UNBOUND,
    dp: Any = _UNBOUND,
    e: Any = _UNBOUND,
    e0: Any = _UNBOUND,
    e1: Any = _UNBOUND,
    f: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    i: Any = _UNBOUND,
    idx: Any = _UNBOUND,
    in_field: Any = _UNBOUND,
    in_pond: Any = _UNBOUND,
    moat_ring: Any = _UNBOUND,
    ok: Any = _UNBOUND,
    p: Any = _UNBOUND,
    pond: Any = _UNBOUND,
    st: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 511 (stream_runs_off_edge) - body verbatim from the legacy gate() (feature 022)."""
    for idx, st in enumerate(M.get("streams", [])):
        e0, e1 = st["poly"][0], st["poly"][-1]

        def in_pond(p: Pt) -> bool:
            return bool(pond) and in_ellipse(p[0], p[1], pond, 1.05)

        def at_moat(p: Pt) -> bool:
            return bool(moat_ring) and poly_dist(p[0], p[1], moat_ring) <= 32  # a city stream may feed the moat

        def at_drain(p: Pt) -> bool:
            return anchored(p, {"kind": "drain"})  # type: ignore[no-any-return]  # a brook may START at the field drain's outfall

        def in_field(p: Pt) -> bool:
            return any(point_in_poly(p[0], p[1], f["outline"]) for f in fields)  # a SOURCE brook may END at the field head

        def at_ditch(p: Pt) -> bool:
            return any(
                seg_dist(p[0], p[1], dp[i], dp[i + 1]) < 22  # a brook DIVERTED into an irrigation channel
                for d in (M.get("field_ditches", []) + M.get("channels", []))
                for dp in [d["poly"]]
                for i in range(len(dp) - 1)
            )

        def at_river(p: Pt) -> bool:
            # a sluiced moat FEEDER taps the trunk river (feature 020's capital: the ring stands
            # ~200px off the bank, so the connection Minami/Nagahara get from their moat feet is
            # drawn as a short leat instead). The river is itself edge-sourced, so a stream rooted
            # on it inherits a real source the way an edge end does.
            riv_ = M.get("river")
            rp_ = (riv_ or {}).get("pts") or (riv_ or {}).get("poly")
            if not rp_:
                return False
            return any(seg_dist(p[0], p[1], rp_[i], rp_[i + 1]) <= (riv_ or {}).get("w", 40) / 2 + 12 for i in range(len(rp_) - 1))

        ok = all(at_edge(e) or in_pond(e) or at_moat(e) or at_drain(e) or in_field(e) or at_ditch(e) or at_river(e) for e in (e0, e1)) and (at_edge(e0) or at_edge(e1) or at_river(e0) or at_river(e1))
        check(f"stream_runs_off_edge[{idx}]", ok, f"stream {idx} ends {e0},{e1} must run off the edge (one end may be a pond, the moat, the field drain, the field head, or a trunk-river tap)")
    return _kept(locals(), ('at_ditch', 'at_drain', 'at_moat', 'at_river', 'e', 'e0', 'e1', 'idx', 'in_field', 'in_pond', 'ok', 'st'))


# WATER SOURCES COME FROM THE MAP EDGE: a pond does not generate water, so any brook FEEDING it (a
# stream with one end in the pond) must ORIGINATE off-map - it flows in from the edge, not out of
# nowhere. (A sole-storage / rain-fed pond with no feeder stream is exempt - no inflow to check.)


def _seg_0512__pond_fed_from_edge(
    *,
    M: Any = _UNBOUND,
    at_edge: Any = _UNBOUND,
    check: Any = _UNBOUND,
    far: Any = _UNBOUND,
    near: Any = _UNBOUND,
    p: Any = _UNBOUND,
    pond: Any = _UNBOUND,
    st: Any = _UNBOUND,
    unsourced: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 512 (pond_fed_from_edge) - body verbatim from the legacy gate() (feature 022)."""
    if pond:
        unsourced = []
        for st in M.get("streams", []):
            p = st["poly"]
            for near, far in ((p[0], p[-1]), (p[-1], p[0])):
                if in_ellipse(near[0], near[1], pond, 1.05) and not at_edge(far):
                    unsourced.append([round(far[0]), round(far[1])])
        check(
            "pond_fed_from_edge",
            not unsourced,
            f"a stream feeds the pond but its far end {unsourced[:3]} is not at the map edge - a pond's feeder brook must flow IN from off-map (the water source comes from the edge, not nowhere)",
        )
    return _kept(locals(), ('far', 'near', 'p', 'st', 'unsourced'))
