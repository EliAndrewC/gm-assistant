# Implementation Plan: settlement/rolling.py -> settlement/rolling/, and roll_village Decomposed

**Branch**: none - `SPECIFY_FEATURE=118-rolling-package` | **Date**: 2026-08-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/118-rolling-package/spec.md`

## Summary

Cut `settlement/rolling.py` (1,197 raw lines, 43 class-body members) into a `settlement/rolling/`
package of six submodules plus a composed `RollingMixin`, then decompose `roll_village` (256 lines,
the largest function in the engine) into seven named stages behind an orchestrator.

The method is the one features 112/113/114/115/116 converged on and is deliberately not re-invented:
a one-shot AST transformer that moves whole class-body members VERBATIM by slicing
`(previous member's end + 1 .. this member's end)` - the span that carries decorators, blank lines
and the comment block above a member, all three of which slicing by `node.lineno` drops silently.
Sub-mixins compose into an unchanged `RollingMixin`, so `settlement/core.py` stays byte-identical
and no consumer file changes.

The decomposition half rests on a measurement, not a hope: `roll_village` makes **zero draws from
the main `random` stream** (spec, "The safety property this feature rests on"), so preserving call
ORDER preserves output. The oracle for both halves is the same and is mechanical - regenerate every
`pool/` generator into a scratch copy and hash against a pre-change baseline.

## Technical Context

**Language/Version**: Python 3.14 (container pin)

**Primary Dependencies**: none new. `ast` + `pathlib` for the one-shot transformer; `ruff`, `mypy`,
`pytest`, `coverage` for the gate

**Storage**: N/A - source refactor only. No manifest, pool artifact or fixture changes.

**Testing**: `pytest -n auto` via `.claude/skills/diagram/Makefile`'s `done` target
(ruff -> ruff format --check -> mypy --strict -> pytest -> 100% coverage on gated modules,
`settlement/` on its `SETTLEMENT_COV_FLOOR = 94` ratchet)

**Target Platform**: the dev container; the `/diagram` skill's Mode B engine

**Project Type**: internal library package inside a Claude Code skill

**Performance Goals**: unchanged. A member move cannot alter runtime; the stage decomposition adds
seven method calls per `roll_village` invocation, against generators that run 1-20 seconds. The
`GEN_TIME_BUDGETS` guard in `tests/test_villages.py` is the standing check and must stay green.

**Constraints**: byte-identical `pool/` artifacts; `settlement/core.py` byte-unchanged; zero
consumer-file changes; no submodule over 1,000 raw lines; no function over ~150 raw lines

**Scale/Scope**: 1 source file (1,197 lines, 43 members) -> 7 files; 1 function (256 lines) ->
8 functions + 1 value class; 3 doc files updated; 1 new guard test

## Constitution Check

*GATE: passed before Phase 0; re-checked after Phase 1 - see "Post-Design Re-Check" below.*

- **I. Accessibility-First Viewports**: **N/A** - no UI. This feature touches no webapp template,
  stylesheet or page.
- **II. Bold, Intentional Design**: **N/A** - no new UI surface.
- **III. Pool Data Conventions**: **N/A** - adds and modifies no pool content. Existing pool
  artifacts must come out byte-identical, which is the opposite of a content change.
- **IV. One Canonical Home for GM Source**: **N/A** - no SOURCE blocks are added or moved.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: **PASS** - no task touches any content
  inside SOURCE markers. `l7r.md` is not read or written.
- **VI. Verify Before Reporting Done**: **PASS** - every task's verification command is named in
  `tasks.md`. The composite proof is: `make done` green, plus the byte-identity sweep, plus the
  guard test proven RED before it is trusted. Nothing is delegated, so there is no subagent output
  to spot-check.
- **VII. De-Localized Generation by Default**: **N/A** - generates no pool content.
- **VIII. Direct Voice Over Framing Distance**: **N/A** - writes no in-world content.
- **IX. Setting Integration**: **N/A** - invents no setting detail and names no new figure.
- **X. Python Discipline (NON-NEGOTIABLE)**: **PASS**, and it is the whole point of the feature.
  - `ruff check` + `ruff format --check` + `mypy --strict` + `pytest` + the coverage gate all run
    via `make done`; the cheap prefix runs first per the skill's dev-loop rule.
  - **Clause 12**: the feature REDUCES the largest function from 256 raw lines to under 150. No
    resulting function approaches the ~500-statement suspect threshold (the current worst,
    `roll_village`, is 117 statements and is being divided).
  - **Clause 13**: the feature is the clause-13 split. Every resulting file is projected under 300
    raw lines (largest: `roll.py`, ~300); measured actuals go in the spec's Status line at the end.
  - **Clause 14 (derive, don't split)**: **considered and correctly N/A.** The clause governs
    ROSTER-shaped bulk - re-export lists, `__all__` duplicates, registry rows derivable from the
    code they point at. `rolling.py` has none: all 1,197 lines are executable engine logic and its
    researched grounding comments. The one roster-shaped artifact this feature creates - the
    `__init__.py` composition - is 7 imports and one class statement, and the composed-surface
    guard's census is deliberately a SUBSET assertion (contracts/mixin-surface.md) precisely so it
    does not become a hand-maintained roster.
  - **TDD**: the one piece of new behavior is the composed-surface guard, and it is written and
    proven RED against two synthetic breakages before it is trusted. The rest of the feature adds
    no behavior by construction - which is why its oracle is byte-identity rather than new tests.
  - No new dependency, so no `requirements.in` change. No `print` in a production path, no
    swallowed exception, no new configuration.
- **XI. Japanese Authenticity**: **N/A** - surfaces no kanji.
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: **N/A, and the reason is checkable
  rather than asserted.** The gate asks whether the feature changes what a generator ASSERTS ABOUT
  THE WORLD. This one changes what a generator asserts about nothing: the byte-identity oracle
  (SC-003) is a stronger statement than the closing bookend would be, since it proves every
  rendered artifact is the same file it was, not merely still defensible. Where a historical
  finding is recorded in a comment (the bundle-pitch post-mortem, the windbreak derivation, the
  threshing-yard sun research), FR-004 requires it to move verbatim, and the comment-line census in
  quickstart step 6 is what enforces that.
- **XIII. No Known Regressions (NON-NEGOTIABLE)**: **PASS**, with the baseline already taken.
  - **Baseline command**: `make done` from `.claude/skills/diagram/`, on unmodified code.
  - **Baseline number, measured 2026-08-17 at `15fac91`**: **exit 0, 3263 passed in 119.77s**,
    coverage gates green.
  - The baseline was taken in the clone at a clean, unmodified HEAD before any edit, which is the
    property `--detach` exists to guarantee; if any re-baseline is needed mid-feature it MUST use
    `git worktree add --detach /tmp/base HEAD`, never a stash (a stash mutates the tree under any
    review agent reading it).
  - **Zero new failures at merge**, and for this feature the bar is stricter than the constitution's
    minimum: byte-identity of every pool artifact. A single differing byte is a regression with the
    same three exits (fix, revert, GM waiver) and blocks `sync-with-main.sh done`.
  - **The re-roll caveat does not apply.** Nothing here changes how many draws a gen takes, so
    per-artifact comparison survives intact and there is no rotated residue to diagnose.

**No gate is DEFERRED. No Complexity Tracking entry is required.**

### Post-Design Re-Check (after Phase 1)

Re-evaluated against `data-model.md` and `contracts/mixin-surface.md`: no gate changes status. The
design introduces one new class (`_MarginFrame`, a frozen dataclass of eight floats plus a mapping
method) and one new test; neither touches a previously N/A principle. Clause 13 is re-confirmed
against the measured partition - the six modules' member spans are 256 / 254 / 214 / 194 / 144 /
120 lines, so no file can reach 1,000 even after headers and the stage-decomposition overhead.

## Project Structure

### Documentation (this feature)

```text
specs/118-rolling-package/
├── plan.md                  # this file
├── spec.md
├── research.md              # Phase 0: the six decisions, each with its alternatives
├── data-model.md            # Phase 1: the partition, member by member, and the stage table
├── quickstart.md            # Phase 1: the runbook, including the byte-identity oracle
├── contracts/
│   └── mixin-surface.md     # the composed-surface contract the guard test implements
├── checklists/
│   └── requirements.md
├── split_rolling.py         # the one-shot transformer (adapted from 116)
└── tasks.md                 # Phase 2 (/speckit-tasks)
```

### Source Code

```text
.claude/skills/diagram/settlement/
├── core.py                  # UNCHANGED (byte-identical) - still `from .rolling import RollingMixin`
├── rolling.py               # DELETED
└── rolling/                 # NEW
    ├── __init__.py          # RollingMixin = composition of the six sub-mixins; no members of its own
    ├── CLAUDE.md            # the package index: one "look here when" row per submodule
    ├── roll.py              # roll_village + its seven stages + _MarginFrame
    ├── seeds.py             # the settlement-FORM seed generators and the perimeter ring
    ├── bundle.py            # what a homestead bundle IS - pure geometry, no placement, no drawing
    ├── fit.py               # may a bundle stand here? every keep-out predicate
    ├── place.py             # find a spot and commit to it: the spiral search and the two slides
    └── farmsteads.py        # the deferred flush: what actually gets DRAWN, and in what order

