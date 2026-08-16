# Tasks: Human-Scale Splits (settlement.py + the two big test files)

**Input**: Design documents from `/specs/025-human-scale-splits/`

**Prerequisites**: plan.md, spec.md, research.md (R1-R12), data-model.md (E1-E5), contracts/import-surface.md, quickstart.md

**Tests**: No new-behavior test tasks - this is a pure-move feature; the identity oracles (research R4) ARE the feature's tests, per the plan's Principle X note.

**Organization**: By user story; landing order US1 -> US2 -> US3 -> US4 (research R12), one green-gate commit per story. All source paths are repo-relative; the skill dir is `.claude/skills/diagram/`, and every `make`/`pytest` runs from the session clone (the Makefile guard enforces this).

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: baseline proof + shared oracle tooling; no production changes

- [x] T001 Establish the pre-feature baseline: run `make done` in `.claude/skills/diagram/` (background, tail the log - no wrapped exit codes) and confirm green before anything moves
- [x] T002 [P] Write the generation-identity oracle `specs/025-human-scale-splits/oracle_gen.py` (capture/compare sha256 of `.json` and of `.svg` **with the `<!-- render-cache: ... -->` stamp line stripped** - the stamp hashes the engine fingerprint and legitimately changes when settlement.py becomes a package; the drawn bytes must not - over every regen-runnable pool gen + a fixed-seed hamletgen cohort; adapt the 022/024 sweep pattern, seeds passed in)
- [x] T003 [P] Write the gate-identity oracle `specs/025-human-scale-splits/oracle_gate.py` (capture/compare ordered `check_village.gate()` verdict streams over every `pool/**/*.json` manifest + `pool/regressions/` fixture; 022 oracle-sweep method)

**Checkpoint**: baseline green; oracle tooling exists and its capture mode runs

---

## Phase 2: Foundational (Blocking Prerequisites)

None - the four stories share no unbuilt infrastructure beyond Phase 1's tooling. (Recorded so the empty phase is a decision, not an omission.)

---

## Phase 3: User Story 1 - Clause 13 explicitly covers test files (Priority: P1) 🎯 MVP

**Goal**: the rule and both mirrors say tests are covered, with the recorded why (context-window tokens; a test file is loaded under the same conditions as source; ordered-data registries stay the only carve-out)

**Independent Test**: grep the three sites per quickstart.md; docs-only diff, so no `make done` (docs-only rule)

- [x] T101 [US1] Amend clause 13 in `.specify/memory/constitution.md`: add the tests-are-covered sentence + why, bump version 1.6.0 -> 1.6.1 (PATCH per research R10), update the sync-impact header
- [x] T102 [P] [US1] Mirror the amendment: root `CLAUDE.md` "Files stay at human scale" bullet gains the tests-included statement; `.specify/templates/plan-template.md` Principle X clause-13 sentence gains "(test files included)"
- [x] T103 [US1] Verify all three sites by grep (quickstart.md commands), then commit the story: `docs(constitution): clause 13 covers test files (v1.6.1) + mirrors - feature 025 US1`

**Checkpoint**: US1 landed; the rule the rest of the feature enforces is written down

---

## Phase 4: User Story 2 - test_checks.py becomes a navigable test package (Priority: P2)

**Goal**: `test_checks.py` (11,475 lines) -> `test_checks/` package mirroring `check_village/`'s file map (data-model E2), collection-identical

**Independent Test**: sorted `pytest --collect-only -q` node lists match on `::`-suffix pre/post; full `make done` green

- [x] T201 [US2] Capture the collection baseline to `specs/025-human-scale-splits/collect_checks_pre.txt` and derive the check -> `check_village` segment-file mapping (from `check_village/registry.py` + `test_fixtures/gate_check_names.json`) to assign every test function a destination module per data-model E2
- [x] T202 [US2] Create `.claude/skills/diagram/test_checks/` as a package: `__init__.py`; `_builders.py` with the shared builders moved verbatim (`f`, `bldg`, `manifest`, `house`, `yard`, `garden`, `well`, `grove`, `vgrove`, `_channel`, `_sink_channel`, `_drain`, `_dryplot`, and any other module-level helpers); one `test_common_*.py` per `common_*` module, one `test_segments_*.py` per `segments_*` file (the three `segments_10_city_battery_*` share one module unless it exceeds ~2,500 lines), `test_driver_and_fixtures.py` for driver/cross-cutting tests - test bodies verbatim, only the `from test_checks._builders import ...` line new; delete `test_checks.py`
- [x] T203 [P] [US2] Write `.claude/skills/diagram/test_checks/CLAUDE.md`: "look here when" index mapping each test module to the `check_village/` file it exercises (check_village/CLAUDE.md is the exemplar)
- [x] T204 [US2] Capture `collect_checks_post.txt`, compare on `::`-suffix (zero lost/added/renamed nodes), run full `make done` (background, tail log), then commit the story: `refactor(diagram): 025 US2 - test_checks.py becomes the test_checks/ package (collection-identical)`

**Checkpoint**: US2 landed; the test-split mechanics US4 reuses are proven

---

## Phase 5: User Story 3 - settlement.py becomes a navigable package (Priority: P2)

**Goal**: `settlement.py` (16,016 lines; one 338-method class + ~2k lines of helpers) -> `settlement/` package per data-model E1 (mixins + `_geom`/`_knobs` + composed class in `core.py`), byte-identical outputs, split-sensitive infra updated (E5)

**Independent Test**: oracle_gen + oracle_gate compare clean; `make done` green (incl. mypy --strict on the package and the 94-floor settlement coverage ratchet)

