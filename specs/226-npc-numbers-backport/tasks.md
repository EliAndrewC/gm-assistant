# Tasks: NPC numbers backport

- [ ] T001 Baseline: `make done` in a detached worktree of main (Principle XIII), log kept.
- [ ] T002 [P] `npcnumbers.render` keeps unparsed block lines; test in `tests/test_rolls_npcnumbers.py` (red first).
- [ ] T003 `l7r/npcbackport.py`: `normalize`, `merge`, `backport`; `tests/test_npcbackport.py` covering every spec
      acceptance scenario and edge case, on a real recorded GM-notes excerpt, 100% coverage.
- [ ] T004 `POST /api/npc-numbers` on `NamesApi`: gate (503/401 before body/OP), 405, 400s, the answer; tests beside the
      names API tests.
- [ ] T005 `conversation._write_notes` merges the fresh block (FR-010); test that a stat added since the conversation
      opened survives a tick.
- [ ] T006 Docs: `docs/key-paths.md` route list, `l7r/repl/rolls/CLAUDE.md` (render keeps unparsed lines), the app
      docstring.
- [ ] T007 Gate (`make done`), commit, `sync-with-main.sh done`, `make deploy`, live check (`no_record` probe).
- [ ] T008 GitHub issue to EliAndrewC/character-sheet for the caller (FR-011, FR-012), watched.