.claude/skills/diagram/tests/settlement/
└── test_rolling.py          # +1 guard test (composed surface); the existing 343 lines unchanged

.claude/skills/diagram/
├── settlement/CLAUDE.md              # the rolling.py row -> the package
├── settlement/civic_grounds/CLAUDE.md # stops citing rolling.py (1,197) as a live unsplit file
└── future-work.md                     # the clause-12 candidate section closed, its finding kept
```

## Phase 0: Research

See [research.md](research.md). Six decisions, all resolved - no NEEDS CLARIFICATION survives into
Phase 1.

## Phase 1: Design

See [data-model.md](data-model.md) (the partition and the stage table),
[contracts/mixin-surface.md](contracts/mixin-surface.md) (the one contract a split can break
silently) and [quickstart.md](quickstart.md) (the runbook and the oracle).

**Agent context**: `.claude/skills/diagram/settlement/CLAUDE.md` is the auto-loading index a session
reads when it edits this directory; its `rolling.py` row is updated in the same change, which is
this project's equivalent of the template's "update agent context" step. The root `CLAUDE.md` needs
no edit - it points at `settlement/CLAUDE.md`, not at individual modules.

## Sequencing, and why it is this order

The two halves ship as two commits, split first, because that ordering makes the oracle diagnostic
rather than merely pass/fail. If the split and the decomposition land together and one artifact
byte moves, the suspect set is 43 moved members plus a rewritten function. Split first, sweep,
decompose, sweep again, and a failure names its own cause.
