# Implementation Plan: One `l7r` Namespace, `l7r.diagram`, and `sitegen`

**Branch**: none - this project stays on `main`. `SPECIFY_FEATURE=119-l7r-diagram-namespace`,
`SPECIFY_FEATURE_DIRECTORY=specs/119-l7r-diagram-namespace` | **Date**: 2026-08-17 |
**Spec**: [spec.md](spec.md)

## Summary

Make `l7r` a PEP 420 namespace shared by the toolkit webapp and the diagram engine, move the engine
under `l7r.diagram`, and give the tiers above hamlet a shared `sitegen` package to build on. Three
landings, each with its own gate and its own byte-identity proof: convert the webapp's `l7r` to a
namespace portion; move the eight engine units into `l7r/diagram/`; extract the ~110 tier-agnostic
lines out of `hamletgen/`.

The correctness argument is mechanical rather than reviewed: all three landings are
output-preserving by construction, so **every `pool/` artifact must regenerate byte-identically**.
Any drift is a bug, not a trade-off.

## Technical Context

**Language/Version**: Python 3.14 (both trees pin `python_version = "3.14"`, `target-version = "py314"`)

**Primary Dependencies**: CherryPy + Jinja2 (webapp); no new runtime dependency anywhere. Tooling:
ruff, mypy 2.3.0, pytest + pytest-xdist + pytest-cov, coverage.

**Storage**: filesystem only - `pool/` map artifacts, gitignored renders, the gate cache.

**Testing**: pytest in both trees. Diagram: `make done` = ruff + format + `mypy --strict` + pytest
(`-n auto`) + 100% coverage on every measured module except the `settlement/` ratchet floor (94).
Webapp: `make done` = ruff + mypy + pytest with `--cov-fail-under=100`.

**Target Platform**: Linux container; the webapp additionally ships to Fly via `Dockerfile`.

**Project Type**: two independent Python trees in one repo, joined only by the new shared namespace.

**Performance Goals**: none - no runtime path changes. The pool regen sweep is the long pole
(~1-20s per live map, fanned out across cpus-2).

**Constraints**: byte-identical pool artifacts; both gates green; no new failure against a
detached-worktree baseline; no compatibility shims or alias modules.

**Scale/Scope**: 245 engine-import lines across 124 files; 26 generator scripts; 39 live-doc command
references across 13 files; ~10 webapp files; ~110 lines extracted into `sitegen`.

## Constitution Check

*GATE: passed before Phase 0; re-checked after Phase 1 (below).*

- **I. Accessibility-First Viewports**: **N/A** - no route, template, stylesheet or rendered page
  changes; only how the app is imported. Not taken as licence to skip verification: landing 1
  commits to a `cherryd --import l7r.app` smoke check that loads the landing page and one sub-page,
  because "the import still works" is exactly what could break.
- **II. Bold, Intentional Design**: **N/A** - no new UI surface.
- **III. Pool Data Conventions**: **N/A** - no generated content of a recurring kind is added or
  modified. `pool/` artifacts must come out byte-identical, which is the opposite of modifying them.
- **IV. One Canonical Home for GM Source**: **N/A** - no SOURCE blocks move.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: **PASS** - no task touches content inside
  SOURCE markers. The doc edits are command-path substitutions in AI-authored index files.
- **VI. Verify Before Reporting Done**: **PASS** - verification per landing is enumerated in
  "Verification per landing" below; nothing is marked done on a subagent's or a script's say-so.
- **VII. De-Localized Generation by Default**: **N/A** - no pool content generated.
- **VIII. Direct Voice Over Framing Distance**: **N/A** - no in-world content written.
- **IX. Setting Integration**: **N/A** - no setting details asserted; no new named figures.
- **X. Python Discipline (NON-NEGOTIABLE)**: **PASS** - both gates run in full. New code is three
  small `sitegen` modules plus two guard tests, all strict-typed and 100%-covered from the start.
  The guard tests are red-green: each is observed to FAIL against a real `__init__.py` before being
  trusted. No file approaches clause 13; `sitegen`'s largest module is `geom.py` at 94 lines.
  Clause 12 is untouched - no function is created, split or grown; members move verbatim.
