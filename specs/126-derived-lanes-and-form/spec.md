# Feature Specification: Derived lanes, and settlement form as a rolled knob

**Feature**: 126-derived-lanes-and-form
**Created**: 2026-08-23
**Status**: Draft
**Input**: GM conversation 2026-08-23 - *"doesn't it make more sense to put the houses there first and then where there are naturally lanes where people would walk, we can put those there ... I think that putting the lanes down and then building up houses around it not only fails to reflect the way that these lanes develop in the first place, which is to say organically, but it also is probably causing more algorithmic problems for our placement."*

## Why this exists

A scripted hamlet currently lays its internal lane skeleton **before** it places any house, and then
seats the houses by fronting those lanes. Two things are wrong with that, one historical and one
measured.

**Historically it inverts how an accretive settlement forms.** A lane between farmsteads is trodden
by the households that already live there; it is the residual gap between two plots, not a corridor
set aside in advance. The project already reached this conclusion once, in writing, when the lane
*web* was moved to run after the houses: *"an alley IS the residual gap between two plots,
'colonized as semi-private space by the adjoining house', not a corridor set aside in advance."* The
skeleton is the remaining half that still runs first.

**Measurably it costs geometry.** When the web was laid before the houses, the four pool clusters'
long axes grew 51%, 58%, 15% and 97% - sprawl that no check measures - because a lane laid before
the houses must reserve its ground from a cluster that has not been packed yet, and so competes with
the very houses it exists to serve. The skeleton is sized on the seat band while the houses spread
wider than that band, which is why it cannot be guaranteed to reach them. That mismatch is the root
of the `farmhouses_reach_a_way` defect that survived seventeen recorded attempts.

Separately, every hamlet this generator produces is **nucleated**, because the tier hardcodes it.
The research supports at least two other forms, and the project's own doctrine (Principle XII) says a
genuinely two-formed finding becomes a seeded knob rather than a choice - the point being that
players must be able to tell one settlement from another at a glance.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Lanes that follow the houses (Priority: P1)

As the GM reading a hamlet map, I want the internal lanes to look like tracks worn between
farmsteads that already stood there, so the map reads as a place that grew rather than a place that
was surveyed.

**Why this priority**: It is the motivating defect, it is the half of the ordering that is still
backwards, and every other item in this feature sits on top of it.

**Independent test**: Roll the 48-seed cohort. Internal lanes are positioned from the final house
positions; no house position is influenced by an internal lane. The cluster's long axis does not
grow relative to the pre-change baseline.

**Acceptance scenarios**:

1. **Given** a hamlet whose houses have been placed, **When** the internal skeleton is drawn,
   **Then** its geometry is a function of the drawn house positions.
2. **Given** the same seed before and after the change, **When** both are rolled, **Then** the
   cluster's long axis is no longer than the baseline's, for every seed in the cohort.
3. **Given** any hamlet, **When** the connector to the off-map road is drawn, **Then** it is still
   laid before the houses, because the road it joins genuinely predates the settlement.

### User Story 2 - Hamlets that differ in form (Priority: P2)

As the GM, I want two hamlets rolled from different seeds to be recognizably different KINDS of
settlement, not the same settlement with different dimensions.

**Why this priority**: It is the project's stated goal for these maps and it is what the research
licenses, but it depends on US1 - a dispersed hamlet cannot be built while houses are seated by
lanes that must exist first.

**Independent test**: Across the cohort, more than one settlement form appears, each form is
visually distinguishable, and each is individually correct against the gate.

**Acceptance scenarios**:

1. **Given** a cohort of 48 seeds, **When** all are rolled, **Then** at least three distinct
   settlement forms occur, and no single form takes more than 70% of the cohort.
2. **Given** a hamlet rolled as dispersed, **When** its map is drawn, **Then** it has no internal
   lane network - only the connector leaving the map - and each farmstead sits in its own grove.
