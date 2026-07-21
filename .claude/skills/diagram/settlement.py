#!/usr/bin/env python3
"""Settlement-map library for the diagram skill (Mode B).

The TRULY COMMON machinery for drawing Rokugani village/hamlet plans lives here:
the palette, organic fields with irregular crop basins, south-facing house glyphs,
hills + shrines + torii, ponds/streams/channels, size-aware house placement, and
the JSON manifest that check_village.py validates.

A specific settlement (see kikuta.gen.py, hikari-no-sato.gen.py) is a thin
script: it instantiates Settlement, declares its fields/water/shrine/houses, and
calls finish(). What varies village to village - number and shape of fields, the
irrigation source (pond vs stream vs field-to-field), torii count, whether a hill
carries the shrine, whether blight left abandoned houses - is passed in, not baked
here. Those declarations are echoed into manifest["meta"] so the validator can
adapt its checks per village instead of assuming one village's specifics.
"""

import hashlib
import json
import math
import os
import random
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterator, Mapping, Sequence
from typing import Any, cast

Pt = tuple[float, float]  # an (x, y) point in map pixels
Poly = list[Pt]  # a polyline / polygon as a list of points
Manifest = dict[str, Any]  # the JSON settlement manifest the generator emits


def _assert_not_main_tree(path: str | None = None) -> None:
    """Refuse to run from the MAIN /gm-assistant checkout. Main is the integration point,
    never a workspace (CLAUDE.md "Session clones"): a generator/gate/test writing into main's
    tree races with another session's mid-ritual push-to-checkout (the 2026-07-20 double-push
    post-mortem). Import-time enforcement here covers every Mode B gen, check_village.py, and
    the pytest suites, since they all import this module. The GM can deliberately override
    with GM_ASSISTANT_ALLOW_MAIN=1; a session must not."""
    p = os.path.realpath(path if path is not None else __file__)
    if p.startswith("/gm-assistant/") and "/.clones/" not in p and os.environ.get("GM_ASSISTANT_ALLOW_MAIN") != "1":
        raise SystemExit(
            "ERROR: this ran from the MAIN /gm-assistant tree. Main is the integration point, never a workspace -\n"
            "every generator, gate, and test runs inside the session's own clone under /gm-assistant/.clones/.\n"
            "Check CLAUDE.md, section 'Session clones' (reload CLAUDE.md if it has fallen out of your context\n"
            "window) for the procedure: create or reuse .clones/<kebab-cased-session-name>, sync it in with\n"
            "'git pull origin main', and run this same command from inside that clone.\n"
            "(GM override for a deliberate main-tree run: GM_ASSISTANT_ALLOW_MAIN=1)"
        )


_assert_not_main_tree()

LAND = '#EFE3C2'
PADDY_SHADES = ['#A7C49C', '#9FBE93', '#AECBA1', '#9BBA8F', '#B4CCA6']  # rice mid-growth (green)
FLOODED_SHADES = ['#93B0A2', '#8AAB9A', '#9DBAAB', '#88A99A', '#9AB6A8']  # just-transplanted paddy (water+shoots, blue-green)
RIPE_SHADES = ['#CBBB74', '#C4B36A', '#D1C180']  # ripening rice (golden) - a few plots
RICE_GREENS = ['#A6C398', '#A2C094', '#A9C69C']  # rice at ONE stage - near-identical greens (reads uniform)


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


def segments_cross(a: Pt, b: Pt, c: Pt, d: Pt) -> bool:
    def ccw(p: Pt, q: Pt, r: Pt) -> bool:
        return (r[1] - p[1]) * (q[0] - p[0]) > (q[1] - p[1]) * (r[0] - p[0])

    return ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d)


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


def seg_intersect(a: Pt, b: Pt, c: Pt, d: Pt) -> Pt | None:
    """The (x, y) where segments ab and cd cross, or None if parallel. Call only when they cross."""
    den = (a[0] - b[0]) * (c[1] - d[1]) - (a[1] - b[1]) * (c[0] - d[0])
    if abs(den) < 1e-9:
        return None
    t = ((a[0] - c[0]) * (c[1] - d[1]) - (a[1] - c[1]) * (c[0] - d[0])) / den
    return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))


def edge_dist(px: float, py: float, poly: Poly) -> float:
    return min(seg_dist(px, py, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


# A village runs ~200-500 inhabitants, averaging ~350 (budgets.md). The spread is deliberately NOT a bell
# curve - the tails are only modestly rarer than the mode - so a generated village varies widely in size while
# still clustering on 350. Households = population / 5 (the "dwellings x5" rule). Weights sum to 100.
_VILLAGE_POP_DIST = ((200, 10), (250, 10), (300, 15), (350, 30), (400, 15), (450, 10), (500, 10))


def village_population(rng: random.Random) -> int:
    """Draw a village population (200-500, mode 350) from the weighted distribution, using the passed
    random.Random so the draw is DETERMINISTIC from the map seed. Returns the integer population."""
    return rng.choices([p for p, _ in _VILLAGE_POP_DIST], weights=[w for _, w in _VILLAGE_POP_DIST])[0]


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


# ---- Knob engine (feature 005): historically-typed, seed-rolled layout variation ---------------
# A "knob" is one named degree of village-layout variation - where the cluster sits, the lane
# skeleton, the water-source position, the plot texture, the focal-feature set. A village spec MAY
# pin any knob; every unpinned knob is resolved by an INDEPENDENT deterministic roll off the map
# seed, filtered by the knob's historical-typing rule so a value invalid for the stated geography (or
# conflicting with an already-resolved knob) is never drawn. Resolution order per knob (data-model.md):
# pinned -> rolled -> default. This is the shared MACHINERY; the actual Family-A knob catalog is
# registered in the US1 pass. Grounding for WHY independent-per-knob (not preset bundles): research.md
# D3 - independent knobs give the widest variety and make "pin one, roll the rest" natural, while the
# per-knob typing rules (not a bundle) keep combinations historically coherent.

TypingRule = Callable[[Any, Mapping[str, Any]], bool]


def _always_typed(value: Any, context: Mapping[str, Any]) -> bool:
    """Default typing rule: every value is allowed (a knob with no geographic constraint)."""
    return True


def knob_rng(seed: int, knob_name: str) -> random.Random:
    """A per-knob INDEPENDENT, deterministic RNG. Derives a stable sub-seed from (map seed, knob
    name) with SHA-256 - Python's built-in hash() is salted per process (PYTHONHASHSEED), so it
    cannot give cross-run determinism - so each knob draws independently of the others and a given
    (seed, knob) pair always yields the same draw. Returns its OWN Random instance and never disturbs
    the global random state the generators seed positionally."""
    digest = hashlib.sha256(f"{seed}\x00{knob_name}".encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


class Knob:
    """One named degree of village-layout variation: a discrete value_space, a default, and a
    typing_rule(value, context) predicate that excludes values historically invalid for the stated
    geography / already-resolved knobs. `roll` draws deterministically and independently from the
    typing-filtered space."""

    def __init__(self, name: str, value_space: Sequence[Any], default: Any, typing_rule: TypingRule | None = None) -> None:
        self.name = name
        self.value_space: list[Any] = list(value_space)
        self.default = default
        self.typing_rule: TypingRule = typing_rule if typing_rule is not None else _always_typed

    def allowed(self, context: Mapping[str, Any]) -> list[Any]:
        """value_space filtered to the values whose typing_rule holds in this context."""
        return [v for v in self.value_space if self.typing_rule(v, context)]

    def roll(self, seed: int, context: Mapping[str, Any]) -> Any:
        """A deterministic, independent draw from the typing-filtered value space. An empty filtered
        space is a spec error (loud), never a silent fallback (contract C2)."""
        pool = self.allowed(context)
        if not pool:
            raise ValueError(f"knob {self.name!r}: no value in {self.value_space} satisfies its typing rule for context {dict(context)!r}")
        return pool[knob_rng(seed, self.name).randrange(len(pool))]


KNOBS: dict[str, Knob] = {}


def register_knob(knob: Knob) -> Knob:
    """Register a knob in the global catalog (last registration per name wins). Returns the knob so
    a module can write `X = register_knob(Knob(...))`."""
    KNOBS[knob.name] = knob
    return knob


def resolve_knob(name: str, seed: int, context: Mapping[str, Any], pinned: Mapping[str, Any], *, do_roll: bool = True) -> Any:
    """Resolve one registered knob. Order (data-model.md): pinned -> rolled -> default. A pinned value
    that is not in the value_space, or that violates the typing_rule, is a loud error - never silently
    drawn (contract C3). With do_roll=False an unpinned knob falls straight to its default (a map that
    opts out of rolling this knob)."""
    knob = KNOBS[name]
    if pinned.get(name) is not None:
        val = pinned[name]
        if val not in knob.value_space:
            raise ValueError(f"knob {name!r}: pinned value {val!r} is not in its value space {knob.value_space}")
        if not knob.typing_rule(val, context):
            raise ValueError(f"knob {name!r}: pinned value {val!r} violates its typing rule for context {dict(context)!r}")
        return val
    if do_roll:
        return knob.roll(seed, context)
    return knob.default


# ---- Family-A knob catalog (feature 005, US1): the within-archetype layout knobs --------------
# Registered at import so a spec can pin or roll them. Value spaces + typing rules follow data-model.md
# D2 / research.md D2 (China-first). Each typing rule reads the village's stated geography from the
# resolution `context` (water_kind, field_origin, scale, ...) and excludes values that would be
# historically incoherent there, so an INDEPENDENT per-knob roll still lands on a coherent village.


def _lane_skeleton_ok(v: Any, ctx: Mapping[str, Any]) -> bool:
    """A 'waterside' lane skeleton needs water running ALONG the cluster (a stream/canal beside it), not
    merely a valley-head pond uphill - so it is allowed only for a stream-fed village or one that
    explicitly declares a waterside/canal site."""
    if v == "waterside":
        return ctx.get("water_kind") == "stream" or bool(ctx.get("waterside_site"))
    return True


def _water_source_ok(v: Any, ctx: Mapping[str, Any]) -> bool:
    """Stream 'edge_*' entry points need a stream source; the pond positions (corner/mid_margin/chain)
    need a pond. Gravity feed (source uphill of the field intake) is a PLACEMENT concern enforced when
    the source is drawn, not a value exclusion here."""
    if v.startswith("edge_"):
        return ctx.get("water_kind") == "stream"
    return ctx.get("water_kind") != "stream"


def _cluster_shape_ok(v: Any, ctx: Mapping[str, Any]) -> bool:
    """A 'split' cluster needs room for two hamlets to read separately - a village/town, not a hamlet."""
    return v != "split" or ctx.get("scale") in ("village", "town")


def _plot_regularity_ok(v: Any, ctx: Mapping[str, Any]) -> bool:
    """A rectilinear 'grid' bund pattern implies a planned/surveyed field (a reclamation or allotment
    context), not an organically-grown old one - so it is excluded unless the field origin is planned."""
    return v != "grid" or ctx.get("field_origin") == "planned"


def _field_archetype_ok(v: Any, ctx: Mapping[str, Any]) -> bool:
    """The FIELD terrain archetype must match the village's stated terrain (research.md D4, China-first):
    contour_terraces need HILL/upland ground; polder_grid needs LOW reclaimed/coastal-delta ground; a
    ribbon_valley needs a narrow valley floor; a mulberry_dike_fishpond is the Pearl-delta low-wet system.
    valley_paddy (the comb default) fits any ordinary valley-bottom terrain. Terrain is read from
    `ctx['terrain']` when the spec declares it; absent a declaration, only valley_paddy is coherent."""
    terrain = ctx.get("terrain")
    need = {"valley_paddy": None, "contour_terraces": "hill", "polder_grid": "low", "ribbon_valley": "narrow_valley", "mulberry_dike_fishpond": "low"}
    req = need.get(v)
    return req is None or terrain == req


def _centroid(poly: Sequence[Pt]) -> list[float]:
    """Rounded centroid of a plot polygon - the identity a land-use record and a wet-plot record share."""
    return [round(sum(p[0] for p in poly) / len(poly), 1), round(sum(p[1] for p in poly) / len(poly), 1)]


def _land_use_ok(v: Any, ctx: Mapping[str, Any]) -> bool:
    """A LAND-USE overlay must suit the setting: mulberry_fishpond + lotus are wet/valley uses fine on ordinary
    paddy land; a tea_fringe needs some hill/terrace margin (`ctx['terrain']` hill, or a terrace archetype) to
    sit on. 'none' (plain rice) is always valid.

    WHY EVERY VALUE HERE IS A *PERMANENT* USE, never a rotation (GM, 2026-07): an overlay recolors SOME plots
    while the rest stay standing rice, so it may only hold crops that genuinely coexist with rice in the same
    season. A dike-pond, a lotus paddy and a hill tea garden are permanent installations - the plot is given
    over to them all year, so the plot next door can be rice. RAPE (油菜) was tried here and REMOVED: rice and
    rape are the two halves of one ROTATION in the SAME plot (rice transplanted May-June and harvested
    Sep-Oct; rape sown into the drained stubble Oct-Nov, flowering Mar-Apr, off by May), so they are never
    both standing. Mixing them at ANY fraction depicts two seasons at once. What varies between households is
    only whether a plot is double-cropped at all, and that shows up in the SPRING picture as yellow rape
    against BARE stubble / standing water - never against green rice. Rape therefore belongs on a future
    seasonal axis (a whole-field state), not on this per-plot land-use axis. Do not re-add it here."""
    if v in ("none", "mulberry_fishpond", "lotus"):
        return True
    return ctx.get("terrain") == "hill" or ctx.get("field_archetype") == "contour_terraces"  # tea_fringe


def _settlement_form_ok(v: Any, ctx: Mapping[str, Any]) -> bool:
    """The SETTLEMENT FORM must suit the site: nucleated/linear/dispersed fit anywhere, but a WATER-TOWN (houses
    fronting a canal) needs a canal - and per GM setting canon artificial transport canals are a LION-lands
    feature, not the Empire-wide default (see the diagram SKILL.md China-first note), so water_town is excluded
    unless the map declares Lion lands or a canal (`ctx['clan']=='Lion'` or `ctx['canal']`)."""
    if v in ("nucleated", "linear", "dispersed"):
        return True
    return ctx.get("clan") == "Lion" or bool(ctx.get("canal"))  # water_town


register_knob(Knob("settlement_form", ["nucleated", "linear", "dispersed", "water_town"], default="nucleated", typing_rule=_settlement_form_ok))
register_knob(Knob("field_archetype", ["valley_paddy", "contour_terraces", "polder_grid", "ribbon_valley", "mulberry_dike_fishpond"], default="valley_paddy", typing_rule=_field_archetype_ok))
register_knob(Knob("land_use_overlay", ["none", "mulberry_fishpond", "lotus", "tea_fringe"], default="none", typing_rule=_land_use_ok))
register_knob(Knob("cluster_position", ["high_margin", "flank", "mid_margin", "valley_mouth", "valley_head", "on_rise"], default="high_margin"))
register_knob(Knob("cluster_shape", ["round", "elongated", "crescent", "split"], default="round", typing_rule=_cluster_shape_ok))
register_knob(Knob("lane_skeleton", ["spine", "T", "Y", "cross", "waterside"], default="spine", typing_rule=_lane_skeleton_ok))
register_knob(
    Knob(
        "water_source_position",
        ["corner_NW", "corner_NE", "corner_SW", "corner_SE", "mid_margin", "chain", "edge_N", "edge_E", "edge_S", "edge_W"],
        default="corner_NW",
        typing_rule=_water_source_ok,
    )
)
register_knob(Knob("plot_size", ["small_irregular", "medium", "large_block", "strip"], default="medium"))
register_knob(Knob("plot_regularity", ["organic", "grid"], default="organic", typing_rule=_plot_regularity_ok))
register_knob(Knob("grain_drift", [-12, -8, -4, 0, 4, 8, 12], default=0))  # degrees of paddy-grain drift off the fall-line


LANE_SKELETONS = ("spine", "T", "Y", "cross", "waterside")


def skeleton_layout(kind: str, cx: float, cy: float, ex: float, ey: float) -> dict[str, Any]:
    """Pure geometry for a nucleated cluster's internal lane skeleton. Given the cluster center (cx, cy)
    and its half-extents (ex horizontal, ey vertical, in px), returns the lane polylines plus the two
    DERIVED focal points a village reads by: the headman compound (the grandest house, at the skeleton's
    prime spot) and the gateway (the downslope exit where the connector track leaves and the tutelary
    shrine sits). Screen frame: -y = upslope/back (the high, dry 背 side), +y = downslope toward the
    field; +x = toward the field flank. The headman lands at a DIFFERENT spot per skeleton (never a fixed
    offset), which is the whole point - it is why two same-water villages stop sharing a headman position.
    Grounding (research.md D2): a nucleated village's lanes followed its site - a spine along a ridge, a T
    where a spur met the field track, a Y where two approaches merged, a cross at a small market node, a
    waterside lane in a stream village - and the headman sat at that skeleton's focal point, not a pixel."""
    top, bot = cy - ey, cy + ey
    if kind == "spine":  # one lane along the margin; headman at the high HEAD, gateway at the low foot
        lanes = [[(cx, top), (cx, bot)]]
        return {"kind": kind, "lanes": lanes, "headman": (cx, top + ey * 0.12), "gateway": (cx, bot)}
    if kind == "T":  # spine + an upper crossbar toward the field; headman at the T-junction
        cj = cy - ey * 0.4
        lanes = [[(cx, top), (cx, bot)], [(cx - ex, cj), (cx + ex, cj)]]
        return {"kind": kind, "lanes": lanes, "headman": (cx, cj), "gateway": (cx, bot)}
    if kind == "Y":  # two approaches merging into one downslope stem; headman at the fork
        fy = cy + ey * 0.2
        lanes = [[(cx - ex * 0.7, top), (cx, fy)], [(cx + ex * 0.7, top), (cx, fy)], [(cx, fy), (cx, bot)]]
        return {"kind": kind, "lanes": lanes, "headman": (cx, fy), "gateway": (cx, bot)}
    if kind == "cross":  # two crossing lanes at a small market node; headman in an adjacent quadrant
        lanes = [[(cx, top), (cx, bot)], [(cx - ex, cy), (cx + ex, cy)]]
        return {"kind": kind, "lanes": lanes, "headman": (cx - ex * 0.4, cy - ey * 0.22), "gateway": (cx, bot), "market": (cx, cy)}
    if kind == "waterside":  # a lane hugging the water flank; headman fronting the water
        lanes = [[(cx - ex, top), (cx - ex, bot)]]
        return {"kind": kind, "lanes": lanes, "headman": (cx - ex, cy), "gateway": (cx - ex, bot)}
    raise ValueError(f"unknown lane_skeleton {kind!r}; expected one of {LANE_SKELETONS}")


class Settlement:
    def __init__(self, W: int = 1820, H: int = 1180, seed: int = 23) -> None:
        random.seed(seed)
        self.W, self.H = W, H
        self.seed = seed  # drives every unpinned knob's independent deterministic roll (feature 005)
        self.knob_pins: dict[str, Any] = {}  # knobs the spec pinned explicitly (bypass the roll)
        self._resolved_knobs: dict[str, Any] = {}  # knobs resolved so far, fed into later knobs' typing context
        self.out: list[str] = []
        self.top: list[str] = []  # deferred TOP layer (gate furniture, torii, kido) - over roads/buildings
        self.toplabels: list[str] = []  # deferred LABEL layer - the very last thing drawn, so TEXT is never
        #                           covered by anything (a label must always be fully readable)
        self.walls: list[str] = []  # deferred WALL layer (city rampart) - over the ground lanes + buildings,
        #                           under the TOP layer, so a street running INTO a wall passes beneath it
        self.ground: list[dict[str, Any]] = []  # deferred LINEAR ground features (alley < street < road): the wider
        self._ground_idx: int | None = None  # lane renders on top. Flushed as one ordered block (below buildings).
        self.water: list[dict[str, Any]] = []  # deferred WATERCOURSES (streams, channels, moat): all BEDS in one
        self._water_idx: int | None = None  # shared-opacity group, then all SHEENS in another, so crossings MERGE
        self._late_water_idx: int | None = None  # a SECOND water block for comb-field channels (opt-in via
        self.late_water: list[dict[str, Any]] = []  # field_channel(late=True)): spliced at its own first-call
        # position, AFTER the field's plots - a city draws its moat/river first, which anchors the shared
        # block early and would composite the whole ditch network UNDER the later-drawn paddy plots (the
        # network invisible + its uncovered corridors reading as parchment pinstripes; 2026-07-21). The
        # villages never hit this (their gens reach water after the fields), so late defaults False and
        # their output is byte-identical. Late ends are clipped to abut other water (never overlap), so
        # the two blocks cannot double-composite into a dark seam.
        #                           into a continuous confluence instead of stacking opacity (a dark seam).
        self.bscale = 1.0  # urban-building footprint scale (a large town packs at a finer grain)
        self.ftpx = 1.0  # declared REAL scale, feet per pixel - set via meta(ftpx=...); the
        #                           glyph library is calibrated at town scale (1 ft/px), so 1.0 = identity
        self.placed: list[Any] = []  # (x, y, w, h)
        self.grove_rects: list[Any] = []  # (x, y, w, h) homestead-grove arms - kept OUT of `placed` so adjacent groves
        #                           may MERGE (abut) where houses cluster; `_fits` still steers wells off them
        self._pending_farmsteads: list[Any] = []  # farmhouses awaiting their threshing yard (drawn by farmsteads())
        self.corridors: list[Any] = []  # polylines houses must avoid
        self.bound: Any = None  # optional bounding polygon: placement stays inside it (city wall)
        self.view: Any = None  # optional (ox,oy,w,h) viewBox crop - render/checks treat it as the map edge
        self.field_polys: list[Any] = []  # smoothed outlines used for blocking
        self.ellipses: list[Any] = []  # (cx, cy, rx, ry) hill/pond/manor - block houses
        self.block_polys: list[Any] = []  # arbitrary no-build polygons (e.g. forest)
        # SWEPT/TENDED GROUND around sacred + funerary features - a keep-out for the LOOSE HINTERLAND
        # SCATTER (commons scrub + marsh reeds) ONLY, not for building placement and not for the grove.
        # A shrine precinct, the ground under a torii and along its sando, and the collar tended around
        # graves were kept clear of wild scrub in reality (raked gravel precinct; the tomb-swept grave
        # collar); the surrounding waste stays scrubby. So this clears a small verge around each, while a
        # shrine's deliberate fengshui/chinju-no-mori grove (a separate feature) is left untouched. See
        # settlements.md 'Swept ground around sacred + funerary features'.
        self.clearings: list[Any] = []
        self._cover_n = 0  # ground-cover scatter ordinal (commons + marsh draws). Each cover entry and each
        #                    swept clearing records it, so the scatter_respects_swept_clearings check can see
        #                    ORDER: a scatter only skips clearings that exist when it runs, so a cover whose
        #                    seq <= a clearing's seq drew before the clearing was registered and may have
        #                    dotted scrub/reeds over the swept ground (fix: s.reserve_clearing FIRST).
        self.dry_polys: list[Any] = []  # dry crop plots (comb hems, vegetable tracts): FOOTPRINT-aware no-build
        #                           cropland - block_polys test only a candidate's CENTER, which let a house
        #                           centered just off a hem strip stand half its footprint on the crop (GM,
        #                           2026-07); these get an edge margin in _in_blocked + a rect test for groves
        self._bbox_cache: dict[Any, Any] = {}  # id(poly-list) -> (len, [per-poly (minx,miny,maxx,maxy)]) for the collision
        #                           pre-filter: reject a far polygon cheaply before the O(vertices) corner /
        #                           segment tests (the homestead solver probes _rect_blocked ~100k+ times)
        self._water_obs_cache: Any = None  # (lengths-key, [(poly, keep-out half-width, bbox)]) - same pre-filter idea
        #                                for _rect_on_water's irrigation lines (channels / ditches / streams)
        self._clip = 0
        self._nbig = 0
        self.M: Manifest = {
            "houses": [],
            "fields": [],
            "fallow_patches": [],
            "channels": [],
            "lane": [],
            "taxfree": [],
            "torii": [],
            "shrines": [],
            "manors": [],
            "streams": [],
            "buildings": [],
            "pastures": [],
            "forest_patches": [],
            "religious": [],
            "flower_fields": [],
            "labels": [],
            "pond": None,
            "storehouses": [],
            "flophouses": [],
            "hill": None,
            "summit": None,
            "shrine": None,
            "forest": None,
            "road": None,
            "wall": None,
            "gate": None,
            "gates": [],
            "moat": None,
            "governor_mansion": None,
            "ministries": [],
            "inspection_stations": [],
            "wells": [],
            "bridges": [],
            "threshing_yards": [],
            "gardens": [],
            "groves": [],
            "cemeteries": [],
            "mausoleums": [],
            "cremation_grounds": [],
            "ossuaries": [],
            "moat_layer": None,
            "fire_towers": [],
            "field_ditches": [],
            "village_groves": [],
            "commons": [],
            "dry_plots": [],
            "marshes": [],
            "byres": [],
            "farm_sheds": [],
            "quarters": [],
            "meta": {"W": W, "H": H},
        }
        self._header()

    # ---- low level
    # draw-order index (z): base-layer items keep their position; TOP-layer items get a
    # huge offset so they always render above the base (roads must pass UNDER them)
    TOPZ = 10_000_000
    LABELZ = 20_000_000  # the LABEL layer renders above even the TOP layer - text is never covered
    WALLZ = 1_000_000  # the WALL layer renders above every ground lane and building (which sit in
    #                          self.out, z < len(out)), below the TOP layer - so lanes pass UNDER walls

    def add(self, s: str) -> int:
        z = len(self.out)
        self.out.append(s)
        return z

    def add_wall(self, s: str) -> int:
        z = self.WALLZ + len(self.walls)
        self.walls.append(s)
        return z

    def add_label(self, s: str) -> int:
        z = self.LABELZ + len(self.toplabels)
        self.toplabels.append(s)
        return z

    def add_top(self, s: str) -> int:
        z = self.TOPZ + len(self.top)
        self.top.append(s)
        return z

    def _ground(self, zpri: float, rec: Any, zkey: str, edge: Any = None, bed: Any = None, top: Any = None) -> None:
        """Defer a linear ground feature (alley/street/road/ring road). The whole set renders as ONE
        block, in THREE sub-layers so crossings read as clean CROSSROADS: all EDGE strokes (the dark
        borders) at the bottom, then all BED strokes (the paved surfaces), then all TOP marks (center
        dashes / gravel speckle). Because every edge sits below every bed, no edge line ever cuts across
        another lane's bed at a junction - the beds merge into a continuous crossroads. Within each
        sub-layer the wider lane (higher zpri = WIDTH) is on top, so the wider road still wins where two
        beds overlap (road 26 > avenue 22 > street 18 > alley 10). Each feature records its BED's final
        draw position (rec[zkey]) for the width-layering check."""
        if self._ground_idx is None:
            self._ground_idx = len(self.out)
            self.out.append("")  # placeholder, replaced by the sorted block at finish()
        self.ground.append({"zpri": zpri, "seq": len(self.ground), "edge": edge, "bed": bed, "top": top, "rec": rec, "zkey": zkey})

    def _water(self, bed: Any, rec: Any, sheen: Any = None, edge: Any = None, clip: Any = None, pond_fill: bool = False, late: bool = False) -> None:
        """Defer a watercourse (stream / channel / moat / POND) so the whole set renders as ONE block, in
        THREE sub-layers: all EDGES (pond rims - the only water feature with a border) at the bottom, then
        all BEDS (the blue water bodies, same color) inside one shared-opacity group, then all SHEENS (the
        lighter mid-current highlights) inside another above it. The shared bed-group opacity means
        overlapping water does NOT stack opacity into a dark seam where two courses cross - the beds
        composite into a single continuous body (a confluence), exactly as the ground beds merge into a
        clean crossroads. And because every EDGE sits below every bed, a feeder's bed COVERS a pond's rim
        where it meets it - so the stream/channel JOINS the pond at the rim (a clean gap) instead of the rim
        cutting across its mouth. Each course records its bed's / sheen's draw position on `rec` (bedz /
        sheenz) for waterways_merge_at_crossings. Spliced at the FIRST water call's position, so later fields
        still paint over a channel's end. `clip` (optional {'pts','bed_t','sheen_t'}) marks a pond-anchored
        feeder whose bed/sheen are RE-EMITTED at flush, snapped to the rim - deferred so it works even when the
        feeder is drawn BEFORE the pond (M['pond'] is not known at call time). `pond_fill` marks the pond's
        water body, drawn LAST among the beds so it paints over any feeder's inside-the-rim overshoot."""
        if late:
            if self._late_water_idx is None:
                self._late_water_idx = len(self.out)
                self.out.append("")  # placeholder for the LATE block (see __init__)
            self.late_water.append({"bed": bed, "sheen": sheen, "edge": edge, "rec": rec, "clip": clip, "pond_fill": pond_fill})
            return
        if self._water_idx is None:
            self._water_idx = len(self.out)
            self.out.append("")  # placeholder, replaced by the three-group block at finish()
        self.water.append({"bed": bed, "sheen": sheen, "edge": edge, "rec": rec, "clip": clip, "pond_fill": pond_fill})

    def _cid(self, prefix: str) -> str:
        self._clip += 1
        return f'{prefix}{self._clip}'

    def _header(self) -> None:
        self.add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.W} {self.H}" font-family="Georgia, \'Times New Roman\', serif">')
        self.add('<defs>')
        self.add(
            '<pattern id="drycrop" width="12" height="12" patternUnits="userSpaceOnUse">'
            '<rect width="12" height="12" fill="#CDB57E"/>'
            '<line x1="0" y1="3" x2="12" y2="3" stroke="#A98E54" stroke-width="0.7"/>'
            '<line x1="0" y1="8" x2="12" y2="8" stroke="#A98E54" stroke-width="0.7"/></pattern>'
        )
        self.add(
            '<pattern id="fallow" width="14" height="14" patternUnits="userSpaceOnUse">'
            '<rect width="14" height="14" fill="#D7C49A"/>'
            '<circle cx="3" cy="4" r="0.9" fill="#A89464"/>'
            '<circle cx="9" cy="9" r="0.9" fill="#A89464"/>'
            '<circle cx="11" cy="3" r="0.7" fill="#B7A06C"/></pattern>'
        )
        self.add('</defs>')
        self.add(f'<rect width="{self.W}" height="{self.H}" fill="{LAND}"/>')

    def meta(self, **kw: Any) -> None:
        if "ftpx" in kw:
            # The map's declared real scale in FEET PER PIXEL - the GM's ladder: hamlet/town 1,
            # village 2, provincial city 3 (the round numbers are deliberate; a human should be
            # able to read distances off the map). Buildings follow automatically via
            # bscale = 1/ftpx: the urban glyph library is calibrated at town scale (a 44x29px
            # farmhouse ~ the 46x28 ft minka anchor), so the building grain IS the scale change -
            # this is what keeps a "merchant house" the same real ~57 ft on every map.
            # VILLAGE maps are exempt: their placement constants (23x14 farmhouse, garden/yard
            # caps, grove bands, the well 0.52 factor) were hand-pre-scaled to 2 ft/px before
            # ftpx existed, and re-deriving them through bscale would perturb every tuned
            # village map for zero visual gain - so a village declares ftpx=2 for the record
            # (and for the checks) but keeps bscale = 1.0.
            self.ftpx = kw["ftpx"]
            if kw.get("scale", self.M["meta"].get("scale")) != "village":
                self.bscale = 1.0 / self.ftpx
        self.M["meta"].update(kw)

    def pin_knob(self, name: str, value: Any) -> None:
        """Pin a knob to an explicit value, bypassing the roll. The pin is still validated against the
        knob's value_space + typing_rule when `resolve` is called (an invalid pin is a loud error)."""
        self.knob_pins[name] = value

    def knob_context(self) -> dict[str, Any]:
        """The geography/other-knob context a typing_rule reads: the map meta (scale, down_deg, region,
        water-source kind, ...) plus every knob resolved so far, so a later knob's rule can depend on an
        earlier resolved one."""
        ctx = dict(self.M["meta"])
        ctx.update(self._resolved_knobs)
        return ctx

    def resolve(self, name: str, do_roll: bool = True) -> Any:
        """Resolve a knob (pinned -> rolled -> default) against the running context, record it so later
        knobs' typing rules can read it, and return the value."""
        val = resolve_knob(name, self.seed, self.knob_context(), self.knob_pins, do_roll=do_roll)
        self._resolved_knobs[name] = val
        return val

    def px(self, ft: float) -> float:
        """A real-world size in FEET -> drawn pixels at this map's declared scale (meta ftpx)."""
        return ft / self.ftpx

    def lw(self, ft: float) -> float:
        """Linework width in px for a real width in FEET, floored at 4px. Standard cartographic
        practice: thin linear features (a 5 ft roji, a hairline gutter) are drawn at a minimum
        visible width rather than to scale, because at 3 ft/px they would be under 2px and vanish.
        True-width-or-floored, never inflated past the floor - so wide features stay honest and
        the floor only rescues features that would otherwise be invisible."""
        return max(ft / self.ftpx, 4.0)

    def set_view(self, ox: float, oy: float, w: float, h: float) -> None:
        """Crop the rendered map to (ox,oy,w,h) instead of the full canvas. Placement still uses
        the full coordinate space, so off-view features (estates, farmland) simply run off the
        edge. The checks read meta['view'] and treat this crop - not the canvas - as the map edge.
        Used for city maps, which 'just barely encompass' the walled city and let the countryside
        run off the edge (a city map is about the city; a town map is about its surroundings)."""
        self.view = (ox, oy, w, h)
        self.M["meta"]["view"] = [ox, oy, w, h]

    # solid HARD footprints the frame must fully contain (+ margin); the fields and pond are added specially.
    # Everything NOT listed here - the commons scrub, streams/channels/lanes - does not set the frame: it is
    # drawn and simply CLIPS at the crop edge (the frame stays tight to the settlement + its fields).
    # NOT "village_groves" (GM 2026-07-20): the COMMUNAL windbreak/copse may CLIP at the frame edge - a
    # partially visible belt reads as "the wood continues", and a smaller crop beats a larger one whose only
    # extra content is more of the same grove (this held Kikuta's frame open north of the village). The belt
    # hugs the cluster, so the houses' own margin always keeps part of it in view; hard_features_within_frame
    # requires partial visibility (not containment) for it, and crop_hugs_content gates the tightness.
    # Homestead "groves" stay: each hugs its own farmhouse, so it never drags the frame anyway.
    _CROP_HARD = (
        "houses",
        "gardens",
        "threshing_yards",
        "groves",
        "dry_plots",
        "buildings",
        "manors",
        "religious",
        "shrines",
        "flophouses",
        "storehouses",
        "farm_sheds",
        "merchant_estates",
        "wells",
        "fire_towers",
        "ministries",
        "inspection_stations",
        "cemeteries",
        "mausoleums",
        "cremation_grounds",
        "ossuaries",
        "forest_patches",
        "pastures",
    )

    def crop_to_content(self, margin: float = 30) -> None:
        """Frame the map to its CONTENT: set the render viewBox to the bounding box of the HARD features placed
        SO FAR plus `margin`, so the image is exactly as large as the settlement + its fields, tight to `margin`
        on every side (nonstandard sizes are fine, and the checks already treat the crop - not the canvas - as
        the map edge). Call this AFTER the large features (water, fields, houses) AND after any SET-APART
        hard feature that would otherwise sit outside the frame (a back-slope graveyard, an outlying shrine -
        those must be placed BEFORE the crop so it includes them), and BEFORE the small features that DROP INTO
        the framed space (wells among the houses, monk plots) AND the title.
        HARD (`_CROP_HARD` + torii arches + the fields' VISIBLE extent + the pond) is what sets the frame. Everything else -
        the BLEED commons scrub AND the linear/off-map RUNNERS (streams, channels, lanes) - does NOT affect the
        frame: it is drawn and simply CLIPS at the edge, trailing off as 'more wild ground / more map this way'.
        (We used to extend the frame to preserve 2/3 of a trailing commons, but the GM wants the frame tight to
        the real content - a graveyard, the pond - never held open by empty back-slope grazing, so the commons
        now clips like the marsh instead of dragging the frame out.)"""
        hx: list[float] = []
        hy: list[float] = []
        for k in self._CROP_HARD:
            for o in self.M.get(k, []):
                if o.get("poly"):
                    hx += [p[0] for p in o["poly"]]
                    hy += [p[1] for p in o["poly"]]
                elif "r" in o:  # a well records {x, y, r} - no poly, no w/h. Latent bug found 2026-07-20:
                    hx += [o["x"] - o["r"], o["x"] + o["r"]]  # wells never set the frame at all, and the
                    hy += [o["y"] - o["r"], o["y"] + o["r"]]  # windbreak band silently covered for them until
                    #                                           the grove stopped counting (crop_hugs_content)
                elif "w" in o and "h" in o:
                    hx += [o["x"] - o["w"] / 2, o["x"] + o["w"] / 2]
                    hy += [o["y"] - o["h"] / 2, o["y"] + o["h"] / 2]
        for t in self.M.get("torii", []):  # a torii ARCH is a visible structure and must be
            hx += [t[0] - 19, t[0] + 19]  # framed too (same box the within-frame check uses:
            hy += [t[1] - 10, t[1] + 18]  # x +/-19, y -10..+18) - else a gateway can poke past

        for fd in self.M.get("fields", []):  # the field's VISIBLE extent, NOT its house-blocking envelope tail
            vb = fd.get("vis_bbox")
            if vb:
                hx += [vb[0], vb[2]]
                hy += [vb[1], vb[3]]
            else:
                hx += [p[0] for p in fd["outline"]]
                hy += [p[1] for p in fd["outline"]]
        if self.M.get("pond"):
            cx, cy, rx, ry = self.M["pond"]
            hx += [cx - rx, cx + rx]
            hy += [cy - ry, cy + ry]
        if self.M.get("forest"):  # the FOREST is a big EDGE feature (a point-list, not
            fpts = self.M["forest"]  # dicts): frame to include it, CLAMPED to the canvas so
            hx += [min(max(p[0], 0), self.W) for p in fpts]  # the view never opens past the edge (the forest fills
            hy += [min(max(p[1], 0), self.H) for p in fpts]  # to the frame edge and bleeds beyond)
        if not hx:  # pragma: no cover - crop is called only after the hard features are placed
            return
        # clamp the frame to the canvas: never open the view PAST the map edge (an EDGE feature like the forest
        # fills to the canvas edge, so its side must be the frame edge with no margin gap - else it reads as
        # "stopping short"). Content within the canvas is unaffected (villages crop tighter than this anyway).
        x0, y0 = max(0, min(hx) - margin), max(0, min(hy) - margin)
        x1, y1 = min(self.W, max(hx) + margin), min(self.H, max(hy) + margin)
        self.set_view(round(x0), round(y0), round(x1 - x0), round(y1 - y0))

    # ---- fields
    def paddy_field(self, shape: Any, label: Any, name: str, amp: float = 52, taxfree: int = 0, fallow_patch: Any = None, label_xy: Any = None, plot: float = 46, kind: str = "paddy") -> None:
        """shape: a bbox (x0,y0,x1,y1) OR a list of base polygon vertices (e.g. a V).
        `plot` is the target plot (sub-paddy) size in px: the field is quilted into jittered
        bunded plots at roughly this grain. Smaller -> a finer patchwork of more, smaller paddies.
        Default 46 is the fine grain that reads as intensively-worked premodern paddy (a 1-cho
        holding was subdivided into dozens of small irregular bunded plots). VERIFIED HONEST at the
        declared scales (audit 2026-07-21): the village grain (plot=34 at 2 ft/px -> ~435 m2) sits
        inside the real 130-600 m2 basin band, and the default (46 -> ~785 m2 at 2 ft/px) is within
        the real parcel range (mean ~1 mu = ~600 m2, merged holdings larger) - no legibility
        inflation is in play, and the houses are true-scale too. The bund stroke thins with the
        grain to suit. See the "Paddy plot grain" entry in the settlements.md historical grounding."""
        bund = 0.03 * plot + 0.35  # bund (aze) stroke thins with the plot grain: ~2.6 at the old 76, ~1.7 at 46
        if len(shape) == 4 and all(isinstance(v, (int, float)) for v in shape):
            bbox = tuple(shape)
            outline = organic_bbox(bbox, amp)
        else:
            base = list(shape)
            outline = organic_poly(base, amp)
            xs = [p[0] for p in outline]
            ys = [p[1] for p in outline]
            bbox = (min(xs), min(ys), max(xs), max(ys))
        x0, y0, x1, y1 = bbox
        smoothed = smooth_points(outline)
        self.M["fields"].append({"name": name, "bbox": list(bbox), "kind": kind, "outline": [[x, y] for (x, y) in smoothed]})
        self.field_polys.append(smoothed)
        d = smooth_closed(outline)
        cid = self._cid('fld')
        self.add(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
        ex0, ey0, ex1, ey1 = x0 - amp, y0 - amp, x1 + amp, y1 + amp

        # PADDY PATCHWORK: pre-modern paddies were an IRREGULAR patchwork of odd-sized bunded plots fitted
        # together by piecemeal reclamation and inheritance - NOT the regular grid of modern (Meiji/Showa)
        # land consolidation. Build it by recursively splitting the field with straight, slightly-angled aze
        # (bund) lines that cut the LONG axis of each plot at a jittered fraction, down to the target grain
        # (with size variation), so bunds meet at T-junctions like real cadastral paddy. See settlements.md.
        _fillstate = random.getstate()  # ISOLATE the paddy fill RNG: the patchwork, crop
        random.seed(int(abs(x0) * 7 + abs(y0) * 13 + abs(x1) * 3 + len(name)))  # roll, growth stage and mottle
        plots = self._paddy_plots((ex0, ey0, ex1, ey1), plot)  # are decorative and must NOT shift
        self.add(f'<g clip-path="url(#{cid})">')  # downstream house placement
        self.add(f'<rect x="{ex0:.0f}" y="{ey0:.0f}" width="{ex1 - ex0:.0f}" height="{ey1 - ey0:.0f}" fill="#C2A772"/>')
        interior: list[Any] = []
        for poly in plots:
            pts = ' '.join(f'{q[0]:.0f},{q[1]:.0f}' for q in poly)
            cx = sum(q[0] for q in poly) / len(poly)
            cy = sum(q[1] for q in poly) / len(poly)
            # CROP MIX: an irrigated valley exists to grow RICE (~85% of the watered common). Dry upland crops
            # (barley/veg, soy) cluster on the MARGINS - the higher, harder-to-water rim - while the well-watered
            # interior is all paddy. So dry/soy probability rises toward the field edge. See settlements.md 'Crop mix'.
            edge = max(0.0, 1.0 - edge_dist(cx, cy, smoothed) / (2.4 * plot))  # 1 at the rim, 0 deep interior
            r = random.random()
            dry_p, soy_p = 0.05 + 0.24 * edge, 0.03 + 0.11 * edge
            crop = 'dry' if r < dry_p else ('soy' if r < dry_p + soy_p else 'rice')
            if crop == 'rice':
                # a village transplants TOGETHER (shared water, exchanged labor), so its paddies are largely
                # ONE stage - here high-summer green - with only minor spread (early/late rice varieties, the odd
                # low flooded plot); NOT a rainbow of stages. See settlements.md 'Crop mix / paddy surface'.
                st = random.random()
                if st < 0.06:
                    fill, flooded = random.choice(FLOODED_SHADES), True
                elif st > 0.95:
                    fill, flooded = random.choice(RIPE_SHADES), False
                else:
                    fill, flooded = random.choice(PADDY_SHADES), False
                self.add(f'<polygon points="{pts}" fill="{fill}" stroke="#C2A772" stroke-width="{bund:.1f}" stroke-linejoin="round"/>')
                self._paddy_surface(poly, pts, flooded)
            else:
                fill = 'url(#drycrop)' if crop == 'dry' else '#9CB36A'
                self.add(f'<polygon points="{pts}" fill="{fill}" stroke="#C2A772" stroke-width="{bund:.1f}" stroke-linejoin="round"/>')
                self._rows(poly, pts, crop)  # dryland crops ARE ridge/row-cultivated
            if point_in_poly(cx, cy, smoothed):
                interior.append((poly, cx, cy))
        if label and taxfree:
            self._taxfree_plots(interior, taxfree)
        if fallow_patch:
            self._fallow_patch(fallow_patch)
        self.add('</g>')
        random.setstate(_fillstate)  # end fill-RNG isolation
        self.add(f'<path d="{d}" fill="none" stroke="#A98A52" stroke-width="3.5"/>')
        if label:
            lx, ly = label_xy if label_xy else ((x0 + x1) / 2, (y0 + y1) / 2)
            z = self.add_label(
                f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" font-size="15" '
                f'font-weight="bold" fill="#33301E" letter-spacing="1.5" '
                f'paint-order="stroke" stroke="{LAND}" stroke-width="3.5">{label}</text>'
            )
            self._record_label(lx, ly, label, 15, "middle", z)

    @staticmethod
    def _split_convex(poly: Poly, px: float, py: float, nx: float, ny: float) -> tuple[Poly, Poly]:
        """Split a convex polygon by the line through (px, py) with normal (nx, ny) into (pos, neg) polygons."""

        def side(v: Pt) -> float:
            return (v[0] - px) * nx + (v[1] - py) * ny

        pos: Poly = []
        neg: Poly = []
        n = len(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            sa, sb = side(a), side(b)
            if sa >= 0:
                pos.append(a)
            if sa <= 0:
                neg.append(a)
            if (sa > 0) != (sb > 0):
                t = sa / (sa - sb)
                pos.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
                neg.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
        return pos, neg

    def _paddy_plots(self, bbox: Any, grain: float) -> list[Poly]:
        """Recursively split a field into an irregular patchwork whose plots share a coherent GRAIN aligned to
        the water and slope - the bunds run along the CONTOUR (NE-SW, for the default NW-uphill tilt) and down
        the FALL LINE (NW-SE), with plots mildly elongated along-contour and stepping downhill - so the paddy
        reads as ORGANIZED BY THE WATER, not randomly diced. Still irregular (jittered split fractions +
        slightly non-parallel bunds), just coherent. Tiles the bbox; clipped to the field outline."""
        ux, uy = 0.7071, -0.7071  # contour (along-slope) = a plot's LONG axis
        fx, fy = 0.7071, 0.7071  # fall line (downhill SE) = a plot's SHORT axis
        aspect = 1.7
        tvf, tvu = grain * 0.78, grain * 0.78 * aspect  # target extents across the fall line / along the contour
        x0, y0, x1, y1 = bbox
        stack: list[Poly] = [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]
        out: list[Poly] = []
        guard = 0
        while stack and guard < 24000:
            guard += 1
            poly = stack.pop()
            cx = sum(q[0] for q in poly) / len(poly)
            cy = sum(q[1] for q in poly) / len(poly)
            us = [q[0] * ux + q[1] * uy for q in poly]
            fs = [q[0] * fx + q[1] * fy for q in poly]
            u_ext, f_ext = max(us) - min(us), max(fs) - min(fs)
            over_f = f_ext > tvf * random.uniform(0.72, 1.45)
            over_u = u_ext > tvu * random.uniform(0.78, 1.6)
            if not over_f and not over_u:
                out.append(poly)
                continue
            if over_f and (not over_u or f_ext / tvf >= u_ext / tvu):
                nx, ny, lo, hi, cen = fx, fy, min(fs), max(fs), cx * fx + cy * fy  # contour bund (normal = fall line)
            else:
                nx, ny, lo, hi, cen = ux, uy, min(us), max(us), cx * ux + cy * uy  # cross bund (normal = contour)
            d = lo + (hi - lo) * random.uniform(0.36, 0.64)  # jittered split position
            px, py = cx + (d - cen) * nx, cy + (d - cen) * ny  # a point on the cut line
            ang = random.uniform(-0.12, 0.12)  # slight wobble - bunds not ruler-parallel
            ca, sa = math.cos(ang), math.sin(ang)
            nnx, nny = nx * ca - ny * sa, nx * sa + ny * ca
            a, b = self._split_convex(poly, px, py, nnx, nny)
            if len(a) >= 3 and len(b) >= 3:
                stack.append(a)
                stack.append(b)
            else:
                out.append(poly)  # pragma: no cover - defensive: a line cutting a convex polygon yields two >=3-gons except the measure-zero exact-tangent case
        return out + stack

    def _taxfree_plots(self, interior: Any, taxfree: int) -> None:
        """Mark `taxfree` scattered interior paddy plots vermilion (a priestess's / temple's tax-free land)."""
        if not interior:
            return
        interior = sorted(interior, key=lambda t: (round(t[2] / 40), t[1]))  # spread them across the field
        n = len(interior)
        for i in sorted(set(min(n - 1, int(n * (k + 0.5) / (taxfree + 1))) for k in range(taxfree))):
            poly, cx, cy = interior[i]
            pts = ' '.join(f'{q[0]:.0f},{q[1]:.0f}' for q in poly)
            self.add(f'<polygon points="{pts}" fill="#A03020" fill-opacity="0.22" stroke="#A03020" stroke-width="4"/>')
            self.M["taxfree"].append([round(cx, 1), round(cy, 1)])

    def _paddy_surface(self, poly: Poly, pts: str, flooded: bool) -> None:
        """A WET paddy: a flooded, mottled sheet (irregular hand-transplanted shoots, plus a faint water sheen
        for a freshly-flooded plot) - NOT ruled rows. Premodern rice was transplanted irregularly; crisp
        checkrow planting (seijoue) is a Meiji improvement, so ruled rows on a paddy read as modern (the same
        era-tell as the consolidation grid). See settlements.md 'Crop mix / paddy surface'."""
        xs = [q[0] for q in poly]
        ys = [q[1] for q in poly]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        rcid = self._cid('ps')
        g = [f'<clipPath id="{rcid}"><polygon points="{pts}"/></clipPath>', f'<g clip-path="url(#{rcid})">']
        if flooded:  # faint sheen lines = standing water catching the light
            for _ in range(2):
                yy = random.uniform(y0 + 2, y1 - 2)
                g.append(f'<line x1="{x0:.0f}" y1="{yy:.0f}" x2="{x1:.0f}" y2="{yy:.0f}" stroke="#CFDFD3" stroke-width="1.5" opacity="0.4"/>')
        n = min(22, max(3, int((x1 - x0) * (y1 - y0) / 80)))  # sparse irregular shoots (the transplant mottle)
        for _ in range(n):
            g.append(f'<circle cx="{random.uniform(x0, x1):.1f}" cy="{random.uniform(y0, y1):.1f}" r="1.0" fill="#6F9061" opacity="0.5"/>')
        g.append('</g>')
        self.add(''.join(g))

    def _rows(self, quad: Poly, pts: str, crop: str) -> None:
        xq = [p[0] for p in quad]
        yq = [p[1] for p in quad]
        cx0, cx1, cy0, cy1 = min(xq), max(xq), min(yq), max(yq)
        ccx, ccy = (cx0 + cx1) / 2, (cy0 + cy1) / 2
        diag = math.hypot(cx1 - cx0, cy1 - cy0)
        theta = random.uniform(-0.6, 0.6)  # per-plot row angle
        dxu, dyu = math.cos(theta), math.sin(theta)
        nx, ny = -dyu, dxu
        rcid = self._cid('rc')
        self.add(f'<clipPath id="{rcid}"><polygon points="{pts}"/></clipPath>')
        # _rows is only ever called for dry/soy plots (rice paddies get _paddy_surface, no rows), so the
        # styling here is the dryland one - dashed, olive, wider spacing
        spacing, stroke, wdt, dash, op = 13, '#7E9B54', 0.8, ' stroke-dasharray="1,3"', 0.85
        g = [f'<g clip-path="url(#{rcid})">']
        s = -diag / 2
        while s <= diag / 2:
            mx_, my_ = ccx + nx * s, ccy + ny * s
            g.append(
                f'<line x1="{mx_ - dxu * diag / 2:.0f}" y1="{my_ - dyu * diag / 2:.0f}" '
                f'x2="{mx_ + dxu * diag / 2:.0f}" y2="{my_ + dyu * diag / 2:.0f}" '
                f'stroke="{stroke}" stroke-width="{wdt}"{dash} opacity="{op}"/>'
            )
            s += spacing
        g.append('</g>')
        self.add(''.join(g))

    def _fallow_patch(self, base: Poly) -> None:
        """A blighted sub-region inside a field: fallow stipple + red X marks. No
        abandoned houses implied (that is a village-specific story, not universal)."""
        d = smooth_closed(organic_poly(base, 16))
        self.add(f'<path d="{d}" fill="url(#fallow)" stroke="#9C7A40" stroke-width="1.6" stroke-dasharray="5,3"/>')
        xs = [p[0] for p in base]
        ys = [p[1] for p in base]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        for _ in range(4):
            mx = cx + random.uniform(-1, 1) * (max(xs) - min(xs)) * 0.28
            my = cy + random.uniform(-1, 1) * (max(ys) - min(ys)) * 0.28
            self.add(f'<g transform="translate({mx:.0f},{my:.0f})" stroke="#9A3A2A" stroke-width="2.4"><line x1="-7" y1="-7" x2="7" y2="7"/><line x1="-7" y1="7" x2="7" y2="-7"/></g>')
        self.M["fallow_patches"].append({"outline": [[round(p[0], 1), round(p[1], 1)] for p in smooth_points(organic_poly(base, 16))]})

    def water_field(self, shape: Any, label: Any, name: str, source: Any, drain: Any, amp: float = 52, taxfree: int = 0, plot: float = 34, label_xy: Any = None, drain_anchor: Any = None) -> None:
        """A rice field built WATER-FIRST: the irrigation network is the generative skeleton, and the plots,
        crops, and colors are all DERIVED from it, so the map actually communicates the hydrology. Water
        enters from `source` (the high NW side, fed from the pond) and drains to `drain` (the low SE side). A
        HEAD ditch runs along the high edge; LATERALS run down the fall line, dividing the field into strips;
        paddies stack between them; a DRAIN ditch collects at the low edge and leaves toward `drain`. Crop
        FOLLOWS the water (rice hugging the ditches, dry upland crops where the network doesn't reach - wide-
        strip middles and the margins); the paddy is ~ONE green (a rice field, not a color mix). Records a
        feed channel (pond->field) and a drain channel (field->drain) so the checks see the supply. See
        settlements.md 'Water-first fields'."""
        if len(shape) == 4 and all(isinstance(v, (int, float)) for v in shape):
            bbox = tuple(shape)
            outline = organic_bbox(bbox, amp)
        else:
            outline = organic_poly(list(shape), amp)
            xs = [q[0] for q in outline]
            ys = [q[1] for q in outline]
            bbox = (min(xs), min(ys), max(xs), max(ys))
        x0, y0, x1, y1 = bbox
        smoothed = smooth_points(outline)
        self.M["fields"].append({"name": name, "bbox": list(bbox), "kind": "paddy", "outline": [[x, y] for (x, y) in smoothed]})
        self.field_polys.append(smoothed)
        d = smooth_closed(outline)
        cid = self._cid('fld')
        self.add(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
        bund = 0.03 * plot + 0.35

        # WATER FRAME: f = downhill (NW->SE, the fall line), u = contour. Orthonormal, so xy<->uf is exact.
        rt = 0.70710678

        def U(px: float, py: float) -> float:
            return rt * (px - py)

        def Ff(px: float, py: float) -> float:
            return rt * (px + py)

        def XY(u: float, f: float) -> Pt:
            return (rt * (u + f), rt * (f - u))

        ex0, ey0, ex1, ey1 = x0 - amp, y0 - amp, x1 + amp, y1 + amp
        ous = [U(px, py) for px, py in smoothed]
        ofs = [Ff(px, py) for px, py in smoothed]
        umin, umax = min(ous) - plot, max(ous) + plot
        fmin, fmax = min(ofs) - plot, max(ofs) + plot
        fhi, flo = min(ofs), max(ofs)  # the field's real high (source) / low (drain) edges
        fh, fd = fhi + plot * 1.4, flo - plot * 1.4  # the MAIN canal (near the high edge) + DRAIN (near the low)

        stt = random.getstate()  # ISOLATE the fill RNG (decorative; must not shift houses)
        random.seed(int(abs(x0) * 7 + abs(y0) * 13 + abs(x1) * 3 + len(name)))

        # LATERALS: strip boundaries in u, spaced 1.4-3.2 plots apart (varied width). Each is a continuous
        # wobbly line down f (so both neighboring strips follow the SAME lateral -> a real ditch, T-junctions).
        # u-grid: plot-wide columns (all wobble down f). Every 2-4 columns carries a LATERAL DITCH; a plot is
        # watered from an adjacent lateral or by cascade from the plot above, so the plots FAR from any lateral
        # (wide-gap middles) and at the field MARGINS are the hard-to-water ground -> dry crops go there.
        ub = [umin]
        while ub[-1] < umax - plot * 0.55:
            ub.append(ub[-1] + plot * random.uniform(0.9, 1.35))
        ub.append(umax)
        phase = [random.uniform(0, 6.28) for _ in ub]

        def uline(i: int, f: float) -> float:
            if i == 0 or i == len(ub) - 1:
                return ub[i]
            return ub[i] + 5.0 * math.sin(f / 66.0 + phase[i]) + 3.0 * math.sin(f / 29.0 + phase[i] * 1.7)

        laterals: list[int] = []
        i = random.randint(1, 2)
        while i < len(ub) - 1:
            laterals.append(i)
            i += random.randint(4, 6)

        self.add(f'<g clip-path="url(#{cid})">')
        self.add(f'<rect x="{ex0:.0f}" y="{ey0:.0f}" width="{ex1 - ex0:.0f}" height="{ey1 - ey0:.0f}" fill="#C2A772"/>')
        interior: list[Any] = []
        ndry, nrice = 0, 0
        for k in range(len(ub) - 1):
            rows = [fmin]
            while rows[-1] < fmax - plot * 0.6:
                rows.append(rows[-1] + plot * random.uniform(0.85, 1.5))
            rows.append(fmax)
            for j in range(len(rows) - 1):
                fa, fb = rows[j], rows[j + 1]
                fm = (fa + fb) / 2
                quad = [XY(uline(k, fa), fa), XY(uline(k + 1, fa), fa), XY(uline(k + 1, fb), fb), XY(uline(k, fb), fb)]
                pts = ' '.join(f'{q[0]:.0f},{q[1]:.0f}' for q in quad)
                cx = sum(q[0] for q in quad) / 4
                cy = sum(q[1] for q in quad) / 4
                edgef = max(0.0, 1.0 - edge_dist(cx, cy, smoothed) / (1.4 * plot))
                un_irrig = fm < fh or fm > fd  # above the main canal / below the drain: gravity can't flood it
                if un_irrig or edgef + random.uniform(-0.08, 0.08) > 0.6:
                    crop = 'dry' if random.random() < 0.62 else 'soy'
                    fill = 'url(#drycrop)' if crop == 'dry' else '#9CB36A'
                    self.add(f'<polygon points="{pts}" fill="{fill}" stroke="#C2A772" stroke-width="{bund:.1f}" stroke-linejoin="round"/>')
                    self._rows(quad, pts, crop)
                    ndry += 1
                else:
                    near_ditch = abs(fm - fh) < plot * 1.4 or abs(fm - fd) < plot * 1.4  # water pools at the canal/drain
                    ro = random.random()
                    if near_ditch and ro < 0.3:
                        fill, flooded = random.choice(FLOODED_SHADES), True
                    elif ro > 0.975:
                        fill, flooded = random.choice(RIPE_SHADES), False
                    else:
                        fill, flooded = random.choice(RICE_GREENS), False
                    self.add(f'<polygon points="{pts}" fill="{fill}" stroke="#C2A772" stroke-width="{bund:.1f}" stroke-linejoin="round"/>')
                    self._paddy_surface(quad, pts, flooded)
                    nrice += 1
                if point_in_poly(cx, cy, smoothed):
                    interior.append((quad, cx, cy))
        if label and taxfree:
            self._taxfree_plots(interior, taxfree)
        self.add('</g>')

        # THE WATER NETWORK, drawn ON TOP and clipped to the field: laterals down the fall line, a head ditch
        # along the high edge, a drain ditch along the low edge - the plots were carved to these, so they align.
        def polyline(pairs: Any, w: float) -> None:
            pts = ' '.join(f'{px:.0f},{py:.0f}' for px, py in pairs)
            self.add(f'<polyline points="{pts}" fill="none" stroke="#9CB4C8" stroke-width="{w}" opacity="0.9" stroke-linejoin="round" stroke-linecap="round"/>')

        def bnd(u: float, lo: float, step: float) -> float | None:  # first f INSIDE the field scanning from lo; None if absent
            f = lo
            while f <= fmax if step > 0 else f >= fmin:
                if point_in_poly(XY(u, f)[0], XY(u, f)[1], smoothed):
                    return f
                f += step
            return None

        def ditch(pairs: Any, w: float, role: str) -> None:  # draw AND record, so the checks can validate it
            polyline(pairs, w)
            self.M["field_ditches"].append({"poly": [[round(px, 1), round(py, 1)] for px, py in pairs], "role": role, "field": name})

        # CONTINUOUS main + drain along the field's true HIGH / LOW boundaries - sampled only where the field
        # actually exists (bnd returns None otherwise), so no junk endpoints jutting outside. Then LATERALS
        # whose ends SNAP onto the nearest main / drain node - so every lateral provably meets both, and the
        # main/drain read as continuous canals (not a sparse dotted line). Paddies between laterals cascade.
        us = [min(ous) + i * 11 for i in range(int((max(ous) - min(ous)) / 11) + 1)] + [max(ous)]
        main_pts: list[Pt] = []
        drain_pts: list[Pt] = []
        for u in us:
            t, bt = bnd(u, fmin, 6), bnd(u, fmax, -6)
            if t is not None and bt is not None and bt - t > plot * 1.4:
                main_pts.append(XY(u, t + plot * 0.7))
                drain_pts.append(XY(u, bt - plot * 0.7))

        def smooth(pts: Poly) -> Poly:  # kill acute turns where the boundary bends sharply
            if len(pts) < 3:
                return pts  # pragma: no cover - defensive: a real field spans many u-columns, so main/drain always have >=3 sampled points
            for _ in range(3):
                pts = [pts[0]] + [((pts[i - 1][0] + pts[i][0] + pts[i + 1][0]) / 3, (pts[i - 1][1] + pts[i][1] + pts[i + 1][1]) / 3) for i in range(1, len(pts) - 1)] + [pts[-1]]
            return pts

        main_pts, drain_pts = smooth(main_pts), smooth(drain_pts)
        self.add(f'<g clip-path="url(#{cid})">')
        if len(main_pts) >= 2:
            ditch(main_pts, 3.3, "main")  # continuous MAIN canal along the high edge
            ditch(drain_pts, 3.0, "drain")  # continuous DRAIN along the low edge
            for li in laterals:
                if not (0 < li < len(ub) - 1):
                    continue  # pragma: no cover - defensive: laterals are built strictly inside (0, len(ub)-1)
                ut = ub[li]
                t, bt = bnd(ut, fmin, 6), bnd(ut, fmax, -6)
                if t is None or bt is None:
                    continue
                tf, bf = t + plot * 0.7, bt - plot * 0.7
                if bf - tf <= plot * 0.7:
                    continue
                mid = [XY(uline(li, f), f) for f in [tf + i * 14 for i in range(1, int((bf - tf) / 14) + 1)] if f < bf]
                ditch([XY(ut, tf)] + mid + [XY(ut, bf)], 2.0, "lateral")  # ends on the continuous main/drain line
        self.add('</g>')
        random.setstate(stt)

        # feed the MAIN at a single point from the pond; empty the DRAIN to the outlet (anchors safely inside).
        safe = [(t[1], t[2]) for t in interior if edge_dist(t[1], t[2], smoothed) >= 14] or [((x0 + x1) / 2, (y0 + y1) / 2)]
        msafe = [q for q in main_pts if edge_dist(q[0], q[1], smoothed) >= 11] or main_pts or safe
        dsafe = [q for q in drain_pts if edge_dist(q[0], q[1], smoothed) >= 11] or drain_pts or safe
        head_pt = min(msafe, key=lambda q: (q[0] - source[0]) ** 2 + (q[1] - source[1]) ** 2)
        drain_pt = min(dsafe, key=lambda q: (q[0] - drain[0]) ** 2 + (q[1] - drain[1]) ** 2)
        self.channel(source, head_pt, {"kind": "pond"}, {"kind": "field", "name": name}, amp=8, width=2.6)
        self.channel(drain_pt, drain, {"kind": "field", "name": name}, drain_anchor or {"kind": "offmap"}, amp=8, width=2.6)

        self.add(f'<path d="{d}" fill="none" stroke="#A98A52" stroke-width="3.5"/>')
        if label:
            lx, ly = label_xy if label_xy else ((x0 + x1) / 2, (y0 + y1) / 2)
            z = self.add_label(
                f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" font-size="15" '
                f'font-weight="bold" fill="#33301E" letter-spacing="1.5" '
                f'paint-order="stroke" stroke="{LAND}" stroke-width="3.5">{label}</text>'
            )
            self._record_label(lx, ly, label, 15, "middle", z)

    def fallow_field(self, bbox: Any, name: str, amp: float = 34) -> None:
        outline = organic_bbox(bbox, amp)
        d = smooth_closed(outline)
        self.add(f'<path d="{d}" fill="url(#fallow)" stroke="#9C7A40" stroke-width="1.8" stroke-dasharray="6,4"/>')
        sm = smooth_points(outline)
        self.M["fields"].append({"name": name, "bbox": list(bbox), "kind": "fallow", "outline": [[x, y] for (x, y) in sm]})
        self.field_polys.append(sm)

    # ---- water
    def pond(self, cx: float, cy: float, rx: float, ry: float, stream_curve: Any = None) -> None:
        """A pond / irrigation reservoir. Routed through the WATER block (not drawn inline) so a stream or
        channel MEETING it JOINS at the rim instead of the rim cutting across its mouth: the RIM is an EDGE
        below every water bed (a feeder's bed covers it at the junction -> a clean gap), the FILL joins the
        shared bed group as the TOPMOST bed (`pond_fill=True`) - so it paints OVER any feeder's inside-the-rim
        overshoot (an irrigation channel's round end-cap bulging past the rim, whichever order it was drawn),
        while the shore rim still shows and the mouths stay clean; the inner highlight is a sheen."""
        if stream_curve:
            # the pond's feeder runs at the lateral/ditch tier - a thin line near the channel weight,
            # NOT the heftier natural-stream weight (see the water-width ladder in settlements.md).
            self._water(f'<path d="{stream_curve}" fill="none" stroke="#9CB4C8" stroke-width="5"/>', {})
        self._water(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#9CB4C8"/>',  # FILL -> shared bed group (topmost bed)
            {},
            sheen=f'<ellipse cx="{cx}" cy="{cy}" rx="{rx - 12}" ry="{ry - 10}" fill="none" stroke="#B6CAD8" stroke-width="1"/>',  # inner highlight
            edge=f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="#5C7488" stroke-width="2.4"/>',  # RIM -> edge layer, below beds
            pond_fill=True,
        )
        self.M["pond"] = [cx, cy, rx, ry]
        self.ellipses.append((cx, cy, rx, ry))

    def draw_comb_field(self, net: dict[str, Any], name: str, source: dict[str, Any]) -> list[Pt]:
        """Draw a `build_comb` net (dry hem + flooded paddies + bunds + channels) AND register the field's
        manifest + water topology, in one call - the ~50 lines every comb gen otherwise repeats inline. Feeds
        the roll-from-seed entrypoint (which cannot hand-place any of it) but is reusable by any comb gen.
        `source` describes where the water comes from: {"kind":"pond", "pond":(cx,cy,rx,ry)} draws a tameike at
        the sluice and feeds from it; {"kind":"stream", "stream":[(x,y),...]} runs a brook in from a canvas edge
        to the sluice. Records the field envelope/bbox/vis_bbox, every channel as a field_ditch, and a hairline
        SOURCE->field feed channel so the water-topology checks (fields_show_water_source, field_ditches_reach_
        source_and_sink) see a source. Returns the field envelope polygon."""
        from waterfields import _RICE_GREEN, BEAN_GREEN, BUND

        # BASE FILL (feature 012): a paddy-green wash over the whole planted extent BEFORE the plots, so the
        # imperfect plot tessellation never lets the parchment background show through as bare "white" gaps -
        # flat wet paddy tiles completely (research.md D5). Filled over the PLOTS' union bbox, NOT the raw
        # envelope, so a nucleated map's harmless phantom tail (the over-declared field_fall the checks let a
        # nucleated cluster carry) stays invisible instead of being painted green.
        pv = [v for p in net["plots"] for v in p["poly"]]
        if pv:
            cid = self._cid("padbase")
            epts = " ".join(f"{x:.1f},{y:.1f}" for x, y in net["envelope"])
            px0, px1 = min(v[0] for v in pv), max(v[0] for v in pv)
            py0, py1 = min(v[1] for v in pv), max(v[1] for v in pv)
            self.add(f'<clipPath id="{cid}"><rect x="{px0:.1f}" y="{py0:.1f}" width="{px1 - px0:.1f}" height="{py1 - py0:.1f}"/></clipPath>')
            self.add(f'<polygon points="{epts}" fill="{_RICE_GREEN}" clip-path="url(#{cid})"/>')

        for p in net["dry_plots"]:  # the dry upslope hem
            pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in p["poly"])
            self.add(f'<polygon points="{pts}" fill="{p["fill"]}" stroke="#A98C58" stroke-width="1.4" stroke-linejoin="round"/>')
            self._draw_furrows(p["poly"], p["furrow"], p["theta"])
            self.M["dry_plots"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in p["poly"]], "crop": p["crop"], "theta": round(p["theta"], 3)})
            self.block_polys.append(p["poly"])  # dry cropland is no-build ground; keep farmsteads off it
        for p in net["plots"]:  # the flooded paddies
            pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in p["poly"])
            self.add(f'<polygon points="{pts}" fill="{p["fill"]}" stroke="{BUND}" stroke-width="2" stroke-linejoin="round"/>')
            # Record the LOW/WET plots (feature 010). This is the topographic ELIGIBILITY set the
            # plot-based land-use overlays draw from. It is written HERE, by the field pass, so that
            # `overlays_on_wet_ground_only` compares two INDEPENDENTLY-produced records rather than
            # reading back the overlay's own self-report - a check that reads one source has no teeth.
            if p.get("low"):
                self.M.setdefault("wet_plots", []).append(_centroid(p["poly"]))
        beads = "".join(f'<circle cx="{x}" cy="{y}" r="1.4" fill="{BEAN_GREEN}"/>' for x, y in net["bund_beans"])
        self.add(f'<g opacity="0.85">{beads}</g>')
        sluice = net["channels"][0]["pts"][0]
        pond_rec: Any = None
        if source.get("kind") == "pond":
            pcx, pcy, prx, pry = source["pond"]
            self.stream([(sluice[0], sluice[1]), (pcx, pcy)], frm={"kind": "offmap"}, to={"kind": "pond"}, width=6) if source.get("feeder") else None
            self.pond(pcx, pcy, prx, pry)
            ring = [(pcx + (prx + 40) * math.cos(a), pcy + (pry + 40) * math.sin(a)) for a in [i * math.pi / 8 for i in range(16)]]
            self.marsh(ring, role="pond_fringe")
            self.block_polys.append([(pcx - prx - 10, pcy - pry - 10), (pcx + prx + 10, pcy - pry - 10), (pcx + prx + 10, pcy + pry + 10), (pcx - prx - 10, pcy + pry + 10)])  # no build on the pond
            pond_rec = (pcx, pcy)
        elif source.get("kind") == "stream" and source.get("stream"):
            # no "stream" polyline = an existing on-map stream already runs at the sluice (the town
            # pattern: the comb taps the map's stream via a weir); nothing extra is drawn, the
            # hairline topology channel below still anchors to that stream
            self.stream(source["stream"], frm={"kind": "offmap"}, width=7)
        for c in sorted(net["channels"], key=lambda c: -c["w"]):
            self.field_channel(c["pts"], "#7C9EB0" if c["role"] == "drain" else "#6C9CBE", c["w"], c.get("w_tail", c["w"]))
        if net["brook"]:
            # the drain-outfall brook shoots STRAIGHT downhill off-map (a fan field's own wiggly brook can
            # re-enter the paddy and trip streams_avoid_fields; a straight downhill exit never does)
            ddb = self.M["meta"].get("down_deg", 90)
            bdx, bdy = math.cos(math.radians(ddb)), math.sin(math.radians(ddb))
            b0 = net["brook"][0]
            b1 = net["brook"][1] if len(net["brook"]) > 1 else (b0[0] + bdx, b0[1] + bdy)
            ex, ey = b1[0] - b0[0], b1[1] - b0[1]  # the drain's own exit direction (smooth junction)
            el = math.hypot(ex, ey) or 1.0
            mid = (b0[0] + ex / el * 70, b0[1] + ey / el * 70)  # a short smooth continuation, THEN turn downhill
            # (first segment = drain direction -> smooth junction; then straight downhill AWAY from the field ->
            # clears a fan envelope's concave lobe without an acute turn, since the drain already runs downhill)
            self.stream([b0, mid, (mid[0] + bdx * 520, mid[1] + bdy * 520)], frm={"kind": "drain"}, to={"kind": "offmap"}, width=8)
        env = [[round(x, 1), round(y, 1)] for x, y in net["envelope"]]
        exs, eys = [p[0] for p in env], [p[1] for p in env]
        pvx = [v[0] for p in net["plots"] for v in p["poly"]]
        pvy = [v[1] for p in net["plots"] for v in p["poly"]]
        # Per-plot [along-fall span, cross-fall span, centroid x, centroid y], so parcel-fabric checks
        # (polder_parcels_vary, polder_parcels_front_water) measure the DRAWN geometry from the manifest
        # rather than trusting a builder self-report.
        ddp = float(self.M["meta"].get("down_deg", 90))
        pdx, pdy = math.cos(math.radians(ddp)), math.sin(math.radians(ddp))
        pdims = []
        for p in net["plots"]:
            al = [vx * pdx + vy * pdy for vx, vy in p["poly"]]
            cr = [vx * pdy - vy * pdx for vx, vy in p["poly"]]
            pcx, pcy = _centroid(p["poly"])
            pdims.append([round(max(al) - min(al), 1), round(max(cr) - min(cr), 1), round(pcx, 1), round(pcy, 1)])
        self.M["fields"].append({"name": name, "kind": "paddy", "outline": env, "bbox": [min(exs), min(eys), max(exs), max(eys)], "vis_bbox": [min(pvx), min(pvy), max(pvx), max(pvy)], "plots": pdims})
        for c in net["channels"]:
            self.M["field_ditches"].append(
                {"poly": [[round(x, 1), round(y, 1)] for x, y in c["pts"]], "role": c["role"], "field": name, "w": round(c["w"], 1), "w_tail": round(c.get("w_tail", c["w"]), 1)}
            )
        # a hairline SOURCE -> field feed carrying the topology (winds a little into the paddy interior). It
        # STARTS at the source (the pond center, or the sluice for a stream) so channel_source_anchored /
        # pond_connected_to_field see it, and carries a gentle perpendicular KINK so channel_winds_gently passes.
        # source kind "cascade" = the field is fed plot-to-plot from an UPSTREAM field (the caller
        # records its own connector channel with to={"kind":"field",...}), so no hairline is added -
        # its frm={"kind":"stream"} anchor would dangle with no stream at the sluice.
        if source.get("kind") != "cascade":
            hr = net["channels"][0]["pts"]
            fork = hr[-1]
            dd = self.M["meta"].get("down_deg", 90)
            dx, dy = math.cos(math.radians(dd)), math.sin(math.radians(dd))
            din = (fork[0] + dx * 70, fork[1] + dy * 70)
            start = pond_rec if pond_rec else (sluice[0], sluice[1])
            frm = {"kind": "pond"} if pond_rec else {"kind": "stream"}
            if not pond_rec:
                # snap the intake's START onto the nearest stream centerline (within the 30px anchor
                # band): an offtake JOINS its stream at a confluence like any junction - the symmetric
                # case of the drain-culvert rule (channels_join_streams_at_confluence) - rather than
                # beginning in the grass beside it. A comb fed by its OWN feeder brook ending AT the
                # sluice is already joined (distance ~0) and is left alone.
                nearest: Any = None
                for st_ in self.M.get("streams", []):
                    sp_ = st_["poly"]
                    for si_ in range(len(sp_) - 1):
                        fq = seg_closest(start[0], start[1], sp_[si_], sp_[si_ + 1])
                        dq = math.hypot(start[0] - fq[0], start[1] - fq[1])
                        if nearest is None or dq < nearest[0]:
                            nearest = (dq, fq)
                if nearest and 0.5 < nearest[0] <= 30:
                    start = nearest[1]
            vx, vy = din[0] - start[0], din[1] - start[1]
            vl = math.hypot(vx, vy) or 1.0
            midx, midy = (start[0] + din[0]) / 2 - vy / vl * 20, (start[1] + din[1]) / 2 + vx / vl * 20
            self.M["channels"].append(
                {
                    "poly": [[round(start[0], 1), round(start[1], 1)], [round(midx, 1), round(midy, 1)], [round(din[0], 1), round(din[1], 1)]],
                    "frm": frm,
                    "to": {"kind": "field", "name": name},
                    "w": 2.5,
                }
            )
        self._paddy_features(net)
        return cast("list[Pt]", net["envelope"])

    # ---- feature 012: deliberate non-rice features the paddy tiles around --------------------------------
    # Placed automatically from the field geometry per the ARCHETYPE MATRIX (specs/012-.../research.md). Only
    # the genuinely NEW in-field glyphs live here - a low-pocket POND, a bedrock ROCK outcrop, and (a disclosed
    # CALIBRATED LIBERTY the GM approved) a rare in-field GRAVE island. The matrix's MARGIN graves + feng-shui
    # knolls are already the village burial ground + back-grove (the research warns a standalone knoll usually
    # IS the back-grove), so they are not redrawn here. Seeded from self.seed so it never ripples other RNG.
    _PADDY_POND_KINDS = ("valley_paddy", "contour_terraces", "polder_grid", "ribbon_valley")
    _PADDY_ROCK_KINDS = ("contour_terraces", "ribbon_valley")  # bedrock ground; alluvial valley/polder + delta dike-pond have none
    _PADDY_GRAVE_KINDS = ("valley_paddy", "contour_terraces", "ribbon_valley")

    def _paddy_features(self, net: dict[str, Any]) -> None:
        if self.M.get("meta", {}).get("scale") in ("town", "city"):
            # the in-field flourishes (low-pocket pond, rock outcrop, rare grave island) are VILLAGE-scale
            # features from the feature-012 archetype matrix. On a town/city map the combs are a SLICE of
            # county farmland, and at the 1 ft/px grain the glyphs read literally - the GM read the grave
            # island as a pauper ossuary on the paddy and the pocket pond as a pond overlapping the rice
            # (Hoshizora, 2026-07) - so a town/city comb stays plain.
            return
        arch = self.M.get("meta", {}).get("field_archetype") or "valley_paddy"
        if arch == "mulberry_dike_fishpond":
            return  # open water IS its fabric - no obstacle tiles among it (research D4)
        rng = random.Random((self.seed ^ 0x9AD1) & 0xFFFFFFFF)
        plots = net["plots"]
        if not plots:  # pragma: no cover - a drawn field always has plots
            return
        low = [p for p in plots if p.get("low")]
        # POND: a low pocket held as open water (research D4). ~55% of eligible fields carry one.
        if arch in self._PADDY_POND_KINDS and low and rng.random() < 0.55:
            self._plot_pond(rng.choice(low))
        # ROCK: bedrock outcrops the risers/bunds wrap around (research D3) - terraces always, ribbon ~half.
        if arch == "contour_terraces" or (arch == "ribbon_valley" and rng.random() < 0.5):
            for _ in range(rng.randint(1, 3)):
                self._plot_rock(rng.choice(plots), rng)
        # GRAVE ISLAND: calibrated liberty (GM 2026-07-20), RARE - the "graves among the paddy" look.
        if arch in self._PADDY_GRAVE_KINDS and rng.random() < 0.3:
            self._plot_grave_island(rng.choice(plots), rng)

    @staticmethod
    def _plot_center_span(poly: Sequence[Pt]) -> tuple[float, float, float, float]:
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        return (sum(xs) / len(xs), sum(ys) / len(ys), (max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2)

    def _plot_pond(self, plot: dict[str, Any]) -> None:
        """A small OPEN-WATER pond sunk into one low plot - a low pocket / header tameike the paddy rings.
        Distinct from the reed/lotus BOG (blue-green, choked) and from the main village reservoir at the
        source. Drawn OVER the plot (so it carries no bund grid) with a reed fringe; recorded in M['field_ponds']."""
        cx, cy, hx, hy = self._plot_center_span(plot["poly"])
        # capped so a wide TERRACE band gives a POND, not a field-spanning lake (a low pocket, not a reservoir)
        rx, ry = min(max(10.0, hx * 0.82), 46.0), min(max(7.0, hy * 0.82), 32.0)
        self.add(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="#9CB4C8" stroke="#5C7488" stroke-width="1.8"/>')
        self.add(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx - 5:.1f}" ry="{ry - 4:.1f}" fill="none" stroke="#B6CAD8" stroke-width="0.9"/>')
        reeds = "".join(
            f'<line x1="{cx + rx * math.cos(a):.1f}" y1="{cy + ry * math.sin(a):.1f}" x2="{cx + rx * math.cos(a):.1f}" y2="{cy + ry * math.sin(a) - 5:.1f}" stroke="#7C9A4E" stroke-width="1.1"/>'
            for a in [i * math.pi / 4 for i in range(8)]
        )
        self.add(f'<g opacity="0.8">{reeds}</g>')
        self.M.setdefault("field_ponds", []).append({"x": round(cx, 1), "y": round(cy, 1), "rx": round(rx, 1), "ry": round(ry, 1)})

    def _plot_rock(self, plot: dict[str, Any], rng: random.Random) -> None:
        """A bedrock OUTCROP the terrace risers wrap around - a cluster of grey boulders. Recorded in
        M['field_rocks']. Small (a few plot-fractions), off-center so it reads as a natural obstacle."""
        cx, cy, hx, hy = self._plot_center_span(plot["poly"])
        cx += rng.uniform(-hx * 0.3, hx * 0.3)
        cy += rng.uniform(-hy * 0.3, hy * 0.3)
        boulders = ""
        for _ in range(rng.randint(2, 4)):
            bx, by = cx + rng.uniform(-7, 7), cy + rng.uniform(-5, 5)
            r = rng.uniform(3.5, 6.5)
            boulders += f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="{r:.1f}" fill="#9C948A" stroke="#5C544A" stroke-width="1"/>'
            boulders += f'<path d="M{bx - r * 0.5:.1f},{by - r * 0.2:.1f} q{r * 0.4:.1f},{-r * 0.5:.1f} {r:.1f},{-r * 0.1:.1f}" fill="none" stroke="#C6BEB2" stroke-width="0.8"/>'  # a lit crown
        self.add(f'<g>{boulders}</g>')
        self.M.setdefault("field_rocks", []).append({"x": round(cx, 1), "y": round(cy, 1)})

    def _plot_grave_island(self, plot: dict[str, Any], rng: random.Random) -> None:
        """A RARE in-field grave island (calibrated liberty) - a small raised earthen mound with a couple of
        stone markers, the flat paddy tiling around it. Recorded in M['field_graves']."""
        cx, cy, hx, hy = self._plot_center_span(plot["poly"])
        rx, ry = max(9.0, hx * 0.55), max(6.0, hy * 0.55)
        self.add(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="#CFC6B4" stroke="#8C8470" stroke-width="1.2" opacity="0.9"/>')
        markers = ""
        for i in range(rng.randint(2, 3)):
            mx = cx + (i - 1) * 6
            markers += f'<rect x="{mx - 1.3:.1f}" y="{cy - 7:.1f}" width="2.6" height="7" rx="1" fill="#9AA1A4" stroke="#5A584F" stroke-width="0.5"/>'
        self.add(f'<g>{markers}</g>')
        self.M.setdefault("field_graves", []).append({"x": round(cx, 1), "y": round(cy, 1)})

    def apply_land_use(self, net: dict[str, Any], overlay: str, rng: random.Random, fraction: float = 0.55, eligible: str = "wet") -> int:
        """Overlay a LAND-USE archetype (feature 005 US4 `land_use_overlay`) onto an already-drawn comb field:
        recolor a FRACTION of the paddy plots (or, for tea, a hill-margin fringe) as the overlay crop, so a
        village growing mulberry-and-fishpond, lotus, or hill-tea reads distinctly from a plain-rice one.
        Records M['land_use'] + meta.land_use_overlay. Returns the number of plots/rows overlaid.

        GROUNDING (feature 010 research.md, China-first). Every value obeys ONE two-term rule:

            TOPOGRAPHY sets which plots are ELIGIBLE; ECONOMY decides how many of them CONVERT.

        The original implementation had only the second term (this `fraction`, applied by uniform random
        sample over ALL plots) and no topographic filter at all - so it drew ponds and lotus on ordinary
        upper-field rice ground. `fraction` now applies to the ELIGIBLE set:

        - `mulberry_fishpond` (桑基魚塘): dug out of 低洼易有洪患之处, the low flood-prone hollows - a
          flood adaptation that drained the hollow while raising the dike. Eligible = FLOODED plots, and
          CLUSTERED (see `_pick_overlay_plots`). NOTE this value was very nearly deleted on the false
          premise that the dike-pond system was only ever a whole-landscape conversion; in fact a scatter
          among rice was its NORMAL state (Shunde county ~4.6% dike-pond in 1581; at Lake Tai mulberry sat
          on the tang banks with rice remaining the polder's main crop permanently). The wall-to-wall
          landscape is the rare end state, which is what the `mulberry_dike_fishpond` ARCHETYPE is for.
          Do not delete this value; the two are different scales of the same system, not duplicates.
        CALIBRATED LIBERTY (constitution XII, GM 2026-07-19) - disclosed, not hidden. Eligibility keys off
        the plot's `low` flag, and `low` is the bottom TWO levels of each field sector rather than only the
        one hemming the drain. Two things drove that. (1) Correctness: `FLOODED` is a random 45% tint over
        the bottom level for visual texture, so keying off it made eligibility an accident of RENDERING.
        (2) A liberty: how wide a valley bottom's wet backswamp ran is not recorded, and the research puts a
        lotus-growing village anywhere from a few percent to ~10-15% of field area - itself an interpolation,
        the weakest number in that report. Binding to the single drain-side hem put lotus at ~2%, technically
        inside the range but so sparse the knob stopped doing its job of making villages look distinct. We
        therefore chose the UPPER part of a plausible range for a stated non-historical reason (legibility).
        What this does NOT do is invent a range: lotus stays on genuinely low ground, and the overlay still
        cannot touch the upper field.

        - `lotus` (藕田): models DEEP-WATER lotus (深水藕, 30-50cm, tolerating ~1m) against paddy rice's
          ~5-9cm optimum - it physically cannot sit on high ground, so eligible = FLOODED plots. Shallow-
          water lotus (浅水藕) in ordinary paddy is real but is NOT modeled: it is an economic choice
          rotating with rice, and drawing it would be indistinguishable from the uniform-random bug this
          replaced. See research.md D1 before "restoring" it.
        - `tea_fringe` (茶): unchanged - already correct. Tea took the LOWER-to-mid FERTILE hillside, never
          the low lands and never the barren upper slope (Fortune, 1843). The boundary rule is exactly
          "the line is the highest irrigation ditch", which is what `net['dry_plots']` already is.
          Two anachronisms to avoid: neat contour-TERRACED tea is post-1949 (terrace the paddy, not the
          tea), and bund-margin tea (畦畔茶) is a JAPANESE practice with no Chinese equivalent.
        - `rape` (油菜): REMOVED and must not return. Rice and rape are two halves of ONE seasonally-
          synchronized rotation in the SAME plot, so they are never both standing - at any percentage and
          in any pattern. Do not re-add it here."""
        if overlay not in ("none", "mulberry_fishpond", "lotus", "tea_fringe"):
            raise ValueError(f"unknown land_use_overlay {overlay!r}")
        self.M["meta"]["land_use_overlay"] = overlay
        if overlay == "none":
            self.M.setdefault("land_use", []).append({"overlay": "none", "count": 0})
            return 0
        plots = list(net["plots"])
        n = 0
        if overlay == "tea_fringe":  # tea BUSH rows along the field's dry HIGH margin (not plot-based)
            for dp in net["dry_plots"]:
                pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in dp["poly"])
                cid = self._cid("tea")
                self.add(f'<clipPath id="{cid}"><polygon points="{pts}"/></clipPath>')
                xs = [p[0] for p in dp["poly"]]
                ys = [p[1] for p in dp["poly"]]
                rows = "".join(
                    f'<line x1="{min(xs):.1f}" y1="{y:.1f}" x2="{max(xs):.1f}" y2="{y:.1f}" stroke="#5C7A3E" stroke-width="2.4" opacity="0.75"/>'
                    for y in [min(ys) + 6 + i * 8 for i in range(int((max(ys) - min(ys)) / 8))]
                )
                self.add(f'<g clip-path="url(#{cid})">{rows}</g>')
                n += 1
            self.M.setdefault("land_use", []).append({"overlay": overlay, "count": n})
            return n
        colors = {"mulberry_fishpond": "#93B7AC", "lotus": "#8FA9A0"}
        # TOPOGRAPHIC FILTER (feature 010). Eligibility is the LOW/WET ground, never the whole field.
        # `fraction` is the ECONOMIC term and applies to the eligible set, not to all plots.
        # `eligible="all"` is the WHOLESALE-CONVERSION escape hatch, used by the mulberry_dike_fishpond
        # ARCHETYPE. At that scale the ponds really have engulfed the ordinary ground too - Shunde county
        # went from ~4.6% dike-pond in 1581 to rice under one-tenth of land by c. 1900 on the same terrain.
        # It is a deliberate, named opt-out, NOT the default, because the mixed patchwork is the norm.
        elig = list(plots) if eligible == "all" else [p for p in plots if p.get("low")]
        # `fraction` is the ECONOMIC term: the share of the ELIGIBLE ground that actually converted, NOT a
        # share of the whole field. Keeping it a share of the field made it inert - the eligible set is
        # always smaller than fraction*all, so every village converted 100% of its low ground and the
        # economic term decided nothing. As a share of eligible it varies independently of topography,
        # which is the whole point: Shunde was ~5% dike-pond county-wide while containing townships past
        # 50% the same year, on identical terrain.
        take = min(len(elig), max(2, round(len(elig) * fraction)))
        chosen = self._pick_overlay_plots(elig, take, clustered=(overlay == "mulberry_fishpond" and eligible != "all"), rng=rng)
        for p in chosen:
            pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in p["poly"])
            self.add(f'<polygon points="{pts}" fill="{colors[overlay]}" stroke="#6C9CBE" stroke-width="1.6" stroke-linejoin="round"/>')
            cx = sum(v[0] for v in p["poly"]) / len(p["poly"])
            cy = sum(v[1] for v in p["poly"]) / len(p["poly"])
            if overlay == "mulberry_fishpond":  # a green mulberry DIKE rim around the fish pond
                self.add(f'<polygon points="{pts}" fill="none" stroke="#6E8B4A" stroke-width="3" stroke-linejoin="round" opacity="0.8"/>')
            elif overlay == "lotus":  # a few lily pads / blooms
                self.add("".join(f'<circle cx="{cx + rng.uniform(-14, 14):.1f}" cy="{cy + rng.uniform(-10, 10):.1f}" r="{rng.uniform(2.5, 4):.1f}" fill="#C98BA6" opacity="0.85"/>' for _ in range(3)))
            n += 1
        self.M.setdefault("land_use", []).append({"overlay": overlay, "count": n, "eligible": eligible, "plots": [_centroid(p["poly"]) for p in chosen]})
        return n

    @staticmethod
    def _pick_overlay_plots(eligible: list[Any], take: int, clustered: bool, rng: random.Random) -> list[Any]:
        """Choose which eligible plots convert.

        CLUSTERED (the dike-pond case): grow PATCHES from a few seed plots outward by nearest-neighbor.
        The 桑基魚塘 conversion was 挖塘培基 - dig one low plot into a pond, pile the spoil into a dike
        around it - a single-plot job one household did in one dry season. It therefore spread as a
        patchwork radiating from where someone started, not as an even sprinkle over the district.
        (research.md D2; Shunde grew 40,084 -> 58,094 mu over 61 years, plot by plot.)

        UNCLUSTERED (lotus): the wet bottom is already contiguous by nature, so an even draw from the
        eligible set lands contiguously without extra help.
        """
        if take >= len(eligible):
            return list(eligible)
        if not clustered:
            return rng.sample(eligible, take)
        cents = [_centroid(p["poly"]) for p in eligible]
        n_seeds = max(1, round(take / 9))  # a handful of households started digging, not everyone at once
        picked = set(rng.sample(range(len(eligible)), min(n_seeds, len(eligible))))
        while len(picked) < take:
            # grow the patch: take the unpicked plot nearest to anything already converted
            best = min(
                (i for i in range(len(eligible)) if i not in picked),
                key=lambda i: min(math.dist(cents[i], cents[j]) for j in picked),
            )
            picked.add(best)
        return [eligible[i] for i in sorted(picked)]

    def _draw_furrows(self, poly: Any, color: str, theta: float) -> None:
        """Stylised ridge/furrow lines within a dry-field plot (dry crops are row-cultivated)."""
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        diag = math.hypot(max(xs) - min(xs), max(ys) - min(ys))
        dx, dy = math.cos(theta), math.sin(theta)
        nx, ny = -dy, dx
        cid = self._cid("dry")
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in poly)
        g = [f'<clipPath id="{cid}"><polygon points="{pts}"/></clipPath>', f'<g clip-path="url(#{cid})">']
        t = -diag / 2
        while t <= diag / 2:
            mx, my = cx + nx * t, cy + ny * t
            g.append(
                f'<line x1="{mx - dx * diag / 2:.1f}" y1="{my - dy * diag / 2:.1f}" x2="{mx + dx * diag / 2:.1f}" y2="{my + dy * diag / 2:.1f}" stroke="{color}" stroke-width="0.8" opacity="0.8"/>'
            )
            t += 5
        g.append("</g>")
        self.add("".join(g))

    def crescent_pond(self, cx: float, cy: float, r: float, facing_deg: float = 270.0) -> None:
        """A fengshui CRESCENT / half-moon pond (半月塘), a focal feature of Huizhou / Hakka single-lineage
        villages (feature 005): a half-disk of water IN FRONT of the cluster, its flat diameter facing the
        houses and the arc bulging away, DISTINCT from the irrigation pond.

        WHAT IT IS (GM asked, 2026-07-21 - labeled "geomantic pond" at his direction): GEOMANTIC, not
        religious - no deity, no rites; cosmological engineering, the same category as orienting a house
        south. The village wants "mountain behind, water in front" (背山面水): the back half is the hill +
        fengshui grove (the windbreak belt these maps already draw), and where no river obliges, the village
        DIGS the front half. Still water gathers and holds qi/wealth where flowing water carries it away;
        the HALF shape leaves the lineage room to grow (a full circle is complete, and what is complete can
        only wane). Grove-arc behind + water-arc in front cradle the village as ONE system. It also earns
        its keep practically - roof/yard runoff retention (hence UNCONNECTED to the irrigation network: it
        is rain-fed by design), fire water beside thatch, fish/ducks/washing, and the flat-side bank doubles
        as the open threshing/ceremony forecourt. The shrine is where religion happens; this is just how a
        well-sited village should be shaped.

        `facing_deg` is the screen direction the FLAT edge faces (toward the village); default 270 = up / N.
        Draws through the shared water block (so it composites cleanly), records the footprint + the
        `crescent_pond` focal feature on the manifest, and reserves a placement keep-out - so call it BEFORE
        `farmsteads()` and the cluster packs around it."""
        fa = math.radians(facing_deg)
        fx, fy = math.cos(fa), math.sin(fa)  # unit vector toward the village (the flat side)
        perp = (-fy, fx)  # along the flat diameter
        n = 26
        pts = []
        for i in range(n + 1):
            t = math.pi * i / n  # sweep the arc across the diameter, bulging AWAY from the village
            px = cx + r * (math.cos(t) * perp[0] - math.sin(t) * fx)
            py = cy + r * (math.cos(t) * perp[1] - math.sin(t) * fy)
            pts.append((round(px, 1), round(py, 1)))
        poly = " ".join(f"{x},{y}" for x, y in pts)
        self._water(
            f'<polygon points="{poly}" fill="#9CB4C8"/>',
            {},
            sheen=f'<polygon points="{poly}" fill="none" stroke="#B6CAD8" stroke-width="1" opacity="0.6"/>',
            edge=f'<polygon points="{poly}" fill="none" stroke="#5C7488" stroke-width="2.4"/>',
            pond_fill=True,
        )
        self.M.setdefault("crescent_ponds", []).append({"cx": cx, "cy": cy, "r": r, "facing": facing_deg, "poly": [[x, y] for x, y in pts]})
        self.note_focal("crescent_pond")
        # keep-out over the bulge half-disk (its centroid sits ~0.42r off center, away from the village)
        self.ellipses.append((cx - fx * r * 0.45, cy - fy * r * 0.45, r * 0.95, r * 0.95))
        # LABELED (GM 2026-07-21): the pond is a culturally specific feature that does not read by
        # itself (the GM asked "what is that?" of an unlabeled one - the don't-label-the-obvious rule cuts the
        # OTHER way here). Placed off the arc side, away from the village (crescent_pond_labeled gates it).
        self.label(cx - fx * (r + 16), cy - fy * (r + 16) + 4, "geomantic pond", 11, italic=True, color="#4C6478")

    def note_focal(self, kind: str) -> None:
        """Record an optional FOCAL feature (feature 005 catalog) on the manifest so the twin-detector reads
        it as a distinctiveness axis (meta.focal_features). Call it for a focus DRAWN via an existing method -
        a secondary shrine via `shrine_hall(primary=False)`, an ancestral hall, a market clearing - as well as
        from the dedicated focal methods (`crescent_pond`, `mill`). Idempotent per kind."""
        foc = self.M["meta"].setdefault("focal_features", [])
        if kind not in foc:
            foc.append(kind)

    def mill(self, x: float, y: float, wheel_side: str = "E", w: float = 30, h: float = 24) -> None:
        """A water MILL (水磨 / 水車), a focal feature: a small mill house with an undershot WATERWHEEL on its
        watercourse side, for hulling/grinding. Place it BESIDE a watercourse with fall (a drain outfall or a
        stream), never on still pond water. `wheel_side` (N/E/S/W) is the side the wheel faces the water. Draws
        the house + wheel, records the footprint (M['mills']) + the `mill` focal feature, and reserves the
        footprint as a placement keep-out (call it before `farmsteads()` if the cluster could reach it)."""
        pw, ph = self.px(w), self.px(h)
        dx, dy = {"E": (1.0, 0.0), "W": (-1.0, 0.0), "N": (0.0, -1.0), "S": (0.0, 1.0)}[wheel_side]
        self.add(f'<rect x="{x - pw / 2:.1f}" y="{y - ph / 2:.1f}" width="{pw:.1f}" height="{ph:.1f}" fill="#C9A57A" stroke="#6B4F2A" stroke-width="2" rx="2"/>')
        self.add(f'<line x1="{x - pw / 2:.1f}" y1="{y:.1f}" x2="{x + pw / 2:.1f}" y2="{y:.1f}" stroke="#6B4F2A" stroke-width="1" opacity="0.6"/>')  # ridge line
        wx, wy = x + dx * (pw / 2 + self.px(5)), y + dy * (ph / 2 + self.px(5))  # waterwheel center, on the water side
        wr = self.px(9)
        spokes = "".join(
            f'<line x1="{wx:.1f}" y1="{wy:.1f}" x2="{wx + wr * math.cos(a):.1f}" y2="{wy + wr * math.sin(a):.1f}" stroke="#5A3F1E" stroke-width="1"/>' for a in [i * math.pi / 4 for i in range(8)]
        )
        self.add(f'<circle cx="{wx:.1f}" cy="{wy:.1f}" r="{wr:.1f}" fill="none" stroke="#5A3F1E" stroke-width="1.8"/>{spokes}')
        self.M.setdefault("mills", []).append({"x": round(x, 1), "y": round(y, 1), "w": pw, "h": ph, "rot": 0})
        self.note_focal("mill")
        self.placed.append((x, y, pw, ph))

    def _focal_block(self, x: float, y: float, pw: float, ph: float) -> None:
        """Reserve a focal footprint as a placement keep-out (so a later farmstead can never overlap it)."""
        self.placed.append((x, y, pw, ph))
        self.block_polys.append([(x - pw / 2 - 6, y - ph / 2 - 6), (x + pw / 2 + 6, y - ph / 2 - 6), (x + pw / 2 + 6, y + ph / 2 + 6), (x - pw / 2 - 6, y + ph / 2 + 6)])

    def ancestral_hall(self, x: float, y: float, w: float = 110, h: float = 74) -> None:
        """A lineage ANCESTRAL HALL (祠堂), a focal feature: the grandest civic building of a single-lineage
        village - broader than any house, a double-eave hall on the auspicious axis fronting the pond/water.
        Draws the hall, records M['ancestral_halls'] + the focal feature, reserves the footprint. Grounding
        (research.md D2): the ancestral hall was the ritual + governance center of a Huizhou/Hakka lineage
        village, its single most prominent structure - so a village that HAS one reads unmistakably by it."""
        pw, ph = self.px(w), self.px(h)
        self.add(f'<rect x="{x - pw / 2:.1f}" y="{y - ph / 2:.1f}" width="{pw:.1f}" height="{ph:.1f}" fill="#DDB87A" stroke="#5A3F1E" stroke-width="2.4" rx="2"/>')
        self.add(
            f'<rect x="{x - pw / 2 + self.px(5):.1f}" y="{y - ph / 2 + self.px(5):.1f}" width="{pw - self.px(10):.1f}" height="{ph - self.px(10):.1f}" fill="none" stroke="#6B4F2A" stroke-width="1.2"/>'
        )  # inner eave
        self.add(f'<rect x="{x - self.px(9):.1f}" y="{y + ph / 2 - self.px(4):.1f}" width="{self.px(18):.1f}" height="{self.px(6):.1f}" fill="#5A3F1E"/>')  # entry porch on the water side
        self.M.setdefault("ancestral_halls", []).append({"x": round(x, 1), "y": round(y, 1), "w": pw, "h": ph, "rot": 0})
        self.note_focal("ancestral_hall")
        self._focal_block(x, y, pw, ph)

    def water_mouth(self, x: float, y: float, r: float = 22) -> None:
        """A fengshui WATER-MOUTH complex (水口), a focal feature: the guarded outlet where the village stream
        leaves, marked by a small hexagonal pavilion (and, per the gen, a screening grove) to 'lock in' the qi
        of the departing water. Draws the pavilion, records M['water_mouths'] + the focal feature. Grounding:
        the shuikou was a standard focal ensemble of south-China lineage villages, sited at the stream exit."""
        pr = self.px(r)
        pts = " ".join(f"{x + pr * math.cos(a):.1f},{y + pr * math.sin(a):.1f}" for a in [math.pi / 6 + i * math.pi / 3 for i in range(6)])
        self.add(f'<polygon points="{pts}" fill="#C9876C" stroke="#6B2A18" stroke-width="2" stroke-linejoin="round"/>')
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{pr * 0.42:.1f}" fill="none" stroke="#6B2A18" stroke-width="1.2"/>')
        self.M.setdefault("water_mouths", []).append({"x": round(x, 1), "y": round(y, 1), "w": pr * 2, "h": pr * 2, "rot": 0})
        self.note_focal("water_mouth")
        self._focal_block(x, y, pr * 2, pr * 2)

    def market(self, x: float, y: float, w: float = 120, h: float = 84) -> None:
        """A village MARKET clearing (墟/市), a focal feature: an open packed-earth space with a few stalls
        where a periodic market gathers - a widening in the lane fabric, not a building. Draws the open court +
        a row of stall marks, records M['markets'] + the focal feature. Grounding: a market node is exactly
        where a `cross` lane skeleton reads as a market village rather than a plain farming one."""
        pw, ph = self.px(w), self.px(h)
        cid = self._cid("mkt")
        self.add(f'<clipPath id="{cid}"><rect x="{x - pw / 2:.1f}" y="{y - ph / 2:.1f}" width="{pw:.1f}" height="{ph:.1f}" rx="3"/></clipPath>')
        self.add(f'<rect x="{x - pw / 2:.1f}" y="{y - ph / 2:.1f}" width="{pw:.1f}" height="{ph:.1f}" fill="#D8C7A0" stroke="#9C7A40" stroke-width="1.6" stroke-dasharray="5 4" rx="3"/>')
        stalls = "".join(
            f'<rect x="{x - pw / 2 + self.px(10) + i * self.px(22):.1f}" y="{y - self.px(6):.1f}" width="{self.px(14):.1f}" height="{self.px(12):.1f}" fill="#C9A57A" stroke="#6B4F2A" stroke-width="1"/>'
            for i in range(max(1, int(w / 34)))
        )
        self.add(f'<g clip-path="url(#{cid})">{stalls}</g>')
        self.M.setdefault("markets", []).append({"x": round(x, 1), "y": round(y, 1), "w": pw, "h": ph, "rot": 0})
        self.note_focal("market")
        self._focal_block(x, y, pw, ph)

    def secondary_shrine(self, x: float, y: float, w_ft: float = 42, h_ft: float = 30) -> None:
        """A SECONDARY tutelary/roadside shrine, a focal feature: a small second shrine besides the village's
        main one (a Benten by the pond, an Inari at a field corner). Records as a 'shrine' kind (so
        religious_matches_scale still sees only shrines) + the focal feature. Grounding: a village often kept a
        minor shrine in addition to its tutelary one; its PRESENCE + placement is a distinctiveness axis.
        TRUE SCALE: dimensions are real feet (a minor wayside hall ~42x30 ft, smaller than the tutelary)."""
        self.shrine(x, y, w_ft, h_ft, kind="shrine")
        self.note_focal("secondary_shrine")

    def stream(self, pts: Any, frm: Any = None, to: Any = None, width: float = 9) -> None:
        """A natural watercourse. If frm/to anchors are given (e.g. a forest brook
        feeding a pond), it is recorded and the gate checks it actually connects
        them - just like an irrigation channel. `width` is the water's drawn width
        (a stream FEEDING A MOAT should be as wide as the moat, by conservation of flow)."""
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
        # always recorded so the gate can check it (anchors optional - only some streams connect things)
        rec = {"poly": [[x, y] for x, y in pts], "frm": frm, "to": to, "w": width}
        self.M["streams"].append(rec)
        bed_t = f'<path d="{{dd}}" fill="none" stroke="#9CB4C8" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>'
        # lighter mid-current highlight (NOT a dashed lane line - this is water, not a road)
        sheen_t = f'<path d="{{dd}}" fill="none" stroke="#B6CAD8" stroke-width="{max(2, width * 0.35):.0f}" stroke-linejoin="round" stroke-linecap="round"/>'
        clip = {"pts": [(x, y) for x, y in pts], "bed_t": bed_t, "sheen_t": sheen_t} if self._pond_anchored(frm, to) else None
        self._water(  # opacity comes from the shared bed/sheen groups, so crossings don't stack into a dark seam
            bed_t.format(dd=dd), rec, sheen=sheen_t.format(dd=dd), clip=clip
        )
        self.corridors.append(([(x, y) for x, y in pts], max(30, width / 2 + 20)))  # no-build: keep houses off the stream

    def river(self, pts: Any, width: float | None = None) -> float:
        """A RIVER - the trunk waterway a river-bank city sits on (most provincial cities do;
        the moat taps it upstream and returns downstream, and the river itself serves as the
        water defense on its flank - Xiangyang/Pingyao/Okayama pattern, see settlements.md).
        Drawn as a wide stream (off-map to off-map) and recorded in M['river'] so the checks
        that compare watercourse weights know this one legitimately outweighs the dug moat."""
        if width is None:
            width = self.px(120)  # a serious provincial river ~120 ft across
        self.stream(pts, frm={"kind": "offmap"}, to={"kind": "offmap"}, width=width)
        self.M["river"] = {"pts": [[x, y] for x, y in pts], "w": width}
        return width

    def channel(self, start: Any, end: Any, frm: Any, to: Any, amp: float = 15, width: float = 2.5, pts: Any = None) -> None:
        """frm/to are anchor dicts: {'kind':'pond'|'offmap'|'field','name':...}. `width` is the drawn
        bed: a field-level irrigation ditch is the THINNEST line on the map (in reality ~0.3 m, ~1/300
        of the 1-cho paddy it feeds), so it sits at the legibility floor (~2.5 px) - a hairline, clearly
        finer than any natural watercourse. See the water-width ladder in settlements.md historical
        grounding. `pts` (optional): an explicit polyline used verbatim instead of the auto-winding -
        for culverts routed by hand (a drain outfall reaching its stream confluence, a field-to-field
        cascade connector) whose waypoints are load-bearing; drawing through THIS method (not a flat
        field_channel stroke) is what puts the bed in the shared water group at the standard bed hue,
        so the mouth merges into the receiving stream like any confluence (GM, Hirameki 2026-07)."""
        poly = [(p[0], p[1]) for p in pts] if pts else winding(start, end, amp=amp)
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in poly)
        rec = {"poly": [[x, y] for x, y in poly], "frm": frm, "to": to, "w": width}
        self.M["channels"].append(rec)
        bed_t = f'<path d="{{dd}}" fill="none" stroke="#9CB4C8" stroke-width="{width}"/>'  # a channel is a thin bed, no sheen
        clip = {"pts": [(x, y) for x, y in poly], "bed_t": bed_t, "sheen_t": None} if self._pond_anchored(frm, to) else None
        self._water(bed_t.format(dd=dd), rec, clip=clip)
        # 33 px keeps even a plain farmhouse's FOOTPRINT (half-diagonal ~26) clear of the
        # channel, not just its center - 22 left corners clipping the channel (see
        # no_structure_on_channel). Matches the stream corridor's footprint-aware spacing.
        self.corridors.append((poly, 33))

    def _clip_to_pond(self, pts: Any) -> Any:
        """Snap a channel's leading endpoint ONTO the pond rim - trim a run that lies inside the pond, or
        extend one that sits just outside (the sluice foot) - so its bed straddles the rim and COVERS it at
        the mouth: a clean JOIN, without the channel drawing a colored line across the open water. No-op
        when there is no pond. (The rim renders in the water EDGE layer, below every bed, so the covering
        works.)"""
        p = self.M.get("pond")
        if not p:
            return pts
        ex, ey, erx, ery = p

        def rad(q: Pt) -> float:
            return cast(float, ((q[0] - ex) / erx) ** 2 + ((q[1] - ey) / ery) ** 2)  # <1 inside, 1 on the rim, >1 outside

        def rim(inside_pt: Pt, outside_pt: Pt) -> Pt:  # the rad==1 crossing on the segment
            lo, hi = 0.0, 1.0
            for _ in range(24):
                m = (lo + hi) / 2
                q = (inside_pt[0] + (outside_pt[0] - inside_pt[0]) * m, inside_pt[1] + (outside_pt[1] - inside_pt[1]) * m)
                lo, hi = (m, hi) if rad(q) < 1.0 else (lo, m)
            return (inside_pt[0] + (outside_pt[0] - inside_pt[0]) * hi, inside_pt[1] + (outside_pt[1] - inside_pt[1]) * hi)

        def snap_front(seq: Any) -> list[Any]:  # snap a leading endpoint that connects to the pond onto the rim
            out = list(seq)
            if rad(out[0]) < 1.0:  # inside: drop the run inside the pond, start AT the rim
                i = 0
                while i + 1 < len(out) and rad(out[i + 1]) < 1.0:
                    i += 1
                if i + 1 < len(out):
                    out = [rim(out[i], out[i + 1])] + out[i + 1 :]
            elif rad(out[0]) < 1.35:  # just outside (the sluice foot): prepend the rim point
                out = [rim((ex, ey), out[0])] + out
            return out

        out = snap_front(pts)  # a comb channel meets the pond at its head (leading end)...
        out = snap_front(out[::-1])[::-1]  # ...a feeder brook meets it at its mouth (trailing end): clip both
        return out

    def _clip_to_moat(self, pts: Any) -> Any:
        """Snap a channel endpoint that meets the MOAT onto the moat bed's edge - trim any run that
        lies within the bed, restarting the channel at the bed's rim with a ~3px inset so its mouth
        covers the rim stroke - the same clean JOIN `_clip_to_pond` gives a pond-fed channel, so a
        moat tap (or a drain emptying into the moat) never draws its bed as a colored line across
        the open moat water. No-op when there is no moat."""
        moat = self.M.get("moat")
        if not moat or len(pts) < 2:
            return pts
        hw = self.M.get("moat_width", 22) / 2

        def foot(q: Pt) -> tuple[Any, Any]:
            best: Any = None
            bd: Any = None
            for i in range(len(moat) - 1):
                ax, ay = moat[i]
                bx, by = moat[i + 1]
                vx, vy = bx - ax, by - ay
                ll = vx * vx + vy * vy or 1.0
                t = max(0.0, min(1.0, ((q[0] - ax) * vx + (q[1] - ay) * vy) / ll))
                fx, fy = ax + vx * t, ay + vy * t
                d = math.hypot(q[0] - fx, q[1] - fy)
                if bd is None or d < bd:
                    bd, best = d, (fx, fy)
            return best, bd

        def snap_front(seq: Any) -> list[Any]:
            out = list(seq)
            if foot(out[0])[1] >= hw:
                return out  # the end is clear of the bed - nothing to snap
            i = 0  # drop any leading run inside the bed
            while i + 1 < len(out) and foot(out[i + 1])[1] < hw:
                i += 1
            if i + 1 >= len(out):
                return out  # the whole channel lies in the moat - leave it
            f, _d = foot(out[i])
            nxt = out[i + 1]
            ux, uy = nxt[0] - f[0], nxt[1] - f[1]
            ul = math.hypot(ux, uy) or 1.0
            return [(f[0] + ux / ul * (hw - 3), f[1] + uy / ul * (hw - 3))] + out[i + 1 :]

        out = snap_front(pts)
        out = snap_front(out[::-1])[::-1]
        return out

    def _clip_to_stream(self, pts: Any) -> Any:
        """Snap a channel endpoint that reaches INTO a stream bed onto the bed's edge (~2px inside
        the bank, so the mouth covers the bank stroke) - the same clean CONFLUENCE `_clip_to_pond`
        and `_clip_to_moat` give: a drain culvert JOINS the receiving stream without drawing its own
        bed as a colored tongue across the current. Trim-only: an end short of the bank is left
        alone (the `channels_join_streams_at_confluence` check requires the RECORDED polyline to
        reach the bed, so the gen extends the record to the centerline and this trims the DRAWING)."""
        streams = self.M.get("streams", [])
        if not streams or len(pts) < 2:
            return pts

        def foot(q: Pt) -> tuple[Any, float, float]:
            best: Any = None
            bd, bhw = 1e9, 4.5
            for st in streams:
                sp = st["poly"]
                hw = st.get("w", 9) / 2
                for i in range(len(sp) - 1):
                    ax, ay = sp[i]
                    bx, by = sp[i + 1]
                    vx, vy = bx - ax, by - ay
                    ll = vx * vx + vy * vy or 1.0
                    t = max(0.0, min(1.0, ((q[0] - ax) * vx + (q[1] - ay) * vy) / ll))
                    fx, fy = ax + vx * t, ay + vy * t
                    d = math.hypot(q[0] - fx, q[1] - fy)
                    if d < bd:
                        bd, best, bhw = d, (fx, fy), hw
            return best, bd, bhw

        def snap_front(seq: Any) -> list[Any]:
            out = list(seq)
            f0, d0, hw0 = foot(out[0])
            if f0 is None or d0 >= hw0 - 2:
                return out  # the end is clear of the bed (or right at its edge) - nothing to trim
            i = 0  # drop any leading run inside the bed
            while i + 1 < len(out):
                _fn, dn, hwn = foot(out[i + 1])
                if dn >= hwn - 2:
                    break
                i += 1
            if i + 1 >= len(out):
                return out  # the whole channel lies in the stream - leave it
            f, _d, hw = foot(out[i])
            nxt = out[i + 1]
            ux, uy = nxt[0] - f[0], nxt[1] - f[1]
            ul = math.hypot(ux, uy) or 1.0
            return [(f[0] + ux / ul * (hw - 2), f[1] + uy / ul * (hw - 2))] + out[i + 1 :]

        out = snap_front(pts)
        out = snap_front(out[::-1])[::-1]
        return out

    @staticmethod
    def _pond_anchored(frm: Any, to: Any) -> bool:
        """True if a watercourse connects TO the pond at either end (frm/to kind == 'pond') - the cue to snap
        that end onto the rim so it JOINS the open water instead of drawing its bed/sheen across it."""
        return any(a and a.get("kind") == "pond" for a in (frm, to))

    def field_channel(self, pts: Any, col: str, w0: float, w1: float, late: bool = False) -> None:
        """Draw a comb-net irrigation channel (from the waterfields engine) THROUGH the water block, so it
        JOINS the pond + the other channels cleanly: its bed sits in the shared bed group (composited as one
        confluence, no dark seam), OVER the pond's rim edge (so its bed covers the rim where it meets the
        pond -> a clean gap, not the rim cutting across). `col` is the bed color (supply vs drain); the width
        tapers `w0 -> w1` along the run (split into pieces). The sluice end is snapped onto the rim by
        `_clip_to_pond`, and an end meeting the MOAT is snapped onto the moat bed's edge by
        `_clip_to_moat` (the same clean-mouth join, for a moated city's taps and drain culverts).
        An end reaching into a STREAM bed is snapped onto that bed's edge by `_clip_to_stream`
        (the confluence mouth for a drain culvert emptying into a stream).
        Not recorded here - the field_ditches are recorded separately for the checks."""
        pts = self._clip_to_stream(self._clip_to_moat(self._clip_to_pond(pts)))
        if abs(w1 - w0) < 0.2:
            dd = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)
            self._water(f'<path d="{dd}" fill="none" stroke="{col}" stroke-width="{w0:.1f}" stroke-linejoin="round" stroke-linecap="round"/>', {}, late=late)
            return
        n, L = 7, len(pts)
        for k in range(n):
            piece = pts[k * (L - 1) // n : (k + 1) * (L - 1) // n + 1]
            if len(piece) < 2:
                continue
            wk = w0 + (w1 - w0) * (k + 0.5) / n
            dd = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in piece)
            self._water(f'<path d="{dd}" fill="none" stroke="{col}" stroke-width="{wk:.1f}" stroke-linejoin="round" stroke-linecap="round"/>', {}, late=late)

    def lane(self, pts: Any, width: float = 16, clearance: float = 22, worn: bool = False, connector: bool = False) -> None:
        """A village lane or connecting path. `worn=True` draws it as UNPAVED TRODDEN EARTH: a NARROW
        single track (China moved rural goods by WHEELBARROW + shoulder-pole porter + packhorse, not wide
        cart roads, so two carts could not pass), packed dirt with soft worn shoulders and NO center
        marking (a paved road was far beyond a village's means). `worn=False` keeps the legacy wide dashed
        lane (the dispersed pool maps until they are rebuilt). `clearance` is the no-build corridor
        half-width (keep houses off the tread). `connector=True` marks the trodden path that LEAVES the
        village for the wider world - it MUST run off the map edge (checked), never stop mid-landscape.
        See settlements.md 'Village lanes and connecting paths'."""
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
        if worn:
            self.add(f'<path d="{dd}" fill="none" stroke="#A98C58" stroke-width="{width + 2.5:.1f}" opacity="0.4" stroke-linejoin="round" stroke-linecap="round"/>')  # soft worn-earth shoulder
            self.add(f'<path d="{dd}" fill="none" stroke="#C9AE79" stroke-width="{width:.1f}" opacity="0.9" stroke-linejoin="round" stroke-linecap="round"/>')  # packed-earth tread, no centerline
        else:
            self.add(f'<path d="{dd}" fill="none" stroke="#CBB178" stroke-width="{width}" opacity="0.65"/>')
            self.add(f'<path d="{dd}" fill="none" stroke="#6B4F2A" stroke-width="1.4" stroke-dasharray="8,8" opacity="0.7"/>')
        self.M.setdefault("lanes", []).append({"pts": [[x, y] for x, y in pts], "worn": worn, "w": width, "connector": connector})
        self.M["lane"] = [[x, y] for x, y in pts]
        self.corridors.append((pts, clearance))

    def street(self, pts: Any, width: float | None = None, label: Any = None, main: bool = False) -> None:
        """A town street (packed earth): the gate-to-yamen main avenue (main=True) or a
        cross lane off it. Buildings front it; a no-build corridor runs down its center.
        Default real width 24 ft (converted at the map's ftpx, linework-floored)."""
        if width is None:
            width = self.lw(24)
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
        self.corridors.append(
            (pts, width / 2 + max(32 * self.bscale, 17))
        )  # buildings front the street but their corners stay off the bed (margin at the map's grain, floored at the largest dwelling's half-diagonal)
        st = {"main": main, "w": width, "pts": [[x, y] for x, y in pts], "z": None}
        self.M.setdefault("town_streets", []).append(st)
        self._ground(
            width,
            st,
            "z",
            edge=f'<path d="{dd}" fill="none" stroke="#B49A66" stroke-width="{width}" opacity="0.9" stroke-linejoin="round" stroke-linecap="round"/>',
            bed=f'<path d="{dd}" fill="none" stroke="#D9C8A0" stroke-width="{width - 7}" opacity="1" stroke-linejoin="round" stroke-linecap="round"/>',
        )
        if label:
            mid = pts[len(pts) // 2]
            self.label(mid[0] + 38, mid[1], label, 11, italic=True, color="#5A4326")

    def kido(self, x: float, y: float, horizontal: bool = True, sw: float | None = None) -> None:
        """A kido - a wooden WARD GATE barring a street at a quarter boundary, manned and shut at
        night to keep the samurai quarter apart from the commoners. A small city seals its wards
        with GATES, not internal ramparts (the walled-ward / fang system was a great-capital, Tang-
        era thing). Drawn OVER the street (a roofed gateway + posts + a guard box); records M['kido'].
        horizontal=True for an E-W street (gate bars N-S), False for an N-S street."""
        if sw is None:
            sw = self.lw(18)  # the barred opening spans a real ~18 ft street
        hw = sw / 2 + 5
        roof: tuple[float, float, float, float]
        if horizontal:  # street runs E-W; the gateway spans N-S
            roof = (x - 7, y - hw, 14, 2 * hw)
            posts = [(x - 8, y - hw - 1, 16, 4), (x - 8, y + hw - 3, 16, 4)]
            guard = (x + 12, y - hw - 13, 16, 15)
        else:  # street runs N-S; the gateway spans E-W
            roof = (x - hw, y - 7, 2 * hw, 14)
            posts = [(x - hw - 1, y - 8, 4, 16), (x + hw - 3, y - 8, 4, 16)]
            guard = (x - hw - 13, y + 12, 15, 16)
        g = ['<g>', f'<rect x="{roof[0]:.0f}" y="{roof[1]:.0f}" width="{roof[2]:.0f}" height="{roof[3]:.0f}" rx="1.5" fill="#8A6E3E" stroke="#3F3018" stroke-width="1.5"/>']
        for px, py, pw, ph in posts:
            g.append(f'<rect x="{px:.0f}" y="{py:.0f}" width="{pw}" height="{ph}" fill="#3F3018"/>')
        g.append(f'<rect x="{guard[0]:.0f}" y="{guard[1]:.0f}" width="{guard[2]}" height="{guard[3]}" rx="1" fill="#CDB890" stroke="#5A4326" stroke-width="1.2"/>')
        g.append('</g>')
        z = self.add_top(''.join(g))
        rects = [roof] + posts + [guard]  # the gate's full drawn footprint (for the labels-on-top check)
        bbox = [min(r[0] for r in rects), min(r[1] for r in rects), max(r[0] + r[2] for r in rects), max(r[1] + r[3] for r in rects)]
        self.M.setdefault("kido", []).append({"x": round(x, 1), "y": round(y, 1), "horizontal": horizontal, "z": z, "bbox": bbox})

    def ward(self, name: str, boundary: Any, gates: Any) -> None:
        """An internal WARD boundary - a light earthwork/palisade fence (NOT a city rampart) that
        SEALS a quarter (the samurai/government ward) off the commoner streets, so its kido gates
        cannot simply be walked around: the fence is continuous between the gates, its ends abut
        the city wall, and a street may pierce it ONLY at a gate. `boundary` is the fence polyline;
        `gates` are (x, y, horizontal) kido where a street crosses it. Records M['wards']."""
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in boundary)
        fz = self.add(f'<path d="{dd}" fill="none" stroke="#9C8A5E" stroke-width="5" opacity="0.9" stroke-linejoin="round" stroke-linecap="round"/>')
        self.add(f'<path d="{dd}" fill="none" stroke="#4A3A22" stroke-width="1.3" stroke-dasharray="2,7" opacity="0.85"/>')  # palisade
        self.corridors.append((boundary, 11))  # buildings keep off the fence line
        # the fence ends ABUT the city wall: lay a short wall-stroke CAP over each end so the rampart
        # renders ON TOP of the fence there (the fence runs UNDER the wall), not the fence over the wall.
        caps: list[Any] = []
        wall = self.M.get("wall")
        if wall:
            ring = list(wall) + [wall[0]]
            for ex, ey in (boundary[0], boundary[-1]):
                best: Any = None
                for i in range(len(ring) - 1):
                    cx, cy = seg_closest(ex, ey, ring[i], ring[i + 1])
                    d = math.hypot(cx - ex, cy - ey)
                    if best is None or d < best[0]:
                        best = (d, (cx, cy), (ring[i + 1][0] - ring[i][0], ring[i + 1][1] - ring[i][1]))
                if best and best[0] < 24:  # the end abuts the wall - cap it
                    (px, py), (tx, ty) = best[1], best[2]
                    tl = math.hypot(tx, ty) or 1
                    ux, uy = tx / tl * 16, ty / tl * 16
                    cz = self.add(f'<path d="M{px - ux:.0f},{py - uy:.0f} L{px + ux:.0f},{py + uy:.0f}" fill="none" stroke="#3A352C" stroke-width="11" stroke-linecap="round"/>')
                    caps.append({"x": round(px, 1), "y": round(py, 1), "z": cz})
        self.M.setdefault("wards", []).append({"name": name, "boundary": [[round(x, 1), round(y, 1)] for x, y in boundary], "z": fz, "wall_caps": caps})
        for gx, gy, horiz in gates:
            self.kido(gx, gy, horizontal=horiz)

    _QUARTER_ZONES = ("residential", "civic", "mixed", "reserve")
    _RESERVE_KINDS = ("drill_ground", "garden", "agricultural_district")

    def quarter(self, poly: Any, zone: str, kind: Any = None, label: Any = None) -> None:
        """Declare a city QUARTER as a first-class zoned region (feature 006). A walled city is a
        set of quarters tiling its interior, each with a ZONE - `residential`, `civic`, `mixed`, or
        `reserve` - so density is judged PER QUARTER (an empty block in a residential quarter is a
        defect; the same emptiness in a declared civic/reserve quarter is intentional). Purely
        DECLARATIVE: it records the region + zone into M['quarters'] and does NOT move or place any
        building. A `reserve` quarter also carries a `kind` and is DRAWN as that visible feature
        (so open ground reads as a deliberate drill ground / garden / farmland, not accidental
        emptiness). Declare reserves BEFORE the packs so the surface renders under later features
        (like fields and streets). `poly` is a list of (x, y); `label` is an optional map label."""
        if zone not in self._QUARTER_ZONES:
            raise ValueError(f"quarter zone must be one of {self._QUARTER_ZONES}, got {zone!r}")
        if zone == "reserve":
            if kind not in self._RESERVE_KINDS:
                raise ValueError(f"a reserve quarter needs kind in {self._RESERVE_KINDS}, got {kind!r}")
            self._draw_reserve(poly, kind)
        elif kind is not None:
            raise ValueError(f"only a reserve quarter may carry a kind (got zone={zone!r}, kind={kind!r})")
        self.M["quarters"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in poly], "zone": zone, "kind": kind, "name": label})
        if label:
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            self.label(sum(xs) / len(xs), sum(ys) / len(ys), label, 9, italic=True, color="#5A4326")

    def _draw_reserve(self, poly: Any, kind: str) -> None:
        """Render a reserve quarter's ground as its declared kind. An agricultural_district is drawn
        by the generator's own field routines (its combs ARE the rendering), so here it only gets a
        faint boundary; a drill_ground is bare packed earth; a garden is a planted green sward."""
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in poly)
        if kind == "drill_ground":
            # a muster / archery field: flat swept earth, a dashed perimeter, a few faint rake lines
            self.add(f'<polygon points="{pts}" fill="#D6C79E" stroke="#A9925C" stroke-width="1.4" stroke-dasharray="6,4"/>')
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            for k in range(1, 5):
                ry = y0 + (y1 - y0) * k / 5
                self.add(f'<line x1="{x0 + 6:.1f}" y1="{ry:.1f}" x2="{x1 - 6:.1f}" y2="{ry:.1f}" stroke="#BBA76E" stroke-width="0.8" opacity="0.6"/>')
        elif kind == "garden":
            # an ornamental / kitchen garden sward: soft green with planted rows
            self.add(f'<polygon points="{pts}" fill="#C4D3A0" stroke="#6E8A44" stroke-width="1.3"/>')
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            for k in range(1, 4):
                ry = y0 + (y1 - y0) * k / 4
                self.add(f'<line x1="{x0 + 6:.1f}" y1="{ry:.1f}" x2="{x1 - 6:.1f}" y2="{ry:.1f}" stroke="#6E9A40" stroke-width="2.0" stroke-linecap="round" opacity="0.75"/>')
        else:  # agricultural_district: the generator's fields carry the visual; mark a faint boundary
            self.add(f'<polygon points="{pts}" fill="none" stroke="#9C8A5E" stroke-width="1.0" stroke-dasharray="3,6" opacity="0.5"/>')

    def alley(self, pts: Any, width: float | None = None) -> None:
        """An UNPAVED interior lane (gravel / wood planks, not the dressed earth of a street) that
        threads the packed block cores: the poor reach their jammed interior housing by alleys,
        not the paved street frontage. Thinner than a street, drawn as a pale gravel path with a
        plank/speckle dash, and a NARROW no-build corridor so the dense core leaves a gap for it.
        Real width ~10 ft (a generous roji is 3-6 ft; ours carries the access for a whole block
        core) - at city scale that lands on the 4px linework floor, which is the doctrine: a roji
        is drawn at the minimum visible width, never to (invisible) true scale."""
        if width is None:
            width = self.lw(10)
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
        self.corridors.append((pts, width / 2 + 11))  # setback keeps building CORNERS off the lane, not just centers
        al = {"pts": [[x, y] for x, y in pts], "w": width, "z": None}
        self.M.setdefault("alleys", []).append(al)
        self._ground(
            width,
            al,
            "z",  # an unpaved gravel lane: its surface IS the bed (no curb/edge), plus a speckle
            bed=f'<path d="{dd}" fill="none" stroke="#C7BB9C" stroke-width="{width}" opacity="0.85" stroke-linejoin="round" stroke-linecap="round"/>',
            top=f'<path d="{dd}" fill="none" stroke="#9A8A68" stroke-width="1.4" stroke-dasharray="2,5" opacity="0.7"/>',
        )

    # ---- hill + shrine + torii
    def hill(self, cx: float, cy: float, rx: float, ry: float, steep: bool = False) -> Pt:
        rings = [(cx, cy + 28, rx, ry), (cx, cy, rx * 0.76, ry * 0.76), (cx, cy - 26, rx * 0.52, ry * 0.52), (cx, cy - 44, rx * 0.30, ry * 0.32)]
        self.M["hill"] = [rings[0][0], rings[0][1], rings[0][2], rings[0][3]]
        self.M["summit"] = [rings[3][0], rings[3][1], rings[3][2], rings[3][3]]
        self.ellipses.append((rings[0][0], rings[0][1], rings[0][2], rings[0][3]))
        for (ax, ay, arx, ary), shade in zip(rings, ['#DFD0A2', '#D8C795', '#D0BD87', '#C8B37B'], strict=False):
            self.add(f'<ellipse cx="{ax:.0f}" cy="{ay:.0f}" rx="{arx:.0f}" ry="{ary:.0f}" fill="{shade}" stroke="#A8995F" stroke-width="1"/>')
        ocx, ocy, orx, ory = rings[0]
        for k in range(30):
            a = 2 * math.pi * k / 30
            ex, ey = ocx + math.cos(a) * orx, ocy + math.sin(a) * ory
            self.add(f'<line x1="{ex:.0f}" y1="{ey:.0f}" x2="{ex + math.cos(a) * 9:.0f}" y2="{ey + math.sin(a) * 9:.0f}" stroke="#A8995F" stroke-width="0.9"/>')
        if steep:
            # emphasized downslope hachures over the steep north back and upper flanks:
            # closely-spaced, longer ticks read as a steep, undefendable-on-foot slope
            n = 52
            for k in range(n + 1):
                ang = math.radians(195 + (345 - 195) * k / n)
                ex, ey = ocx + math.cos(ang) * orx, ocy + math.sin(ang) * ory
                ln = 19 + 5 * math.sin(math.radians(195 + (345 - 195) * k / n) - math.pi / 2)
                self.add(f'<line x1="{ex:.1f}" y1="{ey:.1f}" x2="{ex + math.cos(ang) * ln:.1f}" y2="{ey + math.sin(ang) * ln:.1f}" stroke="#8F7E48" stroke-width="1.0"/>')
        st = random.getstate()
        random.seed(4)
        for _ in range(15):
            a = random.uniform(0, 2 * math.pi)
            rr = random.uniform(0.4, 0.9)
            tx = cx + math.cos(a) * rx * rr
            ty = (cy + 12) + math.sin(a) * ry * rr
            self.add(f'<circle cx="{tx:.0f}" cy="{ty:.0f}" r="{random.uniform(4, 6):.1f}" fill="#7E9B5C" stroke="#52663C" stroke-width="0.8"/>')
            self.add(f'<circle cx="{tx - 1:.0f}" cy="{ty - 1:.0f}" r="1.6" fill="#9DB87A"/>')
        random.setstate(st)
        return (cx, cy - 40)  # summit point for the shrine

    def shrine(self, x: float, y: float, w_ft: float = 62, h_ft: float = 42, kind: str = "shrine") -> None:
        """The legacy simple shrine glyph (the civic_shrine roll path + secondary_shrine). TRUE SCALE
        (GM 2026-07-21): dimensions are REAL FEET, converted through px() - an ordinary village
        tutelary hall ~62x42 ft (~240 m2, inside the 600 m2 village ceiling). The old signature took
        fixed PIXELS (104x68 default), a latent footgun that would have drawn a 208x136 ft
        monastery-sized hall on any village that used the default civic_shrine path."""
        w, h = self.px(w_ft), self.px(h_ft)
        self.add(f'<rect x="{x - w / 2:.0f}" y="{y - h / 2:.0f}" width="{w}" height="{h}" rx="3" fill="#C9876C" stroke="#6B2A18" stroke-width="2"/>')
        self.add(f'<rect x="{x - w / 2:.0f}" y="{y - h / 2:.0f}" width="{w}" height="8" fill="#A03020"/>')
        self.add(f'<rect x="{x - w / 2:.0f}" y="{y + h / 2 - 8:.0f}" width="{w}" height="8" fill="#A03020"/>')
        self.add(f'<line x1="{x - w / 2:.0f}" y1="{y:.0f}" x2="{x + w / 2:.0f}" y2="{y:.0f}" stroke="#6B2A18" stroke-width="0.7"/>')
        self.M["shrine"] = [x - w / 2, y - h / 2, w, h]
        self.M["religious"].append({"kind": kind, "x": x, "y": y, "w": w, "h": h})

    def small_shrine(self, x: float, y: float, w: Any = None, h: Any = None) -> None:
        """A small wayside / neighborhood Shinto SHRINE - a vermilion-roofed shed with a little torii
        in front, the kind that dot a temple neighborhood. Non-residential: recorded in M['religious']
        as kind 'small_shrine' (so it is not housing and not a full temple - it needs no torii avenue
        and is not counted as a dwelling). Placed early so the dense packs flow around it."""
        if w is None:
            w, h = self.px(32), self.px(24)  # ~32x24 ft wayside shrine (town-calibrated glyph)
        x0, y0 = x - w / 2, y - h / 2
        self.add(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w}" height="{h}" rx="2" fill="#C9876C" stroke="#6B2A18" stroke-width="1.4"/>')
        self.add(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w}" height="5" fill="#A03020"/>')  # vermilion roof ridge
        ty = y + h / 2 + max(self.px(8), 3)  # a little torii just in front (south)
        m2 = self.px(9.0) / 2  # TRUE SCALE: a wayside-shrine torii spans ~9 ft (vs the shed's ~32 ft)
        self.add(
            f'<g transform="translate({x:.0f},{ty:.0f})"><line x1="{-m2 * 0.87:.1f}" y1="0" x2="{m2 * 0.87:.1f}" y2="0" stroke="#A03020" stroke-width="{max(self.px(1.2), 1.4):.2f}"/>'
            f'<line x1="{-m2:.1f}" y1="{-m2 * 0.5:.1f}" x2="{m2:.1f}" y2="{-m2 * 0.5:.1f}" stroke="#A03020" stroke-width="{max(self.px(1.0), 1.2):.2f}"/>'
            f'<line x1="{-m2 * 0.62:.1f}" y1="{-m2 * 0.5:.1f}" x2="{-m2 * 0.62:.1f}" y2="{m2 * 0.75:.1f}" stroke="#A03020" stroke-width="{max(self.px(1.0), 1.2):.2f}"/>'
            f'<line x1="{m2 * 0.62:.1f}" y1="{-m2 * 0.5:.1f}" x2="{m2 * 0.62:.1f}" y2="{m2 * 0.75:.1f}" stroke="#A03020" stroke-width="{max(self.px(1.0), 1.2):.2f}"/></g>'
        )
        self.M["religious"].append({"kind": "small_shrine", "x": x, "y": y, "w": w, "h": h, "rot": 0})
        self.placed.append((x, y, w, h))
        bm = 16
        self.block_polys.append([(x0 - bm, y0 - bm), (x + w / 2 + bm, y0 - bm), (x + w / 2 + bm, y + h / 2 + bm + 16), (x0 - bm, y + h / 2 + bm + 16)])

    def well(self, x: float, y: float, r: float = 8) -> None:
        """A public NEIGHBORHOOD WELL (井戸) - a stone curb under an open-sided well-house roof, the
        shared draw-point and social hub (the idobata, where a tenement block's gossip happened). One
        served a courtyard / cluster of ~10-20 households. SMALLER than a house and sits in a block
        INTERIOR off the lanes. Records M['wells'] and blocks placement so the quarter's houses flow
        around it - place BEFORE the quarter's pack. The underground end of a city's water system
        (aqueducts, cisterns, rain barrels feeding the shaft) stays off the map; only the head shows."""
        # THE WELL IS A LOCATION MARKER, NOT A TO-SCALE FOOTPRINT (GM ruling 2026-07-21). A real stone
        # well curb is ~3-4 ft - sub-glyph at every map scale - so the wellhead denotes the well's
        # TO-SCALE LOCATION relative to its surroundings with a legible marker whose own pixels are NOT
        # claimed to be to scale. That places wells under the STROKE CONVENTION (same doctrine as the
        # linework floor, see SKILL.md "to scale"), not in violation of the everything-is-to-scale rule.
        # The marker SCALES WITH THE MAP GRAIN (bscale), exactly as the buildings do, so it keeps a
        # consistent ~0.55x a dwelling at every scale - fixed pixels would make it look right in the
        # dense city but far too small beside a village/town's larger houses. It stays SMALLER than a
        # house regardless of the larger COURTYARD footprint reserved for placement.
        if self._toscale():  # dimensions in FEET, drawn at this map's ftpx (a ~24.8 ft well-house)
            vroof, vcurb = self.px(12.376), self.px(9.36)
        else:  # legacy tiers: the wellhead scales with the urban glyph grain (bscale)
            vroof, vcurb = 11.9 * self.bscale, 9.0 * self.bscale
        self.add(
            f'<rect x="{x - vroof:.1f}" y="{y - vroof:.1f}" width="{2 * vroof:.1f}" height="{2 * vroof:.1f}" rx="1.5" fill="#C7B084" stroke="#6B5836" stroke-width="1.1" opacity="0.55"/>'
        )  # the well-house roof, light so the curb reads through
        self.add(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{vcurb:.1f}" fill="#9AA1A4" stroke="#43403A" stroke-width="1.1"/>')  # stone curb
        self.add(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{vcurb * 0.47:.1f}" fill="#2E4C58"/>')  # dark water in the shaft
        self.M["wells"].append({"x": round(x, 1), "y": round(y, 1), "r": r, "vr": round(vroof, 1)})
        # reserve only a TIGHT courtyard around the small wellhead (not a whole house-plot): houses ring
        # it closely, as in a real tenement court, so a well costs roughly its own footprint, not several
        # dwellings. (`r` stays the recorded clearance radius the checks use; the reserved block is small.)
        self.placed.append((x, y, 2 * vroof, 2 * vroof))
        bm = 8
        self.block_polys.append([(x - vroof - bm, y - vroof - bm), (x + vroof + bm, y - vroof - bm), (x + vroof + bm, y + vroof + bm), (x - vroof - bm, y + vroof + bm)])

    def farm_wells(self, reach_ft: float = 500.0, edge_ft: float = 150.0) -> int:
        """Shared wells for the FARM BELT (town/city scale): the farmsteads outside the urban
        core drink daily too, and Rokugan's unusually well-run domains sink wells liberally
        (the same liberty behind the literal urban idobata count) - so no farmhouse stands
        more than ~500 real ft from a well. Call AFTER farmsteads(). Farmhouses within
        ~150 real ft of the view edge are exempt (their well is presumed just off the map,
        like the fields that run off-edge). Deterministic - no RNG draws, so a map whose
        farm belt is already covered (Hoshizora) is byte-identical with or without the call.
        Greedy cluster cover: seat a well near the densest uncovered cluster's centroid via
        well_at's clear-spot test, repeat. Gated by farm_wells_within_reach."""
        reach = self.px(reach_ft)
        edge = self.px(edge_ft)
        vx, vy, vw, vh = self.view if self.view else (0, 0, self.W, self.H)
        houses = [h for h in self.M["houses"] if min(h["x"] - vx, h["y"] - vy, vx + vw - h["x"], vy + vh - h["y"]) >= edge]

        def covered(h: Mapping[str, Any]) -> bool:
            return any((h["x"] - w["x"]) ** 2 + (h["y"] - w["y"]) ** 2 <= reach * reach for w in self.M["wells"])

        placed = 0
        for _ in range(60):
            todo = [h for h in houses if not covered(h)]
            if not todo:
                break
            best = max(todo, key=lambda h: sum(1 for o in todo if (h["x"] - o["x"]) ** 2 + (h["y"] - o["y"]) ** 2 <= (0.9 * reach) ** 2))
            cl = [o for o in todo if (best["x"] - o["x"]) ** 2 + (best["y"] - o["y"]) ** 2 <= (0.9 * reach) ** 2]
            # seat the well in a STEADING'S DOORYARD, not at the cluster centroid: a farm belt's
            # open ground is mostly CROP (where well_at rightly refuses to stand a wellhead), and
            # historically the rural well sat in a farmstead's own yard anyway - so walk the
            # cluster's members densest-first and ring each until a clear dooryard spot takes
            cl.sort(key=lambda h: -sum(1 for o in todo if (h["x"] - o["x"]) ** 2 + (h["y"] - o["y"]) ** 2 <= (0.9 * reach) ** 2))
            seated = False
            for h in cl:
                for r_, n_ in (
                    (20.0, 8),
                    (30.0, 12),
                    (42.0, 12),
                    (60.0, 16),
                    (80.0, 16),
                    (100.0, 20),
                    (125.0, 24),
                    (150.0, 24),
                ):  # rings widen to ~240 ft at city grain: a steading's inner yard is dense with its own appurtenances and the crop starts right past them, so the clear spot is often the open margin ground BETWEEN steadings
                    for k in range(n_):
                        a = 2 * math.pi * k / n_
                        if self.well_at(h["x"] + r_ * math.cos(a), h["y"] + r_ * math.sin(a)):
                            seated = True
                            placed += 1
                            break
                    if seated:
                        break
                if seated:
                    break
            if not seated:
                # FALLBACK: the cluster's open ground may all be field-ENVELOPE rim slack - the
                # smoothed outline claims more than the crop fills, and _fits rightly refuses the
                # envelope. A farm well standing on unplanted rim ground is fine (that IS the
                # steading's margin); standing on CROP is not. So retry with the envelope blocks
                # suspended and an explicit test against the DRAWN plots instead.
                crop: list[list[tuple[float, float]]] = [list(dp2) for dp2 in self.dry_polys]
                for frec in self.M.get("fields", []):
                    crop += [[(q[0], q[1]) for q in p2] for p2 in frec.get("plot_polys", [])]

                def on_crop(x2: float, y2: float, crop: list[list[tuple[float, float]]] = crop) -> bool:  # bound as a default: the closure lives one loop iteration (B023)
                    m2 = 14.0
                    for cp2 in crop:
                        if min(q[0] for q in cp2) - m2 <= x2 <= max(q[0] for q in cp2) + m2 and min(q[1] for q in cp2) - m2 <= y2 <= max(q[1] for q in cp2) + m2 and point_in_poly(x2, y2, cp2):
                            return True
                    return False

                save = self.field_polys
                self.field_polys = []
                try:
                    for h in cl:
                        # a nearest-first GRID scan, not rings: the clear ground here is pinholes
                        # between steading footprints, and sparse ring angles walk right past them
                        cands = [(h["x"] + dx, h["y"] + dy) for dx in range(-156, 157, 6) for dy in range(-156, 157, 6) if 18 * 18 <= dx * dx + dy * dy <= 156 * 156]
                        cands.sort(key=lambda c: (c[0] - h["x"]) ** 2 + (c[1] - h["y"]) ** 2)
                        for wx2, wy2 in cands:
                            if not on_crop(wx2, wy2) and self.well_at(wx2, wy2):
                                seated = True
                                placed += 1
                                break
                        if seated:
                            break
                finally:
                    self.field_polys = save
            if not seated:
                houses = [h2 for h2 in houses if h2 is not best]  # nothing seats anywhere in this cluster - skip it rather than spin
        return placed

    def well_at(self, x: float, y: float, r: float = 8) -> bool:
        """Place ONE well at (x, y), but only if the spot is clear (a block interior off lanes,
        compounds, the bound, and other placed things - the same `_fits` test place_wells uses).
        Returns True if it placed. For hand-seeding wells into cramped, lane-laced quarters the grid
        scatter can't reach - pass a generous candidate list and the blocked ones simply no-op."""
        if self._fits(x, y, 2 * r + 14, 2 * r + 14):
            self.well(x, y, r)
            return True
        return False

    def place_wells(self, bbox: Any, spacing: float, r: float = 8, near: Any = None, coverage: bool = True) -> list[Pt]:
        """Scatter neighborhood wells across a residential bbox on a grid at ~`spacing` px, keeping
        each in a block INTERIOR: a candidate is dropped if it falls on a lane corridor, outside the
        city bound, on an existing compound (temple/estate/pond), or too near another well (all via
        `_fits`). For each grid cell the cell center is tried first, then a few small offsets, so a
        cell still gets a well when its exact center happens to land on a lane or compound - this keeps
        coverage even in the lane-laced warren. One well per ~spacing px serves the courtyards around
        it. Call BEFORE the quarter's house pack so the houses flow around the wells. Returns the
        placed (x, y) list. Pass coverage=False to keep `near` as a PER-CANDIDATE gate only - the
        coverage pass sweeps ALL dwellings map-wide, which a district-scoped call must not do (it
        would drop wells beside the samurai compounds, which keep no public wells)."""
        x0, y0, x1, y1 = bbox
        probe = 2 * r + 14  # a modest footprint => wells sit in the courtyards, not crammed on a lane
        d = spacing * 0.26
        offsets = [(0, 0), (d, d), (-d, -d), (d, -d), (-d, d)]
        # `near`: only place a well that has a DWELLING within `near` px - a well serves the households
        # around it, so it must sit AMONG the buildings, never out in open countryside. Pass it when the
        # houses are already placed (the rural tiers: place_wells runs AFTER the field rings); a city's
        # pack runs after place_wells and fills in around the wells, so the city omits it.
        dwell = self.M.get("buildings", []) + self.M.get("houses", []) if near is not None else None
        out: list[Pt] = []
        yy = y0 + spacing / 2
        while yy <= y1:
            xx = x0 + spacing / 2
            while xx <= x1:
                for ox, oy in offsets:
                    cx, cy = xx + ox, yy + oy
                    if self._fits(cx, cy, probe, probe) and (dwell is None or any((b["x"] - cx) ** 2 + (b["y"] - cy) ** 2 < near * near for b in dwell)):
                        self.well(cx, cy, r)
                        out.append((cx, cy))
                        break
                xx += spacing
            yy += spacing
        if dwell is not None and coverage:
            # COVERAGE pass: the grid can leave an edge / outlier dwelling in a gap. Guarantee none is left
            # well-less: any dwelling with no well within `spacing` gets one dropped in a clear spot beside it.
            for b in dwell:
                if all((b["x"] - wx) ** 2 + (b["y"] - wy) ** 2 > spacing * spacing for wx, wy in out):
                    for ox, oy in ((0, near * 0.6), (near * 0.6, 0), (-near * 0.6, 0), (0, -near * 0.6), (near * 0.45, near * 0.45), (-near * 0.45, near * 0.45)):
                        cx, cy = b["x"] + ox, b["y"] + oy
                        if self._fits(cx, cy, probe, probe):
                            self.well(cx, cy, r)
                            out.append((cx, cy))
                            break
        return out

    def _draw_byre(self, cx: float, cy: float, w: float, h: float, rot: float = 0) -> None:
        """A small OPEN-FRONTED draft-animal shed (ox / water-buffalo byre): a plank-and-thatch roof with a
        dark stall mouth along the front, distinct from the solid gray kura storehouse and from a dwelling."""
        g = [f'<g transform="translate({cx:.1f},{cy:.1f}) rotate({rot:.1f})">']
        g.append(f'<rect x="{-w / 2:.1f}" y="{-h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="1.6" fill="#B0905E" stroke="#59431F" stroke-width="1.1"/>')  # thatch/plank roof
        g.append(f'<rect x="{-w / 2 + 2:.1f}" y="{h * 0.02:.1f}" width="{w - 4:.1f}" height="{h * 0.4:.1f}" rx="1" fill="#33291C"/>')  # the shaded open stall mouth
        g.append(f'<line x1="{-w / 2 + 2:.1f}" y1="{-h * 0.08:.1f}" x2="{w / 2 - 2:.1f}" y2="{-h * 0.08:.1f}" stroke="#59431F" stroke-width="0.8" opacity="0.6"/>')  # roof ridge
        g.append('</g>')
        self.add(''.join(g))

    def draft_byres(self, fraction: float = 0.2, gap: float = 64) -> list[Pt]:
        """DRAFT-ANIMAL BYRES (ox / water-buffalo sheds) standing in the courtyards among the homesteads.
        Wet-rice plowing and puddling turns on a draft animal, but a buffalo was a costly asset that poorer
        households SHARED or hired, so a village keeps only a MINORITY of byres (~one per 4-5 households ->
        `fraction`) - shared sheds, not one per farm. HOUSE-DRIVEN: for the wealthier homesteads (buffalo
        owners) in turn, spiral outfrom the house to find the nearest clear gap just past its reserved
        footprint (off every other footprint, lane, block, crop, via `_fits`), keeping byres `gap` px apart so
        they read as scattered, not clumped; a homestead boxed in on all sides is skipped. Call AFTER
        farmsteads() (homesteads fixed) and BEFORE the grove (which then skips the byres). Records M['byres']."""
        bs = self.bscale
        # SIZE: a shared byre houses ~1-2 draft animals (an ox / water-buffalo stall is ~2x3 m) plus fodder ->
        # ~16 x 11 ft ~ 15 m2, well under the ~120 m2 farmhouse. To-scale tiers carry it in FEET (drawn at ftpx);
        # legacy tiers scale it with the urban glyph grain (bscale).
        if self._toscale():
            bw, bh = round(self.px(16.12), 1), round(self.px(10.92), 1)
        else:
            bw, bh = round(15.5 * bs, 1), round(10.5 * bs, 1)
        houses = [h for h in self.M.get("houses", []) if h.get("kind") == "plain"]
        ranked = sorted(houses, key=lambda h: (-h.get("wealth", 1.0), h["x"], h["y"]))  # buffalo owners = the wealthier
        target = max(1, round(len(houses) * fraction))
        out: list[Pt] = []
        for h in ranked:
            if len(out) >= target:
                break
            rr = math.hypot(h["w"], h["h"]) / 2 + bh
            done = False
            while rr < math.hypot(h["w"], h["h"]) / 2 + bh + 70 and not done:
                for a in range(0, 360, 30):
                    cx = h["x"] + rr * math.cos(math.radians(a))
                    cy = h["y"] + rr * math.sin(math.radians(a))
                    if (
                        self._fits(cx, cy, bw + 6, bh + 6)
                        and not any(point_in_poly(cx, cy, ff) or edge_dist(cx, cy, ff) < bh for ff in self.field_polys)
                        and all((bx - cx) ** 2 + (by - cy) ** 2 > gap * gap for bx, by in out)
                    ):
                        self._draw_byre(cx, cy, bw, bh)
                        self.placed.append((cx, cy, bw, bh))
                        self.M["byres"].append({"x": round(cx, 1), "y": round(cy, 1), "w": bw, "h": bh, "rot": 0})
                        out.append((cx, cy))
                        done = True
                        break
                rr += 16
        return out

    def shrine_well(self, cx: float, cy: float, r: float = 8) -> Pt | None:
        """Place a set-apart shrine's OWN ablution well (temizu) close beside the hall at (cx, cy): try
        positions on widening rings until one fits clear of the hall, torii, graveyard, lanes, and any other
        placed footprint (`well_at`'s test). A larger hall pushes its well onto an outer ring. Call AFTER the
        hall, houses, and village wells are placed. Returns the placed (x, y), or None if it is walled in.
        For a remote shrine that cannot use the village's shared wells (`remote_shrine_has_own_well`)."""
        for rr in (54, 66, 80, 96, 112):
            for a in range(0, 360, 30):
                x, y = cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a))
                if self.well_at(x, y, r):
                    return (x, y)
        return None

    def _torii(self, tx: float, ty: float, span_ft: float = 16.0) -> int:
        """Draw ONE torii arch TRUE SCALE (GM 2026-07-21) and record it in M['torii']; returns the
        z-handle. `span_ft` is the TOP-RAIL span in real feet: a standard shrine/approach torii runs
        ~10-16 ft between its rail ends (grand landmark torii reach 30-50 ft, but none of our maps
        draws one). The old glyph was FIXED-PIXEL (38 px rail) - honest at 1 ft/px but 76 ft at
        village scale and 114 ft at city scale. Proportions keep the authored glyph's 38:24 rail:height
        ratio; STROKES keep a legibility floor (stroke convention - see SKILL.md "to scale"), never a
        footprint license."""
        s2 = self.px(span_ft) / 2  # half the top-rail span; the glyph was authored at s2=19px
        c2, p2 = s2 * 16 / 19, s2 * 12 / 19  # crossbar half-span, post offset
        hz, hd = s2 * 7 / 19, s2 * 17 / 19  # rail rise above / post drop below the crossbar
        swr = max(self.px(1.4), 1.9)  # rail stroke (~1.4 ft beam, floored)
        swp = max(self.px(1.2), 1.6)  # post stroke (~1.2 ft post, floored)
        tz = self.add_top(
            f'<g transform="translate({tx:.0f},{ty:.0f})">'  # over any street it crosses
            f'<line x1="{-c2:.1f}" y1="0" x2="{c2:.1f}" y2="0" stroke="#A03020" stroke-width="{swr:.2f}"/>'
            f'<line x1="{-s2:.1f}" y1="{-hz:.1f}" x2="{s2:.1f}" y2="{-hz:.1f}" stroke="#A03020" stroke-width="{swr * 0.85:.2f}"/>'
            f'<line x1="{-p2:.1f}" y1="{-hz:.1f}" x2="{-p2:.1f}" y2="{hd:.1f}" stroke="#A03020" stroke-width="{swp:.2f}"/>'
            f'<line x1="{p2:.1f}" y1="{-hz:.1f}" x2="{p2:.1f}" y2="{hd:.1f}" stroke="#A03020" stroke-width="{swp:.2f}"/></g>'
        )
        self.M["torii"].append([round(tx, 1), round(ty, 1), tz])
        return tz

    def torii_path(self, ascent: Any) -> None:
        """Place one torii at each interior vertex of the ascent polyline; draw the
        winding path. Count is village-specific - pass as many points as torii+ends."""
        dstr = 'M' + ' L'.join(f'{x},{y}' for x, y in ascent)
        self.add(f'<path d="{dstr}" fill="none" stroke="#B89A6A" stroke-width="8" opacity="0.7"/>')
        self.add(f'<path d="{dstr}" fill="none" stroke="#6B4F2A" stroke-width="1" stroke-dasharray="3,5"/>')
        for tx, ty in ascent[1:-1]:
            self._torii(tx, ty)

    def torii_even(self, ascent: Any, count: int) -> None:
        """Spread `count` torii by arc-length along an ascent polyline (Kikuta style)."""
        seg = [math.hypot(ascent[i + 1][0] - ascent[i][0], ascent[i + 1][1] - ascent[i][1]) for i in range(len(ascent) - 1)]
        tot = sum(seg)

        def along(t: float) -> Pt:
            target = t * tot
            acc: float = 0
            for i, sl in enumerate(seg):
                if acc + sl >= target:
                    f = (target - acc) / sl
                    return (ascent[i][0] + (ascent[i + 1][0] - ascent[i][0]) * f, ascent[i][1] + (ascent[i + 1][1] - ascent[i][1]) * f)
                acc += sl
            return cast(Pt, ascent[-1])  # pragma: no cover - defensive: t is capped at 0.86, never past the last segment

        dstr = 'M' + ' L'.join(f'{x},{y}' for x, y in ascent)
        self.add(f'<path d="{dstr}" fill="none" stroke="#B89A6A" stroke-width="8" opacity="0.7"/>')
        self.add(f'<path d="{dstr}" fill="none" stroke="#6B4F2A" stroke-width="1" stroke-dasharray="3,5"/>')
        for i in range(count):
            tx, ty = along(0.06 + 0.80 * i / (count - 1))
            self._torii(tx, ty)

    def shrine_hall(
        self,
        x: float,
        y: float,
        label: Any,
        sublabel: str = "",
        w: float = 120,
        h: float = 82,
        torii: Any = None,
        primary: bool = False,
        edge: str = "#6B2A18",
        kind: str = "shrine",
        graveyard: bool = True,
        label_below: bool = False,
    ) -> None:
        """A standalone religious hall on flat ground. The kind follows settlement
        scale: villages have shrines, towns have monasteries, cities have temples
        (hamlets have none). primary=True marks the settlement's main one (M['shrine'],
        used by the torii checks). A torii may stand in front (torii=[(x,y),...]).
        graveyard=False marks a temple that hosts NO burial ground (a new or special-purpose
        hall, e.g. one founded in a former samurai estate) - city_temples_have_graveyards
        then exempts it; every other temple is expected to have a graveyard in its precinct.

        SCALE CONTRACT: `w`/`h` are DRAWN PIXELS, so at 1 ft/px (town) they equal real feet, but a
        coarser map MUST pass s.px(real_ft) - four city temples shipped as fixed 100x64 px = 300x192
        real ft before this was caught (audit 2026-07-21). The guard below refuses a hall whose
        implied real footprint exceeds any real main hall (the largest kondo runs ~150-190 ft;
        Tango's deliberate Daibutsuden-tier landmark is 200 ft) so unscaled px can't slip through."""
        if self.ftpx > 1 and max(w, h) * self.ftpx > 220:
            raise ValueError(f"shrine_hall {w}x{h}px at {self.ftpx} ft/px implies a {max(w, h) * self.ftpx:.0f} ft hall - pass s.px(real_ft), not raw pixels")
        if torii:
            for tx, ty in torii:
                s2 = self.px(16.0) / 2  # matches _torii's default true span
                # block the arch + a NEIGHBOR'S HALF-FOOTPRINT: packs test footprint centers, so the
                # margin must absorb half a house (~28 ft) + slack or a house's edge crosses the arch
                # (the old fixed 38px arch had this margin baked into its own oversize). Still kept
                # SMALLER than a street corridor so torii on a street don't shove the frontage houses.
                bm: float = self.px(28) + 4.0
                self.block_polys.append([(tx - s2 - bm, ty - s2 * 0.5 - bm), (tx + s2 + bm, ty - s2 * 0.5 - bm), (tx + s2 + bm, ty + s2 + bm), (tx - s2 - bm, ty + s2 + bm)])
                self._torii(tx, ty)
                self._clear_ground(tx, ty + 2, max(2 * s2 + 4, 10), max(s2 * 1.3, 8), 30)  # a swept collar under the arch + its sando approach
        self.add(f'<rect x="{x - w / 2:.0f}" y="{y - h / 2:.0f}" width="{w}" height="{h}" rx="3" fill="#C9876C" stroke="{edge}" stroke-width="2"/>')
        self.add(f'<rect x="{x - w / 2:.0f}" y="{y - h / 2:.0f}" width="{w}" height="9" fill="#A03020"/>')
        self.add(f'<rect x="{x - w / 2:.0f}" y="{y + h / 2 - 9:.0f}" width="{w}" height="9" fill="#A03020"/>')
        self.add(f'<line x1="{x - w / 2:.0f}" y1="{y:.0f}" x2="{x + w / 2:.0f}" y2="{y:.0f}" stroke="{edge}" stroke-width="0.7"/>')
        self.M["shrines"].append({"x": x, "y": y, "w": w, "h": h, "label": label})
        self.M["religious"].append({"kind": kind, "x": x, "y": y, "w": w, "h": h, "label": label, "sublabel": sublabel, "graveyard": graveyard})
        if primary:
            self.M["shrine"] = [x - w / 2, y - h / 2, w, h]
        # block a RECT + a building-half margin, at the map's grain (an ellipse undershot the hall
        # corners). The 22px FLOOR (added with the true-size halls, 2026-07-21): packs test footprint
        # CENTERS, so the margin must absorb the check's +4px pad plus half the largest urban neighbor
        # (~29px merchant_large) at ANY scale - at city grain the raw 34*bscale is only ~11px and let a
        # merchant seat its edge into the hall's pad.
        bm = max(34 * self.bscale, 22.0)
        self.block_polys.append([(x - w / 2 - bm, y - h / 2 - bm), (x + w / 2 + bm, y - h / 2 - bm), (x + w / 2 + bm, y + h / 2 + bm), (x - w / 2 - bm, y + h / 2 + bm)])
        self._clear_ground(x, y, w, h, 58)  # the swept shrine precinct - scrub kept off the tended keidai (the grove, if any, is separate)
        if label:
            self.label(x, y + h / 2 + 22 if label_below else y - h / 2 - 10, label, 13, weight="bold", color=edge)
        if sublabel:
            self.label(x, y + h / 2 + 16, sublabel, 9, italic=True, color=edge)

    # ---- landscape / estate features
    def forest(self, west_edge: Any, label: str = "", label_xy: Any = None) -> None:
        """A woodland filling east of an irregular tree-line to the canvas edge.
        Blocks houses. Deterministic tree scatter (RNG saved/restored) so it never
        perturbs house placement."""
        pts = list(west_edge) + [(self.W + 12, west_edge[-1][1]), (self.W + 12, west_edge[0][1])]
        cid = self._cid('forest')
        d = 'M' + ' L'.join(f'{x:.0f},{y:.0f}' for x, y in pts) + ' Z'
        self.add(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
        self.add(f'<path d="{d}" fill="#A9B98C"/>')
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        st = random.getstate()
        random.seed(9)
        self.add(f'<g clip-path="url(#{cid})">')
        yy = min(ys) + 16
        while yy < max(ys):
            xx = min(xs) + 16
            while xx < max(xs):
                tx, ty = xx + random.uniform(-9, 9), yy + random.uniform(-9, 9)
                if point_in_poly(tx, ty, pts):
                    r = random.uniform(6, 9)
                    self.add(f'<circle cx="{tx:.0f}" cy="{ty:.0f}" r="{r:.1f}" fill="#6E8B4C" stroke="#4E6B3C" stroke-width="0.7"/>')
                    self.add(f'<circle cx="{tx - 1.5:.0f}" cy="{ty - 1.5:.0f}" r="{r * 0.4:.1f}" fill="#8FA968"/>')
                xx += 34
            yy += 30
        self.add('</g>')
        random.setstate(st)
        de = 'M' + ' L'.join(f'{x:.0f},{y:.0f}' for x, y in west_edge)
        self.add(f'<path d="{de}" fill="none" stroke="#4E6B3C" stroke-width="2.5"/>')
        self.block_polys.append(pts)
        self.M["forest"] = [[round(x, 1), round(y, 1)] for x, y in pts]
        if label:
            lx, ly = label_xy if label_xy else (min(xs) + (self.W - min(xs)) / 2, (min(ys) + max(ys)) / 2)
            self.label(lx, ly, label, 14, italic=True, weight="bold", color="#3E5631")

    def manor(self, x: float, y: float, w: float, h: float, label: Any, sublabel: str = "", gate_dir: str = "south", rot: float = 0, gate_ft: float = 12.0) -> None:
        """A walled samurai compound (e.g. a magistrate's manor / hunting lodge) shown
        as a feature on a settlement map: ONLY the walls + gate + empty court. The
        interior is deliberately not drawn here - it is the subject of its own Mode A
        diagram, and drawing speculative interior buildings here would contradict it.
        gate_dir (north/south/east/west) is the wall the main gate opens through - face it
        toward whatever the compound fronts (the town / road it sits at the edge of). There
        is no universal default direction (it depends where the town is), but SOUTH is the
        auspicious/formal fallback. `rot` TILTS the whole compound (degrees) so it can parallel
        a diagonal road or river it fronts. Blocks houses.
        TO SCALE (GM 2026-07-19): the gate opening is `gate_ft` real feet (default 12 - a
        nagayamon/yakuimon passes a cart and palanquin; a grand yamen passes gate_ft=18-24),
        the wall draws ~2 ft thick (true-width-or-floored at 2px), and the gate posts are
        ~2 ft squares (floored ~3px). The blank court is DELIBERATE - the interior is the
        subject of its own Mode A diagram when the PCs visit; the wall + gate carry the
        realism, so they are the parts that must be honest. Records gate_w/wall_w (px)."""
        hw, hh = w / 2, h / 2
        wall = '#2D2A24'
        gg = max(self.px(gate_ft) / 2, 2.0)  # gate HALF-gap: real feet, floored so the opening stays visible
        ww = max(self.px(2), 2.0)  # wall thickness: ~2 ft dobei, 2px cartographic floor
        gp = max(self.px(2), 3.0)  # gate post: ~2 ft square, floored for visibility
        a = math.radians(rot)
        ca, sa = math.cos(a), math.sin(a)

        def absol(px: float, py: float) -> Pt:  # a compound-local point -> absolute map coords (after tilt)
            return (x + px * ca - py * sa, y + px * sa + py * ca)

        g = [f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.2f})">', f'<rect x="{-hw:.0f}" y="{-hh:.0f}" width="{w}" height="{h}" fill="#E7D9B4"/>']
        sides = {
            "north": ((-hw, -hh), (hw, -hh), (0, -hh), (0, -1)),
            "south": ((-hw, hh), (hw, hh), (0, hh), (0, 1)),
            "west": ((-hw, -hh), (-hw, hh), (-hw, 0), (-1, 0)),
            "east": ((hw, -hh), (hw, hh), (hw, 0), (1, 0)),
        }
        gcl = sides[gate_dir][2]
        for name, (pa, pb, (gx, gy), outv) in sides.items():
            if name != gate_dir:
                g.append(f'<line x1="{pa[0]:.0f}" y1="{pa[1]:.0f}" x2="{pb[0]:.0f}" y2="{pb[1]:.0f}" stroke="{wall}" stroke-width="{ww:.1f}"/>')
            elif outv[1] == 0:  # vertical wall (west/east) - gap in y
                g.append(f'<line x1="{pa[0]:.0f}" y1="{pa[1]:.0f}" x2="{pa[0]:.0f}" y2="{gy - gg:.1f}" stroke="{wall}" stroke-width="{ww:.1f}"/>')
                g.append(f'<line x1="{pb[0]:.0f}" y1="{gy + gg:.1f}" x2="{pb[0]:.0f}" y2="{pb[1]:.0f}" stroke="{wall}" stroke-width="{ww:.1f}"/>')
                for py in (gy - gg, gy + gg):
                    g.append(f'<rect x="{gx - gp / 2:.1f}" y="{py - gp / 2:.1f}" width="{gp:.1f}" height="{gp:.1f}" fill="{wall}"/>')
            else:  # horizontal wall (north/south) - gap in x
                g.append(f'<line x1="{pa[0]:.0f}" y1="{pa[1]:.0f}" x2="{gx - gg:.1f}" y2="{pa[1]:.0f}" stroke="{wall}" stroke-width="{ww:.1f}"/>')
                g.append(f'<line x1="{gx + gg:.1f}" y1="{pb[1]:.0f}" x2="{pb[0]:.0f}" y2="{pb[1]:.0f}" stroke="{wall}" stroke-width="{ww:.1f}"/>')
                for px in (gx - gg, gx + gg):
                    g.append(f'<rect x="{px - gp / 2:.1f}" y="{gy - gp / 2:.1f}" width="{gp:.1f}" height="{gp:.1f}" fill="{wall}"/>')
        g.append('</g>')
        self.add(''.join(g))
        # interior intentionally left blank: the buildings inside (hall, stables, etc.)
        # belong to a separate Mode A diagram of the manor, not the town/settlement map
        gctr = absol(*gcl)
        corners = [absol(-hw, -hh), absol(hw, -hh), absol(hw, hh), absol(-hw, hh)]
        # an axis-aligned manor whose wall abuts a neighborhood (ward) fence yields that wall to the
        # fence (re-stamped on top), exactly like the mausoleum; tilted manors are left untouched
        ward_walls: list[str] = []
        if rot == 0:
            msides = {
                "north": ((x - hw, y - hh), (x + hw, y - hh)),
                "south": ((x - hw, y + hh), (x + hw, y + hh)),
                "west": ((x - hw, y - hh), (x - hw, y + hh)),
                "east": ((x + hw, y - hh), (x + hw, y + hh)),
            }
            ward_walls = [name for name, (a, b) in msides.items() if name != gate_dir and self._ward_fence_cap(a, b) is not None]
        self.M["manors"].append(
            {
                "x": x,
                "y": y,
                "w": w,
                "h": h,
                "rot": rot,
                "label": label,
                "gate": [round(gctr[0], 1), round(gctr[1], 1)],
                "gate_dir": gate_dir,
                "ward_walls": ward_walls,
                "gate_w": round(2 * gg, 2),
                "wall_w": round(ww, 2),
            }
        )
        m = max(
            36 * self.bscale, 26
        )  # a building-half margin at the map's grain, floored so a standard dwelling's corner keeps the 14px office-abut clearance (a samurai_large needs seed luck - the sweep handles it)
        blk = [absol(-hw - m, -hh - m), absol(hw + m, -hh - m), absol(hw + m, hh + m), absol(-hw - m, hh + m)]
        self.block_polys.append([(round(px, 1), round(py, 1)) for px, py in blk])
        ys = [c[1] for c in corners]
        if label:
            self.label(x, min(ys) - 12, label, 14, weight="bold")
        if sublabel:
            self.label(x, max(ys) + 18, sublabel, 9, italic=True)

    def _estate_wall_clear(self, x: float, y: float, w: float, h: float, marg: float = 2.5) -> bool:
        """Whether a walled compound's PERIMETER at (x,y,w,h) stays off recorded water (canals,
        docks, moat, river, pond), fire towers, AND the street net (streets, alleys, roads, the
        ring road - a compound wall may LINE a street, never stand IN its cleared band), with
        `marg` px of daylight. A fire tower ENCLOSED inside the court is refused too (the watch
        reaches its tower from public ground). Mirrors the merchant_estate_wall_clear_of_* gate
        geometry (which enforces 1.5px; the engine demands a little more so placement never sits
        at the check's edge)."""
        ex0, ey0, ex1, ey1 = x - w / 2, y - h / 2, x + w / 2, y + h / 2
        if any(abs(t["x"] - x) < w / 2 and abs(t["y"] - y) < h / 2 for t in self.M.get("fire_towers", []) if "w" in t):
            return False  # tower walled inside the private court
        edges = [((ex0, ey0), (ex1, ey0)), ((ex1, ey0), (ex1, ey1)), ((ex1, ey1), (ex0, ey1)), ((ex0, ey1), (ex0, ey0))]
        lines: list[tuple[Any, float]] = [(cc["poly"], cc.get("w", 12) / 2 + marg) for cc in self.M.get("canals", [])]
        if self.M.get("moat"):
            lines.append((self.M["moat"], self.M.get("moat_width", 22) / 2 + marg))
        rv = self.M.get("river")
        if rv:
            lines.append((rv["pts"], rv.get("w", 40) / 2 + marg))
        lines += [(st["pts"], st.get("w", 12) / 2 + marg) for st in self.M.get("town_streets", [])]
        lines += [(al["pts"], al.get("w", 8) / 2 + marg) for al in self.M.get("alleys", [])]
        lines += [(rd["pts"], rd["w"] / 2 + marg) for rd in self.M.get("roads", [])]
        if self.M.get("road"):
            lines.append((self.M["road"], self.M.get("road_width", 26) / 2 + marg))
        if self.M.get("ring_road"):
            lines.append((self.M["ring_road"], self.M.get("ring_road_width", 7) / 2 + marg))
        boxes = [(dk["x"], dk["y"], dk["w"] / 2 + marg, dk["h"] / 2 + marg) for dk in self.M.get("docks", [])]
        boxes += [(t["x"], t["y"], t["w"] / 2 + marg, t["h"] / 2 + marg) for t in self.M.get("fire_towers", []) if "w" in t]
        pond = self.M.get("pond")
        for p0, p1 in edges:
            steps = max(2, int(math.hypot(p1[0] - p0[0], p1[1] - p0[1]) / 3))
            for si in range(steps + 1):
                px_, py_ = p0[0] + (p1[0] - p0[0]) * si / steps, p0[1] + (p1[1] - p0[1]) * si / steps
                if any(abs(px_ - bx) < bw and abs(py_ - by) < bh for bx, by, bw, bh in boxes):
                    return False
                if any(any(seg_dist(px_, py_, pts[k], pts[k + 1]) < hw for k in range(len(pts) - 1)) for pts, hw in lines):
                    return False
                if pond and ((px_ - pond[0]) / (pond[2] + marg)) ** 2 + ((py_ - pond[1]) / (pond[3] + marg)) ** 2 <= 1:
                    return False
        return True

    def merchant_estate(self, x: float, y: float, w: Any = None, h: Any = None, gate_dir: str = "south") -> None:
        """A walled merchant compound - a VERY-rich merchant's estate within the merchant quarter: a
        light perimeter wall around a court with the merchant's large house inside (one large dwelling).
        Recorded in M['merchant_estates'] (NOT M['manors'], which are the samurai country estates
        outside the wall). The inner house is a normal merchant_large building, so it counts as housing.
        gate_dir is the side the courtyard gate opens through - it is fine for the walls to ABUT a
        neighboring building, but point the GATE at open ground, never into another building.
        SITING RULE (GM 2026-07-19): the compound wall must stand on dry, private ground - never
        through a canal/dock/moat/river/pond (the waterfront is working quay) or a fire tower
        (the municipal watch cannot be embedded in a private wall). Draw those features BEFORE
        the estate; if the requested spot violates, a small candidate fan slides the estate to
        the nearest clear seat, and if none exists within ~36px this raises rather than drawing
        a wall the gate will reject."""
        if w is None:
            w, h = 186 * self.bscale, 138 * self.bscale  # ~230x170 ft very-rich urban compound, scaled with the building grain
        # ring-ordered fan: near seats first, then wider; includes half-steps so the estate can
        # land in a narrow clear corridor (streets + water can leave windows only a few px wide)
        fan = [(0, 0)] + [(dx, dy) for r in (4, 8, 12, 16, 24, 36, 48) for dx, dy in ((-r, 0), (r, 0), (0, -r), (0, r), (-r, -r), (r, -r), (-r, r), (r, r))]
        for dx, dy in fan:
            if self._estate_wall_clear(x + dx, y + dy, w, h):
                x, y = x + dx, y + dy
                break
        else:
            raise ValueError(
                f"merchant_estate at ({x:.0f},{y:.0f}) {w:.0f}x{h:.0f}: no seat within the slide fan keeps the compound wall clear of water/fire towers - resite it (or the tower) in the gen"
            )
        x0, y0, x1, y1 = x - w / 2, y - h / 2, x + w / 2, y + h / 2
        mww = max(self.px(2), 1.6)  # wall ~2 ft (a merchant's lighter wall), floored for visibility
        mgg = max(self.px(10), 3.5)  # gate opening ~10 real ft (a cart gate), floored
        self.add(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w:.0f}" height="{h:.0f}" fill="#EAD9B0" stroke="#5A4326" stroke-width="{mww:.1f}"/>')  # walled court
        # the gate gap (erases a slot of the wall stroke on the chosen side); gate point on that edge
        gates = {"south": (x, y1, mgg, mww + 2), "north": (x, y0, mgg, mww + 2), "east": (x1, y, mww + 2, mgg), "west": (x0, y, mww + 2, mgg)}
        gx, gy, gw, gh = gates[gate_dir]
        self.add(f'<rect x="{gx - gw / 2:.1f}" y="{gy - gh / 2:.1f}" width="{gw:.1f}" height="{gh:.1f}" fill="#EAD9B0"/>')
        self.building(x, y - 2, *self._dims("merchant_large"), "merchant_large")  # the large house inside the court
        self.M.setdefault("merchant_estates", []).append(
            {"x": round(x, 1), "y": round(y, 1), "w": w, "h": h, "gate": [round(gx, 1), round(gy, 1)], "gate_dir": gate_dir, "gate_w": round(mgg, 2), "wall_w": round(mww, 2)}
        )
        m = 18 * self.bscale  # a building-half margin at the map's grain
        self.block_polys.append([(x0 - m, y0 - m), (x1 + m, y0 - m), (x1 + m, y1 + m), (x0 - m, y1 + m)])

    def road(self, pts: Any, label: Any = None, width: float | None = None, label_xy: Any = None) -> None:
        """A major road (e.g. an Imperial road) - a bordered roadbed. No-build corridor.
        Default real width 26 ft (an Imperial trunk highway; the historical Tokaido ran
        ~18-24 ft), converted at the map's ftpx and linework-floored.
        label_xy overrides the label anchor (default: the polyline midpoint). For a city the
        midpoint is the city CENTER, but the road label names the *Imperial* road, which is an
        Imperial responsibility only OUTSIDE the walls - inside, the same roadway is a city
        street the city maintains - so a city must pass label_xy a point beyond the gates."""
        if width is None:
            width = self.lw(26)
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
        self.corridors.append((pts, width / 2 + max(32 * self.bscale, 17)))  # wide road -> larger building setback (at the map's grain, floored)
        if "road" not in self.M or self.M["road"] is None:
            self.M["road"] = [[x, y] for x, y in pts]  # the FIRST road stays the main road (back-compat
            self.M["road_width"] = width  # for the single-road checks/projections)
        self.M.setdefault("roads", []).append({"pts": [[x, y] for x, y in pts], "w": width})
        self.M["road_z"] = None
        self._ground(
            width,
            self.M,
            "road_z",
            edge=f'<path d="{dd}" fill="none" stroke="#9C7A40" stroke-width="{width}" opacity="0.9"/>',
            bed=f'<path d="{dd}" fill="none" stroke="#D8C49A" stroke-width="{width - 8}" opacity="1"/>',
            top=f'<path d="{dd}" fill="none" stroke="#8A6E3E" stroke-width="1.2" stroke-dasharray="12,10" opacity="0.6"/>',
        )
        if label:
            mid = pts[len(pts) // 2]
            lx, ly = label_xy if label_xy else (mid[0] + 46, mid[1] - 22)
            # DEFERRED to finish(): the label picks its side of the road by what is actually
            # built around it, and at road-draw time the map is still empty (GM label doctrine:
            # a label that can sit in empty ground, should; otherwise cover as little as possible)
            self._road_label: Any = (label, lx, ly)

    # urban building palette and default footprints, keyed by town caste/role
    URBAN = {
        "shop": ('#D8C49A', '#6B4F2A', 48, 32),  # merchant shophouse (modest)
        "merchant": ('#DDB87A', '#5A3F1E', 54, 36),  # merchant house+shop (the storefront, fronts the street)
        "merchant_house": ('#DDB87A', '#5A3F1E', 50, 34),  # a small/average merchant home (behind the storefront)
        "merchant_large": ('#E2BE7E', '#5A3F1E', 86, 60),  # a rich merchant's large home
        "laborer": ('#C2B190', '#6B5A3A', 34, 24),  # laborer dwelling (the standard ~87% - poorer hinin)
        "laborer_large": ('#CBB684', '#6B5A3A', 50, 34),  # a 'master' (rich) laborer's larger home (~12.5% of laborers, budgets.md) - the wealthier hinin who line the back streets
        "servant": ('#CDBE9C', '#6B5A3A', 30, 22),  # servant quarters (small)
        "barn": ('#C9A57A', '#6B4F2A', 84, 56),
        "samurai": ('#DDB87A', '#5A3F1E', 56, 40),  # a junior samurai's small city house (most of the neighborhood)
        "samurai_large": ('#E0BC80', '#5A3F1E', 82, 58),  # a senior samurai's large city house (a minority; walled estates are OUTSIDE the walls)
        "civic": ('#CDB890', '#5A4326', 66, 46),
        "burakumin": ('#BCB29C', '#7A7058', 38, 26),
    }

    def building(self, cx: float, cy: float, w: float, h: float, kind: str = "shop", rot: float = 0) -> None:
        """An urban building (shophouse, laborer dwelling, samurai house, etc.) -
        boxier than a farmhouse, oriented to the street not the sun. Blocks placement."""
        fill, edge = self.URBAN.get(kind, self.URBAN["shop"])[:2]
        x0, y0 = -w / 2, -h / 2
        dash = ' stroke-dasharray="5,3"' if kind == "burakumin" else ''
        g = [f'<g transform="translate({cx:.0f},{cy:.0f}) rotate({rot:.0f})">']
        g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w}" height="{h}" rx="2" fill="{fill}" stroke="{edge}" stroke-width="1.6"{dash}/>')
        g.append(f'<line x1="{-w * 0.30:.1f}" y1="0" x2="{w * 0.30:.1f}" y2="0" stroke="{edge}" stroke-width="0.8" opacity="0.6"/>')
        if kind in ("shop", "merchant"):
            # a BUSINESS: a striped awning along the street frontage + a hanging sign, so
            # commerce reads as visually distinct from plain housing
            g.append(f'<rect x="{-w * 0.5:.1f}" y="{h / 2 - 6:.1f}" width="{w}" height="6.5" fill="#A8472E" opacity="0.95"/>')
            for sx in range(int(-w * 0.5) + 3, int(w * 0.5), 9):
                g.append(f'<rect x="{sx:.1f}" y="{h / 2 - 6:.1f}" width="4.5" height="6.5" fill="#E8D2A8" opacity="0.55"/>')
            g.append(f'<rect x="-5.5" y="{h / 2 - 2:.1f}" width="11" height="9" rx="1" fill="#E8D9A8" stroke="#6B4A22" stroke-width="0.8"/>')  # hanging sign
        else:
            g.append(f'<rect x="{-w * 0.16:.1f}" y="{h / 2 - 3:.1f}" width="{w * 0.32:.1f}" height="3.2" fill="{edge}" opacity="0.8"/>')  # door
        g.append('</g>')
        self.add(''.join(g))
        self.M["buildings"].append({"x": cx, "y": cy, "w": w, "h": h, "kind": kind, "rot": rot})
        self.placed.append((cx, cy, w, h))

    def _dims(self, kind: str) -> tuple[float, float]:
        w, h = self.URBAN.get(kind, self.URBAN["shop"])[2:]
        return w * self.bscale, h * self.bscale

    def try_building(self, cx: float, cy: float, kind: str, rot: float = 0) -> bool:
        w, h = self._dims(kind)
        if self._fits(cx, cy, w, h):
            self.building(cx, cy, w, h, kind, rot)
            return True
        return False

    def _face_street_rot(self, x: float, y: float) -> tuple[float | None, float]:
        """Rotation that turns a building's frontage toward the nearest street/road, and
        the distance to it. (None, inf) if there are no streets."""
        lines = [st["pts"] for st in self.M.get("town_streets", [])]
        if self.M.get("road"):
            lines.append(self.M["road"])
        best: Any = None
        bd = 1e18
        for sp in lines:
            for k in range(len(sp) - 1):
                cx, cy = seg_closest(x, y, sp[k], sp[k + 1])
                d = math.hypot(cx - x, cy - y)
                if d < bd:
                    bd, best = d, (cx, cy)
        if best is None:
            return None, 1e18
        dx, dy = best[0] - x, best[1] - y
        dl = math.hypot(dx, dy) or 1
        return math.degrees(math.atan2(-dx / dl, dy / dl)), bd

    def open_face_rot(self, cx: float, cy: float, w: float, h: float, clear_ft: float = 8.0, prefer: Any = (0, 180, 270, 90)) -> float | None:
        """The rotation whose DOOR side (the local +h/2 face) opens onto clear ground - or None
        if every cardinal is walled in. GM doctrine (2026-07-18): a farmhouse always faces SOUTH
        (its garden and threshing ground need the sun), but a CITY house has no sun constraint
        and must instead have an UNBLOCKED entrance - the door faces open space (street, roji,
        court), never the back of another building an eave-gap away. Tries `prefer` in order and
        returns the first whose door-front band (`clear_ft` real feet deep) contains no placed
        footprint; conservative AABB test against self.placed (rotated neighbors are close
        enough to axis-aligned at row scales for a placement-time choice - the gate check does
        the exact geometry)."""
        clear = self.px(clear_ft)
        for rot in prefer:
            th = math.radians(rot)
            ux, uy = -math.sin(th), math.cos(th)
            fx, fy = cx + ux * h / 2, cy + uy * h / 2
            ok = True
            for ox, oy, ow, oh in self.placed:
                if abs(ox - cx) > (w + ow) / 2 + clear + 2 or abs(oy - cy) > (h + oh) / 2 + clear + 2:
                    continue
                for d in (1.0, clear * 0.55, clear):
                    for t in (-0.3 * w, 0.0, 0.3 * w):
                        px_, py_ = fx + ux * d - uy * t, fy + uy * d + ux * t
                        if abs(px_ - ox) < ow / 2 and abs(py_ - oy) < oh / 2:
                            ok = False
                            break
                    if not ok:
                        break
                if not ok:
                    break
            if ok:
                return float(rot)
        return None

    def rowpack(self, bbox: Any, items: Any, court_every: int = 2, court_ft: float = 21, eave_ft: float = 4, seam: float = 0.4) -> int:
        """CITY row housing - the machiya/nagaya fabric (GM row-packing doctrine, 2026-07):
        urban commoners did not build detached-with-yard; street frontage was taxed and precious,
        back-lot nagaya were literally one roof over a row of family units, and Chinese county-seat
        housing shared party walls in continuous street walls. So dwellings go down as CONTIGUOUS
        TERRACES, not a scatter:
          - rows run E-W; houses TOUCH within a row (a hairline `seam` of 0.4px keeps the SAT
            overlap gate honest - independent structures grown together, outlines merging into
            a terrace strip);
          - rows come in BACK-TO-BACK PAIRS with both doors facing OUTWARD (GM doctrine
            2026-07-18): the first row of a pair faces UP (rot 180), the second DOWN (rot 0),
            their backs sharing the ~3-6 ft eave/drainage gap (`eave_ft` - rain drip, gutter,
            night-soil access - NOT an entrance). A city house has no farmhouse-style
            south-facing sun constraint; what it must have is an unblocked entrance;
          - after every pair a WALKABLE gap opens - a roji lane (~12 ft) by default, widening
            to a COURT (`court_ft`, ~15-25 ft, the idobata courtyard) every ~`court_every`
            rows - so rows never stack more than TWO deep and no household is trapped behind
            another (the city_house_doors_unblocked / city_rows_max_two_deep gates);
          - rows front the caller's roji/alleys TIGHTLY (a real roji had walls you could touch
            from its centerline) but stand a frontage-band back from real streets and the road,
            where the shop rows live. Draw the zone's alleys BEFORE calling this.
        Streets/roads/prior placements break a row naturally (the odd firebreak gap is
        historically honest). Dwelling sizes come from URBAN kinds via bscale, with mild
        per-house jitter so the terrace reads grown-up-over-time, not stamped.
        Returns the number placed."""
        x0, y0, x1, y1 = bbox
        items = list(items)
        n0 = len(self.placed)  # obstacle snapshot: everything placed BEFORE this call
        court_px, eave_px = self.px(court_ft), max(self.px(eave_ft), 1.2)
        roji_px = max(self.px(12), 4.5)  # the walkable between-pairs lane: >= ~12 real ft, floored for legibility (vs the ~7 ft door-clear line the checks enforce)
        # linework the rows must respect: tight against alleys (roji), a frontage band off
        # streets/roads (the shop rows own that ground)
        lines = [(al["pts"], al.get("w", 10) / 2 + max(self.px(3), 2.5)) for al in self.M.get("alleys", [])]  # 2.5 >= the overlap gate's +2 margin
        lines += [(st["pts"], st.get("w", 18) / 2 + self.px(28)) for st in self.M.get("town_streets", [])]
        if self.M.get("road"):
            lines.append((self.M["road"], self.M.get("road_width", 26) / 2 + self.px(28)))
        if self.M.get("ring_road"):
            lines.append((self.M["ring_road"], self.M.get("ring_road_width", 7) / 2 + max(self.px(3), 2.5)))

        def seg_hits_rect(a: Any, b: Any, rx0: float, ry0: float, rx1: float, ry1: float) -> bool:
            # slab-clip the segment against the rect (exact for axis-aligned rects)
            (ax, ay), (bx, by) = a, b
            dx, dy = bx - ax, by - ay
            t0, t1 = 0.0, 1.0
            for p, q in ((-dx, ax - rx0), (dx, rx1 - ax), (-dy, ay - ry0), (dy, ry1 - ay)):
                if p == 0:
                    if q < 0:
                        return False
                else:
                    t = q / p
                    if p < 0:
                        if t > t1:
                            return False
                        t0 = max(t0, t)
                    else:
                        if t < t0:
                            return False
                        t1 = min(t1, t)
            return True

        def rect_ok(cx: float, cy: float, w: float, h: float) -> bool:
            corners = [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]
            for px_, py_ in corners + [(cx, cy)]:
                if px_ < 55 or px_ > self.W - 55 or py_ < 88 or py_ > self.H - 26:
                    return False
                if self.bound and not point_in_poly(px_, py_, self.bound):
                    return False
                if self._in_blocked(px_, py_):
                    return False
            for pts, half in lines:  # exact rect-vs-polyline clearance (a corner
                ex0, ey0 = cx - w / 2 - half, cy - h / 2 - half  # sample would miss a lane crossing
                ex1, ey1 = cx + w / 2 + half, cy + h / 2 + half  # between two corners)
                for k in range(len(pts) - 1):
                    if seg_hits_rect(pts[k], pts[k + 1], ex0, ey0, ex1, ey1):
                        return False
            r = math.hypot(w, h) / 2
            return all(math.hypot(cx - ox, cy - oy) >= r + math.hypot(ow, oh) / 2 + 1 for ox, oy, ow, oh in self.placed[:n0])

        n, idx, row = 0, 0, 0
        ytop = y0
        while items and idx < len(items):
            rowmax = 0.0
            x = x0 + self._hjit(x0, ytop, 0.7) * 4  # ragged row starts (not a stamped grid)
            while x < x1 and idx < len(items):
                kind = items[idx]
                bw, bh = self._dims(kind)
                bw *= 0.94 + self._hjit(x, ytop, 1.3) * 0.24  # grown-over-time variation, still touching
                bh *= 0.95 + self._hjit(x, ytop, 2.1) * 0.15
                if x + bw > x1:
                    break
                cx, cy = x + bw / 2, ytop + bh / 2
                if rect_ok(cx, cy, bw, bh):
                    # pair-facing doctrine: first row of each pair faces UP (door at its top
                    # edge, onto the walkable gap above), second faces DOWN - backs meet
                    # across the eave gap, every door opens outward onto roji/court ground
                    self.building(cx, cy, bw, bh, kind, 180 if row % 2 == 0 else 0)
                    n += 1
                    idx += 1
                    rowmax = max(rowmax, bh)
                    x += bw + seam  # party wall: the next unit starts AT this one's gable
                else:
                    x += 5  # an obstacle breaks the terrace; scan past it
            if rowmax == 0.0:
                rowmax = self._dims("laborer")[1]  # an entirely-blocked row still advances
            row += 1
            if row % 2 == 1:
                gap = eave_px  # inside a pair: the back-to-back eave/drainage gap
            elif (row // 2) % max(1, round(court_every / 2)) == 0:
                gap = court_px  # a full idobata court every ~court_every rows
            else:
                gap = roji_px  # between pairs: a walkable roji so both pair-fronts have entrance ground
            ytop += rowmax + gap
            if ytop + self._dims("laborer")[1] > y1:
                break
        return n

    def pack(self, bbox: Any, items: Any, rot: float = 0, step: float = 46, face_streets: Any = False) -> int:
        """Densely fill a district bbox with a list of building kinds (one building
        each), grid-scan + jitter, skipping the road, blocked regions, and occupied
        spots. With face_streets, each building rotates to face its nearest street.
        Returns the number placed (leftovers are 'off-map')."""
        x0, y0, x1, y1 = bbox
        items = list(items)
        n = 0
        gy = y0 + step / 2
        while gy < y1 and items:
            gx = x0 + step / 2
            while gx < x1 and items:
                jx, jy = random.uniform(-step * 0.28, step * 0.28), random.uniform(-step * 0.28, step * 0.28)
                if face_streets:
                    fr, fd = self._face_street_rot(gx + jx, gy + jy)
                    if face_streets == "core":
                        if fr is not None and fd <= 76:
                            gx += step  # leave the street-facing band for shop frontage; dwellings pack the INTERIOR
                            continue
                        r = rot + random.uniform(-6, 6)  # ONLY the deep block core, set back behind the frontage line
                    elif fr is not None and fd <= 92:
                        r = fr + random.uniform(-4, 4)  # near a street: face it
                    elif face_streets == "fill":
                        r = rot + random.uniform(-6, 6)  # deep block core (e.g. tenement housing)
                    else:
                        gx += step  # businesses only line the frontage
                        continue
                else:
                    r = rot + random.uniform(-6, 6)
                # a scattered (non-street-facing) house still needs an UNBLOCKED door: keep the
                # street-facing rotation when one was chosen, else pick the cardinal whose door
                # side opens onto clear ground (doctrine 2026-07-18; skip a spot walled on all 4).
                # RNG-NEUTRAL by construction: the prefer order starts at the pack's own base
                # rotation and the already-drawn jitter is REUSED (no extra random draws), so a
                # map whose scatter never actually blocks a door regenerates bit-identically to
                # the pre-doctrine engine - the doctrine only perturbs the spots it must.
                if not (face_streets and fr is not None and fd <= 92):
                    w_, h_ = self._dims(items[0])
                    base = (round(rot / 90) * 90) % 360
                    orot = self.open_face_rot(gx + jx, gy + jy, w_, h_, prefer=(base, (base + 180) % 360, (base + 270) % 360, (base + 90) % 360))
                    if orot is None:
                        gx += step
                        continue
                    r = orot + (r - rot)
                if self.try_building(gx + jx, gy + jy, items[0], r):
                    items.pop(0)
                    n += 1
                gx += step
            gy += step
        return n

    def pasture(self, shape: Any, label: Any = None, amp: float = 40, label_xy: Any = None) -> None:
        """Hayfield / grazing land (pastureland, around the barns) - open grass with
        the odd hay bale, distinct from the cultivated paddy fields. Blocks placement."""
        outline = organic_bbox(shape, amp) if len(shape) == 4 and all(isinstance(v, (int, float)) for v in shape) else organic_poly(shape, amp)
        sm = smooth_points(outline)
        d = smooth_closed(outline)
        cid = self._cid('past')
        self.add(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
        self.add(f'<path d="{d}" fill="#C8CF92" stroke="#9CA86A" stroke-width="2" stroke-dasharray="7,5"/>')
        xs, ys = [p[0] for p in sm], [p[1] for p in sm]
        st = random.getstate()
        random.seed(15)
        self.add(f'<g clip-path="url(#{cid})">')
        yy = min(ys) + 14
        while yy < max(ys):
            xx = min(xs) + 14
            while xx < max(xs):
                tx, ty = xx + random.uniform(-7, 7), yy + random.uniform(-7, 7)
                if point_in_poly(tx, ty, sm):
                    if random.random() < 0.10:
                        self.add(f'<rect x="{tx - 6:.0f}" y="{ty - 4:.0f}" width="12" height="8" rx="3" fill="#D8C47E" stroke="#A98E54" stroke-width="0.7"/>')
                    else:
                        self.add(f'<path d="M{tx - 3:.0f},{ty + 2:.0f} L{tx:.0f},{ty - 4:.0f} L{tx + 3:.0f},{ty + 2:.0f}" fill="none" stroke="#8FA05E" stroke-width="0.8"/>')
                xx += 26
            yy += 24
        self.add('</g>')
        random.setstate(st)
        self.block_polys.append(sm)
        self.M.setdefault("pastures", []).append([[round(p[0], 1), round(p[1], 1)] for p in sm])
        if label:
            lx, ly = label_xy if label_xy else ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
            self.label(lx, ly, label, 12, italic=True, color="#5C6B3A")

    def theater_stage(self, cx: float, cy: float, w: Any = None, h: Any = None, rot: float = 0, label: Any = None) -> None:
        """A public THEATER STAGE: a roofed raised stage facing an open viewing ground - the troupe-and-
        festival venue of a Rokugani town/city (the East Asian analog of a Greco-Roman amphitheater: a
        temple OPERA STAGE / shrine NOH-kagura stage). It belongs to a temple/monastery precinct, the
        audience gathering in the open ground between the stage and the hall. (cx,cy) is the center of the
        w x h viewing ground; the roofed stage sits at the -y (north) end facing +y into it; `rot` turns the
        whole feature (point it so the ground opens toward the temple). Records M['theater_stage']; reserves
        its footprint so packing avoids it."""
        if w is None:
            w, h = self.px(150), self.px(105)  # stage + viewing ground ~150x105 ft (town-calibrated)
        hw, hh = w / 2, h / 2
        sw, sh = w * 0.5, h * 0.26  # the roofed stage at the north end
        sy = -hh - sh * 0.5  # straddling the ground's north edge
        g = [f'<g transform="translate({cx:.1f},{cy:.1f}) rotate({rot:.1f})">']
        g.append(f'<rect x="{-hw:.0f}" y="{-hh:.0f}" width="{w:.0f}" height="{h:.0f}" rx="4" fill="#E4D6B0" stroke="#A98E54" stroke-width="1.5"/>')  # the swept earthen viewing ground
        g.append(f'<rect x="{-hw + 5:.0f}" y="{-hh + 5:.0f}" width="{w - 10:.0f}" height="{h - 10:.0f}" rx="3" fill="none" stroke="#C9B484" stroke-width="0.7" opacity="0.6"/>')
        for i in range(3):  # a few faint rows of standing crowd in the ground
            ry = -hh + h * (0.40 + 0.17 * i)
            for k in range(7):
                px = -hw + 14 + (w - 28) * (k + 0.5) / 7
                g.append(f'<circle cx="{px:.0f}" cy="{ry:.0f}" r="1.7" fill="#8A7A56" opacity="0.5"/>')
        g.append(f'<rect x="{-sw / 2:.0f}" y="{sy:.0f}" width="{sw:.0f}" height="{sh:.0f}" rx="2" fill="#C9A57A" stroke="#5A3F1E" stroke-width="1.8"/>')  # stage platform
        g.append(f'<rect x="{-sw / 2:.0f}" y="{sy:.0f}" width="{sw:.0f}" height="{sh * 0.36:.0f}" fill="#7A5A30"/>')  # its roof
        g.append(f'<circle cx="0" cy="{sy + sh * 0.56:.0f}" r="{sh * 0.24:.0f}" fill="#6E8B4A" opacity="0.6"/>')  # a hint of the painted pine backdrop
        g.append(f'<rect x="{-sw / 2:.0f}" y="{sy + sh - 2.5:.0f}" width="{sw:.0f}" height="2.5" fill="#5A3F1E" opacity="0.6"/>')  # stage-front lip onto the ground
        g.append('</g>')
        self.add(''.join(g))
        self.M["theater_stage"] = {"x": cx, "y": cy, "w": w, "h": h, "rot": rot}
        R = math.hypot(hw, hh) + sh * 0.5  # rotation-safe covering radius (stage + ground)
        self.ellipses.append((cx, cy, R, R))
        if label:
            self.label(cx, cy + hh + 16, label, 11, italic=True)

    def fire_tower(self, x: float, y: float, tw: float | None = None, rot: float = 0.0, label: str = "fire tower") -> int:
        """A HINOMI-YAGURA (fire-watch tower): a tall, slender braced-timber tower with a lookout
        platform and an alarm bell (hansho), standing in the dense COMMONER quarter of a walled
        town or city where packed wooden rooftops make fire catastrophic. It is a CIVILIAN interior
        structure - the magistrate's fire-watch - distinct from a wall guard tower (military, on the
        rampart): drawn as an OPEN braced frame (not the guard tower's solid block) with a red bell.
        The watchman strikes the bell in a cadence that tells the town how near the fire is. Records
        M['fire_towers'] (an overlap-checked struct: it must stand clear of the wall, roads, and
        buildings) and reserves a small no-build block (it needs clear sightlines). Place it among the
        laborer/merchant blocks. See the settlements.md 'Fire towers' historical grounding."""
        if tw is None:
            tw = self.px(26)  # a real hinomi-yagura frame is ~26 ft square (town-calibrated glyph)
        h = tw / 2
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        g.append(f'<rect x="{-h - 2:.0f}" y="{-h - 5:.0f}" width="{tw + 4}" height="5" rx="1" fill="#7A5A30"/>')  # the little roof cap over the lookout platform
        g.append(f'<rect x="{-h:.0f}" y="{-h:.0f}" width="{tw}" height="{tw}" fill="#EFE6CC" fill-opacity="0.45" stroke="#7A5A30" stroke-width="2"/>')  # the open braced-timber frame
        g.append(f'<line x1="{-h:.0f}" y1="{-h:.0f}" x2="{h:.0f}" y2="{h:.0f}" stroke="#7A5A30" stroke-width="1.1"/>')  # cross-braces (an X)
        g.append(f'<line x1="{h:.0f}" y1="{-h:.0f}" x2="{-h:.0f}" y2="{h:.0f}" stroke="#7A5A30" stroke-width="1.1"/>')
        g.append(f'<circle cx="0" cy="0" r="{tw * 0.2:.1f}" fill="#B0462F" stroke="#5A3F1E" stroke-width="0.8"/>')  # the alarm bell (hansho)
        g.append('</g>')
        z = self.add_top(''.join(g))
        self.M["fire_towers"].append({"x": round(x, 1), "y": round(y, 1), "w": tw, "h": tw, "rot": round(rot, 1), "z": z, "label": label})
        self.placed.append((x, y, tw, tw))
        bm = 16
        self.block_polys.append([(x - h - bm, y - h - bm), (x + h + bm, y - h - bm), (x + h + bm, y + h + bm), (x - h - bm, y + h + bm)])
        if label:
            self.label(x, y + h + 14, label, 9, italic=True, color="#7A5A30")
        return z

    def _draw_threshing_yard(self, cx: float, cy: float, w: float, h: float, poly: Any) -> None:
        """Draw one small tamped earthen threshing/drying yard (a straw mat + a little hazakake rack). The
        outer footprint is a slightly-irregular quad (`poly`, absolute corner coords) - a swept work surface
        stays NEAR-square; interior detail is laid out in the local (w,h) frame."""
        x0, y0 = -w / 2, -h / 2
        g = [f'<g transform="translate({cx:.0f},{cy:.0f})">']
        pts = " ".join(f"{px - cx:.1f},{py - cy:.1f}" for px, py in poly)
        g.append(f'<polygon points="{pts}" fill="#D2BE94" stroke="#A98E54" stroke-width="1.5"/>')  # tamped earthen floor
        g.append(f'<rect x="{x0 + 3:.0f}" y="{y0 + 3:.0f}" width="{w - 6:.0f}" height="{h - 6:.0f}" rx="1.5" fill="none" stroke="#BBA06E" stroke-width="0.7" opacity="0.6"/>')  # swept rim
        g.append('<rect x="-7" y="-6" width="14" height="9" rx="1" fill="#E2D2A2" stroke="#A98E54" stroke-width="0.6" opacity="0.9"/>')  # a straw drying mat
        ry = h / 2 - 3  # a little drying rack (hazakake) along the floor's lower edge
        g.append(f'<line x1="{x0 + 4:.1f}" y1="{ry:.1f}" x2="{-x0 - 4:.1f}" y2="{ry:.1f}" stroke="#7A5A30" stroke-width="1.2"/>')
        g.append(f'<line x1="{x0 + 4:.1f}" y1="{ry - 3:.1f}" x2="{-x0 - 4:.1f}" y2="{ry - 3:.1f}" stroke="#7A5A30" stroke-width="1.0"/>')
        for px in (x0 + 4, 0.0, -x0 - 4):  # posts + a few hung sheaves
            g.append(f'<line x1="{px:.1f}" y1="{ry - 5:.1f}" x2="{px:.1f}" y2="{ry + 3:.1f}" stroke="#5A3F1E" stroke-width="1.2"/>')
        g.append('</g>')
        self.add(''.join(g))

    def _yard_fits(self, x: float, y: float, w: float, h: float, hx: float, hy: float) -> bool:
        """A threshing yard fits where it is in-bounds, on DRY ground (clear of paddies / blocks),
        off any lane, and clear of every placed footprint EXCEPT its own farmhouse (it abuts that)."""
        if x < 55 or x > self.W - 55 or y < 88 or y > self.H - 26:
            return False
        if self.bound and not point_in_poly(x, y, self.bound):
            return False
        if self._in_blocked(x, y) or self._near_corridor(x, y):
            return False
        if self._rect_hits((x, y, w, h), self.dry_polys):  # hem strips / garden tracts are cropland too -
            return False  # the yard footprint stays off them, same as the house test in _fits (GM, Tango hems)
        r = math.hypot(w, h) / 2
        for poly in self.field_polys:  # keep the whole DRY footprint out of every paddy
            if point_in_poly(x, y, poly) or edge_dist(x, y, poly) < r + 4:
                return False
        for px, py, pw, ph in self.placed:
            if px == hx and py == hy:  # the yard abuts its OWN farmhouse - allowed
                continue
            if math.hypot(x - px, y - py) < r + math.hypot(pw, ph) / 2 + 2:
                return False
        return True

    def _yard_dims(self, hw: float, hh: float) -> tuple[float, float]:
        """PREVIEW: yard scaled to the (now smaller) house, capped so the big headman keeps an ordinary yard."""
        return min(0.73 * hw, 32 * self.bscale), min(0.69 * hh, 20 * self.bscale)

    def _find_yard_spot(self, hx: float, hy: float, hw: float, hh: float) -> tuple[float, float, float, float] | None:
        """The first fitting threshing-yard position for a farmhouse: the sunny SOUTH/front side (+y) is
        the maeniwa; fall back to the E/W sides if the paddy blocks due-south, but NEVER the shady north
        back. Returns (ox, oy, yw, yh) or None if the farmstead is boxed in on all three sides."""
        yw, yh = self._yard_dims(hw, hh)
        for dx, dy in ((0, 1), (1, 0), (-1, 0)):
            ox = hx + dx * (hw / 2 + yw / 2 - 2)
            oy = hy + dy * (hh / 2 + yh / 2 - 2)
            if self._yard_fits(ox, oy, yw, yh, hx, hy):
                return ox, oy, yw, yh
        return None

    def _attach_yard(self, hx: float, hy: float, spot: Any) -> None:
        """Draw a farmstead's threshing/drying yard (it is drawn BEFORE its house, so the house renders on
        top of the overlap) and record it. The work yard was UNIVERSAL, so every farmhouse gets one. Its
        footprint is a SLIGHTLY-irregular quad (a swept work surface stays near-square: small jitter),
        inscribed in the reserved rect so it can never breach the collision the rect already cleared."""
        ox, oy, yw, yh = spot
        poly = self._quad(ox, oy, yw, yh, 0.10, 41.0)
        self._draw_threshing_yard(ox, oy, yw, yh, poly)
        self.M["threshing_yards"].append({"x": round(ox, 1), "y": round(oy, 1), "w": yw, "h": yh, "rot": 0, "of": [hx, hy], "poly": [[round(px, 1), round(py, 1)] for px, py in poly]})
        self.placed.append((ox, oy, yw, yh))

    def _draw_garden(self, cx: float, cy: float, w: float, h: float, poly: Any) -> None:
        """Draw one small dooryard KITCHEN GARDEN (saien): a tilled earthen bed with tidy planted rows
        of greens. Distinct from the tan threshing yard (bare swept earth) and the blue-green paddy quilt.
        The bed's outer footprint is an irregular quad (`poly`, absolute corner coords) - a hand-worked plot
        bent to paths and soil, not surveyed square; the rows are laid out in the local (w,h) frame."""
        x0, y0 = -w / 2, -h / 2
        g = [f'<g transform="translate({cx:.0f},{cy:.0f})">']
        pts = " ".join(f"{px - cx:.1f},{py - cy:.1f}" for px, py in poly)
        g.append(f'<polygon points="{pts}" fill="#B49A62" stroke="#6E5A30" stroke-width="1.3"/>')  # tilled bed
        nrows = 3
        for i in range(nrows):  # rows of greens running along the bed
            ry = y0 + h * (i + 0.5) / nrows
            g.append(f'<line x1="{x0 + 3:.1f}" y1="{ry:.1f}" x2="{-x0 - 3:.1f}" y2="{ry:.1f}" stroke="#6E9A40" stroke-width="2.4" stroke-linecap="round"/>')
            for k in range(3):  # a few leafy plants dotted along each row
                px = x0 + 4 + (w - 8) * (k + 0.5) / 3
                g.append(f'<circle cx="{px:.1f}" cy="{ry:.1f}" r="1.7" fill="#83B255"/>')
        g.append('</g>')
        self.add(''.join(g))

    def _garden_dims(self, hw: float, hh: float) -> tuple[float, float]:
        """PREVIEW: garden scaled to the (now smaller) house, capped."""
        return min(0.55 * hw, 24 * self.bscale), min(0.55 * hh, 16 * self.bscale)

    def _farm_shed_rect(self, hx: float, hy: float, hw: float, hh: float, rot: float, kind: str, shed: Any) -> tuple[float, float, float, float] | None:
        """The footprint of a plain farmhouse's attached STOREHOUSE/shed (kura), drawn as a sub-glyph on
        the house's WEST side (local -x), or None if it has none. Derived here (the shed is not a separate
        recorded struct) so the garden can be kept OFF it - shed and garden sit on opposite sides."""
        if not (shed and kind == "plain"):
            return None
        th = math.radians(rot)
        lx = -0.64 * hw  # shed center in the house's local frame (west side)
        return (hx + lx * math.cos(th), hy + lx * math.sin(th), 0.32 * hw, 0.56 * hh)

    def _garden_fits(self, x: float, y: float, w: float, h: float, hx: float, hy: float, yard: Any, shed_rect: Any = None) -> bool:
        """A garden fits where it is in-bounds, on DRY ground (clear of paddies / blocks), off any lane,
        clear of every placed footprint EXCEPT its own farmhouse, clear of that farmhouse's YARD, and clear
        of its SHED (the yard, shed, and garden all sit on different sides of the house, never overlapping)."""
        if x < 55 or x > self.W - 55 or y < 88 or y > self.H - 26:
            return False
        if self.bound and not point_in_poly(x, y, self.bound):
            return False
        if self._in_blocked(x, y) or self._near_corridor(x, y):
            return False
        r = math.hypot(w, h) / 2
        for poly in self.field_polys:  # a kitchen garden is dry ground, off the paddies
            if point_in_poly(x, y, poly) or edge_dist(x, y, poly) < r + 4:
                return False
        if math.hypot(x - yard[0], y - yard[1]) < r + math.hypot(yard[2], yard[3]) / 2 + 2:
            return False  # not on top of this house's own threshing yard
        if shed_rect and math.hypot(x - shed_rect[0], y - shed_rect[1]) < r + math.hypot(shed_rect[2], shed_rect[3]) / 2 + 2:
            return False  # not on top of this house's own storehouse/shed (its west side)
        for px, py, pw, ph in self.placed:
            if px == hx and py == hy:  # the garden abuts its OWN farmhouse - allowed
                continue
            if math.hypot(x - px, y - py) < r + math.hypot(pw, ph) / 2 + 2:
                return False
        return True

    def _find_garden_spot(self, hx: float, hy: float, hw: float, hh: float, yard: Any, shed_rect: Any = None, wealth: float = 1.0) -> tuple[float, float, float, float] | None:
        """The first fitting kitchen-garden position: a sunny SIDE, preferring the EAST (the kitchen/doma
        end, where the cook steps out to it), then the sunny SE/SW corners, and the windward WALL itself
        LAST - NEVER the shady north back, and never the south front (the threshing yard's apron) nor the west
        shed. The grove's belt sits on the windward WALL (the W face for the default NW wind), so the garden
        takes that wall only as a last resort - the windward CORNER (SW) is still fine, it tucks below the
        grove's arm. Keeping the garden off the windward wall is what frees it for the grove (a garden there
        was the #1 reason a windward arm went missing - e.g. a farm whose EAST faces the paddy). Spot or None."""
        gw, gh = self._garden_dims(hw * wealth, hh * wealth)  # PREVIEW: richer farm -> bigger garden
        wx = self._windward_x()  # windward horizontal sign (-1 W / +1 E / 0)
        wall = (wx, 0) if wx else None  # the windward wall the grove's belt wants
        sides = [(1, 0), (-1, 0), (1, 1), (-1, 1)]
        # try EVERY non-windward-wall side first - flush AND a little further out (to slip the garden past the
        # south yard into the windward CORNER) - and the windward wall itself only as a last resort, so an
        # E-paddy farm puts its garden in the SW corner and leaves the W wall free for the grove
        cands = [(dx, dy, e) for dx, dy in sides if (dx, dy) != wall for e in (0, 15 * self.bscale, 30 * self.bscale)]
        if wall:
            cands += [(wall[0], wall[1], e) for e in (0, 15 * self.bscale)]
        for dx, dy, extra in cands:
            ox = hx + dx * (hw / 2 + gw / 2 - 2 + extra)
            oy = hy + dy * (hh / 2 + gh / 2 - 2)
            if self._garden_fits(ox, oy, gw, gh, hx, hy, yard, shed_rect):
                return ox, oy, gw, gh
        return None

    def _attach_garden(self, hx: float, hy: float, beds: Any) -> None:
        """Draw a farmstead's dooryard kitchen garden BED(S) (before its house, so the house wins any abutment)
        and record them. The kitchen garden was a household staple, so every farmhouse gets one - but the plot
        is occasionally FRAGMENTED into two beds (`_garden_beds` decides where: flanking opposite walls, stacked,
        or side-by-side). `beds` is the reserved-and-collision-checked list of (cx,cy,w,h) rects from the bundle
        geometry; all beds of one house carry the same `of` parent, so `gardens_present` counts one garden per
        house and `garden_area_within_norms` sums their areas. Each bed is drawn as a slightly-irregular hand-
        worked quad (real dooryard beds were bent to paths and soil, not surveyed square); a lone bed can be more
        irregular than a split strip."""
        jit = 0.18 if len(beds) == 1 else 0.13
        for i, (bx, by, bw, bh) in enumerate(beds):
            poly = self._quad(bx, by, bw, bh, jit, 71.0 + i * 5.0)
            self._draw_garden(bx, by, bw, bh, poly)
            self.M["gardens"].append({"x": round(bx, 1), "y": round(by, 1), "w": bw, "h": bh, "rot": 0, "of": [hx, hy], "poly": [[round(px, 1), round(py, 1)] for px, py in poly]})
            self.placed.append((bx, by, bw, bh))

    # the windward faces a homestead grove (yashikirin) shelters, by where the prevailing cold wind comes
    # FROM (its compass key). The grove is an L-BELT: a deep stand on each windward face (for a diagonal
    # like NW, an N arm + a W arm wrapping the corner; for a cardinal, one deep band). Default NW - the
    # East Asian winter monsoon (the Siberian high) blows NW across China AND Japan, so N+W is windward and
    # the S/E is the sheltered, sunny side. A map keys it off its geography with meta(windward=...). Each
    # arm is (face, perp): `face` is the cardinal it sits on; `perp` is the sign the N/S arm extends along
    # to wrap the corner (0 for a lone cardinal arm). See settlements.md 'Homestead groves'.
    _GROVE_ARMS = {
        "NW": [((0, -1), -1), ((-1, 0), 0)],
        "NE": [((0, -1), 1), ((1, 0), 0)],
        "SW": [((0, 1), -1), ((-1, 0), 0)],
        "SE": [((0, 1), 1), ((1, 0), 0)],
        "N": [((0, -1), 0)],
        "S": [((0, 1), 0)],
        "E": [((1, 0), 0)],
        "W": [((-1, 0), 0)],
    }

    def _windward(self) -> str:
        """The map's prevailing-wind compass key (where the cold wind blows FROM), default NW."""
        w = str(self.M["meta"].get("windward", "NW")).upper().strip()
        return w if w in self._GROVE_ARMS else "NW"

    def _windward_x(self) -> int:
        """The horizontal sign of the windward direction: -1 if the wind is from the W (NW/W/SW), +1 if from
        the E (NE/E/SE), 0 for a due N/S wind. Used to keep the garden off the windward wall (the grove's side)."""
        wk = self._windward()
        return -1 if "W" in wk else (1 if "E" in wk else 0)

    def _grove_candidate(self, hx: float, hy: float) -> bool:
        """Whether this farmhouse is a grove candidate. UNIVERSAL by default (the yashikirin ringed every
        dispersed farmstead, so a grove is drawn wherever there is windward room); meta(grove_prevalence=N<1)
        dials it down for an atypical/sheltered microclimate. Deterministic in the house position (stable
        across regenerations, RNG-independent)."""
        rate = float(self.M["meta"].get("grove_prevalence", 1.0))
        return rate >= 1.0 or int(abs(hx) * 31 + abs(hy) * 17) % 100 < rate * 100

    def _grove_arm_rect(self, hx: float, hy: float, hw: float, hh: float, fdx: float, fdy: float, perp: float, d: float, gap: float, lf: float = 1.0) -> tuple[float, float, float, float]:
        """One belt ARM's footprint (cx, cy, w, h), depth `d`, just outside the house wall it shelters. An
        N/S arm runs E-W as wide as the house plus `d` (extending `perp` toward the windward corner so the
        two arms wrap it); an E/W arm runs N-S as tall as the house. The depth `d` is how many trees deep the
        stand is - sized so the whole grove is the LARGEST homestead appurtenance (bigger than the house);
        `lf` shortens the arm's run to slip a partial belt past a close neighbor. See settlements.md 'Homestead
        groves' (Historical scale)."""
        if fdy:  # N or S arm (runs E-W); wraps `perp` toward the windward corner
            return hx + perp * d / 2, hy + fdy * (hh / 2 + d / 2 + gap), (hw + d) * lf, d
        return hx + fdx * (hw / 2 + d / 2 + gap), hy, d, hh * lf  # E or W arm (runs N-S)

    def _grove_fits(self, x: float, y: float, w: float, h: float, own: Any) -> bool:
        """A grove fits where it is in-bounds, on DRY ground (trees do not grow IN a flooded paddy - but a real
        homestead grove HUGS the paddy bund, so the footprint may abut a field, it just may not overlap it),
        off any lane, and clear of every placed footprint EXCEPT its OWN house. Axis-aligned, so an exact AABB
        test serves - not the conservative half-diagonal circle, which would over-reject the elongated bands."""
        if x < 55 or x > self.W - 55 or y < 88 or y > self.H - 26:
            return False
        if self.bound and not point_in_poly(x, y, self.bound):
            return False
        if self._near_corridor(x, y):  # NOT `_in_blocked`: a grove may sit right at the
            return False  # paddy edge (the 14px field set-back is for buildings, not the windbreak)
        if self._rect_hits((x, y, w, h), self.field_polys):  # the whole grove stays OUT of the flooded paddy
            return False  # (same corner/vertex/edge test, with the bbox pre-filter)
        if self._rect_hits((x, y, w, h), self.dry_polys):  # ...and out of the dry crop strips (hems / garden
            return False  # tracts): trees do not grow in the barley either
        for px, py, pw, ph in self.placed:  # clear of every footprint but its OWN homestead
            if any(abs(px - ox) < 1.5 and abs(py - oy) < 1.5 for ox, oy in own):
                continue
            if abs(x - px) < (w + pw) / 2 + 2 and abs(y - py) < (h + ph) / 2 + 2:
                return False
        # the town RAMPART blocks a belt arm at the FOOTPRINT level: the corridor test above is
        # center-only, so a wide arm centered clear of the wall could still lap the stroke
        # (first hit: a Hirameki farm's west arm crossing the east face, 2026-07)
        wallp = self.M.get("wall")
        if wallp and any(
            seg_dist(gx, gy, wallp[k], wallp[k + 1]) < 12 for gx, gy in ((x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)) for k in range(len(wallp) - 1)
        ):
            return False
        # a threshing yard needs clear sky to its SOUTH (the drying sun); a grove squarely in that sun-corridor
        # would shade it, so keep the grove out of the narrow strip directly south of any yard. (Its OWN grove
        # is N/W, far from its own yard's southern corridor, so this only steers it off a NEIGHBOR's yard.)
        for yd in self.M.get("threshing_yards", []):
            cyx, cyy = yd["x"], yd["y"] + yd["h"] / 2 + 11  # corridor center: a ~22px-deep strip south of the yard
            if abs(x - cyx) < (w + yd["w"]) / 2 and abs(y - cyy) < (h + 22) / 2:
                return False
        return True

    GROVE_RATIO = 6.0  # target grove footprint as a multiple of the house (~6:1 - see settlements.md Historical scale)

    def _find_grove_arms(self, hx: float, hy: float, hw: float, hh: float) -> list[Any]:
        """The windward grove's belt arms, AREA-TARGETED to ~GROVE_RATIO x the house footprint (the historical
        ~6:1). Each windward face (N + W for an NW wind) is grown to the deepest belt that fits; if the total
        still falls short of target - because a paddy or neighbor blocks one face - the OTHER, open arm is
        deepened to compensate, so a typical farm's grove still reaches the full ~6:1 and reads as ~40 trees.
        A farm boxed in on BOTH windward faces gets only what fits (a small grove - the genuinely cramped
        minority). Arms are NOT in `placed`, so adjacent groves abut into one continuous windbreak. Returns a
        list of (cx, cy, w, h, face)."""
        target = self.GROVE_RATIO * hw * hh
        own = [(hx, hy)]
        d0 = 1.4 * hh  # base belt depth; the loop deepens to hit the area target
        dcap = 3.6 * hh  # an open arm may deepen this far to cover a blocked one
        dmin = 12 * self.bscale
        step = max(2.0, 0.16 * hh)
        depths: list[Any] = []  # [[(fdx,fdy), perp, depth], ...]
        for (fdx, fdy), perp in self._GROVE_ARMS[self._windward()]:
            d = d0
            placed_arm = False
            while d >= dmin:  # deepest full-width arm <= d0 that fits this face
                cx, cy, w, h = self._grove_arm_rect(hx, hy, hw, hh, fdx, fdy, perp, d, 1.5)
                if self._grove_fits(cx, cy, w, h, own):
                    depths.append([(fdx, fdy), perp, d, 1.0])
                    placed_arm = True
                    break
                d -= step
            if not placed_arm:  # tight face: a NARROW clump still reads as a windbreak
                d = d0
                while d >= dmin:
                    cx, cy, w, h = self._grove_arm_rect(hx, hy, hw, hh, fdx, fdy, perp, d, 1.5, 0.55)
                    if self._grove_fits(cx, cy, w, h, own):
                        depths.append([(fdx, fdy), perp, d, 0.55])
                        break
                    d -= step

        def total_area() -> float:
            rects = [self._grove_arm_rect(hx, hy, hw, hh, fdx, fdy, perp, d, 1.5, lf) for (fdx, fdy), perp, d, lf in depths]
            return _union_area([(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2) for cx, cy, w, h in rects])

        guard = 0
        while depths and total_area() < target and guard < 300:  # compensate: deepen the open arm(s)
            grew = False
            for arm in depths:
                if arm[2] >= dcap:
                    continue
                nd = min(dcap, arm[2] + step)
                cx, cy, w, h = self._grove_arm_rect(hx, hy, hw, hh, arm[0][0], arm[0][1], arm[1], nd, 1.5, arm[3])
                if self._grove_fits(cx, cy, w, h, own):
                    arm[2] = nd
                    grew = True
                    if total_area() >= target:
                        break
            if not grew:
                break
            guard += 1
        return [(*self._grove_arm_rect(hx, hy, hw, hh, fdx, fdy, perp, d, 1.5, lf), (fdx, fdy)) for (fdx, fdy), perp, d, lf in depths]

    def _grove_room(self, hx: float, hy: float, hw: float, hh: float) -> bool:
        """Whether at least a MINIMAL grove clump fits on the windward side - used by the homestead solver to
        prefer a house position that leaves room for a grove (the actual, possibly larger, grove is placed in
        the second pass). Mirrors the minimal footprint the `_find_grove_arms` ladder falls back to."""
        for (fdx, fdy), perp in self._GROVE_ARMS[self._windward()]:
            cx, cy, w, h = self._grove_arm_rect(hx, hy, hw, hh, fdx, fdy, perp, 13 * self.bscale, 1.5, 0.5)
            if self._grove_fits(cx, cy, w, h, [(hx, hy)]):
                return True
        return False

    def _draw_grove(self, cx: float, cy: float, w: float, h: float, face: Any, mix: str = "windbreak") -> None:
        """Draw one windbreak/grove clump as a DENSE MIXED STAND - overlapping canopies packed into a real
        grove (not a few scattered trees), of three species: tall EVERGREEN conifer (dark, dense apex - the
        windbreak backbone, cedar/pine), DECIDUOUS broadleaf (mid green - timber and fruit, zelkova/persimmon),
        and a BAMBOO clump (take - fine culms with leafy tops). `mix` picks the species blend: 'windbreak' is
        conifer-backed (the sheltering wall - the yashikirin and the fengshui back belt); 'dooryard' is bamboo
        + fruit broadleaf with NO conifer (the leafy bamboo/fruit greenery scattered among village houses).
        Distinct from the big s.forest area feature and the striped kitchen-garden bed. Species and placement
        are seeded by position (stable across regenerations). Canopy count scales with footprint area."""
        bs = self.bscale / 0.82  # render scale relative to the town grain
        st = random.getstate()
        random.seed(int(abs(cx) * 5 + abs(cy) * 3 + round(w)))
        n = max(5, min(28, round(w * h / (bs * bs * 48))))  # ~ one crown per ~48 px^2 at 2 ft/px (a ~5 m crown); ~40 across the 6:1 L-grove
        b_th, c_th = (0.20, 0.58) if mix == "windbreak" else (0.45, 0.45)  # dooryard = bamboo + fruit, no conifer
        items: list[Any] = []
        for _ in range(n):
            px = random.uniform(-w / 2 + 2, w / 2 - 2)
            py = random.uniform(-h / 2 + 2, h / 2 - 2)
            roll = random.random()
            kind = "bamboo" if roll < b_th else ("conifer" if roll < c_th else "broadleaf")
            size = random.uniform(1.25, 1.7) if random.random() < 0.25 else random.uniform(0.72, 1.05)  # a few emergent crowns over many small
            items.append((px, py, kind, size))
        g = [f'<g transform="translate({cx:.0f},{cy:.0f})">']
        # Draw back-to-front so the stand layers with depth. Each CROWN is one tree at real size (~5-6 m; a few
        # emergents larger) - that is the to-scale reading, and it is unchanged. We deliberately DROP two kinds
        # of detail that cost ~half the stand's SVG elements without buying scale accuracy: the per-tree trunk
        # (hidden under the closed canopy anyway), and the 6-culm bamboo clump - a real *take* is DOZENS of
        # culms, so any handful is already symbolic, and one compact culm+top reads the same. See the foliage
        # comparison (the 'to scale, compact bamboo' option) for the before/after; groves stay to scale, the
        # SVG + rsvg raster roughly halve.
        for px, py, kind, s in sorted(items, key=lambda t: t[1]):
            if kind == "bamboo":  # one compact culm + leafy top (symbolic, was 6)
                g.append(f'<line x1="{px:.1f}" y1="{py + 4 * bs:.1f}" x2="{px:.1f}" y2="{py - 4 * bs:.1f}" stroke="#88A646" stroke-width="{1.4 * bs:.2f}"/>')
                g.append(f'<circle cx="{px:.1f}" cy="{py - 4 * bs:.1f}" r="{3.0 * bs:.1f}" fill="#BBD06A"/>')
                continue
            rr = (4.6 if kind == "conifer" else 4.0) * s * bs  # one crown = one tree, sized to a real ~5-6 m canopy
            col = "#496733" if kind == "conifer" else random.choice(["#7C9A4E", "#6E8B43"])
            g.append(f'<circle cx="{px:.1f}" cy="{py - 3 * bs:.1f}" r="{rr:.1f}" fill="{col}" stroke="#3C5526" stroke-width="0.8"/>')
            if kind == "conifer":
                g.append(f'<circle cx="{px:.1f}" cy="{py - 3 * bs:.1f}" r="{rr * 0.4:.1f}" fill="#364D22" opacity="0.55"/>')  # dense dark apex
        g.append('</g>')
        self.add(''.join(g))
        random.setstate(st)

    def village_grove(self, poly: Any, role: str = "windbreak", dense: bool = True) -> int:
        """A COMMUNAL village grove - the Chinese *fengshui* forest (风水林). Unlike the per-house *yashikirin*,
        a NUCLEATED village shelters behind ONE village-scale grove, in three roles (see settlements.md 'Village
        windbreak'):
          - `windbreak` - the dense belt on the WINDWARD/high BACK edge (后龙林 back-village grove); the winter-
            monsoon wall and the LARGEST vegetation feature. Nestles against and EMBRACES the cluster.
          - `water_mouth` - a smaller cluster of big old trees at the LOW entrance / water-mouth (水口林);
          - `copse` - the leafy bamboo / fruit-tree greenery scattered through the OPEN gaps among the houses.
        `poly` is the grove's FOOTPRINT - an IRREGULAR, terrain-following outline, NOT a rectangle (real groves
        hug the land and wrap the settlement, they are not ruled walls). It is FILLED with dense mixed-stand
        clumps on a jittered grid; a clump is SKIPPED wherever it would land on a HOUSE / threshing YARD /
        GARDEN / PADDY (so the wood settles into the open ground and hugs the cluster without ever drawing trees
        on a building or out in the crops - this is what lets the belt nestle right up to the village edge).
        `dense=True` packs overlapping clumps into a continuous belt/cluster; `dense=False` scatters them for the
        leafy fringe among houses. role tunes the species mix (windbreak/water_mouth = conifer-backed forest;
        copse = bamboo + fruit, no conifer). Recorded in M['village_groves'] (bbox + role + poly) IF any clump
        is drawn (a footprint entirely over houses/crops draws nothing and records nothing). Returns the count."""
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        mix = "windbreak" if role in ("windbreak", "water_mouth") else "dooryard"
        bs = self.bscale
        step = (20 if dense else 52) * bs
        clump = (28 if dense else 22) * bs
        # never draw a clump ON a home/yard/garden/byre/kura: keep the clump CENTER clear by the footprint's
        # circumscribing radius PLUS the clump's own drawn radius (clump/2) and a hair - so the tree blob settles
        # BESIDE the building, touching at most (grove_clumps_clear_of_structures gates it). (A grove may still hug
        # the eaves visually; the blob edge just may not cross the wall.) Was 0.35*clump - too small by ~0.15*clump,
        # which let a blob corner clip a small house.
        occ = [(o["x"], o["y"], 0.5 * math.hypot(o["w"], o["h"]) + clump * 0.5 + 2) for k in ("houses", "threshing_yards", "gardens", "byres", "farm_sheds") for o in self.M.get(k, [])]
        # a WELL is a clean draw-point: no tree CANOPY may reach the wellhead (a well lost under the grove reads
        # wrong - wells_clear_of_trees gates it). Keep-out = the well's DRAWN half-size (vr) + the canopy reach
        # (~0.9*clump, as for a shrine), NOT the tight 0.35*clump a homestead eave gets. (o["r"] is the recorded
        # clearance radius; the DRAWN wellhead is vr, which is what a crown must not overhang.)
        occ += [(o["x"], o["y"], o.get("vr", o["r"]) + clump * 0.90) for o in self.M.get("wells", [])]
        # A SHRINE and its TORII sit in a CLEAN clearing: no tree CANOPY may reach them (a hall/arch lost in the
        # wood reads wrong - shrine_clear_of_grove_trees / torii_clear_of_grove_trees gate it). The DRAWN canopy
        # overhangs the nominal clump radius (crowns spill past clump/2), reaching ~0.85*clump from the clump
        # center - so the keep-out uses that reach + a hair (0.90*clump), NOT the 0.35*clump a homestead uses
        # (there a grove may hug the eaves). A torii is recorded as [x, y, z]; glyph spans x +/-19, y -10..+18.
        occ += [(o["x"], o["y"], 0.5 * math.hypot(o["w"], o["h"]) + clump * 0.90) for k in ("religious", "shrines") for o in self.M.get(k, [])]
        occ += [(t[0], t[1] + 4, math.hypot(19, 14) + clump * 0.90) for t in self.M.get("torii", [])]
        # ... and OFF the fengshui CRESCENT POND (GM 2026-07-21): no tree canopy may cross the half-moon
        # pond's water (trees_clear_of_fengshui_ponds gates it). The keep-out circle spans the FULL disk
        # (radius r + canopy reach) even though the water is only the away-facing half - the flat side toward
        # the village is the pond's open FORECOURT (the banyuetang fronted the settlement's ceremony/work
        # ground), so keeping the copse fringe off that band too is the historically right reading, not slack.
        occ += [(cp["cx"], cp["cy"], cp["r"] + clump * 0.90) for cp in self.M.get("crescent_ponds", [])]
        corr = self._corridor_buffers(clump * 0.45 + 4)  # ... and keep trees OFF the lanes / streets / road
        cr = clump / 2
        # ... and OUT of the SOUTHERN sun-corridor of every threshing yard + garden (a tree just south of them
        # blocks the drying/growing sun - +y is south). A touch wider than the check so it stays strictly clear.
        sun = [(o["x"], o["y"] + o["h"] / 2, o["w"] / 2 + cr + 2) for k in ("threshing_yards", "gardens") for o in self.M.get(k, [])]
        # ... and OUT of the EASTERN sun-lane of every kitchen GARDEN: a tree just east blocks the MORNING sun
        # (the sun rises in the E; +x is east), so a garden on a house's lee/E side keeps clear sky to its east.
        # Entry = (garden east edge, garden cy, half-height + reach). See gardens_unshaded_from_east.
        east = [(o["x"] + o["w"] / 2, o["y"], o["h"] / 2 + cr + 2) for o in self.M.get("gardens", [])]
        water_lines = [(st_["poly"], st_.get("w", 9) / 2) for st_ in self.M.get("streams", [])]
        water_lines += [(c_["poly"], c_.get("w", 2.5) / 2) for c_ in self.M.get("channels", [])]
        if self.M.get("moat"):
            water_lines.append((self.M["moat"], self.M.get("moat_width", 22) / 2))
        nx, ny = max(1, round((x1 - x0) / step)), max(1, round((y1 - y0) / step))
        clumps: list[Any] = []
        for iy in range(ny + 1):
            for ix in range(nx + 1):
                gx = x0 + ix * (x1 - x0) / nx
                gy = y0 + iy * (y1 - y0) / ny
                jx = gx + (self._hjit(gx, gy, 21.0) - 0.5) * step  # jitter the grid so the stand + its edge read ragged
                jy = gy + (self._hjit(gx, gy, 22.0) - 0.5) * step
                if not point_in_poly(jx, jy, poly):
                    continue
                if any((jx - ox) ** 2 + (jy - oy) ** 2 < rr * rr for ox, oy, rr in occ):
                    continue
                if any(point_in_poly(jx, jy, f) or edge_dist(jx, jy, f) < 12 for f in self.field_polys):
                    continue
                if any(point_in_poly(jx, jy, d) or edge_dist(jx, jy, d) < 12 for d in self.dry_polys):
                    continue  # the hem strips are barley: trees do not grow in the crop (groves_clear_of_dry_plots)
                if any(seg_dist(jx, jy, wl[k], wl[k + 1]) < whw + cr for wl, whw in water_lines for k in range(len(wl) - 1)):
                    continue  # no canopy stands over open water (canopy_clear_of_watercourses)
                if any(seg_dist(jx, jy, lp[k], lp[k + 1]) < buf for lp, buf in corr for k in range(len(lp) - 1)):
                    continue
                if any(abs(jx - sx) < shw and se - cr - 2 < jy < se + 24 + cr for sx, se, shw in sun):
                    continue
                if any(ex - cr - 2 < jx < ex + 24 + cr and abs(jy - ey) < ehh for ex, ey, ehh in east):
                    continue
                self._draw_grove(jx, jy, clump, clump, face=(0, -1), mix=mix)
                clumps.append([round(jx, 1), round(jy, 1)])
        if clumps:
            self.M["village_groves"].append(
                {
                    "x": round((x0 + x1) / 2, 1),
                    "y": round((y0 + y1) / 2, 1),
                    "w": round(x1 - x0, 1),
                    "h": round(y1 - y0, 1),
                    "rot": 0,
                    "role": role,
                    "r": round(clump / 2, 1),
                    "clumps": clumps,  # actual drawn clump centers + radius, for groves_clear_of_lanes
                    "poly": [[round(px, 1), round(py, 1)] for px, py in poly],
                }
            )
        return len(clumps)

    def _corridor_buffers(self, extra: float = 0) -> list[Any]:
        """Lane / town-street / road centerlines with their (half-width + `extra`) keep-out - the corridors that
        trees, scrub, and other vegetation must not be drawn ON. Returns [(polyline, buffer), ...]."""
        corr = [([tuple(p) for p in ln["pts"]], ln.get("w", 6) / 2 + extra) for ln in self.M.get("lanes", [])]
        corr += [([tuple(p) for p in s["pts"]], s.get("w", 10) / 2 + extra) for s in self.M.get("town_streets", [])]
        if self.M.get("road"):
            corr.append(([tuple(p) for p in self.M["road"]], self.M.get("road_width", 26) / 2 + extra))
        return corr

    def _on_lane(self, px: float, py: float, clear: float) -> bool:
        """True if (px, py) lies on (within `clear` of the tread half-width of) a trodden LANE. Decorative
        ground-cover (scrub, reeds) skips it so a constantly-walked path stays BARE and reads ON TOP of the
        scrub, never overgrown - the same reason the tread carries no vegetation in reality. Uses the lanes
        already recorded in M['lanes'] (so it only clears lanes drawn BEFORE the ground-cover)."""
        for ln in self.M.get("lanes", []):
            pts = ln["pts"]
            half = ln["w"] / 2 + clear
            if any(seg_dist(px, py, pts[i], pts[i + 1]) < half for i in range(len(pts) - 1)):
                return True
        return False

    def _on_watercourse(self, px: float, py: float, pad: float = 2.0) -> bool:
        """True if (px, py) lies ON a drawn watercourse - a stream or an irrigation channel (within its half-
        width + `pad`). Decorative ground-cover (scrub, reeds) skips it: vegetation never draws OVER open water,
        the same reason it skips the lane tread and the pond. Uses M['streams'] + M['channels'] recorded so far."""
        for wc in self.M.get("streams", []) + self.M.get("channels", []):
            p = wc["poly"]
            half = wc.get("w", 6) / 2 + pad
            if any(seg_dist(px, py, p[i], p[i + 1]) < half for i in range(len(p) - 1)):
                return True
        # ... and the fengshui crescent pond's open water (found 2026-07-21: scrub tufts drew ON the
        # half-moon pond - the skip knew M['pond'] and the linear courses but not this water body)
        return any(math.hypot(px - cp["cx"], py - cp["cy"]) < cp["r"] + pad for cp in self.M.get("crescent_ponds", []))

    def commons(self, poly: Any, role: str = "commons", avoid: Any = ()) -> None:
        """FUEL-AND-FODDER COMMONS - the degraded open grazing/scrub on the far (upslope / windward) side,
        BEYOND the fengshui back-grove: coarse grass, low brush, and a FEW scattered SCRAGGLY pines, kept
        cropped bare by constant firewood + grass gathering. Deliberately drawn OPEN and SPARSE on drier,
        poorer ground so it is VISUALLY DISTINCT from the dense, dark, closed-canopy village grove - this is a
        COMMONS (not anyone's field), non-arable. WHY (south China's hills were stripped for fuel/timber over a
        millennium - open pine + grass + erosion; the protected grove is the green EXCEPTION; the back slope
        also carried the graves + dry hill-crops): settlements.md 'Village windbreak' / back-slope land use. Recorded
        in M['commons']. `role` picks the glyph (woodland / pasture / commons); `avoid` is a list of KEEP-OUT
        polygons (e.g. the hamlet cluster) the scatter stays out of, so ground-cover never creeps onto them."""
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        bs = self.bscale
        area = (x1 - x0) * (y1 - y0)
        st = random.getstate()
        random.seed(int(abs(x0) * 7 + abs(y0) * 3 + round(x1 - x0)))
        feather = 42 * bs  # scrub THINS toward the boundary (a soft, ragged edge, not a hard line)

        pond = self.M.get("pond")

        def _sparse(px: float, py: float, drop: float) -> bool:  # skip a scatter point outside the poly, on a field/lane/building/water, in a keep-out, or (probabilistically) near the edge
            if (
                not point_in_poly(px, py, poly)
                or any(point_in_poly(px, py, ff) for ff in self.field_polys)
                or self._on_lane(px, py, 3 * bs)  # keep scrub off the trodden lane so the path is not overgrown
                or self._on_watercourse(px, py)  # ... and OFF the pond + streams/channels (scrub never draws over open water)
                or (pond and ((px - pond[0]) / pond[2]) ** 2 + ((py - pond[1]) / pond[3]) ** 2 <= 1.0)
                or any(
                    point_in_poly(px, py, b) for b in self.block_polys
                )  # ... and OFF any building/shrine/torii footprint (a commons that OVERLAPS the shrine must not scatter scrub over the hall + arch)
                or any(point_in_poly(px, py, c) for c in self.clearings)  # ... and off the swept sacred/funerary verge (tended precinct, sando, grave collar)
                or any(point_in_poly(px, py, a) for a in avoid)
            ):  # ... and OUT of any keep-out (the hamlet cluster stays clear of cover)
                return True
            ed = edge_dist(px, py, poly)
            return ed < feather and random.random() > (ed / feather) ** drop

        # NO solid fill: a filled polygon always has a crisp geometric EDGE (that read as a rhombus). Each land
        # type is defined PURELY by its feathered scatter, which thins to nothing at the margin - so the ground
        # has no boundary at all, just its cover petering out onto the open slope. THREE distinct looks so land
        # types read apart at a glance (the GM's rule - grass and woods must NOT look the same):
        #   role="woodland"  -> a COPPICE WOOD: individual, spaced tree CROWNS, an OPEN canopy (gaps show) - the
        #                       upland/ridge wood the hamlet coppices. Clearly TREES, but lighter and more open
        #                       than the dense DARK closed-canopy fengshui village grove (they stay distinct too).
        #   role="pasture"   -> OPEN GRAZING GRASS: grass tufts + the odd brush dot, NO trees at all - reads as
        #                       open pasture, unmistakably NOT woodland.
        #   role="commons"/"grazing" (default) -> the cut-over fuel/fodder scrub: grass + a FEW scraggly pines.
        # SVG-size: the grass BLADES are ~98% of a to-scale map's <line> elements and all share ONE constant
        # style, so they go in a bucket emitted ONCE inside a styled <g> (bare coords per line), not one full
        # stroke=...stroke-width=... string each - ~30% off the file, content-lossless (same lines, grouped),
        # render is visually identical (only the z-order of overlapping scrub texture shifts, in the margins;
        # the fields/buildings are pixel-identical). The sparse dots/pines keep their inline styles.
        g: list[str] = []
        blades: list[str] = []
        if role == "woodland":
            for _ in range(int(area / (540 * bs * bs))):  # spaced crowns: an OPEN coppice canopy, gaps showing
                cx, cy = random.uniform(x0, x1), random.uniform(y0, y1)
                if _sparse(cx, cy, 0.6):
                    continue
                r = random.uniform(6.5, 11.5) * bs
                col = random.choice(("#6E8B4A", "#7C9856", "#87A45C"))
                g.append(f'<ellipse cx="{cx:.1f}" cy="{cy + 2 * bs:.1f}" rx="{r:.1f}" ry="{r * 0.72:.1f}" fill="#59703E" fill-opacity="0.30"/>')  # soft ground shadow
                g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{col}" stroke="#4C6234" stroke-width="0.7"/>')  # the crown
                g.append(f'<circle cx="{cx - r * 0.32:.1f}" cy="{cy - r * 0.32:.1f}" r="{r * 0.42:.1f}" fill="#A6BA79" fill-opacity="0.55"/>')  # sun highlight
        else:
            for _ in range(int(area / (74 * bs * bs))):  # coarse grass tufts + the odd low brush dot
                gx, gy = random.uniform(x0, x1), random.uniform(y0, y1)
                if _sparse(gx, gy, 0.7):
                    continue
                if random.random() < 0.14:  # a low brush dot
                    g.append(f'<circle cx="{gx:.1f}" cy="{gy:.1f}" r="{random.uniform(1.5, 2.4) * bs:.1f}" fill="#94A063" fill-opacity="0.85"/>')
                else:  # a grass tuft: a few short diverging blades (bucketed - see the note at `blades`)
                    for _ in range(3):
                        a, bl = random.uniform(-0.45, 0.45), random.uniform(2.4, 4.2) * bs
                        blades.append(f'<line x1="{gx:.1f}" y1="{gy:.1f}" x2="{gx + math.sin(a) * bl:.1f}" y2="{gy - math.cos(a) * bl:.1f}"/>')
            if role != "pasture":  # the SCRAGGLY pines belong to cut-over scrub, NOT to open pasture
                for _ in range(max(2, int(area / (6000 * bs * bs)))):  # a few SCRAGGLY hill pines (sparse, individual, open)
                    px, py = random.uniform(x0 + 6, x1 - 6), random.uniform(y0 + 6, y1 - 6)
                    if _sparse(px, py, 0.5):
                        continue
                    th = random.uniform(9, 14) * bs
                    g.append(f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{py - th:.1f}" stroke="#7A6A48" stroke-width="{1.1 * bs:.1f}"/>')  # thin trunk
                    for k in range(3):  # sparse open branches - a scraggly wind-cropped pine, NOT a dense crown
                        ly, sp = py - th * (0.45 + 0.25 * k), (3.6 - k) * bs
                        g.append(f'<line x1="{px:.1f}" y1="{ly:.1f}" x2="{px - sp:.1f}" y2="{ly + 2 * bs:.1f}" stroke="#6E8452" stroke-width="{1.0 * bs:.1f}"/>')
                        g.append(f'<line x1="{px:.1f}" y1="{ly:.1f}" x2="{px + sp:.1f}" y2="{ly + 2 * bs:.1f}" stroke="#6E8452" stroke-width="{1.0 * bs:.1f}"/>')
        self.add(f'<g stroke="#A7A860" stroke-width="0.8">{"".join(blades)}</g>')  # bucketed blades (empty group when none - harmless)
        self.add(''.join(g))
        random.setstate(st)
        self._cover_n += 1
        self.M["commons"].append(
            {
                "x": round((x0 + x1) / 2, 1),
                "y": round((y0 + y1) / 2, 1),
                "w": round(x1 - x0, 1),
                "h": round(y1 - y0, 1),
                "rot": 0,
                "role": role,
                "seq": self._cover_n,
                "poly": [[round(px, 1), round(py, 1)] for px, py in poly],
            }
        )

    def marsh(self, poly: Any, role: str = "toe", avoid: Any = ()) -> None:
        """REED MARSH / WET MEADOW - wet reed ground drawn WET and SPARSE, FEATHERED to nothing at the margin like
        the commons (no hard fill edge): a faint blue-green wet tint (soft translucent patches), reed / sedge tufts,
        and a few standing-water glints - a distinctly WET palette, unlike the dry tan scrub commons. Points falling
        IN a paddy or ON the open pond water are skipped, so a generous region ABUTS the field's low edge (the polder
        embankment) or the pond's shore and only fills the wet ground beyond. `role`: 'toe' (default) = the LOW,
        undrained valley toe below the managed paddy, where wet-rice cultivation stops (wet rice is reclaimed FROM
        marsh - polders diked out into marsh/lake; where reclamation stops it stays reed wetland; `marsh_on_low_ground`
        checks this sits downhill); 'pond_fringe' = the reedy shallow MARGIN of a pond (a water-edge fringe, exempt
        from the low-ground rule). WHY: settlements.md 'Marsh'. Recorded M['marshes']."""
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        bs = self.bscale
        area = (x1 - x0) * (y1 - y0)
        st = random.getstate()
        random.seed(int(abs(x0) * 5 + abs(y0) * 7 + round(x1 - x0)))
        feather = 46 * bs
        pond = self.M.get("pond")

        def _sparse(px: float, py: float, drop: float) -> bool:  # skip a point outside the poly, IN a paddy / ON the pond / on a lane/building / in a keep-out, or (probabilistically) near the edge
            if (
                not point_in_poly(px, py, poly)
                or any(point_in_poly(px, py, ff) or edge_dist(px, py, ff) < 10 for ff in self.field_polys)
                or self._on_lane(px, py, 3 * bs)  # a causeway/path through the marsh stays bare, not reeded over
                or self._on_watercourse(px, py)  # ... and OFF a stream/channel bed (reeds fringe water, they do not float on it)
                or any(point_in_poly(px, py, b) for b in self.block_polys)  # ... and OFF any building/shrine/torii footprint
                or any(point_in_poly(px, py, c) for c in self.clearings)  # ... and off the swept sacred/funerary verge
                or any(point_in_poly(px, py, a) for a in avoid)
            ):  # ... and OUT of any keep-out
                return True
            if pond and ((px - pond[0]) / pond[2]) ** 2 + ((py - pond[1]) / pond[3]) ** 2 < 1.0:
                return True  # reeds fringe the shore, they do not float on open water
            ed = edge_dist(px, py, poly)
            return ed < feather and random.random() > (ed / feather) ** drop

        g: list[str] = []
        blades: list[str] = []  # SVG-size lever 2: bucket the constant-styled reed blades (see the note in `commons`)
        for _ in range(int(area / (360 * bs * bs))):  # faint WET TINT: soft translucent blue-green patches (feathered, no hard edge)
            gx, gy = random.uniform(x0, x1), random.uniform(y0, y1)
            if _sparse(gx, gy, 0.9):
                continue
            g.append(f'<circle cx="{gx:.1f}" cy="{gy:.1f}" r="{random.uniform(15, 28) * bs:.1f}" fill="#9FBBAE" fill-opacity="0.14"/>')
        for _ in range(int(area / (150 * bs * bs))):  # SPARSE reed / sedge tufts + the odd standing-water glint (thin, not a solid reedbed)
            gx, gy = random.uniform(x0, x1), random.uniform(y0, y1)
            if _sparse(gx, gy, 0.7):
                continue
            if random.random() < 0.12:  # a standing-water glint
                g.append(f'<ellipse cx="{gx:.1f}" cy="{gy:.1f}" rx="{random.uniform(2.6, 4.6) * bs:.1f}" ry="{random.uniform(1.2, 2.0) * bs:.1f}" fill="#C2D6CE" fill-opacity="0.85"/>')
            else:  # a reed tuft: a few fine near-VERTICAL blades, taller than dry grass
                for _ in range(4):
                    a, bl = random.uniform(-0.2, 0.2), random.uniform(4.0, 7.0) * bs
                    blades.append(f'<line x1="{gx:.1f}" y1="{gy:.1f}" x2="{gx + math.sin(a) * bl:.1f}" y2="{gy - math.cos(a) * bl:.1f}"/>')
        self.add(f'<g stroke="#6E9377" stroke-width="0.8">{"".join(blades)}</g>')  # bucketed blades (empty group when none - harmless)
        self.add(''.join(g))
        random.setstate(st)
        self._cover_n += 1
        self.M["marshes"].append(
            {
                "x": round((x0 + x1) / 2, 1),
                "y": round((y0 + y1) / 2, 1),
                "w": round(x1 - x0, 1),
                "h": round(y1 - y0, 1),
                "rot": 0,
                "role": role,
                "seq": self._cover_n,
                "poly": [[round(px, 1), round(py, 1)] for px, py in poly],
            }
        )
        if role != "pond_fringe":  # the wet valley TOE is UNBUILDABLE: register it as a no-build keep-out
            self.block_polys.append([(round(px, 1), round(py, 1)) for px, py in poly])  # so nothing is placed/dug on a bog (a thin pond-fringe shore ring is exempt)

    def hinterland(
        self, down_deg: Any = None, *, marsh: bool = True, commons: bool = True, interior_fill: bool = True, pad: float = 90, marsh_role: str = "toe", scrub_role: str = "grazing", skip_sides: Any = ()
    ) -> None:
        """Lay out a settlement's non-arable HINTERLAND: a reed MARSH at the downhill TOE (below the paddy's
        drainage line, where wet-rice reclamation stops and the valley floor stays reed wetland) and the
        cut-over SCRUB commons (coarse grass + a few scraggly pines) filling the surrounding non-arable margins.
        CHINA-FIRST: the south-China rice hills were stripped for fuel/timber over ~1,000 years, so the DOMINANT
        cover past the settlement is denuded scrub/rough grazing, NOT forest - the protected fengshui grove is
        the green exception, and the managed WOODLAND (coppice / bamboo / tung / tea-oil 'economic forest') is a
        FEW discrete PATCHES the gen adds by hand on the higher / farther ground (`s.commons([...],
        role='woodland')`), set back from the sun-needing crops by the scrub between. So hinterland lays the
        scrub + marsh; the woodland patches are per-map. The scrub bands are frame-margin strips OUTSIDE the
        CULTIVATED bbox (paddy + dry hatake), so each recorded centroid clears the paddy (`commons_clear_of_
        paddies` is a centroid test). All scatters skip fields/pond/lanes/buildings AND a **hamlet keep-out**
        (the cluster bbox, so no cover creeps among the houses), and NONE is a crop anchor (`_CROP_HARD`), so
        they BLEED off the frame and the crop stays tight. Call AFTER fields + cluster + pond + dry fields,
        BEFORE crop_to_content. `down_deg` (defaults to meta's) picks which frame side the scrub ring OMITS
        (the toe side) AND orients the marsh itself: the toe is a CONTOUR BAND perpendicular to the fall, so it
        rotates with the map like every other feature (see the comment at the marsh block); the scrub ring is
        radial. A comb-FAN field leaves the opposite bbox corner open -> the gen fills it (scrub +
        woodland patches). See settlements.md 'Hinterland (water-flow-keyed)'."""
        if down_deg is None:
            down_deg = self.M.get("meta", {}).get("down_deg", 90)
        polys = self.field_polys
        if not polys:
            return
        xs = [p[0] for poly in polys for p in poly]
        ys = [p[1] for poly in polys for p in poly]
        for dp in self.M.get("dry_plots", []):  # the CULTIVATED extent includes the dry hatake plots
            xs += [p[0] for p in dp["poly"]]
            ys += [p[1] for p in dp["poly"]]
        fx0, fx1, fy0, fy1 = min(xs), max(xs), min(ys), max(ys)
        W, H = self.W, self.H
        dx, dy = math.cos(math.radians(down_deg)), math.sin(math.radians(down_deg))
        # SETTLEMENT KEEP-OUT, so cover never scatters among the dwellings. Its SHAPE depends on the form:
        avoid: list[Any] = []
        hs = self.M.get("houses", [])
        m = 44
        if hs and self.M.get("meta", {}).get("nucleated", True):
            # NUCLEATED: the houses are one tight blob, so the bbox of their positions IS the built footprint.
            hxs, hys = [h["x"] for h in hs], [h["y"] for h in hs]
            avoid.append([(min(hxs) - m, min(hys) - m), (max(hxs) + m, min(hys) - m), (max(hxs) + m, max(hys) + m), (min(hxs) - m, max(hys) + m)])
        elif hs:
            # DISPERSED: the farmsteads RING the settlement, so a bbox of their positions is not their footprint
            # - it is the WHOLE MAP, and using it forbids ground cover everywhere inside the ring. That is what
            # left Akagahara's fan void as bare clay (GM: "a ton of empty space between the ditch and the
            # marsh"): the void fell inside this blanket, so neither the scrub ring nor anything else could
            # clothe it. Keep out each HOMESTEAD individually instead - house plus its bundle (yard, garden,
            # grove) - so the open ground BETWEEN the strewn farms is free to carry rough grazing, as it should.
            for key in ("houses", "gardens", "threshing_yards", "groves"):
                for r in self.M.get(key, []):
                    hw, hh = r.get("w", 40) / 2 + m, r.get("h", 30) / 2 + m
                    avoid.append([(r["x"] - hw, r["y"] - hh), (r["x"] + hw, r["y"] - hh), (r["x"] + hw, r["y"] + hh), (r["x"] - hw, r["y"] + hh)])
        # which frame side is the downhill TOE (marsh) - the other three carry the scrub commons
        toe_side = ("bottom" if dy >= 0 else "top") if abs(dy) >= abs(dx) else ("right" if dx >= 0 else "left")

        BLEED = 120  # a band reaches the canvas edge + this bleed, NOT `outer` beyond it
        # (clamping the OUTER extent to the canvas avoids scattering a huge off-canvas apron of scrub that only
        #  bloats the SVG node count - the frame clips it anyway; the on-canvas cover is unchanged)

        def ring(inner: float, outer: float) -> list[Any]:
            """The four picture-frame side-strips between the cultivated bbox grown by `inner` and by `outer`
            (outer clamped to the canvas + bleed), MINUS the toe side (marsh) and any `skip_sides` (e.g. a forest
            flank). Each strip lies outside the bbox -> centroid clears the paddy."""
            ox0, oy0 = max(-BLEED, fx0 - outer), max(-BLEED, fy0 - outer)
            ox1, oy1 = min(W + BLEED, fx1 + outer), min(H + BLEED, fy1 + outer)
            ix0, iy0, ix1, iy1 = fx0 - inner, fy0 - inner, fx1 + inner, fy1 + inner
            sides = {
                "top": [(ox0, oy0), (ox1, oy0), (ox1, iy0), (ox0, iy0)],
                "bottom": [(ox0, iy1), (ox1, iy1), (ox1, oy1), (ox0, oy1)],
                "left": [(ox0, iy0), (ix0, iy0), (ix0, iy1), (ox0, iy1)],
                "right": [(ix1, iy0), (ox1, iy0), (ox1, iy1), (ix1, iy1)],
            }
            return [v for k, v in sides.items() if k != toe_side and k not in skip_sides]

        if commons:
            for p in ring(0, max(W, H)):  # the cut-over SCRUB commons: the DOMINANT denuded-hill cover
                self.commons(p, role=scrub_role, avoid=avoid)  # (managed woodland is added as a FEW patches by the gen)
            # ...and the INTERIOR. The ring lays strips only OUTSIDE the cultivated bbox, but an irregular field
            # (a comb FAN) does not fill its own bbox: it leaves open VOIDS INSIDE it that nothing else clothes
            # - the strips are outside them and the marsh is a contour band below them - so they render as BARE
            # ground, the only uncovered land on the map. That is what read as "empty space" on Akagahara. This
            # patch covers the cultivated bbox; since the scatter already skips every field, lane, watercourse,
            # building and keep-out, it can only land in those voids, clothing them as the rough grazing they
            # are. Ground the crop does not use is still ground, and it is grazed. A SOLID field (a polder grid
            # fills its whole bbox, no voids) has nothing to clothe here, so `interior_fill=False` skips it.
            if interior_fill:
                self.commons([(fx0, fy0), (fx1, fy0), (fx1, fy1), (fx0, fy1)], role=scrub_role, avoid=avoid)
        if marsh:
            # The toe is a CONTOUR BAND, not an axis-aligned box. Wet ground is defined by HEIGHT, and every
            # other feature here (field, comb, drain, the marsh_on_low_ground check) resolves height by
            # projecting onto the `down_deg` vector - so the marsh's inner edge must be PERPENDICULAR to that
            # vector too. It was previously a bbox-keyed rectangle, which is only an honest contour when the
            # fall is axis-aligned (0/90/180/270); it was the ONE feature that did not rotate with the map.
            # At a diagonal fall that rectangle slices across the slope: on Kikuta/Hoshigaoka (down=45) its
            # inner edge spanned 205/219px of height and its uphill corner reached ABOVE their entire drain,
            # so it swallowed the ditch and painted reeds over ground that is still at rice height. That made
            # the reeds appear to abut the collector on the diagonal maps but not on due-S Akagahara - a pure
            # artifact of the rotation, which read as a real difference between the maps (GM, 2026-07).
            # Since EVERY collector descends ~19-20 degrees across the contours to reach its tameike, there is
            # genuinely ground below the ditch that is still crop-height on every map; the band now shows that
            # consistently instead of hiding it on two maps out of three.
            ux, uy = -dy, dx  # cross-slope unit vector (the contour direction)
            cult = [p for poly in polys for p in poly] + [p for dp in self.M.get("dry_plots", []) for p in dp["poly"]]
            v_in = max(p[0] * dx + p[1] * dy for p in cult) - pad  # inner edge: `pad` ABOVE the crop's lowest point, so the reeds still tuck under the crop
            corners = [(-BLEED, -BLEED), (W + BLEED, -BLEED), (W + BLEED, H + BLEED), (-BLEED, H + BLEED)]
            us = [c[0] * ux + c[1] * uy for c in corners]
            v_out = max(c[0] * dx + c[1] * dy for c in corners)  # far enough downhill to leave the canvas
            u0, u1 = min(us), max(us)
            toe = [(u * ux + v * dx, u * uy + v * dy) for u, v in ((u0, v_in), (u1, v_in), (u1, v_out), (u0, v_out))]
            self.marsh(toe, role=marsh_role, avoid=avoid)  # reed wetland: the low, undrained downhill toe

    def _attach_grove(self, hx: float, hy: float, arms: Any) -> None:
        """Draw a farmstead's windbreak grove (its belt arms) and record each arm under its parent house.
        Arms go into `grove_rects` (NOT `placed`) so a neighbor's grove may MERGE with it and the wells
        still avoid it. Drawn in the farmsteads() second pass, after every house/yard/garden is set."""
        for cx, cy, w, h, face in arms:
            self._draw_grove(cx, cy, w, h, face)
            self.M["groves"].append({"x": round(cx, 1), "y": round(cy, 1), "w": w, "h": h, "rot": 0, "of": [hx, hy], "face": list(face)})
            self.grove_rects.append((cx, cy, w, h))

    def _find_appurtenances(self, hx: float, hy: float, hw: float, hh: float, rot: float = 0, kind: str = "plain", shed: Any = False, wealth: float = 1.0) -> tuple[Any, Any] | None:
        """A farmstead needs room for BOTH its threshing yard (south/front, then a side) AND its dooryard
        kitchen garden (a DIFFERENT sunny side, kept off the west-side shed). Returns (yard_spot, garden_spot)
        or None if either can't fit."""
        yard = self._find_yard_spot(hx, hy, hw, hh)
        if yard is None:
            return None
        shed_rect = self._farm_shed_rect(hx, hy, hw, hh, rot, kind, shed)
        garden = self._find_garden_spot(hx, hy, hw, hh, yard, shed_rect, wealth)
        if garden is None:
            return None
        return yard, garden

    def _farmstead_nudges(self) -> Iterator[tuple[float, float]]:
        """Offsets to try for a farmhouse so the whole homestead (house + yard + garden + grove-room) fits:
        the ring's own spot first, then a widening spiral of shifts. The solver stops as soon as the home
        spot already works, so the wider rings only cost time for a genuinely crowded homestead."""
        yield 0, 0
        for d in (11 * self.bscale, 21 * self.bscale, 32 * self.bscale):
            yield from ((0, d), (d, 0), (-d, 0), (0, -d), (d, d), (-d, d), (d, -d), (-d, -d))

    def _clear_ground(self, x: float, y: float, w: float, h: float, extra: float) -> None:
        """Reserve a swept verge around a sacred/funerary feature: the w x h footprint grown by `extra`,
        added to `self.clearings` so the loose hinterland scatter (commons scrub, marsh reeds) skips it.
        Scaled by the map grain (bscale), so the cleared collar reads at the same real size on any scale.
        Also recorded in M['clearings'] with the current cover ordinal, so the checks can verify ORDER: a
        scatter only skips clearings that exist when it runs (scatter_respects_swept_clearings)."""
        e = extra * self.bscale
        rect = [(x - w / 2 - e, y - h / 2 - e), (x + w / 2 + e, y - h / 2 - e), (x + w / 2 + e, y + h / 2 + e), (x - w / 2 - e, y + h / 2 + e)]
        self.clearings.append(rect)
        self.M.setdefault("clearings", []).append({"poly": [[round(px, 1), round(py, 1)] for px, py in rect], "seq": self._cover_n})

    def reserve_clearing(self, x: float, y: float, w: float, h: float, extra: float = 46) -> None:
        """Pre-register a swept-ground clearing for a sacred/funerary feature a gen draws LATER (e.g. a
        precinct dropped in after crop_to_content, or placed after the hinterland scatter). The scrub/marsh
        scatter only skips clearings that already exist when it runs, so a late precinct must reserve its
        ground FIRST or the scrub covers it. The later shrine_hall/cemetery registers its own clearing too;
        the overlap is harmless. Pass roughly the footprint you will draw (a slightly generous `extra` is
        fine - over-clearing by a few px reads the same)."""
        self._clear_ground(x, y, w, h, extra)

    def cemetery(self, cx: float, cy: float, w: float, h: float, rot: float = 0, label: Any = None, label_above: bool = False, parish: bool = True, organic: bool = False) -> None:
        """A BURIAL GROUND - rows of grave markers (sotoba / stone stelae) with a couple of taller
        memorial stupas. Every settlement above a hamlet buries its dead: a Buddhist danka PARISH
        ground sits in a TEMPLE / MONASTERY precinct (death is the Buddhist clergy's business), while
        a Shinto SHRINE keeps death-pollution (kegare) at arm's length - so a graveyard sits well
        clear of any shrine. parish=False marks a NON-parish burial ground (a village-style plot not
        attached to a temple, e.g. one serving an in-wall farm quarter) - exempt from the temple-precinct
        rule. organic=True draws an IRREGULAR earthen plot (a village burial ground was never surveyed into
        a ruled rectangle - it grew as an unbounded patch on the waste back-slope); the recorded bbox + the
        no-build block stay the w x h rectangle, so the placement/clearance checks are unaffected - only the
        DRAWN ground and the markers within it follow the blob. Records M['cemeteries'] and blocks placement.
        label_above puts the label over the plot (for a cramped intramural ground whose label would otherwise spill onto its temple)."""
        st = random.getstate()
        random.seed(int(abs(cx) + abs(cy) * 3 + w))
        g = [f'<g transform="translate({cx:.1f},{cy:.1f}) rotate({rot:.1f})">']
        if organic:  # a jittered blob INSCRIBED in the w x h footprint - star-shaped from the center
            blob = [(math.cos(a) * (w / 2) * jr, math.sin(a) * (h / 2) * jr) for a, jr in ((2 * math.pi * i / 14, random.uniform(0.74, 1.0)) for i in range(14))]
            g.append(f'<path d="{smooth_closed(blob)}" fill="#CFC6B4" stroke="#8C8470" stroke-width="1.3" opacity="0.75"/>')
        else:
            blob = None
            g.append(f'<rect x="{-w / 2:.1f}" y="{-h / 2:.1f}" width="{w:.0f}" height="{h:.0f}" rx="3" fill="#CFC6B4" stroke="#8C8470" stroke-width="1.3" opacity="0.75"/>')
        yy = -h / 2 + 9
        while yy < h / 2 - 5:  # rows of small upright grave markers (kept inside the blob)
            xx = -w / 2 + 8
            while xx < w / 2 - 5:
                if blob is None or point_in_poly(xx, yy, blob):
                    mh = random.choice([6, 7, 8])
                    g.append(f'<rect x="{xx - 1.4:.1f}" y="{yy - mh:.1f}" width="2.8" height="{mh}" rx="1" fill="#9AA1A4" stroke="#5A584F" stroke-width="0.5"/>')
                xx += 9
            yy += 9
        stupas = (
            [(-w * 0.24, -h * 0.22), (w * 0.24, -h * 0.22)]
            if organic  # interior anchors (always inside the blob)
            else [(-w / 2 + 13, -h / 2 + 1), (w / 2 - 13, -h / 2 + 1)]
        )  # a couple of taller memorial stupas
        for sxp, syp in stupas:
            g.append(f'<rect x="{sxp - 2.2:.1f}" y="{syp:.1f}" width="4.4" height="13" rx="1.5" fill="#B7B0A0" stroke="#5A584F" stroke-width="0.7"/>')
            g.append(f'<circle cx="{sxp:.1f}" cy="{syp:.1f}" r="2.4" fill="#B7B0A0" stroke="#5A584F" stroke-width="0.7"/>')
        random.setstate(st)
        g.append('</g>')
        self.add(''.join(g))
        self.M.setdefault("cemeteries", []).append({"x": round(cx, 1), "y": round(cy, 1), "w": w, "h": h, "rot": round(rot, 1), "parish": parish})
        self.placed.append((cx, cy, w, h))
        bm = 8
        self.block_polys.append([(cx - w / 2 - bm, cy - h / 2 - bm), (cx + w / 2 + bm, cy - h / 2 - bm), (cx + w / 2 + bm, cy + h / 2 + bm), (cx - w / 2 - bm, cy + h / 2 + bm)])
        self._clear_ground(cx, cy, w, h, 30)  # the tended grave collar - scrub trimmed back off the markers (the waste around it stays scrubby)
        if label:
            ly = cy - h / 2 - 8 if label_above else cy + h / 2 + 14
            self.label(cx, ly, label, 11, italic=True, color="#6B5A3C")

    def _ward_fence_cap(self, a: Any, b: Any, tol: float = 16) -> int | None:
        """If the axis-aligned wall segment a-b runs ALONG a neighborhood (ward) fence, re-stamp the
        fence stroke over it so the FENCE renders ON TOP - the compound's own wall runs underneath, and
        the fence IS that side of the compound (no doubled, clashing parallel walls). Mirrors how a
        ward's own ends run under the city rampart. Returns the cap's z if it stamped one, else None."""
        ax, ay = a
        bx, by = b
        horiz = abs(ax - bx) >= abs(ay - by)
        for w in self.M.get("wards", []):
            bnd = w["boundary"]
            for i in range(len(bnd) - 1):
                px, py = bnd[i]
                qx, qy = bnd[i + 1]
                if (abs(px - qx) >= abs(py - qy)) != horiz:  # fence segment must run the same way
                    continue
                if horiz:
                    if abs(py - ay) > tol:
                        continue
                    lo, hi = max(min(ax, bx), min(px, qx)), min(max(ax, bx), max(px, qx))
                    if hi - lo < 10:
                        continue
                    dd = f'M{lo:.0f},{ay:.0f} L{hi:.0f},{ay:.0f}'
                else:
                    if abs(px - ax) > tol:
                        continue
                    lo, hi = max(min(ay, by), min(py, qy)), min(max(ay, by), max(py, qy))
                    if hi - lo < 10:
                        continue
                    dd = f'M{ax:.0f},{lo:.0f} L{ax:.0f},{hi:.0f}'
                self.add(f'<path d="{dd}" fill="none" stroke="#9C8A5E" stroke-width="5" opacity="0.9" stroke-linecap="round"/>')
                z = self.add(f'<path d="{dd}" fill="none" stroke="#4A3A22" stroke-width="1.3" stroke-dasharray="2,7" opacity="0.85"/>')  # palisade dash
                return z
        return None

    def mausoleum(self, cx: float, cy: float, w: float, h: float, label: str = "Ancestral Mausoleum", gate_dir: str = "south", label_below: bool = False) -> None:
        """A walled CRYPT PRECINCT - the ruling clan's ancestral mausoleum, where important samurai are
        interred in crypts and stone monuments after cremation. A prestige ground sited by the SAMURAI /
        government quarter (ancestor veneration is central to samurai identity), religiously staffed but a
        martial-clan monument distinct from the commoner temple graveyards. A walled court (like a manor)
        holding a stone crypt hall and a few tall memorial stupas. Records M['mausoleums']; blocks placement."""
        x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        self.add(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w}" height="{h}" fill="#E7DDC4"/>')  # the swept precinct court
        wall = '#3A352C'
        sides = {"north": ((x0, y0), (x1, y0), cx, y0), "south": ((x0, y1), (x1, y1), cx, y1), "west": ((x0, y0), (x0, y1), x0, cy), "east": ((x1, y0), (x1, y1), x1, cy)}
        mgg = max(self.px(12) / 2, 2.0)  # ceremonial gate: ~12 real ft opening (half-gap), floored
        mww = max(self.px(2), 2.0)  # precinct wall ~2 ft, 2px cartographic floor (GM 2026-07-19 to-scale rule)
        for name, (a, b, gx, gy) in sides.items():
            if name != gate_dir:
                self.add(f'<line x1="{a[0]:.0f}" y1="{a[1]:.0f}" x2="{b[0]:.0f}" y2="{b[1]:.0f}" stroke="{wall}" stroke-width="{mww:.1f}"/>')
            elif name in ("west", "east"):  # vertical wall - gap in y
                self.add(f'<line x1="{a[0]:.0f}" y1="{a[1]:.0f}" x2="{a[0]:.0f}" y2="{gy - mgg:.1f}" stroke="{wall}" stroke-width="{mww:.1f}"/>')
                self.add(f'<line x1="{b[0]:.0f}" y1="{gy + mgg:.1f}" x2="{b[0]:.0f}" y2="{b[1]:.0f}" stroke="{wall}" stroke-width="{mww:.1f}"/>')
            else:  # horizontal wall - gap in x
                self.add(f'<line x1="{a[0]:.0f}" y1="{a[1]:.0f}" x2="{gx - mgg:.1f}" y2="{a[1]:.0f}" stroke="{wall}" stroke-width="{mww:.1f}"/>')
                self.add(f'<line x1="{gx + mgg:.1f}" y1="{b[1]:.0f}" x2="{b[0]:.0f}" y2="{b[1]:.0f}" stroke="{wall}" stroke-width="{mww:.1f}"/>')
        # a wall that ABUTS a neighborhood (ward) fence yields to it: the fence is re-stamped over our
        # own wall there, so it renders ON TOP and IS that side of the precinct (recorded for the gate)
        ward_walls = [name for name, (a, b, gx, gy) in sides.items() if name != gate_dir and self._ward_fence_cap(a, b) is not None]
        hw, hh = min(w * 0.42, 86), min(h * 0.34, 52)  # the stone crypt hall, centered
        self.add(f'<rect x="{cx - hw / 2:.0f}" y="{cy - hh / 2:.0f}" width="{hw:.0f}" height="{hh:.0f}" rx="2" fill="#C9C0AE" stroke="#5A584F" stroke-width="2"/>')
        self.add(f'<rect x="{cx - hw / 2:.0f}" y="{cy - hh / 2:.0f}" width="{hw:.0f}" height="8" fill="#7A5A30"/>')  # the hall's roof band
        for sx in (x0 + 16, x1 - 16):  # tall memorial stupas flanking the hall
            self.add(f'<rect x="{sx - 3:.0f}" y="{cy - 9:.0f}" width="6" height="18" rx="2" fill="#B7B0A0" stroke="#5A584F" stroke-width="0.8"/>')
            self.add(f'<circle cx="{sx:.0f}" cy="{cy - 9:.0f}" r="3.4" fill="#B7B0A0" stroke="#5A584F" stroke-width="0.8"/>')
        self.M["mausoleums"].append({"x": cx, "y": cy, "w": w, "h": h, "rot": 0, "label": label, "gate_dir": gate_dir, "ward_walls": ward_walls, "gate_w": round(2 * mgg, 2), "wall_w": round(mww, 2)})
        self.placed.append((cx, cy, w, h))
        m = 30 * self.bscale  # a building-half margin at the map's grain
        self.block_polys.append([(x0 - m, y0 - m), (x1 + m, y0 - m), (x1 + m, y1 + m), (x0 - m, y1 + m)])
        if label:
            ly = y1 + 14 if label_below else y0 - 12
            self.label(cx, ly, label, 12, weight="bold", italic=True, color="#3A352C")

    def cremation_ground(self, cx: float, cy: float, label: str = "cremation ground", label_above: bool = False) -> None:
        """The CREMATORY (kasoba) - where the dead are burned before their bones are interred. Smoke, fire
        risk, and death-pollution put it OUTSIDE the walls; monks officiate with burakumin assistants (a
        religious order stands outside the caste system, so handling the dead does not pollute its caste).
        A cleared, scorched ground with a raised stone pyre platform, a wisp of smoke, and a small roofed
        shelter for the rite. Records M['cremation_grounds']; blocks placement."""
        # TO SCALE (GM 2026-07-19; anchors in settlements.md): a sanmai's cleared working core is
        # 30-80 real ft for a village/town, ~80-160 ft for a provincial city (even metropolitan
        # Edo's Yoyogi crematory was only ~180 ft square); the pyre platform ~15x10 ft. The old
        # glyph was FIXED-PIXEL (116x80px) and silently tripled at city scale.
        across = 130.0 if self.M["meta"].get("scale") == "city" else 75.0
        crx, cry = max(self.px(across) / 2, 14.0), max(self.px(across * 0.7) / 2, 10.0)
        self.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{crx:.1f}" ry="{cry:.1f}" fill="#C9BCA0" stroke="#8C7A56" stroke-width="1.5" opacity="0.85"/>')  # cleared scorched ground
        self.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{crx * 0.58:.1f}" ry="{cry * 0.55:.1f}" fill="#9A8A6A" opacity="0.5"/>')  # the burned center
        ppw, pph = max(self.px(15), 7.0), max(self.px(10), 5.0)
        self.add(
            f'<rect x="{cx - ppw / 2:.1f}" y="{cy - pph / 2:.1f}" width="{ppw:.1f}" height="{pph:.1f}" rx="1.5" fill="#8C8470" stroke="#4A463C" stroke-width="1.2"/>'
        )  # stone pyre platform (~15x10 ft)
        abw, abh = max(self.px(12), 5.0), max(self.px(8), 3.6)  # the ash bed ON the platform (~12x8 ft burn area)
        self.add(f'<rect x="{cx - abw / 2:.1f}" y="{cy - abh / 2:.1f}" width="{abw:.1f}" height="{abh:.1f}" fill="#5A463A"/>')  # the ash bed
        shw, shh = max(self.px(14), 7.0), max(self.px(10), 5.0)  # the officiants' shelter (~14x10 ft hut)
        shx = cx + crx * 0.52
        self.add(f'<rect x="{shx:.1f}" y="{cy - shh / 2:.1f}" width="{shw:.1f}" height="{shh:.1f}" rx="1.5" fill="#CDB890" stroke="#5A4326" stroke-width="1.2"/>')
        self.add(f'<rect x="{shx:.1f}" y="{cy - shh / 2:.1f}" width="{shw:.1f}" height="{shh * 0.32:.1f}" fill="#5A4326"/>')
        self.M["cremation_grounds"].append({"x": round(cx, 1), "y": round(cy, 1), "w": round(2 * crx, 1), "h": round(2 * cry, 1), "rot": 0})
        self.placed.append((cx, cy, 2 * crx, 2 * cry))
        m = 8
        self.block_polys.append([(cx - crx - m, cy - cry - m), (cx + crx + m, cy - cry - m), (cx + crx + m, cy + cry + m), (cx - crx - m, cy + cry + m)])
        if label:
            self.label(cx, cy - cry - 8 if label_above else cy + cry + 14, label, 11, italic=True, color="#6B5A3C")

    def ossuary(self, cx: float, cy: float, label: str = "pauper ossuary mound") -> None:
        """A PAUPER OSSUARY MOUND - a communal earthen mound where the bones of the poor and the
        'unconnected dead' (muenbotoke - those with no family or temple to inter them) are gathered, by
        the cremation ground outside the walls. A low rounded mound with a single weathered marker stupa.
        Records M['ossuaries']; blocks placement."""
        # TO SCALE (GM 2026-07-19, tightened 2026-07-21): a muenzuka is a 10-30 real-ft mound
        # (cremated, consolidated bone takes almost no volume; Kyoto's monumental Mimizuka, a state
        # monument, is ~50 ft at the base). Drawn at ~22 ft, mid-band. History of this constant: the
        # original glyph was FIXED-PIXEL (92x60px = a 276 ft kofun at city scale); the first fix drew
        # ~40 ft with a 9px floor, which STILL rendered 54 real ft at city scale - the floor, not the
        # size, controlled. The floor is now 4.5px (27 ft at city, inside the band) - a stroke-
        # convention minimum for visibility, never a size license.
        orx = max(self.px(22) / 2, 4.5)
        ory = orx * 0.62
        self.add(f'<ellipse cx="{cx}" cy="{cy + ory * 0.2:.1f}" rx="{orx:.1f}" ry="{ory:.1f}" fill="#BCA878" stroke="#8C7A52" stroke-width="1.5"/>')  # the earthen mound
        self.add(f'<ellipse cx="{cx}" cy="{cy - ory * 0.1:.1f}" rx="{orx * 0.64:.1f}" ry="{ory * 0.55:.1f}" fill="#C8B584" opacity="0.7"/>')  # the crown (shading)
        self.add(f'<rect x="{cx - 2:.0f}" y="{cy - ory - 8:.1f}" width="4" height="9" rx="1.5" fill="#A8A294" stroke="#5A584F" stroke-width="0.8"/>')  # a weathered marker stupa
        self.add(f'<circle cx="{cx:.0f}" cy="{cy - ory - 8:.1f}" r="2.6" fill="#A8A294" stroke="#5A584F" stroke-width="0.8"/>')
        self.M["ossuaries"].append({"x": round(cx, 1), "y": round(cy, 1), "w": round(2 * orx, 1), "h": round(2 * ory, 1), "rot": 0})
        self.placed.append((cx, cy, 2 * orx, 2 * ory))
        m = 8
        self.block_polys.append([(cx - orx - m, cy - ory - m), (cx + orx + m, cy - ory - m), (cx + orx + m, cy + ory + m), (cx - orx - m, cy + ory + m)])
        if label:
            self.label(cx, cy + ory + 12, label, 11, italic=True, color="#6B5A3C")

    def granary(self, x: float, y: float, n: int = 3, w: float = 58, h: float = 34, gap: float = 14, label: str = "granary") -> list[Any]:
        """A short row of fireproof storehouses (kura) - the tax-rice granary of a rice-TRANSIT
        town, where grain from many counties is gathered and forwarded up the kick-up chain.
        White-walled with a dark hip roof. Opt-in (meta(granary=True)): a standard county seat
        keeps its grain inside the magistrate's yamen, so it is NOT drawn separately. Records to
        M['granary'] (gated by town_has_granary) and blocks houses, like the manor."""
        stores: list[Any] = []
        x0 = x - (n * w + (n - 1) * gap) / 2
        for i in range(n):
            cx = x0 + i * (w + gap) + w / 2
            self.add(f'<rect x="{cx - w / 2:.0f}" y="{y - h / 2:.0f}" width="{w}" height="{h}" rx="2" fill="#E8E0CE" stroke="#6B5A3C" stroke-width="2"/>')
            self.add(f'<rect x="{cx - w / 2:.0f}" y="{y - h / 2:.0f}" width="{w}" height="9" fill="#5A4A30"/>')  # dark fireproof hip roof
            self.add(f'<line x1="{cx:.0f}" y1="{y - h / 2 + 9:.0f}" x2="{cx:.0f}" y2="{y + h / 2:.0f}" stroke="#6B5A3C" stroke-width="0.7"/>')
            stores.append({"x": cx, "y": y, "w": w, "h": h, "rot": 0})
            bm = 30  # block a RECT + a building-half margin so dwellings keep clear, like the manor
            self.block_polys.append([(cx - w / 2 - bm, y - h / 2 - bm), (cx + w / 2 + bm, y - h / 2 - bm), (cx + w / 2 + bm, y + h / 2 + bm), (cx - w / 2 - bm, y + h / 2 + bm)])
        self.M["granary"] = {"x": x, "y": y, "n": n, "stores": stores, "label": label}
        if label:
            self.label(x, y - h / 2 - 10, label, 11, italic=True, color="#6B5A3C")
        return stores

    def merchant_storehouses(self, count: int = 6, kw: Any = None, kh: Any = None) -> int:
        """Attach a small fireproof storehouse (kura) to the BACK of several merchant houses.
        Because most Rokugani farmers are TENANTS, the rent-rice and bulk goods of their (often
        absentee) landlords are kept in town - over and above the ordinary inventory storeroom a
        shop already has - so a noticeable MINORITY of businesses run a deep lot with a kura
        behind the shopfront (the classic narrow-front / deep-lot merchant compound). The kura
        is drawn as an annex behind the building (opposite its street-facing awning), like the
        farmhouse shed: part of the premises, not a separately-sited structure, so it needs no
        open ground in the packed quarter. Records to M['storehouses']; call AFTER the
        businesses are placed. Returns the number attached."""
        if kw is None:
            kw, kh = 20 * self.bscale, 14 * self.bscale  # a ~20x14 ft kura, scaled with the building grain
        biz = [b for b in self.M["buildings"] if b["kind"] in ("merchant", "shop")]
        st = random.getstate()  # spread the picks across the quarter without perturbing
        random.seed(7)  # the main placement RNG (saved/restored, like forest())
        random.shuffle(biz)
        random.setstate(st)
        placed = 0
        for b in biz:
            if placed >= count:
                break
            th = math.radians(b["rot"])
            bx, by = math.sin(th), -math.cos(th)  # the building's BACK direction (awning faces -back)
            off = b["h"] / 2 + kh / 2 - 2  # tuck the kura just behind the shopfront
            ox, oy = b["x"] + bx * off, b["y"] + by * off
            # never let a kura sit ON a street/alley bed (the broad corridor test would veto
            # every candidate at city scale, where the shop rows legitimately sit inside the
            # corridor clearance of the street they front)
            beds = [(st["pts"], st.get("w", 18) / 2) for st in self.M.get("town_streets", [])]
            beds += [(al["pts"], al.get("w", 10) / 2) for al in self.M.get("alleys", [])]
            if self.M.get("road"):
                beds.append((self.M["road"], self.M.get("road_width", 26) / 2))
            if any(seg_dist(ox, oy, pts[k], pts[k + 1]) < half + max(kw, kh) / 2 + 3 for pts, half in beds for k in range(len(pts) - 1)):
                continue
            self.add(
                f'<g transform="translate({ox:.0f},{oy:.0f}) rotate({b["rot"]:.0f})">'
                f'<rect x="{-kw / 2:.0f}" y="{-kh / 2:.0f}" width="{kw}" height="{kh}" rx="1.5" fill="#E8E0CE" stroke="#6B5A3C" stroke-width="1.4"/>'
                f'<rect x="{-kw / 2:.0f}" y="{-kh / 2:.0f}" width="{kw}" height="4.5" fill="#5A4A30"/></g>'
            )  # dark fireproof roof
            self.M["storehouses"].append({"x": ox, "y": oy, "w": kw, "h": kh, "of": [b["x"], b["y"]]})
            self.placed.append((ox, oy, kw, kh))  # later packs (the city terraces) must flow around the annex
            placed += 1
        return placed

    def merchant_residences(self, count: int = 4, depth_margin: float = 14, spread: float = 120) -> int:
        """Place a few RICH merchant RESIDENCES (kind 'merchant_large') directly BEHIND the shopfront band,
        each ALIGNED to (same rotation as) the storefront it sits behind - the merchant family lives over/
        behind its own shop. Derived from the ACTUAL placed shops (not fixed coords), so it stays correct
        under any seed: each home is set one step DEEPER than the deepest shop (clearing the storefront band),
        parallel to it. Call AFTER the frontage but BEFORE the laborer packs (which then set back further,
        leaving the merchant-band -> gap -> warren order). Uses a true RECTANGULAR overlap test (the circle
        _fits is far too conservative for a large home in a tight band). Returns count placed."""
        rd = self.M.get("road")
        biz = [b for b in self.M["buildings"] if b["kind"] in ("merchant", "shop")]
        if not (rd and biz):
            return 0

        def droad(x: float, y: float) -> float:
            return min(seg_dist(x, y, rd[k], rd[k + 1]) for k in range(len(rd) - 1))

        def corners(cx: float, cy: float, rw: float, rh: float, rot: float = 0.0) -> list[Pt]:
            th = math.radians(rot)
            c, sn = math.cos(th), math.sin(th)
            return [(cx + dx * c - dy * sn, cy + dx * sn + dy * c) for dx, dy in ((-rw / 2, -rh / 2), (rw / 2, -rh / 2), (rw / 2, rh / 2), (-rw / 2, rh / 2))]

        def overlap(ca: Any, cb: Any) -> bool:
            return (
                any(point_in_poly(px, py, cb) for px, py in ca)
                or any(point_in_poly(px, py, ca) for px, py in cb)
                or any(segments_cross(ca[i], ca[(i + 1) % 4], cb[j], cb[(j + 1) % 4]) for i in range(4) for j in range(4))
            )

        bandmax = max(droad(b["x"], b["y"]) for b in biz)  # depth of the deepest storefront
        w, h = self._dims("merchant_large")
        st = random.getstate()  # spread the picks without perturbing the main placement RNG
        random.seed(11)
        random.shuffle(biz)
        random.setstate(st)
        placed = 0
        used: list[Pt] = []
        for b in biz:
            if placed >= count:
                break
            th = math.radians(b["rot"])
            backx, backy = math.sin(th), -math.cos(th)  # the shop's BACK (inland, away from the road)
            step = bandmax - droad(b["x"], b["y"]) + h / 2 + depth_margin  # land just behind the WHOLE band
            ox, oy = b["x"] + backx * step, b["y"] + backy * step
            if ox < 55 or ox > self.W - 55 or oy < 88 or oy > self.H - 26:
                continue
            if self.bound and not point_in_poly(ox, oy, self.bound):
                continue
            if self._in_blocked(ox, oy) or self._near_corridor(ox, oy):
                continue
            mc = corners(ox, oy, w, h, b["rot"])  # (_in_blocked above already keeps it off the paddies)
            if any(overlap(mc, corners(px, py, pw, ph)) for (px, py, pw, ph) in self.placed if abs(px - ox) + abs(py - oy) <= 150):  # rectangular, not circular: clears the tight band
                continue
            if any(math.hypot(ox - ux, oy - uy) < spread for ux, uy in used):
                continue  # keep the rich homes spread along the band
            self.building(ox, oy, w, h, "merchant_large", rot=b["rot"])
            used.append((ox, oy))
            placed += 1
        return placed

    def flophouse(self, x: float, y: float, w: Any = None, h: Any = None, label: str = "flophouse", label_below: bool = False) -> None:
        """Real size ~104x46 ft (town-calibrated), converted at the map's ftpx.
        A large, plain communal lodging - a kichin-yado / market flophouse - where peasants
        who travel a long way to market day sleep on straw under a roof for a sen a night. It is
        BIGGER and PLAINER than a shophouse (no awning, a long dormitory of plain doorways), set
        where travelers arrive: the gate market of a walled town, the road of an unwalled one.
        Default-on for a town (town_has_flophouse); meta(flophouses=N) requires more. Records to
        M['flophouses'] and blocks houses - place it BEFORE any nearby pack/ring."""
        if w is None:
            w, h = self.px(104), self.px(46)
        x0, y0 = x - w / 2, y - h / 2
        self.add(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w}" height="{h}" rx="2" fill="#CDBE96" stroke="#5A4A30" stroke-width="2"/>')
        self.add(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w}" height="10" fill="#7A6038"/>')  # long roof ridge
        self.add(f'<line x1="{x0:.0f}" y1="{y:.0f}" x2="{x0 + w:.0f}" y2="{y:.0f}" stroke="#5A4A30" stroke-width="0.7"/>')
        for dx in range(int(x0) + 14, int(x0 + w) - 10, 26):  # a row of plain doorways (a long dormitory)
            self.add(f'<rect x="{dx}" y="{y + h / 2 - 7:.0f}" width="9" height="7" fill="#5A4A30" opacity="0.8"/>')
        self.M["flophouses"].append({"x": x, "y": y, "w": w, "h": h, "rot": 0, "label": label})
        self.placed.append((x, y, w, h))
        bm = 30  # block a RECT + a building-half margin so dwellings keep clear, like the manor
        self.block_polys.append([(x0 - bm, y0 - bm), (x0 + w + bm, y0 - bm), (x0 + w + bm, y0 + h + bm), (x0 - bm, y0 + h + bm)])
        if label:
            self.label(x, y0 + h + 19 if label_below else y0 - 10, label, 11, italic=True, color="#5A4A30")

    def inn(self, x: float, y: float, w: Any = None, h: Any = None, rot: float = 0) -> None:
        """A prominent caravan INN - larger and grander than a flophouse, lodging the merchants, drivers
        and guards of the wagon-trains. Recorded in M['buildings'] (kind 'inn', non-residential). It
        FRONTS the road, so `rot` tilts it to lie PARALLEL to a diagonal road with its noren entrance
        (the +y front) FACING the roadbed. Blocks placement - place BEFORE any nearby pack.
        Real size ~66x48 ft (a large 2-story post-road inn), converted at the map's ftpx - as a
        fixed-px glyph it read 2.5x too big on a city map."""
        if w is None:
            w, h = self.px(66), self.px(48)
        hw, hh = w / 2, h / 2
        sf = h / 48  # glyph detail scales with the footprint
        g = [
            f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.2f})">',
            f'<rect x="{-hw:.1f}" y="{-hh:.1f}" width="{w:.1f}" height="{h:.1f}" rx="2" fill="#D9B98C" stroke="#5A3F1E" stroke-width="{max(2.2 * sf, 1.0):.1f}"/>',
            f'<rect x="{-hw:.1f}" y="{-hh:.1f}" width="{w:.1f}" height="{11 * sf:.1f}" fill="#7A5A30"/>',  # roof ridge
            f'<rect x="{-hw:.1f}" y="{hh - 4 * sf:.1f}" width="{w:.1f}" height="{4 * sf:.1f}" fill="#7A5A30" opacity="0.55"/>',
        ]  # lower eave (2-story)
        for i in range(3):  # upper-story lattice windows
            wx = -hw + w * (0.2 + 0.3 * i)
            g.append(f'<rect x="{wx:.1f}" y="{-hh + 14 * sf:.1f}" width="{10 * sf:.1f}" height="{7 * sf:.1f}" fill="#9A7E4E" stroke="#5A3F1E" stroke-width="0.6"/>')
            g.append(f'<line x1="{wx + 5 * sf:.1f}" y1="{-hh + 14 * sf:.1f}" x2="{wx + 5 * sf:.1f}" y2="{-hh + 21 * sf:.1f}" stroke="#D6C49A" stroke-width="0.6"/>')
        nx, nw = -w * 0.19, w * 0.38  # NOREN entrance curtain on the +y front
        g.append(f'<rect x="{nx:.1f}" y="{hh:.1f}" width="{nw:.1f}" height="{9 * sf:.1f}" rx="1" fill="#2E4A6B" stroke="#1E3450" stroke-width="0.6"/>')
        for k in (1, 2):
            g.append(f'<line x1="{nx + nw * k / 3:.1f}" y1="{hh:.1f}" x2="{nx + nw * k / 3:.1f}" y2="{hh + 9 * sf:.1f}" stroke="#C9D4E0" stroke-width="0.7"/>')
        g.append('</g>')
        self.add(''.join(g))
        self.M["buildings"].append({"x": x, "y": y, "w": w, "h": h, "kind": "inn", "rot": rot})
        self.placed.append((x, y, w, h))
        bm = 24
        self.block_polys.append([(x - hw - bm, y - hh - bm), (x + hw + bm, y - hh - bm), (x + hw + bm, y + hh + bm), (x - hw - bm, y + hh + bm)])

    def stables(self, x: float, y: float, w: Any = None, h: Any = None, rot: float = 0) -> None:
        """A large STABLES - long rows of stalls for a wagon-train's many draft animals (oxen, horses).
        Recorded in M['buildings'] (kind 'stables', non-residential). Wants OPEN GROUND around it. `rot`
        tilts it to sit parallel to its inn / the road. Place BEFORE any nearby pack.
        Real size ~92x44 ft (stall rows for a full wagon-train), converted at the map's ftpx."""
        if w is None:
            w, h = self.px(92), self.px(44)
        hw, hh = w / 2, h / 2
        sf = h / 44  # glyph detail scales with the footprint
        g = [
            f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.2f})">',
            f'<rect x="{-hw:.1f}" y="{-hh:.1f}" width="{w:.1f}" height="{h:.1f}" rx="2" fill="#B79A6E" stroke="#5A4326" stroke-width="{max(2 * sf, 1.0):.1f}"/>',
            f'<rect x="{-hw:.1f}" y="{-hh:.1f}" width="{w:.1f}" height="{9 * sf:.1f}" fill="#6B4F2A"/>',
        ]  # roof ridge
        sx, step = -hw + 12 * sf, max(16 * sf, 6)  # stall divisions
        while sx < hw - 8 * sf:
            g.append(f'<line x1="{sx:.1f}" y1="{-hh + 9 * sf:.1f}" x2="{sx:.1f}" y2="{hh:.1f}" stroke="#6B4F2A" stroke-width="1.4" opacity="0.7"/>')
            sx += step
        g.append('</g>')
        self.add(''.join(g))
        self.M["buildings"].append({"x": x, "y": y, "w": w, "h": h, "kind": "stables", "rot": rot})
        self.placed.append((x, y, w, h))
        bm = 24
        self.block_polys.append([(x - hw - bm, y - hh - bm), (x + hw + bm, y - hh - bm), (x + hw + bm, y + hh + bm), (x - hw - bm, y + hh + bm)])

    # ---- provincial-city features (scale="city")
    def _gapped_ring(self, ring: Any, gates: Any, gap: float = 38, closed: bool = True, water_gates: Any = (), water_gap: float = 24) -> str:
        """An SVG path for a wall (closed ring or open arc) with a genuine OPENING (~2*gap wide) at each
        gate, so the rampart can render OVER the ground lanes yet still let the road show THROUGH the gate
        - rather than painting a land rect over the wall (which would erase the road too, once on top).
        `water_gates` open NARROWER gaps (~2*water_gap) where a cargo canal passes the rampart under
        a water-gate arch (the Suzhou shuimen; the canal shows through exactly like a road at a gate)."""
        gpts = [(g[0], g[1]) for g in gates]
        wpts = [(g[0], g[1]) for g in water_gates]

        def isg(p: Any) -> bool:
            return any(math.hypot(p[0] - x, p[1] - y) < 6 for x, y in gpts) or any(math.hypot(p[0] - x, p[1] - y) < 6 for x, y in wpts)

        def gapof(p: Any) -> float:
            return water_gap if any(math.hypot(p[0] - x, p[1] - y) < 6 for x, y in wpts) else gap

        def lerp(a: Any, b: Any, d: float) -> Pt:
            length = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
            return (a[0] + (b[0] - a[0]) * d / length, a[1] + (b[1] - a[1]) * d / length)

        subs: list[Any] = []
        cur: list[Any] = []
        for i in range(len(ring) - 1):
            a, b = ring[i], ring[i + 1]
            s = lerp(a, b, gapof(a)) if isg(a) else a
            e = lerp(b, a, gapof(b)) if isg(b) else b
            if not cur:  # start a fresh run (the first edge, or just after a gate)
                cur = [s]
            cur.append(e)
            if isg(b):  # this edge ends at a gate - close the run (a gap follows)
                subs.append(cur)
                cur = []
        if cur:
            subs.append(cur)
        if closed and len(subs) >= 2 and not isg(ring[0]):  # closed ring, ring[0] not a gate: last run continues into the first
            subs[0] = subs[-1] + subs[0][1:]
            subs.pop()
        return ' '.join('M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in sp) for sp in subs)

    def ring_road(self, wall_pts: Any, inset: float = 34, width: float | None = None) -> list[Pt]:
        """A patrol/access ROAD just inside the city wall - the Chinese 'follow-the-wall street'
        (順城街) - a closed loop offset `inset` px in from the rampart, leaving the wall-clear zone
        a fortified city keeps for moving troops along the wall. Records M['ring_road']; returns the
        loop polygon to use as s.bound (so the quarters pack INSIDE it, off the wall). It is NOT a
        town_street: a fortification road is exempt from the must-be-built-up rule (its wall side is
        bare by design, and stretches run behind fields/compounds), but the grid still connects to it."""
        if width is None:
            width = self.lw(20)  # the ring/patrol street ~20 ft wide
        cx = sum(p[0] for p in wall_pts) / len(wall_pts)
        cy = sum(p[1] for p in wall_pts) / len(wall_pts)
        ring: list[Pt] = []
        for x, y in wall_pts:
            d = math.hypot(x - cx, y - cy) or 1.0
            f = (d - inset) / d
            ring.append((cx + (x - cx) * f, cy + (y - cy) * f))
        loop = ring + [ring[0]]
        dd = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in loop)
        self._ground(
            width,
            self.M,
            "ring_road_z",
            edge=f'<path d="{dd}" fill="none" stroke="#B49A66" stroke-width="{width}" opacity="0.85" stroke-linejoin="round"/>',
            bed=f'<path d="{dd}" fill="none" stroke="#D9C8A0" stroke-width="{width - 6}" opacity="1" stroke-linejoin="round"/>',
        )
        self.corridors.append((loop, width / 2 + 21))  # buildings keep WELL off the ring road (even a large/rotated footprint's corner stays off its bed)
        self.M["ring_road"] = [[round(x, 1), round(y, 1)] for x, y in loop]
        self.M["ring_road_width"] = width
        return ring

    def _tower(self, x: float, y: float, rot: float = 0.0, wc: str = '#3A352C', tw: float = 38) -> int:
        """A square guard tower straddling the wall (drawn OVER the rampart), ROTATED to sit square to
        the wall (rot = the wall's tangent angle there, so a tower on a slanted wall slants with it).
        Records M['wall_towers'] and reserves a no-build block so the packs leave it clear."""
        h = tw / 2
        z = self.add_top(
            f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">'
            f'<rect x="{-h:.0f}" y="{-h:.0f}" width="{tw}" height="{tw}" fill="#9C8A66" stroke="{wc}" stroke-width="2.4"/>'
            f'<rect x="{-h + 7:.0f}" y="{-h + 7:.0f}" width="{tw - 14}" height="{tw - 14}" fill="#6B5A3A"/></g>'
        )
        self.M.setdefault("wall_towers", []).append({"x": round(x, 1), "y": round(y, 1), "w": tw, "h": tw, "rot": round(rot, 1), "z": z})
        bm = 24 * max(self.bscale, 0.5)  # a building-half margin at the map's grain (floored: the tower glyph itself is fixed-size)
        self.block_polys.append([(x - tw / 2 - bm, y - tw / 2 - bm), (x + tw / 2 + bm, y - tw / 2 - bm), (x + tw / 2 + bm, y + tw / 2 + bm), (x - tw / 2 - bm, y + tw / 2 + bm)])
        return z

    def _wall_walk(self, pts: Any, g_idx: int, arc: float, west: bool = True) -> tuple[float, float, float]:
        """From wall vertex g_idx, walk `arc` px ALONG the wall (toward the WEST neighbor - smaller x -
        if west, else EAST), returning (x, y, edge_angle_deg) at that arc-distance. Lets gate furniture
        follow the curving wall and pick up its LOCAL tangent, instead of a flat offset + the gate
        vertex's tangent (which mismatch once the wall has curved away from the gate)."""
        n = len(pts)
        step_to_east = 1 if pts[(g_idx + 1) % n][0] >= pts[(g_idx - 1) % n][0] else -1
        step = -step_to_east if west else step_to_east
        i, rem = g_idx, arc
        while True:
            j = (i + step) % n
            ex, ey = pts[j][0] - pts[i][0], pts[j][1] - pts[i][1]
            seg = math.hypot(ex, ey) or 1.0
            if seg >= rem:
                t = rem / seg
                return pts[i][0] + ex * t, pts[i][1] + ey * t, math.degrees(math.atan2(ey, ex))
            rem -= seg
            i = j

    def city_wall(self, pts: Any, gates: Any = (), ring_inset: float = 34, guard_east: Any = (), tower_skip: Any = (), water_gates: Any = ()) -> None:
        """A CLOSED city rampart (a full ring, unlike the town's open hill-anchored arc), with a
        gap at each gate in `gates` (each (x,y) on the ring, where the wall runs ~horizontal -
        the N and S gates the Imperial road passes through). Each gate gets a GUARD HOUSE with an
        attached INSPECTION STATION (tariff audit) and a GUARD TOWER, all in the top layer so the
        road passes under them. Gates listed in `guard_east` put the guard house + inspection on
        the EAST side of the gate (tower west) instead of the default west - so the furniture can
        fill whichever flank of the road has the ground to spare. `tower_skip` lists keep-clear
        points (e.g. where a ward fence will later meet the wall and hang its kido gate - the
        gate cannot move, it gates a fixed crossing, so the TOWER yields): a mural tower whose
        vertex falls within ~62px of one SLIDES a short way along the wall until clear (both
        directions tried, shortest slide wins - a full vertex jump left a bare stretch of
        rampart, a defensive hole).
        Records M['wall'], M['gates'], M['gate'], M['gate_structs'] (the guard houses + towers),
        and M['inspection_stations']."""
        wc = '#3A352C'
        ring = list(pts) + [pts[0]]
        # the rampart renders in the WALL layer (over the ground lanes - a street running into the wall
        # passes UNDER it) with a GENUINE gap at each gate, so the road shows through the opening
        dd = self._gapped_ring(ring, gates, 38, water_gates=water_gates)
        self.M["wall_z"] = self.add_wall(f'<path d="{dd}" fill="none" stroke="{wc}" stroke-width="11" stroke-linejoin="round" stroke-linecap="round"/>')
        self.add_wall(f'<path d="{dd}" fill="none" stroke="#6B5A3A" stroke-width="3" stroke-linejoin="round" opacity="0.5"/>')
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        n = len(pts)
        # the wall's TANGENT angle at each vertex (the chord through its two neighbors) - towers rotate
        # to sit square to the wall, so a tower on a slanted stretch slants with it
        tang = [math.degrees(math.atan2(pts[(i + 1) % n][1] - pts[i - 1][1], pts[(i + 1) % n][0] - pts[i - 1][0])) for i in range(n)]

        # towers straddle the wall but their FOOTING stays on the BERM: centered on the wall line, a
        # 38-40px tower pokes its outer face into a close-set moat's bed, so every tower is nudged
        # INWARD (toward the ring's centroid) until only ~8px of its outer face projects past the
        # wall centerline - the horse-face bastion's stride, standing dry whatever gap the moat is
        # later drawn at (city_wall runs before s.moat, so it cannot measure the bed; 8px clears
        # the tightest gap in the pool, Tango's 24 - moat half 11 = 13px berm, with ~4px to spare).
        # Gated by city_wall_furniture_clear_of_moat.
        def _berm_nudge(x: float, y: float, tw_: float) -> Pt:
            ux, uy = cx - x, cy - y
            ul = math.hypot(ux, uy) or 1.0
            d = tw_ / 2 - 6  # 6px projection: on a slanted stretch the square's rotation swings a corner ~2px closer than the face
            return x + ux / ul * d, y + uy / ul * d

        self.M["gate_structs"] = []
        for gx, gy in gates:
            g_idx = next(i for i, p in enumerate(pts) if p[0] == gx and p[1] == gy)  # the gate's wall vertex
            # gateposts frame the opening, standing ON the wall line to either side, ORIENTED TO
            # THE WALL'S LOCAL TANGENT - so an E/W gate's posts stand N and S of the opening (not
            # the old hard-coded N/S layout, which floated the posts parallel to an E/W wall). Each
            # post is offset +-35px along the tangent and straddles the wall: ~5px onto the berm
            # (never the moat) and ~26px inward. Recorded as gate_structs so
            # city_wall_furniture_clear_of_moat covers them (GM, 2026-07).
            _tg = math.radians(tang[g_idx])
            _tx, _ty = math.cos(_tg), math.sin(_tg)  # unit tangent along the wall
            _rox, _roy = gx - cx, gy - cy
            _rl = math.hypot(_rox, _roy) or 1.0
            _rox, _roy = _rox / _rl, _roy / _rl  # unit radial OUTWARD
            for _side in (-1, 1):
                _pcx = gx + _tx * 35 * _side - _rox * 10.5  # offset along the wall, shifted inward so
                _pcy = gy + _ty * 35 * _side - _roy * 10.5  # the post projects ~5px out / ~26px in
                self.add_wall(f'<g transform="translate({_pcx:.1f},{_pcy:.1f}) rotate({tang[g_idx]:.1f})"><rect x="-7" y="-15.5" width="14" height="31" fill="{wc}"/></g>')
                self.M["gate_structs"].append({"x": round(_pcx, 1), "y": round(_pcy, 1), "w": 14, "h": 31, "rot": round(tang[g_idx], 1), "kind": "gatepost"})
            # the GUARD HOUSE + INSPECTION STATION sit ON the ring road just inside the gate, each one
            # WALKED along the curving wall (so it picks up the wall's LOCAL tangent there, not the gate
            # vertex's) and pulled in radially to the ring road's centerline (inset `ring_inset`, matching
            # s.ring_road) - so the patrol road runs lengthwise THROUGH each building, which sits SQUARE
            # to the wall like the towers, instead of the road slicing across an axis-aligned box.
            insp_xy: Any = None
            g_east = any(abs(gx - ex) < 2 and abs(gy - ey) < 2 for (ex, ey) in guard_east)
            gh_rect: Any = None
            for kind, arc, fw, fh, fill in (("guardhouse", 80, 66, 44, "#C9A57A"), ("inspection", 144, 60, 44, "#D8C49A")):
                # the inspection station walks OUTWARD from the guard house until the two rects
                # clear - on a small tight ring the fixed arcs converge and the annex would be
                # drawn through the guard house (city_gate_guard_inspection_separate)
                for arc_try, tuck in ((arc, 0), (arc + 14, 0), (arc, 20), (arc + 14, 20), (arc + 28, 20)):
                    # first slide a little along the wall, then TUCK radially inward (an annex
                    # set just inside the patrol line) - sliding alone can walk the inspection
                    # past the ~160px gate radius (city_inspection_station_at_each_gate)
                    wx, wy, ang = self._wall_walk(pts, g_idx, arc_try, west=not g_east)
                    d = math.hypot(wx - cx, wy - cy) or 1.0
                    f = (d - ring_inset - tuck) / d  # radial inset to the ring road centerline (+ tuck)
                    fx, fy = cx + (wx - cx) * f, cy + (wy - cy) * f
                    a = (ang + 90) % 180 - 90  # local wall tangent, folded to (-90, 90]
                    if gh_rect is None:
                        break  # the guard house itself takes the first arc
                    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
                    mine = [
                        (fx + ca * px_ - sa * py_, fy + sa * px_ + ca * py_)
                        for px_, py_ in ((-fw / 2 - 3, -fh / 2 - 3), (fw / 2 + 3, -fh / 2 - 3), (fw / 2 + 3, fh / 2 + 3), (-fw / 2 - 3, fh / 2 + 3))
                    ]
                    if not rects_overlap(mine, gh_rect):
                        break
                trim = (
                    f'<line x1="{-fw / 2:.0f}" y1="0" x2="{fw / 2:.0f}" y2="0" stroke="#5A4326" stroke-width="0.8"/>'
                    if kind == "guardhouse"
                    else f'<rect x="{-fw / 2:.0f}" y="{-fh / 2:.0f}" width="{fw}" height="8" fill="#8A6E3E"/>'
                )
                z = self.add_top(
                    f'<g transform="translate({fx:.0f},{fy:.0f}) rotate({a:.1f})">'
                    f'<rect x="{-fw / 2:.0f}" y="{-fh / 2:.0f}" width="{fw}" height="{fh}" rx="2" fill="{fill}" stroke="#5A4326" stroke-width="1.8"/>'
                    f'{trim}</g>'
                )
                self.M["gate_structs"].append({"x": fx, "y": fy, "w": fw, "h": fh, "rot": round(a, 1), "kind": kind, "z": z})
                if kind == "guardhouse":
                    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
                    gh_rect = [(fx + ca * px_ - sa * py_, fy + sa * px_ + ca * py_) for px_, py_ in ((-fw / 2, -fh / 2), (fw / 2, -fh / 2), (fw / 2, fh / 2), (-fw / 2, fh / 2))]
                if kind == "inspection":
                    self.M["inspection_stations"].append({"x": fx, "y": fy, "w": fw, "h": fh, "rot": round(a, 1), "label": "inspection station"})
                    insp_xy = (fx, fy)
            # the gate guard TOWER straddles the WALL just east of the gate, likewise tilted to the wall
            # there - and NUDGED INWARD so its footing stands on the berm, not in the moat (below)
            _arc = 78
            twx, twy, tang_e = self._wall_walk(pts, g_idx, _arc, west=g_east)
            # walk the tower along the wall until it clears BOTH any kido spot AND this gate's guard
            # house / inspection footprints - the two sit on opposite flanks of the gate but converge
            # near the opening on a tight ring (city_gate_towers_clear_of_gate_furniture, GM 2026-07)
            _gfurn = [(f["x"], f["y"], f["w"], f["h"]) for f in self.M["gate_structs"] if f.get("kind") in ("guardhouse", "inspection")][-2:]

            def _tower_blocked(tx: float, ty: float, _gfurn: Any = _gfurn) -> bool:  # bind loop var (used within this iteration)
                if any(math.hypot(tx - kx_, ty - ky_) < 62 for kx_, ky_ in tower_skip):
                    return True
                return any(abs(tx - fx) < (40 + fw) / 2 + 3 and abs(ty - fy) < (40 + fh) / 2 + 3 for fx, fy, fw, fh in _gfurn)

            while _tower_blocked(twx, twy) and _arc < 240:
                _arc += 20  # a kido or the gate furniture sits there - walk the tower further along the wall
                twx, twy, tang_e = self._wall_walk(pts, g_idx, _arc, west=g_east)
            ta = (tang_e + 90) % 180 - 90
            twx, twy = _berm_nudge(twx, twy, 40)
            tz = self._tower(twx, twy, ta, wc, tw=40)
            self.M["gate_structs"].append({"x": twx, "y": twy, "w": 40, "h": 40, "rot": round(ta, 1), "kind": "tower", "z": tz})
            self.label(insp_xy[0] + 14, insp_xy[1] + 45, "gate guard house + inspection", 9, italic=True, color="#5A4326")
            for gs in self.M["gate_structs"][-3:]:
                bm = 30
                self.block_polys.append(
                    [
                        (gs["x"] - gs["w"] / 2 - bm, gs["y"] - gs["h"] / 2 - bm),
                        (gs["x"] + gs["w"] / 2 + bm, gs["y"] - gs["h"] / 2 - bm),
                        (gs["x"] + gs["w"] / 2 + bm, gs["y"] + gs["h"] / 2 + bm),
                        (gs["x"] - gs["w"] / 2 - bm, gs["y"] + gs["h"] / 2 + bm),
                    ]
                )
        # GUARD TOWERS at regular intervals around the rampart, in addition to the gate towers: a
        # fortified city is towered for enfilading fire along the wall face (a bowshot apart), and the
        # towers also house the stairs up to the parapet. Even spacing at every other wall vertex,
        # skipping the gate vertices (those already have a tower).
        self.M.setdefault("wall_towers", [])  # the gate towers were already added above (via _tower)
        gate_towers = [(gs["x"], gs["y"]) for gs in self.M.get("gate_structs", []) if gs.get("kind") == "tower"]
        # a mural tower must also clear each gate's INSPECTION / GUARD HOUSE (they sit INWARD from the
        # gate, so the 130px gate-vertex filter alone misses them - city_gate_towers_clear_of_gate_furniture)
        gate_furn = [(gs["x"], gs["y"]) for gs in self.M.get("gate_structs", []) if gs.get("kind") in ("guardhouse", "inspection")]
        for i in range(0, n, 2):
            vx, vy = pts[i]
            if any(math.hypot(vx - gx, vy - gy) < 130 for gx, gy in gates):
                continue
            if any(math.hypot(vx - wx2, vy - wy2) < 70 for wx2, wy2 in water_gates):
                continue  # the water-gate arch takes this vertex
            if any(math.hypot(vx - tx2, vy - ty2) < 110 for tx2, ty2 in gate_towers):
                continue  # a mural tower shoulder-to-shoulder with a gate tower reads as a double (GM, 2026-07)
            ta_i = tang[i]
            if any(math.hypot(vx - kx_, vy - ky_) < 62 for kx_, ky_ in tower_skip) or any(math.hypot(vx - fx_, vy - fy_) < 66 for fx_, fy_ in gate_furn):
                # yield to the future kido by SLIDING a short way along the wall, not jumping a
                # whole vertex - a vertex jump left a ~360px towerless stretch on Tango's east
                # wall (the GM: "what if someone attacked the city from the east?"). Try growing
                # arcs in both directions; the first clear spot wins, so coverage stays even.
                slid: Any = None
                for _arc in (44, 62, 80, 98):
                    for _west in (False, True):
                        sx_, sy_, se_ = self._wall_walk(pts, i, _arc, west=_west)
                        if (
                            all(math.hypot(sx_ - kx_, sy_ - ky_) >= 62 for kx_, ky_ in tower_skip)
                            and all(math.hypot(sx_ - fx_, sy_ - fy_) >= 66 for fx_, fy_ in gate_furn)
                            and all(math.hypot(sx_ - gx, sy_ - gy) >= 130 for gx, gy in gates)
                        ):
                            slid = (sx_, sy_, (se_ + 90) % 180 - 90)
                            break
                    if slid:
                        break
                if not slid:
                    continue  # boxed in on both sides - drop this tower (spacing tolerates one gap)
                vx, vy, ta_i = slid
            nvx, nvy = _berm_nudge(vx, vy, 38)
            self._tower(nvx, nvy, ta_i, wc)
        self.M["wall"] = [[x, y] for x, y in pts]
        self.M["gates"] = [[gx, gy] for gx, gy in gates]
        if gates:
            self.M["gate"] = [gates[0][0], gates[0][1]]
        self.corridors.append(([(x, y) for x, y in ring], 46))

    def moat(self, ring: Any, gap: float = 42, width: float | None = None, river: Any = None, river_cut: float = 150) -> list[Pt]:
        """A water moat encircling the city wall - the wall RING pushed outward from its centroid
        by `gap`. Records M['moat']. Feed it from off-map with a stream (AS WIDE as the moat, by
        conservation of flow) and tap it for irrigation channels to the outside fields. A no-build
        corridor. Width ~26 px: a provincial-city defensive moat is the heaviest watercourse on the
        map (Himeji-tier ~20-35 m real, ~70x a field ditch); see the settlements.md water-width ladder.
        `river=<pts>` makes it an OPEN moat for a river-bank city: the arc facing the river (moat
        vertices within `river_cut` of the river centerline) is dropped and both open ends extend
        ONTO the river, which closes the water ring itself - inlet upstream, outlet downstream,
        so the current flushes the moat (the historical norm; see settlements.md river-city entry)."""
        if width is None:
            width = self.px(66)  # a provincial-seat moat ~66 ft across (26px at the old 2.55 ft/px grain)
        cx = sum(p[0] for p in ring) / len(ring)
        cy = sum(p[1] for p in ring) / len(ring)
        mo: list[Pt] = []
        for x, y in ring:
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy) or 1.0
            mo.append((x + dx / d * gap, y + dy / d * gap))
        if river:

            def rdist(q: Any) -> float:
                return min(seg_dist(q[0], q[1], river[i], river[i + 1]) for i in range(len(river) - 1))

            def rfoot(q: Any) -> Pt:
                k = min(range(len(river) - 1), key=lambda i: seg_dist(q[0], q[1], river[i], river[i + 1]))
                return seg_closest(q[0], q[1], river[k], river[k + 1])

            keep = [q for q in mo if rdist(q) >= river_cut]
            # rotate so the kept arc is CONTIGUOUS (the cut can straddle the list seam)
            n0 = len(mo)
            start = next(i for i in range(n0) if rdist(mo[i]) < river_cut and rdist(mo[(i + 1) % n0]) >= river_cut)
            keep = []
            i = (start + 1) % n0
            while rdist(mo[i]) >= river_cut:
                keep.append(mo[i])
                i = (i + 1) % n0
            mo = [rfoot(keep[0])] + keep + [rfoot(keep[-1])]  # both open ends join the river centerline
        else:
            mo.append(mo[0])
        dd = 'M' + ' L'.join(f'{x:.0f},{y:.0f}' for x, y in mo)
        self.M["moat"] = [[round(x, 1), round(y, 1)] for x, y in mo]
        self.M["moat_width"] = width
        ml: dict[str, Any] = {}  # records the moat's bed/sheen draw positions
        self.M["moat_layer"] = ml
        self._water(  # routed through the shared water groups so a feeder stream merges into it cleanly
            f'<path d="{dd}" fill="none" stroke="#9CB4C8" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>',
            ml,
            sheen=f'<path d="{dd}" fill="none" stroke="#B6CAD8" stroke-width="{width * 0.4:.0f}" stroke-linejoin="round" stroke-linecap="round"/>',
        )  # lighter mid-water sheen (NOT a dashed lane line)
        self.corridors.append(([(x, y) for x, y in mo], 28))
        return [(round(x, 1), round(y, 1)) for x, y in mo]

    def water_gate(self, x: float, y: float, rot: float = 0.0) -> int:
        """A WATER GATE (shuimen) - the masonry arch where a cargo canal passes the rampart (the
        Suzhou Pan Gate pattern: a paired land-and-water city, the water passage under a grated
        arch with a sluice). Drawn in the TOP layer so the canal flows visibly beneath it; the
        wall itself must be drawn with a matching gap (city_wall(water_gates=[...])). Records
        M['water_gates'] and reserves a small no-build block."""
        wc = '#3A352C'
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        g.append(f'<rect x="-17" y="-9" width="8" height="18" fill="#9C8A66" stroke="{wc}" stroke-width="1.6"/>')  # piers
        g.append(f'<rect x="9" y="-9" width="8" height="18" fill="#9C8A66" stroke="{wc}" stroke-width="1.6"/>')
        g.append(f'<path d="M-14,-9 C-8,-19 8,-19 14,-9" fill="none" stroke="{wc}" stroke-width="3.4"/>')  # the arch
        for gx_ in (-6, -1, 4):
            g.append(f'<line x1="{gx_}" y1="-8" x2="{gx_}" y2="6" stroke="{wc}" stroke-width="1.1" opacity="0.7"/>')  # the grate/sluice bars
        g.append('</g>')
        z = self.add_top(''.join(g))
        self.M.setdefault("water_gates", []).append({"x": round(x, 1), "y": round(y, 1), "w": 36, "h": 22, "rot": round(rot, 1), "z": z})
        bm = 16
        self.block_polys.append([(x - 18 - bm, y - 11 - bm), (x + 18 + bm, y - 11 - bm), (x + 18 + bm, y + 11 + bm), (x - 18 - bm, y + 11 + bm)])
        return z

    def canal(self, pts: Any, width: float | None = None) -> float:
        """A navigable CARGO CANAL - the one way water legitimately enters a walled city (through
        a water gate; the trunk river never does - the Kaifeng lesson). A middle tier on the
        water-width ladder: clearly heavier than an irrigation hairline, clearly lighter than the
        moat/river. Drawn through the shared water block (it merges with the moat/river/dock and
        passes UNDER the rampart at the gate); records M['canals'] + a no-build corridor."""
        if width is None:
            width = self.px(36)  # a poling barge canal ~36 ft
        dd = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        rec = {"poly": [[round(x, 1), round(y, 1)] for x, y in pts], "w": width}
        self.M.setdefault("canals", []).append(rec)
        self._water(
            f'<path d="{dd}" fill="none" stroke="#9CB4C8" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>',
            rec,
            sheen=f'<path d="{dd}" fill="none" stroke="#B6CAD8" stroke-width="{max(2, width * 0.35):.0f}" stroke-linejoin="round" stroke-linecap="round"/>',
        )
        self.corridors.append(([(x, y) for x, y in pts], width / 2 + 16))
        return width

    def dock(self, cx: float, cy: float, w: float, h: float) -> Pt:
        """An in-city DOCK BASIN at the head of the cargo canal - a rectangular cut of open water
        with a stone quay lip, where the barges tie up (the Jiangnan water-city pattern). Records
        M['docks']; blocks placement so the merchant rows leave the quay clear."""
        self._water(
            f'<rect x="{cx - w / 2:.0f}" y="{cy - h / 2:.0f}" width="{w}" height="{h}" rx="3" fill="#9CB4C8"/>',
            {},
            sheen=f'<rect x="{cx - w / 2 + 4:.0f}" y="{cy - h / 2 + 4:.0f}" width="{w - 8}" height="{h - 8}" rx="2" fill="#B6CAD8" opacity="0.5"/>',
        )
        self.add(f'<rect x="{cx - w / 2:.0f}" y="{cy - h / 2:.0f}" width="{w}" height="{h}" rx="3" fill="none" stroke="#7A6A48" stroke-width="2.2"/>')
        self.M.setdefault("docks", []).append({"x": cx, "y": cy, "w": w, "h": h, "rot": 0})
        self.placed.append((cx, cy, w + 14, h + 14))
        return (cx, cy)

    def jetty(self, x: float, y: float, rot: float = 0.0, length: float | None = None) -> int:
        """A timber JETTY - a planked finger running out from the riverbank into the water, where
        the river craft moor (the wharf suburb outside a river city's water-side gate). Drawn in
        the TOP layer over the water; records M['jetties']."""
        if length is None:
            length = self.px(60)
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        g.append(f'<rect x="0" y="-3.2" width="{length:.0f}" height="6.4" fill="#B0905E" stroke="#59431F" stroke-width="1.1"/>')
        for px_ in range(6, int(length), 9):
            g.append(f'<line x1="{px_}" y1="-3" x2="{px_}" y2="3" stroke="#59431F" stroke-width="0.7" opacity="0.6"/>')
        g.append('</g>')
        z = self.add_top(''.join(g))
        self.M.setdefault("jetties", []).append({"x": round(x, 1), "y": round(y, 1), "rot": round(rot, 1), "len": round(length, 1), "z": z})
        return z

    def bridge(self, x: float, y: float, rot: float, span: float, deck_w: float) -> int:
        """A timber BRIDGE carrying a road (or town street) over a watercourse - a stream, an
        irrigation channel, or the city moat at a gate. Centered on the crossing (x, y); the deck
        runs along `rot` (the road's bearing, degrees) for `span` px (long enough to reach both
        banks) and is `deck_w` wide (the carried road's width). Drawn on the TOP layer so it sits
        ABOVE the water and the roadbed. Records M['bridges']."""
        hl, hw = span / 2, deck_w / 2
        g = [f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.1f})">']
        g.append(f'<rect x="{-hl:.1f}" y="{-hw:.1f}" width="{span:.1f}" height="{deck_w:.1f}" rx="2" fill="#B68D5A" stroke="#5A3F1E" stroke-width="1.6"/>')  # the planked timber deck
        step = max(7, span / 8)  # plank seams across the deck
        sx = -hl + step
        while sx < hl - 1:
            g.append(f'<line x1="{sx:.1f}" y1="{-hw:.1f}" x2="{sx:.1f}" y2="{hw:.1f}" stroke="#5A3F1E" stroke-width="0.7" opacity="0.55"/>')
            sx += step
        g.append(f'<rect x="{-hl:.1f}" y="{-hw - 2.4:.1f}" width="{span:.1f}" height="2.6" fill="#5A3F1E"/>')  # the two side rails
        g.append(f'<rect x="{-hl:.1f}" y="{hw - 0.2:.1f}" width="{span:.1f}" height="2.6" fill="#5A3F1E"/>')
        g.append('</g>')
        z = self.add_top(''.join(g))
        self.M.setdefault("bridges", []).append({"x": round(x, 1), "y": round(y, 1), "rot": round(rot, 1), "span": round(span, 1), "w": round(deck_w, 1), "z": z})
        return z

    def bridges(self) -> int:
        """Auto-span every place a road or town street CROSSES a watercourse with a s.bridge(),
        oriented along the road. Call AFTER all roads/streets AND all water (streams, channels,
        the moat) are placed - a watercourse added later would leave an unbridged crossing (which
        the `roads_bridge_water` check then flags). Returns the number of bridges drawn. Historically
        a walled city's approach road crossed the moat on a bridge at each gate, and a country road
        crossed a stream on a timber bridge."""
        carried: list[Any] = []
        if self.M.get("road"):
            carried.append((self.M["road"], self.M.get("road_width", 26)))
        for st in self.M.get("town_streets", []):
            carried.append((st["pts"], st["w"]))
        for ln in self.M.get("lanes", []):  # a village LANE/path crosses a canal on a plank footbridge
            carried.append((ln["pts"], ln.get("w", 6)))
        waters: list[Any] = []
        for s in self.M.get("streams", []):
            waters.append((s["poly"], s.get("w", 9)))
        for c in self.M.get("channels", []):
            waters.append((c["poly"], 4.2))
        for d in self.M.get("field_ditches", []):  # the irrigation canals a village path must bridge to reach the paddy
            waters.append((d["poly"], d.get("w", 4.2)))
        if self.M.get("moat"):
            waters.append((self.M["moat"], self.M.get("moat_width", 22)))
        n = 0
        for rpts, rw in carried:
            for i in range(len(rpts) - 1):
                ra, rb = tuple(rpts[i]), tuple(rpts[i + 1])
                for wpts, ww in waters:
                    for j in range(len(wpts) - 1):
                        wa, wb = tuple(wpts[j]), tuple(wpts[j + 1])
                        if segments_cross(ra, rb, wa, wb):
                            # segments_cross is True only for a genuine (non-parallel) crossing, so
                            # seg_intersect always returns a point here
                            p = cast(Pt, seg_intersect(ra, rb, wa, wb))
                            rot = math.degrees(math.atan2(rb[1] - ra[1], rb[0] - ra[0]))
                            self.bridge(p[0], p[1], rot, ww + max(28, rw), rw)  # span reaches both banks + abutments
                            n += 1
        return n

    def channel_footbridges(self, spacing: float = 320, min_len: float = 140, plank_w: float = 2.5) -> int:
        """Standalone plank FOOTBRIDGES across the irrigation channels, where field-workers cross a ditch while
        walking the paddy bunds - NOT carried by any lane (people reach them along the earthen bunds, so no
        path leads to them). Any ditch stretch longer than `min_len` gets a plank about MIDWAY; a long stretch
        gets one roughly every `spacing` px, evenly spaced along it. Each plank crosses PERPENDICULAR to the
        ditch, spanning its local width plus short abutments. Call AFTER the field ditches are recorded. Bridges
        draw on the TOP layer (over the water). Records via `bridge()` into M['bridges']; returns the count.
        DECK WIDTH (1 px = 2 ft): a dobashi footplank is a single-file crossing (~3-5 ft), so `plank_w=2.5`
        (~5 ft) - the honest upper end, kept just wide enough to read. It must stay NARROWER than a cart lane
        (~5-6 px); the wider `bridges()` carried-way deck matches the lane it carries, but a footplank does not."""

        def _at(pts: Any, seg: Any, s: float) -> Any:  # point + heading (deg) at arc-length s along the polyline
            acc = 0.0
            for i, sl in enumerate(seg):
                if acc + sl >= s or i == len(seg) - 1:
                    fr = (s - acc) / sl if sl else 0.0
                    ax, ay = pts[i]
                    bx, by = pts[i + 1]
                    return (ax + (bx - ax) * fr, ay + (by - ay) * fr, math.degrees(math.atan2(by - ay, bx - ax)))
                acc += sl

        def _corners(cx: float, cy: float, w: float, h: float, deg: float) -> list[Pt]:
            a = math.radians(deg)
            ca, sa = math.cos(a), math.sin(a)
            return [(cx + dx * ca - dy * sa, cy + dx * sa + dy * ca) for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]

        def _sat(p: Any, q: Any) -> bool:  # separating-axis rect overlap (matches bridges_clear_of_houses)
            for poly in (p, q):
                for i in range(4):
                    x1, y1 = poly[i]
                    x2, y2 = poly[(i + 1) % 4]
                    nx, ny = -(y2 - y1), (x2 - x1)
                    pa = [nx * x + ny * y for x, y in p]
                    qa = [nx * x + ny * y for x, y in q]
                    if max(pa) < min(qa) or max(qa) < min(pa):
                        return False
            return True

        houses = [_corners(h["x"], h["y"], h["w"], h["h"], h.get("rot", 0)) for h in self.M.get("houses", [])]
        n0 = len(self.M.get("bridges", []))
        for d in self.M.get("field_ditches", []):
            pts = d["poly"]
            seg = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
            total = sum(seg)
            if total < min_len:
                continue  # a short stub (e.g. the head-race) is stepped over, no plank
            n = max(1, round(total / spacing))
            w = d.get("w", 4.2)
            for k in range(n):
                base = (k + 0.5) / n * total  # midway for n=1, evenly spaced otherwise
                px, py, ang = _at(pts, seg, base)
                for frac in (0.12, -0.12, 0.24, -0.24, 0.36, -0.36):  # a plank must not land on a home: SLIDE along the ditch to dodge one
                    if not any(_sat(_corners(px, py, w + 15, plank_w, ang + 90), hc) for hc in houses):
                        break
                    px, py, ang = _at(pts, seg, max(0.0, min(total, base + frac * total)))
                self.bridge(px, py, ang + 90, w + 15, plank_w)  # deck runs ACROSS the ditch (perpendicular)
        return len(self.M["bridges"]) - n0

    def governor_mansion(self, x: float, y: float, w: float = 320, h: float = 210, label: str = "Governor's Mansion", gate_dir: str = "west") -> Any:
        """The provincial governor's walled mansion - a large compound, grander than a county
        magistrate's manor. Reuses the manor glyph (walls + gate + empty court; the interior is
        a separate Mode A diagram) and moves the record to M['governor_mansion']."""
        self.manor(x, y, w, h, label, gate_dir=gate_dir, gate_ft=18.0)  # a yamen's formal gatehouse passes ~18 real ft
        self.M["governor_mansion"] = self.M["manors"].pop()  # not an outside samurai estate
        return self.M["governor_mansion"]

    def ministry(self, x: float, y: float, name: str, w: Any = None, h: Any = None, label_below: bool | None = None) -> None:
        """A provincial ministry office (one of the SIX). Records to M['ministries'] with its
        `name`; exactly one city-wide must be the Ministry of Rites (sited in the temple
        neighborhood). Official violet roof so it reads apart from housing/commerce."""
        if w is None:
            w, h = self.px(224), self.px(148)  # a ministry office compound ~224x148 ft (was 88px at the 0.42-grain city)
        self.add(f'<rect x="{x - w / 2:.0f}" y="{y - h / 2:.0f}" width="{w}" height="{h}" rx="2" fill="#BCA6C4" stroke="#463653" stroke-width="2"/>')
        self.add(f'<rect x="{x - w / 2:.0f}" y="{y - h / 2:.0f}" width="{w}" height="9" fill="#6A4A78"/>')
        self.add(f'<line x1="{x - w * 0.3:.0f}" y1="{y:.0f}" x2="{x + w * 0.3:.0f}" y2="{y:.0f}" stroke="#463653" stroke-width="0.7" opacity="0.6"/>')
        self.M["ministries"].append({"x": x, "y": y, "w": w, "h": h, "name": name})
        self.placed.append((x, y, w, h))
        bm = max(30 * self.bscale, 26)  # a building-half margin at the map's grain, floored so a dwelling's corner keeps the 14px office-abut clearance
        self.block_polys.append([(x - w / 2 - bm, y - h / 2 - bm), (x + w / 2 + bm, y - h / 2 - bm), (x + w / 2 + bm, y + h / 2 + bm), (x - w / 2 - bm, y + h / 2 + bm)])
        if label_below is None:
            label_below = self._label_hits(x, y - h / 2 - 9, name, 9) > self._label_hits(x, y + h / 2 + 11, name, 9)
        self.label(x, y + h / 2 + 11 if label_below else y - h / 2 - 9, name, 9, italic=True, color="#463653")

    def _label_hits(self, lx: float, ly: float, text: str, size: float) -> int:
        """How many already-placed footprints (buildings/houses + homestead groves) a label at
        (lx, ly) would cover. The cheap scorer behind auto label placement: prefer a label spot
        in EMPTY ground; when every spot overlaps something, take the least (GM label doctrine,
        2026-07). AABB against self.placed + grove_rects - a few thousand float compares, so it
        stays render-cheap."""
        hw, hh = len(text) * size * 0.31 + 4, size * 0.75 + 4  # +4: a label that CLEARS by a hair still reads as touching
        n = 0
        for px, py, pw, ph in self.placed:
            if abs(px - lx) < hw + pw / 2 and abs(py - ly) < hh + ph / 2:
                n += 1
        for gx, gy, gw, gh in self.grove_rects:
            if abs(gx - lx) < hw + gw / 2 and abs(gy - ly) < hh + gh / 2:
                n += 1
        for gs in self.M.get("gate_structs", []) + self.M.get("wall_towers", []):
            if abs(gs["x"] - lx) < hw + gs["w"] / 2 and abs(gs["y"] - ly) < hh + gs["h"] / 2:
                n += 1
        # the LINE features a label must not straddle: the rampart, the moat, the road itself,
        # and open water - tested as stroke-vs-label-box distance on the box's corner/center points
        lines: list[Any] = []
        if self.M.get("wall"):
            lines.append((self.M["wall"], 7))
        if self.M.get("moat_layer") or self.M.get("moat"):
            lines.append((self.M.get("moat_layer") or self.M.get("moat"), self.M.get("moat_width", 22) / 2))
        if self.M.get("road"):
            lines.append((self.M["road"], self.M.get("road_width", 26) / 2))
        for st in self.M.get("streams", []):
            lines.append((st["poly"], st.get("w", 9) / 2))
        for pts, half in lines:
            hit = False
            for k in range(len(pts) - 1):
                for qx, qy in ((lx - hw, ly - hh), (lx + hw, ly - hh), (lx + hw, ly + hh), (lx - hw, ly + hh), (lx, ly)):
                    px2, py2 = seg_closest(qx, qy, pts[k], pts[k + 1])
                    if abs(px2 - lx) < hw + half and abs(py2 - ly) < hh + half and math.hypot(px2 - qx, py2 - qy) < half + 6:
                        n += 1
                        hit = True
                        break
                if hit:
                    break
            if hit:
                continue
        return n

    def forest_patch(self, base: Any, label: Any = None, label_xy: Any = None) -> None:
        """A bounded copse (organic polygon), as opposed to forest() which fills to
        the canvas edge. Blocks houses; deterministic tree scatter."""
        outline = organic_poly(base, 22)
        sm = smooth_points(outline)
        d = smooth_closed(outline)
        cid = self._cid('copse')
        self.add(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
        self.add(f'<path d="{d}" fill="#A9B98C" stroke="#4E6B3C" stroke-width="1.5"/>')
        xs = [p[0] for p in sm]
        ys = [p[1] for p in sm]
        st = random.getstate()
        random.seed(12)
        self.add(f'<g clip-path="url(#{cid})">')
        yy = min(ys) + 12
        while yy < max(ys):
            xx = min(xs) + 12
            while xx < max(xs):
                tx, ty = xx + random.uniform(-8, 8), yy + random.uniform(-8, 8)
                if point_in_poly(tx, ty, sm):
                    rr = random.uniform(6, 9)
                    self.add(f'<circle cx="{tx:.0f}" cy="{ty:.0f}" r="{rr:.1f}" fill="#6E8B4C" stroke="#4E6B3C" stroke-width="0.7"/>')
                    self.add(f'<circle cx="{tx - 1.5:.0f}" cy="{ty - 1.5:.0f}" r="{rr * 0.4:.1f}" fill="#8FA968"/>')
                xx += 30
            yy += 28
        self.add('</g>')
        random.setstate(st)
        self.block_polys.append(sm)
        self.M["forest_patches"].append([[round(x, 1), round(y, 1)] for x, y in sm])
        if label:
            lx, ly = label_xy if label_xy else ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
            self.label(lx, ly, label, 12, italic=True, weight="bold", color="#3E5631")

    def wall(self, pts: Any, gate: Any = None, label: Any = None, guardtower: bool = True) -> None:
        """An irregular town rampart (thick polyline; may be an open arc anchored to a
        hill). gate=(x,y): a gap with posts, a guard station, and an optional guardtower.
        Recorded so the gate can check the wall and gate exist. No-build corridor."""
        wc = '#3A352C'
        # the rampart renders in the WALL layer (over the ground lanes - a street running into it passes
        # UNDER it), with a genuine gap at the gate so the road shows through the opening
        dd = self._gapped_ring(pts, [gate] if gate else [], 36, closed=False)
        self.M["wall_z"] = self.add_wall(f'<path d="{dd}" fill="none" stroke="{wc}" stroke-width="10" stroke-linejoin="round" stroke-linecap="round"/>')
        self.add_wall(f'<path d="{dd}" fill="none" stroke="#6B5A3A" stroke-width="3" stroke-linejoin="round" opacity="0.5"/>')
        if gate:
            gx, gy = gate
            self.add_wall(f'<rect x="{gx - 42:.0f}" y="{gy - 24:.0f}" width="14" height="48" fill="{wc}"/>')  # gateposts (frame the opening)
            self.add_wall(f'<rect x="{gx + 28:.0f}" y="{gy - 24:.0f}" width="14" height="48" fill="{wc}"/>')
            # the gatehouse (guard station + tower) goes in the TOP layer: a street running
            # through the gate passes UNDER it, not over it
            gz = self.add_top(f'<rect x="{gx - 48:.0f}" y="{gy + 26:.0f}" width="96" height="46" rx="2" fill="#C9A57A" stroke="#5A4326" stroke-width="1.6"/>')  # guard station
            self.add_top(f'<line x1="{gx - 48:.0f}" y1="{gy + 49:.0f}" x2="{gx + 48:.0f}" y2="{gy + 49:.0f}" stroke="#5A4326" stroke-width="0.8"/>')
            self.M["gate_structs"] = [{"x": gx, "y": gy + 49, "w": 96, "h": 46, "z": gz}]  # guard station
            if guardtower:
                tz = self.add_top(f'<rect x="{gx + 50:.0f}" y="{gy - 44:.0f}" width="40" height="40" fill="#9C8A66" stroke="{wc}" stroke-width="2.4"/>')  # guardtower
                self.add_top(f'<rect x="{gx + 58:.0f}" y="{gy - 36:.0f}" width="24" height="24" fill="#6B5A3A"/>')
                self.M["gate_structs"].append({"x": gx + 70, "y": gy - 24, "w": 40, "h": 40, "z": tz})
            # block the guard station / tower from placement (rect + a building-half margin)
            for gs in self.M["gate_structs"]:
                bm = 32
                self.block_polys.append(
                    [
                        (gs["x"] - gs["w"] / 2 - bm, gs["y"] - gs["h"] / 2 - bm),
                        (gs["x"] + gs["w"] / 2 + bm, gs["y"] - gs["h"] / 2 - bm),
                        (gs["x"] + gs["w"] / 2 + bm, gs["y"] + gs["h"] / 2 + bm),
                        (gs["x"] - gs["w"] / 2 - bm, gs["y"] + gs["h"] / 2 + bm),
                    ]
                )
            self.M["gate"] = [gx, gy]
        self.M["wall"] = [[x, y] for x, y in pts]
        # no-build clearance kept wide enough that even a large building's CORNER (not
        # just its center) stays off the rampart stroke (half-diagonal of a 60x40 ~36)
        self.corridors.append(([(x, y) for x, y in pts], 46))
        if label:
            self.label(pts[0][0], pts[0][1] - 16, label, 12, italic=True, weight="bold", color=wc)

    def flower_field(self, shape: Any, label: Any = None, amp: float = 30, label_xy: Any = None, kind: str = "chrysanthemum", flat_west: bool = False) -> None:
        """An ornamental flower field (e.g. chrysanthemums - the Imperial flower).
        Organic outline like a paddy, but rows of gold blooms instead of rice.
        flat_west keeps the west edge straight so it can run flush against a town wall."""
        outline = (
            organic_bbox(shape, amp, flat_edges=cast("tuple[int, ...]", {3} if flat_west else ())) if len(shape) == 4 and all(isinstance(v, (int, float)) for v in shape) else organic_poly(shape, amp)
        )
        sm = smooth_points(outline)
        d = smooth_closed(outline)
        cid = self._cid('flower')
        self.add(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
        self.add(f'<g clip-path="url(#{cid})">')
        self.add(
            f'<rect x="{min(p[0] for p in sm):.0f}" y="{min(p[1] for p in sm):.0f}" '
            f'width="{max(p[0] for p in sm) - min(p[0] for p in sm):.0f}" height="{max(p[1] for p in sm) - min(p[1] for p in sm):.0f}" fill="#B7C089"/>'
        )
        xs, ys = [p[0] for p in sm], [p[1] for p in sm]
        st = random.getstate()
        random.seed(17)
        yy = min(ys) + 12
        while yy < max(ys):
            xx = min(xs) + 12
            while xx < max(xs):
                fx, fy = xx + random.uniform(-4, 4), yy + random.uniform(-4, 4)
                if point_in_poly(fx, fy, sm):
                    self.add(f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="3.4" fill="#E8C84C" stroke="#B89A2E" stroke-width="0.5"/>')
                    self.add(f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="1.2" fill="#FBF2C4"/>')
                xx += 15
            yy += 15
        self.add('</g>')
        random.setstate(st)
        self.add(f'<path d="{d}" fill="none" stroke="#8A8A4A" stroke-width="2.5"/>')
        self.field_polys.append(sm)
        self.M["flower_fields"].append({"kind": kind, "outline": [[round(p[0], 1), round(p[1], 1)] for p in sm]})
        if label:
            lx, ly = label_xy if label_xy else ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
            self.label(lx, ly, label, 11, italic=True, weight="bold", color="#7A6A1A")

    # ---- houses
    def house(self, cx: float, cy: float, w: float, h: float, kind: str = "plain", rot: float = 0, shed: bool = False, shed_side: str = "W") -> None:
        pal = {
            "plain": (random.choice(['#C6AC76', '#BEA26C', '#C2A672', '#B89A62']), '#A98C58', '#5A4326'),
            "big": ('#CFAB64', '#B08C4C', '#4E3A1E'),
            "abandoned": ('#B4AC96', '#9A917A', '#7A7058'),
        }
        light, dark, edge = pal[kind]
        ridge = '#E2CB98' if kind != "abandoned" else '#C7C0AA'
        x0, y0 = -w / 2, -h / 2
        # kura footprint (ox, oy center; sw, sh) in the house's local frame, per side. WEST = a tall block on the
        # west wall (dispersed farms, where the west is free); NORTH = a wide block on the shaded back wall
        # (nucleated farms, where the garden takes the sunnier walls). Shared by the draw + the record below.
        _sox, _soy, _ssw, _ssh = (0.0, -0.60 * h, 0.46 * w, 0.30 * h) if shed_side == "N" else (-0.64 * w, 0.0, 0.32 * w, 0.56 * h)
        g = [f'<g transform="translate({cx:.0f},{cy:.0f}) rotate({rot:.0f})">']
        if shed and kind == "plain":
            g.append(f'<rect x="{_sox - _ssw / 2:.1f}" y="{_soy - _ssh / 2:.1f}" width="{_ssw:.1f}" height="{_ssh:.1f}" rx="2" fill="{dark}" stroke="{edge}" stroke-width="1.1"/>')
        g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w}" height="{h / 2:.1f}" fill="{dark}"/>')
        g.append(f'<rect x="{x0:.1f}" y="0" width="{w}" height="{h / 2:.1f}" fill="{light}"/>')
        dash = ' stroke-dasharray="5,3"' if kind == "abandoned" else ''
        g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w}" height="{h}" rx="3" fill="none" stroke="{edge}" stroke-width="1.5"{dash}/>')
        g.append(f'<line x1="{-w * 0.30:.1f}" y1="0" x2="{w * 0.30:.1f}" y2="0" stroke="{ridge}" stroke-width="2"/>')
        if kind == "big":
            g.append(f'<rect x="{x0 - 1:.1f}" y="{y0 - h * 0.42:.1f}" width="{w * 0.40:.1f}" height="{h * 0.5:.1f}" rx="3" fill="{light}" stroke="{edge}" stroke-width="1.3"/>')
        if kind == "abandoned":
            g.append(f'<polygon points="{-w * 0.16:.1f},{-h * 0.16:.1f} {w * 0.16:.1f},{-h * 0.04:.1f} {-w * 0.04:.1f},{h * 0.2:.1f}" fill="#6E6452" opacity="0.7"/>')
        else:
            g.append(f'<rect x="-3.5" y="{h / 2 - 2:.1f}" width="7" height="3.3" fill="{edge}" opacity="0.85"/>')
        g.append('</g>')
        self.add(''.join(g))
        if shed and kind == "plain":  # record the attached kura so it is first-class + checkable
            th = math.radians(rot)
            self.M.setdefault("farm_sheds", []).append(
                {
                    "x": round(cx + _sox * math.cos(th) - _soy * math.sin(th), 1),
                    "y": round(cy + _sox * math.sin(th) + _soy * math.cos(th), 1),
                    "w": round(_ssw, 1),
                    "h": round(_ssh, 1),
                    "rot": round(rot, 1),
                    "of": [round(cx, 1), round(cy, 1)],
                }
            )

    def _in_blocked(self, x: float, y: float) -> bool:
        # bbox pre-filter (cached, same idea as _rect_hits): a point outside a polygon's bbox - expanded by
        # the 14px field set-back - can neither be inside it nor within 14px of an edge, so skip the O(vertices)
        # point_in_poly / edge_dist. Matters for the one big field envelope and a city's many block polys.
        for poly, (bx0, by0, bx1, by1) in zip(self.field_polys, self._poly_bboxes(self.field_polys), strict=False):
            if x < bx0 - 14 or x > bx1 + 14 or y < by0 - 14 or y > by1 + 14:
                continue
            if point_in_poly(x, y, poly) or edge_dist(x, y, poly) < 14:
                return True
        for poly, (bx0, by0, bx1, by1) in zip(self.block_polys, self._poly_bboxes(self.block_polys), strict=False):
            if x < bx0 or x > bx1 or y < by0 or y > by1:
                continue
            if point_in_poly(x, y, poly):
                return True
        for poly, (bx0, by0, bx1, by1) in zip(self.dry_polys, self._poly_bboxes(self.dry_polys), strict=False):
            if x < bx0 - 12 or x > bx1 + 12 or y < by0 - 12 or y > by1 + 12:
                continue
            if point_in_poly(x, y, poly) or edge_dist(x, y, poly) < 12:
                return True  # dry plots are cropland: a building's whole footprint stays off them
        return any(math.hypot((x - cx) / (rx + 12), (y - cy) / (ry + 12)) < 1.0 for cx, cy, rx, ry in self.ellipses)

    def _near_corridor(self, x: float, y: float, skip: Any = None) -> bool:
        for poly, clearance in self.corridors:
            if poly is skip:  # a frontage row may sit against the street it fronts
                continue
            for k in range(len(poly) - 1):
                a, b = poly[k], poly[k + 1]  # skip a segment whose bbox+clearance can't reach (x,y)
                if x < min(a[0], b[0]) - clearance or x > max(a[0], b[0]) + clearance or y < min(a[1], b[1]) - clearance or y > max(a[1], b[1]) + clearance:
                    continue
                if seg_dist(x, y, a, b) < clearance:
                    return True
        return False

    def _fits(self, x: float, y: float, w: float, h: float, skip: Any = None) -> bool:
        if x < 55 or x > self.W - 55 or y < 88 or y > self.H - 26:  # keep clear of edges + title
            return False
        if self.bound and not point_in_poly(x, y, self.bound):  # stay inside a bounding ring (city wall)
            return False
        if self._in_blocked(x, y) or self._near_corridor(x, y, skip):
            return False
        r = math.hypot(w, h) / 2
        for px, py, pw, ph in self.placed:
            if math.hypot(x - px, y - py) < r + math.hypot(pw, ph) / 2 + 4:
                return False
        return all(math.hypot(x - gx, y - gy) >= r + math.hypot(gw, gh) / 2 + 4 for gx, gy, gw, gh in self.grove_rects)

    def frontage(
        self, street: Any, items: Any, width: float = 24, setback: float = 10, spacing: float = 58, both: bool = True, rows: int = 1, rowgap: float = 9, jitter: float = 4, skip: Any = None
    ) -> int:
        """Place buildings in row(s) along a street, each rotated so its FRONTAGE faces the
        street (shophouses lining the road). rows=2 stacks a second row BACK-TO-BACK behind the
        front one, facing AWAY from the street (GM doctrine 2026-07-18: a door opens onto open
        ground, never into the back row ahead of it - the rear row fronts the back lane/block
        interior, the real ura-dana pattern). Sits against the fronted street (skips that
        street's own corridor - pass skip=<registered poly> when fronting a sub-stretch of a
        longer road) but respects walls, other streets, fields, and collisions."""
        skip = skip if skip is not None else street
        items = list(items)
        seg = [math.hypot(street[i + 1][0] - street[i][0], street[i + 1][1] - street[i][1]) for i in range(len(street) - 1)]
        total = sum(seg)
        sh = width / 2

        def at(d: float) -> tuple[float, float, float, float]:
            acc: float = 0
            for i, sl in enumerate(seg):
                if sl and acc + sl >= d:
                    f = (d - acc) / sl
                    return (
                        street[i][0] + (street[i + 1][0] - street[i][0]) * f,
                        street[i][1] + (street[i + 1][1] - street[i][1]) * f,
                        (street[i + 1][0] - street[i][0]) / sl,
                        (street[i + 1][1] - street[i][1]) / sl,
                    )
                acc += sl
            i = len(seg) - 1  # pragma: no cover
            sl = seg[i] or 1  # pragma: no cover
            return (
                street[-1][0],
                street[-1][1],
                (street[-1][0] - street[-2][0]) / sl,  # pragma: no cover
                (street[-1][1] - street[-2][1]) / sl,
            )  # defensive: while-guard keeps d < total, so a segment always matches

        placed = 0
        d = spacing * 0.55
        sides = [1, -1] if both else [1]
        while d < total and items:
            x, y, tx, ty = at(d)
            for s in sides:
                nx, ny = -ty * s, tx * s  # outward normal (street -> building)
                base_rot = math.degrees(math.atan2(nx, -ny))  # frontage faces the street
                depth = sh + setback
                for ri in range(rows):
                    if not items:
                        break
                    kind = items[0]
                    w, h = self._dims(kind)
                    off = depth + h / 2
                    bx, by = x + nx * off, y + ny * off
                    if self._fits(bx, by, w, h, skip=skip):
                        # rear rows flip 180: back-to-back with the row ahead, door onto the
                        # back lane - never into the front row's rear wall
                        self.building(bx, by, w, h, kind, base_rot + (180 if ri % 2 else 0) + random.uniform(-jitter, jitter))
                        items.pop(0)
                        placed += 1
                        depth = off + h / 2 + rowgap  # next row sits behind this one
                    else:
                        break
            d += spacing
        return placed

    @staticmethod
    def _hjit(x: float, y: float, salt: float) -> float:
        """Deterministic per-position pseudo-random in [0,1) from (x,y,salt) - jitters a homestead's parts
        (house aspect, garden/yard size + shape) WITHOUT a global RNG draw, so it never ripples other
        placement or household counts (position-seeded, exactly like the wealth tier). Real villages were
        never rows of copy-pasted identical farmsteads; this gives each one its own proportions."""
        v = math.sin(x * 12.9898 + y * 4.1414 + salt * 7.373) * 43758.5453
        return v - math.floor(v)

    def _quad(self, cx: float, cy: float, w: float, h: float, jit: float, salt: float) -> list[Pt]:
        """A slightly-IRREGULAR 4-sided polygon INSCRIBED in the (cx,cy,w,h) rect: each corner is pulled
        INWARD by a deterministic, position-seeded fraction (0..jit of the half-span), so the footprint loses
        its perfect 90-degree corners while staying ENTIRELY within its reserved rect - so it can never create
        a new overlap the rect-based placement/checks didn't already clear. Real dooryard plots were bounded by
        paths, walls, and awkward soil, not surveyed to a clean rectangle. `jit` sets how irregular: a garden
        gets more (a hand-worked bed), a threshing yard less (a swept work surface stays near-square). Returns
        the 4 corners [NW, NE, SE, SW] as (x, y) tuples."""
        hw, hh = w / 2.0, h / 2.0
        out: list[Pt] = []
        for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):  # NW, NE, SE, SW
            jx = self._hjit(cx, cy, salt + i * 0.19) * jit  # each corner its own inward pull
            jy = self._hjit(cx, cy, salt + i * 0.19 + 0.5) * jit
            out.append((cx + sx * hw * (1.0 - jx), cy + sy * hh * (1.0 - jy)))
        return out

    def _toscale(self) -> bool:
        """Whether this map uses the to-scale HOMESTEAD BUNDLE (house + grove + yard + garden as one packed
        unit, dimensions in FEET drawn at the map's `ftpx`) vs the legacy house-first path + urban glyphs.
        Every VILLAGE does; a HAMLET opts in with `meta(toscale=True)` (village 2 ft/px, hamlet 1). Every POOL
        map is now to-scale (Moritono was the last legacy hamlet, redone water-first); the legacy house-first
        path is kept as a fallback, covered by `test_settlement.py::test_legacy_dispersed_farmstead_path_still_
        covered`. Kept as one predicate so every to-scale gate stays in sync."""
        m = self.M["meta"]
        return cast(bool, m.get("toscale", m.get("scale") == "village"))

    def try_place(self, x: float, y: float, kind: str, role: Any = None, size: Any = None) -> bool:
        """Place one farmhouse. VILLAGES + HAMLETS + TOWNS use the to-scale HOMESTEAD BUNDLE (house + grove/
        garden + yard, reserved and packed as ONE unit; towns run the NUCLEATED form). CITIES keep the
        shipped house-first path until their own to-scale conversion. `size=(w,h)` overrides the kind's default footprint (base FEET) so
        farmhouses can be individually sized - e.g. a headman is just a LARGER plain farmhouse."""
        if self._toscale():
            return self._try_place_bundle(x, y, kind, role, size)
        return self._try_place_legacy(x, y, kind, role)

    def _try_place_bundle(self, x: float, y: float, kind: str, role: Any = None, size: Any = None) -> bool:
        # a farmhouse shares the MAP'S building grain (bscale): at village/hamlet scale bscale is
        # 1.0 (full size), but a town/city compresses its urban buildings, and a peasant farmhouse
        # must not render LARGER than the samurai and merchant houses inside the walls - so it
        # scales down by the same factor.
        if kind == "abandoned":  # a lone derelict ruin - no homestead bundle
            w, h = self.px(46), self.px(28)  # the 46x28 ft minka, at this map's ft/px
            if not self._fits(x, y, w, h):
                return False
            self.placed.append((x, y, w, h))
            rec = {"x": x, "y": y, "w": w, "h": h, "kind": kind, "rot": random.uniform(-5, 5), "role": role, "shed": False, "wealth": 1.0}
            self.M["houses"].append(rec)
            self._pending_farmsteads.append(rec)
            return True
        # TO-SCALE HOMESTEAD BUNDLE: an occupied farmstead is placed as ONE unit - house + windward grove +
        # threshing yard + dooryard garden - reserved and overlap-checked together so the grove always keeps
        # its ~6:1 room (the fix for groves never reaching target under end-reconciliation). Dimensions are in
        # FEET, drawn at this map's ftpx (village 2 ft/px, hamlet 1): the plain house is the 46x28 ft 8:5 minka
        # (px(46) = 23px at 2 ft/px). A modest, position-seeded wealth tier scales the whole bundle. See
        # settlements.md 'To-scale villages'.
        if size is not None:  # explicit footprint in FEET (e.g. a larger headman)
            wf, hw, hh = 1.0, self.px(size[0]), self.px(size[1])
        elif getattr(self, "_nucleated", False):
            # a minka grew by adding BAYS (ken) along the ridge, so a bigger farmhouse is LONGER far more
            # than it is wider (the roof span caps the depth) - vary length a lot, depth only a little, so
            # houses are individually proportioned (some long, some near-square) but always within the
            # ~1.3-2.5:1 minka norm, never uniformly scaled copies. Position-seeded (no RNG ripple).
            wf = 1.0
            hw = self.px(46) * (0.85 + self._hjit(x, y, 1.0) * 0.5)  # length factor [0.85, 1.35]
            hh = self.px(28) * (0.90 + self._hjit(x, y, 2.0) * 0.2)  # depth factor  [0.90, 1.10]
        else:
            bw, bh = (64, 40) if kind == "big" else (46, 28)  # base minka in FEET
            t = int(abs(x) * 53 + abs(y) * 29) % 100
            wf = 1.0 if kind == "big" else (0.9 if t < 30 else (1.12 if t >= 80 else 1.0))
            hw, hh = self.px(bw) * wf, self.px(bh) * wf
        # a fireproof KURA storehouse is a WEALTH MARKER, not universal - it attaches to the house on ~30% of
        # plain farms (position-seeded off the SEED spot, no RNG ripple; a ruin has none). The HEADMAN always
        # has one (GM 2026-07-21): the shoya/nanushi is by definition among the village's most prosperous
        # farmers - historically the land-opening family - AND the office needs one functionally: the headman
        # kept the village's tax ledgers, land registers, and tax rice awaiting collection, exactly what
        # fireproof kura storage is for. Leaving him on the ~30% dice let all four pool headmen roll bare
        # (chance masquerading as doctrine); headman_has_kura gates it now. It goes on the
        # NORTH (back) wall of a nucleated house: the cluster hugs the field to the EAST so a house's garden takes
        # the west/sunny walls but never the shaded NORTH, so a north kura is clear of it - and its footprint is
        # RESERVED in the homestead bundle so a neighbor never lands on it. Drawn + recorded in farmsteads() so
        # it always moves WITH the house (farm_sheds_attached guards it).
        _shed = kind == "plain" and (role == "headman" or self._hjit(x, y, 3.0) < 0.30)
        spot = self._place_bundle(x, y, hw, hh, shed=_shed)  # pack the bundle (incl. the reserved kura) near (x,y)
        if spot is None:
            return False
        cx, cy, geom = spot
        self.placed.append(geom["bbox"])  # reserve the whole homestead footprint as one rect
        rec = {"x": cx, "y": cy, "w": hw, "h": hh, "kind": kind, "rot": random.uniform(-5, 5), "role": role, "shed": _shed, "shed_side": "N", "wealth": wf, "geom": geom}
        self.M["houses"].append(rec)
        self._pending_farmsteads.append(rec)
        return True

    def _try_place_legacy(self, x: float, y: float, kind: str, role: Any = None) -> bool:
        # a farmhouse shares the MAP'S building grain (bscale): at hamlet scale bscale is 1.0 (full size), but
        # a town/city compresses its urban buildings, and a peasant farmhouse must not render LARGER than the
        # samurai and merchant houses inside the walls - so it scales down by the same factor.
        bw, bh = (60, 40) if kind == "big" else (44, 29)
        wf = 1.0
        if kind == "plain":
            t = int(abs(x) * 53 + abs(y) * 29) % 100
            wf = 0.9 if t < 30 else (1.12 if t >= 80 else 1.0)
        w, h = bw * self.bscale, bh * self.bscale
        if not self._fits(x, y, w, h):
            return False
        rot = random.uniform(-5, 5)
        shed = random.random() < 0.3
        self.placed.append((x, y, w, h))
        rec = {"x": x, "y": y, "w": w, "h": h, "kind": kind, "rot": rot, "role": role, "shed": shed, "wealth": wf}
        self.M["houses"].append(rec)
        self._pending_farmsteads.append(rec)
        return True

    def lane_skeleton(self, kind: str, cx: float, cy: float, ex: float, ey: float, width: float = 5, clearance: float = 18, worn: bool = True) -> dict[str, Any]:
        """Lay a nucleated cluster's internal lanes for the given skeleton and record the skeleton kind on
        the manifest (meta.lane_skeleton, read by the twin-detector). Returns the DERIVED focal points -
        `headman` (place the headman house there) and `gateway` (the downslope exit; anchor the connector
        track and the tutelary shrine off it). The lanes lay their no-build corridors BEFORE the houses,
        so the homesteads front them (same as a hand-placed lane)."""
        layout = skeleton_layout(kind, cx, cy, ex, ey)
        for pts in layout["lanes"]:
            self.lane(pts, width=width, clearance=clearance, worn=worn)
        self.M["meta"]["lane_skeleton"] = kind
        return layout

    def cluster_seeds(self, shape: str, cx: float, cy: float, ex: float, ey: float, n: int, rng: random.Random, record: bool = True) -> list[Pt]:
        """Generate `n` house-seed positions for a nucleated cluster of the given SHAPE (feature 005
        `cluster_shape` knob), to feed to `try_place` (the bundle solver then hugs each homestead to the field
        edge). Records `meta.cluster_shape` when `record=True`. Shapes (grounding: research.md D2 - cluster
        shape followed the available dry ground):
          - `round`     - a filled ellipse (a knoll): the classic disk.
          - `elongated` - a long narrow ellipse (a levee / ridge string): stretched along the margin (the ey axis).
          - `crescent`  - positions hugging a shallow arc (a field-edge crescent), concave toward the field.
          - `split`     - two sub-hamlets on either flank (two dry patches flanking the arable).
        Off the flood toe / field-adjacency are enforced downstream by `try_place` (each candidate that is not
        field-adjacent or lands on a blocker is simply rejected), so this only has to SHAPE the seed cloud."""
        if shape not in ("round", "elongated", "crescent", "split"):
            raise ValueError(f"unknown cluster_shape {shape!r}; expected round / elongated / crescent / split")
        if record:
            self.M["meta"]["cluster_shape"] = shape
        out: list[Pt] = []
        for _ in range(n):
            a = rng.uniform(0, 2 * math.pi)
            r = rng.random() ** 0.5
            if shape == "round":
                out.append((cx + math.cos(a) * r * ex, cy + math.sin(a) * r * ey))
            elif shape == "elongated":  # narrow across the margin, long along it
                out.append((cx + math.cos(a) * r * ex * 0.55, cy + math.sin(a) * r * ey * 1.4))
            elif shape == "crescent":  # a curved band, concave toward the field, NARROW across the margin.
                # The old form spread wide (x1.15 lateral) with the horns curved hard back, so the placer -
                # which pulls every house to hug the paddy and packs ALONG it - strung them into a wide, hollow
                # arc that stranded the horns far from the crops (Kikuta: 55 houses over a hull filled ~20%, NE
                # horn ~400px from any field; see village_cluster_compact / settlements.md 'Cluster compactness').
                # WIDTH is what the placer amplifies, so keep the lateral reach narrow (a nucleated village is a
                # deep blob, not a wide ribbon) and let the depth carry the frontage, with a gentle concave bow.
                t = rng.uniform(-1.0, 1.0)
                depth = rng.random() ** 0.5
                bx = cx + t * ex * 0.5 + math.cos(a) * ex * 0.22 * depth
                by = cy + (t * t - 0.5) * ey * 0.5 + math.sin(a) * ey * 0.95 * depth
                out.append((bx, by))
            else:  # split: two sub-disks on the flanks
                side = -1.0 if rng.random() < 0.5 else 1.0
                out.append((cx + side * ex * 0.62 + math.cos(a) * r * ex * 0.42, cy + math.sin(a) * r * ey * 0.82))
        return out

    def cluster_anchor(self, position: str, field_bbox: tuple[float, float, float, float], down_deg: float, lateral_frac: float = 0.6, depth_frac: float = 0.34) -> tuple[float, float, float, float]:
        """Resolve the `cluster_position` knob into a cluster ANCHOR `(cx, cy, ex, ey)` to feed `cluster_seeds`.
        The knob says WHERE on its field's dry margin a nucleated village sits; this reads that against the
        field's bbox and its `down_deg` fall line and returns a center just OFF the paddy plus screen-axis
        half-extents (`ex`, `ey`) oriented so the cluster runs ALONG that margin. (Field-adjacency + off-the-toe
        are still enforced downstream: `try_place` rejects any seeded house that is not field-adjacent or lands
        on the flood toe / a blocker, so this only has to aim the cloud at the right dry ground.)

        Grounding (research.md D2 - villages took the best DRY ground beside their paddy, 背山面水 'mountain
        behind, water in front'; which dry ground was available varied, and that variation is the knob):
          - `high_margin`  - the upslope (high) edge, centered: the classic back-to-the-hill seat. DEFAULT.
          - `valley_head`  - the high edge but tucked to one cross-slope corner (a head terrace by the intake).
          - `mid_margin`   - the high edge, offset the other way along the margin (partway along, not centered).
          - `flank`        - a cross-slope SIDE margin (a side levee / valley wall), off to one flank.
          - `valley_mouth` - down by the low end where the valley opens, but pulled to the dry lateral shoulder
                             (NEVER straight down into the wet central toe below the drain).
          - `on_rise`      - a dry knoll off a high corner (a rise standing a little out of the plain).
        """
        if position not in ("high_margin", "valley_head", "mid_margin", "flank", "valley_mouth", "on_rise"):
            raise ValueError(f"unknown cluster_position {position!r}")
        fx0, fy0, fx1, fy1 = field_bbox
        fcx, fcy = (fx0 + fx1) / 2, (fy0 + fy1) / 2
        hw, hh = (fx1 - fx0) / 2, (fy1 - fy0) / 2
        dx, dy = math.cos(math.radians(down_deg)), math.sin(math.radians(down_deg))  # downhill unit
        ux, uy = -dy, dx  # cross-slope (lateral / along-margin) unit
        ad = abs(dx) * hw + abs(dy) * hh  # field half-extent along the fall
        au = abs(ux) * hw + abs(uy) * hh  # field half-extent across the fall (the margin's run)
        lat = au * lateral_frac  # the cluster runs ALONG the margin (lateral)...
        dep = min(
            max(ad, au) * depth_frac, 118.0
        )  # ...but stays fairly shallow: the near rows ring the field (field_ringed), the back rows are a legit cluster-span back (cluster_abuts_fields allows it for a nucleated seat)
        clr = dep + 22.0  # the along-slope clearance: the cluster's near edge sits `pad`-ish off the paddy, whole cluster clear
        # (along-slope offset s: -ve = uphill of center; lateral offset t along +u)
        # high-margin lateral offsets stay MODEST (a fan field is narrow at its head, so the bbox overstates
        # how far a high-corner cluster can slide and still sit over the paddy) - the flank/mouth positions push
        # fully out to a cross-slope side where the field is at full width.
        if position == "high_margin":
            s, t = -(ad + clr), 0.0
        elif position == "valley_head":
            s, t = -(ad + clr), -au * 0.3
        elif position == "mid_margin":
            s, t = -(ad + clr), au * 0.3
        elif position == "flank":
            s, t = 0.0, au + clr
        elif position == "valley_mouth":
            s, t = ad * 0.45, au + clr  # low-ish AND pushed to the dry lateral shoulder, never the central toe
        else:  # on_rise: a dry knoll at a HIGH CORNER (up, and a little laterally) - still hugging the high margin
            s, t = -(ad + clr), au * 0.3
        cx = fcx + dx * s + ux * t
        cy = fcy + dy * s + uy * t
        ex = abs(ux) * lat + abs(dx) * dep  # project the lateral+depth extents back onto screen x / y
        ey = abs(uy) * lat + abs(dy) * dep
        return (cx, cy, ex, ey)

    def plot_texture(self, plot_size: str = "medium", plot_regularity: str = "organic", record: bool = True) -> tuple[float, tuple[float, float]]:
        """Resolve the `plot_size` + `plot_regularity` knobs into `build_comb`'s `(plot_across, row_step)` levers
        so they actually change the paddy grain. `plot_across` sets how many bunded plots tile across each canal
        reach (small = many small paddies, large_block = few big ones, strip = narrow but long); `row_step` is
        the along-canal row spacing, and its SPREAD is the regularity: a WIDE spread reads organic/old-grown, a
        TIGHT spread reads as a planned/surveyed grid. Records the two knobs on the manifest. Grounding: old
        wet-rice terraces grew as small irregular paddies fitted to the microtopography; large regular blocks or
        long strips signal a later planned reclamation/allotment (which is why `grid` is typing-gated to a
        planned field origin). Returns `(plot_across, row_step)` to pass straight into `build_comb`."""
        size_map = {
            "small_irregular": (34.0, (20.0, 40.0)),
            "medium": (48.0, (26.0, 36.0)),
            "large_block": (70.0, (30.0, 44.0)),
            "strip": (32.0, (46.0, 66.0)),
        }
        if plot_size not in size_map:
            raise ValueError(f"unknown plot_size {plot_size!r}")
        if plot_regularity not in ("organic", "grid"):
            raise ValueError(f"unknown plot_regularity {plot_regularity!r}")
        across, step = size_map[plot_size]
        if plot_regularity == "grid":  # collapse the row-step spread toward its mean -> even, surveyed rows
            mid = (step[0] + step[1]) / 2
            step = (mid - 3.0, mid + 3.0)
        if record:
            self.M["meta"]["plot_size"] = plot_size
            self.M["meta"]["plot_regularity"] = plot_regularity
        return across, step

    @staticmethod
    def water_sources_for(down_deg: float, water_kind: str) -> list[str]:
        """The `water_source_position` values that gravity-feed a field falling toward `down_deg` (the source
        must sit UPHILL of the field intake - water runs downhill through the comb). Pond kinds are the
        corner/mid/chain set; a stream enters from a canvas edge. A source on the downhill half is excluded
        (it could not feed the field), which is the gravity typing the knob's own `typing_rule` defers to
        placement. Used by the seed roll so an unpinned water source lands somewhere water can actually flow
        from."""
        dx, dy = math.cos(math.radians(down_deg)), math.sin(math.radians(down_deg))
        # each candidate's outward direction from field center; keep those on the UPHILL half (dot with
        # downhill <= a small tolerance, so a cross-slope side counts as feedable)
        dirs = {
            "corner_NW": (-1, -1),
            "corner_NE": (1, -1),
            "corner_SW": (-1, 1),
            "corner_SE": (1, 1),
            "edge_N": (0, -1),
            "edge_E": (1, 0),
            "edge_S": (0, 1),
            "edge_W": (-1, 0),
            "mid_margin": (-dx, -dy),
            "chain": (-dx, -dy),  # the uphill margin itself
        }
        pond = ["corner_NW", "corner_NE", "corner_SW", "corner_SE", "mid_margin", "chain"]
        edge = ["edge_N", "edge_E", "edge_S", "edge_W"]
        names = edge if water_kind == "stream" else pond
        out = []
        for nm in names:
            vx, vy = dirs[nm]
            n = math.hypot(vx, vy) or 1.0
            if (vx / n) * dx + (vy / n) * dy <= 0.35:  # not on the downhill half (tolerance admits cross sides)
                out.append(nm)
        return out

    def water_source_anchor(self, position: str, field_bbox: tuple[float, float, float, float], down_deg: float, pad: float = 90.0) -> Pt:
        """Resolve `water_source_position` into the SLUICE / stream-entry point (where water reaches the field
        head), just off the field on the named margin. Pond positions (`corner_*` / `mid_margin` / `chain`) put
        the feed on that corner or margin; stream `edge_*` positions put it at that canvas-edge margin. RAISES
        if the resolved point is on the DOWNHILL half of the field (gravity: a source below the field cannot
        feed it) - so a historically-impossible pin is rejected here, and `water_sources_for` lists the legal
        set for a roll. Grounding: Chinese canal doctrine feeds a comb from its high end; the varied high-side
        entry (a corner pond, a mid-margin tank, a stepped chain, a stream off one edge) is the knob."""
        if position not in ("corner_NW", "corner_NE", "corner_SW", "corner_SE", "mid_margin", "chain", "edge_N", "edge_E", "edge_S", "edge_W"):
            raise ValueError(f"unknown water_source_position {position!r}")
        fx0, fy0, fx1, fy1 = field_bbox
        fcx, fcy = (fx0 + fx1) / 2, (fy0 + fy1) / 2
        dx, dy = math.cos(math.radians(down_deg)), math.sin(math.radians(down_deg))
        corners = {"corner_NW": (fx0 - pad, fy0 - pad), "corner_NE": (fx1 + pad, fy0 - pad), "corner_SW": (fx0 - pad, fy1 + pad), "corner_SE": (fx1 + pad, fy1 + pad)}
        edges = {"edge_N": (fcx, fy0 - pad), "edge_S": (fcx, fy1 + pad), "edge_E": (fx1 + pad, fcy), "edge_W": (fx0 - pad, fcy)}
        if position in corners:
            sx, sy = corners[position]
        elif position in edges:
            sx, sy = edges[position]
        else:  # mid_margin / chain: the middle of the UPHILL margin (opposite the fall)
            sx, sy = fcx - dx * ((fx1 - fx0) / 2 + pad), fcy - dy * ((fy1 - fy0) / 2 + pad)
        if (sx - fcx) * dx + (sy - fcy) * dy > 0.35 * math.hypot(sx - fcx, sy - fcy):
            raise ValueError(f"water_source_position {position!r} sits downhill of a field falling to {down_deg} deg - it cannot gravity-feed it")
        return (round(sx, 1), round(sy, 1))

    def roll_village(
        self,
        name: str,
        households: int,
        down_deg: float,
        water_kind: str = "pond",
        field_fall: float | None = None,
        offtakes_a: Sequence[float] = (0.22, 0.45, 0.68, 0.88),
        offtakes_b: Sequence[float] = (0.45, 0.8),
        civic_shrine: bool = True,
        frame: bool = True,
        lay_hinterland: bool = True,
    ) -> dict[str, Any]:
        """ROLL a whole gate-passing settlement from the seed (feature 005 US2, SC-004: zero hand-placed
        coordinates). Every unpinned knob is rolled from `self.seed` (pinned ones honored); the rolled values
        then DRIVE the geometry through the resolvers: the water source picks the sluice, plot_texture picks the
        paddy grain, cluster_position + cluster_shape place + shape the homestead cloud, lane_skeleton lays the
        lanes. Two different seeds roll different combinations; the same seed is byte-identical. Call after
        `s.meta(name=, scale=, ftpx=, toscale=True, ...)`. Returns the resolved knob dict. Scope: a nucleated
        HAMLET or VILLAGE (the to-scale tiers); a hamlet needs no headman/shrine/cemetery, a village adds them."""
        from waterfields import build_comb

        self.M["meta"]["water_kind"] = water_kind
        self.M["meta"]["down_deg"] = down_deg
        self.M["meta"]["nucleated"] = True  # a rolled village is a nucleated cluster (per-house-grove path is off; a communal windbreak is drawn below)
        scale = self.M["meta"].get("scale", "village")
        self._nucleated = True
        W, H = self.W, self.H
        dx, dy = math.cos(math.radians(down_deg)), math.sin(math.radians(down_deg))
        # --- roll the knobs (pinned -> rolled -> default) ---
        cluster_position = self.resolve("cluster_position")
        cluster_shape = self.resolve("cluster_shape")
        lane_kind = self.resolve("lane_skeleton")
        plot_size = self.resolve("plot_size")
        plot_regularity = self.resolve("plot_regularity")
        grain_drift = self.resolve("grain_drift")
        if self.knob_pins.get("water_source_position") is not None:
            water_source = self.resolve("water_source_position")
        else:  # roll among the GRAVITY-VALID set (the typing rule defers gravity to placement)
            valid = sorted(self.water_sources_for(down_deg, water_kind))
            # don't put the intake DEAD-CENTER on the high margin where a high-seated village already sits - a
            # center source (mid_margin / chain) would fight the cluster for the narrow fan head, so prefer a
            # corner intake there (historically fine: a corner tank feeding the comb from one high shoulder).
            if cluster_position in ("high_margin", "valley_head", "mid_margin", "on_rise"):
                corner = [v for v in valid if v not in ("mid_margin", "chain")]
                valid = corner or valid
            wr = knob_rng(self.seed, "water_source_position")
            water_source = valid[wr.randrange(len(valid))]
            self._resolved_knobs["water_source_position"] = water_source
        self.M["meta"]["water_source"] = water_source
        # --- the field: sluice from the water source, then the comb ---
        mx, my = W * 0.16, H * 0.16
        # push the nominal field DOWNSLOPE, so its UPHILL margin keeps room for the things that crowd there -
        # the intake AND a high-seated village (a valley_head cluster on a diagonal fall otherwise lands on, or
        # past, the canvas edge, which starves the village and pushes its civic precinct off-frame)
        shift = 0.15 * min(W, H)
        sluice = self.water_source_anchor(water_source, (mx + dx * shift, my + dy * shift, W - mx + dx * shift, H - my + dy * shift), down_deg)
        across, step = self.plot_texture(plot_size, plot_regularity)
        net = build_comb(W, H, sluice, self.seed, down_deg=down_deg, field_fall=field_fall, plot_across=across, row_step=step, grain_drift=grain_drift, offtakes_a=offtakes_a, offtakes_b=offtakes_b)
        self.field_polys.append([(round(x, 1), round(y, 1)) for x, y in net["envelope"]])
        self.meta(dry_furrows_vary=net["furrows_vary"])
        if water_kind == "pond":
            source: dict[str, Any] = {"kind": "pond", "pond": (sluice[0] - dx * 66, sluice[1] - dy * 66, 88.0, 56.0)}
        else:
            source = {"kind": "stream", "stream": [(sluice[0] - dx * 380, sluice[1] - dy * 380), (sluice[0], sluice[1])]}
        # roll the ARCHETYPE knob BEFORE drawing (draw_comb_field reads it to place archetype-appropriate
        # in-field features): field_archetype (only valley_paddy is geometrically implemented, so a roll with
        # no declared terrain lands there by typing).
        self.M["meta"]["field_archetype"] = self.resolve("field_archetype")
        self.draw_comb_field(net, name + "-paddies", source)
        # a land-use OVERLAY drawn over the fresh paddy
        self.apply_land_use(net, self.resolve("land_use_overlay"), random.Random((self.seed ^ 0x1A7D) & 0xFFFFFFFF))
        # --- seat the cluster on the field edge, from the ACTUAL drawn plots (robust to a fan's narrow head) ---
        # The cluster_position gives the CHARACTER (which margin); the seat is computed constructively so it
        # always abuts + rings the field and never fights the water intake: the lateral lean is forced AWAY from
        # the sluice's side, and the seat sits just beyond the drawn rice's reach in that direction. This
        # replaces the earlier anchor+snap+nudge, whose post-hoc pushes destabilised placement roll-to-roll.
        env = net["envelope"]
        exs, eys = [p[0] for p in env], [p[1] for p in env]
        fb = (min(exs), min(eys), max(exs), max(eys))
        verts = [(v[0], v[1]) for p in net["plots"] for v in p["poly"]]
        fcx2 = sum(v[0] for v in verts) / len(verts)
        fcy2 = sum(v[1] for v in verts) / len(verts)
        ux, uy = -dy, dx  # lateral (cross-slope) unit
        away = -1.0 if ((sluice[0] - fcx2) * ux + (sluice[1] - fcy2) * uy) >= 0 else 1.0  # lean opposite the sluice
        along_bias = {"high_margin": -1.0, "valley_head": -1.0, "mid_margin": -1.0, "on_rise": -1.0, "flank": 0.0, "valley_mouth": 0.55}
        lat_bias = {"high_margin": 0.2, "valley_head": 0.6, "mid_margin": 0.6, "on_rise": 0.55, "flank": 1.0, "valley_mouth": 0.95}
        tdx = dx * along_bias[cluster_position] + ux * away * lat_bias[cluster_position]
        tdy = dy * along_bias[cluster_position] + uy * away * lat_bias[cluster_position]
        tl = math.hypot(tdx, tdy) or 1.0
        tdx, tdy = tdx / tl, tdy / tl  # the seat direction (away from the field)
        alx, aly = -tdy, tdx  # ALONG the margin (perpendicular to the seat direction)
        # The cluster is a shallow band in the MARGIN FRAME (along the margin x away from the field), NOT an
        # axis-aligned ellipse: at a diagonal fall the screen-axis extents collapse into a big circle, which
        # sprays seeds over the paddy and starves the village (Kikuta at down_deg=45 placed 3 of 55). Size the
        # band's LENGTH from the household count so a village gets the frontage it needs, and keep its DEPTH
        # shallow so the near rows ring the field.
        # rough bundle pitch per household (house + its yard/garden + the packing gap). Keep this TIGHT: a
        # nucleated village is a dense fabric, and an over-generous pitch spreads the houses into a thin scatter
        # and leaves the skeleton's lanes overshooting into empty ground.
        need = max(1, households) * (56.0 * max(0.6, self.bscale)) ** 2
        # aim for a ~3:1 band (a nucleated village is a blob, not a hairline ribbon): pick the depth that gives
        # that aspect for the area needed, floored so a hamlet stays shallow and capped so it stays a margin band
        dep = max(112.0, min(math.sqrt(need / (3.0 * math.pi)), 240.0))
        lat = max(240.0, min(need / (math.pi * dep), 1500.0))
        reach = max((v[0] - fcx2) * tdx + (v[1] - fcy2) * tdy for v in verts)
        ccx, ccy = fcx2 + tdx * (reach + dep + 30.0), fcy2 + tdy * (reach + dep + 30.0)
        rng = random.Random((self.seed * 2654435761) & 0xFFFFFFFF)

        def to_screen(p: Any) -> Pt:  # margin-frame (along, away-from-field) -> screen
            return (ccx + alx * p[0] + tdx * p[1], ccy + aly * p[0] + tdy * p[1])

        # the lane skeleton is derived in the MARGIN FRAME too, then rotated onto the band - so its lanes run
        # along the margin and its DERIVED headman/gateway land inside the cluster at any fall direction
        layout = skeleton_layout(lane_kind, 0.0, 0.0, lat, dep)
        for lane_pts in layout["lanes"]:
            self.lane([to_screen(p) for p in lane_pts], width=5, clearance=40, worn=True)
        self.M["meta"]["lane_skeleton"] = lane_kind
        sk = {"headman": to_screen(layout["headman"]), "gateway": to_screen(layout["gateway"])}
        placed = 0
        if scale == "village":
            # The headman takes the skeleton's prime spot - but that spot is the JUNCTION itself on a T/Y/cross,
            # and a lane is a no-build corridor, so the compound FRONTS the junction rather than sitting on it:
            # try the spot, then a ring of small offsets around it, taking the first that fits.
            hl = layout["headman"]
            for ox, oy in ((0.0, 0.0), (62.0, 44.0), (-62.0, 44.0), (62.0, -44.0), (-62.0, -44.0), (96.0, 0.0), (-96.0, 0.0)):
                hx, hy = to_screen((hl[0] + ox, hl[1] + oy))
                if self.headman(hx, hy):
                    placed = 1
                    break
        # seeds are shaped in the margin frame, then rotated onto it - so the band hugs the margin at any fall
        for lx, ly in self.cluster_seeds(cluster_shape, 0.0, 0.0, lat, dep, int(households * 3.0) + 18, rng):
            if placed >= households:
                break
            if self.try_place(ccx + alx * lx + tdx * ly, ccy + aly * lx + tdy * ly, "plain"):
                placed += 1
        self.farmsteads()
        hs = self.M["houses"]
        if hs:  # wells among the ACTUAL houses (BEFORE the grove, so the grove's canopy skips them)
            hxs, hys = [h["x"] for h in hs], [h["y"] for h in hs]
            self.place_wells((min(hxs) - 10, min(hys) - 10, max(hxs) + 10, max(hys) + 10), spacing=185, near=104)
        # --- a COMMUNAL windward windbreak BEHIND the cluster (a nucleated village shelters behind one grove,
        # not per-house belts): a belt in the MARGIN FRAME, spanning the band's length on its far-from-field side ---
        # the belt must sit on the WINDWARD (uphill) side in the FALL frame - that is what shelters the village
        # and what village_windbreak_on_windward_side checks - so project the band onto the fall/cross axes
        ux, uy = -dy, dx  # cross-slope
        ext_d = abs(alx * dx + aly * dy) * lat + abs(tdx * dx + tdy * dy) * dep  # the band's reach along the fall
        ext_u = abs(alx * ux + aly * uy) * lat + abs(tdx * ux + tdy * uy) * dep  # ...and across it
        lat_half = ext_u + 34.0
        bc = (ccx - dx * (ext_d + 46), ccy - dy * (ext_d + 46))
        belt = [
            (bc[0] - ux * lat_half - dx * 28, bc[1] - uy * lat_half - dy * 28),
            (bc[0] + ux * lat_half - dx * 28, bc[1] + uy * lat_half - dy * 28),
            (bc[0] + ux * lat_half + dx * 28, bc[1] + uy * lat_half + dy * 28),
            (bc[0] - ux * lat_half + dx * 28, bc[1] - uy * lat_half + dy * 28),
        ]
        belt = [(max(6.0, min(self.W - 6.0, bx)), max(6.0, min(self.H - 6.0, by))) for bx, by in belt]  # keep the belt on-canvas
        self.village_grove(belt, role="windbreak")
        # --- village-only civic features (a hamlet has none) ---
        if scale == "village" and civic_shrine:
            gx, gy = sk["gateway"]
            self.shrine(gx + dx * 46, gy + dy * 46)
        self.bridges()  # carry the lanes over any water they cross
        if self.M.get("field_ditches"):  # planks over the long irrigation ditches
            self.channel_footbridges(spacing=300)
        # `lay_hinterland=False`: a caller that supplies its OWN sacred precinct AFTER roll_village (the
        # civic_shrine=False path) must defer the scrub/marsh scatter until its shrine/torii/graveyard have
        # registered their swept-ground clearings, or the scrub scatters over ground that should read tended.
        # Such a caller calls `s.hinterland()` itself, after placing the precinct.
        if lay_hinterland:
            self.hinterland()
        if frame:  # a caller adding its OWN civic features (a sacred precinct) crops+titles itself, AFTER them
            self.crop_to_content(margin=40)
            self.title(name)
        return {
            "cluster_position": cluster_position,
            "cluster_shape": cluster_shape,
            "lane_skeleton": lane_kind,
            "water_source_position": water_source,
            "plot_size": plot_size,
            "plot_regularity": plot_regularity,
            "grain_drift": grain_drift,
            "households": placed,
            # geometry the caller needs to site its OWN civic features (a sacred precinct, a burial ground)
            # relative to the rolled village, without re-deriving the cluster:
            "cluster": (round(ccx, 1), round(ccy, 1), round(lat, 1), round(dep, 1)),
            "gateway": (round(sk["gateway"][0], 1), round(sk["gateway"][1], 1)),
            "field_bbox": tuple(round(v, 1) for v in fb),
        }

    def line_seeds(self, p0: Pt, p1: Pt, n: int, half_band: float, rng: random.Random, form: str = "linear", record: bool = True) -> list[Pt]:
        """House seeds strung ALONG a line (feature 005 `settlement_form` = 'linear'): a RIBBON of homesteads
        fronting a road / field-margin / dike instead of a nucleated blob - historically the cheapest big
        structural difference between two same-region villages (research.md D5; a levee, a valley-edge track,
        or a canal bank strings the houses out). Distributes `n` seeds along the segment `p0`->`p1` (uniform
        along its length) with a perpendicular jitter up to +/-`half_band`; the bundle solver then hugs each
        homestead to the field edge as usual. Records `meta.settlement_form` when `record=True`."""
        if record:
            self.M["meta"]["settlement_form"] = form
        (x0, y0), (x1, y1) = p0, p1
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy) or 1.0
        px, py = -dy / length, dx / length  # unit perpendicular to the line
        out: list[Pt] = []
        for _ in range(n):
            t = rng.random()
            b = rng.uniform(-1.0, 1.0) * half_band
            out.append((x0 + dx * t + px * b, y0 + dy * t + py * b))
        return out

    def scatter_seeds(self, cx: float, cy: float, rx: float, ry: float, n: int, rng: random.Random, form: str = "dispersed", record: bool = True) -> list[Pt]:
        """House seeds scattered LOOSELY and evenly over a BROAD area (feature 005 `settlement_form`
        = 'dispersed'): scattered farmsteads, each its own yashikirin-groved homestead, rather than a tight
        nucleus - the kainyo / Tonami dispersed-farmstead pattern of the well-watered plains. Area-uniform
        over the ellipse so the farms spread out; `try_place`'s field-adjacency + no-build blockers then
        filter them onto the dry margins, leaving them dotted along the field edges instead of clumped.
        Records `meta.settlement_form`. Pair with `s._nucleated = False` so each farm draws its OWN grove."""
        if record:
            self.M["meta"]["settlement_form"] = form
        out: list[Pt] = []
        for _ in range(n):
            a = rng.uniform(0, 2 * math.pi)
            r = rng.random() ** 0.5  # area-uniform: an even scatter, not center-clumped
            out.append((cx + math.cos(a) * r * rx, cy + math.sin(a) * r * ry))
        return out

    def waterfront_seeds(self, canal: Any, n: int, offset: float, rng: random.Random, form: str = "water_town", record: bool = True) -> list[Pt]:
        """House seeds strung along BOTH banks of a canal (feature 005 `settlement_form` = 'water_town'): a
        Jiangnan-style water town where the houses FRONT the water, offset `offset` px to either side of the
        canal polyline. Records `meta.settlement_form`. (Per GM canon canals are a Lion-lands feature, so this
        form is typing-gated to Lion lands / a declared canal.) `try_place` then keeps each seed field-adjacent
        and off blockers, so the row packs cleanly along the waterfront."""
        if record:
            self.M["meta"]["settlement_form"] = form
        segs = [(canal[i], canal[i + 1]) for i in range(len(canal) - 1)]
        total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs) or 1.0
        out: list[Pt] = []
        for k in range(n):
            d = total * (k + 0.5) / n
            acc = 0.0
            for a, b in segs:
                ln = math.hypot(b[0] - a[0], b[1] - a[1])
                if acc + ln >= d:
                    t = (d - acc) / (ln or 1.0)
                    px, py = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                    nx, ny = -(b[1] - a[1]) / (ln or 1.0), (b[0] - a[0]) / (ln or 1.0)  # canal normal
                    side = 1.0 if k % 2 == 0 else -1.0  # alternate banks
                    out.append((px + nx * offset * side + rng.uniform(-10, 10), py + ny * offset * side + rng.uniform(-10, 10)))
                    break
                acc += ln
        return out

    def headman(self, x: float, y: float, w: float = 92, h: float = 56) -> Any:
        # `w`, `h` are in FEET (drawn at the map's ftpx, px(92) = 46px at 2 ft/px). A nanushi/shoya house is
        # the grandest in the village but still a house - ~92x56 ft, clearly larger than a plain 46x28 ft
        # farmhouse without the old fortress-sized 216x136 ft. headman_is_largest holds.
        if self._toscale():
            # the headman is just a LARGER PLAIN farmhouse - placed through the standard collision-checked
            # bundle path with a tunable SIZE, so it gets its yard + garden and cannot overlap a neighbor.
            # BOTH homestead styles route here (GM 2026-07-21, caught on Hikari no Sato): this guard used to
            # test _nucleated, so a DISPERSED to-scale village's headman fell through to the legacy rec below,
            # which _farmsteads_bundle draws as a LONE house (the abandoned-ruin path) - the grandest
            # farmstead in the village with no threshing yard and no garden. In the dispersed style the
            # bundle also brings the per-house grove when room allows; the solver drops it gracefully in a
            # dense cluster (neighbor tree cover shelters the house), which is the wanted behavior.
            # NO special reservation or "big"-glyph storeroom wing (that wing was drawn outside
            # the reserved footprint and overlapped the north neighbor's yard).
            return self.try_place(x, y, "plain", role="headman", size=(w, h))
        # non-to-scale tiers have no headman (a hamlet falls under the district headman, towns are run by
        # the magistrate - the *_has_no_headman checks), so the old legacy rec branch here was dead code
        # once the Hikari fix routed every to-scale style through the bundle; removed 2026-07-21.
        raise ValueError("headman() is a to-scale village feature - this map is not toscale")

    def _field_adjacent(self, x: float, y: float) -> bool:
        """A farmhouse must stay near the farmland (within the gate's ADJ=165), so a nudge cannot drift it
        off into the urban core or the void."""
        return any(edge_dist(x, y, poly) <= 165 for poly in self.field_polys) if self.field_polys else True

    @staticmethod
    def _bbox_of(rects: Any) -> tuple[float, float, float, float]:
        """The axis-aligned (cx, cy, w, h) bounding box enclosing a list of (cx, cy, w, h) rects."""
        xs = [r[0] - r[2] / 2 for r in rects] + [r[0] + r[2] / 2 for r in rects]
        ys = [r[1] - r[3] / 2 for r in rects] + [r[1] + r[3] / 2 for r in rects]
        return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, max(xs) - min(xs), max(ys) - min(ys))

    def _garden_beds(self, hx: float, hy: float, hw: float, hh: float, gx: float, gy: float, gw: float, gh: float, side: str, gap: float) -> list[Any]:
        """The dooryard garden BED(S) of one nucleated homestead. Usually ONE bed (the reserved plot at
        (gx, gy)). But ~1 in 4 households FRAGMENT the plot into two beds - soil and paths made a single
        clean plot impractical, so you work the good topsoil where it lies. Of the splits (all position-
        seeded, no RNG ripple): ~half FLANK the house on OPPOSITE walls (the E and W walls, or the two south
        corners) because the workable ground just fell on both sides; the rest share ONE side, either
        SIDE-BY-SIDE or - for a SOUTH garden, where the upper bed stays out of the house's shade - STACKED
        above/below. Every bed sits on a SUNNY band (never the cold north back), and because the beds are
        returned to `_bundle_geom` they are RESERVED and collision-checked as part of the whole bundle - so an
        opposite-side bed can never overlap a neighbor or a paddy. Splits only fire when each bed stays wide
        enough (~12 ft) to read as a real garden, so it is the larger (well-off / headman) plots that
        fragment. Total bed area stays in the saien band (`garden_area_within_norms`). Returns (cx,cy,w,h) rects."""
        bs = self.bscale
        if self._hjit(hx, hy, 8.0) >= 0.26:  # the common case: one undivided plot
            return [(gx, gy, gw, gh)]
        south = side in ("SE", "SW")
        # OPPOSITE-SIDE (flanking) split: a bed on each of the E and W walls (or the two south corners for a
        # south garden), each ~half width, the house standing between them
        if self._hjit(hx, hy, 9.0) < 0.5 and gw * 0.55 >= 6 * bs:
            pw = gw * 0.55
            return [(hx + hw / 2 + gap + pw / 2, gy, pw, gh), (hx - hw / 2 - gap - pw / 2, gy, pw, gh)]
        # SAME-SIDE STACKED (above/below): only for a south garden, so the upper bed does not fall into shade
        if south and self._hjit(hx, hy, 10.0) < 0.5 and (gh - gap) / 2 >= 6 * bs:
            ph = (gh - gap) / 2
            return [(gx, gy - (gap + ph) / 2, gw, ph), (gx, gy + (gap + ph) / 2, gw, ph)]
        # SAME-SIDE SIDE-BY-SIDE (the default fragmentation), both beds on the primary wall
        if (gw - gap) / 2 >= 6 * bs:
            pw = (gw - gap) / 2
            return [(gx - (gap + pw) / 2, gy, pw, gh), (gx + (gap + pw) / 2, gy, pw, gh)]
        return [(gx, gy, gw, gh)]  # reserved plot too small to split cleanly

    def _bundle_geom(self, hx: float, hy: float, hw: float, hh: float, garden_side: str = "E", shed: bool = False) -> dict[str, Any]:
        """The metric layout of one homestead BUNDLE around a house centered at (hx, hy). TWO forms:
        NUCLEATED (self._nucleated) = house + lee GARDEN (E) + south YARD only, compact so a cluster can
        pack tight (no per-house grove - a nucleus shelters itself); DISPERSED (default) also carries the
        windward GROVE as an L (an N band + a W band for the default NW wind), sized ~6x the house. The
        dooryard GARDEN tucks tight to the house's E (lee) wall, the threshing YARD sits on the sunny S
        front. Returns a dict of (cx, cy, w, h) rects keyed house/garden/yard (+ grove_n/grove_w when
        dispersed) plus the whole-bundle bbox. (NW windward; other winds are a later generalisation.)"""
        gap = self.px(3)  # 3 ft between a house and its yard/garden, at this map's ftpx
        gw, gh = 0.48 * hw, 0.85 * hh  # garden - tight to the house, scales with wealth
        yw, yh = 0.80 * hw, 0.92 * hh  # threshing/drying yard, ~house-sized
        if not getattr(self, "_nucleated", False):
            # CAP the DISPERSED appurtenances too, same doctrine as the nucleated branch below: a BIG house
            # (the 46x28 px headman) keeps an ORDINARY farm's garden/yard, not ones scaled to the grand
            # house. Found 2026-07-21 (Hikari, GM): the moment the dispersed headman started getting a real
            # bundle, its uncapped 0.48/0.85-scaled garden (~160+ m^2) breached garden_area_within_norms'
            # 140 m^2 ceiling. Garden caps sit BELOW the nucleated ones (42x30 ft vs 48x34) because this
            # path has no up-jitter to absorb - 21x15 px ~ 117 m^2 stays comfortably a garden. Plain
            # dispersed houses (garden ~11x12 px, yard ~25x14) sit far under every cap, so only the headman
            # is affected. Scoped OFF the nucleated path (which recomputes from these as inputs and applies
            # its own caps) so nucleated maps stay byte-identical - capping its inputs re-rolled
            # Hoshigaoka's packing and pushed its fixed-coordinate graveyard off-frame.
            gw, gh = min(gw, self.px(42)), min(gh, self.px(30))
            yw, yh = min(yw, self.px(68)), min(yh, self.px(44))
        east = hx + hw / 2 + gap + gw
        south = hy + hh / 2 + gap + yh
        base: dict[str, Any] = {
            "house": (hx, hy, hw, hh),
            "garden": (hx + hw / 2 + gap + gw / 2, hy, gw, gh),
            "yard": (hx, hy + hh / 2 + gap + yh / 2, yw, yh),
        }
        if getattr(self, "_nucleated", False):
            # NUCLEATED cluster (China-leaning default, per Knapp - and the Japanese shuson): the
            # houses stand close and SHELTER EACH OTHER, so there is NO per-house windbreak grove
            # (a full yashikirin is the DISPERSED-farmstead feature; a tight cluster of grove-bundles
            # cannot nucleate at all). The windbreak becomes a VILLAGE-EDGE belt placed in the second
            # pass. The bundle is house + south yard + a garden on an ADAPTIVE sunny side (chosen by
            # the placer for fit + no shading), so it packs into a real nucleus and the gardens vary
            # instead of all sitting east between houses. See settlements.md 'Settlement form'.
            # CAP the appurtenance dims so a big house (the headman) keeps an ORDINARY farm's yard/garden
            # (spanning ~its adjacent wall but not scaled up to the grand house - "not as tall / not as
            # wide"). A plain 23x14 house is well under these caps, so ordinary farms are unaffected.
            # SIZE variation (position-seeded, no RNG ripple): the garden's base is its MINIMUM (you need at
            # least this plot to feed a household) so it jitters UP - by a different amount in each dimension,
            # which also varies its proportions; the threshing yard's base is its MAXIMUM (a work apron sized
            # to the harvest) so it jitters DOWN. No two homesteads are identical. Both are CAPPED afterward so
            # the big headman still keeps an ordinary farm's yard/garden (the garden jitter can't breach it).
            yw = min(yw * (0.75 + self._hjit(hx, hy, 5.0) * 0.25), self.px(68))  # yard  [0.75,1.00]x, capped at 68 ft
            yh = min(yh * (0.75 + self._hjit(hx, hy, 6.0) * 0.25), self.px(44))
            gw = min(gw * (1.0 + self._hjit(hx, hy, 3.0) * 0.25), self.px(48))  # garden [1.00,1.25]x, capped at 48 ft
            gh = min(gh * (1.0 + self._hjit(hx, hy, 4.0) * 0.25), self.px(34))
            base["yard"] = (hx, hy + hh / 2 + gap + yh / 2, yw, yh)
            if garden_side == "SE":  # tucked beside the south yard (sunny, tight)
                gx, gy = hx + hw / 2 + gap + gw / 2, hy + hh / 2 + gap + gh / 2
            elif garden_side == "SW":
                gx, gy = hx - hw / 2 - gap - gw / 2, hy + hh / 2 + gap + gh / 2
            elif garden_side == "W":  # windward wall, house mid-height
                gx, gy = hx - hw / 2 - gap - gw / 2, hy
            else:  # "E" - lee wall, house mid-height
                gx, gy = hx + hw / 2 + gap + gw / 2, hy
            beds = self._garden_beds(hx, hy, hw, hh, gx, gy, gw, gh, garden_side, gap)
            base["gardens"] = beds  # 1 bed normally; 2 (flanking / stacked / side-by-side) when fragmented
            base["garden"] = beds[0]  # primary bed (kept for the shading score + back-compat)
            rects = [base["house"], base["yard"], *beds]
            if shed:  # a north-wall kura, reserved so a neighbor never lands on it
                base["shed"] = (hx, hy - 0.60 * hh, 0.46 * hw, 0.30 * hh)
                rects.append(base["shed"])
            base["bbox"] = self._bbox_of(rects)
            return base
        # DISPERSED farmstead (the shipped ring-village behavior): the windward GROVE as an L (an N
        # band + a W band, for the default NW wind), sized so the grove footprint is ~6x the house. The
        # multi-bed garden split is a NUCLEATED feature (clean E/W walls, no grove or shed in the way); a
        # dispersed farm keeps its single east garden (its west wall carries the windbreak grove).
        base["gardens"] = [base["garden"]]
        b = 1.57 * hh  # grove band depth -> grove ~= 6x house area
        west = hx - hw / 2 - gap - b
        north = hy - hh / 2 - gap - b
        base["grove_n"] = ((west + east) / 2, north + b / 2, east - west, b)
        base["grove_w"] = (west + b / 2, (north + b + south) / 2, b, south - (north + b))
        base["bbox"] = ((west + east) / 2, (north + south) / 2, east - west, south - north)
        return base

    def _rect_corners(self, rect: Any) -> list[Pt]:
        cx, cy, w, h = rect
        return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]

    def _poly_bboxes(self, polys: Any) -> list[Any]:
        """Cached (minx, miny, maxx, maxy) per polygon in `polys`. Rebuilt only when the list GROWS - the
        block-poly list accretes each placed homestead during the solve, but individual polys are never
        mutated - so a length change is a sufficient staleness signal. Lets _rect_hits reject a far polygon
        with 4 comparisons instead of the O(vertices) corner/segment tests. See `_bbox_cache`."""
        cached = self._bbox_cache.get(id(polys))
        if cached is None or cached[0] != len(polys):
            boxes: list[Any] = []
            for poly in polys:
                xs = [p[0] for p in poly]
                ys = [p[1] for p in poly]
                boxes.append((min(xs), min(ys), max(xs), max(ys)))
            cached = (len(polys), boxes)
            self._bbox_cache[id(polys)] = cached
        return cast(list[Any], cached[1])

    def _rect_hits(self, rect: Any, polys: Any) -> bool:
        """Whether an axis-aligned rect overlaps any polygon in `polys` (corner-in, vertex-in, or edge-cross).
        Bbox pre-filters carry the cost: a polygon whose bbox is disjoint from the rect is skipped outright,
        and within an overlapping polygon each EDGE is bbox-tested before the crossing check (this matters for
        the one huge field-envelope polygon, where the rect only ever meets a couple of its many edges). (A
        spatial grid was tried on top of this and measured NOISE-identical: the bbox reject already makes the
        far-poly scan cheap, and the residual cost is the genuine near-overlap math on polys a grid returns
        anyway - so it was not worth the caching complexity.)"""
        cx, cy, w, h = rect
        rx0, ry0, rx1, ry1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        gc = self._rect_corners(rect)
        for poly, (px0, py0, px1, py1) in zip(polys, self._poly_bboxes(polys), strict=False):
            if px1 < rx0 or px0 > rx1 or py1 < ry0 or py0 > ry1:
                continue  # bboxes disjoint -> cannot overlap
            n = len(poly)
            if any(point_in_poly(px, py, poly) for px, py in gc) or any(rx0 <= vx <= rx1 and ry0 <= vy <= ry1 and point_in_poly(vx, vy, gc) for vx, vy in poly):
                return True
            for k in range(n):  # edge-cross, each edge bbox-gated against the rect
                a, b = poly[k], poly[(k + 1) % n]
                if min(a[0], b[0]) > rx1 or max(a[0], b[0]) < rx0 or min(a[1], b[1]) > ry1 or max(a[1], b[1]) < ry0:
                    continue
                if any(segments_cross(gc[e], gc[(e + 1) % 4], a, b) for e in range(4)):
                    return True
        return False

    def _water_obstacles(self) -> list[Any]:
        """Cached (poly, keep-out half-width, bbox) for every irrigation LINE a solid bundle rect must avoid -
        feeder channels, in-field/drain ditches, streams. Rebuilt only when one of the three source lists
        changes length (all are laid before the homestead solve, then static). Lets _rect_on_water skip a
        whole course - and then an individual segment - whose neighborhood the rect cannot reach."""
        chans = self.M.get("channels", [])
        ditches = self.M.get("field_ditches", [])
        streams = self.M.get("streams", [])
        key = (len(chans), len(ditches), len(streams))
        if self._water_obs_cache is None or self._water_obs_cache[0] != key:
            obs: list[Any] = []
            for lst, base in ((chans, 2.5), (ditches, 7.0), (streams, 9.0)):
                for f in lst:
                    poly = f["poly"]
                    if len(poly) < 2:
                        continue
                    hw = f.get("w", base) / 2 + 5
                    xs = [p[0] for p in poly]
                    ys = [p[1] for p in poly]
                    obs.append((poly, hw, (min(xs), min(ys), max(xs), max(ys))))
            self._water_obs_cache = (key, obs)
        return cast(list[Any], self._water_obs_cache[1])

    def _rect_on_water(self, rect: Any) -> bool:
        """Whether a SOLID bundle rect (house/yard/garden/shed) lands on an irrigation LINE - a feeder
        channel, an in-field/drain ditch, or a stream. These are dry-ground structures, so a garden or
        yard in a running ditch is wrong (gardens_clear_of_channels), and this keeps the homestead solver
        off the drain outfall that threads the village margin. A hair wider than the check's keep-out so
        the solver leaves room the check then confirms. The GROVE is exempt (it may hug a bund). Bbox
        pre-filters (per course, then per segment) skip the seg_dist / crossing math for anything far off."""
        cx, cy, w, h = rect
        gc = self._rect_corners(rect)
        pts = gc + [(cx, cy)]
        rx0, ry0, rx1, ry1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        for poly, hw, (px0, py0, px1, py1) in self._water_obstacles():
            if px1 + hw < rx0 or px0 - hw > rx1 or py1 + hw < ry0 or py0 - hw > ry1:
                continue  # the whole course is out of reach
            for k in range(len(poly) - 1):
                a, b = poly[k], poly[k + 1]
                if min(a[0], b[0]) - hw > rx1 or max(a[0], b[0]) + hw < rx0 or min(a[1], b[1]) - hw > ry1 or max(a[1], b[1]) + hw < ry0:
                    continue  # this segment is out of reach
                if any(seg_dist(px, py, a, b) < hw for px, py in pts):
                    return True
                if any(segments_cross(a, b, gc[e], gc[(e + 1) % 4]) for e in range(4)):
                    return True
        return False

    def _rect_blocked(self, rect: Any, fields: bool) -> bool:
        """Whether a bundle sub-rect lands on forbidden ground: no-build blocks, lanes, hill/pond ellipses,
        irrigation lines, and (only when `fields=True`, i.e. the SOLID house/yard/garden) the flooded
        paddies. The GROVE (fields=False) may HUG a paddy bund, so it is tested against everything BUT the
        fields and the water lines."""
        if self._rect_hits(rect, self.block_polys):
            return True
        if fields and self._rect_hits(rect, self.field_polys):
            return True
        if fields and self._rect_on_water(rect):
            return True
        cx, cy, w, h = rect
        for px, py in self._rect_corners(rect) + [(cx, cy)]:
            for ex, ey, rx, ry in self.ellipses:
                if rx > 0 and ry > 0 and ((px - ex) / rx) ** 2 + ((py - ey) / ry) ** 2 <= 1:
                    return True
        return self._near_corridor(cx, cy)

    def _bundle_fits(self, geom: Any, grove_off_field: bool = True) -> bool:
        """A homestead bundle fits where it is in-bounds, its SOLID parts (house/yard/garden) clear every
        paddy/block/lane/ellipse, its GROVE clears all of those (and may abut - but not enter - a paddy when
        `grove_off_field`, the test used while shoving the grove up against the bund), and the whole bbox
        does not overlap another already-placed homestead (a sliver of tolerance lets adjacent groves ABUT
        into one windbreak). Split into a side-INDEPENDENT half (house/yard/kura/grove/sun - identical for
        every garden side at a position) and a side-DEPENDENT half (the garden bed + the bbox it grows), so
        the nucleated placer can test the common half ONCE across all four sides (see `_fits_any_side`). The
        conjunction is order-independent, so the result is unchanged from the old single test."""
        return self._bundle_common_fits(geom, grove_off_field) and self._bundle_side_fits(geom)

    def _bundle_common_fits(self, geom: Any, grove_off_field: bool = True) -> bool:
        """The fit checks that do NOT depend on which side the garden is on - the house, the south threshing
        yard, a north kura, the windward grove (dispersed only), and the yard sun-corridor. Same for every
        garden side at a given position, so it is tested once per position."""
        if self._rect_blocked(geom["house"], fields=True) or self._rect_blocked(geom["yard"], fields=True) or ("shed" in geom and self._rect_blocked(geom["shed"], fields=True)):
            return False
        if "grove_n" in geom and any(self._rect_blocked(geom[k], fields=grove_off_field) for k in ("grove_n", "grove_w")):
            return False
        return not self._yard_sun_conflict(geom)

    def _bundle_side_fits(self, geom: Any) -> bool:
        """The fit checks that DO move with the garden side (via the bundle bbox): in-bounds, inside any
        bounding ring, the garden bed(s) clear of every paddy/block/lane, and the whole bbox clear of every
        placed homestead."""
        cx, cy, W, H = geom["bbox"]
        if cx - W / 2 < 6 or cx + W / 2 > self.W - 6 or cy - H / 2 < 6 or cy + H / 2 > self.H - 6:
            return False
        if self.bound and any(not point_in_poly(vx, vy, self.bound) for vx, vy in self._rect_corners(geom["bbox"])):
            return False
        if any(self._rect_blocked(g, fields=True) for g in geom["gardens"]):
            return False
        return all(not (abs(cx - px) < (W + pw) / 2 + 2 and abs(cy - py) < (H + ph) / 2 + 2) for px, py, pw, ph in self.placed)

    def _yard_sun_conflict(self, geom: Any) -> bool:
        """A threshing yard dries rice in the southern sun, so no grove may sit in the ~22px strip directly
        SOUTH of any yard. Tests the candidate's grove against every placed yard's sun-corridor and the
        candidate's yard against every placed grove, so packing never stacks a windbreak over a neighbor's
        drying ground."""

        def shades(grove: Any, yard: Any) -> bool:
            cyx, cyy = yard[0], yard[1] + yard[3] / 2 + 11
            return cast(bool, abs(grove[0] - cyx) < (grove[2] + yard[2]) / 2 and abs(grove[1] - cyy) < (grove[3] + 22) / 2)

        new_groves = (geom["grove_n"], geom["grove_w"]) if "grove_n" in geom else ()
        new_yard = geom["yard"]
        for rec in self.M["houses"]:
            g = rec.get("geom")
            if not g:
                continue
            if any(shades(gv, g["yard"]) for gv in new_groves):
                return True
            other_groves = (g["grove_n"], g["grove_w"]) if "grove_n" in g else ()
            if any(shades(gv, new_yard) for gv in other_groves):
                return True
        return False

    @staticmethod
    def _closest_on_seg(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> Pt:
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        if L2 == 0:
            return ax, ay
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
        return ax + t * dx, ay + t * dy

    def _nearest_field_point(self, cx: float, cy: float) -> Pt | None:
        """The closest point on any paddy outline to (cx, cy) - the bund the grove will hug."""
        best: Pt | None = None
        bd = float("inf")
        for poly in self.field_polys:
            n = len(poly)
            for i in range(n):
                qx, qy = self._closest_on_seg(cx, cy, poly[i][0], poly[i][1], poly[(i + 1) % n][0], poly[(i + 1) % n][1])
                d = (qx - cx) ** 2 + (qy - cy) ** 2
                if d < bd:
                    bd, best = d, (qx, qy)
        return best

    def _nearest_placed_point(self, cx: float, cy: float) -> Pt | None:
        """The center of the nearest already-placed homestead/house - the neighbor to pack against."""
        best: Pt | None = None
        bd = float("inf")
        for px, py, _pw, _ph in self.placed:
            d = (px - cx) ** 2 + (py - cy) ** 2
            if d < bd:
                bd, best = d, (px, py)
        return best

    def _slide(self, cx: float, cy: float, hw: float, hh: float, target_fn: Any, grove_off_field: bool) -> Pt:
        """Greedily shove the bundle toward target_fn (a field bund, then a neighbor) in small steps, as
        far as it still fits - the 'pack as close as the rules allow' step."""
        for _ in range(48):
            tgt = target_fn(cx, cy)
            if tgt is None:
                break
            dx, dy = tgt[0] - cx, tgt[1] - cy
            dist = math.hypot(dx, dy)
            if dist < 1.5:
                break
            ncx, ncy = cx + dx / dist * 2.0, cy + dy / dist * 2.0
            if self._bundle_fits(self._bundle_geom(ncx, ncy, hw, hh), grove_off_field=grove_off_field):
                cx, cy = ncx, ncy
            else:
                break
        return cx, cy

    def _place_bundle(self, x: float, y: float, hw: float, hh: float, shed: bool = False) -> Any:
        """Place a homestead bundle one-at-a-time: find the nearest fitting spot to the seed, then COMPACT it
        - shove the grove up against the nearest paddy bund (without entering it), then pack the whole
        complex against its nearest neighbor, each as far as the rules allow. `shed` reserves a north kura in
        the bundle. Returns (cx, cy, geom) or None."""
        if getattr(self, "_nucleated", False):
            return self._place_bundle_nucleated(x, y, hw, hh, shed)
        offsets = [(0, 0)]
        for r in range(7, 92, 7):
            for k in range(12):
                a = k * math.pi / 6
                offsets.append((round(r * math.cos(a)), round(r * math.sin(a))))
        start: Pt | None = None
        for nx, ny in offsets:
            if self._bundle_fits(self._bundle_geom(x + nx, y + ny, hw, hh)):
                start = (x + nx, y + ny)
                break
        if start is None:
            return None
        cx, cy = start
        cx, cy = self._slide(cx, cy, hw, hh, self._nearest_field_point, grove_off_field=True)  # grove hugs the bund
        cx, cy = self._slide(cx, cy, hw, hh, self._nearest_placed_point, grove_off_field=True)  # pack against neighbor
        return cx, cy, self._bundle_geom(cx, cy, hw, hh)

    _NUC_SIDES = ("SE", "SW", "E", "W")  # garden-side preference: sunny south strip first, walls as fallback

    def _garden_shaded(self, grect: Any) -> bool:
        """A dooryard garden is SHADED when a farmhouse stands close to its SOUTH (the sun comes from the
        south), so a garden sandwiched with a neighbor's house just below it gets no light. Tested against
        every placed house - the nucleated placer prefers a side with open sky to the south."""
        gx, gy, gw, gh = grect
        for rec in self.M["houses"]:
            hx, hy, hw, hh = rec["x"], rec["y"], rec["w"], rec["h"]
            if hy > gy + gh / 2 - 3 and abs(hx - gx) < (hw + gw) / 2 and (hy - hh / 2) - (gy + gh / 2) < gh + 4:
                return True
        return False

    def _fits_any_side(self, cx: float, cy: float, hw: float, hh: float, shed: bool = False) -> bool:
        # The house/yard/kura/sun checks are the same for every garden side, so test that common half ONCE -
        # if it fails, no side can fit - then test only each side's garden (+ the bbox it grows). Identical
        # result to any(_bundle_fits(...) for side), but far fewer collision tests on the failing steps that
        # dominate the pack. Safe because the fit path is RNG-free: building fewer geoms cannot shift placement.
        g0 = self._bundle_geom(cx, cy, hw, hh, self._NUC_SIDES[0], shed)
        if not self._bundle_common_fits(g0):
            return False
        for i, side in enumerate(self._NUC_SIDES):
            geom = g0 if i == 0 else self._bundle_geom(cx, cy, hw, hh, side, shed)
            if self._bundle_side_fits(geom):
                return True
        return False

    def _field_dist(self, cx: float, cy: float) -> float:
        """Distance from a point to the nearest paddy edge (inf if there are no fields)."""
        p = self._nearest_field_point(cx, cy)
        return math.hypot(cx - p[0], cy - p[1]) if p else float("inf")

    def _slide_nuc(self, cx: float, cy: float, hw: float, hh: float, target_fn: Any, keep_field: bool = False) -> Pt:
        """Shove a nucleated bundle toward target_fn as far as SOME garden side still fits - the tight-pack
        step (the garden side is re-chosen at the final spot, so the slide only needs one side to work).
        With keep_field, a move is ALSO rejected if it would drift the bundle FURTHER from the paddy than
        where it started: so the neighbor-pack runs ALONG the field edge (tangentially) and never pulls the
        cluster off the paddy - the village glues its field side to the paddy and builds outward in rows."""
        fd_cap: Any = self._field_dist(cx, cy) + 3 if keep_field else None
        for _ in range(80):
            tgt = target_fn(cx, cy)
            if tgt is None:
                break
            dx, dy = tgt[0] - cx, tgt[1] - cy
            dist = math.hypot(dx, dy)
            if dist < 1.5:
                break
            ncx, ncy = cx + dx / dist * 2.0, cy + dy / dist * 2.0
            if keep_field and self._field_dist(ncx, ncy) > fd_cap:
                break
            if self._fits_any_side(ncx, ncy, hw, hh):
                cx, cy = ncx, ncy
            else:
                break
        return cx, cy

    def _place_bundle_nucleated(self, x: float, y: float, hw: float, hh: float, shed: bool = False) -> Any:
        """Nucleated placement: find the nearest spot where SOME garden side fits, pack it hard against the
        field bund then its neighbors, then pick the garden side that is UNSHADED and sunniest. The compact
        (grove-less) bundle lets the cluster nucleate; the adaptive garden gives sun + variety. `shed` reserves
        a north kura in every candidate bundle so a neighbor never lands on it."""
        offsets = [(0, 0)]
        for r in range(5, 80, 5):
            for k in range(12):
                a = k * math.pi / 6
                offsets.append((round(r * math.cos(a)), round(r * math.sin(a))))
        start: Pt | None = None
        for nx, ny in offsets:
            if self._fits_any_side(x + nx, y + ny, hw, hh, shed):
                start = (x + nx, y + ny)
                break
        if start is None:
            return None
        cx, cy = start
        cx, cy = self._slide_nuc(cx, cy, hw, hh, self._nearest_field_point)  # hug the paddy edge
        cx, cy = self._slide_nuc(
            cx,
            cy,
            hw,
            hh,
            self._nearest_placed_point,  # then pack ALONG it (never off it),
            keep_field=True,
        )  # so the cluster glues to the paddy
        best: Any = None
        for rank, side in enumerate(self._NUC_SIDES):
            geom = self._bundle_geom(cx, cy, hw, hh, side, shed)
            if not self._bundle_fits(geom):
                continue
            score = (sum(self._garden_shaded(g) for g in geom["gardens"]), rank)  # fewest shaded beds first, then preference
            if best is None or score < best[0]:
                best = (score, geom)
        if best is None:  # pragma: no cover - the slide only rests where some garden side fits, so best is set
            return None
        return cx, cy, best[1]

    def _solve_homestead(self, rec: Any) -> Any:
        """Find the best position for a farmhouse so its WHOLE homestead fits - threshing yard + dooryard
        garden + room for a windward grove. Searches the placed spot first, then a widening spiral, and stops
        as soon as the home spot already leaves grove-room (no churn). Prefers a spot WITH grove-room, then the
        least displacement; falls back to a yard+garden-only spot if no grove-room is reachable nearby. Updates
        rec's position + reservation. Returns (yard_spot, garden_spot), or None if even yard+garden won't fit."""
        x0, y0, w, h = rec["x"], rec["y"], rec["w"], rec["h"]
        self.placed = [p for p in self.placed if p != (x0, y0, w, h)]  # lift own reservation while searching
        best: Any = None  # (has_grove_room, -displacement, cx, cy, spot)
        for nx, ny in self._farmstead_nudges():
            cx, cy = x0 + nx, y0 + ny
            if not self._fits(cx, cy, w, h) or not self._field_adjacent(cx, cy):
                continue
            spot = self._find_appurtenances(cx, cy, w, h, rec["rot"], rec["kind"], rec["shed"], rec["wealth"])
            if spot is None:
                continue
            wf = rec["wealth"]  # the grove is drawn at the WEALTH size, so reserve room for THAT
            cand = (self._grove_room(cx, cy, w * wf, h * wf), -(abs(nx) + abs(ny)), cx, cy, spot)
            if best is None or cand[:2] > best[:2]:
                best = cand
            if cand[0] and nx == 0 and ny == 0:
                break  # already perfect at the home spot
        cx, cy = (best[2], best[3]) if best else (x0, y0)
        rec["x"], rec["y"] = cx, cy
        self.placed.append((cx, cy, w, h))  # re-reserve at the chosen (or original) spot
        return best[4] if best else None

    def farmsteads(self) -> int:
        """Draw every farmstead. The to-scale tiers (villages/hamlets/towns) draw the reserved homestead
        BUNDLES; cities use the shipped house-first path. Call LAST in the gen so every obstacle is known. Returns the farmhouse count."""
        if self._toscale():
            return self._farmsteads_bundle()
        return self._farmsteads_legacy()

    def _farmsteads_bundle(self) -> int:
        """Draw every reserved homestead bundle: grove (back) -> yard -> garden -> house (on top). The hard
        work (fitting each whole bundle without overlap) already happened in try_place, one at a time, so
        this pass is pure drawing. Abandoned ruins (no bundle) draw as a lone house. Call LAST. Returns the
        farmhouse count.
        Two sub-passes so the garden EAST-shade nudge can see every neighbor's grove: (1) draw all per-house
        GROVES (the back layer), (2) after a south-nudge relaxation, draw the yards/gardens/houses on top."""
        survivors: list[Any] = []
        bundled: list[Any] = []
        for rec in self._pending_farmsteads:
            geom = rec.get("geom")
            if geom is None:  # abandoned ruin / dispersed headman: lone house
                self.house(rec["x"], rec["y"], rec["w"], rec["h"], rec["kind"], rec["rot"])
                survivors.append(rec)
                continue
            for key, face in (("grove_n", (0, -1)), ("grove_w", (-1, 0))):
                if key not in geom:  # nucleated bundle: no per-house grove
                    continue
                cx, cy, w, h = geom[key]
                self._draw_grove(cx, cy, w, h, face)
                self.M["groves"].append({"x": round(cx, 1), "y": round(cy, 1), "w": w, "h": h, "rot": 0, "of": [rec["x"], rec["y"]], "face": list(face)})
                self.grove_rects.append((cx, cy, w, h))
            bundled.append(rec)
            survivors.append(rec)
        self._relax_gardens_south(bundled)  # nudge east-shaded gardens a little S (all groves now known)
        for rec in bundled:
            geom = rec["geom"]
            self._attach_yard(rec["x"], rec["y"], geom["yard"])
            self._attach_garden(rec["x"], rec["y"], geom["gardens"])
            self.house(rec["x"], rec["y"], rec["w"], rec["h"], rec["kind"], rec["rot"], shed=rec["shed"], shed_side=rec.get("shed_side", "W"))
        self.M["houses"] = survivors
        return len(survivors)

    def _east_trees(self, gx1: float, own: Any) -> list[Any]:
        """The y-intervals (y0, y1) of every per-house grove arm standing hard against a garden's EAST - west
        edge within a shade band east of the garden's east edge `gx1`. `own` is the garden's OWN grove arms
        (which sit N/W, never east), excluded. The garden's x is fixed as it shifts S, so this set is stable."""
        band = 22 * self.bscale
        out: list[Any] = []
        for tx, ty, tw, th in self.grove_rects:
            if any(abs(tx - ox) < 1.5 and abs(ty - oy) < 1.5 for ox, oy, _, _ in own):
                continue  # skip the garden's own grove arms
            west = tx - tw / 2
            if gx1 - 2 <= west < gx1 + band:
                out.append((ty - th / 2, ty + th / 2))
        return out

    def _garden_beds_clear(self, beds: Any, others: Any) -> bool:
        """Whether a set of shifted garden beds land on clear ground: each bed off blocks/fields/water/lanes
        (`_rect_blocked`), and clear of every ACTUAL footprint in `others` (neighbors' houses/yards/gardens/
        groves + the garden's own house + yard). Tests real footprints, NOT the loose reserved bundle bboxes -
        a garden may shift into a neighbor's empty bbox margin, it just may not touch a drawn structure."""

        def hit(a: Any, b: Any) -> bool:
            return cast(bool, abs(a[0] - b[0]) < (a[2] + b[2]) / 2 and abs(a[1] - b[1]) < (a[3] + b[3]) / 2)

        for bed in beds:
            if self._rect_blocked(bed, fields=True):
                return False
            if any(hit(bed, r) for r in others):
                return False
        return True

    def _relax_gardens_south(self, recs: Any) -> None:
        """OPTION (villages where each house has its own windward grove and the garden goes on the E/lee side):
        once every yashikirin is drawn, a garden left with a NEIGHBOR'S grove hard against its EAST loses the
        morning sun. Where there is open ground, nudge that garden a little SOUTH so the tree falls to its NE
        and the eastern sky opens - the GM's 'move it a bit south' remedy. Best-effort: a garden boxed in to the
        south stays put (gardens_unshaded_from_east flags only the AVOIDABLE ones). See settlements.md 'gardens'."""
        step = 4 * self.bscale

        def footprints(exclude: int) -> list[Any]:
            """Every homestead's real house/yard/garden/grove rects, minus the rec at index `exclude`."""
            out: list[Any] = []
            for j, r in enumerate(recs):
                if j == exclude:
                    continue
                g = r["geom"]
                out.append(tuple(g["house"]))
                out.append(tuple(g["yard"]))
                out += [tuple(b) for b in g.get("gardens", [])]
                out += [tuple(g[k]) for k in ("grove_n", "grove_w") if k in g]
            return out

        def overlaps(a: Any, b: Any) -> bool:
            return cast(bool, a[0] < b[1] and b[0] < a[1])

        for i, rec in enumerate(recs):
            geom = rec["geom"]
            beds = geom.get("gardens")
            if not beds:
                continue
            own = [geom[k] for k in ("grove_n", "grove_w") if k in geom]
            gx1 = max(b[0] + b[2] / 2 for b in beds)
            gcy = sum(b[1] for b in beds) / len(beds)
            gh = max(b[1] + b[3] / 2 for b in beds) - min(b[1] - b[3] / 2 for b in beds)
            trees = self._east_trees(gx1, own)
            if not any(overlaps((gcy - gh / 2, gcy + gh / 2), t) for t in trees):
                continue  # not currently east-shaded - nothing to do
            maxshift = gh + rec["h"] + 6  # 'a little' - stays a dooryard garden near the house
            others = footprints(i) + [tuple(geom["house"]), tuple(geom["yard"])]
            dy = step
            while dy <= maxshift:
                lane = (gcy + dy - gh / 2, gcy + dy + gh / 2)  # clear of EVERY east tree (a small shift can slip INTO a taller arm)
                if not any(overlaps(lane, t) for t in trees):
                    shifted = [(b[0], b[1] + dy, b[2], b[3]) for b in beds]
                    if self._garden_beds_clear(shifted, others):
                        geom["gardens"] = shifted
                        break
                dy += step

    def _farmsteads_legacy(self) -> int:
        """Draw every deferred farmhouse WITH its threshing/drying YARD (south/front apron) AND its dooryard
        kitchen GARDEN (a sunny side, preferring the east) - both were universal to a farmstead, so every
        farmhouse has one of each. Find spots for both; if they don't fit, nudge the house a little; draw
        garden + yard then the house so the house wins any abutment. A house that cannot host BOTH anywhere
        nearby is dropped (rare) so the 100% invariants hold. Call LAST in the gen. Returns the count."""
        survivors: list[Any] = []
        for rec in self._pending_farmsteads:
            spot = self._solve_homestead(rec)  # shift the homestead to fit yard+garden+grove-room
            if spot is None:
                fp = (rec["x"], rec["y"], rec["w"], rec["h"])
                self.placed = [p for p in self.placed if p != fp]  # drop the un-appurtenanced farmhouse (rare)
                continue
            yard_spot, garden_spot = spot
            self._attach_garden(rec["x"], rec["y"], [garden_spot])  # legacy farms keep ONE bed (multi-bed split is nucleated)
            self._attach_yard(rec["x"], rec["y"], yard_spot)
            # DRAW the house at its WEALTH size - a modest +/-~10% on the rendered glyph only. The manifest keeps
            # w,h at the BASE footprint (what the reservation, the yard/garden, and the overlap checks use, so
            # the variation never causes a drop or a shed/garden clash); the `wealth` factor records the render
            # scale and the grove (below) scales with it.
            wf = rec["wealth"]
            self.house(rec["x"], rec["y"], rec["w"] * wf, rec["h"] * wf, rec["kind"], rec["rot"], shed=rec["shed"])
            survivors.append(rec)
        self.M["houses"] = survivors
        # SECOND PASS - the windward homestead groves (yashikirin). Run AFTER every farmhouse + its yard +
        # garden is placed, so a grove (an optional flourish) can NEVER block a neighbor's MANDATORY yard/
        # garden and drop that house. Near-universal (meta.grove_prevalence), but OFF for a farm inside a
        # CITY wall (an intramural plot is not an isolated farmstead - it is sheltered by the urban fabric
        # and sits on land too precious for a tree belt; meta(inwall_groves=True) to override). A farm whose
        # windward side is boxed in goes without. Returns the farmhouse count.
        meta = self.M["meta"]
        wall: Any = self.M.get("wall")
        inwall_off = bool(wall) and meta.get("scale") == "city" and not meta.get("inwall_groves", False)
        for rec in survivors:
            if inwall_off and point_in_poly(rec["x"], rec["y"], wall):
                continue
            if self._grove_candidate(rec["x"], rec["y"]):
                wf = rec["wealth"]  # a wealthier farm's bigger house carries a bigger grove
                arms = self._find_grove_arms(rec["x"], rec["y"], rec["w"] * wf, rec["h"] * wf)
                if arms:
                    self._attach_grove(rec["x"], rec["y"], arms)
        return len(survivors)

    def _perim_bbox(self, bbox: Any, n: int, gap: float) -> list[Pt]:
        x0, y0, x1, y1 = bbox
        bw, bh = x1 - x0, y1 - y0
        per = 2 * (bw + bh)
        pts: list[Pt] = []
        for k in range(n):
            d = (k + random.uniform(0.18, 0.82)) / n * per
            if d < bw:
                x, y, nx, ny = x0 + d, y0, 0, -1
            elif d < bw + bh:
                x, y, nx, ny = x1, y0 + (d - bw), 1, 0
            elif d < 2 * bw + bh:
                x, y, nx, ny = x1 - (d - bw - bh), y1, 0, 1
            else:
                x, y, nx, ny = x0, y1 - (d - 2 * bw - bh), -1, 0
            g = gap + random.uniform(4, gap * 0.85)
            pts.append((x + nx * g + random.uniform(-10, 10), y + ny * g + random.uniform(-10, 10)))
        return pts

    def _perim_poly(self, poly: Any, n: int, gap: float) -> list[Pt]:
        area = _signed_area(poly)
        seglen = [math.hypot(poly[(i + 1) % len(poly)][0] - poly[i][0], poly[(i + 1) % len(poly)][1] - poly[i][1]) for i in range(len(poly))]
        per = sum(seglen)
        pts: list[Pt] = []
        for k in range(n):
            d = (k + random.uniform(0.2, 0.8)) / n * per
            acc: float = 0
            for i, sl in enumerate(seglen):
                if acc + sl >= d:
                    f = (d - acc) / sl if sl else 0
                    x1, y1 = poly[i]
                    x2, y2 = poly[(i + 1) % len(poly)]
                    px, py = x1 + (x2 - x1) * f, y1 + (y2 - y1) * f
                    dx, dy = x2 - x1, y2 - y1
                    L = math.hypot(dx, dy) or 1
                    nx, ny = (dy / L, -dx / L) if area > 0 else (-dy / L, dx / L)
                    gg = gap + random.uniform(4, gap * 0.85)
                    pts.append((px + nx * gg + random.uniform(-10, 10), py + ny * gg + random.uniform(-10, 10)))
                    break
                acc += sl
        return pts

    def ring(self, shape: Any, n: int, gap: float, kinds: Any, max_big: int = 4) -> None:
        """Ring a field with houses. shape: bbox tuple, or ('poly', smoothed_outline)."""
        cand = self._perim_poly(shape[1], n, gap) if isinstance(shape, tuple) and shape and shape[0] == 'poly' else self._perim_bbox(shape, n, gap)
        for x, y in cand:
            k = random.choice(kinds)
            if k == "big":
                if self._nbig >= max_big:
                    k = "plain"
                else:
                    self._nbig += 1
            if not self.try_place(x, y, k) and k == "big":
                self._nbig -= 1

    # ---- annotation
    def _record_label(self, x: float, y: float, text: str, size: float, anchor: str, z: int) -> None:
        w = len(text) * size * 0.55  # rough serif advance; slightly generous so near-misses flag
        x0 = x - w / 2 if anchor == "middle" else (x - w if anchor == "end" else x)
        # record the TEXT (element [5]) too, so the gate can verify a zone/neighborhood label actually
        # sits with the cluster it names (same side of the wall, among its buildings)
        self.M["labels"].append([round(x0, 1), round(y - size * 0.8, 1), round(x0 + w, 1), round(y + size * 0.25, 1), z, text])

    def label(self, x: float, y: float, text: str, size: float = 12, anchor: str = "middle", italic: bool = False, weight: str = "normal", color: str = "#2D2A24") -> None:
        esc = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        st = ' font-style="italic"' if italic else ''
        # labels live in the topmost LABEL layer so nothing - not a road, not a wall, not a kido or torii
        # - ever paints over the text (a label must always be fully readable)
        z = self.add_label(
            f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" font-size="{size}" font-weight="{weight}"{st} fill="{color}" paint-order="stroke" stroke="{LAND}" stroke-width="3">{esc}</text>'
        )
        self._record_label(x, y, text, size, anchor, z)

    def title(self, name: str, fs: float = 30) -> None:
        """Place the map title (the bold place name plus a scale bar under it) over BLANK space: scan the
        rendered window for a spot where the box clears every feature (buildings, fields, water, groves,
        the pond), scanning top-first so the title lands high when it can. Records the placed box in M['title']
        so `title_clear_of_features` can verify it. Call AFTER crop_to_content, so the search runs over the
        framed window. Falls back to the top-left of the view (or the canvas center) only if the map is too full
        to find any gap.

        SCALE BAR (GM 2026-07-20: every settlement map shows its scale, matching the Mode A compound
        sheets): the bar spans 100 map-px, which is a round real distance at every rung of the GM's
        scale ladder - 100 ft at hamlet/town (1 ft/px), 200 ft at village (2 ft/px), 300 ft at
        provincial city (3 ft/px) - drawn in the Mode A furniture style (end ticks + mid tick, the
        distance under the bar, a fine-print '(1 px = N ft)' line). The searched AND recorded box
        covers the title + bar together, so `title_clear_of_features` gates the bar's placement too.

        PLACARD (GM 2026-07-21): the title + scale bar sit on a stylized parchment CARD - a cream
        cartouche (lighter than the #EFE3C2 ground, double-line brown border) drawn under the text -
        so the block stays legible no matter what ground cover it lands over (the satoyama ring put
        scrub speckle nearly everywhere a title can sit, and ink-on-scrub was hard to read). The
        searched and recorded box is the PLACARD's extent, so the clearance check gates the whole
        card; `title_has_placard` gates its presence (a manifest without one predates the card)."""
        tw, th = len(name) * fs * 0.58 + 10, fs * 1.2  # estimated text box (bold serif runs ~0.58 em/char; +10 so a long name never kisses the card border)
        bar_px, bar_ft = 100.0, round(100 * self.ftpx)
        PAD = 12  # placard padding around the text block
        bw, bh = max(tw, bar_px) + 2 * PAD, th + 46 + 2 * PAD  # the searched box: the whole placard
        vx0, vy0, vw, vh = self.view if self.view else (0, 0, self.W, self.H)
        spot = self._blank_label_spot(vx0, vy0, vw, vh, bw, bh)
        if spot:
            px0, py0 = spot
        elif self.view:  # map too full - fall back to the top-left corner
            px0, py0 = vx0 + 30, vy0 + 16
        else:
            px0, py0 = self.W / 2 - bw / 2, 22
        x, y = px0 + PAD, py0 + PAD  # the text block's origin, inside the card
        self.M["title"] = {
            "name": name,
            "bbox": [round(px0, 1), round(py0, 1), round(px0 + bw, 1), round(py0 + bh, 1)],
            "placard": [round(px0, 1), round(py0, 1), round(px0 + bw, 1), round(py0 + bh, 1)],
        }
        self.add_label(  # the card FIRST, so every text draws over it (add_label draws in call order)
            f'<g><rect x="{px0:.0f}" y="{py0:.0f}" width="{bw:.0f}" height="{bh:.0f}" rx="7" fill="#F7F0DC" fill-opacity="0.94" stroke="#8C7A55" stroke-width="1.6"/>'
            f'<rect x="{px0 + 3.5:.0f}" y="{py0 + 3.5:.0f}" width="{bw - 7:.0f}" height="{bh - 7:.0f}" rx="5" fill="none" stroke="#BCAA7E" stroke-width="0.8"/></g>'
        )
        self.add_label(f'<text x="{x:.0f}" y="{y + fs:.0f}" font-size="{fs}" font-weight="bold" fill="#2D2A24">{name}</text>')
        bx0, bx1, by = x, x + bar_px, y + th + 12  # bar left-aligned under the title
        self.M["scalebar"] = {"ft": bar_ft, "ftpx": self.ftpx, "bbox": [round(bx0, 1), round(by - 5, 1), round(bx1, 1), round(y + bh, 1)]}
        self.add_label(
            f'<g stroke="#3A2E1C" stroke-width="2">'
            f'<line x1="{bx0:.0f}" y1="{by:.0f}" x2="{bx1:.0f}" y2="{by:.0f}"/>'
            f'<line x1="{bx0:.0f}" y1="{by - 5:.0f}" x2="{bx0:.0f}" y2="{by + 5:.0f}"/>'
            f'<line x1="{bx1:.0f}" y1="{by - 5:.0f}" x2="{bx1:.0f}" y2="{by + 5:.0f}"/>'
            f'<line x1="{(bx0 + bx1) / 2:.0f}" y1="{by - 3:.0f}" x2="{(bx0 + bx1) / 2:.0f}" y2="{by + 3:.0f}" stroke-width="1"/>'
            f'</g>'
        )
        self.add_label(f'<text x="{(bx0 + bx1) / 2:.0f}" y="{by + 17:.0f}" text-anchor="middle" font-size="12" fill="#3A2E1C">{bar_ft} ft</text>')
        self.add_label(f'<text x="{(bx0 + bx1) / 2:.0f}" y="{by + 31:.0f}" text-anchor="middle" font-size="10" font-style="italic" fill="#5C4830">(1 px = {self.ftpx:g} ft)</text>')

    def _title_obstacles(self) -> tuple[list[Any], list[Any], list[Any]]:
        """Feature footprints a title must clear, as (rects, polys, lines). Solid buildings/plots -> rects;
        the fields, groves, and commons -> polygons (so the title can sit in the empty corners around a diagonal
        field); the pond -> a rect; water lines + lanes -> polylines (a title must not cross a road or stream)."""
        rects: list[Any] = []
        polys: list[Any] = []
        lines: list[Any] = []
        for k in (
            "houses",
            "gardens",
            "threshing_yards",
            "groves",
            "dry_plots",
            "buildings",
            "manors",
            "religious",
            "shrines",
            "flophouses",
            "storehouses",
            "merchant_estates",
            "cemeteries",
            "mausoleums",
            "cremation_grounds",
            "ossuaries",
            "ministries",
        ):
            for o in self.M.get(k, []):
                if o.get("poly"):
                    xs = [p[0] for p in o["poly"]]
                    ys = [p[1] for p in o["poly"]]
                    rects.append((min(xs), min(ys), max(xs), max(ys)))
                elif "w" in o and "h" in o:
                    rects.append((o["x"] - o["w"] / 2, o["y"] - o["h"] / 2, o["x"] + o["w"] / 2, o["y"] + o["h"] / 2))
        # NOT the scrub commons: it is sparse GROUND COVER (a feathered scatter of grass tufts on open ground),
        # not a feature with a footprint, and a bold place name reads perfectly well over it. Treating it as an
        # obstacle only worked while some ground was left bare - once the commons properly clothes the field's
        # voids too, scrub covers nearly the whole map and a title could find nowhere at all to sit. The grove
        # (dense closed canopy) and the marsh (a distinct wetland) stay obstacles.
        for o in self.M.get("village_groves", []) + self.M.get("marshes", []):
            polys.append([tuple(p) for p in o["poly"]])
        for fd in self.M.get("fields", []):
            polys.append([tuple(p) for p in fd["outline"]])
        if self.M.get("pond"):
            cx, cy, rx, ry = self.M["pond"]
            rects.append((cx - rx, cy - ry, cx + rx, cy + ry))
        for o in self.M.get("streams", []) + self.M.get("channels", []):
            lines.append([tuple(p) for p in o["poly"]])
        for ln in self.M.get("lanes", []):
            lines.append([tuple(p) for p in ln["pts"]])
        return rects, polys, lines

    def _box_clear(self, bx0: float, by0: float, bx1: float, by1: float, obs: Any) -> bool:
        """Whether the axis-aligned box clears every obstacle in (rects, polys, lines)."""
        rects, polys, lines = obs
        for ox0, oy0, ox1, oy1 in rects:
            if not (bx1 < ox0 or bx0 > ox1 or by1 < oy0 or by0 > oy1):
                return False
        corners = [(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)]
        for poly in polys:
            n = len(poly)
            if (
                any(point_in_poly(cx, cy, poly) for cx, cy in corners)
                or any(bx0 <= vx <= bx1 and by0 <= vy <= by1 for vx, vy in poly)
                or any(segments_cross(corners[e], corners[(e + 1) % 4], poly[k], poly[(k + 1) % n]) for e in range(4) for k in range(n))
            ):
                return False
        for poly in lines:
            if any(bx0 <= vx <= bx1 and by0 <= vy <= by1 for vx, vy in poly) or any(
                segments_cross(corners[e], corners[(e + 1) % 4], poly[k], poly[k + 1]) for e in range(4) for k in range(len(poly) - 1)
            ):
                return False
        return True

    def _blank_label_spot(self, vx0: float, vy0: float, vw: float, vh: float, tw: float, th: float, margin: float = 22, step: float = 24) -> Pt | None:
        """Scan the window (top-to-bottom, left-to-right) for the first box of size (tw, th) that clears every
        feature; returns its (x, y) top-left, or None if the map is too full."""
        obs = self._title_obstacles()
        y = vy0 + margin
        while y + th <= vy0 + vh - margin:
            x = vx0 + margin
            while x + tw <= vx0 + vw - margin:
                if self._box_clear(x, y, x + tw, y + th, obs):
                    return (x, y)
                x += step
            y += step
        return None

    def finish(self, basepath: str, render: bool = True, png_width: int = 2600) -> int:
        if getattr(self, "_road_label", None):
            text, lx, ly = self._road_label
            rd = self.M.get("road") or []
            best = min((seg_closest(lx, ly, rd[i], rd[i + 1]) for i in range(len(rd) - 1)), key=lambda c: math.hypot(c[0] - lx, c[1] - ly), default=None)
            cands = [(lx, ly)]
            if best is not None:
                bx, by = best
                d = math.hypot(lx - bx, ly - by) or 1.0
                nx, ny = (lx - bx) / d, (ly - by) / d  # road -> anchor normal
                tx, ty = -ny, nx  # along-road tangent
                for side in (1, -1):  # anchor's side, then mirrored
                    for slide in (0, -45, 45, 90, -90):  # ...sliding along the road
                        cands.append((round(bx + nx * d * side + tx * slide), round(by + ny * d * side + ty * slide)))
            scored = [(self._label_hits(cx, cy, text, 12), i, (cx, cy)) for i, (cx, cy) in enumerate(cands)]
            _, _, (lx, ly) = min(scored)  # first zero-hit spot wins; else least-covered
            self.label(lx, ly, text, 12, italic=True, weight="bold", color="#5A4326")
            self.M["road_label"] = [lx, ly]
            self._road_label = None
        splices: list[Any] = []  # (placeholder_idx, block) - spliced high-index-first below
        if self._ground_idx is not None:  # the ordered linear-ground block (alley<street<road)
            feats = sorted(self.ground, key=lambda g: (g["zpri"], g["seq"]))
            block: list[Any] = []
            edge_zs: list[Any] = []
            bed_zs: list[Any] = []
            for g in feats:  # EDGES first (the dark borders), bottom of the block
                if g["edge"] is not None:
                    edge_zs.append(self._ground_idx + len(block))
                    block.append(g["edge"])
            for g in feats:  # then BEDS (paved surfaces) - they merge at crossings
                if g["bed"] is not None:
                    g["rec"][g["zkey"]] = self._ground_idx + len(block)  # recorded z = the bed's draw position
                    bed_zs.append(self._ground_idx + len(block))
                    block.append(g["bed"])
            for g in feats:  # then TOP marks (center dashes / gravel speckle)
                if g["top"] is not None:
                    block.append(g["top"])
            if edge_zs:  # every edge sits below every bed -> clean crossroads
                self.M["ground_edge_zmax"] = max(edge_zs)
            if bed_zs:
                self.M["ground_bed_zmin"] = min(bed_zs)
            splices.append((self._ground_idx, block))
        if self._water_idx is not None:  # the watercourse block: all EDGES (pond rims), then all
            wblock: list[Any] = []  # BEDS (one opacity group), then all SHEENS - crossings MERGE
            bedzs: list[Any] = []
            sheenzs: list[Any] = []
            for w in self.water:  # rims below every bed -> a feeder's bed covers the rim at its mouth
                if w.get("edge") is not None:
                    wblock.append(w["edge"])
            for w in self.water:  # a pond-anchored feeder is snapped to the rim now that the
                w["_bed"], w["_sheen"] = w["bed"], w["sheen"]  # pond is known (deferred - it may predate the pond)
                if w["clip"] is not None and self.M.get("pond"):
                    cp = self._clip_to_pond(w["clip"]["pts"])
                    dd = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in cp)
                    w["_bed"] = w["clip"]["bed_t"].format(dd=dd)
                    if w["clip"]["sheen_t"] is not None:
                        w["_sheen"] = w["clip"]["sheen_t"].format(dd=dd)
            wblock.append('<g opacity="0.85">')
            for w in sorted(self.water, key=lambda w: w["pond_fill"]):  # pond FILL drawn LAST (stable sort) so it
                w["rec"]["bedz"] = self._water_idx + len(wblock)  # covers any feeder's inside-the-rim overshoot
                bedzs.append(self._water_idx + len(wblock))
                wblock.append(w["_bed"])
            wblock.append('</g>')
            wblock.append('<g opacity="0.55">')
            for w in self.water:
                if w["_sheen"] is not None:
                    w["rec"]["sheenz"] = self._water_idx + len(wblock)
                    sheenzs.append(self._water_idx + len(wblock))
                    wblock.append(w["_sheen"])
            wblock.append('</g>')
            if bedzs:  # every bed sits below every sheen -> clean confluence
                self.M["water_bed_zmax"] = max(bedzs)
            if sheenzs:
                self.M["water_sheen_zmin"] = min(sheenzs)
            splices.append((self._water_idx, wblock))
        if self._late_water_idx is not None:  # the LATE block (comb-field channels; see __init__): same
            lblock: list[Any] = ['<g opacity="0.85">']  # shared-opacity compositing, spliced at ITS OWN
            for w in self.late_water:  # first-call position so the ditch net draws OVER the field's plots
                w["rec"]["bedz"] = self._late_water_idx + len(lblock)
                lblock.append(w["bed"])
            lblock.append('</g>')
            lblock.append('<g opacity="0.55">')
            for w in self.late_water:
                if w["sheen"] is not None:
                    w["rec"]["sheenz"] = self._late_water_idx + len(lblock)
                    lblock.append(w["sheen"])
            lblock.append('</g>')
            splices.append((self._late_water_idx, lblock))
        for idx, block in sorted(splices, key=lambda s: -s[0]):  # high index first so the lower stays valid
            self.out[idx : idx + 1] = block
        if self.view:  # crop the viewBox to the requested window
            ox, oy, vw, vh = self.view
            self.out[0] = self.out[0].replace(f'viewBox="0 0 {self.W} {self.H}"', f'viewBox="{ox} {oy} {vw} {vh}"')
        body = self.out + self.walls + self.top + self.toplabels + ['</svg>']  # WALLS over lanes; TOP furniture; LABEL text topmost
        with open(basepath + '.svg', 'w') as f:
            f.write('\n'.join(body))
        with open(basepath + '.json', 'w') as f:
            json.dump(self.M, f)
        # Two env knobs make iteration cheap without changing committed output (see SKILL.md
        # 'Render pipeline'; since the resvg switch the raster is ~0.6s even for the biggest map,
        # so these mostly save the render when nothing will look at the PNG):
        #   DIAGRAM_SKIP_RENDER  - skip the raster entirely; the gate reads the JSON, so tests set this and
        #                          never pay to render a PNG no test looks at.
        #   DIAGRAM_PNG_WIDTH=N  - render at N px instead of 2600; unset for the full-res committed PNG.
        if render and not os.environ.get("DIAGRAM_SKIP_RENDER"):
            env_w = os.environ.get("DIAGRAM_PNG_WIDTH")
            self.render_png(basepath, int(env_w) if env_w else png_width)  # keep the .png paired with the .svg
        return len(self.placed)

    def render_png(self, basepath: str, width: int = 2600) -> None:
        """Rasterize basepath.svg -> basepath.png via resvg.

        Called from finish() so the PNG can never drift from the SVG: there is no way to
        regenerate a map's SVG (by hand or via the test harness, which re-runs every gen)
        without also refreshing its PNG. Settlement maps need ~2600px for the small labels.

        resvg, not rsvg-convert (and deliberately NO fallback - resvg is required, see the
        SKILL.md skill-load install check): profiling Tango (2026-07) showed rsvg-convert
        spent ~16s at 2600px, ~2/3 of it on foliage circles lying entirely outside the
        cropped city viewBox; resvg culls off-view geometry properly and rasterizes the
        same SVG in ~0.6s with visually identical output. Two font requirements for that
        "identical": resvg's generic-family defaults name MS fonts, so 'serif' must be
        mapped to DejaVu Serif explicitly (--serif-family), and resvg does not synthesize
        oblique, so the real italic faces (fonts-dejavu-extra) must be installed or every
        italic label silently renders upright.
        A no-op (with a warning) when resvg is absent - the skill cannot render at all
        without it, so that is a host-setup problem, not a generation bug."""
        exe = shutil.which('resvg')
        if not exe:  # pragma: no cover - depends on the host toolchain, not on any code path
            sys.stderr.write(f'warning: resvg not found (sudo apt-get install -y resvg fonts-dejavu-extra); {basepath}.png not refreshed\n')
            return
        subprocess.run([exe, '--width', str(width), '--serif-family', 'DejaVu Serif', basepath + '.svg', basepath + '.png'], check=True)