- [x] T301 [US3] Capture the pre-split oracles: `oracle_gen.py capture` -> `oracle_gen_pre.json`; `oracle_gate.py capture` -> `oracle_gate_pre.json` (both in `specs/025-human-scale-splits/`)
- [x] T302 [P] [US3] Census the consumers: scan all importers for `settlement.<name>` / `from settlement import` references (the re-export surface, contracts/import-surface.md method) AND every `monkeypatch.setattr`/`patch` targeting settlement module-level names (research R9); write both lists to `specs/025-human-scale-splits/consumer-census.md`
- [x] T303 [US3] Write the mover script `specs/025-human-scale-splits/split_settlement.py`: AST-driven, cuts `settlement.py` at data-model E1's boundaries into `_geom.py`, `_knobs.py`, mixin modules, and `core.py` (class attrs + `__init__` + composed `class Settlement(<mixins>)`); adds `self: "Settlement"` annotations + `if TYPE_CHECKING: from .core import Settlement` per mixin (research R1/R2); generates `settlement/__init__.py` explicit re-exports from the T302 surface; moves banner comments with their code
- [x] T304 [US3] Run the mover, delete `settlement.py`, add per-module imports of the helpers each mixin uses, and iterate until `python3 -c "import settlement"` and every consumer module imports clean
- [x] T305 [US3] Update the split-sensitive infrastructure (data-model E5, same commit): `Makefile` coverage patterns `*/settlement.py` -> `*/settlement/*` + `SETTLEMENT_COV_FLOOR` comment; `pyproject.toml` mypy `files` `"settlement.py"` -> `"settlement"` + ruff per-file-ignore `"settlement/__init__.py" = ["F401"]`; `render_cache.py` `engine_fingerprint()` walks non-test `.py` at any depth minus `pool/`, `wip/`, itself (research R6) + update `test_render_cache.py`
- [x] T306 [P] [US3] Re-point module-level monkeypatch targets found in T302 to the defining submodule, and update every doc naming `settlement.py` (`.claude/skills/diagram/CLAUDE.md`, `SKILL.md`, `migration-plan.md`, `settlements/` docs, `docs/` references if any)
- [x] T307 [P] [US3] Write `.claude/skills/diagram/settlement/CLAUDE.md`: "look here when" index for every subfile, the DRAW ORDER pointer (core.py record streams + finish.py assembly), and the monkeypatch-a-policy-table section (check_village precedent)
- [x] T308 [US3] Prove and land: `oracle_gen.py compare` + `oracle_gate.py compare` clean; fill the generated surface into `specs/025-human-scale-splits/contracts/import-surface.md`; full `make done` (background, tail log); commit the story: `refactor(diagram): 025 US3 - settlement.py becomes the settlement/ package (byte-identical outputs)`

**Checkpoint**: US3 landed; `settlement/` layout is final, unblocking US4

---

## Phase 6: User Story 4 - test_settlement.py mirrors the new layout (Priority: P3)

**Goal**: `test_settlement.py` (7,123 lines) -> `test_settlement/` package mirroring the final `settlement/` module map (data-model E3), collection-identical

**Independent Test**: same as US2 (collect-list `::`-suffix compare + full `make done`)

- [x] T401 [US4] Capture `collect_settlement_pre.txt`; map every test function to the `settlement/` module defining its primary exercised attribute (data-model E3)
- [x] T402 [US4] Create `.claude/skills/diagram/test_settlement/` package: `__init__.py`, `_builders.py` (shared helpers verbatim), one `test_<module>.py` per settlement module that has tests - bodies verbatim, new import lines only; delete `test_settlement.py`
- [x] T403 [P] [US4] Write `.claude/skills/diagram/test_settlement/CLAUDE.md` index (module <-> settlement/ file map)
- [x] T404 [US4] Capture `collect_settlement_post.txt`, compare on `::`-suffix, run full `make done` (background, tail log), commit the story: `refactor(diagram): 025 US4 - test_settlement.py mirrors the settlement/ package (collection-identical)`

**Checkpoint**: all four stories landed

---

## Phase 7: Polish & Cross-Cutting Concerns

- [x] T501 Re-run the file-size census over `.claude/skills/diagram/` and record the before/after table (34,614 lines in 3 files -> N files, max size) in `specs/025-human-scale-splits/research.md` as R13 "What implementation taught the plan", including any boundary-map deviations made at T304 and why
- [ ] T502 Stop-work ritual: final commit, then `scripts/sync-with-main.sh done` from the clone (locked pull+push + render-sync). NOTE: the 19 frozen legacy maps' renders are now write-once git exhibits (main commit 0719da0) whose gens never run - they keep their old stamps; only scripted-tier maps re-stamp under the new engine fingerprint, and their drawn bytes are proven unchanged by the oracle

---

## Dependencies

- **US1** (Phase 3): independent - only Phase 1's baseline
- **US2** (Phase 4): independent of US1/US3; needs T001 baseline
- **US3** (Phase 5): independent of US1/US2 in content; lands after US2 by doctrine (R12). T303 needs T302's census; T304 needs T303; T305/T306/T307 after T304; T308 last
- **US4** (Phase 6): **strictly after US3** (mirrors its final layout)
- Phase 7 after all stories

## Parallel Opportunities

- T002 + T003 (different files); T101 + T102 within US1; T203 alongside T202's tail; T302 alongside T301; T305/T306/T307 across different files after T304; T403 alongside T402's tail. Story phases themselves land sequentially by doctrine - parallelism lives inside a story, batched into single turns per the iteration-loop rules.

## Implementation Strategy

US1 alone is the MVP (the durable rule). Each story is a complete, separately-committed,
gate-green increment; a stop after any checkpoint leaves the repo consistent. The mover script
(T303) is committed with the feature as evidence, like 024's `split_package.py`.
