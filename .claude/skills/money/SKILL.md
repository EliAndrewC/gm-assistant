---
name: money
description: What things cost in Rokugan and what a sum of money is worth - prices in the coins a buyer would actually hand over, each with its basis and how solid it is (historical / deliberate deviation / guess), plus two dollar readings of a koku (goods dollars: what it BUYS, by a basket of goods; wage dollars: how much it MATTERS), and conversions of historical money (mon, monme, yen) into both and into Rokugani coin. Research questions go to the diagram repository by GitHub issue.
argument-hint: <item or service> | <amount of koku/bu/zeni/sen> | <dollars>
---

# Money

The goal (GM, 2026-10-18): figure out what things would realistically cost in the setting *"instead of just completely
hand waving"*. Pre-modern price records are patchy (nobody preserved what a Roman gladius cost), so most prices are
reasoned from neighbors - similar goods, the metal, the labor, the same good in a comparable society. The standard is
**internal consistency**: every figure rests on a stated basis, says how solid it is, and agrees with the others.

## The tools (run from `webapp/`)

The lookups below are read-only and fine in main's tree. `estimate`, `link` and `finding` WRITE the logs: run them
in your session clone's `webapp/`, then commit and push (`calibration.md`).

```
cd /gm-assistant/webapp && python3 -m l7r.money price sword          # ledger rows matching every word
cd /gm-assistant/webapp && python3 -m l7r.money convert 3 koku 4 bu  # exact coins, koku, goods and wage dollars
cd /gm-assistant/webapp && python3 -m l7r.money dollars 500          # dollars -> coin (add --wage-dollars)
cd /gm-assistant/webapp && python3 -m l7r.money era 20 mon --era kyoto-1745  # historical money, three ways
cd /gm-assistant/webapp && python3 -m l7r.money baskets              # dollars per koku, every basket
cd /gm-assistant/webapp && python3 -m l7r.money history              # dollars per koku, every price snapshot
cd /gm-assistant/webapp && python3 -m l7r.money check                # validate the ledger, baskets, snapshots, eras
```

Knobs on any command: `--basket standard|standard-no-housing|bassino-ma-a`, `--snapshot YYYY-MM`,
`--koku-kg sheet-2017|budgets-brown|budgets-polished|<kg>`, `--wage <dollars/hour>`, `--wage-date`. Every output prints
the basis it used; quote it with the answer. The same basket is a page anyone can play with: the toolkit's Money
section, `/money/koku`.

`price` ends with each matched good's **swing note** (`data/swings.jsonl`): whether its real-world price was steady or
swung across periods, and why. Quote it with a price whose spread matters to the answer.

