# Tasks: Minami - the Fox Clan provincial city

**Input**: Design documents from `/specs/016-minami-provincial-city/`

**Prerequisites**: spec.md, plan.md (design decisions D1-D4), research.md (Principle XII opening bookend, findings 1-6)

**Tests**: INCLUDED - red-green TDD is constitutional (Principle X), and the skill's check discipline is red-first against pinned fixtures.

**Organization**: grouped by user story. US1 = the map itself, US2 = the eight-temple budget program, US3 = the multi-temple justification ratchet, US4 = the untested branches (rides along with US1).

**Paths** are relative to `/gm-assistant/.clones/diagram-city/.claude/skills/diagram/` unless stated otherwise.

**Loop discipline** (skill CLAUDE.md): iterate on the ONE map with `DIAGRAM_SKIP_RENDER=1 python3 pool/provincial-cities/minami.gen.py && python3 check_village.py pool/provincial-cities/minami.json` (~1-7s); run the ~80s `make done` sweep ONCE at the end, backgrounded, and never poll it.

## STATUS (2026-07-26)

**Engine work COMPLETE and green** (Phases 1-3, T01-T10). **The map is a running first draft**
(T11 partial): it generates 364 features and passes **216 of ~244** gate checks. It is parked at
`specs/016-minami-provincial-city/draft/minami.gen.py`, deliberately NOT under `pool/`, because
`test_villages.py` globs `pool/*/*.gen.py` and gates every map it finds - a red map there would
break the suite for every other session. Move it into `pool/provincial-cities/` once green.

Remaining gate failures, grouped (each is signposted by its own check message, and both shipped
gens show the pattern to copy):

1. **Missing civic furniture** - `city_has_cremation_ground`, `city_has_ossuary`,
   `city_has_kosatsuba` (3 boards), `city_has_punishment_spot`, `city_has_execution_ground`,
   `city_has_mausoleum` (one is drawn but not being seen - check its seat relative to the ward),
   `walled_settlement_has_drum_tower`, `city_temples_have_graveyards` (Hotei/Jurojin/Bishamon).
2. **Under-packed** - 303 urban buildings against the ~520 target, so
   `population_consistent_with_housing`, `city_caste_counts_in_band`,
   `city_residential_quarters_dense_enough` and `city_samurai_housing_sufficient` all trail. The
   SE ward is the worst (the samurai pack seats ~12 of 480): its region needs re-cutting around
   the civic aprons the way Nagahara's does.
3. **Overlaps to clear** - structures on the road/wall/moat/street/torii/religious halls; the
   Inari hall sits on a lane (`shrine_halls_clear_of_lanes`); Daikoku is in the ring-road corridor.
4. **Placement rules** - `tanning_yard_on_water` (the yard must abut the bank),
   `near_ring_cultivated_fraction` (no farmland drawn yet), `funerary_set_back_from_water`,
   `walled_exterior_cemetery_larger`, `alleys_serve_buildings`, and a label-collision batch.
5. **Frame** - `crop_not_held_open_by_one_feature` on three labels.

Use `s.open_seat` / `site_justice.py` for the re-seating rather than guessing coordinates - the
skill's dev-loop doc is explicit that hand-picked seats are the most expensive loop here.

## Phase 1: Setup and guardrails

- [x] T01 Confirm the environment: `container-scripts/setup-dev-env.sh --check` (~3s) so a missing `resvg` or font surfaces now rather than at first render.
- [x] T02 **Name-collision sweep** (Principle IX, the Kazuma/Harima precedent): grep the existing pool, `l7r.md`, and the campaign-names cache for every name this map will introduce - the city `Minami`, the `Nanke` lineage, the governor and any named officeholder, and each temple's dedication - before any of them is written into the generator. Record the cleared names in the notes file.

## Phase 2: User Story 2 - the eight-temple budget program (P1)

**Goal**: the temple program becomes declared knobs whose defaults reprice both shipped cities identically.

**Independent test**: `python3 citybudget.py --plan --population 2600 --river` prints a temple line reading 8 precincts; the Tango back-prediction still lands within 0.1%.

