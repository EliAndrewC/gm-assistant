# Tasks: Capital Housing Layer

**Input**: Design documents from `specs/021-capital-housing/` (plan.md, research.md,
data-model.md, contracts/checks.md, quickstart.md)

**Tests**: INCLUDED - Principle X mandates red-green TDD for every new check and placement
behavior; check tests come BEFORE engine behavior throughout (the invoker's ordering
constraint). All paths below are relative to `.claude/skills/diagram/` unless they start
with `specs/` or `scripts/`.

**Doctrine constraints honored in the ordering**: budget reconciliation before packing;
staged build on the ONE map (`wip/shiro-daika`) with the full sweep exactly once at the end;
perf A/B before the `GEN_TIME_BUDGETS` entry; settlement-review launched the moment the map
is final; XII closing bookend + stop-work ritual last.

## Phase 1: Setup

- [X] T001 Sync the clone (`git pull origin main` in `/gm-assistant/.clones/diagram-city`),
      regenerate the baseline (`DIAGRAM_SKIP_RENDER=1 python3 wip/shiro-daika.gen.py &&
      python3 check_village.py wip/shiro-daika.json`), and confirm the 020 baseline state:
      exactly `imperial_road_town_has_farrier` failing. Record the solo gen time as the perf
      baseline for T024.

## Phase 2: Foundational (blocking all stories)

- [X] T002 Budget reconciliation BEFORE packing: from `wip/shiro-daika.json`'s recorded
      budget block, extract the four band targets (`samurai_yashiki`, `samurai_detached`,
      `samurai_terrace`, `packed`) and compute drawable ground per intended district region
      (interior minus 020 reservations, via a scratchpad script reading the manifest).
      Record the reconciliation (targets vs ground, and any capped target WITH its reason)
      as a comment block in `wip/shiro-daika.gen.py` where the targets are consumed. The
      unmeetable-target grind is the known failure this task exists to prevent.
- [X] T003 Districts vocabulary, test-first: red-green tests in `test_checks.py` for
      `capital_districts_declared` (packs ran, no `districts` records -> fires) and in
      `test_settlement.py` for `s.districts(...)` region records; then implement the record
      in `settlement.py` and the check in `check_village.py`; classify the new `districts`
      key (overlap-EXEMPT region with reason, label-exempt) per the keep-clear contract.
- [X] T004 [P] Rank-gradient rule, test-first: red-green test in `test_checks.py` for
      `capital_rank_gradient` (a yashiki-band compound seated beyond the terrace band's mean
      castle distance on a constructed manifest -> fires; the gradient-ordered manifest ->
      passes); implement in `check_village.py` (classification family, centers, per
      contracts/checks.md).
- [ ] T005 Terrace vocabulary, test-first: red-green tests for `s.terrace` (record shape
      `{x,y,w,h,rot,units,z}`, party-wall seams drawn at ~18 ft frontage per research item
      2) in `test_settlement.py` and `terraces_are_ranges` (units < 2 -> fires) in
      `test_checks.py`; implement glyph + record + check; add `terraces` to
      `_OVERLAP_STRUCTS` + `_LABEL_GROUP` and verify the matrix-extents audit sees it
      (record count == extent count on a test manifest).

## Phase 3: User Story 1 - The GM reads a lived-in capital (P1) - MVP

**Goal**: 12,360 inhabitants housed in rank-graded fabric around every reservation.

**Independent test**: `population_consistent_with_housing` + density + tiling green at
capital scale; gradient visible in crops; zero overlap regressions.

- [ ] T006 [US1] Extend the city housing battery to capital scale, test-first: in
      `test_checks.py`, red cases on a minimal capital manifest (declared population,
      no dwellings -> `population_consistent_with_housing` fires; plus the capital variants
      of density floors / quarter tiling / senior-majority mix per contracts/checks.md
      "extended" list); implement the scale extensions in `check_village.py`. The empty
      02x-state capital manifest becomes the frozen red fixture in `pool/regressions/`.
- [ ] T007 [US1] Yashiki band: seat the walled-compound district regions
      (`s.districts`) nearest the castle/government ward in `wip/shiro-daika.gen.py` and
      pack the yashiki-band compounds (manor-based, in-wall - the inverted rule) to the
      reconciled target; iterate with `check_village.py` + batched crops.
- [ ] T008 [US1] Detached band: pack detached samurai houses (C_SPACED texture) in the
      middle band of `wip/shiro-daika.gen.py`; gradient check green so far.
- [ ] T009 [US1] Terrace band: pack retainer terraces (`s.terrace` ranges) at the band edge
      in `wip/shiro-daika.gen.py`; confirm `terraces_are_ranges` + gradient green.
