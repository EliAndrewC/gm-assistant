# L5R Setting Generation Project

This project is a Legend of the Five Rings tabletop RPG worldbuilding environment. The GM uses Claude Code to generate setting details (NPCs, locations, items, etc.) guided by their extensive setting notes and evolving preferences.

<!-- Dev-container config consumed by scripts/launch-container.sh. Format is HOST:CONTAINER. -->
<!-- container-ports: 8080:8080 8091:8090 -->
<!-- container-mounts: ..:/host-l7r-repo -->
<!-- container-workdir: /gm-assistant -->
<!-- (distinct mount path per repo so Claude memory under ~/.claude/projects/ stays separate across sibling repos) -->

## Core Rules

### Canonical Source

The GM's canonical notes file is `/host-l7r-repo/setting/l7r.md` - the GM's `EliAndrewC/l7r` repo, bind-mounted from the host. This file is the master record of campaign and setting notes. The GM appends to it directly from their laptop, and you append to it via the [Note Intake Workflow](#note-intake-workflow) below when the GM pastes notes into the chat. If the mount is not present, the container was not launched per [`/gm-assistant/README.md`](README.md) - ask the GM rather than guessing.

The GM handles all git operations (`add`, `commit`, `push`) from their laptop. From inside the container, **never run `git commit` or `git push`** against the mount; read-only operations like `git log` / `git diff` are fine if you need historical context.

### Protecting the GM's Writing

Content between `<!-- SOURCE: GM NOTES - DO NOT MODIFY -->` and `<!-- END SOURCE -->` markers is the GM's original writing. These sections must NEVER be modified, rephrased, summarized, reworded, or "improved" in any way. Only the GM may edit these sections, and only when they explicitly instruct you to do so.

These blocks are **frozen historical excerpts**: they capture what the GM wrote at the time the downstream file was created and are not kept in sync with subsequent edits to `/host-l7r-repo/setting/l7r.md`. Drift between a downstream `SOURCE` block and the current canonical is expected and intentional - the block is a point-in-time snapshot, not a live mirror. The canonical for any topic is always `l7r.md`.

AI-generated content (preferences, generation instructions, examples of liked/disliked output) lives outside these markers and can be updated as the GM's preferences evolve.

This convention applies to ALL files in the project - both skill files and reference directory files.

### File Organization

#### Skills (invocable as /slash-commands)

Each skill lives in `/.claude/skills/<skill-name>/SKILL.md` with YAML frontmatter. Skills are for *generating* specific types of content.

#### Reference Directories (not invocable, indexed by CLAUDE.md)

Reference directories hold organized source material and context. Each directory has its own `CLAUDE.md` that indexes and explains its contents. Skills should reference these directories when they need shared context.

- `/setting/` - Demographics, castes, currency, samurai ranks, government structure (Six Ministries), geography, lineage system, merchant families, ashigaru, experience levels
- `/campaigns/` - Campaign-specific material: Karmic Inquisitors, First Toshi Ranbo, Hidden Way, Wasp Bounty Hunters, timelines, PC/NPC backstories, the Order of Lord Moon
- `/hooks/` - Adventure hooks organized by type (countryside, town, city, caravan, prison camp), grifts and scams
- `/cosmology/` - Lord Moon's heavenly court, mythological stories/fables, maho & bloodspeakers, "between places", gaijin religions (Uru, Burning Sands), Fortune theology, soothsaying
- `/notes/` - Miscellaneous source material not yet organized into a dedicated reference directory

### Generation Behavior

- When generating content, draw on the GM's source notes for tone, style, and setting details.
- Preference feedback from the GM is captured in memory and incorporated into skill files over time.
- Never invent setting details that contradict the GM's source notes.
- Skills should reference the relevant reference directories for shared context (e.g., `/temple` should draw on `/setting/` for demographics and `/cosmology/` for Fortune theology).
- **Hyphens only - no em-dashes (U+2014) or en-dashes (U+2013) anywhere in the project**, including generated content, webapp templates, skill files, specs, docs, and tests. This applies project-wide, not just to `l7r.md`.
- **American spellings, never British ones.** Always use: `color`, `center`/`centered`, `gray`, `honor`, `judgment`, `catalog`, `labeled`/`labeling`, `behavior`, `neighbor`/`neighborhood`, `analyze`/`organize`/`recognize` (the `-ize` forms), `artifact`, `defense`, `license`, `practice` (both noun and verb), `skeptic`, `story` (of a building), `while`, `traveled`, `modeled`, `program`, `meter`, `liter`, `mold`, `plow`, `curb`, `draft`, `aging`, `marvelous`, `jewelry`, `skillful`. Never their British counterparts (the `-our`, `-re`, `-ise`, `-ce`-noun, doubled-`l`, and `-ogue` forms). This applies project-wide and to **everything**: generated content, prose, docs, specs, skill files, webapp templates, tests, comments and docstrings, **and code identifiers** (variable names, parameters, dict keys, CSS class names). The one exception is the GM's own writing - never "correct" text inside `<!-- SOURCE: GM NOTES -->` blocks or in `l7r.md`, and leave direct quotations of it alone.
- **Constitution Principle XI** (Japanese Authenticity): any kanji that surfaces in generated content - relic names, sword names, given names, temple titles, vow refrains, decorative stamps - must pass the kanji ↔ romaji ↔ meaning triangle. Real characters, plausible reading, English meaning that maps back. Stylized readings are allowed when explained in surrounding prose.
- **Record the "why" of every research-driven rule (REQUIRED).** When historical (or setting) research leads us to a concrete generation rule, automated check, or magic number - "every farmhouse had a work yard," "~30% of farms had a storehouse," "threshing was per-household, not communal" - we MUST capture the *reasoning* alongside the *rule*, not just the rule. Encoding the finding into a check or generator is necessary but **not sufficient**: a bare `count >= 0.3 * n` teaches a future reader nothing about why 0.3. So write the finding down where the rule lives - a "Historical grounding"/research section in the skill's `SKILL.md`, or a comment next to the check - covering what the research found, the decision it drove, and any deliberate departures from literal reality (e.g. features drawn larger than true scale for legibility while keeping *relative* sizes roughly honest). Explicit source citations are optional (usually overkill); the *why* is mandatory. This protects against having to redo the research when memory fades or the context window rolls over. Applies to any generator (skills, the webapp, future tools), not just `/diagram`.

## Skills

| Skill | Purpose |
|-------|---------|
| `/sword` | Generate famous swords with histories and properties |
| `/temple` | Generate temples, monk NPCs, temple daily life |
| `/relic` | Generate temple relics, cursed items, supposedly-supernatural objects |
| `/vow` | Generate oaths and vows for various orders and roles |
| `/place-names` | Generate Rokugani place names at four scales (province, town, village, hamlet) with suffix-aware emit-time notes and a tagged pool |
| `/calendar` | Generate seasonal details, festivals, agricultural events |
| `/law` | Generate legal cases, rulings, magistrate proceedings |
| `/fortune` | Generate cosmological content, soothsaying, omens, Fortune theology |
| `/moto` | Generate Moto culture content, Yassa rulings, horse culture, Burning Sands |
| `/bounty` | Generate bounties, Wasp clan content, minor clan details |
| `/name` | Generate Rokugani personal names with meanings in varied formats. Args: `[m\|f] [p] [N]` - supports shorthand and concatenation (e.g. `pf3`) |
| `/diagram` | Generate SVG top-down diagrams of L5R locations (manor plans, village layouts, temple plans, etc.) and render to PNG |
| `/dream` | Generate Rokugani dream-omen scenes: randomized d10 dream tables for PCs seeking a fortune's (or other spirit's) will in sleep, grounded in Kitsu Okura's six-doctrine theology of attunement. Strange, open fragments that describe the dream's events and never its meaning; shared no-dream/noise bands, a 10-is-always-significant Coda, and a two-tier (public / gitignored-local) spoiler-safe pool |
| `/synthesize` | Write a backstory for an existing Obsidian Portal NPC, Claude-native (in-session prose - no external LLM; the webapp button still uses Gemini): reads the OP record + tagline and the campaign-context cast, researches the setting files directly, review (upload as-is / regenerate / upload with typed changes), merges into GM-only notes. Args: `<character name> [ - steering]` |
| `/chargen` | Make a brand-new NPC end-to-end and upload it to Obsidian Portal: roll a skeleton character with the chargen engine (asking only about genuinely-missing essentials), write a Claude-native backstory (the `/synthesize` method, not Gemini) from the rolled attributes, generate and attach an AI portrait, and create the OP record. Public by default; GM-only if the concept says private/hidden. Args: `<free-text character concept>` |
| `/weather` | Ground Rokugan weather in real historical data: map a place to a continental-US climate analog (latitude, distance from ocean, elevation) and read actual recorded weather for a Rokugani calendar date translated to a real-world date. Args: `<place> <month> <day>` |

