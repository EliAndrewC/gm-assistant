# Feature Specification: Near-Ring Farmland Density (towns and provincial cities)

**Feature Branch**: `013-near-ring-farmland` (spec directory; work lands on `main` per the session-clone workflow)

**Created**: 2026-07-22

**Status**: Draft

**Input**: GM observation - "the farm density around towns and cities is a little sparse. Towns and cities often grew up around places with lots of fertile land, so I wonder whether these areas should be packed with farms instead of having the town/city and then a smattering of farms in the surrounding area."

## Context and Research Findings

This section is the durable record of the research that motivates the feature (per the CLAUDE.md "record the why" rule). The eventual implementation must carry this reasoning forward into `settlements.md` and code comments; it is captured here first so the plan and tasks inherit it.

### The problem, concretely

The current town and city maps (`pool/towns/hirameki.png`, `pool/provincial-cities/tango.png`) render as: the settlement core, then a thin scatter of farmhouses around a few discrete fan-shaped paddy clusters, then rough-grazing / cut-over **scrub commons** filling most of the remaining frame right up to the settlement edge. The `hinterland()` method in `settlement.py` treats denuded scrub/rough-grazing as the **dominant matrix** and drops paddy in as the exception. This reads as sparse: a town sitting in a mostly-empty landscape.

### Why the current model over-weights scrub in the near ring

The scrub-dominant model rests on a genuine China-first fact - south-China rice hills were stripped for fuel and timber over ~1,000 years, so the dominant cover *between valleys and far from settlement* is denuded scrub, not forest. That fact is correct. The error is one of **placement**: it is applied to the land immediately around the settlement, where it does not belong.

Three lines of evidence say the near ring should instead read as **packed farmland**:

1. **The setting's own land-use numbers are domain-wide averages, not local ones.** `budgets.md` ("Rice and arable-land math"): ~15% of Rokugan is arable, ~4% is rice-suitable (imperial-Chinese anchor), and of that only ~1/3 is active wet paddy in any given year; land is **labor-limited, not land-limited**, so every domain carries substantial fallow. But those figures average over 560 sq mi of mixed terrain per median domain - mountains, arid borderlands, frontier. They are the wrong number for the half-mile around a county seat.

2. **Site-selection bias.** Towns and cities grow at the best available spot - the alluvial basin, the river confluence, the fertile plain. The land immediately around a settlement is systematically **far above** the 4% domain average in rice-suitability. That fertile basin is *why the settlement is there*.

3. **The von Thünen intensity gradient.** Even in a labor-limited economy, land nearest the settlement is worked hardest, because the labor and transport cost of reaching a field rises with distance. Chinese wet-rice farmers preferred **intensifying existing fields** over extending the cultivated area. The labor-limited fallow therefore accumulates at the **far margins and on the poorer soils** of the catchment, not in the near ring. (South-China landscapes show exactly this dual pattern: intensively cultivated valley floors and terraced lower slopes, with denuded scrub on the higher and farther hills - both true at once.)

### Frame math (why this matters at the scale we draw)

The maps we draw are small windows. Hirameki (town) at 1 px = 1 ft is a ~2,600 px frame, about **0.5 mile across**; Tango (city) at 1 px = 3 ft is about **1.5 miles across**. Both frames sit entirely inside what would historically be the intensive inner ring of a well-sited settlement. Within a half-mile of a county seat on good bottomland there would be essentially **no rough grazing at all**; the scrub belongs miles out, beyond the frame.

### The correct picture

Settlement core -> **dense inner ring of intensively worked land** (paddy + kitchen gardens + dryland aftercrop/bean plots) -> thinning outward -> scrub / rough grazing / fallow / managed woodland at the far edges and beyond the frame. The current maps have **inverted** this gradient: scrub in the near ring, farms scattered thinly through it. Densifying the near ring is therefore *more* faithful to the labor-limited setting model, not less - the fallow still exists, it is simply relocated to where the model actually puts it.

### Deliberate departures and boundaries of the claim

- This is **not** "paint the whole canvas green." Topography still governs (see FR-004): paddy needs flat, waterable ground; hills in-frame keep dry fields / tea / woodland / scrub on their slopes.
- "Packed" is a **quilt**, not a rice monoculture (see FR-003): paddy plus dryland plots plus gardens plus a genuine minority of fallow/rotation plots (the existing "~1 in 6 dry plots" convention already models this).
- The dense near ring is a property of a **well-sited** settlement. A dry rain-shadow town (Kikuta-type) or a marginal/frontier domain genuinely has thinner surroundings, so the intensity must be **tunable down** (see FR-005), not hard-coded high everywhere.

## User Scenarios and Testing *(mandatory)*

The "user" here is the GM generating and browsing `/diagram` settlement maps.

### User Story 1 - A well-sited town reads as embedded in packed farmland (Priority: P1)

The GM generates (or regenerates) a town map for a settlement on good bottomland. Instead of a town ringed by a thin scatter of farmhouses in a sea of scrub, the map shows the town embedded in a dense, worked near ring: fields fill the flat ground close to the settlement, farmhouses ring those fields at realistic density, and rough grazing / scrub only appears at the frame margins and on genuinely non-arable ground.

