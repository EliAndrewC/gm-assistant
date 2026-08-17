# Contract: the composed `RollingMixin` surface

The one thing a package split can break silently. A member dropped by the transformer produces a
package that imports cleanly, type-checks cleanly under `mypy --strict`, and draws nothing - and it
surfaces only when whichever generator calls that member happens to run. A member defined TWICE
produces a working import, a clean typecheck, and one silently dead implementation, because the MRO
just picks the first base.

This file is what the guard test in `tests/settlement/test_rolling.py` implements. It is feature
116's contract with this file's census substituted; the shape is deliberately unchanged.

## C1 - No pre-split member is lost

**Assertion**: the union of `vars(cls)` over `RollingMixin.__mro__` is a SUPERSET of the 43-name
pre-split census.

**SUBSET, not equality**, for the reason 112/113/114/116 each recorded: a later decomposition
legitimately adds named private helpers, and equality would turn every such change into a contract
edit - training a reader to update the frozenset without thinking, which is the reflex that lets a
real subtraction through. An addition is visible in review; a subtraction is silent until a
generator hits it.

**This feature is itself the case that rule was written for.** Its second commit adds seven
`_roll_*` stage methods to `roll.py`. Under an equality assertion that commit would have to edit
the contract, in the same change that rewrites the function - exactly the coupling that makes the
guard stop guarding.

**`vars(cls)`, not `callable(v)`**: the census admits any non-dunder name the class body defines,
data attributes included. Feature 112 needed a whole extra test because its guard counted callables
only. That is not hypothetical here: **`_NUC_SIDES` is a class-level tuple**, the first non-callable
member any of these splits has had to carry, and a callable-only census would not notice it going
missing.

The 43 names:

```
# public - called from pool gens, wip/, other engine modules and tests
farmsteads, headman, line_seeds, ring, roll_village, scatter_seeds, sun_corridor,
waterfront_seeds

# private - reached through self., including from OUTSIDE the package
_bbox_of, _bundle_common_fits, _bundle_fits, _bundle_geom, _bundle_side_fits, _closest_on_seg,
_east_trees, _farmsteads_bundle, _farmsteads_legacy, _field_adjacent, _field_dist,
_fits_any_side, _garden_beds, _garden_beds_clear, _garden_shaded, _kura_side,
_nearest_field_point, _nearest_placed_point, _perim_bbox, _perim_poly, _place_bundle,
_place_bundle_nucleated, _poly_bboxes, _rect_blocked, _rect_corners, _rect_hits,
_rect_on_water, _relax_gardens_south, _slide, _slide_nuc, _solve_homestead, _sun_corridor_ok,
_water_obstacles, _yard_sun_conflict

# class-level data - NOT a callable, see above
_NUC_SIDES
```

## C2 - No name is defined twice across the sub-mixins

**Assertion**: summed over the six sub-mixins, each member name appears in exactly one
`vars(sub_mixin)`.

**Why this needs its own assertion**: C1 cannot see it. A name defined in two bases still appears
in the union, so a duplicated member passes C1, passes the import, passes `mypy --strict`, and runs
whichever definition the MRO reaches first - leaving the other as dead code that a future reader
will edit believing it is live. The transformer refuses a partition that assigns a member twice,
but the transformer is a one-shot script that will be deleted; the test outlives it and covers the
member somebody adds by hand next year.

## Proving the guard before trusting it

Both assertions are proven RED against a synthetic breakage before the split is believed, per the
project's subagent-check TDD discipline (a check that has never fired is a check nobody has
verified):

- **C1**: delete one member from one sub-mixin's `MODULES` tuple, re-run the transformer into a
  scratch tree, confirm the test names the missing member.
- **C2**: add one member to a second module's tuple as well, bypass the transformer's own duplicate
  refusal, confirm the test names the duplicated member.

A guard that has only ever been green is indistinguishable from a guard that is not running - which
is the failure this project has documented three separate times ("A check that never RUNS looks
exactly like a check that passes").
