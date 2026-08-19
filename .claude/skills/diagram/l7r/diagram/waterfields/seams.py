"""close_seams - reconcile a carved comb fan into ONE shared-bund fabric.

TWO ADJACENT BASINS SHARE ONE BUND (GM 2026-08-17, on Inashiro: *"a tiny little standalone
rectangle of earthen walls is just smack dab in the middle of where the field should be ... it
should basically always be the case that two adjacent rice paddies share a single earthen wall
rather than two different earthen walls"*).

THE RESEARCH BEHIND THE RULE (see `research/fields.md`, "Bunds are shared, and the fabric is
continuous"). An *aze* is a puddled-mud ridge 1-2 ft wide, re-plastered every spring (*azenuri*)
so each basin holds its 4-6 inches of standing water. It is the WALL BETWEEN two basins, and it
is built once: a second parallel ridge would double the annual azenuri, drain neither basin, and
strand the strip between them - inside an irrigated command area, the most valuable land there is.
Real paddy fabric is therefore one CONNECTED bund network whose lines meet at T-junctions; a
free-standing four-sided ring floating inside it is not a paddy at all. (The odd-shaped,
piecemeal parcels that fabric produces are the honest look - the tidy detached rectangle is a
modern land-consolidation read, which `research/fields.md` already flags as anachronistic.)

WHAT THIS REPLACES, and why the old pass could not get there. `_fill_wedges` sampled the fan on a
12 px grid, boxed each cluster of bare cells, and then SHRANK the box toward its own centroid
until it lapped its neighbors only shallowly. Three consequences, all of them the defect above:

- the box was sized from where the SAMPLES were, not from where the pocket's walls are, so a
  fitted tile stopped a few px short of the surrounding bunds on every side - a rectangle with its
  own four walls and a ribbon of bare floor around it;
- the shrink was uniform, so a tile lapping one neighbor retreated from all four;
- the acceptance test allowed every probe to sit up to 12 real ft INSIDE a neighbor as long as
  one probe stood on bare ground, which drew bund rings in the middle of other people's basins.

Measured on the pre-fix pool (2026-08-17, by `paddy_plot_seams_shared`): 52 doubled-bund plots on
Inashiro, 57 on Kashikawa, 64 on Mizuguchi, 81 on Sawada, plus a nested ring on each of the last
two. All four are at zero after this pass.

THE REPLACEMENT IS A DIFFERENT QUESTION, not a better search. Instead of guessing a rectangle and
retreating, take the bare ground EXACTLY as the carve left it - the command area, minus everything
already planted, minus the water and its banks - and give every piece of it to the fabric:

- a pocket wide enough to hold a basin is PLANTED, subdivided at the fan's own grain. Its outer
  boundary IS the surrounding plots' boundary, so the bunds coincide by construction rather than
  by tolerance, and its interior seams are cut from one box so they coincide too.
- a pocket too thin to hold a basin is ABSORBED into the neighbor it shares the most bund with.
  That is what welds a doubled bund into a single one: the strip stops being ground between two
  walls and becomes part of the basin on one side of it.

So the pass has one postcondition - every square foot inside the command area is planted, is
water, or is outside the fan - and `paddy_plot_seams_shared` is the gate that holds it.

IT RUNS LAST, after `_comb_toe_and_hem`. That order is load-bearing: the toe pass DROPS slivers
too acute to bund and re-hems every bund onto the drain bank, so anything that ran before it would
have its work reopened as fresh bare ground. Running afterwards means this pass reconciles what
the whole pipeline actually left, whichever stage left it.
"""

import math
import random
from collections.abc import Callable
from typing import Any

from shapely.errors import GEOSException
from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from .banks import (
    _GATE_MIN_APEX,
    _GATE_MIN_AREA,
    _TINT_END_FT,
    _TINT_MIN_APEX,
    _TINT_MIN_SOLIDITY,
    _TOE_MIN_APEX,
    _TOE_MIN_AREA,
    _WELD_MIN_APEX,
    _WELD_MIN_SOLIDITY,
    cell_area,
    dedup_ring,
    is_chevron,
    jog_steps,
    jog_vertices,
    pointed_ring,
    polyline_cum,
    tapers_to_a_point,
)
from .frame import BANK_MARGIN, Poly, Pt, _f_at_u, _Frame, taper_w
from .palette import FLOODED, RICE_GREENS

# The carve's own "too narrow to plant" side (`_sector_body_rows` / `_sector_canal_closers` both
# refuse an edge under 6 * grain), reused here so a pocket this pass plants is exactly a pocket the
# carve would have planted had its grid reached there. Below it the ground is a seam, not a basin.
MIN_PLOT_SIDE = 6.0

# Boolean geometry leaves hairline artifacts where two boundaries nearly graze; this is the width
# below which a feature is one of them rather than ground. A fifth of a drawn aze (AZE_FT 1.5, and
# never under 0.5 px), so the opening it drives cannot move anything the map can show.
_SPIKE = 0.25


def _parts(geom: BaseGeometry) -> list[Polygon]:
    """Simple polygons of `geom`, in a deterministic order (shapely does not promise one)."""
    out = [g for g in getattr(geom, "geoms", [geom]) if isinstance(g, Polygon) and not g.is_empty and g.is_valid]
    return sorted(out, key=lambda g: (round(g.bounds[0], 1), round(g.bounds[1], 1)))


def _despike(geom: BaseGeometry) -> BaseGeometry:
    """Open the geometry by a fraction of a pixel to shed hairline spurs.

    Subtracting one polygon from another that nearly grazes it leaves zero-width spikes: a vertex
    pair that runs out and straight back along the same line. On Inashiro one such spur reached
    5.5 px ACROSS a delivery ditch off a pocket that was correctly clipped to the ditch's bank, and
    the recorded ring failed `paddy_bunds_clear_the_supply_channels` - a bund vertex in the middle
    of the water that no bund was ever placed at. An opening (erode then dilate by the same amount)
    deletes anything narrower than 2 x SPIKE and restores every straight edge exactly, so a shared
    seam stays shared.

    MITRE JOINS, not the default round ones. A rounded opening is not idempotent on a real corner:
    it arcs every convex corner at SPIKE radius and samples the arc, which on the first run here
    turned 4-vertex basins into 130-vertex rings of near-duplicate points.

    AND THE RESULT IS INTERSECTED BACK WITH THE INPUT, so the opening can only ever REMOVE ground.
    A mitred offset extends an acute corner by up to `mitre_limit` times the offset in each of its
    two passes, and at the acute wedges where a pocket runs out between a ditch bank and a plot
    edge that was enough to push a corner ~5 px past the bank - putting a new basin's bund inside
    a delivery ditch, which is the very rule (`paddy_bunds_clear_the_supply_channels`) the pocket
    had been clipped to satisfy. Intersecting makes the pass monotone: whatever the offsets do,
    the output is a subset of the bare ground that was handed in.

    AND IT NEVER RAISES. Clipping a pocket to a grid cell can produce a ring carrying a zero-length
    edge, and GEOS refuses to offset one - `TopologyException: found non-noded intersection`, thrown
    from the middle of a map generation (`test_build_comb_supply_banks_hems_bunds_onto_the_channel_
    banks`, 2026-08-17). `buffer(0)` nodes the input first, which handles most of them; for the rest
    the honest answer is that this is a TIDYING step, so a geometry GEOS will not offset goes on
    un-tidied rather than taking the map down. Nothing downstream trusts it: every ring this pass
    records is round-tripped for validity before it is kept."""
    cleaned = geom.buffer(0)
    if cleaned.is_empty:
        return cleaned
    try:
        opened = cleaned.buffer(-_SPIKE, join_style="mitre", mitre_limit=2.0).buffer(_SPIKE, join_style="mitre", mitre_limit=2.0)
        return cleaned.intersection(opened)
    except GEOSException:
        return cleaned


