# Feature Specification: Capital Housing Layer

**Feature Branch**: `021-capital-housing` (no git branch - `SPECIFY_FEATURE=021-capital-housing`, per the no-feature-branches rule)

**Created**: 2026-08-09

**Status**: Draft

**Input**: User description: "Capital housing layer (feature 021) for the /diagram skill: fill Shiro Daika's interior fabric around the ground reserved by feature 020, and graduate the map from wip/ to pool/capitals/. Scope: rank-graded samurai districts, retainer terraces, and commoner machi packs at capital scale (1px = 3ft, row-packing doctrine); public wells as josui-ido cistern-wells drawing on the buried aqueduct mains per the 020 research; fire towers and the kido ward-gate mesh; the two sovereign temple precinct interiors drawn inside their 020-reserved ground (residence, administration, library, monk housing) plus their monzen neighborhoods per the patron-temple doctrine; the lean teramachi backstrip; a declared wind bearing before nuisance trades land; closing the graveyard claims when precincts are drawn; the wharf's kashi merchant frontage (brokers' row, warehouses, entertainment district) per the wharf-chain doctrine; the farrier and relay stables that turn imperial_road_town_has_farrier green; and one deliberate caption-loudness pass at the end. The review-deferred items and doctrine live in wip/shiro-daika.notes.md, settlements/capitals.md, and research/cities/capitals.md."

## What this feature is

Features 018-020 built the capital's skeleton: budget, wall, castle, government ward, lineage
compounds, waterfront works, and every piece of ground that must be RESERVED before housing.
The map today is a city of institutions with nobody home - 12,360 declared inhabitants and
zero dwellings. Feature 021 fills the fabric: where the samurai, retainers, commoners, monks,
brokers, and porters of a domain capital actually live and trade, packed around the reserved
ground, with the safety and administrative furniture (wells, fire towers, ward gates, the
relay stables) a city of this size keeps. When it is done, the map graduates from `wip/` to
`pool/capitals/` as the first finished domain capital and the worked example for every
capital after it.

This is a GENERATOR capability, not a one-map effort: the packs, precinct interiors, and
wharf fabric become engine features any future capital gen calls, exactly as the provincial
cities and villages share their packs today. Shiro Daika is the proving map.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The GM reads a lived-in capital (Priority: P1)

The GM opens the finished map and sees a complete city rather than institutions on bare
ground: samurai districts graded by rank around the castle (higher rank nearer the castle
and the government ward), retainer terraces behind them, dense commoner machi filling the
south and the approaches, every district packed in the established row doctrine (rows touch;
roji gaps are features, not slack), and no unexplained empty ground inside the wall except
the ground the doctrine holds open on purpose.

**Why this priority**: housing is the feature; everything else in 021 decorates it. A capital
with dwellings but no wharf fabric is still a city; a capital with a wharf district and no
dwellings is still a diagram of institutions.

**Independent Test**: regenerate the map and confirm the declared population is actually
housed - the housing consistency rules that run on every provincial city run here and pass -
and that district placement follows the rank gradient by inspection.

**Acceptance Scenarios**:

1. **Given** the 020 map, **When** the housing packs run, **Then** the map houses its
   declared 12,360 inhabitants within the tolerance the city-scale consistency rules demand.
2. **Given** the finished map, **When** the GM inspects any samurai district, **Then**
   rank-graded compounds sit nearer the castle than lower-rank terraces, and commoner rows
   sit furthest, matching the recorded gradient doctrine.
3. **Given** the finished map, **When** any pack has seated, **Then** no dwelling stands on
   reserved ground (compounds, precincts, corridors, keep-outs) - the overlap gate stays
   green.

---

### User Story 2 - A reader traces daily water and daily safety (Priority: P2)

A reader who follows the aqueduct from the intake weir to the settling basin can continue
the story inside the wall: cistern-wells (the josui-ido of the 020 research) serve the
districts the buried mains reach, ordinary draw-wells serve the rest, every dwelling is
within reach of some water, fire towers watch the dense quarters, and the kido ward-gate
mesh closes the commoner streets at night exactly as the internal-walls research recorded.

**Why this priority**: the water story is the map's declared User Story 3 from feature 020,
and safety furniture is what makes dense fabric read as governed rather than sprawl.

**Independent Test**: the existing watered-dwellings and fire-cover rules pass at capital
scale; cistern-wells appear only along the buried main's plausible reach from the gate
terminus; kido stand at the commoner district mouths.

**Acceptance Scenarios**:

1. **Given** the finished map, **When** the watered-dwellings rule runs, **Then** every
   dwelling is within the recorded reach of a well, and the wells in the aqueduct's service
   band are drawn and recorded as cistern-wells.
2. **Given** the dense quarters, **When** fire-cover rules run, **Then** towers cover the
   fabric per the city doctrine, clear of everything per the keep-clear contract.
