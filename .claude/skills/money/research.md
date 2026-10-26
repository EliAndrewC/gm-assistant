# Research requests to the diagram repository

Load this file when: asking the diagram repository a money question, or taking in its answer.

Research is done in diagram, not here: its record has the search pass, the source archive, verbatim citations and the
checking agents, and diagram feature 389 gave it a "Money and prices" section. Never copy its agents or scripts here
(they depend on ~35 diagram scripts and would drift). The skill CITES its question files.

## Asking

0. **Estimate every figure the request asks for, and log it, before writing the request** (`calibration.md`; time,
   shares and counts take `--unit`). Name the ids in the request file's `**Estimates logged before filing**:` line
   (the gate checks it), and `link` them to the issue once it exists. The values stay out of the issue body.
1. Write the body in `requests/NNNN-<slug>.md` (first line is the title, bolded). Per question, four things:
   - **Question** - what history should answer.
   - **Figure needed** - the number the ledger needs back, and its unit.
   - **Canon beside it** - the `setting/l7r.md` / `setting/budgets.md` figure it must sit beside, quoted.
   - **Region order** - Japan-first (Tokugawa series are the richest for prices and wages) or China-first (geography,
     transport, settlement - the project's usual order), or both.
   A diagram page session writes at most four questions at a time; bundle up to four per issue.
2. Open and watch it, from MAIN's tree (the token is in main's gitignored `webapp/development-secrets.ini`; a clone has
   no copy, so the call fails there):
   ```
   cd /gm-assistant && tail -n +3 <clone>/.claude/skills/money/requests/NNNN-<slug>.md > <scratch>/body.md \
     && python3 ~/.claude/hooks/issue_watch.py open EliAndrewC/diagram "Money research: <title>" < <scratch>/body.md
   ```
   `open` also starts the watch. A running diagram session only sees issues it already watches, so point it at a new
   one by commenting on an issue it watches (or the GM pastes the link there). Since 2026-10-18 the GM pre-approves on
   the diagram side any money request he asked to be filed; it starts without a separate approval.
3. Add the issue to the table below.

## Taking in an answer

The answer names, per question, the fragment FILE (`research/questions/NNNN-<slug>.html`), a verdict per figure, and
what is still open.

1. Read the file on diagram's `main` (GitHub contents API with `Accept: application/vnd.github.raw` and main's
   `[github] push_pat`). Check the figure is in the file's findings as quoted, not only in the issue comment.
2. Update the ledger rows it bears on: `source` becomes
   `https://github.com/EliAndrewC/diagram/blob/main/research/questions/NNNN-<slug>.html`, and the label follows the
   verdict:

   | Verdict | Label |
   |---|---|
   | ATTESTED | `historical` |
   | ATTESTED ONLY FOR (a place, period or class) | `historical`, with the scope in `notes`; a Rokugani row carried beyond it is `extrapolated` |
   | NOT ATTESTED / SILENT | `estimated`, or `extrapolated` if it carries a researched relative's price (keep the lead; note the diagram file as searched) |

3. If the history contradicts the canon, change nothing in the canon: put both to the GM. If the GM keeps the canon,
   the row becomes `deviation` with the diagram file as its source.
4. If an answer changes a basket input or the laborer's year, follow `updating.md`.
5. Record a finding for each logged estimate the answer grades (`calibration.md` step 4).
6. Run `check`, commit, push; then post a short verification note and close the issue
   (`python3 ~/.claude/hooks/issue_watch.py close EliAndrewC/diagram#N "what was verified"`). The asker closes.

## Requests