def _ring(poly: Polygon) -> Poly:
    """A plot ring as the manifest records it: 1dp, no repeated closing vertex, and no vertex
    that rounding has collapsed onto its predecessor (a boolean result carries plenty)."""
    out: Poly = []
    for x, y in list(poly.exterior.coords)[:-1]:
        pt = (round(float(x), 1), round(float(y), 1))
        if not out or pt != out[-1]:
            out.append(pt)
    while len(out) > 3 and out[0] == out[-1]:
        out.pop()
    return out


def _water(channels: list[dict[str, Any]], g: float) -> BaseGeometry:
    """Every drawn course plus its BANK - the ground a bund may abut but never stand in.

    Buffered per SEGMENT at the local width, because the supply canals taper hard (14 px head to a
    couple at the tail): one buffer at the widest half-width would claim bank the fan really does
    plant, and re-open exactly the kind of strip this pass exists to close.

    AND A DISC AT EVERY INTERIOR VERTEX, which is not optional. Flat-capped segment buffers are
    rectangles, so two of them meeting at a bend leave a WEDGE of uncovered ground on the outside
    of the turn. Ten of Inashiro's new basins came out with a bund inside a delivery ditch through
    exactly those notches - the ground looked bare to this pass and was water to the gate. The
    discs close them without the over-claim a round CAP would add past the head and tail, where
    `supply_bank_clearance` reports `past` and the stroke governs nothing anyway."""
    strokes: list[BaseGeometry] = []
    for c in channels:
        pts = [(float(q[0]), float(q[1])) for q in c.get("pts") or []]
        if len(pts) < 2:
            continue
        w0 = float(c["w"])
        w1 = float(c.get("w_tail", w0))
        cum = polyline_cum(pts)
        tot = cum[-1] or 1.0

        def half(k: int, w0: float = w0, w1: float = w1, cum: list[float] = cum, tot: float = tot) -> float:
            return taper_w(w0, w1, cum[k] / tot) / 2 + BANK_MARGIN * g

        for i in range(len(pts) - 1):
            strokes.append(LineString([pts[i], pts[i + 1]]).buffer(half(i), cap_style="flat"))
        for i in range(1, len(pts) - 1):
            strokes.append(Point(pts[i]).buffer(half(i)))
    return unary_union(strokes) if strokes else Polygon()


def _band(F: _Frame, us: list[float], fs: list[float], f_far: float) -> Polygon:
    """The region between the sampled curve f(u) and a constant fall far outside the fan."""
    pts = [F.to_xy(u, f) for u, f in zip(us, fs, strict=True)]
    pts += [F.to_xy(us[-1], f_far), F.to_xy(us[0], f_far)]
    return Polygon(pts).buffer(0)


def _outside_command(F: _Frame, a_pts: Poly, dpts: Poly, field: Polygon, g: float, bank: Callable[[float], float]) -> BaseGeometry:
    """Ground the fan cannot command: below the collector, or upslope of the supply canal.

    The collector is extended LEVEL beyond both drawn ends (the same clamp `_fill_wedges` used and
    `floor_overhang` states): the command area's low boundary conceptually continues past the
    drawn water, so a low-u fork wedge still counts as commanded while the floating-diamond ground
    past the outfall does not. Where the canal does not reach a given u there is nothing upslope to
    exclude, so that sample falls back to a bound outside the fan entirely."""
    x0, y0, x1, y1 = field.bounds
    corners = [F.to_uf(x0, y0), F.to_uf(x1, y0), F.to_uf(x1, y1), F.to_uf(x0, y1)]
    ulo, uhi = min(u for u, _ in corners), max(u for u, _ in corners)
    flo, fhi = min(f for _, f in corners), max(f for _, f in corners)
    span = (uhi - ulo) + (fhi - flo) + 1.0
    # SAMPLE THE CURVES FINELY. The band is a polygon through sampled points, so between samples
    # its edge is a CHORD - and a chord across a bend in a wandering collector cuts inside the
    # curve, admitting ground the fan may not plant. A fixed 64 samples is ~23 px apart on a hamlet
    # fan, which was enough to put a new basin's bund in the collector on 4 of 24 cohort seeds. One
    # sample every 6 px is finer than the drain's own jitter, and the whole band costs one polyline
    # scan per sample.
    _n_u = max(64, int((uhi - ulo) / 6.0))
    us = [ulo + (uhi - ulo) * k / _n_u for k in range(_n_u + 1)]
    dus = [F.to_uf(*p)[0] for p in dpts]
    du_lo, du_hi = min(dus), max(dus)

    def drain_f(u: float) -> float:
        fd = _f_at_u(F, dpts, u)
        if fd is not None:
            return fd
        end = dpts[0] if abs(u - du_lo) < abs(u - du_hi) else dpts[-1]
        return F.to_uf(*end)[1]

    def canal_f(u: float) -> float:
        fc = _f_at_u(F, a_pts, u)
        return flo - span if fc is None else fc + 4 * g

    # The low bound is the collector's BANK IN FALL - `_drain_bank`, the very function `_carve`
    # hems its closing rank onto - not a flat margin. `_fill_wedges` used a flat 3 * grain, which
    # is neither: too much where the collector is narrow (it left the last residue of doubled bunds
    # along the fan's toe, wedges this pass was forbidden to reach) and too little downstream,
    # where the drain widens to DRAIN_FT[1] and `paddy_bunds_clear_the_collector` measures a
    # slope-leaned set-back that a flat margin does not cover. Same predicate as the placer, so
    # ground this pass plants is ground the carve would have been allowed to plant.
    below = _band(F, us, [drain_f(u) - bank(u) for u in us], fhi + span)
    above = _band(F, us, [canal_f(u) for u in us], flo - span)
    return unary_union([below, above])


def _open_to(pocket: Polygon, w: float) -> Polygon | None:
    """`pocket` with everything narrower than `w` removed, or None if nothing survives.

    THE TAPERING-SCRAP ESCAPE. A scrap that needles every basin it could join is almost always a
    TAPERING strip: wide enough to be real at one end, running out to nothing at the other. Welding
    all of it draws the host out to a point; welding none of it leaves a doubled bund. Neither is
    what a farmer does - they take the strip as far as it is worth walling and let the last sliver
    go, which is this function.

    The width to stop at is not a guess: `paddy_plot_seams_shared` ignores a gap under 3 ft on its
    own stated reasoning ("two bunds that close draw as one line"), so a tail left below that is
    invisible to the doubled-bund rule by the rule's OWN definition rather than by a tolerance
    tuned until the pool passed. So the weld gets the workable part and the sub-3-ft tail stays
    bare, which is also the "odd corner left unpaddied" the research describes.

    Mechanically this is `_despike`'s opening at a larger radius, with the same two safeguards and
    for the same reasons: MITRE joins (a rounded opening arcs every convex corner and explodes the
    vertex count) and INTERSECTING the result back with the input (a mitred offset can push an
    acute corner outward, and this pass must only ever REMOVE ground)."""
    try:
        opened = pocket.buffer(-w / 2, join_style="mitre", mitre_limit=2.0).buffer(w / 2, join_style="mitre", mitre_limit=2.0)
    except GEOSException:
        return None
    parts = _parts(pocket.intersection(opened.buffer(0)))
    if not parts:
        return None
    return max(parts, key=lambda p: p.area)