3. **Given** the commoner machi, **When** the map is finished, **Then** ward gates close the
   machi street mouths, and samurai streets are sealed by their own yashiki walls (no
   district-wall ring, per the internal-walls research).

---

### User Story 3 - The temples grow their real precincts and neighborhoods (Priority: P2)

The two sovereign temples (Benten, Jurojin) fill the ground 020 reserved for them: abbot's
residence, administration hall, library, and monk housing inside the precinct, with each
temple's monzen neighborhood (the lay quarter that serves it) growing outside its gate. The
six patron temples on the rim keep their modest halls, each with the lean backstrip the
teramachi doctrine demands - and the graveyard claims every temple declared in 020 are
closed: the ground is drawn, or the claim is removed.

**Why this priority**: the precinct reservations are 020 promises this feature exists to
keep; the monzen neighborhoods are the patron-temple doctrine the GM adopted as world canon.

**Independent Test**: precinct interiors draw inside the reserved rectangles only; monzen
rows front the temple approaches; the teramachi backstrip stays within its lean depth; no
`graveyard: true` claim survives without drawn ground.

**Acceptance Scenarios**:

1. **Given** the reserved precinct ground, **When** the precinct interiors draw, **Then**
   every building lands inside its reservation and the sovereign-temple staffing canon
   (50+ monks, initiates living out) is visibly plausible.
2. **Given** a temple with a monzen neighborhood, **When** the packs run, **Then** lay rows
   front the temple's approach on the street side its torii face.
3. **Given** the rim temples, **When** the map is finished, **Then** the strip behind the
   teramachi rim stays lean per the review-deferred note.

---

### User Story 4 - The wharf becomes the commercial hub the research promised (Priority: P3)

The kashi landing gains its merchant fabric per the wharf-chain doctrine: warehouse rows on
the bank top, the brokers' row in front of the domain granary (merchant, wealth skewed
high), and the entertainment district beside it - the chain wharf -> granary -> brokers ->
theaters that makes the waterfront read as one mechanism. Nuisance trades (tanning, dyeing,
kilns) land only after a wind bearing is declared, and sit downwind and downstream of the
dwellings they would offend.