- **XI. Japanese Authenticity (NON-NEGOTIABLE)**: **N/A** - no kanji, names or in-world text.
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: **N/A, and provably so.** The trigger is
  a feature that changes what a generator ASSERTS ABOUT THE WORLD. A repath cannot: the closing
  bookend re-examines the rendered artifact, and here the rendered artifact is required to be
  byte-identical to the one that already passed its own bookend. Byte-identity is a strictly
  stronger check than re-reading the PNG. If any artifact drifts, this gate is no longer N/A and the
  feature stops.
- **XIII. No Known Regressions (NON-NEGOTIABLE)**: **PASS** - baseline taken on unmodified code in a
  detached worktree (`git worktree add --detach /tmp/119-base HEAD`), never a stash. Commands and
  measured numbers recorded in "Baseline" below before any landing is judged. Zero new failures is
  the merge bar; pre-existing failures are ledgered, not fixed here.

**No Complexity Tracking entries** - no gate is DEFERRED and no violation needs justification.

## Baseline (Principle XIII) - recorded before any file moves

| baseline | command | result |
|---|---|---|
| diagram gate | `cd /tmp/119-base/.claude/skills/diagram && make done` | *filled in at task T001* |
| webapp gate | `cd /tmp/119-base/webapp && make done` | *filled in at task T001* |
| pool artifacts | regen every gen with `--frozen-ok` in a scratch copy; `sha256` every `pool/**` artifact into `baseline-hashes.txt` | *filled in at task T002* |

The hash manifest is the oracle for all three landings. It is taken ONCE, against unmodified code,
and every landing compares against that original - never against the previous landing's output.

## Project Structure

### Documentation (this feature)

```text
specs/119-l7r-diagram-namespace/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0 - R1..R10
├── data-model.md        # Phase 1 - the entities and their invariants
├── quickstart.md        # Phase 1 - how to run/verify the result
├── contracts/
│   └── import-surface.md    # the public import contract before/after
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code

**Before**

```text
webapp/
├── l7r/                          # REGULAR package (__init__.py mounts the CherryPy tree)
│   ├── __init__.py               #   <- the blocker
│   └── app.py  names.py  places.py  dreams.py  ...
└── conftest.py  Makefile  Dockerfile  pyproject.toml

.claude/skills/diagram/           # <- sys.path root
├── settlement/  check_village/  waterfields/  hamletgen/  pipeline/  tools/
├── compound.py  citybudget.py
└── pool/  tests/  Makefile  pyproject.toml  CLAUDE.md  SKILL.md
```

**After**

```text
webapp/                           # <- sys.path root
├── l7r/                          # NAMESPACE portion (no __init__.py)
│   └── app.py  names.py  places.py  dreams.py  ...        -> l7r.app, l7r.names, ...
└── conftest.py  Makefile  Dockerfile  pyproject.toml

