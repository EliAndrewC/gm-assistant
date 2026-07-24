#!/usr/bin/env python3
"""Budget-first city wall sizing (feature 009, specs/009-city-area-budget).

Every settlement mode grows from a first principle: villages from water flow, manors from a
declared square footage. This module gives provincial cities theirs - the SPACE BUDGET. From the
declared population and program it enumerates the full building inventory, costs it at calibrated
DRAWN-footprint gross ground costs (packed rows vs spaced compounds), adds the fixed civic
program, water, reserves, and a circulation fraction, and DERIVES the wall from the total. The
wall is the output of the budget, never a guess to iterate on: `city_wall_matches_budget` in
check_village.py then holds the drawn map to the promise recorded in `meta.budget`.

CALIBRATION (specs/009-city-area-budget/research.md, measured 2026-07 from the shipped pool):
every constant below carries its measured/researched basis inline. The two anchors: shipped
Tango (GM-accepted) back-predicts within ~1%; the pinned pre-feature Nagahara (GM-rejected,
~17% unaccounted open ground) prices as ~21% over-enclosed and fails the check.

Historical grounding (research.md B, China first per project doctrine): a Chinese county seat
ran a sparse street net (~10-20% of ground; ours draw at ~7% - deep blocks + alley warrens) and
NORMALLY enclosed 25-30% deliberately unbuilt ground (siege insurance, rank-sized walls). On a
diagram that roominess reads as emptiness unless drawn, so open ground enters the budget ONLY as
a declared, drawn line (agricultural district, drill ground, gardens) - never as ambient slack.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, field

# ---- calibration constants (all px^2 / px at the 3 ft/px city scale) -----------------------

HOUSEHOLD = 5.0  # humans per family - budgets.md convention used across the skill

# Family share by caste for a provincial city - budgets.md "Provincial city" caste table
# (600 families at pop 3,000: servants 120 / laborers 240 / merchants 150 / burakumin 30 /
# samurai 60; ZERO farmers - city farmland is worked from surrounding villages, unless an
# agricultural district deliberately overrides that assumption).
CASTE_FAMILY_FRAC: dict[str, float] = {"servants": 0.20, "laborers": 0.40, "merchants": 0.25, "burakumin": 0.05, "samurai": 0.10}
PACKED_CASTES = ("servants", "laborers", "merchants", "burakumin")  # row-housing castes (party walls)

# 2/3 of samurai families live INSIDE the walls; the rest hold extramural walled estates and
# commute (the estate doctrine). Measured: Tango 33 in-wall samurai houses, Nagahara 41, of the
# caste table's 60 families -> 0.55-0.68; 2/3 is the round middle.
SAMURAI_INWALL_FRAC = 2.0 / 3.0

# GROSS ground cost per dwelling = drawn footprint + its share of eave gaps / roji / margins.
# Measured on Tango (research.md A): packed healthy-quarter gross 448-822 px^2 (858 over all
# res+mixed quarters), samurai-ward gross ~2,915 px^2 (ratio ~3.6x). The pair below solves the
# Tango back-prediction to +0.2% while keeping that measured ratio - budget at DRAWN footprints
# (legibility floors included), never real-world square footage (FR-011).
C_PACKED = 690.0
C_SPACED = 2480.0

# The fixed civic program - a FLOOR, not per-capita (a pop-2,000 seat still carries the full
# mandatory program: governor's yamen, 6 ministries, temples, theater, gate furniture...).
# Itemized at Tango's measured compound footprints (research.md A) so program changes reprice
# honestly; historically civic ground is ~10% of a county seat's enclosure (research.md B).
CIVIC_PROGRAM: tuple[tuple[str, int | None, float], ...] = (
    ("governor's mansion (yamen)", 1, 17_730.0),
    ("six provincial ministries", 6, 7_980.0),
    ("temple precincts", 2, 16_250.0),
    ("minor civic (theater, flophouses, funerary, inspection, kura)", None, 17_440.0),
    ("shops, inns, stables", 21, 4_700.0),
    # Bell-and-drum tower (GM 2026-07-24): the walled seat's timekeeping/curfew tower at the main
    # street crossing - a ~70 ft masonry platform (23.3 px at 3 ft/px) + its reserved clear block.
    ("bell-and-drum tower", 1, 600.0),
)

# One in-wall water feature: a pond (landlocked) or the cargo canal + dock basin (river city).
# Measured: Tango pond 2,865 px^2; Nagahara canal-in-wall + dock 2,834 px^2 - same budget line.
WATER_AREA = 2_900.0

# Circulation (trunk road + ring road + streets + alleys) as a fraction of the interior, at
# DRAWN widths: measured 6.8% (Tango) / 7.0% (Nagahara). The historical band is 10-20% of
# ground (research.md B - itself triangulated, not measured), and our sparse end is consistent
# with the deep-block, alley-warren doctrine - so the MAP-calibrated figure wins.
CIRC_FRAC = 0.07

# A Tango-style in-wall agricultural district, as a fraction of the interior. Measured: Tango's
# declared agri reserve is 103,577 px^2 of a 689k interior = 15.0%; also comfortably inside the
# feature-006 reserve cap (20%) and the historical 25-30% open-reserve norm (research.md B).
AGRI_FRAC = 0.15

# Canonical provincial-city population band (budgets.md); capitals are a future tier.
POP_MIN, POP_MAX = 2000, 4000

# Clearance the wall needs to the canvas edge: moat gap (24) + moat (~22) + gate furniture,
# towers, labels and the crop margin - measured from both shipped gens' view margins.
WALL_MARGIN_PX = 150.0

CAL_FTPX = 3  # the scale every constant above is calibrated at (the city rung of the ladder)


@dataclass(frozen=True)
class BudgetLine:
    """One auditable row: what, how many, how much ground, and WHY that number."""

    label: str
    count: int | None
    area_px2: float
    basis: str


@dataclass(frozen=True)
class CityProgram:
    """The declaration made BEFORE anything is drawn - population plus the feature program."""

    population: int
    ftpx: int = CAL_FTPX
    river: bool = False
    agricultural_district: bool = False
    aspect: float = 0.93  # RY/RX; both shipped cities are near-round (Tango 0.938, Nagahara 0.931)
    nring: int = 20  # wall vertices; the shipped gens draw 20-22-gon rings
    extras: tuple[BudgetLine, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class WallSpec:
    """The derived wall: a closed ellipse N-gon (research.md Decision 4: both shipped cities are
    full rings - even river-bank Nagahara; the river never enters the walls)."""

    shape: str
    rx: float
    ry: float
    nring: int
    interior_px2: float
    perimeter_px: float


@dataclass(frozen=True)
class CityBudget:
    program: CityProgram
    lines: tuple[BudgetLine, ...]
    required_interior_px2: float
    wall: WallSpec
    dwelling_target: dict[str, object]


def derive_wall(required_px2: float, *, aspect: float, nring: int = 20) -> WallSpec:
    """Solve the wall semi-axes so the DRAWN N-gon encloses `required_px2`.

    The gen scripts draw the wall as an ellipse N-gon whose polygon area is 0.5*N*sin(2pi/N)*rx*ry
    - slightly under the smooth ellipse's pi*rx*ry. Target the N-gon area, or every wall comes
    out systematically small (data-model.md)."""
    if not 0.0 < aspect <= 1.0:
        raise ValueError(f"aspect must be in (0, 1] (RY/RX of a near-round ring), got {aspect}")
    factor = 0.5 * nring * math.sin(2 * math.pi / nring)
    rx = math.sqrt(required_px2 / (factor * aspect))
    ry = aspect * rx
    pts = [(rx * math.cos(2 * math.pi * i / nring), ry * math.sin(2 * math.pi * i / nring)) for i in range(nring)]
    perimeter = sum(math.dist(pts[i], pts[(i + 1) % nring]) for i in range(nring))
    return WallSpec(shape="ring", rx=rx, ry=ry, nring=nring, interior_px2=factor * rx * ry, perimeter_px=perimeter)


def plan_city(program: CityProgram, canvas: tuple[float, float] | None = None) -> CityBudget:
    """Compute the full space budget and derive the wall - BEFORE anything is placed.

    Deterministic and pure. Raises ValueError (with the numbers) when the population is outside
    the provincial band or the derived wall cannot fit the canvas - never silently clamps."""
    pop = program.population
    if not POP_MIN <= pop <= POP_MAX:
        raise ValueError(f"population {pop} outside the canonical provincial-city band [{POP_MIN}, {POP_MAX}] (budgets.md; capitals are a future tier)")
    k = (CAL_FTPX / program.ftpx) ** 2  # constants are calibrated at 3 ft/px; drawn px^2 scale by (3/ftpx)^2

    families = {caste: round(pop / HOUSEHOLD * frac) for caste, frac in CASTE_FAMILY_FRAC.items()}
    packed_n = sum(families[c] for c in PACKED_CASTES)
    samurai_inwall = round(families["samurai"] * SAMURAI_INWALL_FRAC)

    lines: list[BudgetLine] = [
        BudgetLine(
            "packed row housing (laborer/servant/merchant/burakumin)",
            packed_n,
            packed_n * C_PACKED * k,
            f"{packed_n} families x C_PACKED {C_PACKED:.0f} px^2 gross (Tango-measured rows + eaves + roji)",
        ),
        BudgetLine(
            "samurai houses in-wall",
            samurai_inwall,
            samurai_inwall * C_SPACED * k,
            f"2/3 of {families['samurai']} samurai families x C_SPACED {C_SPACED:.0f} px^2 gross (Tango samurai-ward; rest hold extramural estates)",
        ),
    ]
    lines += [BudgetLine(label, count, area * k, "fixed civic program floor at Tango-measured compound footprints (research.md A)") for label, count, area in CIVIC_PROGRAM]
    # Adept-monk housing (GM 2026-07-24): each of the 2 temple precincts keeps 2-3 ordinary homes
    # in its neighborhood for the married adepts among its 15-30 monks (temple-density canon,
    # settlements.md "City temples"). Clergy are not a lay caste, so these 5 households ride
    # OUTSIDE the caste table's 600 families - a small civic-adjacent line at packed gross cost.
    lines.append(
        BudgetLine("adept-monk houses by the temple precincts", 5, 5 * C_PACKED * k, "2 temple precincts x 2-3 adept-monk households at C_PACKED gross (clergy live outside the lay caste table)")
    )
    water_label = "cargo canal + dock basin" if program.river else "pond"
    lines.append(BudgetLine(water_label, 1, WATER_AREA * k, "one in-wall water feature - Tango pond 2,865 / Nagahara canal+dock 2,834 px^2 measured"))
    lines.extend(program.extras)

    fixed = sum(ln.area_px2 for ln in lines)
    denom = 1.0 - CIRC_FRAC - (AGRI_FRAC if program.agricultural_district else 0.0)
    required = fixed / denom
    lines.append(
        BudgetLine(
            "circulation (trunk + ring road + streets + alleys)",
            None,
            required * CIRC_FRAC,
            f"{CIRC_FRAC:.0%} of interior at drawn widths (measured 6.8-7.0%; historical envelope 10-20%, research.md B)",
        )
    )
    if program.agricultural_district:
        lines.append(
            BudgetLine(
                "agricultural district (in-wall farms, declared reserve)", None, required * AGRI_FRAC, f"{AGRI_FRAC:.0%} of interior (Tango's declared agri reserve; inside the 20% reserve cap)"
            )
        )

    wall = derive_wall(required, aspect=program.aspect, nring=program.nring)
    if canvas is not None:
        need_w, need_h = 2 * (wall.rx + WALL_MARGIN_PX), 2 * (wall.ry + WALL_MARGIN_PX)
        if need_w > canvas[0] or need_h > canvas[1]:
            raise ValueError(
                f"derived wall {wall.rx:.0f}x{wall.ry:.0f} needs {need_w:.0f}x{need_h:.0f} px incl. the {WALL_MARGIN_PX:.0f} px moat/margin clearance but the canvas is {canvas[0]:.0f}x{canvas[1]:.0f} - enlarge the canvas or trim the program; never clamp the wall"
            )

    target: dict[str, object] = {"families": families, "packed": packed_n, "samurai_inwall": samurai_inwall}
    return CityBudget(program=program, lines=tuple(lines), required_interior_px2=required, wall=wall, dwelling_target=target)


def budget_to_manifest(budget: CityBudget) -> dict[str, object]:
    """JSON-serializable dict for `s.meta(budget=...)` - the promise the checks hold the map to."""
    return {
        "required_interior_px2": budget.required_interior_px2,
        "interior_px2": budget.wall.interior_px2,
        "lines": [{"label": ln.label, "count": ln.count, "area_px2": ln.area_px2, "basis": ln.basis} for ln in budget.lines],
        "circulation_frac": CIRC_FRAC,
        "flags": {"river": budget.program.river, "agricultural_district": budget.program.agricultural_district},
        "wall": {"shape": budget.wall.shape, "rx": budget.wall.rx, "ry": budget.wall.ry, "nring": budget.wall.nring},
        "dwelling_target": budget.dwelling_target,
    }


def format_budget(budget: CityBudget) -> str:
    """The itemized, auditable report (returns the string; only the CLI prints)."""
    ftpx = budget.program.ftpx
    sqft = ftpx * ftpx
    out = [
        f"SPACE BUDGET - population {budget.program.population}, {ftpx} ft/px"
        + (", river city" if budget.program.river else "")
        + (", agricultural district" if budget.program.agricultural_district else "")
    ]
    out.append(f"{'line':66} {'count':>5} {'px^2':>9} {'acres':>6}  basis")
    for ln in budget.lines:
        acres = ln.area_px2 * sqft / 43_560
        out.append(f"{ln.label:66} {ln.count if ln.count is not None else '-':>5} {ln.area_px2:>9.0f} {acres:>6.2f}  {ln.basis}")
    w = budget.wall
    out.append(f"required interior: {budget.required_interior_px2:.0f} px^2 ({budget.required_interior_px2 * sqft / 43_560:.1f} acres)")
    out.append(
        f"derived wall: {w.nring}-gon ring rx={w.rx:.0f} ry={w.ry:.0f} px ({w.rx * ftpx:.0f} x {w.ry * ftpx:.0f} ft semi-axes), perimeter {w.perimeter_px * ftpx:.0f} ft ({w.perimeter_px * ftpx / 5280:.2f} mi), encloses {w.interior_px2:.0f} px^2"
    )
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    """CLI: `python3 citybudget.py --plan --population 3000 [--river] [--agri] [--canvas WxH]`."""
    ap = argparse.ArgumentParser(description="Budget-first city wall sizing (feature 009)")
    ap.add_argument("--plan", action="store_true", help="print the itemized budget + derived wall")
    ap.add_argument("--population", type=int, required=True)
    ap.add_argument("--river", action="store_true")
    ap.add_argument("--agri", action="store_true", help="in-wall agricultural district (Tango-style)")
    ap.add_argument("--aspect", type=float, default=0.93)
    ap.add_argument("--nring", type=int, default=20)
    ap.add_argument("--canvas", type=str, default=None, help="WxH px, e.g. 3200x2700")
    args = ap.parse_args(argv)
    canvas = None
    if args.canvas:
        cw, ch = args.canvas.lower().split("x")
        canvas = (float(cw), float(ch))
    try:
        budget = plan_city(CityProgram(population=args.population, river=args.river, agricultural_district=args.agri, aspect=args.aspect, nring=args.nring), canvas=canvas)
    except ValueError as e:
        import sys

        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(format_budget(budget))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
