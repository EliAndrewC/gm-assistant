# Phase 1 Data Model: the partition, and the stage table

## Part 1 - The partition

All 43 class-body members of `RollingMixin`, in source order within each module. Line counts are
MEASURED member spans (`previous member's end + 1 .. this member's end`, the slice the transformer
takes), so they exclude only the 15-line module header the original carries.

Total: 1,182 member-span lines + 15 header = 1,197. Every member is accounted for exactly once;
the transformer asserts this rather than trusting it.

### `roll.py` - `RollVillageMixin` (256 lines -> ~300 after decomposition)

> **Look here when**: you are changing what a seed-rolled hamlet or village COMES OUT AS - which
> knobs are rolled, where the field goes, where the cluster band is seated, what civic features a
> village gets.

| member | lines |
|---|---|
| `roll_village` | 256 |

Post-decomposition this module also holds `_MarginFrame` and the seven `_roll_*` stages - see
Part 2.

### `seeds.py` - `SeedFormsMixin` (144 lines)

> **Look here when**: you are adding or changing a settlement FORM - the shape the houses are
> strung in before any of them is placed.

| member | lines | note |
|---|---|---|
| `line_seeds` | 19 | `settlement_form = 'linear'` - a ribbon along a road/dike/canal bank |
| `scatter_seeds` | 16 | `settlement_form = 'dispersed'` - area-uniform over an ellipse |
| `waterfront_seeds` | 25 | `settlement_form = 'water_town'` - both banks of a canal |
| `_perim_bbox` | 19 | perimeter candidates around a bbox |
| `_perim_poly` | 23 | perimeter candidates around a polygon outline |
| `ring` | 40 | ring a field with houses; owns the `rng_scope("ring", ...)` and the road-severance test |

**Why the perimeter ring is here and not in `place.py`**: `_perim_bbox`/`_perim_poly` answer the
same question the three `*_seeds` members answer - "where are the candidate seats?" - and `ring` is
their consumer in the same way `roll_village` is `cluster_seeds`'. Its one `try_place` call reaches
`place.py` through `self.`, which is the same relationship `roll_village` has.

### `bundle.py` - `BundleGeomMixin` (120 lines)

> **Look here when**: you are changing what a homestead bundle IS - the house, its threshing yard,
> its dooryard garden beds, its kura, the grove arms, and the caps that keep the headman's
> appurtenances ordinary. Pure geometry: it places nothing and draws nothing.

| member | lines | note |
|---|---|---|
| `_bbox_of` | 6 | `@staticmethod` - the enclosing bbox of a rect list |
| `_garden_beds` | 31 | the 1-or-2 bed dooryard garden and its three split forms |
| `_bundle_geom` | 82 | the whole bundle's metric layout, nucleated and dispersed |

This is the smallest module and deliberately so: it is the one a session loads to change a
DIMENSION, and dimensions are where the researched numbers live (the 0.48/0.85 garden scaling, the
42x30 / 68x44 caps, the 1.57 grove band depth). Keeping it free of predicates means those numbers
are readable in one screen.

### `fit.py` - `BundleFitMixin` (254 lines)

> **Look here when**: you are changing whether a bundle may STAND somewhere - any keep-out, any
> clearance, the sun corridor, the water and field predicates, and the two spatial caches that make
> asking cheap.

| member | lines | note |
|---|---|---|
| `_field_adjacent` | 5 | the gate's ADJ=165 farmland-adjacency rule |
| `_rect_corners` | 4 | |
| `_poly_bboxes` | 16 | the length-keyed bbox cache (`_bbox_cache`) |
| `_rect_hits` | 25 | rect-vs-polygons, bbox-prefiltered per poly and per edge |
| `_water_obstacles` | 24 | the irrigation-line cache (`_water_obs_cache`) |
| `_rect_on_water` | 24 | a SOLID rect on a channel/ditch/stream |
| `_rect_blocked` | 21 | the composite: blocks, fields, water, hard ground, ellipses, corridors |
| `_bundle_fits` | 12 | the conjunction of the common and side halves |
| `_sun_corridor_ok` | 49 | the opt-in threshing-yard sun rule and its research grounding |
| `sun_corridor` | 5 | the opt-in switch a generator calls |
| `_bundle_common_fits` | 13 | side-INDEPENDENT half - tested once per position |
| `_bundle_side_fits` | 14 | side-DEPENDENT half - bounds, ring, beds, placed bboxes |
| `_yard_sun_conflict` | 24 | grove-over-a-neighbor's-drying-ground |
| `_garden_shaded` | 12 | a house standing to a garden's south |
| `_fits_any_side` | 14 | the four-side fast path: common half once, then each side's garden |

**The two caches live with the predicates that own them**, not in a shared helpers module: each is
read by exactly one predicate (`_poly_bboxes` by `_rect_hits`, `_water_obstacles` by
`_rect_on_water`), and their staleness keys are the subtle part - the engine's own CLAUDE.md
records that two of three historical staleness bugs came from a cache added to fix a scan. Keeping
key and consumer adjacent is the point.

### `place.py` - `PlacerMixin` (194 lines)

> **Look here when**: you are changing how a bundle FINDS its spot - the spiral search, the two
> compaction slides, the nucleated garden-side choice, or the legacy per-house solver.

