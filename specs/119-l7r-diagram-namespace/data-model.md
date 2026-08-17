# Data Model: 119-l7r-diagram-namespace

This feature moves code rather than data. The "entities" are import-system objects and the artifacts
that prove they behave; each is listed with the invariant that must hold and how it is checked.

## Namespace portion

A directory named `l7r` contributing its contents to a shared `l7r.__path__`.

| field | value |
|---|---|
| locations | `webapp/l7r/`, `.claude/skills/diagram/l7r/` |
| `__init__.py` | **must not exist** |
| identity test | `l7r.__file__ is None` |
| checked by | `test_namespace_portion.py` in each tree, proven RED against a real `__init__.py` |

**Invariant**: neither portion may ever gain an `__init__.py`. Violating it does not raise at the
point of the mistake - the other portion simply stops resolving, which is why the check is a test
rather than a convention.

## Regular package

| entity | path | `__init__.py` |
|---|---|---|
| `l7r.diagram` | `.claude/skills/diagram/l7r/diagram/` | required |
| `l7r.diagram.sitegen` | `.../l7r/diagram/sitegen/` | required |
| the eight engine units | `.../l7r/diagram/<unit>` | as today |

## Engine unit

One of the eight top-level modules or packages that moves in landing 2.

| unit | kind | public entry today |
|---|---|---|
| `settlement` | package | `Settlement`, geometry primitives |
| `check_village` | package | `gate()`, `python3 -m check_village` |
| `waterfields` | package | comb-field engine |
| `hamletgen` | package | `HamletSpec`, `generate`, `python3 -m hamletgen` |
| `pipeline` | package | `regen`, `gencache`, `pool_index`, `poolmaps` |
| `tools` | package | `why_placed`, `pack_audit`, `cohort_audit`, … |
| `compound` | module | Mode A compound program |
| `citybudget` | module | space-budget city planner |

**Invariant**: after the move, each unit is importable under exactly ONE dotted name. No shim, no
alias, no re-export at the old path.

## `sitegen` member

| module | contents | source |
|---|---|---|
| `sitegen/types.py` | `Pt`, `Poly`, `SQ_FT_PER_ACRE` | `hamletgen/consts.py` (verbatim) |
| `sitegen/geom.py` | `centroid`, `unit`, `crop_polys`, `crosses_disc`, `crosses_poly`, `pull_clear`, `net_acres`, `poly_area` | `hamletgen/geom.py` (verbatim, 94 lines) |
| `sitegen/jobs.py` | `default_jobs` | `hamletgen/driver.py` (verbatim) |

**Membership rule (the invariant that decides future additions)**: a module belongs in `sitegen`
only if it names no concept from any one settlement tier - no households, paddies, bunds, hamlet
bands, headmen, walls, wards. A module that does belongs in that tier's generator.

**Direction rule**: `hamletgen` may import `sitegen`. `sitegen` may **never** import `hamletgen` or
any other tier generator. Asserted by a test, not by convention.

**Growth rule**: a hamlet stage that a later tier needs is **MOVED** into `sitegen`, never copied.
Recorded in `migration-plan.md` and `hamletgen/CLAUDE.md` so a village-tier session meets it without
reading this spec.

## Byte-identity oracle

| field | value |
|---|---|
| population | every generator under `pool/` and `wip/`, frozen legacy maps included (`--frozen-ok`) |
| artifact set | every file each generator writes under `pool/**` |
| baseline | taken once, on unmodified code, in a detached worktree at `HEAD` |
| comparison | `sha256` per artifact; **every** landing compares against the ORIGINAL baseline |
| pass condition | 100% identical. One differing byte stops the feature |
