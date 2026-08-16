# Feature Specification: Collapse check_village/__init__.py to a star-import surface

**Feature Branch**: `main` (session-clone workflow - see CLAUDE.md; no feature branches, `SPECIFY_FEATURE=027-init-star-imports`)

**Created**: 2026-08-16

**Status**: Implemented (2026-08-16)

**Input**: User description: "Collapse check_village/__init__.py from a 3,148-line explicit re-export monolith to a small star-import surface... [GM 2026-08-16, full text in conversation]. The pattern is counterproductive to our goals: the file is 95% a re-export service and causes the very token problem the clause-13 splits exist to solve."

## Context

Feature 024 split the `check_village.py` monolith into a package, and its `__init__.py` was written to restore the legacy `import check_village; check_village.<name>` surface **verbatim** - every name the monolith ever bound, imported explicitly. That decision was safe but maximal: the file is 3,148 lines, of which ~3,000 are import lists, including **1,414 underscore-prefixed segment names** (`_seg_NNNN_MMM__*`).

Session recon (2026-08-16) established the actual demand on that surface:

- `check_village._seg_*` has **zero consumers** anywhere in the repo (greps over `check_village\._seg`, `cv\._seg`, `getattr(check_village`, aliased imports).
- The full consumed surface - every `check_village.<name>` attribute access plus every `from check_village import ...` - is **42 names**, only six of them underscore-prefixed: `_LABEL_EXEMPT`, `_LABEL_GROUP`, `_MATRIX_OUTSTANDING`, `_OVERLAP_EXEMPT`, `_OVERLAP_STRUCTS`, `_ward_interior`.
- No test pins the package's full attribute surface (no `dir(check_village)` / `__all__` assertions exist).

### Resolved decision: star imports, no de-underscore rename

The GM's initial proposal was to remove the underscore prefixes from re-exported names so plain `from .submodule import *` picks them up. Recon shows that rename is unnecessary: since nothing consumes the underscore re-exports (except the six above), they can simply be **dropped** from the package surface. This avoids renaming ~1,400 machine-generated segment identifiers across the segment files, `registry.py` (its own deferred refactor - do not touch), and the segmentization tooling that generated them. The GM's goal - the 3,000-line token sink gone - is met with strictly less churn. (Recorded per the stop-and-ask calculus: cheap-to-adjust call made in-session, reported in the completion summary.)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A session loads the package surface cheaply (Priority: P1)

A future Claude session (or the GM) opens `check_village/__init__.py` to understand what the package exposes and how it is stitched together. Today that read costs ~3,150 lines to learn ~40 useful facts; afterwards it should cost roughly a screenful: the docstring, the external re-exports, one star-import line per submodule, and a short explicit block for the consumed underscore names.

**Why this priority**: This is the feature's entire motivation - the file is the worst remaining instance of the problem constitution clause 13 (human-scale files) exists to solve, and it is loaded often because it is the package's front door.

**Independent Test**: Open the file; its length is a few dozen to ~150 lines and every line carries information (no generated name rosters).

**Acceptance Scenarios**:

1. **Given** the refactored package, **When** `wc -l check_village/__init__.py` runs, **Then** the count is at most 150 lines.
2. **Given** the refactored package, **When** a reader scans the file, **Then** the mechanism (star imports + explicit underscore block + external re-exports) is fully visible without scrolling through generated identifiers.

---

### User Story 2 - Every existing consumer keeps working unchanged (Priority: P1)

All code that reaches through the package namespace - `check_village.gate`, `from check_village import QUARTER_DENSITY_CEIL, ...`, the six underscore names, the `__main__` CLI - continues to work with no edits at call sites.

**Why this priority**: The re-export surface is the package's public API; breaking it breaks the gate, the cohort tooling, and the test bed. A refactor that required touching consumers would also be a bigger diff than the file it shrinks.

