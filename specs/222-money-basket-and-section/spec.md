# Feature 222: A standard basket, today's prices, a conversion table, and the Money section

**Feature Branch**: none (main, in a session clone)

**Created**: 2026-10-24

**Status**: Draft

**Input**: `request.md` (the GM, 2026-10-24, three messages, verbatim)

## Why

The skill's purchasing-power reading of a koku is $552 *in 2017 dollars*, which the GM finds *"not really helpful
considering how much inflation has happened since then"*. He wants it re-priced, and re-priceable: *"some kind of
scripted or automated process that we are able to just kind of update"*, *"extensible"* enough to *"run it for
different baskets of goods"* and see *"how much does it move the numbers if you count this other thing"*.

He also wants every historical amount of money on diagram's research site to carry a conversion (*"`20 mon` is worth
$X in purchasing power parity terms, $Y in modern labor terms, some amount of Rokugani money"*), which needs *"some
basket of goods that we have standardized on, that is our like main one, that we think is representative"*, costed in
*"different time periods in the history of the places that we have researched"*, so the conversions *"make sense
without just being totally hand-wavy, even if they are approximate"*. The basket's contents need thought: *"salt ...
might be something that needs to be there, because that is an essential thing that people need, as opposed to
something like pepper"*.

And he wants a Money section on the GM Assistant site whose first tool is *"the how much is a koku worth tool that
lets you play with that and kind of add or remove things from the basket"*, with *"other things on the money section
of the site"* to come.

The split agreed in the conversation: the basket design, today's prices, the engine, the conversion table and the site
section are done HERE; each era's historical prices, coin rates and wages, and the tooltip on the research site, are
diagram's, asked for by GitHub issue.

## User Scenarios & Testing

### User Story 1 - A koku in today's dollars (Priority: P1)

The GM asks what a koku buys and gets a figure in current dollars, from a basket re-priced this month, not a 2017
figure.

**Independent Test**: `python3 -m l7r.money convert 1 koku` names a 2026 snapshot and the standard basket; `--snapshot
2017-04 --basket bassino-ma-a` still prints $552.39.

**Acceptance Scenarios**:
1. **Given** the 2026 snapshot, **When** a koku is converted, **Then** the goods-dollar reading uses the standard basket
   priced in 2026 and names both.
2. **Given** the 2017 inputs, **When** they are selected, **Then** the reading reproduces the spreadsheet's $552.39.

### User Story 2 - Re-pricing is a command, not a project (Priority: P1)

Next year a session runs one command, fills in a price and a link for each good, and the new month becomes the
default.

**Acceptance Scenarios**:
1. **Given** the newest snapshot, **When** `reprice YYYY-MM` runs, **Then** it writes a new snapshot file with every
   good of every basket listed and its price blank, and refuses to let `check` pass until each has a price and a link.
2. **Given** a snapshot, **When** `crosscheck` runs, **Then** it compares the snapshot's rice and dried-bean prices with
   the US Bureau of Labor Statistics average retail prices for the same month and flags a gap of more than half.

### User Story 3 - A standard basket, and others beside it (Priority: P1)

The standard basket is a documented choice: each good's inclusion or exclusion, its quantity and both of its prices
carry a source or are labeled a guess. Alternate baskets (the 2017 one, and variants that add or drop a good) are named
data files that every command and the site can use.

**Acceptance Scenarios**:
1. **Given** the standard basket, **When** it is listed, **Then** salt, fuel and housing are in it, a luxury such as pepper is
   not, and each good shows its source or its guess label.
2. **Given** two baskets, **When** `baskets` runs, **Then** it prints each one's dollars per koku side by side for the
   chosen snapshot.

### User Story 4 - A conversion table for historical money (Priority: P1)

For each era and place with data, an amount of its money converts to goods dollars, wage dollars and Rokugani coin.
The table is a committed, generated file diagram's site can read.

**Acceptance Scenarios**:
1. **Given** Kyoto 1745-54, **When** 20 mon is converted, **Then** it gives goods dollars, wage dollars and a Rokugani
   sum in sen, zeni, bu and/or koku, with the era, its coin rate and its confidence named.
2. **Given** an era whose basket is only partly priced, **When** it converts, **Then** it says which reading it falls
   back on (rice alone, or the goods it has) rather than presenting it as a full-basket figure.
3. **Given** the committed table, **When** the gate runs, **Then** it fails if the table differs from what the engine
   generates.

### User Story 5 - The Money section and "What's a koku worth?" (Priority: P1)

A visitor opens Money on the toolkit, sees a landing page with the tool as its first entry, and in the tool toggles
goods in and out, edits quantities, switches baskets and price snapshots, adds a custom good, and watches the koku's
dollar value and each good's share change.

**Acceptance Scenarios**:
1. **Given** the page, **When** it opens, **Then** it shows the standard basket at the newest snapshot, the koku in goods
   dollars and in wage dollars, and each good's quantity, both prices and share of the cost.
2. **Given** a change (a good off, a quantity, a substitute, a basket, a snapshot, a custom good), **When** it is made, **Then** the
   readings update at once and the link carries the change, so the link reopens the same variant.
3. **Given** a variant, **When** Reset is pressed, **Then** the standard basket returns.

### User Story 6 - Diagram is asked (Priority: P1)

The research the conversions need is filed on diagram as issues: the historical prices of the new goods, each era's
basket cost, wages and coin rates, and the tooltip.

### Edge Cases

