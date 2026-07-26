# Feature Specification: Minami - the Fox Clan provincial city

**Feature Branch**: `016-minami-provincial-city`

**Created**: 2026-07-26

**Status**: Draft

**Input**: GM request - "create a new provincial city to supplement Tango and Nagahara, since I think it would be a useful way to test our placement algorithms and automated checks on a fresh city. The city will be the provincial city of Minami, the southern province of the Kitsune family, i.e. Fox clan (a minor clan). This is a landlocked city next to a river, specifically the same Hayakawa river which runs through the Nagahara province."

## Why this map exists

The GM's stated purpose is **exercising the engine, not adding scenery**. Tango and Nagahara between them cover only a narrow slice of the city mode's declared option space, and several branches of `citybudget.py` and `check_village.py` have never been run by any map - they are held up only by unit tests, which is precisely the failure shape CLAUDE.md warns about ("a check that never RUNS looks exactly like a check that passes"). Minami is chosen to land on the untested branches:

| Knob | Tango | Nagahara | **Minami** |
|---|---|---|---|
| `wall_defense` | siege | siege | **peaceful** (never exercised) |
| `population` | 3,000 | 3,000 | **2,600** (first non-3,000 city) |
| `CityProgram.extras` | unused | unused | **used** (timber/charcoal ground) |
| `agricultural_district` | True | False | False |
| `imperial_road` | True | False | False |
| river | no | yes | yes |
| major temples | 3 (changed hands) | 2 (patron pair) | **8** (Fox seven-temple structure) |
| `meta(temple_fortunes=...)` override | unused | unused | **used** |
| clan | Crane | Crab | **Fox** (a minor clan; absent from `CLAN_FORTUNES`) |

The eight-temple program is the centerpiece: it is the first city whose religious program is not "two great compounds," and it drives the budget model, the monk-housing checks, and the graveyard rule all at once.

## Setting basis (canon, not invention)

Everything below is drawn from `l7r.md` and the existing skill docs; nothing here invents new setting.

- **The province.** Minami is the southernmost Fox province, administered by the **Nanke lineage** (`l7r.md`, "Fox Lineages and Provinces"). The Fox are a single domain of 3,000 samurai / 150,000 humans across four cardinal-named provinces - so a Fox province averages ~37,500 against the median province's ~42,000, which is what sets Minami's population below the tier average.
- **The name.** Per the place-name liberty (`settlements/water.md`, `l7r.md` "Place Names"), a provincial city takes its province's name - the provincial city of Nagahara seats Nagahara province. So the city is **Minami**.
- **The river.** The **Hayakawa** runs north-to-south past Nagahara (Crab, Reiji domain), which puts Minami **upstream**. One name end to end, per the same doctrine - no local variant.
- **The economy.** Fox wealth is the forest: lumber ("significantly more being shipped downriver" than the ~10,000 koku/yr moved by cart), charcoal (charcoal burners outnumber farmers), and Kitsune-Koh incense. That splits cleanly by channel - **the river carries bulk timber, the roads carry charcoal and incense** - and it is why the declared open ground is timber and charcoal working ground rather than Tango's paddies.
- **The Imperial road.** An Imperial road does run through Minami province, uniquely without waystations and (per `/place-names`) without `-shuku` villages by treaty. **The GM has ruled it passes miles off this city**, so Minami declares `imperial_road=False` and is served by ordinary clan roads.
- **The temples.** `l7r.md` "Fox Temples": no Grand Abbots (each temple has a **High Monk**), no Stewards (**Shika**), and the **Three Bonds** - High Monk, Temple Master, Chief of Discipline - run the temple. **These three are the only monks in a Fox temple required to be celibate**; every other position is hereditary, so "the temple's revenue sources are effectively family businesses passed down along bloodlines within the temple." The Seven Temples hold usufruct over sections of the forest, and in Fox lands the question is "which *temples* do X," not which merchant families - moneylending sits with Fukurokujin and Ebisu, wedding loans with Benten.

## GM decisions taken at design time

Recorded here so no downstream artifact re-litigates them:

1. **Road**: the Imperial road passes miles off. `imperial_road=False`; the road net leaves the map in >= 2 directions.
2. **Temples**: **seven small precincts for the seven Fortunes of Good Luck, plus an Inari precinct slightly larger than the others - and none of the eight as large as a typical provincial-city complex.**
3. **Defenses**: walled, `wall_defense="peaceful"`.
4. **River**: the Hayakawa runs north-to-south, as at Nagahara.
5. **Clergy**: ~8-12 per precinct - the three celibate Bonds inside the compound, the remaining hereditary temple families housed in the blocks around it (~5-9 households per precinct, ~40-50 citywide).
6. **Population**: ~2,600.
7. **Open ground**: timber and charcoal working ground, itemized as budget `extras`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A fresh city passes the whole gate (Priority: P1)

