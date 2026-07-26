# Tasks: Minami - the Fox Clan provincial city

**Input**: Design documents from `/specs/016-minami-provincial-city/`

**Prerequisites**: spec.md, plan.md (design decisions D1-D4), research.md (Principle XII opening bookend, findings 1-6)

**Tests**: INCLUDED - red-green TDD is constitutional (Principle X), and the skill's check discipline is red-first against pinned fixtures.

**Organization**: grouped by user story. US1 = the map itself, US2 = the eight-temple budget program, US3 = the multi-temple justification ratchet, US4 = the untested branches (rides along with US1).

**Paths** are relative to `/gm-assistant/.clones/diagram-city/.claude/skills/diagram/` unless stated otherwise.

**Loop discipline** (skill CLAUDE.md): iterate on the ONE map with `DIAGRAM_SKIP_RENDER=1 python3 pool/provincial-cities/minami.gen.py && python3 check_village.py pool/provincial-cities/minami.json` (~1-7s); run the ~80s `make done` sweep ONCE at the end, backgrounded, and never poll it.

## STATUS (2026-07-26, second pass)

**Engine work COMPLETE and green** (Phases 1-3, T01-T10, T20). **The map gates at 8 failures of
~370 checks** and `check_village.py <m>.json --capacity` reads **SIZED_AND_PACKED** - 449 dwellings
placed in-wall against a 448 target, wall scale x1.00. Still parked at
`specs/016-minami-provincial-city/draft/`, NOT under `pool/`, because `test_villages.py` globs
`pool/*/*.gen.py` and a red map there breaks the suite for every other session.

**A NOTE ON THIS FILE'S HISTORY.** Two sessions edited this generator concurrently for several
hours (the first was believed crashed but was live). Measurements taken during that window are not
trustworthy - the generator looked nondeterministic because the source was changing between runs.
It is deterministic: identical source gives byte-identical output, verified.

### The declared population is the crux, and it is a GM decision

`spec.md` FR-010 says population ~2,600. The map cannot hold that: it delivers ~450 dwellings
where 2,600 needs 520. The first session lowered `LAY_POP` to **2000** (declared total 2,240, since
the 48 temple families ride outside the lay caste table and add 240), and that is where it sits.
`LAY_POP` cannot go lower - `citybudget.POP_MIN` is 2000.

Its reasoning, which measurement supports: eight scattered precincts - each with a compound, a
caption band and a ring of temple families - fragment the commoner quarters far more than the
two-complex program `citybudget` was calibrated on, and fragmentation costs packing efficiency the
model does not price. Note the clergy count is NOT a lever: a monk house is one dwelling and five
residents, exactly break-even.

So the options, all spec-level:
1. Accept 2,240 (current). Cheapest; contradicts FR-010's 2,600.
2. Re-derive a LARGER wall from a budget that prices fragmentation - the project's own doctrine
   ("if it wants a resize, fix the budget model, not the wall"). The honest fix, biggest change:
   every hand-placed seat on the map is absolute, so the ring moving invalidates them.
3. Trim the program (7 precincts, or a smaller timber ground) to buy back interior.

### Remaining 8 failures, and what each actually needs

1. `labels_clear_of_other_buildings` (~14 collisions) - **the one to do next, and do it by MOVING
   the captions, not by reserving more ground.** Reserving costs ~40 dwellings and still leaves ~12;
   flipping `label_below` or passing `label_xy` costs nothing. Offenders are the temple captions plus
   bathhouse/brewery, flophouse/cemetery, flophouse/stables, guard-stations/flophouse, notice
   board, dye works, burakumin, samurai neighborhood.
2. `city_samurai_housing_sufficient` (28, wants 29) and `city_caste_counts_in_band` (samurai) - one
   or two more in-wall samurai. Do NOT add extramural estates: `city_samurai_estates_outside` caps
   the drawn country seats at 3.
3. `city_row_housing_touches` (176/327, wants 180) - four more touching pairs.
4. `city_well_density_sufficient` + `city_neighborhoods_have_wells` - more draw-points. Careful:
   adding a head near the merchant warren once made density WORSE by shifting nearest-well
   assignment; verify each pass.
5. `businesses_front_streets` (19/40) - kind `merchant` is a shop-house and belongs on a frontage;
   interior rowpacks should carry only `merchant_house`.
6. `no_structure_on_street` - `place_punishment_spot()` auto-sites on a street verge and picks a
   node ~2px off the x1300 roji, which the check reads as a structure on the alley. Its verge probe
   does not honor corridors, so widening the roji's corridor does not move it; `site_justice.py`
   finds no legal seat among 60. Use the manual `s.punishment_spot(x, y, ...)` API.

### THE REGISTRY MAP - read this before touching any reservation

Which placer honors which registry, verified against `settlement.py` rather than assumed. Getting
this wrong cost most of a session:

| placer | block_polys | corridors | placed |
|---|---|---|---|
| `rowpack` | YES (`_in_blocked`) | **NO** | yes |
| `top_up`, `place_wells`, the `_fits` packs | yes | YES (`_near_corridor`) | yes |

Both are **centre**-tested; the difference is shape, not footprint-vs-centre. So a caption band needs
BOTH entries - a corridor alone lets the terraces walk under the text, a block poly alone lets the
fills do it. The original `precinct()` comment said exactly this; half the implementation was
missing, and removing the other half looked like a 33-dwelling win right up until the captions came
back. `reserve_caption_ground()` now does both, sized from the RECORDED label box (half-extents =
caption half-height + the widest row kind's), which is why it replaced two hand-rolled guesses.

**And it is ORDER-sensitive:** each precinct's caption must be reserved inside `precinct()`, before
the per-precinct `monk_house` pack runs - a pack only avoids what is in the registries when it runs.

### Other things worth not re-deriving

- **`top_up`'s clearance is why the fills were detached.** Its exact sweep held 3px off every
  neighbor, so every dwelling it seated was detached by construction - the reason the fills ran out
  of ground early AND why `city_row_housing_touches` stalled. A final party-wall pass at **gap=2.4**
  is the measured threshold: below it, fills seated behind a row block doorways
  (`city_house_doors_unblocked`) and stack terraces three deep (`city_rows_max_two_deep`).
- **Do NOT shift the x1300 roji.** Moving it 10px east reflowed every rowpack in the western
  quarters and took caption collisions from 2 to 15. A lane is load-bearing for everything that
  packs around it.
- **The SE ward is CORRECTLY low-density** (0.47/1000px^2 against the SW's 1.84). Samurai plots are
  C_SPACED 2,480px^2 against a commoner's C_PACKED 690, and the quarter also carries the yamen, six
  ministries, the mausoleum, the martial hall and two dojos. Chasing density there fights the budget.
  Servants do NOT belong inside a gated ward - terracing them there starved both samurai checks.
- **`city_capacity` runs under the check name `city_wall_sized_to_population`**, so grepping the
  gate for "city_capacity" returns 0 and looks like a check that never runs. The CLI is
  `check_village.py <m>.json --capacity [--capacity-map]`; its per-quarter density table is what
  located the starving quarters, and it is the tool to answer "wall or packing?".
- `city_government_offices_dont_abut` measures the **rotated** bbox, which a diagonal
  `face_streets` seat inflates ~40% (the offender cleared 15.5px square and failed at 12.4px turned).

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
