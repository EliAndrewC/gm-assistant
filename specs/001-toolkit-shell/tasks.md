---
description: "Task list for L7R Toolkit Phase 1 implementation"
---

# Tasks: L7R Toolkit Phase 1 - App Shell + Chargen + Relics

**Input**: Design documents in `/gm-assistant/specs/001-toolkit-shell/`

**Prerequisites**: ✅ plan.md, ✅ spec.md, ✅ research.md, ✅ data-model.md, ✅ contracts/

**Tests**: Per Principle X (NON-NEGOTIABLE), tests are MANDATORY for new code in the `l7r/` package. TDD red-green order: test first, watch it fail, implement.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other [P] tasks (different files, no shared deps)
- **[Story]**: US1 = Relics, US2 = Chargen integration, US3 = Landing/nav shell, FOUND = Foundational

---

## Phase 1: Setup (Shared Infrastructure)

- [x] **T001** [FOUND] pyproject.toml with ruff + mypy + pytest + cov config (already done in Phase 0)
- [x] **T002** [FOUND] Makefile with `done` target wiring lint + format + types + tests + cov (already done in Phase 0)
- [x] **T003** [FOUND] requirements.in lists pyyaml and dev deps (already done in Phase 0)
- [ ] **T004** [FOUND] Create `l7r/__init__.py` (empty package marker)
- [ ] **T005** [FOUND] Create `tests/__init__.py`, `tests/conftest.py`, `tests/fixtures/pool_sample/` with 4-5 fixture relics spanning multiple Fortunes and clans

---

## Phase 2: Foundational (blocking - must come before any user story implementation)

- [ ] **T010** [FOUND] **TEST** `tests/test_pool.py` - write failing tests for `pool.load_relics`, `pool.Relic` dataclass, frontmatter parsing, missing-field handling
- [ ] **T011** [FOUND] **IMPL** `l7r/pool.py` - `Relic` frozen dataclass + `load_relics(pool_dir: Path) -> list[Relic]` that walks `<pool_dir>/<fortune>/*.md`, parses frontmatter via pyyaml, skips files with missing required fields (logs warning), returns sorted list. Make T010 tests pass.
- [ ] **T012** [FOUND] **TEST** `tests/test_sections.py` - write failing tests for `SECTIONS` registry shape, ordering, enabled-flag behavior, `find_section_by_slug`
- [ ] **T013** [FOUND] **IMPL** `l7r/sections.py` - `Section` dataclass + `SECTIONS` tuple + `find_section_by_slug(slug)`. Make T012 tests pass.
- [ ] **T014** [FOUND] **TEST** `tests/test_slugs.py` - write failing tests for `find_relic_by_slug`, `relics_for_fortune`, `neighbors_in_fortune` (wraparound at ends; only one item; missing slug)
- [ ] **T015** [FOUND] **IMPL** `l7r/slugs.py` - slug lookup helpers. Make T014 tests pass.
- [ ] **T016** [FOUND] **IMPL** `l7r/jinja_env.py` - shared Jinja2 environment with ChoiceLoader (l7r templates first, chargen templates second), filters for `description_html` (paragraphs + `*em*`) and `relic_type_short`

---

## Phase 3: User Story 1 - Relics Catalog (P1)

**Goal**: Browse /relics and /relics/<slug> with the prototype's look and feel.

