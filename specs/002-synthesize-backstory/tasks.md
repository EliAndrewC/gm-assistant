# Tasks: Synthesize Backstory

**Input**: Design documents from `/specs/002-synthesize-backstory/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/synthesize.md, quickstart.md

**Tests**: INCLUDED - Principle X (NON-NEGOTIABLE) mandates red-green TDD and 100% coverage on new production logic (FR-011), and the external Gemini boundary is fixture-tested (Principle X.5).

**Organization**: By user story. Per the GM's "refactor-first then button" directive, the Part A productionization (Foundational + US3) precedes the Part B button (US1, US2). US1 is the user-facing MVP but is sequenced after the refactor; it has no hard dependency on US3 (bundling) once Foundational is done.

**Path convention**: web app under `webapp/`; chargen sub-app at `webapp/chargen/`. Tests live beside code as `test_<module>.py`; fixtures in `webapp/chargen/fixtures/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1 / US2 / US3 for story-phase tasks only

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Relocate production content and put the new module under the Principle X gate.

- [X] T001 [P] Copy `webapp/bakeoff/flavor_clans.md` to `webapp/chargen/flavor_clans.md` (production home; the bakeoff copy is removed later when `bakeoff/` is deleted, completing the move). Verify: files identical (`diff`).
- [X] T002 [P] In `webapp/pyproject.toml`, add `chargen/brief.py` to `[tool.coverage.run] source` (and ensure it is not omitted) so the new module is under the 100% gate; confirm it is NOT in the chargen ruff `per-file-ignores` or mypy grace `overrides`. Verify: diff shows only the intended additions; a later `make cov` run measures `chargen/brief.py`.
- [X] T003 [P] Create `webapp/chargen/fixtures/` directory (for the saved Gemini response). Verify: directory exists.

---

## Phase 2: Foundational (Part A refactor - BLOCKS all stories)

**Purpose**: Assemble the full-corpus brief in compliant production code. No story can ship until `synthesize()` produces the full brief in dev.

**⚠️ CRITICAL**: Blocks US1, US2, US3.

- [X] T004 [P] Write FAILING tests in `webapp/chargen/test_brief.py` (red): corpus resolution order (explicit config/env → bundled `webapp/setting/` → dev mount `/host-l7r-repo/setting/`), fail-loud typed error when corpus/files absent, full-brief assembly structure (brief + clan blurb + flavor + l7r + labeled budgets), and "The Great Clans" extraction by heading. Verify: `pytest webapp/chargen/test_brief.py` fails.
- [X] T005 Implement `webapp/chargen/brief.py` to pass T004 (green): typed `BriefSources` resolution, verbatim file reads (never mutate - Principle V), `extract_section` for the blurb, `build_full_brief()` assembly; raise a clear typed error on missing corpus (FR-010); use `logging`, not `print`. Verify: `pytest webapp/chargen/test_brief.py` passes; `ruff check`, `ruff format --check`, `mypy --strict` clean on `chargen/brief.py`.
- [X] T006 Wire `webapp/chargen/synthesis.py` `load_brief` / `build_prompt` to delegate to `chargen.brief`, preserving the existing signatures/behavior and keeping the honor model + calendar instruction (FR-004). Verify: existing `_main` path still assembles; no behavior change to `synthesize()` other than richer brief.
- [X] T007 Add equivalence test `webapp/chargen/test_brief_equivalence.py` asserting `chargen.brief.build_full_brief() == bakeoff.briefs.build_tier('full')` for the same corpus (FR-009); runs while `bakeoff/` still exists. Verify: test passes (gates the later bakeoff deletion).
- [X] T008 Record one real `gemini-3.1-pro-preview` `generate_content` response into `webapp/chargen/fixtures/` and add `webapp/chargen/test_synthesis.py` exercising `build_prompt` (no network) and `synthesize()` with the client's `generate_content` substituted by the saved fixture (Principle X.5 - fixture, not transport mock). Verify: tests pass; `--cov=...` shows the new logic at 100%.

