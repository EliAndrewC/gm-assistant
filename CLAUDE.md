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
| `/synthesize` | Write a backstory for an existing Obsidian Portal NPC, Claude-native (in-session prose - no external LLM; the webapp button still uses Gemini): reads the OP record + tagline and the campaign-context cast, researches the setting files directly, review (upload as-is / regenerate / upload with typed changes), merges into GM-only notes. Args: `<character name> [ - steering]` |

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

**Subagent-check TDD (REQUIRED procedure for improving review subagents)**: when the GM asks for a new rule that a review subagent (e.g. `building-review`) should enforce, do NOT simply apply the fix and write the rule into the agent. The current artifacts contain the motivating defect - that is the failing test. Procedure:

1. Add only the **general, category-level rule** to the agent definition. Never name the specific instance yet - that would test nothing about whether the check generalizes.
2. Run the agent against the artifact that contains the known defect, unfixed.
3. **If it flags the defect**, the rule generalizes: now fix the artifacts, and only now record the specific instance in the agent definition as a validated example for future runs.
4. **If it misses**, sharpen the general rule and re-run - do not shortcut by naming the instance. Escalation ladder from the first application (2026-07): a trait buried in a checklist gets skimmed; adding a protocol step barely helps; what reliably works is making the agent's **output format demand an enumerated sweep** (a mandatory report section listing every item checked) - models do what the required output structure forces.
5. Record the red/green outcome in the artifact's review log.

**Gotcha (harness behavior)**: agent definitions are snapshotted when the session registers them - mid-session edits to `.claude/agents/*.md` do NOT reach agents launched by type, which silently invalidates the TDD run. When iterating on an agent definition, launch a `general-purpose` agent instructed to Read the definition file and adopt it; the registered type picks up the changes next session.

**Spec-kit hooks**: `.specify/extensions.yml` defines auto-commit hooks before each spec-kit step. Per the project's git-safety convention, do not auto-execute those - surface them and let the user confirm each time.

**Launching the container**: prefer [`scripts/launch-container.sh`](scripts/launch-container.sh) over a hand-edited podman command. Run it from the repo root: if this repo's container is already running it opens a fresh `bash` shell inside that one (and prints the ports it has published); otherwise it starts a new `--rm` container named `claude-<repo-dir>`, mounting the repo at `/gm-assistant` plus the host `~/.claude/` and `~/.claude.json`, and publishing/mounting whatever this file declares. Those declarations are the two greppable HTML comments near the top of this file: `container-ports` (HOST:CONTAINER, primary webapp first, secondary blind-eval webapp second) and `container-mounts` (HOST:CONTAINER). Host and container ports may differ so multiple repos that all serve on 8080 internally can each get a distinct host port; here container 8080 (the toolkit) maps to host 8080 and container 8090 (the bakeoff blind-eval app) maps to host 8091. Mount host paths are resolved relative to the repo root (or `~`, or absolute), so `..:/host-l7r-repo` mounts the repo's parent directory - the GM keeps each project repo as a sibling inside the `l7r` notes repo (`<l7r>/gm-assistant`, `<l7r>/character-sheet`, ...), so the parent is always the canonical `l7r` checkout regardless of where the tree lives. The same script works for the GM's other repos - each just needs its own `container-ports`/`container-mounts` lines. `--fresh` recreates from scratch; `--no-ports` skips publishing; `--no-claude` skips mounting the host `~/.claude*` (use it on a shared/work machine so the container does not inherit that host's default Claude account - log in fresh inside instead; `CLAUDE_SRC=/path` points at a specific config dir).

**Fresh-container init (start here on every new container)**: the container is launched via [`scripts/launch-container.sh`](scripts/launch-container.sh) (see above; the legacy hand-written podman command in [`/gm-assistant/README.md`](README.md) does the same thing) - it bind-mounts the repo at `/gm-assistant`, the GM's `l7r` repo at `/host-l7r-repo`, and the host's `~/.claude/` + `~/.claude.json` into `/home/agent/` so Claude Code auth, preferences, agents, skills, and per-project memory all persist across container rebuilds. Once you're inside, from `/gm-assistant/webapp/`:

```
pip install --break-system-packages -r requirements.txt -r requirements-dev.txt # prod + dev deps
python3 -m playwright install chromium                                          # one-time browser download for Principle I screenshots
```

After that, `make done` should pass (ruff + format + mypy --strict + pytest + 100% coverage) and `cherryd --import l7r` runs the app at `http://0.0.0.0:8080`.

Prod and dev deps are split into two lockfiles - `requirements.txt` (what the Fly image installs) and `requirements-dev.txt` (ruff/mypy/pytest/pytest-cov/playwright/pip-tools). Both lockfiles target **Python 3.13**, which is what ships in both the dev container (`docker.io/docker/sandbox-templates:claude-code`) and the Fly prod image (`python:3.13-slim`, see [`webapp/Dockerfile`](webapp/Dockerfile)). The version is also pinned in `webapp/pyproject.toml` (`requires-python`, ruff `target-version`, mypy `python_version`). Re-lock either file with `pip-compile --upgrade --output-file=<file>.txt <file>.in` from `/gm-assistant/webapp/` (sources are `requirements.in` and `requirements-dev.in`). If you bump the Python version, update all four locations (Dockerfile, pyproject.toml, both lockfiles) together - they're meant to stay aligned.

The server binds to `0.0.0.0:8080` automatically when it detects a container runtime (podman's `/run/.containerenv` or docker's `/.dockerenv`), so podman's `--publish 8080:8080` reaches it from the host. On a bare host (no container markers, no `FLY_APP_NAME`) it stays on the CherryPy default `127.0.0.1`. Fly continues to bind 0.0.0.0 via `FLY_APP_NAME`, and the X-Forwarded-Proto trust setting is still gated on `FLY_APP_NAME` alone - podman doesn't have a TLS-terminating proxy in front, so we don't want cherrypy.url() emitting `https://` URLs there. Logic lives in `l7r/app.py:_apply_server_config`.

**Key paths**:

- `.specify/memory/constitution.md` - the constitution
- `.specify/templates/plan-template.md` - Constitution Check gate lives here
- `/gm-assistant/webapp-prototype/` - static frontend prototypes (current: relics index + detail)
- `/gm-assistant/webapp/` - **L7R Toolkit** (CherryPy + Jinja2). Run with `cherryd --import l7r` from this dir. Routes: `/` landing, `/relics`, `/relics/<slug>`, `/names` (with `?gender=` / `?caste=` filters), `/chargen/*` (legacy chargen mounted as a sub-app). New code under `l7r/` package; legacy chargen modules on Principle X grace period.
- `/gm-assistant/webapp/Makefile` - `make done` runs ruff + format check + mypy --strict + pytest + 100% coverage gate
- `/gm-assistant/webapp/tests/screenshot.py` and `tests/dom_audit.py` - Playwright suite for Principle I verification at GM-100 / GM-200 / tablet / mobile. The screenshot script outputs multi-scroll contact sheets to `/tmp/l7r-shots/sheet-<page>-<viewport>.png`.
- `/gm-assistant/.claude/agents/frontend-review.md` - independent design-review subagent. Invoke before declaring a UI change done if the same agent implemented AND reviewed.
- `/gm-assistant/.claude/skills/relic/pool/` - exemplar of the pool data convention (Principle III)
- `/gm-assistant/.claude/skills/name/pool-male.jsonl` + `pool-female.jsonl` - the 200-name pool consumed by the `/names` section

<!-- SPECKIT START -->
Current active plan: [`specs/004-synthesize-op-npc/plan.md`](specs/004-synthesize-op-npc/plan.md)
Active feature: /synthesize skill - chat-driven backstory synthesis for existing Obsidian Portal NPCs (reads the OP tagline, reuses the webapp's per-caste corpus + campaign context, review with upload/regenerate/upload-with-typed-changes, idempotent GM-notes merge)
Feature directory: `specs/004-synthesize-op-npc/`
<!-- SPECKIT END -->
