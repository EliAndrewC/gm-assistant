# Feature 124: Two lane ends may not front the same farmhouse from the same side

**Status**: specified
**Created**: 2026-08-18
**Origin**: a `settlement-review` finding on Mizuguchi, ledgered during feature 123 as the one
defect that feature could not reach. The GM asked for it to be fixed rather than left
(2026-08-18: *"it does seem like this is something that is worth fixing"*).

## Why this exists

Three ways leave one node on Mizuguchi's east side at bearings 19.7 / 8.7 / 356.8 degrees - a
**22.9 degree total spread**, with adjacent gaps of 11.0 and 11.9 - and two of the three end blunt in
open ground. At 3x zoom the reviewer read it as **a broom, or a bird's foot**: not three ways, one
way drawn three times with the ends fanned.

It is not slack, and it is not the lane web. Both of the offending arms are **skeleton** lanes laid
by `stage_ways` BEFORE the houses exist. That timing is the whole defect:

- The web's shadow rule lives in `_lay_web_lane` and tests a new WEB run against what is already
  drawn. The skeleton's arms are drawn before any of that and are **never tested against each
  other**, so two arms may run the same corridor for their whole length with nothing objecting.
  Measured on Mizuguchi: lane 2 is within 30 ft of lane 0 for **100%** of its 127 ft (median 12.3 ft)
  and within 30 ft of lane 4 for 100% of it - **three treads in one 25 ft corridor**.
- `lanes_reach_something` is silent for a reason that is worth stating plainly: it asks each lane end
  to reach a way within 40 ft **or a farmhouse within 90**, and all three blunt ends claim **the same
  house** - at 66.9, 55.1 and 40.0 ft. One farmhouse is discharging the obligation of three separate
  lane ends standing within 40 ft of each other.

The reviewer named the missing rule exactly, and this feature is that sentence: **two lane ends may
not front the same farmhouse from the same side.**

## User scenarios

### US1 (P1) - A hamlet's ways read as a network, not as a frayed rope

A GM looks at the east side of Mizuguchi and sees one lane arriving at the cluster, not a three-toed
fan of near-parallel stubs. Nothing about the map's function changes; what changes is that it stops
reading as a drafting accident.

**Independent test**: no two internal lane ends within 40 ft of each other, at bearings under ~25
degrees apart, share the nearest farmhouse.

### US2 (P1) - The rule is enforced where it can be seen, on every tier

The gate gains a check, because this is the third time a near-parallel pair of ways has been caught
by eye rather than by the battery - the notes already record "a near-parallel contact does not count
as arrival ... proximity is not arrival" from an earlier round, and that rule was written for a
LANE'S OWN end, not for two ends beside each other.

**Independent test**: the check fires on the pre-fix Mizuguchi manifest, which is frozen as its
negative fixture.

## Functional requirements

- **FR1** A gate check: no two internal lane ends may front the same farmhouse from the same side.
  "Same side" is a bearing test, so a genuine crossroads - two ends arriving at one house from
  opposite quarters - is not caught.
- **FR2** The generator stops producing them, by testing a skeleton arm against the arms already laid
  the way a web run is tested against the network.
- **FR3** The fix may not cost coverage: no farmhouse may lose its way, and
  `farmhouses_reach_a_way` stays green on the pool and on the in-gate cohort.
- **FR4** The pre-fix manifest is frozen in `pool/regressions/` and the check demonstrably fires on
  it before anything is fixed.

## Success criteria

- **SC1** Zero same-house end pairs across the four pool hamlets and the 24-seed cohort.
- **SC2** `make done` green; in-gate cohort stays 4/4; no pre-existing check regresses
  (Principle XIII, baseline in a detached worktree at the feature's start).
- **SC3** `settlement-review` on the re-rolled maps confirms the fan is gone and reports no new
  defect in its place.

## Assumptions

- The four live scripted hamlets re-roll; the 19 legacy maps stay FROZEN.
- Trimming is preferred to re-routing: the reviewer's own minimum change was "trim lane 2 back to the
  node - it is 100% shadowed by lane 0 over its whole length and costs nothing", since the only house
  it serves is 23.7 ft from another lane.

## Out of scope

- The five seeds in feature 123's 24-seed sweep that fail `farmhouses_reach_a_way`. Related in
  spirit, not in mechanism, and not yet diagnosed - the first attempt measured maps built with the
  wrong household counts, so the residue is real but its cause is not established.
