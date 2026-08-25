# Feature Specification: Scripted NPC Naming with a Live Used-Name Cache

**Feature Branch**: `200-scripted-npc-names` (no branch - `SPECIFY_FEATURE=200-scripted-npc-names` on `main` in the session clone)

**Created**: 2026-08-25

**Status**: Draft

**Input**: The GM's request, verbatim (two messages, 2026-08-25, session "GM assistant names"):

> We have a list of names which are part of the /names skill. This pregenerated list probably needs to be bigger. I also think that when we use the /chargen skill then that other skill, or the /synthesize skill as well, should use a scripted process for generating a name instead of a manual process, which is what happens now. Currently, what will happen is that I will evoke one of those skills, and then it will go through a bunch of back and forth iteration, which results in significantly more time and tokens being taken up. So I would therefore like to have a scripted process. And I believe there actually is a script already, but we might need to make some changes to it - I'm not sure about this, and it might just work as is. At the very least, I think we started off with something like one hundred names or possibly one hundred names for each gender. So two hundred names total or so. And I suspect that we need more because we have now used many dozens of names. Does that sound right?

The session answered with three numbered recommendations - (1) derive the used-name exclusion list from the OAuth-backed campaign cache instead of the stale cookie scrape, (2) unify the engine's name lists and the skill pool into one source with exclusion and set-distinctness applied inside the engine plus a gender constructor argument, (3) grow the pool - and the GM replied:

> Can we make it so that every time we upload a new character to Obsidian Portal, we update a local cache? I think we already do something similar with updating our /synthesize prompt, so we could also update a local cache of what names have been used, right? After that then please implemnent 1 and 2, but hold off on 3 for now since I have more questions before we decide to grow the size of the pool.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A newly uploaded character is immediately a used name (Priority: P1)

