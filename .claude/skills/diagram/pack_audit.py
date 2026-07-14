#!/usr/bin/env python3
"""pack_audit.py - packing / whitespace report for a Mode A compound plan.

Read-only. Parses a hand-authored compound SVG and reports the numbers that make
"is there too much empty space?" objective, WITHOUT the misleading ones:

  - building-COVERAGE % of the walled interior (the historical anchor; a jin'ya
    runs ~37-42% built, the rest intentional courtyard - see buildings.md
    grounding "Packing: a jin'ya is mostly open..."). Coverage, NOT "total empty
    %", is the realism signal: a courtyard compound is SUPPOSED to be mostly open.
  - the TOP-N genuinely-vacant rectangles (+ orientation + location): the real
    "a whole region sits empty" signal. Reporting only the single largest hid a
    big secondary void behind the legitimate forecourt (GM caught this, 2026-07),
    so the report lists several - each judged forecourt-feature vs slack.
  - PER-REGION density: the interior tiled into a grid, so a locally-sparse
    quadrant is visible even when the GLOBAL coverage is comfortably in-band
    (a compound can be 37% overall while one quarter is ~68% empty).
  - ALIGNED BUILDING GAPS: pairs of buildings stacked on a shared edge with empty
    ground between them. A ~6 ft fire-gap around a plaster KURA is correct; a
    12-16 ft gap between ordinary wooden service buildings is loose slack.

"Empty %" and "largest empty CONNECTED region" are deliberately NOT the headline
numbers: the open ground is one connected blob (courtyard network), so a
connected-component count is degenerate, and a high open % is expected, not a
defect. Coverage + top-N vacant RECTANGLES + per-region density + aligned gaps
are the actionable set.

Usage:  python3 pack_audit.py pool/<subject>.svg [more.svg ...]
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass

FTPX: float = 3.0  # 3 px = 1 ft
INTERIOR_FILL = "url(#court-earth)"
BUILDING_FILLS: frozenset[str] = frozenset({"#DDB87A", "#C9A57A", "#E8D2A8", "#F2EFE4", "#C9876C", "#B89868", "#8C6F3E", "#6B4030"})
BUILDING_PATTERNS: frozenset[str] = frozenset({"url(#granary-slats)", "url(#colonnade-hatch)"})
KURA_FILLS: frozenset[str] = frozenset({"#F2EFE4"})  # fireproof plaster kura: a fire-gap IS correct
OPEN_PATTERNS: frozenset[str] = frozenset({"url(#garden-stipple)", "url(#oshirasu-sand)"})
MIN_BLDG_AREA_PX: float = 900.0  # 100 sqft; below this it is furniture, not a building mass

_RECT_RE = re.compile(r'<rect x="([\-\d.]+)" y="([\-\d.]+)" width="([\d.]+)" height="([\d.]+)"[^>]*?fill="([^"]+)"')
_CIRCLE_RE = re.compile(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)"')
_ELLIPSE_RE = re.compile(r'<ellipse cx="([\d.]+)" cy="([\d.]+)" rx="([\d.]+)" ry="([\d.]+)"')

Grid = list[list[bool]]


@dataclass(frozen=True)
class Rect:
    """An axis-aligned rectangle in SVG pixel space."""

    x: float
    y: float
    w: float
    h: float
    fill: str = ""

    @property
    def x2(self) -> float:
        return self.x + self.w

    @property
    def y2(self) -> float:
        return self.y + self.h

    @property
    def area_px(self) -> float:
        return self.w * self.h

    @property
    def is_kura(self) -> bool:
        return self.fill in KURA_FILLS


@dataclass(frozen=True)
class ParsedPlan:
    """Classified geometry of one compound plan."""

    interior: tuple[Rect, ...]
    buildings: tuple[Rect, ...]
    open_features: tuple[Rect, ...]
    glyphs: tuple[Rect, ...]

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        minx = min(r.x for r in self.interior)
        miny = min(r.y for r in self.interior)
        maxx = max(r.x2 for r in self.interior)
        maxy = max(r.y2 for r in self.interior)
        return minx, miny, maxx, maxy


@dataclass(frozen=True)
class VacantRect:
    """A maximal empty rectangle, sized in feet with its SVG-pixel top-left."""

    w_ft: float
    h_ft: float
    area_sqft: float
    x: float
    y: float

    @property
    def orient(self) -> str:
        return "horizontal" if self.w_ft >= self.h_ft else "vertical"


@dataclass(frozen=True)
class Gap:
    """An empty gap (ft) between two buildings stacked on a shared edge."""

    ft: float
    orient: str
    mx: float
    my: float
    kura: bool


@dataclass(frozen=True)
class RegionTile:
    """Building coverage within one tile of the interior grid."""

    row: int
    col: int
    coverage_pct: float
    interior_sqft: float


def parse_svg(text: str) -> ParsedPlan:
    """Parse an SVG into interior / building / open-feature / point-glyph rects."""
    rects = [Rect(float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)), m.group(5)) for m in _RECT_RE.finditer(text)]
    interior = tuple(r for r in rects if r.fill == INTERIOR_FILL)
    if not interior:
        raise ValueError("no court-earth interior rect found in the SVG")
    buildings = tuple(r for r in rects if (r.fill in BUILDING_FILLS or r.fill in BUILDING_PATTERNS) and r.area_px >= MIN_BLDG_AREA_PX)
    open_features = tuple(r for r in rects if r.fill in OPEN_PATTERNS)
    glyphs: list[Rect] = []
    for c in _CIRCLE_RE.finditer(text):
        cx, cy, rad = float(c.group(1)), float(c.group(2)), float(c.group(3))
        if rad >= 4.0:
            glyphs.append(Rect(cx - rad, cy - rad, 2 * rad, 2 * rad))
    for e in _ELLIPSE_RE.finditer(text):
        ex, ey, rx, ry = float(e.group(1)), float(e.group(2)), float(e.group(3)), float(e.group(4))
        glyphs.append(Rect(ex - rx, ey - ry, 2 * rx, 2 * ry))
    return ParsedPlan(interior, buildings, open_features, tuple(glyphs))


def _blank(w: int, h: int) -> Grid:
    return [[False] * w for _ in range(h)]


def _paint(mask: Grid, r: Rect, cell: int, minx: float, miny: float, w: int, h: int) -> None:
    gy0 = max(0, int((r.y - miny) // cell))
    gy1 = min(h, int((r.y2 - miny) // cell) + 1)
    gx0 = max(0, int((r.x - minx) // cell))
    gx1 = min(w, int((r.x2 - minx) // cell) + 1)
    for gy in range(gy0, gy1):
        row = mask[gy]
        for gx in range(gx0, gx1):
            row[gx] = True


@dataclass(frozen=True)
class _Grids:
    inside: Grid
    building: Grid
    occ: Grid
    w: int
    h: int
    minx: float
    miny: float
    cell: int


def _grids(plan: ParsedPlan, cell: int) -> _Grids:
    minx, miny, maxx, maxy = plan.bounds
    w = max(1, int((maxx - minx) // cell) + 1)
    h = max(1, int((maxy - miny) // cell) + 1)
    inside = _blank(w, h)
    building = _blank(w, h)
    occ = _blank(w, h)
    for r in plan.interior:
        _paint(inside, r, cell, minx, miny, w, h)
    for r in plan.buildings:
        _paint(building, r, cell, minx, miny, w, h)
        _paint(occ, r, cell, minx, miny, w, h)
    for r in plan.open_features:
        _paint(occ, r, cell, minx, miny, w, h)
    for r in plan.glyphs:
        _paint(occ, r, cell, minx, miny, w, h)
    return _Grids(inside, building, occ, w, h, minx, miny, cell)


def coverage(plan: ParsedPlan, cell: int = 2) -> float:
    """Building footprint as a fraction (0..1) of the walled interior."""
    g = _grids(plan, cell)
    inside_cells = 0
    built_cells = 0
    for gy in range(g.h):
        for gx in range(g.w):
            if g.inside[gy][gx]:
                inside_cells += 1
                if g.building[gy][gx]:
                    built_cells += 1
    return built_cells / inside_cells


def _max_rect(mask: Grid, w: int, h: int) -> tuple[int, int, int, int, int]:
    """Largest all-True axis-aligned rectangle: (area, left, top, width, height) in cells."""
    heights = [0] * w
    best = (0, 0, 0, 0, 0)
    for y in range(h):
        row = mask[y]
        for x in range(w):
            heights[x] = heights[x] + 1 if row[x] else 0
        stack: list[int] = []
        x = 0
        while x <= w:
            cur = heights[x] if x < w else 0
            if not stack or cur >= heights[stack[-1]]:
                stack.append(x)
                x += 1
            else:
                top = stack.pop()
                width = x if not stack else x - stack[-1] - 1
                area = heights[top] * width
                if area > best[0]:
                    left = stack[-1] + 1 if stack else 0
                    best = (area, left, y - heights[top] + 1, width, heights[top])
    return best


def top_vacant_rects(plan: ParsedPlan, n: int = 3, cell: int = 2, min_area_sqft: float = 150.0) -> list[VacantRect]:
    """The n largest non-overlapping empty rectangles, largest first (greedy)."""
    g = _grids(plan, cell)
    vacant: Grid = [[g.inside[gy][gx] and not g.occ[gy][gx] for gx in range(g.w)] for gy in range(g.h)]
    floor_px = min_area_sqft * FTPX * FTPX
    out: list[VacantRect] = []
    for _ in range(n):
        area_cells, gx0, gy0, wc, hc = _max_rect(vacant, g.w, g.h)
        if area_cells * cell * cell < floor_px:
            break
        out.append(
            VacantRect(
                w_ft=wc * cell / FTPX,
                h_ft=hc * cell / FTPX,
                area_sqft=round(area_cells * cell * cell / (FTPX * FTPX)),
                x=gx0 * cell + g.minx,
                y=gy0 * cell + g.miny,
            )
        )
        for yy in range(gy0, gy0 + hc):
            for xx in range(gx0, gx0 + wc):
                vacant[yy][xx] = False
    return out


def region_density(plan: ParsedPlan, rows: int = 3, cols: int = 3, cell: int = 2) -> list[RegionTile]:
    """Per-tile building coverage over the interior (exposes local sparsity)."""
    g = _grids(plan, cell)
    tiles: list[RegionTile] = []
    for row in range(rows):
        gy0, gy1 = row * g.h // rows, (row + 1) * g.h // rows
        for col in range(cols):
            gx0, gx1 = col * g.w // cols, (col + 1) * g.w // cols
            inside_cells = 0
            built_cells = 0
            for gy in range(gy0, gy1):
                for gx in range(gx0, gx1):
                    if g.inside[gy][gx]:
                        inside_cells += 1
                        if g.building[gy][gx]:
                            built_cells += 1
            pct = built_cells / inside_cells if inside_cells else 0.0
            tiles.append(RegionTile(row, col, pct, round(inside_cells * cell * cell / (FTPX * FTPX))))
    return tiles


def _blocked(
    buildings: tuple[Rect, ...],
    i: int,
    j: int,
    lo: float,
    hi: float,
    near: float,
    far: float,
    *,
    vert: bool,
) -> bool:
    for k, r in enumerate(buildings):
        if k in (i, j):
            continue
        if vert and r.x < hi and r.x2 > lo and r.y < far and r.y2 > near:
            return True
        if not vert and r.y < hi and r.y2 > lo and r.x < far and r.x2 > near:
            return True
    return False


def aligned_gaps(plan: ParsedPlan) -> list[Gap]:
    """Empty gaps (5-30 ft) between buildings stacked on a shared edge, largest first."""
    b = plan.buildings
    raw: list[Gap] = []
    for i, a in enumerate(b):
        for j, c in enumerate(b):
            if i == j:
                continue
            ox = min(a.x2, c.x2) - max(a.x, c.x)
            if ox >= 30 and c.y >= a.y2 and 15 <= (c.y - a.y2) <= 90:
                xl, xr = max(a.x, c.x), min(a.x2, c.x2)
                if not _blocked(b, i, j, xl, xr, a.y2, c.y, vert=True):
                    raw.append(
                        Gap(
                            (c.y - a.y2) / FTPX,
                            "V",
                            (xl + xr) / 2,
                            (a.y2 + c.y) / 2,
                            a.is_kura or c.is_kura,
                        )
                    )
            oy = min(a.y2, c.y2) - max(a.y, c.y)
            if oy >= 30 and c.x >= a.x2 and 15 <= (c.x - a.x2) <= 90:
                yl, yr = max(a.y, c.y), min(a.y2, c.y2)
                if not _blocked(b, i, j, a.x2, c.x, yl, yr, vert=False):
                    raw.append(
                        Gap(
                            (c.x - a.x2) / FTPX,
                            "H",
                            (a.x2 + c.x) / 2,
                            (yl + yr) / 2,
                            a.is_kura or c.is_kura,
                        )
                    )
    raw.sort(key=lambda gp: gp.ft, reverse=True)
    out: list[Gap] = []
    for gp in raw:
        if not any(abs(gp.mx - o.mx) < 15 and abs(gp.my - o.my) < 15 for o in out):
            out.append(gp)
    return out


def gap_tag(gap: Gap) -> str:
    """Heuristic label for an aligned gap (a kura keeps a fire-gap; wooden slack tightens)."""
    if gap.kura:
        return "fire-gap OK (kura)" if gap.ft <= 10 else "LOOSE (kura gap >10 ft)"
    return "tight" if gap.ft <= 8 else "LOOSE (wooden >8 ft)"


def format_report(plan: ParsedPlan, cell: int = 2) -> str:
    """Human-readable packing report (the CLI prints this; pure so it is testable)."""
    g = _grids(plan, cell)
    inside = built = openc = empty = 0
    for gy in range(g.h):
        for gx in range(g.w):
            if not g.inside[gy][gx]:
                continue
            inside += 1
            if g.building[gy][gx]:
                built += 1
            elif g.occ[gy][gx]:
                openc += 1
            else:
                empty += 1
    minx, miny, maxx, maxy = plan.bounds
    lines = [
        f"walled interior: {(maxx - minx) / FTPX:.0f} x {(maxy - miny) / FTPX:.0f} ft = {inside * cell * cell / (FTPX * FTPX):,.0f} sqft",
        f"building coverage: {100 * built / inside:.0f}%  (jin'ya band 37-42%)",
        f"purposeful open (garden/court/glyphs): {100 * openc / inside:.0f}%  (features)",
        f"bare open ground: {100 * empty / inside:.0f}%  (courts are open - not a defect alone)",
        "top vacant rectangles (largest first - forecourt/oshirasu FEATURE, or slack?):",
    ]
    tv = top_vacant_rects(plan, n=4, cell=cell)
    if not tv:
        lines.append("    (none above the floor area)")
    lines += [f"    {v.w_ft:.0f} x {v.h_ft:.0f} ft = {v.area_sqft:,.0f} sqft [{v.orient}] at svg({v.x:.0f},{v.y:.0f})" for v in tv]
    lines.append("per-region density (a large low-coverage tile = consolidation candidate):")
    lines += [f"    tile[r{t.row}c{t.col}]: {100 * t.coverage_pct:.0f}% built  ({t.interior_sqft:,.0f} sqft interior)" for t in region_density(plan, cell=cell)]
    lines.append("aligned building gaps 5-30 ft (kura fire-gap OK ~10 ft; wooden >8 ft loose):")
    gaps = aligned_gaps(plan)
    if not gaps:
        lines.append("    (none in the 5-30 ft range)")
    lines += [f"    {gp.ft:.1f} ft  {gp.orient}  at svg({gp.mx:.0f},{gp.my:.0f})   {gap_tag(gp)}" for gp in gaps[:12]]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("usage: pack_audit.py <compound.svg> [more.svg ...]", file=sys.stderr)
        return 2
    for path in args:
        with open(path, encoding="utf-8") as fh:
            plan = parse_svg(fh.read())
        print(f"=== {path.split('/')[-1]} ===")
        print(format_report(plan))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
