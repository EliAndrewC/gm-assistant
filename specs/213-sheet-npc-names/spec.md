# Feature Specification: `GET /api/names` - name suggestions for the character sheet's generated NPCs

**Feature Directory**: `specs/213-sheet-npc-names`

**Created**: 2026-09-28

**Status**: Specified.

**Input**: the GM's decisions D10, D16, D26 and design section 4.6 of the character-sheet repository's
`combat-design/design.md`, verbatim in [gm-request.md](gm-request.md).

## Why

The character-sheet app is gaining a combat tracker that generates NPCs for the GM (Wave Men,
samurai-school opponents). The GM wants their names suggested "the way gm-assistant does it" (D10):
from gm-assistant's name pool, never a name already used in the campaign, never one too similar to
one. The used-name set - the Obsidian Portal roster, the GM's manual list, the campaign's lineage
names, the sheet app's own grouped characters - is assembled only here (`opcache.used_given_names`),
so the picking stays here and the sheet app asks for names over HTTP (4.6).

The sheet side is already written (its `app/services/npc_names.py`): it calls
`GET {GM_ASSISTANT_URL}/api/names?count=N&peasant=true|false[&avoid=A,B]` with
`Authorization: Bearer <token>`, a 12 second timeout, and reads `{"names": [...]}` from a 200. Any
other outcome yields no names and the sheet falls back to "Wave Man 1..N" (4.6, second bullet).

## User Scenarios & Testing

### User Story 1 - the GM generates NPCs and they arrive named (P1)

1. **Given** the GM generates four Wave Men, **When** the sheet asks for 4 peasant names, **Then** it
   receives four male given names from the peasant-flagged part of the pool, none used in the
   campaign or too similar to a used one, and no two of them in conflict with each other.
2. **Given** the GM generates three samurai-school NPCs, **When** the sheet asks for 3 non-peasant
   names, **Then** it receives three male given names, every one samurai-eligible (a non-peasant entry,
   or a peasant-flagged entry marked `samurai: true`), given name
   only - no family name (D26).
3. **Given** the sheet already holds names for this batch (the GM asked for "another" for one NPC),
   **When** it passes them as `avoid`, **Then** no returned name conflicts with them.

### User Story 2 - names used by earlier fights stay used (P1)

1. **Given** an NPC generated last week is on the sheet app (flagged `is_npc` in its
   `GET /api/characters`), **When** names are next requested and the used-name cache has gone
   stale, **Then** that NPC's given name counts as used (4.6, third bullet).
2. **Given** a character was added on Obsidian Portal since the last refresh, **When** the cache is
   stale at request time, **Then** the endpoint refreshes it and the new name counts as used (4.6:
   "refreshes the used-name cache when stale").

### User Story 3 - only the sheet app can ask (P1)

1. **Given** a request with no bearer token or the wrong one, **Then** 401 and no names.
2. **Given** gm-assistant has no `names_token` configured, **Then** 503 and no names, whatever is
   presented - the endpoint is closed until the GM configures it.

### Edge cases

- **The pool runs out** for the requested caste under the exclusions: fewer names than asked, still
  a 200. The sheet already copes with a short list.
- **Obsidian Portal or the sheet app is unreachable during a refresh**: the refresh fails, and the
  request is answered from the last cache. A refresh failure never turns into an error response.
- **A refresh is slow** (a cold machine, many changed records): the request waits for it to finish.
  If that runs past the sheet's 12 seconds, the sheet uses its "Wave Man 1..N" fallback - the
  outcome the GM specified for gm-assistant being asleep or down (Decision 1).

## Requirements

- **FR-001** `GET /api/names` on the CherryPy app, answering JSON on every path (success and error).
- **FR-002** Auth: the secret is `[character_sheet] names_token` in `development-secrets.ini`. It is
  accepted ONLY as `Authorization: Bearer <token>` and compared in constant time
  (`hmac.compare_digest`). Unset or blank -> `503 {"error": ...}`. Configured, and the header missing
  or wrong -> `401 {"error": ...}`. The session-cookie auth tool does not gate `/api` (it stays at
  `min_role` anonymous there); the bearer check in the handler is the whole gate.
- **FR-003** Male names only (D16). The endpoint takes no gender parameter.
- **FR-004** `peasant=true` draws with `namepool.pick_name(..., peasant=True)` - only
  peasant-flagged entries (D26, Wave Men). `peasant=false` draws ONLY from samurai-eligible entries:
  non-peasant, or peasant-flagged with `samurai: true` (D26). It does NOT use `pick_name`'s
  `peasant=False` mode, because that mode falls back to the whole pool, peasant-only names included,
  once the samurai-eligible entries are exhausted; here, running out is exhaustion (FR-008). Absent
  means `false`. Any other value -> `400 {"error": ...}`.
