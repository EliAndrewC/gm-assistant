# Contract: the composed `FieldsMixin` surface

The only interface this feature exposes is the set of methods `settlement.fields.FieldsMixin`
contributes to `Settlement`. Everything else in the package is internal.

## The contract

`from settlement.fields import FieldsMixin` MUST yield a class contributing exactly these 24
method names to `Settlement`, with the same behavior as the pre-split class:

**Public entry points** (called from pool gens, `hamletgen/`, other engine modules, `check_village`
segments, or tests):

    apply_land_use   bund_junctions   comb_base_fill   crescent_pond
    draw_comb_field  fallow_field     paddy_field      pond             water_field

**Private helpers** (reached only through `self.`, but part of the surface because tests and other
engine modules call some of them on an instance):

    _draw_furrows      _fallow_patch    _mulberry_rows      _paddy_features
    _paddy_plots       _paddy_surface   _pick_overlay_plots _plot_center_span
    _plot_grave_island _plot_pond       _plot_rock          _rounded_pond
    _rows              _split_convex    _taxfree_plots

## Guard test

`test_settlement/test_fields.py` gains a test that pins this contract:

1. The composed `FieldsMixin` exposes exactly the 24 names above - asserted against a literal
   frozenset in the test, so an accidental drop or an unannounced addition both fail.
2. No two sub-mixins define the same name. Computed by intersecting each sub-mixin's own
   `vars(cls)` keys pairwise; a non-empty intersection fails and names the collision.
3. Every one of the 24 resolves on `Settlement` itself, not merely on `FieldsMixin` - which is what
   consumers actually rely on.

**Red-green requirement (FR-003, Principle X)**: before the guard is trusted, it must be observed
FAILING. Two deliberate breakages, each reverted immediately after the observation:

- delete one method from a sub-mixin -> assertion 1 fails naming that method;
- copy one method into a second sub-mixin -> assertion 2 fails naming the collision.

Record both observations in `tasks.md` as done, with the failure text, or the guard is unproven.

## What is deliberately NOT in the contract

- **Which submodule holds a given method.** That is an internal decision, documented in
  `fields/CLAUDE.md` for navigation and free to change later. Pinning it in a test would make every
  future re-partition a contract change.
- **Stage 2's extracted helpers.** They are new private names created by decomposition, internal by
  construction, and pinning them would freeze the very structure Stage 2 exists to improve.
- **Module-level names.** The census (research R8) found none reached from outside, so there is no
  module-level surface to contract.
