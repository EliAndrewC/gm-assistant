# Plan: feature 221 - issue inbox

| piece | where |
|---|---|
| the inbox: `Inbox` (highest number seen + ETag) as a `repos` field of the existing per-session `Watch`; `look_inbox` (the repository's issue list, newest 30 by creation, conditional); `check` looks at inboxes first and auto-watches what it finds; `inbox` / `stop OWNER/REPO` / `status`; `own_repo` (the `"repo"` key, else a GitHub origin, following local-path origins); the `NEW_ISSUE` delivery heading; the coordinating reminder in `nudge` | `webapp/l7r/issuewatch.py` (still ONE stdlib-only file, Python 3.10 syntax) |
| tests (the fake GitHub gains a repository issue list; a 215-shape watch file) | `webapp/tests/test_issuewatch.py` |
| this repository's `"repo"` | `.claude/issue-watch.json` |
| the procedure | "Coordinating over GitHub issues" in the user-level `~/.claude/CLAUDE.md` (outside this repository; the shared host mount) |
| where the next session finds it | module docstring; `docs/key-paths.md` entry |

## Constitution check

- **X**: 100% coverage, mypy strict, ruff - the module is in the gated tree.
- **XIII**: baseline = 215's 82 issue-watch tests on the same HEAD, all still green unchanged
  apart from the fake GitHub learning the list endpoint.
- **Live install**: the shared copy is replaced under running sessions in other containers, so
  `locked()` reads every field but the identity with a default (FR-009).

## Ordering note

`check` looks at inboxes BEFORE issues, so a new issue's existing comments arrive in the same
delivery as the issue itself.
