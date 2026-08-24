# Feature Specification: Farmhouses Before Lanes

**Feature Branch**: none - this project does not use feature branches (`SPECIFY_FEATURE=128-all-lanes-derived`)

**Created**: 2026-08-24

**Status**: APPROVED - `spec-fidelity` verdict FAITHFUL at round 2

**Input**: [`gm-request.md`](gm-request.md), verbatim and unedited.

**Supersedes**: [`specs/126-derived-lanes-and-form/`](../126-derived-lanes-and-form/) **FR-003, in
full.** Everything else 126 landed stands and is not re-derived here.

## The feature, in the GM's words

> *"We are reordering the procedural layout of the hamlet generation so that farmhouses are rendered
> after the fields and water, but before any village lanes. That is what the feature is. Full stop."*

That sentence is the specification. Everything below serves it.

    water, fields, drainage  ->  FARMHOUSES  ->  every lane, without exception

## Why the current order is wrong

**Because a lane reserves ground.** `s.lane(..., clearance=LANE_CLEARANCE, worn=True)` appends to
`self.corridors` and records a tread (`settlement/water_ways.py:514`), and `_fits` refuses any house
whose center falls in a corridor or on a tread (`settlement/houses.py:309-311`). `STAGES` runs
`stage_ways` before `stage_homesteads`, so both of the ways it draws - the connector at `ways.py:1555`
and the field spur at `ways.py:1535` - have taken ground before a single house is seated.

That is the GM's complaint, unchanged since feature 126: *"the lanes being there was the thing that
was making it difficult to lay out the farmhouses."*

**This is deliberately NOT argued from provenance**, and the correction matters. An earlier draft
justified moving the spur by claiming a path to a hamlet's own field cannot predate the households
who walk it. The fidelity review showed that is not universally true - land can be assarted and
worked from an older settlement before anyone lives beside it, a bund or boundary track can already
run along a paddy, a hamlet can be founded against an existing through-path. Resting the case on
provenance also produced a false asymmetry, since it made the spur obviously movable and the
connector arguable. **The reason that actually carries is the one the GM gave and the code confirms:
a lane drawn first takes ground the houses then cannot have.** That is true of every lane regardless
of what it represents.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - No lane exists when the houses are seated (Priority: P1) MVP

The whole feature, as one testable statement.

**Independent Test**: at the moment `stage_homesteads` returns, the manifest holds no lane of any
kind and no lane corridor or tread is registered.

**Acceptance Scenarios**:

1. **Given** any hamlet, **When** the houses are being seated, **Then** no lane exists and no lane
   corridor or tread constrains any candidate seat.
2. **Given** the seated houses, **When** the lanes are drawn, **Then** every one of them - connector,
   field spur, cluster skeleton and lane web alike - is laid after them.
3. **Given** the reference hamlet, **When** it is rolled, **Then** every gate check still passes.

### User Story 2 - Each lane is positioned from where the houses actually are (Priority: P1)

Laying a lane late is not the same as deriving it from the houses. A way drawn afterwards can still
be positioned from a prediction, and today both are.

**Why this matters**: `stage_ways` calls `skeleton_layout` over the PREDICTED seat band to find the
connector gateway (`ways.py:1474`), and the spur starts at the band's own center. The band and the
houses disagree, and that mismatch is the recorded root of the `farmhouses_reach_a_way` defect that
survived seventeen attempts. Feature 126's task T009 named this and was never done.

**Independent Test**: `skeleton_layout` is not called before `stage_homesteads`, and each lane's
origin lies on the placed cluster's own extent.

**Acceptance Scenarios**:

1. **Given** placed houses, **When** the connector is drawn, **Then** its origin comes from their
   positions rather than from the seat band.
2. **Given** placed houses, **When** the field spur is drawn, **Then** it runs from the settlement as
   it stands to the field.
3. **Given** a hamlet whose houses spread wider than the band predicted, **When** it is rolled,
   **Then** every lane still meets the settlement.

### Edge Cases

- **THE POLDER BRANCH DRAWS ITS OWN CONNECTOR AND RETURNS EARLY** (`ways.py:1499`, found by the
  fidelity review). The ordering rule has to be applied in TWO places, not one. A change that fixes
  only the valley path leaves polder hamlets reserving ground exactly as before, and the reference
  hamlet would not catch it.
- **A linear hamlet seats its houses ALONG the connector**, so that form needs the connector's ROUTE
  known before seating - but a route is not a corridor, and nothing may be reserved. The form is
  pinned to nucleated so nothing draws it today; the design must not make it unbuildable.
- **The connector must still reach the map edge** (`connector_lane_runs_off_edge`).
- **The spur must still avoid the crop** and meet water squarely where it crosses.
- **The front half of the order is unchanged**: water, fields and drainage still come first. This
  feature moves ONE boundary.

## Requirements *(mandatory)*

- **FR-001**: No lane of any kind may be drawn, and no corridor or tread registered, before
  `stage_homesteads` has placed the houses. This covers the connector and the field spur equally, in
  BOTH the valley and polder paths, and supersedes feature 126's FR-003 in full.
