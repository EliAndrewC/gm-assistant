# Phase 1 Data Model: Campaign Character Context

No database. In-memory + one JSON cache file.

## Cached character (one entry)
- `updated_at` (str): OP change marker; drives incremental refresh (normalize before comparing - list vs body formats differ).
- `name` (str): display name.
- `tags` (list[str]): clan/role/lineage/location tags (from the list call; free).
- `bio` (str): public biography (may be empty).
- `game_master_info` (str): GM-only notes (may be empty).

## Character cache
- Shape: `dict[str, CachedCharacter]` keyed by OP character id.
- Persisted as `webapp/opcache/characters.json` (gitignored, bundled at build).
- Refresh (pure, injected fetchers): list -> for each id, fetch body iff new/changed -> drop deleted -> return `(cache, stats)` where stats = counts of fetched/kept/dropped.
- Load/save: tolerant of a missing file (returns `{}`); tolerant of malformed file (treated as empty, logged) so a corrupt cache never blocks synthesis.

## Campaign context block (assembled)
- Input: the cache + the name to exclude (the character being generated).
- Output: `(text, count)` where `text` is the `# OTHER CAMPAIGN CHARACTERS` prompt section (each entry: `## {name}`, tags line, bio, gm_info) and `count` is how many characters were included.
- Empty cache (or all excluded) -> `('', 0)`; `build_prompt` then omits the section entirely.

## Runtime context holder (in-memory, per instance)
- `{cache, assembled_at}` with a TTL. `get_campaign_context(exclude_name, now)`:
  - within TTL -> reuse the held cache;
  - else -> load base file (first time), refresh via op helpers, hold, stamp `assembled_at = now`;
  - then assemble + return `(text, count)`.
- OP failure -> refresh is a no-op; whatever is held (possibly empty) is used. Never raises.

## Synthesize response (extended)
- Existing: `{ok, backstory, error}`.
- Added: `context_count` (int) - campaign characters included, surfaced in the UI readout.
