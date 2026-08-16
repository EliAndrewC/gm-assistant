# Feature Specification: waterfields.py -> waterfields/ Package Split

**Feature Branch**: `110-waterfields-package`

**Created**: 2026-08-16

**Status**: Implemented (2026-08-16)

**Input**: User description: "Refactor .claude/skills/diagram/waterfields.py (2,689 lines) into a waterfields/ package of focused submodules with its own CLAUDE.md index, following the check_village/ exemplar and constitution Principle X clause 13 (files at human scale, ~1,000-line bar). Two documented motivations: (1) engineering - split the three mega-functions (build_comb ~495 lines, build_polder ~458, _carve ~437, together over half the file) into smaller focused functions; (2) tokens - a package with a CLAUDE.md index lets a session load only the comb, polder, or bank-clearance module it needs instead of the whole file. The refactor must be behavior-preserving: verified via the manifest-based check_village gate and the pool/regressions/ negative-fixture corpus, with zero consumer changes."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Behavior-preserving package split (Priority: P1)

A session working on the water-first field engine currently loads all 2,689 lines of `waterfields.py` to use one part of it. After this feature, `waterfields` is a package of focused submodules, each under the ~1,000-line clause-13 bar, and every existing consumer (16 pool `.gen.py` scripts, `hamletgen.py`, `settlement/fields.py`, `settlement/houses.py`, 3 `check_village` segment files, `test_villages.py`, `test_hamletgen.py`) keeps working with **zero changes** - `from waterfields import build_comb` and `import waterfields as wf` resolve exactly as before, including the underscore names consumers reach for (`_RICE_GREEN`, `wf._Frame`, `wf._miter_normals`).

**Why this priority**: This is the feature. Without a verified behavior-preserving split, nothing else matters; a split that changes rendered output or breaks a consumer is a regression, not a refactor.

**Independent Test**: Regenerate every map that calls into waterfields and diff its manifest against the pre-split manifest byte-for-byte (deterministic seeds make this exact). Run the full existing test suite and the check_village gate with no test edits beyond import-path mechanics (none expected).

**Acceptance Scenarios**:

1. **Given** the split is complete, **When** every pool map that consumes waterfields is regenerated, **Then** each manifest is identical to the one produced by the pre-split monolith (same seed, same output).
2. **Given** the split is complete, **When** the full diagram test suite and check_village gate run, **Then** they pass with zero consumer-file modifications.
3. **Given** the split is complete, **When** any existing import form is exercised (`from waterfields import X` for every public and underscore name currently imported, `import waterfields as wf` attribute access), **Then** all resolve to the same objects.

---

### User Story 2 - Mega-functions decomposed (Priority: P2)

A maintainer opening `build_comb` (~495 lines), `build_polder` (~458), or `_carve` (~437) today faces over half the file in three functions. After this feature, each is decomposed into named stage functions whose names describe the pipeline (the way the check_village split named its segments), so a reader can follow the algorithm top-down and a future change can target one stage.

**Why this priority**: The engineering motivation. Valuable, but only safe on top of the P1 verification harness - decomposition without the manifest-diff net is where behavior drift sneaks in.

**Independent Test**: After decomposition, no function in the package exceeds ~150 lines; manifests still byte-identical; coverage still 100% on pure logic.

**Acceptance Scenarios**:

1. **Given** the decomposition is complete, **When** function lengths are measured, **Then** no function exceeds ~150 lines and each extracted stage has a name describing what it does.
2. **Given** the decomposition is complete, **When** all manifests are regenerated, **Then** they remain byte-identical to the pre-split baseline.

---

### User Story 3 - Token-scale package index (Priority: P3)

A session that needs only the bank-clearance helpers (or only the polder builder) reads the package's `CLAUDE.md` index and loads just that submodule, instead of the whole monolith. The index says which file holds what, in the style of `check_village/CLAUDE.md`.

**Why this priority**: The token motivation. It falls out of the split almost for free but is only useful once the split exists.

**Independent Test**: Every submodule is under the ~1,000-line bar; `CLAUDE.md` names each submodule with a one-line "what lives here"; a named concern (comb, polder, terraces, ribbon, bank clearance, bund beans, dry fields, shared frame math) maps to exactly one submodule.

**Acceptance Scenarios**:

1. **Given** the package exists, **When** a reader consults `waterfields/CLAUDE.md`, **Then** each submodule is listed with its contents and the reader can identify the single file for a given concern.
2. **Given** the package exists, **When** file sizes are measured, **Then** every submodule (including `__init__.py`) is under ~1,000 raw lines.

---

### Edge Cases

