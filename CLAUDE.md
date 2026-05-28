# L5R Setting Generation Project

This project is a Legend of the Five Rings tabletop RPG worldbuilding environment. The GM uses Claude Code to generate setting details (NPCs, locations, items, etc.) guided by their extensive setting notes and evolving preferences.

## Core Rules

### Canonical Source and Syncing

The GM maintains a canonical notes file at https://raw.githubusercontent.com/EliAndrewC/l7r/refs/heads/master/ai/l7r.txt A local copy is saved at `/notes/canonical-source.txt` as a snapshot of what was last parsed. When the GM indicates the canonical source has been updated, or at the start of a session when asked:

1. Fetch the current version using the GitHub API (not raw.githubusercontent.com, which has aggressive CDN caching that serves stale content). Use this exact command to fetch and decode:
   ```
   curl -sL "https://api.github.com/repos/EliAndrewC/l7r/contents/ai/l7r.txt?ref=master" | python3 -c "
   import sys, json, base64
   data = json.load(sys.stdin)
   content = base64.b64decode(data['content']).decode('utf-8')
   with open('/tmp/new-canonical-api.txt', 'w') as f:
       f.write(content)
   "
   ```
   IMPORTANT: Always use `/tmp/new-canonical-api.txt` as the freshly fetched file for all subsequent steps. Never diff or compare against a file fetched via raw.githubusercontent.com or any previously cached download. If you have already fetched the file earlier in the conversation, fetch it again — do not reuse a previous download.
2. Diff `/tmp/new-canonical-api.txt` against `/notes/canonical-source.txt` to identify what changed.
3. Propagate changes to the appropriate downstream files (skill files, reference directories, etc.) - updating the GM's words within their `SOURCE: GM NOTES` markers to match the new canonical version.
4. Overwrite `/notes/canonical-source.txt` with `/tmp/new-canonical-api.txt` so it's ready for the next diff. Do NOT update the snapshot until all downstream files have been verified as correct.

This is the one exception to the "don't modify the GM's words" rule: when the canonical source itself has changed, downstream copies must be updated to match.

### Protecting the GM's Writing

Content between `<!-- SOURCE: GM NOTES - DO NOT MODIFY -->` and `<!-- END SOURCE -->` markers is the GM's original writing. These sections must NEVER be modified, rephrased, summarized, reworded, or "improved" in any way. Only the GM may edit these sections, and only when they explicitly instruct you to do so.

The sole exception is syncing from the canonical source (see above) - if the GM has updated their original notes, the downstream copies must be updated to match exactly.

AI-generated content (preferences, generation instructions, examples of liked/disliked output) lives outside these markers and can be updated as the GM's preferences evolve.

This convention applies to ALL files in the project - both skill files and reference directory files.

### Single Canonical Home for Source Blocks

Each piece of GM source content has exactly **one** canonical home — a single `SOURCE: GM NOTES` block in one file. Other files that conceptually relate to that content link to the canonical home by reference rather than duplicating the block.

This keeps canonical-source syncs surgical: when the GM updates their notes, only one downstream file needs to change per concept. It also prevents drift, since there is no second copy to fall out of sync.

When deciding the canonical home for a given source block:

- If the content is primarily *generation guidance* (how to write a kind of thing, with examples) → it belongs in the relevant skill's `SKILL.md`
- If the content is primarily *setting reference* (demographics, geography, hierarchies, fixed facts) → it belongs in a file under the appropriate reference directory
- If both, pick whichever the content leans toward more heavily and have the other side reference it

**Exception:** `/notes/canonical-source.txt` is a sync baseline (the diff target for canonical-source updates from GitHub), not a reference document. It mirrors the canonical source from the GM's GitHub repository by design, and the duplication there is intentional and necessary for the sync workflow described above.

### File Organization

#### Skills (invocable as /slash-commands)

Each skill lives in `/.claude/skills/<skill-name>/SKILL.md` with YAML frontmatter. Skills are for *generating* specific types of content.

#### Reference Directories (not invocable, indexed by CLAUDE.md)

Reference directories hold organized source material and context. Each directory has its own `CLAUDE.md` that indexes and explains its contents. Skills should reference these directories when they need shared context.

- `/setting/` - Demographics, castes, currency, samurai ranks, government structure (Six Ministries), geography, lineage system, merchant families, ashigaru, experience levels
- `/campaigns/` - Campaign-specific material: Karmic Inquisitors, First Toshi Ranbo, Hidden Way, Wasp Bounty Hunters, timelines, PC/NPC backstories, the Order of Lord Moon
- `/hooks/` - Adventure hooks organized by type (countryside, town, city, caravan, prison camp), grifts and scams
- `/cosmology/` - Lord Moon's heavenly court, mythological stories/fables, maho & bloodspeakers, "between places", gaijin religions (Uru, Burning Sands), Fortune theology, soothsaying
- `/notes/` - The canonical source snapshot and any material not yet organized elsewhere

### Generation Behavior

