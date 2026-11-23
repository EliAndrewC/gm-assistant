# Feature Specification: Money skill - prices by place, and what carrying a good costs

**Feature Branch**: none (this project stays on `main`; `SPECIFY_FEATURE=233-money-place-prices`)

**Created**: 2026-11-23

**Status**: Draft - specified only. The GM asked for the spec and NOT the implementation; plan, tasks and implement wait for the GM.

**Input**: the GM's request, verbatim (dictated, 2026-11-23):

> More generally: does our money skill have enough detail on the **range** of prices to be able to support these kinds
> of questions? Like enough for us to be able to say something like "tea sells more cheaply in Crab lands, whose arable
> land is well suited to growing it, and it is more expensive in Kyuden Kakita, and based on historical research that
> price difference is likely to be ____"?

and, after the session answered no and proposed tooling changes alongside a research request (filed as
[EliAndrewC/diagram#24](https://github.com/EliAndrewC/diagram/issues/24), `requests/0023-producer-to-market-price-spread.md`):

> And then please create the spec kit feature for the associated tooling changes, but don't actually work the feature yet.

The "associated tooling changes", as proposed to the GM in the same conversation:

1. an optional place on ledger rows, so one good can carry a producing-region price and a consuming-city price;
2. a command that, for any good from place A to place B, derives the destination price the way the charcoal rows already
   do (origin price + freight + gate tariffs + a merchant's margin) and prints the result with its basis;
3. room for the sea-freight, margin and ship rows that diagram#24 will return.

## Why (the gap, as measured on 2026-11-23)

- The ledger (`webapp/l7r/money/data/ledger.jsonl`, 276 rows) has one low-high range per item and no place field. A
  range mixes source uncertainty, grade, and disagreement between sources; a place appears only in free-text notes.
- No long-distance trade good is priced (tea, sugar, raw silk, spices, incense have no row; iron by weight only as a
  sickle's input). A session answering "a boatload of Yasuki sugar landed at Shiro Etsuko" had to derive every figure.
- diagram#15's place-to-place spread came back as seven swing notes about TIME (`data/swings.jsonl`), plus two remarks
  on place (salt monopolies; rice and lamp oil borrow freely between cities).
- The one place model that exists is hand-built in the charcoal rows (`questions.md`, charcoal): kiln price, plus
  carriage at a researched per-ri rate, plus *"a 15% tariff per border and a merchant's margin"*. It is prose and
  per-row arithmetic, not something another good can reuse.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The GM's tea sentence (Priority: P1)

The GM, or a session answering for the GM, asks how much more a good costs where it is consumed than where it is made,
and gets a sentence of the form the GM asked for: "tea sells more cheaply in <producing place> ... and it is more
expensive in <consuming place>, and based on historical research that price difference is likely to be <ratio or
range>", with the basis and its solidity (researched / extrapolated / estimated) stated.

**Why this priority**: it is the GM's question, word for word; everything else exists to make it answerable.

**Independent Test**: with a good that has a producing-place price row and a researched producer-to-market ratio (or,
before diagram#24 answers, a logged estimate), ask the carriage command for that good from a producing place to a
consuming place and read back a price at each end, the difference as a ratio, and the label of every input used.

**Acceptance Scenarios**:

1. **Given** tea has a price row at its producing place and freight rows exist for the route, **When** the command is
   asked for tea from the producing place to Kyuden Kakita, **Then** it prints the price at both ends, the ratio between
   them, and each component (origin price, freight, tariffs, margin) with its source and label.
2. **Given** an input is only estimated (no research yet), **When** the answer prints, **Then** the answer's overall
   label is no stronger than its weakest input, and the estimated input is named.
3. **Given** a researched producer-to-market ratio exists for the good (from diagram#24), **When** the command runs,
   **Then** it prints that ratio beside the derived one, so a gap between the cost model and history is visible.

---

### User Story 2 - A price can say where it was observed (Priority: P1)

A ledger row may carry the place its price belongs to (a producing region, a consuming city, or a named Rokugani
place), so one good can hold a price at each end of a trade route without two rows being mistaken for disagreeing
sources.

**Why this priority**: without it there is nothing for Story 1 to read; it is the data half of the same answer.

**Independent Test**: add two rows for the same good at two places; `price <good>` shows both, each with its place,
and `check` passes; a row without a place still behaves exactly as today.

**Acceptance Scenarios**:

1. **Given** a row with no place (every existing row), **When** any existing command runs, **Then** its output is
   unchanged.
2. **Given** two rows for one good at different places, **When** `price` lists them, **Then** each shows its place and
   they read as the two ends of a route, not as a disagreement.
3. **Given** a row names a place the money tools do not recognize, **When** `check` runs, **Then** it fails and the
   message names the row and says how to fix it.

---

### User Story 3 - Tariffs follow canon and the GM's rulings (Priority: P2)

The carriage command applies the gate tariff the way the setting defines it, not a flat 15%, and lets the asker say
whose goods they are and at whose gate they are sold.

**Why this priority**: the questions that prompted this feature turn on the gap between rates; a flat 15% hides
exactly what the GM was asking about. The GM, 2026-11-23, on the bulletin's "many-colored Yasuki" smuggler: *"The
Crane hate the Yasuki and let's say they stubbornly impose the maximum tarriff on Yasuki goods. And let's say that a
desire for Scorpion silk and Phoenix iron and Mantis sugarcane has led them to impose the lowest possible tarriff on
those goods. What is the % difference"*; and later: *"while a local House daimyo cannot waive the Family or Clan
tarriff rates, the family and clan itself can negotiate those rates, and so that means that it is plausible that the
only rate on Phoenix Iron, for example, would be the Imperial rate, correct?"*

**Independent Test**: price one cargo at one gate under three origins (full rate, typical rate, negotiated rate) and read
back three tariffs that match the rules below.

**Acceptance Scenarios**:

1. **Given** no origin arrangement is named, **When** the command prices a sale, **Then** it uses the typical
   effective rate (*"about 15% of declared sales value"*, `setting/l7r.md`, Ministry of Revenue) and says so.
2. **Given** an origin with no preferential arrangement, **When** priced, **Then** the rate is the 20% legal maximum.
3. **Given** the Family and Clan above the gate of sale have negotiated their layers to zero for this origin, and the
   local daimyo charges no portion, **When** priced, **Then** only the Imperial 5% applies; the Imperial layer is
   never negotiated away.
4. **Given** the Family and Clan above the gate have negotiated their layers part of the way down (say to 1% and 1%),
   **When** priced, **Then** the rate is those layers plus the Imperial 5% plus the local daimyo's portion.
5. **Given** goods declared in transit, **When** priced at a transit city, **Then** no tariff is charged there (canon:
   tariffs are point-of-sale, not point-of-transit).

---

### User Story 4 - The research lands somewhere (Priority: P3)

When diagram#24 answers (coastal sea freight, wholesalers' and shipowner-traders' margins, ships' burthen, crew and
cost), its figures go into the ledger as rows the carriage command reads, through the skill's existing take-in path
(`research.md`, "Taking in an answer"), and the logged estimates E0220-E0238 are graded as usual.

**Why this priority**: the tooling must not need rework when the research arrives, but the research is not here yet.

**Independent Test**: add a sea-freight row and a margin row in the shape the answer will take; the carriage command
picks them up for a sea route with no code change.

**Acceptance Scenarios**:

1. **Given** a sea-freight row exists, **When** a route is declared as by sea, **Then** the command uses it rather than
   the river or pack-horse rate, and names it.
2. **Given** no margin row exists for a kind of trader, **When** the command runs, **Then** it uses the skill's stated
   default margin, labels it estimated, and says which row would replace it.
3. **Given** rows for coastal ships (burthen, crew, crew pay, build cost, working life, charter), **When** `check`
   runs, **Then** they are accepted; the carriage command is not required to read them.

### Edge Cases

- A route crosses several domains: tariff is charged only at the city of sale (canon: *"Tariffs are point-of-sale, not
  point-of-transit"*), not per border crossed. The charcoal rows' "15% per border" wording differs; that difference is
  recorded under FR-012, and whether to change the charcoal rows is the GM's call, separate from this feature.
- The origin price and the destination price are both researched and disagree with the cost model: both are shown,
  and the gap is reported, not hidden.
- A good has no producing-place row at all: the command says so and names what would fix it, rather than guessing.
- The asker gives a place the tools do not know: the error lists the known places.
- The same good is produced in more than one region: each producing place is its own row; the asker chooses.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A ledger row MUST be able to carry an optional place; rows without one MUST behave exactly as they do now.
- **FR-002**: `check` MUST reject a row whose place is not a recognized place, with a message naming the row and the fix.
- **FR-003**: `price` MUST show a row's place when it has one.
- **FR-004**: A new command MUST, for a named good, origin place and destination place, print the price at the origin,
  each added cost (freight, tariff, merchant's margin), the price at the destination, and the destination-to-origin
  ratio.
- **FR-005**: Every printed figure MUST name its source row and label; the answer's overall label MUST be no stronger
  than its weakest input.
- **FR-006**: Freight MUST be chosen by mode of carriage (sea, river, land) from ledger rows, scaled by distance.
- **FR-007**: The tariff MUST be charged once, at the city of sale, at a rate set by the canon rate structure: a 20%
  maximum of declared sales value; a 10% kick-up layer (2% Family, 3% Clan, 5% Imperial) the local daimyo cannot waive;
  the Family and Clan above the gate's daimyo MAY negotiate their own 2% and 3% layers down, to as low as zero, for a
  given origin (GM 2026-11-23); the Imperial 5% is never negotiated away; goods in transit pay nothing.
- **FR-008**: The asker MUST be able to name the seller's origin arrangement (full rate, typical, a named discount of
  the local daimyo's portion, a negotiated Family/Clan rate) and get the matching rate; with none named, the typical ~15% applies and is stated.
- **FR-009**: Where a researched producer-to-market ratio exists for the good, the command MUST print it beside the
  derived ratio.
- **FR-010**: Missing inputs MUST produce a message naming the missing row and how to add it, not a silent default;
  where the skill has a stated default (a merchant's margin), the default is used, labeled estimated, and named.
- **FR-011**: The skill's `SKILL.md` MUST say, in one line plus an index entry, when to use the new command; detail goes
  in a topic file that opens with "Load this file when:".
- **FR-012**: The existing charcoal far-market rows MUST be reproducible by the new command from their own inputs, or
  the difference MUST be recorded with its reason.
- **FR-013**: Ledger rows for coastal ships (burthen, crew, crew pay, build cost, working life, charter) MUST be
  accepted and pass `check`; the carriage command need not read them.

### Key Entities

- **Place**: a named location a price belongs to - a Rokugani settlement or region (Kyuden Kakita, Shiro Etsuko, the
  Yasuki Estates, Sparrow lands) or a historical one a source names (Osaka, Uji); has the distance and mode of carriage
  to other places where known.
- **Route**: an origin place, a destination place, a mode of carriage and a distance.
- **Origin arrangement**: who is selling and what rate their clan and family have negotiated at the gate of sale.
- **Carriage answer**: the price at each end, each added cost, the ratio, and the label and source of every part.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Given producing-place rows for a good (from diagram#24, or entered from the logged estimates), the GM's
  tea sentence comes out of one command for that good between its producing place and Kyuden Kakita, with every
  number's basis printed. Entering those rows is not part of this feature.
- **SC-002**: All 276 existing ledger rows pass `check` unchanged, and every existing command's output is unchanged
  for them.
- **SC-003**: The three tariff cases from the GM's questions (User Story 3) each come out of the command at the stated
  rate: Yasuki goods at the 20% maximum; a favored house at the 10% floor (the local daimyo's portion at zero); and
  Phoenix goods at 5% when the Family and Clan above the gate have negotiated their layers to zero and the local
  daimyo charges no portion.
- **SC-004**: When diagram#24's answer is taken in, no code change is needed for the command to use the new rows.
- **SC-005**: The charcoal far-market prices are reproduced within their stated ranges, or each difference is recorded.

## Assumptions

- **Command-line only.** The GM asked for the tooling behind answers; a webapp page (beside `/money/koku`) is out of
  scope unless the GM asks.
- **Place names come from canon and the sources**, not invented; a Rokugani place a session needs that has no canon
  location is an error, not a guess.
- **Distances between Rokugani places are not in canon** for most pairs; the command takes a distance from the asker
  when no recorded one exists, and prints that it was supplied.
- **The negotiated-layer rule** (the Family and Clan above a gate may negotiate their own layers down, to zero; the
  Imperial 5% never is) is the GM's ruling of 2026-11-23 in conversation; it is not yet written into `setting/l7r.md`. Implementation applies it; writing
  it into the canon is the GM's call, separate from this feature.
- **Research first, where it is cheap**: implementing before diagram#24 answers is fine (the command works on
  estimates and labels them); the GM will decide when to work the feature.
- **The rows diagram#24 returns** enter through the existing take-in path in `research.md`; this feature adds no new
  intake process.

## Review history

- **Round 1 (spec-fidelity): CHANGES REQUIRED.** Six changes, all applied: ship rows got FR-013 and a User Story 4
  scenario (item 3 asked for "room" for them); "waive" became "negotiate", to as low as zero, per the GM's own word;
  the layers belong to the Family and Clan above the gate of sale, and the 5% case states that the local daimyo
  charges no portion; SC-001 no longer requires entering four goods' price rows; the charcoal "per border" difference
  is recorded under FR-012 and changing the charcoal rows is left to the GM; the tariff cases and the smuggling
  context now quote the GM's words.
- **Round 2 (spec-fidelity): FAITHFUL.** One wording tidy applied ("treaty rate" -> "negotiated rate" in User Story 3's
  independent test).
