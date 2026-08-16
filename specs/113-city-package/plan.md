# Implementation Plan: settlement/city.py -> settlement/city/ Package Split

**Branch**: none - `export SPECIFY_FEATURE=113-city-package` | **Date**: 2026-08-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/113-city-package/spec.md`

## Summary

Carve `settlement/city.py` (1,582 lines, 27 methods, one `CityMixin`) into a six-module
`settlement/city/` package composed back into a single `CityMixin`, so `settlement/core.py` stays
byte-unchanged. Then decompose the five oversized methods one at a time. The technical approach is
feature 112's, adapted rather than reinvented: a one-shot AST transformer that slices the class body
between members, a composed-surface guard test proven red before it is trusted, and a byte-identity
sweep over the whole `pool/` corpus as the oracle - run after the move and after every single
decomposition.

The one thing this feature does NOT inherit from 112 is its delete/modify merge hazard. The peer
"Diagram reorganize" session confirmed it touches nothing under `settlement/`; what it does move is
this feature's TOOLING (`tests/settlement/`, `python3 -m pipeline.regen`, the `engine_files()`
prune), so implementation begins only after that session's push lands and every path below is
written post-reorg.

## Technical Context

**Language/Version**: Python 3.14 (container pin)

**Primary Dependencies**: none new. Standard library `ast` for the transformer; existing `ruff`,
`mypy`, `pytest`, `pytest-xdist`, `pytest-cov`.

**Storage**: N/A - the artifacts are SVG/PNG/JSON files under `.claude/skills/diagram/pool/`.

**Testing**: `pytest -n auto`, `ruff check`, `ruff format --check`, `mypy --strict`, all via
`make done` from `.claude/skills/diagram/`. New guard test at `tests/settlement/test_city.py`
(post-reorg path).

**Target Platform**: the dev container; no runtime consumers outside this repo.

**Project Type**: internal library - the Mode B settlement drawing engine inside the `/diagram`
skill.

**Performance Goals**: unchanged. `GEN_TIME_BUDGETS` in `test_villages.py` must keep passing
unmodified - an extraction that adds per-call overhead to a hot inner loop would show there.

**Constraints**:

- **Byte-identity** of every regenerated `pool/**` artifact, after the move and after each
  decomposition. This is the hard constraint everything else is arranged around.
- **`settlement/core.py` byte-unchanged** - proven by an empty `git diff --stat`, not by inspection.
- **`SETTLEMENT_COV_FLOOR` never falls** (currently 94; the peer session left it deliberately for
  this feature to own).
- **Build on the peer's tip**, not beside it.

**Scale/Scope**: 1,582 lines -> 6 modules (largest ~494) + `__init__.py` + `CLAUDE.md`. 27 methods
redistributed, 0 renamed, 0 relocated out of the package. Oracle: 28 pool generators, roughly 884
artifacts.

## Constitution Check

*GATE: evaluated before Phase 0, re-evaluated after Phase 1 design (see the re-check at the end).*

- **I. Accessibility-First Viewports**: **N/A** - this feature ships no UI; the L7R Toolkit webapp
  is untouched.
- **II. Bold, Intentional Design**: **N/A** - no new UI surfaces.
- **III. Pool Data Conventions**: **N/A** - no generated content of a recurring kind is added or
  modified. `pool/` is read as an oracle and must come back byte-identical; nothing is written to it.
- **IV. One Canonical Home for GM Source**: **N/A** - no SOURCE blocks are added or moved.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: **PASS** - no task in this plan touches
  content inside SOURCE markers. The two documents edited (`settlement/CLAUDE.md`,
  `settlement/city/CLAUDE.md`) contain none.
- **VI. Verify Before Reporting Done**: **PASS** - every task carries its verification. The cheap
  prefix (`ruff format`, `ruff check`, `mypy`) then the WHOLE affected test files (never a `-k`
  subset), then the byte-identity sweep, then one backgrounded `make done` read by its log tail.
  No delegated work in this feature, so nothing to spot-check on a subagent's behalf.
- **VII. De-Localized Generation by Default**: **N/A** - no pool content generated.
- **VIII. Direct Voice Over Framing Distance**: **N/A** - no in-world content written.
- **IX. Setting Integration**: **N/A** - no setting details asserted, no new named figures.
- **X. Python Discipline (NON-NEGOTIABLE)**: **PASS**, and this principle IS the feature.
  - `ruff check` + `ruff format --check` + `mypy --strict`: in the gate, run as the cheap prefix
    before the expensive half.
  - Red-green TDD: the composed-surface guard (FR-003) is written and observed FAILING - twice, once
    per assertion - before the split lands. Recorded in tasks.md with the failure text, per the
    contract.
  - `pytest --cov-fail-under=100` on pure-logic packages, and the `settlement/` ratchet at its
    floor. Clause 12 (functions at human scale) is US2's whole subject; clause 13 (files at human
    scale) is US1's.
  - Clause 14 (derive, don't maintain or split) was evaluated and **does not apply**: `city.py` is
    not roster-shaped. Its 27 members are hand-written drawing logic, each with distinct behavior -
    nothing here restates what code elsewhere declares, so there is no surface to derive. The
    census that clause 14 asks for is instead spent on the composed-mixin surface (contract), which
    is what the guard test pins. Recorded in research R2 so a later reader does not mistake the
    non-application for an oversight.
  - Every new file lands well under 1,000 raw lines by construction; that is the point.
- **XI. Japanese Authenticity (NON-NEGOTIABLE)**: **N/A** - no kanji, names or in-world titles are
  generated. Existing labels move verbatim inside method bodies.
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: **N/A**, and the justification is
  unusually strong. The gate asks whether the feature changes what a generator ASSERTS ABOUT THE
  WORLD. This feature's binding success criterion is that every rendered artifact is
  BYTE-IDENTICAL - a strictly stronger claim than "the grounding is unchanged", and one that is
  mechanically checked seven times rather than argued. There is no element added or changed to
  research in Phase 0, and the closing bookend's question ("does the rendered PNG still match the
  Phase 0 findings?") is answered by the sweep: the PNGs are the same bytes. If any sweep were to
  come back non-empty, this gate would immediately stop being N/A - a changed artifact means the
  refactor changed a drawing, and the feature is red until that is undone rather than re-grounded.

No gate is DEFERRED; the Complexity Tracking table is therefore empty and omitted.

## Project Structure

### Documentation (this feature)

```text
specs/113-city-package/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0
├── data-model.md        # Phase 1 - the partition, method by method
├── quickstart.md        # Phase 1 - how to run the oracle
├── contracts/
│   └── mixin-surface.md # Phase 1 - the composed CityMixin contract
├── split_city.py        # Phase 1 - the one-shot transformer (adapted from 112)
└── tasks.md             # Phase 2, by /speckit-tasks
```

### Source Code

All paths relative to `.claude/skills/diagram/`, written POST-reorg (the peer session's tip).

```text
settlement/
├── CLAUDE.md            # MODIFIED - the city.py row becomes rows + a pointer to the sub-index
├── core.py              # UNCHANGED, byte for byte - `from .city import CityMixin` still resolves
├── city.py              # DELETED by this feature
└── city/                # NEW
    ├── __init__.py      # composed `class CityMixin(WallsMixin, MoatMixin, ...)`
    ├── CLAUDE.md        # NEW - the "Look here when" sub-index
    ├── walls.py         # ~494 lines - ring road, wall, towers, wall walk
    ├── moat.py          # ~240 - moat, water gates, sluices, the inwall drain
    ├── canals.py        # ~210 - canal, towpath, the farmland ring
    ├── waterfront.py    # ~258 - quay, aqueduct, dock, jetty, log boom
    ├── bridges.py       # ~331 - bridge, bridges, channel footbridges
    └── civic.py         # ~21 - the governor's mansion, isolated on purpose (research R1)

tests/settlement/
└── test_city.py         # MODIFIED - gains the composed-surface guard

Makefile                 # possibly MODIFIED - SETTLEMENT_COV_FLOOR, raised only if measured higher
```

**Structure Decision**: a sub-package under `settlement/`, exactly mirroring `settlement/fields/`
(feature 112). That precedent settles every structural question this feature would otherwise have
to re-litigate: the composed-mixin `__init__.py` that keeps `core.py` still, the two-dot
`TYPE_CHECKING` import of `Settlement`, the per-module docstring naming its subsystem, and the
`CLAUDE.md` sub-index. It also settles the tooling question - the peer session verified on its own
tip that `settlement/fields/` remains inside `gencache.engine_files()` and that the coverage globs
stayed glob-shaped (`*/settlement/*`), so a nested `settlement/city/` is walked, fingerprinted and
measured with no plumbing change from this feature.

## Phase 0: Research

Output: [research.md](research.md). The questions this feature actually had to settle, none of them
about "which library":

- **R1** - where the seams fall (settled by the call graph, not reading order), and the one method
  that has no natural home
- **R2** - why clause 14 (derive, don't split) does not apply here
- **R3** - the oracle: which corpus, captured how, and why not the committed manifests
- **R4** - stage sequencing, and why the sweep runs seven times rather than twice
- **R5** - the peer-session interaction: what changed from feature 112's R14 and what did not
- **R6** - what the transformer must carry that a naive slice drops
- **R7** - the coverage ratchet: what this split can and cannot move

## Phase 1: Design and Contracts

Outputs:

- **[data-model.md](data-model.md)** - the partition as five tables, one row per method, with its
  current line span and the reason it sits where it sits. This is the transformer's input and the
  document a reviewer checks the transformer against.
- **[contracts/mixin-surface.md](contracts/mixin-surface.md)** - the 27-name composed surface, the
  three guard assertions, the red-green requirement, and an explicit list of what is deliberately
  NOT contracted (which submodule holds a method; Stage 2's extracted helpers).
- **[quickstart.md](quickstart.md)** - the runnable harness: baseline capture, sweep-and-compare,
  clone-cleanliness check, the gate, the guard-fires proof, and the size measurement.
- **split_city.py** - the one-shot transformer, adapted from `specs/112-fields-package/split_fields.py`.

**Agent context update**: the `<!-- SPECKIT START -->` / `<!-- SPECKIT END -->` markers do not exist
in this repo's `CLAUDE.md` - the project deliberately tracks no single "active plan" pointer, since
a hardcoded one goes stale as features come and go (root `CLAUDE.md`, last paragraph). No update is
made, and this note records that the step was considered rather than skipped.

## Post-Design Constitution Re-Check

Re-evaluated after the Phase 1 artifacts were written. No gate changed status. Two things worth
recording from the design pass:

- The design pass CHANGED the partition the spec sketched, from five modules to six. Computing the
  intra-class call graph (rather than trusting reading order) confirmed the five seams, and
  confirmed one method belongs to none of them: `governor_mansion` calls `self.manor(...)`, making
  it a structure rather than city infrastructure. It gets its own `civic.py`, with folding it into
  `settlement/castle_civic.py` recorded as a follow-up. This is a placement decision inside one
  package - it touches no gate - but it is recorded here because the spec said five and the
  delivered package has six.
- Principle X clause 12's bar is "a few hundred logical statements", measured in statements, not
  raw lines. `city_wall` at 339 raw lines is under that bar by the letter, so US2 is driven by
  FR-009's own ~150-line house rule rather than by the constitution's outer limit. The plan states
  this explicitly so US2 is not later read as a constitutional requirement it is not - it is
  ordinary hygiene the GM asked for, and the byte-identity constraint is what keeps it honest.
