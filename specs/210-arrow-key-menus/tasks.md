# Tasks: arrow-key menus

- [x] T001 Read `keys.py`, `console.py` and every prompt in `annotate.py`, `lines.py`, `npcskills.py`
- [x] T002 Spec; the GM's two messages and the approved plan verbatim
- [x] T003 `menu.py`: `Option`, `Picker` (pure state + drawing), `choose` (key loop), `ask_choice`
- [x] T004 `interactive(ask)`: real terminal AND a registered asker, so scripted tests never hang
- [x] T005 `console.py`: the overlay redraw (US3); `asking()` - the `>>> ` redraw defect (XIV)
- [x] T006 Call sites: which roll, o/c/d/ob, which of yours, the always-contested picker, which
      line, the no-lines discard question, how the NPC appeared, join-or-discard, mistake/record
- [x] T007 At a terminal the typed enumeration is not printed as well
- [x] T008 Prove FR-004 on one artifact: every pre-existing rolls test passes UNMODIFIED
- [x] T009 `tests/test_rolls_menu.py`: keys, drawing, a real pty, the watcher, a whole arrow-key run
- [x] T010 Fidelity round 1: enumeration illustrative, join default pinned, collapse is a decision
- [x] T011 `rolls/CLAUDE.md` "Feature 210"
- [x] T012 Fidelity verdict recorded; `make done` green; commit; `sync-with-main.sh done`
