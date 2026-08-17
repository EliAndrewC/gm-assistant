# settlement/shrines_wells/ - the shrines/wells subsystem as a package

Split from the 1,179-line `settlement/shrines_wells.py` by feature 116 (constitution Principle X
clause 13 - the cost being managed is context-window tokens). **Load only the file the task calls
for**; this index is the map. `from .shrines_wells import ShrinesWellsMixin` still resolves and
`settlement/core.py` is byte-unchanged, so nothing above this directory knows the split happened.

**This package was never ONE subsystem, and its NAME concedes it** - the only module in the engine
joined by an `and`. Feature 025 sliced the 16,016-line original by POSITION, so six unrelated
subsystems ended up sharing a file: religious halls, torii avenues, the well subsystem, a general
seat-finding API, draft byres and woodland stands. So the seven modules are grouped by **what a
session comes here to change**, not by theme, and they are deliberately uneven in size (72 to 294
lines) because tasks are uneven in size. The evidence that this was the right file to cut first,
though three larger ones remain: a session changing the torii threshold rule (34 lines) used to load
1,145 lines it did not need, and every reader of any subsystem loaded the 447-line well subsystem.

## Look here when

| file | look here when |
|---|---|
| `__init__.py` | you need the composition itself; never add logic here |
| `shrines.py` | a religious hall or a wayside shrine's GLYPH, or where its caption goes: `shrine_hall` (the roll, the avenue call, the true-scale guard, the caption band), `shrine` and `small_shrine` (the two simple glyphs), `hill` (the terraced landform a shrine may stand on), `_hall_caption_y` (keeping a hall's caption out of its own sando) |
| `torii.py` | the APPROACH - how many arches, how far apart, how far off the hall, how they dodge a wall: `_torii` (one true-scale arch), `_avenue_pitch` (stride), `_avenue_at_threshold` (the innermost arch one pitch off the hall's footprint), `_avenue_short_of_walls` (pull the run back rather than straddle a barrier), `_assert_walls_clear_of_torii` (re-ask when a WALL lands after an arch), `torii_path` / `torii_even` (hand-placed ascents) |
| `wellground.py` | **whether a patch of ground may take a wellhead at all**, and the cost of asking: `_well_ground_clear` (the predicate), `_build_well_index` / `_well_index` (the three `PointGrid`s), `frozen_terrain` (the per-pass freeze that asserts its own invariant), `_terrain_fingerprint`, `_wet_toe_keepout` (the reed toe, derived before the reeds are drawn), `_in_scrub_cover` (the grazed-waste refusal). **The hub - read the perf notes here before touching any of it** |
| `wells.py` | the wellhead GLYPH and how many wells a map gets and where: `well`, `_well_vr` (the drawn extent placement must predict), `well_at` (place one if the spot is clear), `place_wells` / `_place_wells` (the neighborhood grid + coverage pass), `farm_wells` / `_farm_wells` (the farm-belt cluster cover and its envelope-suspended fallback), `shrine_well` (a set-apart hall's ablution well) |
| `seats.py` | the general "where can a `w` x `h` feature stand?" API: `open_seat` (asks the real `_fits` at the moment of placement) and `_footprint_clear` (the whole-footprint test against the BOUND only, deliberately). Nothing to do with shrines or wells - see "Three placements you will want to fix" below |
| `byres.py` | the draft-animal byre: `_draw_byre` (the open-fronted stall glyph) and `draft_byres` (the house-driven pass, ~one shed per 4-5 households because a buffalo was shared, not owned) |
| `woods.py` | how a wood is DRAWN - a stand of individual trees, never a terrain wash: `_tree_stand` (queues it; carries the canopy-density research), `flush_tree_stands` / `_draw_stand` (the deferred canopy, drawn at crop time against the complete map), `_stand_fringe` (thicket-masked advance growth on the cut-over margin), `_crowns`, `_fringe_blocked`, `forest` |

## Composition, and why it is in `__init__.py`

`ShrinesWellsMixin` is
`class ShrinesWellsMixin(ShrineHallsMixin, ToriiAvenueMixin, WellGroundMixin, WellsMixin, OpenSeatMixin, DraftByresMixin, TreeStandsMixin)`
with no members of its own. It exists ONLY so `core.py` keeps its single import and
`ShrinesWellsMixin` keeps its position in the `class Settlement(...)` base list - which means the
partition here can be re-cut later without touching `core.py`.

**Cross-submodule calls need no import.** Every sub-mixin is a base of the same `Settlement`, so
`self._well_ground_clear(...)` from `wells.py` resolves through the MRO wherever the caller's text
lives. The engine already relies on this from outside the package too: `water_ways.py`,
`civic_grounds.py` and `structures/compounds.py` all call `self._assert_walls_clear_of_torii`;
`civic_grounds.py` calls `self._well_vr` and `self._well_ground_clear`; `core.py` and `finish.py`
call `self.flush_tree_stands`.

**`wellground.py` is the hub**, which is the shape a well-cut partition should have - two of the
other six call into it and it calls out to none of them:

| from | to | call |
|---|---|---|
| `wells.py` | `wellground.py` | `well_at` -> `_in_scrub_cover`, `_well_ground_clear`; `_place_wells` -> both; `farm_wells` / `place_wells` -> `frozen_terrain` |
| `seats.py` | `wellground.py` | `open_seat(well=True)` -> `_in_scrub_cover` |
| `shrines.py` | `torii.py` | `shrine_hall` -> `_avenue_pitch`, `_avenue_at_threshold`, `_avenue_short_of_walls`, `_torii` |

## Three placements you will want to "fix" - each is deliberate

Recorded here rather than only in `specs/116-shrines-wells-package/research.md`, because a decision
that lives only in a spec file is a decision nobody will find.

### `seats.py` and `byres.py` hold members that do not belong in this package at all

`open_seat` + `_footprint_clear` are a general placement API - the skill's `CLAUDE.md` documents
`open_seat` under "Ask the ENGINE where a feature fits", and its consumers are nine pool gens plus
`civic_grounds.py`, `houses.py`, `rolling.py` and `structures/fixtures.py`. Its home is `houses.py`,
beside the `_fits` it delegates to. `_draw_byre` + `draft_byres` are a homestead appurtenance and
belong with `homestead_parts.py`'s threshing yards, gardens and sheds.

Both are here only because feature 025's positional cut put them here. Neither was MOVED by this
feature, because moving a member between parent-level mixins is a different change with different
risk, and folding it in would make the byte-identity oracle answer two questions at once. Each gets
an isolated module so the eventual move is a one-file change - feature 113's `city/civic.py` and
114's `structures/ground.py` precedent.

### `shrine_well` is filed with the wells, not the shrines

The naming pulls one way and everything else pulls the other. It IS a well: it calls `well_at`
(hence `_in_scrub_cover` + `_well_ground_clear` + `_fits`), records an `M["wells"]` entry with
`shrine=True`, and exists so a remote hall passes `remote_shrine_has_own_well`. Its neighbors in
behavior are the other three placement passes, not the hall glyph. Placement follows the code.

### `_hall_caption_y` is filed with the halls, not the torii

It reads torii seat geometry, which argues for `torii.py`; but its single consumer is `shrine_hall`
and its subject is where the HALL's caption goes. Placement follows the caller - feature 113's
`_ring_upslope` precedent, 114's door probes. The cross-module read costs nothing (see above).

## If a module grows: the seams, decided in advance

- **`wells.py`** (largest, 294 lines): `farm_wells`/`_farm_wells` is an independent pass sharing only
  `well_at` and the freeze scope with `place_wells`/`_place_wells`. Cut there - `farmwells.py` - if
  either pass grows substantially.
- **`shrines.py`** (251): `hill` is scenery, not a shrine; it is here because a village shrine stands
  on one. If a second landform arrives, `hill` LEAVES for a landform module rather than `shrines.py`
  being cut in half.
- **`woods.py`** (185): the crown primitives (`_crowns`, `_fringe_blocked`) are the reusable half, the
  stand policy the rest. No reason to cut today.

## Monkeypatching a module-level name

Submodules bind helper names at import (`from .._geom import point_in_poly`), so patching
`settlement.shrines_wells.point_in_poly` does not reach a mixin that already imported it - patch the
DEFINING submodule (`settlement._geom.point_in_poly`) or, for anything reached via `self.`, patch
`settlement.Settlement` (class-level patching is unaffected by the split). After feature 116, "the
defining submodule" for a member of this subsystem is `settlement.shrines_wells.<module>`, not
`settlement.shrines_wells`. No test in the suite does this today (census: feature 116 research R6).

## The guard that makes the split safe

`tests/settlement/test_shrines_wells.py` holds the composed-surface guard: every one of the 38
pre-split names still on the composed class (a SUBSET assertion, so a later helper needs no
bookkeeping), no two sub-mixins defining the same name (MRO would silently orphan one), all 38
resolving on `Settlement` itself, and `frozen_terrain` still being a context manager - the decorator
being the one thing a slice can drop while leaving the NAME in place, so the surface census alone
cannot see it. Both surface assertions were proven red before they were trusted; the contract and its
red proofs are in `specs/116-shrines-wells-package/contracts/mixin-surface.md`.