**Why this priority**: it completes the internal-dock research answer ("the grain-only look
is the ground layer's emptiness") and the 020 review's nuisance-trade deferral, but the city
is legible without it sooner than without housing or water.

**Independent Test**: the wharf chain's four links are present and adjacent in order; every
nuisance trade sits on the declared lee side; the wind bearing is recorded on the map.

**Acceptance Scenarios**:

1. **Given** the finished waterfront, **When** the GM traces the chain, **Then** warehouse
   rows, brokers' row, and the entertainment district adjoin in the doctrinal order.
2. **Given** the declared wind bearing, **When** nuisance trades seat, **Then** each sits
   downwind of the residential fabric and downstream of the water draw points.

---

### User Story 5 - The gate goes green and the map ships (Priority: P3)

The relay stables and farrier that an Imperial-road city keeps turn the one deliberately-red
check green. A final caption-loudness pass tunes every label on the sheet to one deliberate
hierarchy. The map moves from `wip/` to `pool/capitals/`, enters the regression corpus and
the render pool, and the independent settlement review passes on the full sheet.

**Why this priority**: shipping is the point, but it is only meaningful after stories 1-4.

**Independent Test**: the full gate reports zero failing checks on the map in its pool
location with zero new waivers; the review agent's FULL pass returns no errors.

**Acceptance Scenarios**:

1. **Given** the finished fabric, **When** the farrier and relay stables seat by the gate
   doctrine, **Then** `imperial_road_town_has_farrier` passes without exemption.
2. **Given** the finished sheet, **When** the caption-loudness pass ends, **Then** the label
   hierarchy is deliberate (documented), and the review agent confirms no caption shouts
   over a more important neighbor.
3. **Given** the shipped map, **When** the pool sweep runs, **Then** the capital gates green
   among the pool with its budgets entry and cache behavior like any other map.

### Edge Cases

- A pack that cannot meet its housing target inside its district (the reserved ground is
  large): the budget's targets must be reconciled with drawable ground BEFORE packing, not
  discovered as an unmeetable-target grind (the Minami seat-memo lesson).
- The aqueduct's service band covers only part of the fabric: dwellings beyond it must fall
  back to draw-wells without the watered-dwellings rule flapping.
- Precinct interiors vs the canopy keep-outs and label bands already registered in 020: the
  draw order must let precinct buildings in while keeping foreign packs out.
- The wind bearing conflicts with an already-seated feature (the dye yard on the wharf side):
  the bearing is declared FIRST; any conflict is a siting error to fix, not a waiver.
- Ward gates (kido) meeting the keep-clear contract: kido record drawn extents and are
  matrix-visible (the 2026-07-27 lesson) - new fabric must not regress that.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The map MUST house its declared population: the same consistency rules that
  bind every provincial city (population vs dwellings, density floors, quarter tiling) run
  and pass at capital scale.
- **FR-002**: Samurai housing MUST grade by rank with distance from the castle/government
  ward, retainer terraces between, commoner machi furthest, per the recorded gradient
  doctrine; the gradient must be visible on the sheet and checkable from the manifest.
- **FR-003**: All packs MUST respect every 020 reservation (compounds, precincts, corridors,
  aprons, canopy keep-outs) - zero overlap-matrix regressions.
- **FR-004**: Public wells MUST split into cistern-wells (recorded as such) within the
  buried main's service band from the aqueduct's gate terminus, and ordinary draw-wells
  elsewhere; every dwelling within recorded reach of some well.
- **FR-005**: Fire towers MUST cover the dense fabric per existing city fire doctrine; kido
  ward gates MUST close commoner street mouths; both remain fully keep-clear-classified.
- **FR-006**: The two sovereign temple precincts MUST draw their interiors (residence,
  administration, library, monk housing) inside the 020-reserved ground, and each declared
  `graveyard: true` claim MUST end the feature either drawn or removed.
- **FR-007**: Monzen lay neighborhoods MUST front each temple's approach; the teramachi
  backstrip MUST stay lean per the review-deferred bound.
- **FR-008**: The wharf MUST gain its kashi fabric in the doctrinal chain order: warehouses,
  brokers' row (merchant, wealth-high), entertainment district.
- **FR-009**: The map MUST declare a wind bearing before any nuisance trade seats, and every
  nuisance trade MUST sit downwind of dwellings and downstream of water draws.
- **FR-010**: Relay stables and a farrier MUST seat per the Imperial-road doctrine, turning
  `imperial_road_town_has_farrier` green without exemption.
- **FR-011**: A deliberate caption-loudness pass MUST end the feature, with the chosen
  hierarchy recorded (record-the-why).
- **FR-012**: The finished map MUST move to `pool/capitals/`, join the pool sweep, budgets,
  and cache like any pool map, and pass a FULL independent settlement review.
- **FR-013**: Every new engine capability (capital packs, precinct interiors, wharf fabric,
  cistern-wells, wind bearing) MUST be a reusable knob for future capital gens, not
  Shiro-Daika-only code.

### Key Entities

- **District**: a named region of the fabric (samurai band, retainer terrace, machi, monzen
  neighborhood) with a caste, a rank grade, and a housing target reconciled to its ground.
- **Cistern-well (josui-ido)**: a public well drawing on the buried aqueduct main; recorded
  distinctly from draw-wells; exists only within the main's service band.
- **Precinct interior**: the buildings inside a sovereign temple's reserved ground.
- **Wind bearing**: a declared map-level bearing that gates nuisance-trade placement.
- **Wharf fabric**: the warehouse rows, brokers' row, and entertainment district bound to
  the landing in chain order.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The capital houses 12,360 declared inhabitants within the same tolerance every
  provincial city meets, with zero failing checks and zero new waivers on the shipped map.
- **SC-002**: `imperial_road_town_has_farrier` - the one deliberately-red check since 019 -
  passes, making the map the first green capital.
- **SC-003**: The independent settlement review (FULL scope) returns a pass verdict on the
  shipped sheet with zero errors.
- **SC-004**: Every 020 reservation is either built on by its intended owner or explained;
  no `graveyard: true` claim survives undrawn; the review's four deferred items are closed.
- **SC-005**: A second capital gen could call every new capability without touching engine
  internals (the knobs are documented in the capitals doctrine file).
- **SC-006**: The whole-pool gate stays green and within its time budgets with the capital
  added to the pool.

## Assumptions

- **The 018 budget is the housing authority**: caste splits and district ground come from
  the recorded `plan_capital` budget and budgets.md canon (samurai share per the capital
  tier), not from new demographic research. Any reconciliation (target vs drawable ground)
  is documented at plan time.
- **Row-packing doctrine transfers from Tango**: capital fabric uses the city row-packing
  rules (rows touch, roji as features) at 3 ft/px; no new packing paradigm is invented.
- **The wind bearing is a researched knob**: its default for Shiro Daika is settled during
  planning from the map's declared geography (river valley, NE->SW fall), recorded with the
  why; it is a `meta` knob for future capitals.
- **Sovereign-temple staffing canon** (50+ monks each, initiates 2x living out, lay temple
  neighborhoods) is the fixed input for precinct sizing - already GM-decided, not re-opened.
- **No new waivers**: if a rule genuinely cannot hold at capital scale, the rule gains a
  scale-aware bound (with research), never a Shiro-Daika waiver.
- **The GM reviews the rendered map at the end** (their stated preference this session);
  mid-feature questions go to the GM only when research cannot settle them.
