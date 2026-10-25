# Feature 224: Miso and soy sauce in the basket, from the recorded prices

**Feature Branch**: none (main, in a session clone)

**Created**: 2026-10-25

**Status**: Draft

**Input**: `request.md` (the GM's words, 2026-10-25)

## Why

The standard basket's 52 kg of soybeans a year stands for miso, soy sauce, tofu and natto, but is priced as whole
beans from a wholesale Osaka table that Bassino & Ma equated with rice. The Mitsui house's own account books record
miso and soy sauce at retail in seven of our periods (Kyoto 1745, 1790, 1800; Edo 1818, 1830, 1850, 1860; diagram
0303). The GM ruled: *"switch the basket to the recorded prices"*, by the split he approved (`request.md`).

## User Scenarios & Testing

### User Story 1 - The basket holds miso and soy sauce (Priority: P1)

The GM opens `/money/koku` and sees Miso and Soy sauce as goods of the standard basket beside a smaller Soybeans line,
each with its single-good koku, weight, today's US price and the periods behind its Rokugani price.

**Acceptance**:
1. The standard basket holds 39 kg of miso, the soy sauce of FR-002 and 34.4 kg of soybeans a year, and nothing else
   in it changes.
2. Miso's and soy sauce's Rokugani prices rest on the seven Mitsui periods, each footnoted with its research link.
3. Both readings (averaged over goods, whole basket) move, and the page, the skill and the conversion table quote the
   new range.

### User Story 2 - Today's prices for the new goods, and the promised alternatives (Priority: P2)

**Acceptance**:
1. A new dated snapshot prices miso (default the cheapest plain pack, Shirakiku white, 2 kg for $21.28: $10.64 a kg;
   alternatives Shirakiku red $11.83 and Walmart's cheapest, Hikari, $16.73) and soy sauce (default Great Value
   Naturally Brewed, $3.90 a liter; alternative Kikkoman, $6.86), each with its listing link (diagram 0299).
2. It carries every 2026-10 option unchanged, plus alternatives (never defaults): all-purpose flour for barley and
   wheat ($0.95 a kg), canned sardines for fish ($13.36 a kg), and for housing the median asking rent per m² (two
   readings, $182 and $132; diagram 0300) and Allen's poverty-line rent (about $25 a m² a month, $300 a year;
   diagram 0298). The 2026-10 snapshot is not edited.
3. The new snapshot sorts after 2026-10 and becomes the page's prices.

### Edge Cases

- The 2017 snapshot cannot price miso or soy sauce: the standard basket at 2017 lists them as not priced, and the 2017
  sheet's pinned $552 (basket A, Kyoto alone) is unchanged.
- A period that records soybeans but not miso still prices the Soybeans line; miso rests only on periods that record
  miso. The basket is the same in every period (GM, 2026-10-25).

## Requirements

- **FR-001**: Goods `miso` (kg) and `soy-sauce` (liter) exist; Soybeans' description becomes whole beans for tofu,
  natto and eating.
- **FR-002**: Quantities, each with its basis recorded where the basket lives:
  - miso: 13 kg of beans (the middle of 9.0 kg, Hirosaki 1816, and 16.8 kg, 家訓全書 1760; diagram 0303) times
    3 kg of miso a kg of dry beans (modern rice-koji home recipes, koji at or below the beans; 0303) = 39 kg;
  - soy sauce: 4.6 kg of beans (廣益國産考 1844; 0303) times a yield. **PENDING THE GM'S RULING**: no cited
    food-science or industry source states liters of soy sauce a kg of beans (0303: "no source read states liters a
    kilogram of soybeans"), so the condition he approved ("a modern yield from a cited food-science or industry
    source") is unmet for soy sauce. The candidate put to him: diagram's own upper-bound arithmetic from Oguri 2008's
    proportions and Noda's press yield, 3.0-3.4 L a kg (13.8-15.6 L a year). (Edo's 1821 soy sauce arrivals are not
    a cross-check: 0303 leaves them out, since no readable page names their document and no 1821 population is
    held.) The 4.6 kg of beans comes out of the soybean line whatever the yield;
  - soybeans: 52 - 13 - 4.6 = 34.4 kg.
  The same split applies to "Standard, no housing".
- **FR-003**: The seven Mitsui periods price miso (monme for 10 kan) and soy sauce (monme a koku) from 0303's cells,
  chained to Kyoto 1745-54's own cells like every Mitsui good; Kyoto 1745 records both (label historical). Thinner
  cells are declined, with the reason in the era script: osaka-1712's single autumn-1713 Osaka cell, osaka-1706's
  Edo cells, osaka-1620's "Soya" (soy sauce only by reading), tokyo-1882's 1887 "Soy".
- **FR-004**: A snapshot dated 2026-10-25 per User Story 2. Snapshots sort by date, so a day-dated snapshot follows
  its month's.
- **FR-005**: The conversion table, page, money skill and memory are regenerated or updated; diagram is told on
  diagram#18 that `conversions.json` changed.

## Not in scope

- Edo 1860-67's oils: 0304 ties them to the opening only for 1859-60 of the era's eight years, so they stay counted;
  reported to the GM.
- Fisher (US quantities for soybeans and cloth are SILENT).

## Success Criteria

- **SC-001**: the gate passes; the 2017 sheet's $552 is unchanged.
- **SC-002**: the live page lists Miso and Soy sauce with seven footnoted periods each, and the headline range is the
  regenerated one.

## Review history

- 2026-10-25, spec-fidelity round 1: CHANGES REQUIRED. (1) The soy sauce yield of 3.0 L a kg was the session's own
  choice on diagram's arithmetic, where the GM approved only a cited modern yield: now pending his ruling. (2) The
  kept `standard-soybeans` basket was unrequested (Bassino & Ma's basket survives as `bassino-ma-a`): removed. Ruled
  in scope: the snapshot's alternatives, and the same split for "Standard, no housing".
