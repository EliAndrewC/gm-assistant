# Feature Specification: Domain-capital space budget and tier declaration

**Feature Branch**: none - this project stays on `main` (CLAUDE.md, GM 2026-07-27). Active feature is carried by `export SPECIFY_FEATURE=018-capital-space-budget`.

**Created**: 2026-08-08

**Status**: Draft

**Input**: Domain-capital space budget and tier declaration - the capital-city tier's first principle, mirroring feature 009 for provincial cities. Add `meta(scale="capital")` as a settlement tier and give it the budget-first machinery that derives its wall, so the capital map built in the FOLLOWING feature is sized from a declared program rather than guessed.

## Context: the decisions are already made

Every number and rule this feature encodes was settled with the GM across 2026-08-08 and is recorded, with its historical basis, in:

- [`.claude/skills/diagram/settlements/capitals.md`](../../.claude/skills/diagram/settlements/capitals.md) - the tier's operational rules
- [`.claude/skills/diagram/research/cities/capitals.md`](../../.claude/skills/diagram/research/cities/capitals.md) - the findings, anchors and disclosed departures

**Read both before planning. Do not re-litigate the decisions in them.** This spec's job is to say what the software must do, not to re-derive why.

## Scope boundary *(read this first)*

The capital tier is far too large for one feature. This feature is the tier's **first principle only** - the space budget that derives the wall - exactly as feature 009 was for provincial cities. The project's own doctrine requires this ordering: *"compute the budget FIRST, derive the wall from it, and hold the drawn map to the promise."*

**IN scope:** the budget model, the tier's declared knobs and their validation, the auditable report, and the check that holds a capital manifest to its declared budget.

**OUT of scope, and deliberately deferred to a following feature:** the castle glyph and its enceinte; the aqueduct glyph (open canal, *kakehi*, draw-basins); the wharf, domain granary and brokers' row glyphs; the kido mesh that replaces the continuous ward fence; rank-graded samurai districts, walled yashiki and retainer terraces as DRAWN features; the full capital-scale check block; and the Shiro Daika worked map.

**This feature therefore draws nothing.** It adds a tier that nothing yet uses, and the pool must come out byte-identical.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A capital's wall is DERIVED, never guessed (Priority: P1)

The GM asks for a domain capital. Rather than picking a wall size and grinding placements until things fit, the generator declares the capital's program - its population, whether it has a river, where its castle sits, how big the castle is - and the budget model returns the wall that program requires. The wall is an output.

**Why this priority**: This is the whole feature. Every later capital feature is built against the wall this produces, and a capital's wall cannot be guessed from population the way a provincial city's nearly can - a median castle alone is ~85% of an entire provincial city's interior, so population predicts a capital's size badly.

**Independent Test**: Declare a capital program and receive a wall specification, with no map drawn and nothing else in the tier implemented.

**Acceptance Scenarios**:

1. **Given** a capital program at the canonical population, **When** the budget is planned, **Then** it returns an itemized set of budget lines and a derived wall whose enclosed area matches the required interior.
2. **Given** the canonical capital program, **When** the wall is derived, **Then** it fits inside the existing standard canvas with its moat-and-margin clearance, so no canvas change is forced.
3. **Given** a population outside the capital's band, **When** the budget is planned, **Then** it raises with the numbers stated rather than silently clamping.
4. **Given** a provincial-city program, **When** the budget is planned, **Then** the result is byte-identical to what it was before this feature.

---

### User Story 2 - The GM can audit the budget line by line before anything is drawn (Priority: P2)

Before committing to a capital, the GM wants to see where its ground goes: how much is castle, how much is housing by type, how much is civic program, how much is circulation. Each line states what it is, how many, how much ground, and **why that number**.

**Why this priority**: The auditability is what makes the budget trustworthy rather than a black box, and it is how the GM catches a mis-priced program before a map is built on it. The provincial tier already works this way and the capital must not regress from it.

**Independent Test**: Run the report for a capital and read the itemized lines, with no map in existence.

**Acceptance Scenarios**:

1. **Given** a capital program, **When** the report is produced, **Then** every line carries its label, count, ground cost, and a basis string explaining where the number comes from.
2. **Given** a capital program, **When** the report is produced, **Then** the castle appears as its own line, and the samurai cohort appears as separate lines for walled compounds, detached houses and terraced housing rather than one undifferentiated total.

---

### User Story 3 - A capital's variant knobs are validated when declared (Priority: P3)

A capital declares choices that give two capitals different skeletons: where the castle sits, where the Emperor's granaries sit. Each is a genuine either/or with no strong default, and an impossible combination must be refused at declaration time rather than discovered on a rendered map.

**Why this priority**: Cheap to build, and it prevents a whole class of late failure - most importantly a castle declared on a dry edge, which is not a variant but a weak wall.

**Independent Test**: Declare each knob value and each invalid combination, and observe acceptance or a stated refusal.

**Acceptance Scenarios**:

1. **Given** a capital declaring an edge-seated castle with no water, **When** the program is validated, **Then** it is refused with a message naming the reason.
2. **Given** a capital declaring an edge-seated castle on a river, **When** the program is validated, **Then** it is accepted.
3. **Given** a capital declaring an unrecognized value for either knob, **When** the program is validated, **Then** it is refused with the legal values listed.

### Edge Cases

