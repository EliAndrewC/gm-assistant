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

`LABORER_KOKU_YEAR` (3.32) and `WORKING_DAYS` (250) in `webapp/l7r/money/readings.py` are the 2017 sheet's figures. When
diagram#1 Q2 answers, change them there with the question file in the comment, and update the two wage rows in the
ledger. Every "big deal" figure and every laborer-days count moves with them.

## Settling the koku's rice mass

When the GM decides what a koku of rice weighs, add it to `KOKU_KG` in `readings.py` under a name, make it
`DEFAULT_KOKU`, and record the GM's ruling and date in the comment. The PPP reading of every snapshot moves (151.5 kg
gives $552; 121 kg gives $442).
