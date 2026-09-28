# Implementation Plan: `GET /api/names`

**Feature**: `specs/213-sheet-npc-names` | **Date**: 2026-09-28 | **Spec**: [spec.md](spec.md)

## What is measured and where it came from

gm-assistant at `aa4a384d`, character-sheet at `17555dc` (plus its uncommitted
`app/services/npc_names.py`), both 2026-09-28.

| finding | consequence |
|---|---|
| `l7r/repl/names.py:147-171` builds a batch as repeated `pick_name(g, pool, used, [*avoid, *picks], peasant=...)` | FR-006 reuses the same loop shape; no second engine |
| `pick_name(peasant=False)` has two tiers, the second being the whole pool | FR-004 cannot call it that way; it passes a pool already filtered to samurai-eligible entries with `peasant=None` (one tier, no fallback) |
| `opcache.refresh_if_stale(max_age)` already refreshes both the OP roster and (first) the sheet index roster, fail-soft on OP's empty listing, but lets other exceptions out | the endpoint wraps it: lock + catch-all, logged |
| `l7r/repl/names.py` already holds a `_refresh_lock` for the REPL | a separate lock in the webapp module: the REPL and the webapp are different processes, so sharing the object buys nothing, and importing `l7r.repl` into the webapp would pull the whole REPL namespace |
| `sheetroster` scrapes the sheet's PUBLIC index; generated NPCs are invisible to players there (character-sheet `17555dc`) | FR-010 needs a second, authenticated source: `GET /api/characters`, which flags `is_npc` |
| the REPL reads `/api/characters` with `[character_sheet] roll_query_token` (`l7r/repl/rolls/sheet.py:query_token`) | `sheetroster` reuses `query_token` (lazily imported) so the secret's name lives in one place |
| `test_mount_application_handles_missing_chargen` reloads `l7r.app` with every `chargen` import failing | `l7r.app` must not import `chargen` at module level; `l7r/sheetnames.py` imports `chargen` inside its functions |
| `webapp/fly.toml`: `min_machines_running = 0`, no volume; the Dockerfile copies `development-secrets.ini` and `opcache/` into the image | the deployed app reads `names_token` from the bundled secrets file, and every cold boot starts from the deploy-time cache (spec Decision 1) |
| the sheet client sends `count`, `peasant=true|false`, optional `avoid`, a Bearer header, 12 s timeout; reads `names` from a 200 and treats anything else as "no names" | the contract below matches it exactly |

## Design

### D1. `l7r/sheetnames.py` (new) - pure helpers plus the refresh

- `parse_count(raw) -> int` (absent 1, clamp 1..30, non-integer `ValueError`),
  `parse_peasant(raw) -> bool` (absent/`false` False, `true` True, case-insensitive, else
  `ValueError`), `parse_avoid(raw) -> list[str]` (str or list of str; comma split, stripped,
  empties dropped).
- `token_matches(header, configured) -> bool`: scheme `Bearer` (case-insensitive), then
  `hmac.compare_digest` over UTF-8 bytes, so a non-ASCII header cannot raise.
- `suggest_names(count, *, peasant, pool, used, avoid=(), rng=None) -> list[str]`: builds the caste
  set (peasant-flagged, or samurai-eligible = `not peasant or samurai`) from the male entries, then
  the repeated `pick_name` loop with `peasant=None` over that set; `NamePoolExhausted` ends it.
- `refresh_used_names() -> bool`: `with _refresh_lock:` `opcache.refresh_if_stale(MAX_AGE)`; any
  exception logged and swallowed (FR-009). `MAX_AGE = 3600.0`, the cache's own default window,
  named here so the test can pin it.

### D2. `app.py`

- `_names_token()` reads `[character_sheet] names_token` through `_load_secrets()` at request time,
  stripped.
- `NamesApi` (exposed `names`), attached as `Root.api`; `Root.__init__` takes
  `names_token: Callable[[], str] | None` (default `_names_token`, resolved at call time so tests
  and a secrets change both reach it). Order in the handler, settled here: Content-Type; 503 if no
  token configured; 401 (with `WWW-Authenticate: Bearer`) on a bad header; 400 on bad parameters;
  refresh; pick; 200. Auth BEFORE parameter parsing and before the refresh, so an unauthenticated
  caller can neither probe parameter handling nor trigger an Obsidian Portal refresh.
- Mount config: `'/api': {'tools.l7r_auth.min_role': 'anonymous'}`, commented that the bearer is
  checked in the handler.
- Module docstring route list and CLAUDE.md's route list gain the endpoint.

### D3. `chargen/sheetroster.py` - NPC names (FR-010)

- `API_URL`, `parse_npcs(payload) -> list[str]` (names of entries with a truthy `is_npc`; a payload
  without a `characters` list is a `ValueError`), `fetch_npc_names()` (Bearer `query_token()`,
  raises when the token is unset).
- `refresh_if_stale(..., fetch_npcs=None)`: unchanged for the index. When the index succeeds, the
  NPC fetch runs; its failure is logged and the previously cached `npcs` list is carried forward.
  The cache file becomes `{"names": [...], "npcs": [...]}`; `npc_names(path)` reads the second
  list and `given_names(path)` unions both. The index failing still writes nothing, exactly as
  before (the file's age is the retry signal; writing on a half-success would make it look fresh).
- Both conftests refuse `fetch_npc_names` the way they refuse `fetch_index` (FR-013).

### D4. Secrets example

`[character_sheet]` does not exist in the example yet (its two outbound tokens were added by hand to
main's file). Add the section with all three keys, empty, each commented with its direction.

## Constitution check

- **X (Python discipline)**: ruff, format, mypy --strict, 100% coverage on `l7r` and
  `chargen.sheetroster` via `make done`. New module is small and pure where it can be; the network
  boundaries (`fetch_npc_names`, the refresh) are injected or patched in tests.
- **XIII (no known regressions)**: baseline `make done` taken on unmodified `aa4a384d`'s parent in a
  detached worktree before any code change.
- **XIV (fix defects where found)**: none found outside the delta so far; any found goes in this work.
- **XVI (build what was asked)**: spec reviewed FAITHFUL in round 2; the two departures the review
  caught are recorded in the spec's Review history. No exception is carved in this plan.
- **XVII (READMEs)**: none touched.
- **Record the why**: spec Decisions 1-5 carry the priced alternatives; the no-fallback samurai
  draw and the lock carry comments at the point of change.
- **I (UI)**: no UI change - JSON only - so no screenshots or DOM audit apply.
