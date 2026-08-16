# Phase 0 Research: settlement/fields.py -> settlement/fields/

All four questions the plan invocation raised are resolved here. Nothing is left NEEDS
CLARIFICATION.

## R1. The partition is derived from the intra-class call graph, not chosen by theme

**Decision**: four sub-mixins - `paddy.py`, `comb.py`, `landuse.py`, `features.py`.

**Rationale**: `FieldsMixin`'s 24 methods were analyzed for `self.<method>` edges among themselves.
The graph is almost perfectly clustered - four groups, each with one or two externally-called entry
points and a tail of private helpers reached only from inside the group:

| group | entry points | private helpers reached only from within the group |
|---|---|---|
| paddy | `paddy_field`, `water_field`, `fallow_field` | `_paddy_plots`, `_split_convex`, `_taxfree_plots`, `_rows`, `_fallow_patch`, `_paddy_surface` |
| comb | `draw_comb_field`, `comb_base_fill`, `bund_junctions` | `_draw_furrows` |
| land use | `apply_land_use` | `_mulberry_rows`, `_pick_overlay_plots` |
| features | `pond`, `crescent_pond` | `_paddy_features`, `_plot_center_span`, `_plot_pond`, `_plot_rock`, `_plot_grave_island`, `_rounded_pond` |

Only **two** helper edges cross a group boundary, and both are recorded below with the home chosen
and why. Deriving the seams from the call graph rather than from the method names is the same
discipline as "derive, don't pin": a thematic guess would have put the three pond drawers in three
different places, and the graph shows they belong together.

**Alternatives considered**:

- **Split by the file's three banner comments** (`# ---- fields` at 35, `# ---- water` at 489,
  `# ---- feature 012 ...` at 946). Rejected: the banners divide the file into 454 / 457 / 558
  lines, which is a legal split, but the third region mixes the feature-012 plot features with the
  whole 266-line land-use overlay subsystem, which has nothing to do with them. The banners mark
  when code was written, not what it is.
- **Two modules only** (`fields.py` + `overlays.py`, roughly 950 / 550). Rejected: it clears the
  clause-13 bar on a technicality while leaving the largest module at 950 lines, i.e. it buys almost
  none of the token saving the feature exists for.
- **A shared `_helpers.py`** for the cross-group helpers. Rejected on R2's finding: cross-group
  calls need no import, so a helpers module would add a file and an import edge to solve a problem
  that does not exist.

## R2. Cross-group helper calls cost nothing, so each helper lands with its primary user

**Decision**: no shared-helper module. Each helper's TEXT lives in exactly one submodule, chosen by
primary caller; cross-group calls stay `self.<helper>(...)` and are resolved by the composed class.

**Rationale**: every sub-mixin is a base of the same `Settlement`, so `self._paddy_surface(...)`
resolves through the MRO wherever the caller's text happens to live. This is not a workaround - it
is how the parent `settlement/` package already works, and the engine already relies on it across
module boundaries: `settlement/land.py` calls `self._draw_furrows(...)`, which is defined in
`fields.py` today and will be defined in `fields/comb.py` afterward, with no import either way.

The two cross-group edges and their resolved homes:

| helper | callers | home | why |
|---|---|---|---|
| `_paddy_surface` | `paddy_field`, `water_field` (paddy), `apply_land_use` (land use) | `paddy.py` | two of three callers are paddy, and it renders the paddy SURFACE - the land-use overlay is a consumer of paddy rendering, not a co-owner of it |
| `_rounded_pond` | `apply_land_use` (land use) only | `features.py` | its only caller is in land use, but it is a pond GLYPH and its three siblings (`pond`, `crescent_pond`, `_plot_pond`) all live in `features.py`. A reader looking for how a pond is drawn must find all four in one place; splitting one off by caller would hide it |

`_rounded_pond` is the deliberate exception to "home = primary caller", and it is recorded here so
the next reader does not "fix" it back.

## R3. `pond` is a public entry point, not the comb builder's private helper

**Decision**: `pond`, `crescent_pond` and `_rounded_pond` go in `features.py`, not in `comb.py`.

**Rationale**: the intra-class graph shows `pond` called only by `draw_comb_field`, which would put
it in `comb.py` on the primary-caller rule. The external census contradicts that: `pond` is called
from **13 sites outside the class**, including `hamletgen/sink.py` and ten pool gens. It is a public
water glyph that the comb builder happens to also use. Burying it in the comb-field module would
mean a session looking for "how is a pond drawn" opens the comb-field builder - exactly the
navigation failure the `CLAUDE.md` index exists to prevent.

**The general lesson, worth carrying**: the intra-class call graph is the right tool for placing
PRIVATE helpers and the wrong tool for placing PUBLIC entry points. Census the external callers
before trusting a group boundary derived from internal edges alone.

## R4. The byte-identity oracle must include the frozen legacy gens, run in scratch

**Decision**: capture the baseline from a scratch copy of the pre-split tree, sweeping **every** pool
generator - live scripted maps and frozen legacy maps alike - plus `wip/shiro-daika.gen.py`. Compare
after each stage. Nothing frozen is regenerated in place and nothing frozen is committed.

**Rationale**: the live scripted pool is four `valley_paddy` hamlets, and the census shows what they
reach. `draw_comb_field` IS exercised live (`hamletgen/water.py` calls it), so the comb wing has a
live oracle. `apply_land_use` is a different story: its callers are `settlement/rolling.py`, the
frozen `pool/hamlets/kuwabata.gen.py`, and one `check_village` segment. Whether the live hamlet path
reaches it depends on `roll_village`, which the scripted hamlets do not use. So decomposing a
266-line method with no manifest-level oracle at all is the risk this decision removes: Kuwabata,
Tango, Minami and Nagahara are the only artifacts that prove the overlay code still draws what it
drew.

