# Contract: the `settlement._geom` package surface

The split is meant to be invisible to everything above `settlement/_geom/__init__.py`. This file
states what "invisible" means precisely, and how each half is proven rather than asserted.

## C1. Every pre-split name still resolves on `settlement._geom`

**The census**: the 89 module-level names of the pre-split file, captured by AST before the move and
frozen into the test as a literal tuple.

**The assertion**: a SUBSET check - `missing = [n for n in CENSUS if not hasattr(settlement._geom, n)]`
must be empty. A subset rather than an equality, so adding a helper later needs no bookkeeping (116's
FR-003 rationale, and 114's before it).

**Why it is needed even with a green suite**: a member the transformer drops produces a package that
imports cleanly, type-checks cleanly, and fails only when whichever caller needs it happens to run.
This file has 12 members with no test of their own and several reached only by the frozen city wing,
so the suite alone is not a complete census.

**Red proof (required before it is trusted)**: delete one member from a submodule, run the test,
observe it name that member. Recorded in `tasks.md` T014 with the observed output.

**It also bit for real, unprompted, on its first run**: the aliased block had six of the seven
underscore names, and the census named `_VILLAGE_POP_DIST` - a name that resolved before the split
and did not after - on a package that imported cleanly and passed every other test in the suite. See
`research.md` R2.

## C2. No public name is bound twice across the submodules

**The assertion**: for every public name on `settlement._geom`, the set of submodules that define it
has exactly one element - equivalently, no two submodules bind the same public name to different
objects.

**Why this is new to this feature.** Features 025 and 112-116 composed a MIXIN, where a duplicate
name is at least *reachable* through the MRO and their guard caught it structurally. A star-import
surface has no MRO: `from .a import *` followed by `from .b import *` silently keeps `b`'s binding,
with no error from Python, ruff or `mypy --strict`. The consequence is a working import and one dead
implementation - the same failure `tests/check_village/test_surface.py` guards for the feature-027
package, which is the precedent this test follows.

**Red proof**: bind an existing name (e.g. `seg_dist`) in a second submodule, run the test, observe
the collision half fire naming the name and both modules. Recorded in `tasks.md` T12.

## C3. The import-time main-tree guard still fires

**The assertion**: `settlement._geom.base` runs `_assert_not_main_tree()` at import, and the function
remains importable as `settlement._assert_not_main_tree` (its two consumers spell it that way).

**Why it is called out**: the guard's call statement is the one UNNAMED top-level statement in the
file (research R4), the only member a name-keyed partition can drop without noticing, and its failure
mode is silence - every test already runs inside a clone, so a disarmed guard looks exactly like a
working one until someone runs a generator in main's tree. The existing
`test_assert_not_main_tree_*` tests in `tests/settlement/test_geom.py` already exercise the FUNCTION
with synthetic paths and keep passing unchanged; what this contract adds is that the CALL survived,
checked by reading `settlement/_geom/base.py` for the bare call rather than by trusting the move.

## C4. No consumer changes

**The assertion**, checked by `git diff --stat` at the end of the feature: the only files touched
outside `settlement/_geom/` and `specs/117-geom-package/` are

- `settlement/CLAUDE.md` (the `_geom` row re-points at the sub-index),
- `tests/settlement/test_geom.py` (gains C1-C3),
- `tools/cache_audit.py` (`TARGET` + its comment + the `moved N` line),
- `pyproject.toml` (the per-file-ignores entry),
- `.claude/skills/diagram/CLAUDE.md` if the `settlement/` row needs it.

Specifically NOT touched: any of the 41 engine files that import from `_geom`, any pool generator,
`wip/shiro-daika.gen.py`, `tools/scatter_audit.py` (which imports the submodule path
`settlement._geom` directly), `check_village/common_01_geometry.py`, `hamletgen/*`, and
`settlement/__init__.py`'s 58-line `_geom` roster.

## C5. Byte-identical output

**The assertion**: `sha256sum` over all 893 `pool/**` artifacts matches `/tmp/117-baseline-hashes.txt`
exactly. Baseline captured 2026-08-17 from a detached worktree at the pre-split HEAD, 28/28
generators REGENERATED, exit 0. Both sweeps run
`python3 -m pipeline.regen --no-cache --frozen-ok pool/*/*.gen.py`, the frozen legacy maps included -
they carry the city and town wings, which are the only exercise `ward_interior`, `wall_runs`,
`torii_wall_conflicts`, `tower_quad` and `kido_bar_deg` get.

This is the contract that makes all the others cheap: a move that changes no byte of 893 artifacts,
across 28 generators covering every scale tier, has not changed behavior.
