# Data Model: Land-Use Overlay Historical Grounding

## 1. The `land_use_overlay` knob

| | Before | After |
|---|---|---|
| Value space | `none`, `mulberry_fishpond`, `lotus`, `tea_fringe` | `none`, `lotus`, `tea_fringe` |
| Default | `none` | `none` (unchanged) |
| Typing rule | `_land_use_ok` | `_land_use_ok` (unchanged in shape) |

`mulberry_fishpond` is removed from BOTH the registered value space and the accepted set inside
`apply_land_use`, so a pin or a stale spec raises rather than silently drawing. The dike-pond system
remains available where it belongs, as the `mulberry_dike_fishpond` value of the `field_archetype` knob.

## 2. The field plot record

Produced by the four builders in `waterfields.py` and handed to `apply_land_use` as `net["plots"]`:

```python
{"poly": [(x, y), ...], "fill": "<hex>"}
```

`fill == FLOODED` (`#93B7AC`) is the marker for **low, permanently wet ground**. All four builders set it,
each on the lowest ground its geometry defines:

| Builder | Which plots get `FLOODED` |
|---|---|
| `build_comb` | plots whose bottom edge lies on the collector drain (45% of those that abut) |
| `build_terraces` | the lowest 3 terraces |
| `build_polder` | the lowest 2 rows |
| `build_ribbon` | the lowest 3 bands |

This uniformity is what makes `FLOODED` a sound proxy for the lotus siting rule rather than a comb-only
quirk. Confirmed in Phase 0 research.

## 3. `apply_land_use` contract change

- **Before**: `take = max(2, int(len(plots) * fraction))`, then `rng.sample(plots, take)` - uniform over ALL
  plots, always hitting the fraction.
- **After**: lotus selects `[p for p in plots if p["fill"] == FLOODED]`, capped at `fraction * len(plots)`
  so a very wet field does not turn entirely into lotus. The returned count is therefore
  `min(len(wet_plots), take)` and **may legitimately be small, or zero**.
- Zero wet plots is a valid outcome: draw nothing, record `{"overlay": "lotus", "count": 0}`, do not fall
  back to random placement.

`tea_fringe` is unchanged (it already iterates `net["dry_plots"]`, the dry hill margin).

## 4. New manifest records (so the check has teeth)

The gate currently cannot see plot placement at all - the manifest records only
`land_use: [{"overlay", "count"}]`. Two additions, written by DIFFERENT code paths so the check compares
independent sources rather than reading back a self-report:

- `M["wet_plots"]` - centroid of every `FLOODED` plot, recorded by the field-drawing pass.
- `land_use[].plots` - centroid of every plot the overlay recolored, recorded by `apply_land_use`.

## 5. New check: `lotus_on_wet_ground_only`

Fires when any centroid in `land_use[].plots` (for `overlay == "lotus"`) is not among `M["wet_plots"]`.
Negative fixture in `test_checks.py` supplies a manifest with a lotus plot off the wet ground.

## 6. Modified check: `land_use_overlay_drawn`

Must keep catching a declared-but-never-called overlay while tolerating a legitimately small or zero
lotus count. Resolution: the check requires a `land_use` RECORD to exist for the declared overlay (proving
`apply_land_use` ran), and requires `count > 0` only when the overlay had eligible ground - for lotus,
only when `M["wet_plots"]` is non-empty.
