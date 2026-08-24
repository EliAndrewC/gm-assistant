# Tasks: Derived lanes, and settlement form as a rolled knob

> [!WARNING]
> **THIS FILE IS NOT A PROGRESS RECORD. Do not trust its checkboxes.**
>
> It carries 42 tasks and 0 ticks, including tasks that were fully completed - it was never
> maintained during implementation, which breaks the discipline the whole spec-kit flow rests on.
>
> Verified by inspection on 2026-08-24, these were **NOT** done: **T008** (rename `stage_ways` ->
> `stage_track`), **T010** (rename `stage_web` -> `stage_lanes`), **T009** (re-origin the connector
> from the seat band rather than the skeleton gateway - substantive, and the task file itself calls
> it the one place the reorder forces a real behavior change), and **T006 / FR-004** (the
> `provenance` field on lane records).
>
> **`.claude/skills/diagram/dev/RESUME-HERE.md` is the authoritative state.** Read it first.
>
> Also read FR-003 sceptically: it requires the connector *and the field spur* to stay ahead of the
> houses. That carve-out was written by the implementing session, not asked for by the GM, and the
> spur half of it does not survive scrutiny - a path to a hamlet's own paddy cannot predate the
> hamlet.


**Feature**: 126-derived-lanes-and-form
**Plan**: [plan.md](plan.md) | **Research**: [research.md](research.md) | **Model**: [data-model.md](data-model.md)

All paths are relative to `.claude/skills/diagram/` unless stated otherwise. Every command runs
inside the session clone `/gm-assistant/.clones/diagram-architecture`, never in main's tree.

**Baseline (recorded, do not re-take)**: 44/48 cohort on HEAD `8ec2a91`. Residue, all pre-existing
and ledgered, none introduced here: seeds 12 and 39 `paddy_bunds_do_not_stagger`, seed 24
`village_groves_visibly_stocked`, seed 37 `captions_clear_the_ways_they_stand_on`.

---

## Phase 1: Setup and measurement

- [ ] T000 Record the opening bookend on UNMODIFIED code: `make perf LABEL=126-start` (done retroactively from the detached worktree, since the rule postdates the feature), and read the existing trend for drift
- [ ] T001 Confirm the baseline gate in `scratchpad/base125` finished green and record its verdict in this file, so the comparison at the end has a recorded number rather than a remembered one
- [ ] T002 Finish the frontage-removal measurement (how many households still seat when `lane_frontage` returns nothing, on the four live specs) and record the result in [research.md](research.md) as R1a - this is the feature's single largest risk and it must be a number before US1 begins
- [ ] T003 [P] Record each cohort seed's current `cluster_seeding` and `cluster_shape` to `scratchpad/base_forms.json`, so the post-change cohort can be compared WITHIN a form rather than only in aggregate

---

## Phase 2: Foundational (blocks every user story)

- [ ] T004 Roll `settlement_form` from the map's seed in `stage_water_frame` (`l7r/diagram/hamletgen/water.py`) and write it to `meta`, keeping the existing `nucleated` bool derived from it so the two cannot disagree
- [ ] T005 Add `settlement_form_asked` and `settlement_form_substituted` to `meta` per [data-model.md](data-model.md), with the fallback rule: a form that cannot be built is replaced by one that can, and the substitution is RECORDED rather than silent
- [ ] T006 [P] Add the `provenance` field (`exogenous` / `endogenous`) to lane records in `l7r/diagram/settlement/water_ways.py`, satisfying FR-004 - an explicit decision, not inferred from the absence of `connector`/`web`
- [ ] T007 [P] Add the form roll and its weights to `l7r/diagram/hamletgen/consts.py` with a record-the-why comment: linear is the weakest-attested of the three ([research.md](research.md) R3) and its weight must reflect that, but no form may be so rare it goes untested by the cohort

---

## Phase 3: User Story 1 - Lanes that follow the houses (P1)

**Goal**: internal lanes are positioned from final house positions; no house position depends on an
internal lane.

**Independent test**: roll the 48-seed cohort; no seed's cluster long axis exceeds its baseline.

