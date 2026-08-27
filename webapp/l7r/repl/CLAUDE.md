# `l7r.repl` - the GM's Python REPL

`scripts/repl.py` (repo root) drops the GM into a Python prompt with the campaign tools loaded:
dice (`d10`, `xky`, `initiative`, `percent`), exact roll-and-keep odds (`prob`, `dist`), and
pool-backed picks (`name`, `names`, `bank`, `place`). It replaced the GM's copy-paste
`current/dice.py` (2026-08-27); function names and signatures were kept so muscle memory works.

| file | holds |
|---|---|
| `__init__.py` | `namespace()` - what the prompt starts with - and the `COMMANDS` banner. **Add a function to `__all__` and `COMMANDS` and it is at the prompt.** |
| `dice.py` | the rolls and the EXACT XkY distribution (a DP over "how many dice are still >= t"; the docstring has the math). `prob(6, 3)` is a `Dist` that compares and formats as its mean; `prob(6, 3, 20)` is P(>= 20); `prob(6, 3, table=True)` prints a TN table. `prob[6, 3]` / `prob[6, 3, 20]` is dict-style indexing with rerolls on; `prob[False][6, 3]` (and the old `prob[True][6, 3]`) selects reroll explicitly. |
| `names.py` | `name` / `names` / `bank` go through `chargen.namepool.pick_name` - the chargen engine's own picker - so a REPL pick excludes every name in use (the OP roster, `used-names-extra.txt`, every character in a group on the character-sheet app via `chargen/sheetroster.py`, and every family / house / lineage name from OP `<X> Lineage` tags and the chargen `[family]` / `[house]` / `[provincial_lineages]` config via `chargen/placeuse.py` - the Obana case) and is set-distinct within a call. The REPL's roster window is SIX hours (`MAX_AGE`; the `/name` skill keeps one), and `shell.py` starts a daemon thread at the prompt that runs `warm_caches()` so the refresh never blocks the prompt (`cache_status()` says what it found; a pick during the refresh waits on `_refresh_lock`). `place()` excludes names in use at the requested scale - OP tags like `Nagahara province` / `Hayakawa county` / `Hoshigaoka village` / `<x> hamlet`, plus the provinces every house holds in `development-defaults.ini` `[locations]` - via `chargen/placeuse.py`, which records why exclusion is per scale. `place(scale)` reads the place-name pool; `province_name()` / `town_name()` / `village_name()` / `hamlet_name()` are its aliases. Both return a `Pick`: a `str` with `.explanation` and `.entry`. |
| `sheets.py` | the PCs with Discern Honor (`PCS`: Jimen, Tetsuro, Makoto - add a `PC(name, sheet_id)` line to add one) and their public sheets on l7r-character-sheet.fly.dev. `resolve_pc` takes `"Jimen"` / `"Tsuruchi Jimen"` / `TSURUCHI_JIMEN` / `TsuruchiJimen`, and the same forms are REPL constants. `knack_rank(pc)` parses the knack's filled dots off the sheet HTML (no JSON route exists; fixture `tests/fixtures/sheets/jimen.html` is a trimmed real page) with a 24 h cache in `opcache/sheet-knacks.json` (GM: ranks change rarely). |
| `honor.py` | (PC rank comes off their sheet - `rank=` overrides, and is required for an unregistered PC; Unconventional / Virtue belong to the TARGET and are read from the NPC's OP notes: `Unconventional` always reads low on the first conversation, `Virtue` always high.) `discern_honor(npc, pc, rank=None, upload=True)` - the Discern Honor school knack (`rules/05-school_knacks.md` in the l7r repo). Reads the NPC's true Honor from the `Honor: X.Y` line of the OP GM-only notes, resolves the NPC name with `opsynth.match_character` (whole name tokens only: "Sakura" / "Reiji Sakura" / "Hida Sakura" / "Hida no Reiji Sakura" all work, "Saku" does not; an ambiguous match is an error listing the candidates), keeps a `Discern Honor:` block in those notes - one `- PC (rank N): told X.Y after N conversations` line per PC - and moves the told value `0.rank` closer per conversation until it locks in. The module docstring records the rules-typo decision (`- 5`, not `- 0.5`). |
| `shell.py` | readline + tab completion + `~/.l7r_repl_history`; sets the terminal title to `L7R repl >>>` (OSC 0, only on a TTY); `repl.py 'xky(6, 3)'` runs the argument and exits (a lone expression echoes its value; a multi-line quoted script just runs), `-i` stays. |

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
