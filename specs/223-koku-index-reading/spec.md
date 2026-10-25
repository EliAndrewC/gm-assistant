# Feature 223: The goods-dollar koku as an index - per-good readings, a range, two framings, eras averaged in rice

**Feature Branch**: none (main, in a session clone)

**Created**: 2026-10-25

**Status**: Draft

**Input**: `request.md` (the GM, 2026-10-25, two messages verbatim, and the proposal he approved)

## Why

The GM read the koku playground (`/money/koku`, feature 222) as adding each ticked good's dollars to the koku, and
judged that *"a mixture of the two [approaches] that invalidates both"*. The arithmetic was in fact already a
weighted average (basket dollars over basket silver is the spending-weighted arithmetic mean of each good's own
reading, a Laspeyres index), but his conclusions stand:

- the readings of single goods spread over two orders of magnitude (cloth $36, rice $191, housing $4,384), so *"what
  a koku is worth"* has no single answer, and the page showed one confident figure that hid the spread and the
  choice of mean that produced it;
- the toggles suit *"some kind of average"* over goods but not *"this basket of goods consumed over the course of a
  year"*, where *"excluding things that we know that would have been used invalidates the calculation"*;
- Rokugan's prices came from one period, Kyoto 1745-54, where *"we will probably have some kind of weighted average
  of the pre-modern prices that uses the different periods and how representative we think they are of our setting
  ... we should do that no matter what"*.

He approved the proposal in `request.md`: per-good table, a range headline with the mean as a knob, two framings,
era averaging in rice terms, and research questions to diagram (filed as diagram#17).

## User Scenarios & Testing

### User Story 1 - See what a koku buys good by good (Priority: P1)

The GM opens `/money/koku` and sees, for each good, what a koku's worth buys of that good alone, priced today (the
single-good koku: rice $191, cloth $36, housing $4,384, ...) and how much that good weighs in the average (its share
of a year's spending at Rokugan's prices). The spread is visible at a glance on a chart.

**Acceptance**:
1. Every good priced on both sides shows its single-good koku and its weight; weights sum to 100%.
2. Rice's single-good koku equals the koku's rice mass times today's chosen rice price (151.5 kg x $1.26 = $191).
3. A chart places every good's single-good koku on one axis (log scale, since they span ~100x), sized by weight, with
   the central and high readings marked.

### User Story 2 - A headline that is a range, with the mean named (Priority: P1)

The headline goods-dollar figure is the central reading, with the range beside it, each labeled by the mean that
produced it: the weighted geometric mean (central) and the weighted arithmetic mean (high, the household-basket
reading). The visitor can pick which mean is the headline.

