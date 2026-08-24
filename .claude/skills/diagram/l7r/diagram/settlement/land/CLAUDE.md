# land/ - the land-surface subsystem

Split from the 1,187-line `settlement/land.py` by feature 120 (constitution Principle X clause 13),
the **last** un-split file in the `settlement/` package. **Load only the submodule your task calls
for**; this index is the map. `LandMixin` still composes the whole surface, so `settlement/core.py`'s
import and its position in the `class Settlement(...)` base list are unchanged - the split is
invisible above that line.

This package was a **residue bucket, not a chain.** `land.py` was cut positionally out of the
16,016-line `settlement.py` by feature 025, so what it held was four unrelated land subsystems that
happened to be adjacent. The partition is therefore by SUBJECT, and the test of it is that a real
task stays inside one module.

## Look here when

| file | look here when |
|---|---|
| `dikes.py` | you are changing the polder **perimeter dike** - its varying width, its willow/mulberry planted rows, its sluice notches, the `crest` it records - or `dike_top_houses`, the single-file village that stands on that crest. They are one module because the second reads the first's crest and skips its sluice gaps |
| `wet.py` | you are changing **wet ground**: the `marsh` glyph and its four roles (`toe` / `pond_fringe` / `defense` / `waterside`), `toe_band` (the contour band that decides where the toe lies), `trim_off_marsh` (walking a way's ends back to dry ground), or `surface_water_dist` - the module-level predicate shared by the gate and by `hamletgen.place_wells` |
| `cover.py` | you are changing **dry ground cover**: `commons` (the feathered scatter - woodland / pasture / scrub by `role`), `hinterland` (the composer that picks the toe side, lays the ring strips and fills interior voids), or `_clear_ground` / `reserve_clearing` (the swept verge the scatters must skip) |
| `nearring.py` | you are changing **near-ring farmland** at town or city scale: `near_ring_cropland` (the dry hatake + garden quilt, with its density tiers) or `near_ring_paddy` (wet-rice basins, placed only where legitimately watered, with the moat intake and the city farm rings) |
| `__init__.py` | you need the composed `LandMixin` or the `surface_water_dist` re-export; never add logic here |

## The three things worth knowing before you edit

**`toe_band` is derived, not drawn, and that is deliberate.** It was factored out of `hinterland` in
2026-08-12 so a WAY could ask where the wet ground will be while it still has a choice of route -
`hinterland` lays the marsh late, after the structures. Deriving that in two places is the trap this
skill's notes call *"placement and its check must read the SAME source"*, so there is ONE derivation
and both callers use it. If you need the toe earlier still, call `toe_band` earlier; do not
re-derive it.

**Two corrections are baked into that band, and both were expensive.** It is a CONTOUR band
perpendicular to the fall, not an axis-aligned box - a rectangle is only an honest contour at a
0/90/180/270 fall, and at a diagonal it slices across the slope and swallows the drain. And its
WIDTH comes from the ground the fan waters, never from the canvas: an alluvial fan's spring line
follows the FAN's toe and a floodplain's backswamp is bounded by its levees, so wet ground is
FEATURE-bounded in both landforms (`research/water.md`, "The wet toe is as wide as the FAN"). The
canvas-wide version was never a decision - it arrived as a side effect - and three separate pieces
of work built on it before anyone checked. The skill's `CLAUDE.md` keeps that story under "A side
effect is not a rule".

**The swept verge lives with the scatters that skip it, and the ordering is the rule.** A scatter
only skips clearings that EXIST when it runs, which is why `reserve_clearing` is there at all: a
precinct dropped in after `hinterland` must reserve its ground FIRST or the scrub covers it.
`scatter_respects_swept_clearings` checks exactly that, reading the `seq` ordinal `_clear_ground`
records.

## The one cross-submodule call

`hinterland` (cover.py) reaches `self.toe_band(...)` and `self.marsh(...)` in wet.py. It needs no
import: both are on the composed `Settlement`, which is what lets this partition be re-cut later
without touching `core.py`.

## What did NOT move here

`_attach_grove`, `_find_appurtenances` and `_farmstead_nudges` went to
[`../homestead_parts.py`](../homestead_parts.py) rather than into this package. They are farmstead
plumbing, not land surfaces, and every function they call (`_draw_grove`, `_find_yard_spot`,
`_farm_shed_rect`, `_find_garden_spot`) was already defined there - they sat in `land.py` only
because of where feature 025's knife fell. Packaging them as a 27-line submodule would have
preserved the accident.

Two relocations were priced and DECLINED, recorded so the question is not reopened from scratch:
`pasture` moving IN from `structures/` (proposed in `future-work/`, sound, but a cross-package
move does not belong in a split whose safety argument is that nothing moves but text), and
`surface_water_dist` moving OUT to `_geom/` (arguably a better home, but 17 lines of no clause 13
benefit and a second monkeypatch-path change in one feature). Full reasoning in
`specs/120-land-package/spec.md`.

## Mixins and mypy

Every mixin method is annotated `self: "Settlement"` with `from ..core import Settlement` under
`TYPE_CHECKING` - the two-dot form, one level deeper than the pre-split file used. That is what lets
`mypy --strict` resolve cross-subsystem attribute access with zero runtime import cycle. When adding
a method, keep that pattern; when adding a submodule, add its mixin to `LandMixin`'s bases in
`__init__.py` and a row to the table above.

## Monkeypatching

A module-level name is now one level deeper: patch `settlement.land.wet.surface_water_dist`, not
`settlement.land.surface_water_dist`. Anything reached via `self.` is unaffected - patch
`settlement.Settlement` as before.