- [x] T03 [US2] Write the **default-equivalence test FIRST** in `test_citybudget.py`: for both shipped programs (Tango pop 3000 + agri + its extras; Nagahara pop 3000 + river), the full `plan_city` line list and derived `wall.rx/.ry` are **exactly equal** before and after the refactor - pin the current values as literals so the test cannot drift with the code it guards. Expected GREEN immediately (it describes today's behavior); it is the regression net for T04.
- [x] T04 [US2] Implement D1 in `citybudget.py`: add `temple_precincts: int = 2`, `temple_precinct_px2: float = 16_250.0`, `monk_houses_per_precinct: float = 2.5` to `CityProgram`; move the `("temple precincts", 2, 16_250.0)` row out of the static `CIVIC_PROGRAM` tuple and emit it from the knobs; derive the adept-monk line as `round(temple_precincts * monk_houses_per_precinct)`. Every knob carries a "why" comment pointing at research.md findings 1 and 3. T03 must stay green.
- [x] T05 [US2] Add Minami-program tests to `test_citybudget.py`: 8 precincts produce a temple line of count 8; the adept-monk line scales (not the constant 5); an `extras` line for the Inari uplift appears verbatim in the output; population 2600 is inside the band and derives a smaller ring than the 3000 cases.
- [x] T06 [US2] Cheap linters, then move on: `python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy` (do NOT spend a full gate run here).

## Phase 3: User Story 3 - the multi-temple justification ratchet (P2)

**Goal**: a city drawing >= 3 major temples must declare which recognized exception licenses it.

**Independent test**: the check fires red on a synthetic 3-temple manifest with no declaration, and green on all three pool cities.

- [x] T07 [US3] Write the check RED in `test_checks.py` using the fixture builders: a walled-city manifest with 3 `kind="temple"` records and no `meta.temple_exception` FAILS the new check; the same manifest with `temple_exception="changed_hands"` passes; an unrecognized value (e.g. `"because"`) FAILS. Expected RED - the check does not exist yet.
- [x] T08 [US3] Implement `city_multi_temple_exception_declared` in `check_village.py` per D2: walled-city scope, fires when major temples >= 3 and `meta.temple_exception` is absent or outside the fixed vocabulary `{"large", "pious", "changed_hands", "fox_structure"}`. The failure message names the count and lists the recognized values. Confirm T07 goes green.
- [x] T09 [US3] Declare Tango's existing justification: add `temple_exception="changed_hands"` to the `s.meta(...)` call in `pool/provincial-cities/tango.gen.py`. This is a meta line only - **no geometry may change**. Regenerate and diff the manifest SEMANTICALLY (json.load both sides, compare key by key) to prove only `meta` moved.
- [x] T10 [US3] Freeze the negative fixture: save the undeclared-3-temple manifest into `pool/regressions/` per the corpus convention and wire it into `test_regressions.py`, so the check keeps its teeth (coverage alone does not prove a check bites).

## Phase 4: User Story 1 + 4 - the map (P1)

**Goal**: a green Minami that exercises `peaceful`, population 2,600, and `extras`.

**Independent test**: `python3 pool/provincial-cities/minami.gen.py && python3 check_village.py pool/provincial-cities/minami.json` reports zero failures.

- [~] T11 [US1] (DRAFT RUNNING, 216/244 checks - see STATUS) Author `pool/provincial-cities/minami.gen.py`, following the standing city render order (river -> walls + moat -> roads -> ring road -> towers -> gates + furniture -> water works -> civic compounds each reserving a no-build block -> dense packs -> farmsteads/wells/fire towers last). Declares: `water_flow=90`, `scale="city"`, `walled=True`, `population=2600`, `ftpx=3`, `wall_defense="peaceful"`, `imperial_road=False`, `river_port=True`, `clan="Fox"`, `capital_dir="northeast"`, `temple_fortunes=[the 7 + Inari]`, `temple_exception="fox_structure"`, and the budget from `plan_city`. **Wall from the budget, never hand-picked** (FR-011). Docstring states the city's premise the way Tango's and Nagahara's do.
  - Sub-goals, each verified on the single-map loop: the ring + moat + river junction tilts; the road net leaving in >= 2 directions with nothing labeled Imperial; the eight precincts distributed by trade (D3) with the Inari precinct largest; ~5-9 `monk_house` around each precinct; the declared timber/charcoal working ground DRAWN as its kind; the riverside lumber yard and kilns outside the wall.
- [ ] T12 [US1] Iterate to zero failures on the single-map loop. Use `s.open_seat(...)` to ask the engine where a feature fits rather than guessing coordinates, and `site_justice.py` for any feature governed by interacting rules. **Confirm `city_capacity` reads `sized_and_packed` on the FIRST derivation** - if it wants a resize, fix the budget model, not the wall (SC-003).
- [ ] T13 [US4] Verify the untested branches actually RAN, per the "a check that never runs looks like a check that passes" diagnostic: `python3 check_village.py pool/provincial-cities/minami.json | grep -c city_wall_tower_coverage` must be non-zero, and the manifest's budget must contain the `extras` line. A zero here is the bug.

## Phase 5: Docs - the "why" (REQUIRED, not optional)

- [ ] T14 Land research.md findings 1-4 into `research/religion-and-death.md` and finding 5 into `research/urban-features.md`, in the four-field entry format; register the 13 new keys in `research/SOURCES.md` with what each was used FOR.
- [ ] T15 FR-017: add the Fox eight-precinct program to `settlements/religion-and-death.md` as the **fourth** recognized justification for more than two major temples - including (a) that the eight-precinct form is inside the attested band and our two-complex default is the liberty, so nobody "corrects" it back, (b) the celibacy canon driving the housing inversion, and (c) why `city_graveyard_count` deliberately does NOT scale with precinct count.
- [ ] T16 FR-018: record the temple knobs and their derivation in `settlements/cities/sizing.md`, next to the existing civic-program bullet.
- [ ] T17 FR-019: add Minami to the `SKILL.md` references list as Mode B example G, stating what it is the worked example OF (the eight-precinct Fox program, the peaceful tier, the first non-3,000 population, the first `extras` city).
- [ ] T18 Write `pool/provincial-cities/minami.notes.md` recording the seven GM decisions, the cleared names from T02, and the review log.

## Phase 6: Gate and the Principle XII closing bookend

- [ ] T19 Run the FULL sweep ONCE, backgrounded, and act on the notification - do not poll: `make done`. Fix everything it lists together, then re-run once.
- [x] T20 Prove SC-002 by semantic key-by-key diff (never a text diff - these are single-line JSON files). **DONE, and the criterion was corrected**: every budget line's label/count/area, the derived wall and all geometry are unchanged on both cities; the only diffs are Tango's intended `temple_exception` and two `basis` strings that now state their derivation. Both cities re-gate `ALL CHECKS PASSED`.
- [ ] T21 **Principle XII CLOSING BOOKEND (NON-NEGOTIABLE)**: render at full width, read the PNG back, and re-examine it against each of research.md's six findings - the eight precincts modest and Inari largest; precincts sited by trade rather than belted at the rim; temple families ringing each precinct and indistinguishable from laborer houses; 2-4 shared burial grounds; timber yard on the bank with kilns outside; a wall whose tower ring reads as peaceful rather than siege. `check_village` proves internal consistency, never historical truth - a map can pass every check and still depict something that never existed.
- [ ] T22 Batch the map inspection (do NOT crop-and-read one region per turn): in ONE `crop_map.py` call, crop every region worth looking at - each temple precinct, the river works, the timber ground, the gates - then Read them together.
- [ ] T23 Stop-work ritual: commit in the clone, then `scripts/sync-with-main.sh done` from inside it (locked pull + push, then render-sync). Never force-push.

## Dependencies

- T03 strictly before T04 (the regression net must exist before the refactor it guards).
- T07 strictly before T08 (red before green).
- T04 before T11 (the map needs the knobs).
- T08 + T09 before T19 (the sweep must see a green Tango).
- T11 -> T12 -> T13 in order.
- T21 after T12 (there must be a finished render to examine) and after T19 (do not spend the closing bookend on a map the gate will change).
