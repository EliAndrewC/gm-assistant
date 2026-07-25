# Phase 1 Contract: Engine API and Check Names

**Feature**: 015-punishment-execution-grounds | **Date**: 2026-07-25

The `/diagram` skill's public interface is the `Settlement` method surface a `*.gen.py` spec calls, plus the check names the validator emits. Both are contracts: a gen spec depends on the signatures, and the regression corpus depends on the check names being stable.

## Generator methods (`settlement.py`)

```python
def punishment_spot(
    self, x: float, y: float, rot: float = 0.0, label: str | None = "punishment ground"
) -> None:
    """The town's public-shaming installation: a cangue frame, a flogging post, a kneeling
    stone. Sited on traffic (market or magistracy frontage), NOT at the seat of authority
    for its own sake. Draws NO notice board - the crime text rides on the cangue, and the
    settlement kosatsuba is a separate institution. ~30x12 ft, true size at every tier.
    Records M['punishment_spots']; reserves ground (placed + block_polys).
    Call BEFORE the urban packs. WHY: settlements.md 'Punishment spot'."""

def execution_ground(
    self,
    cx: float,
    cy: float,
    rot: float = 0.0,
    screened: bool | None = None,
    label: str | None = "execution ground",
) -> None:
    """The execution ground (keijou) - bare waste ground on the road past the boundary
    stone, outside the wall or the built edge. Crucifixion post SOCKETS (posts raised only
    when needed), a burning stake, a sand beheading bed, a head-display stand facing the
    road, a well, a disposal pit. Sized by tier: ~60x60 ft county, ~100x60 ft city,
    ~150-250x50-80 ft capital. `screened` defaults to True above town tier. At county tier
    it must read DISUSED - the county sees one execution every 5-10 years.
    Records M['execution_grounds']; reserves ground. Call beside the funerary cluster.
    WHY: settlements.md 'Execution ground'."""

def boundary_marker(
    self, x: float, y: float, rot: float = 0.0, label: str | None = "boundary stone"
) -> None:
    """A dosojin / sae-no-kami stone at the settlement's ritual boundary, where the road
    leaves clean ground. A LOCATION MARKER: true ~3 ft footprint recorded in w/h, drawn
    box in vw/vh, same doctrine as the wells and the kosatsuba.
    Records M['boundary_markers']. WHY: settlements.md 'Boundary marker'."""
```

## Manifest opt-outs (`meta`)

- `meta(punishment_spot=False)` - suppress the presence floor for a backwater seat
- `meta(execution_ground=False)` - likewise

## Check names (`check_village.py`)

Stable identifiers. Each gets a `test_checks.py` unit test **and** a negative fixture at `pool/regressions/<name>_fires_on_<case>.json`.

| Check | Fires when |
| --- | --- |
| `{scale}_has_punishment_spot` | a town/city declares no punishment spot and has not opted out |
| `punishment_spot_in_the_core` | the spot sits outside the wall, or outside the built area on an unwalled map |
| `punishment_spot_by_the_traffic` | the spot stands more than ~60 real ft from every street/road |
| `punishment_spot_only_at_a_seat_of_justice` | a hamlet or village declares one |
| `{scale}_has_execution_ground` | a town/city declares no execution ground and has not opted out |
| `execution_ground_outside_the_settlement` | the ground lies inside the wall, or within 120 real ft of a dwelling on an unwalled map |
| `execution_ground_by_the_road` | the ground stands more than ~120 real ft from every road/main street |
| `execution_ground_past_the_boundary_marker` | no boundary marker lies between the settlement centroid and the ground |
| `execution_ground_clear_of_the_dead` | the ground is within 150 real ft of a cemetery, cremation ground, ossuary, or mausoleum |
| `execution_ground_off_the_farmland` | the ground overlaps a field, paddy, or dry plot |
| `execution_ground_beyond_the_burakumin_quarter` | the ground is nearer the centroid than the quarter, or more than 90 degrees off its bearing (skipped when no burakumin dwellings exist) |
| `execution_ground_only_at_a_seat_of_justice` | a hamlet or village declares one |

## Struct-overlap registration

`punishment_spots`, `execution_grounds`, and `boundary_markers` are appended to the kind list `check_village.py` iterates for structure-vs-structure overlap, so they inherit the existing clearance rules (wells, troughs, hitching rails, torii, walls, and each other) with no new code. The boundary marker contributes its **drawn** box (`vw`/`vh`) there, per `_struct_rect`.

## Backward compatibility

Every new presence check is tier-gated and opt-outable, and the three registries default to empty lists. A hamlet or village map that declares nothing is unaffected - required by SC-005, which demands byte-identical hamlet and village renders after the change.
