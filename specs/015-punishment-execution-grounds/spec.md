# Feature Specification: Punishment Spots and Execution Grounds

**Feature Branch**: `main` (session-clone workflow - see CLAUDE.md; features 002-014 committed to `main` inside the clone rather than to a feature branch)

**Created**: 2026-07-25

**Status**: Draft

**Input**: User description: "We should document these research findings and then update our maps to have our towns and cities have 'the punishment spot' in the middle of town, and then also have the execution grounds outside the walls (for walled settlements) away from the main settlements and also away from the normal countryside graveyards and such."

## Context

Rokugan's justice apparatus has never appeared on a settlement map. The research pass that preceded this spec established that there are **two** distinct installations, used at wildly different frequencies, sited by opposite logics, and that conflating them would be a modeling error:

- **The punishment spot** is in the middle of town, used constantly (stocks, flogging, public shaming), and is ordinary civic furniture.
- **The execution ground** is outside the settlement, used once every several years at county scale, and is ritually polluted ground that must stay away from the built area, from farmland, and from the community's own burial ground.

Both are new settlement vocabulary for Mode B maps. The research behind them (the China/Japan reconciliation, the size anchors, the volume math, the siting rules) must be recorded alongside the rules per the project's record-the-why requirement.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The execution ground reads correctly from the road (Priority: P1)

The GM opens a town or provincial-city render and can see where the Empire carries out death sentences: a bare, unbunded patch of waste ground outside the settlement, on the main road past the boundary marker, with its posts and disposal pit. It is unmistakably outside the settlement, unmistakably not farmland, and unmistakably not the community burial ground.

**Why this priority**: This is the headline request and the harder half. It introduces a feature whose entire meaning is *where it is not* - get the siting wrong and the map asserts something false about Rokugani pollution beliefs.

**Independent Test**: Add an execution ground to one town spec, regenerate, and confirm from the manifest that it sits outside the built edge, off all field polygons, beyond the boundary marker on the main road, and at a real separation from the burial ground. Delivers the GM a correct map even if the punishment spot never ships.

**Acceptance Scenarios**:

1. **Given** a walled settlement spec that declares an execution ground, **When** the map is generated, **Then** the ground lies entirely outside the wall polygon.
2. **Given** an unwalled town spec that declares an execution ground, **When** the map is generated, **Then** the ground lies outside the built-up area with clear separation from the outermost building.
3. **Given** a settlement that has both an execution ground and a burial ground, **When** the map is generated, **Then** the two do not overlap and are not adjacent.
4. **Given** an execution ground, **When** the map is generated, **Then** it does not overlap any field, paddy, house, street, or wall.
5. **Given** an execution ground placed on a settlement whose burakumin quarter is known, **When** the map is generated, **Then** the ground is on the same side of the settlement as that quarter and further out than it.
6. **Given** an execution ground, **When** the manifest is inspected, **Then** its footprint matches the tier size band for that settlement tier.

---

### User Story 2 - The punishment spot sits in the middle of town (Priority: P2)

The GM opens a town or provincial-city render and can see the everyday face of the magistrate's authority: a small public installation at the market or the magistracy frontage, in the built core, where townsfolk pass it daily.

**Why this priority**: Independently valuable and much simpler than the execution ground, but secondary because it is small civic furniture rather than a structural statement about the settlement's edges.

**Independent Test**: Add a punishment spot to one town spec, regenerate, and confirm from the manifest that it sits in the core, fronts a street, and occupies the expected frontage. Delivers value with no execution ground present.

**Acceptance Scenarios**:

1. **Given** a town spec that declares a punishment spot, **When** the map is generated, **Then** the spot lies inside the built-up area (inside the wall, for a walled settlement).
2. **Given** a punishment spot, **When** the map is generated, **Then** it fronts a street or the market space and does not overlap any building, street surface, or other feature.
3. **Given** a punishment spot, **When** the manifest is inspected, **Then** its frontage falls inside the specified size band.

---

### User Story 3 - The research survives the context window (Priority: P3)

A future session (or the GM months from now) opens the skill docs and finds why the execution ground is where it is, why the county one is a weedy patch rather than an installation, and where the size numbers came from - without redoing the research.

**Why this priority**: Mandatory by project rule and cheap, but it does not change a single pixel, so it ranks below the two map features it explains.

