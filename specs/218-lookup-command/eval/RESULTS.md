# Evaluation results (2026-10-17)

The full glossary (500 hand-written entries plus about 125 people baked from Obsidian Portal,
about 35k prompt tokens) against 88 questions: the GM's five verbatim, terminology from the English
side, people, places, the asker's own character, mis-worded questions, rules terms, wider-world
facts, and five the notes cannot answer. Per-question records: the `*-2026-10-17.json` files;
failures: the `.md` files.

| model | correct | abstained when it should | brief | median cost | median time | p95 time |
|---|---|---|---|---|---|---|
| gemini-3.1-flash-lite | 97.6% | 100% | 97.7% | $0.0019 | 1.1 s | 1.8 s |
| gemini-3.5-flash-lite | 86.7% | 100% | 100% | $0.0023 | 0.8 s | 1.1 s |
| gemini-3.8-flash | 100% | 100% | 98.9% | $0.0046 | 2.5 s | 5.3 s |
| gemini-3.1-pro-preview | 100% | 100% | 100% | $0.0188 | 6.2 s | 12.4 s |

**Default: `gemini-3.1-flash-lite`** by the spec's rule (Story 7.5): the cheapest tier within 5
points of the best (100%), with no more invented answers on the unanswerable questions than the
best tier (none). Its two misses both answered correctly but left out the wiki link (Doctrine of
Three Steps, The Family Reckoning). SC-003's 2-cent working target is met with room to spare: a
median of 0.19 cents, about 1/200th of the 40-cent backstory call.

`gemini-3.5-flash-lite` scored 97.1% on the first-pass glossary (149 entries) but 86.7% on the full
one, mostly by saying "the notes do not cover it" when they did: it loses its way in the longer
context. `gemini-3.8-flash` is the step up if 3.1 Flash-Lite's misses ever matter, at about 2.5x the
cost and time.

**Caveat, recorded so nobody over-reads these numbers:** the questions were written by the session
that wrote the glossary, so they flatter it. The query log on the box (`data/log.jsonl`) is the
source of better questions; add real ones to `eval/questions.jsonl` and rerun.
