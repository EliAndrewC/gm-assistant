# Feature 225: Price sheets on the Money section

**Feature Branch**: none (main, in a session clone)

**Created**: 2026-10-25

**Status**: Draft

**Input**: `request.md` (the GM, 2026-10-25, verbatim)

## Why

The money skill's ledger holds ~90 Rokugani prices for common goods and services, plus wages and incomes, each with a
range, a label (researched or guessed), a source and notes. Today they can be read only through the skill's command
line. The GM wants *"price sheets for common goods and such, with price ranges for each item. With some kind of
organization"*, a page beside "What's a koku worth?", and wages and incomes on it *"when we have it"*. Wages and
incomes are already in the ledger (the unskilled and skilled day, the 2026-10-25 guesses for clerks, servants, a smith
and entertainers), so they go in now.

## User Scenarios & Testing

### User Story 1 - Read the price sheets (Priority: P1)

The GM opens `/money/prices` from the Money section and sees the ledger's prices grouped into sheets by kind (food and
drink, lodging and travel, housing and rent, land, clothing and cloth, entertainment, paper and books, tools and
weapons, fuel, offerings, wages and incomes), each item with its price range in the coins a buyer would hand over and
the unit it buys.

**Acceptance**:
1. Every synthesis row of the ledger that is not a shrine-builder line appears on exactly one sheet, in a fixed order
   of sheets, cheapest first within a sheet. A **shrine-builder line** is a row tagged both `construction` and
   `shrine` (the shrine builder's 104 line items); the tag `shrine` alone is not the test, so the Fox shrine-grade
   charcoal rows (tagged `fuel`, `charcoal`, `shrine`) go on the fuel sheet.
2. Each item shows its range in everyday coins (`3-5 zeni`, `about 1 koku 5 bu`), the unit (per night, per item, per
   year), and its range in laborer-days, so its size is felt without converting.
3. Each item shows how solid it is: **researched** (label historical), **guess**, or **departs from history** (label
   deviation); a historical row resting on an unverified lead says so.
4. Opening an item shows its notes (the basis) and a link to its source: the diagram research page, the canon section,
   or the logged estimate it came from.
5. A sheet whose goods carry a swing note (salt, rice, wages, ...) shows it once, under the sheet: how much the good's
   price moved across periods, and why.

### User Story 2 - Wages and incomes (Priority: P1)

**Acceptance**: a "Wages and incomes" sheet lists every wage and income row (day wages, yearly wages, a smith's and a
troupe's takings), each with its range, and in **wage dollars** (how much it matters) where the other sheets give
**goods dollars** (what it buys), each reading named.

### User Story 3 - Find an item (Priority: P2)

**Acceptance**: a contents list jumps to each sheet; a filter box narrows every sheet to items whose name or notes
contain the words typed, and says when nothing matches. Without JavaScript every sheet is shown in full.

### User Story 4 - The page belongs to the Money section (Priority: P2)

**Acceptance**: the Money landing page lists "Price sheets" beside "What's a koku worth?"; the page says what the
ranges mean (a range is the spread of the evidence or the guess, not a haggling margin), that a koku is 1,000 sen, and
links "What's a koku worth?" for the dollar readings. Shrine-building prices are not repeated; the page links the
shrine builder for them.

### Edge Cases

- A ledger row with no tag that maps to a sheet: the gate fails, naming the row, so no price silently disappears.
- Comparative rows (other societies) and source rows (no `id`) are never shown as Rokugani prices.
- A one-figure row (low = high) shows a single price, not "13-13 sen".

## Requirements

- **FR-001**: Sheets are derived from the ledger at request time (no copy of the prices is kept); the tag-to-sheet map
  lives in code with the first matching sheet winning, and a test asserts both directions: every eligible row lands on
  exactly one sheet, and the Fox shrine-grade charcoal rows are among them on the fuel sheet.
- **FR-002**: Coins by `coins.everyday`; laborer-days at the unskilled day; goods dollars at the central reading
  (averaged over goods), wage dollars for the wages sheet, both from the money skill's own conversion.
- **FR-003**: Screenshots, `dom_audit` at zero issues and `frontend-review` before it ships (Principle I).

## Success Criteria

- **SC-001**: every synthesis row that is not a shrine-builder line is on the page; the gate passes.
- **SC-002**: the live page shows the sheets, and the landing page links it.

## Review history

- 2026-10-25, spec-fidelity round 1: CHANGES REQUIRED. "Shrine-builder line" was undefined, and filtering on the tag
  `shrine` would have dropped the 11 Fox shrine-grade charcoal prices, ordinary fuel. Now defined as tagged both
  `construction` and `shrine`, with a test in both directions. Ruled faithful: the shrine lines linked rather than
  repeated, wages and incomes now, dollar readings and laborer-days, the filter and swing notes.
- 2026-10-25, spec-fidelity round 2: FAITHFUL.