Running a frozen gen as a differential oracle does not violate the freeze. The freeze (skill
`CLAUDE.md`, "The legacy pool is FROZEN") forbids maintaining frozen maps against new rules,
re-gating them, and committing regenerated bytes. It does not forbid reading them. The scratch-tree
method is the one features 110 and 111 used, and for the same reason: the committed manifests are
not a valid baseline on their own, because the engine may have drifted since they were committed -
only a pre-change run of the same tree is.

**Alternatives considered**:

- **Committed manifests as the baseline.** Rejected: proven unreliable by feature 110's research
  R3. A mismatch would be indistinguishable from a refactor bug.
- **Live scripted hamlets only.** Rejected: leaves `apply_land_use` unverified, which is 266 of the
  773 lines Stage 2 touches.
- **Unit tests as the sole Stage 2 oracle.** Rejected as insufficient alone: `test_fields.py` is
  475 lines against a 1,511-line subsystem inside a package sitting at a 94% coverage floor, so
  line coverage does not imply the drawn geometry is unchanged. Used as a supplement, not a
  substitute.

## R5. Stage sequencing: pure move first, decomposition second, verified between

**Decision**: Stage 1 (move, zero logic edits) lands and is verified before any of Stage 2's three
decompositions begin; each decomposition is verified on its own.

**Rationale**: the two stages have different failure modes and mixing them destroys the diagnostic.
A pure move that breaks byte-identity means the composition or an import binding is wrong; a
decomposition that breaks it means a draw was reordered. Verified separately, a red sweep names its
own cause. Verified together, it does not. This is the same reason feature 111 sequenced its P1
harness ahead of its P2 decomposition.

Within Stage 2 the three methods are done one at a time, sweeping after each, for the same reason -
and because RNG draw order is the specific hazard: the engine's randomness is positional or scoped,
so an extraction that moves a `random` call relative to another changes every downstream coordinate.
The sweep catches it; doing three at once means bisecting to find which.

## R6. Composition mechanism and its guard

**Decision**: `fields/__init__.py` does four `from .x import XMixin` and one
`class FieldsMixin(PaddyMixin, CombMixin, LandUseMixin, FieldFeaturesMixin): pass`, with a docstring
saying the class exists only to preserve `core.py`'s single import. The guard test asserts the
composed class exposes exactly the 24 method names the pre-split class exposed, and that no two
sub-mixins define the same name.

**Rationale**: composing in the package `__init__` keeps `core.py` byte-unchanged, which is FR-002
and is worth more than the alternative's tidiness. The name-collision half of the guard matters
because MRO resolves a duplicate silently: two sub-mixins defining `_rows` would produce a working
import, a passing type check, and one dead implementation.

**Alternatives considered**:

- **Add the four sub-mixins directly to `core.py`'s base list.** Rejected: it edits `core.py`
  (violating FR-002 and SC-002), and it leaks the internal partition into the class declaration, so
  a future re-partition would touch `core.py` again.
- **`FieldsMixin = type("FieldsMixin", (...), {})`.** Rejected: identical semantics, worse
  readability, and `mypy --strict` cannot follow it.

## R7. The transformer: adapt 025's, do not re-derive it

**Decision**: reuse `specs/025-human-scale-splits/split_settlement.py` as the mechanical exemplar,
adapted for a class-to-subpackage split rather than a module-to-package one.

**Rationale**: 025 solved the same problem one level up - it carved `settlement.py` into mixin
modules and its manifest rows are exactly `(module, mixin_name, last_method)` triples, one of which
is `("fields", "FieldsMixin", "crescent_pond")`. The per-method extraction, the import header
generation and the `TYPE_CHECKING` + `self: "Settlement"` annotation pattern all carry over. What
differs is that the source is a class body rather than a module body, so slices are taken between
method boundaries rather than between top-level statements.

**The import-header rule**: each new submodule imports only the names its own methods use. Do not
copy the parent header wholesale - `ruff` will flag the unused ones, and an over-broad header
re-creates the module-level binding hazard that `settlement/CLAUDE.md` warns about (a name bound in
a module nobody patches is harmless; a name bound in four modules when a test patches one is a bug
waiting).

## R8. Consumer census result

**Decision**: no consumer file changes. Verified, not assumed.

**Rationale**: the census run before planning found:

- `FieldsMixin` the name: **one** consumer, `settlement/core.py` (one import, one base-list mention).
- `settlement.fields` module-level names reached from outside: **none**. No test, tool or gen
  imports from the module or patches a name in it.
- Private methods reached from outside the class: `_taxfree_plots`, `_paddy_features`,
  `_mulberry_rows`, `_pick_overlay_plots` (all from `test_settlement/test_fields.py`, all via
  `s.<name>` on a `Settlement` instance) and `_draw_furrows` (from `settlement/land.py`, via
  `self.`). Every one resolves through the composed class regardless of which submodule holds it, so
  none constrains the partition.
- Public methods reached from outside: 8 to 21 call sites each across pool gens, `hamletgen/`,
  `settlement/land.py`, `settlement/rolling.py`, two `check_village` segments and the tests. All are
  attribute access on a `Settlement` instance; none is an import.

**The one loose end, checked and CLOSED**: `settlement/__init__.py` re-exports the parent
package's public surface, so if it re-exported anything from `.fields` the new package `__init__`
would have to reproduce it. It does not - its re-export block draws only from `._geom` and
`._knobs`, and `fields.py` has no module-level name other than the class itself. Nothing to
preserve; the package `__init__` owes the parent nothing beyond the name `FieldsMixin`.
