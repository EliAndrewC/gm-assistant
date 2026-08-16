# Data Model: Human-Scale Files (024)

## Package layout (AS BUILT - see research.md R13 for why it differs from the projection)

| module | contents | lines |
|---|---|---|
| `__init__.py` | docstring, the monolith's legacy import block (40 names), explicit re-exports, `__all__` | 121 |
| `__main__.py` | CLI (`python3 -m check_village`, `--capacity`) | 38 |
| `common_01_geometry.py` | types, `load`/`rect_corners`/hulls, overlap+label taxonomy tables, size constants | 946 |
| `common_02_overlap_policy.py` | matrix engine, `GridIndex`, ring-road/theater/fire helpers, torii/dojo consts | 859 |
| `common_03_capacity.py` | street/lane/crop helpers, `DEFAULT_MANIFEST`, kind tables, `city_capacity`, `_UNBOUND`/`_kept` | 853 |
| `segments_01_city_frame_and_yards.py` | segs 0000-0096 | 2,413 |
| `segments_02_capital_and_walls.py` | segs 0097-0133_030 | 2,358 |
| `segments_03_structures_and_wards.py` | segs 0133_031-0267 | 2,397 |
| `segments_04_homesteads.py` | segs 0268-0285_091 | 2,363 |
| `segments_05_fields_and_funerary.py` | segs 0285_092-0333 | 2,345 |
| `segments_06_ways_and_bridges.py` | segs 0334-0409 | 2,339 |
| `segments_07_water.py` | segs 0410-0512 | 2,348 |
| `segments_08_town_and_fire.py` | segs 0513-0554 | 2,271 |
| `segments_09_justice_and_tanning.py` | segs 0555_000-0562_042 | 1,478 |
| `segments_10_city_battery_a.py` | segs 0563_000-0563_125 | 1,958 |
| `segments_10_city_battery_b.py` | segs 0563_126-0563_251 | 1,707 |
| `segments_10_city_battery_c.py` | segs 0563_252-0563_376 | 2,324 |
| `segments_11_polders_and_edges.py` | segs 0564-0594 | 1,366 |
| `registry.py` | `_GateSeg`, `GATE_SEGMENTS` (1,375 rows), `META_CHECKS`, `_SEG_DEPS` - clause-13 justified | 8,420 |
| `driver.py` | `gate()`, twin detector, `main()` | 224 |

## Split tooling data shapes

### Segment census row (`split_oversized.py` output, recorded in tasks/commit)

```json
{"seg": "_seg_0285__wells_clear_of_shrine_and_torii", "lines": 1351, "units": 427,
 "checks": 42, "action": "split", "new_segs": ["_seg_0285_000__gardens_present", "..."]}
```

### Oracle baseline (`oracle_sweep.py capture` - unchanged 022 format)

Per fixture/manifest: ordered verdict list + sha256 of verbose stdout. Identity = zero diffs on
`compare`, and `targeted` verdict sets equal to full-run sets.

### `_GateSeg` (UNCHANGED - the contract)

```python
class _GateSeg(NamedTuple):
    fn: Any; free: tuple[str, ...]; writes: tuple[str, ...]
    checks: tuple[str, ...]; needs: tuple[str, ...]; meta: bool; always: bool
```

New per-check segments get rows with: `checks` = the one check name (plus any names the group
still emits together when statements are inseparable), `free`/`writes`/`needs` recomputed by the
same dataflow rules as 022 (`transform_gate.py`), row order = statement order within the old
segment, spliced at the old row's registry position.

### Registry-pin fixture

`test_fixtures/gate_check_names.json` maps the registry's segment names/checks; regenerated after
stage 1 (segment names change; CHECK names do not - fixture `_regression.fires` keys stay valid).

## Import generation rule (`split_package.py`)

For each moved top-level def/assign: free names = AST loads not bound locally, minus params,
builtins, and its own module's definitions; each remaining name imports explicitly from the
module that defines it (always an earlier file by contiguity; `settlement`/`waterfields` imports
stay absolute). Cycles are impossible by construction: imports only point backwards in file
order, except `registry.py` importing segment functions and `driver.py` importing registry -
both strictly forward of their dependencies.
