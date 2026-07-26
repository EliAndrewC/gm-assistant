# Tasks: Punishment Spots and Execution Grounds

**Input**: Design documents from `specs/015-punishment-execution-grounds/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/engine-api.md](contracts/engine-api.md)

**Tests**: REQUIRED for this feature. Constitution Principle X (NON-NEGOTIABLE) mandates red-green TDD and 100% coverage, and FR-019/FR-020 require an automated check plus a negative regression fixture for every siting rule. Test tasks are therefore not optional here.

**Working directory**: all paths are relative to `.claude/skills/diagram/` unless stated otherwise. All work happens in the session clone `.clones/diagram-town`, never in main's tree.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallelizable (different files, no dependency on an incomplete task)
- **[Story]**: US1 / US2 / US3 from spec.md

---

## Phase 1: Setup

**Purpose**: nothing to install - the feature is additive within an existing package. This phase only confirms the workspace is sound before engine edits begin.

- [x] T001 Confirm the container is healthy with `container-scripts/setup-dev-env.sh --check` (~3s, no network) - a rebuilt container silently loses `resvg` and the diagram tests then fail for unrelated-looking reasons
- [x] T002 Confirm the clone is synced and on a green base

**Checkpoint**: workspace verified.

---

## Phase 2: Foundational (blocking prerequisites)

**Purpose**: the manifest registries and the overlap plumbing that BOTH map features depend on. No user story can start until these exist.

- [x] T003 Add the three empty registries `punishment_spots`, `execution_grounds`, `boundary_markers` to the manifest dict in `Settlement.__init__` in `settlement.py`, beside `cremation_grounds` / `ossuaries` / `kosatsuba`
- [x] T004 Register the three new kinds in the structure-overlap kind list in `check_village.py` (the list containing `"kosatsuba"`, ~line 179) so they inherit the existing clearance rules against wells, troughs, hitching rails, torii, walls, and each other
- [x] T005 [P] Extend the fixture builders at the top of `test_checks.py` so a manifest can carry the three new record kinds, and confirm `test_fixture_builders_survive_every_check` still passes - per the dev-loop doc this is what stops a missing key from ambushing later check tests

**Checkpoint**: registries exist and are overlap-aware; user stories can proceed.

---

## Phase 3: User Story 1 - The execution ground reads correctly from the road (Priority: P1) - MVP

**Goal**: a bare, unbunded ground outside the settlement, on the road past the boundary stone, clear of farmland and clear of the community's dead.

**Independent test**: add an execution ground to `pool/towns/hoshizora.gen.py`, regenerate, and confirm from the manifest that it sits outside the built edge, off all field polygons, beyond the boundary marker, and 150+ ft from the funerary cluster.

### Tests first (red)

- [x] T006 [P] [US1] Write failing unit tests in `test_settlement.py` for `boundary_marker()`: records to `M["boundary_markers"]`, records TRUE `w`/`h` (~3 ft) separately from the drawn `vw`/`vh` marker box, and the drawn box never shrinks below the legibility floor at coarse grain
- [x] T007 [P] [US1] Write failing unit tests in `test_settlement.py` for `execution_ground()`: records to `M["execution_grounds"]`, footprint matches the tier band (~60x60 ft town, ~100x60 ft city), `screened` defaults False at town and True above it, and the ground reserves ground in BOTH `placed` and `block_polys`
- [x] T008 [P] [US1] Write failing check tests in `test_checks.py` for `execution_ground_outside_the_settlement`, `execution_ground_by_the_road`, and `execution_ground_past_the_boundary_marker`, each with a passing and a failing manifest built from the fixture builders
- [x] T009 [P] [US1] Write failing check tests in `test_checks.py` for `execution_ground_clear_of_the_dead`, `execution_ground_off_the_farmland`, `execution_ground_beyond_the_burakumin_quarter` (including the skip-when-no-quarter case), and `execution_ground_only_at_a_seat_of_justice`
- [x] T010 [P] [US1] Write a failing check test in `test_checks.py` for the presence floor `{scale}_has_execution_ground`, including the `meta(execution_ground=False)` opt-out path

### Implementation (green)

- [x] T011 [US1] Implement `boundary_marker()` in `settlement.py` as a location marker (dosojin stone pair glyph; true footprint in `w`/`h`, drawn box in `vw`/`vh`), following the wells and kosatsuba doctrine
- [x] T012 [US1] Implement `execution_ground()` in `settlement.py`: bare ground fill visually distinct from field and built ground; crucifixion post sockets, burning stake, sand beheading bed, head-display stand with crime board oriented to the road, well, disposal pit; three-sided screen fence above town tier; tier-sized footprint; records the manifest entry and reserves ground
- [x] T013 [US1] Make the county-tier ground read DISUSED (weathered treatment, socket stones rather than standing posts) per the volume finding in research.md - one execution per county per 5-10 years - and put a `# WHY:` pointer beside it
- [x] T014 [US1] Implement the seven US1 checks in `check_village.py` beside the existing funerary checks, each carrying a `# WHY:` pointer to the settlements.md grounding entry
- [x] T015 [US1] Put the 150 ft separation constant behind a named constant with a comment stating plainly that the true historical separation was far larger and the number is a map-legibility floor - the disclosure Principle XII's calibrated-liberty clause requires

