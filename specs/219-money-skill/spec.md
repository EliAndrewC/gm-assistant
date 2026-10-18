# Feature 219: The money skill

**Feature Branch**: none (main, in a session clone)

**Created**: 2026-10-18

**Status**: Draft

**Input**: `request.md` (the GM, 2026-10-18), and the handoff it names (`money/HANDOFF.md` and `money/digest.md` in the
GM's l7r repository)

## Why

The GM wants to *"figure out what things would realistically cost in our setting instead of just completely hand
waving"* (request.md). Pre-modern price records are patchy - nobody preserved what a Roman gladius cost - so most prices
have to be reasoned from neighbors: similar goods, the metal, the smithing, equivalent goods in comparable societies.
The GM's standard is *"some amount of internal consistency"*. The skill therefore rests every figure on a stated basis,
says how solid that basis is, and keeps the bases consistent with one another and with the canon.

Three kinds of basis already exist or are coming:
- **Research already done**: the GM's 2013-2017 notes and the two spreadsheets Chris shared (PPP basket, Austen in
  Rokugan), digested by diagram's Money session.
- **Purchasing power parity**: a historical basket of goods re-priced in today's dollars, which gives what a koku buys.
- **New research**, which the diagram repository does (its record has the search pass, the source archive and the
  checking agents). This skill asks for it by GitHub issue and cites the answers.

And the GM is clear about how money is used: *"very few people would buy things with Koku because that is just an
absurdly high amount of money ... most people in this setting do not either ... Player characters who do are
exceptionally wealthy in a way which is noteworthy."*

## User Scenarios & Testing

### User Story 1 - What does it cost? (Priority: P1)

The GM asks `/money` what a thing costs in Rokugan (a sword, a night at an inn, a farm, a laborer's year, a bribe). The
skill answers with a figure or range in the coins a buyer would actually hand over, the koku equivalent, both dollar
readings, and the basis: which ledger row or reasoning chain it rests on and how solid that is.

**Why this priority**: it is the skill.

**Independent Test**: ask for an item that is in the ledger and one that is not. The first answer quotes the row and its
label; the second reasons from named neighboring rows (material, labor, comparable goods), labels the result a guess, and
offers to add it to the ledger or to ask diagram for research.

**Acceptance Scenarios**:

1. **Given** a ledger row for the item, **When** the GM asks its price, **Then** the answer gives the row's figure in
   everyday coins (sen / zeni / bu for anything a commoner buys), its koku value, its PPP and "big deal" dollar readings,
   its label and its source pointer.
2. **Given** an item with no row, **When** the GM asks, **Then** the answer derives a figure from named rows, shows the
   derivation, labels it a guess, and says which research request would firm it up.
3. **Given** a price of a koku or more, **When** it is answered, **Then** the answer says who in the setting would pay that
   sum in gold and that doing so marks the payer as noteworthy wealth.

### User Story 2 - What does a koku get you? (Priority: P1)

The GM asks what a sum is worth: "what is 3 koku to a farmer", "what does 4 bu buy". The skill converts between the coins
and gives both dollar readings, each derived from dated inputs, plus a few ledger items the sum would buy.

**Why this priority**: the GM's request names it (*"figure out what a Koku gets you"*), and every price answer depends on it.

**Independent Test**: the conversion of the 2017 basket snapshot reproduces the spreadsheet: $797.22 = 144.32 zeni,
1 koku = $552. The "big deal" reading of 1 koku at the default wage is about $9,400.

**Acceptance Scenarios**:

1. **Given** an amount in any coin, **When** it is converted, **Then** the result is exact in koku / bu / zeni / sen
   (1 koku = 10 bu = 100 zeni = 1,000 sen).
2. **Given** the dated basket snapshot in use, **When** a koku is converted to PPP dollars, **Then** the answer names the
   snapshot date and the koku-of-rice mass it assumed.
3. **Given** the dated wage in use, **When** a koku is converted to "big deal" dollars, **Then** the answer names that wage
   and the unskilled laborer's year in koku it divides by.

### User Story 3 - Ask diagram, take in the answer (Priority: P1)

A price the ledger cannot support well needs research. The skill drafts a request for the diagram repository, the GM's
session there works it, and the answer comes back as question files with verdicts. The skill verifies the answer, updates
the ledger rows (figure, label, source pointer) and closes the issue.

**Why this priority**: the GM's request: *"they will be handling the research questions that come up, of which I am sure
that there will be a lot"*.

**Independent Test**: the first request is opened on `EliAndrewC/diagram` in this feature; the skill documents the
request body (question, figure needed, canon it sits beside, Japan-first or China-first) and the intake steps.

**Acceptance Scenarios**:

1. **Given** a research question, **When** the skill opens a request, **Then** the issue carries the question, the figure
   the skill needs, the canon it must sit beside, and Japan-first or China-first.
2. **Given** a diagram answer, **When** it is taken in, **Then** each affected ledger row points at the question file on
   GitHub, its label reflects the verdict, and the issue is closed by this side after checking.
3. **Given** an answer whose history contradicts the canon, **When** it is taken in, **Then** the canon is not changed;
   the contradiction is put to the GM, who decides.

### User Story 4 - Keep it up to date (Priority: P2)

Years later, the GM wants current dollars. The skill re-prices the basket into a new dated snapshot (keeping the old one)
and re-takes the wage, and every dollar reading moves with them.

**Why this priority**: the GM: *"keep up to date and keep track of so that we can update it periodically"*.

**Independent Test**: adding a second snapshot file changes the default PPP reading to the newer snapshot while the 2017
reading stays reproducible by naming its date.

**Acceptance Scenarios**:

1. **Given** a new re-pricing, **When** it is recorded, **Then** it is a new dated snapshot with its prices and links, and
   no older snapshot is edited.
2. **Given** several snapshots, **When** the GM asks for the history, **Then** the skill lists the dollar value of a koku
   per snapshot.

### Edge Cases

- **No historical price exists** (the gladius problem). Reason from the closest rows - metal, smithing labor, comparable
  weapons elsewhere - and label the result a guess with the chain shown.
- **History disagrees with the canon.** Report both; the GM decides; the canon is never changed silently.
- **The koku's rice mass is unsettled** (40 gallons as recalled, 151.5 kg as the spreadsheet computed, ~180 L
  historically). It is an input with a recorded default, not a hidden constant; answers name the one used.
