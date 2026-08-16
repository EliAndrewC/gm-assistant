"""Gate segments (city battery b) - bodies verbatim from check_village.py (feature 024 package split; registry order preserved)."""

import math
from typing import Any

from settlement import sat_overlap

from .common_01_geometry import (
    CLAN_FORTUNES,
    TEMPLE_EXCEPTIONS,
    Poly,
    _struct_rect,
    edge_gap,
    point_in_poly,
    rect_corners,
    seg_closest,
    seg_dist,
    seg_intersect,
    segments_cross,
    solid_structs,
    unit_dir,
)
from .common_02_overlap_policy import _ward_interior, check_ring_road_clear, edge_dist, footprint_on_line, kido_quads
from .common_03_capacity import _UNBOUND, _kept


def _seg_0563_126__gf_hit_1(
    *, _gfurn: Any = _UNBOUND, _gtowers: Any = _UNBOUND, gf_hit: Any = _UNBOUND, meta: Any = _UNBOUND, o: Any = _UNBOUND, scale: Any = _UNBOUND, t: Any = _UNBOUND, tc: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.126 (gf_hit, o, t, tc) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for t in _gtowers:
            tc = rect_corners({"x": t["x"], "y": t["y"], "w": t["w"], "h": t.get("h", t["w"]), "rot": t.get("rot", 0)})
            for o in _gfurn:
                if sat_overlap(tc, rect_corners({"x": o["x"], "y": o["y"], "w": o["w"], "h": o.get("h", o["w"]), "rot": o.get("rot", 0)})):
                    gf_hit.append((round(t["x"]), round(t["y"])))
                    break
    return _kept(locals(), ('gf_hit', 'o', 't', 'tc'))


def _seg_0563_127__city_gate_towers_clear_of_gate_furniture(*, check: Any = _UNBOUND, gf_hit: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.127 (city_gate_towers_clear_of_gate_furniture) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_gate_towers_clear_of_gate_furniture",
            not gf_hit,
            f"guard tower(s) overlapping an inspection station or gate house: {sorted(set(gf_hit))[:4]} - the gate "
            f"complex packs tight but each footprint sits CLEAR; move the tower (or the furniture) so they abut, not stack",
        )
    return _kept(locals(), ())


# ... and clear of the HOUSING: the kido + its guard box occupy a fixed crossing that the
# packs cannot see (s.ward draws long after the quarters are built), so the gen must
# RESERVE each gate's ground (block_polys) before any pack runs - else a row house lands
# under the guard box (GM, 2026-07: caught twice, on both fence-end gates)


def _seg_0563_128__kb_hit(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.128 (kb_hit) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        kb_hit = []  # type: ignore[var-annotated]
    return _kept(locals(), ('kb_hit',))


def _seg_0563_129__it(
    *, M: Any = _UNBOUND, it: Any = _UNBOUND, kb_hit: Any = _UNBOUND, kc: Any = _UNBOUND, kd: Any = _UNBOUND, key_: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.129 (it, kb_hit, kc, kd) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for kd in M.get("kido", []):
            for kc in kido_quads(kd):
                if any(
                    sat_overlap(kc, rect_corners({"x": it["x"], "y": it["y"], "w": it.get("w", 20), "h": it.get("h", 14), "rot": it.get("rot", 0)}))
                    for key_ in ("buildings", "houses", "flophouses", "storehouses")
                    for it in M.get(key_, []) or []
                ):
                    kb_hit.append((round(kd["x"]), round(kd["y"])))
                    break
    return _kept(locals(), ('it', 'kb_hit', 'kc', 'kd', 'key_'))


def _seg_0563_130__kido_clear_of_buildings(*, check: Any = _UNBOUND, kb_hit: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.130 (kido_clear_of_buildings) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "kido_clear_of_buildings",
            not kb_hit,
            f"ward gate(s) overlapping a building: {sorted(set(kb_hit))[:4]} - the kido and its guard box hold "
            f"their crossing; reserve the gate's ground before the packs run (block_polys around each kido spot)",
        )
    return _kept(locals(), ())


# a walled city has a RING ROAD (順城街) just inside the rampart - the wall-clear patrol zone a
# fortified city keeps for moving troops along the wall; the quarters pack INSIDE it (s.ring_road
# returns the loop to use as s.bound).


def _seg_0563_131__ring_rd(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.131 (ring_rd) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        ring_rd: Any = M.get("ring_road")  # type: ignore[no-redef,unused-ignore]
    return _kept(locals(), ('ring_rd',))


def _seg_0563_132__city_has_ring_road(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, ring_rd: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.132 (city_has_ring_road) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_has_ring_road",
            bool(ring_rd) and len(ring_rd) >= 4,
            "a walled city needs a ring road just inside the wall (the wall-clear patrol zone) - s.ring_road(WALL); set s.bound to the loop it returns",
        )
    return _kept(locals(), ())


# a street running toward a THROUGH-LANE (the Imperial road or the ring road) must MEET it
# cleanly at a T-junction: its bed reaches the lane's bed and ENDS there - neither a sliver
# SHORT of it (an undershoot, the street appears to dead-end in open ground) nor a sliver
# PAST it (an overshoot, the street pokes through to the far side instead of stopping at the
# junction). A genuine crossroads, where the street truly continues well past the lane, is
# fine - only a short stub poking through is wrong. (The ring road is gated where it crosses
# the ward fence, so even the government quarter's lanes may give onto it without un-sealing.)


def _seg_0563_133__through(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.133 (through) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        through = []  # type: ignore[var-annotated]
    return _kept(locals(), ('through',))


def _seg_0563_134__through_1(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, through: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.134 (through) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and M.get("road"):
        through.append((M["road"], (M.get("road_width", 26) - 8) / 2))
    return _kept(locals(), ('through',))


def _seg_0563_135__through_2(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, ring_rd: Any = _UNBOUND, scale: Any = _UNBOUND, through: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.135 (through) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and ring_rd:
        through.append((ring_rd, (M.get("ring_road_width", 15) - 6) / 2))
    return _kept(locals(), ('through',))


def _seg_0563_136__bad_meet(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.136 (bad_meet) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        bad_meet = []  # type: ignore[var-annotated]
    return _kept(locals(), ('bad_meet',))


# streets AND alleys: a gravel alley that runs straight at a through-lane and stops a sliver
# short of it (the laborer warren's east lane stopping just shy of the east ring road) should
# reach it too, just like a paved street


def _seg_0563_137__a(*, M: Any = _UNBOUND, a: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.137 (a, meeting_lanes, st) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        meeting_lanes = [(st["pts"], st.get("w", 18) / 2) for st in M.get("town_streets", [])] + [(a["pts"], 5.0) for a in M.get("alleys", [])]
    return _kept(locals(), ('a', 'meeting_lanes', 'st'))


def _seg_0563_138__E(
    *,
    E: Any = _UNBOUND,
    L: Any = _UNBOUND,
    align: Any = _UNBOUND,
    bad_meet: Any = _UNBOUND,
    bedhalf: Any = _UNBOUND,
    c: Any = _UNBOUND,
    cp: Any = _UNBOUND,
    dl: Any = _UNBOUND,
    gap: Any = _UNBOUND,
    i: Any = _UNBOUND,
    ip: Any = _UNBOUND,
    meeting_lanes: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    nb: Any = _UNBOUND,
    pts: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    sh: Any = _UNBOUND,
    through: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.138 (E, L, align, bad_meet) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for pts, sh in meeting_lanes:
            for E, nb in ((pts[0], pts[1]), (pts[-1], pts[-2])):
                for L, bedhalf in through:
                    cp = min((seg_closest(E[0], E[1], L[i], L[i + 1]) for i in range(len(L) - 1)), key=lambda c: math.hypot(E[0] - c[0], E[1] - c[1]))
                    gap = math.hypot(E[0] - cp[0], E[1] - cp[1])
                    if gap > 46:
                        continue
                    ip = next((seg_intersect(nb, E, L[i], L[i + 1]) for i in range(len(L) - 1) if segments_cross(nb, E, L[i], L[i + 1])), None)
                    if ip is not None:  # crosses the lane: must END at the junction, not poke a stub past it
                        if 3 < math.hypot(E[0] - ip[0], E[1] - ip[1]) < 50:
                            bad_meet.append((round(E[0]), round(E[1])))
                    else:  # short of the lane: its bed must reach the lane's bed
                        dl = math.hypot(E[0] - nb[0], E[1] - nb[1]) or 1.0
                        align = ((E[0] - nb[0]) / dl) * ((cp[0] - E[0]) / max(gap, 1e-6)) + ((E[1] - nb[1]) / dl) * ((cp[1] - E[1]) / max(gap, 1e-6))
                        if align > 0.6 and gap >= sh + bedhalf:
                            bad_meet.append((round(E[0]), round(E[1])))
    return _kept(locals(), ('E', 'L', 'align', 'bad_meet', 'bedhalf', 'cp', 'dl', 'gap', 'i', 'ip', 'nb', 'pts', 'sh'))


def _seg_0563_139__city_streets_meet_through_lanes(*, bad_meet: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.139 (city_streets_meet_through_lanes) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_streets_meet_through_lanes",
            not bad_meet,
            f"street/alley(s) not meeting the Imperial road / ring road cleanly at a junction - stopping a sliver short of it or poking a sliver past it: {sorted(set(bad_meet))}",
        )
    return _kept(locals(), ())


# the RING ROAD is a CLEAR patrol road: it must run clear of EVERY solid footprint and of
# fields. The gate guard houses / inspection stations / towers DO sit along it (wall
# furniture - `gate_structs` and `wall_towers` are overlap TARGETS and EXEMPT respectively,
# so the registry leaves them out), and a ward fence may cross it - but only at a gated kido
# (enforced by city_samurai_ward_sealed, which has the ring road in its netlines). Overlap =
# the ring's BED passes through a footprint.
#
# READS THE REGISTRY, NOT A HAND LIST (GM 2026-07-25). This check used to name its own eight
# keys, so every new feature had to be remembered into it - and the martial hall, correctly
# classified and correctly cleared of all thirteen no_structure_on_* hazards, sat squarely on
# Tango's ring road with the gate green because nobody had. See solid_structs' docstring.


def _seg_0563_140__ring_road_kept_clear(
    *,
    M: Any = _UNBOUND,
    _foot: Any = _UNBOUND,
    check: Any = _UNBOUND,
    grave_on_ring: Any = _UNBOUND,
    it: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    rect_corners_xywh: Any = _UNBOUND,
    rhalf: Any = _UNBOUND,
    ring_rd: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.140 (city_graveyard_clear_of_ring_road, ring_road_kept_clear) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and ring_rd:

        def _foot(it: dict[str, Any]) -> list[tuple[float, float]]:
            return rect_corners(it) if "rot" in it else rect_corners_xywh(it, 0)

        # ...except an official NOTICE BOARD inside a GATE PRECINCT. A kosatsuba is street
        # furniture, not a compound: a ~12x5 ft post-and-roof board that must stand within ~60
        # real ft of a road where people pass (kosatsuba_by_the_road), which at a gate means the
        # same crowded verge the guard house, inspection station and towers already line. Scoped
        # to the precinct on purpose - a board out on an open stretch of patrol lane is still a
        # defect. Radius matches the barbican keep-out city_wall_tower_coverage uses.
        check_ring_road_clear(M, check)  # factored to module level so the CAPITAL scope runs it too (GM 2026-08-09)
        # ...and the BURIAL grounds keep off the ring road's FULL drawn width (GM, 2026-07-23:
        # Tango's two intramural graveyards sat squarely ON the drawn ring road and the gate
        # waved them through). WHY a second, stricter check: ring_road_kept_clear's bed is
        # (width - 6) / 2 - a fixed ~3px-per-side eaves forgiveness, sized for the default 15px
        # ring. At city scale (1px = 3ft) the ring road is a ~20ft lane = ~6.7px, so that
        # forgiveness swallows nearly the whole bed and only a dead-center footprint could fire.
        # A burial ground has no eaves to forgive - its fence line IS its footprint, and graves
        # spilling onto the patrol road read as a plain collision - so it clears the full
        # half-width, no tolerance.
        rhalf = M.get("ring_road_width", 15) / 2
        grave_on_ring = [
            (round(it["x"]), round(it["y"]))
            for it in M.get("cemeteries", []) + M.get("mausoleums", []) + M.get("cremation_grounds", []) + M.get("ossuaries", [])
            if footprint_on_line(_foot(it), ring_rd, rhalf)
        ]
        check(
            "city_graveyard_clear_of_ring_road",
            not grave_on_ring,
            f"burial ground(s) overlapping the drawn ring road: {grave_on_ring[:4]} - graves do not encroach "
            f"on the patrol road at all (no eaves forgiveness on a fence line); shift the ground clear of the ring's full width",
        )
    return _kept(locals(), ('_foot', 'grave_on_ring', 'it', 'rhalf'))


def _seg_0563_141__b_7(*, M: Any = _UNBOUND, b: Any = _UNBOUND, inwall: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.141 (b, buraku_in) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        buraku_in = [b for b in M.get("buildings", []) if b.get("kind") == "burakumin" and inwall(b["x"], b["y"])]
    return _kept(locals(), ('b', 'buraku_in'))


# WHY (a walled city cannot do without burakumin labor during a siege, so some live inside): settlements.md "Historical grounding"


def _seg_0563_142__walled_city_has_burakumin_inside(*, buraku_in: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.142 (walled_city_has_burakumin_inside) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "walled_city_has_burakumin_inside",
            len(buraku_in) >= 3,
            f"{len(buraku_in)} burakumin inside the walls - a walled provincial city must keep >= 1 burakumin neighborhood within (they cannot be without burakumin during a siege)",
        )
    return _kept(locals(), ())


def _seg_0563_143__est_out(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, mn: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.143 (est_out, mn) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        est_out = [mn for mn in M.get("manors", []) if len(w) >= 3 and not point_in_poly(mn["x"], mn["y"], w)]
    return _kept(locals(), ('est_out', 'mn'))


def _seg_0563_144__city_samurai_estates_outside(*, URBAN: Any = _UNBOUND, check: Any = _UNBOUND, est_out: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.144 (city_samurai_estates_outside) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):  # noqa: SIM102
            if URBAN:  # CAPITAL-INVERTED (021): the capital's walled yashiki stand IN-WALL (020 doctrine) and its country cohort is detached houses, not 1-3 dispersed estates
                check(
                    "city_samurai_estates_outside",
                    1 <= len(est_out) <= 3,
                    f"{len(est_out)} walled samurai estates shown outside the walls, expected 1-3 - a provincial city's country estates are DISPERSED across the rural district (each an isolated fortified compound by its own land, miles out); a city map shows only the nearest 1-3 at the frame edge, the rest off-map (NOT a cluster of 5+ ringing the moat)",
                )
    return _kept(locals(), ())


# ... and the shown estates are DISPERSED, not a tight cluster: each is its own walled compound
# on its own landholding with fields between, so no two sit adjacent. A packed clump at one
# stretch of wall is the COMMERCIAL SUBURB's density, not the genteel country-estate pattern -
# gentry estates scatter by land/scenery, they do not ring the moat (GM 2026-07-22, researched:
# China-first absentee-landlord + dispersed-fortified-manor pattern, Japan agreeing). See settlements.md.


def _seg_0563_145__est_pts(*, est_out: Any = _UNBOUND, meta: Any = _UNBOUND, mn: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.145 (est_pts, mn) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        est_pts = [(mn["x"], mn["y"]) for mn in est_out]
    return _kept(locals(), ('est_pts', 'mn'))


def _seg_0563_146__EST_MIN_SEP(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.146 (EST_MIN_SEP) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        EST_MIN_SEP = 200
    return _kept(locals(), ('EST_MIN_SEP',))


def _seg_0563_147__est_too_close(*, EST_MIN_SEP: Any = _UNBOUND, est_pts: Any = _UNBOUND, i: Any = _UNBOUND, j: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.147 (est_too_close, i, j) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        est_too_close = [
            (round(est_pts[i][0]), round(est_pts[i][1]))
            for i in range(len(est_pts))
            for j in range(i + 1, len(est_pts))
            if math.hypot(est_pts[i][0] - est_pts[j][0], est_pts[i][1] - est_pts[j][1]) < EST_MIN_SEP
        ]
    return _kept(locals(), ('est_too_close', 'i', 'j'))


def _seg_0563_148__city_samurai_estates_dispersed(*, EST_MIN_SEP: Any = _UNBOUND, check: Any = _UNBOUND, est_too_close: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.148 (city_samurai_estates_dispersed) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):
            check(
                "city_samurai_estates_dispersed",
                not est_too_close,
                f"samurai estate(s) packed too close together {sorted(set(est_too_close))} - the country estates are separate compounds each on its own land, spread >= {EST_MIN_SEP}px apart, not a cluster ringing the moat (the dense belt hugging the wall is the commercial suburb, not estates)",
            )
    return _kept(locals(), ())


# WHY (the extramural samurai residence is the walled, defensible country ESTATE; a lone
# UNWALLED samurai house beyond the rampart is defenseless and belongs in the sealed ward
# inside): settlements.md "Historical grounding". Hard-zero - the estates rule above is
# exactly why the commoner inside-walls check exempts samurai, so this closes that gap
# (validated instance: Tango's SE top_up sweep leaked 14 houses into the moat berm, 2026-07-20).


def _seg_0563_149__b_8(*, M: Any = _UNBOUND, b: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.149 (b, sam_out) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        sam_out = [(round(b["x"]), round(b["y"])) for b in M.get("buildings", []) if b.get("kind") in ("samurai", "samurai_large") and len(w) >= 3 and not point_in_poly(b["x"], b["y"], w)]
    return _kept(locals(), ('b', 'sam_out'))


def _seg_0563_150__city_samurai_houses_inside_walls(*, URBAN: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, sam_out: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.150 (city_samurai_houses_inside_walls) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):  # noqa: SIM102
        if URBAN:  # CAPITAL-INVERTED (021): CAPITAL_SAMURAI_INWALL_FRAC deliberately keeps ~15% of the cohort in country seats on the approaches
            check(
                "city_samurai_houses_inside_walls",
                not sam_out,
                f"{len(sam_out)} free-standing samurai house(s) sit OUTSIDE the walls {sorted(set(sam_out))[:5]} - in-city "
                f"samurai live unwalled INSIDE the sealed ward; the only extramural samurai residences are the walled "
                f"country estates (s.manor). Re-seat these houses in the samurai quarter.",
            )
    return _kept(locals(), ())


def _seg_0563_151__areas(*, est_out: Any = _UNBOUND, meta: Any = _UNBOUND, mn: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.151 (areas, mn) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        areas = sorted((mn["w"] * mn["h"]) for mn in est_out)
    return _kept(locals(), ('areas', 'mn'))


def _seg_0563_152__city_samurai_estates_vary_in_size(*, areas: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.152 (city_samurai_estates_vary_in_size) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_samurai_estates_vary_in_size",
            len(areas) < 2 or areas[-1] >= 1.5 * areas[0],
            "the samurai estates should vary in size (some larger than others) - largest area >= 1.5x the smallest",
        )
    return _kept(locals(), ())


# scattered country estates each front their OWN approach lane (not drawn at this scale), so
# their depicted (formal) gates do NOT all open the same way - a uniform direction is the
# unconsidered default. The formal gate favours the auspicious south; others face the cityward
# approach (the cityward service gate, like the governor's, is omitted at this scale).


def _seg_0563_153__egd(*, est_out: Any = _UNBOUND, meta: Any = _UNBOUND, mn: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.153 (egd, mn) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        egd = [mn.get("gate_dir") for mn in est_out]
    return _kept(locals(), ('egd', 'mn'))


def _seg_0563_154__city_estate_gates_vary(*, check: Any = _UNBOUND, egd: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.154 (city_estate_gates_vary) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_estate_gates_vary",
            len(egd) < 3 or len(set(egd)) >= 2,
            f"all {len(egd)} country estate gates open the same way ({egd[0] if egd else None}) - scattered estates each front their own approach, so vary the gate_dir (some south, some cityward)",
        )
    return _kept(locals(), ())


def _seg_0563_155__moat(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.155 (moat) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        moat: Any = M.get("moat")  # type: ignore[no-redef,unused-ignore]
    return _kept(locals(), ('moat',))


# all city temples INSIDE the walls, and clear of the wall stroke and the moat


def _seg_0563_156__rel(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.156 (rel) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        rel = M.get("religious", [])
    return _kept(locals(), ('rel',))


def _seg_0563_157__out_rel(*, inwall: Any = _UNBOUND, meta: Any = _UNBOUND, r: Any = _UNBOUND, rel: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.157 (out_rel, r) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        out_rel = [r.get("label") for r in rel if not inwall(r["x"], r["y"])]
    return _kept(locals(), ('out_rel', 'r'))


def _seg_0563_158__city_temples_inside_walls(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, out_rel: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.158 (city_temples_inside_walls) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_temples_inside_walls", not out_rel, f"temple(s) outside the city walls (all of a city's temples belong inside): {out_rel}")
    return _kept(locals(), ())


def _seg_0563_159__r(
    *, meta: Any = _UNBOUND, moat: Any = _UNBOUND, r: Any = _UNBOUND, rect_corners_xywh: Any = _UNBOUND, rel: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.159 (r, rel_bad) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        rel_bad = [r.get("label") for r in rel if footprint_on_line(rect_corners_xywh(r, 0), w, 9) or (moat and footprint_on_line(rect_corners_xywh(r, 0), moat, 13))]
    return _kept(locals(), ('r', 'rel_bad'))


def _seg_0563_160__city_temples_clear_of_wall_moat(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, rel_bad: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.160 (city_temples_clear_of_wall_moat) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_temples_clear_of_wall_moat", not rel_bad, f"temple(s) overlapping the wall or moat: {rel_bad}")
    return _kept(locals(), ())


# THE LABELED (major) CITY TEMPLES ARE DEDICATED TO THE CLAN'S TWO PATRON FORTUNES. Hantei
# X codified that every city holds a temple to each of its clan's patron fortunes (l7r.md);
# the two GREAT temples honor those, and a smattering of small wayside shrines fills the
# rest. Declare meta(clan=...); the labeled temples (kind="temple", not "small_shrine")
# must be exactly the clan's two fortunes. Override with meta(temple_fortunes=[...]) for a
# city that changed hands. GM, 2026-07: Nagahara (Crab) had a large Temple of Suitengu -
# a thematic pick, not a Crab patron (Crab = Bishamon + Ebisu). Named after "Temple of X".


def _seg_0563_161__declared_t(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.161 (declared_t) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        declared_t = meta.get("temple_fortunes")
    return _kept(locals(), ('declared_t',))


def _seg_0563_162__clan_t(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.162 (clan_t) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        clan_t = meta.get("clan")
    return _kept(locals(), ('clan_t',))


def _seg_0563_163__city_clan_known(*, cf: Any = _UNBOUND, check: Any = _UNBOUND, clan_t: Any = _UNBOUND, declared_t: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.163 (city_clan_known) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and declared_t is None and clan_t:
        cf = CLAN_FORTUNES.get(clan_t.lower())
        check("city_clan_known", cf is not None, f"unknown clan {clan_t!r} - no patron fortunes")
        declared_t = sorted(cf) if cf else None
    return _kept(locals(), ('cf', 'declared_t'))


def _seg_0563_164__city_temples_dedicated(
    *,
    _tfortune: Any = _UNBOUND,
    allowed: Any = _UNBOUND,
    check: Any = _UNBOUND,
    clan_t: Any = _UNBOUND,
    declared_t: Any = _UNBOUND,
    f: Any = _UNBOUND,
    lab: Any = _UNBOUND,
    major: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    missing: Any = _UNBOUND,
    r: Any = _UNBOUND,
    rel: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    stray_t: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.164 (city_temples_dedicated) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and declared_t is not None:

        def _tfortune(r: dict[str, Any]) -> str:
            lab = (r.get("label") or "").strip()
            return lab.rsplit(" of ", 1)[-1].strip() if " of " in lab else lab

        major = [_tfortune(r) for r in rel if r.get("kind") == "temple"]
        # every major temple honors a PATRON fortune (or Bishamon, the warrior fortune of
        # any clan's samurai quarter - for Crab it IS a patron; for Crane/Tango it stands
        # beside the two patron temples), and BOTH patrons must be present. A great temple to
        # a non-patron (Nagahara's Suitengu) fails; small wayside shrines carry the rest.
        allowed = set(declared_t) | {"Bishamon"}
        stray_t = sorted(set(f for f in major if f not in allowed))
        missing = sorted(f for f in declared_t if f not in major)
        check(
            "city_temples_dedicated",
            not stray_t and not missing,
            f"major city temples {sorted(set(major))}: stray non-patron {stray_t}, missing patron {missing} "
            f"(clan {clan_t!r} patrons {sorted(declared_t)}); a city has a great temple to each of its two "
            f"patron fortunes (+ optionally Bishamon in the samurai quarter), the rest small shrines",
        )
    return _kept(locals(), ('_tfortune', 'allowed', 'f', 'major', 'missing', 'r', 'stray_t'))


# MORE THAN TWO MAJOR TEMPLES IS THE MARKED EXCEPTION, AND IT MUST BE DECLARED (feature
# 016). settlements/religion-and-death.md has enumerated the recognized justifications
# since it was written, but nothing enforced them - so a city could quietly draw six
# temples and ship green, which is the "a check that never RUNS looks exactly like a
# check that passes" shape one level up: the RULE existed and the check did not. The
# declaration is meta(temple_exception=...), from the fixed TEMPLE_EXCEPTIONS vocabulary.


def _seg_0563_165__major_t(*, meta: Any = _UNBOUND, r: Any = _UNBOUND, rel: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.165 (major_t, r) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        major_t = [r for r in rel if r.get("kind") == "temple"]
    return _kept(locals(), ('major_t', 'r'))


def _seg_0563_166__city_multi_temple_exception_declared(*, check: Any = _UNBOUND, exc: Any = _UNBOUND, major_t: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.166 (city_multi_temple_exception_declared) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and len(major_t) > 2:
        exc = meta.get("temple_exception")
        check(
            "city_multi_temple_exception_declared",
            exc in TEMPLE_EXCEPTIONS,
            f"{len(major_t)} major temples but meta(temple_exception=...) is {exc!r} - a city defaults to TWO great "
            f"complexes (one per patron fortune); more is the marked exception and must name its reason, one of "
            f"{sorted(TEMPLE_EXCEPTIONS)} (see settlements/religion-and-death.md)",
        )
    return _kept(locals(), ('exc',))


# a TEMPLE NEIGHBORHOOD (>= 2 temples clustered together) should be dotted with a smattering of
# small wayside SHRINES (s.small_shrine - non-residential, kind 'small_shrine'). A lone temple
# among houses (e.g. the warrior-fortune temple in the samurai quarter) is not a neighborhood.


def _seg_0563_167__r_1(*, meta: Any = _UNBOUND, r: Any = _UNBOUND, rel: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.167 (r, temples) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        temples = [r for r in rel if r.get("kind") == "temple"]
    return _kept(locals(), ('r', 'temples'))


def _seg_0563_168__r_2(*, meta: Any = _UNBOUND, r: Any = _UNBOUND, rel: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.168 (r, shrines) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        shrines = [r for r in rel if r.get("kind") == "small_shrine"]
    return _kept(locals(), ('r', 'shrines'))


def _seg_0563_169__clustered(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND, t: Any = _UNBOUND, temples: Any = _UNBOUND, u: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.169 (clustered, t, u) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        clustered = [t for t in temples if any(u is not t and math.hypot(t["x"] - u["x"], t["y"] - u["y"]) < 400 for u in temples)]
    return _kept(locals(), ('clustered', 't', 'u'))


def _seg_0563_170__city_temple_neighborhood_has_shrines(
    *, check: Any = _UNBOUND, clustered: Any = _UNBOUND, meta: Any = _UNBOUND, near_sh: Any = _UNBOUND, scale: Any = _UNBOUND, sh: Any = _UNBOUND, shrines: Any = _UNBOUND, t: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.170 (city_temple_neighborhood_has_shrines) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and len(clustered) >= 2:
        near_sh = sum(1 for sh in shrines if any(math.hypot(sh["x"] - t["x"], sh["y"] - t["y"]) < 350 for t in clustered))
        check(
            "city_temple_neighborhood_has_shrines",
            near_sh >= 3,
            f"the temple neighborhood ({len(clustered)} clustered temples) has only {near_sh} small wayside shrine(s) - dot it with a few more (s.small_shrine)",
        )
    return _kept(locals(), ('near_sh', 'sh', 't'))


# ADEPT-MONK HOUSING (GM 2026-07-24). A city temple is a blank-court COMPLEX like the
# governor's yamen - the subject of its own Mode A diagram, a big walled rectangle on the
# city map - and its celibate resident monks live INSIDE the precinct, implied. But a
# share of each complex's 15-30 monks are married ADEPTS (adepts marry and raise
# children), and those households keep ordinary homes in the temple's neighborhood. So
# every major temple needs >= 2 dwellings of kind "monk_house" within ~170px - drawn
# deliberately identical to a laborer house (no label, no glyph of its own; the manifest
# kind exists so this check, the budget, and the population math can see households the
# caste bands must NOT count - clergy are not a lay caste).


def _seg_0563_171__b_9(*, M: Any = _UNBOUND, b: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.171 (b, monk_h) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        monk_h = [b for b in M.get("buildings", []) if b.get("kind") == "monk_house"]
    return _kept(locals(), ('b', 'monk_h'))


def _seg_0563_172__m_1(*, m: Any = _UNBOUND, meta: Any = _UNBOUND, monk_h: Any = _UNBOUND, scale: Any = _UNBOUND, t: Any = _UNBOUND, temples: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.172 (m, t, t_unserved) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        t_unserved = [t.get("label", (round(t["x"]), round(t["y"]))) for t in temples if sum(1 for m in monk_h if math.hypot(m["x"] - t["x"], m["y"] - t["y"]) <= 170) < 2]
    return _kept(locals(), ('m', 't', 't_unserved'))


def _seg_0563_173__city_temples_have_monk_housing(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, t_unserved: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.173 (city_temples_have_monk_housing) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_temples_have_monk_housing",
            not t_unserved,
            f"major temple(s) without adept-monk housing nearby: {t_unserved} - each temple complex keeps 2-3 "
            f"ordinary homes (kind 'monk_house', drawn identical to a laborer house) in its neighborhood for the "
            f"married adepts among its 15-30 monks (the celibate monks live inside the precinct, implied)",
        )
    return _kept(locals(), ())


def _seg_0563_174__m_2(*, m: Any = _UNBOUND, meta: Any = _UNBOUND, monk_h: Any = _UNBOUND, scale: Any = _UNBOUND, t: Any = _UNBOUND, temples: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.174 (m, stray_mh, t) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        stray_mh = [(round(m["x"]), round(m["y"])) for m in monk_h if not temples or min(math.hypot(m["x"] - t["x"], m["y"] - t["y"]) for t in temples) > 170]
    return _kept(locals(), ('m', 'stray_mh', 't'))


def _seg_0563_175__city_monk_houses_by_their_temple(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, stray_mh: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.175 (city_monk_houses_by_their_temple) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_monk_houses_by_their_temple",
            not stray_mh,
            f"monk house(s) stranded away from every temple (>170px): {stray_mh} - an adept's household lives in its temple's neighborhood, not scattered across the city",
        )
    return _kept(locals(), ())


# the outside samurai estates: no overlapping each other, none over the wall or moat


def _seg_0563_176__est_corners(*, est_out: Any = _UNBOUND, meta: Any = _UNBOUND, mn: Any = _UNBOUND, rect_corners_xywh: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.176 (est_corners, mn) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        est_corners = [rect_corners_xywh(mn, 0) for mn in est_out]
    return _kept(locals(), ('est_corners', 'mn'))


def _seg_0563_177__est_overlap(*, est_corners: Any = _UNBOUND, est_out: Any = _UNBOUND, i: Any = _UNBOUND, j: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.177 (est_overlap, i, j) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        est_overlap = [1 for i in range(len(est_out)) for j in range(i + 1, len(est_out)) if sat_overlap(est_corners[i], est_corners[j])]
    return _kept(locals(), ('est_overlap', 'i', 'j'))


def _seg_0563_178__city_estates_no_overlap(*, check: Any = _UNBOUND, est_overlap: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.178 (city_estates_no_overlap) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_estates_no_overlap", not est_overlap, f"{len(est_overlap)} overlapping estate pair(s)")
    return _kept(locals(), ())


def _seg_0563_179__est_bad(
    *, est_corners: Any = _UNBOUND, est_out: Any = _UNBOUND, i: Any = _UNBOUND, meta: Any = _UNBOUND, moat: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.179 (est_bad, i) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        est_bad = [1 for i in range(len(est_out)) if footprint_on_line(est_corners[i], w, 9) or (moat and footprint_on_line(est_corners[i], moat, 13))]
    return _kept(locals(), ('est_bad', 'i'))


def _seg_0563_180__city_estates_clear_of_wall_moat(*, check: Any = _UNBOUND, est_bad: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.180 (city_estates_clear_of_wall_moat) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_estates_clear_of_wall_moat", not est_bad, f"{len(est_bad)} estate(s) overlapping the wall or moat")
    return _kept(locals(), ())


# the WALLED MERCHANT ESTATES (their court, not just the house inside) must likewise sit clear
# of the rampart, the moat, and any other building. (The estate's OWN inner house, centered in
# the court, is fine; everything else - temples, compounds, other homes, other estates - is not.)


def _seg_0563_181__mest_1(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.181 (mest) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        mest = M.get("merchant_estates", [])
    return _kept(locals(), ('mest',))


def _seg_0563_182__e(*, e: Any = _UNBOUND, mest: Any = _UNBOUND, meta: Any = _UNBOUND, rect_corners_xywh: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.182 (e, mest_corners) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        mest_corners = [rect_corners_xywh(e, 0) for e in mest]
    return _kept(locals(), ('e', 'mest_corners'))


def _seg_0563_183__i_1(
    *, i: Any = _UNBOUND, mest: Any = _UNBOUND, mest_corners: Any = _UNBOUND, meta: Any = _UNBOUND, moat: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.183 (i, mest_wm) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        mest_wm = [(round(mest[i]["x"]), round(mest[i]["y"])) for i in range(len(mest)) if footprint_on_line(mest_corners[i], w, 9) or (moat and footprint_on_line(mest_corners[i], moat, 13))]
    return _kept(locals(), ('i', 'mest_wm'))


def _seg_0563_184__city_merchant_estates_clear_of_wall_moat(*, check: Any = _UNBOUND, mest_wm: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.184 (city_merchant_estates_clear_of_wall_moat) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_merchant_estates_clear_of_wall_moat", not mest_wm, f"walled merchant estate(s) overlapping the city wall or moat (keep them well inside the rampart): {mest_wm}")
    return _kept(locals(), ())


def _seg_0563_185__civics(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.185 (civics) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        civics = M.get("religious", []) + M.get("ministries", []) + ([M["governor_mansion"]] if M.get("governor_mansion") else [])
    return _kept(locals(), ('civics',))


# registry-driven (GM 2026-07-25): an estate court may not swallow ANY solid footprint


def _seg_0563_186__o(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, o: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.186 (o, others_me) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        others_me = [o for o in solid_structs(M, "religious") if o is not None]
    return _kept(locals(), ('o', 'others_me'))


def _seg_0563_187__o_1(*, meta: Any = _UNBOUND, o: Any = _UNBOUND, others_me: Any = _UNBOUND, rect_corners_xywh: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.187 (o, other_struct) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        other_struct = [rect_corners(o) if "rot" in o else rect_corners_xywh(o, 0) for o in others_me]
    return _kept(locals(), ('o', 'other_struct'))


def _seg_0563_188__o_2(*, meta: Any = _UNBOUND, o: Any = _UNBOUND, others_me: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.188 (o, other_xy) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        other_xy = [(o["x"], o["y"]) for o in others_me]
    return _kept(locals(), ('o', 'other_xy'))


def _seg_0563_189__mest_bld(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.189 (mest_bld) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        mest_bld = []  # type: ignore[var-annotated]
    return _kept(locals(), ('mest_bld',))


def _seg_0563_190__e_1(
    *,
    e: Any = _UNBOUND,
    i: Any = _UNBOUND,
    j: Any = _UNBOUND,
    mest: Any = _UNBOUND,
    mest_bld: Any = _UNBOUND,
    mest_corners: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    oc: Any = _UNBOUND,
    other_struct: Any = _UNBOUND,
    other_xy: Any = _UNBOUND,
    ox: Any = _UNBOUND,
    oy: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.190 (e, i, j, mest_bld) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for i in range(len(mest)):
            e = mest[i]
            for oc, (ox, oy) in zip(other_struct, other_xy, strict=False):
                if abs(ox - e["x"]) <= e["w"] / 2 and abs(oy - e["y"]) <= e["h"] / 2:
                    continue  # a structure centered INSIDE the court = the estate's own house
                if sat_overlap(mest_corners[i], oc):
                    mest_bld.append((round(e["x"]), round(e["y"])))
                    break
            else:
                for j in range(len(mest)):
                    if j != i and sat_overlap(mest_corners[i], mest_corners[j]):
                        mest_bld.append((round(e["x"]), round(e["y"])))
                        break
    return _kept(locals(), ('e', 'i', 'j', 'mest_bld', 'oc', 'ox', 'oy'))


def _seg_0563_191__city_merchant_estates_clear_of_buildings(*, check: Any = _UNBOUND, mest_bld: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.191 (city_merchant_estates_clear_of_buildings) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_merchant_estates_clear_of_buildings", not mest_bld, f"walled merchant estate(s) overlapping a building (temple, compound, house, or another estate): {sorted(set(mest_bld))}")
    return _kept(locals(), ())


# a walled estate's GATE may not open INTO a building. The walls may ABUT a neighbor (very
# common historically), but the threshold just outside the gate must front OPEN ground, not
# a COMPOUND (temple, ministry, the yamen, or another estate court) - point the gate elsewhere.


def _seg_0563_192__GDIR(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.192 (GDIR) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        GDIR = {"south": (0, 1), "north": (0, -1), "east": (1, 0), "west": (-1, 0)}
    return _kept(locals(), ('GDIR',))


def _seg_0563_193__compounds(
    *, civics: Any = _UNBOUND, mest_corners: Any = _UNBOUND, meta: Any = _UNBOUND, o: Any = _UNBOUND, rect_corners_xywh: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.193 (compounds, o) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        compounds = [rect_corners_xywh(o, 0) for o in civics] + list(mest_corners)
    return _kept(locals(), ('compounds', 'o'))


def _seg_0563_194__gate_bad(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.194 (gate_bad) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        gate_bad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('gate_bad',))


def _seg_0563_195__cc(
    *,
    GDIR: Any = _UNBOUND,
    cc: Any = _UNBOUND,
    civics: Any = _UNBOUND,
    compounds: Any = _UNBOUND,
    g: Any = _UNBOUND,
    gate_bad: Any = _UNBOUND,
    i: Any = _UNBOUND,
    j: Any = _UNBOUND,
    mest: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    ox: Any = _UNBOUND,
    oy: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    tcx: Any = _UNBOUND,
    tcy: Any = _UNBOUND,
    th: Any = _UNBOUND,
    thr: Any = _UNBOUND,
    tw: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.195 (cc, g, gate_bad, i) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for i in range(len(mest)):
            g = mest[i].get("gate")
            if not g:
                continue
            ox, oy = GDIR.get(mest[i].get("gate_dir", "south"), (0, 1))
            tcx, tcy = g[0] + ox * 11, g[1] + oy * 11  # a threshold box just OUTSIDE the gate
            tw, th = (24, 22) if ox == 0 else (22, 24)
            thr = [(tcx - tw / 2, tcy - th / 2), (tcx + tw / 2, tcy - th / 2), (tcx + tw / 2, tcy + th / 2), (tcx - tw / 2, tcy + th / 2)]
            for j, cc in enumerate(compounds):
                if j == len(civics) + i:  # skip the estate's OWN court
                    continue
                if sat_overlap(thr, cc):
                    gate_bad.append((round(mest[i]["x"]), round(mest[i]["y"])))
                    break
    return _kept(locals(), ('cc', 'g', 'gate_bad', 'i', 'j', 'ox', 'oy', 'tcx', 'tcy', 'th', 'thr', 'tw'))


def _seg_0563_196__city_merchant_estate_gate_clear(*, check: Any = _UNBOUND, gate_bad: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.196 (city_merchant_estate_gate_clear) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_merchant_estate_gate_clear",
            not gate_bad,
            f"walled merchant estate gate(s) opening INTO a building (a temple/compound/another estate) - point the gate at open ground: {gate_bad}",
        )
    return _kept(locals(), ())


# the government compounds (governor's mansion + ministry offices) sit inside, clear of the
# barriers. (The governor's YAMEN is legitimately a large walled compound - a whole city block,
# dozens of buildings inside, drawn here as walls-only - so its size is fine; it must just not
# cross the rampart.)


def _seg_0563_197__gov(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.197 (gov) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        gov = M.get("governor_mansion")
    return _kept(locals(), ('gov',))


def _seg_0563_198__gov_items(*, M: Any = _UNBOUND, gov: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.198 (gov_items) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        gov_items = ([gov] if gov else []) + M.get("ministries", [])
    return _kept(locals(), ('gov_items',))


def _seg_0563_199__g_5(
    *, g: Any = _UNBOUND, gov_items: Any = _UNBOUND, meta: Any = _UNBOUND, moat: Any = _UNBOUND, rect_corners_xywh: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.199 (g, gov_bad) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        gov_bad = [
            g.get("name") or g.get("label") or "governor's mansion"
            for g in gov_items
            if footprint_on_line(rect_corners_xywh(g, 0), w, 9) or (moat and footprint_on_line(rect_corners_xywh(g, 0), moat, 13))
        ]
    return _kept(locals(), ('g', 'gov_bad'))


def _seg_0563_200__city_government_clear_of_wall_moat(*, check: Any = _UNBOUND, gov_bad: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.200 (city_government_clear_of_wall_moat) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_government_clear_of_wall_moat", not gov_bad, f"government compound(s) overlapping the wall or moat: {gov_bad}")
    return _kept(locals(), ())


# the governor's mansion is the GRANDEST compound - a city-block yamen, at least as large
# as any samurai estate and several times any single ministry office


def _seg_0563_201__city_governor_mansion_large(
    *,
    M: Any = _UNBOUND,
    _floor: Any = _UNBOUND,
    big_other: Any = _UNBOUND,
    check: Any = _UNBOUND,
    est_out: Any = _UNBOUND,
    far_min: Any = _UNBOUND,
    ga: Any = _UNBOUND,
    gov: Any = _UNBOUND,
    m: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    mn: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.201 (city_governor_mansion_large, city_ministries_cluster_at_government) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and gov:
        ga = gov["w"] * gov["h"]
        # the absolute floor is REAL area (~1.4 ha): 24000px2 was tuned at the pre-ladder
        # ~2.55 ft/px grain and would demand a 2 ha yamen at 3 ft/px
        _floor = round(24000 * (2.55 / meta.get("ftpx", 2.55)) ** 2)
        big_other = max([mn["w"] * mn["h"] for mn in est_out] + [3 * m["w"] * m["h"] for m in M.get("ministries", [])] + [_floor])
        check(
            "city_governor_mansion_large",
            ga >= big_other,
            f"the governor's mansion ({ga:.0f}px2) must be the grandest compound - a city-block yamen at least as large as any estate and >= 3x any ministry (need >= {big_other:.0f})",
        )
        # the ministries cluster around the yamen (the government district), threading into the
        # samurai quarter; only the Ministry of Rites sits apart, with the temples it oversees
        far_min = [m.get("name") for m in M.get("ministries", []) if "rites" not in (m.get("name") or "").lower() and math.hypot(m["x"] - gov["x"], m["y"] - gov["y"]) > 480]
        check(
            "city_ministries_cluster_at_government",
            not far_min,
            f"ministry office(s) far from the governor's mansion - the ministries belong around the yamen / in the samurai quarter (only Rites sits with the temples): {far_min}",
        )
    return _kept(locals(), ('_floor', 'big_other', 'far_min', 'ga', 'm', 'mn'))


# a planned city's government offices FRONT its streets - the yamen sits where the main
# streets cross and the bureaus line the avenues around it (Chinese official street /
# jokamachi grid), so every ministry must sit on a street, not float mid-block


def _seg_0563_202__r23(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, r23: Any = _UNBOUND, scale: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.202 (r23, st, st_pts) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        st_pts = (
            [st["pts"] for st in M.get("town_streets", [])] + ([M["road"]] if M.get("road") else []) + [r23["pts"] for r23 in M.get("roads", [])]
        )  # the ote-suji IS the avenue (021: capital ministries front the road)
    return _kept(locals(), ('r23', 'st', 'st_pts'))


def _seg_0563_203__i_2(*, M: Any = _UNBOUND, i: Any = _UNBOUND, m: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, sp: Any = _UNBOUND, st_pts: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.203 (i, m, no_front, sp) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        no_front = [m.get("name") for m in M.get("ministries", []) if not any(seg_dist(m["x"], m["y"], sp[i], sp[i + 1]) < 85 for sp in st_pts for i in range(len(sp) - 1))]
    return _kept(locals(), ('i', 'm', 'no_front', 'sp'))


def _seg_0563_204__city_ministries_front_a_street(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, no_front: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.204 (city_ministries_front_a_street) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_ministries_front_a_street",
            not no_front,
            f"ministry office(s) not fronting any city street - government offices line the avenues around the yamen, they do not float mid-block: {no_front}",
        )
    return _kept(locals(), ())


# a walled city SEALS its samurai/government quarter off the commoner streets with kido
# (wooden ward gates), not internal ramparts: full walled wards are a great-capital / Tang
# feature, over-scaled here, so a provincial city gates the quarter's street entries instead


def _seg_0563_205__i_3(*, M: Any = _UNBOUND, i: Any = _UNBOUND, k: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.205 (i, k, on_st_kido, st) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        on_st_kido = [
            k
            for k in M.get("kido", [])
            if any(seg_dist(k["x"], k["y"], st["pts"][i], st["pts"][i + 1]) < st.get("w", 18) / 2 + 8 for st in M.get("town_streets", []) for i in range(len(st["pts"]) - 1))
        ]
    return _kept(locals(), ('i', 'k', 'on_st_kido', 'st'))


def _seg_0563_206__gated(*, gov: Any = _UNBOUND, k: Any = _UNBOUND, meta: Any = _UNBOUND, on_st_kido: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.206 (gated, k) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        gated = [k for k in on_st_kido if gov and math.hypot(k["x"] - gov["x"], k["y"] - gov["y"]) < 480]
    return _kept(locals(), ('gated', 'k'))


# CAPITAL-INVERTED (021): the capital adopts the ward MESH (kido at machi mouths;
# yashiki walls seal the samurai streets). Either form is the interior-gate doctrine,
# which meta(ward_gates=False) turns off for a city that does not use it - there is
# then nothing to seal with (GM 2026-08-10).


def _seg_0563_207__city_samurai_quarter_gated(*, URBAN: Any = _UNBOUND, check: Any = _UNBOUND, gated: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.207 (city_samurai_quarter_gated) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):  # noqa: SIM102
            if URBAN and meta.get("ward_gates", True):
                check(
                    "city_samurai_quarter_gated",
                    len(gated) >= 2,
                    f"a walled city seals its samurai/government quarter with kido ward gates across the streets entering it (s.kido), not walls - {len(gated)} gate(s) bar the quarter's street entries near the yamen, need >= 2",
                )
    return _kept(locals(), ())


# ...and that ward must be SEALED: a continuous fence whose ends abut the city wall, that
# a street pierces ONLY at a kido gate. Otherwise the gates can just be walked around, and
# the road network connects samurai to commoner with no gate between them.


def _seg_0563_208__wards(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.208 (wards) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        wards = M.get("wards", [])
    return _kept(locals(), ('wards',))


def _seg_0563_209__kido(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.209 (kido) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        kido = M.get("kido", [])
    return _kept(locals(), ('kido',))


def _seg_0563_210__a_1(*, M: Any = _UNBOUND, a: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.210 (a, netlines, st) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        netlines = [st["pts"] for st in M.get("town_streets", [])] + ([M["road"]] if M.get("road") else []) + [a["pts"] for a in M.get("alleys", [])] + ([M["ring_road"]] if M.get("ring_road") else [])
    return _kept(locals(), ('a', 'netlines', 'st'))


def _seg_0563_211__bad_cross(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.211 (bad_cross, open_end) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        bad_cross, open_end = [], []  # type: ignore[var-annotated]
    return _kept(locals(), ('bad_cross', 'open_end'))


def _seg_0563_212__bad_cross_1(
    *,
    bad_cross: Any = _UNBOUND,
    bnd: Any = _UNBOUND,
    e: Any = _UNBOUND,
    g: Any = _UNBOUND,
    i: Any = _UNBOUND,
    ip: Any = _UNBOUND,
    ki: Any = _UNBOUND,
    kido: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    netlines: Any = _UNBOUND,
    open_end: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    sp: Any = _UNBOUND,
    w: Any = _UNBOUND,
    wards: Any = _UNBOUND,
    wd: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.212 (bad_cross, bnd, e, g) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for wd in wards:
            bnd = wd["boundary"]
            for sp in netlines:
                for i in range(len(sp) - 1):
                    for ki in range(len(bnd) - 1):
                        if segments_cross(sp[i], sp[i + 1], bnd[ki], bnd[ki + 1]):
                            ip = seg_intersect(sp[i], sp[i + 1], bnd[ki], bnd[ki + 1])
                            if ip and not any(math.hypot(g["x"] - ip[0], g["y"] - ip[1]) < 32 for g in kido):
                                bad_cross.append((round(ip[0]), round(ip[1])))
            for e in (bnd[0], bnd[-1]):
                if len(w) >= 3 and edge_dist(e[0], e[1], w) > 45:
                    open_end.append((round(e[0]), round(e[1])))
    return _kept(locals(), ('bad_cross', 'bnd', 'e', 'g', 'i', 'ip', 'ki', 'open_end', 'sp', 'wd'))


# ...same mesh doctrine, same knob


def _seg_0563_213__city_samurai_ward_sealed(
    *, URBAN: Any = _UNBOUND, bad_cross: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, open_end: Any = _UNBOUND, scale: Any = _UNBOUND, wards: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.213 (city_samurai_ward_sealed) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):  # noqa: SIM102
            if URBAN and meta.get("ward_gates", True):
                check(
                    "city_samurai_ward_sealed",
                    bool(wards) and not bad_cross and not open_end,
                    f"the samurai/government ward is not SEALED (s.ward): wards={len(wards)}, ungated street crossings={bad_cross}, fence ends not meeting the wall={open_end} - a kido gate can be walked around unless the fence is continuous, ends at the wall, and a street pierces it only at a gate",
                )
    return _kept(locals(), ())


# ...and the fence ends must actually TOUCH the wall - a gap (even a small one, which the
# coarse 45px seal tolerance lets slide) means commoners can simply walk AROUND the end of
# the fence. The end must abut the rampart within ~10px (about the wall's own half-width).


def _seg_0563_214__fence_gap(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.214 (fence_gap) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        fence_gap = []  # type: ignore[var-annotated]
    return _kept(locals(), ('fence_gap',))


def _seg_0563_215__bnd(
    *,
    bnd: Any = _UNBOUND,
    e: Any = _UNBOUND,
    fence_gap: Any = _UNBOUND,
    g: Any = _UNBOUND,
    gates: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    w: Any = _UNBOUND,
    wards: Any = _UNBOUND,
    wd: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.215 (bnd, e, fence_gap, g) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for wd in wards:
            bnd = wd["boundary"]
            for e in (bnd[0], bnd[-1]):
                if len(w) >= 3 and edge_dist(e[0], e[1], w) > 10:
                    fence_gap.append((round(e[0]), round(e[1]), "gap to the wall"))
                elif any(math.hypot(e[0] - g[0], e[1] - g[1]) < 45 for g in gates):
                    fence_gap.append((round(e[0]), round(e[1]), "lands in a gate OPENING (the wall is cut there, so the fence meets nothing)"))
    return _kept(locals(), ('bnd', 'e', 'fence_gap', 'g', 'wd'))


def _seg_0563_216__city_ward_fence_meets_wall(*, check: Any = _UNBOUND, fence_gap: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.216 (city_ward_fence_meets_wall) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_ward_fence_meets_wall",
            not fence_gap,
            f"ward-fence end(s) not abutting SOLID city wall (commoners could walk around the fence end): {fence_gap} - extend the fence to solid rampart, clear of any gate opening",
        )
    return _kept(locals(), ())


# THE FENCE SEALS COMMONERS OUT - so nobody it seals out may LIVE inside it (GM
# 2026-08-02, on Minami: 2 laborer houses in the middle of the samurai neighborhood
# and a merchant row hugging the inside of the west fence, leaked in by whole-interior
# top-up sweeps whose rectangles overlap the ward). Historical grounding: an Edo-era
# jokamachi zoned samurai and chonin ground apart as a matter of LAW (bukechi vs
# chonin-chi), and a Chinese provincial seat likewise kept commerce off the yamen
# quarter - a laborer terrace between two samurai houses inside the palisade is not
# variety, it contradicts the fence around it. Only samurai dwellings, their live-in
# domestics (servant - the gens interleave them deliberately) and government ground
# belong inside. monk_house is deliberately NOT barred: a temple may stand inside the
# ward (Tango's Bishamon precinct - the warrior fortune beside the garrison quarter)
# and its clergy row belongs with its temple, held there by the temple-neighborhood
# checks. Classification family: CENTER-tested on purpose (a building belongs to ONE
# ward; see "Centers, footprints, and aggregates" in the skill CLAUDE.md).


def _seg_0563_217__barred(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.217 (barred) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        barred = ("laborer", "laborer_large", "merchant", "merchant_house", "merchant_large", "burakumin", "shop", "inn")
    return _kept(locals(), ('barred',))


def _seg_0563_218__commoner_in(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.218 (commoner_in) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        commoner_in = []  # type: ignore[var-annotated]
    return _kept(locals(), ('commoner_in',))


def _seg_0563_219__b_10(
    *,
    M: Any = _UNBOUND,
    b: Any = _UNBOUND,
    barred: Any = _UNBOUND,
    commoner_in: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    region: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    w: Any = _UNBOUND,
    wards: Any = _UNBOUND,
    wd: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.219 (b, commoner_in, region, wd) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for wd in wards:
            if wd.get("name") != "samurai":
                continue
            region = _ward_interior(wd["boundary"], w)
            for b in M.get("buildings", []):
                if region and b.get("kind") in barred and point_in_poly(b["x"], b["y"], region):
                    commoner_in.append((b["kind"], round(b["x"]), round(b["y"])))
    return _kept(locals(), ('b', 'commoner_in', 'region', 'wd'))


# ...and the residents who ARE admitted must be housed the way the ward houses them.
# A samurai household's domestics lived in the perimeter nagaya that forms the plot's
# street boundary, in the nagayamon gate rooms, or in nando off the kitchen - never in
# a freestanding house in the buke-chi; a Chinese elite compound puts them in the
# daozuofang, the south row whose blank back IS the street wall. Ranks of small uniform
# dwellings are real, but they are ashigaru kumi-yashiki on the town FRINGE. So every
# servant inside the fence must carry `of` (its master's house), ABUT that house, and
# be a RANGE rather than a cottage. GM 2026-08-02, after the barred kinds were evicted
# and the packs refilled the same ground with servants: "I swear I'm seeing way MORE
# commoner houses in the samurai neighborhood now!" - the servant glyph is a laborer
# glyph with a 4 ft trim, so detached-and-ranked reads as exactly what the fence
# excludes. The COUNT is canon and is not what this polices (budgets.md: 72 of a
# provincial city's 120 servant families are attached to its 60 samurai households);
# the ARRANGEMENT is. Research: research/cities/government.md.


def _seg_0563_220__loose_servants(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.220 (loose_servants) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        loose_servants = []  # type: ignore[var-annotated]
    return _kept(locals(), ('loose_servants',))


def _seg_0563_221__b_11(
    *,
    M: Any = _UNBOUND,
    b: Any = _UNBOUND,
    host: Any = _UNBOUND,
    hosts: Any = _UNBOUND,
    loose_servants: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    of: Any = _UNBOUND,
    region: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    w: Any = _UNBOUND,
    wards: Any = _UNBOUND,
    wd: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.221 (b, host, hosts, loose_servants) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for wd in wards:
            if wd.get("name") != "samurai":
                continue
            region = _ward_interior(wd["boundary"], w)
            if not region:
                continue
            hosts = {(round(b["x"], 1), round(b["y"], 1)): b for b in M.get("buildings", []) if b.get("kind") in ("samurai", "samurai_large")}
            for b in M.get("buildings", []):
                if b.get("kind") != "servant" or "w" not in b or not point_in_poly(b["x"], b["y"], region):
                    continue
                of = b.get("of")
                host = hosts.get((round(of[0], 1), round(of[1], 1))) if of else None
                if host is None:
                    loose_servants.append((round(b["x"]), round(b["y"]), "freestanding - no samurai household"))
                elif edge_gap(b, host) > 2.5:
                    loose_servants.append((round(b["x"]), round(b["y"]), f"detached from its household by {edge_gap(b, host):.0f}px"))
                elif max(b["w"], b["h"]) < 2.2 * min(b["w"], b["h"]):
                    loose_servants.append((round(b["x"]), round(b["y"]), "drawn as a cottage, not a range"))
    return _kept(locals(), ('b', 'host', 'hosts', 'loose_servants', 'of', 'region', 'wd'))


def _seg_0563_222__city_ward_servants_housed_as_ranges(*, check: Any = _UNBOUND, loose_servants: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.222 (city_ward_servants_housed_as_ranges) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_ward_servants_housed_as_ranges",
            not loose_servants,
            f"servant dwelling(s) inside the samurai ward not drawn as their household's RANGE: {loose_servants[:6]} - a samurai household's "
            f"domestics live in the nagaya along its own frontage, not in a freestanding cottage among the compounds (which reads as the very "
            f"commoner fabric the fence excludes); place them with s.servant_ranges() AFTER the ward's samurai houses, and put any genuinely "
            f"ranked small housing outside the fence, where ashigaru kumi-yashiki belong",
        )
    return _kept(locals(), ())


def _seg_0563_223__city_samurai_ward_residents_only(*, check: Any = _UNBOUND, commoner_in: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.223 (city_samurai_ward_residents_only) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital'):  # noqa: SIM102
        if meta.get('walled'):
            check(
                "city_samurai_ward_residents_only",
                not commoner_in,
                f"commoner dwelling(s)/commerce INSIDE the samurai ward fence: {commoner_in[:8]} - the ward exists to seal the samurai/government quarter off the commoners; only samurai houses, their live-in servants and government ground belong inside (s.building refuses these seats once s.ward has run - hoist s.ward ahead of the commoner packs and re-seat the leaked households outside the fence)",
            )
    return _kept(locals(), ())


# the ward FENCE runs in OPEN ground - it must not pass THROUGH a building, a mausoleum, or
# another ward's fence (GM, 2026-07). The packs keep off the fence via s.ward's corridor, but
# a hand-placed compound (the mausoleum) or a diagonal fence segment can still cut through one.


def _seg_0563_224__fence_hit(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.224 (fence_hit) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        fence_hit = []  # type: ignore[var-annotated]
    return _kept(locals(), ('fence_hit',))


def _seg_0563_225___ftargets(*, M: Any = _UNBOUND, b: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.225 (_ftargets, b) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        _ftargets = [b for b in (M.get("buildings", []) + M.get("houses", []) + M.get("mausoleums", [])) if "w" in b]
    return _kept(locals(), ('_ftargets', 'b'))


def _seg_0563_226__b_12(
    *,
    _ftargets: Any = _UNBOUND,
    b: Any = _UNBOUND,
    b2: Any = _UNBOUND,
    bc: Any = _UNBOUND,
    bnd: Any = _UNBOUND,
    fence_hit: Any = _UNBOUND,
    i: Any = _UNBOUND,
    j: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    wards: Any = _UNBOUND,
    wd: Any = _UNBOUND,
    wd2: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.226 (b, b2, bc, bnd) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for wd in wards:
            bnd = wd["boundary"]
            for b in _ftargets:
                bc = rect_corners({"x": b["x"], "y": b["y"], "w": b["w"], "h": b.get("h", b["w"]), "rot": b.get("rot", 0)})
                if footprint_on_line(bc, bnd, 4):
                    fence_hit.append((round(b["x"]), round(b["y"])))
            for wd2 in wards:
                if wd2 is wd:
                    continue
                b2 = wd2["boundary"]
                if any(segments_cross(bnd[i], bnd[i + 1], b2[j], b2[j + 1]) for i in range(len(bnd) - 1) for j in range(len(b2) - 1)):
                    fence_hit.append(("ward-x-ward", round(bnd[0][0])))
    return _kept(locals(), ('b', 'b2', 'bc', 'bnd', 'fence_hit', 'i', 'j', 'wd', 'wd2'))


def _seg_0563_227__city_ward_fence_clear_of_structures(*, check: Any = _UNBOUND, fence_hit: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.227 (city_ward_fence_clear_of_structures) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_ward_fence_clear_of_structures",
            not fence_hit,
            f"ward fence passing THROUGH a structure (building / mausoleum / another fence): {sorted(set(fence_hit))[:4]} - "
            f"the fence runs in open ground; move the structure clear of the fence line or reroute the fence",
        )
    return _kept(locals(), ())


# a KIDO is a gate THROUGH the fence, so it must sit ON the fence (overlap it), not beside it
# (GM, 2026-07: a gate next to rather than part of the wall does not work). Its crossing point
# must lie within ~8px of a fence segment so the gate visibly straddles the fence.


def _seg_0563_228__off_fence(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.228 (off_fence) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        off_fence = []  # type: ignore[var-annotated]
    return _kept(locals(), ('off_fence',))


def _seg_0563_229__i_4(
    *, i: Any = _UNBOUND, kd: Any = _UNBOUND, kido: Any = _UNBOUND, meta: Any = _UNBOUND, off_fence: Any = _UNBOUND, scale: Any = _UNBOUND, wards: Any = _UNBOUND, wd: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.229 (i, kd, off_fence, wd) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for kd in kido:
            if wards and min((seg_dist(kd["x"], kd["y"], wd["boundary"][i], wd["boundary"][i + 1]) for wd in wards for i in range(len(wd["boundary"]) - 1)), default=999) > 8:
                off_fence.append((round(kd["x"]), round(kd["y"])))
    return _kept(locals(), ('i', 'kd', 'off_fence', 'wd'))


def _seg_0563_230__city_kido_on_ward_fence(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, off_fence: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.230 (city_kido_on_ward_fence) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_kido_on_ward_fence",
            not off_fence,
            f"ward gate(s) sitting BESIDE the fence, not on it: {off_fence[:4]} - a kido gates a crossing THROUGH the "
            f"fence, so its point must lie ON the fence line (overlap it), not offset into the ward",
        )
    return _kept(locals(), ())


# ...and where the fence meets the wall, the city WALL must render ON TOP (the fence runs
# UNDER the rampart). The fence is drawn late (high z), so without a wall cap on top of the
# junction it paints over the wall stroke. s.ward records the fence z and the wall cap it
# lays over each end; the cap's z must be above the fence's.


def _seg_0563_231__not_under(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.231 (not_under) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        not_under = []  # type: ignore[var-annotated]
    return _kept(locals(), ('not_under',))


def _seg_0563_232__c(
    *,
    c: Any = _UNBOUND,
    caps: Any = _UNBOUND,
    e: Any = _UNBOUND,
    fz: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    not_under: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    w: Any = _UNBOUND,
    wards: Any = _UNBOUND,
    wd: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.232 (c, caps, e, fz) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        for wd in wards:
            fz = wd.get("z")
            caps = wd.get("wall_caps", [])
            if fz is None:
                continue
            for e in (wd["boundary"][0], wd["boundary"][-1]):
                if len(w) >= 3 and edge_dist(e[0], e[1], w) <= 15 and not any(c.get("z", -1) > fz and math.hypot(c["x"] - e[0], c["y"] - e[1]) < 30 for c in caps):
                    not_under.append((round(e[0]), round(e[1])))
    return _kept(locals(), ('c', 'caps', 'e', 'fz', 'not_under', 'wd'))


def _seg_0563_233__city_ward_fence_under_wall(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, not_under: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.233 (city_ward_fence_under_wall) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_ward_fence_under_wall",
            not not_under,
            f"ward-fence end(s) NOT rendered under the city wall - no wall cap on top of the junction, so the fence paints over the rampart: {not_under}",
        )
    return _kept(locals(), ())


# the extramural samurai estates all lie TOWARD OTOSAN UCHI (the Imperial capital) - a
# samurai builds his country seat on the capital-facing side, so the direction is
# per-city: meta(capital_dir=<cardinal>) (Tango SE, Nagahara NE). Each estate must sit in
# the correct half-plane(s) for that direction (a diagonal requires BOTH axes).


def _seg_0563_234__cx(*, meta: Any = _UNBOUND, p: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.234 (cx, cy, p) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        cx, cy = sum(p[0] for p in w) / len(w), sum(p[1] for p in w) / len(w)
    return _kept(locals(), ('cx', 'cy', 'p'))


def _seg_0563_235__cap(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.235 (cap) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        cap = meta.get("capital_dir", "southeast")
    return _kept(locals(), ('cap',))


def _seg_0563_236__cd(*, cap: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.236 (cd) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        cd = unit_dir(cap)
    return _kept(locals(), ('cd',))


def _seg_0563_237__city_capital_dir_valid(*, cap: Any = _UNBOUND, cd: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.237 (city_capital_dir_valid) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_capital_dir_valid", cd is not None, f"meta(capital_dir={cap!r}) is not a cardinal direction")
    return _kept(locals(), ())


def _seg_0563_238__city_estates_toward_capital(
    *,
    cap: Any = _UNBOUND,
    cd: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    est_out: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    mn: Any = _UNBOUND,
    not_cap: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    toward: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.238 (city_estates_toward_capital) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and cd:

        def toward(mn: dict[str, Any]) -> bool:
            okx = (mn["x"] > cx) if cd[0] > 0.3 else (mn["x"] < cx) if cd[0] < -0.3 else True
            oky = (mn["y"] > cy) if cd[1] > 0.3 else (mn["y"] < cy) if cd[1] < -0.3 else True
            return okx and oky

        not_cap = [(round(mn["x"]), round(mn["y"])) for mn in est_out if not toward(mn)]
        check(
            "city_estates_toward_capital",
            not not_cap,
            f"{len(not_cap)} samurai estate(s) not toward the capital ({cap}): {not_cap[:3]} - a city's extramural estates cluster on the Otosan-Uchi-facing side (meta(capital_dir=...))",
        )
    return _kept(locals(), ('mn', 'not_cap', 'toward'))


# ... and clear of the ROADS leaving the city (an estate straddling the highway blocks it -
# GM, 2026-07: a Nagahara estate sat on the bridge road). Test each outside estate footprint
# against every recorded road.


def _seg_0563_239__r_3(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, r: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.239 (r, roads_all) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        roads_all = [r["pts"] for r in M.get("roads", [])] or ([M["road"]] if M.get("road") else [])
    return _kept(locals(), ('r', 'roads_all'))


def _seg_0563_240__est_on_road(
    *, M: Any = _UNBOUND, est_out: Any = _UNBOUND, meta: Any = _UNBOUND, mn: Any = _UNBOUND, roads_all: Any = _UNBOUND, rp: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.240 (est_on_road, mn, rp) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        est_on_road = [(round(mn["x"]), round(mn["y"])) for mn in est_out if any(footprint_on_line(rect_corners(_struct_rect(mn)), rp, (M.get("road_width", 26) / 2 + 4)) for rp in roads_all)]
    return _kept(locals(), ('est_on_road', 'mn', 'rp'))


def _seg_0563_241__city_estates_clear_of_roads(*, check: Any = _UNBOUND, est_on_road: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.241 (city_estates_clear_of_roads) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check(
            "city_estates_clear_of_roads",
            not est_on_road,
            f"samurai estate(s) straddling a road out of the city: {est_on_road[:3]} - an estate fronts its own approach lane but must not sit ON the highway",
        )
    return _kept(locals(), ())


# the ground circulation (streets + alleys; NOT the Imperial road, which exits at the
# gates) must stay INSIDE the wall and clear of the moat - separate checks, since a lane
# can poke through the rampart, the moat, or both (the elliptical wall curves in, so a
# lane run to the block edge can spill outside even with its vertices nominally interior)


def _seg_0563_242__a_2(*, M: Any = _UNBOUND, a: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.242 (a, lanes_pts, st) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        lanes_pts = [st["pts"] for st in M.get("town_streets", [])] + [a["pts"] for a in M.get("alleys", [])]
    return _kept(locals(), ('a', 'lanes_pts', 'st'))


def _seg_0563_243__crosses_ring(*, i: Any = _UNBOUND, k: Any = _UNBOUND, meta: Any = _UNBOUND, pts: Any = _UNBOUND, ring: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.243 (crosses_ring) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):

        def crosses_ring(pts: Poly, ring: Poly, closed: bool) -> bool:
            rng = range(len(ring)) if closed else range(len(ring) - 1)
            return any(segments_cross(pts[k], pts[k + 1], ring[i], ring[(i + 1) % len(ring)]) for k in range(len(pts) - 1) for i in rng)

    return _kept(locals(), ('crosses_ring',))


# a way WHOLLY outside the rampart is the SUBURB's own circulation (021: the kashi
# belt and guan-xiang wards keep streets and roji like any machi) - only a way that
# CROSSES the wall, or an inside way poking out, is the defect


def _seg_0563_244__p_2(
    *, crosses_ring: Any = _UNBOUND, inwall: Any = _UNBOUND, lanes_pts: Any = _UNBOUND, meta: Any = _UNBOUND, p: Any = _UNBOUND, pts: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.244 (p, pts, wall_hit) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        wall_hit = [pts[0] for pts in lanes_pts if crosses_ring(pts, w, True) or (any(not inwall(p[0], p[1]) for p in pts) and any(inwall(p[0], p[1]) for p in pts))]
    return _kept(locals(), ('p', 'pts', 'wall_hit'))


def _seg_0563_245__city_streets_clear_of_wall(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, wall_hit: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.245 (city_streets_clear_of_wall) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_streets_clear_of_wall", not wall_hit, f"{len(wall_hit)} street/alley(s) crossing the city wall (a lane running outside the rampart): {wall_hit}")
    return _kept(locals(), ())


def _seg_0563_246__moat_1(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.246 (moat) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        moat = M.get("moat")
    return _kept(locals(), ('moat',))


def _seg_0563_247__city_streets_clear_of_moat(
    *, check: Any = _UNBOUND, crosses_ring: Any = _UNBOUND, lanes_pts: Any = _UNBOUND, meta: Any = _UNBOUND, moat: Any = _UNBOUND, moat_hit: Any = _UNBOUND, pts: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 563.247 (city_streets_clear_of_moat) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and moat:
        moat_hit = [pts[0] for pts in lanes_pts if crosses_ring(pts, moat, False)]
        check("city_streets_clear_of_moat", not moat_hit, f"{len(moat_hit)} street/alley(s) crossing the moat: {moat_hit}")
    return _kept(locals(), ('moat_hit', 'pts'))


# farm fields (in-wall plots OR the surrounding farmland) must not cut across the wall stroke
# or the moat - the moat sits between the wall and the close-in fields, so they abut, not overlap


def _seg_0563_248__f(*, f: Any = _UNBOUND, fields: Any = _UNBOUND, meta: Any = _UNBOUND, moat: Any = _UNBOUND, scale: Any = _UNBOUND, w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.248 (f, fld_bad) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        fld_bad = [f["name"] for f in fields if footprint_on_line(f["outline"], w, 10) or (moat and footprint_on_line(f["outline"], moat, 13))]
    return _kept(locals(), ('f', 'fld_bad'))


def _seg_0563_249__city_fields_clear_of_wall_moat(*, check: Any = _UNBOUND, fld_bad: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.249 (city_fields_clear_of_wall_moat) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        check("city_fields_clear_of_wall_moat", not fld_bad, f"field(s) overlapping the city wall or moat: {fld_bad}")
    return _kept(locals(), ())


# the in-wall pond is a water source, not a moat - it must not touch the wall or moat


def _seg_0563_250__pnd(*, M: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 563.250 (pnd) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled'):
        pnd = M.get("pond")
    return _kept(locals(), ('pnd',))


def _seg_0563_251__city_pond_clear_of_wall_moat(
    *,
    check: Any = _UNBOUND,
    k: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    moat: Any = _UNBOUND,
    p_out: Any = _UNBOUND,
    pcx: Any = _UNBOUND,
    pcy: Any = _UNBOUND,
    pnd: Any = _UNBOUND,
    prx: Any = _UNBOUND,
    pry: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    w: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 563.251 (city_pond_clear_of_wall_moat) - body verbatim from the city mega-segment (feature 023; guards preserved, see research.md R2/R3)."""
    if scale in ('city', 'capital') and meta.get('walled') and pnd:
        pcx, pcy, prx, pry = pnd
        p_out = [(pcx + math.cos(math.tau * k / 28) * prx, pcy + math.sin(math.tau * k / 28) * pry) for k in range(28)]
        check("city_pond_clear_of_wall_moat", not (footprint_on_line(p_out, w, 9) or (moat and footprint_on_line(p_out, moat, 13))), "the in-wall pond overlaps the city wall or moat")
    return _kept(locals(), ('k', 'p_out', 'pcx', 'pcy', 'prx', 'pry'))
