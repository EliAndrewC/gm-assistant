# Feature Specification: settlement/fields.py -> settlement/fields/ Package Split

**Feature Branch**: `112-fields-package`

**Created**: 2026-08-16

**Status**: Implemented (2026-08-16) - US1, US2 and US3 complete

**Input**: User description: "Split /gm-assistant/.claude/skills/diagram/settlement/fields.py (1,511 lines, a single FieldsMixin class of 24 methods) into a settlement/fields/ package with its own CLAUDE.md index, per constitution Principle X clause 13 (files stay at human scale; the cost being managed is context-window tokens). Two-stage scope, both stages verified by byte-identical pool artifacts. STAGE 1 - PURE MOVE: divide FieldsMixin into subsystem sub-mixins in separate modules. fields/__init__.py composes them into a single FieldsMixin so settlement/core.py's `from .fields import FieldsMixin` and its `class Settlement(...)` bases are UNCHANGED. Reuse the feature 025 transformer at specs/025-human-scale-splits/split_settlement.py as the exemplar; keep the TYPE_CHECKING `self: Settlement` annotation pattern. STAGE 2 - FUNCTION DECOMPOSITION: decompose draw_comb_field (321 lines), apply_land_use (266), water_field (194), which together are 52% of the file. VERIFICATION: make done green; every committed pool artifact byte-identical; check_village gate output identical. Update settlement/CLAUDE.md's index table and add fields/CLAUDE.md. OUT OF SCOPE: splitting test_settlement/test_fields.py (475 lines); any change to DRAW ORDER, knob doctrine, or field geometry; the other oversized settlement modules."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Behavior-preserving package split (Priority: P1)

A session touching one part of the field engine - the comb-field builder, say, or the land-use
overlays - currently loads all 1,511 lines of `settlement/fields.py` to reach it. After this
feature, `settlement.fields` is a package of focused submodules, each well under the ~1,000-line
clause-13 bar, and every existing consumer keeps working with **zero changes**: `settlement/core.py`
still does `from .fields import FieldsMixin` and still lists `FieldsMixin` first in its
`class Settlement(...)` bases, in the same position.

**Why this priority**: This is the feature. A split that changes a drawn coordinate or breaks the
mixin composition is a regression, not a refactor; nothing else in this spec is safe to attempt
without the byte-identity harness this story establishes.

**Independent Test**: Regenerate every pool generator - the live scripted hamlets and, in a
throwaway scratch tree, the frozen legacy maps that are the only exercisers of the comb-field and
land-use wings - and diff each manifest against a pre-split baseline byte-for-byte. Run the full
diagram test suite and the `check_village` gate with no consumer-file edits.

**Acceptance Scenarios**:

1. **Given** the split is complete, **When** each pool generator is re-run at its committed seed,
   **Then** the produced manifest, SVG and PNG are byte-identical to those produced by the pre-split
   tree.
2. **Given** the split is complete, **When** `git status` is checked under `pool/`, **Then** it is
   clean: no committed artifact of a frozen map has been altered.
3. **Given** the split is complete, **When** the full diagram test suite and `make done` run,
   **Then** they pass with zero modifications to any consumer file, including `core.py`.
4. **Given** the split is complete, **When** `Settlement`'s method resolution order is inspected,
   **Then** every one of `FieldsMixin`'s 24 methods resolves to the same implementation as before,
   and class-level monkeypatching of `settlement.Settlement` behaves identically.

---

### User Story 2 - Oversized methods decomposed (Priority: P2)

A maintainer opening `draw_comb_field` (321 lines), `apply_land_use` (266) or `water_field` (194)
today reads one long body and has to hold the whole subsystem in their head - together these three
are 52% of the file. After this feature each is decomposed into named helpers whose names describe
the step, so the method reads top-down as a short sequence of named steps and a future change can
target one of them.