**Why this priority**: This is the whole point of the feature and the GM's original observation. It delivers value on its own even if the city scale and the tuning knob came later.

**Independent Test**: Regenerate the motivating town map (Hirameki) and confirm by eye and by manifest that cultivated area in the near ring rises substantially and scrub in the near ring drops, while the town, water, roads, and caste layout are unchanged and the existing gate stays green.

**Acceptance Scenarios**:

1. **Given** a well-sited town map, **When** it is generated, **Then** the flat, waterable ground within the near ring is predominantly cultivated (fields + farmsteads + gardens), not scrub.
2. **Given** the same map, **When** its hinterland is inspected, **Then** scrub / rough grazing appears only at the frame margins and on non-arable ground (hill slopes, the wet toe/marsh), not abutting the settlement edge on flat ground.
3. **Given** the same map, **When** the existing validator gate runs, **Then** all currently-passing checks still pass (population, caste counts, water connectivity, off-edge field, overlaps, no farmhouse on a channel, etc.).

---

### User Story 2 - A well-sited provincial city reads the same way (Priority: P2)

The same densification applies at city scale (`scale="city"`), so a walled or unwalled provincial city sits in a packed near ring rather than a sparse one, respecting the in-wall agricultural district and the moat/wall where present.

**Why this priority**: The city case shares the engine with towns and is the second half of the GM's question, but it is more constrained (walls, moat, the in-wall agricultural district, denser building grain), so it follows the town case rather than leading it.

**Independent Test**: Regenerate Tango and confirm the near-ring cultivated fraction rises while walls, moat, bridges, gates, ward fences, and the government compounds are unchanged and the city gate stays green.

**Acceptance Scenarios**:

1. **Given** a provincial-city map, **When** it is generated, **Then** the flat ground outside the wall within the near ring is predominantly cultivated.
2. **Given** a walled city, **When** densifying, **Then** no field, farmstead, or ground cover crosses the wall or the moat, and every gate approach road still bridges the moat.

---

### User Story 3 - Hinterland intensity is tunable per map (Priority: P3)

The GM can dial the near-ring farmland intensity down for a settlement that is deliberately not on prime land (a dry rain-shadow town, a marginal or frontier domain), so those maps keep a thinner, scrubbier surround while the default for a well-sited settlement is dense.

**Why this priority**: Without the knob the feature would over-correct and force every town into the same packed look, which is itself unhistorical. But the default (dense) delivers most of the value, so the knob can follow the default behavior.

**Independent Test**: Generate one map at the dense default and one with the intensity dialed down, and confirm the near-ring cultivated fraction differs as intended, with both passing the gate.

**Acceptance Scenarios**:

1. **Given** a map that declares reduced hinterland intensity, **When** it is generated, **Then** its near ring shows visibly more scrub / fallow and less cultivation than the default.
2. **Given** a map that declares nothing, **When** it is generated, **Then** it uses the dense (well-sited) default.

---

### Edge Cases

- **Hill in the frame**: the near ring around a hill must keep the hill's slopes in dry fields / tea / woodland / scrub (no paddy on slopes), while densifying the flat valley floor around it. Densification must not put paddy on a hill.
- **Wet toe / marsh**: the downhill reed marsh at the drainage toe stays; densification does not drain or overwrite it.
- **Walled settlement**: densified fields and farmsteads outside the wall must not cross the wall, moat, or gate approach, and must not collide with the segregated burakumin quarter or the gate market that sit outside the wall.
- **Water budget**: more near-ring fields need a plausible water story; the feature must not create fields with no visible water source, or channels that violate the existing downhill / anchored-at-both-ends / no-build-corridor rules.
- **Population and caste counts**: densifying farmland must not push farmhouse counts so high that `town_farmers_plurality` or the population/caste bands break, nor so low that the near ring looks sparse again.
- **Off-map implication**: at least one field must still run off the map edge (the "more farmland beyond" signal); densification must not accidentally close the frame into a self-contained island.
- **Regression fixtures**: if a new check is added, a pre-densification "sparse" manifest must be saved as a negative fixture proving the check has teeth.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: On town (`scale="town"`) and provincial-city (`scale="city"`) maps, the generator MUST fill the flat, waterable ground in the settlement's **near ring** predominantly with cultivated land (fields, farmsteads, gardens) rather than rough-grazing scrub, so a well-sited settlement reads as embedded in packed farmland.
- **FR-002**: The generator MUST relocate rough grazing / cut-over scrub and genuine fallow to the **frame margins and non-arable ground**, so scrub no longer abuts the settlement edge on flat, arable ground.
- **FR-003**: The densified near ring MUST remain a **quilt** of land uses - wet paddy plus dryland aftercrop/bean plots plus kitchen gardens plus a minority of fallow/rotation plots - and MUST NOT become a wet-paddy monoculture. The existing "~1 in 6 dry plots" convention is the floor for non-paddy variety, not a ceiling.
- **FR-004**: Densification MUST respect topography: no paddy on hill slopes; hills in-frame keep dry fields / tea / woodland / scrub on their slopes; only the flat, waterable ground is densified.
- **FR-005**: Near-ring farmland intensity MUST be **tunable per map**, defaulting to dense (well-sited) and dialable down for a deliberately marginal settlement (dry rain-shadow, frontier). A map that declares nothing gets the dense default.
- **FR-006**: All existing validator-gate checks that currently pass on the pool maps MUST continue to pass after densification - population and per-caste bands, farmer plurality, water source/connectivity, downhill flow, off-edge field, road/stream/channel/wall/moat overlap rules, bridges at water crossings, and the no-structure-on-corridor footprint tests.
- **FR-007**: Densification MUST NOT violate spatial exclusions: fields, farmsteads, and ground cover MUST stay off roads, streets, streams, irrigation channels, the manor block, the wall, the moat, and MUST NOT cross the wall or moat on a walled map; the burakumin quarter and gate market outside a wall MUST be preserved.
- **FR-008**: At least one field MUST still run off the map edge on town and city maps (the "farmland continues beyond the frame" signal); densification MUST NOT close the frame into a self-contained island.
- **FR-009**: The historical reasoning in "Context and Research Findings" above MUST be recorded alongside whatever knob, check, or generator change this feature produces (a "Historical grounding" note in `settlements.md` and/or a comment beside the relevant code), per the CLAUDE.md record-the-why rule.
- **FR-010**: If a new automated check is introduced to enforce near-ring density, a **negative regression fixture** (a pre-densification "sparse" manifest) MUST be saved under `pool/regressions/` proving the check fires on the sparse case, per the regression-corpus convention.
- **FR-011**: Village and hamlet scales are **out of scope**; their generators MUST be left behavior-unchanged by this feature (their frames are already mostly their own fields).

