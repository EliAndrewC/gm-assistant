# Research: /synthesize skill for existing Obsidian Portal NPCs

Phase 0 decisions. No `NEEDS CLARIFICATION` markers remained from the spec (the
three product decisions were settled with the GM before specification); the items
below are the technical unknowns resolved by direct investigation of the live OP
API and the existing codebase during the pre-spec exploration.

## D1 - Where the one-line summary ("tagline") lives, and how to read it

- **Decision**: Read the tagline by fetching the character's OP page HTML through
  the existing authenticated browser session (`op._get_browser_session`) and
  parsing the `<div class='tagline'> <p> <em>...</em> </p> </div>` element.
- **Rationale**: Empirically confirmed live - the OAuth JSON API (both the list
  and detail endpoints) returns a fixed field set (`name`, `tags`, `description`,
  `bio`, `game_master_info`, ...) with **no** tagline, while the authenticated
  page returns HTTP 200 with the tagline present verbatim
  (`<em>drinking companion of Kyoma</em>`). `op.update_character` accepts a
  `tagline` field on PATCH, confirming OP stores it first-class; the GET simply
  omits it.
- **Alternatives considered**: (a) OAuth API only - rejected, it cannot see the
  tagline, so the motivating example fails. (b) Unauthenticated WebFetch of the
  public URL - rejected, the private campaign returns 403.

## D2 - Fetch/parse split for testability

- **Decision**: `op.py` gets a thin `fetch_character_page(url) -> str | None`
  boundary function (fail-soft, returns page HTML or None); the tagline
  extraction is a pure function `opsynth.parse_tagline(html) -> str` tested
  against a saved HTML fixture.
- **Rationale**: Constitution X.5 - external boundaries tested via saved
  fixtures, pure logic at 100% coverage. Keeping the regex/parse out of the
  network call makes the parse fully unit-testable and the fetch a trivial
  boundary.
- **Alternatives considered**: fetch-and-parse in one `op.py` function - rejected,
  it buries testable parsing logic behind the network boundary.

## D3 - Caste inference for the per-caste supplement

- **Decision**: Infer caste from the character's tags and GM notes with a small
  ordered ruleset: monastic markers (an "Order of ..." tag, "monk"/"temple"/
  "abbot"/"shugenja"/"priest" in tags or notes) -> Monk; explicit peasant markers
  ("peasant"/"heimin"/"ashigaru"/"farmer"/"servant") -> Peasant; otherwise
  Samurai. State the inferred caste to the GM; the "generate another" path lets
  them override.
- **Rationale**: The campaign cast is overwhelmingly samurai, so Samurai is the
  safe default; the supplement only changes which extra setting sections are
  appended, so a wrong guess degrades gracefully (a monk read as samurai still
  gets a coherent, if less temple-flavored, backstory). Inference is pure logic,
  fully testable and parametrized over representative tag/note inputs.
- **Alternatives considered**: (a) always ask the GM - rejected as friction for
  the common case. (b) always Samurai - rejected, it silently mis-serves monks
  and peasants when the tags clearly say otherwise.

## D4 - Related-character ("also listed that way") lookup

- **Decision**: When the subject's tagline names another cast member, scan the
  other characters' taglines for that same name. Taglines are gathered into a
  gitignored `webapp/opcache/taglines.json` cache (id -> tagline), refreshed
  incrementally exactly like the existing character cache - one page fetch only
  for ids that are new or whose `updated_at` changed. The scan itself (matching a
  target name across cached taglines) is pure logic.
- **Rationale**: Reuses the proven opcache incremental pattern; the ~81-page
  cost is paid once and then only for changed characters, not on every run. The
  matching is deterministic and unit-testable. P3 is a `SHOULD`, so if the cache
  is empty (e.g. OP unreachable) the feature proceeds without related context.
- **Alternatives considered**: (a) fetch all 81 pages every run - rejected, too
  slow. (b) extend the main `characters.json` opcache to also store taglines -
  rejected for this feature to avoid changing the webapp's synthesis context;
  a separate cache keeps the change contained (a future consolidation is noted
  as out of scope).

## D5 - Idempotent save into GM-only notes

- **Decision**: Merge the backstory into `game_master_info` between two literal
  sentinel lines (`--- Synthesized Backstory (auto) ---` /
  `--- End Synthesized Backstory ---`). If both sentinels are already present,
  replace the text between them (inclusive); otherwise append the delimited block
  after the existing notes with a single blank-line separator. Pure string logic.
- **Rationale**: Satisfies FR-010/FR-011/SC-003/SC-004 - existing notes are
  preserved, re-runs produce exactly one synthesized section, and the markers are
  human-readable in the OP GM-notes view. Deterministic and fully unit-testable.
- **Alternatives considered**: (a) HTML-comment sentinels - rejected, OP Textile
  rendering of raw comments is unreliable. (b) replace-to-end-of-notes - rejected,
  it would eat any notes the GM added after the block.

## D6 - Skill-to-Python orchestration and inter-step state

- **Decision**: The skill markdown drives the flow by running short Python
  snippets via Bash that import the chargen modules, and by using the review
  review (two listed options plus a free-text changes box) between them. The
  "generate" step writes a small JSON
  handoff (character id, name, existing `game_master_info`, chosen caste, the
  backstory) to the session scratchpad; the "save" step reads it, merges, and
  PATCHes. Re-fetch of `game_master_info` immediately before the merge guards
  against staleness.
- **Rationale**: Each Bash call is a fresh process, so state must be passed via a
  file; the scratchpad is the designated place. Keeping orchestration in the
  skill (not Python) matches the project's "skills are orchestration, Python is
  logic" split and keeps the pure module free of I/O.
- **Alternatives considered**: a single long-running Python process - rejected,
  it cannot pause for the GM's menu choice mid-run.
