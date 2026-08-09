# Feature Specification: The capital's ground-reserving layer

**Feature Branch**: none - this project stays on `main`. Active feature via `export SPECIFY_FEATURE=020-capital-ground-layer`.

**Created**: 2026-08-09

**Status**: Draft

**Input**: Every compound and public work that must be sited BEFORE housing, drawn onto the Shiro Daika skeleton.

## Context

Feature 018 shipped the capital space budget; feature 019 shipped the tier plumbing, the castle and the skeleton map, parked as a draft at `.claude/skills/diagram/wip/shiro-daika.gen.py`. Every decision this feature draws against is already settled and recorded in:

- [`.claude/skills/diagram/settlements/capitals.md`](../../.claude/skills/diagram/settlements/capitals.md)
- [`.claude/skills/diagram/research/cities/capitals.md`](../../.claude/skills/diagram/research/cities/capitals.md)
- [`.claude/skills/diagram/wip/README.md`](../../.claude/skills/diagram/wip/README.md) - including two defects feature 019's review found and deliberately deferred here

**Read all three before planning. Do not re-litigate them.**

## Scope boundary, and why it falls HERE

The split between this feature and the next is **forced by draw order, not chosen for convenience**. The skill's doctrine is that anything which must RESERVE ground has to run before the dense packs and register in a registry the placer actually honors. Civic compounds, temples, lineage estates and the waterfront all reserve ground; housing consumes what is left. Building housing first would mean re-packing it the moment this layer landed.

**IN scope**: everything that reserves ground - the government ward and its avenue, the Imperial Magistrate's compound, the Emperor's granaries, the eight lineage compounds, the sovereign temples and the teramachi rim, the wharf and its works, and the aqueduct. Plus the two carried-over defects.

**OUT of scope, deferred to feature 021**: all housing (rank-graded samurai districts, retainer terraces, commoner machi), public wells, fire towers, the kido mesh, the exact-population fill, and the remainder of the capital check block.

**The map will still not be green at the end of this feature.** It will still lack its declared population and the relay stables its farrier rule wants, so it stays a draft in `wip/` and moves into `pool/capitals/` only when 021 lands. That is the honest state, not a deferral of the problem: a map that is not green cannot live in the swept pool without turning `make done` red for every session.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The capital reads as a seat of government (Priority: P1)

The GM opens the map and can see where the domain is governed from: a ceremonial avenue running south from the castle's front to the Imperial road, the six domain ministries flanking it, the House Chancellery and the domain school on the same axis.

**Why this priority**: this is the axis the whole tier is composed around - the jokamachi rule that the main road passes the castle's front exists to make exactly this legible. Nothing else in the layer means much if the government quarter does not read.

**Independent Test**: open the render and trace the avenue from the castle gate to the Imperial road, counting the ministries along it.

**Acceptance Scenarios**:

1. **Given** the map, **When** the ceremonial avenue is traced, **Then** it runs from the castle's front gate to the through-road, with six ministry compounds fronting it.
2. **Given** the map, **When** the government compounds are inspected, **Then** each stands in its own ground rather than abutting a neighbor, and each is labeled with the office it houses.
3. **Given** the map, **When** the quarters are read, **Then** the civic zone is the ground the government actually occupies rather than a wedge chosen before the castle was placed.

---

### User Story 2 - The capital reads as a SPECIFIC domain's seat (Priority: P2)

The eight lineage compounds stand in the samurai ground, labeled with their families, at visibly different sizes - and the sizes track how many of each lineage actually live in the capital rather than the rank of its head.

**Why this priority**: this is what stops the map being a generic capital with a name on it. It is second only because it needs the government ward's ground settled first.

**Independent Test**: read the eight labels off the render and compare their footprints against the recorded household weights.

**Acceptance Scenarios**:

1. **Given** the map, **When** the lineage compounds are measured, **Then** four grand chancellery estates, one smaller chancellor's estate and three modest houses are distinguishable by size.
2. **Given** the map, **When** the ruling lineage is looked for, **Then** it has no separate compound, because its seat is the castle.
3. **Given** the provincial-seated chancellor's estate, **When** it is compared to the other chancellors', **Then** it is visibly smaller - a full chancellor whose people live in his province.

---

### User Story 3 - The waterfront and the water supply read as working infrastructure (Priority: P3)

The river bank carries a wharf with its dock and jetties, the domain granary behind it, a merchants' row in front, and a towpath running to the wharf. Separately, an aqueduct brings water from the river to a city gate.

**Why this priority**: it is the layer's biggest single block of new vocabulary and the least entangled with the rest, so it can land last without blocking anything.

**Independent Test**: trace the water: the river to the intake, the intake to the gate; and the river to the wharf, the wharf to the granary.

**Acceptance Scenarios**:

1. **Given** the map, **When** the riverside is inspected, **Then** a towpath runs along the wharf's own bank to the wharf and no further, and it is visibly not a road.
2. **Given** the map, **When** the aqueduct is traced, **Then** it is an open channel outside the wall ending at a gate, with no arcade anywhere and no open channel threading the interior.
3. **Given** the map, **When** the domain's grain is looked for, **Then** it is at the wharf, and the castle's own stores are not drawn at all.

