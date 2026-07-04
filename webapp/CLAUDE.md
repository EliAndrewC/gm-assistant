# L5R NPC Generator - Project Persona

## System Role
You are an expert Python developer.  You are assisting in building a webapp to
generate NPCs for the Rokugan setting of the Legend of the Five Rings RPG.

## Environment & Commands
- **Python Version**: 3.13
- **Virtual Env**: `./env`
- **Install**: `./env/bin/pip install -r requirements.txt` (Note: Use pip-compile via requirements.in)
- **Run Server**: `./env/bin/cherryd --import chargen` (Runs at http://127.0.0.1:8080)
- **Tests**: `./env/bin/pytest` (Standard location: /tests)

## Technical Constraints
- **Configuration**: Use `ConfigObj`. Validation is in `chargen/configspec.ini`. Never hardcode constants that belong in config.

## Coding Style
- Follow the existing pattern in `character.py` for class inheritance (`Samurai`, `Monk`, `Peasant`).
- Use the `weighted_choice` utility for randomizing attributes based on config weights.
- Ensure `to_dict()` is updated if new character attributes are added.
- Use single quotes for strings and triple-double-quotes for docstrings.

## Synthesize Backstory (shipped)

The chargen "Synthesize Backstory" button turns a generated character's traits
into a 1-3 paragraph prose gestalt via a Gemini text model (the text twin of the
AI portrait button), with re-roll and GM steering notes.

A blind evaluation chose the **full canonical corpus** as the prompt: the design
brief (`chargen/synthesis_brief.md`: low-fantasy ethos, the conviction-not-virtue
honor model, the good-vs-good conflict guidance, the calendar date-anchoring
instruction) + the "The Great Clans" framing + `chargen/flavor_clans.md` + l7r.md
+ budgets.md. Model: `gemini-3.1-pro-preview` (Pro, not Flash; configurable via
`[gemini] text_model`). One cost trim rides on top of the full-corpus decision:
prompt-irrelevant sections are excised at prompt-build time - never from the
canonical files themselves - via `_EXCLUDED_L7R_SECTIONS` (Moto/gaijin material,
past-campaign writeups, two sections duplicated in the OP campaign cast),
`_EXCLUDED_BUDGET_SECTIONS`, and `_PRUNED_BUDGET_SECTIONS` (pure-calculation
budgets.md sections; "Domain" keeps its "Discretionary budgets" subsection) in
`chargen/brief.py`, whose comments record the reasoning and measured savings. A
missing excluded heading fails loud (a renamed section in l7r.md or budgets.md
must not silently re-inflate the prompt). Removal uses merged-span
`remove_sections` (bounds computed on the original text), so excluded and
caste-conditional titles may nest inside one another in any listing order.

**Per-caste prompts + prompt-layer caching order.** `_CASTE_L7R_SECTIONS` and
`_CASTE_BUDGET_SECTIONS` in `chargen/brief.py` map type-dropdown values to
sections excised from the base corpus for EVERYONE (the base stays
byte-identical across castes) and re-appended via `brief.build_caste_supplement`
only for that type - monk (temple internals, soothsaying, oaths/vows), peasant
(the Peasant Campaign), and samurai (government structure, rank accordances,
legion backstories, the Damasu Domain, and the budgets.md ministry/
office-holder/Imperial-budget machinery). Supplement extraction strips foreign
(other-caste or excluded) sections nested inside extracted blocks. With this
split, all three caste prompts sit under Gemini's 200k long-context boundary.
The prompt layers in `synthesis.build_prompt` are ordered most-stable-first as a
caching contract (Gemini implicit prefix caching bills only up to the first
divergence): (1) instructions + base corpus, (2) process-start cast snapshot,
(3) caste supplement, (4) runtime-discovered cast additions
(`opcache.get_campaign_context` returns the snapshot/recent blocks split on
`_baseline_ids` = ids in the cache file at process start), (5) the subject
character + steering notes. Do not reorder these layers or insert variable
content into the middle; the frontend sends `character_type` (the type dropdown
value) with the synthesize POST.

**Per-click cost**: the token-count and dollar-cost table (per caste, for the
production `gemini-3.1-pro-preview` and the `gemini-3.5-flash` alternative,
cold vs. cached) lives in [`chargen/synthesis_costs.md`](chargen/synthesis_costs.md),
with the free `count_tokens` script to regenerate it after the corpus grows.
As of 2026-07 a synthesis runs ~$0.27-$0.42 cold and ~$0.06-$0.07 warm on Pro;
that doc has the current authoritative numbers and the "why not switch to Flash"
rationale.

- **Brief assembly**: `chargen/brief.py` (`build_full_brief`), the compliant,
  100%-covered module; `chargen/synthesis.py` `load_brief` delegates to it.
- **Corpus resolution**: `$L7R_SETTING_DIR` -> dev mount `/host-l7r-repo/setting`
  -> bundled `webapp/setting/`. The deployed app has no mount, so `make
  prepare-deploy` snapshots l7r.md + budgets.md into gitignored `webapp/setting/`
  (the Dockerfile copies it). A missing corpus fails loud - never a thin fallback.
- **Route + UI**: `@ajax synthesize` in `chargen/website.py`; the control lives in
  `chargen/templates/index.html`.
- **Campaign character context**: `chargen/opcache.py` (compliant, 100%-covered)
  keeps an id-keyed cache of the campaign's OP characters and injects an
  `OTHER CAMPAIGN CHARACTERS` block into the prompt so new backstories stay
  consistent with the cast and honor steering-note references to them. Refresh is
  incremental (1 OP list call + body fetches only for new/changed ids, via
  fail-soft `op.existing_characters` / `op.get_character_body`); cache is
  gitignored `webapp/opcache/characters.json`, refreshed + bundled by
  `make prepare-deploy`, refreshed in-memory at runtime (short TTL). Non-fatal:
  OP down -> 0 characters in context, synthesis still runs (the route reports
  `context_count`, shown by the UI). See `specs/003-campaign-character-context/`.
  **Cache-order contract** (for Gemini implicit prefix caching): `opcache.refresh`
  keeps prior entries in their established order regardless of OP listing order
  and appends new characters at the end, so the mid-prompt cast block perturbs
  the smallest possible suffix of the prompt when the roster changes. Do not
  "helpfully" sort or reorder it.

See `specs/002-synthesize-backstory/` for the synthesis feature spec/plan/tasks.

**Chat-driven twin - the `/synthesize` skill.** `.claude/skills/synthesize/`
lets the GM synthesize a backstory for an NPC that already exists on Obsidian
Portal, from a Claude Code session, reusing this exact synthesis stack. New pure
logic lives in `chargen/opsynth.py` (100%-covered, mypy-strict): name matching,
caste inference, OP-page tagline parsing, related-cast lookup, incremental
tagline cache, and an idempotent `merge_backstory` that splices the result into
GM-only notes between `--- Synthesized Backstory (auto) ---` sentinels without
clobbering existing notes. The one-line summary ("tagline") it reads is NOT in
the OAuth JSON API - it only appears on the character page HTML - so
`op.fetch_character_page` (fail-soft boundary) fetches the page and
`opsynth.parse_tagline` extracts it. See `specs/004-synthesize-op-npc/`.
