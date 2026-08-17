"""Coordinate math on points, segments and rings - no map vocabulary in here at all.

Everything above this layer is built from these: a distance, a containment, a crossing, an
intersection. Nothing here reads a manifest or knows what a paddy is.

Split from settlement/_geom.py by feature 117 - see settlement/_geom/CLAUDE.md for the index.
"""

import math

from .base import Poly, Pt


def _signed_area(poly: Poly) -> float:
    a = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return a / 2


def point_in_poly(px: float, py: float, poly: Poly) -> bool:
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi + 1e-9) + xi):
            inside = not inside
        j = i
    return inside


def seg_closest(px: float, py: float, a: Pt, b: Pt) -> Pt:
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return ax, ay
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return ax + t * dx, ay + t * dy


def seg_dist(px: float, py: float, a: Pt, b: Pt) -> float:
    cx, cy = seg_closest(px, py, a, b)
    return math.hypot(px - cx, py - cy)


def seg_in_ellipse_core(a: Pt, b: Pt, cx: float, cy: float, rx: float, ry: float, inset: float = 4.0) -> bool:
    """Does segment a-b pass through the CORE of this ellipse - the water inside its rim?

    The shared predicate of the feature-012 field pond's containment rule: `_plot_pond` (placement)
    and `field_ponds_sunk_into_one_plot` (the verdict) both call this one function, so the siter and
    the check cannot disagree - the same discipline as `paddy_wet_rings` in extents.py. The core is the
    ellipse shrunk by `inset` px (rim stroke + reed fringe): a bund may TOUCH the shore - the host
    plot's own ring does - but a bund running through open water means the pond spans plots.
    Computed in the scaled space where the core is the unit circle, so one segment-to-center
    distance answers it for any ellipse."""
    crx, cry = max(1.0, rx - inset), max(1.0, ry - inset)
    ax, ay = (float(a[0]) - cx) / crx, (float(a[1]) - cy) / cry
    bx, by = (float(b[0]) - cx) / crx, (float(b[1]) - cy) / cry
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, -(ax * dx + ay * dy) / max(1e-12, dx * dx + dy * dy)))
    return math.hypot(ax + t * dx, ay + t * dy) < 1.0


def ring_touches(cx: float, cy: float, r: float, ring: Poly) -> bool:
    """Does a disc of radius r at (cx, cy) lap this ring - inside it, or within r of an edge?"""
    return point_in_poly(cx, cy, ring) or any(seg_dist(cx, cy, ring[i], ring[(i + 1) % len(ring)]) < r for i in range(len(ring)))


#                             fits INSIDE the empty court with air on both sides: at 11pt
#                             "Governor's Mansion" measures 123px in the render font against the
#                             145px-wide mansions of Tango and Nagahara, i.e. ~11px (~33 real ft)
#                             off each wall. At 14 it measured 157px and would not fit at all.


def segments_cross(a: Pt, b: Pt, c: Pt, d: Pt) -> bool:
    def ccw(p: Pt, q: Pt, r: Pt) -> bool:
        return (r[1] - p[1]) * (q[0] - p[0]) > (q[1] - p[1]) * (r[0] - p[0])

    return ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d)


def seg_intersect(a: Pt, b: Pt, c: Pt, d: Pt) -> Pt | None:
    """The (x, y) where segments ab and cd cross, or None if parallel. Call only when they cross."""
    den = (a[0] - b[0]) * (c[1] - d[1]) - (a[1] - b[1]) * (c[0] - d[0])
    if abs(den) < 1e-9:
        return None
    t = ((a[0] - c[0]) * (c[1] - d[1]) - (a[1] - c[1]) * (c[0] - d[0])) / den
    return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))


def edge_dist(px: float, py: float, poly: Poly) -> float:
    return min(seg_dist(px, py, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))
