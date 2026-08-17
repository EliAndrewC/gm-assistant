"""Gate segments (bridge labels and reach; keys 0360-0386) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from l7r.diagram.settlement import bridge_crossed_waters

from .common_01_geometry import point_in_poly, seg_closest, seg_dist, segments_cross
from .common_02_overlap_policy import GridIndex
from .common_03_capacity import _UNBOUND, DWELLING_KINDS, _kept

# A DECK LANDS PAST ITS BANKS (GM 2026-08-09, tightened from ends-reach-the-edge): every
# CORNER of the deck clears the crossed water's edge onto dry ground. The ends-based rule
# let an oblique deck pass with a corner sitting exactly AT the water's edge (the capital's
# east deck landed 0.0 ft), which reads structurally impossible - a real abutment sill sits
# BACK from the channel edge so scour cannot undercut the bearing (settlement.LANDING_FT
# holds the research). s.bridges() draws LANDING_FT (10 real ft) of landing per side; the
# floor here is 6 ft so local water curvature under a deck does not flap the gate. A
# standalone FOOTPLANK keeps its deliberately short PLANK_ABUTMENT (GM 2026-07-22) and is
# floored at 2 ft. Real feet, converted via meta.ftpx. The crossed water is the WIDEST
# watercourse under the deck's seat, from the same shared source both bridging sides read;
# footprint family: gap VERDICT, measured on the deck's four real corners.


def _seg_0360__b_ftpx(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 360 (b_ftpx) - body verbatim from the legacy gate() (feature 022)."""
    b_ftpx = float(meta.get("ftpx", 1) or 1)
    return _kept(locals(), ('b_ftpx',))


def _seg_0361__b_short() -> dict[str, Any]:
    """Gate segment 361 (b_short) - body verbatim from the legacy gate() (feature 022)."""
    b_short = []  # type: ignore[var-annotated]
    return _kept(locals(), ('b_short',))


def _seg_0362__b_dry() -> dict[str, Any]:
    """Gate segment 362 (b_dry) - body verbatim from the legacy gate() (feature 022)."""
    b_dry: list[str] = []
    return _kept(locals(), ('b_dry',))