.claude/skills/diagram/           # <- sys.path root (unchanged)
├── l7r/                          # NAMESPACE portion (no __init__.py)
│   └── diagram/                  # regular package (__init__.py)
│       ├── settlement/  check_village/  waterfields/  hamletgen/  pipeline/  tools/
│       ├── sitegen/              # NEW - types.py, geom.py, jobs.py
│       └── compound.py  citybudget.py
└── pool/  tests/  Makefile  pyproject.toml  CLAUDE.md  SKILL.md
```

**Structure Decision**: `pool/`, `tests/`, `Makefile` and `pyproject.toml` deliberately stay at the
skill root. Three reasons, each load-bearing:

1. Every pool generator computes `SKILL = dirname(dirname(HERE))` from its own location. Because
   `pool/` does not move, that arithmetic stays correct and **every generator's bootstrap block is
   byte-unchanged** - only its single import line differs. Moving `pool/` under `l7r/` would
   silently point 26 bootstraps one directory wrong.
2. The skill directory remains the `sys.path` root, so the namespace portion sits directly on it,
   which is what makes the two-portion merge work.
3. The diagram gate stays the diagram gate. Sharing a namespace is not sharing a build.

## The three landings

### Landing 1 - webapp namespace conversion

Delete `webapp/l7r/__init__.py`; move its docstring to `l7r/app.py` where it becomes literally true.
Repoint the seven consumers of the bare-import side effect (research R9): Dockerfile CMD, Makefile
`serve` and the `opcache` refresh line, `conftest.py`, five character tests. `tests/test_app.py`'s
`from l7r import app as app_module` and `pytest --cov=l7r` are unchanged.

Add `webapp/tests/test_namespace_portion.py`: asserts `l7r.__file__ is None`, proven RED by
temporarily creating `webapp/l7r/__init__.py`.

**Gate**: `cd webapp && make done`, plus the serve smoke check.

### Landing 2 - the engine under `l7r.diagram`

`git mv` the eight engine units into `l7r/diagram/`. Create `l7r/diagram/__init__.py`; create NO
`l7r/__init__.py`. Delete the old trees outright (a surviving directory is how one file gets two
module identities - research R2).

Repath, in this order, each verified by grep before moving on:

1. the 245 absolute engine imports (`from settlement` -> `from l7r.diagram.settlement`, etc.);
   intra-package relative imports (`from .geom import`) are untouched by construction;
2. `pyproject.toml` - ruff per-file-ignores (5 entries), mypy `files`, coverage `source`, coverage
   `omit`; and the Makefile's coverage include/omit globs;
3. the 26 generator import lines in `pool/` and `wip/` - **the bootstrap block must diff clean**;
4. the 39 live-doc command references across 13 files. Historical `specs/` artifacts are left alone
   (research R6).

Add `tests/test_namespace_portion.py` in the skill tree, same assertion, proven RED the same way.

**Gate**: `make done` in the skill dir + the pool byte-identity sweep against the R10 baseline.

### Landing 3 - `sitegen`

Create `l7r/diagram/sitegen/` with `types.py` (`Pt`, `Poly`, `SQ_FT_PER_ACRE`), `geom.py` (the
94-line helper set, verbatim) and `jobs.py` (`default_jobs`, verbatim), plus a `CLAUDE.md` index
whose first line states the membership rule. Repoint `hamletgen`'s eight intra-package importers.
`hamletgen/__init__.py` keeps re-exporting the same names, so its public surface is unchanged and no
generator moves.

Add a test asserting the one-way import direction: nothing under `sitegen/` may import `hamletgen`.

Record the standing rule where a village-tier session will read it: `migration-plan.md` section 5
(the architectural question, now ANSWERED) and section 8 (the ordering, if villages jump the
archetypes), and `hamletgen/CLAUDE.md`.

**Gate**: `make done` + the same byte-identity sweep against the same original baseline.

## Verification per landing (Principle VI)

| landing | verification |
|---|---|
| 1 | `webapp make done` green; `cherryd --import l7r.app` serves and two pages render; guard test proven RED then green |
| 2 | diagram `make done` green; every pool artifact byte-identical to the R10 baseline (frozen included); `git diff` on any generator shows only its import line; grep proves zero stale module paths in Python and in live docs; guard test proven RED then green |
| 3 | diagram `make done` green; byte-identity again vs the ORIGINAL baseline; `sitegen` modules contain no tier concept; import-direction test proven RED then green |
| all | both gates re-run at the end; zero new failures vs baseline |

Nothing here is delegated to a subagent, so there is no delegated work to spot-check. No
`settlement-review` pass is required: a change that cannot alter output has a mechanical oracle
(the same reasoning feature 118 recorded).

## Risks and how each is closed

| risk | closure |
|---|---|
| A stray `__init__.py` re-added later silently unmakes the namespace | guard test in each portion, each proven RED against a real file |
| One file reachable under two module identities | old trees deleted (not copied); mypy would report the duplicate; grep proves no stale path survives |
| `__pycache__` shadowing the old layout | sweep runs in a scratch copy taken from the committed tree; caches cleared before the gate |
| A generator's bootstrap silently pointing one level wrong | `pool/` does not move; the bootstrap block is diffed and must be byte-unchanged |
| mypy needing `explicit_package_bases` | measured as NOT needed (R2); available and recorded if the real tree disagrees |
| Three sibling diagram sessions editing the same files | the diff is repo-wide and textual, so land promptly: commit and `sync-with-main.sh` after each landing rather than holding all three |
| Landing 3's seam being wrong | it is deliberately conservative (~110 lines of zero-tier-content code); anything arguable stays in `hamletgen` until the village tier gives it a second consumer |

## Post-Design Constitution Re-Check

Re-evaluated after Phase 1. No gate changed status. Design added no UI, no pool content, no setting
assertion and no new dependency; it added three small modules, three guard tests, and a
documentation rule. Principle X's obligations are met by construction (both gates unchanged and
still enforced); Principle XIII's baseline is defined with commands rather than intentions; Principle
XII remains N/A on the strength of the byte-identity requirement, which is the stronger check.
