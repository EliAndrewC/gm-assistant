"""Geometry predicates and measures shared by every stage of every tier generator.

Split from hamletgen.py by feature 111 (bodies verbatim), moved out of hamletgen/ into the shared
sitegen/ by feature 119 when the GM ruled that tiers share a library. See sitegen/CLAUDE.md.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from l7r.diagram.settlement import Settlement, point_in_poly, seg_dist, segments_cross

from .types import SQ_FT_PER_ACRE, Poly, Pt

# ---- geometry helpers ---------------------------------------------------------------------------


def poly_area(poly: Sequence[Pt]) -> float:
    """Absolute area of a closed polygon (the shoelace formula)."""
    n = len(poly)
    return abs(sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))) / 2.0


def net_acres(net: Mapping[str, Any], ftpx: float) -> float:
    """The DRAWN paddy acreage of a comb net - the sum of the plot polygons actually carved.

    Deliberately measured from the plots and not from `build_comb`'s own `acres` (which assumes the
    village grain of 1 px = 2 ft and so over-reports 4x on a 1 ft/px hamlet) and not from the field
    envelope (which bows outside the plots and would count the bunds, the canals and the gaps as
    rice). The plots are what a farmer plants, so the plots are what gets counted."""
    return sum(poly_area(p["poly"]) for p in net["plots"]) * ftpx * ftpx / SQ_FT_PER_ACRE


def centroid(poly: Sequence[Pt]) -> Pt:
    return (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))


def unit(vx: float, vy: float) -> Pt:
    ln = math.hypot(vx, vy) or 1.0
    return (vx / ln, vy / ln)


def crop_polys(s: Settlement) -> list[Poly]:
    """Every DRY crop plot recorded so far, read back from the manifest.

    Read back rather than carried along from `build_comb`, because `draw_comb_field` DROPS hem plots
    that landed on standing water or on another fan's rice - so the net's list and the map's list
    are not the same list, and the one that matters is what was drawn."""
    return [[(float(v[0]), float(v[1])) for v in d["poly"]] for d in s.M.get("dry_plots", [])]


def pull_clear(pt: Pt, toward: Pt, obstacles: Sequence[Poly], margin: float, step: float = 12.0, tries: int = 24) -> Pt:
    """Walk a point back toward `toward` until it is `margin` clear of every obstacle.

    Used to shape the windbreak belt around the crop. Deforming the belt is the right answer rather
    than shrinking it uniformly: a fengshui grove hugs the land it is planted on and wraps whatever
    is in its way, so a belt that bends around a hem plot reads MORE like a real grove than a
    rectangle would, and it keeps its length (the gate wants a belt that embraces the cluster, and
    a uniformly-shrunk belt stops embracing before it stops overlapping)."""
    x, y = pt
    for _ in range(tries):
        if not any(point_in_poly(x, y, list(o)) or min(seg_dist(x, y, o[i], o[(i + 1) % len(o)]) for i in range(len(o))) < margin for o in obstacles):
            return (x, y)
        ux, uy = unit(toward[0] - x, toward[1] - y)
        x, y = x + ux * step, y + uy * step
    return (x, y)


def crosses_disc(a: Pt, b: Pt, center: Pt, r: float) -> bool:
    """Does the segment a->b come within `r` of `center`? (Point-to-segment distance.)"""
    return seg_dist(center[0], center[1], a, b) < r


def crosses_poly(a: Pt, b: Pt, poly: Sequence[Pt], step: float = 8.0, cap: int = 900) -> bool:
    """Does the segment a->b pass through `poly`? Sampled rather than solved, but sampled by LENGTH.

    It used to take a fixed 60 samples whatever the segment measured, which is fine for a lane and
    useless for the thing it is mostly asked about: a connector track or a drain brook runs 4,000 px
    to the frame, so 60 samples is one every 67 px and the test steps clean over a field lobe. The
    map then ships a brook drawn through the rice with the router insisting it had checked
    (`streams_avoid_fields`). One sample every 8 px is under the width of anything it is testing
    against, and the cap keeps a stray off-canvas endpoint from turning this into a million tests."""
    ring = list(poly)
    # EXACT edge intersection first, which is what `streams_avoid_fields` and its siblings use. A
    # sampled containment test cannot see a segment that clips a thin sliver of the outline - it
    # enters and leaves between two samples, and no sample is ever strictly inside - so a brook
    # routed by sampling alone was drawn across a lobe of the rice with every point it checked
    # legitimately outside the crop. Sampling stays as the second half, because it also catches the
    # case exact-crossing cannot: a segment lying wholly INSIDE the polygon, crossing no edge.
    if any(segments_cross(a, b, ring[i], ring[(i + 1) % len(ring)]) for i in range(len(ring))):
        return True
    n = min(cap, max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step)))
    return any(point_in_poly(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n, ring) for i in range(n + 1))
