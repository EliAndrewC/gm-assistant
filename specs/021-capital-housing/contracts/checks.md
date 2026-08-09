# Gate Contract: Capital Housing Layer (021)

The externally-visible interface of a /diagram feature is its gate rules - what
`check_village.gate()` newly demands of a capital manifest. Every rule follows the standing
discipline: red-green TDD, regression fixture for the motivating defect where one exists,
scale-scoped so no shipped map changes verdict except as listed, footprint family declared
(gap verdict / classification / association / point fixture), and the declaration-existence
pattern for anything gated on an optional `meta` field.

## Extended to capital scale (existing city rules; must PASS on the finished map)

- `population_consistent_with_housing`, density floors, quarter tiling - the housing
  authority (FR-001).
- `city_wells_*` + watered-dwellings reach - with the cistern extension below.
- fire-cover battery (`fire_tower_*`) at the capital count.
- `businesses_front_streets`, `poor_housing_mostly_interior`, row-depth rules - the machi
  doctrine unchanged at 3 ft/px.
- burakumin segregation + tanning-yard battery - now also wind-gated (below).
- `imperial_road_town_has_farrier` - flips green; its "documented sole failure" note in the
  notes file is retired.
- INVERTED at capital (already law from 020 research, asserted by tests): no
  `city_has_governor_mansion`, `s.manor` allowed in-wall, senior-majority housing mix
  (capital variant of `city_samurai_housing_varied`).

## New rules

| rule | scope | family | red case (fixture or test) |
|---|---|---|---|
| `capital_rank_gradient` | capital | classification (band membership by center) + ordering | a yashiki seated beyond the terrace band's mean castle distance |
| `capital_districts_declared` | capital | declaration-existence | packs ran with no `districts` records |
| `cistern_wells_in_service_band` | any map with aqueduct | gap verdict (street-path reach) | a `kind:"cistern"` well beyond the band; a band dwelling served by no well |
| `nuisance_trades_downwind` | city + capital | bearing (aggregate; deliberate) | tanning yard upwind of dwellings with `wind_from` declared |
| `nuisance_needs_declared_wind` | city + capital | declaration-existence | nuisance trade present, no `wind_from` |
| `precinct_interiors_within_reservation` | capital | gap verdict (footprints vs reserved rect) | a dormitory overhanging the reservation |
| `precinct_graveyard_claims_closed` | capital | declaration audit | `graveyard: true` with no drawn ground |
| `monzen_fronts_the_approach` | capital | association (center-to-way reach) | monzen row on the blind side of the temple |
| `teramachi_backstrip_lean` | capital | gap verdict (depth bound) | packed rows silting the rim strip |
| `kido_close_the_machi_mouths` | capital | point fixture (kido records parts - matrix-visible) | a machi street mouth with no kido |
| `terraces_are_ranges` | any | classification | a terrace record with units < 2 (a detached house miscoded) |

## Verdict-change budget

Only `wip/shiro-daika` (becoming `pool/capitals/shiro-daika`) changes verdicts. The three
provincial cities MUST NOT change verdict under any new rule (the wind rules are
declaration-gated; no shipped city declares `wind_from`, so their tanning yards stay
governed by the existing outcast-side battery until a separate feature declares winds for
them - recorded as deliberate, not silent).

## Regression fixtures

Each new rule freezes its red case: either the mid-build capital manifest exhibiting the
defect (preferred, per the flush-corner and stub-gate precedents) or a constructed minimal
manifest when the defect never naturally occurred.