**Why this priority**: The engineering half of the GM's ask, and the reason `fields.py` was chosen
over larger files whose functions are already small. Valuable, but only safe on top of the P1
byte-identity harness - decomposition without that net is exactly where behavior drift hides.

**Independent Test**: After decomposition, no method or helper in the package exceeds ~150 lines
(or carries an inline one-line justification for being genuinely atomic); the byte-identity sweep is
re-run after each individual decomposition and the diff is empty every time.

**Acceptance Scenarios**:

1. **Given** the decomposition is complete, **When** function lengths across the package are
   measured, **Then** no function exceeds ~150 lines without an inline justification, and each
   extracted helper has a name describing what it does.
2. **Given** the decomposition is complete, **When** the byte-identity sweep is re-run after each
   individual method's decomposition, **Then** the manifest diff is empty every time.
3. **Given** the decomposition is complete, **When** the combined `settlement/` coverage is
   measured, **Then** it is at or above the `SETTLEMENT_COV_FLOOR` ratchet, and the floor is raised
   if the split raised it.

---

### User Story 3 - Token-scale package index (Priority: P3)

A session that needs only the land-use overlays (or only the paddy geometry, or only the plot
features) reads the package's `CLAUDE.md` index and loads just that submodule instead of the whole
file. The index says which file holds what, in the style of `check_village/CLAUDE.md`,
`waterfields/CLAUDE.md` and `hamletgen/CLAUDE.md`, and the parent `settlement/CLAUDE.md` table
points at the package rather than at the vanished single file.

**Why this priority**: The token motivation. It falls out of the split almost for free but is only
useful once the split exists, and a package whose index is not wired into the parent index is a
package nobody finds.

**Independent Test**: Every submodule is under the ~1,000-line bar; `fields/CLAUDE.md` names each
submodule with a one-line "look here when"; `settlement/CLAUDE.md`'s "Look here when" table has the
single `fields.py` row replaced by rows that resolve to the new files.

**Acceptance Scenarios**:

1. **Given** the package exists, **When** a reader consults `settlement/CLAUDE.md` and then
   `fields/CLAUDE.md`, **Then** they can identify the single file for a given concern without
   opening any source file.
2. **Given** the package exists, **When** file sizes are measured, **Then** every submodule,
   `__init__.py` included, is under ~1,000 raw lines.

---

### Edge Cases

- **The mixin is the unit, not the module.** `fields.py` is one `FieldsMixin` class, so the split
  divides a CLASS, not a set of module-level functions. `fields/__init__.py` must compose the
  sub-mixins back into a single name `FieldsMixin` so `core.py` is untouched. Sub-mixin method names
  must not collide, or MRO silently picks a winner; a guard must prove the composed class exposes
  exactly the 24 methods it exposes today.
- **Cross-group method calls.** Methods in one proposed group call methods in another through
  `self.` (for example the comb builder reaching paddy-surface helpers). That keeps working after
  the split because every sub-mixin lands on the same `Settlement` instance, but it means the
  partition cannot be validated by import analysis alone - the seams are conceptual, not
  dependency-derived.
- **Shared private helpers.** Small helpers (`_split_convex`, `_rows`, `_plot_center_span`,
  `_paddy_surface`) may be used by more than one group. Each must land in exactly one module, chosen
  by primary user, or in a shared helpers module - the choice is a planning decision and must be
  recorded with its reason.
- **Module-level name binding and monkeypatching.** Submodules bind shared helper names at import
  (`from .._geom import ...`), so patching `settlement.fields.<name>` would no longer reach code in
  a sub-mixin. `settlement/CLAUDE.md` already documents this hazard for the parent split and records
  that no test in the suite patches a settlement module-level name; that census must be re-verified
  for `fields` specifically before the move, not assumed.
- **Import cycles.** Submodules share geometry and knob helpers from `.._geom` and `.._knobs`, and
  must annotate `self: "Settlement"` under `TYPE_CHECKING` with `from ..core import Settlement` -
  the pattern that lets `mypy --strict` resolve cross-subsystem attribute access with no runtime
  cycle. A sub-mixin importing `core` at runtime would create one.
