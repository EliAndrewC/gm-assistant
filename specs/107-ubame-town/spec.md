# Feature Specification: Ubame County Town (border charcoal district)

**Feature Branch**: `main` (session-clone workflow - see CLAUDE.md; features 002-015 committed to `main` inside the clone rather than to a feature branch, so the mandatory `before_specify` git hook is superseded here)

**Created**: 2026-07-26

**Status**: Draft

**Input**: User description: "I'd like to create a new town to supplement Hoshizora and Hirameki, which will serve as a useful way to test our placement algorithms and automated checks on a fresh town. The town will be the county town of Ubame ... Please create this town, putting the magistracy at the border. This town has no walls, due to many centuries of peace with the Fox clan. The county magistrate's manor is at the eastern edge, as indicated in the notes."

## Context

Ubame is the easternmost of Moriguchi province's five counties in the Daika domain (Scorpion), and the county the road from the Kitsune Mori arrives in. `l7r.md` ("The Kurogi and the dynasty province of Moriguchi") establishes it as a working charcoal district in its own right - its own stands of ubame oak, its own kilns, and iron smelting that grew up around the fuel rather than the ore. The Mode A compound plan `pool/magistracies/ubame-magistracy.svg` already exists and fixes the geometry this map must agree with: the magistracy's east wall **is** the Fox/Scorpion border, it presents a ceremonial **south** face to the county town and a frontier **east** face, and a parley room is built into the border wall itself.

The pool currently holds two towns - Hoshizora (unwalled, Imperial road) and Hirameki (walled, no Imperial road). Ubame is deliberately the **third combination: unwalled with no Imperial road**, so the town gate's rules run over geometry no existing artifact has exercised.

### GM decisions already taken (not open for re-litigation)

| Decision | Value | Consequence |
|---|---|---|
| Walls | none | centuries of peace with the Fox; no rampart, gate, gate market, fire tower or drum tower |
| Magistracy | northeast corner, east wall on the border, `gate_dir="south"` | the town spreads south and southwest below it |
| Road | domain trunk road (the charcoal road) | **unlabeled** (only Imperial roads are labeled); no farrier |
| Land fall | mountains northeast, `down_deg=135` / `water_flow=135` | streams run NE -> SW; downstream is southwest |
| Kilns and smelting furnaces | off-map, in the hills | canon: charcoal is burned where the wood grows, and the furnaces went to the fuel |
| Clan | Scorpion | monasteries default to Benten and Jurojin |
| Town name | Ubame (姥目) | the county town takes the county's name |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A fresh county town that reads as a border charcoal district (Priority: P1)

The GM opens `pool/towns/ubame.png` and sees a county seat that could not be mistaken for Hoshizora or Hirameki: a magistracy standing on the clan border at the top-right, the charcoal road running west from it, a merchants' charcoal store on the trade approach, an iron refining forge out on the edge, and the land falling away southwest into paddy.

**Why this priority**: this is the artifact the GM asked for, and it is the integration test for everything else - every engine feature below only matters because this map uses it.

**Independent Test**: run `python3 pool/towns/ubame.gen.py` and then `python3 check_village.py pool/towns/ubame.json`; the gate reports ALL CHECKS PASSED and the render is legible.

**Acceptance Scenarios**:

1. **Given** the finished generator, **When** it is run, **Then** it writes `ubame.svg`, `ubame.png` and `ubame.json` and the validator passes every check.
2. **Given** the rendered map, **When** the magistracy is located, **Then** it stands at the northeast with its gate facing the town and its east wall on the drawn border line.
3. **Given** the manifest, **When** the road records are read, **Then** no road carries the label "Imperial Road" and no farrier is present.
4. **Given** the manifest, **When** the caste counts are summed, **Then** each non-farmer caste lands in its `budgets.md` band and farmhouses remain the largest single group.
5. **Given** the manifest, **When** the nuisance features are located, **Then** the burakumin quarter, the tanning yard and the execution ground all lie on the downstream (southwest) side, and the execution ground is past the boundary marker on the road out - not at the frontier crossing.

---

### User Story 2 - A charcoal store any fuel town can draw (Priority: P2)

A future map of any charcoal or firewood district calls one method and gets a correctly-sited merchants' charcoal yard, with the dryness and fire-gap rules enforced rather than remembered.

**Why this priority**: it is the trade that defines Ubame, and the reusable half of the work. Without it the town's own economy is invisible on its own map.

**Independent Test**: call the method on a synthetic manifest; the yard records its own manifest key, is gated off every keep-clear hazard by registry membership alone, and a deliberately-broken fixture trips its own siting checks.

**Acceptance Scenarios**:

