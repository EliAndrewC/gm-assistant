# L5R Setting Generation Project

This project is a Legend of the Five Rings tabletop RPG worldbuilding environment. The GM uses Claude Code to generate setting details (NPCs, locations, items, etc.) guided by their extensive setting notes and evolving preferences.

## Core Rules

### Canonical Source and Syncing

The GM maintains a canonical notes file at https://raw.githubusercontent.com/EliAndrewC/l7r/refs/heads/master/ai/l7r.txt A local copy is saved at `/notes/canonical-source.txt` as a snapshot of what was last parsed. When the GM indicates the canonical source has been updated, or at the start of a session when asked:

1. Fetch the current version from the remote URL.
2. Diff against `/notes/canonical-source.txt` to identify what changed.
3. Propagate changes to the appropriate downstream files (skill files, reference directories, etc.) — updating the GM's words within their `SOURCE: GM NOTES` markers to match the new canonical version.
4. Overwrite `/notes/canonical-source.txt` with the new version so it's ready for the next diff.

This is the one exception to the "don't modify the GM's words" rule: when the canonical source itself has changed, downstream copies must be updated to match.

### Protecting the GM's Writing

Content between `<!-- SOURCE: GM NOTES — DO NOT MODIFY -->` and `<!-- END SOURCE -->` markers is the GM's original writing. These sections must NEVER be modified, rephrased, summarized, reworded, or "improved" in any way. Only the GM may edit these sections, and only when they explicitly instruct you to do so.

The sole exception is syncing from the canonical source (see above) — if the GM has updated their original notes, the downstream copies must be updated to match exactly.

AI-generated content (preferences, generation instructions, examples of liked/disliked output) lives outside these markers and can be updated as the GM's preferences evolve.

This convention applies to ALL files in the project — both skill files and reference directory files.

### File Organization

#### Skills (invocable as /slash-commands)

Each skill lives in `/.claude/skills/<skill-name>/SKILL.md` with YAML frontmatter. Skills are for *generating* specific types of content.

#### Reference Directories (not invocable, indexed by CLAUDE.md)

Reference directories hold organized source material and context. Each directory has its own `CLAUDE.md` that indexes and explains its contents. Skills should reference these directories when they need shared context.

- `/setting/` — Demographics, castes, currency, samurai ranks, government structure (Six Ministries), geography, lineage system, merchant families, ashigaru, experience levels
- `/campaigns/` — Campaign-specific material: Karmic Inquisitors, First Toshi Ranbo, Hidden Way, Wasp Bounty Hunters, timelines, PC/NPC backstories, the Order of Lord Moon
- `/hooks/` — Adventure hooks organized by type (countryside, town, city, caravan, prison camp), grifts and scams
- `/cosmology/` — Lord Moon's heavenly court, mythological stories/fables, maho & bloodspeakers, "between places", gaijin religions (Uru, Burning Sands), Fortune theology, soothsaying
- `/notes/` — The canonical source snapshot and any material not yet organized elsewhere

### Generation Behavior

- When generating content, draw on the GM's source notes for tone, style, and setting details.
- Preference feedback from the GM is captured in memory and incorporated into skill files over time.
- Never invent setting details that contradict the GM's source notes.
- Skills should reference the relevant reference directories for shared context (e.g., `/temple` should draw on `/setting/` for demographics and `/cosmology/` for Fortune theology).

## Skills

| Skill | Purpose |
|-------|---------|
| `/sword` | Generate famous swords with histories and properties |
| `/temple` | Generate temples, relics, monk NPCs, temple daily life |
| `/vow` | Generate oaths and vows for various orders and roles |
| `/village` | Generate farming villages, hamlets, village headsmen |
| `/calendar` | Generate seasonal details, festivals, agricultural events |
| `/law` | Generate legal cases, rulings, magistrate proceedings |
| `/fortune` | Generate cosmological content, soothsaying, omens, Fortune theology |
| `/moto` | Generate Moto culture content, Yassa rulings, horse culture, Burning Sands |
| `/bounty` | Generate bounties, Wasp clan content, minor clan details |

## Reference Directories

| Directory | Contents |
|-----------|----------|
| `/setting/` | Demographics, government, ranks, castes, economics, geography |
| `/campaigns/` | Campaign timelines, NPC/PC backstories, Order of Lord Moon |
| `/hooks/` | Adventure hooks by setting type |
| `/cosmology/` | Moon court, stories, maho, gaijin religion, Fortune theology |
| `/notes/` | Canonical source snapshot |