- **The byte-identity oracle must reach the code being changed.** The live scripted pool is four
  `valley_paddy` hamlets; the comb-field and land-use wings are exercised by the FROZEN legacy maps
  and by unit tests, not by any live gen. So the sweep must include the frozen gens run in a
  throwaway scratch tree, or the decomposition of `apply_land_use` and `draw_comb_field` ships with
  no manifest-level oracle at all.
- **The frozen pool must stay byte-clean.** Running a frozen gen for a differential oracle is
  legitimate; committing what it produces is not. The sweep must leave `pool/`'s committed bytes
  exactly as it found them (restore, do not re-run), per the freeze rules.
- **RNG draw order.** The engine is seeded and deterministic, and randomness is positional or
  scoped. Any extraction that changes the order in which draws happen changes every downstream
  coordinate. Extractions must preserve code order, draw order and float-operation order exactly.
- **Coverage accounting.** The Makefile enforces 100% on everything except `*/settlement/*`, which
  rides the `SETTLEMENT_COV_FLOOR` ratchet. New files under `settlement/fields/` match that same
  glob, so the Makefile needs no change - but this must be verified rather than assumed, because a
  mismatch would silently move field code from the ratchet into the 100% rule or out of both.
- **Deleting the old file.** `fields.py` must be removed in the same change; a stale module beside a
  package of the same name is a shadowing hazard.
- **Comments carry researched "why".** The record-the-why rule means the file's inline reasoning
  (bund spacing, overlay prevalence, plot-feature rates) is load-bearing documentation. It must move
  with its code intact, not be trimmed as part of "tidying".

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `settlement.fields` MUST become a package of focused submodules; the monolithic
  `settlement/fields.py` MUST be removed in the same change.
- **FR-002**: `settlement/core.py` MUST NOT change: `from .fields import FieldsMixin` must keep
  resolving, and `FieldsMixin` must keep its current position in the `class Settlement(...)` base
  list.
- **FR-003**: `fields/__init__.py` MUST compose the sub-mixins into a single `FieldsMixin` exposing
  exactly the 24 methods the current class exposes, with no name collisions between sub-mixins; a
  guard test MUST prove the composed surface, and MUST be demonstrated to FAIL against a
  deliberately dropped method before it is trusted.
- **FR-004**: Regenerating every pool generator - the live scripted maps in place, and the frozen
  legacy maps in a throwaway scratch tree - MUST produce artifacts byte-identical to those produced
  by the pre-split tree at the same seeds. The baseline MUST be captured before any code change.
- **FR-005**: The sweep MUST leave every committed artifact under `pool/` byte-unchanged; `git
  status` under `pool/` MUST be clean at the end of each stage.
- **FR-006**: `draw_comb_field`, `apply_land_use` and `water_field` MUST be decomposed into named
  helpers; no function in the package may exceed ~150 lines without an inline one-line
  justification.
- **FR-007**: Every file in the package, `__init__.py` included, MUST be under ~1,000 raw lines
  (constitution clause 13).
- **FR-008**: The package MUST have a `CLAUDE.md` index in the established style: one line per
  submodule saying what lives there and when to load it. `settlement/CLAUDE.md`'s "Look here when"
  table MUST replace its single `fields.py` row with rows resolving to the new files.
- **FR-009**: Every submodule MUST use the `TYPE_CHECKING` + `self: "Settlement"` annotation pattern
  so `mypy --strict` passes with no runtime import cycle.
- **FR-010**: A consumer census for `settlement.fields` module-level names MUST be run and recorded
  before the move, covering tests, tooling and pool gens; any name reached from outside MUST keep
  resolving, and any monkeypatch target MUST be documented in `fields/CLAUDE.md`.
