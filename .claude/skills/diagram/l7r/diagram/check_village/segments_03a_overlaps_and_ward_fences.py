"""Gate segments (overlaps and ward fences; keys 0133_031-0196) - bodies verbatim, registry order preserved."""

import math
from collections.abc import Sequence
from typing import Any

from l7r.diagram.settlement import label_aabb, sat_overlap, torii_wall_conflicts

from .common_01_geometry import (
    _LABEL_CLASSIFIED,
    _OVERLAP_CLASSIFIED,
    _OVERLAP_SINGLETONS,
    _OVERLAP_STRUCTS,
    Poly,
    Pt,
    _struct_rect,
    point_in_poly,
    poly_dist,
    rect_corners,
    seg_dist,
    seg_intersect,
    segments_cross,
)
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