### Edge Cases

- **The interior is still mostly empty**, since housing is deferred. Checks that assume a populated interior must not fire, and must not be weakened to achieve that.
- **A compound placed where housing will later go** must reserve its ground in a registry the packer honors, or feature 021 will build on top of it.
- **A new drawn feature that is recorded in the wrong SHAPE** silently escapes every keep-clear guardrail at once - the failure feature 019 hit. Every new record is a list.
- **A way crossing water without a bridge** must be caught - including on roads, rivers and castle moats, all three of which are currently invisible to both the drawer and the checker.
- **The castle's siege stores must not appear at the wharf, and the wharf's working rice must not appear in the castle.** The domain's grain is in two places for two reasons.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST draw a ceremonial avenue from the castle's front gate to the through-road, and MUST site the six domain ministries fronting it.
- **FR-002**: The system MUST draw the House Chancellery and the domain school on the same government axis.
- **FR-003**: Each government compound MUST stand clear of its neighbors rather than abutting them, and MUST be labeled with the office it houses.
- **FR-004**: The system MUST draw the Imperial Magistrate's compound so that it reads as foreign sovereign ground rather than as another domain office.
- **FR-005**: The system MUST site the Emperor's granaries according to the declared seat knob, and MUST keep them separate from the domain's own stores.
- **FR-006**: The system MUST draw eight labeled lineage compounds at sizes tracking the recorded household weights, in four visibly distinct bands, and MUST NOT give the ruling lineage a compound of its own.
- **FR-007**: The system MUST draw two sovereign temples dedicated to the holding clan's patron fortunes, and MUST belt the remaining temples along the inner face of the rampart rather than gathering them in one quarter.
- **FR-008**: The system MUST draw a wharf on the river with its dock, jetties and quay frontage, the domain granary behind it, and a merchants' row in front.
- **FR-009**: The system MUST draw a towpath on the wharf's own bank, visually distinct from a road, terminating at the wharf; and MUST NOT draw any road running alongside the river.
- **FR-010**: The system MUST draw an aqueduct as an open channel outside the wall terminating at a gate, MUST NOT draw an arcade, and MUST NOT draw an open channel through the walled interior.
- **FR-011**: Every feature this layer adds MUST reserve its ground against later placement, in the registry the packer honors.
- **FR-012**: Every feature this layer adds MUST be classified for overlap, given a caption group, and classified as roofed or open-air ground - and MUST be recorded as a list of records so those classifications can see it.
- **FR-013**: The system MUST bridge every way that crosses water, including ordinary roads, the river, and the castle's moat, and the check that verifies this MUST read the same complete sets - so that agreement between them is not achieved by both being blind.
- **FR-014**: The declared quarters MUST reflect where the government actually stands.
- **FR-015**: Checks that assume a populated interior MUST NOT fire on this still-unpopulated map, and MUST NOT be weakened to achieve that; what is deferred MUST be stated.
- **FR-016**: Every existing settlement MUST remain byte-identical.
- **FR-017**: The rendered artifact MUST be examined against this tier's recorded historical findings, and independently reviewed, before the feature is complete.

### Key Entities

- **Government ward**: the ceremonial avenue plus the compounds fronting it - ministries, chancellery, school.
- **Lineage compound**: a labeled walled estate whose footprint tracks the households it houses.
- **Sovereign temple**: the head house of a domain-wide religious order, distinct from an ordinary precinct.
- **Wharf works**: dock, jetties, quay, granary, brokers' row and towpath - one functional chain from river to store.
- **Aqueduct**: intake, open approach channel, and a gate terminus; buried beyond it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reader can trace the government axis from the castle gate to the through-road and count six ministries on it.
- **SC-002**: A reader can name all eight lineages from the map, and rank them into the four size bands without measuring.
- **SC-003**: The domain's grain appears at the wharf and nowhere else on the map.
- **SC-004**: No road runs alongside the river, and the towpath is distinguishable from a road at a glance.
- **SC-005**: No arcade appears anywhere, and no open watercourse threads the walled interior.
- **SC-006**: Every way-over-water crossing on the map carries a bridge.
- **SC-007**: Every feature added is governed by the keep-clear contract - none is invisible to it.
- **SC-008**: Every existing settlement regenerates byte-identically.
- **SC-009**: The rendered artifact has been checked against the tier's historical findings and independently reviewed, with both outcomes recorded.

## Assumptions

- **The recorded decisions are authoritative**: the ministries' siting outside the castle, the blank-castle doctrine, the towpath-not-road finding, the aqueduct's open-outside/buried-inside form, the lineage weights and the two-places-for-grain rule all come from the tier docs and are settled input.
- **Shiro Daika declares its Imperial granaries at the wharf**, exercising that knob rather than the magistrate-adjacent alternative.
- **The holding clan is Scorpion**, so the sovereign temples are Benten and Jurojin.
- **The map remains a draft.** Ending this feature not-green is the expected outcome, not a failure; the population check cannot pass until housing lands in 021.
- **The two carried-over defects are in scope** because both concern ground and water this layer draws on, and leaving a known-blind bridging check in place while adding more water crossings would compound it.
