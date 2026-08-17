"""Making a drawn line or ring look hand-made rather than drafted: fillets, Catmull-Rom smoothing,
organic jitter, a gently winding path.

Every one of these is a research-backed shape rather than a drawing quirk - a dug earth ditch
bends on a swept curve because a sharp corner scours outside and silts inside until the water has
rounded it itself.

Split from settlement/_geom.py by feature 117 - see settlement/_geom/CLAUDE.md for the index.
"""

import math
import random
from typing import Any

from .base import Poly, Pt


def fillet_polyline(pts: Poly, radius: float, steps: int = 6, min_turn_deg: float = 8.0) -> Poly:
    """Round every interior corner of a drawn watercourse, returning a densified polyline (so callers
    keep building plain `M ... L ...` paths and the taper/piece machinery is unaffected).

    WHY (GM 2026-07-25): flowing water in an EARTHEN channel has no mitred corners. A dug ditch that
    changes direction does it on a swept bend, because a sharp corner scours on the outside and silts
    on the inside until the water has rounded it itself - the maintenance crew re-digs the bend, not
    the corner. Sharp corners belong to masonry (a stone-lined aqueduct, a sluice box, a revetted
    canal), and nothing at village/town scale in this setting is lined: these are hand-dug earth
    ditches with grass banks. HOW BIG: an alluvial channel's bend radius runs ~2-3 channel widths
    (Leopold & Wolman's meander geometry), and a dug farm ditch's bend is no tighter, so callers pass
    ~2.5x the drawn width and the bend scales with the ditch instead of being a fixed drawing quirk -
    a big head-race sweeps, a thin lateral turns tight, both at the same real ratio.

    `radius` is the target cut-back along each leg, capped at 35% of either adjacent segment, so two
    neighboring corners can never eat the segment between them (0.35 + 0.35 < 1) and a short offtake
    stub keeps its shape. Corners gentler than `min_turn_deg` are left alone - there is no visible
    elbow to round, and rounding them would only add points."""
    if len(pts) < 3 or radius <= 0:
        return [(float(x), float(y)) for x, y in pts]
    out: Poly = [(float(pts[0][0]), float(pts[0][1]))]
    for i in range(1, len(pts) - 1):
        p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
        v0, v1 = (p0[0] - p1[0], p0[1] - p1[1]), (p2[0] - p1[0], p2[1] - p1[1])
        l0, l1 = math.hypot(*v0), math.hypot(*v1)
        if l0 < 1e-6 or l1 < 1e-6:
            continue  # a repeated vertex bends nothing
        cosang = max(-1.0, min(1.0, (v0[0] * v1[0] + v0[1] * v1[1]) / (l0 * l1)))
        if 180.0 - math.degrees(math.acos(cosang)) < min_turn_deg:
            out.append((float(p1[0]), float(p1[1])))
            continue
        d = min(radius, 0.35 * l0, 0.35 * l1)
        a = (p1[0] + v0[0] / l0 * d, p1[1] + v0[1] / l0 * d)
        b = (p1[0] + v1[0] / l1 * d, p1[1] + v1[1] / l1 * d)
        for s in range(steps + 1):  # quadratic bend, the corner itself as the control point
            t = s / steps
            mt = 1 - t
            out.append((mt * mt * a[0] + 2 * mt * t * p1[0] + t * t * b[0], mt * mt * a[1] + 2 * mt * t * p1[1] + t * t * b[1]))
    out.append((float(pts[-1][0]), float(pts[-1][1])))
    return out


def smooth_closed(pts: Poly) -> str:
    n = len(pts)
    d = f'M{pts[0][0]:.1f},{pts[0][1]:.1f}'
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f' C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}'
    return d + 'Z'


def smooth_points(pts: Poly, steps: int = 10) -> Poly:
    """Sample the rendered (Catmull-Rom) boundary so the manifest matches what's
    drawn - the curve bows inward of the raw vertices (a hard-won lesson)."""
    n = len(pts)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        for s in range(steps):
            t = s / steps
            mt = 1 - t
            x = mt**3 * p1[0] + 3 * mt**2 * t * c1[0] + 3 * mt * t**2 * c2[0] + t**3 * p2[0]
            y = mt**3 * p1[1] + 3 * mt**2 * t * c1[1] + 3 * mt * t**2 * c2[1] + t**3 * p2[1]
            out.append((round(x, 1), round(y, 1)))
    return out


def organic_bbox(bbox: Any, amp: float, flat_edges: tuple[int, ...] = ()) -> Poly:
    """Semi-rectangular core with lobes (outgrowths) and bays (indentations).
    Edges listed in flat_edges (0=N, 1=E, 2=S, 3=W) are kept straight - e.g. a field
    that must run flush against a town wall flattens the abutting edge."""
    x0, y0, x1, y1 = bbox
    edges = [((x0, y0), (x1, y0), (0, -1)), ((x1, y0), (x1, y1), (1, 0)), ((x1, y1), (x0, y1), (0, 1)), ((x0, y1), (x0, y0), (-1, 0))]
    pts = []
    for ei, (sa, sb, (nx, ny)) in enumerate(edges):
        for i in range(4):
            t = i / 4
            bx, by = sa[0] + (sb[0] - sa[0]) * t, sa[1] + (sb[1] - sa[1]) * t
            off = random.uniform(-amp * 0.5, amp)
            jt = random.uniform(-amp * 0.18, amp * 0.18)  # consume RNG even when flat, to keep placement aligned
            if ei in flat_edges:
                pts.append((bx, by))
                continue
            if i == 0:
                off *= 0.35
            pts.append((bx + nx * off + jt, by + ny * off + jt))
    return pts


def organic_poly(base: Poly, amp: float) -> Poly:
    """Organic-ize an arbitrary base polygon (handles concave shapes like a V):
    densify each edge and jitter the samples; smoothing rounds it."""
    pts = []
    n = len(base)
    for i in range(n):
        ax, ay = base[i]
        bx, by = base[(i + 1) % n]
        segs = max(1, int(math.hypot(bx - ax, by - ay) / 150))
        for s in range(segs):
            t = s / segs
            pts.append((ax + (bx - ax) * t + random.uniform(-amp, amp) * 0.5, ay + (by - ay) * t + random.uniform(-amp, amp) * 0.5))
    return pts


def winding(start: Pt, end: Pt, amp: float = 15, n: int = 2) -> Poly:
    """A gently winding path from start to end (a shallow S, not a straight line)."""
    sx, sy = start
    ex, ey = end
    dx, dy = ex - sx, ey - sy
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    pts = [(float(sx), float(sy))]
    for k in range(1, n + 1):
        t = k / (n + 1)
        off = amp * (1 if k % 2 else -1)
        pts.append((round(sx + dx * t + nx * off, 1), round(sy + dy * t + ny * off, 1)))
    pts.append((float(ex), float(ey)))
    return pts