1. **Given** a charcoal yard drawn anywhere on a map, **When** the gate runs, **Then** it is refused any position overlapping a road, street, watercourse, wall, manor, religious hall or other structure, with no per-hazard wiring needed.
2. **Given** a charcoal yard placed inside the fire gap of another structure, **When** the gate runs, **Then** the fire-gap check fires and names both features.
3. **Given** a caption from another feature dropped across the yard, **When** the gate runs, **Then** the label check fires.

---

### User Story 3 - A refining forge for any iron district (Priority: P3)

A future map of an iron county calls one method and gets the downstream half of the tatara system - the forge that turns hill-smelted iron into bar - sited off the housing where its smoke and fire belong.

**Why this priority**: it completes the county's declared economy (iron smelted where the charcoal already was) and generalizes to Tatarano and any other iron district in the domain.

**Independent Test**: same shape as US2 - synthetic placement, registry-driven hazard coverage, a negative fixture per new siting rule.

**Acceptance Scenarios**:

1. **Given** a refining forge placed among dwellings, **When** the gate runs, **Then** the standoff check fires.
2. **Given** a refining forge on a map, **When** the overlap battery runs, **Then** it is treated as a solid structure like any other premises.

---

### User Story 4 - A drawn clan border (Priority: P4)

Any frontier settlement can draw the jurisdictional line it sits on, labeled, without the line behaving like a physical obstacle.

**Why this priority**: lowest cost and lowest risk, but without it Ubame's central fact - that this town's east edge is where the Empire's Scorpion ends and its Fox begins - is only in the notes and not on the sheet.

**Independent Test**: a border line drawn under a compound wall passes the gate; the manifest key is classified as overlap-exempt with its reason recorded.

**Acceptance Scenarios**:

1. **Given** a border line running beneath the magistracy's east wall, **When** the gate runs, **Then** no overlap check fires, because a line of law is not a physical object.
2. **Given** any new manifest key, **When** the gate runs, **Then** the classification checks force it to be either registered or exempted with a reason - the border line included.

### Edge Cases

- **The magistracy at the frame edge.** The compound must sit at the northeast corner with the border line running off both the top and bottom of the frame; `crop_to_content` clamps to the canvas, so the compound, its label, and the border's tails must all be authored inside the canvas or the crop cannot frame them.
- **The execution ground versus the frontier.** `execution_ground_on_the_outcast_side` and `execution_ground_by_the_road` could both be satisfied on the *east* road, which is the road the Fox delegation arrives by. The siting must resolve to the west road out; if the automated rules alone would permit the east siting, that is a judgment the notes must record rather than a check to loosen.
- **Charcoal versus the tanning yard.** Both want marginal edge ground and the tannery must be below every intake. The charcoal store is a *dry, valuable* good on the trade approach and the tannery a wet nuisance downstream; they must not be allowed to compete for the same pocket.
- **A fire gap that cannot be met.** If the packed town leaves no seat with the charcoal yard's fire gap, the correct answer is to move the yard to genuinely open ground, not to shrink the gap.
- **No walls means no wall-scoped features.** Every check scoped to `meta.walled` must simply not run; a check that silently never runs looks exactly like a check that passes, so the absence must be deliberate rather than accidental.
- **Two monasteries, one theater stage.** The stage must sit adjacent to a hall and open toward it; with two halls the choice of which is a siting decision that must be made, not defaulted.

## Requirements *(mandatory)*

### Functional Requirements

**The map**

- **FR-001**: The system MUST produce a town-scale settlement map named Ubame at 1 ft/px, declared unwalled, with a Scorpion holding clan and a depicted population consistent with its drawn dwellings.
- **FR-002**: The map MUST place the magistrate's walled manor at the northeast, its gate facing the town it administers, and its east wall standing on the drawn clan border.
- **FR-003**: The map MUST carry a trunk road entering from the east at the border and running off the western frame, with no Imperial-road label anywhere and no farrier.
- **FR-004**: The map MUST declare a northeast-to-southwest land fall and drainage bearing, and every watercourse, drain and channel MUST run with it.
- **FR-005**: The map MUST place all castes at their documented town counts, with farmhouses the largest single group.
- **FR-006**: The map MUST carry the full standing town program: two monasteries, a theater stage adjacent to and opening toward one of them, a market-day flophouse, one caravan inn with stables and open ground beside them, a notice board on the road, a punishment ground on the traffic, an execution ground with its boundary marker on the road out, a graveyard, a cremation ground and an ossuary, communal wells reaching every dwelling, merchant storehouses, samurai housing by the manor, and a tanning yard on water below every intake.
- **FR-007**: The map MUST site the burakumin quarter, the tanning yard, the execution ground and its boundary marker on the downstream southwest side, and MUST NOT site the execution ground on the eastern frontier approach.
- **FR-008**: The map MUST carry water-first comb fields on the lower southwest ground with at least one field running off the frame edge, a communal windbreak on the northwest windward margin, and a stand of ubame oak on the northeast high ground.
- **FR-009**: The map MUST pass every check in the settlement validator with no suppressions, and MUST NOT declare any opt-out knob that exists only to make a check pass.

