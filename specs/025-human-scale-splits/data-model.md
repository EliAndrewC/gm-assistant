# Data Model: Human-Scale Splits (025)

No runtime data changes - the "entities" here are the module boundary maps, the proof artifacts,
and the split-sensitive infrastructure touchpoints. Line numbers are as of the 2026-08-16 recon
(commit 7e857c0); the mover script re-derives exact ranges from the live AST at implement time -
the RANGES below are the design, the numbers are advisory.

## E1 - settlement/ package boundary map (US3)

`settlement.py` = module docstring + imports + helpers (1-2031) + `class Settlement` (2032-16016,
338 methods, 35 class-body assigns).

### Helper modules (module-level defs, lines 1-2031)

| module | takes (advisory ranges) | contents |
|---|---|---|
| `_geom.py` | ~36-1307 | `_assert_not_main_tree` + pure geometry/spatial: `torii_halfbox`..`winding` incl. `Indexed`, `SeatMemo`, `PointGrid`, grids, label-quad/tilt helpers, overlap/gap/poly math, `village_population`, smoothing |
| `_knobs.py` | ~1310-2030 | knob engine (`Knob`, `register_knob`, `resolve_knob`, `scope_seed`, `knob_rng`, validators, `skeleton_layout`) + roll/size helpers (`roll_torii_count`, `roll_merchant_estate_count`, `execution_ground_ft`, `wall_tower_spacing_px`, bridge/machi/moat helpers, `crop_boxes`) |

(`_geom.py` lands ~1,270 lines, `_knobs.py` ~720 - both under threshold; if implementation
measures `_geom.py` heavier than expected it cuts once more at the label-helper boundary ~line
490.)

### Mixin modules (contiguous method runs of `class Settlement`)

| module | method run (advisory) | first..last method | ~lines |
|---|---|---|---|
| `core.py` | 2033-2520 + class attrs | `__init__`..`crop_to_content` (record/meta/knob-resolve/rng/view/crop) + the 35 class-body assigns + composed `class Settlement(...)` | ~700 |
| `fields.py` | 2523-3982 | `paddy_field`..`crescent_pond` (paddy, comb, land use, overlays, furrows) | ~1,460 |
| `water_ways.py` | 3984-4824 | `note_focal`..`alley` (mill/hall/market, streams/channels/clips, lanes/streets/kido/ward/quarter/alley) | ~840 |
| `shrines_wells.py` | 4827-5969 | `hill`..`forest` (shrines, wells+indexes, torii, avenues, tree stands) | ~1,140 |
| `structures.py` | 5971-7402 | `manor`..`drum_tower` (estates, road, building, servant ranges, rowpack/pack, pasture, theater, fire tower, kosatsuba, punishment-spot placement, labels-blockers) | ~1,430 |
| `trades.py` | 7406-8172 | `_trade_record`..`tanning_yard` (brewery, dye, lumber, oil, pawnshop, bathhouses, farrier, kiln, charcoal, forge, border, tanning) | ~770 |
| `homestead_parts.py` | 8174-8863 | `_draw_threshing_yard`..`_urban_keepouts` (yards, gardens, sheds, groves, village grove, corridor/canopy keepouts) | ~690 |
| `land.py` | 8865-9984 | `perimeter_dike`..`reserve_clearing` (dikes, commons, marsh, toe band, hinterland, near-ring cropland/paddy, farmstead nudges) | ~1,120 |
| `civic_grounds.py` | 9986-11104 | `precinct_interior`..`flush_stable_yards` (cemetery/mausoleum/cremation/ossuary, punishment/execution grounds, boundary/district/terrace, granary, merchant houses, flophouse/inn/stables + stable yard) | ~1,120 |
| `city.py` | 11107-12659 | `_gapped_ring`..`governor_mansion` (ring road, city wall, moat, gates, canal, towpath, farmland ring, quay, aqueduct, docks, log boom, bridges, footbridges) | ~1,550 |
| `castle_civic.py` | 12661-13523 | `castle`..`flower_field` (castle, ministry, dojos, label-spot engine, caption placement, forest patch, wall) | ~860 |
| `houses.py` | 13526-14385 | `house`..`water_source_anchor` (house, corridors/keepouts/treads, fits, frontage, try_place, cluster seeds, plot texture, water sources) | ~860 |
| `rolling.py` | 14388-15589 | `roll_village`..`ring` (roll_village, seeds, headman, bundle geometry + placement, farmsteads, perimeter ring) | ~1,200 |
| `finish.py` | 15573-16016 | `_record_label`..`render_png` (labels, title, blank-spot, finish, png) | ~450 |

