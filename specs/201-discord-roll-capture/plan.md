# Implementation Plan: Discord roll capture into Obsidian Portal

**Feature**: `specs/201-discord-roll-capture` | **Date**: 2026-08-28 | **Spec**: [spec.md](spec.md)

**Status**: spec is FAITHFUL after two rounds of independent `spec-fidelity` review (see the spec's
Review history). Evidence base is [research.md](research.md), findings R1-R10.

## Technical Context

**Language**: Python 3.14 (the container pin) | **Style**: ruff + `ruff format` + `mypy --strict`
**Testing**: pytest with `-n auto`; 100% line coverage on pure logic (Principle X)
**Home**: a new package `webapp/l7r/repl/rolls/`, inside the existing REPL package
**Entry points**: `begin_conversation()`, `end_conversation()`, `abandon_conversation()`,
`conversation_status()` at the REPL prompt

**External boundaries, all injected as callables so tests never touch the network** - the pattern
`discern_honor(npc, pc, characters=..., get_body=..., update=...)` already establishes:

| boundary | reached by | tested with |
|---|---|---|
| Discord REST | `rolls/discord.py` | `webapp/tests/fixtures/discord/messages.json` (615 real pseudonymized messages) |
| character-sheet `/api/rolls`, `/api/characters` | `rolls/sheet.py` | hand-written fixtures - **THE ENDPOINTS DO NOT EXIST YET** |
| Obsidian Portal | `chargen/op.py` (existing) | injected callables, as `discern_honor` does |
| the skill vocabulary | `/host-l7r-repo/rules/02-skills.md` | the real file; it is mounted and canonical |

**Unknowns**: none outstanding. The two that existed were resolved in research - the `@N` magnitude
threshold (R4, settled from `rules/01-character_creation.md`) and the Discord time-window fetch
(R9, settled by live measurement). One question is deliberately REFERRED TO THE GM rather than
guessed (bare-number rolls, research.md closing section); it does not block anything.

## Constitution Check

*GATE: passed before Phase 0. Re-checked after Phase 1 design - result identical, noted at the end.*

- **I. Accessibility-First Viewports**: **N/A** - no UI. This feature adds REPL functions and writes
  text to an external site; it renders no page in the L7R Toolkit.
- **II. Bold, Intentional Design**: **N/A** - no new UI surface.
- **III. Pool Data Conventions**: **N/A** - generates no pooled content. The committed Discord
  fixture is test data, not a content pool.
- **IV. One Canonical Home for GM Source**: **N/A** - adds and moves no SOURCE blocks.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: **PASS** - no task touches SOURCE markers.
  The one write is a splice into an OP `bio`, which is not GM SOURCE-marked content, and the splice
  is additive: existing bio text is preserved verbatim (FR-015).
- **VI. Verify Before Reporting Done**: **PASS** - every task names its check. Pure-logic tasks run
  their own test file in full (never `-k`); the feature ends with one `make done` from `webapp/`.
  The corpus sweep (SC-002/SC-003) is its own task and its own test, not a spot check.
- **VII. De-Localized Generation by Default**: **N/A** - generates no setting content.
- **VIII. Direct Voice Over Framing Distance**: **N/A** - generates no prose.
- **IX. Setting Integration**: **N/A**.
- **X. Python Discipline (NON-NEGOTIABLE)**: **PASS** - ruff, `ruff format --check`, `mypy --strict`,
  pytest, 100% coverage on the pure modules. The package split below exists to keep every file well
  under ~1,000 lines, and the package gets a `CLAUDE.md` index like its parent has.
- **XI. Japanese Authenticity (NON-NEGOTIABLE)**: **N/A** - emits no kanji; character names are
  copied from existing records, never invented.
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: **PASS** - the reasoning behind every
  rule is recorded where the rule lives. Specifically, the Etiquette cap carries the GM's stated
  reason (politeness is restraint) as a comment in `rules.py`, and the `@N` threshold cites
  `rules/01-character_creation.md`. research.md R1-R10 carry the measurements.
- **XIII. No Known Regressions (NON-NEGOTIABLE)**: **PASS** - baseline taken in a detached worktree
  (`git worktree add --detach`) before the first code change, never by stashing, and each failure it
  reports checked against the clone before being called pre-existing.
