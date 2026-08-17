# settlement/civic_grounds/ - the civic-grounds subsystem as a package

Split from the 1,162-line `settlement/civic_grounds.py` by feature 115 (constitution Principle X
clause 13 - the cost being managed is context-window tokens). **Load only the file the task calls
for**; this index is the map. `from .civic_grounds import CivicGroundsMixin` still resolves and
`settlement/core.py` is byte-unchanged, so nothing above this directory knows the split happened.

**This package was never ONE subsystem, and that shapes everything below.** `fields/` is the field
engine cut four ways; `city/` is one tier cut six ways. `civic_grounds.py`, like `structures.py`
before it, was a RESIDUE BUCKET - four unrelated subsystems that feature 025 happened to leave in
one file. So the five modules are grouped by **what a session comes here to change**, not by theme,
and they are deliberately uneven in size (36 to 362 lines) because tasks are uneven in size.

This file was NOT the largest one left in `settlement/` when it was split - `_geom.py` (1,303),
`rolling.py` (1,197), `land.py` (1,187) and `shrines_wells.py` (1,179) were all bigger. It was
chosen on **cost per read**: those four are each one long cohesive subsystem, and a long cohesive
file is one you meant to open. It was also chosen because it held `_stable_yard` at 335 lines, the
largest function anywhere in the engine.

**Historical note (2026-08-17):** three of those four have since been cut on the same cost-per-read
argument - `shrines_wells/` (116), `rolling/` (118) and `_geom/` (117) - which says the "long
cohesive subsystem" reprieve was about ORDER, not exemption. Only `land.py` is still whole. The
sentence above is preserved as written because it records why THIS file went first; do not read it
as a current statement of what is unsplit.

## Look here when

| file | look here when |
|---|---|
| `__init__.py` | you need the composition itself; never add logic here |
| `funerary.py` | ground given over to the DEAD: `cemetery` (parish rectangle vs organic common ground - the Louzeyuan-vs-Japan distinction lives in its docstring), `mausoleum`, `cremation_ground`, `ossuary`, and `_ward_fence_cap`, the ward-fence predicate `mausoleum` sites against |
| `justice.py` | ground given over to PUNISHMENT: `punishment_spot` (the in-settlement post/stocks), `execution_ground` (the outside-the-settlement siting rules - road, boundary, outcast side), and `boundary_marker` |
| `civic.py` | institutional and COMMERCIAL works - what a domain builds because it administers and trades, as opposed to what its inhabitants build to live: `granary`, `merchant_storehouses`, `merchant_residences`, `district`, `terrace`, and `precinct_interior` (the sovereign temple precinct's interior program) |
| `lodging.py` | where travelers and their ANIMALS stop: `flophouse`, `inn`, `stables`, `animal_ground`, `flush_stable_yards` (the deferred draw that puts the yards on the map last, at crop time, when the map is complete), plus the way-bearing helpers `_way_bearing_near` and `_way_seat_near` |
| `stable_yard.py` | the working YARD around a gate stables, as STAGES: the beaten-earth scatter, the road-parallel rail, the interior rails, the trough cluster and its well, the dung heaps. See "The stable yard" below, and read the RNG rules there BEFORE editing it |
| `_yardctx.py` | `_YardCtx` - one yard's shared state (keep-outs, the wall, prior yards' rails/troughs/heaps, the candidate ring) and the six predicates every stage tests against (`clear`, `take`, `rail_rec`, `draw_hitch`, `rail_clear_of_heaps`, `glyph_free`). Not a mixin; it is constructed per yard |

## Composition, and why it is in `__init__.py`

`CivicGroundsMixin` is
`class CivicGroundsMixin(FuneraryGroundsMixin, JusticeGroundsMixin, CivicWorksMixin, LodgingMixin, StableYardMixin)`
with no members of its own. It exists ONLY so `core.py` keeps its single import and
`CivicGroundsMixin` keeps its position in the `class Settlement(...)` base list - which means the
partition here can be re-cut later without touching `core.py`.

**Cross-submodule calls need no import.** Every sub-mixin is a base of the same `Settlement`, so
`self.cemetery(...)` from `civic.py` resolves through the MRO wherever the caller's text lives. Two
such calls exist here by design, and both are intentional rather than accidents of the cut:

| from | to | call |
|---|---|---|
| `civic.py` | `funerary.py` | `precinct_interior` -> `cemetery` (the precinct claims its own graveyard) |
| `lodging.py` | `stable_yard.py` | `flush_stable_yards` -> `_stable_yard` |

Two members are also reached from OUTSIDE the package through `self.`, which is why neither is as
private as its underscore suggests: `structures/compounds.py` calls `self._ward_fence_cap(...)`, and
`trades.py` calls `self._way_bearing_near(...)`.

## Three placements you will want to "fix" - each is deliberate

Recorded here rather than only in `specs/115-civic-grounds-package/research.md`, because a decision
that lives only in a spec file is a decision nobody will find.

### `_ward_fence_cap` is in `funerary.py`, not with the ward fences

It reads like a ward-fence utility and its natural home is beside the ward fences in
`water_ways.py`. It is here because `mausoleum` is its caller inside this package, and **placement
follows the caller** (feature 113's `_ring_upslope` precedent). Its external consumer
(`structures/compounds.py`) reaches it through the composed `Settlement` either way, so its
placement costs that consumer nothing.

Moving it to `water_ways.py` is a PARENT-level move - a different change with a different risk
profile - and folding it into feature 115 would have made the byte-identity oracle answer two
questions at once. It is a named follow-up, not an oversight.

### `precinct_interior` is in `civic.py`, not with the shrines

It draws a sovereign temple precinct's interior program - abbot's residence, order administration,
library, two monk dormitories, kitchen/refectory - so thematically it is religious ground and its
natural eventual home is beside the shrines in `shrines_wells.py`. It sits in `civic.py` as the
institutional-works member for the same parent-level-move reason as above.

Two things to know if you touch it: it calls `self.cemetery` across the module boundary (normal, see
the table above), and its **only consumer in the entire tree is `wip/shiro-daika.gen.py`**. That
last fact is why feature 115 ran that one 6-minute map in its byte-identity baseline instead of
excluding it the way features 112 and 114 did - excluding it would have left a moved member with no
artifact-level proof at all.

### `_stable_yard` has a module to itself

A module holding one private method reads oddly next to `funerary.py`'s five siblings. At 335 lines
pre-decomposition it was larger than three of the other four modules, and folding it into
`lodging.py` beside its caller would have produced a ~575-line module - half the pre-split file,
which would have moved the grab-bag problem rather than solved it.

## The stable yard

`_stable_yard` draws the working ground around a gate stables (GM 2026-07-22): a beaten-earth
forecourt, NOT a fenced paddock, whose "in active use" signal is carts, tethered animals and
littered ground - the Qingming Shanghe Tu gate convention. It is the single densest concentration of
researched, dated GM decisions in the engine, which is why feature 115 checked comment survival
across both the move and the decomposition rather than trusting either.

### The stages, and where each one's research lives

`_stable_yard` was a single 335-line method - the largest function in the engine - until feature
115 stage 2. It is now an outer method holding the RNG bracket, the stage calls in order, and the
record; each stage carries its own dated GM-decision comments verbatim.

| # | stage | what it draws, and the decision behind it |
|---|---|---|
| 1 | `_YardCtx(...)` | no drawing - builds the tight footprint keep-out (~3 px margin, real drawn buildings only, NOT the urban halo and NOT `block_polys`), including `farriers`, because the shoeing forge stands ON this yard by design (GM 2026-07-25) |
| 2 | `_yard_litter` | the beaten-earth scuff and straw scatter, feathered to nothing at the rim so the ground reads TRODDEN rather than blank |
| 3 | `ctx.seat_init` | no drawing - builds and SHUFFLES the four candidate rings. The yard's last RNG draw |
| 4 | `_yard_road_rail` | the road-parallel hitching rail, set back off the roadbed. Probed at its FULL extent, tips included (GM 2026-07-24) - a rail whose tip lies on the tread is exactly what it exists to prevent |
| 5 | `_yard_interior_rails` | one or two more rails, with BOUNDED RETRIES rather than two attempts: a candidate refused by the heap/glyph rules must not cost the yard a rail, since the tie-up room is the whole "in active use" signal |
| 6 | `_yard_watering` | 2-3 troughs clustered AT a well (a working ox drinks ~10 gal/day; a train needs 300-600 gal in relays), offset direction-aware by a bucket-pour. A yard with no reachable well DIGS ITS OWN rather than carrying water - the Nagahara defect, GM 2026-07-23 |
| 7 | `_yard_dung_heaps` | 1-2 heaps, held 25 px off every rail line ON THE MAP (two rounds of GM review: 15 px still read as "next to the hitching posts", and the first version measured only this yard's own rails) |

Rails draw as BARE posts and the yard shows no animals at all - the drawn oxen kept reading as muck
piles however they were styled, and the standing doctrine is that these maps render no humans, so
they render no animals either (GM 2026-07-25).

### The RNG rules - READ THESE BEFORE EDITING

`_stable_yard` does not take an injected RNG. It brackets its whole body in
`random.getstate()` / `random.seed(...)` / `random.setstate(st)` and draws from the **global**
`random` stream throughout - the litter scatter, the furniture shuffle, the rail candidates, the
trough jitter. The seed is derived from the yard's own position and radius, so each yard is
independently deterministic; but WITHIN a yard the output depends on the exact sequence of draws.

1. **The bracket stays in the outer method.** A stage that seeded its own stream, or ran outside the
   bracket, would leak state into the rest of the map.
2. **Stages are called in source order and no draw moves across a stage boundary.** Extracting a
   block that ends mid-expression is how this goes wrong.
3. **No stage may become eagerly evaluated where it was previously short-circuited.** The
   interior-rail pass has bounded retries and the trough pass has a "no reachable well -> dig one"
   fallback; both are branches whose draw count depends on the map. Hoisting a candidate list out of
   one of those branches to tidy a signature changes the draw count on maps that take the other
   branch. **It looks like a cleanup and it is a bug** - and neither `mypy --strict`, `ruff`, nor
   the unit tests will see it. What sees it is a byte-identity sweep over the pool.

## Two thresholds, so the next session does not decide them under pressure

- **No module here is near the bar.** After feature 115 stage 2 the package is `civic.py` 267,
  `stable_yard.py` 264, `funerary.py` 228, `justice.py` 193, `lodging.py` 187, `_yardctx.py` 173,
  `__init__.py` 36. The ctx/stages split was itself the first re-cut: the decomposition took
  `stable_yard.py` to 421 in one file, over this feature's own 400-line criterion, and pulling
  `_YardCtx` out was the honest fix rather than relaxing the number. If `stable_yard.py` grows
  again the next seam is **furniture** (the litter, both rail passes, the heaps) versus **water**
  (the trough cluster and its dug well) - the water stage is the only one that reaches outside the
  yard for a recorded well, and it is the largest stage by a factor of two.
- **`tests/settlement/test_civic_grounds.py` stays ONE file** at its current size. When it crosses
  ~1,000 lines it becomes `tests/settlement/test_civic_grounds/`, mirroring this package. Clause 13
  gives tests no exemption; this file is simply not over the bar yet.

## Monkeypatching

Each submodule binds shared helper names at import (`from .._geom import rail_quad`), so patching
`settlement.civic_grounds.rail_quad` reaches nothing. Patch the DEFINING module
(`settlement._geom.rail_quad`) or, for anything reached through `self.`, patch
`settlement.Settlement` - class-level patching is unaffected by the split.

The pre-split file had **no module-level functions or constants at all** - it was a docstring,
imports, and one class - so unlike some of its siblings this package never had a module-level patch
surface to break. A grep for `civic_grounds.` across the skill returns no hits outside the package.

## The guard, and what it is for

`tests/settlement/test_civic_grounds.py` holds the 22 pre-split members as a SUBSET of what the
composed class exposes, a second test holds that no two sub-mixins define the same name, and a third
holds that all 22 resolve on `Settlement` itself. Both breakage classes were proven to fire before
the guard was trusted (feature 115 T007/T017).

- **Subset, not equality** - so the decomposition's added private stages need no bookkeeping. The
  direction that HIDES is a member going missing: an addition is visible in review, while a
  subtraction surfaces only when whichever generator happens to call it runs - and for
  `precinct_interior` that is one `wip/` map nobody runs by default.
- **The census admits attributes, not just callables**, even though this class has none today. A
  constant is as easy to lose in a split as a method and much easier to overlook.
- **`_way_seat_near` is LIVE.** It has no consumer outside the package and a cross-file census that
  excludes the defining file reports it deletable - feature 115's own pre-spec census did exactly
  that and proposed deleting it. `_way_bearing_near` calls it, one line. Any dead-member pass here
  MUST count intra-file callers.
