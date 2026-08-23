# `perf-log/` - how long the generator took, over time

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
