# Tasks: Shrine Builder

- [x] T001 Baseline: `make done` on unmodified code in a detached worktree; record failures.
- [x] T002 `webapp/l7r/shrines/catalog.yaml`: categories, options, descriptions, lines, voids,
      reference flags; header with the pricing why (FR-002, FR-002a, FR-003, FR-004, FR-009).
- [x] T003 `webapp/l7r/shrines/__init__.py`: load + validate catalog, parse design / GM settings,
      price, negotiate, default budget, share query (FR-006, FR-010-FR-015).
- [x] T004 `tests/test_shrines.py`: logic, catalog validation, word guard proven to fire.
- [x] T005 Route + nav + template + CSS + JS (FR-001, FR-005-FR-008, FR-013).
- [x] T006 `tests/test_shrines_routes.py`: player view leaks nothing (SC-002), GM view sums
      (SC-005), link round-trip (SC-003), malformed params.
- [x] T007 `webapp/l7r/shrines/CLAUDE.md`: index, historical grounding, test steps (FR-016);
      add the route to the root CLAUDE.md key-paths line.
- [x] T008 Add the page to `tests/screenshot.py` and `tests/dom_audit.py` PAGES (player and GM).
- [x] T009 Reference artifact: render one design player + GM, read the page.
- [x] T010 Screenshots at four viewports, DOM audit zero issues, `frontend-review`.
- [x] T011 `make done` green; commit; `sync-with-main.sh done`; deploy if the deploy path is
      available.
