# Feature 227: Researched, Extrapolated, Estimated

**Feature Branch**: none (main, in a session clone)

**Created**: 2026-10-26

**Status**: Draft

**Input**: `request.md` (the GM's words, and his "yes please" to the definitions)

## Why

Every money ledger price that is not researched carries one label, `guess`, shown as "Guess". The GM sees two
different things under it: a price carried over from research on a close relative (*"a direct extrapolation"*), and a
price reasoned up from the model, which he would call *"Estimated"*, since even the true guesses are reasoned.

## The tiers (as proposed and accepted)

- **Researched** (`historical`): the record prices this good itself, possibly in a nearby place or period.
- **Extrapolated** (`extrapolated`): no price for this exact item, but a researched price for a close relative is
  carried over by a stated rule: a unit conversion, a ratio the research gives, scaling by size or distance, the same
  good in China.
- **Estimated** (`estimated`): built from the model (materials, labor-days, neighboring goods), with no researched
  price of its own kind.

`deviation` (departs from history on purpose) and `comparative` (another society) are unchanged.

## User Scenarios & Testing

### User Story 1 - The price sheets show three tiers (Priority: P1)

**Acceptance**:
1. Every item on `/money/prices` carries one of Researched, Extrapolated, Estimated (or Departs from history), each
   badge distinct without relying on color, and the key explains all three in the words above.
2. The Fox shrine-grade charcoal rows read Extrapolated.

### User Story 2 - The ledger holds the tiers (Priority: P1)

**Acceptance**:
1. The label `guess` no longer exists in the ledger; each of its 167 rows is reclassified by its own basis, by the
   definitions above, not by its source field alone (a row sourced to a research page whose notes say the research is
   SILENT and the price is kept from the model is Estimated).
2. An `extrapolated` row must cite the research it carries over (a research question page as its source, or one
   named in its notes); the ledger check fails otherwise.
3. The money skill (`price`, its docs) and the research intake rule use the new labels.

## Edge Cases

- The shrine builder's lines are relabeled in the ledger like every row; the shrine builder does not show labels.
- Canon figures nobody has checked against history (rent and tax caps, hay) are Estimated with a `canon:` source.
- The era price files keep their own `historical`/`guess` labels (a separate scheme, not shown as badges); out of
  scope.

## Success Criteria

- **SC-001**: no `guess` label in the ledger; the gate passes; the live sheets show the three badges.