| Issue | Questions | Status |
|---|---|---|
| [EliAndrewC/diagram#1](https://github.com/EliAndrewC/diagram/issues/1) | land price in years of yield; unskilled day wages; the koku of rice; the Kyoto basket (`requests/0001-foundations.md`) | closed, answered by 0248-0251 |
| [EliAndrewC/diagram#2](https://github.com/EliAndrewC/diagram/issues/2) | The Complete Servant (1825): archive it, check the servant wages already extracted into the ledger, add provision prices (`requests/0002-complete-servant.md`; `sources.md`) | closed 2026-10-19 |
| [EliAndrewC/diagram#3](https://github.com/EliAndrewC/diagram/issues/3) | campaign costs I: inns and stabling, hired transport, cloth and kimono, sake (`requests/0003-...`; `questions.md`) | answered 2026-10-19 by 0259-0262: 11 graded or SILENT, E0014 withdrawn (units slip); inns, cheap lodging, cloth, kimono, silk and sake rows moved; copper-to-silver rate asked as a new question; closed |
| [EliAndrewC/diagram#4](https://github.com/EliAndrewC/diagram/issues/4) | campaign costs II: arrows, notice boards and paper, rents, plays and entertainers (`requests/0004-...`; `questions.md`) | answered 2026-10-19 by 0263-0267 and 0190: 16 findings; weapons and entertainment recipes adjusted; rent at 3-6% of value; closed |
| [EliAndrewC/diagram#5](https://github.com/EliAndrewC/diagram/issues/5) | campaign costs III: fruit, salt and small offerings, skilled day wages (`requests/0005-...`) | closed 2026-10-19 by 0272-0275: 3 graded (apples from a Qing court price), the salt bag SILENT; skilled day 17-34 sen |
| [EliAndrewC/diagram#6](https://github.com/EliAndrewC/diagram/issues/6) | PRIORITY: what a small forest shrine cost to build (`requests/0006-...`; estimates E0035-E0051) | answered 2026-10-19 by 0255-0258: E0052 graded (1.46x low), 15 SILENT; sanctuary re-priced; closed |
| [EliAndrewC/diagram#7](https://github.com/EliAndrewC/diagram/issues/7) | the rest of the shrine builder's options (`requests/0007-...`; 84 `shrine catalog` estimates) | answered 2026-10-19 by 0268-0271: 3 graded, 28 SILENT; lanterns, pavilion, tall lantern and site line re-priced; reference 62.7, budget 80; closed |
| [EliAndrewC/diagram#8](https://github.com/EliAndrewC/diagram/issues/8) | kitchen knives (E0156-E0158) and the copper-to-silver rate (`requests/0008-...`) | closed 2026-10-19 (0276-0277) |
| [EliAndrewC/diagram#10](https://github.com/EliAndrewC/diagram/issues/10) | the shrine builder's small lines #6 and #7 never asked (48 estimates; `requests/0009-...`) | closed 2026-10-21 (feature 408; new question 0278) |
| [EliAndrewC/diagram#11](https://github.com/EliAndrewC/diagram/issues/11) | charcoal, ordinary black and fine white (E0159-E0166; `requests/0010-charcoal.md`) | closed 2026-10-22 (feature 410, question 0279) |
| [EliAndrewC/diagram#12](https://github.com/EliAndrewC/diagram/issues/12) | how far goods traveled and what distance did to price: freight by land and water, haul limits, tea caravans, a famous good far from home (E0167-E0168; `requests/0011-charcoal-far-markets.md`) | closed 2026-10-22 (feature 411, questions 0280-0283; E0167-E0168 SILENT) |
| [EliAndrewC/diagram#13](https://github.com/EliAndrewC/diagram/issues/13) | the standard basket in every era: salt, fuel and a room in Kyoto 1745-54; basket cost, unskilled wage and coin rates per era and place (feature 222; `requests/0012-standard-basket-eras.md`) | open |
| [EliAndrewC/diagram#14](https://github.com/EliAndrewC/diagram/issues/14) | the research site's money tooltip, reading gm-assistant's `conversions.json` (feature 222; `requests/0013-money-tooltip.md`) | open |
| [EliAndrewC/diagram#15](https://github.com/EliAndrewC/diagram/issues/15) | price stability by time scale (within a day to a century) and by good, place-to-place spread, and a researched closeness rule for borrowed conversions (`requests/0014-price-stability.md`) | answered 2026-10-25 by 0290-0294: swing notes in `data/swings.jsonl`, the closeness rule in SKILL.md; England's series: GM yes, as comparative sources in "Comparative money: other societies" |
| [EliAndrewC/diagram#16](https://github.com/EliAndrewC/diagram/issues/16) | gold, silver and copper as separate monies: legal against market rates, who paid in what, coin-dependent and sticky copper prices, who lost when rates moved (`requests/0015-three-metals.md`) | answered (0295, 0296); GM 2026-10-25: the ladder stays fixed, a premium by coin is negotiated in play |
| [EliAndrewC/diagram#17](https://github.com/EliAndrewC/diagram/issues/17) | the goods-dollar koku as an index: like-for-like modern goods, housing, era coverage, which mean (`requests/0016-index-basis.md`) | answered (feature 420); applied in 223-224; closed 2026-10-25 |
| [EliAndrewC/diagram#18](https://github.com/EliAndrewC/diagram/issues/18) | miso and soy sauce, and which goods the opening changed (`requests/0017-miso-and-the-opening.md`) | answered (0303, 0304); applied in 224; closed 2026-10-25 |
| [EliAndrewC/diagram#19](https://github.com/EliAndrewC/diagram/issues/19) | books (buying, borrowing, copying), skilled wages (clerk, armed guard, cook, lady's maid), a smith's inputs, sales and income, entertainers' incomes, troupe size, costumes and instruments (`requests/0018-...`; E0169-E0193) | answered 2026-10-26 by 0305-0308: 8 graded, 17 SILENT; tools and entertainment recipes adjusted; closed |

| [EliAndrewC/diagram#20](https://github.com/EliAndrewC/diagram/issues/20) | days worked a year by kind of worker, engaged by the job or the year, how often players performed (`requests/0019-...`; no estimates: filed before the rule) | answered 2026-10-26 by 0307, 0309-0311: farm servants 310-330 days; the 250 stays a labeled convention; closed |
| [EliAndrewC/diagram#21](https://github.com/EliAndrewC/diagram/issues/21) | a household's unpaid work: the year by member, the tasks and their time, the fiber chain, city households, the proverb, why women's work went unrecorded (`requests/0020-...`; E0194-E0218, in hours, days, percent and count) | open |

## Next candidates (not yet asked)

- **Horses**: a farm horse, a packhorse, a warhorse - the medieval (0.33-2 koku) and Regency (14.5 koku) comparative rows
  disagree by an order of magnitude, and neither may set the Rokugani price.
- **Swords and armor**: a common and a fine sword in Tokugawa Japan and Ming/Qing China, against smith and polisher
  labor and the steel; the 2017 working figure is 1.5 koku for a samurai wakizashi, katana open.
- **Prepared street food**: noodles, rice balls, grilled fish from a stall.
