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
until it lapped its neighbours only shallowly. Three consequences, all of them the defect above:

- the box was sized from where the SAMPLES were, not from where the pocket's walls are, so a
  fitted tile stopped a few px short of the surrounding bunds on every side - a rectangle with its
  own four walls and a ribbon of bare floor around it;
- the shrink was uniform, so a tile lapping one neighbour retreated from all four;
- the acceptance test allowed every probe to sit up to 12 real ft INSIDE a neighbour as long as
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
- a pocket too thin to hold a basin is ABSORBED into the neighbour it shares the most bund with.
  That is what welds a doubled bund into a single one: the strip stops being ground between two
  walls and becomes part of the basin on one side of it.

So the pass has one postcondition - every square foot inside the command area is planted, is
water, or is outside the fan - and `paddy_plot_seams_shared` is the gate that holds it.

IT RUNS LAST, after `_comb_toe_and_hem`. That order is load-bearing: the toe pass DROPS slivers
too acute to bund and re-hems every bund onto the drain bank, so anything that ran before it would
have its work reopened as fresh bare ground. Running afterwards means this pass reconciles what
the whole pipeline actually left, whichever stage left it.
"""

import random
from collections.abc import Callable
from typing import Any

from shapely.errors import GEOSException
from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from .banks import dedup_ring, pointed_ring, polyline_cum
from .frame import BANK_MARGIN, Poly, _f_at_u, _Frame
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
            return (w0 + (w1 - w0) * cum[k] / tot) / 2 + BANK_MARGIN * g

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
    # where the drain widens to DRAIN_W_TAIL and `paddy_bunds_clear_the_collector` measures a
    # slope-leaned set-back that a flat margin does not cover. Same predicate as the placer, so
    # ground this pass plants is ground the carve would have been allowed to plant.
    below = _band(F, us, [drain_f(u) - bank(u) for u in us], fhi + span)
    above = _band(F, us, [canal_f(u) for u in us], flo - span)
    return unary_union([below, above])


def _absorb(pocket: Polygon, into: list[Polygon], grown: set[int]) -> None:
    """Fold a too-thin pocket into the basin it shares the most bund with - the weld that turns two
    walls with a strip between them into the one wall a real aze is. The neighbour is chosen by
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
        # shipped a 10-vertex bow-tie basin whose outline crossed its neighbour's twice and read as
        # a doubled bund at the fan toe. Simplification here is only tidying, so a result that is
        # not a clean simple polygon is discarded in favour of the union it came from.
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
        into[j] = candidate
        grown.add(j)
        return


def _plant(F: _Frame, pocket: Polygon, plot_across: float, row_step: tuple[float, float], half: float) -> tuple[list[Polygon], list[Polygon]]:
    """Subdivide a plantable pocket at the FAN'S OWN GRAIN and hand back the basins.

    One giant slab would dwarf the ~0.08-acre plots around it (the relative-size doctrine), so the
    pocket's (u, f) box is cut into ~plot_across x row_step cells and the pocket clipped to each.
    Cells are cut from ONE box, so neighbouring pieces share their seam exactly; the pocket's own
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
    nu = max(1, round((uhi - ulo) / plot_across))
    nf = max(1, round((fhi - flo) / ((row_step[0] + row_step[1]) / 2)))
    cells: list[Polygon] = []
    for iu in range(nu):
        ua, ub = ulo + (uhi - ulo) * iu / nu, ulo + (uhi - ulo) * (iu + 1) / nu
        for jf in range(nf):
            fa, fb = flo + (fhi - flo) * jf / nf, flo + (fhi - flo) * (jf + 1) / nf
            cell = Polygon([F.to_xy(ua, fa), F.to_xy(ub, fa), F.to_xy(ub, fb), F.to_xy(ua, fb)])
            cells += _parts(_despike(pocket.intersection(cell)))
    good = [c for c in cells if not c.buffer(-half).is_empty]
    if not good:
        return [pocket], []  # the grid cut the one thick part up; the pocket is a basin as it stands
    return good, [c for c in cells if c.buffer(-half).is_empty]


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
    place: absorbed neighbours get a new `poly`, planted pockets are appended."""
    if not plots or len(envelope) < 3:
        return
    half = MIN_PLOT_SIDE * g / 2
    keep = [Polygon(p["poly"]).buffer(0) for p in plots]
    field = Polygon(envelope).buffer(0)
    outside = _outside_command(F, a_pts, dpts, field, g, bank)
    water = _water(channels, g)
    carved = len(keep)
    grown: set[int] = set()
    # TWICE ROUND. Welding a scrap into a basin changes which basin borders the NEXT scrap, and
    # planting a pocket gives its neighbours a new edge to weld against - so a second look at the
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
                    basins += got
                    scraps += offcuts
        # PLANT FIRST, WELD SECOND, and weld against the whole field including what was just
        # planted: a scrap's best neighbour is often the new basin beside it, and a scrap offered
        # only its own siblings has nowhere to go when they refuse the union.
        keep += sorted(basins, key=lambda q: (round(q.bounds[0], 1), round(q.bounds[1], 1)))
        for scrap in sorted(scraps, key=lambda q: (round(q.bounds[0], 1), round(q.bounds[1], 1))):
            _absorb(scrap, keep, grown)
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
    # A POINTED SLIVER MUST NOT WEAR THE WATER TINT - the same rule `_sector_closing_rank` applies
    # when it carves one, and for the same reason: a blue plot tapering to a needle reads as a tiny
    # triangular pond at fit zoom, not as a leveled basin. The carve's own demotion judges the quad
    # it cuts, and TWO later stages reshape it - `_comb_toe_and_hem`'s re-hem onto the drain bank,
    # and this pass's welds - so the tint is re-judged here, at the end, against every plot's final
    # ring rather than only the ones this pass touched. The replacement green is picked by POSITION
    # so it takes no draw from R and no other plot's colour moves; `low` is untouched, because it is
    # the topography and the tint is only the picture (feature 010).
    # BOTH the raw ring and the deduped one, because the two carry different apexes and the gate
    # judges the RAW one. `_sector_closing_rank` dedupes before testing for the reason its own
    # comment gives - a quad with a sub-pixel collapsed edge shows near-90 deg corners while its
    # merged triangle shows the needle - but the merge can also retire an apex the raw ring still
    # has, and `flooded_plots_read_as_basins` reads the ring as recorded (cohort seed 8). Testing
    # both at the carve's generous 25 deg keeps the placer strictly stricter than the gate's 15.
    for p in plots:
        if p.get("fill") == FLOODED and (pointed_ring(p["poly"]) or pointed_ring(dedup_ring(p["poly"], 1.0))):
            p["fill"] = RICE_GREENS[(int(abs(p["poly"][0][0]) * 7) + int(abs(p["poly"][0][1]) * 3)) % len(RICE_GREENS)]
