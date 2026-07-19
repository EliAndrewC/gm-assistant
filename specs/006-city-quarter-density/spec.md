# Feature Specification: City Quarter Density and Wall-Sizing Correctness

**Feature Branch**: `006-city-quarter-density`

**Created**: 2026-07-13

**Status**: Draft

**Input**: User description: "Spatial (per-quarter) density and wall-sizing correctness for /diagram provincial cities, so a walled city ends at an appropriate, evenly-distributed density with its people inside the walls - fixing the failure where the current global-aggregate capacity check passed a lopsided Nagahara (dense east, empty NW temple quarter, ~35 commoner dwellings spilled outside the walls, one near-empty block)."

## Context and Problem Statement

The `/diagram` skill generates top-down maps of L7R provincial cities and gates each one through an automated validator (`check_village.py`). A prior feature added a wall-sizing analysis (`city_capacity`) meant to answer "do the walls enclose too much or too little space for the target population." It shipped a city (Nagahara, target 3,000) that reads as broken to the GM: a densely packed east half, a NW temple quarter with zero commoner dwellings, a near-empty interior block, and roughly 35 commoner dwellings spilled OUTSIDE the walls to the north-east and south-east - an extramural neighborhood that has no business being outside a walled city.

The validator passed it anyway. Three defects let it through:

1. **The capacity check is a global aggregate.** It compares total residential-capable area (times a canonical density) against total placed dwellings. Both are city-wide sums, so a dense east and an empty west average to "about right." It is mathematically blind to how dwellings are distributed.
2. **The population count ignores the walls.** For a walled city it counts every dwelling regardless of whether it sits inside the rampart, so the generator satisfied the target by spilling ~35 dwellings into the surrounding fields. Counted inside-only, the city holds 525 dwellings (below the target band) and would have been flagged.
3. **Open space is measured in a way that cannot distinguish empty blocks from normal packing.** Packed row-housing is mostly interstitial gaps, so a well-packed city already reads about half "open"; the single open-fraction number cannot separate a genuinely empty quarter from ordinary breathing room.

The deeper lesson: a spatial, distributional property was reduced to one scalar and calibrated on the good example until it read "pass," with no known-bad map kept as a fixture that must fail. This feature replaces the global-aggregate model with a per-quarter, spatially-aware one, closes the extramural leak, and reframes wall-sizing so that "shrink the wall" is a genuine, recommended outcome.

## User Scenarios & Testing *(mandatory)*

The primary user is the GM generating a city map in conversation. The secondary "user" is the generator/validator toolchain that must be structurally unable to pass a lopsided or leaky city.

### User Story 1 - The validator rejects a lopsided or leaky city (Priority: P1)

The GM (or the skill on their behalf) runs the validator on a city map. If any residential part of the city is left near-empty, or commoner dwellings sit outside the walls, or the interior is too sparse to house the declared population, the validator flags exactly that, naming the offending quarter or the extramural dwellings, so the map cannot ship looking broken.

**Why this priority**: This is the whole point of the feature and the MVP. Without it, the toolchain keeps green-lighting maps that visibly fail the GM's eye. It is the acceptance gate for everything else.

**Independent Test**: Run the validator against the current broken Nagahara map (snapshotted before any change). It must flag the sparse interior, the empty NW temple quarter, the near-empty block, and the ~35 extramural commoner dwellings. Run it against the good Tango map: it must pass. Deliverable value: a bad map is caught, a good map is not, before a single generator line changes.

**Acceptance Scenarios**:

1. **Given** the pre-change Nagahara map (525 dwellings inside a wall sized for ~600, plus ~35 commoner dwellings outside), **When** the validator runs, **Then** it reports the interior as under-filled for the population target and it does not report "about right."
2. **Given** the pre-change Nagahara map, **When** the validator runs, **Then** it flags the commoner dwellings sitting outside the walls (as distinct from legitimately-extramural samurai estates, farmhouses, wharf, and gate market, which are not flagged).
3. **Given** a residential quarter that is nearly empty (the NW temple area or a near-empty block), **When** the validator runs, **Then** it names that quarter/region as below the expected residential density.
4. **Given** the good Tango map, **When** the validator runs, **Then** none of the new checks fire.