## Testing

- **Framework:** pytest with pytest-cov
- **Location:** Tests live alongside the code they test as `test_<module>.py`
- **Coverage target:** 100% line coverage for pure logic. External boundaries (HTTP requests, browser sessions) are tested via saved fixtures, not mocks of the transport layer.
- **Running:** `pytest <skill-dir> -v` for a specific skill, or `pytest --cov=<skill-dir> --cov-report=term-missing` for coverage

## Reference Directories

| Directory | Contents |
|-----------|----------|
| `/setting/` | Demographics, government, ranks, castes, economics, geography |
| `/campaigns/` | Campaign timelines, NPC/PC backstories, Order of Lord Moon |
| `/hooks/` | Adventure hooks by setting type |
| `/cosmology/` | Moon court, stories, maho, gaijin religion, Fortune theology |
| `/notes/` | Miscellaneous source material, not yet organized into a dedicated reference directory |

## Note Intake Workflow

When the GM pastes raw campaign notes into the chat - actions a character took at the table, new lore that came up in play, NPC backstory beats, world-building ideas - your job is to **copy-edit for presentability** and **write the notes to two destinations**:

1. **`/host-l7r-repo/setting/l7r.md`** - always, no exceptions. You decide where in the file to insert based on topic. Don't append at the end if a better-placed paragraph exists. Match the tone of the surrounding section.

2. **Obsidian Portal** - exactly one of these, as specified by the GM at intake time:
   - **A specific character's record** - the GM names the character AND specifies whether the note goes to **GM-only notes** (`game_master_info`) or to the public **Wish Lists and Goals** section of the bio (`bio`, edited as a Textile heading-anchored subsection). Look up via `op.existing_characters()` (returns `{id, slug, name, …}`). To edit the Wish Lists and Goals subsection: read the current `bio`, locate the `Wish Lists and Goals` heading, splice your addition under it, then send the full updated body via `op.update_character(id, bio=...)`. Avatars/images go via the browser-sim path - the OAuth API silently no-ops on avatar fields.
   - **A wiki page** - the GM says "wiki." You decide which page based on topic. Look up via `op.existing_wiki_pages()` (returns `{id, slug, name, wiki_page_url, …}`). Update via `op.update_wiki_page(id, ...)` with `body` (public Textile), `game_master_info` (GM-only), or `name` / `tags` / `is_game_master_only`. Adventure Log entries also use the blog-post fields `post_title` / `post_tagline` / `post_time`. **If no existing page is a good fit, ask before creating a new one** - page proliferation is hard to undo.

**Routing is your judgment call, not the GM's.** Make a best-guess routing decision based on the content - propose specific destinations rather than asking "where does this go?" Notes may be split across multiple destinations (different paragraphs going to different wiki pages, or some content to the wiki + some to a character record) - splitting is expected and fine. If you're highly confident in the routing (e.g. "more Imperial bounties" → the bounties skill/data), proceed and report exactly what you did. If you have any uncertainty about a destination, **present your proposed routing and ask for confirmation before writing** - phrased as "I think this goes to X, confirm?", never as an open-ended "where does this go?". When the GM is explicit about destination (e.g. "save this to character Akodo Toturi, GM-only"), use what they said; for character intake, you still need both the character name AND whether the content is GM-only vs Wish Lists/Goals - if either is missing, ask with a guess.

