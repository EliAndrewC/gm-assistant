# Tasks: feature 214 - the Isawa Ishi 3rd Dan boost

Mark a task done only when verified.

## Phase 0 - specify and hand off

- [x] T000a GM request recorded verbatim; spec written and reviewed by `spec-fidelity`.
- [x] T000b Handoff document `discord-design/ishi-boost-requirements.md` written into the
      character-sheet working tree, uncommitted.
- [x] T000c Baseline `make done` on the unmodified clone.

## Phase 1 - gm-assistant

- [x] T101 `models.py`: `Roll.boost`, `Roll.boosted_by`; `Conversation.boosts`.
- [x] T102 `sheet.py`: `RecordedRoll.roll_key`, `RecordedRoll.target_message_id`.
- [x] T103 `boost.py`: recognition (bot message, typed, recorded row), reply reference, place /
      apply / hold, un-apply. Tests in `tests/test_rolls_boost.py`.
- [x] T104 `conversation.py` collect: route boosts, no roll from a boost message, re-settle /
      re-compare after applying; the LOADING fix with its own test.
- [x] T105 `end_conversation` refuses with a held boost; force names it. `cancel_boost()`.
- [x] T106 `annotate.py`: held boosts in the list, the target picker, staging, Ctrl-C.
- [x] T107 `cancel_boost` at the prompt; `rolls/CLAUDE.md` section.
- [x] T108 `make done` green; no regression against T000c.

## Phase 2 - ship gm-assistant's half

- [ ] T201 Commit, `sync-with-main.sh done`.

## Phase 3 - after the character-sheet session deploys (not this session's to start)

- [ ] T301 Run the handoff document's Part 4 against the deployed app. A missing requirement is
      REPORTED, not worked around.
