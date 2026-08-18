# Research: the lane web

## R1. The historical finding, and how it splits

Recorded in full at `.claude/skills/diagram/research/homesteads.md` ("Is every farmhouse reached by
a lane, and in what FORM?"). It splits exactly along the two rungs of constitution Principle XII's
ladder, which is why it is the worked example:

- **Decisive - access.** "Every house in the nucleated village is accessible via the interconnected
  system of narrow lanes and alleys"; the gridiron of narrow lanes is "functionally the most
  efficient form of compact settlement". Compactness exists FOR the access. Implement it.
- **Two-formed - the shape of that access.** Alleys off a spine (accretive; laterals colonised as
  semi-private space by the adjoining house) OR a back lane behind the plots (planned; "back lanes
  on each side of the main street", dividing village from agricultural land). Both attested,
  neither dominant. Knob it.

**Decision**: the axial coverage is unconditional; its FORM is a `lane_web` knob.

## R2. Where the defect actually is - MEASURED, not reasoned

The ledger said "the back rank is not served", which implied a DEPTH problem. It is not. Measuring
the four pool hamlets in each cluster's own principal frame (PCA over the seated house centers):

| map | skeleton | houses | cluster major x minor | aspect | unserved (>120 ft) | where they are |
|---|---|---|---|---|---|---|
| sawada | Y | 19 | 808 x 235 ft | 3.43 | 9 | major offset 65-370 ft, one at -319 |
| inashiro | spine | 15 | 716 x 220 ft | 3.26 | 6 | major offset 157-360 ft, two negative |
| kashikawa | T | 20 | 994 x 278 ft | 3.58 | 5 | ALL at major -168 to -478 |
| mizuguchi | Y | 12 | 518 x 279 ft | 1.86 | 5 | major +/-196-279 |

**Every unserved house is at a large offset ALONG the cluster's long axis.** The minor offsets are
small everywhere. So this is a LATERAL coverage failure, and the cause is a size mismatch that has
been in plain sight:

- `skeleton_layout` is called with `seat["lat"]` / `seat["dep"]`, so its arms span the seat band.
- `front_row` samples the outline out to `seat["lat"] * 1.6`, so the houses span **1.6x** that.

The lanes therefore huddle in the middle of a cluster that is 1.6x longer than they are. Kashikawa
is the clearest case: it is a `T`, its crossbar DOES run along the long axis, and the crossbar got
clipped off on the negative side - which is precisely the side all five of its unserved houses are
on. **Alternative rejected**: adding a spur per orphaned house. That is pinning (a lane derived from
where a house happened to land), it multiplies short dead-end treads, and `lanes_reach_something`
would then be satisfied by construction rather than tested.

## R3. The reach threshold, derived rather than chosen

`lanes_reach_something`'s existing 90 ft house-reach was flagged in `future-work.md` as "a number
nobody has justified", and the new rule must not repeat that. The honest basis is already on the
map: **`BUNDLE_PITCH` = 100 ft** is the ground one homestead occupies, and it is the spacing
`front_row` samples at because "two homesteads cannot stand closer than that". A house whose center
is within one pitch of a way has that way passing its own plot or its immediate neighbor's - which
is what "colonised as semi-private space by the adjoining house" describes. So `WEB_REACH_FT =
BUNDLE_PITCH`, ONE definition, read by the generator and the gate alike.

It also sizes the alleys: laterals every <= `2 * BUNDLE_PITCH` put any house between two of them
within one pitch of one. The threshold and the spacing are the same number used twice, which is what
makes the rule self-consistent instead of two magic constants that happen to agree today.

## R4. Both forms satisfy the rule BY CONSTRUCTION

With `ex` widened to the real house span and `ey` the cluster depth (layout frame: x along the
margin, +y away from the field):

- **back_lane** - two axial lanes at `y = +/- ey * 0.66`, each spanning `+/-ex`. A middle-rank house
  is `0.66 * ey` ~ 83 ft from one; a front- or back-rank house ~43 ft. This is the "back lanes on
  each side of the main street" framework, and the +y lane sits on the non-field side, behind the
  plots, exactly where the sources put it.
- **alleys** - one axial lane at `y = 0` spanning `+/-ex`, plus laterals spanning `+/-ey` at every
  `2 * BUNDLE_PITCH` along x. A house is within one pitch of a lateral along x, and a lateral spans
  the full depth, so the depth offset costs nothing.

Both are computed from `(ex, ey, BUNDLE_PITCH)` alone - no house position is read, which is what
lets the web be laid BEFORE the houses, where it belongs (a lane is a no-build corridor the
homesteads front).

## R5. What clipping can still take away

Web arms go through the same clip-and-trim path as every other skeleton arm: out of the crop, off
the wet toe, off marsh, stopping at a watercourse rather than crossing it. That can shorten an axial
lane and reopen a gap - which is how kashikawa's crossbar died. This is expected and the gate is the
oracle: `farmhouses_reach_a_way` measures what was DRAWN. If the cohort shows clipping routinely
defeating coverage, the fix is in the routing, not in relaxing the check.

## R6. Ordering

The web is laid inside `stage_ways`, with the rest of the skeleton, before `stage_homesteads`. That
preserves the existing invariant (homesteads front the corridors) and needs no change to `STAGES`.
Laying a web AFTER the houses - threading the residual gaps, which is how a real accreted alley
forms - was considered and rejected for now: it would need a new stage between 5 and 6 and it makes
the alleys' geometry depend on placement order, which is the harder thing to keep deterministic.
