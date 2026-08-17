# Phase 1 Data Model: the partition

## Part 1 - the partition

All 14 class-body members of `LandMixin` plus the one module-level function that follows the class,
in source order within each destination. Line counts are MEASURED member spans (`previous member's
end + 1 .. this member's end`, the slice the transformer takes), so they exclude only the 14-line
module header the original carries.

Total: 1,173 member-span lines + 14 header = 1,187. Every member is accounted for exactly once; the
transformer asserts this rather than trusting it.

### `dikes.py` - `DikeMixin` (242 lines)

> **Look here when**: you are changing the polder perimeter dike - its width, its planted rows, its
> sluice notches, the crest it records - or the single-file village that stands on that crest.

| member | lines | note |
|---|---|---|
| `perimeter_dike` | 155 | the earthwork band: organic outer face, willow + mulberry rows, sluice gaps, records `dikes` with its `crest` |
| `dike_top_houses` | 87 | `settlement_form = 'dike_top'` - bare houses on widened crest platforms, tagged `on_dike` |

**Why these two and only these two**: `dike_top_houses` reads the `crest` centerline that
`perimeter_dike` records, and skips any site within `gap_clear` of a sluice gap that
`perimeter_dike` cut. Nothing else in the file touches either. This is the most self-contained
subject in `land.py` and the easiest module to be confident about.

### `wet.py` - `WetGroundMixin` (188 lines)

> **Look here when**: you are changing reed marsh - the glyph, where the band lies, its four roles -
> or the trim that stops a way running into it, or the shared surface-water distance predicate.

| member | lines | note |
|---|---|---|
| `marsh` | 93 | the wet scatter: tint patches, reed tufts, water glints; roles `toe` / `pond_fringe` / `defense` / `waterside` |
| `trim_off_marsh` | 34 | walk a way's ENDS back to dry ground (only the ends - a wet MIDDLE is a routing problem) |
| `toe_band` | 44 | the CONTOUR band below the crop, factored out so a router can ask for it BEFORE it is drawn |
| `surface_water_dist` | 17 | **module-level, after the class** - takes a manifest, not a Settlement |

**Why `toe_band` is here and not with `hinterland`**: it was FACTORED OUT of `hinterland` in
2026-08-12 precisely so it could be asked for before the marsh is drawn, because a way has to be
routed early while it still has a choice. It answers "where will the wet ground be", which is the
same question `marsh` answers by drawing it - and deriving that in two places is the trap this
skill's notes call "placement and its check must read the SAME source". Keeping the derivation
beside the drawing is the point of the factoring.

**Why `surface_water_dist` is here**: it is the package's one water-distance predicate, and this is
the package's water module. It is genuinely borderline - `_geom/` holds the other shared
placer-and-check manifest predicates and `_geom/village.py` is the precedent for a small pure one -
and that alternative is priced and declined in spec.md's Out of Scope. The index says plainly where
it lives so nobody has to guess.

### `cover.py` - `GroundCoverMixin` (362 lines)

> **Look here when**: you are changing what dry ground cover LOOKS like (scrub, pasture, coppice
> woodland), which ground gets it, or the swept verge that cover has to skip.

| member | lines | note |
|---|---|---|
| `commons` | 168 | the feathered dry scatter; `role` picks woodland / pasture / commons; `render='bare'` claims ground without scattering |
| `hinterland` | 136 | the COMPOSER: toe side, ring strips, toe strip, interior void fill, then the marsh |
| `_clear_ground` | 50 | the swept verge blob - inward-only bays, so a collar never annexes ground |
| `reserve_clearing` | 8 | pre-register a verge for a feature the gen draws LATER |

**Why the verge is here**: `clearings` is a keep-out registry this module both WRITES (`_clear_ground`)
and READS (`clr_b` in `commons`, and in `marsh` next door). The rule that makes it load-bearing is an
ORDERING one - a scatter only skips clearings that exist when it runs - so the reservation and the
scatter that honors it belong in front of the same reader.

**Why `hinterland` is here rather than in its own module**: it is a composer whose dominant callee is
`commons` (it calls it up to three times per map and `marsh` once). Feature 118 put `roll_village`
with the stage helpers it drives for the same reason. Splitting a 136-line composer away from the
168-line scatter it mostly calls would mean loading both for almost every real task.

