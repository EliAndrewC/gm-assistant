"""A footprint's corner ring, and whether two regions meet or how far apart they are.

The distinction this module exists to keep straight is the one the skill's CLAUDE.md calls
'CENTER vs FOOTPRINT': a gap VERDICT reads real rotated corners (sat_overlap, poly_gap,
edge-to-edge), a PREFILTER may read a circumscribed extent, and the two must never be swapped.

Split from settlement/_geom.py by feature 117 - see settlement/_geom/CLAUDE.md for the index.
"""

import math
from collections.abc import Sequence
from typing import Any

from .base import Poly, Pt
from .primitives import point_in_poly, seg_dist, segments_cross


def stroke_quads(pts: Sequence[Any], hw: float) -> list[Poly]:
    """One quad per segment of a polyline at half-width `hw` - a linear feature as real polygons, so
    a caller can SAT-test against it instead of measuring to sample points (a corner-distance test
    misses a line passing through the MIDDLE of a box, which is exactly the ward-fence-through-the-
    guard-box case it was hiding)."""
    quads: list[Poly] = []
    for i in range(len(pts) - 1):
        ax, ay = float(pts[i][0]), float(pts[i][1])
        bx, by = float(pts[i + 1][0]), float(pts[i + 1][1])
        ln = math.hypot(bx - ax, by - ay) or 1.0
        nx, ny = -(by - ay) / ln * hw, (bx - ax) / ln * hw
        quads.append([(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)])
    return quads


def box_gap(a: Sequence[float], b: Sequence[float]) -> float:
    """Clear separation between two axis-aligned boxes (x0, y0, x1, y1) - 0 when they touch or
    overlap. The single measure behind the label standoff ladder in labels.py AND behind the gate's
    `label_hugs_its_referent`, so placer and checker agree by construction."""
    dx = max(0.0, b[0] - a[2], a[0] - b[2])
    dy = max(0.0, b[1] - a[3], a[1] - b[3])
    return math.hypot(dx, dy)


def _rect_ring(x: float, y: float, w: float, h: float, rot: float = 0.0) -> Poly:
    """The closed corner ring of a (possibly rotated) w x h rect centered at (x, y)."""
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    pts: Poly = [(x + dx * c - dy * s, y + dx * s + dy * c) for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
    return pts + [pts[0]]


def drawn_extent(w: float, h: float, rot: float = 0.0) -> tuple[float, float]:
    """The axis-aligned extent a `w` x `h` rect actually OCCUPIES once drawn at `rot` degrees.

    This is the honest replacement for the circumscribed circle in a collision test (feature 121).
    The circle is rotation-invariant, which is why it was safe, but it reserves the half-DIAGONAL in
    every direction: a 46 x 28 house gets r = 26.9 against a true half-width of 23, so two of them
    are forced 57.8 px apart where true touching is 46. This returns 46 x 28 at rot 0, and swaps to
    28 x 46 at 90 deg, so a box test on it is EXACT for an axis-aligned pair and a tight bound for a
    raked one - and it can never permit a real overlap, because a rotated rect always fits inside
    its own axis-aligned extent.

    NOT A PREFILTER. The `_reach_index` boxes keep the half-diagonal deliberately: an index may
    over-state an extent (it only admits pairs the exact test then rejects) but must never
    under-state one, or it starts deciding instead of pruning. See `_fits`."""
    a = math.radians(rot)
    ca, sa = abs(math.cos(a)), abs(math.sin(a))
    return (w * ca + h * sa, w * sa + h * ca)


def sat_overlap(p: Sequence[Sequence[float]], q: Sequence[Sequence[float]]) -> bool:
    """Do two CONVEX polygons overlap? (separating-axis test; touching edges do not count.)"""
    for poly in (p, q):
        for i in range(len(poly)):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % len(poly)]
            nx, ny = -(y2 - y1), (x2 - x1)
            pa = [nx * x + ny * y for x, y in p]
            qa = [nx * x + ny * y for x, y in q]
            if max(pa) < min(qa) or max(qa) < min(pa):
                return False
    return True


def _union_area(rects: Any) -> float:
    """Total area covered by a set of axis-aligned rects (x0, y0, x1, y1), counting overlap ONCE. The grove's
    belt arms abut at the windward corner, so summing their areas double-counts it; the honest grove footprint
    is the union. Few small rects, so a coordinate-compression sweep is ample."""
    rects = [r for r in rects if r[2] > r[0] and r[3] > r[1]]
    if not rects:
        return 0.0
    xs = sorted({r[0] for r in rects} | {r[2] for r in rects})
    area = 0.0
    for i in range(len(xs) - 1):
        x0, x1 = xs[i], xs[i + 1]
        spans = sorted((r[1], r[3]) for r in rects if r[0] <= x0 and r[2] >= x1)
        cy = -1e18
        covered = 0.0
        for y0, y1 in spans:
            if y1 <= cy:
                continue
            covered += y1 - max(y0, cy)
            cy = y1
        area += (x1 - x0) * covered
    return area


