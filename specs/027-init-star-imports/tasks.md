# Tasks: Collapse check_village/__init__.py to a star-import surface

**Input**: Design documents from `specs/027-init-star-imports/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md (all present)

**Tests**: Test tasks ARE included - the spec's FR-005 and the project's check-before-fix rule require the guard/surface test to exist and fire BEFORE the rewrite.

**Organization**: All paths relative to `.claude/skills/diagram/` unless repo-anchored. User stories from spec.md: US1 = cheap-to-load surface (P1), US2 = consumers unchanged (P1), US3 = shadowing guard (P2). Because the feature is one file, US2 and US3's test work is sequenced FIRST (it pins the behavior US1's rewrite must preserve) - the stories remain independently verifiable, but execution interleaves by necessity.

## Phase 1: Setup

- [x] T001 Re-run the consumed-surface census against the current clone tip (greps for `check_village\.<attr>`, `from check_village import`, aliased imports, `getattr`) and record the final name list + each name's providing module in `specs/027-init-star-imports/census.md`. Verify the six underscore names and identify which consumed names are NOT public module-level names of the 15 star-import submodules (these need the aliased explicit block; expect the `settlement`/`waterfields` geometry helpers).

## Phase 2: Foundational (check-before-fix - tests land against the CURRENT file)

- [x] T002 [US3] Write `test_check_village_surface.py` (skill dir, alongside the other root-level test files) with (a) the clash guard: no public name bound to different objects across the 15 submodules, failure message names the name + both modules; (b) the surface pin: every census name resolves via `check_village.<name>`; each underscore name `is` its defining module's attribute. Run it against the CURRENT monolithic `__init__` - it must pass (proves the pin is compatible with today's surface).
- [x] T003 [US3] Demonstrate the clash guard FIRES: inject a synthetic clash (monkeypatched module pair or a temp module in the test itself, not a repo file), observe the failure message, keep that scenario as a permanent test case (`test_guard_fires_on_synthetic_clash`). Check-before-fix satisfied: the guard has proven teeth before the rewrite relies on it.

## Phase 3: User Story 1 - the rewrite (US1 cheap surface + US2 consumers unchanged)

- [x] T004 [US1] Rewrite `check_village/__init__.py`: docstring (updated - keep the WHY pointer paragraphs, describe the star-import mechanism, record why `__all__` is gone per research.md R1), star imports for the 15 submodules in data-model.md order, aliased explicit block for the six underscore names + census-determined external names from `settlement`/`waterfields`, DELETE the `__all__` roster and all `_seg_*` re-exports. Target ≤150 lines.
- [x] T005 [US1] Update `pyproject.toml` per-file-ignores for `check_village/__init__.py` from `["F401"]` to `["F401", "F403"]` with a one-line why-comment (star imports ARE the re-export mechanism, feature 027).
- [x] T006 [US2] Run the fast local loop: `pytest test_check_village_surface.py -n auto` then `python3 -m mypy` then `ruff check check_village/__init__.py pyproject.toml` - fix forward until green. (Full suite waits for T008; iterate on the one motivating artifact.)

## Phase 4: Polish & documentation

- [x] T007 [P] Update `check_village/CLAUDE.md`'s index entry for `__init__.py` (it currently describes the verbatim-restore roster; describe the star-import surface, the aliased block, and point at `specs/027-init-star-imports/` + the guard test). Cross-check `.claude/skills/diagram/CLAUDE.md` for any stale mention of the 3,148-line `__init__`.
- [x] T008 Run the full gate: `make done > /tmp/.../gate.log 2>&1` backgrounded, bare (no trailing echo - exit codes lie if wrapped), act on the completion notification, tail the log before believing green. Whole affected test files, no `-k`.
- [x] T009 Mark tasks complete, update `spec.md` Status to Implemented, commit, run `scripts/sync-with-main.sh done` (stop-work ritual; render-sync expected to restamp Mode B maps since `check_village` is engine-adjacent - verify it short-circuits or completes cleanly).

## Dependencies

- T001 → T002 (census feeds the pin list) → T003 → T004 → T005 → T006 → T008 → T009; T007 parallel with T004-T006 after T003.

## Implementation strategy

Single increment - the file IS the feature. MVP = T001-T006 (surface rewritten, locally green); T007-T009 are the project's mandatory polish/ritual, not optional extras.