def _min_apex(ring: Poly) -> float:
    """The sharpest interior angle in `ring`, in degrees (180.0 for a ring too short to have one).

    `pointed_ring` answers the yes/no; this answers "how sharp", which is what lets `_absorb` RANK
    imperfect welds instead of only accepting or refusing them."""
    n = len(ring)
    if n < 3:
        return 180.0
    out = 180.0
    for i in range(n):
        a, v, c = ring[i - 1], ring[i], ring[(i + 1) % n]
        v1 = (a[0] - v[0], a[1] - v[1])
        v2 = (c[0] - v[0], c[1] - v[1])
        d1 = math.hypot(*v1) or 1.0
        d2 = math.hypot(*v2) or 1.0
        cs = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (d1 * d2)))
        out = min(out, math.degrees(math.acos(cs)))
    return out


def _absorb(pocket: Polygon, into: list[Polygon], grown: set[int], thin: float, g: float) -> bool:
    """Fold a too-thin pocket into the basin it shares the most bund with - the weld that turns two
    walls with a strip between them into the one wall a real aze is. The neighbor is chosen by
    SHARED BOUNDARY LENGTH rather than by distance or area: the basin whose wall actually forms
    most of this strip is the one whose farmer would have taken it in."""
    bx0, by0, bx1, by1 = pocket.bounds
    reach = pocket.buffer(0.4)
    ranked: list[tuple[float, int]] = []
    for j, q in enumerate(into):
        qx0, qy0, qx1, qy1 = q.bounds
        if qx1 < bx0 - 1 or qx0 > bx1 + 1 or qy1 < by0 - 1 or qy0 > by1 + 1:
            continue
        shared = q.boundary.intersection(reach).length
        if shared > 0.0:
            ranked.append((-shared, j))
    # EVERY candidate in turn, not just the best one. A union comes back as a MultiPolygon (the
    # strip meets that basin only at a point) or with a hole (it wraps the basin) often enough to
    # matter - 64 of 255 welds on Inashiro - and each failure leaves the doubled bund it was there
    # to close. The runner-up basin borders the same strip and usually takes it cleanly.
    _fallback: tuple[float, int, Polygon] | None = None
    _lumpy: tuple[float, int, Polygon] | None = None
    _chev: tuple[float, int, Polygon] | None = None
    _jogged: tuple[int, int, Polygon] | None = None
    for _neg, j in sorted(ranked):
        # dilate the scrap by a hair before the union. A scrap and the basin beside it only TOUCH
        # (they were cut from each other), and a union of two merely-touching polygons comes back
        # as a MultiPolygon or an invalid ring as often as not - which used to abandon the weld and
        # leave the doubled bund. 0.02 px is two orders below the 0.1 px the manifest records, so
        # it changes the geometry by nothing and the overlap by enough.
        merged = into[j].union(pocket.buffer(0.02)).buffer(0)
        if not isinstance(merged, Polygon) or merged.interiors:
            continue
        # SIMPLIFY CAN INVALIDATE. Douglas-Peucker moves vertices independently, and on the long
        # thin unions this pass makes that is enough to fold a ring back through itself: Inashiro
        # shipped a 10-vertex bow-tie basin whose outline crossed its neighbor's twice and read as
        # a doubled bund at the fan toe. Simplification here is only tidying, so a result that is
        # not a clean simple polygon is discarded in favor of the union it came from.
        simplified = merged.simplify(0.05)
        candidate = simplified if isinstance(simplified, Polygon) and simplified.is_valid and not simplified.interiors else merged
        # AND JUDGE THE RING THE MANIFEST WILL ACTUALLY CARRY. Validating the shapely polygon is
        # not enough: `_ring` rounds to 0.1 px afterwards, and on a near-degenerate weld that last
        # rounding is itself enough to cross two edges (settlement-review, Inashiro 2026-08-17,
        # basin #570 - a valid union recorded as a 13-vertex ring that folded back on itself into
        # an 875 sq ft lobe plus a 46 x 1.1 ft sliver). A crossing ring is invisible in ink under a
        # 1.5 px stroke, which is exactly why it has to be caught here rather than by eye: every
        # downstream consumer that measures basin geometry gets a MultiPolygon where it expects a
        # basin. So the recorded ring is round-tripped and the weld declined if it does not survive
        # - the runner-up basin takes the scrap instead.
        if not Polygon(_ring(candidate)).is_valid:
            continue
        # AND A WELD MUST NOT MAKE A NEEDLE OUT OF THE BASIN THAT TAKES THE SCRAP. Measured by
        # provenance on Inashiro (2026-08-17): with the carve and `_plant` both refusing needles,
        # EVERY surviving one was `carved_grown` - a perfectly good basin that welding a toe strip
        # into it drew out to a point. Absorbing is meant to turn two walls into one, not to trade
        # a doubled bund for an unworkable apex, so this is judged in the same ladder as the
        # MultiPolygon, hole and bow-tie rejections above and for the same reason: the runner-up
        # basin borders the same strip and usually takes it cleanly.
        #
        # AND IF NO NEIGHBOR CAN TAKE IT, THE SCRAP STAYS BARE, WHICH IS THE HONEST ANSWER. A
        # strip that needles every basin it touches is the "odd corner left unpaddied" that the
        # research describes at a real fan toe - the fan's base floor (`comb_base_fill`) draws
        # under it, so it reads as the toe's own ground rather than as a hole, exactly as it does
        # for the slivers `_comb_toe_and_hem` drops.
        # MEASURE THE RING THE GATE MEASURES - the DEDUPED one, and nothing else. This guard used to
        # take min(raw, deduped): stricter, but stricter on a DIFFERENT measurement than the rule it
        # is protecting, which is not a margin at all. `paddy_plots_are_workable_basins` reads the
        # deduped ring, so an apex only the raw ring carries is invisible to the rule and must not be
        # able to veto a weld here. Placer-stricter-than-gate means a stricter THRESHOLD on the SAME
        # measurement (18 vs 15), never a second measurement bolted alongside it.
        _cand = dedup_ring(_ring(candidate), 1.0)
        _apex = _min_apex(_cand)
        if _apex < _WELD_MIN_APEX:
            # NOT GOOD ENOUGH, BUT REMEMBER IT - refusing outright is its own defect. Measured on
            # the 24-seed cohort: declining every needling weld traded two needles for two doubled
            # bunds (seeds 9 and 11) and took the cohort 22 -> 20, because a scrap that needles the
            # basin it would join is often a TAPERING strip whose only alternative is to lie bare
            # between two walls. Neither outcome is realistic, so the choice is not decline-or-
            # accept: it is WHICH NEIGHBOR takes it. The ranking above is by shared bund length,
            # which is the right first preference (the farmer whose wall already forms most of the
            # strip); when none of those is clean, the honest fallback is the neighbor that takes
            # the strip BEST rather than the one that shares the most of it.
            # BEFORE GIVING UP ON THIS NEIGHBOR, TRY THE WORKABLE PART OF THE SCRAP. `_open_to`
            # drops the tapering tail that is narrower than the doubled-bund rule's own 3 ft floor,
            # so the host takes the part worth walling and what is left is a sliver that rule
            # already treats as one line rather than two. This is what resolves cohort seeds 9 and
            # 11, where welding the whole scrap needled the host and welding none of it doubled a
            # bund - the choice was never between those two.
            _part = _open_to(pocket, thin)
            if _part is not None:
                _m2 = into[j].union(_part.buffer(0.02)).buffer(0)
                if isinstance(_m2, Polygon) and not _m2.interiors:
                    _s2 = _m2.simplify(0.05)
                    _c2 = _s2 if isinstance(_s2, Polygon) and _s2.is_valid and not _s2.interiors else _m2
                    _r2 = _ring(_c2)
                    # ...and the partial weld faces the arrowhead test too. This path had only the
                    # apex guard, and a provenance probe found it was where the survivors came from:
                    # ZERO chevrons entered `close_seams` on Inashiro and Mizuguchi and three left,
                    # because welding the workable PART of a scrap is exactly how a basin acquires a
                    # point at one end and a bite in its side.
                    if Polygon(_r2).is_valid and _min_apex(dedup_ring(_r2, 1.0)) >= _WELD_MIN_APEX and not is_chevron(_r2):
                        into[j] = _c2
                        grown.add(j)
                        return True
            if _fallback is None or _apex > _fallback[0]:
                _fallback = (_apex, j, candidate)
            continue
        # AND A WELD MUST NOT MAKE A LUMP OUT OF THE HOST EITHER. The ranking above is by shared
        # bund length, which is blind to the SHAPE the union comes out as, and both guards it has
        # already passed measure an apex - so a union that grows a blunt-cornered lobe or an
        # out-and-back prong sails through them (settlement-review, Mizuguchi and Sawada
        # 2026-08-17; see `_WELD_MIN_SOLIDITY` for the measurements and for why solidity rather
        # than an angle). Treated exactly like a needling weld, and for the same reason: the
        # runner-up borders the same strip and usually takes it in a shape a farmer would
        # recognize, but refusing every host outright would trade the lump for a doubled bund.
        # A WELD MUST NOT MAKE AN ARROWHEAD EITHER, and this is a third measurement rather than a
        # tighter one: a chevron is pointed AND notched, and this ladder's apex guard (18 deg) and
        # solidity guard (0.85) each pass a ring at 39 deg / 0.878 that is plainly an arrowhead. See
        # `_CHEVRON_MIN_APEX` for the measured population. Same treatment as a lump - remembered, not
        # refused outright, so the scrap still finds a host when no clean one exists.
        _sol = candidate.area / (candidate.convex_hull.area or 1.0)
        if is_chevron(_ring(candidate)):
            if _chev is None or _sol > _chev[0]:
                _chev = (_sol, j, candidate)
            continue
        if _sol < _WELD_MIN_SOLIDITY:
            if _lumpy is None or _sol > _lumpy[0]:
                _lumpy = (_sol, j, candidate)
            continue
        # AND A WELD MUST NOT MAKE THE HOST'S WALL STEP SIDEWAYS. This is the third shape complaint
        # in the same ladder and it is blind to the two above it by construction: a scrap welded on
        # flush at both its own ends but a few feet PAST the host's leaves the host a rectangular
        # tab, which is a right-angled 90/270 corner pair (no apex to fail) at solidity ~0.8 (no lump
        # to fail) - and reads as an earthen wall randomly zigzagging, which is how the GM found it
        # (2026-08-18, `jog_steps`). It arises because `_plant` grids a pocket at ITS OWN pitch, so
        # the offcuts it hands back are cut where neither the row above nor the row below has a seam;
        # welding one alternately up and down builds the staircase. Judged as a DELTA against the
        # host's current ring rather than as an absolute, for the reason the apex guard gives about
        # measuring what the rule measures: a host that already carries a step must not be barred
        # from taking in the scrap beside it because of a step that was there first.
        _jog = jog_steps(_ring(candidate), g) - jog_steps(_ring(into[j]), g)
        if _jog > 0:
            if _jogged is None or _jog < _jogged[0]:
                _jogged = (_jog, j, candidate)
            continue
        into[j] = candidate
        grown.add(j)
        return True
    # THE LEAST-JOGGING WELD, ahead of both. When no host takes the scrap without complaint, a wall
    # standing a few feet off line is the mildest of the three: the basin is still a basin a farmer
    # would build, which is more than the lump or the needle can say. Ranked by how many steps the
    # weld ADDS, so a host that takes the scrap with one step beats one that takes it with three.
    if _jogged is not None:
        _, j, candidate = _jogged
        into[j] = candidate
        grown.add(j)
        return True
    # THE LEAST-LUMPY WELD, ahead of the needle fallback below. A lobe is a milder defect than an
    # unworkable apex - it is a basin a farmer would call awkward rather than one they could not
    # flood - so when no host takes the scrap cleanly, the shape complaint yields before the
    # workability one does.
    if _lumpy is not None:
        _, j, candidate = _lumpy
        into[j] = candidate
        grown.add(j)
        return True
    # ...then the least-bad ARROWHEAD, behind the lump. A chevron is the worse read of the two - a
    # lump is an awkward basin, an arrowhead does not read as a basin at all - so it is the last
    # shape the ladder will accept, and only when no other host will take the scrap. (Merged
    # 2026-08-18: this tier and the jog tier above were added independently by two sessions to the
    # same ladder. Order is by how badly the shape reads - jog, then lump, then arrowhead - so the
    # mildest complaint yields first, which is the ordering rule the two tiers above already state.)
    if _chev is not None:
        _, j, candidate = _chev
        into[j] = candidate
        grown.add(j)
        return True
    # THE LEAST-BAD WELD, and only if it still clears the GATE. `_WELD_MIN_APEX` is the placer's
    # margin, not the rule; a union between the gate line and that margin is a basin the gate
    # ACCEPTS, so welding it is strictly better than leaving a doubled bund. Below the gate line it
    # is a real needle and the scrap stays bare instead - the "odd corner left unpaddied" the
    # research describes, which the Sawada review confirmed is invisible in ink (the fan's base
    # floor is drawn in the same fill as a plot interior, measured at the pixel).
    if _fallback is not None and _fallback[0] >= _GATE_MIN_APEX + 1.0:
        _, j, candidate = _fallback
        into[j] = candidate
        grown.add(j)
        return True
    return False


