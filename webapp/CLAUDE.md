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
instruction) + the "The Great Clans" framing + `chargen/flavor_clans.md` + the
entire l7r.md + budgets.md. Model: `gemini-3.1-pro-preview` (Pro, not Flash;
configurable via `[gemini] text_model`).

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

See `specs/002-synthesize-backstory/` for the synthesis feature spec/plan/tasks.
