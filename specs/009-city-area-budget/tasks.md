# Tasks: Budget-First City Wall Sizing

**Input**: Design documents from `/specs/009-city-area-budget/`

**Prerequisites**: plan.md, spec.md, research.md (calibration constants + historical grounding), data-model.md, contracts/citybudget-api.md

**Tests**: INCLUDED - red-green TDD is constitutional (Principle X) and the skill's check discipline is red-first against pinned fixtures.

**Organization**: grouped by user story. US1 = the budget engine + check (core inversion), US2 = Nagahara regenerated, US3 = agricultural-district toggle surface.

**Concurrency caution (applies to every task)**: a parallel session is editing `settlement.py` / `check_village.py` for village work. Keep edits to those two files additive and text-anchored; on "file modified since read" re-grep the anchor and retry; re-run the full suite before reporting done.

## Phase 1: Setup

- [X] T001 Register the new module with the quality gate: add `citybudget.py` to the mypy `files` list in `/gm-assistant/.claude/skills/diagram/pyproject.toml` (strict from day one, no ratchet entry)

## Phase 2: Foundational (blocking prerequisites)

- [X] T002 Pin the known-bad anchor: copy the CURRENT `/gm-assistant/.claude/skills/diagram/pool/nagahara.json` to `/gm-assistant/.claude/skills/diagram/pool/regressions/city_budget_fires_on_the_too_empty_nagahara.json` unchanged (this is the GM-rejected map the new acceptance line must fail; do this BEFORE any regen touches nagahara.json)
- [X] T003 Wire the fixture into the regression suite per the corpus convention in `/gm-assistant/.claude/skills/diagram/test_regressions.py` (and `make_regressions.py` if the convention requires an entry), asserting the fixture FAILS `city_wall_matches_budget` - expected RED until T008 lands the check; leave it xfail-free (a plain failing test) per the red-first discipline

## Phase 3: User Story 1 - Derive the wall from the space budget (P1)

**Goal**: `plan_city(program)` turns population + program into an itemized budget and a derived wall; new check compares promised vs delivered; Tango back-predicts.

**Independent test**: `python3 citybudget.py --plan --population 3000 --river` prints an auditable budget whose lines sum to the required interior and whose derived wall matches it; `pytest test_citybudget.py` green incl. the Tango back-prediction; `city_wall_matches_budget` red on the pinned fixture, green on Tango.

