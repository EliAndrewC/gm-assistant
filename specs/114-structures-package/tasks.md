# Tasks: settlement/structures.py -> settlement/structures/ Package Split

**Input**: Design documents from `specs/114-structures-package/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/mixin-surface.md,
quickstart.md, split_structures.py

**Tests**: test tasks ARE included - the spec requires a red-green guard test (FR-003) and the
byte-identity harness is the feature's oracle.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1 (pure move, P1), US2 (guard proven, P2), US3 (index, P3)
- All paths relative to the session clone root unless absolute

**Working directory for every command**: `.claude/skills/diagram/`

**Scratch root**: `/tmp/claude-1000/-gm-assistant/0081234f-d258-4c07-ba00-719616cd2729/scratchpad`

---

## Phase 1: Setup

**Purpose**: establish the oracle, and prove the oracle can actually see the thing it will measure.
Nothing in Phase 3+ is safe without both.

- [x] T001 Confirm the clone is synced to main's tip and re-measure `.claude/skills/diagram/settlement/structures.py`: expect 1,459 raw lines and 33 `StructuresMixin` members (30 `FunctionDef` + 3 `Assign`). Re-measure rather than trust plan.md - a peer session may have moved the tree between planning and implementation
- [x] T002 Run quickstart.md step 0 BEFORE the split and record the output in this file's Notes: `gencache.engine_files()` must list `settlement/structures.py` and must report `tests contributing: 0`. This is the pre-image of the post-split check in T019
- [x] T003 Capture the byte-identity baseline per quickstart.md step 1: copy `.claude/skills/diagram/` to `$SCRATCH/114-baseline/diagram`, run `python3 -m pipeline.regen --no-cache --frozen-ok pool/*/*.gen.py` there, and write `sha256sum` of every `pool/**` `.json`/`.svg`/`.png` to `/tmp/114-baseline.sha`
- [x] T004 Record the baseline sweep's own verdict in this file's Notes (generator count, `REGENERATED` count, artifact count, any gen that failed in the PRE-split tree), so a Stage 1 failure can be told apart from a pre-existing one

**Checkpoint**: an oracle exists, it can fail, and it is known to be looking at the right file.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: the guard test and the transformer. Blocks Phase 3. These tasks deliver most of US2;
its two remaining red proofs cannot run until sub-mixins exist and so appear in Phase 3.

**CRITICAL**: T006 must be observed failing before T010 lands.

- [x] T005 Write the composed-surface guard test in `.claude/skills/diagram/tests/settlement/test_structures.py` per contracts/mixin-surface.md: assert the composed `StructuresMixin` exposes AT LEAST the 33-name frozenset (subset, not equality), assert no two sub-mixins define the same name, assert all 33 resolve on `Settlement` itself. The census must admit class-level ATTRIBUTES as well as methods (`URBAN`, `SERVANT_RANGE_DEPTH_FT`, `_OFFICE_STANDOFF`) - feature 112 needed a separate test because its guard was methods-only
- [x] T006 Prove assertion 1 RED before the split and record the failure text in this file's Notes: delete one method from `StructuresMixin`, observe assertion 1 name it, revert
- [x] T007 Derive the sub-mixin list from `StructuresMixin.__mro__` rather than by importing `settlement.structures.urban` and its siblings by name - that is what lets this guard be written and run BEFORE the split exists (pre-split the derived list is empty and assertion 2 is vacuous). Note in this file's Notes that assertion 2's and assertion 3's red proofs are therefore deferred to T017/T018, and why
- [x] T008 [P] Verify `specs/114-structures-package/split_structures.py` runs its refusal paths: temporarily drop a name from a `MODULES` tuple and confirm it exits non-zero printing `missing=`, then assign one name to two modules and confirm the duplicate-assignment refusal fires, then restore. A transformer that silently drops a method produces a package that imports fine and draws nothing

**Checkpoint**: guard proven to fire on the assertion that can fire yet; transformer proven to refuse
both ways.

---

## Phase 3: User Story 1 - Behavior-preserving package split (Priority: P1) 🎯 MVP

**Goal**: `settlement.structures` becomes a seven-module package; `core.py` untouched; every
artifact byte-identical.

**Independent test**: the quickstart sweep diff is empty, `git status` under `pool/` is clean, and
`make done` is green with `core.py` byte-unchanged.

- [x] T009 [US1] Run the transformer from `.claude/skills/diagram/` to create `settlement/structures/` with `compounds.py`, `ground.py`, `urban.py`, `servants.py`, `packing.py`, `captions.py`, `fixtures.py`, assigning members exactly per data-model.md's seven tables (4 / 2 / 6 / 7 / 3 / 5 / 6 members)
- [x] T010 [US1] Confirm the transformer wrote `settlement/structures/__init__.py` composing `class StructuresMixin(CompoundsMixin, GroundMixin, UrbanBuildingMixin, ServantRangesMixin, PackingMixin, CaptionProbesMixin, PublicFixturesMixin)`, with the docstring explaining it exists to preserve `core.py`'s single import
- [x] T011 [US1] Confirm each of the seven modules carries `if TYPE_CHECKING: from ..core import Settlement` (two-dot path) and that every method kept its `self: "Settlement"` annotation - data-model.md invariant 3
- [x] T012 [US1] Delete `.claude/skills/diagram/settlement/structures.py` (invariant: a stale module beside a package of the same name is a shadowing hazard)
- [x] T013 [US1] Verify `.claude/skills/diagram/settlement/core.py` is byte-unchanged (`git diff --stat -- settlement/core.py` empty) - FR-002
- [x] T014 [US1] Verify the move was PURE, per quickstart.md step 6: every comment line in the pre-split class body survives somewhere in the package (`comment lines lost: 0`). In this project a comment above a method is usually researched grounding - the manor glyph doctrine, the nagaya sourcing, the Pingyao drum-tower footprint - and a move that drops one is not pure (research R5, R9)
- [x] T015 [US1] Prune the copied import headers and format: `python3 -m ruff check --select F401 --fix settlement/structures/ && python3 -m ruff format settlement/structures/`, then the full cheap prefix `python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy`
- [x] T016 [US1] Update the one consumer that asserts on the source FILENAME: `.claude/skills/diagram/tests/tools/test_why_placed.py` line ~80, `"structures.py"` -> `"urban.py"` (the traced `try_building` -> `building` frame now lives in `settlement/structures/urban.py`), with the comment naming feature 114 the way the current one names the 025 split - FR-011, research R6
- [x] T017 [US2] Now that sub-mixins exist, prove guard assertion 2 RED and record the failure text in Notes: copy one method into a second sub-mixin, observe assertion 2 name the collision, revert. FR-003 is not satisfied until this is done
- [x] T018 [US2] Prove the ATTRIBUTE half of assertion 1 RED and record the failure text in Notes: delete `URBAN` from `urban.py`, observe assertion 1 name it, revert. This is the half feature 112's guard could not see (contracts/mixin-surface.md)
- [x] T019 [US1] Re-run quickstart.md step 0 POST-split: every `settlement/structures/*.py` must appear in `gencache.engine_files()` and `tests` must still contribute 0. A nested package falling out of the engine fingerprint would make every later sweep a false green
- [x] T020 [US1] Run the WHOLE affected test files, not a `-k` subset: `python3 -m pytest tests/settlement/ tests/tools/ -q -n auto --no-cov`. `tests/tools/` is included because T016 changed it and a `tests/settlement/`-only run would miss it
- [x] T021 [US1] Run the byte-identity sweep per quickstart.md step 2 and require ALL THREE of: regen exit code 0, a `REGENERATED` count equal to the baseline's, and an EMPTY diff against `/tmp/114-baseline.sha`. Run it with nothing else heavy in flight - an OOM-killed render leaves the committed artifacts in place and the diff comes back empty having tested nothing
- [x] T022 [US1] Confirm `git status --porcelain -- .claude/skills/diagram/pool` prints nothing
- [x] T023 [US1] Check combined `settlement/` coverage (`python3 -m coverage report --include='*/settlement/*'`) is at or above `SETTLEMENT_COV_FLOOR` (94) and, critically, that it did not MOVE. A pure move relocates executable lines without adding or removing one, so any movement is a signal to investigate - a member lost, a module not composed - not a number to re-baseline (research R7)
- [x] T024 [US1] Confirm `GEN_TIME_BUDGETS` in `tests/test_villages.py` still passes unmodified - a pure move should add no per-call overhead in the hot placement loops (`pack`, `rowpack`)
- [x] T025 [US1] Run `make done` backgrounded, once; read the log tail before believing green (no `; echo EXIT=$?` wrapper, which makes a failed gate report exit 0)
- [x] T026 [US1] Landed as ONE commit rather than two. The task list inherited 113's two-commit shape (move, then decomposition) so a bisect could separate them - but this feature has no decomposition stage (research R4), and the index is docs-only, so there is no second behavior change for a bisect to separate. Splitting it would have produced a docs-only second commit and a false suggestion that something behavioral followed the move

**Checkpoint**: US1 and US2 are complete and independently shippable. If Stage 2 were abandoned
here, the clause-13 debt is already paid.

---

## Phase 4: User Story 3 - Token-scale package index (Priority: P3)

**Goal**: a session can find the one file it needs without opening a source file.

**Independent test**: a reader given any named structures concern resolves it from the two index
files alone.

- [x] T027 [P] [US3] Write `.claude/skills/diagram/settlement/structures/CLAUDE.md` in the `settlement/fields/` + `settlement/city/` style: what the package is and why it is a residue bucket rather than one subsystem, a "Look here when" row per submodule, the composition mechanism, the cross-submodule call table (data-model.md), and the THREE decisions a reader will otherwise want to "fix" - `road`/`pasture` in `ground.py` with each member's intended destination (R1a), the four door/solid probes with `servant_ranges` rather than `building` (R1b), and `captions.py` vs `castle_civic.py`'s `place_caption` recorded as an OPEN question (R1c)
- [x] T028 [US3] Add to that index the two thresholds a future session will otherwise decide under pressure: `fixtures.py`'s re-split seam at ~500 lines or any member past ~150 (glyph-drawers vs auto-siters, data-model.md), and `tests/settlement/test_structures.py` becoming a directory at ~1,000 lines (research R11). Plus the monkeypatching note (R8) and the coverage note
- [x] T029 [US3] Replace the single `structures.py` row in `.claude/skills/diagram/settlement/CLAUDE.md`'s "Look here when" table so it points at the sub-index, matching the shape the `fields/` and `city/` rows already have
- [x] T030 [P] [US3] Verify every file in `settlement/structures/` is under 450 raw lines (`wc -l settlement/structures/*.py | sort -rn`) - SC-001, and record the counts in this file's Notes

---

## Phase 5: Polish and Cross-Cutting

- [x] T031 [P] Grep the skill for prose naming the FILE `settlement/structures.py` and update to the package; leave importable-path references (`from .structures import StructuresMixin`) and prior `specs/NNN` artifacts verbatim as historical record
- [x] T032 Record in `specs/114-structures-package/research.md` anything the implementation learned that the plan got wrong - especially any member whose assignment moved from data-model.md's table, with the reason
- [x] T033 Add the three intended follow-up relocations (`road` -> `water_ways.py`, `pasture` -> `land.py`, the possible `captions.py` -> `castle_civic.py` fold) to `.claude/skills/diagram/future-work.md` as named follow-ups with their reasoning, so they do not live only in this spec
- [x] T034 Set this spec's Status to Implemented with the date, and note the final per-file line counts
- [ ] T035 Final `make done` green (skip if everything since the last green gate is markdown - root CLAUDE.md, "Docs-only diffs skip the gate"), then the stop-work ritual: commit in the clone and run `scripts/sync-with-main.sh done`

---

## Dependencies

- **Phase 1 (T001-T004)** blocks everything - no oracle, no safe change.
- **Phase 2 (T005-T008)** blocks Phase 3. T006 (red proof) blocks T009 (the transformer run).
- **T009** blocks everything after it in Phase 3; T017/T018 (the deferred red proofs) block T026
  (the commit), because FR-003 is not satisfied until all three proofs are recorded.
- **T021** (the sweep) depends on T015 - a package that does not import cannot be swept.
- **US3 (Phase 4)** depends only on US1's final shape; T027-T029 are docs-only and skip the gate.
- **Phase 5** depends on US1, US2 and US3.

## Parallel Opportunities

- T008 (transformer refusal check) runs beside T005-T007.
- T027 and T030 run together; T031 can run any time after T012.
- T017 and T018 are two independent breakages of the same file and are cheap enough to run in one
  turn, but each must be reverted before the next.

Do NOT run the byte-identity sweep (T021) beside `make done` (T025) or any `-n auto` pytest. That
contention is what produced feature 113's false green: an OOM-killed render leaves the committed
artifacts untouched in the scratch tree, and they hash equal to the baseline.

## Notes

### T001 - the census, re-measured rather than trusted

`settlement/structures.py`: **1,459 raw lines, 33 `StructuresMixin` members** -
`Counter({'FunctionDef': 30, 'Assign': 3})`. Matches plan.md exactly; no peer session had moved the
tree.

### T002 / T019 - the oracle can see what it measures

Pre-split: 85 engine files, structures files seen `['settlement/structures.py']`, tests contributing
0. Post-split: **92** engine files, structures files seen `__init__.py`, `captions.py`,
`compounds.py`, `fixtures.py`, `ground.py`, `packing.py`, `servants.py`, `urban.py` - all eight - and
tests still contributing 0. The nested package is walked exactly as `settlement/fields/` and
`settlement/city/` are, so no sweep is a false green from a stale cache.

### T004 - the baseline sweep's own verdict

**28 generators, 889 artifacts** (`.json` + `.svg` + `.png`) under `pool/`, hashed into
`/tmp/114-baseline.sha`. `REGEN EXIT=0`, zero occurrences of `traceback` / `error` / `failed` in the
log, `FROZEN: 0` (so `--frozen-ok` did exercise the 19 legacy maps). Any Stage 1 failure is therefore
attributable to Stage 1.

### T006 - guard assertion 1 proven RED for a METHOD (pre-split)

Deleted `_office_records` from `StructuresMixin`:

    E       AssertionError: missing=['_office_records']
    1 failed, 51 deselected

Reverted; `structures.py` back to 1,459 lines.

### T007 - why two of the three red proofs are deferred to T017/T018

A duplicate-name collision needs two sub-mixins to live in, and an attribute deletion needs a
sub-mixin to delete it FROM, so neither can be staged before the package exists. Feature 112's task
list put both of its red proofs before its transformer ran, which is not actually possible; 113
recorded the correction and this feature inherits it.

**The guard was written to work at BOTH stages**, which is what makes the deferral safe rather than
merely necessary: `_structures_submixins()` derives the sub-mixin list from
`StructuresMixin.__mro__` instead of importing `settlement.structures.urban` and friends directly.
Pre-split the list is empty and the collision assertion is vacuous; post-split it is the seven.

### T008 - the transformer proven to REFUSE, both ways

Dropped `_office_records` from the `servants` tuple in `MODULES`:

    REFUSING: partition does not cover the class. missing=['_office_records'] extra=[]
    exit=1

Then assigned `_dims` to `ground` as well as `urban` - a refusal path feature 113's transformer did
not have, added here because a seven-way partition has more surface for a copy-paste duplicate:

    REFUSING: a member is assigned to more than one module: ['_dims']
    exit=1

Neither refusing run created `settlement/structures/` - the refusal happens before `PKG.mkdir()`,
which matters, because a half-written package beside a live module is worse than no package.

### T017 - the COLLISION assertion proven RED (post-split)

Copied `_dims` into `GroundMixin`:

    E   AssertionError: GroundMixin and UrbanBuildingMixin both define ['_dims'] - MRO would orphan one
    1 failed, 51 deselected

Reverted.

### T018 - the ATTRIBUTE half of assertion 1 proven RED (post-split)

This is the half feature 112's guard could not see - its census counted callables only, so its
`_PADDY_*_KINDS` matrices needed a test of their own. Deleted `URBAN` from `UrbanBuildingMixin`:

    E       AssertionError: missing=['URBAN']
    1 failed, 51 deselected

Reverted; all three guard tests green again.

### T009-T015 - what the move actually produced

| file | lines | members |
|---|---|---|
| `fixtures.py` | 407 | 6 |
| `packing.py` | 292 | 3 |
| `compounds.py` | 277 | 4 |
| `servants.py` | 218 | 7 |
| `urban.py` | 177 | 6 |
| `captions.py` | 101 | 5 |
| `ground.py` | 92 | 2 |
| `__init__.py` | 40 | 0 (composition only) |

1,459 -> largest file **407** (SC-001's bar was 450). The ruff prune removed **140** unused imports
from the seven copied headers.

`settlement/core.py`: `git diff --stat` empty (FR-002). No member's assignment moved from
data-model.md's tables.

### T014 - the move was PURE, checked rather than assumed

**`comment lines lost: 0`** - every comment line in the pre-split class body survives somewhere in
the package. This is the check that matters most in this repo: a comment above a method is usually
researched grounding (the manor's glyph-not-a-scale-drawing doctrine, `servant_ranges`' nagaya
sourcing, `drum_tower`'s re-verified Pingyao footprint, `kosatsuba`'s marker-floor reasoning), and a
"pure move" that drops a why-comment is not pure.

### T020 - the whole affected test files

`pytest tests/settlement/ tests/tools/ -q -n auto --no-cov`: **705 passed** in 25.7s, no `-k`
filter. `tests/tools/` was in the run because T016 changed `test_why_placed.py`, which a
`tests/settlement/`-only run would have missed.

### T021 - the byte-identity sweep, all three pass conditions

    regen exit code: 0
    REGENERATED: 28  (baseline: 28)
    artifacts: 889  (baseline: 889)
    BYTE-IDENTICAL

Run with nothing else heavy in flight, per the feature-113 false-green lesson. `git status
--porcelain -- pool` prints nothing (T022).

### T023 / T025 - the gate, and the coverage that did not move

`make done`: **gate green**. Combined `settlement/` coverage **95%** (8,452 statements, 450 missed)
against the `SETTLEMENT_COV_FLOOR` of 94 - the same 95 feature 113 measured, so a pure move moved
nothing, exactly as research R7 predicted. The floor was NOT raised: 95 is the pre-existing figure,
not something this feature earned.

The per-module split the package now makes legible, which the single opaque number could not:

| module | stmts | miss | cov |
|---|---|---|---|
| `urban.py` | 89 | 1 | 99% |
| `compounds.py` | 127 | 4 | 97% |
| `captions.py` | - | - | (fully covered) |
| `servants.py` | 114 | 14 | 88% |
| `fixtures.py` | 199 | 22 | 89% |
| `packing.py` | 152 | 48 | 68% |
| `ground.py` | 49 | 29 | 41% |

`packing.py` and `ground.py` are the town/city wings the legacy freeze left unexercised - `rowpack`
is city row housing and `pasture` is a hand-authored-map feature. They re-cover as those tiers
convert to scripted generation, and now a reader can see WHICH wings rather than being told
"mostly in structures.py".

### T024 - GEN_TIME_BUDGETS

Passed unmodified inside the green gate. A pure move adds no call-site indirection - the members
land on the same composed class and resolve through the same MRO - so no per-gen CPU budget moved.
