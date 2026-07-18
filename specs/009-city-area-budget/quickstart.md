# Quickstart: Budget-First City Wall Sizing

## Budget a brand-new city

```bash
cd /gm-assistant/.claude/skills/diagram
python3 citybudget.py --plan --population 2600 --river          # audit the itemized budget + derived wall
```

Read the report: every line has a basis (caste table / calibration constant / research figure). If the program needs a city-specific extra (a grand shrine precinct, a drill ground), add it as an `extras` BudgetLine in the gen script - never by inflating the wall by hand.

In the gen script (`pool/<name>.gen.py`):

```python
prog = CityProgram(population=2600, river=True)
budget = plan_city(prog, canvas=(W, H))
RX, RY = budget.wall.rx, budget.wall.ry
# ... place wall from RX/RY, then the normal render order ...
s.meta(..., budget=budget_to_manifest(budget))
```

Then the usual gate:

```bash
python3 pool/<name>.gen.py && python3 check_village.py pool/<name>.json
python3 check_village.py pool/<name>.json --capacity   # verdict must be sized_and_packed FIRST pass
```

## Verify the feature itself

```bash
cd /gm-assistant/.claude/skills/diagram
make done                          # ruff + format + mypy --strict + pytest + 100% cov
python3 -m pytest test_citybudget.py test_checks.py test_regressions.py -v
for m in pool/*.json; do python3 check_village.py "$m"; done   # every pool map green
```

Calibration invariants (unit-tested):
- Tango back-prediction: `plan_city(tango_program)` derives the shipped wall within tolerance.
- Pinned pre-feature Nagahara fixture FAILS `city_wall_matches_budget`.
- Band sweep: populations 2000/3000/4000 x {river, ring} x {agri on/off} all derive walls that pass their own budget check by construction.

## Regenerate Nagahara (the acceptance case)

```bash
python3 pool/nagahara.gen.py && python3 check_village.py pool/nagahara.json --capacity-map
rsvg-convert pool/nagahara.svg -o pool/nagahara.png   # (or the skill's usual render step)
```

Done means: all checks green, `sized_and_packed` first pass, AND the GM confirms the empty-space problem is gone on the rendered PNG.