- **Market rice price against the Imperial rate.** Taxes, rent and stipends use the fixed Imperial rate; a market price is
  an input that floats with harvest and place.
- **Two supportable figures.** Both stay in the ledger as a range or as a knob with a default, not a silent choice.

## Requirements

### Functional Requirements

- **FR-001**: A `/money` skill MUST answer what things cost in Rokugan and what a sum of money is worth.
- **FR-002**: Coin arithmetic MUST follow the canon exactly: 1 koku (gold) = 10 bu (silver) = 100 zeni (copper) = 1,000
  sen; amounts are kept exact (integer sen).
- **FR-003**: Prices MUST be stated in the coins a buyer would actually use, and the skill MUST reflect that koku-scale
  payment in gold is rare and marks noteworthy wealth.
- **FR-004**: The PPP reading of a koku MUST be computed from a dated basket snapshot (goods, quantities, historical
  silver prices, dollar prices and links), and the koku-of-rice mass MUST be an input with a recorded default. The 2017
  snapshot MUST reproduce the spreadsheet's $797.22 / 144.32 zeni / $552.
- **FR-005**: The "big deal" reading of a koku MUST be derived: one koku as a share of an unskilled laborer's year in koku,
  applied to a dated US unskilled full-time year. The wage is an input with a recorded default.
- **FR-006**: The skill MUST keep a price ledger. Every row MUST carry a figure or range, a unit, a label (historically
  accurate / deliberate deviation / guess) and a source pointer (a diagram question file, the canon, or a lead in the GM's
  notes). A test MUST refuse a row without them.
- **FR-007**: Research MUST be requested from the diagram repository by GitHub issue, with the request body of User Story
  3, and taken in by updating ledger rows with pointers to the answering question files. The skill MUST NOT copy diagram's
  research agents or scripts.
- **FR-008**: A finding that contradicts the canon (`setting/l7r.md` "Money", `setting/budgets.md`) MUST go to the GM;
  the skill changes no canon on its own.
- **FR-009**: Updating MUST be by new dated snapshots and dated wages, never by editing old ones and never by a CPI scale.
- **FR-010**: The first research request MUST be opened on `EliAndrewC/diagram` in this feature.

### Key Entities

- **Basket snapshot**: one dated re-pricing of the historical basket - goods, quantities, silver prices, dollar prices,
  links, and the rice price that ties silver to coin.
- **Wage reading**: a dated US unskilled hourly wage and its source, for the "big deal" reading.
- **Ledger row**: an item or service, its figure or range in coin, its unit, label, source pointer and notes.
- **Research request**: a GitHub issue on `EliAndrewC/diagram` and its answer.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The 2017 snapshot reproduces $797.22, 144.32 zeni and $552 per koku to the cent.
- **SC-002**: The "big deal" reading of 1 koku at the default wage is within 1% of the derivation in the handoff (~$9,400).
- **SC-003**: Every ledger row passes the label-and-source test; the digest's anchors are in the ledger as rows.
- **SC-004**: At least one research request is open on `EliAndrewC/diagram` and watched.
- **SC-005**: An item absent from the ledger gets an answer with its derivation shown and labeled a guess.

## Decisions Recorded

| Decision | Why | Recorded at |
|---|---|---|
| Research lives in diagram; the skill cites it | one checked research machinery, no copy to drift (handoff; diagram feature 389) | this spec, SKILL.md |
| Koku rice mass and the wage are inputs with defaults (151.5 kg, $15/hour) | two supportable answers become a knob; both stay OPEN FOR THE GM (the handoff's open items 1-2), and the defaults only keep answers flowing meanwhile | plan.md; raised to the GM at the end of this feature |
| Pure logic in `webapp/l7r/money/`, not in the skill directory | the gate only collects tests under `webapp/` | plan.md |
| No webapp page | bulk and lookup needs belong in chat | plan.md |

## Assumptions

- The GM starts the diagram session that works each request.
- The money folder in the GM's l7r repository is committed by the GM; until then its files are cited by their future
  GitHub path.

## Review history

- **spec-fidelity round 1 (2026-10-18): FAITHFUL.** Aside: the koku rice mass and the "big deal" wage are open questions
  for the GM, not decisions; the Decisions table now says so.
