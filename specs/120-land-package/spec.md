# Feature Specification: the `land/` package

**Feature Branch**: none - this project does not use feature branches (CLAUDE.md, GM 2026-07-27).
The active feature is carried by `export SPECIFY_FEATURE=120-land-package` plus
`export SPECIFY_FEATURE_DIRECTORY=specs/120-land-package`.

**Created**: 2026-08-17

**Status**: Draft

**Input**: User description: "Please refactor land.py - which is over a thousand lines of code - to
comport to our documented conventions for function and file size."

## Why this exists

`settlement/land.py` is **1,187 raw lines**, and it is the LAST un-split file in the `settlement/`
package. `settlement/civic_grounds/CLAUDE.md` has said so in as many words since feature 115:
*"Only `land.py` is still whole."* Constitution Principle X clause 13 makes a file past roughly
1,000 raw lines prompt a question that MUST actually be asked - should this become a package of
subfiles? - and the cost being managed is token economy: a session that needs `toe_band` today pays
context-window tokens for the perimeter dike, both near-ring tilers and the swept-verge blob as
well.

Seven predecessors have already answered that question the same way for this exact package, so this
feature is the last instance of an established practice rather than a new idea:

| feature | file split | becomes |
|---|---|---|
| 025 | `settlement.py` (16,016 lines) | the `settlement/` package |
| 112 | `fields.py` | `fields/` |
| 113 | `city.py` | `city/` |
| 114 | `structures.py` | `structures/` |
| 115 | `civic_grounds.py` | `civic_grounds/` |
| 116 | `shrines_wells.py` | `shrines_wells/` |
| 117 | `_geom.py` | `_geom/` |
| 118 | `rolling.py` | `rolling/` |
| **120** | **`land.py`** | **`land/`** |

**Clause 12 (functions) is already satisfied and this feature does not touch it.** Measured in
LOGIC UNITS as clause 12 requires - statements and expressions, never raw lines - the largest member
is `near_ring_paddy` at 126 statements, then `perimeter_dike` at 101, `commons` at 71 and
`near_ring_cropland` at 70. Clause 12's "suspect" line is a few hundred and its defect line is
roughly 1,000. The 10-line-function dogma is explicitly REJECTED by the same clause, so no function
body is decomposed here and none should be. **The whole of this feature is clause 13.**

## User Scenarios & Testing *(mandatory)*

The "user" here is a future session working on the Mode B engine, plus the GM reading the maps that
engine produces. Both stories are independently testable and either one alone is worth shipping.

### User Story 1 - a session loads only the land subject it is working on (Priority: P1)

A session is asked to change where the wet toe sits on a diagonal-fall map. Today it must load all
1,187 lines of `land.py` - the polder dike, the dike-top village, the scrub scatter, both near-ring
tilers and the swept-verge blob - to reach the 44-line `toe_band`. After this feature it reads a
short `land/CLAUDE.md` index, sees that wet ground is `wet.py`, and loads 188 lines.

**Why this priority**: this IS the constitutional cost clause 13 exists to manage, and it is the
only reason to do the work at all. Everything else in this spec is a constraint on doing it safely.

**Independent Test**: open `land/CLAUDE.md`, pick any of the four subjects, and confirm the task it
names is contained in the one module named for it - no cross-module reading required to make the
change.

**Acceptance Scenarios**:

1. **Given** a session needs to change the polder dike or the village on its crest, **When** it
   reads `land/CLAUDE.md`, **Then** it is directed to `dikes.py` alone (about 242 lines).
2. **Given** a session needs to change reed marsh, the contour band that places it, or the trim that
   keeps ways out of it, **When** it reads the index, **Then** it is directed to `wet.py` alone
   (about 188 lines).
3. **Given** a session needs to change scrub cover or which frame sides carry it, **When** it reads
   the index, **Then** it is directed to `cover.py` alone (about 362 lines).
4. **Given** a session needs to change near-ring farmland at town or city scale, **When** it reads
   the index, **Then** it is directed to `nearring.py` alone (about 338 lines).
5. **Given** any of the four modules, **When** its raw line count is measured, **Then** it is
   comfortably under the clause 13 line, and so is every other file this feature touches.

---

### User Story 2 - every map comes out exactly as it did before (Priority: P1)

The GM's pool of settlement maps must be untouched by this work. A refactor of the engine that
moves so much as one pixel of one map has failed, whatever else it achieved.

**Why this priority**: equal-first with story 1, and it is what makes story 1 safe to attempt. This
is PURE CODE MOTION - method bodies move verbatim - so byte-identity is not an aspiration but a
CONSTRUCTION PROPERTY, and any drift at all is a refactor bug rather than a judgment call. That in
turn gives this feature an unusually strong oracle: unlike a placement-rule change, it needs no
`settlement-review` pass, because "did it change?" is answerable by hashing rather than by looking.

**Independent Test**: hash every pool artifact before the change and after it, and diff the two
lists.

**Acceptance Scenarios**:

1. **Given** the pool regenerated on unmodified code, **When** it is regenerated again after the
   split, **Then** every `.json`, `.svg` and `.png` under `pool/` hashes identically.
2. **Given** `import settlement`, **When** any existing consumer imports `surface_water_dist` or
   uses `settlement.Settlement`, **Then** it behaves exactly as before with no source change.
3. **Given** the full gate, **When** it is run after the change, **Then** it reports no failure that
   the measured baseline did not already report (constitution Principle XIII).

---

### Edge Cases

- **A member is silently dropped or duplicated by the move.** The transformer must REFUSE rather
  than guess: a partition that does not exactly cover the class body, a member assigned to two
  modules, or an unnamed class-body member each abort it by name. Predecessors 112-118 all carry
  this guard and it has fired in anger.
- **A decorator or a comment bank is lost by slicing on the wrong line.** `ast` reports a function's
  `lineno` at the `def`, not at a decorator above it, and in this project a comment above a method
  is usually researched grounding (the perimeter dike's wei-tian sourcing, the toe band's
  alluvial-fan research, the swept verge's inward-only-bay argument). The slice must run from the
  PREVIOUS member's end, not from this member's `lineno`.
- **The module-level tail is not part of the class body.** `surface_water_dist` sits AFTER
  `class LandMixin`, so a transformer that slices only the class body drops it silently. This is the
  first split in the lineage whose source has a module-level member following the class, and the
  transformer must account for the tail explicitly rather than by luck.
- **A stale `.pyc` from the deleted module shadows the new package.** Feature 118 recorded this:
  clear `__pycache__` after the transform, because the resulting failure looks nothing like its
  cause.
- **The dependency walk does not reach the new submodules**, leaving every map `CACHED` so a green
  sweep proves nothing. The walk has been depth-agnostic since feature 025 and has survived seven
  splits, but "expected" is converted to "checked" once, explicitly.
- **A name used only in an ANNOTATION is not imported by the submodule that needs it.** Python's
  deferred annotations hide this until runtime; `mypy --strict` is what catches it (feature 117
  research R6). `_farmstead_nudges` returning `Iterator` is the live instance here, and it is one of
  the members crossing a FILE boundary rather than staying in the package.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `settlement/land.py` MUST become the package `settlement/land/`, and the old module
  MUST be deleted - never left beside a package of the same name.
- **FR-002**: The package MUST carry a `CLAUDE.md` index with one "look here when" line per
  submodule, following the project's slim-index / load-on-demand doc pattern.
- **FR-003**: The partition MUST be by SUBJECT. `land.py` is a residue bucket left by feature 025's
  positional cut - unlike `rolling/`, it is not a chain - so the axis is what a member is ABOUT:
  - `dikes.py` - the polder perimeter dike and the dike-top village on its crest
  - `wet.py` - reed marsh, the contour band that sites it, the way-trim, and the surface-water
    distance predicate
  - `cover.py` - the dry scrub commons, the hinterland layout that lays it, and the swept verge the
    scatters skip
  - `nearring.py` - near-ring dry cropland and near-ring paddy
- **FR-004**: Every member MUST land in exactly one module, and the transformer MUST prove that by
  refusing on any partition that does not exactly cover the source.
- **FR-005**: Method bodies MUST move VERBATIM. No behavior change, no decomposition, no
  reformatting of a moved body, no "while I am here" fixes.
- **FR-006**: `LandMixin` MUST survive as the composed surface, so `settlement/core.py`'s single
  import AND its position in the `class Settlement(...)` base list are unchanged. The split must be
  invisible above that line.
- **FR-007**: `surface_water_dist` MUST stay importable as `settlement.surface_water_dist`. Its
  three consumers (`hamletgen/homesteads.py`, `check_village/segments_04_homesteads.py`,
  `tests/settlement/test_core.py`) MUST need no source change.
- **FR-008**: The three farmstead helpers `_attach_grove`, `_find_appurtenances` and
  `_farmstead_nudges` (27 lines) MUST move to `settlement/homestead_parts.py`, not into the new
  package. Every function they call already lives there (`_draw_grove`, `_find_yard_spot`,
  `_farm_shed_rect`, `_find_garden_spot`), so this REMOVES residue rather than packaging it - and a
  27-line module holding three helpers that belong somewhere else is exactly the over-fragmentation
  clause 13 warns costs more than length does.
- **FR-009**: Comment lines MUST NOT be lost. The count across the new files MUST be greater than or
  equal to the old file's, and any "above"/"below" sentence made false by crossing a module boundary
  MUST be re-pointed rather than deleted.
- **FR-010**: `settlement/CLAUDE.md`'s `land.py` row MUST be updated to point at the new package
  index, matching the form the seven sibling rows already use.
- **FR-011**: The `settlement/` coverage RATCHET floor MUST NOT be lowered. Code motion moves no
  line in or out of coverage, so the floor holds unchanged.
- **FR-012**: A guard test MUST hold the composed surface - every member reachable on `Settlement`
  after the split, and no name bound in two submodules - and it MUST be proven to FIRE on a
  synthetic sabotage before it is trusted (the feature 117 / clause 14 discipline: a census that
  silently returns nothing is indistinguishable from a clean bill of health).

### Key Entities

- **A member**: one class-body `def` in `LandMixin`, sliced together with its decorators, its
  preceding blank lines and any comment block written above it. 14 of them, plus one module-level
  function after the class.
- **The partition**: the mapping from member to destination module. It is the one piece of real
  DECISION in this feature; everything else is mechanical.
- **The composed surface**: `LandMixin`, recomposed in `land/__init__.py` from four sub-mixins, with
  no members of its own.
- **The byte-identity oracle**: the sorted hash list of every artifact under `pool/`, taken on
  unmodified code in a scratch copy or a detached worktree, never by stashing.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: No file this feature creates or touches exceeds 1,000 raw lines. Concretely: the four
  new modules land at roughly 242 / 188 / 362 / 338 lines, and `homestead_parts.py` goes from 756 to
  about 783.
- **SC-002**: A session working on any one of the four land subjects loads at most about 362 lines
  instead of 1,187 - a reduction of between 69% and 84% depending on the subject.
- **SC-003**: Every artifact under `pool/` hashes identically before and after. Not "almost all",
  not "only the title moved": an empty diff.
- **SC-004**: Zero consumer source changes outside `settlement/` itself. The census is three files
  and all three stay untouched.
- **SC-005**: The full gate passes with no failure absent from the measured baseline, and the
  `settlement/` coverage floor is met without being lowered.
- **SC-006**: Comment lines are conserved or increased, so no researched grounding is lost in the
  move.
- **SC-007**: `settlement/` contains no remaining source file over 1,000 raw lines - the eight-part
  split that began with feature 025 is complete.

## Assumptions

- **Spec number 120 is claimed from main's state**, per the concurrent-sessions protocol: the
  highest `specs/NNN` seen after sync-in was 119, and the claim is published by committing and
  pushing `specs/120-land-package/` the moment `spec.md` exists.
- **The pool artifacts committed in git are NOT a valid baseline.** They were produced by whatever
  engine shipped them, and the frozen exhibits deliberately predate rules the current engine has.
  The baseline is captured by regenerating from a scratch copy at the pre-change commit, so it
  reflects what THIS code produces (feature 110 research R3).
- **`--frozen-ok` is required on the baseline sweep.** Without it the 19 frozen legacy maps print
  `FROZEN` and skip, and they are the maps that exercise most of `land.py`: `perimeter_dike`,
  `dike_top_houses` and `near_ring_paddy` are polder and city-tier features the scripted hamlet
  cohort barely touches. Skipping them would leave the headline members unexercised by the oracle.
- **The baseline is re-taken if main moves under the clone.** A baseline is only a baseline for the
  commit it was measured at; syncing in a peer's engine change invalidates it.
- **No `settlement-review` pass is needed.** That agent judges what a green gate structurally
  cannot - glyph legibility, feature form, whether a map reads as a place. A byte-identical pool has
  no such residue to judge, and feature 118 established the same reasoning for the same reason.
- **`ruff format` may reflow the copied import headers** in the new modules; that is formatting of
  the HEADER, not of a moved body, and is expected.
- **Existing pre-split behavior stays exactly as it is**, including anything currently imperfect. A
  pure move is not the place to fix a rule, and any defect noticed in passing is recorded rather
  than repaired here.

## Out of Scope - accepted limitations and the alternatives declined

Recorded per the CLAUDE.md rule that a decision to ACCEPT a limitation is written down with what it
costs and what was priced against it, so a later session does not reopen it from scratch or mistake
it for a bug. Chosen by this session, 2026-08-17, under a GM instruction scoped to file and function
size.

- **Decomposing any function body.** Clause 12 is measured and already satisfied (see "Why this
  exists"); the cost of accepting this is nil, and the declined alternative - splitting
  `near_ring_paddy` or `perimeter_dike` into helpers - was rejected because clause 12 explicitly
  rejects the 10-line-function dogma and both functions are deep-but-cohesive engine code of exactly
  the kind it protects.
- **Moving `pasture` into the land subsystem.** `future-work.md` proposes it and the reasoning is
  sound - it is a land surface, and this package already holds the commons and marsh. Declined here
  because it is a relocation FROM another package whose members this feature never reads, and it
  would put a second cross-package move inside a change whose entire safety argument is that nothing
  moves but text. Cost of accepting: `pasture` stays one directory away from its siblings until that
  change is made, which is where it has been all along.
- **Relocating `surface_water_dist` into `_geom/`.** Arguably the better long-term home: `_geom/`
  already holds the shared placer-and-check manifest predicates, and `_geom/village.py` is the
  precedent for a small pure-manifest module. Declined because it buys no clause 13 benefit (17
  lines), it would move the monkeypatch path a second time in one feature, and this change already
  carries one cross-file relocation. Cost of accepting: the predicate lives in `wet.py`, which the
  index states plainly so nobody has to guess.
- **Any change to what a map draws, where anything is placed, or what the gate checks.**
