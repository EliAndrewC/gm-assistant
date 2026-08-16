# Feature Specification: Derive the check_village Gate Registry

**Feature Branch**: `109-registry-derive` (no branch - `SPECIFY_FEATURE=109-registry-derive`, per the no-feature-branches rule)

**Created**: 2026-08-16

**Status**: Draft

**Input**: User description: "Collapse check_village/registry.py (8,432 lines) to a derived surface per constitution clause 14 (rosters that restate code are derived, not maintained)."

## Context

`check_village/registry.py` is 8,432 lines: a ~1,405-line import block naming every one of the
~600 segment functions, a `_GateSeg` NamedTuple, and a ~7,000-line `GATE_SEGMENTS` tuple of 1,365
dense data rows (`fn`, `free`, `writes`, `checks`, `needs`, `meta`, `always`), plus `META_CHECKS`
and the computed `_SEG_DEPS`. The file carries a clause-13 justification header claiming its rows
are ordered DATA - but clause 14 (constitution v1.7.0) supersedes that reading: every field of
every row was **machine-computed** by `specs/022-gate-check-registry/transform_gate.py` from the
same statement bodies that now live verbatim in the `segments_*.py` modules, and the execution
order is encoded in the `_seg_NNNN[_NNN]` function names themselves. Nothing in the registry is a
hand-written decision that exists nowhere else; it is a derived roster being maintained by hand.
Feature 027 already applied the clause-14 method to `__init__.py` (3,148 -> 63 lines, zero
consumer changes) and explicitly deferred `registry.py` as its own effort. This is that effort.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Registry becomes a derived surface with identical gate behavior (Priority: P1)

A future session (the "user" of this package is a Claude session loading files into its context
window) needs to consult or modify the gate. Today, touching any registry concern loads an
8,432-line file. After this feature, the registry module is a small piece of derivation logic; the
row data is computed from the `segments_*` modules at import time, and the gate behaves
identically on every manifest.

**Why this priority**: This is the whole feature - the token sink is the motivation, and identical
behavior is the non-negotiable constraint (the 189-check gate protects every settlement map in the
pool).

**Independent Test**: Freeze the current `GATE_SEGMENTS` tuple as a golden fixture, swap in the
derived registry, and assert the derived tuple is equal row-for-row (function identity, all six
metadata fields, order). Run the full `check_village` test suite and the regression corpus
unchanged.

**Acceptance Scenarios**:

1. **Given** the current hand-maintained registry frozen as a fixture, **When** the derived
   registry is imported, **Then** every derived row equals its frozen counterpart (same segment
   function, same `free`/`writes`/`checks`/`needs`/`meta`/`always`, same position).
2. **Given** the existing test suite and regression-corpus manifests, **When** they run against
   the derived registry, **Then** every test passes and every manifest produces the same
   pass/fail/waiver results as before.
3. **Given** the collapse has landed, **When** a session lists the package, **Then** the registry
   surface is a small file (target: under ~200 lines including the derivation logic and its
   record-the-why commentary) and no other consumer file changed.

---

### User Story 2 - The safety property moves into guard tests proven to fire (Priority: P2)

The registry's row order IS the gate's execution contract (feature 022). Today that contract is
"protected" by the file being hand-maintained data. After this feature, guard tests hold the
property instead: they must detectably fail when the contract is violated (a segment out of order,
a metadata field wrong, a segment dropped or duplicated).

**Why this priority**: Clause 14 requires the safety property to move into a guard test *proven to
fire* before the roster is derived - deriving without the guard just hides breakage.

**Independent Test**: Mutation-test each guard: perturb the derivation (swap two rows, drop a
name from a `needs` tuple, flip a `meta` flag, omit a segment) and confirm the guard test fails;
restore and confirm it passes.

**Acceptance Scenarios**:

1. **Given** the guard tests, **When** the derived order of any two segments is swapped, **Then**
   at least one guard fails.
2. **Given** the guard tests, **When** a derived metadata field diverges from the frozen fixture,
   **Then** at least one guard fails and its message names the segment and field.
3. **Given** the guard tests, **When** a segment function is removed from a segments module but
   the fixture still lists it, **Then** at least one guard fails.

---

### User Story 3 - Adding a new gate segment stays a documented, workable path (Priority: P3)

A future feature adds a new check. Today the documented workflow is "add the `_GateSeg` row at the
right execution position in `registry.py`". After this feature, the workflow must be re-documented
in the package's `CLAUDE.md`: how a new segment's name places it in the order, and how its
metadata comes into being (derived, with the fixture updated deliberately).

**Why this priority**: The package evolves (features 022/024/026/027 all touched it); an
undocumented derivation would trade a token sink for a knowledge sink.

**Independent Test**: Follow the updated `CLAUDE.md` instructions to add a trivial no-op segment
in a scratch branch of the working tree; the derived registry picks it up at the intended
position; revert.

**Acceptance Scenarios**:

1. **Given** the updated package `CLAUDE.md`, **When** a session follows it to add a segment,
   **Then** the documented steps produce a registry row at the intended execution position without
   hand-editing a data tuple.
2. **Given** the collapse has landed, **When** a session reads the package `CLAUDE.md` index,
   **Then** the registry entry describes the derived design and points at where the "why" is
   recorded.

---

### Edge Cases

- A segment whose derived metadata cannot be made to match the frozen row exactly (an AST-analysis
  edge the original transform special-cased): the mismatching field for that segment is a real
  decision, not derivable - it stays as an explicit, justified exception entry (expected to be
  rare or empty; every entry must carry a why).