**The charcoal yard**

- **FR-010**: The system MUST provide a charcoal-yard feature drawn as roofed stacking sheds holding baled charcoal, a weighing floor, and cart standing, recorded under its own manifest key.
- **FR-011**: The charcoal yard MUST be classified in the overlap registry and given a caption group, so it is gated off every keep-clear hazard and protected from foreign captions without per-hazard wiring.
- **FR-012**: The system MUST enforce a minimum clearance between a charcoal yard and every other structure, because charcoal fines self-heat, and MUST record the reasoning beside the rule.
- **FR-013**: The charcoal yard's stock MUST be drawn under cover rather than as open ground, because the county's premium good is bought for a dry, odorless burn.

**The refining forge**

- **FR-014**: The system MUST provide a refining-forge feature drawn as an open-sided hammer floor with a charcoal shed, quench trough and slag heap, recorded under its own manifest key and classified in both registries.
- **FR-015**: The system MUST enforce a standoff between a refining forge and dwellings, and MUST record the smoke, noise and fire reasoning beside the rule.
- **FR-016**: The system MUST record the research establishing that smelting happens at the fuel in the hills while refining happens in the valley settlement, so the off-map/on-map split is defensible rather than assumed.

**The clan border**

- **FR-017**: The system MUST provide a drawn jurisdictional border line with a label, recorded under its own manifest key.
- **FR-018**: The border line MUST be classified as overlap-exempt with its reason recorded, because a compound wall standing on the line is the intended arrangement rather than a defect.

**Process obligations**

- **FR-019**: Every new siting rule MUST ship with a negative fixture that trips it, saved into the regression corpus, and MUST be verified to fire red before the artifact is fixed.
- **FR-020**: Every new rule's historical or setting reasoning MUST be recorded in the topic file that carries the rule, not only in the code.
- **FR-021**: The full skill gate MUST pass, including the whole-pool regeneration sweep and the 100% coverage floor, proving no existing map regressed.

### Key Entities

- **Charcoal yard**: a merchants' fuel store. Attributes: position, rotation, footprint, caption, shed count. Relationships: sits near the trade road and the magistracy's tally; keeps a fire gap from every structure.
- **Refining forge**: an iron-working premises. Attributes: position, rotation, footprint, caption. Relationships: stands off the dwellings; receives from off-map hill furnaces.
- **Border line**: a jurisdictional polyline. Attributes: point list, label. Relationships: the magistracy's east wall stands on it; it obstructs nothing.
- **Ubame map manifest**: the machine-checkable record of everything drawn, consumed by the validator.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The Ubame map passes every validator check with zero failures and zero opt-out knobs added for the purpose.
- **SC-002**: The full skill test suite passes, including the regeneration of every existing pool map, with no existing map's verdict changed.
- **SC-003**: Line coverage over the validator and the settlement library remains at 100%.
- **SC-004**: Each of the three new features is refused placement on every keep-clear hazard by registry membership alone, demonstrated by the existing contract test naming the new keys.
- **SC-005**: Each new siting rule has at least one saved negative fixture on which it demonstrably fires, and each was observed red before the map was corrected.
- **SC-006**: A reader who knows only the two existing towns can tell Ubame apart from both at a glance - different wall state, different road status, different land fall, and a visible trade the others do not have.
- **SC-007**: Every new rule's reasoning is discoverable in the topic file that carries the rule, without reading the code.

## Assumptions

- The county town shares the county's name, Ubame, following the ordinary Rokugani pattern for a seat.
- The road east of the magistracy leads to the Kitsune Mori 15 miles away and the road west leads toward Shiro Daika; both leave the frame, and the forest itself is off-map.
- The prevailing cold wind is the default northwest winter monsoon, so the downwind edge for smoke-producing works is the southeast, while the downstream edge for water-fouling works is the southwest.
- Depicted population follows the existing town convention: the urban households are drawn in full at their documented counts while the farmer cohort is a sampled slice, with the rest implied by fields running off the frame.
- The existing Mode A magistracy sheet is authoritative for the compound's orientation and for the border's position; this map agrees with it rather than revising it.
- Iron ore, kilns, tatara furnaces and the charcoal-burners' camps are all off-map in the hills, consistent with canon, and are not drawn.
- Work happens in the session clone on `main`; the spec-kit git branch hook is superseded by the repository's session-clone workflow, as it was for features 002-015.
