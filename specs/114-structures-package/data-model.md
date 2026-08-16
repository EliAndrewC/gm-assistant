# Data Model: the `settlement/structures/` partition

There is no persisted data model in this feature - the "entities" are the class-body members of
`StructuresMixin` and the modules they are assigned to. This file is the authoritative partition;
`split_structures.py`'s `MODULES` dict must match it exactly, and the transformer refuses to run if
the union of the seven tables is not exactly the class.

**Census of the source** (measured, not assumed): `settlement/structures.py` is 1,459 raw lines and
`StructuresMixin` has **33** class-body members - 30 `FunctionDef` and 3 `Assign`. Members are listed
below in SOURCE order within each table; "lines" is the sliced BLOCK size (the member plus its
decorators, blank lines and any comment block above it), which is what actually moves.

---

## `compounds.py` - `CompoundsMixin`

> Walled compounds shown as a glyph on a settlement map: the samurai manor and the merchant estate.

| member | lines | note |
|---|---|---|
| `manor` | 143 | the glyph-not-a-scale-drawing doctrine lives in its docstring |
| `_estate_wall_clear` | 40 | the siting predicate `merchant_estate`'s slide fan uses |
| `merchant_estate` | 48 | |
| `merchant_estates` | 23 | rolls the count, then seats from vetted candidates |

**254 lines.** `_estate_wall_clear` goes here rather than with the placement machinery because its
only consumer is `merchant_estate` (R1b's rule), and because it mirrors the
`merchant_estate_wall_clear_of_*` gate geometry - it is that feature's predicate, not a general one.

---

## `ground.py` - `GroundMixin`

> Unbuilt GROUND SURFACES that reserve placement rather than structures that occupy it.

| member | lines | note |
|---|---|---|
| `road` | 33 | appends a corridor; records `M["road"]`/`M["roads"]` |
| `pasture` | 39 | appends a block poly; records `M["pastures"]` |

**72 lines.** Neither belongs to the structures subsystem - `road` belongs with `water_ways.py`'s
ways, `pasture` with `land.py`'s land surfaces. They are isolated here so each eventual move is a
one-file change. Full reasoning: research R1a. **Their intended destinations are recorded in the
package index**, not only here.

---

## `urban.py` - `UrbanBuildingMixin`

> The urban building glyph, its palette, and the per-building helpers that seat ONE of them.

| member | lines | note |
|---|---|---|
| `URBAN` | 22 | class-level dict: palette + default footprints by caste/role |
| `building` | 74 | the one seat every pack, frontage and top-up funnels through |
| `_dims` | 4 | palette lookup scaled by `bscale`; called directly from pool gens |
| `try_building` | 6 | `_fits` then `building` |
| `_face_street_rot` | 20 | |
| `open_face_rot` | 33 | |

**159 lines.** The four door/solid probes textually adjacent to `building` are NOT here - see
`servants.py` and research R1b.

---

## `servants.py` - `ServantRangesMixin`

> The nagaya pass that attaches a servant range to each ward samurai household, and the four probes
> that exist to serve it.

| member | lines | note |
|---|---|---|
| `SERVANT_RANGE_DEPTH_FT` | 2 | class-level: 15.0, the measured nagayamon depth |
| `_OFFICE_STANDOFF` | 1 | class-level: 15.0, a px over the check's 14 |
| `_solid_records` | 15 | sweeps the manifest rather than a hand list of keys |
| `_blocks_any_door` | 24 | mirrors `city_house_doors_unblocked` sample for sample |
| `_door_is_clear` | 20 | the mirror of the above |
| `_office_records` | 6 | |
| `servant_ranges` | 128 | |

**196 lines.** The two class constants move WITH the methods that read them
(`servant_ranges` reads both). A class attribute is as easy to lose in a split as a method and much
easier to overlook, which is why the guard test's census covers attributes (feature 112's
`_PADDY_*_KINDS` precedent).

---

## `packing.py` - `PackingMixin`

> The two multi-building placement engines and the shortfall bookkeeping they share.

| member | lines | note |
|---|---|---|
| `rowpack` | 130 | walks an INDEX |
| `pack` | 115 | POPs its work-list |
| `_shortfall` | 29 | also called from `houses.py`'s `frontage`, via `self.` |

**274 lines.** The index-vs-pop asymmetry between `rowpack` and `pack` is a documented bug source
(skill `CLAUDE.md`, "Two placer bugs of the same shape"), which is an argument for keeping the two
in one file where the difference is visible, not for separating them.

---

## `captions.py` - `CaptionProbesMixin`

