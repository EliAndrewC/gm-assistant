#!/usr/bin/env python3
"""Automated checks for a Mode B settlement-map manifest (diagram skill).

Reads the JSON manifest the generator emits and asserts the Mode B rules. The
UNIVERSAL invariants (no overlaps, houses off corridors and field-adjacent, every
field ringed, no cultivation on a hill, houses face south, headman largest,
channels anchored at both ends and gently winding) are always checked. The
VILLAGE-SPECIFIC expectations are read from manifest["meta"] and from each
channel's frm/to anchors, so this validator works for any village/hamlet rather
than assuming one village's layout. Exit 0 if all pass, 1 otherwise.

The skill's plain-English / persona review still applies on top of this gate -
and remember a green check on the wrong geometry is worse than no check, so the
manifest records the *rendered* (smoothed) boundary and you still eyeball a crop.

Many checks are pure rendering/geometry (no overlaps, lanes layered, labels clear) and need no
justification. But where a check encodes a HISTORICAL or SETTING finding - who lives where, well
densities, the Shinto/Buddhist split, caste geography, the commerce-fronts-the-street pattern - the
reasoning (the "why") lives in settlements.md's "Historical grounding: the why behind the realism checks"
section; such checks below carry a brief `# WHY:` pointer to it. (Project policy: research-driven
rules record their why next to the rule - see CLAUDE.md "Generation Behavior".)
"""

import json
import math
import sys
from collections.abc import Callable, Sequence
from typing import Any

Manifest = dict[str, Any]  # the JSON settlement manifest the generator emits
Pt = Sequence[float]  # an (x, y) point (list from JSON, or a tuple)
Poly = Sequence[Sequence[float]]  # a polyline / polygon
Check = Callable[..., None]  # the check(name, passed, message) sink passed into the check functions


def load(path: str) -> Manifest:
    with open(path) as f:
        result: Manifest = json.load(f)
        return result


def rect_corners(h: dict[str, Any]) -> list[tuple[float, float]]:
    a = math.radians(h["rot"])
    ca, sa = math.cos(a), math.sin(a)
    w, ht = h["w"], h["h"]
    return [(h["x"] + dx * ca - dy * sa, h["y"] + dx * sa + dy * ca) for dx, dy in [(-w / 2, -ht / 2), (w / 2, -ht / 2), (w / 2, ht / 2), (-w / 2, ht / 2)]]


def _struct_rect(s: dict[str, Any]) -> dict[str, Any]:
    """Normalize a solid footprint feature to a rect for the overlap tests. Every solid feature now
    carries w/h(/rot)."""
    return {"x": s["x"], "y": s["y"], "w": s["w"], "h": s["h"], "rot": s.get("rot", 0)}


def _box_hits_poly(box: tuple[float, float, float, float], poly: Poly) -> bool:
    """Whether an axis-aligned box (x0,y0,x1,y1) overlaps a polygon (corner-in, vertex-in, or edge-cross)."""
    x0, y0, x1, y1 = box
    bc = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    n = len(poly)
    return (
        any(point_in_poly(cx, cy, poly) for cx, cy in bc)
        or any(x0 <= vx <= x1 and y0 <= vy <= y1 for vx, vy in poly)
        or any(segments_cross(bc[e], bc[(e + 1) % 4], poly[k], poly[(k + 1) % n]) for e in range(4) for k in range(n))
    )


def sweep_hi(lo: float, hi: float, step: float, cap: int = 500) -> float:
    """Clamp a grid-sweep's upper bound so a MALFORMED coordinate (a stray vertex millions of px
    off the map) cannot blow the sweep up to billions of cells and make the validator appear to
    hang. A real settlement spans at most ~1,000-3,000 px (a few hundred steps at the 8px cell,
    well under `cap`), so this never truncates a valid map - but garbage input is bounded to `cap`
    steps per axis (<= 250k cells, a couple of seconds), so the check FAILS the bad manifest (via
    city_geometry_within_canvas) instead of looping forever. A validator must never hang on bad input."""
    return min(hi, lo + step * cap)


def poly_area(pts: Poly) -> float:
    """Absolute polygon area (shoelace) of a list of (x, y) vertices."""
    n = len(pts)
    s = 0.0
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        s += x0 * y1 - x1 * y0
    return abs(s) / 2.0


def convex_hull(pts: Sequence[Pt]) -> Poly:
    """Convex hull (monotone chain) of a point cloud, as a CCW vertex list. <3 unique points returns them
    as-is (a degenerate hull of zero area)."""
    ps = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))
    if len(ps) < 3:
        return [(x, y) for x, y in ps]

    def cross(o: Pt, a: Pt, b: Pt) -> float:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list[Pt] = []
    for p in ps:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list[Pt] = []
    for p in reversed(ps):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def largest_empty_gap(poly: Poly, pts: Sequence[Pt], occupied: list[dict[str, Any]] | None = None, step: float = 30) -> float:
    """The radius of the largest empty pocket inside `poly`: the max over interior grid points of the
    distance to the nearest point in `pts`. A thin firebreak strip stays within a house-reach of homes
    on either side (small gap); a whole empty block has an interior point far from any house (large gap).
    This is the dead-zone signal a per-quarter density AVERAGE cannot see (a half-full quarter averages
    fine). Grid points that fall inside an `occupied` rect (a civic compound - a temple or yamen in a
    mixed quarter is built ground, not empty) are skipped, so a compound does not read as a dwelling
    dead zone. Returns 0.0 for an empty poly bbox; a large sentinel if `pts` is empty."""
    if not pts:
        return float("inf")
    occupied = occupied or []
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    worst = 0.0
    _hx, _hy = sweep_hi(min(xs), max(xs), step), sweep_hi(min(ys), max(ys), step)  # bounded: a malformed vertex cannot hang the sweep
    gx = min(xs)
    while gx <= _hx:
        gy = min(ys)
        while gy <= _hy:
            if point_in_poly(gx, gy, poly) and not any(abs(gx - r["x"]) <= r["w"] / 2 and abs(gy - r["y"]) <= r["h"] / 2 for r in occupied):
                d = min(math.hypot(gx - dx, gy - dy) for dx, dy in pts)
                if d > worst:
                    worst = d
            gy += step
        gx += step
    return worst


# ---- overlap classification registry ---------------------------------------------------------------
# Every footprint feature (a manifest key holding a list of dicts with positional geometry) must be
# classified below. The DEFAULT is "must not overlap anything": a SOLID feature joins `structs`, which
# the no_structure_* checks clear against each other and against the walls / water / roads / fields it
# should not sit on. Overlaps are OPT-IN - a feature that is meant to overlap something (a label, a
# bridge over water, a guard tower on the wall) is named in _OVERLAP_EXEMPT with its reason. The
# `every_feature_classified_for_overlap` check fires when a NEW feature key appears in none of these
# sets, forcing whoever adds it to declare its overlap behavior rather than silently skipping it.
_OVERLAP_STRUCTS = ("houses", "buildings", "flophouses", "cemeteries", "mausoleums", "cremation_grounds", "ossuaries", "ministries", "fire_towers", "byres")
# `shrines` duplicates the primary religious halls (shrine_hall records both), so it rides along with
# `religious`; both are halls that structs must AVOID, gated by no_structure_on_religious.
_OVERLAP_TARGETS = ("manors", "religious", "shrines", "gate_structs", "docks")
_OVERLAP_LINEAR = (
    "fields",
    "fallow_patches",
    "flower_fields",
    "streams",
    "channels",
    "town_streets",
    "alleys",
    "lanes",
    "wards",
    "ponds",
    "pastures",
    "forests",
    "commons",
    "dry_plots",
    "marshes",
    "canals",
    "roads",
    "crescent_ponds",
)  # linear / area features structs avoid (canals = the cargo canal; roads = the multi-road list, same ground the single M['road'] covers; crescent_ponds = the fengshui 半月塘 focal pond, reserved as a placement keep-out so the cluster packs around it)
_OVERLAP_EXEMPT = {
    "storehouses": "merchant kura drawn as an annex deliberately abutting its shop",
    "farm_sheds": "a farmstead's grain-storehouse kura drawn as an annex abutting its own farmhouse's back wall (farm_sheds_attached verifies the attachment)",
    "threshing_yards": "a farmstead's threshing/drying yard drawn as an annex abutting its own farmhouse",
    "gardens": "a farmstead's dooryard kitchen garden drawn as a plot abutting its own farmhouse",
    "groves": "a farmstead's windbreak grove (yashikirin) drawn as a clump abutting the windward side of its own farmhouse",
    "merchant_estates": "a walled court AROUND an inner building that is itself an overlap-checked struct",
    "wells": "a small well-head dropped into the open gaps between dwellings (its nominal footprint may kiss a dense-city building)",
    "wall_towers": "guard towers stand ON the city wall - an intentional overlap - and clear of the interior",
    "bridges": "a bridge spans a stream/moat to carry a road over it (intentional water + road overlap)",
    "kido": "a ward gate sits ON the ward fence at the point a lane passes through it",
    "inspection_stations": "an inspection post sited AT the city gate, part of the gate complex (overlaps the gate furniture)",
    "water_gates": "the shuimen arch stands ON the city wall over its canal - intentional, like the kido on its fence",
    "jetties": "planked mooring fingers running out over the river water, like bridge decks",
    "field_ditches": "in-field irrigation ditches (main/laterals/drain) - water lines drawn ON the paddy, validated by water_channels_obtuse_turns + field_ditches_terminate, not solid structures",
    "village_groves": "the COMMUNAL fengshui windbreak (back-village belt / water-mouth cluster / bamboo copses) - vegetation drawn LAST in open ground at the cluster margins; a copse may abut a house, validated by the village_windbreak_* checks",
    "quarters": "declarative zoning overlays (feature 006), not solid structures - they intentionally contain buildings and are validated by the city_quarters_* / per-quarter density checks",
    "mills": "a water mill (水磨) focal feature drawn BESIDE its watercourse with the wheel dipping into the drain/stream - an intentional water-adjacency like a bridge/jetty; reserved in open ground (self.placed) so it does not overlap dwellings",
    "field_ponds": "feature 012: a low-pocket pond sunk INTO one paddy plot, the field tiling around it - drawn ON the paddy like field_ditches, validated by paddy_features_match_archetype",
    "field_rocks": "feature 012: a bedrock outcrop the terrace risers wrap around, drawn ON the paddy - validated by paddy_features_match_archetype (bedrock archetypes only)",
    "field_graves": "feature 012: a rare in-field grave island (calibrated liberty) the flat paddy tiles around, drawn ON the paddy - validated by paddy_features_match_archetype",
}
_OVERLAP_CLASSIFIED = set(_OVERLAP_STRUCTS) | set(_OVERLAP_TARGETS) | set(_OVERLAP_LINEAR) | set(_OVERLAP_EXEMPT)


def sat_overlap(p: Poly, q: Poly) -> bool:
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


def seg_closest(px: float, py: float, a: Pt, b: Pt) -> tuple[float, float]:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return ax, ay
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return ax + t * dx, ay + t * dy


def seg_dist(px: float, py: float, a: Pt, b: Pt) -> float:
    cx, cy = seg_closest(px, py, a, b)
    return math.hypot(px - cx, py - cy)


def pt_to_rect(px: float, py: float, rect: dict[str, Any]) -> float:
    """Shortest distance from a point to a (possibly rotated) rectangle footprint; 0 if the point is inside.
    Un-rotates the point into the rect's local frame, clamps to the half-extents, and measures the overhang."""
    a = math.radians(rect.get("rot", 0))
    ca, sa = math.cos(a), math.sin(a)
    dx, dy = px - rect["x"], py - rect["y"]
    lx, ly = dx * ca + dy * sa, -dx * sa + dy * ca  # local coords (rect axis-aligned here)
    ox = max(abs(lx) - rect["w"] / 2, 0.0)
    oy = max(abs(ly) - rect["h"] / 2, 0.0)
    return math.hypot(ox, oy)


def seg_to_rect_dist(a: Pt, b: Pt, rect: dict[str, Any]) -> float:
    """Shortest distance between segment a-b and a (possibly rotated) rectangle; 0 if they touch/cross. Needed
    where a thin corridor can thread THROUGH a wide footprint BETWEEN its corners - corner-sampling misses that.
    Standard convex result: 0 on intersection, else min(endpoint-to-rect, rect-corner-to-segment)."""
    corners = rect_corners(rect)
    for i in range(4):
        if segments_cross(a, b, corners[i], corners[(i + 1) % 4]):
            return 0.0
    if pt_to_rect(a[0], a[1], rect) == 0 or pt_to_rect(b[0], b[1], rect) == 0:
        return 0.0
    return min(min(pt_to_rect(a[0], a[1], rect), pt_to_rect(b[0], b[1], rect)), min(seg_dist(cx, cy, a, b) for cx, cy in corners))


# the 2 patron fortunes of each Great Clan - a town defaults to one monastery for each
CLAN_FORTUNES = {
    "crab": {"Bishamon", "Ebisu"},
    "crane": {"Benten", "Daikoku"},
    "dragon": {"Hotei", "Ebisu"},
    "lion": {"Bishamon", "Daikoku"},
    "phoenix": {"Fukurokujin", "Hotei"},
    "scorpion": {"Benten", "Jurojin"},
    "unicorn": {"Fukurokujin", "Jurojin"},
}


def unit_dir(spec: Any) -> tuple[float, float] | None:
    """A cardinal name or [dx,dy] vector -> a unit vector in map coords (+y=south). None if bad."""
    DIRS = {
        "north": (0, -1),
        "south": (0, 1),
        "east": (1, 0),
        "west": (-1, 0),
        "northeast": (0.7071, -0.7071),
        "northwest": (-0.7071, -0.7071),
        "southeast": (0.7071, 0.7071),
        "southwest": (-0.7071, 0.7071),
    }
    if spec is None:
        return None
    if isinstance(spec, str):
        return DIRS.get(spec.lower())
    dl = math.hypot(spec[0], spec[1]) or 1
    return (spec[0] / dl, spec[1] / dl)


def segments_cross(a: Pt, b: Pt, c: Pt, d: Pt) -> bool:
    def ccw(p: Pt, q: Pt, r: Pt) -> bool:
        return (r[1] - p[1]) * (q[0] - p[0]) > (q[1] - p[1]) * (r[0] - p[0])

    return ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d)


def seg_intersect(a: Pt, b: Pt, c: Pt, d: Pt) -> tuple[float, float] | None:
    """The (x, y) where segments ab and cd cross, or None if parallel. Call only when they cross."""
    den = (a[0] - b[0]) * (c[1] - d[1]) - (a[1] - b[1]) * (c[0] - d[0])
    if abs(den) < 1e-9:
        return None
    t = ((a[0] - c[0]) * (c[1] - d[1]) - (a[1] - c[1]) * (c[0] - d[0])) / den
    return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))


def point_in_poly(px: float, py: float, poly: Any) -> bool:
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


def poly_dist(px: float, py: float, poly: Poly) -> float:
    if point_in_poly(px, py, poly):
        return 0.0
    return min(seg_dist(px, py, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def poly_gap(a: Poly, b: Poly) -> float:
    """Minimum distance between two polygons; 0.0 if they overlap, touch, or one contains the other."""
    na, nb = len(a), len(b)
    if any(point_in_poly(x, y, b) for x, y in a) or any(point_in_poly(x, y, a) for x, y in b):
        return 0.0
    if any(segments_cross(a[i], a[(i + 1) % na], b[j], b[(j + 1) % nb]) for i in range(na) for j in range(nb)):
        return 0.0
    return min(min(poly_dist(x, y, b) for x, y in a), min(poly_dist(x, y, a) for x, y in b))


def check_theater_stage(M: Manifest, check: Check) -> None:
    """The theater stage's siting. It BELONGS to a temple/monastery precinct (a temple OPERA STAGE / shrine
    NOH stage), the audience gathering in the open ground between stage and hall, the stage FACING the hall:
    (1) `theater_stage_clear` - the stage + its viewing ground sit in CLEAR ground, overlapping NOTHING (no
        wall, moat, road, street/alley, watercourse, building, compound, grave, field, or pond). Unlike a
        packed dwelling it is not auto-checked by the generic overlap pass, so this is its dedicated guard.
    (2) `theater_stage_by_temple` - ADJACENT to a religious hall (center within ~260px of the nearest one).
    (3) `theater_stage_faces_temple` - its viewing ground OPENS TOWARD that hall (the stage faces it). The
        glyph's open side is local +y, so after `rot` it points (-sin, cos); that aligns with the hall."""
    ts = M.get("theater_stage")
    if not ts:
        return
    # (1) CLEAR: build the full footprint (the viewing ground PLUS the roofed stage straddling its north edge)
    w, h = ts["w"], ts["h"]
    sh = h * 0.26
    cyl, fh = -sh * 0.25, h + sh * 0.5
    thr = math.radians(ts.get("rot", 0))
    ca, sa = math.cos(thr), math.sin(thr)
    sc = [(ts["x"] + dx * ca - dy * sa, ts["y"] + dx * sa + dy * ca) for dx, dy in ((-w / 2, cyl - fh / 2), (w / 2, cyl - fh / 2), (w / 2, cyl + fh / 2), (-w / 2, cyl + fh / 2))]
    hits = []
    lines = []  # linear barriers (name, polyline, half-width)
    if M.get("wall"):
        lines.append(("the wall", M["wall"], 9))
    if M.get("moat"):
        lines.append(("the moat", M["moat"], M.get("moat_width", 26) / 2 + 4))
    if M.get("road"):
        lines.append(("a road", M["road"], M.get("road_width", 26) / 2))
    if M.get("ring_road"):
        lines.append(("the ring road", M["ring_road"], M.get("ring_road_width", 15) / 2))
    lines += [("a street", st["pts"], st.get("w", 18) / 2) for st in M.get("town_streets", [])]
    lines += [("an alley", a["pts"], a.get("w", 10) / 2) for a in M.get("alleys", [])]
    lines += [("a stream", s["poly"], s.get("w", 9) / 2) for s in M.get("streams", [])]
    lines += [("a channel", c["poly"], c.get("w", 2.5) / 2 + 2) for c in M.get("channels", [])]
    lines += [("the canal", c["poly"], c.get("w", 12) / 2 + 2) for c in M.get("canals", [])]
    for nm, pts, hw in lines:
        if len(pts) >= 2 and footprint_on_line(sc, pts, hw):
            hits.append(nm)
    granary = M.get("granary")  # solid features (buildings, compounds, graves)
    solids = (
        [s for k in _OVERLAP_STRUCTS for s in M.get(k, [])]
        + M.get("manors", [])
        + M.get("religious", [])
        + M.get("shrines", [])
        + M.get("gate_structs", [])
        + M.get("storehouses", [])
        + M.get("merchant_estates", [])
        + M.get("threshing_yards", [])
        + M.get("gardens", [])
        + M.get("inspection_stations", [])
        + (granary["stores"] if granary else [])
    )
    if M.get("governor_mansion"):
        solids.append(M["governor_mansion"])
    for r in solids:
        if abs(r["x"] - ts["x"]) + abs(r["y"] - ts["y"]) <= 440 and sat_overlap(sc, rect_corners(_struct_rect(r))):
            hits.append(f"a {r.get('kind', 'building')}")
    for fkey in ("fields", "fallow_patches", "flower_fields"):  # areas: paddies/fields and the pond
        for fld in M.get(fkey, []):
            ol = fld["outline"]
            if any(point_in_poly(px, py, ol) for px, py in sc) or any(point_in_poly(vx, vy, sc) for vx, vy in ol):
                hits.append("a field")
                break
    pond = M.get("pond")
    if pond and (
        point_in_poly(pond[0], pond[1], sc)  # pond engulfed by the stage, OR a stage corner in the pond
        or any(((px - pond[0]) / (pond[2] + 6)) ** 2 + ((py - pond[1]) / (pond[3] + 6)) ** 2 <= 1.0 for px, py in sc)
    ):
        hits.append("the pond")
    check(
        "theater_stage_clear",
        not hits,
        f"the theater stage footprint overlaps {sorted(set(hits))[:6]} - the stage and its viewing ground "
        f"must sit in CLEAR ground, touching nothing (no wall, moat, road, street/alley, watercourse, "
        f"building, compound, grave, field, or pond)",
    )
    halls = M.get("religious", [])
    if not halls:
        return
    nearest = min(halls, key=lambda h: math.hypot(ts["x"] - h["x"], ts["y"] - h["y"]))
    near = math.hypot(ts["x"] - nearest["x"], ts["y"] - nearest["y"])
    check(
        "theater_stage_by_temple",
        near <= 260,
        f"the theater stage sits {round(near)}px from the nearest temple/monastery (want <= 260) - it is a "
        f"temple/shrine performance stage, so site it ADJACENT to a religious hall with the viewing ground between them",
    )
    th = math.radians(ts.get("rot", 0))
    ox, oy = -math.sin(th), math.cos(th)  # the viewing ground's open direction (toward the audience/temple)
    dx, dy = nearest["x"] - ts["x"], nearest["y"] - ts["y"]
    d = math.hypot(dx, dy) or 1.0
    facing = (ox * dx + oy * dy) / d
    check(
        "theater_stage_faces_temple",
        facing >= 0.5,
        f"the theater stage's viewing ground does not OPEN toward its temple (alignment {facing:.2f}, want "
        f">= 0.5) - the stage faces the hall with the audience between, so set its `rot` so the ground opens "
        f"toward the temple (the stage's back is the side AWAY from the audience)",
    )


def check_fire_features(M: Manifest, check: Check) -> None:
    """Geometry of the fire-watch towers (hinomi-yagura) a walled town or a city draws. Scale-agnostic:
    the PRESENCE/count checks live in the scale blocks; this validates whatever is drawn, so it is a
    no-op for a settlement that has none. WHY (a dense, enclosed wooden core needs a fire-watch over
    its rooftops, manned by the magistrate's watch): settlements.md 'Fire towers'."""
    towers = M.get("fire_towers", [])
    # A tower's WATCH RADIUS: the visual neighborhood of rooftops one hinomi-yagura usefully covers.
    # Both clauses below share it - a tower more than one radius from any dwelling watches nothing,
    # and two towers within one radius of EACH OTHER watch the same rooftops twice.
    WATCH = 230
    COMMON = {"laborer", "laborer_large", "servant", "merchant", "merchant_house", "merchant_large", "shop"}
    SAM = {"samurai", "samurai_large"}
    dwell = [(b["x"], b["y"], b.get("kind")) for b in M.get("buildings", []) if b.get("kind") in COMMON | SAM]
    if towers and dwell:
        misplaced = []
        for t in towers:
            near = sorted(dwell, key=lambda d: math.hypot(d[0] - t["x"], d[1] - t["y"]))[:3]
            nearest = math.hypot(near[0][0] - t["x"], near[0][1] - t["y"])
            sam = sum(1 for d in near if d[2] in SAM)
            if nearest > WATCH or sam * 2 > len(near):  # isolated, or sitting in the samurai quarter
                misplaced.append((round(t["x"]), round(t["y"])))
        check("fire_tower_in_commoner_quarter", not misplaced, f"fire tower(s) {misplaced} sit isolated or in the samurai quarter - a hinomi-yagura watches the dense COMMONER rooftops")
    # a fire tower stands in the dense built-up core, never ON cultivated ground: a hinomi-yagura on a
    # paddy (or the in-wall chrysanthemum field / a fallow patch) is nonsense, and an in-wall agricultural
    # district puts a real field right where a tower might land. (There is no blanket no_structure_on_field
    # - farmhouses legitimately ring the fields - so the towers carry their own field-clearance check.)
    fields = [f["outline"] for f in M.get("fields", [])] + [f["outline"] for f in M.get("fallow_patches", [])] + [f["outline"] for f in M.get("flower_fields", [])]
    if towers and fields:
        on_field = []
        for t in towers:
            rc = rect_corners(_struct_rect(t))
            for ol in fields:
                n = len(ol)
                if any(point_in_poly(cx, cy, ol) for cx, cy in rc) or any(segments_cross(rc[i], rc[(i + 1) % 4], ol[e], ol[(e + 1) % n]) for i in range(4) for e in range(n)):
                    on_field.append((round(t["x"]), round(t["y"])))
                    break
        check("fire_tower_clear_of_fields", not on_field, f"fire tower(s) {on_field} sit on a field - a hinomi-yagura stands in the dense urban core, never on a paddy or planting")
    # MULTIPLE TOWERS DISPERSE. A settlement dense/populous enough to warrant a second tower gets it
    # to watch a DIFFERENT quarter's rooftops: historically the fire-watch was parcelled out per
    # neighborhood (in Edo each machi block-group kept its own hinomi-yagura, and the shogunate's
    # official watch stations were likewise distributed one to a district), so towers were spread
    # across the city, never bunched. Two towers inside one watch radius of each other duplicate
    # coverage while some other dense quarter goes unwatched - the second tower accomplishes nothing.
    # WHY: settlements.md "Fire towers".
    if len(towers) >= 2:
        bunched = [((round(a["x"]), round(a["y"])), (round(b["x"]), round(b["y"]))) for i, a in enumerate(towers) for b in towers[i + 1 :] if math.hypot(a["x"] - b["x"], a["y"] - b["y"]) < WATCH]
        check(
            "fire_towers_dispersed",
            not bunched,
            f"fire tower pair(s) {bunched} stand within one watch radius ({WATCH} px) of each other - a second "
            f"hinomi-yagura exists to watch a DIFFERENT quarter's rooftops; spread them across the settlement",
        )
    # EACH TOWER STANDS AMID THE DISTRICT IT WATCHES. Dispersal alone is not enough: two towers a
    # comfortable distance apart can still both sit in the SAME QUADRANT, leaving the dense commoner
    # quarter across the city unwatched (Tango's original pair both stood NW of center while the NE
    # laborer warren - the city's biggest rooftop mass - had no watch). Historically the watch was
    # parcelled by district, every commoner roof belonging to SOME tower's watch, and the tower stood
    # amid its blocks (it watched outward over rooftops on all sides, not a district it sat at the far
    # edge of). So: assign every commoner dwelling to its NEAREST tower - that partition IS the de
    # facto watch districting the drawn towers imply - and each tower must stand near its district's
    # center of mass: offset <= max(0.9 x the district's RMS radius, one WATCH radius). A tower parked
    # in the wrong quadrant inherits the whole far side of the city as its "district" and lands far
    # off that centroid, which is exactly the failure. Inside the walls only, when walled - the
    # extramural gate-market rows are not part of the enclosed core the towers exist for.
    # WHY: settlements.md "Fire towers".
    wallp = M.get("wall")
    core = [d for d in dwell if d[2] not in SAM and (not wallp or point_in_poly(d[0], d[1], wallp))]
    if len(towers) >= 2 and core:
        offside = []
        for ti, t in enumerate(towers):
            g = [d for d in core if ti == min(range(len(towers)), key=lambda j: math.hypot(d[0] - towers[j]["x"], d[1] - towers[j]["y"]))]
            if not g:
                continue
            gx, gy = sum(d[0] for d in g) / len(g), sum(d[1] for d in g) / len(g)
            rms = math.sqrt(sum((d[0] - gx) ** 2 + (d[1] - gy) ** 2 for d in g) / len(g))
            off = math.hypot(t["x"] - gx, t["y"] - gy)
            if off > max(0.9 * rms, WATCH):
                offside.append((round(t["x"]), round(t["y"]), round(off), round(rms)))
        check(
            "fire_tower_amid_its_district",
            not offside,
            f"fire tower(s) {offside} (x, y, offset, district rms) stand far off the center of the rooftop "
            f"district they are nearest to - the towers are bunched in one part of the city while a dense "
            f"commoner quarter goes unwatched; put one tower AMID each major commoner quarter",
        )
    # A TOWER KEEPS A SMALL STANDOFF FROM ITS NEIGHBORS (>= 5 px of daylight). The blanket
    # no_structure_overlaps SAT test only catches true footprint intersection, so a tower butted
    # flush against a house passes it while READING as a collision: the drawn glyph's roof cap
    # overhangs the recorded frame by ~2px a side, and an open braced-timber tower needs its
    # footing and ladder clear of the neighboring eaves anyway (it stands on a seam, not in a
    # party-wall row). GM rule: at least 5 px between a fire tower and any neighboring building.
    STANDOFF = 5
    if towers:
        neigh = [s for k in _OVERLAP_STRUCTS if k != "fire_towers" for s in M.get(k, [])]
        crowded = []
        for t in towers:
            tc = rect_corners(_struct_rect(t))
            for s in neigh:
                sc = rect_corners(_struct_rect(s))
                if math.hypot(t["x"] - s["x"], t["y"] - s["y"]) > 160:  # cheap prefilter
                    continue
                gap = min(min(seg_dist(px, py, sc[i], sc[(i + 1) % 4]) for px, py in tc for i in range(4)), min(seg_dist(px, py, tc[i], tc[(i + 1) % 4]) for px, py in sc for i in range(4)))
                if sat_overlap(tc, sc) or gap < STANDOFF:
                    crowded.append((round(t["x"]), round(t["y"]), round(gap, 1)))
                    break
        check(
            "fire_tower_standoff",
            not crowded,
            f"fire tower(s) {crowded} (x, y, gap px) stand within {STANDOFF} px of a neighboring building - "
            f"the open braced frame (and its overhanging roof cap) needs a little daylight around its footing; "
            f"nudge the tower onto clearer ground",
        )
    # A TOWER NEVER STANDS ON A WELLHEAD. Wells are overlap-EXEMPT (a wellhead's nominal footprint
    # may kiss a dense-city building - see _OVERLAP_EXEMPT), so neither the blanket
    # no_structure_overlaps pass nor fire_tower_standoff above (which walks _OVERLAP_STRUCTS only)
    # guards a tower dropped onto a well. But that exemption is about houses ringing a tenement
    # court closely - a fire tower must not ride it: its braced footing would stand in the well
    # court blocking the shared draw-point, and the two glyphs read as a plain collision. Same
    # 5 px daylight rule as fire_tower_standoff; circle (the well's clearance disc, radius r,
    # as in wells_clear_of_shrine_and_torii) vs the tower's rect.
    wells = M.get("wells", [])
    if towers and wells:
        on_well = []
        for t in towers:
            hw, hh = t["w"] / 2, t["h"] / 2
            for wl in wells:
                ddx = wl["x"] - t["x"] - max(-hw, min(hw, wl["x"] - t["x"]))
                ddy = wl["y"] - t["y"] - max(-hh, min(hh, wl["y"] - t["y"]))
                if math.hypot(ddx, ddy) < wl["r"] + STANDOFF:
                    on_well.append((round(t["x"]), round(t["y"])))
                    break
        check(
            "fire_tower_clear_of_wells",
            not on_well,
            f"fire tower(s) {on_well} stand on (or within {STANDOFF} px of) a wellhead - a hinomi-yagura's footing must not block a quarter's shared draw-point; nudge the tower off the well court",
        )
    # ... and clear of GRAVEYARDS (GM, 2026-07): a watch-tower's braced footing planted among
    # the graves reads as a plain collision - the dead get the same daylight as the living
    cems = M.get("cemeteries", [])
    if towers and cems:
        on_grave = []
        for t in towers:
            tc = rect_corners({"x": t["x"], "y": t["y"], "w": t["w"] + 2 * STANDOFF, "h": t["h"] + 2 * STANDOFF, "rot": 0})
            for cm in cems:
                if sat_overlap(tc, rect_corners({"x": cm["x"], "y": cm["y"], "w": cm["w"], "h": cm["h"], "rot": 0})):
                    on_grave.append((round(t["x"]), round(t["y"])))
                    break
        check("fire_tower_clear_of_graveyards", not on_grave, f"fire tower(s) {on_grave} stand on (or within {STANDOFF} px of) a graveyard - move the watch-tower off the burial ground")


def water_setback(width: float) -> float:
    """The set-back a BURIAL ground keeps from the EDGE of open water, scaling with the waterway's
    width: even a narrow STREAM floods graves out, so the floor is a solid ~75px; a moat (the heaviest
    watercourse, ~26px wide -> ~130px) more still, a river or canal most. A burial ground by big water
    floods out, so the bigger the watercourse the further back the dead must lie. (Thin irrigation
    channels are not open water and are not checked at all.)"""
    return max(75, min(140, 5.0 * width))


def edge_dist(px: float, py: float, poly: Poly) -> float:
    return min(seg_dist(px, py, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def in_ellipse(px: float, py: float, e: Any, scale: float = 1.0) -> bool:
    cx, cy, rx, ry = e
    return bool(((px - cx) / (rx * scale)) ** 2 + ((py - cy) / (ry * scale)) ** 2 <= 1.0)


def polyline_len(poly: Poly) -> float:
    return sum(math.hypot(poly[i + 1][0] - poly[i][0], poly[i + 1][1] - poly[i][1]) for i in range(len(poly) - 1))


def clip_poly_rect(poly: Poly, x0: float, y0: float, x1: float, y1: float) -> list[Any]:
    """Sutherland-Hodgman clip of a polygon to an axis rect; returns the clipped polygon (may be []).
    Used to find how much of an off-edge field actually shows inside the rendered map window."""

    def cl(pts: list[Any], ins: Callable[[Any], bool], isc: Callable[[Any, Any], tuple[float, float]]) -> list[Any]:
        out = []
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            ia, ib = ins(a), ins(b)
            if ia:
                out.append(a)
            if ia != ib:
                out.append(isc(a, b))
        return out

    p: list[Any] = list(poly)
    for ins, isc in (
        (lambda q: q[0] >= x0, lambda a, b: (x0, a[1] + (b[1] - a[1]) * (x0 - a[0]) / ((b[0] - a[0]) or 1e-9))),
        (lambda q: q[0] <= x1, lambda a, b: (x1, a[1] + (b[1] - a[1]) * (x1 - a[0]) / ((b[0] - a[0]) or 1e-9))),
        (lambda q: q[1] >= y0, lambda a, b: (a[0] + (b[0] - a[0]) * (y0 - a[1]) / ((b[1] - a[1]) or 1e-9), y0)),
        (lambda q: q[1] <= y1, lambda a, b: (a[0] + (b[0] - a[0]) * (y1 - a[1]) / ((b[1] - a[1]) or 1e-9), y1)),
    ):
        if not p:
            return []
        p = cl(p, ins, isc)
    return p


def onmap_field_edge(poly: Poly, x0: float, y0: float, x1: float, y1: float, eps: float = 8) -> float:
    """Length of a field's REAL boundary lying inside the map rect - EXCLUDING the segments that run
    along the rect edge (those are the off-map cut, where the field's farmhouses are off-screen).
    This is the on-map field frontage that ought to carry farmhouses."""
    cp = clip_poly_rect(poly, x0, y0, x1, y1)
    if len(cp) < 2:
        return 0.0
    total = 0.0
    for i in range(len(cp)):
        a, b = cp[i], cp[(i + 1) % len(cp)]
        on_rect = (
            (abs(a[0] - x0) < eps and abs(b[0] - x0) < eps)
            or (abs(a[0] - x1) < eps and abs(b[0] - x1) < eps)
            or (abs(a[1] - y0) < eps and abs(b[1] - y0) < eps)
            or (abs(a[1] - y1) < eps and abs(b[1] - y1) < eps)
        )
        if not on_rect:
            total += math.hypot(b[0] - a[0], b[1] - a[1])
    return total


def footprint_on_line(sc: Poly, sp: Poly, hw: float) -> bool:
    """True if closed polygon sc overlaps polyline sp within half-width hw - a corner near a
    segment, a polyline vertex inside the polygon, or an edge crossing. sc may be a 4-corner
    building footprint OR a field outline. Used to test a footprint/field against a barrier
    (city wall stroke, moat)."""
    if any(seg_dist(cx, cy, sp[k], sp[k + 1]) < hw for (cx, cy) in sc for k in range(len(sp) - 1)):
        return True
    if any(point_in_poly(rx, ry, sc) for rx, ry in sp):
        return True
    return any(segments_cross(sp[k], sp[k + 1], sc[e], sc[(e + 1) % len(sc)]) for k in range(len(sp) - 1) for e in range(len(sc)))


def empty_street_runs(M: Manifest, w: Poly, maxgap: float = 130) -> list[tuple[str, int]]:
    """Stretches of town/city street INSIDE the wall `w` longer than `maxgap` with no building
    FRONTING them. A building serves only the street it actually fronts (its nearest, within the
    frontage band), so one beside a perpendicular cross-street can't paper over an empty stub on
    the lane. Returns [(label, run_px), ...] - a street earns its length from what it serves."""
    streets = M.get("town_streets", [])
    if not (streets and len(w) >= 3):
        return []
    # houses and shops front streets, but so do the CIVIC buildings - a government avenue lined
    # with ministries (or the governor's yamen, a temple) is serving those, not running empty
    blds = M.get("buildings", []) + M.get("houses", []) + M.get("ministries", []) + M.get("religious", []) + M.get("flophouses", [])
    if M.get("governor_mansion"):
        blds = blds + [M["governor_mansion"]]
    lines = [st["pts"] for st in streets]
    # a building cannot FRONT a street it is walled off from: if a ward fence or the city wall lies
    # between the building and the point it would front, it serves some OTHER side, not this street.
    # (Without this, the gap-band housing across a ward fence papered over a bare government avenue -
    # the avenue read as "served by houses" that were actually on the far side of the fence.)
    barriers = [wd["boundary"] for wd in M.get("wards", [])] + [list(w)]

    def walled_off(bx: float, by: float, fx: float, fy: float) -> bool:
        return any(segments_cross((bx, by), (fx, fy), tuple(bar[i]), tuple(bar[i + 1])) for bar in barriers for i in range(len(bar) - 1))

    FRONT, COVER, STEP = 95.0, 105.0, 25
    fronts: dict[int, list[dict[str, Any]]] = {}
    for b in blds:
        best, bi, bfoot = FRONT, None, None
        for i, sp in enumerate(lines):
            for k in range(len(sp) - 1):
                dd = seg_dist(b["x"], b["y"], sp[k], sp[k + 1])
                if dd < best:
                    best, bi = dd, i
                    bfoot = seg_closest(b["x"], b["y"], sp[k], sp[k + 1])
        if bi is not None and bfoot is not None and not walled_off(b["x"], b["y"], bfoot[0], bfoot[1]):
            fronts.setdefault(bi, []).append(b)
    empty = []
    for si, st in enumerate(streets):
        pts = st["pts"]
        servers = fronts.get(si, [])
        run = worst = 0
        for k in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[k], pts[k + 1]
            steps = max(1, int(math.hypot(bx - ax, by - ay) // STEP))
            for j in range(steps):
                t = j / steps
                x, y = ax + (bx - ax) * t, ay + (by - ay) * t
                if not point_in_poly(x, y, w) or any((b["x"] - x) ** 2 + (b["y"] - y) ** 2 < COVER * COVER for b in servers):
                    run = 0
                else:
                    run += STEP
                    worst = max(worst, run)
        if worst > maxgap:
            empty.append(("main" if st.get("main") else f"@{pts[0]}", worst))
    return empty


def approach_span(mx: float, my: float, half: float, ux: float, uy: float, M: Manifest, w: Poly, Wd: float, Hd: float) -> float:
    """March from a religious hall's front edge along (ux, uy) to the first HARD terminus - a
    town street, a field/flower-field, the rampart, or the map edge - and return the clear
    length. Buildings are deliberately NOT termini: a torii avenue is a cleared processional way
    (sando) that displaces dwellings, so its length is set by the public street or barrier it
    reaches, not by whatever housing it pushes aside. Used to size a monastery's torii avenue."""
    fields = [f["outline"] for f in M.get("fields", [])] + [f["outline"] for f in M.get("flower_fields", [])]
    streets = [(st["pts"], st.get("w", 24)) for st in M.get("town_streets", [])]
    start = half + 12
    s = start
    while s < start + 600:
        px, py = mx + ux * s, my + uy * s
        if not (0 <= px <= Wd and 0 <= py <= Hd):
            break
        if w and not point_in_poly(px, py, w):
            break
        if any(point_in_poly(px, py, fp) for fp in fields):
            break
        if any(seg_dist(px, py, pts[k], pts[k + 1]) < sw / 2 + 4 for pts, sw in streets for k in range(len(pts) - 1)):
            break
        s += 10
    return s - start


def torii_room_for_more(r: dict[str, Any], grp: Sequence[Pt], M: Manifest, w: Poly, Wd: float, Hd: float, pitch: float = 46) -> bool:
    """Is there clear space for ANOTHER torii beyond a temple's existing avenue `grp`? Find the street/
    road the torii sit on, head along it AWAY from the temple, and test the next arch-slot (one `pitch`
    past the farthest torii): it has room if that point is inside the wall and clear of buildings/fields.
    Buildings are OBSTACLES, never displaced - the check only fills space that is ALREADY open after all
    the housing is placed, so it never nudges a rearrangement. A temple whose torii aren't on a street,
    or whose approach is built up to the avenue's end, has no room and is fine as-is."""
    tc = (sum(t[0] for t in grp) / len(grp), sum(t[1] for t in grp) / len(grp))
    lanes = [st["pts"] for st in M.get("town_streets", [])] + ([M["road"]] if M.get("road") else [])
    best = None
    for pts in lanes:
        for k in range(len(pts) - 1):
            d = seg_dist(tc[0], tc[1], pts[k], pts[k + 1])
            if best is None or d < best[0]:
                best = (d, pts[k], pts[k + 1])
    if best is None or best[0] > 40:
        return False  # torii not on a street - no clear approach axis
    a, b = best[1], best[2]
    ln = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    ux, uy = (b[0] - a[0]) / ln, (b[1] - a[1]) / ln
    if ux * (r["x"] - tc[0]) + uy * (r["y"] - tc[1]) > 0:  # point the axis AWAY from the temple
        ux, uy = -ux, -uy
    far = max(grp, key=lambda t: ux * t[0] + uy * t[1])
    px, py = far[0] + ux * pitch, far[1] + uy * pitch
    if not (0 <= px <= Wd and 0 <= py <= Hd):
        return False
    if w and not point_in_poly(px, py, w):
        return False
    if any(point_in_poly(px, py, f["outline"]) for f in M.get("fields", [])):
        return False
    # a building within ~a street's frontage distance of the slot means the approach is already a
    # built-up residential street there (houses LINE it, beside the avenue) - the torii avenue ends
    # where the frontage begins, so this is NOT open room. A bigger gap = genuinely open ground.
    CLR = 32
    return not any(abs(bd["x"] - px) < bd["w"] / 2 + CLR and abs(bd["y"] - py) < bd["h"] / 2 + CLR for bd in M.get("buildings", []) + M.get("houses", []))


DEFAULT_MANIFEST: Manifest = {
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
    "town_streets": [],
    "gate_structs": [],
    "pond": None,
    "hill": None,
    "summit": None,
    "shrine": None,
    "forest": None,
    "storehouses": [],
    "flophouses": [],
    "road": None,
    "wall": None,
    "gate": None,
    "gates": [],
    "moat": None,
    "governor_mansion": None,
    "ministries": [],
    "inspection_stations": [],
    "theater_stage": None,
    "granary": None,
    "wells": [],
    "threshing_yards": [],
    "gardens": [],
    "groves": [],
    "fire_towers": [],
    "village_groves": [],
    "commons": [],
    "dry_plots": [],
    "marshes": [],
    "title": None,
    "meta": {},
}


# a building's role for the population/frontage maths. A DWELLING houses one ~5-person household;
# a BUSINESS is a commercial frontage (the merchant's house+shop is BOTH - dual-use); everything
# else (civic, government, granary kura, barns, gate furniture) houses no one and fronts nothing.
DWELLING_KINDS = {
    "laborer",
    "laborer_large",
    "servant",
    "burakumin",
    "samurai",
    "samurai_large",
    "merchant",
    "merchant_house",
    "merchant_large",
}  # samurai_large was missing (a senior samurai house is a dwelling like every other _large variant) - found when Tango's population count kept landing 5 short of its generator's
BUSINESS_KINDS = {"shop", "merchant"}
HOUSEHOLD = 5
# COMMONER dwellings must shelter INSIDE a walled city (feature 006). In imperial-Chinese and
# Japanese practice the ordinary working population (laborers, artisans, most shopkeepers) lived
# intramurally - the wall's whole purpose is to protect them - while only four categories sat
# legitimately outside: elite country estates, farmhouses, the riverside wharf suburb, and the
# gate/approach-road (guan-xiang) market. So a commoner dwelling outside the wall is the true
# anomaly (it defeats the wall and has no economic anchor) and is flagged hard-zero; samurai are
# NOT commoners (their country seats are a legitimate extramural category).
COMMONER_KINDS = {"laborer", "laborer_large", "servant", "burakumin", "merchant", "merchant_house", "merchant_large"}
EXTRAMURAL_COMMONER_MAX = 0  # GM decision (FR-002): hard zero, no allowance the generator can drift into


def lane_near_misses(M: Manifest, maxgap: float = 80.0, eps: float = 4.0, align: float = 0.80, block: float = 18.0) -> list[tuple[int, int, int]]:
    """Endpoints of one lane (street/alley) that HEAD STRAIGHT TOWARD another lane and stop just short
    with a CLEAR path between - two lanes pointing at each other that don't meet, which should simply
    connect. Returns [(x, y, gap), ...], one entry per offending endpoint. Filters out: an endpoint that
    already meets a lane or the (wide) road (a junction/corner, not a dangling end); an end that does not
    point toward the other lane (within ~37 deg); and a gap something genuinely BLOCKS - a building, a
    ward fence, or the city wall - since then stopping short is intentional (the lane routes around it)."""
    lanes = [st["pts"] for st in M.get("town_streets", [])] + [(al["pts"] if isinstance(al, dict) else al) for al in M.get("alleys", [])]
    rd = M.get("road")
    bld = [(b["x"], b["y"]) for b in M.get("buildings", [])] + [(h["x"], h["y"]) for h in M.get("houses", [])]
    fences = [wd["boundary"] for wd in M.get("wards", [])]
    wall = M.get("wall") or []

    def to_lane(p: Pt, pts: Poly) -> tuple[tuple[float, float], float]:
        best, bd = (0.0, 0.0), 1e9
        for k in range(len(pts) - 1):
            cx, cy = seg_closest(p[0], p[1], pts[k], pts[k + 1])
            dd = math.hypot(p[0] - cx, p[1] - cy)
            if dd < bd:
                bd, best = dd, (cx, cy)
        return best, bd

    def blocked(a: Pt, b: Pt) -> bool:
        if any(seg_dist(bx, by, a, b) < block for bx, by in bld):
            return True
        if any(segments_cross(a, b, fb[k], fb[k + 1]) for fb in fences for k in range(len(fb) - 1)):
            return True
        return len(wall) >= 3 and any(segments_cross(a, b, wall[k], wall[(k + 1) % len(wall)]) for k in range(len(wall)))

    hits = []
    for i, pi in enumerate(lanes):
        for E, nb in ((pi[0], pi[1]), (pi[-1], pi[-2])):
            if rd and to_lane(E, rd)[1] < 30:  # bed-overlaps the wide road
                continue
            if any(to_lane(E, c)[1] < eps for c in lanes if c is not pi):  # already a junction/corner
                continue
            for j, pj in enumerate(lanes):
                if j == i:
                    continue
                cp, g = to_lane(E, pj)
                if not (eps < g < maxgap):
                    continue
                dl = math.hypot(E[0] - nb[0], E[1] - nb[1]) or 1.0
                if (((E[0] - nb[0]) / dl) * (cp[0] - E[0]) + ((E[1] - nb[1]) / dl) * (cp[1] - E[1])) / g < align:
                    continue  # E is not heading toward pj
                if blocked(E, cp):
                    continue
                hits.append((round(E[0]), round(E[1]), round(g)))
                break
    return hits


def lane_ward_shortfalls(M: Manifest, maxgap: float = 60.0, eps: float = 6.0, align: float = 0.80, block: float = 18.0, gate_dist: float = 34.0) -> list[tuple[int, int, str]]:
    """Lane (street/alley) endpoints that head toward a NEIGHBORHOOD wall (a ward fence) but either
    stop short of it or reach it without a gate. Such a lane should extend to the fence and END AT A
    KIDO GATE (so e.g. laborers can pass through to work in the samurai quarter). Returns
    [(x, y, reason), ...]. The MAIN city wall is NOT a target - a lane may stop short of the outer
    rampart (the city's own boundary); only INTERNAL neighborhood fences pull a lane in to a gate."""
    fences = [wd["boundary"] for wd in M.get("wards", [])]
    if not fences:
        return []
    lanes = [st["pts"] for st in M.get("town_streets", [])] + [(al["pts"] if isinstance(al, dict) else al) for al in M.get("alleys", [])]
    kido = M.get("kido", [])
    wall = M.get("wall") or []
    bld = [(b["x"], b["y"]) for b in M.get("buildings", [])] + [(h["x"], h["y"]) for h in M.get("houses", [])]
    # an INTERIOR anchor (the governor's yamen, else the fences' centroid): a lane endpoint on the same
    # side of the fence as the anchor is INSIDE the ward (an internal government/samurai lane), which
    # needs no entry gate - only the COMMONER lanes approaching from OUTSIDE the fence are pulled in.
    gov = M.get("governor_mansion")
    if gov:
        anchor = (gov["x"], gov["y"])
    else:
        fpts = [p for fb in fences for p in fb]
        anchor = (sum(p[0] for p in fpts) / len(fpts), sum(p[1] for p in fpts) / len(fpts))

    def to_fence(p: Pt, pts: Poly) -> tuple[tuple[float, float], float, tuple[Any, Any]]:
        best, bd, bseg = (0.0, 0.0), 1e9, (pts[0], pts[1])
        for k in range(len(pts) - 1):
            cx, cy = seg_closest(p[0], p[1], pts[k], pts[k + 1])
            dd = math.hypot(p[0] - cx, p[1] - cy)
            if dd < bd:
                bd, best, bseg = dd, (cx, cy), (pts[k], pts[k + 1])
        return best, bd, bseg

    def side(p: Pt, a: Pt, b: Pt) -> float:
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])

    hits = []
    for pi in lanes:
        for E, nb in ((pi[0], pi[1]), (pi[-1], pi[-2])):
            for fb in fences:
                cp, g, seg = to_fence(E, fb)
                if g >= maxgap:
                    continue
                if side(E, *seg) * side(anchor, *seg) > 0:  # E is INSIDE the ward (an internal lane)
                    continue
                dl = math.hypot(E[0] - nb[0], E[1] - nb[1]) or 1.0
                toward = (((E[0] - nb[0]) / dl) * (cp[0] - E[0]) + ((E[1] - nb[1]) / dl) * (cp[1] - E[1])) / max(g, 1e-6)
                if g > eps and toward < align:  # not heading at the fence -> a passer-by, not an entry
                    continue
                if any(seg_dist(bx, by, E, cp) < block for bx, by in bld):
                    continue  # a building blocks the way -> the stop is intentional
                if len(wall) >= 3 and any(segments_cross(E, cp, wall[k], wall[(k + 1) % len(wall)]) for k in range(len(wall))):
                    continue  # the main rampart is between them
                if g > eps:
                    hits.append((round(E[0]), round(E[1]), "stops short of the neighborhood wall - extend it to the fence and end at a kido gate"))
                elif not any(math.hypot(E[0] - gt["x"], E[1] - gt["y"]) < gate_dist for gt in kido):
                    hits.append((round(E[0]), round(E[1]), "meets the neighborhood wall but has no kido gate there"))
                break
    return hits


def _fronts_route(bx: float, by: float, routes: Sequence[Poly], others: Sequence[dict[str, Any]], road_d: float = 115) -> bool:
    """True if (bx, by) is within road_d of a trade route (the Imperial road or a town street) AND no
    `others` building lies between it and the nearest route point - i.e. it FRONTS the road, not hides
    behind the shop rows. Used to keep the caravan inn on the road, not buried in the back blocks."""
    npt, bd = None, 1e18
    for r in routes:
        for k in range(len(r) - 1):
            cx, cy = seg_closest(bx, by, r[k], r[k + 1])
            d = math.hypot(cx - bx, cy - by)
            if d < bd:
                bd, npt = d, (cx, cy)
    if npt is None or bd > road_d:
        return False
    for o in others:
        oc = rect_corners(_struct_rect(o))
        if any(segments_cross((bx, by), npt, oc[e], oc[(e + 1) % 4]) for e in range(4)):
            return False
    return True


# ---- SOFT ADVISORY: crop-limiting relocatable singleton ------------------------------------------------
# The crop-hard feature kinds that DRIVE crop_to_content's frame (the village/hamlet subset of
# settlement._CROP_HARD; the fields' vis_bbox + the pond are added specially, exactly as the crop does).
_CROP_DRIVERS = ("houses", "gardens", "threshing_yards", "village_groves", "groves", "dry_plots", "manors", "religious", "shrines", "farm_sheds", "wells", "cemeteries", "torii")
# discrete placed features a single move could freely RELOCATE (NOT the contiguous house/field/grove fabric).
# The outlying irrigation POND is the archetype; the rest are included so the detector is general and filtered
# by the conditions (terrain-anchor, threshold, empty-landing), not hard-coded away.
_RELOCATABLE = ("pond", "cemeteries", "religious", "shrines", "manors")


def _adv_bbox(o: Any) -> tuple[float, float, float, float]:
    """(x0,y0,x1,y1) of a feature: a torii list [x,y,z], a poly dict, a w/h dict, or a well radius dict."""
    if isinstance(o, (list, tuple)):
        return (o[0] - 19, o[1] - 10, o[0] + 19, o[1] + 18)  # torii arch box
    if o.get("poly"):
        xs = [p[0] for p in o["poly"]]
        ys = [p[1] for p in o["poly"]]
        return (min(xs), min(ys), max(xs), max(ys))
    if "w" in o and "h" in o:
        return (o["x"] - o["w"] / 2, o["y"] - o["h"] / 2, o["x"] + o["w"] / 2, o["y"] + o["h"] / 2)
    return (o["x"] - o["r"], o["y"] - o["r"], o["x"] + o["r"], o["y"] + o["r"])  # a well


def _pond_bbox(M: Manifest) -> tuple[float, float, float, float]:
    c = M["pond"]
    return (c[0] - c[2], c[1] - c[3], c[0] + c[2], c[1] + c[3])


def _norm_skip(skip: Any) -> frozenset[tuple[str, int]]:
    """Normalize `skip` to a SET of (kind, i) members: None -> {}, else the given iterable of members (so a
    whole GROUP - a shrine + its churchyard + well - can be skipped at once, not just a single feature)."""
    return frozenset(skip) if skip else frozenset()


def _member_bbox(M: Manifest, member: tuple[str, int]) -> tuple[float, float, float, float]:
    """The bbox of one crop-driver member (kind, i) - the pond, a torii list, or a w/h / poly / well dict."""
    k, i = member
    return _pond_bbox(M) if k == "pond" else _adv_bbox(M[k][i])


def _crop_frame_boxes(M: Manifest, skip: Any = None) -> list[tuple[float, ...]]:
    """The bboxes that DRIVE the crop frame (crop-hard kinds + fields' visible extent + pond), minus `skip`
    (a single member OR a set of them - a whole relocatable GROUP)."""
    skip = _norm_skip(skip)
    B: list[tuple[float, ...]] = []
    for k in _CROP_DRIVERS:
        for i, o in enumerate(M.get(k) or []):
            if (k, i) not in skip:
                B.append(_adv_bbox(o))
    for fd in M.get("fields") or []:
        vb = fd.get("vis_bbox")
        B.append(tuple(vb) if vb else _adv_bbox({"poly": fd["outline"]}))
    if M.get("pond") and ("pond", 0) not in skip:
        B.append(_pond_bbox(M))
    return B


def _solid_occupancy(M: Manifest, skip: Any = None) -> list[tuple[float, ...]]:
    """Everything a relocated feature must AVOID: the frame drivers + fields + forest + marsh + hill. The
    COMMONS scrub is deliberately excluded - it is sparse grazing waste a pond/feature can simply replace.
    (Marsh IS included: a shrine/graveyard landing must be DRY.) `skip` may be a single member or a group."""
    B = _crop_frame_boxes(M, skip)
    for k in ("forest", "marshes"):
        for o in M.get(k) or []:
            B.append(_adv_bbox(o))
    if M.get("hill"):
        h = M["hill"]
        B.append((h[0] - h[2], h[1] - h[3], h[0] + h[2], h[1] + h[3]))
    return B


def _bbox_frame(B: Sequence[Sequence[float]], m: float = 30) -> tuple[float, float, float, float]:
    return (min(b[0] for b in B) - m, min(b[1] for b in B) - m, max(b[2] for b in B) + m, max(b[3] for b in B) + m)


def _shrine_group(M: Manifest, i: int) -> set[tuple[str, int]]:
    """The set of members that move AS ONE with the shrine at religious[i]: the shrine itself, the graveyard
    it is responsible for (a cemetery within ~300px), its ablution well (~150px), and its torii (~140px). A
    village shrine and its churchyard are a single sacred precinct - you relocate the whole precinct, not the
    altar alone - so the crop advisory must weigh them together, not one at a time. See settlements.md."""
    sh = M["religious"][i]
    sx, sy = sh["x"], sh["y"]
    members = {("religious", i)}
    # the SAME shrine is mirrored into the geometric `shrines` list (parallel footprint records); the mirror
    # is also a crop-driver, so the group must carry it too or the copy left behind still pins the crop edge.
    for j, s in enumerate(M.get("shrines") or []):
        if abs(s["x"] - sx) <= 1 and abs(s["y"] - sy) <= 1:
            members.add(("shrines", j))
    for j, cm in enumerate(M.get("cemeteries") or []):
        if math.hypot(cm["x"] - sx, cm["y"] - sy) <= 300:
            members.add(("cemeteries", j))
    for j, wl in enumerate(M.get("wells") or []):
        if math.hypot(wl["x"] - sx, wl["y"] - sy) <= 150:
            members.add(("wells", j))
    for j, t in enumerate(M.get("torii") or []):
        if math.hypot(t[0] - sx, t[1] - sy) <= 140:
            members.add(("torii", j))
    return members


def crop_relocatable_singletons(M: Manifest, min_shrink: float = 150, clear: float = 20) -> list[dict[str, Any]]:
    """SOFT ADVISORY (never a gate failure): find a relocatable CANDIDATE that ALONE holds a crop_to_content
    edge out by >= `min_shrink` px, AND for which an EMPTY landing (clear of all SOLID occupancy) exists INSIDE
    the tighter frame - so moving it would let the image crop significantly smaller without disturbing anything
    else. A candidate is either (a) a single freely-relocatable feature (the archetype: an outlying irrigation
    POND), or (b) a GROUP that moves as one unit - a village SHRINE together with its churchyard GRAVEYARD (and
    its ablution well + torii). The group case matters because removing the shrine ALONE leaves the graveyard
    holding the same crop corner (and vice versa), so neither reads as relocatable singly - only weighed
    together does the precinct free the corner. Only applies to a village/hamlet that crops to content
    (`meta.view`). Returns a list of {kind, at, edge, shrink, landing, members}; empty when nothing qualifies.
    See settlements.md 'Crop advisory'."""
    meta = M.get("meta", {})
    if meta.get("scale") not in ("village", "hamlet") or not meta.get("view"):
        return []
    full_boxes = _crop_frame_boxes(M)
    if not full_boxes:
        return []
    full = _bbox_frame(full_boxes)
    hill = M.get("hill")
    out: list[dict[str, Any]] = []
    # a pond WIRED TO THE FIELD's water is hydrologically anchored (like a hill-shrine), NOT relocatable: a
    # SOURCE pond (a channel frm=pond -> to=field) belongs UPHILL of the field, so moving it "into the frame"
    # would drop it below the water-entry (backwards for a gravity feed); a DRAINAGE pond (frm=drain -> to=pond)
    # belongs at the low foot BELOW the field, so it must poke past the low crop corner. Either way its poke is
    # intrinsic - the fix is to NUDGE it flush, not move it. (A standalone/decorative pond with no field wiring
    # stays a candidate.) See settlements.md 'Crop advisory'.
    pond_wired = any(
        (c.get("frm", {}).get("kind") == "pond" and c.get("to", {}).get("kind") == "field") or (c.get("frm", {}).get("kind") == "drain" and c.get("to", {}).get("kind") == "pond")
        for c in M.get("channels", [])
    )
    # cands: each entry is (label, members-frozenset, (ox, oy) primary anchor).
    cands: list[tuple[str, frozenset[tuple[str, int]], tuple[float, float]]] = []
    if M.get("pond") and not pond_wired:
        cands.append(("pond", frozenset({("pond", 0)}), (M["pond"][0], M["pond"][1])))
    for k in _RELOCATABLE:
        if k == "pond":
            continue
        for i, o in enumerate(M.get(k) or []):
            cands.append((k, frozenset({(k, i)}), (o["x"], o["y"])))
    # GROUP candidates: a shrine + its churchyard graveyard (+ well + torii) as one movable precinct. Only a
    # shrine with a real COMPANION (a graveyard/well/torii) is a group - a bare shrine (plus its own `shrines`
    # mirror record, which always pairs) is just the singleton already considered above.
    for i, sh in enumerate(M.get("religious") or []):
        gmem = _shrine_group(M, i)
        if any(m[0] in ("cemeteries", "wells", "torii") for m in gmem):
            cands.append(("shrine+churchyard", frozenset(gmem), (sh["x"], sh["y"])))
    for kind, members, (ox, oy) in cands:
        without = _crop_frame_boxes(M, members)
        if not without:
            continue
        f2 = _bbox_frame(without)
        edges = {"W": f2[0] - full[0], "N": f2[1] - full[1], "E": full[2] - f2[2], "S": full[3] - f2[3]}
        shrink = max(edges.values())
        if shrink < min_shrink:
            continue
        is_pond = ("pond", 0) in members
        if hill and not is_pond and in_ellipse(ox, oy, hill):
            continue  # terrain-anchored (a hill-shrine can't move to flat ground)
        mb = [_member_bbox(M, m) for m in members]  # the group's COMBINED footprint moves as one rigid unit
        w = max(b[2] for b in mb) - min(b[0] for b in mb)
        h = max(b[3] for b in mb) - min(b[1] for b in mb)
        occ = _solid_occupancy(M, members)
        tb = _bbox_frame(without, 0)  # the TIGHTER content bbox - land here and the crop tightens
        landing = None  # (a feature wider/taller than tb never enters the loops -> stays None)
        gy = tb[1] + h / 2
        while gy <= tb[3] - h / 2 and landing is None:
            gx = tb[0] + w / 2
            while gx <= tb[2] - w / 2:
                if not any(gx - w / 2 < b[2] + clear and b[0] < gx + w / 2 + clear and gy - h / 2 < b[3] + clear and b[1] < gy + h / 2 + clear for b in occ):
                    landing = (round(gx), round(gy))
                    break
                gx += 25
            gy += 25
        if landing is None:
            continue
        out.append({"kind": kind, "at": (round(ox), round(oy)), "edge": max(edges, key=lambda e: edges[e]), "shrink": round(shrink), "landing": landing, "members": len(members)})
    return out


# canonical residential DENSITY: dwellings per px^2 of residential-capable ground (interior minus
# overhead) that a well-packed provincial-city quarter delivers. Calibrated on Tango, a GM-accepted
# 3,000-person city: 561 placed dwellings on ~378k px^2 of non-overhead, NON-RESERVE interior
# (449,984 res-capable minus the agri reserve's ~72k of non-field slack) = ~1.49/1000.
# Feature-009 recalibration: the original 0.00127 divided by res-capable ground that still
# CONTAINED Tango's agricultural-reserve slack (only non-agri reserves were deducted), so the
# constant under-read what packed urban ground actually delivers - and a no-reserve city
# (Nagahara at its budget-derived ring) was told to 'enlarge' at a density Tango itself packs.
# Reserve ground of ANY kind is committed to non-housing; it must never dilute the density norm.
RHO_CANONICAL = 0.00149

# --- feature 006: per-quarter density + reserve/civic zoning thresholds --------------------
# These are calibrated against Tango (GM-accepted, must pass) AND the pinned pre-feature broken
# Nagahara (pool/regressions/city_density_broken_nagahara.json, must fail); see settlements.md
# "Quarters and per-quarter density" for the recorded why behind each number.
#
# QUARTER_DENSITY band (dwellings per px^2, averaged over a residential/mixed quarter): a commoner
# warren runs ~4-6x denser than a samurai/official ward (Edo: commoners ~50% of population on
# ~20% of land vs samurai ~50% on ~70%; provincial castle towns 4-6x), so the band spans ~5x from
# a low-density samurai ward floor to a packed-warren ceiling. Below the floor reads as a
# half-built quarter; above the ceiling is implausibly crammed. Floor/ceil are provisional here
# and pinned during calibration (T019).
QUARTER_DENSITY_FLOOR = 0.00030  # ~ a legitimately sparse government/samurai ward (Tango's SE reads 0.36/1000 over its non-civic ground; calibrated on Tango)
QUARTER_DENSITY_CEIL = 0.00230  # ~ a packed commoner warren (Tango's NE laborer wedge reads 2.13/1000); ~7.7x the floor, within the 4-8x historical spread
# a residential quarter must not hide a DEAD ZONE: a contiguous empty region larger than a
# firebreak strip. Block-density medians alone cannot separate a good city from a lopsided one
# (Tango and the broken Nagahara share a 4.6/10k median); the discriminator is empty *sub-regions*
# inside a quarter that should be housing. Fire-breaks are thin; a whole empty block is not.
DEAD_ZONE_MAX = 150.0  # px, longest side of an allowed empty pocket in a residential quarter
# a CIVIC precinct (yamen, temple) is legitimately majority-open (roofed halls ~25-45%, courtyards
# and gardens the rest), so tolerate up to ~70% open - but only when the openness is STRUCTURED
# (the quarter actually holds civic compounds); an open-and-structureless "civic" quarter reads as
# merely empty and is flagged.
CIVIC_OPEN_TOL = 0.70
# RESERVE ground (drill ground + gardens + agricultural district) is capped at ~20% of the walled
# interior. Civic *buildings* alone are only ~3-6% of a Chinese county seat; the big open consumer
# is the drill ground plus deliberately under-built garden/farm remainder. ~20% comfortably fits a
# drill ground + gardens + an agricultural district and is historically conservative; beyond it the
# wall encloses more open ground than a provincial seat justifies (read: shrink the wall).
RESERVE_CAP_FRAC = 0.20

# --- feature 009: budget-first wall sizing (specs/009-city-area-budget) ---------------------
# A walled city's wall is DERIVED from a declared space budget (citybudget.plan_city, recorded
# at meta.budget by the gen script BEFORE the wall is drawn); these tolerances bound how far the
# drawn enclosure may drift from that promise, in EITHER direction. Calibrated on the two pinned
# anchors: shipped Tango's enclosure sits ~+0.2% off its budget (must pass) while the pre-feature
# Nagahara - the GM-rejected "too empty" city every other check called green - sits ~+21% (must
# fail, pool/regressions/city_budget_fires_on_the_too_empty_nagahara.json). OVER at 8% leaves
# >2x separation to the known-bad anchor; UNDER is tighter (5%) because an undersized wall
# breaks packing immediately rather than merely reading as sparse.
BUDGET_TOL_OVER = 0.08
BUDGET_TOL_UNDER = 0.05

# --- to-scale gates/walls + funerary features (GM, 2026-07-19) ------------------------------
# Anchors researched 2026-07-19 (full memo in settlements.md "Historical grounding"):
# GATES: a samurai residence gate (nagayamon/yakuimon) opens ~9-12 real ft; a grand yamen
# gatehouse carriage opening runs to ~24 ft. Openings above that (the old fixed +-34px gap =
# 204 ft at city scale) read as a missing wall. WALLS: dobei/tsuijibei ~1.5-2 ft; the 2px
# cartographic floor at 3 ft/px draws 6 ft, so the band top is 8.
GATE_FT_MIN, GATE_FT_MAX = 6.0, 24.0
WALL_FT_MIN, WALL_FT_MAX = 1.0, 8.0
# CREMATION: a village/town sanmai's cleared working core is 30-80 ft across (Fukui sanmai
# survey: ~7 ft hearth, 10-13 ft sheltered structures + bone platform + attendant hut); a
# provincial city justifies ~80-160 ft; the Yoyogi crematory serving metropolitan Edo was ~900
# tsubo (~180 ft square) - the far ceiling, not a template. Floors keep a token dot from
# passing as a crematory.
CREMATION_FT_MIN, CREMATION_FT_MAX_TOWN, CREMATION_FT_MAX_CITY = 25.0, 90.0, 160.0
# OSSUARY: a muenzuka bone mound is typically 10-30 ft across, 3-8 ft high (cremated,
# consolidated bone takes almost no volume - Kozukappara's 100k+ dead never made a great
# mound); Kyoto's monumental state-built Mimizuka is ~50 ft at the base. Band top 60 admits
# the small-glyph legibility floor.
OSSUARY_FT_MIN, OSSUARY_FT_MAX = 8.0, 60.0
# BURIAL GROUNDS (cremation-then-inter culture, aggressive plot reuse, ~1 generation of active
# plots): ~10-20 sq ft per urn-grave packed incl. circulation -> village (~350) 0.1-0.25 ac,
# town (~1,200) 0.25-0.75, city (~3,000) 0.75-2 split across yards. Bands widened a little
# both ways for glyph rounding; the LADDER must stay monotone with population served.
BURIAL_AC_BAND = {"village": (0.04, 0.30), "town": (0.10, 0.80), "city": (0.35, 2.20)}

# --- doors-face-open + rows-max-two-deep (GM, 2026-07-18) -----------------------------------
# The boundary between "an eave/drainage gap" (~3-6 real ft between back-to-back rows - rain
# drip and night-soil access, NOT an entrance) and "walkable entrance ground" (a roji/court at
# >= ~10 real ft). 7 ft sits cleanly between the two bands at every map scale; the checks
# convert it to drawn px via meta.ftpx.
DOOR_CLEAR_FT = 7.0


def city_capacity(M: Manifest, step: float = 8, grid_step: float | None = None) -> dict[str, Any] | None:
    """SPACE-BUDGET ANALYSIS: is the city wall sized to hold its target population?

    Guessing a wall size and then grinding placements is backwards - the honest process is to
    MEASURE. This grid-samples the walled interior (every `step` px), classes each cell as
    dwelling / civic-overhead / water / trunk-circulation / residential-street / field / OPEN,
    reads the density the built residential quarters actually achieve, and projects whether
    filling the OPEN ground would reach the target. Returns a dict with a verdict
    ('enlarge' | 'shrink' | 'densify' | 'sized_and_packed'), the space budget, and a suggested wall SCALE so
    the wall can be resized ONCE to the right size rather than by trial and error. A city WITH
    an agricultural district commits its slack to fields (canon), so field cells are excluded
    from both the residential ground and the wasted-open ground."""
    meta = M.get("meta", {})
    wall = M.get("wall")
    pop = meta.get("population")
    if not wall or not pop:
        return None
    T = pop / 5.0
    bound = M.get("ring_road") or (list(wall) + [wall[0]])
    xs = [p[0] for p in bound]
    ys = [p[1] for p in bound]
    # bound the sweep span so a malformed coordinate (a wall/ring vertex millions of px off) cannot
    # blow the cell + ASCII grid sweeps up to billions of cells and hang the validator (both sweeps
    # below run over x0..x1 / y0..y1); a real map's span is far under sweep_hi's cap.
    x0, x1, y0, y1 = min(xs), sweep_hi(min(xs), max(xs), step), min(ys), sweep_hi(min(ys), max(ys), step)

    def _rects(items: Sequence[dict[str, Any]], vscale: float = 1.0) -> list[list[tuple[float, float]]]:
        out: list[list[tuple[float, float]]] = []
        for it in items:
            if "w" not in it:
                continue
            out.append(rect_corners({"x": it["x"], "y": it["y"], "w": it["w"], "h": it["h"] * vscale, "rot": it.get("rot", 0)}))
        return out

    dwell_r = _rects([b for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS])
    dwell_r += [rect_corners(_struct_rect(h)) for h in M.get("houses", []) if point_in_poly(h["x"], h["y"], wall)]
    civic = (
        M.get("ministries", [])
        + M.get("religious", [])
        + M.get("flophouses", [])
        + M.get("storehouses", [])
        + M.get("cemeteries", [])
        + M.get("mausoleums", [])
        + M.get("merchant_estates", [])
        + M.get("inspection_stations", [])
        + [b for b in M.get("buildings", []) if b.get("kind") in ("shop", "inn", "stables")]
        + ([M["governor_mansion"]] if M.get("governor_mansion") else [])
        + M.get("docks", [])
    )
    civic_r = _rects(civic)
    ts = M.get("theater_stage")
    if ts:
        civic_r.append(rect_corners({"x": ts["x"], "y": ts["y"], "w": ts["w"], "h": ts["h"] * 1.3, "rot": ts.get("rot", 0)}))
    field_polys = [f["outline"] for f in M.get("fields", []) if point_in_poly((f["bbox"][0] + f["bbox"][2]) / 2, (f["bbox"][1] + f["bbox"][3]) / 2, wall)]
    field_polys += [dp["poly"] for dp in M.get("dry_plots", []) if point_in_poly(dp["poly"][0][0], dp["poly"][0][1], wall)]
    water = ([(M["moat"], M.get("moat_width", 22) / 2)] if M.get("moat") else []) + [(cc["poly"], cc.get("w", 12) / 2) for cc in M.get("canals", [])]
    trunk = [(M["road"], M.get("road_width", 26) / 2)] if M.get("road") else []
    trunk += [(r["pts"], r["w"] / 2) for r in M.get("roads", [])]
    if M.get("ring_road"):
        trunk.append((M["ring_road"], M.get("ring_road_width", 15) / 2 + 24))
    res_st = [(s["pts"], s.get("w", 12) / 2) for s in M.get("town_streets", [])] + [(a["pts"], a.get("w", 8) / 2) for a in M.get("alleys", [])]

    # PERFORMANCE: the sweeps below sample ~40k grid points on a provincial city, and the naive
    # form probed every dwelling/civic rect, field poly, and street segment from every point -
    # ~23M point_in_poly/seg_dist calls, ~13s per gate run (profiled on Tango, 2026-07-20), paid
    # on every in-session map iteration and every city regression fixture. The features are tiny
    # relative to the walled span, so index them into coarse spatial bins and test each sample
    # point only against the features whose bounding box overlaps its bin. The classification is
    # IDENTICAL to the naive sweep: same sample points, same predicates in the same priority
    # order, and the bin prefilter is conservative (a poly lies inside its bbox; a "within hw of
    # segment" capsule lies inside the segment bbox inflated by hw), so no true hit is skipped.
    BIN = step * 8

    def _bucket_polys(polys: Sequence[Poly]) -> dict[tuple[int, int], list[Poly]]:
        out: dict[tuple[int, int], list[Poly]] = {}
        for p in polys:
            pxs = [q[0] for q in p]
            pys = [q[1] for q in p]
            for bx in range(int(min(pxs) // BIN), int(max(pxs) // BIN) + 1):
                for by in range(int(min(pys) // BIN), int(max(pys) // BIN) + 1):
                    out.setdefault((bx, by), []).append(p)
        return out

    def _bucket_lines(lines: Sequence[tuple[Poly, float]]) -> dict[tuple[int, int], list[tuple[Pt, Pt, float]]]:
        out: dict[tuple[int, int], list[tuple[Pt, Pt, float]]] = {}
        for pts, hw in lines:
            for k in range(len(pts) - 1):
                a, b = pts[k], pts[k + 1]
                for bx in range(int((min(a[0], b[0]) - hw) // BIN), int((max(a[0], b[0]) + hw) // BIN) + 1):
                    for by in range(int((min(a[1], b[1]) - hw) // BIN), int((max(a[1], b[1]) + hw) // BIN) + 1):
                        out.setdefault((bx, by), []).append((a, b, hw))
        return out

    dwell_bk, civic_bk, field_bk = _bucket_polys(dwell_r), _bucket_polys(civic_r), _bucket_polys(field_polys)
    water_bk, trunk_bk, res_bk = _bucket_lines(water), _bucket_lines(trunk), _bucket_lines(res_st)
    pond = M.get("pond")

    def _classify(gx: float, gy: float) -> str:
        """Class one sample point: 'outside' the wall, else the first matching ground category
        in the fixed priority order. Shared by the count sweep and the ASCII-map sweep so the
        two can never disagree."""
        b = (int(gx // BIN), int(gy // BIN))
        if not point_in_poly(gx, gy, wall):
            return "outside"
        if any(point_in_poly(gx, gy, r) for r in dwell_bk.get(b, [])):
            return "dwell"
        if any(point_in_poly(gx, gy, r) for r in civic_bk.get(b, [])):
            return "civic"
        if (pond and in_ellipse(gx, gy, pond)) or any(seg_dist(gx, gy, a, bb) < hw for a, bb, hw in water_bk.get(b, [])):
            return "water"
        if any(point_in_poly(gx, gy, p) for p in field_bk.get(b, [])):
            return "field"
        if any(seg_dist(gx, gy, a, bb) < hw for a, bb, hw in trunk_bk.get(b, [])):
            return "trunk"
        if any(seg_dist(gx, gy, a, bb) < hw for a, bb, hw in res_bk.get(b, [])):
            return "res_st"
        return "open"

    c = {"dwell": 0, "civic": 0, "water": 0, "trunk": 0, "res_st": 0, "field": 0, "open": 0}
    gx = x0
    while gx <= x1:
        gy = y0
        while gy <= y1:
            kind = _classify(gx, gy)
            if kind != "outside":
                c[kind] += 1
            gy += step
        gx += step
    cell = step * step
    A = {k: v * cell for k, v in c.items()}
    ring_area = sum(A.values()) or 1
    # OPTIONAL coarse ASCII map of the interior classification, so the report shows WHERE the
    # open ground is (not just how much) - the operator can then aim new quarters at it rather
    # than guess. Reuses the rects/lines already built above; a second coarse sweep is cheap.
    grid_rows = None
    if grid_step:
        _sym = {"outside": " ", "dwell": "D", "civic": "C", "water": "~", "trunk": "#", "res_st": "+", "field": "F", "open": "."}
        grid_rows = []
        gy = y0
        while gy <= y1:
            row = []
            gx = x0
            while gx <= x1:
                row.append(_sym[_classify(gx, gy)])
                gx += grid_step
            grid_rows.append("".join(row))
            gy += grid_step
    # PLACED dwellings: for a walled city only those INSIDE the wall count (feature 006 - the
    # extramural spill must not inflate the figure); in-wall farmhouses count too.
    D = len([b for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS and point_in_poly(b["x"], b["y"], wall)]) + sum(1 for h in M.get("houses", []) if point_in_poly(h["x"], h["y"], wall))
    # residential-CAPABLE ground = the interior minus the fixed overhead (government + temples +
    # wharf/dock/gates/shops, water, trunk roads + ring road + wall berm, committed field ground) -
    # the per-cell classification already excludes civic buildings, water, trunk, and fields (an
    # agricultural-district reserve draws as fields, so it is already out). A drill-ground / garden
    # reserve draws as OPEN, so subtract those declared reserves explicitly (feature 006): they are
    # committed to non-housing and must not count toward what the wall can house.
    quarters = M.get("quarters", [])
    civic_q = sum(poly_area(q["poly"]) for q in quarters if q.get("zone") == "civic")
    reserve_q = sum(poly_area(q["poly"]) for q in quarters if q.get("zone") == "reserve")
    # ALL reserve ground is committed to non-housing and must not count toward what the wall can
    # house. An agricultural district draws mostly as FIELDS - those cells are already classed out -
    # so deduct only its non-field remainder (farmhouse yards, groves, margins between combs).
    # (Feature 009: the earlier deduction skipped agricultural reserves entirely, leaving ~72k px^2
    # of Tango's reserve slack inside res_capable and diluting RHO_CANONICAL - see its comment.)
    reserve_deduct = max(reserve_q - A["field"], 0.0)
    reserve_frac = reserve_q / ring_area
    overhead = A["civic"] + A["water"] + A["trunk"] + A["field"]
    res_capable = max(A["dwell"] + A["res_st"] + A["open"] - reserve_deduct, 1)  # everything that could be residential
    inherent_cap = res_capable * RHO_CANONICAL  # dwellings the wall CAN hold, well-packed
    open_frac = A["open"] / ring_area
    # size the wall so its residential-capable ground holds T at the canonical density (+5% slack).
    need_res = (T / RHO_CANONICAL) * 1.05
    scale = math.sqrt((ring_area - res_capable + need_res) / ring_area)
    # per-quarter density (residential + mixed), measured over non-civic ground - the report the
    # operator reads to see WHICH quarter is under-built, not just the city-wide total.
    per_quarter = []
    if quarters:
        civ_rects = [
            _struct_rect(cc)
            for cc in (
                M.get("ministries", [])
                + M.get("religious", [])
                + M.get("cemeteries", [])
                + M.get("mausoleums", [])
                + M.get("storehouses", [])
                + ([M["governor_mansion"]] if M.get("governor_mansion") else [])
            )
            if "w" in cc
        ]
        dpts = [(b["x"], b["y"]) for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS and point_in_poly(b["x"], b["y"], wall)]
        for q in quarters:
            if q.get("zone") not in ("residential", "mixed"):
                continue
            qa = poly_area(q["poly"])
            cf = sum(r["w"] * r["h"] for r in civ_rects if point_in_poly(r["x"], r["y"], q["poly"]))
            nq = sum(1 for x, y in dpts if point_in_poly(x, y, q["poly"]))
            per_quarter.append({"name": q.get("name"), "zone": q["zone"], "dwellings": nq, "density": round(nq / max(qa - cf, 1), 5)})
    # VERDICT -> one clear ACTION (feature 006 rename of the earlier too_small/too_big/underpacked/
    # about_right). The densify boundary tracks population_tol so the capacity verdict and the
    # population check never disagree; a wall fillable only by OVER-CAP reserve reads as shrink
    # (emptiness cannot be laundered as reserve).
    pop_tol = meta.get("population_tol", 0.07)
    if inherent_cap < 0.9 * T:
        verdict = "enlarge"  # even well-packed the wall cannot hold T
    elif inherent_cap > 1.4 * T or reserve_frac > RESERVE_CAP_FRAC:
        verdict = "shrink"  # far more room than T needs (or only fillable via over-cap reserve)
    elif (1 - pop_tol) * T > D:
        verdict = "densify"  # the WALL is right; the placement is too sparse
    else:
        verdict = "sized_and_packed"
    return {
        "verdict": verdict,
        "target_dwellings": round(T),
        "placed": D,
        "inherent_capacity": round(inherent_cap),
        "ring_area": round(ring_area),
        "res_capable_area": round(res_capable),
        "overhead_area": round(overhead),
        "civic_area": round(civic_q),
        "reserve_area": round(reserve_q),
        "reserve_frac": round(reserve_frac, 3),
        "open_frac": round(open_frac, 3),
        "suggested_wall_scale": round(scale, 3),
        "areas": {k: round(v) for k, v in A.items()},
        "per_quarter": per_quarter,
        "grid": grid_rows,
        "grid_origin": (round(x0), round(y0)),
        "grid_step": grid_step,
    }


def gate(M: Manifest, verbose: bool = True) -> list[str]:
    """Run every check over a manifest dict M and return the list of FAILED check names.
    verbose prints the PASS/FAIL lines. Pass a synthetic M to unit-test a single check."""
    # tolerate sparse synthetic manifests (unit tests build only the keys a check needs)
    M = {**DEFAULT_MANIFEST, **M}
    meta = M.get("meta", {})
    scale = meta.get("scale", "village")
    houses, fields = M["houses"], M["fields"]
    field_by = {f["name"]: f for f in fields}
    Wd, Hd = meta.get("W", 1820), meta.get("H", 1180)
    # the "map edge" is the rendered window: the cropped view if one is set (city maps crop tight
    # to the walls and let the countryside run off), else the full canvas.
    _vw = meta.get("view")
    EX0, EY0, EX1, EY1 = (_vw[0], _vw[1], _vw[0] + _vw[2], _vw[1] + _vw[3]) if _vw else (0, 0, Wd, Hd)
    fails: list[str] = []

    def check(name: str, ok: Any, detail: str = "") -> None:
        if verbose:
            print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"  -> {detail}"))
        if not ok:
            fails.append(name)

    # Every HARD feature the frame is meant to CONTAIN must actually lie INSIDE the rendered window. A deferred
    # feature placed AFTER crop_to_content - a set-apart back-slope graveyard, an outlying shrine, the wells -
    # can land outside the tight frame and be silently CLIPPED (caught the Ueda west graveyard, which the crop
    # never framed because it was drawn after the crop). Scoped to the crop-to-content scales; a town/city is
    # framed bespoke (tight to walls, fields run off-edge) so its "off-frame is intentional" is not a bug here.
    if scale in ("hamlet", "village") and _vw:
        # the village/hamlet hard features (a town/city carries urban/funerary kinds recorded as lists that this
        # per-scale check does not model). Each carries EITHER a torii list [x,y,z], a `poly`, a well `r`, or w/h.
        _HARD_IN_FRAME = ("houses", "gardens", "threshing_yards", "village_groves", "groves", "dry_plots", "manors", "religious", "shrines", "farm_sheds", "wells", "cemeteries", "torii")
        clipped = []
        for k in _HARD_IN_FRAME:
            for o in M.get(k, []):
                if k == "torii":  # recorded [x, y, z]; arch spans x +/-19, y -10..+18
                    fx0, fy0, fx1, fy1 = o[0] - 19, o[1] - 10, o[0] + 19, o[1] + 18
                elif o.get("poly"):
                    xs = [p[0] for p in o["poly"]]
                    ys = [p[1] for p in o["poly"]]
                    fx0, fy0, fx1, fy1 = min(xs), min(ys), max(xs), max(ys)
                elif "r" in o:  # a well carries a radius, not w/h
                    fx0, fy0, fx1, fy1 = o["x"] - o["r"], o["y"] - o["r"], o["x"] + o["r"], o["y"] + o["r"]
                else:  # every other hard feature carries w/h
                    fx0, fy0, fx1, fy1 = o["x"] - o["w"] / 2, o["y"] - o["h"] / 2, o["x"] + o["w"] / 2, o["y"] + o["h"] / 2
                if fx0 < EX0 - 1 or fy0 < EY0 - 1 or fx1 > EX1 + 1 or fy1 > EY1 + 1:
                    clipped.append((k, round((fx0 + fx1) / 2), round((fy0 + fy1) / 2)))
        check(
            "hard_features_within_frame",
            not clipped,
            f"{len(clipped)} hard feature(s) run OUTSIDE the cropped frame and get clipped: {clipped[:4]} - a "
            f"feature the frame must contain (esp. a set-apart graveyard/shrine placed AFTER crop_to_content) "
            f"must sit inside the view; place it BEFORE the crop so the frame includes it",
        )

    # population is DWELLINGS x ~5, NEVER total buildings: a town/city's shops, government
    # offices, flophouses, kura and gate furniture house no one, so counting them as housing
    # would inflate the population. Farmhouses + urban dwellings are the only residences.
    if scale in ("town", "city") and meta.get("population"):
        # a CITY's declared population (~3,000) is its URBAN castes ONLY - servants, laborers, merchants,
        # burakumin, samurai (budgets.md caste tables list ZERO farmers for a city). FARMERS do not count
        # at all: not the surrounding villagers, and not even the unusual IN-WALL agricultural district's
        # farmers - so a city's farmhouses (M["houses"]) are excluded entirely from the figure. A TOWN's
        # depicted farmhouses ARE its (partial) county farmer cohort, so they DO count there.
        # a WALLED city's people shelter INSIDE the rampart, so only in-wall dwellings count toward
        # the declared figure (feature 006). Counting extramural dwellings too let a generator hit
        # the target by spilling houses into the fields while the interior sat half-empty - the exact
        # leak that passed the broken Nagahara (525 in-wall + 35 spilled = 560 ~ target).
        _wall = M.get("wall")
        if scale == "city" and _wall:
            urban = sum(1 for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS and point_in_poly(b["x"], b["y"], _wall))
        else:
            urban = sum(1 for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS)
        if scale == "city" and meta.get("agricultural_district") and M.get("wall"):
            # the unusual agricultural-district city (Tango's canon deviation) HOUSES its in-wall
            # farmers: they are walled residents and count toward the declared figure - the
            # budgets' zero-farmer assumption is precisely what agricultural_district overrides.
            # Surrounding (extramural) farmhouses still do not count.
            inwall_farms = sum(1 for h in houses if point_in_poly(h["x"], h["y"], M["wall"]))
            dwellings = urban + inwall_farms
        elif scale == "city":
            dwellings = urban
        else:
            dwellings = len(houses) + urban
        est = dwellings * HOUSEHOLD
        pop = meta["population"]
        tol = meta.get("population_tol", 0.07)  # the map should DELIVER the declared figure, not merely be in a wide band
        farm_note = "" if scale == "city" else "farmhouses + "
        check(
            "population_consistent_with_housing",
            abs(est - pop) <= tol * pop,
            f"{dwellings} dwellings x{HOUSEHOLD} = ~{est} residents, but meta population is {pop} "
            f"(>{tol:.0%} off) - count ONLY dwellings ({farm_note}laborer/servant/burakumin/samurai/merchant), "
            f"never the shops, government offices, flophouses, kura, gate furniture{' or any farmhouses (city farmers are not in the ~3,000)' if scale == 'city' else ''}; "
            f"place enough dwellings to hit the declared figure",
        )

    # COMMONER DWELLINGS SHELTER INSIDE THE WALLS (feature 006). A walled city's ordinary
    # population (laborers, artisans, servants, merchants) lived intramurally - the wall exists to
    # protect them. Only four categories sat legitimately outside: samurai country estates,
    # farmhouses, the riverside wharf suburb, and the gate/approach-road (guan-xiang) market shops.
    # So ANY commoner DWELLING outside the wall is the anomaly (it defeats the wall and has no
    # economic anchor); hard-zero. Samurai are exempt (their country seats are a legitimate
    # extramural category); shops are businesses, not dwellings, so they are not in COMMONER_KINDS.
    if scale == "city" and M.get("wall"):
        wall_p = M["wall"]
        outside_com = [(round(b["x"]), round(b["y"])) for b in M.get("buildings", []) if b.get("kind") in COMMONER_KINDS and not point_in_poly(b["x"], b["y"], wall_p)]
        check(
            "city_commoner_dwellings_inside_walls",
            len(outside_com) <= EXTRAMURAL_COMMONER_MAX,
            f"{len(outside_com)} commoner dwelling(s) sit OUTSIDE the walls {sorted(set(outside_com))[:4]} - a walled "
            f"city's commoners shelter inside the rampart; only samurai country estates, farmhouses, the wharf suburb, "
            f"and gate-market shops belong outside. Move these dwellings inside the wall.",
        )

        # DECLARED QUARTERS + PER-QUARTER DENSITY (feature 006). A walled city is a set of zoned
        # quarters tiling its interior; density is judged PER QUARTER (residential/mixed against a
        # band + a dead-zone guard), civic quarters must actually hold civic ground, and reserve
        # ground is capped. This is what a global aggregate could not see: a dense east + empty west
        # averages to "fine" (measured: Tango and the broken Nagahara share the same block-density
        # median; the difference is WHERE the empty ground sits).
        quarters = M.get("quarters", [])
        # a MALFORMED manifest (a wall or quarter vertex millions of px off the map) must FAIL, not
        # hang - the grid sweeps are bounded by sweep_hi so they cannot loop forever, and this flags
        # the bad geometry so the validator reports it instead of silently sweeping garbage. A real
        # settlement's features lie within one canvas-width of margin of the drawn canvas.
        _Wd = meta.get("W") or 3200
        _Hd = meta.get("H") or 2700
        _oob = [(round(vx), round(vy)) for vx, vy in ([tuple(p) for p in wall_p] + [tuple(v) for q in quarters for v in q["poly"]]) if not (-_Wd <= vx <= 2 * _Wd and -_Hd <= vy <= 2 * _Hd)]
        check(
            "city_geometry_within_canvas",
            not _oob,
            f"wall/quarter vertex(es) far outside the canvas ({_Wd}x{_Hd}): {sorted(set(_oob))[:4]} - a coordinate "
            f"millions of px off the map is malformed input; a valid settlement's geometry lies near the drawn canvas",
        )
        check(
            "city_quarters_declared",
            bool(quarters),
            "a walled city must declare its quarters - s.quarter(poly, zone, kind=...) - so density is judged per "
            "quarter, not by a global aggregate a lopsided city can satisfy (a dense half plus an empty half averages fine)",
        )
        if quarters:
            interior_area = poly_area(wall_p)
            dwell_pts = [(b["x"], b["y"]) for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS and point_in_poly(b["x"], b["y"], wall_p)]
            _civic = (
                M.get("ministries", [])
                + M.get("religious", [])
                + M.get("cemeteries", [])
                + M.get("mausoleums", [])
                + M.get("storehouses", [])
                + ([M["governor_mansion"]] if M.get("governor_mansion") else [])
            )
            civic_rects = [_struct_rect(c) for c in _civic if "w" in c]

            # TILING: sweep the wall-plus-quarters bbox once (so a quarter that spills OUTSIDE the
            # wall is sampled too) - quarters must cover the interior (>=85%), not overlap (<=5%),
            # and not spill outside the wall (<=3% of interior-equivalent cells).
            wxs = [p[0] for p in wall_p] + [v[0] for q in quarters for v in q["poly"]]
            wys = [p[1] for p in wall_p] + [v[1] for q in quarters for v in q["poly"]]
            interior_cells = uncovered = overlapped = spill_cells = 0
            _hx = sweep_hi(min(wxs), max(wxs), 40)  # bounded so a malformed vertex cannot hang the sweep
            _hy = sweep_hi(min(wys), max(wys), 40)
            gx = min(wxs)
            while gx <= _hx:
                gy = min(wys)
                while gy <= _hy:
                    n_in = sum(1 for q in quarters if point_in_poly(gx, gy, q["poly"]))
                    if point_in_poly(gx, gy, wall_p):
                        interior_cells += 1
                        if n_in == 0:
                            uncovered += 1
                        elif n_in > 1:
                            overlapped += 1
                    elif n_in >= 1:
                        spill_cells += 1
                    gy += 40
                gx += 40
            ic = max(interior_cells, 1)
            covered = 1 - uncovered / ic
            check(
                "city_quarters_tile_interior",
                covered >= 0.85 and overlapped / ic <= 0.05 and spill_cells / ic <= 0.03,
                f"declared quarters must tile the walled interior without overlap or spill - covered {covered:.0%} "
                f"(need >=85%), overlapped {overlapped / ic:.0%} (<=5%), outside-wall {spill_cells / ic:.0%} (<=3%)",
            )

            # PER-QUARTER DENSITY + DEAD ZONE (residential + mixed quarters)
            thin_q = []
            for q in quarters:
                if q.get("zone") not in ("residential", "mixed"):
                    continue
                qpoly = q["poly"]
                qarea = poly_area(qpoly)
                if qarea <= 0:
                    continue
                qd = [(x, y) for x, y in dwell_pts if point_in_poly(x, y, qpoly)]
                # density is measured over HOUSING-AVAILABLE ground: subtract any civic compound
                # footprint sitting in the quarter (a government ward or a temple in a merchant
                # district eats area that was never going to be housing), so a mixed quarter is not
                # wrongly flagged under-built for the ground its compounds occupy.
                civic_in_q = sum(r["w"] * r["h"] for r in civic_rects if point_in_poly(r["x"], r["y"], qpoly))
                eff_area = max(qarea - civic_in_q, 1.0)
                dens = len(qd) / eff_area
                nm = q.get("name") or f"quarter@({round(sum(p[0] for p in qpoly) / len(qpoly))},{round(sum(p[1] for p in qpoly) / len(qpoly))})"
                if dens < QUARTER_DENSITY_FLOOR:
                    thin_q.append((nm, f"{len(qd)} dwellings, density {dens * 1000:.2f}/1000px^2 < floor {QUARTER_DENSITY_FLOOR * 1000:.2f} (under-built)"))
                elif dens > QUARTER_DENSITY_CEIL:
                    thin_q.append((nm, f"density {dens * 1000:.2f}/1000px^2 > ceil {QUARTER_DENSITY_CEIL * 1000:.2f} (implausibly crammed)"))
                elif (
                    q.get("zone") == "residential"
                    and largest_empty_gap(
                        qpoly, qd + [(w["x"], w["y"]) for w in M.get("wells", []) if point_in_poly(w["x"], w["y"], qpoly)], occupied=[r for r in civic_rects if point_in_poly(r["x"], r["y"], qpoly)]
                    )
                    > DEAD_ZONE_MAX
                ):
                    # the dead-zone guard applies to PURE residential quarters (uniform housing, no
                    # empty blocks); a MIXED quarter legitimately holds a civic forecourt/plaza, so it
                    # is judged on the density AVERAGE only. An all-empty region declared to dodge this
                    # still fails: as residential it fires here, as civic it fires city_civic_quarter,
                    # as mixed its average density is too low.
                    thin_q.append((nm, f"dead zone: an empty pocket wider than a firebreak ({DEAD_ZONE_MAX:.0f}px) inside a residential quarter"))
            check(
                "city_residential_quarters_dense_enough",
                not thin_q,
                f"residential/mixed quarter(s) not evenly built up (per-quarter density band "
                f"[{QUARTER_DENSITY_FLOOR * 1000:.2f}, {QUARTER_DENSITY_CEIL * 1000:.2f}]/1000px^2 + no dead zone): {thin_q[:4]}",
            )

            # CIVIC quarters must actually hold civic ground (not be emptiness labeled civic)
            open_civic = []
            for q in quarters:
                if q.get("zone") != "civic":
                    continue
                qpoly = q["poly"]
                qarea = poly_area(qpoly)
                if qarea <= 0:
                    continue
                built = sum(r["w"] * r["h"] for r in civic_rects if point_in_poly(r["x"], r["y"], qpoly))
                open_share = 1 - min(built / qarea, 1.0)
                if open_share > CIVIC_OPEN_TOL:
                    nm = q.get("name") or "civic quarter"
                    open_civic.append((nm, f"{open_share:.0%} open > {CIVIC_OPEN_TOL:.0%}; holds little civic building"))
            check(
                "city_civic_quarter_not_mostly_open",
                not open_civic,
                f"civic quarter(s) that are mostly empty rather than a real precinct - a yamen/temple precinct is majority-open but STRUCTURED (it holds its compounds); flag: {open_civic[:3]}",
            )

            # RESERVE ground capped
            reserve_area = sum(poly_area(q["poly"]) for q in quarters if q.get("zone") == "reserve")
            rfrac = reserve_area / max(interior_area, 1)
            check(
                "city_reserve_within_cap",
                rfrac <= RESERVE_CAP_FRAC,
                f"declared reserve ground is {rfrac:.0%} of the interior, over the {RESERVE_CAP_FRAC:.0%} cap - "
                f"a wall enclosing this much deliberately-open ground is too big for the residential program (shrink it, "
                f"or convert reserve to housing)",
            )

    # IS THE WALL THE RIGHT SIZE FOR THE POPULATION? A space-budget analysis, so "the wall is
    # too big / too small" becomes a first-class, automated judgment instead of trial and error.
    # city_capacity() grid-samples the interior, subtracts the fixed overhead (government, temples,
    # wharf, gates, water, trunk roads + ring road + berm, committed fields), and asks whether the
    # residential-capable ground - at a well-packed quarter's canonical density - can hold the
    # target. TOO_SMALL / TOO_BIG are WALL faults (resize by the suggested scale); UNDERPACKED means
    # the wall is right but the placement is sparse (densify - population_consistent catches that
    # separately). See settlements.md "Sizing the wall to the population".
    if scale == "city" and meta.get("population"):
        cap = city_capacity(M)
        if cap:
            check(
                "city_wall_sized_to_population",
                cap["verdict"] not in ("enlarge", "shrink"),
                f"the wall wants to {cap['verdict']} for a population of {meta['population']} "
                f"(target {cap['target_dwellings']} dwellings; the ring holds ~{cap['inherent_capacity']} well-packed, "
                f"reserve fraction {cap['reserve_frac']}) - resize the wall by the suggested scale x{cap['suggested_wall_scale']} "
                f"(>1 enlarge, <1 shrink), then re-run; do NOT grind placements against a mis-sized wall",
            )

    # THE WALL MATCHES THE DECLARED SPACE BUDGET (feature 009). Budget-first is the city
    # workflow: the gen computes citybudget.plan_city(...) BEFORE drawing anything, takes the
    # wall from budget.wall, and records the promise at meta.budget - this check holds the
    # drawn map to it. Enclosing MORE ground than the budget justifies is the empty-space
    # defect (the pre-feature Nagahara read fully green while ~17% of its interior was
    # unaccounted open ground); enclosing less starves the program. Open ground is credited
    # only as itemized budget lines (reserve/agri/extras) - never as ambient slack.
    if scale == "city" and meta.get("walled") and M.get("wall"):
        bud = meta.get("budget")
        if not bud:
            check(
                "city_wall_matches_budget",
                False,
                "no space budget declared - a walled city is sized budget-first: compute citybudget.plan_city(program), take the wall from budget.wall, and record s.meta(budget=budget_to_manifest(budget)) (specs/009-city-area-budget)",
            )
        else:
            measured = poly_area(M["wall"])
            req = float(bud["required_interior_px2"])
            bud_over = measured > req * (1 + BUDGET_TOL_OVER)
            bud_under = measured < req * (1 - BUDGET_TOL_UNDER)
            check(
                "city_wall_matches_budget",
                not (bud_over or bud_under),
                f"the wall encloses {measured:.0f} px^2 vs the budget's required {req:.0f} ({measured / req - 1:+.1%}, tolerance +{BUDGET_TOL_OVER:.0%}/-{BUDGET_TOL_UNDER:.0%}) - "
                + (
                    "unjustified open ground (the empty-space defect): shrink the wall to the budget, or declare+draw the extra ground as reserve/extras lines"
                    if bud_over
                    else "the wall cannot hold the program: enlarge to the budget, or trim the program"
                ),
            )

    # DOORS OPEN OUTWARD; ROWS STACK AT MOST TWO DEEP (GM, 2026-07-18). An urban building's door
    # glyph sits on its local +h/2 side (rotated by `rot` - settlement.building), so the door's
    # world direction derives from the manifest alone. A door must open onto WALKABLE ground
    # (street, roji, court, open space) - never into the back of another house an eave-gap away.
    # FARMHOUSES ARE EXEMPT EVERYWHERE: a farmhouse always faces SOUTH (its garden and threshing
    # ground need the sunlight - the orientation is canon); a city house has no sun constraint,
    # so it must face open ground instead. The pair rule follows from the same fact: contiguous
    # rows stack at most TWO deep (back-to-back, both fronts outward), because the middle row of
    # a 3-stack has walls hard against BOTH long faces - those households would be trapped.
    # Separations in real feet: an eave/drainage gap is ~3-6 ft (drainage, not an entrance), a
    # walkable roji/court is >= ~10 ft; DOOR_CLEAR_FT = 7 sits cleanly between them at every
    # map scale (ftpx converts to drawn px).
    if scale in ("town", "city"):
        door_clear = DOOR_CLEAR_FT / meta.get("ftpx", 1)
        subj = [b for b in M.get("buildings", []) if "w" in b]
        blockers = subj + [h for h in M.get("houses", []) if "w" in h]
        bcorn = [rect_corners(_struct_rect(b)) for b in blockers]
        bdiag = [math.hypot(b["w"], b["h"]) / 2 for b in blockers]

        def _face_blocked(b: dict[str, Any], sgn: float) -> bool:
            th = math.radians(b.get("rot", 0))
            ux, uy = -math.sin(th) * sgn, math.cos(th) * sgn  # outward normal of the (sgn=+1) door face
            vx, vy = -uy, ux  # lateral, along the face
            fx, fy = b["x"] + ux * b["h"] / 2, b["y"] + uy * b["h"] / 2  # face center
            rr = math.hypot(b["w"], b["h"]) / 2 + door_clear + 1
            for o, oc, od in zip(blockers, bcorn, bdiag, strict=True):
                if o is b or math.hypot(o["x"] - b["x"], o["y"] - b["y"]) > rr + od:
                    continue
                for d in (0.8, door_clear * 0.55, door_clear):
                    for t in (-0.3 * b["w"], 0.0, 0.3 * b["w"]):
                        if point_in_poly(fx + ux * d + vx * t, fy + uy * d + vy * t, oc):
                            return True
            return False

        bad_doors = [b for b in subj if _face_blocked(b, 1.0)]
        check(
            "city_house_doors_unblocked",
            not bad_doors,
            f"{len(bad_doors)} building(s) whose DOOR opens into another structure within ~{DOOR_CLEAR_FT:.0f} real ft "
            f"(an eave gap, not an entrance): {[(round(b['x']), round(b['y']), b.get('kind')) for b in bad_doors[:5]]} - a city house faces "
            f"open ground (street/roji/court); in a back-to-back pair both doors face OUTWARD (rot the row 180), never into a neighbor's back wall",
        )
        trapped = [b for b in subj if _face_blocked(b, 1.0) and _face_blocked(b, -1.0)]
        check(
            "city_rows_max_two_deep",
            not trapped,
            f"{len(trapped)} building(s) walled on BOTH long faces - the trapped middle of a 3-deep row stack: "
            f"{[(round(b['x']), round(b['y']), b.get('kind')) for b in trapped[:5]]} - rows/columns stack at most TWO deep (back-to-back); "
            f"after every pair leave a walkable roji/court (>= ~10 real ft), so every household fronts open ground",
        )

    # A MERCHANT ESTATE'S WALL STANDS ON DRY, PRIVATE GROUND (GM, 2026-07-19). The walled
    # compound of a very-rich urban merchant must not run its perimeter wall through WATER
    # (a wall footed in a canal/dock basin is undermined, and the working quay/towpath must
    # stay open to the boats and porters that make the merchant rich) or through a FIRE TOWER
    # (the fire watch is municipal - it needs its own footing, daylight around the frame, and
    # access for the watch; it cannot be embedded in a private compound wall). The whole
    # perimeter is walked, gate gap included - a courtyard gate opening straight onto water
    # or into the tower frame is the same siting error.
    if scale in ("town", "city") and M.get("merchant_estates"):
        WMARG = 1.5  # px of daylight demanded beyond the drawn footprints/line widths

        def _near_line(pts: Any, hw: float) -> Any:
            return lambda px_, py_: any(seg_dist(px_, py_, pts[k], pts[k + 1]) < hw for k in range(len(pts) - 1))

        def _in_grown_rect(it: dict[str, Any]) -> Any:
            gc = rect_corners(_struct_rect({**it, "w": it["w"] + 2 * WMARG, "h": it["h"] + 2 * WMARG}))
            return lambda px_, py_: point_in_poly(px_, py_, gc)

        est_waters: list[tuple[str, Any]] = [("canal", _near_line(cc["poly"], cc.get("w", 12) / 2 + WMARG)) for cc in M.get("canals", [])]
        if M.get("moat"):
            est_waters.append(("moat", _near_line(M["moat"], M.get("moat_width", 22) / 2 + WMARG)))
        rv = M.get("river")
        if rv:
            est_waters.append(("river", _near_line(rv["pts"], rv.get("w", 40) / 2 + WMARG)))
        est_waters += [("dock", _in_grown_rect(dk)) for dk in M.get("docks", [])]
        if M.get("pond"):
            pcx, pcy, prx, pry = M["pond"]
            est_waters.append(("pond", lambda px_, py_: ((px_ - pcx) / (prx + WMARG)) ** 2 + ((py_ - pcy) / (pry + WMARG)) ** 2 <= 1))
        est_ftowers: list[tuple[str, Any]] = [("fire tower", _in_grown_rect(t)) for t in M.get("fire_towers", []) if "w" in t]

        def _wall_pts(est: dict[str, Any]) -> list[tuple[float, float]]:
            ex0, ey0, ex1, ey1 = est["x"] - est["w"] / 2, est["y"] - est["h"] / 2, est["x"] + est["w"] / 2, est["y"] + est["h"] / 2
            pts = []
            for p0, p1 in [((ex0, ey0), (ex1, ey0)), ((ex1, ey0), (ex1, ey1)), ((ex1, ey1), (ex0, ey1)), ((ex0, ey1), (ex0, ey0))]:
                steps = max(2, int(math.hypot(p1[0] - p0[0], p1[1] - p0[1]) / 3))
                pts += [(p0[0] + (p1[0] - p0[0]) * si / steps, p0[1] + (p1[1] - p0[1]) * si / steps) for si in range(steps + 1)]
            return pts

        def _wall_hits(est: dict[str, Any], targets: list[tuple[str, Any]]) -> list[str]:
            pts = _wall_pts(est)
            return [name for name, fn in targets if any(fn(px_, py_) for px_, py_ in pts)]

        est_wet = [(round(e["x"]), round(e["y"]), _wall_hits(e, est_waters)) for e in M["merchant_estates"]]
        est_wet = [ew for ew in est_wet if ew[2]]
        check(
            "merchant_estate_wall_clear_of_water",
            not est_wet,
            f"merchant-estate wall(s) running through open water: {est_wet} - a compound wall stands on dry ground; "
            f"the canal/dock/moat/pond edge is working waterfront (boats, porters, the towpath), not private wall footing - move the estate clear",
        )

        # a tower ENCLOSED in the private court (wall-line clear, tower trapped inside) is the
        # same siting error as a wall through it - the watch must reach its tower from public ground
        def _tower_conflict(e: dict[str, Any]) -> bool:
            if _wall_hits(e, est_ftowers):
                return True
            return any(abs(t["x"] - e["x"]) < e["w"] / 2 and abs(t["y"] - e["y"]) < e["h"] / 2 for t in M.get("fire_towers", []) if "w" in t)

        towered = [(round(e["x"]), round(e["y"])) for e in M["merchant_estates"] if _tower_conflict(e)]
        check(
            "merchant_estate_wall_clear_of_fire_towers",
            not towered,
            f"merchant-estate wall(s) running through - or enclosing - a fire tower: {towered} - the fire watch is municipal; the tower needs its own "
            f"footing, daylight around the braced frame, and watch access from public ground - it cannot be embedded in (or walled inside) a private compound; move the estate or the tower",
        )

        # THE SAME WALLS STAY OFF THE STREETS (GM follow-up, 2026-07-19): a compound wall
        # standing in a street bed blocks the public way - the wall may LINE a street (that is
        # what a walled compound on a block looks like) but never stand IN its cleared band.
        est_streets: list[tuple[str, Any]] = [("street", _near_line(st["pts"], st.get("w", 12) / 2 + WMARG)) for st in M.get("town_streets", [])]
        est_streets += [("alley", _near_line(al["pts"], al.get("w", 8) / 2 + WMARG)) for al in M.get("alleys", [])]
        est_streets += [("road", _near_line(rd["pts"], rd["w"] / 2 + WMARG)) for rd in M.get("roads", [])]
        if M.get("road"):
            est_streets.append(("road", _near_line(M["road"], M.get("road_width", 26) / 2 + WMARG)))
        if M.get("ring_road"):
            est_streets.append(("ring road", _near_line(M["ring_road"], M.get("ring_road_width", 7) / 2 + WMARG)))
        est_on_st = [(round(e["x"]), round(e["y"]), _wall_hits(e, est_streets)) for e in M["merchant_estates"]]
        est_on_st = [ew for ew in est_on_st if ew[2]]
        check(
            "merchant_estate_wall_clear_of_streets",
            not est_on_st,
            f"merchant-estate wall(s) standing IN a street/alley/road bed: {est_on_st} - the public way stays open; "
            f"a compound wall may line a street but never stand in its cleared band - move the estate off the street",
        )

    # COMPOUND GATES AND WALLS TO SCALE (GM, 2026-07-19). The walled compounds (samurai country
    # estates/manors, the governor's yamen, merchant estates, the mausoleum) draw only walls +
    # gate + a deliberately BLANK court (the interior is its own Mode A diagram) - so the wall
    # and gate ARE the feature, and they must be honest: a samurai residence gate (nagayamon /
    # yakuimon) opens ~9-12 real ft (cart + palanquin), a grand yamen gatehouse up to ~24 ft;
    # the old fixed-pixel gap (+-34px) drew a 204 ft opening at city scale - most of a wall
    # missing. Walls (dobei/tsuijibei) run ~1.5-2 ft thick, drawn true-width-or-floored (the
    # 2px cartographic floor = 6 ft at city scale; band top 8 allows it). A manifest that
    # records no gate_w predates the to-scale engine and cannot prove its gates - regenerate.
    _gcomp = [("manor", mn) for mn in M.get("manors", [])] + [("merchant estate", me) for me in M.get("merchant_estates", [])] + [("mausoleum", mu) for mu in M.get("mausoleums", [])]
    if M.get("governor_mansion"):
        _gcomp.append(("governor's mansion", M["governor_mansion"]))
    if _gcomp:
        _gftpx = meta.get("ftpx", 1)
        gcomp_bad = []
        for gkind, gc in _gcomp:
            gw = gc.get("gate_w")
            if gw is None:
                gcomp_bad.append((gkind, round(gc["x"]), round(gc["y"]), "gate unrecorded - regenerate with the to-scale engine"))
                continue
            gft = gw * _gftpx
            side = gc["w"] if gc.get("gate_dir", "south") in ("north", "south") else gc["h"]
            wallft = gc.get("wall_w", 0) * _gftpx
            if not GATE_FT_MIN <= gft <= GATE_FT_MAX:
                gcomp_bad.append((gkind, round(gc["x"]), round(gc["y"]), f"gate opening {gft:.0f} ft outside [{GATE_FT_MIN:.0f},{GATE_FT_MAX:.0f}]"))
            elif gw > 0.4 * side:
                gcomp_bad.append((gkind, round(gc["x"]), round(gc["y"]), f"gate is {gw / side:.0%} of its wall side - reads as a missing wall, not a gate"))
            elif not WALL_FT_MIN <= wallft <= WALL_FT_MAX:
                gcomp_bad.append((gkind, round(gc["x"]), round(gc["y"]), f"wall drawn {wallft:.0f} ft thick, outside [{WALL_FT_MIN:.0f},{WALL_FT_MAX:.0f}]"))
        check(
            "compound_gates_to_scale",
            not gcomp_bad,
            f"walled compound(s) with out-of-scale gates/walls: {gcomp_bad[:4]} - a residence gate opens ~9-12 real ft (a grand "
            f"yamen gatehouse up to ~24), walls run ~2 ft thick (2px cartographic floor); the blank court is deliberate (the interior is its own diagram) so the wall+gate must carry the realism",
        )

    # FUNERARY FEATURES TO SCALE (GM, 2026-07-19; anchors in settlements.md "Historical
    # grounding"). The old glyphs were FIXED-PIXEL and silently tripled at city scale.
    _fftpx = meta.get("ftpx", 1)
    crem_bad = []
    for cg in M.get("cremation_grounds", []):
        long_ft = max(cg["w"], cg["h"]) * _fftpx
        crem_cap = CREMATION_FT_MAX_CITY if scale == "city" else CREMATION_FT_MAX_TOWN
        if not CREMATION_FT_MIN <= long_ft <= crem_cap:
            crem_bad.append((round(cg["x"]), round(cg["y"]), f"{long_ft:.0f} ft across vs [{CREMATION_FT_MIN:.0f},{crem_cap:.0f}]"))
    if M.get("cremation_grounds"):
        check(
            "cremation_ground_to_scale",
            not crem_bad,
            f"cremation ground(s) out of scale: {crem_bad} - a sanmai's working core (7 ft hearth, shelter, bone platform, mourner ground) "
            f"clears 30-80 ft for a village/town and ~80-160 ft for a provincial city; even the crematory serving metropolitan Edo was ~180 ft square",
        )
    oss_bad = [(round(o["x"]), round(o["y"]), f"{max(o['w'], o['h']) * _fftpx:.0f} ft") for o in M.get("ossuaries", []) if not OSSUARY_FT_MIN <= max(o["w"], o["h"]) * _fftpx <= OSSUARY_FT_MAX]
    if M.get("ossuaries"):
        check(
            "ossuary_to_scale",
            not oss_bad,
            f"pauper ossuary mound(s) out of scale: {oss_bad} (band [{OSSUARY_FT_MIN:.0f},{OSSUARY_FT_MAX:.0f}] ft) - a muenzuka is a 10-30 ft mound "
            f"(cremated bone takes almost no volume; even Kyoto's monumental state-built Mimizuka is ~50 ft at the base); the band top allows the small-glyph legibility floor",
        )
    if M.get("cemeteries") and scale in ("village", "town", "city"):
        total_ac = sum(c["w"] * c["h"] for c in M["cemeteries"]) * _fftpx * _fftpx / 43_560
        lo, hi = BURIAL_AC_BAND[scale]
        check(
            "burial_grounds_sized_to_population",
            lo <= total_ac <= hi,
            f"total burial ground {total_ac:.2f} acres vs the {scale} band [{lo},{hi}] - size the grounds to the population served "
            f"(cremation-then-inter culture, ~1 generation of active plots before reuse: village ~0.1-0.25 ac, town ~0.25-0.75, city ~0.75-2 split across yards); "
            f"the ladder must read MONOTONE with population - a village ground must never dwarf a town's",
        )

    # ALMOST all shops front a street (commerce wants the street); POOR housing (laborer/burakumin)
    # mostly packs the block INTERIOR, reached by alleys, not the paved street frontage. (The towns
    # set the template: businesses on the frontage via s.frontage, dwellings interior via s.pack.)
    if scale in ("town", "city"):
        st_lines = [st["pts"] for st in M.get("town_streets", [])] + ([M["road"]] if M.get("road") else [])

        def on_a_street(b: dict[str, Any]) -> bool:
            # 85 REAL FEET of a street centerline (converted at the declared scale): the fixed
            # 85px was tuned at the towns' 1 ft/px grain and would call most of a 3 ft/px city
            # "on a street" (85px there is 255 ft - two full blocks)
            return any(seg_dist(b["x"], b["y"], sp[i], sp[i + 1]) < 85 / meta.get("ftpx", 1) for sp in st_lines for i in range(len(sp) - 1))

        biz = [b for b in M.get("buildings", []) if b.get("kind") in BUSINESS_KINDS]
        if biz:
            off = [b for b in biz if not on_a_street(b)]
            # WHY (commerce takes the valuable street frontage; dwellings sit behind/interior): settlements.md "Historical grounding"
            check(
                "businesses_front_streets",
                len(off) <= 0.15 * len(biz),
                f"{len(off)}/{len(biz)} shops/merchant houses are NOT on a street - almost every business fronts a street (the more mercantile a quarter, the more streets); only dwellings fill the block interior",
            )
        poor = [b for b in M.get("buildings", []) if b.get("kind") in ("laborer", "burakumin")]
        if poor:
            onst = [b for b in poor if on_a_street(b)]
            check(
                "poor_housing_mostly_interior",
                len(onst) <= 0.5 * len(poor),
                f"{len(onst)}/{len(poor)} laborer/burakumin dwellings sit ON a street - most poor housing jams the block INTERIOR (reached by alleys), behind the street-facing businesses",
            )
        # surrounding farmland must be WORKED: the part of each outside field that SHOWS on the map
        # carries farmhouses at roughly the village/hamlet linear density (~12 per 1000px of field edge,
        # min ~4). Off-map field portions have their farmhouses off-screen (fine, expected), but a field
        # presenting a real on-map edge with almost no farmhouses beside it is wrong - farmers build
        # close to the fields they work. We count only IN-VIEW houses against the on-map field edge, so
        # a partially-rendered field is held to its SHOWN extent (the gap the old per-field >=2 missed).
        ADJ = 165
        FARM_LD = 7.0  # houses per 1000px of shown edge - a floor: village fields run ~4-19, the bad ones ~0
        sparse = []
        for f in fields:
            cx, cy = (f["bbox"][0] + f["bbox"][2]) / 2, (f["bbox"][1] + f["bbox"][3]) / 2
            if M.get("wall") and point_in_poly(cx, cy, M["wall"]):
                continue  # in-wall plots are not surrounding farmland
            edge = onmap_field_edge(f["outline"], EX0, EY0, EX1, EY1)
            if edge < 120:
                continue  # only a tiny sliver shows - too little to require farmhouses
            nv = sum(1 for h in houses if EX0 <= h["x"] <= EX1 and EY0 <= h["y"] <= EY1 and poly_dist(h["x"], h["y"], f["outline"]) <= ADJ)
            if nv < FARM_LD * edge / 1000:
                sparse.append((f["name"], nv, round(FARM_LD * edge / 1000, 1)))
        check("outside_fields_farmhouse_density", not sparse, f"shown field edge(s) with too few farmhouses beside the on-map portion (farmers build close; expect ~village density): {sparse}")
        # the IN-WALL agricultural district (the unusual city that farms inside its walls) is REAL
        # farmland too. Unlike the SURROUNDING fields above - mostly off the cropped map, so only a
        # FLOOR (7) is enforceable on their shown sliver - an in-wall field sits ENTIRELY in view, so
        # its WHOLE perimeter must read as worked: ring it DENSELY all the way round, not a sparse few
        # on one side leaving long bare edges. Held to a much higher density (the dense end of village
        # ringing). Only bites when meta(agricultural_district=True) - most cities have no in-wall fields.
        FARM_LD_INWALL = 16.0  # houses per 1000px of edge - a full, all-round ring, not the off-map floor
        if scale == "city" and meta.get("agricultural_district") and M.get("wall"):
            thin = []
            for f in fields:
                cx, cy = (f["bbox"][0] + f["bbox"][2]) / 2, (f["bbox"][1] + f["bbox"][3]) / 2
                if not point_in_poly(cx, cy, M["wall"]):
                    continue  # only the in-wall plots
                # VEGETABLE tracts are exempt from the farmstead ring: urban garden ground is
                # worked by the residents of the surrounding quarters (well/night-soil fed
                # intensive plots), not by dedicated in-wall farm households - only in-wall
                # PADDY carries the village-density farmhouse ring
                if f.get("kind") != "paddy":
                    continue
                edge = onmap_field_edge(f["outline"], EX0, EY0, EX1, EY1)
                if edge < 120:
                    continue
                nv = sum(1 for h in houses if poly_dist(h["x"], h["y"], f["outline"]) <= ADJ)
                if nv < FARM_LD_INWALL * edge / 1000:
                    thin.append((f["name"], nv, round(FARM_LD_INWALL * edge / 1000, 1)))
            check(
                "city_interior_fields_farmhouse_density",
                not thin,
                f"in-wall agricultural field(s) too sparsely farmed - an in-wall field shows its WHOLE perimeter, so ring it densely all the way round (no long bare edges), not a token few: {thin}",
            )
        # housing packs DEEP, but no GIANT cluster may be cut off from circulation: a big block of
        # dwellings with no street OR alley anywhere near it has no way in or out. Deep blocks must
        # be laced with gravel alleys (s.alley) so every dwelling is reachable.
        acc = [s["pts"] for s in M.get("town_streets", [])] + ([M["road"]] if M.get("road") else []) + [a["pts"] for a in M.get("alleys", [])]

        def cut_off(b: dict[str, Any]) -> bool:
            return not any(seg_dist(b["x"], b["y"], ln[i], ln[i + 1]) < 95 for ln in acc for i in range(len(ln) - 1))

        iso = [b for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS and cut_off(b)]
        seen: set[int] = set()
        biggest = 0
        for i in range(len(iso)):
            if i in seen:
                continue
            stack, n = [i], 0
            seen.add(i)
            while stack:
                j = stack.pop()
                n += 1
                for kk in range(len(iso)):
                    if kk not in seen and abs(iso[j]["x"] - iso[kk]["x"]) < 46 and abs(iso[j]["y"] - iso[kk]["y"]) < 46:
                        seen.add(kk)
                        stack.append(kk)
            biggest = max(biggest, n)
        check(
            "no_isolated_dwelling_cluster",
            biggest <= 30,
            f"a contiguous cluster of {biggest} dwellings sits >95px from any street OR alley - a giant block of houses with no way in or out; lace deep blocks with gravel alleys (s.alley) so every block is reachable",
        )
        # an alley must EARN its length by UNIQUELY serving dwellings. A building is credited to its
        # NEAREST lane only (the one it actually fronts), exactly as empty_street_runs scores streets -
        # so a lane counts only what no other lane already reaches. This catches BOTH a lane running off
        # into a half-empty corner (a "lane to nowhere") AND a redundant lane laid beside or across one
        # that already serves the same block (a perpendicular arm the block's spine already reaches, or a
        # second lane shadowing a parallel street). Scaled to the buildings (~1 dwelling per 30px of its
        # own length), so it holds at the city's dense small-footprint grain, not a fixed town pixel gap.
        alley_blds = M.get("buildings", []) + M.get("houses", [])
        alleys = [a["pts"] for a in M.get("alleys", [])]
        other = [s["pts"] for s in M.get("town_streets", [])] + ([M["road"]] if M.get("road") else [])

        kido = M.get("kido", [])

        def lane_dist(b: dict[str, Any], pts: Poly) -> float:
            return min(seg_dist(b["x"], b["y"], pts[i], pts[i + 1]) for i in range(len(pts) - 1))

        def foot(b: dict[str, Any], pts: Poly) -> tuple[float, float]:
            return min((seg_closest(b["x"], b["y"], pts[i], pts[i + 1]) for i in range(len(pts) - 1)), key=lambda c: math.hypot(b["x"] - c[0], b["y"] - c[1]))

        def gate_spur(pts: Poly) -> float:
            # a terminal stretch running OUT to a ward GATE past the last served building is a legitimate
            # gate-access spur (the lane pulls in to a kido), NOT a lane-to-nowhere - so it does not count
            # toward the serve ratio. Trim it from each gated end (distance from the gate to the nearest
            # building the lane fronts, measured along the lane).
            spur = 0.0
            for E in (pts[0], pts[-1]):
                if not any(math.hypot(E[0] - g["x"], E[1] - g["y"]) < 20 for g in kido):
                    continue
                reach = [math.hypot(E[0] - (c := foot(b, pts))[0], E[1] - c[1]) for b in alley_blds if lane_dist(b, pts) < 60]
                if reach:
                    spur += min(reach)
            return spur

        uniq = [0] * len(alleys)
        for b in alley_blds:
            best_d, best_i = 60.0, None  # only buildings within a frontage band count for any lane
            for li, pts in enumerate(alleys):
                d = lane_dist(b, pts)
                if d < best_d:
                    best_d, best_i = d, li
            if best_i is None:
                continue
            if all(lane_dist(b, pts) > best_d for pts in other):  # no street/road is closer - this alley owns it
                uniq[best_i] += 1
        thin = []
        for li, pts in enumerate(alleys):
            length = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
            length -= gate_spur(pts)  # the run out to a ward gate is access, not block-service
            if uniq[li] * 30 < length:
                thin.append((pts[0], uniq[li], round(length)))
        check(
            "alleys_serve_buildings",
            not thin,
            f"alley(s) that uniquely serve too few dwellings to justify their length - a lane to nowhere or a redundant lane beside/across one that already serves the block (need ~1 uniquely-served dwelling per 30px): {thin}",
        )

    # ---- universal invariants ------------------------------------------------
    # standalone civic buildings (flophouse, granary kura) are checked for overlaps exactly like
    # houses and shops - they must not sit on a road / stream / wall / street / channel, or on
    # each other / the manor / a hall. (Merchant storehouses are NOT here: they are drawn as
    # annexes deliberately abutting their shop, so they would trip the structure-overlap test.)
    granary = M.get("granary")
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
    structs = [_struct_rect(s) for k in _OVERLAP_STRUCTS for s in M.get(k, [])] + [_struct_rect(s) for s in (granary["stores"] if granary else [])]
    corners = [rect_corners(s) for s in structs]
    bad = [
        (i, j)
        for i in range(len(structs))
        for j in range(i + 1, len(structs))
        if math.hypot(structs[i]["x"] - structs[j]["x"], structs[i]["y"] - structs[j]["y"]) <= 110 and sat_overlap(corners[i], corners[j])
    ]
    check("no_structure_overlaps", not bad, f"{len(bad)} overlapping structure pair(s)")

    # COMPLETENESS GUARD: every footprint feature in the manifest must be classified for overlap (in the
    # _OVERLAP_* registry above). The default is MUST-NOT-OVERLAP - a new feature joins _OVERLAP_STRUCTS
    # and is cleared by the checks above; anything allowed to overlap is named in _OVERLAP_EXEMPT. This
    # fires when a generator emits a feature key nobody classified, so a new feature can never silently
    # skip the overlap rules (the recurring trap: harvest features shipped unchecked).
    unclassified = sorted(
        k for k, v in M.items() if isinstance(v, list) and v and isinstance(v[0], dict) and any(g in v[0] for g in ("x", "pts", "outline", "boundary", "poly")) and k not in _OVERLAP_CLASSIFIED
    )
    check(
        "every_feature_classified_for_overlap",
        not unclassified,
        f"map feature(s) {unclassified} are not classified for overlap. The default is MUST-NOT-OVERLAP: add the key "
        f"to _OVERLAP_STRUCTS (so the no_structure_* checks clear it) or, if it is MEANT to overlap something (a label, "
        f"a bridge over water, a guard tower on a wall), to _OVERLAP_EXEMPT with the reason.",
    )

    # no structure overlaps the magistrate's manor walls (a tilted manor uses its rotated corners)
    bad_m = []
    for mn in M.get("manors", []):
        e = 4  # wall thickness
        mc = rect_corners({"x": mn["x"], "y": mn["y"], "w": mn["w"] + 2 * e, "h": mn["h"] + 2 * e, "rot": mn.get("rot", 0)})
        bad_m += [1 for sc in corners if sat_overlap(sc, mc)]
    check("no_structure_on_manor", not bad_m, f"{len(bad_m)} structure(s) overlap the manor walls")

    def rect_corners_xywh(item: dict[str, Any], e: float) -> list[tuple[float, float]]:
        cx, cy, w, h = item["x"], item["y"], item["w"], item["h"]
        return [(cx - w / 2 - e, cy - h / 2 - e), (cx + w / 2 + e, cy - h / 2 - e), (cx + w / 2 + e, cy + h / 2 + e), (cx - w / 2 - e, cy + h / 2 + e)]

    # no structure overlaps a religious hall (an ellipse block undershot its corners)
    bad_rel = [1 for rel in M.get("religious", []) for sc in corners if sat_overlap(sc, rect_corners_xywh(rel, 4))]
    check("no_structure_on_religious", not bad_rel, f"{len(bad_rel)} structure(s) overlap a religious hall")

    # no structure overlaps the gate's guard station / guardtower
    bad_g = [1 for gs in M.get("gate_structs", []) for sc in corners if sat_overlap(sc, rect_corners_xywh(gs, 2))]
    check("no_structure_on_gate", not bad_g, f"{len(bad_g)} structure(s) overlap the gate guard station/tower")

    # no structure overlaps a torii arch (footprint ~38x28, centerd just below the post tops)
    bad_t = [1 for t in M.get("torii", []) for sc in corners if sat_overlap(sc, [(t[0] - 19, t[1] - 10), (t[0] + 19, t[1] - 10), (t[0] + 19, t[1] + 18), (t[0] - 19, t[1] + 18)])]
    check("no_structure_on_torii", not bad_t, f"{len(bad_t)} structure(s) overlap a torii arch")

    # roads/streets are a GROUND layer: a gatehouse or label that legitimately sits on a road
    # must be drawn ON TOP of it (higher draw-order z), never have the road painted over it.
    road_layers = []
    if M.get("road") is not None and M.get("road_z") is not None:
        road_layers.append((M["road"], M["road_z"], M.get("road_width", 26) / 2))
    road_layers += [(st["pts"], st["z"], st["w"] / 2) for st in M.get("town_streets", []) if "z" in st]
    overlays = [("label", lab[:4], lab[4]) for lab in M.get("labels", []) if len(lab) > 4]
    overlays += [("gatehouse", (gs["x"] - gs["w"] / 2, gs["y"] - gs["h"] / 2, gs["x"] + gs["w"] / 2, gs["y"] + gs["h"] / 2), gs["z"]) for gs in M.get("gate_structs", []) if "z" in gs]

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

    bad_z = [name for poly, rz, hw in road_layers for name, box, oz in overlays if rz > oz and line_hits_box(poly, box, hw)]
    check("roads_drawn_under_overlays", not bad_z, f"{len(bad_z)} road/street drawn OVER a gatehouse/label it should pass under: {sorted(set(bad_z))}")

    # LANE LAYERING: where two linear ground features cross, the WIDER renders on top (higher draw z).
    # The Imperial road is painted over the city streets it crosses, streets over the alleys they cross.
    # z is the recorded final draw position (settlement flushes road/street/alley as one ordered block).
    lanes = []
    if M.get("road") and M.get("road_z") is not None:
        lanes.append(("road", M["road"], M.get("road_width", 26), M["road_z"]))
    lanes += [("street", st["pts"], st["w"], st["z"]) for st in M.get("town_streets", []) if st.get("z") is not None]
    lanes += [("alley", a["pts"], a.get("w", 10), a["z"]) for a in M.get("alleys", []) if a.get("z") is not None]

    def lanes_cross(pi: Poly, pj: Poly) -> bool:
        return any(segments_cross(pi[a], pi[a + 1], pj[b], pj[b + 1]) for a in range(len(pi) - 1) for b in range(len(pj) - 1))

    mislayered = []
    for i in range(len(lanes)):
        for j in range(i + 1, len(lanes)):
            ni, pi, wi, zi = lanes[i]
            nj, pj, wj, zj = lanes[j]
            if abs(wi - wj) < 1 or not lanes_cross(pi, pj):
                continue  # same width (either order ok) or they don't cross
            wider, narrower = ((ni, zi), (nj, zj)) if wi > wj else ((nj, zj), (ni, zi))
            if wider[1] < narrower[1]:
                mislayered.append(f"{narrower[0]} over {wider[0]}")
    check("city_lanes_layered_by_width", not mislayered, f"a narrower lane is painted OVER a wider one it crosses (the wider lane must be on top): {sorted(set(mislayered))}")
    # where lanes meet they form a clean CROSSROADS: the paved BEDS merge into a continuous surface, with
    # no lane's EDGE (its dark curb-line) cutting across another lane's bed at the junction. The engine
    # draws the ground block in sub-layers - all edges, then all beds, then center-marks - so every edge
    # sits below every bed; the check guards that invariant (max edge draw-z < min bed draw-z).
    ez, bz = M.get("ground_edge_zmax"), M.get("ground_bed_zmin")
    if ez is not None and bz is not None:
        check(
            "intersections_are_crossroads",
            ez < bz,
            "lane edge-strokes render OVER bed-strokes, so a junction shows a line across it instead of a merged crossroads - draw all ground edges below all ground beds",
        )

    # WALLS render OVER the ground lanes: a road/street/alley that runs INTO a wall - touches or crosses
    # its stroke - must pass UNDER it (the wall has a higher draw z). The settlement draws ramparts in a
    # dedicated WALL layer above the ground block precisely so this holds; the check guards the invariant
    # for the city/town wall AND every neighborhood (ward) fence. A lane only breaches a wall at a GATE,
    # where the wall has a genuine opening (no stroke to render over), so crossings/touches at a gate are
    # exempt. The wall is a closed ring at city scale, an open hill-anchored arc at town scale.
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

    wall, wall_z = M.get("wall"), M.get("wall_z")
    gates = M.get("gates") or ([M["gate"]] if M.get("gate") else [])
    if wall and wall_z is not None and len(wall) >= 3:
        over_wall = lanes_over(list(wall), wall_z, scale == "city", gates)
        check(
            "city_lane_under_wall",
            not over_wall,
            f"a road/street/alley runs INTO the city wall and renders OVER it - a lane must pass UNDER the rampart (it shows through only at a gate opening): {over_wall}",
        )
    kido_pts = [(k["x"], k["y"]) for k in M.get("kido", [])]
    over_fence = []
    for wd in M.get("wards", []):
        if wd.get("z") is not None and len(wd.get("boundary", [])) >= 2:
            over_fence += [(wd.get("name", "ward"), n) for n in lanes_over(wd["boundary"], wd["z"], False, kido_pts)]
    check("city_lanes_under_ward_fences", not over_fence, f"a lane runs into a neighborhood (ward) fence and renders OVER it - lanes pass UNDER the fence (the kido marks the passage): {over_fence}")

    # A walled COMPOUND (mausoleum / manor) whose wall sits ALONG a neighborhood (ward) fence must
    # YIELD that wall to the fence: the fence is re-stamped on top and IS that side of the compound,
    # so there is no doubled, clashing parallel wall (s.mausoleum / s.manor do this automatically and
    # record the yielded sides in "ward_walls"). Verify every geometric abutment is recorded.
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

    # no structure overlaps the (wide) road
    road: Any = M.get("road")
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

    # no structure overlaps a stream
    streams = M.get("streams", [])
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

    # no structure overlaps an irrigation channel - the SAME full-footprint test as a stream.
    # (houses_off_corridors below also touches channels, but only by house CENTER distance, so a
    # channel clipping a farmhouse's corner while its center stayed clear used to slip through.)
    channels_struct = M.get("channels", [])
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

    # no structure overlaps the navigable CARGO CANAL - the same full-footprint test as a channel,
    # but the canal is a WIDER watercourse (a poling barge, not a field ditch), so its half-width is
    # honored. A merchant house / warehouse fronts the quay but must not stand IN the water (GM,
    # 2026-07: a merchant_large sat on Nagahara's canal - there was no canal-vs-struct check at all,
    # this being the first city with a canal). Jetties/water-gates/bridges legitimately cross it (EXEMPT).
    canals_struct = M.get("canals", [])
    if canals_struct:

        def on_canal(sc: Poly, cp: Poly, chw: float) -> bool:
            if any(seg_dist(cx, cy, cp[k], cp[k + 1]) < chw for (cx, cy) in sc for k in range(len(cp) - 1)):
                return True
            if any(point_in_poly(rx, ry, sc) for rx, ry in cp):
                return True
            return any(segments_cross(cp[k], cp[k + 1], sc[e], sc[(e + 1) % 4]) for k in range(len(cp) - 1) for e in range(4))

        bad_cn = [1 for sc in corners for c in canals_struct if on_canal(sc, c["poly"], c.get("w", 12) / 2 + 2)]
        check("no_structure_on_canal", not bad_cn, f"{len(bad_cn)} structure(s) overlap the cargo canal")

    # no structure overlaps the town wall (the thick rampart stroke)
    wallpts = M.get("wall")
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

    # no structure overlaps the MOAT (the water ring outside the wall) - extramural structures (the
    # common burial ground, the cremation ground, the ossuary, samurai estates) must keep clear of it
    moatpts = M.get("moat")
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

    # no structure overlaps the POND (the irrigation reservoir / in-wall water source). The pond is
    # the one water body that was never in this section: streams/channels/moat all have their clause
    # above, but a struct standing IN the pond slipped through (Tango's west fire tower landed on the
    # pond rim). Village ponds are auto-placed clear of everything, so this only ever bites hand-placed
    # structs - which is exactly when a check is needed. The pond is a true ellipse [cx, cy, rx, ry];
    # a footprint hits it if any sampled boundary point (corners + edge quarter-points, enough for
    # struct-sized rects vs a pond-sized ellipse) dips inside the rim, or the rect swallows the center.
    pond_st = M.get("pond")
    if pond_st:
        pe = [pond_st[0], pond_st[1], pond_st[2] + 3, pond_st[3] + 3]  # rim stroke (2.4) half-width + a little

        def on_pond(sc: Poly) -> bool:
            if point_in_poly(pond_st[0], pond_st[1], sc):
                return True
            pts = [(sc[e][0] + (sc[(e + 1) % 4][0] - sc[e][0]) * t, sc[e][1] + (sc[(e + 1) % 4][1] - sc[e][1]) * t) for e in range(4) for t in (0.0, 0.25, 0.5, 0.75)]
            return any(in_ellipse(px, py, pe) for px, py in pts)

        bad_p = [1 for sc in corners if on_pond(sc)]
        check("no_structure_on_pond", not bad_p, f"{len(bad_p)} structure(s) overlap the pond")

    # WATER-WIDTH LADDER. Real wet-rice water systems are a tiered hierarchy whose widths step up
    # ~2-4x per tier (channel width scales with the sqrt of command-area flow): a field ditch ~0.3 m,
    # a village creek ~2 m (~6x the ditch), a town river / castle moat ~20 m (~70x the ditch). That
    # true 250:1 span can't be drawn at schematic scale, so the rendered widths are a deliberate LOG-
    # COMPRESSION of it - but the ORDERING and the coarse steps must survive: an irrigation ditch is
    # ALWAYS the thinnest line, a natural watercourse clearly heavier, the city moat heaviest of all.
    # The clauses below pin that. (Why these numbers: settlements.md "Water-width ladder" grounding.)
    chan_ws = [c["w"] for c in M.get("channels", []) if "w" in c]
    strm_ws = [st["w"] for st in M.get("streams", []) if "w" in st]
    moat_w = M.get("moat_width")
    # (1) Irrigation channels are HAIRLINES: at/just above the legibility floor, never fattened toward
    # stream weight. A ditch drawn as a stout line (the old 4.2 px) reads as a watercourse, not a ditch.
    if chan_ws:
        fat = [w for w in chan_ws if not 2.0 <= w <= 3.5]
        check(
            "irrigation_channels_hairline",
            not fat,
            f"channel width(s) {sorted(set(fat))} outside the hairline band [2.0, 3.5] px - a field "
            f"ditch is the thinnest line on the map (~0.3 m, ~1/300 of the paddy it feeds); keep it at "
            f"the legibility floor, distinct from any natural watercourse",
        )
    # (2) The tiers are ORDERED with honest gaps: a creek clearly beats a ditch (>=2.5x), a natural
    # stream never out-widths the city moat (a moat-feeder may EQUAL it, by conservation of flow), and
    # the moat dwarfs a ditch (>=4x). Each clause runs only when both features it compares are present.
    if chan_ws and strm_ws:
        ok = min(strm_ws) >= 2.5 * max(chan_ws)
        check(
            "watercourses_wider_than_ditches",
            ok,
            f"narrowest stream {min(strm_ws)} px is not >= 2.5x the widest channel {max(chan_ws)} px - a natural creek must read clearly heavier than an irrigation ditch, not as its sibling",
        )
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
    if chan_ws and moat_w:
        check(
            "moat_dwarfs_ditches",
            moat_w >= 4.0 * max(chan_ws),
            f"city moat {moat_w} px is not >= 4x the widest channel {max(chan_ws)} px - a defensive moat (~20-35 m real, ~70x a field ditch) must dwarf an irrigation ditch",
        )

    # no structure overlaps a street OR an alley (a paved lane or a gravel alley running over a
    # house is wrong) - alleys are drawn last, so a careless alley can be laid across a building
    tstreets = M.get("town_streets", [])
    lanes = tstreets + [{"pts": a["pts"], "w": a.get("w", 10)} for a in M.get("alleys", [])]
    if lanes:

        def on_street(sc: Poly, sp: Poly, hw: float) -> bool:
            if any(seg_dist(cx, cy, sp[k], sp[k + 1]) < hw for (cx, cy) in sc for k in range(len(sp) - 1)):
                return True
            if any(point_in_poly(rx, ry, sc) for rx, ry in sp):
                return True
            return any(segments_cross(sp[k], sp[k + 1], sc[e], sc[(e + 1) % 4]) for k in range(len(sp) - 1) for e in range(4))

        bad_ts = [1 for sc in corners for st in lanes if on_street(sc, st["pts"], st.get("w", 24) / 2 + 2)]
        check("no_structure_on_street", not bad_ts, f"{len(bad_ts)} structure(s) overlapped by a street/alley")

    # ---- street-faced town layout: businesses front the streets (and face them); housing
    # sits back off the main commercial street. The "streets" are the town streets plus any
    # road (an unwalled town's road is its high street).
    street_lines = [st["pts"] for st in M.get("town_streets", [])]
    main_idx = next((i for i, st in enumerate(M.get("town_streets", [])) if st.get("main")), None)
    if M.get("road"):
        street_lines.append([list(p) for p in M["road"]])
        if main_idx is None:
            main_idx = len(street_lines) - 1
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

    corr = ([M["lane"]] if M.get("lane") else []) + [c["poly"] for c in M["channels"]]
    onroad = sum(1 for h in houses for poly in corr if any(seg_dist(h["x"], h["y"], poly[k], poly[k + 1]) < 14 for k in range(len(poly) - 1)))
    check("houses_off_corridors", onroad == 0, f"{onroad} house-on-corridor hit(s)")

    ADJ = 165
    # WHY (farmers build close to the fields they work): settlements.md "Historical grounding". The invariant
    # depends on the SETTLEMENT FORM, and it is TUNABLE via meta.nucleated:
    #   - DISPERSED (the default): every farmhouse fronts its own fields, so EACH house must be within ADJ
    #     of a field (`all_houses_field_adjacent`).
    #   - NUCLEATED (meta.nucleated=True): the houses cluster together and the FIELDS radiate from the
    #     cluster's edge - the interior houses are legitimately a cluster-span BACK from the nearest field,
    #     so per-house adjacency is wrong. Instead the whole CLUSTER must ABUT its fields: the nearest house
    #     is field-adjacent (the village sits ON its land, not floating in open country) AND no house is
    #     farther than the cluster's own diameter past that edge (`cluster_abuts_fields`).
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
    down_deg = meta.get("down_deg")
    drains = [fd["poly"] for fd in M.get("field_ditches", []) if fd.get("role") == "drain" and len(fd.get("poly", [])) >= 2]
    if houses and down_deg is not None and drains and not meta.get("nucleated"):
        dux, duy = math.cos(math.radians(down_deg)), math.sin(math.radians(down_deg))
        in_toe = []
        for h in houses + M.get("buildings", []):
            for dp in drains:
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
                if not at_end and (h["x"] - px) * dux + (h["y"] - py) * duy > 18:  # center clearly on the wet (downslope) side of the drain
                    in_toe.append((round(h["x"]), round(h["y"])))
                    break
        check(
            "dwellings_above_field_drain",
            not in_toe,
            f"{len(in_toe)} dwelling(s) sit in the WET low toe DOWNSLOPE of the field drain at {in_toe[:4]} - the "
            f"ground below the drainage line (marsh / low reclaimed paddy / the tameike) is the wettest in the "
            f"valley, not building ground; strew the farms on the DRY margins ABOVE the drain (flank farms past the drain's ends are fine)",
        )

    def runs_off_edge(ol: Poly) -> bool:
        return any(p[0] < EX0 or p[0] > EX1 or p[1] < EY0 or p[1] > EY1 for p in ol)

    for f in fields:
        if runs_off_edge(f["outline"]):
            continue  # a field running off the map has its farmhouses implied off-map too
        if f.get("kind") == "vegetable":
            continue  # urban garden tracts are worked by the surrounding quarters, not farmsteads
        ring = [h for h in houses if poly_dist(h["x"], h["y"], f["outline"]) <= ADJ]
        area = (f["bbox"][2] - f["bbox"][0]) * (f["bbox"][3] - f["bbox"][1])
        need = 5 if area > 80000 else 3
        check(f"field_ringed[{f['name']}]", len(ring) >= need, f"{len(ring)} houses, need {need}")

    not_south = [h for h in houses if h["w"] < h["h"] or abs(h["rot"]) > 12]
    check("houses_face_south", not not_south, f"{len(not_south)} house(s) not south-facing")

    headman = next((h for h in houses if h.get("role") == "headman"), None)
    if scale == "village":
        check("village_has_headman", headman is not None, "a village must have a headman")
    else:
        # hamlets fall under the village district headman; towns are run by the magistrate
        check(f"{scale}_has_no_headman", headman is None, f"a {scale} has no peasant headman of its own")

    # religious building by settlement scale: hamlet none, village shrine, town
    # monastery, city temple
    # WHY (the Shinto/Buddhist split + scale: shrine -> monastery -> temple): settlements.md "Historical grounding"
    expected_rel = {"hamlet": None, "village": "shrine", "town": "monastery", "city": "temple"}.get(scale)
    rel_kinds = set(r["kind"] for r in M.get("religious", [])) - {"small_shrine"}  # small wayside shrines are auxiliary, allowed alongside the scale's main religious building
    if expected_rel is None:
        check("religious_matches_scale", not rel_kinds, f"a {scale} should have no religious building (found {rel_kinds or 'none'})")
    else:
        check("religious_matches_scale", rel_kinds == {expected_rel}, f"a {scale} should have only {expected_rel}(s); found {rel_kinds or 'none'}")

    # A SHRINE and its TORII arch NESTLE in a CLEARING within the sacred grove - neither may sit UNDER the trees
    # (a hall/arch drawn on top of tree canopy reads as buried in the wood). So no fengshui-grove tree CLUMP may
    # overlap a religious hall's or a torii's footprint. The recorded clump `r` is the NOMINAL clump radius, but
    # the drawn crowns OVERHANG it, so the visible canopy reaches ~1.7x that - use the CANOPY radius so the check
    # matches what the eye sees. (The grove is drawn to SKIP the shrine + torii clearing; place them BEFORE it.)
    CANOPY = 1.7
    grove_clumps = [(c[0], c[1], gv.get("r", 10) * CANOPY) for k in ("village_groves", "groves") for gv in M.get(k, []) for c in gv.get("clumps", [])]
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
    # a religious building's subtitle must not RESTATE its type (the label already names it,
    # e.g. "Monastery of Tengen" needs no "(town monastery)" note)
    redundant_sub = [r.get("label") for r in M.get("religious", []) if r.get("sublabel") and any(t in r["sublabel"].lower() for t in ("shrine", "monastery", "temple"))]
    check("religious_subtitle_not_redundant", not redundant_sub, f"religious subtitle restates the building type (already in the label): {sorted(set(redundant_sub))}")
    if headman is not None:
        hm = headman["w"] * headman["h"]
        bigger = [h for h in houses if h is not headman and h["w"] * h["h"] >= hm]
        check("headman_is_largest", not bigger, f"{len(bigger)} house(s) >= headman")

    # no two body labels overlap (the title block is excluded by the generator)
    labels = M.get("labels", [])
    # An overlap is real when the bboxes cross by more than the estimation slack. The horizontal slack
    # is small (a >2px x-overlap means the glyphs actually touch); the vertical slack stays larger (~4px)
    # to absorb the descender allowance in the y-bbox, so two cleanly-separated STACKED labels whose boxes
    # merely kiss (e.g. Tango's "Mausoleum" / "Ministry of Works") are not falsely flagged.
    ov = [
        (i, j)
        for i in range(len(labels))
        for j in range(i + 1, len(labels))
        if min(labels[i][2], labels[j][2]) - max(labels[i][0], labels[j][0]) > 2 and min(labels[i][3], labels[j][3]) - max(labels[i][1], labels[j][1]) > 4
    ]
    check("no_label_overlaps", not ov, f"{len(ov)} overlapping label pair(s)")

    # the TITLE (the map's place name) must sit over BLANK space, not on a building / field / water / grove -
    # the reader has to be able to read it. The generator searches for a clear box (crop_to_content first, so the
    # search runs over the framed window); this verifies it landed clear. Solid features + the fields + pond.
    ttl = M.get("title")
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
                if s.get("poly"):
                    if _box_hits_poly(tb, s["poly"]):
                        thit.append(k)
                        break
                elif "w" in s and not (tb[2] < s["x"] - s["w"] / 2 or tb[0] > s["x"] + s["w"] / 2 or tb[3] < s["y"] - s["h"] / 2 or tb[1] > s["y"] + s["h"] / 2):
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
        check(
            "title_clear_of_features",
            not thit,
            f"the map title sits on {thit[:2]} - it must go over BLANK space so the place name is readable (the generator's s.title() searches for a clear box; call it AFTER crop_to_content)",
        )

    # A LABEL must not sit on a building/structure it does NOT name (town + city scale, where features
    # carry distinct identities). A label may overlap the feature(s) it names - its own building/compound,
    # or (for a zone label) any building of that cluster - and may clip a street-fronting shop or an
    # interleaved servant house (those line every quarter, so never a victim). But where a label spills
    # onto a DIFFERENT-identity feature it tells the reader that feature is something it is not (a
    # "Monastery" label over the graveyard, a "graveyard" label over the monastery). Each labeled feature
    # carries a GROUP; the label text declares which group(s) it may cover - else it fires.
    if scale in ("town", "city"):
        LABEL_FREE = {"shop", "servant"}
        FUNERARY = {"cemetery", "mausoleum", "cremation", "ossuary"}

        def _grp(kind: str) -> str:
            if kind in ("samurai", "samurai_large"):
                return "samurai"
            if kind in ("merchant", "merchant_house", "merchant_large"):
                return "merchant"
            if kind == "laborer_large":
                return "laborer"
            return kind

        def _bb(it: dict[str, Any]) -> tuple[float, float, float, float]:
            rot = it.get("rot", 0)
            hw, hh = it.get("w", 0) / 2, it.get("h", 0) / 2
            if not rot:
                return it["x"] - hw, it["y"] - hh, it["x"] + hw, it["y"] + hh
            a = math.radians(rot)
            ca, sa = math.cos(a), math.sin(a)
            xs = [it["x"] + dx * ca - dy * sa for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]
            ys = [it["y"] + dx * sa + dy * ca for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]
            return min(xs), min(ys), max(xs), max(ys)

        vics = [(_grp(b.get("kind", "")), _bb(b)) for b in M.get("buildings", []) if _grp(b.get("kind", "")) not in LABEL_FREE]
        vics += [("flophouse", _bb(fp)) for fp in M.get("flophouses", [])]
        vics += [("temple", _bb(r)) for r in M.get("religious", [])]
        vics += [("ministry", _bb(mi)) for mi in M.get("ministries", [])]
        vics += [("governor", _bb(M["governor_mansion"]))] if M.get("governor_mansion") else []
        vics += [("gate", _bb(gs)) for gs in M.get("gate_structs", [])]
        vics += [("merchant", _bb(e)) for e in M.get("merchant_estates", [])]
        vics += [("estate", _bb(mn)) for mn in M.get("manors", [])]
        vics += [("cemetery", _bb(c)) for c in M.get("cemeteries", [])]
        vics += [("mausoleum", _bb(mu)) for mu in M.get("mausoleums", [])]
        vics += [("cremation", _bb(cg)) for cg in M.get("cremation_grounds", [])]
        vics += [("ossuary", _bb(o)) for o in M.get("ossuaries", [])]

        def _label_allows(txt: str) -> set[str]:
            t = txt.lower()
            if "guard" in t or "inspection" in t:  # "guard house" / "guard station" / "front gate (...)"
                return {"gate"}
            if "flophouse" in t:
                return {"flophouse"}
            if "ministry" in t:
                return {"ministry"}
            if "governor" in t or "mansion" in t:
                return {"governor"}
            if "manor" in t or "magistrate" in t:
                return {"estate"}
            if any(w in t for w in ("temple", "shrine", "monastery", "chapel")):
                return {"temple"}
            if any(w in t for w in ("graveyard", "burial", "cemetery", "cremation", "mausoleum", "ossuary")):
                return FUNERARY  # the funerary structures cluster, so a funerary label may cover any of them
            if "samurai" in t:
                return {"samurai", "estate"}
            if "laborer" in t or "laborer" in t:
                return {"laborer"}
            if "burakumin" in t or "agricultur" in t:  # the in-wall farming district also houses burakumin
                return {"burakumin"}
            if "barn" in t:
                return {"barn"}
            if "merchant" in t:
                return {"merchant"}
            if any(w in t for w in ("street", "avenue", "road")):
                return {"merchant"}  # a street/road label runs along its frontage, so it may clip the storefronts it lines
            return set()  # farmland / market / theater stage / title labels name no building

        mislabel = []
        for L in M.get("labels", []):
            if len(L) <= 5:
                continue
            allow = _label_allows(L[5])
            for g, (x0, y0, x1, y1) in vics:
                if g in allow:
                    continue
                if L[0] < x1 and x0 < L[2] and L[1] < y1 and y0 < L[3]:
                    mislabel.append(f"{L[5]!r} over a {g}")
                    break
        check(
            "labels_clear_of_other_buildings",
            not mislabel,
            f"label(s) sitting on a feature they do not name (a label may cover only the thing it labels, or a fronting shop/servant house): {sorted(set(mislabel))}",
        )

    # LABELS must stay WITHIN the rendered image. Plenty of things rightly run off the edge - farm
    # fields, roads, samurai country estates, farmhouses, the countryside continuing beyond the frame -
    # but a label that spills past the edge is clipped and unreadable, so every label's bounding box
    # must sit inside the frame. The frame is the cropped view (a city map crops tight to the walls,
    # so its EX/EY bounds are the viewBox) or, uncropped, the full canvas. The title is placed directly
    # (not recorded in M["labels"]) and sits inside the frame by construction.
    off_img = [L[5] if len(L) > 5 else "label" for L in labels if L[0] < EX0 - 1 or L[1] < EY0 - 1 or L[2] > EX1 + 1 or L[3] > EY1 + 1]
    check(
        "labels_within_image",
        not off_img,
        f"label(s) running off the edge of the image - a label must sit fully within the frame (fields/roads/estates/farmhouses may run off, labels may not): {sorted(set(off_img))}",
    )

    # every WELL must sit AMONG the buildings it serves (ANY scale): a communal well is the draw-point for
    # the households around it, so one out in open countryside with no building beside it is unreal. (A city's
    # pack fills in around its wells; the rural tiers place wells only near houses via place_wells(..., near=...),
    # since their grid would otherwise scatter into the fields.) A well may also serve a RELIGIOUS building - a
    # set-apart shrine's own ablution well stands beside the shrine, not among houses - so religious halls count.
    all_wells = M.get("wells", [])
    if all_wells:
        dwell_all = M.get("buildings", []) + M.get("houses", []) + M.get("religious", [])
        stray = [
            (round(wl["x"]), round(wl["y"])) for wl in all_wells if dwell_all and min(math.hypot(wl["x"] - b["x"], wl["y"] - b["y"]) - 0.5 * math.hypot(b["w"], b["h"]) for b in dwell_all) > 95
        ]  # gap to the served building's EDGE (fair to a large hall)
        check(
            "wells_among_dwellings",
            not stray,
            f"well(s) standing in open ground with no building within ~95px - a well serves the households around it and must sit AMONG them, not out in the fields/countryside: {stray[:4]}",
        )
        # a wellhead must be DRAWN at a size proportional to the buildings: it scales with the map grain
        # (bscale) the way the houses do, so it reads as a consistent ~half-a-dwelling at every tier. A
        # fixed pixel size looks right in the dense city but shrinks to a speck beside a village/town's
        # larger houses. Each well records its drawn radius `vr`; the mean well diameter should be a
        # sensible fraction of the median dwelling.
        ddims = [max(b["w"], b["h"]) for b in dwell_all if "w" in b and "h" in b]
        if ddims and any("vr" in wl for wl in all_wells):
            med = sorted(ddims)[len(ddims) // 2]
            mean_dia = 2 * sum(wl.get("vr", 5) for wl in all_wells) / len(all_wells)
            check(
                "wells_sized_to_buildings",
                0.35 <= mean_dia / med <= 0.85,
                f"wells are mis-sized for this map - drawn at {mean_dia:.0f}px against a ~{med:.0f}px median dwelling "
                f"({mean_dia / med:.0%}; want ~40-80%): a wellhead must scale with the map grain (bscale), not a fixed pixel size",
            )

    # WATER ACCESS for the rural tiers (town/village/hamlet): every settlement needs communal WELLS, and
    # every household must be able to reach water. Wells dot the dwellings (one per ~20-25 households),
    # but a farm household may instead draw from the irrigation network it sits beside - a channel, the
    # pond, the stream, the moat - so a dwelling counts as watered if a WELL OR an irrigation watercourse
    # is within reach. (The CITY tier has its own finer well suite - density, block-interior placement,
    # the samurai-quarter exemption - so this covers the village/hamlet/town tiers the same way.)
    if scale in ("town", "village", "hamlet"):
        wells = M.get("wells", [])
        dwell = M.get("houses", []) + [b for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS]
        # A WELL stands BESIDE a shrine, never ON its hall or UNDER its torii arch (a wellhead drawn on the hall
        # or in the gateway reads wrong). remote_shrine_has_own_well WANTS a well close by - but beside it, clear
        # of the footprints. Circle (well disc) vs rect (hall / the torii arch's x +/-19, y -10..+18 box). Root
        # cause when it fires: wells were scattered BEFORE the shrine/torii were placed, so their block-outs did
        # not yet exist - place the shrine_hall (with its torii) BEFORE place_wells / shrine_well.
        sacred = [(r["x"], r["y"], r["w"] / 2, r["h"] / 2) for r in M.get("religious", [])]
        sacred += [(t[0], t[1] + 4, 19, 14) for t in M.get("torii", [])]
        if wells and sacred:
            on_sacred = []
            for wl in wells:
                for bx, by, hw, hh in sacred:
                    ddx = wl["x"] - bx - max(-hw, min(hw, wl["x"] - bx))
                    ddy = wl["y"] - by - max(-hh, min(hh, wl["y"] - by))
                    if ddx * ddx + ddy * ddy < wl["r"] * wl["r"]:
                        on_sacred.append((round(wl["x"]), round(wl["y"])))
                        break
            check(
                "wells_clear_of_shrine_and_torii",
                not on_sacred,
                f"{len(on_sacred)} well(s) overlap a shrine hall or torii arch at {on_sacred[:4]} - a wellhead "
                f"stands BESIDE the shrine, never on the hall or under the gateway; place the shrine + torii "
                f"BEFORE the wells so they are blocked out",
            )
        if wells:
            # a WELLHEAD is a clean draw-point: no tree canopy may reach it (a well lost under the wood reads
            # wrong). Gather every tree feature - the communal fengshui GROVE clumps (windbreak/water-mouth/copse,
            # each a center + drawn radius), the per-house YASHIKIRIN grove rects, a big FOREST, and the managed-
            # WOODLAND coppice patches - and fire on any well whose drawn head (vr) overlaps one. Fix at placement:
            # the grove is placed AFTER the wells and skips them (with a keep-out wide enough for the canopy).
            _clumps = [(cx, cy, g.get("r", 6)) for g in M.get("village_groves", []) for cx, cy in g.get("clumps", [])]
            _grects = [(g["x"], g["y"], g["w"], g["h"]) for g in M.get("groves", [])]
            _forest = M.get("forest")
            _wl_polys = [c["poly"] for c in M.get("commons", []) if c.get("role") == "woodland"]
            on_trees = []
            for wl in wells:
                wx, wy, vr = wl["x"], wl["y"], wl.get("vr", wl.get("r", 8))
                if (
                    any(math.hypot(wx - cx, wy - cy) < vr + cr for cx, cy, cr in _clumps)
                    or any(abs(wx - gx) < gw / 2 + vr and abs(wy - gy) < gh / 2 + vr for gx, gy, gw, gh in _grects)
                    or (_forest and point_in_poly(wx, wy, _forest))
                    or any(point_in_poly(wx, wy, p) for p in _wl_polys)
                ):
                    on_trees.append((round(wx), round(wy)))
            check(
                "wells_clear_of_trees",
                not on_trees,
                f"well(s) {on_trees[:4]} sit UNDER trees - a wellhead is a clean draw-point, not lost in the wood; "
                f"keep it clear of the fengshui grove, the per-house groves, the forest, and the coppice patches "
                f"(place the wells BEFORE the grove so it skips them, with a well keep-out wide enough for the canopy)",
            )
        if dwell:
            check(
                "settlement_has_wells",
                len(wells) >= max(1, round(len(dwell) / 25)),
                f"a {scale} of {len(dwell)} households has only {len(wells)} communal well(s) - every settlement "
                f"keeps wells (about one per 20-25 households); scatter them among the dwellings with s.place_wells(...)",
            )
            lines = [c["poly"] for c in M.get("channels", [])] + [st["poly"] for st in M.get("streams", [])] + ([M["moat"]] if M.get("moat") else [])
            pond = M.get("pond")
            REACH = round(760 / float(meta.get("ftpx") or meta.get("ft_per_px") or 2.0))  # ~760 ft, in px at this map's scale (380 at 2 ft/px)
            dry = []
            for h in dwell:
                d = min((math.hypot(h["x"] - wl["x"], h["y"] - wl["y"]) for wl in wells), default=1e9)
                for ln in lines:
                    d = min([d] + [seg_dist(h["x"], h["y"], ln[i], ln[i + 1]) for i in range(len(ln) - 1)])
                if pond:
                    d = min(d, abs(math.hypot(h["x"] - pond[0], h["y"] - pond[1]) - max(pond[2], pond[3])))
                if d > REACH:
                    dry.append((round(h["x"]), round(h["y"])))
            check(
                "settlement_dwellings_watered",
                not dry,
                f"{len(dry)} household(s) more than {REACH}px from any water source - a well, or an irrigation channel / pond / stream / moat: {dry[:4]} - put a well within reach",
            )

            # A shrine/temple set sufficiently APART from the village keeps its OWN WELL close by for purification
            # (temizu): too far to walk to the village's shared wells, it needs a dedicated draw-point right beside
            # it - and specifically a WELL, not just any water (a ditch/pond is not an ablution source). A shrine
            # AMONG or near the houses shares the village wells (exempt). "Set apart" = the nearest dwelling is more
            # than SHRINE_FAR px away; "close by" = a well within SHRINE_WELL_NEAR px.
            SHRINE_FAR, SHRINE_WELL_GAP = 150, 70
            shrine_hill = M.get("hill")
            wellless = []
            for r in M.get("religious", []):
                if shrine_hill and in_ellipse(r["x"], r["y"], shrine_hill):
                    continue  # a hilltop/mountain shrine draws from a spring/basin, not a dug well
                if min((math.hypot(r["x"] - b["x"], r["y"] - b["y"]) for b in dwell), default=1e9) <= SHRINE_FAR:
                    continue  # among/near the houses -> shares the village wells
                near_well = min((math.hypot(r["x"] - wl["x"], r["y"] - wl["y"]) for wl in wells), default=1e9)
                if near_well - 0.5 * math.hypot(r["w"], r["h"]) > SHRINE_WELL_GAP:  # gap to the hall's EDGE (a big monastery's well sits further out)
                    wellless.append((round(r["x"]), round(r["y"])))
            check(
                "remote_shrine_has_own_well",
                not wellless,
                f"{len(wellless)} shrine/temple(s) set apart from the village (>{SHRINE_FAR}px from any house) with no "
                f"well beside them - a remote shrine keeps its own well for ablution: {wellless[:4]}",
            )

        # HARVEST PROCESSING (per-farmstead): a rice settlement threshes and dries its crop at the
        # FARMHOUSE, not on one communal floor. Each household works its cut rice on its own small tamped
        # earthen YARD (niwa) beside the house, with a little drying rack. Historically Japan had no central
        # village threshing ground; processing was household-scale. A MINORITY of farmsteads show a yard
        # (~1/3, matching the ~30% that carry a shed); the rest imply it / run off-frame. Applies wherever
        # there are farmhouses - town/village/hamlet AND a city's farm rings (in-wall district + outside).
        if scale in ("town", "village", "hamlet", "city"):
            fields_ol = [fdef["outline"] for fdef in fields]
            yards = M.get("threshing_yards", [])
            occ_h = [h for h in houses if h.get("kind") != "abandoned" and h.get("role") != "headman"]
            # the work yard (niwa) was UNIVERSAL: EVERY farmhouse threshed and dried its own rice on its own
            # yard, so EVERY farmhouse must have one (a firm 100%). The generator guarantees this by making
            # the yard integral to farmstead placement - a house is only sited where its yard also fits
            # (nudging it as needed) - so a farmhouse without a yard is a generator bug, not a density limit.
            without = [(round(h["x"]), round(h["y"])) for h in occ_h if not any(t["of"][0] == h["x"] and t["of"][1] == h["y"] for t in yards)]
            check(
                "harvest_yards_present",
                not without,
                f"a {scale} threshes and dries its rice at the farmstead, and the work yard was universal: "
                f"{len(without)} of {len(occ_h)} farmhouses have NO threshing/drying yard {without[:3]} - every "
                f"farmhouse must have one (placement makes the yard integral to the farmstead)",
            )
            # the yard is the farmstead's own dry work apron, SMALLER than the house it serves (not a
            # second dwelling). Each yard records `of` = its parent farmhouse center.
            hmap = {(round(h["x"]), round(h["y"])): h["w"] * h["h"] for h in houses}
            oversize = [(round(t["x"]), round(t["y"])) for t in yards if t["w"] * t["h"] >= hmap.get((round(t["of"][0]), round(t["of"][1])), 0)]
            check("harvest_yards_smaller_than_farmhouse", not oversize, f"threshing yard(s) are not smaller than their farmhouse: {oversize[:3]} - the niwa is a small dry apron beside the house")
            # the yard is the maeniwa - the SOUTH-facing front work yard. Rice must dry in the SUN and
            # minka face south, so the yard sits on the house's south/front side (or, if the paddy blocks
            # that, a side), but NEVER the shady NORTH back. +y is south here, so a yard must not sit
            # meaningfully north of (above) its own farmhouse center (`of[1]`).
            shady = [(round(t["x"]), round(t["y"])) for t in yards if t["y"] < t["of"][1] - 5]
            check(
                "harvest_yards_on_sunny_side",
                not shady,
                f"threshing yard(s) sit on the shady NORTH/back side of their farmhouse: {shady[:3]} - the niwa is the "
                f"south-facing front work yard (rice must dry in the sun), so it belongs on the house's south/front side",
            )
            # the yard is a DRY tamped floor: its whole footprint must stay out of the flooded paddies.
            in_paddy = []
            for t in yards:
                fc = rect_corners(_struct_rect(t))
                if any(
                    any(point_in_poly(px, py, ol) for px, py in fc)
                    or any(point_in_poly(vx, vy, fc) for vx, vy in ol)
                    or any(segments_cross(fc[e], fc[(e + 1) % 4], ol[k], ol[(k + 1) % len(ol)]) for e in range(4) for k in range(len(ol)))
                    for ol in fields_ol
                ):
                    in_paddy.append((round(t["x"]), round(t["y"])))
            check(
                "harvest_yards_clear_of_paddies",
                not in_paddy,
                f"threshing yard footprint(s) sit IN a flooded paddy: {in_paddy[:3]} - the yard is dry ground; keep its whole footprint clear of every field outline",
            )
            # the yard abuts its OWN farmhouse (intentional, overlap-exempt) but must touch NOTHING else -
            # not another farmhouse, a shop, a civic building, or a kura (parent matched by `of`). This is
            # the dedicated guard the exemption would otherwise skip - a feature placed before the yard
            # (a shop) OR after it (a hand-placed building) must not end up under it.
            others = [s for k in _OVERLAP_STRUCTS for s in M.get(k, [])] + M.get("storehouses", []) + M.get("merchant_estates", [])
            fouled = []
            for t in yards:
                tc = rect_corners(_struct_rect(t))
                par = (round(t["of"][0]), round(t["of"][1]))
                for s in others:
                    if (round(s["x"]), round(s["y"])) == par:
                        continue
                    if abs(s["x"] - t["x"]) + abs(s["y"] - t["y"]) > 140:
                        continue
                    if sat_overlap(tc, rect_corners(_struct_rect(s))):
                        fouled.append((round(t["x"]), round(t["y"])))
                        break
            check("harvest_yards_clear_of_structures", not fouled, f"threshing yard(s) overlap a building other than their own farmhouse: {fouled[:3]} - a yard abuts only its own house")

            # ATTACHED KURA STOREHOUSE: a farm's fireproof grain store is drawn as an annex on the house's back
            # wall, so every one that exists must ABUT a farmhouse - never float detached in the courtyard (that
            # reads as a shed nobody owns). ~30% of farms carry one (a wealth marker), so it is not REQUIRED, but
            # any present must be attached. Guards the regression where a move-procedure strands the shed.
            sheds = M.get("farm_sheds", [])
            if sheds and M.get("houses"):
                stranded = []
                for sd in sheds:
                    h = min(M["houses"], key=lambda h: math.hypot(sd["x"] - h["x"], sd["y"] - h["y"]))
                    if math.hypot(sd["x"] - h["x"], sd["y"] - h["y"]) > 0.5 * math.hypot(h["w"], h["h"]) + 0.5 * math.hypot(sd["w"], sd["h"]) + 10:
                        stranded.append((round(sd["x"]), round(sd["y"])))
                check(
                    "farm_sheds_attached",
                    not stranded,
                    f"{len(stranded)} farm storehouse(s) detached from any farmhouse at {stranded[:4]} - a kura is an "
                    f"annex on the house's back wall; draw it WITH the house so a move cannot strand it",
                )

            # DOORYARD KITCHEN GARDEN (saien). Every farmstead kept a small intensive vegetable plot for
            # the household's daily greens - as universal as the work yard, so EVERY farmhouse must have one
            # (a firm 100%, guaranteed by making the garden integral to farmstead placement). It sits on a
            # sunny SIDE (preferring the east kitchen end), NOT the north shade and NOT the south front (the
            # threshing apron's ground), is SMALLER than the farmhouse, stays on DRY ground off the paddies,
            # and abuts only its own house. (Why a side, not the south front: settlements.md "Dooryard gardens".)
            gardens = M.get("gardens", [])
            g_without = [(round(h["x"]), round(h["y"])) for h in occ_h if not any(gd["of"][0] == h["x"] and gd["of"][1] == h["y"] for gd in gardens)]
            check(
                "gardens_present",
                not g_without,
                f"a {scale} farmstead kept a dooryard kitchen garden for the household's vegetables, and it "
                f"was universal: {len(g_without)} of {len(occ_h)} farmhouses have NO garden {g_without[:3]} - "
                f"every farmhouse must have one (placement makes the garden integral to the farmstead)",
            )
            g_oversize = [(round(gd["x"]), round(gd["y"])) for gd in gardens if gd["w"] * gd["h"] >= hmap.get((round(gd["of"][0]), round(gd["of"][1])), 0)]
            check("gardens_smaller_than_farmhouse", not g_oversize, f"kitchen garden(s) are not smaller than their farmhouse: {g_oversize[:3]} - the saien is a small dooryard plot, not a field")
            g_shady = [(round(gd["x"]), round(gd["y"])) for gd in gardens if gd["y"] < gd["of"][1] - 5]
            check(
                "gardens_on_sunny_side",
                not g_shady,
                f"kitchen garden(s) sit on the shady NORTH/back side of their farmhouse: {g_shady[:3]} - the saien belongs on a SUNNY side (the east kitchen end, or west), never the cold north back",
            )
            g_in_paddy = []
            for gd in gardens:
                fc = rect_corners(_struct_rect(gd))
                if any(
                    any(point_in_poly(px, py, ol) for px, py in fc)
                    or any(point_in_poly(vx, vy, fc) for vx, vy in ol)
                    or any(segments_cross(fc[e], fc[(e + 1) % 4], ol[k], ol[(k + 1) % len(ol)]) for e in range(4) for k in range(len(ol)))
                    for ol in fields_ol
                ):
                    g_in_paddy.append((round(gd["x"]), round(gd["y"])))
            check(
                "gardens_clear_of_paddies",
                not g_in_paddy,
                f"kitchen garden footprint(s) sit IN a flooded paddy: {g_in_paddy[:3]} - the saien is dry ground; keep its whole footprint clear of every field outline",
            )
            # ... and off the IRRIGATION LINES too: the feeder CHANNELS, the in-field/drain DITCHES, and any
            # STREAM. A raised-bed vegetable plot cannot sit in a running ditch; `gardens_clear_of_paddies`
            # covers the flooded basin, but a feeder channel or the drain ditch threads the DRY village margin
            # where the gardens are, so test each garden footprint against every water polyline (its own
            # half-width + a little). Same full-footprint test used for structures vs a channel/stream.
            waterlines = (
                [(c["poly"], c.get("w", 2.5) / 2 + 3) for c in M.get("channels", [])]
                + [(d["poly"], d.get("w", 7) / 2 + 3) for d in M.get("field_ditches", [])]
                + [(st["poly"], st.get("w", 9) / 2 + 3) for st in M.get("streams", [])]
            )
            g_on_water = []
            for gd in gardens:
                gc = rect_corners(_struct_rect(gd))
                for wp, whw in waterlines:
                    if (
                        any(seg_dist(cx, cy, wp[k], wp[k + 1]) < whw for cx, cy in gc for k in range(len(wp) - 1))
                        or any(point_in_poly(wx, wy, gc) for wx, wy in wp)
                        or any(segments_cross(wp[k], wp[k + 1], gc[e], gc[(e + 1) % 4]) for k in range(len(wp) - 1) for e in range(4))
                    ):
                        g_on_water.append((round(gd["x"]), round(gd["y"])))
                        break
            check(
                "gardens_clear_of_channels",
                not g_on_water,
                f"kitchen garden(s) overlap an irrigation channel/ditch: {g_on_water[:3]} - a raised-bed saien sits on dry ground, never in a running feeder channel, field ditch, or stream",
            )
            g_fouled = []
            for gd in gardens:
                gc = rect_corners(_struct_rect(gd))
                par = (round(gd["of"][0]), round(gd["of"][1]))
                for s in others:
                    if (round(s["x"]), round(s["y"])) == par:
                        continue
                    if abs(s["x"] - gd["x"]) + abs(s["y"] - gd["y"]) > 140:
                        continue
                    if sat_overlap(gc, rect_corners(_struct_rect(s))):
                        g_fouled.append((round(gd["x"]), round(gd["y"])))
                        break
            check("gardens_clear_of_structures", not g_fouled, f"kitchen garden(s) overlap a building other than their own farmhouse: {g_fouled[:3]} - a garden abuts only its own house")
            # the garden and the farmhouse's STOREHOUSE/shed must never overlap - the shed sits on a wall the
            # garden does not use (west for a dispersed farm, the shaded north for a nucleated one). The shed is
            # a recorded annex (M['farm_sheds']), so read its actual footprint straight from there.
            sheds = M.get("farm_sheds", [])
            g_on_shed = []
            for gd in gardens:
                gc = rect_corners(_struct_rect(gd))
                for sd in sheds:
                    if abs(sd["x"] - gd["x"]) + abs(sd["y"] - gd["y"]) > 120:
                        continue
                    if sat_overlap(gc, rect_corners(sd)):
                        g_on_shed.append((round(gd["x"]), round(gd["y"])))
                        break
            check(
                "gardens_clear_of_sheds",
                not g_on_shed,
                f"kitchen garden(s) overlap a farmhouse's storehouse/shed: {g_on_shed[:3]} - the shed sits on the "
                f"house's WEST side and the garden on a sunny (east-preferred) side, so the two must never collide",
            )

            # A dooryard bed and a threshing yard were HAND-worked plots bent to paths and soil, not surveyed
            # rectangles - the generator draws each as a slightly-irregular 4-sided quad (a garden more irregular,
            # a swept work yard near-square). Validate the SHAPE it records: every garden/yard with a `poly` must
            # carry exactly 4 vertices, be non-degenerate (real area), and stay INSCRIBED in its recorded w x h
            # bounds (the jitter only pulls corners INWARD, so a poly poking outside its rect means the overlap
            # checks - which use that rect - were cleared against the wrong footprint). WHY quads: settlements.md
            # "Dooryard kitchen gardens" / "Threshing yards" (irregular-plot grounding).
            bad_quad = []
            for pl in gardens + yards:
                pg = pl.get("poly")
                if pg is None:
                    continue  # legacy rect-only record (dispersed maps predate poly)
                hw, hh = pl["w"] / 2 + 0.6, pl["h"] / 2 + 0.6  # small tolerance for rounding
                inside = all(abs(px - pl["x"]) <= hw and abs(py - pl["y"]) <= hh for px, py in pg)
                if len(pg) != 4 or poly_area(pg) < 0.20 * pl["w"] * pl["h"] or not inside:
                    bad_quad.append((round(pl["x"]), round(pl["y"])))
            check(
                "garden_plots_are_quads",
                not bad_quad,
                f"garden/yard footprint(s) are not valid inscribed 4-gons: {bad_quad[:3]} - each is a slightly-"
                f"irregular quadrilateral (4 vertices, real area) that stays within its reserved w x h rect",
            )

            # GARDEN AREA is held to a HISTORICAL band. Unlike the house/yard (drawn oversized against the
            # fields for legibility), a dooryard kitchen garden at 1 px = 2 ft is near its TRUE size, so its area
            # is a real quantity we can check against the ground a household could hand-work. The saien is the
            # small intensive daily-greens bed by the kitchen (the bulk vegetable growing was out in the hatake
            # dry fields, not here): historically a few tsubo up to ~1.4 se - roughly 10-140 m^2 (1 tsubo = 3.31
            # m^2; 1 se = 30 tsubo ~ 99 m^2). We sum ALL of a household's garden beds (a fragmented plot is still
            # one household's garden) and require the TOTAL in that band. WHY the numbers: settlements.md "Dooryard
            # kitchen gardens" (area grounding). Scale override via meta.ft_per_px for any non-standard map.
            ft_per_px = float(meta.get("ftpx") or meta.get("ft_per_px") or 2.0)  # the map's real scale (village 2, hamlet 1)
            m2_per_px2 = (ft_per_px * 0.3048) ** 2  # ft/px -> m per px, squared -> m^2 per px^2
            GARDEN_M2_MIN, GARDEN_M2_MAX = 10.0, 140.0
            by_house: dict[tuple[int, int], float] = {}
            for gd in gardens:
                pg = gd.get("poly")
                a_px = poly_area(pg) if pg else gd["w"] * gd["h"]
                key = (round(gd["of"][0]), round(gd["of"][1]))
                by_house[key] = by_house.get(key, 0.0) + a_px
            g_area_bad = [(hx, hy, round(a_px * m2_per_px2)) for (hx, hy), a_px in by_house.items() if not (GARDEN_M2_MIN <= a_px * m2_per_px2 <= GARDEN_M2_MAX)]
            check(
                "garden_area_within_norms",
                not g_area_bad,
                f"household kitchen-garden total area out of the historical band "
                f"[{GARDEN_M2_MIN:.0f}-{GARDEN_M2_MAX:.0f} m^2]: {g_area_bad[:3]} (x, y, m^2) - a saien is the small "
                f"intensive daily-greens bed by the kitchen, ~a few tsubo up to ~1.4 se; bigger reads as a field, "
                f"tinier as no garden at all",
            )

            # HOMESTEAD GROVE (yashikirin) - the farmhouse windbreak. A dense L-BELT of shelter trees on the
            # WINDWARD side(s) of the house (one record per belt ARM), blocking the cold prevailing wind while
            # leaving the SUNNY lee open. Default windward NW: the East Asian winter monsoon blows NW across
            # China and Japan alike, so N+W is windward, S/E the sheltered sunny side - a map keys it off its
            # own geography with meta(windward=...). The grove is NEAR-UNIVERSAL (meta.grove_prevalence) and
            # the LARGEST homestead appurtenance - bigger than the house. We gate GEOMETRY per arm (windward,
            # off the paddy, off other buildings), the typical grove's SCALE (groves_are_substantial), a
            # presence FLOOR scaled to the knob, and (city) that NO intramural farm carries one. WHY (the ~30-40
            # tree stand, the windward rule, the firewood/timber/bamboo it gave): settlements.md "Homestead groves".
            groves = M.get("groves", [])
            grove_of = {(round(gv["of"][0]), round(gv["of"][1])) for gv in groves}  # distinct farms with a grove
            WINDV = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0), "NW": (-1, -1), "NE": (1, -1), "SW": (-1, 1), "SE": (1, 1)}
            windward = str(meta.get("windward", "NW")).upper().strip()
            wvx, wvy = WINDV.get(windward, (-1, -1))
            g_lee = [(round(gv["x"]), round(gv["y"])) for gv in groves if (gv["x"] - gv["of"][0]) * wvx + (gv["y"] - gv["of"][1]) * wvy <= 0]
            check(
                "groves_on_windward_side",
                not g_lee,
                f"homestead grove(s) sit on the LEE/sunny side of their farmhouse, not the windward {windward}: "
                f"{g_lee[:3]} - a yashikirin shelters the windward wall (default N/W) and leaves the sunny lee open",
            )
            g_in_paddy = [(round(gv["x"]), round(gv["y"])) for gv in groves if any(point_in_poly(gv["x"], gv["y"], ol) for ol in fields_ol)]
            check(
                "groves_clear_of_paddies",
                not g_in_paddy,
                f"homestead grove(s) sit squarely IN a flooded paddy (center over water): {g_in_paddy[:3]} - the "
                f"windbreak HUGS the bund (abutting/overlapping the field edge is correct) but must not be planted "
                f"out in the paddy itself",
            )
            gr_fouled = []
            for gv in groves:
                gci = dict(gv)
                gci["w"] = gv["w"] * 0.7
                gci["h"] = gv["h"] * 0.7  # inset: tolerate abutting
                gc = rect_corners(_struct_rect(gci))
                par = (round(gv["of"][0]), round(gv["of"][1]))
                for s in others:
                    if (round(s["x"]), round(s["y"])) == par:
                        continue
                    if abs(s["x"] - gv["x"]) + abs(s["y"] - gv["y"]) > 140:
                        continue
                    if sat_overlap(gc, rect_corners(_struct_rect(s))):
                        gr_fouled.append((round(gv["x"]), round(gv["y"])))
                        break
            check("groves_clear_of_structures", not gr_fouled, f"homestead grove(s) overlap a building other than their own farmhouse: {gr_fouled[:3]} - a grove abuts only its own house")
            # SUN: a threshing yard dries rice in the SOUTHERN sun, so no grove may sit in the strip directly
            # SOUTH of a yard (a neighbor's grove there would shade it). A grove is N/W of its OWN house, far
            # from its own yard's southern corridor, so this only catches a grove shading a NEIGHBOR's yard.
            shaded = []
            for yd in yards:
                cyx, cyy = yd["x"], yd["y"] + yd["h"] / 2 + 11  # the ~22px sun-corridor just south of the yard
                if any(abs(gv["x"] - cyx) < (gv["w"] + yd["w"]) / 2 and abs(gv["y"] - cyy) < (gv["h"] + 22) / 2 for gv in groves):
                    shaded.append((round(yd["x"]), round(yd["y"])))
            check(
                "yards_unshaded_by_groves",
                not shaded,
                f"threshing yard(s) {shaded[:3]} have a grove in the sun-corridor just to their SOUTH - it would shade the drying ground; keep groves out of the strip south of any yard",
            )
            # SAME sun rule for the COMMUNAL fengshui trees: no village-grove CLUMP may sit in the southern sun-
            # corridor of a threshing yard OR a kitchen garden (both need the drying/growing sun from the south).
            # The scatter records its real clumps, so test those, not the bounding poly. WHY: settlements.md 'Village windbreak'.
            vg_clumps = [(cx, cy, g.get("r", 6)) for g in M.get("village_groves", []) for cx, cy in g.get("clumps", [])]
            vg_shaded = []
            for f in yards + gardens:
                se = f["y"] + f["h"] / 2
                if any(abs(cx - f["x"]) < f["w"] / 2 + r and se - r < cy < se + 22 + r for cx, cy, r in vg_clumps):
                    vg_shaded.append((round(f["x"]), round(f["y"])))
            check(
                "village_trees_unshade_yards_and_gardens",
                not vg_shaded,
                f"a village-grove tree sits in the southern sun-corridor of yard/garden(s) {vg_shaded[:3]} - it would "
                f"shade the drying/growing ground; keep the scatter + belts out of the strip south of any yard or garden",
            )
            # EAST SUN (option): a kitchen garden on a house's lee/EAST side loses its MORNING sun if a neighbor's
            # grove arm (or a copse) stands hard against its east. Where a small SOUTHWARD nudge into open ground
            # would clear it (the tree then falls to the garden's NE), the placement takes it (_relax_gardens_south).
            # This fires ONLY on an AVOIDABLE case - a garden still east-shaded though a clear south-shift existed -
            # so a garden genuinely boxed in to the south (paddy/lane/neighbor) is exempt. WHY: settlements.md 'gardens'.
            # scoped to the BUNDLE-path farmsteads (villages + to-scale hamlets), where _relax_gardens_south runs;
            # a town/city places its outside farms on the legacy path (no south-nudge), so the rule does not apply.
            if groves and meta.get("toscale", scale == "village"):
                _band = 22
                _hh = {(round(h["x"]), round(h["y"])): h["h"] for h in houses}
                _lanes = M.get("lanes", [])
                _bog = [m["poly"] for m in M.get("marshes", []) if m.get("role") != "pond_fringe" and m.get("poly")]
                _water = [c["poly"] for c in M.get("channels", [])] + [st["poly"] for st in M.get("streams", [])]
                _fol = [f["outline"] for f in M.get("fields", []) if f.get("outline")]
                _hill, _pond = M.get("hill"), M.get("pond")

                def _e_iv(ge: float, own: tuple[float, ...]) -> list[tuple[float, float]]:
                    iv = [(gv["y"] - gv["h"] / 2, gv["y"] + gv["h"] / 2) for gv in groves if tuple(gv.get("of", [])) != own and ge - 2 <= gv["x"] - gv["w"] / 2 < ge + _band]
                    iv += [(cy - r, cy + r) for cx, cy, r in vg_clumps if ge - 2 <= cx - r < ge + _band]
                    return iv

                def _shaded(lane: tuple[float, float], iv: list[tuple[float, float]]) -> bool:
                    return any(a < lane[1] and lane[0] < b for a, b in iv)

                def _bed_clear(bx: float, by: float, bw: float, bh: float, own: tuple[float, ...]) -> bool:
                    box = (bx - bw / 2, by - bh / 2, bx + bw / 2, by + bh / 2)
                    for h in houses:
                        if (round(h["x"]), round(h["y"])) != (round(own[0]), round(own[1])) and abs(bx - h["x"]) < (bw + h["w"]) / 2 and abs(by - h["y"]) < (bh + h["h"]) / 2:
                            return False
                    for s in yards + groves + gardens + M.get("farm_sheds", []) + M.get("byres", []):
                        if tuple(s.get("of", [])) == own:  # skip the garden's OWN yard/grove/beds/shed
                            continue
                        if abs(bx - s["x"]) < (bw + s["w"]) / 2 and abs(by - s["y"]) < (bh + s["h"]) / 2:
                            return False
                    if any(_box_hits_poly(box, ol) for ol in _fol) or any(_box_hits_poly(box, p) for p in _bog):
                        return False
                    for ln in _lanes:
                        p = ln["pts"]
                        if any(seg_dist(bx, by, p[k], p[k + 1]) < ln.get("w", 6) / 2 + 2 for k in range(len(p) - 1)):
                            return False
                    for wp in _water:
                        if any(seg_dist(bx, by, wp[k], wp[k + 1]) < 6 for k in range(len(wp) - 1)):
                            return False
                    return not ((_hill and in_ellipse(bx, by, _hill)) or (_pond and in_ellipse(bx, by, _pond)))

                east_bad = []
                for gd in gardens:
                    gx, gy, gw, gh = gd["x"], gd["y"], gd["w"], gd["h"]
                    own = tuple(gd.get("of", []))
                    iv = _e_iv(gx + gw / 2, own)
                    if not _shaded((gy - gh / 2, gy + gh / 2), iv):
                        continue  # not currently east-shaded
                    hh = _hh.get((round(own[0]), round(own[1])), gh) if own else gh
                    maxshift, dy = gh + hh + 6, 4
                    while dy <= maxshift:
                        if not _shaded((gy + dy - gh / 2, gy + dy + gh / 2), iv) and _bed_clear(gx, gy + dy, gw, gh, own):
                            east_bad.append((round(gx), round(gy)))  # a clear south-shift existed -> avoidable
                            break
                        dy += 4
                check(
                    "gardens_unshaded_from_east",
                    not east_bad,
                    f"kitchen garden(s) {east_bad[:4]} sit with a tree hard against their EAST (losing the morning sun) "
                    f"though a small SOUTHWARD shift into open ground would clear it - nudge the garden south of the "
                    f"tree (the placement's _relax_gardens_south does this; a garden truly boxed in south is exempt)",
                )
            # SCALE: the typical grove must read as the LARGEST homestead appurtenance - a real stand of dozens
            # of trees, not a clump. The median grove's total footprint (its arms) must be >= ~0.75x the house
            # it shelters (the spacious farms run well above; a single-arm grove on a cramped farm pulls the
            # median but stays substantial). This catches a regression that shrinks groves back to a few trees.
            if len(grove_of) >= 6:
                hsz = {(round(h["x"]), round(h["y"])): h["w"] * h["h"] for h in houses}
                gsz: dict[tuple[int, int], float] = {}
                for gv in groves:
                    gk = (round(gv["of"][0]), round(gv["of"][1]))
                    gsz[gk] = gsz.get(gk, 0) + gv["w"] * gv["h"]
                ratios = sorted(a / hsz[gk] for gk, a in gsz.items() if gk in hsz and hsz[gk])
                med = ratios[len(ratios) // 2]
                check(
                    "groves_are_substantial",
                    med >= 0.5,
                    f"the typical homestead grove is too small (median {med:.2f}x its house) - the spacious farms must "
                    f"carry a real stand (a yashikirin is the LARGEST homestead feature); small clumps on cramped farms "
                    f"are fine, but a median below half the house means groves shrank back to a few trees everywhere",
                )
            # VISIBLE: the dooryard garden must not be buried under a grove (the homestead solver spaces the
            # garden to the LEE side and the grove to the windward, so they never stack). A garden substantially
            # overlapped by a grove arm is a regression. WHY: settlements.md "Homestead groves".
            g_buried = [
                (round(gd["x"]), round(gd["y"]))
                for gd in gardens
                if any(abs(gd["x"] - gv["x"]) < (gd["w"] + gv["w"]) / 2 - 3 and abs(gd["y"] - gv["y"]) < (gd["h"] + gv["h"]) / 2 - 3 for gv in groves)
            ]
            check(
                "gardens_clear_of_groves",
                not g_buried,
                f"kitchen garden(s) {g_buried[:3]} sit under a homestead grove - the solver spaces the garden to the LEE side and the grove to the windward; they must not overlap",
            )
            # WHERE POSSIBLE: a grove is drawn on EVERY farmhouse that has windward room - the yashikirin ringed
            # every dispersed farmstead - so a grove-LESS farm must be one whose windward side is genuinely blocked
            # (a paddy, a neighbor, or the sun-corridor south of a yard). If a grove-less farm has CLEAR windward
            # room, the generator omitted a grove it could have placed. Replaces the old blunt presence floor.
            if scale in ("town", "village", "hamlet") and len(houses) >= 10 and not meta.get("nucleated"):
                WF = {
                    "N": [((0, -1), 0)],
                    "S": [((0, 1), 0)],
                    "E": [((1, 0), 0)],
                    "W": [((-1, 0), 0)],
                    "NW": [((0, -1), -1), ((-1, 0), 0)],
                    "NE": [((0, -1), 1), ((1, 0), 0)],
                    "SW": [((0, 1), -1), ((-1, 0), 0)],
                    "SE": [((0, 1), 1), ((1, 0), 0)],
                }
                avoid = others + gardens + yards + M.get("manors", []) + M.get("religious", [])
                corridors = [c for c in [M.get("lane"), M.get("road")] if c]
                corridors += [(c.get("poly", c) if isinstance(c, dict) else c) for c in M.get("channels", [])]
                corridors += [(s.get("poly", s) if isinstance(s, dict) else s) for s in M.get("streams", [])]
                Wm, Hm = meta.get("W", 1820), meta.get("H", 1180)

                def min_clump(hh_: dict[str, Any], fdx: float, fdy: float, perp: float) -> tuple[float, float, float, float]:
                    hx, hy, hw, hz = hh_["x"], hh_["y"], hh_["w"], hh_["h"]
                    dm = 13 * hw / 44.0  # minimal-clump depth (44 = base house width / bscale)
                    if fdy:
                        return hx + perp * dm / 2, hy + fdy * (hz / 2 + dm / 2 + 1.5), (hw + dm) * 0.5, dm
                    return hx + fdx * (hw / 2 + dm / 2 + 1.5), hy, dm, hz * 0.5

                # B is a CONSERVATIVE margin: the check only claims "room" when the windward side is CLEARLY
                # open (room + B px), so it fires on a gross omission (a farm with plenty of space and no grove)
                # but tolerates the borderline cases where this check can't perfectly mirror the placement test.
                B = 7

                def clump_clear(cx: float, cy: float, cw: float, ch: float, par: tuple[int, int]) -> bool:
                    if cx < 55 or cx > Wm - 55 or cy < 88 or cy > Hm - 26:
                        return False
                    rc = rect_corners({"x": cx, "y": cy, "w": cw, "h": ch, "rot": 0})
                    for ol in fields_ol:
                        n = len(ol)
                        if (
                            point_in_poly(cx, cy, ol)
                            or edge_dist(cx, cy, ol) < 14 + B  # mirror settlement._in_blocked
                            or any(point_in_poly(px, py, ol) for px, py in rc)
                            or any(point_in_poly(vx, vy, rc) for vx, vy in ol)
                            or any(segments_cross(rc[e], rc[(e + 1) % 4], ol[k], ol[(k + 1) % n]) for e in range(4) for k in range(n))
                        ):
                            return False
                    for s in avoid:
                        if (round(s["x"]), round(s["y"])) == par:
                            continue
                        if abs(cx - s["x"]) < (cw + s["w"]) / 2 + B and abs(cy - s["y"]) < (ch + s["h"]) / 2 + B:
                            return False
                    for yd in yards:
                        if abs(cx - yd["x"]) < (cw + yd["w"]) / 2 + B and abs(cy - (yd["y"] + yd["h"] / 2 + 11)) < (ch + 22) / 2 + B:
                            return False
                    return all(not (len(poly) >= 2 and any(seg_dist(cx, cy, poly[k], poly[k + 1]) < 20 + B for k in range(len(poly) - 1))) for poly in corridors)

                omitted = []
                for hh_ in houses:
                    if hh_.get("role") == "headman" or hh_.get("kind") == "abandoned":
                        continue
                    par = (round(hh_["x"]), round(hh_["y"]))
                    if par in grove_of:
                        continue
                    if any(clump_clear(*min_clump(hh_, fdx, fdy, perp), par) for (fdx, fdy), perp in WF.get(windward, WF["NW"])):
                        omitted.append(par)
                check(
                    "groves_where_possible",
                    not omitted,
                    f"farm(s) {omitted[:4]} have clear windward room but no grove - a yashikirin is drawn on every farm "
                    f"that can host one; only a paddy/neighbor/yard-shaded windward side may leave a farm grove-less",
                )

            # NUCLEATED villages shelter behind a COMMUNAL fengshui WINDBREAK (风水林), NOT per-house groves: a
            # dense grove belt on the high WINDWARD back edge (the winter-monsoon wall + sacred back-village
            # grove), a smaller cluster at the low water-mouth entrance, and scattered bamboo/fruit copses. So a
            # nucleated village is NOT required to grove every farm (groves_where_possible is skipped above for
            # meta.nucleated); instead it MUST carry the village windbreak, on the windward side, off the paddies.
            # WHY (the fengshui-forest research - ~2 groves/village, a ~1-2 ha back grove at ~3,400 stems/ha, a
            # water-mouth cluster, kept off the crops and the road): settlements.md 'Village windbreak'.
            vgroves = M.get("village_groves", [])
            if meta.get("nucleated") and len(houses) >= 10:
                windbreaks = [g for g in vgroves if g.get("role") == "windbreak"]
                check(
                    "village_windbreak_present",
                    bool(windbreaks),
                    "a nucleated village shelters behind a COMMUNAL windbreak (a fengshui back-village grove), but "
                    "no role='windbreak' village grove is present - add s.village_grove(..., role='windbreak') on the "
                    "high windward edge",
                )
                # the belt backs the cluster on the WINDWARD/high side (default NW) - its centroid must lie
                # windward of the house-cluster centroid, so the wall faces the cold wind, not the sunny field side
                ccx = sum(h["x"] for h in houses) / len(houses)
                ccy = sum(h["y"] for h in houses) / len(houses)
                lee = [(round(g["x"]), round(g["y"])) for g in windbreaks if (g["x"] - ccx) * wvx + (g["y"] - ccy) * wvy <= 0]
                check(
                    "village_windbreak_on_windward_side",
                    not lee,
                    f"the village windbreak sits on the LEE/sunny side of the cluster, not the windward {windward}: "
                    f"{lee[:2]} - the back-village grove shelters the high windward edge and leaves the sunny field side open",
                )
            # every village grove (of any role) is DRY woodland - its center must not sit in a flooded paddy
            vg_in_paddy = [(round(g["x"]), round(g["y"])) for g in vgroves if any(point_in_poly(g["x"], g["y"], ol) for ol in fields_ol)]
            check(
                "village_groves_clear_of_paddies",
                not vg_in_paddy,
                f"village grove(s) sit IN a flooded paddy (center over water): {vg_in_paddy[:3]} - the fengshui "
                f"windbreak stands on dry ground at the cluster's back and entrance, never out in the paddy",
            )

            # A grove clump (a tree blob, radius r) may abut a farmstead - trees stand right up against a house
            # wall - but it must NOT OVERLAP a building/yard/garden footprint (a tree drawn ON the roof reads
            # wrong). Both the placement (the village_grove keep-out uses the clump's FULL radius) and this check
            # enforce it. The nominal blob radius is the measure; canopy leaves spilling a few px onto the eaves
            # are "adjacent," which is fine. Covers the whole homestead: house, threshing yard, kitchen garden,
            # draft byre, farm shed. WHY (trees beside, not on, the buildings): settlements.md 'Village windbreak'.
            _clm = [(cx, cy, g.get("r", 6)) for g in vgroves for cx, cy in g.get("clumps", [])]
            on_struct = []
            for k in ("houses", "threshing_yards", "gardens", "byres", "farm_sheds"):
                for o in M.get(k, []):
                    rect = _struct_rect(o)
                    for cx, cy, r in _clm:
                        if pt_to_rect(cx, cy, rect) < r - 1:  # real penetration (just-touching is allowed)
                            on_struct.append((k, round(o["x"]), round(o["y"])))
                            break
            check(
                "grove_clumps_clear_of_structures",
                not on_struct,
                f"{len(on_struct)} farmstead footprint(s) have a grove-clump tree drawn OVER them: {on_struct[:4]} - "
                f"a copse/windbreak clump may stand right beside a house but never ON it; widen the village_grove "
                f"keep-out to the clump's full radius so the blob settles into the open ground beside the buildings",
            )

            # FUEL-AND-FODDER COMMONS - the degraded open grazing/scrub on the far side, BEYOND the back-grove.
            # South China's hills were stripped for fuel/timber over a millennium (open pine + grass + erosion),
            # so past the protected grove is NON-ARABLE waste: coarse grass, brush, scraggly pines - a commons,
            # not a field, and never the flooded paddy. The land toposequence is village -> back-grove -> fuel
            # commons, so the commons sits on the WINDWARD/high side and FURTHER out than the windbreak. WHY (the
            # denuded hills + back-slope waste; graves + dry hill-crops also live here): settlements.md 'Village windbreak'.
            # Test the DRAWN OUTCOME, not the patch's bbox CENTER. `commons()` skips every paddy point when it
            # scatters, so scrub can never actually be drawn on a flooded field - "is the center over water" was
            # only ever a PROXY for that, and a wrong one: an INTERIOR fill (the patch that clothes the voids an
            # irregular field leaves inside its own bbox) legitimately has its center on the crop while every
            # glyph it draws falls in the voids around it. Scoring the center would fail a correct patch, which
            # is the same bbox-stands-in-for-real-geometry mistake as the phantom field tail. What genuinely
            # goes wrong is a patch placed where it can clothe NOTHING - it silently draws nothing at all - so
            # that is what we test: sample each patch and require real open (non-crop) ground under it.
            commons = M.get("commons", [])
            barren = []
            for c in commons:
                poly = c.get("poly")
                if not poly:
                    continue
                xs = [p[0] for p in poly]
                ys = [p[1] for p in poly]
                n_inside: int = 0
                n_open: int = 0
                step = max(6.0, min(max(xs) - min(xs), max(ys) - min(ys)) / 12.0)
                gy = min(ys)
                while gy <= max(ys):
                    gx = min(xs)
                    while gx <= max(xs):
                        if point_in_poly(gx, gy, poly):
                            n_inside += 1
                            if not any(point_in_poly(gx, gy, ol) for ol in fields_ol):
                                n_open += 1
                        gx += step
                    gy += step
                if n_inside and not n_open:
                    barren.append((round(c["x"]), round(c["y"])))
            check(
                "commons_clear_of_paddies",
                not barren,
                f"fuel/fodder commons patch(es) lie ENTIRELY over flooded paddy, so they clothe nothing and draw nothing: {barren[:3]} - the commons is NON-arable degraded grazing, never the productive wet paddy; put the patch where there is open ground",
            )
            # MANAGED-WOODLAND patches must not OVERLAP the crops nor BLOCK THEIR LIGHT (GM). Both the placement and
            # this check enforce it. A tree canopy over a crop competes for root/light; and the sun is to the SOUTH
            # (maps are north-up), so a tree casts its shadow toward the NORTH - a patch may sit just north/beside a
            # crop, but on the crop's SOUTH (sunny) side it must stand well back (a canopy's shadow reach) or it
            # shades the field. Covers BOTH the paddy and the dry hatake plots. Distances: a fixed crown-radius
            # no-overhang CLEAR, plus a real-world shadow reach on the south side (feet -> px at the map's ftpx).
            woodland = [c for c in commons if c.get("role") == "woodland"]
            if woodland:
                _fp = float(meta.get("ftpx") or meta.get("ft_per_px") or 2.0)
                CLEAR = 14  # ~a crown radius: the canopy must not overhang the crop
                SHADE = 14 + round(55 / _fp)  # ... plus a shadow reach (~55 ft) on the crop's SUNNY south side
                crops = [f["outline"] for f in fields if f.get("kind") == "paddy"]
                crops += [dp["poly"] for dp in M.get("dry_plots", [])]
                w_over, w_shade = [], []
                for c in woodland:
                    wp = c.get("poly")
                    if not wp:
                        continue
                    tag = (round(c["x"]), round(c["y"]))
                    wy0 = min(p[1] for p in wp)
                    wx0 = min(p[0] for p in wp)
                    wx1 = max(p[0] for p in wp)
                    for crop in crops:
                        gap = poly_gap(wp, crop)
                        if gap <= 0:
                            w_over.append(tag)
                            break
                        cx0 = min(p[0] for p in crop)
                        cx1 = max(p[0] for p in crop)
                        cy1 = max(p[1] for p in crop)
                        south = wy0 >= cy1 - CLEAR and wx0 < cx1 and cx0 < wx1  # patch sits south of the crop, in its shadow column
                        if gap < (SHADE if south else CLEAR):
                            w_shade.append(tag)
                            break
                check(
                    "woodland_clear_of_crops",
                    not w_over and not w_shade,
                    f"managed-woodland patch(es) overlap {sorted(set(w_over))[:3]} or shade {sorted(set(w_shade))[:3]} the "
                    f"crops - a coppice patch must stand clear of the paddy + dry hatake (a canopy over crops competes; a "
                    f"tree on the crop's SOUTH/sunny side blocks its light). Set it back on the high ground, north/beside the fields",
                )
                # a coppice WOODLAND patch is a DISTINCT wood from the protected fengshui GROVE (village_groves) -
                # the two must not overlap, or they merge into one indistinct green mass (GM). Keep each patch off
                # every grove clump (its drawn radius). Place the coppice on its OWN stretch of the high ground.
                w_on_grove = []
                for c in woodland:
                    wp = c.get("poly")
                    if not wp:
                        continue
                    if any(point_in_poly(gx, gy, wp) or poly_dist(gx, gy, wp) < g.get("r", 6) for g in M.get("village_groves", []) for gx, gy in g.get("clumps", [])):
                        w_on_grove.append((round(c["x"]), round(c["y"])))
                check(
                    "woodland_clear_of_grove",
                    not w_on_grove,
                    f"managed-woodland patch(es) {sorted(set(w_on_grove))[:3]} overlap the fengshui GROVE - the coppice "
                    f"commons and the protected village grove are DISTINCT woods; keep the patch off the grove clumps",
                )
            if meta.get("nucleated") and commons and len(houses) >= 10:
                wbs = [g for g in vgroves if g.get("role") == "windbreak"]
                if wbs:
                    ccx = sum(h["x"] for h in houses) / len(houses)
                    ccy = sum(h["y"] for h in houses) / len(houses)
                    wb_proj = max((g["x"] - ccx) * wvx + (g["y"] - ccy) * wvy for g in wbs)
                    # only the fuel/fodder COMMONS proper (role 'commons') must lie on the windward back-slope;
                    # the general marginal hill land types - 'grazing' scrub, open 'pasture', coppice 'woodland' -
                    # can sit on ANY dry flank (the NE upland, the SW corner, the uphill head) and are exempt from
                    # the beyond-the-windbreak toposequence rule (they are the hinterland catena, not the fuel commons)
                    near = [
                        (round(c["x"]), round(c["y"]))
                        for c in commons
                        if c.get("role", "commons") not in ("grazing", "pasture", "woodland") and (c["x"] - ccx) * wvx + (c["y"] - ccy) * wvy <= wb_proj + 5
                    ]
                    check(
                        "commons_beyond_the_windbreak",
                        not near,
                        f"fuel/fodder commons {near[:2]} sit between the village and its back-grove (or on the field "
                        f"side), not BEYOND the windbreak - the toposequence is village -> back-grove -> commons, so the "
                        f"degraded grazing lies on the far windward side, past the protected wood",
                    )

            # WEALTH VARIATION: farmhouses are not one uniform size - a modest wealth tier (recorded as `wealth`)
            # scales the rendered house and, with it, the grove, so holdings read as ranging from the landless
            # mizunomi to a honbyakushO landholder. Verify the tiers are ACTIVE so a regression that flattens
            # them to one size is caught. (Only the house + grove carry the signal; the yard/garden/shed stay
            # uniform - scaling them coupled into farmstead placement and dropped houses.) WHY: settlements.md.
            plain = [h for h in houses if h.get("role") != "headman"]
            if len(plain) >= 10:
                # measure the ACTUAL rendered-footprint spread, which is carried TWO ways: the DISPERSED path
                # keeps a uniform base w x h and scales the drawn house by a `wealth` tier (0.9/1.0/1.12), while
                # the NUCLEATED path jitters the base w x h (length/depth) directly at wealth 1.0. Fold both in
                # via effective area = w * h * wealth^2 (the wealth factor scales each dimension), so a regression
                # that flattens houses to one size is caught under EITHER encoding.
                def _eff(h: dict[str, Any]) -> float:
                    return float(h["w"] * h["h"] * (h.get("wealth", 1.0) ** 2))

                areas = sorted(_eff(h) for h in plain)
                med = areas[len(areas) // 2] or 1
                varied = sum(1 for h in plain if abs(_eff(h) - med) > 0.05 * med)
                check(
                    "farmhouse_sizes_vary",
                    varied >= 0.2 * len(plain),
                    f"farmhouses show no size variation ({varied}/{len(plain)} off the median footprint) - a modest spread of homestead sizes is expected (they look flattened to one size)",
                )
                # a minka is rectangular but within the ~1.3-2.5:1 norm - a house grew by adding bays
                # (longer), never into a 4:1 shed. Guard the aspect so the length jitter stays plausible.
                lop = [[round(h["x"]), round(h["y"])] for h in houses if min(h["w"], h["h"]) > 0 and max(h["w"], h["h"]) / min(h["w"], h["h"]) > 2.7]
                check(
                    "farmhouse_aspect_in_range", not lop, f"farmhouse(s) {lop[:3]} are more than 2.7:1 long-to-wide - a minka stays roughly 1.3-2.5:1 (it lengthened by bays, it did not become a shed)"
                )

    # THE DEAD - a full funerary geography. Every settlement above a hamlet buries its cremated dead
    # (a hamlet's go to the village district's ground, just as it has no shrine or headman). GRAVEYARDS
    # are temple parish grounds: the state merged Shinsei and Fortune worship, so ANY temple may host
    # one (a temple opts out with graveyard=False - a new or special-purpose hall). A Shinto SHRINE
    # keeps death-pollution (kegare) at arm's length, so no grave site sits hard against a shrine. A
    # CITY additionally shows 2-4 graveyards split inside/outside the walls, the ruling clan's walled
    # MAUSOLEUM by the samurai quarter, an extramural CREMATION GROUND, and a pauper OSSUARY beside it.
    if scale in ("village", "town", "city"):
        cems = M.get("cemeteries", [])
        maus = M.get("mausoleums", [])
        crem = M.get("cremation_grounds", [])
        oss = M.get("ossuaries", [])
        relig = M.get("religious", [])
        shrines = [r for r in relig if r.get("kind") in ("shrine", "small_shrine")]
        temples = [r for r in relig if r.get("kind") in ("monastery", "temple")]
        wall = M.get("wall")

        def _inside(px: float, py: float) -> bool:
            return bool(wall) and point_in_poly(px, py, wall)

        # PRESENCE: a village/town has >=1 graveyard; a city shows 2-4 (a few parish grounds,
        # consolidated over the centuries - not one, not a dozen)
        if scale == "city":
            check("city_graveyard_count", 2 <= len(cems) <= 4, f"a provincial city should show 2-4 temple graveyards; found {len(cems)}")
        else:
            check(
                "settlement_has_cemetery",
                len(cems) >= 1,
                f"a {scale} buries its dead but has no graveyard - add s.cemetery(...) (a hamlet is exempt; its dead go to the village district's burial ground)",
            )

        # CHURCHYARD (L7R): a village SHRINE is officially Shinseist and its monk performs the funerary rites, so
        # the graveyard sits IN the shrine's precinct - like a Buddhist-temple parish ground - NOT held away from
        # it (real-Japan Shinto kegare does NOT apply: the shrine IS the death-handling institution). Only the
        # sacred HALL + its TORII gateway stay clear: graves fill the yard AROUND them, never ON them. WHY:
        # settlements.md "Historical grounding" (Brotherhood of Shinsei monks tend the country shrines and the dead).
        def _on_shrine_building(site: dict[str, Any]) -> bool:
            sc = rect_corners(_struct_rect(site))
            for r in shrines:
                if sat_overlap(sc, rect_corners({"x": r["x"], "y": r["y"], "w": r["w"] + 20, "h": r["h"] + 20, "rot": 0})):
                    return True
            return any(sat_overlap(sc, rect_corners({"x": t[0], "y": t[1] + 4, "w": 58, "h": 48, "rot": 0})) for t in M.get("torii", []))

        on_bldg = [(round(s["x"]), round(s["y"])) for s in cems + maus if _on_shrine_building(s)]
        check(
            "cemetery_clear_of_shrine",
            not on_bldg,
            f"grave site(s) sit ON the shrine hall or its torii gateway: {on_bldg[:3]} - the monk tends the graves "
            f"so they fill the shrine's yard, but the sacred hall + gateway themselves stay clear of burials",
        )

        # MARSH is unbuildable wet ground: no SACRED hall and no BURIAL ground sits on a reed marsh - you would
        # never raise a shrine or dig graves in a bog (they belong on DRY ground, the spur / high ground). The
        # `toe` marsh is the wet valley floor; a `pond_fringe` (a thin decorative shore ring) is exempt. GM 2026-07.
        bog = [m["poly"] for m in M.get("marshes", []) if m.get("role") != "pond_fringe" and m.get("poly")]
        if bog:

            def _on_marsh(site: dict[str, Any]) -> bool:
                return any(point_in_poly(site["x"], site["y"], mp) for mp in bog) or any(point_in_poly(cx, cy, mp) for cx, cy in rect_corners(_struct_rect(site)) for mp in bog)

            marshy = [(round(s["x"]), round(s["y"])) for s in relig + cems + maus + crem + oss if _on_marsh(s)]
            check(
                "sacred_and_graves_off_marsh",
                not marshy,
                f"shrine/temple or grave site(s) {sorted(set(marshy))[:3]} sit on a reed MARSH - a hall is not "
                f"raised and graves are not dug in a bog; site them on DRY ground (the spur / high ground), off the marsh",
            )

        # PRECINCT (village): the village graveyard sits BY the shrine (the Shinsei monk's funerary ground),
        # mirroring the town/city temple-precinct rule. A HILLTOP shrine is exempt (graves do not climb the
        # sacred hill, and a prominent hill-shrine is not the humble earth-god monk's funerary base - as with
        # remote_shrine_has_own_well); if every shrine is hilltop, the ground is placed by eye. A hamlet has no
        # shrine at all (its dead go to the village district's ground).
        flat_shrines = [r for r in shrines if not (M.get("hill") and in_ellipse(r["x"], r["y"], M["hill"]))]
        if scale == "village" and cems and flat_shrines:
            far = [(round(c["x"]), round(c["y"])) for c in cems if not any(math.hypot(c["x"] - r["x"], c["y"] - r["y"]) < 250 for r in flat_shrines)]
            check(
                "village_graveyard_by_shrine",
                not far,
                f"village graveyard(s) set apart from the shrine: {far[:3]} - the village shrine is Shinseist and its monk performs the funerary rites, so the graveyard sits IN the shrine's precinct",
            )

        # WATER SET-BACK: burial grounds keep a clear margin from OPEN WATER (the moat, a stream, or a
        # pond), and that margin SCALES WITH THE WATERWAY'S SIZE (water_setback() - a creek needs little,
        # a moat/river much more) because a burial ground by big water floods out. The CREMATION ground
        # may sit NEARER the water (fire/ritual), so the graveyard naturally lands beyond it. Non-overlap
        # is not enough. (Thin irrigation channels are NOT open water and don't trigger this.)
        # the moat is OUTSIDE the wall, so an INSIDE-wall ground is shielded from it by the rampart and is
        # exempt from the moat term (streams/ponds apply regardless of which side they sit on).
        line_waters = ([(M["moat"], M.get("moat_width", 22), True)] if M.get("moat") else []) + [(s["poly"], s.get("w", 9), False) for s in M.get("streams", [])]
        pond = M.get("pond")
        field_outlines = [f["outline"] for f in M.get("fields", [])] + [f["outline"] for f in M.get("flower_fields", [])]
        FIELD_SETBACK = 50  # a RICE PADDY is standing water when flooded - a real flood hazard, not a
        #                      trickle - so a burial ground keeps a clear margin from its edge (more than a creek)
        crowded = []
        for site, is_crem in [(c, False) for c in cems] + [(o, False) for o in oss] + [(cr, True) for cr in crem]:
            cor = rect_corners(site)
            inside_wall = bool(wall) and point_in_poly(site["x"], site["y"], wall)
            near_water = False
            for poly, width, is_moat in line_waters:
                if is_moat and inside_wall:
                    continue
                sb = 30 if is_crem else water_setback(width)  # cremation may sit near water; burials scale
                if min(seg_dist(cx, cy, poly[k], poly[k + 1]) for cx, cy in cor for k in range(len(poly) - 1)) < width / 2 + sb:
                    near_water = True
                    break
            if not near_water and pond:
                sb = 30 if is_crem else 55
                if min(math.hypot(cx - pond[0], cy - pond[1]) for cx, cy in cor) < max(pond[2], pond[3]) + sb:
                    near_water = True
            # RICE PADDIES flood, so a BURIAL ground keeps a creek-level set-back from any field edge too
            # (treat the field boundary like a small watercourse). The cremation ground is exempt (a fire
            # site, not flood-sensitive graves).
            if not near_water and not is_crem:
                for ol in field_outlines:
                    if min(poly_dist(cx, cy, ol) for cx, cy in cor) < FIELD_SETBACK:
                        near_water = True
                        break
            if near_water:
                crowded.append((round(site["x"]), round(site["y"])))
        check(
            "funerary_set_back_from_water",
            not crowded,
            f"grave site(s) crowd open water OR a flood-prone rice paddy - a burial ground's set-back scales with "
            f"the waterway (a moat/river needs far more room than a creek; field edges count as creeks): {crowded[:3]}",
        )

        # THE CREMATORY ADJOINS AN EXTERNAL BURIAL GROUND: the body is burned and its cremated bones
        # interred next door, so a cremation ground sits ADJACENT to an EXTERNAL (outside-the-walls)
        # cemetery - together they form the extramural funerary complex beyond a gate. (An unwalled
        # settlement has no walls, so any of its cemeteries counts as external.)
        if crem:
            ext_cems = [c for c in cems if not (wall and point_in_poly(c["x"], c["y"], wall))]

            def _edge_gap(a: dict[str, Any], b: dict[str, Any]) -> float:
                gx = max(0.0, abs(a["x"] - b["x"]) - (a["w"] + b["w"]) / 2)
                gy = max(0.0, abs(a["y"] - b["y"]) - (a["h"] + b["h"]) / 2)
                return math.hypot(gx, gy)

            lonely = [(round(cr["x"]), round(cr["y"])) for cr in crem if not any(_edge_gap(cr, c) <= 70 for c in ext_cems)]
            check(
                "cremation_ground_by_external_cemetery",
                not lonely,
                f"cremation ground(s) not adjacent to an external (outside-the-walls) burial ground: {lonely[:3]} - "
                f"the body is cremated and its bones interred next door, so the crematory adjoins an extramural cemetery",
            )

            # SET BACK FROM THE MAIN ROAD: the crematory is marginal, polluting land reached by a minor
            # funeral path, NOT the high street - so it keeps clear of the Imperial / trunk road (town
            # streets and minor lanes don't count; only the main road). The temple's own parish graveyard
            # may sit by the temple wherever it is, but the smoking pyre stays off the main thoroughfare.
            ROAD_SETBACK = 130
            mainroad = M.get("road")
            if mainroad:

                def _rdist(x: float, y: float) -> float:
                    return min(seg_dist(x, y, mainroad[k], mainroad[k + 1]) for k in range(len(mainroad) - 1))

                crem_on_road = [(round(cr["x"]), round(cr["y"])) for cr in crem if _rdist(cr["x"], cr["y"]) < ROAD_SETBACK]
                check(
                    "cremation_ground_set_back_from_main_road",
                    not crem_on_road,
                    f"cremation ground(s) crowd the main road: {crem_on_road[:3]} - a crematory is marginal land reached "
                    f"by a minor funeral path, not high-street frontage; keep it >= {ROAD_SETBACK}px off the trunk road",
                )
                # NOT BETWEEN its temple and the road: you should not walk past the pyre to reach the
                # monastery. The crematory sits BEHIND or beside its nearest temple (at least as far from
                # the road as that temple, less a small tolerance), never on the road-side approach to it.
                # (The temple's own graveyard may still sit road-side by the temple - this is the pyre only.)
                temples_r = [t for t in M.get("religious", []) if t.get("kind") in ("monastery", "temple")]
                between = []
                for cr in crem:
                    near_t = [t for t in temples_r if math.hypot(t["x"] - cr["x"], t["y"] - cr["y"]) <= 400]
                    if near_t:
                        t = min(near_t, key=lambda t: math.hypot(t["x"] - cr["x"], t["y"] - cr["y"]))
                        if _rdist(cr["x"], cr["y"]) < _rdist(t["x"], t["y"]) - 40:
                            between.append((round(cr["x"]), round(cr["y"])))
                check(
                    "cremation_ground_not_between_temple_and_road",
                    not between,
                    f"cremation ground(s) sit between a temple and the road: {between[:3]} - you should not walk past "
                    f"the pyre to reach the monastery; put the crematory BEHIND or beside its temple, off the road side",
                )

        # PRECINCT: a graveyard is a temple parish ground - it sits by a temple. (At CITY scale only an
        # INSIDE-wall graveyard must; an OUTSIDE-wall one is the extramural common burial ground, exempt.)
        if scale in ("town", "city") and cems and temples:
            # a graveyard must be by a temple UNLESS it is outside a walled settlement's wall (then it
            # is the extramural common burial ground - exempt). An unwalled town has no outside, so all
            # its graveyards are parish grounds and must sit by a monastery.
            stray = [
                (round(c["x"]), round(c["y"]))
                for c in cems
                if c.get("parish", True) and (not wall or _inside(c["x"], c["y"])) and not any(math.hypot(c["x"] - r["x"], c["y"] - r["y"]) < 230 for r in temples)
            ]
            check(
                "cemetery_in_temple_precinct",
                not stray,
                f"graveyard(s) not in any temple precinct: {stray[:3]} - a parish ground sits by its temple (a walled settlement's extramural common ground, and any parish=False plot, are exempt)",
            )

        # SPLIT: any WALLED settlement (town or city) keeps a graveyard both inside AND outside the
        # walls - and the EXTERIOR common ground is noticeably larger than the cramped intramural one
        # (there is room beyond the walls; inside, the temple grounds are hemmed in by the city).
        if wall and cems:
            ins = [c for c in cems if _inside(c["x"], c["y"])]
            out = [c for c in cems if not _inside(c["x"], c["y"])]
            check(
                "walled_graveyards_inside_and_outside",
                bool(ins) and bool(out),
                f"a walled settlement keeps a graveyard both inside AND outside the walls (inside {len(ins)}, outside {len(out)}) - keep at least one of each",
            )
            if ins and out:
                bi = max(c["w"] * c["h"] for c in ins)
                bo = max(c["w"] * c["h"] for c in out)
                check(
                    "walled_exterior_cemetery_larger",
                    bo >= 1.3 * bi,
                    f"the exterior common burial ground should be noticeably larger than the cramped intramural "
                    f"ground (outside {bo:.0f}px2 vs inside {bi:.0f}px2; want >= 1.3x) - there is room beyond the walls",
                )

        if scale == "city":
            # every temple that CAN host a graveyard has one in its precinct (graveyard=False opts out)
            needy = [r for r in temples if r.get("graveyard", True)]
            unserved = [r.get("label", (round(r["x"]), round(r["y"]))) for r in needy if not any(math.hypot(c["x"] - r["x"], c["y"] - r["y"]) < 230 for c in cems)]
            check(
                "city_temples_have_graveyards",
                not unserved,
                f"temple(s) with no graveyard in their precinct: {unserved[:3]} - Shinsei and Fortune worship are merged, so every temple keeps a burial ground unless it opts out (graveyard=False)",
            )
            # CLAN MAUSOLEUM: a walled crypt precinct inside the walls, by the samurai/government quarter
            gov = M.get("governor_mansion")
            sam = [b for b in M.get("buildings", []) if b.get("kind") in ("samurai", "samurai_large")]
            if gov:
                anchor = (gov["x"], gov["y"])
            elif sam:
                anchor = (sum(b["x"] for b in sam) / len(sam), sum(b["y"] for b in sam) / len(sam))
            else:
                anchor = None
            maus_ok = bool(maus) and any(_inside(m2["x"], m2["y"]) for m2 in maus) and (anchor is None or any(math.hypot(m2["x"] - anchor[0], m2["y"] - anchor[1]) < 640 for m2 in maus))
            check(
                "city_has_mausoleum",
                maus_ok,
                "a provincial city needs the ruling clan's ancestral MAUSOLEUM (s.mausoleum) inside the walls, by the samurai/government quarter - a walled crypt precinct for the elite dead",
            )
            # CREMATION GROUND: smoke, fire, and pollution push the crematory OUTSIDE the walls
            crem_out = [c for c in crem if not _inside(c["x"], c["y"])]
            check(
                "city_has_cremation_ground",
                bool(crem_out),
                "a city cremates its dead at a CREMATION GROUND (s.cremation_ground) OUTSIDE the walls - monk-run with burakumin assistants; smoke and fire keep it beyond a gate",
            )
            # PAUPER OSSUARY: outside the walls, beside the cremation ground
            oss_ok = any(not _inside(o["x"], o["y"]) and any(math.hypot(o["x"] - c["x"], o["y"] - c["y"]) < 320 for c in crem) for o in oss)
            check(
                "city_has_ossuary",
                oss_ok,
                "a city needs a pauper OSSUARY mound (s.ossuary) outside the walls by the cremation ground - the communal bones of the poor and the unconnected dead (muenbotoke)",
            )

        if scale == "town":
            # a county town cremates too - a cremation ground at the edge, clear of the dwellings
            dwell_t = M.get("houses", []) + [b for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS]
            far_crem = [c for c in crem if all(math.hypot(c["x"] - h["x"], c["y"] - h["y"]) > 120 for h in dwell_t)] if dwell_t else crem
            check(
                "town_has_cremation_ground",
                bool(far_crem),
                "a county town cremates its dead at a CREMATION GROUND (s.cremation_ground) at the edge, clear of the dwellings - monk-run with burakumin assistants",
            )

    # LABEL TEXT renders ON TOP of everything: no part of a label may be covered. Labels live in the
    # topmost layer (s.add_label), above the TOP-layer structures (gate furniture, kido, torii); the
    # check guards it - a label overlapped by any structure drawn OVER it (higher draw-z) is covered.
    occluders = []
    for gs in M.get("gate_structs", []):
        if gs.get("z") is not None:
            occluders.append((gs["x"] - gs["w"] / 2, gs["y"] - gs["h"] / 2, gs["x"] + gs["w"] / 2, gs["y"] + gs["h"] / 2, gs["z"]))
    for kd in M.get("kido", []):
        if kd.get("z") is not None and kd.get("bbox"):
            occluders.append((kd["bbox"][0], kd["bbox"][1], kd["bbox"][2], kd["bbox"][3], kd["z"]))
    for t in M.get("torii", []):
        if len(t) >= 3:
            occluders.append((t[0] - 22, t[1] - 28, t[0] + 22, t[1] + 12, t[2]))  # the arch's drawn extent
    covered_labels = []
    for L in labels:
        lx0, ly0, lx1, ly1, lz = L[0], L[1], L[2], L[3], L[4]
        for ox0, oy0, ox1, oy1, oz in occluders:
            if oz > lz and lx0 < ox1 and ox0 < lx1 and ly0 < oy1 and oy0 < ly1:
                covered_labels.append(L[5] if len(L) > 5 else "label")
                break
    check("labels_render_on_top", not covered_labels, f"label text covered by a structure drawn over it (a label must render on top of everything, fully readable): {sorted(set(covered_labels))}")

    hill = M.get("hill")
    if hill:
        onhill = [f["name"] for f in fields if any(in_ellipse(px, py, hill) for px, py in f["outline"])]
        check("no_field_on_hill", not onhill, f"on hill: {onhill}")

    # every watercourse - irrigation channel OR natural stream - must connect what it
    # claims to: each end anchored to its pond / off-map edge / field / forest
    pond = M.get("pond")
    forest = M.get("forest")

    def anchored(pt: Pt, anchor: dict[str, Any]) -> bool:
        k = anchor["kind"]
        if k == "pond":
            return bool(pond) and in_ellipse(pt[0], pt[1], pond, 1.02)
        if k == "offmap":
            return bool(min(pt[0] - EX0, EX1 - pt[0], pt[1] - EY0, EY1 - pt[1]) <= 32)
        if k == "forest":
            return bool(forest) and point_in_poly(pt[0], pt[1], forest)
        if k == "stream":
            return any(seg_dist(pt[0], pt[1], sp[i], sp[i + 1]) < 30 for st in M.get("streams", []) for sp in [st["poly"]] for i in range(len(sp) - 1))
        if k == "field":
            fo: Any = field_by.get(anchor["name"])
            return bool(fo) and point_in_poly(pt[0], pt[1], fo["outline"]) and edge_dist(pt[0], pt[1], fo["outline"]) >= 10
        if k == "moat":
            mo: Any = M.get("moat")
            return bool(mo) and any(seg_dist(pt[0], pt[1], mo[i], mo[i + 1]) < 34 for i in range(len(mo) - 1))
        if k == "drain":  # a brook empties FROM the field drain (akusui outfall)
            return any(seg_dist(pt[0], pt[1], dp[i], dp[i + 1]) < 30 for fd in M.get("field_ditches", []) if fd.get("role") == "drain" for dp in [fd["poly"]] for i in range(len(dp) - 1))
        return False

    for idx, c in enumerate(M["channels"]):
        poly, frm, to = c["poly"], c["frm"], c["to"]
        start, end = poly[0], poly[-1]
        tag = to.get("name", idx)
        check(f"channel_source_anchored[{tag}]", anchored(start, frm), f"start {start} not anchored to {frm}")
        check(f"channel_field_anchored[{tag}]", anchored(end, to), f"end {end} not anchored to {to}")
        dev = max((seg_dist(p[0], p[1], start, end) for p in poly[1:-1]), default=0)
        check(f"channel_winds_gently[{tag}]", 5 <= dev <= 50, f"deviation {dev:.0f}px (want 5-50)")
        straight = math.hypot(end[0] - start[0], end[1] - start[1])
        check(f"channel_directness[{tag}]", straight == 0 or polyline_len(poly) <= 1.6 * straight, f"len {polyline_len(poly):.0f} vs straight {straight:.0f}")

    # natural streams: those that declare anchors must connect them (e.g. a forest
    # brook into a pond); and NO stream may run through a farm field
    def stream_through_field(poly: Poly, outline: Poly, frm: Any, to: Any) -> bool:
        # A stream ANCHORED to the field's drain/outfall (a drain-fed brook carrying the runoff off-map) or to
        # the field itself legitimately CONNECTS there, so it starts (or ends) inside the field envelope. Trim
        # the run from that anchored end up to where it first LEAVES the field, then check only the rest - so the
        # legitimate connection is allowed, but a stream that RE-ENTERS or cuts across the crop still fires.
        pts = list(poly)
        if frm and frm.get("kind") in ("drain", "field"):
            while len(pts) > 1 and point_in_poly(pts[0][0], pts[0][1], outline):
                pts = pts[1:]
        if to and to.get("kind") in ("drain", "field"):
            while len(pts) > 1 and point_in_poly(pts[-1][0], pts[-1][1], outline):
                pts = pts[:-1]
        if any(point_in_poly(px, py, outline) for px, py in pts):
            return True
        n = len(outline)
        return any(segments_cross(pts[k], pts[k + 1], outline[e], outline[(e + 1) % n]) for k in range(len(pts) - 1) for e in range(n))

    through = []
    for idx, st in enumerate(M.get("streams", [])):
        poly, frm, to = st["poly"], st.get("frm"), st.get("to")
        if frm and to:
            check(f"stream_source_anchored[{idx}]", anchored(poly[0], frm), f"start {poly[0]} not anchored to {frm}")
            check(f"stream_end_anchored[{idx}]", anchored(poly[-1], to), f"end {poly[-1]} not anchored to {to}")
        through += [f["name"] for f in fields if stream_through_field(poly, f["outline"], frm, to)]
    check("streams_avoid_fields", not through, f"stream(s) run through field(s): {sorted(set(through))}")

    # WATER CHANNELS TURN ONLY THROUGH OBTUSE ANGLES (>90 deg). A canal/ditch does not make an acute hairpin
    # without bizarre topology, so at every interior vertex the incoming and outgoing segments must not fold
    # back on each other (dot >= 0 => turn <= 90 deg => interior angle >= 90 deg). Applies to every recorded
    # watercourse: irrigation channels, natural streams, and the in-field irrigation ditches.
    def acute_turns(poly: Poly) -> list[tuple[int, int]]:
        bad: list[tuple[int, int]] = []
        for i in range(1, len(poly) - 1):
            ax, ay = poly[i][0] - poly[i - 1][0], poly[i][1] - poly[i - 1][1]
            bx, by = poly[i + 1][0] - poly[i][0], poly[i + 1][1] - poly[i][1]
            la, lb = math.hypot(ax, ay), math.hypot(bx, by)
            if la < 3 or lb < 3:
                continue  # ignore jitter-length segments
            if (ax * bx + ay * by) / (la * lb) < -0.02:  # cos(turn) < 0 => turn > 90 deg => acute interior angle (1 deg tol)
                bad.append((round(poly[i][0]), round(poly[i][1])))
        return bad

    acute = []
    for c in M.get("channels", []):
        acute += acute_turns(c["poly"])
    for st in M.get("streams", []):
        acute += acute_turns(st["poly"])
    for fdt in M.get("field_ditches", []):
        acute += acute_turns(fdt["poly"])
    check(
        "water_channels_obtuse_turns",
        not acute,
        f"water channel(s) make an ACUTE (<90 deg) turn at {sorted(set(acute))[:5]} - a ditch/canal only bends through obtuse angles; an acute hairpin implies impossible topology",
    )

    # DRY-FIELD FURROWS vary PER PLOT - no two EDGE-ADJACENT dry plots may run their ridges the SAME way.
    # Fragmented dry holdings were a mosaic of family strips, each plowed to its OWN orientation (the patchwork-
    # quilt look); ridge-along-contour is a STEEP-slope erosion measure, NOT forced on a gentle valley margin.
    # A furrow is an undirected LINE, so "same direction" is compared mod pi. WHY: settlements.md 'Water-first v2' crop.
    # A steep / terraced village may declare CONTOUR furrows (meta.dry_furrows_vary=False - the rows converge
    # onto the contour for erosion control), in which case aligned rows are correct and variation is NOT required.
    dry_plots = M.get("dry_plots", [])
    if len(dry_plots) >= 4 and M.get("meta", {}).get("dry_furrows_vary", True):
        dcen = [(sum(v[0] for v in p["poly"]) / len(p["poly"]), sum(v[1] for v in p["poly"]) / len(p["poly"])) for p in dry_plots]
        same = []
        for ai in range(len(dry_plots)):
            for bi in range(ai + 1, len(dry_plots)):
                if (dcen[ai][0] - dcen[bi][0]) ** 2 + (dcen[ai][1] - dcen[bi][1]) ** 2 >= 50**2:
                    continue  # only EDGE-adjacent plots (a shared boundary)
                d = abs(dry_plots[ai]["theta"] - dry_plots[bi]["theta"]) % math.pi
                if min(d, math.pi - d) <= 0.10:  # within ~6 deg reads as the SAME row direction
                    same.append((round(dcen[ai][0]), round(dcen[ai][1])))
        check(
            "dry_plot_furrows_vary",
            not same,
            f"neighboring dry-field plot(s) run their furrows the SAME way {same[:3]} - fragmented family strips "
            f"were each plowed to their own orientation, so adjacent plots must differ in row direction",
        )

    # BUILDINGS AND WORK YARDS STAY OFF THE DRY PLOTS: a hem of barley/soy strips (or an urban
    # vegetable tract) is CROPLAND, not building ground - a farmstead may ABUT a plot, never stand
    # on it. The dry plots were classified in the overlap registry but no check actually TESTED
    # structures against them, and placement guarded them center-only (block_polys), so a house
    # nudged for its yard - or a ring house at the envelope gap - could stand half its footprint
    # on a hem strip (GM caught farmsteads on Tango's fn1/nw1 hems, 2026-07). Footprints are
    # shrunk ~6% so a plot ABUTTING a wall does not false-fire; real overlap does.
    dry_polys_c = [dp["poly"] for dp in M.get("dry_plots", [])]
    if dry_polys_c:
        on_dry = []
        for mkey in ("houses", "buildings", "threshing_yards", "flophouses", "storehouses", "cemeteries", "cremation_grounds", "ossuaries", "mausoleums"):
            for it in M.get(mkey, []) or []:
                fc = rect_corners({"x": it["x"], "y": it["y"], "w": it.get("w", 20), "h": it.get("h", 14), "rot": it.get("rot", 0)})
                fc = [(it["x"] + (px - it["x"]) * 0.94, it["y"] + (py - it["y"]) * 0.94) for px, py in fc]
                for poly in dry_polys_c:
                    if (
                        any(point_in_poly(px, py, poly) for px, py in fc)
                        or any(point_in_poly(qx, qy, fc) for qx, qy in poly)
                        or any(segments_cross(fc[i], fc[(i + 1) % 4], poly[j], poly[(j + 1) % len(poly)]) for i in range(4) for j in range(len(poly)))
                    ):
                        on_dry.append((round(it["x"]), round(it["y"])))
                        break
        check(
            "structures_clear_of_dry_plots",
            not on_dry,
            f"building(s)/work yard(s) standing ON a dry crop plot: {sorted(set(on_dry))[:6]} - the hem strips and garden tracts are cropland; a farmstead may abut a plot but never overlap it",
        )
        # ... and the WINDBREAK TREES stay off the crops too: a homestead grove hugs the paddy bund
        # but its canopy clumps must not stand in a dry plot (same rule as groves_clear_of_lanes)
        gro_dry = []
        for g in M.get("village_groves", []):
            gr = g.get("r", 10)
            for gx_, gy_ in g.get("clumps", []):
                if any(point_in_poly(gx_, gy_, poly) or min(seg_dist(gx_, gy_, poly[j], poly[(j + 1) % len(poly)]) for j in range(len(poly))) < gr * 0.75 for poly in dry_polys_c):
                    gro_dry.append((round(gx_), round(gy_)))
        check(
            "groves_clear_of_dry_plots",
            not gro_dry,
            f"windbreak canopy clump(s) standing in a dry crop plot: {sorted(set(gro_dry))[:6]} - a grove may hug a plot's edge, but its trees do not grow in the crop",
        )

    # FUNERARY GROUNDS STAND CLEAR OF THE FIELDS: a burial / cremation ground sits in open ground
    # BESIDE the farmland, never ON a paddy's body or its irrigation ditches (GM, 2026-07: Nagahara's
    # cremation ground sat on the far-bank comb's main ditch AND its dry plots). funerary_set_back_from_water
    # keeps graves off open WATER + a creek-margin off field EDGES, and the cremation ground is exempt
    # from that water rule (a fire site) - but a funerary footprint sitting IN a field interior or ON a
    # field ditch is wrong for every funerary kind, cremation included. Field-EDGE abutment is fine
    # (that is the set-back's job); this catches the footprint standing inside the cropped field.
    fld_outlines = [f["outline"] for f in M.get("fields", [])]
    fdit = [d["poly"] for d in M.get("field_ditches", [])]
    if fld_outlines or fdit:
        on_field = []
        for mkey in ("cemeteries", "cremation_grounds", "ossuaries", "mausoleums"):
            for it in M.get(mkey, []) or []:
                fc = rect_corners({"x": it["x"], "y": it["y"], "w": it.get("w", 40), "h": it.get("h", 28), "rot": it.get("rot", 0)})
                fc = [(it["x"] + (px - it["x"]) * 0.9, it["y"] + (py - it["y"]) * 0.9) for px, py in fc]
                inside_field = any(point_in_poly(px, py, ol) for ol in fld_outlines for px, py in fc)
                on_ditch = any(seg_dist(cx, cy, dp[k], dp[k + 1]) < 8 for dp in fdit for (cx, cy) in fc for k in range(len(dp) - 1))
                if inside_field or on_ditch:
                    on_field.append((round(it["x"]), round(it["y"])))
        check(
            "funerary_clear_of_fields",
            not on_field,
            f"funerary ground(s) standing on a field or its ditches: {sorted(set(on_field))[:4]} - a burial / "
            f"cremation ground sits in open ground BESIDE the farmland, not on the paddy body or its irrigation ditches",
        )

    # EVERY IN-FIELD IRRIGATION DITCH TERMINATES AT A DITCH THAT LEAVES THE FIELD - no channel runs to the
    # middle of a field and dead-ends. Concretely: each LATERAL's two ends sit on the MAIN or the DRAIN (which
    # in turn is fed by a pond channel / emptied by an off-map or cascade channel, so the whole net exits to
    # the pond or the map edge). Off-map fields are exempt (their water is implied beyond the frame).
    ditches = M.get("field_ditches", [])
    if ditches:

        def near_any(pt: Pt, polys: Sequence[Poly], tol: float = 13) -> bool:
            return any(seg_dist(pt[0], pt[1], pl[i], pl[i + 1]) < tol for pl in polys for i in range(len(pl) - 1))

        dangling: list[tuple[int, int]] = []
        for fname in {d["field"] for d in ditches}:
            trunks = [d["poly"] for d in ditches if d["field"] == fname and d["role"] in ("main", "drain")]
            for lat in [d["poly"] for d in ditches if d["field"] == fname and d["role"] == "lateral"]:
                for end in (lat[0], lat[-1]):
                    if not near_any(end, trunks):
                        dangling.append((round(end[0]), round(end[1])))
        check(
            "field_ditches_terminate",
            not dangling,
            f"irrigation channel(s) dead-end / overshoot inside a field at {sorted(set(dangling))[:5]} - every "
            f"lateral must END on the main canal or the drain (not stop, and not stub past it toward the edge)",
        )

        # DELIVERY DITCHES TAPER: a delivery ditch (role "branch") sheds its water into the paddies all
        # along its length, so its flow dwindles and it must NARROW toward the point where it stops - not
        # end abruptly at full width, which reads as a jarring blunt stub. Where head/tail widths are
        # recorded (w / w_tail), each delivery ditch must taper: w_tail < ~0.85*w. Maps that do not record
        # widths (the older water_field engine) are exempt - no width to judge.
        blunt: list[list[int]] = []
        for fd in ditches:
            if fd.get("role") != "branch":
                continue
            w, wt = fd.get("w"), fd.get("w_tail")
            if w is None or wt is None:
                continue
            if wt > 0.85 * w:
                blunt.append([round(fd["poly"][-1][0]), round(fd["poly"][-1][1])])
        check(
            "delivery_ditches_taper",
            not blunt,
            f"delivery ditch(es) stop at nearly full width {blunt[:3]} - a ditch feeding paddies sheds its water along the way, so it must TAPER to a thread at its stopping point (w_tail < ~0.85*w)",
        )

        # CONNECTIVITY: every in-field ditch must trace to BOTH an external SOURCE (a pond feed) and a runoff
        # SINK (an off-map drain or a stream). Build the watercourse graph - channels + streams + field ditches,
        # joined where their polylines come within tol (crossing-aware) - and require each ditch's component to
        # contain a pond-grounded segment AND a sink-grounded one; else the ditch is tied to nothing outside.
        def touch(pa: Poly, pb: Poly, tol: float = 16) -> bool:
            return any(seg_dist(v[0], v[1], pb[k], pb[k + 1]) < tol for v in pa for k in range(len(pb) - 1)) or any(
                seg_dist(v[0], v[1], pa[k], pa[k + 1]) < tol for v in pb for k in range(len(pa) - 1)
            )

        # a pond is the SOURCE by default (it feeds the field); meta(pond_role="drainage") makes it the SINK
        # (the field drains into it - a reservoir below the fields). Grounding is then DIRECTIONAL: the frm side
        # brings water FROM a source (an inflow brook / off-map / a source pond), the to side carries it OUT to
        # a sink (off-map / a stream / a drainage pond). Streams follow the same rule (a feeder brook grounds a
        # source, a drain brook grounds a sink) instead of the old assume-sink.
        pond_is_source = meta.get("pond_role", "source") == "source"

        def _grounds(frm: Any, to: Any) -> tuple[bool, bool]:
            # the MOAT grounds both ways: it is a fed watercourse (a moated city's fields tap it -
            # city_moat_irrigates_fields), and it is the city's storm drain (an outside field's
            # collector may empty into it), so frm=moat is a source and to=moat is a sink
            fk, tk = (frm or {}).get("kind"), (to or {}).get("kind")
            src = fk in ("offmap", "forest", "stream", "moat") or (fk == "pond" and pond_is_source) or (tk == "pond" and pond_is_source)
            snk = tk in ("offmap", "stream", "moat") or (tk == "pond" and not pond_is_source) or (fk == "pond" and not pond_is_source)
            return src, snk

        segs = [(c["poly"], *_grounds(c["frm"], c["to"])) for c in M.get("channels", [])]
        segs += [(st["poly"], *_grounds(st.get("frm"), st.get("to"))) for st in M.get("streams", [])]
        d0 = len(segs)
        segs += [(d["poly"], False, False) for d in ditches]
        parent = list(range(len(segs)))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for i in range(len(segs)):
            for j in range(i + 1, len(segs)):
                if touch(segs[i][0], segs[j][0]):
                    parent[find(i)] = find(j)
        grounded = {}
        for r in {find(i) for i in range(len(segs))}:
            members = [m for m in range(len(segs)) if find(m) == r]
            grounded[r] = (any(segs[m][1] for m in members), any(segs[m][2] for m in members))
        # ROLE-AWARE grounding, so BOTH water models pass: a SUPPLY ditch (main/branch/lateral) must trace to
        # the pond SOURCE; the DRAIN must trace to a runoff SINK. They need NOT be one component - in the
        # tagoshi CASCADE model the delivery ditches END mid-field and the water flows plot-to-plot to the
        # drain (which sits offset below them), so supply and drain are separate networks bridged by the
        # cascade, not by a ditch. (In the older end-on-drain model they are one component, which still
        # satisfies both.) A ditch missing its required grounding is tied to nothing outside the field.
        supply = ("main", "branch", "lateral", "feed")
        ungrounded = []
        for m in range(d0, len(segs)):
            role = ditches[m - d0]["role"]
            has_source, has_sink = grounded[find(m)]
            if (role in supply and not has_source) or (role == "drain" and not has_sink):
                ungrounded.append((role, ditches[m - d0]["field"]))
        ungrounded = sorted(set(ungrounded))
        check(
            "field_ditches_reach_source_and_sink",
            not ungrounded,
            f"in-field ditch(es) not grounded: {ungrounded[:4]} - a SUPPLY ditch (main/branch/lateral) must trace to the pond source; the DRAIN must trace to a runoff sink (off-map / stream / brook)",
        )

    # no farm field overlaps a road OR a town street (the roadbed/street band must not clip
    # a field) - the road leading into town must not run through a farm field
    roadways = []
    if road:
        roadways.append((road, M.get("road_width", 26) / 2 + 2))
    roadways += [(st["pts"], st["w"] / 2 + 2) for st in M.get("town_streets", [])]
    if roadways:
        bad_fr = []
        for f in fields:
            ol = f["outline"]
            n = len(ol)
            for poly, hw in roadways:
                if (
                    any(seg_dist(px, py, poly[k], poly[k + 1]) < hw for px, py in ol for k in range(len(poly) - 1))
                    or any(point_in_poly(rx, ry, ol) for rx, ry in poly)
                    or any(segments_cross(poly[k], poly[k + 1], ol[e], ol[(e + 1) % n]) for k in range(len(poly) - 1) for e in range(n))
                ):
                    bad_fr.append(f["name"])
                    break
        check("fields_clear_of_road", not bad_fr, f"field(s) run under a road/street: {sorted(set(bad_fr))}")

    # WHERE A ROAD (or town street) CROSSES A WATERCOURSE, a bridge must carry it over - a road does
    # not simply run through open water. Crossings are road/street segments intersecting a stream, an
    # irrigation channel, or the city moat (a walled city's approach road crosses the moat at each
    # gate). Every such crossing must have a recorded bridge near the intersection point. (A road that
    # merely runs ALONGSIDE water, never intersecting it, needs no bridge - only true crossings count.)
    bridges = M.get("bridges", [])
    waters_b = [s["poly"] for s in M.get("streams", [])] + [c["poly"] for c in M.get("channels", [])] + [d["poly"] for d in M.get("field_ditches", [])] + ([M["moat"]] if M.get("moat") else [])
    carried_b = ([road] if road else []) + [st["pts"] for st in M.get("town_streets", [])] + [ln["pts"] for ln in M.get("lanes", [])]
    unbridged = []
    for rpts in carried_b:
        for i in range(len(rpts) - 1):
            ra, rb = rpts[i], rpts[i + 1]
            for wpts in waters_b:
                for j in range(len(wpts) - 1):
                    if segments_cross(ra, rb, wpts[j], wpts[j + 1]):
                        p = seg_intersect(ra, rb, wpts[j], wpts[j + 1])
                        if p is not None and not any(math.hypot(b["x"] - p[0], b["y"] - p[1]) <= 40 for b in bridges):
                            unbridged.append((round(p[0]), round(p[1])))
    check("roads_bridge_water", not unbridged, f"a road/street crosses water with no bridge at {sorted(set(unbridged))} - carry it over (call s.bridges() after laying all roads and water)")

    # STANDALONE plank FOOTBRIDGES on the irrigation ditches (opt-in via meta.field_footbridges): field-workers
    # cross a ditch on a plank while walking the bunds, so any long ditch stretch carries at least one plank
    # about midway (these are NOT lane crossings - no path leads to them). Fires if a long ditch has none near it.
    if meta.get("field_footbridges"):
        FB_MIN = 140
        unplanked = []
        for d in M.get("field_ditches", []):
            pts = d["poly"]
            length = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
            if length < FB_MIN:
                continue
            if not any(poly_dist(b["x"], b["y"], pts) <= 20 for b in M.get("bridges", [])):
                unplanked.append((round(pts[0][0]), round(pts[0][1])))
        check(
            "long_ditches_have_a_footbridge",
            not unplanked,
            f"{len(unplanked)} long irrigation ditch(es) with no plank footbridge near {unplanked[:4]} - a long ditch stretch needs a plank about midway (call s.channel_footbridges())",
        )

    # A plank bridge is overlap-EXEMPT in general (it intentionally sits ON the water it spans), but it must
    # never land on a FARMHOUSE - a plank crosses a ditch, it does not sit on a home. Rotated-rect SAT of each
    # bridge deck (span x deck-width) against every house footprint.
    house_corners = [rect_corners(_struct_rect(h)) for h in M.get("houses", [])]
    on_house = []
    for b in M.get("bridges", []):
        deck = rect_corners({"x": b["x"], "y": b["y"], "w": b["span"], "h": b["w"], "rot": b.get("rot", 0)})
        if any(sat_overlap(deck, hc) for hc in house_corners):
            on_house.append((round(b["x"]), round(b["y"])))
    check("bridges_clear_of_houses", not on_house, f"{len(on_house)} plank bridge(s) overlap a farmhouse at {on_house[:4]} - a plank spans a ditch, it must not sit on a home")

    # WHERE WATERCOURSES MEET they must MERGE like a confluence, not stack opacity into a dark seam.
    # All water BEDS render below all water SHEENS (the shared-opacity bed group composites first, the
    # lighter mid-current group on top), exactly as road beds merge at a crossroads - so at every place
    # two courses CROSS or one FEEDS INTO another, the higher-drawn course's opaque bed must not paint
    # over the other's sheen. Checked via the recorded bed/sheen draw positions (bedz / sheenz).
    ways = [(s["poly"], s.get("bedz"), s.get("sheenz")) for s in M.get("streams", [])]
    ways += [(c["poly"], c.get("bedz"), c.get("sheenz")) for c in M.get("channels", [])]
    if M.get("moat") and M.get("moat_layer"):
        ml = M["moat_layer"]
        ways.append((M["moat"], ml.get("bedz"), ml.get("sheenz")))

    def _water_meet(pa: Poly, pb: Poly) -> Pt | None:
        for i in range(len(pa) - 1):
            for j in range(len(pb) - 1):
                if segments_cross(pa[i], pa[i + 1], pb[j], pb[j + 1]):
                    return seg_intersect(pa[i], pa[i + 1], pb[j], pb[j + 1])
        for pt in (pa[0], pa[-1]):  # a feeder's endpoint sitting ON the other course
            if poly_dist(pt[0], pt[1], pb) <= 12:
                return pt
        for pt in (pb[0], pb[-1]):
            if poly_dist(pt[0], pt[1], pa) <= 12:
                return pt
        return None

    seams = []
    for i in range(len(ways)):
        for j in range(i + 1, len(ways)):
            pa, ba, sa = ways[i]
            pb, bb, sb = ways[j]
            if ba is None or bb is None:
                continue
            pt = _water_meet(pa, pb)
            sheens = [z for z in (sa, sb) if z is not None]
            if pt is not None and sheens and max(ba, bb) > min(sheens):
                seams.append((round(pt[0]), round(pt[1])))
    check(
        "waterways_merge_at_crossings",
        not seams,
        f"watercourses overlap instead of merging at {sorted(set(seams))} - a higher-drawn bed paints over "
        f"another course's sheen (stacking into a dark seam); route all water through s.stream / s.channel / "
        f"s.moat so the shared bed and sheen groups composite it as one confluence",
    )

    # no field overlaps the town wall: a field may ABUT the wall but must stay on one
    # side of it (the chrysanthemum field inside the walls touches but never crosses)
    wall = M.get("wall")
    if wall:
        walled_fields = [(f["name"], f["outline"]) for f in fields] + [(f"flower[{i}]", ff["outline"]) for i, ff in enumerate(M.get("flower_fields", []))]
        bad_fw = []
        for nm, ol in walled_fields:
            n = len(ol)
            if any(segments_cross(wall[k], wall[k + 1], ol[e], ol[(e + 1) % n]) for k in range(len(wall) - 1) for e in range(n)) or any(point_in_poly(wx, wy, ol) for wx, wy in wall):
                bad_fw.append(nm)
        check("fields_clear_of_wall", not bad_fw, f"field(s) overlap the wall: {sorted(set(bad_fw))}")

    # EVERY fully-on-map paddy field must SHOW a source of water: a channel feeding it, or
    # the field directly abutting a stream or pond (its bank at the water). A field merely
    # NEAR water without a visible connection does not count. Fields that run off the map
    # edge are exempt (their water source may be off-map too).
    channels = M.get("channels", [])
    streams_m = M.get("streams", [])

    def watered(ol: Poly) -> bool:
        if any(point_in_poly(c["poly"][-1][0], c["poly"][-1][1], ol) for c in channels):
            return True  # a channel ends inside it
        if any(
            seg_dist(px, py, sp[k], sp[k + 1]) < 18  # the field bank abuts a stream
            for st in streams_m
            for sp in [st["poly"]]
            for px, py in ol
            for k in range(len(sp) - 1)
        ):
            return True
        return bool(pond and any(in_ellipse(px, py, pond, 1.10) for px, py in ol))  # ...or the pond

    dry = [f["name"] for f in fields if f["kind"] == "paddy" and not runs_off_edge(f["outline"]) and not watered(f["outline"])]
    check("fields_show_water_source", not dry, f"on-map field(s) with no visible water source (channel or abutting stream/pond): {sorted(set(dry))}")

    # water flows DOWNHILL. If the map declares its slope (meta(downhill=<dir>)), every
    # channel must run with it: the source (tap on the stream/pond, poly[0]) sits uphill of
    # where it feeds the field (poly[-1]). A channel angled the other way would carry the
    # stream's water away from the field, not into it. <dir> is a cardinal name or [dx,dy]
    # vector in map coords (+y = south). Maps without the tag are exempt (slope unknown).
    downhill = meta.get("downhill")
    if downhill and channels:
        dvec = unit_dir(downhill)
        check("downhill_direction_valid", bool(dvec), f"meta(downhill={downhill!r}) is not a cardinal name or [dx,dy] vector")
        if dvec:
            uphill = []
            for c in channels:
                (sx, sy), (ex, ey) = c["poly"][0], c["poly"][-1]
                vx, vy = ex - sx, ey - sy
                L = math.hypot(vx, vy)
                if L > 0 and (vx * dvec[0] + vy * dvec[1]) < 0.2 * L:  # not clearly running downhill
                    uphill.append(c["to"].get("name", "?"))
            check("channels_flow_downhill", not uphill, f"channel(s) not running downhill (source must be uphill of the field) for downhill={downhill}: {sorted(set(uphill))}")

    # the same flow logic applies to a city MOAT: the moat is fed by a stream entering from one
    # side (the source), so the moat water heads that-source-to-the-far-side direction (Tango's
    # feeder enters from the north, so the moat water heads SOUTH). A moat-fed irrigation channel
    # must run WITH that current - its field-end downstream of its moat-tap. A channel whose field
    # is UPSTREAM of the tap reads as water flowing from the field INTO the moat (backwards).
    moat_ring: Any = M.get("moat")
    mfed = [c for c in channels if (c.get("frm") or {}).get("kind") == "moat"]
    if moat_ring and len(moat_ring) >= 3 and mfed:
        feeder = None
        for st in streams_m:
            ends = (st["poly"][0], st["poly"][-1])
            ends_on_moat = [e for e in ends if poly_dist(e[0], e[1], moat_ring) <= 35]
            if ends_on_moat:
                entry = ends_on_moat[0]
                feeder = (entry, ends[1] if ends[0] == entry else ends[0])
                break
        if feeder:
            entry, origin = feeder
            dx, dy = entry[0] - origin[0], entry[1] - origin[1]  # the heading the feeder water enters on
            flow = (0, 1 if dy > 0 else -1) if abs(dy) >= abs(dx) else (1 if dx > 0 else -1, 0)  # snapped to a cardinal
            against = []
            for c in mfed:
                (sx, sy), (ex, ey) = c["poly"][0], c["poly"][-1]  # frm=moat, so poly[0] is the moat tap
                if (ex - sx) * flow[0] + (ey - sy) * flow[1] < -8:  # field clearly upstream of the tap
                    against.append(c["to"].get("name", "?"))
            check(
                "moat_channels_flow_with_current",
                not against,
                f"moat-fed channel(s) running against the moat current (field is upstream of the tap; the feeder makes the moat flow {flow}): {sorted(set(against))}",
            )

    # large area features (forests, pastures) near a map edge must run OFF it - implying
    # they continue beyond what's drawn. Bounded farm fields are exempt.
    NEAR = 55
    area_feats = [("forest", M["forest"])] if M.get("forest") else []
    area_feats += [(f"forest_patch[{i}]", fp) for i, fp in enumerate(M.get("forest_patches", []))]
    area_feats += [(f"pasture[{i}]", ps) for i, ps in enumerate(M.get("pastures", []))]
    edge_bad = []
    for nm, ol in area_feats:
        xs, ys = [p[0] for p in ol], [p[1] for p in ol]
        if EX1 - NEAR <= max(xs) < EX1:
            edge_bad.append(f"{nm}:right")
        if EX0 < min(xs) <= EX0 + NEAR:
            edge_bad.append(f"{nm}:left")
        if EY1 - NEAR <= max(ys) < EY1:
            edge_bad.append(f"{nm}:bottom")
        if EY0 < min(ys) <= EY0 + NEAR:
            edge_bad.append(f"{nm}:top")
    check("edge_features_run_off_map", not edge_bad, f"edge feature(s) stop short of the edge: {edge_bad}")

    # roads and streams must run off the map edge (a stream may instead end in a pond
    # at one end; irrigation channels are exempt - they connect ponds/fields)
    EDGE = 30

    def at_edge(pt: Pt) -> bool:
        return pt[0] <= EX0 + EDGE or pt[0] >= EX1 - EDGE or pt[1] <= EY0 + EDGE or pt[1] >= EY1 - EDGE

    if road:
        check("road_runs_off_edge", at_edge(road[0]) and at_edge(road[-1]), f"a road must reach the map edge at both ends (ends {road[0]}, {road[-1]})")

    # a CONNECTOR lane (the trodden path leaving the village for the wider world) must run OFF the map
    # edge - it links to a district/Imperial road (or a canal landing) beyond the frame, so it must not
    # stop mid-landscape. Internal lanes (the spine, field spurs) are exempt: they legitimately end in
    # the cluster or at the paddy. See settlements.md 'Village lanes and connecting paths'.
    for i, ln in enumerate(M.get("lanes", [])):
        if ln.get("connector"):
            p = ln["pts"]
            check(
                f"connector_lane_runs_off_edge[{i}]",
                at_edge(p[0]) or at_edge(p[-1]),
                f"the connector path (lane {i}) must run OFF the map edge (ends {p[0]}, {p[-1]}) - it leaves the village for the wider world and must not stop mid-landscape",
            )

    # FARMHOUSES must not sit ON a village lane - a lane lays a no-build corridor and houses FRONT it,
    # never overlap the tread (place lanes BEFORE the houses). Fires if any house footprint corner/center
    # falls within the lane's tread half-width.
    def _house_pts(h: dict[str, Any]) -> list[tuple[float, float]]:
        hw2, hh2 = h["w"] / 2, h["h"] / 2
        return [(h["x"] - hw2, h["y"] - hh2), (h["x"] + hw2, h["y"] - hh2), (h["x"] + hw2, h["y"] + hh2), (h["x"] - hw2, h["y"] + hh2), (h["x"], h["y"])]

    lane_hits = []
    for h in M.get("houses", []):
        for ln in M.get("lanes", []):
            half = ln.get("w", 5) / 2 + 2  # tread half-width + a hair
            p = ln["pts"]
            if any(seg_dist(cx, cy, p[k], p[k + 1]) < half for cx, cy in _house_pts(h) for k in range(len(p) - 1)):
                lane_hits.append((round(h["x"]), round(h["y"])))
                break
    check(
        "houses_clear_of_lanes",
        not lane_hits,
        f"farmhouse(s) sit ON a village lane at {lane_hits[:5]} - a lane is a no-build corridor; houses FRONT it, never overlap the tread (lay lanes BEFORE the houses so they pack around it)",
    )

    # A shrine/temple HALL must not sit ON a lane/street/road: a building stands BESIDE the way, not in it. The
    # TORII is the deliberate exception - a gateway arch straddles the approach path and the road runs UNDER it
    # (a real, common feature), so torii are NOT checked here. The road may run up to and through the torii to a
    # hall set just off the way. Covers religious halls (shrine/monastery/temple). WHY: settlements.md 'Shrines'.
    hall_on_lane = []
    _hcorr = [(ln["pts"], ln.get("w", 6) / 2 + 2) for ln in M.get("lanes", [])]
    _hcorr += [(s["pts"], s.get("w", 10) / 2 + 2) for s in M.get("town_streets", [])]
    if M.get("road"):
        _hcorr.append((M["road"], M.get("road_width", 26) / 2 + 2))
    for hall in M.get("religious", []):
        rect = _struct_rect(hall)
        if any(seg_to_rect_dist(p[k], p[k + 1], rect) < half for p, half in _hcorr for k in range(len(p) - 1)):
            hall_on_lane.append((round(hall["x"]), round(hall["y"])))
    check(
        "shrine_halls_clear_of_lanes",
        not hall_on_lane,
        f"shrine/temple hall(s) sit ON a lane/street/road at {hall_on_lane[:4]} - a HALL stands beside the way, "
        f"not in it (place it off the corridor); the road may pass UNDER the shrine's TORII (arches are exempt), "
        f"but never through the hall itself",
    )

    # TREES must not be drawn ON a lane / street / road - a path is bare trodden earth, not planted over. Covers
    # BOTH the communal fengshui grove (village_groves: each records its actual drawn clump centers + radius) and
    # the per-house windbreak grove (groves: a rect footprint). Every corridor (lanes, town streets, the road) is
    # a keep-out; the generator skips any clump within it, and this verifies nothing slipped through.
    corridors = [(ln["pts"], ln.get("w", 6) / 2) for ln in M.get("lanes", [])]
    corridors += [(s["pts"], s.get("w", 10) / 2) for s in M.get("town_streets", [])]
    if M.get("road"):
        corridors.append((M["road"], M.get("road_width", 26) / 2))
    tree_on_path = []
    for g in M.get("village_groves", []):
        r = g.get("r", 6)
        for cx, cy in g.get("clumps", []):
            if any(seg_dist(cx, cy, p[k], p[k + 1]) < half + r for p, half in corridors for k in range(len(p) - 1)):
                tree_on_path.append((round(cx), round(cy)))
                break
    for g in M.get("groves", []):
        gc = rect_corners(_struct_rect(g)) + [(g["x"], g["y"])]
        if any(seg_dist(cx, cy, p[k], p[k + 1]) < half for cx, cy in gc for p, half in corridors for k in range(len(p) - 1)):
            tree_on_path.append((round(g["x"]), round(g["y"])))
    check(
        "groves_clear_of_lanes",
        not tree_on_path,
        f"tree/grove clump(s) sit ON a lane/street/road at {tree_on_path[:4]} - a path is bare trodden earth; keep vegetation off every corridor (the generator skips clumps within a lane's keep-out)",
    )
    moat_ring = M.get("moat")
    for idx, st in enumerate(M.get("streams", [])):
        e0, e1 = st["poly"][0], st["poly"][-1]

        def in_pond(p: Pt) -> bool:
            return bool(pond) and in_ellipse(p[0], p[1], pond, 1.05)

        def at_moat(p: Pt) -> bool:
            return bool(moat_ring) and poly_dist(p[0], p[1], moat_ring) <= 32  # a city stream may feed the moat

        def at_drain(p: Pt) -> bool:
            return anchored(p, {"kind": "drain"})  # a brook may START at the field drain's outfall

        def in_field(p: Pt) -> bool:
            return any(point_in_poly(p[0], p[1], f["outline"]) for f in fields)  # a SOURCE brook may END at the field head

        def at_ditch(p: Pt) -> bool:
            return any(
                seg_dist(p[0], p[1], dp[i], dp[i + 1]) < 22  # a brook DIVERTED into an irrigation channel
                for d in (M.get("field_ditches", []) + M.get("channels", []))
                for dp in [d["poly"]]
                for i in range(len(dp) - 1)
            )

        ok = all(at_edge(e) or in_pond(e) or at_moat(e) or at_drain(e) or in_field(e) or at_ditch(e) for e in (e0, e1)) and (at_edge(e0) or at_edge(e1))
        check(f"stream_runs_off_edge[{idx}]", ok, f"stream {idx} ends {e0},{e1} must run off the edge (one end may be a pond, the moat, the field drain, or the field head)")

    # WATER SOURCES COME FROM THE MAP EDGE: a pond does not generate water, so any brook FEEDING it (a
    # stream with one end in the pond) must ORIGINATE off-map - it flows in from the edge, not out of
    # nowhere. (A sole-storage / rain-fed pond with no feeder stream is exempt - no inflow to check.)
    if pond:
        unsourced = []
        for st in M.get("streams", []):
            p = st["poly"]
            for near, far in ((p[0], p[-1]), (p[-1], p[0])):
                if in_ellipse(near[0], near[1], pond, 1.05) and not at_edge(far):
                    unsourced.append([round(far[0]), round(far[1])])
        check(
            "pond_fed_from_edge",
            not unsourced,
            f"a stream feeds the pond but its far end {unsourced[:3]} is not at the map edge - a pond's feeder brook must flow IN from off-map (the water source comes from the edge, not nowhere)",
        )

    # THE POND CONNECTS TO THE FIELD's WATER, matching its role. A SOURCE pond (the default) must FEED the
    # field through an irrigation channel that touches the pond; a DRAINAGE pond (meta pond_role="drainage",
    # a reservoir below the fields) must be REACHED BY the field's drain - the drain must actually run into
    # the pond, not stop short of it (the disconnected-drain bug). Either way SOME watercourse endpoint sits
    # in the pond.
    if pond:
        if meta.get("pond_role", "source") == "source":
            wc = [c["poly"] for c in M.get("channels", []) if "pond" in ((c["frm"] or {}).get("kind"), (c["to"] or {}).get("kind"))]
            why = "a source pond must FEED the field through an irrigation channel, but none connects to the pond"
        else:
            wc = [d["poly"] for d in M.get("field_ditches", []) if d.get("role") == "drain"] + [
                c["poly"] for c in M.get("channels", []) if "pond" in ((c["frm"] or {}).get("kind"), (c["to"] or {}).get("kind"))
            ]
            why = "a drainage pond is fed by the field's DRAIN, but the drain does not reach the pond (it stops short of the water)"
        connected = any(in_ellipse(p[0], p[1], pond, 1.12) for poly in wc for p in (poly[0], poly[-1]))
        check("pond_connected_to_field", connected, why)

    # AN IRRIGATION POND DOES NOT SIT ON THE PADDIES. A pond WIRED to the field's water (a source reservoir at
    # the head, or a drainage tameike at the low foot) is a distinct body of water BESIDE or BELOW the field,
    # joined to the crop by a channel - never laid OVER the paddies. So its ellipse must not overlap the field
    # envelope (no rim point inside a field, no field vertex inside it). A DECORATIVE pond not connected to the
    # field's water (a city garden pond) is exempt - it is not part of the irrigation system.
    _pond_wired = any("pond" in ((c.get("frm") or {}).get("kind"), (c.get("to") or {}).get("kind")) for c in M.get("channels", []))
    if pond and fields and _pond_wired:
        _peri = [(pond[0] + pond[2] * math.cos(a), pond[1] + pond[3] * math.sin(a)) for a in [i * math.pi / 12 for i in range(24)]]
        pond_on_field = any(point_in_poly(px, py, fo["outline"]) for px, py in _peri for fo in fields) or any(in_ellipse(v[0], v[1], pond, 1.0) for fo in fields for v in fo["outline"])
        check(
            "pond_clear_of_field",
            not pond_on_field,
            "the pond overlaps the paddy field - a pond is a distinct water body beside/below the field, joined to it by a channel, not laid over the crop (site the pond clear of the field envelope)",
        )

    # DRAINAGE FLOWS DOWNHILL (matches the map's configured slope). We do NOT require the drain to RUN
    # downhill - a collector (akusui) legitimately runs ACROSS the low margin, ~perpendicular to the fall,
    # to gather runoff from every cascade column; a downhill-running drain would collect nothing. What we
    # DO require is that the water never runs UPHILL: the drain's OUTFALL (the end that discharges to the
    # brook / off-map) must be the lower-ground end, and the discharge brook must head downhill. `fall` =
    # projection onto the downhill unit vector (meta.down_deg); higher fall = further downhill = lower ground.
    _dd = M["meta"].get("down_deg")
    if _dd is not None:
        _dv = (math.cos(math.radians(_dd)), math.sin(math.radians(_dd)))

        def fall(p: Pt) -> float:
            return p[0] * _dv[0] + p[1] * _dv[1]

        # REED MARSH sits on the LOW, downhill ground below the paddy (wet rice is reclaimed FROM marsh; the un-
        # reclaimed valley toe stays wetland). So a marsh must lie DOWNHILL of the field it borders - its centroid's
        # fall must exceed the field centroid's; a marsh on the high/dry side would read wrong. WHY: settlements.md 'Marsh'.
        marshes_ = [m for m in M.get("marshes", []) if m.get("role") != "pond_fringe"]  # a pond's reedy MARGIN is a water fringe, not the low valley toe - exempt
        if marshes_ and M.get("fields"):
            fol = M["fields"][0]["outline"]
            fcen = (sum(p[0] for p in fol) / len(fol), sum(p[1] for p in fol) / len(fol))
            high_marsh = [(round(m["x"]), round(m["y"])) for m in marshes_ if fall((m["x"], m["y"])) <= fall(fcen)]
            check(
                "marsh_on_low_ground",
                not high_marsh,
                f"reed marsh {high_marsh[:2]} sits UPHILL of the paddy - marsh is the LOW, undrained valley toe "
                f"below the field (wet rice is reclaimed from marsh), so it must lie downhill (higher fall)",
            )
        streams_ = M.get("streams", [])

        def _near_stream(pt: Pt) -> bool:
            return any(seg_dist(pt[0], pt[1], sp[i], sp[i + 1]) < 30 for st in streams_ for sp in [st["poly"]] for i in range(len(sp) - 1))

        up_drain, up_disch = [], []
        for fd in M.get("field_ditches", []):
            if fd.get("role") != "drain":
                continue
            p = fd["poly"]
            e0, e1 = p[0], p[-1]
            # the OUTFALL is the end that meets a brook or runs off-map (else default to the lower end)
            if _near_stream(e1) or at_edge(e1):
                out, head = e1, e0
            elif _near_stream(e0) or at_edge(e0):
                out, head = e0, e1
            else:
                out, head = (e1, e0) if fall(e1) >= fall(e0) else (e0, e1)
            if fall(out) < fall(head) - 8:  # outfall is UPHILL of the head - water runs backwards
                up_drain.append([round(out[0]), round(out[1])])
        for st in streams_:  # a drainage brook must head downhill off the field
            if (st.get("frm") or {}).get("kind") == "drain":
                p = st["poly"]
                if fall(p[-1]) < fall(p[0]) - 8:
                    up_disch.append([round(p[-1][0]), round(p[-1][1])])
        check(
            "drain_flows_downhill",
            not up_drain,
            f"a drain's OUTFALL {up_drain[:3]} sits UPHILL of its head - water would run backwards; the discharge end of a collector must be its lowest point (per meta.down_deg)",
        )
        check(
            "drainage_discharges_downhill",
            not up_disch,
            f"a drainage brook {up_disch[:3]} runs UPHILL from the drain outfall - it must carry the runoff DOWNHILL (toward the fall direction, meta.down_deg), matching the water flow elsewhere",
        )
        # a collector runs CROSS-SLOPE (roughly along the contour), because it must gather runoff from every
        # cascade column - a drain running with the fall would follow one column and collect nothing. So its
        # direction must be more PERPENDICULAR to the fall than parallel: the along-fall fraction of its
        # head->outfall vector stays below ~0.65 (angle to the fall > ~50 deg). It may descend to carry water
        # to the discharge, but must not run straight downhill like a delivery ditch.
        crossy = []
        for fd in M.get("field_ditches", []):
            if fd.get("role") != "drain":
                continue
            a, b = fd["poly"][0], fd["poly"][-1]
            vx, vy = b[0] - a[0], b[1] - a[1]
            vlen = math.hypot(vx, vy)
            if vlen < 1:  # pragma: no cover - a real drain spans the field's low edge; guards a 0-length poly
                continue
            along = abs(vx * _dv[0] + vy * _dv[1]) / vlen  # |cos(angle to the fall)|
            if along > 0.65:
                crossy.append(round(math.degrees(math.acos(min(1.0, along)))))
        check(
            "drain_runs_cross_slope",
            not crossy,
            f"a drain runs too nearly WITH the slope (only {crossy[:3]} deg off the fall) - a collector must run roughly PERPENDICULAR to the flow (along the contour) to gather every column's runoff",
        )

    # A drainage brook LEAVES the collector as a smooth BEND, not a hard right-angle corner - a contour
    # collector turns down the valley INTO the stream, it does not meet it at 90 deg. For each drain-fed
    # brook, compare the drain's ARRIVAL heading (into the shared outfall) with the brook's DEPARTURE
    # heading (each averaged over ~40px, so short jittery segments do not fool it); the turn must be < 65 deg.
    def _flow_dir(poly: Poly, at_start: bool, span: float = 40.0) -> tuple[float, float]:
        end = poly[0] if at_start else poly[-1]
        ref = end
        for q in poly[1:] if at_start else poly[-2::-1]:
            ref = q
            if math.hypot(q[0] - end[0], q[1] - end[1]) >= span:
                break
        return (ref[0] - end[0], ref[1] - end[1]) if at_start else (end[0] - ref[0], end[1] - ref[1])

    _drains = [fd["poly"] for fd in M.get("field_ditches", []) if fd.get("role") == "drain"]
    sharp = []
    for st in M.get("streams", []):
        if (st.get("frm") or {}).get("kind") != "drain" or len(st["poly"]) < 2:
            continue
        bp = st["poly"]
        near_drain = min(
            (
                (math.hypot(bp[0][0] - dp[e][0], bp[0][1] - dp[e][1]), dp, e)  # the drain it leaves:
                for dp in _drains
                for e in (0, -1)
            ),
            default=None,
        )  # nearest drain endpoint
        if near_drain is None or near_drain[0] > 40 or len(near_drain[1]) < 2:
            continue
        arr, dep = _flow_dir(near_drain[1], at_start=(near_drain[2] == 0)), _flow_dir(bp, at_start=True)
        la, ld = math.hypot(*arr), math.hypot(*dep)
        if la < 1 or ld < 1:  # pragma: no cover - real drains/brooks span the field; guards 0-length polys
            continue
        ang = math.degrees(math.acos(max(-1.0, min(1.0, (arr[0] * dep[0] + arr[1] * dep[1]) / (la * ld)))))
        if ang > 65:
            sharp.append(round(ang))
    check(
        "drainage_junction_smooth",
        not sharp,
        f"a drainage brook leaves the collector at a sharp {sharp[:3]} deg corner - it must CURVE out of "
        f"the drain's heading (a collector turns down the valley into the stream, not a hard right angle)",
    )

    # torii (if any): clear of the shrine and spread out (universal)
    torii = M.get("torii", [])
    if torii:
        shrine = M.get("shrine")
        if shrine:
            sx, sy, sw, sh = shrine
            under = [t for t in torii if sx - 6 <= t[0] <= sx + sw + 6 and sy - 6 <= t[1] <= sy + sh + 6]
            check("torii_clear_of_shrine", not under, f"{len(under)} torii under the shrine")
        spread = all(math.hypot(torii[i][0] - torii[j][0], torii[i][1] - torii[j][1]) > 25 for i in range(len(torii)) for j in range(i + 1, len(torii)))
        check("torii_spread_out", spread, "torii too close together")

    # ---- village-specific expectations (from meta) ---------------------------
    abandoned = sum(1 for h in houses if h["kind"] == "abandoned")
    occupied = len(houses) - abandoned
    if meta.get("households"):
        # occupied farmhouses must portray the declared households ~1:1. A ~5-person
        # home is one nuclear/stem family per roof, and population / 5 = households =
        # farmhouses (GM: "population ~350 so there should be ~70 farmhouses"), so the
        # map DEPICTS close to the full household count - ~0.85-1.05x, allowing a few
        # off-frame homesteads or the odd shared roof. (Supersedes the earlier ~0.7x
        # extended-family assumption: the target is to depict every household.)
        hh = meta["households"]
        if meta.get("toscale", scale == "village"):  # to-scale tiers (village + hamlet) depict ~every household 1:1
            lo, hi = round(0.85 * hh), round(1.05 * hh)
        else:  # legacy tiers still depict ~0.7-0.9 (extended-family sharing, off-frame)
            lo, hi = round(0.68 * hh), round(0.9 * hh)
        check("households_consistent", lo <= occupied <= hi, f"{occupied} occupied houses for ~{hh} households (expect {lo}-{hi}; +{abandoned} abandoned)")
    elif meta.get("target_houses"):
        t = meta["target_houses"]
        lo, hi = round(0.85 * t), round(1.15 * t)
        check("house_count_in_range", lo <= len(houses) <= hi, f"{len(houses)} houses (expect ~{t})")
    elif scale in ("village", "hamlet"):
        lo, hi = (40, 80) if scale == "village" else (10, 30)
        check("house_count_in_range", lo <= len(houses) <= hi, f"{len(houses)} houses (expect {lo}-{hi} for a {scale})")
    if scale == "town":
        # a town must represent its whole non-farmer population at the per-town household
        # counts documented in budgets.md (Town caste table, Families column ~= one
        # building each). Bands allow for RNG fit. Modeling calls baked into the targets:
        #  - servants (~13 households) are ALL drawn as their own dwellings: the population is
        #    counted from dwellings x5 (businesses/gatehouses house no one), so hiding most
        #    servants "inside compounds" would undercount the housing - draw the full ~13.
        #  - merchant DWELLINGS (~24) are counted on their own; shops are additional
        #    business premises (not household-gated).
        #  - samurai: ~4 resident families but a ~15-strong working platoon; show 5-10
        #    houses, the unmarried platoon barracked inside the manor (not drawn).
        bk: dict[str, int] = {}
        for b in M.get("buildings", []):
            bk[b["kind"]] = bk.get(b["kind"], 0) + 1
        farmhouses = len(houses)
        bands = {"merchant": (20, 28), "laborer": (25, 35), "servant": (9, 17), "burakumin": (10, 14), "samurai": (5, 10)}
        # a caste's homes come in size variants (the wealthy get larger houses); count them together
        VARIANTS = {"merchant": ("merchant", "merchant_house", "merchant_large"), "laborer": ("laborer", "laborer_large"), "samurai": ("samurai", "samurai_large")}
        caste_n = {kind: sum(bk.get(k, 0) for k in VARIANTS.get(kind, (kind,))) for kind in bands}
        for kind, (lo, hi) in bands.items():
            c = caste_n[kind]
            check(f"town_caste_count[{kind}]", lo <= c <= hi, f"{kind} buildings {c} outside budgets.md band [{lo},{hi}]")
        non_farmer_max = max(caste_n.values(), default=0)
        # WHY (farmers are the overwhelming majority caste): settlements.md "Historical grounding"
        check("town_farmers_plurality", farmhouses >= non_farmer_max, f"farmhouses {farmhouses} should be the largest single group (max other {non_farmer_max})")
        # MERCHANT and LABORER housing varies in SIZE by wealth, like a provincial city's (budgets.md
        # Town wealth tiers): a MINORITY of merchants are very-rich / rich and live in large homes
        # (~5 of ~24), and a few laborers are 'master/rich' (~2-3 of ~29); the rest live in small/standard
        # dwellings. Require the larger homes (kind merchant_large / laborer_large) to be PRESENT and a
        # CLEAR MINORITY - not that every house is one uniform size.
        m_small = bk.get("merchant", 0) + bk.get("merchant_house", 0)
        m_big = bk.get("merchant_large", 0)
        if m_small + m_big:
            check(
                "town_merchant_housing_varied",
                m_big >= 2 and m_small > m_big,
                f"town merchant housing lacks size variety (budgets.md: ~5 of ~24 merchants are very-rich/rich): "
                f"{m_big} large of {m_small + m_big} - give the wealthy merchants larger homes (kind 'merchant_large'), a clear minority",
            )
        l_small = bk.get("laborer", 0)
        l_big = bk.get("laborer_large", 0)
        if l_small + l_big:
            check(
                "town_laborer_housing_varied",
                l_big >= 2 and l_small > l_big,
                f"town laborer housing lacks size variety (budgets.md: ~2-3 'master/rich' of ~29 laborers): "
                f"{l_big} large of {l_small + l_big} - give the wealthier laborers larger homes (kind 'laborer_large'), a clear minority",
            )
        # MERCHANT RESIDENCES sit BEHIND the merchant BUSINESSES, and CLOSER to the road than the
        # LABORER housing - a clean radial band: shops front the road, the merchant homes directly
        # behind them, then a gap, then the laborers set further back. Scoped to road-fronted towns
        # (those with a trunk M["road"], e.g. unwalled Hoshizora); a walled town's interior grid is laid
        # out around cross-streets, not one radial axis, so this single-axis test does not apply there.
        # droad = perpendicular distance from a building to the nearest road segment.
        rd = M.get("road")
        if rd:

            def _droad(b: dict[str, Any]) -> float:
                return min(seg_dist(b["x"], b["y"], rd[k], rd[k + 1]) for k in range(len(rd) - 1))

            biz = [b for b in M.get("buildings", []) if b.get("kind") in ("shop", "merchant")]
            mres = [b for b in M.get("buildings", []) if b.get("kind") in ("merchant_house", "merchant_large")]
            labs = [b for b in M.get("buildings", []) if b.get("kind") in ("laborer", "laborer_large")]
            mh_problems = []
            if biz and mres:
                maxbiz = max(_droad(b) for b in biz)
                in_biz_band = [b for b in mres if _droad(b) <= maxbiz]
                if in_biz_band:
                    mh_problems.append(f"{len(in_biz_band)} merchant residence(s) sit within the storefront band, not behind it")
                maxres = max(_droad(b) for b in mres)
                if labs:
                    GAP = 35  # min radial gap (px, center-to-center depth) between the merchant-home band and the laborer warren
                    minlab = min(_droad(b) for b in labs)
                    if minlab < maxres + GAP:
                        mh_problems.append(
                            f"laborer housing not set back beyond the merchant residences with a gap "
                            f"(nearest laborer {round(minlab)}px from road vs merchant residences out to {round(maxres)}px; want >= {GAP}px clear)"
                        )
                check(
                    "merchant_residences_behind_businesses",
                    not mh_problems,
                    f"a road-fronted town's merchant residences must sit directly BEHIND the shops, with the laborer housing set FURTHER back and a gap between the two bands: {mh_problems}",
                )
            # HOUSING DIRECTLY BEHIND A STOREFRONT shares the storefront's ORIENTATION: a home tucked
            # right behind a shop (a merchant family over/behind its own premises) must lie PARALLEL to
            # that shop, not askew to it - the block reads as one aligned unit, shopfront then dwelling.
            # "Directly behind" is judged in ROAD coordinates, not raw distance: project each building onto
            # the road to get (along, droad). A home H sits directly behind its nearest shop S when it is at
            # nearly the SAME position ALONG the road (|along_H - along_S| <= ALONG_TOL = in S's radial shadow)
            # AND one building DEEPER (DEPTH_MIN < droad_H - droad_S <= DEPTH_MAX, i.e. immediately behind S,
            # not way back in the warren and not merely beside it). This isolates the home-over-its-shop case
            # from pack-edge dwellings that happen to lie near a shop. Angles compared mod 180 (a 180deg-flipped
            # footprint is still parallel). Road-fronted only - same single-axis scoping as the band check above.
            rcum = [0.0]
            for ki in range(len(rd) - 1):
                rcum.append(rcum[-1] + math.hypot(rd[ki + 1][0] - rd[ki][0], rd[ki + 1][1] - rd[ki][1]))

            def _along(b: dict[str, Any]) -> float:
                bestd, bestt = float("inf"), 0.0
                for k in range(len(rd) - 1):
                    cx, cy = seg_closest(b["x"], b["y"], rd[k], rd[k + 1])
                    d = math.hypot(cx - b["x"], cy - b["y"])
                    if d < bestd:
                        bestd, bestt = d, rcum[k] + math.hypot(cx - rd[k][0], cy - rd[k][1])
                return bestt

            shops = [b for b in M.get("buildings", []) if b.get("kind") in ("shop", "merchant")]
            homes = [b for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS and b.get("kind") != "merchant"]
            ALONG_TOL, DEPTH_MIN, DEPTH_MAX, ANG_TOL = 42, 15, 74, 15
            askew = []
            for h in homes:
                nsh = min(shops, key=lambda s: math.hypot(s["x"] - h["x"], s["y"] - h["y"]), default=None)
                if nsh is None:
                    continue
                if abs(_along(h) - _along(nsh)) > ALONG_TOL:  # not in the shop's radial shadow
                    continue
                if not (DEPTH_MIN < _droad(h) - _droad(nsh) <= DEPTH_MAX):  # beside / far back, not directly behind
                    continue
                d = abs(h.get("rot", 0) - nsh.get("rot", 0)) % 180
                d = min(d, 180 - d)
                if d > ANG_TOL:
                    askew.append((round(h["x"]), round(h["y"]), round(d)))
            check(
                "housing_aligned_behind_storefronts",
                not askew,
                f"housing tucked directly behind a storefront must lie PARALLEL to it (orientation within {ANG_TOL}deg, mod 180); these homes are askew (x, y, mismatch deg): {askew}",
            )
        check("town_has_magistrate_manor", len(M.get("manors", [])) >= 1, "a county-seat town must have the magistrate's manor")
        # a town has hundreds of farmers - we never show all the farmland, so at least
        # one field must run off the map edge (implying more farmland beyond what's drawn)
        off_edge = [f["name"] for f in fields if runs_off_edge(f["outline"])]
        check("town_has_field_off_edge", off_edge, "a town must have at least one field running off the map edge (more farmland implied)")
        # a rice-TRANSIT town (meta(granary=True)) shows a distinct tax-rice granary - a row of
        # fireproof kura where grain gathered from many counties is forwarded up the kick-up
        # chain. A standard county seat does NOT draw one: its grain sits inside the magistrate's
        # yamen, implied by the manor. Opt-in, so the default is no check (unlike the gate
        # market, theater stage, and monasteries, which are opt-OUT defaults).
        if meta.get("granary"):
            check("town_has_granary", bool(M.get("granary")), "meta(granary=True) declares a rice-transit town - it must draw a granary via s.granary(...)")
        # a noticeable MINORITY of merchant houses keep a fireproof storehouse (kura) for their
        # (often absentee) landlords' rent-rice and bulk goods - more than a token 1-2, beyond a
        # shop's ordinary inventory. Draw them with s.merchant_storehouses(...).
        check(
            "town_has_merchant_storehouses",
            len(M.get("storehouses", [])) >= 3,
            f"{len(M.get('storehouses', []))} merchant storehouses - a town's merchant quarter should show several attached kura (call s.merchant_storehouses(...))",
        )
        # a county seat is a market center: peasants from the far edge of its catchment stay
        # over on market eve in a cheap communal flophouse (kichin-yado) where travelers arrive
        # - the gate market of a walled town, the road of an unwalled one. Default-on (>= 1);
        # meta(flophouses=N) requires more (a busy hub); meta(flophouses=0) opts out.
        want_flop = meta.get("flophouses", 1)
        check(
            "town_has_flophouse",
            len(M.get("flophouses", [])) >= want_flop,
            f"{len(M.get('flophouses', []))} flophouses, expected >= {want_flop} (cheap market-day lodging via s.flophouse(...); meta(flophouses=N) to change)",
        )
        # a county town is a stop on the trade route: it needs ONE caravan INN (s.inn) with a STABLES
        # (s.stables) next to it and OPEN GROUND beside the stables - a pasture for the wagon-train oxen
        # and horses - exactly like a provincial city's gate caravan facilities, but a single one. The
        # inn must sit ALONG the road (the Imperial road, or a town street) - the caravans pull up to it -
        # NOT buried behind the shop rows. A WALLED town keeps it INSIDE the rampart (caravans enter the gate).
        inns = [b for b in M.get("buildings", []) if b.get("kind") == "inn"]
        stbl = [b for b in M.get("buildings", []) if b.get("kind") == "stables"]
        cwall = M.get("wall")
        routes = ([M["road"]] if M.get("road") else []) + [s["pts"] for s in M.get("town_streets", [])]
        others = [b for b in M.get("buildings", []) if b.get("kind") not in ("inn", "stables")]
        dwell_t = [b for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS] + M.get("houses", [])
        caravan_ok, why = False, f"inn={len(inns)} stables={len(stbl)}"
        for inn in inns:
            near_st = [s for s in stbl if math.hypot(s["x"] - inn["x"], s["y"] - inn["y"]) <= 150]
            if not near_st:
                why = "the inn has no stables beside it"
                continue
            st = near_st[0]
            if meta.get("walled") and cwall and not (point_in_poly(inn["x"], inn["y"], cwall) and point_in_poly(st["x"], st["y"], cwall)):
                why = "the caravan inn + stables must be INSIDE the walls"
                continue
            crowd = sum(1 for d in dwell_t if math.hypot(d["x"] - st["x"], d["y"] - st["y"]) < 75)
            if crowd > 4:
                why = f"the stables is hemmed in by {crowd} dwellings (it needs open ground - a pasture for the animals)"
                continue
            if routes and not _fronts_route(inn["x"], inn["y"], routes, others):
                why = "the inn sits BEHIND the shop rows - it must front the road/main street (caravans pull up to it)"
                continue
            caravan_ok = True
            break
        check(
            "town_has_caravan_inn",
            caravan_ok,
            f"a county town needs ONE caravan INN with a STABLES beside it, OPEN GROUND for the wagon-train animals, and "
            f"FRONTING the road (inside the walls if walled): {why} - add s.inn(...) + s.stables(...), like a provincial city's gate facilities but a single one",
        )
        # the inn FACES the road and lies PARALLEL to it - the caravans pull straight up to it - so its
        # noren front (the +y edge after the inn's `rot`) must point at the nearest route point, which also
        # makes its long frontage edge run along the road. A diagonal road needs a tilted inn.
        unaligned = []
        for inn in inns:
            npt, bd = None, 1e18
            for r in routes:
                for ki in range(len(r) - 1):
                    cx, cy = seg_closest(inn["x"], inn["y"], r[ki], r[ki + 1])
                    d = math.hypot(cx - inn["x"], cy - inn["y"])
                    if d < bd:
                        bd, npt = d, (cx, cy)
            if npt is None or bd < 1:
                continue
            dx, dy = (npt[0] - inn["x"]) / bd, (npt[1] - inn["y"]) / bd
            th = math.radians(inn.get("rot", 0))
            fn = (-math.sin(th), math.cos(th))  # the +y front's outward normal after rot
            if fn[0] * dx + fn[1] * dy < 0.88:  # within ~28deg of facing the nearest road point
                unaligned.append((round(inn["x"]), round(inn["y"])))
        if routes:
            check(
                "inn_faces_the_road",
                not unaligned,
                f"caravan inn(s) not oriented to FACE the road and lie parallel to it: {unaligned[:3]} - tilt the inn "
                f"(s.inn(x, y, rot=...)) so its noren front faces the roadbed and its long edge runs along the road",
            )
        # every town has a THEATER STAGE unless meta(theater_stage=False); for a walled town
        # it sits INSIDE the walls unless meta(theater_stage="outside")
        ts_meta = meta.get("theater_stage", True)
        amph = M.get("theater_stage")
        if ts_meta is not False:
            check("town_has_theater_stage", bool(amph), "a town must have a theater stage (set meta(theater_stage=False) to omit)")
        if amph and meta.get("walled") and ts_meta != "outside":
            w = M.get("wall") or []
            check(
                "theater_stage_inside_wall",
                len(w) >= 3 and point_in_poly(amph["x"], amph["y"], w),
                "a walled town's theater stage belongs inside the walls (set meta(theater_stage='outside') to allow outside)",
            )
        check_theater_stage(M, check)
        check_fire_features(M, check)  # geometry of any fire towers (presence required only for a WALLED town, below)

        # a town's monasteries: by default 2, dedicated to the patron fortunes of the clan
        # whose holdings include it (meta(clan=...)). Override with an explicit list -
        # meta(monastery_fortunes=[...]) - for a town that changed hands, or a 1-monastery town.
        monks = [r for r in M.get("religious", []) if r.get("kind") == "monastery"]

        def _fortune(r: dict[str, Any]) -> str:
            lab = (r.get("label") or "").strip()
            return lab.rsplit(" of ", 1)[-1].strip() if " of " in lab else lab

        declared = meta.get("monastery_fortunes")
        clan = meta.get("clan")
        if declared is None and clan:
            cf = CLAN_FORTUNES.get(clan.lower())
            check("town_clan_known", cf is not None, f"unknown clan {clan!r} - no patron fortunes")
            declared = sorted(cf) if cf else None
        check("town_declares_monasteries", declared is not None, "a town must declare its monasteries via meta(clan=...) or meta(monastery_fortunes=[...])")
        if declared is not None:
            check("town_monastery_count", len(monks) == len(declared), f"{len(monks)} monasteries, expected {len(declared)} for {sorted(declared)}")
            got = sorted(_fortune(r) for r in monks)
            check("town_monasteries_dedicated", got == sorted(declared), f"monasteries dedicated to {got}, expected {sorted(declared)}")

    # A magistrate's manor sits at the EDGE of its settlement; its gate faces what it fronts - the
    # town/hamlet it administers (the built-up centroid) OR the Imperial road it sits beside. There is
    # no fixed default direction (it depends where the town is); SOUTH is the formal fallback. (At CITY
    # scale M['manors'] are the scattered country estates, which face their own lanes - city_estate_gates_vary.)
    if scale in ("hamlet", "town") and M.get("manors"):
        GATE_OUT = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
        dwell_all = M.get("houses", []) + M.get("buildings", [])
        mroad = M.get("road")
        bad_mg = []
        for mn in M.get("manors", []):
            o = GATE_OUT.get(mn.get("gate_dir"), (0, 0))
            ang = math.radians(mn.get("rot", 0))
            ovec = (o[0] * math.cos(ang) - o[1] * math.sin(ang), o[0] * math.sin(ang) + o[1] * math.cos(ang))
            dirs = []
            if dwell_all:
                tvx = sum(b["x"] for b in dwell_all) / len(dwell_all) - mn["x"]
                tvy = sum(b["y"] for b in dwell_all) / len(dwell_all) - mn["y"]
                tl = math.hypot(tvx, tvy) or 1
                dirs.append((tvx / tl, tvy / tl))
            if mroad:
                rp = min((seg_closest(mn["x"], mn["y"], mroad[k], mroad[k + 1]) for k in range(len(mroad) - 1)), key=lambda c: (c[0] - mn["x"]) ** 2 + (c[1] - mn["y"]) ** 2)
                rvx, rvy = rp[0] - mn["x"], rp[1] - mn["y"]
                rl = math.hypot(rvx, rvy) or 1
                dirs.append((rvx / rl, rvy / rl))
            if dirs and max(ovec[0] * d[0] + ovec[1] * d[1] for d in dirs) < 0.45:
                bad_mg.append(mn.get("gate_dir"))
        check(
            "manor_gate_faces_town",
            not bad_mg,
            f"a magistrate's manor gate {bad_mg} faces neither the town it administers nor the road it fronts - "
            f"it sits at the settlement's edge, so its gate should open toward the town/road (no fixed default; south is the formal fallback)",
        )

    if scale == "town" and meta.get("walled"):
        check("walled_town_has_wall", bool(M.get("wall")) and bool(M.get("gate")), "a walled town must have a wall and a gate")
        # the dense, ENCLOSED wooden core needs a fire-watch tower over its rooftops (the wall that
        # keeps raiders out also traps a fire in); an OPEN road-town relies on its road and field gaps
        # and gets none. WHY: settlements.md "Fire towers". Opt out per-map with meta(fire_tower=False).
        if meta.get("fire_tower", True):
            check("walled_town_has_fire_tower", len(M.get("fire_towers", [])) >= 1, "a walled town's dense wooden core needs a fire-watch tower (s.fire_tower(...); meta(fire_tower=False) to omit)")
        w = M.get("wall") or []
        if len(w) >= 3:
            lens = [math.hypot(w[i + 1][0] - w[i][0], w[i + 1][1] - w[i][1]) for i in range(len(w) - 1)]
            # "irregular" = not a regular polygon: high spread in section lengths. A
            # coefficient of variation (stdev/mean) test, unlike a pairwise-equal test,
            # allows a wall to hug a feature with several short segments (the chrysanthemum
            # field) while still failing a lazy near-equal-sided wall.
            mean = sum(lens) / len(lens)
            cov = (sum((ln - mean) ** 2 for ln in lens) / len(lens)) ** 0.5 / mean if mean else 0
            check("wall_sections_irregular", len(lens) >= 5 and cov >= 0.25, f"wall has {len(lens)} sections, length CoV {cov:.2f} (need >= 5 sections and CoV >= 0.25 for an irregular rampart)")
        # the gate-to-yamen axis: a main street must run inward from the gate
        gate: Any = M.get("gate")
        mains = [st for st in M.get("town_streets", []) if st.get("main")]
        has_main = bool(gate) and any(min(math.hypot(p[0] - gate[0], p[1] - gate[1]) for p in st["pts"]) < 75 for st in mains)
        check("walled_town_has_main_street", has_main, "a walled town needs a main street running inward from the gate (the gate-to-yamen axis)")

        # no "street to nowhere": a street exists to give access to the buildings along it,
        # and is paved/worn by the traffic to and from them - so no long INSIDE-the-walls
        # stretch may be empty of buildings. (Buildings off any street are fine; that's the
        # poor who can't afford street frontage.) The map edge / off-wall approach is exempt.
        empty = empty_street_runs(M, w)
        check(
            "streets_have_buildings",
            not empty,
            f"street(s) with a stretch inside the walls with no building FRONTING it (a street with no buildings would not exist - trim it or move buildings onto it): {empty}",
        )

        # a wall is expensive: it should HUG the built-up town, not enclose large empty
        # margins. Terrain can justify some slack (a wall climbs/skirts a hill rather than
        # leveling it), so the hill counts as filled "occupancy". Flag a long contiguous
        # stretch of wall whose inside is empty of any building, feature, or terrain - that
        # length of wall would not have been built; a tighter line costs less.
        if len(w) >= 3:
            occ = [(b["x"], b["y"]) for b in M.get("buildings", []) + houses if point_in_poly(b["x"], b["y"], w)]
            for ff in M.get("flower_fields", []):
                occ += [(p[0], p[1]) for p in ff["outline"][::3]]
            occ += [(r["x"], r["y"]) for r in M.get("religious", [])] + [(mn["x"], mn["y"]) for mn in M.get("manors", [])]
            amph = M.get("theater_stage")
            if amph:
                occ.append((amph["x"], amph["y"]))
            hill = M.get("hill")

            def occ_dist(x: float, y: float) -> float:
                d = min((math.hypot(ox - x, oy - y) for ox, oy in occ), default=1e9)
                if hill:
                    hx, hy, hrx, hry = hill
                    if ((x - hx) / hrx) ** 2 + ((y - hy) / hry) ** 2 <= 1.0:
                        return 0.0  # on the hill - terrain occupancy
                    d = min(d, min(math.hypot(hx + math.cos(math.tau * k / 48) * hrx - x, hy + math.sin(math.tau * k / 48) * hry - y) for k in range(48)))
                return d

            MAXGAP, EMPTY_RUN, STEP = 140, 280, 25
            run = worst = 0
            for ki in range(len(w) - 1):
                (ax, ay), (bx, by) = w[ki], w[ki + 1]
                for j in range(max(1, int(math.hypot(bx - ax, by - ay) // STEP))):
                    t = j / max(1, int(math.hypot(bx - ax, by - ay) // STEP))
                    if occ_dist(ax + (bx - ax) * t, ay + (by - ay) * t) > MAXGAP:
                        run += STEP
                        worst = max(worst, run)
                    else:
                        run = 0
            check("wall_hugs_the_town", worst <= EMPTY_RUN, f"~{worst:.0f}px of wall runs more than {MAXGAP}px from any building or terrain (it encloses empty space - draw a tighter wall)")

        # a town monastery fronts a torii AVENUE whose number of arches is set by the open
        # approach in front of it: a grand monastery with a long clear run to the street shows
        # several arches; one wedged into a corner (the Benten monastery, hard against the west
        # wall and the Imperial field) shows a single arch. This fires ONLY for monasteries and
        # ONLY inside a wall - village SHRINES are exempt (they get 0-1 torii regardless). Each
        # torii is assigned to its nearest monastery; the approach direction is taken from the
        # monastery toward that group of torii, and the available span runs to the first street/
        # field/wall/edge (approach_span, which ignores buildings - the avenue displaces them).
        monks = [r for r in M.get("religious", []) if r.get("kind") == "monastery"]
        if monks and torii:
            PITCH = 55  # approx spacing between arches along a sando
            bad_torii = []
            for m in monks:
                grp = [t for t in torii if min(monks, key=lambda r: math.hypot(r["x"] - t[0], r["y"] - t[1])) is m]
                n = len(grp)
                if n:
                    cx, cy = sum(t[0] for t in grp) / n, sum(t[1] for t in grp) / n
                    dlen = math.hypot(cx - m["x"], cy - m["y"]) or 1.0
                    span = approach_span(m["x"], m["y"], m["h"] / 2, (cx - m["x"]) / dlen, (cy - m["y"]) / dlen, M, w, Wd, Hd)
                else:
                    span = 0.0
                lo, hi = max(1, round(span / PITCH) - 1), round(span / PITCH) + 1
                if not (lo <= n <= hi):
                    bad_torii.append((m.get("label"), f"{n} torii", f"want {lo}-{hi}", f"~{span:.0f}px"))
            check(
                "monastery_torii_scale_with_space",
                not bad_torii,
                f"a walled-town monastery's torii avenue should fill its approach space (a roomy approach wants several arches, a cramped one a single arch): {bad_torii}",
            )

        # a walled town almost always accretes a small extramural MARKET (a Chinese guan-xiang)
        # just outside its gate: the gate is a chokepoint where the rural population trades
        # without entering the walls, travelers buy services, and vendors dodge the intramural
        # tax and market regulation. So a few businesses should sit OUTSIDE the wall near the
        # gate - unless the town opts out with meta(gate_market=False) (a purely military fort,
        # or a depopulated / suppressed gate).
        if meta.get("gate_market", True):
            gate = M.get("gate")
            if gate and len(w) >= 3:
                outside_biz = [
                    b for b in M.get("buildings", []) if b.get("kind") in ("shop", "merchant") and not point_in_poly(b["x"], b["y"], w) and math.hypot(b["x"] - gate[0], b["y"] - gate[1]) <= 420
                ]
                check(
                    "walled_town_has_gate_market",
                    len(outside_biz) >= 3,
                    f"{len(outside_biz)} business(es) outside the gate - a walled town has a small gate market (guan-xiang) of a few shophouses unless meta(gate_market=False)",
                )

    if scale == "city":
        # A PROVINCIAL CITY (budgets.md: ~2,000-4,000, avg ~3,000; 600 households - servants 120,
        # laborers 240, merchants 150, burakumin 30, samurai 60; ZERO in-city farmers). Placing
        # all 600 is unreadable, so the map shows REPRESENTATIVE neighborhoods and these checks
        # verify the required STRUCTURES + neighborhood presence, not a full per-caste headcount.
        bk = {}
        for b in M.get("buildings", []):
            bk[b.get("kind")] = bk.get(b.get("kind"), 0) + 1
        # every provincial city's interior carries the provincial government:
        check("city_has_governor_mansion", bool(M.get("governor_mansion")), "a provincial city must have the governor's mansion (s.governor_mansion(...))")
        mins = M.get("ministries", [])
        check("city_has_six_ministries", len(mins) == 6, f"{len(mins)} provincial ministry offices, expected exactly 6 (s.ministry(...))")
        rites = [m for m in mins if "rites" in (m.get("name") or "").lower()]
        check("city_has_ministry_of_rites", len(rites) == 1, f"{len(rites)} Ministry of Rites office(s), expected exactly 1 (sited in the temple neighborhood)")
        sam_n = bk.get("samurai", 0) + bk.get("samurai_large", 0)
        check("city_has_samurai_neighborhood", sam_n >= 8, f"{sam_n} samurai houses - a provincial city needs a samurai neighborhood")
        # a provincial city is ~10% samurai (~300 of ~3,000, budgets.md) - about pop/50 households.
        # Most are housed in the samurai neighborhood as individual houses; the governor's compound
        # and the extramural estates hold the rest. Require the neighborhood to depict at least ~65%
        # of that expected household count, so it is a real quarter, not a token cluster of a few.
        samurai_h = [b for b in M.get("buildings", []) if b.get("kind") in ("samurai", "samurai_large")]
        pop = meta.get("population", 0)
        if pop:
            need = round(0.65 * (0.10 * pop / HOUSEHOLD))
            check(
                "city_samurai_housing_sufficient",
                len(samurai_h) >= need,
                f"only {len(samurai_h)} samurai houses for a ~{round(0.10 * pop)}-samurai city (~{round(0.10 * pop / HOUSEHOLD)} households); "
                f"expect >= {need} in the neighborhood (the governor's compound + extramural estates hold the rest)",
            )
        # samurai (unlike the poor, who sit in the deep block cores) LINE their streets - many houses
        # front a street even if deeper lots sit behind. Require at least a third near a street/road.
        if samurai_h:
            slines = [st["pts"] for st in M.get("town_streets", [])] + ([M["road"]] if M.get("road") else [])
            near_ct = sum(1 for b in samurai_h if any(seg_dist(b["x"], b["y"], sp[i], sp[i + 1]) < 90 for sp in slines for i in range(len(sp) - 1)))
            check(
                "city_samurai_partly_front_streets", near_ct >= len(samurai_h) / 3, f"only {near_ct}/{len(samurai_h)} samurai houses front a street (want >= 1/3) - a samurai quarter lines its streets"
            )
        # SAMURAI HOUSING varies in size by rank, UNLIKE a uniform cluster. budgets.md's provincial-city
        # rank table puts ~25% of resident samurai in the senior ranks (R5-7) and the rest in R1-4; so the
        # in-city neighborhood mixes a MINORITY of large houses (senior) among many small ones (junior).
        # Crucially, samurai walled ESTATES are OUTSIDE the walls (rural goshi) - the only walled samurai
        # compound inside the city is the governor's mansion - so NO manor may sit inside the wall ring.
        slarge = [b for b in M.get("buildings", []) if b.get("kind") == "samurai_large"]
        ssmall = [b for b in M.get("buildings", []) if b.get("kind") == "samurai"]
        if slarge or ssmall:
            w = M.get("wall") or []
            in_est = [m for m in M.get("manors", []) if len(w) >= 3 and point_in_poly(m["x"], m["y"], w)]
            check(
                "city_samurai_housing_varied",
                len(slarge) >= 3 and len(ssmall) > len(slarge) and not in_est,
                f"samurai housing lacks size variety or has in-wall estates (large city houses={len(slarge)}, "
                f"small={len(ssmall)}, walled estates inside the city={len(in_est)}) - senior ranks get large city "
                f"houses, juniors small ones, and samurai walled estates sit OUTSIDE the walls (only the "
                f"governor's mansion is walled within)",
            )
        check("city_has_merchant_district", bk.get("merchant", 0) >= 12, f"{bk.get('merchant', 0)} merchant houses - a provincial city needs a merchant district")
        check(
            "city_has_laborer_neighborhoods",
            bk.get("laborer", 0) + bk.get("laborer_large", 0) >= 12,
            f"{bk.get('laborer', 0) + bk.get('laborer_large', 0)} laborer dwellings - a provincial city needs laborer neighborhoods",
        )
        # LABORER HOUSING VARIES BY WEALTH, like the samurai and merchant tiers: budgets.md's provincial-city
        # laborer cohort is ~12.5% "master" (rich) laborers, the rest standard - so a MINORITY of larger homes
        # (kind "laborer_large", the wealthier hinin who line the prime back-street frontage, with room around
        # them) among the overwhelming majority of small standard dwellings. The exact share is room-limited
        # (the big homes need street frontage), so the band is generous around the 12.5% target; the point is
        # that the variety is PRESENT and a clear minority, not that every laborer dwelling is identical.
        lab_std, lab_big = bk.get("laborer", 0), bk.get("laborer_large", 0)
        if lab_std + lab_big:
            big_frac = lab_big / (lab_std + lab_big)
            check(
                "city_laborer_housing_varied",
                0.06 <= big_frac <= 0.20 and lab_std > lab_big,
                f"laborer houses don't vary by wealth the way budgets.md expects (~12.5% larger 'master/rich' homes, "
                f"the rest standard): {lab_big} large of {lab_std + lab_big} ({big_frac:.0%}; want a clear minority, "
                f"~6-20%) - give the wealthier laborers (the ones fronting the back streets, with room) larger homes "
                f"(kind 'laborer_large')",
            )
        # the city's CASTE MIX must match budgets.md, not just the total head-count: a provincial city is
        # ~40% laborer / 20% servant / 25% merchant / 10% samurai / 5% burakumin of its ~600 households.
        # The total-population check alone lets the mix DRIFT (e.g. laborers absorbing everyone else's
        # slots, servants starved to near-zero because they were appended to the END of a pack list), so
        # each caste is held within +/-30% of its target. Servants live among the merchants/samurai they
        # serve - INTERLEAVE them into those packs rather than tacking them on the end.
        cpop = meta.get("population", 0)
        if cpop:
            caste = {
                "laborer": bk.get("laborer", 0) + bk.get("laborer_large", 0),
                "servant": bk.get("servant", 0),
                "merchant": bk.get("merchant", 0) + bk.get("merchant_house", 0) + bk.get("merchant_large", 0) + len(M.get("merchant_estates", [])),
                "samurai": bk.get("samurai", 0) + bk.get("samurai_large", 0) + len(M.get("manors", [])),
                "burakumin": bk.get("burakumin", 0),
            }
            frac = {"laborer": 0.40, "servant": 0.20, "merchant": 0.25, "samurai": 0.10, "burakumin": 0.05}
            hh = cpop / HOUSEHOLD
            off = []
            for ck, fr in frac.items():
                tgt = fr * hh
                if not (0.70 * tgt <= caste[ck] <= 1.30 * tgt):
                    off.append(f"{ck} {caste[ck]} (want ~{round(tgt)})")
            check(
                "city_caste_counts_in_band",
                not off,
                f"city caste mix is off the budgets.md targets - each caste should be within +/-30% of "
                f"~40% laborer / 20% servant / 25% merchant / 10% samurai / 5% burakumin of {round(hh)} households: {off}",
            )
        # MERCHANT HOUSING is varied and roomy, UNLIKE the uniform, jammed laborer warren. Behind the
        # storefronts the homes mix sizes by wealth band (budgets.md: very rich -> walled ESTATES, rich
        # -> LARGE houses, the rest -> small houses) and are SPREAD OUT - more room between them than the
        # densely-packed laborers (a few denser merchant blocks are fine; the median is robust to those).
        # ROW-PACKING doctrine (GM, 2026-07): city commoner housing is CONTIGUOUS - the
        # machiya/nagaya fabric of party walls and touching eaves, not detached-with-yard.
        # Real urban commoners packed into terraces (street frontage was taxed and precious;
        # a back-lot nagaya was one roof over a row of family units; Chinese county-seat
        # courtyard housing shared party walls in continuous street walls). Measured on the
        # pre-doctrine Tango: median nearest-neighbor gap was 12px (~31 ft) with ZERO
        # touching pairs - a suburb, not a city quarter. Gaps allowed: a hairline seam
        # (<=1.2px, touching), the ~3-6 ft eave gap between back-to-back rows, courts,
        # and street/roji breaks - but the QUARTER-WIDE stats must read as terraces.
        rowk = [b for b in M.get("buildings", []) if b.get("kind") in ("laborer", "servant", "burakumin", "merchant_house")]
        if len(rowk) >= 20:

            def _egap(a: dict[str, Any], b: dict[str, Any]) -> float:
                dx = abs(a["x"] - b["x"]) - (a["w"] + b["w"]) / 2
                dy = abs(a["y"] - b["y"]) - (a["h"] + b["h"]) / 2
                return float(max(dx, dy))

            _gaps = sorted(min(_egap(a, b) for j, b in enumerate(rowk) if j != i) for i, a in enumerate(rowk))
            _touch = sum(1 for g in _gaps if g <= 1.2)
            check(
                "city_row_housing_touches",
                _touch >= 0.55 * len(rowk),
                f"only {_touch}/{len(rowk)} row-class dwellings (laborer/servant/burakumin/merchant_house) TOUCH a "
                f"neighbor - city commoner housing is contiguous terraces (party walls), not detached houses",
            )
            _med = _gaps[len(_gaps) // 2]
            check(
                "city_row_housing_gap",
                _med <= 2.0,
                f"median nearest-neighbor edge gap among row-class dwellings is {_med:.1f}px - the quarter reads as scattered houses, not terraces (want <= 2px: a party wall or a ~3-6 ft eave gap)",
            )
        mlarge = [b for b in M.get("buildings", []) if b.get("kind") == "merchant_large"]
        msmall = [b for b in M.get("buildings", []) if b.get("kind") == "merchant_house"]
        mest = M.get("merchant_estates", [])
        if mlarge or msmall:  # a merchant district whose homes are drawn
            check(
                "city_merchant_housing_varied",
                len(mest) >= 1 and len(mlarge) >= 3 and len(msmall) >= 1,
                f"merchant housing lacks variety (walled estates={len(mest)}, large houses={len(mlarge)}, small houses={len(msmall)}) - "
                f"a merchant quarter mixes small/average houses, LARGE (rich) houses and a few WALLED ESTATES, not one uniform size",
            )
            homes = [(b["x"], b["y"]) for b in mlarge + msmall]
            labor = [(b["x"], b["y"]) for b in M.get("buildings", []) if b.get("kind") == "laborer"]
            if len(homes) >= 5 and len(labor) >= 5:

                def med_nn(pts: Sequence[Pt]) -> float:
                    nn = sorted(min(math.hypot(p[0] - q[0], p[1] - q[1]) for j, q in enumerate(pts) if j != i) for i, p in enumerate(pts))
                    return nn[len(nn) // 2]

                mh, lh = med_nn(homes), med_nn(labor)
                check(
                    "city_merchant_housing_spread",
                    mh >= 1.3 * lh,
                    f"merchant homes are not more SPREAD OUT than the laborers (median neighbor gap {mh:.0f}px vs laborer {lh:.0f}px; want >= 1.3x) - "
                    f"give merchant houses more room between them; the laborer warren is the dense, uniform contrast",
                )
        check("city_has_outside_farmland", bool([f for f in fields if runs_off_edge(f["outline"])]), "a city has extensive farmland outside its walls - at least one field must run off the map edge")
        # civic amenities ported up from the town tier (a city is a bigger version of the same):
        check(
            "city_has_merchant_storehouses",
            len(M.get("storehouses", [])) >= 5,
            f"{len(M.get('storehouses', []))} merchant storehouses - a city's merchant district keeps fireproof kura (s.merchant_storehouses(...))",
        )
        check("city_has_flophouse", len(M.get("flophouses", [])) >= 1, "a provincial city is a major market center and needs market-day lodging (s.flophouse(...))")
        check("city_has_theater_stage", bool(M.get("theater_stage")), "a provincial city needs a theater stage (s.theater_stage(...))")
        check_theater_stage(M, check)
        # a CITY theater stage is bigger than a town's (towns run a viewing ground ~150 wide) - a provincial
        # city draws a larger crowd, so its viewing ground is wider (>= 185, the city baseline)
        amph = M.get("theater_stage")
        if amph:
            # compared in REAL FEET via the declared scale (meta ftpx, default 1): a town's stage
            # is ~150 ft wide, so a provincial city's must be >= 185 ft - the old 185px threshold
            # assumed the pre-ladder ~1 ft/px grain and would silently pass a to-scale city map
            # whose stage shrank in pixels while staying honest in feet
            _ftpx = meta.get("ftpx", 1)
            check(
                "city_theater_stage_larger_than_town",
                amph.get("w", 0) * _ftpx >= 185,
                f"the city theater stage (viewing ground ~{round(amph.get('w', 0) * _ftpx)} ft wide) is no bigger than a town's - a provincial city's is larger (>= 185 ft)",
            )
        # FIRE DEFENSE: a city's dense quarters each need a fire-watch tower (hinomi-yagura). WHY:
        # settlements.md "Fire towers". Opt out per-map with meta(fire_tower=False).
        if meta.get("fire_tower", True):
            nft = len(M.get("fire_towers", []))
            check("city_has_fire_towers", nft >= 2, f"{nft} fire towers - a provincial city's dense quarters each need a fire-watch tower (>= 2; s.fire_tower(...); meta(fire_tower=False) to omit)")
        check_fire_features(M, check)

        # A NAMED civic building's label must sit on ITS OWN building, never on a DIFFERENT one of the
        # same kind. labels_clear_of_other_buildings lumps every ministry into one "ministry" GROUP, so
        # it permits a ministry label to sit on a SIBLING ministry (the "Ministry of Justice" label
        # drifted onto the "Ministry of Works" office). This catches that finer case: a label that names
        # a civic building (a ministry by name, the governor's yamen, a named temple) must not overlap
        # any OTHER named civic building.
        civic = [(mi["name"], _bb(mi)) for mi in M.get("ministries", []) if mi.get("name")]
        _gv = M.get("governor_mansion")
        if _gv and _gv.get("label"):
            civic.append((_gv["label"], _bb(_gv)))
        civic += [(r["label"], _bb(r)) for r in M.get("religious", []) if r.get("label") and r.get("kind") == "temple"]
        civic_names = {n for n, _ in civic}
        cross = []
        for L in M.get("labels", []):
            if len(L) <= 5 or L[5] not in civic_names:
                continue
            for n, (x0, y0, x1, y1) in civic:
                if n != L[5] and L[0] < x1 and x0 < L[2] and L[1] < y1 and y0 < L[3]:
                    cross.append(f"{L[5]!r} over {n!r}")
        check("city_civic_label_on_its_own_building", not cross, f"a civic building's label sits on a DIFFERENT civic building (not the one it names): {sorted(set(cross))}")

        # GOVERNMENT OFFICES stand in their own ground - a ministry or the governor's yamen is a large,
        # important compound and must not ABUT another structure. Ordinary city houses may touch each
        # other, but a government office keeps a clear gap from every other building/compound around it.
        OFFICE_GAP = 14
        offices = ([("the governor's yamen", _gv)] if _gv else []) + [(mi.get("name", "a ministry"), mi) for mi in M.get("ministries", [])]
        others = M.get("buildings", []) + M.get("ministries", []) + M.get("religious", []) + M.get("flophouses", []) + M.get("merchant_estates", []) + ([_gv] if _gv else [])

        def _edge_gap(a: dict[str, Any], b: dict[str, Any]) -> float:
            ax0, ay0, ax1, ay1 = _bb(a)
            bx0, by0, bx1, by1 = _bb(b)
            return math.hypot(max(0.0, ax0 - bx1, bx0 - ax1), max(0.0, ay0 - by1, by0 - ay1))

        abut = []
        for nm, o in offices:
            for st in others:
                if st is not o and "w" in st and _edge_gap(o, st) < OFFICE_GAP:
                    abut.append(f"{nm!r} abuts {(st.get('name') or st.get('label') or st.get('kind') or 'a building')!r}")
        check(
            "city_government_offices_dont_abut", not abut, f"government office(s) abutting another structure - a ministry / the yamen must stand clear, not touch ({OFFICE_GAP}px): {sorted(set(abut))}"
        )

        # PUBLIC WELLS: ensuring every commoner could draw water was a defining civic concern of a
        # premodern city. A communal well (the idobata) served a courtyard / cluster of ~10-20
        # households, so the warren is dotted with them - one within a short walk of any home. The
        # underground half of the system (aqueducts, cisterns, rain barrels feeding the shafts) is too
        # small or literally subterranean and stays OFF the map; only the wellheads show.
        wells = M.get("wells", [])
        if wells:
            wp = M.get("wall") or []
            inw: Any = (lambda x, y: point_in_poly(x, y, wp)) if len(wp) >= 3 else (lambda x, y: True)  # noqa: E731
            # WATER ACCESS: every commoner dwelling INSIDE the walls (laborer/burakumin/merchant kinds;
            # samurai have private wells in their compounds, and a transient gate market outside the wall
            # is not housing) must have a public well within reach. Servants are interleaved among the
            # commoners and share the same wells, so they ride along. A dwelling too far from any well is
            # a neighborhood the water network forgot.
            REACH = 290
            COMMON = {"laborer", "laborer_large", "burakumin", "merchant", "merchant_house", "merchant_large"}
            dry = [
                (round(b["x"]), round(b["y"]))
                for b in M.get("buildings", [])
                if b.get("kind") in COMMON and inw(b["x"], b["y"]) and min(math.hypot(b["x"] - w["x"], b["y"] - w["y"]) for w in wells) > REACH
            ]
            check(
                "city_neighborhoods_have_wells",
                not dry,
                f"{len(dry)} commoner dwelling(s) inside the walls more than {REACH}px from any public well - every neighborhood needs water access; scatter wells through the warren (e.g. {dry[:3]})",
            )
            # and ENOUGH wells that none is OVER-BURDENED: a communal well historically served a courtyard
            # / cluster of ~10-20 households, so assigning each commoner dwelling (servants included - they
            # draw here too) to its NEAREST well, no well should end up doing the work of three. The reach
            # check guarantees coverage but not density - the AVERAGE can look fine while the busiest wells
            # in the dense laborer warren are swamped - so this bounds the per-well share. (The nearest-well
            # split over-counts a little where two wells are nearly equidistant, so the ceiling sits a touch
            # above the historical 20.)
            MAX_PER_WELL = 26
            hh = [(b["x"], b["y"]) for b in M.get("buildings", []) if b.get("kind") in (COMMON | {"servant"}) and inw(b["x"], b["y"])]
            served = [0] * len(wells)
            for hx, hy in hh:
                served[min(range(len(wells)), key=lambda i: math.hypot(hx - wells[i]["x"], hy - wells[i]["y"]))] += 1
            swamped = [(round(wells[i]["x"]), round(wells[i]["y"]), c) for i, c in enumerate(served) if c > MAX_PER_WELL]
            # WHY (~1 communal well per 10-20 households - the premodern courtyard-well norm): settlements.md "Historical grounding"
            check(
                "city_well_density_sufficient",
                not swamped,
                f"public well(s) each the nearest for more than {MAX_PER_WELL} commoner households - too few wells for "
                f"the neighborhood (~1 per 10-20 households is realistic); add wells where the warren is densest: {swamped}",
            )
            # wells sit in a block INTERIOR off the lanes (the idobata was a courtyard, not the avenue),
            # and a wellhead must not overlap a building or compound. Placement guarantees both (well_at /
            # place_wells use the same clearance test the houses do), so this is the backstop.
            wlanes = [st["pts"] for st in M.get("town_streets", [])] + ([M["road"]] if M.get("road") else []) + [a["pts"] for a in M.get("alleys", [])]
            lane_w = [st.get("w", 24) for st in M.get("town_streets", [])] + ([M.get("road_width", 26)] if M.get("road") else []) + [10 for _ in M.get("alleys", [])]
            _gov = M.get("governor_mansion")
            structs = M.get("buildings", []) + M.get("flophouses", []) + M.get("religious", []) + M.get("ministries", []) + M.get("merchant_estates", []) + ([_gov] if _gov else [])
            bad_well = []
            for w in wells:
                wx, wy, wr = w["x"], w["y"], w.get("r", 8)
                if any(seg_dist(wx, wy, ln[i], ln[i + 1]) < lw / 2 + wr for ln, lw in zip(wlanes, lane_w, strict=False) for i in range(len(ln) - 1)):
                    bad_well.append((round(wx), round(wy), "on a lane"))
                elif any("w" in st and abs(wx - st["x"]) < st["w"] / 2 + wr and abs(wy - st["y"]) < st["h"] / 2 + wr for st in structs):
                    bad_well.append((round(wx), round(wy), "on a building"))
            check("city_wells_in_block_interiors", not bad_well, f"well(s) not sitting clear in a block interior - a wellhead is on a lane or overlaps a structure: {bad_well[:4]}")
            # the SAMURAI/GOVERNMENT quarter has NO public wells - samurai drew from PRIVATE wells inside
            # their own walled compounds, and gathering at the communal idobata was a commoner-district
            # institution (beneath samurai status). So a public wellhead embedded AMONG the samurai
            # dwellings is wrong; their water is private and stays off-map, like their gardens. A well is
            # "in the samurai quarter" if the dwellings it actually sits among are mostly samurai - a
            # relative test, robust where a commoner well sits a block from the quarter across the ward fence.
            SAMK = {"samurai", "samurai_large"}
            HOUSEK = {"laborer", "laborer_large", "servant", "burakumin", "merchant", "merchant_house", "merchant_large"} | SAMK
            dwl = [(b["x"], b["y"], b.get("kind") in SAMK) for b in M.get("buildings", []) if b.get("kind") in HOUSEK]
            sam_wells = []
            for w in wells:
                near_dw = sorted(dwl, key=lambda d: math.hypot(d[0] - w["x"], d[1] - w["y"]))[:3]
                if near_dw and sum(1 for d in near_dw if d[2]) * 2 >= len(near_dw):  # most of its nearest neighbors are samurai
                    sam_wells.append((round(w["x"]), round(w["y"])))
            # WHY (samurai/official households drew from PRIVATE wells inside their walled compounds): settlements.md "Historical grounding"
            check(
                "city_samurai_quarter_has_no_public_wells",
                not sam_wells,
                f"public well(s) sitting among the samurai dwellings: {sam_wells} - the samurai/government quarter has no "
                f"communal wells (samurai draw from private wells inside their compounds; the public idobata is a commoner institution)",
            )

        # a city ON the Imperial road LINES that road with COMMERCE (shops + traveler inns): the
        # through-road is the city's prime frontage, where caravans and travelers pass, so it must not
        # run bare. This holds for ANY city with an Imperial road, WALLED OR NOT - a city WITHOUT a road
        # has no such ribbon (its commerce stays in the market district). The road's portion running
        # THROUGH the city is judged: bounded by the WALL if there is one, else by the URBAN FOOTPRINT
        # (the bbox of the city's buildings). Scaled to that length at ~1 commercial frontage per 130px,
        # a floor that catches a bare spine.
        road = M.get("road") or []
        road_through = bool(road) and any(p[1] < EY0 for p in road) and any(p[1] > EY1 for p in road)
        if road_through:
            wp = M.get("wall") or []
            if len(wp) >= 3:
                in_city: Any = lambda x, y: point_in_poly(x, y, wp)  # noqa: E731
            else:
                bx = [b["x"] for b in M.get("buildings", [])] or [EX0, EX1]
                by = [b["y"] for b in M.get("buildings", [])] or [EY0, EY1]
                x0, x1, y0, y1 = min(bx) - 40, max(bx) + 40, min(by) - 40, max(by) + 40
                in_city = lambda x, y: x0 <= x <= x1 and y0 <= y <= y1  # noqa: E731
            il = 0.0
            for i in range(len(road) - 1):
                a, b = road[i], road[i + 1]
                frac_inside = sum(1 for t in range(11) if in_city(a[0] + (b[0] - a[0]) * t / 10, a[1] + (b[1] - a[1]) * t / 10)) / 11
                il += math.hypot(b[0] - a[0], b[1] - a[1]) * frac_inside
            COMMERCE = {"shop", "merchant", "inn"}
            road_comm = sum(
                1
                for bg in M.get("buildings", [])
                if bg.get("kind") in COMMERCE and in_city(bg["x"], bg["y"]) and min(seg_dist(bg["x"], bg["y"], road[k], road[k + 1]) for k in range(len(road) - 1)) <= 95
            )
            need = round(il / 130)
            check(
                "city_imperial_road_has_commerce",
                road_comm >= need,
                f"only {road_comm} shops/inns front the {round(il)}px of Imperial road running through the city (want >= {need}) - a "
                f"city on a trade route lines its through-road with commerce to service travelers; don't leave the prime road frontage bare",
            )

        # two lanes (streets/alleys) heading STRAIGHT at each other and stopping just short, with nothing
        # between them, should simply CONNECT - a near-miss reads as a mistake, not a deliberate dead-end.
        # (Unlike city_streets_no_near_miss, which only compares street-vs-street segment proximity, this
        # catches ALLEYS too and the aligned end-to-end / T case, and ignores gaps a building/fence/wall
        # genuinely blocks.) Generic to any city with lanes, walled or not.
        misses = lane_near_misses(M)
        check(
            "city_lanes_meet_when_aligned",
            not misses,
            f"lane endpoint(s) stopping a short CLEAR distance from another lane they point straight at - "
            f"two lanes heading toward each other with nothing between should connect, not stop short: {misses}",
        )

        # a lane heading at a NEIGHBORHOOD wall (a ward fence) should reach it and end at a KIDO GATE - the
        # commoners' lanes pull in to the gates they pass through to work in the samurai quarter. Stopping a
        # sliver short, or meeting the fence with no gate, both read as a mistake. (Stopping short of the
        # MAIN city wall is fine - that is the city's own edge, not a neighborhood boundary.)
        shortfalls = lane_ward_shortfalls(M)
        check("city_lanes_reach_ward_gates", not shortfalls, f"lane(s) at a neighborhood (ward) wall that should extend to it and end at a gate: {shortfalls}")

        if meta.get("walled"):
            w = M.get("wall") or []
            gates = M.get("gates", [])

            def inwall(px: float, py: float) -> bool:
                return len(w) >= 3 and point_in_poly(px, py, w)

            check("walled_city_has_wall_and_gates", len(w) >= 3 and len(gates) >= 2, f"a walled city needs a closed wall and >= 2 gates (wall={len(w)} pts, {len(gates)} gates)")
            ins = M.get("inspection_stations", [])
            no_station = [g for g in gates if not any(math.hypot(s["x"] - g[0], s["y"] - g[1]) <= 160 for s in ins)]
            check("city_inspection_station_at_each_gate", len(gates) >= 2 and not no_station, f"every city gate needs an inspection station within ~160px ({len(no_station)} gate(s) without one)")
            gstructs = M.get("gate_structs", [])
            no_guard = [g for g in gates if sum(1 for s in gstructs if math.hypot(s["x"] - g[0], s["y"] - g[1]) <= 180) < 2]
            check(
                "city_gate_has_guardhouse", len(gates) >= 2 and not no_guard, f"every city gate needs a guard house + guard tower (>= 2 gate structures within ~180px): {len(no_guard)} gate(s) short"
            )
            # a fortified city is TOWERED for enfilading fire along the wall face: guard towers spaced
            # at regular intervals around the whole rampart (a bowshot apart), not only at the gates -
            # so no long bare arc of wall sits uncovered. Spacing is judged by the widest angular gap
            # between consecutive towers around the wall centroid.
            towers = M.get("wall_towers", [])
            wcx, wcy = sum(p[0] for p in w) / len(w), sum(p[1] for p in w) / len(w)
            angs = sorted(math.atan2(t["y"] - wcy, t["x"] - wcx) for t in towers)
            maxgap = max([angs[i + 1] - angs[i] for i in range(len(angs) - 1)] + [angs[0] + 2 * math.pi - angs[-1]]) if angs else 2 * math.pi
            check(
                "city_wall_towers_spaced",
                len(towers) >= 6 and maxgap < math.radians(75),
                f"a fortified city needs guard towers spaced around the wall, not just at the gates ({len(towers)} towers, widest bare arc {round(math.degrees(maxgap))} deg, want < 75) - place towers at regular intervals (s.city_wall does this automatically)",
            )
            # guard towers sit SQUARE to the wall (rotated to its tangent) rather than all axis-aligned -
            # a tower on a slanted stretch slants with it. Each tower's recorded rotation must match the
            # angle of the nearest wall edge (mod 90, since a square reads the same every 90 degrees).
            ring2: Any = list(w) + [w[0]]
            misaligned = []
            for t in towers:
                ek = min(range(len(ring2) - 1), key=lambda k: seg_dist(t["x"], t["y"], ring2[k], ring2[k + 1]))
                edge_ang = math.degrees(math.atan2(ring2[ek + 1][1] - ring2[ek][1], ring2[ek + 1][0] - ring2[ek][0]))
                d = (t.get("rot", 0) - edge_ang) % 90
                if min(d, 90 - d) > 15:
                    misaligned.append((round(t["x"]), round(t["y"])))
            check("city_wall_towers_aligned", not misaligned, f"guard tower(s) not square to the wall - a tower should rotate to the wall's tangent there, not stay axis-aligned: {misaligned}")
            # the GATE FURNITURE - the guard house + inspection station that sit along the ring road just
            # inside each gate - is likewise SQUARE TO THE WALL: rotated to the wall's LOCAL tangent at its
            # own position (NOT the gate vertex's - the wall has already curved away by then), so the ring
            # road runs lengthwise through it. Each is a rectangle (its long axis runs ALONG the wall), so
            # its rotation must match the nearest wall edge angle mod 180 (a 180 deg flip is the same, a 90
            # deg turn would stand it the wrong way across the road). Tolerance is TIGHTER than the towers'
            # (6 vs 15 deg): the furniture rotation is set from the exact local edge angle, not the towers'
            # chord-through-neighbors approximation, so a correctly-placed piece matches near-exactly - and
            # the gates sit on shallow wall stretches (~8 deg), which a 15 deg window would wave through.
            furn = [g for g in M.get("gate_structs", []) if g.get("kind") in ("guardhouse", "inspection")]
            fmis = []
            for gstruct in furn:
                ek = min(range(len(ring2) - 1), key=lambda k: seg_dist(gstruct["x"], gstruct["y"], ring2[k], ring2[k + 1]))
                edge_ang = math.degrees(math.atan2(ring2[ek + 1][1] - ring2[ek][1], ring2[ek + 1][0] - ring2[ek][0]))
                d = (gstruct.get("rot", 0) - edge_ang) % 180
                if min(d, 180 - d) > 6:
                    fmis.append((round(gstruct["x"]), round(gstruct["y"])))
            check(
                "city_gate_furniture_aligned",
                not fmis,
                f"gate guard house / inspection station(s) not square to the wall - they should rotate to the wall's LOCAL tangent where they sit (so the ring road runs through them lengthwise), not stay flat: {fmis}",
            )
            # ... and the guard house + inspection station are SEPARATE buildings: walked along a
            # tightly-curving wall the two arcs can converge, and an inspection annex drawn through
            # its guard house reads as a collision (GM, 2026-07)
            gpairs = []
            ghs = [g for g in M.get("gate_structs", []) if g.get("kind") == "guardhouse"]
            for ins in M.get("inspection_stations", []):
                for gh in ghs:
                    if math.hypot(ins["x"] - gh["x"], ins["y"] - gh["y"]) < 160 and sat_overlap(
                        rect_corners({"x": ins["x"], "y": ins["y"], "w": ins["w"], "h": ins["h"], "rot": ins.get("rot", 0)}),
                        rect_corners({"x": gh["x"], "y": gh["y"], "w": gh["w"], "h": gh["h"], "rot": gh.get("rot", 0)}),
                    ):
                        gpairs.append((round(ins["x"]), round(ins["y"])))
            check(
                "city_gate_guard_inspection_separate",
                not gpairs,
                f"gate inspection station(s) overlapping their guard house: {gpairs} - the two are separate buildings on the ring road; space them along the wall until they clear",
            )
            # WALL FURNITURE STAYS OUT OF THE MOAT: a guard tower straddles the wall and may PROJECT a
            # stride past its outer face (the horse-face bastion), but its footing must stand on the
            # BERM, never in the water - a tight moat gap leaves a narrow berm, so a tower centered on
            # the wall line pokes its outer face into the bed. Same for the gate towers and the guard
            # house / inspection station. (Bridges are exempt - they span the moat by design.)
            mo_f = M.get("moat")
            if mo_f:
                mhw_f = M.get("moat_width", 22) / 2
                furn_wet: list[tuple[int, int]] = []
                for it in M.get("wall_towers", []) + M.get("gate_structs", []) + M.get("inspection_stations", []):
                    fc = rect_corners({"x": it["x"], "y": it["y"], "w": it.get("w", 26), "h": it.get("h", 26), "rot": it.get("rot", 0)})
                    if footprint_on_line(fc, mo_f, mhw_f + 1):
                        furn_wet.append((round(it["x"]), round(it["y"])))
                check(
                    "city_wall_furniture_clear_of_moat",
                    not furn_wet,
                    f"guard tower(s) / gate furniture standing IN the moat: {sorted(set(furn_wet))[:6]} - wall furniture "
                    f"footings stay on the berm; nudge them inward so only a small outer projection passes the wall face",
                )
            # THE WARD GATES STAND CLEAR OF THE WALL TOWERS: a kido hangs on the ward fence where a
            # lane or the ring road crosses it, and the fence ends abut the rampart - so the LAST
            # kido can land against a mural tower's footprint (its guard box read as "a small square
            # building" inside the tower - GM, 2026-07). Both are overlap-EXEMPT classes (each sits
            # on its own wall), so no generic pass catches the pair. The kido cannot move (it gates
            # a fixed crossing), so the TOWER yields - city_wall(tower_skip=[...]) relocates it to
            # the neighboring wall vertex.
            k_hit = []
            for kd in M.get("kido", []):
                bb = kd.get("bbox")
                if not bb:
                    continue
                kc = [(bb[0], bb[1]), (bb[2], bb[1]), (bb[2], bb[3]), (bb[0], bb[3])]
                for t in M.get("wall_towers", []) + [g_ for g_ in M.get("gate_structs", []) if g_.get("kind") == "tower"]:
                    if sat_overlap(kc, rect_corners({"x": t["x"], "y": t["y"], "w": t.get("w", 38), "h": t.get("h", 38), "rot": t.get("rot", 0)})):
                        k_hit.append((round(kd["x"]), round(kd["y"])))
                        break
            check(
                "kido_clear_of_wall_towers",
                not k_hit,
                f"ward gate(s) overlapping a guard tower: {sorted(set(k_hit))[:4]} - where the ward fence meets the "
                f"rampart the kido keeps its ground (it gates a fixed crossing); slide the tower along the wall "
                f"(city_wall tower_skip)",
            )
            # a GATE TOWER (a gate's guard tower, or a mural tower) must not OVERLAP the gate's
            # INSPECTION STATION or GUARD HOUSE (GM, 2026-07). The gate complex packs tight (guardhouse
            # + inspection + tower + gateposts at each gate) and inspection stations are overlap-EXEMPT
            # against the gate furniture, which had let a tower footprint STACK on the inspection post -
            # each is a distinct building and they must sit CLEAR of one another, abutting not stacked.
            _gtowers = [g for g in (M.get("wall_towers", []) + [x for x in M.get("gate_structs", []) if x.get("kind") == "tower"]) if "w" in g]
            _gfurn = [g for g in ([x for x in M.get("gate_structs", []) if x.get("kind") in ("inspection", "guardhouse")] + M.get("inspection_stations", [])) if "w" in g]
            gf_hit = []
            for t in _gtowers:
                tc = rect_corners({"x": t["x"], "y": t["y"], "w": t["w"], "h": t.get("h", t["w"]), "rot": t.get("rot", 0)})
                for o in _gfurn:
                    if sat_overlap(tc, rect_corners({"x": o["x"], "y": o["y"], "w": o["w"], "h": o.get("h", o["w"]), "rot": o.get("rot", 0)})):
                        gf_hit.append((round(t["x"]), round(t["y"])))
                        break
            check(
                "city_gate_towers_clear_of_gate_furniture",
                not gf_hit,
                f"guard tower(s) overlapping an inspection station or gate house: {sorted(set(gf_hit))[:4]} - the gate "
                f"complex packs tight but each footprint sits CLEAR; move the tower (or the furniture) so they abut, not stack",
            )
            # ... and clear of the HOUSING: the kido + its guard box occupy a fixed crossing that the
            # packs cannot see (s.ward draws long after the quarters are built), so the gen must
            # RESERVE each gate's ground (block_polys) before any pack runs - else a row house lands
            # under the guard box (GM, 2026-07: caught twice, on both fence-end gates)
            kb_hit = []
            for kd in M.get("kido", []):
                bb = kd.get("bbox")
                if not bb:
                    continue
                kc = [(bb[0], bb[1]), (bb[2], bb[1]), (bb[2], bb[3]), (bb[0], bb[3])]
                for key_ in ("buildings", "houses", "flophouses", "storehouses"):
                    if any(sat_overlap(kc, rect_corners({"x": it["x"], "y": it["y"], "w": it.get("w", 20), "h": it.get("h", 14), "rot": it.get("rot", 0)})) for it in M.get(key_, []) or []):
                        kb_hit.append((round(kd["x"]), round(kd["y"])))
                        break
            check(
                "kido_clear_of_buildings",
                not kb_hit,
                f"ward gate(s) overlapping a building: {sorted(set(kb_hit))[:4]} - the kido and its guard box hold "
                f"their crossing; reserve the gate's ground before the packs run (block_polys around each kido spot)",
            )
            # a walled city has a RING ROAD (順城街) just inside the rampart - the wall-clear patrol zone a
            # fortified city keeps for moving troops along the wall; the quarters pack INSIDE it (s.ring_road
            # returns the loop to use as s.bound).
            ring_rd: Any = M.get("ring_road")
            check(
                "city_has_ring_road",
                bool(ring_rd) and len(ring_rd) >= 4,
                "a walled city needs a ring road just inside the wall (the wall-clear patrol zone) - s.ring_road(WALL); set s.bound to the loop it returns",
            )
            # a street running toward a THROUGH-LANE (the Imperial road or the ring road) must MEET it
            # cleanly at a T-junction: its bed reaches the lane's bed and ENDS there - neither a sliver
            # SHORT of it (an undershoot, the street appears to dead-end in open ground) nor a sliver
            # PAST it (an overshoot, the street pokes through to the far side instead of stopping at the
            # junction). A genuine crossroads, where the street truly continues well past the lane, is
            # fine - only a short stub poking through is wrong. (The ring road is gated where it crosses
            # the ward fence, so even the government quarter's lanes may give onto it without un-sealing.)
            through = []
            if M.get("road"):
                through.append((M["road"], (M.get("road_width", 26) - 8) / 2))
            if ring_rd:
                through.append((ring_rd, (M.get("ring_road_width", 15) - 6) / 2))
            bad_meet = []
            # streets AND alleys: a gravel alley that runs straight at a through-lane and stops a sliver
            # short of it (the laborer warren's east lane stopping just shy of the east ring road) should
            # reach it too, just like a paved street
            meeting_lanes = [(st["pts"], st.get("w", 18) / 2) for st in M.get("town_streets", [])] + [(a["pts"], 5.0) for a in M.get("alleys", [])]
            for pts, sh in meeting_lanes:
                for E, nb in ((pts[0], pts[1]), (pts[-1], pts[-2])):
                    for L, bedhalf in through:
                        cp = min((seg_closest(E[0], E[1], L[i], L[i + 1]) for i in range(len(L) - 1)), key=lambda c: math.hypot(E[0] - c[0], E[1] - c[1]))
                        gap = math.hypot(E[0] - cp[0], E[1] - cp[1])
                        if gap > 46:
                            continue
                        ip = next((seg_intersect(nb, E, L[i], L[i + 1]) for i in range(len(L) - 1) if segments_cross(nb, E, L[i], L[i + 1])), None)
                        if ip is not None:  # crosses the lane: must END at the junction, not poke a stub past it
                            if 3 < math.hypot(E[0] - ip[0], E[1] - ip[1]) < 50:
                                bad_meet.append((round(E[0]), round(E[1])))
                        else:  # short of the lane: its bed must reach the lane's bed
                            dl = math.hypot(E[0] - nb[0], E[1] - nb[1]) or 1.0
                            align = ((E[0] - nb[0]) / dl) * ((cp[0] - E[0]) / max(gap, 1e-6)) + ((E[1] - nb[1]) / dl) * ((cp[1] - E[1]) / max(gap, 1e-6))
                            if align > 0.6 and gap >= sh + bedhalf:
                                bad_meet.append((round(E[0]), round(E[1])))
            check(
                "city_streets_meet_through_lanes",
                not bad_meet,
                f"street/alley(s) not meeting the Imperial road / ring road cleanly at a junction - stopping a sliver short of it or poking a sliver past it: {sorted(set(bad_meet))}",
            )
            # the RING ROAD is a CLEAR patrol road: it must run clear of buildings, civic compounds
            # (ministries, the governor's yamen, temples) and fields. The gate guard houses / inspection
            # stations / towers DO sit along it (wall furniture, not in these lists, so exempt), and a
            # ward fence may cross it - but only at a gated kido (enforced by city_samurai_ward_sealed,
            # which has the ring road in its netlines). Overlap = the ring's BED passes through a footprint.
            if ring_rd:
                rbed = (M.get("ring_road_width", 15) - 6) / 2
                rgov = M.get("governor_mansion")

                def _foot(it: dict[str, Any]) -> list[tuple[float, float]]:
                    return rect_corners(it) if "rot" in it else rect_corners_xywh(it, 0)

                on_ring = [
                    it.get("name") or it.get("label") or it.get("kind") or "compound"
                    for it in (
                        M.get("buildings", [])
                        + M.get("ministries", [])
                        + M.get("religious", [])
                        + ([rgov] if rgov else [])
                        + M.get("cemeteries", [])
                        + M.get("mausoleums", [])
                        + M.get("cremation_grounds", [])
                        + M.get("ossuaries", [])
                    )
                    if footprint_on_line(_foot(it), ring_rd, rbed)
                ]
                on_ring += ["field:" + f["name"] for f in fields if footprint_on_line(f["outline"], ring_rd, rbed)]
                check(
                    "ring_road_kept_clear",
                    not on_ring,
                    f"the ring road must run CLEAR of buildings/civic compounds/fields (only the gate guard houses, inspection stations, towers and gated ward fences may sit on it): {sorted(set(on_ring))}",
                )
            buraku_in = [b for b in M.get("buildings", []) if b.get("kind") == "burakumin" and inwall(b["x"], b["y"])]
            # WHY (a walled city cannot do without burakumin labor during a siege, so some live inside): settlements.md "Historical grounding"
            check(
                "walled_city_has_burakumin_inside",
                len(buraku_in) >= 3,
                f"{len(buraku_in)} burakumin inside the walls - a walled provincial city must keep >= 1 burakumin neighborhood within (they cannot be without burakumin during a siege)",
            )
            est_out = [mn for mn in M.get("manors", []) if len(w) >= 3 and not point_in_poly(mn["x"], mn["y"], w)]
            check(
                "city_samurai_estates_outside",
                5 <= len(est_out) <= 15,
                f"{len(est_out)} walled samurai estates outside the walls, expected 5-15 - a walled city's cramped interior pushes wealthy samurai to extramural estates they commute in from",
            )
            areas = sorted((mn["w"] * mn["h"]) for mn in est_out)
            check(
                "city_samurai_estates_vary_in_size",
                len(areas) < 2 or areas[-1] >= 1.5 * areas[0],
                "the samurai estates should vary in size (some larger than others) - largest area >= 1.5x the smallest",
            )
            # scattered country estates each front their OWN approach lane (not drawn at this scale), so
            # their depicted (formal) gates do NOT all open the same way - a uniform direction is the
            # unconsidered default. The formal gate favours the auspicious south; others face the cityward
            # approach (the cityward service gate, like the governor's, is omitted at this scale).
            egd = [mn.get("gate_dir") for mn in est_out]
            check(
                "city_estate_gates_vary",
                len(egd) < 3 or len(set(egd)) >= 2,
                f"all {len(egd)} country estate gates open the same way ({egd[0] if egd else None}) - scattered "
                f"estates each front their own approach, so vary the gate_dir (some south, some cityward)",
            )
            moat: Any = M.get("moat")
            # all city temples INSIDE the walls, and clear of the wall stroke and the moat
            rel = M.get("religious", [])
            out_rel = [r.get("label") for r in rel if not inwall(r["x"], r["y"])]
            check("city_temples_inside_walls", not out_rel, f"temple(s) outside the city walls (all of a city's temples belong inside): {out_rel}")
            rel_bad = [r.get("label") for r in rel if footprint_on_line(rect_corners_xywh(r, 0), w, 9) or (moat and footprint_on_line(rect_corners_xywh(r, 0), moat, 13))]
            check("city_temples_clear_of_wall_moat", not rel_bad, f"temple(s) overlapping the wall or moat: {rel_bad}")
            # THE LABELED (major) CITY TEMPLES ARE DEDICATED TO THE CLAN'S TWO PATRON FORTUNES. Hantei
            # X codified that every city holds a temple to each of its clan's patron fortunes (l7r.md);
            # the two GREAT temples honor those, and a smattering of small wayside shrines fills the
            # rest. Declare meta(clan=...); the labeled temples (kind="temple", not "small_shrine")
            # must be exactly the clan's two fortunes. Override with meta(temple_fortunes=[...]) for a
            # city that changed hands. GM, 2026-07: Nagahara (Crab) had a large Temple of Suitengu -
            # a thematic pick, not a Crab patron (Crab = Bishamon + Ebisu). Named after "Temple of X".
            declared_t = meta.get("temple_fortunes")
            clan_t = meta.get("clan")
            if declared_t is None and clan_t:
                cf = CLAN_FORTUNES.get(clan_t.lower())
                check("city_clan_known", cf is not None, f"unknown clan {clan_t!r} - no patron fortunes")
                declared_t = sorted(cf) if cf else None
            if declared_t is not None:

                def _tfortune(r: dict[str, Any]) -> str:
                    lab = (r.get("label") or "").strip()
                    return lab.rsplit(" of ", 1)[-1].strip() if " of " in lab else lab

                major = [_tfortune(r) for r in rel if r.get("kind") == "temple"]
                # every major temple honors a PATRON fortune (or Bishamon, the warrior fortune of
                # any clan's samurai quarter - for Crab it IS a patron; for Crane/Tango it stands
                # beside the two patron temples), and BOTH patrons must be present. A great temple to
                # a non-patron (Nagahara's Suitengu) fails; small wayside shrines carry the rest.
                allowed = set(declared_t) | {"Bishamon"}
                stray_t = sorted(set(f for f in major if f not in allowed))
                missing = sorted(f for f in declared_t if f not in major)
                check(
                    "city_temples_dedicated",
                    not stray_t and not missing,
                    f"major city temples {sorted(set(major))}: stray non-patron {stray_t}, missing patron {missing} "
                    f"(clan {clan_t!r} patrons {sorted(declared_t)}); a city has a great temple to each of its two "
                    f"patron fortunes (+ optionally Bishamon in the samurai quarter), the rest small shrines",
                )
            # a TEMPLE NEIGHBORHOOD (>= 2 temples clustered together) should be dotted with a smattering of
            # small wayside SHRINES (s.small_shrine - non-residential, kind 'small_shrine'). A lone temple
            # among houses (e.g. the warrior-fortune temple in the samurai quarter) is not a neighborhood.
            temples = [r for r in rel if r.get("kind") == "temple"]
            shrines = [r for r in rel if r.get("kind") == "small_shrine"]
            clustered = [t for t in temples if any(u is not t and math.hypot(t["x"] - u["x"], t["y"] - u["y"]) < 400 for u in temples)]
            if len(clustered) >= 2:
                near_sh = sum(1 for sh in shrines if any(math.hypot(sh["x"] - t["x"], sh["y"] - t["y"]) < 350 for t in clustered))
                check(
                    "city_temple_neighborhood_has_shrines",
                    near_sh >= 3,
                    f"the temple neighborhood ({len(clustered)} clustered temples) has only {near_sh} small wayside shrine(s) - dot it with a few more (s.small_shrine)",
                )
            # the outside samurai estates: no overlapping each other, none over the wall or moat
            est_corners = [rect_corners_xywh(mn, 0) for mn in est_out]
            est_overlap = [1 for i in range(len(est_out)) for j in range(i + 1, len(est_out)) if sat_overlap(est_corners[i], est_corners[j])]
            check("city_estates_no_overlap", not est_overlap, f"{len(est_overlap)} overlapping estate pair(s)")
            est_bad = [1 for i in range(len(est_out)) if footprint_on_line(est_corners[i], w, 9) or (moat and footprint_on_line(est_corners[i], moat, 13))]
            check("city_estates_clear_of_wall_moat", not est_bad, f"{len(est_bad)} estate(s) overlapping the wall or moat")
            # the WALLED MERCHANT ESTATES (their court, not just the house inside) must likewise sit clear
            # of the rampart, the moat, and any other building. (The estate's OWN inner house, centered in
            # the court, is fine; everything else - temples, compounds, other homes, other estates - is not.)
            mest = M.get("merchant_estates", [])
            mest_corners = [rect_corners_xywh(e, 0) for e in mest]
            mest_wm = [(round(mest[i]["x"]), round(mest[i]["y"])) for i in range(len(mest)) if footprint_on_line(mest_corners[i], w, 9) or (moat and footprint_on_line(mest_corners[i], moat, 13))]
            check("city_merchant_estates_clear_of_wall_moat", not mest_wm, f"walled merchant estate(s) overlapping the city wall or moat (keep them well inside the rampart): {mest_wm}")
            civics = M.get("religious", []) + M.get("ministries", []) + ([M["governor_mansion"]] if M.get("governor_mansion") else [])
            other_struct = [rect_corners_xywh(o, 0) for o in civics] + [rect_corners(b) for b in M.get("buildings", [])]
            other_xy = [(o["x"], o["y"]) for o in civics] + [(b["x"], b["y"]) for b in M.get("buildings", [])]
            mest_bld = []
            for i in range(len(mest)):
                e = mest[i]
                for oc, (ox, oy) in zip(other_struct, other_xy, strict=False):
                    if abs(ox - e["x"]) <= e["w"] / 2 and abs(oy - e["y"]) <= e["h"] / 2:
                        continue  # a structure centered INSIDE the court = the estate's own house
                    if sat_overlap(mest_corners[i], oc):
                        mest_bld.append((round(e["x"]), round(e["y"])))
                        break
                else:
                    for j in range(len(mest)):
                        if j != i and sat_overlap(mest_corners[i], mest_corners[j]):
                            mest_bld.append((round(e["x"]), round(e["y"])))
                            break
            check("city_merchant_estates_clear_of_buildings", not mest_bld, f"walled merchant estate(s) overlapping a building (temple, compound, house, or another estate): {sorted(set(mest_bld))}")
            # a walled estate's GATE may not open INTO a building. The walls may ABUT a neighbor (very
            # common historically), but the threshold just outside the gate must front OPEN ground, not
            # a COMPOUND (temple, ministry, the yamen, or another estate court) - point the gate elsewhere.
            GDIR = {"south": (0, 1), "north": (0, -1), "east": (1, 0), "west": (-1, 0)}
            compounds = [rect_corners_xywh(o, 0) for o in civics] + list(mest_corners)
            gate_bad = []
            for i in range(len(mest)):
                g = mest[i].get("gate")
                if not g:
                    continue
                ox, oy = GDIR.get(mest[i].get("gate_dir", "south"), (0, 1))
                tcx, tcy = g[0] + ox * 11, g[1] + oy * 11  # a threshold box just OUTSIDE the gate
                tw, th = (24, 22) if ox == 0 else (22, 24)
                thr = [(tcx - tw / 2, tcy - th / 2), (tcx + tw / 2, tcy - th / 2), (tcx + tw / 2, tcy + th / 2), (tcx - tw / 2, tcy + th / 2)]
                for j, cc in enumerate(compounds):
                    if j == len(civics) + i:  # skip the estate's OWN court
                        continue
                    if sat_overlap(thr, cc):
                        gate_bad.append((round(mest[i]["x"]), round(mest[i]["y"])))
                        break
            check(
                "city_merchant_estate_gate_clear",
                not gate_bad,
                f"walled merchant estate gate(s) opening INTO a building (a temple/compound/another estate) - point the gate at open ground: {gate_bad}",
            )
            # the government compounds (governor's mansion + ministry offices) sit inside, clear of the
            # barriers. (The governor's YAMEN is legitimately a large walled compound - a whole city block,
            # dozens of buildings inside, drawn here as walls-only - so its size is fine; it must just not
            # cross the rampart.)
            gov = M.get("governor_mansion")
            gov_items = ([gov] if gov else []) + M.get("ministries", [])
            gov_bad = [
                g.get("name") or g.get("label") or "governor's mansion"
                for g in gov_items
                if footprint_on_line(rect_corners_xywh(g, 0), w, 9) or (moat and footprint_on_line(rect_corners_xywh(g, 0), moat, 13))
            ]
            check("city_government_clear_of_wall_moat", not gov_bad, f"government compound(s) overlapping the wall or moat: {gov_bad}")
            # the governor's mansion is the GRANDEST compound - a city-block yamen, at least as large
            # as any samurai estate and several times any single ministry office
            if gov:
                ga = gov["w"] * gov["h"]
                # the absolute floor is REAL area (~1.4 ha): 24000px2 was tuned at the pre-ladder
                # ~2.55 ft/px grain and would demand a 2 ha yamen at 3 ft/px
                _floor = round(24000 * (2.55 / meta.get("ftpx", 2.55)) ** 2)
                big_other = max([mn["w"] * mn["h"] for mn in est_out] + [3 * m["w"] * m["h"] for m in M.get("ministries", [])] + [_floor])
                check(
                    "city_governor_mansion_large",
                    ga >= big_other,
                    f"the governor's mansion ({ga:.0f}px2) must be the grandest compound - a city-block yamen at least as large as any estate and >= 3x any ministry (need >= {big_other:.0f})",
                )
                # the ministries cluster around the yamen (the government district), threading into the
                # samurai quarter; only the Ministry of Rites sits apart, with the temples it oversees
                far_min = [m.get("name") for m in M.get("ministries", []) if "rites" not in (m.get("name") or "").lower() and math.hypot(m["x"] - gov["x"], m["y"] - gov["y"]) > 480]
                check(
                    "city_ministries_cluster_at_government",
                    not far_min,
                    f"ministry office(s) far from the governor's mansion - the ministries belong around the yamen / in the samurai quarter (only Rites sits with the temples): {far_min}",
                )
            # a planned city's government offices FRONT its streets - the yamen sits where the main
            # streets cross and the bureaus line the avenues around it (Chinese official street /
            # jokamachi grid), so every ministry must sit on a street, not float mid-block
            st_pts = [st["pts"] for st in M.get("town_streets", [])]
            no_front = [m.get("name") for m in M.get("ministries", []) if not any(seg_dist(m["x"], m["y"], sp[i], sp[i + 1]) < 85 for sp in st_pts for i in range(len(sp) - 1))]
            check(
                "city_ministries_front_a_street",
                not no_front,
                f"ministry office(s) not fronting any city street - government offices line the avenues around the yamen, they do not float mid-block: {no_front}",
            )
            # a walled city SEALS its samurai/government quarter off the commoner streets with kido
            # (wooden ward gates), not internal ramparts: full walled wards are a great-capital / Tang
            # feature, over-scaled here, so a provincial city gates the quarter's street entries instead
            on_st_kido = [
                k
                for k in M.get("kido", [])
                if any(seg_dist(k["x"], k["y"], st["pts"][i], st["pts"][i + 1]) < st.get("w", 18) / 2 + 8 for st in M.get("town_streets", []) for i in range(len(st["pts"]) - 1))
            ]
            gated = [k for k in on_st_kido if gov and math.hypot(k["x"] - gov["x"], k["y"] - gov["y"]) < 480]
            check(
                "city_samurai_quarter_gated",
                len(gated) >= 2,
                f"a walled city seals its samurai/government quarter with kido ward gates across the streets entering it (s.kido), not walls - {len(gated)} gate(s) bar the quarter's street entries near the yamen, need >= 2",
            )
            # ...and that ward must be SEALED: a continuous fence whose ends abut the city wall, that
            # a street pierces ONLY at a kido gate. Otherwise the gates can just be walked around, and
            # the road network connects samurai to commoner with no gate between them.
            wards = M.get("wards", [])
            kido = M.get("kido", [])
            netlines = (
                [st["pts"] for st in M.get("town_streets", [])] + ([M["road"]] if M.get("road") else []) + [a["pts"] for a in M.get("alleys", [])] + ([M["ring_road"]] if M.get("ring_road") else [])
            )
            bad_cross, open_end = [], []
            for wd in wards:
                bnd = wd["boundary"]
                for sp in netlines:
                    for i in range(len(sp) - 1):
                        for ki in range(len(bnd) - 1):
                            if segments_cross(sp[i], sp[i + 1], bnd[ki], bnd[ki + 1]):
                                ip = seg_intersect(sp[i], sp[i + 1], bnd[ki], bnd[ki + 1])
                                if ip and not any(math.hypot(g["x"] - ip[0], g["y"] - ip[1]) < 32 for g in kido):
                                    bad_cross.append((round(ip[0]), round(ip[1])))
                for e in (bnd[0], bnd[-1]):
                    if len(w) >= 3 and edge_dist(e[0], e[1], w) > 45:
                        open_end.append((round(e[0]), round(e[1])))
            check(
                "city_samurai_ward_sealed",
                bool(wards) and not bad_cross and not open_end,
                f"the samurai/government ward is not SEALED (s.ward): wards={len(wards)}, ungated street crossings={bad_cross}, fence ends not meeting the wall={open_end} - a kido gate can be walked around unless the fence is continuous, ends at the wall, and a street pierces it only at a gate",
            )
            # ...and the fence ends must actually TOUCH the wall - a gap (even a small one, which the
            # coarse 45px seal tolerance lets slide) means commoners can simply walk AROUND the end of
            # the fence. The end must abut the rampart within ~10px (about the wall's own half-width).
            fence_gap = []
            for wd in wards:
                bnd = wd["boundary"]
                for e in (bnd[0], bnd[-1]):
                    if len(w) >= 3 and edge_dist(e[0], e[1], w) > 10:
                        fence_gap.append((round(e[0]), round(e[1]), "gap to the wall"))
                    elif any(math.hypot(e[0] - g[0], e[1] - g[1]) < 45 for g in gates):
                        fence_gap.append((round(e[0]), round(e[1]), "lands in a gate OPENING (the wall is cut there, so the fence meets nothing)"))
            check(
                "city_ward_fence_meets_wall",
                not fence_gap,
                f"ward-fence end(s) not abutting SOLID city wall (commoners could walk around the fence end): {fence_gap} - extend the fence to solid rampart, clear of any gate opening",
            )
            # the ward FENCE runs in OPEN ground - it must not pass THROUGH a building, a mausoleum, or
            # another ward's fence (GM, 2026-07). The packs keep off the fence via s.ward's corridor, but
            # a hand-placed compound (the mausoleum) or a diagonal fence segment can still cut through one.
            fence_hit = []
            _ftargets = [b for b in (M.get("buildings", []) + M.get("houses", []) + M.get("mausoleums", [])) if "w" in b]
            for wd in wards:
                bnd = wd["boundary"]
                for b in _ftargets:
                    bc = rect_corners({"x": b["x"], "y": b["y"], "w": b["w"], "h": b.get("h", b["w"]), "rot": b.get("rot", 0)})
                    if footprint_on_line(bc, bnd, 4):
                        fence_hit.append((round(b["x"]), round(b["y"])))
                for wd2 in wards:
                    if wd2 is wd:
                        continue
                    b2 = wd2["boundary"]
                    if any(segments_cross(bnd[i], bnd[i + 1], b2[j], b2[j + 1]) for i in range(len(bnd) - 1) for j in range(len(b2) - 1)):
                        fence_hit.append(("ward-x-ward", round(bnd[0][0])))
            check(
                "city_ward_fence_clear_of_structures",
                not fence_hit,
                f"ward fence passing THROUGH a structure (building / mausoleum / another fence): {sorted(set(fence_hit))[:4]} - "
                f"the fence runs in open ground; move the structure clear of the fence line or reroute the fence",
            )
            # a KIDO is a gate THROUGH the fence, so it must sit ON the fence (overlap it), not beside it
            # (GM, 2026-07: a gate next to rather than part of the wall does not work). Its crossing point
            # must lie within ~8px of a fence segment so the gate visibly straddles the fence.
            off_fence = []
            for kd in kido:
                if wards and min((seg_dist(kd["x"], kd["y"], wd["boundary"][i], wd["boundary"][i + 1]) for wd in wards for i in range(len(wd["boundary"]) - 1)), default=999) > 8:
                    off_fence.append((round(kd["x"]), round(kd["y"])))
            check(
                "city_kido_on_ward_fence",
                not off_fence,
                f"ward gate(s) sitting BESIDE the fence, not on it: {off_fence[:4]} - a kido gates a crossing THROUGH the "
                f"fence, so its point must lie ON the fence line (overlap it), not offset into the ward",
            )
            # ...and where the fence meets the wall, the city WALL must render ON TOP (the fence runs
            # UNDER the rampart). The fence is drawn late (high z), so without a wall cap on top of the
            # junction it paints over the wall stroke. s.ward records the fence z and the wall cap it
            # lays over each end; the cap's z must be above the fence's.
            not_under = []
            for wd in wards:
                fz = wd.get("z")
                caps = wd.get("wall_caps", [])
                if fz is None:
                    continue
                for e in (wd["boundary"][0], wd["boundary"][-1]):
                    if len(w) >= 3 and edge_dist(e[0], e[1], w) <= 15 and not any(c.get("z", -1) > fz and math.hypot(c["x"] - e[0], c["y"] - e[1]) < 30 for c in caps):
                        not_under.append((round(e[0]), round(e[1])))
            check(
                "city_ward_fence_under_wall",
                not not_under,
                f"ward-fence end(s) NOT rendered under the city wall - no wall cap on top of the junction, so the fence paints over the rampart: {not_under}",
            )
            # the extramural samurai estates all lie TOWARD OTOSAN UCHI (the Imperial capital) - a
            # samurai builds his country seat on the capital-facing side, so the direction is
            # per-city: meta(capital_dir=<cardinal>) (Tango SE, Nagahara NE). Each estate must sit in
            # the correct half-plane(s) for that direction (a diagonal requires BOTH axes).
            cx, cy = sum(p[0] for p in w) / len(w), sum(p[1] for p in w) / len(w)
            cap = meta.get("capital_dir", "southeast")
            cd = unit_dir(cap)
            check("city_capital_dir_valid", cd is not None, f"meta(capital_dir={cap!r}) is not a cardinal direction")
            if cd:

                def toward(mn: dict[str, Any]) -> bool:
                    okx = (mn["x"] > cx) if cd[0] > 0.3 else (mn["x"] < cx) if cd[0] < -0.3 else True
                    oky = (mn["y"] > cy) if cd[1] > 0.3 else (mn["y"] < cy) if cd[1] < -0.3 else True
                    return okx and oky

                not_cap = [(round(mn["x"]), round(mn["y"])) for mn in est_out if not toward(mn)]
                check(
                    "city_estates_toward_capital",
                    not not_cap,
                    f"{len(not_cap)} samurai estate(s) not toward the capital ({cap}): {not_cap[:3]} - a city's extramural estates cluster on the Otosan-Uchi-facing side (meta(capital_dir=...))",
                )
            # ... and clear of the ROADS leaving the city (an estate straddling the highway blocks it -
            # GM, 2026-07: a Nagahara estate sat on the bridge road). Test each outside estate footprint
            # against every recorded road.
            roads_all = [r["pts"] for r in M.get("roads", [])] or ([M["road"]] if M.get("road") else [])
            est_on_road = [(round(mn["x"]), round(mn["y"])) for mn in est_out if any(footprint_on_line(rect_corners(_struct_rect(mn)), rp, (M.get("road_width", 26) / 2 + 4)) for rp in roads_all)]
            check(
                "city_estates_clear_of_roads",
                not est_on_road,
                f"samurai estate(s) straddling a road out of the city: {est_on_road[:3]} - an estate fronts its own approach lane but must not sit ON the highway",
            )
            # the ground circulation (streets + alleys; NOT the Imperial road, which exits at the
            # gates) must stay INSIDE the wall and clear of the moat - separate checks, since a lane
            # can poke through the rampart, the moat, or both (the elliptical wall curves in, so a
            # lane run to the block edge can spill outside even with its vertices nominally interior)
            lanes_pts = [st["pts"] for st in M.get("town_streets", [])] + [a["pts"] for a in M.get("alleys", [])]

            def crosses_ring(pts: Poly, ring: Poly, closed: bool) -> bool:
                rng = range(len(ring)) if closed else range(len(ring) - 1)
                return any(segments_cross(pts[k], pts[k + 1], ring[i], ring[(i + 1) % len(ring)]) for k in range(len(pts) - 1) for i in rng)

            wall_hit = [pts[0] for pts in lanes_pts if crosses_ring(pts, w, True) or any(not inwall(p[0], p[1]) for p in pts)]
            check("city_streets_clear_of_wall", not wall_hit, f"{len(wall_hit)} street/alley(s) crossing the city wall (a lane running outside the rampart): {wall_hit}")
            moat = M.get("moat")
            if moat:
                moat_hit = [pts[0] for pts in lanes_pts if crosses_ring(pts, moat, False)]
                check("city_streets_clear_of_moat", not moat_hit, f"{len(moat_hit)} street/alley(s) crossing the moat: {moat_hit}")
            # farm fields (in-wall plots OR the surrounding farmland) must not cut across the wall stroke
            # or the moat - the moat sits between the wall and the close-in fields, so they abut, not overlap
            fld_bad = [f["name"] for f in fields if footprint_on_line(f["outline"], w, 10) or (moat and footprint_on_line(f["outline"], moat, 13))]
            check("city_fields_clear_of_wall_moat", not fld_bad, f"field(s) overlapping the city wall or moat: {fld_bad}")
            # the in-wall pond is a water source, not a moat - it must not touch the wall or moat
            pnd = M.get("pond")
            if pnd:
                pcx, pcy, prx, pry = pnd
                p_out = [(pcx + math.cos(math.tau * k / 28) * prx, pcy + math.sin(math.tau * k / 28) * pry) for k in range(28)]
                check("city_pond_clear_of_wall_moat", not (footprint_on_line(p_out, w, 9) or (moat and footprint_on_line(p_out, moat, 13))), "the in-wall pond overlaps the city wall or moat")
            # internal streets must not run THROUGH the civic compounds (ministries, governor, temples,
            # gate furniture) any more than they may through ordinary buildings
            civic = M.get("ministries", []) + M.get("religious", []) + M.get("inspection_stations", []) + ([gov] if gov else [])
            civic_on_street = [
                c.get("name") or c.get("label") or "compound" for st in M.get("town_streets", []) for c in civic if footprint_on_line(rect_corners_xywh(c, 0), st["pts"], st.get("w", 24) / 2 + 2)
            ]
            check("city_civic_clear_of_streets", not civic_on_street, f"city street(s) running through a civic compound: {civic_on_street}")

            # ZONE / NEIGHBORHOOD labels must sit WITH the cluster they name: ENTIRELY on the same side
            # of the city wall as that cluster, AMONG its buildings, and not floating over a foreign field.
            # A label over the moat, a neighboring compound, or a paddy misleads the reader about what it
            # names (the "laborer neighborhoods" label drifted outside the wall, "samurai neighborhood"
            # sat over a ministry, "burakumin neighborhood" sat over a field).
            def subject_of(txt: str) -> tuple[list[tuple[float, float]], float, bool]:
                t = txt.lower()
                if "estate" in t:
                    return [(m["x"], m["y"]) for m in M.get("manors", [])], 230, True
                if "agricultur" in t:  # the in-wall agricultural district, NOT the extramural farmland
                    return [c for c in (((f["bbox"][0] + f["bbox"][2]) / 2, (f["bbox"][1] + f["bbox"][3]) / 2) for f in fields) if inwall(*c)], 260, True
                if "temple" in t:
                    return [(r["x"], r["y"]) for r in M.get("religious", [])], 230, True
                for key, kinds in (
                    ("samurai", {"samurai", "samurai_large"}),
                    ("laborer", {"laborer", "laborer_large"}),
                    ("burakumin", {"burakumin"}),
                    ("merchant", {"merchant", "merchant_house", "merchant_large"}),
                ):
                    if key in t:
                        return [(b["x"], b["y"]) for b in M.get("buildings", []) if b.get("kind") in kinds], 130, False
                return [], 0, True

            bad_lab = []
            for lab in M.get("labels", []):
                if len(lab) <= 5 or not (lab[5].lower().endswith(("neighborhood", "neighborhoods", "district")) or "estates" in lab[5].lower()):
                    continue
                x0, y0, x1, y1, _z, txt = lab[:6]
                pts, reach, area_subj = subject_of(txt)
                if not pts:
                    continue  # nothing of that kind drawn - can't verify
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                subj_in = sum(1 for px, py in pts if inwall(px, py)) * 2 >= len(pts)
                if not all(inwall(px, py) == subj_in for px, py in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))):
                    bad_lab.append(f"{txt!r} not entirely {'inside' if subj_in else 'outside'} the wall (its cluster is)")
                elif min(math.hypot(px - cx, py - cy) for px, py in pts) > reach:
                    bad_lab.append(f"{txt!r} sits >{reach}px from any of its buildings - place it among them")
                elif not area_subj and any(point_in_poly(cx, cy, f["outline"]) for f in fields):
                    bad_lab.append(f"{txt!r} floats over a farm field, not its own houses")
            check("city_labels_placed_with_subject", not bad_lab, f"neighborhood/zone label(s) misplaced relative to what they name: {bad_lab}")
            # the surrounding farmland: every OUTSIDE field (even off-edge) has farmhouses, and the
            # fields sit close to the city (cities grow up around fertile land)
            out_fields = [f for f in fields if not inwall((f["bbox"][0] + f["bbox"][2]) / 2, (f["bbox"][1] + f["bbox"][3]) / 2)]
            no_farm = [f["name"] for f in out_fields if sum(1 for h in houses if poly_dist(h["x"], h["y"], f["outline"]) <= ADJ) < 2]
            check("city_outside_fields_have_farmhouses", not no_farm, f"outside field(s) with < 2 farmhouses (even off-edge fields are worked by nearby villagers): {no_farm}")
            far = [f["name"] for f in out_fields if len(w) >= 3 and min(poly_dist(p[0], p[1], w) for p in f["outline"]) > 520]
            check("city_fields_close_to_city", not far, f"outside field(s) too far from the city (cities grow up around fertile land, fields stay close): {far}")
            # a MOATED city irrigates several large fields from the moat
            if moat:
                chans = M.get("channels", [])
                big_out = [f for f in out_fields if (f["bbox"][2] - f["bbox"][0]) * (f["bbox"][3] - f["bbox"][1]) > 55000]

                def moat_fed(fo: dict[str, Any]) -> bool:
                    for c in chans:
                        ends = (c["poly"][0], c["poly"][-1])
                        near_moat = any(any(seg_dist(e[0], e[1], moat[i], moat[i + 1]) < 34 for i in range(len(moat) - 1)) for e in ends)
                        in_field = any(point_in_poly(e[0], e[1], fo["outline"]) for e in ends)
                        if near_moat and in_field:
                            return True
                    return False

                fed = [f["name"] for f in big_out if moat_fed(f)]
                check("city_moat_irrigates_fields", len(fed) >= 3, f"{len(fed)} large outside fields fed by moat irrigation, expected >= 3 (a moated city irrigates its farmland from the moat)")
            # a gate market outside one of the gates (like a town's guan-xiang)
            biz_out = [
                b for b in M.get("buildings", []) if b.get("kind") in ("shop", "merchant") and not inwall(b["x"], b["y"]) and any(math.hypot(b["x"] - g[0], b["y"] - g[1]) <= 520 for g in gates)
            ]
            check("city_has_gate_market", len(biz_out) >= 3, f"{len(biz_out)} businesses outside a gate - a city should have a gate market (like a town's guan-xiang)")
            # market-day lodging: a flophouse INSIDE the walls, and one OUTSIDE each gate (for
            # travelers arriving from either direction, who reach the gate after it has shut)
            flops = M.get("flophouses", [])
            check("city_flophouse_inside_walls", any(inwall(fl["x"], fl["y"]) for fl in flops), "a city needs market-day lodging inside the walls (a flophouse)")
            gates_wo_flop = [i for i, g in enumerate(gates) if not any((not inwall(fl["x"], fl["y"])) and math.hypot(fl["x"] - g[0], fl["y"] - g[1]) <= 520 for fl in flops)]
            check(
                "city_flophouse_outside_each_gate",
                not gates_wo_flop,
                f"every city gate needs a flophouse just outside it (travelers who arrive after the gate shuts sleep there); gate(s) without one: {gates_wo_flop}",
            )
            # a flophouse is a humble doss-house (a sen a night, on straw): inside the walls it belongs
            # in a HUMBLE quarter (the laborer section, or Tango's agrarian sector), NEVER cheek-by-jowl
            # with the nicer neighborhoods (temples, merchants, samurai), and never in or up against the
            # burakumin quarter. Only the in-wall flophouse is judged (the gate ones sit by the gate market).
            nice = [b for b in M.get("buildings", []) if b.get("kind") in ("merchant", "samurai", "samurai_large")] + M.get("religious", [])
            bura = [b for b in M.get("buildings", []) if b.get("kind") == "burakumin"]
            inns = [b for b in M.get("buildings", []) if b.get("kind") == "inn"]
            stbl = [b for b in M.get("buildings", []) if b.get("kind") == "stables"]
            bad_flop = []
            for fl in flops:
                if not inwall(fl["x"], fl["y"]):
                    continue
                # a CARAVAN flophouse (one paired with an inn AND a stables, a gate transit cluster) is
                # exempt from the humble-quarter rule - the gate is a transit zone, not a nice neighborhood
                if any(math.hypot(b["x"] - fl["x"], b["y"] - fl["y"]) < 170 for b in inns) and any(math.hypot(b["x"] - fl["x"], b["y"] - fl["y"]) < 170 for b in stbl):
                    continue
                if any(math.hypot(b["x"] - fl["x"], b["y"] - fl["y"]) < 110 for b in nice):
                    bad_flop.append((round(fl["x"]), round(fl["y"]), "next to a temple/merchant/samurai"))
                elif any(math.hypot(b["x"] - fl["x"], b["y"] - fl["y"]) < 150 for b in bura):
                    bad_flop.append((round(fl["x"]), round(fl["y"]), "in/next to the burakumin quarter"))
            check(
                "city_flophouse_in_humble_quarter",
                not bad_flop,
                f"in-wall flophouse(s) sited in/beside a nicer or burakumin neighborhood (a doss-house belongs in the laborer/agrarian sector): {bad_flop}",
            )
            # CARAVAN facilities: just INSIDE each gate a wagon-train needs a prominent INN and a large
            # STABLES (dozens of draft animals + crew) close to its flophouse, with OPEN GROUND around the
            # stables for the animals to be tied up / penned. Three buildings near each gate, not just one.
            caravan_bad = []
            for g in gates:

                def gnear(items: Sequence[dict[str, Any]], r: float = 340, g: Any = g) -> list[dict[str, Any]]:  # bind loop var (used within this iteration)
                    return [b for b in items if inwall(b["x"], b["y"]) and math.hypot(b["x"] - g[0], b["y"] - g[1]) <= r]

                gi, gs, gf = gnear(inns), gnear(stbl), gnear(flops)
                if not (gi and gs and gf):
                    caravan_bad.append((g, f"inn={len(gi)} stables={len(gs)} flophouse={len(gf)}"))
                    continue
                crowd = sum(1 for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS and math.hypot(b["x"] - gs[0]["x"], b["y"] - gs[0]["y"]) < 75)
                if crowd > 4:
                    caravan_bad.append((g, f"stables hemmed in by {crowd} dwellings (needs open ground for animals)"))
            check(
                "city_gate_caravan_facilities",
                not caravan_bad,
                f"city gate(s) lacking inside caravan facilities (a prominent inn + large stables + flophouse + open ground close to the gate): {caravan_bad}",
            )

            # at least a couple of the samurai estates must fall (even partly) inside the rendered
            # window, so the map signals that there are several - not just one - country estates
            def _shown(m: dict[str, Any]) -> bool:
                hw, hh = m["w"] / 2, m["h"] / 2
                return bool(m["x"] + hw > EX0 and m["x"] - hw < EX1 and m["y"] + hh > EY0 and m["y"] - hh < EY1)

            shown_est = [m for m in M.get("manors", []) if _shown(m)]
            check(
                "city_estates_multiple_shown",
                len(shown_est) >= 2,
                f"{len(shown_est)} samurai estates fall inside the map window - show at least 2 (cropped at the edge is fine) so it reads as several, not one",
            )
            # the Imperial-road label must sit OUTSIDE the walls (inside, the roadway is a city street)
            rlab = M.get("road_label")
            if rlab:
                check(
                    "city_road_label_outside_walls",
                    not inwall(rlab[0], rlab[1]),
                    "the 'Imperial Road' label must sit outside the walls - inside the gates the same roadway is a city street, a city (not Imperial) responsibility",
                )
            empty_city_streets = empty_street_runs(M, w)
            check(
                "city_streets_have_buildings",
                not empty_city_streets,
                f"city street(s) with a stretch inside the walls with no building fronting it (a street network earns its length from the buildings it serves): {empty_city_streets}",
            )
            # ROADSIDE LAND on a larger city street is PRIME real estate: a paved through-street in a
            # commercial/residential quarter must be LINED with buildings (houses, shops, civic halls)
            # close to it, not left with a long bare margin. This is stricter than city_streets_have_buildings
            # (which tolerates a building up to ~105px away): here a building must sit WITHIN ~58px of the
            # street, the way storefronts and house-fronts actually line a road. Only the narrow gravel
            # ALLEYS that thread the block interiors are exempt (those are the "small streets" that need no
            # frontage), and so is the GOVERNMENT avenue - its frontage is the spaced ministry compounds,
            # governed by city_ministries_front_a_street, not shops/houses. (The merchant avenue once read
            # bare because its storefront frontage was silently blocked by the avenue's own corridor.)
            line_blds = M.get("buildings", []) + M.get("religious", []) + M.get("ministries", []) + M.get("flophouses", []) + ([gov] if gov else [])
            gov_pts = M.get("ministries", []) + ([gov] if gov else [])
            LINE_D, LINE_RUN = 58, 140
            bare_streets = []
            for st in M.get("town_streets", []):
                pts = st["pts"]
                if sum(1 for m in gov_pts if min(seg_dist(m["x"], m["y"], pts[i], pts[i + 1]) for i in range(len(pts) - 1)) < 70) >= 2:
                    continue  # a government avenue - lined by ministry compounds
                worst = run = 0
                for ki in range(len(pts) - 1):
                    a, b = pts[ki], pts[ki + 1]
                    steps = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) // 20))
                    for j in range(steps):
                        t = j / steps
                        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                        if not point_in_poly(x, y, w) or any((bl["x"] - x) ** 2 + (bl["y"] - y) ** 2 < LINE_D * LINE_D for bl in line_blds):
                            run = 0
                        else:
                            run += 20
                            worst = max(worst, run)
                if worst > LINE_RUN:
                    bare_streets.append(("main" if st.get("main") else f"@{(round(pts[0][0]), round(pts[0][1]))}", worst))
            check(
                "city_larger_streets_lined",
                not bare_streets,
                f"larger city street(s) with a long bare stretch of roadside land - a commercial/residential through-street should be "
                f"LINED with buildings close to it (only narrow alleys may run unlined): {bare_streets}",
            )
            road = M.get("road") or []
            if meta.get("imperial_road", True):
                road_through = bool(road) and any(p[1] < EY0 for p in road) and any(p[1] > EY1 for p in road)
                check("city_imperial_road_through", road_through, "the Imperial road must run N-S through a walled city - off both the top and bottom edges, via the gates")
            else:
                # NO Imperial road (it passes miles away): the city still lives on through-traffic,
                # so its road net must leave the map in at least TWO directions (one polyline
                # bending through the city - off-map N, through the gates, off-map SE - counts
                # as two; a dead-end road serves nobody)
                rds = [r["pts"] for r in M.get("roads", [])] or ([road] if road else [])

                def offend(p: Pt) -> bool:
                    return p[0] < EX0 or p[0] > EX1 or p[1] < EY0 or p[1] > EY1

                exits = sum(1 for r in rds for e in (r[0], r[-1]) if offend(e))
                dead = [(round(e[0]), round(e[1])) for r in rds for e in (r[0], r[-1]) if not offend(e)]
                check(
                    "city_roads_run_offmap",
                    exits >= 2 and not dead,
                    f"{exits} off-map road end(s), dead end(s) at {dead[:3]} - a provincial city without an "
                    f"Imperial spine still connects to the wider world in >= 2 directions, and no road stops dead",
                )
            if not meta.get("agricultural_district"):
                inwall_fields = [f["name"] for f in fields if inwall((f["bbox"][0] + f["bbox"][2]) / 2, (f["bbox"][1] + f["bbox"][3]) / 2)]
                check("city_no_inwall_farms", not inwall_fields, f"farms inside a city wall are uncharacteristic - set meta(agricultural_district=True) to allow them: {inwall_fields}")
            # INTRAMURAL groves OFF: a farm inside the wall carries NO windbreak grove - an in-wall plot is not
            # an isolated farmstead (the urban fabric already breaks the wind) and sits on land too precious for
            # a tree belt. So the in-wall agricultural district stays grove-free. WHY: settlements.md "Homestead groves".
            if not meta.get("inwall_groves"):
                inwall_groves = sorted({(round(gv["of"][0]), round(gv["of"][1])) for gv in M.get("groves", []) if inwall(gv["of"][0], gv["of"][1])})
                check(
                    "no_groves_inside_walls",
                    not inwall_groves,
                    f"farm(s) inside the city wall carry a windbreak grove {inwall_groves[:3]} - an intramural plot is "
                    f"sheltered by the urban fabric and on land too precious for one (meta(inwall_groves=True) to allow)",
                )
            moat = M.get("moat")
            if moat:
                rv = M.get("river")
                if rv:
                    # a river-bank city's moat is an OPEN arc: the river closes the water ring on its
                    # flank (Xiangyang/Pingyao pattern). Coverage: every wall vertex stands behind
                    # water - within ~72px of the moat arc OR ~200px of the river (the wharf strip
                    # sits between wall and bank, so the river runs further out than a dug moat) -
                    # and BOTH open moat ends must actually JOIN the river (inlet upstream, outlet
                    # downstream, the current flushing the ring).
                    rpts = rv["pts"]

                    def rdist(q: Pt) -> float:
                        return min(seg_dist(q[0], q[1], rpts[i], rpts[i + 1]) for i in range(len(rpts) - 1))

                    bare = [(round(wx), round(wy)) for wx, wy in w if min(seg_dist(wx, wy, moat[i], moat[i + 1]) for i in range(len(moat) - 1)) > 72 and rdist((wx, wy)) > 200]
                    check(
                        "city_moat_surrounds_wall",
                        not bare,
                        f"wall stretch(es) behind neither the moat arc nor the river: {bare[:4]} - a river-bank city's dug moat covers the landward faces and the river covers its own flank",
                    )
                    loose = [(round(e[0]), round(e[1])) for e in (moat[0], moat[-1]) if rdist(e) > rv["w"] / 2 + 12]
                    check(
                        "city_moat_joins_river",
                        not loose,
                        f"open moat end(s) not joining the river: {loose} - the moat taps the river upstream and returns downstream (the current flushes it); extend the ends onto the river",
                    )
                else:
                    check("city_moat_surrounds_wall", len(w) >= 3 and all(point_in_poly(wx, wy, moat) for wx, wy in w), "the moat must encircle the wall (every wall point inside the moat ring)")
                moat_is_fed = any(
                    any(p[0] < EX0 or p[0] > EX1 or p[1] < EY0 or p[1] > EY1 for p in (s["poly"][0], s["poly"][-1])) and min(poly_dist(q[0], q[1], moat) for q in s["poly"]) <= 32
                    for s in M.get("streams", [])
                )
                check("city_moat_fed_offmap", moat_is_fed, "the moat must be fed from an off-map water source (a stream from a map edge reaching the moat)")
                # the FEEDER must carry the moat's flow: a stream filling the moat is as WIDE as the moat
                # itself (a trickle cannot keep a full moat supplied) - so any stream reaching the moat must
                # match its width (within ~25%).
                mw = M.get("moat_width", 22)
                feeders = [s for s in M.get("streams", []) if min(poly_dist(q[0], q[1], moat) for q in s["poly"]) <= 32]
                narrow = [s.get("w", 9) for s in feeders if s.get("w", 9) < 0.75 * mw]
                check(
                    "city_moat_feeder_matches_width",
                    not narrow,
                    f"the stream feeding the moat is too narrow ({narrow} px vs the {mw}px moat) - a moat's water source "
                    f"must be about as wide as the moat it supplies (pass s.stream(..., width=<moat width>))",
                )

            # RIVER-CITY WATERWORKS (a cargo canal + wharf; only where they are drawn):
            river_c: Any = M.get("river")
            canals_c = M.get("canals", [])
            docks_c = M.get("docks", [])
            # (1) THE CANAL CONNECTS THE RIVER TO THE DOCK, like a street reaching the road: one end
            # taps the river (through the water gate), the other feeds the in-city dock basin - a
            # canal that stops short of the dock is a ditch to nowhere (GM, 2026-07: Nagahara's canal
            # left a visible gap to the dock). "Reaches" = the end's bed physically meets the target
            # (within the target's half-extent + the canal half-width + a small tolerance).
            if canals_c:

                def _end_near_river(e: Pt) -> bool:
                    return bool(river_c) and min(seg_dist(e[0], e[1], river_c["pts"][i], river_c["pts"][i + 1]) for i in range(len(river_c["pts"]) - 1)) <= river_c["w"] / 2 + 14

                def _end_near_dock(e: Pt, chw: float) -> bool:
                    # the canal MOUTH opens into the basin: the endpoint sits at the quay edge or
                    # inside it (a visible gap to the dock = not connected), so no slack beyond ~3px
                    return any(abs(e[0] - d["x"]) <= d["w"] / 2 + 3 and abs(e[1] - d["y"]) <= d["h"] / 2 + 3 for d in docks_c)

                unreached = []
                for c in canals_c:
                    chw = c.get("w", 12) / 2
                    ends = (c["poly"][0], c["poly"][-1])
                    if not (any(_end_near_river(e) for e in ends) and (not docks_c or any(_end_near_dock(e, chw) for e in ends))):
                        unreached.append([round(c["poly"][0][0]), round(c["poly"][0][1])])
                check(
                    "city_canal_reaches_dock",
                    not unreached,
                    f"cargo canal(s) not connecting the river to the dock basin: {unreached[:3]} - one end taps the "
                    f"river (at the water gate), the other must feed the in-city dock (extend it to the quay, like a "
                    f"street reaching the road)",
                )
            # (2) THE WHARF JETTIES REACH THE BANK: a jetty is a finger running out from the river's
            # near bank into the water - its landward end must TOUCH the bank, not float mid-stream
            # (GM, 2026-07: Nagahara's jetties floated in the middle of the river). The near bank is
            # the river centerline offset by half its width toward the city; a jetty's nearest end
            # must sit within ~14px of it.
            jetties_c = M.get("jetties", [])
            if jetties_c and river_c:
                rp = river_c["pts"]
                rhw = river_c["w"] / 2
                cx_r = sum(p[0] for p in w) / len(w) if len(w) >= 3 else EX0
                cy_r = sum(p[1] for p in w) / len(w) if len(w) >= 3 else EY0
                floats = []
                for j in jetties_c:
                    jends = [(j["x"], j["y"]), (j["x"] + math.cos(math.radians(j["rot"])) * j["len"], j["y"] + math.sin(math.radians(j["rot"])) * j["len"])]

                    # a jetty runs out from the CITYWARD bank into the water. At least one end must
                    # sit on that near bank: within ~14px of the bank line (|dist-to-centerline - rhw|
                    # small) AND on the city's side of the centerline (dot of (end - foot) with the
                    # direction to the wall centroid is positive).
                    def cityward_dist(px: float, py: float) -> tuple[float, bool]:
                        # (distance to the river centerline, is-it-on-the-city-side-of-the-centerline)
                        k = min(range(len(rp) - 1), key=lambda i: seg_dist(px, py, rp[i], rp[i + 1]))
                        fx, fy = seg_closest(px, py, rp[k], rp[k + 1])
                        d = math.hypot(px - fx, py - fy)
                        cityward = (px - fx) * (cx_r - fx) + (py - fy) * (cy_r - fy) > 0
                        return d, cityward

                    # a jetty is a FINGER: its ROOT sits at the near bank or just onto land (cityward,
                    # >= rhw-6 from the centerline - so the plank visibly connects to the shore, not
                    # floating a stride out in the water), and its TIP runs INTO the near-half water
                    # (cityward, <= rhw - it neither floats mid-stream nor spans past the far bank).
                    root = any((lambda dc: dc[1] and dc[0] >= rhw - 6)(cityward_dist(*e)) for e in jends)
                    tip = any((lambda dc: dc[1] and dc[0] <= rhw)(cityward_dist(*e)) for e in jends)
                    if not (root and tip):
                        floats.append([round(jends[0][0]), round(jends[0][1])])
                check(
                    "city_wharf_jetties_on_bank",
                    not floats,
                    f"wharf jetties floating off the bank: {floats[:3]} - a jetty's landward end must touch the river's near bank, running out into the water from there, not float mid-stream",
                )

            # the street network must be CONNECTED - one coherent grid wired to the Imperial
            # road, not isolated stubs (ported from the town "no street to nowhere" thinking).
            streets = M.get("town_streets", [])
            if streets:
                sseg = [st["pts"] for st in streets] + ([M["road"]] if M.get("road") else [])
                # width of each segment's paved bed (the road counts as a street here): two streets
                # are CONNECTED only if you can walk between them, i.e. their beds actually overlap -
                # centerline gap < the sum of their half-widths. A street whose end stops even a roadbed
                # short of the next one is a SEPARATE network (you cannot step from one to the other),
                # which is exactly the laborer grid that ended 40px shy of the Imperial road. (Kido ward
                # gates do NOT break this: the street centerline runs on under the gate, uninterrupted.)
                widths = [st.get("w", 18) for st in streets] + ([M.get("road_width", 26)] if M.get("road") else [])
                parent = list(range(len(sseg)))

                def find2(a: int) -> int:
                    while parent[a] != a:
                        parent[a] = parent[parent[a]]
                        a = parent[a]
                    return a

                def beds_meet(ia: int, ib: int) -> bool:  # beds overlap: segments cross, or a centerline endpoint lies
                    sa, sb = sseg[ia], sseg[ib]  # within the two beds' combined half-widths (+2px slack)
                    tol = widths[ia] / 2 + widths[ib] / 2 + 2
                    for i in range(len(sa) - 1):
                        for k in range(len(sb) - 1):
                            if segments_cross(sa[i], sa[i + 1], sb[k], sb[k + 1]):
                                return True
                            if (
                                seg_dist(sa[i][0], sa[i][1], sb[k], sb[k + 1]) < tol
                                or seg_dist(sa[i + 1][0], sa[i + 1][1], sb[k], sb[k + 1]) < tol
                                or seg_dist(sb[k][0], sb[k][1], sa[i], sa[i + 1]) < tol
                                or seg_dist(sb[k + 1][0], sb[k + 1][1], sa[i], sa[i + 1]) < tol
                            ):
                                return True
                    return False

                for ai in range(len(sseg)):
                    for bi in range(ai + 1, len(sseg)):
                        if beds_meet(ai, bi):
                            parent[find2(ai)] = find2(bi)
                comps = {find2(i) for i in range(len(streets))}
                check(
                    "city_streets_connected",
                    len(comps) == 1,
                    f"the city streets form {len(comps)} disconnected groups - a street whose bed does not actually reach another's is a separate network; wire every grid to the Imperial road (extend it until the beds overlap)",
                )

                # two streets that come ALMOST together without meeting read as a mistake - they
                # should either JOIN (cross/touch) or stay clearly apart, never leave a sliver gap
                def seg_seg_dist(a0: Pt, a1: Pt, b0: Pt, b1: Pt) -> float:
                    return min(seg_dist(a0[0], a0[1], b0, b1), seg_dist(a1[0], a1[1], b0, b1), seg_dist(b0[0], b0[1], a0, a1), seg_dist(b1[0], b1[1], a0, a1))

                slines = [st["pts"] for st in streets]
                near_miss = set()
                for ia in range(len(slines)):
                    for ib in range(ia + 1, len(slines)):
                        for i in range(len(slines[ia]) - 1):
                            for ki in range(len(slines[ib]) - 1):
                                if segments_cross(slines[ia][i], slines[ia][i + 1], slines[ib][ki], slines[ib][ki + 1]):
                                    continue
                                if 2 < seg_seg_dist(slines[ia][i], slines[ia][i + 1], slines[ib][ki], slines[ib][ki + 1]) < 30:
                                    near_miss.add((ia, ib))
                check(
                    "city_streets_no_near_miss",
                    not near_miss,
                    f"city street pair(s) that come within a sliver of each other without meeting - close the gap so they join, or separate them: {sorted(near_miss)}",
                )
                # a street that crosses another and then STOPS a little way past it leaves an ugly
                # dangling stub. Fine to cross and keep going (to the next block/edge), or to
                # terminate AT the junction (an L/T corner), but not to overshoot it by a sliver.
                stub = set()
                for ia, sa in enumerate(slines):
                    for end, nbr in ((sa[0], sa[1]), (sa[-1], sa[-2])):
                        for ib, sb in enumerate(slines):
                            if ib == ia:
                                continue
                            for ki in range(len(sb) - 1):
                                if segments_cross(nbr, end, sb[ki], sb[ki + 1]) and 3 < seg_dist(end[0], end[1], sb[ki], sb[ki + 1]) < 50:
                                    stub.add((ia, ib))
                check(
                    "city_streets_no_intersection_stub",
                    not stub,
                    f"city street(s) that cross another and then stop just past it, leaving a dangling stub - end them AT the junction or run them on: {sorted(stub)}",
                )

            # a temple a city street runs UP TO (a street that terminates at its front) marks a
            # sacred approach - it needs torii arches on that street, just in front of the temple
            torii = M.get("torii", [])

            def pt_rect(px: float, py: float, t: dict[str, Any]) -> float:
                dx = max(t["x"] - t["w"] / 2 - px, 0, px - t["x"] - t["w"] / 2)
                dy = max(t["y"] - t["h"] / 2 - py, 0, py - t["y"] - t["h"] / 2)
                return math.hypot(dx, dy)

            no_torii = []
            for t in [r for r in M.get("religious", []) if r.get("kind") == "temple"]:
                runs_up = any(min(pt_rect(e[0], e[1], t) for e in (st["pts"][0], st["pts"][-1])) < 28 for st in M.get("town_streets", []))
                if runs_up and not any(math.hypot(to[0] - t["x"], to[1] - t["y"]) < 95 for to in torii):
                    no_torii.append(t.get("label"))
            check("city_temple_approach_has_torii", not no_torii, f"temple(s) a city street runs straight up to, with no torii arch in front: {no_torii}")
            # and a temple's torii avenue should FILL the clear approach space: where a temple HAS torii
            # (an established sacred approach) and there is still open room along its street for another
            # arch - AFTER all the housing is placed - it should be filled. This never asks for a building
            # to move (the next slot is tested only against EXISTING open ground); a temple with no torii,
            # or one whose approach is built right up to its avenue, is left alone (0-1 torii is fine).
            temples = [r for r in M.get("religious", []) if r.get("kind") == "temple"]
            underfilled = []
            for r in temples:
                grp = [t for t in torii if min(temples, key=lambda x: math.hypot(x["x"] - t[0], x["y"] - t[1])) is r]
                if grp and torii_room_for_more(r, grp, M, w, Wd, Hd):
                    underfilled.append(r.get("label"))
            check(
                "city_temple_torii_fill_approach",
                not underfilled,
                f"temple(s) with clear room for MORE torii along their approach street, left unfilled (a temple's "
                f"torii avenue fills the open space leading up to it; this never displaces a building): {underfilled}",
            )
            # a torii arch stands OVER the street it spans - the street passes beneath it - so a
            # torii sitting on a street must be drawn after (higher z than) that street, not under it
            to_under = []
            for t in torii:
                for st in M.get("town_streets", []):
                    sp = st["pts"]
                    if any(seg_dist(t[0], t[1], sp[i], sp[i + 1]) <= st.get("w", 24) / 2 + 12 for i in range(len(sp) - 1)) and t[2] <= st.get("z", 0):
                        to_under.append((t[0], t[1]))
            check("city_torii_over_streets", not to_under, f"torii arch(es) drawn UNDER a street they span (the street must pass beneath the arch): {to_under}")
            # no LARGE empty swath inside the walls (ported from wall_hugs_the_town). A city keeps
            # SOME open ground (drill / refuge / the road's right-of-way), so this is generous,
            # but a big contiguous region with no buildings, civic structures, fields, or pond
            # would not have been walled in.
            occ = [(b["x"], b["y"]) for b in M.get("buildings", []) + houses]
            for gkey in ("manors", "ministries", "religious", "inspection_stations"):
                occ += [(o["x"], o["y"]) for o in M.get(gkey, [])]
            occ += [(o["x"], o["y"]) for o in M.get("flophouses", []) + M.get("storehouses", [])]
            for one in (M.get("governor_mansion"), M.get("theater_stage")):
                if one:
                    occ.append((one["x"], one["y"]))
            field_polys = [f["outline"] for f in fields]
            pondE = M.get("pond")

            def used(x: float, y: float) -> bool:
                if any((x - ox) ** 2 + (y - oy) ** 2 < 120 * 120 for ox, oy in occ):
                    return True
                if pondE and in_ellipse(x, y, pondE, 1.1):
                    return True
                return any(point_in_poly(x, y, fp) for fp in field_polys)

            STEP = 80
            empty_cells = set()
            for ci in range(int(Wd // STEP) + 1):
                for cj in range(int(Hd // STEP) + 1):
                    x, y = ci * STEP, cj * STEP
                    if point_in_poly(x, y, w) and not used(x, y):
                        empty_cells.add((ci, cj))
            seen_cells, largest = set(), 0
            for cell in empty_cells:
                if cell in seen_cells:
                    continue
                cell_stack, size = [cell], 0
                seen_cells.add(cell)
                while cell_stack:
                    pi, pj = cell_stack.pop()
                    size += 1
                    for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nb = (pi + di, pj + dj)
                        if nb in empty_cells and nb not in seen_cells:
                            seen_cells.add(nb)
                            cell_stack.append(nb)
                largest = max(largest, size)
            check(
                "city_no_large_empty_space",
                largest <= 12,
                f"a contiguous empty region of ~{largest} grid cells (~{largest * STEP * STEP // 1000}k px2) inside the walls - a city does not wall in large unused ground",
            )

    # Tax-free (temple/monk glebe) plots are OPTIONAL - marking them on the map is a choice, not a
    # requirement. The check only validates the COUNT when a map opts in (it drew some, or meta asks for
    # them); a village that does not denote them at all is fine.
    if scale == "village" and (M.get("taxfree") or meta.get("taxfree_expected")):
        tf = M.get("taxfree", [])
        check("taxfree_plots_in_range", 2 <= len(tf) <= 3, f"{len(tf)} tax-free plots (law: ~2 households)")

    big_paddies = sorted(
        [f for f in fields if f["kind"] == "paddy" and (f["bbox"][2] - f["bbox"][0]) * (f["bbox"][3] - f["bbox"][1]) > 80000],
        key=lambda f: -(f["bbox"][2] - f["bbox"][0]) * (f["bbox"][3] - f["bbox"][1]),
    )
    if scale != "city" and len(big_paddies) >= 2:  # a city's in-wall plots / off-edge fields are not staggered common fields

        def wide(f: dict[str, Any]) -> bool:
            return bool((f["bbox"][2] - f["bbox"][0]) >= (f["bbox"][3] - f["bbox"][1]))

        check("common_fields_vary_orientation", wide(big_paddies[0]) != wide(big_paddies[1]), "the two large common fields share an orientation")

    if meta.get("fallow_implies_abandoned"):
        for f in fields:
            if f["kind"] == "fallow":
                ab = sum(1 for h in houses if h["kind"] == "abandoned" and poly_dist(h["x"], h["y"], f["outline"]) <= ADJ)
                check(f"fallow_has_abandoned[{f['name']}]", ab >= 2, f"{ab} abandoned near {f['name']}, need 2")

    if meta.get("shrine_on_hill") and M.get("shrine") and M.get("summit") and hill:
        sx, sy, sw, sh = M["shrine"]
        sc = [(sx, sy), (sx + sw, sy), (sx + sw, sy + sh), (sx, sy + sh)]
        on_hill = all(in_ellipse(px, py, hill) for px, py in sc)
        on_summit = in_ellipse(sx + sw / 2, sy + sh / 2, M["summit"])
        check("shrine_on_hill_summit", on_hill and on_summit, "shrine overhangs the hill or is off the summit")
        offhill = [t for t in torii if not in_ellipse(t[0], t[1], hill)]
        check("torii_on_hill", not offhill, f"{len(offhill)} torii off the hill")

    if "torii_expected" in meta:
        check("torii_count", len(torii) == meta["torii_expected"], f"{len(torii)} torii, expected {meta['torii_expected']}")

    if M.get("pond"):
        pcx, pcy, prx, pry = M["pond"]
        if headman is not None:
            check("pond_bigger_than_headman", math.pi * prx * pry > headman["w"] * headman["h"], "pond not larger than headman house")
        if hill:
            check("pond_clear_of_hill", not in_ellipse(pcx, pcy, hill, 1.4), "pond too close to the hill (erosion)")

    # A declared LAND-USE overlay must actually be DRAWN (feature 005 US4): a village that says it grows
    # mulberry-fishpond / rape / lotus / hill-tea must show plots (or a tea fringe) of it, not just a label.
    lu = meta.get("land_use_overlay")
    if lu and lu != "none":
        recs = [r for r in M.get("land_use", []) if r.get("overlay") == lu]
        wet = {tuple(p) for p in M.get("wet_plots", [])}
        # An overlay with NO eligible ground legitimately draws nothing (feature 010) - so the "was it
        # drawn" test is: the record must EXIST (proving apply_land_use ran), and must have a non-zero
        # count unless there was no eligible ground for it to sit on.
        had_ground = bool(wet) or lu == "tea_fringe" or (recs and recs[0].get("eligible") == "all")
        check(
            "land_use_overlay_drawn",
            bool(recs) and (recs[0].get("count", 0) > 0 or not had_ground),
            f"meta declares land_use_overlay={lu!r} but no plots/rows were drawn with it - call s.apply_land_use()",
        )

        # TOPOGRAPHIC GROUNDING (feature 010). A plot-based overlay may only sit on the LOW/WET ground.
        # Topography sets which plots are ELIGIBLE; economy decides how many convert. Deep-water lotus
        # (30-50cm, vs paddy rice's 5-9cm) physically cannot sit on high ground, and the dike-pond system
        # was dug out of 低洼易有洪患之处 - the low flood-prone hollows. See research.md D1/D2.
        # `eligible == "all"` is the named wholesale-conversion opt-out used by the dike-pond ARCHETYPE.
        # Teeth: `wet_plots` is written by the FIELD pass and `plots` by the OVERLAY pass, so this
        # compares two independently-produced records rather than reading back a self-report.
        for r in recs:
            if r.get("eligible") == "all" or not r.get("plots"):
                continue
            off = [p for p in r["plots"] if tuple(p) not in wet]
            check("overlays_on_wet_ground_only", not off, f"{len(off)} {lu} plot(s) sit on ordinary rice ground, not the low/wet ground that determines them (e.g. {off[:2]})")

        # NO `dikeponds_are_clustered` CHECK - deliberately, and this is worth recording so nobody "adds
        # the missing check" later. The dike-pond conversion really did spread plot-by-plot in patches
        # (挖塘培基, a one-plot job in one dry season), and `_pick_overlay_plots` models that. But it is
        # NOT INDEPENDENTLY OBSERVABLE here: the eligible set is always a thin contiguous strip of low
        # ground (comb = plots abutting the drain, polder = the lowest rows, terraces/ribbon = the lowest
        # bands), and every subset of a strip is "clustered" by any nearest-neighbor-vs-span metric. A
        # version of this check was written, and an EVEN random scatter of the same count passed it - so
        # it would have been a check that cannot fail, which is worse than no check. If a future field
        # archetype ever yields a genuinely 2-D eligible region, this becomes testable and worth adding.

    # IN-FIELD PADDY FEATURES (feature 012) must honor the per-archetype ELIGIBILITY MATRIX
    # (specs/012-.../research.md): a low-pocket pond, a bedrock rock outcrop, or a rare grave island appear
    # only where their archetype allows, and NEVER on mulberry_dike_fishpond (open water is its fabric).
    # Ponds must additionally sit on LOW/WET ground (the pocket that determines them) - teeth from `wet_plots`
    # (written by the field pass) vs the pond record (written by the feature pass), two independent sources.
    arch = meta.get("field_archetype")
    _ELIG = {
        "field_ponds": ("valley_paddy", "contour_terraces", "polder_grid", "ribbon_valley"),
        "field_rocks": ("contour_terraces", "ribbon_valley"),
        "field_graves": ("valley_paddy", "contour_terraces", "ribbon_valley"),
    }
    if arch:
        mis = [(k, len(M.get(k, []))) for k, ok in _ELIG.items() if M.get(k) and arch not in ok]
        check("paddy_features_match_archetype", not mis, f"in-field feature(s) on the wrong paddy type ({arch}): {mis} - see the archetype matrix in specs/012-in-field-paddy-features/research.md")
        if M.get("field_ponds"):
            wet = {tuple(p) for p in M.get("wet_plots", [])}
            off = [[p["x"], p["y"]] for p in M["field_ponds"] if (p["x"], p["y"]) not in wet]
            check("field_ponds_on_low_ground", not off, f"{len(off)} field pond(s) not on the low/wet ground that determines them (e.g. {off[:2]}) - a pond is a LOW pocket, not a mid-field puddle")

    # A contour-TERRACES field (feature 005 US4) must actually read as STEPPED CROSS-SLOPE BANDS: enough terrace
    # retaining bunds, each running roughly PERPENDICULAR to the fall (a terrace lip follows the contour, across
    # the slope - a bund that ran downhill would be a channel, not a terrace step). This is the archetype's teeth.
    if meta.get("field_archetype") == "contour_terraces":
        bunds = M.get("terrace_bunds", [])
        dd = meta.get("down_deg", 90)
        ddx, ddy = math.cos(math.radians(dd)), math.sin(math.radians(dd))
        n_cross = 0
        for bl in bunds:
            if len(bl) < 2:
                continue
            along = abs((bl[-1][0] - bl[0][0]) * ddx + (bl[-1][1] - bl[0][1]) * ddy)  # span along the fall
            acrs = abs((bl[-1][0] - bl[0][0]) * -ddy + (bl[-1][1] - bl[0][1]) * ddx)  # span across the fall
            if acrs > 2.0 * along:  # a genuine n_cross-slope contour bund
                n_cross += 1
        check(
            "contour_terraces_are_stepped_bands",
            len(bunds) >= 8 and n_cross >= 8,
            f"a contour_terraces field needs >=8 cross-slope terrace bunds (found {len(bunds)} bunds, {n_cross} cross-slope) - the defining stepped-band look",
        )

    # A POLDER-grid field (feature 005 US4) is a solid rectilinear BLOCK - it FILLS its bounding box (unlike the
    # comb fan or the contour terraces, whose outline covers a small fraction of its bbox). That fill ratio is
    # the archetype's teeth: a polder reads as a surveyed rectangle, not an organic field.
    if meta.get("field_archetype") == "polder_grid" and fields:
        pf = fields[0]
        b = pf.get("bbox") or [0, 0, 1, 1]
        bbox_area = max(1.0, (b[2] - b[0]) * (b[3] - b[1]))
        fill_ratio = poly_area(pf["outline"]) / bbox_area
        check(
            "polder_fills_its_bbox",
            fill_ratio >= 0.82,
            f"a polder_grid field must FILL its bounding box (a surveyed rectangular block), but its outline covers only {fill_ratio:.0%} of its bbox - that reads as a fan/terraced field, not a polder",
        )

    # A MULBERRY-DIKE FISH-POND field (feature 005 US4, 桑基魚塘) is a filled block whose cells are FISH PONDS
    # rimmed by mulberry dikes - so it must both fill its bbox (a reclaimed block) AND carry a mulberry_fishpond
    # land-use over most of it. China-first: the Pearl-delta closed sericulture-aquaculture system.
    if meta.get("field_archetype") == "mulberry_dike_fishpond" and fields:
        pf = fields[0]
        b = pf.get("bbox") or [0, 0, 1, 1]
        dp_fill = poly_area(pf["outline"]) / max(1.0, (b[2] - b[0]) * (b[3] - b[1]))
        pond_rec = [r for r in M.get("land_use", []) if r.get("overlay") == "mulberry_fishpond" and r.get("count", 0) >= 20]
        check(
            "dikepond_is_ponds_in_a_block",
            dp_fill >= 0.82 and bool(pond_rec),
            f"a mulberry_dike_fishpond field must be a filled block ({dp_fill:.0%} of bbox) of many mulberry-rimmed fish ponds (enough pond cells: {bool(pond_rec)}) - the 桑基魚塘 system",
        )

    # A RIBBON-VALLEY field (feature 005 US4) is LONG and NARROW - a thin strip strung down a confined valley -
    # so its extent ALONG the fall is much greater than its extent ACROSS it. That aspect is the archetype's
    # teeth: a ribbon reads as a winding valley strip, not a broad fan/block.
    if meta.get("field_archetype") == "ribbon_valley" and fields:
        dd = meta.get("down_deg", 90)
        rdx, rdy = math.cos(math.radians(dd)), math.sin(math.radians(dd))
        ol = fields[0]["outline"]
        along_vals = [px * rdx + py * rdy for px, py in ol]
        cross_vals = [px * -rdy + py * rdx for px, py in ol]
        along_span = max(along_vals) - min(along_vals)
        cross_span = max(1.0, max(cross_vals) - min(cross_vals))
        check(
            "ribbon_is_long_and_narrow",
            along_span >= 2.0 * cross_span,
            f"a ribbon_valley field must run far along the fall relative to its width (along {along_span:.0f} vs across {cross_span:.0f}, want >=2x) - the defining narrow-valley strip",
        )

    # SOFT ADVISORY (default-on; a map opts out with meta(crop_advisory=False)): a single feature that could
    # be moved to free a significantly tighter crop. NOT a failure - it never enters `fails` or gates the map;
    # it just prints a hint. (Unlike a hard invariant, e.g. houses-clear-of-moats, this is a default we accept.)
    if meta.get("crop_advisory", True):
        for adv in crop_relocatable_singletons(M):
            if verbose:
                who = f"the {adv['kind']} at {adv['at']} (a {adv['members']}-feature group, moved as one unit)" if adv.get("members", 1) > 1 else f"the {adv['kind']} at {adv['at']} alone"
                print(
                    f"ADVISORY crop_could_tighten  -> {who} holds the "
                    f"{adv['edge']} crop edge out by ~{adv['shrink']}px; empty space near {adv['landing']} "
                    f"could take it, cropping the image significantly smaller (soft hint - move it + re-crop, "
                    f"or set meta(crop_advisory=False) to silence)"
                )

    if verbose:
        print(f"\n{len(fails)} failing check(s): {fails}" if fails else "\nALL CHECKS PASSED")
    return fails


# ---- Pool-level twin-detector (feature 005) -----------------------------------------------------
# The per-map gate() validates ONE manifest; this is a CROSS-map tool. Two villages that share a water
# direction (down_deg) should still read as different PLACES - the GM's complaint was that Kikuta was a
# near-copy of Hoshigaoka down to the headman's house position. So for every same-down_deg pair we count
# how many of the structural axes a viewer actually reads (SC-001) fall in DIFFERENT coarse buckets, and
# flag the pair when too few differ. Two design choices, both from research.md D6:
#   - Same-down_deg SCOPING: villages that already differ by water direction are trivially distinguishable
#     and are not compared (comparing them would dilute the signal).
#   - COARSE buckets (which side / which type / which octant), never pixel positions, so genuine near-
#     variants are not falsely flagged as twins - the axes answer "different KIND of place?", not "moved a
#     few px?". The 4-of-7 threshold is the tuning target; recorded with its reasoning in settlements.md.
TWIN_AXES = ("cluster_region", "cluster_shape", "headman_side", "lane_skeleton", "water_source", "focal_set", "grain_orient", "settlement_form")
TWIN_MIN_DIFF = 4  # a same-down_deg pair must differ on >= this many of the 8 axes to read as distinct


def _dir8(dx: float, dy: float, dead: float = 1e-9) -> str | None:
    """Bucket a vector into one of 8 compass labels (N/NE/E/SE/S/SW/W/NW), y DOWN = south. Returns None
    for a ~zero vector (no meaningful direction). Coarse on purpose: a village on the W margin reads the
    same whether it is a few px higher or lower."""
    if dx * dx + dy * dy < dead:
        return None
    ang = math.degrees(math.atan2(dy, dx)) % 360  # 0=E, 90=S (y down), 180=W, 270=N
    return ("E", "SE", "S", "SW", "W", "NW", "N", "NE")[int((ang + 22.5) % 360 // 45)]


def _cluster_centroid(M: Manifest) -> tuple[float, float] | None:
    hs = M.get("houses", [])
    if not hs:
        return None
    return (sum(h["x"] for h in hs) / len(hs), sum(h["y"] for h in hs) / len(hs))


def twin_axes(M: Manifest) -> dict[str, Any]:
    """Extract the coarse structural axes a viewer reads a village by, for twin comparison. Each axis is
    a small hashable label (or None when the map lacks the data); two maps 'differ' on an axis only when
    both are present and their labels are unequal (a missing datum never manufactures a difference)."""
    meta = M.get("meta", {})
    hs = M.get("houses", [])
    cen = _cluster_centroid(M)
    fields = M.get("fields", [])
    fb = fields[0]["bbox"] if fields else None
    fc = ((fb[0] + fb[2]) / 2, (fb[1] + fb[3]) / 2) if fb else None
    ax: dict[str, Any] = {}

    # 1. cluster_region: which side of the field the village sits on (the 背山面水 "background" octant)
    ax["cluster_region"] = _dir8(cen[0] - fc[0], cen[1] - fc[1]) if (cen and fc) else None

    # 2. cluster_shape: the declared knob if present, else the cluster-bbox aspect (round vs elongated + axis)
    if meta.get("cluster_shape"):
        ax["cluster_shape"] = meta["cluster_shape"]
    elif hs:
        xs = [h["x"] for h in hs]
        ys = [h["y"] for h in hs]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        r = w / h if h else 1.0
        ax["cluster_shape"] = "round" if 0.7 <= r <= 1.4 else ("wide" if r > 1.4 else "tall")
    else:
        ax["cluster_shape"] = None

    # 3. headman_side: where the headman compound sits WITHIN the cluster (octant off the centroid, or
    #    'center' when near the middle) - the GM's specific twinning symptom
    headman = next((h for h in hs if h.get("role") == "headman"), None)
    if headman and cen:
        span = 0.0
        if hs:
            span = max(max(h["x"] for h in hs) - min(h["x"] for h in hs), max(h["y"] for h in hs) - min(h["y"] for h in hs))
        d = math.hypot(headman["x"] - cen[0], headman["y"] - cen[1])
        ax["headman_side"] = "center" if d < 0.15 * span else _dir8(headman["x"] - cen[0], headman["y"] - cen[1])
    else:
        ax["headman_side"] = None

    # 4. lane_skeleton: the declared knob (spine / T / Y / cross / waterside); no reliable geometric fallback
    ax["lane_skeleton"] = meta.get("lane_skeleton")

    # 5. water_source: pond octant off the field center (which corner), else the stream entry edge, else None
    pond = M.get("pond")
    if meta.get("water_source_position"):
        ax["water_source"] = meta["water_source_position"]
    elif pond and fc:
        ax["water_source"] = _dir8(pond[0] - fc[0], pond[1] - fc[1])
    else:
        ax["water_source"] = None

    # 6. focal_set: the set of OPTIONAL focal features present (a frozenset so order does not matter)
    ax["focal_set"] = frozenset(meta.get("focal_features", []))

    # 7. grain_orient: median paddy/dry-plot grain angle, bucketed to 15-degree bands (mod 180, a bund has
    #    no head/tail) - the "uniform 45deg" residual becomes a real differentiator once it drifts per map
    thetas = [d["theta"] for d in M.get("dry_plots", []) if "theta" in d]
    if thetas:
        med = sorted(thetas)[len(thetas) // 2]
        ax["grain_orient"] = round((math.degrees(med) % 180) / 15)
    else:
        ax["grain_orient"] = None

    # 8. settlement_form: nucleated blob vs linear ribbon vs dispersed vs water-town - the biggest structural
    #    read of all. Defaults to 'nucleated' (the base form) when a map does not declare it.
    ax["settlement_form"] = meta.get("settlement_form", "nucleated")
    return ax


def twin_diff_count(a: dict[str, Any], b: dict[str, Any]) -> int:
    """How many axes two extracted axis-dicts differ on (both present and unequal). A None on either side
    is 'no evidence', not a difference, so a data gap never inflates distinctiveness."""
    n = 0
    for k in TWIN_AXES:
        av, bv = a.get(k), b.get(k)
        if av is None or bv is None:
            continue
        if av != bv:
            n += 1
    return n


def twin_report(manifests: Sequence[Manifest]) -> list[dict[str, Any]]:
    """For every pair of villages that SHARE a water direction, report how many structural axes differ and
    whether the pair reads as distinct. Verdict 'TWINNED' (too similar) when fewer than TWIN_MIN_DIFF axes
    differ, else 'PASS'. Non-village manifests (no down_deg) are skipped. This is a pool-level tool run
    alongside - not inside - the per-map gate()."""
    named = [(str(M.get("meta", {}).get("name", i)), M) for i, M in enumerate(manifests)]
    axes = {name: twin_axes(M) for name, M in named}
    out: list[dict[str, Any]] = []
    for i in range(len(named)):
        for j in range(i + 1, len(named)):
            na, Ma = named[i]
            nb, Mb = named[j]
            da, db = Ma.get("meta", {}).get("down_deg"), Mb.get("meta", {}).get("down_deg")
            if da is None or db is None or da != db:
                continue  # only same-water-direction pairs are compared
            diff = twin_diff_count(axes[na], axes[nb])
            out.append({"pair": (na, nb), "down_deg": da, "diffs": diff, "verdict": "PASS" if diff >= TWIN_MIN_DIFF else "TWINNED"})
    return out


def main(path: str) -> int:
    return 1 if gate(load(path)) else 0


if __name__ == "__main__":
    import os

    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(here, "pool", "villages", "kikuta-village.json")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = args[0] if args else default
    if "--capacity" in sys.argv[1:]:
        import json as _json

        want_map = "--capacity-map" in sys.argv[1:]
        with open(path) as _cf:
            rep = city_capacity(_json.load(_cf), grid_step=40 if want_map else None)
        if rep is None:
            print("no capacity report (not a walled city with a declared population)")
        else:
            _action = {"sized_and_packed": "sized and packed - done", "densify": "add dwellings (wall is right)", "enlarge": "ENLARGE the wall", "shrink": "SHRINK the wall"}
            print(f"WALL CAPACITY: {rep['verdict'].upper()} -> {_action.get(rep['verdict'], '')}")
            print(f"  target {rep['target_dwellings']} dwellings, placed IN-WALL {rep['placed']}, INHERENT capacity (well-packed) {rep['inherent_capacity']}")
            print(
                f"  ring {rep['ring_area']}px^2: residential-capable {rep['res_capable_area']}, civic {rep['civic_area']}, reserve {rep['reserve_area']} (reserve frac {rep['reserve_frac']}, cap {RESERVE_CAP_FRAC})"
            )
            print(f"  suggested wall scale x{rep['suggested_wall_scale']} (>1 enlarge, <1 shrink)")
            for pq in rep.get("per_quarter", []):
                _band = "" if QUARTER_DENSITY_FLOOR <= pq["density"] <= QUARTER_DENSITY_CEIL else "  <-- OUT OF BAND"
                print(f"  quarter {str(pq['name']):>22} [{pq['zone']:11}] {pq['dwellings']:3d} dwellings, density {pq['density'] * 1000:.2f}/1000px^2{_band}")
            if rep.get("grid"):
                ox, oy = rep["grid_origin"]
                print(f"  interior map (D dwell / C civic / ~ water / # trunk / + res-street / F field / . OPEN); each cell {rep['grid_step']}px, origin ({ox},{oy}):")
                for j, row in enumerate(rep["grid"]):
                    print(f"    {oy + j * rep['grid_step']:>5} {row}")
        sys.exit(0)
    sys.exit(main(path))