- **XIV. Fix Defects Where You Find Them (NON-NEGOTIABLE)**: **PASS** - acknowledged. One candidate
  already arose and was correctly NOT "fixed": an apparent 404 from `op.get_character_body` was the
  diagnostic passing a slug where the function documents an id (research.md R10). Recording it stops
  the next reader from mis-fixing a healthy function.
- **XV. Keep Going (NON-NEGOTIABLE)**: **PASS** - the sheet-app endpoints are absent, and the plan
  routes around that by proving the typed path first rather than stopping.
- **XVI. Build What Was Asked (NON-NEGOTIABLE)**: **PASS** - two rounds of `spec-fidelity` review,
  verdict FAITHFUL, recorded in the spec. The single addition beyond the request (the abandon call)
  is recorded in the spec's Assumptions to be raised with the GM once the implementation works.
- **XVII. A README Is Written By A Human (NON-NEGOTIABLE)**: **PASS** - no README is written. The
  package index is a `CLAUDE.md`, which is the project's own convention for that.
- **XVIII. A Guard Ships With Its Test (NON-NEGOTIABLE)**: **N/A** - adds no hook or guard script.

**No gate is DEFERRED, so there is no Complexity Tracking entry and nothing needs GM approval
before `/speckit-tasks`.**

## Project Structure

```
webapp/l7r/repl/rolls/
  CLAUDE.md          index: which file holds what, and the testing stanza
  __init__.py        public surface re-exported to the prompt
  rules.py           PURE. rounding, the Etiquette cap, contested margin, line rendering
  skills.py          PURE. the skill vocabulary read from rules/02-skills.md, prefix matching
  parse.py           PURE. typed-message -> Roll, across every observed form
  bio.py             PURE. splice a line into an OP bio after the [[File:...]] embed
  models.py          PURE. Roll / Contest / Conversation dataclasses
  discord.py         BOUNDARY. REST reads, snowflake synthesis, after-paging
  sheet.py           BOUNDARY. the character-sheet client; absent endpoints degrade to empty
  conversation.py    orchestration + the background poller + the OP write
webapp/tests/
  test_rolls_rules.py  test_rolls_skills.py  test_rolls_parse.py  test_rolls_bio.py
  test_rolls_models.py test_rolls_discord.py test_rolls_sheet.py  test_rolls_conversation.py
  test_rolls_corpus.py   <- SC-002 / SC-003 sweep over the whole fixture
  fixtures/discord/messages.json   fixtures/sheet/*.json
```

Six of the nine modules are pure and carry the 100% coverage requirement. The two boundary modules
are thin by construction - the logic they would otherwise hold lives in the pure modules - so the
fixture tests cover them without mocking the transport.

## Phase 0: Research

Complete. [research.md](research.md) holds R1-R10: why the roll-history join is the DETECTOR rather
than a lookup (R1), the per-player split that makes the typed path primary (R2), every observed
typed form across three passes (R3), the rules-grounded `@N` threshold (R4), the adversarial
negatives (R5), the skill vocabulary's canonical home (R6), why the GM's own rolls stay in (R7),
round timing (R8), the Discord API's mutually-exclusive `before`/`after` (R9), and the bio splice
anchor plus two API facts that each cost a wrong turn (R10).

## Phase 1: Design

See [data-model.md](data-model.md) for the entities and [contracts/](contracts/) for the two
interface contracts - the REPL surface the GM types at, and the character-sheet client interface
that stands in for endpoints which do not exist yet.

**Ordering, decided here rather than discovered one failure at a time** (the project's
ordering rule): `skills.py` -> `rules.py` -> `models.py` -> `parse.py` -> `bio.py` -> `discord.py`
-> `sheet.py` -> `conversation.py`. Every arrow is a real dependency: `parse` needs the vocabulary
and the models; `rules` renders what `models` holds; `conversation` is the only module that knows
about all of them, and is therefore the only one that is not pure.

**Proving order, which is NOT the build order** (constitution VI - one artifact first, then the
sweep): the typed path end to end on ONE conversation before the corpus sweep, and the corpus sweep
before the image path, because the image path depends on endpoints that do not exist and the typed
path does not.

## Post-design Constitution re-check

Re-evaluated after the Phase 1 artifacts: unchanged, all PASS or N/A, nothing deferred. The design
added no UI, no pool data, no SOURCE blocks and no guard, so the N/A gates stay N/A, and the package
split is what keeps Principle X's file-size clause satisfied rather than merely promised.
