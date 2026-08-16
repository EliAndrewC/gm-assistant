# settlement/fields/ - the field subsystem as a package

Split from the 1,511-line `settlement/fields.py` by feature 112 (constitution Principle X clause 13
- the cost being managed is context-window tokens). **Load only the file the task calls for**; this
index is the map. `from .fields import FieldsMixin` still resolves and `settlement/core.py` is
byte-unchanged, so nothing above this directory knows the split happened.

## Look here when

| file | look here when |
|---|---|
| `__init__.py` | you need the composition itself; never add logic here |
| `paddy.py` | wet and dry field BODIES and the plot geometry they quilt themselves from: `paddy_field`, `water_field`, `fallow_field`, plot splitting (`_paddy_plots`, `_split_convex`), tax-free plots, the paddy surface render, crop rows, the fallow patch |
| `comb.py` | the comb-field builder and only it: `draw_comb_field`, `comb_base_fill`, `bund_junctions`, `_draw_furrows` |
| `landuse.py` | the land-use overlay pass - mulberry-and-fishpond, lotus, hill tea: `apply_land_use`, `_mulberry_rows`, `_pick_overlay_plots` |
| `features.py` | anything that is NOT rice: the feature-012 in-field pond / rock outcrop / grave island with their archetype-matrix constants, and every standing-water glyph (`pond`, `crescent_pond`, `_rounded_pond`) |

## Composition, and why it is in `__init__.py`

`FieldsMixin` is `class FieldsMixin(PaddyMixin, CombMixin, LandUseMixin, FieldFeaturesMixin)` with
no members of its own. It exists ONLY so `core.py` keeps its single import and `FieldsMixin` keeps
its position in the `class Settlement(...)` base list - which means the partition here can be
re-cut later without touching `core.py`.

**Cross-submodule calls need no import.** Every sub-mixin is a base of the same `Settlement`, so
`self._paddy_surface(...)` resolves through the MRO wherever the caller's text lives. The engine
already relies on this from outside the package too: `settlement/land.py` calls
`self._draw_furrows(...)`, which is defined in `comb.py`.

**Two members deliberately do NOT live with their primary caller.** Both are recorded so nobody
"fixes" them back:

- **`_paddy_surface` is in `paddy.py`** though `apply_land_use` (in `landuse.py`) is one of its
  three callers. It renders the paddy SURFACE; the overlay is a consumer of paddy rendering, not a
  co-owner of it.
- **`_rounded_pond` is in `features.py`** though its ONLY caller is `apply_land_use`. It is a pond
  glyph, and a reader looking for how a pond is drawn must find all four pond drawers in one place.

## The guard, and what it is for

`test_settlement/test_fields.py::test_composed_fields_mixin_exposes_exactly_the_pre_split_surface`
pins the 24-name surface, and `test_no_two_fields_submixins_define_the_same_name` pins that no two
sub-mixins define the same member. The second is the one that is easy to under-rate: a duplicated
member produces a working import, a clean `mypy --strict`, and one silently dead implementation,
because MRO just picks the first base. Both were proven to fire before being trusted (feature 112
T005). **Adding a method here means adding its name to `_FIELDS_SURFACE`** - that is deliberate, so
the surface grows on purpose rather than by accident.

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
