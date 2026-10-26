# Plan: feature 231

- Data: `webapp/l7r/money/data/household.json` holds every figure with its verdict and research question (0311-0317,
  verified on diagram main at aa9bbeb); `l7r/money/household.py` loads and checks it (a figure without a known verdict
  or source fails) and computes homemade goods beside the ledger's market price and the day wages.
- Ledger (FR-002): four researched city prices from 0315 (a public bath, sushi and omelette pieces, a peddler family's
  day of rice); the travel sheet's description names the bath.
- Calibration (FR-003): findings for E0194-E0218 (7 graded, 17 SILENT, 1 not attested); the household recipe in
  `questions.md` adjusted as the report asks.
- Page: `/money/household` (`money_household.html`), a third card on `/money`, and the landing note links to its
  "Why so much is missing". A bar list for the counted year (one measure, women's work in vermillion, a legend), tables
  that stack on mobile, verdict badges that differ by fill and border and link to the research record.
- Verification: tests (`test_money_household.py`), the gate, screenshots and the DOM audit, frontend-review, deploy.