**Granularity of routing proposals**: work at the **page / destination level**, not the section-within-page level. Say "the Fox Clan page for most, the Three Man Alliance page for the cash/rice paragraph," not "this paragraph at h3 X, that paragraph between h3 Y and h3 Z." The GM trusts you to decide section/paragraph placement within a page once the destination is confirmed - don't ask them to approve those choices individually.

**Copy-edit rules**:

- Raw input → readable prose. Fix grammar, punctuation, sentence structure, fragments. Expand shorthand into full sentences. The result should be presentable, not a transcript.
- Preserve meaning and voice. The GM's register is laconic and matter-of-fact; don't add flowery elaboration, don't smooth into marketing tone, don't introduce claims or implications the source didn't make.
- If a fragment is too cryptic to interpret with confidence, stop and ask rather than guess.
- **Tone matches `l7r.md` at both destinations.** Read nearby sections of `l7r.md` to calibrate before writing to either `l7r.md` itself or to OP. Don't shift register based on audience - what's good for `l7r.md` is good for the wiki/character bio too.
- For OP destinations: convert to Textile (not Markdown). Match nearby pages' conventions (`\r\n` line endings, `bq).` for blockquotes, `[[wiki-slug]]` for internal links).
- **Silently correct known GM-typos** in any text you write or any existing wiki/character content you happen to be editing:
  - "Chancellary" → "Chancellery"
- Always report back exactly where each piece was written (which page or `l7r.md` section; which character record; public Wish Lists/Goals vs GM-only) - never assume the GM will read the diff blind.

**Implementation pointers**:

- `/gm-assistant/webapp/chargen/op.py` - all the API helpers (`existing_characters`, `update_character`, `existing_wiki_pages`, `get_wiki_page`, `create_wiki_page`, `update_wiki_page`, `delete_wiki_page`). All use the OAuth path. Image uploads remain browser-sim.
- OAuth creds live in `[obsidian_portal]` of `development-secrets.ini`; rotation via `probe_op_oauth.py --full` (see [`/gm-assistant/webapp/probe_op_oauth.py`](webapp/probe_op_oauth.py)).
- This workflow is intentionally **documented in CLAUDE.md rather than a skill**. Skills in this project are content *generators*; intake is a routing workflow that should be present in every session's context.

## L7R Style Conventions

These conventions govern any edit to `/host-l7r-repo/setting/l7r.md` - both copy-edit passes and new content insertions. Apply them silently; never explain the style in the prose itself.

**Numbers - AP-style with overrides**:

- Spell out one through nine in narrative prose: `two days passed`, `four reasons`, `seven of his sons`.
- Numerals for 10 and above: `the next 14 days`, `30 days each`, `over 200 Witch Hunters`.
- **Always numeric** regardless of size:
  - With units of measure: `5 koku`, `2 koku/year`, `7 miles`, `6 years` (as duration), `5%`, `1 bu`, `3 zeni`, `4 feet`.
  - Years/dates: `1117`, `1129`.
  - Ranks: `Rank 5`, `the 5th rank`, `5th-rank samurai`.
  - Fractions and ratios: `1/3`, `1/6`, `2:1`.
  - **Fixed setting labels**: `the 7 Great Clans`, `the 12 members of The Order`, `the 4 Gods of Death`, `the 4 Bloodswords`, `the 5 Major Fortunes`, `the 7 maho disciplines`, `the 6 Ministries` (a.k.a. `Six Ministries`), `the 4 Imperial Families`. The numeral is part of the descriptor.
- **Always spell out**: numbers that begin a sentence; informal round numbers (`a thousand years`, `several hundred`, `a few`).
- Setting-canonical labels that *already* use spelled-out form (`the Twelve Months`, `the Ten Heavenly Stems`, `the Twelve Earthly Branches`) stay spelled-out - don't convert these.

**Voice - minimize narrator "I" / "we" in setting commentary**:

