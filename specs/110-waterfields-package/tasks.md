# Tasks: waterfields.py -> waterfields/ Package Split

**Input**: Design documents from `/specs/110-waterfields-package/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/package-surface.md, quickstart.md

**Tests**: Included - the spec's FR-003 mandates the guard test (proven to fire), and the whole
feature rides on the byte-identity oracle. All paths below are relative to
`.claude/skills/diagram/` inside the session clone unless stated otherwise.

**Organization**: US1 (behavior-preserving split) is the MVP and carries nearly all the
mechanics; US2 (mega-function decomposition) and US3 (CLAUDE.md index) build on it.

## Phase 1: Setup - baseline capture (MUST precede any code change)

- [x] T001 Census check: re-grep the consumer surface (`from waterfields import`, `import waterfields`, `wf.<attr>`) across the skill tree and record any names beyond the contracts/package-surface.md list (concurrent sessions may have added consumers since 2026-08-16 spec time)
- [x] T002 Capture the pre-split baseline per quickstart.md section 1: copy the skill tree at HEAD to the scratchpad, run every waterfields-consuming gen directly (frozen included - the scratch copy is throwaway), store all produced `pool/*/*.json` manifests + `.svg` under `<scratchpad>/wf-baseline/manifests/`; verify the copy count matches the consumer census and note any gen that fails to run pre-split (a pre-existing failure is excluded from the oracle, recorded in tasks notes)

## Phase 2: Foundational - guard test (blocks all stories)

- [x] T003 Write `test_waterfields_surface.py` (modeled on `test_check_village_surface.py`): pin every censused name from T001, assert each resolves from `waterfields` and is identical (`is`) to the defining submodule's binding once the package exists; include the mechanical re-census (grep the tree, assert every found imported name resolves). Run it now against the MONOLITH - the name-resolution half must PASS (surface exists today) and the submodule-identity half must be written to activate only when `waterfields` is a package, so the test is green pre-split and stays meaningful post-split

## Phase 3: User Story 1 - behavior-preserving package split (P1) - MVP

**Goal**: `waterfields/` package, six modules moved verbatim, derived `__init__`, zero consumer
changes, byte-identical output.

**Independent test**: quickstart.md sections 2-3 - scratch-tree manifest diff empty + `make done`
green with no consumer file modified.

- [x] T004 [US1] Create `waterfields/` and move code VERBATIM (no logic edits, comments/docstrings travel intact per FR-009) from `waterfields.py` into `waterfields/frame.py`, `waterfields/palette.py`, `waterfields/banks.py`, `waterfields/comb.py`, `waterfields/carve.py`, `waterfields/polder.py` per the data-model.md layout; each module gets a short docstring naming its concern + the module-level imports it needs (`math`, `random`, typing, and cross-module imports per the DAG: comb -> carve/banks/frame/palette, polder -> banks/frame/palette, carve -> frame/banks, banks -> frame); the monolith's head docstring (THE INVERSION / ENGINE / SLOPE IS A KNOB) moves to `waterfields/__init__.py`'s docstring
- [x] T005 [US1] Write `waterfields/__init__.py`: the moved head docstring + six `from .<module> import *` lines (leaf-first: frame, palette, banks, carve, comb, polder) + aliased explicit block for the censused underscore names (`from .palette import _RICE_GREEN as _RICE_GREEN`, `from .frame import _Frame as _Frame, _miter_normals as _miter_normals`, plus any T001 additions); NO `__all__`, no logic; then DELETE `waterfields.py` in the same change so a stale monolith can never shadow the package
- [x] T006 [US1] Update `pyproject.toml`: mypy `files` entry `"waterfields.py"` -> `"waterfields"`; add `"waterfields/__init__.py" = ["F401", "F403"]` to ruff per-file-ignores with the check_village-style why-comment
- [x] T007 [US1] Guard-test TDD proof: temporarily comment out one star import in `waterfields/__init__.py`, run `python3 -m pytest test_waterfields_surface.py` and confirm it FAILS naming the missing surface; restore, confirm green (record the red run in the task note - a guard never proven to fire is the failure mode the project's check-first rule exists for)
- [x] T008 [US1] Post-move byte-identity: quickstart.md section 2 - fresh scratch copy of the working tree, run the same gen sweep as T002, `diff -r` manifests against the baseline; MUST be empty before proceeding
- [x] T009 [US1] Run the full gate from the clone (`make done`, backgrounded, log tailed - never wrapped with a trailing echo): ruff + format + mypy --strict + full pytest incl. `test_villages.py` scripted-map sweep and the regression corpus; fix anything it lists together, re-run once
- [x] T010 [US1] Verify SC-002 (zero consumer changes): `git status`/`git diff --stat` shows changes ONLY in `waterfields/` (new), `waterfields.py` (deleted), `pyproject.toml`, `test_waterfields_surface.py`, and specs/; commit the move as its own commit (bisectable point)

## Phase 4: User Story 2 - mega-function decomposition (P2)

**Goal**: `build_comb`, `_carve`, `build_polder` each decomposed into named sequential stage
functions, <= ~150 lines each, state passed explicitly, byte-identity after EACH function.

**Independent test**: quickstart.md section 4 (AST length check) + empty manifest diff per pass.

- [x] T011 [US2] Decompose `_carve` in `waterfields/carve.py` into named stage functions (research.md R5 method: mechanical extraction, code order + RNG draw order + float-op order preserved exactly, parameters in / values out, no shared mutable module state); re-run the T008 byte-identity sweep - MUST be empty; commit
- [x] T012 [US2] Decompose `build_comb` in `waterfields/comb.py` the same way (its pipeline stages become the extracted names); byte-identity sweep empty; commit
- [x] T013 [US2] Decompose `build_polder` in `waterfields/polder.py` the same way; byte-identity sweep empty; commit
- [x] T014 [US2] Function-scale verification: run the quickstart section-4 AST check over `waterfields/*.py`; any function still > ~150 lines is either further split or carries an inline one-line justification (genuinely atomic stage); re-run `make done` (shared code changed -> full sweep is mandatory)

## Phase 5: User Story 3 - the package index (P3)

**Goal**: `waterfields/CLAUDE.md` in the check_village "look here when" style; skill docs point
at the package.

- [x] T015 [P] [US3] Write `waterfields/CLAUDE.md`: header stating the split provenance (feature 110, clause 13/14, the 027 re-export mechanism + guard test name), the "load only the file the task calls for" doctrine, and a "look here when" table covering `__init__.py`, `frame.py`, `palette.py`, `banks.py`, `comb.py`, `carve.py`, `polder.py` - each row naming its key functions/constants; include the decomposed stage-function naming convention
- [x] T016 [P] [US3] Update `.claude/skills/diagram/CLAUDE.md`: the LIVE-engine line's `waterfields.py` mention becomes the `waterfields/` package (pointer to its CLAUDE.md); grep the skill's other auto-loading docs (`SKILL.md`, `settlements.md`, `hamletgen.md`) for `waterfields.py` FILE-path references and update them (prose references to importable paths like `waterfields._bund_beans` stay; old `specs/NNN` artifacts stay verbatim per research.md R6)

## Phase 6: Polish & close-out

- [x] T017 Final full verification: `make done` backgrounded from the clone (docs-only diffs since the last green gate may skip it per the docs-only rule - re-run only if T015/T016 landed after any code change); confirm every SC: manifests identical (SC-001), consumer diff scope (SC-002), file/function sizes (SC-003), index maps concerns to files (SC-004), suite + gate + corpus green (SC-005)
- [x] T018 Mark tasks complete, update this file's checkboxes, commit; stop-work ritual: `scripts/sync-with-main.sh done` from the clone (locked pull+push + render-sync); report the outcome to the GM with concrete verify steps

## Dependencies

- T001 -> T002 -> T003 -> US1 (T004-T010, sequential) -> US2 (T011 -> T012 -> T013 -> T014) -> US3 (T015, T016 parallel) -> T017 -> T018
- US2 strictly after US1's commit (the move must be a clean bisect point before any decomposition).
- US3 can start after US1 but T015's stage-function rows want US2 done; run it last for one pass.

## Parallel opportunities

- T015 and T016 are [P] - different files, no ordering between them.
- The per-map gen runs inside T002/T008 sweeps fan out naturally (independent processes).
- Everything else is deliberately serial: each step's oracle depends on the previous commit.

## Implementation strategy

MVP = US1 alone (a green, byte-identical package split with zero consumer changes is shippable
by itself). US2 lands one function per commit so any drift bisects to a single extraction.
US3 is a docs pass. Estimated: US1 is the bulk; US2 is three careful mechanical passes; US3 is
minutes.