- [ ] T010 [US1] Commoner machi: pack the machi row fabric (row doctrine at 3 ft/px:
      rows touch, roji as features, businesses front streets, poor housing interior)
      including the TWO burakumin-quarter housing regions (segregation battery green;
      tanning yards themselves deferred to T021 behind the wind gate) in
      `wip/shiro-daika.gen.py`.
- [ ] T011 [US1] Monk houses: seat the ~5 adept-monk households by the two precincts per
      the budget line in `wip/shiro-daika.gen.py`.
- [ ] T012 [US1] US1 gate-on-the-map: full capital check battery green except the known
      remaining (farrier + any not-yet-implemented 021 rules); batched crop review of all
      four bands; freeze any motivating-defect manifest found along the way into
      `pool/regressions/` with its `_regression` block.

## Phase 4: User Story 2 - Water and safety (P2)

**Goal**: every dwelling watered (cistern-wells in the service band), fire watch and kido
mesh over the dense fabric.

**Independent test**: watered-dwellings + fire battery + `cistern_wells_in_service_band` +
`kido_close_the_machi_mouths` green.

- [ ] T013 [US2] Cistern-wells, test-first: red-green tests for
      `cistern_wells_in_service_band` (a `kind:"cistern"` well beyond ~600 street-ft of the
      settling basin -> fires; a band dwelling served by no well -> fires) in
      `test_checks.py`; implement the `wells` `kind` field (absent = legacy, pool
      byte-identity) + the street-path service-band helper in `settlement.py` and the check
      in `check_village.py`, with the 600 ft calibrated-liberty disclosure as a comment at
      the constant (research item 4).
- [ ] T014 [US2] Well pass on the map: place the ~160-240 public wells (cistern kind inside
      the band, dug elsewhere) in `wip/shiro-daika.gen.py` via the engine's own seat
      search; watered-dwellings green.
- [ ] T015 [US2] Fire towers: seat ~10-15 towers over the dense fabric in
      `wip/shiro-daika.gen.py`; fire battery green (existing vocabulary, capital count -
      research item 5).
- [ ] T016 [US2] Kido mesh, test-first: red-green test for `kido_close_the_machi_mouths`
      (a machi street mouth with no kido within tolerance -> fires) in `test_checks.py`;
      implement the mouth-of-machi placement rule in `settlement.py` (ward_style="mesh"
      default per research item 6) and the check; place the mesh in
      `wip/shiro-daika.gen.py`.

## Phase 5: User Story 3 - Temple precincts and neighborhoods (P2)

**Goal**: sovereign precinct interiors inside reserved ground; monzen quarters; lean
backstrip; graveyard claims closed.

**Independent test**: the four US3 checks green; precinct crops match the seven-halls
program.

- [ ] T017 [US3] Precinct interiors, test-first: red-green tests for
      `precinct_interiors_within_reservation` (a dormitory overhanging the reserved rect ->
      fires) and `precinct_graveyard_claims_closed` (`graveyard: true` with no drawn ground
      -> fires) in `test_checks.py`; implement the precinct-interior draw (residence,
      administration, library, dormitories, kitchen - research item 7) in `settlement.py` +
      both checks in `check_village.py`; draw both precincts in `wip/shiro-daika.gen.py`
      and close every 020 graveyard claim (drawn or removed).
- [ ] T018 [US3] Monzen neighborhoods, test-first: red-green test for
      `monzen_fronts_the_approach` (monzen row on the blind side -> fires) in
      `test_checks.py`; implement the check + monzen row placement (open commercial rows
      fronting the approach the torii face, research item 8) for both sovereign temples in
      `wip/shiro-daika.gen.py`; patron-temple frontages where ground allows.
- [ ] T019 [US3] Teramachi backstrip, test-first: red-green test for
      `teramachi_backstrip_lean` (packed rows silting the rim strip -> fires) in
      `test_checks.py`; implement the depth bound in `check_village.py`; confirm the map's
      rim strip complies (adjust packs if not).

## Phase 6: User Story 4 - The wharf hub and the wind (P3)

**Goal**: kashi fabric in chain order; nuisance trades wind-gated.

**Independent test**: chain order readable in crops; wind checks green; three cities'
verdicts unchanged.

- [ ] T020 [US4] Wind knob, test-first: red-green tests for `nuisance_needs_declared_wind`
      (nuisance trade, no `wind_from` -> fires) and `nuisance_trades_downwind` (tanning
      yard upwind of dwellings -> fires) in `test_checks.py`; implement `meta(wind_from=)`
      in `settlement.py` + both checks in `check_village.py` (bearing family, research item
      10); dry-run the three provincial cities and assert NO verdict change (they declare
      no wind - the deliberate scoping recorded in contracts/checks.md).