- Author-voice constructions like `"We've portrayed Rokugan as..."` / `"Now let's talk about X"` / `"In my campaign..."` convert to impersonal/passive: `"Rokugan has been portrayed as..."`, `"X follows:"` or `"With Y covered, the discussion turns to X"`, `"In one previous campaign..."`.
- **Preserve "I" / "we" in**: vow text (`I, [Name], in reverence to...`), in-character dialogue and stage scenes, character first-person backstories, in-universe treatises and letters (Saibankan's ruling, "On Soothsaying", Bashi's letter, Kitsu Okura's play, etc.), GM-to-players direct address in campaign pitches.
- When in doubt, leave it. Better to under-rewrite than butcher a character's voice.

**Gender-neutral language for office-holders**:

- Use `they` / `their` / `them` (epicene singular) when referring to a generic daimyo, governor, magistrate, minister, samurai, or any other office or role, rather than `he` / `his` / `him`.  Example: `"each governor's tax-farming cut covers their province"`, not `"...covers his province"`.
- This applies to all role labels even though historically these positions were male-restricted - L7R has deliberately made Rokugan more gender-egalitarian than historical samurai cultures so that female players can fully participate in the game.
- **Specific named characters retain their actual gender pronouns** (e.g. Akodo Toturi is `he/him`; Tsume Horobinu is `he/him` per his backstory; Yasuki Aina is `she/her` per her backstory).  The rule applies to *generic* office references, not to *named* individuals.
- Epicene singular `they` takes plural verb form (`they handle`, not `they handles`) - this is grammatically correct and has been accepted in formal English for years.

**"Person" / "people" has caste meaning in Rokugan**:

- In the Rokugani Celestial Order, **only samurai are "people"**.  Heimen (farmers, merchants, artisans) are "half-people"; hinin (laborers, servants, entertainers, criminals) are "non-people"; burakumin (the lowest hinin) are "untouchables".
- This is documented in the Castes section of `l7r.md`: *"samurai are 'people', and this is why 'inhabitants' or 'humans' is the preferred term when discussing populations."*
- Therefore, do NOT write things like `"4 out of every 5 people work the land"` (technically false - farmers are half-people, not people) or `"~1 county per 6,800 people"` (most county residents are heimen or hinin).
- **Use one of these instead** when referring to all humans in Rokugan generically:
  - `humans` (most direct - "4 out of every 5 humans work the land")
  - `inhabitants` ("~1 county per 6,800 inhabitants")
  - `population` ("~80% of the population are farmers")
  - Specific caste terms when accurate ("most peasants", "most samurai", etc.)
- `people` IS correct when specifically referring to samurai (e.g. *"most people in significant government posts"* is fine because those posts are held by samurai).
- `people` is also fine in narrative/lore voice ("the people of Toshi Ranbo worry about a city-destroying fire"), in-character dialogue, vow text, festival descriptions, and folktale content - same exceptions as the "I/we" rule above.  The constraint applies primarily to **demographic, statistical, and analytical contexts**.

**Use "domain" instead of "demesne"**:

- L7R uses `domain` for the territory administered by a daimyo, governor, or magistrate at any tier - never `demesne` (the medieval European term).
- Applies to all compound usages too: "Imperial domain" (not "Imperial demesne"), "personal domain" (not "personal demesne"), "Hantei lands" rather than "Hantei demesne", etc.
- Silently fix `demesne` → `domain` in any text being edited.

**Capitalize "Family" and "Clan" as institutions**:

- **Family** (capital F) when it means the institutional house/alliance within a Clan: named Families (`Hida Family`, `Matsu Family`, `Yasuki Family`), the `Family daimyo`, the `Family` kick-up layer, `Family capital`/`Family seat`, the kick-up recipients (`Family, Clan, and Imperial`), and the `Imperial Families` (Hantei, Seppun, Otomo, Miya). Lowercase `family` for the generic/relatives sense: `the daimyo's family`, `family members`, `family households`, `farm/merchant/samurai families`, `family name` (surname), `birth family`, `family connections`.
- **Clan** (capital C) as part of a clan's name or the institution: `Crab Clan`, `Lion Clan`, the minor clans (`Wasp Clan`, `Fox Clan`), `Clan daimyo`, `Clan capital`, the `Family/Clan/Imperial` kick-up tiers, and the fixed labels `Great Clans` / `Minor Clans`. Lowercase `clan` only in relational/process compounds: `clan-supplied`, `cross-clan`, `inter-clan`, `clan-level`.
- Quick test: "the daimyo's family" is their parents/siblings/spouse/children; "the daimyo's Family" is e.g. the Hida Family.

- Hyphens only. No em-dashes (U+2014) or en-dashes (U+2013) anywhere.
- Two spaces after a period is house style. Preserve it.
- Section headings have no trailing colons: `### Hikobayashi County`, not `### Hikobayashi County:`.
- Numbered lists use `N.` not `N)`. Sub-bullets under a numbered item need **three** leading spaces to align with text after `N. ` (e.g. `   - sub-bullet`). Sub-bullets under a `-` bullet need two.
- Multi-paragraph bullet items: continuation paragraphs must be indented to match the bullet's text column (2 spaces under `- `, 3 spaces under `N. `).
- Play scenes: character names in bold (`**Okura:**`), stage directions in italics inside the bolded speaker (`**Okura** *(sharply):*`), `*End Scene*` italicized.

**Heading hierarchy and TOC**:

- `#` document title only; `##` top-level sections; `###` sub-sections; `####` per-NPC / per-relic / per-element; `#####` per-detail (per-lineage, per-province, per-garden).
- The TOC at the top is **curated, not generated**. The GM selectively trims entries they don't want listed even when those headings exist in the body. **Never bulk-regenerate the TOC from current headings** - doing so would put back every entry the GM deliberately removed. Instead, when adding new headings, **surgically insert only the new TOC entries** in their correct nested position, leaving every other line of the TOC untouched. Use `git diff` to verify only the intended additions are present before reporting done.
- When in doubt about whether a new heading belongs in the TOC, ask the GM rather than adding it.
- Never delete a heading from the body to slim the TOC - headings stay in the body for in-page anchoring even when omitted from the TOC.

**Process**:

- File state shifts during long editing sessions (linters, parallel saves). If `Edit` fails with "file modified since read", re-grep the anchor text and try again - don't trust line numbers across multiple edits.
- For sweeps that touch many places, delegate the *scan* to a subagent that produces a report, then apply changes via direct `Edit`s anchored on text content (not line numbers).
- Known silent-fix typos accumulate. At minimum: `Chancellary` → `Chancellery`. `Otaku` (not `Utaku`) is the GM's canonical spelling for the Unicorn family.

This guide lives in CLAUDE.md rather than a skill because these conventions apply implicitly to every edit of `l7r.md`, not on explicit invocation - same rationale as the Note Intake Workflow above.

## Development Workflow

This project uses spec-driven development governed by [`.specify/memory/constitution.md`](.specify/memory/constitution.md) (currently v1.1.0, 10 principles, 3 NON-NEGOTIABLE). The constitution is the higher-level authority; this CLAUDE.md operationalizes it.

**When to use spec-kit:**

- **Feature work** (new sections of the webapp, new skills, new generators, the upcoming Python backend) → invoke `/speckit-specify` and follow through plan → tasks → implement. The Constitution Check section in `.specify/templates/plan-template.md` is the gate that enforces the constitution at plan-time; skipping spec-kit on feature work means skipping that gate.
- **Tweaks and iteration** (CSS adjustments, wording fixes, regenerating one item, fixing one bug) → just do the work directly. The constitution still applies, but the formal spec/plan/tasks flow is overkill.
- **Ambiguous cases** → ask before chain-firing `/speckit-specify`.

**Verification before reporting "done"** (per Principle VI of the constitution):

- **UI changes** (per Principle I, expanded in v1.3.0):
  - Run `webapp/tests/screenshot.py` to produce **multi-scroll contact sheets** at GM-100 / GM-200 / tablet / mobile. For pages taller than 1.3× viewport, the script captures 0%/33%/66%/100% scroll positions and stitches them horizontally - so layout asymmetry, dead space, and below-fold problems are visible at a glance.
  - Run `webapp/tests/dom_audit.py`. It must report **zero issues** across all pages × viewports. The audit now covers BOTH clipping (overflow, ellipsis, line-clamp) AND layout balance (sibling-height ratio inside flex/grid containers must not exceed 2.5×).
  - **Persona-driven review pass**: before declaring done, examine at least one contact sheet at GM-200 with the user's task in mind (not the implementer's: "Eli is opening this page; what is he trying to do here?"). If the same agent both implemented and reviewed, **invoke the `frontend-review` subagent** (`.claude/agents/frontend-review.md`) to get an independent pass. Author ≠ reliable reviewer.