The GM asks for the provincial city of Minami and receives a rendered map that satisfies every check in `check_village.py` with zero mechanical failures, exactly as Tango and Nagahara do.

**Why this priority**: This is the deliverable. Every other story is a property *of* this map; without a green city there is nothing to look at and nothing to have learned.

**Independent Test**: `python3 pool/provincial-cities/minami.gen.py && python3 check_village.py pool/provincial-cities/minami.json` reports no failures, and `test_villages.py` regenerates it as part of the pool sweep.

**Acceptance Scenarios**:

1. **Given** the Minami generator, **When** it is run, **Then** it writes `minami.svg`, `minami.png` and `minami.json` and the gate reports zero failures.
2. **Given** the shipped manifest, **When** `city_capacity` is read, **Then** the verdict is `sized_and_packed` on the **first** wall derivation - no resize round-trip (per the feature-009 rule that a wall wanting a resize means the budget model, not the wall, is wrong).
3. **Given** the pool sweep, **When** `test_villages.py` runs, **Then** Tango's and Nagahara's manifests are **byte-identical** to before this feature.

---

### User Story 2 - The eight-temple program is a declared, budgeted, checked thing (Priority: P1)

A Fox city's religious program is eight modest precincts rather than two great ones, and the space budget, the doctrine files, and the gate all agree on that - rather than the map simply drawing eight compounds while the budget silently prices two.

**Why this priority**: Equal-first with the map itself, because this is the branch the GM actually wants tested. A map that drew eight temples against a two-temple budget would enclose materially the wrong amount of ground and would teach us nothing.

**Independent Test**: `python3 citybudget.py --plan --population 2600 --river` (with the temple knobs) prints a temple line reading eight precincts, and `city_wall_matches_budget` holds the drawn ring to it.

**Acceptance Scenarios**:

1. **Given** a `CityProgram` with the temple knobs left at their defaults, **When** `plan_city` runs, **Then** the temple line and the adept-monk line are **identical to today's** (2 precincts x 16,250 px^2; 5 monk houses) so both shipped cities reprice unchanged.
2. **Given** Minami's program, **When** `plan_city` runs, **Then** the temple precinct line reads 8 precincts and the adept-monk line scales with the precinct count rather than sitting at the hard-coded 5.
3. **Given** the shipped manifest, **When** `city_temples_dedicated` runs, **Then** it passes against `meta(temple_fortunes=[...])` listing the seven Fortunes of Good Luck plus Inari, with no stray and no missing fortune.
4. **Given** the shipped manifest, **When** `city_temples_have_monk_housing` and `city_monk_houses_by_their_temple` run, **Then** every one of the eight precincts has its own temple-family housing nearby and no monk house is stranded.

---

### User Story 3 - The multi-temple exception is DECLARED, not assumed (Priority: P2)

A city carrying more than two major temples has to say why, and the gate refuses a city that quietly draws extra temples with no justification on record.

**Why this priority**: `religion-and-death.md` already states that more than two major temples is "the marked exception" with recognized justifications - but nothing enforces it, so today any city could draw six temples and ship green. Minami is the map that makes the rule real. It is P2 rather than P1 because Minami is green either way; the ratchet protects *future* cities.

**Independent Test**: Remove the justification declaration from Minami's meta and confirm the new check fires; restore it and confirm it passes.

**Acceptance Scenarios**:

1. **Given** a city manifest with >= 3 major temples and no declared justification, **When** the gate runs, **Then** the new check FAILS naming the temple count.
2. **Given** Minami with its declared justification, **When** the gate runs, **Then** the check passes.
3. **Given** Tango (3 temples, changed-hands) and Nagahara (2 temples), **When** the gate runs, **Then** both still pass - Tango by declaring its existing changed-hands justification, Nagahara by being under the threshold.

---

### User Story 4 - The untested budget and defense branches get run by a real map (Priority: P2)

`wall_defense="peaceful"`, a non-3,000 population, and `CityProgram.extras` are exercised by a shipped map rather than only by unit tests.

**Why this priority**: This is the GM's stated motive for a third city, but it rides along with the map rather than needing separate work.

