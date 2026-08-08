# Feature Specification: The capital map skeleton and the castle

**Feature Branch**: none - this project stays on `main`. Active feature is carried by `export SPECIFY_FEATURE=019-capital-skeleton-castle`.

**Created**: 2026-08-08

**Status**: Draft

**Input**: The first DRAWN half of the domain-capital tier - the skeleton that feature 018's budget sizes, plus the castle - and the feature that renders Shiro Daika's first artifact.

## Context: the decisions are already made

Feature 018 shipped the capital space budget. Every rule this feature draws against was settled with the GM across 2026-08-08 and is recorded, with its historical basis, in:

- [`.claude/skills/diagram/settlements/capitals.md`](../../.claude/skills/diagram/settlements/capitals.md) - the tier's operational rules
- [`.claude/skills/diagram/research/cities/capitals.md`](../../.claude/skills/diagram/research/cities/capitals.md) - the findings and disclosed departures
- [`specs/018-capital-space-budget/research.md`](../018-capital-space-budget/research.md) - the Phase 0 findings this feature's closing gate must be judged against

**Read all three before planning. Do not re-litigate them.**

## Scope boundary *(read this first)*

The drawn capital is too large for one feature, exactly as the tier was. This one builds the **skeleton and the castle** and stops, so the castle - the tier's single biggest visual decision, and one the GM has explicitly marked provisional - can be judged off an early render rather than at the end of a long build.

**IN scope**: the tier wired far enough to run a gen; the castle as a drawn feature; a Shiro Daika gen producing wall, moat, river, roads, gates, ring road and castle; the checks governing exactly those; and the rendered PNG.

**OUT of scope, deferred to feature 020**: all housing (rank-graded samurai districts, walled yashiki, retainer terraces, commoner machi); the eight lineage compounds; the sovereign temples and teramachi rim; the wharf, domain granary, brokers' row and towpath; the aqueduct; the kido mesh; and the remainder of the capital check block.

**A skeleton map is expected to look empty inside.** That is the increment, not a defect - and it is precisely the condition under which the castle question can be judged on its own.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A domain capital renders at all (Priority: P1)

The GM asks for Shiro Daika and gets a map: a budget-sized wall with its moat, the river running through the landscape, the Imperial road and the two trunk roads leaving in the directions the domain actually lies, four gates, and the castle standing inside.

**Why this priority**: nothing else in the tier can be judged until something renders. This is also the first time the 018 budget's wall is drawn rather than computed, so it is the first real test of that model.

**Independent Test**: run the gen and open the PNG. It either produces a coherent walled place or it does not.

**Acceptance Scenarios**:

1. **Given** the Shiro Daika program, **When** the gen runs, **Then** it writes an SVG, a manifest and a PNG, and the wall drawn is the one the budget derived rather than a hand-picked figure.
2. **Given** the rendered map, **When** it is read at full size, **Then** its labels and features are as legible as a provincial city's - the tier's larger extent is absorbed by render width, not by shrinking the drawing.
3. **Given** the manifest, **When** the validator runs, **Then** every check that applies to a capital skeleton passes, including the budget-conformance checks feature 018 shipped.

---

### User Story 2 - The castle reads as a castle (Priority: P2)

The castle occupies roughly 85% of a provincial city's worth of ground and contains nothing that may be drawn. The GM needs to see whether that enclosure reads as a fortress or as an enormous empty box, and to decide whether its internal walls earn the sync cost they carry.

**Why this priority**: this is the question the feature exists to answer early. It is second only because it needs US1 to render first.

**Independent Test**: look at the castle on the render and answer one question - fortress, or empty box?

**Acceptance Scenarios**:

1. **Given** the castle is drawn, **When** the map is inspected, **Then** no building of any kind stands inside the enceinte - no keep, no palace, no store.
2. **Given** the provisional decision to draw internal walls, **When** the render is reviewed, **Then** a verdict is recorded in the tier doc either way, and if the walls stay, the constraint they place on the future castle plan is recorded with them.
3. **Given** the castle's main gate, **When** the map is inspected, **Then** it faces the ceremonial approach from the south, which is where the Imperial road enters.

---

### User Story 3 - The ways match the domain's real geography (Priority: P3)

Shiro Daika is a real place in the campaign with real neighbors. Its roads leave toward the places that are actually there.

**Why this priority**: cheap once the skeleton exists, and it is what stops the map being a generic capital with a name on it.

**Independent Test**: trace each way off the edge and check its bearing against the campaign map and the recorded road list.

**Acceptance Scenarios**:

1. **Given** the map, **When** the Imperial road is traced, **Then** it enters at the southern gate, runs north through the city, and leaves bending northwest.
2. **Given** the map, **When** the other trunk roads are traced, **Then** one leaves east and one leaves southwest, and neither is labeled as Imperial.
3. **Given** the river, **When** it is traced, **Then** it runs northeast to southwest and leaves the map at both ends, and no trunk road runs alongside it.

