# Quickstart: auditing a domain-capital budget

## See where a capital's ground goes

```bash
cd .claude/skills/diagram
python3 citybudget.py --plan --tier capital --population 12360 --river
```

Every line prints its label, count, ground in px^2 and acres, and the **basis** - the one-line reason that number is what it is. Read it before building anything: this is where a mis-priced program is cheap to catch.

The provincial invocation is unchanged:

```bash
python3 citybudget.py --plan --population 3000 --river
```

## Use it from a gen

```python
from citybudget import CapitalProgram, plan_capital, budget_to_manifest

budget = plan_capital(CapitalProgram(population=12_360, river=True), canvas=(W, H))
RX, RY = budget.wall.rx, budget.wall.ry      # take the wall; never hand-pick it
s.meta(scale="capital", budget=budget_to_manifest(budget))
```

**The wall is an output.** If a capital's ground will not take its program, the answer is to grow the wall from the budget or trim the program - never to shrink the declared population to fit the layout.

## Try the knobs

```python
CapitalProgram(population=12_360, river=True,  castle_seat="edge")       # ok
CapitalProgram(population=12_360, river=False, castle_seat="edge")       # raises - a castle
                                                                          # on a dry edge is a
                                                                          # weak wall, not a variant
CapitalProgram(population=12_360, imperial_granary_seat="wharf")          # ok - neither seat
                                                                          # is privileged
CapitalProgram(population=12_360, castle_px2=40_000.0)                    # raises - outside the
                                                                          # documented 50-230 ha band
```

## Verify a change to this module

Cheapest first, per the skill's dev-loop doc:

```bash
python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy
python3 -m pytest test_citybudget.py test_checks.py -q -n auto --no-cov   # WHOLE files, never -k
make done                                                                 # once, backgrounded
git status --porcelain -- pool/                                           # must be EMPTY
```

That last line is the real proof of this feature's central claim. The tier is additive and nothing uses it yet, so **any dirty tracked file under `pool/` means a shipped map moved** and the byte-identity claim is false.

---

## Inherited obligation for feature 019

**Principle XII's closing gate was TRANSFERRED out of this feature, not satisfied by it.** This feature renders nothing, so there is no artifact to examine. The obligation is real and lands on the feature that draws the first capital:

> Before feature 019 is done, examine the rendered Shiro Daika PNG - the picture, not the code and not the intent - and confirm each element still matches the Phase 0 findings in [research.md](research.md). `check_village` proves internal consistency, never historical truth.

Feature 019's plan must carry this explicitly. It is recorded here, in [plan.md](plan.md)'s Constitution Check, and in its Complexity Tracking table, so the transfer cannot be quietly lost.
