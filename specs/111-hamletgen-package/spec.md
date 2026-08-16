# Feature Specification: hamletgen.py -> hamletgen/ Package Split

**Feature Branch**: `111-hamletgen-package`

**Created**: 2026-08-16

**Status**: Implemented (2026-08-16) - US1/US3/US4 complete; US2 held, see research.md R12

**Input**: User description: "Refactor .claude/skills/diagram/hamletgen.py (2,913 lines) into a hamletgen/ package of focused submodules with its own CLAUDE.md index, following the waterfields/ (feature 110) and check_village/ (feature 024) exemplars and constitution Principle X clause 13 (files at human scale, ~1,000-line bar) plus clause 14 (derived re-export surface). Two documented motivations: (1) tokens - a package with a CLAUDE.md index lets a session load only the stage it needs (water, field, sink, ways, homesteads, wells, hinterland, frame) instead of all 2,913 lines on every hamlet re-roll; (2) engineering - decompose the oversized stage functions (stage_ways 177 lines, seat_cluster 127, stage_sink 168, place_wells 164, open_ground_patches 137, stage_polder 126, stage_homesteads 111, connector_track 89, belt_polygon 85) into named sub-stage functions. The file's own STAGE banner comments already mark the seams. The refactor must be behavior-preserving: byte-identical manifests for the four live hamlets (inashiro, mizuguchi, kashikawa, sawada) plus a seeded cohort sweep, with zero consumer changes - pool gens import HamletSpec/generate, and test_hamletgen.py + cohort_audit.py reach 47 distinct hg.* names including four underscore names (_arm_crossing_accidental, _clear_gap, _fork_spur, _near_line). The STAGES tuple is the pipeline contract and must stay in one place with an ordering comment. test_hamletgen.py (714 lines) becomes test_hamletgen/ mirroring the modules, per constitution v1.6.1 (tests count)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Behavior-preserving package split (Priority: P1)

A session working on the scripted hamlet generator currently loads all 2,913 lines of
`hamletgen.py` to touch one stage of the pipeline. After this feature, `hamletgen` is a package of
focused submodules, each well under the ~1,000-line clause-13 bar, and every existing consumer
keeps working with **zero changes**: the four pool `.gen.py` scripts (`inashiro`, `mizuguchi`,
`kashikawa`, `sawada`) still do `from hamletgen import HamletSpec, generate`, and
`test_hamletgen.py` + `cohort_audit.py` still reach all 47 distinct `hg.<name>` attributes they use
today - including the four underscore names (`_arm_crossing_accidental`, `_clear_gap`, `_fork_spur`,
`_near_line`).

**Why this priority**: This is the feature. A split that changes rendered output or breaks a
consumer is a regression, not a refactor; nothing else in this spec is safe to attempt without the
verification harness this story establishes.

**Independent Test**: Regenerate all four live hamlets and a fixed-seed cohort and diff each
manifest against a pre-split baseline byte-for-byte (deterministic seeds make this exact). Run the
full diagram test suite and the `check_village` gate with no consumer-file edits.

**Acceptance Scenarios**:

1. **Given** the split is complete, **When** each of the four live hamlet gens is re-run at its
   committed seed, **Then** the produced manifest is byte-identical to the one produced by the
   pre-split monolith.
2. **Given** the split is complete, **When** a fixed-seed cohort sweep is run
   (`hamletgen --batch`), **Then** every rolled manifest is byte-identical to the pre-split
   baseline for the same seeds, and the pass/fail verdict per seed is unchanged.
3. **Given** the split is complete, **When** the full diagram test suite and `make done` gate run,
   **Then** they pass with zero modifications to any consumer file.
4. **Given** the split is complete, **When** every import form in use today is exercised
   (`from hamletgen import HamletSpec, generate`; `import hamletgen as hg` attribute access for all
   47 censused names), **Then** each resolves to the same object as before.

---

### User Story 2 - Oversized stage functions decomposed (Priority: P2)

A maintainer opening `stage_ways` (177 lines), `stage_sink` (168), `place_wells` (164),
`open_ground_patches` (137), `seat_cluster` (127), `stage_polder` (126), `stage_homesteads` (111),
`connector_track` (89) or `belt_polygon` (85) today reads one long body and has to hold the whole
stage in their head. After this feature each is decomposed into named sub-stage functions whose
names describe the step, so the stage reads top-down as a short sequence of named steps and a
future change can target one of them.

**Why this priority**: The engineering motivation. Valuable, but only safe on top of the P1
byte-identity harness - decomposition without that net is exactly where behavior drift hides.

**Independent Test**: After decomposition, no function in the package exceeds ~150 lines (or
carries an inline one-line justification for being genuinely atomic); manifests remain
byte-identical; coverage unchanged.

**Acceptance Scenarios**:

1. **Given** the decomposition is complete, **When** function lengths across the package are
   measured, **Then** no function exceeds ~150 lines without an inline justification, and each
   extracted sub-stage has a name describing what it does.
2. **Given** the decomposition is complete, **When** the byte-identity sweep is re-run after each
   individual function's decomposition, **Then** the manifest diff is empty every time.

