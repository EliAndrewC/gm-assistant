# Phase 0 Research: settlement/structures.py -> settlement/structures/

Every finding here is a decision the implementation is bound to, or a hazard it must route around.
Findings that led to REJECTING an option are recorded too - that is the point of the file.

---

## R1. The partition: seven modules, and how each grouping was decided

**Decision**: seven submodules, listed in `data-model.md`.

**The method**, and it is not "group by theme". Feature 112's `fields/` and 113's `city/` both cut a
file that was ONE subsystem into facets of that subsystem. `structures.py` is not that: it is
feature 025's residue bucket - the members that were neither field, nor way, nor homestead, nor
funerary ground. So the grouping question here is different, and the rule that answered it is:

> **Group by what a session comes here to change.**

A partition is right if a task ("make the notice board sit closer to the bridgehead", "stop the
packer forcing 57 px between two 28 px houses", "give the merchant estate a second gate") names ONE
file. Applying that to the 33 members produced seven clusters, and the clusters are uneven in size
(72 to 385 lines) precisely because tasks are uneven in size - a partition tuned for equal file
sizes would have to cut a cluster a task does not.

**The three placements a future reader would otherwise re-litigate.** Each is recorded here and
repeated in the package index, because a decision that lives only in a spec file is a decision
nobody will find.

### R1a. `road` and `pasture` -> `ground.py`, and NOT into `water_ways.py` / `land.py`

Neither belongs to the structures subsystem at all. `road` is a way, and the parent package already
has a ways module (`water_ways.py`, which holds lanes, streets, alleys, kido, wards). `pasture` is a
land surface, and the parent has `land.py` (commons, marsh, toe bands, hinterland). Both are here
because feature 025's cut put them here.

**Rejected: move them to their proper parent modules as part of this feature.** Two reasons, and the
second is the load-bearing one:

1. It is a different change with a different risk profile. This feature's whole value proposition is
   that it changes nothing; a cross-mixin relocation touches two files this feature otherwise never
   opens.
2. **It would make the oracle answer two questions at once.** If the byte-identity sweep came back
   dirty, the diff could not distinguish "the package composition is wrong" from "moving `road`
   changed something". An oracle that cannot localize a failure is most of an oracle wasted.

So they get an isolated module, exactly as feature 113 did with `governor_mansion` in `city/civic.py`
for the same reason - and the index records each member's intended eventual destination, which makes
each future move a one-file change plus one index row.

**What `ground.py` legitimately is**, so the module is not merely a leftovers drawer: both members
draw an unbuilt GROUND SURFACE that reserves placement rather than a structure that occupies it -
`road` appends a corridor, `pasture` appends a block poly, and neither records a footprint the
overlap matrix treats as solid. That is a real shared property, and it is what the module docstring
says.

### R1b. The four door/solid probes -> `servants.py`, not `urban.py`

`_solid_records`, `_blocks_any_door`, `_door_is_clear` and `_office_records` read like general
placement utilities and sit textually right after `building`, which is what makes `urban.py` the
tempting home. A consumer census says otherwise - every one of them has exactly one consumer:

| probe | consumers |
|---|---|
| `_solid_records` | `_door_is_clear`, `servant_ranges` |
| `_blocks_any_door` | `servant_ranges` |
| `_door_is_clear` | `servant_ranges` (plus one direct test) |
| `_office_records` | `servant_ranges` |

**Placement follows the caller** - feature 113's `_ring_upslope` precedent, where a helper that read
like a `ring_road` utility went with `farmland_ring` because that is its only caller. Splitting these
four away from `servant_ranges` would mean a session working on the nagaya pass opens two files to
read one algorithm, which is the cost this feature exists to remove.

**And they are not general in the way they look.** `_blocks_any_door` and `_door_is_clear` are
deliberately written to mirror `city_house_doors_unblocked`'s sample geometry point for point - the
same-source doctrine - which makes them tied to a specific check, not to `building` in the abstract.
Their docstrings say so. If a second consumer ever appears, promoting them is a move of four small
methods, and the index says where to put them.

### R1c. `captions.py` here vs `place_caption` in `castle_civic.py`

The parent's `castle_civic.py` holds `place_caption`, the standoff-ladder seat engine used at draw
time. `structures/captions.py` holds the PRIMITIVES underneath that question: what boxes a caption
must miss (`label_blockers`), how wide a caption is AS RECORDED (`label_caption_hw`), whether a given
seat is clear (`label_seat_clear`), the outward-walking search (`clear_label_seat`), and the inverse
test - whether a FOOTPRINT would land under a caption already placed (`_under_a_caption`).

**Rejected: fold them into `castle_civic.py` beside `place_caption`.** Same reasoning as R1a - it is
a cross-mixin move, and it is also not obviously right: three of the five are consumed by
`place_kosatsuba` and `place_punishment_spot`, which live in this package. Recorded as an open
question rather than silently decided, so the next session that touches captions can settle it with
the full picture instead of re-deriving the split.

**Why they are not in `fixtures.py` with their callers**, which R1b's own rule would suggest:
`label_blockers` and `label_caption_hw` are the two members most likely to gain consumers - they are
the answer to "what does a caption collide with", a question every future captioned feature asks -
and `label_seat_clear` is already called from two different siters. That is the distinction from
R1b: those four probes have one caller and a check-shaped contract; these five have several callers
and a general contract. Keeping them separate also keeps `fixtures.py`, the largest module at ~385
lines, from growing another 84.

---

## R2. Clause 14 (derive, don't maintain or split) does not apply

Constitution Principle X clause 14 says an oversized ROSTER-shaped file - re-export lists, `__all__`
duplicates, registry rows a machine could regenerate - should be DERIVED rather than maintained or
split. Evaluated and rejected as not applicable, for the same reason feature 113 recorded it:
`structures.py` is 33 hand-written drawing and placement routines, each with distinct behavior and
most carrying researched grounding in their docstrings. Nothing here restates what code elsewhere
declares, so there is no surface to derive.

The census clause 14 asks for is spent instead on the composed-mixin surface (see
`contracts/mixin-surface.md`), which is what the guard test pins.

---

## R3. The oracle: the pool corpus, captured from a scratch copy of the PRE-split tree

**Decision**: sweep every `pool/` generator - live and frozen alike - in a scratch copy of the tree,
hash every resulting `.json` / `.svg` / `.png`, and compare. `wip/shiro-daika.gen.py` is excluded.

**Why not the committed manifests.** Feature 110 research R3 proved them unreliable as a baseline:
the engine may have drifted since they were committed, so a mismatch would be indistinguishable from
a refactor bug. Only a pre-change run of the SAME tree is a valid fixed point.

**Why the frozen legacy maps are included.** `--frozen-ok` is required or `regen` prints `FROZEN` and
skips them, and for THIS feature they carry most of the diagnostic power. The members being moved
skew urban - `servant_ranges`, `rowpack`, `merchant_estates`, `drum_tower`, `theater_stage`,
`fire_tower`, `place_punishment_spot` are town/city/capital features, and the scripted cohort is
hamlets. A sweep of the live scripted maps alone would leave `servants.py` and most of `fixtures.py`
unexercised - an oracle with a hole exactly where the code is.

Reading a frozen map does not violate the freeze. The freeze forbids maintaining frozen maps against
new rules, re-gating them, and committing regenerated bytes; it does not forbid running one as a
differential oracle in a scratch tree. Features 110, 111, 112 and 113 all used this method.

**Why `wip/shiro-daika.gen.py` is excluded**: feature 112 research R11 measured it at over 6 minutes
without output against roughly 3 minutes for the whole pool. It is capital-scale and exercises no
member of this package that the three provincial cities do not. Two sweeps at +6 minutes each buys
no diagnostic power.

**The false-green trap, inherited verbatim from 113 R9 and worth repeating because it fires
silently.** `cp -a` copies the COMMITTED pool artifacts into the scratch tree. If the sweep dies
early - `regen` fans out across processes and a `resvg` render can be OOM-killed when something
heavy runs beside it - the artifacts sitting there are the committed ones, untouched, and they hash
equal to a baseline that faithfully reproduced those same bytes. `diff` prints nothing and the oracle
reports success having tested nothing. So the pass condition is THREE things, not one: empty hash
diff, regen exit code 0, and a `REGENERATED` count equal to the baseline's. And do not run the sweep
beside an `-n auto` pytest or a `make done`.

---

## R4. Two sweeps, not seven - because there is no decomposition stage

Feature 113 ran its byte-identity sweep seven times: once after the pure move and once after each of
six method decompositions, because each decomposition is a real behavior risk (an RNG call changing
position relative to another re-rolls a map). This feature runs it **twice**: once to capture the
baseline, once after the move.

**Why there is no decomposition stage.** The bar features 112 and 113 converged on is ~150 lines per
function. The four largest members here are `rowpack` (130), `servant_ranges` (128), `pack` (115) and
`place_kosatsuba` (110) - all under it. Nothing here resembles `city_wall`'s 339 lines. So there is
no clause-12 debt to pay, and adding a decomposition stage would put behavior-changing risk inside a
feature whose entire value is that it changes nothing.

**And the decomposition that IS coming has a better owner.** The skill's `CLAUDE.md` names the next
substantial engine job as the placer's rotated-footprint fix (CENTER vs FOOTPRINT item 3, then item
2's `sat_overlap` swap). That work rewrites the inside of `pack`/`rowpack`/`_fits` and will
re-partition them for its own reasons, against a `packing.py` that is by then 274 lines rather than a
1,459-line file. Decomposing them speculatively now would be work that feature throws away.

---

## R5. The transformer, and the slicing rule that must not be re-derived

**Decision**: adapt `specs/113-city-package/split_city.py` (itself adapted from 112's
`split_fields.py`, itself from 025's `split_settlement.py`) rather than write a fresh one or move the
code by hand.

**The slicing rule is the part a fresh implementation gets wrong.** Blocks are sliced as
`(previous member's end + 1 .. this member's end)`, NOT by the member's own `lineno`. That span
carries three things `node.lineno` drops: decorator lines (`@staticmethod` sits ABOVE the `def`,
and `ast` reports `FunctionDef.lineno` at the `def`), the blank lines, and any comment block written
above the member. **In this project the third is the real loss** - a comment above a method is
usually researched grounding, and a "pure move" that drops a why-comment is not pure.

`structures.py` has this in force. `URBAN`'s block carries the `# urban building palette and default
footprints, keyed by town caste/role` line above it; `SERVANT_RANGE_DEPTH_FT` and `_OFFICE_STANDOFF`
carry their measurement citations as trailing comments on the assignment itself.

**The two-dot rewrite applies to the BODY as well as the header.** Feature 112 rewrote only the
header because none of its methods had an in-body import; 113 found `_wall_point_at_arc` doing a lazy
`from .core import Settlement` inside its body, which left alone would silently resolve to a
non-existent `settlement.city.core`. `structures.py` has no in-body import today (verified: no
`import` statement inside any member), but the body rewrite stays in the transformer - it costs
nothing and the next split inherits it.

**Three class-level `Assign` members** (`URBAN`, `SERVANT_RANGE_DEPTH_FT`, `_OFFICE_STANDOFF`) mean
113's dormant `Assign` branch in `member_name()` actually fires here, as it did in 112 for the
`_PADDY_*_KINDS` matrices. The refusal path for an unnamed class-body member stays.

**The transformer must refuse, not warn.** A partition that does not exactly cover the class exits
non-zero naming the missing and extra members. A method silently dropped produces a package that
imports cleanly, type-checks cleanly and draws nothing - surfacing only when whichever generator
calls it happens to run.

---

## R6. Consumer census: exactly one file outside `settlement/` must change

Swept the whole skill for references to the module, the mixin, and each of the 33 member names.

**Nothing imports the submodule by path.** The only import is `settlement/core.py`'s
`from .structures import StructuresMixin`, which a package satisfies unchanged. No test patches a
`settlement.structures` module-level name (consistent with the 025 census).

**Pool generators reach three members directly on the instance** - `s._dims(...)` (nagahara, minami),
`s.try_building(...)`, `s.open_face_rot(...)` - and all three keep resolving through the MRO. No gen
changes.

**One consumer asserts on the FILENAME**, and it is the feature's only required edit outside the
package:

    tests/tools/test_why_placed.py:80
        assert "structures.py" in files  # ...the engine method that chose the spot

`why_placed` walks `inspect.stack()` and reports the frame's file basename. The traced call there is
`s.try_building(300, 300, "shop")` -> `building`, which after the split lives in
`settlement/structures/urban.py`. So the assertion becomes `"urban.py"`, with its comment updated to
name feature 114 the way the current one names the 025 split. This is a filename string, not
behavior - and it is a genuinely useful assertion, so it is updated rather than deleted.

**One near-miss worth recording so it is not mistaken for a hit**: `check_village/driver.py` and the
city battery segments define a local `URBAN` boolean (`scale in ("city", "capital")`). Unrelated to
`StructuresMixin.URBAN`, the building palette. Grep for `URBAN` in this repo returns both.

---

## R7. Coverage cannot move, and a movement is a signal rather than a number to bank

The Makefile enforces 100% on every module except `settlement/` (combined), which holds the
`SETTLEMENT_COV_FLOOR` ratchet at 94. A pure move relocates executable lines without adding,
removing or altering one, and the floor is measured over the package COMBINED - so the figure is
arithmetically unchanged.

**If it moves, investigate; do not re-baseline.** A drop means something is not being imported or
not being reached (a member lost, a module not composed). A rise means lines vanished. Either way the
correct response is to find out why, not to edit the floor. Feature 113 recorded the same rule and it
held.

Never lower the floor. Raising it is legitimate only to a figure THIS feature measured, with the
measurement recorded in the comment above it - and a pure move has no business raising it.

---

## R8. Monkeypatching after the split

Submodules bind helper names at import (`from .._geom import poly_gap`), so patching
`settlement.structures.poly_gap` would reach nothing. The rule, unchanged from `fields/` and `city/`:
patch the DEFINING module (`settlement._geom.poly_gap`), or - for anything reached through `self.` -
patch `settlement.Settlement`, since class-level patching is unaffected by the split.

Census: no test in the suite patches a module-level name in `settlement/structures.py`. The tests
that do patch reach `settlement.Settlement.<method>`, which is exactly the case the split preserves.
Recorded in the package index so the next reader does not have to re-run the census.

---

## R9. Principle XII (Historical Grounding Bookends) does not apply

The gate asks whether the feature changes what a generator ASSERTS ABOUT THE WORLD. It does not: no
element is added or changed, no size, spacing, prevalence or siting rule is touched, and the oracle
is byte-identity of the rendered artifacts - which is a stronger statement than "the depiction is
unchanged", since it proves the pixels are.

The closing bookend (re-examine the rendered PNG) is likewise satisfied by construction: an empty
hash diff over every `.png` in the pool is the same claim the eye would be making, checked exhaustively.

**The historical grounding already IN the file is what R5's slicing rule protects.** `manor`'s
glyph-not-scale-drawing doctrine, `servant_ranges`' nagaya sourcing, `drum_tower`'s re-verified
Pingyao footprint, `kosatsuba`'s marker-floor reasoning - all of it lives in docstrings and
above-method comments, and all of it must arrive in the new modules intact. That is a Phase 3
verification step, not an assumption.

---

## R10. Module and mixin names

Submodule names are short nouns naming the SUBJECT (`compounds`, `ground`, `urban`, `servants`,
`packing`, `captions`, `fixtures`), matching the convention `fields/` and `city/` set. Mixin names
are the subject plus `Mixin`, disambiguated where a bare name would collide or mislead:

- `UrbanBuildingMixin`, not `UrbanMixin` - `URBAN` is an overloaded token in this repo (R6).
- `PublicFixturesMixin`, not `FixturesMixin` - "fixture" means pytest fixture everywhere else in the
  tree; these are the settlement's public street furniture.
- `CaptionProbesMixin`, not `CaptionsMixin` - the parent's `castle_civic.py` owns caption SEATING
  (`place_caption`); this module owns the probes underneath it (R1c).
- `ServantRangesMixin` names the pass, since the four probes are there because they serve it (R1b).
- `GroundMixin` names the shared property (unbuilt ground surfaces that reserve placement), not the
  members (R1a).

No name collides with an existing mixin in the tree (`FieldsMixin`, `FieldFeaturesMixin`,
`WaterWaysMixin`, `ShrinesWellsMixin`, `TradesMixin`, `HomesteadPartsMixin`, `LandMixin`,
`CivicGroundsMixin`, `CityMixin`, `CastleCivicMixin`, `HousesMixin`, `RollingMixin`, `FinishMixin`,
and `city/`'s six).

---

## R11. The test file is not split, and that is a decision rather than an oversight

`tests/settlement/test_structures.py` is 591 raw lines - under the ~1,000-line clause-13 bar. Its two
predecessors were left whole at 589 (`test_fields.py`) and 754 (`test_city.py`).

Clause 13 explicitly gives tests no exemption, and this feature does not claim one: the file is
simply not over the bar. Splitting it pre-emptively would also break the one-test-file-per-mixin
mirror the `tests/` CLAUDE.md describes, since the package composes back to a single mixin. When it
crosses ~1,000 lines it becomes `tests/settlement/test_structures/`, mirroring the package - and the
package index says so, so the next session does not have to decide it fresh.

---

## R12. What the implementation learned (added post-hoc, per tasks T032)

Recorded so the next split in this lineage inherits it rather than re-deriving it.

**The plan was right about the partition; nothing moved.** All 33 members landed exactly where
`data-model.md` assigned them, and no assignment was reconsidered during implementation. The
predicted line counts were within a few percent of the pruned-and-formatted result (predicted
254/72/159/196/274/84/385 block lines; actual files 277/92/177/218/292/101/407 including each
module's own docstring and pruned header).

**Two things worth carrying forward:**

- **The transformer needed a refusal path its predecessor did not have.** 113's `split_city.py`
  checks only that the partition COVERS the class (`missing=` / `extra=`). That is sufficient for a
  six-way partition of 27 members and not for a seven-way partition of 33: a copy-paste duplicate
  assigns one name to two modules, which leaves `sorted(assigned) != sorted(blocks)` *false* if the
  duplicate displaces nothing - the member is simply emitted twice, the package imports fine, and
  the collision assertion in the guard is the only thing standing between that and one silently dead
  implementation. Added an explicit duplicate-assignment check ahead of the coverage check, and
  proved it fires (tasks T008). **Any future split with more than a handful of modules wants both.**

- **The guard's ATTRIBUTE half earned its keep, and the earlier features' guards would have missed
  it.** Features 112 and 113 both censused members with `callable(v) or isinstance(v, staticmethod)`,
  which cannot see `URBAN` (a dict), `SERVANT_RANGE_DEPTH_FT` or `_OFFICE_STANDOFF` (floats) - 112
  hit this and wrote a SECOND test naming its three matrices explicitly, which is a list that has to
  be remembered into. Censusing `{k for k in vars(cls) if not k.startswith("__")}` covers methods
  and data in one assertion with nothing to remember, and it was proven red on `URBAN` (T018).
  **Use the vars-based census in the next split**, not the callable-based one.

**One prediction that held and is worth stating because it is cheap to doubt:** a pure move really
did leave coverage untouched. R7 pre-committed to treating any movement as a defect to investigate
rather than a floor to re-baseline, and there was nothing to investigate.