- When generating content, draw on the GM's source notes for tone, style, and setting details.
- Preference feedback from the GM is captured in memory and incorporated into skill files over time.
- Never invent setting details that contradict the GM's source notes.
- Skills should reference the relevant reference directories for shared context (e.g., `/temple` should draw on `/setting/` for demographics and `/cosmology/` for Fortune theology).
- **Constitution Principle XI** (Japanese Authenticity): any kanji that surfaces in generated content — relic names, sword names, given names, temple titles, vow refrains, decorative stamps — must pass the kanji ↔ romaji ↔ meaning triangle. Real characters, plausible reading, English meaning that maps back. Stylized readings are allowed when explained in surrounding prose.

## Skills

| Skill | Purpose |
|-------|---------|
| `/sword` | Generate famous swords with histories and properties |
| `/temple` | Generate temples, monk NPCs, temple daily life |
| `/relic` | Generate temple relics, cursed items, supposedly-supernatural objects |
| `/vow` | Generate oaths and vows for various orders and roles |
| `/village` | Generate farming villages, hamlets, village headsmen |
| `/calendar` | Generate seasonal details, festivals, agricultural events |
| `/law` | Generate legal cases, rulings, magistrate proceedings |
| `/fortune` | Generate cosmological content, soothsaying, omens, Fortune theology |
| `/moto` | Generate Moto culture content, Yassa rulings, horse culture, Burning Sands |
| `/bounty` | Generate bounties, Wasp clan content, minor clan details |
| `/name` | Generate Rokugani personal names with meanings in varied formats. Args: `[m\|f] [p] [N]` — supports shorthand and concatenation (e.g. `pf3`) |

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
| `/notes/` | Canonical source snapshot |

## Development Workflow

This project uses spec-driven development governed by [`.specify/memory/constitution.md`](.specify/memory/constitution.md) (currently v1.1.0, 10 principles, 3 NON-NEGOTIABLE). The constitution is the higher-level authority; this CLAUDE.md operationalizes it.

**When to use spec-kit:**

- **Feature work** (new sections of the webapp, new skills, new generators, the upcoming Python backend) → invoke `/speckit-specify` and follow through plan → tasks → implement. The Constitution Check section in `.specify/templates/plan-template.md` is the gate that enforces the constitution at plan-time; skipping spec-kit on feature work means skipping that gate.
- **Tweaks and iteration** (CSS adjustments, wording fixes, regenerating one item, fixing one bug) → just do the work directly. The constitution still applies, but the formal spec/plan/tasks flow is overkill.
- **Ambiguous cases** → ask before chain-firing `/speckit-specify`.

**Verification before reporting "done"** (per Principle VI of the constitution):

- **UI changes**: run `/workspace/webapp-prototype/relics/screenshot.py` (or analogous) — captures screenshots at GM-100 (1850×1050), GM-200 (925×525), tablet (800×1100), and mobile (390×844) viewports and runs a DOM-overflow audit. The user uses Chrome at 200% zoom; UI must be clean at that zoom.
- **Python changes**: `ruff check` + `ruff format --check` + `mypy --strict` + `pytest` + `--cov-fail-under=100` on pure-logic packages (Principle X).
- **Delegated work**: spot-check actual artifacts before relaying success to the user. "The subagent said it was done" is not sufficient.

**Spec-kit hooks**: `.specify/extensions.yml` defines auto-commit hooks before each spec-kit step. Per the project's git-safety convention, do not auto-execute those — surface them and let the user confirm each time.

**Key paths**:

- `.specify/memory/constitution.md` — the constitution
- `.specify/templates/plan-template.md` — Constitution Check gate lives here
- `/workspace/webapp-prototype/` — static frontend prototypes (current: relics index + detail)
- `/workspace/webapp/` — **L7R Toolkit** (CherryPy + Jinja2). Run with `cherryd --import l7r` from this dir. Routes: `/` landing, `/relics`, `/relics/<slug>`, `/names` (with `?gender=` / `?caste=` filters), `/chargen/*` (legacy chargen mounted as a sub-app). New code under `l7r/` package; legacy chargen modules on Principle X grace period.
- `/workspace/webapp/Makefile` — `make done` runs ruff + format check + mypy --strict + pytest + 100% coverage gate
- `/workspace/webapp/tests/screenshot.py` and `tests/dom_audit.py` — Playwright suite for Principle I verification at GM-100 / GM-200 / tablet / mobile
- `/workspace/.claude/skills/relic/pool/` — exemplar of the pool data convention (Principle III)
- `/workspace/.claude/skills/name/pool-male.jsonl` + `pool-female.jsonl` — the 200-name pool consumed by the `/names` section

<!-- SPECKIT START -->
Current active plan: [`specs/001-toolkit-shell/plan.md`](specs/001-toolkit-shell/plan.md)
Active feature: L7R Toolkit Phase 1 — App Shell + Chargen + Relics
Feature directory: `specs/001-toolkit-shell/`
<!-- SPECKIT END -->
