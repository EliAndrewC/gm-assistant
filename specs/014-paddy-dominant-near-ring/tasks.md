---
description: "Task list for Paddy-Dominant Near-Ring Farmland"
---

# Tasks: Paddy-Dominant Near-Ring Farmland (correct feature 013's composition)

**Input**: Design documents from `specs/014-paddy-dominant-near-ring/`

**Prerequisites**: spec.md, plan.md, research.md, data-model.md, quickstart.md (all present)

**Tests**: INCLUDED - Principle X mandates red-green TDD; FR-009 requires a frozen negative regression fixture.

**Working location**: the session clone `.clones/diagram-town`, inside `.claude/skills/diagram/`. All paths relative to there unless noted.

**Format**: `[ID] [P?] [Story?] Description` - `[P]` = parallelizable (different files, no incomplete-task dependency).

---

## Phase 1: Setup (doctrine correction) - docs-only, no gate

- [ ] T001 In `settlements.md`, **correct** the feature-013 "Near-ring farmland density" text that asserts dry-field-carried densification: the flat near ring of a well-sited town/city is **paddy-dominant** (wet rice the dominant use on the flat waterable ground), dry grain **secondary on the drier/higher margins**, vegetable/market gardens in a **tight band by the settlement**. Keep 013's packed-density and knob doctrine.
- [ ] T002 In `settlements.md`, add the **Historical grounding for the correction** (research.md Part A: site-selection -> paddy, the mis-applied ~1/3 domain average, water+micro-topography as the governing variable) AND the **explicit recorded rejection** of the dry-grain-dominant reading and why (Principle XII), so it is never reinvented.

**Checkpoint**: the corrected "why" exists before any rule references it.

---

## Phase 2: Foundational (shared engine) - BLOCKS all user stories

- [ ] T003 [P] Write the failing dominance-check test + negative fixture (RED): add `test_near_ring_paddy_dominant_*` to `test_checks.py` (fires when dry-grain cells >= paddy cells; passes when paddy dominates; town+city only; scales by tier). Freeze the current (013, dry-grain-dominant) Hirameki manifest as `pool/regressions/near_ring_paddy_dominant_fires_on_dry_dominant_hirameki.json` with `_regression.fires`. Confirm the (not-yet-existing) check would fire on it.
- [ ] T004 Re-locate current anchors (the tree moves under active parallel work): grep `settlement.py` for `def paddy_field`, `_paddy_plots`, `_paddy_surface`, `def near_ring_cropland`, `_blocked`; `check_village.py` for `near_ring_cultivated_fraction`, `fields_show_water_source`, `streams_avoid_fields`, `pond_clear_of_paddies`, `city_outside_fields_have_farmhouses`, `common_fields_vary_orientation`. Record real line numbers (no edit).
- [ ] T005 Factor the basin primitives if cleaner: expose `_paddy_plots` + `_paddy_surface` (from `paddy_field`) so a filler can draw one flooded basin polygon with the true paddy look and record a minimal `kind="paddy"` field.
- [ ] T006 Implement `Settlement.near_ring_paddy(bbox, density=None, *, seed=0, avoid=())` in `settlement.py` (near `near_ring_cropland`): tile flooded paddy basins over the flat near-ring ground, placing a basin ONLY where legitimately watered - abutting an `M["streams"]` segment within ~18px (stream not crossing the basin), OR in the pond's 1.0-1.10x ring, OR running off the map edge - and skipping any cell with no reachable water. Reuse `near_ring_cropland`'s keep-out `_blocked`. Record `kind="paddy"` fields (name/outline/bbox, no channels). Enforce town bbox<80000 (or alternate orientation) and city off-edge-or-farmhouse constraints. Deterministic own RNG.
- [ ] T007 Implement `near_ring_paddy_dominant` in `check_village.py` (GREEN for T003): clone the `near_ring_cultivated_fraction` 25px band + `committed` mask; tally paddy-outline cells vs dry-grain `dry_plots` (`crop != "garden"`) cells; require paddy > dry-grain, scaled per `near_ring_density` tier (dense: clear margin; thin: paddy at least ties). Town+city only; failure detail reports both counts + the fix. Record-the-why comment with the tier ratios pointing at research.md.
- [ ] T008 [P] Unit-test `near_ring_paddy` in `test_settlement.py` (behavior-named, parametrized: stream-abutting basin kept; off-edge basin kept; no-water basin dropped; stream-crossing basin dropped; pond-core basin dropped; keep-outs respected; tiers monotonic) to 100% line coverage on the new paths.

