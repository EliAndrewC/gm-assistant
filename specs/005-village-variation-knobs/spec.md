# Feature Specification: Village Visual Variation Knobs

**Feature Branch**: `005-village-variation-knobs`

**Created**: 2026-07-12

**Status**: Draft

**Input**: User description: "Village visual variation knobs for the Mode B settlement generator. Goal: two villages - even with the same water-flow direction - should come out visually distinct enough that a viewer could tell them apart with the names removed, while staying to-scale and historically accurate (China-first, Japan corroborating). The variation must come from historically-grounded, tunable knobs that can be specified in advance OR randomly rolled from a seed - not just RNG jitter within one fixed template."

## Context & Problem

The Mode B settlement generator currently produces village maps from one implicit template. Two villages built with the same water-flow direction (`down_deg`) come out nearly identical: the current pool proves this - Kikuta is a near-copy of Hoshigaoka down to the position of the headman's house, differing only in the shrine. The seed only jitters placement *within* a frozen layout; the layout itself (cluster position and shape, internal lane skeleton, headman/shrine placement, water-source position, plot texture, focal features) is hardcoded per map.

Historical reality (China-first, Song/Ming rice south; Japan corroborating): within one region and terrain type, wet-rice villages genuinely rhymed - but real variation lived on four axes the generator currently collapses to a single value each: (1) terrain/field archetype, (2) settlement form, (3) focal & incidental features, (4) crop/land-use overlay. Recovering that variation as historically-typed, tunable knobs is the goal - villages that read as distinct *places* while remaining exactly as to-scale and historically accurate as they are today.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Same water direction, still visually distinct (Priority: P1)

As the GM generating village maps, I can create two villages that share the same water-flow direction and have them come out visually distinct enough that I (or a player) could tell them apart with the names removed - without hand-authoring each one as a bespoke layout.

**Why this priority**: This is the core complaint and the minimum viable outcome. It directly kills the Kikuta/Hoshigaoka twinning. It is achievable with "within-archetype" knobs (cluster geometry, internal layout, water placement, plot texture, focal-feature set) that vary the layout the seed currently only jitters within - the cheapest, highest-leverage slice.

**Independent Test**: Generate two nucleated broad-valley villages with identical `down_deg` but different seeds/knob rolls; confirm they differ on multiple structural axes (cluster position/shape, headman/shrine placement, water-source position, focal features, plot grain) and that a blind reviewer reads them as different places. Regenerate the existing pool so Kikuta and Hoshigaoka no longer twin.

**Acceptance Scenarios**:

1. **Given** two village specs with the same `down_deg` and different seeds, **When** each is generated, **Then** their cluster centroids sit in different regions of the frame, their headman houses are in different positions relative to the cluster, and their focal-feature sets differ.
2. **Given** the current pool, **When** Kikuta and Hoshigaoka are regenerated with the variation knobs applied, **Then** they no longer share cluster position, headman position, and focal features, and both still pass the `check_village` gate.
3. **Given** a village spec that pins specific knob values (cluster position, lane skeleton, water source, focal features), **When** it is generated, **Then** the map honors every pinned value and is deterministic across regenerations.

---

### User Story 2 - Roll a distinct village from a seed (Priority: P2)

As the GM who wants a village quickly, I can supply only a seed and a small number of geographic facts (scale, water direction, water-source kind, region/terrain type) and get a distinct, historically-coherent village, with the generator rolling the unspecified knobs from the seed.

**Why this priority**: Delivers the "randomly selected during generation" half of the goal and makes bulk village generation practical. Depends on the knob machinery from P1 existing first.

**Independent Test**: Generate several villages from the same minimal facts but different seeds; confirm each rolls a different but internally-coherent combination of knobs, all passing the gate, none reading as a copy of another.

**Acceptance Scenarios**:

1. **Given** a minimal spec (seed + scale + water direction + water-source kind), **When** generated, **Then** the generator rolls the remaining knobs deterministically from the seed and produces a passing map.
2. **Given** two minimal specs differing only in seed, **When** both are generated, **Then** they roll different knob combinations and read as different places.
3. **Given** a stated region/terrain that is incompatible with a knob value (e.g. a mulberry-fishpond overlay in a dry upland), **When** the roll happens, **Then** that value is excluded from the roll (historically-typed knobs respect the stated geography).

---

