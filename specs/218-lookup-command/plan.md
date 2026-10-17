# Plan 218: `/look-up`

**Spec**: [spec.md](spec.md). **Created**: 2026-10-17.

## Summary

A new package `webapp/l7r/lookup/` holds the pure logic:
- the glossary (data)
- the prompt builder
- the player profiles
- the mechanical name linker and the link filter
- the Gemini REST client
- the spending ledger
- the evaluation runner

The existing mention responder (`webapp/l7r/mention/`) learns one new gateway event,
`INTERACTION_CREATE`. When the event is `/look-up`, it acknowledges with a private deferred
response, runs the lookup in a worker thread, and edits the private placeholder with the answer.
The glossary is a checked-in JSONL file that Claude writes in-session.

## Technical context

- **Language**: Python 3.14, the repository's pin. The new code is held to the pure-logic bar:
  `mypy --strict` and 100% coverage.
- **Gemini over plain REST** (`urllib`, `generativelanguage.googleapis.com/v1beta/models/
  <model>:generateContent`), **not** the `google-genai` SDK. The bot's box is a 512 MB Lightsail
  nano that runs the responder in 21 MB on stdlib plus `websockets` and `configobj`. The SDK pulls
  in pydantic, httpx and more, so it would multiply the footprint for one POST. The webapp's
  `chargen/synthesis.py` keeps using the SDK; nothing there changes.
- **Discord interactions over the gateway.** The L7R GM Assistant application has no interactions
  endpoint URL (checked 2026-10-17: `interactions_endpoint_url` is `None`), so slash-command
  events arrive as `INTERACTION_CREATE` dispatches on the gateway connection the responder already
  holds. They need no extra intent.
  - **Answering** is `POST /interactions/{id}/{token}/callback` with type 5 (deferred) and flags
    64 (ephemeral), sent within Discord's 3-second limit. The lookup then runs, and
    `PATCH /webhooks/{application_id}/{token}/messages/@original` replaces the placeholder with
    the answer.
  - **Flags**: the PATCH carries flags 4 (SUPPRESS_EMBEDS), so links do not unfurl, and
    `allowed_mentions: {parse: []}`.
  - **Registration** is a guild command: `PUT /applications/{app}/guilds/745421621829042297/
    commands`. Guild commands appear instantly, where global ones can take an hour. A small
    script, `scripts/register_lookup_command.py`, does the PUT and is idempotent.
- **Command name**: `look-up`, the GM's spelling. Discord command names allow hyphens. It takes
  one required string option, `question`.

## Design decisions (each one resolved here, per the unattended-chain rule)

1. **The glossary format** is `webapp/l7r/lookup/glossary.jsonl`, one entry per line:

   ```
   {term, aliases[], kind, scope, reading, meaning, summary, related[], link, source}
   ```

   - **`scope`** is `world`, `wasp`, or another campaign's slug.
   - **`source`** is `{file, section, sha}`, where `sha` is the hash of the section text the entry
     was built from, as of the build.
   - **Why JSONL**: one line per entry diffs cleanly when a refresh touches a few entries, and a
     test can validate every line.

   The prompt renders the glossary as compact text, one entry per line, so the JSON key names do
   not cost tokens on every call.
2. **The staleness report** is `python3 -m l7r.lookup.sources --stale`. It splits `l7r.md` and
   the rules files into heading sections, hashes each one, and compares the hashes with the `sha`
   values recorded in the glossary. It lists sections that have changed or are new, plus the OP
   pages whose `updated_at` is newer than the glossary's build stamp. A Claude session rebuilding
   the glossary reads only those sections. The whole build procedure, written down for the next
   session, lives in `webapp/l7r/lookup/CLAUDE.md`.
3. **Player profiles** are built at deploy time, plus a live refresh:
   - **At deploy**: the character-sheet API (bearer token, local only) maps `owner_discord_id`
     to the non-NPC characters in the campaign's gaming groups. The groups are configuration:
     `[lookup] campaign_groups = Monday Group, Tuesday Group`. Each profile also takes the
     school, Dan and lineage from the character's public sheet page, and the clan of origin from
     the school.
   - **On the box**: the bot refreshes school and Dan from the public sheet page at most hourly
     (no token needed). The baked profile is the fallback if that fetch fails.
   - **Why**: the box deliberately holds no credential beyond what it must (see 6), and the
     sheet's bearer token reads every character, NPCs included.
