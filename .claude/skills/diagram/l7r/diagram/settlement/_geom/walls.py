"""Every wall on a settlement map, what closes a ward against one, and the arches that must stand
clear of one.

The torii members are here rather than with settlement/shrines_wells/torii.py deliberately: at
THIS level an arch has exactly one geometric rule - it may not stand in a wall - and both
predicates are computed from wall_runs(). The arch glyph, the avenue count, the stride and the
threshold all live in shrines_wells/torii.py and are untouched by this module.

Split from settlement/_geom.py by feature 117 - see settlement/_geom/CLAUDE.md for the index.
"""

import math
from typing import Any

from .base import Manifest, Poly, Pt
from .overlap import _rect_ring
from .primitives import seg_dist, segments_cross

# TORII AVENUE PITCH (GM 2026-07-25, after a research pass - see settlements.md 'Torii'). Rokugan's
# sando is the 1/3/7 SET of formal gateways, NOT a Fushimi-style donation row: donation rows are a
# designated-site special case here (Shinden Togashi, the Temple of Amaterasu, the Ki Rin Shrine and
# their like), so NEITHER real-world spacing regime is the model. The research found only two: a
# donation row's arches nearly touch (~0.5-1 m in the dense tunnel, "several yards" where it loosens),
# and ranked ichi/ni/san gates stand 200 m - 1.3 km apart (off the map at every settlement scale).
# Our avenues fall between, so the spacing is a house rule rather than a copied fact: arches stand
# ~20 ft apart center-to-center, and NEVER more than two rail-spans (32 ft), past which a sando reads
# as a line of isolated gates rather than one approach. The floor is the existing one arch-span
# (torii_spread_out) so they never overlap into a blob. Village avenues sit at the top of the band
# (~30 ft) by GM preference and are deliberately left alone - the cap, not the target, is the rule.
TORII_PITCH_FT = 20.0  # the usual stride: what the engine lays when it sets an avenue's pitch
TORII_PITCH_MAX_SPANS = 2.0  # the ceiling, in torii rail-spans (32 ft for a standard 16 ft arch)


def torii_halfbox(ftpx: float, span_ft: float = 16.0) -> tuple[float, float, float]:
    """True drawn half-extents (x half-width, y-up, y-down) of a `_torii` glyph at scale `ftpx`, plus a small
    stroke pad - used to FRAME torii (crop_to_content) and to verify they sit within the frame (check_village
    mirrors this function; keep the two in sync). Follows _torii's geometry: s2 = (span_ft/ftpx)/2, rail ends at
    +/-s2, rail rise s2*7/19, post drop s2*17/19. Replaces the legacy fixed x+/-19 / y-10..+18 box - the
    pre-true-scale 38px glyph (GM 2026-07-21), which over-reserved ~5x the arch's real footprint of frame margin
    (a village torii is ~8px/16ft wide, not 38px), pushing the crop out around the end of an approach avenue."""
    s2 = (span_ft / ftpx) / 2
    pad = 2.0  # rail/post stroke half-width + a hair, so the frame never clips the vermilion
    return s2 + pad, s2 * 7.0 / 19.0 + pad, s2 * 17.0 / 19.0 + pad


# Urban building kinds a SAMURAI WARD refuses (Settlement.ward / Settlement.building): the commoner
# dwellings and commerce the fence exists to keep out (GM 2026-08-02, on Minami: laborer houses in
# the middle of the samurai neighborhood, on the samurai side of the fence). servant is deliberately
# absent - samurai households' live-in domestics lodge inside the ward, and the city gens interleave
# them on purpose. So is monk_house: a temple may legitimately stand inside the ward (Tango's
# Bishamon precinct - the warrior fortune beside the garrison quarter) and its clergy row belongs
# with its temple, held to it by the temple-neighborhood checks.
WARD_BARRED_KINDS = frozenset({"laborer", "laborer_large", "merchant", "merchant_house", "merchant_large", "burakumin", "shop", "inn"})