def _seam_cuts(lo: float, hi: float, want: float, marks: list[float]) -> list[float]:
    """Where to cut a pocket between `lo` and `hi`, aiming for cells about `want` across.

    CUT WHERE THE FABRIC ALREADY BREAKS. A pocket's own outline IS the surrounding basins' outline,
    so the coordinates of its corners are the positions at which the rows either side of it end -
    and cutting there means a piece this pass hands back lines up with the basin it will be welded
    into. Cutting on a fresh grid instead, which is what this did first, puts every seam where
    NEITHER row breaks: on a hamlet that is `plot_across`, 48 ft, and it is the mechanism behind the
    staircase the GM reported (2026-08-18) - the offcuts land mid-basin on both sides and get welded
    alternately up and down.

    The ideal spacing still governs; a mark only wins when it is within 0.35 of a cell of where the
    next cut wanted to be, and never when it would leave a sliver under a third of a cell on either
    side. THAT NUMBER IS A MEASURED CEILING, not a taste: at 0.40 and above the cut follows the
    neighbours far enough to move the fan's envelope, and Kashikawa's dry hem - which tiles against
    that envelope - shifts onto a footbridge and trips `features_do_not_overlap`. Steps across the
    four scripted hamlets go 2/2/9/3 at 0.35 and 1/2/8/1 at 0.40, so the last four cost a regression
    in another subsystem and are not taken (see `future-work.md`). Where the neighbours break nowhere near the right place the grid falls back to the even
    spacing it always used, which is the honest answer: there is no seam there to line up with."""
    span = hi - lo
    if span <= 1.5 * want or want <= 0.0:
        return [lo, hi]
    keep = want / 3.0
    cuts = [lo]
    while hi - cuts[-1] > 1.5 * want:
        target = cuts[-1] + want
        near = [m for m in marks if cuts[-1] + keep <= m <= hi - keep and abs(m - target) <= 0.35 * want]
        cuts.append(min(near, key=lambda m: abs(m - target)) if near else target)
    cuts.append(hi)
    return cuts


