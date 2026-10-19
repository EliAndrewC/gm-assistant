# Estimates and calibration

Load this file when: the GM asks a price the ledger cannot back with research, or a diagram answer arrives for a logged
estimate, or the GM asks how good the model is.

The GM (2026-10-18, feature 220): estimate what was never priced, log the guess, research it later, and track *"how in
line with our research our estimates were, because that tells us how well calibrated our model is"*. A constant miss in
one direction adjusts the model; staying inside the error bars is a good sign; guesses all over the place mean the
method is weak there - *"Markets are ultimately the thing that determine actual prices"*, and the model only
approximates them.

## The standard path for any price not already backed by research

1. **Estimate** from the model (`questions.md` recipes; anchors: the unskilled day, a koku of rice, cloth, worked metal,
   the skilled day), show the derivation, and answer the GM.
2. **Record** it, before research can color it (run from the clone's `webapp/`; the logs are data files):
   ```
   python3 -m l7r.money estimate --item "a replacement tsuba (iron, plain)" \
     --question "what do we think a replacement katana handguard cost?" --low "3 bu" --high "6 bu" --per item \
     --category weapons --method "iron ~1 bu + 2-4 skilled days" --rows wage-skilled-day
   ```
   It prints the id (E0035...). Add the synthesis row to the ledger too, with its consistency rules (feature 219).
3. **File** a diagram issue for the research (`research.md`), one issue per ask (items asked together share one), and
   link it: `python3 -m l7r.money link https://github.com/EliAndrewC/diagram/issues/N E0035 [E0036 ...]`.
4. **Take in** the answer when it lands: verify it against the question file, then record a finding per estimate, in the
   estimate's own unit (convert a bundle price to the item and say how in `--notes`):
   ```
   python3 -m l7r.money finding E0035 --low "2 bu" --high "4 bu" \
     --source https://github.com/EliAndrewC/diagram/blob/main/research/questions/NNNN-x.html --verdict ATTESTED
   ```
   NOT ATTESTED and SILENT are recorded too; they grade nothing. A comparative source (Regency England etc.) never
   grades an estimate. Then update the ledger row to the researched figure. **Never edit the estimate**: the gate fails
   if a committed line of `data/estimates.jsonl` changes.
5. **Grade**: `python3 -m l7r.money calibration`.

`python3 -m l7r.money estimates --open` lists what is still waiting, and which issue it waits on.

## Reading the calibration

Per category and overall, with the count:
- **guesses run N x high / low** - the bias (geometric mean of estimate/finding). Within 1.5x either way is calibrated.
- **typical miss N x** - the spread (median miss as a factor, either direction). Under 2x is good for pre-modern prices.
- **research inside our range N%** - the hit rate.

## Adjusting the model

When a category has **3 or more graded estimates** and its bias is beyond **1.5x** either way, or its typical miss is
over **2x**, the report flags it (`<- revise this recipe`). Then:
1. Find the shared cause: a wrong anchor (cloth price, the skilled wage), a missing input (the return trip), a markup.
2. Revise that category's recipe or anchor in `questions.md`, and add a dated line under the category:
   `Adjusted 2026-MM-DD: <what changed>, because calibration showed <the report line>.`
3. Leave the old estimates alone. Estimates logged after the change carry the date and model inputs that let a later
   reading compare before and after.
Below 3 graded estimates, report the numbers but do not adjust: two points are noise.