**Checkpoint**: `pytest` + 100% cov green; the dominance check fires on the frozen dry-dominant fixture and passes on a synthetic paddy-dominant manifest; no map recomposed yet.

---

## Phase 3: User Story 1 - A well-sited TOWN reads paddy-dominant (Priority: P1) 🎯 MVP

**Goal**: Hirameki's flat near ring reads as rice paddy (dominant), grain on the margins, gardens by the town; full gate green.

**Independent Test**: regenerate Hirameki; by eye the near ring reads paddy-dominant; `near_ring_paddy_dominant` + `near_ring_cultivated_fraction` (still packed) + `fields_show_water_source` (no waterless paddy) + every existing check pass.

- [ ] T009 [US1] Recompose `pool/towns/hirameki.gen.py`: call `s.near_ring_paddy(<flat-floor bbox>)` (basins along the W/E streams and off-edge), demote `near_ring_cropland` to a margin-grain pass (drier/higher bbox, low garden_frac, paddy region in `avoid`) + a near-town garden band (tight bbox, garden_frac≈0.85). Enlarge the `build_comb` fans if the floor needs more watered paddy.
- [ ] T010 [US1] Iterate single-map regen + gate until paddy-dominant AND green: `near_ring_paddy_dominant`, `near_ring_cultivated_fraction`, `fields_show_water_source`, `streams_avoid_fields`, `pond_clear_of_paddies`, `common_fields_vary_orientation`, all overlap/water checks. Fix via water-reachable basin placement + margin geometry, never by faking water.
- [ ] T011 [US1] Confirm population/caste bands unaffected (paddy basins + dry fill house no one) - verify `town_caste_count`/`households_consistent`/`town_farmers_plurality` still pass.
- [ ] T012 [US1] Principle XII spot-review of `pool/towns/hirameki.png`: paddy dominates the flat near ring, grain on the drier/higher margins, gardens by the town, no paddy without visible water. Record the outcome.

**Checkpoint**: MVP - a well-sited town reads paddy-dominant and passes every check.

---

## Phase 4: User Story 2 - Well-sited CITIES read paddy-dominant (Priority: P2)

**Goal**: Tango + Nagahara extramural near rings read paddy-dominant outside the wall; walls/moat/bridges/estates unchanged.

**Independent Test**: regenerate Tango + Nagahara; extramural ring paddy-dominant; every added paddy watered (stream/river abut or off-edge or farmhouse-ringed); nothing crosses wall/moat; city gate green.

- [ ] T013 [US2] Recompose `pool/provincial-cities/tango.gen.py`: extramural `near_ring_paddy` (basins tapping the streams/river, or off-edge, or farmhouse-ringed for `city_outside_fields_have_farmhouses`); demote `near_ring_cropland` to margin grain + near-wall garden band; enlarge the extramural combs if needed. Respect moat/wall/gates/estates.
- [ ] T014 [US2] Recompose `pool/provincial-cities/nagahara.gen.py` likewise (it has a river in the near ring - lean on river-abutting basins).
- [ ] T015 [US2] Iterate regen + gate on each until paddy-dominant AND green, including `city_outside_fields_have_farmhouses`, `city_moat_irrigates_fields`, `roads_bridge_water`, wall/moat overlaps.
- [ ] T016 [US2] Principle XII spot-review of both city PNGs: extramural paddy dominates, grain on margins, gardens by the wall, nothing crosses wall/moat. Record the outcome.

**Checkpoint**: both cities read paddy-dominant and pass independently.

---

## Phase 5: User Story 3 - Tunability preserved, thin map paddy-led (Priority: P3)

**Goal**: Hoshizora (thin) still reads visibly thinner than the dense maps, but its modest cultivation is paddy-led, not dry-grain-led.

