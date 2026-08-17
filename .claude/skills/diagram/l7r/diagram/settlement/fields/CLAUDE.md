# settlement/fields/ - the field subsystem as a package

Split from the 1,511-line `settlement/fields.py` by feature 112 (constitution Principle X clause 13
- the cost being managed is context-window tokens). **Load only the file the task calls for**; this
index is the map. `from .fields import FieldsMixin` still resolves and `settlement/core.py` is
byte-unchanged, so nothing above this directory knows the split happened.

## Look here when

| file | look here when |
|---|---|
| `__init__.py` | you need the composition itself; never add logic here |
| `paddy.py` | wet and dry field BODIES and the plot geometry they quilt themselves from: `paddy_field`, `water_field`, `fallow_field`, plot splitting (`_paddy_plots`, `_split_convex`), tax-free plots, the paddy surface render, crop rows, the fallow patch. Also the module-level WATER FRAME (`_uf_u` / `_uf_f` / `_uf_xy`) - the contour/fall transforms, pure and shared |
| `comb.py` | the comb-field builder and only it: `draw_comb_field` and its eight `_comb_*` steps (hem, paddies, beads, source, ditches, the field record, the ditch records, the hairline source channel), plus `comb_base_fill`, `bund_junctions`, `_draw_furrows` |
| `landuse.py` | the land-use overlay pass - mulberry-and-fishpond, lotus, hill tea: `apply_land_use` and its four `_landuse_*` steps (tea fringe, wholesale leftovers, one converted plot, the dike-pond sluices), plus `_mulberry_rows`, `_pick_overlay_plots` |
| `features.py` | anything that is NOT rice: the feature-012 in-field pond / rock outcrop / grave island with their archetype-matrix constants, and every standing-water glyph (`pond`, `crescent_pond`, `_rounded_pond`) |

## Composition, and why it is in `__init__.py`

`FieldsMixin` is `class FieldsMixin(PaddyMixin, CombMixin, LandUseMixin, FieldFeaturesMixin)` with
no members of its own. It exists ONLY so `core.py` keeps its single import and `FieldsMixin` keeps
its position in the `class Settlement(...)` base list - which means the partition here can be
re-cut later without touching `core.py`.

**Cross-submodule calls need no import.** Every sub-mixin is a base of the same `Settlement`, so
`self._paddy_surface(...)` resolves through the MRO wherever the caller's text lives. The engine
already relies on this from outside the package too: `settlement/land/nearring.py` calls
`self._draw_furrows(...)`, which is defined in `comb.py`.

**Two members deliberately do NOT live with their primary caller.** Both are recorded so nobody
"fixes" them back:

- **`_paddy_surface` is in `paddy.py`** though `apply_land_use` (in `landuse.py`) is one of its
  three callers. It renders the paddy SURFACE; the overlay is a consumer of paddy rendering, not a
  co-owner of it.
- **`_rounded_pond` is in `features.py`** though its ONLY caller is `apply_land_use`. It is a pond
  glyph, and a reader looking for how a pond is drawn must find all four pond drawers in one place.

## The guard, and what it is for

`test_settlement/test_fields.py::test_no_pre_split_fields_member_was_lost_in_the_move` holds the
24 pre-split members as a SUBSET of what the composed class exposes, and
`test_no_two_fields_submixins_define_the_same_name` holds that no two sub-mixins define the same
member. Both were proven to fire before being trusted (feature 112 T005).

Two things about the shape of that pair:

- **Subset, not equality** - so adding a method here needs no bookkeeping. Stage 2 added thirteen
  private helpers and will not be the last to add some. The direction that HIDES is a member going
  missing: an addition is visible in review, while a subtraction surfaces only when whichever
  generator calls it happens to run.
- **The collision half is the one that is easy to under-rate**: a member defined by two sub-mixins
  produces a working import, a clean `mypy --strict`, and one silently dead implementation, because
  MRO just picks the first base.

## The class body is not only methods

`features.py` carries three class-level tuples - `_PADDY_POND_KINDS`, `_PADDY_ROCK_KINDS`,
`_PADDY_GRAVE_KINDS` - the feature-012 archetype matrix saying which field kinds get which in-field
feature. The surface guard cannot see attributes, so
`test_feature_012_archetype_constants_survived_the_split` covers them separately. Any future
re-partition of this package must move class attributes as deliberately as methods; the feature 112
transformer refuses to run if its manifest does not name every class-body member.

## Monkeypatching

Each submodule binds shared helper names at import (`from .._geom import point_in_poly`), so
patching `settlement.fields.point_in_poly` reaches nothing. Patch the DEFINING module
(`settlement._geom.point_in_poly`) or, for anything reached through `self.`, patch
`settlement.Settlement` - class-level patching is unaffected by the split. As of feature 112 no test
in the suite patches a module-level name in this package (census: `specs/112-fields-package/`
research R8).

## Function scale

Feature 112's second stage decomposed the three methods that were 52% of the old file:
`draw_comb_field` 321 -> 47, `apply_land_use` 266 -> 123, `water_field` 194 -> 150. Nothing in the
package now exceeds ~150 lines.

`water_field` is the one that stopped at the bar rather than well under it, and its own body says
why at the point of the decision: what remains is coupled through `uline`, a closure over the
lateral boundaries that both the plot-carving loop and the lateral draw call. Cutting further would
mean threading a closure plus nine locals through a helper - worse to read than the sequence it
would replace. **The next move there is to give the water frame a small object, not to lengthen a
parameter list.** (It is also the v1 field builder, superseded by `waterfields/` for rebuilt maps,
so it is not where new work should go.)