- [ ] **T100** [US1] **STATIC** Port `/gm-assistant/webapp-prototype/relics/styles.css` to `l7r/static/css/l7r.css`. Strip prototype-only selectors not used by the live app; add app-shell rules (`.app-shell`, `.app-nav-main`, `.app-footer`); keep the design system intact.
- [ ] **T101** [US1] **STATIC** Write `l7r/static/js/l7r.js` for seal-filter behavior (port from prototype's `main.js` filter handling; remove the bundle-loading code since data is server-rendered now).
- [ ] **T102** [US1] **TEMPLATE** Create `l7r/templates/_layout.html` - base shell with nav, footer, font links, shared shell markup.
- [ ] **T103** [US1] **TEMPLATE** Create `l7r/templates/relics_index.html` - extends `_layout.html`; renders per-Fortune sections with the seal filter rail and card grid. Uses fortune list, clan label registry.
- [ ] **T104** [US1] **TEMPLATE** Create `l7r/templates/relic_detail.html` - extends `_layout.html`; hero kanji, romaji, name, meta band (Fortune/Clan/Type/Resides-at/Tied-to), prose, prev/next.
- [ ] **T105** [US1] **TEMPLATE** Create `l7r/templates/_404.html` - extends `_layout.html`; clean 404 message in the shell.
- [ ] **T110** [US1] **TEST** `tests/test_app.py::test_relics_index_lists_all_relics` - integration test: GET /relics returns 200 with 42 cards, 7 fortune sections.
- [ ] **T111** [US1] **TEST** `tests/test_app.py::test_relic_detail_renders` - integration: GET /relics/<known-slug> returns 200 with kanji and name in body.
- [ ] **T112** [US1] **TEST** `tests/test_app.py::test_relic_detail_404` - integration: GET /relics/unknown-slug returns 404 with `_404.html` body.
- [ ] **T113** [US1] **IMPL** `l7r/app.py::Root.relics` - CherryPy handler for both `/relics` and `/relics/<slug>`. Make T110/T111/T112 pass.

---

## Phase 4: User Story 2 - Chargen Integration (P2)

**Goal**: Chargen UI inside the new shell, functional behavior preserved.

- [ ] **T200** [US2] **EDIT** Update `chargen/templates/index.html` to extend `l7r/templates/_layout.html` (replaces its own `<html>...<body>` chrome with `{% extends "_layout.html" %}` and a content block). The chargen-specific form, CSS classes, and inline JS for char generation stay inside the content block.
- [ ] **T201** [US2] **EDIT** Update chargen's JS within `chargen/templates/index.html` to call `/chargen/generate` and `/chargen/upload` (instead of `/generate` and `/upload`).
- [ ] **T202** [US2] **EDIT** Update `chargen/website.py` `Root` class - no behavior change, but document that it's now mounted at `/chargen` rather than `/`.
- [ ] **T210** [US2] **TEST** `tests/test_app.py::test_chargen_route_returns_html` - GET /chargen returns 200 with chargen-specific form-field IDs in body.
- [ ] **T211** [US2] **IMPL** Wire chargen `Root` into the CherryPy tree at `/chargen` in the app entry point.

---

## Phase 5: User Story 3 - Landing + Nav Shell (P3)

**Goal**: Coherent landing page and consistent nav across all sections.

- [ ] **T300** [US3] **TEMPLATE** Create `l7r/templates/landing.html` - extends `_layout.html`; toolkit name, one-paragraph description, section cards/links.
- [ ] **T301** [US3] **TEMPLATE** Create `l7r/templates/names_placeholder.html` - extends `_layout.html`; "coming soon" message.
- [ ] **T310** [US3] **TEST** `tests/test_app.py::test_landing_returns_html` - GET / returns 200 with toolkit name in body.
- [ ] **T311** [US3] **TEST** `tests/test_app.py::test_names_placeholder_returns_html` - GET /names returns 200 with placeholder copy.
- [ ] **T312** [US3] **TEST** `tests/test_app.py::test_nav_has_all_sections` - every shell-rendered page contains nav links for all enabled+placeholder sections.
- [ ] **T313** [US3] **IMPL** `l7r/app.py::Root.index` + `Root.names` - make T310/T311/T312 pass.

---

## Phase 6: Entry-point wiring and static-asset serving

- [ ] **T400** [FOUND] **IMPL** Create `l7r/app.py` entry point: build pool, build root, mount root at `/`, mount chargen at `/chargen`, register staticdir for `/static`, register 404 error page handler.
- [ ] **T401** [FOUND] **IMPL** Update `chargen/__init__.py` (or replace as the import target) so `cherryd --import l7r` boots the l7r app. (Decision: add new top-level entry `l7r/__init__.py` that triggers the wiring; chargen's `__init__.py` stops auto-mounting.)
- [ ] **T402** [FOUND] **VERIFY** Run `make serve`, hit `http://127.0.0.1:8080/` and the 4 main routes; manually confirm pages render.

---

## Phase 7: UI verification (Constitution Principle I & VI)

- [ ] **T500** [FOUND] **TOOL** Create `tests/screenshot.py` adapted from the prototype's `screenshot.py` - covers GET /, /relics, /relics/<sample-slug>, /chargen, /names at GM-100, GM-200, tablet, mobile viewports.
- [ ] **T501** [FOUND] **TOOL** Create `tests/dom_audit.py` for the overflow audit at the four viewports (port from the prototype's Python inspection helpers).
- [ ] **T510** [FOUND] **VERIFY** Run `python3 tests/screenshot.py` and review output. Fix any clipping / truncation issues found.
- [ ] **T511** [FOUND] **VERIFY** Run `python3 tests/dom_audit.py` and confirm zero overflows at all four viewports.

---

## Phase 8: Final "done" check

- [ ] **T600** [FOUND] **VERIFY** `make done` exits clean (ruff check + ruff format --check + mypy --strict + pytest + 100% coverage on `l7r/`).
- [ ] **T601** [FOUND] **DOC** Update `/gm-assistant/CLAUDE.md` if needed to reflect any new paths/conventions introduced.

---

## Parallel execution opportunities

Tasks marked `[P]` (not used above - every task has a clear ordering) can in principle run in parallel. In this plan, the natural parallelism is:

- **T100, T101** (CSS + JS): parallel-safe, different files.
- **T102, T103, T104, T105, T300, T301** (templates): parallel after T102 (`_layout.html`); each per-page template is independent.
- **T011, T013, T015, T016** (FOUND impls): must each follow their test counterpart (T010, T012, T014); among themselves, parallel-safe.

Subagent dispatch can be used for the template family (T102-T105, T300-T301) once the layout is settled.

---

## Verification matrix

| User story | Independent test | Acceptance check |
|------------|------------------|------------------|
| US1 Relics | T110, T111, T112 (HTTP), T510 (screenshots) | All 42 relics render, filter works, detail page renders, 404 handled |
| US2 Chargen | T210 (HTTP), manual smoke test | /chargen renders inside shell, generate + upload still work |
| US3 Shell | T310, T311, T312 (HTTP), T510 (screenshots) | / renders, /names renders, nav consistent across all pages |

## Constitution gate at end

Per Principle VI, before marking Phase 1 complete:
- [ ] `make done` exits 0
- [ ] Screenshot audit clean at all 4 viewports
- [ ] DOM overflow audit reports 0 overflows
- [ ] Manual smoke test: chargen generate + upload flow works end-to-end
