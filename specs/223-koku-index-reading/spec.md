# Feature 223: The goods-dollar koku as an index - per-good readings, a range, two readings, eras averaged in rice

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

**What moves, so it is seen before it is built**: the skill's single goods-dollar figure and every `goods_dollars` in
the conversion table become the central reading, about $406 a koku against today's $875 (all 23 eras weighted
equally), a fall of a little over half; the method of the old figure survives as the whole-basket (high) reading
beside it, now ~$891 because Rokugan's prices average the eras.

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

### User Story 2 - Two readings side by side: the whole basket and the average over goods (Priority: P1)

The GM's two approaches become two readings, shown together, each coherent on its own terms; together they are the
range.

**Whole basket** (the household year): a laborer's year of necessities, fixed. Its figure is literally *"the year
cost N koku then and $D today, so a koku is $D/N"*, and the page prints N, $D and $D/N. Only the source of today's
price per good can change it (and the choice among complete baskets, today only Standard); switching goods in and out
does not touch it. $D/N is, identically, the spending-weighted arithmetic mean of the single-good kokus, so it is
labeled the high reading.

**Average over goods**: the single-good kokus averaged with a chosen mean - the spending-weighted geometric mean by
default (the central reading), or the spending-weighted arithmetic mean, each with spending weights or equal weights.
Goods can be switched in and out of THIS average, and goods of one's own added to it; the page labels the switches as
choosing which goods enter the average, never as changing what a household bought.

**Acceptance**:
1. Default page: average over goods = weighted geometric mean of all goods (central); whole basket = $D/N (high);
   both shown, each named.
2. The whole-basket figure printed equals $D/N to the cent, and equals the average-over-goods figure when that is set
   to the weighted arithmetic mean with every good on.
3. Switching a good off or adding a custom good changes the average-over-goods figure only; the whole-basket figure
   and its N and $D do not move.
4. Choosing a substitute price changes both.
5. The mean and weighting choices are in the link; reloading reproduces them.
6. When modern quantities exist (diagram#17 question 6), a Paasche reading (low) and Fisher (central, the geometric
   mean of Laspeyres and Paasche) become available and Fisher becomes the default central. Until then the page says
   the low end needs modern quantities, and no Fisher figure is shown.

### User Story 3 - The headline is the range (Priority: P1)

The goods-dollar card shows the central (average-over-goods) figure large and the whole-basket figure beside it as
the high end, e.g. "$407 averaged over goods - $898 for the whole basket", with the wage-dollar card unchanged.

**Acceptance**: no single goods-dollar figure appears on the page without its name (which reading, which mean).

### User Story 4 - Rokugan's prices averaged over the periods the record holds (Priority: P1)

