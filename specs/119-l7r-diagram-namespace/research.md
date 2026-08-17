# Phase 0 Research: One `l7r` Namespace, `l7r.diagram`, and `sitegen`

**Feature**: 119-l7r-diagram-namespace | **Date**: 2026-08-17

Every finding below was measured in this clone or in a scratch tree. Where a probe refuted
something the spec asserted, the refutation is recorded and the spec was corrected - not quietly
worked around.

---

## R1. PEP 420 namespace packages do what the GM asked for

**Decision**: use implicit namespace packages. `l7r/` carries no `__init__.py` in either location.

**Measured** (scratch tree, two roots, both on `PYTHONPATH`):

```
l7r.__file__ = None
paths = ['.../rootA/l7r', '.../rootB/l7r']
pkg.f(1) = 2 | other.VALUE = from root B
```

`l7r.diagram.pkg` from root A and `l7r.other` from root B resolve in one interpreter. This is the
capability the feature exists to create, and it is confirmed before any code moves.

**`l7r.__file__ is None` is the discriminator.** A regular package's `__file__` is its
`__init__.py`; a namespace's is `None`. That single expression is what the guard tests assert, and
it is why the guard is possible at all.

**Alternatives considered and rejected**:

- *Two separate regular packages both named `l7r`, never co-resident on `sys.path`.* Works today by
  accident and fails silently the first time anything puts both roots on the path - which is
  precisely the webapp-renders-a-map scenario that motivates the shared prefix. Rejected: it makes
  the collision arrive later and at a worse moment.
- *Nesting the diagram engine inside `webapp/l7r/diagram/`.* Gets a real `l7r.diagram` with no
  namespace mechanics at all, but drags the engine out of the skill directory away from `pool/`,
  its `Makefile` and its `pyproject.toml`, and entangles two independent gates. Rejected.
- *A distinct root name (`l7r_diagram`).* Zero collision, zero webapp surgery - but it is not the
  shared parent the GM asked for, and two roots named `l7r*` that cannot merge is the confusion the
  prefix was supposed to remove. Rejected.

## R2. mypy --strict resolves a namespace portion with no configuration change

**Measured** (mypy 2.3.0, `files = ["l7r"]`, no other settings):

```
Success: no issues found in 2 source files
```

Adding `explicit_package_bases = true` + `mypy_path = "."` also succeeds, so it is available if the
real tree surfaces a duplicate-module error, but it is **not** required up front.

**Decision**: repath `[tool.mypy] files` to the `l7r/diagram/...` paths, and add
`explicit_package_bases` where the real tree demands it.

**The real tree DID demand it, and the probe did not predict it - recorded rather than smoothed
over.** The scratch tree passed because `files = ["l7r"]` names the package explicitly. The webapp
runs `mypy .` (the whole directory), which walks up from `l7r/auth_routes.py`, finds no
`__init__.py` to stop at, and reports:

```
l7r/auth_routes.py: error: Source file found twice under different module names:
                    "auth_routes" and "l7r.auth_routes"
```

This is precisely the duplicate-identity failure this research flagged as the residual risk, and it
appeared on landing 1 rather than landing 2. The fix is mypy's own documented resolution (b):
`explicit_package_bases = true` plus `mypy_path = "."` in `webapp/pyproject.toml`, which tells mypy
where module paths begin so each file has exactly one identity. Verified: `Success: no issues found
in 59 source files`.

