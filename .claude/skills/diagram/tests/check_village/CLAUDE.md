# tests/check_village/ - the gate's negative-fixture unit tests as a package

Split from the 11,475-line `test_checks.py` by feature 025 (constitution Principle X clause 13,
which covers test files as of v1.6.1 - the cost being managed is context-window tokens). **Load
only the module the task calls for**; this index is the map. Collection is unchanged: same test
names, same count, `python3 -m pytest tests/check_village/` from the skill dir.

The mapping rule: a test lives in the module named after the segment GROUP that defines the CHECK
it exercises (derived from the registry, not guessed from test names). A GROUP is the number:
`test_segments_05_*` covers every check in `check_village/segments_05a..05d`, which feature 122 cut
out of the old single `segments_05_fields_and_funerary.py`. The group, not the file, because the
source split is about how much text a reader loads and the test split is about the same thing
measured separately - mirroring 38 source files with 38 test modules would have churned eleven
modules that were already under the bar to buy nothing.

Where a group's tests DO exceed the bar (~1,000 lines, constitution X clause 13, which covers tests
as of v1.6.1), that module splits in SOURCE ORDER into two named halves - `test_segments_05_*` and
`test_segments_08_*` are the two, and their halves are named for what they mostly cover. Source
order rather than by-owner regrouping is deliberate: these test modules are not written in registry
order, so regrouping them by owning sub-file would have reordered 326 tests to save nobody any
reading, and reordering tests is a behavior change wearing a refactor's clothes.

Shared fixture builders live in `_builders.py` and are imported explicitly - never copy a builder
into a test module.

## Look here when

| module | tests for |
|---|---|
| `_builders.py` | the shared manifest/feature builders (`f`, `manifest`, `house`, `well`, city/town/capital fixture factories, ...). 1,500 lines, deliberately one file: a cohesive builder library, loaded only when writing fixtures. NOTE: `_CITY_WALL` (900-square) and `_CITY_WALL_SMALL` (800-square) are DIFFERENT walls - the old flat file defined the name twice and tests were written against whichever definition was in scope at their line; the split gave the second a distinct name |
| `test_common_geometry.py` | helpers in `check_village/common_01_geometry.py` (hulls, gaps, taxonomy tables) |
| `test_common_overlap_policy.py` | the overlap-matrix engine in `common_02_overlap_policy.py` |
| `test_common_capacity.py` | `city_capacity` + street/ward helpers in `common_03_capacity.py` |
| `test_segments_01_*.py` .. `test_segments_11_*.py` | the checks defined in the same-NUMBERED `check_village/segments_NN*.py` files - `test_segments_04_homesteads.py` covers `segments_04a`, `04b` and `04c`. The `segments_10_city_battery_*` run (now `10a..10h`) keeps its three test modules `_a`/`_b`/`_c` |
| `test_segments_05_fields_and_ditches.py` + `test_segments_05_supply_and_graveyards.py` | group 05, split in source order at 1,044 lines |
| `test_segments_08_town_and_flow.py` + `test_segments_08_kosatsuba_and_basins.py` | group 08, split in source order at 1,140 lines |
| `test_driver_and_fixtures.py` | `gate()`/driver behavior, the twin-detector, fixture-builder survival, registry-wide sweeps, and genuinely cross-cutting tests |

## Adding a test

Write it in the module matching the check's segment GROUP (find the segment file, and so its
number, via `check_village/CLAUDE.md`'s registry ranges); import builders from `tests.check_village._builders`. If a
new fixture builder is generally useful, add it to `_builders.py`; a one-test helper can live
next to its test. Extend `tests/fixtures/gate_check_names.json` when adding a check, as before.