---

### User Story 3 - Token-scale package index (Priority: P3)

A session that needs only the well-siting logic (or only the field-fitting, or only the hinterland
scan) reads the package's `CLAUDE.md` index and loads just that submodule instead of the whole
monolith. The index says which file holds what, in the style of `check_village/CLAUDE.md` and
`waterfields/CLAUDE.md`.

**Why this priority**: The token motivation, and the reason this file was picked next. It falls out
of the split almost for free but is only useful once the split exists.

**Independent Test**: Every submodule is under the ~1,000-line bar; `CLAUDE.md` names each
submodule with a one-line "look here when"; each named concern (constants, site plan, geometry
helpers, water frame + field, sink, cluster seating, ways, homesteads + wells, hinterland +
woodland + windbreak, crossings + notice board + frame, the pipeline driver, the CLI) maps to
exactly one submodule.

**Acceptance Scenarios**:

1. **Given** the package exists, **When** a reader consults `hamletgen/CLAUDE.md`, **Then** each
   submodule is listed with its contents and the reader can identify the single file for a given
   concern without opening any source file.
2. **Given** the package exists, **When** file sizes are measured, **Then** every submodule
   (`__init__.py` included) is under ~1,000 raw lines.

---

### User Story 4 - Test file mirrors the package (Priority: P4)

`test_hamletgen.py` (714 lines) becomes a `test_hamletgen/` package whose modules mirror the source
submodules, so a session modifying one stage loads only that stage's tests - the same economics
that motivate the source split, applied to tests per constitution v1.6.1.

**Why this priority**: Under the ~1,000-line bar today, so this is preventive rather than
corrective; it is cheap once the source partition is settled, and doing it in the same feature
means the source/test correspondence is established by the same person who chose the partition.

**Independent Test**: `test_hamletgen/` modules each map to a source submodule by name; the full
suite collects and passes the same number of tests as before the move.

**Acceptance Scenarios**:

1. **Given** the test split is complete, **When** the suite runs, **Then** the same set of test
   node IDs passes (module path changes only), with no test deleted, skipped or renamed in
   substance.
2. **Given** the test split is complete, **When** a source submodule is named, **Then** exactly one
   `test_hamletgen/` module corresponds to it.

---

### Edge Cases

- **Underscore names imported from outside**: `test_hamletgen.py` uses `hg._arm_crossing_accidental`,
  `hg._clear_gap`, `hg._fork_spur`, `hg._near_line`. A bare star-import surface drops underscore
  names, so the re-export surface must carry them explicitly. A guard test must prove every name any
  consumer reaches today resolves from the package.
- **Re-exported third-party names**: `hg.point_in_poly` is not defined in `hamletgen` - it is
  imported into the monolith from another module and reached through it. The census must
  distinguish defined-here names from pass-through names, and the package surface must preserve
  both.
- **Module-level constant identity**: consumers read constants (`ROLLED_ARCHETYPES`,
  `OFFTAKE_LADDER`, `WIND_VECTORS`, `FIELD_ARCHETYPES`, `SQ_FT_PER_ACRE`,
  `GROSS_ACRES_PER_HOUSEHOLD`); re-export must preserve object identity, not copies that could
  drift.
- **The `STAGES` tuple is the pipeline contract**: the module docstring says "THE ORDER IS THE
  DESIGN," and the skill's DRAW ORDER map depends on it. Splitting the stages across files must not
  scatter the order; `STAGES` stays in exactly one place with a comment at the point of change
  saying the sequence is load-bearing.
- **RNG draw order**: the generator is seeded and deterministic. Any extraction that changes the
  order in which random draws happen changes every downstream coordinate. Extractions must preserve
  code order, draw order and float-operation order exactly.
- **Import cycles**: submodules share helpers (geometry predicates, the plan dataclass, constants);
  the partition must be ordered so no cycle forms.
- **CLI entry point**: `python3 hamletgen.py --batch 12` is documented in the module docstring and
  in `hamletgen.md`. A package must keep an equivalent invocation working, and any doc naming the
  old form must be updated.
- **`sys.path` consumers**: pool `.gen.py` scripts import `hamletgen` after adding the diagram dir
  to `sys.path`; a package directory at the same path satisfies this unchanged, but the old
  `hamletgen.py` must be deleted in the same change so a stale monolith can never shadow the
  package.
- **Retry loops inside stages**: several stages retry internally against the placer's verdict.
  Extraction must not change how many attempts run or the state each attempt sees.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `hamletgen` MUST become a package of focused submodules; the monolithic
  `hamletgen.py` MUST be removed in the same change.
- **FR-002**: Every existing consumer import MUST keep working with zero consumer-file changes -
  the two `from hamletgen import ...` forms in the four pool gens, and all 47 distinct `hg.<name>`
  attributes used by `test_hamletgen.py` and `cohort_audit.py`, including the four underscore names
  and the pass-through name `point_in_poly`.