def _plant(F: _Frame, pocket: Polygon, plot_across: float, row_step: tuple[float, float], half: float) -> tuple[list[Polygon], list[Polygon]]:
    """Subdivide a plantable pocket at the FAN'S OWN GRAIN and hand back the basins.

    One giant slab would dwarf the ~0.08-acre plots around it (the relative-size doctrine), so the
    pocket's (u, f) box is cut into ~plot_across x row_step cells and the pocket clipped to each.
    Cells are cut from ONE box, so neighboring pieces share their seam exactly; the pocket's own
    outline is the surrounding plots' outline, so the outer bunds are shared too.

    Returns `(basins, offcuts)`. Offcuts - cells the grid cut too thin to bund - are handed BACK
    rather than welded here, so the caller can offer them the whole field to weld into. Welding
    them among their own siblings was tried first and left five toe wedges bare on Inashiro: a
    scrap whose only sibling refuses the union (the two meet at a point) had nowhere else to go,
    and stayed a doubled bund."""
    x0, y0, x1, y1 = pocket.bounds
    corners = [F.to_uf(x0, y0), F.to_uf(x1, y0), F.to_uf(x1, y1), F.to_uf(x0, y1)]
    ulo, uhi = min(u for u, _ in corners), max(u for u, _ in corners)
    flo, fhi = min(f for _, f in corners), max(f for _, f in corners)
    # THE POCKET'S OWN CORNERS ARE THE SURROUNDING BASINS' CORNERS, so they are where the fabric
    # actually breaks - see `_seam_cuts`.
    marks = [F.to_uf(float(q[0]), float(q[1])) for q in pocket.exterior.coords]
    us = _seam_cuts(ulo, uhi, plot_across, sorted(m[0] for m in marks))
    fs = _seam_cuts(flo, fhi, (row_step[0] + row_step[1]) / 2, sorted(m[1] for m in marks))
    cells: list[Polygon] = []
    for ua, ub in zip(us[:-1], us[1:], strict=True):
        for fa, fb in zip(fs[:-1], fs[1:], strict=True):
            cell = Polygon([F.to_xy(ua, fa), F.to_xy(ub, fa), F.to_xy(ub, fb), F.to_xy(ua, fb)])
            cells += _parts(_despike(pocket.intersection(cell)))
    good = [c for c in cells if not c.buffer(-half).is_empty]
    if not good:
        return [pocket], []  # the grid cut the one thick part up; the pocket is a basin as it stands
    return good, [c for c in cells if c.buffer(-half).is_empty]


def _tab_cut(poly: Poly, g: float, rb: Pt, rc: Pt) -> set[Pt] | None:
    """The four vertices of the TAB this step is one end of, or None if the step stands alone.

    A tab is the shape a weld leaves: the wall steps off its line, runs along a second line for a
    stretch, and steps back. Cutting one of its risers turns the tab into a TRIANGLE, so a row of
    tabs becomes a rank of long diagonal slashes - which is a different artifact, not a fix, and was
    exactly what Inashiro's east flank turned into when this cut did not exist. Dropping all four
    vertices hands the whole strip to the basin on the other side and the wall runs on unbroken.

    A TAB SHOWS UP AS ONE STEP, NOT TWO, which is the thing to know before editing this. `jog_steps`
    is directed - it wants the wall to resume in the SAME direction - and a tab's two risers face
    opposite ways, so only the second of them is ever reported. The first is found by walking BACK
    along the ring from the reported riser: one edge for the tab's own run, one more for the riser
    that opened it, and that riser must oppose the reported one to within a quarter of its length."""
    ring = dedup_ring([(float(q[0]), float(q[1])) for q in poly], 0.5)
    n = len(ring)
    if n < 6:
        return None
    at = {(round(v[0], 1), round(v[1], 1)): k for k, v in enumerate(ring)}
    if rb not in at or rc not in at:
        return None
    j = at[rb]
    if (j + 1) % n != at[rc]:
        return None
    riser = (ring[at[rc]][0] - ring[j][0], ring[at[rc]][1] - ring[j][1])
    for back in (True, False):
        if back:
            b, c = ring[(j - 2) % n], ring[(j - 1) % n]
        else:
            b, c = ring[(j + 2) % n], ring[(j + 3) % n]
        other = (c[0] - b[0], c[1] - b[1])
        if riser[0] * other[0] + riser[1] * other[1] >= 0.0:
            continue  # the two risers go the same way: a staircase, not a tab
        if abs(math.hypot(*other) - math.hypot(*riser)) > 0.25 * math.hypot(*riser):
            continue  # a riser of a different depth is a different feature, not this tab's other end
        return {rb, rc, (round(b[0], 1), round(b[1], 1)), (round(c[0], 1), round(c[1], 1))}
    return None


def _unjog(plots: list[dict[str, Any]], g: float, floor: float, water: BaseGeometry, outside: BaseGeometry) -> None:
    """Straighten a wall that still steps, by TRADING the corner between the two basins that share it.

    WHY A REPAIR AND NOT A BETTER CHOICE (GM 2026-08-18, on Inashiro: *"instead of just continuing on
    and meeting at the four way intersection ... it just goes sharply to the left before going down"*).
    `_absorb`'s jog guard picks the host whose wall does not end up stepping, and that is worth having,
    but it can only choose - and the steps that survive it are the ones where the ground had exactly
    one home, so no choice existed. Those need the wall MOVED, which is this pass.

    THE MOVE IS THE ONE A FIELD WOULD MAKE: run the wall from where it starts to where it resumes, so
    the hop becomes a bend. `research/fields.md` says a bend is period-correct and a parcel fitted to
    its neighbours is the honest look; what it never describes is a wall doubling back, which is
    exactly and only what this removes.

    IT TRADES GROUND RATHER THAN DROPPING VERTICES, and that distinction is the whole difference
    between this and the version that did not work. Dropping the step's two vertices from every ring
    that carries them looks partition-preserving and is not: the two rings either side of a wall have
    DIFFERENT neighbouring vertices, so the chords they close over differ, and on Inashiro rings 460
    and 592 lost 400 px2 and gained 259 - the difference being bare floor with a bund each side of it.
    Taking the corner as a polygon (`was.difference(now)`) and handing that same polygon to the
    neighbour conserves the ground by construction, whatever the two rings look like.

    EVERY REFUSAL BELOW IS A RULE THIS PASS WOULD OTHERWISE BREAK, and each was measured breaking it:

    - a **T-junction** (three rings on the corner): each cuts its corner a different way and the patch
      between them is bare floor - `paddy_plot_seams_shared`, 4 plots.
    - a corner whose two vertices are **not held by the same basins**: the wall then moves on one side
      only - `paddy_plot_seams_shared`, 2 plots.
    - a trade that would **shrink both** rings, or shrink the only ring on the wall: the ground given
      up lies bare rather than moving.
    - a repair that takes a basin under the fan's **size floor** - `paddy_basins_are_worth_their_bund`,
      1 basin at 16% of the cell. Judged at the GATE's line (`_GATE_MIN_AREA`, 0.20 of the design
      cell) rather than the placer's margin above it (`_TOE_MIN_AREA`, 0.25), for the same reason the
      apex is judged at the gate's 15 deg: a repair is not a placement choice, so it is allowed
      exactly where the map would have been allowed to draw it. Measured, the difference is not
      cosmetic - the basin that has to GIVE UP the corner is usually the one near the floor, and the
      placer's margin refused the repair on rings the gate would have accepted.
    - a repair that draws a basin out to a **needle** - `paddy_plots_are_workable_basins`, judged on the
      ring the gate reads at the gate's own 15 deg, because a repair is not a placement choice: it is
      allowed exactly where the map would have been allowed to draw it.
    - a repair whose new wall lands **in the water or off the command area** - the chord cuts the corner,
      and a corner the carve put there was often hugging a delivery ditch's bank
      (`paddy_bunds_clear_the_supply_channels`, Mizuguchi). Tested against the same `water` and
      `outside` geometries the pass itself uses to decide what may be planted, which are strictly
      stricter than the gate's own sampled clearance.

    IT RUNS UNTIL NOTHING MOVES, capped, because straightening one step can retire or expose
    another and the cheapest cut for a ring often only becomes available once its neighbour has been
    repaired. The cap is a backstop against a repair that undoes itself, not a tuning knob - on every
    pool map the set converges in three rounds or fewer."""
    for _ in range(6):
        moved = False
        seen: set[frozenset[Pt]] = set()
        for i in range(len(plots)):
            for b, c in jog_vertices([(float(q[0]), float(q[1])) for q in plots[i]["poly"]], g):
                rb = (round(b[0], 1), round(b[1], 1))
                rc = (round(c[0], 1), round(c[1], 1))
                if frozenset((rb, rc)) in seen:
                    continue
                seen.add(frozenset((rb, rc)))
                # THE WHOLE TAB FIRST, WHERE THERE IS ONE - and this is the cut that matters most,
                # because it is the only one that leaves a STRAIGHT wall. A welded tab is TWO steps a
                # few feet apart on the same ring: the wall drops to the tab's line, runs along it,
                # and climbs back. Cutting either corner on its own turns the tab into a triangle, so
                # a row of tabs becomes a row of long diagonal slashes - measured by eye on Inashiro's
                # east flank, where the staircase was gone and a rank of parallel diagonals had taken
                # its place, which is a different artifact rather than a fix. Dropping all four of the
                # tab's vertices hands the whole strip to the basin on the other side and the wall
                # runs on unbroken, which is what the fabric should have had.
                _tab = _tab_cut(plots[i]["poly"], g, rb, rc)
                _cuts = ([_tab] if _tab else []) + [{rb}, {rc}, {rb, rc}]
                # GENTLEST CUT NEXT. Dropping the end of the hop that sits on the LONGER run
                # absorbs the offset over the longer distance, so the wall slants where it used to
                # step and the two basins trade a sliver rather than a corner; dropping the other end
                # is the same repair over a shorter run; dropping both cuts the corner off square and
                # is the crudest, because it hands over the whole triangle and is what drove the
                # needle refusals (230 of 580 trades, 2026-08-18) when it was the only cut on offer.
                # A DEAD LEVER, MEASURED, so the next reader does not pull it: a wall belongs to TWO
                # basins, and letting the one on the other side attempt the repair when this one is
                # refused looks like it should help - the two cuts are genuinely different. It buys
                # one step in four maps (5/5/7/5 -> 5/5/6/5) and costs 70% of the regeneration, because
                # finding the other side means scanning every plot's vertices for the corner.
                for _drop in _cuts:
                    if _trade(plots, i, _drop, g, floor, water, outside):
                        moved = True
                        break
        if not moved:
            return