**Which era to convert a historical amount in** ([diagram 0294](https://github.com/EliAndrewC/diagram/blob/main/research/questions/0294-when-does-a-price-borrowed-from-another-year-or-place-need-a-note.html),
this project's derivation; no source states a rule). An amount within a good's no-note span of an era's years converts
plainly: Kyoto rice ~25 years, miso and the day wage 15, sake 50, firewood, soy sauce and lamp oil 5, Edo goods 20,
Osaka rice 10, the Qing baskets 5. Past that span it still converts, with a note naming the borrowed era (on
diagram's site, `data-paid`): no further limit is measured. It never converts across a break: the 1859 opening, a
recoinage that changed the coin's silver, a change of money system (the yen, China's tael, cash and dollar), a domain's
own notes, or a move in China's cash rate. Between cities, rice and lamp oil borrow freely; miso, soy sauce and
firewood need a note.

## Coins and who uses them (canon: `setting/l7r.md` "Money")

1 koku (gold) = 10 bu (silver) = 100 zeni (copper) = 1,000 sen (small copper, minted as strings of 10 to cut apart).

- **Daily life is copper.** A meal, a tip, a day's wage, a cheap blade: sen and zeni.
- **Silver bu** is for sums a household plans for: a tool, a season's rent, a real bribe.
- **Gold koku** belongs to landlords, merchant houses, officials and treasuries. *"Very few people would buy things with
  Koku ... Player characters who do are exceptionally wealthy in a way which is noteworthy."* Any answer of a koku or
  more says who would pay that in gold, and that paying it marks the payer.
- **The ladder is fixed; a premium by coin is negotiated** (GM 2026-10-25). The decimal ratios never move: a labeled
  deviation from history, where gold, silver and copper were separate monies whose legal rate the market ignored
  ([diagram#16](https://github.com/EliAndrewC/diagram/issues/16): 0295 Japan, 0296 China). What does happen is a
  premium or discount for paying in a particular coin, struck between buyer and seller in a particular place or
  crisis (a copper shortage, a changer's fee, a merchant who wants gold for a long journey): play, not a rate table.
  Historical conversions still take each coin at its own era's market rate (`data/eras/`).
- The **Imperial rate** fixes 1 koku = 48 gallons (180 liters) of rice for taxes, rent and stipends; market rice floats with harvest
  and place, and the Ministry of Retainers' mix of rice and coin is soft power.
- Canon money rules to apply, not re-derive: stipend = rank squared; gifts by highest rank involved (token = that many
  zeni, consideration = bu, compensatory = koku); tariffs typically ~15% of declared sales value; interest (GM 2013)
  15-20% a year in cities, ~25% in the countryside including fees.

## Two dollar readings of a koku - always give both, never mix them

- **Goods dollars** (~$875 on the standard basket at 2026-10 prices; ~$443 without housing): what a koku BUYS. The
  standard basket is Bassino & Ma's Kyoto basket plus salt, fuel and a share of a room (feature 222; housing is about
  half of today's dollars, so name the no-housing figure when a sum is about food and goods). Until 2026-10 this was
  "PPP dollars", ~$552 in 2017 prices on the food-only basket.
- **Wage dollars** (~$9,400 at $15/hour; "big deal" dollars until feature 222): how much a windfall, a debt or a loss
  MATTERS. One koku is 1/3.32 of an
  unskilled laborer's year, applied to a US unskilled full-time year. (The GM's table feel is ~$10,000.)
- **Laborer-days** is the yardstick for consistency: a new price that takes an implausible number of days of unskilled
  work (about 13.3 sen a day) is wrong, whatever its dollar reading says.

## Answering "what does X cost?"

1. `price <words>`. If a row matches, give its figure in everyday coins, its koku value, both readings, its label and its
   source. A `historical` row resting on a `lead:` is **unverified** - say so.
2. No row backed by research: **estimate** from named rows - materials, laborer-days of skilled or unskilled work, the
   East Asian comparable - show the chain and label it a **guess**. Then, every time (feature 220): **log the
   estimate**, add the synthesis row and its rules, **file a diagram issue** and link it. The steps and commands are in
   `calibration.md`.
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

- **Price ranges that show how much a good swung across periods** (GM 2026-10-24): the swing notes are in
  (`data/swings.jsonl`, from [diagram#15](https://github.com/EliAndrewC/diagram/issues/15)); the ledger's own page on
  the Money section, which will show them beside each narrow range, is still to build.

- **The pound-to-koku rate** for the English comparative rows: 145 sen per pound (the Austen sheet: 1 GBP = $80 at
  $550/koku). Anchoring on wages instead (an English laborer's GBP 15-20 a year = a Rokugani laborer's 3.32 koku) gives
  ~190 sen per pound, about 30% higher.
- **The "big deal" wage**: $15/hour default; the federal minimum or a median unskilled wage are the alternatives.

## Index

| File | Load it when |
|---|---|
| [`questions.md`](questions.md) | A price question comes up at the table: the campaign's questions, first answers, and the category recipes (wages, lodging, transport, weapons, paper, food, offerings, rentals, clothing, drink, entertainment, construction, tools, fuel). |
| [`calibration.md`](calibration.md) | Logging an estimate, taking in a finding for one, reading the calibration report, or adjusting a recipe. |
| [`research.md`](research.md) | Asking the diagram repository a question, or taking in its answer. |
| [`updating.md`](updating.md) | Re-pricing the basket, re-taking the wage, or settling one of the open knobs. |
| [`sources.md`](sources.md) | Pricing a household, servants or a gentleman's budget; primary sources read directly (The Complete Servant). |
| `requests/` | The bodies of research requests already opened. |
| [`webapp/l7r/money/CLAUDE.md`](../../../webapp/l7r/money/CLAUDE.md) | Changing the code or data files, and how to test them. |

Sources behind the seed figures: the GM's money folder (`money/` in the l7r repository: `HANDOFF.md`, `digest.md`, the
2017 PPP and Austen spreadsheets, and the 2013-2017 emails).