def region_blocked(quad: Poly, circles: Sequence[tuple[float, float, float]], halo: Sequence[tuple[float, float, float]], lines: Sequence[tuple[Any, float]], polys: Sequence[Poly]) -> bool:
    """Does a cell REGION meet any keep-out? Circles by distance-to-region, stroked lines by
    segment-to-region, polygons by containment-or-crossing.

    Factored out of near_ring_cropland so it can be tested directly: the bug it exists to stop is a
    keep-out that sits against the middle of a cell EDGE, touching neither the cell's center nor any
    of its corners, which is how a wellhead ended up 1 px inside a hatake plot with every sample
    point clear."""
    if any(point_quad_dist(cx, cy, quad) < r for cx, cy, r in circles):
        return True
    if any(point_quad_dist(cx, cy, quad) < r for cx, cy, r in halo):
        return True
    if any(quad_hits_seg(quad, pl[i], pl[i + 1], hw) for pl, hw in lines for i in range(len(pl) - 1)):
        return True
    return any(quad_hits_poly(quad, gp) for gp in polys)


def quad_hits_poly(quad: Poly, poly: Poly) -> bool:
    """Does a convex cell REGION meet an arbitrary polygon? Containment either way, plus edge
    crossings - so a polygon threading between the cell's sample points is still caught."""
    if any(point_in_poly(qx, qy, poly) for qx, qy in quad):
        return True
    if any(point_in_poly(px, py, quad) for px, py in poly):
        return True
    for i in range(len(quad)):
        a, b = quad[i], quad[(i + 1) % len(quad)]
        for j in range(len(poly)):
            c, d = poly[j], poly[(j + 1) % len(poly)]
            if segments_cross(a, b, c, d):
                return True
    return False


def point_quad_dist(px: float, py: float, quad: Poly) -> float:
    """Distance from a point to a convex cell region; 0 inside it."""
    if point_in_poly(px, py, quad):
        return 0.0
    return min(seg_dist(px, py, quad[i], quad[(i + 1) % len(quad)]) for i in range(len(quad)))


def quad_hits_seg(quad: Poly, a: Pt, b: Pt, hw: float) -> bool:
    """Does a stroked line (segment + half-width) meet a cell region? Tests the SEGMENT against the
    cell's edges, not just its corners - a ditch crossing the middle of a cell touches no corner."""
    if point_quad_dist(a[0], a[1], quad) < hw or point_quad_dist(b[0], b[1], quad) < hw:
        return True
    for i in range(len(quad)):
        c, d = quad[i], quad[(i + 1) % len(quad)]
        if segments_cross(a, b, c, d):
            return True
        if seg_dist(c[0], c[1], a, b) < hw or seg_dist(d[0], d[1], a, b) < hw:
            return True
    return False


def rot_rect(cx: float, cy: float, w: float, h: float, deg: float = 0.0) -> Poly:
    """The four corners of a (possibly rotated) footprint - the shape most placement tests want."""
    th = math.radians(deg or 0.0)
    c, sn = math.cos(th), math.sin(th)
    return [(cx + dx * c - dy * sn, cy + dx * sn + dy * c) for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]


def poly_gap(p: Poly, q: Poly) -> float:
    """The true gap in px between two convex quads - 0.0 if they overlap or touch.

    For two non-intersecting convex polygons the closest approach always involves a vertex of one
    and an edge of the other, so the four vertex-to-edge minima are exact, not an approximation."""
    if rects_overlap(p, q):
        return 0.0
    best = 1e18
    for a, b in ((p, q), (q, p)):
        for vx, vy in a:
            for i in range(len(b)):
                best = min(best, seg_dist(vx, vy, b[i], b[(i + 1) % len(b)]))
    return best


def _aabb_gap(p: Poly, q: Poly) -> float:
    """The gap between two quads' AXIS-ALIGNED bounds - 0 where the bounds meet or overlap.

    Deliberately the coarse measure, because it is the one `city_government_offices_dont_abut`
    uses: that check reads AABBs, so a placement probe that guards the same standoff has to read
    AABBs too or the two disagree exactly where a feature is drawn at an angle."""
    ax0, ay0, ax1, ay1 = min(x for x, _ in p), min(y for _, y in p), max(x for x, _ in p), max(y for _, y in p)
    bx0, by0, bx1, by1 = min(x for x, _ in q), min(y for _, y in q), max(x for x, _ in q), max(y for _, y in q)
    return math.hypot(max(0.0, ax0 - bx1, bx0 - ax1), max(0.0, ay0 - by1, by0 - ay1))


def rects_overlap(p: Poly, q: Poly) -> bool:
    """Separating-axis overlap for two convex quads (corner lists)."""
    for poly in (p, q):
        for i in range(len(poly)):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % len(poly)]
            nx, ny = -(y2 - y1), (x2 - x1)
            pa = [nx * x + ny * y for x, y in p]
            qa = [nx * x + ny * y for x, y in q]
            if max(pa) < min(qa) or max(qa) < min(pa):
                return False
    return True
