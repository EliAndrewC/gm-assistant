# Data Model: the partition of `ShrinesWellsMixin`

This is the AUTHORITATIVE partition. `split_shrines_wells.py` encodes the same table and refuses to
run if the two disagree with the class (a member in no module, in two modules, or a member the
partition does not name). Line spans are from an AST census of the pre-split file at
`settlement/shrines_wells.py` (1,179 lines, 38 members, all `FunctionDef`, no class-level `Assign`).

`lines` is the member's slice - *previous member's end + 1* through *its own end* - so the numbers
include each member's leading comment block and blank lines, and they sum to the class body exactly.

## The seven modules

### `shrines.py` -> `ShrineHallsMixin` (5 members, 230 lines)

The hall and shrine GLYPHS, the hill they may stand on, and the hall's caption.

| member | pre-split lines | span | note |
|---|---|---|---|
| `hill` | 35-67 | 33 | the terraced hill glyph; returns the summit point a shrine sits on |
| `shrine` | 68-81 | 14 | the legacy simple shrine glyph (true scale since 2026-07-21) |
| `small_shrine` | 82-104 | 23 | the wayside/neighborhood shrine: shed + its own little torii |
| `_hall_caption_y` | 749-794 | 46 | where the hall's caption goes so it never covers its own sando (R1d) |
| `shrine_hall` | 900-1013 | 114 | the standalone religious hall: the roll, the avenue, the glyph, the caption band |

### `torii.py` -> `ToriiAvenueMixin` (7 members, 179 lines)

The arch glyph and the whole approach engine: the gen authors the LINE, the engine owns the count,
the stride, the threshold and the wall clearance.

| member | pre-split lines | span | note |
|---|---|---|---|
| `_assert_walls_clear_of_torii` | 675-688 | 14 | re-asks the question when a WALL lands after an arch; called from three modules outside the package |
| `_avenue_pitch` | 689-714 | 26 | holds the avenue to the house pitch |
| `_avenue_at_threshold` | 715-748 | 34 | seats the innermost arch one pitch off the hall's footprint |
| `_avenue_short_of_walls` | 795-838 | 44 | scales the run back so no arch stands in a wall |
| `_torii` | 839-868 | 30 | ONE arch, true scale; refuses to stand in a barrier |
| `torii_path` | 869-877 | 9 | hand-placed arches at an ascent's interior vertices |
| `torii_even` | 878-899 | 22 | `count` arches spread by arc length (Kikuta style) |

### `wellground.py` -> `WellGroundMixin` (7 members, 172 lines) - **the hub**

One question - *is this ground fit to sink a wellhead in?* - and everything that makes asking it
cheap. Calls nothing else in the package (R10).

| member | pre-split lines | span | note |
|---|---|---|---|
| `_build_well_index` | 105-131 | 27 | the three `PointGrid`s: watercourses, dry plots, paddy wet rings |
| `_terrain_fingerprint` | 132-143 | 12 | expensive on purpose - runs twice per PASS, not per candidate |
| `frozen_terrain` | 144-179 | 36 | **the only decorated member** (`@contextlib.contextmanager`) - see research R5 |
| `_well_index` | 180-183 | 4 | frozen index if inside a scope, else built per call |
| `_wet_toe_keepout` | 184-211 | 28 | the reed toe below all cultivation, derived before the reeds are drawn |
| `_well_ground_clear` | 212-264 | 53 | the predicate itself; carries the 45-minute-grind post-mortem |
| `_in_scrub_cover` | 529-540 | 12 | the grazed-waste refusal, shared with `open_seat(well=True)` |

### `wells.py` -> `WellsMixin` (8 members, 275 lines)

The wellhead glyph, and the four passes that put wells on a map.

| member | pre-split lines | span | note |
|---|---|---|---|
| `_well_vr` | 265-273 | 9 | the drawn roof half-size placement must predict; also read by `civic_grounds.py` |
| `well` | 274-309 | 36 | the glyph: curb + shaft + well-house roof, and its `placed`/`block_polys` reservation |
| `farm_wells` | 310-323 | 14 | the farm-belt pass (scoped RNG + frozen terrain) |
| `_farm_wells` | 324-412 | 89 | its greedy cluster cover, the dooryard rings, and the envelope-suspended fallback |
| `well_at` | 413-459 | 47 | place ONE well if the spot is clear; carries the 30 px-vs-`ftpx` reservation note |
| `place_wells` | 541-555 | 15 | the neighborhood grid scatter (scoped RNG + frozen terrain) |
| `_place_wells` | 556-607 | 52 | the grid, the offsets, the `near` gate and the coverage pass |
| `shrine_well` | 662-674 | 13 | a set-apart shrine's own ablution well - a WELL, filed here (R1c) |

