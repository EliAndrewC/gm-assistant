# Implementation Plan: Interrogation rolls grouped by line of questioning

**Feature**: `206-interrogation-lines` (no branch - `SPECIFY_FEATURE` exported, per CLAUDE.md) |
**Date**: 2026-09-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/206-interrogation-lines/spec.md`; the GM's request
verbatim in [gm-request.md](gm-request.md).

## Summary

An interrogation roll is never written against the GM's Sincerity roll (the margin would tell the
players whether the NPC was truthful). It is written exactly as rolled with the interrogator's
rank attached, and rolls on one line of questioning share one written line:
`interrogation (grilling): 37@2 Jimen / 24@1 Moriko - what Fumitake ordered his escorts to do`.
The change is confined to the `l7r.repl.rolls` package: two fields on `Roll`, one new renderer
and a grouping pass in `rules.py`, and an interrogation branch in the `annotate()` menu that
replaces the open/contested/discard/open-with-bonus prompt for that one skill. Lines of
questioning are DERIVED from the rolls rather than stored as a second structure, so the menu's
stage-then-commit and Ctrl-C-discards-all semantics carry over unchanged.

## Technical Context

**Language/Version**: Python 3.14 (the pin in `docs/container.md`)

**Primary Dependencies**: none new. Standard library only; the package already depends on nothing
outside the repository for this path.

**Storage**: none new. The rolls live on the open `Conversation` in memory and are written as
Textile lines into the NPC's Obsidian Portal bio by the existing `bio.rewrite` path.

**Testing**: pytest with `-n auto`, `tests/test_rolls_*.py` alongside the package; 100% line
coverage on `l7r` is the gate (`make done` from `webapp/`).

**Target Platform**: the GM's REPL (`scripts/repl.py`) inside the container, Linux.

**Project Type**: library + interactive prompt (the `annotate()` menu drives `input()`).

**Performance Goals**: not applicable - a conversation holds tens of rolls at most.

**Constraints**: mypy --strict; ruff; no `print` outside the REPL's exempt path (`l7r/repl/**` is
T20-exempt because printing IS the interface); hyphens only, American spellings; the menu's
answers go through `ask_quietly` (feature of 2026-09-09) so they stay out of readline history.

**Scale/Scope**: three source files (`models.py`, `rules.py`, `annotate.py`), their tests, and the
package `CLAUDE.md`. `test_rolls_annotate.py` is at 565 lines and `rules.py` at 438; neither
approaches the ~1,000-line question after this feature (estimate: +150 and +80).

**Single-artifact target** (constitution VI): ONE reference test module,
`tests/test_rolls_interrogation.py`, holding the GM's two example lines as the first tests -
`interrogation (grilling): 37@2 Jimen / 24@1 Moriko - what Fumitake ordered his escorts to do` and
`interrogation: 25@2 Jimen - what Fumitake thinks of Tsuruchi`. Every renderer and menu change is
proven there first. The sweep is the whole `tests/` directory under `make done`, run exactly once
at the end.

**Every step is two steps.** Each phase below names the reference artifact step and the sweep step
separately; see Phase 2 in tasks.md.

## Constitution Check

- **I. Accessibility-First Viewports**: N/A - no UI; the surface is a terminal prompt.
- **II. Bold, Intentional Design**: N/A - no UI.
- **III. Pool Data Conventions**: N/A - no pool content.
- **IV. One Canonical Home for GM Source**: N/A - no SOURCE blocks added or moved. The GM's
  request is quoted in `gm-request.md`, which is a spec artifact, not a SOURCE block.
- **V. Protecting the GM's Writing**: PASS - nothing inside SOURCE markers is touched.
- **VI. Verify Before Reporting Done**: PASS - each task runs its test module; the final task
  runs `make done` (ruff, format, mypy --strict, hook-guard suites, pytest, 100% coverage) and
  then the REPL hand-check in `quickstart.md`.
- **VII. De-Localized Generation by Default**: N/A - nothing generated; the names in tests are
  the GM's own campaign PCs, which is the existing convention in `tests/test_rolls_*.py`.
- **VIII. Direct Voice Over Framing Distance**: N/A - no in-world prose.
- **IX. Setting Integration**: PASS - the only setting fact used is the rules text for
  Interrogation (`rules/02-skills.md`), cited in the spec and in `rules.py`.
- **X. Python Discipline**: PASS - ruff + format + mypy --strict + pytest at 100% on `l7r`; TDD
  red-green on the reference module (the two example lines fail before the renderer exists);
  no new dependencies; no config values (the skill name `interrogation` is a rules fact, held as
  a module constant beside `EXEMPT_FROM_ANNOTATION` and `CONTESTED_PAIRS` where the other
  skill-keyed rules live). Functions and files stay at human scale (see Scale/Scope).
- **XI. Japanese Authenticity**: N/A - no kanji or names generated.
- **XII. Historical Grounding Bookends**: N/A - the feature asserts nothing about the world; it
  records dice. The one grounding is the RULES text, opened in `research.md` R1.
- **XIII. No Known Regressions**: PASS - baseline taken 2026-09-10 on unmodified `HEAD`
  (`f2a0c885`) in a detached worktree with main's gitignored secrets and cache copied in:
  `pytest -q -n auto tests/` -> **1248 passed, 0 failed**. The merge bar is zero new failures;
  every existing `test_rolls_*` assertion about non-interrogation lines must still pass unchanged.
- **XIV. Fix Defects Where You Find Them**: acknowledged - anything found in the rolls package
  during this work is fixed in this feature with its own test.
- **XVI. Fidelity**: the spec was handed with the GM's verbatim request to the `spec-fidelity`
  agent before implementation; verdict recorded in `spec.md` (the review gate reads it at push).

No gate is DEFERRED; Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/206-interrogation-lines/
├── gm-request.md        # the GM's words, verbatim, plus the accepted judgment calls
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0: the decisions and their alternatives
├── data-model.md        # Phase 1: Roll's two new fields; the derived line of questioning
├── quickstart.md        # Phase 1: how to drive it at the REPL and what to expect
├── checklists/requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks)
```

No `contracts/`: the feature has no external interface. The written line's shape is the contract
and it is pinned by the reference test module.

### Source Code (repository root)

```text
webapp/l7r/repl/rolls/
├── models.py        # Roll: + line (int | None), + grilling (bool)
├── rules.py         # + INTERROGATION, is_interrogation(), render_interrogation();
│                    #   render_lines groups interrogation rolls by line
├── annotate.py      # Decision: + line, grilling, rank; _interrogate() branch in annotate()
└── CLAUDE.md        # the written-line catalog gains the interrogation line and its why

webapp/tests/
├── test_rolls_interrogation.py   # NEW - the reference module (renderer + menu + write path)
├── test_rolls_annotate.py        # unchanged assertions; one test that o/c/d/ob is NOT offered
│                                 #   for interrogation lives in the new module instead
└── test_rolls_rules.py           # unchanged
```

**Structure Decision**: everything stays in the existing package; the new behavior is one branch
in the menu and one renderer, which is the shape feature 202 already has for contested rolls. A
new test module rather than growing `test_rolls_annotate.py` past ~700 lines, and because the
feature's tests read as one story (the leak, the line, the rank, the menu).

## Phase 0 - Research

See [research.md](research.md). No NEEDS CLARIFICATION remained after the spec review; the
research records five design decisions with the alternatives priced.

## Phase 1 - Design

See [data-model.md](data-model.md) and [quickstart.md](quickstart.md). Agent context: this
repository deliberately tracks no "active plan" pointer in `CLAUDE.md` (no `SPECKIT` markers
exist; CLAUDE.md says to read the highest-numbered `specs/` directory instead), so no context
update is made.

## Phase 2 - Tasks

Produced by `/speckit-tasks` into `tasks.md`. Ordering constraint worth stating here: the
renderer (`rules.py`) lands before the menu (`annotate.py`), because the menu prints the staged
line through the renderer; and `models.py` before both.

## Constitution Check - post-design

Re-evaluated after Phase 1: unchanged. The design adds two fields and one renderer; no gate moved.
