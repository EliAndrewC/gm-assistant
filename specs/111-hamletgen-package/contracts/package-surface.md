# Contract: the `hamletgen` package import surface

**Feature**: 111-hamletgen-package | **Date**: 2026-08-16

Every name any consumer reaches from `hamletgen` today. The package MUST reproduce all of them from
the package root, resolving to the same objects. Guard: `test_hamletgen_surface.py`.

Censused at clone HEAD `665db35` by grepping the skill tree for `from hamletgen import`,
`import hamletgen`, and `hg\.<attr>`.

## Direct imports

| consumer | statement |
|---|---|
| `pool/hamlets/inashiro.gen.py` | `from hamletgen import HamletSpec, generate` |
| `pool/hamlets/mizuguchi.gen.py` | `from hamletgen import HamletSpec, generate` |
| `pool/hamlets/kashikawa.gen.py` | `from hamletgen import HamletSpec, generate` |
| `pool/hamlets/sawada.gen.py` | `from hamletgen import HamletSpec, generate` |

## Attribute access (`import hamletgen as hg`)

Consumers: `test_hamletgen.py`, `cohort_audit.py`.

### Classes and dataclasses (3)

`HamletSpec`, `SitePlan`, `Report`

### Constants (6)

`ROLLED_ARCHETYPES`, `OFFTAKE_LADDER`, `WIND_VECTORS`, `FIELD_ARCHETYPES`, `SQ_FT_PER_ACRE`,
`GROSS_ACRES_PER_HOUSEHOLD`

Object identity matters: consumers read these, so re-export must bind the same objects, never
copies.

### Public functions (36)

`plan_site`, `canvas_for`, `offtakes_for`, `windward_for`, `net_acres`, `poly_area`, `centroid`,
`unit`, `pull_clear`, `crosses_disc`, `crosses_poly`, `point_in_poly`, `head_sluice`,
`net_bends_acutely`, `stage_water_frame`, `drain_outfall`, `drain_heading`, `edge_run`, `pond_clear_of_crop`,
`pond_setback`, `below_drain`, `back_fouled`, `seat_cluster`, `push_out_of`, `route_around`,
`clip_to_clear`, `clear_runs` (feature 123 - every clear run of a through-lane, as opposed to
`clip_to_clear`'s leading one), `connector_track`, `path_violations`, `crossing_lands_on_crop`,
`shallow_crossing`, `well_target`, `place_wells`, `stage_notice`, `build`, `main`, `cohort`

### Underscore functions (4)

`_arm_crossing_accidental`, `_clear_gap`, `_fork_spur`, `_near_line`

A bare `from .module import *` DROPS these. They require an explicit aliased block in
`__init__.py`:

```python
from .cluster import _arm_crossing_accidental as _arm_crossing_accidental
from .cluster import _fork_spur as _fork_spur
from .hinterland import _clear_gap as _clear_gap
from .hinterland import _near_line as _near_line
```

### Pass-through name

`point_in_poly` is defined in `settlement`, not in `hamletgen`. The monolith imports it and
consumers reach it through the module. It lands in `geom.py` (whose predicates call it) and is
carried to the package root by that module's star import - it is a public name, so no aliased entry
is needed. **This is the one name in the contract that is not defined anywhere in the package**, and
the guard test asserts `hamletgen.point_in_poly is settlement.point_in_poly`.

## Invariants the guard test enforces

1. **Resolution**: every name above resolves as an attribute of `hamletgen`.
2. **Identity**: for each name defined in a submodule, `getattr(hamletgen, name) is
   getattr(hamletgen.<submodule>, name)` - the re-export is a binding, not a copy.
3. **Mechanical re-census**: the test re-greps the skill tree for `hg.<attr>` and `from hamletgen
   import` and asserts every name it finds is in the pinned list, so a consumer added later cannot
   silently widen the surface without updating this contract.
4. **Proven to fire**: before the guard is trusted, one star import is commented out and the test
   must FAIL naming the missing surface (FR-003, SC-006).

## Not part of the contract

- Submodule paths (`hamletgen.ways.stage_ways`). Consumers use the package root only; submodule
  layout is free to change in a later feature.
- `STAGES` - not reached by any consumer today, but it stays public in `driver.py` and is carried
  by the star import.
