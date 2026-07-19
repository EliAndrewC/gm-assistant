---
description: "Task list for Village Visual Variation Knobs"
---

# Tasks: Village Visual Variation Knobs

**Input**: Design documents from `/specs/005-village-variation-knobs/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/knob-interface.md, quickstart.md

**Tests**: INCLUDED. The project mandates red-green TDD (Constitution Principle X) and the diagram skill is check-driven; every new check/knob lands test-first. All paths are under `.claude/skills/diagram/`.

**Note on the shared spec-kit pointer**: `.specify/feature.json` is a single shared slot and a concurrent effort (`006-city-quarter-density`) currently owns it. Run this feature's scripts with `SPECIFY_FEATURE=005-village-variation-knobs`, or set `.specify/feature.json` back to `specs/005-village-variation-knobs` before `/speckit-implement` (coordinate so the two efforts do not clobber each other).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1..US4 (user-story phases only)

---

## Phase 1: Setup (the maintained gate)

**Purpose**: wire the Principle X gate so lint/type/test run together and cannot be missed going forward.

- [x] T001 Add `ruff` (lint + format) and `mypy` (global `strict = true`) config to `.claude/skills/diagram/pyproject.toml`, keeping the existing pytest + `fail_under = 100` config.
- [x] T002 [P] Create `.claude/skills/diagram/Makefile` with a `done:` target running `ruff check` + `ruff format --check` + `mypy` + `pytest --cov-fail-under=100`, so all checks run as one command.
- [x] T003 [P] Document the `make done` gate + how to run it in `.claude/skills/diagram/SKILL.md`.

---

## Phase 2: Foundational (blocking prerequisites)

**Purpose**: bring the skill to full Principle X compliance (the GM-directed ratchet) AND build the shared knob machinery. **No user-story work begins until this phase is complete.**

**⚠️ CRITICAL**: blocks all user stories.

### 2a. Principle X ratchet (ruff + mypy)

- [x] T004 Fix the ~10 `ruff` findings (unused vars, lambda-assignments) in `settlement.py`, `check_village.py`, `waterfields.py`; `ruff check` + `ruff format --check` green.
- [x] T005 Configure the mypy per-module ratchet in `pyproject.toml`: global `strict`, with `settlement.py` + `check_village.py` + `waterfields.py` relaxed via `[[tool.mypy.overrides]]`, so the gate is green while NEW code is strict from day one.
- [x] T006 Migrate `waterfields.py` to `mypy --strict` (annotate; remove its relax override); pytest stays green. (~99 errors - smallest module first.)
- [x] T007 Migrate `check_village.py` to `mypy --strict` (annotate; remove its relax override); pytest + coverage stay green. (~1,107 errors - large; move CLI `print` behind the script entrypoint / `logging`.)
- [x] T008 Migrate `settlement.py` to `mypy --strict` (annotate; remove its relax override); pytest + coverage stay green. (~1,266 errors - largest; a typed manifest structure helps.)

### 2b. Knob machinery core (the shared engine every story uses)

- [x] T009 [P] Write FAILING unit tests for the seeded roll engine (determinism: same spec+seed -> same draw; independence: different knobs draw separately; two seeds -> different combos) in `test_settlement.py`.
- [x] T010 Implement the `Knob` registry + `roll(seed, knob_name, context)` (independent, deterministic, seeded) in `settlement.py` (green T009).
- [x] T011 [P] Write FAILING unit tests for the historical-typing gate (a value invalid for the stated geography is excluded from the roll; a pinned invalid value is rejected/warned) in `test_settlement.py`.
- [x] T012 Implement the typing-rule gate + the knob-declaration surface (extend `s.meta(...)` to pin/leave-unset knobs; resolution order pinned -> rolled -> default) in `settlement.py` (green T011).

**Checkpoint**: gate is green (ruff + format + mypy --strict + pytest 100%); knob engine rolls + gates; user stories can begin.

---

## Phase 3: User Story 1 - Same water direction, still visually distinct (Priority: P1) 🎯 MVP

**Goal**: two same-`down_deg` villages read as different places; Kikuta and Hoshigaoka stop twinning.

**Independent Test**: regenerate the pool; the twin-detector reports no twinned same-`down_deg` pair; Kikuta and Hoshigaoka differ on >= 4 SC-001 axes and both pass `check_village`; author render-review confirms they read as different places.

### Tests for User Story 1 (write first, ensure they FAIL)

- [x] T013 [P] [US1] Negative fixture + test: the twin-detector FIRES on a deliberately-twinned same-`down_deg` manifest pair, in `test_checks.py`.
- [x] T014 [P] [US1] Unit tests: headman + primary-shrine positions are DERIVED from `cluster_position` + `lane_skeleton` (not constants), parametrized over skeletons, in `test_settlement.py`.
- [x] T015 [P] [US1] Unit tests: each Family-A knob's value space + typing rule (parametrized), in `test_settlement.py`.

### Implementation for User Story 1

- [x] T016 [US1] Implement `cluster_position` + `cluster_shape` knobs (round / elongated / crescent / split-into-2-hamlets), field-adjacent + off the flood toe, in `settlement.py` (green T015).
- [x] T017 [US1] Implement the `lane_skeleton` knob (spine / T / Y / cross / waterside) + DERIVED headman & primary-shrine placement in `settlement.py` (green T014).
- [x] T018 [US1] Implement the `water_source_position` knob (pond corner / mid-margin / chain; stream entry edge), keeping the source uphill of the field intake, in `settlement.py` + `waterfields.py`.
- [x] T019 [US1] Implement the `plot_texture` (size + organic/grid regularity) + `grain_drift` knobs in `waterfields.py` (resolves the "uniform 45deg grain" residual).
- [x] T020 [US1] Implement the focal-feature catalog placement (crescent pond, ancestral hall, water-mouth complex, mill, market, secondary shrine) in `settlement.py`, each placed by the existing overlap/set-back invariants and recorded in the manifest.
- [x] T021 [US1] Implement the pool-level twin-detector in `check_village.py` (SC-001 axis discretization + >= 4-of-7 threshold), tuned against the re-varied pool (green T013).
- [x] T022 [US1] Re-vary `pool/hoshigaoka.gen.py` through the knobs (distinct cluster/lane/water/grain/focal set); `check_village` green + render self-review.
- [x] T023 [US1] Re-vary `pool/kikuta-village.gen.py` through the knobs so it differs from Hoshigaoka on >= 4 axes; `check_village` green + twin-detector clean + render self-review.
- [x] T024 [US1] Record the China-first historical grounding for every Family-A knob value + the twin-detector axis set/threshold in `settlements.md` (SC-005).


> **Backlog (surfaced by the twin-detector, 2026-07-15):** Ikegami / Hikari no Sato (down_deg 90) also twin (differ on 1/7 axes). GM scoped the US1 re-vary to Kikuta + Hoshigaoka only; this pair is deferred for a later pass.

**Checkpoint**: MVP done - the twinning is fixed and mechanically guarded. STOP and validate (SC-001, SC-002, SC-003).

---


> **Structural variation added (2026-07-15, GM-directed):** the earlier 4-axis PASS still read as similar to the GM because it varied only INTERNAL detail (lane pattern, grain, foci) on a SHARED archetype. Fixed by adding two structural capabilities and the biggest visual differentiator: `cluster_seeds` (shape: round/elongated/crescent/split, T016 mechanism) and `line_seeds` + `settlement_form` (the LINEAR ribbon archetype, a Family-B/US4 knob pulled forward). Kikuta re-varied to a LINEAR ribbon village vs Hoshigaoka's NUCLEATED blob -> now differ on 5/8 twin-detector axes (settlement_form added as the 8th axis). Still open: T018 water_source_position geometry; a driven `cluster_position`; the rest of the Family-B archetypes (terraces/polder/water-town).

## Phase 4: User Story 2 - Roll a distinct village from a seed (Priority: P2)

**Goal**: a minimal spec (seed + scale + `down_deg` + water-source kind [+ region]) yields a complete, distinct, gate-passing village.

**Independent Test**: generate several minimal specs differing only in seed; each rolls a different coherent knob combination, all pass the gate, none reads as a copy.

- [x] T025 [P] [US2] FAILING test: a minimal spec generates a gate-passing map with zero hand-placed coordinates (SC-004); two seeds roll different combinations, in `test_settlement.py`.
- [x] T026 [US2] Implement the minimal-spec entrypoint (roll every unpinned knob) + add a demo minimal `pool/<name>.gen.py`; `check_village` green (green T025).

**Checkpoint**: US1 + US2 both work.

---

## Phase 5: User Story 3 - Pin any knob for a designed village (Priority: P2)

**Goal**: any knob can be pinned while the rest roll/default; incompatible pins are rejected/warned.

**Independent Test**: pin one knob and leave others unset -> pinned value honored, deterministic across regenerations; pin an incompatible value -> rejected/warned, not drawn.

- [x] T027 [P] [US3] FAILING test: a pinned knob is honored + byte-identical across two regenerations (SC-006); a historically-incompatible pin is rejected/warned, in `test_settlement.py`.
- [x] T028 [US3] Implement pin-honoring determinism + incompatible-pin rejection/warning in `settlement.py` (green T027).

**Checkpoint**: US1 + US2 + US3 all work; knobs are a superset of hand-authoring.

---

## Phase 6: User Story 4 - Terrain / settlement archetypes (Priority: P3, incremental)

**Goal**: whole-archetype variety (terraces, polder, ribbon, mulberry-fishpond; linear/dispersed/water-town; land-use overlays), one validated end-to-end before the next.

**Independent Test**: a map built with a non-default archetype passes a gate that includes the archetype's rules; its grounding is recorded.

- [x] T029 [P] [US4] Research + record the China-first grounding for the FIRST archetype (recommended: linear settlement form OR contour terraces - biggest bang) in `research.md` + `settlements.md`.
- [x] T030 [US4] Implement the archetype registry (`field_archetype` / `settlement_form` / `land_use_overlay`) + region-typing in `settlement.py`.
- [x] T031 [P] [US4] Write FAILING tests + negative fixtures for the first archetype's validator rules in `test_checks.py`.
- [x] T032 [US4] Implement the first archetype's geometry generator (in `waterfields.py`/`settlement.py`) + settlement placement + archetype-specific validator rules (green T031); add a demo `pool/<name>.gen.py`; grounding recorded.
- [x] T033 [US4] REPEAT the T029/T031/T032 increment for each subsequent archetype (terraces, polder, ribbon, mulberry-fishpond; linear/water-town/dispersed; rape/lotus/tea overlays) - one at a time, each its own validated round.

**Checkpoint**: at least one archetype proves the registry; the rest follow incrementally.

---

## Phase 7: Polish & Cross-Cutting

- [x] T034 [P] Document the full knob surface + roll-vs-pin in `SKILL.md` and update the settlements.md map roster.
- [x] T035 [P] Save negative-fixture regressions to `pool/regressions/` for the twin-detector + each new check (coverage alone does not prove teeth).
- [x] T036 Run the full gate: `make done` (ruff + format + mypy --strict + pytest 100% cov) green; `check_village` on all six maps; twin-detector reports zero twinned pairs; render-review Kikuta + Hoshigaoka (SC-001..SC-006).
- [x] T037 Verify 100% of shipped knob values have recorded grounding in `settlements.md` (SC-005); run `quickstart.md` walkthrough end-to-end.

---

## Dependencies & Execution Order

- **Phase 1 (Setup)**: start immediately.
- **Phase 2 (Foundational)**: after Setup; BLOCKS all user stories. 2a (ratchet) and 2b (knob engine) can proceed in parallel, but the gate must be green before Phase 3. T006 → T007 → T008 are ordered by size but independent; each keeps pytest green.
- **Phase 3 (US1, MVP)**: after Phase 2. T016-T020 build on the knob engine (T010/T012); T021 (twin-detector) is independent of them; T022/T023 (re-vary) depend on T016-T021; T024 (grounding) after the knobs land.
- **Phase 4 (US2)** and **Phase 5 (US3)**: after Phase 2; mostly emergent from the knob engine + US1 machinery; independently testable.
- **Phase 6 (US4)**: after Phase 2; each archetype is its own increment and does not block US1-US3.
- **Phase 7 (Polish)**: after the desired stories are complete.

### Within a story

- Tests written and FAILING before implementation (T013-T015 before T016-T021; T025 before T026; T027 before T028; T031 before T032).
- Knob engine (Phase 2b) before any knob (Phase 3).
- Re-vary maps (T022/T023) only after all Family-A knobs + the twin-detector exist.

### Parallel opportunities

- Setup: T002, T003 in parallel.
- Foundational: 2a and 2b tracks in parallel; T009 and T011 (test-writing) in parallel.
- US1: T013, T014, T015 (tests) in parallel; then the knob implementations T016-T020 are mostly parallel (different regions of `settlement.py`/`waterfields.py` - coordinate to avoid same-hunk edits).

---

## Implementation Strategy

### MVP first (User Story 1)

1. Phase 1 Setup → 2. Phase 2 Foundational (the ratchet + the knob engine; gate green) → 3. Phase 3 US1 → 4. STOP and validate: twin-detector clean, Kikuta vs Hoshigaoka differ on >= 4 axes, all six maps pass, render-review. This is the demo that answers the GM's complaint.

### Incremental delivery

Foundation → US1 (MVP, the distinctiveness win) → US2 (roll-from-seed) → US3 (pin-any-knob) → US4 archetypes one at a time. Each increment keeps the gate green and adds value without breaking the previous maps.

---

## Notes

- Every implementation task ends with the diagram-skill gate (`make done`) green + `check_village` on affected maps + a render self-review for any changed map (Constitution VI).
- The mypy migration tasks (T006-T008) are large; they are typing-only work verified by mypy + the unchanged pytest gate, so they carry low behavioral risk but real effort.
- Byte-identical preservation is NOT required for the two re-varied maps (Kikuta, Hoshigaoka); the other four village/hamlet maps stay as-is and must keep passing.
- Record the "why" for every knob value + archetype in `settlements.md` as it lands (project policy; SC-005).
