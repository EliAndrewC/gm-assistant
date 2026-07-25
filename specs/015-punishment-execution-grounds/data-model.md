# Phase 1 Data Model: Punishment Spots and Execution Grounds

**Feature**: 015-punishment-execution-grounds | **Date**: 2026-07-25

The "data model" for a Mode B feature is the set of records the generator writes into the JSON manifest, because the manifest is what every check reads and what any later analysis reads (the dev-loop rule: read derived geometry from the manifest, never by re-running the generator). Three new registries, initialized empty in `Settlement.__init__` alongside `cremation_grounds` / `ossuaries` / `kosatsuba`.

## `M["punishment_spots"]` - list

The in-town display installation.

| Field | Type | Meaning |
| --- | --- | --- |
| `x`, `y` | float | center, map coordinates |
| `w`, `h` | float | true footprint in px at the map's grain (~30 x 12 ft) |
| `rot` | float | degrees; the frontage faces the street it lines |
| `label` | str or null | `"punishment ground"` by default |

Drawn at true size at every tier, so no `vw`/`vh`.

## `M["execution_grounds"]` - list

The out-of-town ground. A list, not a singleton: a capital or great city legitimately has one per major road gate.

| Field | Type | Meaning |
| --- | --- | --- |
| `x`, `y` | float | center |
| `w`, `h` | float | true footprint in px, from the tier size band |
| `rot` | float | degrees; the long axis runs with the road |
| `screened` | bool | three-sided screen fence (city and capital) vs. bare (county) |
| `label` | str or null | `"execution ground"` by default |

## `M["boundary_markers"]` - list

The dosojin stone. A **location marker** in the established sense: a real stone is ~3 ft, sub-glyph at every tier.

| Field | Type | Meaning |
| --- | --- | --- |
| `x`, `y` | float | center |
| `w`, `h` | float | TRUE footprint (~3 ft), so a size audit reads real feet |
| `vw`, `vh` | float | DRAWN box at the legibility floor - what the overlap checks clear |
| `rot` | float | degrees |
| `label` | str or null | `"boundary stone"`, or null for an unlabeled companion stone |

## Relationships and the rules that fall out of them

```text
settlement core ──contains──> punishment_spot        (inside wall / built area, fronting traffic)
        │
        └──main road──> boundary_marker ──beyond──> execution_ground
                                                          │
                                            ┌─────────────┴─────────────┐
                                     ≥150 ft from                 no overlap with
                                  cemeteries, cremation           fields, dry plots,
                                  grounds, ossuaries,             buildings, streets,
                                  mausoleums                      walls, other structs
```

- **`execution_ground` -> funerary features**: a *separation* relationship with a 150 ft floor. Compressed from a much larger historical separation for map legibility; disclosed in research.md and beside the check.
- **`execution_ground` -> `boundary_marker`**: an *ordering* relationship. The marker's projection onto the line from the settlement centroid to the ground must fall between them.
- **`execution_ground` -> burakumin quarter**: a *directional preference* (SHOULD, not MUST). Same side within a 90-degree tolerance, and further from the centroid. Skipped when the map has no burakumin dwellings.
- **All three -> the struct-overlap machinery**: the new kinds join the list `check_village.py` iterates for structure-vs-structure overlap, so they inherit the existing clearance rules against wells, troughs, rails, torii, walls, and each other without new code. The boundary marker contributes its `vw`/`vh` box there, per `_struct_rect`.

## Tier applicability

| Tier | punishment_spot | execution_ground | boundary_marker |
| --- | --- | --- | --- |
| hamlet | forbidden | forbidden | allowed (a plain road shrine) |
| village | forbidden | forbidden | allowed |
| town / walled town | **required** (opt-out) | **required** (opt-out) | required when a ground exists |
| provincial city | **required** (opt-out) | **required** (opt-out) | required when a ground exists |
| capital | required when the tier exists | required when the tier exists | required when a ground exists |

"Forbidden" is enforced by check, not by a silent no-op, so a spec that declares one at the wrong tier fails loudly.