**Independent Test**: Grep the gate output for the peaceful-tier coverage check and confirm it appears (a count of 0 would mean the branch still never runs).

**Acceptance Scenarios**:

1. **Given** the shipped manifest, **When** `check_village.py pool/provincial-cities/minami.json | grep -c city_wall_tower_coverage` is run, **Then** the count is non-zero and the check evaluated the `peaceful` branch.
2. **Given** the shipped manifest, **When** the budget is read back, **Then** it contains at least one `extras` line for the timber/charcoal working ground, and the ground so claimed is DRAWN (not ambient slack).

---

### Edge Cases

- **Eight precincts vs. the 2-4 graveyard ceiling.** `city_graveyard_count` demands 2-4 temple graveyards at city scale. Eight precincts do not get eight graveyards: the Fox precincts are economic institutions holding forest usufruct, not eight separate parishes, so the city's dead go to a small number of shared burial grounds. The ceiling stands unchanged and the reasoning is recorded with the rule.
- **Monk houses vs. the caste bands.** ~40-50 monk households are real dwellings for the population count but sit OUTSIDE the lay caste table, per the existing `monk_house` doctrine. At this scale they are ~8-10% of dwellings - far more than any previous map - so `city_caste_counts_in_band` must be verified not to drift as a side effect.
- **A temple neighborhood that is eight neighborhoods.** `city_temple_neighborhood_has_shrines` fires only where >= 2 temples cluster within 400px. Eight precincts distributed through the quarters may form one cluster, several, or none; whichever occurs, the wayside-shrine floor must be satisfied for each cluster that exists.
- **Smaller precincts and the torii roll.** Torii count is patronage, rolled per temple on the city column (30/40/30 for 1/3/7). Eight rolls will produce some 7s; a 7-arch avenue must still fit a *modest* precinct's approach without standing in a wall (`torii_clear_of_walls` shortens rather than overlapping).
- **Peaceful tier on a river city.** The sparser tower ring must still cover the river-facing curtain, where the moat gives way to the river arc.

## Requirements *(mandatory)*

### Functional Requirements

**The budget model**

- **FR-001**: `CityProgram` MUST expose the temple program as declared knobs - the number of precincts and the ground each takes - rather than the hard-coded `("temple precincts", 2, 16_250.0)` row.
- **FR-002**: The adept-monk housing line MUST derive from the precinct count rather than the constant 5, and its basis string MUST state the derivation.
- **FR-003**: Default knob values MUST reproduce today's budget exactly, so Tango's and Nagahara's derived walls and shipped manifests are unchanged. The `test_citybudget.py` Tango back-prediction remains the guard.
- **FR-004**: The Inari precinct's extra ground over its seven siblings MUST appear as its own auditable line, so "slightly larger" is a number on the sheet rather than a claim in prose.
- **FR-005**: Minami's timber and charcoal working ground MUST be declared through `CityProgram.extras`, with a `basis` string giving the reasoning and the real-feet sizing.

**The gate**

- **FR-006**: A walled city drawing >= 3 major temples MUST declare a justification, and the gate MUST fail one that does not. Recognized justifications are the three already in `religion-and-death.md` (especially large, especially pious/pilgrimage, changed hands) plus the new Fox structural case.
- **FR-007**: Tango MUST declare its existing changed-hands justification to keep passing; this is a declaration added to its meta, not a change to its map.
- **FR-008**: `city_temples_dedicated` MUST accept Minami's eight declared fortunes through the existing `meta(temple_fortunes=[...])` override with no change to the check's logic.
- **FR-009**: Every new or changed check MUST be red-tested against a deliberately broken synthetic manifest in `test_checks.py` before the fix, per the standing "every found defect becomes an automated check" rule.

**The map**

- **FR-010**: The map MUST be a walled provincial city named Minami, population ~2,600, at 3 ft/px, `wall_defense="peaceful"`, `imperial_road=False`, `clan="Fox"`, on the Hayakawa running north-to-south.
- **FR-011**: The wall MUST be derived from `plan_city` - never hand-picked - and `city_capacity` MUST read `sized_and_packed` on the first derivation.
- **FR-012**: The map MUST carry eight major temple precincts: seven dedicated to the Fortunes of Good Luck and one to Inari, the Inari precinct visibly the largest of the eight and every one of them smaller than Tango's or Nagahara's complexes.
- **FR-013**: Each precinct MUST have its hereditary temple families housed in the blocks around it (`monk_house`), ~5-9 per precinct.
- **FR-014**: The road network MUST leave the map in >= 2 directions with no road labeled Imperial (`city_roads_run_offmap`).
- **FR-015**: The timber economy MUST be visible: rafting/landing works on the river outside the wall, and the declared timber/charcoal working ground inside it, drawn as its kind rather than left as bare ground.
- **FR-016**: Every new manifest key MUST be classified in `_OVERLAP_STRUCTS` (or `_OVERLAP_EXEMPT` with a reason) and given a caption group in `_LABEL_GROUP`, per the KEEP-CLEAR CONTRACT.