### `seats.py` -> `OpenSeatMixin` (2 members, 69 lines)

The general "where can a `w` x `h` feature stand?" API. Belongs at parent level with `houses.py`;
isolated so that move is a one-file change (R1a).

| member | pre-split lines | span | note |
|---|---|---|---|
| `_footprint_clear` | 460-484 | 25 | nine-sample whole-footprint test against the BOUND only, deliberately |
| `open_seat` | 485-528 | 44 | scans a rect, asks the real `_fits`, returns the best clear seat |

### `byres.py` -> `DraftByresMixin` (2 members, 54 lines)

The draft-animal shed. Belongs at parent level with `homestead_parts.py`; isolated for the same
reason (R1b).

| member | pre-split lines | span | note |
|---|---|---|---|
| `_draw_byre` | 608-617 | 10 | the open-fronted stall glyph |
| `draft_byres` | 618-661 | 44 | the house-driven placement pass (~one byre per 4-5 households) |

### `woods.py` -> `TreeStandsMixin` (7 members, 166 lines)

A wood is a STAND of individual trees, never a terrain wash. Floor drawn early, canopy deferred to
crop time.

| member | pre-split lines | span | note |
|---|---|---|---|
| `_tree_stand` | 1014-1059 | 46 | queues a stand; carries the canopy-density research |
| `flush_tree_stands` | 1060-1071 | 12 | draws every queued canopy at crop time; called from `core.py` and `finish.py` |
| `_draw_stand` | 1072-1101 | 30 | one stand's crowns + fringe, filtered against the complete map |
| `_stand_fringe` | 1102-1133 | 32 | the cut-over margin's thicket-masked advance growth |
| `_crowns` | 1134-1147 | 14 | SVG for a set of crowns, back-to-front; records `M['tree_crowns']` |
| `_fringe_blocked` | 1148-1159 | 12 | ground already spoken for |
| `forest` | 1160-1179 | 20 | the woodland east of a tree line to the canvas edge |

## Composition

`settlement/shrines_wells/__init__.py`:

```python
class ShrinesWellsMixin(
    ShrineHallsMixin,
    ToriiAvenueMixin,
    WellGroundMixin,
    WellsMixin,
    OpenSeatMixin,
    DraftByresMixin,
    TreeStandsMixin,
): ...
```

No members of its own, by design. The base order is source order and is behaviorally irrelevant - no
name is defined twice, which is exactly what the guard's second assertion keeps true. It exists ONLY
so `settlement/core.py` keeps `from .shrines_wells import ShrinesWellsMixin` and its position in the
`class Settlement(...)` base list, which means this partition can be re-cut later without touching
`core.py`.

## Invariants the transformer enforces

1. **Total coverage**: the 38 members of the class are exactly the 38 named above. Any member the
   partition does not name, or names twice, is a REFUSAL (non-zero exit, listing the names).
2. **Source order within a module**: members are emitted in the order listed, which is their
   pre-split source order. Diff-friendliness, nothing more - the order is behaviorally irrelevant.
3. **Verbatim bodies**: each member's text is sliced from *previous end + 1* to *its own end*, so
   decorators, blank lines and leading comment blocks travel with it (research R5). The ONLY text
   deliberately dropped is the two section-divider banners - `# ---- hill + shrine + torii` above
   `hill` and `# ---- landscape / estate features` above `_tree_stand`. Both describe a position in a
   file that will no longer exist, and the first one names a grouping the split dissolves (its torii
   half moves to `torii.py`). Each module's own docstring replaces them, and quickstart step 6b
   checks both that nothing ELSE was lost and that these two really are gone.
4. **Import depth**: `from ._geom` -> `from .._geom`, `from ._knobs` -> `from .._knobs`,
   `from .core` -> `from ..core`, applied to the copied header AND to member bodies (113 found a lazy
   in-body import; this file has none, but the rewrite is free insurance).
5. **No unnamed class-body member**: refuse rather than drop.

## If a module grows: the recorded seams

Recorded now so a future session inherits the cut rather than choosing one under pressure.

- **`wells.py`** (largest, ~275): `farm_wells`/`_farm_wells` is an independent pass sharing only
  `well_at` and the freeze scope with `place_wells`/`_place_wells`. Cut there - `farmwells.py` - if
  either pass grows substantially.
- **`shrines.py`** (~230): `hill` is scenery, not a shrine; it is here because a village shrine
  stands on one. If a second landform arrives, `hill` leaves for a landform module rather than
  `shrines.py` being cut in half.
- **`woods.py`** (~166): the crown-drawing primitives (`_crowns`, `_fringe_blocked`) are the reusable
  half; the stand policy is the rest. No reason to cut today.