- **Underscore names imported from outside**: `settlement/fields.py` imports `_RICE_GREEN`; `test_hamletgen.py` uses `wf._Frame` and `wf._miter_normals`. A bare star-import surface drops underscore names, so the re-export surface must carry them explicitly (or via submodule `__all__`). A guard test must prove every name any consumer imports today resolves from the package.
- **Module-level constant identity**: consumers compare against constants (`AZE`, `BANK_MARGIN`); re-export must preserve object identity, not copies that could drift.
- **Import cycles**: submodules share helpers (`_Frame`, `_seg_x`, geometry predicates); the split must order modules so no cycle forms.
- **`sys.path` consumers**: pool `.gen.py` scripts import `waterfields` by adding the diagram dir to `sys.path`; a package directory at the same path satisfies this unchanged, but the old `waterfields.py` must be deleted in the same change so a stale monolith never shadows the package.
- **Doc references to `waterfields.py`**: prose in check messages and docs refers to `waterfields._bund_beans` etc.; those references stay valid (same importable path) but any doc naming the *file* `waterfields.py` needs its path updated.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `waterfields` MUST become a package of focused submodules; the monolithic `waterfields.py` MUST be removed in the same change.
- **FR-002**: Every existing consumer import MUST keep working with zero consumer-file changes, including the underscore names in use today (`_RICE_GREEN`, `_Frame`, `_miter_normals`) and attribute access via `import waterfields as wf`.
- **FR-003**: The package `__init__.py` MUST be a derived re-export surface per constitution clause 14 (star imports plus explicit underscore re-exports), not a maintained roster; a guard test MUST enumerate every name currently imported by any consumer and prove each resolves.
- **FR-004**: Regenerating every waterfields-consuming map in the pool MUST produce manifests byte-identical to those produced by the pre-split monolith (same seeds). The baseline MUST be captured before the split begins.
- **FR-005**: The three mega-functions (`build_comb`, `build_polder`, `_carve`) MUST be decomposed into named stage functions; no function in the package may exceed ~150 lines.
- **FR-006**: Every file in the package, `__init__.py` included, MUST be under ~1,000 raw lines (constitution clause 13).
- **FR-007**: The package MUST have a `CLAUDE.md` index in the check_village style: one line per submodule saying what lives there and when to load it.
- **FR-008**: The full diagram test suite, the check_village gate on all pool maps, and the pool/regressions/ negative-fixture corpus MUST pass unchanged (the negative fixtures must still FAIL their checks - proving the checks kept their teeth).
- **FR-009**: Existing comments and docstrings MUST move with their code intact; the "record the why" content (magic numbers, historical grounding) must not be lost or trimmed in the move.
- **FR-010**: Coverage MUST remain at the pre-split level (100% on pure logic per project standard) with no coverage regression introduced by the extraction.

### Key Entities

- **waterfields package**: the new directory; submodules partitioned by concern - shared geometry/frame primitives, palette + parcel helpers, bank-clearance mechanics, the comb builder pipeline, the polder builder pipeline, terraces/ribbon builders, dry fields + bund beans.
- **Re-export surface (`__init__.py`)**: derived star-import surface plus explicit underscore re-exports; consumers' single import target.
- **Manifest baseline**: pre-split regeneration record of every consuming map, the byte-identity oracle for the whole feature.
- **Guard test**: enumerated consumer-name resolution test; the safety property that replaces a maintained roster.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of regenerated consumer-map manifests are byte-identical to the pre-split baseline.
- **SC-002**: Zero lines changed in any consumer file (pool scripts, hamletgen, settlement/, check_village/, tests) - measured by `git diff --stat` scope.
- **SC-003**: Largest file in the package is under 1,000 raw lines; largest function under ~150 lines (down from 495).
- **SC-004**: A session needing one concern (e.g. bank clearance) can load a single submodule identified from the index, at a fraction of the monolith's 2,689 lines.
- **SC-005**: Full test suite + check_village gate + regression corpus green with no test deletions or weakenings.

## Assumptions

- Generation is deterministic given a seed, so manifest byte-identity is a valid oracle (established practice: the check gate runs on manifests, not pixels).
- The check_village/ package (feature 024) and the 027 star-import method are the exemplars to follow for structure and re-export style respectively; no new convention is being invented.
- Decomposing mega-functions into same-module stage functions preserves behavior when extraction is mechanical (no logic edits); byte-identity of manifests is the check on that claim.
- Existing test files are consumers, not part of the refactor surface; they change only if they would fail for import-mechanics reasons (none expected).
- The ~150-line function bar is a working target derived from the engineering motivation, not a constitution number; modest overshoot on a genuinely atomic stage is acceptable with an inline justification.
