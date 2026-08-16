# Tasks: settlement/city.py -> settlement/city/ Package Split

**Input**: Design documents from `specs/113-city-package/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/mixin-surface.md, quickstart.md, split_city.py

**Tests**: test tasks ARE included - the spec requires a red-green guard test (FR-003) and the
byte-identity harness is the feature's oracle.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1 (pure move, P1), US2 (decomposition, P2), US3 (index, P3)
- All paths relative to the session clone root unless absolute

**Working directory for every command**: `.claude/skills/diagram/`

**Scratch root** (used by the sweeps): `/tmp/claude-1000/-gm-assistant/adc2474d-f7cd-431a-a978-3e8b51b66abb/scratchpad`

---

## Phase 1: Setup

**Purpose**: establish the oracle, and prove the oracle can actually see the thing it will measure.
Nothing in Phase 3+ is safe without both.

- [x] T001 Confirm the clone is synced to the post-reorg tip and re-measure `.claude/skills/diagram/settlement/city.py`: expect 1,582 lines and 27 `CityMixin` members, all `FunctionDef`. Re-measure rather than trust plan.md - a peer session moved the tree between planning and implementation
- [x] T002 Run quickstart.md step 0 BEFORE the split and record the output in this file's Notes: `gencache.engine_files()` must list `settlement/city.py` and must report `tests contributing: 0`. This is the pre-image of the post-split check in T017
- [x] T003 Capture the byte-identity baseline per quickstart.md step 1: copy `.claude/skills/diagram/` to `$SCRATCH/113-baseline/diagram`, run `python3 -m pipeline.regen --no-cache --frozen-ok pool/*/*.gen.py` there, and write `sha256sum` of every `pool/**` `.json`/`.svg`/`.png` to `/tmp/113-baseline.sha`
- [x] T004 Record the baseline sweep's own verdict in this file's Notes (generator count, artifact count, any gen that failed in the PRE-split tree), so a Stage 1 failure can be told apart from a pre-existing one

**Checkpoint**: an oracle exists, it can fail, and it is known to be looking at the right files.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: the guard test and the transformer. Blocks all user stories.

**CRITICAL**: T006 must be observed failing before T009 lands.

- [x] T005 Write the composed-surface guard test in `.claude/skills/diagram/tests/settlement/test_city.py` per contracts/mixin-surface.md: assert the composed `CityMixin` exposes exactly the 27-name frozenset, assert no two sub-mixins define the same name, assert all 27 resolve on `Settlement` itself. Import helpers package-qualified (`from tests.settlement._builders import ...`). The test is written against the PRE-split tree, where `settlement.city` is still a module - assertions 1 and 3 are meaningful there and pass; assertion 2 is vacuous until sub-mixins exist
- [x] T006 Prove assertion 1 RED before the split and record the failure text in this file's Notes: delete one method from `CityMixin`, observe assertion 1 name it, revert
- [x] T007 Note in this file's Notes that assertion 2's red proof CANNOT run pre-split - a duplicate name needs two sub-mixins to live in - so it is deferred to T016, before Stage 1 is committed. Feature 112's task list implied both proofs ran before its transformer; that ordering is not actually possible, and recording the correction here stops the next split from copying it
- [x] T008 [P] Verify `specs/113-city-package/split_city.py` runs its refusal paths: temporarily drop a name from a `MODULES` tuple and confirm it exits non-zero printing `missing=`, then restore. A transformer that silently drops a method produces a package that imports fine and draws nothing

**Checkpoint**: guard proven to fire on the assertion that can fire yet; transformer proven to refuse.

---

## Phase 3: User Story 1 - Behavior-preserving package split (Priority: P1) 🎯 MVP

**Goal**: `settlement.city` becomes a six-module package; `core.py` untouched; every artifact byte-identical.

**Independent test**: the quickstart sweep diff is empty, `git status` under `pool/` is clean, and `make done` is green with no consumer file modified.

- [x] T009 [US1] Run the transformer from `.claude/skills/diagram/` to create `settlement/city/` with `walls.py`, `moat.py`, `canals.py`, `waterfront.py`, `bridges.py`, `civic.py`, assigning methods exactly per data-model.md's six tables (8 / 5 / 4 / 5 / 4 / 1 members)
- [x] T010 [US1] Confirm the transformer wrote `settlement/city/__init__.py` composing `class CityMixin(WallsMixin, MoatMixin, CanalsMixin, WaterfrontMixin, BridgesMixin, CityCivicMixin)`, with the docstring explaining it exists to preserve `core.py`'s single import
- [x] T011 [US1] Confirm each of the six modules carries `if TYPE_CHECKING: from ..core import Settlement` (two-dot path) and that every method kept its `self: "Settlement"` annotation - data-model.md invariant 3
- [x] T012 [US1] Delete `.claude/skills/diagram/settlement/city.py` (invariant: a stale module beside a package of the same name is a shadowing hazard)
- [x] T013 [US1] Verify `.claude/skills/diagram/settlement/core.py` is byte-unchanged (`git diff --stat -- settlement/core.py` empty) - FR-002, SC-004
- [x] T014 [US1] Prune the copied import headers and format: `python3 -m ruff check --select F401 --fix settlement/city/ && python3 -m ruff format settlement/city/`, then the full cheap prefix `python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy`
- [x] T015 [US1] Run the WHOLE affected test files, not a `-k` subset: `python3 -m pytest tests/settlement/ tests/check_village/ -q -n auto --no-cov`
- [x] T016 [US1] Now that sub-mixins exist, prove guard assertion 2 RED and record the failure text in Notes: copy one method into a second sub-mixin, observe assertion 2 name the collision, revert. FR-003 is not satisfied until this is done
- [x] T017 [US1] Re-run quickstart.md step 0 POST-split: every `settlement/city/*.py` must appear in `gencache.engine_files()` and `tests` must still contribute 0. A nested package falling out of the engine fingerprint would make every later sweep a false green (research R5)
- [x] T018 [US1] Run the byte-identity sweep per quickstart.md step 2 and require ALL THREE of: regen exit code 0, a REGENERATED count equal to the baseline's 28, and an EMPTY diff against `/tmp/113-baseline.sha`. Run it with nothing else heavy in flight - see the Notes entry on the first attempt
- [x] T019 [US1] Confirm `git status --porcelain -- .claude/skills/diagram/pool` prints nothing (FR-005)
- [x] T020 [US1] Run `make done` backgrounded, once; read the log tail before believing green (no `; echo EXIT=$?` wrapper, which makes a failed gate report exit 0)
- [x] T021 [US1] Commit Stage 1 as its own commit, so a later bisect can separate the move from the decomposition (FR-014), then run `scripts/sync-with-main.sh done` - Stage 1 is independently shippable and landing it early keeps any future peer collision mechanical

**Checkpoint**: US1 is independently shippable. If Stage 2 were abandoned here, the clause-13 debt is already paid.

---

## Phase 4: User Story 2 - Oversized methods decomposed (Priority: P2)

**Goal**: every method over the ~150-line bar reads as a short sequence of named steps. MEASURE before extracting - the spec's list of five was a pre-measurement guess and only two survive it (research R10).

**Independent test**: no function over ~150 lines without an inline justification; the sweep diff is empty after EACH decomposition.

**CRITICAL**: one method at a time, sweeping between - research R4. Doing both at once means bisecting to find which extraction moved a draw. Smaller one first, so the technique is proven before it reaches the 339-line one.

- [x] T022 [US2] MEASURE first: function sizes across the package, in statements as well as raw lines (constitution clause 12 measures statements, "never raw lines"). Result in research R10 - only `city_wall` (339 raw / 160 stmts) and `channel_footbridges` (195 raw / 91 stmts) exceed FR-009's ~150 bar
- [x] T023 [US2] SKIPPED WITH REASON, not silently: `log_boom` (97 raw / 41 stmts), `moat` (111 / 57) and `farmland_ring` (121 / 48) are already under the bar, and 31-35 of their raw lines are mandatory researched docstring that splitting would duplicate or orphan. Full reasoning and the reversal cost in research R10
- [x] T024 [US2] Decompose `channel_footbridges` (195 raw / 91 stmts) in `.claude/skills/diagram/settlement/city/bridges.py` into named helpers, preserving code order, RNG draw order and float-operation order exactly. 14 external consumers - the most-used method in the package
- [x] T025 [US2] Sweep after T024: exit 0, 28 generators, empty diff, `pool/` clean
- [x] T030 [US2] Decompose `city_wall` (339 raw / 160 stmts, the largest function in the skill) in `.claude/skills/diagram/settlement/city/walls.py`, same constraints. It already has six private callees, so the extraction has an established vocabulary to extend rather than invent
- [x] T031 [US2] Sweep after T030: exit 0, 28 generators, empty diff, `pool/` clean. Confirm the provincial-city maps (`tango`, `minami`, `nagahara`) and the walled towns are in the swept set - they are the only artifacts exercising the wall wing
- [x] T032 [US2] Measure function sizes across the package with the quickstart step 6 script; anything still over ~150 lines gets an inline one-line justification at its `def`, or gets split further
- [x] T033 [US2] Check combined `settlement/` coverage (`python3 -m coverage report --include='*/settlement/*'`); if the achievable figure rose BECAUSE OF THIS SPLIT, raise `SETTLEMENT_COV_FLOOR` in `.claude/skills/diagram/Makefile` to match and record the new measurement in the comment above it. Never lower it. A movement after Stage 1 alone is a signal to investigate, not a number to bank (research R7)
- [x] T034 [US2] Confirm `GEN_TIME_BUDGETS` in `tests/test_villages.py` still passes unmodified - extraction must not have moved a per-gen CPU budget

**Checkpoint**: both halves of the GM's ask are delivered.

---

## Phase 5: User Story 3 - Token-scale package index (Priority: P3)

**Goal**: a session can find the one file it needs without opening a source file.

**Independent test**: a reader given any named city concern resolves it from the two index files alone.

- [x] T035 [P] [US3] Write `.claude/skills/diagram/settlement/city/CLAUDE.md` in the `check_village/` + `hamletgen/` + `settlement/fields/` style: what the package is, a "Look here when" row per submodule, the composition mechanism, the one cross-seam call (`farmland_ring` -> `sluice_gate`), and the two placement decisions a reader will otherwise want to "fix" - `_ring_upslope` living with its caller rather than with `ring_road`, and `civic.py` existing at all
- [x] T036 [US3] Replace the single `city.py` row in `.claude/skills/diagram/settlement/CLAUDE.md`'s "Look here when" table with rows resolving to the six new modules, and note the package has its own sub-index
- [x] T037 [P] [US3] Verify every file in `settlement/city/` is under ~1,000 raw lines (`wc -l settlement/city/*.py`) - SC-001

---

## Phase 6: Polish and Cross-Cutting

- [x] T038 [P] Grep the skill for prose naming the FILE `settlement/city.py` and update to the package; leave importable-path references and prior `specs/NNN` artifacts verbatim as historical record (FR-013)
- [x] T039 Record in `specs/113-city-package/research.md` anything the implementation learned that the plan got wrong - especially any method whose assignment moved from data-model.md's table, with the reason
- [x] T040 Add the `civic.py` -> `castle_civic.py` relocation to `.claude/skills/diagram/future-work.md` as a named follow-up with its reasoning, so it does not live only in this spec
- [x] T041 Set this spec's Status to Implemented with the date, and note the final per-file line counts
- [x] T042 Final `make done` green, then the stop-work ritual: commit in the clone and run `scripts/sync-with-main.sh done`

---

## Dependencies

- **Phase 1 (T001-T004)** blocks everything - no oracle, no safe change.
- **Phase 2 (T005-T008)** blocks Phase 3. T006 (red proof) blocks T009.
- **US1 (Phase 3)** blocks **US2 (Phase 4)** - research R4: the stages have different failure modes and must be diagnosable separately.
- Within US2, each decomposition blocks its own sweep, and each sweep blocks the next decomposition. This is deliberately serial.
- **US3 (Phase 5)** depends only on US1; it may be pulled forward to run beside US2, since the index rows cite no line counts.
- **Phase 6** depends on US1, US2 and US3.

## Parallel Opportunities

Genuinely few, and that is by design - the oracle serializes Stage 2. The real ones:

- T008 (transformer refusal check) runs beside T005-T007.
- T035 and T037 run together, and either can run during Phase 4.
- T038 can run any time after T012.

Do NOT parallelize the Stage 2 decompositions. The whole point of the seven-sweep structure is that a red sweep names its own cause.

## Notes

### T002 / T017 - the oracle can see what it measures

Pre-split: 78 engine files, city files seen `['settlement/city.py']`, tests contributing 0.
Post-split: **84** engine files, city files seen `settlement/city/__init__.py`, `bridges.py`,
`canals.py`, `civic.py`, `moat.py`, `walls.py`, `waterfront.py` - all seven - and tests still
contributing 0. The nested package is walked exactly as `settlement/fields/` is, so no sweep is a
false green from a stale cache.

### T004 - the baseline sweep's own verdict

28 generators, **885 artifacts** (`.json` + `.svg` + `.png`) under `pool/`, hashed into
`/tmp/113-baseline.sha`. No generator failed and no error or traceback appeared in the pre-split
run, so any Stage 1 failure is attributable to Stage 1.

### T006 - guard assertion 1 proven RED (pre-split)

Deleted `_tower` from `CityMixin` (lines 97-120 of the pre-split `city.py`):

    E       AssertionError: missing=['_tower']
    1 failed, 43 deselected

Reverted; `city.py` back to 1,582 lines.

### T007 - why assertion 2's red proof is deferred to T016

A duplicate-name collision needs two sub-mixins to live in, so it cannot be staged before the
package exists. Feature 112's task list put both red proofs before its transformer ran, which is
not actually possible; recorded here so the next split does not copy the ordering.

**The guard was written to work at BOTH stages**, which is what makes the deferral safe rather than
just necessary: `_city_submixins()` derives the sub-mixin list from `CityMixin.__mro__` instead of
importing `settlement.city.walls` and friends directly. Pre-split the list is empty and assertion 2
is vacuous; post-split it is the six. 112's version imported the submodules by name and therefore
could not be written until after its own split.

### T016 - guard assertion 2 proven RED (post-split)

Injected a duplicate `_wall_perimeter` into `MoatMixin`:

    E       AssertionError: WallsMixin and MoatMixin both define ['_wall_perimeter'] - MRO would orphan one
    1 failed, 43 deselected

Reverted; `moat.py` back to 258 lines, all 44 tests in the file green.

### T008 - the transformer proven to REFUSE

Dropped `_tower` from the `walls` tuple in `MODULES` and re-ran:

    REFUSING: partition does not cover the class. missing=['_tower'] extra=[]
    exit=1

Restored.

### T009-T014 - what the move actually produced

| file | lines |
|---|---|
| `walls.py` | 512 |
| `bridges.py` | 359 |
| `waterfront.py` | 274 |
| `moat.py` | 258 |
| `canals.py` | 227 |
| `civic.py` | 37 |
| `__init__.py` | 25 |

Largest file 512 lines against a 1,582-line predecessor - SC-001 met with room to spare.
`ruff check --select F401 --fix` pruned 114 unused imports from the copied headers.
`git diff --stat -- settlement/core.py` is empty (FR-002 / SC-004).

**One real defect found, in the INHERITED transformer** (recorded in research R8): feature 112's
`split_fields.py` rewrote one-dot relative imports only in the module HEADER, because none of its
methods had an in-body import. `city.py` has one - `_wall_point_at_arc` does a lazy
`from .core import Settlement` inside its body, a runtime class-attribute read that would cycle at
module level. Moved verbatim, it kept the one-dot path and pointed at a nonexistent
`settlement.city.core`. `mypy --strict` caught it (`walls.py:141: error: Cannot find implementation
or library stub for module named "settlement.city.core"`); in a module mypy did not check it would
have been an `ImportError` at draw time, and the byte-identity sweep would have reported it as a
failed generator rather than as a wrong import. Fixed in the file AND in `split_city.py`, which now
applies the same rewrite to member bodies, so the next split inherits the fix.

### T011 - the staticmethod count, which looks wrong and is not

`self: Settlement` appears 4/4/1/5/5/5 across bridges/canals/civic/moat/walls/waterfront = 24, not
27. The three unannotated members are `walls.py`'s `_wall_perimeter`, `_wall_point_at_arc` and
`_wall_arc_of`, which are `@staticmethod` and take no `self`. Their decorator lines sit ABOVE the
`def` and arrived intact - which is the transformer's slicing rule (previous member's end, not this
member's `lineno`) doing exactly the job it exists for.

### T018 - the sweep, on the third attempt

    regen rc=0   REGENERATED=28 (baseline 28)   artifacts=885 (baseline 885)
    PASS: exit 0 + 28 generators + empty diff = BYTE-IDENTICAL

Attempt 1 was the false green of research R9 (OOM-killed beside an `-n auto` pytest; 0 generators
ran). Attempt 2 failed on the wrong fix for it - deleting the scratch tree's artifacts destroys
hand-authored Mode A `.svg` SOURCE, which `resvg` then failed to render. Attempt 3 ran alone with
no deletion and the three-condition check. The pure move is verified.

### T020 - the gate

`make done`: ruff `All checks passed!`, `mypy` clean, **3,179 passed**, combined `settlement/`
coverage **95%** against its 94 floor, `gate green`.

### T038 - no stale prose to fix

Grepped the skill for markdown naming the FILE `settlement/city.py`. Outside `specs/`, the only hit
is the new `settlement/city/CLAUDE.md`, which names it correctly as the package's 1,582-line
predecessor. `specs/025-human-scale-splits/research.md` names it too and is left verbatim as
historical record per FR-013. Nothing to change.

### T015 - the affected suites

`pytest tests/settlement/ tests/check_village/ -q -n auto --no-cov`: **1,887 passed**.

### Stage 2 result (T024-T032)

| method | before | after |
|---|---|---|
| `city_wall` | 339 raw / 160 stmts | **69 / 23** |
| `channel_footbridges` | 195 / 91 | **120 / 44** |

Extracted, each carrying its own researched why: `_draw_gate` (17 raw) over `_gate_piers` (15),
`_gate_flanking_buildings` (51), `_gate_tower` (29), `_gate_caption` (69); `_seat_mural_towers`
(107); `_berm_nudge` (12); `_widen_for_confluence` (29), `_deck_clears_its_water` (30); and the
module-level `_at_arc` / `_deck_quad` / `_quads_overlap`.

**No function in the package exceeds 150 raw lines** (T032), and no file exceeds 550 (T037):
walls 549, bridges 382, waterfront 274, moat 258, canals 227, civic 37, `__init__` 25.

Both sweeps passed on the first attempt - rc=0, 28 generators, 885 artifacts, empty diff. Neither
method contains any RNG, so the only hazard was float-operation order, which a textual move
preserves. `GEN_TIME_BUDGETS` passes unmodified (T034).

### Final per-file line counts (T041)

1,582 lines in one file -> 1,752 across seven, largest 549. The +170 is six module headers and the
docstrings the extracted methods now carry; the number that matters is the 1,582 -> 549 a session
loads to work on the wall.

### Found but NOT fixed here (reported instead)

**17 test files carry a stale index pointer.** Every file under `tests/settlement/` still has the
docstring `"""Split from test_settlement.py by feature 025 - see test_settlement/CLAUDE.md for the
index."""`, but the peer session's reorg moved that directory to `tests/settlement/`, so the path
no longer resolves. Docs-only and harmless to behavior, but it points a future session at a
directory that does not exist.

Deliberately left alone by feature 113 for two reasons: it is the reorg's fallout rather than this
feature's, and the session that made the move may be fixing it right now - a 17-file collision is
worse than a stale docstring. Reported to that session directly.

**The `.coverage.*` gitignore was inert, and IS fixed here** (it was blocking this feature's own
commits). Both `.gitignore` and `.claude/skills/diagram/.gitignore` had the pattern written with a
trailing comment - `.coverage.*   # pytest-xdist writes one per worker...` - and `#` only opens a
comment at the START of a gitignore line, so the whole string was one literal pattern matching
nothing. The bare `.coverage` above it worked, which is what made it look half-applied. Comment
moved to its own line; verified with `git check-ignore -v` against a real xdist file rather than by
re-reading the pattern.

### T033 - the coverage decision, measured

`settlement/` combined: **95% (8,418 statements, 449 missed)** on the final tip, against 8,400/448
before the decomposition. Unchanged - which is what a behavior-preserving refactor should do, and a
small independent confirmation that it was one.

**`SETTLEMENT_COV_FLOOR` stays at 94.** The 95 predates this feature and the concurrent reorg both;
neither a pure move nor a decomposition can create coverage. Banking it here would credit this
feature with someone else's point and make a future failure hard to attribute - the same reasoning
the peer session used when it declined to raise the floor inside its own refactor. A tier
conversion that actually lights up the city wing should be what raises it.

What the split DID buy here: the 95 is no longer one opaque number. Per file it reads walls 94%,
bridges 97%, canals 99%, moat / waterfront / civic 100% - so the uncovered city wing is localized
to two files instead of hiding inside a 1,582-line one.

### T042 - final gate and the stop-work ritual

`make done` green: 3,179 passed, ruff and mypy clean, `settlement/` 95% against its 94 floor.
Committed and pushed to main (`67040c3`), render-sync run.