4. **Clan of origin** is derived from the school's family, using the existing
   `l7r.mention.lore.topics.CLAN_FAMILIES` (the Great Clans). It is extended for the schools in
   `rules/11-non_pc_schools.md` (Kitsune: Fox, Suzume: Sparrow, Mantis Wave-Treader: Mantis) and
   for Tsuruchi (Wasp).
   - **Generic schools** (Courtier, Merchant, Priest, Shugenja, Brotherhood of Shinsei Monk) give
     **no** inferred clan, and the profile says "clan of origin not recorded". Inventing one would
     be guessing.
   - **The derivation is tested** against every school heading in `04-schools.md` and
     `11-non_pc_schools.md`, so a new school cannot silently fall through.
   - **Why reuse**: a second family table would drift from the first.
5. **The linker** works from the roster: every non-GM-only OP character (name, then address)
   plus each Wasp PC (OP page if one exists, otherwise sheet page). For each person it matches the
   full name, then the bare given name when that given name is unique in the roster. The longest
   match wins, so "Tsuruchi Kyoma" is never split into a link on "Kyoma". Text already inside a
   markdown link is left alone. Each person is linked once per reply, at the first mention.
   - **Why once**: repeated links are visual noise in a five-line reply, and the GM asked that a
     mentioned person be linked, not every occurrence.
6. **The link filter** strips any markdown link or bare URL whose address is not in the
   glossary's `link` set or the roster. The link text is kept as plain text.
7. **The prompt**, assembled in this order so the stable prefix is cached by Gemini's implicit
   prefix caching:
   1. instructions
   2. the Wasp campaign brief
   3. the glossary
   4. the asker's profile
   5. the question

   The **Wasp campaign brief** is a short hand-written block in the package: the PCs are Wasp
   marshals reporting to Tsuruchi Kyoma, the six domains, and the Three Man Alliance. "Our" and
   "we" mean the Wasp marshals.

   The **instructions** say:
   - read the question for what the asker means
   - answer in at most five short lines
   - use full names at least once
   - include a glossary entry's link when the question is about that topic, and never invent a
     link
   - say plainly when the glossary does not cover it, and never guess
   - prefer `wasp` and `world` scope over other campaigns' entries
8. **Cost and the ceiling.** Cost is computed from the response's `usageMetadata` (prompt,
   cached, candidates and thoughts token counts) against a price table in
   `development-defaults.ini` `[lookup_prices]`. The table is configuration because prices
   change (sources and the date checked are recorded in research.md). The ledger is a small JSON
   file on the box, `lookup-spend.json`, holding the day and the dollars spent. Over
   `[lookup] daily_ceiling_usd` (default 1.00), the bot replies privately that the lookup budget
   for today is spent. The query log is `lookup-log.jsonl`, gitignored.
9. **Secrets on the box.** The bot needs a Gemini key. The deploy script copies
   `[lookup] gemini_api_key` (a key dedicated to this bot) and **nothing else new**, and refuses
   to deploy the lookup without it. It never falls back to `[gemini] api_key`, which also pays for
   portraits and backstories. A fallback would silently ship the main key to an internet-facing
   box, the exact thing the deploy script's header forbids. The GM creates the dedicated key in AI
   Studio. Until it exists, the responder runs without `/look-up`, and the command answers "not
   configured" if registered.
10. **Thinking**: Flash-tier Gemini models may "think" by default, and thinking tokens bill as
    output. The client sends the lowest thinking setting each model accepts and records thought
    tokens, so the evaluation shows the cost honestly. Whether thinking improves correctness
    enough to pay for itself is measured as an evaluation variant, not assumed.

## Evaluation (Story 7)

- **Questions**: `webapp/l7r/lookup/eval/questions.jsonl`, at least 60 of them. Each has:

  ```
  {id, question, asker (sheet id or null), must[] (each a list of acceptable alternatives),
   links[] (required link slugs), answerable, note}
  ```
- **Runner**: `python3 -m l7r.lookup.eval --model M [--runs N]` writes
  `specs/218-lookup-command/eval/<model>-<date>.json` plus a markdown summary. It reports
  per-question pass/fail on facts and links, the abstain check, line count, cost, latency, and
  totals.
- **Scoring is mechanical**: case-insensitive match of each required fact's alternatives, with
  macrons and hyphens normalized. For an unanswerable question, the reply must contain an abstain
  phrase from a fixed list and none of the question's listed "invention bait" facts. After each
  run, Claude reads every failing answer, and fixes the scoring of any answer that is right but
  graded wrong (or wrong but graded right) in the question file. That pass is recorded.
  - **Why mechanical first**: it is reproducible and free, which is what makes it a regression
    test (Story 7.6). The human-level reading catches the mechanical grader's blind spots.
- **Tiers**: `gemini-2.5-flash-lite` (the price floor), `gemini-3.1-flash-lite`,
  `gemini-3.5-flash-lite`, `gemini-3.8-flash`, and `gemini-3.1-pro-preview` as the ceiling.
  Thinking parameters differ by generation (`thinkingBudget` on 2.5, `thinkingLevel` on 3.x), so
  each tier is probed with a one-line call before the runner assumes a shape.

