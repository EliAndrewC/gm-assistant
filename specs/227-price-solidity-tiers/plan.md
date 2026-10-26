# Plan: feature 227

- Ledger: `guess` split into `extrapolated` (31 rows: a researched relative's price carried over, each citing it) and
  `estimated` (144 rows), by each row's basis; `ledger.LABELS` and a check that an extrapolated row cites research.
- Era files: `eras.py` relabels Kyoto 1745's salt `extrapolated` and both housing entries `estimated`;
  `basket.LABELS` follows.
- Price sheets: three badges (filled Researched, solid-outline Extrapolated, dashed Estimated) and a three-line key.
- Skill docs (SKILL.md, research.md, questions.md) and the `price` command's hint use the new words.
- Tests updated; gate; screenshots and a frontend check of the badges; deploy.
