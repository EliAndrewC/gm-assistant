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

## Note Intake Workflow

When the GM hands you raw campaign notes — actions a character took at the table, new lore that came up in play, NPC backstory beats, world-building ideas — your job is to **copy-edit lightly** and **route to the right sinks**. There are three sinks, and most intakes touch more than one.

**The three sinks**:

1. **A specific character's bio or GM-only notes** on Obsidian Portal. Use when the intake is about something a single character did, was, or knows.
   - Public bio (visible to all players): `op.update_character(id, bio=...)`
   - GM-only notes: `op.update_character(id, game_master_info=...)`
   - Also `name`, `tagline`, `description`, `tags`. Avatars/images go via the browser-sim path — the OAuth API silently no-ops on avatar fields.
   - Listing + lookup: `op.existing_characters()` returns `{id, slug, name, …}` dicts; filter by name/slug to find the target.

2. **A wiki page** on Obsidian Portal. Use when the intake is about a place, faction, institution, ongoing event, or any world-level fact that isn't tied to a single character.
   - Public body (Textile markup): `op.update_wiki_page(id, body=...)`
   - GM-only section: `op.update_wiki_page(id, game_master_info=...)`
   - Also `name`, `tags`, `is_game_master_only`, `post_title`/`post_tagline`/`post_time` (the blog-post fields, for Adventure Log entries).
   - Listing + lookup: `op.existing_wiki_pages()` returns `{id, slug, name, wiki_page_url, …}`. If no matching page exists, **ask before creating one** — page proliferation is hard to undo.
   - Body is Textile, not Markdown. Match the conventions of nearby pages (`\r\n` line endings, `bq).` for blockquotes, `[[wiki-slug]]` for internal links).

