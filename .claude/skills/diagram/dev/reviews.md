# Invoking a review agent

**Load this file when:** You are about to launch `settlement-review`, `building-review` or `backstory-review`.

Split out of [`../CLAUDE.md`](../CLAUDE.md) so it is not in every diagram session's
context. The text is verbatim; the short always-on version of each rule stays in the index.

## Invoking a review agent: SCOPE it, SPLIT it, and launch it EARLY

`settlement-review` is mandatory before a Mode B map ships, and it is also the single most expensive
thing a session waits on. Measured 2026-08-08, on a change that resized some captions: one agent,
two maps, a full audit - **12.3 minutes, 22% of the whole task's wall clock**, with this session idle
for 11.4 of them. The findings were right; two of the five had nothing to do with the change and had
been sitting in the pool for weeks.

Three rules, all of them free:

- **Say the SCOPE.** The agent now takes `DELTA: <what changed>` and reviews the change, whatever the
  re-pack moved, and whatever the change made incoherent - skipping the spelling/twin/nuisance/traffic
  sweeps and saying which it skipped. Reserve `FULL` for a new or heavily-rewritten map. A caption
  resize is a DELTA.
- **One map per agent, launched in parallel.** The sweeps share no work across maps, so handing two
  maps to one agent just serializes two audits behind one notification.
- **Launch it the moment the motivating map's regen + gate is green - BEFORE your own visual
  pass**, the docs and the commit. Everything you do while it runs is free; everything after it is
  added on. Measured 2026-08-16 (the cut-bank fix): the review agent was the whole task's
  critical-path TAIL - its last 84s ran past an already-green `make done` - and it was launched
  only after a 52s reasoning turn plus the session's own crop reads. The reviewer independently
  re-verifies that ground anyway, so every second of your own pass spent before the launch is a
  second added to the task's total.

Same three rules apply to `building-review` and `backstory-review`.
