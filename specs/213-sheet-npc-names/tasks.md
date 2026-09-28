# Tasks: `GET /api/names` (feature 213)

- [x] T001 Spec, GM request (verbatim), fidelity review to FAITHFUL, claim pushed (`aa4a384d`)
- [x] T002 Baseline `make done` on unmodified code in a detached worktree
- [x] T003 Tests first: `tests/test_sheetnames.py` (picking rules, parsing, token check, refresh
      lock and failure, the HTTP contract) - red
- [x] T004 `l7r/sheetnames.py` + `app.py` handler, `Root.api`, `_names_token`, `/api` mount
      config - green
- [x] T005 Tests first: `chargen/test_sheetroster.py` NPC cases (parse, fetch, carry-forward,
      given_names union) and the conftest refusals - red
- [x] T006 `chargen/sheetroster.py` NPC names - green
- [x] T007 Docs: `app.py` docstring route list, CLAUDE.md route list,
      `development-secrets.ini.example` `[character_sheet]` section
- [x] T008 Whole affected test files with `-n auto --no-cov`, then `make done` (backgrounded)
- [x] T009 Commit; `scripts/sync-with-main.sh done`
- [ ] T010 (GM) set `[character_sheet] names_token` in main's secrets, deploy gm-assistant; set
      `GM_ASSISTANT_URL` / `GM_ASSISTANT_NAMES_TOKEN` on the character sheet