def ward_interior(fence: Poly, wall: Poly) -> Poly | None:
    """Close a ward FENCE polyline against the city wall ring: the ward's interior polygon.

    The fence's two ends abut the rampart (city_ward_fence_meets_wall holds that), so the fence
    plus the wall arc between its ends encloses the ward. Two arcs qualify; the ward is the
    SMALLER enclosed region - a ward is a quarter carved off the city, never the larger half
    (all three pool cities measure 21-25% of the walled area). Returns None when there is
    nothing to close (no wall ring / a degenerate fence) - callers skip rather than guess.
    check_village re-derives this independently for city_samurai_ward_residents_only: the check
    must not trust the engine's arithmetic."""
    if len(wall) < 3 or len(fence) < 2:
        return None
    # ARC-LENGTH closure, not nearest-VERTEX closure: a fence end abuts the rampart mid-EDGE, so
    # walking vertex indices from "the nearest vertex" can skip (or wrongly include) the vertex on
    # the far side of the junction, and the resulting polygon self-intersects - a bowtie, whose
    # shoelace area under-measures by cancellation and steals the smaller-area vote (caught by the
    # square-wall unit test). Projecting each end onto the ring and collecting the vertices whose
    # arc position lies strictly between the two junctions, in traversal order, yields a SIMPLE
    # polygon for both candidate closures, so the smaller-area rule is sound.
    ring = list(wall) + [wall[0]]
    arcs = [0.0]
    for i in range(len(ring) - 1):
        arcs.append(arcs[-1] + math.hypot(ring[i + 1][0] - ring[i][0], ring[i + 1][1] - ring[i][1]))
    perim = arcs[-1]
    if perim <= 0:
        return None

    def project(p: Pt) -> float:
        best: tuple[float, float] | None = None
        for i in range(len(ring) - 1):
            ax, ay = ring[i]
            bx, by = ring[i + 1]
            dx, dy = bx - ax, by - ay
            length2 = dx * dx + dy * dy
            t = 0.0 if length2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / length2))
            qx, qy = ax + t * dx, ay + t * dy
            d = (p[0] - qx) ** 2 + (p[1] - qy) ** 2
            if best is None or d < best[0]:
                best = (d, arcs[i] + t * math.sqrt(length2))
        return 0.0 if best is None else best[1]

    def area(poly: Poly) -> float:
        a = 0.0
        for i in range(len(poly)):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % len(poly)]
            a += x1 * y2 - x2 * y1
        return abs(a) / 2

    t0, t1 = project(fence[-1]), project(fence[0])
    fwd_span = (t1 - t0) % perim
    fwd = sorted(((arcs[i] - t0) % perim, wall[i]) for i in range(len(wall)))
    arc_fwd = [v for o, v in fwd if 1e-6 < o < fwd_span - 1e-6]
    back = sorted(((t0 - arcs[i]) % perim, wall[i]) for i in range(len(wall)))
    arc_back = [v for o, v in back if 1e-6 < o < (perim - fwd_span) - 1e-6]
    pa = list(fence) + arc_fwd
    pb = list(fence) + arc_back
    return pa if area(pa) <= area(pb) else pb


def wall_runs(M: Manifest) -> list[tuple[str, Poly, float]]:
    """Every WALL on a settlement map as (label, polyline, half-width px): the city rampart, each
    ward fence (plus the short wall-stroke caps where it abuts the rampart), and the perimeter of
    every walled compound - manor, governor's mansion, merchant estate, mausoleum. The half-widths
    are the DRAWN stroke half-widths (city_wall's 11 px rampart, ward's 5 px fence and 11 px cap,
    each compound's recorded wall_w), so the test is against the ink actually on the page."""
    runs: list[tuple[str, Poly, float]] = []
    ring = M.get("wall")
    if ring:
        pts: Poly = [(float(p[0]), float(p[1])) for p in ring]
        runs.append(("the city wall", pts + [pts[0]], 5.5))
    for wd in M.get("wards", []):
        runs.append((f"the {wd.get('name', 'ward')} ward fence", [(float(p[0]), float(p[1])) for p in wd["boundary"]], 2.5))
        for cap in wd.get("wall_caps", []):
            runs.append(("a ward fence wall-cap", [(float(p[0]), float(p[1])) for p in cap.get("pts", [])], 5.5))
    walled: list[tuple[str, Any]] = [(lbl, c) for lbl, key in (("a manor wall", "manors"), ("a merchant estate wall", "merchant_estates"), ("a mausoleum wall", "mausoleums")) for c in M.get(key, [])]
    if M.get("governor_mansion"):
        walled.append(("the governor's mansion wall", M["governor_mansion"]))
    for lbl, c in walled:
        if not all(k in c for k in ("x", "y", "w", "h")):
            continue  # a synthetic fixture compound recorded for some other check's sake carries no footprint to wall
        runs.append((lbl, _rect_ring(c["x"], c["y"], c["w"], c["h"], float(c.get("rot", 0) or 0)), float(c.get("wall_w", 2.0)) / 2))
    return [(lbl, p, half) for lbl, p, half in runs if len(p) >= 2]


