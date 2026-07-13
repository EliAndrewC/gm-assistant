---
description: "Task list for City Quarter Density and Wall-Sizing Correctness"
---

# Tasks: City Quarter Density and Wall-Sizing Correctness

**Input**: Design documents from `/gm-assistant/specs/006-city-quarter-density/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/interfaces.md, quickstart.md

**Tests**: REQUIRED for this feature. Every new check is added red-first (a failing test/fixture exists before the check logic lands) per the project's constitution (Principle X) and CLAUDE.md's red-first discipline; 100% line coverage is gated.

**Working directory**: all source paths are under `/gm-assistant/.claude/skills/diagram/`.

**Organization**: grouped by user story. US1 is the MVP (the validator catches the bad map) and is independently testable with synthetic manifests. US2 declares quarters in the real cities and calibrates. US3 reframes the wall-sizing verdict.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallelizable (different file, no dependency on an incomplete task)
- **[Story]**: US1 / US2 / US3 (Setup, Foundational, Polish carry no story label)

---

## Phase 1: Setup (snapshot the crime scene FIRST)

**Purpose**: Freeze the known-bad map as a fixture before any code changes, and stage the named thresholds.

- [x] T001 Snapshot the current broken map BEFORE any change: `cp pool/nagahara.json pool/regressions/city_density_broken_nagahara.json` (525 in-wall dwellings, ~35 extramural commoners, empty NW quarter, near-empty block, no `M["quarters"]`).
- [x] T002 Record the baseline defect in `pool/regressions/city_density_broken_nagahara.notes.md`: capture today's `check_village.py pool/regressions/city_density_broken_nagahara.json` result (passes) and `--capacity` verdict (about_right / sized), as the "before" proof the new checks must overturn.
- [x] T003 [P] Add named threshold constants with docstring rationale stubs in `check_village.py`: `RESERVE_CAP_FRAC`, `QUARTER_DENSITY_FLOOR`, `QUARTER_DENSITY_CEIL`, `CIVIC_OPEN_TOL`, `DEAD_ZONE_MAX`, `EXTRAMURAL_COMMONER_MAX = 0`, plus sets `COMMONER_KINDS` and `EXTRAMURAL_EXEMPT_KINDS` (samurai estates / farmhouses / wharf / gate-market shops). Initial values from research.md section C; final values calibrated in T018.

---

## Phase 2: Foundational (the quarter engine - blocks US2 real declarations and calibration)

**Purpose**: The `s.quarter()` engine helper. US1's checks can be unit-tested with synthetic manifests, but US2's real-city declarations and the T018 calibration need this.

- [x] T004 Implement `s.quarter(poly, zone, kind=None, label=None)` in `settlement.py`: validate `zone` in {residential, civic, mixed, reserve}, require `kind` iff reserve, append `{poly, zone, kind, name}` to `M["quarters"]`. Purely declarative (no placement change).
- [x] T005 Implement reserve rendering in `s.quarter` for `kind` in {drill_ground, garden, agricultural_district}: draw a visible ground feature (drill-ground surface / garden planting / delegate to the field routines for an agricultural district), z-ordered like other ground features.
- [x] T006 [P] Unit tests in `test_settlement.py` (red-green): `s.quarter` records the manifest entry; reserve rendering emits the expected feature; invalid zone / missing reserve kind raise.

---

## Phase 3: User Story 1 - The validator rejects a lopsided or leaky city (Priority: P1) MVP

**Goal**: New/modified checks that flag the extramural leak, the missing quarter declarations, an under-dense residential quarter, an over-open civic quarter, and over-cap reserve.

**Independent Test**: Run the validator on `pool/regressions/city_density_broken_nagahara.json`: it flags the extramural commoners and the missing quarters, and reads under-filled (not about_right). Synthetic manifests with declared quarters exercise the pass side. No dependency on the real cities being retrofitted.

### Checks that need NO quarters (fire on the raw snapshot)

- [x] T007 [US1] Modify `population_consistent_with_housing` in `check_village.py`: for a walled city, count only dwellings with `point_in_poly(b, wall)`; extramural dwellings excluded. Update its message.
- [x] T008 [US1] Unit test in `test_checks.py` (red-green) for the in-wall population count (a walled manifest with dwellings straddling the wall), AND assert it now FIRES on `city_density_broken_nagahara.json` (525 < the ~558 floor).
- [x] T009 [US1] New check `city_commoner_dwellings_inside_walls` in `check_village.py`: fire if any `COMMONER_KINDS` dwelling sits outside `wall`; `EXTRAMURAL_EXEMPT_KINDS` never counted. Message names the count and a few coordinates.
- [x] T010 [US1] Unit tests in `test_checks.py` for `city_commoner_dwellings_inside_walls` (commoner outside -> fires; samurai estate / farmhouse / wharf / gate-market shop outside -> passes), AND assert it fires on the broken snapshot (~35).

### Checks that need declared quarters (unit-tested via synthetic manifests)

- [x] T011 [US1] New checks `city_quarters_declared` (walled city must have non-empty `M["quarters"]`) and `city_quarters_tile_interior` (no overlap, none outside the wall, no large uncovered interior region) in `check_village.py`.
- [x] T012 [US1] Unit tests in `test_checks.py` for T011 (synthetic: tiling passes; overlap/gap/extramural quarter fires), AND assert `city_quarters_declared` fires on the quarter-less broken snapshot.
- [x] T013 [US1] New check `city_residential_quarters_dense_enough` in `check_village.py`: for each residential/mixed quarter, average dwelling density within `[QUARTER_DENSITY_FLOOR, QUARTER_DENSITY_CEIL]`, AND no contiguous empty sub-region larger than `DEAD_ZONE_MAX` (fire-breaks are thinner). Message names the offending quarter and whether it failed on average or dead-zone.
- [x] T014 [US1] Unit tests in `test_checks.py` for T013 (synthetic: a packed quarter passes; a uniformly-sparse quarter fires on average; a half-dense/half-empty quarter fires on the dead-zone guard even with an in-band average - the key anti-trap case).
- [x] T015 [US1] New check `city_civic_quarter_not_mostly_open` in `check_village.py`: a civic quarter whose non-civic-building open share exceeds `CIVIC_OPEN_TOL` AND which holds little civic-building area is flagged (open + structureless). Unit tests (synthetic: a courtyard-heavy civic precinct with compounds passes; a bare "civic" quarter fires).
- [x] T016 [US1] New check `city_reserve_within_cap` in `check_village.py`: total reserve area / interior <= `RESERVE_CAP_FRAC`. Unit test (synthetic over-cap reserve fires; within-cap passes).
- [x] T017 [US1] Wire `city_density_broken_nagahara.json` into `test_regressions.py`, asserting the no-quarter checks (`population_consistent_with_housing`, `city_commoner_dwellings_inside_walls`, `city_quarters_declared`) fire on it. Add per-check synthetic negative fixtures under `pool/regressions/` where the red-first pattern warrants a pinned artifact.

**Checkpoint**: US1 delivers the MVP - the broken map is caught (extramural + missing quarters + under-filled), verified on the pinned fixture and synthetics, with zero changes to the real generators yet.

---

## Phase 4: User Story 2 - Cities declare quarters, and the band is calibrated (Priority: P2)

**Goal**: Both worked cities declare quarters; the thresholds are calibrated so Tango passes and the broken snapshot fails; Nagahara stops spilling commoners outside.

**Independent Test**: `python3 pool/tango.gen.py && check_village.py pool/tango.json` passes all new checks; the per-quarter density report lists each quarter in band; the broken snapshot still fails.

- [x] T018 [US2] Retrofit `pool/tango.gen.py`: declare its residential wards, the civic yamen + temple precincts, mixed merchant district, and the in-wall agricultural district as a `reserve` (kind `agricultural_district`); regenerate `tango.json`/`.svg`.
- [x] T019 [US2] Calibrate `QUARTER_DENSITY_FLOOR/CEIL` (target ~5x spread per research.md C2), `CIVIC_OPEN_TOL` (~0.70), `RESERVE_CAP_FRAC` (~0.20), `DEAD_ZONE_MAX` against Tango (must pass) AND `city_density_broken_nagahara.json` (must still fire the density/quarter checks). Record each final number's "why" in the constant's docstring (also folded into settlements.md in T027).
- [x] T020 [US2] Declare quarters in `pool/nagahara.gen.py` (residential laborer/merchant/burakumin wards, civic temple + government precincts, any intentional open ground as a declared reserve within cap), and route every former extramural commoner top-up INSIDE the wall (zero commoners outside).
- [x] T021 [US2] Regenerate Nagahara; confirm `city_commoner_dwellings_inside_walls`, `city_quarters_declared`, `city_quarters_tile_interior`, `city_reserve_within_cap`, and `city_civic_quarter_not_mostly_open` all pass; capture the per-quarter density report.

**Checkpoint**: both cities carry declared quarters; calibration proven (Tango green, broken snapshot red); Nagahara no longer leaks commoners.

---

## Phase 5: User Story 3 - Wall-sizing recommends the right action (Priority: P3)

**Goal**: The capacity verdict is computed against usable residential ground and maps to one clear action; Nagahara is resized to fit; over-cap reserve cannot launder emptiness.

**Independent Test**: `check_village.py pool/nagahara.json --capacity` returns a verdict mapping to one action; a synthetic over-cap-reserve city is flagged, never sized_and_packed.

- [x] T022 [US3] Rework `city_capacity` in `check_village.py`: `residential_capable_area = interior - civic_quarter_area - reserve_quarter_area`; verdict enum {sized_and_packed, densify, enlarge, shrink}; add `per_quarter` density table, `reserve_area`/`civic_area`/`reserve_frac`; count `placed` in-wall only; align the `densify` boundary to `pop_tol`; `shrink` also when the wall is only fillable via over-cap reserve.
- [x] T023 [US3] Update `city_wall_sized_to_population` to fire on `enlarge`/`shrink`; update the `--capacity` / `--capacity-map` CLI output (verdict names + area budget + reserve_frac + per-quarter table; `--capacity-map` overlays quarter zones). Unit tests in `test_checks.py` for each verdict branch (synthetic manifests) plus the CLI-guarded lines.
- [x] T024 [US3] Synthetic over-cap-reserve manifest test: a city whose empty ground is declared reserve beyond the cap is flagged (`city_reserve_within_cap` and/or `shrink`), never `sized_and_packed`. Pin as a regression fixture.
- [x] T025 [US3] Apply the verdict to `pool/nagahara.gen.py`: run `--capacity`; if `shrink`, scale the whole generator by `suggested_wall_scale` about the wall centre; re-run until `sized_and_packed` with every residential quarter in band and no dead zone. Regenerate.

**Checkpoint**: the wall-sizing verdict is action-mapped and agrees with the population check; Nagahara is correctly sized.

---

## Phase 6: Polish and Cross-Cutting

- [x] T026 Run the FULL validator on `pool/nagahara.json` to zero mechanical fails; render `rsvg-convert -w 950 pool/nagahara.svg -o /tmp/nag.png` and review; run the `building-review` subagent on the final Nagahara (author is not a reliable reviewer).
- [x] T027 Regenerate and validate the WHOLE pool (`tango`, `nagahara`, and all village/town maps) to confirm none regressed; confirm all pinned regression fixtures still fire; confirm `city_density_broken_nagahara.json` still fails the new checks.
- [x] T028 [P] Update `settlements.md`: the quarter/zoning model, per-quarter density judgement + dead-zone guard, reserve kinds + cap, civic-open tolerance, the reframed capacity verdicts, and the recorded "why" for every threshold (research.md section C), plus the empirical post-mortem (section A) explaining why per-quarter replaced the aggregate.
- [x] T029 [P] Green gate: `ruff check .` + `ruff format --check .` + `mypy --strict check_village.py settlement.py` + `python3 -m pytest` (100% coverage) + `grep -RlP '[\x{2013}\x{2014}]' *.py *.md pool/*.gen.py` returns nothing.
- [x] T030 [P] Update memory `project_diagram_city_mode.md`: the per-quarter density model, the extramural-leak fix, the reframed verdict, and the lesson (aggregate-blind-to-distribution; keep a known-bad fixture that must fail).

---

## Dependencies and Execution Order

- **Setup (T001-T003)** first; **T001 MUST precede every code change** (snapshot the crime scene).
- **Foundational engine (T004-T006)** before US2 real declarations (T018, T020) and the T019 calibration.
- **US1 (T007-T017)** depends only on Setup (its checks are unit-tested with synthetic manifests) - the MVP, deliverable without touching the real generators.
- **US2 (T018-T021)** depends on US1 checks existing (to calibrate against) and the engine (T004-T006).
- **US3 (T022-T025)** depends on US2 (quarters declared, so residential-capable ground is computable) - T025 (Nagahara resize) depends on T022 verdict + T020 declarations.
- **Polish (T026-T030)** last; T026/T027 depend on all generator work; T028-T030 are [P] (different files).

### Within-file serialization

Most check tasks edit `check_village.py` (serialize T007, T009, T011, T013, T015, T016, T022, T023). Engine tasks edit `settlement.py` (T004-T005). These two files can progress in parallel with each other. Doctrine/memory (T028, T030) and the green gate (T029) touch separate files and are [P].

## Parallel Opportunities

- T003 (constants) [P] with T004-T006 (engine, different file).
- T006 (settlement tests) [P] with the US1 check work (different file).
- T028, T029, T030 all [P] (settlements.md / gate run / memory file - distinct targets).

## Implementation Strategy

- **MVP = US1 alone**: after Phase 3, the validator catches the exact defect (extramural commoners + missing quarters + under-filled), proven on the pinned broken-Nagahara fixture and synthetics, with no generator changes. That is a shippable increment: the toolchain can no longer green-light a lopsided/leaky city.
- **US2** makes the real cities conform and calibrates the numbers against Tango-good / Nagahara-bad.
- **US3** turns the diagnosis into the "densify / enlarge / shrink" recommendation and resizes Nagahara.
- Ship incrementally; each phase ends at a testable checkpoint.
