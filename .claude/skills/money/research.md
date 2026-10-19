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
   `open` also starts the watch. Tell the GM: they start a diagram session to work it.
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
5. Run `check`, commit, push; then post a short verification note and close the issue
   (`python3 ~/.claude/hooks/issue_watch.py close EliAndrewC/diagram#N "what was verified"`). The asker closes.

## Requests

| Issue | Questions | Status |
|---|---|---|
| [EliAndrewC/diagram#1](https://github.com/EliAndrewC/diagram/issues/1) | land price in years of yield; unskilled day wages; the koku of rice; the Kyoto basket (`requests/0001-foundations.md`) | open 2026-10-18 |
| [EliAndrewC/diagram#2](https://github.com/EliAndrewC/diagram/issues/2) | The Complete Servant (1825): archive it, check the servant wages already extracted into the ledger, add provision prices (`requests/0002-complete-servant.md`; `sources.md`) | open 2026-10-18 |
| [EliAndrewC/diagram#3](https://github.com/EliAndrewC/diagram/issues/3) | campaign costs I: inns and stabling, hired transport, cloth and kimono, sake (`requests/0003-...`; `questions.md`) | open 2026-10-18 |
| [EliAndrewC/diagram#4](https://github.com/EliAndrewC/diagram/issues/4) | campaign costs II: arrows, notice boards and paper, rents, plays and entertainers (`requests/0004-...`; `questions.md`) | open 2026-10-18 |

## Next candidates (not yet asked)

- **Horses**: a farm horse, a packhorse, a warhorse - the medieval (0.33-2 koku) and Regency (14.5 koku) comparative rows
  disagree by an order of magnitude, and neither may set the Rokugani price.
- **Swords and armor**: a common and a fine sword in Tokugawa Japan and Ming/Qing China, against smith and polisher
  labor and the steel; the 2017 working figure is 1.5 koku for a samurai wakizashi, katana open.
- **Fruit, salt and everyday food**: fruit by the piece, salt under a monopoly, prepared street food.
