#!/usr/bin/env python3
"""compound.py - a feet-first compound PROGRAM + a perimeter-first PLACER (feature 008).

Mode A compound plans are hand-authored, but their COMPOSITION (buildings ringing the
courts, the open court-spine held in the center) is easy to get wrong by hand. This module
lets a compound be declared as a feet-based program - the envelope, the reserved court-spine
(forecourt -> oshirasu -> garden), and a list of buildings each sized IN FEET with a wall
tag - and arranges them PERIMETER-FIRST into a composed draft SVG the GM then refines.

Footage is the source unit; pixels are derived (FTPX) only at emit time. The placer is the
Mode A analog of the Mode B water-first generator: a fixed ordering (reserve the spine, then
hug the walls largest-first with fire-gaps) that cannot paint itself into a corner - the
opposite of worst-fit, which would scatter buildings into the center.

See buildings.md "Composition: perimeter buildings + a named court-spine".

CLI:  python3 compound.py            # place the built-in county magistracy, write a draft SVG
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

FTPX: float = 3.0  # 3 px = 1 ft (emit-time only)
FIRE_GAP_FT: float = 7.0  # default gap between hugging buildings (a real fire-gap)
WALL_MARGIN_FT: float = 3.0  # a building's inset from the very corner / wall stroke

# palette keys -> (fill, stroke) reused from the Mode A vocabulary (SKILL.md)
KINDS: dict[str, tuple[str, str]] = {
    "lord": ("#DDB87A", "#5A3F1E"),
    "service": ("#C9A57A", "#6B4F2A"),
    "plain": ("#E8D2A8", "#6B4F2A"),
    "kura": ("#F2EFE4", "#4A3318"),
    "shrine": ("#C9876C", "#6B2A18"),
    "cell": ("#B89868", "#5C4318"),
    "dark": ("#8C6F3E", "#4A3318"),
}
COURT_FILL: dict[str, str] = {
    "forecourt": "url(#court-earth)",
    "oshirasu": "url(#oshirasu-sand)",
    "garden": "url(#garden-stipple)",
    "yard": "url(#court-earth)",
}


@dataclass(frozen=True)
class Envelope:
    """The walled interior, in feet. Inner (residence) court is north (y small); outer
    (administrative) court is south (y large), with the main gate on the south wall."""

    w_ft: float
    h_ft: float
    divider_ft: float  # y of the inner/outer court divider
    gate_w_ft: float = 13.0  # main-gate opening width (on the south wall, centered)


@dataclass(frozen=True)
class CourtZone:
    """A reserved OPEN court in the spine (buildings never overlap it)."""

    name: str
    x_ft: float
    y_ft: float
    w_ft: float
    h_ft: float

    @property
    def x2(self) -> float:
        return self.x_ft + self.w_ft

    @property
    def y2(self) -> float:
        return self.y_ft + self.h_ft


@dataclass(frozen=True)
class BuildingSpec:
    """A building sized in feet with a placement tag."""

    name: str
    kind: str
    w_ft: float
    h_ft: float
    court: str  # "outer" | "inner"
    wall: str  # "N" | "S" | "E" | "W" | "divider"
    order: int = 0  # higher places first (largest/most-important hug the wall first)


@dataclass(frozen=True)
class CompoundProgram:
    title: str
    envelope: Envelope
    spine: tuple[CourtZone, ...] = ()
    buildings: tuple[BuildingSpec, ...] = ()


@dataclass(frozen=True)
class Placed:
    """A building assigned a feet position (top-left)."""

    spec: BuildingSpec
    x_ft: float
    y_ft: float

    @property
    def x2(self) -> float:
        return self.x_ft + self.spec.w_ft

    @property
    def y2(self) -> float:
        return self.y_ft + self.spec.h_ft


@dataclass
class PlaceResult:
    placed: list[Placed] = field(default_factory=list)
    overflow: list[BuildingSpec] = field(default_factory=list)  # did not fit the ring


# ---- placement (perimeter-first) ---------------------------------------------------------


def _court_yrange(env: Envelope, court: str) -> tuple[float, float]:
    return (0.0, env.divider_ft) if court == "inner" else (env.divider_ft, env.h_ft)


def _gate_interval(env: Envelope) -> tuple[float, float]:
    half = env.gate_w_ft / 2
    return (env.w_ft / 2 - half, env.w_ft / 2 + half)


def _cross_coord(env: Envelope, court: str, wall: str, spec: BuildingSpec) -> float:
    """Fixed cross-axis top-left coord for a hugging building (y for N/S/divider, x for E/W)."""
    if wall == "N":
        return 0.0
    if wall == "S":
        return env.h_ft - spec.h_ft
    if wall == "divider":
        return env.divider_ft if court == "outer" else env.divider_ft - spec.h_ft
    if wall == "W":
        return 0.0
    return env.w_ft - spec.w_ft  # "E"


def _overlaps(ax: float, ay: float, aw: float, ah: float, z: CourtZone) -> bool:
    return ax < z.x2 and ax + aw > z.x_ft and ay < z.y2 and ay + ah > z.y_ft


def _obstacle_end(
    env: Envelope,
    wall: str,
    gate: tuple[float, float] | None,
    spine: tuple[CourtZone, ...],
    px: float,
    py: float,
    spec: BuildingSpec,
    horizontal: bool,
) -> float | None:
    """Along-axis end of the nearest obstacle (gate or spine court) the building overlaps."""
    ends: list[float] = []
    if gate is not None and px < gate[1] and px + spec.w_ft > gate[0]:
        ends.append(gate[1])
    for z in spine:
        if _overlaps(px, py, spec.w_ft, spec.h_ft, z):
            ends.append(z.x2 if horizontal else z.y2)
    return max(ends) if ends else None


@dataclass(frozen=True)
class _Reserve:
    """The corners belong to the vertical (E/W) walls, so horizontal rows inset by these."""

    left: float  # max W-wall building width
    right: float  # max E-wall building width


def _place_wall(
    env: Envelope,
    court: str,
    wall: str,
    specs: list[BuildingSpec],
    spine: tuple[CourtZone, ...],
    res: _Reserve,
    result: PlaceResult,
) -> None:
    horizontal = wall in ("N", "S", "divider")
    if horizontal:  # N/S/divider rows inset by the W/E corner reservations (corners are E/W's)
        along_start, along_end = res.left, env.w_ft - res.right
    else:  # E/W rows use the full court height (they own the corners)
        along_start, along_end = _court_yrange(env, court)
    gate = _gate_interval(env) if wall == "S" else None
    cursor = along_start + WALL_MARGIN_FT
    for spec in specs:
        cross = _cross_coord(env, court, wall, spec)
        size = spec.w_ft if horizontal else spec.h_ft
        while True:
            px, py = (cursor, cross) if horizontal else (cross, cursor)
            end = _obstacle_end(env, wall, gate, spine, px, py, spec, horizontal)
            if end is None:
                break
            cursor = end + FIRE_GAP_FT
        if cursor + size > along_end - WALL_MARGIN_FT:
            result.overflow.append(spec)
            continue
        px, py = (cursor, cross) if horizontal else (cross, cursor)
        result.placed.append(Placed(spec, px, py))
        cursor += size + FIRE_GAP_FT


def place(program: CompoundProgram) -> PlaceResult:
    """Arrange the program's buildings perimeter-first: reserve the spine + the corners, then
    hug each wall largest/most-important first with fire-gaps, skipping the gate and courts."""
    result = PlaceResult()
    groups: dict[tuple[str, str], list[BuildingSpec]] = {}
    for s in program.buildings:
        groups.setdefault((s.court, s.wall), []).append(s)

    def maxdim(court: str, wall: str, dim: str) -> float:
        vals = [getattr(s, dim) for s in groups.get((court, wall), [])]
        return max(vals) if vals else 0.0

    for (court, wall), specs in sorted(groups.items()):
        specs.sort(key=lambda s: (-s.order, -(s.w_ft * s.h_ft)))
        res = _Reserve(left=maxdim(court, "W", "w_ft"), right=maxdim(court, "E", "w_ft"))
        _place_wall(program.envelope, court, wall, specs, program.spine, res, result)
    return result


# ---- SVG emit (feet -> px at FTPX; a composed DRAFT the GM refines) -----------------------

_DEFS = (
    '<defs>'
    '<pattern id="court-earth" patternUnits="userSpaceOnUse" width="16" height="16">'
    '<rect width="16" height="16" fill="#D9C28E"/><circle cx="4" cy="6" r="0.6" fill="#A88E58"/>'
    '<circle cx="12" cy="2" r="0.6" fill="#A88E58"/></pattern>'
    '<pattern id="oshirasu-sand" patternUnits="userSpaceOnUse" width="12" height="12">'
    '<rect width="12" height="12" fill="#F2EAD0"/><circle cx="3" cy="4" r="0.5" fill="#C9B884"/>'
    '<circle cx="8" cy="2" r="0.5" fill="#C9B884"/></pattern>'
    '<pattern id="garden-stipple" patternUnits="userSpaceOnUse" width="14" height="14">'
    '<rect width="14" height="14" fill="#BFCFA0"/><circle cx="3" cy="3" r="0.8" fill="#7A8C5C"/>'
    '<circle cx="10" cy="9" r="0.8" fill="#7A8C5C"/></pattern></defs>'
)


def emit_svg(program: CompoundProgram, result: PlaceResult, margin_ft: float = 20.0) -> str:
    """Build a composed draft SVG (feet -> px). Not a final map - the GM refines it."""
    env = program.envelope
    ox = oy = margin_ft * FTPX
    iw, ih = env.w_ft * FTPX, env.h_ft * FTPX
    cw, ch = iw + 2 * ox, ih + 2 * oy

    def rect(x: float, y: float, w: float, h: float, fill: str, stroke: str, sw: float) -> str:
        return f'<rect x="{ox + x * FTPX:.0f}" y="{oy + y * FTPX:.0f}" width="{w * FTPX:.0f}" height="{h * FTPX:.0f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'

    def label(cx: float, cy: float, s: str, size: int, italic: bool, fill: str) -> str:
        st = ' font-style="italic"' if italic else ' font-weight="bold"'
        return f'<text x="{ox + cx * FTPX:.0f}" y="{oy + cy * FTPX:.0f}" text-anchor="middle" font-size="{size}"{st} fill="{fill}">{s}</text>'

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cw:.0f} {ch:.0f}" font-family="Georgia, \'Times New Roman\', serif">',
        _DEFS,
        f'<rect x="0" y="0" width="{cw:.0f}" height="{ch:.0f}" fill="#EFE3C2"/>',
        rect(0, 0, env.w_ft, env.h_ft, "url(#court-earth)", "none", 0),
        label(env.w_ft / 2, -9, program.title, 20, False, "#3A2E1C"),
        label(env.w_ft / 2, -3, "(perimeter-first composed draft - refine by hand)", 10, True, "#6B4F2A"),
    ]
    for z in program.spine:  # reserved open courts, drawn + named
        parts.append(rect(z.x_ft, z.y_ft, z.w_ft, z.h_ft, COURT_FILL.get(z.name, "url(#court-earth)"), "#9C7A40", 0.8))
        parts.append(label(z.x_ft + z.w_ft / 2, z.y_ft + z.h_ft / 2, z.name, 11, True, "#5C4318"))
    for p in result.placed:  # buildings
        fill, stroke = KINDS.get(p.spec.kind, KINDS["service"])
        parts.append(rect(p.x_ft, p.y_ft, p.spec.w_ft, p.spec.h_ft, fill, stroke, 2))
        parts.append(label(p.x_ft + p.spec.w_ft / 2, p.y_ft + p.spec.h_ft / 2 + 1, p.spec.name, 10, False, "#3A2E1C"))
    # compound wall (4 segments; S wall broken by the gate) + divider
    gl, gr = _gate_interval(env)
    for x1, y1, x2, y2 in [
        (0, 0, env.w_ft, 0),
        (0, 0, 0, env.h_ft),
        (env.w_ft, 0, env.w_ft, env.h_ft),
        (0, env.h_ft, gl, env.h_ft),
        (gr, env.h_ft, env.w_ft, env.h_ft),
    ]:
        parts.append(f'<line x1="{ox + x1 * FTPX:.0f}" y1="{oy + y1 * FTPX:.0f}" x2="{ox + x2 * FTPX:.0f}" y2="{oy + y2 * FTPX:.0f}" stroke="#2D2A24" stroke-width="9"/>')
    parts.append(f'<line x1="{ox:.0f}" y1="{oy + env.divider_ft * FTPX:.0f}" x2="{ox + iw:.0f}" y2="{oy + env.divider_ft * FTPX:.0f}" stroke="#3F3A30" stroke-width="6"/>')
    parts.append("</svg>")
    return "\n".join(parts)


# ---- a built-in county-magistracy program ------------------------------------------------


def county_magistracy_program() -> CompoundProgram:
    """A generic county magistracy declared entirely in feet (the placer composes it).

    Building masses are sized to land in the ~37-42% jin'ya coverage band (real jin'ya
    consolidate into a few large masses); the spine (garden -> oshirasu -> forecourt) sits
    clear of the wall rows so the placer never has to overlap it.
    """
    env = Envelope(w_ft=270.0, h_ft=200.0, divider_ft=90.0, gate_w_ft=13.0)
    spine = (
        CourtZone("garden", 50.0, 36.0, 165.0, 24.0),  # inner court, between residence and karo
        CourtZone("oshirasu", 68.0, 126.0, 132.0, 39.0),  # outer court, before the office-hall dais
        CourtZone("forecourt", 118.0, 166.0, 36.0, 31.0),  # just inside the main gate
    )
    b = BuildingSpec
    buildings = (
        # inner (residence) court - buildings ring N/E/W walls + back the divider
        b("residence", "lord", 92.0, 36.0, "inner", "N", order=10),
        b("servants", "service", 66.0, 15.0, "inner", "N", order=2),
        b("kitchen", "service", 44.0, 36.0, "inner", "W", order=5),
        b("shrine", "shrine", 40.0, 32.0, "inner", "E", order=4),
        b("guest house", "lord", 33.0, 30.0, "inner", "E", order=3),
        b("karo's house", "lord", 37.0, 26.0, "inner", "divider", order=3),
        # outer (administrative) court - office hall backs the divider (oshirasu in front)
        b("office hall", "lord", 113.0, 34.0, "outer", "divider", order=10),
        b("tax archive", "kura", 34.0, 30.0, "outer", "W", order=6),
        b("senior retainers", "service", 60.0, 18.0, "outer", "W", order=4),
        b("clerks' room", "plain", 30.0, 20.0, "outer", "W", order=2),
        b("granary", "kura", 52.0, 28.0, "outer", "E", order=6),
        b("barracks", "service", 33.0, 34.0, "outer", "E", order=4),
        b("cell", "cell", 18.0, 16.0, "outer", "E", order=1),
        b("gatehouse", "dark", 42.0, 15.0, "outer", "S", order=8),
        b("stables", "service", 33.0, 23.0, "outer", "S", order=5),
    )
    return CompoundProgram("County Magistracy (draft)", env, spine, buildings)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    out = args[0] if args else "pool/county-magistracy-draft.svg"
    program = county_magistracy_program()
    result = place(program)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(emit_svg(program, result))
    print(f"wrote {out}: {len(result.placed)} buildings placed, {len(result.overflow)} overflow")
    for spec in result.overflow:
        print(f"  OVERFLOW (did not fit its wall): {spec.name} ({spec.w_ft:.0f}x{spec.h_ft:.0f} ft, {spec.court} {spec.wall})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
