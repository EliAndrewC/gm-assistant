# Tasks: Human-Scale Files

**Input**: Design documents from `/specs/024-human-scale-files/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/check_village-api.md

**Tests**: No new test tasks - the oracle identity sweeps (022 tooling) and the existing diagram
suite ARE the tests for a verbatim-move refactor (plan.md Constitution Check, Principle X note).
The registry-pin fixture is regenerated, not hand-written.

**Organization**: US1 = the rule documented; US2 = check_village package; US3 = oversized-segment
splits. US3 runs BEFORE US2's file move (research.md R1: split in the monolith, then move).

## Phase 1: Setup

- [ ] T001 Verify clone is synced and the diagram suite is green pre-feature: `git pull origin main` in the clone, then `python3 -m ruff check .claude/skills/diagram` and a fast pytest smoke (`pytest .claude/skills/diagram/test_regressions.py -n auto -q`) - a red baseline would poison every identity claim downstream

## Phase 2: Foundational (oracle baseline)

- [ ] T002 Capture the oracle baseline against the untouched monolith: from `.claude/skills/diagram/`, `python3 ../../../specs/022-gate-check-registry/oracle_sweep.py capture ../../../specs/024-human-scale-files/oracle_pre.json` (all 797 regression fixtures + pool manifests, verbose stdout hashed)

## Phase 3: User Story 1 - The rule exists and is findable (P1)

**Goal**: clause 13 in the constitution + dependent-template propagation.
**Independent test**: read Principle X - the file-size clause exists with threshold, target
shape, token-economy why; version 1.6.0; plan template + CLAUDE.md carry the mirrors.

- [ ] T003 [US1] Add clause 13 "Files stay at human scale" to Principle X in `.specify/memory/constitution.md`: ~1,000 raw lines prompts the package-of-subfiles question; target shape = directory-module + CLAUDE.md index with "look here when" lines (slim-index/load-on-demand pattern); why = token economy (context-window cost scales with raw text - hence RAW LINES here vs clause 12's logic units, stated explicitly per research.md R11); same anti-dogma caution as clause 12 (ask-the-question line, not a mandate; ordered-data files may stay large with an inline justification); motivating case = check_village.py at 35,603 lines. Bump version 1.5.0 -> 1.6.0, update the Last Amended date, and prepend a new SYNC IMPACT REPORT entry per the amendment procedure
- [ ] T004 [P] [US1] Extend the Principle X gate text in `.specify/templates/plan-template.md` with one sentence: plans whose implementation would grow a FILE past ~1,000 lines must say so and either plan the package split or justify the file (mirroring the clause-12 sentence already there)
- [ ] T005 [P] [US1] Add a one-line operational mirror to `/gm-assistant/CLAUDE.md` (clone copy) in the Development Workflow section near the constitution references: files past ~1,000 lines prompt the split-into-package question, exemplar `check_village/` (constitution Principle X clause 13)

## Phase 4: User Story 3 - Oversized segments become per-check segments (P2 - runs before US2 per research.md R1)

**Goal**: the 9 segments ≥300 lines with ≥2 checks (census in research.md R3) become per-check
segments in the monolith, identity proven.
**Independent test**: oracle compare vs oracle_pre.json = zero diffs; targeted sweep passes;
no segment over clause-12 scale remains.

- [ ] T006 [US3] Write `specs/024-human-scale-files/split_oversized.py` adapted from `specs/023-split-city-mega-segment/split_megaseg.py`: for each census segment (0285, 0286, 0562, 0543, 0106, 0523, 0555, 0040, 0438; include 0133 iff its statements cut cleanly per check), group top-level statements at `check(...)` boundaries (023 rule), emit `_seg_NNNN_MMM__<checkname>` functions verbatim-bodied with recomputed free/writes/needs per 022 `transform_gate.py` dataflow rules (re-read 022 research.md R9 holes first: helper-closure mutation, upward-exposed reads, comprehension-target scoping), splice replacement rows at the old registry position, print the census JSON rows (data-model.md shape)
- [ ] T007 [US3] Run split_oversized.py against `.claude/skills/diagram/check_village.py`, then `python3 -m ruff format` + `ruff check` (SIM102 guard-combining allowed) + `mypy` on the diagram dir
- [ ] T008 [US3] Prove identity: oracle `compare` vs `oracle_pre.json` (zero diffs) and oracle `targeted` from `.claude/skills/diagram/`; if either fails, fix the transform - never hand-patch verdicts
- [ ] T009 [US3] Regenerate `test_fixtures/gate_check_names.json` for the new segment names (find its documented regeneration path - the registry-pin test in the diagram suite - and rerun it), then run the whole affected test files: `pytest .claude/skills/diagram/test_regressions.py .claude/skills/diagram/test_checks.py -n auto -q`
- [ ] T010 [US3] Commit stage 1 with the census table in the commit message

## Phase 5: User Story 2 - check_village.py becomes a navigable package (P1)

**Goal**: monolith -> `check_village/` package, contract surface preserved, identity proven.
**Independent test**: `import check_village` exposes the full legacy surface; oracle compare +
targeted clean; only registry.py exceeds ~1,000 lines and says why.

- [ ] T011 [US2] Write `specs/024-human-scale-files/split_package.py`: census the (post-stage-1) monolith's top-level statements; cut the common region (~lines 1-2630) into 3 contiguous `common_*.py` files at def boundaries and the segment region into ~10-14 contiguous `segments_NN_<theme>.py` files (theme from dominant check-name vocabulary; every cut on a top-level statement boundary; concatenation in file order reproduces definition order); emit `registry.py` (_GateSeg + GATE_SEGMENTS + META_CHECKS + _SEG_DEPS loop, with clause-13 justification header and the stale "586 dense data rows" comment corrected to the true count), `driver.py` (gate, twin helpers, main), `__main__.py`, and a generated `__init__.py` with explicit re-exports of EVERY module-level name in definition order (research.md R6 - no star imports); generate each module's explicit imports from free-name analysis (backwards-pointing only, data-model.md rule); move the module docstring + `_assert_not_main_tree` guard into `__init__.py`; delete `check_village.py`
- [ ] T012 [US2] Run split_package.py, then `python3 -m ruff format .claude/skills/diagram && python3 -m ruff check .claude/skills/diagram && python3 -m mypy` (from the diagram dir, per its config)
- [ ] T013 [US2] Prove identity again: oracle `compare` vs `oracle_pre.json` + oracle `targeted`; then `pytest .claude/skills/diagram -n auto -q` scoped to the diagram dir (never repo root - clone double-collection gotcha)
- [ ] T014 [US2] Write `.claude/skills/diagram/check_village/CLAUDE.md`: one line per module with a "look here when" hook (e.g. "well/garden/grove placement checks -> segments_NN_homesteads.py"), the registry-order invariant, the `only=` targeting pointer, and the clause-13 note about registry.py; verify every package file is listed (script the check: `ls check_village/*.py` vs lines in the index)
- [ ] T015 [US2] Update callers and docs: `.claude/skills/diagram/CLAUDE.md` registry section (file names + "adding a check" instructions now name the package modules), any `python3 check_village.py` invocation in `.claude/skills/diagram/**/*.md` and reference docs -> `python3 -m check_village` (contracts/check_village-api.md CLI section); grep-verify zero stale invocations and that `import check_village`/`from check_village import` callers (cohort_audit, site_justice, make_regressions, hamletgen, 5 test modules, oracle_sweep) run unmodified
- [ ] T016 [US2] Commit stage 2

## Phase 6: Polish & Cross-Cutting

- [ ] T017 Verify coverage config still reaches the package (diagram pyproject: if coverage/mypy config names `check_village.py`, update to the package) and run the diagram skill's FULL gate in the background: `make done > <scratchpad>/gate024.log 2>&1` with nothing appended after; act on the completion notification and tail the log before believing green
- [ ] T018 Record the "why" trail: mark research.md dispositions final (R9 waterfields exemption, R10 settlement.py deferral), update `specs/024-human-scale-files/` with actual file names chosen by the census, and mark all tasks checked
- [ ] T019 Stop-work ritual: final commit in the clone, then `scripts/sync-with-main.sh done` from inside it

## Dependencies

- T002 blocks T006+ (baseline before any mutation). T003-T005 (US1 docs) are independent of code phases and parallel with each other after T002.
- US3 (T006-T010) strictly before US2 (T011-T016) - research.md R1.
- T017-T019 last.

## Implementation Strategy

Docs land first (durable rule). Then baseline -> stage 1 (segments) -> stage 2 (package), each
stage proven identical before the next. MVP = US1 alone is a valid stopping point; US3+US2 ship
together as the exemplar. Every "fix a red oracle" loop happens in the split SCRIPTS, keeping the
monolith itself out of context per the feature's own token-economy rationale.
