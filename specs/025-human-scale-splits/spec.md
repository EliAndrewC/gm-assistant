# Feature Specification: Human-Scale Splits (settlement.py + the two big test files)

**Feature Branch**: `025-human-scale-splits`

**Created**: 2026-08-16

**Status**: Draft

**Input**: User description: "Split the /diagram skill's three remaining oversized files into packages per constitution clause 13 (files stay at human scale, ~1,000 lines), and amend the documentation to state that the rule applies to test files too. Scope: (1) Amend constitution clause 13 (patch bump) + its template/CLAUDE.md mirrors to state explicitly that the human-scale rule covers unit test files as well as source, with the why: the cost being managed is context-window tokens, and a test file is loaded under the same conditions as source (you load test_settlement.py to modify one test the same way you load settlement.py to use one function), so tests get no exemption; the ordered-data registry exemption remains the only carve-out. (2) Split test_checks.py (~11.5k lines) into per-segment test modules mirroring the existing check_village/ package structure from feature 024 - purely mechanical, no design decisions. (3) Split settlement.py (~16k lines) into a settlement/ package with its own CLAUDE.md index - the design-work stage: choose module boundaries (rolling vs layout vs draw functions vs city/castle/wall subsystems), preserve the DRAW ORDER map and ordering-critical comments. (4) Split test_settlement.py (~7.1k lines) mirroring the new settlement/ package layout, strictly after stage 3 settles it. Verification: pure moves with no behavior change - make done green with 100% coverage before and after each stage, and the check_village gate produces identical output on a fixed-seed manifest before/after. Explicitly OUT of scope: check_village/registry.py (8.4k lines) - rides the ordered-data exemption for now; its serious refactor is a separate future effort per GM decision 2026-08-16."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Clause 13 explicitly covers test files (Priority: P1)

The GM decided (2026-08-16) that the file-size rule applies to unit test files exactly as it does
to source files, and the documentation must say so - with the reasoning, per the project's
record-the-why rule. The why: the cost clause 13 manages is context-window tokens, and a test
file is loaded under the same conditions as source - a session loads `test_settlement.py` to
modify one test the same way it loads `settlement.py` to use one function. Nothing about being a
test changes the economics, so tests get no exemption. The ordered-data registry exemption
remains the only carve-out.