**Checkpoint**: `synthesize()` produces the full-corpus brief in dev; new code passes the five-point Python gate.

---

## Phase 3: User Story 3 - Same fidelity in the deployed app (Priority: P1)

**Goal**: The full-corpus prompt is available with no bind-mount, via a bundled snapshot (completes Part A productionization).

**Independent Test**: Build/run with the mount absent and the bundle present; `synthesize()` yields full-grounded output; with neither present, it errors clearly (no thin fallback).

- [X] T009 [US3] Extend the `prepare-deploy` target in `webapp/Makefile` to snapshot `l7r.md` + `budgets.md` from the resolved corpus dir into `webapp/setting/`; add `webapp/setting/` to `webapp/.gitignore` and ensure it is in the Docker build context (check `webapp/.dockerignore`). Verify: `make prepare-deploy` populates `webapp/setting/` with both files.
- [X] T010 [P] [US3] Add a test case in `webapp/chargen/test_brief.py` for bundle-path resolution with the mount absent (corpus resolves to `webapp/setting/`) and for the missing-corpus error path. Verify: `pytest` passes; coverage stays 100%.
- [X] T011 [US3] Validate per quickstart: with the mount path unavailable, `synthesize()` (direct call, no button) assembles from the bundle; remove the bundle and confirm a clear error. Verify: documented in quickstart run; no silent degradation.

**Checkpoint**: Productionized brief works from a mount-free artifact (US3 complete).

---

## Phase 4: User Story 1 - Synthesize a backstory from a character (Priority: P1) 🎯 MVP

**Goal**: One click on the chargen character page returns a 1-3 paragraph grounded backstory.

**Independent Test**: Generate a character, click Synthesize Backstory, get a coherent 1-3 paragraph result consistent with clan/rank/honor/traits; honor reads as conviction (low honor not villainous).

- [X] T012 [US1] Add an `@ajax synthesize` route to `webapp/chargen/website.py` mirroring `generate_art`: read the displayed character payload + optional `extra_notes`, call `synthesis.synthesize(...)`, return `{ok: true, backstory}` or `{ok: false, error}`; never fall back to a thinner prompt (FR-010). Verify: route importable; manual call returns envelope.
- [X] T013 [P] [US1] Add the Synthesize Backstory control to `webapp/chargen/templates/index.html`: button, in-progress state, result panel (mirror the portrait control), button disabled while a request is in flight. Verify: renders on the character page.
- [X] T014 [US1] Add `webapp/chargen/test_website_synthesize.py`: success envelope via fixture-backed `synthesize`, and error envelope via an injected failure (missing credential / model error). Verify: `pytest` passes; covered logic at 100%.
- [X] T015 [US1] UI verification (Principle I + VI) on the chargen character page: run `webapp/tests/screenshot.py` (GM-100 / GM-200 / tablet / mobile, multi-scroll contact sheets) and `webapp/tests/dom_audit.py` (zero clipping + balance issues); if the tooling needs a `/chargen` target URL, add it. Then an independent `frontend-review` subagent pass at GM-200. Verify: zero DOM-audit issues; reviewer sign-off.

**Checkpoint**: MVP - the GM can synthesize a grounded backstory in dev with one click.

---

## Phase 5: User Story 2 - Re-roll and steer (Priority: P2)

**Goal**: Re-roll for a fresh result; steering notes shape the next synthesis.

**Independent Test**: Synthesize, add a steering note, re-roll; the new result differs and reflects the steer without contradicting fixed traits or the setting.

- [X] T016 [US2] Add a GM steering-notes textarea to `webapp/chargen/templates/index.html` and pass its value as `extra_notes` to the synthesize route; wire re-roll to re-invoke the route. Verify: steer text reaches the backend; re-roll issues a fresh call.
- [X] T017 [P] [US2] Extend `webapp/chargen/test_website_synthesize.py` (or `test_synthesis.py`) to assert `extra_notes` is threaded into `build_prompt` (the GM-steering block appears) and that an empty note is a no-op. Verify: `pytest` passes; coverage 100%.
- [X] T018 [US2] If the steering UI changed layout, re-run `webapp/tests/screenshot.py` + `webapp/tests/dom_audit.py` on the character page (else note covered by T015). Verify: zero DOM-audit issues.

