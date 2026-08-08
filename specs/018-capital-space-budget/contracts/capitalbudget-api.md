# Contract: the capital budget's public surface

The `/diagram` skill has two consumers of `citybudget.py` - a **gen script** (which declares a program and takes the wall) and the **CLI** (which the GM reads). This file pins what each is promised. Shapes are in [data-model.md](data-model.md).

## Python surface (consumed by a capital `.gen.py`)

```python
from citybudget import CapitalProgram, plan_capital, budget_to_manifest

budget = plan_capital(
    CapitalProgram(
        population=12_360,
        river=True,
        castle_seat="ring",
        imperial_granary_seat="wharf",
    ),
    canvas=(W, H),
)

RX, RY = budget.wall.rx, budget.wall.ry      # never hand-picked
s.meta(scale="capital", budget=budget_to_manifest(budget))
```

### Guarantees

1. **`plan_capital` is pure and deterministic.** Same program in, same budget out, every time. No I/O, no randomness, no clock.
2. **The wall is an OUTPUT.** `budget.wall.rx/.ry` is the ring to draw. A gen that hand-picks semi-axes and declares a budget beside them is misusing the module, and `capital_wall_matches_budget` will catch the mismatch.
3. **Illegal programs cannot be constructed.** Validation is in `CapitalProgram.__post_init__`, so a caller never holds a program that `plan_capital` would reject. Every raise names the offending value and the legal range or set.
4. **Never clamps.** A population outside the band, a castle outside the 50-230 ha band, or a derived wall that will not fit the declared canvas raises with the numbers stated.
5. **Lines sum exactly** to `required_interior_px2`.
6. **`budget_to_manifest` output is manifest bytes.** Its shape is unchanged from the provincial tier - adding a key would dirty every shipped city, so the capital adds none. The capital's extra information rides in the existing `dwelling_target` dict.

### What this contract deliberately does NOT promise

- **No drawing.** This feature adds no glyph, no check on drawn features, and no map. `dwelling_target` tells a future gen what to deliver; nothing yet delivers it.
- **No stability of the constants.** `C_YASHIKI` and `C_TERRACE` are provisional and documented as such; they will be re-derived against the first drawn capital, exactly as `C_PACKED`/`C_SPACED` were back-predicted from Tango. A consumer must not depend on their current values.

## CLI surface (consumed by the GM)

```
python3 citybudget.py --plan --tier capital --population 12360 --river
python3 citybudget.py --plan --population 3000 --river          # unchanged, provincial
```

### Guarantees

1. **`--tier` defaults to `provincial`**, so every existing invocation behaves exactly as before - including its flags, its output format, and its exit codes.
2. **Every line prints its basis.** Label, count, ground in px^2, ground in acres, and the one-line "why". A reader can trace any number without opening the source (SC-004).
3. **A refusal prints the reason to stderr and exits non-zero**, with the offending number in the message.
4. `--agri` is **rejected** with `--tier capital` rather than silently ignored - a capital walls its farms out, and silently dropping a flag the GM typed is how a wrong wall gets trusted.

## Validator surface (consumed by `check_village.py`)

A capital manifest promises:

| `meta` key | Required | Meaning |
|---|---|---|
| `scale` | yes | `"capital"` - what scopes both new checks |
| `budget` | **yes** | `budget_to_manifest(...)` output. **Absent is a FAILURE**, not a skip (FR-015). |

`capital_wall_matches_budget` holds the drawn interior to `budget.required_interior_px2` at **+8% / -5%**, and `capital_declares_a_budget` is the ratchet that stops the first check from being silently skippable.

Both checks are scoped to `scale == "capital"`, so **no existing map runs either of them** - which is also why the pool must come out byte-identical.
