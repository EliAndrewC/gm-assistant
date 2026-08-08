# Implementation Plan: Domain-capital space budget and tier declaration

**Branch**: none - this project stays on `main`; the active feature is carried by `export SPECIFY_FEATURE=018-capital-space-budget` | **Date**: 2026-08-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/018-capital-space-budget/spec.md`

## Summary

Give the domain-capital tier its first principle: a **space budget** that derives the wall from a declared program, exactly as feature 009 did for provincial cities. The capital cannot borrow the provincial model, because a median castle alone is ~85% of an entire provincial city's interior, so population predicts a capital's size badly.

The chosen approach is a **parallel entry point, not a widened one**: a new `CapitalProgram` dataclass and a new `plan_capital()` function beside the existing `CityProgram` / `plan_city()`, sharing the primitives (`BudgetLine`, `WallSpec`, `derive_wall`, `budget_to_manifest`, `format_budget`) but not the inventory logic. The provincial path therefore executes **zero new branches**, which is the strongest available guarantee for the byte-identity constraint.

This feature draws nothing. It adds a tier nothing yet uses, and the pool must come out byte-identical.

## Technical Context

**Language/Version**: Python 3.14 (the container pin)

**Primary Dependencies**: none new - `citybudget.py` is pure stdlib (`dataclasses`, `math`, `argparse`) and stays that way

**Storage**: N/A - the budget is computed, echoed into a manifest's `meta.budget`, and read back by the validator

**Testing**: pytest, in `.claude/skills/diagram/test_citybudget.py` (extends the existing file) and `test_checks.py` for the validator side

**Target Platform**: the `/diagram` skill's toolchain, run from a session clone

**Project Type**: single pure-logic module plus a validator extension - no UI, no service

**Performance Goals**: N/A - the budget is arithmetic over a few dozen lines; it runs once per gen

**Constraints**: every existing shipped settlement MUST regenerate byte-identically; the provincial band's raise-don't-clamp behavior MUST survive unchanged; budget line ORDER is manifest bytes and must not churn

**Scale/Scope**: one new dataclass, one new planning function, one new civic program table, two new ground-cost constants, two new validator checks, and their tests

## Constitution Check

*GATE: passed before Phase 0; re-checked after Phase 1 design - see "Post-design re-check" below.*

- **I. Accessibility-First Viewports**: **N/A** - no UI. This feature ships a pure-logic module and a validator check; nothing renders.
- **II. Bold, Intentional Design**: **N/A** - no new UI surfaces.
- **III. Pool Data Conventions**: **N/A** - no pool content is added or modified. The feature adds no map, and the existing pool must come out byte-identical.
- **IV. One Canonical Home for GM Source**: **N/A** - no SOURCE blocks are added or moved.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: **PASS** - no task touches content inside SOURCE markers.
- **VI. Verify Before Reporting Done**: **PASS** - every task names its verification. Pure logic: `ruff check` + `ruff format --check` + `mypy --strict` + `pytest -n auto` + `--cov-fail-under=100`. The byte-identity claim is verified by the full pool sweep (`make done` runs `test_villages.py`, which regenerates every map), not asserted.
- **VII. De-Localized Generation by Default**: **PASS** - the tier is generic. No city is baked in: Shiro Daika appears in the docs as the *planned* first example and in no code path. Clan identity changes labels only (GM 2026-08-08), so there are no clan-specific program rows.
- **VIII. Direct Voice Over Framing Distance**: **N/A** - no in-world prose is generated.
- **IX. Setting Integration**: **PASS** - every number comes from `budgets.md` (the capital caste table, the rank distribution) or from the recorded research; cross-referenced in `research.md`. No setting detail is invented.
- **X. Python Discipline (NON-NEGOTIABLE)**: **PASS** - committed to in full: ruff check + format, `mypy --strict`, red-green TDD (each new behavior's test lands failing first), 100% line coverage on the new logic, no swallowed exceptions, no `print` outside the CLI entry point, behavior-named tests, and `pytest.mark.parametrize` for the knob-validation matrix. No new dependencies, so the lockfiles do not move.
- **XI. Japanese Authenticity (NON-NEGOTIABLE)**: **PASS** - the terms this feature encodes in comments and labels (*yashiki*, *kuramai*, *hanko*, *kakehi*, *josui*, *zhalan*) each pass the kanji/romaji/meaning triangle and are used in their attested senses; see `research.md`, which carries the sources.
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: **Opening gate PASS; closing gate TRANSFERRED to feature 019** - see the dedicated section below, and the Complexity Tracking entry.

### Principle XII in detail

This feature does change what a generator asserts about the world - it asserts how much ground a domain capital covers and what institutions occupy it - so the principle applies.

**Opening gate: PASS.** The research was done BEFORE this spec was written and is recorded in [`research/cities/capitals.md`](../../.claude/skills/diagram/research/cities/capitals.md), with [`research.md`](research.md) here summarizing what each budget number rests on. For every element: what the historical reality was (China-first where China has something to say, Japan leading at this tier by a *disclosed and justified* inversion), whether the design matches, and **what determines the element in reality**. Two designs were changed at this gate rather than implemented and revisited, which is the gate working:

- an "ashigaru terrace" line was **dropped** - Rokugani ashigaru are peasants living in villages, so the institution does not exist here - and replaced with a retainer terrace for junior samurai;
- and the same correction reversed its **quantity**, because the capital's rank mix is 70% senior against a provincial city's 27%.

**Closing gate: TRANSFERRED, and this is the one judgment in the plan the GM should see.** The closing gate demands re-examining the *rendered artifact*. **This feature renders nothing**, so there is no artifact to examine - the gate is vacuous here rather than violated. The obligation does not evaporate: it transfers to feature 019 (the drawn capital), where the first Shiro Daika PNG must be examined against these Phase 0 findings before that feature is done. Recorded in Complexity Tracking so the transfer is visible rather than assumed, and restated in this feature's `quickstart.md`.

### Post-design re-check (after Phase 1)

Re-run against the completed design artifacts: no gate status changed. The design adds no UI, no pool content, no dependency, and no new external boundary; the only additions are a frozen dataclass, a pure function, two constants, one table, and two validator checks - all inside the existing Principle X envelope.

## Project Structure

### Documentation (this feature)

```text
specs/018-capital-space-budget/
├── plan.md              # This file
├── research.md          # Phase 0 - the historical + calibration basis of every number
├── data-model.md        # Phase 1 - entities, fields, validation rules
├── quickstart.md        # Phase 1 - how to audit a capital budget
├── contracts/
│   └── capitalbudget-api.md   # Phase 1 - the public surface
├── checklists/
│   └── requirements.md  # Spec quality checklist (from /speckit-specify)
└── tasks.md             # Phase 2 - NOT created by /speckit-plan
```

### Source Code (repository root)

```text
.claude/skills/diagram/
├── citybudget.py            # EXTENDED: CapitalProgram, plan_capital, the capital
│                            #   constants and civic program, CLI --tier
├── check_village.py         # EXTENDED: capital_wall_matches_budget,
│                            #   capital_declares_a_budget
├── test_citybudget.py       # EXTENDED: the capital budget's tests
├── test_checks.py           # EXTENDED: the two new checks' tests + fixtures
├── settlements/capitals.md  # UPDATED: point the tier doc at the shipped surface
└── research/cities/capitals.md  # UPDATED: mark the constants as shipped
```

**Structure Decision**: the feature extends two existing modules in place rather than adding a new one. `citybudget.py` is already the single home of budget-first sizing and its docstring says so; splitting the capital into a sibling module would put two halves of one concept in two files and duplicate `derive_wall`, `BudgetLine` and the serializer. The pure-logic/validator split already in place is the right seam and is preserved.

## The central design decision: a parallel entry point

The spec's hardest constraint is FR-016 - every shipped city reprices byte-identically - against FR-001, a capital band that must not widen the provincial one. Three options were weighed:

| Option | How | Rejected / chosen because |
|---|---|---|
| **Tier discriminator on `CityProgram`** | `tier: str = "provincial"`, branches inside `plan_city` | **Rejected.** Puts capital branches on the provincial code path, so the byte-identity guarantee becomes "the branches were written correctly" rather than "that code did not change". The two tiers also differ in inventory *structure* - three samurai housing types against one, a castle line, no agricultural district - so the shared function would be mostly branching anyway. |
| **Subclass `CapitalProgram(CityProgram)`** | inheritance + overrides | **Rejected.** Inherits `agricultural_district` and the provincial band as *meaningful* fields when they are not, and still leaves the branching problem in `plan_city`. A capital is not a kind of provincial city. |
| **Parallel `CapitalProgram` + `plan_capital()`** | new dataclass, new function, shared primitives | **CHOSEN.** The provincial path executes zero new branches, so byte-identity is guaranteed structurally rather than by test. Line order cannot churn because the provincial line sequence is untouched code. Each tier validates its own band, so FR-013's raise-don't-clamp survives on both sides independently. |

**What is shared, deliberately**: `BudgetLine`, `WallSpec`, `CityBudget`, `derive_wall`, `budget_to_manifest`, `format_budget`. These are tier-agnostic - a budget line is a budget line - and duplicating them is how two correct implementations of one idea start to drift (the same lesson the skill's dev-loop doc records for `edge_gap` and `_fr_gap`).

**The one accommodation this requires**: `budget_to_manifest` serializes `flags` from `program.river` and `program.agricultural_district`. `CapitalProgram` therefore carries `agricultural_district` as a field that is **always False**, documented at the point of definition as "a capital walls its farms out (GM 2026-08-08); the field exists so the shared serializer needs no tier branch." Validated to be False rather than merely defaulted, so a caller cannot set it and get a silently mis-priced wall.

## The validator side

Two checks, both scoped to `meta.scale == "capital"`:

- **`capital_wall_matches_budget`** - the sibling of `city_wall_matches_budget`, reusing the same tolerances (over by more than **+8%** = the empty-space defect; under by more than **-5%** = the program does not fit). The tolerances are inherited deliberately rather than re-derived: they are pinned by the shipped-Tango / rejected-Nagahara pair, and nothing about a capital argues for different slack.
- **`capital_declares_a_budget`** - the FR-015 ratchet. A capital manifest with no `meta.budget` **fails**, rather than skipping the conformance check and showing green. This is modeled directly on `settlement_declares_a_land_fall`, and it exists because the skill's dev-loop doc records three separate occasions where a rule gated on an optional declaration silently never ran while the gate stayed green: *"a check that never RUNS looks exactly like a check that passes."*

Both are additive and scoped, so no existing map runs them.

## Verification strategy

Ordered cheapest-first, per the skill's dev-loop doc:

1. `python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy`
2. `python3 -m pytest test_citybudget.py test_checks.py -q -n auto --no-cov` - the WHOLE files for the modules touched, never a `-k` subset
3. `make done` once, backgrounded, not polled - this runs `test_villages.py`, which regenerates every pool map, and is what actually PROVES the byte-identity claim rather than asserting it
4. `git status --porcelain` over `pool/` - any dirty tracked manifest means the feature moved a shipped map and the claim is false

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Principle XII closing gate transferred to feature 019** | The closing gate examines a RENDERED ARTIFACT. This feature deliberately renders nothing - it is the budget half of a two-feature tier, and the project's own budget-first doctrine requires the budget to land before anything is drawn. | Drawing a throwaway capital map inside this feature purely to satisfy the gate would produce an artifact built on unreviewed glyphs, which is a worse basis for a historical-grounding judgment than no artifact at all. The obligation is transferred, not dropped: feature 019's plan MUST carry the closing gate against the first Shiro Daika render, checked against this feature's `research.md`. |
| **`CapitalProgram.agricultural_district` exists but is always False** | The shared `budget_to_manifest` serializer reads it; carrying the field avoids a tier branch inside shared code. | Branching the serializer on tier would put capital-aware code on the provincial serialization path - the exact thing the parallel-entry-point decision exists to avoid. The field is validated False, not merely defaulted, so it cannot be misused. |
