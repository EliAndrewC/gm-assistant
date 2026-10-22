# Research requests to the diagram repository

Load this file when: asking the diagram repository a money question, or taking in its answer.

Research is done in diagram, not here: its record has the search pass, the source archive, verbatim citations and the
checking agents, and diagram feature 389 gave it a "Money and prices" section. Never copy its agents or scripts here
(they depend on ~35 diagram scripts and would drift). The skill CITES its question files.

## Asking

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
   | ATTESTED ONLY FOR (a place, period or class) | `historical`, with the scope in `notes`; a Rokugani row extrapolated beyond it stays `guess` |
   | NOT ATTESTED / SILENT | `guess` (keep the lead; note the diagram file as searched) |

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
| [EliAndrewC/diagram#12](https://github.com/EliAndrewC/diagram/issues/12) | how far goods traveled and what distance did to price: freight by land and water, haul limits, tea caravans, a famous good far from home (E0167-E0168; `requests/0011-charcoal-far-markets.md`) | open 2026-10-22, low priority |

## Next candidates (not yet asked)

- **Horses**: a farm horse, a packhorse, a warhorse - the medieval (0.33-2 koku) and Regency (14.5 koku) comparative rows
  disagree by an order of magnitude, and neither may set the Rokugani price.
- **Swords and armor**: a common and a fine sword in Tokugawa Japan and Ming/Qing China, against smith and polisher
  labor and the steel; the 2017 working figure is 1.5 koku for a samurai wakizashi, katana open.
- **Prepared street food**: noodles, rice balls, grilled fish from a stall.
