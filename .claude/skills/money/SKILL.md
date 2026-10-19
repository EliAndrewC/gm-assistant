---
name: money
description: What things cost in Rokugan and what a sum of money is worth - prices in the coins a buyer would actually hand over, each with its basis and how solid it is (historical / deliberate deviation / guess), plus two dollar readings of a koku (what it BUYS by purchasing power parity, and how big a DEAL it is). Research questions go to the diagram repository by GitHub issue.
argument-hint: <item or service> | <amount of koku/bu/zeni/sen> | <dollars>
---

# Money

The goal (GM, 2026-10-18): figure out what things would realistically cost in the setting *"instead of just completely
hand waving"*. Pre-modern price records are patchy (nobody preserved what a Roman gladius cost), so most prices are
reasoned from neighbors - similar goods, the metal, the labor, the same good in a comparable society. The standard is
**internal consistency**: every figure rests on a stated basis, says how solid it is, and agrees with the others.

## The tools (run from `webapp/`; read-only, fine in main's tree)

```
cd /gm-assistant/webapp && python3 -m l7r.money price sword          # ledger rows matching every word
cd /gm-assistant/webapp && python3 -m l7r.money convert 3 koku 4 bu  # exact coins, koku, both dollar readings
cd /gm-assistant/webapp && python3 -m l7r.money dollars 500          # dollars -> coin (add --big-deal)
cd /gm-assistant/webapp && python3 -m l7r.money history              # dollars per koku, every basket snapshot
cd /gm-assistant/webapp && python3 -m l7r.money check                # validate the ledger
```

Knobs on any command: `--koku-kg sheet-2017|budgets-brown|budgets-polished|forty-gallons|<kg>`, `--snapshot YYYY-MM`, `--wage <dollars/hour>`,
`--wage-date`. Every output prints the basis it used; quote it with the answer.

## Coins and who uses them (canon: `setting/l7r.md` "Money")

1 koku (gold) = 10 bu (silver) = 100 zeni (copper) = 1,000 sen (small copper, minted as strings of 10 to cut apart).

- **Daily life is copper.** A meal, a tip, a day's wage, a cheap blade: sen and zeni.
- **Silver bu** is for sums a household plans for: a tool, a season's rent, a real bribe.
- **Gold koku** belongs to landlords, merchant houses, officials and treasuries. *"Very few people would buy things with
  Koku ... Player characters who do are exceptionally wealthy in a way which is noteworthy."* Any answer of a koku or
  more says who would pay that in gold, and that paying it marks the payer.
- The **Imperial rate** fixes 1 koku = 40 gallons of rice for taxes, rent and stipends; market rice floats with harvest
  and place, and the Ministry of Retainers' mix of rice and coin is soft power.
- Canon money rules to apply, not re-derive: stipend = rank squared; gifts by highest rank involved (token = that many
  zeni, consideration = bu, compensatory = koku); tariffs typically ~15% of declared sales value; interest (GM 2013)
  15-20% a year in cities, ~25% in the countryside including fees.

## Two dollar readings of a koku - always give both, never mix them

- **PPP dollars** (~$552 on the 2017 snapshot): what a koku BUYS. From a dated re-pricing of Bassino & Ma's Kyoto basket.
- **"Big deal" dollars** (~$9,400 at $15/hour): how much a windfall, a debt or a loss MATTERS. One koku is 1/3.32 of an
  unskilled laborer's year, applied to a US unskilled full-time year. (The GM's table feel is ~$10,000.)
- **Laborer-days** is the yardstick for consistency: a new price that takes an implausible number of days of unskilled
  work (about 13.3 sen a day) is wrong, whatever its dollar reading says.

## Answering "what does X cost?"

1. `price <words>`. If a row matches, give its figure in everyday coins, its koku value, both readings, its label and its
   source. A `historical` row resting on a `lead:` is **unverified** - say so.
2. No row: **derive from named rows** - materials, laborer-days of skilled or unskilled work, the comparable good - show
   the chain, label it a **guess**, and offer to add it as a row. If the price matters (it will recur at the table, or
   other prices would lean on it), propose a research request (`research.md`).
3. Never contradict the canon silently. If history and canon disagree, show both; the GM decides.

## Ledger rows (`webapp/l7r/money/data/ledger.jsonl`)

**Two kinds of row.** A *source row* (no `id`) records what one source says, as found; sources may disagree (place,
period, debased coin, a different koku). A *synthesis row* (with an `id`) is what you answer with. Answers are a
synthesis: derive a synthesis row from the sources, add it, and never answer straight from a source row.
**Consistency rules** (`data/rules.jsonl`) bind synthesis rows - a kimono costs at least its cloth, a skilled wage is at
least the unskilled one, tavern sake at least retail - and `check` and the gate fail on a broken one. A note or a range
never exempts a row; when sources disagree, widen the synthesis range or explain it, never drop the rule. When you add
a row, add the rules that tie it to its inputs.

Figures in whole sen; `label` is `historical`, `deviation` (departs from history on purpose), `guess`, or
`comparative`; `source` is a diagram question URL, `canon:<file> "<section>"`, or `lead:<file>`. The field rules are in
`webapp/l7r/money/ledger.py`'s docstring; `check` and the gate refuse a row without a label and source.

**Comparative rows** (Regency England, medieval Lucca; GM ruling, diagram feature 391) are yardsticks players
recognize, put through the same conversion. They never set a Rokugani price or wage, and never set the value of a koku
(*"not because we will use it to establish the actual value of a koku"*). Quote one beside a Rokugani figure, or as a
cross-check on a derivation that rests on Japanese or Chinese evidence; never as the basis of a Rokugani figure.

## Open for the GM

- **The koku's rice mass**: `l7r.md` says ~40 gallons (twice: "Money" and "Rent and taxes"), but `budgets.md`
  "Historical units" says ~180 L (~48 gallons) and ~150 kg as brown rice, "the canonical figure", which its yield math
  uses (0.021 koku per gallon). The 2017 sheet's 151.5 kg agrees with budgets.md within 1% ($552; `--koku-kg
  budgets-brown` gives $547); only a literal 40 gallons (~121 kg, $442) breaks from it. diagram#1 Q3 cites the history.
- **The pound-to-koku rate** for the English comparative rows: 145 sen per pound (the Austen sheet: 1 GBP = $80 at
  $550/koku). Anchoring on wages instead (an English laborer's GBP 15-20 a year = a Rokugani laborer's 3.32 koku) gives
  ~190 sen per pound, about 30% higher.
- **The "big deal" wage**: $15/hour default; the federal minimum or a median unskilled wage are the alternatives.

## Index

| File | Load it when |
|---|---|
| [`questions.md`](questions.md) | A price question comes up at the table: the campaign's questions, first answers, and the category recipes (wages, lodging, transport, weapons, paper, food, offerings, rentals, clothing, drink, entertainment). |
| [`research.md`](research.md) | Asking the diagram repository a question, or taking in its answer. |
| [`updating.md`](updating.md) | Re-pricing the basket, re-taking the wage, or settling one of the open knobs. |
| [`sources.md`](sources.md) | Pricing a household, servants or a gentleman's budget; primary sources read directly (The Complete Servant). |
| `requests/` | The bodies of research requests already opened. |
| [`webapp/l7r/money/CLAUDE.md`](../../../webapp/l7r/money/CLAUDE.md) | Changing the code or data files, and how to test them. |

Sources behind the seed figures: the GM's money folder (`money/` in the l7r repository: `HANDOFF.md`, `digest.md`, the
2017 PPP and Austen spreadsheets, and the 2013-2017 emails).