**Acceptance**:
1. Default: central = weighted geometric mean, high = weighted arithmetic mean; both shown.
2. Choosing the arithmetic mean makes it the headline; the link carries the choice and reloading reproduces it.
3. When a snapshot carries modern quantities (diagram#17 question 6), a Paasche reading (low) and the Fisher index
   (central, the geometric mean of Laspeyres and Paasche) become available and Fisher becomes the default central.
   Until then the page says the low end needs modern quantities, and no Fisher figure is shown.

### User Story 3 - Two framings, each coherent (Priority: P1)

**Whole basket** (the default): a laborer's year of necessities is fixed; no good can be switched off, only the source
of today's price chosen. Its figure is read as *"the year cost N koku then and $D today, so a koku is $D/N"* and the
page says so, with N and $D shown.

**Average over goods**: goods can be switched in and out and goods of one's own added; the page labels this as
choosing which goods enter the average, not as changing what a household bought.

**Acceptance**:
1. In whole-basket framing no good has an on/off control and custom goods are not offered; only baskets marked
   complete are offered (today: Standard).
2. In average-over-goods framing every good has an on/off control, any basket may be the starting weights, custom
   goods are offered, and the copy names it an average.
3. The framing is in the link.

### User Story 4 - Rokugan's prices averaged over the periods the record holds (Priority: P1)

Each good's Rokugani price is the weighted mean, over the eras that price both it and rice, of its price in
kilograms of rice (so debasements and silver's own changing value drop out), anchored to the koku's rice silver. Each
era carries a weight the GM sets.

**Acceptance**:
1. Default: every era held weighs 1 (equal). Setting only Kyoto 1745-54 to 1 and the rest to 0 reproduces feature
   222's reference prices exactly.
2. The page lists the eras with their weights, which goods each one prices, and a control per era; the link carries
   non-default weights.
3. An era that prices only rice contributes nothing and the page says so.
4. The CLI and the conversion table use the same weights.

### User Story 5 - The skill and the conversion table follow (Priority: P1)

`python3 -m l7r.money dollars` prints the central reading with its range and the mean used; `era` conversions value
an era's money by the central reading; the conversion table diagram reads keeps `goods_dollars` (now the central
reading) and adds `goods_dollars_high`. The skill's SKILL.md explains the readings as an index with a range.

**Acceptance**:
1. The 2017 calibration still reproduces $552.39 with the arithmetic mean and Kyoto-only weights.
2. `conversions.json` keeps every existing field; diagram is told on diagram#17 what moved.

### User Story 6 - Like-for-like modern prices (Priority: P2, waits on diagram#17)

When diagram#17 answers which modern product matches each historical good and at what market level, a new dated
snapshot re-prices the mismatched goods (soybeans, wheat, millet, fish, and housing's comparator); old snapshots are
never edited.

**Acceptance**: a new snapshot exists, `check` passes, and the per-good spread is re-measured and reported to the GM.

### Edge Cases

- A good priced on only one side (or a custom good missing a price) is left out and named, never counted at zero.
- A good with zero weight after toggles is left out of both means.
- All era weights zero: the page falls back to the reference era alone and says so (never divides by zero).
- An old feature-222 link (`q_<good>=0` without a framing) opens in average-over-goods framing, so the link still
  reproduces the goods it chose.
- A link weight that does not parse is ignored.

## Requirements

### Functional Requirements

- **FR-001**: For each counted good g: weight w_g = q_g x s_g / sum(q x s) where s is Rokugan's silver price; single-
  good koku r_g = (dollars a unit / s_g) x the koku's silver.
- **FR-002**: Arithmetic reading = sum(w_g x r_g) (identical to feature 222's figure under Kyoto-only weights);
  geometric reading = exp(sum(w_g x ln r_g)). Paasche = 1 / sum(v_g / r_g) with v_g the modern spending shares, and
  Fisher = sqrt(arithmetic x Paasche), only where every counted good has a modern quantity.
- **FR-003**: The mean is a knob (`geometric` default, `arithmetic`, and `fisher`/`paasche` once available), in the
  link, the CLI (`--mean`) and the code, with its why recorded in the code.
- **FR-004**: Two framings (`whole` default, `goods`) as in User Story 3; baskets carry a `complete` flag; the
  whole-basket framing shows N koku and $D for the year.
- **FR-005**: Rokugan's silver price of good g = rice_ref x exp(sum_e(W_e x ln(p_eg / p_e,rice)) / sum_e W_e) over
  eras e pricing both; rice_ref stays Kyoto 1745-54's rice silver (the coin anchor). Era weights default 1, overridable
  in the link (`w_<era>=`), the CLI and a data file whose description records the why.
- **FR-006**: The page shows the per-good table (single-good koku, weight), the log-scale strip chart, the range, the
  framing switch, the mean choice and the era weights; `money.js` computes the same numbers as the Python (the node
  test extended to every new quantity).
- **FR-007**: `convert` values an era's money as: the era's price level against Rokugan's over goods priced in both,
  by the same mean, then the central dollars a Rokugani gram buys. `conversions.json` adds `goods_dollars_high` and a
  top-level `mean`; nothing is removed.
- **FR-008**: The SKILL.md, the module CLAUDE.md and the page's notes describe goods dollars as an index over goods
  with a range, the two framings, and the era averaging; they cite diagram#17 for what is still open.
- **FR-009**: The 2017 snapshot test keeps reproducing $552.39 (arithmetic, Kyoto-only).
- **FR-010**: User Story 6's re-pricing lands as a new snapshot when diagram#17 answers; this feature's code does not
  wait for it.

### Key Entities

- **Era weight**: era id -> non-negative number; default 1.
- **Rokugan prices**: good -> grams of silver, derived from the eras and their weights (no longer one era's file).
- **Reading**: per-good lines (weight, single-good koku) and the arithmetic, geometric and (when possible) Paasche and
  Fisher figures.
- **Framing**: whole basket or average over goods.

## Success Criteria

- **SC-001**: On the default page the GM can read every good's single-good koku and weight without clicking anything.
- **SC-002**: The headline shows a central figure and a range, each named by its mean.
- **SC-003**: In whole-basket framing there is no way to switch off a good.
- **SC-004**: Kyoto-only weights with the arithmetic mean reproduce feature 222's $875 (2026-10) and the 2017 $552.39.
- **SC-005**: Browser and server agree on every figure for every tested state.
- **SC-006**: `dom_audit.py` at zero issues and `frontend-review` passes the page.

## Assumptions and decisions

- **Central = weighted geometric mean until modern quantities exist** (then Fisher). Why: with relative prices that
  moved ~100x, the arithmetic mean of base-period weights is dominated by the goods that became dear (housing alone
  contributes $482 of $875) and is the textbook upper bound (Laspeyres overstates against a substitution-aware
  index); the geometric mean is what statistical agencies use for elementary aggregates with substitution, and
  Fisher is the standard "ideal" index when both periods' quantities are known. Diagram#17 question 5 asks what
  economic historians actually do; if it answers differently the default moves.
- **Era weights default to equal.** The GM: *"how representative we think they are of our setting"* - a judgment that is
  his; equal is the neutral starting point, and the knob is his. Measured: equal weights move the arithmetic reading
  $875 -> $898 and the geometric $370 -> $407 (relative prices in rice are steady across the Japanese eras), so the
  default does not swing the headline.
- **Prices in rice, not silver,** across eras: each era's silver was its own coinage (debasements, the 1700s-1850s
  silver flows), and Rokugan's coin is pegged to rice, so rice is the natural numeraire. Diagram#17 question 5 asks
  whether rice's harvest swings make that unsound; eras are multi-year averages, which damps them.
- **The standard-no-housing and Bassino & Ma baskets stay** (calibration and comparison) but are not marked complete,
  so they appear only in average-over-goods framing.
- **Custom goods only in average-over-goods framing**: adding a good changes what is averaged, which is that
  framing's purpose.
- **Old links** open in average-over-goods framing when they carry a toggle, so they reproduce what they chose.

## Review history

(spec-fidelity rounds recorded here)