- **A capital at the bottom or top of its population band** must plan without error; outside it, the refusal states both the figure and the band.
- **A castle declared far outside the documented 50-230 ha band** is a program error the GM should see, not a silently accepted wall.
- **A capital manifest whose drawn interior drifts from its declared budget** must fail the same way a provincial one does, at the same tolerances.
- **A manifest that declares no budget at all** must not silently skip the check - a check that never runs looks exactly like a check that passes.
- **The provincial tier's existing refusal behavior** (raising outside its own band rather than clamping) must survive unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST support a capital tier distinct from the provincial-city tier, with its own population band centered on the canonical ~12,360, and MUST NOT satisfy it by widening the provincial band.
- **FR-002**: The system MUST enumerate a capital's household inventory from the capital caste table (480 servant, 960 laborer, 600 merchant, 120 burakumin, 240 samurai, plus 72 relocated samurai and 12 foreign Imperial households, and zero farmers).
- **FR-003**: The system MUST split the capital's samurai cohort by rank at roughly 70% senior / 30% junior - the inverse of a provincial city's mix - and MUST price the resulting groups as three distinct housing types.
- **FR-004**: The system MUST price a walled in-wall samurai compound and a retainer terrace as ground-cost constants distinct from the existing packed-row and detached-house constants, each carrying its measured basis at the point of definition.
- **FR-005**: The system MUST treat the castle as a declared program line with a documented default and a documented legal band, not a fixed constant.
- **FR-006**: The system MUST include a capital civic program covering the institutions the tier adds: the domain ministries and their government ward, the Imperial Magistrate's compound, the Emperor's granaries, the House Chancellery, the domain school, the sovereign temples, the domain granary with its brokers' row, and the aqueduct's works.
- **FR-007**: The system MUST apply a capital-specific in-wall samurai fraction, higher than the provincial tier's, reflecting that proximity to the daimyo's court is the point of a capital posting.
- **FR-008**: The system MUST accept a castle-seat declaration of either "ring" or "edge", MUST refuse "edge" unless the capital also declares water, and MUST refuse any other value.
- **FR-009**: The system MUST accept an Imperial-granary-seat declaration of either "magistrate" or "wharf", with neither as a privileged default, and MUST refuse any other value.
- **FR-010**: The system MUST derive the wall from the required interior using the same drawn-polygon geometry the provincial tier uses, so the derived wall is what will actually be drawn rather than an idealized shape.
- **FR-011**: The system MUST produce an itemized, auditable report for a capital in which every line carries a label, a count where meaningful, a ground cost, and a basis string.
- **FR-012**: The system MUST expose the capital tier through the same command-line audit path the provincial tier uses.
- **FR-013**: The system MUST refuse a population outside the capital band, and a derived wall that will not fit the declared canvas, by raising with the offending numbers stated - never by clamping.
- **FR-014**: The system MUST hold a capital manifest's drawn interior to its declared budget at the same tolerances the provincial tier uses (over by more than 8%, or under by more than 5%, is a failure).
- **FR-015**: The budget-conformance check MUST NOT be silently skippable: a capital manifest that declares no budget MUST fail rather than pass unexamined.
- **FR-016**: The system MUST leave every existing settlement byte-identical, and MUST preserve the provincial tier's existing out-of-band refusal behavior exactly.

### Key Entities

- **Capital program**: the declaration made before anything is drawn - population, water, castle seat and size, granary seat, temple program, and any itemized extras.
- **Budget line**: one auditable row - what it is, how many, how much ground it takes, and why that number.
- **Wall specification**: the derived enclosure - its shape, semi-axes, vertex count, enclosed area and perimeter.
- **Household inventory**: the capital's families by caste, with the samurai cohort further split by rank into the three housing types.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A GM can obtain a complete, itemized space budget and a derived wall for a domain capital without drawing anything.
- **SC-002**: The derived capital wall fits within the existing standard canvas including its moat-and-margin clearance, so adopting the tier forces no canvas change.
- **SC-003**: Every existing settlement in the pool regenerates byte-identically - the tier is additive and disturbs nothing.
- **SC-004**: Every budget line in a capital report states its basis, so a reader can trace any number to its source without reading code.
- **SC-005**: Every invalid declaration in the Edge Cases section produces a refusal that names the offending value and the legal alternatives.
- **SC-006**: The new logic reaches 100% line coverage, and the full project gate passes.
- **SC-007**: A capital manifest whose enclosed area drifts outside the declared tolerances is reported as a failure, and one that declares no budget is likewise reported rather than passing unexamined.

## Assumptions

- **The recorded decisions are authoritative.** Population, caste table, rank split, ground-cost constants, castle size band, the two knobs, and the in-wall samurai fraction all come from `settlements/capitals.md` and `research/cities/capitals.md` and are treated as settled input, not open questions.
- **`C_TERRACE` is the softest number in the feature** and is documented as such. It is bracketed by measured anchors at both ends but its position between them is a judgment, and both new constants are expected to be re-derived against the first drawn capital, exactly as the provincial constants were back-predicted from Tango.
- **The capital keeps the provincial tier's circulation fraction** unless the first drawn capital shows otherwise; there is no measured capital figure yet, and inventing one would be less honest than reusing a measured one.
- **The capital has no agricultural district.** The wall encloses all inhabitants and no farmland (GM 2026-08-08), so the provincial agricultural-district reserve does not apply.
- **Clan identity does not affect the budget.** Clan changes labels only (GM 2026-08-08), so no clan-specific program rows exist.
- **The castle's interior is not priced separately.** The granary and armory sit inside the castle and are not drawn (GM 2026-08-08), so they are inside the castle's single declared line rather than itemized against the city's ground.
- **The first drawn capital, Shiro Daika, is a river city with a ring-seated castle**, so the "edge" seat is validated in this feature but only the "ring" seat is exercised by a real program.
