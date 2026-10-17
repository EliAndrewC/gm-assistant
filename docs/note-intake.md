# Note intake workflow (full text)

*Project reference, moved out of [`../CLAUDE.md`](../CLAUDE.md) on 2026-10-17 so it is loaded on demand rather than in every session (and every subagent) context. CLAUDE.md keeps the one-line always-on version of each rule.*

**Load this file when:** the GM pastes raw campaign notes into the chat (table events, lore, NPC beats, world-building) to be written up into `l7r.md` and Obsidian Portal.

---

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
- OAuth creds live in `[obsidian_portal]` of `development-secrets.ini`; rotation via `probe_op_oauth.py --full` (see [`/gm-assistant/webapp/probe_op_oauth.py`](../webapp/probe_op_oauth.py)).
- This workflow is intentionally **not a skill**: its summary and trigger are in the always-loaded CLAUDE.md, and this doc is the full procedure. Skills in this project are content *generators*; intake is a routing workflow that should be present in every session's context.