## Interaction-path safety

- The deferred acknowledgement, the Gemini call and the PATCH all run in `asyncio.to_thread`, so a
  slow REST call cannot starve the gateway heartbeat.
- A gateway RESUME replays events, and a replayed `INTERACTION_CREATE` carries an expired token,
  so its acknowledgement 4xxs. Every Discord call in the path is wrapped the way `handle` wraps
  `send_message`: a failure is logged and the loop carries on. Interaction ids are remembered, as
  message ids already are, so a replay is not answered twice.
- An interaction whose author is a bot is ignored, the same guard as the mention path.

## Build order (iterate on one artifact, then the pool)

1. The pipeline end to end with a FIRST-PASS glossary: the Wasp campaign sections, government,
   castes and ranks, the Fortunes and clan patrons, and the rules terms. That is enough for the
   GM's five examples and about 30 more questions.
2. Prove the whole path: the command registered, a real private reply in Discord, the linker
   firing, the cost logged.
3. Then sweep the rest of `l7r.md`, the remaining OP pages and the character bios into the
   glossary, and run the full evaluation across tiers.

## Constitution Check

- **I. Accessibility-First Viewports**: N/A. There is no web UI; the surface is a Discord message.
- **II. Bold, Intentional Design**: N/A. There is no new UI surface.
- **III. Pool Data Conventions**: N/A. The glossary is reference data, not generated content of a
  recurring kind. It is still one-entry-per-line data with a validating test.
- **IV. One Canonical Home for GM Source**: PASS. No SOURCE blocks are added; the glossary
  paraphrases, and `l7r.md` stays canonical, recorded per entry by `source`.
- **V. Protecting the GM's Writing**: PASS. Nothing edits `l7r.md` or any SOURCE block.
- **VI. Verify Before Reporting Done**: PASS. The plan verifies by:
  - `make done`
  - the evaluation run across tiers
  - a live `/look-up` in Discord from this container (see quickstart), with the reply checked to
    be private
  - spot-reading of the glossary's entries against `l7r.md`
- **VII. De-Localized Generation by Default**: N/A. Nothing is generated about a place.
- **VIII. Direct Voice Over Framing Distance**: PASS. The instructions ask for plain direct
  answers.
- **IX. Setting Integration**: PASS. The glossary draws every entry from the GM's notes, with its
  source recorded.
- **X. Python Discipline**: PASS. There is a new package with mypy --strict, 100% coverage, files
  under 1,000 lines, and a `CLAUDE.md` index. The network boundaries (Gemini, Discord, the sheet
  pages) are injectable and tested with saved fixtures.
- **XI. Japanese Authenticity**: PASS. Readings and literal meanings in the glossary are taken
  from the GM's notes where given. A term whose notes give no meaning gets none, never an invented
  one.
- **XII. Historical Grounding Bookends**: N/A. This is not a historical-practice generator.
- **XIII. No Known Regressions**: PASS. The baseline is the `make done` state before the change;
  the mention responder's existing tests must stay green.
- **XIV / XV**: noted. The `[gemini] api_key` value in the secrets file is written in quotes.
  That is not a defect: `chargen` and the deploy script read it with ConfigObj, which strips
  quotes; only an ad-hoc `configparser` read sees them. `l7r/lookup/` reads with ConfigObj too,
  tested with a quoted value.
- **XVI. Build What Was Asked**: PASS. The spec has the reviewer's verdict.
- **XVII. README**: PASS. There is no README. Docs go in `CLAUDE.md`.
- **XVIII. A Guard Ships With Its Test**: PASS. The link filter and the spending ceiling are
  guards, each with tests proven to fire.

## Project structure

```text
webapp/l7r/lookup/
  CLAUDE.md          index, glossary build/refresh procedure, how to test
  __init__.py
  glossary.jsonl     data (Claude-built)
  glossary.py        load + validate + render for the prompt
  sources.py         section hashing, staleness report
  campaign.py        Wasp campaign brief, prompt assembly
  profiles.py        sheet API -> profiles (deploy time), public-page refresh, clan derivation
  links.py           roster, mechanical linker, link filter
  gemini.py          REST client, usage -> cost
  ledger.py          daily spending ceiling + query log
  service.py         answer(question, asker) -> reply text, end to end, injectable
  eval/__init__.py, eval/__main__.py, eval/questions.jsonl
  data/              deploy-time baked roster + profiles (gitignored)
webapp/l7r/mention/  responder.py + gateway.py learn INTERACTION_CREATE
scripts/register_lookup_command.py
scripts/deploy_mention_bot.sh   ships lookup/, its baked data, the dedicated key
webapp/tests/test_lookup_*.py
```

## Complexity tracking

None.
