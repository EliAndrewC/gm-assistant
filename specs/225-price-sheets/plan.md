# Plan: feature 225

- `webapp/l7r/money/prices.py`: the sheets (`SHEETS`, first matching tag wins), `eligible` (a synthesis row, not
  comparative, not a shrine-builder line: tagged both `construction` and `shrine`), `sheets` (items cheapest first,
  coins, laborer-days, the sheet's dollar reading, solidity, swing notes), `source_link`, `unplaced`.
- Route `/money/prices` in `app.py`; `templates/money_prices.html`; `static/js/money_prices.js` (the filter only);
  styles in `money.css`; the landing card in `money_index.html`.
- Tests `tests/test_money_prices.py` (both directions of placement, the Fox charcoal on fuel, formatting, the route,
  the landing link); `tests/screenshot.py` gains `money-prices`.
- Screenshots, dom_audit, frontend-review, deploy.
