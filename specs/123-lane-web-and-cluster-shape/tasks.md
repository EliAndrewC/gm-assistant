# Tasks: feature 123 - WORK IN PROGRESS, NOT SHIPPABLE

**Do not run `sync-with-main.sh done` on this state.** The gate is not green (constitution
Principle XIII). Everything below is committed in the clone `.clones/diagram-architecture` and
deliberately unpushed.

**Baseline** (detached worktree at `ae1f94d`): 24-seed cohort **24/24**, pool gate green,
32 of the four pool hamlets' 66 farmhouses beyond 100 ft of any way.

## Done

- [x] T001 Research pass, recorded in `.claude/skills/diagram/research/homesteads.md` (both
      questions) - decisive on access, two-formed on shape.
- [x] T002 The new gate segment `farmhouses_reach_a_way`
      (`check_village/segments_07c_moats_drains_and_edges.py`), registered in
      `tests/fixtures/gate_check_names.json`.
- [x] T003 **Proved it has teeth before fixing anything**: red on all four pool manifests
      (10/8/8/6 houses), and those four manifests are frozen as negative fixtures in
      `pool/regressions/farmhouses_reach_a_way_fires_on_*_before_the_lane_web.json`.
- [x] T004 `web_lanes` in `settlement/_knobs.py` - pure geometry, both forms, coverage proven by
      construction (worst-case distance = extent/m <= 0.9 * pitch).
- [x] T005 The `lane_web` knob: registered in `_knobs.py`, rolled in `plan_site`, recorded as
      `meta.lane_web`.
- [x] T006 `_margin_frame` in `hamletgen/ways.py` - outline coordinates (arc, standoff), restricted
      to the field side the cluster is actually on.
- [x] T007 `longest_clear_run` - the through-lane counterpart of `clip_to_clear`.
- [x] T008 Web lanes excluded from `lane_frontage` (service, not building frontage) and given their
      own narrower corridor `WEB_CLEARANCE`.

## Where it actually stands (measured, not estimated)

Unserved farmhouses (>100 ft from any way), four pool hamlets, 66 houses:

| stage | unserved | note |
|---|---|---|
| baseline | 32 | the defect |
| straight seat-frame lanes | 22 | back lanes clipped to stubs against the curved margin |
| outline coordinates | 26 | laterals started ON the outline and clipped to nothing |
| + inset to buildable ground | 19 | |
| + longest-clear-run + side filter | 15 | |
| + narrow web corridor | see below | |

At `WEB_CLEARANCE = 24`: **Kashikawa fully green**; Sawada, Inashiro and Mizuguchi still fail
`farmhouses_reach_a_way`, and Inashiro additionally `features_do_not_overlap`.

## The open problem, stated precisely

**Adding lanes inside a compact cluster competes with the houses for the same ground**, and the two
constraints pull opposite ways:

- A WIDE web corridor (`LANE_CLEARANCE`, 40 ft) reserves the middle of the cluster, so the placer
  pushes houses outward. Measured: the four long axes went 808 -> 1220, 716 -> 1131, 994 -> 1144 and
  518 -> 1022 ft. **Nothing in the gate measures sprawl**, so this would have shipped silently - it
  was caught only by measuring the cluster's principal axes by hand.
- A NARROW corridor (12 ft) keeps the cluster compact and fixes the reach, but drawn houses then
  collide (`features_do_not_overlap` on three maps).
- 24 ft is the best point found so far and is green on exactly one map.

**This is a calibration dead end, and the next session should not continue tuning the number.** The
likely right answer is structural: the web should be laid where the houses ARE NOT, which means
either (a) a post-placement web threaded through the residual gaps (a new stage between 5 and 6 -
rejected in research.md R6 for determinism reasons that are worth revisiting now that straight
placement has failed), or (b) the placer seating houses in explicit RANKS with the web in the gaps
between them by construction, rather than the two competing for the same free ground.

Both are real designs, not tweaks. Read research.md R2-R6 first - each dead end there is a measured
result, not a guess, and the sequence of them is the argument for (a) or (b).

## Not started

- [ ] T009 Unit tests for `web_lanes`, `_margin_frame`, `longest_clear_run` (100% coverage rule).
- [ ] T010 Check test for `farmhouses_reach_a_way` in `tests/check_village/test_segments_07_*.py`.
- [ ] T011 US3 - honor the rolled `cluster_shape` (GM ruling B). Untouched. `stage_homesteads`
      still seats by rows/frontage and records `meta.cluster_seeding`, i.e. it still declares in
      writing that the rolled knob went unhonored. Worth its own feature.
- [ ] T012 Cohort, `make done`, `settlement-review` per map.
