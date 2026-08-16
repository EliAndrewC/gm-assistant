# Implementation Plan: Human-Scale Files

**Branch**: `024-human-scale-files` | **Date**: 2026-08-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/024-human-scale-files/spec.md`

## Summary

Add the file-size sibling of Principle X clause 12 (files past ~1,000 raw lines prompt the
package-of-subfiles question; target shape = directory-module + CLAUDE.md index; motivation =
token economy) and apply it to the largest offender: `check_village.py` (35,603 lines) becomes the
`check_village/` package. In the same feature, the nine multi-check gate segments over 300 raw
lines (led by `_seg_0285__wells_clear_of_shrine_and_torii`, 1,351 lines / 427 statements / 42
check names) are split into per-check segments with the feature-022/023 method, and verdict
identity is proven by the 022 oracle sweep over all 797 regression fixtures + pool manifests.
Everything is scripted AST surgery - the 35k-line file is never loaded into a context window,
which is itself a demonstration of the rule's motivation.

## Technical Context

**Language/Version**: Python 3.14 (diagram skill pyproject pin)

**Primary Dependencies**: stdlib `ast` for the split tooling; existing diagram-skill deps
unchanged. Oracle tooling: `specs/022-gate-check-registry/oracle_sweep.py` reused as-is
(it imports `check_village` by name, which keeps resolving after the package split).

**Storage**: N/A (source files; JSON oracle baselines in the feature dir)

**Testing**: pytest via the diagram skill's `make done` (ruff + format + mypy --strict + pytest
+ 100% coverage on pure logic); oracle capture/compare/targeted sweeps for verdict identity;
registry-pin fixture `test_fixtures/gate_check_names.json` regenerated for the new segment names.

**Target Platform**: dev container, Linux

**Project Type**: refactor of an existing pure-logic validator package + governance doc amendment

**Performance Goals**: no regression in gate wall time; targeted regression replay stays at its
~58 s serial order of magnitude.

**Constraints**: byte-identical verbose gate output per fixture (oracle-hash contract);
`gate(M, only=...)` closure semantics unchanged; registry order preserved exactly; no file in the
new package over ~1,000 lines without an inline justification (registry data file justifies).

**Scale/Scope**: 35,603 lines, 1,042 module-level defs (972 segments), 972 registry rows,
797 regression fixtures + pool manifests as the identity corpus.

## Constitution Check

- **I. Accessibility-First Viewports**: N/A - no UI.
- **II. Bold, Intentional Design**: N/A - no UI.
- **III. Pool Data Conventions**: N/A - no pool content added or modified.
- **IV. One Canonical Home for GM Source**: N/A - no SOURCE blocks touched.
- **V. Protecting the GM's Writing**: PASS - no task touches SOURCE markers; the constitution
  amendment adds a new clause outside any GM-source content.
- **VI. Verify Before Reporting Done**: PASS - verification is the heart of the feature: oracle
  capture/compare/targeted at each stage, full diagram `make done`, registry-pin fixture update,
  and a final grep sweep for stale `check_village.py` references. Each task lists its check.
- **VII. De-Localized Generation**: N/A - no generated in-world content.
- **VIII. Direct Voice**: N/A - no in-world prose (package CLAUDE.md is dev doc).
- **IX. Setting Integration**: N/A - no setting content.
- **X. Python Discipline**: PASS - ruff/format/mypy --strict/pytest/100%-coverage all reassert
  via `make done`; moves are verbatim (no behavior change), so TDD red-green applies only to the
  split tooling's own assertions (identity checks ARE the tests). Clause 12: the feature
  REDUCES function sizes; the registry module exceeds the file threshold as ordered data and
  carries the inline justification FR-010 requires.
- **XI. Japanese Authenticity**: N/A - no kanji surfaces.
- **XII. Historical Grounding Bookends**: N/A - the feature changes no assertion about the world;
  the oracle identity proof is precisely the demonstration that every rendered artifact's
  validation is unchanged. No generator output differs.

No DEFERRED gates; Complexity Tracking not needed.

## Project Structure

### Documentation (this feature)

```text
specs/024-human-scale-files/
├── plan.md              # This file
├── research.md          # Phase 0: decisions, segment census, dispositions
├── data-model.md        # Phase 1: package layout, tooling data shapes
├── quickstart.md        # Phase 1: the command sequence + verification steps
├── contracts/
│   └── check_village-api.md   # public import surface + CLI contract
├── split_oversized.py   # one-shot: per-check split of the 9 fat segments (adapted from 023)
├── split_package.py     # one-shot: the monolith -> package mover + import generator
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
.claude/skills/diagram/check_village/          # NEW package, replaces check_village.py
├── CLAUDE.md            # index: every subfile + "look here when" line
├── __init__.py          # generated explicit re-export of every module-level name
├── __main__.py          # CLI: python3 -m check_village <manifest.json>
├── common_*.py          # the pre-segment region (lines 1-2630) as ~3 contiguous files
│                        #   (geometry/spatial, overlap+label policy tables, capacity+seg base)
├── segments_NN_*.py     # ~10-14 thematic contiguous segment files (registry order preserved)
├── registry.py          # _GateSeg, GATE_SEGMENTS (972+ rows), META_CHECKS, _SEG_DEPS
│                        #   > 1,000 lines WITH inline justification: ordered data, not logic
└── driver.py            # gate(), twin_* helpers, main()

.specify/memory/constitution.md                # clause 13 + version 1.6.0 + sync report
.specify/templates/plan-template.md            # Principle X gate text gains file-scale sentence
CLAUDE.md                                      # one-line operational mirror (Development Workflow)
.claude/skills/diagram/CLAUDE.md               # registry-section pointers updated to the package
.claude/skills/diagram/test_fixtures/gate_check_names.json   # regenerated for new segment names
```

**Structure Decision**: single-package refactor in place; exact `common_*`/`segments_*` file
names are decided by the split script's census (contiguous ranges, theme named from dominant
check-name keywords) and recorded in the package CLAUDE.md - see research.md R2/R3.

## Phase ordering (why this sequence)

1. **Docs first** (constitution clause 13, template gate text, CLAUDE.md line): the rule is the
   durable deliverable and nothing downstream depends on it.
2. **Oracle baseline** captured against the untouched monolith.
3. **Segment splits inside the monolith** (adapted 023 tooling targets the single-file format) -
   compare + targeted sweeps prove identity; registry-pin fixture updated.
4. **Package split** (pure verbatim moves + generated imports) - compare + targeted again.
5. **Callers/docs/CLI + package CLAUDE.md**, final full gate + fixture sweep.

Splitting segments BEFORE moving files means the 023-style tooling runs against the format it was
built for, and each stage's oracle diff isolates its own class of defect.
