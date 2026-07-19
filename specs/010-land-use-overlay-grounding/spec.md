# Feature Specification: Land-Use Overlay Historical Grounding

**Feature Branch**: (none - worked directly on `main` per the GM's solo workflow)

**Created**: 2026-07-19

**Status**: Draft

**Input**: GM: fix the `land_use_overlay` knob's historical grounding, rigorously through spec-kit, with historical-grounding analysis as the opening steps and grounding verification as the closing steps.

**REVISED after Phase 0 (2026-07-19).** The original input was "drop `mulberry_fishpond` from the overlay knob and bind `lotus` to the wettest plots." Phase 0 research **refuted the first half**: a scatter of dike-ponds among rice was the system's normal state (Shunde county was ~4.6% dike-pond in 1581; Lake Tai kept mulberry on the *tang* banks with rice as the polder's main crop permanently). `mulberry_fishpond` therefore STAYS as an overlay. The real defect is shared by both values and is different from the one assumed: the overlay has an economic term (`fraction`) but **no topographic filter**. See [research.md](research.md) D2. GM confirmed the reversal.

## Context

The `/diagram` Mode B `land_use_overlay` knob recolors a fraction of a settlement's paddy plots to depict a secondary land use. A prior pass shipped a `rape` value that was historically impossible - rice and rape are the two halves of ONE rotation in the SAME plot, so they are never both standing. It passed every automated check and its unit tests, and was caught only when the GM looked at the rendered map and asked what the yellow blocks were. `rape` has since been removed.

That failure exposed a second, subtler class of error still living in the remaining values: the overlay picks its plots with a uniform random sample, when in reality **what determines a secondary land use is the ground, not chance**. This feature corrects the remaining values on that basis, and is the first feature to run under **Constitution Principle XII (Historical Grounding Bookends)**.

Phase 0 sharpened that diagnosis into a two-term rule that governs every value:

> **Topography sets which plots are ELIGIBLE. Economy decides how many of the eligible plots CONVERT.**

The current implementation has only the second term - a `fraction` applied by uniform random sample - and no topographic filter at all. The fix is to add the missing filter and let `fraction` mean what it should always have meant: a share of the *eligible* ground.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A lotus paddy sits where lotus actually grew (Priority: P1)

As the GM, when a village rolls the `lotus` overlay, I want the lotus plots to occupy the low, permanently-wet ground - the plots the engine already marks as flooded because they sit on the drain - rather than plots scattered at random across the field, so the map shows *why* those plots are lotus.

**Why this priority**: This is the substantive correction. It changes what the map asserts about the land.

**Independent Test**: Roll or pin the lotus overlay on a comb-field map; every lotus plot coincides with a plot the field engine flagged as low/wet, and none sits on ordinary upper-field rice ground.

**Acceptance Scenarios**:

1. **Given** a comb field with low plots flagged as flooded, **When** the lotus overlay is applied, **Then** every recolored plot is one of those low plots.
2. **Given** a field with very few low plots, **When** lotus is applied, **Then** the overlay covers only those plots (a small honest count) rather than padding out to a target fraction.
3. **Given** a field with no low/wet plots at all, **When** lotus is applied, **Then** the overlay draws nothing and records a zero count, rather than falling back to random placement.

### User Story 2 - Dike-ponds are dug in the flood-prone hollows, in patches (Priority: P1)

As the GM, when a village rolls the `mulberry_fishpond` overlay, I want the ponds dug out of the low, flood-prone ground and clustered in patches, because that is how the conversion actually spread - one household digging one low plot into a pond in one dry season (挖塘培基), the patch growing outward over generations. A uniform sprinkle across the whole field depicts a conversion pattern that did not happen.

**Why this priority**: Same defect as lotus, same fix, and it is the more common roll of the two.

**Independent Test**: Roll or pin the dike-pond overlay; every pond coincides with a plot the field engine flagged low/wet, and the ponds form patches rather than an even scatter.

**Acceptance Scenarios**:

1. **Given** a field with low plots flagged as flooded, **When** the dike-pond overlay is applied, **Then** every pond sits on one of those low plots.
2. **Given** a map that already uses the `mulberry_dike_fishpond` field archetype, **When** it is regenerated, **Then** it does not ALSO carry the overlay - the landscape is drawn once, as the archetype.
3. **Given** a field with no low/wet plots, **When** the overlay is applied, **Then** nothing is drawn and a zero count is recorded.

