# Contract: `chargen.opcache` + synthesize-response extension

## Module API (`chargen/opcache.py`, compliant/typed/100%-covered)

Pure logic (injected fetchers - no network, fully unit-tested):
- `load_cache(path: Path) -> dict[str, dict]` - read the JSON cache; `{}` if missing or malformed (logged).
- `save_cache(path: Path, cache: dict[str, dict]) -> None` - write the JSON cache.
- `refresh(cache, list_fn, body_fn) -> tuple[dict[str, dict], RefreshStats]` - list-diff on `updated_at`; body-fetch only new/changed ids; drop deleted. `list_fn() -> list[dict]` (each has id, updated_at, name, tags); `body_fn(id) -> dict | None` (bio, game_master_info, name, tags, updated_at; `None` = fetch failed, keep prior if any).
- `assemble_context(cache, exclude_name=None) -> tuple[str, int]` - the `# OTHER CAMPAIGN CHARACTERS` block + count; `('', 0)` when empty/all-excluded. Case-insensitive name exclusion.

Orchestration (thin; op boundary + time injected for tests):
- `get_campaign_context(exclude_name=None, *, now=None) -> tuple[str, int]` - TTL-guarded in-memory refresh via op helpers, then `assemble_context`. Never raises; OP failure -> uses held/empty cache.
- `refresh_cache_file() -> RefreshStats` - build-time: load file, refresh via op helpers, save file. Called by `make prepare-deploy`.

## op.py helpers (grace-listed boundary, fail-soft)
- `existing_characters()` - extended to include `updated_at` per character (still returns `[]` on failure).
- `get_character_body(character_id) -> dict | None` - single-character GET; `{bio, game_master_info, name, tags, updated_at}` or `None` on failure (logged, never raises).

## Prompt contract (`synthesis.build_prompt`)
- Inserts `# OTHER CAMPAIGN CHARACTERS\n\n<block>` between `# SETTING BRIEF` and `# CHARACTER` when the block is non-empty; omits it entirely when empty.
- Adds an INSTRUCTIONS bullet: stay consistent with those characters; honor steering-note references to them grounded in their stated backstories; never contradict them.
- All prior behavior (honor model, calendar, rank-not-office, summary/tags, steering) unchanged.

## synthesize route contract (`website.py`)
- Gathers context via `opcache.get_campaign_context(exclude_name=<full_name>)`, passes the text into synthesis, and returns it in the prompt.
- Response envelope gains `context_count` (int). Success: `{ok: true, backstory, error: null, context_count: N}`. Gathering context never turns a success into a failure.

## UI contract (`templates/index.html`)
- After a successful synthesis, show "N campaign characters in context" near the Backstory result (reads 0 when OP is down / cache empty).

## Test contract
- `refresh`/`assemble`/`load`/`save`/`get_campaign_context`/`refresh_cache_file`: 100% covered via injected fetchers + saved OP fixtures under `chargen/fixtures/`; time injected for the TTL path. No transport mocks.