### Edge Cases

- **The interior is nearly empty at this increment.** Emptiness checks that assume a filled city must not fire on a deliberate skeleton, and must not be weakened to accommodate it - they should be scoped so they begin applying when the fabric lands.
- **The castle is an enormous keep-out.** Everything placed later must flow around it; the skeleton must reserve its ground rather than leave it to be discovered in feature 020.
- **A gate that no road reaches**, or a road that reaches no gate, is a defect at any tier.
- **The wall must not be hand-picked.** A gen that declares a budget and then draws a different wall must fail rather than render.
- **The render is roughly twice a provincial city's extent.** If legibility is preserved by shrinking rather than by rendering wider, the tier has silently broken the to-scale doctrine.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST support generating a settlement at the domain-capital tier end to end - declaration, drawing, manifest, validation and render.
- **FR-002**: The system MUST draw a castle as an enclosure of walls, moats and gates, taking its ground from the declared castle program rather than a drawn-to-fit shape.
- **FR-003**: The system MUST NOT place any building inside the castle enclosure, at any time, for any reason.
- **FR-004**: The system MUST draw the castle's internal divisions - its bailey walls, inner moats and angled gate approaches - as a provisional treatment that the feature explicitly evaluates before completion.
- **FR-005**: The castle's principal gate MUST face the ceremonial approach, on the side the Imperial road enters.
- **FR-006**: The system MUST reserve the castle's whole footprint against later placement, so the fabric added in the next feature flows around it.
- **FR-007**: The map MUST carry four gates, with the Imperial road running through the city between two of them and a trunk road leaving through each of the others.
- **FR-008**: The Imperial road MUST be the only way labeled as such; other trunk roads carry no name.
- **FR-009**: The river MUST run northeast to southwest, leave the map at both ends, and have no trunk road running alongside it.
- **FR-010**: The wall drawn MUST be the wall the space budget derived, and a map whose enclosure departs from its declared budget MUST fail validation.
- **FR-011**: The rendered image MUST preserve the legibility of the provincial tier by rendering at greater width, never by reducing the drawing scale.
- **FR-012**: Checks that assume a populated interior MUST NOT fire on a deliberate skeleton, and MUST NOT be weakened in order to achieve that - the scoping must be explicit about what is deferred.
- **FR-013**: The feature MUST record, in the tier documentation, the verdict on whether the castle's internal walls are kept.
- **FR-014**: The rendered artifact MUST be examined against the historical findings recorded for this tier before the feature is complete.
- **FR-015**: The map MUST pass an independent review before it ships.

### Key Entities

- **Castle**: a walled enclosure with moats, gates and internal divisions, whose interior is deliberately empty and whose ground is reserved against all later placement.
- **Way**: a road or river crossing the map, each with a bearing, a destination and a rule about whether it is named.
- **Gate**: an opening in the city wall where a way crosses it, with its furniture.
- **Skeleton map**: the increment itself - a complete, valid capital whose fabric is not yet drawn.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The GM can open a rendered Shiro Daika and see a walled capital with a castle in it.
- **SC-002**: Features on the capital render are as legible as the equivalent features on a provincial-city render.
- **SC-003**: No building appears inside the castle on the rendered map.
- **SC-004**: Every way leaves the map in the direction the campaign geography puts its destination.
- **SC-005**: The validator reports no failures for the capital.
- **SC-006**: A verdict on the castle's internal walls is recorded in the tier documentation, with its reasoning, whichever way it goes.
- **SC-007**: The rendered artifact has been checked against this tier's historical findings, and an independent review has been run on the map, with both outcomes recorded.
- **SC-008**: Every existing settlement in the pool still regenerates byte-identically.

## Assumptions

- **The recorded decisions are authoritative** - the castle's size and blankness, the road and gate layout, the ote facing south, the towpath rule, and the scale/render decision all come from `settlements/capitals.md` and are treated as settled input.
- **The bailey walls are provisional by the GM's explicit framing** ("we can remove them if needed"), so the feature is not complete until they are judged. A verdict of "remove" is a successful outcome, not a failure.
- **A skeleton looks empty and that is correct.** The deferred fabric is listed in the scope boundary; no check should be relaxed to make an empty interior pass.
- **Shiro Daika is a river city with a ring-seated castle**, per the tier doc's build order - the edge-seated castle remains unexercised until a later capital.
- **Principle XII's closing gate lands here.** It was transferred out of feature 018 because that feature rendered nothing; this is the feature that produces the artifact, so the obligation is discharged here.
- **The independent map review is pre-authorized** and is scoped to this feature's delta rather than a full audit, since the map is new but most of its vocabulary is not.
