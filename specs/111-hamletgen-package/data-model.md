# Phase 1 Data Model: hamletgen/ package layout

**Feature**: 111-hamletgen-package | **Date**: 2026-08-16

This feature moves code; it introduces no new runtime data structures. The "data model" here is the
package layout, the import DAG, and the baseline corpus that serves as the oracle.

## Package layout

```text
.claude/skills/diagram/
├── hamletgen/
│   ├── __init__.py        # sys.path bootstrap + head docstring + derived re-export surface
│   ├── CLAUDE.md          # "look here when" index
│   ├── __main__.py        # 3-line CLI shim -> driver.main()
│   ├── consts.py          # Pt/Poly aliases + 32 researched constants (each with its why)
│   ├── plan.py            # HamletSpec, SitePlan, plan_site + the spec->plan derivation
│   ├── geom.py            # shared geometry predicates and measures
│   ├── water.py           # STAGE 1-2: the water frame, the field it shapes, polders
│   ├── sink.py            # STAGE 3: where the runoff goes (drain, tameike)
│   ├── cluster.py         # STAGE 4a: seating the settlement on the margin
│   ├── ways.py            # STAGE 4b: lanes, the connector track, path validity
│   ├── homesteads.py      # STAGE 5-6: houses on lane frontage, appurtenances, wells
│   ├── hinterland.py      # STAGE 7: open-ground scan, woodland, windbreak belt
│   ├── frame.py           # STAGE 8: crossings, the notice board, the map frame
│   └── driver.py          # STAGES tuple (the pipeline contract), Report, build, generate, cohort, main
├── test_hamletgen/
│   ├── __init__.py
│   ├── test_plan.py       # (one module per source submodule that has tests)
│   ├── test_geom.py
│   ├── test_water.py
│   ├── test_sink.py
│   ├── test_cluster.py
│   ├── test_ways.py
│   ├── test_homesteads.py
│   ├── test_hinterland.py
│   ├── test_frame.py
│   └── test_driver.py
├── test_hamletgen_surface.py   # NEW guard test - the consumed surface census
└── pyproject.toml              # mypy files entry + ruff per-file-ignores
```

`hamletgen.py` is DELETED in the same change (FR-001) so a stale monolith can never shadow the
package on `sys.path`.

## Import DAG (verified acyclic, research R1)

```text
        consts
        /    \
     plan    geom
        \    /
   ┌──────┴───────────────────────────────┐
   │                                      │
 water  sink  cluster  homesteads  hinterland  frame
                 │
               ways
                 │
   └──────────────┬───────────────────────┘
               driver          (imports every stage module via STAGES)
                 │
            __init__ / __main__
```

Star-import order in `__init__.py` is leaf-first: `consts`, `geom`, `plan`, `water`, `sink`,
`cluster`, `ways`, `homesteads`, `hinterland`, `frame`, `driver`.

## External dependencies (unchanged, moved with their users)

| import | used by |
|---|---|
| `settlement`: `Settlement`, `knob_rng`, `point_in_poly`, `seg_closest`, `seg_dist`, `seg_intersect`, `segments_cross`, `skeleton_layout` | distributed to the submodules that call each name; `point_in_poly` lands in `geom.py` and is re-exported (consumer-visible, contracts) |
| `waterfields`: `build_comb`, `build_polder` | `water.py` |
| stdlib: `argparse` (driver), `math`, `os`/`sys` (`__init__` bootstrap), `random`, `collections.abc`, `dataclasses`, `typing` | per module, as needed |

## Sizes: before and after

| | raw lines |
|---|---|
| `hamletgen.py` (before) | 2,913 |
| largest module after (`water.py`) | ~449 + header |
| second largest (`ways.py`) | ~442 + header |
| `driver.py` | ~119 |
| smallest (`geom.py`) | ~76 |
| clause-13 bar | ~1,000 |

Post-decomposition (US2), no function exceeds ~150 lines. Nine functions are above ~85 lines today
and are the decomposition targets (research R5).

## Baseline corpus (the oracle)

| artifact | count | source |
|---|---|---|
| live hamlet manifests + SVGs | 4 | `pool/hamlets/{inashiro,mizuguchi,kashikawa,sawada}.gen.py` at committed seeds |
| cohort manifests | 24 | `python3 -m hamletgen --batch 24` (fixed seed range) |

Captured from a scratch copy of the pre-split tree BEFORE any code change (research R3), stored
under `<scratchpad>/hg-baseline/`. Every subsequent step diffs against it and must produce an
empty diff.

## Consumed surface (the contract)

47 attribute names + 2 direct-import names, enumerated in
[contracts/package-surface.md](contracts/package-surface.md). The guard test
`test_hamletgen_surface.py` pins them and re-censuses the tree so a new consumer cannot be added
without the contract noticing.
