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

- **UI changes** (per Principle I, expanded in v1.3.0):
  - Run `webapp/tests/screenshot.py` to produce **multi-scroll contact sheets** at GM-100 / GM-200 / tablet / mobile. For pages taller than 1.3× viewport, the script captures 0%/33%/66%/100% scroll positions and stitches them horizontally — so layout asymmetry, dead space, and below-fold problems are visible at a glance.
  - Run `webapp/tests/dom_audit.py`. It must report **zero issues** across all pages × viewports. The audit now covers BOTH clipping (overflow, ellipsis, line-clamp) AND layout balance (sibling-height ratio inside flex/grid containers must not exceed 2.5×).
  - **Persona-driven review pass**: before declaring done, examine at least one contact sheet at GM-200 with the user's task in mind (not the implementer's: "Eli is opening this page; what is he trying to do here?"). If the same agent both implemented and reviewed, **invoke the `frontend-review` subagent** (`.claude/agents/frontend-review.md`) to get an independent pass. Author ≠ reliable reviewer.
- **Python changes**: `ruff check` + `ruff format --check` + `mypy --strict` + `pytest` + `--cov-fail-under=100` on pure-logic packages (Principle X).
- **Delegated work**: spot-check actual artifacts before relaying success to the user. "The subagent said it was done" is not sufficient.

**Spec-kit hooks**: `.specify/extensions.yml` defines auto-commit hooks before each spec-kit step. Per the project's git-safety convention, do not auto-execute those — surface them and let the user confirm each time.

**Container memory persistence**: Claude Code's auto-memory loader reads from `/home/agent/.claude/projects/-workspace/memory/`, which is on the container's overlay-FS upper dir and gets wiped on rebuild. To survive rebuilds, the actual memory files live in this repo at `/workspace/.claude/memory/` (ext4-mounted, persistent), and `/workspace/.claude/bootstrap-container.sh` symlinks the loader path to that persistent dir. Run it once after starting a fresh container:

```
bash /workspace/.claude/bootstrap-container.sh
```

The script is idempotent. Without it, the loader sees an empty directory and prior memories aren't surfaced — so first thing in a fresh container, run it. (Existing containers where the symlink already resolves correctly need no action.)

**Running the webapp locally (fresh container)**: prod and dev deps are split into two lockfiles — `requirements.txt` (what the Fly image installs) and `requirements-dev.txt` (ruff/mypy/pytest/pytest-cov/playwright/pip-tools). Install both for `make done` to work. From `/workspace/webapp/`:

```
pip install --break-system-packages -r requirements.txt -r requirements-dev.txt
python3 -m playwright install chromium  # one-time browser download
cherryd --import l7r
```

Re-lock either file with `pip-compile --output-file=<file>.txt <file>.in` (sources are `requirements.in` and `requirements-dev.in`). The prod lockfile must resolve under Python 3.10 (Docker base); the dev lockfile under whichever Python the container runs.

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
- `/workspace/.claude/memory/` — persistent Claude Code memory store (see Container memory persistence above)
- `/workspace/.claude/bootstrap-container.sh` — run once per fresh container to link the memory dir into the loader path

<!-- SPECKIT START -->
Current active plan: [`specs/001-toolkit-shell/plan.md`](specs/001-toolkit-shell/plan.md)
Active feature: L7R Toolkit Phase 1 — App Shell + Chargen + Relics
Feature directory: `specs/001-toolkit-shell/`
<!-- SPECKIT END -->
