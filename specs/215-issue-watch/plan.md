# Plan: feature 215 - issue watch

| piece | where |
|---|---|
| the whole mechanism: opt-in config and token, GitHub calls with ETags, per-session watch state under a lock, `/clear` adoption by Claude process, the three hooks, the commands, the installer | `webapp/l7r/issuewatch.py` - ONE stdlib-only file, because it is installed into the shared `~/.claude/hooks/` and run by every container (it imports nothing from this repository) |
| tests (fake GitHub honoring If-None-Match; fake `/proc`) | `webapp/tests/test_issuewatch.py` |
| this repository's opt-in | `.claude/issue-watch.json` (token: `[github] push_pat` in `webapp/development-secrets.ini`) |
| the sheet's opt-in and note | `.claude/issue-watch.json` and `issue-watch-note.md` in that tree, uncommitted |
| where the next session finds it | the root `CLAUDE.md` key-paths entry, and the module docstring |

## Constitution check

- **X**: 100% coverage, mypy strict, ruff - the module is in the gated tree.
- **XIII**: baseline = the green 214 gate on the same HEAD; nothing outside the new files changes.
- **Guards**: the installed hook commands carry `GUARD_EDIT_OK` with a reason, as every
  user-level hook entry does.

## Ordering note

`hook deliver` rewrites the wait token BEFORE checking, so the previous turn's idle wait exits
rather than waking a session that is already working (FR-008 and the GM's "not interrupted").
