# settlement/rolling/ - the rolling / homestead-solver subsystem as a package

Split from the 1,197-line `settlement/rolling.py` by feature 118 (constitution Principle X clause
13 - the cost being managed is context-window tokens). **Load only the file the task calls for**;
this index is the map. `from .rolling import RollingMixin` still resolves and `settlement/core.py`
is byte-unchanged, so nothing above this directory knows the split happened.

**This package is a CHAIN, and that shapes everything below.** `structures/` and `civic_grounds/`
were residue buckets - unrelated subsystems feature 025 happened to leave in one file - so their
submodules are grouped by "what a session comes here to change" and are deliberately uneven.
`rolling.py` was never a bucket: it is one cohesive pipeline, from *roll a whole village out of a
seed* down to *does this rectangle touch a ditch*. So the six modules are its LINKS, in order:

    roll -> seeds -> bundle -> fit -> place -> farmsteads
    (compose)  (candidates)  (geometry)  (may it stand?)  (find a spot)  (draw it)

The partition was chosen by testing it against real tasks rather than by theme, because a partition
is only worth its churn if tasks stop straddling files. Four, from this skill's own backlog:

| task | files it loads |
|---|---|
| add a settlement FORM (a new `*_seeds` generator) | `seeds.py` alone |
| the standing "placer must test the ROTATED footprint it draws" debt (skill CLAUDE.md, CENTER vs FOOTPRINT item 3) | `fit.py` alone - `_bundle_common_fits` is the named three-line landing site |
| the collision-circle swap (item 2) | `fit.py` + `place.py` |
| change what the flush DRAWS (the kura side, the garden relaxation) | `farmsteads.py` alone |
| tune a `roll_village` phase | `roll.py` alone |

## Look here when