**The docs (the "why", per the project's REQUIRED research-grounding rule)**

- **FR-017**: `settlements/religion-and-death.md` MUST record the Fox eight-precinct structure as a fourth recognized justification for more than two major temples, including the celibacy canon that drives the housing inversion and the reason the graveyard ceiling does not scale with precinct count.
- **FR-018**: `settlements/cities/sizing.md` MUST record the temple-program knobs and what the Minami numbers were derived from.
- **FR-019**: The map MUST be added to the `SKILL.md` references list as Mode B example G, stating what it is the worked example OF.

### Key Entities

- **Temple precinct (Fox variant)**: a small walled compound holding only the three celibate Bonds, with its hereditary temple families living out in the surrounding blocks. Eight per city; recorded as `kind="temple"` in `M["religious"]` exactly as today.
- **Temple family household**: `kind="monk_house"` - drawn identical to a laborer house, real for the population count, outside the lay caste bands. ~40-50 citywide.
- **Timber/charcoal working ground**: declared open ground inside the wall, itemized in the budget and drawn as its kind.
- **Multi-temple justification**: a map-level declaration naming which recognized exception licenses a city's third-and-beyond major temple.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `check_village.py` reports **zero failures** on `minami.json`.
- **SC-002**: **No number moves** in Tango's or Nagahara's manifest - every budget line's label, count and area, the derived wall, and all geometry are unchanged, and the `test_citybudget.py` Tango back-prediction still re-derives the shipped 487x457 ring to within 0.1%. *(Measured: the only permitted diffs are Tango's intended `temple_exception` meta line and two budget `basis` STRINGS - the temple and adept-monk lines now state their derivation instead of the generic civic-floor sentence. The original wording of this criterion said "byte-identical"; that was written before the basis strings were known to improve, and is corrected here rather than being quietly satisfied by leaving worse documentation in place.)*
- **SC-003**: `city_capacity` on Minami reads `sized_and_packed` at the **first** wall derivation, with no manual resize.
- **SC-004**: The new multi-temple-justification check **fires red** on a synthetic manifest with 3 undeclared temples and passes on all three pool cities.
- **SC-005**: `city_wall_tower_coverage` appears in Minami's gate output with the `peaceful` tier evaluated (grep count > 0), closing a branch no map has ever run.
- **SC-006**: `make done` is green: ruff, ruff format, mypy --strict, pytest, and 100% coverage on `check_village.py`, `settlement.py` and `citybudget.py`.
- **SC-007**: Every dwelling caste stays within +/-30% of its budgets.md target (`city_caste_counts_in_band`) despite ~40-50 monk households riding outside the bands.

## Assumptions

- **The GM's seven decisions above are settled** and are not re-opened by plan or tasks.
- **Minami sits on the EAST bank** of the Hayakawa (the river running down the city's west flank), mirroring Nagahara's west-bank arrangement. Chosen for variety rather than canon - no source constrains the bank - and recorded here so it is a decision rather than an accident.
- **`capital_dir="northeast"`**: Otosan Uchi lies in northeastern Rokugan, so the samurai country estates face northeast, as Nagahara's do.
- **`water_flow=90`** (south): the Hayakawa comes out of the Kitsune Mori to the north and runs south toward Crab lands, consistent with its bearing at Nagahara downstream.
- **The seven Fortunes of Good Luck** are Benten, Bishamon, Daikoku, Ebisu, Fukurokujin, Hotei and Jurojin, matching the set already in `CLAN_FORTUNES`.
- **The Fox are NOT added to `CLAN_FORTUNES`.** They have no two-patron structure to record; the eight-fortune list is declared per-map through the existing `temple_fortunes` override. A future Fox map declares its own program the same way.
- **Total clergy stays comparable to a normal provincial city** (~70 across eight precincts vs ~30-60 across two), so the temple-density canon is redistributed rather than inflated.
- **Capitals remain out of scope** - this is the provincial-city tier only.