**Independent Test**: Read the historical-grounding section cold and answer: why is the ground outside the settlement, why does a county town have one at all when Japan's castle towns monopolized executions, and where does the ~60x60 ft figure come from. Delivers value with no code change.

**Acceptance Scenarios**:

1. **Given** the skill's grounding documentation, **When** a reader looks up the execution ground, **Then** they find the China/Japan reconciliation, the size anchors, the volume reasoning, and each siting rule paired with its reason.
2. **Given** a new validator check introduced by this feature, **When** a reader finds it in the code, **Then** a comment or the grounding section explains the number it enforces.

---

### Edge Cases

- **A settlement declares an execution ground but has no wall and no clearly-defined built edge.** The rule must degrade to a measured separation from the outermost building rather than silently passing.
- **A settlement declares an execution ground but no burial ground.** The separation check has nothing to compare against and must pass rather than error.
- **The main road exits the map before the boundary marker distance is reached.** The ground may sit at the map edge; it must not be pushed off-map or silently dropped.
- **A hamlet or village spec declares either feature.** This is a canon violation and must be rejected, not drawn.
- **The burakumin quarter is on the opposite side from the only usable road exit.** The two siting preferences conflict; the spec must state which one wins.
- **A settlement declares two execution grounds** (a great city with several road gates). This is legitimate at capital/great-city scale and must not be forbidden by a "at most one" assumption.

## Requirements *(mandatory)*

### Functional Requirements

**The punishment spot**

- **FR-001**: A settlement spec MUST be able to declare a punishment spot as a named feature with a position.
- **FR-002**: The punishment spot MUST render its constituent furniture: stocks, a flogging post, a kneeling stone, and a notice board.
- **FR-003**: The punishment spot MUST occupy 20-40 ft of street frontage.
- **FR-004**: The punishment spot MUST be sited inside the built-up area, at or beside the market space or the magistracy frontage, fronting a street.
- **FR-005**: The punishment spot MUST NOT overlap any building, street surface, wall, or other feature.

**The execution ground**

- **FR-006**: A settlement spec MUST be able to declare one or more execution grounds as named features with positions.
- **FR-007**: The execution ground MUST render as bare, unbunded ground, visually distinct from both farmland and built ground.
- **FR-008**: The execution ground MUST render its furniture: crucifixion post sockets, a burning stake, a beheading bed, a head-display stand with crime board oriented toward the road, a well, and a disposal pit.
- **FR-009**: The execution ground MUST be sized to the settlement tier: county town ~60x60 ft unfenced; provincial city ~100x60 ft screened on three sides with the road side open; domain capital ~150-250 ft along the road by 50-80 ft deep.
- **FR-010**: The execution ground MUST lie outside the wall for a walled settlement, and outside the built-up area for an unwalled one.
- **FR-011**: The execution ground MUST sit on or beside the settlement's main road, beyond the settlement boundary marker.
- **FR-012**: A settlement boundary marker MUST be renderable on the road between the settlement and the execution ground.
- **FR-013**: The execution ground MUST NOT overlap or sit adjacent to the community burial ground.
- **FR-014**: The execution ground MUST NOT overlap any field, paddy, house, street, wall, or other feature.
- **FR-015**: The execution ground SHOULD be placed on the same side of the settlement as the burakumin quarter and further out than it, where the settlement has one.
- **FR-016**: A memorial marker MAY be placed on the opposite side of the road from the execution ground.

**Tier gating**

- **FR-017**: Neither feature may appear on a hamlet or village map; a spec that declares one at those tiers MUST be rejected with a clear message.
- **FR-018**: Both features MUST be optional at town and provincial-city tier - an existing map that declares neither MUST continue to generate unchanged.

**Validation and regression**

- **FR-019**: Each siting rule above that can be violated MUST have a corresponding automated check.
- **FR-020**: Each new check MUST have a negative regression fixture recorded in the regressions pool, per the project convention that coverage alone does not prove a check has teeth.
- **FR-021**: The existing town, walled town, and provincial-city pool maps MUST be updated to carry both features and regenerated.

**Documentation**

- **FR-022**: The skill's historical-grounding documentation MUST record: the China/Japan reconciliation, the size anchors and what they scale from, the execution-volume reasoning, and every siting rule paired with its reason.
- **FR-023**: The new settlement vocabulary MUST be documented alongside the existing vocabulary so a future spec author can find it.
- **FR-024**: The setting-level findings MUST be written to `l7r.md` as a new sub-section under The Structure of Rokugani Government, following the file's style conventions, with only the new TOC entry inserted and every other TOC line untouched.

