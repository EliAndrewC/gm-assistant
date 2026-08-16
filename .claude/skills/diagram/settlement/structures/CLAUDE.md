# settlement/structures/ - the structures subsystem as a package

Split from the 1,459-line `settlement/structures.py` by feature 114 (constitution Principle X
clause 13 - the cost being managed is context-window tokens). **Load only the file the task calls
for**; this index is the map. `from .structures import StructuresMixin` still resolves and
`settlement/core.py` is byte-unchanged, so nothing above this directory knows the split happened.

**This package was never ONE subsystem, and that shapes everything below.** `fields/` is the field
engine cut four ways; `city/` is one tier cut six ways. `structures.py` was feature 025's RESIDUE
BUCKET - whatever was neither field, nor way, nor homestead, nor funerary ground. So the seven
modules are grouped by **what a session comes here to change**, not by theme, and they are
deliberately uneven in size (92 to 407 lines) because tasks are uneven in size. A partition tuned
for equal files would have to cut a cluster that no task cuts.

## Look here when

| file | look here when |
|---|---|
| `__init__.py` | you need the composition itself; never add logic here |
| `compounds.py` | a WALLED COMPOUND drawn as a glyph: `manor` (the samurai compound - its glyph-not-a-scale-drawing doctrine is in its docstring), `merchant_estate` + `merchant_estates` (the rolled count and the vetted-seat list), and `_estate_wall_clear`, the siting predicate that keeps a compound wall off water, fire towers and the street net |
| `ground.py` | `road` (a bordered roadbed + its no-build corridor) or `pasture` (grazing land). Two members that do NOT belong to this subsystem at all - see "Three placements you will want to fix" below |
| `urban.py` | the generic urban BUILDING: the `URBAN` palette (fill/edge/footprint by caste and role), `building` itself - the one seat every pack, frontage and top-up funnels through, and where the samurai-ward refusal lives - plus the per-building seating helpers `_dims`, `try_building`, `_face_street_rot`, `open_face_rot` |
| `servants.py` | the SERVANT RANGE (nagaya) pass: `servant_ranges` and the four probes that exist to serve it (`_solid_records`, `_blocks_any_door`, `_door_is_clear`, `_office_records`), plus `SERVANT_RANGE_DEPTH_FT` and `_OFFICE_STANDOFF` |
| `packing.py` | the two multi-building placement ENGINES - `rowpack` (city row housing: terraces, back-to-back pairs, roji and courts) and `pack` (grid-scan district fill, footpaths, street-facing) - and `_shortfall`, the authored-vs-landed bookkeeping both use (and `houses.py`'s `frontage` too) |
| `captions.py` | the caption PROBES: what boxes a caption must miss (`label_blockers`), how wide it is AS RECORDED (`label_caption_hw`), whether a seat is clear (`label_seat_clear`), the outward-walking search (`clear_label_seat`), and the inverse test - would a FOOTPRINT land under a caption already placed (`_under_a_caption`) |
| `fixtures.py` | public street furniture and civic fixtures: `theater_stage`, `fire_tower`, `kosatsuba` (the notice board), `drum_tower`, and the two traffic-driven auto-siters `place_kosatsuba` and `place_punishment_spot` |

## Composition, and why it is in `__init__.py`

`StructuresMixin` is
`class StructuresMixin(CompoundsMixin, GroundMixin, UrbanBuildingMixin, ServantRangesMixin, PackingMixin, CaptionProbesMixin, PublicFixturesMixin)`
with no members of its own. It exists ONLY so `core.py` keeps its single import and `StructuresMixin`
keeps its position in the `class Settlement(...)` base list - which means the partition here can be
re-cut later without touching `core.py`.

**Cross-submodule calls need no import.** Every sub-mixin is a base of the same `Settlement`, so
`self._dims(...)` from `packing.py` resolves through the MRO wherever the caller's text lives. The
engine already relies on this from outside the package too: `houses.py`'s `frontage` calls
`self._shortfall(...)`, and `try_building` here calls `self._fits(...)`, which lives in `houses.py`.

**`urban.py` is the hub**, which is the shape a well-cut partition should have - three of the other
six call into it and it calls out to none of them:

| from | to | call |
|---|---|---|
| `compounds.py` | `urban.py` | `merchant_estate` -> `building`, `_dims` |
| `packing.py` | `urban.py` | `pack` -> `try_building`, `_dims`, `_face_street_rot`, `open_face_rot`; `rowpack` -> `building`, `_dims` |
| `servants.py` | `urban.py` | `servant_ranges` -> `building` |
| `fixtures.py` | `captions.py` | `place_kosatsuba` -> `label_blockers`, `label_caption_hw`, `label_seat_clear`; `place_punishment_spot` -> `clear_label_seat`, `_under_a_caption` |

## Three placements you will want to "fix" - each is deliberate

Recorded here rather than only in `specs/114-structures-package/research.md`, because a decision
that lives only in a spec file is a decision nobody will find.

### `road` and `pasture` are in a module of their own because neither belongs HERE

`road` belongs with `water_ways.py`'s ways (lanes, streets, alleys, kido); `pasture` belongs with
`land.py`'s land surfaces (commons, marsh, toe bands, hinterland). Both are in this package only
because feature 025's cut put them here.

They were NOT moved to their proper homes by feature 114, and the reason is not timidity: moving a
member between parent-level mixins is a different change with a different risk profile, and folding
it in would have made the byte-identity oracle answer two questions at once - a dirty diff could not
then distinguish "the composition is wrong" from "moving `road` changed something". Isolating them
makes each eventual move a one-file change plus one row of this table. Same call feature 113 made
with `governor_mansion` in `city/civic.py`.

What the module legitimately IS, so it is not merely a leftovers drawer: both members draw an
unbuilt GROUND SURFACE that reserves placement rather than a structure that occupies it - `road`
appends a corridor, `pasture` appends a block poly, and neither records a footprint the overlap
matrix treats as solid.

### The four door/solid probes live with `servant_ranges`, not with `building`

`_solid_records`, `_blocks_any_door`, `_door_is_clear` and `_office_records` read like general
placement utilities and sat textually right after `building` in the old file. A census gives each of
them exactly one consumer - `servant_ranges` (`_solid_records` also serving `_door_is_clear`) - and
**placement follows the caller** (feature 113's `_ring_upslope` precedent). Splitting them away
would mean a session working on the nagaya pass opens two files to read one algorithm.

They are also less general than they look: `_blocks_any_door` and `_door_is_clear` mirror
`city_house_doors_unblocked`'s sample geometry point for point - the same-source doctrine - so they
are tied to a specific check, not to `building` in the abstract. If a second consumer appears,
promote them to `urban.py`; it is a move of four small methods.

### `captions.py` here vs `place_caption` in `castle_civic.py` - an OPEN question

`castle_civic.py` holds `place_caption`, the standoff-ladder seat engine used at draw time; this
package holds the primitives underneath it. Whether they should eventually live together is
**undecided**, not settled. The argument for folding: one caption subsystem. The argument against:
three of the five are consumed by `place_kosatsuba` and `place_punishment_spot`, which live here.

**Implementation sketch for whoever decides it** (per the skill CLAUDE.md's "an OPEN DECISION
carries an implementation sketch" rule): the change is to move the five members into
`castle_civic.py`'s `CastleCivicMixin`, delete `captions.py` and its base from `__init__.py`, and
drop its row from this table. Nothing else moves - every consumer reaches them through `self.`, so
no call site changes. What holds it is `tests/settlement/test_structures.py`'s composed-surface
guard: the five names must move OUT of `_STRUCTURES_SURFACE` in the same commit, or assertion 1
fails naming them, which is the guard working. The deliberate exclusion is `_under_a_caption` - it
is the INVERSE test (a footprint under someone else's caption) and its only consumer is
`place_punishment_spot`, so by the R1b rule above it stays here even if the other four go.

## Two thresholds, so the next session does not decide them under pressure

- **`fixtures.py` is the largest module at 407 lines.** Re-split it when it crosses ~500 lines or
  any member crosses ~150. The seam is **glyph-drawers** (`theater_stage`, `fire_tower`,
  `kosatsuba`, `drum_tower`) versus **auto-siters** (`place_kosatsuba`, `place_punishment_spot`) -
  the two halves share nothing but the subject.
- **`tests/settlement/test_structures.py` stays ONE file** at its current ~690 lines. When it
  crosses ~1,000 it becomes `tests/settlement/test_structures/`, mirroring this package. Clause 13
  gives tests no exemption; this file is simply not over the bar yet.

## Monkeypatching

Each submodule binds shared helper names at import (`from .._geom import point_in_poly`), so
patching `settlement.structures.point_in_poly` reaches nothing. Patch the DEFINING module
(`settlement._geom.point_in_poly`) or, for anything reached through `self.`, patch
`settlement.Settlement` - class-level patching is unaffected by the split. As of feature 114 no test
in the suite patches a module-level name in this package.

## The guard, and what it is for

`tests/settlement/test_structures.py` holds the 33 pre-split members as a SUBSET of what the
composed class exposes, and a second test holds that no two sub-mixins define the same name. All
three breakage classes were proven to fire before the guard was trusted (feature 114 T006/T017/T018).

Three things about its shape:

- **Subset, not equality** - so adding a member here needs no bookkeeping. The direction that HIDES
  is a member going missing: an addition is visible in review, while a subtraction surfaces only
  when whichever generator happens to call it runs.
- **The census admits ATTRIBUTES, not just callables.** `URBAN`, `SERVANT_RANGE_DEPTH_FT` and
  `_OFFICE_STANDOFF` are class-body members and move as deliberately as the methods. Feature 112's
  guard counted callables only and needed a separate test for its `_PADDY_*_KINDS` matrices; this
  one covers all 33 in one assertion.
- **The collision half is the one that is easy to under-rate**: a member defined by two sub-mixins
  produces a working import, a clean `mypy --strict`, and one silently dead implementation, because
  MRO just picks the first base.

## Function scale

Nothing here was decomposed, and that is a measurement rather than an omission. The largest members
are `rowpack` (130 raw lines), `servant_ranges` (128), `pack` (115) and `place_kosatsuba` (110) -
all under the ~150-line bar features 112 and 113 converged on, and nothing resembling `city_wall`'s
339. The decomposition that IS coming has a better owner: the placer's rotated-footprint fix (the
skill `CLAUDE.md`'s CENTER vs FOOTPRINT item 3, then item 2's `sat_overlap` swap) rewrites the
inside of `pack`/`rowpack`/`_fits` and will re-partition them for its own reasons.
