---
description: "Task list for the Dreams Section (Webapp) feature"
---

# Tasks: Dreams Section (Webapp)

**Input**: Design documents from `specs/011-dreams-section/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/routes.md

**Tests**: INCLUDED - Constitution Principle X (NON-NEGOTIABLE) requires red-green TDD for the new loader, and Principle I requires the screenshot + DOM-audit verification for the UI.

**Organization**: grouped by user story (P1 → P3), preceded by shared setup and the foundational loader that every story depends on.

## Format: `[ID] [P?] [Story?] Description with file path`

- **[P]**: parallelizable (different files, no dependency on an incomplete task)
- **[Story]**: US1 / US2 / US3 (user-story phases only)

## Path Conventions

Web app; all paths are under `webapp/` (the `l7r/` package and `tests/`), plus the public pool at `.claude/skills/dream/pool/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: deploy-bundling so the public pool (and only the public pool) reaches the running app.

- [x] T001 [P] Extend `prepare-deploy` in `webapp/Makefile` to sync the PUBLIC dream pool into the build context: create `skills/dream/` and `cp -r ../.claude/skills/dream/pool skills/dream/pool` (copy `pool` ONLY, never `pool-local`); confirm the `clean` target still removes `skills`.
- [x] T002 [P] Mirror the relic pool's deploy wiring for dreams: in `webapp/Dockerfile` (and `fly.toml` runtime env) ship `skills/dream/pool` and set `L7R_DREAM_POOL_DIR` to the bundled path, exactly as `L7R_RELIC_POOL_DIR` is wired.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: the scene loader every page depends on. MUST complete before any user story. TDD (red before green).

- [x] T003 [P] Create loader fixtures under `webapp/tests/fixtures/dream_pool/`: (a) `pool/` with one valid scene file, (b) a malformed file in `pool/` (missing a required field and one with no frontmatter), (c) a sibling `pool-local/` containing a decoy scene (to prove it is never read).
- [x] T004 Write FAILING loader tests in `webapp/tests/test_dreams.py` (red): loads the valid scene; skips malformed files with a logged warning (INV-2); sorts scenes by title; renders the markdown body to HTML; and INV-1 - given a pool dir with a sibling `pool-local/`, the loader returns ONLY the public scene and never the decoy. Behavior-named, parametrized where natural.
- [x] T005 Implement `webapp/l7r/dreams.py` to green: `DreamScene` frozen dataclass (per data-model.md), `load_dream_scenes(pool_dir)` mirroring `l7r/pool.py` (frontmatter split, required-field skip-with-warning, title sort, slug from stem), and a module-level `markdown-it-py` renderer (CommonMark + tables, raw-HTML disabled) producing `body_html`. Must reach 100% line coverage; no swallowed exceptions; no `print`.
- [x] T006 Wire the pool into the app in `webapp/l7r/app.py`: add `_resolve_default_dream_pool_dir()` (env `L7R_DREAM_POOL_DIR`, else dev default `.claude/skills/dream/pool`), load scenes in `make_app()`, store them on `Root`, and render `content/dreams_framework.md` to HTML once at startup.

**Checkpoint**: `pytest tests/test_dreams.py --cov=l7r/dreams --cov-fail-under=100` green; scenes load in a REPL from the real public pool.

---

## Phase 3: User Story 1 - Learn the framework and read a worked example (P1) 🎯 MVP

**Goal**: `/dreams` shows the player-facing framework + the example, and `/dreams/<slug>` renders the full scene.

**Independent test**: load `/dreams`, read the framework, follow the example link, and confirm the full Daikoku scene renders (question, divine direction, how-to-run, shared bands, four tables, the 10 menu, design notes).

- [x] T007 [P] [US1] Author `webapp/l7r/content/dreams_framework.md` - hand-written player-facing rules & framework: the theology (constant sending, poor receiver, expected noise/silence), attunement/circumstances, and the mechanic (1k1 roll; no-dream/noise/meaningful bands; the always-significant 10 + lucid point pool; rerolls). OMIT authoring internals (pool tiers, fragment-writing, spoiler handling). Hyphens only; no em/en dashes.
- [x] T008 [US1] Add the `dreams(self, slug=None)` route to `Root` in `webapp/l7r/app.py`: `slug is None` renders `dreams_index.html` (framework HTML + `scenes`); otherwise look up by slug and render `dream_detail.html`, or `_render_404()` on miss (FR-009). `current_section='dreams'`.
- [x] T009 [P] [US1] Create `webapp/l7r/templates/dreams_index.html` (extends `_layout.html`): the rendered framework block, then the examples list.
- [x] T010 [P] [US1] Create `webapp/l7r/templates/dream_detail.html` (extends `_layout.html`): scene title, sender, and the rendered `body_html`, with prev/back navigation to `/dreams`.
- [x] T011 [US1] Add Dreams styles to `webapp/l7r/static/css/l7r.css` using EXISTING tokens only (Fraunces/EB Garamond/Shippori Mincho, existing color vars): framework prose block, scene section rhythm, and fragment tables - wide tables MUST scroll inside their own `overflow-x:auto` container so the page body never scrolls horizontally.
- [x] T012 [US1] Verify US1 (Principle I): run `webapp/tests/screenshot.py` and `webapp/tests/dom_audit.py` for `/dreams` and `/dreams/daikoku-masamune-sword-akishi`; zero DOM-audit issues at GM-100/GM-200/tablet/mobile; examine a GM-200 contact sheet from the player's perspective.

