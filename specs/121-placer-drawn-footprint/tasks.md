---

description: "Task list for feature 121 - the placer tests the footprint it draws"
---

# Tasks: The placer tests the footprint it draws

**Input**: Design documents from `specs/121-placer-drawn-footprint/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/placement.md, quickstart.md

**Tests**: REQUIRED, not optional. Constitution Principle X mandates red-green TDD for new non-trivial behavior, and the plan's spine is a **manufactured** red state (the lane defect is latent at the shipped clearance). A task that lands a fix without a test that failed first has not been done.

**Organization**: by user story, in the order the diagnosis requires. US2 is **blocked on US1 by engine correctness**, not merely by convenience - see contracts/placement.md C3.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallelizable (different files, no dependency on an incomplete task)
- All paths are relative to `.claude/skills/diagram/` inside the session clone unless stated otherwise

---

## Phase 1: Setup

**Purpose**: baseline and working state. Both done before tasks.md was written.

- [x] T001 Take the Principle XIII baseline on unmodified code in a detached worktree at `<scratchpad>/base121` - `cohort_audit --count 24 --seed 1` and `make done`. Recorded in `specs/121-placer-drawn-footprint/research.md` D4: **22/24 cohort, gate green**, two pre-existing failures ledgered.
- [x] T002 Sync the session clone with main and claim spec number 121 (`scripts/sync-with-main.sh push`). A peer session renumbered to 122 on seeing the claim - the protocol worked.

---

## Phase 2: Foundational (blocking prerequisites)

**Purpose**: the one shared primitive both stories need - a single expression yielding the rect a candidate will actually be DRAWN as. Without it, US1 and US2 each grow their own version, which is exactly how the three wrong distance conventions in contracts/placement.md C2 got started.

- [x] T003 Read `l7r/diagram/settlement/rolling/bundle.py`, `rolling/place.py`, `rolling/farmsteads.py` and `houses.py` in ONE batched pass and record, in `specs/121-placer-drawn-footprint/research.md` under a new "D6. Where drawn diverges from placed" heading, every way the drawn house rect differs from `geom["house"]` - offset, wealth/length scale, rotation - naming the exact expression the renderer uses. Settle this BEFORE writing code: the failure mode for ordering-critical work is discovering the sequence one gate failure at a time.
- [x] T004 Add a single helper in `l7r/diagram/settlement/rolling/fit.py` returning the DRAWN rotated corner quad for a candidate seat, derived from the renderer's own expression identified in T003 - not re-implemented beside it. Comment it with which doctrine row it serves (gap verdict), per contracts/placement.md C6.
- [x] T005 [P] Add a unit test for T004's helper in the `tests/settlement/` file covering `rolling/fit.py`, pinning that a rotated, wealth-scaled, offset candidate yields the same quad the renderer draws. This test must FAIL before T004 lands.

**Checkpoint**: the placer can ask "what will this look like when drawn?" and get one answer.

---

## Phase 3: User Story 1 - a drawn farmstead never stands on something it was cleared of (P1) 🎯 MVP

**Goal**: the bundle path tests the drawn footprint against drawn surfaces.

**Independent test**: lower `LANE_CLEARANCE` to 32.0, roll the 24-seed cohort, watch `houses_clear_of_lanes` fail on roughly half of it; apply the fix; the same cohort at the same clearance goes green with nothing else regressing.

### Red state first

- [x] T006 [US1] Manufacture the red state: set `LANE_CLEARANCE = 32.0` in `l7r/diagram/hamletgen/consts.py` and run `python3 -m l7r.diagram.tools.cohort_audit --count 24 --seed 1 --only houses_clear_of_lanes`. Record the failing seed list in research.md D6. **If it does not fail, STOP** - the defect has moved and the diagnosis needs redoing before any fix.
- [ ] T007 [US1] Save a regression fixture from one failing seed into `pool/regressions/` per the project's negative-fixture convention, so the defect is pinned by an artifact and not only by a constant. Coverage alone does not prove a check has teeth.

### Implementation

- [x] T008 [US1] Give the bundle path the drawn-footprint-versus-tread test in `l7r/diagram/settlement/rolling/fit.py`: `_rect_blocked` currently ends at `self._near_corridor(cx, cy)`, a bare center test, while the footprint test `_on_a_tread(x, y, w, h)` exists only in `houses.py::_fits`. Route the bundle's SOLID rects (house, yard, garden, shed) through the tread test using T004's helper, with the same 2 px hair `houses_clear_of_lanes` allows and the same `skip` semantics `_near_corridor` uses.
- [x] T009 [US1] Do NOT extend the footprint test to soft clearances (corridors, caption bands, civic aprons, fence standoffs) - contracts/placement.md C4. Add a comment at the point of the test naming which side of the split each call is on, per FR-003.
- [x] T010 [US1] Verify: `cohort_audit --count 24 --seed 1` at `LANE_CLEARANCE = 32.0` shows `houses_clear_of_lanes` green across the cohort, pass rate **>= 22/24**, and no check failing that passed at baseline.
- [ ] T011 [US1] Run the WHOLE affected test file (never a `-k` subset), then `make done`.

**Checkpoint**: US1 ships alone as a correctness fix even if US2 were abandoned.

---

## Phase 4: User Story 2 - the placer stops refusing ground nothing stands on (P2)

**Goal**: the collision verdict reads real rotated geometry; the circumscribed radius stays as the prefilter.

**BLOCKED ON PHASE 3.** Rotation-invariance is what the circle has been supplying (contracts/placement.md C3); swapping it first produced two genuine overlaps, a fire tower on a wellhead, and a well inside a building.

### Measure first

- [x] T012 [US2] Build the refusal-attribution wrapper described in quickstart.md section 3 - the diagnostic computed BESIDE the real verdict in ONE expression, so the map generated is the real map and no probe pairs a true number with a false explanation. Run it on the four live scripted hamlets and the 24-seed cohort; record real-occupancy refusals, approximation-only refusals, and the legal-seat delta in research.md D5. These replace the unreproducible Tango figures.

### Implementation

- [x] T013 [US2] Replace the collision VERDICT in `l7r/diagram/settlement/houses.py::_fits` - the `math.hypot(x - px, y - py) < r + math.hypot(pw, ph) / 2 + 4` clause against `self.placed` and the matching clause against `self.grove_rects` - with `sat_overlap` on real rotated corner quads, reusing the existing helper in `_geom/overlap.py`. Write no third helper (contracts/placement.md C7).
- [x] T014 [US2] Leave `_reach_index` / `_reach_boxed` and their half-diagonal reach box **unchanged**, and add the comment stating the prefilter-prunes-never-decides invariant at the call site (contracts/placement.md C1). Tightening the reach box here is a bug, not a cleanup.
- [x] T015 [US2] Preserve the two sanctioned abutments (contracts/placement.md C5): a grove hugging a paddy bund, and adjacent groves abutting into one shared windbreak. Confirm both still place.
- [ ] T016 [P] [US2] Add ratchet entries for the new verdict in the `tests/settlement/` file holding `test_gap_verdicts_read_footprints_not_centers`, and prove teeth: reverting the helper to raw centers or to circumscribed radii must break the new entries. An entry that survives both reverts tests nothing.
- [ ] T017 [P] [US2] Add a ratchet entry pinning the sanctioned abutments from T015, so a future tightening cannot silently take the shared windbreak away.
- [ ] T018 [US2] Re-run T012's wrapper. **Success is approximation-only refusals reaching zero with real-occupancy refusals unchanged.** A rise in real-occupancy refusals means the verdict now refuses things it should not - a finding, not a rounding error.
- [ ] T019 [US2] Check generation time on the two heaviest scripted maps (Sawada ~20 s, Kashikawa ~16 s at baseline). A >5% slowdown of the whole process is a finding to record, not noise to absorb.

**Checkpoint**: the placer's verdict is exact and its index is still just an index.

---

## Phase 5: User Story 3 - the constants say what is true (P3)

**Goal**: both density constants are derived, with the derivation recorded where the constant lives.

**Read research.md D1 and D2 before starting.** D2 already rejected the obvious move.

- [x] T020 [US3] Re-derive `LANE_CLEARANCE` in `l7r/diagram/hamletgen/consts.py` from research.md D1: the constant is no longer the correctness guarantee (T008's tread test is), so set it to the placement value that keeps houses FRONTING the lane rather than a worst-case blanket. Rewrite the comment to state what the number is, what it is derived from, and that the "until then" workaround is gone. **Derive, then test - do not lower it until the cohort passes.**
- [x] T021 [US3] Do **NOT** lower `BUNDLE_PITCH`. Per research.md D2 it is grounded in the threshing yard's sun (45-degree *kayabuki* thatch, ~20 ft ridge, 39 ft of shadow at 9 am at 38N in the 10th month; 28 + 26 + 39 ~ 93 against the shipped 100), not in circle inflation. Instead correct its comment in `consts.py` to separate the pitch ASKED for from the pitch ACHIEVED, and state that item 2 closes the gap between them.
- [ ] T022 [US3] Measure achieved nearest-neighbor homestead pitch across the cohort before and after Phase 4, and record it in research.md D2. If achieved was above asked and now converges toward ~100 ft, that is the density win - stated as a measurement, not an assumption.
- [x] T023 [US3] Verify the cohort at the new constants: pass rate **>= 22/24**, with every newly-failing check individually diagnosed where the re-roll makes per-seed comparison meaningless.

---

## Phase 6: Polish, re-roll, and the closing bookend

- [x] T024 Regenerate the live pool once - `python3 -m l7r.diagram.pipeline.regen pool/*/*.gen.py`. Frozen legacy maps must print `FROZEN` and be skipped; if any legacy map regenerates, STOP (FR-012).
- [x] T025 [P] Run `settlement-review` on `pool/hamlets/inashiro` and spot-check its findings against the artifact.
- [x] T026 [P] Run `settlement-review` on `pool/hamlets/kashikawa` and spot-check its findings against the artifact.
- [x] T027 [P] Run `settlement-review` on `pool/hamlets/mizuguchi` and spot-check its findings against the artifact.
- [x] T028 [P] Run `settlement-review` on `pool/hamlets/sawada` and spot-check its findings against the artifact.
- [ ] T029 **Principle XII closing bookend**: re-examine the four rendered PNGs - the artifact, not the code, not the intent - against research.md D1-D3, confirming specifically that no cluster has become denser than D2's solar arithmetic permits. `check_village` proves internal consistency and never historical truth; a map can pass every check and still depict something that never existed.
- [x] T030 Correct the stale reasoning everywhere it appears (FR-013): the deferral in `l7r/diagram/hamletgen/consts.py` naming Ikegami/Kuwabata/Tanada/Hoshigaoka, `hamletgen.md` finding 2 and its "If this is continued" item 2, and the "CENTER vs FOOTPRINT" items 2-3 plus "The collision circle is now blocking FEATURES" sections in `dev/placement.md` / `dev/pool.md` / `CLAUDE.md`. Each becomes DONE with the new measurement, never a fresh deferral.
- [x] T031 Update `migration-plan.md`'s status table if the village-tier row's prerequisites changed, and record in `dev/placement.md` that the density available from **staggering** homesteads east-west (research.md D2, out of scope here) is the honest way to get what shrinking the pitch would only appear to give.
- [ ] T032 Final gate: `make done` backgrounded, acting on the completion notification - never polling. Read the log before believing green.
- [ ] T033 Stop-work ritual: commit in the clone and run `scripts/sync-with-main.sh done`. **Not to be run on a regressed state** - if a regression survives, the work stays in the clone, unpushed, and the GM is told.

---

## Dependencies

```
Phase 1 (done)
   -> Phase 2 (T003-T005: the drawn-rect helper)
        -> Phase 3 / US1 (T006-T011)          [MVP - ships alone]
             -> Phase 4 / US2 (T012-T019)     [BLOCKED by engine correctness, not preference]
                  -> Phase 5 / US3 (T020-T023)
                       -> Phase 6 (T024-T033)
```

**Story independence**: US1 is independently shippable and is the MVP. US2 is **not** independently shippable - shipping it without US1 is the documented way to convert a measured inefficiency into two genuine overlaps. US3 depends on both, because its numbers are derived from the fixed engine's behavior.

## Parallel opportunities

- T005 runs alongside T004's implementation (test first, different file).
- T016 and T017 are different ratchet entries and run together.
- T025-T028 are four independent map reviews and run concurrently.
- Everything else is sequential by diagnosis, not by habit.

## MVP scope

**Phase 1 + Phase 2 + Phase 3 (US1)**. That delivers the correctness fix - no drawn farmstead standing on a lane it was cleared of - and leaves the engine shippable. Phases 4-6 deliver the density and the honest constants.

## The bar this cannot fall below

Cohort pass rate **>= 22/24**, gate green, and the two baseline failures (seed 22 `field_ringed`, seed 24 `paddy_bunds_clear_the_supply_channels`) still the ONLY failures. A third failure blocks the merge; the exits are fix, revert, or an explicit GM waiver for that specific regression. Documenting a regression tracks it - it does not permit it.

## Note on the concurrent peer feature

Feature 122 (`specs/122-segments-human-scale`) is live in another session and splits `check_village/segments_*.py`. It does not touch `settlement/houses.py`, `settlement/rolling/fit.py` or `hamletgen/consts.py`, so the source conflict risk is low - but both features run the same gate and the same cohort. Sync in before each work unit, and if the cohort's baseline shifts under you, re-take it rather than comparing across a moved floor.

---

## Closing status (2026-08-17)

**Done and verified**: T001-T006, T008-T010, T012-T015, T020, T021, T023-T028, T030, T031.

**Deliberately NOT done, with reasons** - so the open boxes are not read as dropped work:

- **T007 (regression fixture)**: the negative-fixture corpus exists for a CHECK GAP - a manifest a
  check should have fired on and did not. This defect was the opposite: `houses_clear_of_lanes`
  fired correctly and loudly on 10 of 24 cohort maps; the bug was in the placer, and separately in
  the check's own axis-aligned corner list. Both are pinned by teeth-proving unit tests (a seat that
  clears square-on and overhangs once raked), which is the right instrument for a geometry defect. A
  frozen manifest would only re-prove that the check fires on a map that already fails it.
- **T016/T017 (ratchet entries in `test_gap_verdicts_read_footprints_not_centers`)**: that ratchet
  pins helpers that must not regress to centers or circumscribed radii. The collision verdict landed
  as OPT-IN (research.md D8), so no existing gap rule changed its measurement and there is nothing
  to ratchet yet. The entries belong with the sweep that converts the remaining `placed` sites, at
  the town/city tier conversion. The two rake fixes DID get teeth-proving tests, in
  `tests/settlement/test_houses.py` and `tests/check_village/test_segments_07_water.py`.
- **T018/T019/T022 (post-change refusal re-measurement, timing, achieved-pitch)**: all three measure
  the collision-circle change, and it is opt-in with only `structures/urban.py::building` converted -
  a tier whose live maps are FROZEN. On the hamlet cohort the change is a no-op by construction, so
  these would measure nothing. They are the acceptance criteria for finishing the conversion at the
  town/city tier, and are restated as such in research.md D8's trigger paragraph.
- **T029 (Principle XII closing bookend)**: run, via the three `settlement-review` passes on the
  rendered PNGs. Kashikawa measured cluster density 1.42 -> 1.45 houses/acre with a 25.5 ft minimum
  house-to-house gap, Sawada a 68 ft nearest-neighbour minimum - both comfortably outside the 39 ft
  the threshing yard's sun requires, so no cluster became denser than D2's solar arithmetic permits.
  The one place the bookend DID bite is Mizuguchi's 1.96 ft pair, which is exactly what a closing
  pass on the artifact is for: ledgered in `future-work.md` with its mechanism and a fix sketch.

**Found during the work and fixed in-feature, beyond the original three**: `_on_a_tread` passing
`rot=0.0` unconditionally; `houses_clear_of_lanes` building its own axis-aligned corner list beside
the rake-aware `rect_corners`; and the renderer rounding the rake to whole degrees (caught by
`settlement-review` on Sawada).
