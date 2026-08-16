# test_checks/ - the gate's negative-fixture unit tests as a package

Split from the 11,475-line `test_checks.py` by feature 025 (constitution Principle X clause 13,
which covers test files as of v1.6.1 - the cost being managed is context-window tokens). **Load
only the module the task calls for**; this index is the map. Collection is unchanged: same test
names, same count, `python3 -m pytest test_checks/` from the skill dir.

The mapping rule: a test lives in the module named after the `check_village/` file that defines
the CHECK it exercises (derived from the registry, not guessed from test names). Shared fixture
builders live in `_builders.py` and are imported explicitly - never copy a builder into a test
module.

## Look here when

| module | tests for |
|---|---|
| `_builders.py` | the shared manifest/feature builders (`f`, `manifest`, `house`, `well`, city/town/capital fixture factories, ...). 1,500 lines, deliberately one file: a cohesive builder library, loaded only when writing fixtures. NOTE: `_CITY_WALL` (900-square) and `_CITY_WALL_SMALL` (800-square) are DIFFERENT walls - the old flat file defined the name twice and tests were written against whichever definition was in scope at their line; the split gave the second a distinct name |
| `test_common_geometry.py` | helpers in `check_village/common_01_geometry.py` (hulls, gaps, taxonomy tables) |
| `test_common_overlap_policy.py` | the overlap-matrix engine in `common_02_overlap_policy.py` |
| `test_common_capacity.py` | `city_capacity` + street/ward helpers in `common_03_capacity.py` |
| `test_segments_01_city_frame_and_yards.py` .. `test_segments_11_polders_and_edges.py` | the checks defined in the same-named `check_village/segments_*.py` file (one test module per segment file, including all three `segments_10_city_battery_*` files) |
| `test_driver_and_fixtures.py` | `gate()`/driver behavior, the twin-detector, fixture-builder survival, registry-wide sweeps, and genuinely cross-cutting tests |

## Adding a test

Write it in the module matching the check's segment file (find the segment file via
`check_village/CLAUDE.md`'s registry ranges); import builders from `test_checks._builders`. If a
new fixture builder is generally useful, add it to `_builders.py`; a one-test helper can live
next to its test. Extend `test_fixtures/gate_check_names.json` when adding a check, as before.
