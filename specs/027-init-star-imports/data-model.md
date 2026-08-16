# Data Model: check_village package surface (feature 027)

**Date**: 2026-08-16

The "data" of this feature is the set of names bound on the `check_village` package namespace. Three populations:

## 1. Star-provided public surface (the bulk)

Every public (non-underscore) module-level name of the 15 star-imported submodules, in this import order (mirrors the current file's known-cycle-free order):

`segments_cross`, `segments_01_city_frame_and_yards`, `segments_02_capital_and_walls`, `segments_03_structures_and_wards`, `segments_04_homesteads`, `segments_05_fields_and_funerary`, `segments_06_ways_and_bridges`, `segments_07_water`, `segments_08_town_and_fire`, `segments_09_justice_and_tanning`, `segments_10_city_battery_a`, `segments_10_city_battery_b`, `segments_10_city_battery_c`, `segments_11_polders_and_edges`, `registry`, `driver`

Census 2026-08-16: 124 distinct public names, zero clashes. Includes every publicly-consumed check/helper (`gate`, `main`, `GATE_SEGMENTS`, `META_CHECKS`, `TWIN_AXES`, `city_capacity`, `QUARTER_DENSITY_*`, ...). Also includes harmless pollution (submodules' own stdlib imports); the guard test tolerates identical-object sharing and rejects only true clashes.

## 2. Aliased explicit block (the exceptions)

Names that star imports cannot carry, imported `from <module> import name as name` (mypy-explicit re-export idiom):

- The six consumed underscore names: `_LABEL_EXEMPT`, `_LABEL_GROUP`, `_MATRIX_OUTSTANDING`, `_OVERLAP_EXEMPT`, `_OVERLAP_STRUCTS`, `_ward_interior` (defining submodule found at implement time).
- Consumed names defined outside the package (in `settlement` or `waterfields`) - determined by the implement-time census re-run; expected members include geometry helpers such as `point_in_poly`, `poly_area`, `seg_dist`, `edge_gap`, `water_setback`, `sweep_hi` if the census confirms they are not star-provided.

## 3. Dropped roster

- All `_seg_NNNN_MMM__*` re-exports (1,414 names; zero consumers).
- The entire `__all__` list (lines 1596-3148 of the current file).
- Unconsumed external re-exports from `settlement`/`waterfields` (e.g. `_assert_not_main_tree`, `KIDO_TOWER_KEEPCLEAR`) - each submodule that needs them already imports them directly.

## Guard/surface test contract (new test file)

1. **Clash guard**: for every pair of star-imported submodules, no public name binds different objects; on failure, report name + both module names.
2. **Surface pin**: every name on the implement-time census list (superset of the spec's 42) resolves via `check_village.<name>`, and each of the six underscore names is identical (`is`) to the attribute on its defining module.
3. The test imports submodules via `check_village.<submodule>` so it exercises exactly the import graph the package ships.

## Validation rules

- `wc -l check_village/__init__.py` ≤ 150.
- `python3 -m mypy` green (strict, no new relaxations); `ruff check` green with per-file-ignores `F401,F403` on this one file; `ruff format --check` green.
- Full skill gate green with zero changes outside the allowed file set (FR-007).