### User Story 3 - Pin any knob for a designed village (Priority: P2)

As the GM designing a specific village for the campaign, I can pin any individual knob (cluster shape, water-source position, a required focal feature such as an ancestral hall, the field archetype) while letting the rest roll or default, so a hand-designed village and a rolled village use the same machinery.

**Why this priority**: The "specified in advance" half of the goal. Ensures the knobs are a superset of today's hand-authoring, not a replacement that removes control.

**Acceptance Scenarios**:

1. **Given** a spec pinning one knob and leaving others unset, **When** generated, **Then** the pinned knob is honored exactly and the rest roll/default without contradicting it.
2. **Given** a spec pinning a combination that is historically valid, **When** generated, **Then** it produces a passing map; **Given** a combination that is historically incompatible, **Then** the generator refuses or warns rather than drawing an implausible map.

---

### User Story 4 - New terrain / settlement archetypes for dramatic variety (Priority: P3)

As the GM building out a varied region, I can select a whole terrain or settlement archetype beyond the broad-valley nucleated default - contour terraces, a diked polder grid, a ribbon valley, a mulberry-dike fish-pond mosaic; or a linear/dispersed/water-town settlement form - so that villages differ not just in arrangement but in kind.

**Why this priority**: The largest visual payoff but the largest build - each new field archetype needs its own generator, validator rules, and to-scale grounding. Sequenced after the within-archetype knobs prove the model. Delivered incrementally, one archetype at a time.

**Acceptance Scenarios**:

1. **Given** a spec selecting a non-default field archetype, **When** generated, **Then** the field geometry, irrigation, and settlement placement follow that archetype and the map passes a validator that includes archetype-specific rules.
2. **Given** any new archetype, **When** it is added, **Then** its historical grounding (why it looks the way it does, China-first) is recorded alongside its rules, per project policy.

---

### Edge Cases

- A pinned knob combination that cannot physically fit (e.g. a large focal complex plus a maximal cluster on a small frame): the generator must fail loudly or shrink gracefully, never silently overlap or clip.
- A roll that would place two focal features in the same spot, or a focal feature on the paddy/marsh/lane: excluded by the same placement invariants that already gate hand-authored features.
- A knob whose value has no historical grounding yet: must not ship until its grounding is researched and recorded (no un-grounded variety).
- Very small (hamlet) or very large (edge-of-town) settlements where a knob's assumptions break: knobs are scoped to the scales where they are historically meaningful.
- Regenerating an existing map after the knobs land: intended output change is acceptable (and desired for the twinned maps), but every map must still pass the gate.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The generator MUST expose the village layout as a set of named, individually-tunable knobs, where each knob can be (a) pinned to an explicit value in the village spec, or (b) left unset to be rolled deterministically from the map seed.
- **FR-002**: The Phase-1 ("same water direction still distinct") knob set MUST cover, at minimum: cluster position (which region/margin of the field the village sits on), cluster shape/aspect/orientation (round, elongated, crescent, or split into sub-clusters), the internal lane skeleton (chosen from a set of historically-real patterns), the headman house and primary shrine positions **derived from** the cluster and lane skeleton rather than hardcoded, the water-source position (pond corner/mid-margin/chain, or stream entry edge), plot texture (plot size and bund regularity) with a paddy-grain drift so the field is not a rigid uniform angle, and a rolled/pinned focal-feature set drawn from a historically-grounded catalogue.
- **FR-003**: Every knob value MUST be historically grounded (China-first, Japan corroborating), with its reasoning recorded in the settlement grounding docs before it ships - no un-grounded variety.
- **FR-004**: Knobs MUST be historically typed so that a roll respects a village's stated geography: a knob value incompatible with the stated region/terrain/water-source is excluded from the roll and rejected (or warned) if pinned.
- **FR-005**: Two villages sharing the same water-flow direction but different seeds MUST come out distinguishable on multiple structural axes (not merely jittered), such that a blind viewer reads them as different places.
- **FR-006**: Given only a minimal spec (seed + scale + water direction + water-source kind + optional region/terrain), the generator MUST produce a complete, gate-passing village by rolling the unspecified knobs from the seed.
- **FR-007**: Pinned knobs MUST be honored exactly and produce deterministic output across regenerations (same spec + same seed produces an identical map).
- **FR-008**: All six existing pool maps MUST continue to pass the `check_village` gate after the knobs land; the twinned maps (at minimum Kikuta vs Hoshigaoka) MUST be regenerated to no longer read as copies.
- **FR-009**: The focal-feature catalogue MUST include the historically-attested village foci: a fengshui crescent pond, an ancestral hall, a water-mouth complex (grove + bridge + pavilion), a mill/waterwheel, a market stand, and a secondary shrine - each placed by the same overlap/placement invariants that gate existing features.
- **FR-010**: Later-phase archetype knobs (field/terrain type, settlement form, land-use overlay) MUST each carry archetype-specific validator rules and to-scale grounding, and MUST be delivered incrementally (one archetype validated end-to-end before the next).
- **FR-011**: The variation MUST preserve to-scale realism: every knob value draws a real historical form at honest relative size; no knob may inflate or shrink a feature past its true relative magnitude to manufacture difference.
- **FR-012**: The generator MUST NOT silently produce implausible or overlapping layouts from any knob combination; an impossible combination fails loudly or resolves by shifting/shrinking within the existing placement rules.