- [ ] T021 [US4] Nuisance trades on the map: declare `wind_from="northwest"` in
      `wip/shiro-daika.gen.py` and seat the 2 tanning yards in the lee-and-downstream arc
      (S-SW riverward, below the wharf) beside their burakumin quarters; wind + segregation
      batteries green.
- [ ] T022 [US4] Wharf fabric: draw the kashi chain in order in `wip/shiro-daika.gen.py` -
      warehouse/kura rows on the bank top (~20), brokers' row fronting the domain granary
      (merchant, wealth-high), entertainment district beside it (theater stages, an
      `entertainment` district region) - plus the 4-8 walled merchant estates from the
      counts table; batched crop review of the whole waterfront.

## Phase 7: User Story 5 - Green gate and ship (P3)

**Goal**: farrier green, perf budgeted, captions tuned, map shipped and reviewed.

**Independent test**: full gate zero failures in `pool/capitals/`; FULL review pass.

- [ ] T023 [US5] Farrier + relay stables: seat the relay stables (capital class) and
      farrier per the gate doctrine on the Imperial road axis in `wip/shiro-daika.gen.py`;
      `imperial_road_town_has_farrier` green honestly (research item 12).
- [ ] T024 [US5] Perf pass BEFORE the budget entry: solo A/B the gen against HEAD (two
      timed runs, not profile seconds), measure SeatMemo re-visit share per caste pass
      (wire the memo only where re-visits > ~1/3), fix any per-candidate-scan-of-static-
      geometry shape found; then add the `GEN_TIME_BUDGETS` entry (~4x final solo) in
      `test_villages.py`.
- [ ] T025 [US5] Caption-loudness pass: one deliberate pass over every label on the sheet
      (hierarchy: title > castle/Imperial road > institutions > water words > fixtures),
      documented in `wip/shiro-daika.notes.md` (record-the-why); batched crop review.
- [ ] T026 [US5] Ship the map: `git mv` gen to `pool/capitals/shiro-daika.gen.py`,
      regenerate the manifest there, retire the wip draft note ("fails exactly one check")
      in the notes file, then run the FULL sweep exactly once (`make done` backgrounded,
      log tail read) - the one full-suite run of the feature.
- [ ] T027 [US5] FULL settlement-review, launched the moment T026's map is final (before
      docs/commit work, one map per agent): act on every error-class finding, re-gate if
      the map changes, and spot-check the review's claims against the actual render before
      relaying.
- [ ] T028 [US5] Principle XII closing bookend: re-examine the rendered PNG (not the code)
      against research.md items 1-13 one by one - gradient visible, terraces read as
      ranges, cistern band plausible, mesh at the mouths, precincts match the program,
      monzen on the right side, backstrip lean, nuisance arc correct, chain order readable,
      stables at the gate - and record the confirmation (or the fix) in
      `wip/shiro-daika.notes.md` (which moves with the map).

## Phase 8: Polish & Cross-Cutting

- [ ] T029 Documentation (record-the-why, load-bearing): new research sections into
      `research/cities/capitals.md` (service band, fire watch, wind/nuisance, terrace form,
      named-machi decision), doctrine updates into `settlements/capitals.md` (knobs table:
      `ward_style`, `wind_from`, cistern band; the "Open, still to settle" list pruned),
      and the feature log in `wip/shiro-daika.notes.md`; verify every new check name
      appears in contracts/checks.md with its final semantics.
- [ ] T030 Stop-work ritual: commit in the clone, `scripts/sync-with-main.sh done`
      (render-sync carries the new capital render to main), and report to the GM with the
      map path, the crops reviewed, and concrete test steps (regen + gate commands).

## Dependencies

- Phase 2 blocks everything (T002 targets feed every pack; T003-T005 vocabulary feeds all
  stories).
- US1 (T006-T012) blocks US2 (wells need dwellings to water; kido need machi mouths) and
  US4's nuisance siting (downwind needs dwellings). US3 (T017-T019) depends only on Phase 2
  plus the machi vocabulary for monzen rows (after T010).
- US5 is strictly last; within it T024 (perf) before T026 (budget entry ships with the
  sweep), T026 before T027 (review the final map), T027/T028 before T029/T030.

## Parallel opportunities

- T004 alongside T003/T005 (different check families, different test regions).
- T013 (check tests) can be authored while T007-T012 iterate the map (different files).
- T017/T018/T019 test-authoring in one batch (same file, one edit pass) while US2's map
  passes settle.
- The T027 review runs in the background while T029 documentation is written (the standing
  launch-early rule).

## Implementation strategy

MVP = Phase 1-3 (US1): a housed capital is reviewable on its own. Then US2 -> US3 -> US4 in
priority order, each leaving the one map gate-green for its implemented scope; US5 ships.
Commit at each phase boundary (the stop-work ritual runs at natural milestones, not only at
the end); the full sweep runs once, at T026, per the iteration doctrine.
