# Tasks: Split the City Mega-Segment

**Input**: Design documents from `specs/023-split-city-mega-segment/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: no new test files - this is a behavior-preserving transform whose "tests" are the
pre-captured oracle baseline (red on any diff), the teeth check, and the existing suites run
whole. That verification IS the work, so it appears as explicit tasks, not as optional extras.

**Organization**: single pipeline; the user-story phases map to spec.md's US1 (human-scale
segments land), US2 (targeted execution correct + narrower), US3 (test surface green,
unchanged in what it asserts). Later phases depend on earlier ones - this feature has little
parallelism by nature (one file, sequential verification), and the iteration-loop rules
(batch turns, background the gate, no `-k` subsets) govern execution.

**Paths**: `diagram/` = `.claude/skills/diagram/`; `023/` = `specs/023-split-city-mega-segment/`;
`022/` = `specs/022-gate-check-registry/`; scratch = the session scratchpad dir.

## Phase 1: Setup (Baselines - BEFORE any code changes)

**Purpose**: freeze the red bar. A baseline captured after any edit is worthless.

- [X] T001 Capture the full-mode oracle baseline at the current tip: `python3 022/oracle_sweep.py capture <scratch>/oracle-baseline-023.json` from `diagram/` (all regression fixtures + pool manifests; verify the count printed matches the manifest census)
- [X] T002 [P] Record timing baselines in 023/timings.md: `import check_village` wall time, and `pytest test_regressions.py -n auto -q` wall time in `diagram/`
- [X] T003 [P] Record the pre-split size census in 023/timings.md: AST statement count of `_seg_0563__city_has_six_ministries` and the sha256 of `diagram/test_fixtures/gate_check_names.json` (must be unchanged at the end)

## Phase 2: Foundational (the transformer)

**Purpose**: the one-shot tool that performs the split. Blocking for everything after.

- [X] T004 Write 023/split_megaseg.py `census` mode: parse `diagram/check_village.py`, locate the mega-segment, extract the outer-guard (82) and walled-guard (295) statement sequences, and run the hard-fail census per research.md R3/R4 (early return, global/nonlocal, del-of-local, `scale`/`meta` rebinding or mutation, stale helper cells among the 27 nested defs, lambda-freeze WARNs); reuse 022/transform_gate.py's analysis functions by import (sys.path insert - do NOT copy the code); print per-SubSeg stats (free/writes/checks/needs counts, statement sizes, check-name union) and assert the union == the registry row's 148 names
- [X] T005 Write 023/split_megaseg.py `generate` mode per data-model.md: emit ~378 `_seg_0563_NNN__<slug>` defs at the mega-function's file position (bodies VERBATIM from source lines, wrapped in their guard, gap comment banks preserved above their segment), regenerate per-segment `return _kept(...)`, replace registry row 563 with the new `_GateSeg` rows in order, delete the clause-12 annotation, then run the type-ignore/ruff fixpoint (reuse 022's `_inject_type_ignores` scoped approach) - idempotence guard: refuse to run if `_seg_0563_000__` already exists

## Phase 3: User Story 1 - the split lands at human scale (P1) [US1]

**Goal**: mega-segment replaced by human-scale segments, registry coherent.

**Independent test**: spec.md US1 acceptance - grep any of the 148 names, land in a small
segment; AST census shows no function past the lines.

- [X] T006 [US1] Run `python3 023/split_megaseg.py census` then `generate` from `diagram/`; eyeball the diff head/tail (`git diff --stat`, spot-check one outer-guard and one walled-guard segment for verbatim body + preserved comments)
- [X] T007 [US1] Verify sizes and names (spec FR-001/FR-002/SC-001): AST census over `diagram/check_village.py` - largest function well under 1,000 statements, every new `_seg_0563_*` under 400, no clause-12 annotation remains, union of new rows' checks == the frozen 148, `gate_check_names.json` byte-identical (sha256 vs T003); record results in 023/timings.md

## Phase 4: User Story 2 - verdict identity + targeted narrowing (P2) [US2]

**Goal**: nothing observable moved; targeted runs got narrower.

**Independent test**: spec.md US2 acceptance - oracle sweeps green; closure shrinks.

- [X] T008 [US2] Full-mode byte identity (spec FR-003/SC-002): `python3 022/oracle_sweep.py compare <scratch>/oracle-baseline-023.json` from `diagram/` - zero diffs, zero missing; on ANY diff, fix the transformer and re-run generate from a clean checkout of check_village.py (never hand-patch generated bodies mid-feature - 022 R7 rule)
- [X] T009 [US2] Targeted-vs-full sweep (spec FR-004/FR-005): `python3 022/oracle_sweep.py targeted` - zero MISMATCH; investigate any new FALLBACK count (baseline: 0)
- [X] T010 [US2] Teeth check: invert the condition of one outer-guard check and one walled-guard check in the NEW segments, confirm their regression fixtures go red in targeted mode, revert both edits and re-confirm green (record which two checks in 023/timings.md)
- [X] T011 [US2] Narrowing + perf measurement (spec FR-008/SC-004): re-time `import check_village` and the `test_regressions.py -n auto` replay vs T002; compute the closure size (segments + total statements executed) for one representative city check (e.g. `city_has_bathhouse`) before/after (before = 1,040 statements by construction); record in 023/timings.md; if import time regressed noticeably, implement the indexed-writers `_SEG_DEPS` builder from research.md R6 with a unit test, and re-measure

## Phase 5: User Story 3 - the existing test surface stays green (P3) [US3]

**Goal**: every suite green, nothing weakened.

**Independent test**: spec.md US3 acceptance - pin test + replay + whole files pass.

- [X] T012 [US3] Run the whole affected test files from `diagram/` (never `-k`): `python3 -m pytest test_checks.py test_regressions.py -n auto -q`; fix any breakage at the transformer level (regenerate), not by editing generated bodies
- [X] T013 [US3] Background `make done > <scratch>/make-done-023.log 2>&1` in `diagram/` (nothing appended after the redirect - the exit code must be honest); on the completion notification, tail the log and confirm ruff + format + mypy strict + pytest + 100% coverage all green

## Phase 6: Polish and record-the-why

- [X] T014 [P] Update the "The gate is a REGISTRY" section of diagram/CLAUDE.md (spec FR-009): the city battery is now per-statement segments under in-body scale guards (`_seg_0563_NNN__*`), the clause-12 debt is retired, adding-a-check guidance now points at the sub-segment convention for city/capital checks; one short paragraph, not a rewrite
- [X] T015 [P] Close out 023 artifacts: research.md gains a short "what implementation taught" addendum ONLY if the sweeps caught a new dataflow hole (mirror 022 R9; skip if none), timings.md gets the final measured table (baseline vs post: import, replay, closure sizes, largest-function census); mark tasks.md checkboxes as each task verified
- [ ] T016 Stop-work ritual: commit in the clone, run `scripts/sync-with-main.sh done` from the clone root

## Dependencies

- T001-T003 before T006 (baseline must precede any transform); T004-T005 before T006
- T006 before T007; T007 before T008-T011 (no point sweeping a malformed split)
- T008-T009 before T010-T011 (teeth/perf only meaningful on an identity-clean build)
- T012 before T013 (whole-file runs precede the gate per the gate-hooks rule); T013 before T016
- T014-T015 parallel with T012-T013 (docs-only), but T015's final table needs T011/T013 numbers

## Implementation strategy

Straight pipeline, MVP = US1+US2 (a split that lands but fails identity is worthless, so the
first shippable increment is through T009). T010-T015 complete the feature; T016 ships it.
Batch aggressively per the iteration-loop rules: T001-T003 in one turn; census+generate+size
checks foldable into asserted scripts; the gate backgrounded exactly once at the end.