**Checkpoint**: US1 is a shippable MVP - the section works even before nav polish.

---

## Phase 4: User Story 2 - Discover Dreams from the site and browse the gallery (P2)

**Goal**: Dreams is in the nav and the gallery cards are legible and consistent with Relics.

**Independent test**: from any page, "Dreams" is in the primary nav; clicking it shows the examples list with title + descriptor per scene, each linking to its page (nav → /dreams → scene ≤ 2 clicks).

- [x] T013 [US2] Add `Section(slug='dreams', label='Dreams', path='/dreams', enabled=True)` to `webapp/l7r/sections.py` (after `places`).
- [x] T014 [P] [US2] Style the examples gallery cards in `webapp/l7r/templates/dreams_index.html` (title, sender, summary descriptor, link) to match the Relics catalog card treatment.
- [x] T015 [US2] Verify US2: confirm "Dreams" renders in the nav on every page and the ≤2-click path holds; re-run `dom_audit.py` across all pages (the nav change touches every page).

---

## Phase 5: User Story 3 - The gallery grows data-driven (P3)

**Goal**: adding a public scene file makes it appear with no code change.

**Independent test**: add a second valid scene to the pool, reload, and confirm it appears in the gallery and is viewable.

- [x] T016 [US3] Add a regression test in `webapp/tests/test_dreams.py` (INV-3): dropping a new valid scene file into the pool dir makes `load_dream_scenes()` include it and resolve it by slug with no code change, and the result stays deterministically title-sorted.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T017 Run `make done` in `webapp/` (ruff check + ruff format --check + mypy --strict + pytest + `--cov-fail-under=100`); all green.
- [x] T018 Full-site Principle I regression: `webapp/tests/screenshot.py` + `webapp/tests/dom_audit.py` across ALL pages × 4 viewports (zero issues), then invoke the `frontend-review` subagent for an independent pass on `/dreams` and `/dreams/<slug>` (author != reviewer).
- [x] T019 [P] Spoiler smoke check (FR-007 / SC-004): with the app running, confirm no `pool-local` scene (e.g. `ebisu-dreams-shiro-reiji`) is listed on `/dreams`, and `/dreams/ebisu-dreams-shiro-reiji` returns 404.
- [x] T020 [P] Docs: add `/dreams` and `/dreams/<slug>` to the Routes list in `webapp/CLAUDE.md` (and the main `CLAUDE.md` Key paths), and confirm `make prepare-deploy` produces `webapp/skills/dream/pool` but no `pool-local`.

---

## Dependencies & Execution Order

- **Setup (T001-T002)**: independent of code; can run anytime, parallel to each other.
- **Foundational (T003-T006)**: T003 → T004 → T005 → T006 (TDD chain). Blocks ALL user stories.
- **US1 (T007-T012)**: needs Foundational. T007/T009/T010 are parallel; T008 needs T006 + the templates; T011 needs the templates; T012 needs T007-T011. **US1 alone is the MVP.**
- **US2 (T013-T015)**: needs US1 pages to exist. T013/T014 parallel-ish; T015 after both.
- **US3 (T016)**: needs Foundational only (independent of US1/US2 UI).
- **Polish (T017-T020)**: after the stories in scope. T019/T020 parallel.

## Parallel Opportunities

- Setup: `T001` ∥ `T002`.
- Foundational fixtures: `T003` while reviewing the plan.
- US1: `T007` (framework prose) ∥ `T009` ∥ `T010` (both templates) - different files.
- Polish: `T019` ∥ `T020`.

## Implementation Strategy

- **MVP = User Story 1** (T001-T012): a working, verified `/dreams` landing + `/dreams/<slug>` detail rendering the Daikoku example, even before the nav entry. Ship-able on its own.
- **Increment 2 = US2** (nav + gallery polish) makes it discoverable.
- **Increment 3 = US3** (the data-driven-growth regression) locks in the "add a file, it appears" property.
- The spoiler boundary (FR-007) is exercised in Foundational (INV-1 test, T004) and re-confirmed in Polish (T019) - it is never deferred.
