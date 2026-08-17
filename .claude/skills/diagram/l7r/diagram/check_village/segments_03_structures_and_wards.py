"""Gate segments (structures and wards) - bodies verbatim from check_village.py (feature 024 package split; registry order preserved)."""

import math
from collections.abc import Sequence
from typing import Any

from l7r.diagram.settlement import LABEL_AIR_CAP, box_gap, label_aabb, label_quad, linear_tilt, sat_overlap, torii_wall_conflicts
from l7r.diagram.waterfields import hem_on_paddy

from .common_01_geometry import (
    _LABEL_CLASSIFIED,
    _OVERLAP_CLASSIFIED,
    _OVERLAP_SINGLETONS,
    _OVERLAP_STRUCTS,
    Poly,
    Pt,
    _box_hits_poly,
    _struct_rect,
    convex_hull,
    point_in_poly,
    poly_area,
    poly_dist,
    rect_corners,
    seg_closest,
    seg_dist,
    seg_intersect,
    segments_cross,
)
from .common_02_overlap_policy import in_ellipse, poly_gap
from .common_03_capacity import _UNBOUND, _kept


def _seg_0133_031__alleys_serve_buildings(*, check: Any = _UNBOUND, scale: Any = _UNBOUND, thin: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0133.031 (alleys_serve_buildings) - body verbatim from _seg_0133__outside_fields_farmhouse_density (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city', 'capital'):
        check(
            "alleys_serve_buildings",
            not thin,
            f"alley(s) that uniquely serve too few dwellings to justify their length - a lane to nowhere or a redundant lane beside/across one that already serves the block (need ~1 uniquely-served dwelling per 30px): {thin}",
        )
    return _kept(locals(), ())


# ---- universal invariants ------------------------------------------------
# standalone civic buildings (flophouse, granary kura) are checked for overlaps exactly like
# houses and shops - they must not sit on a road / stream / wall / street / channel, or on
# each other / the manor / a hall. (Merchant storehouses are NOT here: they are drawn as
# annexes deliberately abutting their shop, so they would trip the structure-overlap test.)


def _seg_0134__granary(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 134 (granary) - body verbatim from the legacy gate() (feature 022)."""
    granary = M.get("granary")
    return _kept(locals(), ('granary',))


# the funerary structures are first-class structures for overlap purposes: a graveyard, mausoleum,
# cremation ground, or ossuary must not sit on a building, the wall, the moat, a road, or a street
# (they were added late, so it is easy to forget - this is what catches a grave on the moat or a
# mausoleum in the street). They carry x/y/w/h/rot like any building.
# EVERY solid footprint feature is a first-class structure for overlap purposes (see the
# _OVERLAP_STRUCTS registry): houses, civic/urban buildings, the funerary structures, wayside
# shrines, ministries, inspection stations. They are normalized to rects and then checked, like any
# building, against each other and against the wall / moat / road / stream / channel / street /
# manor / hall / gate / torii. Adding a new feature here is the DEFAULT; exceptions that may overlap
# (annex storehouses, annex threshing yards, on-wall towers, bridges) live in _OVERLAP_EXEMPT.


def _seg_0135__k(*, M: Any = _UNBOUND, granary: Any = _UNBOUND, k: Any = _UNBOUND, s: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 135 (k, s, structs) - body verbatim from the legacy gate() (feature 022)."""
    structs = [_struct_rect(s) for k in _OVERLAP_STRUCTS for s in M.get(k, [])] + [_struct_rect(s) for s in (granary["stores"] if granary else [])]
    return _kept(locals(), ('k', 's', 'structs'))


def _seg_0136__corners(*, s: Any = _UNBOUND, structs: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 136 (corners, s) - body verbatim from the legacy gate() (feature 022)."""
    corners = [rect_corners(s) for s in structs]
    return _kept(locals(), ('corners', 's'))


def _seg_0137__bad(*, corners: Any = _UNBOUND, i: Any = _UNBOUND, j: Any = _UNBOUND, structs: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 137 (bad, i, j) - body verbatim from the legacy gate() (feature 022)."""
    bad = [
        (i, j)
        for i in range(len(structs))
        for j in range(i + 1, len(structs))
        if math.hypot(structs[i]["x"] - structs[j]["x"], structs[i]["y"] - structs[j]["y"]) <= 110 and sat_overlap(corners[i], corners[j])
    ]
    return _kept(locals(), ('bad', 'i', 'j'))


def _seg_0138__no_structure_overlaps(*, bad: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 138 (no_structure_overlaps) - body verbatim from the legacy gate() (feature 022)."""
    check("no_structure_overlaps", not bad, f"{len(bad)} overlapping structure pair(s)")
    return _kept(locals(), ())


# COMPLETENESS GUARD: every footprint feature in the manifest must be classified for overlap (in the
# _OVERLAP_* registry above). The default is MUST-NOT-OVERLAP - a new feature joins _OVERLAP_STRUCTS
# and is cleared by the checks above; anything allowed to overlap is named in _OVERLAP_EXEMPT. This
# fires when a generator emits a feature key nobody classified, so a new feature can never silently
# skip the overlap rules (the recurring trap: harvest features shipped unchecked).


def _seg_0139__g(*, M: Any = _UNBOUND, g: Any = _UNBOUND, k: Any = _UNBOUND, v: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 139 (g, k, unclassified, v) - body verbatim from the legacy gate() (feature 022)."""
    unclassified = sorted(
        k for k, v in M.items() if isinstance(v, list) and v and isinstance(v[0], dict) and any(g in v[0] for g in ("x", "pts", "outline", "boundary", "poly")) and k not in _OVERLAP_CLASSIFIED
    )
    return _kept(locals(), ('g', 'k', 'unclassified', 'v'))


def _seg_0140__every_feature_classified_for_overlap(*, check: Any = _UNBOUND, unclassified: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 140 (every_feature_classified_for_overlap) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "every_feature_classified_for_overlap",
        not unclassified,
        f"map feature(s) {unclassified} are not classified for overlap. The default is MUST-NOT-OVERLAP: add the key "
        f"to _OVERLAP_STRUCTS (so the no_structure_* checks clear it) or, if it is MEANT to overlap something (a label, "
        f"a bridge over water, a guard tower on a wall), to _OVERLAP_EXEMPT with the reason.",
    )
    return _kept(locals(), ())


# ...and the same completeness guard for CAPTIONS. A feature protected from every solid neighbor
# is still not protected from a label dropped on top of it, and that list fell behind twice before
# it was made a registry (GM 2026-07-26). Every solid key must name the label GROUP a caption has
# to use to be allowed over it, or be excused in _LABEL_EXEMPT with a reason.


def _seg_0141__k_1(*, k: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 141 (k, unlabeled) - body verbatim from the legacy gate() (feature 022)."""
    unlabeled = sorted(k for k in _OVERLAP_STRUCTS + _OVERLAP_SINGLETONS if k not in _LABEL_CLASSIFIED)
    return _kept(locals(), ('k', 'unlabeled'))


def _seg_0142__every_solid_feature_classified_for_labels(*, check: Any = _UNBOUND, unlabeled: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 142 (every_solid_feature_classified_for_labels) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "every_solid_feature_classified_for_labels",
        not unlabeled,
        f"map feature(s) {unlabeled} are not classified for LABELS. Give each one its caption GROUP in _LABEL_GROUP "
        f"(the group name is the word a caption must contain to be allowed to cover it) or, if a caption over it is "
        f"harmless, name it in _LABEL_EXEMPT with the reason.",
    )
    return _kept(locals(), ())


# no structure overlaps the magistrate's manor walls (a tilted manor uses its rotated corners)


def _seg_0143__bad_m() -> dict[str, Any]:
    """Gate segment 143 (bad_m) - body verbatim from the legacy gate() (feature 022)."""
    bad_m = []  # type: ignore[var-annotated]
    return _kept(locals(), ('bad_m',))


def _seg_0144__bad_m_1(*, M: Any = _UNBOUND, bad_m: Any = _UNBOUND, corners: Any = _UNBOUND, e: Any = _UNBOUND, mc: Any = _UNBOUND, mn: Any = _UNBOUND, sc: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 144 (bad_m, e, mc, mn) - body verbatim from the legacy gate() (feature 022)."""
    for mn in M.get("manors", []):
        e = 4  # wall thickness
        mc = rect_corners({"x": mn["x"], "y": mn["y"], "w": mn["w"] + 2 * e, "h": mn["h"] + 2 * e, "rot": mn.get("rot", 0)})
        bad_m += [1 for sc in corners if sat_overlap(sc, mc)]
    return _kept(locals(), ('bad_m', 'e', 'mc', 'mn', 'sc'))


def _seg_0145__no_structure_on_manor(*, bad_m: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 145 (no_structure_on_manor) - body verbatim from the legacy gate() (feature 022)."""
    check("no_structure_on_manor", not bad_m, f"{len(bad_m)} structure(s) overlap the manor walls")
    return _kept(locals(), ())


def _seg_0146__rect_corners_xywh(*, cx: Any = _UNBOUND, cy: Any = _UNBOUND, e: Any = _UNBOUND, h: Any = _UNBOUND, w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 146 (rect_corners_xywh) - body verbatim from the legacy gate() (feature 022)."""

    def rect_corners_xywh(item: dict[str, Any], e: float) -> list[tuple[float, float]]:
        cx, cy, w, h = item["x"], item["y"], item["w"], item["h"]
        return [(cx - w / 2 - e, cy - h / 2 - e), (cx + w / 2 + e, cy - h / 2 - e), (cx + w / 2 + e, cy + h / 2 + e), (cx - w / 2 - e, cy + h / 2 + e)]

    return _kept(locals(), ('rect_corners_xywh',))


# no structure overlaps a religious hall (an ellipse block undershot its corners)


def _seg_0147__bad_rel(*, M: Any = _UNBOUND, corners: Any = _UNBOUND, rect_corners_xywh: Any = _UNBOUND, rel: Any = _UNBOUND, sc: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 147 (bad_rel, rel, sc) - body verbatim from the legacy gate() (feature 022)."""
    bad_rel = [1 for rel in M.get("religious", []) for sc in corners if sat_overlap(sc, rect_corners_xywh(rel, 4))]
    return _kept(locals(), ('bad_rel', 'rel', 'sc'))


def _seg_0148__no_structure_on_religious(*, bad_rel: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 148 (no_structure_on_religious) - body verbatim from the legacy gate() (feature 022)."""
    check("no_structure_on_religious", not bad_rel, f"{len(bad_rel)} structure(s) overlap a religious hall")
    return _kept(locals(), ())


# no structure overlaps the gate's guard station / guardtower


def _seg_0149__bad_g(*, M: Any = _UNBOUND, corners: Any = _UNBOUND, gs: Any = _UNBOUND, rect_corners_xywh: Any = _UNBOUND, sc: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 149 (bad_g, gs, sc) - body verbatim from the legacy gate() (feature 022)."""
    bad_g = [1 for gs in M.get("gate_structs", []) for sc in corners if sat_overlap(sc, rect_corners_xywh(gs, 2))]
    return _kept(locals(), ('bad_g', 'gs', 'sc'))


def _seg_0150__no_structure_on_gate(*, bad_g: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 150 (no_structure_on_gate) - body verbatim from the legacy gate() (feature 022)."""
    check("no_structure_on_gate", not bad_g, f"{len(bad_g)} structure(s) overlap the gate guard station/tower")
    return _kept(locals(), ())


# no structure overlaps a torii arch. The arch is TRUE SCALE since 2026-07-21 (a 16 ft rail span,
# drawn via px()), so its box scales with meta.ftpx - the old fixed 38x28 box over-flagged houses
# that legitimately pack near the smaller true-size arch. Geometry mirrors settlement._torii
# (rail rise 7/19, post drop 17/19 of the half-span) + a 2px pad.


def _seg_0151___tft(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 151 (_tft) - body verbatim from the legacy gate() (feature 022)."""
    _tft = float(M.get("meta", {}).get("ftpx", 1) or 1)
    return _kept(locals(), ('_tft',))


def _seg_0152___ts2(*, _tft: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 152 (_ts2) - body verbatim from the legacy gate() (feature 022)."""
    _ts2 = 8.0 / _tft + 2
    return _kept(locals(), ('_ts2',))


def _seg_0153__bad_t(*, M: Any = _UNBOUND, _ts2: Any = _UNBOUND, corners: Any = _UNBOUND, sc: Any = _UNBOUND, t: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 153 (bad_t, sc, t) - body verbatim from the legacy gate() (feature 022)."""
    bad_t = [
        1
        for t in M.get("torii", [])
        for sc in corners
        if sat_overlap(sc, [(t[0] - _ts2, t[1] - _ts2 * 0.37), (t[0] + _ts2, t[1] - _ts2 * 0.37), (t[0] + _ts2, t[1] + _ts2 * 0.9), (t[0] - _ts2, t[1] + _ts2 * 0.9)])
    ]
    return _kept(locals(), ('bad_t', 'sc', 't'))


def _seg_0154__no_structure_on_torii(*, bad_t: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 154 (no_structure_on_torii) - body verbatim from the legacy gate() (feature 022)."""
    check("no_structure_on_torii", not bad_t, f"{len(bad_t)} structure(s) overlap a torii arch")
    return _kept(locals(), ())


# TORII AND RELIGIOUS FOOTPRINTS KEEP CLEAR OF THE DEFENSIVE WORKS AND THE PATROL RING (GM
# placement rules 2026-07-21, caught on Tango: a wayside shrine seated against the SW wall
# tower). A torii arch overlapping a temple/shrine hall, a guard tower / gate structure, or
# the ring-road corridor - or a religious footprint overlapping a tower or the ring road -
# reads as impossible construction: the wall's works and its patrol lane are kept clear, and
# an arch stands in the open on its approach, never against a hall. (A torii OVER an ordinary
# street stays legitimate - a monzen sando arch spans its road - so only the RING road is a
# corridor here.)


def _seg_0155___ring(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 155 (_ring) - body verbatim from the legacy gate() (feature 022)."""
    _ring = M.get("ring_road") or []
    return _kept(locals(), ('_ring',))


def _seg_0156___rw2(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 156 (_rw2) - body verbatim from the legacy gate() (feature 022)."""
    _rw2 = float(M.get("ring_road_width") or 0) / 2
    return _kept(locals(), ('_rw2',))


def _seg_0157___tow(*, M: Any = _UNBOUND, g: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 157 (_tow, g) - body verbatim from the legacy gate() (feature 022)."""
    _tow = [g for g in list(M.get("gate_structs", [])) + list(M.get("wall_towers", [])) + list(M.get("fire_towers", [])) if isinstance(g, dict) and "w" in g]
    return _kept(locals(), ('_tow', 'g'))


def _seg_0158___ring_hit_poly(
    *, _ring: Any = _UNBOUND, _rw2: Any = _UNBOUND, a: Any = _UNBOUND, b: Any = _UNBOUND, i: Any = _UNBOUND, k: Any = _UNBOUND, poly: Any = _UNBOUND, px: Any = _UNBOUND, py: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 158 (_ring_hit_poly) - body verbatim from the legacy gate() (feature 022)."""

    def _ring_hit_poly(poly: list[tuple[float, float]]) -> bool:
        """Does a FOOTPRINT reach the ring-road bed? Corner-to-segment, not center-plus-a-radius:
        the circumscribed radius this used to pass over-states an elongated hall's reach along one
        axis and under-states nothing, so it flagged halls that were genuinely clear while a long
        thin one laid across the lane could still slip through the far side of the same
        approximation (GM audit, 2026-07-27)."""
        for i in range(len(_ring) - 1):
            a, b = _ring[i], _ring[i + 1]
            # CROSSING FIRST, then proximity. Corner-sampling alone answers "is a corner near the
            # centerline", which is not the question: a hall laid ACROSS the lane can have every
            # corner outside the bed while its flanks straddle it - the y=890 hall over a bed
            # spanning 896-904 has its nearest corner exactly _rw2 away and overlaps 8 px of
            # roadbed. The old circumscribed-radius form caught that case by being loose enough,
            # which is not the same as being right; this catches it by asking the real question.
            if any(segments_cross(a, b, poly[k], poly[(k + 1) % len(poly)]) for k in range(len(poly))):
                return True
            if min(min(seg_dist(px, py, a, b) for px, py in poly), poly_dist(a[0], a[1], poly), poly_dist(b[0], b[1], poly)) < _rw2:
                return True
        return False

    return _kept(locals(), ('_ring_hit_poly',))


def _seg_0159___torii_poly(*, _ts2: Any = _UNBOUND, t: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 159 (_torii_poly) - body verbatim from the legacy gate() (feature 022)."""

    def _torii_poly(t: Sequence[float]) -> list[tuple[float, float]]:
        return [(t[0] - _ts2, t[1] - _ts2), (t[0] + _ts2, t[1] - _ts2), (t[0] + _ts2, t[1] + _ts2), (t[0] - _ts2, t[1] + _ts2)]

    return _kept(locals(), ('_torii_poly',))


def _seg_0160__bad_tor_pl() -> dict[str, Any]:
    """Gate segment 160 (bad_tor_pl) - body verbatim from the legacy gate() (feature 022)."""
    bad_tor_pl = []  # type: ignore[var-annotated]
    return _kept(locals(), ('bad_tor_pl',))


def _seg_0161___torp(
    *,
    M: Any = _UNBOUND,
    _ring_hit_poly: Any = _UNBOUND,
    _torii_poly: Any = _UNBOUND,
    _torp: Any = _UNBOUND,
    _tow: Any = _UNBOUND,
    bad_tor_pl: Any = _UNBOUND,
    g: Any = _UNBOUND,
    hit_rel: Any = _UNBOUND,
    hit_tw: Any = _UNBOUND,
    r: Any = _UNBOUND,
    t: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 161 (_torp, bad_tor_pl, g, hit_rel) - body verbatim from the legacy gate() (feature 022)."""
    for t in M.get("torii", []):
        _torp = _torii_poly(t)
        # ROTATED corners on the hall/tower side. The axis-aligned `abs(dx) < w/2 + pad` form this
        # replaces reads a tilted hall as its upright box, which is neither its footprint nor a
        # conservative cover of it - it misses the swung corners and invents ground at the flats.
        hit_rel = any(sat_overlap(_torp, rect_corners(_struct_rect(r))) for r in M.get("religious", []))
        hit_tw = any(sat_overlap(_torp, rect_corners(_struct_rect(g))) for g in _tow)
        if hit_rel or hit_tw or _ring_hit_poly(_torp):
            bad_tor_pl.append((round(t[0]), round(t[1])))
    return _kept(locals(), ('_torp', 'bad_tor_pl', 'g', 'hit_rel', 'hit_tw', 'r', 't'))


def _seg_0162__torii_clear_of_halls_towers_ring(*, bad_tor_pl: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 162 (torii_clear_of_halls_towers_ring) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "torii_clear_of_halls_towers_ring",
        not bad_tor_pl,
        f"torii arch(es) overlapping a temple/shrine hall, guard tower/gate structure, or the ring-road corridor: {sorted(set(bad_tor_pl))[:4]} - an arch stands clear on its approach (an ordinary street through the arch is fine; the patrol ring is not)",
    )
    return _kept(locals(), ())


# ... AND CLEAR OF EVERY WALL (GM 2026-07-25, caught on Nagahara: the seventh arch of the Ebisu
# sando stood in the samurai ward fence). A torii is a FREESTANDING gateway - posts in open
# ground, carrying nothing, closing nothing - while a wall is a continuous barrier, so an arch
# drawn on a wall run is impossible construction: the posts stand inside the palisade and the
# gateway opens onto a barrier. Where a way pierces a wall the opening is a GATE STRUCTURE (the
# city gate, a ward kido), never an arch. The rule and its geometry live in settlement.py's
# wall_runs block, which the PLACEMENT side reads too (shrine_hall shortens a sando that would
# reach a wall; _torii and each wall-drawing method refuse the conflict outright) - this is the
# manifest-level backstop over the city rampart, ward fences and every walled compound.


def _seg_0163__tor_wall(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 163 (tor_wall) - body verbatim from the legacy gate() (feature 022)."""
    tor_wall = torii_wall_conflicts(M)
    return _kept(locals(), ('tor_wall',))


def _seg_0164__torii_clear_of_walls(*, check: Any = _UNBOUND, tor_wall: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 164 (torii_clear_of_walls) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "torii_clear_of_walls",
        not tor_wall,
        f"torii arch(es) standing in a wall: {tor_wall[:4]} - a torii is a freestanding gateway on open ground and a "
        f"wall is a continuous barrier; a way through a wall is a GATE (the city gate, a ward kido), never an arch. "
        f"Move the arch clear - or draw the wall BEFORE the hall, and shrine_hall stops its avenue short of it.",
    )
    return _kept(locals(), ())


def _seg_0165__bad_rel_pl() -> dict[str, Any]:
    """Gate segment 165 (bad_rel_pl) - body verbatim from the legacy gate() (feature 022)."""
    bad_rel_pl = []  # type: ignore[var-annotated]
    return _kept(locals(), ('bad_rel_pl',))


def _seg_0166___relp(
    *, M: Any = _UNBOUND, _relp: Any = _UNBOUND, _ring_hit_poly: Any = _UNBOUND, _tow: Any = _UNBOUND, bad_rel_pl: Any = _UNBOUND, g: Any = _UNBOUND, hit_tw: Any = _UNBOUND, r: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 166 (_relp, bad_rel_pl, g, hit_tw) - body verbatim from the legacy gate() (feature 022)."""
    for r in M.get("religious", []):
        _relp = rect_corners(_struct_rect(r))
        hit_tw = any(sat_overlap(_relp, rect_corners(_struct_rect(g))) for g in _tow)
        if hit_tw or _ring_hit_poly(_relp):
            bad_rel_pl.append((r.get("label") or r["kind"], round(r["x"]), round(r["y"])))
    return _kept(locals(), ('_relp', 'bad_rel_pl', 'g', 'hit_tw', 'r'))


def _seg_0167__religious_clear_of_ring_and_towers(*, bad_rel_pl: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 167 (religious_clear_of_ring_and_towers) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "religious_clear_of_ring_and_towers",
        not bad_rel_pl,
        f"religious footprint(s) overlapping a guard tower/gate structure or the ring-road corridor: {bad_rel_pl[:4]} - shrines and halls keep clear of the wall's works and the patrol lane",
    )
    return _kept(locals(), ())


# roads/streets are a GROUND layer: a gatehouse or label that legitimately sits on a road
# must be drawn ON TOP of it (higher draw-order z), never have the road painted over it.


def _seg_0168__road_layers() -> dict[str, Any]:
    """Gate segment 168 (road_layers) - body verbatim from the legacy gate() (feature 022)."""
    road_layers = []  # type: ignore[var-annotated]
    return _kept(locals(), ('road_layers',))


def _seg_0169__road_layers_1(*, M: Any = _UNBOUND, road_layers: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 169 (road_layers) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("road") is not None and M.get("road_z") is not None:
        road_layers.append((M["road"], M["road_z"], M.get("road_width", 26) / 2))
    return _kept(locals(), ('road_layers',))


def _seg_0170__road_layers_2(*, M: Any = _UNBOUND, road_layers: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 170 (road_layers, st) - body verbatim from the legacy gate() (feature 022)."""
    road_layers += [(st["pts"], st["z"], st["w"] / 2) for st in M.get("town_streets", []) if "z" in st]
    return _kept(locals(), ('road_layers', 'st'))


def _seg_0171__lab(*, M: Any = _UNBOUND, lab: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 171 (lab, overlays) - body verbatim from the legacy gate() (feature 022)."""
    overlays = [("label", label_aabb(lab), lab[4]) for lab in M.get("labels", []) if len(lab) > 4]
    return _kept(locals(), ('lab', 'overlays'))


def _seg_0172__gs(*, M: Any = _UNBOUND, gs: Any = _UNBOUND, overlays: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 172 (gs, overlays) - body verbatim from the legacy gate() (feature 022)."""
    overlays += [("gatehouse", (gs["x"] - gs["w"] / 2, gs["y"] - gs["h"] / 2, gs["x"] + gs["w"] / 2, gs["y"] + gs["h"] / 2), gs["z"]) for gs in M.get("gate_structs", []) if "z" in gs]
    return _kept(locals(), ('gs', 'overlays'))


def _seg_0173__line_hits_box(
    *,
    ax: Any = _UNBOUND,
    ay: Any = _UNBOUND,
    box: Any = _UNBOUND,
    bx: Any = _UNBOUND,
    bx0: Any = _UNBOUND,
    bx1: Any = _UNBOUND,
    by: Any = _UNBOUND,
    by0: Any = _UNBOUND,
    by1: Any = _UNBOUND,
    j: Any = _UNBOUND,
    k: Any = _UNBOUND,
    pad: Any = _UNBOUND,
    poly: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    steps: Any = _UNBOUND,
    t: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 173 (line_hits_box) - body verbatim from the legacy gate() (feature 022)."""

    def line_hits_box(poly: Poly, box: tuple[float, float, float, float], pad: float) -> bool:
        bx0, by0, bx1, by1 = box
        for k in range(len(poly) - 1):
            (ax, ay), (bx, by) = poly[k], poly[k + 1]
            steps = max(1, int(math.hypot(bx - ax, by - ay) // 8))
            for j in range(steps + 1):
                t = j / steps
                px, py = ax + (bx - ax) * t, ay + (by - ay) * t
                if bx0 - pad <= px <= bx1 + pad and by0 - pad <= py <= by1 + pad:
                    return True
        return False

    return _kept(locals(), ('line_hits_box',))


def _seg_0174__bad_z(
    *,
    box: Any = _UNBOUND,
    hw: Any = _UNBOUND,
    line_hits_box: Any = _UNBOUND,
    name: Any = _UNBOUND,
    overlays: Any = _UNBOUND,
    oz: Any = _UNBOUND,
    poly: Any = _UNBOUND,
    road_layers: Any = _UNBOUND,
    rz: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 174 (bad_z, box, hw, name) - body verbatim from the legacy gate() (feature 022)."""
    bad_z = [name for poly, rz, hw in road_layers for name, box, oz in overlays if rz > oz and line_hits_box(poly, box, hw)]
    return _kept(locals(), ('bad_z', 'box', 'hw', 'name', 'oz', 'poly', 'rz'))


def _seg_0175__roads_drawn_under_overlays(*, bad_z: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 175 (roads_drawn_under_overlays) - body verbatim from the legacy gate() (feature 022)."""
    check("roads_drawn_under_overlays", not bad_z, f"{len(bad_z)} road/street drawn OVER a gatehouse/label it should pass under: {sorted(set(bad_z))}")
    return _kept(locals(), ())


# LANE LAYERING: where two linear ground features cross, the WIDER renders on top (higher draw z).
# The Imperial road is painted over the city streets it crosses, streets over the alleys they cross.
# z is the recorded final draw position (settlement flushes road/street/alley as one ordered block).


def _seg_0176__lanes() -> dict[str, Any]:
    """Gate segment 176 (lanes) - body verbatim from the legacy gate() (feature 022)."""
    lanes = []  # type: ignore[var-annotated]
    return _kept(locals(), ('lanes',))


def _seg_0177__lanes_1(*, M: Any = _UNBOUND, lanes: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 177 (lanes) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("road") and M.get("road_z") is not None:
        lanes.append(("road", M["road"], M.get("road_width", 26), M["road_z"]))
    return _kept(locals(), ('lanes',))


def _seg_0178__lanes_2(*, M: Any = _UNBOUND, lanes: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 178 (lanes, st) - body verbatim from the legacy gate() (feature 022)."""
    lanes += [("street", st["pts"], st["w"], st["z"]) for st in M.get("town_streets", []) if st.get("z") is not None]
    return _kept(locals(), ('lanes', 'st'))


def _seg_0179__a(*, M: Any = _UNBOUND, a: Any = _UNBOUND, lanes: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 179 (a, lanes) - body verbatim from the legacy gate() (feature 022)."""
    lanes += [("alley", a["pts"], a.get("w", 10), a["z"]) for a in M.get("alleys", []) if a.get("z") is not None]
    return _kept(locals(), ('a', 'lanes'))


def _seg_0180__lanes_cross(*, a: Any = _UNBOUND, b: Any = _UNBOUND, pi: Any = _UNBOUND, pj: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 180 (lanes_cross) - body verbatim from the legacy gate() (feature 022)."""

    def lanes_cross(pi: Poly, pj: Poly) -> bool:
        return any(segments_cross(pi[a], pi[a + 1], pj[b], pj[b + 1]) for a in range(len(pi) - 1) for b in range(len(pj) - 1))

    return _kept(locals(), ('lanes_cross',))


def _seg_0181__mislayered() -> dict[str, Any]:
    """Gate segment 181 (mislayered) - body verbatim from the legacy gate() (feature 022)."""
    mislayered = []  # type: ignore[var-annotated]
    return _kept(locals(), ('mislayered',))


def _seg_0182__i(
    *,
    i: Any = _UNBOUND,
    j: Any = _UNBOUND,
    lanes: Any = _UNBOUND,
    lanes_cross: Any = _UNBOUND,
    mislayered: Any = _UNBOUND,
    narrower: Any = _UNBOUND,
    ni: Any = _UNBOUND,
    nj: Any = _UNBOUND,
    pi: Any = _UNBOUND,
    pj: Any = _UNBOUND,
    wi: Any = _UNBOUND,
    wider: Any = _UNBOUND,
    wj: Any = _UNBOUND,
    zi: Any = _UNBOUND,
    zj: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 182 (i, j, mislayered, narrower) - body verbatim from the legacy gate() (feature 022)."""
    for i in range(len(lanes)):
        for j in range(i + 1, len(lanes)):
            ni, pi, wi, zi = lanes[i]
            nj, pj, wj, zj = lanes[j]
            if abs(wi - wj) < 1 or not lanes_cross(pi, pj):
                continue  # same width (either order ok) or they don't cross
            wider, narrower = ((ni, zi), (nj, zj)) if wi > wj else ((nj, zj), (ni, zi))
            if wider[1] < narrower[1]:
                mislayered.append(f"{narrower[0]} over {wider[0]}")
    return _kept(locals(), ('i', 'j', 'mislayered', 'narrower', 'ni', 'nj', 'pi', 'pj', 'wi', 'wider', 'wj', 'zi', 'zj'))


def _seg_0183__city_lanes_layered_by_width(*, check: Any = _UNBOUND, mislayered: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 183 (city_lanes_layered_by_width) - body verbatim from the legacy gate() (feature 022)."""
    check("city_lanes_layered_by_width", not mislayered, f"a narrower lane is painted OVER a wider one it crosses (the wider lane must be on top): {sorted(set(mislayered))}")
    return _kept(locals(), ())


# where lanes meet they form a clean CROSSROADS: the paved BEDS merge into a continuous surface, with
# no lane's EDGE (its dark curb-line) cutting across another lane's bed at the junction. The engine
# draws the ground block in sub-layers - all edges, then all beds, then center-marks - so every edge
# sits below every bed; the check guards that invariant (max edge draw-z < min bed draw-z).


def _seg_0184__bz(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 184 (bz, ez) - body verbatim from the legacy gate() (feature 022)."""
    ez, bz = M.get("ground_edge_zmax"), M.get("ground_bed_zmin")
    return _kept(locals(), ('bz', 'ez'))


def _seg_0185__intersections_are_crossroads(*, bz: Any = _UNBOUND, check: Any = _UNBOUND, ez: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 185 (intersections_are_crossroads) - body verbatim from the legacy gate() (feature 022)."""
    if ez is not None and bz is not None:
        check(
            "intersections_are_crossroads",
            ez < bz,
            "lane edge-strokes render OVER bed-strokes, so a junction shows a line across it instead of a merged crossroads - draw all ground edges below all ground beds",
        )
    return _kept(locals(), ())


# WALLS render OVER the ground lanes: a road/street/alley that runs INTO a wall - touches or crosses
# its stroke - must pass UNDER it (the wall has a higher draw z). The settlement draws ramparts in a
# dedicated WALL layer above the ground block precisely so this holds; the check guards the invariant
# for the city/town wall AND every neighborhood (ward) fence. A lane only breaches a wall at a GATE,
# where the wall has a genuine opening (no stroke to render over), so crossings/touches at a gate are
# exempt. The wall is a closed ring at city scale, an open hill-anchored arc at town scale.


def _seg_0186__bad_1(
    *,
    a: Any = _UNBOUND,
    b: Any = _UNBOUND,
    bad: Any = _UNBOUND,
    bz: Any = _UNBOUND,
    ex: Any = _UNBOUND,
    ey: Any = _UNBOUND,
    k: Any = _UNBOUND,
    lanes: Any = _UNBOUND,
    name: Any = _UNBOUND,
    near: Any = _UNBOUND,
    p: Any = _UNBOUND,
    pts: Any = _UNBOUND,
    ring: Any = _UNBOUND,
    w: Any = _UNBOUND,
    x: Any = _UNBOUND,
    y: Any = _UNBOUND,
    z: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 186 (bad, lanes_over) - body verbatim from the legacy gate() (feature 022)."""

    def lanes_over(ring: Poly, bz: float, closed: bool, exempt: Sequence[Pt], near: float = 6.0) -> list[str]:
        edges = [(ring[k], ring[(k + 1) % len(ring)]) for k in (range(len(ring)) if closed else range(len(ring) - 1))]

        def at_gate(x: float, y: float) -> bool:
            return any(math.hypot(x - ex, y - ey) < 50 for ex, ey in exempt)

        bad: list[str] = []
        for name, pts, w, z in lanes:
            if z < bz:
                continue  # the lane already renders under this wall
            meets = any(seg_dist(p[0], p[1], a, b) < near + w / 2 and not at_gate(p[0], p[1]) for p in pts for a, b in edges)
            for k in range(len(pts) - 1):
                for a, b in edges:
                    if segments_cross(pts[k], pts[k + 1], a, b):
                        xy = seg_intersect(pts[k], pts[k + 1], a, b)
                        if xy and not at_gate(xy[0], xy[1]):
                            meets = True
            if meets:
                bad.append(name)
        return sorted(set(bad))

    return _kept(locals(), ('bad', 'lanes_over'))


def _seg_0187__wall(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 187 (wall, wall_z) - body verbatim from the legacy gate() (feature 022)."""
    wall, wall_z = M.get("wall"), M.get("wall_z")
    return _kept(locals(), ('wall', 'wall_z'))


def _seg_0188__gates(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 188 (gates) - body verbatim from the legacy gate() (feature 022)."""
    gates = M.get("gates") or ([M["gate"]] if M.get("gate") else [])
    return _kept(locals(), ('gates',))


def _seg_0189__city_lane_under_wall(
    *, check: Any = _UNBOUND, gates: Any = _UNBOUND, lanes_over: Any = _UNBOUND, over_wall: Any = _UNBOUND, scale: Any = _UNBOUND, wall: Any = _UNBOUND, wall_z: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 189 (city_lane_under_wall) - body verbatim from the legacy gate() (feature 022)."""
    if wall and wall_z is not None and len(wall) >= 3:
        over_wall = lanes_over(list(wall), wall_z, scale == "city", gates)
        check(
            "city_lane_under_wall",
            not over_wall,
            f"a road/street/alley runs INTO the city wall and renders OVER it - a lane must pass UNDER the rampart (it shows through only at a gate opening): {over_wall}",
        )
    return _kept(locals(), ('over_wall',))


def _seg_0190__k_2(*, M: Any = _UNBOUND, k: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 190 (k, kido_pts) - body verbatim from the legacy gate() (feature 022)."""
    kido_pts = [(k["x"], k["y"]) for k in M.get("kido", [])]
    return _kept(locals(), ('k', 'kido_pts'))


def _seg_0191__over_fence() -> dict[str, Any]:
    """Gate segment 191 (over_fence) - body verbatim from the legacy gate() (feature 022)."""
    over_fence = []  # type: ignore[var-annotated]
    return _kept(locals(), ('over_fence',))


def _seg_0192__n(*, M: Any = _UNBOUND, kido_pts: Any = _UNBOUND, lanes_over: Any = _UNBOUND, n: Any = _UNBOUND, over_fence: Any = _UNBOUND, wd: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 192 (n, over_fence, wd) - body verbatim from the legacy gate() (feature 022)."""
    for wd in M.get("wards", []):
        if wd.get("z") is not None and len(wd.get("boundary", [])) >= 2:
            over_fence += [(wd.get("name", "ward"), n) for n in lanes_over(wd["boundary"], wd["z"], False, kido_pts)]
    return _kept(locals(), ('n', 'over_fence', 'wd'))


def _seg_0193__city_lanes_under_ward_fences(*, check: Any = _UNBOUND, over_fence: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 193 (city_lanes_under_ward_fences) - body verbatim from the legacy gate() (feature 022)."""
    check("city_lanes_under_ward_fences", not over_fence, f"a lane runs into a neighborhood (ward) fence and renders OVER it - lanes pass UNDER the fence (the kido marks the passage): {over_fence}")
    return _kept(locals(), ())


# NO DOUBLED WALL: the short wall-stroke CAP that plugs a ward fence into the rampart must lie FLUSH
# along the wall, not jut across it. A straight cap tangent to one segment, laid at a wall CORNER, juts
# past the bend and reads as a second wall section overlapping the first (Nagahara SW, GM 2026-07). The
# cap is now drawn to FOLLOW the wall (arc +/-16 px through any vertex in the span); this guards the
# invariant so a regression to a straight-tangent cap is caught. Every cap vertex must sit within
# tolerance of the wall polyline.


def _seg_0194___wall_ring(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 194 (_wall_ring) - body verbatim from the legacy gate() (feature 022)."""
    _wall_ring = M.get("wall")
    return _kept(locals(), ('_wall_ring',))


def _seg_0195__city_ward_cap_flush_to_wall(
    *,
    M: Any = _UNBOUND,
    _d: Any = _UNBOUND,
    _off: Any = _UNBOUND,
    _ring: Any = _UNBOUND,
    _wall_ring: Any = _UNBOUND,
    _wrng: Any = _UNBOUND,
    cap: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cx3: Any = _UNBOUND,
    cy3: Any = _UNBOUND,
    i: Any = _UNBOUND,
    wd: Any = _UNBOUND,
    x: Any = _UNBOUND,
    y: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 195 (city_ward_cap_flush_to_wall) - body verbatim from the legacy gate() (feature 022)."""
    if _wall_ring:
        _wrng = [(x, y) for x, y in _wall_ring]
        _ring = _wrng + [_wrng[0]]
        _off = []
        for wd in M.get("wards", []):
            for cap in wd.get("wall_caps", []):
                for cx3, cy3 in cap.get("pts", []):
                    _d = min(seg_dist(cx3, cy3, _ring[i], _ring[i + 1]) for i in range(len(_ring) - 1))
                    if _d > 4.0:  # a flush cap sits ON the wall (~0-1 px); >4 px means it juts across the bend
                        _off.append((round(cx3), round(cy3), round(_d, 1)))
        check(
            "city_ward_cap_flush_to_wall",
            not _off,
            f"ward fence wall-cap vertex/vertices jut off the rampart (x, y, px-off-wall): {_off[:4]} - the cap plugs the "
            f"fence into the wall and must lie FLUSH along it (follow the wall through any corner), not cross it as a "
            f"straight stub - which renders as two wall sections overlapping instead of one bent wall (settlement.ward)",
        )
    return _kept(locals(), ('_d', '_off', '_ring', '_wrng', 'cap', 'cx3', 'cy3', 'i', 'wd', 'x', 'y'))


# JOIN, DON'T INTERSECT - the WALL member of a family the ways and the watercourses already had
# (GM 2026-07-27, on Minami: "the neighborhood walls stick out the other side of the city walls").
# Where two linear features meet, one of them ENDS at the junction: a lane terminates at the
# through-lane it reaches rather than poking a stub out the far side
# (city_streets_no_intersection_stub, city_streets_meet_through_lanes), and a watercourse joins at
# a T or a Y rather than crossing (water_channels_join_not_cross, channels_join_water_not_cross).
# A neighborhood (ward) fence meeting the city rampart is the same junction and was the one member
# of the family nobody had stated: the fence ENDS at the wall, because the wall is what seals it -
# a palisade continuing out through the rampart into the fields encloses nothing and reads as two
# walls crossing at an intersection.
#
# city_ward_fence_meets_wall is the mirror rule (the UNDERSHOOT - a gap the commoners walk around)
# and deliberately allows ~10px of slop in EITHER direction, which is why this defect shipped
# green: Minami's two fence ends sat 4.2 and 4.9px OUTSIDE the wall ring, well inside that
# tolerance. The overshoot has to be measured against the DRAWN ink instead, and it is small
# numbers all the way down - the rampart's stroke covers only its own half-width (11/2 = 5.5px),
# while the fence is stroked with a ROUND LINECAP that inks half a stroke-width (5/2 = 2.5px) past
# its last recorded vertex. So 4.9 + 2.5 = 7.4px of fence against 5.5px of wall left a ~2px tan
# nub outside the rampart - at a city's 1px = 3ft, about 6ft of palisade standing in the moat
# berm. Both widths come from the engine's own records (M['wall_stroke'], the ward's 'stroke') so
# placement and check read the same source; the literals are the fallback for manifests written
# before those records existed.


def _seg_0196__city_ward_fence_joins_wall_not_crosses(
    *,
    M: Any = _UNBOUND,
    _bnd: Any = _UNBOUND,
    _cap: Any = _UNBOUND,
    _dl: Any = _UNBOUND,
    _dx: Any = _UNBOUND,
    _dy: Any = _UNBOUND,
    _i: Any = _UNBOUND,
    _in: Any = _UNBOUND,
    _out: Any = _UNBOUND,
    _poke: Any = _UNBOUND,
    _probes: Any = _UNBOUND,
    _ring: Any = _UNBOUND,
    _tx: Any = _UNBOUND,
    _ty: Any = _UNBOUND,
    _vi: Any = _UNBOUND,
    _vx: Any = _UNBOUND,
    _vy: Any = _UNBOUND,
    _wall_half: Any = _UNBOUND,
    _wall_ring: Any = _UNBOUND,
    _wrng: Any = _UNBOUND,
    check: Any = _UNBOUND,
    p: Any = _UNBOUND,
    wd: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 196 (city_ward_fence_joins_wall_not_crosses) - body verbatim from the legacy gate() (feature 022)."""
    if _wall_ring:
        _wall_half = float(M.get("wall_stroke", 11.0)) / 2
        _poke = []
        for wd in M.get("wards", []):
            _bnd = [(p[0], p[1]) for p in wd.get("boundary", [])]
            if len(_bnd) < 2:
                continue
            _cap = float(wd.get("stroke", 5.0)) / 2  # the round linecap inks this far past the tip
            # probe every vertex; the two ENDS are pushed out by the cap radius along their own
            # terminal segment, so what is tested is the ink, not the recorded coordinate. Interior
            # vertices are probed bare - a fence that dives out through the rampart and back mid-run
            # is the same crossing, just further from the end.
            _probes: list[tuple[float, float]] = []  # type: ignore[no-redef]
            for _vi, (_vx, _vy) in enumerate(_bnd):
                _in = _bnd[1] if _vi == 0 else _bnd[-2] if _vi == len(_bnd) - 1 else None
                if _in is None:
                    _probes.append((_vx, _vy))
                    continue
                _dx, _dy = _vx - _in[0], _vy - _in[1]
                _dl = math.hypot(_dx, _dy) or 1.0
                _probes.append((_vx + _dx / _dl * _cap, _vy + _dy / _dl * _cap))
            for _tx, _ty in _probes:
                _out = min(seg_dist(_tx, _ty, _ring[_i], _ring[_i + 1]) for _i in range(len(_ring) - 1)) - _wall_half
                if _out > 0 and not point_in_poly(_tx, _ty, _wrng):
                    _poke.append((round(_tx), round(_ty), round(_out, 1)))
        check(
            "city_ward_fence_joins_wall_not_crosses",
            not _poke,
            f"neighborhood (ward) fence ink OUTSIDE the city wall (x, y, px past the rampart's outer face): {_poke[:4]} - "
            f"a ward fence JOINS the rampart, it does not cross it: the fence ENDS where the wall seals it, so no part of "
            f"the palisade may stick out the far side into the berm. Same rule the lanes and the watercourses follow "
            f"(city_streets_no_intersection_stub, water_channels_join_not_cross). Snap the fence's end vertex onto the "
            f"wall centerline - s.ward does this automatically, so a hit here means the end was placed out of its reach",
        )
    return _kept(locals(), ('_bnd', '_cap', '_dl', '_dx', '_dy', '_i', '_in', '_out', '_poke', '_probes', '_tx', '_ty', '_vi', '_vx', '_vy', '_wall_half', 'p', 'wd'))


# A walled COMPOUND (mausoleum / manor) whose wall sits ALONG a neighborhood (ward) fence must
# YIELD that wall to the fence: the fence is re-stamped on top and IS that side of the compound,
# so there is no doubled, clashing parallel wall (s.mausoleum / s.manor do this automatically and
# record the yielded sides in "ward_walls"). Verify every geometric abutment is recorded.


def _seg_0197__walled_structure_yields_to_ward_wall(
    *,
    M: Any = _UNBOUND,
    _wall_along_fence: Any = _UNBOUND,
    a: Any = _UNBOUND,
    ax: Any = _UNBOUND,
    ay: Any = _UNBOUND,
    b: Any = _UNBOUND,
    bnd: Any = _UNBOUND,
    bx: Any = _UNBOUND,
    by: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    h: Any = _UNBOUND,
    k: Any = _UNBOUND,
    name: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    qx: Any = _UNBOUND,
    qy: Any = _UNBOUND,
    recorded: Any = _UNBOUND,
    s: Any = _UNBOUND,
    sides: Any = _UNBOUND,
    tol: Any = _UNBOUND,
    unyielded: Any = _UNBOUND,
    w: Any = _UNBOUND,
    wall_ring: Any = _UNBOUND,
    wd: Any = _UNBOUND,
    x0: Any = _UNBOUND,
    x1: Any = _UNBOUND,
    y0: Any = _UNBOUND,
    y1: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 197 (walled_structure_yields_to_ward_wall) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("wards"):

        def _wall_along_fence(a: Pt, b: Pt, tol: float = 16) -> bool:
            ax, ay = a
            bx, by = b
            horiz = abs(ax - bx) >= abs(ay - by)
            for wd in M["wards"]:
                bnd = wd.get("boundary", [])
                for k in range(len(bnd) - 1):
                    px, py = bnd[k]
                    qx, qy = bnd[k + 1]
                    if (abs(px - qx) >= abs(py - qy)) != horiz:  # fence segment must run the same way
                        continue
                    if horiz and abs(py - ay) <= tol and min(max(ax, bx), max(px, qx)) - max(min(ax, bx), min(px, qx)) >= 10:
                        return True
                    if not horiz and abs(px - ax) <= tol and min(max(ay, by), max(py, qy)) - max(min(ay, by), min(py, qy)) >= 10:
                        return True
            return False

        wall_ring = M.get("wall")
        unyielded = []
        for s in M.get("mausoleums", []) + M.get("manors", []):
            if s.get("rot", 0):
                continue  # tilted compound: not axis-aligned to a fence
            if wall_ring and not point_in_poly(s["x"], s["y"], wall_ring):
                continue  # only compounds INSIDE the city
            cx, cy, w, h = s["x"], s["y"], s["w"], s["h"]
            x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
            sides = {"north": ((x0, y0), (x1, y0)), "south": ((x0, y1), (x1, y1)), "west": ((x0, y0), (x0, y1)), "east": ((x1, y0), (x1, y1))}
            recorded = set(s.get("ward_walls", []))
            for name, (a, b) in sides.items():
                if name != s.get("gate_dir") and _wall_along_fence(a, b) and name not in recorded:
                    unyielded.append((round(cx), round(cy), name))
        check(
            "walled_structure_yields_to_ward_wall",
            not unyielded,
            f"walled compound(s) draw their own wall OVER a neighborhood (ward) fence instead of yielding to it: {unyielded[:3]} - "
            f"where a mausoleum/manor wall abuts a ward fence, the FENCE is that side's wall (render the compound's wall UNDER it); "
            f"s.mausoleum / s.manor do this automatically and record the yielded sides in 'ward_walls'",
        )
    return _kept(locals(), ('_wall_along_fence', 'a', 'b', 'cx', 'cy', 'h', 'name', 'recorded', 's', 'sides', 'unyielded', 'w', 'wall_ring', 'x0', 'x1', 'y0', 'y1'))


# no structure overlaps the (wide) road


def _seg_0198__road(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 198 (road) - body verbatim from the legacy gate() (feature 022)."""
    road: Any = M.get("road")
    return _kept(locals(), ('road',))


def _seg_0199__no_structure_on_road(
    *,
    M: Any = _UNBOUND,
    bad_r: Any = _UNBOUND,
    check: Any = _UNBOUND,
    corners: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    e: Any = _UNBOUND,
    k: Any = _UNBOUND,
    on_road: Any = _UNBOUND,
    road: Any = _UNBOUND,
    rw: Any = _UNBOUND,
    rx: Any = _UNBOUND,
    ry: Any = _UNBOUND,
    sc: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 199 (no_structure_on_road) - body verbatim from the legacy gate() (feature 022)."""
    if road:
        rw = M.get("road_width", 26) / 2 + 2  # roadbed half-width + a little

        def on_road(sc: Poly) -> bool:
            if any(seg_dist(cx, cy, road[k], road[k + 1]) < rw for (cx, cy) in sc for k in range(len(road) - 1)):
                return True
            if any(point_in_poly(rx, ry, sc) for (rx, ry) in road):
                return True
            return any(segments_cross(road[k], road[k + 1], sc[e], sc[(e + 1) % 4]) for k in range(len(road) - 1) for e in range(4))

        bad_r = [1 for sc in corners if on_road(sc)]
        check("no_structure_on_road", not bad_r, f"{len(bad_r)} structure(s) overlap the road")
    return _kept(locals(), ('bad_r', 'on_road', 'rw', 'sc'))


# no structure overlaps a stream


def _seg_0200__streams(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 200 (streams) - body verbatim from the legacy gate() (feature 022)."""
    streams = M.get("streams", [])
    return _kept(locals(), ('streams',))


def _seg_0201__no_structure_on_stream(
    *,
    bad_s: Any = _UNBOUND,
    check: Any = _UNBOUND,
    corners: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    e: Any = _UNBOUND,
    k: Any = _UNBOUND,
    on_stream: Any = _UNBOUND,
    rx: Any = _UNBOUND,
    ry: Any = _UNBOUND,
    sc: Any = _UNBOUND,
    sp: Any = _UNBOUND,
    srw: Any = _UNBOUND,
    st: Any = _UNBOUND,
    streams: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 201 (no_structure_on_stream) - body verbatim from the legacy gate() (feature 022)."""
    if streams:
        srw = 6  # stream half-width + a little

        def on_stream(sc: Poly, sp: Poly) -> bool:
            if any(seg_dist(cx, cy, sp[k], sp[k + 1]) < srw for (cx, cy) in sc for k in range(len(sp) - 1)):
                return True
            if any(point_in_poly(rx, ry, sc) for rx, ry in sp):
                return True
            return any(segments_cross(sp[k], sp[k + 1], sc[e], sc[(e + 1) % 4]) for k in range(len(sp) - 1) for e in range(4))

        bad_s = [1 for sc in corners for st in streams if on_stream(sc, st["poly"])]
        check("no_structure_on_stream", not bad_s, f"{len(bad_s)} structure(s) overlap a stream")
    return _kept(locals(), ('bad_s', 'on_stream', 'sc', 'srw', 'st'))


# no structure overlaps an irrigation channel - the SAME full-footprint test as a stream.
# (houses_off_corridors below also touches channels, but only by house CENTER distance, so a
# channel clipping a farmhouse's corner while its center stayed clear used to slip through.)


def _seg_0202__channels_struct(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 202 (channels_struct) - body verbatim from the legacy gate() (feature 022)."""
    channels_struct = M.get("channels", [])
    return _kept(locals(), ('channels_struct',))


def _seg_0203__no_structure_on_channel(
    *,
    bad_c: Any = _UNBOUND,
    c: Any = _UNBOUND,
    channels_struct: Any = _UNBOUND,
    check: Any = _UNBOUND,
    corners: Any = _UNBOUND,
    crw: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    e: Any = _UNBOUND,
    k: Any = _UNBOUND,
    on_channel: Any = _UNBOUND,
    rx: Any = _UNBOUND,
    ry: Any = _UNBOUND,
    sc: Any = _UNBOUND,
    sp: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 203 (no_structure_on_channel) - body verbatim from the legacy gate() (feature 022)."""
    if channels_struct:
        crw = 5  # channel half-width (hairline stroke ~2.5 -> ~1.25) + a little: a corner this close is on it

        def on_channel(sc: Poly, sp: Poly) -> bool:
            if any(seg_dist(cx, cy, sp[k], sp[k + 1]) < crw for (cx, cy) in sc for k in range(len(sp) - 1)):
                return True
            if any(point_in_poly(rx, ry, sc) for rx, ry in sp):
                return True
            return any(segments_cross(sp[k], sp[k + 1], sc[e], sc[(e + 1) % 4]) for k in range(len(sp) - 1) for e in range(4))

        bad_c = [1 for sc in corners for c in channels_struct if on_channel(sc, c["poly"])]
        check("no_structure_on_channel", not bad_c, f"{len(bad_c)} structure(s) overlap an irrigation channel")
    return _kept(locals(), ('bad_c', 'c', 'crw', 'on_channel', 'sc'))


# no structure overlaps the navigable CARGO CANAL - the same full-footprint test as a channel,
# but the canal is a WIDER watercourse (a poling barge, not a field ditch), so its half-width is
# honored. A merchant house / warehouse fronts the quay but must not stand IN the water (GM,
# 2026-07: a merchant_large sat on Nagahara's canal - there was no canal-vs-struct check at all,
# this being the first city with a canal). Jetties/water-gates/bridges legitimately cross it (EXEMPT).


def _seg_0204__canals_struct(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 204 (canals_struct) - body verbatim from the legacy gate() (feature 022)."""
    canals_struct = M.get("canals", [])
    return _kept(locals(), ('canals_struct',))


def _seg_0205__no_structure_on_canal(
    *,
    bad_cn: Any = _UNBOUND,
    c: Any = _UNBOUND,
    canals_struct: Any = _UNBOUND,
    check: Any = _UNBOUND,
    chw: Any = _UNBOUND,
    corners: Any = _UNBOUND,
    cp: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    e: Any = _UNBOUND,
    k: Any = _UNBOUND,
    on_canal: Any = _UNBOUND,
    rx: Any = _UNBOUND,
    ry: Any = _UNBOUND,
    sc: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 205 (no_structure_on_canal) - body verbatim from the legacy gate() (feature 022)."""
    if canals_struct:

        def on_canal(sc: Poly, cp: Poly, chw: float) -> bool:
            if any(seg_dist(cx, cy, cp[k], cp[k + 1]) < chw for (cx, cy) in sc for k in range(len(cp) - 1)):
                return True
            if any(point_in_poly(rx, ry, sc) for rx, ry in cp):
                return True
            return any(segments_cross(cp[k], cp[k + 1], sc[e], sc[(e + 1) % 4]) for k in range(len(cp) - 1) for e in range(4))

        bad_cn = [1 for sc in corners for c in canals_struct if on_canal(sc, c["poly"], c.get("w", 12) / 2 + 2)]
        check("no_structure_on_canal", not bad_cn, f"{len(bad_cn)} structure(s) overlap the cargo canal")
    return _kept(locals(), ('bad_cn', 'c', 'on_canal', 'sc'))


# no structure overlaps the town wall (the thick rampart stroke)


def _seg_0206__wallpts(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 206 (wallpts) - body verbatim from the legacy gate() (feature 022)."""
    wallpts = M.get("wall")
    return _kept(locals(), ('wallpts',))


def _seg_0207__no_structure_on_wall(
    *,
    bad_w: Any = _UNBOUND,
    check: Any = _UNBOUND,
    corners: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    e: Any = _UNBOUND,
    k: Any = _UNBOUND,
    on_wall: Any = _UNBOUND,
    sc: Any = _UNBOUND,
    wallpts: Any = _UNBOUND,
    ww: Any = _UNBOUND,
    wx: Any = _UNBOUND,
    wy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 207 (no_structure_on_wall) - body verbatim from the legacy gate() (feature 022)."""
    if wallpts:
        ww = 9  # wall half-width (stroke ~10) + a little

        def on_wall(sc: Poly) -> bool:
            if any(seg_dist(cx, cy, wallpts[k], wallpts[k + 1]) < ww for (cx, cy) in sc for k in range(len(wallpts) - 1)):
                return True
            if any(point_in_poly(wx, wy, sc) for wx, wy in wallpts):
                return True
            return any(segments_cross(wallpts[k], wallpts[k + 1], sc[e], sc[(e + 1) % 4]) for k in range(len(wallpts) - 1) for e in range(4))

        bad_w = [1 for sc in corners if on_wall(sc)]
        check("no_structure_on_wall", not bad_w, f"{len(bad_w)} structure(s) overlap the town wall")
    return _kept(locals(), ('bad_w', 'on_wall', 'sc', 'ww'))


# no structure overlaps the MOAT (the water ring outside the wall) - extramural structures (the
# common burial ground, the cremation ground, the ossuary, samurai estates) must keep clear of it


def _seg_0208__moatpts(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 208 (moatpts) - body verbatim from the legacy gate() (feature 022)."""
    moatpts = M.get("moat")
    return _kept(locals(), ('moatpts',))


def _seg_0209__no_structure_on_moat(
    *,
    M: Any = _UNBOUND,
    bad_mo: Any = _UNBOUND,
    check: Any = _UNBOUND,
    corners: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    e: Any = _UNBOUND,
    k: Any = _UNBOUND,
    mhw: Any = _UNBOUND,
    moatpts: Any = _UNBOUND,
    on_moat: Any = _UNBOUND,
    sc: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 209 (no_structure_on_moat) - body verbatim from the legacy gate() (feature 022)."""
    if moatpts:
        mhw = M.get("moat_width", 26) / 2 + 4

        def on_moat(sc: Poly) -> bool:
            if any(seg_dist(cx, cy, moatpts[k], moatpts[k + 1]) < mhw for (cx, cy) in sc for k in range(len(moatpts) - 1)):
                return True
            if any(point_in_poly(mx, my, sc) for mx, my in moatpts):
                return True
            return any(segments_cross(moatpts[k], moatpts[k + 1], sc[e], sc[(e + 1) % 4]) for k in range(len(moatpts) - 1) for e in range(4))

        bad_mo = [1 for sc in corners if on_moat(sc)]
        check("no_structure_on_moat", not bad_mo, f"{len(bad_mo)} structure(s) overlap the moat")
    return _kept(locals(), ('bad_mo', 'mhw', 'on_moat', 'sc'))


# no structure overlaps the POND (the irrigation reservoir / in-wall water source). The pond is
# the one water body that was never in this section: streams/channels/moat all have their clause
# above, but a struct standing IN the pond slipped through (Tango's west fire tower landed on the
# pond rim). Village ponds are auto-placed clear of everything, so this only ever bites hand-placed
# structs - which is exactly when a check is needed. The pond is a true ellipse [cx, cy, rx, ry];
# a footprint hits it if any sampled boundary point (corners + edge quarter-points, enough for
# struct-sized rects vs a pond-sized ellipse) dips inside the rim, or the rect swallows the center.


def _seg_0210__pond_st(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 210 (pond_st) - body verbatim from the legacy gate() (feature 022)."""
    pond_st = M.get("pond")
    return _kept(locals(), ('pond_st',))


def _seg_0211__no_structure_on_pond(
    *,
    bad_p: Any = _UNBOUND,
    check: Any = _UNBOUND,
    corners: Any = _UNBOUND,
    e: Any = _UNBOUND,
    on_pond: Any = _UNBOUND,
    pe: Any = _UNBOUND,
    pond_st: Any = _UNBOUND,
    pts: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    sc: Any = _UNBOUND,
    t: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 211 (no_structure_on_pond) - body verbatim from the legacy gate() (feature 022)."""
    if pond_st:
        pe = [pond_st[0], pond_st[1], pond_st[2] + 3, pond_st[3] + 3]  # rim stroke (2.4) half-width + a little

        def on_pond(sc: Poly) -> bool:
            if point_in_poly(pond_st[0], pond_st[1], sc):
                return True
            pts = [(sc[e][0] + (sc[(e + 1) % 4][0] - sc[e][0]) * t, sc[e][1] + (sc[(e + 1) % 4][1] - sc[e][1]) * t) for e in range(4) for t in (0.0, 0.25, 0.5, 0.75)]
            return any(in_ellipse(px, py, pe) for px, py in pts)

        bad_p = [1 for sc in corners if on_pond(sc)]
        check("no_structure_on_pond", not bad_p, f"{len(bad_p)} structure(s) overlap the pond")
    return _kept(locals(), ('bad_p', 'on_pond', 'pe', 'sc'))


# no structure stands ON a rice paddy - the long-missing member of this family (GM, Hoshizora
# 2026-07: the legacy house-first placement tested only the CENTER +14px against the field, so a
# town-scale 44px farmhouse could sink a corner ~12px into the crop while every village's 23px
# houses stayed clear by luck of the grain). A corner is IN the paddy only when it penetrates
# deeper than 3px past the outline - bund-hugging abutment (and the organic outline's stroke)
# stays legal.


def _seg_0212__f(*, M: Any = _UNBOUND, f: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 212 (f, paddy_ol_st) - body verbatim from the legacy gate() (feature 022)."""
    paddy_ol_st = [f["outline"] for f in M.get("fields", []) if f.get("kind") == "paddy"]
    return _kept(locals(), ('f', 'paddy_ol_st'))


def _seg_0213__no_structure_on_paddy(
    *,
    M: Any = _UNBOUND,
    _pol_bb: Any = _UNBOUND,
    bad_pd: Any = _UNBOUND,
    bx0: Any = _UNBOUND,
    bx1: Any = _UNBOUND,
    by0: Any = _UNBOUND,
    by1: Any = _UNBOUND,
    check: Any = _UNBOUND,
    corners: Any = _UNBOUND,
    dp: Any = _UNBOUND,
    dp_on_rice: Any = _UNBOUND,
    i: Any = _UNBOUND,
    ol: Any = _UNBOUND,
    p: Any = _UNBOUND,
    paddy_depth: Any = _UNBOUND,
    paddy_ol_st: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    q: Any = _UNBOUND,
    qx0: Any = _UNBOUND,
    qx1: Any = _UNBOUND,
    qy0: Any = _UNBOUND,
    qy1: Any = _UNBOUND,
    sc: Any = _UNBOUND,
    worst: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 213 (dry_plots_clear_of_paddies, no_structure_on_paddy) - body verbatim from the legacy gate() (feature 022)."""
    if paddy_ol_st:

        def paddy_depth(sc: Poly) -> float:
            worst = 0.0
            for px, py in sc:
                for ol in paddy_ol_st:
                    if point_in_poly(px, py, ol):
                        worst = max(worst, min(seg_dist(px, py, ol[i], ol[i + 1]) for i in range(len(ol) - 1)))
            return worst

        bad_pd = [1 for sc in corners if paddy_depth(sc) > 3]
        check(
            "no_structure_on_paddy",
            not bad_pd,
            f"{len(bad_pd)} structure(s) stand on a rice paddy - houses, yards, and every other footprint sit on dry ground BESIDE the crop, never in the flooded field",
        )

        # ... and no DRY plot lies on one either. The hem quilt exists precisely because its ground
        # sits UPSLOPE of what the canal commands, so dry-crop-on-rice is a contradiction in the
        # water logic, not a style choice. On a multi-fan map each fan's hem is generated blind to
        # the other fans - the generators drop any hem plot that hits a previously recorded fan via
        # the SAME hem_on_paddy predicate this check runs (waterfields.py; the same-source doctrine,
        # diagram CLAUDE.md), and this gate is what proves the filter worked. First caught: Tango's
        # fe2 hem punching into fe1's envelope (2026-07-23) - only hand-tuned dry_keepout circles
        # held fans' hems apart before, and hand tuning missed a spot.
        dp_on_rice = []
        _pol_bb = [(ol, (min(p[0] for p in ol), min(p[1] for p in ol), max(p[0] for p in ol), max(p[1] for p in ol))) for ol in paddy_ol_st]
        for dp in M.get("dry_plots", []):
            q = dp["poly"]
            qx0, qy0, qx1, qy1 = min(p[0] for p in q), min(p[1] for p in q), max(p[0] for p in q), max(p[1] for p in q)
            if any(qx1 >= bx0 and qx0 <= bx1 and qy1 >= by0 and qy0 <= by1 and hem_on_paddy(q, ol) for ol, (bx0, by0, bx1, by1) in _pol_bb):
                dp_on_rice.append((round((qx0 + qx1) / 2), round((qy0 + qy1) / 2)))
        check(
            "dry_plots_clear_of_paddies",
            not dp_on_rice,
            f"{len(dp_on_rice)} dry plot(s) overlap a flooded paddy fan (plot centers): {dp_on_rice[:4]} - dry "
            f"crops grow on the ground the water CANNOT command, so a hem plot never laps onto the rice; on a "
            f"multi-fan map the hem filter must drop plots that land on a neighboring fan's envelope",
        )
    return _kept(locals(), ('_pol_bb', 'bad_pd', 'bx0', 'bx1', 'by0', 'by1', 'dp', 'dp_on_rice', 'ol', 'p', 'paddy_depth', 'q', 'qx0', 'qx1', 'qy0', 'qy1', 'sc'))


# WATER-WIDTH LADDER - a STROKE CONVENTION, not a size license (GM ruling 2026-07-21). Real
# wet-rice water systems are a tiered hierarchy whose widths step up ~2-4x per tier (channel
# width scales with the sqrt of command-area flow): a field ditch ~0.3 m, a village creek ~2 m
# (~6x the ditch), a town river / castle moat ~20 m (~70x the ditch). Watercourses are LINEWORK:
# the smallest lines draw at a minimum-visible floor (a true 1 ft ditch is 0.33px at city scale -
# invisible), true-width-or-floored and never fattened past the floor, while honesty anchors on
# the LARGE end (the city moat draws its real ~66+ ft). The ORDERING and coarse steps must
# survive the compression: an irrigation ditch is ALWAYS the thinnest line, a natural watercourse
# clearly heavier, the city moat heaviest of all. The clauses below pin that. (Why these numbers:
# settlements.md "Water-width ladder" grounding.)


def _seg_0214__c_1(*, M: Any = _UNBOUND, c: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 214 (c, chan_ws) - body verbatim from the legacy gate() (feature 022)."""
    chan_ws = [c["w"] for c in M.get("channels", []) if "w" in c]
    return _kept(locals(), ('c', 'chan_ws'))


def _seg_0215__st(*, M: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 215 (st, strm_ws) - body verbatim from the legacy gate() (feature 022)."""
    strm_ws = [st["w"] for st in M.get("streams", []) if "w" in st]
    return _kept(locals(), ('st', 'strm_ws'))


def _seg_0216__moat_w(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 216 (moat_w) - body verbatim from the legacy gate() (feature 022)."""
    moat_w = M.get("moat_width")
    return _kept(locals(), ('moat_w',))


# (1) Irrigation channels are HAIRLINES: at/just above the legibility floor, never fattened toward
# stream weight. A ditch drawn as a stout line (the old 4.2 px) reads as a watercourse, not a ditch.


def _seg_0217__irrigation_channels_hairline(*, M: Any = _UNBOUND, c: Any = _UNBOUND, chan_ws: Any = _UNBOUND, check: Any = _UNBOUND, fat: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 217 (irrigation_channels_hairline) - body verbatim from the legacy gate() (feature 022)."""
    if chan_ws:
        # a DRAIN-OUTFALL CULVERT is not a field ditch: it carries a whole fan's gathered runoff and
        # must MATCH the drain's outfall width (6.0 x grain = 4.0 at the city grain) - a culvert
        # narrower than the ditch it drains read as the water SHRINKING past the gate (GM 2026-07-23,
        # the widening-drains pass). Its ceiling is 4.5; everything else keeps the hairline band.
        fat = [c["w"] for c in M.get("channels", []) if "w" in c and not 2.0 <= c["w"] <= (4.5 if (c.get("frm") or {}).get("kind") == "drain" else 3.5)]
        check(
            "irrigation_channels_hairline",
            not fat,
            f"channel width(s) {sorted(set(fat))} outside the hairline band [2.0, 3.5] px (drain-outfall "
            f"culverts may run to 4.5 - they carry the fan's whole runoff and match the drain's outfall) - a field "
            f"ditch is the thinnest line on the map (~0.3 m, ~1/300 of the paddy it feeds); keep it at "
            f"the legibility floor, distinct from any natural watercourse",
        )
    return _kept(locals(), ('c', 'fat'))


# (2) The tiers are ORDERED with honest gaps: a creek clearly beats a ditch (>=2.5x), a natural
# stream never out-widths the city moat (a moat-feeder may EQUAL it, by conservation of flow), and
# the moat dwarfs a ditch (>=4x). Each clause runs only when both features it compares are present.


def _seg_0218__watercourses_wider_than_ditches(*, chan_ws: Any = _UNBOUND, check: Any = _UNBOUND, ok: Any = _UNBOUND, strm_ws: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 218 (watercourses_wider_than_ditches) - body verbatim from the legacy gate() (feature 022)."""
    if chan_ws and strm_ws:
        ok = min(strm_ws) >= 2.5 * max(chan_ws)
        check(
            "watercourses_wider_than_ditches",
            ok,
            f"narrowest stream {min(strm_ws)} px is not >= 2.5x the widest channel {max(chan_ws)} px - a natural creek must read clearly heavier than an irrigation ditch, not as its sibling",
        )
    return _kept(locals(), ('ok',))


def _seg_0219__moat_is_heaviest_watercourse(
    *, M: Any = _UNBOUND, check: Any = _UNBOUND, moat_w: Any = _UNBOUND, rv_w: Any = _UNBOUND, strm_cmp: Any = _UNBOUND, strm_ws: Any = _UNBOUND, w_: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 219 (moat_is_heaviest_watercourse) - body verbatim from the legacy gate() (feature 022)."""
    if strm_ws and moat_w:
        # a RIVER-bank city's river legitimately outweighs its dug moat (the river IS the heavier
        # defense - it closes the water ring on its flank), so the river's own stream record is
        # excluded from the comparison; every OTHER stream still respects the moat's weight
        rv_w = (M.get("river") or {}).get("w")
        strm_cmp = [w_ for w_ in strm_ws if rv_w is None or w_ != rv_w]
        check(
            "moat_is_heaviest_watercourse",
            not strm_cmp or max(strm_cmp) <= moat_w * 1.05,
            f"a stream ({max(strm_cmp or [0])} px) is wider than the city moat ({moat_w} px) - the moat is the "
            f"heaviest watercourse; a feeder stream may equal it (conservation of flow) but not exceed it",
        )
    return _kept(locals(), ('rv_w', 'strm_cmp', 'w_'))


def _seg_0220__moat_dwarfs_ditches(*, chan_ws: Any = _UNBOUND, check: Any = _UNBOUND, moat_w: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 220 (moat_dwarfs_ditches) - body verbatim from the legacy gate() (feature 022)."""
    if chan_ws and moat_w:
        check(
            "moat_dwarfs_ditches",
            moat_w >= 4.0 * max(chan_ws),
            f"city moat {moat_w} px is not >= 4x the widest channel {max(chan_ws)} px - a defensive moat (~20-35 m real, ~70x a field ditch) must dwarf an irrigation ditch",
        )
    return _kept(locals(), ())


# no structure overlaps a street OR an alley (a paved lane or a gravel alley running over a
# house is wrong) - alleys are drawn last, so a careless alley can be laid across a building


def _seg_0221__tstreets(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 221 (tstreets) - body verbatim from the legacy gate() (feature 022)."""
    tstreets = M.get("town_streets", [])
    return _kept(locals(), ('tstreets',))


def _seg_0222__a_1(*, M: Any = _UNBOUND, a: Any = _UNBOUND, tstreets: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 222 (a, lanes) - body verbatim from the legacy gate() (feature 022)."""
    lanes = tstreets + [{"pts": a["pts"], "w": a.get("w", 10)} for a in M.get("alleys", [])]
    return _kept(locals(), ('a', 'lanes'))


def _seg_0223__no_structure_on_street(
    *,
    bad_ts: Any = _UNBOUND,
    check: Any = _UNBOUND,
    corners: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    e: Any = _UNBOUND,
    hw: Any = _UNBOUND,
    k: Any = _UNBOUND,
    lanes: Any = _UNBOUND,
    on_street: Any = _UNBOUND,
    rx: Any = _UNBOUND,
    ry: Any = _UNBOUND,
    sc: Any = _UNBOUND,
    sp: Any = _UNBOUND,
    st: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 223 (no_structure_on_street) - body verbatim from the legacy gate() (feature 022)."""
    if lanes:

        def on_street(sc: Poly, sp: Poly, hw: float) -> bool:
            if any(seg_dist(cx, cy, sp[k], sp[k + 1]) < hw for (cx, cy) in sc for k in range(len(sp) - 1)):
                return True
            if any(point_in_poly(rx, ry, sc) for rx, ry in sp):
                return True
            return any(segments_cross(sp[k], sp[k + 1], sc[e], sc[(e + 1) % 4]) for k in range(len(sp) - 1) for e in range(4))

        bad_ts = [1 for sc in corners for st in lanes if on_street(sc, st["pts"], st.get("w", 24) / 2 + 2)]
        check("no_structure_on_street", not bad_ts, f"{len(bad_ts)} structure(s) overlapped by a street/alley")
    return _kept(locals(), ('bad_ts', 'on_street', 'sc', 'st'))


# ---- street-faced town layout: businesses front the streets (and face them); housing
# sits back off the main commercial street. The "streets" are the town streets plus any
# road (an unwalled town's road is its high street).


def _seg_0224__st_1(*, M: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 224 (st, street_lines) - body verbatim from the legacy gate() (feature 022)."""
    street_lines = [st["pts"] for st in M.get("town_streets", [])]
    return _kept(locals(), ('st', 'street_lines'))


def _seg_0225__i_1(*, M: Any = _UNBOUND, i: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 225 (i, main_idx, st) - body verbatim from the legacy gate() (feature 022)."""
    main_idx = next((i for i, st in enumerate(M.get("town_streets", [])) if st.get("main")), None)
    return _kept(locals(), ('i', 'main_idx', 'st'))


def _seg_0226__main_idx(*, M: Any = _UNBOUND, main_idx: Any = _UNBOUND, p: Any = _UNBOUND, street_lines: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 226 (main_idx, p, street_lines) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("road"):
        street_lines.append([list(p) for p in M["road"]])
        if main_idx is None:
            main_idx = len(street_lines) - 1
    return _kept(locals(), ('main_idx', 'p', 'street_lines'))


def _seg_0227__businesses_front_streets(
    *,
    BUSINESS: Any = _UNBOUND,
    FRONT: Any = _UNBOUND,
    HOUSING: Any = _UNBOUND,
    M: Any = _UNBOUND,
    aligns: Any = _UNBOUND,
    b: Any = _UNBOUND,
    bd: Any = _UNBOUND,
    best: Any = _UNBOUND,
    biz_off: Any = _UNBOUND,
    check: Any = _UNBOUND,
    closest_on_line: Any = _UNBOUND,
    cp: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    d: Any = _UNBOUND,
    dl: Any = _UNBOUND,
    dmin: Any = _UNBOUND,
    fx: Any = _UNBOUND,
    fy: Any = _UNBOUND,
    house_front: Any = _UNBOUND,
    k: Any = _UNBOUND,
    kind: Any = _UNBOUND,
    li: Any = _UNBOUND,
    limin: Any = _UNBOUND,
    main_idx: Any = _UNBOUND,
    off_face: Any = _UNBOUND,
    per: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    r: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    sp: Any = _UNBOUND,
    street_lines: Any = _UNBOUND,
    th: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 227 (buildings_face_street, businesses_front_streets, housing_off_main_street) - body verbatim from the legacy gate() (feature 022)."""
    if scale == "town" and street_lines and M.get("buildings"):

        def closest_on_line(px: float, py: float, sp: Poly) -> tuple[float, tuple[float, float] | None]:
            best, bd = None, 1e18
            for k in range(len(sp) - 1):
                cx, cy = seg_closest(px, py, sp[k], sp[k + 1])
                d = math.hypot(cx - px, cy - py)
                if d < bd:
                    bd, best = d, (cx, cy)
            return bd, best

        BUSINESS, HOUSING = {"shop", "merchant"}, {"laborer", "servant"}
        FRONT = 92  # within this of a street = "fronting" it
        biz_off, off_face, house_front = [], [], []
        for b in M["buildings"]:
            kind = b["kind"]
            per = [(closest_on_line(b["x"], b["y"], sp), li) for li, sp in enumerate(street_lines)]
            (dmin, cpmin), limin = min(per, key=lambda r: r[0][0])
            if kind in BUSINESS and dmin > FRONT:
                biz_off.append(kind)
            if dmin <= FRONT and kind in (BUSINESS | HOUSING):
                th = math.radians(b.get("rot", 0))
                fx, fy = -math.sin(th), math.cos(th)  # frontage normal
                # a corner building may face any street it fronts, not only the nearest
                aligns = []
                for (d, cp), _ in per:
                    if d <= FRONT and cp:
                        dl = math.hypot(cp[0] - b["x"], cp[1] - b["y"]) or 1
                        aligns.append((fx * (cp[0] - b["x"]) + fy * (cp[1] - b["y"])) / dl)
                if aligns and max(aligns) < 0.5:  # > 60 deg off every nearby street
                    off_face.append(kind)
            if kind in HOUSING and limin == main_idx and dmin <= FRONT:
                house_front.append(kind)
        check("businesses_front_streets", not biz_off, f"{len(biz_off)} business(es) not fronting any street")
        check("buildings_face_street", not off_face, f"{len(off_face)} street-fronting building(s) not facing any street it fronts")
        check("housing_off_main_street", not house_front, f"{len(house_front)} dwelling(s) on the main street frontage (housing belongs set back)")
    return _kept(
        locals(),
        (
            'BUSINESS',
            'FRONT',
            'HOUSING',
            '_',
            'aligns',
            'b',
            'biz_off',
            'closest_on_line',
            'cp',
            'cpmin',
            'd',
            'dl',
            'dmin',
            'fx',
            'fy',
            'house_front',
            'kind',
            'li',
            'limin',
            'off_face',
            'per',
            'sp',
            'th',
        ),
    )


def _seg_0228__c_2(*, M: Any = _UNBOUND, c: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 228 (c, corr) - body verbatim from the legacy gate() (feature 022)."""
    corr = ([M["lane"]] if M.get("lane") else []) + [c["poly"] for c in M["channels"]]
    return _kept(locals(), ('c', 'corr'))


def _seg_0229__h(*, corr: Any = _UNBOUND, h: Any = _UNBOUND, houses: Any = _UNBOUND, k: Any = _UNBOUND, poly: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 229 (h, k, onroad, poly) - body verbatim from the legacy gate() (feature 022)."""
    onroad = sum(1 for h in houses for poly in corr if any(seg_dist(h["x"], h["y"], poly[k], poly[k + 1]) < 14 for k in range(len(poly) - 1)))
    return _kept(locals(), ('h', 'k', 'onroad', 'poly'))


def _seg_0230__houses_off_corridors(*, check: Any = _UNBOUND, onroad: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 230 (houses_off_corridors) - body verbatim from the legacy gate() (feature 022)."""
    check("houses_off_corridors", onroad == 0, f"{onroad} house-on-corridor hit(s)")
    return _kept(locals(), ())


def _seg_0231__ADJ() -> dict[str, Any]:
    """Gate segment 231 (ADJ) - body verbatim from the legacy gate() (feature 022)."""
    ADJ = 165
    return _kept(locals(), ('ADJ',))


# WHY (farmers build close to the fields they work): settlements.md "Historical grounding". The invariant
# depends on the SETTLEMENT FORM, and it is TUNABLE via meta.nucleated:
#   - DISPERSED (the default): every farmhouse fronts its own fields, so EACH house must be within ADJ
#     of a field (`all_houses_field_adjacent`).
#   - NUCLEATED (meta.nucleated=True): the houses cluster together and the FIELDS radiate from the
#     cluster's edge - the interior houses are legitimately a cluster-span BACK from the nearest field,
#     so per-house adjacency is wrong. Instead the whole CLUSTER must ABUT its fields: the nearest house
#     is field-adjacent (the village sits ON its land, not floating in open country) AND no house is
#     farther than the cluster's own diameter past that edge (`cluster_abuts_fields`).


def _seg_0232__cluster_abuts_fields(
    *,
    ADJ: Any = _UNBOUND,
    M: Any = _UNBOUND,
    PHANTOM: Any = _UNBOUND,
    b: Any = _UNBOUND,
    built: Any = _UNBOUND,
    ccx: Any = _UNBOUND,
    ccy: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cov: Any = _UNBOUND,
    d: Any = _UNBOUND,
    dists: Any = _UNBOUND,
    f: Any = _UNBOUND,
    far: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    grp: Any = _UNBOUND,
    h: Any = _UNBOUND,
    harea: Any = _UNBOUND,
    hh: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    hx: Any = _UNBOUND,
    hy: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    nearest: Any = _UNBOUND,
    pad: Any = _UNBOUND,
    r: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    span: Any = _UNBOUND,
    tails: Any = _UNBOUND,
    v: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 232 (all_houses_field_adjacent, cluster_abuts_fields, field_outline_matches_planting, village_cluster_compact) - body verbatim from the legacy gate() (feature 022)."""
    if fields and houses:
        hh = [h for h in houses if h.get("role") != "headman"]
        dists = [(h, min(poly_dist(h["x"], h["y"], f["outline"]) for f in fields)) for h in hh]
        if meta.get("nucleated"):
            hx = [h["x"] for h in houses]
            hy = [h["y"] for h in houses]
            ccx, ccy = sum(hx) / len(hx), sum(hy) / len(hy)
            span = max((math.hypot(h["x"] - ccx, h["y"] - ccy) for h in houses), default=0)  # cluster radius
            nearest = min((d for _, d in dists), default=999)
            far = [h for h, d in dists if d > ADJ + 2 * span]  # farther than a cluster-diameter past the field edge
            check(
                "cluster_abuts_fields",
                nearest <= ADJ and not far,
                f"nucleated cluster: nearest house {nearest:.0f}px from a field (want <={ADJ}); {len(far)} house(s) beyond a cluster-span of the fields",
            )
            # A NUCLEATED cluster must be a COMPACT FABRIC, not a thin hollow arc. `cluster_abuts_fields`
            # measures each house against the cluster's OWN span, so a big hollow cluster gets a big
            # allowance and passes even when a horn juts into empty ground far from the crops. Measure the
            # BUILT COVERAGE of the cluster's convex hull instead: the houses + their gardens / threshing
            # yards / farmstead groves should fill a healthy fraction of the footprint they span. A cluster
            # strung thin over a wide, hollow hull (the placer pulls every house to hug the paddy and packs
            # ALONG it, so an over-WIDE seed shape strings them into a stranded arc) fills far less of its
            # hull than a compact blob does. CALIBRATION: the pathological rolled crescent that motivated this
            # filled ~0.20 (Kikuta: 55 houses over a hull filled 20%, NE horn ~400px from any crop); the
            # roll_village placer's healthy nucleated villages fill ~0.28-0.31, and the tightly hand-placed
            # villages ~0.40. Floor 0.25 sits clear below the healthy band and above the pathology. Village
            # scale + >=12 houses only: a hamlet is legitimately loose, and a tiny cluster's hull is degenerate.
            if scale == "village" and len(houses) >= 12:
                harea = poly_area(convex_hull([(h["x"], h["y"]) for h in houses]))
                built = sum(r.get("w", 30) * r.get("h", 24) for grp in ("houses", "gardens", "threshing_yards", "groves") for r in M.get(grp, []))
                cov = built / harea if harea else 0.0
                check(
                    "village_cluster_compact",
                    cov >= 0.25,
                    f"nucleated village cluster fills only {cov:.0%} of the footprint it spans (want >=25%): the houses are strung thin over a hollow hull (an over-wide cluster stranding houses far from the fields), not a compact village fabric",
                )
        else:
            far = [h for h, d in dists if d > ADJ]
            check("all_houses_field_adjacent", not far, f"{len(far)} house(s) >{ADJ}px from any field")

            # ...and the outline that adjacency was just measured against must BE the planting. A field's
            # `outline` is the smoothed ENVELOPE the water net claims; `vis_bbox` is the extent of the plots
            # actually DRAWN. They diverge when a gen declares more field than the comb fills (an over-declared
            # `field_fall`): the surplus becomes a PHANTOM TAIL - invisible on the map, but fully real to every
            # distance test. A farm hugging that tail reads as "field-adjacent" while sitting well out past the
            # last rice, which is exactly how Akagahara grew a line of farmsteads hanging south of its paddy
            # (the tail was 181px; the gate saw nothing). Without this, `all_houses_field_adjacent` has no teeth
            # on precisely the maps that need it. DISPERSED only: there the outline is load-bearing for
            # placement, whereas a nucleated cluster is seeded as a unit and never rides the envelope, so a tail
            # is inert (Hoshigaoka/Kikuta carry ~210px tails harmlessly). Tolerance 60px allows the genuine
            # rounding of a smoothed rim over irregular plots, well under the ~165px band it protects.
            PHANTOM = 60
            tails = []
            for f in fields:
                b, v = f.get("bbox"), f.get("vis_bbox")
                if not b or not v:
                    continue
                pad = max(v[0] - b[0], v[1] - b[1], b[2] - v[2], b[3] - v[3])
                if pad > PHANTOM:
                    tails.append(f"{f.get('name')} (+{pad:.0f}px)")
            check("field_outline_matches_planting", not tails, f"field outline overruns the planted crop by >{PHANTOM}px, so adjacency is measured against empty ground: {', '.join(tails)}")
    return _kept(locals(), ('PHANTOM', '_', 'b', 'built', 'ccx', 'ccy', 'cov', 'd', 'dists', 'f', 'far', 'grp', 'h', 'harea', 'hh', 'hx', 'hy', 'nearest', 'pad', 'r', 'span', 'tails', 'v'))


# DWELLINGS sit on the DRY higher ground, NEVER in the wet low toe below the field's drainage. The field
# drains to its lowest edge (the akusui collector ditch); the ground DOWNSLOPE of that drain - reed marsh,
# low reclaimed paddy, or the drainage tameike - is the wettest in the valley and is not building ground.
# So no dwelling may sit downslope of the drain line WITHIN the drain's cross-slope span (a farm off to the
# SIDE, past the drain's ends, is a legit flank homestead and is NOT flagged - only the central toe below
# the drain is). Scoped to DISPERSED maps (like the per-house `all_houses_field_adjacent` above): each
# strewn farm must individually sit on dry ground, whereas a NUCLEATED cluster is placed as a unit and
# governed by `cluster_abuts_fields` (and a tight cluster beside a diagonal drain reads as "downslope" of it
# without being in any wet toe). Needs the map's slope (meta.down_deg) + a drain ditch; skipped otherwise.
# WHY: the GM (2026-07) flagged dispersed farmhouses strewn S of a drainage ditch into marshland - see
# settlements.md 'Marsh'.
# PER-FIELD FALL here too (GM 2026-07-25): each drain carries its OWN downslope, so a map that
# declares no single bearing - the two provincial cities, whose fans fall 210 deg apart - is still
# checked. This was the last of the three drainage-slope checks left on the map-level constant,
# which meant it silently skipped both cities even after the other two were converted.


def _seg_0233__down_deg(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 233 (down_deg) - body verbatim from the legacy gate() (feature 022)."""
    down_deg = meta.get("down_deg")
    return _kept(locals(), ('down_deg',))


def _seg_0234___fdd_here(*, M: Any = _UNBOUND, f: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 234 (_fdd_here, f) - body verbatim from the legacy gate() (feature 022)."""
    _fdd_here = {f.get("name"): f["down_deg"] for f in M.get("fields", []) if f.get("down_deg") is not None}
    return _kept(locals(), ('_fdd_here', 'f'))


def _seg_0235__drains(*, M: Any = _UNBOUND, _fdd_here: Any = _UNBOUND, down_deg: Any = _UNBOUND, fd: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 235 (drains, fd) - body verbatim from the legacy gate() (feature 022)."""
    drains = [(fd["poly"], _fdd_here.get(fd.get("field"), down_deg)) for fd in M.get("field_ditches", []) if fd.get("role") == "drain" and len(fd.get("poly", [])) >= 2]
    return _kept(locals(), ('drains', 'fd'))


def _seg_0236__dd_(*, dd_: Any = _UNBOUND, drains: Any = _UNBOUND, pl_: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 236 (dd_, drains, pl_) - body verbatim from the legacy gate() (feature 022)."""
    drains = [(pl_, dd_) for pl_, dd_ in drains if dd_ is not None]
    return _kept(locals(), ('dd_', 'drains', 'pl_'))


# NOT APPLIED AT CITY SCALE (GM decision 2026-07-25). City farms are RING-placed - s.ring lays
# them around the whole field envelope as a unit, so the low-side arc necessarily lands below the
# collector; by this check's own rationale that belongs with the NUCLEATED exemption ("a cluster is
# placed as a unit"), not the dispersed case it was written for. It is also RIGHT for a moated city:
# the farms round a moat legitimately differ by local topography - some drain INTO the moat, others
# have their paddies FED BY it - and expecting every one of them to sit above its field's collector
# imposes a uniformity the ground does not have. (For the record, turning it on flags 25% of Tango's
# farmhouses and 42% of Nagahara's: the ring algorithm, not stray misplacements.)


def _seg_0237__dwellings_above_field_drain(
    *,
    M: Any = _UNBOUND,
    _d: Any = _UNBOUND,
    _ddd: Any = _UNBOUND,
    at_end: Any = _UNBOUND,
    ax: Any = _UNBOUND,
    ay: Any = _UNBOUND,
    best: Any = _UNBOUND,
    bx: Any = _UNBOUND,
    by: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d: Any = _UNBOUND,
    dp: Any = _UNBOUND,
    drains: Any = _UNBOUND,
    dux: Any = _UNBOUND,
    duy: Any = _UNBOUND,
    h: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    in_toe: Any = _UNBOUND,
    ll: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    si: Any = _UNBOUND,
    toe_px: Any = _UNBOUND,
    tt: Any = _UNBOUND,
    vx: Any = _UNBOUND,
    vy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 237 (dwellings_above_field_drain) - body verbatim from the legacy gate() (feature 022)."""
    if houses and drains and not meta.get("nucleated") and scale != "city":
        # the WET TOE is a BAND below the collector (~240 real ft - the marsh/reclaimed strip the
        # runoff keeps soggy), not an infinite downslope slab: without this cap the first town
        # with drains (Hirameki) had tenements flagged 780px away, across the town wall, merely
        # for being south of a field's collector. Distance converts at the map's ft/px.
        toe_px = 240.0 / float(meta.get("ftpx", 1) or 1)
        in_toe = []
        for h in houses + M.get("buildings", []):
            for dp, _ddd in drains:
                dux, duy = math.cos(math.radians(_ddd)), math.sin(math.radians(_ddd))
                best = None
                for si in range(len(dp) - 1):
                    ax, ay = dp[si]
                    bx, by = dp[si + 1]
                    vx, vy = bx - ax, by - ay
                    ll = vx * vx + vy * vy
                    tt = 0.0 if ll == 0 else max(0.0, min(1.0, ((h["x"] - ax) * vx + (h["y"] - ay) * vy) / ll))
                    px, py = ax + vx * tt, ay + vy * tt
                    d = math.hypot(h["x"] - px, h["y"] - py)
                    at_end = (si == 0 and tt <= 0.001) or (si == len(dp) - 2 and tt >= 0.999)  # clamped to the polyline's absolute end -> off the side
                    if best is None or d < best[0]:
                        best = (d, px, py, at_end)
                assert best is not None
                _d, px, py, at_end = best
                if not at_end and _d <= toe_px and (h["x"] - px) * dux + (h["y"] - py) * duy > 18:  # center clearly on the wet (downslope) side, within the toe band
                    in_toe.append((round(h["x"]), round(h["y"])))
                    break
        check(
            "dwellings_above_field_drain",
            not in_toe,
            f"{len(in_toe)} dwelling(s) sit in the WET low toe DOWNSLOPE of the field drain at {in_toe[:4]} - the "
            f"ground below the drainage line (marsh / low reclaimed paddy / the tameike) is the wettest in the "
            f"valley, not building ground; strew the farms on the DRY margins ABOVE the drain (flank farms past the drain's ends are fine)",
        )
    return _kept(locals(), ('_d', '_ddd', 'at_end', 'ax', 'ay', 'best', 'bx', 'by', 'd', 'dp', 'dux', 'duy', 'h', 'in_toe', 'll', 'px', 'py', 'si', 'toe_px', 'tt', 'vx', 'vy'))


def _seg_0238__runs_off_edge(*, EX0: Any = _UNBOUND, EX1: Any = _UNBOUND, EY0: Any = _UNBOUND, EY1: Any = _UNBOUND, ol: Any = _UNBOUND, p: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 238 (runs_off_edge) - body verbatim from the legacy gate() (feature 022)."""

    def runs_off_edge(ol: Poly) -> bool:
        return any(p[0] < EX0 or p[0] > EX1 or p[1] < EY0 or p[1] > EY1 for p in ol)

    return _kept(locals(), ('runs_off_edge',))


def _seg_0239__field_ringed(
    *,
    ADJ: Any = _UNBOUND,
    area: Any = _UNBOUND,
    check: Any = _UNBOUND,
    f: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    h: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    need: Any = _UNBOUND,
    ring: Any = _UNBOUND,
    runs_off_edge: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 239 (field_ringed) - body verbatim from the legacy gate() (feature 022)."""
    for f in fields:
        if runs_off_edge(f["outline"]):
            continue  # a field running off the map has its farmhouses implied off-map too
        if f.get("kind") == "vegetable":
            continue  # urban garden tracts are worked by the surrounding quarters, not farmsteads
        ring = [h for h in houses if poly_dist(h["x"], h["y"], f["outline"]) <= ADJ]
        area = (f["bbox"][2] - f["bbox"][0]) * (f["bbox"][3] - f["bbox"][1])
        need = 5 if area > 80000 else 3
        check(f"field_ringed[{f['name']}]", len(ring) >= need, f"{len(ring)} houses, need {need}")
    return _kept(locals(), ('area', 'f', 'h', 'need', 'ring'))


def _seg_0240__h_1(*, h: Any = _UNBOUND, houses: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 240 (h, not_south) - body verbatim from the legacy gate() (feature 022)."""
    not_south = [h for h in houses if h["w"] < h["h"] or abs(h["rot"]) > 12]
    return _kept(locals(), ('h', 'not_south'))


def _seg_0241__houses_face_south(*, check: Any = _UNBOUND, not_south: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 241 (houses_face_south) - body verbatim from the legacy gate() (feature 022)."""
    check("houses_face_south", not not_south, f"{len(not_south)} house(s) not south-facing")
    return _kept(locals(), ())


def _seg_0242__h_2(*, h: Any = _UNBOUND, houses: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 242 (h, headman) - body verbatim from the legacy gate() (feature 022)."""
    headman = next((h for h in houses if h.get("role") == "headman"), None)
    return _kept(locals(), ('h', 'headman'))


def _seg_0243__village_has_headman(*, check: Any = _UNBOUND, headman: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 243 (capital_has_no_headman, city_has_no_headman, hamlet_has_no_headman, town_has_no_headman, village_has_headman, village_has_no_headman) - body verbatim from the legacy gate() (feature 022)."""
    if scale == "village":
        check("village_has_headman", headman is not None, "a village must have a headman")
    else:
        # hamlets fall under the village district headman; towns are run by the magistrate
        check(f"{scale}_has_no_headman", headman is None, f"a {scale} has no peasant headman of its own")
    return _kept(locals(), ())


# religious building by settlement scale: hamlet none, village shrine, town
# monastery, city temple
# WHY (the Shinto/Buddhist split + scale: shrine -> monastery -> temple): settlements.md "Historical grounding"
# a capital is the city tier at 4x scale - temples, same as a provincial city (feature 020)


def _seg_0244__expected_rel(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 244 (expected_rel) - body verbatim from the legacy gate() (feature 022)."""
    expected_rel = {"hamlet": None, "village": "shrine", "town": "monastery", "city": "temple", "capital": "temple"}.get(scale)
    return _kept(locals(), ('expected_rel',))


def _seg_0245__r(*, M: Any = _UNBOUND, r: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 245 (r, rel_kinds) - body verbatim from the legacy gate() (feature 022)."""
    rel_kinds = set(r["kind"] for r in M.get("religious", [])) - {"small_shrine"}  # small wayside shrines are auxiliary, allowed alongside the scale's main religious building
    return _kept(locals(), ('r', 'rel_kinds'))


def _seg_0246__religious_matches_scale(*, check: Any = _UNBOUND, expected_rel: Any = _UNBOUND, rel_kinds: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 246 (religious_matches_scale) - body verbatim from the legacy gate() (feature 022)."""
    if expected_rel is None:
        check("religious_matches_scale", not rel_kinds, f"a {scale} should have no religious building (found {rel_kinds or 'none'})")
    else:
        check("religious_matches_scale", rel_kinds == {expected_rel}, f"a {scale} should have only {expected_rel}(s); found {rel_kinds or 'none'}")
    return _kept(locals(), ())


# TORII COUNT NUMEROLOGY (GM canon 2026-07-21): a torii approach is either a MODEST ENTRANCE
# (1-2 arches) or a FULL AVENUE of EXACTLY SEVEN - 7 is the numerologically significant count.
# (RETIRED 2026-07-21: torii_full_avenue_is_seven sanctioned {1, 2, 7} and banned 3-6 as "an
# unfinished avenue". The GM's numerology ruling the same day supersedes it - counts are exactly
# {1, 3, 7} at EVERY proper hall, with torii_outlier for marked exceptions - and that doctrine is
# gated by torii_count_canonical below, which also fixes this check's misattribution: it assigned
# arches to the nearest of ALL religious features, so a wayside small_shrine near a temple sando
# could absorb the temple's gates and hide a violation, which is exactly how Tango's 2-arch
# Daikoku entrance slipped through.)

# ... and a village/hamlet SHRINE has a village-scale FOOTPRINT (GM 2026-07-21, caught on Hikari no
# Sato, whose two shrines survived from before the size norms crystallized at 192x128 / 236x164 ft -
# small-monastery footprints in a village). religious_matches_scale gates the TYPE per tier but said
# nothing about SIZE, so oversize halls sailed through. Calibration (the pool + temple-density canon): a
# village kami hall is a modest structure - the ordinary earth-god/water-mouth shrine is ~275 m^2
# (60x48 ft, Ueda/Hoshigaoka, with the recorded why in Ueda's gen), and Kikuta's showcase Benten with
# its 7-torii avenue is ~490 m^2 - so the 600 m^2 ceiling clears every deliberate design with headroom
# while the monastery/temple tier (a town's smallest monastery runs well past 1,000 m^2) stays cleanly
# out of reach. No floor: a tiny wayside hall is legitimate.


def _seg_0247__village_shrine_footprint_within_norms(
    *, M: Any = _UNBOUND, _ft: Any = _UNBOUND, _oversize_rel: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, r: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 247 (village_shrine_footprint_within_norms) - body verbatim from the legacy gate() (feature 022)."""
    if scale in ("village", "hamlet"):
        _ft = float(meta.get("ftpx") or 2.0)
        _oversize_rel = [
            (round(r["x"]), round(r["y"]), round(r["w"] * r["h"] * _ft * _ft * 0.3048 * 0.3048)) for r in M.get("religious", []) if r.get("w") and r["w"] * r["h"] * _ft * _ft * 0.3048 * 0.3048 > 600
        ]
        check(
            "village_shrine_footprint_within_norms",
            not _oversize_rel,
            f"village-scale shrine hall(s) with a monastery-tier footprint (x, y, m^2): {_oversize_rel[:3]} - a village kami shrine is a modest hall (~275 m^2 ordinary, ~490 m^2 for a showcase Benten; ceiling 600), the monastery/temple tier belongs to towns and cities (temple-density canon)",
        )
    return _kept(locals(), ('_ft', '_oversize_rel', 'r'))


# A SHRINE and its TORII arch NESTLE in a CLEARING within the sacred grove - neither may sit UNDER the trees
# (a hall/arch drawn on top of tree canopy reads as buried in the wood). So no fengshui-grove tree CLUMP may
# overlap a religious hall's or a torii's footprint. The recorded clump `r` is the NOMINAL clump radius, but
# the drawn crowns OVERHANG it, so the visible canopy reaches ~1.7x that - use the CANOPY radius so the check
# matches what the eye sees. (The grove is drawn to SKIP the shrine + torii clearing; place them BEFORE it.)


def _seg_0248__CANOPY() -> dict[str, Any]:
    """Gate segment 248 (CANOPY) - body verbatim from the legacy gate() (feature 022)."""
    CANOPY = 1.7
    return _kept(locals(), ('CANOPY',))


def _seg_0249__c_3(*, CANOPY: Any = _UNBOUND, M: Any = _UNBOUND, c: Any = _UNBOUND, gv: Any = _UNBOUND, k: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 249 (c, grove_clumps, gv, k) - body verbatim from the legacy gate() (feature 022)."""
    grove_clumps = [(c[0], c[1], gv.get("r", 10) * CANOPY) for k in ("village_groves", "groves") for gv in M.get(k, []) for c in gv.get("clumps", [])]
    return _kept(locals(), ('c', 'grove_clumps', 'gv', 'k'))


def _seg_0250__shrine_clear_of_grove_trees(
    *,
    M: Any = _UNBOUND,
    _under_trees: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cpd: Any = _UNBOUND,
    cr: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cx0: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    gcr: Any = _UNBOUND,
    gcx: Any = _UNBOUND,
    gcy: Any = _UNBOUND,
    grove_clumps: Any = _UNBOUND,
    hh: Any = _UNBOUND,
    hw: Any = _UNBOUND,
    p: Any = _UNBOUND,
    pond_trees: Any = _UNBOUND,
    r: Any = _UNBOUND,
    t: Any = _UNBOUND,
    torii_under: Any = _UNBOUND,
    under_trees: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 250 (shrine_clear_of_grove_trees, torii_clear_of_grove_trees, trees_clear_of_fengshui_ponds) - body verbatim from the legacy gate() (feature 022)."""
    if grove_clumps:

        def _under_trees(cx0: float, cy0: float, hw: float, hh: float) -> bool:  # any canopy circle overlaps the rect (center cx0,cy0; half hw,hh)?
            return any((cx - cx0 - max(-hw, min(hw, cx - cx0))) ** 2 + (cy - cy0 - max(-hh, min(hh, cy - cy0))) ** 2 < cr * cr for cx, cy, cr in grove_clumps)

        under_trees = [(round(r["x"]), round(r["y"])) for r in M.get("religious", []) if _under_trees(r["x"], r["y"], r["w"] / 2, r["h"] / 2)]
        check(
            "shrine_clear_of_grove_trees",
            not under_trees,
            f"{len(under_trees)} shrine/temple(s) sit UNDER the grove's trees at {under_trees[:4]} - a hall nestles "
            f"in a CLEARING within the sacred grove; draw the grove to skip the shrine (place the shrine BEFORE it)",
        )
        # a torii is recorded [x, y, z]; its arch spans x +/-19, y -10..+18 (center ~y+4, half-height 14)
        torii_under = [(round(t[0]), round(t[1])) for t in M.get("torii", []) if _under_trees(t[0], t[1] + 4, 19, 14)]
        check(
            "torii_clear_of_grove_trees",
            not torii_under,
            f"{len(torii_under)} torii arch(es) sit UNDER the grove's trees at {torii_under[:4]} - a torii stands "
            f"in the OPEN before its shrine, not buried in the wood; draw the grove to skip it (place torii BEFORE it)",
        )
        # ... and no tree canopy crosses a fengshui CRESCENT POND's water (GM 2026-07-21, caught on
        # Hoshigaoka, where a windbreak clump overhung the half-moon pond): the banyuetang is an OPEN water
        # mirror at the settlement's front - reflecting sky is its fengshui job - and its flat-side forecourt
        # was the village's open ceremony/work ground, so trees neither overhang the water nor crowd it.
        # Same canopy doctrine as the shrine/torii checks (drawn crowns reach ~1.7x the clump's nominal r).
        pond_trees = []
        for cpd in M.get("crescent_ponds", []):
            for gcx, gcy, gcr in grove_clumps:
                if point_in_poly(gcx, gcy, cpd["poly"]) or poly_dist(gcx, gcy, [tuple(p) for p in cpd["poly"]]) < gcr:
                    pond_trees.append((round(gcx), round(gcy)))
        check(
            "trees_clear_of_fengshui_ponds",
            not pond_trees,
            f"tree clump(s) overhang the fengshui crescent pond's water at {pond_trees[:4]} - the half-moon pond is an open water mirror (its fengshui job is reflecting sky); the grove placement keeps a full-disk keep-out around it",
        )
    return _kept(locals(), ('_under_trees', 'cpd', 'gcr', 'gcx', 'gcy', 'p', 'pond_trees', 'r', 't', 'torii_under', 'under_trees'))


# every fengshui crescent pond carries its "geomantic pond" label (GM 2026-07-21): a culturally specific
# feature that does not read by itself - the GM asked "what is that?" of an unlabeled one, so the
# don't-label-the-obvious rule cuts the OTHER way here. crescent_pond() draws the label; this gates it.


def _seg_0251__unlabeled_cp() -> dict[str, Any]:
    """Gate segment 251 (unlabeled_cp) - body verbatim from the legacy gate() (feature 022)."""
    unlabeled_cp = []  # type: ignore[var-annotated]
    return _kept(locals(), ('unlabeled_cp',))


def _seg_0252__cpd(*, M: Any = _UNBOUND, cpd: Any = _UNBOUND, lb: Any = _UNBOUND, near: Any = _UNBOUND, unlabeled_cp: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 252 (cpd, lb, near, unlabeled_cp) - body verbatim from the legacy gate() (feature 022)."""
    for cpd in M.get("crescent_ponds", []):
        near = [lb for lb in M.get("labels", []) if len(lb) >= 6 and "geomantic" in str(lb[5]) and math.hypot((lb[0] + lb[2]) / 2 - cpd["cx"], (lb[1] + lb[3]) / 2 - cpd["cy"]) < cpd["r"] + 60]
        if not near:
            unlabeled_cp.append((round(cpd["cx"]), round(cpd["cy"])))
    return _kept(locals(), ('cpd', 'lb', 'near', 'unlabeled_cp'))


def _seg_0253__crescent_pond_labeled(*, check: Any = _UNBOUND, unlabeled_cp: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 253 (crescent_pond_labeled) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "crescent_pond_labeled",
        not unlabeled_cp,
        f"fengshui crescent pond(s) with no 'geomantic pond' label at {unlabeled_cp[:3]} - the banyuetang is culturally specific and does not read by itself; crescent_pond() draws the label automatically",
    )
    return _kept(locals(), ())


# a religious building's subtitle must not RESTATE its type (the label already names it,
# e.g. "Monastery of Tengen" needs no "(town monastery)" note)


def _seg_0254__r_1(*, M: Any = _UNBOUND, r: Any = _UNBOUND, t: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 254 (r, redundant_sub, t) - body verbatim from the legacy gate() (feature 022)."""
    redundant_sub = [r.get("label") for r in M.get("religious", []) if r.get("sublabel") and any(t in r["sublabel"].lower() for t in ("shrine", "monastery", "temple"))]
    return _kept(locals(), ('r', 'redundant_sub', 't'))


def _seg_0255__religious_subtitle_not_redundant(*, check: Any = _UNBOUND, redundant_sub: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 255 (religious_subtitle_not_redundant) - body verbatim from the legacy gate() (feature 022)."""
    check("religious_subtitle_not_redundant", not redundant_sub, f"religious subtitle restates the building type (already in the label): {sorted(set(redundant_sub))}")
    return _kept(locals(), ())


def _seg_0256__headman_is_largest(*, bigger: Any = _UNBOUND, check: Any = _UNBOUND, h: Any = _UNBOUND, headman: Any = _UNBOUND, hm: Any = _UNBOUND, houses: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 256 (headman_has_kura, headman_is_largest) - body verbatim from the legacy gate() (feature 022)."""
    if headman is not None:
        hm = headman["w"] * headman["h"]
        bigger = [h for h in houses if h is not headman and h["w"] * h["h"] >= hm]
        check("headman_is_largest", not bigger, f"{len(bigger)} house(s) >= headman")
        # ... and the headman always has an attached fireproof KURA (GM 2026-07-21): the shoya/nanushi is by
        # definition among the village's most prosperous farmers, and the office functionally needs one - tax
        # ledgers, land registers, and tax rice awaiting collection are exactly what fireproof storage is
        # for. The ~30% wealth-marker roll is for ORDINARY plain farms; leaving the headman on those dice let
        # all four pool headmen roll bare. The kura rides in the reserved bundle (farm_sheds_attached guards
        # the drawn record); this gates the flag at the source.
        check(
            "headman_has_kura",
            bool(headman.get("shed")),
            f"the headman's house at ({headman['x']:.0f},{headman['y']:.0f}) has no attached kura storehouse - the village's most prosperous farmer (and keeper of its ledgers and tax rice) always has one; the generator forces shed=True for role='headman'",
        )
    return _kept(locals(), ('bigger', 'h', 'hm'))


# no two body labels overlap (the title block is excluded by the generator)


def _seg_0257__labels(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 257 (labels) - body verbatim from the legacy gate() (feature 022)."""
    labels = M.get("labels", [])
    return _kept(locals(), ('labels',))


# An overlap is real when the bboxes cross by more than the estimation slack. The horizontal slack
# is small (a >2px x-overlap means the glyphs actually touch); the vertical slack stays larger (~4px)
# to absorb the descender allowance in the y-bbox, so two cleanly-separated STACKED labels whose boxes
# merely kiss (e.g. Tango's "Mausoleum" / "Ministry of Works") are not falsely flagged.


def _seg_0258___lb_shrunk(*, L: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 258 (_lb_shrunk) - body verbatim from the legacy gate() (feature 022)."""

    def _lb_shrunk(L: Sequence[Any]) -> list[tuple[float, float]]:
        # a TILTED pair is judged by the true drawn quads (SAT), with the same estimation slack
        # the box test subtracts (2px x, 4px y) taken off each record in ITS OWN frame before
        # rotating - so the tilted verdict is the box verdict's geometry, rotated
        return label_quad([L[0] + 1.0, L[1] + 2.0, L[2] - 1.0, L[3] - 2.0, *L[4:]])

    return _kept(locals(), ('_lb_shrunk',))


def _seg_0259__i_2(*, _lb_shrunk: Any = _UNBOUND, i: Any = _UNBOUND, j: Any = _UNBOUND, labels: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 259 (i, j, ov) - body verbatim from the legacy gate() (feature 022)."""
    ov = [
        (i, j)
        for i in range(len(labels))
        for j in range(i + 1, len(labels))
        if (
            sat_overlap(_lb_shrunk(labels[i]), _lb_shrunk(labels[j]))
            if len(labels[i]) > 7 or len(labels[j]) > 7
            else min(labels[i][2], labels[j][2]) - max(labels[i][0], labels[j][0]) > 2 and min(labels[i][3], labels[j][3]) - max(labels[i][1], labels[j][1]) > 4
        )
    ]
    return _kept(locals(), ('i', 'j', 'ov'))


def _seg_0260__no_label_overlaps(*, check: Any = _UNBOUND, ov: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 260 (no_label_overlaps) - body verbatim from the legacy gate() (feature 022)."""
    check("no_label_overlaps", not ov, f"{len(ov)} overlapping label pair(s)")
    return _kept(locals(), ())


# A caption must HUG the thing it names. "Empty ground wins" (the label doctrine) used to be the
# only rule, and empty ground is plentiful - so a caption could satisfy it 55px out with nothing
# but bare land between it and its subject, reading as if it named whatever it had drifted next
# to (Tango's south "gate market" ended up nearer the flophouse than the stalls). The engine's
# standoff ladder now seats such a caption at the NEAREST clear spot and records the subject's
# box as element [6] of the label record; this measures the FINISHED gap from the recorded
# boxes, so it verifies the outcome rather than re-deriving the placer's own arithmetic.
#
# Only ladder-placed captions carry a referent. A district/zone caption ("samurai neighborhood",
# "agricultural district") names an AREA, not a feature, and is deliberately exempt - it is
# governed instead by city_labels_placed_with_subject.


def _seg_0261__adrift() -> dict[str, Any]:
    """Gate segment 261 (adrift) - body verbatim from the legacy gate() (feature 022)."""
    adrift = []  # type: ignore[var-annotated]
    return _kept(locals(), ('adrift',))


def _seg_0262__L(*, L: Any = _UNBOUND, adrift: Any = _UNBOUND, lab_gap: Any = _UNBOUND, lab_size: Any = _UNBOUND, labels: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 262 (L, adrift, lab_gap, lab_size) - body verbatim from the legacy gate() (feature 022)."""
    for L in labels:
        if len(L) < 7 or not L[6]:
            continue
        lab_size = (L[3] - L[1]) / 1.05  # the recorded box is ascent (0.8) + descender (0.25) tall (elements [0..3] stay the pre-tilt box, so this holds for tilted records too)
        # a TILTED caption's gap is measured from its true drawn quad (poly_gap, the rotated
        # sibling of box_gap - same measure, same 0-at-touch convention)
        lab_gap = poly_gap(label_quad(L), [(L[6][0], L[6][1]), (L[6][2], L[6][1]), (L[6][2], L[6][3]), (L[6][0], L[6][3])]) if len(L) > 7 else box_gap(L[:4], L[6])
        if lab_gap > LABEL_AIR_CAP * lab_size:
            adrift.append(f"{L[5]!r} {lab_gap:.0f}px from its subject (cap {LABEL_AIR_CAP * lab_size:.0f}px)")
    return _kept(locals(), ('L', 'adrift', 'lab_gap', 'lab_size'))


def _seg_0263__label_hugs_its_referent(*, adrift: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 263 (label_hugs_its_referent) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "label_hugs_its_referent",
        not adrift,
        f"caption(s) floating too far from the feature they name - the standoff ladder could not seat them near their subject, so move the subject or caption it by hand: {sorted(adrift)}",
    )
    return _kept(locals(), ())


# A caption naming a LINEAR feature must RUN ALONG it (GM 2026-08-08). The 2026-08-02 tilt
# fixed this for building glyphs and stopped at them, so "Imperial Road" still sat level beside
# Hoshizora's -27deg roadbed - level text against a diagonal subject, which is the same reason
# a level caption beside a rot=-16 inn read wrong. The ROAD caption is the linear case the gate
# can hold: the engine seats it itself, so there is no hand-placed anchor to excuse.
#
# `linear_tilt` is the SHARED definition, imported rather than restated (placement and its
# check read the same source - this skill's CLAUDE.md). That matters most for the part that
# looks like an exception: a road steeper than 45deg keeps a LEVEL caption (the GM's
# north-south convention - there is no second edge family to align with, so tilting would
# match nothing drawn), and because the clamp lives in one function the check demands level
# there rather than being silent about it. Tango (due N-S) and Nagahara (72deg) are gated as
# firmly as Hoshizora, they just expect 0.


def _seg_0264__rdpts(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 264 (rdpts, rlab) - body verbatim from the legacy gate() (feature 022)."""
    rlab, rdpts = M.get("road_label"), M.get("road")
    return _kept(locals(), ('rdpts', 'rlab'))


def _seg_0265__road_label_tilts_with_the_roadway(
    *,
    L: Any = _UNBOUND,
    check: Any = _UNBOUND,
    got_tilt: Any = _UNBOUND,
    i: Any = _UNBOUND,
    labels: Any = _UNBOUND,
    rdpts: Any = _UNBOUND,
    rl0: Any = _UNBOUND,
    rl1: Any = _UNBOUND,
    rlab: Any = _UNBOUND,
    rrec: Any = _UNBOUND,
    si: Any = _UNBOUND,
    want_tilt: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 265 (road_label_tilts_with_the_roadway) - body verbatim from the legacy gate() (feature 022)."""
    if rlab and rdpts and len(rdpts) > 1:
        rl0, rl1 = float(rlab[0]), float(rlab[1])  # bound out of the lambda: narrowing does not reach inside one
        si = min(range(len(rdpts) - 1), key=lambda i: seg_dist(rl0, rl1, rdpts[i], rdpts[i + 1]))
        want_tilt = linear_tilt(math.degrees(math.atan2(rdpts[si + 1][1] - rdpts[si][1], rdpts[si + 1][0] - rdpts[si][0])))
        # The caption's own record, found by POSITION: `road_label` is the anchor the engine drew
        # at, so the record is the one whose UNROTATED box centers on that anchor's x and straddles
        # its baseline. Matching that way rather than by text keeps the check independent of what
        # the road is called (and of a map that captions two roads).
        rrec = [L for L in labels if len(L) > 5 and abs((L[0] + L[2]) / 2 - rlab[0]) < 1.5 and L[1] <= rlab[1] <= L[3]]
        got_tilt = (float(rrec[0][7]) if len(rrec[0]) > 7 and rrec[0][7] else 0.0) if rrec else None
        check(
            "road_label_tilts_with_the_roadway",
            got_tilt is not None and abs(got_tilt - want_tilt) <= 1.0,
            f"the road caption is drawn at {got_tilt}deg where the roadway beside it runs at {want_tilt}deg - "
            f"a caption naming a road runs ALONG the road (a roadway steeper than 45deg keeps a level caption; see settlement.linear_tilt)",
        )
    return _kept(locals(), ('L', 'got_tilt', 'rl0', 'rl1', 'rrec', 'si', 'want_tilt'))


# the TITLE (the map's place name) must sit over BLANK space, not on a building / field / water / grove -
# the reader has to be able to read it. The generator searches for a clear box (crop_to_content first, so the
# search runs over the framed window); this verifies it landed clear. Solid features + the fields + pond.


def _seg_0266__ttl(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 266 (ttl) - body verbatim from the legacy gate() (feature 022)."""
    ttl = M.get("title")
    return _kept(locals(), ('ttl',))


def _seg_0267__title_clear_of_features(
    *,
    M: Any = _UNBOUND,
    _lb2: Any = _UNBOUND,
    _thit_now: Any = _UNBOUND,
    check: Any = _UNBOUND,
    fdef: Any = _UNBOUND,
    ftpx: Any = _UNBOUND,
    k: Any = _UNBOUND,
    lb2: Any = _UNBOUND,
    pcx: Any = _UNBOUND,
    pcy: Any = _UNBOUND,
    prx: Any = _UNBOUND,
    pry: Any = _UNBOUND,
    s: Any = _UNBOUND,
    sb: Any = _UNBOUND,
    tb: Any = _UNBOUND,
    thit: Any = _UNBOUND,
    ttl: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 267 (scalebar_matches_declared_scale, title_clear_of_features, title_has_placard) - body verbatim from the legacy gate() (feature 022)."""
    if ttl:
        tb = ttl["bbox"]
        tc = [(tb[0], tb[1]), (tb[2], tb[1]), (tb[2], tb[3]), (tb[0], tb[3])]
        thit = []
        for k in (
            "houses",
            "gardens",
            "threshing_yards",
            "groves",
            "dry_plots",
            "buildings",
            "manors",
            "religious",
            "flophouses",
            "storehouses",
            "merchant_estates",
            "ministries",
            "village_groves",
            # NOT "commons": the scrub is sparse GROUND COVER (a feathered grass scatter on open ground), not a
            # feature with a footprint, and a bold place name reads fine over it. Kept in step with
            # `_title_obstacles` in settlement.py - once the commons clothes the field's interior voids too it
            # covers nearly the whole map, so blocking on it would leave a title nowhere to sit.
            "marshes",
        ):
            for s in M.get(k, []):
                # THE POLY IS AUTHORITATIVE WHERE THERE IS ONE (2026-08-10): a scattered marsh
                # records a w/h AABB spanning its whole scatter - kikuta's pond fringe measures
                # 5,040 px across - so falling through to the box after the poly MISSES reports a
                # title sitting on ground the feature does not occupy. Only a record with no
                # outline is judged by its box.
                _thit_now = (
                    _box_hits_poly(tb, s["poly"])
                    if s.get("poly")
                    else ("w" in s and not (tb[2] < s["x"] - s["w"] / 2 or tb[0] > s["x"] + s["w"] / 2 or tb[3] < s["y"] - s["h"] / 2 or tb[1] > s["y"] + s["h"] / 2))
                )
                if _thit_now:
                    thit.append(k)
                    break
            if thit:
                break
        if not thit:
            for fdef in M.get("fields", []):
                if _box_hits_poly(tb, fdef["outline"]):
                    thit.append("fields")
                    break
        if not thit and M.get("pond"):
            pcx, pcy, prx, pry = M["pond"]
            if not (tb[2] < pcx - prx or tb[0] > pcx + prx or tb[3] < pcy - pry or tb[1] > pcy + pry):
                thit.append("pond")
        if not thit:
            # placed LABELS too: a title placard over a feature label erases it (caught 2026-07-23 on the
            # Tango content crop - the placard landed on the 'pauper ossuary mound' label)
            for lb2 in M.get("labels", []):
                _lb2 = label_aabb(lb2)  # a tilted caption's reach is its rotated AABB
                if not (tb[2] < _lb2[0] or tb[0] > _lb2[2] or tb[3] < _lb2[1] or tb[1] > _lb2[3]):
                    thit.append(f"label:{lb2[5]}")
                    break
        check(
            "title_clear_of_features",
            not thit,
            f"the map title sits on {thit[:2]} - it must go over BLANK space so the place name is readable (the generator's s.title() searches for a clear box; call it AFTER crop_to_content)",
        )
        # every settlement map shows a SCALE BAR (GM 2026-07-20, matching the Mode A compound sheets),
        # and the bar's declared distance must agree with the map's declared ft/px - the bar is 100
        # map-px, so ft = 100 x ftpx (100 hamlet/town, 200 village, 300 city). s.title() draws it, so
        # a manifest with a title but no scalebar means the generator predates the bar - regenerate.
        sb = M.get("scalebar")
        ftpx = M.get("meta", {}).get("ftpx", 1.0)
        check(
            "scalebar_matches_declared_scale",
            sb is not None and sb["ft"] == round(100 * ftpx),
            f"scalebar {sb} disagrees with (or is missing for) the declared scale of {ftpx} ft/px - the 100 map-px bar must read {round(100 * ftpx)} ft",
        )
        # ... and the block sits on its parchment PLACARD (GM 2026-07-21: ink over scrub speckle was hard
        # to read - the card keeps the title + scale legible over any ground cover). s.title() draws it;
        # a manifest without the record predates the card - regenerate.
        check(
            "title_has_placard",
            bool(ttl.get("placard")),
            "the title block records no placard - the parchment card under the title + scale bar is drawn by s.title(); regenerate the map",
        )
    return _kept(locals(), ('_lb2', '_thit_now', 'fdef', 'ftpx', 'k', 'lb2', 'pcx', 'pcy', 'prx', 'pry', 's', 'sb', 'tb', 'tc', 'thit'))
