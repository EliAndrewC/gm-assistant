# Tasks: settlement/shrines_wells.py -> settlement/shrines_wells/ Package Split

**Input**: Design documents from `specs/116-shrines-wells-package/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/mixin-surface.md,
quickstart.md, split_shrines_wells.py

**Tests**: test tasks ARE included - the spec requires a red-green guard test (FR-003) and the
byte-identity harness is the feature's oracle.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1 (pure move, P1), US2 (guard proven, P2), US3 (index, P3)
- All paths relative to the session clone root unless absolute

**Working directory for every command**: `.claude/skills/diagram/`

**Scratch root**: `/tmp/claude-1000/-gm-assistant/4eb77348-7747-44cf-b815-3d76370aeb37/scratchpad`

---

## Phase 1: Setup

**Purpose**: establish the oracle, and prove the oracle can actually see the thing it will measure.
Nothing in Phase 3+ is safe without both.

- [x] T001 Confirm the clone is synced to main's tip and re-measure `.claude/skills/diagram/settlement/shrines_wells.py`: expect 1,179 raw lines and 38 `ShrinesWellsMixin` members, all `FunctionDef`. Re-measure rather than trust plan.md - a peer session (feature 115, `civic_grounds`) is live in this tree's history and may have moved things between planning and implementation
- [x] T002 Run quickstart.md step 0 BEFORE the split and record the output in this file's Notes: `gencache.engine_files()` must list `settlement/shrines_wells.py` and must report `tests contributing: 0`. This is the pre-image of the post-split check in T020
- [x] T003 Capture the byte-identity baseline per quickstart.md step 1: copy `.claude/skills/diagram/` to `$SCRATCH/116-baseline/diagram`, run `python3 -m pipeline.regen --no-cache --frozen-ok pool/*/*.gen.py` there, and write `sha256sum` of every `pool/**` `.json`/`.svg`/`.png` to `/tmp/116-baseline.sha`
- [x] T004 Record the baseline sweep's own verdict in this file's Notes (generator count, `REGENERATED` count, artifact count, any gen that failed in the PRE-split tree), so a Stage 1 failure can be told apart from a pre-existing one

**Checkpoint**: an oracle exists, it can fail, and it is known to be looking at the right file.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: the guard test and the transformer. Blocks Phase 3. These tasks deliver most of US2; its
remaining red proof cannot run until sub-mixins exist and so appears in Phase 3.

**CRITICAL**: T006 must be observed failing before T010 lands.

- [x] T005 Write the composed-surface guard test in `.claude/skills/diagram/tests/settlement/test_shrines_wells.py` per contracts/mixin-surface.md: assert the composed `ShrinesWellsMixin` exposes AT LEAST the 38-name frozenset (subset, not equality), assert no two sub-mixins define the same name, assert all 38 resolve on `Settlement` itself. The census must read `vars(cls)` rather than filtering on `callable` - this class has no class-level attribute today, but a methods-only census is the half feature 112 needed a whole extra test for, and the `vars()` form costs nothing
- [x] T006 Prove assertion C1 RED before the split and record the failure text in this file's Notes: delete one method from `ShrinesWellsMixin` (e.g. `_well_vr`), observe C1 name it, revert
- [x] T007 Derive the sub-mixin list from `ShrinesWellsMixin.__mro__` rather than by importing `settlement.shrines_wells.wells` and its siblings by name - that is what lets this guard be written and run BEFORE the split exists (pre-split the derived list is empty and C2 is vacuous). Note in this file's Notes that C2's red proof is therefore deferred to T017, and why
- [x] T008 [P] Verify `specs/116-shrines-wells-package/split_shrines_wells.py` runs its refusal paths: temporarily drop a name from a `MODULES` tuple and confirm it exits non-zero printing `missing=`, then assign one name to two modules and confirm the duplicate-assignment refusal fires, then restore. A transformer that silently drops a method produces a package that imports fine and draws nothing

**Checkpoint**: guard proven to fire on the assertion that can fire yet; transformer proven to refuse
both ways.

---

## Phase 3: User Story 1 - Behavior-preserving package split (Priority: P1) 🎯 MVP

**Goal**: `settlement.shrines_wells` becomes a seven-module package; `core.py` untouched; every
artifact byte-identical.

**Independent test**: the quickstart sweep diff is empty, `git status` under `pool/` is clean, and
`make done` is green with `core.py` byte-unchanged.

- [x] T009 [US1] Run the transformer from `.claude/skills/diagram/` to create `settlement/shrines_wells/` with `shrines.py`, `torii.py`, `wellground.py`, `wells.py`, `seats.py`, `byres.py`, `woods.py`, assigning members exactly per data-model.md's seven tables (5 / 7 / 7 / 8 / 2 / 2 / 7 members = 38)
- [x] T010 [US1] Confirm the transformer wrote `settlement/shrines_wells/__init__.py` composing `class ShrinesWellsMixin(ShrineHallsMixin, ToriiAvenueMixin, WellGroundMixin, WellsMixin, OpenSeatMixin, DraftByresMixin, TreeStandsMixin)`, with the docstring explaining it exists to preserve `core.py`'s single import and naming `wellground.py` as the hub
- [x] T011 [US1] Confirm each of the seven modules carries `if TYPE_CHECKING: from ..core import Settlement` (two-dot path) and that every method kept its `self: "Settlement"` annotation - data-model.md invariant 4
- [x] T012 [US1] Verify the DECORATOR survived the slice, per quickstart.md step 6a: `@contextlib.contextmanager` is present on `frozen_terrain` in `settlement/shrines_wells/wellground.py`, and `with s.frozen_terrain():` still works on a live `Settlement`. This is the hazard unique to this split (research R5) - a lost decorator keeps the NAME, passes the guard, passes `mypy --strict`, and fails at every call site
- [x] T013 [US1] Delete `.claude/skills/diagram/settlement/shrines_wells.py` (invariant: a stale module beside a package of the same name is a shadowing hazard)
- [x] T014 [US1] Verify `.claude/skills/diagram/settlement/core.py` is byte-unchanged (`git diff --stat -- settlement/core.py` empty) - FR-002
- [x] T015 [US1] Verify the move was PURE, per quickstart.md step 6b: every comment line in the pre-split class body survives somewhere in the package (`comment lines lost: 0`), AND the two deliberately-dropped section-divider banners are really gone (`banners still present: []`). In this project a comment above a method is usually researched grounding - the 45-minute-grind post-mortem, the canopy density study, the 30 px-vs-`ftpx` reservation table - and a move that drops one is not pure (research R5, R9)
- [x] T016 [US1] Prune the copied import headers and format: `python3 -m ruff check --select F401 --fix settlement/shrines_wells/ && python3 -m ruff format settlement/shrines_wells/`, then the full cheap prefix `python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy`
- [x] T017 [US2] Now that sub-mixins exist, prove guard assertion C2 RED and record the failure text in Notes: copy one method into a second sub-mixin, observe C2 name the collision, revert. FR-003 is not satisfied until this is done
- [x] T018 [US1] Confirm the consumer census still holds after the move (research R6): `grep -rn shrines_wells --include='*.py'` over the skill finds the module named ONLY by `settlement/core.py`'s import line, so no consumer file changes. Unlike feature 114, there is no filename-string assertion to update - verify rather than assume
- [x] T019 [US1] Run the WHOLE affected test file, not a `-k` subset: `python3 -m pytest tests/settlement/ -q -n auto --no-cov`
- [x] T020 [US1] Re-run quickstart.md step 0 POST-split: every `settlement/shrines_wells/*.py` must appear in `gencache.engine_files()` and `tests` must still contribute 0. A nested package falling out of the engine fingerprint would make every later sweep a false green
- [x] T021 [US1] Run the byte-identity sweep per quickstart.md step 2 and require ALL THREE of: regen exit code 0, a `REGENERATED` count equal to the baseline's, and an EMPTY diff against `/tmp/116-baseline.sha`. Run it with nothing else heavy in flight - an OOM-killed render leaves the committed artifacts in place and the diff comes back empty having tested nothing
- [x] T022 [US1] Confirm `git status --porcelain -- .claude/skills/diagram/pool` prints nothing
- [x] T023 [US1] Check combined `settlement/` coverage (`python3 -m coverage report --include='*/settlement/*'`) is at or above `SETTLEMENT_COV_FLOOR` (94) and, critically, that it did not MOVE. A pure move relocates executable lines without adding or removing one, so any movement is a signal to investigate - a member lost, a module not composed - not a number to re-baseline (research R7)
- [x] T024 [US1] Confirm `GEN_TIME_BUDGETS` in `tests/test_villages.py` still passes unmodified. This matters more here than in any predecessor: `_well_ground_clear` and `_in_scrub_cover` are the engine's two hottest predicates (~133k candidate seats on Minami), and the whole `frozen_terrain` design exists because a few microseconds per candidate once turned a 5s gen into a 45-minute grind
- [x] T025 [US1] Run `make done` backgrounded, once; read the log tail before believing green (no `; echo EXIT=$?` wrapper, which makes a failed gate report exit 0)
- [ ] T026 [US1] Commit the move + guard as ONE commit (no decomposition stage exists to separate for a bisect - research R4), then run `scripts/sync-with-main.sh done` from inside the clone

**Checkpoint**: US1 and US2 are complete and shippable on their own. If the feature stopped here, the
clause-13 debt is paid.

---

## Phase 4: User Story 3 - The package is navigable without reading it (Priority: P3)

**Goal**: a session can pick the right file from an index without opening several.

**Independent test**: a reader given "hold the torii avenue short of a wall" names `torii.py` from the
index alone.

- [x] T027 [US3] Write `.claude/skills/diagram/settlement/shrines_wells/CLAUDE.md`: the split's provenance, a "look here when" row per module, the hub statement (`wellground.py`), and the cross-submodule call map from research R10
- [x] T028 [US3] Record in that index the four placements a reader would otherwise re-litigate (FR-008): `seats.py` and `byres.py` holding members that belong at parent level, with each one's intended destination; `shrine_well` filed by its code rather than its name; `_hall_caption_y` filed with its caller. Also carry the monkeypatching note one level deeper (research R8) and the "if a module grows" seams from data-model.md
- [x] T029 [US3] Update the `shrines_wells` row of `.claude/skills/diagram/settlement/CLAUDE.md` to point at the sub-index rather than list contents inline - the same shape the `fields/`, `city/` and `structures/` rows already have. Re-read the row first: feature 115 is editing the same table in a peer session
- [ ] T030 [US3] Docs-only, so skip the gate (root CLAUDE.md, "Docs-only diffs skip the gate"). Commit and run `scripts/sync-with-main.sh done`

---

## Phase 5: Polish & Cross-Cutting

- [x] T031 [P] Confirm SC-001: `wc -l settlement/shrines_wells/*.py` shows every file under 320 raw lines
- [x] T032 [P] Update `specs/116-shrines-wells-package/spec.md`'s Status line with the final per-file line counts and the oracle's verdict, the way features 113 and 114 did - the spec is the record of what actually shipped, not only of what was intended
- [x] T033 Record in this file's Notes the remaining clause-13 debt in `settlement/` (`_geom.py` 1,303, `rolling.py` 1,197, `land.py` 1,187 - and whatever feature 115 leaves of `civic_grounds.py`), so the next session inherits the list rather than rediscovering it

---

## Dependencies

```text
Phase 1 (T001-T004)  ── the oracle
        └─> Phase 2 (T005-T008)  ── guard red, transformer proven to refuse
                └─> Phase 3 (T009-T026)  ── US1 + the rest of US2  🎯 MVP
                        └─> Phase 4 (T027-T030)  ── US3, docs-only
                                └─> Phase 5 (T031-T033)
```

- **T003 blocks T021**: no baseline, no comparison. The single hardest dependency in the feature.
- **T006 blocks T009**: a guard not seen red is not a guard.
- **T009 blocks everything in Phase 3** - it is the move itself.
- **T017 needs T009**: C2 is vacuous until more than one sub-mixin exists.
- **Phase 4 needs Phase 3's final shape** (line counts, the hub, what actually landed where).

## Parallel opportunities

Genuinely few, and saying so is more useful than inventing some: this feature is one mechanical
transformation with a verification chain hanging off it, and most steps are strictly ordered.

- **T008** (transformer refusal paths) runs in parallel with T005-T007 - different files.
- **T031 and T032** are independent of each other.
- **T003's baseline sweep (~3 min) is the one place to overlap**: start it, then write the guard test
  (T005) while it runs. Do NOT run anything heavy beside it - quickstart step 2 explains why an
  OOM-killed render makes the whole oracle a false green.

## Implementation strategy

**MVP = Phases 1-3.** US1 + US2 together pay the entire clause-13 debt and are independently
shippable; the index is polish that depends on the final shape. That ordering is also what makes a
failure cheap: if byte-identity fails at T021, nothing downstream has been written yet.

**One commit for the move, one for the docs.** Not because a bisect needs it - there is no second
behavior change - but because the docs commit skips the gate and mixing it in would obscure that.

---

## Notes

### T002 / T020 - the cache walk sees the right thing, before and after

Pre-split: `shrines_wells files seen: ['settlement/shrines_wells.py']`, `tests contributing: 0`.
Post-split: all eight `settlement/shrines_wells/*.py` listed (`__init__`, `byres`, `seats`,
`shrines`, `torii`, `wellground`, `wells`, `woods`), `tests contributing: 0`. The walk is
depth-agnostic by construction, but a borrowed analogy is not a check.

### T001 - pre-split census, re-measured rather than trusted

1,179 raw lines; `ShrinesWellsMixin` with 38 members, all `FunctionDef` (no class-level `Assign`) -
matching data-model.md exactly, so nothing moved under the plan.

### T004 - baseline verdict

28 `REGENERATED`, 0 `FROZEN` (so `--frozen-ok` really did exercise the 19 legacy maps), 896 artifacts
hashed, `REGEN_EXIT=0`, no gen failed in the PRE-split tree. So there was no pre-existing failure for
a Stage 1 failure to hide behind.

### T006 - guard assertion C1 proven RED pre-split

Deleted `_well_vr` from `ShrinesWellsMixin` (lines 265-273) and ran the guard:

```text
>       assert composed >= _SHRINES_WELLS_SURFACE, f"missing={sorted(_SHRINES_WELLS_SURFACE - composed)}"
E       AssertionError: missing=['_well_vr']
1 failed, 40 deselected
```

### T007 - why C2's red proof is deferred

`_shrines_wells_submixins()` derives the sub-mixin list from `ShrinesWellsMixin.__mro__`, so the
guard file is written ONCE and runs unchanged on both sides of the split. Pre-split the derived list
is empty, so C2 is vacuously true and cannot be proven red until sub-mixins exist - hence T017. The
alternative (importing `settlement.shrines_wells.wells` by name) cannot even be written before the
package exists, which is the ordering trap feature 112 hit and 113 recorded.

### T008 - the transformer refuses, both ways

```text
REFUSING: partition does not cover the class. missing=['_well_vr'] extra=[]      -> exit 1
REFUSING: a member is assigned to more than one module: ['_well_vr']             -> exit 1
```

### T017 - guard assertion C2 proven RED post-split

Appended a second `_well_vr` to `wellground.py`:

```text
E       AssertionError: WellGroundMixin and WellsMixin both define ['_well_vr'] - MRO would orphan one
```

Feature 114's third breakage (delete a class-level ATTRIBUTE) has no subject here - this class
defines none - but C1 keeps the `vars()` form that would catch it.

### T012 - the decorator survived, and is now pinned by a test

`@contextlib.contextmanager` is on line 63 of `wellground.py`, directly above `def frozen_terrain`,
and `with s.frozen_terrain():` works on a live `Settlement`. Pinned by
`test_frozen_terrain_is_still_a_context_manager` rather than left to a one-off check, because the
failure mode is invisible to every other assertion in the guard.

### T015 - the move was pure

`comment lines lost: 0`; `banners still present: []`. Both halves matter: nothing of the researched
grounding was dropped, and the two section-divider banners really were removed rather than assumed
removed.

### T021 - the oracle

`BYTE-IDENTICAL`, `REGEN_EXIT=0`, work `REGENERATED` 28 == baseline 28, 896 artifacts each side. All
three pass conditions met, so this is not the false green quickstart step 2 warns about.

### T018 - consumer census after the move

`grep -rn shrines_wells --include='*.py'` finds the module named by exactly one non-test line,
`settlement/core.py:19`, which the package preserves verbatim. The only other hits are inside the
guard test this feature added. So, unlike feature 114, no consumer file changed at all.

### Final module sizes (SC-001: ceiling 320)

```text
294  wells.py        251  shrines.py     201  torii.py     194  wellground.py
185  woods.py         86  seats.py        72  byres.py      41  __init__.py
```

1,179 -> largest 294. A session on one subsystem now loads 25% of what it used to at worst, and 6% at
best.

### T033 - clause-13 debt still standing in settlement/ (for the next session)

| file | raw lines | note |
|---|---|---|
| `_geom.py` | 1,303 | pure geometry helpers, no `self` - one coherent subsystem, needs its own partition research |
| `rolling.py` | 1,197 | `roll_village` + the whole homestead-bundle solver |
| `land.py` | 1,187 | land surfaces: dikes, commons, marsh, toe bands, hinterland |
| `civic_grounds.py` | 1,162 | **claimed by feature 115** in a peer session |

Each is a single coherent subsystem, unlike this one - so each needs its own partition decision, and
each should be its own feature with its own byte-identity sweep. Bundling them would make a failure
ambiguous about which split caused it.