Every file <=~1,550 lines; composed class in `core.py` lists mixins in a fixed order chosen so
the MRO is linear and produces the identical single definition per method (no name is defined
twice anywhere - verified by `scripts/check-duplicate-defs.py` in the gate).

**DRAW ORDER**: the draw-order contract lives in runtime code (`finish`'s layer assembly and the
`add`/`add_top` record streams, `core.py`) and the DRAW ORDER map documentation in the skill's
CLAUDE.md; the package CLAUDE.md index points at `core.py` + `finish.py` for it. Banner comments
(LABEL STANDOFF LADDER ~394, STABLE-YARD GLYPH EXTENTS ~580, knob-engine banners ~1310/1408)
move with their code.

## E2 - test_checks/ package map (US2)

Grouping key: **which `check_village` file the tested check's segment lives in**, derived from
the registry (`gate_check_names.json` + `registry.py` row -> segment file). Cross-cutting tests
(fixture-builder survival, matrix-debt bookkeeping, driver/twin-detector behavior) go to
`test_driver_and_fixtures.py`; helper-function unit tests to `test_common_*.py` mirroring the
three `common_*` modules.

| module | mirrors |
|---|---|
| `_builders.py` | (shared builders, moved verbatim) |
| `test_common_geometry.py` | `common_01_geometry.py` |
| `test_common_overlap_policy.py` | `common_02_overlap_policy.py` |
| `test_common_capacity.py` | `common_03_capacity.py` |
| `test_segments_01_city_frame_and_yards.py` .. `test_segments_11_polders_and_edges.py` | one per `segments_*` file (the three `segments_10_city_battery_*` files share ONE test module if their combined tests stay under threshold, else split to match) |
| `test_driver_and_fixtures.py` | `driver.py`, `__main__.py`, registry plumbing, cross-cutting |

## E3 - test_settlement/ package map (US4)

One `test_<module>.py` per E1 module that has tests (empty mirrors are not created); shared
builders to `_builders.py`. Exact mapping derived after US3 lands, by resolving each test's
primary exercised attribute to its new defining module.

## E4 - Identity-proof artifacts (stored under specs/025-human-scale-splits/)

| artifact | produced by | proves |
|---|---|---|
| `oracle_gen_pre.json` / `_post.json` | run every regen-runnable gen + fixed-seed hamletgen cohort; sha256 of each `.svg`/`.json` | US3 generation identity (byte-equal) |
| `oracle_gate_pre.json` / `_post.json` | ordered gate verdict stream per pool manifest + regression fixture (022 oracle-sweep method) | US3 gate identity |
| `collect_checks_pre.txt` / `_post.txt` | `pytest --collect-only -q`, sorted, `::`-suffix compared | US2 collection identity |
| `collect_settlement_pre.txt` / `_post.txt` | same | US4 collection identity |

## E5 - Split-sensitive infrastructure touchpoints (US3, same commit as the package)

| file | change |
|---|---|
| `Makefile` | coverage `--omit`/`--include` patterns `*/settlement.py` -> `*/settlement/*`; `SETTLEMENT_COV_FLOOR` comment updated (floor now covers the package's combined report) |
| `pyproject.toml` | mypy `files`: `"settlement.py"` -> `"settlement"`; ruff per-file-ignores += `"settlement/__init__.py" = ["F401"]`; coverage `source` unchanged (`"settlement"` names the import path either way) |
| `render_cache.py` | `engine_fingerprint()` walks non-test `.py` at any depth under the skill root minus `pool/`, `wip/`, itself (research R6); `test_render_cache.py` updated |
| docs naming `settlement.py` | diagram `CLAUDE.md`, `SKILL.md`, `migration-plan.md`, settlements docs - path/name references updated |
| `.specify/memory/constitution.md` + root `CLAUDE.md` + `plan-template.md` | US1 amendment + mirrors |