### Regression fixtures (prove the checks have teeth)

- [x] T016 [US1] Save one negative fixture per US1 check to `pool/regressions/` using `make_regressions.py`, named `<check_name>_fires_on_<case>.json` - coverage alone does not prove a check has teeth

### First map

- [x] T017 [US1] Add a boundary marker and execution ground to `pool/towns/hoshizora.gen.py` (the unwalled county seat - the harder siting case, since "outside" must be measured from dwellings rather than a wall), using `s.open_seat(...)` rather than hand-picked coordinates if the ground is tight
- [x] T018 [US1] Regenerate and gate that ONE map, then confirm each new check actually RAN on it: `python3 check_village.py pool/towns/hoshizora.json | grep -c <check_name>` returns non-zero for each

**Checkpoint**: US1 is independently deliverable - one town map carries a correctly-sited execution ground.

---

## Phase 4: User Story 2 - The punishment spot sits in the middle of town (Priority: P2)

**Goal**: the everyday face of the magistrate's authority, in the built core, on the traffic.

**Independent test**: add a punishment spot to one town spec, regenerate, and confirm from the manifest that it sits in the core, within ~60 ft of a street, and overlaps nothing.

### Tests first (red)

- [x] T019 [P] [US2] Write failing unit tests in `test_settlement.py` for `punishment_spot()`: records to `M["punishment_spots"]`, ~30x12 ft true footprint at every tier, reserves ground, and draws NO notice board (the crime text rides on the cangue - the kosatsuba is a separate institution)
- [x] T020 [P] [US2] Write failing check tests in `test_checks.py` for `punishment_spot_in_the_core`, `punishment_spot_by_the_traffic`, `punishment_spot_only_at_a_seat_of_justice`, and the presence floor `{scale}_has_punishment_spot` with its `meta(punishment_spot=False)` opt-out

### Implementation (green)

- [x] T021 [US2] Implement `punishment_spot()` in `settlement.py`: cangue frame, flogging post, kneeling stone, with a `# WHY:` pointer recording the research finding that the BEATING is a court act inside the magistracy and the street installation is a DISPLAY device
- [x] T022 [US2] Implement the four US2 checks in `check_village.py`
- [x] T023 [US2] Save one negative fixture per US2 check to `pool/regressions/`

### First map

- [x] T024 [US2] Add a punishment spot to `pool/towns/hoshizora.gen.py`, called BEFORE the urban packs so it reserves its ground (see the DRAW ORDER decision in plan.md), then regenerate and gate that one map

**Checkpoint**: US2 is independently deliverable.

---

## Phase 5: Roll out across the pool

**Purpose**: FR-021 - every town, walled town, and provincial city carries both features.

