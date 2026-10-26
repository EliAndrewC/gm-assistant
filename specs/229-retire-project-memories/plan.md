# Plan 229: Retire project memories

## Tooling (each with its test companion, run by `make done`)

| FR | Change | Where | Test |
|---|---|---|---|
| 021 | Seed a clone's gitignored secrets (`webapp/development-secrets.ini`, `webapp/.env`) from main when missing, at claim time and on every prompt | `scripts/clone-sync-hooks.sh` (`seed_secrets`) | `scripts/test-clone-sync-hooks.sh` |
| 021 | `op.OPNotConfigured` (a `ValueError`) raised by `_get_oauth_session`/`_get_campaign_id`; every fail-soft read re-raises it instead of answering `[]`/`None` | `webapp/chargen/op.py` | `webapp/chargen/test_op.py` |
| 021 | `flyctl` installed and checked | `container-scripts/setup-dev-env.sh` | its own `--check` |
| 022 | Steering lines: healed scars (positive description AND the forbid), daisho on the left hip for bushi with no third sword, full figure with white space above head and below feet, white tabi and straw zori (not for monks? monks wear sandals too - tabi/zori is fine for all), "unmistakably a woman" for women | `webapp/chargen/art.py` `generate_prompt` | `webapp/chargen/test_art.py` / `tests/test_art.py` |
| 022 | Pad with white before the headshot crop so a crown trimmed to y=0 keeps headroom | `art.get_headshot_crop` + `crop_headshot` share a pad | same |
| 023 | `stop` mode: block the turn end (exit 2) when (a) a `make done` runs with its cwd inside this session's clone, or (b) the clone's HEAD is not in main's history; allow when `stop_hook_active`, when the session has no claimed clone | `scripts/clone-sync-hooks.sh stop`, wired as a `Stop` hook in `.claude/settings.json` | `scripts/test-clone-sync-hooks.sh` |
| 024 | Warn (stdout, exit 0) once per other claimant when a LIVE other session claims the same clone, checked BEFORE the dirty-tree exit | `scripts/clone-sync-hooks.sh pretool` | `scripts/test-clone-sync-hooks.sh` (dirty clone + live claimant -> warning, still allowed) |
| 025 | Local container paths in text written to setting content (`setting/`, `campaigns/`, `cosmology/`, `hooks/`, `notes/` of this repo or a clone, and EVERY file under `/host-l7r-repo/`) are blocked; evaluated BEFORE the house-style hook's GM-writing exemption; SOURCE blocks skipped | `scripts/house-style-hooks.sh` | `scripts/test_hooks_cases.py` (incl. an edit to `/host-l7r-repo/setting/budgets.md`) |
| 026 | Rule: no hardcoded catalog counts in copy | `.claude/agents/frontend-review.md` | review-agent TDD (see tasks) |
| 027 | Shizu's Shoda design priced per contract on a trail; pinned figures, plus the handout's table when `/host-l7r-repo/current/shoda-shrine.md` exists | `webapp/tests/test_shrines_shoda.py` | itself |

Guard files (`scripts/*-hooks.sh`, `.claude/settings.json`) need `GUARD_EDIT_OK` with a reason in the edit.

## Docs

As spec FR-009..FR-020, plus: `docs/generation-rules.md` line 10 ("captured in memory") rewritten; comments in
`scripts/sync-with-main.sh:82` and `scripts/deploy-secrets-hooks.sh:6` that cite a memory now cite the hook;
`docs/guards.md` table + count; CLAUDE.md Guards count and a one-line "no memory" rule.

## Memory off

`autoMemoryEnabled: false` in `.claude/settings.json`; delete `~/.claude/projects/-gm-assistant/memory/*` last,
after everything above is pushed.