def _box_hits_run(box: tuple[float, float, float, float], pts: Poly, half: float) -> bool:
    """Does an axis-aligned box (x0, y0, x1, y1) reach a polyline drawn `2 * half` px thick? The
    wall's stroke is a THICK line, so the box must clear its EDGE, not its centerline - and a run
    that merely ends inside the box (crossing no edge) counts too."""
    x0, y0, x1, y1 = box
    edges = (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0)))
    for i in range(len(pts) - 1):
        a, b = (pts[i][0], pts[i][1]), (pts[i + 1][0], pts[i + 1][1])
        if x0 <= a[0] <= x1 and y0 <= a[1] <= y1:
            return True
        for e0, e1 in edges:
            if segments_cross(a, b, e0, e1):
                return True
            if min(seg_dist(a[0], a[1], e0, e1), seg_dist(b[0], b[1], e0, e1), seg_dist(e0[0], e0[1], a, b), seg_dist(e1[0], e1[1], a, b)) < half:
                return True
    return False


# ---------------------------------------------------------------------------------------------
# A TORII STANDS CLEAR OF EVERY WALL (GM 2026-07-25, caught on Nagahara: the seventh arch of the
# Ebisu sando stood in the samurai ward fence). WHY: a torii is a FREESTANDING gateway - two posts
# in open ground that carry no load and close nothing, marking the threshold of sacred ground. A
# wall is its opposite: a continuous barrier whose whole purpose is that you cannot walk through
# it. So an arch drawn ON a wall run is impossible construction twice over - the posts stand inside
# the palisade, and the "gateway" opens onto a barrier. Where a way genuinely pierces a wall the
# opening is a GATE STRUCTURE (the city gate, a ward kido), never an arch. A torii over an ordinary
# street or lane stays legitimate: a sando arch spans its road, and a road is not a barrier.
#
# The rule is enforced from BOTH ends, because either feature may be drawn first (see CLAUDE.md
# "DRAW ORDER"): _torii refuses a seat standing in a wall already drawn (and shrine_hall shortens
# its avenue to fit rather than fail), while every wall-drawing method re-asks the question once
# its own run is on the page. check_village's torii_clear_of_walls is the manifest-level backstop,
# and all three read the SAME wall_runs() / torii_wall_conflicts() in this module.


def torii_seat_on_wall(M: Manifest, tx: float, ty: float, ftpx: float, runs: list[tuple[str, Poly, float]] | None = None) -> str | None:
    """The label of the wall an arch seated at (tx, ty) would stand in, or None if it stands clear.
    Asked of ONE candidate seat before it is drawn; `runs` caches wall_runs(M) across a sweep. The
    arch's extent is torii_halfbox - the same true-scale glyph box the crop and frame checks use."""
    txh, tyu, tyd = torii_halfbox(ftpx)
    for lbl, pts, half in wall_runs(M) if runs is None else runs:
        if _box_hits_run((tx - txh, ty - tyu, tx + txh, ty + tyd), pts, half):
            return lbl
    return None


def torii_wall_conflicts(M: Manifest) -> list[tuple[float, float, str]]:
    """Every recorded arch standing in a wall, as [(x, y, wall label), ...] - the whole-manifest
    form of torii_seat_on_wall, shared by the engine's post-draw guards and by check_village."""
    ftpx = float(M.get("meta", {}).get("ftpx", 1) or 1)
    runs = wall_runs(M)
    bad = []
    for t in M.get("torii") or []:
        lbl = torii_seat_on_wall(M, float(t[0]), float(t[1]), ftpx, runs)
        if lbl:
            bad.append((round(float(t[0]), 1), round(float(t[1]), 1), lbl))
    return bad