- **Python changes**: `ruff check` + `ruff format --check` + `mypy --strict` + `pytest` + `--cov-fail-under=100` on pure-logic packages (Principle X).
- **Delegated work**: spot-check actual artifacts before relaying success to the user. "The subagent said it was done" is not sufficient.

**Iteration-loop efficiency** (profiled with the GM, 2026-07-20): a transcript-timestamp profile of a representative small feature showed **78% of wall time was model turn latency and only 22% tool execution** - tool speed is NOT the bottleneck; the NUMBER of sequential turns is. This holds project-wide (webapp + skills). Standing practice:

- **Batch into fewer, bigger turns.** Group independent recon (greps, file reads, artifact inspections) as parallel tool calls in ONE turn instead of one lookup per turn, and apply a planned multi-edit to a file in one turn rather than edit-per-turn. Only serialize when the next step genuinely depends on the previous result - do not batch past a real decision point, and never skip looking at a result that could change the plan.
- **Docs-only diffs skip the gate.** If everything changed since the last green gate is markdown/docs, do not re-run the gate (`make done`) - it runs once at stop-work for the code that changed. (This redundancy has cost a full gate run before: a re-run after only a docs edit.)
- **Iterate on the motivating artifact; run the full test bed exactly once, at the end.** The red/green loop runs against the one artifact (map, fixture, page) that exhibits the defect - a single-artifact rebuild is cheap, so cycles are near-free. The full sweep (the whole test suite / every generated artifact) is reserved for AFTER the motivating artifact is in a good state - but it is MANDATORY then whenever shared code changed, since every downstream artifact depends on it and the sweep is what turns "no other case has this bug" from a hope into a verified claim. Anti-pattern: using the full suite as the FIRST verification of a shared-code change - a failure that would surface in seconds on one artifact surfaces many minutes in. Package-specific gate timings and sweep mechanics live in that skill's dev-loop doc (e.g. [`.claude/skills/diagram/CLAUDE.md`](.claude/skills/diagram/CLAUDE.md)).
- **Background the final gate.** Start the stop-work gate with `run_in_background` and write the docs/commit message while it runs; report done only after it comes back green.
- **Do NOT cut the ritual steps** (regression-fixture freeze, overlap-registry classification, record-the-why docs, the stop-work ritual). GM-confirmed 2026-07-20: they cost ~2 minutes per feature and are why the regression rate stays near zero. The savings come from turn structure, never from skipping guardrails.

**Subagent-check TDD (REQUIRED procedure for improving review subagents)**: when the GM asks for a new rule that a review subagent (e.g. `building-review`) should enforce, do NOT simply apply the fix and write the rule into the agent. The current artifacts contain the motivating defect - that is the failing test. Procedure:

1. Add only the **general, category-level rule** to the agent definition. Never name the specific instance yet - that would test nothing about whether the check generalizes.
2. Run the agent against the artifact that contains the known defect, unfixed.
3. **If it flags the defect**, the rule generalizes: now fix the artifacts, and only now record the specific instance in the agent definition as a validated example for future runs.
4. **If it misses**, sharpen the general rule and re-run - do not shortcut by naming the instance. Escalation ladder from the first application (2026-07): a trait buried in a checklist gets skimmed; adding a protocol step barely helps; what reliably works is making the agent's **output format demand an enumerated sweep** (a mandatory report section listing every item checked) - models do what the required output structure forces.
5. Record the red/green outcome in the artifact's review log.

**Gotcha (harness behavior)**: agent definitions are snapshotted when the session registers them - mid-session edits to `.claude/agents/*.md` do NOT reach agents launched by type, which silently invalidates the TDD run. When iterating on an agent definition, launch a `general-purpose` agent instructed to Read the definition file and adopt it; the registered type picks up the changes next session.

**Spec-kit hooks**: `.specify/extensions.yml` defines auto-commit hooks before each spec-kit step. Under the session-clone workflow (below), spec-kit work happens inside the session's clone, where committing is the session's job - the auto-commit hooks may run there. Never run them against main `/gm-assistant` or `/host-l7r-repo`.

**Session clones (REQUIRED for every session that modifies this repo)**: any session that is about to change a file in this repo first makes an **isolated clone under `.clones/`** and does all of its work there - this is the standard workflow for every code-modifying session, not just for known-parallel work. A shared working tree is what causes the cross-session pain: constant "file modified since read" churn on shared files (`settlement.py`, `pyproject.toml`, ...), a `git status` that mixes multiple features' uncommitted work, and test-globs (`test_villages` globbing `pool/*/*.gen.py`, etc.) picking up another session's in-flight files. The clone is the workspace; main `/gm-assistant` is the integration point. Sessions that only *read* this repo, or that only write to `/host-l7r-repo`, Obsidian Portal, or the scratchpad, do not need a clone.

