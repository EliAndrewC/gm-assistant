# Tasks: hamletgen.py -> hamletgen/ Package Split

**Input**: Design documents from `/specs/111-hamletgen-package/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/package-surface.md, quickstart.md

**Tests**: Included - spec FR-003 mandates the guard test (proven to fire), FR-009 mandates the
test-package mirror, and the whole feature rides on the byte-identity oracle. All paths below are
relative to `.claude/skills/diagram/` inside the session clone unless stated otherwise.

**Organization**: US1 (behavior-preserving split) is the MVP and carries nearly all the mechanics;
US2 (function decomposition), US3 (the index) and US4 (test mirror) build on it.

## Phase 1: Setup - baseline capture (MUST precede any code change)

- [x] T001 Census check: re-grep the consumer surface (`from hamletgen import`, `import hamletgen`, `hg\.<attr>`) across the skill tree and record any names beyond the contracts/package-surface.md list in `specs/111-hamletgen-package/contracts/package-surface.md` (concurrent sessions may have added consumers since spec time)
- [x] T002 Capture the pre-split baseline per quickstart.md section 1: copy the skill tree at HEAD to `<scratchpad>/hg-baseline/tree`, run the four live hamlet gens plus `specs/111-hamletgen-package/baseline_cohort.py --out <scratchpad>/hg-baseline/cohort --count 24`, and the `--batch 24` report table into `cohort-report.txt`; verify all four hamlet manifests and 24 cohort manifests exist and note any gen that fails pre-split (a pre-existing failure is excluded from the oracle, recorded in this file's notes)

## Phase 2: Foundational - guard test (blocks all stories)

- [x] T003 Write `test_hamletgen_surface.py` (modeled on `test_check_village_surface.py`): pin every censused name from T001, assert each resolves from `hamletgen`, assert submodule identity (`getattr(hamletgen, n) is getattr(submodule, n)`), assert `hamletgen.point_in_poly is settlement.point_in_poly`, add the no-public-name-clash check across submodules, and add the mechanical re-census (grep the tree, assert every found name is pinned). Write the package-only assertions so they activate when `hamletgen` becomes a package, so the file is green against the monolith and meaningful after the split

## Phase 3: User Story 1 - behavior-preserving package split (P1) - MVP

**Goal**: `hamletgen/` package, eleven modules moved verbatim, derived `__init__`, zero consumer
changes, byte-identical output.

**Independent test**: quickstart.md sections 2-3 and 7 - scratch-tree manifest diff empty, guard
green, `make done` green, no consumer file modified.

- [x] T004 [US1] Create `hamletgen/` and move code VERBATIM (no logic edits; comments and docstrings travel intact per FR-011) from `hamletgen.py` into `hamletgen/consts.py`, `plan.py`, `geom.py`, `water.py`, `sink.py`, `cluster.py`, `ways.py`, `homesteads.py`, `hinterland.py`, `frame.py`, `driver.py` per the data-model.md layout; each module gets a short docstring naming its concern plus the module-level imports it needs, with cross-module imports following the verified DAG (research R1: plan/geom -> consts; the six stage modules -> plan/geom/consts; ways -> cluster; driver -> every stage module)
- [x] T005 [US1] Put the `STAGES` tuple in `hamletgen/driver.py` in its current order with an ordering comment at that point saying the sequence is the design and is shared with the skill CLAUDE.md DRAW ORDER map (FR-008, research R6 - including why it is a literal tuple and not derived)
- [x] T006 [US1] Write `hamletgen/__init__.py`: the `HERE`/`sys.path` bootstrap FIRST (research R7), then the moved head docstring (all four doctrine paragraphs verbatim), then eleven `from .<module> import *` lines leaf-first (consts, geom, plan, water, sink, cluster, ways, homesteads, hinterland, frame, driver) plus the aliased block for the four underscore names (`_arm_crossing_accidental`, `_fork_spur` from cluster; `_clear_gap`, `_near_line` from hinterland); NO `__all__`, no logic
- [x] T007 [US1] Write `hamletgen/__main__.py` as a shim (`from .driver import main` + `raise SystemExit(main())`) so `python3 -m hamletgen` works; `main` STAYS in `driver.py` because consumers reach `hg.main`
- [x] T008 [US1] DELETE `hamletgen.py` in the same change so a stale monolith can never shadow the package on `sys.path`
- [x] T009 [US1] Update `pyproject.toml`: mypy `files` entry `"hamletgen.py"` -> `"hamletgen"`; add `"hamletgen/__init__.py" = ["F401", "F403"]` to `[tool.ruff.lint.per-file-ignores]` with the same why-comment style as the three existing entries. Coverage `source` needs no edit (research R4) - verify that claim by reading the coverage report for `hamletgen/*` in T012
- [ ] T010 [US1] Guard-test TDD proof (SC-006): temporarily comment out one star import in `hamletgen/__init__.py`, run `python3 -m pytest test_hamletgen_surface.py`, confirm it FAILS naming the missing surface; restore, confirm green; record the red run in this file's notes
- [ ] T011 [US1] Post-move byte-identity: quickstart.md section 2 - fresh scratch copy of the working tree, re-run the four hamlet gens + `baseline_cohort.py` + the `--batch 24` table, `diff -r` all three against the T002 baseline; MUST be empty before proceeding
- [ ] T012 [US1] Run the full gate from the clone (`make done`, backgrounded to a log, tailed - never wrapped with a trailing `echo EXIT=$?`): ruff + duplicate-def check + format + mypy --strict + full pytest + the per-module 100% coverage gate; confirm the coverage table lists `hamletgen/*.py` modules at 100%; fix everything it lists together, re-run once
- [ ] T013 [US1] Verify SC-002 (zero consumer changes) with `git diff --stat`: changes ONLY in `hamletgen/` (new), `hamletgen.py` (deleted), `test_hamletgen_surface.py` (new), `pyproject.toml`, and `specs/`; nothing under `pool/hamlets/*.gen.py` or in `cohort_audit.py`; commit the move as its own bisectable commit

## Phase 4: User Story 2 - oversized stage functions decomposed (P2) - NOT EXECUTED, see research R12

**Goal**: the nine functions at or above ~85 lines decomposed into named sub-stage functions, each
<= ~150 lines, byte-identity re-verified after EACH one.

**Independent test**: quickstart.md section 4 (AST length check) + empty manifest diff per pass.

**HELD (research R12, 2026-08-16).** Re-measured before T014 against the constitution's ACTUAL
function metric: clause 12 counts LOGIC UNITS, not raw lines, and sets the bar at "a few hundred
statements". The largest function here is **67 statements** (`stage_ways`); the raw counts are
inflated 2-3x by the project's mandatory record-the-why comments (22-87 lines apiece, each block
explaining the statement below it). The ~150-LINE bar this phase was written against is the
clause-13 FILE metric, applied to functions by mistake at spec time. Executing it would trade
cohesion and comment locality for a metric the constitution explicitly rejects, and would collide
with FR-011. Full measurement table and reasoning in research.md R12. Left with the GM as a taste
call, not a compliance one.

Method if it is ever taken up (research R5): mechanical extraction only - code order, RNG draw
order and float-operation order preserved exactly; state in as parameters, values out; no new
shared mutable module state; no "while I'm here" tidying.

- [ ] T014 [US2] Decompose `stage_ways` (177 lines) in `hamletgen/ways.py` into named sub-stage functions; re-run the T011 byte-identity sweep - MUST be empty; commit
- [ ] T015 [US2] Decompose `stage_sink` (168 lines) in `hamletgen/sink.py`; byte-identity sweep empty; commit
- [ ] T016 [US2] Decompose `place_wells` (164 lines) in `hamletgen/homesteads.py`; byte-identity sweep empty; commit
- [ ] T017 [US2] Decompose `open_ground_patches` (137 lines) in `hamletgen/hinterland.py`; byte-identity sweep empty; commit
- [ ] T018 [US2] Decompose `seat_cluster` (127 lines) in `hamletgen/cluster.py`; byte-identity sweep empty; commit
- [ ] T019 [US2] Decompose `stage_polder` (126 lines) in `hamletgen/water.py`; byte-identity sweep empty; commit
- [ ] T020 [US2] Decompose `stage_homesteads` (111 lines) in `hamletgen/homesteads.py`; byte-identity sweep empty; commit
- [ ] T021 [US2] Decompose `connector_track` (89 lines) in `hamletgen/ways.py` and `belt_polygon` (85 lines) in `hamletgen/hinterland.py`; byte-identity sweep empty; commit
- [ ] T022 [US2] Function-scale verification: run the quickstart section-4 AST check over `hamletgen/*.py`; any function still over ~150 lines is split further or carries an inline one-line justification; re-run `make done` (shared code changed, so the full sweep is mandatory) and confirm coverage is still 100% on every `hamletgen/` module - a newly extracted sub-stage with an unreachable branch shows up here

## Phase 5: User Story 3 - the package index (P3)

**Goal**: `hamletgen/CLAUDE.md` in the check_village / waterfields "look here when" style; skill
docs point at the package.

- [x] T023 [P] [US3] Write `hamletgen/CLAUDE.md`: header stating the split provenance (feature 111, clause 13/14, the 027 re-export mechanism, the guard-test name), the "load only the file the task calls for" doctrine, the note that `STAGES` in `driver.py` is the pipeline contract, and a "look here when" table covering all thirteen files with each row naming its key functions and constants
- [x] T024 [P] [US3] Update file-path references from `hamletgen.py` to the package in `.claude/skills/diagram/CLAUDE.md`, `SKILL.md`, `hamletgen.md`, `migration-plan.md`, and the four `pool/hamlets/*.notes.md`, including the CLI form (`python3 hamletgen.py ...` -> `python3 -m hamletgen ...`); leave importable-path prose (`hamletgen.seat_cluster`) and historical `specs/NNN` artifacts verbatim (research R8)

## Phase 6: User Story 4 - test package mirror (P4)

**Goal**: `test_hamletgen/` mirrors the source submodules; no test lost or changed in substance.

- [x] T025 [US4] Split `test_hamletgen.py` into `test_hamletgen/` with `__init__.py` and one module per source submodule that has tests (`test_plan.py`, `test_geom.py`, `test_water.py`, `test_sink.py`, `test_cluster.py`, `test_ways.py`, `test_homesteads.py`, `test_hinterland.py`, `test_frame.py`, `test_driver.py`); shared fixtures/builders go in `test_hamletgen/_builders.py` if any exist; DELETE `test_hamletgen.py`
- [x] T026 [US4] Prove no test was lost: compare `python3 -m pytest test_hamletgen --collect-only -q` count against the pre-split count recorded in T002's notes; the same number of tests must collect and pass, with only module paths changed
- [ ] T027 [US4] Re-run `make done` and confirm coverage on `hamletgen/` is unchanged at 100% (a test accidentally dropped in the move shows up as a coverage hole, not as a failure); commit

## Phase 7: Polish & close-out

- [ ] T028 Final full verification: `make done` backgrounded from the clone (skip only if everything since the last green gate is docs-only), then confirm every success criterion - manifests byte-identical (SC-001), consumer diff scope (SC-002), file and function sizes (SC-003), the index maps every concern to one file (SC-004), suite + gate + regression corpus green with the same test count (SC-005), guard proven to fire (SC-006)
- [ ] T029 Update `spec.md` status Draft -> Implemented, check off this file's boxes with notes on anything that deviated, commit; stop-work ritual: `scripts/sync-with-main.sh done` from the clone (locked pull+push + render-sync); report to the GM with concrete verify steps

## Dependencies

- T001 -> T002 -> T003 -> US1 (T004-T013, sequential) -> US2 (T014...T022, sequential) -> US3 (T023, T024 parallel) -> US4 (T025 -> T026 -> T027) -> T028 -> T029
- US2 strictly after US1's commit: the move must be a clean bisect point before any decomposition.
- US4 after US2, because the test modules should land against the decomposed source rather than be
  split twice.
- US3's T023 wants US2 done so its rows can name the sub-stage convention; it runs after.

## Parallel opportunities

- T023 and T024 are [P] - different files, no ordering between them.
- The per-map gen runs inside the T002/T011 sweeps fan out naturally (independent processes).
- Everything else is deliberately serial: each step's oracle is the previous commit.

## Implementation strategy

MVP = US1 alone. A green, byte-identical package split with zero consumer changes is shippable by
itself and already delivers the token motivation in full. US2 lands one function per commit so any
drift bisects to a single extraction. US3 is a docs pass; US4 is a mechanical test move. If the run
must stop early, stop at a US-phase boundary, never mid-phase.

## Notes

- **T001**: census re-confirmed at 47 `hg.<attr>` names + 2 direct-import names. No new consumers
  since spec time.
- **T002**: pre-split test count for `test_hamletgen.py` = **81 tests**. All four live hamlet gens
  ran clean pre-split; nothing excluded from the oracle.
- **T004**: partition landed as planned. Two measured import edges beyond the plan's sketch:
  `frame -> hinterland` (title-pocket helpers) and the expected `ways -> cluster`. Still acyclic.
  `ruff format` touched only trailing blank lines at file ends - no body was reformatted.
- **T023/T024**: `hamletgen/CLAUDE.md` written; skill `CLAUDE.md`, `SKILL.md`, `hamletgen.md`,
  `migration-plan.md` and the four `pool/hamlets/*.notes.md` updated to the package path and the
  `python3 -m hamletgen` CLI form.
- **T025/T026**: test package landed - 10 test modules + `_builders.py` + `__init__.py`, largest
  155 lines. **81 tests collected, exactly matching the pre-split count.** Curated the
  test-to-module mapping by hand where the automatic attribute-count heuristic mis-assigned the
  polder/pond tests (they call `plan_site` as setup but exercise `water`/`sink`).
- **Byte-identity (T011, live-hamlet half)**: all four live hamlet manifests AND SVGs
  byte-identical to the pre-split baseline - empty `diff -r` across all 8 files.
- **Deviation (research R11)**: five `monkeypatch.setattr(hg, ...)` calls in `test_hamletgen.py`
  had to be retargeted to `hg.sink` / `hg.driver`. Three tests failed and one was passing by
  accident. No production consumer affected; SC-002 amended to "zero production consumer changes".
