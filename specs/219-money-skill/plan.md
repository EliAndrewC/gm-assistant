# Plan: feature 219, the money skill

## Shape

| Piece | Where | What |
|---|---|---|
| Skill | `.claude/skills/money/SKILL.md` | doctrine (who pays in what coin, the two dollar readings, labels), how to answer, index of topic files |
| Topic: research | `.claude/skills/money/research.md` | the diagram request protocol, request bodies under `requests/`, intake steps |
| Topic: updating | `.claude/skills/money/updating.md` | re-pricing the basket into a new snapshot, re-taking the wage |
| Pure logic | `webapp/l7r/money/` | `coins.py` (exact sen arithmetic, parse and format), `readings.py` (PPP from snapshots, "big deal" from wages), `ledger.py` (load, validate, search), `__main__.py` (CLI) |
| Data | `webapp/l7r/money/data/` | `baskets/2017-04.json`, `wages.json`, `ledger.jsonl` |
| Tests | `webapp/tests/test_money_*.py` | 100% coverage |
| Index | `webapp/l7r/money/CLAUDE.md` | what each file is, how to test |

The pure logic lives under `webapp/` because the gate (`make done`) only collects tests there (`testpaths`, coverage
`source = ["l7r"]`); the weather skill's in-directory tests are not gated, and this feature should be.

## Decisions

1. **Koku of rice mass is an input** (default 151.515 kg, the spreadsheet's basis: rice at 0.66 zeni/kg, i.e. its
   constant 2.257575 g silver per zeni is 1.49 g/kg x 151.515 kg / 100). Alternatives kept as named values: ~120 kg
   (40 gallons at 0.8 kg/L) and the historical koku (pending diagram#1 Q3). Declined: hard-coding 2.257575 - it would
   hide the GM's open question inside a constant.
2. **"Big deal" wage is an input** (default $15.00/hour x 2,080 hours, dated 2026-10-18). Alternatives: the federal
   minimum ($7.25) and a median unskilled wage. Declined: asserting $10,000 - deriving it lets it move with the wage.
   The divisor (3.32 koku per unskilled year) is labeled a lead until diagram#1 Q2 answers.
3. **Re-price, never CPI-scale.** Rice and beans move differently from the CPI; a CPI scale would quietly carry 2017's
   relative prices forward. Each re-pricing is a new `baskets/YYYY-MM.json`; old snapshots are never edited. The newest
   snapshot is the default.
4. **Ledger as JSONL** with `item, low, high, unit, coin, label, source, notes` (figures in sen, exact). Labels:
   `historical`, `deviation`, `guess`. Source: an `https://` URL (diagram question file, GitHub canon file) or
   `canon:` / `lead:` pointer. The digest's anchors enter as `guess` with `lead:` sources until research upgrades them.
5. **No webapp page** (bulk and lookup needs belong in chat). **No copy of diagram's agents** (handoff; diagram 389).
6. **Everyday coin**: `coins.everyday()` formats an amount in the largest coin a buyer at that price level would use -
   sen/zeni under a bu, bu under a koku, koku above - and the skill text says when koku-scale gold marks noteworthy wealth.
