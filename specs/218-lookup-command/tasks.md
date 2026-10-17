# Tasks 218: `/look-up`

Each task is marked done only when its verification has run.

## Phase 1 - the pipeline, offline

- [ ] T001 Probe each Gemini tier with a one-line REST call; record the working thinking-parameter
      shape per generation and the prices with their sources in `research.md`.
- [ ] T002 `l7r/lookup/glossary.py`: load and validate `glossary.jsonl` (required fields, known
      kinds and scopes, http(s) links only, no duplicate term+scope), render compact prompt text.
      Tests.
- [ ] T003 `l7r/lookup/sources.py`: split `l7r.md` and rules files into heading sections, hash
      them, report the sections that are stale or new against the glossary's recorded `sha`s.
      Tests on fixture markdown.
- [ ] T004 `l7r/lookup/profiles.py`: clan-of-origin derivation (test against every school heading
      in the rules), sheet-API to profile mapping (fixture payload), public sheet page parse for
      school, Dan and lineage (fixture HTML), and profile text for the prompt. Tests.
- [ ] T005 `l7r/lookup/links.py`: roster from the OP character listing and the profiles (GM-only
      excluded), the mechanical linker (full name, unique given name, longest match, once per
      person, never inside an existing link), and the filter that strips unknown addresses.
      Tests, including the filter proven to fire.
- [ ] T006 `l7r/lookup/gemini.py`: REST call, usage to cost against the price table, timeout and
      error mapping; ConfigObj secrets read (quoted key tested). Tests via an injected opener.
- [ ] T007 `l7r/lookup/ledger.py`: daily ceiling and query log. Tests, including the ceiling
      proven to fire and the day rollover.
- [ ] T008 `l7r/lookup/campaign.py` + `service.py`: the Wasp brief, prompt assembly in
      cache-friendly order, `answer()` end to end with every boundary injected; the
      ceiling, failure and not-configured replies. Tests.
- [ ] T009 First-pass glossary: the Wasp campaign sections, government/castes/ranks, the
      Fortunes and clan patrons, rule terms, the 17 public wiki pages, and the Wasp NPCs' public
      bios.
- [ ] T010 Evaluation: `eval/questions.jsonl` (60+, the GM's five verbatim), the runner, and
      mechanical scoring. Tests of the scorer.
- [ ] T011 First evaluation run on one cheap tier; read every failing answer; fix the glossary,
      the prompt or the grading as each case warrants.

## Phase 2 - Discord

- [ ] T012 `gateway.py`: the interaction callback (deferred, ephemeral) and the PATCH of the
      original (suppress embeds, no mentions). Tests via an injected opener.
- [ ] T013 `responder.py`: dispatch `INTERACTION_CREATE` for `look-up`, run in
      `asyncio.to_thread`, ignore bots, de-duplicate replayed interaction ids, and survive
      4xx from expired tokens. Tests with the fake socket.
- [ ] T014 `scripts/register_lookup_command.py`: idempotent guild command PUT.
- [ ] T015 Deploy: the deploy script ships `l7r/lookup/` and its baked roster and profiles, plus
      `[lookup] gemini_api_key` only if present, with no fallback to `[gemini] api_key`. The bot
      runs without `/look-up` when the key is absent.
- [ ] T016 Live proof from this container: register the command, run the responder locally,
      ask the GM's examples in Discord, confirm the reply is private, links work, and cost is
      logged.

## Phase 3 - the pool

- [ ] T017 Sweep the rest of `l7r.md`, the rules and the remaining public character bios into
      the glossary. Staleness report shows nothing stale.
- [ ] T018 Full evaluation across the five tiers; record the results; choose the default by
      the Story 7 rule; set it in `development-defaults.ini`.
- [ ] T019 `l7r/lookup/CLAUDE.md` (index, glossary refresh procedure, how to test), the mention
      `CLAUDE.md` deployment notes, and the root `CLAUDE.md` key paths.
- [ ] T020 `make done` green; stop-work procedure.
