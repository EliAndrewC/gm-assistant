# Keeping the money skill up to date

Load this file when: re-pricing the basket, re-taking the wage, or settling one of the open knobs.

The GM wants the skill to *"keep up to date and keep track of so that we can update it periodically"*. Every dollar
reading rests on dated inputs, so updating is adding a new dated input - never editing an old one.

## Re-pricing the basket (goods dollars)

**Re-price, never scale by the CPI.** Rice and beans move differently from the CPI; scaling 2017's figure would carry
2017's relative prices forward under a new date (handoff, 2026-10-18).

The data is split three ways (feature 221; `webapp/l7r/money/basket.py` explains why): `data/baskets/` is what is
bought, `data/snapshots/YYYY-MM.json` is what each good cost in dollars that month, `data/eras/` is what it cost in
silver at a place and time. Re-pricing touches only snapshots.

1. From your clone's `webapp/`: `python3 -m l7r.money reprice YYYY-MM`. It writes the new snapshot with every good of
   every basket and each option of the last snapshot; the options tied to a BLS average-price series (rice, beans) come
   filled from FRED's newest month, the rest blank.
2. Fill each blank `dollars_per_unit` and `link`, and set `priced_by` and `source`. Same rule as before: the cheapest
   plain version in an ordinary household bulk pack (about 2-25 lb) from a national retailer, per the good's unit (the
   pricing rule and each good's unit conversions are in `specs/221-money-basket-and-section/research.md`). An option is
   a substitute the playground can swap in; keep the first as the default.
3. `python3 -m l7r.money crosscheck` sets each priced option beside the BLS average; a line marked "check this price"
   is under half or over twice it (adzuki always is: a specialty bean in the US).
4. `check` refuses the file until every option is priced and linked. Then `export` (the conversion table moves with
   the snapshot; a test fails if it is stale), `history`, and the gate. Never edit an older snapshot:
   `--snapshot 2017-04 --basket bassino-ma-a` must keep reproducing $552.39.

## Changing a basket, or adding an era

- A basket is `data/baskets/<id>.json`; a new one is a new file and shows up in `baskets`, `--basket` and the site.
  Changing `standard` changes every default reading: record the reason in the file's description and in the spec.
- An era is `data/eras/<id>.json` (place, years, coins in grams of pure silver, each good's silver price with label and
  source, an unskilled day wage). Diagram's research answers arrive this way; then `export`. Exactly one era is the
  `reference` (Kyoto 1745-54): Rokugan's prices are its prices.

## Re-taking the wage (wage dollars)

Append a reading to `webapp/l7r/money/data/wages.json` (`date`, `hourly`, `hours_per_year`, `basis`, `source`). The
newest is the default; `--wage-date` reaches older ones.

## The laborer's year

`LABORER_KOKU_YEAR` (3.32) and `WORKING_DAYS` (250) in `webapp/l7r/money/readings.py` are the 2017 sheet's figures.
Diagram 0250: ~2 kg of rice a day is attested; the 250-day year is a modern convention. A future count of working days
would change them; the two wage rows cite 0250. Every wage-dollar figure and every laborer-days count moves with them.

## The basket against its source

Diagram 0249 checked the 2017 snapshot against Bassino & Ma's Tables 1 and 3: every quantity and silver price matches
(325.816 g). The paper's labels are "Beans (excluding soybeans)" and "Linen (m)" (the snapshot says adzuki and
cotton), and only rice and lamp oil were recorded in Kyoto 1745-54; the rest are the paper's reconstructions. Cite
the published copy: https://www.econhistdbm.com/uploads/8/1/9/7/81977286/reh_japanese_wages_bassino_and_ma.pdf

## Settling the koku's rice mass

Settled by diagram 0248: a koku is 180 L, ~150 kg as brown rice, so the sheet's 151.5 kg stands ($552). If a later
ruling changes it, add the value to `KOKU_KG` in `readings.py` under a name, make it `DEFAULT_KOKU`, and record the
ruling and date in the comment; the PPP reading of every snapshot moves with it.

## Taking in research on a price we estimated

Record a finding against the estimate (`python3 -m l7r.money finding E.... --verdict ...`, the diagram question file
as source), then move the synthesis ROW that answers with it - never log a new "estimate" after the research, because
calibration would grade the model against its own answer. The shrine builder's prices are such rows (`shrine/...`);
change the row and the catalog line together, and `tests/test_shrines.py` checks they agree.
