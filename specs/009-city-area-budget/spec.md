# Feature Specification: Budget-First City Wall Sizing

**Feature Branch**: `009-city-area-budget` (not created - the GM handles all git operations)

**Created**: 2026-07-16

**Status**: Draft

**Input**: User description: "Budget-first city wall sizing for the /diagram settlement generator. Invert the order of operations for provincial-city generation: instead of guessing a wall ellipse and iterating against the post-hoc city_capacity verdict (enlarge/shrink/densify), compute the city's full space budget IN ADVANCE and derive the wall dimensions from it - the same design philosophy as the other modes (farming villages start from water flow and build paddies around it; magistrate manors start from square footage and place buildings within it; cities should start from the area budget and wrap the wall around it). Before any wall is placed: enumerate the full building inventory by caste/kind from population; classify each kind as PACKED vs SPACED and sum footprints with per-class spacing overhead; add non-building features' area; add a standard circulation (road/street/alley) fraction; sum to required interior area and derive the wall ellipse from it. Include a toggle for in-wall agricultural districts (Tango-style, not typical but not a one-off). The existing city_capacity check machinery stays as the verification gate, but generation should hit sized_and_packed on the first pass by construction rather than by iteration. Success criterion: regenerate Nagahara under the new budget-first workflow and confirm it eliminates the persistent empty-space problem while keeping all existing checks green."

## The Problem

Every settlement mode in the /diagram skill has a "first principle" its layout grows from: farming villages start from water flow and grow paddies around it; magistrate manors start from a declared square footage and place buildings within it. Provincial cities have no such principle today. City generation guesses a wall ellipse, places everything, then asks the post-hoc `city_capacity` verdict whether the guess was right (`enlarge` / `shrink` / `densify`), and iterates. Two shipped cities have now gone through that grind (Tango required a shrink-then-repack pass; Nagahara required an enlarge, then a densify, then a per-quarter density feature), and Nagahara STILL reads as having far too much empty ground inside the walls even with every automated check green - which means the iterate-until-green loop converges on maps the checks accept but the GM does not.

