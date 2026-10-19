# Plan: feature 220, estimate log and calibration

| Piece | Where |
|---|---|
| Logs and measures | `webapp/l7r/money/calibration.py`; `data/estimates.jsonl`, `data/requests.jsonl`, `data/findings.jsonl` |
| Commands | `python3 -m l7r.money estimate | link | finding | estimates | calibration` |
| Append-only guard | `rewritten()`, tested against `git show HEAD:` of the estimate log |
| Skill text | `.claude/skills/money/calibration.md` (Load this file when...), SKILL.md's answer procedure |
| Tests | `webapp/tests/test_money_calibration.py` |

## Decisions

1. **Three append-only files**, so filing an issue or taking in research never edits a guess.
2. **Ratios in log space** (bias = geometric mean of estimate/finding midpoints; spread = median |log ratio| as a
   factor; hit rate = finding midpoint inside the estimate range). Declined: arithmetic sen differences, which one
   koku-scale item would dominate.
3. **The adjustment threshold** (spec US4): a category with **3 or more** counted findings whose bias is outside
   **0.67-1.5** (a consistent miss of more than 1.5x one way), or whose spread is over **2.0** (typical miss over a
   factor of two), gets its recipe or anchors revised in `questions.md`, dated, with the calibration line quoted.
   Below 3 findings, report but do not adjust: two points are noise.
4. **Append-only enforced against git HEAD**: catches any edit before it is committed. Declined: per-line signatures,
   which add machinery without stopping a determined edit any better than review does.
5. **The model inputs saved with each estimate** (basket snapshot, koku mass, wage date, laborer's year), so a later
   change to the model can be read before and after.