- [ ] T008 [US1] Rename `stage_ways` to `stage_track` in `l7r/diagram/hamletgen/ways.py`, keeping `seat_cluster` (which sets `plan.seat`, the real dependency per R1), the watercourse list, the connector and the field spur; remove the internal skeleton from it
- [ ] T009 [US1] Re-origin the connector from the seat band's downslope edge instead of the skeleton's gateway in `l7r/diagram/hamletgen/ways.py` - the ONE place this reorder forces a genuine behavior change rather than a move (R6), so leave a comment saying so at the point of change
- [ ] T010 [US1] Rename `stage_web` to `stage_lanes` in `l7r/diagram/hamletgen/ways.py` and widen it to derive the internal skeleton as well as the web, both from the placed houses via the existing `web_cuts` solver in `l7r/diagram/settlement/_knobs.py`
- [ ] T011 [US1] Update the `STAGES` tuple in `l7r/diagram/hamletgen/driver.py` to the settled sequence (R6), and update the ordering comment there - `STAGES` is the authority for the scripted tier and a change to it is a change to the DRAW ORDER map
- [ ] T012 [US1] Retire `_FRONT_ROW_LANE_CAP` and its `_lane_dist` filter in `l7r/diagram/hamletgen/homesteads.py`, with a record-the-why comment stating it was compensation for lanes-first and MUST NOT be re-tuned - two prior dead ends on that lever are already recorded in that file
- [ ] T013 [US1] Update `tests/hamletgen/test_ways.py` and `tests/hamletgen/test_driver.py` for the renamed stages and the derived skeleton
- [ ] T014 [US1] Measure cluster long axis per seed against `scratchpad/base_forms.json` and confirm no seed grew (SC-001)

---

## Phase 4: User Story 2 - Hamlets that differ in form (P2)

**Goal**: at least three distinct settlement forms across the cohort, each individually correct.

**Independent test**: cohort reports three or more forms, none above 70%; every seed is reproducible.

- [ ] T015 [US2] Make seating form-conditional in `stage_homesteads` (`l7r/diagram/hamletgen/homesteads.py`): front row plus cloud for nucleated, connector frontage for linear, spread along the margin for dispersed
- [ ] T016 [US2] Point `lane_frontage` at the CONNECTOR for the linear form in `l7r/diagram/hamletgen/homesteads.py` - its own docstring already names linear as the archetype whose houses front the road, so this is implementing what the code documents
- [ ] T017 [US2] Make `stage_lanes` a no-op for the dispersed form in `l7r/diagram/hamletgen/ways.py`
- [ ] T018 [US2] Give each dispersed farmstead its own *kainyo* grove in `l7r/diagram/hamletgen/hinterland.py`, using the existing per-house belt branch rather than a new mechanism
- [ ] T019 [US2] Make gate segment 0610 `farmhouses_reach_a_way` form-conditional on `meta["settlement_form"]` in `l7r/diagram/check_village/segments_07c_moats_drains_and_edges.py`, with a comment recording WHY this is a condition and not a waiver (R5)
- [ ] T020 [US2] Make gate segment 0607 `lanes_reach_something` form-conditional in the same file, same reasoning
- [ ] T021 [P] [US2] Add negative fixtures to `pool/regressions/` for the form-conditional checks - one dispersed map that correctly passes with no lanes, one nucleated map that correctly FAILS with a stranded house, per the regression-corpus convention
- [ ] T022 [US2] Report the form distribution and the substitution rate in `l7r/diagram/tools/cohort_audit.py`, so SC-003 is measurable from the tool rather than by hand
- [ ] T023 [US2] Verify determinism (SC-004): roll three seeds twice each and confirm identical manifests
- [ ] T024 [US2] Add tests for the form roll, the fallback substitution, and the form-conditional gate segments

---

## Phase 5: User Story 3 - Density set by the sun (P3)

**Goal**: spacing decided by whether a neighbor's roof shades a drying yard, evaluated by bearing.

**Independent test**: no drying yard shaded at the reference hour; at least one pair closer than the
old uniform pitch.

