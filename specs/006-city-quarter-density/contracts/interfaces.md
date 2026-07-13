# Interface Contracts: City Quarter Density and Wall-Sizing Correctness

This skill exposes three internal contracts: the engine API (what a generator calls), the manifest schema (what the validator reads), and the check contracts (what fails and when). All are internal to the `/diagram` skill; there is no external/network surface.

## 1. Engine API (`settlement.py`)

### `s.quarter(poly, zone, kind=None, label=None)`

Declares a city quarter and (for reserves) draws it.

- `poly`: list of `(x, y)` vertices, a closed polygon inside the wall.
- `zone`: `"residential"` | `"civic"` | `"mixed"` | `"reserve"`.
- `kind`: required iff `zone == "reserve"`; one of `"drill_ground"`, `"garden"`, `"agricultural_district"` (extensible).
- `label`: optional map label.
- Effect: appends `{"poly": [...], "zone": ..., "kind": ..., "name": label}` to `M["quarters"]`. For `zone == "reserve"`, renders the ground as `kind` (drill-ground surface, garden planting, or delegates to the field routines for an agricultural district) so the open ground is visibly intentional.
- Contract: does NOT move or affect placement of any building; purely declarative + decorative. Callable before or after packing (rendering z-order handled like other ground features).

## 2. Manifest schema (`M["quarters"]`)

```json
"quarters": [
  {"poly": [[x,y], ...], "zone": "residential", "kind": null, "name": "laborer terraces"},
  {"poly": [[x,y], ...], "zone": "civic",       "kind": null, "name": "temple neighborhood"},
  {"poly": [[x,y], ...], "zone": "reserve",     "kind": "drill_ground", "name": "drill ground"}
]
```

A walled city (`meta.scale == "city"` and `M["wall"]`) MUST provide a non-empty `quarters`. Non-walled settlements omit it.

## 3. Check contracts (`check_village.py`)

Each is a gate check (fails the map when its condition is violated). All are walled-city-scoped.

| Check | Fails when |
|-------|-----------|
| `population_consistent_with_housing` (modified) | in-wall dwellings x5 outside `pop_tol` of `meta.population` (extramural dwellings no longer counted). |
| `city_commoner_dwellings_inside_walls` (new) | any commoner dwelling (laborer/merchant/burakumin/servant + large variants) sits outside the wall. |
| `city_quarters_declared` (new) | a walled city has empty/absent `M["quarters"]`. |
| `city_quarters_tile_interior` (new) | quarters overlap, extend outside the wall, or leave a non-trivial interior region uncovered. |
| `city_residential_quarters_dense_enough` (new) | a residential/mixed quarter's average density is below the band floor (or above the ceil), OR it contains a contiguous empty sub-region larger than `DEAD_ZONE_MAX` (a dead zone bigger than a fire-break). Names the quarter. |
| `city_civic_quarter_not_mostly_open` (new) | a civic quarter's non-civic-building open share exceeds `CIVIC_OPEN_TOL`. |
| `city_reserve_within_cap` (new) | total reserve area / interior exceeds `RESERVE_CAP_FRAC` (~0.20). |
| `city_wall_sized_to_population` (modified) | capacity verdict is `enlarge` or `shrink` (now computed against usable residential ground). |

### Capacity CLI (`check_village.py --capacity [--capacity-map]`)

- Prints the verdict (`sized_and_packed` / `densify` / `enlarge` / `shrink`), the residential-capable / civic / reserve area budget, `reserve_frac`, `suggested_wall_scale`, and the per-quarter density table.
- `--capacity-map`: the ASCII interior map, now overlaying quarter zones so the operator sees which region is under-dense.

## Backward-compatibility contract

- Non-city settlements (hamlet/village/town) and unwalled settlements: unaffected; the new checks no-op when `M["quarters"]` is absent and the settlement is not a walled city.
- Existing pool maps other than the two cities keep passing unchanged.
- The renamed verdict strings are internal; the only external consumer is the CLI output and the `city_wall_sized_to_population` check, both updated in lockstep.
