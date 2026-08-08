# Data Model: Domain-capital space budget

Everything lives in the existing pure-logic module `.claude/skills/diagram/citybudget.py` (mypy --strict, 100% coverage), beside the provincial entities it does not touch. Concrete numbers and their bases come from [research.md](research.md); this file defines shapes and rules.

## CapitalProgram (input) - NEW

The declaration made before anything is drawn. A **frozen dataclass**, parallel to `CityProgram` rather than derived from it (see [plan.md](plan.md), "The central design decision").

| Field | Type | Default | Meaning and validation |
|-------|------|---------|------------------------|
| `population` | `int` | required | In-wall settled population. Canonical **12,360**; band `CAPITAL_POP_MIN`/`MAX`. Outside the band **raises** with both figures stated - never clamps. |
| `ftpx` | `int` | `CAL_FTPX` (3) | Scale. Constants are calibrated at 3 ft/px and scale by `(3/ftpx)^2`, exactly as the provincial path does. |
| `river` | `bool` | `False` | River capital. Selects the water line's label, and **gates `castle_seat="edge"`**. |
| `agricultural_district` | `bool` | `False` | **Always False.** Present only so the shared `budget_to_manifest` needs no tier branch; a capital walls its farms out (GM 2026-08-08). **Validated False**, not merely defaulted - setting it True raises. |
| `aspect` | `float` | `0.93` | Target RY/RX of the wall N-gon, as provincial. |
| `nring` | `int` | `20` | Wall vertices. |
| `castle_seat` | `str` | `"ring"` | One of `CASTLE_SEATS = ("ring", "edge")`. **`"edge"` requires `river=True`** - every attested edge castle is a river or sea castle, and a castle on a dry edge is a weak wall, not a variant. Any other value raises with the legal set listed. |
| `castle_px2` | `float` | `CASTLE_PX2` (~598,000) | The castle's declared ground. Documented band **50-230 ha**; outside it raises, because a castle two orders of magnitude off is a program error the GM should see, not a wall. |
| `imperial_granary_seat` | `str` | `"magistrate"` | One of `IMPERIAL_GRANARY_SEATS = ("magistrate", "wharf")`. **Neither is privileged** - the default exists only because a dataclass field needs one, and the docstring says so. Any other value raises. |
| `temple_precincts` | `int` | `2` | Sovereign temples. Same knob shape feature 016 gave the provincial tier. |
| `temple_precinct_px2` | `float` | `SOVEREIGN_PRECINCT_PX2` | A sovereign temple is the head house of a domain-wide Order (50+ monks), so its default is larger than a provincial precinct's. |
| `monk_houses_per_precinct` | `float` | `2.5` | As provincial. |
| `extras` | `tuple[BudgetLine, ...]` | `()` | Itemized city-specific additions, so one-off program features stay auditable rather than fudged. |

**Validation happens in `__post_init__`**, so an illegal program cannot exist - a caller never holds a `CapitalProgram` that `plan_capital` would reject. Each raise names the offending value AND the legal alternatives (SC-005).

## Household inventory (derived, not declared)

`CAPITAL_FAMILIES` - absolute household counts from the `budgets.md` Capital city caste table, **not fractions of population**, because the capital carries two cohorts that sit *outside* the settled 12,000 breakdown:

| caste | households | note |
|---|---|---|
| servants | 480 | |
| laborers | 960 | |
| merchants | 600 | |
| burakumin | 120 | |
| samurai (domestic) | 240 | |
| samurai (relocated, non-working) | +72 | the schooling-and-retirement cohort |
| samurai (foreign, Imperial) | +12 | the Imperial Magistrate's office |
| farmers | **0** | a capital walls its farmland out |

Packed castes are the same four as provincial. The samurai total (312) is then split:

1. **In-wall**: `round(312 * CAPITAL_SAMURAI_INWALL_FRAC)` with the fraction ~0.85 (against the provincial 2/3).
2. **By rank band**, using `CAPITAL_RANK_BANDS` read off `budgets.md`'s capital rank column - **upper (R8-12) 20% -> walled yashiki, middle (R5-7) 50% -> detached house, junior (R1-4) 30% -> retainer terrace.** The bands are stored as the raw rank-table counts with the shares derived from them, so the split is traceable to a published table rather than three magic percentages.

## Ground-cost constants - NEW

| Constant | Value | Basis (carried in a comment at the definition) |
|---|---|---|
| `C_YASHIKI` | ~4,150 px^2 | Fukui Suginuma plan (1,000-koku retainer, 28 x 32.5 ken = ~167 x 194 ft = 3,600 px^2) + ~1.15x street margin |
| `C_TERRACE` | ~660 px^2 | Shibata ICP ashigaru-nagaya (378 sq ft/household) as floor, detached samurai house as ceiling. **The softest number in the feature**, and labeled so. |

`C_PACKED` and `C_SPACED` are reused unchanged.

## CAPITAL_CIVIC_PROGRAM - NEW

Same tuple shape as `CIVIC_PROGRAM`: `(label, count | None, row_total_px2)`.

**The row-total convention is the trap to respect**: every third field is the ROW TOTAL, not a per-unit cost. Reading it as per-unit is how feature 016 nearly doubled every city's temple ground, and the pinned shipped-program test is what catches it. The capital table gets its own pinned test for the same reason.

Rows: the six domain ministries and their government ward; the House Chancellery; the Imperial Magistrate's compound; the Emperor's granaries; the domain school; the domain granary with its brokers' row; the domain martial hall plus its rolled private dojos; the aqueduct's in-wall works (small - the conduit is buried and consumes almost no interior); minor civic; shops/inns/stables; the bell-and-drum tower; breweries; trade works.

The castle and the sovereign temples are **not** in this table - both are knob-driven declared lines, so they reprice when declared rather than being frozen into a program floor.

## CityBudget (output) - REUSED, one field widened

`plan_capital` returns the existing `CityBudget`. One change: `program` is typed `CityProgram | CapitalProgram`.

`budget_to_manifest` and `format_budget` touch only fields both types carry (`population`, `ftpx`, `river`, `agricultural_district`), so neither needs a tier branch - which is the whole reason `agricultural_district` exists on `CapitalProgram`.

`dwelling_target` gains the capital's extra keys (`samurai_yashiki`, `samurai_detached`, `samurai_terrace`) so the drawing feature can read the split it must deliver.

## Rules

- Lines sum exactly to `required_interior_px2` - property-tested, as provincial.
- Circulation is a solved fraction of the interior, not of the fixed subtotal.
- The provincial line SEQUENCE is untouched code; the capital has its own sequence, pinned by its own test the day it ships so it cannot churn silently later.
- **Every raise states the offending number and the legal range or set.** No silent clamping anywhere.

## Validator entities (check_village.py)

| Check | Scope | Rule |
|---|---|---|
| `capital_wall_matches_budget` | `meta.scale == "capital"` | Enclosed interior against `meta.budget.required_interior_px2`: over **+8%** = shrink (the empty-space defect), under **-5%** = enlarge (the program does not fit). Tolerances inherited from the provincial check deliberately - they are pinned by the shipped-Tango / rejected-Nagahara pair. |
| `capital_declares_a_budget` | `meta.scale == "capital"` | A capital manifest with no `meta.budget` **FAILS**. The FR-015 ratchet, modeled on `settlement_declares_a_land_fall`: without it, a capital that declares nothing would skip the conformance check and show green - and a check that never runs looks exactly like a check that passes. |