| member | lines | note |
|---|---|---|
| `headman` | 21 | the nanushi/shoya house: a larger plain farmhouse through the standard bundle path |
| `_closest_on_seg` | 8 | `@staticmethod` |
| `_nearest_field_point` | 13 | the bund a grove will hug |
| `_nearest_placed_point` | 11 | the neighbor to pack against |
| `_slide` | 18 | the dispersed compaction step |
| `_place_bundle` | 24 | dispersed placement: spiral, hug the bund, pack the neighbor |
| `_NUC_SIDES` | 2 | the garden-side preference order (see research R4) |
| `_field_dist` | 5 | |
| `_slide_nuc` | 24 | the nucleated slide, with the `keep_field` tangential constraint |
| `_place_bundle_nucleated` | 39 | nucleated placement + the unshaded-garden-side score |
| `_solve_homestead` | 29 | the legacy per-house solver: lift the reservation, nudge, re-reserve |

`headman` is here rather than in `bundle.py` because its body is a `try_place` call - it is a
placement entry point with a size argument, not a geometry definition.

### `farmsteads.py` - `FarmsteadFlushMixin` (214 lines)

> **Look here when**: you are changing what the deferred farmstead flush DRAWS, or the ORDER it
> draws in. This is the module the DRAW ORDER contract in the skill's CLAUDE.md is about.

| member | lines | note |
|---|---|---|
| `farmsteads` | 11 | the entry point and its single `rng_scope("farmsteads")` |
| `_farmsteads_bundle` | 42 | the to-scale path: groves recorded, then the south-nudge, then yards/gardens/houses, then the arms LAST |
| `_east_trees` | 14 | the east-shade band a garden is nudged out of |
| `_garden_beds_clear` | 16 | real footprints, not reserved bboxes |
| `_relax_gardens_south` | 48 | the south-nudge relaxation |
| `_kura_side` | 29 | which wall a LEGACY kura stands against, decided at DRAW time |
| `_farmsteads_legacy` | 54 | the legacy path: solve, attach, second-pass houses, second-pass groves |

### `__init__.py` (~40 lines)

Seven imports and `class RollingMixin(RollVillageMixin, SeedFormsMixin, BundleGeomMixin,
BundleFitMixin, PlacerMixin, FarmsteadFlushMixin)` with no members of its own, plus the docstring
that says why. Base order is source order and is behaviorally irrelevant - no name is defined
twice, which is the composed-surface guard's second assertion.

---

## Part 2 - The `roll_village` stage table

Eight functions where there was one. Line budgets are the source spans they carry plus a signature
and a docstring; none approaches the ~150 bar.

| stage | source lines it carries | ~lines | what it does | what it returns |
|---|---|---|---|---|
| `roll_village` | 16-44, 242-271 | ~70 | the orchestrator: signature, docstring, the meta writes, the fall vector, then the eight calls and the returned knob dict | the resolved knob dict |
| `_roll_knobs` | 45-65 | ~30 | six `resolve()` calls, then the gravity-valid water-source roll with its corner-intake preference | the seven rolled values |
| `_roll_field` | 66-87 | ~32 | the sluice anchor, the plot texture, `build_comb`, the field envelope, the archetype knob, `draw_comb_field`, the land-use overlay | `net`, `sluice` |
| `_roll_margin_frame` | 88-149 | ~70 | the seat direction away from the sluice, the band's aspect from the household count, the frame origin - and the bundle-pitch and band-sizing post-mortems | `_MarginFrame`, the field bbox, the cluster rng |
| `_roll_cluster` | 150-184 | ~45 | the lane skeleton trimmed off marsh, the headman's offset ring, the seed loop, `farmsteads()` | the skeleton points, the placed count |
| `_roll_wells` | 185-199 | ~22 | the INSET well grid over the houses that actually landed | - |
| `_roll_windbreak` | 200-227 | ~36 | the communal belt, derived from the placed houses rather than the requested band | - |
| `_roll_civic` | 228-241 | ~22 | the village-only shrine and its numerological torii march | - |

### The value object

```
_MarginFrame(ccx, ccy, alx, aly, tdx, tdy, lat, dep)   # frozen dataclass
    .to_screen(p) -> Pt                                 # margin frame -> screen, verbatim from the closure
```

### Invariants the decomposition must preserve

1. **Call order.** Every main-stream draw happens inside a callee (`lane`, `try_place`,
   `farmsteads`, `place_wells`, `village_grove`, `hinterland`, `bridges`), so the sequence of those
   calls IS the output. No stage may reorder, add or drop one.
2. **`hs` is bound once, in the orchestrator.** `roll_village` reads `self.M["houses"]` after
   `farmsteads()` and both `_roll_wells` and `_roll_windbreak` use it. Passing the same list to
   both preserves the original semantics exactly, rather than re-reading and hoping nothing rebound
   it.
3. **The guard asymmetry stays.** The well grid is guarded by `if hs:`; the windbreak derivation is
   not, and would divide by zero on an empty cluster. That is pre-existing behavior and is moved,
   not fixed - a refactor that quietly changes a failure mode is not a refactor.
4. **The seed loop's arithmetic stays literal.** `try_place(ccx + alx*lx + tdx*ly, ...)` is
   algebraically `to_screen((lx, ly))`, but it is left as written: identical float expressions in
   identical order are what byte-identity rests on, and there is no reason to spend that guarantee
   on a cosmetic substitution.
