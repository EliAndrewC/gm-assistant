# Implementation Plan: Collapse check_village/__init__.py to a star-import surface

**Branch**: `main` (no feature branches; `SPECIFY_FEATURE=027-init-star-imports`) | **Date**: 2026-08-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/027-init-star-imports/spec.md`

## Summary

Replace the 3,148-line `check_village/__init__.py` - which is an explicit import roster (lines 1-~1595) plus a duplicate `__all__` roster (lines 1596-3148) - with a ≤150-line surface: one `from .<submodule> import *` per submodule, a small aliased explicit block for consumed underscore names and consumed external (`settlement`/`waterfields`) names, and an updated docstring recording the mechanism and why. Research (research.md) established that star imports satisfy mypy strict's `no_implicit_reexport` without `__all__`, that zero public-name clashes exist across the 15 submodules, and that the only surface anything consumes is 42 names. A permanent guard test replaces the safety the explicit rosters provided.

## Technical Context

**Language/Version**: Python 3.14 (project pin)

**Primary Dependencies**: mypy 2.3.0 (strict), ruff (E,F,I,UP,B,SIM; line-length 200), pytest + coverage per the skill Makefile

**Storage**: N/A (source-only refactor)

**Testing**: `make done` in `.claude/skills/diagram/` (ruff check + format check + mypy + pytest with per-module coverage enforcement); new guard/surface test added to the suite

**Target Platform**: the dev container (Linux)

**Project Type**: library package internal to the /diagram skill

**Performance Goals**: mypy baseline stays ~3.6s; import time of `check_village` unchanged (same modules load - only the roster prose disappears)

**Constraints**: FR-007 - changes confined to `check_village/__init__.py`, test files, lint/type config, and the package's CLAUDE.md index line for `__init__.py`. No renames in `segments_*`/`registry.py`/`driver.py`; no consumer call-site edits.

**Scale/Scope**: one file 3,148 → ≤150 lines; one new test file; one pyproject line

## Constitution Check

- **I. Accessibility-First Viewports**: N/A - no UI touched.
- **II. Bold, Intentional Design**: N/A - no UI surfaces.
- **III. Pool Data Conventions**: N/A - no generated pool content.
- **IV. One Canonical Home for GM Source**: N/A - no SOURCE blocks involved.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: PASS - no GM prose anywhere near the diff.
- **VI. Verify Before Reporting Done**: PASS - verification steps per task listed below; the full gate runs once at the end (iteration-loop rule: iterate on the one artifact, full bed once); the guard test is demonstrated RED on a synthetic clash before being trusted (check-before-fix).
- **VII. De-Localized Generation by Default**: N/A - no generated content.
- **VIII. Direct Voice Over Framing Distance**: N/A - no prose output (docstring follows normal engineering register).
- **IX. Setting Integration**: N/A.
- **X. Python Discipline (NON-NEGOTIABLE)**: PASS - mypy strict retained with no relaxation (research shows none needed); ruff per-file-ignores gain `F403` scoped to this one `__init__` with a why-comment; coverage bars unchanged (`__init__` import lines all execute at import time); clause 13 is the feature's motivation - the file returns to human scale.
- **XI. Japanese Authenticity**: N/A - no kanji/romaji content.
- **XII. Historical Grounding Bookends**: N/A - no historical research; the record-the-why obligation is satisfied by the new docstring + research.md (why `__all__` could be dropped, why star imports are safe here).

No DEFERRED gates; no Complexity Tracking entries needed. Re-checked after Phase 1 design: unchanged.

## Phase 0: Research

Complete - see [research.md](research.md). All four items (mypy re-export mechanism, clash census, ruff needs, consumed-surface verification) resolved empirically; no NEEDS CLARIFICATION remain.

## Phase 1: Design

- **Data model**: [data-model.md](data-model.md) - the three name populations (star-provided public surface, aliased explicit block, dropped roster) and the guard/surface test's contract.
- **Contracts**: the package surface IS the contract; documented in data-model.md rather than a separate contracts/ dir (internal library, no external interface).
- **Quickstart**: [quickstart.md](quickstart.md) - how to verify the refactor and how to extend the package after it.
- **Agent context**: `.specify/feature.json` already points at this feature dir; CLAUDE.md carries no SPECKIT marker block (project convention - features are found via `specs/` + git log).

## Phase 2: Task planning approach

Tasks follow check-before-fix: census re-verification and the guard/surface test land BEFORE the rewrite (test proven RED on a synthetic clash, and the surface test pinned against the CURRENT file so the rewrite must preserve the 42 names to go green). Then the rewrite, lint config, package CLAUDE.md index update, and one full gate run at the end - backgrounded, acted on via notification per the iteration-loop rules.