**Landing 2 needed it too, and the prediction was wrong.** The reasoning above - "`files = [...]`
names packages explicitly, so expect it to be fine" - did not survive contact: the diagram tree
raised the same error on `l7r/diagram/waterfields/__init__.py` ("Source file found twice under
different module names: `diagram.waterfields` and `l7r.diagram.waterfields`"). Naming a package in
`files` does not tell mypy where module paths BEGIN; only `explicit_package_bases` + `mypy_path`
does. Both trees now carry the pair, each with the comment explaining why the obvious fix (adding
`l7r/__init__.py`) is the wrong one.

The `[tool.mypy]` block carries a comment saying all this, including "do NOT fix this by adding
`l7r/__init__.py`" - the wrong fix is the obvious one and it silently hides the other portion.

**The risk this leaves**: mypy's classic namespace failure is one file reachable under two module
identities (`settlement.core` and `l7r.diagram.settlement.core`). That can only happen if the old
tree survives the move, which the task list forbids explicitly (old directories are deleted, not
copied) and which the gate would catch as a duplicate-module error.

## R3. ruff's isort needs no `known-first-party` entry

`ruff check --select I` on `import os` / blank / `import l7r.diagram.pkg` passes. Ruff infers
first-party from the `src` root (default `.`), which is how bare `settlement` is classified today;
`l7r` sitting in the same root inherits the same treatment. **Decision**: no ruff config change for
import sorting. The gate's `ruff check` on the real tree is the verification, not this probe.

## R4. The pool byte-identity sweep already has the flag it needs

`pipeline/regen.py` skips frozen legacy maps by default and prints `FROZEN`; **`--frozen-ok`
forces them**. Feature 118 established the precedent and the reason: the frozen hand-authored maps
are most of the pool, so a sweep that honored the freeze would exercise the change almost not at
all.

**Decision**: the oracle is a regenerate-and-hash sweep with `--frozen-ok` over every `pool/`
generator, run in a scratch copy, compared against a baseline taken the same way on unmodified code
in a **detached worktree** (`git worktree add --detach`), never a stash. Run once per landing.

## R5. Nothing outside the diagram skill imports the engine

Grepped `scripts/` and `webapp/` for `from settlement`, `import check_village`, `waterfields`,
`hamletgen`, `citybudget`, `compound`: **zero hits**. The 245 import lines are all inside the skill
directory, so landing 2's blast radius is exactly the skill tree plus its docs. Render-sync does not
import the engine either - it copies rendered files.

## R6. Historical `specs/` documents are NOT rewritten - and this cuts the doc work by 60%

The spec budgeted "97 markdown command references across 44 files". Broken down by location:

| location | lines | rewritten? |
|---|---|---|
| live docs (`.claude/skills/diagram/**/CLAUDE.md`, `SKILL.md`, `migration-plan.md`, `future-work.md`, `settlements.md`, `hamletgen.md`, `docs/iteration-loop.md`, two `.claude/agents/*.md`) | **39 across 13 files** | **yes** |
| historical `specs/NNN-*/` artifacts | **~61** | **no** |

**Decision**: only live docs are updated. A `specs/113-city-package/quickstart.md` is a dated record
of how the command read when that feature shipped; rewriting it would make the record assert
something that was not true at the time. This is the same reasoning that freezes `SOURCE` blocks and
that keeps the legacy pool frozen: a point-in-time artifact is not a live mirror. The one exception
is this feature's own `specs/119-*` documents, which describe the new state by construction.

**Grep gotcha, recorded because it cost a filter**: `grep -rn ... --include='*.md' .` in this
environment emits paths **without** a `./` prefix, so `grep -v "/specs/"` does not filter them.
Use `grep -v '^specs/'`.

## R7. What is actually tier-agnostic in `hamletgen/` - the spec's estimate was wrong

The spec claimed `geom.py`, `frame.py`, the driver's `Report` / batch fan-out, and "the
tier-agnostic half of `consts.py`" - about 450 lines. **Reading the imports refutes most of that.**
The estimate had been made from filenames and line counts; the dependency edges say otherwise:

| candidate | verdict | evidence |
|---|---|---|
| `geom.py` (94 lines) | **MOVES** | imports only `settlement` primitives and `Poly`/`Pt`/`SQ_FT_PER_ACRE`; its eight consumers use `centroid`, `unit`, `crop_polys`, `crosses_disc`, `crosses_poly`, `pull_clear`, `net_acres`, `poly_area` - all pure geometry |
| `Pt`, `Poly`, `SQ_FT_PER_ACRE` | **MOVE** | type aliases and a unit conversion; zero tier content |
| `default_jobs` (5 lines) | **MOVES** | cpus-minus-2 courtesy, already the single definition three call sites share |
| `frame.py` (104 lines) | **STAYS** | all three members are `stage_*(s, plan: SitePlan)`, and it imports `CROP_MARGIN` from `hinterland`. It is three hamlet stages, not a frame library |
| `Report` (driver) | **STAYS** | wraps `SitePlan` and prints households / acres / fall / wind / sink / cluster shape / lane skeleton - a hamlet cohort row |
| `cohort`, `baseline_verdict`, `main` | **STAY** | hamlet cohort machinery over `Report` |
| `WIND_VECTORS`, `FALL_BEARINGS`, `CARDINAL_BEARINGS`, `WIND_TURNS` | **STAY, for now** | genuinely terrain doctrine that a village shares - but their comment blocks say "hamlet", and the project's move rule is VERBATIM. They move when the village tier is their second real consumer and can re-voice the comment with a reason |

**Decision**: `sitegen` v1 is **~110 lines**, not 450: `sitegen/types.py` (`Pt`, `Poly`,
`SQ_FT_PER_ACRE`), `sitegen/geom.py` (the 94-line helper set, verbatim), `sitegen/jobs.py`
(`default_jobs`, verbatim).

**Why a 110-line package is still the right deliverable.** The value is not the lines moved; it is
that (a) a destination exists with a stated membership rule, (b) the import direction is fixed and
provable - `hamletgen` may import `sitegen`, never the reverse - and (c) the village tier has
somewhere to move things TO, so the MOVE-don't-copy rule has a referent. Extracting more now would
be predicting the seam instead of observing it, which is the failure this ordering exists to avoid.

**The spec was corrected** (FR-012) rather than left standing with a claim this research disproved.

## R8. Package CLIs keep working

`check_village/` and `hamletgen/` each carry a `__main__.py`, so `python3 -m l7r.diagram.check_village`
and `python3 -m l7r.diagram.hamletgen` work by the same mechanism as today - only the dotted path
lengthens. **Decision**: no shim, no alias module, no console-script indirection. A shim would leave
two live names for one module, which is exactly the ambiguity the namespace is meant to remove; the
39 live doc lines are updated instead.

## R9. The webapp's mount side effect, and what depends on it

`webapp/l7r/__init__.py` is six lines whose payload is `from l7r import app` "side effect: mounts
CherryPy tree". Consumers of that side effect:

| consumer | change |
|---|---|
| `Dockerfile:47` `CMD ["cherryd", "--import", "l7r"]` | `--import l7r.app` |
| `webapp/Makefile:65` serve target | `--import l7r.app` |
| `webapp/conftest.py:10` `import l7r` | `import l7r.app` |
| 5 character tests (`import l7r  # force l7r to load first (chargen<->l7r circular import)`) | `import l7r.app` |
| `tests/test_app.py` `from l7r import app as app_module` (x3) | **unchanged** - submodule import from a namespace portion works |
| `webapp/Makefile:58` `pytest --cov=l7r` | **unchanged** - coverage measures the directory |
| `webapp/Makefile:103` `python3 -c "import l7r; from chargen import opcache; ..."` | `import l7r.app` |

**Decision**: `l7r.app` is the mount module; nothing new is created to hold the side effect. The
`__init__.py`'s docstring content ("Importing this package wires the CherryPy tree") is not lost -
it moves to `l7r/app.py`'s module docstring, where it is now literally true.

## R11. Three traps this feature hit, each worth the next session knowing

**A module path in a STRING LITERAL is invisible to every check the project runs.** It is not an
import, so nothing resolves it; not a test, so nothing runs it. Landing 2 hit this class three
times in code that IS exercised: `gencache` WRITES a subprocess driver containing
`"from pipeline import gencache"`; the three `test_surface.py` censuses build module names with
`importlib.import_module(f"check_village.{...}")`; `cache_audit` holds its `TARGET` as
`os.path.join("settlement", "_geom", "curves.py")`. The test suite caught all three - grep for the
import form caught none. The same class also accounts for all four entries in `plan.md`'s
pre-existing-defect ledger, dead since features 024, 111 and 025 respectively.

**`sed` treats `.` as "any character", and that silently corrupted the gate config.** Adding
`sitegen` to `pyproject.toml` ran two seds - one for the mypy path list (`"l7r/diagram/hamletgen",`)
and one for the coverage dotted list (`"l7r.diagram.hamletgen",`). The second pattern matched the
FIRST line too, rewriting a real path into a dotted non-path. mypy then reported a nonsense
"Duplicate module named `__main__`" pointing at packages that had nothing to do with it. Use `-F`,
or escape the dots, whenever a substitution's two forms differ only by separator.

**`mypy --strict` implies `--no-implicit-reexport`, so a re-export must be spelled `X as X`.**
`hamletgen/consts.py` re-exports `Pt` / `Poly` / `SQ_FT_PER_ACRE` from `sitegen.types` so that
`from .consts import Poly, Pt` keeps working inside the package; written as a plain import, every
one of those consumers fails to type-check with "does not explicitly export attribute". Same for
`driver.py`'s `default_jobs`. This is what makes a "the public surface does not change" refactor
actually not change it.

## R10. The baseline, per Principle XIII

Taken on unmodified code in a detached worktree before any file moves:

```
git worktree add --detach /tmp/119-base HEAD
# diagram: cd /tmp/119-base/.claude/skills/diagram && make done
# webapp:  cd /tmp/119-base/webapp && make done
# pool:    regen every gen with --frozen-ok into a scratch copy; hash all artifacts
```

Both gate results and the artifact hash manifest are recorded in `plan.md`'s closing notes before
any landing is judged. Anything green in the baseline and failing after is a regression that blocks
the merge; anything already failing is ledgered and is not this feature's to fix.
