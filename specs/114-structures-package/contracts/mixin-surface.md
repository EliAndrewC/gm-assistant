# Contract: the composed `StructuresMixin` surface

The only interface this feature exposes is the set of members
`settlement.structures.StructuresMixin` contributes to `Settlement`. Everything else in the package
is internal.

## The contract

`from settlement.structures import StructuresMixin` MUST yield a class contributing **at least**
these 33 member names to `Settlement`, with the same behavior as the pre-split class:

**Public entry points** (called from pool gens, `wip/`, other engine modules, or tests):

    building        clear_label_seat        drum_tower          fire_tower
    kosatsuba       label_blockers          label_caption_hw    label_seat_clear
    manor           merchant_estate         merchant_estates    open_face_rot
    pack            pasture                 place_kosatsuba     place_punishment_spot
    road            rowpack                 servant_ranges      theater_stage
    try_building

**Private helpers** (reached through `self.`, but part of the surface because engine modules and
tests reach some of them on an instance):

    _blocks_any_door    _dims           _door_is_clear      _estate_wall_clear
    _face_street_rot    _office_records _shortfall          _solid_records
    _under_a_caption

**Class-level attributes** (part of the surface, and the half a methods-only census cannot see):

    URBAN    SERVANT_RANGE_DEPTH_FT    _OFFICE_STANDOFF

21 + 9 + 3 = 33.

Several private names have no consumer outside the class today. They stay in the contract anyway:
the contract's job is to prove the SPLIT dropped nothing, and a name with no external consumer is
exactly the kind a careless partition loses without any test noticing.

## Guard test

`tests/settlement/test_structures.py` gains a test that pins this contract:

1. The composed `StructuresMixin` exposes **at least** the 33 names above - a SUBSET assertion
   (`composed >= _STRUCTURES_SURFACE`), not equality. Equality would turn every future addition into
   a contract edit, which trains a reader to update the frozenset without thinking - exactly the
   reflex that lets a real subtraction through. The assertion guards the direction that HIDES: an
   addition is visible in review, a subtraction is silent until whichever generator calls it happens
   to run. Features 112 and 113 both reached this conclusion during implementation.
2. **No two sub-mixins define the same name.** Computed by intersecting each sub-mixin's own
   `vars(cls)` keys pairwise; a non-empty intersection fails and names the collision. This is the
   half that is easy to under-rate: a member defined twice produces a working import, a clean
   `mypy --strict`, and one silently dead implementation, because MRO just picks the first base.
3. Every one of the 33 resolves on `Settlement` itself, not merely on `StructuresMixin` - which is
   what consumers actually rely on.

**The census must cover ATTRIBUTES, not only methods.** `URBAN`, `SERVANT_RANGE_DEPTH_FT` and
`_OFFICE_STANDOFF` are class-body members and move exactly as deliberately as the methods do.
Feature 112 needed a SEPARATE test for its `_PADDY_*_KINDS` matrices because its surface guard was
methods-only; this guard uses a census that admits both (`hasattr`-based, with the frozenset built
from the pre-split class body via `ast`), so one test covers all 33.

**The sub-mixin list is derived from `StructuresMixin.__mro__`**, not from importing
`settlement.structures.urban` and its siblings by name. That is what lets this guard be written and
run BEFORE the split exists: pre-split the derived list is empty and assertion 2 is vacuous;
post-split it is the seven sub-mixins, with no edit to the test in between. Feature 112 imported the
submodules directly, which is why its assertion-2 red proof could not actually run in the order its
task list implied (feature 113 tasks.md T007).

**Red-green requirement (FR-003, Principle X)**: before the guard is trusted, it MUST be observed
FAILING. Assertion 1 can be proven red PRE-split; assertion 2 cannot, because a duplicate name needs
two sub-mixins to live in - so its proof is deferred to after the transformer runs and before the
stage is committed. Three deliberate breakages, each reverted immediately after the observation:

- delete one METHOD from a sub-mixin -> assertion 1 fails, naming that method;
- delete one class-level ATTRIBUTE -> assertion 1 fails, naming it (this is the half feature 112's
  guard could not see, so it is proven separately);
- copy one method into a second sub-mixin -> assertion 2 fails, naming the collision.

Record all three observations in `tasks.md` with the failure text, or the guard is unproven. A guard
test that has never been seen red is an assumption wearing a test's clothes.

## What is deliberately NOT in the contract

- **Which submodule holds a given member.** That is an internal decision, documented in
  `settlement/structures/CLAUDE.md` for navigation and free to change later. Pinning it in a test
  would make every future re-partition a contract change - and this feature already knows of three
  intended re-partitions (`road` -> `water_ways.py`, `pasture` -> `land.py`, and the possible
  `captions.py` -> `castle_civic.py` fold).
- **The MRO order of the seven sub-mixins.** Behaviorally irrelevant given assertion 2, which is
  precisely why assertion 2 is worth having.
- **Module-level names.** `structures.py` has none below the import header - the file is one class -
  so there is no module-level surface to contract.
- **`URBAN`'s contents.** The palette's keys and values are behavior, covered by the byte-identity
  oracle; the contract pins only that the attribute survives the move.