def _trade(
    plots: list[dict[str, Any]],
    i: int,
    drop: set[Pt],
    g: float,
    floor: float,
    water: BaseGeometry,
    outside: BaseGeometry,
) -> bool:
    """Move the wall of plot `i` past the step at (`rb`, `rc`), giving the corner it cuts off to
    whatever lies on the other side. Returns whether the trade happened.

    THE NEIGHBOUR IS FOUND BY GEOMETRY, NOT BY SHARED VERTICES, and that is what makes the pass
    actually reach the steps. The first version required both ends of the hop to be held by the same
    basins, on the reasoning that a shared wall is shared vertex for vertex - true of the carve, and
    false of exactly the fabric this pass exists to repair: a welded tab's two base vertices belong to
    the host, while the basin under it may touch only one of them. Measured, that rule refused **399
    of 580 steps**, more than every other refusal combined. The corner is a POLYGON; who it belongs to
    is a question about that polygon's boundary, and `_absorb` has answered the same question by
    shared boundary length since it was written."""
    cut = [q for q in plots[i]["poly"] if (round(q[0], 1), round(q[1], 1)) not in drop]
    if len(cut) < 3:
        return False
    # AND THE REPAIR MUST ACTUALLY RETIRE THE STEP. Dropping ONE end of the hop absorbs the offset as
    # a slant over the run beside it - a bend, which is what the fabric should have had - and dropping
    # BOTH cuts the corner off square. Either can fail to help on an awkward ring, and a repair that
    # merely moves a step somewhere else is worse than none, so the ring is re-measured rather than
    # assumed.
    if jog_steps([(float(q[0]), float(q[1])) for q in cut], g) >= jog_steps([(float(q[0]), float(q[1])) for q in plots[i]["poly"]], g):
        return False
    try:
        was = Polygon(plots[i]["poly"]).buffer(0)
        now = Polygon(cut).buffer(0)
        if not isinstance(now, Polygon) or not now.is_valid or now.is_empty or now.area < floor:
            return False
        gives = now.area < was.area
        traded = was.difference(now) if gives else now.difference(was)
        if traded.is_empty or traded.area <= 0.0:
            return False
        near = traded.buffer(0.4)
        # THE NEW WALL, WHICH IS THE ONLY GEOMETRY THIS REPAIR INVENTS. A basin's bund is SUPPOSED to
        # lie against a delivery ditch's bank - the carve hems it there on purpose - so testing the
        # whole ring against the water refuses repairs that never went near a channel (measured: 926
        # of 1,368 trades). What can actually put a bund in the water is the edge the cut creates,
        # where the chord crosses a corner the carve had wrapped around a bank
        # (`paddy_bunds_clear_the_supply_channels`, Mizuguchi). Tested against the same `water` and
        # `outside` the pass uses to decide what may be planted at all - strictly stricter than the
        # gate's own sampled clearance.
        _had = {(min(_va, _vb), max(_va, _vb)) for _va, _vb in zip(plots[i]["poly"], plots[i]["poly"][1:] + plots[i]["poly"][:1], strict=True)}
        _new = _ring(now)
        for _va, _vb in zip(_new, _new[1:] + _new[:1], strict=True):
            if (min(_va, _vb), max(_va, _vb)) in _had:
                continue
            _seg = LineString([_va, _vb])
            if (not water.is_empty and _seg.intersects(water)) or (not outside.is_empty and _seg.intersects(outside)):
                return False
        if len(_new) < 3 or pointed_ring(dedup_ring(_new, 1.0), _GATE_MIN_APEX):
            return False
        if gives:
            # EVERY BASIN ALONG THE CORNER IN TURN, best first - the same ladder `_absorb` runs, and
            # for the same reason. The corner has to go somewhere, and the basin whose bund forms most
            # of its edge is the right first preference; but a corner welded into one basin can draw it
            # out to a needle while the runner-up takes it cleanly, and refusing outright leaves the
            # step standing. Measured before this loop existed: 366 of 1,468 trades refused on a
            # needle and 248 more on a malformed union, against 260 that went through.
            ranked: list[tuple[float, int]] = []
            nx0, ny0, nx1, ny1 = near.bounds
            for k, q in enumerate(plots):
                if k == i or len(q["poly"]) < 3:
                    continue
                if max(v[0] for v in q["poly"]) < nx0 or min(v[0] for v in q["poly"]) > nx1 or max(v[1] for v in q["poly"]) < ny0 or min(v[1] for v in q["poly"]) > ny1:
                    continue
                qp = Polygon(q["poly"]).buffer(0)
                if not isinstance(qp, Polygon) or not qp.is_valid or qp.is_empty or not qp.intersects(near):
                    continue
                shared = qp.boundary.intersection(near).length
                if shared > 0.0:
                    ranked.append((-shared, k))
            for _neg, k in sorted(ranked):
                grew = (Polygon(plots[k]["poly"]).buffer(0).union(traded.buffer(0.02))).buffer(0)
                if not isinstance(grew, Polygon) or grew.interiors or grew.is_empty or grew.area < floor:
                    continue
                gr = _ring(grew)
                if len(gr) < 3 or not Polygon(gr).buffer(0).is_valid or pointed_ring(dedup_ring(gr, 1.0), _GATE_MIN_APEX):
                    continue
                rings = [(i, _new), (k, gr)]
                break
            else:
                return False
        else:
            # THE GROUND HAS TO COME FROM SOMEWHERE. Whatever the corner overlaps gives it up - all of
            # them, not the best one, or two basins end up claiming the same square foot. What it
            # overlaps nothing of is bare floor, and taking that in is free and is the point.
            rings = [(i, _new)]
            tx0, ty0, tx1, ty1 = traded.bounds
            for k, q in enumerate(plots):
                if k == i or len(q["poly"]) < 3:
                    continue
                if max(v[0] for v in q["poly"]) < tx0 or min(v[0] for v in q["poly"]) > tx1 or max(v[1] for v in q["poly"]) < ty0 or min(v[1] for v in q["poly"]) > ty1:
                    continue
                qp = Polygon(q["poly"]).buffer(0)
                if not isinstance(qp, Polygon) or not qp.is_valid or qp.is_empty or qp.intersection(traded).area <= 0.01:
                    continue
                lost = qp.difference(traded).buffer(0)
                if not isinstance(lost, Polygon) or lost.interiors or lost.is_empty or lost.area < floor:
                    return False
                lr = _ring(lost)
                if len(lr) < 3 or not Polygon(lr).buffer(0).is_valid or pointed_ring(dedup_ring(lr, 1.0), _GATE_MIN_APEX):
                    return False
                rings.append((k, lr))
    except GEOSException:
        return False
    for k, r in rings:
        plots[k]["poly"] = r
    return True


