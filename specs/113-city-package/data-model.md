# Phase 1 Data Model: the `settlement/city/` package

"Entities" here are modules, sub-mixin classes and method assignments. Line figures are measured
from the pre-split `settlement/city.py` (1,582 lines, 27 methods, all `FunctionDef` - no
class-level constants). "Block lines" is what the transformer actually moves: from the previous
member's end through this member's end, so decorators, blank lines and comment blocks above a
member travel with it.

This document is the transformer's input AND the thing a reviewer checks the transformer's output
against. If the two disagree, this document is wrong and gets corrected - it is not a wish.

## Modules and sub-mixins

| module | sub-mixin class | methods | block lines | projected file (pre-prune) |
|---|---|---|---|---|
| `walls.py` | `WallsMixin` | 8 | 494 | ~521 |
| `moat.py` | `MoatMixin` | 5 | 240 | ~267 |
| `canals.py` | `CanalsMixin` | 4 | 210 | ~237 |
| `waterfront.py` | `WaterfrontMixin` | 5 | 258 | ~285 |
| `bridges.py` | `BridgesMixin` | 4 | 331 | ~358 |
| `civic.py` | `CityCivicMixin` | 1 | 21 | ~48 |
| `__init__.py` | `CityMixin` (composition only) | 0 | - | ~25 |
| `CLAUDE.md` | - | - | - | ~50 |

Block lines total 1,554; plus the 27-line shared header that becomes the parent of all six modules,
that accounts for all 1,582 lines. The projected figures are BEFORE
`ruff check --select F401 --fix` prunes each module's copied import header, so every file lands
lower than shown. The largest, `walls.py`, is comfortably under the ~1,000 clause-13 bar with room
for Stage 2's extracted helper signatures.

**Composition order** in `class CityMixin(WallsMixin, MoatMixin, CanalsMixin, WaterfrontMixin,
BridgesMixin, CityCivicMixin)` follows source order. Because no name is defined twice (guard
assertion 2), the MRO is behaviorally irrelevant - the order is for readability only.

## Method assignment

### `walls.py` - `WallsMixin`

The city's defensive shell: the wall itself, its towers and walk, and the patrol road inside it.

| method | lines | visibility | notes |
|---|---|---|---|
| `_gapped_ring` | 37 | private; also reached by `settlement/` and `tests/` | called by `city_wall` |
| `ring_road` | 29 | public entry (5 sites) | 順城街, the follow-the-wall street; calls nothing |
| `_tower` | 23 | private, `city_wall` only | 0 external consumers |
| `_wall_walk` | 18 | private; also reached by `tests/` | called by `city_wall` |
| `_wall_perimeter` | 3 | private | called by `city_wall` |
| `_wall_point_at_arc` | 16 | private | called by `city_wall` |
| `_wall_arc_of` | 17 | private | called by `city_wall` |
| `city_wall` | 339 | public entry (7 sites) | **Stage 2 target, done LAST** |

The tightest cluster in the class: six of the eight exist only to serve `city_wall`. `ring_road`
rides along because it is the same subsystem conceptually (the wall-clear zone is what it occupies)
even though it shares no code.

### `moat.py` - `MoatMixin`

The wet defense and every opening through it.

| method | lines | visibility | notes |
|---|---|---|---|
| `moat` | 111 | public entry (9 sites, the most-consumed in the class) | **Stage 2 target** |
| `water_gate` | 19 | public entry (4 sites) | |
| `sluice_gate` | 37 | public entry (6 sites) | **cross-seam**: also called by `farmland_ring` |
| `inwall_drain_outfall` | 59 | public entry (4 sites) | calls `sluice_gate` |
| `moat_flow` | 9 | public entry (5 sites) | |

### `canals.py` - `CanalsMixin`

Water carried for transport and irrigation rather than defense, and the farmland ring it feeds.

| method | lines | visibility | notes |
|---|---|---|---|
| `canal` | 19 | public entry (3 sites) | |
| `towpath` | 21 | public entry (3 sites) | |
| `_ring_upslope` | 45 | private, `farmland_ring` only | **placement follows the CALLER, not the name** - it reads like a `ring_road` helper and is not one (research R1) |
| `farmland_ring` | 121 | public entry (4 sites) | **Stage 2 target**; calls `_ring_upslope` + `sluice_gate` |

### `waterfront.py` - `WaterfrontMixin`

Where the city meets navigable water. Five independent entry points - the loosest-coupled group in
the class, calling nothing and called by nothing inside it.

| method | lines | visibility | notes |
|---|---|---|---|
| `quay` | 69 | public entry (2 sites) | |
| `aqueduct` | 60 | public entry (3 sites) | |
| `dock` | 13 | public entry (3 sites) | |
| `jetty` | 14 | public entry (4 sites) | |
| `log_boom` | 97 | public entry (2 sites) | **Stage 2 target, done FIRST** - smallest, no callees |

### `bridges.py` - `BridgesMixin`

Crossings, from a single span to the footbridge net over a channel system.

| method | lines | visibility | notes |
|---|---|---|---|
| `bridge` | 32 | public entry (5 sites) | called by `bridges` and `channel_footbridges` |
| `bridges` | 72 | public entry (17 sites, most-consumed in the file) | calls `bridge` |
| `channel_footbridges` | 195 | public entry (14 sites) | **Stage 2 target** |
| `_plank_reaches_useful_ground` | 28 | private, `channel_footbridges` only | 0 external consumers |

### `civic.py` - `CityCivicMixin`

The one civic BUILDING the city tier draws.

| method | lines | visibility | notes |
|---|---|---|---|
| `governor_mansion` | 21 | public entry (5 sites) | see below |

**Why this module exists at all**, since a one-method module is otherwise a smell:
`governor_mansion` calls `self.manor(...)` and re-keys the result out of `M["manors"]`. It is a
structure reusing the manor glyph, not city infrastructure - topically a sibling of the contents of
`castle_civic.py`, not of walls and moats. Isolating it keeps every other module's index row
honest and makes the eventual relocation a one-file change. Full reasoning and the two rejected
alternatives are in research R1.

**Follow-up, deliberately NOT done here**: fold `civic.py` into `settlement/castle_civic.py`
(903 + 21 = 924, still under the bar). Out of scope for 113 because it would widen the guard
contract across two mixins and make US1 something other than a pure move.

## Invariants

1. **The partition exactly covers the class.** 8 + 5 + 4 + 5 + 4 + 1 = 27. The transformer refuses
   to run otherwise, printing `missing=` and `extra=`.
2. **No method is renamed, and no method's body is edited**, in Stage 1. The only text that changes
   is the module header and the class statement above it.
3. **Every method keeps its `self: "Settlement"` annotation**, and every module carries
   `if TYPE_CHECKING: from ..core import Settlement` - the two-dot path, since the modules sit one
   level deeper than `city.py` did. This is what lets `mypy --strict` resolve cross-subsystem
   attribute access with no runtime import cycle.
4. **`settlement/core.py` does not change.** `from .city import CityMixin` resolves to the
   package's `__init__.py` instead of the module, and the `class Settlement(...)` bases line is
   byte-identical.
5. **Cross-seam calls need no imports.** `farmland_ring` -> `sluice_gate` works because sub-mixin
   methods reach each other through `self.` on the composed `Settlement`.
