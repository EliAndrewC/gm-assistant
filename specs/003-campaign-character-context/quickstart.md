# Quickstart: Campaign Character Context

All commands from `webapp/`.

## Prerequisites
- Dev container with the l7r mount and `[obsidian_portal]` creds in `development-secrets.ini` (already configured).
- `[gemini] api_key` set. No new pip deps.

## Build order (refactor-style, test-first)
1. `chargen/op.py`: add `updated_at` to `existing_characters()`; add fail-soft `get_character_body(id)`.
2. `chargen/opcache.py` (test-first): `load_cache`/`save_cache`, `refresh` (list-diff), `assemble_context`, `get_campaign_context` (TTL + op + assemble), `refresh_cache_file` (build entry). Add `chargen/fixtures/` OP list + body fixtures.
3. `chargen/synthesis.py`: `build_prompt` inserts the `OTHER CAMPAIGN CHARACTERS` section + consistency instruction; excludes self by name.
4. `chargen/website.py`: `synthesize` gathers context (`exclude_name=full_name`), adds `context_count` to the envelope; context failure never fails the response.
5. `chargen/templates/index.html`: "N campaign characters in context" readout near the result.
6. `make prepare-deploy`: `python3 -c "import l7r; from chargen import opcache; opcache.refresh_cache_file()"` -> writes `webapp/opcache/characters.json`; Dockerfile `COPY opcache`; add `opcache/` to `.gitignore`; add `chargen.opcache` to the `cov` target.

## Verify
Python gate (Principle X), with the new module under coverage:
```
make done        # ruff + format + mypy --strict + pytest + 100% cov (incl. chargen.opcache)
```
Boundary is fixture-tested; no network in tests.

UI (Principle I + VI) - the small readout:
```
# render the chargen page, reveal the synthesis result with a sample context_count,
# screenshot + DOM-audit at GM-100/200/tablet/mobile (zero issues) + frontend-review pass
```

Live smokes:
- `opcache.refresh_cache_file()` populates `webapp/opcache/characters.json` from OP (first run = full pull; re-run = incremental, only-changed bodies).
- `get_campaign_context('Some New Name')` returns a non-empty block + count > 0; a named existing character appears in it and is excluded when it IS the name passed.
- Simulate OP down (creds unset / network blocked): `get_campaign_context(...)` returns `('', 0)` and `synthesize` still returns a backstory.
- End-to-end: synthesize with a steering note naming an existing character; confirm the result reflects that character's real backstory.

## Deploy
`make deploy` (runs `make done` + `prepare-deploy` incl. the cache refresh + `flyctl deploy --remote-only`). The bundled `opcache/characters.json` is the cold-start base; runtime refreshes it in-memory against OP.
