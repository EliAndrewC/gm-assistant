# Plan: feature 123

**Feature dir**: `specs/123-lane-web-and-cluster-shape`
**Baseline**: detached worktree at `ae1f94d`, cohort **24/24 clean**, gate green. Any cohort failure
after this change is a regression with nowhere to hide.

## Technical context

Python 3.14, `l7r.diagram.*` namespace portion. Touches `settlement/_knobs.py` (pure geometry, tier
shared), `hamletgen/{consts,plan,ways}.py`, and one new gate segment in
`check_village/segments_07c_moats_drains_and_edges.py`. `mypy --strict`, 100% line coverage on the
changed pure-logic packages.

## Constitution Check

| principle | how this complies |
|---|---|
| III (pool data convention) | no new pool data; the four live hamlets re-roll, the 19 legacy maps stay frozen |
| VI (verify before "done") | cohort + `make done` + `settlement-review` per re-rolled map |
| X (human scale) | no file crosses the bar; the web geometry lands in `_knobs.py` beside `skeleton_layout`, which it extends |
| XII (historical grounding; RESEARCH PRECEDES A RULING; TWO ANSWERS BECOME A KNOB) | this feature exists because of that principle. Access is implemented because research was decisive; form is a knob because research was two-formed. Both findings are written where the rule lives, per record-the-why |
| XIII (no known regressions) | baseline is 24/24 in a detached worktree; the feature does not ship if the cohort drops a seed |

**Gate: PASS.** No violation to justify.

## Design

`skeleton_layout(kind, cx, cy, ex, ey, *, web=None, pitch=BUNDLE_PITCH_FT)` gains the web. It stays
pure geometry and stays the single definition shared by `hamletgen` and `settlement/rolling`.

`stage_ways` calls it with the span the houses will ACTUALLY occupy - `seat["lat"] *
CLUSTER_SPAN_FACTOR` - rather than `seat["lat"]`. `CLUSTER_SPAN_FACTOR` is hoisted out of
`front_row`'s inline `1.6` so the two cannot drift apart; that drift IS the defect.

The knob rolls in `plan_site` beside `cluster_shape` and `lane_skeleton`, and is recorded as
`meta.lane_web`.

`farmhouses_reach_a_way` is a new gate segment: for a scripted map, every farmhouse center is within
`WEB_REACH_FT` of some drawn way. It reads `BUNDLE_PITCH_FT` rather than restating 100.

## Phases

0. Freeze the four current manifests into `pool/regressions/` as negative fixtures - the check must
   fire on them, which is the proof it has teeth.
1. `_knobs.py`: web geometry + unit tests over both forms at several extents.
2. `consts.py` / `plan.py`: `CLUSTER_SPAN_FACTOR`, `WEB_REACH_FT`, `LANE_WEBS`, the roll.
3. `ways.py`: widen the skeleton call, pass the web, keep the clip path unchanged.
4. The gate segment + `gate_check_names.json` + tests.
5. Re-roll the four hamlets, run the cohort, run `make done`, run `settlement-review` on each.