### User Story 2 - The city declares its quarters and reserves as first-class regions (Priority: P2)

The generator declares the city's quarters explicitly: each quarter is a region with a zoning type (residential, civic, mixed, or reserve). Reserve quarters (drill ground, garden, agricultural district) additionally declare their kind and are drawn as that visible feature, so open ground is a deliberate, legible choice rather than accidental emptiness. The validator reads these declarations as ground truth instead of inferring quarters from pixels.

**Why this priority**: The per-quarter checks need to measure the regions the generator intended, not arbitrary tiles. Declared regions also let "empty" and "reserved" be a stated distinction rather than a guess, which is what makes the anti-trap guards enforceable.

**Independent Test**: Generate a city that declares quarters; confirm the map records each quarter's polygon and zone, that reserve quarters render as their named feature, and that the validator's per-quarter report lists each declared quarter with its measured density. Value: the city's zoning is explicit and inspectable.

**Acceptance Scenarios**:

1. **Given** a generated walled city, **When** it is produced, **Then** the map records a set of quarters that tile the walled interior, each with a zone type, with reserves carrying a kind.
2. **Given** a reserve quarter (e.g. a drill ground), **When** the city renders, **Then** that ground is visibly drawn as its declared kind, not left blank.
3. **Given** a walled city that declares no quarters, **When** the validator runs, **Then** it flags the omission rather than silently falling back to a global-only judgment.

### User Story 3 - Wall-sizing recommends the right corrective action (Priority: P3)

When a city does not fit its population well, the capacity analysis tells the GM which of a small set of corrective actions to take: densify the residential quarters (the wall is right, placement is sparse), enlarge the wall (even packed, it cannot hold the target), or shrink the wall (the residential program cannot fill it without inventing open ground). The reserve mechanism cannot be used to launder emptiness: declared reserves are capped as a fraction of the interior, and every square of civic or reserve ground reduces the residential ground the wall is judged against, so hiding empty ground as "reserve" pushes the verdict toward "shrink the wall."

**Why this priority**: This turns the diagnosis into a clear next step and makes "shrink the wall" - the action Nagahara actually needed - a first-class outcome. It depends on the per-quarter accounting from US1/US2.

**Independent Test**: Run the capacity analysis on the broken Nagahara: it recommends densify or shrink (not "about right"). Construct a variant whose empty ground is all declared as reserve beyond the cap: the analysis flags the reserve over-cap and/or recommends shrinking, never "about right." Value: the tool's recommendation matches what a person would decide by looking.

**Acceptance Scenarios**:

1. **Given** a city whose interior is sparsely filled but the wall could hold the target if packed, **When** the analysis runs, **Then** it recommends densifying (not resizing).
2. **Given** a city that cannot reach the target even packed, **When** the analysis runs, **Then** it recommends enlarging the wall.
3. **Given** a city whose residential quarters cannot fill the wall without large open ground, **When** the analysis runs, **Then** it recommends shrinking the wall.
4. **Given** a city that declares more than the allowed fraction of its interior as reserve, **When** the validator runs, **Then** it flags the reserve as over the cap.

### Edge Cases