- **FR-011**: The full diagram test suite, the `check_village` gate, and the `pool/regressions/`
  negative-fixture corpus MUST pass unchanged - the negative fixtures must still FAIL their checks,
  proving the checks kept their teeth.
- **FR-012**: Existing comments and docstrings MUST move with their code intact, in particular every
  researched constant's "why".
- **FR-013**: Combined `settlement/` coverage MUST be at or above `SETTLEMENT_COV_FLOOR`; if the
  split raises the achievable figure, the floor MUST be raised to match and never lowered.
- **FR-014**: Docs that reference the FILE `settlement/fields.py` MUST be updated to the package;
  prose references to importable paths stay valid, and prior `specs/NNN` artifacts stay verbatim as
  historical record.

### Key Entities

- **Sub-mixin**: one class in one submodule, holding one field subsystem, under the ~1,000-line bar,
  named for what it holds; composed into `FieldsMixin` by the package `__init__`.
- **Composed surface**: the 24 method names `FieldsMixin` exposes today, which the package must
  reproduce identically, plus any module-level name a consumer reaches.
- **Byte-identity baseline**: the set of artifacts produced by the pre-split tree at fixed seeds -
  the oracle for every subsequent step, and the only thing that makes Stage 2 safe.
- **Extracted helper**: a named function pulled out of an oversized method, taking its inputs as
  parameters and returning its outputs, preserving code order and RNG draw order exactly.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every regenerated artifact - live scripted maps plus the frozen legacy maps swept in
  scratch - is byte-identical to the pre-split baseline: zero differing bytes.
- **SC-002**: Zero consumer files are modified. The change touches only the new package, the deleted
  monolith, the new guard test, docs, and `specs/`; `core.py` in particular is untouched.
- **SC-003**: Every file in `settlement/fields/` is under ~1,000 raw lines, and no function exceeds
  ~150 lines without an inline justification. The three named methods are no longer 51% of the
  subsystem.
- **SC-004**: A reader given any one of the named concerns can identify the single file holding it
  from `settlement/CLAUDE.md` plus `fields/CLAUDE.md` alone, without opening a source file.
- **SC-005**: `make done` is green - ruff, format check, `mypy --strict`, pytest, the 100% rule on
  non-settlement modules and the `settlement/` ratchet - with the same test count as before the
  split.
- **SC-006**: The guard test on the composed mixin surface has been observed to FAIL against a
  deliberately broken composition before being trusted.

## Assumptions

- The proposed seams - paddy and water fields, comb fields, land-use overlays, plot features and
  ponds - follow the file's existing method ordering, which already groups related methods
  contiguously. The exact module list and the home of each shared helper are settled in planning,
  not here.
- `core.py` being the only consumer of the name `FieldsMixin` is established by the census run
  before this spec (one import, one base-list mention). FR-010 re-verifies the wider module-level
  surface rather than trusting that narrower result.
- The committed pool manifests are NOT a valid baseline on their own - the pool is frozen against
  re-rolls and the engine may have drifted since some artifacts were committed. The baseline is
  captured from a scratch copy of the pre-split tree, the method features 110 and 111 used.
- Running frozen legacy gens as a differential oracle in a scratch tree does not violate the freeze,
  which forbids maintaining, re-gating and committing them - not reading them. No frozen artifact is
  regenerated in place.
- `test_settlement/test_fields.py` (475 lines) stays a single file: it is comfortably under the
  clause-13 bar, so splitting it would be churn rather than debt repayment. It tracks the package by
  section order instead. If Stage 2 pushes it past the bar, that is a follow-up, not a scope
  expansion here.
- No behavior change of any kind is in scope. No field geometry, DRAW ORDER position, knob, or
  placement rule changes, so the byte-identity oracle stays valid throughout.
- This feature supersedes nothing; it applies the clause-13 method that features 024, 025, 027, 110
  and 111 established to the largest remaining live-engine module with genuine function-level debt.
