# Implementation Plan: settlement/_geom.py -> settlement/_geom/ Package Split

**Branch**: none - `export SPECIFY_FEATURE=117-geom-package` (this project stays on `main`) |
**Date**: 2026-08-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/117-geom-package/spec.md`

## Summary

Move the 89 module-level members of `settlement/_geom.py` (1,303 lines) into eleven submodules of a
`settlement/_geom/` package, verbatim, by a one-shot AST transformer that refuses on any partition
error. The package `__init__.py` re-exports the whole surface with star imports plus an `as`-alias
block for the six underscore names, so all 41 importing engine files, both `tools/` consumers and
`settlement/__init__.py`'s own roster keep resolving with zero edits. Proof is a pool-wide
byte-identity oracle against a baseline already captured from a detached worktree, a surface guard
proven red first, and a green `make done`. The only consumer change in the feature is
`tools/cache_audit.py`, whose mutation target is a file path that is about to become a directory.

## Technical Context

**Language/Version**: Python 3.14 (deferred annotation evaluation is load-bearing here - see
research R6)

**Primary Dependencies**: none new. `ruff`, `mypy --strict`, `pytest` + `pytest-xdist` + coverage,
all already gating this skill.

**Storage**: N/A - the artifacts are the `pool/**` map files, which must not change.

**Testing**: `pytest` (`tests/settlement/test_geom.py` for the module; `make done` for the gate);
`python3 -m pipeline.regen --no-cache --frozen-ok` as the byte-identity oracle;
`python3 -m tools.cache_audit` for the moved audit target.

**Target Platform**: the dev container, run from the session clone.

**Project Type**: internal library refactor - the Mode B diagram engine.

**Performance Goals**: unchanged. A pure move executes the same statements; the gate's own budget
guard (`GEN_TIME_BUDGETS`) is the backstop if that is ever untrue.

**Constraints**: byte-identical `pool/**` output; no consumer edits except the audit target; the
`SETTLEMENT_COV_FLOOR` ratchet is not lowered.

**Scale/Scope**: 1,303 lines, 89 members, 11 new submodules, 41 importing engine files left
untouched.

## Constitution Check

*GATE: passed before Phase 0; re-checked after Phase 1 (see "Post-design re-check" below).*

- **I. Accessibility-First Viewports**: N/A - no UI. This feature ships no HTML, CSS or template.
- **II. Bold, Intentional Design**: N/A - no new UI surface.
- **III. Pool Data Conventions**: N/A - generates no pool content. The existing `pool/` artifacts are
  the oracle and must not change.
- **IV. One Canonical Home for GM Source**: N/A - no SOURCE blocks are added or moved.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: **PASS** - no task touches any SOURCE marker;
  the feature changes only Python and its own docs.
- **VI. Verify Before Reporting Done**: **PASS** - each task in `tasks.md` names its verification
  command. The feature's own bar: the transformer's refusals, the surface guard proven red, the
  893-artifact hash diff, a green `make done`, and a passing `tools.cache_audit` run.
- **VII. De-Localized Generation by Default**: N/A - generates no content.
- **VIII. Direct Voice Over Framing Distance**: N/A - writes no in-world content.
- **IX. Setting Integration**: N/A - no setting claims, no named figures.
- **X. Python Discipline (NON-NEGOTIABLE)**: **PASS**, and it is the principle this feature exists to
  serve.
  - `ruff check` + `ruff format --check` + `mypy --strict` + `pytest --cov` all run via `make done`.
  - **Clause 12 (functions)**: already compliant and stays so. Largest member after the split is
    `ward_interior` (58 raw lines / 34 statements). No function is created, split or grown.
  - **Clause 13 (files)**: this is the debt being paid. Largest post-split file is projected at ~265
    raw lines against 1,303, and the package gets its `CLAUDE.md` index. `tests/settlement/
    test_geom.py` (353) stays whole - under the bar.
  - **Clause 14 (rosters)**: applied to the new `__init__.py`. A hand-written re-export roster for 89
    names is precisely the roster shape clause 14 names, so the surface is DERIVED with star imports
    and the safety property moves into a guard test proven to fire (research R2, contracts/
    surface.md). `specs/027-init-star-imports/` is the exemplar being followed.
  - **Red-green TDD**: applies to the two guard assertions, which are the only new behavior. Both are
    demonstrated red before they are trusted (tasks T11-T12). The 89 moved members are a MOVE, not
    new behavior - their tests already exist and must keep passing unchanged, which is the stronger
    statement.
  - No new `print` in a production path, no swallowed exceptions, no new configuration.
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: **N/A, and deliberately so.** This feature
  changes nothing a generator asserts about the world: no element is added, changed or dropped, and
  the closing bookend's question ("does the rendered artifact still match the finding?") is answered
  by a stronger instrument than a re-read of the PNG - every one of the 893 artifacts must be
  byte-identical. A move that satisfies that cannot have changed a depiction. The researched
  grounding blocks the file carries are preserved verbatim and are checked mechanically (FR-011).
- **XIII. No Known Regressions (NON-NEGOTIABLE)**: **PASS**.
  - **Baseline, measured before any judging**: taken in a detached worktree
    (`git worktree add --detach /tmp/base117 HEAD`), never a stash. Command:
    `python3 -m pipeline.regen --no-cache --frozen-ok pool/*/*.gen.py`, then `sha256sum` over every
    `pool/**` `.json`/`.svg`/`.png`. **Result: 28/28 generators REGENERATED, exit 0, 893 artifacts
    hashed to `/tmp/117-baseline-hashes.txt`.** Captured 2026-08-17, before a line of the split was
    written.
  - **Zero new failures at merge**: the pass condition is an EMPTY hash diff, not a pass rate - a
    move has no licence to change one byte. The re-roll caveat about rotated residue cannot apply,
    because nothing re-rolls: no draw count changes.
  - The `make done` suite is the second bed: any test that passed before and fails after blocks the
    merge, with the three exits (fix, revert, GM waiver) and nothing else.

**Post-design re-check (after Phase 1)**: unchanged - all gates hold. The design added one consumer
edit (`tools/cache_audit.py`), which is inside Principle X's scope and carries no UI, content or
world-claim implications; it is covered by SC-005's explicit carve-out and verified by SC-008.

## Project Structure

### Documentation (this feature)

```text
specs/117-geom-package/
├── spec.md              # the feature specification
├── plan.md              # this file
├── research.md          # Phase 0: the seven decisions, each with its alternatives
├── data-model.md        # Phase 1: the partition - all 89 members, and the import DAG
├── quickstart.md        # Phase 1: the exact command sequence, including both oracle sweeps
├── contracts/
│   └── surface.md       # Phase 1: the package surface contract and its red proofs
├── checklists/
│   └── requirements.md  # spec quality checklist
├── split_geom.py        # the one-shot transformer (retired after the run, kept as the record)
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
.claude/skills/diagram/
├── settlement/
│   ├── _geom.py                 # DELETED by this feature
│   └── _geom/                   # NEW package
│       ├── __init__.py          # star re-exports + the underscore alias block
│       ├── CLAUDE.md            # the index (FR-007)
│       ├── base.py              # type aliases, main-tree guard, palette
│       ├── primitives.py        # point/segment/ring math
│       ├── overlap.py           # corner rings + collision/gap/region predicates
│       ├── indexes.py           # boxed_* prefilters, PointGrid, Indexed, indexed_grid
│       ├── seatmemo.py          # SeatMemo
│       ├── labels.py            # caption typography: ladder, sizes, tilt, quad, seat
│       ├── ways.py              # travelled ways, the kido bar, plank/deck constants
│       ├── walls.py             # walls, ward closure, torii-vs-wall clearance
│       ├── extents.py           # drawn extents read off a manifest
│       ├── curves.py            # fillets, smoothing, organic jitter, winding
│       └── village.py           # population roll + bundle pitch (isolated for a later move)
│   └── CLAUDE.md                # the `_geom` row re-points at the sub-index
├── tools/cache_audit.py         # TARGET moves off the deleted file path
├── tests/settlement/test_geom.py# gains the two surface-guard assertions
└── pyproject.toml               # per-file-ignores entry for the new __init__
```

## Phase 0: Research

Complete - see [research.md](research.md). Seven decisions, no unresolved NEEDS CLARIFICATION:

| # | question | decision |
|---|---|---|
| R1 | what partition, and on what axis | eleven modules cut by *what a session comes here to change*, not by size |
| R2 | how to re-export: mixin, roster, or stars | stars + an underscore alias block (clause 14, feature 027's idiom) |
| R3 | how the transformer slices | `(previous node's end + 1 .. this node's end)`, the 112-116 rule, so comment banks and decorators travel |
| R4 | the unnamed module-level statement | the `_assert_not_main_tree()` guard call folds into its definition's block |
| R5 | which comment banks cross a module line | exactly one bank moves; exactly four cross-reference sentences are re-pointed |
| R6 | the annotation-vs-runtime dependency trap | partition by RUNTIME references; the layering rule is what keeps it acyclic |
| R7 | where `tools/cache_audit.py`'s TARGET goes | `curves.py`, chosen on measured executed-literal data, and the audit gains a "did the mutation move anything" line so the choice stays checkable |

## Phase 1: Design

Complete - see [data-model.md](data-model.md) (the full 89-member partition and the import DAG),
[contracts/surface.md](contracts/surface.md) (the surface contract and how each half is proven red),
and [quickstart.md](quickstart.md) (the command sequence, both oracle sweeps, and the trap list).

## Complexity Tracking

No gate is DEFERRED. No constitutional deviation is requested.

The one judgment call worth recording rather than hiding: **eleven modules for 1,303 lines is finer
than the lineage's average** (116 cut 1,179 into seven). That is deliberate and follows 116's own
stated rule - modules are grouped by what a session comes here to change and are "deliberately
uneven in size", because tasks are uneven in size. The two smallest (`seatmemo.py` at ~105 and
`village.py` at ~25) exist for reasons that a size-tuned partition would destroy: `SeatMemo` is a
distinct subject with a 40-line post-mortem attached, and `village.py` isolates the members that do
not belong in this package at all so their eventual move is a one-file change - the same device 116
used for `seats.py` and `byres.py`.