- **FR-002**: Each lane's position MUST be derived from the placed houses rather than from the
  predicted seat band. `skeleton_layout` MUST NOT be called before the houses exist.
- **FR-003**: A gate check MUST measure that no house was refused a seat by a lane, so the property
  is verified rather than argued.
- **FR-004**: The reference settlement (Inashiro, seed 4) MUST pass the whole gate.
- **FR-005**: The stage-by-stage walk-through page MUST be regenerated and its captions MUST match
  what the pipeline does. That page is how the GM reads the order, and a stale caption on it is what
  made this feature necessary.
- **FR-006**: Feature 126's FR-003 MUST be marked superseded, so a later reader does not implement it
  again.

**If the connector turns out to be unbuildable after the houses**, that is an EXCEPTION REQUEST and
goes to an independent exception check against the GM's verbatim words (constitution XVI). It is not
pre-authorized here, and no requirement in this spec may be read as leaving that door open. The GM:
*"the spec should absolutely pre decide. that the connector must be drawn after all of the houses."*

### Scope Boundaries

**In scope**: the position of `stage_ways` relative to `stage_homesteads` in both branches; where each
lane's geometry is derived from; the reference hamlet; the walk-through page.

**Out of scope**, so the reviewer can hold the author to it:

- **The cohort.** Seeds 8, 18, 23, 42, 47 fail today. The GM's standing limit is *"only a working
  reference hamlet with a single seed"*.
- **The dispersed and linear forms.** `settlement_form` stays pinned to nucleated.
- **The rescue passes** (`_serve_stragglers`, `_join_orphan_ways`, `_bridge_collinear_breaks`). Three
  repair passes stacked on a derivation is a real smell, but changing them here would hide whether
  THIS change helped.
- **Generation speed.** Feature 126's ~51% slowdown is recorded in `future-work/`.
- **Way provenance.** Dropped after round 1: unrequested, inherited from 126's own unimplemented
  FR-004, not needed by FR-003's check (which reads stage order, not a manifest field), and a
  constant once every lane is endogenous.

## Success Criteria *(mandatory)*

- **SC-001**: At the moment the houses are seated, the manifest holds **zero** lanes and **zero** lane
  corridors. Measured, not argued.
- **SC-002**: The number of houses refused a seat by a lane is **zero**.
- **SC-003**: The reference hamlet passes the full gate.
- **SC-004**: Both perf bookends exist for the reference hamlet, and it does not regress more than 5%.
- **SC-005**: The walk-through page's plates and captions agree with the pipeline, checked by reading
  the page.
- **SC-006**: Feature 126's FR-003 is marked superseded.

## Assumptions

- `settlement_form` stays pinned to nucleated, so only that form is exercised.
- The gate's existing checks are the oracle; this feature adds one (FR-003) and changes none.
- The reference hamlet is Inashiro seed 4 (constitution VI).

## Review history

- **Round 2** - **`FAITHFUL`**. The reviewer swept the document for `except` / `still` / `unless` /
  `only when` / `MUST NOT` and confirmed the three `still`s preserve geometry checks rather than
  reopening ordering. It confirmed the pre-house lane emitters are exactly `ways.py:1499`, `1535` and
  `1555`, all three covered by FR-001, and that `338` and `995` already run after the houses.

  It named ONE sentence as the shape a fifth carve-out would take: the linear-hamlet Edge Case, which
  says that form needs the connector's ROUTE known before seating. It judged the sentence safe - it
  forbids reservation in the same breath, applies to a form that is pinned off, sits in Edge Cases
  rather than Requirements, and is fenced by FR-002 - but flagged it as **the line to re-adjudicate
  as an exception request if the linear form is ever unpinned.** Recorded here so that instruction
  survives the feature.

  Implementation note it raised: the `STAGES` comment block in `hamletgen/driver.py` is declared to
  be the DRAW ORDER map's authority, so it must move with the tuple.

- **Round 1** - `CHANGES REQUIRED` (4 findings), all accepted:
  1. **FR-004/US3 deferred the connector decision.** The reviewer reached the GM's ruling
     independently, and added an argument the GM did not need to make: the deferral CONTRADICTED the
     spec's own FR-003, since a way whose origin is a function of the placed houses cannot be drawn
     before them. The door was already closed; leaving it ajar was the 126 failure mode with better
     paperwork.
  2. **FR-005 (provenance) was unrequested** - 126's leftover, not needed by the check that cited it,
     and a constant once every lane is endogenous. Deleted.
  3. **SC-004 said "no seed"**, which can only be satisfied by running the cohort the same document
     excludes. Rescoped to the reference hamlet.
  4. **The spur's justification rested on a false claim.** "A field path cannot predate the
     households" is not universally true, and it produced the false spur-versus-connector asymmetry.
     Restated on ground reservation, which is verified in the code and is the reason the GM gave.
     This is the finding the review existed for: the claim was the AUTHOR's, the GM had accepted it
     in conversation rather than originating it, and a spec faithful to a false premise would have
     passed an ordinary fidelity check.

  The reviewer also verified the two other author claims as TRUE with precise citations, and found
  the polder early-return that means the ordering rule applies in two places.
