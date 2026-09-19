# Tasks: Oppose Social / Oppose Knowledge penalties

- [x] T001 Read the rules text for both knacks and the rolls package end to end (US all)
- [x] T002 Spec, GM request verbatim, claim feature 208
- [x] T003 Vocabulary: `MULTIWORD_KNACKS`, per-word abbreviation, bare `oppose` stays ambiguous (US1)
- [x] T004 Parser phrase pass, run before the one-word cluster (US1)
- [x] T005 Prove T004 on the corpus: `EXPECTED_ROLLS` unchanged at 125 (FR-002)
- [x] T006 `oppose.py`: derived penalty, highest-wins, `for_line`, `settle` (US2-US4)
- [x] T007 `GmRoll.penalty` apart from `bonus`; `DiceTotal._shift` returns the entry's total (US2)
- [x] T008 Called and tagged NPC rolls pay it; a mistake pays nothing (US2)
- [x] T009 `annotate()` prices an untagged roll or typed total when it is paired (US2.5)
- [x] T010 Lines of questioning: retroactive on the current line, never twice (US3)
- [x] T011 Arrival: settle late-seen rolls, say what happened, re-run the line (US1, US3)
- [x] T012 The record: bare open line in sequence, never pending, mode `automatic` (US5)
- [x] T013 Fidelity round 1: strike the tool-written note; ring mapping becomes the GM's statement
      with the rules text as a reported check
- [x] T014 Fidelity round 2: strike the discard command from spec AND code; record the gap
- [x] T015 `tests/test_rolls_oppose.py`, then the whole rolls suite
- [x] T016 Docs: `rolls/CLAUDE.md` "Feature 208", `repl/CLAUDE.md` gmrolls row
- [x] T017 Fidelity round 3 verdict recorded in spec.md
- [x] T018 `make done` green; commit; `sync-with-main.sh done`