- [x] T025 [P] Add both features plus a boundary marker to `pool/towns/hirameki.gen.py` (walled county seat - the ground goes outside the wall), regenerate, gate
- [x] T026 [P] Add both features plus a boundary marker to `pool/provincial-cities/tango.gen.py` (screened city-tier ground, clear of the existing cemetery/cremation/ossuary cluster near the east wall), regenerate, gate
- [x] T027 [P] Add both features plus a boundary marker to `pool/provincial-cities/nagahara.gen.py` (screened city-tier ground; mind the Hayakawa bank set-backs the existing funerary features already respect), regenerate, gate
- [x] T028 Confirm every new check RAN on every one of the four maps (the grep-count diagnostic from T018) - a check that never runs looks exactly like a check that passes

---

## Phase 6: User Story 3 - The research survives the context window (Priority: P3)

**Goal**: a future reader can reconstruct why, without redoing the research.

- [x] T029 [P] [US3] Add the settlement-vocabulary entries for the punishment spot, execution ground, and boundary marker to the "Towns and walled towns" vocabulary in `settlements.md`, with the method signatures and the rules a spec author will trip over
- [x] T030 [P] [US3] Add the historical-grounding entries to the "Historical grounding" section of `settlements.md`: the China/Japan reconciliation (jurisdiction from China, siting from Japan) and why it explains the canon county-jail budget line; the Suzugamori size anchor and the volume ladder that scales it; the beating/display split; the 150 ft legibility compression and its disclosure; the governing variable for each element
- [x] T031 [US3] Write the setting-level sub-section into `/host-l7r-repo/setting/l7r.md` after The Ministry of Justice, following the L7R style conventions (AP-style numbers with the unit overrides, gender-neutral office-holders, "humans"/"inhabitants" not "people" in demographic contexts, "domain" not "demesne", two spaces after a period, hyphens only), and insert exactly ONE new TOC line in its correct nested position
- [x] T032 [US3] Verify with `git -C /host-l7r-repo diff` that the l7r.md diff contains ONLY the new section and the single new TOC line - no reflowed paragraphs, no other TOC lines touched, no SOURCE block anywhere altered. Do not commit: the GM owns git on that repo

---

## Phase 7: Polish and the closing gate

- [x] T033 Run the cheap linters: `python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy`
- [x] T034 Run the whole touched test files: `python3 -m pytest test_settlement.py test_checks.py -q -n auto --no-cov`
- [x] T035 Run `make done` ONCE, backgrounded, and act on the completion notification - never poll it. Fix everything it reports together, then re-run once
- [x] T036 **Principle XII closing gate**: batch every crop into ONE `crop_map.py` call across all four maps, read the PNGs together, and confirm per map that the execution ground reads as outside the settlement, as bare waste ground rather than a field, as disused at county tier, as on the road past the boundary stone, and as a visibly different place from the burial/cremation cluster. `make done` proves internal consistency; only the picture proves this
- [x] T037 Confirm SC-005: all hamlet and village renders are unchanged (no tracked manifest for those tiers is dirty after the full sweep)
- [ ] T038 Commit in the clone and run the stop-work ritual: `scripts/sync-with-main.sh done`

---

## Dependencies

```text
Phase 1 (setup)
   -> Phase 2 (registries + overlap plumbing)   [BLOCKS everything]
          -> Phase 3 US1 (execution ground + boundary marker)   [P1, MVP]
          -> Phase 4 US2 (punishment spot)                      [P2, independent of US1]
                 -> Phase 5 (pool rollout)   [needs both features to exist]
                        -> Phase 7 (gate + artifact review)
       Phase 6 US3 (docs) can run any time after Phase 3/4 land; T031-T032 touch a different repo entirely
```

US1 and US2 are genuinely independent after Phase 2 - they touch different methods and different checks, and each delivers a usable map on its own. Phase 5 depends on both only because it puts both onto the same maps.

## Parallel opportunities

- T006-T010 (US1 test authoring) are all `[P]` - different test functions, no shared state
- T019-T020 (US2 test authoring) likewise
- T025-T027 (three different pool gens) are `[P]` - different files
- T029-T030 (two different sections of settlements.md) are `[P]`; T031 is a different repo again

## Implementation strategy

