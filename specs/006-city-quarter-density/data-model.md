# Data Model: City Quarter Density and Wall-Sizing Correctness

The `/diagram` "data model" is the JSON manifest (`M`) a generator emits and the validator reads. This feature adds one new top-level entity (`quarters`) and reworks the capacity report. No database; these are in-memory dicts serialized to `pool/<city>.json`.

## Entity: Quarter (`M["quarters"]`, list)

A declared region of the walled interior. The unit at which density is judged.

| Field | Type | Notes |
|-------|------|-------|
| `poly` | list of `[x, y]` | Closed polygon (implicitly closed; first != last). MUST lie inside the wall. |
| `zone` | string | One of `residential`, `civic`, `mixed`, `reserve`. |
| `kind` | string or null | Required when `zone == "reserve"` (e.g. `drill_ground`, `garden`, `agricultural_district`); null otherwise. |
| `name` | string or null | Optional human label (e.g. "laborer terraces", "temple neighborhood"). |

**Validation rules** (enforced by checks, not the writer):
- Every quarter `poly` lies inside `M["wall"]` (no vertex or area outside).
- Quarters do not overlap (beyond a small shared-edge tolerance).
- The union of quarters covers the walled interior minus wall furniture / ring-road berm (uncovered interior beyond a tolerance is flagged).
- A `reserve` quarter has a non-null `kind` drawn from the allowed reserve kinds.

**Zone semantics**:
- `residential`: primarily dwellings; subject to the per-quarter density band + dead-zone guard.
- `mixed`: dwellings plus fronting shops/civic (e.g. a merchant district with a fire tower and storehouses); treated as residential for density but with a relaxed floor for its civic footprint.
- `civic`: government/temple precinct; subject to the civic-open tolerance (its non-civic-building open ground must be small).
- `reserve`: intentional open ground; must be rendered as `kind`; counts toward the reserve cap; contributes zero residential capacity.

## Reworked: Capacity report (`city_capacity(M)` return)

Existing keys retained (`target_dwellings`, `placed`, `ring_area`, `areas`, `grid`, `grid_origin`, `grid_step`). Changed / added:

| Key | Type | Change |
|-----|------|--------|
| `placed` | int | Now counts only in-wall dwellings for a walled city. |
| `residential_capable_area` | int | Redefined: interior MINUS civic-quarter area MINUS reserve-quarter area (was: interior minus per-cell civic/water/trunk/field). |
| `reserve_area`, `civic_area` | int | New: declared reserve and civic quarter areas (for the cap and the accounting). |
| `reserve_frac` | float | New: `reserve_area / interior`; flagged if > cap (~0.20). |
| `verdict` | string | `sized_and_packed` \| `densify` \| `enlarge` \| `shrink`. (`underpacked` renamed to `densify`; `too_small`->`enlarge`, `too_big`->`shrink`, `about_right`->`sized_and_packed` for action-clarity.) |
| `suggested_wall_scale` | float | Retained; computed against residential-capable ground. |
| `per_quarter` | list | New: for each residential/mixed quarter, `{name, area, dwellings, density, in_band}`. |

**Verdict logic** (against usable residential ground `R = residential_capable_area`, target `T`, tolerance `pop_tol`):
- `enlarge` if even well-packed `R` cannot hold `T` (`R * RHO_CANONICAL < 0.9*T`).
- `shrink` if `R` far exceeds what `T` needs OR the wall can only be "filled" by reserve ground beyond the cap.
- `densify` if `R` is right but in-wall placed `< (1 - pop_tol) * T` (boundary aligned to the population check).
- `sized_and_packed` otherwise.

## New module constants (named, with recorded rationale in `settlements.md`)

| Constant | Meaning | Calibration source |
|----------|---------|--------------------|
| `RHO_CANONICAL` | canonical well-packed dwelling density (existing, retained) | Tango |
| `QUARTER_DENSITY_FLOOR`, `QUARTER_DENSITY_CEIL` | per-residential-quarter density band | Tango quarters (pass) + broken Nagahara (fail) |
| `RESERVE_CAP_FRAC` | max reserve share of interior (~0.20) | historical (Phase 0) + Tango agri district |
| `CIVIC_OPEN_TOL` | max non-civic-building open share of a civic quarter | historical (Phase 0) |
| `DEAD_ZONE_MAX` | largest contiguous empty region allowed inside a residential quarter (fire-breaks are thinner) | Tango vs Nagahara empty-block separation |
| `EXTRAMURAL_COMMONER_MAX` = 0 | hard-zero commoner dwellings outside the wall | GM decision (FR-002) |

## Exempt-from-extramural building kinds

Legitimately outside the wall (never flagged by `city_commoner_dwellings_inside_walls`): samurai estates (`M["manors"]`), farmhouses (`M["houses"]`), the wharf suburb structures, gate-market shops. Flagged if outside: `laborer`, `laborer_large`, `merchant`, `merchant_house`, `merchant_large`, `burakumin`, `servant`.

## Fixtures

- `pool/regressions/<...>.json`: the pre-change broken Nagahara snapshot (must fire the new checks) + one synthetic per new check (per red-first discipline).
- Positive anchor: the retrofitted Tango `pool/tango.json` (all new checks pass).