- [ ] T025 [US3] Implement the directional shadow corridor as a pure function in `l7r/diagram/settlement/_geom/` - full reach through the northern arc, footprint plus working room east and west, interpolated between (R4 has the derivation)
- [ ] T026 [US3] Replace the uniform `BUNDLE_PITCH` pairwise separation test with the directional one in `l7r/diagram/settlement/rolling/fit.py`, keeping `BUNDLE_PITCH` itself as the row-planning constant
- [ ] T027 [US3] Update the `BUNDLE_PITCH` comment block in `l7r/diagram/hamletgen/consts.py` to record that the scalar's separation role has been superseded, why, and that the constant survives for row planning - the comment currently names this exact change as the unimplemented next step, so it must not be left describing the old state
- [ ] T028 [US3] Add a gate check that no threshing yard stands in a neighboring farmhouse's shadow (SC-005), plus its negative fixture in `pool/regressions/`
- [ ] T029 [US3] Add unit tests for the shadow corridor at the cardinal bearings and at the arc edges, at 100% coverage
- [ ] T030 [US3] Demonstrate SC-006: identify at least one cohort map where two farmsteads stand closer than the pre-change uniform pitch, and record it in [research.md](research.md)

---

## Phase 6: Documentation, review and the gate

**None of these may be dropped.** The docs tasks are deliverables the GM asked for by name.

- [ ] T031 [P] Update the `STAGES` table in `dev/placement.md` - rows 4 and 7 change name and meaning - and the phase-model notes beneath it
- [ ] T032 Rewrite the affected `NOTES` prose in `l7r/diagram/tools/placement_stages.py` for the renamed and moved stages, then regenerate `dev/placement-stages/hamlet-placement.html`. **A re-render alone is not sufficient** - the page explains WHY each stage sits where it does, and this feature changes those answers (GM, 2026-08-23)
- [ ] T033 [P] Verify the new `research/homesteads.md` section is reachable from the rules it justifies - each form-conditional check and the shadow corridor should cite it, so a future reader meets the research at the rule
- [ ] T034 [P] Update the hamlet row in `migration-plan.md` if its status changed
- [ ] T035 Regenerate the four live pool hamlets (inashiro, kashikawa, mizuguchi, sawada)
- [ ] T036 Run `settlement-review` on each regenerated map, with **at least one map per form** in the reviewed set (Principle I - the author is not a reviewer of their own visual output)
- [ ] T037 Fix every defect the reviews surface, in this feature, per Principle XIV - including defects outside this feature's delta
- [ ] T038 Run the full cohort and compare against the 44/48 baseline: pass rate must not drop, and every newly-failing check must be individually diagnosed. Compare WITHIN a form where the seed's form is unchanged
- [ ] T039 Record the closing bookend: `make perf LABEL=126-end`, then `make perf-report AGAINST=126-start`, and diagnose IN WRITING every seed more than 5% slower - especially seed 25, which is known to be ~2.5x the baseline
- [ ] T040 `make done` green, backgrounded, not polled
- [ ] T041 Stop-work ritual: commit in the clone, then `scripts/sync-with-main.sh done`

---

## Dependencies

- **Phase 2 blocks everything.** The form knob is read by seating, lane derivation, groves and the gate.
- **US1 (P1) is the MVP** and is independently shippable: derived lanes with the form pinned to nucleated is a complete, correct improvement.
- **US2 depends on US1.** A dispersed hamlet cannot be built while houses are seated by lanes that must exist first.
- **US3 is independent of US2** and can be built on US1 alone.
- **Phase 6 depends on everything**, except T031/T033/T034, which can run alongside Phase 5.

## Parallel opportunities

- T003 alongside T001/T002
- T006 and T007 alongside T004/T005
- T021 alongside T019/T020
- T031, T033, T034 alongside Phase 5

## Implementation strategy

**MVP is US1 alone**: split the ways by provenance, derive the skeleton, retire the cap. That is the
GM's actual question answered, and it is verifiable on its own against SC-001 with the form pinned to
nucleated so nothing else moves.

Then US2 for the visible payoff (three kinds of settlement), then US3 for density.

**Stop and report rather than push** if the cohort pass rate drops below 44/48 and the cause is not
diagnosed - Principle XIII allows exactly three exits, and "documented" is not one of them.