**MVP = Phase 1 + 2 + 3.** That delivers the headline request - the execution ground, correctly sited - on one town map, with every siting rule gated and every gate backed by a negative fixture.

Then Phase 4 adds the in-town half, Phase 5 spreads both across the pool, Phase 6 records the why, and Phase 7 runs the real gate and looks at the pictures.

**Iteration discipline throughout**: run the red/green loop against the ONE motivating map (Hoshizora), where a regen + gate is 1-7s. Reserve the full pool sweep for the end - but it is MANDATORY then, because `settlement.py` and `check_village.py` are shared engine code and every pool map is downstream of them.

---

## Implementation notes (what changed against the plan, and why)

Recorded here rather than silently absorbed, because each was a design decision made against a real
failure rather than a preference.

1. **T021/T024 - the punishment ground is AUTO-SITED, not hand-placed before the packs.** The plan had
   it placed before the urban packs so it could reserve ground. In practice the opposite is right: it
   is placed AFTER the packs and the notice board by a new `place_punishment_spot()`, which scores
   street verges by traffic exactly as `place_kosatsuba` does. Hand-picked rects fed to `open_seat`
   failed `punishment_spot_by_the_traffic` on all three remaining maps the same way - `open_seat` ties
   toward the rect's CENTER, which is the open ground behind the frontage, precisely where a display
   feature must not be. Siting by the governing variable beats reserving ground.
2. **`execution_ground_beyond_the_burakumin_quarter` was renamed `execution_ground_on_the_outcast_side`
   and relaxed to DIRECTION only.** The radius half of the rule was unsatisfiable on a walled town
   (Hirameki's outcast quarter is extramural at the canvas corner, so "further out than the quarter"
   put the ground off the map), and radius is an artifact of where the wall sits. The claim the
   research supports - downwind, downstream, the outcast side - is directional.
3. **`execution_ground_by_the_road` measures gates at ~400 ft, roads at ~120 ft.** A road is a line the
   ground can hug; a gate is a point standing in for the road that leaves it. Hirameki draws no
   extramural road at all, so measuring its gates at the road's tolerance made the rule unsatisfiable.
4. **`execution_ground_past_the_boundary_marker` also demands the stone stand OUTSIDE the wall.** Found
   while siting Nagahara: a stone inside the rampart satisfied the between-ness arithmetic while
   asserting the opposite of what a boundary stone means.
5. **Label placement needed engine support, twice.** `punishment_spot` gained `label_above` and
   `label_xy` (the `paddy_field` convention), and `place_punishment_spot` probes the label outward
   through four directions x nine rings. A verge-hugging feature's default below-label lands on the
   frontage it hugs - that is not bad luck, it is what hugging the frontage means. The probe must use
   each building's AXIS-ALIGNED box, which for a rotated shopfront is much larger than its `w`/`h`.
6. **All three features are frame-setting keys** (`_CROP_HARD` + `_CROP_CITY`). Not in the plan, but a
   ground clipped at the frame edge reads as "somewhere off that way", which is the one thing its
   siting is not. The corollary bit twice: a seat outside the map's existing view drags the crop out
   and detaches the road from the edge it must run off, so seats are chosen inside the current view.
7. **A siting probe was written rather than guessed at** (scratchpad, not committed): it brute-forces
   the same predicates the gate enforces and prints legal ground/stone pairs. After the first two maps
   cost several regenerate-and-check cycles each, the last two cost one probe each.

8. **The Principle XII closing gate earned its keep, and this is the record of it.** Every automated
   check was green and every map passed when the rendered PNGs were opened - and Nagahara's execution
   ground, at 225 real ft from the burial cluster, plainly read as *part of that cluster*. The 150 ft
   constant had been derived by analogy to an existing dwelling-separation number rather than from a
   picture. It was raised to **400 ft** (the distance at which, at the coarsest grain we draw, the two
   are unmistakably two places), Nagahara's ground was re-sited, and both the constant's comment and
   the settlements.md grounding entry now record why. `check_village` proved internal consistency the
   whole time; only the artifact could show the number was wrong.