The fix is to invert the order of operations. Everything needed to size the wall is known before the wall is drawn: the population fixes the dwelling count; the caste mix fixes how many dwellings pack contiguously (row housing) versus how many need space around them (samurai houses, compounds); the civic program (governor's mansion, 6 ministries, temples, theater, gates) is a fixed list; circulation (roads, streets, alleys, the ring road) is a stable fraction of any pre-modern walled city's ground. Sum those and the required interior area - and therefore the wall's dimensions and circumference - is a calculation, not a guess.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Derive the wall from the space budget (Priority: P1)

As the GM generating a walled provincial city, I declare the city's population and program (which civic features, river or not, agricultural district or not), and the generator computes the full space budget FIRST - building inventory by caste/kind, packed vs spaced footprint totals, non-building features, circulation overhead - and derives the wall ellipse from that budget before placing anything. The wall is the output of the budget, not an input to be tuned.

**Why this priority**: This is the core inversion. Without it, every future city repeats the Tango/Nagahara grind, and empty-space problems keep being discovered late (or never) instead of being impossible by construction.

**Independent Test**: For a declared population and program, the generator produces a budget report (inventory, per-class areas, circulation, total interior area, derived wall dimensions) that can be checked by hand against the caste mix and the calibration city, without rendering anything.

**Acceptance Scenarios**:

1. **Given** a declared population of 3,000 and a standard provincial-city program, **When** the budget is computed, **Then** the report enumerates dwelling counts per caste (population / 5 households, split per the budgets.md caste mix), shop counts, and the full civic list, and every count is traceable to its source figure.
2. **Given** the computed budget, **When** the wall is derived, **Then** the enclosed interior area matches the budget total (within a stated tolerance), and the generator proceeds to place the wall without any post-hoc resize step.
3. **Given** the finished city, **When** the existing `city_capacity` verification gate runs, **Then** the verdict is `sized_and_packed` on the first pass - no enlarge/shrink/densify iteration.
4. **Given** the same population with a different program (e.g. river city vs landlocked, with vs without agricultural district), **When** budgets are computed, **Then** the derived walls differ in the direction and rough magnitude the program change implies.

---

### User Story 2 - Nagahara regenerated without the empty ground (Priority: P1)

As the GM, I want Nagahara rebuilt under the budget-first workflow so its walls enclose only the ground its population and program actually justify, eliminating the persistent empty-space problem that survived every previous fix.

**Why this priority**: Nagahara is the motivating defect and the proof the inversion works. A new workflow that cannot fix the known-bad case is not done.

**Independent Test**: Regenerate Nagahara from its declared population (3,000) and program (river city, canal + dock, no agricultural district) and compare against the current version - visually (the GM's eyeball is the final judge) and by measured open-ground fraction.

**Acceptance Scenarios**:

1. **Given** Nagahara's declared population and program, **When** the city is regenerated budget-first, **Then** the map passes every existing check (including per-quarter density, dead zones, population consistency) AND the GM confirms the empty-space problem is resolved.
2. **Given** the current (pre-feature) Nagahara that the GM judges too empty, **When** it is preserved as a known-bad regression fixture, **Then** the tightened acceptance line (whatever measure this feature calibrates - open-ground fraction, dead-zone size, or budget-vs-enclosed-area mismatch) flags it as failing, so the checks can never again call a GM-rejected map fully green.
3. **Given** the regenerated Nagahara, **When** its river-city features are inspected, **Then** the river/moat/canal/dock/wharf layer and all existing river-city checks still pass - the rebuild does not regress the river-city mode.

---

### User Story 3 - In-wall agricultural district toggle (Priority: P2)

As the GM, I can declare that a city keeps farms inside its walls (like Tango - not typical, but not a one-off either), and the budget adds the agricultural district's ground to the interior area, producing a proportionally larger wall for the same population.

**Why this priority**: Required for the budget model to describe both shipped cities and future ones honestly. Tango is the calibration anchor, so the model must express Tango's program - but the toggle's value is validated on the model, not by rebuilding Tango.

**Independent Test**: Compute the same city's budget with the toggle off and on; the on-budget exceeds the off-budget by the agricultural district's declared area, and the derived wall grows accordingly.

**Acceptance Scenarios**:

1. **Given** a city with the agricultural-district toggle on, **When** the budget is computed, **Then** the report itemizes the district as its own line and the derived interior area includes it.
2. **Given** Tango's declared population, program, and toggle-on setting, **When** its budget is computed, **Then** the derived wall dimensions match the shipped Tango wall within the calibration tolerance - i.e. the model back-predicts the known-good city.

---

### Edge Cases

- **Population at the band edges** (2,000 and 4,000, the canonical provincial-city range): the budget must scale smoothly across the band; neither edge may produce a wall below the readable minimum or above the canvas.
- **River cities**: the ring stands beside the river (a closed ring, per the river-city doctrine - the river never enters the walls), but the program differs: the in-wall canal + dock basin consume interior ground, while the wharf/jetties/gate-market ground OUTSIDE the wall must not be counted against the interior budget.
- **Program-heavy small city**: a population-2,000 city still carries the full mandatory civic program (governor's mansion, 6 ministries, temples, gates); the civic floor must not get squeezed out of a small budget - civic area is a fixed cost, not a per-capita one.
- **Budget/canvas conflict**: if the derived wall cannot fit the canvas at the city scale (1px = 3ft), the generator must say so up front (fail loudly with the numbers) rather than silently clamping the wall and re-creating the density problem in reverse.
- **Rounding and readability floors**: dwelling glyphs have legibility minimums that make drawn footprints larger than literal reality; the budget must use the DRAWN footprint costs, not real-world square footage, or the derivation will systematically undersize walls.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The generator MUST compute a city's complete space budget before any wall geometry is chosen. The budget MUST enumerate: (a) the building inventory by caste/kind derived from the declared population (households = population / 5, split per the budgets.md caste mix) plus shops and the full civic program; (b) the total ground cost of that inventory; (c) non-building feature areas (theater, ring road, government precinct forecourts and setbacks, reserves/drill ground, ponds, canal and dock where present, ward fences' clearances); (d) a circulation allowance (imperial road, streets, alleys) expressed as a fraction of interior area; (e) the resulting required interior area.
- **FR-002**: Every building kind in the inventory MUST carry a spacing class - PACKED (contiguous row housing: laborer, servant, burakumin, merchant rows - party walls, near-zero ambient spacing, per the established row-packing doctrine) or SPACED (samurai houses, temples, civic compounds - courtyards, setbacks, margins) - and the budget MUST cost each class with its own per-building ground overhead, calibrated so the packed classes reflect touching rows plus roji/eave gaps and the spaced classes reflect their real margins.
- **FR-003**: The circulation fraction MUST be grounded in historical research (Chinese county seats first, Japanese jokamachi as tiebreaker, per the project's China-first doctrine) AND calibrated against the shipped Tango, with the research findings and the chosen figure's "why" recorded where the rule lives (per the project's research-rule documentation requirement).
- **FR-004**: The wall dimensions MUST be derived from the required interior area, with the derivation producing walls that enclose the budget within a stated tolerance. Both shipped cities - including river-bank Nagahara - are full closed rings (the river never enters the walls, per the established river-city doctrine), so the closed-ring derivation is the required form; the design keeps room for a future open-arc form without building it now.
- **FR-005**: The generator MUST support an in-wall agricultural district toggle; when on, the district's area is added to the interior budget as an itemized line and the derived wall grows accordingly. Default is off (most cities wall their farms out).
- **FR-006**: The existing verification machinery (`city_capacity`, `city_wall_sized_to_population`, per-quarter density, dead zones, population consistency, and all other checks) MUST remain the acceptance gate. A budget-first city MUST reach the `sized_and_packed` verdict on first derivation, without any enlarge/shrink/densify iteration on the wall.
- **FR-007**: The budget MUST be reportable as a human-readable itemized statement (inventory counts, per-class areas, feature lines, circulation, total, derived wall) so the GM can audit any line before or after generation, and the manifest MUST record the budget so checks can compare promised vs delivered.
- **FR-008**: A verification check MUST compare the enclosed interior area against the budget's required area and fail on material mismatch in either direction - a wall that encloses substantially more ground than the budget justifies is the empty-space defect this feature exists to prevent, and it must be a first-class automated finding.
- **FR-009**: The model MUST be calibrated against both anchors per the project's regression discipline: shipped Tango (known-good) must back-predict within tolerance and keep passing all checks unchanged, and the current pre-feature Nagahara (GM-judged too empty despite green checks) must be pinned as a known-bad regression fixture that the new acceptance line flags.
- **FR-010**: Nagahara MUST be regenerated under the budget-first workflow from its declared population (3,000) and program (river city with canal, dock, wharf; no agricultural district), pass all checks, and resolve the empty-space problem to the GM's eye. All other pool maps MUST remain green.
- **FR-011**: The budget MUST cost buildings at their DRAWN footprints (including legibility floors and the city scale of 1px = 3ft), not real-world square footage, so the derivation sizes the wall for what will actually be rendered.

### Key Entities

- **Space budget**: the pre-wall calculation - building inventory (counts by caste/kind), spacing class per kind, per-class ground costs, non-building feature lines, circulation fraction, required interior area, derived wall parameters. Recorded in the manifest; printable as an itemized report.
- **Spacing class**: PACKED vs SPACED - the property of a building kind that determines its ground overhead in the budget (party-wall rows vs courtyard compounds).
- **City program**: the declared feature set that varies between cities - river vs landlocked, agricultural district on/off, clan/patron temples, canal/dock, estates - each with an area consequence the budget itemizes.
- **Calibration anchors**: Tango (known-good; the model must back-predict it) and pre-feature Nagahara (known-bad; the model must reject it).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The regenerated Nagahara passes every existing automated check AND the GM signs off that the empty-space problem is gone - the map reads as a packed provincial city, not a suburb inside an oversized wall.
- **SC-002**: The budget model back-predicts shipped Tango's wall dimensions within its stated calibration tolerance, and Tango plus all other pool maps remain fully green with no regeneration required.
- **SC-003**: A budget-first city reaches the `sized_and_packed` capacity verdict on the first derivation - zero wall-resize iterations - for populations across the canonical 2,000-4,000 band, with and without the agricultural-district toggle.
- **SC-004**: The pre-feature Nagahara, pinned as a regression fixture, fails the new budget-vs-enclosed-area acceptance line - a GM-rejected map can no longer be called fully green by the check suite.
- **SC-005**: Every researched constant in the budget (circulation fraction, per-class overheads, civic floor) has its "why" recorded alongside the rule, with the historical grounding documented.
- **SC-006**: The budget report lets the GM audit wall sizing as arithmetic: for any declared population and program, the report's lines sum to the required interior area and the derived wall encloses it within tolerance.

## Assumptions

- **Scope is walled provincial cities only.** Towns (walled or not), villages, hamlets, and the future capital tier are out of scope; they keep their current workflows. The budget-first principle may be extended to capitals later.
- **Tango is NOT regenerated.** It is the known-good calibration anchor; the model must describe it, not replace it. Only Nagahara is rebuilt.
- **Nagahara keeps its identity**: population 3,000, river-city program (Hayakawa bank, moat on the landward faces, water gate, canal to dock, wharf outside), clan and capital-direction metadata, quarter structure free to change as the budget dictates.
- **The existing check suite is the floor, not the ceiling.** All current checks keep passing; this feature adds the budget-vs-area acceptance line rather than relaxing anything.
- **"Empty space" is judged at the GM's eye with the automated line as backstop** - the feature's acceptance measure must be calibrated so the current Nagahara fails it, but final sign-off on the regenerated map is visual.
- **The per-quarter density machinery (feature 006) stays.** Budget-first sizing makes the wall right by construction; per-quarter checks still guard distribution within the right-sized wall.
- **Populations follow the canonical provincial-city band** (2,000-4,000, average ~3,000, 5 humans per household) from the setting's demographic notes.
