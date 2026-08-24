# Tasks: Every Expensive Path Runs Through a Gated Make Target

**Spec**: [spec.md](spec.md) (APPROVED - `spec-fidelity` FAITHFUL, round 3) | **Plan**: [plan.md](plan.md)

> [!IMPORTANT]
> **TICK THESE AS YOU GO. This is not paperwork.**
>
> Feature 126's task list was left with 42 tasks and zero ticks, including tasks that were fully
> completed. The next session could not tell what remained, several planned tasks turned out never to
> have been done, and the handoff had to be reconstructed by reading the source. Spec-kit is used in
> this project as **externalized working memory** - a list nobody marks off is worse than no list,
> because it looks like a record and is not one.
>
> A task is ticked when its verification passed, not when its code was written.

## Rule governing this list: every guard is TWO tasks

A guard is not implemented when it exists. It is implemented when both directions are proven:

- **FIRES** on the case it exists to catch (FR-015)
- **STAYS QUIET** on the legitimate path (FR-016)

A guard appearing once in this list is a planning error. The second direction is the one that
protects the feature from causing the behavior it exists to stop: a guard that fires on correct work
teaches a session that the override is routine, which is how tier 2 of the threat model became
habitual in the first place.

---

## Phase 1: Setup

- [x] T001 Take the regression baseline on UNMODIFIED code in a detached worktree (`git worktree add --detach /tmp/base127 HEAD`), run the gate there, and record its verdict in this file under Baseline below - a remembered baseline is not a baseline (Principle XIII)
- [x] T002 Record `make reference` wall-clock on unmodified code in the Baseline section below, for SC-002's before/after comparison
- [x] T003 [P] Enumerate every CLI entry point under `.claude/skills/diagram/l7r/diagram/` (`find l7r -name __main__.py`, plus modules with a `__main__` guard) and every existing `Makefile` target, into `specs/127-gated-make-commands/contracts/operations.md` as the draft operation registry with a `cost` column per [data-model.md](data-model.md)

## Phase 2: Foundational (blocks every user story)

