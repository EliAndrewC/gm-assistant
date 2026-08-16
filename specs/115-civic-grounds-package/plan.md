# Implementation Plan: settlement/civic_grounds.py -> settlement/civic_grounds/ Package Split

**Branch**: none - `export SPECIFY_FEATURE=115-civic-grounds-package` | **Date**: 2026-08-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/115-civic-grounds-package/spec.md`

## Summary

Carve `settlement/civic_grounds.py` (1,162 lines, 22 members, one `CivicGroundsMixin`) into a
five-module `settlement/civic_grounds/` package composed back into a single `CivicGroundsMixin`, so
`settlement/core.py` stays byte-unchanged - then decompose `_stable_yard` (335 lines) into named
stages. The technical approach is features 112/113/114's, adapted rather than reinvented: a one-shot
AST transformer that slices the class body between members, a composed-surface guard test proven red
before it is trusted, and a byte-identity sweep over the whole `pool/` corpus as the oracle.

**Three stages, not two.** Feature 114 skipped the per-method decomposition stage because its largest
member was 130 lines, under the ~150 bar feature 112 settled on. This file's largest member is 335 -
the largest function in the engine, 2.2x the bar, 29% of the file by itself. The clause-12 debt is
real, so the sweep runs three times rather than twice (research R4): once to establish the baseline,
once after the move, once after the decomposition. Splitting the runs is what makes a hash mismatch
diagnostic instead of merely alarming.

**What drives the partition**: like `structures.py` and unlike `fields.py`/`city.py`, this file is a
residue bucket rather than one subsystem cut into facets - funerary ground, judicial ground, civic
and commercial works, lodging with its livestock yards. So the grouping rule is again "group by what
a session comes here to change", and the resulting modules are deliberately uneven (research R1).
The one departure from 114's shape is `stable_yard.py`: a module holding a single private method,
justified in R1c by the fact that the method alone is bigger than three of the other four modules.

**The one real risk, named early**: `_stable_yard` brackets its whole body in
`random.getstate()` / `random.seed(...)` / ... / `random.setstate(st)` and draws from the GLOBAL
`random` stream throughout - scatter, furniture shuffle, rail candidates, trough jitter. Extracting
stages is therefore safe only if every extracted stage consumes that stream at exactly the same point
in the same order. This is the sole way this feature can silently change a map while passing
`mypy --strict`, `ruff` and every unit test, and it is what the third byte-identity sweep exists to
catch (research R12).

## Technical Context

**Language/Version**: Python 3.14 (container pin)

**Primary Dependencies**: none new. Standard library `ast` for the transformer; existing `ruff`,
`mypy`, `pytest`, `pytest-xdist`, `pytest-cov`.

**Storage**: N/A - the artifacts are SVG/PNG/JSON files under `.claude/skills/diagram/pool/`.

**Testing**: `pytest -n auto`, `ruff check`, `ruff format --check`, `mypy --strict`, all via
`make done` from `.claude/skills/diagram/`. The guard test extends
`tests/settlement/test_civic_grounds.py` (489 lines, left whole - research R10).

**Target Platform**: the dev container; no runtime consumers outside this repo.

**Project Type**: internal library - the Mode B settlement drawing engine inside the `/diagram` skill.

**Performance Goals**: unchanged. `GEN_TIME_BUDGETS` in `tests/test_villages.py` must keep passing
unmodified. The move adds no call-site indirection. The decomposition adds up to seven Python calls
per stable yard drawn - a yard is drawn a handful of times per city map, so the cost is unmeasurable
against a ~3-minute pool sweep. If a budget trips, that is a finding, not a number to raise.

**Constraints**:

- **Byte-identity** of every regenerated `pool/**` artifact, at TWO checkpoints (post-move,
  post-decomposition). This is the hard constraint everything else is arranged around.
- **`settlement/core.py` byte-unchanged** - proven by an empty `git diff --stat`, not by inspection.
- **RNG draw order preserved** through the decomposition (research R12).
- **`SETTLEMENT_COV_FLOOR` never falls** (currently 94, in `.claude/skills/diagram/Makefile:62` -
  note it is the SKILL's Makefile, not the webapp's; the spec's FR-014 is corrected here).
- **Zero consumer files outside `settlement/` change behavior.** Unlike 114, no consumer here asserts
  on the source filename (research R6), so the expected count is zero rather than one.

**Scale/Scope**: 1,162 lines -> 5 modules (largest ~385) + `__init__.py` + `CLAUDE.md`. 22 members
redistributed, 0 renamed, 0 relocated out of the package, 0 deleted. One 335-line method becomes
seven named stages. Oracle: every `pool/` generator, live and frozen, plus one `wip/shiro-daika` run.

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
  `settlement/civic_grounds/CLAUDE.md`) contain none.
- **VI. Verify Before Reporting Done**: **PASS** - every task carries its verification. The cheap
  prefix (`ruff format`, `ruff check`, `mypy`), then the WHOLE affected test file (never a `-k`
  subset), then the byte-identity sweep, then one backgrounded `make done` read by its log tail. No
  delegated work in this feature, so nothing to spot-check on a subagent's behalf.
- **VII. De-Localized Generation by Default**: **N/A** - no pool content generated.
- **VIII. Direct Voice Over Framing Distance**: **N/A** - no in-world content written.
- **IX. Setting Integration**: **N/A** - no setting details asserted, no new named figures. The
  setting research already IN the file (the Qingming Shanghe Tu gate convention, the caravanserai and
  yizhan watering doctrine, the ox-consumption arithmetic behind the trough count) must arrive
  intact - a verification step rather than new content, and the one this feature most has to earn,
  because unlike a pure move the decomposition physically relocates those comments.
- **X. Python Discipline (NON-NEGOTIABLE)**: **PASS**, and this principle IS the feature.
  - `ruff check` + `ruff format --check` + `mypy --strict`: in the gate, run as the cheap prefix
    before the expensive half.
  - Red-green TDD: the composed-surface guard (FR-003) is written and observed FAILING - twice, once
    per breakage class - before the split is committed. Recorded in tasks.md with the failure text.
  - `pytest --cov-fail-under=100` on pure-logic packages, and the `settlement/` ratchet at its floor.
  - **Clause 12** (functions at human scale): this is US3's whole subject. `_stable_yard` at 335
    lines is the engine's largest function; after this feature the engine's largest is
    `rolling.py::roll_village` at 256, which is named here as the next clause-12 candidate but is
    explicitly NOT in scope.
  - **Clause 13** (files at human scale, tests included): this is US1's whole subject. The test file
    at 489 lines is under the bar and stays whole; research R10 records that as a decision with the
    threshold at which it changes.
  - **Clause 14** (derive, don't maintain or split) was evaluated and **does not apply**:
    `civic_grounds.py` is not roster-shaped. Its 22 members are hand-written drawing and siting logic
    with distinct behavior - nothing restates what code elsewhere declares. The new `__init__.py` is
    composition-only (~40 lines), far below the size at which a derived surface would pay. Recorded
    in research R2 so a later reader does not mistake the omission for an oversight. Research R6
    records the one clause-14-adjacent finding: a dead-member census run WITHOUT intra-file callers
    falsely reported `_way_seat_near` as deletable.
- **XI. Japanese Authenticity (NON-NEGOTIABLE)**: **N/A** - no kanji is generated or altered.
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: **N/A**, and argued rather than asserted -
  research R9. The feature changes nothing a generator asserts about the world: no element added or
  changed, no size, spacing, prevalence or siting rule touched. The closing bookend (re-examine the
  rendered PNG) is satisfied more strongly than by eye - an empty hash diff over every `.png` in the
  pool proves the depiction is unchanged pixel for pixel. The grounding already in the file is
  protected by the slicing rule (R5) for the move, and by an explicit comment-survival check
  (quickstart step 7) for the decomposition, where slicing does not protect it.

**Result: no gate DEFERRED, no Complexity Tracking entries.**

## Project Structure

### Documentation (this feature)

```text
specs/115-civic-grounds-package/
├── plan.md                      # this file
├── spec.md
├── research.md                  # Phase 0: R1-R12
├── data-model.md                # Phase 1: the authoritative partition + stage decomposition
├── quickstart.md                # Phase 1: the verification harness
├── contracts/
│   └── mixin-surface.md         # Phase 1: the composed-surface contract
├── split_civic_grounds.py       # Phase 1: the one-shot transformer
├── checklists/
│   └── requirements.md
└── tasks.md                     # Phase 2 (/speckit-tasks)
```

### Source Code

```text
.claude/skills/diagram/
├── settlement/
│   ├── CLAUDE.md                # EDITED: the `civic_grounds` row points at the sub-index
│   ├── core.py                  # UNCHANGED (byte-for-byte; proven, not inspected)
│   ├── civic_grounds.py         # DELETED
│   └── civic_grounds/           # NEW
│       ├── CLAUDE.md            # the token-scale index (US4)
│       ├── __init__.py          # composes CivicGroundsMixin; no members of its own  (~40)
│       ├── funerary.py          # cemetery, mausoleum, cremation, ossuary            (~230)
│       ├── justice.py           # punishment spots, execution grounds, markers       (~200)
│       ├── civic.py             # precinct interior, districts, terraces, granary,
│       │                        #   merchant storehouses + residences                (~265)
│       ├── lodging.py           # flophouse, inn, stables, animal ground, the flush  (~190)
│       └── stable_yard.py       # _stable_yard, decomposed into seven stages         (~385)
└── tests/
    └── settlement/test_civic_grounds.py   # EDITED: + the composed-surface guard
```

**Structure Decision**: mirrors `settlement/fields/` (112), `settlement/city/` (113) and
`settlement/structures/` (114) exactly - a directory module whose `__init__.py` composes the
sub-mixins back into the single mixin name `core.py` imports, plus a `CLAUDE.md` index. This is the
fourth instance of the pattern in this package, which is itself the argument for not inventing a
fifth shape.

## Implementation stages

### Stage 0 - baseline (blocking)

Capture the byte-identity baseline from a scratch copy of the PRE-split tree (quickstart step 1),
including one `wip/shiro-daika` run (FR-005), and record the `REGENERATED` count and the sweep's own
verdict. Confirm `gencache.engine_files()` sees the file (quickstart step 0), so the post-split
re-run is a real comparison. An oracle that has not been shown to work is not an oracle.

### Stage 1 - the pure move (US1 P1, US2 P2)

Write the guard test first and prove its member-deletion assertion red pre-split. Then run
`split_civic_grounds.py`, prune the copied import headers with ruff, delete `civic_grounds.py`,
prove the collision assertion red, and sweep. Byte-identity, a clean `git status` under `pool/`, and
a green `make done` with `core.py` byte-unchanged are the exit criteria.

`_stable_yard` moves in this stage UNCHANGED - a 335-line method inside a 385-line module. Stage 1
is allowed to leave the clause-12 debt standing precisely so that a hash mismatch here can only mean
the move broke something.

### Stage 2 - the stable-yard decomposition (US3 P3)

Extract the seven stages named in `data-model.md`, keeping the `getstate`/`seed`/`setstate` bracket
in the outer method and every RNG draw in its original order (research R12). Each extracted stage
carries its banner comment verbatim. Then the second byte-identity sweep, and the comment-survival
check (quickstart step 7).

If the sweep comes back dirty at this stage, the cause is RNG order and the diff is per-map - revert
the last stage extracted rather than debugging forward.

### Stage 3 - the index (US4 P4)

`settlement/civic_grounds/CLAUDE.md` with a "look here when" row per module, the three placement
decisions (research R1a/R1b/R1c), the stage map for `stable_yard.py`, the monkeypatching note (R8),
and the test-file threshold (R10). Update `settlement/CLAUDE.md`'s `civic_grounds` row to point at
it rather than list contents inline.

Docs-only, so it skips the gate (root CLAUDE.md, "Docs-only diffs skip the gate").

## Constitution re-check (post-Phase 1 design)

Re-evaluated against the artifacts now that they exist. No gate changes status.

The design added no UI, no pool content, no in-world prose and no setting assertion, so gates I-IX,
XI and XII stand as recorded. Principle X is reinforced rather than weakened by the design: the
partition in `data-model.md` puts every module under 400 lines (clause 13 satisfied with margin) and
every function under 150 lines (clause 12 satisfied, closing the engine's worst outstanding case),
and the contract in `contracts/mixin-surface.md` specifies the two red proofs plus a THIRD that 114
did not need - that each of the seven extracted stages is actually reached, so a stage that silently
stopped being called cannot hide behind an unchanged hash.

Two design decisions are worth flagging as accepted rather than avoided:

- **`stable_yard.py` at ~385 lines holds one public entry point.** That is a module whose whole
  contents serve a single private method, which reads oddly next to `funerary.py`'s five siblings.
  It is right anyway: the alternative is a `lodging.py` of ~575 lines, which fails the very bar this
  feature exists to enforce. `data-model.md` records the seam along which it would re-cut if the
  yard grows again.
- **Principle XII is marked N/A on a feature that physically moves ~90 lines of researched
  grounding comments.** The justification is that N/A refers to what the generator ASSERTS, which is
  provably unchanged; the risk to the grounding is a different risk, and it is met with an explicit
  check (quickstart step 7) rather than with a gate status.