### Key Entities

- **Punishment spot**: An in-town public-shaming installation. Attributes: position, street frontage, constituent furniture. Belongs to the built core.
- **Execution ground**: An out-of-town execution site. Attributes: position, footprint, tier size band, screening, constituent furniture, disposal pit. Defined as much by its exclusions (wall, built edge, fields, burial ground) as by its contents.
- **Boundary marker**: A road-side stone marking where the settlement's clean ground ends. Sits between the settlement and the execution ground.
- **Burial ground**: Existing entity. Newly acquires a separation relationship with the execution ground.
- **Burakumin quarter**: Existing entity. Newly acquires a directional relationship with the execution ground.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every town, walled town, and provincial-city map in the pool carries both a punishment spot and an execution ground, and every one of them passes the full validator.
- **SC-002**: 100% of the new siting rules are enforced by an automated check, and every check has a negative fixture that fails without it.
- **SC-003**: Zero execution grounds in the pool overlap or sit adjacent to a burial ground, a field, a building, or a wall.
- **SC-004**: A reader who has never seen this feature can state, from the documentation alone, why the execution ground is outside the settlement and where its size comes from.
- **SC-005**: No hamlet or village map gains either feature, and all existing hamlet and village renders are byte-identical after the change.
- **SC-006**: The full skill gate (lint, types, tests, 100% coverage) passes.

## Assumptions

- **The domain-capital tier is documented but not exercised.** The pool has hamlets, villages, towns, provincial cities, and Mode A magistracies - there is no capital generator yet. Capital sizing is recorded so the number is ready when that tier arrives, but no capital map is produced by this feature.
- **"Adjacent" for the burial-ground separation is a measured minimum distance**, not merely non-overlap. The specific figure is an implementation decision to be fixed at plan time and justified in the grounding docs.
- **Where the burakumin-quarter direction (FR-015) conflicts with the road placement (FR-011), the road wins.** The road placement is the load-bearing rule - the ground exists to be seen by travelers - and the quarter preference is a tiebreaker among otherwise-valid road-side positions. This is why FR-015 is SHOULD and FR-011 is MUST.
- **Existing maps that predate this feature remain valid without it.** The features are opt-in per spec, so this change cannot break an unrelated map.
- **Labeling follows the existing don't-label-the-obvious rule.** Both features get labels (neither is self-evident from its shape), but their constituent furniture does not.
- **The two lore questions with no canon answer stay unanswered rather than invented**: which office confirms a heimin death sentence, and whether the Empire clusters executions into an annual season. Neither changes a map. The `l7r.md` section states the structure they imply (confirmation sits above the county magistrate) and leaves the ruling to the GM.

## Out of Scope

- Mode A compound plans. A magistracy's internal detention cell already exists and is unchanged; samurai executions happen inside walls by seppuku or a samurai's blade and are not this feature.
- Any capital-tier or great-city generator.
- Changes to the burial-ground or burakumin-quarter features themselves, beyond the new relationships with the execution ground.

## Resolved Decisions

- **Where the research gets written down (decided, not asked).** The findings split by audience, so they go to two places:
  - **Diagram-specific reasoning** (size anchors, why a county ground is a weedy patch, each siting rule and its check) goes in the skill's historical-grounding section, next to the checks it justifies. Covered by FR-022.
  - **Setting-level worldbuilding** (which settlement tiers have execution grounds, the jurisdiction chain that puts the confirming authority above the county magistrate, the volume math, the samurai/non-samurai split already implied by the canon that burakumin perform all non-samurai executions) goes to `l7r.md` as a new sub-section under The Structure of Rokugani Government, immediately after The Ministry of Justice, with a single surgical TOC insertion. This follows the canonical-home convention: `l7r.md` is the master record for setting material, and the skill docs reference rather than duplicate it. Covered by FR-024.
  - The two lore questions with no canon answer (which office confirms a heimin death sentence, and whether the Empire clusters executions into an annual season) are written into `l7r.md` as the *structure* they imply without inventing a ruling the GM has not made - the section states that confirmation sits above the county magistrate and leaves the exact office for the GM to fix.
