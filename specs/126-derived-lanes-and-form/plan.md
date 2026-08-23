# Implementation Plan: Derived lanes, and settlement form as a rolled knob

**Feature**: 126-derived-lanes-and-form
**Spec**: [spec.md](spec.md)
**Research**: [research.md](research.md)
**Date**: 2026-08-23

## Summary

Split the hamlet's ways by PROVENANCE rather than by timing. Ways that genuinely predate the
settlement (the connector to the off-map road, the field spur) stay before the houses; the internal
skeleton moves after them and is derived from where the houses actually landed, using the `web_cuts`
solver that already does exactly this for the lane web. Then roll the settlement FORM per seed -
nucleated, dispersed, linear - and make the two access rules state the form they apply to. Finally,
replace the uniform farmstead pitch with a bearing-dependent shadow test, so farmsteads may stand
close east-west where no shadow falls.

## Technical Context

**Language**: Python 3.14, `mypy --strict`, `ruff`, 100% line coverage on pure-logic packages.
**Primary paths**: `.claude/skills/diagram/l7r/diagram/hamletgen/` (driver, ways, homesteads, water,
consts, hinterland), `settlement/_knobs.py`, `settlement/rolling/`, `check_village/segments_07c`.
**Test bed**: the 48-seed cohort (`tools/cohort_audit.py`), plus the four live scripted pool hamlets.
**Single-artifact target** (constitution VI, added mid-feature 2026-08-23 BECAUSE this feature
violated it): **Inashiro** for the ordering change; plus one seed per rolled form once the form knob
exists, since a single map cannot exercise a knob - seed 7 (nucleated), seed 6 (dispersed), seed 4
(linear, which is what Inashiro itself now rolls). ~30-60s per map. The 48-seed cohort runs ONCE, at
the end. It was instead used as the iteration loop twice here, and both runs were killed without a
result: the first ran 30 minutes with 19 of 20 workers idle while one seed near-hung.

**Baseline**: taken on unmodified `HEAD` (8ec2a91) in a detached worktree at `scratchpad/base125` -
48-seed cohort plus a full `make done`. Required by Principle XIII before any comparison is claimed.

**Resolved during Phase 0** (no NEEDS CLARIFICATION remain):

- What `stage_homesteads` takes from `stage_ways` - answered by reading, not assumption (R1). The
  answer changed the design: `plan.seat` is the real dependency, not the lanes, so the pre-house
  stage shrinks rather than disappearing.
- Historical grounding for the dispersed and linear forms (R2, R3).
- The shadow corridor's geometry as a function of bearing (R4).
- Whether the access rules become form-conditional or waived - form-conditional (R5).
- The settled stage sequence (R6).

## Performance bookends (constitution VI - added mid-feature 2026-08-23 BECAUSE this feature regressed)

| | label | total | median | worst | notes |
|---|---|---|---|---|---|
| before | `126-start` | see `dev/perf-log/` | | | taken retroactively from the untouched worktree at `8ec2a91` |
| after | `126-end` | | | | before the push |

**This feature is the reason the rule exists.** Moving the skeleton after the houses took seed 25
from 65s to 160s, and nothing surfaced it: two 48-map cohorts were launched, ran 30 and 15 minutes
with 19 of 20 workers idle behind one stalled seed, and were killed without producing a result.
A four-seed reference sweep would have shown it in about three minutes, before any cohort ran.

Known going in, to be resolved at the `126-end` bookend: seed 25 is ~2.5x the baseline while seed
39 is ~2.8x FASTER. A net that is favourable on average still owes an explanation for the outlier.

## Constitution Check

| Principle | Status | Note |
|---|---|---|
| **I. Independent review** | PLANNED | `settlement-review` on every re-rolled pool map. The author of a map is not its reviewer, and the whole point of this change is visual. |
| **III. Pool data conventions** | OK | No new pool tier; the four live hamlets re-roll in place. |
| **VI. Verify before done** | PLANNED | `make done` green, cohort measured against the recorded baseline, artifacts spot-checked rather than relayed. |
| **X. Python discipline** | PLANNED | ruff + `mypy --strict` + pytest + 100% coverage on the touched pure-logic modules. No file crosses ~1,000 lines as a result; `ways.py` is watched, since it gains the derivation and loses the skeleton. |
| **XII. Historical grounding** (NON-NEGOTIABLE) | **SATISFIED, and it drove the design** | The research ladder ran properly: the access question was already researched and decisive for nucleated; the FORM question came back genuinely multi-form, so it becomes a seeded knob rather than a choice (R2, R3). Findings are written to the durable record, not only to this feature - see the storage tasks below. |
| **XIII. No known regressions** (NON-NEGOTIABLE) | PLANNED | Baseline taken in a detached worktree, never by stashing. Because a seed's FORM is now rolled, per-seed comparison degrades; the spec falls back to the documented rule - pass RATE must not drop, and every newly-failing check is diagnosed individually. |
| **XIV. Fix defects where you find them** (NON-NEGOTIABLE) | ACCEPTED | Defects surfaced by this work or by the reviews get fixed in it. |