3. **The canonical `l7r.md`** (the GM's giant unified notes file). Use *in addition to* whichever OP sink fired, so the GM's authoritative source-of-truth captures everything that made it into the campaign.
   - Path inside this container: **`/host-l7r-repo/ai/l7r.txt`** (the GM's `EliAndrewC/l7r` repo, volume-mounted from the host). If that path doesn't exist, the mount isn't set up; ask before falling back to the snapshot at `/notes/canonical-source.txt`.
   - After every edit to `/host-l7r-repo/ai/l7r.txt`, ALSO update `/notes/canonical-source.txt` so the sync-from-GitHub diff workflow stays accurate.
   - The GM commits + pushes the changes from their laptop after the session — you don't run `git` in the mount.

**Routing rules** (decision tree, top-down):

- *"X did Y" / "X said Y" / "X feels Y about Z"* → that character's bio (public-facing thing) or GM-only notes (private/hidden motivation). Look up by name via `existing_characters()`. ALWAYS also reflect in `l7r.md`.
- *"There's a place / institution / faction / ongoing event called X"* → wiki page. If an existing page matches, PATCH; if not, ask before creating. ALWAYS also reflect in `l7r.md`.
- *"The setting works like X" / "Here's how Y works in Rokugan"* → wiki page if it has a natural home, otherwise just `l7r.md` (and consider whether this should also seed a new skill or reference doc).
- *"NPC X is..."* with no character record yet → ask before creating an OP character. Adding a placeholder character is a stronger commitment than appending to `l7r.md`.
- *Ambiguous or touches multiple sinks* → ask. Don't write to OP without explicit routing approval; the GM's voice in published bios + wiki is load-bearing.

**Copy-edit rules**:

- Preserve the GM's voice. Light grammar/structure only — no rewording for "flow," no smoothing that drifts meaning.
- Don't add claims the GM didn't make. If a sentence implies more than was said, ask.
- For wiki sinks: convert to Textile.
- For `l7r.md`: match the surrounding section's tone (raw notes, not a polished article). When inserting, find the right section by topic; don't append at the end if a better-placed paragraph exists.
- Always report back where each piece was written — never assume the GM will read the diff blind.

**Implementation pointers**:

- `/workspace/webapp/chargen/op.py` — all the API helpers (`existing_characters`, `update_character`, `existing_wiki_pages`, `get_wiki_page`, `create_wiki_page`, `update_wiki_page`, `delete_wiki_page`). All use the OAuth path. Image uploads remain browser-sim.
- OAuth creds live in `[obsidian_portal]` of `development-secrets.ini`; rotation via `probe_op_oauth.py --full` (see [`/workspace/webapp/probe_op_oauth.py`](webapp/probe_op_oauth.py)).
- This workflow is intentionally **documented in CLAUDE.md rather than a skill**. Skills in this project are content *generators*; intake is a routing workflow that should be present in every session's context.

## Development Workflow

This project uses spec-driven development governed by [`.specify/memory/constitution.md`](.specify/memory/constitution.md) (currently v1.1.0, 10 principles, 3 NON-NEGOTIABLE). The constitution is the higher-level authority; this CLAUDE.md operationalizes it.

**When to use spec-kit:**

- **Feature work** (new sections of the webapp, new skills, new generators, the upcoming Python backend) → invoke `/speckit-specify` and follow through plan → tasks → implement. The Constitution Check section in `.specify/templates/plan-template.md` is the gate that enforces the constitution at plan-time; skipping spec-kit on feature work means skipping that gate.
- **Tweaks and iteration** (CSS adjustments, wording fixes, regenerating one item, fixing one bug) → just do the work directly. The constitution still applies, but the formal spec/plan/tasks flow is overkill.
- **Ambiguous cases** → ask before chain-firing `/speckit-specify`.

**Verification before reporting "done"** (per Principle VI of the constitution):

- **UI changes** (per Principle I, expanded in v1.3.0):
  - Run `webapp/tests/screenshot.py` to produce **multi-scroll contact sheets** at GM-100 / GM-200 / tablet / mobile. For pages taller than 1.3× viewport, the script captures 0%/33%/66%/100% scroll positions and stitches them horizontally — so layout asymmetry, dead space, and below-fold problems are visible at a glance.
  - Run `webapp/tests/dom_audit.py`. It must report **zero issues** across all pages × viewports. The audit now covers BOTH clipping (overflow, ellipsis, line-clamp) AND layout balance (sibling-height ratio inside flex/grid containers must not exceed 2.5×).
  - **Persona-driven review pass**: before declaring done, examine at least one contact sheet at GM-200 with the user's task in mind (not the implementer's: "Eli is opening this page; what is he trying to do here?"). If the same agent both implemented and reviewed, **invoke the `frontend-review` subagent** (`.claude/agents/frontend-review.md`) to get an independent pass. Author ≠ reliable reviewer.
- **Python changes**: `ruff check` + `ruff format --check` + `mypy --strict` + `pytest` + `--cov-fail-under=100` on pure-logic packages (Principle X).
- **Delegated work**: spot-check actual artifacts before relaying success to the user. "The subagent said it was done" is not sufficient.

**Spec-kit hooks**: `.specify/extensions.yml` defines auto-commit hooks before each spec-kit step. Per the project's git-safety convention, do not auto-execute those — surface them and let the user confirm each time.

**Fresh-container init (start here on every new container)**: the container is launched via the podman command in [`/workspace/README.md`](README.md) — it bind-mounts the repo at `/workspace`, the GM's `l7r` repo at `/host-l7r-repo`, and the host's `~/.claude/` + `~/.claude.json` into `/home/agent/` so Claude Code auth, preferences, agents, skills, and per-project memory all persist across container rebuilds. Once you're inside, from `/workspace/webapp/`:

```
pip install --break-system-packages -r requirements.txt -r requirements-dev.txt # prod + dev deps
python3 -m playwright install chromium                                          # one-time browser download for Principle I screenshots
```

After that, `make done` should pass (ruff + format + mypy --strict + pytest + 100% coverage) and `cherryd --import l7r` runs the app at `http://0.0.0.0:8080`.

Prod and dev deps are split into two lockfiles — `requirements.txt` (what the Fly image installs) and `requirements-dev.txt` (ruff/mypy/pytest/pytest-cov/playwright/pip-tools). Both lockfiles target **Python 3.13**, which is what ships in both the dev container (`docker.io/docker/sandbox-templates:claude-code`) and the Fly prod image (`python:3.13-slim`, see [`webapp/Dockerfile`](webapp/Dockerfile)). The version is also pinned in `webapp/pyproject.toml` (`requires-python`, ruff `target-version`, mypy `python_version`). Re-lock either file with `pip-compile --upgrade --output-file=<file>.txt <file>.in` from `/workspace/webapp/` (sources are `requirements.in` and `requirements-dev.in`). If you bump the Python version, update all four locations (Dockerfile, pyproject.toml, both lockfiles) together — they're meant to stay aligned.

The server binds to `0.0.0.0:8080` automatically when it detects a container runtime (podman's `/run/.containerenv` or docker's `/.dockerenv`), so podman's `--publish 8080:8080` reaches it from the host. On a bare host (no container markers, no `FLY_APP_NAME`) it stays on the CherryPy default `127.0.0.1`. Fly continues to bind 0.0.0.0 via `FLY_APP_NAME`, and the X-Forwarded-Proto trust setting is still gated on `FLY_APP_NAME` alone — podman doesn't have a TLS-terminating proxy in front, so we don't want cherrypy.url() emitting `https://` URLs there. Logic lives in `l7r/app.py:_apply_server_config`.

**Key paths**:

- `.specify/memory/constitution.md` — the constitution
- `.specify/templates/plan-template.md` — Constitution Check gate lives here
- `/workspace/webapp-prototype/` — static frontend prototypes (current: relics index + detail)
- `/workspace/webapp/` — **L7R Toolkit** (CherryPy + Jinja2). Run with `cherryd --import l7r` from this dir. Routes: `/` landing, `/relics`, `/relics/<slug>`, `/names` (with `?gender=` / `?caste=` filters), `/chargen/*` (legacy chargen mounted as a sub-app). New code under `l7r/` package; legacy chargen modules on Principle X grace period.
- `/workspace/webapp/Makefile` — `make done` runs ruff + format check + mypy --strict + pytest + 100% coverage gate
- `/workspace/webapp/tests/screenshot.py` and `tests/dom_audit.py` — Playwright suite for Principle I verification at GM-100 / GM-200 / tablet / mobile. The screenshot script outputs multi-scroll contact sheets to `/tmp/l7r-shots/sheet-<page>-<viewport>.png`.
- `/workspace/.claude/agents/frontend-review.md` — independent design-review subagent. Invoke before declaring a UI change done if the same agent implemented AND reviewed.
- `/workspace/.claude/skills/relic/pool/` — exemplar of the pool data convention (Principle III)
- `/workspace/.claude/skills/name/pool-male.jsonl` + `pool-female.jsonl` — the 200-name pool consumed by the `/names` section

<!-- SPECKIT START -->
Current active plan: [`specs/001-toolkit-shell/plan.md`](specs/001-toolkit-shell/plan.md)
Active feature: L7R Toolkit Phase 1 — App Shell + Chargen + Relics
Feature directory: `specs/001-toolkit-shell/`
<!-- SPECKIT END -->