3. **Given** a hamlet rolled as linear, **When** its map is drawn, **Then** its houses are strung
   along the connector.
4. **Given** any seed, **When** it is rolled twice, **Then** it produces the same form both times.

### User Story 3 - Density set by the sun, not by a scalar (Priority: P3)

As the GM, I want farmsteads packed close together where they would actually want to be, with the
spacing decided by whether a neighbor's roof shades a drying yard rather than by one uniform number
applied in every direction.

**Why this priority**: A genuine improvement in both realism and density, and the constant's own
comment already names it as the unimplemented next step - but the map is correct without it, so it
ranks below the two structural changes.

**Independent test**: Farmsteads may sit closer together on the axis where no shadow falls, and no
drying yard is shaded by a neighboring farmhouse at the reference hour.

**Acceptance scenarios**:

1. **Given** two farmsteads side by side on an east-west line, **When** they are placed, **Then**
   they may sit closer than the uniform pitch, because neither casts a shadow on the other's yard.
2. **Given** a farmstead north of another, **When** it is placed, **Then** it stands far enough away
   that its roof does not shade the southern neighbor's drying yard at the reference hour.
3. **Given** any hamlet, **When** it is drawn, **Then** no threshing yard lies in a neighboring
   farmhouse's shadow.

### Edge Cases

- A dispersed hamlet has no internal lanes, so any rule requiring every farmhouse to be reached by a
  way must not be applied to it. Applying the nucleated premise universally would fail a correct map.
- A linear hamlet's houses front the connector, which means the connector is load-bearing for
  placement in that form and merely an exit in the others.
- A form may turn out to be unbuildable on a particular site (for example, a margin too short to
  string a linear settlement along). The generator must fall back to a buildable form rather than
  emit a broken map, and must say which form it actually used.
- With houses no longer seated against a lane, the seat generator loses its organizing structure and
  must seat against the field margin instead. A site whose margin is too small must still produce a
  legible cluster.
- Reducing spacing on the unshaded axis must not let a house intersect a neighbor's yard, garden,
  byre or grove.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Internal lanes MUST be positioned from the final positions of the houses they serve.
- **FR-002**: House placement MUST NOT depend on the position of any internal lane.
- **FR-003**: ~~Ways that genuinely predate the settlement - the connector to the off-map road, and
  the spur to the field - MUST still be laid before the houses.~~
  **SUPERSEDED IN FULL by [feature 128](../128-all-lanes-derived/spec.md) (2026-08-24). DO NOT
  IMPLEMENT THIS.**

  This requirement was never asked for. The GM's request was "put the houses there first"; the
  carve-out was written by the implementing session on a provenance argument, and it kept two lanes
  reserving ground before any house was seated - which is the exact defect the feature existed to
  remove. The GM found it five days later by reading the walk-through page: *"you are still putting
  lanes down before the farmhouses."*

  Two things are worth carrying rather than just the reversal:

  - **The provenance argument was the wrong axis entirely.** A road CAN predate a settlement, so an
    argument for drawing it first is always available - which is why resting on provenance preserved
    the exception instead of examining it. The reason that decides is ground reservation: a lane
    drawn before the houses takes ground they cannot then have, whatever the lane represents.
  - **The rule is now settled and is not reopenable by research** (GM 2026-08-24): *"the spec should
    absolutely pre decide. that the connector must be drawn after all of the houses. I cannot
    emphasize enough that that is explicitly what I have repeatedly asked for."*
- **FR-004**: The generator MUST record, on each map, which ways were exogenous and which were
  derived, so a reader can tell the two apart without reading the code.
- **FR-005**: Each hamlet's settlement form MUST be rolled from the map's own seed, and MUST be
  reproducible for that seed.
- **FR-006**: The generator MUST support at least the nucleated, dispersed and linear forms.
- **FR-007**: A nucleated hamlet MUST guarantee that every farmhouse is reached by a way, which the
  research establishes as decisive for that form.
