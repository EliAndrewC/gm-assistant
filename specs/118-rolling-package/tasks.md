# Tasks: settlement/rolling.py -> settlement/rolling/, and roll_village Decomposed

**Feature**: `118-rolling-package` | **Plan**: [plan.md](plan.md) | **Spec**: [spec.md](spec.md)

**Runbook**: every command is in [quickstart.md](quickstart.md); tasks reference its step numbers
rather than repeating them. All paths are relative to `.claude/skills/diagram/` unless stated.

`$SCRATCH` = `/tmp/claude-1000/-gm-assistant/17b6cc0a-e82e-420c-b23a-d446bdfb4f3e/scratchpad`

---

## Phase 1: Setup

- [x] T001 Confirm the clone is synced and the tree is clean: `git -C /gm-assistant/.clones/diagram-architecture status --short` prints nothing but `specs/118-*`, and `scripts/sync-with-main.sh sync-in` has run for this work unit
- [x] T002 Record the Principle XIII baseline in plan.md's Constitution Check - `make done` on unmodified code (DONE 2026-08-17 at `15fac91`: exit 0, 3263 passed in 119.77s)
- [x] T003 Capture the byte-identity baseline into `$SCRATCH/118-baseline.sha` from a scratch copy at the pre-change commit, per quickstart step 2 - `--frozen-ok` is required, and the log must show a line per generator before the hashes are trusted

## Phase 2: Foundational (blocks every user story)

- [x] T004 Verify the transformer's partition covers the class exactly: run `specs/118-rolling-package/split_rolling.py` against a scratch copy first and confirm it neither REFUSES nor leaves a member unassigned
- [x] T005 Verify the generation cache can SEE a package (quickstart step 0) - perturb a numeric literal in a member a live map executes, confirm `pipeline/regen.py` prints `REGENERATED` not `CACHED`, then revert. A cache blind to the new layout makes every later sweep a green test of nothing

---

## Phase 3: User Story 1 - Behavior-preserving package split (P1) 🎯 MVP

**Goal**: `settlement/rolling.py` becomes `settlement/rolling/`, six submodules under a composed
`RollingMixin`, with `settlement/core.py` byte-unchanged and zero consumer changes.

**Independent test**: the pool regenerates byte-identically and `make done` is green, with
`roll_village` still one 256-line body. That is a complete, shippable feature on its own.

- [x] T006 [US1] Run the transformer for real from `.claude/skills/diagram/`: `python3 ../../../specs/118-rolling-package/split_rolling.py`, creating `settlement/rolling/{__init__,roll,seeds,bundle,fit,place,farmsteads}.py`
- [x] T007 [US1] Prune the copied import headers: `python3 -m ruff check --select F401 --fix settlement/rolling/` then `python3 -m ruff format settlement/rolling/`
- [x] T008 [US1] Delete the old module and its stale bytecode: `git rm settlement/rolling.py` and `find settlement -name __pycache__ -prune -exec rm -rf {} +` (a leftover `rolling.cpython-*.pyc` can shadow the package, and the failure looks nothing like its cause)
- [x] T009 [US1] Write `settlement/rolling/CLAUDE.md` - the package index, one "look here when" row per submodule, plus the invariants sections the six sibling packages carry (composition, cross-submodule calls, monkeypatching)
- [x] T010 [P] [US1] Add the C1 composed-surface guard to `tests/settlement/test_rolling.py` - a SUPERSET assertion over the 43-name census in `contracts/mixin-surface.md`, using `vars(cls)` over the MRO rather than a callable filter (`_NUC_SIDES` is not callable)
- [x] T011 [P] [US1] Add the C2 no-duplicate-definition guard to `tests/settlement/test_rolling.py` - each member name appears in exactly one sub-mixin's `vars()`
- [x] T012 [US1] Prove BOTH guards RED before trusting them (contracts/mixin-surface.md, "Proving the guard"): drop a member from a module tuple and confirm C1 names it; assign a member to two modules and confirm C2 names it; restore. A guard that has only ever been green is indistinguishable from one that is not running
- [x] T013 [US1] Run the cheap linters (quickstart step 4): `python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy`
- [x] T014 [US1] Run the byte-identity sweep (quickstart step 5) and confirm `IDENTICAL` **and** that the log shows every generator actually regenerated - an early death leaves copied bytes that hash equal and prove nothing
- [x] T015 [US1] Census the comments (quickstart step 6b): `grep -c '^\s*#'` on the pre-split file must equal the sum across `settlement/rolling/*.py`. Target: 0 lost
- [x] T016 [US1] Confirm the blast radius (quickstart step 6c): `git diff --stat HEAD` shows no `settlement/core.py`, no pool generator, no tool, no check
- [x] T017 [US1] Run the gate backgrounded and unpolled: `make done > $SCRATCH/118-gate-split.log 2>&1`, nothing appended. Tail the log before believing green
- [x] T018 [US1] Commit the split in the clone (no push yet - the decomposition follows in the same work unit)