### Key Entities

- **Near ring**: the band of hinterland immediately around a settlement that, on a well-sited map, is intensively cultivated. Its extent is what the frame mostly shows at town/city scale.
- **Hinterland intensity**: the per-map tunable that sets how densely the near ring is cultivated versus left as scrub/fallow; default dense.
- **Cultivated near-ring land**: the quilt of wet paddy, dryland plots, kitchen gardens, and a fallow/rotation minority that fills the flat, waterable near ring.
- **Non-arable ground**: hill slopes, the wet drainage toe/marsh, and the frame margins - where scrub, rough grazing, managed woodland, and fallow now live.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On the motivating town map (Hirameki), the fraction of flat near-ring ground that is cultivated (field + farmstead + garden) rises substantially versus today, and the fraction that is bare scrub within the near ring drops correspondingly - the GM reads the regenerated map as "town embedded in farmland," not "town in a mostly-empty landscape."
- **SC-002**: On the provincial-city map (Tango), the same near-ring densification is visible outside the wall, with walls, moat, bridges, gates, and government compounds unchanged.
- **SC-003**: Every pool settlement map (all hamlets, villages, towns, provincial cities) regenerates cleanly and the full validator gate passes for all of them after the engine change (the mandatory full-pool sweep for shared-engine changes).
- **SC-004**: A map with hinterland intensity dialed down produces a visibly thinner, scrubbier near ring than the dense default, and both pass the gate - demonstrating the knob works in both directions.
- **SC-005**: Village and hamlet maps are byte-for-byte unchanged (or changed only as an intentional, reviewed side effect), confirming the feature is scoped to town/city.
- **SC-006**: The historical "why" is discoverable in `settlements.md` (and/or code comments) by a future reader without re-doing the research.

## Assumptions

- The primary artifacts to move are the existing pool maps Hirameki (town) and Tango (city); Hoshizora (unwalled town) and Nagahara (city) are additional downstream artifacts to verify but not necessarily to redesign.
- "Near ring" is defined relative to the drawn frame, not an absolute distance: at the scales we draw (town ~0.5 mi, city ~1.5 mi across), effectively the whole frame outside the settlement and its non-arable ground is near ring.
- Densification works by extending / adding field blocks and their ringing farmsteads on the flat ground and shrinking the scrub fill, reusing the existing field, farmstead, water, and hinterland machinery rather than inventing a new drawing vocabulary; the plan phase will decide the exact mechanism.
- The tunable will most naturally be a `meta(...)` knob on the settlement (a hinterland-intensity or local-arable-fraction parameter), consistent with how other per-map settlement options are declared; the exact name and range are a plan-phase decision.
- Population and caste counts remain governed by the existing declared `meta` figures and their gate bands; densifying farmland changes how much *field and farmhouse* is drawn, and any farmhouse-count change stays within the existing plurality/population tolerances (topped up or trimmed the same way the current generators do).
- This is a shared-engine change (`settlement.py`, and possibly `waterfields.py` / `check_village.py`), so the mandatory end-of-work full-pool regeneration and gate sweep applies.
- Work is done in the session clone on `main` (session-clone workflow); the spec-kit git feature-branch hook is intentionally not used because it conflicts with the push-back-to-`main` ritual.
