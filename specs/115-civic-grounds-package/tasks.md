# Tasks: settlement/civic_grounds.py -> settlement/civic_grounds/ Package Split

**Input**: Design documents from `specs/115-civic-grounds-package/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/mixin-surface.md,
quickstart.md, split_civic_grounds.py

**Tests**: test tasks ARE included - the spec requires a red-green guard test (FR-003) and the
byte-identity harness is the feature's oracle.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1 (pure move, P1), US2 (guard proven, P2), US3 (stable-yard decomposition, P3),
  US4 (index, P4)
- All paths relative to the session clone root unless absolute

**Working directory for every command**: `.claude/skills/diagram/`

**Scratch root**: `/tmp/claude-1000/-gm-assistant/51f99e4b-813a-471d-a5a0-c95c154a36bf/scratchpad`

**Active feature**: pass `SPECIFY_FEATURE=115-civic-grounds-package` inline on every spec-kit script
call. Do NOT rely on `.specify/feature.json` - it is a git-tracked single-session pointer and a peer
session repointed it to `116-shrines-wells-package` mid-chain. See Notes.

---

## Phase 1: Setup

**Purpose**: establish the oracle, and prove the oracle can actually see the thing it will measure.
Nothing in Phase 3+ is safe without both.

- [ ] T001 Confirm the clone is synced to main's tip and re-measure `.claude/skills/diagram/settlement/civic_grounds.py`: expect 1,162 raw lines and 22 `CivicGroundsMixin` members, ALL `FunctionDef` (no class-level `Assign`, unlike feature 114). Re-measure rather than trust plan.md - a peer session may have moved the tree between planning and implementation, and one demonstrably did during this feature's planning
- [ ] T002 Run quickstart.md step 0 BEFORE the split and record the output in this file's Notes: `gencache.engine_files()` must list `settlement/civic_grounds.py` and must report `tests contributing: 0`. This is the pre-image of the post-split check in T018
- [ ] T003 Capture the byte-identity baseline per quickstart.md step 1: copy `.claude/skills/diagram/` to `$SCRATCH/115-baseline/diagram`, run `python3 -m pipeline.regen --no-cache --frozen-ok pool/*/*.gen.py` there, and write `sha256sum` of every `pool/**` `.json`/`.svg`/`.png` to `/tmp/115-baseline.sha`
- [ ] T004 In the SAME baseline copy, run `python3 -m pipeline.regen --no-cache --frozen-ok wip/shiro-daika.gen.py` and append its artifact hashes to `/tmp/115-baseline.sha`. Budget over 6 minutes. This map is the ONLY consumer of `precinct_interior` in the tree, so features 112/114's blanket exclusion of it would leave a moved member with no artifact-level proof (research R11)
- [ ] T005 Record the baseline sweep's own verdict in this file's Notes (generator count, `REGENERATED` count, artifact count, any gen that failed in the PRE-split tree), so a Stage 1 failure can be told apart from a pre-existing one

**Checkpoint**: an oracle exists, it can fail, and it is known to be looking at the right file.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: the guard test and the transformer. Blocks Phase 3. These tasks deliver most of US2;
its remaining red proof cannot run until sub-mixins exist and so appears in Phase 3.

**CRITICAL**: T007 must be observed failing before T010 lands.

- [ ] T006 Write the composed-surface guard test in `.claude/skills/diagram/tests/settlement/test_civic_grounds.py` per contracts/mixin-surface.md: assert the composed `CivicGroundsMixin` exposes AT LEAST the 22-name frozenset (subset, not equality - C1), assert no two sub-mixins define the same name (C2), assert all 22 resolve on `Settlement` itself (C3). Derive the sub-mixin list from `CivicGroundsMixin.__mro__` rather than importing `settlement.civic_grounds.funerary` and its siblings by name - that is what lets the guard be written and run BEFORE the split exists
- [ ] T007 Prove C1 RED before the split and record the failure text in this file's Notes: delete one method from `CivicGroundsMixin`, observe C1 name it, revert
- [ ] T008 Note in this file's Notes that C2's red proof is deferred to T017 and why: a duplicate-name collision needs two sub-mixins to live in, so it cannot be staged before the package exists. Unlike feature 114 there is NO third breakage to stage - `CivicGroundsMixin` has no class-level attributes (T001), so the attribute half of the census is vacuous here
- [ ] T009 [P] Verify `specs/115-civic-grounds-package/split_civic_grounds.py` runs its refusal paths: temporarily drop a name from a `MODULES` tuple and confirm it exits non-zero printing `missing=`, then assign one name to two modules and confirm the duplicate-assignment refusal fires, then restore. Confirm NEITHER refusing run created `settlement/civic_grounds/` - a half-written package beside a live module is worse than no package

**Checkpoint**: guard proven to fire on the assertion that can fire yet; transformer proven to refuse
both ways.

---

## Phase 3: User Story 1 - Behavior-preserving package split (Priority: P1) 🎯 MVP

**Goal**: `settlement.civic_grounds` becomes a five-module package; `core.py` untouched; every
artifact byte-identical. `_stable_yard` moves UNCHANGED - the clause-12 debt stands until Phase 4, so
that a hash mismatch here can only mean the move broke something.

**Independent test**: the quickstart sweep diff is empty, `git status` under `pool/` is clean, and
`make done` is green with `core.py` byte-unchanged.

- [ ] T010 [US1] Run the transformer from `.claude/skills/diagram/` to create `settlement/civic_grounds/` with `funerary.py`, `justice.py`, `civic.py`, `lodging.py`, `stable_yard.py`, assigning members exactly per data-model.md Part 1 (5 / 3 / 6 / 7 / 1 members)
- [ ] T011 [US1] Confirm the transformer wrote `settlement/civic_grounds/__init__.py` composing `class CivicGroundsMixin(FuneraryGroundsMixin, JusticeGroundsMixin, CivicWorksMixin, LodgingMixin, StableYardMixin)`, with the docstring explaining it exists to preserve `core.py`'s single import and naming the two by-design cross-module calls (`precinct_interior` -> `cemetery`, `flush_stable_yards` -> `_stable_yard`)
- [ ] T012 [US1] Confirm each of the five modules carries `if TYPE_CHECKING: from ..core import Settlement` (two-dot path) and that every method kept its `self: "Settlement"` annotation - FR-006
- [ ] T013 [US1] Delete `.claude/skills/diagram/settlement/civic_grounds.py` (invariant: a stale module beside a package of the same name is a shadowing hazard) - FR-007
- [ ] T014 [US1] Verify `.claude/skills/diagram/settlement/core.py` is byte-unchanged (`git diff --stat -- settlement/core.py` empty) - FR-002, contract C6
- [ ] T015 [US1] Verify the move was PURE, per quickstart.md step 6: every comment line in the pre-split class body survives somewhere in the package (`comment lines lost: 0`). This file holds the densest researched grounding in the engine - the Qingming Shanghe Tu gate convention, the ox-consumption arithmetic behind the trough count, the two-round dung-heap clearance history - and a move that drops one is not pure (research R5)
- [ ] T016 [US1] Prune the copied import headers and format: `python3 -m ruff check --select F401 --fix settlement/civic_grounds/ && python3 -m ruff format settlement/civic_grounds/`, then the full cheap prefix `python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy`
- [ ] T017 [US2] Now that sub-mixins exist, prove guard C2 RED and record the failure text in Notes: copy one method into a second sub-mixin, observe C2 name the collision and both classes, revert. FR-003 is not satisfied until this is done
- [ ] T018 [US1] Re-run quickstart.md step 0 POST-split: every `settlement/civic_grounds/*.py` must appear in `gencache.engine_files()` and `tests` must still contribute 0. A nested package falling out of the engine fingerprint would make every later sweep a false green
- [ ] T019 [US1] Run the WHOLE affected test file, not a `-k` subset: `python3 -m pytest tests/settlement/ -q -n auto --no-cov`. Unlike feature 114 there is no `tests/tools/` filename assertion to carry (research R6)
- [ ] T020 [US1] Run the byte-identity sweep per quickstart.md step 5 (pool AND the one `wip/shiro-daika` run) and require ALL THREE of: regen exit code 0, a `REGENERATED` count equal to the baseline's, and an EMPTY diff against `/tmp/115-baseline.sha`. Run it with nothing else heavy in flight - an OOM-killed render leaves the committed artifacts in place and the diff comes back empty having tested nothing
- [ ] T021 [US1] Confirm `git status --porcelain -- .claude/skills/diagram/pool` prints nothing
- [ ] T022 [US1] Check combined `settlement/` coverage (`python3 -m coverage report --include='*/settlement/*'`) is at or above `SETTLEMENT_COV_FLOOR` (94, in `.claude/skills/diagram/Makefile:62` - the SKILL's Makefile, not the webapp's) and, critically, that it did not MOVE. A pure move relocates executable lines without adding or removing one, so any movement is a signal to investigate (research R7)
- [ ] T023 [US1] Confirm `GEN_TIME_BUDGETS` in `tests/test_villages.py` still passes unmodified
- [ ] T024 [US1] Run `make done` backgrounded, once; read the log tail before believing green (no `; echo EXIT=$?` wrapper, which makes a failed gate report exit 0)
- [ ] T025 [US1] Commit Stage 1 ALONE, before any decomposition work starts. Unlike feature 114 this feature has a second behavior-changing stage, so the two-commit shape is real here: a bisect must be able to separate "the move broke it" from "the decomposition broke it"

**Checkpoint**: US1 and US2 are complete and independently shippable. If Stage 2 were abandoned
here, the clause-13 debt is already paid and only the clause-12 debt stands.

---

## Phase 4: User Story 3 - The 335-line stable yard becomes readable stages (Priority: P3)

**Goal**: `_stable_yard` becomes an outer method holding the RNG bracket and seven named stage calls,
each stage under ~150 lines, each carrying its banner comment verbatim.

**Independent test**: the byte-identity sweep is empty AGAINST THE SAME BASELINE, which given a
global order-sensitive RNG stream is strong proof the extraction was faithful.

**CRITICAL - the three binding ordering rules** (data-model.md Part 2, research R12). Re-read them
before each extraction, not once at the start:

1. The `random.getstate()` / `random.seed(...)` / `random.setstate(st)` bracket stays in the OUTER
   method. No stage seeds its own stream or runs outside the bracket.
2. Stages are called in source order and no RNG draw moves across a stage boundary.
3. No stage becomes eagerly evaluated where it was previously short-circuited. Stages 5 and 6 have
   branches whose draw count depends on the map - hoisting a candidate list out of one to tidy a
   signature changes the draw count on maps that take the other branch. It looks like a cleanup and
   is a bug.

- [ ] T026 [US3] Extract stage 1 `_yard_keepouts` from `settlement/civic_grounds/stable_yard.py` - the corridor buffers and the tight footprint keep-out, carrying the "~3px margin / NOT the wide urban halo / NOT block_polys" comment and the farrier's-forge-stands-ON-the-yard note (GM 2026-07-25) verbatim
- [ ] T027 [US3] Extract stages 2 and 3 - `_yard_litter` (the "1. BEATEN-EARTH scuff + STRAW litter" feathered scatter) and `_yard_seat` (the "2. FURNITURE" greedy ring walker, carrying the probes doctrine: tips and edges tested, not centers, GM 2026-07-24)
- [ ] T028 [US3] Extract stages 4 and 5 - `_yard_road_rail` and `_yard_interior_rails` - carrying the HITCHING RAILS block (bare posts, no animal glyphs, GM 2026-07-25) and the bounded-retries reasoning. Promote the nested would-be-rail record closure alongside them
- [ ] T029 [US3] Extract stage 6 `_yard_watering` - the largest stage at ~110 lines - carrying the whole WATERING POINT block: the ox-consumption arithmetic, the 2-3 troughs clustered AT a well, the direction-aware offset (Tango's caravan ground), and the dig-your-own-well fallback (the Nagahara defect). Rule 3 applies most sharply here
- [ ] T030 [US3] Extract stage 7 `_yard_dung_heaps`, carrying the two-round map-wide rail-clearance history (15 px -> 24 px check floor / 25 px placement) verbatim. Promote the nested `_glyph_free` closure to a module-level helper, since stages 4, 5, 6 and 7 all read it
- [ ] T031 [US3] Run the fast proxy after EACH of T026-T030 before moving on: `python3 -m pytest tests/settlement/test_civic_grounds.py -q -n auto --no-cov`. Its ~25 stable-yard cases drive the yard through `flush_stable_yards` and are cheap; a failure here localizes to the stage just extracted, where a failure at T035 would not
- [ ] T032 [US3] Confirm the outer `_stable_yard` is now ~35 lines: the docstring, the RNG bracket, the seven stage calls in source order, and the record write. Verify rule 1 by inspection - `getstate`/`seed`/`setstate` appear in the outer method and in no stage
- [ ] T033 [US3] Re-run the comment-survival check from quickstart.md step 7 against `/tmp/115-pre.py`. Expect `comment lines lost: 0` again. Slicing protected the comments across the MOVE; nothing protects them across the DECOMPOSITION, which is why this runs twice - FR-009
- [ ] T034 [US3] Verify contract C4 - every extracted stage is reached: `python3 -m coverage report --include='*/civic_grounds/stable_yard.py' -m` must show no stage function body wholly unexecuted. A stage that exists, type-checks and is never called is the decomposition's own failure mode, and the sweep cannot see it for stages that fire on a minority of maps
- [ ] T035 [US3] Run the byte-identity sweep per quickstart.md step 8 (`pool/` only - the decomposition touches nothing `wip/shiro-daika` exercises beyond the cities). This is the RNG-order proof. If it comes back DIRTY, revert the last stage extracted rather than debugging forward - the diff is per-map and the cause is ordering, not logic
- [ ] T036 [US3] Verify SC-004: the longest function in `settlement/civic_grounds/` is under 150 lines (quickstart.md step 10's AST snippet). Record the new engine-wide maximum, which should now be `rolling.py::roll_village` at 256
- [ ] T037 [US3] Run `make done` backgrounded, read the log tail, then commit Stage 2 ALONE

**Checkpoint**: the engine's largest function is gone. Both behavior-changing stages are separately
bisectable.

---

## Phase 5: User Story 4 - Token-scale package index (Priority: P4)

**Goal**: a session can find the one file it needs without opening a source file.

**Independent test**: a reader given any named civic-grounds concern resolves it from the two index
files alone.

- [ ] T038 [P] [US4] Write `.claude/skills/diagram/settlement/civic_grounds/CLAUDE.md` in the `fields/` + `city/` + `structures/` style: what the package is and why it is a residue bucket rather than one subsystem, a "Look here when" row per submodule, the composition mechanism, the two by-design cross-module calls, and the THREE placement decisions a reader will otherwise want to "fix" - `_ward_fence_cap` with the funerary grounds (R1a), `precinct_interior` in `civic.py` (R1b), `_stable_yard` in a module of its own (R1c) - FR-011, FR-012
- [ ] T039 [US4] Add to that index the stage map for `stable_yard.py` (the seven stages and what each draws), the three RNG ordering rules as a STANDING WARNING for anyone editing the yard - rule 3 especially, since it is the one that looks like an improvement while being a bug - the monkeypatching note (research R8: this package has no module-level names, so class-level patching is unaffected), the coverage note, and the two thresholds a future session would otherwise decide under pressure: `stable_yard.py`'s re-split seam (furniture vs water, data-model.md) and `tests/settlement/test_civic_grounds.py` becoming a directory at ~1,000 lines (research R10)
- [ ] T040 [US4] Replace the single `civic_grounds.py` row in `.claude/skills/diagram/settlement/CLAUDE.md`'s "Look here when" table so it points at the sub-index, matching the shape the `fields/`, `city/` and `structures/` rows already have
- [ ] T041 [P] [US4] Verify every file in `settlement/civic_grounds/` is under 400 raw lines (`wc -l settlement/civic_grounds/*.py | sort -rn`) - SC-001, and record the counts in this file's Notes

---

## Phase 6: Polish and Cross-Cutting

- [ ] T042 [P] Grep the skill for prose naming the FILE `settlement/civic_grounds.py` and update to the package; leave importable-path references (`from .civic_grounds import CivicGroundsMixin`) and prior `specs/NNN` artifacts verbatim as historical record
- [ ] T043 Record in `specs/115-civic-grounds-package/research.md` anything the implementation learned that the plan got wrong - especially any member whose assignment moved from data-model.md's tables, or any stage boundary that had to move to preserve RNG order, with the reason
- [ ] T044 Add to `.claude/skills/diagram/future-work.md`: the two intended follow-up relocations (`_ward_fence_cap` -> `water_ways.py`, `precinct_interior` -> `shrines_wells.py`) and the next clause-12 candidate now that this one is closed - `rolling.py::roll_village` at 256 lines - so they do not live only in this spec. Check first whether feature 116 (`shrines-wells-package`, claimed by a peer session mid-chain) has already moved `shrines_wells.py` into a package, and name the right destination file if so
- [ ] T045 Set this spec's Status to Implemented with the date, and note the final per-file line counts and the new longest-function figure
- [ ] T046 Final `make done` green (skip if everything since the last green gate is markdown - root CLAUDE.md, "Docs-only diffs skip the gate"), then the stop-work ritual: commit in the clone and run `scripts/sync-with-main.sh done`

---

## Dependencies

- **Phase 1 (T001-T005)** blocks everything - no oracle, no safe change.
- **Phase 2 (T006-T009)** blocks Phase 3. T007 (red proof) blocks T010 (the transformer run).
- **T010** blocks everything after it in Phase 3; T017 (the deferred red proof) blocks T025 (the
  Stage 1 commit), because FR-003 is not satisfied until both proofs are recorded.
- **T020** (the sweep) depends on T016 - a package that does not import cannot be swept.
- **Phase 4 depends on T025**, not merely on Phase 3 finishing. The decomposition must run against a
  tree already proven byte-identical AND already committed, or a dirty sweep at T035 has two
  candidate causes instead of one.
- **T026-T030 are strictly sequential** despite touching one file each time - each extraction changes
  the text the next one slices, and T031 gates each on the fast proxy.
- **US4 (Phase 5)** depends only on US3's final shape; T038-T040 are docs-only and skip the gate.
- **Phase 6** depends on US1, US2, US3 and US4.

## Parallel Opportunities

- T009 (transformer refusal check) runs beside T006-T008.
- T038 and T041 run together; T042 can run any time after T013.
- Nothing in Phase 4 parallelizes - see the dependency note above.

Do NOT run either byte-identity sweep (T020, T035) beside `make done` (T024, T037) or any `-n auto`
pytest. That contention is what produced feature 113's false green: an OOM-killed render leaves the
committed artifacts untouched in the scratch tree, and they hash equal to the baseline.

## Notes

### Concurrent-session finding, recorded at planning time

`.specify/feature.json` is a git-tracked pointer holding ONE active feature directory, and every
concurrent session's `/speckit-specify` overwrites it. During this feature's planning a peer session
claimed `116-shrines-wells-package` and its commit repointed `feature.json` to 116; the sync-in
merge took theirs. That is harmless here only because every spec-kit script in this chain is called
with `SPECIFY_FEATURE=115-civic-grounds-package` set inline, which `common.sh`'s
`get_current_branch()` honors ahead of anything else.

The spec-NUMBER claim protocol worked exactly as CLAUDE.md describes - the peer saw 115 already in
main and took 116, with no negotiation. It is only the `feature.json` pointer that does not
serialize, and it was deliberately NOT reverted to 115: stomping it back would just restart the
fight. Worth raising with the GM as a protocol gap rather than fixing unilaterally.

*(the rest filled in during implementation - each red proof's failure text, the baseline verdict,
the final line counts, and anything the plan got wrong)*
