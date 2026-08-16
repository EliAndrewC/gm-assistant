# Implementation Plan: settlement/structures.py -> settlement/structures/ Package Split

**Branch**: none - `export SPECIFY_FEATURE=114-structures-package` | **Date**: 2026-08-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/114-structures-package/spec.md`

## Summary

Carve `settlement/structures.py` (1,459 lines, 33 members, one `StructuresMixin`) into a
seven-module `settlement/structures/` package composed back into a single `StructuresMixin`, so
`settlement/core.py` stays byte-unchanged. The technical approach is features 112 and 113's, adapted
rather than reinvented: a one-shot AST transformer that slices the class body between members, a
composed-surface guard test proven red before it is trusted, and a byte-identity sweep over the whole
`pool/` corpus as the oracle.

**Two stages, not three.** Its predecessors each followed the pure move with a per-method
decomposition stage, because both held functions far past the ~150-line bar (`city_wall` at 339,
`draw_comb_field` at 321). This file's largest member is `rowpack` at 130 lines. There is no clause-12
debt to pay, so the feature is the move plus the index - and the sweep runs twice rather than seven
times (research R4).

**What makes this file different from its two predecessors**, and it drives the partition: `fields.py`
and `city.py` were each ONE subsystem cut into facets. `structures.py` is feature 025's residue
bucket - seven unrelated subsystems in one file. So the grouping rule is "group by what a session
comes here to change" rather than "group by theme", and the resulting modules are deliberately uneven
in size (72 to 385 lines), because tasks are uneven in size (research R1).

## Technical Context

**Language/Version**: Python 3.14 (container pin)

**Primary Dependencies**: none new. Standard library `ast` for the transformer; existing `ruff`,
`mypy`, `pytest`, `pytest-xdist`, `pytest-cov`.

**Storage**: N/A - the artifacts are SVG/PNG/JSON files under `.claude/skills/diagram/pool/`.

**Testing**: `pytest -n auto`, `ruff check`, `ruff format --check`, `mypy --strict`, all via
`make done` from `.claude/skills/diagram/`. Guard test extends
`tests/settlement/test_structures.py` (591 lines, left whole - research R11).

**Target Platform**: the dev container; no runtime consumers outside this repo.

**Project Type**: internal library - the Mode B settlement drawing engine inside the `/diagram` skill.

**Performance Goals**: unchanged. `GEN_TIME_BUDGETS` in `tests/test_villages.py` must keep passing
unmodified. A pure move adds no call-site indirection - the members land on the same composed class
and resolve through the same MRO - so no per-call overhead is expected in the hot placement loops
(`pack`, `rowpack`, `_fits`). If a budget trips, that is a finding, not a number to raise.

**Constraints**:

- **Byte-identity** of every regenerated `pool/**` artifact. This is the hard constraint everything
  else is arranged around.
- **`settlement/core.py` byte-unchanged** - proven by an empty `git diff --stat`, not by inspection.
- **`SETTLEMENT_COV_FLOOR` never falls** (currently 94). A pure move cannot move it either way;
  research R7 says a movement is a signal to investigate rather than a number to bank.
- **Exactly one consumer file outside the package changes**, and only a filename string in it
  (`tests/tools/test_why_placed.py`; research R6).

**Scale/Scope**: 1,459 lines -> 7 modules (largest ~385) + `__init__.py` + `CLAUDE.md`. 33 members
redistributed, 0 renamed, 0 relocated out of the package. Oracle: every `pool/` generator, live and
frozen.

## Constitution Check

*GATE: evaluated before Phase 0, re-evaluated after Phase 1 design (see the re-check at the end).*

- **I. Accessibility-First Viewports**: **N/A** - this feature ships no UI; the L7R Toolkit webapp is
  untouched.
- **II. Bold, Intentional Design**: **N/A** - no new UI surfaces.
- **III. Pool Data Conventions**: **N/A** - no generated content of a recurring kind is added or
  modified. `pool/` is read as an oracle and must come back byte-identical; nothing is written to it.
- **IV. One Canonical Home for GM Source**: **N/A** - no SOURCE blocks are added or moved.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: **PASS** - no task in this plan touches content
  inside SOURCE markers. The two documents edited (`settlement/CLAUDE.md`,
  `settlement/structures/CLAUDE.md`) contain none.
- **VI. Verify Before Reporting Done**: **PASS** - every task carries its verification. The cheap
  prefix (`ruff format`, `ruff check`, `mypy`), then the WHOLE affected test files (never a `-k`
  subset, and including `tests/tools/` because of the one consumer change), then the byte-identity
  sweep, then one backgrounded `make done` read by its log tail. No delegated work in this feature,
  so nothing to spot-check on a subagent's behalf.
- **VII. De-Localized Generation by Default**: **N/A** - no pool content generated.
- **VIII. Direct Voice Over Framing Distance**: **N/A** - no in-world content written.
- **IX. Setting Integration**: **N/A** - no setting details asserted, no new named figures. The
  setting research already IN the file (the manor glyph doctrine, the nagaya sourcing, the Pingyao
  drum-tower footprint) must arrive intact, which is a verification step rather than new content.
- **X. Python Discipline (NON-NEGOTIABLE)**: **PASS**, and this principle IS the feature.
  - `ruff check` + `ruff format --check` + `mypy --strict`: in the gate, run as the cheap prefix
    before the expensive half.
  - Red-green TDD: the composed-surface guard (FR-003) is written and observed FAILING - three times,
    once per breakage class - before the split is committed. Recorded in tasks.md with the failure
    text, per the contract.
  - `pytest --cov-fail-under=100` on pure-logic packages, and the `settlement/` ratchet at its floor.
  - **Clause 12** (functions at human scale): evaluated, nothing to do. Largest member is 130 lines,
    under the ~150 bar its predecessors settled on. Research R4 says why decomposing anyway would be
    wrong here.
  - **Clause 13** (files at human scale, tests included): this is US1's whole subject. The test file
    at 591 lines is under the bar and stays whole; research R11 records that as a decision with the
    threshold at which it changes.
  - **Clause 14** (derive, don't maintain or split) was evaluated and **does not apply**:
    `structures.py` is not roster-shaped. Its 33 members are hand-written drawing and placement logic
    with distinct behavior - nothing restates what code elsewhere declares, so there is no surface to
    derive. Recorded in research R2 so a later reader does not mistake the omission for an oversight.
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: **N/A**, and argued rather than asserted -
  research R9. The feature changes nothing a generator asserts about the world: no element added or
  changed, no size, spacing, prevalence or siting rule touched. The closing bookend (re-examine the
  rendered PNG) is satisfied more strongly than by eye - an empty hash diff over every `.png` in the
  pool proves the depiction is unchanged pixel for pixel. The grounding already in the file is
  protected by the slicing rule (R5) and CHECKED, not assumed, by quickstart step 6.

**Result: no gate DEFERRED, no Complexity Tracking entries.**

## Project Structure

### Documentation (this feature)

```text
specs/114-structures-package/
├── plan.md                      # this file
├── spec.md
├── research.md                  # Phase 0: R1-R11
├── data-model.md                # Phase 1: the authoritative partition
├── quickstart.md                # Phase 1: the verification harness
├── contracts/
│   └── mixin-surface.md         # Phase 1: the composed-surface contract
├── split_structures.py          # Phase 1: the one-shot transformer
├── checklists/
│   └── requirements.md
└── tasks.md                     # Phase 2 (/speckit-tasks)
```

### Source Code

```text
.claude/skills/diagram/
├── settlement/
│   ├── CLAUDE.md                # EDITED: the `structures` row points at the sub-index
│   ├── core.py                  # UNCHANGED (byte-for-byte; proven, not inspected)
│   ├── structures.py            # DELETED
│   └── structures/              # NEW
│       ├── CLAUDE.md            # the token-scale index (US2)
│       ├── __init__.py          # composes StructuresMixin; no members of its own
│       ├── compounds.py         # manor, merchant estates            (~254 lines)
│       ├── ground.py            # road, pasture                      (~72)
│       ├── urban.py             # URBAN palette, building, seating   (~159)
│       ├── servants.py          # the nagaya pass + its four probes  (~196)
│       ├── packing.py           # rowpack, pack, _shortfall          (~274)
│       ├── captions.py          # the caption probes                 (~84)
│       └── fixtures.py          # public street furniture + siters   (~385)
└── tests/
    ├── settlement/test_structures.py   # EDITED: + the composed-surface guard
    └── tools/test_why_placed.py        # EDITED: one filename string (research R6)
```

**Structure Decision**: mirrors `settlement/fields/` (feature 112) and `settlement/city/` (feature
113) exactly - a directory module whose `__init__.py` composes the sub-mixins back into the single
mixin name `core.py` imports, plus a `CLAUDE.md` index. This is the third instance of the pattern in
this package, which is itself the argument for not inventing a fourth shape.

## Implementation stages

### Stage 0 - baseline (blocking)

Capture the byte-identity baseline from a scratch copy of the PRE-split tree
(quickstart step 1), and record the `REGENERATED` count and the sweep's own verdict. Confirm
`gencache.engine_files()` sees the file (quickstart step 0), so the post-split re-run is a real
comparison. An oracle that has not been shown to work is not an oracle.

### Stage 1 - the pure move (US1, P1)

Write the guard test first and prove its method-deletion assertion red pre-split. Then run
`split_structures.py`, prune the copied import headers with ruff, delete `structures.py`, prove the
remaining two guard breakages red, update the one consumer filename, and sweep. Byte-identity, a
clean `git status` under `pool/`, and a green `make done` with `core.py` byte-unchanged are the exit
criteria.

### Stage 2 - the index (US2, P2)

`settlement/structures/CLAUDE.md` with a "look here when" row per module, plus the three decisions a
reader would otherwise re-litigate (research R1a/R1b/R1c), the monkeypatching note (R8), the
`fixtures.py` re-split seam, and the test-file threshold (R11). Update `settlement/CLAUDE.md`'s
`structures` row to point at it rather than list contents inline.

Docs-only, so it skips the gate (root CLAUDE.md, "Docs-only diffs skip the gate").

## Constitution re-check (post-Phase 1 design)

Re-evaluated against the artifacts now that they exist. No gate changes status.

The design added no UI, no pool content, no in-world prose and no setting assertion, so gates I-IX
and XII stand as recorded. Principle X is reinforced rather than weakened by the design: the
partition in `data-model.md` puts every module under 450 lines (clause 13 satisfied with margin), the
contract in `contracts/mixin-surface.md` specifies THREE red proofs rather than the two features 112
and 113 ran - the extra one covering class-level attributes, which 112 needed a separate test for -
and research R7 pre-commits to treating any coverage movement as a defect rather than as a floor
adjustment.

One design decision is worth flagging as accepted rather than avoided: `fixtures.py` at ~385 lines is
over half the size of the next-largest module. It is under every bar and it is a coherent cluster,
but `data-model.md` records the seam along which it should be re-cut if it grows, so the next session
inherits the decision rather than making it under pressure.
