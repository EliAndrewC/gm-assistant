# Implementation Plan: waterfields.py -> waterfields/ Package Split

**Branch**: `110-waterfields-package` | **Date**: 2026-08-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/110-waterfields-package/spec.md`

## Summary

Split the 2,689-line `waterfields.py` water-first field engine into a six-module `waterfields/`
package with a derived star-import `__init__.py` (clause 13 + clause 14, following the
check_village/027 exemplars), then decompose the three mega-functions (`build_comb` 493 lines,
`build_polder` 456, `_carve` 435) into named stage functions. Behavior-preservation is proven by
byte-identical manifests from a pre-split scratch baseline (the frozen pool means committed
artifacts are not a valid oracle - research.md R3), plus the full `make done` gate and the
scripted-map check battery. Zero consumer changes; a guard test pins the consumed surface.

## Technical Context

**Language/Version**: Python 3.14 (project pin)

**Primary Dependencies**: stdlib only inside the module (`math`, `random`, typing); consumers
are the diagram skill's engines (`hamletgen`, `settlement/`), pool gens, and `check_village`

**Storage**: N/A (pure functions returning plain data; SVG drawn by callers)

**Testing**: pytest (+xdist) via `make done`; gate = ruff + format + mypy --strict + tests +
per-module 100% coverage; scratch-tree byte-identity harness (this feature's oracle)

**Target Platform**: dev container, Linux

**Project Type**: library refactor inside the diagram skill

**Performance Goals**: no runtime change expected or required (import indirection is
negligible); gate wall-time unchanged

**Constraints**: byte-identical output (manifests + SVG) at every step; zero consumer edits;
every package file < 1,000 raw lines; functions <= ~150 lines post-decomposition

**Scale/Scope**: one 2,689-line module -> 6 submodules + `__init__` + CLAUDE.md; 3 mega-function
decompositions; 1 new guard test; 2 config lines (mypy files entry, ruff per-file-ignores)

## Constitution Check

- **I. Accessibility-First Viewports**: N/A - no UI.
- **II. Bold, Intentional Design**: N/A - no new UI surfaces.
- **III. Pool Data Conventions**: N/A - no generated content added or modified (byte-identity
  is the feature's core requirement).
- **IV. One Canonical Home for GM Source**: N/A - no SOURCE blocks involved.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: PASS - no task touches SOURCE-marked
  content anywhere.
- **VI. Verify Before Reporting Done**: PASS - verification per task: scratch-tree
  byte-identity diff after the move and after each decomposition; full `make done` (whole test
  files, never `-k`); guard test proven to fire before trusting it; final gate backgrounded and
  read from its log.
- **VII. De-Localized Generation by Default**: N/A - no pool content generated.
- **VIII. Direct Voice Over Framing Distance**: N/A - no in-world prose.
- **IX. Setting Integration**: N/A - no setting content; no new named figures.
- **X. Python Discipline (NON-NEGOTIABLE)**: PASS - this feature IS a clause-13/14 execution.
  ruff + format + mypy --strict (waterfields is already fully strict; the `files` entry flips
  `waterfields.py` -> `waterfields`) + pytest with the per-module 100% gate. Coverage scope
  unchanged (waterfields stays unmeasured - recorded decision, research.md R4). Clause 12 note:
  this feature deliberately SUPERSEDES 024-R9's "do not split the engine builders" disposition,
  on explicit GM request (2026-08-16); recorded in research.md R5. TDD shape: the guard test is
  written and shown to fire (red) against a deliberately broken re-export before being trusted;
  the byte-identity oracle is captured before any change.
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: N/A - the feature changes nothing
  the generator asserts about the world; byte-identical output is the definition of "no
  assertion changed." (Any byte difference is a gate failure, not a new assertion.)

## Project Structure

### Documentation (this feature)

```text
specs/110-waterfields-package/
├── plan.md              # This file
├── research.md          # Phase 0 - partition, surface, oracle, config, method
├── data-model.md        # Phase 1 - package layout, import DAG, census, baseline
├── quickstart.md        # Phase 1 - verification commands
├── contracts/
│   └── package-surface.md   # the import-surface contract
└── tasks.md             # Phase 2 (/speckit-tasks - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
.claude/skills/diagram/
├── waterfields/                 # NEW package (replaces waterfields.py, deleted same change)
│   ├── __init__.py              # derived surface: 6 star imports + aliased underscore block
│   ├── CLAUDE.md                # "look here when" index
│   ├── frame.py                 # layer-0 frame math + march constants
│   ├── palette.py               # layer-0 colors, paddy grain, organic parcels
│   ├── banks.py                 # layer-1 bank clearance + channel joints
│   ├── comb.py                  # build_comb (+ stages) + _fill_wedges
│   ├── carve.py                 # _carve (+ stages) + _dry_fields + _bund_beans
│   └── polder.py                # build_polder (+ stages) + terraces + ribbon
├── test_waterfields_surface.py  # NEW guard test (census + identity, modeled on
│                                #   test_check_village_surface.py)
├── pyproject.toml               # mypy files entry + ruff per-file-ignores line
└── CLAUDE.md                    # LIVE-engine line: waterfields.py -> waterfields/ pointer
```

**Structure Decision**: package-of-subfiles split per the check_village exemplar; partition
follows the measured call graph (research.md R1) so the import DAG is cycle-free by
construction. Consumers untouched.

## Complexity Tracking

No constitution violations to justify. The one superseded prior disposition (024-R9 clause-12
exemption for the engine builders) is a GM-directed reversal, recorded in research.md R5.
