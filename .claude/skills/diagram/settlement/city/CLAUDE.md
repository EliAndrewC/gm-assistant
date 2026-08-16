# settlement/city/ - the provincial-city subsystem as a package

Split from the 1,582-line `settlement/city.py` by feature 113 (constitution Principle X clause 13 -
the cost being managed is context-window tokens). **Load only the file the task calls for**; this
index is the map. `settlement/core.py` is byte-unchanged: `from .city import CityMixin` now
resolves to this package's `__init__.py`, which composes the six sub-mixins back into one
`CityMixin` occupying the same position in the `class Settlement(...)` base list.

## Look here when

| file | look here when |
|---|---|
| `__init__.py` | you need the composition or the re-export mechanism; never add logic here |
| `walls.py` | the defensive shell: `ring_road` (順城街, the follow-the-wall patrol street), `city_wall` and its private vocabulary - `_gapped_ring`, `_tower`, `_wall_walk`, `_wall_perimeter`, `_wall_point_at_arc`, `_wall_arc_of` |
| `moat.py` | the wet defense and every opening through it: `moat`, `water_gate`, `sluice_gate`, `inwall_drain_outfall`, `moat_flow` |
| `canals.py` | water carried for transport and irrigation rather than defense, and the farmland ring it feeds: `canal`, `towpath`, `farmland_ring`, `_ring_upslope` |
| `waterfront.py` | where the city meets navigable water: `quay`, `aqueduct`, `dock`, `jetty`, `log_boom` |
| `bridges.py` | crossings, from a single span to the footbridge net over a channel system: `bridge`, `bridges`, `channel_footbridges`, `_plank_reaches_useful_ground` |
| `civic.py` | the governor's mansion - and see below before you "fix" it |

## The composition mechanism

`CityMixin` has no members of its own. Sub-mixin methods reach each other through `self.` on the
composed `Settlement`, so a cross-submodule call needs no import and the partition can be re-cut
later without touching a call site. There is exactly ONE such call today:

    farmland_ring (canals.py) -> sluice_gate (moat.py)

When decomposing `farmland_ring`, leave that reaching through `self.` - do not "helpfully" add an
import from `moat.py`, which would turn a free re-partition into a breaking one.

The base order in `__init__.py` is source order and is behaviorally irrelevant, because no name is
defined twice. That property is not an accident - it is what
`tests/settlement/test_city.py::test_no_two_city_submixins_define_the_same_name` exists to keep
true, and it has been observed failing (feature 113 tasks.md T016).

## Two placement decisions, so nobody corrects them back

- **`_ring_upslope` lives in `canals.py`, not with `ring_road` in `walls.py`.** The name says ring
  road; the code says otherwise - its only caller is `farmland_ring`. Placement follows the caller.
- **`civic.py` holds one method, on purpose.** `governor_mansion` calls `self.manor(...)` and
  re-keys the record out of `M["manors"]`: it is a STRUCTURE reusing the manor glyph, not city
  infrastructure, so it belongs to none of the five subsystems above. A one-method module is a
  smell, but a module whose index row is a lie is a defect - isolating it keeps every other row
  honest. **Intended follow-up**: fold `civic.py` into `settlement/castle_civic.py`, where it
  topically belongs (903 + 21 = 924 lines, still under the bar). Scoped out of 113 because it
  would have widened the guard contract across two mixins during a pure move.

## Mixins and mypy

Every mixin method is annotated `self: "Settlement"` with `from ..core import Settlement` under
`TYPE_CHECKING` - the TWO-dot path, since these modules sit one level deeper than `city.py` did.
That is what lets `mypy --strict` resolve cross-subsystem attribute access with zero runtime import
cycle. Three of `walls.py`'s members are `@staticmethod` and take no `self`.

**One in-body import to know about**: `_wall_point_at_arc` does a lazy
`from ..core import Settlement` INSIDE its body (a runtime class-attribute read that would cycle at
module level). Feature 113's transformer originally rewrote only the module header, so this line
kept its one-dot path and silently pointed at a nonexistent `settlement.city.core`. `mypy` caught
it; in a module mypy did not check it would have been an `ImportError` at draw time. The
transformer now rewrites bodies too - any future split of a file with in-body relative imports
inherits the fix.

## The oracle for any change in here

Byte-identity of the regenerated pool, not the test suite. The city wing is exercised by the
provincial-city maps (`tango`, `minami`, `nagahara`) and the walled towns - a sweep of the live
scripted hamlets alone leaves `city_wall`, `moat`, `farmland_ring` and the whole waterfront module
unverified. `specs/113-city-package/quickstart.md` has the runnable harness.
