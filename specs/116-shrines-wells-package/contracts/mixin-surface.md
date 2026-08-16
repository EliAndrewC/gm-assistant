# Contract: the composed `ShrinesWellsMixin` surface

The one thing a package split can break silently. A member dropped by the transformer produces a
package that imports cleanly, type-checks cleanly under `mypy --strict`, and draws nothing - and it
surfaces only when whichever generator calls that member happens to run. A member defined TWICE
produces a working import, a clean typecheck, and one silently dead implementation, because the MRO
just picks the first base.

This file is what the guard test in `tests/settlement/test_shrines_wells.py` implements. It is
feature 114's contract with this file's census substituted; the shape is deliberately unchanged.

## C1 - No pre-split member is lost

**Assertion**: the union of `vars(cls)` over `ShrinesWellsMixin.__mro__` is a SUPERSET of the 38-name
pre-split census.

**SUBSET, not equality**, for the reason 112/113/114 each recorded: a later decomposition legitimately
adds named private helpers, and equality would turn every such change into a contract edit - training
a reader to update the frozenset without thinking, which is the reflex that lets a real subtraction
through. An addition is visible in review; a subtraction is silent until a generator hits it.

**`vars(cls)`, not `callable(v)`**: the census admits any non-dunder name the class body defines,
data attributes included. `ShrinesWellsMixin` has no class-level attribute today (census: 38 members,
all `FunctionDef`) - but feature 112 needed a whole extra test because its guard counted callables
only, and this form costs nothing and covers the constant somebody adds later.

The 38 names:

```
# public, called from pool gens, wip/, other engine modules and tests
draft_byres, farm_wells, flush_tree_stands, forest, frozen_terrain, hill, open_seat,
place_wells, shrine, shrine_hall, shrine_well, small_shrine, torii_even, torii_path,
well, well_at

# private, reached through self. - including from OUTSIDE the package
_assert_walls_clear_of_torii, _avenue_at_threshold, _avenue_pitch, _avenue_short_of_walls,
_build_well_index, _crowns, _draw_byre, _draw_stand, _farm_wells, _footprint_clear,
_fringe_blocked, _hall_caption_y, _in_scrub_cover, _place_wells, _stand_fringe,
_terrain_fingerprint, _torii, _tree_stand, _well_ground_clear, _well_index, _well_vr,
_wet_toe_keepout
```

Thirteen of the private names have no consumer anywhere outside the class. They stay in the census
precisely because a name nothing else calls is the kind a careless partition drops with no other test
noticing.

## C2 - No two sub-mixins define the same name

**Assertion**: for every pair of sub-mixins in the MRO, `vars(a) & vars(b)` is empty, and the failure
names both classes and the colliding names.

The sub-mixin list is derived FROM THE MRO, not by importing the submodules. That is what lets the
guard run unchanged before and after the split: pre-split `ShrinesWellsMixin` is a single class, the
list is empty, and this assertion is vacuously true. Importing `settlement.shrines_wells.wells` et al.
directly - the shape feature 112 used - cannot be written before the package exists, which is what
made 112's red proof impossible to run in the order its task list implied (recorded in 113 tasks
T007).

## C3 - Every member resolves on `Settlement` itself

**Assertion**: `hasattr(Settlement, name)` for all 38.

C1 proves the names survive on the mixin; C3 proves they reach the class consumers actually use. A
mixin left out of the `class ShrinesWellsMixin(...)` base list passes neither, but a mixin left out of
`class Settlement(...)` would pass C1 and fail only here.

## Red proofs (required before the guard is trusted)

A guard never seen red is an assumption wearing a test's clothes. Record each failure's text in
`tasks.md`.

| # | breakage | must fail | when it can be run |
|---|---|---|---|
| 1 | delete a method from a sub-mixin (e.g. `_well_vr` from `wells.py`) | C1, naming it | PRE-split too, against the single class |
| 2 | copy one member into a second sub-mixin (e.g. `_well_vr` into `wellground.py`) | C2, naming both classes and the name | post-split only - needs >1 sub-mixin |

Breakage 3 from feature 114 (delete a class-level ATTRIBUTE) has no subject here: this class defines
none. C1's `vars()` form keeps the coverage for whenever one appears, which is why the form is kept
rather than simplified to callables.

## What this contract does NOT cover

- **Behavior.** Byte-identity of every regenerated `pool/**` artifact is the oracle for that
  (`quickstart.md`), and it is a far stronger statement than any surface census.
- **The decorator on `frozen_terrain`.** C1 sees the NAME, and a decorator lost in the move leaves the
  name in place while turning a context manager into a plain generator. That failure is caught by the
  test suite (every `with self.frozen_terrain():` call site raises `AttributeError: __enter__`) and by
  the byte-identity sweep, and it is checked directly in quickstart step 6a.
- **Import health of each submodule in isolation.** `ruff check` catches unused imports after the
  header prune; `mypy --strict` catches a missing one.