### `nearring.py` - `NearRingMixin` (338 lines)

> **Look here when**: you are changing near-ring farmland at town or city scale - the dry hatake and
> garden quilt, the wet-rice basins, their density tiers, or the keep-outs either tiler honors.

| member | lines | note |
|---|---|---|
| `near_ring_cropland` | 147 | the dry quilt; `density` tiers dense/medium/thin; `_blocked` prefilter + `_blocked_region` decider |
| `near_ring_paddy` | 191 | wet-rice basins, placed only where legitimately watered; moat intake with the current; the city farm rings and wells |

**Why together**: they tile the same ground with the same keep-out set in a fixed order - paddy
first, grain filling only what paddy did not - and `near_ring_paddy`'s docstring says outright that
it "reuses `near_ring_cropland`'s keep-outs". Changing a keep-out means changing both.

### Relocated OUT of the package -> `settlement/homestead_parts.py` (27 lines)

| member | lines | every function it calls, and where that already lives |
|---|---|---|
| `_attach_grove` | 8 | `_draw_grove` - homestead_parts.py |
| `_find_appurtenances` | 12 | `_find_yard_spot`, `_farm_shed_rect`, `_find_garden_spot` - all homestead_parts.py |
| `_farmstead_nudges` | 7 | none (a generator of offsets); the homestead solver is its only caller |

These three are the residue of feature 025's positional cut: three farmstead helpers that were never
about land surfaces at all and sat in `land.py` only because of where the knife fell in a
16,016-line file. Every callee is already in `homestead_parts.py`, whose subject is exactly "the
parts of a homestead that are not the house". Packaging them as a 27-line `land/` submodule would
preserve the accident and teach a future reader nothing; moving them removes it.

Cost of the move, stated plainly: `homestead_parts.py` goes 756 -> ~783 raw lines, still comfortably
under the clause 13 line, and one extra import name (`Iterator`) is added to its header for
`_farmstead_nudges`'s return annotation.

## Part 2 - what does NOT change

The whole safety argument of this feature rests on this list being exhaustive.

| thing | before | after |
|---|---|---|
| `settlement/core.py` import | `from .land import LandMixin` | identical |
| `class Settlement(...)` bases | `..., LandMixin, CivicGroundsMixin, ...` | identical, same position |
| `settlement/__init__.py` | `from .land import surface_water_dist as surface_water_dist` | identical |
| `hamletgen/homesteads.py` | `from settlement import Settlement, surface_water_dist` | identical |
| `check_village/segments_04_homesteads.py` | `from settlement import ..., surface_water_dist` | identical |
| `tests/settlement/test_core.py` | `from settlement import ..., surface_water_dist` | identical |
| every method body | - | byte-identical text |
| every pool artifact | - | byte-identical hash |
| `pyproject.toml` | no per-file ruff ignore for `land` | none needed: `land/__init__.py`'s imports are all USED (in the class bases and the re-export), unlike `_geom/__init__.py`'s star imports |
| `SETTLEMENT_COV_FLOOR` | 94 | 94 - code motion moves no line in or out of coverage |

## Part 3 - the composed surface

```
Settlement
  ...
  LandMixin                 <- settlement/land/__init__.py, no members of its own
      DikeMixin             <- land/dikes.py
      WetGroundMixin        <- land/wet.py
      GroundCoverMixin      <- land/cover.py
      NearRingMixin         <- land/nearring.py
  ...
  HomesteadPartsMixin       <- settlement/homestead_parts.py, +3 relocated members
```

The one CROSS-SUBMODULE call is `hinterland` (cover.py) reaching `self.toe_band(...)` and
`self.marsh(...)` (wet.py). It needs no import: both are on the composed `Settlement`, which is
exactly the property that lets the partition be re-cut later without touching `core.py`.

MRO note: base order is source order and is behaviorally irrelevant here, because no name is bound in
two sub-mixins. That is not an assumption - it is the composed-surface guard's second assertion, and
the guard is proven to fire on a synthetic duplicate before it is trusted.
