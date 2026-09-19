# Tasks: Roll modes (feature 207)

Marked off only when the named test file is green. One full gate at the end.

## Phase 0 - baseline
- [x] T001 `make done` on unmodified HEAD in the clone; record the result in research.md

## Phase 1 - vocabulary, modes, rules-derived tables
- [x] T010 `skills.py`: single-word knacks that declare a ring join the vocabulary; `skill_rings()`, `advanced_skills()` (tests: `test_rolls_skills.py`)
- [x] T011 corpus sweep re-read; every change in `EXPECTED_ROLLS` explained in research.md (`test_rolls_corpus.py`)
- [x] T012 `modes.py`: the table, `mode_of()`, and the every-entry-has-a-mode test (`test_rolls_modes.py`)
- [x] T013 `npcnumbers.py`: block parse/render, school extra dice from the rules, school detection, `infer`, `compare` with void point answers, automatic raises (`test_rolls_npcnumbers.py`)

## Phase 2 - tagged rolls
- [x] T020 `GmRoll` fields; `DiceTotal.__sub__` hands off to a tag (`test_repl_gmrolls.py`, `test_repl_dice.py`)
- [x] T021 `npcskills.py`: `SkillTag` tag form, record / check / disagreement prompt, Ctrl-C = mistake (`test_rolls_npcskills.py`)
- [x] T022 `SkillTag` call forms, `vp`, prompts for missing rank/ring, rank 0, acting/history recorded-not-rolled, automatic raises on the call form only
- [x] T023 conversation: load numbers + school at begin, persist the numbers block on the debounce (`test_rolls_conversation.py`, `test_rolls_watch.py`)

## Phase 3 - rendering
- [x] T030 `Roll.outcome`; interrogation line with outcome, grouped by outcome; acting line (`test_rolls_rules.py`, `test_rolls_interrogation.py`)
- [x] T031 `hidden.py` block and its persistence; SC-001 test that no hidden number reaches the bio (`test_rolls_hidden.py`)

## Phase 4 - lines of questioning
- [x] T040 `new_line_of_questioning`: declare, synchronous collect, per-roll prompt for unattached and repeat rolls (`test_rolls_lines.py`)
- [x] T041 attach-by-message-time in collect; collect lock
- [x] T042 `grilling()` retroactive and idempotent; `detected()`; private comparison with exact or inferred Sincerity rank

## Phase 5 - annotate()
- [x] T050 `keys.py`: decoder + two-press undo + first-key hand-back to readline (`test_rolls_keys.py`)
- [x] T051 mode dispatch: always-open, default-open with undo and typed fallback (`test_rolls_annotate.py`, `test_rolls_annotate_modes.py`)
- [x] T052 manipulation picker with 15; sneaking picker with nobody; pre-pairing from tagged rolls with exact free raises
- [x] T053 acting: hidden opposing roll + outcome; interrogation branch reduced to unattached rolls and missing ranks

## Phase 6 - finish
- [x] T060 namespace, `COMMANDS`, banner; `rolls/CLAUDE.md` and `repl/CLAUDE.md` indexes
- [x] T061 scripted end-to-end run against fakes (quickstart.md)
- [x] T062 `make done` green; tasks marked; commit; `sync-with-main.sh done`

Added during implementation:
- [x] T054 the picker's letters (`n` / `f` / `t`) at a pre-paired prompt - found by T061's scripted session (research R9)
