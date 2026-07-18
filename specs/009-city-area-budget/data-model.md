# Data Model: Budget-First City Wall Sizing

All entities live in the new pure-logic module `.claude/skills/diagram/citybudget.py` (mypy --strict, 100% coverage). Concrete calibration constants come from [research.md](research.md); this file defines shapes and rules.

## CityProgram (input)

The declaration the GM/gen script makes before anything is drawn.

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| `population` | int | required | In-wall settled population; canonical band 2,000-4,000. Validated: outside the band is an error (capitals are a future tier). |
| `ftpx` | int | 3 | Scale (1px = N ft). Cities are 3 by the scale ladder; parameterized, not hardcoded. |
| `river` | bool | False | River-bank city: wall is an open arc closed by the bank; wharf/canal/dock program lines activate. |
| `agricultural_district` | bool | False | Tango-style in-wall farms; adds the agri-district line to the budget. |
| `aspect` | float | ~0.93 | Target RY/RX ratio for the wall ellipse (both shipped cities are near-round; kept declarative). |
| `extras` | list[BudgetLine] | [] | City-specific itemized additions (e.g. an oversized temple precinct) so one-off program features stay auditable rather than fudged. |

Derived, not declared: households = population / 5; per-caste family counts from the budgets.md Provincial city caste mix (fractions of 600 families at pop 3,000, scaled linearly): servants 20%, laborers 40%, merchants 25%, burakumin 5%, samurai 10%. Zero farmers unless `agricultural_district` (which adds farmhouses as walled residents, matching the existing `city_capacity` convention).

## SpacingClass (enum)

`PACKED` - contiguous row housing (laborer, servant, burakumin, merchant): party walls, eave gaps, roji share. Gross ground cost per dwelling = drawn footprint + packed overhead (calibrated on Tango).
`SPACED` - courtyard/margin kinds (samurai houses, temples, civic compounds): gross cost = drawn footprint + measured margin overhead.

Every inventory kind carries exactly one SpacingClass. The class determines which calibrated overhead multiplier applies - never per-city fudge factors.

## BudgetLine

One auditable row of the budget report.

| Field | Type | Meaning |
|-------|------|---------|
| `label` | str | Human-readable ("laborer row housing", "6 ministries", "circulation @ N%") |
| `count` | int \| None | Number of items (None for area-only lines like circulation) |
| `area_px2` | float | Gross ground cost in px^2 at the declared ftpx |
| `basis` | str | One-line "why" - the source of the number (caste table, calibration constant, research figure). Required: every line is traceable (FR-007, SC-005/006). |

## CityBudget (output of `plan_city`)

| Field | Type | Meaning |
|-------|------|---------|
| `program` | CityProgram | Echo of the input |
| `lines` | list[BudgetLine] | Itemized: per-caste dwellings, shops, civic program, non-building features, reserves, circulation |
| `required_interior_px2` | float | Sum of lines |
| `wall` | WallSpec | Derived wall parameters |
| `dwelling_target` | dict[str, int] | Per-kind dwelling counts the packer must deliver (feeds the existing population/caste checks) |

Rules:
- Lines sum EXACTLY to `required_interior_px2` (property-tested).
- Circulation is computed on interior area, so it appears as a solved fraction: `circ = f/(1-f) * sum(non-circ lines)` - documented in the module.
- The budget is recorded verbatim into the manifest (`M["budget"]`, JSON-serializable) by the gen script.

## WallSpec

| Field | Type | Meaning |
|-------|------|---------|
| `shape` | `"ring"` | Closed ellipse ring. Research finding (research.md Decision 4): BOTH shipped cities are closed rings - even river-bank Nagahara stands beside the river with a full ring (the river never enters the walls). The field exists so a future true bank-arc city can extend the enum; no arc solver ships now. |
| `rx`, `ry` | float | Semi-axes of the ring |
| `interior_px2` | float | Area actually enclosed by the derived N-gon (must be within tolerance of required). NOTE: gen scripts draw the wall as an ellipse N-gon (20-22 vertices) whose polygon area is slightly under pi*rx*ry - the derivation must target the N-gon area (`0.5*N*sin(2pi/N)*rx*ry`), not the smooth-ellipse area, or every wall comes out systematically small. |
| `perimeter_ft` | float | Reported for the GM sanity read (real-world wall length) |

Rules:
- Ring: N-gon area solved with the declared aspect: `rx = sqrt(required / (0.5*N*sin(2*pi/N) * aspect))`, `ry = aspect * rx` (N supplied by the caller; both shipped cities use 20-22).
- Canvas check: the caller passes canvas dims; if the wall + moat + margin cannot fit, `plan_city` raises with the numbers (edge case: budget/canvas conflict - never silently clamp).

## Manifest additions (`M["budget"]`)

```json
{
  "required_interior_px2": 0.0,
  "interior_px2": 0.0,
  "lines": [{"label": "...", "count": 0, "area_px2": 0.0, "basis": "..."}],
  "circulation_frac": 0.0,
  "flags": {"river": true, "agricultural_district": false}
}
```

Consumed by the new check `city_wall_matches_budget`:
- measured enclosed interior (computed the way `city_capacity` already measures it) vs `required_interior_px2`: fail if off by more than the tolerance IN EITHER DIRECTION (too much ground = the empty-space defect; too little = the packing grind).
- A walled city with NO `M["budget"]` fails the check (budget-first is now the required workflow for `scale="city"`; older non-city maps unaffected).

## Calibration anchors (fixtures)

- **Tango (known-good)**: `plan_city(tango_program)` must back-predict the shipped RX/RY within the calibration tolerance (unit test, not a map regen).
- **Pre-feature Nagahara (known-bad)**: current `pool/nagahara.json` pinned to `pool/regressions/` - must FAIL `city_wall_matches_budget` (and remains the visual definition of "too empty").
