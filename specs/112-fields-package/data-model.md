# Phase 1 Data Model: the `settlement/fields/` package

"Entities" here are modules, sub-mixin classes and method assignments. Line figures are from the
pre-split file and exclude the per-module import header (~30 lines each).

## Modules and sub-mixins

| module | sub-mixin class | methods | body lines | projected file |
|---|---|---|---|---|
| `paddy.py` | `PaddyMixin` | 9 | 443 | ~475 |
| `comb.py` | `CombMixin` | 4 | 448 | ~480 |
| `landuse.py` | `LandUseMixin` | 3 | 364 | ~395 |
| `features.py` | `FieldFeaturesMixin` | 8 | 175 | ~205 |
| `__init__.py` | `FieldsMixin` (composition only) | 0 | - | ~25 |
| `CLAUDE.md` | - | - | - | ~45 |

Largest projected file ~480 lines, comfortably under the ~1,000 clause-13 bar, with room for Stage
2's extracted helper signatures.

## Method assignment

### `paddy.py` - `PaddyMixin`

Wet and dry field bodies and the plot geometry they quilt themselves from.

| method | lines | visibility | notes |
|---|---|---|---|
| `paddy_field` | 90 | public entry (8 external sites) | |
| `_split_convex` | 21 | private, called by `_paddy_plots` only | |
| `_paddy_plots` | 43 | private, called by `paddy_field` only | |
| `_taxfree_plots` | 11 | private; also reached by `test_fields.py` | |
| `_paddy_surface` | 38 | private; **cross-group** - also called by `apply_land_use` | R2: home here, 2 of 3 callers |
| `_rows` | 26 | private | |
| `_fallow_patch` | 13 | private, called by `paddy_field` only | |
| `water_field` | 194 | public entry | **Stage 2 decomposition target** |
| `fallow_field` | 7 | public entry | |

### `comb.py` - `CombMixin`

The comb-field builder and the pieces only it uses.

| method | lines | visibility | notes |
|---|---|---|---|
| `comb_base_fill` | 37 | public entry (12 external sites) | |
| `bund_junctions` | 78 | public entry (13 external sites) | |
| `draw_comb_field` | 313 | public entry (21 external sites) | **Stage 2 decomposition target** |
| `_draw_furrows` | 20 | private; **cross-group** - also called by `settlement/land.py` via `self.` | resolves through the composed class; no import |

### `landuse.py` - `LandUseMixin`

The land-use overlay pass and its row-drawing helpers.

| method | lines | visibility | notes |
|---|---|---|---|
| `apply_land_use` | 266 | public entry (13 external sites) | **Stage 2 decomposition target** |
| `_mulberry_rows` | 71 | private; also reached by `test_fields.py` | |
| `_pick_overlay_plots` | 27 | private; also reached by `test_fields.py` | |

### `features.py` - `FieldFeaturesMixin`

Non-rice features the paddy tiles around (feature 012) plus every standing-water glyph.

| method | lines | visibility | notes |
|---|---|---|---|
| `_paddy_features` | 26 | private; also reached by `test_fields.py` | the feature-012 dispatcher |
| `_plot_center_span` | 4 | private | shared by the three plot features |
| `_plot_pond` | 15 | private | |
| `_plot_rock` | 14 | private | |
| `_plot_grave_island` | 12 | private | |
| `pond` | 24 | public entry (13 external sites) | R3: public, so NOT buried in `comb.py` |
| `crescent_pond` | 47 | public entry | |
| `_rounded_pond` | 33 | private; only caller is `apply_land_use` | R2: deliberate exception - lives with its pond siblings, not its caller |

## Invariants the model must preserve

1. **The composed surface is exactly 24 method names** - the set the pre-split `FieldsMixin`
   exposed. No name added, none dropped, none renamed. Stage 2's extracted helpers are new PRIVATE
   names and are counted separately (see the contract).
2. **No name is defined by two sub-mixins.** MRO would silently pick one and orphan the other.
3. **`core.py` is byte-unchanged**: `from .fields import FieldsMixin`, and `FieldsMixin` stays first
   in the `class Settlement(...)` base list.
4. **Each module imports only what its own methods use** (R7), and annotates `self: "Settlement"`
   under `TYPE_CHECKING` with `from ..core import Settlement` - the two-dot path, since the package
   is now one level deeper than `fields.py` was.
5. **Method text moves verbatim in Stage 1** - including every inline comment carrying a researched
   "why". Reformatting, renaming and comment tidying are Stage 2 concerns at the earliest, and are
   not in scope even there beyond what extraction requires.
6. **Draw order and RNG draw order are untouched.** No method changes position relative to another
   in the sequence a generator calls them, because the split moves text between files and never
   changes a call site.
