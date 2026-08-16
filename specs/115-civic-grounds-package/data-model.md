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

---

## Part 3 - the `_YardCtx` design (GM-chosen option (a), research R13)

Settled in writing BEFORE any code moves, per the root CLAUDE.md rule: "Before changing ORDERING or
architecture, read every path involved in ONE batched pass and settle the sequence first. The failure
mode is discovering the ordering one gate failure at a time."

### The captured state, censused from the eight closure bodies

| name | built from | read by | mutated? |
|---|---|---|---|
| `sx, sy, r` | the method's own args | `clear`, everything | no |
| `corridors` | `self._corridor_buffers(2.0)` | `clear`, the road-rail search | no |
| `keep` | 14 `self.M[...]` kinds, inflated 3 px, culled to the disc + 50 | `clear` | no |
| `wallp` | `self.M["wall"]` | `clear` | no |
| `cand` | 4 rings x 12, then `random.shuffle` | `take` | **RNG - see below** |
| `used` | empty | `take` | yes |
| `rails` | empty | `draw_hitch`, `_glyph_free` | yes |
| `heaps` | empty | the heap stage | yes |
| `prior_heaps` | earlier yards' `dung_heaps` | `_rail_clear_of_heaps` | no |
| `prior_boxes` | earlier yards' `troughs_box` | `_glyph_free` | no |
| `prior_rails` | earlier yards' `rails` | `_glyph_free` | no |

Predicates that become `_YardCtx` methods: `clear`, `take`, `rail_rec`, `draw_hitch`,
`rail_clear_of_heaps`, `glyph_free`. (`beside` and `clear_of_rails` stay with their stages -
each has exactly one caller and is more stage-logic than shared predicate.)

### THE RNG LANDMINE, found before writing any code

`cand` is built and **`random.shuffle(cand)` runs at what is currently line 124** - which is AFTER
the litter scatter's draws (`random.uniform` / `random.random`, lines 94-115) and after the
`random.seed` at line 42.

So the obvious shape - build the whole context eagerly at the top of the method, `cand` included -
**moves the shuffle ahead of the litter draws and changes every stable yard on every map**. It would
type-check, lint clean, and pass the unit tests that only assert structural properties; the
byte-identity sweep would catch it, but only after the fact and without saying which decision did it.

This is rule 3 of the ordering rules, made concrete, and it is exactly the failure R13 accepted as
the cost of option (a).

**The rule this imposes on the implementation:**

- `_YardCtx.__init__` builds ONLY the RNG-free state: `sx/sy/r`, `corridors`, `keep`, `wallp`,
  `prior_heaps`, `prior_boxes`, `prior_rails`, and the empty `used`/`rails`/`heaps`. Construction
  must consume **zero** RNG draws. That is checkable and must be checked, not assumed.
- `cand` is NOT a constructor field. The furniture stage calls `ctx.seat_init()` at the exact point
  the old code built and shuffled `cand` - between the litter stage and the first `take`. That one
  call is the only place a draw moves at all, and it moves nowhere.
- Every other predicate is pure relative to the RNG: none of `clear`, `rail_rec`, `draw_hitch`,
  `rail_clear_of_heaps` or `glyph_free` draws. Verified by reading all eight bodies - the only
  `random.*` calls in the whole method are the seed, the litter scatter, the `cand` shuffle, and the
  draws inside the rail/trough/heap stage bodies themselves.

### The RNG surface is FOUR call sites, and only one ordering constraint (measured, not assumed)

A grep of every `random.*` call in the 335-line method returns exactly four kinds:

| line | call | stage |
|---|---|---|
| 41-42 | `random.getstate()` / `random.seed(...)` | the outer bracket |
| 94-115 | `random.uniform` / `random.random` (x5, in the scatter loop) | 2, litter |
| 124 | `random.shuffle(cand)` | 3, furniture setup |
| 362 | `random.setstate(st)` | the outer bracket |

**Stages 4, 5, 6 and 7 draw NOTHING.** The road rail, the interior rails, the watering point and the
dung heaps are fully deterministic given the already-shuffled `cand`, the `used` list, and the map
state. Ordering rule 3's warning about "branches whose draw count depends on the map" turns out NOT
to apply to them - the bounded-retry loop and the dig-your-own-well fallback consume candidates, not
random numbers.

So the entire RNG risk of this refactor collapses to **one constraint**: the litter scatter's draws
must still happen before `random.shuffle(cand)`. That is a single orderable fact between two adjacent
stages, not a lattice-wide hazard.

This materially de-risks GM-chosen option (a) relative to what research R13 assumed when the choice
was put. R13's caution stands as written for the general case; this measurement is why it does not
bite here. It also means the `seat_init()` split (below) is not a workaround - it is the one thing
the design actually has to get right.

### Verification specific to this design

Add to the existing task checks (quickstart step 8 remains the real proof):

1. **Assert construction draws nothing.** Snapshot `random.getstate()`, build a `_YardCtx`, assert
   the state is unchanged. A cheap unit test that pins the invariant the whole design rests on, and
   it fires instantly rather than after a 3-minute sweep.
2. **Assert `seat_init` is called exactly once per yard**, between the litter and the first `take`.
3. The stage-by-stage fast proxy (tasks T031) after each extraction, unchanged.

### Stage-to-context mapping

| stage | takes | uses from ctx |
|---|---|---|
| 1 keep-outs | - | IS the constructor |
| 2 litter | `ctx` | `clear` |
| 3 furniture | `ctx` | `seat_init`, `take` |
| 4 road rail | `ctx` | `corridors`, `take`, `rail_rec`, `draw_hitch`, `rail_clear_of_heaps`, `glyph_free` |
| 5 interior rails | `ctx` | same as 4 |
| 6 watering | `ctx` | `clear(rim=False)`, `glyph_free`, `rails` |
| 7 dung heaps | `ctx` | `clear`, `rails` + `prior_rails`, `heaps` |
