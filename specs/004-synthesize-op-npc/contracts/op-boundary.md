# Contract: `chargen/op.py` boundary additions (fail-soft, fixture-tested)

These are the only new network-touching functions. They follow the existing
`op.py` grace-listed style: catch, log, and return a safe value; never raise into
callers. Tested against saved fixtures (a real OP page HTML and character JSON),
not transport-layer mocks.

## `fetch_character_page(character_url) -> str | None`

- GETs the authenticated character page via `_get_browser_session()`.
- Returns the page HTML on 200; `None` on any failure (logged). Never raises.
- The tagline is parsed from this HTML by `opsynth.parse_tagline` (pure).

## `refresh_taglines(cache, characters, page_fetch, parse) -> tuple[dict, stats]`

- Incremental, mirroring `opcache.refresh`: for each character, fetch+parse a
  tagline only when the id is new or its `updated_at` changed; keep unchanged;
  drop absent ids. `page_fetch`/`parse` are injected so the logic is testable
  without network (the injection seam is pure; the default wiring uses
  `fetch_character_page` + `opsynth.parse_tagline`).
- Returns `(new_cache, {fetched, kept, dropped})`.
- NOTE: the *iteration/merge* logic is pure and unit-tested; only the injected
  `page_fetch` default is the boundary.

## Reused as-is (no change)

- `existing_characters()` -> list of `{id, slug, name, ...}` (name matching).
- `get_character_body(id)` -> `{name, tags, bio, description?, game_master_info, updated_at}`.
- `update_character(id, game_master_info=...)` -> PATCH the merged notes on save.

## `get_character_body` note

`get_character_body` currently returns `name, tags, bio, game_master_info,
updated_at` but drops `description`. Add `description` to its projection (a
one-line, backward-compatible addition) so the public prose is available to
synthesis. Covered by the existing fixture-based boundary test with the field
added to the fixture assertion.