### Key Entities

- **Knob**: a named degree of variation in a village's layout, with a value space, a historical-typing rule (which geographies/archetypes it is valid for), a default, and a deterministic roll from the seed. Examples: cluster-position, cluster-shape, lane-skeleton, water-source-position, plot-texture, focal-feature-set, field-archetype, settlement-form, land-use-overlay.
- **Village spec**: the per-map declaration (today the `.gen.py` plus its `meta`) that pins some knobs, states the geographic facts (scale, water direction, water-source kind, region/terrain), and supplies the seed. Unpinned knobs are rolled.
- **Focal feature**: an optional, historically-attested village element (crescent pond, ancestral hall, water-mouth complex, mill, market, secondary shrine) drawn from a catalogue and placed by existing overlap invariants.
- **Archetype**: a whole terrain/settlement type (broad-valley nucleated is the current default) that swaps the field-geometry generator, the settlement-placement logic, and adds archetype-specific validator rules.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For any two villages in the regenerated pool that share the same `down_deg`, they differ on at least 4 of these structural axes: cluster centroid region, cluster shape/aspect, headman position relative to the cluster, lane-skeleton type, water-source position, focal-feature set, paddy-grain orientation. (Today Kikuta and Hoshigaoka differ on ~1.)
- **SC-002**: A blind review of the regenerated pool (maps shown without names) yields correct "these are different villages" judgements - no two same-direction villages are mistaken for the same place.
- **SC-003**: All six existing pool maps pass the `check_village` gate after the change; the full test suite is green except for pre-existing failures owned by other work.
- **SC-004**: A village can be generated from a minimal spec (seed + scale + water direction + water-source kind) with zero hand-placed coordinates and still pass the gate.
- **SC-005**: Every shipped knob value has its historical grounding recorded in the settlement grounding docs (100% of shipped knob values, per the project's "record the why" policy).
- **SC-006**: Pinning a knob and regenerating twice yields byte-identical output (determinism), and pinning an incompatible value is rejected or warned rather than silently drawn.

## Assumptions

- The "user" is the GM authoring village maps via the Mode B generator; there is no external/end-user surface. "Visually distinct" is judged by a human looking at the rendered PNGs, supported by the structural-axis metric in SC-001.
- Re-varying the existing pool maps is in scope and desired: the twinned maps will be regenerated to look distinct. Byte-identical preservation of existing maps is explicitly NOT required for this feature (the intent is to change them), but every map must keep passing the gate.
- Phase 1 (within-archetype knobs) is the priority and the MVP; the archetype knobs (Phase 2+) are sequenced after and delivered one archetype at a time. This spec covers the whole effort; the plan and tasks may stage it.
- China-first governs undecided variation questions (Song/Ming rice south); Japanese forms corroborate and serve as tiebreakers; established GM/world canon overrides the historical default where they conflict.
- The knob machinery is a superset of today's hand-authoring: existing hand-placed villages remain expressible by pinning knobs, so no authoring capability is lost.
- Determinism is preserved: the roll is seeded, so a given spec plus seed always produces the same map (no wall-clock or nondeterministic entropy).
- Each new field archetype is a substantial build (new geometry generator plus validator rules plus grounding), not an afternoon tweak; the plan will treat archetypes as separate increments.
