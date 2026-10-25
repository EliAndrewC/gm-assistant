# Plan: Feature 223 - the goods-dollar koku as an index

**Spec**: `spec.md` (spec-fidelity: round 1 CHANGES REQUIRED, round 2 FAITHFUL). **Constitution**: one feature in the
existing `l7r.money` subsystem; no new dependency, no new route.

## Technical approach

| Piece | Where | What changes |
|---|---|---|
| Rokugan's prices | `basket.py` `Model.prices/weights/rests_on/reference_only` | Each good: rice anchor x weighted geometric mean over eras of (era price / era rice); borrowed prices out unless nothing else prices the good; all-zero weights fall back to Kyoto alone. |
| Era weights | `data/era-weights.json` (new) | `{"weights": {}}`: every era 1, provisional. `problems` refuses unknown eras and negatives. |
| Borrowed prices | `Price.borrowed`; written by `specs/222-.../measure/eras.py` | Kyoto 1745's Meiji-ratio goods, soybeans (= rice), edible oil (= lamp oil). |
| Readings | `basket.Reading` | `alone(line)`, `weighted`, `arithmetic`, `geometric`, `whole` ($D/N), `koku_cost` (N), `per_koku` by `mean`; `equal` weighting. |
| Complete baskets | `Basket.complete`; `standard.json` | Only complete baskets feed the whole-basket reading; `problems` needs one. |
| Era conversion | `basket.convert` | Price level by the chosen mean over shared goods; `goods_dollars` (central) and `goods_dollars_high` (arithmetic throughout). |
| Conversion table | `conversions.py` | Adds `goods_dollars_high` and top-level `mean`; nothing removed. Diagram told on diagram#17. |
| CLI | `__main__.py` | `--mean`, `--equal-weights`, `--reference-only`; outputs name both readings and the basis. |
| Page | `web.py`, `money_koku.html`, `money.js`, `money.css` | Both readings in the goods card; per-good weight, single-good koku and a log-scale dot track with the two readings as rules; mean and weighting controls; the periods panel with a weight per era; custom goods and toggles act on the average only. `money.js` mirrors `prices`/`reading`. |
| Docs | SKILL.md, `l7r/money/CLAUDE.md` | Goods dollars as a range; the knobs; how to test by hand. |

## Why these choices (recorded at the point of change too)

- Central = geometric, high = arithmetic (whole basket): `basket.py` docstring; spec Assumptions.
- Geometric across eras, not the knob: ratios; `basket.py` docstring.
- Per-row dot track instead of one strip chart: twelve labeled goods on one strip collide; aligned with the table,
  each dot sits beside its own name and numbers, and the two readings become rules through every row.

## Deferred, with its trigger

- Paasche/Fisher: when diagram#17 question 6 gives modern quantities (spec US2 acceptance 6).
- Re-priced snapshot (US6): when diagram#17 questions 1-3 answer; a new dated snapshot, never an edit.
- Other eras' borrowed/chained prices marked: when question 4 answers.

## Verification

Money test files (whole), `make done`, screenshots of `money-koku*` at all four viewports, `tests/dom_audit.py` at
zero issues, `frontend-review`.
