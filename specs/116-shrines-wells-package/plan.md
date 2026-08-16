# Implementation Plan: settlement/shrines_wells.py -> settlement/shrines_wells/ Package Split

**Branch**: none - `export SPECIFY_FEATURE=116-shrines-wells-package` | **Date**: 2026-08-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/116-shrines-wells-package/spec.md`

## Summary

Carve `settlement/shrines_wells.py` (1,179 lines, 38 members, one `ShrinesWellsMixin`) into a
seven-module `settlement/shrines_wells/` package composed back into a single `ShrinesWellsMixin`, so
`settlement/core.py` stays byte-unchanged. The technical approach is features 112, 113 and 114's,
adapted rather than reinvented: a one-shot AST transformer that slices the class body BETWEEN
members, a composed-surface guard test proven red before it is trusted, and a byte-identity sweep
over the whole `pool/` corpus as the oracle.

**One stage, not two.** Features 112 and 113 followed the pure move with a per-method decomposition
stage because both held functions far past the ~150-line bar (`city_wall` 339, `draw_comb_field`
321). Feature 114 skipped it at a 130-line maximum. This file's largest member is `shrine_hall` at
114 lines, so there is no clause-12 debt to pay and the sweep runs twice rather than many times
(research R4).

**What drives the partition.** `fields.py` was one subsystem cut four ways and `city.py` one tier cut
six ways; `structures.py` (114) was a residue bucket grouped by what a session comes to change. This
file is the residue-bucket case in its purest form - its NAME concedes it, being the only module in
the package joined by an `and`. Six unrelated subsystems share it because feature 025 sliced the
16,016-line original by position: religious halls, torii avenues, the well subsystem, a general
seat-finding API, draft byres, and woodland stands. So the grouping rule is again "group by what a
session comes here to CHANGE", and the resulting modules are deliberately uneven (54 to 275 body
lines), because tasks are uneven (research R1).

**One judgment call worth surfacing up front.** The well subsystem is 447 lines - big enough to be
the whole justification for the split and big enough to want cutting itself. It is cut at the seam
between *"is this ground fit to sink a wellhead in"* (`wellground.py`: the three-grid index, the
`frozen_terrain` scope, the wet-toe keepout, the scrub refusal) and *"put wells on the map"*
(`wells.py`: the glyph and the four placement passes). That is a real task boundary - the open
performance work touches the first, the open siting defects touch the second - and research R1e
records why it was cut there rather than left whole or cut by tier.

## Technical Context

**Language/Version**: Python 3.14 (container pin)

**Primary Dependencies**: none new. Standard library `ast` for the transformer; existing `ruff`,
`mypy`, `pytest`, `pytest-xdist`, `pytest-cov`.

**Storage**: N/A - the artifacts are SVG/PNG/JSON files under `.claude/skills/diagram/pool/`.

**Testing**: `pytest -n auto`, `ruff check`, `ruff format --check`, `mypy --strict`, all via
`make done` from `.claude/skills/diagram/`. The guard test extends
`tests/settlement/test_shrines_wells.py` (474 lines, left whole - research R11).

**Target Platform**: the dev container; no runtime consumers outside this repo.

**Project Type**: internal library - the Mode B settlement drawing engine inside the `/diagram` skill.

**Performance Goals**: unchanged. `GEN_TIME_BUDGETS` in `tests/test_villages.py` must keep passing
unmodified. A pure move adds no call-site indirection - the members land on the same composed class
and resolve through the same MRO - so no per-call overhead is expected. That matters more here than
in any predecessor: `_well_ground_clear` and `_in_scrub_cover` are the two hottest predicates in the
engine (~133k candidate seats on Minami alone), and the whole `frozen_terrain` design exists because
a per-candidate cost of a few microseconds once turned a 5s gen into a 45-minute grind. If a budget
trips, that is a finding, not a number to raise.

**Constraints**:

- **Byte-identity** of every regenerated `pool/**` artifact. The hard constraint everything else is
  arranged around.
- **`settlement/core.py` byte-unchanged** - proven by an empty `git diff --stat`, not by inspection.
- **`SETTLEMENT_COV_FLOOR` never falls** (currently 94). A pure move cannot move it either way;
  research R7 says a movement is a signal to investigate, never a number to re-baseline.
- **No consumer file outside the package changes at all.** Feature 114 had exactly one (a filename
  string in `tests/tools/test_why_placed.py`); the census for THIS module's name finds none -
  `settlement/core.py`'s import line is the only occurrence anywhere, and it survives the split
  unchanged (research R6).

**Scale/Scope**: 1,179 lines -> 7 modules (largest ~275 body lines) + `__init__.py` + `CLAUDE.md`. 38
members redistributed, 0 renamed, 0 relocated out of the package. Oracle: every `pool/` generator,
live and frozen.

## Constitution Check

*GATE: evaluated before Phase 0, re-evaluated after Phase 1 design (see the re-check at the end).*

- **I. Accessibility-First Viewports**: **N/A** - this feature ships no UI; the L7R Toolkit webapp is
  untouched.
- **II. Bold, Intentional Design**: **N/A** - no new UI surfaces.
- **III. Pool Data Conventions**: **N/A** - no generated content of a recurring kind is added or
  modified. `pool/` is read as an oracle and must come back byte-identical; nothing is written to it.
- **IV. One Canonical Home for GM Source**: **N/A** - no SOURCE blocks are added or moved.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: **PASS** - no task in this plan touches
  content inside SOURCE markers. The two documents edited (`settlement/CLAUDE.md`,
  `settlement/shrines_wells/CLAUDE.md`) contain none.
- **VI. Verify Before Reporting Done**: **PASS** - every task carries its verification. The cheap
  prefix (`ruff format`, `ruff check`, `mypy`), then the WHOLE affected test file (never a `-k`
  subset), then the byte-identity sweep, then one backgrounded `make done` read by its log tail. No
  delegated work in this feature, so nothing to spot-check on a subagent's behalf.
- **VII. De-Localized Generation by Default**: **N/A** - no pool content generated.
- **VIII. Direct Voice Over Framing Distance**: **N/A** - no in-world content written.
- **IX. Setting Integration**: **N/A** - no setting details asserted, no new named figures. The
  setting and historical research already IN the file (the canopy-density study, the true-scale
  shrine-hall guard, the wayside-shrine glyph, the idobata doctrine) must arrive intact, which is a
  verification step rather than new content.
- **X. Python Discipline (NON-NEGOTIABLE)**: **PASS**, and this principle IS the feature.
  - `ruff check` + `ruff format --check` + `mypy --strict`: in the gate, run as the cheap prefix
    before the expensive half.
  - Red-green TDD: the composed-surface guard (FR-003) is written and observed FAILING - twice, once
    per breakage class - before the split is committed. Recorded in tasks.md with the failure text,
    per the contract.
  - `pytest --cov-fail-under=100` on pure-logic packages, and the `settlement/` ratchet at its floor.
  - **Clause 12** (functions at human scale): evaluated, nothing to do. Largest member is
    `shrine_hall` at 114 lines, under the ~150 bar its predecessors settled on. Research R4 says why
    decomposing anyway would be wrong here.
  - **Clause 13** (files at human scale, tests included): this is US1's whole subject. The test file
    at 474 lines is under the bar and stays whole; research R11 records that as a decision with the
    threshold at which it changes.
  - **Clause 14** (derive, don't maintain or split) was evaluated and **does not apply**:
    `shrines_wells.py` is not roster-shaped. Its 38 members are hand-written drawing and placement
    logic with distinct behavior - nothing restates what code elsewhere declares, so there is no
    surface to derive. Recorded in research R2 so a later reader does not mistake the omission for an
    oversight.
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: **N/A**, and argued rather than asserted -
  research R9. The feature changes nothing a generator asserts about the world: no element added or
  changed, no size, spacing, prevalence or siting rule touched. The closing bookend (re-examine the
  rendered PNG) is satisfied more strongly than by eye - an empty hash diff over every `.png` in the
  pool proves the depiction is unchanged pixel for pixel. The grounding already in the file - and
  this file carries more of it than any other module in the package - is protected by the slicing
  rule (R5) and CHECKED, not assumed, by quickstart step 6.

**Result: no gate DEFERRED, no Complexity Tracking entries.**

## Project Structure

### Documentation (this feature)

```text
specs/116-shrines-wells-package/
├── plan.md                      # this file
├── spec.md
├── research.md                  # Phase 0: R1-R12
├── data-model.md                # Phase 1: the authoritative partition
├── quickstart.md                # Phase 1: the verification harness
├── contracts/
│   └── mixin-surface.md         # Phase 1: the composed-surface contract
├── split_shrines_wells.py       # Phase 1: the one-shot transformer
├── checklists/
│   └── requirements.md
└── tasks.md                     # Phase 2 (/speckit-tasks)
```

### Source Code

```text
.claude/skills/diagram/
├── settlement/
│   ├── CLAUDE.md                # EDITED: the `shrines_wells` row points at the sub-index
│   ├── core.py                  # UNCHANGED (byte-for-byte; proven, not inspected)
│   ├── shrines_wells.py         # DELETED
│   └── shrines_wells/           # NEW
│       ├── CLAUDE.md            # the token-scale index (US3)
│       ├── __init__.py          # composes ShrinesWellsMixin; no members of its own
│       ├── shrines.py           # hill, shrine glyphs, the hall + its caption   (~230 body lines)
│       ├── torii.py             # the arch glyph and the whole avenue engine    (~179)
│       ├── wellground.py        # where a wellhead MAY stand (the hub)          (~172)
│       ├── wells.py             # the wellhead glyph and the four passes        (~275)
│       ├── seats.py             # open_seat + _footprint_clear                  (~69)
│       ├── byres.py             # the draft-animal byre                         (~54)
│       └── woods.py             # tree stands, the fringe, forest               (~166)
└── tests/
    └── settlement/test_shrines_wells.py   # EDITED: + the composed-surface guard
```

**Structure Decision**: mirrors `settlement/fields/` (112), `settlement/city/` (113) and
`settlement/structures/` (114) exactly - a directory module whose `__init__.py` composes the
sub-mixins back into the single mixin name `core.py` imports, plus a `CLAUDE.md` index. This is the
fourth instance of the pattern in this package, which is itself the argument for not inventing a
fifth shape.

## Implementation stages

### Stage 0 - baseline (blocking)

Capture the byte-identity baseline from a scratch copy of the PRE-split tree (quickstart step 1) and
record the `REGENERATED` count and the sweep's own exit code. Confirm `gencache.engine_files()` sees
the package after the split (quickstart step 0) - its walk is already depth-agnostic by construction
(feature 025 made `settlement/` a package for exactly this reason), but a borrowed analogy is not a
check. An oracle that has not been shown to work is not an oracle.

### Stage 1 - the pure move (US1 + US2, P1/P2)

Write the guard test first and prove its member-deletion assertion red PRE-split (it runs unchanged
before and after - the collision half is vacuous while `ShrinesWellsMixin` is a single class). Then
run `split_shrines_wells.py`, prune the copied import headers with ruff, delete `shrines_wells.py`,
prove the collision breakage red, and sweep. Byte-identity, a clean `git status` under `pool/`, zero
comment lines lost, and a green `make done` with `core.py` byte-unchanged are the exit criteria.

### Stage 2 - the index (US3, P3)

`settlement/shrines_wells/CLAUDE.md` with a "look here when" row per module, the hub statement, the
cross-submodule call map, and the four decisions a reader would otherwise re-litigate (research
R1a-R1d). Update `settlement/CLAUDE.md`'s `shrines_wells` row to point at it rather than list
contents inline.

Docs-only, so it skips the gate (root CLAUDE.md, "Docs-only diffs skip the gate").

## Constitution re-check (post-Phase 1 design)

Re-evaluated against the artifacts now that they exist. No gate changes status.

The design added no UI, no pool content, no in-world prose and no setting assertion, so gates I-IX
and XII stand as recorded. Principle X is reinforced rather than weakened by the design: the
partition in `data-model.md` puts every module under 320 raw lines (clause 13 satisfied with a wide
margin), the contract in `contracts/mixin-surface.md` keeps feature 114's `vars()`-based census -
which sees class-level attributes as well as methods, the half a callable-only census cannot - even
though this class has no class attribute today, and research R7 pre-commits to treating any coverage
movement as a defect rather than as a floor adjustment.

Two design decisions are worth flagging as accepted rather than avoided:

- **`wells.py` at ~275 body lines** is the largest module and roughly a fifth of the pre-split file.
  It is a coherent cluster (one glyph, four passes that place it) and well under every bar.
  `data-model.md` records the seam along which it would be re-cut if it grows - `farm_wells` and
  `place_wells` are independent passes with no shared helper - so the next session inherits the
  decision rather than making it under pressure.
- **`seats.py` and `byres.py` are small on purpose.** Both hold members that do not belong to this
  subsystem at all; isolating each makes its eventual move a one-file change. Feature 113 did this
  with `governor_mansion`, 114 with `road`/`pasture`, and both isolations are still correct today.
