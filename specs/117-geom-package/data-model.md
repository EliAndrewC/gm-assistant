# Phase 1 Data Model: the partition

All 89 module-level members of `settlement/_geom.py`, each assigned to exactly one submodule, in
SOURCE order within the module (the order the transformer writes them). `L` is the member's first
line in the pre-split file - the transformer keys on names, and these are here so a reviewer can
follow the move.

## `base.py` - what every other submodule needs first (9 members, ~50 lines)

| L | member | note |
|---|---|---|
| 9 | `Pt` | `tuple[float, float]` |
| 10 | `Poly` | `list[Pt]` |
| 11 | `Manifest` | `dict[str, Any]` |
| 14 | `_assert_not_main_tree` | the import-time guard; its bare CALL statement (line 35) folds into this block - research R4 |
| 37 | `LAND` | palette; not geometry, isolated deliberately - research R1 |
| 38 | `PADDY_SHADES` | |
| 39 | `FLOODED_SHADES` | |
| 40 | `RIPE_SHADES` | |
| 41 | `RICE_GREENS` | |

## `primitives.py` - coordinate math, no map vocabulary (9 members, ~95 lines)

| L | member |
|---|---|
| 87 | `_signed_area` |
| 131 | `point_in_poly` |
| 214 | `seg_closest` |
| 223 | `seg_dist` |
| 228 | `seg_in_ellipse_core` |
| 246 | `ring_touches` |
| 445 | `segments_cross` |
| 713 | `seg_intersect` |
| 722 | `edge_dist` |

## `overlap.py` - corner rings, and whether two regions meet (13 members, ~175 lines)

| L | member | note |
|---|---|---|
| 340 | `stroke_quads` | a polyline as real polygons |
| 381 | `box_gap` | the AABB measure; its docstring's forward reference to the label ladder is re-pointed (R5) |
| 469 | `_rect_ring` | the 16-line torii doctrine bank physically above this member is LIFTED OUT to `walls.py` (R5) |
| 476 | `sat_overlap` | |
| 690 | `_union_area` | |
| 1152 | `region_blocked` | |
| 1169 | `quad_hits_poly` | |
| 1185 | `point_quad_dist` | |
| 1192 | `quad_hits_seg` | |
| 1206 | `rot_rect` | |
| 1213 | `poly_gap` | |
| 1228 | `_aabb_gap` | consumed by `structures/servants.py` - in the underscore alias block |
| 1239 | `rects_overlap` | |

## `indexes.py` - the prefilter family and the spatial indexes (8 members, ~245 lines)

| L | member | note |
|---|---|---|
| 726 | `boxed_polys` | |
| 737 | `boxed_hit` | carries the 24.6M-call profile that motivated the family |
| 755 | `boxed_segs` | |
| 766 | `boxed_seg_hit` | |
| 772 | `Indexed` | the mutation-versioned registry + its two staleness post-mortems |
| 855 | `indexed_grid` | annotates `PointGrid` before it is defined - legal under PEP 649, research R6 |
| 982 | `boxed_grid` | |
| 992 | `PointGrid` | including the `_MAX_SPAN` clamp and the 5.6-billion-cell incident |

The largest module, and the one that most deserves to be alone: its 245 lines are ~60% researched
post-mortem, which is exactly the payload a reader of any OTHER subject currently pays for.

## `seatmemo.py` - the refusal memo (1 member, ~105 lines)

| L | member |
|---|---|
| 882 | `SeatMemo` |

One class, its own file, because it is one subject with a 40-line measured rationale (the 511,519
candidate positions, the 64.6% re-visit share, the "measure the re-visit share per gen first"
warning) and because a session touching the indexes above almost never touches it.

## `labels.py` - caption typography (12 members, ~145 lines)

| L | member | note |
|---|---|---|
| 390 | `LABEL_MIN_AIR` | heads the 35-line standoff-ladder bank |
| 406 | `LABEL_AIR_STEP` | |
| 411 | `LABEL_AIR_RINGS` | |
| 413 | `LABEL_AIR_CAP` | |
| 415 | `HALL_CAPTION_FS` | heads the caption-size ruling |
| 433 | `GOVERNOR_CAPTION_FS` | |
| 490 | `label_tilt` | the FOLD |
| 503 | `linear_tilt_full` | |
| 515 | `linear_tilt` | the CLAMP - the docstring that says why the two must never be swapped |
| 537 | `label_quad` | |
| 553 | `label_aabb` | |
| 563 | `tilt_caption_seat` | |

## `ways.py` - the travelled ways, and the gate that bars one (11 members, ~125 lines)

| L | member | note |
|---|---|---|
| 43 | `PLANK_ABUTMENT` | heads the standalone-footplank geometry bank |
| 48 | `PLANK_BANK_REACH` | |
| 49 | `LANDING_FT` | |
| 50 | `PLANK_VILLAGE_REACH` | |
| 287 | `LANE_THROUGH_TOL` | heads the "a kido squares to the WAY" bank; its reference to `torii_wall_conflicts` is re-pointed (R5) |
| 293 | `LANE_CROSSES_MIN_DEG` | |
| 298 | `lane_runs` | |
| 317 | `way_beds` | |
| 355 | `lane_through_gate` | |
| 374 | `kido_bar_deg` | |
| 1069 | `CARRIED_LANDING_FLOOR_FT` | the carried-deck landing floor - a crossing constant, filed with the crossings |

