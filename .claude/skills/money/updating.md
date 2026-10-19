# Keeping the money skill up to date

Load this file when: re-pricing the basket, re-taking the wage, or settling one of the open knobs.

The GM wants the skill to *"keep up to date and keep track of so that we can update it periodically"*. Every dollar
reading rests on dated inputs, so updating is adding a new dated input - never editing an old one.

## Re-pricing the basket (PPP dollars)

**Re-price, never scale by the CPI.** Rice and beans move differently from the CPI; scaling 2017's figure would carry
2017's relative prices forward under a new date (handoff, 2026-10-18).

1. Copy the newest `webapp/l7r/money/data/baskets/YYYY-MM.json` to a new file named for this month.
2. Set `date`, `priced_by` (who, which store) and `source`. Keep `goods`, `quantity`, `unit` and `silver_g_per_unit`
   exactly - those are the historical basket. Replace each `dollars_per_unit` and `link` with today's price per unit
   (bulk retail, the same kind of good; note a substitute in `priced_as`).
3. `python3 -m l7r.money history` lists every snapshot's dollars per koku; the newest is now the default. Do not touch
   the older files - `--snapshot 2017-04` must keep reproducing $552.
4. If diagram#1 Q4 corrects the basket itself (quantities or silver prices), that is a new snapshot too, with a note.

## Re-taking the wage ("big deal" dollars)

Append a reading to `webapp/l7r/money/data/wages.json` (`date`, `hourly`, `hours_per_year`, `basis`, `source`). The
newest is the default; `--wage-date` reaches older ones.

## The laborer's year

`LABORER_KOKU_YEAR` (3.32) and `WORKING_DAYS` (250) in `webapp/l7r/money/readings.py` are the 2017 sheet's figures.
Diagram 0250: ~2 kg of rice a day is attested; the 250-day year is a modern convention. A future count of working days
would change them; the two wage rows cite 0250. Every "big deal" figure and every laborer-days count moves with them.

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
