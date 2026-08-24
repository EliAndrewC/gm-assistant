# `perf-log/` - how long the generator took, over time

> **This was a README until 2026-08-24, and the rename is not cosmetic.** A README is not loaded into
> a session's context; a directory `CLAUDE.md` is, automatically, whenever work happens here. The
> "why a directory and not one log file" rule below was written in this file, read by a session
> during an unrelated audit, and then broken by that same session hours later when it created a
> single-file `run-log.jsonl`. Had this been a CLAUDE.md the rule would have been in context at the
> moment it mattered. **A README is written by a human for a human; anything a session must KNOW
> belongs in a CLAUDE.md or a doc a CLAUDE.md points at.**

One JSON file per snapshot. **Never edit these; never delete one to make a trend look better.**

    make perf                 # record a snapshot (label it: make perf LABEL=126-start)
    make perf-report          # print the trend, latest vs the one before
    python3 -m l7r.diagram.tools.perf_snapshot --report --against 126-start

## Why a directory and not one log file

Several session clones change this engine at the same time, and an append-only shared log conflicts
on every concurrent push - the merge is textual, the content is not, and resolving it by hand is
exactly the kind of chore that ends with someone deleting rows. A file per snapshot never conflicts,
because git merges disjoint new files without being asked.

The filename carries `<utc>-<label>-<clone>`, so the trend reconstructs WHO changed WHAT and WHEN
without opening anything: a run of slow snapshots all from one clone is a feature that regressed,
while a step across every clone at once is the machine or a dependency.

## What a snapshot measures

The REFERENCE HAMLET - Inashiro's spec, held fixed - rolled across a fixed set of seeds, timed per
stage. Seeds rather than maps, because one map proves nothing about performance: a seed can be
pathologically good as easily as bad. The seed set deliberately includes the slowest seeds known
when it was chosen, so a comfortable average cannot hide a stalled outlier.

This does NOT replace `GEN_TIME_BUDGETS` in `tests/test_villages.py`. That is a per-gen CEILING that
fires when one pool map goes pathological. This is a TREND, and it answers the other question: is
the generator getting slower, and since when.

## The bookends

Constitution VI requires a diagram spec-kit feature to record `<NNN>-start` before it changes
anything and `<NNN>-end` before it ships, and to diagnose any seed more than 5% slower. The 5% is
the project's own threshold for a whole-process speedup mattering, applied in the other direction.
