# Development workflow (full text)

*Project reference, moved out of [`../CLAUDE.md`](../CLAUDE.md) on 2026-10-17 so it is loaded on demand rather than in every session (and every subagent) context. CLAUDE.md keeps the one-line always-on version of each rule.*

**Load this file when:** starting or running a spec-kit feature, deciding whether to stop and ask, judging whether something is a regression or a defect you must fix, verifying work before calling it done, or you want the full form of an iteration-loop rule.

---

This project uses spec-driven development governed by [`.specify/memory/constitution.md`](../.specify/memory/constitution.md) (currently v1.12.1, 15 principles, 8 NON-NEGOTIABLE). The constitution is the higher-level authority; CLAUDE.md and this doc operationalize it.

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
  license to exceed ordinary authorized work, and persistence means continuing to make PROGRESS, not
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
  auto-loading directory CLAUDE.md (the diagram repository's skill CLAUDE.md is the exemplar); SKILL.md stays the
  usage-facing index. A rule that applies to only one domain belongs in that domain's CLAUDE.md,
  not in a forked constitution.
- **NO FEATURE BRANCHES - spec-kit work included** (GM 2026-07-27). Isolation already comes from the session clone; a branch on top of it is a second axis that buys nothing and broke the stop-work procedure for a whole session. Branch creation is off (`.specify/extensions.yml`, `before_specify`, `enabled: false`) and [`scripts/no-branch-hooks.sh`](../scripts/no-branch-hooks.sh) blocks a hand-rolled `git checkout -b` (escape hatch: `NO_BRANCH_OK` in the command, with a reason). Spec-kit still needs to know which feature is active: **`export SPECIFY_FEATURE=NNN-slug`**, which `common.sh`'s `get_current_branch()` returns ahead of asking git, so `check_feature_branch()` in `setup-plan.sh` / `setup-tasks.sh` is satisfied with no branch at all. **Export `SPECIFY_FEATURE_DIRECTORY` alongside it** - `export SPECIFY_FEATURE_DIRECTORY=specs/NNN-slug`. `SPECIFY_FEATURE` alone is NOT enough and the difference is silent: `common.sh` resolves `FEATURE_DIR` from `SPECIFY_FEATURE_DIRECTORY` (priority 1), then `.specify/feature.json` (priority 2), and only then from the branch name that `SPECIFY_FEATURE` supplies (priority 3) - so with a stale pointer present, `SPECIFY_FEATURE=115` yields `CURRENT_BRANCH=115` and `FEATURE_DIR=.../116`, and spec-kit writes into a PEER's feature directory while every log line looks right. Measured 2026-08-16 on features 115/116.
- **Concurrent sessions: spec numbers are CLAIMED UNDER A LOCK, not computed by hand** (GM
  2026-08-16; the tool ported from the diagram repository 2026-10-26). Run `python3
  scripts/claim-feature.py <kebab-slug>` from your clone: under `flock` it reads main's `specs/`,
  the fetched `origin/main`, every OTHER clone's unpushed `specs/` and its ledger, creates
  `specs/NNN-slug/` in your clone, and prints `export SPECIFY_FEATURE=...` /
  `export SPECIFY_FEATURE_DIRECTORY=...`. Then, the moment `/speckit-specify` writes `spec.md`,
  commit that directory and `scripts/sync-with-main.sh push` it - the review gate passes a push
  that is exactly one new spec directory with no verdict (the claim), and owes the verdict on the
  next push touching it. Do NOT coordinate numbering by messaging peer sessions. Full protocol in
  [`session-clones.md`](session-clones.md).
- **A regression is measured, not remembered.** It is anything that passed before your change and fails after it - a test, a gate check, a pool artifact, a cohort seed, a rate. Take the baseline on unmodified code in a **detached worktree** (`git worktree add --detach /tmp/base HEAD`), never by stashing - a stash mutates the tree under any review agent currently reading it. **And check each failure the worktree reports against your clone before calling it pre-existing**: a fresh worktree carries no GITIGNORED artifacts, so tests that read them fail there for reasons that have nothing to do with the code (measured 2026-08-24: 2 such failures, 20 pool PNGs in the worktree against the clone's 28). The reverse is the dangerous half - the same gap can make a test pass ONLY in the worktree, hiding a real regression from the moment the baseline is taken.
- **Pre-existing failures are NOT regressions.** They stay ledgered and are not fixed under someone else's feature. That distinction is exactly why the baseline is mandatory.
- **None of these excuses one**: it is small; it is "only" a cohort seed or a fixture; you documented it (a ledger entry tracks a regression, it does not permit one); the change fixes more than it breaks; or the residue "ROTATED" because a re-roll moved which seeds fail. On rotation specifically - where per-seed comparison survives, a check that passed on a seed and now fails is a regression; where the re-roll makes per-seed comparison meaningless, the pass RATE must not drop **and** every newly-failing check must be individually diagnosed.
- **Three exits only: fix it, revert it, or get an explicit GM waiver** for that specific regression. If you cannot fix it, STOP and say so - the work stays in the clone, **unpushed**. `sync-with-main.sh done` is not run on a regressed state; committing inside your own clone is still fine and correct (mid-task work is sacred).

**FIX DEFECTS WHERE YOU FIND THEM - bugs before new code** (constitution Principle XIV, NON-NEGOTIABLE, GM 2026-08-17: *"anytime we are working on the diagram skill and you in the course of implementing a feature come across some new defect - even if it is a defect that did not have anything to do with what you were working on - I would like you to fix it as part of that work ... in general, we should fix bugs before writing new code."*). A defect you find while doing something else is fixed IN that work, with the same verification anything else gets - not filed, not deferred to "its own pass". The **only** exception is a fix that would be a complete overhaul or a giant architectural change (a stage reordering, a new subsystem, a placement engine rewritten), and deferring one is a deliverable rather than a shrug: it carries the MEASUREMENT that establishes the defect, the mechanism, and an implementation sketch.

- **When the GM names a defect, write the check FIRST** (GM 2026-08-10: *"which all need to be fixed after we add new automated checks to catch these issues in the future"*): (1) the check, watched RED against the current artifact; (2) only then the fix; (3) the diagnosis in the failure message, so the next session is told what to do. A fix without a check comes undone at the next change. Two traps: a feature defined by its relation to geometry that moves must be DERIVED from that geometry, never pinned to a coordinate that was right once; and verify the check RUNS where you care about it (rules testing `scale == "city"` silently skipped the capital tier, 74 checks, until the GM found it by eye).
- **Do NOT reach for Principle XIII's "pre-existing failures stay ledgered."** That clause is about what BLOCKS a push. This one is about what you owe a defect you have actually seen. A pre-existing failure you never touched does not stop you shipping; one you found gets fixed.
- **Most of these arrive from the review subagents**, which are pointed at a DELTA and reliably find things outside it - that is an independent reviewer working, not scope creep. Same for a defect a diagnostic surfaces, a number that looks wrong while you were measuring something else, or a comment describing code that no longer exists.
- **The why is compounding** (the GM's own reasoning): the point of these generators is to expand them onto a foundation whose behavior is known-good. Every defect left in place is one the next tier inherits and builds over, entangled by then with work that assumed it. Keeping the floor level is what lets the building get taller.
- **Record a fix that FAILED, at the point of change.** A cheap wrong lever that measurably did nothing saves the next session from pulling it again - the exemplar is the front-row lane cap's two recorded dead ends in the diagram repository's `hamletgen/homesteads.py`.

**Verification before reporting "done"** (per Principle VI of the constitution):

- **UI changes** (per Principle I, expanded in v1.3.0):
  - Run `webapp/tests/screenshot.py` to produce **multi-scroll contact sheets** at GM-100 / GM-200 / tablet / mobile. For pages taller than 1.3× viewport, the script captures 0%/33%/66%/100% scroll positions and stitches them horizontally - so layout asymmetry, dead space, and below-fold problems are visible at a glance.
  - Run `webapp/tests/dom_audit.py`. It must report **zero issues** across all pages × viewports. The audit now covers BOTH clipping (overflow, ellipsis, line-clamp) AND layout balance (sibling-height ratio inside flex/grid containers must not exceed 2.5×).
  - **Persona-driven review pass**: before declaring done, examine at least one contact sheet at GM-200 with the user's task in mind (not the implementer's: "Eli is opening this page; what is he trying to do here?"). If the same agent both implemented and reviewed, **invoke the `frontend-review` subagent** (`.claude/agents/frontend-review.md`) to get an independent pass. Author ≠ reliable reviewer.
- **Python changes**: `ruff check` + `ruff format --check` + `mypy --strict` + `pytest` + `--cov-fail-under=100` on pure-logic packages (Principle X).
- **Files stay at human scale** (constitution Principle X clause 13, GM 2026-08-15; tests included per v1.6.1, GM 2026-08-16): a source OR TEST file past ~1,000 raw lines prompts the question "should this become a package of subfiles with its own CLAUDE.md index?" The cost being managed is context-window tokens - loading a huge file to use one part of it - and a test file is loaded under the same conditions as source (you load a test file to modify one test the way you load a source file to use one function), so tests get no exemption. Exemplar: the diagram repository's `check_village/` package. Ordered-data files (registries) may stay large with an inline justification - the only carve-out, and it protects only rows stating real DECISIONS (execution order, curation, hand-written metadata that exists nowhere else). **A roster that merely restates what code elsewhere already declares is DERIVED, not maintained or split** (clause 14, v1.7.0, GM 2026-08-16): census who actually consumes each name (most of a grown roster has zero consumers), move the roster's safety property into a guard test proven to fire, then derive the surface - star imports for re-export `__init__`s, introspection for derivable registry rows. Exemplar: feature 027 collapsed `check_village/__init__.py` from 3,148 lines to 63 with zero consumer changes; full method in the diagram repository's `specs/027-init-star-imports/`.
- **Delegated work**: spot-check actual artifacts before relaying success to the user. "The subagent said it was done" is not sufficient.

**Iteration-loop efficiency.** A transcript profile (2026-07-20, re-confirmed 2026-07-25) found **78% of wall time is model turn latency, not tool execution** - the number of sequential turns is the cost, not tool speed. The rules, shortest form; the incident evidence behind each is in [`docs/iteration-loop.md`](iteration-loop.md):

- **Batch into fewer, bigger turns.** Independent recon goes in ONE turn as parallel calls; a planned multi-edit goes in one turn. Serialize only past a real decision point. **ENFORCED** by [`scripts/batching-hooks.sh`](../scripts/batching-hooks.sh) - when **3 of the last 6 turns** each made a single quick read-only call it blocks the next RECON-SHAPED call (a rolling window since 2026-08-08: **147 of 162 round trips single-call, 22.7 min of latency for 4.0 min of work** under the old consecutive streak). Since 2026-08-10 substantive calls (heredocs, `&&`/`;` folds, pytest/make/git-commit) are never the blocked call, the bar re-arms higher after each firing and decays back as turns batch, and the block message itself carries the full playbook (fold the retry-patch into one asserted script, act-on-read in the same command, never pad with no-ops) - measured 2026-08-09: 49 of 52 blocks in a patch-grind session were landing on already-substantive or already-folded calls.
- **Edit files with `Edit`, not with heredoc'd Python that rewrites them.** This costs no extra round trips - several `Edit` calls batch into ONE turn exactly like one folded bash command does - and it removes a hazard the patch script carries by construction: Python-inside-a-heredoc that itself contains quoted Python has to be hand-escaped, and when it breaks it breaks as a `SyntaxError` in the PATCHER, so the anchor never even gets tested and a full model turn goes on rewriting the quoting. Measured 2026-08-16 (fan-toe pond fix): three failed patch scripts, ~4-5 min, ~10% of the task, every one a quoting slip rather than a wrong anchor. Keep heredocs for analysis, asserts, and glue that contains no quoted code - and when an edit genuinely must be scripted (a mechanical sweep over many files), assert the anchor matched.
- **Docs-only diffs skip the gate.** If everything changed since the last green gate is markdown, do not re-run `make done`.
- **Before the gate, run the WHOLE affected test file - never a `-k` subset.** A filter selects the tests you were thinking about; a change breaks the ones you were not. **ENFORCED** by [`scripts/gate-hooks.sh`](../scripts/gate-hooks.sh) - if the only local test run since your last `.py` edit used `-k`, it blocks `make done` once. (Escape: `GATE_OK` in the command, with a reason. Cost of getting this wrong, once: a 3.9-minute gate cycle lost to a test in the same file the filter did not select.)
- **The gate is `make done`, run from `webapp/` inside your clone.** It runs ruff, format-check,
  mypy --strict, the hook-guard suites, pytest and the 100% coverage gate, reports every failure
  together, and stamps the tree so `sync-with-main.sh` can prove a green gate saw the Python being
  pushed. ~15 s on this box. (The diagram repository's `make quick`/`make reference`/`make done`
  ladder and its make-only enforcement hooks moved with it in feature 131; this repository has no
  engine entry points to guard.)
- **Never re-run what the gate just ran, and never run pytest without `-n auto`.** Serial pytest is ~7x slower here; a green `make done` is already the proof. (Cost of getting this wrong, once: 13.2 minutes, 19% of a feature.)
- **`make done` reports ALL failures together.** Fix everything it lists, then re-run once. On a coverage failure it also prints the lines you changed that no test reaches.
- **Background the final gate - and NEVER poll it.** Act on the completion notification. **ENFORCED** by [`scripts/no-poll-hooks.sh`](../scripts/no-poll-hooks.sh), which blocks `pgrep -f`, sleep-loops, and the `command sleep` bypass. (A wait on genuinely EXTERNAL state passes by putting `POLL_OK` in the command with a note saying what it waits for.)
- **Read derived data from the recorded artifact, not by re-running the generator.** Regenerate when you need to change what a generator DRAWS; read its manifest/output when you need to know what it drew.
- **Iterate on ONE artifact; run the full test bed exactly once, at the end** - but that final sweep is MANDATORY whenever shared code changed. **This binds when BUILDING, not only when debugging** (GM 2026-08-23, constitution VI). A new capability has no artifact "exhibiting the defect", so the whole suite looks like the natural first check; it is not - prove the change on one page, one pool entry, one test file, then sweep. **Every step of a generator feature is TWO steps** - the reference artifact, then the whole pool - and both are tasks (constitution VI). A feature adding a KNOB owes one artifact per knob VALUE.
- **Before changing ORDERING or architecture, read every path involved in ONE batched pass and settle the sequence first.** The failure mode is discovering the ordering one gate failure at a time. Where you add ordering-critical code, leave a comment at the point of change - a rule in a document nobody re-reads does not hold.
- **Do NOT cut the process steps** (regression-fixture freeze, overlap-registry classification, record-the-why docs, the stop-work procedure). They cost ~2 minutes per feature and are why the regression rate stays near zero. Savings come from turn structure, never from skipping guardrails.

The diagram skill's own dev-loop doctrine moved with it to <https://github.com/EliAndrewC/diagram> (feature 131).

**Improving a review subagent** (`backstory-review`, `frontend-review`, `mention-context-review`): do NOT just apply the fix and write the rule in. The current artifacts contain the motivating defect - that is the failing test. Add the **general, category-level rule only**, run the agent against the unfixed artifact, and only once it FIRES do you fix the artifact and record the specific instance as a validated example. Full procedure, plus the harness gotcha that mid-session edits to `.claude/agents/*.md` do not reach agents launched by type, in [`docs/spec-kit-and-reviews.md`](spec-kit-and-reviews.md).

**Running tests by hand** (the gate is still `make done`): `pytest <dir> -n auto` for one package, `pytest <dir> -n auto --cov=<dir> --cov-report=term-missing` for its coverage. Keep the path scoped to your working dir - a repo-root run collects every clone.