**Independent Test**: regenerate Hoshizora; near ring visibly thinner than dense maps; what cultivation it has is paddy-led (paddy at least ties dry-grain); passes at the thin tier.

- [ ] T017 [US3] Recompose `pool/towns/hoshizora.gen.py` at the thin tier: `near_ring_paddy` where its stream/pond reach (the drainage tameike, the NE/SW stream); demote the dry fill; keep the hayfield/pasture grazing character. Confirm the thin-tier dominance ratio (paddy at least ties) passes.
- [ ] T018 [US3] Iterate regen + gate; confirm Hoshizora stays visibly thinner than the dense maps and the dense maps still pass - the knob works and a thin map is paddy-led, never dry-dominant.
- [ ] T019 [US3] Principle XII spot-review of `pool/towns/hoshizora.png`: visibly thinner than dense, paddy-led not dry-grain-led. Record the outcome.

**Checkpoint**: all three stories independently functional; the knob preserved and paddy-led at every tier.

---

## Phase 6: Polish & Cross-Cutting (MANDATORY for a shared-engine change)

- [ ] T020 Full-pool sweep (MANDATORY): `make done` (regen every map + ruff + format + mypy --strict + pytest + 100% cov + full gate). Background it; report done only when green.
- [ ] T021 Verify scope isolation (SC-006): village + hamlet tracked `.json` manifests unchanged; fix any downstream disturbance.
- [ ] T022 Principle XII CLOSING gate (full pass): review all four PNGs against research.md Part A - paddy dominates the flat near ring, grain on margins, gardens by town, no waterless paddy, thin map paddy-led. Fix the MAP if any picture still reads dry-grain-heavy; never relax the check. Record each outcome.
- [ ] T023 Confirm SC-007: the corrected "why" + the recorded rejection are present in `settlements.md` and by the check; grep to verify. Confirm 013's research.md is left as historical record.
- [ ] T024 Stop-work ritual: commit; `bash scripts/sync-with-main.sh done` (locked push + render-sync). Fix-forward on any auto-merge with the concurrent session; never force-push.

---

## Dependencies & Execution Order

- **Phase 1 (doctrine)**: docs-only; anytime, ideally first.
- **Phase 2 (Foundational)**: T003 (RED) + T004 (recon) first; T005 before T006; T006/T007 land GREEN; T008 restores coverage. **Blocks all user stories.**
- **Phase 3 (US1/MVP)**: after Phase 2. T009 -> T010 -> T011 -> T012.
- **Phase 4 (US2)**: after Phase 2 (independent of US1; sequenced after for MVP-first). T013/T014 -> T015 -> T016.
- **Phase 5 (US3)**: after Phase 2 (independent). T017 -> T018 -> T019.
- **Phase 6 (Polish)**: after all stories. T020 -> T021 -> T022 -> T023 -> T024.

### Parallel opportunities
- T003 [P] and T004 run in parallel (test/fixture vs read-only recon).
- T008 [P] alongside T006/T007 once signatures fixed.
- The three stories are independent post-Phase-2; recommended path is sequential MVP-first (single-map loop is cheap).

---

## Implementation Strategy

**MVP = Phase 1 + Phase 2 + Phase 3 (US1)** - a well-sited town reading paddy-dominant, gated and XII-reviewed. Stop and validate there before US2/US3.

**Iteration discipline** (quickstart.md + the diagram dev-loop doc): iterate the red/green loop on the ONE motivating map (single-map regen + gate ~1-7s); reserve the full-pool `make done` for Phase 6, mandatory because shared engine changed. The XII closing gate reviews the PNG, not the code - the 013 maps passed every check while depicting the wrong crop, which is the exact failure this feature exists to correct.

---

## Notes
- `[P]` = different files, no incomplete-task dependency.
- Tests precede implementation (T003 before T007); verify RED before GREEN.
- The honest limit (research.md Part B): the filler makes paddy dominant on the *waterable* flat ground; where a map genuinely lacks near-ring water, the answer is a lower tier, never fake paddy. The check enforces dominance, not a paddy quantity.
- No `contracts/` dir: internal contracts live in data-model.md.
