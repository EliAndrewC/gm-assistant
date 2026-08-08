# Implementation Plan: The capital map skeleton and the castle

**Branch**: none - this project stays on `main`; active feature via `export SPECIFY_FEATURE=019-capital-skeleton-castle` | **Date**: 2026-08-08 | **Spec**: [spec.md](spec.md)

## Summary

Draw the skeleton that feature 018's budget sizes, plus the castle, and stop. The castle is built FIRST because the GM marked its internal walls provisional and a skeleton is the cheapest, clearest condition under which to judge them.

Two recon findings shape the whole plan:

1. **`meta()` is already tier-generic.** `s.meta(scale="capital", ftpx=3)` sets `bscale = 1/3` with no change - the ftpx branch only special-cases `village`. So the tier needs no new declaration machinery.
2. **Only 12 sites in `settlement.py` branch on `scale == "city"`**, and every one of them is an "urban ring drawn at 3 ft/px" behavior a capital shares (execution-ground sizing, the walled-ring paths, grove suppression inside walls, street widths). So the plumbing is a **widening of those predicates**, not a parallel drawing path - the opposite of the decision feature 018 made for the budget, and for the opposite reason: there, the risk was repricing shipped cities; here, the shared behavior IS the correct behavior and duplicating it would fork the vocabulary.

## Technical Context

**Language/Version**: Python 3.14 | **Dependencies**: none new | **Testing**: pytest (`test_settlement.py`, `test_checks.py`, `test_villages.py`)

**Constraints**: the pool must stay byte-identical (no capital exists, so widening a predicate must not change any existing map's behavior); the castle must reserve its ground before any later placement; nothing may be drawn inside the castle.

**Scale/Scope**: one new drawn feature, one new gen, a widened set of scale predicates, capital-scoped checks, and a render at ~4,600 px.

## Constitution Check

- **I / II**: **N/A** - no UI.
- **III. Pool Data Conventions**: **PASS** - a new pool map under `pool/capitals/`, following the existing `pool/provincial-cities/` convention (gen + json + svg + gitignored png).
- **IV / V**: **N/A / PASS** - no SOURCE blocks touched.
- **VI. Verify Before Reporting Done**: **PASS** - linters, whole affected test files, `make done` once backgrounded, `git status -- pool/` for the untouched maps, plus the two artifact gates below.
- **VII. De-Localized Generation**: **PASS with a noted exception** - the tier machinery is generic; **Shiro Daika itself is deliberately campaign-specific**, which is the same standing exception every pool map takes (Tango, Nagahara, Ubame are all named places). Nothing city-specific enters the engine.
- **VIII**: **N/A** - no in-world prose.
- **IX. Setting Integration**: **PASS** - the roads, gates and geography come from the GM and the campaign map; the budget from `budgets.md`. No invented setting detail.
- **X. Python Discipline (NON-NEGOTIABLE)**: **PASS** - ruff, `mypy --strict`, red-green TDD, 100% coverage, behavior-named tests, parametrized variants.
- **XI. Japanese Authenticity**: **PASS** - *masugata*, *ote-mon*, *honmaru/ninomaru/sannomaru*, *ishigaki* all used in their attested senses (see 018's research.md).
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: **BOTH GATES DISCHARGED HERE.**
  - *Opening*: already done and recorded in [`../018-capital-space-budget/research.md`](../018-capital-space-budget/research.md) and `research/cities/capitals.md`. This feature adds no new world-assertion beyond drawing what that research settled, so it inherits rather than repeats the gate.
  - *Closing*: **transferred INTO this feature from 018**, and this is the feature that finally produces an artifact. Before done, the rendered Shiro Daika PNG is examined - the picture, not the code - against those Phase 0 findings. This is a task, not a sentiment (see tasks.md).

## The three design decisions

### 1. Scale plumbing: widen the predicates, do not fork the path

The 12 `scale == "city"` sites become a shared membership test. A capital IS an urban walled ring at the same grain, so it wants the same execution-ground sizing, the same in-wall grove suppression, the same street widths. **Byte-identity is preserved trivially** because no existing map declares `capital`, so no widened predicate changes any existing evaluation - but the pool sweep proves it rather than the argument.

### 2. The castle: a compound glyph with an empty court

Built on the `manor` / `governor_mansion` lineage, which already draws exactly what is wanted - walls, a gate, an empty court whose interior is a separate Mode A sheet - and extended with the three things a castle has and a manor does not:

- **its own moat** ringing the enceinte,
- **bailey walls** - concentric inner rings dividing sannomaru / ninomaru / honmaru,
- **a *masugata* gate approach** - the dogleg that turns an attacker twice.

All three are PROVISIONAL per the GM and switchable by one knob, so the verdict can be applied by flipping it rather than by unpicking the glyph. **No building is drawn inside, ever** - that is not a knob.

### 3. The castle reserves its ground in THIS feature

FR-006, and it is the one thing that would be expensive to defer. The enceinte is ~85% of a provincial city's interior, so feature 020's packers must flow around it. Per the skill's DRAW ORDER doctrine, a feature that must reserve ground has to run BEFORE placement and register in a registry the placer actually honors - and the two registries differ (`block_polys` is center-tested for urban packs; `placed` is distance-tested). The castle registers in **both**, because a half-overlapping building on a castle wall is exactly the class of defect that doctrine exists to prevent.

## Project Structure

```text
.claude/skills/diagram/
├── settlement.py                     # widened scale predicates; s.castle(...)
├── check_village.py                  # capital-scoped skeleton checks
├── test_settlement.py                # the castle glyph's tests
├── test_checks.py                    # the new checks' tests
├── test_villages.py                  # register the new gen + its CPU budget
├── pool/capitals/shiro-daika.gen.py  # NEW - the gen
├── settlements/capitals.md           # the bailey-wall VERDICT lands here
└── specs/019-capital-skeleton-castle/
```

**Structure Decision**: a new `pool/capitals/` directory, parallel to `pool/provincial-cities/`. The render-sync and cache paths glob `pool/*/*.gen.py`, so a new tier directory is picked up without wiring.

## Verification strategy

1. `ruff format` + `ruff check` + `mypy --strict`
2. whole affected test files, `-n auto`, never a `-k` subset
3. **render and LOOK** - the artifact gates, which no automated check can do:
   - Principle XII closing gate against 018's research.md
   - the bailey-wall verdict (US2)
   - `settlement-review`, scoped as a DELTA and launched the moment the map is final, not after the docs
4. `make done` once, backgrounded, never polled
5. `git status --porcelain -- pool/provincial-cities pool/towns pool/villages pool/hamlets` MUST be empty

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| A pool map named for a specific campaign place (Principle VII) | Every pool map is a named place; a tier is proven by drawing a real one. | A generic "Capital" exemplar would still have to choose roads, gates and a river, so it would be a specific place with a vague name - worse, not more general. The ENGINE stays generic; only the gen is specific. |
| The castle's internal walls create a Mode A sync surface | The GM decided to try them, judging that a 50 ha blank reads worse than the sync risk costs. | Not drawing them is the safe default and remains one flag away; the whole point of the feature order is that this is judged on evidence rather than argued. |
