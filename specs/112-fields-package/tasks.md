# Tasks: settlement/fields.py -> settlement/fields/ Package Split

**Input**: Design documents from `specs/112-fields-package/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/mixin-surface.md, quickstart.md

**Tests**: test tasks ARE included - the spec requires a red-green guard test (FR-003) and the
byte-identity harness is the feature's oracle.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1 (pure move, P1), US2 (decomposition, P2), US3 (index, P3)
- All paths relative to the session clone root unless absolute

**Working directory for every command**: `.claude/skills/diagram/`

---

## Phase 1: Setup

**Purpose**: establish the oracle before anything moves. Nothing in Phase 3+ is safe without it.

- [ ] T001 Export `SPECIFY_FEATURE=112-fields-package` and confirm the clone is synced with main (`git log --oneline -1`); re-measure `.claude/skills/diagram/settlement/fields.py` and confirm 1,511 lines / 24 methods, since a peer session last edited it
- [ ] T002 Capture the byte-identity baseline per quickstart.md step 1: copy `.claude/skills/diagram/` to a scratch tree, run `python3 regen.py --no-cache --frozen-ok pool/*/*.gen.py wip/*.gen.py` there, and write `sha256sum` of every `pool/**` and `wip/**` `.json`/`.svg`/`.png` to `/tmp/112-baseline.sha`
- [ ] T003 Record the baseline sweep's own verdict (map count, any gen that failed in the pre-split tree) in this file under Notes, so a Stage 1 failure can be distinguished from a pre-existing one

**Checkpoint**: an oracle exists that can fail.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: the guard test and the transformer. Blocks all user stories.

**CRITICAL**: T005 must be observed failing before T006 lands.

- [ ] T004 Write the composed-surface guard test in `.claude/skills/diagram/test_settlement/test_fields.py` per contracts/mixin-surface.md: assert the composed `FieldsMixin` exposes exactly the 24-name frozenset, assert no two sub-mixins define the same name, assert all 24 resolve on `Settlement` itself
- [ ] T005 Prove the guard RED both ways and record the failure text in this file's Notes: (a) delete one method from a sub-mixin, observe assertion 1 name it, revert; (b) copy one method into a second sub-mixin, observe assertion 2 name the collision, revert
- [ ] T006 [P] Adapt `specs/025-human-scale-splits/split_settlement.py` into `specs/112-fields-package/split_fields.py` for a class-to-subpackage split: slice between METHOD boundaries in the class body rather than between top-level statements, emit one sub-mixin class per module, and generate each module's import header from the names its own methods actually use (research R7)

**Checkpoint**: guard proven to fire; transformer ready.

---

## Phase 3: User Story 1 - Behavior-preserving package split (Priority: P1) 🎯 MVP

**Goal**: `settlement.fields` becomes a four-module package; `core.py` untouched; every artifact byte-identical.

**Independent test**: the quickstart sweep diff is empty, `git status` under `pool/` is clean, and `make done` is green with no consumer file modified.

- [ ] T007 [US1] Run the transformer to create `.claude/skills/diagram/settlement/fields/` with `paddy.py`, `comb.py`, `landuse.py`, `features.py`, assigning methods exactly per data-model.md's four tables (9 / 4 / 3 / 8 methods)
- [ ] T008 [US1] Write `.claude/skills/diagram/settlement/fields/__init__.py`: four sub-mixin imports plus `class FieldsMixin(PaddyMixin, CombMixin, LandUseMixin, FieldFeaturesMixin)`, with a docstring saying it exists to preserve `core.py`'s single import (research R6)
- [ ] T009 [US1] In each of the four modules, add the `TYPE_CHECKING` block with `from ..core import Settlement` (two-dot path) and keep every method's `self: "Settlement"` annotation - data-model.md invariant 4
- [ ] T010 [US1] Delete `.claude/skills/diagram/settlement/fields.py` (invariant: a stale module beside a package of the same name is a shadowing hazard)
- [ ] T011 [US1] Verify `.claude/skills/diagram/settlement/core.py` is byte-unchanged (`git diff --stat -- settlement/core.py` empty) - FR-002, SC-002
- [ ] T012 [US1] Run the cheap linter prefix: `python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy`; fix unused-import fallout in the generated headers only
- [ ] T013 [US1] Run the WHOLE affected test files, not a `-k` subset: `python3 -m pytest test_settlement/ test_checks/ -q -n auto --no-cov`
- [ ] T014 [US1] Run the byte-identity sweep per quickstart.md step 2 and require an EMPTY diff against `/tmp/112-baseline.sha`
- [ ] T015 [US1] Confirm `git status --porcelain -- .claude/skills/diagram/pool` prints nothing (FR-005)
- [ ] T016 [US1] Run `make done` backgrounded, once; read the log tail before believing green (no `; echo EXIT=$?` wrapper)
- [ ] T017 [US1] Commit Stage 1 as its own commit, so a later bisect can separate the move from the decomposition

**Checkpoint**: US1 is independently shippable. If Stage 2 were abandoned here, the clause-13 debt is already paid.

---

## Phase 4: User Story 2 - Oversized methods decomposed (Priority: P2)

**Goal**: the three oversized methods read as short sequences of named steps.

**Independent test**: no function over ~150 lines without an inline justification; the sweep diff is empty after EACH decomposition.

**CRITICAL**: one method at a time, sweeping between. Research R5 - doing three at once means bisecting to find which extraction moved a draw.

- [ ] T018 [US2] Decompose `draw_comb_field` (321 lines) in `.claude/skills/diagram/settlement/fields/comb.py` into named helpers, preserving code order, RNG draw order and float-operation order exactly
- [ ] T019 [US2] Sweep after T018: empty diff against the baseline, `pool/` clean
- [ ] T020 [US2] Decompose `apply_land_use` (266 lines) in `.claude/skills/diagram/settlement/fields/landuse.py` into named helpers, same constraints
- [ ] T021 [US2] Sweep after T020: empty diff against the baseline, `pool/` clean. This is the decomposition whose ONLY manifest-level oracle is the frozen legacy maps (research R4) - confirm Kuwabata, Tango, Minami and Nagahara are in the swept set
- [ ] T022 [US2] Decompose `water_field` (194 lines) in `.claude/skills/diagram/settlement/fields/paddy.py` into named helpers, same constraints
- [ ] T023 [US2] Sweep after T022: empty diff against the baseline, `pool/` clean
- [ ] T024 [US2] Measure function sizes across the package with the quickstart step 6 script; anything still over ~150 lines gets an inline one-line justification at its `def`, or gets split further
- [ ] T025 [US2] Check combined `settlement/` coverage (`python3 -m coverage report --include='*/settlement/*'`); if the achievable figure rose, raise `SETTLEMENT_COV_FLOOR` in `.claude/skills/diagram/Makefile` to match and record the new measurement in the comment above it. Never lower it
- [ ] T026 [US2] Confirm `GEN_TIME_BUDGETS` in `test_villages.py` still passes unmodified - extraction must not have moved a per-gen CPU budget

**Checkpoint**: both halves of the GM's ask are delivered.

---

## Phase 5: User Story 3 - Token-scale package index (Priority: P3)

**Goal**: a session can find the one file it needs without opening a source file.

**Independent test**: a reader given any named concern resolves it from the two index files alone.

- [ ] T027 [P] [US3] Write `.claude/skills/diagram/settlement/fields/CLAUDE.md` in the `check_village/` + `hamletgen/` style: what the package is, a "Look here when" row per submodule, the composition mechanism, and the two documented placement exceptions (`_paddy_surface` in `paddy.py`, `_rounded_pond` in `features.py`) so nobody "fixes" them back
- [ ] T028 [US3] Replace the single `fields.py` row in `.claude/skills/diagram/settlement/CLAUDE.md`'s "Look here when" table with rows resolving to the four new modules, and note the package has its own sub-index
- [ ] T029 [P] [US3] Verify every file in `settlement/fields/` is under ~1,000 raw lines (`wc -l settlement/fields/*.py`)

---

## Phase 6: Polish and Cross-Cutting

- [ ] T030 [P] Grep the skill for prose naming the FILE `settlement/fields.py` and update to the package; leave importable-path references and prior `specs/NNN` artifacts verbatim as historical record (FR-014)
- [ ] T031 Record in `specs/112-fields-package/research.md` anything the implementation learned that the plan got wrong - especially any method whose assignment moved from data-model.md's table, with the reason
- [ ] T032 Set this spec's Status to Implemented with the date, and note the final per-file line counts
- [ ] T033 Final `make done` green, then the stop-work ritual: commit in the clone and run `scripts/sync-with-main.sh done`

---

## Dependencies

- **Phase 1 (T001-T003)** blocks everything - no oracle, no safe change.
- **Phase 2 (T004-T006)** blocks Phase 3. T005 (red proof) blocks T007.
- **US1 (Phase 3)** blocks **US2 (Phase 4)** - research R5, the stages have different failure modes and must be diagnosable separately.
- **US3 (Phase 5)** depends only on US1; it may be pulled forward to run beside US2 if convenient, since the index rows cite no line counts.
- **Phase 6** depends on US1, US2 and US3.

## Parallel Opportunities

- T006 (transformer) runs parallel with T004/T005 (guard test) - different files.
- T027 and T029 are parallel within US3.
- T030 is parallel with T031/T032.
- Inside US2, the three decompositions are deliberately NOT parallel: the sweep between them is the diagnostic.

## Implementation Strategy

**MVP = Phase 1 + Phase 2 + US1.** That alone pays the clause-13 debt, is byte-identity proven, and
is committed separately (T017) so it stands on its own. US2 is the engineering half and US3 is the
navigation half; both are additive on a green US1.

**Stop-and-ask trigger**: if the Stage 1 sweep is not byte-identical, do NOT adjust the baseline or
accept the diff - it means the composition or an import binding changed behavior, which is exactly
what the harness exists to catch. Diagnose from the first differing map.

## Notes

*(T003 and T005 record their observations here during implementation.)*
