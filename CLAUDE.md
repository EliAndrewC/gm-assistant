# L5R Setting Generation Project

This project is a Legend of the Five Rings tabletop RPG worldbuilding environment. The GM uses Claude Code to generate setting details (NPCs, locations, items, etc.) guided by their extensive setting notes and evolving preferences.

**This file is the always-on core; detail lives in the topic docs indexed below.** It is loaded into every session and every general-purpose subagent, so keep it to rules needed in every session plus pointers (trimmed from 66KB on 2026-10-17; see [`docs/subagent-caching.md`](docs/subagent-caching.md) for the measured cost). A new rule gets ONE line here only if a session would go wrong without it before it knew to open a doc; its full text, incident and reasoning go in the topic doc.

## Core Rules

### Canonical Source

The GM's canonical notes file is `/host-l7r-repo/setting/l7r.md` - the GM's `EliAndrewC/l7r` repo, bind-mounted from the host. It is the master record of campaign and setting notes; the GM appends to it from their laptop, and you append to it via the note intake workflow below. If the mount is not present, the container was not launched per [`README.md`](README.md) - ask the GM rather than guessing.

**The L7R RULES live in the same repo at `/host-l7r-repo/rules/NN-*.md`** (character creation, skills, combat, schools, knacks, spells, advantages, disadvantages, professions, ...). A question about how a mechanic works is answered THERE, by grep, before anything is built on it - and a rule that reads wrong (a formula that cannot produce the range the GM describes) is flagged to the GM, not silently fixed in the rules file. Exemplar: `discern_honor()` in `webapp/l7r/repl/honor.py`.

**Never run `git commit` or `git push` against `/host-l7r-repo`** - the GM handles that repo's git from their laptop; read-only git there is fine. (This repository is different: the session pushes main itself - see Session clones.)

### Protecting the GM's Writing

Content between `<!-- SOURCE: GM NOTES - DO NOT MODIFY -->` and `<!-- END SOURCE -->` markers is the GM's original writing: NEVER modified, rephrased, summarized or "improved", unless the GM explicitly says so. The blocks are frozen point-in-time excerpts, not live mirrors of `l7r.md` - drift is expected. AI-generated content outside the markers may be updated as preferences evolve. Applies to every file in the project.

### File Organization