- **FR-008**: A dispersed hamlet MUST have no internal lane network, and each farmstead MUST have
  its own shelter grove.
- **FR-009**: Rules that encode the nucleated premise MUST apply only to the forms they are true of,
  and MUST state which forms those are.
- **FR-010**: The declared form MUST be recorded on the map's metadata and MUST match what was drawn.
- **FR-011**: Farmstead spacing MUST be decided by whether a neighboring roof shades a drying yard,
  evaluated directionally, rather than by a single distance applied in all directions.
- **FR-012**: No drying yard may stand in a neighboring farmhouse's shadow at the reference hour.
- **FR-013**: Where no shadow falls, farmsteads MUST be permitted to sit closer together than the
  current uniform spacing.
- **FR-014**: The historical basis for each form, and for the shadow rule, MUST be recorded in the
  skill's durable research record, not only in this feature's artifacts.
- **FR-015**: Every re-rolled pool map MUST pass an independent settlement review before it ships.

### Key Entities

- **Way provenance**: whether a way predates the settlement (exogenous - the connector, the field
  spur) or was worn by it (endogenous - the internal skeleton and the lane web). Determines when the
  way is placed relative to the houses.
- **Settlement form**: the kind of settlement a map is - nucleated, dispersed or linear. Rolled per
  map from the seed. Determines whether an internal lane network exists at all, how houses relate to
  the connector, and which access rules apply.
- **Shadow corridor**: the ground north of a drying yard that a neighboring roof must not occupy,
  derived from roof height, latitude and the reference date and hour.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: No seed in the 48-seed cohort has a longer cluster long axis than it did before the
  change.
- **SC-002**: The cohort pass rate is at least the pre-change baseline. No check that passed on a
  seed before the change fails on it after, unless the seed's rolled form changed - in which case
  each newly-failing check is individually diagnosed.
- **SC-003**: At least three settlement forms appear across the 48-seed cohort, with no single form
  exceeding 70% of it.
- **SC-004**: Every seed produces an identical map when rolled twice.
- **SC-005**: Zero drying yards stand in a neighboring farmhouse's shadow, across the whole cohort.
- **SC-006**: In at least one cohort map, two farmsteads stand closer together than the pre-change
  uniform spacing, demonstrating the directional rule delivers density rather than only cost.
- **SC-007**: A reader shown a dispersed, a linear and a nucleated map can tell which is which
  without being told - verified by independent settlement review rather than by the author.
- **SC-008**: The historical grounding for all three forms and for the shadow rule is present in the
  skill's research record and reachable from the rule it justifies.

## Assumptions

- **The 48-seed cohort is the test bed**, as it has been for the preceding features in this area.
- **The four live scripted hamlets** (inashiro, kashikawa, mizuguchi, sawada) are re-rolled by this
  change. The five maps in `LEGACY_FROZEN_GENS` are never regenerated and are out of scope.
- **`water_town` and `dike_top`**, the two remaining values of the existing form knob, are out of
  scope. They describe sites this tier does not currently generate; adding them is separate work.
- **Fallback over failure**: where a rolled form cannot be built on a given site, the generator
  substitutes a buildable form and records that it did so. A map that cannot be drawn is worse than
  a map drawn in a different form, and silence about the substitution is worse than either.
- **The reference hour for the shadow rule** stays the one the existing constant was derived from
  (38N, 10th month, 9am), so the new directional rule and the old scalar remain comparable.
- **Cohort re-roll changes which seeds fail.** Because a seed's form is now rolled, per-seed
  comparison is not always meaningful; where it breaks down, the pass RATE governs and every
  newly-failing check is diagnosed individually, per the project's regression rule.

## Out of scope

- The `water_town` and `dike_top` forms.
- Any change to the village, town, provincial-city or capital tiers.
- Regenerating or re-gating the frozen legacy maps.
- Changing what a lane looks like once drawn - this feature moves WHEN and WHENCE lanes are decided,
  not their rendering.