- A quarter polygon that crosses the wall line, or quarters that overlap each other or leave interior gaps uncovered - how is the interior partitioned and are gaps/overlaps flagged?
- A small city where one quarter effectively spans most of the interior (does per-quarter degenerate back into a global judgment, and is that acceptable at small scale?).
- An unwalled provincial city (do quarters and inside-the-wall accounting apply, or is this walled-only?).
- A legitimately-extramural cluster (samurai estates across a river, the wharf suburb) - must not be flagged as spilled dwellings.
- A civic quarter (temples, government yamen) that is mostly open ground around its compounds - how much non-civic open is tolerated before it counts against the wall.
- A residential quarter deliberately kept lower-density (e.g. wealthier samurai lots) - does the band accommodate a range of legitimate residential densities.
- Cities with an agricultural district (Tango) whose in-wall fields are a declared reserve.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: For a walled city, the population accounting MUST count only dwellings located inside the walls; dwellings outside the walls MUST NOT count toward the declared population.
- **FR-002**: The validator MUST flag ANY commoner dwelling (laborer, merchant, burakumin, servant kinds and their large variants) located outside the walls - the tolerance is a hard zero. Legitimately-extramural elements MUST NOT be flagged: samurai country estates, farmhouses, the wharf suburb, and gate-market shops. (Rationale: a walled city's commoners shelter inside the rampart; a hard zero closes the leak completely and leaves no allowance the generator can quietly fill.)
- **FR-003**: A walled city MUST declare its quarters as first-class regions in the map data: each quarter a polygon plus a zone type in {residential, civic, mixed, reserve}; reserve quarters additionally carry a kind (e.g. drill ground, garden, agricultural district).
- **FR-004**: The declared quarters MUST cover the walled interior; the validator MUST flag interior ground that belongs to no quarter, and MUST flag quarters that overlap or fall outside the walls.
- **FR-005**: Reserve quarters MUST be rendered as their declared kind (a visible feature such as a drill ground surface, garden, or fields), so that intentional open ground is legible and distinguishable from accidental emptiness.
- **FR-006**: The validator MUST evaluate residential (and mixed) quarters for LOCAL dwelling density and flag any such quarter whose density falls below (or above) an acceptable band, naming the quarter. A near-empty residential quarter or block MUST fail.
- **FR-007**: The validator MUST flag a civic quarter whose non-civic open ground exceeds an allowed share, so emptiness cannot be hidden by labeling a mostly-empty region "civic."
- **FR-008**: Total declared reserve ground MUST be capped at ~20% of the walled interior; the validator MUST flag a city that exceeds the cap. (Rationale: a fifth of the interior comfortably fits a yamen drill ground plus temple gardens plus an agricultural district; beyond that the wall is enclosing more open ground than a provincial city justifies, which should read as "shrink the wall," not "reserve.")
- **FR-009**: The wall-sizing analysis MUST compute the wall's residential capacity against USABLE residential ground (interior minus civic minus reserves), not the raw interior, so that civic and reserve ground reduce the residential capacity the wall is judged against.
- **FR-010**: The wall-sizing analysis MUST return one of a small set of verdicts, each mapping to a distinct corrective action: densify (wall right, placement sparse), enlarge the wall (cannot hold target even packed), shrink the wall (residential program cannot fill the wall without excess open ground), or sized-and-packed (correct). The under-filled/"densify" boundary MUST align with the population tolerance so the capacity verdict and the population check agree.
- **FR-011**: The per-quarter density band and the extramural, reserve-cap, and civic-open thresholds MUST be calibrated empirically against BOTH a known-good city (Tango, which must pass) and a known-bad city (the pre-change Nagahara, which must fail), and the calibration rationale (the "why" behind each number) MUST be recorded alongside the rule.
- **FR-012**: The pre-change Nagahara map MUST be snapshotted as a permanent negative fixture BEFORE any generator change, and the new checks MUST demonstrably fire on it (under-filled interior, empty NW quarter, near-empty block, extramural commoner dwellings). The good Tango map MUST be a positive fixture that the new checks pass.
- **FR-013**: After the checks exist and fire on the bad fixture, the Nagahara generator MUST be corrected so the shipped city has no commoner dwellings outside the walls, every residential quarter within the density band, any intentional open ground declared and rendered as a reserve within the cap, and a wall sized so the residential quarters fill it - passing the full validator.
- **FR-014**: The new checks MUST integrate with the existing red-first check discipline: add the general rule, prove it fires on the defective artifact, fix the artifact, then pin the defective manifest as a regression fixture; and unit-test each new check.
- **FR-015**: The doctrine document for settlements MUST be updated to describe the quarter/zoning model, the per-quarter density judgment, the reserve rules, and the reframed wall-sizing verdicts, including the reasoning behind each threshold.
- **FR-016**: Tango MUST be retrofitted to declare its quarters under the new model as part of THIS feature, and every walled city MUST declare quarters with no grandfathered exceptions. Both worked cities thus exercise the quarter-based checks, and Tango serves as the known-good calibration anchor for the density band. (Rationale: the band cannot be calibrated on the bad city alone; a live "declare quarters unless grandfathered" exception is exactly the kind of carve-out the next city would copy.)

### Non-Functional / Project Requirements

- **NFR-001**: All new pure-logic code MUST retain 100% line coverage (project testing standard).
- **NFR-002**: No em-dashes or en-dashes anywhere in code, tests, docs, or generated content (project style rule; hyphens only).
- **NFR-003**: Historical grounding MUST follow the project's China-first geography stance, and every research-driven threshold MUST record its "why" per the project's constitution.
- **NFR-004**: Scope is provincial cities. Domain capitals are a later tier and out of scope. Existing non-city settlements (hamlets, villages, towns) MUST continue to pass unchanged.

### Key Entities

- **Quarter**: a declared region of the walled interior - a polygon plus a zone type (residential, civic, mixed, reserve) and, for reserves, a kind. The unit at which density is judged.
- **Reserve**: a quarter of intentionally open/non-residential ground with a declared, rendered purpose (drill ground, garden, agricultural district), subject to a total-interior cap.
- **Residential-capable ground**: the walled interior minus civic and reserve ground - the area the wall's population capacity is judged against.
- **Capacity verdict**: the analysis outcome (densify / enlarge / shrink / sized-and-packed) plus its supporting per-quarter density report and wall-size recommendation.
- **Regression fixtures**: the pinned pre-change Nagahara (must fail the new checks) and the good Tango (must pass).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Running the validator on the snapshotted pre-change Nagahara flags all four defects: under-filled interior, the empty NW temple quarter, the near-empty block, and the extramural commoner dwellings. (Today it reports "about right" and passes.)
- **SC-002**: Running the validator on the good Tango triggers none of the new checks.
- **SC-003**: After correction, the shipped Nagahara has zero commoner dwellings outside the walls (down from ~35), and every residential quarter's local density falls within the calibrated band.
- **SC-004**: After correction, the shipped Nagahara passes the full validator with the population counted inside-the-wall only, and its wall is sized so no residential quarter is left near-empty (no single residential quarter below the band's floor).
- **SC-005**: The wall-sizing analysis, run on any city, returns a verdict that maps to a single clear action (densify / enlarge / shrink / sized-and-packed), and its under-filled boundary agrees with the population check (they never disagree on the same map).
- **SC-006**: A constructed city that hides its empty ground as over-cap reserve is flagged (either reserve-over-cap or a shrink recommendation), never "sized-and-packed."
- **SC-007**: The whole existing map pool plus the two worked cities pass their intended verdicts, with 100% pure-logic test coverage maintained and no forbidden dashes introduced.

## Assumptions

- The feature is walled-city-scoped; unwalled provincial cities keep their current treatment unless a quarter model is trivially applicable. Hamlets, villages, and towns are unaffected.
- "Commoner dwellings" means laborer/merchant/burakumin/servant kinds (and large variants); samurai estates are treated as legitimately extramural country seats.
- The per-quarter density band is a range (not a single value) so that legitimately lower-density residential quarters (e.g. samurai lots) and denser commoner warrens both pass, while a near-empty quarter fails.
- Tango is retrofitted to declare quarters as part of this feature (FR-016, confirmed), so both worked cities exercise the model and anchor calibration.
- The reserve mechanism exists to give real, rendered purpose to open ground (drill grounds, gardens, agricultural districts); it is not a means to exempt arbitrary emptiness, which the cap and the residential-ground accounting prevent.
- Domain capitals, and any city scale above provincial, are explicitly out of scope.