- **Clone name = the Claude Code session name, kebab-cased**: lowercase, spaces to hyphens, punctuation dropped. "Diagram (city)" -> `.clones/diagram-city`; "miscellaneous" -> `.clones/miscellaneous`. **Resolve YOUR OWN session name reliably - do NOT guess or default** (GM 2026-07-22, after a session that ignored its name defaulted to the shared clone and collided with another that did the same): your `session_id` is in your scratchpad path; grep `~/.claude/sessions/*.json` for that id and read its `.name`. The sessions-json filename is the session's PID and its body carries `{"id": "<your session_id>", "name": "...", "nameSource": ...}`, so the id is the reliable key (the `<pid>.json` framing assumed you know your PID - you usually do not). `nameSource: "derived"` means an auto-generated title, not a GM-chosen name; a GM-set name must never be overridden.
- **`gm-assistant` is a FORBIDDEN clone name** (GM 2026-07-22): it is the repository, not a session, and being the old unnamed-default is exactly what let two sessions share one working tree. There is no "default clone" anymore. A session that is unnamed, has an auto-derived title, or is literally named "gm assistant" therefore has no valid workspace: **stop and ask the GM to `/rename` it to something distinct before doing any repo work** (Claude cannot rename a session from inside it - `/rename` is user-facing only, verified 2026-07-20). The tooling enforces this - `scripts/sync-with-main.sh` refuses to run from `.clones/gm-assistant`, and the PreToolUse hook blocks edits that resolve or route to it - so if you hit that error, relay it and have the GM rename the session.
- **Clone isolation is ENFORCED by the PreToolUse hook** ([`scripts/clone-sync-hooks.sh`](scripts/clone-sync-hooks.sh), tested by [`scripts/test-clone-sync-hooks.sh`](scripts/test-clone-sync-hooks.sh)): at a clean work-unit boundary it (1) blocks the forbidden `gm-assistant` clone / unnamed sessions, (2) NAME-ROUTES - blocks any edit whose clone is not `.clones/<this session's resolved name>`, so a session cannot wander into another's clone or the shared default, (3) CLAIM-BACKSTOP - blocks a clone another **live** session already occupies (deterministic liveness: session_id -> PID = the sessions-json filename -> `/proc`, so a previous same-named session's stale claim never blocks a legitimate reuse), (4) blocks a clone whose HEAD is behind main. A DIRTY tree is always allowed (mid-task work is sacred; guards run only at clean boundaries). Because every session runs main's copy of the hook via the absolute path in `.claude/settings.json`, changes to it take effect for all sessions at once - keep `test-clone-sync-hooks.sh` green.
- **`.clones/` is gitignored and lives on the host mount** (`/gm-assistant` is bind-mounted), so clones survive container rebuilds. If `.clones/<session-name>` already exists (a resumed session), reuse it - do not re-clone.
- **Sync in at the start of EVERY new piece of work, not just at the final push - now ENFORCED by harness hooks** (GM 2026-07-21, wired in `.claude/settings.json` + [`scripts/clone-sync-hooks.sh`](scripts/clone-sync-hooks.sh)): a UserPromptSubmit hook auto-runs `sync-with-main.sh sync-in` (git pull) on the session's known clone at every GM message while its tree is clean, and a PreToolUse hook BLOCKS Edit/Write in any clone whose tree is clean but whose HEAD is behind main - a work-unit boundary on a stale base. A dirty tree is never touched or blocked (mid-task work is sacred). Renders are NOT synced into the clone (GM 2026-07-22): `render-sync` regenerates main's renders in place from main's own tip, so nothing flows clone -> main and a clone never needs main's renders - it regenerates whatever map it iterates on. Whenever a GM message kicks off new work in an existing clone - a resumed session, or the next task in a long-lived session - run `git pull origin main` inside the clone before touching anything. Other sessions push improvements to main between your tasks (test speedups, shared-file fixes), and new work must not build on a stale base. The pull is near-free at this moment (the clone has nothing uncommitted, so it's almost always a fast-forward), and any conflict surfaces at the cheapest possible time - before new work exists - instead of at the stop-work push-back. A fresh `git clone` is born synced, so this only applies from the second work unit onward.
- **Create the clone (cheap):** `git clone /gm-assistant .clones/<session-name>` - a local clone hardlinks the object store, so it is near-instant and does not double the disk. The clone's `origin` is the main `/gm-assistant` checkout, which makes the sync commands below symmetric (`pull origin` / `push origin`). Repo-local git config does NOT copy over, so set the committer identity in the fresh clone before the first commit: `git config user.name "$(git -C /gm-assistant config user.name)" && git config user.email "$(git -C /gm-assistant config user.email)"` (run inside the clone).
- **Git ownership.** Inside the clone, and for syncing the clone back into main, the session performs ALL git actions itself (add / commit / merge / push-back to main). The GM's only git job is the **GitHub push/pull from main**: after a session stops working, `git status` in `/gm-assistant` shows main "ahead of origin/main by N commits", fully committed and ready for the GM to examine and push. Never push to GitHub yourself, and (per the Core Rules) never commit or push against `/host-l7r-repo`.
- **A clone captures only committed state.** Under this workflow main is normally fully committed, but the GM's own in-progress edits in main may not be - if the task depends on the GM's latest hand edits, ask them to commit first; otherwise note that uncommitted main-tree files are absent from the clone.
- **Stop-work ritual - run EVERY time you stop working** (reporting a task done, reaching a milestone, or pausing for GM input). **SCRIPTED (GM 2026-07-21): run [`scripts/sync-with-main.sh`](scripts/sync-with-main.sh) from inside the clone instead of hand-typing the steps** - `sync-with-main.sh sync-in` (start of work), `sync-with-main.sh push` (commit first yourself; locked pull+push, exit 3 = incoming changes overlapped your files, rerun the gate and fix forward), `sync-with-main.sh render-sync` (regenerates main's renders IN PLACE from main's tip, cache-short-circuited, under the lock), `sync-with-main.sh done` (push + render-sync). Hand-typed rituals caused every sync incident on record (skipped flock, wrong-cwd rsync, error-suppressed cp, stray Mode A outputs); the numbered steps below are the SPEC the script implements - and the fallback if it misbehaves:
  1. **Commit** all work in the clone with a normal descriptive message.
  2. **Sync in + push back as ONE command under the ritual lock.** From inside the clone:

     ```
     flock /gm-assistant/.clones/.ritual.lock sh -c 'git pull --no-rebase origin main && git push origin main'
     ```

     The flock serializes every session's pull-and-push (two sessions finishing in the same minute is real - it happened 2026-07-20, two pushes landing in the same second), so no other session can slip a push into the gap between your merge of main's tip and your push. The lock is held only for the seconds the pull+push take. Main has `receive.denyCurrentBranch = updateInstead` set (one-time setup: `git -C /gm-assistant config receive.denyCurrentBranch updateInstead`; redo after any fresh checkout of this repo), so the push also updates main's working tree.
  3. **If the locked command fails, fix in the clone and re-run it - NEVER `git push --force`.** The failure modes:
     - **Merge conflicts** (the pull stopped): resolve them in the clone, and if the merge brought in someone else's changes to files you touched, rerun the relevant gate (`make done` for webapp work, the skill's `pytest --cov` for skill work) - conflict resolution and gate runs happen OUTSIDE the lock (a 15-minute test run must never hold it) - then commit the merge and re-run the locked command. This converges: each round merges whatever landed meanwhile.
     - **Clean auto-merge that touched your files** (the locked command succeeded, but the pull's merge combined someone else's edits with yours in the same files): the push has already happened, so rerun the relevant gate NOW and **fix forward** - commit any fix and run the locked command again immediately. A briefly-broken main between the two pushes is tolerable because every session's sync-in gate rerun catches it; an unexamined semantic clash is not.
     - **Push rejected as non-fast-forward** (only possible if the lock was skipped): the rejection is git's ref serialization working as designed - the answer is another pull/retest/push round, never force. Forcing is the ONE thing that overwrites other sessions' work (2026-07-20: a session answered this rejection with a force push and briefly clobbered main's branch; recovered via the reflog).
  4. **If the push is refused by updateInstead** (main has uncommitted changes to tracked files), fall back to `git -C /gm-assistant pull --ff-only .clones/<session-name> main`; if that is also refused, stop and tell the GM main needs a commit or stash - do not force anything.
  5. **Regenerate main's diagram renders in place (GM 2026-07-22, replacing the old build-in-clone-then-copy machinery).** Main's working tree is where the GM browses EVERY pool render in one place, so the gitignored derived renders (Mode B `.svg`+`.png` in `pool/{hamlets,villages,towns,provincial-cities}/`, Mode A `.png` in `pool/magistracies/`) must be current in main even though git never carries them - stale or missing renders in main are a bug, not "normal drift". The old approach BUILT renders in the clone and COPIED them into main (rsync + tip-guard + byte-verify); that was fragile because whether a clone had refreshed a given render was situational, so a stale copy could linger. **The new rule: after the push, main regenerates its OWN renders from its OWN committed tip** - a render in main is a pure function of main's code, so it can never be a stale copy. `sync-with-main.sh render-sync` (folded into `done`) runs it:
     - It invokes [`render_cache.py`](.claude/skills/diagram/render_cache.py) against main's pool under the ritual lock, with `GM_ASSISTANT_ALLOW_MAIN=1` so the engine's main-tree guard stands down for this ONE sanctioned regen-in-main. Each generator runs from its OWN directory (the Mode A cwd trap), and the raster is the generators' own resvg call, so no separate render command is needed.
     - **The regen is unconditional but cheap**, because it short-circuits on a content hash. Every derived (Mode B) svg is stamped `<!-- render-cache: <sha256> -->`, where the hash covers that map's `gen.py` source AND the shared engine sources. render-sync skips any map whose stamp is fresh and whose png is present, and re-runs the rest. So it is self-healing (main re-derives correct renders from tip regardless of history - even after a crashed prior session) yet a push that changed nothing a map depends on costs ~0.3s; an engine change restamps every map and does the full ~30s refresh. Mode A magistracy plans (tracked svg source, only the png gitignored) are exempt from the cache: they always re-run and reproduce their tracked svg byte-identically (never stamped - a comment would dirty a tracked file), so their gitignored png is refreshed each time. This is the whole reason the old TIP-GUARD / last-writer-wins / byte-verify dance is gone: regenerating whatever tip main currently holds is always correct, and a redundant run just finds every stamp fresh and skips.
     - This is the ONE sanctioned write into main's tree, and it is now the ONE place a session runs generators against main - held under the lock, so it cannot race another session's push-to-checkout. If the regen leaves any TRACKED pool file dirty (a `.json` manifest or a Mode A `.svg`), a generator is nondeterministic: render-sync warns loudly and you must investigate (a dirty tracked file also blocks the next session's `updateInstead` push). Do not hand-copy renders and do not run generators against main by any other path.
- **Main is the integration point, never a workspace: the ONLY thing a session runs in main's tree is render-sync (step 5).** No other generators, no tests, no writes - any other command writing into `/gm-assistant` races with another session's mid-ritual push-to-checkout (2026-07-20: a derived-file regen run in main during another session's push produced a confusingly mixed tree). render-sync itself is safe only because it holds the ritual lock and regenerates from main's own committed tip. Read-only commands against main (`git log`, `git status`, greps) stay fine. **This rule is SELF-ENFORCED**: the diagram skill (`settlement.py` import-time, which every gen/gate/test imports), the webapp rootdir `conftest.py`, and both Makefiles abort with a reminder pointing here when run from main's tree - if you hit that error, re-read this section (reload CLAUDE.md if it has fallen out of context) and rerun from your clone. `GM_ASSISTANT_ALLOW_MAIN=1` is that guard's override: the GM sets it for a deliberate main-tree run, and render-sync sets it (scoped to its one locked regen) - a session never sets it by hand for anything else. (`make serve` in the webapp is exempt - the GM legitimately serves the toolkit from main.)
- **Gotchas:** keep `pytest`/`ripgrep` scoped to the working dir (git ignores `.clones/`, but those tools do not read `.gitignore`, so a repo-root `pytest` would double-collect every clone's tests). Self-contained features (e.g. `/diagram`) run fully in the clone; a feature that needs `/host-l7r-repo` or `development-secrets.ini` still reaches them by absolute path - only repo-relative paths shift into the clone.

**Launching the container**: prefer [`scripts/launch-container.sh`](scripts/launch-container.sh) over a hand-edited podman command. Run it from the repo root: if this repo's container is already running it opens a fresh `bash` shell inside that one (and prints the ports it has published); otherwise it starts a new detached container named `claude-<repo-dir>` (PID 1 is `sleep infinity` and every terminal - including the first - is a `podman exec` shell, so exiting any terminal leaves the container and the other shells running; it persists until `--fresh` or `podman rm -f`), mounting the repo at `/gm-assistant` plus the host `~/.claude/` and `~/.claude.json`, and publishing/mounting whatever this file declares. Those declarations are the two greppable HTML comments near the top of this file: `container-ports` (HOST:CONTAINER, primary webapp first, secondary blind-eval webapp second) and `container-mounts` (HOST:CONTAINER). Host and container ports may differ so multiple repos that all serve on 8080 internally can each get a distinct host port; here container 8080 (the toolkit) maps to host 8080 and container 8090 (the bakeoff blind-eval app) maps to host 8091. Mount host paths are resolved relative to the repo root (or `~`, or absolute), so `..:/host-l7r-repo` mounts the repo's parent directory - the GM keeps each project repo as a sibling inside the `l7r` notes repo (`<l7r>/gm-assistant`, `<l7r>/character-sheet`, ...), so the parent is always the canonical `l7r` checkout regardless of where the tree lives. The same script works for the GM's other repos - each just needs its own `container-ports`/`container-mounts` lines. `--fresh` recreates from scratch; `--no-ports` skips publishing; `--no-claude` skips mounting the host `~/.claude*` (use it on a shared/work machine so the container does not inherit that host's default Claude account - log in fresh inside instead; `CLAUDE_SRC=/path` points at a specific config dir).

**Fresh-container init (start here on every new container)**: the container is launched via [`scripts/launch-container.sh`](scripts/launch-container.sh) (see above; [`/gm-assistant/README.md`](README.md) keeps the legacy hand-written podman command for reference, but that one is the old attached `--rm` design) - it bind-mounts the repo at `/gm-assistant`, the GM's `l7r` repo at `/host-l7r-repo`, and the host's `~/.claude/` + `~/.claude.json` into `/home/agent/` so Claude Code auth, preferences, agents, skills, and per-project memory all persist across container rebuilds. Once you're inside, from `/gm-assistant/webapp/`:

```
pip install --break-system-packages -r requirements.txt -r requirements-dev.txt # prod + dev deps
python3 -m playwright install chromium                                          # one-time browser download for Principle I screenshots
```

After that, `make done` should pass (ruff + format + mypy --strict + pytest + 100% coverage) and `cherryd --import l7r` runs the app at `http://0.0.0.0:8080`.

Prod and dev deps are split into two lockfiles - `requirements.txt` (what the Fly image installs) and `requirements-dev.txt` (ruff/mypy/pytest/pytest-cov/pytest-xdist/playwright/pip-tools). Both lockfiles target **Python 3.14**, which is what ships in both the dev container (`docker.io/docker/sandbox-templates:claude-code`) and the Fly prod image (`python:3.14-slim`, see [`webapp/Dockerfile`](webapp/Dockerfile)). The version is also pinned in `webapp/pyproject.toml` (`requires-python`, ruff `target-version`, mypy `python_version`). Re-lock either file with `pip-compile --upgrade --output-file=<file>.txt <file>.in` from `/gm-assistant/webapp/` (sources are `requirements.in` and `requirements-dev.in`). If you bump the Python version, update all four locations (Dockerfile, pyproject.toml, both lockfiles) together - they're meant to stay aligned.

The server binds to `0.0.0.0:8080` automatically when it detects a container runtime (podman's `/run/.containerenv` or docker's `/.dockerenv`), so podman's `--publish 8080:8080` reaches it from the host. On a bare host (no container markers, no `FLY_APP_NAME`) it stays on the CherryPy default `127.0.0.1`. Fly continues to bind 0.0.0.0 via `FLY_APP_NAME`, and the X-Forwarded-Proto trust setting is still gated on `FLY_APP_NAME` alone - podman doesn't have a TLS-terminating proxy in front, so we don't want cherrypy.url() emitting `https://` URLs there. Logic lives in `l7r/app.py:_apply_server_config`.

**Key paths**:

- `.specify/memory/constitution.md` - the constitution
- `.specify/templates/plan-template.md` - Constitution Check gate lives here
- `/gm-assistant/webapp-prototype/` - static frontend prototypes (current: relics index + detail)
- `/gm-assistant/webapp/` - **L7R Toolkit** (CherryPy + Jinja2). Run with `cherryd --import l7r` from this dir. Routes: `/` landing, `/relics`, `/relics/<slug>`, `/names` (with `?gender=` / `?caste=` filters), `/places`, `/places/<slug>`, `/dreams` (dream-divination framework + example gallery, public `pool/` tier only), `/dreams/<slug>`, `/chargen/*` (legacy chargen mounted as a sub-app). New code under `l7r/` package; legacy chargen modules on Principle X grace period.
- `/gm-assistant/webapp/Makefile` - `make done` runs ruff + format check + mypy --strict + pytest + 100% coverage gate
- `/gm-assistant/webapp/tests/screenshot.py` and `tests/dom_audit.py` - Playwright suite for Principle I verification at GM-100 / GM-200 / tablet / mobile. The screenshot script outputs multi-scroll contact sheets to `/tmp/l7r-shots/sheet-<page>-<viewport>.png`.
- `/gm-assistant/.claude/agents/frontend-review.md` - independent design-review subagent. Invoke before declaring a UI change done if the same agent implemented AND reviewed.
- `/gm-assistant/.claude/agents/backstory-review.md` - independent review of synthesized NPC prose (`/synthesize`, `/chargen`), run automatically by those skills before the GM sees a backstory. Holds a **growing catalog of previously GM-caught mistakes** plus the baseline canon/style rules and sweeps them by enumeration, so recurring errors are fixed in-session. When the GM catches a new category of mistake in generated prose, distil it into a general rule here (follow the Subagent-check TDD procedure).
- `/gm-assistant/.claude/skills/relic/pool/` - exemplar of the pool data convention (Principle III)
- `/gm-assistant/.claude/skills/name/pool-male.jsonl` + `pool-female.jsonl` - the 200-name pool consumed by the `/names` section

Spec-kit features (the `specify` -> `plan` -> `tasks` -> `implement` flow) live under `specs/NNN-*/`. There is deliberately **no single "active plan" tracked here** - a hardcoded pointer just goes stale as features come and go. For current status, look at the highest-numbered `specs/` dir, its `tasks.md` checkboxes, and `git log`.
