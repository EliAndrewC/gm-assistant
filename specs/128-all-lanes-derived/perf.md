# Feature 128: the performance diagnosis constitution VI asks for

**Verdict: ships.** Total across the seed set **382.5s -> 268.2s, -29.9%**, well inside the 10% cap.
Three seeds are individually more than 5% slower and each is diagnosed below, which is what the
per-seed band requires.

    128-end vs 128-start:
      seed   4    23.7s ->   26.8s   +13.1%  <-- SLOWER
      seed  25   222.7s ->   80.6s   -63.8%  faster
      seed  39    67.8s ->   71.5s    +5.5%  <-- SLOWER
      seed  47    68.3s ->   89.3s   +30.7%  <-- SLOWER
      TOTAL      382.5s ->  268.2s   -29.9%

## THE NEW CODE IS NOT THE CAUSE, and that is measured rather than argued

The obvious suspects were the two paths this feature added to every build: `_fabric_hits`, which the
connector's bearing sweep runs for all 41 candidate bearings, and `_pull_back_to_service`, which walks
the connector against the whole way network. Both were benchmarked on Kashikawa's real geometry - 110
fabric polygons, 148 network segments:

| path | cost | share of an 80 s generation |
|---|---|---|
| one full 41-bearing sweep of `_fabric_hits` | 148.7 ms | 0.19% |
| one `_pull_back_to_service` on the connector | 80.1 ms | 0.10% |
| **both together** | **228.8 ms** | **0.286%** |

A 30% swing on a seed cannot come from 0.286% of the work. (One real cost WAS found and fixed on the
way: adding the fabric term made the sweep run all 41 bearings instead of stopping at the first clean
one, because a bearing that used to score zero now often scores a steading. That was +25% on the
reference seed and is now pruned lexicographically - a candidate already behind on wet and steadings
cannot win, so its expensive crop term is never computed. Seed 4 went +25.3% -> +13.1%.)

## WHAT IS ACTUALLY HAPPENING: the maps are different maps

This feature reorders the pipeline so the houses are seated before any lane is drawn. That changes
the geometry of every settlement it touches - Inashiro's cluster long axis went 603 -> 462 ft and its
aspect 2.88 -> 2.31. **A seed's before-and-after is therefore not the same work measured twice**; it
is two different settlements, each with its own amount of work in the stages that dominate a build
(`place_kosatsuba` alone is ~36% of one).

The spread is the tell. A uniform slowdown moves every seed the same way. This one moved seed 25 by
-63.8% and seed 47 by +30.7% in the same run - which is what a changed workload looks like, not a
slower generator. The aggregate is the measure that survives the change, and it is down 30%.

## Accepted, in writing, with the numbers

Seeds 4 (+13.1%), 39 (+5.5%) and 47 (+30.7%) are **accepted**: their maps changed shape, the
generator did not get slower, and the total fell 29.9%. If a later feature that does NOT reorder
anything sees the same per-seed pattern, this reasoning does not transfer - per-seed comparison is
meaningful again the moment the maps stop moving.

## The rule this run changed

Under the old rule any single seed over 5% returned nonzero, so this feature would have been blocked
by seed 39's +5.5% while the generator was 30% faster overall. The GM set the two bands on
2026-08-24 (constitution VI, v1.16.0): per-seed 5% DIAGNOSES, the total 10% BLOCKS.
