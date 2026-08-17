# Feature Specification: The placer tests the footprint it draws

**Feature Branch**: none - this project does not use feature branches (CLAUDE.md, GM 2026-07-27). `SPECIFY_FEATURE=121-placer-drawn-footprint`

**Created**: 2026-08-17

**Status**: Draft

**Input**: User description: make the settlement placer test the rotated footprint it actually DRAWS, retire the circumscribed-circle collision as a verdict, and re-derive the two hamletgen density constants that exist only to compensate for those two defects - all in one pool re-roll, before the village tier is built on top of them.

## Context

Two engine defects have been documented since 2026-08-08 as "CENTER vs FOOTPRINT" items 3 and 2. Both are *false negatives in seat availability*: the placer refuses ground that nothing occupies, and separately clears ground it then draws over. Both were deferred on a cost estimate - "it re-rolls Ikegami, Kuwabata, Tanada and Hoshigaoka, breaks Hoshigaoka's gate, and moves Tango by +21 houses" - that has since evaporated: every map that estimate named is now in `LEGACY_FROZEN_GENS` and is never regenerated or re-gated. The live Mode B pool is four scripted hamlets.

The reason to do this **before** the village tier, rather than after, is not merely that a village is denser. It is that the two constants the village generator will be calibrated against are documented in the source as inflated purely to compensate for these defects:

- `LANE_CLEARANCE = 48.0` - *"Until then this stays wide enough that the drawn steading clears the tread from any seat."*
- `BUNDLE_PITCH = 100.0` - *"the placer then keeps bundles apart by circumscribed circles rather than real footprints, so the effective pitch is larger again."*

Calibrate a village against compensation and the compensation has to come out of the village pool later, at village prices.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A drawn farmstead never stands on something it was cleared of (Priority: P1)

The GM opens a scripted hamlet and finds no farmhouse corner overhanging a lane, no steading laid across ground the placer promised was clear. Today the map only looks right because the generator asks for 48 px of lane clearance - far more than the rule requires - so the *drawn* steading stays off the lane by luck of the margin rather than by test. Drop that margin toward its honest value and half the cohort puts a house corner on a lane.

**Why this priority**: It is the correctness half, it is the prerequisite for Story 2 (the circle is what has been masking the rotation mismatch, so removing it first converts a documented inefficiency into shipped overlaps), and it is what makes the honest lane clearance in Story 3 safe to adopt.

**Independent Test**: Lower the generator's lane clearance to a value the current engine cannot survive, roll the cohort, and confirm the lane checks fail; apply the fix and confirm they pass at that same lowered value with no other check regressing.

**Acceptance Scenarios**:

1. **Given** a homestead bundle whose drawn house is offset from and scaled differently to the seed rect, **When** the placer evaluates that seat, **Then** it tests the rect that will be drawn - at its drawn size, drawn position and drawn rotation - not the seed rect.
2. **Given** a lane with a registered drawn tread, **When** a bundle is seated near it, **Then** the whole drawn footprint is tested against that tread, not merely the bundle's center point.
3. **Given** the generator asks for a lane clearance at which the current engine puts house corners on lanes, **When** the cohort is rolled after the fix, **Then** no map fails a lane-clearance check.

---

### User Story 2 - The placer stops refusing ground nothing is standing on (Priority: P2)

Seats are currently refused by a half-diagonal circle drawn around each placed feature. For a 46x28 house that reserves a 26.9 px radius against a true half-width of 23, forcing two such houses 57.8 px apart where true touching is 28. The last measurement attributed 38.7% of all refusals to that approximation alone, and removing it exposed 57.6% more legal seats. The visible symptoms are a capital that cannot seat a wellhead in two blocks that the well-density rule says need one, and a paddy that refuses a farmhouse at 6 of 10 tried positions.

**Why this priority**: It is the density half - large, measured, and blocking features rather than merely wasting ground - but it is only safe once Story 1 has the placer testing rotated footprints, because rotation-invariance is precisely what the circle has been providing.

