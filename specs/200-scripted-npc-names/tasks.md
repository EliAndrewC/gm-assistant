# Tasks: Scripted NPC Naming with a Live Used-Name Cache

**Input**: spec.md, plan.md, research.md. Baseline (constitution XIII): detached worktree of HEAD, `make done` -> gate green; `.claude/skills/name` -> 89 passed.

Every task names its verification. "Reference artifact" tasks are proven on ONE file/run; "sweep" tasks run the whole suite once at the end.

## Phase 1 - Shared similarity module (FR-006)

- [x] T001 Port `.claude/skills/name/similarity.py` to `webapp/chargen/similarity.py` (typed, strict mypy, docstrings kept incl. the `-ko` rationale) and its tests to `webapp/chargen/test_similarity.py`. Verify: `pytest chargen/test_similarity.py -n auto` green, 100% of the module.
- [x] T002 Replace the skill's `similarity.py` with a shim (`sys.path` -> `webapp/`, `from chargen.similarity import *` with explicit names). Verify: `pytest .claude/skills/name/test_similarity.py` still green through the shim.

## Phase 2 - Cache: atomic write, staleness, used names (FR-001, FR-002, FR-004, FR-007, FR-014)

- [x] T003 [TDD] `opcache.save_cache` writes `<path>.tmp` then `os.replace`; `opcache.cache_age(path) -> float | None`; `opcache.refresh_if_stale(max_age_seconds=3600, path=...) -> bool` (fail-soft; returns whether a refresh ran); `opcache.used_given_names(path) -> frozenset[str]` memoized by `(path, mtime, size)`. Tests first in `test_opcache.py`. Verify: `pytest chargen/test_opcache.py -n auto`, 100%.
- [x] T004 `op.create_character`: on success, `opcache.refresh_cache_file()` in try/except logging failure (FR-001, fail-soft). `op.update_used_names` hourly thread -> also call `refresh_cache_file()` so the file reconciles website-added characters. Verify: `pytest chargen/test_op.py -n auto` green (fixture-based).

## Phase 3 - Engine draws from the pool (FR-005, FR-008, FR-009, FR-011)

- [x] T005 [TDD] `webapp/chargen/namepool.py`: `pool_dir()` (env `L7R_NAMES_DIR`, else `webapp/skills/name` if present, else `../.claude/skills/name`), `load_pool(dir)` memoized via `l7r.names.load_names`, `NamePoolExhausted`, `pick_name(gender, pool, used, avoid, rng) -> GeneratedName`. Tests in `test_namepool.py` with a tiny fixture pool. Verify: `pytest chargen/test_namepool.py -n auto`, 100%.
- [x] T006 `character.unused_name(gender, avoid)` -> `namepool.pick_name` with `used = constants.USED_NAMES | opcache.used_given_names()`; `Character.__init__(gender=None, avoid=())`; `Samurai`/`Peasant`/`Monk` accept and forward `gender`, `avoid`. Delete `male_names.txt`, `female_names.txt` and their loading in `constants.py` (keep `USED_NAMES`). Verify: `tests/test_character_*.py` green; a new `tests/test_character_names.py` proves pinned gender first roll, avoid-list distinctness over 200 rolls, exclusion of a used name, and `NamePoolExhausted` on an exhausted pool.
- [x] T007 Makefile `cov`: add `--cov=chargen.similarity --cov=chargen.namepool`. Verify: part of the final gate.

## Phase 4 - Skill scripts (FR-003, FR-004, FR-012, FR-015)

- [x] T008 `pick_name.py`: used names from `chargen.opcache` (sys.path shim), `refresh_if_stale` before picking, `--refresh`, `--avoid a,b`, `--bank N`, stale/empty-roster warning to stderr. Update `test_pick_name.py` (campaign-file tests -> cache-file tests). Verify: `pytest .claude/skills/name -n auto`; then ONE real run `python3 pick_name.py --bank 4 --avoid Izumi` against the live cache (reference artifact).
- [x] T009 `validate_pool.py`, `fix_pool.py`: used names from the cache; update their tests. Delete `fetch_campaign_names.py`, `test_fetch_campaign_names.py`, `campaign-names.txt`, `setup.sh`. Verify: `pytest .claude/skills/name -n auto` green; `python3 validate_pool.py` reports the two live-NPC pool names as expected (they are excluded at pick time, not deleted - FR-013).

## Phase 5 - Skill and agent docs (FR-003, FR-010, FR-015)

- [x] T010 `/name` SKILL.md: remove cookie, `.env`, `setup.sh`, `/loop 1h`; document `--refresh`, `--avoid`, `--bank`; refill procedure validates against the cache. Hyphens only, American spelling.
- [x] T011 `/chargen` SKILL.md Step 2: `GENDER` and `AVOID` become constructor kwargs, `opcache.refresh_if_stale()` before rolling, re-roll loop and hand set-check removed; Step 3b: name bank before the prose (FR-015). `/synthesize` SKILL.md Step 2c: name bank before the prose, avoid = subject's given name. `backstory-review.md`: invented names must come from the bank file.
- [x] T012 CLAUDE.md skill table rows for `/name` (flags) and `/chargen` (scripted naming); note the engine's private lists are gone.

## Phase 6 - Sweep and ship (constitution VI, XIII)

- [x] T013 End-to-end: run the `/chargen` Step 2 script for real with a pinned gender and a set of 3 (no upload) - names distinct, gender honored, no OP call from the engine. Verify by output.
- [x] T014 Final gate: `make done` -> gate green, 614 passed, 100% coverage (1,460 stmts), 1m24s wall; `pytest .claude/skills/name -n auto` -> 83 passed (baseline 89 included 6 scraper tests, deleted with the scraper; every surviving test passes; zero new failures).
- [x] T015 Commit in the clone; `scripts/sync-with-main.sh done`; report to the GM including the accepted 862 -> 200 supply drop for the pending pool-size decision.

## Closing notes (2026-08-25)

- Reference artifacts: `chargen/test_namepool.py` (10 passed), then `pick_name.py --bank 3 --avoid Izumi` against the live cache (117 roster names, 3+3 labeled names, no WARNING), then the engine end-to-end: three `Samurai(base_rank=3, clan='wasp', gender='female', avoid=...)` -> Tsuruchi Wadoko / Yakumo / Enishi, all female on the first roll, mutually distinct under the set rule, none too similar to the 117 used names, `refresh_if_stale()` a no-op on a fresh cache (no network from the engine).
- Defect found and fixed under XIV while proving T008: `refresh_if_stale` wrote an EMPTY cache when the OAuth listing came back empty (the clone had no `development-secrets.ini`), and that empty file then looked fresh for an hour with every name looking free. An empty listing now writes nothing; test added. `campaign.used_names` also warns on an empty roster.
- Accepted and reported: the engine's raw supply drops 862 -> 200 (the private lists are deleted); ~180 usable against today's roster. For the GM's pending pool-size decision (item 3).
