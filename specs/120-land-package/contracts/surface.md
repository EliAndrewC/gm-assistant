# Contract: the composed `LandMixin` surface

The one thing a package split can break SILENTLY, and therefore the one thing that needs a test
outliving the one-shot transformer.

## Why a contract at all

Three failure modes, and none of them shows up as an error:

- **A member is DROPPED.** The package imports cleanly, `mypy --strict` passes, and the method
  simply is not there. It surfaces only when whichever generator calls it happens to run - which,
  for a member exercised by one frozen city map, could be months.
- **A member is defined TWICE.** The import works, the typecheck passes, and the MRO silently picks
  the first base. The other implementation becomes dead code that a future reader will edit
  believing it is live.
- **The module-level tail is lost.** `surface_water_dist` is not a mixin member; a transformer
  slicing only the class body drops it, and three consumers break at import.

The transformer refuses all three. But the transformer is a one-shot script that will be retired,
and the member somebody adds BY HAND next month gets none of its protection. That is what these
tests are for.

## C1 - no member of the pre-split surface is lost

**Where**: `tests/settlement/test_land.py::test_no_member_of_the_pre_split_land_surface_is_lost`

The 14 names of `LandMixin` as it stood at `56f6dfb` are pinned in `_LAND_SURFACE`, and every one
must be reachable on the composed `Settlement`.

**Pinned against `Settlement`, not against `LandMixin`** - deliberately, and this is the one place
this feature's contract differs from its seven predecessors'. Three members legitimately left the
package for `homestead_parts.py`, so a `LandMixin`-scoped census would fail for a relocation that is
CORRECT. Pinning the composed surface asks the question that actually matters ("can anything still
call it?") and keeps the pin honest, rather than training a reader to delete names from it.

**SUPERSET, not equality**, for the same reason feature 118 gave: a later decomposition legitimately
adds named private helpers, and equality would turn every such change into a contract edit - the
reflex that eventually lets a real subtraction through.

**Proven to fire**: dropping `NearRingMixin` from `LandMixin`'s bases (a transformer that forgot a
module) fails it, naming the two missing members.

## C2 - no member is defined in two sub-mixins

**Where**: `tests/settlement/test_land.py::test_no_land_member_is_defined_in_two_sub_mixins`

C1 cannot see this: a duplicated name still appears in the union. This walks each sub-mixin's own
`vars()` and reports any name bound in two of them.

It is also what licenses the statement in `land/__init__.py` that base order is behaviorally
irrelevant. That claim is only true while no name is bound twice, so it is asserted rather than
assumed.

**Proven to fire**: appending a second `toe_band` to `GroundCoverMixin` (one already exists in
`WetGroundMixin`) fails it, naming both classes.

## C3 - the relocated helpers stay relocated

**Where**: `tests/settlement/test_land.py::test_the_relocated_farmstead_helpers_live_in_homestead_parts_not_in_land`

`_attach_grove`, `_find_appurtenances` and `_farmstead_nudges` must be on `HomesteadPartsMixin` and
must NOT be on any `LandMixin` sub-mixin.

This exists because the relocation is a DECISION with a reason (every function they call was already
in `homestead_parts.py` - see research.md R3), and a decision that lives only in a document has
already been proven not to hold. A future session may well move them again; this makes that a
deliberate act rather than a drift.

**Proven to fire**: appending an `_attach_grove` stub to `GroundCoverMixin` fails it.

## C4 - the module-level tail survives at both import paths

**Where**: `tests/settlement/test_land.py::test_surface_water_dist_survives_the_split_at_both_import_paths`

`settlement.surface_water_dist is settlement.land.surface_water_dist`, and it still computes.

**Proven to fire**: removing the re-export from `land/__init__.py` fails collection outright,
because `settlement/__init__.py` imports it at module scope.

## What is NOT contracted here

- **Which module a member lives in.** That is `data-model.md`'s partition and `land/CLAUDE.md`'s
  index, and it is meant to be re-cuttable without ceremony - sub-mixin methods reach each other
  through `self.`, so moving one between submodules changes no call site. Pinning it would make a
  future re-cut a contract edit for no safety gained.
- **Behavior of any member.** That is covered by the 43 existing tests in `test_land.py` and, far
  more strongly, by the byte-identity oracle over all 893 pool artifacts.
