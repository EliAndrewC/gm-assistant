# Tasks: Discord roll capture into Obsidian Portal

**Feature**: `specs/201-discord-roll-capture` | **Plan**: [plan.md](plan.md)

Build order is the dependency order settled in the plan. Proving order is different and deliberate
(constitution VI): one conversation on the typed path first, THEN the corpus sweep, THEN the image
path - because the image path depends on endpoints that do not exist and the typed path does not.

Every task names the check that closes it. No task is done because it looks done.

## Phase A - baseline and scaffolding

- [x] **T001** Take the regression baseline on unmodified code and record it in
  `specs/201-discord-roll-capture/baseline.md`: every currently-failing test, so a later failure can
  be classified rather than argued about. Check each reported failure against the clone before
  calling it pre-existing (gitignored artifacts differ between trees).
  *Check*: `make done` output captured; the ledger lists each failure with its cause.
- [x] **T002** Create the package skeleton `webapp/l7r/repl/rolls/` with `__init__.py` and a
  `CLAUDE.md` index in the shape of `webapp/l7r/repl/CLAUDE.md` - a table of which file holds what,
  the design notes, and a Testing stanza with the exact pytest command.
  *Check*: `python3 -c "import l7r.repl.rolls"` from `webapp/`.

## Phase B - pure logic (P1 typed path)

- [x] **T003** `rolls/skills.py`: read the canonical vocabulary from
  `/host-l7r-repo/rules/02-skills.md` "## Skill List" (R6); exact and unambiguous-prefix matching;
  an ambiguous prefix REPORTS rather than chooses. Combat's attack/parry included.
  *Check*: `pytest tests/test_rolls_skills.py` in full, including a test that the real rules file
  yields all 18 social/knowledge skills.
- [x] **T004** `rolls/models.py`: `Roll`, `Contest`, `RecordingRule`, `Conversation` per
  [data-model.md](data-model.md).
  *Check*: `pytest tests/test_rolls_models.py`.
- [x] **T005** `rolls/rules.py`: round down to the increment (FR-010); per-skill cap applied BEFORE
  rounding (FR-011); contested margin with both totals unrounded (FR-012); render the open line
  (FR-021) and the contested line. **The GM's reason for the Etiquette cap is recorded as a comment
  at the cap** - politeness is restraint, so a very high etiquette roll cannot be noteworthy the way
  a gift can (constitution XII).
  *Check*: `pytest tests/test_rolls_rules.py` covering the rounding boundary (24/25/29), the cap
  (68 -> 40, NOT 65), the contested margin (41 vs 28 -> 10), a tie, and SC-006 - adding a capped
  skill is one dict entry.
- [x] **T006** `rolls/parse.py`: typed message -> `list[Roll]`, across every form in R3 - `@N` and
  `at N`, rank before or after the skill, dice traces ignored, named bonuses ignored, abbreviations,
  multiple rolls per message. The `@N` magnitude threshold of FR-006 with its citation to
  `rules/01-character_creation.md`, and the 6-9 band SURFACED rather than guessed.
  *Check*: `pytest tests/test_rolls_parse.py` with one case per form in R3.

## Phase C - first artifact end to end (typed path)

- [x] **T007** `rolls/bio.py`: splice a line into an OP bio directly after the `[[File:...]]` embed
  (R10), or at the top when there is none; existing content preserved byte for byte (FR-015).
  *Check*: `pytest tests/test_rolls_bio.py` against a real captured bio, asserting the rest of the
  body is unchanged.
- [x] **T008** `rolls/discord.py`: REST reads with a synthesized snowflake and `after` alone (R9),
  incremental paging from `last_seen`, the bot token from `[discord] bot_token`.
  *Check*: `pytest tests/test_rolls_discord.py` against the committed fixture; plus one live
  hand-check against the test server once the GM has made it.
- [x] **T009** `rolls/conversation.py`: the state machine, the daemon-thread poller following
  `shell.py`'s `warm_caches` pattern, and the OP write. `end_conversation()` writes immediately
  (FR-019). Boundaries injected as callables, as `discern_honor` does.
  *Check*: `pytest tests/test_rolls_conversation.py` - open/collect/close with injected fakes,
  the window bounds (FR-003), double-open, close-with-nothing, and that the poller never blocks.
- [x] **T010** Wire into the prompt: re-export in `l7r/repl/rolls/__init__.py`, add the four names to
  `l7r/repl/__init__.py`'s `__all__` and `COMMANDS`.
  *Check*: `./scripts/repl.py 'conversation_status()'` runs and prints.
- [x] **T011** **PROVE ONE ARTIFACT**: one real conversation from the saved corpus, typed rolls only,
  producing the GM's exact line for the motivating etiquette round.
  *Check*: the rendered line equals the GM's own format, by assertion, in
  `tests/test_rolls_conversation.py`.

## Phase D - the corpus sweep

- [x] **T012** `tests/test_rolls_corpus.py`: run the parser over all 615 fixture messages.
  **SC-002** - every roll is parsed correctly or explicitly reported, and NONE is parsed wrongly.
  **SC-003** - no non-roll produces a roll, including the adversarial negatives of R5 (dates, ring
  stats, session counts, the GM's own pasted REPL output).
  *Check*: the test itself; it is the measurement, not a spot check.

## Phase E - the image path (P2, endpoint-dependent)

- [~] **T013** `rolls/sheet.py` to the contract in
  [contracts/character-sheet-client.md](contracts/character-sheet-client.md): both calls, the
  rank-resolution order, and degradation to empty on every failure mode including "endpoint never
  built".
  *Check*: `pytest tests/test_rolls_sheet.py` with fixtures for success, 404, unset token, and
  malformed JSON.
- [~] **T014** Join image posts to recorded rolls by author and timestamp; unmatched images ignored
  silently (FR-008); dedup preferring the recorded roll (FR-009); unresolved reported (FR-018).
  *Check*: `pytest tests/test_rolls_conversation.py` extended - a meme in the window resolves to
  nothing, and a player who both pasted and typed yields ONE roll.

## Phase F - close out

- [x] **T015** Package `CLAUDE.md` completed with the real file table and testing stanza; parent
  `webapp/l7r/repl/CLAUDE.md` gains a row pointing at the new package; root `CLAUDE.md` skills table
  untouched (this is not a skill).
  *Check*: read it as a newcomer would - does it say which file holds what?
- [ ] **T016** Full gate once, from `webapp/`, backgrounded, then compared against T001's ledger.
  Any new failure is a regression and blocks the push (Principle XIII).
  *Check*: `make done` green, or every failure matched to the baseline ledger.
- [ ] **T017** Commit and `scripts/sync-with-main.sh done`. Report to the GM what was built, what is
  waiting on the character-sheet endpoints, and the two questions the fidelity review referred to
  them (the Etiquette cap on CONTESTED rolls, and bare-number rolls).

## Parallelizable

T003, T004 and T007 touch different files with no dependency between them. T005 needs T004; T006
needs T003 and T004. Everything in Phase E needs Phase C.

## Status at hand-off (2026-08-28)

T001-T012 and T015 are done and verified. T013/T014 (the image path) are written and unit
tested against fixtures but CANNOT be verified end to end until the character-sheet
endpoints exist - marked `[~]`, not `[x]`, because the fixtures prove the client contract
and not the real response. T016/T017 are the gate and the push.