- **Skills** (`.claude/skills/<name>/SKILL.md`) *generate* content; Claude Code lists them with their descriptions and argument hints. `/diagram` **moved** to its own repository (<https://github.com/EliAndrewC/diagram>, feature 131) - map work happens in a session there.
- **Reference directories** hold source material, each indexed by its own `CLAUDE.md`: `/setting/` (demographics, castes, currency, ranks, government, geography, lineage, merchants, ashigaru, experience), `/campaigns/` (campaigns, timelines, PC/NPC backstories, Order of Lord Moon), `/hooks/` (adventure hooks by setting type, grifts), `/cosmology/` (Moon court, stories, maho, between places, gaijin religions, Fortune theology, soothsaying), `/notes/` (not yet organized). Skills draw on these for shared context.

### Generation Behavior (one line each; full text, incidents and mechanisms in [`docs/generation-rules.md`](docs/generation-rules.md))

- Draw on the GM's source notes for tone and setting; never invent details that contradict them.
- **A request to generate a character IS the authorization to upload it** (`/chargen`, `/synthesize`): no review menu, no "are you sure" - upload, report with the full prose, offer a re-roll. `backstory-review` still runs every time, and when the GM corrects generated prose, distil the general rule into `.claude/agents/backstory-review.md` (TDD procedure in [`docs/spec-kit-and-reviews.md`](docs/spec-kit-and-reviews.md)).
- **Every NPC you create gets an AI portrait, asked for or not** - including NPCs made outside `/chargen`. The mechanism has silent-failure traps (an existing character needs `op.set_character_avatar`): read the portrait bullet in the doc before doing it by hand.
- **Hyphens only** - no em-dashes or en-dashes anywhere in the project. **American spellings, never British**, everywhere including code identifiers. Both hook-enforced; the GM's own writing is exempt.
- **Principle XI**: any kanji in generated content passes the kanji <-> romaji <-> meaning triangle.
- **Record the "why" of every research-driven rule** where the rule lives, and **record a decision to accept a limitation with the alternatives declined** - in ENGINEERING docs only.
- **Setting content describes the world, never the conversation that produced it** - no "decisions", "Option A/B" or "we considered" in `l7r.md`, OP pages or character records.
- **Research before you ask for a ruling** (Principle XII); **two supportable answers become a knob, not a choice**.
- **"People" has caste meaning** (only samurai are people): use `humans` / `inhabitants` / `population` in analytical writing. **"Domain", never "demesne".** **Gender-neutral generic office-holders** (`they`); named characters keep their pronouns.

## Testing

pytest + pytest-cov; tests live beside the code as `test_<module>.py`; 100% line coverage for pure logic; external boundaries (HTTP, browser) are tested with saved fixtures, not transport mocks.

## Reference docs (load on demand)

| Doc | Load it when |
|---|---|
| [`docs/generation-rules.md`](docs/generation-rules.md) | Generating or editing setting content, making a portrait by hand, turning research into a generator rule, or deciding whether to ask the GM for a ruling. |
| [`docs/note-intake.md`](docs/note-intake.md) | The GM pastes raw campaign notes to be written into `l7r.md` and Obsidian Portal. |
| [`docs/l7r-style.md`](docs/l7r-style.md) | Editing `l7r.md`, or writing prose into an Obsidian Portal wiki page or character record. |
| [`docs/dev-workflow.md`](docs/dev-workflow.md) | Running a spec-kit feature, deciding whether to stop and ask, judging a regression or a found defect, verifying before "done", or you want the full form of a loop rule. |
| [`docs/session-clones.md`](docs/session-clones.md) | Setting up a clone, a clone/sync hook block, a push conflict, the spec-number claim protocol, or the `cd` rule's history. |
| [`docs/guards.md`](docs/guards.md) | A hook blocked you, or you are adding/changing a guard or deciding whether a rule should be enforced. |
| [`docs/iteration-loop.md`](docs/iteration-loop.md) | You want the measured evidence behind a loop rule, or you are about to argue with one. |
| [`docs/spec-kit-and-reviews.md`](docs/spec-kit-and-reviews.md) | Adding a rule to a review subagent, the same-session agent-definition gotcha, or wiring spec-kit hooks. |
| [`docs/subagent-caching.md`](docs/subagent-caching.md) | Writing an agent definition, launching several subagents with shared instructions or context, writing a `Workflow` script, or a `subagent-cache` block. |
| [`docs/container.md`](docs/container.md) | Launching or rebuilding the container, a "command not found" / "No module named" failure, adding a dependency, or bumping Python. |
| [`docs/key-paths.md`](docs/key-paths.md) | Finding where something lives: webapp routes, REPL, Discord bots, OP crawler, issue watch, screenshot suite, review agents, feature numbering. |

**Subagent token cost** (GM 2026-10-17, measured): shared instructions go in a `.claude/agents/*.md` definition (its body is the only part reused across launches), every definition sets `omitClaudeMd: true`, and putting shared text first in a launch prompt does NOT make it cache. Prefer a typed agent to `general-purpose` for anything launched repeatedly.

## Note Intake Workflow

When the GM pastes raw campaign notes (table events, lore, NPC beats, world-building), **load [`docs/note-intake.md`](docs/note-intake.md) and follow it.** In short: copy-edit to presentable prose in the GM's laconic voice (ask if a fragment is too cryptic), and write to **`l7r.md` always** plus **Obsidian Portal** - a named character's record (GM-only notes or the public Wish Lists and Goals section) or a wiki page; splitting the notes across several destinations is expected and fine. Routing is your call: propose a destination when unsure ("I think this goes to X, confirm?"), never "where does this go?"; ask before creating a new wiki page. Report exactly where each piece was written.

## L7R House Style

**Load [`docs/l7r-style.md`](docs/l7r-style.md) before any edit to `l7r.md` or any prose written into Obsidian Portal.** Never bulk-regenerate `l7r.md`'s TOC (the GM curates it; insert only new entries and `git diff` to prove nothing else moved). If `Edit` fails with "file modified since read", re-grep the anchor - never trust line numbers across edits.

## Development Workflow

Governed by [`.specify/memory/constitution.md`](.specify/memory/constitution.md); this file operationalizes it. One constitution for the whole repo, deliberately: a rule for only one domain goes in that domain's directory `CLAUDE.md`, never a forked constitution. Full text of every rule below, with its incident: [`docs/dev-workflow.md`](docs/dev-workflow.md).

- **Spec-kit for feature work** (new webapp sections, skills, generators) - specify -> plan -> tasks -> implement, **run end to end unattended**, answering each stage's own questions and recording the decisions. Tweaks and one-bug fixes are done directly; ask before chain-firing on an ambiguous case.
- **No feature branches** (`scripts/no-branch-hooks.sh`). Export BOTH `SPECIFY_FEATURE=NNN-slug` and `SPECIFY_FEATURE_DIRECTORY=specs/NNN-slug` - the first alone silently writes into a peer's feature directory.
- **Concurrent sessions: spec numbers are claimed in main**: after sync-in, highest `specs/NNN` + 1; commit and `sync-with-main.sh push` the moment `spec.md` exists. This repository's features restart at 200 (the diagram repository holds 005-131+).
- **Stop and ask ONLY when a wrong guess would be expensive to unwind**; cheap choices are made, reported and offered for adjustment.
- **THE GM STARTS WORK AND LEAVES** (XV, NON-NEGOTIABLE): when a path forward exists, take it; when stuck, the next step is a measurement, not another speculative edit.
- **DO THE LITERAL THING** (XVI, NON-NEGOTIABLE): asked for X, build X, never "X except Y"; a needed exception goes to an independent subagent with the GM's request verbatim. **A spec is reviewed against the GM's own words by `spec-fidelity`** before implementation, up to three rounds, then escalate.
- **NO KNOWN REGRESSIONS** (XIII, NON-NEGOTIABLE): measure a baseline in a detached worktree (never a stash; check gitignored-artifact differences); nothing regressed is pushed; exits are fix (expected), revert (with a written impossibility investigation) or an explicit GM waiver.
- **FIX DEFECTS WHERE YOU FIND THEM** (XIV, NON-NEGOTIABLE), pre-existing or not, in the work at hand; only a giant architectural change may be deferred, with the measurement and a sketch. Record a fix that FAILED at the point of change.
- **Verification before "done"**: UI changes get `webapp/tests/screenshot.py` contact sheets, `tests/dom_audit.py` at zero issues, and the `frontend-review` agent; Python gets the gate; delegated work is spot-checked. A source or test file past ~1,000 lines prompts a split question; a roster that restates other code is derived, not maintained.
- **Improving a review subagent is TDD**: add the general rule, watch it FIRE on the unfixed artifact, then fix and record the instance ([`docs/spec-kit-and-reviews.md`](docs/spec-kit-and-reviews.md)).

**Iteration loop** (78% of wall time is model turn latency; evidence in [`docs/iteration-loop.md`](docs/iteration-loop.md)):

- **Batch into fewer, bigger turns** - independent reads in parallel, act-on-read in the same command (`scripts/batching-hooks.sh`). Edit with `Edit`, not heredoc'd Python rewrites.
- **The gate is `make done`, run from `webapp/` inside your clone** (~15 s; ruff, format, mypy --strict, hook suites, pytest, 100% coverage). It reports ALL failures; fix them together, re-run once. Docs-only diffs skip it. Before the gate, run the WHOLE affected test file - never a `-k` subset (`scripts/gate-hooks.sh`). Never re-run what it just ran; never run pytest without `-n auto`.
- **Background the final gate and never poll it** (`scripts/no-poll-hooks.sh`); act on the notification.
- **Iterate on ONE artifact; sweep the full test bed once, at the end** - also when building. Read derived data from recorded artifacts rather than re-running generators. Settle ordering by reading every involved path in one pass first. Never cut the process steps.

**Session clones (REQUIRED for every session that modifies this repo)** - full spec and every failure mode in [`docs/session-clones.md`](docs/session-clones.md):

- Work in `.clones/<session-name-kebab-cased>` (resolve the name from the transcript's last `custom-title` record; `gm-assistant` is forbidden - ask the GM to `/rename`). Create with `git clone /gm-assistant .clones/<name>` and set `user.name`/`user.email` in it.
- **Sync in at the start of every new piece of work**; **stop-work procedure every time you stop**: commit in the clone, then `scripts/sync-with-main.sh done` (locked pull + push to main and GitHub; exit 4 = landed in main, not GitHub). Never `git push --force`. Commit on `main` in the clone, never a branch.
- **Main is the integration point, never a workspace** - nothing runs in main's tree but read-only commands.
- **Name the tree in the command**: `git -C <abs-path>` for every git call, `( cd <abs> && ... )` when a cwd is needed, one tree per command. A bare `cd` leaks into later commands and has made sessions report the wrong tree.
- Keep `pytest`/`ripgrep` scoped to the working dir (they would double-collect every clone).
- Clone `CLAUDE.md` files are excluded from loading (`claudeMdExcludes` in `.claude/settings.json`), so every session reads MAIN's copy once instead of both - an edit to CLAUDE.md in your clone takes effect for sessions only after it is pushed.

**Guards** - fifteen hooks and checks, each with a test companion run by the gate; the table, what is deliberately not enforced, and the four properties every new guard needs are in [`docs/guards.md`](docs/guards.md). A guideline that can be counted gets asserted at the STANDARD, not where the code sits.

**Review subagents are pre-authorized** (`backstory-review`, `frontend-review`, `spec-fidelity`, `mention-context-review`) via `container-scripts/append-system-prompt.md`, because the default system prompt otherwise outranks this file; if one gets skipped, check `type claude` first. Run `mention-context-review` one category at a time, never in parallel (the GM's terminal has crashed on fan-out). Broad fan-out, `Workflow` and deep research still need an explicit request.

**Container**: install what you need (passwordless sudo); `container-scripts/setup-dev-env.sh --check` the moment something fails with "command not found" / "No module named" ([`docs/container.md`](docs/container.md)).

**Key paths**: the constitution is `.specify/memory/constitution.md`; the L7R Toolkit webapp is `webapp/` (CherryPy + Jinja2, new code under the `l7r/` namespace portion, each subsystem indexed by its own `CLAUDE.md`); everything else is in [`docs/key-paths.md`](docs/key-paths.md). For current feature status, read the highest-numbered `specs/` directory's `tasks.md` and `git log` - there is deliberately no "active plan" pointer here.