Each good's Rokugani price is the weighted mean, over the eras that price both it and rice, of its price in
kilograms of rice (so debasements and silver's own changing value drop out), anchored to the koku's rice silver. Each
era carries a weight the GM sets.

**Acceptance**:
1. Default: every era held weighs 1 (equal), Chinese and Meiji eras included; this default is PROVISIONAL and is
   reported to the GM as awaiting his weights. Setting only Kyoto 1745-54 to 1 and the rest to 0 reproduces feature
   222's reference prices exactly.
2. The page lists the eras with their weights, which goods each one prices, and a control per era; for each good it
   shows which eras its Rokugani price rests on under the current weights; the link carries non-default weights.
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
- An old feature-222 link (`q_<good>=0`) opens with those goods off in the average-over-goods reading.
- A link weight that does not parse is ignored.

## Requirements

### Functional Requirements

- **FR-001**: For each counted good g: weight w_g = q_g x s_g / sum(q x s) where s is Rokugan's silver price; single-
  good koku r_g = (dollars a unit / s_g) x the koku's silver.
- **FR-002**: Arithmetic reading = sum(w_g x r_g) (identical to feature 222's figure under Kyoto-only weights);
  geometric reading = exp(sum(w_g x ln r_g)). Paasche = 1 / sum(v_g / r_g) with v_g the modern spending shares, and
  Fisher = sqrt(arithmetic x Paasche), only where every counted good has a modern quantity.
- **FR-003**: The mean of the average-over-goods reading is a knob (`geometric` default, `arithmetic`, and
  `fisher`/`paasche` once available - deferred with question 6, not yet in code) with weights `spending` (default) or `equal`, in the link, the CLI (`--mean`,
  `--equal-weights`) and the code, with its why recorded in the code.
- **FR-004**: The two readings of User Story 2 are computed and shown together: the whole-basket reading ($D/N over
  the chosen complete basket with every good, N and $D printed) and the average-over-goods reading (toggles, custom
  goods, mean and weighting). Baskets carry a `complete` flag; only complete baskets feed the whole-basket reading.
  Any basket may be the starting point of the average.
- **FR-005**: Rokugan's silver price of good g = rice_ref x exp(sum_e(W_e x ln(p_eg / p_e,rice)) / sum_e W_e) over
  eras e pricing both; rice_ref stays Kyoto 1745-54's rice silver (the coin anchor). Era weights default 1, overridable
  in the link (`w_<era>=`), the CLI and a data file whose description records the why.
- **FR-006**: The page shows the per-good table (single-good koku, weight), the log-scale strip chart, the range, the
  two readings, the mean choice and the era weights; `money.js` computes the same numbers as the Python (the node
  test extended to every new quantity).
- **FR-007**: `convert` values an era's money as: the era's price level against Rokugan's over goods priced in both,
  by the same mean, then the central dollars a Rokugani gram buys. `conversions.json` adds `goods_dollars_high` and a
  top-level `mean`; nothing is removed.
- **FR-008**: The SKILL.md, the module CLAUDE.md and the page's notes describe goods dollars as an index over goods
  with a range, the two readings, and the era averaging; they cite diagram#17 for what is still open.
- **FR-009**: The 2017 snapshot test keeps reproducing $552.39 (arithmetic, Kyoto-only).
- **FR-010**: User Story 6's re-pricing lands as a new snapshot when diagram#17 answers; this feature's code does not
  wait for it.

### Key Entities

- **Era weight**: era id -> non-negative number; default 1.
- **Rokugan prices**: good -> grams of silver, derived from the eras and their weights (no longer one era's file).
- **Reading**: per-good lines (weight, single-good koku) and the arithmetic, geometric and (when possible) Paasche and
  Fisher figures.
- **Two readings**: whole basket ($D/N) and average over goods (mean, weighting, toggles).

## Success Criteria

- **SC-001**: On the default page the GM can read every good's single-good koku and weight without clicking anything.
- **SC-002**: The headline shows a central figure and a range, each named by its mean.
- **SC-003**: No control on the page changes the whole-basket figure except a price source or a complete basket.
- **SC-004**: Kyoto-only weights with the arithmetic mean reproduce feature 222's $875 (2026-10) and the 2017 $552.39.
- **SC-005**: Browser and server agree on every figure for every tested state.
- **SC-006**: `dom_audit.py` at zero issues and `frontend-review` passes the page.

## Assumptions and decisions

- **Central = weighted geometric mean until modern quantities exist** (then Fisher). Why: with relative prices that
  moved ~100x, the arithmetic mean of base-period weights is dominated by the goods that became dear (housing alone
  contributes $482 of $875) and is the textbook upper bound (Laspeyres overstates against a substitution-aware
  index); the geometric mean is what statistical agencies use for elementary aggregates with substitution, and
  Fisher is the standard "ideal" index when both periods' quantities are known. Diagram#17 question 5 asks what
  economic historians actually do; if it answers differently the default moves. Early answer (diagram#17,
  2026-10-25, leads from diagram feature 420's search passes): none of the works takes one basket index as "the"
  modern value; where consumption differs they compute Laspeyres and Paasche, take the Fisher, and read the
  Laspeyres/Paasche spread as the uncertainty (Allen et al. 2011; Deaton & Heston); published modern-money figures
  are given side by side, each labeled by what it measures (MeasuringWorth; the Bank of Japan's ryo by rice and by a
  carpenter's wage). So the geometric mean over goods is an interim stand-in for Fisher, which question 6's modern
  quantities will allow; the page's two labeled readings follow the side-by-side practice.
- **Era weights default to equal across all 23 eras held, PROVISIONALLY.** The GM: *"how representative we think they
  are of our setting"* - a judgment that is his, so the default is reported to him as awaiting his weights, not
  presented as neutral. It includes 8 Chinese eras (Beijing x5, Canton 1835, Songjiang 1680, Suzhou 1750) and Meiji
  Tokyo 1882. Where each good's default price rests (eras pricing it beside rice): fish on Kyoto 1745, Canton 1835 and
  Tokyo 1882 (so two-thirds non-Tokugawa); housing on Kyoto 1745 and Edo 1818; salt on 9 eras of which 3 Chinese;
  fuel on 11 of which 4 Chinese; soybeans, barley/wheat, oils and cloth mostly on Japanese eras; beans on Kyoto 1745
  and Tokyo 1882 only. Measured over the 2026-10 snapshot: Kyoto-only weights give arithmetic $875 / geometric $370;
  all 23 eras equal give $898 / $407 counting borrowed prices, $891 / $406 without (the shipped rule, below); the 13
  Japanese eras alone (Kyoto, Osaka, Edo, Tokyo) give $924 / $410 counting borrowed prices.
- **A borrowed price is not counted twice.** Diagram confirmed (diagram#17, from 0249) that Bassino & Ma priced Kyoto
  1745's beans, barley and wheat, buckwheat and fish from their early-Meiji ratios to rice, set soybeans equal to rice
  and edible oil equal to lamp oil. Averaged beside Tokyo 1882 they would count one observation twice, so such a
  price carries `borrowed` and is left out of the cross-era mean unless no other weighted era prices the good. Fish
  therefore rests on Canton 1835 and Tokyo 1882 alone by default; beans on Tokyo 1882 alone. Diagram#17 question 4
  will mark the other eras' borrowed and chained prices (several Japanese series chain soybeans and edible oil off
  rice and lamp oil the same way). The
  page shows each good's eras so the GM can see what to reweigh.
- **The mean across eras is geometric and is not the `--mean` knob.** A price in rice is a ratio, and the geometric
  mean is the natural mean of ratios: it treats an era where fish cost twice rice and one where it cost half rice
  symmetrically (the arithmetic mean would not, and would depend on which good is the numeraire). The knob chooses the
  mean across GOODS only.
- **Prices in rice, not silver,** across eras: each era's silver was its own coinage (debasements, the 1700s-1850s
  silver flows), and Rokugan's coin is pegged to rice, so rice is the natural numeraire. Diagram#17 question 5 asks
  whether rice's harvest swings make that unsound; eras are multi-year averages, which damps them.
- **The standard-no-housing and Bassino & Ma baskets stay** (calibration and comparison) but are not marked complete,
  so they never feed the whole-basket reading (any basket may start the average).
- **Custom goods feed only the average-over-goods reading**: adding a good changes what is averaged; the whole basket is
  the household's year as reconstructed.
- **Old links** keep working: their toggles and custom goods now act on the average-over-goods reading.

## Review history

- Round 1 (spec-fidelity, 2026-10-25): CHANGES REQUIRED. (1) the whole-basket framing's $D/N wording sat beside a
  geometric default headline that is not $D/N -> the two framings became two readings shown together, whole basket
  always $D/N; (2) the across-era mean was an unstated geometric choice -> recorded with its why, and it is not the
  knob; (3) equal era weights were called neutral though they include Chinese and Meiji eras -> stated as provisional,
  with each good's eras listed, and the headline's fall disclosed in Why.