- [x] T004 Create `.claude/skills/diagram/l7r/diagram/_invocation.py` with `assert_via_make(operation, target)`: walk `/proc/<pid>/stat` PPid to PID 1, accept a `make`/`gmake` ancestor whose `/proc/<pid>/cwd` is inside the repo and whose `/proc/<pid>/cmdline` carries no `-f`/`--file`/`--makefile` naming a path outside it (research R1, R2)
- [x] T005 Cache the verdict at module level so the `/proc` walk happens ONCE per process, with a comment at the point of use stating that `assert_via_make` is called at the TOP of an operation and never in a loop or a library helper (research R4 - this engine's whole performance history is the per-candidate-scan-of-static-geometry shape, and a careless placement recreates it)
- [ ] T006 Build the operation registry in `.claude/skills/diagram/l7r/diagram/_invocation.py` from T003, with `module`/`target`/`cost` per [data-model.md](data-model.md) - enumerated, never inferred from module paths (`tools/` holds both a 25-minute cohort and a manifest read)
- [ ] T007 Write the guard test that every discoverable entry point has a registry row, so an entry point added later without one fails the gate rather than shipping ungated (constitution X clause 14: derive the surface, guard the property)

## Phase 3: User Story 1 - An expensive run cannot be started by picking a different command (P1) 🎯 MVP

**Goal**: Every route in the threat model refuses or prompts.
**Independent test**: Attempt each route from [quickstart.md](quickstart.md) §1; each refuses and names its make target.

- [x] T008 [US1] Create `scripts/make-only-hooks.sh` (PreToolUse on Bash) blocking bare `python3 -m l7r.diagram.<entry point>`, bare `pytest`, `make -f`/`--file`/`--makefile`, and inline `REF_WHY=`/`REF_OK=` overrides - following the structure and voice of the five existing `scripts/*-hooks.sh`
- [x] T009 [US1] Make every refusal message name the make target that does the same job (FR-006), per the project's tips-live-in-error-output rule - a refusal that does not say what to run instead is a bug
- [x] T010 [US1] Wire `make-only-hooks.sh` into `.claude/settings.json` as a `PreToolUse` hook with matcher `Bash`
- [x] T011 [US1] **FIRES**: create `scripts/test-make-only-hooks.sh` asserting each blocked shape IS blocked - one case per threat-model row
- [x] T012 [US1] **STAYS QUIET**: extend `scripts/test-make-only-hooks.sh` asserting ordinary `make <target>` calls, reads of source files, and `scripts/` invocations are NOT blocked
- [ ] T013 [US1] Call `assert_via_make` at the top of each expensive operation, including the in-process entry points, so importing the engine and calling it directly is refused on the same terms (FR-008)
- [ ] T014 [US1] Add `assert_via_make` to `.claude/skills/diagram/tests/conftest.py` so the suite itself refuses when run outside make
- [x] T015 [US1] **FIRES**: create `.claude/skills/diagram/tests/test_invocation.py` covering no-make-in-ancestry, foreign `cwd`, foreign `-f`, and the in-process call
- [x] T016 [US1] **STAYS QUIET**: extend `test_invocation.py` covering make-direct, make→`sh -c`, nested `$(MAKE)`, and a multiprocessing child three levels down (research R1's four measured shapes)
- [x] T017 [US1] **STAYS QUIET**: assert in `test_invocation.py` that the `/proc` walk happens once across repeated calls, so a refactor that drops the cache is caught rather than silently slow (research R4)
- [ ] T018 [US1] Add a make target for every operation in the registry so each refusal has somewhere to point (FR-001, *"we want make commands for everything"*)
- [ ] T019 [US1] Verify [quickstart.md](quickstart.md) §1 by hand and record the actual refusal text in this file

## Phase 4: User Story 2 - The cheap path stays cheap, and needs no override (P2)

**Goal**: Correct work never prompts.
**Independent test**: [quickstart.md](quickstart.md) §2 and §3 - `make reference` and the diagnostics run clean; the prompt defaults to CANCEL.

- [x] T020 [US2] Give the read-only diagnostics make targets that carry REFUSAL but never PROMPTING (FR-007, and the round-1 adjudication recorded in spec.md Scope Boundaries)
- [x] T021 [US2] **STAYS QUIET**: assert in `scripts/test-make-only-hooks.sh` that a diagnostic run through its make target produces no prompt and no override
- [ ] T022 [US2] Extend the override prompt to satisfy FR-010/FR-011 across every gated target: explanation, CANCEL default, written reason, refusal when non-interactive
- [ ] T023 [US2] **FIRES**: assert the non-interactive override is REFUSED (the tier-3 failure - a backgrounded `FULL=1` run that nothing could answer for)
- [x] T024 [US2] **STAYS QUIET**: assert `make reference` completes with zero prompts and zero overrides, and compare wall-clock against T002 (SC-002)
- [ ] T025 [US2] Add `outcome` (`permitted`/`cancelled`/`refused`) to `dev/bypass-log.jsonl` writes per [data-model.md](data-model.md) - without it a session that backed out is indistinguishable from one that never tried (FR-012)
- [ ] T026 [US2] Add a make target for render-sync, refusal-only and NOT subject to reference-first ordering (FR-009, FR-009a - CLAUDE.md:282 forbids a second generator run in main's tree)
- [ ] T027 [US2] Change `scripts/sync-with-main.sh` line 138 from the bare `python3 -m l7r.diagram.pipeline.render_cache` to the T026 make target
- [ ] T028 [US2] **STAYS QUIET**: run the full stop-work ritual and confirm render-sync completes with no refusal and no prompt (SC-004, [quickstart.md](quickstart.md) §7)
- [ ] T029 [US2] Apply FR-014 - every expensive target verifies the reference settlement first and refuses to proceed when it fails - and confirm the render-sync target is exempt per FR-009a

## Phase 5: User Story 3 - Weakening a guard is visible and breaks the build (P3)

**Goal**: The guards guard themselves.
**Independent test**: [quickstart.md](quickstart.md) §5 and §6.

- [x] T030 [US3] Create `scripts/guard-file-hooks.sh` (PreToolUse on `Edit|Write|NotebookEdit`) intercepting edits to `Makefile`, `scripts/*-hooks.sh`, and `.claude/settings.json`, requiring a stated reason (FR-013)
- [x] T031 [US3] Wire `guard-file-hooks.sh` into `.claude/settings.json`
- [x] T032 [US3] **FIRES**: create `scripts/test-guard-file-hooks.sh` asserting an edit to each guard file is intercepted
- [x] T033 [US3] **STAYS QUIET**: assert in `scripts/test-guard-file-hooks.sh` that an edit to `.claude/agents/*.md` is NOT intercepted - removed from the guard list at fidelity round 1 as unrequested, and because it would obstruct the project's own procedure for improving review subagents
- [x] T034 [US3] **THE DECORATION CHECK (SC-003)**: in a scratch copy, delete each guard in turn and confirm at least one test goes red naming it. A guard whose test still passes when the guard is gone is decoration, and this task is the only thing that distinguishes the two. Record the result per guard in this file

## ADDED MID-FEATURE: make `quick` actually quick (GM 2026-08-24)

The GM, on learning `quick` measured 254 s: *"that is really bad, and that is basically making it so
that our guards and gates are driving us towards the quick make target but then the quick make target
isn't even quick, which kind of defeats the purpose of the whole thing."* Correct, and in scope - this
feature is about properly gated and properly TIMED make targets.

- [x] T043 Mark every map-rolling test with `@pytest.mark.rolls_map` and switch `quick` from a file
      deselect to the marker - the file list claimed in its own output that map-rolling tests were
      excluded while the three polder tests ran every time
- [x] T044 Add `tests/test_markers.py` so the marker cannot rot, matching AST CALLS rather than text
- [x] T045 Remove the reference-map roll from `quick` - its contract is "no maps"
- [x] T046 Add `make durations`, an operation with no target, so "why is this slow" has a route that
      is not the override
- [x] T047 Give `quick` a time BUDGET that fails the target, so drift alarms instead of accumulating

**254 s -> 33 s.**

## Phase 6: Polish & Cross-Cutting

- [x] T035 Record the threat model and which layer closes each tier in `scripts/make-only-hooks.sh`'s header comment (FR-017), so a later session can tell whether a proposed change reopens a known route
- [x] T036 [P] Update `.claude/skills/diagram/CLAUDE.md`'s always-on section with the new command map, stating plainly that `make done` is ~5.5 minutes and is NOT the quick check - the mistake that cost this feature its predecessor
- [x] T037 [P] Update the root `CLAUDE.md` iteration-loop section to point at the gated targets
- [x] T038 Enumerate every remaining possible bypass against SC-006 and confirm each either appears in a git diff or could not be described as diligence. **Any that fails this test MUST be recorded in spec.md Assumptions and excluded from SC-006 explicitly** - an unenumerated hole under a criterion claiming enumeration is a false claim
- [ ] T039 Run `ruff format` + `ruff check` + `mypy --strict` and confirm 100% coverage on `_invocation.py` (Principle X)
- [ ] T040 Run the full gate ONCE at the end, backgrounded, and compare against T001's baseline - no regressions (Principle XIII)
- [x] T041 Audit `dev/bypass-log.jsonl` for entries added during this feature and state in writing whether each was justified (constitution closing step)
- [ ] T042 Tick every completed task in this file and confirm no task is left unticked that was in fact done

## Dependencies

- Phase 1 → Phase 2 → Phase 3 (US1). US1 is the MVP and is independently shippable.
- US2 (Phase 4) depends on T004-T006 only; it does not depend on US1's hook.
- US3 (Phase 5) is fully independent of US1 and US2 - `guard-file-hooks.sh` shares no code with the others.
- T034 depends on every guard existing and is the last substantive task.

## Parallel opportunities

- T003 during T001/T002 (the baseline runs in a worktree; the inventory is a read).
- Phase 5 (T030-T033) can run alongside Phase 4 entirely - different files, no shared code.
- T036 and T037 are different files and parallel.

## Implementation strategy

**MVP = Phase 1 + Phase 2 + Phase 3 (US1).** That alone closes every tier the threat model actually
observed. US2 makes it safe to live with, and US3 closes the tiers above those observed.

**Scope limit, unchanged**: a working reference hamlet at a single seed. This feature touches no map
geometry and fixes no failing seed.

## T034 result: the decoration check (SC-003)

Each guard removed in a scratch copy; each must turn at least one test red.

| guard | mutation | result |
|---|---|---|
| `scripts/make-only-hooks.sh` | every match pattern disabled | **15 of 26 failed** |
| `scripts/guard-file-hooks.sh` | the guard-file matcher disabled | **7 of 17 failed** |
| `l7r/diagram/_invocation.py` | `_compute` forced to accept everything | **7 of 25 failed** |

All three have teeth.

**AND THE CHECK ITSELF NEARLY FAILED THE SAME WAY IT EXISTS TO CATCH.** The first attempt at the
`guard-file-hooks.sh` mutation used a `sed` whose pattern did not match (one space versus two before
`;;`), so the file was unmodified and the run reported **17 passed, 0 failed** - which reads exactly
like "this guard is decoration". A `diff` against the original is what caught it.

So the rule this task teaches is one level up from the task: **a mutation test must assert that its
mutation applied.** Every mutation above now goes through a Python replace with
`assert s.count(old) == 1` and aborts rather than reporting a result it cannot stand behind. A
silently-unapplied mutation produces a false PASS on the guard and a false FAIL on the check, and
both readings are wrong in the direction that costs you the guard.

## Baseline

<!-- T001/T002 fill this in. Recorded, not remembered (Principle XIII). -->

| | value | taken |
|---|---|---|
| gate verdict, detached worktree `/tmp/base127` | **2 failed, 3420 passed** - both failures SPURIOUS, see below | 2026-08-24 |
| gate verdict, effective baseline (the clone) | **green** - 3450 passed, both coverage floors met | 2026-08-24 |
| `make reference` wall-clock | **26 s** | 2026-08-24 |

**THE DETACHED-WORKTREE BASELINE IS NOT VALID FOR EVERY TEST, and this cost a false alarm.**
Principle XIII mandates taking the baseline in a detached worktree rather than by stashing, and that
is right - but a fresh worktree does not carry the GITIGNORED render artifacts. It had 20 PNGs
against the clone's 28, so two tests failed there that pass in the clone:

- `tests/pipeline/test_render_cache.py::test_every_live_pool_png_matches_its_own_svg_viewbox`
- `tests/tools/test_scatter_audit.py::test_crown_fills_covers_every_recorded_crown`

Both verified passing in the clone on unmodified code. They are worktree artifacts, NOT pre-existing
failures, and treating them as either a regression or a ledgered failure would have been wrong.
**Effective baseline: the clone's own green run.** Recorded rather than remembered, per XIII.

**Also recorded because it happened again**: the background gate was launched as
`( make done > log; echo "rc=$?" >> log )`, so the completion notification reported exit 0 while the
gate had FAILED - the subshell exits with `echo`'s status, not make's. There is a standing memory
about this exact wrapper and it was repeated anyway. Read the log, never the notification's code.