The GM uploads a new NPC to Obsidian Portal (through `/chargen` or the webapp's create button). The very next name request - from the `/name` skill, from `/chargen`, or from the webapp - already treats that character's given name (and anything too similar to it) as taken, without the GM refreshing anything by hand.

**Why this priority**: This is the thing the GM asked for first and by name. The stale exclusion list is the root cause of the measured leak (64 cached names against 117 live characters; two pool names already belonging to live NPCs).

**Independent Test**: Create a character; then ask for names and verify the new given name and its near-neighbors never appear. Verify the local campaign cache now contains the new character.

**Acceptance Scenarios**:

1. **Given** a character named `Hida no Reiji Kentaro` has just been created on Obsidian Portal, **When** any name request is served, **Then** `Kentaro` and names the similarity rule counts as too close to it are excluded.
2. **Given** the local campaign cache is older than the staleness window and the GM runs the `/name` skill, **When** names are picked, **Then** the cache is refreshed from Obsidian Portal first (via the same authenticated path the backstory context uses), and the pick reflects the live roster.
3. **Given** Obsidian Portal is unreachable, **When** a name is requested, **Then** the request still succeeds using the last cached roster, and the staleness is reported rather than silently ignored.
4. **Given** a character was added through the Obsidian Portal website rather than through this project, **When** the cache is next refreshed, **Then** that character is present too (the refresh is a reconciliation, not an append-only log).

---

### User Story 2 - `/chargen` names a character with no manual iteration (Priority: P1)

The GM invokes `/chargen` (optionally pinning a gender, optionally asking for a SET of several NPCs). The character comes back with a given name that is (a) drawn from the same curated pool the `/name` skill and the `/names` web page use, (b) not in use or too similar to a used campaign name, and (c) for a set, unmistakable from the set's other names - all in one scripted step, with no re-roll loop and no name deliberation in the transcript.

**Why this priority**: This is the time-and-token cost the GM described. Today `/chargen` draws from a separate 862-name list that has no caste tags, ignores the used-name list entirely when run from the skill (the list is only ever filled by a web-server start-up event), and enforces set-distinctness by re-rolling by hand.

**Independent Test**: Run the engine from a plain script (no web server) with a used-name list containing a known name; generate many characters; verify none carries that name or a near-neighbor, that a pinned gender is honored on the first roll, and that a generated set of N has mutually distinct names by the set rule.

**Acceptance Scenarios**:

1. **Given** the GM asks `/chargen` for a female Crab magistrate, **When** the skeleton is rolled, **Then** the first roll is female, and no re-roll happens for the sake of gender.
2. **Given** the GM asks `/chargen` for three Tsuruchi bounty hunters, **When** the three are rolled, **Then** no two given names share a first letter, rhyme, or differ by one letter, and this holds without the skill running any check or re-roll itself.
3. **Given** the used-name cache lists `Isao` and `Chiyoko` (both live NPCs and both currently in the pool), **When** 200 characters are rolled, **Then** neither name appears.
4. **Given** the engine is run from a script rather than the web server, **When** a name is picked, **Then** the exclusion list is populated from the local campaign cache anyway.
5. **Given** the webapp's Generate button is used, **When** a character is generated, **Then** it behaves identically to the script path (same pool, same exclusions).

---

### User Story 3 - One name source, one procedure (Priority: P2)

The `/name` skill, the `/names` web page, and the chargen engine all read the same two pool files, and the `/name` skill no longer requires a browser session cookie or a background hourly loop to stay current.

**Why this priority**: Two lists diverge; the cookie scrape rotted because nobody could refresh it. Removing the second source is what makes the first two stories stay true.

**Independent Test**: Delete the engine's private name lists and the cookie scraper; every existing test and skill path still works; the skill's documented procedure contains no cookie step and no `/loop` step.

**Acceptance Scenarios**:

1. **Given** the engine's private name lists are removed, **When** the web app starts and generates a character, **Then** it succeeds, drawing from the skill pool.
2. **Given** the `/name` skill is invoked for the first time in a session, **When** the documented procedure is followed, **Then** it involves no cookie, no `.env`, and no background loop.
3. **Given** the pool is validated, **When** validation runs, **Then** it checks against the live-cache roster, not a hand-maintained text file.

---

### Edge Cases

- The campaign cache file does not exist yet (fresh container): a name request triggers a full pull; if that fails, the pick proceeds with an empty exclusion list and says so.
- Every pool name for the requested gender/caste is excluded (pool exhausted by the roster): the engine and the skill report this clearly (the skill already prints an error; the engine must not loop forever).
- A pinned gender that the pool cannot serve after exclusion: same clear failure, no infinite loop.
- A given name that appears in the roster as a mononym (peasants: `Denbei`, `Otohime`) or as the last token of a long samurai name (`Bayushi no Daika Bokuden` -> `Bokuden`): both count as used. A roster entry that is a bare family or place name (`Tsuruchi`, `Reiji`) is treated like any other last token - the similarity rule is deliberately loose.
- The creation call succeeds on Obsidian Portal but the cache refresh afterwards fails: the character exists, the in-process used-name set still knows the name, and the next refresh reconciles. Creation is never reported as failed because the cache step failed.
- Concurrent readers: the skill picker and the web server may read the cache file while a refresh writes it; a partially written file must not be read as an empty roster.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: After every successful character creation on Obsidian Portal from this project, the local campaign-character cache MUST be updated to include the new character before the creation call returns. The update MUST be fail-soft: a failed update never turns a successful creation into a reported failure.
- **FR-002**: The set of used given names MUST be derived from the local campaign-character cache (the same cache the backstory-synthesis prompt reads), not from a separately maintained list. "Given name" is the last whitespace-separated token of the character's full name.
- **FR-003**: The cookie-based campaign-name scraper and its hand-maintained output file MUST be retired, along with the `/name` skill's cookie-setup and hourly background-loop instructions and any dependency-installation step that existed only to serve the scraper.
- **FR-004**: When the `/name` skill picks names, it MUST refresh the campaign cache from Obsidian Portal first if the cache is older than a staleness window (default: one hour; the picker accepts an explicit force-refresh). Refresh MUST use the authenticated API path already used for the backstory context, never a browser cookie. Refresh failure MUST NOT block the pick; the picker MUST report that it is working from a stale or empty roster.
- **FR-005**: The chargen engine MUST draw given names from the `/name` skill's pool files (`pool-male.jsonl`, `pool-female.jsonl`) and the engine's private per-gender name lists MUST be removed. The name's meaning text carried on the character MUST come from the pool entry's explanation.
- **FR-006**: The engine MUST exclude any pool name that is used or too similar to a used given name, by the same similarity rule the `/name` skill uses, and that rule MUST have exactly one implementation shared by the engine and the skill.
- **FR-007**: The engine MUST populate its used-name set from the local campaign cache whenever it picks a name, without depending on the web server's start-up event. The web server's periodic refresh MAY remain as an additional reconciliation.
- **FR-008**: Every character constructor MUST accept an optional gender; when given, the character is rolled with that gender on the first attempt. When absent, gender is random as today.
- **FR-009**: Every character constructor MUST accept an optional list of given names to avoid; a picked name MUST NOT conflict with any of them under the set-distinctness rule (no shared first letter, no rhyme, no one-letter difference). This is how a set of NPCs generated together stays mutually distinct.
- **FR-010**: The `/chargen` skill's rolling step MUST use the gender argument and the avoid list, and MUST contain no gender re-roll loop and no manual set-distinctness check.
- **FR-011**: When no pool name satisfies the exclusions for the requested gender, the engine MUST raise a clear error naming the gender and the reason; it MUST NOT loop indefinitely.
- **FR-012**: Pool validation MUST check the pool against the given names in the campaign cache rather than a hand-maintained file.
- **FR-013**: The pool MUST NOT be grown by this feature. Its contents are unchanged except that no entry is added; entries are not removed either (the two pool names that are currently live NPCs are handled by exclusion, not deletion, so the pool-size question stays open for the GM).
- **FR-014**: Reading the cache MUST tolerate a concurrent write (a partial file reads as "unavailable", not as an empty roster) and writes MUST be atomic (write-then-rename).

### Key Entities

- **Campaign-character cache**: the id-keyed local record of every Obsidian Portal character (name, tags, bio, GM notes, updated-at), already maintained incrementally for backstory synthesis. Gains two consumers (used-name derivation; the `/name` skill) and one new writer moment (post-creation).
- **Used given name**: the last token of a cached character's full name. Derived, never stored separately.
- **Name pool**: the curated per-gender JSONL entries (name, gender, explanation, format, notes, peasant flag). Becomes the single source for the skill, the web page, and the engine.
- **Similarity rules**: the loose "too similar to a used name" rule and the strict within-set "set conflict" rule. One implementation, two consumers.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Immediately after a character is created from this project, a name request excludes its given name - 100% of the time, with zero manual refresh steps.
- **SC-002**: A `/chargen` invocation with a pinned gender and/or a set of N characters produces correctly gendered, mutually distinct, unused names in ONE engine call per character - zero re-rolls for gender, zero manual distinctness checks, zero name deliberation in the transcript.
- **SC-003**: Over 1,000 generated characters against the live roster, zero given names are used or too similar to a used name.
- **SC-004**: The `/name` skill's first-invocation procedure has no cookie, `.env`, or background-loop step; the number of name sources in the repository drops from two to one.
- **SC-005**: The pool file line counts are unchanged by this feature (103 male / 97 female).
- **SC-006**: No regressions: every test that passed on the baseline still passes; the webapp gate (lint, format, strict types, tests, 100% coverage on pure-logic packages) is green.

## Assumptions

- The Obsidian Portal OAuth path (`existing_characters`, `get_character_body`) remains the authenticated boundary; the feature adds no new external calls, only new call sites.
- The engine's private lists (574 male / 288 female) hold names the pool does not; dropping them reduces the engine's raw supply from 862 to 200. This is accepted because the GM explicitly deferred pool growth (item 3) and asked for unification (item 2); the trade-off is recorded here and reported to the GM so the pool-size decision is made with it in view.
- `/synthesize` does not pick names (it works on an existing record) and needs no change beyond sharing the cache; the GM's mention of it is satisfied by the cache being the same one its prompt already uses.
- The staleness window of one hour mirrors the retired `/loop 1h` cadence; the picker's force-refresh flag covers the "I just added someone on the website" case.
- The webapp's deploy bundling already copies the pool files into the build context, so the engine reading the pool needs no new deploy step.
- "Update a local cache on upload" is satisfied by an incremental reconciliation after creation (one list call plus one body fetch for the new id), which also catches characters added on the website in the same pass.