- [X] T004 [US1] Write `test_citybudget.py` RED in `/gm-assistant/.claude/skills/diagram/test_citybudget.py`: (a) inventory derivation from the budgets.md caste mix (pop 3000 -> 600 families: servants 120 / laborers 240 / merchants 150 / burakumin 30 / samurai 60; linear scaling at 2000/4000; ValueError outside the band); (b) lines sum exactly to `required_interior_px2`; (c) circulation solved as `f/(1-f)` of non-circulation lines at f=0.07; (d) `derive_wall` targets the N-gon area (`0.5*N*sin(2pi/N)*rx*ry`), respects aspect, round-trips enclosed-vs-required within tolerance; (e) canvas-conflict ValueError carries the numbers; (f) agricultural-district toggle adds exactly its itemized line (delta test); (g) TANGO BACK-PREDICTION: the Tango program (pop 3000, agri on, its measured extras) derives RX/RY within the calibration tolerance of the shipped 487x457; (h) NAGAHARA MISMATCH: the pre-feature program (pop 3000, river, no agri) prices required interior far enough below the pinned fixture's measured ~702k px^2 interior to breach the over-enclosure tolerance; (i) `budget_to_manifest` round-trips JSON-serializably; (j) `format_budget` includes every line's basis and the wall figures. Behavior-named tests, parametrized where inputs vary
- [X] T005 [US1] Implement `/gm-assistant/.claude/skills/diagram/citybudget.py` GREEN per contracts/citybudget-api.md: `CityProgram` / `BudgetLine` / `CityBudget` / `WallSpec` dataclasses, `plan_city`, `derive_wall` (ring N-gon closed form), `format_budget` (returns str), `budget_to_manifest`, thin `--plan` CLI. Every calibration constant carries its measured/researched "why" comment citing research.md (C_packed ~800 px^2, C_spaced ~2900 px^2, itemized civic program lines summing to the measured ~62-64k, circulation 0.07, tolerances sized so Tango passes and pre-feature Nagahara fails)
- [X] T006 [US1] Run the module gate: `make done` in `/gm-assistant/.claude/skills/diagram/` (ruff + format + mypy --strict + pytest incl. 100% coverage of citybudget.py); fix fallout
- [X] T007 [US1] Write RED tests for the new check in `/gm-assistant/.claude/skills/diagram/test_checks.py`: `city_wall_matches_budget` fails a walled city manifest with no `M["budget"]`; fails a synthetic manifest whose measured interior exceeds `required_interior_px2` by more than the over-tolerance; fails the undersized direction; passes a matched synthetic; passes the shipped `pool/tango.json` once Tango's budget is attached via T009 (until then scope the pass-case to synthetic)
- [X] T008 [US1] Implement `city_wall_matches_budget` in `/gm-assistant/.claude/skills/diagram/check_village.py` per the contract (walled-city scope, measured interior computed the same way `city_capacity` measures it, both-direction tolerances as module constants with "why" comments); confirm T003's regression fixture now fails it and T007 goes green
- [X] T009 [US1] Attach a budget to Tango WITHOUT regenerating its geometry: in `/gm-assistant/.claude/skills/diagram/pool/tango.gen.py` compute `plan_city(tango_program)` and record `budget_to_manifest` into `s.meta(budget=...)` (add the meta passthrough in `/gm-assistant/.claude/skills/diagram/settlement.py` only if `meta()` does not already forward arbitrary kwargs); re-emit `pool/tango.json` with the existing wall untouched; `python3 check_village.py pool/tango.json` fully green including the new check
- [X] T010 [US1] Document the doctrine: add a "Budget-first wall sizing (feature 009)" section to `/gm-assistant/.claude/skills/diagram/settlements.md` (the model, each constant's why, the historical grounding incl. the 25-30% Chinese open-reserve norm and why reserve must be declared+drawn, the source-strength caveat on the triangulated circulation figure, the new render-order step "budget -> wall -> ..."), and update the city workflow in `/gm-assistant/.claude/skills/diagram/SKILL.md`

**Checkpoint**: budget engine + check shipped; Tango green with a recorded budget; pinned pre-feature Nagahara failing; all OTHER pool maps still green.

## Phase 4: User Story 2 - Nagahara regenerated without the empty ground (P1)

**Goal**: Nagahara rebuilt budget-first; wall derived (expect ~15% less enclosed ground); packed to `sized_and_packed` on the first derivation; all checks green.

**Independent test**: `python3 pool/nagahara.gen.py && python3 check_village.py pool/nagahara.json --capacity` = zero fails + `sized_and_packed`; the rendered PNG goes to the GM for the empty-space verdict.

- [X] T011 [US2] Rework `/gm-assistant/.claude/skills/diagram/pool/nagahara.gen.py` to the budget-first order: compute `plan_city(CityProgram(population=3000, river=True), canvas=...)`, take RX/RY from `budget.wall` (replacing the hand-tuned 494x460), record `M["budget"]`, and re-fit the fixed-coordinate layout (river/moat/canal/dock, quarters, ward fence, streets, civic compounds, packs) to the smaller derived ring - reusing the similarity-transform lesson from feature 006 (scale the WHOLE gen about the wall centre where possible rather than re-tuning features one by one)
- [X] T012 [US2] Grind Nagahara green: iterate placement (NOT the wall - the wall is now fixed by the budget) until `python3 check_village.py pool/nagahara.json` reports zero fails and `--capacity` reads `sized_and_packed` with no resize step; the budget's `dwelling_target` per kind must be met (existing population/caste floors); document any legit program change as an `extras` BudgetLine, never as wall slack
- [X] T013 [US2] Render and verify the full corpus: re-render `pool/nagahara.svg` -> `pool/nagahara.png`; run `python3 check_village.py` over EVERY `pool/*.json`; `make done`; confirm the pinned T002 fixture still fails and shipped Tango still passes
- [X] T014 [US2] Visual review pass: inspect the PNG against the pre-feature render (open-ground pockets from research.md - especially the five >=35k px^2 pockets, largest ~440x512 at the SW samurai/governor quarter - must be gone or declared+drawn); then present both renders to the GM for the SC-001 empty-space sign-off (the GM's eye is the acceptance authority; do NOT mark the story done on checks alone)

**Checkpoint**: the motivating defect is fixed end-to-end; feature is demonstrable.

## Phase 5: User Story 3 - In-wall agricultural district toggle (P2)

**Goal**: the toggle is a first-class, documented program knob (the mechanics land with T004-T005; this phase proves and documents the surface).

**Independent test**: same-population budgets with toggle off/on differ by exactly the itemized district line and the derived wall grows accordingly; Tango's toggle-on program back-predicts its shipped wall.

- [X] T015 [P] [US3] Extend `test_citybudget.py` with the toggle acceptance pair from the spec: off-vs-on budget delta equals the district line; derived wall area grows by it (parametrized across the 2000/3000/4000 band); confirm the Tango back-prediction test (T004g) covers the toggle-on path and add it if scoped out
- [X] T016 [P] [US3] Document the knob: agricultural-district entry in the settlements.md feature-009 section (when to use it - "not typical but not a one-off", Tango as the worked example, the historical why from research.md) and the `CityProgram` field reference in SKILL.md

## Final Phase: Polish & Cross-Cutting

- [X] T017 Full-suite sweep: `make done` in `/gm-assistant/.claude/skills/diagram/`, all pool manifests through `check_village.py`, `test_regressions.py` green, coverage 100% on `citybudget.py` and the touched check code; reconcile with any parallel-session engine changes (re-run after a `git status` look at `settlement.py`/`check_village.py`)
- [X] T018 Close the loop on the spec artifacts: check off the validated items in `specs/009-city-area-budget/checklists/requirements.md`, record actual calibration tolerances chosen in research.md if they moved during implementation, and note the regen outcome (before/after interior px^2, open fraction) in the feature dir for the record

## Dependencies

- Phase 1 (T001) and Phase 2 (T002-T003) first; T002 MUST precede any nagahara.json regeneration.
- US1: T004 -> T005 -> T006; T007 -> T008 (needs T005's types); T009 needs T008; T010 anytime after T005.
- US2 (T011-T014) needs US1 complete (the wall comes from the module; the check must exist to gate the regen).
- US3 (T015-T016) needs T005; parallel to US2.
- Polish last.

## Parallel opportunities

- T002/T003 alongside T001.
- Within US1: T007 can be drafted while T005 is in progress (different files); T010 in parallel with T009.
- US3 (T015, T016) fully parallel to US2's grind.
- The US2 grind (T012) is the long pole; nothing else blocks on it except T013-T014.

## Implementation strategy

MVP = Phase 1 + 2 + US1 (budget engine, check, Tango budget attached): at that point the defect is automatically detectable and any new city can be budgeted. US2 delivers the visible payoff (Nagahara). US3 is a documentation/proof increment on mechanics US1 already carries.