**Why this priority**: The documentation is the durable part (same rationale as 024's US1). This
feature's three splits are the application; the amended rule is what makes the next oversized
test file a recognized defect instead of a judgment call re-argued from scratch.

**Independent Test**: Read constitution clause 13; it states that test files are covered, and
why. The clause-13 summaries in `CLAUDE.md` (root) and the plan template's Constitution Check
mirror the same statement.

**Acceptance Scenarios**:

1. **Given** the constitution at v1.6.0, **When** the amendment lands, **Then** clause 13
   explicitly names test files as covered, records the loaded-under-the-same-conditions
   reasoning, the version is bumped per the constitution's own semver policy, and the sync-impact
   header is updated.
2. **Given** the root `CLAUDE.md` clause-13 summary bullet and the plan template's Constitution
   Check, **When** the amendment lands, **Then** each mirror carries the tests-included statement
   (mirrors stay consistent with the constitution, per 024 precedent).

---

### User Story 2 - test_checks.py becomes a navigable test package (Priority: P2)

A session that needs to read or edit the tests for one gate check today loads an 11,475-line
file. After the split, the gate tests live in a test package whose modules mirror the
`check_village/` package structure settled in feature 024 (per-segment-file test modules plus a
shared fixture/helper home), so the session loads only the test module for the segment file it
cares about.

**Why this priority**: Purely mechanical - the target structure already exists (`check_village/`'s
file layout IS the answer), so this is the cheapest of the three splits and exercises the
test-split method that Story 4 reuses. It does not depend on Story 3.

**Independent Test**: The pytest suite collects exactly the same set of tests before and after
(same node count, no test lost or duplicated), all pass, and coverage stays at the gate's
required level; no new test module exceeds the clause-13 threshold.

**Acceptance Scenarios**:

1. **Given** the current single test file, **When** the split lands, **Then** the collected test
   node count is identical, every test passes, and `make done` (or the skill's equivalent gate)
   is green with coverage unchanged.
2. **Given** the new test package, **When** a session asks "where are the tests for the water
   checks?", **Then** the module naming answers directly (module names track the
   `check_village/segments_*` / `common_*` files they test).
3. **Given** shared fixture builders used across the old file (manifest/house/yard/grove
   helpers), **When** the split lands, **Then** they live in one shared home (conftest or a
   helpers module) rather than being duplicated per module.

---

### User Story 3 - settlement.py becomes a navigable package (Priority: P2)

A session that needs one draw function or one layout stage today loads a 16,016-line file - the
largest in the project. After the split, `settlement/` is a package of subsystem files with a
CLAUDE.md that says when to look in each, so the session loads only the subsystem it is working
on. This is the design stage of the feature: module boundaries must be chosen (candidate axes:
rolling/parameter generation vs layout vs draw functions vs city/castle/wall subsystems), and the
DRAW ORDER map plus every ordering-critical comment must survive the move intact and findable.

**Why this priority**: The largest remaining token sink in the skill and the direct application
of clause 13's ask-the-question rule. P2 alongside Story 2 (independent of it); listed after
because it is the riskier, design-heavy stage.

**Independent Test**: Existing callers (`regen.py`, `hamletgen.py`, `poolmaps.py`, pool `.gen.py`
scripts, tests, docs) work unchanged or are updated in this feature; a fixed-seed generation run
produces a byte-identical manifest before and after the split; the check_village gate over that
manifest produces identical verdicts; the package CLAUDE.md indexes every subfile.

**Acceptance Scenarios**:

1. **Given** the current single file, **When** the package split lands, **Then** for a fixed seed
   and spec the generated manifest is byte-identical to the pre-split capture, and the full
   check_village gate over existing pool manifests reports identical verdicts.
2. **Given** the new package, **When** a session asks "where does the city wall get drawn?" or
   "where is the DRAW ORDER contract?", **Then** the package CLAUDE.md answers with a specific
   file and a one-line description.
3. **Given** ordering-critical code (the DRAW ORDER map, comments marking sequence-sensitive
   stages), **When** the split lands, **Then** those comments sit with the code they govern and
   the CLAUDE.md index points at the DRAW ORDER's home.

---

### User Story 4 - test_settlement.py mirrors the new settlement/ layout (Priority: P3)

After Story 3 settles the `settlement/` package layout, the 7,123-line test file splits into test
modules mirroring that layout, so a session editing one subsystem loads only that subsystem's
tests.

**Why this priority**: P3 because it is strictly sequenced after Story 3 (splitting it first
would mean re-shuffling it to match whatever layout Story 3 chooses) and reuses the mechanical
method proven by Story 2.

**Independent Test**: Same identity proof as Story 2 - identical collected test node count, all
green, coverage unchanged, no new module over the threshold, module names track the `settlement/`
subfiles they test.

**Acceptance Scenarios**:

1. **Given** the post-Story-3 package, **When** the test split lands, **Then** the collected
   node count is identical, all tests pass, and the gate is green with coverage unchanged.
2. **Given** the new test modules, **When** a session edits one `settlement/` subfile, **Then**
   there is one obvious test module to load alongside it.

---

### Edge Cases

- **Shared test helpers**: both big test files define module-level fixture builders reused by
  hundreds of tests; the split must give them one shared home without changing what any test
  actually exercises, and without helper-name collisions across new modules.
- **Test collection identity**: renamed/moved tests must not silently drop from collection
  (pytest only collects `test_*` files/functions) or double-collect; the before/after proof is
  the collected node list, not just "tests pass".
- **Import surface of settlement.py**: callers import it as a module (`import settlement` /
  `from settlement import ...`); the package `__init__` must preserve every externally-used name,
  including names consumed by pool `.gen.py` scripts that are not exercised by the test suite.
- **Render/generation caches keyed on source**: the skill has `render_cache.py` /
  `cache_audit.py` / gencache tooling; if any cache keys on source-file hashes or paths, the
  split invalidates or confuses it - the plan must check and record the disposition.
- **Module-level state and import order**: registries, constants, or monkeypatch targets defined
  at settlement.py module scope must keep identity (one definition, importable under the old
  name) so tests that monkeypatch `settlement.X` still patch the object the code reads.
- **DRAW ORDER is a contract**: thematic file grouping must not perturb the draw sequence; the
  order lives in code that executes, not just in a comment.
- **Pre-existing British spellings in test names** (e.g. `..._two_neighbours_share...`): renames
  are OUT of scope for a pure-move feature; recorded so it is a decision, not an oversight. New
  names introduced by the split follow the American-spelling rule.
- **Ordered-data exemption boundary**: if any new `settlement/` subfile is itself a cohesive
  ordered dataset over the threshold, it takes the clause-13 inline justification rather than a
  forced further split.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Constitution clause 13 MUST be amended to state explicitly that unit test files
  are covered by the human-scale rule, recording the why: the managed cost is context-window
  tokens, and a test file is loaded under the same conditions as source (you load a test file to
  modify one test the same way you load a source file to use one function), so tests get no
  exemption; the ordered-data justification remains the only carve-out. Version bumped per the
  constitution's semver policy with the sync-impact header updated.
- **FR-002**: The clause-13 mirrors MUST be updated in the same amendment: the root `CLAUDE.md`
  "Files stay at human scale" bullet and the plan template's Constitution Check reference,
  consistent with how 024 propagated the original clause.
- **FR-003**: `test_checks.py` MUST become a package (or module family) of gate-test files whose
  structure mirrors `check_village/`'s file layout, with shared fixture builders in one shared
  home, and with the collected pytest node set proven identical before/after.
- **FR-004**: `settlement.py` MUST become a `settlement/` package of subsystem files with a
  package `CLAUDE.md` index ("look here when" line per subfile), the public import surface
  preserved via the package `__init__`, and the DRAW ORDER map plus ordering-critical comments
  preserved with the code they govern.
- **FR-005**: Behavior identity for the settlement split MUST be proven: a fixed-seed
  generation produces a byte-identical manifest before and after, and the check_village gate over
  pool manifests and regression fixtures reports identical verdicts.
- **FR-006**: `test_settlement.py` MUST split into test modules mirroring the final
  `settlement/` package layout, strictly after FR-004 settles that layout, with the same
  collection-identity proof as FR-003.
- **FR-007**: All callers and docs MUST be updated where the split changes an invocation or
  path: regen/tooling scripts, pool `.gen.py` scripts, the diagram skill's CLAUDE.md/SKILL.md and
  any doc quoting `settlement.py`, `test_checks.py`, or `test_settlement.py` by name.
- **FR-008**: The full quality gate MUST be green after each story lands (lint, format, strict
  typing, tests, coverage at its current enforced level) - each story is a separately verifiable
  landing, not one big-bang diff.
- **FR-009**: No new file created by this feature may exceed the clause-13 threshold shape used
  by 024 (segment-file scale, roughly ≤2,500 lines) without an inline ordered-data
  justification.
- **FR-010**: `check_village/registry.py` is explicitly OUT of scope: it rides the ordered-data
  exemption for now, and its serious refactor is a separate future effort (GM decision
  2026-08-16). This disposition MUST be recorded in the feature's research notes.

### Key Entities

- **Constitution clause 13 (amended)**: the file-size rule, now explicitly covering test files;
  mirrored in root CLAUDE.md and the plan template's Constitution Check.
- **Gate-test package**: the split of `test_checks.py`, structured to mirror `check_village/`.
- **settlement/ package**: the split of `settlement.py` - subsystem files, `__init__` preserving
  the import surface, CLAUDE.md index, DRAW ORDER home.
- **Settlement-test package**: the split of `test_settlement.py`, mirroring `settlement/`.
- **Identity proofs**: collected-node-list comparison for test splits; fixed-seed manifest
  capture + gate-verdict comparison for the settlement split.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A session working on one settlement subsystem or one segment's tests loads a file
  a fraction of the old size: no new file exceeds ~2,500 lines (vs 16,016 / 11,475 / 7,123
  today), except under an inline ordered-data justification.
- **SC-002**: Behavior identity: 100% of fixed-seed generation captures are byte-identical
  before/after, and 100% of pool manifests and regression fixtures produce identical gate
  verdicts.
- **SC-003**: Test identity: the collected pytest node count for the skill is identical
  before/after each test split, with zero tests lost, added, or duplicated.
- **SC-004**: The full quality gate passes after every story, at the same coverage level as
  before the feature.
- **SC-005**: The constitution, root CLAUDE.md, and plan template all state that clause 13
  covers test files, with the reasoning recorded where the rule lives.
- **SC-006**: Each new package's CLAUDE.md index answers "where does X live?" from the index
  alone - subsystem/segment lookup requires loading exactly one subfile.

## Assumptions

- **Version bump is PATCH** (1.6.0 -> 1.6.1): the amendment clarifies the reach of an existing
  clause rather than adding a new principle or materially new guidance; recorded here as the
  resolved decision per the constitution's semver policy. If the constitution's own policy text
  demands MINOR for any wording expansion, the plan follows the constitution over this
  assumption.
- **Story order** is US1 -> US2 -> US3 -> US4: docs first (cheap, establishes the rule), then the
  mechanical test split, then the design-heavy settlement split, then its dependent test split.
  US2 and US3 are independent; US4 strictly follows US3.
- **"Mirror check_village/"** for test_checks.py means module-per-segment-file (plus common_*
  test modules and a shared helper home), not necessarily module-per-check; granularity follows
  the source package's file layout because that is what a session loads alongside.
- **Pure moves**: no behavior change, no renames beyond what a move forces, no drive-by fixes
  (including pre-existing British-spelling test names). Anything discovered broken gets recorded,
  not silently fixed in-flight.
- **The 024 method transfers**: capture-then-compare identity proofs (oracle sweeps for gate
  verdicts, fixed-seed manifest capture for generation, collected-node lists for tests) are the
  established proof shape; this feature reuses it rather than inventing new machinery.
- **check_village/registry.py stays put** (GM 2026-08-16): ordered-data exemption, future
  dedicated effort; also recorded in session memory.
- The GM handles no part of this; the session runs specify -> plan -> tasks -> implement
  unattended per the project's spec-kit doctrine.
