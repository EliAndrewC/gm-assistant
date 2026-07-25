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
  - STRUCTURES ON WALLS: a footprint drawn across the INK of a compound wall or a
    court divider. A wall is a built object with real thickness, so a structure
    either abuts it or stands clear - it can never occupy the same ground.

"Empty %" and "largest empty CONNECTED region" are deliberately NOT the headline
numbers: the open ground is one connected blob (courtyard network), so a
connected-component count is degenerate, and a high open % is expected, not a
defect. Coverage + top-N vacant RECTANGLES + per-region density + aligned gaps
are the actionable set.

Usage:  python3 pack_audit.py pool/<subject>.svg [more.svg ...]
"""

from __future__ import annotations

import math
import re
import sys
from dataclasses import dataclass

FTPX: float = 3.0  # 3 px = 1 ft
INTERIOR_FILL = "url(#court-earth)"
BUILDING_FILLS: frozenset[str] = frozenset({"#DDB87A", "#C9A57A", "#E8D2A8", "#F2EFE4", "#C9876C", "#B89868", "#8C6F3E", "#6B4030"})
BUILDING_PATTERNS: frozenset[str] = frozenset({"url(#granary-slats)", "url(#colonnade-hatch)"})
KURA_FILLS: frozenset[str] = frozenset({"#F2EFE4"})  # fireproof plaster kura: a fire-gap IS correct
OPEN_PATTERNS: frozenset[str] = frozenset({"url(#garden-stipple)", "url(#oshirasu-sand)", "url(#keiko-earth)"})
MIN_BLDG_AREA_PX: float = 500.0  # ~55 sqft; below this it is furniture, not a building mass. Lowered
# from 900 (2026-07-21): the glyph-doctrine retirement shrank real buildings to TRUE size - an 11x7 ft
# modest shrine is 693 px2 - and the old floor silently dropped them from coverage/adjacency, emitting
# a false "fire tub adrift" on Hayakawa (the tub sits 1.8 ft off the shrine the tool stopped seeing).

_RECT_RE = re.compile(r'<rect x="([\-\d.]+)" y="([\-\d.]+)" width="([\d.]+)" height="([\d.]+)"[^>]*?fill="([^"]+)"')
_CIRCLE_RE = re.compile(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)"')
_ELLIPSE_RE = re.compile(r'<ellipse cx="([\d.]+)" cy="([\d.]+)" rx="([\d.]+)" ry="([\d.]+)"')
DIVIDER_STROKE = "#3F3A30"  # internal court-divider wall; buildings legitimately back it, so it
# counts as a "wall" for perimeter-hugging (a jin'ya's office hall backs the divider).
_DIV_GROUP_RE = re.compile(rf'<g stroke="{re.escape(DIVIDER_STROKE)}"[^>]*>(.*?)</g>', re.DOTALL)
_LINE_RE = re.compile(r'<line x1="([\-\d.]+)" y1="([\-\d.]+)" x2="([\-\d.]+)" y2="([\-\d.]+)"')
FIRE_WATER_FILL = "#8FB0C6"  # tensuioke (rain-water fire tubs). They are GUTTER-FED by roof runoff,
# so each must sit at a building's wall/eaves; a tub standing out in the open court is fed by nothing.
_TUB_GROUP_RE = re.compile(rf'<g fill="{re.escape(FIRE_WATER_FILL)}"[^>]*>(.*?)</g>', re.DOTALL)
TUB_MAX_GAP_FT: float = 3.5  # a wall-hugging tub sits ~1.7-2 ft from a wall (its own radius + eaves);
# beyond this it is adrift in the court with no roof draining into it.
TUB_WELL_MIN_PX: float = 1.0  # a fire-water tub overlapping a well glyph by more than this sits ON it

# --- text labels (for the layer/legibility/proximity checks) ---
_TEXT_RE = re.compile(r"<text\s([^>]*)>(.*?)</text>", re.DOTALL)
_ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')
_INNER_TAG_RE = re.compile(r"<[^>]*>")
CHAR_W_FRAC: float = 0.55  # a serif glyph's advance width as a fraction of font-size (bbox estimate)
CHAR_W_BOLD: float = 0.72  # bold ALL-CAPS band labels (RESIDENCE, HEARING COURT) run widest
CHAR_W_BOLD_MIXED: float = 0.60  # ...but mixed-case bold (building names) is much narrower than caps.
# Measured 2026-07-25 by rendering real pool strings through resvg/DejaVu Serif and reading the ink
# extents: at 0.72 the all-caps band labels land at 0.95-0.99x of true width (right), while
# mixed-case bold came out 1.26-1.27x (way over). That 26% phantom width was enough to make the
# widened occlusion check report a FALSE positive on Ochiba - "Tatsuya's quarters" was estimated to
# run into the residence's connecting corridor when the real ink stops 7 px short of it. 0.60 lands
# mixed-case at 0.96-1.06x: still biased slightly LONG, which is the safe direction for a check that
# is looking for overlaps.
CAPS_RATIO: float = 0.8  # a label with >= this share of upper-case letters is a caps label
WELL_FILL = "#9C8C70"  # well-curb stone
WALL_STROKE = "#2D2A24"  # the compound wall (and gate posts / well-mouths share this dark ink)
_WALL_GROUP_RE = re.compile(rf'<g stroke="{re.escape(WALL_STROKE)}"[^>]*>(.*?)</g>', re.DOTALL)
# Fills dark enough that BLACK label ink laid over them stops being legible (luminance < ~0.30):
DARK_FILLS: frozenset[str] = frozenset({"#2D2A24", "#3A2010", "#3A2418", "#1A1410", "#4A3318", "#5C0A04", "#3A2E1C", "#6B4030", "#5A3F1E", "#5C1A0A"})
LABEL_DARK_LUMA: float = 0.42  # a label whose own fill is darker than this is "black ink" for legibility
MIN_DARK_AREA_PX: float = 150.0  # ignore tiny dark markers (kura door, altar square) - only a real dark BLOCK or wall hurts legibility
DARK_MIN_OVERLAP_PX: float = 2.5  # a label must sit ON a dark feature by at least this much (not just graze an edge)
OCCLUSION_MIN_PX: float = 3.0  # a later feature must cover at least this much of a foreground item to count
# The occlusion check is deliberately fill-BLIND on the occluder side: ANY rect or glyph drawn later
# counts, not just the fills this tool happens to classify as a building or a garden. Enumerating
# occluders by fill is what let two real defects through (2026-07-25) - a note box (an unclassified
# solid fill) painted over the bounty bill, and a NEW pattern (url(#cart-gravel), unknown to
# OPEN_PATTERNS) painted over a privy. A palette grows; "drawn later, covers it" does not.
FURNITURE_MAX_AREA_PX: float = MIN_BLDG_AREA_PX  # a rect below the building floor is furniture
# (privy, door, board, hearth, stilt, mat) - foreground that belongs ABOVE the fills, like a label.
GROUP_LABEL_GLYPHS: dict[str, str] = {"fire-water tub": "tub", "well": "well"}  # label text -> glyph kind it names
GROUP_LABEL_MAX_FT: float = 9.0  # a glyph-group label must sit within this of a glyph it names
NOTICE_BOARD_MAX_FT: float = 20.0  # a notice board must sit within this of a gate opening to be read
OPENING_MAX_PX: float = 80.0  # a wider gap in the wall is a structural break (a wall drawn around a
# building that IS part of it), not a gate - see `wall_openings`
NUDGE_STEP_PX: float = 4.0
NUDGE_MAX_PX: float = 40.0  # search radius for a legibility-clearing nudge
LABEL_OVERLAP_MIN_PX: float = 3.0  # two labels overlapping by more than this collide/smear
DOOR_MAX_AREA_PX: float = 250.0  # a door glyph is small (a kura door); bigger dark rects are hearths/blocks
DOOR_FLUSH_TOL_PX: float = 1.5  # a door within this of a building edge reads as ON the wall
DOOR_NEAR_PX: float = 12.0  # a door candidate this close to an edge is TRYING to be in the wall (vs a deep interior marker)

# --- structures vs wall ink (a structure may ABUT a wall, never occupy it) ---
# Every roofed/built footprint color, with NO area floor: the motivating defect was a 26x8 px
# ENTRY PORCH laid across Ochiba's court divider (GM caught it, 2026-07-24), and the
# MIN_BLDG_AREA_PX floor that keeps furniture out of the coverage math would have hidden it.
# Porches, sheds and privies are small but they are still built things standing on the ground.
UTILITY_FILLS: frozenset[str] = frozenset({"#7E726A", WELL_FILL})  # privies/sheds + well curbs
STRUCTURE_FILLS: frozenset[str] = BUILDING_FILLS | BUILDING_PATTERNS | UTILITY_FILLS
# Why UTILITY_FILLS had to be added (2026-07-25): the comment above already said privies count, but
# the fill list did not contain the privy color, so all 23 utility rects in the pool went
# unchecked - documented intent and implementation had silently drifted apart.
#
# And why this list stays ENUMERATED, where the occlusion check went deliberately fill-blind: the
# two rules have opposite defaults. NOTHING may legitimately bury a foreground item, so there the
# safe rule is "any later shape counts". But plenty of things legitimately occupy wall ink - gate
# posts flank an opening, threshold and boundary stones mark a crossing, salt wards flank a door -
# so "anything that is not ground" would flag every one of them. A structure is a ROOFED, standing
# thing, and that has to be named rather than inferred.
WALL_KIND: dict[str, str] = {WALL_STROKE: "compound wall", DIVIDER_STROKE: "court divider"}
WALL_OVERLAP_MIN_PX: float = 0.5  # sub-pixel contact is a flush abutment + integer-emit rounding,
# not a structure standing in the masonry. The pool's tightest LEGITIMATE clearance is 0.5 px
# (Hayakawa's south-wall stables/gatehouse row) and the smallest real defect found was 3 px, so
# this threshold has ~1 px of margin on the passing side and 6x on the failing side.

Grid = list[list[bool]]


@dataclass(frozen=True)
class Rect:
    """An axis-aligned rectangle in SVG pixel space."""

    x: float
    y: float
    w: float
    h: float
    fill: str = ""
    pos: int = -1  # byte offset in the source SVG (document/draw order; higher = drawn later, on top)

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
class Label:
    """A text label with an ESTIMATED bounding box (px) and its draw-order position."""

    x: float  # bbox top-left
    y: float
    w: float
    h: float
    fill: str
    text: str
    pos: int  # byte offset in the source SVG (draw order)

    @property
    def x2(self) -> float:
        return self.x + self.w

    @property
    def y2(self) -> float:
        return self.y + self.h

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2


def _luma(fill: str) -> float:
    """Relative luminance (0=black, 1=white) of a #rrggbb fill; 1.0 for anything non-hex."""
    if not (len(fill) == 7 and fill.startswith("#")):
        return 1.0
    r, g, b = (int(fill[i : i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


@dataclass(frozen=True)
class ParsedPlan:
    """Classified geometry of one compound plan."""

    interior: tuple[Rect, ...]
    buildings: tuple[Rect, ...]
    open_features: tuple[Rect, ...]
    glyphs: tuple[Rect, ...]
    dividers: tuple[Rect, ...] = ()  # internal divider walls, as thin rects
    tubs: tuple[Rect, ...] = ()  # fire-water tubs (bbox of each), to check wall-adjacency
    labels: tuple[Label, ...] = ()  # text labels with estimated bboxes + draw order
    wall_segs: tuple[Rect, ...] = ()  # compound-wall line segments (thin rects), for gate openings
    wells: tuple[Rect, ...] = ()  # well-curb rects, for the 'well' group-label proximity check
    dark_rects: tuple[Rect, ...] = ()  # dark-filled rects, for the black-on-black legibility check
    door_rects: tuple[Rect, ...] = ()  # small dark rects (door glyphs), for the door-on-a-wall check
    wall_bands: tuple[Rect, ...] = ()  # the INKED band of each wall/divider stroke (`fill` = its stroke color)
    structures: tuple[Rect, ...] = ()  # every built footprint, NO area floor (porches/sheds count)
    fills: tuple[Rect, ...] = ()  # every drawn rect (any fill) - the fill-blind occluder set
    furniture: tuple[Rect, ...] = ()  # sub-building rects (privy, door, board, mat): foreground

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
    zone: str = "central"  # "central" (courtyard) or "perimeter" (gap in the wall ring)

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


@dataclass(frozen=True)
class TubAdrift:
    """A fire-water tub sitting too far from any building to be gutter-fed."""

    x: float  # tub center, SVG px
    y: float
    gap_ft: float  # distance from tub center to the nearest building


def _bold_char_w(text: str) -> float:
    """Per-character advance for BOLD text: caps labels run wider than mixed-case ones."""
    letters = [c for c in text if c.isalpha()]
    caps = sum(c.isupper() for c in letters) / len(letters) if letters else 0.0
    return CHAR_W_BOLD if caps >= CAPS_RATIO else CHAR_W_BOLD_MIXED


def _parse_labels(text: str) -> list[Label]:
    """Text labels with an estimated bbox (from font-size x string length) + draw-order pos."""
    out: list[Label] = []
    for m in _TEXT_RE.finditer(text):
        attrs = dict(_ATTR_RE.findall(m.group(1)))
        content = _INNER_TAG_RE.sub("", m.group(2)).replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").strip()
        if not content or "x" not in attrs or "y" not in attrs:
            continue
        x, y = float(attrs["x"]), float(attrs["y"])
        fs = float(attrs.get("font-size", "13"))
        ls = float(attrs.get("letter-spacing", "0"))
        n = len(content)
        frac = _bold_char_w(content) if attrs.get("font-weight") == "bold" else CHAR_W_FRAC
        w = n * fs * frac + ls * max(n - 1, 0)
        anchor = attrs.get("text-anchor", "start")
        left = x - w / 2 if anchor == "middle" else (x - w if anchor == "end" else x)
        out.append(Label(left, y - fs * 0.78, w, fs, attrs.get("fill", "#000000"), content, m.start()))
    return out


_ELEM_RE = re.compile(r"<(/?)(g|line)\b([^>]*?)/?>")


def _wall_bands(text: str) -> list[Rect]:
    """The INKED band of every wall / court-divider stroke, as an axis-aligned rect.

    Handles both authoring forms present in the pool - a `<g stroke=... stroke-width=...>`
    wrapping bare `<line>`s (the hand-authored plans) and stand-alone `<line stroke=...
    stroke-width=.../>` (compound.py's emitter) - by tracking `<g>` attribute inheritance, so a
    plan drawn either way is checked rather than silently skipped.

    Parsed separately from `wall_segs` on purpose: those stay CENTERLINE segments because
    `_gate_openings` measures the gaps BETWEEN them, and widening them by the stroke would shrink
    every measured opening by a stroke width. `fill` carries the stroke color so the report can
    name which barrier was hit. Mode A walls are axis-aligned, so a run is classified by its
    longer axis; a `stroke-linecap="square"` run also inks half a stroke past each endpoint.
    """
    stack: list[dict[str, str]] = []
    out: list[Rect] = []
    for m in _ELEM_RE.finditer(text):
        closing, name, attrs = m.group(1), m.group(2), m.group(3)
        if name == "g":
            if not closing:
                stack.append(dict(_ATTR_RE.findall(attrs)))
            elif stack:
                stack.pop()
            continue
        d: dict[str, str] = {}
        for frame in stack:
            d.update(frame)
        d.update(dict(_ATTR_RE.findall(attrs)))
        stroke = d.get("stroke", "")
        if stroke not in WALL_KIND or "x1" not in d:
            continue
        sw = float(d.get("stroke-width", "1"))
        hw = sw / 2
        cap = hw if d.get("stroke-linecap") == "square" else 0.0
        x1, y1, x2, y2 = (float(d[k]) for k in ("x1", "y1", "x2", "y2"))
        if abs(y2 - y1) <= abs(x2 - x1):  # horizontal run
            out.append(Rect(min(x1, x2) - cap, min(y1, y2) - hw, abs(x2 - x1) + 2 * cap, sw, stroke, m.start()))
        else:
            out.append(Rect(min(x1, x2) - hw, min(y1, y2) - cap, sw, abs(y2 - y1) + 2 * cap, stroke, m.start()))
    return out


def parse_svg(text: str) -> ParsedPlan:
    """Parse an SVG into interior / building / open-feature / point-glyph rects + labels + walls."""
    rects = [Rect(float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)), m.group(5), m.start()) for m in _RECT_RE.finditer(text)]
    interior = tuple(r for r in rects if r.fill == INTERIOR_FILL)
    if not interior:
        raise ValueError("no court-earth interior rect found in the SVG")
    buildings = tuple(r for r in rects if (r.fill in BUILDING_FILLS or r.fill in BUILDING_PATTERNS) and r.area_px >= MIN_BLDG_AREA_PX)
    open_features = tuple(r for r in rects if r.fill in OPEN_PATTERNS)
    glyphs: list[Rect] = []
    for c in _CIRCLE_RE.finditer(text):
        cx, cy, rad = float(c.group(1)), float(c.group(2)), float(c.group(3))
        if rad >= 4.0:
            glyphs.append(Rect(cx - rad, cy - rad, 2 * rad, 2 * rad, "", c.start()))
    for e in _ELLIPSE_RE.finditer(text):
        ex, ey, rx, ry = float(e.group(1)), float(e.group(2)), float(e.group(3)), float(e.group(4))
        glyphs.append(Rect(ex - rx, ey - ry, 2 * rx, 2 * ry, "", e.start()))
    dividers: list[Rect] = []
    for grp in _DIV_GROUP_RE.finditer(text):
        for ln in _LINE_RE.finditer(grp.group(1)):
            x1, y1, x2, y2 = (float(ln.group(i)) for i in range(1, 5))
            dividers.append(Rect(min(x1, x2), min(y1, y2), max(abs(x2 - x1), 2.0), max(abs(y2 - y1), 2.0)))
    tubs: list[Rect] = []
    for grp in _TUB_GROUP_RE.finditer(text):
        for c in _CIRCLE_RE.finditer(grp.group(1)):
            cx, cy, rad = float(c.group(1)), float(c.group(2)), float(c.group(3))
            tubs.append(Rect(cx - rad, cy - rad, 2 * rad, 2 * rad, FIRE_WATER_FILL, grp.start() + c.start()))
    wall_segs: list[Rect] = []
    for grp in _WALL_GROUP_RE.finditer(text):
        for ln in _LINE_RE.finditer(grp.group(1)):
            x1, y1, x2, y2 = (float(ln.group(i)) for i in range(1, 5))
            wall_segs.append(Rect(min(x1, x2), min(y1, y2), max(abs(x2 - x1), 2.0), max(abs(y2 - y1), 2.0)))
    wells = tuple(r for r in rects if r.fill == WELL_FILL)
    fills = tuple(r for r in rects if r.fill != INTERIOR_FILL)
    furniture = tuple(r for r in fills if r.area_px < FURNITURE_MAX_AREA_PX)
    dark_rects = tuple(r for r in rects if r.fill in DARK_FILLS and r.area_px >= MIN_DARK_AREA_PX)
    door_rects = tuple(r for r in rects if r.fill in DARK_FILLS and r.area_px < DOOR_MAX_AREA_PX)
    return ParsedPlan(
        interior,
        buildings,
        open_features,
        tuple(glyphs),
        tuple(dividers),
        tuple(tubs),
        tuple(_parse_labels(text)),
        tuple(wall_segs),
        wells,
        dark_rects,
        door_rects,
        tuple(_wall_bands(text)),
        tuple(r for r in rects if r.fill in STRUCTURE_FILLS),
        fills=fills,
        furniture=furniture,
    )


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
    divider: Grid
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
    divider = _blank(w, h)
    for r in plan.dividers:
        _paint(divider, r, cell, minx, miny, w, h)
    return _Grids(inside, building, occ, divider, w, h, minx, miny, cell)


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


def _perimeter_band(g: _Grids, depth_cells: int) -> Grid:
    """Inside cells within depth_cells of the interior edge (a wall), by cardinal rays."""
    band = _blank(g.w, g.h)
    for gy in range(g.h):
        for gx in range(g.w):
            if not g.inside[gy][gx]:
                continue
            near = False
            for d in range(1, depth_cells + 1):
                for ny, nx in ((gy - d, gx), (gy + d, gx), (gy, gx - d), (gy, gx + d)):
                    if not (0 <= ny < g.h and 0 <= nx < g.w) or not g.inside[ny][nx] or g.divider[ny][nx]:
                        near = True
                        break
                if near:
                    break
            band[gy][gx] = near
    return band


def perimeter_hugging_pct(plan: ParsedPlan, depth_ft: float = 25.0, cell: int = 2) -> float:
    """Fraction of building footprint sitting within depth_ft of a wall (high = a good ring)."""
    g = _grids(plan, cell)
    band = _perimeter_band(g, max(1, int(depth_ft * FTPX / cell)))
    built = 0
    hugging = 0
    for gy in range(g.h):
        for gx in range(g.w):
            if g.building[gy][gx] and g.inside[gy][gx]:
                built += 1
                if band[gy][gx]:
                    hugging += 1
    return hugging / built if built else 0.0


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


def top_vacant_rects(
    plan: ParsedPlan,
    n: int = 3,
    cell: int = 2,
    min_area_sqft: float = 150.0,
    perimeter_depth_ft: float = 25.0,
) -> list[VacantRect]:
    """The n largest non-overlapping empty rectangles, largest first (greedy).

    Each is tagged zone="central" (courtyard - good) or "perimeter" (a gap in the
    wall ring - slack) by whether its centroid sits in the perimeter band.
    """
    g = _grids(plan, cell)
    band = _perimeter_band(g, max(1, int(perimeter_depth_ft * FTPX / cell)))
    vacant: Grid = [[g.inside[gy][gx] and not g.occ[gy][gx] for gx in range(g.w)] for gy in range(g.h)]
    floor_px = min_area_sqft * FTPX * FTPX
    out: list[VacantRect] = []
    for _ in range(n):
        area_cells, gx0, gy0, wc, hc = _max_rect(vacant, g.w, g.h)
        if area_cells * cell * cell < floor_px:
            break
        cy, cx = gy0 + hc // 2, gx0 + wc // 2
        out.append(
            VacantRect(
                w_ft=wc * cell / FTPX,
                h_ft=hc * cell / FTPX,
                area_sqft=round(area_cells * cell * cell / (FTPX * FTPX)),
                x=gx0 * cell + g.minx,
                y=gy0 * cell + g.miny,
                zone="perimeter" if band[cy][cx] else "central",
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


def _point_rect_dist(px: float, py: float, r: Rect) -> float:
    """Euclidean distance from a point to a rectangle (0 if the point is inside)."""
    dx = max(r.x - px, 0.0, px - r.x2)
    dy = max(r.y - py, 0.0, py - r.y2)
    return math.hypot(dx, dy)


def fire_water_adrift(plan: ParsedPlan, max_gap_ft: float = TUB_MAX_GAP_FT) -> list[TubAdrift]:
    """Fire-water tubs sitting farther than max_gap_ft from any building.

    A tensuioke is fed by roof runoff (gutter -> downspout -> tub at the wall base), so every
    tub must sit against a building. Unlike a court's open space (a judgment call), this is a
    hard geometric rule: a tub adrift in the court is fed by nothing. Worst (farthest) first.
    """
    out: list[TubAdrift] = []
    for t in plan.tubs:
        cx, cy = t.x + t.w / 2, t.y + t.h / 2
        gaps = [_point_rect_dist(cx, cy, b) for b in plan.buildings]
        gap_ft = (min(gaps) if gaps else float("inf")) / FTPX
        if gap_ft > max_gap_ft:
            out.append(TubAdrift(cx, cy, gap_ft))
    out.sort(key=lambda t: t.gap_ft, reverse=True)
    return out


@dataclass(frozen=True)
class TubIndoors:
    """A fire-water tub drawn INSIDE a building instead of against its outside wall."""

    x: float
    y: float
    depth_ft: float  # how far the tub's center lies inside the footprint


def tubs_indoors(plan: ParsedPlan) -> list[TubIndoors]:
    """Fire-water tubs standing INSIDE a building footprint rather than against its outside wall.

    A tensuioke stands in the open at the foot of a downspout, catching what the roof sheds, so
    it belongs OUTSIDE the wall it serves. Drawn inside the footprint it is fed by nothing and
    stands where no bucket line can reach it - the two things the tub exists for. This is the
    companion of `fire_water_adrift`: that check pulls a tub IN toward a building, this one keeps
    it OUT of one, and only the narrow band along the outside wall - where a real tub stands -
    satisfies both. Worst (deepest inside) first.
    """
    out: list[TubIndoors] = []
    for t in plan.tubs:
        cx, cy = t.x + t.w / 2, t.y + t.h / 2
        depth = 0.0
        for b in plan.buildings:
            if b.x <= cx <= b.x2 and b.y <= cy <= b.y2:
                depth = max(depth, min(cx - b.x, b.x2 - cx, cy - b.y, b.y2 - cy))
        if depth > 0:
            out.append(TubIndoors(cx, cy, depth / FTPX))
    out.sort(key=lambda t: t.depth_ft, reverse=True)
    return out


@dataclass(frozen=True)
class TubOnWell:
    """A fire-water tub glyph overlapping a well glyph - they smear into one blob."""

    x: float
    y: float


def tubs_on_wells(plan: ParsedPlan, min_px: float = TUB_WELL_MIN_PX) -> list[TubOnWell]:
    """Fire-water tubs sitting ON a well. Both are small point-glyphs; overlapping ones read as
    one object and are functionally wrong (a rain-fed fire tub is not the drawing well). Any real
    overlap is a defect - move the tub to a different eaves corner."""
    out: list[TubOnWell] = []
    for t in plan.tubs:
        if any(_overlap_px(t.x, t.y, t.x2, t.y2, w) >= min_px for w in plan.wells):
            out.append(TubOnWell(t.x + t.w / 2, t.y + t.h / 2))
    return out


@dataclass(frozen=True)
class Occluded:
    """A foreground item painted over by anything drawn later in the SVG (not on the top layer)."""

    kind: str  # "label" | "tub" | "well" | "feature"
    text: str  # label text, or "" for a tub
    x: float
    y: float


def _overlap_px(ax: float, ay: float, ax2: float, ay2: float, b: Rect) -> float:
    """Smaller of the x/y overlaps between a box and rect b (>0 only on a real 2-D overlap)."""
    return min(min(ax2, b.x2) - max(ax, b.x), min(ay2, b.y2) - max(ay, b.y))


def occluded_foreground(plan: ParsedPlan, min_px: float = OCCLUSION_MIN_PX) -> list[Occluded]:
    """Foreground items painted OVER by anything drawn LATER in the SVG - i.e. not on the top
    layer, so they read as buried (a label's ink, a tub's rim, a privy that vanishes).

    Draw-order rule: labels, point glyphs and furniture-scale features all belong ABOVE the
    fills, so any later rect or glyph covering one is a defect. Both sides of that test are
    deliberately broad - the occluder side is fill-BLIND (see OCCLUSION_MIN_PX) and the occluded
    side spans labels, tubs, wells and every sub-building rect - because the two defects this
    check was widened for (2026-07-25) each slipped through a narrow enumeration: a note box was
    not a "building or garden", and a privy was not a "label or tub".
    """
    occluders = plan.fills + plan.glyphs
    out: list[Occluded] = []

    def buried(x: float, y: float, x2: float, y2: float, pos: int) -> bool:
        # A later shape wholly INSIDE the item is its own detailing (a well-mouth circle in its
        # curb, a hearth's fire in its hearth), not something painted over it.
        return any(f.pos > pos and _overlap_px(x, y, x2, y2, f) >= min_px and not (f.x >= x and f.y >= y and f.x2 <= x2 and f.y2 <= y2) for f in occluders)

    for lab in plan.labels:
        if buried(lab.x, lab.y, lab.x2, lab.y2, lab.pos):
            out.append(Occluded("label", lab.text, lab.cx, lab.cy))
    for t in plan.tubs:
        if buried(t.x, t.y, t.x2, t.y2, t.pos):
            out.append(Occluded("tub", "", t.x + t.w / 2, t.y + t.h / 2))
    for w in plan.wells:
        if buried(w.x, w.y, w.x2, w.y2, w.pos):
            out.append(Occluded("well", "", w.x + w.w / 2, w.y + w.h / 2))
    for f0 in plan.furniture:
        if buried(f0.x, f0.y, f0.x2, f0.y2, f0.pos):
            out.append(Occluded("feature", "", f0.x + f0.w / 2, f0.y + f0.h / 2))
    return out


@dataclass(frozen=True)
class OrphanLabel:
    """A glyph-group label (e.g. 'fire-water tubs') sitting too far from any glyph it names."""

    text: str
    x: float
    y: float
    gap_ft: float


def orphan_group_labels(plan: ParsedPlan, max_ft: float = GROUP_LABEL_MAX_FT) -> list[OrphanLabel]:
    """Labels that NAME a glyph group (fire-water tubs, well) must sit next to a glyph of that kind
    - a label far from every glyph it names is orphaned. (Building labels sit on their rect, so they
    are not this check's concern; only the small point-glyph groups drift.)"""
    kinds: dict[str, tuple[Rect, ...]] = {"tub": plan.tubs, "well": plan.wells}
    out: list[OrphanLabel] = []
    for lab in plan.labels:
        low = lab.text.lower()
        for key, kind in GROUP_LABEL_GLYPHS.items():
            if key not in low:
                continue
            centers = kinds[kind]
            if centers:
                lr = Rect(lab.x, lab.y, lab.w, lab.h)
                d = min(_point_rect_dist(c.x + c.w / 2, c.y + c.h / 2, lr) for c in centers) / FTPX
                if d > max_ft:
                    out.append(OrphanLabel(lab.text, lab.cx, lab.cy, d))
            break
    out.sort(key=lambda o: o.gap_ft, reverse=True)
    return out


@dataclass(frozen=True)
class WallOpening:
    """A gap in the compound wall's INK - the passage a cart actually drives through."""

    x: float
    y: float
    ft: float


def wall_openings(plan: ParsedPlan) -> list[WallOpening]:
    """Openings in the compound wall, measured from the INK, widest first.

    Measured from `wall_bands` - which model `stroke-linecap="square"`, a run inking half a stroke
    past each endpoint - and NOT from the line endpoints. That difference IS the check. WHY
    (2026-07-25): all three pool manors were authored by writing each intended opening as the two
    flanking ENDPOINTS, which a 9 px capped wall then narrowed by a full stroke width, so every
    stated 13.3 ft main gate rendered as 10.3 ft of passage. On Ubame that had quietly made the
    goods-cart gate WIDER than the ceremonial main gate - a hierarchy inversion nobody intended.
    Nothing in the audit measured ink, so the error was invisible in the report: it had to be found
    by eye on one map, and it then sat unfixed on the other two until they were hand-checked.
    Reporting ink width makes "ink equals intent" something an author reads off the audit.

    The correct authoring idiom is to pull each flanking endpoint back by half a stroke (4.5 px on
    the 9 px compound wall) so the CAP lands on the intended edge - never to write the endpoints at
    the opening's coordinates and hope the cap is not there.
    """
    out: list[WallOpening] = []
    for horiz in (True, False):
        groups: dict[float, list[Rect]] = {}
        for band in plan.wall_bands:
            if band.fill != WALL_STROKE or (band.w >= band.h) != horiz:
                continue
            groups.setdefault(round(band.y + band.h / 2 if horiz else band.x + band.w / 2, 1), []).append(band)
        for key, segs in groups.items():
            segs.sort(key=lambda s: s.x if horiz else s.y)
            for a, b in zip(segs, segs[1:], strict=False):
                gap = (b.x - a.x2) if horiz else (b.y - a.y2)
                if 0 < gap < OPENING_MAX_PX:
                    mid = (a.x2 + b.x) / 2 if horiz else (a.y2 + b.y) / 2
                    out.append(WallOpening(mid if horiz else key, key if horiz else mid, gap / FTPX))
    out.sort(key=lambda o: o.ft, reverse=True)
    return out


def _gate_openings(plan: ParsedPlan) -> list[tuple[float, float]]:
    """Midpoints of gaps in the compound wall - the gate/postern openings."""
    return [(o.x, o.y) for o in wall_openings(plan)]


@dataclass(frozen=True)
class MisplacedBoard:
    """A notice board too far from any gate opening to be seen by passers-through."""

    x: float
    y: float
    gap_ft: float


def notice_board_adrift(plan: ParsedPlan, max_ft: float = NOTICE_BOARD_MAX_FT) -> list[MisplacedBoard]:
    """A notice board (kosatsu) is read where people pass, so it must sit at a gate. Flag any
    'notice board' label farther than max_ft from the nearest wall gate opening."""
    ops = _gate_openings(plan)
    if not ops:
        return []
    out: list[MisplacedBoard] = []
    for lab in plan.labels:
        if "notice board" in lab.text.lower():
            lr = Rect(lab.x, lab.y, lab.w, lab.h)
            d = min(_point_rect_dist(ox, oy, lr) for ox, oy in ops) / FTPX  # nearest edge of the board
            if d > max_ft:
                out.append(MisplacedBoard(lab.cx, lab.cy, d))
    return out


@dataclass(frozen=True)
class DarkOnDark:
    """A dark (black-ink) label laid over a dark feature, with a nudge that would clear it."""

    text: str
    x: float
    y: float
    nudge_dx_ft: float
    nudge_dy_ft: float
    fixable: bool


def _dark_hit(x: float, y: float, w: float, h: float, darks: tuple[Rect, ...], walls: tuple[Rect, ...]) -> bool:
    """True if box (x,y,w,h) sits ON any dark-filled rect or (stroke-widened) wall by >= the min overlap."""
    if any(_overlap_px(x, y, x + w, y + h, d) >= DARK_MIN_OVERLAP_PX for d in darks):
        return True
    return any(_overlap_px(x, y, x + w, y + h, Rect(s.x - 4.5, s.y - 4.5, s.w + 9, s.h + 9)) >= DARK_MIN_OVERLAP_PX for s in walls)


def dark_on_dark_labels(plan: ParsedPlan) -> list[DarkOnDark]:
    """Black-ink labels sitting on a dark feature (a wall, a dark block) where they lose contrast.
    For each, search a small grid of nudges and report the first offset that lands the label on
    clear ground (fixable=False if nothing within the search radius clears it)."""
    out: list[DarkOnDark] = []
    steps = [n * NUDGE_STEP_PX for n in range(1, int(NUDGE_MAX_PX / NUDGE_STEP_PX) + 1)]
    for lab in plan.labels:
        if _luma(lab.fill) >= LABEL_DARK_LUMA or not _dark_hit(lab.x, lab.y, lab.w, lab.h, plan.dark_rects, plan.wall_segs):
            continue
        best: tuple[float, float] | None = None
        for r in steps:
            for dx, dy in ((r, 0), (-r, 0), (0, r), (0, -r)):
                if not _dark_hit(lab.x + dx, lab.y + dy, lab.w, lab.h, plan.dark_rects, plan.wall_segs):
                    best = (dx / FTPX, dy / FTPX)
                    break
            if best is not None:
                break
        out.append(DarkOnDark(lab.text, lab.cx, lab.cy, *(best or (0.0, 0.0)), best is not None))
    return out


@dataclass(frozen=True)
class LabelClash:
    """Two labels whose boxes overlap - their text smears together."""

    a: str
    b: str
    x: float
    y: float


def overlapping_labels(plan: ParsedPlan, min_px: float = LABEL_OVERLAP_MIN_PX) -> list[LabelClash]:
    """Pairs of labels whose estimated boxes overlap by more than min_px on both axes."""
    out: list[LabelClash] = []
    labs = plan.labels
    for i, a in enumerate(labs):
        for b in labs[i + 1 :]:
            ox = min(a.x2, b.x2) - max(a.x, b.x)
            oy = min(a.y2, b.y2) - max(a.y, b.y)
            if ox >= min_px and oy >= min_px:
                out.append(LabelClash(a.text, b.text, (max(a.x, b.x) + min(a.x2, b.x2)) / 2, (max(a.y, b.y) + min(a.y2, b.y2)) / 2))
    return out


@dataclass(frozen=True)
class FloatingDoor:
    """A door glyph floating INSIDE a building instead of sitting on (an opening in) its wall."""

    x: float
    y: float
    gap_ft: float  # gap to the nearest wall it should sit on


def floating_doors(plan: ParsedPlan) -> list[FloatingDoor]:
    """A door is an opening in a WALL, so its glyph must sit on a building edge, not adrift in the
    interior. Flag a small dark door-rect fully contained in a building whose nearest edge is close
    (it is clearly meant to be that wall's door) but not flush - leaving white space to the wall."""
    out: list[FloatingDoor] = []
    for d in plan.door_rects:
        for b in plan.buildings:
            gaps = (d.x - b.x, b.x2 - d.x2, d.y - b.y, b.y2 - d.y2)
            if all(g >= 0 for g in gaps):  # fully inside this building
                gap = min(gaps)
                if DOOR_FLUSH_TOL_PX < gap <= DOOR_NEAR_PX:
                    out.append(FloatingDoor(d.x + d.w / 2, d.y + d.h / 2, gap / FTPX))
                break
    return out


@dataclass(frozen=True)
class StructureOnWall:
    """A built footprint drawn across the ink of a wall, i.e. standing inside the masonry."""

    x: float  # structure center, SVG px
    y: float
    w_ft: float  # the structure's size, to identify it in the source
    h_ft: float
    into_ft: float  # how far it reaches into the wall's ink
    wall: str  # "compound wall" | "court divider"


def structures_on_walls(plan: ParsedPlan, min_px: float = WALL_OVERLAP_MIN_PX) -> list[StructureOnWall]:
    """Structures overlapping the ink of a compound wall or a court divider, worst first.

    A wall is a built object with real thickness (drawn at true scale - 3 ft for the compound
    wall, 2 ft for the divider - and centered on the boundary, so half of it lies inside), not a
    boundary line with no substance. Two things go wrong when a structure is drawn across it:
    the plan asserts a building and a wall occupy the same ground, and the render shows it -
    the wall is painted last, so it eats the structure's own outline and the structure reads as
    bleeding through the masonry. The correct relation is ABUT: a jin'ya's buildings back the
    wall with their rear eaves nearly touching it, which the check permits (a flush edge scores
    zero overlap). Where a structure genuinely IS part of the wall - a nagayamon gatehouse, a
    postern - the established idiom is to draw the wall as segments BROKEN around it (already
    used for Ochiba's kitchen postern and both south gates), which states the relationship
    explicitly and leaves no ink to overlap.
    """
    out: list[StructureOnWall] = []
    for s in plan.structures:
        worst: tuple[float, str] | None = None
        for band in plan.wall_bands:
            ov = _overlap_px(s.x, s.y, s.x2, s.y2, band)
            if ov > min_px and (worst is None or ov > worst[0]):
                worst = (ov, WALL_KIND[band.fill])
        if worst is not None:
            out.append(StructureOnWall(s.x + s.w / 2, s.y + s.h / 2, s.w / FTPX, s.h / FTPX, worst[0] / FTPX, worst[1]))
    out.sort(key=lambda r: r.into_ft, reverse=True)
    return out


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
    hug = perimeter_hugging_pct(plan, cell=cell)
    lines = [
        f"walled interior: {(maxx - minx) / FTPX:.0f} x {(maxy - miny) / FTPX:.0f} ft = {inside * cell * cell / (FTPX * FTPX):,.0f} sqft",
        f"building coverage: {100 * built / inside:.0f}%  (jin'ya band 37-42%)",
        f"purposeful open (garden/court/glyphs): {100 * openc / inside:.0f}%  (features)",
        f"bare open ground: {100 * empty / inside:.0f}%  (courts are open - not a defect alone)",
        f"perimeter-hugging: {100 * hug:.0f}% of building footprint within 25 ft of a wall  (high = buildings ring the courts)",
        "top vacant rectangles (largest first - CENTRAL=courtyard/feature, PERIMETER=ring gap/slack):",
    ]
    tv = top_vacant_rects(plan, n=4, cell=cell)
    if not tv:
        lines.append("    (none above the floor area)")
    lines += [f"    {v.w_ft:.0f} x {v.h_ft:.0f} ft = {v.area_sqft:,.0f} sqft [{v.orient}, {v.zone}] at svg({v.x:.0f},{v.y:.0f})" for v in tv]
    lines.append("per-region density (a large low-coverage tile = consolidation candidate):")
    lines += [f"    tile[r{t.row}c{t.col}]: {100 * t.coverage_pct:.0f}% built  ({t.interior_sqft:,.0f} sqft interior)" for t in region_density(plan, cell=cell)]
    lines.append("aligned building gaps 5-30 ft (kura fire-gap OK ~10 ft; wooden >8 ft loose):")
    gaps = aligned_gaps(plan)
    if not gaps:
        lines.append("    (none in the 5-30 ft range)")
    lines += [f"    {gp.ft:.1f} ft  {gp.orient}  at svg({gp.mx:.0f},{gp.my:.0f})   {gap_tag(gp)}" for gp in gaps[:12]]
    lines.append(f"fire-water tubs adrift (a gutter-fed tub must sit <={TUB_MAX_GAP_FT:.0f} ft from a building):")
    if not plan.tubs:
        lines.append("    (no fire-water tubs in this plan)")
    else:
        adrift = fire_water_adrift(plan)
        indoors = tubs_indoors(plan)
        if not adrift and not indoors:
            lines.append(f"    (all {len(plan.tubs)} tubs sit outside, against a building)")
        lines += [f"    tub at svg({t.x:.0f},{t.y:.0f}) is {t.gap_ft:.1f} ft from the nearest building - move it to a wall/eaves" for t in adrift]
        lines += [
            f"    TUB INDOORS: a fire-water tub at svg({t.x:.0f},{t.y:.0f}) stands {t.depth_ft:.1f} ft INSIDE a building - a tensuioke is gutter-fed and bucket-served, so move it OUT against the wall"
            for t in indoors
        ]
    lines.append("LAYER/LABEL checks:")
    occ = occluded_foreground(plan)
    if not occ:
        lines.append("    labels/tubs on top: OK (nothing buried under a later feature)")
    lines += [f"    BURIED: {o.kind} {(repr(o.text) + ' ') if o.text else ''}at svg({o.x:.0f},{o.y:.0f}) is under a feature drawn later - move it to the top layer" for o in occ]
    for orp in orphan_group_labels(plan):
        lines.append(f"    ORPHAN LABEL: {orp.text!r} at svg({orp.x:.0f},{orp.y:.0f}) is {orp.gap_ft:.1f} ft from the nearest glyph it names - move it beside one")
    for bd in notice_board_adrift(plan):
        lines.append(f"    NOTICE BOARD: at svg({bd.x:.0f},{bd.y:.0f}) is {bd.gap_ft:.1f} ft from the nearest gate opening - move it to a gate")
    for dk in dark_on_dark_labels(plan):
        fix = f"nudge ({dk.nudge_dx_ft:+.0f},{dk.nudge_dy_ft:+.0f}) ft clears it" if dk.fixable else "no small nudge clears it - relocate"
        lines.append(f"    DARK-ON-DARK: {dk.text!r} at svg({dk.x:.0f},{dk.y:.0f}) - black ink over a dark feature; {fix}")
    for cl in overlapping_labels(plan):
        lines.append(f"    LABEL CLASH: {cl.a!r} and {cl.b!r} overlap at svg({cl.x:.0f},{cl.y:.0f}) - move one apart")
    for dr in floating_doors(plan):
        lines.append(f"    DOOR ADRIFT: a door at svg({dr.x:.0f},{dr.y:.0f}) floats {dr.gap_ft:.1f} ft inside the building - set it on the wall")
    for tw in tubs_on_wells(plan):
        lines.append(f"    TUB ON WELL: a fire-water tub at svg({tw.x:.0f},{tw.y:.0f}) overlaps a well - move it to a different eaves corner")
    lines.append("GATE OPENINGS (compound wall, measured from the INK - a square cap eats 1.5 ft per end):")
    openings = wall_openings(plan)
    if not openings:
        lines.append("    (no openings found in the compound wall)")
    lines += [f"    {o.ft:5.1f} ft  at svg({o.x:.0f},{o.y:.0f})   compare with the width this opening's comment claims" for o in openings]
    lines.append("STRUCTURE/WALL check (a structure abuts a wall, never stands in it):")
    if not plan.wall_bands:
        lines.append("    (no wall strokes in this plan)")
    else:
        onwall = structures_on_walls(plan)
        if not onwall:
            lines.append(f"    all {len(plan.structures)} structures clear the wall ink: OK")
        lines += [
            f"    ON WALL: a {sw.w_ft:.0f} x {sw.h_ft:.0f} ft structure at svg({sw.x:.0f},{sw.y:.0f}) reaches {sw.into_ft:.1f} ft into the {sw.wall} - "
            "set it against the wall's inner face, or break the wall around it if it IS part of the wall"
            for sw in onwall
        ]
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
