# Regression fixture: city_density_broken_nagahara.json

Snapshot of `pool/nagahara.json` taken BEFORE the 006-city-quarter-density feature, frozen as the permanent must-fail fixture (the discipline skipped in the prior wall-sizing effort: keep a known-bad map that the new checks are required to flag).

## The defect (what the GM saw)

A lopsided provincial city (target population 3,000): a densely packed east half, a NW temple quarter with zero commoner dwellings, a near-empty interior block, and ~35 commoner dwellings spilled OUTSIDE the north-east / south-east walls.

## Measured state at snapshot time

- In-wall dwellings: 525 (below the ~558 population floor for pop 3,000 at 7% tolerance).
- Extramural commoner dwellings: 35 (29 NE, 6 SE) - 17 laborer_large, 11 laborer, 3 merchant_house, 3 merchant, 1 servant.
- `M["quarters"]`: absent (the pre-feature manifest has no quarter declarations).
- NW temple quarter: 0 commoner dwellings.

## The "before" proof (why the old validator was blind)

At snapshot time this manifest **passes the full validator** (`ALL CHECKS PASSED`) and the capacity analysis reads **`WALL CAPACITY: ABOUT RIGHT`** (target 600, placed 560, inherent 636). The placed count of 560 = 525 in-wall + 35 extramural, because the old population count had no inside-the-wall filter, and the old capacity model was a global aggregate blind to distribution.

## What the new checks MUST do to this fixture

- `population_consistent_with_housing`: fire (525 in-wall < the ~558 floor once extramural dwellings stop counting).
- `city_commoner_dwellings_inside_walls`: fire (35 extramural commoners).
- `city_quarters_declared`: fire (no `M["quarters"]`).
- `city_capacity`: verdict `densify` or `shrink`, never `sized_and_packed`.

This fixture is wired into `test_regressions.py`; it must keep failing the new checks for the life of the feature.
