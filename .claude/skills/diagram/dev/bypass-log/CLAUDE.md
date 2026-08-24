# `bypass-log/` - every attempt to run the expensive path, and what came of it

One JSON file per attempt: target, outcome (permitted / cancelled / refused), the written
reason, and the commit. Read it with
`make audit`; never edit or delete an entry to make the history look better.

**A CLAUDE.md rather than a README, deliberately**: this is a rule a session has to KNOW, and a
README is never loaded. See [`../perf-log/CLAUDE.md`](../perf-log/CLAUDE.md) for what that cost.

## Why a directory and not one log file

**The same reason as [`../perf-log/`](../perf-log/README.md), and this file exists because that
lesson had to be learned twice.** Several session clones work on this engine at once, and an
append-only shared log conflicts on EVERY concurrent push: two sessions add lines at the same offset
and git has no way to know which goes first. The merge is textual; the content is not. A file per
entry never conflicts, because git merges disjoint new files without being asked.

The first version of this log was a single `run-log.jsonl`, written on 2026-08-24 by a session that
had read `perf-log/README.md` earlier the same day and quoted it. The GM caught it: *"I thought that
the general way to deal with this would be to have a directory rather than a file... I'm not sure if
you implemented a single file because you figured out that this will not be a problem or if my
instructions simply got dropped."* Neither - the pattern was in the repo and went unapplied.

## Why it exists at all

GM 2026-08-24: *"if there exists a make done that can be run in order to run the full tests, do we
still have the ability to audit that it is only being run when we have fully completed a feature?
... not just confirming that in the moment, but also being able to audit after the fact."*

Before this, only BYPASSES were recorded, so plain `make done` usage was invisible and that question
had no answer. Elapsed seconds are recorded too: a target that quietly gets slower shows up in the
history rather than in someone's memory, which is how `make quick` reached 254 s unnoticed.


## What the outcomes are for

`permitted` / `cancelled` / `refused`. Without `outcome` a session that read the warning and backed
out is indistinguishable from one that never tried, and the log cannot answer the question it exists
for. **A rising count of `cancelled` is the early signal that the cheap path has stopped being
sufficient** - at which point the answer is to make the fast path better, not to keep refusing.

The 2026-08-24 audit of the pre-guard entries found 3 of 5 UNJUSTIFIED: full sweeps run after the GM
had set the bar at the reference settlement alone, one of them re-verifying a whitespace fix. The log
had recorded all five and stopped none, because the override could be supplied on the command line
and skipped the prompt entirely. An audit trail records a decision; it does not make one.