- Sub-numbered segments (`_seg_0040_000` ... `_seg_0040_036`) must interleave at their exact
  legacy position - ordering must compare the full numeric name, not a single integer prefix.
- Multi-check segments (e.g. `_seg_0587` emits three check names) and zero-check helper segments
  (name suffix is a variable, not a check) must both derive correctly - the check list cannot be
  read off the function name alone.
- `META_CHECKS` and `_SEG_DEPS` are themselves derived from the rows and must come out identical.
- Import-time cost: the derivation runs on every `check_village` import (gate runs, tests,
  renders). It must not noticeably slow the ~15 s scripted-generation loop or the test suite.
- The `test_check_village_surface.py` guard from feature 027 and any other test importing registry
  names must keep passing without modification (zero consumer changes includes test consumers,
  except tests whose subject IS the registry file's internals).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The current `GATE_SEGMENTS` contents (segment identity by name, `free`, `writes`,
  `checks`, `needs`, `meta`, `always`, and row order), plus `META_CHECKS`, MUST be frozen as a
  regression fixture BEFORE the registry is replaced, and that fixture MUST be committed with the
  feature.
- **FR-002**: After the collapse, the registry surface MUST export `GATE_SEGMENTS`, `META_CHECKS`,
  and `_SEG_DEPS` with values equal to the frozen fixture (row-for-row, field-for-field, in
  order), derived from the `segments_*` modules rather than restated by hand.
- **FR-003**: No consumer file may change: `driver.py`, `__init__.py`, the segments modules, and
  all existing tests keep their current imports and behavior. (Tests that specifically exercise
  the old file's internals may be updated; the feature-027 surface guard may not.)
- **FR-004**: Guard tests MUST hold the execution-order and metadata contract, and each guard MUST
  be proven to fire (a deliberate perturbation makes it fail) before the derived registry ships.
  The proof runs MUST be recorded in the feature artifacts.
- **FR-005**: Any row field that cannot be derived exactly MUST live in an explicit exception
  structure with an inline justification per entry - silent divergence from the fixture is not
  permitted, and an empty exception structure is the expected outcome.
- **FR-006**: The derivation logic MUST record its "why" where it lives (module docstring or
  adjacent comments): what each field means, how it is derived, why the order is trusted to the
  segment names, and a pointer to feature 022's transform as the provenance of the scheme.
- **FR-007**: The package `CLAUDE.md` (and any other doc naming `registry.py`'s size carve-out,
  including the constitution's clause-13 example if it cites this file) MUST be updated to
  describe the derived design and the new add-a-segment workflow.
- **FR-008**: The full verification gate for Python changes MUST pass: `ruff check`,
  `ruff format --check`, `mypy --strict`, and pytest with 100% line coverage on the touched
  pure-logic code, plus the whole `check_village`/diagram test bed run once at the end.
- **FR-009**: Importing the package with the derived registry MUST NOT materially slow existing
  workflows (budget: added import-time work stays under ~1 second; measured and recorded).
- **FR-010**: The memory/status trail MUST be closed out: the "registry.py refactor deferred"
  standing note is superseded by this feature and MUST be updated when the feature lands.

### Key Entities

- **Gate segment**: one extracted statement of the legacy gate, a keyword-only function in a
  `segments_*` module; its name encodes execution position and (usually) its check or primary
  write.
- **Registry row (`_GateSeg`)**: (fn, free, writes, checks, needs, meta, always) - the per-segment
  metadata the driver uses for targeted execution and dependency closure.
- **Frozen fixture**: the pre-collapse row data, serialized; the equality oracle for the
  derivation and the guard tests' reference.
- **Exception structure**: the (expected-empty) set of hand-stated field overrides for rows whose
  derivation cannot reproduce the fixture, each with a recorded why.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The hand-maintained registry data file shrinks from 8,432 lines to a derived
  surface of under ~200 lines (fixture and tests excluded); the package sheds roughly 8,000 lines
  of restated data.
- **SC-002**: The full existing test suite and the regression corpus pass unchanged; the derived
  rows are equal to the frozen fixture for all 1,365 rows.
- **SC-003**: Each guard test has a recorded proven-to-fire run (perturbation -> red, restore ->
  green).
- **SC-004**: Zero consumer-file changes land (verified by diff scope); the feature-027 surface
  guard passes untouched.
- **SC-005**: Package import-time overhead added by derivation is measured at under ~1 second.

## Assumptions

- The rows really are fully derivable: `free` equals each segment function's keyword-only
  parameter list (the signatures were generated FROM `free` by feature 022's transform), and
  `writes`/`needs`/`checks`/`meta`/`always` are reproducible by running the same AST analysis the
  transform used against the segment bodies, which are verbatim copies of the analyzed statements.
  If recon during planning falsifies this for some rows, FR-005's exception structure absorbs
  them; if it falsifies it wholesale, the feature stops and reports rather than shipping a
  half-derived registry (that outcome would mean the rows ARE decisions and clause 13's carve-out
  was correct after all).
- Execution order is fully recoverable from the `_seg_` function names' numeric components; no
  two segments share a numeric key.
- The derivation may reuse/adapt analysis code from `specs/022-gate-check-registry/transform_gate.py`
  (repo-local provenance, no new dependencies required).
- Whether derivation runs at import time or as a build step with a committed artifact is a
  plan-stage decision; the spec constrains only equality, consumer stability, and the time budget.
- `_SEG_DEPS` stays computed exactly as today (from `needs` x `writes`); it was already derived.