## `walls.py` - walls, ward closure, and arches that must stand clear (9 members, ~170 lines)

| L | member | note |
|---|---|---|
| 60 | `TORII_PITCH_FT` | heads the avenue-pitch ruling |
| 72 | `TORII_PITCH_MAX_SPANS` | |
| 75 | `torii_halfbox` | the true-scale glyph box, mirrored by `check_village` |
| 144 | `WARD_BARRED_KINDS` | |
| 154 | `ward_interior` | the arc-length closure (largest member: 58 lines / 34 statements) |
| 623 | `wall_runs` | every wall on the map |
| 648 | `_box_hits_run` | |
| 666 | `torii_seat_on_wall` | **receives the moved doctrine bank** (R5) |
| 677 | `torii_wall_conflicts` | |

## `extents.py` - a recorded feature's DRAWN extent (8 members, ~120 lines)

| L | member | note |
|---|---|---|
| 97 | `forest_reveal_x` | |
| 112 | `forest_frame_span` | |
| 251 | `paddy_wet_rings` | the "prefer the drawn plots" ruling |
| 576 | `YARD_GLYPH_SLACK` | heads the stable-yard collision post-mortem |
| 594 | `wellhead_quad` | |
| 600 | `trough_quad` | |
| 606 | `tower_quad` | |
| 615 | `rail_quad` | |

The unifying subject is the doctrine, not the shape: every member here is a predicate that the
PLACER and its CHECK must read identically, which is why each is the single definition of one drawn
extent.

## `curves.py` - making a line or a ring look hand-made (6 members, ~125 lines)

| L | member | note |
|---|---|---|
| 1081 | `fillet_polyline` | the earthen-channel bend research |
| 1123 | `smooth_closed` | |
| 1134 | `smooth_points` | |
| 1253 | `organic_bbox` | |
| 1275 | `organic_poly` | |
| 1290 | `winding` | |

`tools/cache_audit.py`'s mutation TARGET after this feature - research R7.

## `village.py` - not geometry; isolated for a later move (3 members, ~25 lines)

| L | member |
|---|---|
| 1057 | `_VILLAGE_POP_DIST` |
| 1063 | `BUNDLE_PITCH_FT` |
| 1075 | `village_population` |

A population roll and a homestead pitch are `rolling.py`'s business. They are here only because
feature 025's positional cut put them here. Isolated rather than moved, so the eventual move is a
one-file change - feature 116's `seats.py`/`byres.py` precedent, and 113's `city/civic.py`.

## The import DAG

Each submodule copies the original's import header (`math`, `os`, `random`, `collections.abc`,
`typing`) and is then pruned by `ruff check --select F401 --fix`. On top of that the transformer
writes exactly these cross-module imports - hand-specified rather than inferred, so no cycle can be
introduced by a pruning surprise:

| module | supplemental imports |
|---|---|
| `base` | none |
| `primitives` | `from .base import Poly, Pt` |
| `overlap` | `from .base import Poly, Pt`; `from .primitives import point_in_poly, seg_dist, segments_cross` |
| `indexes` | `from .base import Poly, Pt`; `from .primitives import edge_dist, point_in_poly, seg_dist` |
| `seatmemo` | none |
| `labels` | `from .base import Poly, Pt` |
| `ways` | `from .base import Manifest, Poly`; `from .primitives import seg_dist` |
| `walls` | `from .base import Manifest, Poly, Pt`; `from .primitives import seg_dist, segments_cross`; `from .overlap import _rect_ring` |
| `extents` | `from .base import Manifest, Poly` |
| `curves` | `from .base import Poly, Pt` |
| `village` | none |

**Layering rule** (stated in the package index, FR-007): `base` <- `primitives` <- `overlap` <-
everything else. `seatmemo` and `village` import nothing from the package. No submodule imports from
a module to its right in that order, so the package is acyclic by construction and stays so as long
as an addition respects the rule.

## The package surface

`settlement/_geom/__init__.py`:

```python
from .base import *
from .base import _assert_not_main_tree as _assert_not_main_tree
from .curves import *
from .extents import *
from .indexes import *
from .labels import *
from .overlap import *
from .overlap import _aabb_gap as _aabb_gap
from .overlap import _rect_ring as _rect_ring
from .overlap import _union_area as _union_area
from .primitives import *
from .primitives import _signed_area as _signed_area
from .seatmemo import *
from .village import *
from .village import _VILLAGE_POP_DIST as _VILLAGE_POP_DIST
from .walls import *
from .walls import _box_hits_run as _box_hits_run
from .ways import *
```

Nothing else. No `__all__` (star-imported public names are re-exported explicitly enough for
`mypy --strict` - research R2), no logic, no re-derivation of anything a submodule declares.
