# Phase 1 Data Model: the authoritative partition

This file is the contract the transformer reads and the index documents. If the two disagree, this
file wins.

## Part 1 - the module partition

All 22 members of `CivicGroundsMixin`, in SOURCE order, each in exactly one module. No renames, no
relocations out of the package, no deletions (research R6).

### `funerary.py` - `FuneraryGroundsMixin` (~230 lines)

> Ground given over to the dead: where a settlement buries, entombs, burns and stores its bones.

| member | lines | note |
|---|---|---|
| `cemetery` | 72 | |
| `_ward_fence_cap` | 33 | placed by R1a - called by `mausoleum` here, and by `structures/compounds.py` through the composed class |
| `mausoleum` | 43 | |
| `cremation_ground` | 30 | |
| `ossuary` | 24 | |

### `justice.py` - `JusticeGroundsMixin` (~200 lines)

> Ground given over to punishment and to the boundaries punishment is measured against.

| member | lines | note |
|---|---|---|
| `punishment_spot` | 55 | |
| `execution_ground` | 85 | the second-largest member in the file; stays whole (under the ~150 bar) |
| `boundary_marker` | 32 | |

### `civic.py` - `CivicWorksMixin` (~265 lines)

> Institutional and commercial works: what a domain builds because it administers and trades, as
> opposed to what its inhabitants build to live.

| member | lines | note |
|---|---|---|
| `precinct_interior` | 36 | placed by R1b; calls `self.cemetery` across the module boundary, which is normal |
| `district` | 10 | |
| `terrace` | 25 | |
| `granary` | 52 | |
| `merchant_storehouses` | 57 | |
| `merchant_residences` | 58 | |

### `lodging.py` - `LodgingMixin` (~190 lines)

> Where travelers and their animals stop: the beds, the stalls, and the deferred draw that puts the
> yards on the map last.

| member | lines | note |
|---|---|---|
| `_way_bearing_near` | 7 | also consumed by `settlement/trades.py` |
| `_way_seat_near` | 20 | LIVE - called by `_way_bearing_near`; see research R6 before deleting it |
| `flophouse` | 41 | |
| `inn` | 31 | |
| `stables` | 35 | |
| `animal_ground` | 13 | |
| `flush_stable_yards` | 15 | calls `self._stable_yard` across the module boundary |

### `stable_yard.py` - `StableYardMixin` (~385 lines)

> One private method and its seven stages. Sized by R1c: at 335 lines it is larger than three of the
> other four modules, and folding it into `lodging.py` would produce a ~575-line module.

| member | lines | note |
|---|---|---|
| `_stable_yard` | 335 -> ~35 | the outer method after decomposition: the RNG bracket, the stage calls, the record |
| the seven stages | ~340 total | see Part 2 |

### `__init__.py` - `CivicGroundsMixin` (~40 lines)

Composition only, no members of its own. It exists so `settlement/core.py` keeps its single
`from .civic_grounds import CivicGroundsMixin` and its position in the `class Settlement(...)` base
list, and so the partition can be re-cut later without touching `core.py`.

**Base order is source order**, so that a hypothetical future name collision resolves the way a
reader scanning the original file would expect:

```python
class CivicGroundsMixin(
    FuneraryGroundsMixin,
    JusticeGroundsMixin,
    CivicWorksMixin,
    LodgingMixin,
    StableYardMixin,
): ...
```

The collision half of the guard (contracts/mixin-surface.md) means this order should never actually
decide anything.

---

## Part 2 - the `_stable_yard` decomposition

Seven stages, taken from the banner comments the method already carries. Each keeps its banner
verbatim (research R5). Line counts are estimates; the binding constraints are the ordering rules
below and the ~150-line clause-12 bar.

| # | stage | banner it carries | ~lines |
|---|---|---|---|
| 1 | `_yard_keepouts` | the tight footprint keep-out - real drawn buildings only, ~3 px margin, NOT the wide urban halo and NOT `block_polys`; plus the farrier's forge, which stands ON the yard by design (GM 2026-07-25) | 45 |
| 2 | `_yard_litter` | "1. BEATEN-EARTH scuff + STRAW litter: a feathered scatter so the ground reads TRODDEN, not blank" | 30 |
| 3 | `_yard_seat` | "2. FURNITURE: greedily seated at clear spots on rings around the stables (deterministic order)", including the `probes` doctrine - tips and edges tested, not centers (GM 2026-07-24) | 25 |
| 4 | `_yard_road_rail` | "(1) the ROAD-PARALLEL edge rail", plus the rails-draw-as-bare-posts doctrine and the no-animal-glyphs history (GM 2026-07-25) | 40 |
| 5 | `_yard_interior_rails` | "(2) one or two more rails at clear interior spots", with the bounded-retries reasoning - a candidate refused by the heap/glyph rules must not COST the yard a rail | 35 |
| 6 | `_yard_watering` | "the WATERING POINT" - the ox-consumption arithmetic, the 2-3 troughs clustered AT a well, the direction-aware offset, and the dig-your-own-well fallback (the Nagahara defect) | 110 |
| 7 | `_yard_dung_heaps` | "1-2 DUNG HEAPS" and the two-round map-wide rail-clearance history (15 px -> 24 px check floor / 25 px placement) | 50 |

Two closures already nested inside `_stable_yard` - the would-be-rail record builder and
`_glyph_free` - move with the stages that use them. `_glyph_free` is read by stages 4, 5, 6 and 7,
so it becomes a module-level helper rather than a closure; the rail-record builder is used only by
stages 4 and 5.

### Ordering rules (binding - research R12)

1. The `random.getstate()` / `random.seed(...)` / `random.setstate(st)` bracket **stays in the outer
   method**. No stage seeds its own stream or runs outside the bracket.
2. Stages are called in the order above, and **no RNG draw moves across a stage boundary**.
3. **No stage becomes eagerly evaluated where it was previously short-circuited.** Stages 5 and 6
   both contain branches whose draw count depends on the map (bounded retries; no-reachable-well
   fallback). Hoisting a candidate list out of one of those branches to tidy a signature changes the
   draw count on maps that take the other branch - it looks like a cleanup and is a bug.

### The re-cut seam, if the yard grows again

`stable_yard.py` at ~385 lines is the package's largest module and holds a single entry point. If it
grows past the bar, the seam is **furniture (stages 3-5, 7) vs water (stage 6)** - stage 6 is the
only one that reaches outside the yard for a recorded well, and it is already the largest stage by a
factor of two.