**Independent Test**: Re-run the refusal-attribution measurement on the live cohort before and after; confirm approximation-only refusals fall to zero and the gate stays green.

**Acceptance Scenarios**:

1. **Given** two placed features that do not overlap in reality, **When** the placer measures them, **Then** it returns a verdict from their real rotated corner geometry, not from circumscribed radii.
2. **Given** the spatial index that finds collision candidates, **When** the verdict changes, **Then** the index keeps using a circumscribed extent - an over-stated extent can only admit a pair the exact test then rejects, which is the sanctioned prefilter role.
3. **Given** a rotated building (90/180 degrees, or a house at a few degrees of rake), **When** it is tested for collision, **Then** the test uses its rotated extent and not its placement-frame width and height.

---

### User Story 3 - The density constants say what is true, not what was survivable (Priority: P3)

`LANE_CLEARANCE` and `BUNDLE_PITCH` are both padded to absorb the two defects above. With the defects fixed, each is re-derived from what the geometry actually needs and the reasoning is recorded where the constant lives, so the village tier inherits honest numbers.

**Why this priority**: It is the payoff that motivates the ordering. Without it the feature banks the correctness fix and none of the density, and the village tier is still calibrated against compensation. It depends on both stories above.

**Independent Test**: Confirm each constant's new value is derived from a stated measurement rather than tuned until green, and that its source comment states what the number is, why, and that the old inflation is gone.

**Acceptance Scenarios**:

1. **Given** the placer now tests drawn footprints, **When** the lane clearance is re-derived, **Then** its value follows from the drawn steading's real reach plus the lane's half-tread, and the comment no longer describes it as a stand-in for an unfixed defect.
2. **Given** the collision verdict is now exact, **When** the bundle pitch is re-derived, **Then** its value follows from the bundle's real reserved extent and the sun corridor, with no allowance for circle inflation.
3. **Given** either constant changes, **When** the cohort is rolled, **Then** the pass rate does not fall below the recorded baseline.

---

### Edge Cases

- **A bundle sub-rect that is legitimately allowed to abut.** The grove may hug a paddy bund and adjacent groves may abut into one shared windbreak. Tightening the collision verdict must not turn a sanctioned abutment into a refusal.
- **Clearances vs surfaces.** A soft clearance (a caption band, a civic apron, a fence standoff) is slack that a footprint routinely overhangs by a few px; a road surface is not. The footprint test applies to surfaces; clearances keep their existing treatment. Conflating the two previously cost a well and pushed a punishment ground off its street.
- **Rotation where width and height swap.** Buildings drawn at 90/180 degrees have their placement-frame `w` and `h` exchanged; an axis-aligned test on placement dimensions is simply wrong for them, and this is the specific failure that made an earlier naive circle removal produce genuine overlaps.
- **A frozen map that would now fail.** Legacy maps are exhibits: their violations of post-freeze rules are expected and are not bugs. Nothing in this feature regenerates or re-gates one.
- **A seat that becomes legal only because of the fix.** More legal seats change packing, which changes what fits beside it - so every downstream feature (wells, gardens, groves, windbreaks) on a re-rolled map is in scope for review, not just the houses.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The homestead bundle placement path MUST evaluate each candidate seat against the rect that will be drawn - drawn size, drawn position, drawn rotation - rather than the seed rect it is derived from.
- **FR-002**: The bundle path MUST test a candidate's whole footprint against registered drawn road surfaces, matching the treatment the non-bundle path already applies, instead of testing only the candidate's center point.
- **FR-003**: Soft clearances MUST retain their present center-based treatment; only drawn surfaces gain the footprint test. The split MUST be stated in a comment at the point of the test.
- **FR-004**: Feature-to-feature collision MUST be decided from real rotated corner geometry rather than from circumscribed radii.
- **FR-005**: The spatial index that selects collision candidates MUST continue to use a circumscribed extent, and its role as a prefilter that prunes but never decides MUST be stated where it is used.
- **FR-006**: Sanctioned abutments (grove to bund, grove to neighboring grove) MUST remain legal after the collision verdict is tightened.
- **FR-007**: The generator's lane clearance and bundle pitch MUST be re-derived from measurement once FR-001 to FR-005 are in place, and each constant's comment MUST record what the number is, what it is derived from, and that its former inflation has been removed.
- **FR-008**: Every distance rule this feature touches or adds MUST be placed in the correct row of the project's centers/footprints doctrine table and MUST gain a ratchet entry, so no rule lives only in a document.
- **FR-009**: A measured baseline MUST be taken on unmodified code in a detached worktree before any change, covering the cohort pass rate, the per-seed failure histogram, and the full test bed.
- **FR-010**: The refusal-attribution measurement MUST be re-taken on the live scripted cohort. The historical figures were measured on a map that is now frozen and no longer regenerates, so they are no longer reproducible evidence.
- **FR-011**: Every live scripted map whose output moves MUST be regenerated and independently reviewed before the feature is considered done.
- **FR-012**: No frozen legacy map may be regenerated, re-gated, or "fixed" by this feature.
- **FR-013**: The stale reasoning recorded against these two defects MUST be corrected everywhere it appears, including the deferral rationale that named maps which are now frozen.

