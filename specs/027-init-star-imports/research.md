# Research: Collapse check_village/__init__.py to a star-import surface

**Feature**: 027-init-star-imports | **Date**: 2026-08-16

All four research items were resolved empirically in-session (probes run against mypy 2.3.0, the project's pinned Python 3.14 toolchain, in the session clone).

## R1: How the current file satisfies mypy --strict's no_implicit_reexport - and how the new one will

**Finding**: The current `__init__.py` is TWO rosters, not one. Lines 1-~1595 are the explicit import lists; lines 1596-3148 are a giant `__all__ = [...]` naming every imported symbol again. `__all__` membership is mypy's explicit-export mechanism, which is why consumers like `hamletgen.py`'s `from check_village import gate` pass strict today even though the imports are plain (non-aliased). So the file pays for every name **twice** - once in the import block, once in `__all__`.

**Probe results** (scratchpad `mypyprobe/`, mypy 2.3.0, both CLI `--strict` and config-file `strict = true` - identical behavior):

- `pkg_star/__init__.py` containing only `from .sub import *`, no `__all__`: a strict-checked consumer doing `from pkg_star import visible` **passes**. Star imports re-export public names under `no_implicit_reexport`.
- `pkg_expl/__init__.py` containing plain `from .sub import visible`: the same consumer **fails** with `Module "pkg_expl" does not explicitly export attribute "visible"`.
- Project baseline: `python3 -m mypy` in the skill dir is green in 3.6s over 46 source files.

**Decision**: Drop `__all__` entirely. Public surface re-exports via `from .<submodule> import *` (mypy-explicit per the probe). The handful of names that still need explicit import statements (the six consumed underscore names, plus any consumed names that live in `settlement`/`waterfields` rather than in package submodules) use the `from X import name as name` **aliased re-export idiom**, which mypy treats as explicit export - future-proofing them even though today's consumers of those names (tests, `site_justice.py`, `make_regressions.py`) are outside mypy's `files` list.

**Alternatives considered**: (a) Keep a pruned `__all__` of just the consumed names - rejected: it is a second roster to maintain, and the probe shows it is unnecessary. (b) A module-scoped `implicit_reexport` relaxation in pyproject - rejected: not needed once star imports carry the surface, and FR-008 treats it as last resort. Note the side effect of dropping `__all__`: `from check_village import *` semantics change from "the roster" to "star-import default" - grep shows **zero** `from check_village import *` consumers, so nothing observes the difference.

## R2: Public-name clashes across star-imported submodules

**Finding**: An import census over all 15 modules (`segments_01`...`segments_11` including the three city batteries, `segments_cross` via the same mechanism, `driver`, `registry`) found **124 distinct public names and ZERO clashes** (same name bound to different objects). Shared names (e.g. stdlib modules `math`, `json` imported by several segments) bind identical objects and are harmless namespace pollution.

**Decision**: `from .<submodule> import *` for every submodule, in the same relative order as the current explicit blocks (registry and driver last, mirroring today's file - they import from segments themselves, so this order is known-cycle-free). A permanent guard test re-runs the census and fails, naming both modules, if two submodules ever export the same public name with different objects (star shadowing is otherwise silent - last import wins).

## R3: ruff and formatter behavior

- `F403` (star import used) will fire on the new `__init__.py`: add it to the existing per-file-ignores entry (which already carries `F401` for the intentionally-"unused" re-exports), with a why-comment. `F405` is irrelevant - the `__init__` body references no star-imported names.
- The `as`-aliased same-name re-export idiom is ruff's recognized explicit-reexport form; `F401` does not flag it (and the per-file ignore covers any edge). `PLC0414` (useless-import-alias) is not in the selected rule set (`E,F,I,UP,B,SIM`).
- `ruff format` and isort (`I`) handle star imports normally; no config change beyond the per-file-ignores line.

## R4: Consumed-surface re-verification

The spec's 42-name census was captured 2026-08-16. Because other sessions are pushing concurrently (two pushes landed during this feature's specify phase alone), the implementing task **re-runs the census** (grep for `check_village\.<attr>` accesses plus `from check_village import` across the skill tree) immediately before writing the final explicit-import block, and the surface test pins the result. Names provided by the star imports need nothing; the census only determines (a) the underscore names needing aliased explicit imports and (b) the minimal `settlement`/`waterfields` external block.

**External block decision**: prune the external `settlement`/`waterfields` imports to the names the census shows are actually consumed through `check_village` and any the `__init__` docstring's contract requires - rather than keeping all ~31 current ones. Rationale: every kept name is a line a future reader pays for; the guard/surface test pins what is kept; and un-consumed external re-exports are exactly the pattern this feature deletes. If a segments module itself needs a settlement name, it already imports it directly - the external block only ever fed the package surface.