**Checkpoint**: US1 is independently shippable here.

---

## Phase 4: User Story 2 - roll_village decomposed into stages (P2)

**Goal**: `roll_village` becomes an orchestrator over seven named stages, no function over ~150 raw
lines, with the frame carried by an explicit value object.

**Independent test**: the same byte-identity sweep, re-run. Identical artifacts prove the stages
preserved call order - which is the entire safety argument, since `roll_village` draws nothing from
the main RNG stream itself.

- [x] T019 [US2] Add the `_MarginFrame` frozen dataclass to `settlement/rolling/roll.py` - eight floats (`ccx`, `ccy`, `alx`, `aly`, `tdx`, `tdy`, `lat`, `dep`) and a `to_screen` method carrying the closure's body verbatim
- [x] T020 [US2] Extract `_roll_knobs` from `roll_village` (source lines 45-65) in `settlement/rolling/roll.py` - the six `resolve()` calls and the gravity-valid water-source roll, in unchanged order
- [x] T021 [US2] Extract `_roll_field` (source 66-87) in `settlement/rolling/roll.py` - sluice anchor, plot texture, `build_comb`, envelope, archetype knob, `draw_comb_field`, land-use overlay
- [x] T022 [US2] Extract `_roll_margin_frame` (source 88-149) in `settlement/rolling/roll.py`, returning `_MarginFrame` plus the field bbox and the cluster rng - carrying the bundle-pitch and band-sizing comment banks verbatim
- [x] T023 [US2] Extract `_roll_cluster` (source 150-184) in `settlement/rolling/roll.py` - lane skeleton, the headman offset ring, the seed loop, `farmsteads()`. Leave the seed loop's arithmetic literal rather than routing it through `to_screen` (data-model.md invariant 4)
- [x] T024 [US2] Extract `_roll_wells` (source 185-199) in `settlement/rolling/roll.py`, taking `hs` as a parameter
- [x] T025 [US2] Extract `_roll_windbreak` (source 200-227) in `settlement/rolling/roll.py`, taking `hs` as a parameter and PRESERVING its unguarded division (data-model.md invariant 3 - the asymmetry with `_roll_wells`' `if hs:` is pre-existing behavior, not a bug to fix under a refactor)
- [x] T026 [US2] Extract `_roll_civic` (source 228-241) in `settlement/rolling/roll.py` - shrine plus the numerological torii march
- [x] T027 [US2] Reduce `roll_village` to the orchestrator: signature, docstring, meta writes, fall vector, the eight calls in unchanged order, the returned knob dict
- [x] T028 [US2] Verify no main-stream draw was added, removed or reordered - diff the ordered call sequence of `lane` / `try_place` / `farmsteads` / `place_wells` / `village_grove` / `hinterland` / `bridges` / `channel_footbridges` / `place_kosatsuba` against the pre-decomposition body
- [x] T029 [US2] Run the cheap linters (quickstart step 4)
- [x] T030 [US2] Assert the ~150-line bar with the AST check in quickstart step 8 - must print only `checked` (SC-002)
- [x] T031 [US2] Re-run the byte-identity sweep (quickstart step 5). `honda`, `shimizu` and `kikuta` are the three maps that exercise `roll_village`, and all three are FROZEN, so `--frozen-ok` is what makes this task meaningful at all
- [x] T032 [US2] Re-census the comments (quickstart step 6b) - `roll_village` holds the heaviest banks in the module
- [ ] T033 [US2] Run the gate backgrounded and unpolled: `make done > $SCRATCH/118-gate-stages.log 2>&1`

**Checkpoint**: both halves complete and independently proven.

---

## Phase 5: User Story 3 - The indexes tell the truth (P3)

**Goal**: no index or standing doc asserts a fact this feature made false.

**Independent test**: read each updated file and follow its rows to files that exist.

- [x] T034 [P] [US3] Update the `rolling.py` row in `settlement/CLAUDE.md` to point at the package and its own index, in the form the six sibling rows use. **Expect a merge conflict here** - feature 117 is editing the same table concurrently
- [x] T035 [P] [US3] Update `settlement/civic_grounds/CLAUDE.md`, which cites `rolling.py (1,197)` as a then-larger unsplit file, so it does not assert as current a fact this feature made false
- [x] T036 [P] [US3] Close the "next clause-12 candidate: `rolling.py::roll_village`" section in `future-work.md` - and MIGRATE its two measurements rather than deleting them with the task: the measured RNG finding (zero main-stream draws, which contradicted the prediction recorded there) and the one-closure result are reusable facts about the engine
- [x] T037 [US3] Update the spec's Status line with the MEASURED final per-file line counts, the largest surviving function, and the sweep's artifact count - matching the form of 116's Status line

## Phase 6: Polish & Stop-Work

- [x] T038 Record the "why" of the partition where the rule lives, not only in `specs/` - the package `CLAUDE.md` must say WHY the axis is the chain's links and why real tasks stay inside one link (root CLAUDE.md, "Record the why of every research-driven rule")
- [x] T039 Re-run `git diff --stat` against the merge-base and confirm the final blast radius is exactly: `settlement/rolling*`, `settlement/CLAUDE.md`, `settlement/civic_grounds/CLAUDE.md`, `future-work.md`, `tests/settlement/test_rolling.py`, `specs/118-*`
- [x] T040 Delete nothing from `specs/118-rolling-package/split_rolling.py` - the one-shot transformer stays as the record of the partition, exactly as 112-116's do
- [ ] T041 Stop-work ritual: commit in the clone, then `scripts/sync-with-main.sh done` from inside it. **Only** with the gate green and the sweep IDENTICAL - a moved byte is a Principle XIII regression whose only exits are fix, revert, or an explicit GM waiver

---

## Dependencies

```text
Setup (T001-T003)
  └─> Foundational (T004-T005)
        └─> US1 split (T006-T018)          <- MVP, independently shippable
              └─> US2 decomposition (T019-T033)
                    └─> US3 docs (T034-T037)
                          └─> Polish (T038-T041)
```

US2 depends on US1 only because it edits the file US1 creates - not because the split needs the
decomposition. US3 depends on both because T037 records measured results.

**Why US1 and US2 are strictly sequential, when they touch different concerns** (research R6): a
combined change whose sweep reports one moved byte has a suspect set of 43 moved members plus a
rewritten 256-line function. Sequenced, each sweep names its own cause. The cost is one extra sweep.

## Parallel opportunities

- T010 / T011 - the two guard tests, different assertions in the same file (write together, one edit turn)
- T034 / T035 / T036 - three unrelated documentation files
- The stage extractions T020-T026 are NOT parallel: they are successive edits to one function's body

## Implementation strategy

**MVP = User Story 1.** The split alone satisfies clause 13, is the larger token win, and carries no
behavioral risk. If anything about US2 turns out worse than the measurement predicts, US1 ships and
US2 goes back to `future-work.md` with what was learned - which is strictly better than the status
quo, where both are open.

## Format validation

All 41 tasks carry a checkbox, a sequential ID, a `[P]` marker only where the files are disjoint, a
`[US#]` label in the story phases only (none in Setup, Foundational or Polish), and a concrete file
path or a named command.