- **FR-005** Each name is a given name only, as the pool stores it (D26).
- **FR-006** `count=N` names, built the way `l7r/repl/names.py` builds a batch: repeated
  `pick_name('m', pool, used, [*avoid, *picks], ...)` over the caste set FR-004 defines (never
  `pick_name`'s `peasant=False` fallback mode), where `used` is
  `opcache.used_given_names()`. That applies both the used-name rule (used names and names too
  similar to them) and the within-batch set-conflict rule (4.6, "applies both"). `count` absent means
  1; it is clamped to 1..30; a non-integer -> `400 {"error": ...}`.
- **FR-007** `avoid=A,B` (comma-separated; entries stripped, empties dropped) is added to the
  within-batch exclusions, so a replacement name cannot conflict with names the sheet already holds.
- **FR-008** `NamePoolExhausted` ends the batch early: `200 {"names": [...]}` with the names picked
  so far (possibly none).
- **FR-009** Freshness: before picking, the used-name cache is refreshed if older than the cache's
  own default window (`opcache.refresh_if_stale`'s one hour), under a module-level lock so
  concurrent requests do not refresh twice. The request waits for the refresh to finish, then picks.
  A refresh failure is logged and never fails the request: the names are picked against the last
  cache (Decision 1).
- **FR-010** The sheet app's NPCs count as used: the character-sheet roster cache
  (`chargen/sheetroster.py`), refreshed on the same cadence, also records the names of every
  character the sheet's `GET /api/characters` flags `is_npc`, read with the existing
  `[character_sheet] roll_query_token`, and `used_given_names()` includes their given names. A
  failed fetch keeps the previously cached NPC names; it never empties them. This serves every
  consumer of the used-name set, not just this endpoint (4.6 says the set, not the endpoint).
- **FR-011** `development-secrets.ini.example` gains `names_token =` (empty) under
  `[character_sheet]`, commented as INBOUND (the sheet app presents it to us), unlike that section's
  outbound tokens. No real value is written anywhere by this feature; the GM sets it and deploys.
- **FR-012** The route lists in `app.py`'s module docstring and CLAUDE.md name the endpoint.
- **FR-013** Tests never reach the network: the new sheet API fetch is refused by the same autouse
  fixtures that refuse the index scrape, and the endpoint's tests patch the refresh.

## Decisions (each made by the session, each cheap to change)

1. **Refresh when stale, synchronously, under a lock; answer from the last cache only when the
   refresh FAILS.** 4.6 says the endpoint "refreshes the used-name cache when stale", and this is
   that. What it costs, observably: the deployed app scales to zero (`min_machines_running = 0`)
   and has no volume, so every cold boot starts from the deploy-time cache, which is weeks old -
   the first request of a game night is a cold boot AND a refresh (one Obsidian Portal listing, one
   body per changed character, two sheet-app fetches). If that runs past the sheet's 12 second
   timeout, the sheet uses "Wave Man 1..N" for that batch, which is the fallback the GM specified
   for gm-assistant being asleep or down; the refresh still completes, so the GM's next "ask for
   another" gets real names. Priced and declined: (a) the bundled deploy-time cache, never
   refreshed - fastest, but every name added since the deploy, last week's NPCs included, looks
   free, which is what D10 and 4.6's third bullet exist to prevent; (b) a bounded wait (answer from
   the cache on disk after ~5 s, refresh behind) - drafted first and struck by the fidelity review:
   the cache on disk in exactly that case is the weeks-old one, so it would re-suggest last week's
   NPCs, and it swaps the GM's chosen fallback for the session's own trade; (c) serve stale and
   refresh behind, always - the same defect as (b), every time. If cold-boot latency proves to be
   a problem in play, the fix that does not depart from 4.6 is making the refresh faster (a volume
   for the cache, or a refresh at startup), not answering without it.
2. **The endpoint's own secret, not the sheet's read token reused.** `roll_query_token` is a secret
   the SHEET issues and gm-assistant presents (outbound); this one gm-assistant issues and the sheet
   presents (inbound). Reusing one value for both directions would let either app's leak open the
   other.
3. **Bad parameters are a 400, not silently defaulted.** The only client sends well-formed values;
   a malformed one is a bug in a client, and a 400 says so where a quiet default would hide it.
   `count` out of range is clamped rather than refused, because it is well-formed.
4. **NPC names come from `/api/characters`, not a new sheet endpoint.** The sheet already lists them
   flagged `is_npc` (4.6), and the REPL already reads that endpoint with `roll_query_token`.
5. **Names only, no meanings, in the response.** The client reads a list of strings; the explanation
   is available on `/names` for a GM who wants it.

## Success criteria

- **SC-001** With the token configured, the sheet's `fetch_names(4, peasant=True)` returns four
  distinct, unused, male, peasant-pool names.
- **SC-002** A request that cannot be served correctly never returns names: 401 / 503 / 400 carry
  `{"error": ...}` and no `names` key.
- **SC-003** No request fails because Obsidian Portal or the sheet app is down.
- **SC-004** An `is_npc` character's given name on the sheet is excluded from later suggestions once
  the roster cache has refreshed.

## Review history

- **Round 1 - CHANGES REQUIRED** (2026-09-28). The quotation in gm-request.md was verified word for
  word against the character-sheet design file. Every clause was carried except two departures.
  (1) FR-004 used `pick_name(peasant=False)`, which falls back to the whole pool - peasant-only
  names included - once the samurai-eligible entries run out, against D26's "samurai-eligible
  personal name only"; now a strict samurai-eligible draw where running out is exhaustion.
  (2) Decision 1 bounded the refresh wait at 5 seconds and then answered from the cache on disk -
  judged NOT LEGITIMATE as an exception to 4.6's "refreshes the used-name cache when stale": on a
  cold boot the cache on disk is the weeks-old deploy-time one, so it would re-suggest last week's
  NPCs, and the GM already chose the outcome for a slow or sleeping gm-assistant ("Wave Man
  1..N"). The bound is now a declined alternative in Decision 1. FR-010 (the sheet's `is_npc`
  names) was confirmed in scope by 4.6's third bullet.
- **Round 2 - FAITHFUL** (2026-09-28). Both changes confirmed; the whole spec re-walked against
  the request with nothing missing, unrequested or contradicting. One drafting note - FR-006 still
  named `pick_name(..., peasant=...)` - fixed after the verdict so the samurai branch cannot drift
  back onto the fallback mode.
