# Data Model: Capital Housing Layer (021)

The "data" of a /diagram feature is the manifest contract: what keys a capital map records,
what the budget binds, and which knobs a future capital gen may turn. Every NEW key enters
the keep-clear contract (`_OVERLAP_STRUCTS` or `_OVERLAP_EXEMPT` with reason, `_LABEL_GROUP`
or `_LABEL_EXEMPT`, and a footprint the matrix extractor can read) - that is the standing
checklist, restated here once instead of per-entity.

## Budget bindings (read-only inputs, from the recorded 018 budget)

| binding | source | value on Shiro Daika |
|---|---|---|
| dwelling targets by band | `budget.dwelling_target` (`samurai_yashiki`, `samurai_detached`, `samurai_terrace`, `packed`, `dwellings`) | recorded in the manifest's budget block |
| senior/junior mix | CAPITAL_RANK_BANDS via the same block | 70/30 senior-heavy (inverts provincial) |
| civic floors | CAPITAL_CIVIC_PROGRAM lines | already drawn in 019/020 |
| monk houses | `monk_houses_per_precinct` | 2.5/precinct, ~5 total |

Targets are reconciled to drawable ground BEFORE packing (edge case #1 in the spec); the
reconciliation note lands in the gen where the numbers are consumed.

## Manifest keys

### New keys

| key | record shape | overlap class | label group | notes |
|---|---|---|---|---|
| `terraces` | `{x, y, w, h, rot, units, z}` | SOLID struct | "terrace" | one record per nagaya range; `units` = household count; party-wall seams drawn, not recorded |
| `districts` | `{name, kind, poly, rank_band?}` | EXEMPT (region, not a structure) | exempt (regions carry no caption by default) | placement regions for packs + the gradient check's ground truth; kinds: `yashiki`, `detached`, `terrace`, `machi`, `monzen`, `entertainment` |
| `entertainment` fabric | reuses `businesses`/`theater_stages` + a `districts` record | existing classes | existing groups | no new glyph |

### Extended keys (existing records gain a field; absent field = legacy behavior, pool byte-identity preserved)

| key | extension | rule |
|---|---|---|
| `wells` | `kind: "cistern"` only when in the service band | cistern-wells only within ~600 street-ft of the settling basin (research item 4); field absent on every existing map |
| `meta` | `wind_from: <bearing>` | declared BEFORE nuisance trades; declaration-existence check |
| `religious` | `graveyard: true` claims | close-out: drawn ground or claim removed (020 debt) |
| `kido` | mouth-of-machi placement at capital | same record shape (parts + guard already matrix-visible) |

### Reused unchanged

`buildings` (precinct interiors draw as religious-palette buildings inside the reserved
rectangles), `kura`/warehouse rows, `businesses` (brokers' row, monzen rows), `fire_towers`,
`stables`/`farriers`, `manors` (merchant estates), `tanning_yards`, burakumin-quarter
housing (packed rows with caste region), `theater_stages`.

## Knobs (the FR-013 reuse surface, all on `meta()` or the placer signatures)

| knob | values | default | worked example |
|---|---|---|---|
| `ward_style` | `"mesh"` / `"fang"` | `"mesh"` | mesh (fang reserved for the first Lion city) |
| `wind_from` | compass bearing | none (no nuisance trades until declared) | `"northwest"` |
| cistern service band | real-ft street reach | 600 | 600 (calibrated liberty, disclosed) |
| terrace unit frontage | real ft | 18 | 18 (Shibata anchor) |
| rank-gradient bands | derived from budget | - | 3 bands + machi |

## State transitions

One: `wip/shiro-daika.{gen.py,json}` -> `pool/capitals/` at ship, after which the map is
pool-swept, budget-timed (`GEN_TIME_BUDGETS` entry), cache-covered, and regression-frozen
like every pool map. The farrier check flips from documented-red to green in the same move.