### Key Entities

- **Bundle geometry**: the metric layout of one homestead - house, threshing yard, dooryard garden, optional storehouse, optional windward grove - plus the bounding box that reserves them together.
- **Drawn footprint**: the rotated corner quad of a feature as the map actually renders it, as opposed to the axis-aligned placement rect it was seated from.
- **Drawn surface (tread)**: the rendered width of a way, registered alongside its softer corridor, against which a footprint must clear.
- **Collision reach**: the extent used to decide whether two features conflict - a prefilter extent for candidate selection, an exact extent for the verdict.
- **Live scripted map**: a pool map generated by a scripted engine, regenerated and gated by the sweep. Distinct from a frozen legacy exhibit.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At a lane clearance where the current engine puts a house corner on a lane on roughly half the cohort, the fixed engine puts one on none of them.
- **SC-002**: Refusals attributable to an approximation rather than to real occupancy fall to zero, measured by the same before/after method on the same live cohort.
- **SC-003**: The cohort pass rate does not fall below the recorded baseline, and every check that passed on a given seed at baseline still passes on that seed - or, where a re-roll makes per-seed comparison meaningless, every newly failing check is individually diagnosed.
- **SC-004**: Both density constants have values derived from a stated measurement, with the derivation recorded at the constant.
- **SC-005**: Every live scripted map that moves has been regenerated and has passed an independent review.
- **SC-006**: No documentation anywhere in the skill still defers this work on a cost that named frozen maps.

## Assumptions

- **The frozen pool genuinely removes the old blocker.** Verified against the classification list: the five maps every deferral cited are all frozen, and the live Mode B pool is exactly four scripted hamlets. The pool cost of this feature is those four plus one review each.
- **The ordering constraint survives the freeze.** The earlier trial in which removing the circle produced genuine overlaps was diagnosed as a rotation mismatch - an engine fact, not a pool-accounting fact - so it will reproduce on any live map with rotated buildings. Item 3 therefore precedes item 2 regardless of which maps are frozen.
- **The historical refusal figures are indicative, not a target.** They came from a map that no longer regenerates. They justify the work; the new measurement is what the feature is judged against.
- **No red gate exists today.** The lane defect is latent, paid for with roughly 16 px of clearance. The red state is manufactured by lowering the constant first, per the project's check-before-fix rule, rather than found.
- **Reviews are pre-authorized.** Settlement review of each moved map is a standing requirement of shipping a Mode B map, not an optional extra.
- **Village-tier work is out of scope.** This feature exists so the village tier starts from honest numbers; it does not begin that tier.