- A good with no historical price cannot enter a basket's ratio: it is shown as unpriced and left out of the sum, and
  the page and commands say so.
- A snapshot older than a basket's newest good has no dollar price for that good: the same rule.
- A custom good in the tool needs both prices; until both are entered it is shown and not counted.
- A quantity of zero is the same as switching the good off.

## Requirements

### Functional Requirements

**Baskets and prices**
- **FR-001**: Basket COMPOSITION (goods, quantities per adult per year, the historical price in grams of silver of each,
  with source or guess label) is stored apart from dated DOLLAR SNAPSHOTS (per good: dollars per unit, link, what it
  was priced as).
- **FR-002**: A standard basket is designed from the welfare-ratio literature (Bassino & Ma 2005; Allen et al. 2011),
  adding what Rokugan's commoners need to live (salt; fuel; housing) and excluding luxuries, with the reason for each inclusion
  and exclusion recorded with the data. It is the default.
- **FR-003**: The 2017 basket survives as the named basket `bassino-ma-a`, and the 2017 snapshot read through it
  reproduces $552.39.
- **FR-004**: A 2026 snapshot prices every good of every shipped basket at US bulk retail, with a link per good.
- **FR-005**: `reprice YYYY-MM` starts a new snapshot from the newest; `check` refuses a snapshot with a good unpriced
  or unlinked.
- **FR-006**: `crosscheck` compares a snapshot's rice and dried beans with BLS average retail prices (tested against a
  saved response).
- **FR-007**: Alternate baskets are data files; `baskets` compares them; every reading command takes `--basket`.
- **FR-008**: The standard basket includes housing, as the GM approved (*"salt, fuel and housing in"*). A named variant
  without housing ships beside it, and every place that quotes the standard koku can show what housing adds.

**Readings and names**
- **FR-009**: The second reading is renamed from "big deal" dollars to **wage dollars** everywhere (commands, skill,
  docs), paired with **goods dollars**.

**The conversion table**
- **FR-010**: An era is a data file (a new era is a new file, never a code or spec change): its place and years, its coins in grams of silver (with source), the standard
  basket's cost there (whole, partial with the goods named, or rice only), an unskilled day wage, and a confidence.
- **FR-011**: An amount of an era's money converts to goods dollars, wage dollars and a Rokugani sum in sen, zeni, bu
  and/or koku (through the ratio of the era's basket cost to Rokugan's), and names what each rests on.
- **FR-012**: The first eras are the ones already sourced: Kyoto 1745-54 and Tokyo 1882-86 (Bassino & Ma).
- **FR-013**: `export` writes the conversion table as committed JSON; a test fails if it is stale.

**The site**
- **FR-014**: A Money section in the toolkit's nav and on the landing page, with a landing page that lists its tools
  (one for now) and room for more.
- **FR-015**: "What's a koku worth?": per good a toggle, an editable quantity, both prices and its share, and a choice
  among its named substitutes (what today's dollar price is taken from: medium- against long-grain rice, cloth by the
  running meter against cloth of a Japanese bolt's width); a basket picker, a snapshot picker, a custom good (name, unit, quantity, silver price, dollar price), both readings live, Reset,
  and the whole state in the URL.
- **FR-016**: The page computes in the browser from data the server embeds; the server renders the same numbers for the
  default state, and a test holds the two to the same arithmetic.
- **FR-017**: The section is public, like Dreams and Names: nothing on it is GM-only.

**Diagram**
- **FR-018**: A research issue on diagram (up to four questions): the new goods' Kyoto 1745-54 prices; and, for EVERY era
  and place its price research draws on (the Edo periods beyond 1745-54, each Chinese dynasty used - Qing at least, and
  Ming and Song where the record has prices), the standard basket's cost as far as the sources allow, an unskilled
  wage, and the coin rates. A second issue asks for the tooltip, reading the conversion table.

## Success Criteria

- **SC-001**: A koku's goods-dollar value is quoted in 2026 dollars, and every figure in it traces to a dated link.
- **SC-002**: Re-pricing next year is `reprice`, filling one file, `check`.
- **SC-003**: The GM can see in the tool how much fish, housing or any good moves the koku.
- **SC-004**: Diagram has what it needs to build the tooltip without asking gm-assistant again.

## Assumptions and decisions

- **Basket quantities are per adult per year**, as in both papers; the koku reading is a ratio, so the scale cancels.
- **Housing is in the standard basket**, as the GM approved. It nearly doubles the koku (research.md has the numbers),
  so the no-housing variant is shipped and the size of the difference is reported to the GM; it is his to change.
- **New goods' historical prices start as labeled guesses** from the nearest sourced figures (diagram's salt and
  charcoal questions, Allen's Beijing fuel), and diagram is asked to replace them.
- **The section is public** (FR-017); cheap to change.

## Review history

- **Round 1** (spec-fidelity, 2026-10-24): CHANGES REQUIRED. (1) Housing had been moved out of the standard basket the GM
  approved - reversed: housing is in, the no-housing basket is the variant (FR-008); (2) the approved substitute swap was
  missing - added to FR-015 and User Story 5; (3) the eras were narrowed to the two already sourced - FR-018 now asks for
  every era and place diagram's price research uses (later Edo, Qing, Ming, Song where it has prices) and FR-010 takes
  new eras as data files; (4) the Rokugani sum is named as sen, zeni, bu and/or koku (FR-011, User Story 4).
- **Round 2** (spec-fidelity, 2026-10-24): **FAITHFUL** - all four carried, nothing else drifted.
