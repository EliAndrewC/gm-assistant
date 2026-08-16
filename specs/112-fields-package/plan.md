# Implementation Plan: settlement/fields.py -> settlement/fields/ Package Split

**Branch**: `112-fields-package` (no branch - `export SPECIFY_FEATURE=112-fields-package`) | **Date**: 2026-08-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/112-fields-package/spec.md`

## Summary

`settlement/fields.py` is 1,511 lines holding one `FieldsMixin` class of 24 methods, of which three
(`draw_comb_field` 321, `apply_land_use` 266, `water_field` 194) are 52% of the file. Split the
class into four sub-mixins in four submodules under `settlement/fields/`, composed back into a
single `FieldsMixin` by the package `__init__` so `core.py` is untouched, then decompose the three
oversized methods into named helpers. Both stages are proven by byte-identical pool artifacts
against a baseline captured from the pre-split tree.

The partition is derived from the class's own intra-class call graph, which is almost perfectly
clustered: four groups with exactly two cross-group helper edges, both of which cost nothing because
sub-mixin methods reach each other through `self.` on the composed `Settlement` instance and need no
import at all.

## Technical Context

**Language/Version**: Python 3.14 (container pin)

**Primary Dependencies**: none new. Package-internal only: `settlement._geom`, `settlement._knobs`,
stdlib (`hashlib`, `math`, `random`, `collections.abc`, `typing`)

**Storage**: N/A - the artifacts are pool `.json` manifests plus `.svg`/`.png` renders on disk

**Testing**: pytest with `-n auto`, `test_settlement/test_fields.py` (475 lines, stays one file),
plus the `check_village` gate and the `pool/regressions/` negative-fixture corpus

**Target Platform**: Linux container, CLI generators

**Project Type**: internal library - the Mode B settlement drawing engine of the `/diagram` skill

**Performance Goals**: unchanged. This is a pure refactor; `GEN_TIME_BUDGETS` per-gen CPU budgets
must not move. Method-call overhead from extraction is immaterial next to the geometry loops.

**Constraints**: byte-identical output for every pool artifact; zero consumer-file edits; no runtime
import cycle (`mypy --strict` must pass); every file under ~1,000 raw lines and every function under
~150 lines without justification

**Scale/Scope**: 1,511 lines, one class, 24 methods, 4 new submodules plus `__init__.py` and
`CLAUDE.md`; 21 files call `draw_comb_field`, 13 call `bund_junctions`, 13 call `pond` - none of
which change

## Constitution Check

*GATE: evaluated before Phase 0, re-checked after Phase 1 design. Result: PASS - no deferrals, no
Complexity Tracking entries.*

- **I. Accessibility-First Viewports**: **N/A** - no UI. This feature touches only the diagram
  engine's Python modules; no webapp page, template, or CSS is involved.
- **II. Bold, Intentional Design**: **N/A** - no new UI surface, so no aesthetic direction or
  typographic system to name.
- **III. Pool Data Conventions**: **N/A** - no pool content is added or modified. The opposite is
  required: every existing pool artifact must come back byte-identical.
- **IV. One Canonical Home for GM Source**: **N/A** - the feature adds and moves no SOURCE blocks.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: **PASS** - no task in this plan reads or
  writes anything inside `<!-- SOURCE: GM NOTES -->` markers, and none touches
  `/host-l7r-repo/setting/l7r.md`.
- **VI. Verify Before Reporting Done**: **PASS** - every task carries its verification. Stage 1 and
  Stage 2 each end with the byte-identity sweep (live gens in place, frozen gens in a scratch tree)
  plus `make done`; `git status` under `pool/` must be clean; the composed-surface guard test must
  be observed to FAIL before it is trusted. No subagent work is relayed without a spot-check of the
  artifact.
- **VII. De-Localized Generation by Default**: **N/A** - no pool content is generated.
- **VIII. Direct Voice Over Framing Distance**: **N/A** - no in-world content is written.
- **IX. Setting Integration**: **N/A** - no setting details are asserted and no named figures are
  introduced, so there is nothing to cross-reference and no name-collision risk.
- **X. Python Discipline (NON-NEGOTIABLE)**: **PASS**, and this principle is the feature.
  - `ruff check` + `ruff format --check` + `mypy --strict` + `pytest` all run in `make done`; the
    100% rule applies to every module outside `*/settlement/*` and the package rides the
    `SETTLEMENT_COV_FLOOR = 94` ratchet (verified: `settlement/fields/*.py` matches the same glob,
    so the Makefile needs no change).
  - **Clause 12 (functions at human scale)**: Stage 2 is exactly this - `draw_comb_field` (321),
    `apply_land_use` (266) and `water_field` (194) are decomposed to under ~150 lines each or
    carry an inline justification.
  - **Clause 13 (files at human scale)**: the motivation. Every resulting file is projected under
    ~500 raw lines; the largest, `paddy.py`, lands near 450.
  - **Clause 14 (derive, don't maintain a roster)**: **N/A with justification** - `fields/__init__.py`
    is not roster-shaped. It is four imports plus one `class FieldsMixin(...)` statement, and the
    sub-mixin bases ARE the surface; there is no per-name list to drift. The safety property is
    nonetheless moved into a guard test (FR-003) proven to fail against a dropped method, which is
    the part of clause 14's method that does apply.
  - **Red-green**: the composed-surface guard test is written and observed failing before the split
    lands.
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: **N/A with justification** - this feature
  changes nothing a generator asserts about the world. No element is added or changed; no farming,
  building or land-use rule moves. The byte-identity oracle is a stronger form of the closing
  bookend than a render re-examination would be: if any drawn element differed, the sweep fails. No
  Phase 0 grounding entry is therefore required, and none is invented.

## Project Structure

### Documentation (this feature)

```text
specs/112-fields-package/
├── plan.md              # This file
├── research.md          # Phase 0 - the partition decision and its alternatives
├── data-model.md        # Phase 1 - modules, sub-mixins, method assignment
├── quickstart.md        # Phase 1 - how to run the byte-identity harness
├── contracts/
│   └── mixin-surface.md # Phase 1 - the composed FieldsMixin contract
├── checklists/
│   └── requirements.md  # spec quality checklist
└── tasks.md             # Phase 2 (/speckit-tasks - not created here)
```

### Source Code

```text
.claude/skills/diagram/settlement/
├── CLAUDE.md            # MODIFIED: the fields.py row becomes the package rows
├── core.py              # UNCHANGED: from .fields import FieldsMixin; class Settlement(FieldsMixin, ...)
├── fields.py            # DELETED
└── fields/              # NEW package
    ├── CLAUDE.md        # NEW: the sub-index ("look here when")
    ├── __init__.py      # NEW: composes the four sub-mixins into FieldsMixin
    ├── paddy.py         # PaddyMixin - paddy + water + fallow fields and their plot geometry
    ├── comb.py          # CombMixin - the comb-field builder, base fill, bund junctions, furrows
    ├── landuse.py       # LandUseMixin - the land-use overlays and mulberry rows
    └── features.py      # FieldFeaturesMixin - non-rice features and standing-water glyphs

.claude/skills/diagram/test_settlement/
└── test_fields.py       # UNCHANGED in substance (475 lines, stays one file); gains the
                         # composed-surface guard test
```

**Structure Decision**: a package directory beside its siblings inside the existing `settlement/`
package, exactly as features 024, 110 and 111 shaped `check_village/`, `waterfields/` and
`hamletgen/`. `fields/` is a nested package rather than four flat `settlement/fields_*.py` modules
because the parent `settlement/CLAUDE.md` index is already at the limit of what one table can
usefully hold, and a nested package gets its own `CLAUDE.md` sub-index - which is the token saving
this feature exists for.

## Complexity Tracking

No Constitution Check violations. Table omitted.
