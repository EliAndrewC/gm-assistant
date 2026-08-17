# settlement/_geom/ - the geometry helpers as a package

Split from the 1,303-line `settlement/_geom.py` by feature 117 (constitution Principle X clause 13 -
the cost being managed is context-window tokens). **Load only the file the task calls for**; this
index is the map. `from ._geom import ...`, `from .._geom import ...` and
`from settlement._geom import ...` all resolve exactly as before, so nothing above this directory
knows the split happened - not one of the 41 importing engine files changed.

**This was never "one thing", though its calling convention said so.** The lineage's earlier splits
cut mixin classes; this file looked different because every member is a plain function with no
`self`, and feature 116's spec duly called it "one thing (pure geometry helpers)". An 89-member
census says otherwise: coordinate math, collision predicates, spatial indexes, a placement memo,
caption typography, manifest readers, curve generation, and three things that are not geometry at
all - eight populations that share nothing but feature 025's positional cut. And this is the most
widely imported module in the engine (41 of the 47 files under `settlement/`, plus `check_village`,
`hamletgen` and two `tools/` scripts), so every one of those readers paid for all eight.

## Look here when

| file | look here when |
|---|---|
| `__init__.py` | you need the re-export surface; never add logic here |
| `base.py` | the `Pt` / `Poly` / `Manifest` aliases, the import-time main-tree guard, or the land/crop palette (`LAND`, `PADDY_SHADES`, `FLOODED_SHADES`, `RIPE_SHADES`, `RICE_GREENS`) |
| `primitives.py` | plain coordinate math with no map vocabulary: `point_in_poly`, `seg_closest`, `seg_dist`, `edge_dist`, `segments_cross`, `seg_intersect`, `ring_touches`, `seg_in_ellipse_core`, `_signed_area` |
| `overlap.py` | a footprint's corner ring, or whether two regions meet: `rot_rect` / `_rect_ring` (corners), `stroke_quads` (a polyline as polygons), `sat_overlap` / `rects_overlap`, `poly_gap` / `_aabb_gap` / `box_gap` (the three gap MEASURES - know which one your rule is entitled to), `region_blocked` / `quad_hits_poly` / `quad_hits_seg` / `point_quad_dist` (cell-region tests), `_union_area` |
| `indexes.py` | a per-candidate scan is eating a gen: the `boxed_*` bbox prefilters, `PointGrid` (uniform grid, and its `_MAX_SPAN` clamp), `Indexed` (the registry that versions ITSELF rather than being fingerprinted), `indexed_grid`, `boxed_grid`. **Read the two staleness post-mortems here before adding any cache** |
| `seatmemo.py` | `SeatMemo` - the refusal memo behind a dwelling top-up, its measured 64.6%-re-visit rationale, and the `sync()` invariant it ASSERTS instead of assuming. Also read it before wiring the memo into a new gen: below ~a third re-visits it is a pessimization |
| `labels.py` | caption typography: the standoff ladder (`LABEL_MIN_AIR`, `LABEL_AIR_STEP`, `LABEL_AIR_RINGS`, `LABEL_AIR_CAP`), the two caption sizes (`HALL_CAPTION_FS`, `GOVERNOR_CAPTION_FS`), and tilt/box geometry (`label_tilt` the FOLD, `linear_tilt` the CLAMP, `linear_tilt_full`, `label_quad`, `label_aabb`, `tilt_caption_seat`) |
| `ways.py` | what someone could walk or cart along, read off a manifest: `lane_runs`, `way_beds` (the AVOIDANCE list - it carries the village lane network `lane_runs` does not), `lane_through_gate` + `kido_bar_deg` (a kido squares to the WAY, not to the fence), and the crossing constants `PLANK_*` / `LANDING_FT` / `CARRIED_LANDING_FLOOR_FT` |
| `walls.py` | every wall on the map (`wall_runs`, `_box_hits_run`), what closes a ward against one (`ward_interior`, `WARD_BARRED_KINDS`), and the arches that must stand clear of one (`torii_halfbox`, `torii_seat_on_wall`, `torii_wall_conflicts`, `TORII_PITCH_FT`, `TORII_PITCH_MAX_SPANS`) |
| `extents.py` | the DRAWN extent of a recorded feature, read back off the manifest: `paddy_wet_rings` (the water a wellhead may not stand in), `forest_reveal_x` / `forest_frame_span` (what a canvas-filling wood contributes to the crop), and the stable-yard glyph quads `wellhead_quad` / `trough_quad` / `tower_quad` / `rail_quad` (+ `YARD_GLYPH_SLACK`) |
| `curves.py` | making a line or ring look hand-made: `fillet_polyline` (the swept-bend research), `smooth_closed` / `smooth_points` (Catmull-Rom, and why the manifest records the SAMPLED curve), `organic_bbox`, `organic_poly`, `winding` |
| `village.py` | `village_population`, `_VILLAGE_POP_DIST`, `BUNDLE_PITCH_FT` - and see "Placements that look wrong" below before moving them |