**Checkpoint**: Re-roll + steering work; US1 still works.

---

## Phase 6: Polish & Cleanup (Cross-Cutting)

**Purpose**: Retire the evaluation harness and confirm the project gate.

- [X] T019 With T007 (equivalence) green, delete the entire `webapp/bakeoff/` directory. Verify: directory gone; T007's equivalence test (which imported bakeoff) is removed/retired with it.
- [X] T020 Remove all `bakeoff/*` entries from `webapp/pyproject.toml` (ruff `per-file-ignores`, mypy `overrides`, coverage `omit`) and any other references. Verify: `grep -rn "bakeoff" webapp` returns nothing (outside git history).
- [X] T021 Run the full Python gate from `webapp/`: `make done` (ruff check + ruff format --check + mypy --strict + pytest + `--cov-fail-under=100`). Then a live-Gemini smoke: generate a character → Synthesize Backstory → add a steer → re-roll. Verify: `make done` green; button works end to end.
- [X] T022 [P] Update `webapp/CLAUDE.md` "Current Work" section to reflect the shipped synthesis feature and the removed bakeoff; update the project memory's productionization-TODO note as done. Verify: no dangling bakeoff references in docs.

---

## Dependencies & Execution Order

### Phase dependencies

- **Setup (P1)**: no dependencies.
- **Foundational (P2)**: depends on Setup; BLOCKS US1/US2/US3.
- **US3 (P3 phase)**: depends on Foundational. Sequenced before US1 per the refactor-first directive (no hard code dependency on US1).
- **US1 (P4 phase)**: depends on Foundational (NOT on US3). MVP.
- **US2 (P5 phase)**: depends on US1 (extends the same route/template).
- **Polish (P6)**: T019/T020 depend on T007 passing; T021 depends on all prior; runs last.

### Within stories

- Tests written and failing before implementation (T004 before T005).
- `brief.py` (T005) before the synthesis wiring (T006) and equivalence (T007).
- Route (T012) before its test (T014) and before US2's steering (T016).

### Parallel opportunities

- Setup: T001, T002, T003 are all `[P]`.
- Foundational: T004 `[P]` (test authoring) can begin immediately; T005-T008 are sequential on `brief.py`.
- US3: T010 `[P]` alongside T009.
- US1: T013 `[P]` (template) alongside T012 (route).
- US2: T017 `[P]` (test) alongside T016.
- Polish: T022 `[P]`.

---

## Implementation Strategy

### Refactor-first (the GM's directive)

1. Phase 1 Setup → Phase 2 Foundational: the brief assembles the full corpus in dev, fully tested. **STOP and VALIDATE** the equivalence check (T007).
2. Phase 3 US3: bundle the corpus → the prompt works mount-free. Productionization complete.
3. Phase 4 US1 (MVP): the button. **STOP and VALIDATE** end to end in dev.
4. Phase 5 US2: re-roll + steering.
5. Phase 6 Polish: delete `bakeoff/`, clean pyproject, `make done`, live smoke.

### MVP scope

Foundational + US1 (the button over the full-corpus brief in dev) is the minimum demonstrable product. US3 makes it deployable; US2 makes it pleasant.

---

## Notes

- `[P]` = different files, no incomplete-task dependency.
- Do not delete `bakeoff/` until the equivalence check (T007) is green - it is the reference implementation of the winning assembly.
- Never modify GM SOURCE content; the corpus snapshot is a verbatim read-only copy (Principle V).
- Hyphens only in committed files; the dash guard test enforces it.
- The GM handles all git; do not commit, branch, or push.
