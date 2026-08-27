# `l7r.repl` - the GM's Python REPL

`scripts/repl.py` (repo root) drops the GM into a Python prompt with the campaign tools loaded:
dice (`d10`, `xky`, `initiative`, `percent`), exact roll-and-keep odds (`prob`, `dist`), and
pool-backed picks (`name`, `names`, `bank`, `place`). It replaced the GM's copy-paste
`current/dice.py` (2026-08-27); function names and signatures were kept so muscle memory works.

| file | holds |
|---|---|
| `__init__.py` | `namespace()` - what the prompt starts with - and the `COMMANDS` banner. **Add a function to `__all__` and `COMMANDS` and it is at the prompt.** |
| `dice.py` | the rolls and the EXACT XkY distribution (a DP over "how many dice are still >= t"; the docstring has the math). `prob(6, 3)` is a `Dist` that compares and formats as its mean; `prob(6, 3, 20)` is P(>= 20); `prob(6, 3, table=True)` prints a TN table. `prob[True][6, 3]` is the old dict-style indexing. |
| `names.py` | `name` / `names` / `bank` go through `chargen.namepool.pick_name` - the chargen engine's own picker - so a REPL pick excludes the campaign roster (cache refreshed if > 1 h old, fail-soft) and is set-distinct within a call. `place(scale)` reads the place-name pool. Both return a `Pick`: a `str` with `.explanation` and `.entry`. |
| `shell.py` | readline + tab completion + `~/.l7r_repl_history`; `repl.py 'xky(6, 3)'` runs the argument and exits (a lone expression echoes its value; a multi-line quoted script just runs), `-i` stays. |

Design notes:

- **Printing is the interface** - every pick prints its meaning and every `xky` prints its dice,
  so `l7r/repl/**` is exempt from ruff's T20 in `pyproject.toml`. Functions still RETURN real
  values (`Pick` is a `str`), so they compose in a snippet.
- **`>=` not `>`.** The old Monte Carlo table counted `P(result > tn)`; the new one counts
  `P(result >= tn)`, which is the actual L5R success test. Deliberate, not a port bug.
- **`names` the function shadows `l7r.repl.names` the module** on the package; tests reach the
  module through `importlib.import_module`.

## Testing

```
( cd webapp && pytest -n auto tests/test_repl_dice.py tests/test_repl_names.py tests/test_repl_shell.py )
```

The names tests read the REAL pools but fixture the campaign roster (no Obsidian Portal call).
Hand-check: `./scripts/repl.py 'prob(6, 3, table=True)'` and `./scripts/repl.py 'bank(2)'`.
