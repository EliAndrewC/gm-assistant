# Phase 0 Research: Campaign Character Context

Design decisions. No `NEEDS CLARIFICATION` remained; the OP facts were established by live probe (see spec Assumptions).

## D1. Cache format + location
**Decision**: `webapp/opcache/characters.json` - a JSON object keyed by character id, each value `{updated_at, name, tags, bio, game_master_info}`. Gitignored. Resolved by the module relative to itself (`chargen/../opcache`), so it's `webapp/opcache/` in dev and `/app/opcache/` in the image - same trick `brief.py` uses for the corpus bundle.
**Rationale**: one small file, easy to bundle + load; id keys make incremental diffing and dedup trivial.

## D2. Incremental refresh algorithm
**Decision**: `refresh(cache, list_fn, body_fn)` (pure, injected fetchers):
1. `entries = list_fn()` - all characters with `id` + `updated_at` (+ name, tags).
2. For each entry: if id absent from cache OR normalized `updated_at` differs, call `body_fn(id)` and store the fresh body; else keep cached.
3. Drop cached ids not present in `entries` (deletes).
Return `(new_cache, stats)`. Normalize `updated_at` before comparing (list gives 20-char, body 25-char forms) - compare on a normalized prefix/parsed timestamp.
**Rationale**: one list call + body calls only for changed ids; matches the confirmed OP shape. Pure + injected => 100% testable with fixtures.

## D3. op.py additions (grace-listed boundary)
**Decision**: (a) add `updated_at` (and keep name/tags) to `existing_characters()`'s returned dicts - additive, low-risk; (b) add `get_character_body(character_id)` doing `GET /campaigns/{id}/characters/{cid}.json`, returning `{'bio','game_master_info','name','tags','updated_at'}` or `None` on failure. Both **fail soft**: catch/log and return `[]`/`None`, never raise to callers.
**Rationale**: keeps the try/except + network mess in the already-grace-listed module, so `opcache.py` stays broad-except-free (Principle X.7).

## D4. Graceful degradation
**Decision**: if `list_fn()` returns `[]` (OP down) the refresh is a no-op and the assembled context is whatever the cache already holds (possibly empty). `synthesize` proceeds regardless; a missing/empty context is normal, never an error. Contrast the corpus (`brief.py`), which fails loud.
**Rationale**: FR-007 - context is an enhancement; reliability of the core click must not regress.

## D5. Runtime TTL cache
**Decision**: module-level in-memory holder `{cache, assembled_at}`. `get_campaign_context(exclude_name)`: if within TTL (default 60s), reuse; else refresh via the op helpers, re-assemble, stamp. Load the bundled file as the base on first use. Never write the file at runtime (image FS is ephemeral); the file is only (re)written by the build-time refresh.
**Rationale**: re-rolls within a minute don't re-list; new saves are picked up on the next refresh (their `updated_at` bumps). Time is injectable for tests.

## D6. Prompt placement + instruction
**Decision**: `build_prompt` inserts an `# OTHER CAMPAIGN CHARACTERS` section between the SETTING BRIEF and the CHARACTER block, each character rendered as `## {name}` + tags + bio + gm_info. Add an INSTRUCTIONS bullet: keep this character consistent with those others, and when the GM's steering notes name one, ground the relationship in that character's stated backstory; do not contradict them.
**Rationale**: context before subject; explicit instruction turns passive context into active consistency (mirrors the calendar/honor lesson - the text alone isn't enough).

## D7. Excluding the character being generated
**Decision**: exclude by case-insensitive `full_name` match (the new character usually isn't saved yet, so no id). If an id is ever supplied, prefer id.
**Rationale**: avoids feeding a regenerated character its own prior backstory.

## D8. Boundary testing (fixtures)
**Decision**: save real OP responses under `chargen/fixtures/` (a list response + a couple of body responses). `test_opcache.py` drives `refresh`/`assemble`/`load`/`save` with injected `list_fn`/`body_fn` returning fixture data - 100% coverage, no network, no transport mocks.

## D9. Build-time refresh entry point
**Decision**: `opcache.refresh_cache_file()` - load the existing file, refresh via the real op helpers, write the file. `make prepare-deploy` calls it (`python3 -c "import l7r; from chargen import opcache; opcache.refresh_cache_file()"`). First run (no file) = full pull; later = incremental.
**Rationale**: reuses the same refresh logic for build and runtime; incremental as long as the prior gitignored file is present.

## D10. Scope + token budget
**Decision**: all campaign characters (minus self) in v1, as the GM asked. Note it grows with the cast; if the assembled block ever threatens the input budget, tag-scoping (tags are free in the list call) is the ready refinement - out of scope now. `log()` the character count so growth is visible.
**Rationale**: matches the GM's "pull everything"; the model + steering notes handle relevance; budget is ample today.
