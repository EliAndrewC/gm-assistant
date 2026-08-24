# Where the hamlet lane work stands (2026-08-24)

**Load this if you are picking up the lane/ordering work.** It replaces the feature-126 handoff,
because feature 128 closed most of what that file was warning about.

## The order, settled

    water, fields, drainage  ->  FARMHOUSES  ->  every lane, without exception

The GM, stating it (2026-08-24): *"We are reordering the procedural layout of the hamlet generation
so that farmhouses are rendered after the fields and water, but before any village lanes. That is
what the feature is. Full stop."*

**ANY lane.** There is no exogenous class, no connector exception. This was argued four separate
times across two features and is now closed - and NOT reopenable by a research argument, because a
road CAN predate a settlement in the world, which is exactly why that argument would always be
available. The reason that decides is ground reservation: a lane drawn before the houses registers a
no-build corridor the placer then refuses seats against, whatever the lane represents.

| stage | draws | lanes on the map |
|---|---|---|
| `stage_water_frame`, `stage_field`, `stage_sink` | the water and the fields | 0 |
| `stage_seat` | NOTHING - it decides where the cluster sits | 0 |
| `stage_homesteads` | the farmhouses | **0** |
| `stage_track` | the connector and the field spur | 2 |
| `stage_appurtenances` | wells, byres, sheds, yards | 2 |
| `stage_web` | the alley web | more |

## What feature 128 had to learn, so you do not repeat it

- **`stage_ways` did two jobs**, which is why 126 could not simply reorder: it SEATED the cluster
  (`plan.seat`, a hard dependency of `stage_homesteads`) and it DREW. Split into `stage_seat` and
  `stage_track`.
- **The obligation inverts with the order.** Lanes laid first were corridors the houses avoided;
  laid last, nothing stops a track being drawn through a farmstead. `_thread_the_fabric` routes each
  track round the standing steadings and clips what is drawn.
- **A route that STARTS inside the fabric cannot be routed out of it.** Both tracks began at points
  derived from the predicted seat band; with houses placed first, those points sit inside the cloud.
  `_cluster_gateway` measures the placed cloud instead. This was 126's unfinished T009 and it was
  load-bearing, not polish.
- **The bearing has to know the houses are there.** Routing and clipping cannot rescue a connector
  aimed through the cluster: `_route` declines every connector outright (its lattice exceeds the
  90,000-cell cap at canvas span) and a clip can only SHORTEN a run. So `connector_track`'s sweep
  ranks bearings against the steadings - wet ground, then steadings, then crops. Mizuguchi is the
  map that proved it; the write-up is in its notes file.
- **Proximity, not crossing, is the question about a farmstead.** `path_violations` asks
  `crosses_poly`, which is right for a paddy and wrong for a house, because a lane is DRAWN WITH A
  WIDTH and the overlap matrix sizes every lane at 6 ft. Mizuguchi's connector crossed nothing at
  all and still overlapped a garden.
- **A gap test must measure from BOTH shapes.** `_crosses_fabric` measured `edge_dist` at the run's
  own vertices, which is blind to anything beside the middle of a long segment - and a connector's
  segments are hundreds of pixels long.
- **`stage_track` sits BEFORE `stage_appurtenances`**, not after. A well is not a farmhouse, and
  threading a fabric that already held every wellhead put a connector 3.6 px from one. A well is dug
  where people already walk.

## Still open

- **The lane web breaks into islands.** Four of Inashiro's fragments touch nothing, at 28.1-28.5 ft
  against `WEB_CLEARANCE = 28.0` - each web lane REGISTERS that clearance as its corridor, so the
  next one routes exactly one clearance short of the way it meant to join. `_LANE_JOIN = 40.0` sits
  above it, so the gate welds them into a "component" the ink does not contain. Both halves of the
  fix, and the measurements, are in `future-work/farming-communities.md`.
- **The cohort.** Seeds 8, 18, 23, 42, 47 fail, plus 12 and 39 which predate all of this. The GM's
  standing limit is the reference hamlet at one seed, so the cohort has not been the bar - but it is
  the obvious next question.
- **The rescue passes.** `_serve_stragglers`, `_join_orphan_ways`, `_bridge_collinear_breaks` are
  three repair passes stacked on the lane derivation. Three repairs on one derivation is a smell,
  and 128 deliberately did NOT touch them so that its own effect stayed measurable. Worth asking
  whether the derivation, done right, needs them at all.
- **Generation speed.** Feature 126 cost ~51% (total 261 s -> 394 s across the bookend seeds) and it
  was never diagnosed - it shipped because `perf-report` printed "diagnose before shipping" and
  exited 0. Both halves are closed now, and the measurement is in
  [`../future-work/farming-communities.md`](../future-work/farming-communities.md). The larger
  separate prize is `place_kosatsuba`: ~36% of every build to site one signboard.
- **Dispersed and linear forms** stay pinned to nucleated. If linear is ever unpinned, the
  `spec-fidelity` reviewer flagged one sentence to re-adjudicate as an exception request: a linear
  hamlet seats houses ALONG the connector, so it needs the route known before seating - a route is
  not a corridor, and nothing may be reserved.

## How to work here

`make explain` when the reference map is red - it prints every failing check WITH its message, and
attributes an overlap to the lane that caused it. It exists because when the reference map is the
thing under surgery, every other target refuses to run.