**No violations to justify.** The one item worth flagging is scale: this is an architecture change to
the placement pipeline, which is exactly the case Principle XIV carves out as too big for an in-flight
fix - hence a spec-kit feature rather than a tweak, which is the GM's explicit instruction.

## Design

### The sequence (settled in R6, restated because it is the contract)

`stage_ways` -> **`stage_track`** (keeps `seat_cluster`/`plan.seat`, watercourses, connector, field
spur; loses the internal skeleton). `stage_web` -> **`stage_lanes`** (derives the internal skeleton
AND the web from placed houses). `stage_water_frame` additionally rolls `settlement_form`.

Everything else keeps its position. Stage count stays 13.

### Form behavior

| | nucleated | dispersed | linear |
|---|---|---|---|
| seating | front row + cloud | spread along the margin | frontage on the CONNECTOR |
| internal lanes | full derived web | **none** | minimal, if any |
| shelter grove | one village grove | **per farmstead** (*kainyo*) | one village grove |
| access rules 0607/0610 | apply | **do not apply** | apply |

### The shadow corridor - SUPERSEDED, see research.md R8

This section proposed replacing the uniform `BUNDLE_PITCH` separation with a bearing-dependent
shadow test. **It is withdrawn: the rule already exists.** `_sun_corridor_ok` keeps 39 ft of open
ground south of every threshing yard, bidirectionally between neighbors, gated by
`yards_unshaded_by_neighbors`; feature 121 already replaced circle-spacing with real rotated
footprints; and `BUNDLE_PITCH` is already only a row-planning constant. The proposal was written
from a stale comment on that constant, which has been corrected. No code change - implementing one
would be a second implementation of a rule the checker owns.

## Risk register

| Risk | Mitigation |
|---|---|
| Removing `lane_frontage` for nucleated loses a seat pass that currently places real houses | `cluster_seeding` meta already records whether a map seated by "cloud" or "frontage" - measure the four pool maps BEFORE the change to know the blast radius, not after. |
| The connector's new origin (seat band edge, not skeleton gateway) changes every map's exit | Called out in R6 as the one genuine behavior change. Verify `connector_lane_runs_off_edge` still passes across the cohort. |
| Form roll makes per-seed regression comparison meaningless | Documented fallback: pass RATE governs, every newly-failing check diagnosed individually. Also record each seed's rolled form so a comparison can be made WITHIN a form. |
| Three forms means three times the visual surface, reviewed by its author | One `settlement-review` per re-rolled pool map, and at least one map per form in the reviewed set. |
| Coverage on newly form-conditional branches | The dispersed and linear paths need cohort seeds that actually exercise them; roll weights must not make a form so rare it is untested. |

## Research storage (a deliverable, not a side effect)

The GM asked for this explicitly on 2026-08-23: *"I know that sometimes we do research that does not
actually end up being stored in the correct places. So I wanna make sure that we capture this both
the reasoning that we are applying and the specific research that you did."*

Three destinations, three different jobs:

1. **`research/homesteads.md`** - the durable, skill-level historical record, where the existing
   lane-form entry already lives. Gets the DISPERSED (R2) and LINEAR (R3) findings written to the
   same standard as the existing entry, with sources.
2. **`specs/126-.../research.md`** - this feature's decision reasoning: what was chosen, why, and
   what was rejected. Already written.
3. **At the point of change** - a record-the-why comment beside every constant that moves or retires,
   including the RETIREMENT of `_FRONT_ROW_LANE_CAP` and the reason it must not be re-tuned.

Plus `dev/placement.md`, the rulebook, whose STAGES table describes the order this feature changes.

## Documentation deliverables

- **`dev/placement-stages/hamlet-placement.html` must be regenerated and its per-stage prose
  updated** (GM, 2026-08-23). This is deliberately NOT automated on sync - it is a one-time
  deliverable of this feature, because this feature reorders the very stages that page exists to
  explain. Its `NOTES` entries for the renamed and moved stages must be rewritten, not merely
  re-rendered, and the page should show a map whose form is worth showing.
- `dev/placement.md` STAGES table and the phase-model notes.
- `migration-plan.md` status, if the hamlet tier's row changes.

## Progress

- [x] Phase 0: research.md - all five questions resolved
- [x] Phase 1: design (this document), data-model.md, quickstart.md
- [ ] Phase 2: tasks.md
- [ ] Implementation