### User Story 3 - The grounding survives the next pass (Priority: P2)

As a future maintainer, I want the reasoning for each surviving *and* rejected overlay value recorded where the rule lives, so a later pass does not reinvent a rejected design or re-randomize a topography-driven one.

**Independent Test**: `settlements.md` and the overlay driver's docstring each state, per value, what governs it in reality; the rejected values (`rape`, `mulberry_fishpond`-as-overlay) carry their rejection reasoning.

### Edge Cases

- A field archetype with no flooded plots at all (terraces where the flag lands elsewhere, a polder, a ribbon valley): lotus must degrade to "nothing drawn", never to random placement.
- Maps that currently carry a plot-based overlay (Kikuta, Kuwabata, rolled-a, rolled-b) all change appearance, because placement moves from random to wet-ground-only. They must be regenerated and re-verified, not assumed.
- Kuwabata carries the dike-pond archetype AND the dike-pond overlay - the same landscape drawn twice. It sheds the overlay under FR-008.
- The existing `land_use_overlay_drawn` check must not fire spuriously when an overlay legitimately covers only a few plots.
- A field whose eligible plots are few may yield a visibly sparser overlay than the old uniform 32%. That is the honest outcome, not a regression.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `land_use_overlay` knob's value space MUST be exactly `none`, `mulberry_fishpond`, `lotus`, `tea_fringe` (unchanged; the removal of `rape` in the prior pass stands).
- **FR-002**: Pinning the removed `rape` value MUST be a loud error, never silently drawn or silently ignored.
- **FR-003**: The plot-based overlays (`lotus`, `mulberry_fishpond`) MUST place only on plots the field engine marks as low/wet, never on a uniform random sample of all plots.
- **FR-004**: When no low/wet plots exist, a plot-based overlay MUST draw nothing and record a zero count, never falling back to random placement.
- **FR-005**: `mulberry_fishpond` ponds MUST be clustered in patches rather than evenly scattered, reflecting plot-by-plot household conversion spreading outward.
- **FR-006**: `fraction` MUST be interpreted as a share of the ELIGIBLE (low/wet) plots, not of all plots - the economic term applied after the topographic filter.
- **FR-007**: `tea_fringe` MUST remain on the dry margin above the highest irrigation ditch - already topography-driven, unchanged in code by this feature.
- **FR-008**: A map using the `mulberry_dike_fishpond` field archetype MUST NOT also carry the `mulberry_fishpond` overlay; the landscape is drawn once.
- **FR-009**: Per-value grounding, including for the rejected values and the corrected tea-siting language, MUST be recorded in `settlements.md` and in the code where the rule lives.
- **FR-010**: Every existing pool map MUST still pass the `check_village` gate after regeneration.

### Key Entities

- **`land_use_overlay` knob** - its registered value space and typing rule.
- **The overlay driver** - the routine that selects and recolors plots.
- **Field plot** - carries a fill; the low/wet ones are marked flooded by the field builders.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of plot-based overlay plots (lotus and dike-pond alike) on any generated map coincide with low/wet plots; zero sit on ordinary rice ground.
- **SC-002**: Dike-pond overlays form patches - measurably more clustered than a uniform random sample of the same count over the same eligible plots.
- **SC-003**: No map carries both the `mulberry_dike_fishpond` archetype and the `mulberry_fishpond` overlay.
- **SC-004**: Every pool map passes `check_village`, and the suite stays at 100% line coverage.
- **SC-005**: A rendered map carrying each plot-based overlay, inspected as an image, shows the overlay confined to the wet bottom ground - the Principle XII closing bookend, verified on the artifact rather than the code.
- **SC-006**: Each surviving and each rejected overlay value has its governing variable recorded in prose.

## Assumptions

- The engine's flooded fill is a sound proxy for "low, permanently wet ground". CONFIRMED in Phase 0 (research.md D5): all four field builders mark it on the lowest ground their geometry defines.
- Changing which plots an overlay occupies is a visual and semantic change only; no check depends on placement beyond the existing "overlay was drawn" check.
- Shallow-water lotus (rotated with rice in ordinary paddy) is real but deliberately not modeled - see research.md D1 for the reasoning, recorded so a later pass does not "restore" it as random scatter.