## The surface is DERIVED, not maintained

`__init__.py` is star imports plus an aliased block, and nothing else - Principle X clause 14
(feature 027's idiom, whose exemplar collapsed `check_village/__init__.py` from 3,148 lines to 63).
An 89-name import roster would restate what the submodules already declare, and would go stale the
first time a member moved.

**`import *` does NOT carry underscore names**, so all seven private members are re-exported by the
`as`-alias block. This is not a formality: the surface census caught `_VILLAGE_POP_DIST` missing from
that block the first time it ran, on a package that imported cleanly and passed every other test.
**If you move a private member between submodules, fix its alias line in the same edit.**

## The two guards, and what they are for

`tests/settlement/test_geom.py` holds them, and both were proven red before they were trusted
(`specs/117-geom-package/contracts/surface.md`):

- **The surface census** - all 89 pre-split names still resolve on `settlement._geom`, as a SUBSET
  assertion so a later helper needs no bookkeeping. A dropped member gives a package that imports
  cleanly, type-checks cleanly, and fails only when whichever caller needs it happens to run.
- **The shadowing guard** - no name is defined in two submodules. This one is specific to a
  star-import surface and has no counterpart in the mixin splits: `from .a import *` followed by
  `from .b import *` silently keeps `b`'s binding and leaves `a`'s implementation dead, with no error
  from Python, ruff or `mypy --strict`. A mixin at least keeps a duplicate reachable through the MRO.

A third test reads `base.py` for the bare `_assert_not_main_tree()` call. That call is the one
UNNAMED top-level statement in the pre-split file - the single member a name-keyed partition can drop
- and its failure mode is silence, because every test already runs inside a session clone.

## Layering, so the package stays acyclic

    base  <-  primitives  <-  overlap  <-  { indexes, labels, ways, walls, extents, curves }

`seatmemo.py` and `village.py` import nothing from the package. No submodule imports from a module to
its right. **Respect the order when adding a member** - and note that Python 3.14 evaluates
annotations lazily (PEP 649), so an annotation-only reference is NOT an import dependency and a cycle
invented to satisfy one is a cycle for nothing. `indexed_grid` annotating `PointGrid` ~140 lines
before it is defined is the live example. `mypy --strict` catches the reverse error - a name used in
an annotation that no submodule imports.

## Placements that look wrong - each is deliberate

### `base.py` holds two things that are not geometry

The import-time main-tree guard and the drawing palette. Neither belongs in a geometry package on
subject grounds; both are what everything else needs FIRST (`core.py` imports `LAND` from here), and
the guard must run on ANY import of the package - which it does, because every submodule's star
import in `__init__.py` reaches this one, so there is no import path that bypasses it.

### `walls.py` holds torii predicates, and `shrines_wells/torii.py` exists

At THIS level an arch has exactly one geometric rule - it may not stand in a wall - and both
predicates are computed from `wall_runs()`. Filing them with the arches would put them in a module
that cannot see the walls they are about. The arch GLYPH, the avenue count, the stride, the threshold
and the wall-dodging are all `settlement/shrines_wells/torii.py` and were not touched.

### `village.py` does not belong in this package at all

A village population roll and a homestead-bundle pitch are `rolling.py`'s business - `rolling.py` is
their only consumer. They are here because feature 025's positional cut put them here, and they are
isolated in a module of their own so the eventual move is a one-file change rather than a diff
threaded through a 1,300-line file. Same device as feature 116's `seats.py`/`byres.py` and 113's
`city/civic.py`. **Moving them is a separate change with its own oracle** - do not fold it into
something else.

### `seatmemo.py` is one class in one file

Not a size decision. `SeatMemo` is its own subject (it remembers ANSWERS, not geometry) with a long
measured rationale attached, and a session working on the indexes next door almost never touches it.

## If a module grows: the seams, decided in advance

- **`indexes.py`** (247 lines, the largest): the `boxed_*` prefilters and the two index CLASSES are
  independent - the prefilters take a list, the classes own a structure. Cut there (`prefilter.py`)
  if either half grows.
- **`walls.py`** (197): the wall/ward half and the torii half already touch only through
  `wall_runs()`. Cut there if the torii rule gains more than clearance.
- **`overlap.py`** (184): the corner CONSTRUCTORS (`rot_rect`, `_rect_ring`, `stroke_quads`) are the
  reusable half, the predicates the rest. No reason to cut today.

## Monkeypatching a module-level name

Submodules bind helper names at import (`from .primitives import seg_dist`), so patching
`settlement._geom.seg_dist` does not reach a submodule that already imported it - patch the DEFINING
submodule (`settlement._geom.primitives.seg_dist`) or, for anything reached via `self.`, patch
`settlement.Settlement`. After feature 117 "the defining submodule" is `settlement._geom.<module>`,
not `settlement._geom`. No test in the suite does this today.