- **FR-003**: The package `__init__.py` MUST be a derived re-export surface per constitution
  clause 14 (star imports plus an explicit aliased block for underscore names), not a hand-maintained
  roster; a guard test MUST enumerate every name any consumer reaches today and prove each resolves,
  and MUST be demonstrated to FAIL before it is trusted.
- **FR-004**: Regenerating the four live hamlets and a fixed-seed cohort MUST produce manifests
  byte-identical to those produced by the pre-split monolith at the same seeds. The baseline MUST be
  captured before any code change.
- **FR-005**: The oversized stage functions MUST be decomposed into named sub-stage functions; no
  function in the package may exceed ~150 lines without an inline one-line justification.
- **FR-006**: Every file in the package, `__init__.py` included, MUST be under ~1,000 raw lines
  (constitution clause 13).
- **FR-007**: The package MUST have a `CLAUDE.md` index in the `check_village/` and `waterfields/`
  style: one line per submodule saying what lives there and when to load it.
- **FR-008**: The `STAGES` pipeline tuple MUST live in exactly one module, in its current order,
  with a comment at that point stating that the order is the design and is shared with the skill's
  DRAW ORDER map.
- **FR-009**: `test_hamletgen.py` MUST become a `test_hamletgen/` package whose modules mirror the
  source submodules, with no test deleted, skipped, or changed in substance.
- **FR-010**: The full diagram test suite, the `check_village` gate on all hamlet maps, and the
  `pool/regressions/` negative-fixture corpus MUST pass unchanged (the negative fixtures must still
  FAIL their checks, proving the checks kept their teeth).
- **FR-011**: Existing comments and docstrings MUST move with their code intact - in particular the
  32 researched constants each carry their "why" (the project's record-the-why rule) and the head
  docstring's four doctrine paragraphs (WHAT THIS IS / THE ORDER IS THE DESIGN / DERIVE NEVER PIN /
  THE CHECKS ARE THE ORACLE). None of this may be lost or trimmed in the move.
- **FR-012**: A documented command MUST continue to roll a hamlet and a cohort from the command line;
  docs that name the old `python3 hamletgen.py ...` form MUST be updated to the working form.
- **FR-013**: Coverage MUST remain at the pre-split level with no coverage regression introduced by
  the extraction, and `mypy --strict` / `ruff` configuration MUST be updated to point at the package.
- **FR-014**: Docs that reference the FILE `hamletgen.py` (the skill `CLAUDE.md`, `SKILL.md`,
  `hamletgen.md`, `migration-plan.md`) MUST be updated to the package; prose references to
  importable paths (`hamletgen.seat_cluster`) stay valid and unchanged, and prior `specs/NNN`
  artifacts stay verbatim as historical record.

### Key Entities

- **Submodule**: one file in the package, holding one stage or one shared concern, under the
  ~1,000-line bar, named for what it holds.
- **Consumed surface**: the censused set of names any consumer reaches from `hamletgen` today (47
  attribute names plus the two direct-import names), which the package must reproduce identically.
- **Byte-identity baseline**: the set of manifests produced by the pre-split monolith at fixed
  seeds; the oracle for every subsequent step.
- **Sub-stage function**: a named function extracted from an oversized stage, taking its inputs as
  parameters and returning its outputs, preserving code order and RNG draw order exactly.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every regenerated manifest (four live hamlets + the fixed-seed cohort) is byte-identical
  to the pre-split baseline - zero differing bytes.
- **SC-002**: Zero consumer files are modified: the change touches only the new package, the deleted
  monolith, the test package, the tooling config, the new guard test, docs, and `specs/`.
- **SC-003**: Every file in `hamletgen/` and `test_hamletgen/` is under ~1,000 raw lines, and no
  function exceeds ~150 lines without an inline justification.
- **SC-004**: A reader given any one of the named concerns can identify the single file holding it
  from `hamletgen/CLAUDE.md` alone, without opening a source file.
- **SC-005**: The full test suite, the `make done` gate (ruff + format + mypy --strict + pytest +
  coverage) and the regression corpus are green, with the same test count as before the split.
- **SC-006**: The guard test on the consumed surface has been observed to FAIL against a
  deliberately broken re-export before being trusted.

## Assumptions

- The partition follows the file's own STAGE banner comments, which already mark the seams the
  author intended; the exact module list is settled in planning, not here.
- The four live hamlets plus a fixed-seed cohort are a sufficient oracle: `hamletgen` has no other
  consumers that produce artifacts, and the generator is fully deterministic per seed.
- The committed pool manifests are NOT a valid baseline on their own (feature 110's research R3
  found the pool is frozen against re-rolls); the baseline is captured from a scratch copy of the
  pre-split tree, the same method 110 used.
- No behavior change of any kind is in scope. Known open items in `future-work.md` that touch this
  module (the well minimax objective, the envelope-trim vertex dedup, woodland crown records) are
  explicitly NOT addressed here - they stay open, so the byte-identity oracle stays valid.
- `cohort_audit.py` is treated as a consumer whose surface must be preserved, not as a file to
  update.
- This feature supersedes nothing; it applies the same clause-13/14 method that features 024, 025,
  027 and 110 established, to the last remaining hand-maintained monolith in the skill.