def close_seams(
    R: random.Random,
    F: _Frame,
    plots: list[dict[str, Any]],
    envelope: Poly,
    g: float,
    channels: list[dict[str, Any]],
    plot_across: float,
    row_step: tuple[float, float],
    a_pts: Poly,
    dpts: Poly,
    bank: Callable[[float], float],
) -> None:
    """Plant or absorb every scrap of bare ground the carve left inside the command area, so that
    each basin's bund is shared with whatever lies on the other side of it. Mutates `plots` in
    place: absorbed neighbors get a new `poly`, planted pockets are appended."""
    if not plots or len(envelope) < 3:
        return
    half = MIN_PLOT_SIDE * g / 2
    # A RING THAT CROSSES ITSELF IS NOT A BASIN, and it is drawn as ink whatever the manifest thinks.
    # Sawada shipped one: ring 688 at (167, 2558), four vertices whose edges 1-2 and 3-0 cross, and
    # the SVG carries it verbatim as a `<polygon>` (settlement-review 2026-08-18). It is INVISIBLE -
    # the neighbor painted after it covers the stray edge and the nonzero fill hides the bow - so no
    # amount of looking would have found it; what makes it worth removing is that it is not a simple
    # polygon, so every shape metric computed on it is meaningless. It scores solidity 0.43, the
    # worst on the sheet, and the area floor cannot reach it because its shoelace area is 2.9x the
    # floor. This pass already drops a WELD whose rounded ring will not survive validation, on
    # exactly the argument that "bare ground is an honest thing to record, a crossing ring is not";
    # a CARVED plot had no equivalent. One ring in 818 fails it, so the cost is a scrap of floor the
    # fan's base fill already covers.
    #
    # REPAIR, DO NOT DROP - measured. `buffer(0)` nodes a bow-tie into valid parts and the largest
    # is the basin the carve meant; keeping it holds the plot COUNT, so the shared placement RNG
    # does not re-roll and the map barely moves. Dropping instead cost two cohort seeds
    # (`features_do_not_overlap`, `lanes_reach_something`) purely through that rotation, on top of
    # the bare-ground problem below. A ring `buffer(0)` cannot rescue is still dropped.
    #
    # IT RUNS FIRST, not last, and that ordering is the whole fix. Dropped AFTER the plant/absorb
    # passes the ring's ground is simply gone, and the neighbor's wall is left standing alone -
    # 12 of 48 cohort seeds failed `paddy_plot_seams_shared` that way. Dropped HERE the ground is
    # just more bare pocket, and this pass reclaims it like any other.
    for _p in plots:
        if len(_p["poly"]) < 3 or Polygon(_p["poly"]).is_valid:
            continue
        _fixed = _parts(Polygon(_p["poly"]).buffer(0))
        if not _fixed:
            continue
        # ...and the repaired ring faces the same bar every other basin does. Noding a bow-tie can
        # leave the surviving lobe pointed - cohort seed 20 came out as a needle and tripped
        # `paddy_plots_are_workable_basins` - so a repair that is not a workable basin is refused and
        # the ground returns to the bare pocket below, which is this pass's standing answer for a
        # scrap. Judged at the GATE's own threshold, since a repair is not a placement choice.
        _cand = _ring(max(_fixed, key=lambda q: q.area))
        if len(_cand) >= 3 and not pointed_ring(dedup_ring(_cand, 1.0), _GATE_MIN_APEX):
            _p["poly"] = _cand
    plots[:] = [_p for _p in plots if len(_p["poly"]) >= 3 and Polygon(_p["poly"]).is_valid]
    keep = [Polygon(p["poly"]).buffer(0) for p in plots]
    field = Polygon(envelope).buffer(0)
    outside = _outside_command(F, a_pts, dpts, field, g, bank)
    water = _water(channels, g)
    carved = len(keep)
    grown: set[int] = set()
    # TWICE ROUND. Welding a scrap into a basin changes which basin borders the NEXT scrap, and
    # planting a pocket gives its neighbors a new edge to weld against - so a second look at the
    # bare ground reaches scraps the first pass could not place (three of Inashiro's toe wedges,
    # where a strip's only candidate refused the union until the basin beside it had grown). A
    # third round finds nothing on any pool map: the set converges because every round can only
    # shrink the bare ground.
    for _round in range(2):
        bare = field.difference(unary_union(keep)).difference(water).difference(outside)
        basins: list[Polygon] = []
        scraps: list[Polygon] = []
        for pocket in _parts(bare):
            for piece in _parts(_despike(pocket.simplify(0.05))):
                if piece.buffer(-half).is_empty:
                    scraps.append(piece)
                else:
                    got, offcuts = _plant(F, piece, plot_across, row_step, half)
                    # A NEEDLE IS A SCRAP, NOT A BASIN - it just does not look like one to the
                    # thinness test above. `buffer(-half).is_empty` asks "is this too thin
                    # ANYWHERE to be a plot", which a LONG wedge passes on the strength of its
                    # middle while its point is still unworkable; that is how the fan-toe sunburst
                    # survived both this pass and `_comb_toe_and_hem`'s inradius drop (GM realism
                    # ruling 2026-08-17 - see `_TOE_MIN_APEX`). So re-judge what `_plant` hands
                    # back by APEX as well, and send the needles down the scrap path, where
                    # `_absorb` welds each into the basin it shares the most bund with. That is
                    # this module's own research answer for an unplantable scrap ("taken into the
                    # basin beside it rather than walled off on its own"), so the ground stays
                    # planted, the bund stays shared, and no bare floor is opened. BOTH rings, at
                    # the carve's generous 25 deg, for the reason the tint rule below gives: the
                    # merge retires some apexes and creates others, and the placer must stay
                    # strictly stricter than the gate's 15.
                    # A FRAGMENT IS A SCRAP TOO, on exactly the same argument and for the same
                    # destination. `_plant` tiles at ~plot_across x row_step, so its whole tiles are
                    # fine; what it also hands back are the part-tiles where the pocket ran out, and
                    # a part-tile under `_TOE_MIN_AREA` of the design cell is not a basin worth its
                    # own perimeter of azenuri when the neighbor can simply take the ground in (see
                    # `_TOE_MIN_AREA` in banks.py for why the floor is a RATIO and not an acreage).
                    # This is the seam-pass half of the rule `_comb_toe_and_hem` applies to the
                    # carve: without it the toe pass drops a fragment, the ground returns here as
                    # bare pocket, and this pass plants the same fragment straight back.
                    _floor = _TOE_MIN_AREA * cell_area(plot_across, row_step)
                    for _q in got:
                        _qr = _ring(_q)
                        if len(_qr) >= 3 and (pointed_ring(_qr, _TOE_MIN_APEX) or pointed_ring(dedup_ring(_qr, 1.0), _TOE_MIN_APEX) or _q.area < _floor or is_chevron(_qr)):
                            scraps.append(_q)
                        else:
                            basins.append(_q)
                    scraps += offcuts
        # PLANT FIRST, WELD SECOND, and weld against the whole field including what was just
        # planted: a scrap's best neighbor is often the new basin beside it, and a scrap offered
        # only its own siblings has nowhere to go when they refuse the union.
        keep += sorted(basins, key=lambda q: (round(q.bounds[0], 1), round(q.bounds[1], 1)))
        for scrap in sorted(scraps, key=lambda q: (round(q.bounds[0], 1), round(q.bounds[1], 1))):
            # The 3 ft `paddy_plot_seams_shared` itself ignores, in px at this map's scale. MIND THE
            # UNIT: `grain` is `2 / ftpx` (the scripted tier's principled value), so px-per-foot is
            # `g / 2` and 3 ft is `1.5 * g` - NOT `3.0 * g`, which is what this said first and is
            # double. At a hamlet's ftpx 1.0 that fed 6.0 px to an opening meant to shed a tail from
            # a strip whose whole mean width was 5.6 px, so it annihilated every scrap it was handed
            # and the escape hatch silently did nothing (cohort seeds 9 and 11). Measured at the
            # corrected width the same weld comes out at a 77.1 deg apex.
            _absorb(scrap, keep, grown, 1.5 * g, g)
    for j in sorted(j for j in grown if j < carved):
        plots[j]["poly"] = _ring(keep[j])
    for basin in keep[carved:]:
        # ROUND-TRIP THE RECORDED RING here too, for the reason `_absorb` gives: a valid polygon can
        # still cross itself once `_ring` rounds it to 0.1 px, and a planted basin gets the same
        # rounding a welded one does. A basin that will not survive it is dropped and its ground
        # left to the fan floor - bare ground is an honest thing to record, a crossing ring is not.
        ring = _ring(basin)
        if len(ring) < 3 or not Polygon(ring).is_valid:
            continue
        # `filler` is read by the water-topology anchors (channel_field_anchored), which want a
        # plot the CARVE sited rather than one this pass reclaimed
        plots.append({"poly": ring, "fill": R.choice(RICE_GREENS), "filler": True})
    _unjog(plots, g, _GATE_MIN_AREA * cell_area(plot_across, row_step), water, outside)
    # A POINTED SLIVER MUST NOT WEAR THE WATER TINT - the same rule `_sector_closing_rank` applies
    # when it carves one, and for the same reason: a blue plot tapering to a needle reads as a tiny
    # triangular pond at fit zoom, not as a leveled basin. The carve's own demotion judges the quad
    # it cuts, and TWO later stages reshape it - `_comb_toe_and_hem`'s re-hem onto the drain bank,
    # and this pass's welds - so the tint is re-judged here, at the end, against every plot's final
    # ring rather than only the ones this pass touched. The replacement green is indexed by POSITION
    # rather than drawn from R - the point is the ABSENT DRAW (the stream stays put, so demoting one
    # plot cannot re-roll the rest), not variety: `RICE_GREENS` holds one color three times today.
    # Wording kept honest after a settlement-review read the old comment as promising shades.
    # so it takes no draw from R and no other plot's color moves; `low` is untouched, because it is
    # the topography and the tint is only the picture (feature 010).
    # BOTH the raw ring and the deduped one, because the two carry different apexes and the gate
    # judges the RAW one. `_sector_closing_rank` dedupes before testing for the reason its own
    # comment gives - a quad with a sub-pixel collapsed edge shows near-90 deg corners while its
    # merged triangle shows the needle - but the merge can also retire an apex the raw ring still
    # has, and `flooded_plots_read_as_basins` reads the ring as recorded (cohort seed 8). Testing
    # both at the carve's generous 25 deg keeps the placer strictly stricter than the gate's 15.
    for p in plots:
        # TWO RINGS, AND BOTH CLAUSES EARN THEIR KEEP - this is the one place a second measurement is
        # right, and the reason is that they answer to different masters. `flooded_plots_read_as_basins`
        # is the GATE for a tinted plot and it reads `dedup_ring(r, 1.0)` at 15 deg, so the first
        # clause is the placer being strictly stricter on the GATE'S OWN measurement (25 vs 15) - drop
        # it and a plot pointed at 1.0 but blunt at the end width keeps its tint and trips the gate,
        # which is exactly what cohort seed 8 did when this briefly tested the end-collapsed ring
        # alone. The second clause catches the defect the gate CANNOT see: a needle truncated a few
        # feet short of its point, which no interior angle on the 1.0 ring will ever report.
        # AND A THIRD CLAUSE, WHICH MEASURES SHAPE RATHER THAN TAPER. Both clauses above ask "does
        # this come to a point"; neither can see a blunt-cornered LOBE, and welding a scrap into
        # the fan's one blue plot is exactly how a lobe gets there. Sawada shipped a 0.731-solidity
        # flooded plot reading as an arrowhead pond with a 41.8 deg minimum apex and both ends
        # wider than 5 ft - clear of both guards (see `_TINT_MIN_SOLIDITY`). Blue has to mean "a
        # leveled basin pooling on the collector", so a blue plot that does not read as a basin
        # goes back to rice green whatever its corners measure.
        # AND A FOURTH CLAUSE, WHICH MEASURES SITING RATHER THAN SHAPE - the first blind spot the
        # three above share. Sawada, whose gen docstring and notes both define it as the hamlet with
        # NO pond, shipped a 78 x 72 ft blue basin 4 ft from the collector's tail and 15 ft from the
        # head of the off-map brook: a compact blue blob fused to the exact point where the ditch
        # becomes a stream and leaves the frame, which is where a tameike sits. Every shape predicate
        # passed it and correctly so - min apex 81.4 deg, no end under `_TINT_END_FT`, solidity 0.910.
        # It is a perfectly good basin standing in the one place a reader cannot read as a basin
        # (settlement-review 2026-08-18).
        #
        # THE OUTFALL, NOT THE WHOLE DRAIN. Blue MEANS "the closing rank pooling before the outfall",
        # so a blue plot lying ALONG the collector is the rule working; only the terminus is
        # ambiguous, and the keep-out is one and a half plot widths of it - far enough to break the
        # fusion with the stream head, near enough to leave the rest of the closing rank tinted.
        _t_end = _TINT_END_FT * g / 2
        _pg = Polygon(p["poly"]).buffer(0)
        _psol = (_pg.area / (_pg.convex_hull.area or 1.0)) if isinstance(_pg, Polygon) and not _pg.is_empty else 1.0
        _pcx = sum(_q[0] for _q in p["poly"]) / len(p["poly"])
        _pcy = sum(_q[1] for _q in p["poly"]) / len(p["poly"])
        _at_outfall = bool(dpts) and math.hypot(_pcx - dpts[-1][0], _pcy - dpts[-1][1]) < 1.5 * plot_across
        if p.get("fill") == FLOODED and (
            pointed_ring(dedup_ring(p["poly"], 1.0), _TINT_MIN_APEX) or tapers_to_a_point(p["poly"], _t_end, _TINT_MIN_APEX, 4 * _t_end) or _psol < _TINT_MIN_SOLIDITY or _at_outfall
        ):
            p["fill"] = RICE_GREENS[(int(abs(p["poly"][0][0]) * 7) + int(abs(p["poly"][0][1]) * 3)) % len(RICE_GREENS)]
