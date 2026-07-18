# Contract: citybudget module API

The public surface of `.claude/skills/diagram/citybudget.py`. Consumers: pool gen scripts (`pool/*.gen.py`), `check_village.py` (the budget check re-derives expectations), tests.

## Functions

### `plan_city(program: CityProgram, canvas: tuple[float, float] | None = None) -> CityBudget`

- Deterministic, pure (no RNG, no I/O).
- Raises `ValueError` with a numeric, actionable message when: population outside [2000, 4000]; derived wall (+moat/margin allowance) exceeds `canvas` when one is given; a program combination is unsupported.
- The returned budget's lines sum exactly to `required_interior_px2`; `wall.interior_px2` is within `WALL_FIT_TOL` of required.

### `derive_wall(required_px2: float, *, aspect: float, nring: int = 20) -> WallSpec`

- Closed-form N-gon solve: `rx = sqrt(required / (0.5 * nring * sin(2*pi/nring) * aspect))`, `ry = aspect * rx`. Targets the drawn N-gon's polygon area, not the smooth ellipse (gen scripts draw 20-22-vertex rings; the smooth-ellipse formula would undersize every wall by the N-gon deficit).
- Only `shape="ring"` ships (research.md Decision 4: both shipped cities, including river-bank Nagahara, are full closed rings - the river never enters the walls). Exposed separately from `plan_city` so tests can property-check the geometry alone.

### `format_budget(budget: CityBudget) -> str`

- Human-readable itemized table: one row per BudgetLine (label, count, px^2, real acreage at ftpx, basis), totals, derived wall (rx/ry px, real-ft axes, perimeter, enclosed vs required delta %).
- RETURNS a string (Principle X: no print in library paths). The `python3 citybudget.py --plan ...` CLI entry may print it.

### `budget_to_manifest(budget: CityBudget) -> dict[str, object]`

- JSON-serializable dict for `M["budget"]` per the schema in data-model.md. Round-trips: `check_village` reads it without importing citybudget types.

## Gen-script usage contract (the new city workflow)

```python
from citybudget import CityProgram, plan_city, format_budget

prog = CityProgram(population=3000, river=True)
budget = plan_city(prog, canvas=(3200, 2700))
# print(format_budget(budget))  # audit before committing to a layout
RX, RY = budget.wall.rx, budget.wall.ry     # the wall is DERIVED, not guessed
...
s.meta(..., budget=budget_to_manifest(budget))
```

Order of operations (extends the render-order doctrine in settlements.md): **budget -> wall -> river/moat -> roads -> ring -> gates -> canal/dock -> quarters -> civic -> packs -> top-up**. The budget's `dwelling_target` feeds the same population/caste floors the checks already enforce.

## Check contract (`check_village.py::city_wall_matches_budget`)

Scope: `meta.scale == "city" and meta.walled`.

1. `M["budget"]` missing -> FAIL ("budget-first is the city workflow").
2. Measured enclosed interior area (same measurement `city_capacity` uses) vs `budget.required_interior_px2`:
   - `measured > required * (1 + BUDGET_TOL_OVER)` -> FAIL (enclosing unjustified ground - the empty-space defect).
   - `measured < required * (1 - BUDGET_TOL_UNDER)` -> FAIL (wall cannot hold the program).
3. Tolerances are module constants with "why" comments; calibrated so shipped Tango PASSES and pinned pre-feature Nagahara FAILS (research.md sets the values).

Red-green order: fixture pinned + check lands red against it BEFORE the generator work; Tango must stay green the whole time.

## CLI

`python3 citybudget.py --plan --population 3000 --river [--agri] [--canvas 3200x2700]` prints `format_budget` output. Exit 1 on `ValueError` with the message on stderr. (Thin wrapper; logic stays importable + covered.)
