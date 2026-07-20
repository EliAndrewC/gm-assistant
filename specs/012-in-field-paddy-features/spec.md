# Feature Specification: In-Field & Field-Margin Paddy Features

**Feature Branch**: (none - worked directly on `main` per the GM's solo workflow)
**Created**: 2026-07-20
**Status**: Draft
**Input**: GM wants deliberate non-rice features - grave mounds, feng-shui knolls, rock outcrops, small ponds - placed where historically appropriate per paddy type, replacing the bare tessellation gaps that currently show background through the paddy. Grounded via [research.md](research.md); GM approved "both" grave placements (margin + occasional in-field island) and full-matrix scope across all archetypes.

## Context

Rice-paddy fields currently draw plot polygons directly on the parchment background with no base fill, so
imperfect tiling leaves bare "white" gaps. The GM read those as infertile ground; research (D5) shows they
are artifacts. This feature (a) fills the gaps so flat wet paddy reads as complete, and (b) adds deliberate,
archetype-appropriate non-rice features per the research matrix - most at the field margin or on hill paddy,
with open-water ponds the one feature that genuinely belongs in the flat wet middle.

## User Scenarios & Testing

### US1 - The paddy tiles completely (Priority: P1)
Bare tessellation gaps no longer show through any paddy. **Test:** a paddy-green base fills the field
envelope under the plots; no parchment-colored gap remains inside a drawn field on any map.

### US2 - Small ponds sit in the low/head ground (Priority: P1)
A paddy may carry an open-water pond - a low pocket, a header tameike near the sluice, or a half-moon pond
fronting a homestead/hall - on valley_paddy, contour_terraces, polder_grid, ribbon_valley (never on
mulberry_dike_fishpond). **Test:** ponds are recorded, sit on eligible low/head ground, and the paddy tiles
around them; dike-pond maps carry none as an obstacle.

### US3 - Rock outcrops only where there is bedrock (Priority: P2)
In-field rock outcrops appear on contour_terraces (and occasionally ribbon_valley), never on polder_grid or
mulberry_dike_fishpond, and only at the margin (rare) on valley_paddy. **Test:** rock records honor the
archetype eligibility; a polder/dike-pond map has none.

### US4 - Graves and knolls at the slope margin (Priority: P2)
Grave-mound clusters and feng-shui knolls sit at the field margin (where paddy meets rising slope) on
valley_paddy/terraces/ribbon, on slope shoulders for terraces, never on polder/dike-pond - with an
occasional in-field grave island permitted as a disclosed calibrated liberty. Knolls stay distinct from and
rarer than the village back-grove. **Test:** graves/knolls honor archetype eligibility and the margin bias;
no map double-counts a knoll as the back-grove.

### Edge Cases
- A field with no eligible low ground draws no pond (never a forced/random one).
- The in-field grave island is rare (calibrated), not the default.
- Base fill must not paint over lanes, water, the pond, or non-field ground.
- dike-pond (kuwabata) gets the base fill but NONE of the four features.

## Requirements

- **FR-001**: A paddy-green base MUST fill each field envelope beneath the plots so no background gap shows.
- **FR-002**: Each of the four features MUST honor the per-archetype eligibility matrix in research.md.
- **FR-003**: Ponds MUST sit on eligible low/head/feng-shui ground and the paddy MUST tile around them; zero eligible ground draws none.
- **FR-004**: Rock outcrops MUST be in-field only on terraces (and occasional ribbon); absent on polder/dike-pond.
- **FR-005**: Graves/knolls MUST bias to the field margin/slope; an in-field grave island is permitted but rare (calibrated liberty, disclosed).
- **FR-006**: A standalone feng-shui knoll MUST be distinct from the village back-grove (no double count).
- **FR-007**: mulberry_dike_fishpond MUST receive none of the four features.
- **FR-008**: Every feature MUST be recorded in the manifest and gated by a validator with a negative fixture.
- **FR-009**: Every pool map MUST pass check_village; suite stays at 100% coverage.
- **FR-010**: Per-feature grounding (incl. calibrated liberty + interpolated-frequency flags) MUST be recorded in settlements.md.

## Success Criteria

- **SC-001**: No parchment gap inside any drawn paddy on any pool map (visual + geometric).
- **SC-002**: Each feature appears only on its eligible archetypes; wrong-archetype placement is impossible (pin raises or check fires).
- **SC-003**: A rendered map per archetype, inspected as an image, shows the features reading correctly (ponds in low/head ground, rock on terraces, graves/knolls at the margin) - the Principle XII closing bookend.
- **SC-004**: All pool maps pass the gate at 100% coverage.

## Assumptions
- The field builders' `low` flag (feature 010) marks eligible low ground for ponds/low-pocket placement.
- "Margin" = the dry band just outside the field envelope where it meets rising ground (the cluster/dry-plot side), reusing existing frame/margin geometry.
- Frequencies are legibility-driven estimates within the research's plausible ranges, disclosed.