**Independent Test**: The full diagram gate (`make done` in the skill dir: ruff + format + mypy --strict + pytest at the Makefile's coverage bars) passes with no consumer file modified.

**Acceptance Scenarios**:

1. **Given** the refactored package, **When** the full gate runs, **Then** it is green with zero changes outside `check_village/__init__.py`, its tests, and lint configuration.
2. **Given** the 42-name consumed surface recorded in this spec, **When** each name is resolved as `check_village.<name>`, **Then** each resolves to the same object as before the refactor.

---

### User Story 3 - Silent star-import shadowing is guarded forever (Priority: P2)

With explicit imports, a duplicate public name across submodules is at least visible in the import lists; with star imports, the last module's binding silently wins. A permanent guard test asserts that no two star-imported submodules export the same public name bound to different objects, so a future submodule addition cannot silently shadow an existing check or helper.

**Why this priority**: The one real safety property the explicit lists provided must survive their removal - but it can be provided by a test instead of by 3,000 lines.

**Independent Test**: The guard test exists, runs in the normal suite, and fails when pointed at a synthetic clash (verified once during development per the check-before-fix discipline).

**Acceptance Scenarios**:

1. **Given** the current submodules, **When** the guard test runs, **Then** it passes.
2. **Given** a hypothetical submodule pair exporting the same public name with different objects, **When** the guard logic evaluates it, **Then** it reports the clash and the offending modules.

---

### Edge Cases

- **mypy strict re-export semantics**: `--strict` implies `no_implicit_reexport`; the current file passes with plain (non-aliased, no-`__all__`) imports. Research must establish *why* it currently passes and preserve that property under star imports - without weakening strictness for any module other than, at most, the `__init__` whose sole purpose is re-export.
- **Star-import namespace pollution**: `from .segments_X import *` also binds the submodule's own imports (`math`, `json`, names imported from `settlement`, ...) into `check_village`. This is acceptable pollution (nothing collides by construction - the guard test proves it), and it must not be "fixed" by reintroducing `__all__` rosters in every submodule, which would just move the 3,000 lines rather than delete them.
- **Duplicate-def guard interaction**: `scripts/check-duplicate-defs.py` runs at every push; the refactor must not trip it (it screens top-level defs per file, not imports, so no interaction is expected - verify, not assume).
- **Names consumed but defined outside the package** (`settlement`, `waterfields` re-exports such as `point_in_poly`, `edge_gap`): the external import block stays explicit - star-importing another top-level module's surface would couple the package to everything that module ever adds.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `check_village/__init__.py` MUST be at most 150 lines while preserving its docstring's substance (updated to describe the new mechanism and why - record-the-why applies).
- **FR-002**: The package MUST continue to expose every name on the consumed-surface list in this spec (42 names, including the six underscore names) as `check_village.<name>`, bound to the same objects as before.
- **FR-003**: The public (non-underscore) surface MUST be provided via `from .<submodule> import *` statements; the six consumed underscore names via one small explicit import block; the external `settlement` / `waterfields` re-exports via the existing explicit block (pruned or kept as-is, but never star-imported).
- **FR-004**: The ~1,400 unconsumed underscore re-exports MUST be dropped from the package surface. Dropping them is a deliberate surface change, not an accident - the spec records that greps found zero consumers.
- **FR-005**: A guard test MUST assert that no two star-imported submodules export the same public name bound to different objects, naming the clashing modules on failure, and MUST have been demonstrated to fire on a synthetic clash during development.
- **FR-006**: The full diagram gate (ruff check, ruff format --check, mypy --strict, pytest with the Makefile's coverage enforcement) MUST pass; lint configuration MAY gain `F403` (and keep `F401`) in the per-file-ignores for `check_village/__init__.py` only, with a comment saying why.
- **FR-007**: No file outside `check_village/__init__.py`, test files, and lint/type configuration may change. In particular `registry.py` and the `segments_*` files are untouched (no renames), and no consumer call site changes.
- **FR-008**: If mypy's re-export strictness requires a module-scoped accommodation, it MUST be scoped to `check_village.__init__` at most, carry a why-comment, and MUST NOT relax any other strictness flag.

### Key Entities

- **The consumed surface (42 names)**: `BUDGET_TOL_OVER`, `BUDGET_TOL_UNDER`, `GATE_SEGMENTS`, `HOUSEHOLD`, `META_CHECKS`, `OVERLAP_CLASS`, `RESERVE_CAP_FRAC`, `TWIN_AXES`, `_LABEL_EXEMPT`, `_LABEL_GROUP`, `_MATRIX_OUTSTANDING`, `_OVERLAP_EXEMPT`, `_OVERLAP_STRUCTS`, `_ward_interior`, `city_capacity`, `clip_poly_rect`, `crop_relocatable_singletons`, `edge_gap`, `forest_reveal_x`, `gate`, `kiln_quarters`, `lane_near_misses`, `lane_ward_shortfalls`, `largest_empty_gap`, `main`, `matrix_extents`, `matrix_policy`, `matrix_violations`, `onmap_field_edge`, `point_in_poly`, `poly_area`, `poly_dist`, `poly_gap`, `rect_corners`, `seg_dist`, `seg_intersect`, `seg_to_rect_dist`, `sweep_hi`, `twin_axes`, `twin_diff_count`, `twin_report`, `water_setback`, plus the `__main__` CLI imports (`QUARTER_DENSITY_CEIL`, `QUARTER_DENSITY_FLOOR` - already counted above where overlapping).
- **The dropped surface**: every `_seg_NNNN_MMM__*` name and any other underscore name not on the consumed list.
- **The guard test**: a pure-logic test over the star-imported submodules' public namespaces.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `check_village/__init__.py` shrinks from 3,148 lines to at most 150 (a >95% reduction in the tokens a session pays to open the package's front door).
- **SC-002**: The full diagram gate passes with zero consumer-file changes.
- **SC-003**: All 42 consumed-surface names resolve identically before and after (pinned by test, not by eyeball).
- **SC-004**: The shadowing guard exists, passes, and was observed to fire on a synthetic clash exactly once during development.

## Assumptions

- The grep-established consumer inventory is complete: consumers of `check_village` live only in this repo (the skill's own modules, tests, and tools). Nothing outside the repo imports the package.
- The unconsumed underscore re-exports carry no intentional-but-dormant API promise; feature 024's "restore the surface verbatim" was conservatism during the split, not a contract. (The GM's 2026-08-16 direction to collapse the file supersedes it regardless.)
- `pool/` map generators do not import `check_village` internals beyond the consumed list (they are excluded from lint but still run; the gate plus `render-sync` regeneration would surface a break).
- The 42-name list was captured on 2026-08-16 against main at commit `2453ad7` plus feature-026; the implementing task re-verifies it before writing the final import block rather than trusting this snapshot blindly.
