# Contract: the composed `CityMixin` surface

The only interface this feature exposes is the set of methods `settlement.city.CityMixin`
contributes to `Settlement`. Everything else in the package is internal.

## The contract

`from settlement.city import CityMixin` MUST yield a class contributing exactly these 27 method
names to `Settlement`, with the same behavior as the pre-split class:

**Public entry points** (called from pool gens, `wip/`, other engine modules, `check_village`
segments, `hamletgen/`, or tests):

    aqueduct       bridge      bridges              canal          channel_footbridges
    city_wall      dock        farmland_ring        governor_mansion
    inwall_drain_outfall       jetty                log_boom       moat
    moat_flow      quay        ring_road            sluice_gate    towpath
    water_gate

**Private helpers** (reached through `self.`, but part of the surface because engine modules and
tests reach some of them on an instance):

    _gapped_ring    _plank_reaches_useful_ground   _ring_upslope   _tower
    _wall_arc_of    _wall_perimeter                _wall_point_at_arc
    _wall_walk

19 + 8 = 27.

Two of the eight private names have zero external consumers today (`_tower`,
`_plank_reaches_useful_ground`). They stay in the contract anyway: the contract's job is to prove
the SPLIT dropped nothing, and a name with no consumer is exactly the kind a careless partition
loses without any test noticing.

## Guard test

`tests/settlement/test_city.py` gains a test that pins this contract:

1. The composed `CityMixin` exposes **at least** the 27 names above - a SUBSET assertion
   (`composed >= _CITY_SURFACE`), not equality. Equality was the original wording here and is
   wrong: Stage 2 decomposes the oversized methods into named private helpers, so the composed
   class legitimately holds MORE than 27, and will hold more again the next time a method is
   split. Equality would turn every future decomposition into a contract edit, which trains a
   reader to update the frozenset without thinking - exactly the reflex that lets a real
   subtraction through. The assertion guards the direction that HIDES: an addition is visible in
   review, a subtraction is silent until whichever generator calls it happens to run. Feature 112
   reached the same conclusion during its own implementation.
2. No two sub-mixins define the same name. Computed by intersecting each sub-mixin's own
   `vars(cls)` keys pairwise; a non-empty intersection fails and names the collision.
3. Every one of the 27 resolves on `Settlement` itself, not merely on `CityMixin` - which is what
   consumers actually rely on.

**The sub-mixin list is derived from `CityMixin.__mro__`**, not from importing
`settlement.city.walls` and its siblings by name. That is what lets this guard be written and run
BEFORE the split exists: pre-split the derived list is empty and assertion 2 is vacuous; post-split
it is the six sub-mixins, with no edit to the test in between. Feature 112 imported the submodules
directly, which is why its assertion-2 red proof could not actually run in the order its task list
implied (feature 113 tasks.md T007).

**Red-green requirement (FR-003, Principle X)**: before the guard is trusted, it MUST be observed
FAILING. Two deliberate breakages, each reverted immediately after the observation:

- delete one method from a sub-mixin -> assertion 1 fails, naming that method;
- copy one method into a second sub-mixin -> assertion 2 fails, naming the collision.

Record both observations in `tasks.md` with the failure text, or the guard is unproven. A guard
test that has never been seen red is an assumption wearing a test's clothes.

## What is deliberately NOT in the contract

- **Which submodule holds a given method.** That is an internal decision, documented in
  `settlement/city/CLAUDE.md` for navigation and free to change later. Pinning it in a test would
  make every future re-partition a contract change - and this feature already knows of one intended
  re-partition (`civic.py` folding into `castle_civic.py`).
- **Stage 2's extracted helpers.** They are new private names created by decomposition, internal by
  construction. Pinning them would freeze the very structure Stage 2 exists to improve.
- **Module-level names.** `city.py` has none below the import header - the file is one class - so
  there is no module-level surface to contract.
- **The MRO order of the six sub-mixins.** Behaviorally irrelevant given assertion 2, which is
  precisely why assertion 2 is worth having.
