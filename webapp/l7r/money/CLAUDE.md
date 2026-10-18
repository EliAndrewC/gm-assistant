# `l7r.money` - the `/money` skill's arithmetic and data (feature 219)

The skill itself is `.claude/skills/money/SKILL.md`; spec and decisions in `specs/219-money-skill/`. No webapp page.

| file | holds |
|---|---|
| `coins.py` | Exact coin arithmetic in whole sen: `parse`, `fmt`, `everyday` (the two largest coins, rounded). |
| `readings.py` | PPP dollars per koku from a basket snapshot and a koku of rice mass; "big deal" dollars from a wage; `laborer_days`. The why of each choice is in its docstring. |
| `ledger.py` | Load, validate and search the price ledger; the row rules are in its docstring. |
| `__main__.py` | The command line the skill runs (`convert`, `dollars`, `price`, `history`, `check`). |
| `data/baskets/YYYY-MM.json` | One dated re-pricing each. **Never edit an old one**; add a new file. |
| `data/wages.json` | Dated US unskilled wages for the "big deal" reading; newest is the default. |
| `data/ledger.jsonl` | The price ledger, one row per line, figures in sen. |

## Testing

```
( cd webapp && python3 -m pytest -n auto tests/test_money.py )
( cd webapp && python3 -m l7r.money check && python3 -m l7r.money convert 1 koku )
```

`test_2017_snapshot_reproduces_the_spreadsheet` pins the 2017 basket to the shared sheet ($797.22 = 144.32 zeni ->
$552 per koku); if it fails, an old snapshot was edited. `test_every_ledger_row_carries_label_and_source` loads the
real ledger, so a row without a label or source fails the gate.