| file | look here when |
|---|---|
| `__init__.py` | you need the composition itself; never add logic here |
| `roll.py` | you are changing what a seed-rolled hamlet or village COMES OUT AS: `roll_village` (the orchestrator) and its seven stages - `_roll_knobs` (which knobs, and the gravity-valid water-source roll), `_roll_field` (sluice, comb, land-use overlay), `_roll_margin_frame` (where the cluster band sits and how big it is - carries the bundle-pitch post-mortem), `_roll_cluster` (lanes, headman, the seed loop), `_roll_wells`, `_roll_windbreak`, `_roll_civic`. Plus `_MarginFrame`, the value object the stages pass around |
| `seeds.py` | you are adding or changing a settlement FORM - the shape houses are strung in before any is placed: `line_seeds` (linear ribbon), `scatter_seeds` (dispersed), `waterfront_seeds` (water town), and the perimeter ring (`_perim_bbox`, `_perim_poly`, `ring`) |
| `bundle.py` | you are changing what a homestead BUNDLE is - the dimensions: `_bundle_geom` (the whole metric layout, nucleated and dispersed), `_garden_beds` (the 1-or-2 bed dooryard garden and its three split forms), `_bbox_of`. **Pure geometry** - it places nothing, draws nothing, and calls nothing outside itself |
| `fit.py` | you are changing whether a bundle may STAND somewhere: `_rect_blocked` (the composite), `_rect_hits` / `_rect_on_water` / `_field_adjacent` (the primitives), `_bundle_fits` and its common/side halves, `_fits_any_side` (the four-side fast path), `_sun_corridor_ok` + `sun_corridor` (the opt-in threshing-yard sun rule), `_yard_sun_conflict`, `_garden_shaded`, and the two caches - `_poly_bboxes` and `_water_obstacles` |
| `place.py` | you are changing how a bundle FINDS its spot: `_place_bundle` / `_place_bundle_nucleated` (the two spiral searches), `_slide` / `_slide_nuc` (the compaction steps, and `keep_field`'s tangential constraint), `_nearest_field_point` / `_nearest_placed_point`, `_solve_homestead` (the legacy per-house solver), `headman`, and `_NUC_SIDES` |
| `farmsteads.py` | you are changing what the deferred flush DRAWS or the ORDER it draws in - this is the module the skill CLAUDE.md's DRAW ORDER contract is about: `farmsteads` (the entry point and its one `rng_scope`), `_farmsteads_bundle` (to-scale: groves recorded, south-nudge, yards/gardens/houses, arms LAST), `_farmsteads_legacy`, `_relax_gardens_south`, `_kura_side`, `_east_trees`, `_garden_beds_clear` |

## The dependency graph, MEASURED

Not asserted - computed from the AST by walking every `self.<attr>` against the member-to-module
map. Recompute it rather than trusting this table if you re-cut the partition:

| module | calls into |
|---|---|
| `bundle` | nothing |
| `seeds` | nothing (its `try_place` reaches `houses.py`, outside this package) |
| `roll` | `place`, `farmsteads` |
| `fit` | `bundle`, `place` |
| `place` | `bundle`, `fit` |
| `farmsteads` | `fit`, `place` |

**`place.py` is the hub** (three incoming edges), not `fit.py` as the chain diagram suggests - the
flush and the roller both reach placement directly. **`bundle.py` is a pure leaf**, which is the
property that makes it the right place for the researched dimension numbers: a change there cannot
ripple sideways within the package.

The one CYCLE, `fit` <-> `place`, is deliberate and is a single edge in one direction:
`_fits_any_side` (in `fit`) reads `self._NUC_SIDES`, which lives beside the nucleated placer that
the constant exists for. Nothing else crosses that way.

## Composition, and why it is in `__init__.py`

`RollingMixin` is `class RollingMixin(RollVillageMixin, SeedFormsMixin, BundleGeomMixin,
BundleFitMixin, PlacerMixin, FarmsteadFlushMixin)` with no members of its own. It exists ONLY so
`core.py` keeps its single import and `RollingMixin` keeps its position in the
`class Settlement(...)` base list - which means the partition here can be re-cut later without
touching `core.py`.

**Cross-submodule calls need no import.** Every sub-mixin is a base of the same `Settlement`, so a
member in one file reaches a member in another through `self.` exactly as before the split. Base
order is source order and is behaviorally irrelevant, because no name is defined twice - which is
what the composed-surface guard's second assertion exists to keep true
(`tests/settlement/test_rolling.py`).

## Two invariants the split does NOT touch

- **DRAW ORDER is a runtime contract.** `farmsteads.py` is the module most exposed to it: the
  bundle flush records grove rects first (the garden relaxation needs them), then draws
  yards/gardens/houses, then draws the yashikirin arms LAST so `_draw_grove`'s keep-out can see
  the houses. Moving a method's TEXT between files never changes when it runs; reordering the
  statements inside `_farmsteads_bundle` does.
- **`roll_village` draws NOTHING from the main RNG stream.** All four generators it constructs are
  seeded from `self.seed`, and its knobs go through `scope_seed`/`knob_rng`. Every main-stream draw
  happens inside a callee (`lane`, `try_place`, `farmsteads`, `place_wells`, `village_grove`,
  `hinterland`, `bridges`), so **the sequence of those calls IS the output.** That is what made the
  stage decomposition safe, and it is the property to re-check before moving a stage boundary
  again. (Measured 2026-08-17, feature 118; `future-work/` had predicted the opposite, which is
  why the rule is to measure rather than reason.)

## Monkeypatching a module-level name

Submodules bind helper names at import (`from .._geom import poly_gap`), so patching
`settlement.poly_gap` does not reach a mixin that already imported it - patch the DEFINING
submodule (`settlement._geom.poly_gap`) or, for anything reached via `self.`, patch
`settlement.Settlement` (class-level patching is unaffected by the split). No test in the suite
patches a settlement module-level name.

## Where the tests are

`tests/settlement/test_rolling.py` - ONE file, not a mirror package. At 343 lines it is well under
clause 13's bar, and the tests/ mapping rule already survives a source file becoming a package
(`test_structures.py` is 692 lines against a seven-module `structures/`). Its last two tests are
the feature-118 composed-surface guards.
