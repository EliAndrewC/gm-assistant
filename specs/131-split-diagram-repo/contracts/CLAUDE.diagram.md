# L7R Diagram - the settlement and building map generator

<!-- container-mounts: ../gm-assistant:/gm-assistant -->
<!-- container-workdir: /diagram -->

This repository is the `/diagram` skill of the GM's L5R worldbuilding project, split out of
[`EliAndrewC/gm-assistant`](https://github.com/EliAndrewC/gm-assistant) on 2026-08-25 (feature 131)
because it had *"grown into a project into its own right"* with rules the rest of that repository
should not carry: **every change here is a spec-kit feature; everything runs through `make`; the
merge gate runs on AWS CodeBuild (feature 130, once implemented).** The skill still lives at
[`.claude/skills/diagram/`](.claude/skills/diagram/) - the SAME path as before the split, on
purpose, so nothing in the engine, the pool generators or the feature-127 guards moved.

**Read next**: [`.claude/skills/diagram/SKILL.md`](.claude/skills/diagram/SKILL.md) (usage) and
[`.claude/skills/diagram/CLAUDE.md`](.claude/skills/diagram/CLAUDE.md) (the dev loop - auto-loads
when you edit under it). The GM's setting notes that the research cites live in gm-assistant
(`setting/`, `cosmology/`, `campaigns/`) - mounted read-only at `/gm-assistant` in this container,
and on GitHub at <https://github.com/EliAndrewC/gm-assistant/tree/main/setting>. The canonical
campaign notes remain `/host-l7r-repo/setting/l7r.md` in the GM's `l7r` repo; this repository never
edits them.

**A feature is identified by REPOSITORY + number from 2026-08-25.** This repository continues from
132; gm-assistant restarts at 200. Features 001-131 that concern the diagram live here with their
numbers; the five that do not (001-004, 011) stayed in gm-assistant.

## Core Rules

### Protecting the GM's Writing

Content between `<!-- SOURCE: GM NOTES - DO NOT MODIFY -->` and `<!-- END SOURCE -->` markers is the GM's original writing. These sections must NEVER be modified, rephrased, summarized, reworded, or "improved" in any way. Only the GM may edit these sections, and only when they explicitly instruct you to do so.

These blocks are **frozen historical excerpts**: they capture what the GM wrote at the time the downstream file was created and are not kept in sync with subsequent edits to `/host-l7r-repo/setting/l7r.md`. Drift between a downstream `SOURCE` block and the current canonical is expected and intentional - the block is a point-in-time snapshot, not a live mirror. The canonical for any topic is always `l7r.md`.

AI-generated content (preferences, generation instructions, examples of liked/disliked output) lives outside these markers and can be updated as the GM's preferences evolve.

This convention applies to ALL files in the project - both skill files and reference directory files.

### Skills (invocable as /slash-commands)

Each skill lives in `/.claude/skills/<skill-name>/SKILL.md` with YAML frontmatter. Skills are for *generating* specific types of content.

#### Reference Directories (not invocable, indexed by CLAUDE.md)

Reference directories hold organized source material and context. Each directory has its own `CLAUDE.md` that indexes and explains its contents. Skills should reference these directories when they need shared context.

- `/setting/` - Demographics, castes, currency, samurai ranks, government structure (Six Ministries), geography, lineage system, merchant families, ashigaru, experience levels
- `/campaigns/` - Campaign-specific material: Karmic Inquisitors, First Toshi Ranbo, Hidden Way, Wasp Bounty Hunters, timelines, PC/NPC backstories, the Order of Lord Moon
- `/hooks/` - Adventure hooks organized by type (countryside, town, city, caravan, prison camp), grifts and scams
- `/cosmology/` - Lord Moon's heavenly court, mythological stories/fables, maho & bloodspeakers, "between places", gaijin religions (Uru, Burning Sands), Fortune theology, soothsaying
- `/notes/` - Miscellaneous source material not yet organized into a dedicated reference directory

### Generation Behavior

- Preference feedback from the GM is captured in memory and incorporated into skill files over time.
- Never invent setting details that contradict the GM's source notes.
- **Hyphens only - no em-dashes (U+2014) or en-dashes (U+2013) anywhere in the project**, including generated content, webapp templates, skill files, specs, docs, and tests. This applies project-wide, not just to `l7r.md`.
- **American spellings, never British ones.** Always use: `color`, `center`/`centered`, `gray`, `honor`, `judgment`, `catalog`, `labeled`/`labeling`, `behavior`, `neighbor`/`neighborhood`, `analyze`/`organize`/`recognize` (the `-ize` forms), `artifact`, `defense`, `license`, `practice` (both noun and verb), `skeptic`, `story` (of a building), `while`, `traveled`, `modeled`, `program`, `meter`, `liter`, `mold`, `plow`, `curb`, `draft`, `aging`, `marvelous`, `jewelry`, `skillful`. Never their British counterparts (the `-our`, `-re`, `-ise`, `-ce`-noun, doubled-`l`, and `-ogue` forms). This applies project-wide and to **everything**: generated content, prose, docs, specs, skill files, webapp templates, tests, comments and docstrings, **and code identifiers** (variable names, parameters, dict keys, CSS class names). The one exception is the GM's own writing - never "correct" text inside `<!-- SOURCE: GM NOTES -->` blocks or in `l7r.md`, and leave direct quotations of it alone.
- **Constitution Principle XI** (Japanese Authenticity): any kanji that surfaces in generated content - relic names, sword names, given names, temple titles, vow refrains, decorative stamps - must pass the kanji ↔ romaji ↔ meaning triangle. Real characters, plausible reading, English meaning that maps back. Stylized readings are allowed when explained in surrounding prose.
- **Record the "why" of every research-driven rule (REQUIRED).** When historical (or setting) research leads us to a concrete generation rule, automated check, or magic number - "every farmhouse had a work yard," "~30% of farms had a storehouse," "threshing was per-household, not communal" - we MUST capture the *reasoning* alongside the *rule*, not just the rule. Encoding the finding into a check or generator is necessary but **not sufficient**: a bare `count >= 0.3 * n` teaches a future reader nothing about why 0.3. So write the finding down where the rule lives - a "Historical grounding"/research section in the skill's `SKILL.md`, or a comment next to the check - covering what the research found, the decision it drove, and any deliberate departures from literal reality (e.g. features drawn larger than true scale for legibility while keeping *relative* sizes roughly honest). Explicit source citations are optional (usually overkill); the *why* is mandatory. This protects against having to redo the research when memory fades or the context window rolls over. Applies to any generator (skills, the webapp, future tools), not just `/diagram`.
- **Record a decision to ACCEPT a limitation, and the alternatives that were declined (REQUIRED)** (GM 2026-08-17: *"we should always document this kind of decision... that way if we look it up later, we'll know it was a deliberate decision"*). The rule above covers a decision that produced a rule; this covers the other kind - where we looked at something imperfect and deliberately chose to leave it. Undocumented, those are indistinguishable from bugs, and the next session "fixes" them. So write down **what was accepted, what it costs in observable terms, which alternatives were priced, and who chose** - the rejected options matter as much as the chosen one, because they are what stops the question being reopened from scratch. Worked example: [`.claude/skills/diagram/settlements/water.md`](.claude/skills/diagram/settlements/water.md) "THE TAPER IS SUB-PERCEPTUAL AT TRUE SCALE" - the GM asked why a channel did not visibly narrow, the honest answer was that at true scale it cannot, two legibility multipliers were priced against keeping true size, and the ruling plus both declined numbers are recorded where the next reader will meet the map.
- **RESEARCH BEFORE YOU ASK FOR A RULING (REQUIRED)** (GM 2026-08-18, constitution Principle XII). A question about how a place was actually built, farmed or lived in is a RESEARCH question. Run the search pass FIRST; the GM is asked only when the record turns out silent or contradictory, and the ask must say what was searched, what was found, and why it does not settle the matter. This binds the review loop hardest, because that is where these surface: a reviewer writing *"this wants a one-line ruling"* has identified a QUESTION, not delegated it. Two questions queued for the GM on 2026-08-17 - whether a byre may stand beside a wellhead, and whether a hamlet's back rank needs a way - were both answered by one research pass the next morning.
- **TWO SUPPORTABLE ANSWERS BECOME A KNOB, NOT A CHOICE (REQUIRED)** (GM 2026-08-18, constitution Principle XII). Where the research shows a thing was genuinely done more than one way, do NOT pick the reading you prefer: make it a **tunable knob with per-settlement variance**, rolled from the map's own seed like every other knob. The reason is a project goal rather than a historical one - these maps exist for players who must tell one settlement from another at a glance, so *"we want settlements which are within historical norms while being as different from one another as is justifiable by our historical research"*. Every place the record permits two forms is a place two maps can honestly differ, and picking one throws that away permanently. The ladder: research it; if decisive, implement what it says; if it supports two forms, add the knob; only if it is silent does the GM rule. (The older "calibrated liberty" clause still covers a DEGREE along a continuum - how large, how dense, how often - never a choice between distinct FORMS.)
- **"People" has caste meaning.** In the Celestial Order only samurai are "people"; heimen are "half-people", hinin "non-people". In demographic, statistical, or analytical writing use `humans` / `inhabitants` / `population` / a specific caste term - never "4 out of every 5 people work the land". `people` is fine for samurai specifically, and in narrative, lore, dialogue, vow and folktale voice. Full rule in [`docs/l7r-style.md`](docs/l7r-style.md) (copied from gm-assistant; the canonical copy is there).
- **"Domain", never "demesne"**, for territory administered at any tier, including compounds ("Imperial domain"). Silently fix `demesne` -> `domain` in any text you edit.
- **Gender-neutral office-holders.** Use `they`/`their`/`them` for a GENERIC daimyo, governor, magistrate, minister, or samurai; specific named characters keep their own pronouns.


## Development Workflow

This project uses spec-driven development governed by [`.specify/memory/constitution.md`](.specify/memory/constitution.md) (currently v1.12.1, 15 principles, 8 NON-NEGOTIABLE). The constitution is the higher-level authority; this CLAUDE.md operationalizes it.

**When to use spec-kit:**

- **Feature work** (new sections of the webapp, new skills, new generators, the upcoming Python backend) → invoke `/speckit-specify` and follow through plan → tasks → implement. The Constitution Check section in `.specify/templates/plan-template.md` is the gate that enforces the constitution at plan-time; skipping spec-kit on feature work means skipping that gate.
- **Tweaks and iteration** (CSS adjustments, wording fixes, regenerating one item, fixing one bug) → just do the work directly. The constitution still applies, but the formal spec/plan/tasks flow is overkill.
- **Ambiguous cases** → ask before chain-firing `/speckit-specify`.
- **Run the chain end-to-end, unattended** (GM 2026-08-15). Spec-kit here is externalized working
  memory - the same discipline that keeps a handoff to a human from dropping work: break it down,
  write it down, mark things off only when verified. It is NOT stage-gate ceremony, and the
  constitution is maintained pragmatically rather than artisanally. When implementing a spec-kit
  feature, run specify -> plan -> tasks -> implement straight through without pausing for GM
  approval between stages, answer each stage's own questions yourself, and record every resolved
  decision in the artifact where it arose.
- **Stop-and-ask calculus** (GM 2026-08-15, narrowed 2026-08-23): interrupt the run ONLY when a
  wrong guess would be expensive to unwind - an hour-plus of implementation that might be thrown
  away buys a question first. When a choice is cheap to adjust after the fact, make the call, finish
  the task, report what was chosen, and offer the adjustment. Asking beats redoing; redoing beats
  blocking on trivia. **This covers AMBIGUITY about what is wanted, and nothing else.** Difficulty
  in delivering something already known to be wanted is governed by constitution **Principle XV
  (Keep Going)**, and there the answer is to keep working.
- **THE GM STARTS WORK AND LEAVES** (GM 2026-08-23, constitution XV, NON-NEGOTIABLE). Stopping to
  ask "which of these should I do?" does not cost seconds of their attention - it costs the whole
  span until they return, and they come back to find the work where they left it. When a path
  forward exists, TAKE it; if one avenue is blocked, work the parts that are not. The only reason to
  stop is a genuine belief the thing cannot be done at all. If the options list contains "fix it and
  make it work", that is the answer and it does not need confirming. Two limits: this is never a
  licence to exceed ordinary authorized work, and persistence means continuing to make PROGRESS, not
  continuing to make CHANGES - when stuck, the next step is a MEASUREMENT, not another speculative
  edit.
- **DO THE LITERAL THING; AN EXCEPTION IS NOT YOURS TO APPROVE** (GM 2026-08-24,
  constitution Principle XVI, NON-NEGOTIABLE). Asked for X, build X - never "X except
  where Y". This is the exact tension the project's own answer to spec-kit creates:
  sessions are told to answer their own questions rather than stop constantly, and the
  failure mode of that instruction is a session quietly resolving a question the GM
  had already answered. **The resolution is that exceptions are presumed wrong.** If
  one still looks necessary, an independent Opus 5 subagent decides - given the GM's
  request VERBATIM - and the honest question to put to it is "am I carving out a case
  contrary to what I was told?". If it agrees, carry on and raise it with the GM once
  the implementation WORKS; the GM starts long work and comes back to a finished
  thing, so a mid-flight question costs them the whole span.
- **A SPEC IS REVIEWED AGAINST THE GM'S OWN WORDS, BY SOMEONE ELSE** (same principle).
  Before implementation, hand the finished `spec.md` and the GM's request AS WRITTEN to
  an independent subagent: does this specify what was asked, and does it add anything
  that was not? Not the plan - a spec graded against its own plan is being checked for
  self-consistency, which a wrong spec passes. Adjust and re-review up to **three**
  times; if the third round still returns changes, STOP and escalate, because three
  failures means a persistent misunderstanding a fourth attempt will not find. The
  motivating case is feature 126's FR-003, which said "farmhouses before lanes EXCEPT
  the connector and the field spur" when the GM had said "farmhouses before lanes".
- **One constitution for the whole repo, deliberately** (GM 2026-08-15): spec-kit's Constitution
  Check reads a single file, and the domain separation the project needs already exists in layers -
  the constitution carries universal principles; each domain's operational doctrine lives in its
  auto-loading directory CLAUDE.md (the diagram skill's is the exemplar); SKILL.md stays the
  usage-facing index. A rule that applies to only one domain belongs in that domain's CLAUDE.md,
  not in a forked constitution.
- **NO FEATURE BRANCHES - spec-kit work included** (GM 2026-07-27). Isolation already comes from the session clone; a branch on top of it is a second axis that buys nothing and broke the stop-work ritual for a whole session. Branch creation is off (`.specify/extensions.yml`, `before_specify`, `enabled: false`) and [`scripts/no-branch-hooks.sh`](scripts/no-branch-hooks.sh) blocks a hand-rolled `git checkout -b` (escape hatch: `NO_BRANCH_OK` in the command, with a reason). Spec-kit still needs to know which feature is active: **`export SPECIFY_FEATURE=NNN-slug`**, which `common.sh`'s `get_current_branch()` returns ahead of asking git, so `check_feature_branch()` in `setup-plan.sh` / `setup-tasks.sh` is satisfied with no branch at all. **Export `SPECIFY_FEATURE_DIRECTORY` alongside it** - `export SPECIFY_FEATURE_DIRECTORY=specs/NNN-slug`. `SPECIFY_FEATURE` alone is NOT enough and the difference is silent: `common.sh` resolves `FEATURE_DIR` from `SPECIFY_FEATURE_DIRECTORY` (priority 1), then `.specify/feature.json` (priority 2), and only then from the branch name that `SPECIFY_FEATURE` supplies (priority 3) - so with a stale pointer present, `SPECIFY_FEATURE=115` yields `CURRENT_BRANCH=115` and `FEATURE_DIR=.../116`, and spec-kit writes into a PEER's feature directory while every log line looks right. Measured 2026-08-16 on features 115/116.
- **Concurrent sessions: spec numbers are CLAIMED IN MAIN, not negotiated** (GM 2026-08-16). The
  GM runs several sessions at once, and each allocates its own `specs/NNN` - so allocate from
  main's state and publish the claim immediately: after `sync-in`, next number = highest `NNN`
  under `specs/` + 1; the moment `/speckit-specify` writes `spec.md`, commit the new
  `specs/NNN-slug/` in the clone and run `scripts/sync-with-main.sh push` (a mid-feature
  milestone push). The locked pull+push makes the claim atomic - if the pull surfaces another
  session's same-numbered spec, renumber yours before pushing. Do NOT coordinate numbering by
  messaging peer sessions: a busy session replies late or never, while main serializes with zero
  cooperation. Full protocol (and what peer messaging IS for) in
  [`docs/session-clones.md`](docs/session-clones.md).

**FIXING IT IS THE EXIT.** Principle XIII's three ways out are not a menu (GM 2026-08-23): FIX is
the expected outcome, REVERT requires a WRITTEN impossibility investigation rather than a
preference, and a waiver is the GM's to grant after a fix has genuinely been attempted. A session
that has found a path forward takes it.

**NO KNOWN REGRESSIONS - and nothing merges to main carrying one** (constitution Principle XIII, NON-NEGOTIABLE, GM 2026-08-17: *"never count our work as being done when there are known regressions. Nothing should EVER be merged back into main if even one single new regression was added."*). Two separate bars, and work routinely clears the first and fails the second:

- **A regression is measured, not remembered.** It is anything that passed before your change and fails after it - a test, a gate check, a pool artifact, a cohort seed, a rate. Take the baseline on unmodified code in a **detached worktree** (`git worktree add --detach /tmp/base HEAD`), never by stashing - a stash mutates the tree under any review agent currently reading it. **And check each failure the worktree reports against your clone before calling it pre-existing**: a fresh worktree carries no GITIGNORED artifacts, so tests that read them fail there for reasons that have nothing to do with the code (measured 2026-08-24: 2 such failures, 20 pool PNGs in the worktree against the clone's 28). The reverse is the dangerous half - the same gap can make a test pass ONLY in the worktree, hiding a real regression from the moment the baseline is taken.
- **Pre-existing failures are NOT regressions.** They stay ledgered and are not fixed under someone else's feature. That distinction is exactly why the baseline is mandatory.
- **None of these excuses one**: it is small; it is "only" a cohort seed or a fixture; you documented it (a ledger entry tracks a regression, it does not permit one); the change fixes more than it breaks; or the residue "ROTATED" because a re-roll moved which seeds fail. On rotation specifically - where per-seed comparison survives, a check that passed on a seed and now fails is a regression; where the re-roll makes per-seed comparison meaningless, the pass RATE must not drop **and** every newly-failing check must be individually diagnosed.
- **Three exits only: fix it, revert it, or get an explicit GM waiver** for that specific regression. If you cannot fix it, STOP and say so - the work stays in the clone, **unpushed**. `sync-with-main.sh done` is not run on a regressed state; committing inside your own clone is still fine and correct (mid-task work is sacred).

**FIX DEFECTS WHERE YOU FIND THEM - bugs before new code** (constitution Principle XIV, NON-NEGOTIABLE, GM 2026-08-17: *"anytime we are working on the diagram skill and you in the course of implementing a feature come across some new defect - even if it is a defect that did not have anything to do with what you were working on - I would like you to fix it as part of that work ... in general, we should fix bugs before writing new code."*). A defect you find while doing something else is fixed IN that work, with the same verification anything else gets - not filed, not deferred to "its own pass". The **only** exception is a fix that would be a complete overhaul or a giant architectural change (a stage reordering, a new subsystem, a placement engine rewritten), and deferring one is a deliverable rather than a shrug: it carries the MEASUREMENT that establishes the defect, the mechanism, and an implementation sketch.

- **Do NOT reach for Principle XIII's "pre-existing failures stay ledgered."** That clause is about what BLOCKS a push. This one is about what you owe a defect you have actually seen. A pre-existing failure you never touched does not stop you shipping; one you found gets fixed.
- **Most of these arrive from the review subagents**, which are pointed at a DELTA and reliably find things outside it - that is an independent reviewer working, not scope creep. Same for a defect a diagnostic surfaces, a number that looks wrong while you were measuring something else, or a comment describing code that no longer exists.
- **The why is compounding** (the GM's own reasoning): the point of these generators is to expand them onto a foundation whose behavior is known-good. Every defect left in place is one the next tier inherits and builds over, entangled by then with work that assumed it. Keeping the floor level is what lets the building get taller.
- **Record a fix that FAILED, at the point of change.** A cheap wrong lever that measurably did nothing saves the next session from pulling it again - see the front-row lane cap's two recorded dead ends in [`hamletgen/homesteads.py`](.claude/skills/diagram/l7r/diagram/hamletgen/homesteads.py).

**Verification before reporting "done"** (per Principle VI of the constitution):

- **UI changes** (per Principle I, expanded in v1.3.0):
  - Run `webapp/tests/screenshot.py` to produce **multi-scroll contact sheets** at GM-100 / GM-200 / tablet / mobile. For pages taller than 1.3× viewport, the script captures 0%/33%/66%/100% scroll positions and stitches them horizontally - so layout asymmetry, dead space, and below-fold problems are visible at a glance.
  - Run `webapp/tests/dom_audit.py`. It must report **zero issues** across all pages × viewports. The audit now covers BOTH clipping (overflow, ellipsis, line-clamp) AND layout balance (sibling-height ratio inside flex/grid containers must not exceed 2.5×).
  - **Persona-driven review pass**: before declaring done, examine at least one contact sheet at GM-200 with the user's task in mind (not the implementer's: "Eli is opening this page; what is he trying to do here?"). If the same agent both implemented and reviewed, **invoke the `frontend-review` subagent** (`.claude/agents/frontend-review.md`) to get an independent pass. Author ≠ reliable reviewer.
- **Python changes**: `ruff check` + `ruff format --check` + `mypy --strict` + `pytest` + `--cov-fail-under=100` on pure-logic packages (Principle X).
- **Files stay at human scale** (constitution Principle X clause 13, GM 2026-08-15; tests included per v1.6.1, GM 2026-08-16): a source OR TEST file past ~1,000 raw lines prompts the question "should this become a package of subfiles with its own CLAUDE.md index?" The cost being managed is context-window tokens - loading a huge file to use one part of it - and a test file is loaded under the same conditions as source (you load a test file to modify one test the way you load a source file to use one function), so tests get no exemption. Exemplar: `.claude/skills/diagram/l7r/diagram/check_village/`. Ordered-data files (registries) may stay large with an inline justification - the only carve-out, and it protects only rows stating real DECISIONS (execution order, curation, hand-written metadata that exists nowhere else). **A roster that merely restates what code elsewhere already declares is DERIVED, not maintained or split** (clause 14, v1.7.0, GM 2026-08-16): census who actually consumes each name (most of a grown roster has zero consumers), move the roster's safety property into a guard test proven to fire, then derive the surface - star imports for re-export `__init__`s, introspection for derivable registry rows. Exemplar: feature 027 collapsed `check_village/__init__.py` from 3,148 lines to 63 with zero consumer changes; full method in `specs/027-init-star-imports/`.
- **Delegated work**: spot-check actual artifacts before relaying success to the user. "The subagent said it was done" is not sufficient.

**Iteration-loop efficiency.** A transcript profile (2026-07-20, re-confirmed 2026-07-25) found **78% of wall time is model turn latency, not tool execution** - the number of sequential turns is the cost, not tool speed. The rules, shortest form; the incident evidence behind each is in [`docs/iteration-loop.md`](docs/iteration-loop.md):

- **Batch into fewer, bigger turns.** Independent recon goes in ONE turn as parallel calls; a planned multi-edit goes in one turn. Serialize only past a real decision point. **ENFORCED** by [`scripts/batching-hooks.sh`](scripts/batching-hooks.sh) - when **3 of the last 6 turns** each made a single quick read-only call it blocks the next RECON-SHAPED call (a rolling window since 2026-08-08: **147 of 162 round trips single-call, 22.7 min of latency for 4.0 min of work** under the old consecutive streak). Since 2026-08-10 substantive calls (heredocs, `&&`/`;` folds, pytest/make/git-commit) are never the blocked call, the bar re-arms higher after each firing and decays back as turns batch, and the block message itself carries the full playbook (fold the retry-patch into one asserted script, act-on-read in the same command, never pad with no-ops) - measured 2026-08-09: 49 of 52 blocks in a patch-grind session were landing on already-substantive or already-folded calls.
- **Edit files with `Edit`, not with heredoc'd Python that rewrites them.** This costs no extra round trips - several `Edit` calls batch into ONE turn exactly like one folded bash command does - and it removes a hazard the patch script carries by construction: Python-inside-a-heredoc that itself contains quoted Python has to be hand-escaped, and when it breaks it breaks as a `SyntaxError` in the PATCHER, so the anchor never even gets tested and a full model turn goes on rewriting the quoting. Measured 2026-08-16 (fan-toe pond fix): three failed patch scripts, ~4-5 min, ~10% of the task, every one a quoting slip rather than a wrong anchor. Keep heredocs for analysis, asserts, and glue that contains no quoted code - and when an edit genuinely must be scripted (a mechanical sweep over many files), assert the anchor matched.
- **Docs-only diffs skip the gate.** If everything changed since the last green gate is markdown, do not re-run `make done`.
- **Before the gate, run the WHOLE affected test file - never a `-k` subset.** A filter selects the tests you were thinking about; a change breaks the ones you were not. **ENFORCED** by [`scripts/gate-hooks.sh`](scripts/gate-hooks.sh) - if the only local test run since your last `.py` edit used `-k`, it blocks `make done` once. (Escape: `GATE_OK` in the command, with a reason. Cost of getting this wrong, once: a 3.9-minute gate cycle lost to a test in the same file the filter did not select.)
- **Foreground-regenerate ONLY the motivating map - never a pre-gate pool sweep.** The gate verifies the pool itself, and render-sync regenerates main's renders from main's own tip, so a clone-side `pipeline/regen.py pool/*/*.gen.py` before `make done` is pure waste (38s measured 2026-08-16; evidence in [`docs/iteration-loop.md`](docs/iteration-loop.md)).
- **EVERYTHING RUNS THROUGH `make`, and it is enforced rather than requested** (feature 127). A bare
  interpreter reaching an engine entry point, a bare pytest, a make driven by a foreign makefile, or
  an inline override supplied to skip a prompt is refused BEFORE it runs by
  `scripts/make-only-hooks.sh`; the engine refuses in-process calls too. In the diagram skill the
  ladder is `make quick` (~33 s), `make reference` (~26 s), `make done` (~5.5 min, NOT the quick one),
  `make done FULL=1` (prompts, cancels by default, logs a reason). Every refusal names the target that
  does the job, because a guard that blocks a legitimate question without giving the route is a guard
  that gets worked around.
- **Never re-run what the gate just ran, and never run pytest without `-n auto`.** Serial pytest is ~7x slower here; a green `make done` is already the proof. (Cost of getting this wrong, once: 13.2 minutes, 19% of a feature.)
- **`make done` reports ALL failures together.** Fix everything it lists, then re-run once. On a coverage failure it also prints the lines you changed that no test reaches.
- **Background the final gate - and NEVER poll it.** Act on the completion notification. **ENFORCED** by [`scripts/no-poll-hooks.sh`](scripts/no-poll-hooks.sh), which blocks `pgrep -f`, sleep-loops, and the `command sleep` bypass. (A wait on genuinely EXTERNAL state passes by putting `POLL_OK` in the command with a note saying what it waits for.)
- **Read derived data from the recorded artifact, not by re-running the generator.** Regenerate when you need to change what a generator DRAWS; read its manifest/output when you need to know what it drew.
- **Iterate on ONE artifact; run the full test bed exactly once, at the end** - but that final sweep is MANDATORY whenever shared code changed. **This binds when BUILDING, not only when debugging** (GM 2026-08-23, constitution VI). The old wording said "the ONE motivating artifact", which a feature can read as not applying to it - a new capability has no artifact "exhibiting the defect", so the cohort looks like the natural first check. It is not: on feature 126 a 48-map cohort was launched mid-experiment, one seed near-hung, and 30 minutes returned no result, twice. Use **`make maps`**, which picks its own scope: after a failed run it does the reference hamlet alone (~1 min) and stops at the first problem; after a clean run it does the whole tier and reports every failure together. There is no second command on purpose - the earlier two-command version relied on the session choosing right, and it did not. **Every step of a generator feature is TWO steps** - reference settlement, then pool - and both are tasks (constitution VI). The bare commands are the cheap ones on purpose; `make done` re-checks the whole pool anyway, so forgetting the sweep costs time, never correctness. A feature adding a KNOB owes one map per knob VALUE - three, not forty-eight.
- **Before changing ORDERING or architecture, read every path involved in ONE batched pass and settle the sequence first.** The failure mode is discovering the ordering one gate failure at a time. Where you add ordering-critical code, leave a comment at the point of change - a rule in a document nobody re-reads does not hold.
- **Do NOT cut the ritual steps** (regression-fixture freeze, overlap-registry classification, record-the-why docs, the stop-work ritual). They cost ~2 minutes per feature and are why the regression rate stays near zero. Savings come from turn structure, never from skipping guardrails.

Package-specific timings and skill-specific lessons live in that skill's dev-loop doc, e.g. [`.claude/skills/diagram/CLAUDE.md`](.claude/skills/diagram/CLAUDE.md) - an index over [`.claude/skills/diagram/dev/`](.claude/skills/diagram/dev/), where the DRAW ORDER map and the KEEP-CLEAR CONTRACT live ([`dev/placement.md`](.claude/skills/diagram/dev/placement.md)).

**Improving a review subagent** (`building-review`, `backstory-review`, `frontend-review`): do NOT just apply the fix and write the rule in. The current artifacts contain the motivating defect - that is the failing test. Add the **general, category-level rule only**, run the agent against the unfixed artifact, and only once it FIRES do you fix the artifact and record the specific instance as a validated example. Full procedure, plus the harness gotcha that mid-session edits to `.claude/agents/*.md` do not reach agents launched by type, in [`docs/spec-kit-and-reviews.md`](docs/spec-kit-and-reviews.md).

**Session clones (REQUIRED for every session that modifies this repo).** Any session about to change a file here works in an isolated clone under `.clones/` - never in main's tree. The normal path:

- **Clone name = this session's name, kebab-cased.** Resolve it - do not guess: your `session_id` is in your scratchpad path; grep `~/.claude/sessions/*.json` for that id and read its `.name`. `diagram` (this repository's own name) and `gm-assistant` are FORBIDDEN clone names; an unnamed or auto-derived session has no valid workspace, so ask the GM to `/rename` it before doing repo work.
- **Create it with** `git clone /diagram .clones/<session-name>`, then set `user.name`/`user.email` inside it (repo-local config does not copy). Reuse an existing clone for a resumed session.
- **Sync in at the start of EVERY new piece of work** - `git pull origin main` inside the clone - not just at the final push.
- **Stop-work ritual, EVERY time you stop** (task done, milestone, or pausing for GM input): commit in the clone, then run [`scripts/sync-with-main.sh`](scripts/sync-with-main.sh) `done` from inside it (locked pull+push, then render-sync). **Never `git push --force`** - it is the one thing that overwrites other sessions' work.
- **Main is the integration point, never a workspace.** The ONLY thing a session runs in main's tree is render-sync. No generators, no tests, no writes. Read-only commands are fine.
- **Git ownership:** the session does all commits/merges/push-back-to-main; the GM's only git job is the GitHub push/pull from main. Never commit or push against `/host-l7r-repo`.
- **Commit on `main` inside the clone** - never on a branch. `sync-with-main.sh` pushes `HEAD:main`, so what you committed is what lands.
- Hooks enforce all of this ([`scripts/clone-sync-hooks.sh`](scripts/clone-sync-hooks.sh)): the forbidden name, name-routing to another session's clone, a live-session claim, and a clean-but-stale HEAD. A dirty tree is never blocked - mid-task work is sacred. **If a hook blocks you, the full spec and every failure mode is in [`docs/session-clones.md`](docs/session-clones.md).**
- **Gotcha:** keep `pytest`/`ripgrep` scoped to the working dir - they do not read `.gitignore`, so a repo-root run double-collects every clone.
- **NAME THE TREE IN THE COMMAND; never carry a `cd` into it** (measured 2026-08-17). A bare `cd` persists for the REST of that command AND into the next Bash call, so a block opening `cd /gm-assistant && ...` silently answers about MAIN for everything after it - including the half you labeled CLONE. That cost one session two wrong readings of its own state in a single sitting, the second one immediately after writing up the first. Measured behavior: `( cd X && ... )` in a subshell leaks nothing, either way; a bare `cd X` leaks both ways. So:
  - **`git -C <abs-path> ...` for every git call.** No `cd` at all, and - the part that actually matters - the tree is named IN THE COMMAND TEXT, so a mislabeled section header cannot survive a re-read of what you ran.
  - **`( cd <abs> && ... )`** when something genuinely needs a cwd (`make`, `pytest`, `python3 -m`).
  - **One tree per command.** If you want main and a clone side by side, that is two `git -C` calls, not one `cd` and a header.
  Note what this is and is not for: actually WRITING in main is already caught three ways (`webapp/mainguard.py`, the Makefile's `guard`, `settlement._assert_not_main_tree`). This rule prevents the quieter failure those guards cannot see - a read-only diagnostic that confidently reports the wrong tree, which is worse than an error because it looks like an answer.
  **A hook was priced and DECLINED (GM 2026-08-17: "I can't think of a better enforcement mechanism either").** A `PreToolUse` hook is this project's usual answer to a recurring mistake, and it does not fit this one. A hook precise enough to catch the motivating case would have to demand `git -C` on EVERY git call - it fired on a command with one legitimate `cd` and no second path, so nothing structural marked it as wrong - and a hook that fires on nearly every correct command trains sessions to pattern-match past it, which degrades the guards that matter. The narrow alternative (fire only when ONE command contains both a `cd` to a non-clone path AND `.clones/`) is near-zero noise but would have caught neither instance, since neither named two trees. So this rule is deliberately unenforced and rests on habit; the cost is that it will be broken again. **Reopen only with a mechanism that would catch a single-`cd` command whose section header names the other tree** - that is the shape to beat, and neither candidate above does.

**WHAT IS ENFORCED, AND WHERE** (audit 2026-08-24). Twelve guards, each with a test companion that
`make hooks-test` runs as a gate phase - a guard without one turns the gate red (constitution XVIII).

| rule | mechanism |
|---|---|
| never `git push --force` | [`scripts/repo-safety-hooks.sh`](scripts/repo-safety-hooks.sh) - no escape; "never" stops meaning never the moment one exists |
| no git writes to `/host-l7r-repo` | same script; EDITS there stay legal, the intake workflow needs them |
| the GM's SOURCE blocks are not editable (V) | [`scripts/source-block-hooks.sh`](scripts/source-block-hooks.sh) - checks containment against the file on disk |
| hyphens only; American spellings | [`scripts/house-style-hooks.sh`](scripts/house-style-hooks.sh) - exempts the GM's writing and the files that must quote the rule |
| a README is the GM's to write (XVII) | [`scripts/readme-hooks.sh`](scripts/readme-hooks.sh) |
| everything runs through `make` | [`scripts/make-only-hooks.sh`](scripts/make-only-hooks.sh) + `l7r/diagram/_invocation.py` |
| guard files are not edited casually | [`scripts/guard-file-hooks.sh`](scripts/guard-file-hooks.sh) |
| a spec is reviewed before implementation (XVI); a Mode B map before it ships | [`scripts/review-gate.sh`](scripts/review-gate.sh), run by `sync-with-main.sh` at PUSH time |
| both perf bookends exist; a seed >5% slower must be DIAGNOSED and a total >10% BLOCKS as a regression (VI) | `make perf-gate`, a phase of `make done FULL=1`; the two bands are in `tools/perf_snapshot.py` with `tests/tools/test_perf_snapshot.py` proving each fires |
| no `-k` subset before the gate; no branches; no polling; batching | the pre-existing `gate`/`no-branch`/`no-poll`/`batching` hooks |

**Deliberately NOT enforced**, because a guard that fires on correct work teaches a session to bypass
every guard: the caste sense of "people" (correct in narrative and vow voice), gender-neutral
office-holders (named characters keep their pronouns), Principle XI's kanji triangle, and the
behavioral principles XII/XIV/XV. File size past ~1,000 lines is REPORTED by `make audit`, never
gated - the rule prompts a question rather than forbidding a size.

**When you add a guard**, three properties, each learned by getting it wrong: match INVOCATIONS not
mentions (seven false positives in one feature - a grep, a commit message, a docstring, a fixture
argument, a redirect, a test harness, and a hook that blocked its own repair); check the ESCAPE FIRST
or the guard cannot be repaired through the channel it guards; and prove it FIRES by deleting it and
watching a test go red.

**Review subagents are pre-authorized (GM 2026-07-27).** Claude Code's default system prompt tells a session not to call the Agent tool unless the user asked - a sensible default that nonetheless sits ABOVE this file in the instruction hierarchy, so it silently outranked the mandate to run `settlement-review` before shipping a Mode B map, and three city maps went out unreviewed with nothing warning. The fix is [`container-scripts/append-system-prompt.md`](container-scripts/append-system-prompt.md), loaded via `--append-system-prompt` by the `claude()` wrapper that `setup-dev-env.sh` installs into `~/.bashrc`: it lands AFTER that line with the same authority and grants standing authorization for the four review agents only. **If a review agent ever gets skipped again, check `type claude` first** - the wrapper is per-container and dies with a rebuild. Broad fan-out, `Workflow`, and deep research still need an explicit request.

**Container.** Launch with [`scripts/launch-container.sh`](scripts/launch-container.sh) from the repo root. On every fresh container run `container-scripts/setup-dev-env.sh` once (`--check` re-verifies in ~3s - run it the moment something that used to work fails with "command not found" / "No module named" / "resvg not found"). **INSTALL WHAT YOU NEED** - passwordless sudo exists precisely so a session can `apt-get install` or pip-install without asking; never reject a design *because* a dependency is not currently installed. Ports/mounts, the Python 3.14 pin, the two lockfiles and the server-binding logic are in [`docs/container.md`](docs/container.md).

**Key paths**:

- `.specify/memory/constitution.md` - the constitution (copied from gm-assistant at the split; the two diverge from here)
- `.specify/templates/plan-template.md` - Constitution Check gate lives here
- `.claude/skills/diagram/SKILL.md` - usage; `.claude/skills/diagram/CLAUDE.md` - the dev loop (auto-loads under that tree)
- `.claude/skills/diagram/migration-plan.md` - **standing project plan** for converting `/diagram` from hand-authored maps to scripted generation. **Read it before drawing or scripting a settlement map, and update its status table when a conversion lands.**
- `.claude/agents/settlement-review.md`, `building-review.md`, `size-audit.md` - the independent reviews of Mode B maps and Mode A plans (mandatory before a map ships); `.claude/agents/spec-fidelity.md` - the spec review (constitution XVI)
- `/gm-assistant/` (read-only mount) - the setting notes the research cites (`setting/`, `cosmology/`), the webapp, the content skills. Nothing here writes there.

Spec-kit features (the `specify` -> `plan` -> `tasks` -> `implement` flow) live under `specs/NNN-*/`. There is deliberately **no single "active plan" tracked here** - a hardcoded pointer just goes stale as features come and go. For current status, look at the highest-numbered `specs/` dir, its `tasks.md` checkboxes, and `git log`.

**Since the split (feature 131, 2026-08-25)**: this repository's main is `/diagram`; session
clones are `/diagram/.clones/<name>`; the ritual, the hooks, the guards and `gate-stamp` derive
that root from git rather than hardcoding it. The webapp is not here - `webapp/make done` and the
Playwright suite belong to gm-assistant. The Note Intake Workflow, the content skills
(`/chargen`, `/synthesize`, `/name`, ...) and Obsidian Portal are gm-assistant's; a session here
does none of that.
