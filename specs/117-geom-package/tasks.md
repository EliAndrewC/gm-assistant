# Tasks: settlement/_geom.py -> settlement/_geom/ Package Split

**Input**: Design documents from `specs/117-geom-package/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/surface.md, quickstart.md

**Tests**: test tasks ARE included here, and only for the two genuinely NEW behaviors - the surface
guard's two halves (contracts C1/C2). The 89 moved members are a MOVE: their tests already exist and
must keep passing untouched, which is a stronger statement than a new test would make.

**Organization**: by user story, per spec.md. US1 (the split) is the MVP and is independently
shippable; US2 (the guard) and US3 (the index) each add a separate kind of assurance.

**All commands run from `.claude/skills/diagram/` inside the clone unless stated otherwise.**

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1 / US2 / US3

---

## Phase 1: Setup

- [x] T001 Confirm the clone is synced to main's tip and `git status --short` is clean under
      `.claude/skills/diagram/pool` before anything runs, in `/gm-assistant/.clones/diagram-tokens`
- [x] T002 Confirm the Principle XIII baseline exists and is the PRE-split one: `/tmp/117-baseline-hashes.txt`
      (893 artifacts) and `/tmp/117-baseline-sweep.log` (exit 0, `REGENERATED 28`), captured from the
      detached worktree `/tmp/base117` per quickstart step 1

## Phase 2: Foundational (blocks every user story)

- [x] T003 Add the per-file-ignores entry for `settlement/_geom/__init__.py` (`F401`, `F403`) with a
      one-line rationale matching the four existing star-import entries, in `pyproject.toml`

## Phase 3: User Story 1 - Behavior-preserving package split (P1) - MVP

**Goal**: the 89 members live in eleven submodules; every consumer resolves unchanged; every pool
artifact is byte-identical.

**Independent test**: `diff /tmp/117-baseline-hashes.txt /tmp/117-post-hashes.txt` is empty, and
`git diff --stat` shows no consumer file changed.

- [x] T004 [US1] Run the transformer: `python3 ../../../specs/117-geom-package/split_geom.py` -
      it must report the folded unnamed guard call, the moved doctrine bank, and eleven written
      modules, and must exit 0 (a REFUSAL is the design working: fix the partition, never bypass it)
- [x] T005 [US1] Prune and format the copied headers:
      `python3 -m ruff check --select F401 --fix settlement/_geom/ && python3 -m ruff format settlement/_geom/`
- [x] T006 [US1] Delete the pre-split module: `git rm -q settlement/_geom.py` (FR-006 - never leave a
      module beside a package of the same name)
- [x] T007 [US1] Run the cheap linters before anything expensive:
      `python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy` - mypy is what catches
      an ANNOTATION-only name no submodule imports, which PEP 649 would otherwise hide until runtime
- [x] T008 [US1] Run the whole affected test files (never a `-k` subset):
      `python3 -m pytest tests/settlement/ tests/tools/ -q -n auto --no-cov`
- [x] T009 [US1] Capture the post-split oracle in a SCRATCH COPY (never in the clone - the frozen
      renders are tracked): copy the skill dir to `/tmp/post117`, run
      `python3 -m pipeline.regen --no-cache --frozen-ok pool/*/*.gen.py`, hash all `pool/**`
      artifacts to `/tmp/117-post-hashes.txt`
- [x] T010 [US1] Prove FR-004/SC-003: `diff /tmp/117-baseline-hashes.txt /tmp/117-post-hashes.txt`
      is EMPTY, and the post sweep's exit code is 0 with 28 REGENERATED

## Phase 4: User Story 2 - The move is proven complete (P2)

**Goal**: the surface census and the star-import shadowing guard, each proven red before trusted.

**Independent test**: sabotage each half and observe the named failure.

- [x] T011 [US2] Add the surface census (contract C1) to `tests/settlement/test_geom.py`: the 89-name
      literal tuple, asserted as a SUBSET of `dir(settlement._geom)`
- [x] T012 [US2] Add the shadowing guard (contract C2) to `tests/settlement/test_geom.py`: no public
      name bound to two different objects across the eleven submodules
- [x] T013 [US2] Add the guard-call check (contract C3) to `tests/settlement/test_geom.py`:
      `settlement/_geom/base.py` still contains the bare `_assert_not_main_tree()` call, and
      `settlement._assert_not_main_tree` still resolves
- [x] T014 [US2] RED PROOF for C1: delete one member from a submodule, run
      `python3 -m pytest tests/settlement/test_geom.py -q -k surface`, record the observed failure
      text in this file, restore
- [x] T015 [US2] RED PROOF for C2: bind `seg_dist` in a second submodule, run the same, record the
      observed failure text in this file, restore

## Phase 5: User Story 3 - The package is navigable without reading it (P3)

**Goal**: an index that answers "which file?" without a grep, and records the decisions.

**Independent test**: every one of the 89 members is covered by exactly one row.

- [x] T016 [P] [US3] Write `settlement/_geom/CLAUDE.md`: a "look here when" row per submodule, the
      layering rule (`base` <- `primitives` <- `overlap` <- everything else), the monkeypatching
      note (the defining submodule is now `settlement._geom.<module>`), and the four recorded
      placements from FR-008
- [x] T017 [P] [US3] Re-point the `_geom` row in `settlement/CLAUDE.md` at the sub-index, matching
      the shape of the `fields/`, `city/`, `structures/`, `civic_grounds/` and `shrines_wells/` rows

## Phase 6: The audit target (cross-cutting - FR-012)

- [x] T018 Move `TARGET` to `settlement/_geom/curves.py` in `tools/cache_audit.py` and rewrite the
      comment above it to say what was MEASURED (35 candidate literals, 9 executed by the live
      hamlets, all geometry-moving) and why `labels`/`indexes` were rejected - research R7
- [x] T019 Add the per-trial `moved N artifacts` line to `tools/cache_audit.py`: snapshot the CLEAN
      baseline once before the loop, and report per trial whether the mutation moved anything. A
      trial that moved nothing proved nothing, and today it prints an identical `[OK ]`
- [x] T020 Run `python3 -m tools.cache_audit --trials 3` (~10 min, backgrounded, NOT polled) and
      confirm exit 0 with at least one trial reporting a non-zero `moved` count (SC-008).
      **PASS** (2026-08-17, against settlement/_geom/curves.py): 3 mutation(s) audited, 0 skipped, 16 vacuous (moved nothing, retried), 0 FAILED

## Phase 7: Polish and verification

- [x] T021 Prove FR-011/SC-007: comment-line count of the pre-split file
      (`git show HEAD:.claude/skills/diagram/settlement/_geom.py | grep -c '^\s*#'`) is <= the
      package's total (`cat settlement/_geom/*.py | grep -c '^\s*#'`), and the four re-pointed
      sentences are the only comment TEXT changes
- [x] T022 Prove SC-001/SC-002: `wc -l settlement/_geom/*.py` - no file over 280 raw lines
- [x] T023 Prove SC-005/C4: `git diff --stat` names no file outside the contract's allowed list -
      no engine importer, no pool gen, no `wip/` script, not `tools/scatter_audit.py`, not
      `settlement/__init__.py`
- [x] T024 Run the gate, backgrounded and NOT polled, nothing after the redirect:
      `cd /gm-assistant/.clones/diagram-tokens/.claude/skills/diagram && make done > /tmp/117-gate.log 2>&1`;
      tail the log before believing green (SC-004, ratchet floor unchanged)
- [x] T025 Update `specs/117-geom-package/spec.md` Status to Implemented with the final per-file line
      counts and the oracle result, matching feature 116's spec-status convention
- [x] T026 Update `.claude/skills/diagram/CLAUDE.md` if the `settlement/` row's wording needs it, and
      confirm `settlement/CLAUDE.md`'s coverage note still reads true
- [ ] T027 Stop-work ritual: commit in the clone, then `scripts/sync-with-main.sh done`. NOT run on a
      regressed state - Principle XIII's three exits are fix, revert, or an explicit GM waiver

## Dependencies

```text
T001,T002 (setup)
   └─> T003 (foundational)
         └─> US1: T004 -> T005 -> T006 -> T007 -> T008 -> T009 -> T010     [MVP ends here]
               ├─> US2: T011,T012,T013 -> T014,T015
               ├─> US3: T016 [P] T017                 (docs-only; no code dependency)
               └─> T018 -> T019 -> T020               (needs the package to exist)
                     └─> T021..T027 (polish; T024 after every code task)
```

- **US1 is the MVP** and is shippable alone: the clause-13 debt is paid the moment T010 is empty.
- **US2 depends on US1** only because the package must exist to have a surface.
- **US3 is docs-only** and can be written in parallel with US2 - different files, no code dependency.
- **T024 (`make done`) must come after every code-touching task**, including T019.

## Parallel opportunities

- T016 and T017 are different files, no shared state - run together.
- T011/T012/T013 all edit `tests/settlement/test_geom.py`, so they are NOT parallel to each other;
  write them in one edit pass.
- Nothing in US1 is parallel: it is a strict pipeline (transform -> prune -> delete -> lint -> test
  -> sweep -> diff), and each step's output is the next one's input.

## Implementation strategy

Ship US1 first and prove it with the hash diff before writing a line of US2 or US3 - if the oracle
is not empty, everything else is wasted work on a package that is going to be re-cut. Then the guard
(US2), which is what makes the NEXT change to this package safe, then the index (US3), which is what
makes the next READ cheap. The audit target (Phase 6) is separable but must not be deferred past the
merge: leaving `TARGET` on a deleted path ships a broken audit that nobody will notice until the next
mandatory cache run.

## Red-proof records (T014/T015)

- **C1 (surface census)**: truncated `settlement/_geom/curves.py` at `def winding(`, ran
  `pytest tests/settlement/test_geom.py -k surface_still_carries` ->
  `AssertionError: the _geom package no longer exposes: ['winding']`. Restored.
- **C2 (star-import shadowing)**: appended a second `def seg_dist(...)` to
  `settlement/_geom/village.py`, ran `pytest ... -k two_submodules` ->
  `AssertionError: a name is defined in more than one _geom submodule (the later star import
  silently wins): {'seg_dist': ['primitives', 'village']}`. Restored.
- **C1, unprompted**: the census ALSO failed on its first real run, naming `_VILLAGE_POP_DIST` -
  the aliased block had six of the seven underscore names and `import *` carries none of them. The
  package imported cleanly, `mypy --strict` passed and 713 tests passed. Fixed in the transformer
  (so the script still reproduces the package), not by hand in the output. See `research.md` R2.
