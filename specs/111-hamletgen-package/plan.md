# Implementation Plan: hamletgen.py -> hamletgen/ Package Split

**Branch**: `111-hamletgen-package` | **Date**: 2026-08-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/111-hamletgen-package/spec.md`

## Summary

Split the 2,913-line `hamletgen.py` scripted-hamlet generator - the last hand-maintained monolith
in the diagram skill - into an eleven-module `hamletgen/` package with a derived star-import
`__init__.py` (clause 13 + clause 14, following the check_village/024/027 and waterfields/110
exemplars), then decompose the nine oversized stage functions into named sub-stage functions, and
mirror the split in `test_hamletgen/`. Behavior-preservation is proven by byte-identical manifests
against a pre-split scratch baseline covering the four live hamlets plus a 24-seed cohort, plus the
full `make done` gate. Zero consumer changes; a guard test pins the 49-name consumed surface and is
proven to fire before it is trusted.

## Technical Context

**Language/Version**: Python 3.14 (project pin)

**Primary Dependencies**: `settlement` (the placer/renderer), `waterfields` (the comb/polder field
engine), `check_village` (the in-process gate); stdlib `argparse`/`math`/`random`/`dataclasses`

**Storage**: N/A (pure functions plus a `Settlement` manifest written by the caller)

**Testing**: pytest (+xdist) via `make done`; gate = ruff + duplicate-def check + format check +
mypy --strict + tests + per-module 100% coverage; scratch-tree byte-identity harness (this
feature's oracle)

**Target Platform**: dev container, Linux

**Project Type**: library refactor inside the diagram skill

**Performance Goals**: no runtime change expected or required; a hamlet roll stays ~1 s and the
24-seed cohort stays seconds

**Constraints**: byte-identical manifests at every step; zero consumer edits; every package file
< 1,000 raw lines; functions <= ~150 lines post-decomposition; RNG draw order and float-op order
preserved exactly

**Scale/Scope**: one 2,913-line module -> 11 submodules + `__init__` + `__main__` + CLAUDE.md;
9 function decompositions; 1 test file -> 10-module test package; 1 new guard test; 2 config lines

## Constitution Check

- **I. Accessibility-First Viewports**: N/A - no UI.
- **II. Bold, Intentional Design**: N/A - no new UI surfaces.
- **III. Pool Data Conventions**: PASS by construction - no generated content is added or modified;
  byte-identity of the four pool hamlets is the feature's core requirement, and the pool files are
  never dirtied (verification runs in a scratch copy, quickstart section 2).
- **IV. One Canonical Home for GM Source**: N/A - no SOURCE blocks involved.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: PASS - no task touches SOURCE-marked content.
- **VI. Verify Before Reporting Done**: PASS - per-task verification: scratch-tree byte-identity
  diff after the move and after EACH function decomposition; full `make done` (whole test files,
  never `-k`); the guard test proven red before trusted; the final gate backgrounded and read from
  its log, never wrapped with a trailing `echo EXIT=$?`.
- **VII. De-Localized Generation by Default**: N/A - no pool content generated.
- **VIII. Direct Voice Over Framing Distance**: N/A - no in-world prose.
- **IX. Setting Integration**: N/A - no setting content; no new named figures.
- **X. Python Discipline (NON-NEGOTIABLE)**: PASS - this feature IS a clause-13/14 execution.
  ruff + `check-duplicate-defs.py` + format + mypy --strict (the `files` entry flips
  `hamletgen.py` -> `hamletgen`) + pytest with the per-module 100% gate (`hamletgen` is already a
  measured module at 100%; the coverage `source` entry needs no edit - a package name resolves the
  same way, research R4). Clause 12: the nine oversized functions are the US2 target. Clause 13:
  the file split. Clause 14: the `__init__` is derived (stars + aliased underscore block), not a
  roster. TDD shape: the guard test is shown to FAIL against a deliberately broken re-export before
  being trusted; the byte-identity oracle is captured before any change.
- **XI. Japanese Authenticity**: N/A - no kanji surfaces; existing names move verbatim.
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: PASS - the feature changes nothing the
  generator asserts about the world; byte-identical output IS the definition of "no assertion
  changed". The 32 researched constants keep their recorded "why" comments verbatim (FR-011), which
  is the clause this principle most directly protects here.

## Project Structure

### Documentation (this feature)

```text
specs/111-hamletgen-package/
├── plan.md                     # This file
├── spec.md                     # The feature specification
├── research.md                 # Phase 0 - partition, surface, oracle, config, method, scope
├── data-model.md               # Phase 1 - package layout, import DAG, sizes, baseline corpus
├── quickstart.md               # Phase 1 - verification commands
├── baseline_cohort.py          # Phase 1 - writes cohort manifests (cohort() discards them)
├── contracts/
│   └── package-surface.md      # the 49-name import-surface contract
├── checklists/
│   └── requirements.md         # spec quality checklist
└── tasks.md                    # Phase 2 (/speckit-tasks - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
.claude/skills/diagram/
├── hamletgen/                    # NEW package (replaces hamletgen.py, deleted same change)
│   ├── __init__.py               # sys.path bootstrap + head docstring + derived surface
│   ├── __main__.py               # CLI shim -> driver.main()
│   ├── CLAUDE.md                 # "look here when" index
│   ├── consts.py                 # Pt/Poly + the 32 researched constants
│   ├── plan.py                   # HamletSpec, SitePlan, plan_site
│   ├── geom.py                   # shared geometry predicates
│   ├── water.py                  # STAGE 1-2
│   ├── sink.py                   # STAGE 3
│   ├── cluster.py                # STAGE 4a
│   ├── ways.py                   # STAGE 4b
│   ├── homesteads.py             # STAGE 5-6
│   ├── hinterland.py             # STAGE 7
│   ├── frame.py                  # STAGE 8
│   └── driver.py                 # STAGES (the pipeline contract), Report, build, generate, cohort, main
├── test_hamletgen/               # NEW test package (replaces test_hamletgen.py)
├── test_hamletgen_surface.py     # NEW guard test
├── pyproject.toml                # mypy files entry + ruff per-file-ignores
├── CLAUDE.md, SKILL.md, hamletgen.md, migration-plan.md   # file-path references updated
└── pool/hamlets/*.notes.md       # file-path references updated
```

**Structure Decision**: package-of-subfiles per the check_village/waterfields exemplars; the
partition follows the monolith's own STAGE banner comments (research R1) with one deliberate
departure - STAGE 4's 670 lines split into `cluster.py` + `ways.py`. The import DAG was verified
acyclic by AST analysis before any code moved. Consumers untouched.

## Complexity Tracking

No constitution violations to justify.

One point worth recording rather than hiding: `STAGES` is NOT derived by introspection, even though
clause 14 pushes toward derived registries. The stage ORDER is a design decision (water before the
field the water shapes; ways before the homesteads that front them), not a fact recoverable from
the code, so it is exactly the ordered-data case clause 14 carves out. It stays a literal tuple in
one place, with a comment saying so - research R6.