def _seg_0363__b_1(
    *,
    M: Any = _UNBOUND,
    b: Any = _UNBOUND,
    b_crossed: Any = _UNBOUND,
    b_cw: Any = _UNBOUND,
    b_cx: Any = _UNBOUND,
    b_cy: Any = _UNBOUND,
    b_d: Any = _UNBOUND,
    b_dry: Any = _UNBOUND,
    b_floor: Any = _UNBOUND,
    b_ftpx: Any = _UNBOUND,
    b_hl: Any = _UNBOUND,
    b_hw: Any = _UNBOUND,
    b_pts: Any = _UNBOUND,
    b_short: Any = _UNBOUND,
    b_su: Any = _UNBOUND,
    b_sv: Any = _UNBOUND,
    b_th: Any = _UNBOUND,
    b_ux: Any = _UNBOUND,
    b_uy: Any = _UNBOUND,
    b_wid: Any = _UNBOUND,
    i: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 363 (b, b_crossed, b_cw, b_cx) - body verbatim from the legacy gate() (feature 022)."""
    for b in M.get("bridges", []):
        b_th = math.radians(b.get("rot", 0.0))
        b_ux, b_uy = math.cos(b_th), math.sin(b_th)
        b_hl, b_hw = b["span"] / 2, b["w"] / 2
        b_crossed: Any = None  # type: ignore[no-redef]
        b_cw = 0.0
        for b_pts, b_wid in bridge_crossed_waters(M):
            b_d = min(seg_dist(b["x"], b["y"], b_pts[i], b_pts[i + 1]) for i in range(len(b_pts) - 1))
            if b_d <= b_wid / 2 + 2 and b_wid > b_cw:
                b_crossed, b_cw = b_pts, b_wid
        if b_crossed is None:
            b_dry.append(f"({round(b['x'])},{round(b['y'])}) span {b['span']:.0f}")
            continue  # no water under the seat: bridges_seat_on_water fires below; the span rule has nothing to measure
        b_floor = (2.0 if b.get("foot") else 6.0) / b_ftpx
        for b_su, b_sv in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            b_cx = b["x"] + b_su * b_ux * b_hl - b_sv * b_uy * b_hw
            b_cy = b["y"] + b_su * b_uy * b_hl + b_sv * b_ux * b_hw
            if min(seg_dist(b_cx, b_cy, b_crossed[i], b_crossed[i + 1]) for i in range(len(b_crossed) - 1)) < b_cw / 2 + b_floor:
                b_short.append(f"({round(b['x'])},{round(b['y'])}) span {b['span']:.0f} on ~{b_cw:.0f}px water")
                break
    return _kept(locals(), ('b', 'b_crossed', 'b_cw', 'b_cx', 'b_cy', 'b_d', 'b_dry', 'b_floor', 'b_hl', 'b_hw', 'b_pts', 'b_short', 'b_su', 'b_sv', 'b_th', 'b_ux', 'b_uy', 'b_wid', 'i'))


# A DECK MUST SIT ON WATER AT ALL (settlement-review 2026-08-10): Shiro Daika's towpath
# plank kept its seat when the drain's re-route moved the ford, and it lay on bare bank for
# a whole feature - bridges_span_their_water silently skipped it (nothing to measure) and no
# other rule owned the case. A check that never runs looks exactly like a check that passes.
# BANK-PARALLEL WORKS FOLLOW THEIR BANK (GM 2026-08-10: "when we originally rendered the
# domain granaries and the imperial granary, they were aligned with the river. However, at
# a certain point, it looks like the angle of the river changed slightly, but the angle of
# the granaries did not"). A quay granary row is laid ALONG the water it loads from, and a
# jetty runs ACROSS it - both angles are properties of the bank, not constants, so a
# re-routed river must drag them or they read as a row built by someone who could not see
# the water. Same family as towpath_hugs_the_bank: derive the angle from the CURRENT
# polyline, never keep a rot that was right before the re-route.


def _seg_0364__bp_riv(*, M: Any = _UNBOUND, cn9: Any = _UNBOUND, w9: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 364 (bp_riv, cn9, w9) - body verbatim from the legacy gate() (feature 022)."""
    bp_riv = [w9["poly"] for w9 in M.get("streams", [])] + [cn9["poly"] for cn9 in M.get("canals", [])]
    return _kept(locals(), ('bp_riv', 'cn9', 'w9'))


def _seg_0365__waterside_works_follow_the_bank(
    *,
    M: Any = _UNBOUND,
    bp_bad: Any = _UNBOUND,
    bp_bear: Any = _UNBOUND,
    bp_bearing: Any = _UNBOUND,
    bp_d: Any = _UNBOUND,
    bp_f: Any = _UNBOUND,
    bp_key: Any = _UNBOUND,
    bp_off: Any = _UNBOUND,
    bp_riv: Any = _UNBOUND,
    bp_want: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d9: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    wp9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 365 (waterside_works_follow_the_bank) - body verbatim from the legacy gate() (feature 022)."""
    if bp_riv:

        def bp_bearing(px: float, py: float) -> tuple[float, float]:
            bp_best = (1e9, 0.0)
            for wp9 in bp_riv:
                for i9 in range(len(wp9) - 1):
                    d9 = seg_dist(px, py, wp9[i9], wp9[i9 + 1])
                    if d9 < bp_best[0]:
                        bp_best = (d9, math.degrees(math.atan2(wp9[i9 + 1][1] - wp9[i9][1], wp9[i9 + 1][0] - wp9[i9][0])))
            return bp_best

        bp_bad = []
        for bp_key, bp_want in (("granaries", 0.0), ("jetties", 90.0), ("tanning_yards", 0.0), ("dye_yards", 0.0)):  # rows and wash yards lie ALONG the bank; stages run ACROSS it
            for bp_f in M.get(bp_key, []):  # both keys hold records, never raw polygons
                bp_d, bp_bear = bp_bearing(bp_f["x"], bp_f["y"])
                if bp_d > 140:
                    continue  # not a waterside instance (an inland store is not bank-parallel)
                bp_off = abs((float(bp_f.get("rot", 0.0)) - bp_bear - bp_want) % 180.0)
                bp_off = min(bp_off, 180.0 - bp_off)
                if bp_off > 4.0:
                    bp_bad.append((bp_key, round(bp_f["x"]), round(bp_f["y"]), round(bp_off, 1)))
        check(
            "waterside_works_follow_the_bank",
            not bp_bad,
            f"waterside work(s) off their bank's angle (key, x, y, degrees off): {sorted(set(bp_bad))[:4]} - a quay granary row lies "
            f"ALONG the water and a jetty runs ACROSS it; recompute the rot from the CURRENT river polyline at that point (a bank "
            f"angle is derived geometry, not a constant that survives a re-route)",
        )
    return _kept(locals(), ('bp_bad', 'bp_bear', 'bp_bearing', 'bp_d', 'bp_f', 'bp_key', 'bp_off', 'bp_want'))


# A CAPTION SITS BY WHAT IT NAMES (GM 2026-08-10: "the aqueduct labels are no longer
# correctly placed - the settling basin one is not even really next to the actual feature,
# it is on top of the city walls, and the intake weir label is way far away from the actual
# thing it is labeling"). `labels_clear_of_other_buildings` stops a caption COVERING the
# wrong thing; nothing stopped one drifting away from the RIGHT thing. Point-feature
# captions (the water furniture, the works) are checked against the feature their text
# names, because those are the ones a standoff ladder can push far from their subject.


def _seg_0366__lb_named() -> dict[str, Any]:
    """Gate segment 366 (lb_named) - body verbatim from the legacy gate() (feature 022)."""
    lb_named: list[tuple[str, list[tuple[float, float]]]] = []
    return _kept(locals(), ('lb_named',))


def _seg_0367__a9(
    *,
    M: Any = _UNBOUND,
    a9: Any = _UNBOUND,
    f9: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    lb_key: Any = _UNBOUND,
    lb_named: Any = _UNBOUND,
    lb_pts: Any = _UNBOUND,
    lb_word: Any = _UNBOUND,
    p1_9: Any = _UNBOUND,
    p2_9: Any = _UNBOUND,
    t9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 367 (a9, f9, i9, lb_key) - body verbatim from the legacy gate() (feature 022)."""
    for lb_key, lb_word in (("sluice_gates", "sluice"), ("aqueducts", "aqueduct"), ("kilns", "kiln"), ("dye_yards", "dye"), ("tanning_yards", "tanning")):
        lb_pts = [(f9["x"], f9["y"]) for f9 in M.get(lb_key, []) if isinstance(f9, dict) and "x" in f9]
        if lb_key == "aqueducts":  # a LINE's caption may sit anywhere along it, so sample the run
            for a9 in M.get("aqueducts", []):
                for i9 in range(len(a9.get("poly", [])) - 1):
                    p1_9, p2_9 = a9["poly"][i9], a9["poly"][i9 + 1]
                    for t9 in range(0, 11):
                        lb_pts.append((p1_9[0] + (p2_9[0] - p1_9[0]) * t9 / 10, p1_9[1] + (p2_9[1] - p1_9[1]) * t9 / 10))
        if lb_pts:
            lb_named.append((lb_word, lb_pts))
    return _kept(locals(), ('a9', 'f9', 'i9', 'lb_key', 'lb_named', 'lb_pts', 'lb_word', 'p1_9', 'p2_9', 't9'))


def _seg_0368__captions_sit_by_their_feature(
    *,
    M: Any = _UNBOUND,
    check: Any = _UNBOUND,
    lb: Any = _UNBOUND,
    lb_bad: Any = _UNBOUND,
    lb_cx: Any = _UNBOUND,
    lb_cy: Any = _UNBOUND,
    lb_d: Any = _UNBOUND,
    lb_extra: Any = _UNBOUND,
    lb_named: Any = _UNBOUND,
    lb_pts: Any = _UNBOUND,
    lb_text: Any = _UNBOUND,
    lb_word: Any = _UNBOUND,
    px9: Any = _UNBOUND,
    py9: Any = _UNBOUND,
    w9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 368 (captions_sit_by_their_feature) - body verbatim from the legacy gate() (feature 022)."""
    if lb_named:
        lb_extra = {"aqueduct": ("intake", "weir", "basin", "settling")}
        lb_bad = []
        for lb in M.get("labels", []):
            if len(lb) < 6:
                continue  # legacy fixture labels predate the text field
            lb_text = str(lb[5]).lower()
            lb_cx, lb_cy = (float(lb[0]) + float(lb[2])) / 2, (float(lb[1]) + float(lb[3])) / 2
            for lb_word, lb_pts in lb_named:
                if lb_word in lb_text or any(w9 in lb_text for w9 in lb_extra.get(lb_word, ())):
                    lb_d = min(math.hypot(lb_cx - px9, lb_cy - py9) for px9, py9 in lb_pts)
                    if lb_d > 90:  # 270 real ft at city grain - past that a caption reads as naming its neighbor
                        lb_bad.append((str(lb[5]), round(lb_cx), round(lb_cy), round(lb_d)))
                    break
        check(
            "captions_sit_by_their_feature",
            not lb_bad,
            f"caption(s) far from the feature they name (text, x, y, px): {lb_bad[:3]} - a caption that has drifted off its subject "
            f"names whatever it lands on instead; give it an explicit label_xy at the feature, or shorten the standoff ladder",
        )
    return _kept(locals(), ('lb', 'lb_bad', 'lb_cx', 'lb_cy', 'lb_d', 'lb_extra', 'lb_pts', 'lb_text', 'lb_word', 'px9', 'py9', 'w9'))


# ...AND NOT ON THE RAMPART (GM 2026-08-10: the settling-basin caption "is on top of the
# city walls"). A caption laid across the wall or the moat reads as naming the defenses,
# and the wall's own ink swallows the text. The label battery protects FOOTPRINTS from
# captions; the wall is a polyline, so nothing covered it.


def _seg_0369__cd_lines() -> dict[str, Any]:
    """Gate segment 369 (cd_lines) - body verbatim from the legacy gate() (feature 022)."""
    cd_lines = []  # type: ignore[var-annotated]
    return _kept(locals(), ('cd_lines',))


def _seg_0370__cd_lines_1(*, M: Any = _UNBOUND, cd_lines: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 370 (cd_lines) - body verbatim from the legacy gate() (feature 022)."""
    if len(M.get("wall") or []) >= 3:
        cd_lines.append((list(M["wall"]) + [M["wall"][0]], 9.0))
    return _kept(locals(), ('cd_lines',))


def _seg_0371__cd_lines_2(*, M: Any = _UNBOUND, cd_lines: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 371 (cd_lines) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("moat"):
        cd_lines.append((list(M["moat"]) + [M["moat"][0]], float(M.get("moat_width", 22)) / 2))
    return _kept(locals(), ('cd_lines',))


def _seg_0372__captions_clear_of_the_defenses(
    *,
    M: Any = _UNBOUND,
    cd_bad: Any = _UNBOUND,
    cd_hit: Any = _UNBOUND,
    cd_hw: Any = _UNBOUND,
    cd_lines: Any = _UNBOUND,
    cd_pts: Any = _UNBOUND,
    cd_quad: Any = _UNBOUND,
    check: Any = _UNBOUND,
    e9: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    lb: Any = _UNBOUND,
    qx9: Any = _UNBOUND,
    qy9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 372 (captions_clear_of_the_defenses) - body verbatim from the legacy gate() (feature 022)."""
    if cd_lines:
        cd_bad = []
        for lb in M.get("labels", []):
            if len(lb) < 6:
                continue  # ...same legacy shape
            cd_quad = [(float(lb[0]), float(lb[1])), (float(lb[2]), float(lb[1])), (float(lb[2]), float(lb[3])), (float(lb[0]), float(lb[3]))]
            for cd_pts, cd_hw in cd_lines:
                # corners AND edges: a caption box wider than the wall's band straddles the line
                # with every corner clear of it, which a corner-only test calls fine (the same
                # point-vs-footprint trap the skill has paid for before)
                cd_hit = any(seg_dist(qx9, qy9, cd_pts[i9], cd_pts[i9 + 1]) < cd_hw for qx9, qy9 in cd_quad for i9 in range(len(cd_pts) - 1)) or any(
                    segments_cross(cd_quad[e9], cd_quad[(e9 + 1) % 4], cd_pts[i9], cd_pts[i9 + 1]) for e9 in range(4) for i9 in range(len(cd_pts) - 1)
                )
                if cd_hit:
                    cd_bad.append((str(lb[5]), round((float(lb[0]) + float(lb[2])) / 2), round((float(lb[1]) + float(lb[3])) / 2)))
                    break
        check(
            "captions_clear_of_the_defenses",
            not cd_bad,
            f"caption(s) lying across the wall or moat: {cd_bad[:3]} - the rampart's ink swallows the text and the caption reads as "
            f"naming the defenses; move the label off the wall band (label_xy), keeping it beside the feature it names",
        )
    return _kept(locals(), ('cd_bad', 'cd_hit', 'cd_hw', 'cd_pts', 'cd_quad', 'e9', 'i9', 'lb', 'qx9', 'qy9'))


# WORKER HOUSING SITS WITH THE WORK (GM 2026-08-10: "I would expect the housing for those
# facilities to be close to those businesses and granaries... since the whole point of those
# houses being outside the city instead of inside of it is that those are the housing for
# the workers who work those facilities"). An extramural dwelling exists BECAUSE something
# outside needs hands on it - the quay, the granaries, the gate market's inns and stables.
# A row across the channel from all of it is a suburb with no reason, and the ruling that
# allowed extramural housing at all (2026-08-10, the wharf hamlet) was granted on exactly
# that basis. Measured to the nearest workplace, not to the wall.


def _seg_0373__extramural_housing_serves_its_work(
    *,
    M: Any = _UNBOUND,
    URBAN: Any = _UNBOUND,
    b9: Any = _UNBOUND,
    check: Any = _UNBOUND,
    eh_bad: Any = _UNBOUND,
    eh_ftpx: Any = _UNBOUND,
    eh_reach: Any = _UNBOUND,
    eh_wall: Any = _UNBOUND,
    eh_work: Any = _UNBOUND,
    k9: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    s9: Any = _UNBOUND,
    w9: Any = _UNBOUND,
    wx9: Any = _UNBOUND,
    wy9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 373 (extramural_housing_serves_its_work) - body verbatim from the legacy gate() (feature 022)."""
    if URBAN and len(M.get("wall") or []) >= 3:
        eh_wall = M["wall"]
        eh_ftpx = float(meta.get("ftpx", 1) or 1)
        eh_work = [
            (w9["x"], w9["y"])
            for k9 in ("granaries", "jetties", "storehouses", "stables", "inns", "kilns", "dye_yards", "tanning_yards", "lumber_yards")
            for w9 in M.get(k9, [])
            if isinstance(w9, dict) and "x" in w9
        ]
        eh_work += [(s9["x"], s9["y"]) for s9 in M.get("buildings", []) if s9.get("kind") in ("shop", "merchant", "inn", "stables")]
        if eh_work:
            eh_reach = 400.0 / eh_ftpx
            eh_bad = []
            for b9 in M.get("buildings", []):
                if b9.get("kind") not in DWELLING_KINDS or point_in_poly(b9["x"], b9["y"], eh_wall):
                    continue
                if min(math.hypot(b9["x"] - wx9, b9["y"] - wy9) for wx9, wy9 in eh_work) > eh_reach:
                    eh_bad.append((round(b9["x"]), round(b9["y"])))
            check(
                "extramural_housing_serves_its_work",
                len(eh_bad) <= 2,
                f"{len(eh_bad)} extramural dwelling(s) more than 400 ft from any workplace, e.g. {sorted(set(eh_bad))[:3]} - housing outside "
                f"the wall exists to put hands next to the quay, the granaries or the gate market; move the rows to the works they serve "
                f"(or the households belong inside the wall)",
            )
    return _kept(locals(), ('b9', 'eh_bad', 'eh_ftpx', 'eh_reach', 'eh_wall', 'eh_work', 'k9', 's9', 'w9', 'wx9', 'wy9'))


# THE FUNERARY GROUND STARTS AT THE WALL AND RUNS OUTWARD (GM 2026-08-10, researched; the
# why and the sources are in research/cities/capitals.md "How far outside the wall does the
# funerary ground sit?"). Nothing in the record holds it far off: ritual pollution is a
# BINARY satisfied by being outside at all (Kyoto's Injo-ji stood ON the Odoi rampart and
# marked the boundary of the living), fire is worth 50 ft by code and was never a siting
# driver at all (Edo cremated on open pyres inside its own temple precincts for 250 years
# and moved them in 1873 for the STENCH), and what actually set the distance was worthless
# ground on the road out of the gate. In every attested case the complex's ENTRANCE is at or
# just past the wall and the field runs outward - so a compact feature at 900+ ft is drawing
# the FAR end of a historical site at its NEAR end, which is what made the capital's read
# unmotivated.


def _seg_0374__funerary_ground_within_reach(
    *,
    M: Any = _UNBOUND,
    URBAN: Any = _UNBOUND,
    c9: Any = _UNBOUND,
    check: Any = _UNBOUND,
    f9: Any = _UNBOUND,
    fg_bad: Any = _UNBOUND,
    fg_cem: Any = _UNBOUND,
    fg_crem: Any = _UNBOUND,
    fg_d: Any = _UNBOUND,
    fg_edge: Any = _UNBOUND,
    fg_f: Any = _UNBOUND,
    fg_ftpx: Any = _UNBOUND,
    fg_k: Any = _UNBOUND,
    fg_max: Any = _UNBOUND,
    fg_min: Any = _UNBOUND,
    fg_oss: Any = _UNBOUND,
    fg_out: Any = _UNBOUND,
    fg_sites: Any = _UNBOUND,
    fg_split: Any = _UNBOUND,
    fg_wall: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    k9: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 374 (funerary_complex_is_one_ground, funerary_ground_within_reach) - body verbatim from the legacy gate() (feature 022)."""
    if URBAN and len(M.get("wall") or []) >= 3:
        fg_wall = M["wall"]
        fg_ftpx = float(meta.get("ftpx", 1) or 1)
        fg_max = (900.0 / fg_ftpx) if scale == "capital" else 1e9  # GM 2026-08-10 scoped the cap to capitals; the provincial spread is recorded, not enforced
        fg_min = 150.0 / fg_ftpx
        fg_sites = [(k9, f9) for k9 in ("cemeteries", "cremation_grounds", "ossuaries") for f9 in M.get(k9, []) if isinstance(f9, dict) and "x" in f9]
        fg_out = [(k9, f9) for k9, f9 in fg_sites if not point_in_poly(f9["x"], f9["y"], fg_wall)]
        fg_bad = []
        for fg_k, fg_f in fg_out:
            fg_d = min(seg_dist(fg_f["x"], fg_f["y"], fg_wall[i9], fg_wall[(i9 + 1) % len(fg_wall)]) for i9 in range(len(fg_wall)))
            fg_edge = fg_d - max(float(fg_f.get("w", 0)), float(fg_f.get("h", 0))) / 2  # the NEAR edge, not the centre
            if fg_edge > fg_max or fg_edge < fg_min:
                fg_bad.append((fg_k, round(fg_f["x"]), round(fg_f["y"]), round(fg_edge * fg_ftpx)))
        check(
            "funerary_ground_within_reach",
            not fg_bad,
            f"funerary feature(s) at the wrong reach (key, x, y, ft from the wall; want {round(fg_min * fg_ftpx)}-{round(fg_max * fg_ftpx)}): {fg_bad[:4]} - "
            f"the complex BEGINS just past the wall on the road out of a gate and runs outward; nothing holds it further off "
            f"(pollution is satisfied by being outside at all, and a pyre's codified setback is 50 ft)",
        )
        # ...and the three sit as ONE complex: Edo's north gate held burial ground, crematory and
        # pauper mound within ~290 ft of each other, entered through one gate-temple.
        fg_crem = [f9 for k9, f9 in fg_out if k9 == "cremation_grounds"]
        fg_oss = [f9 for k9, f9 in fg_out if k9 == "ossuaries"]
        fg_cem = [f9 for k9, f9 in fg_out if k9 == "cemeteries"]
        if fg_crem and fg_cem:
            fg_split = []
            for fg_f in fg_crem + fg_oss:
                if min(math.hypot(fg_f["x"] - c9["x"], fg_f["y"] - c9["y"]) for c9 in fg_cem) > 600.0 / fg_ftpx:
                    fg_split.append((round(fg_f["x"]), round(fg_f["y"])))
            check(
                "funerary_complex_is_one_ground",
                not fg_split,
                f"crematory/ossuary standing apart from the burial ground it serves: {fg_split[:3]} - the three are ONE complex on one "
                f"outbound road (Kozukappara held all three within ~290 ft); draw them together with the marker temple at the near end",
            )
    return _kept(
        locals(), ('c9', 'f9', 'fg_bad', 'fg_cem', 'fg_crem', 'fg_d', 'fg_edge', 'fg_f', 'fg_ftpx', 'fg_k', 'fg_max', 'fg_min', 'fg_oss', 'fg_out', 'fg_sites', 'fg_split', 'fg_wall', 'i9', 'k9')
    )


# A STREET EARNS ITS LENGTH ON BOTH SIDES (GM 2026-08-10: "several city streets extend out
# into empty space with nothing on either side of them and also not leading to anywhere...
# this is essentially a road to nowhere check"). `city_streets_have_buildings` measures ONE
# side and excuses frontage onto claimed open ground, which is right for a street along a
# drill ground or a firebreak - but a long stretch bare on BOTH sides is a street nobody
# walks, and the GM accepts that placement order may lay one down before that is knowable,
# so the CHECK is the backstop. Claimed ground does not excuse this one: the point is that
# the street serves nothing, not that the ground beside it is spoken for.


def _seg_0375__city_streets_serve_both_sides(
    *,
    M: Any = _UNBOUND,
    URBAN: Any = _UNBOUND,
    a9: Any = _UNBOUND,
    b9: Any = _UNBOUND,
    b9p: Any = _UNBOUND,
    bs_bad: Any = _UNBOUND,
    bs_blds: Any = _UNBOUND,
    bs_grid: Any = _UNBOUND,
    bs_len: Any = _UNBOUND,
    bs_run: Any = _UNBOUND,
    bs_worst: Any = _UNBOUND,
    bx9: Any = _UNBOUND,
    by9: Any = _UNBOUND,
    check: Any = _UNBOUND,
    j9: Any = _UNBOUND,
    k9: Any = _UNBOUND,
    pts9: Any = _UNBOUND,
    st9: Any = _UNBOUND,
    t9: Any = _UNBOUND,
    x9: Any = _UNBOUND,
    y9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 375 (city_streets_serve_both_sides) - body verbatim from the legacy gate() (feature 022)."""
    if URBAN and M.get("town_streets"):
        bs_blds = [
            b9
            for k9 in (
                "buildings",
                "shops",
                "flophouses",
                "inns",
                "manors",
                "ministries",
                "religious",
                "storehouses",
                "bathhouses",
                "breweries",
                "stables",
                "kura",
                "precincts",
                "castles",
                "mausoleums",
                "granaries",
            )
            for b9 in M.get(k9, [])
            if isinstance(b9, dict) and "x" in b9
        ]
        bs_grid = GridIndex(120.0)
        for b9 in bs_blds:
            bs_grid.add(b9["x"] - 60, b9["y"] - 60, b9["x"] + 60, b9["y"] + 60, (b9["x"], b9["y"]))
        bs_bad = []
        for st9 in M["town_streets"]:
            pts9 = st9["pts"]
            bs_worst = bs_run = 0.0
            for j9 in range(len(pts9) - 1):
                a9, b9p = pts9[j9], pts9[j9 + 1]
                bs_len = math.hypot(b9p[0] - a9[0], b9p[1] - a9[1])
                for k9 in range(max(1, int(bs_len // 20)) + 1):
                    t9 = k9 / max(1, int(bs_len // 20))
                    x9, y9 = a9[0] + (b9p[0] - a9[0]) * t9, a9[1] + (b9p[1] - a9[1]) * t9
                    if any((bx9 - x9) ** 2 + (by9 - y9) ** 2 < 60 * 60 for bx9, by9 in bs_grid.near(x9, y9)):
                        bs_run = 0.0
                    else:
                        bs_run += 20.0
                        bs_worst = max(bs_worst, bs_run)
            if bs_worst >= 300:
                bs_bad.append((round(pts9[0][0]), round(pts9[0][1]), round(bs_worst)))
        check(
            "city_streets_serve_both_sides",
            not bs_bad,
            f"city street(s) with a long stretch bare on BOTH sides (start x, y, px): {bs_bad[:4]} - a street nobody fronts is a "
            f"road to nowhere; shorten it to the fabric it serves, or fill the block it opens (claimed open ground does not excuse "
            f"this one - the objection is that the street serves nothing)",
        )
    return _kept(locals(), ('a9', 'b9', 'b9p', 'bs_bad', 'bs_blds', 'bs_grid', 'bs_len', 'bs_run', 'bs_worst', 'bx9', 'by9', 'j9', 'k9', 'pts9', 'st9', 't9', 'x9', 'y9'))


# A SHOP FACES THE WAY IT FRONTS (GM 2026-08-10: "at the northern gate market there is a row
# of several merchant shops, and then just one of those shops is oriented facing away from
# the road"). A storefront IS its street face - the noren, the counter and the goods are on
# that side - so a shop within a frontage band of a way must open toward it. The glyph's
# front is local +y, as with the theater stage, so after `rot` it points (-sin, cos).
# Placement gets this right when it seats the file; what it cannot see is a LATER re-lay
# that moves the way, or a hand-placed file whose setback sign flips one seat.


def _seg_0376__r9(*, M: Any = _UNBOUND, r9: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 376 (r9, sf_ways) - body verbatim from the legacy gate() (feature 022)."""
    sf_ways = ([("road", M["road"], float(M.get("road_width", 26)))] if M.get("road") else []) + [
        ("road", r9["pts"] if isinstance(r9, dict) else r9, float(r9.get("w", 20)) if isinstance(r9, dict) else 20.0) for r9 in M.get("roads", [])
    ]
    return _kept(locals(), ('r9', 'sf_ways'))


def _seg_0377__s9(*, M: Any = _UNBOUND, s9: Any = _UNBOUND, sf_ways: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 377 (s9, sf_ways) - body verbatim from the legacy gate() (feature 022)."""
    sf_ways += [("street", s9["pts"], float(s9.get("w", 18))) for s9 in M.get("town_streets", [])]
    return _kept(locals(), ('s9', 'sf_ways'))


def _seg_0378__frontage_shops_face_their_way(
    *,
    M: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d9: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    sf_b: Any = _UNBOUND,
    sf_bad: Any = _UNBOUND,
    sf_best: Any = _UNBOUND,
    sf_cp: Any = _UNBOUND,
    sf_d: Any = _UNBOUND,
    sf_l: Any = _UNBOUND,
    sf_ox: Any = _UNBOUND,
    sf_oy: Any = _UNBOUND,
    sf_pts: Any = _UNBOUND,
    sf_th: Any = _UNBOUND,
    sf_vx: Any = _UNBOUND,
    sf_vy: Any = _UNBOUND,
    sf_w: Any = _UNBOUND,
    sf_ways: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 378 (frontage_shops_face_their_way) - body verbatim from the legacy gate() (feature 022)."""
    if sf_ways:
        sf_bad = []
        for sf_b in M.get("buildings", []) + M.get("shops", []):
            if not isinstance(sf_b, dict) or sf_b.get("kind") not in ("shop", "merchant"):
                continue
            sf_best = (1e9, (0.0, 0.0), 0.0)
            for _sf_kind, sf_pts, sf_w in sf_ways:
                for i9 in range(len(sf_pts) - 1):
                    d9 = seg_dist(sf_b["x"], sf_b["y"], sf_pts[i9], sf_pts[i9 + 1])
                    if d9 < sf_best[0]:
                        sf_best = (d9, seg_closest(sf_b["x"], sf_b["y"], sf_pts[i9], sf_pts[i9 + 1]), sf_w)
            sf_d, sf_cp, sf_w = sf_best
            if sf_d > sf_w / 2 + 40:
                continue  # not a frontage shop - an interior stall owes the way nothing
            sf_th = math.radians(float(sf_b.get("rot", 0.0)))
            sf_ox, sf_oy = -math.sin(sf_th), math.cos(sf_th)
            sf_vx, sf_vy = sf_cp[0] - sf_b["x"], sf_cp[1] - sf_b["y"]
            sf_l = math.hypot(sf_vx, sf_vy) or 1.0
            if (sf_ox * sf_vx + sf_oy * sf_vy) / sf_l < -0.3:
                sf_bad.append((round(sf_b["x"]), round(sf_b["y"])))
        check(
            "frontage_shops_face_their_way",
            not sf_bad,
            f"shop(s) turned away from the way they front (x, y): {sorted(set(sf_bad))[:4]} - a storefront IS its street face "
            f"(noren, counter, goods); flip the seat's rot by 180 deg, or move the shop off the frontage band if it is meant to be an interior stall",
        )
    return _kept(locals(), ('_sf_kind', 'd9', 'i9', 'sf_b', 'sf_bad', 'sf_best', 'sf_cp', 'sf_d', 'sf_l', 'sf_ox', 'sf_oy', 'sf_pts', 'sf_th', 'sf_vx', 'sf_vy', 'sf_w'))


# A SLUICE GATE SITS ON ITS CHANNEL'S CENTERLINE (GM 2026-08-10, after the same defect
# recurred across several re-lays: "the northern sluice gate is still misaligned with the
# irrigated channel that it is gating... I know we have automated checks for this, so I'm
# not sure how this keeps happening over and over again"). It kept happening because
# `sluice_gates_on_water` measures to the BANK: a gate 15.8px from the centerline of a 22px
# channel sits 4.8px past the bank, inside that rule's 6px tolerance, and passed - while
# reading as a frame floating beside the water. A sluice's frame spans BANK TO BANK, so the
# only correct seat is the centerline itself. Tolerance is a fraction of the channel's own
# half-width (a wide river's gate may sit a little off; a narrow ditch's may not) with a
# small absolute floor for the linework.


def _seg_0379__cn9(*, M: Any = _UNBOUND, cn9: Any = _UNBOUND, w9: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 379 (cn9, sc_waters, w9) - body verbatim from the legacy gate() (feature 022)."""
    sc_waters = [(w9["poly"], float(w9.get("w", 9))) for w9 in M.get("streams", [])] + [(cn9["poly"], float(cn9.get("w", 12))) for cn9 in M.get("canals", [])]
    return _kept(locals(), ('cn9', 'sc_waters', 'w9'))


def _seg_0380__ch9(*, M: Any = _UNBOUND, ch9: Any = _UNBOUND, sc_waters: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 380 (ch9, sc_waters) - body verbatim from the legacy gate() (feature 022)."""
    sc_waters += [(ch9["poly"], float(ch9.get("w", 2.5))) for ch9 in M.get("channels", []) if ch9.get("poly")]
    return _kept(locals(), ('ch9', 'sc_waters'))


def _seg_0381__sc_waters(*, M: Any = _UNBOUND, sc_waters: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 381 (sc_waters) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("moat"):
        sc_waters.append((list(M["moat"]) + [M["moat"][0]], float(M.get("moat_width", 22))))
    return _kept(locals(), ('sc_waters',))


def _seg_0382__sluice_gates_centered_on_their_channel(
    *,
    M: Any = _UNBOUND,
    check: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    sc_bad: Any = _UNBOUND,
    sc_best: Any = _UNBOUND,
    sc_d: Any = _UNBOUND,
    sc_w: Any = _UNBOUND,
    sc_waters: Any = _UNBOUND,
    sg9: Any = _UNBOUND,
    wp9: Any = _UNBOUND,
    ww9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 382 (sluice_gates_centered_on_their_channel) - body verbatim from the legacy gate() (feature 022)."""
    if sc_waters and M.get("sluice_gates"):
        sc_bad = []
        for sg9 in M["sluice_gates"]:
            sc_best = min((min(seg_dist(sg9["x"], sg9["y"], wp9[i9], wp9[i9 + 1]) for i9 in range(len(wp9) - 1)), ww9) for wp9, ww9 in sc_waters)
            sc_d, sc_w = sc_best
            if sc_d > max(3.0, sc_w * 0.3):
                sc_bad.append((round(sg9["x"]), round(sg9["y"]), round(sc_d, 1)))
        check(
            "sluice_gates_centered_on_their_channel",
            not sc_bad,
            f"sluice gate(s) off their channel's CENTERLINE (x, y, px off): {sc_bad[:4]} - the frame spans bank to bank, so the "
            f"gate's center belongs ON the centerline; snap it to the nearest point of the watercourse polyline (being merely "
            f"inside the water's band is what let this recur - sluice_gates_on_water measures to the bank)",
        )
    return _kept(locals(), ('i9', 'sc_bad', 'sc_best', 'sc_d', 'sc_w', 'sg9', 'wp9', 'ww9'))


# A ROAD DOES NOT SIMPLY STOP (GM 2026-08-10: "the road leading to the southwest gate comes a
# little way into the city and then just stops... we expect that caravans coming into the city
# would need to be able to take this road in order to reach the castle keep"). A trunk road
# exists to carry traffic THROUGH: each end must leave the map, meet another road, or join a
# street/ring bed a wagon can turn onto. An end that dies in open ground is a road to nowhere.


def _seg_0383__roads_join_the_network(
    *,
    M: Any = _UNBOUND,
    b9: Any = _UNBOUND,
    bh9: Any = _UNBOUND,
    cg9: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cs9: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    j9: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    o9: Any = _UNBOUND,
    r9: Any = _UNBOUND,
    rj_E: Any = _UNBOUND,
    rj_H: Any = _UNBOUND,
    rj_W: Any = _UNBOUND,
    rj_bad: Any = _UNBOUND,
    rj_beds: Any = _UNBOUND,
    rj_i: Any = _UNBOUND,
    rj_pts: Any = _UNBOUND,
    rj_ways: Any = _UNBOUND,
    s9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 383 (roads_join_the_network) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("roads") or M.get("road"):
        rj_ways = [r9["pts"] if isinstance(r9, dict) else r9 for r9 in M.get("roads", [])] + ([M["road"]] if M.get("road") else [])
        rj_beds = [(s9["pts"], float(s9.get("w", 18)) / 2) for s9 in M.get("town_streets", [])]
        if M.get("ring_road"):
            rj_beds.append((list(M["ring_road"]) + [M["ring_road"][0]], float(M.get("ring_road_width", 15)) / 2))
        rj_W, rj_H = float(meta.get("W", 1820)), float(meta.get("H", 1180))
        rj_bad = []
        for rj_i, rj_pts in enumerate(rj_ways):
            if len(rj_pts) < 2:
                continue
            for rj_E in (rj_pts[0], rj_pts[-1]):
                if rj_E[0] <= 8 or rj_E[1] <= 8 or rj_E[0] >= rj_W - 8 or rj_E[1] >= rj_H - 8:
                    continue  # leaves the map
                if any(min(seg_dist(rj_E[0], rj_E[1], o9[i9], o9[i9 + 1]) for i9 in range(len(o9) - 1)) <= 20 for j9, o9 in enumerate(rj_ways) if j9 != rj_i and len(o9) >= 2):
                    continue  # meets another road
                if any(min(seg_dist(rj_E[0], rj_E[1], b9[i9], b9[i9 + 1]) for i9 in range(len(b9) - 1)) <= bh9 + 14 for b9, bh9 in rj_beds if len(b9) >= 2):
                    continue  # joins a street or the ring
                # ...and a castle approach legitimately ENDS at the gate it serves: the ote-suji
                # stops at the ote-mon and the karamete road at the postern tower, exactly as a
                # real approach does. That is a terminus with a reason, not a road to nowhere.
                if any(
                    math.hypot(rj_E[0] - cg9[0], rj_E[1] - cg9[1]) <= 60 for cs9 in M.get("castles", []) for cg9 in (list(cs9.get("gates") or []) + ([cs9["karamete"]] if cs9.get("karamete") else []))
                ):
                    continue
                rj_bad.append((round(rj_E[0]), round(rj_E[1])))
        check(
            "roads_join_the_network",
            not rj_bad,
            f"road end(s) stopping in open ground (x, y): {sorted(set(rj_bad))[:4]} - a trunk road carries traffic THROUGH: run it "
            f"off the map, into another road, or onto a street/ring bed a wagon can turn from (a gate road must reach the network "
            f"that serves the castle and the markets)",
        )
    return _kept(locals(), ('b9', 'bh9', 'cg9', 'cs9', 'i9', 'j9', 'o9', 'r9', 'rj_E', 'rj_H', 'rj_W', 'rj_bad', 'rj_beds', 'rj_i', 'rj_pts', 'rj_ways', 's9'))


# NO WAY STANDS IN WATER WITHOUT A DECK (GM 2026-08-10: "roads should not overlap with water
# without a bridge present"). `roads_bridge_water` already demands a deck wherever a CARRIED
# way's centerline CROSSES a watercourse's centerline - but it reads only the ways
# bridge_carried_ways names (the trunk roads, streets and the ring), and it tests crossings
# rather than OVERLAP. So an alley whose bed laps a stream's bed, or a way that runs into the
# water and stops, sails past it: the capital's wharf shore path lay in the moat drain for
# 40 px with no plank. This one samples EVERY drawn way against every watercourse using both
# BEDS' widths - the question a reader asks of the picture is whether the paving and the water
# occupy the same ground, not whether two abstract centerlines intersect.


def _seg_0384__cn9_1(*, M: Any = _UNBOUND, cn9: Any = _UNBOUND, w9: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 384 (cn9, w9, wd_waters) - body verbatim from the legacy gate() (feature 022)."""
    wd_waters = [(w9["poly"], float(w9.get("w", 9))) for w9 in M.get("streams", [])] + [(cn9["poly"], float(cn9.get("w", 12))) for cn9 in M.get("canals", [])]
    return _kept(locals(), ('cn9', 'w9', 'wd_waters'))


def _seg_0385__wd_waters(*, M: Any = _UNBOUND, wd_waters: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 385 (wd_waters) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("moat"):
        wd_waters.append((list(M["moat"]) + [M["moat"][0]], float(M.get("moat_width", 22))))
    return _kept(locals(), ('wd_waters',))


def _seg_0386__cs9(*, M: Any = _UNBOUND, cs9: Any = _UNBOUND, wd_waters: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 386 (cs9, wd_waters) - body verbatim from the legacy gate() (feature 022)."""
    for cs9 in M.get("castles", []):
        if cs9.get("moat"):
            wd_waters.append((list(cs9["moat"]) + [cs9["moat"][0]], float(cs9.get("moat_width", 22))))
    return _kept(locals(), ('cs9', 'wd_waters'))