> The primitives a siter uses to ask whether a caption fits, and whether a footprint would land
> under one.

| member | lines | note |
|---|---|---|
| `label_blockers` | 32 | DERIVED from the manifest, never a hand list |
| `label_caption_hw` | 8 | the half-width AS RECORDED, not as PIL measures it |
| `label_seat_clear` | 11 | |
| `clear_label_seat` | 19 | the outward-walking 16-ring search |
| `_under_a_caption` | 14 | the inverse test |

**84 lines.** Distinct from `castle_civic.py`'s `place_caption`, which is the draw-time seat LADDER.
Whether these should eventually join it is an OPEN question, recorded in research R1c rather than
silently decided.

---

## `fixtures.py` - `PublicFixturesMixin`

> The settlement's public street furniture and civic fixtures, and the two auto-siters.

| member | lines | note |
|---|---|---|
| `theater_stage` | 52 | |
| `fire_tower` | 31 | |
| `kosatsuba` | 70 | the notice board glyph |
| `place_kosatsuba` | 110 | the auto-siter |
| `place_punishment_spot` | 78 | the board's sibling; `punishment_spot` itself is in `civic_grounds.py` |
| `drum_tower` | 44 | |

**385 lines** - the largest module, and the one to watch. It is a coherent cluster (public fixtures
sited by foot traffic) but it is also the module most likely to need a further cut. The bar to
re-split it is a member crossing ~150 lines or the file crossing ~500; the natural seam is
glyph-drawers (`theater_stage`, `fire_tower`, `kosatsuba`, `drum_tower`) versus auto-siters
(`place_kosatsuba`, `place_punishment_spot`). Recorded in the index so the next session inherits the
seam rather than choosing one under pressure.

---

## `__init__.py` - the composed `StructuresMixin`

    class StructuresMixin(
        CompoundsMixin, GroundMixin, UrbanBuildingMixin, ServantRangesMixin,
        PackingMixin, CaptionProbesMixin, PublicFixturesMixin,
    ):
        """The composed structures surface. No members of its own by design."""

**No members of its own, by design.** It exists ONLY so `settlement/core.py` keeps its single
`from .structures import StructuresMixin` and its position in the `class Settlement(...)` base list -
which means the partition above can be re-cut later without touching `core.py`.

Base order is source order and is behaviorally irrelevant, because no name is defined twice - which
is exactly what the guard's collision assertion exists to keep true.

**Cross-submodule calls need no import.** Every sub-mixin is a base of the same `Settlement`, so
`self._dims(...)` from `packing.py` resolves through the MRO wherever the caller's text lives. The
engine already relies on this from outside the package: `houses.py`'s `frontage` calls
`self._shortfall(...)`, and `_fits` (in `houses.py`) is called from `try_building` here.

**The cross-submodule calls inside this package**, enumerated so a future re-cut can see the coupling
at a glance:

| from | to | call |
|---|---|---|
| `compounds.py` | `urban.py` | `merchant_estate` -> `building`, `_dims` |
| `packing.py` | `urban.py` | `pack` -> `try_building`, `_dims`, `_face_street_rot`, `open_face_rot`; `rowpack` -> `building`, `_dims` |
| `servants.py` | `urban.py` | `servant_ranges` -> `building` |
| `fixtures.py` | `captions.py` | `place_kosatsuba` -> `label_blockers`, `label_caption_hw`, `label_seat_clear`; `place_punishment_spot` -> `clear_label_seat`, `_under_a_caption` |
| `fixtures.py` | `fixtures.py` | `place_kosatsuba` -> `kosatsuba` |
| `captions.py` | `captions.py` | `clear_label_seat` -> `label_caption_hw`, `label_blockers`, `label_seat_clear` |

`urban.py` is the hub - three of the other six call into it and it calls out to none of them, which
is the shape a well-cut partition should have.

---

## Invariants the transformer and the guard enforce

1. **Exactly 33 members, each in exactly one module.** Transformer refuses otherwise, naming
   `missing=` and `extra=`.
2. **Every member arrives with its decorators, blank lines and the comment block above it.** The
   slicing rule; research R5.
3. **Every submodule carries `if TYPE_CHECKING: from ..core import Settlement`** (two dots) and every
   method keeps `self: "Settlement"` - what lets `mypy --strict` resolve cross-subsystem attribute
   access with no runtime import cycle.
4. **`settlement/core.py` is byte-unchanged**, proven by an empty `git diff --stat`.
5. **`settlement/structures.py` is deleted** - a stale module beside a package of the same name is a
   shadowing hazard.
