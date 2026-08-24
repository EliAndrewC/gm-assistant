# Feature Specification: The Merge Gate Runs on AWS CodeBuild, and Only When It Must

**Feature Branch**: none - this project does not use feature branches (`SPECIFY_FEATURE=128-codebuild-merge-gate`)

**Created**: 2026-08-24

**Status**: APPROVED by `spec-fidelity` (round 3, verdict FAITHFUL); **AMENDED the same day on the
GM's second request** (the full sweep goes to CodeBuild too; the sync flow is tooling, not memory) -
amendment APPROVED at its own round 3 (FAITHFUL); **AMENDED AGAIN on the GM's third request**
(FULL during iteration; local checks first with the build pre-warmed in parallel; the FULL prompt
no longer stands in for the reference check) - third-request amendment APPROVED at round 1 (FAITHFUL), see Review history. **This feature is SPECIFIED AND PLANNED ONLY.**
The GM's instruction is explicit: *"you can write the SpecKit feature, you cannot actually automate
it yet"*. Implementation waits for a separate go.

**Input**: The GM's request is recorded verbatim in [`gm-request.md`](gm-request.md). **That file is
the authority for this specification.** It was written before this spec and must not be edited.

## Why this exists

The GM's laptop is the bottleneck: *"my laptop is not really up to snuff when it comes to having
the amount of CPU that I would want."* The sessions themselves are pleasant to run locally; the
thing worth moving is *"the expensive ones, like the ones that take five minutes or longer."*

The GM has priced the options and chosen AWS CodeBuild - pay per build-minute, nothing idle, queued
builds start when a slot frees, *"kinda like what Jenkins does"*. The infrastructure exists as of
2026-08-24: two CodeBuild projects (`gm-assistant-merge` at concurrency 1, `gm-assistant-check` at
concurrency 3, both `xlarge` = 36 vCPU / 68 GB at $0.08 per build-minute, 60-minute timeout), a
scoped IAM user, a GitHub token in Secrets Manager, a ruleset on `main` that blocks force pushes and
deletions, and a full set of budgets and live alarms. What does NOT exist is any way for a session to
use it, and that is what this feature specifies.

**The feature has two halves that pull in opposite directions, and both are the GM's.** The first is
speed: offload the five-minute check. The second, which the GM calls *"one of the most important
things about this feature"*, is that **every remote run costs money**, so the conditions under which
one starts must be far stricter than the conditions under which `make done` runs today. Most of this
spec is the second half.

## Re-audited baseline (GM: *"whatever you had evaluated at the start of this conversation will need to be reaudited"*)

Every number this feature was first discussed against was gathered before feature 127 landed, and
several are now wrong. The current record, from feature 127's stopwatch (`.claude/skills/diagram/CLAUDE.md`)
and this session's own CodeBuild smoke tests:

| what | at the start of the conversation | now (2026-08-24, post-127) |
|---|---|---|
| the local gate | "`make done` ~5 min" | **`make done` ~5.5 min** on the laptop, REFERENCE scope: Inashiro seed 4, lint/types, `hooks-test`, and every test that does not roll another map. **This is the run this feature offloads.** |
| the cheap check | "`make quick` ~4 min" | **`make quick` ~33 s**, with a 60 s self-enforced budget; `make reference` ~26 s; `make test-file FILE=...` for one whole file. **These stay local, always.** |
| "the 25-minute run" | assumed to be the normal gate | it is `make cohort` (48 seeds) - gated, reference-first, and NOT part of any `make done`. **Out of scope** (see Scope Boundaries). |
| the full pre-push sweep | did not exist as a separate thing | **`make done FULL=1`** ~6 min on the laptop: adds every live pool map, the seeds 41-44 ratchet, both coverage floors, and `perf-gate`. It PROMPTS with a cancel-by-default question and REFUSES to run without a terminal. **In scope on the GM's second request**: the prompt stays local; the dispatch happens after the operator declines the escape hatch; the build accepts the non-interactive run only because the tree it tests carries the logged reason (FR-024..FR-027). |
| what the push already checks | flock'd pull+push, render-sync | that, plus **`gate-stamp`** (a green `make done` must have run against byte-identical Python), **`review-gate`** (a spec carries a FAITHFUL verdict; a re-rolled map has its notes touched), duplicate-def screening. All local, all cheap, all kept. |
| performance | not tracked | **bookended per feature** (`make perf LABEL=NNN-start` / `-end`, `perf-report`), enforced by `perf-gate` inside `FULL=1` only. Snapshots are **only comparable on the same machine**; with `FULL=1` on CodeBuild, the bookends move there too - a consistent machine class, which the laptop never was (FR-028, FR-029). The laptop-era snapshots stay as history and are never compared against build-machine ones. |
| CodeBuild startup | "30-60 s" estimated | **20 s wall, 7 s provisioning**, measured on the stock image. With a custom image from ECR: unmeasured, expected 20-40 s. **There are no separate "resources" to create**: on-demand CodeBuild provisions when a build STARTS, and bills from then. The only way to pre-warm is to start the build and park it (FR-035). |
| does `FULL=1` check the reference map first? | assumed yes ("no way to short circuit that") | **NO - a defect this feature fixes.** the `done:` target runs `bypass-audit` INSTEAD of `reference` when `FULL` is set (its first recipe line), so a FULL run goes prompt -> lint -> types -> hooks-test -> the whole suite with no reference-first stop. The prompt's own text lists "the reference map is under surgery" as a reason to continue, so it was built as the reference BYPASS rather than as a gate ahead of it. Reference scope does stop on a red map. FR-034 separates the two. |
| `make done` remotely | "25 min becomes 6-9 min" estimated | **UNMEASURED.** The local 5.5 min is dominated by `pytest -n auto` over 22 laptop threads that throttle; on 36 unthrottled cores it should fall, but the serial floor (one reference hamlet ~26 s, provisioning ~20 s, source transfer) does not. **Measuring it is a task of this feature, and the number goes in `timings.md`, never in prose.** |
| cost per run | "~$0.60" for a 25-min job | at $0.08/min, a 5.5-minute run is **~$0.45**; if it lands at 3 minutes, **~$0.25**. Cost controls: $10/day and $75/month budgets emailing at every 20%; $100/month hard stop that denies further builds; a live alarm at 125 build-minutes per rolling day; a live email at every 20% of the monthly budget. |

## Decisions the request settles, and the two it delegated

The GM settled most of the design in conversation before asking for the spec. They are restated here
so the fidelity reviewer can check each against `gm-request.md`, and so the plan does not reopen them.

1. **CodeBuild, on demand, no reserved capacity.** *"I definitely do not want to just have these
   things sitting around idle."* Startup latency is accepted in exchange.
2. **No webhook. Sessions dispatch explicitly.** *"we will not have automatic hooks at the GitHub
   level. Instead, these Claude code sessions will have their own process by which AWS code build is
   invoked."* Pushing a branch never starts a build.
3. **The merge gate is sequential, and the thing tested is the merge result against the latest
   main.** *"only the first ones check would be valid ... AWS code build itself is what pulls in the
   main branch ... it is always getting the latest thing."* Concurrency 1 on the merge project is
   the mechanism; git's refusal of a non-fast-forward push is the guarantee.
4. **Main cannot have its history rewritten by the build's credential.** *"it can do whatever it
   wants to to our branches including rebasing and the like, but our main branch should be
   protected."* Done: a ruleset on `main` blocks force pushes and deletions, and the token has no
   permission to edit the ruleset.
5. **Direct push, not pull requests** - the GM delegated this to "whatever everyone else is doing"
   and the session answered: direct fast-forward push with a protected branch is the Bors /
   merge-train shape. No reviewer would ever look at the PR, so it would be ceremony.
6. **Only the lengthy runs go remote; the short ones stay local.** *"we do not want to run the
   quicker version of the tests on AWS. We only want to run the lengthy tests."*
7. **Nothing runs on AWS for a change outside the diagram skill, or for a docs-only change inside
   it.** *"Our AWS code build integration exists entirely for the sake of our diagram skill."*
8. **The remote run is the `make done` that precedes a push to main** - *"at least in the initial
   phase only doing this for actual make done actions that are merging stuff back into main"* - in
   whichever SCOPE the operator invoked it: reference scope by default, or the full sweep.
9. **The full sweep goes to CodeBuild too, with its prompt kept and run locally** (second request):
   *"this is exactly the kind of thing that we want to run there ... that part can be run locally,
   and then the actual dispatch to AWS infrastructure can happen after the operator has decided not
   to take the escape hatch."*
10. **Syncing GitHub main into the mirror and into every clone is the tooling's job** (second
    request): *"This should definitely happen at the tooling level, not at the 'remember to do it'
    level."*
11. **The full sweep is ALSO an iteration tool** (third request): *"there is a use case for running
    full test suites when we iterate ... okay, I have now made a change that I want to test on a
    wider variety of stuff."* The second-request reading "FULL is merge-only" is withdrawn.
12. **Inexpensive local checks ALWAYS run before anything touches AWS, and the build is warmed in
    parallel with the reference check** (third request): *"we always want to do inexpensive local
    checks first before we even do anything with AWS ... run really cheap tests, like linting ...
    while the AWS code build resources are being created, we run our local reference tests ... if
    the local reference tests fail, we immediately shut down ... if the local reference tests
    succeed, then we submit."* The general pattern for every remote target.

**The delegated decision - where main lives - and how it is resolved.** The GM thought aloud: *"the
local clones push to remote GitHub branches rather than... pushing back to Maine locally. I don't
know."* and then *"I don't really care. I just want to do whatever everyone else is doing."* This
spec resolves it as: **GitHub `main` becomes the integration point; `/gm-assistant` on the laptop
becomes a mirror of it.** A session clone stays exactly what it is today - an isolated workspace on
local `main`, no branches checked out - and pushes its HEAD to a GitHub *mailbox* branch
(`session/<clone-name>`) purely so the build has a commit to fetch. The build merges GitHub `main`
into that, runs the gate, and fast-forward-pushes the result to GitHub `main`; the mirror pulls, and
render-sync runs in the mirror exactly as it does in main today. The GM's laptop-side "push main to
GitHub" job disappears, because GitHub main IS main.

*The alternative, priced and declined* (recorded per the project's rule on accepted limitations):
keep local `/gm-assistant` as the integration point and ship only a verification record back from
the build. Declined because GitHub `main` lags local main whenever the GM has not pushed, so the
build would merge a STALE main and the GM's *"always getting the latest thing"* would be false by
construction; fixing that means shipping local main's tip to the build alongside the work, which is
the two-integration-points bookkeeping the GM called an *"impedance mismatch"*. The chosen design has
one main, and it is the one every other CodeBuild user has.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A finished diagram feature merges through CodeBuild, and nothing else does (Priority: P1)

A session has finished a feature that changed diagram engine code, has committed in its clone, and
runs the merge action - the stop-work ritual's push, which is the `make done` *"that pushes back to
main"*. The merge action decides whether a remote run is warranted; if it is, the run happens on
CodeBuild against the merge of this work with the latest main, and on green the result lands on
main. If it is not warranted, it says exactly which condition failed and nothing is spent. A
`make done` that is NOT merging anything - run for its verdict, as today - stays on the laptop, free,
unchanged.

**Why this priority**: This is the feature - the five-minute run leaves the laptop - and the
conditions around it are what the GM called the most important part.

**Independent Test**: With the conditions satisfied, the merge action dispatches exactly one build
and the merge lands. With each condition violated in turn, it refuses, names the condition, and no
build is started (verifiable in the CodeBuild build list, which must show none).

**Acceptance Scenarios**:

1. **Given** a clone whose own commits (not commits merged in from main) touch diagram engine code,
   a feature whose task list is complete, and a green local check since the last edit, **When**
   the merge action runs, **Then** one build starts on the merge project, it merges the latest main,
   runs the reference-scope gate, and on green fast-forward-pushes the merge result to main.
2. **Given** a clone whose own commits touch ONLY files outside the diagram skill (the constitution,
   `docs/`, the webapp, a spec), **When** the merge action runs, **Then** it reports that no diagram
   code is in the delta, starts no build, and pushes by the direct route.
3. **Given** a clone whose own commits touch diagram files that are documentation only (`*.md`,
   `dev/*-log/`, `future-work/`, `settlements/`, `research/`, a `.notes.md`), **When** the merge
   action runs, **Then** it reports the delta is docs-only, starts no build, and pushes directly.
4. **Given** a clone that merged main's diagram-code changes into itself but made none of its own,
   **When** the merge action runs, **Then** it starts no build - the merged-in work is main's,
   already verified there.
5. **Given** an active spec-kit feature whose `tasks.md` still has open tasks, **When** the merge
   action runs, **Then** it refuses, names the open tasks, and starts no build.
5a. **Given** any tree at all, **When** a plain `make done` runs in the skill directory, **Then** it
   runs locally exactly as it does today, costs nothing, and makes no network call.
6. **Given** the build's merge of main into the work conflicts, **When** the build runs, **Then** it
   fails within its first minute, reports the conflict, and the session is told to merge main
   locally, resolve, commit, and run again.
7. **Given** two sessions dispatch at once, **When** both builds are submitted, **Then** the second
   queues behind the first and, when it runs, merges the main that the first one just advanced.
8. **Given** a build that went green but main advanced between its fetch and its push, **When** it
   pushes, **Then** the push is refused as non-fast-forward, the build reports "main moved, re-run",
   and nothing lands.

---

### User Story 2 - A gate that just failed is not re-dispatched without a green local check (Priority: P1)

A remote gate fails. The session edits a file and immediately tries to dispatch again. The second
attempt refuses before dispatching: the last thing that ran was a failed gate and no local check has
passed since. The session runs `make quick` (or `make test-file`, `make reference`, or a local
`make done`), it passes, and the dispatch now goes ahead.

**Why this priority**: The GM identified this as a workflow to *"actually prevent"*, and every
instance of it is a wasted paid build.

**Independent Test**: Fail a remote gate, edit, dispatch: refused, no build. Run `make quick` green,
dispatch: a build starts.

**Acceptance Scenarios**:

1. **Given** the most recent recorded verification is a FAILED gate (remote or local), **When** a
   dispatch is attempted, **Then** it refuses immediately, without dispatching, and names the local
   target to run.
2. **Given** the most recent recorded verification is a GREEN local target (`quick`, `test-file`,
   `reference`, or a local `make done`) run after the last source edit, **When** a dispatch is
   attempted, **Then** it may proceed.
3. **Given** a source edit after the last green local target, **When** a dispatch is attempted,
   **Then** it refuses - the green run vouched for different code. (See Assumptions for why this
   case is read the way it is.)

---

### User Story 3 - A tree already verified remotely is never verified twice (Priority: P2)

A session mid-feature wants the lengthy suite run against its current work. It runs the iteration
form of the remote check: the build pulls the latest main into the work first, bails on a conflict,
and on green records that this exact resulting tree passed. Later the session runs `make done`; the
tree that would land on main is the same tree, so the merge happens with no second build.

**Why this priority**: *"This saves both time and money"*, and it removes a waste the GM sees today
even with one session: local tests, then a `make done` that redoes them.

**Independent Test**: Run the iteration check green on a tree; run `make done` on the same tree:
no build, merge lands. Change one source line; `make done`: a build runs.

**Acceptance Scenarios**:

1. **Given** the iteration check is requested, **When** it runs, **Then** the build first merges the
   latest main into the work, fails immediately on a conflict, and otherwise runs the gate and, on
   green, records the merge result as verified.
2. **Given** a verified record for exactly the tree the merge action would push, **When** the merge
   action runs, **Then** it skips the build, says which build verified the tree, and proceeds to
   merge.
3. **Given** main has advanced since the iteration check so the merge result differs, **When** the
   merge action runs, **Then** the record does not match and a build runs.
4. **Given** a session with no AWS access to the verified-record store's write path, **When** it
   tries to write a record by hand, **Then** it cannot: only the build writes records.
5. **Given** the same conditions as User Story 1 (our diagram code, feature complete, green local
   check), **When** the iteration check is requested, **Then** the same dispatch conditions apply
   EXCEPT feature completeness, which mid-feature work cannot satisfy by definition.

---

### User Story 4 - Every remote run is auditable, and its cost is visible before and after (Priority: P2)

Before dispatching, the merge action states what it is about to spend and why; afterwards, the run
is in the same audit trail as local runs, with its wall time, its build minutes, and its dollar cost,
and `make audit` shows month-to-date spend from those records.

**Why this priority**: The GM asked for *"a lot of cost monitoring"*; a paid run that leaves no
local record cannot be monitored by the project's own audit, only by the AWS console.

**Independent Test**: After one remote run, `make audit` lists it with where it ran, its minutes and
its cost, and a month-to-date total.

**Acceptance Scenarios**:

1. **Given** a dispatch is about to happen, **When** the conditions pass, **Then** the command prints
   the estimated minutes and dollars, the month-to-date spend, and the reason each condition passed.
2. **Given** a remote run finished (any outcome), **When** the session's command returns, **Then** a
   run-log entry exists locally marked as remote, with build id, minutes billed, cost, and outcome.
3. **Given** the monthly hard-stop has tripped, **When** a dispatch is attempted, **Then** it
   reports the circuit breaker plainly and names where to re-enable it, rather than a bare permission
   error.

---

### User Story 5 - The local ladder is untouched (Priority: P3)

Every local target works exactly as today: `make done` is the free local reference-scope gate it is
now, and the cheap targets below it change in no way. Nothing local prompts, dispatches, or makes a
network call.

**Why this priority**: A regression guard for feature 127, and the GM's *"the short versions to
continue to be run locally."*

**Acceptance Scenarios**:

1. **Given** `make done`, `make quick`, `make reference`, `make test-file`, `make maps`, and every
   read-only diagnostic, **When** run, **Then** no remote anything happens and nothing about them
   changed.
2. **Given** a remote run genuinely cannot happen (no network, an outage, the breaker tripped),
   **When** the merge action is attempted on a gated-route delta, **Then** it refuses and the work
   stays in the clone. There is no local override of the gated route: the GM's integrity argument -
   *"only the first ones check would be valid"* - is about the merge, and a local run cannot supply
   it.

---

### User Story 6 - The full sweep runs on CodeBuild, after the operator declines the escape hatch locally (Priority: P1)

At the end of a feature the session runs the merge action with `FULL=1`. The prompt appears in the
terminal exactly as today - the explanation, the default of cancel, the request for a written
reason. If the operator cancels, nothing runs anywhere. If they give a reason, it is logged and
committed, and the full sweep - every pool map, the ratchet, both coverage floors, `perf-gate` -
runs on CodeBuild against the merge with the latest main; on green the result lands on main.

**Why this priority**: The GM's second request, and the constitution's mandatory once-at-the-end
full run is the single most expensive thing the laptop does.

**Independent Test**: [quickstart](quickstart.md) §7 - cancel at the prompt: no build; answer it:
one FULL build; try the same non-interactively: refused locally, and a hand-crafted mailbox without
a committed reason: refused by the build.

**Acceptance Scenarios**:

1. **Given** the merge action with `FULL=1` in a terminal, **When** the operator presses Enter at the
   prompt, **Then** the cancellation is logged as today and no build starts.
2. **Given** the same, **When** the operator gives a reason, **Then** the reason is logged as
   `permitted`, that log entry is committed and shipped with the work, and one build runs the full
   sweep on the merge result.
3. **Given** the merge action with `FULL=1` and no terminal, **When** it runs, **Then** it is refused
   locally before any dispatch, as the existing guard refuses it today.
4. **Given** a mailbox commit whose tree carries NO `permitted` entry for this run, **When** the
   build is asked to run FULL, **Then** the build refuses the full scope and fails - the reason must
   be in the tree it tests, not in an environment variable the session sets.
5. **Given** a FULL build that ran `perf-gate`, **When** it finishes, **Then** its performance
   snapshots return to the clone's `dev/perf-log/`, stamped with the machine that took them, and
   `perf-gate` compared them only against a baseline from the same machine class.
6. **Given** a FULL build, **When** `perf-gate` needs the `-start` bookend, **Then** the build takes
   it ITSELF, in the same run, on the unmodified code (the main it just merged, before the merge) -
   the retroactive worktree baseline `perf-gate` already documents, done by the build rather than
   by a session. No separate remote run exists for a bookend.

---

### User Story 7 - GitHub main flows into the mirror and every clone without anyone remembering (Priority: P1)

A landing happens on GitHub `main` - from a build, a direct push, or the GM's own laptop. The next
time any session does anything, its clone is at that main, `/gm-assistant` is at that main, and the
renders the GM browses in `/gm-assistant` reflect it. No session ran a command to make that so.

**Why this priority**: The GM's second request, in the GM's words *"tooling level, not ... 'remember
to do it' level"* - and the project's whole history of guards is that a rule kept only in memory
does not hold.

**Independent Test**: push a commit to GitHub `main` from outside any session; start a session turn;
`git -C /gm-assistant log -1` and the clone's `HEAD` both show it, and the mirror's renders match.

**Acceptance Scenarios**:

1. **Given** GitHub `main` has advanced and the clone is CLEAN, **When** a session turn starts,
   **Then** the prompt hook fetches GitHub `main`, fast-forwards `/gm-assistant` to it under the
   ritual lock, runs render-sync there, and merges it into the clone - in that order.
2. **Given** GitHub `main` has advanced and the clone is DIRTY (mid-task), **When** a session turn
   starts, **Then** the fetch, the mirror fast-forward and render-sync still run; only the clone
   merge is skipped, with today's "mid-task, sync-in skipped" message. Mid-task work is sacred;
   the mirror is nobody's workspace and cannot fall behind because a session is busy.
3. **Given** `/gm-assistant` cannot fast-forward (someone committed there by hand), **When** the
   mirror step runs, **Then** it stops and says so rather than merging in the mirror.
4. **Given** nothing has changed, **When** a turn starts, **Then** it costs what sync-in costs today -
   the fetch, a no-op fast-forward, and render-sync's cache short-circuit.

---

### User Story 8 - Every remote run is preceded by local checks, with the build warmed in parallel (Priority: P1)

Any remote target - reference-scope or FULL, merge or iteration - runs the same local ladder first:
lint in seconds; then, with the build already started and parked, the reference settlement(s)
locally; the build is released only when they pass and stopped the moment one fails.

**Why this priority**: The GM's third request, and its reason: *"there's no point in doing the
expensive AWS dispatch if we are not going to run the local tests."*

**Independent Test**: [quickstart](quickstart.md) §9.

**Acceptance Scenarios**:

1. **Given** a dispatch whose lint fails, **When** it runs, **Then** it stops in seconds and no
   build is started - nothing about AWS has happened.
2. **Given** lint passes, **When** the dispatch continues, **Then** a build is started on the right
   project and parks at its first step waiting for a go/abort signal, while the reference
   settlement(s) run locally.
3. **Given** a reference settlement fails locally, **When** that is known, **Then** the parked build
   is stopped immediately (a queued build stops for free; a started one costs its partial minute)
   and the dispatch reports the failure.
4. **Given** every reference settlement passes, **When** that is known, **Then** the build is
   released and proceeds to the merge and the gate.
5. **Given** the dispatcher dies with a build parked, **When** the park timeout elapses, **Then** the
   build aborts itself - a parked build can never wait indefinitely on a session that is gone.
6. **Given** another session's build is parked or running, **When** this session stops a build,
   **Then** it can only stop the build it started - build ids are per dispatcher, nothing is shared.
7. **Given** a `FULL=1` dispatch, **When** the local ladder runs, **Then** the reference check is
   NOT skipped by the prompt: prompt (authorizes the expense), lint, reference, release. `REF_OK`
   remains a separate, logged bypass of the reference step, as it is for every other target.

---

### Edge Cases

- **The FULL prompt's answer travels in the tree.** The build cannot ask a question, so it must be
  handed the answer in a form it can trust more than an environment variable: the `permitted`
  bypass-log entry, committed, with the commit it authorized as an ancestor of the tree under
  test. Forging one locally is an edit to a tracked file and appears in the diff - the visibility
  bar feature 127 set for every remaining bypass.
- **A docs-only push still has to reach main.** The GM's spec-number claim protocol pushes a fresh
  `specs/NNN/` minutes after it is written. That delta has no diagram code, so it goes to main by the
  direct route - a fast-forward push from the clone, with today's local pre-push guards - and costs
  nothing. Two routes to main are therefore required, and which one applies is decided by the same
  delta inspection that decides dispatch.
- **"Our work" after a sync-in.** A clone that pulled main mid-feature has main's commits in its
  history. The delta that matters is what THIS clone added since it diverged from main - the
  commits main does not have - never "everything that differs from where main was when we started."
- **A merge commit the session made locally.** If the session merged main by hand, the merge commit
  is "ours" but its content is main's. The delta inspection must look at the changes the clone's own
  commits introduce, not at file lists in merge commits.
- **A verified tree that main has since moved past.** The record is keyed by the tree the build
  would push; if main advanced, the merge result is a different tree and the record simply does not
  match. No invalidation logic is needed.
- **The build times out or is stopped.** Outcome is failure; the local run-log records it as such;
  the verification state becomes "failed gate" so the next `make done` refuses until a local check
  passes.
- **The reference settlement is red.** The remote gate runs `make done`, which runs `make reference`
  first and stops there. The build fails in about a minute, which is the cheapest possible failure;
  but a session should never have got this far, because dispatch requires a green local check since
  the last edit and `make reference` is one of the accepted ones.
- **`FULL=1` on the remote gate, without the committed reason.** Refused by the build (US6 #4). The
  existing local guard - a non-interactive FULL with `REF_WHY` on the command line is refused - stays
  exactly as it is; the build-side acceptance is a SECOND door that opens only to a reason the
  operator answered at the prompt.
- **A green local `make done` followed by the merge action.** The local run counts as the green
  local check (FR-012) and satisfies today's `gate-stamp`; the merge action still dispatches, because
  the thing being verified is the merge with the LATEST main, sequentially, which a local run
  cannot be. The redundancy the GM wants removed is the one FR-013 removes: a tree already verified
  REMOTELY is not verified remotely again.
- **Performance snapshots are per machine.** The laptop's `dev/perf-log/` history stays; a
  build-machine snapshot carries its machine identity and is compared only with build-machine
  snapshots. A `-start` taken on the laptop cannot pair with an `-end` taken on CodeBuild, and
  `perf-gate` says so rather than reporting a meaningless number. A FULL build therefore takes
  BOTH bookends itself - the baseline on the pre-merge main, the end on the merge - which costs one
  extra `perf` inside a run already paid for, and never a run of its own.
- **The build image is stale relative to `setup-dev-env.sh`.** The gate fails on a missing tool.
  The image is rebuilt by an explicit make target, itself a remote (paid) operation and therefore
  refusal-guarded and logged like every other.
- **Secrets.** The build needs the GitHub token and nothing else - no Obsidian Portal, Gemini, or
  Discord credentials go anywhere near it.

## Requirements *(mandatory)*

### Functional Requirements

**Where main lives, and how work reaches it**

- **FR-001**: GitHub `main` MUST be the integration point. `/gm-assistant` on the laptop MUST become
  a mirror that is updated from GitHub `main` after every landing and never pushed to directly by a
  session. Session clones are unchanged as workspaces.
- **FR-002**: There MUST be exactly two routes to main, chosen by the delta inspection of FR-007,
  never by the session: the DIRECT route (a fast-forward push from the clone, preceded by today's
  local pre-push guards) for a delta containing no diagram code, and the GATED route (the CodeBuild
  merge project) for a delta that does.
- **FR-003**: On the gated route the build MUST fetch the session's work, merge the LATEST GitHub
  `main` into it, fail immediately on a merge conflict, run the reference-scope gate on the merge
  result, and on green push that exact merge result to `main` as a fast-forward. A push refused as
  non-fast-forward MUST fail the build with a message saying main moved, and MUST NOT retry on its
  own.
- **FR-004**: No push to `main` by any route MAY be a force push or a deletion, and the build's
  credential MUST be unable to change that rule. (Done: ruleset + a contents-only token.)
- **FR-005**: The merge project MUST run one build at a time; the iteration-check project MAY run
  several. Excess builds queue.
- **FR-006**: Nothing at GitHub MAY start a build. Only a session's make target does.

**When a remote run is permitted at all** - every condition below is checked locally, before any
AWS call, and a refusal names the condition

- **FR-007**: The delta inspected MUST be the changes introduced by THIS clone's own commits since it
  diverged from main - not commits it merged in from main, and not the content of merge commits.
- **FR-008**: A remote run MUST NOT start unless that delta touches diagram ENGINE code. The set of
  engine paths MUST be one explicit list in one place. Documentation, design notes, research, the
  append-only logs, and pool `.notes.md` files are NOT engine code, even inside the skill. This list
  governs DISPATCH only; it MUST NOT narrow what the existing `gate-stamp` guard hashes.
- **FR-009**: A remote run MUST NOT start for a delta touching only files outside the diagram skill.
- **FR-010**: Only the lengthy runs - `make done` in reference scope, and `make done FULL=1` - MAY
  run remotely. `quick`, `reference`, `test-file`, `durations`, `maps`, and every read-only
  diagnostic MUST stay local.
- **FR-011**: The merge route MUST NOT dispatch while an active spec-kit feature has open tasks.
  "Active feature" is the one spec-kit already tracks. (What "complete" means for work with no
  active feature is the session's reading, flagged in Assumptions.)
- **FR-012**: A dispatch MUST be refused when the most recent recorded verification is a failed gate
  (remote or local), and MUST be permitted when it is a green local target (`quick`, `test-file`,
  `reference`, or a local `make done`) that ran after the last source edit. A source edit resets the
  state.
- **FR-013**: Before a merge dispatch, the tree that would land MUST be checked against the verified
  records (FR-016); a match skips the build.
- **FR-014**: The command MUST print, before dispatching, the estimated build minutes and cost, the
  month-to-date spend, and each condition with why it passed.

**The iteration check**

- **FR-015**: There MUST be a way to run the lengthy suite remotely mid-feature, in either scope
  (reference by default, `FULL=1` with the local prompt - third request). It MUST merge the latest
  main into the work first, bail immediately on a conflict, and otherwise run the same gate the
  merge route runs in that scope. It MUST satisfy every condition of FR-007 to FR-012 except
  FR-011.
- **FR-016**: A green remote run MUST record the exact resulting tree as verified, together with the
  build that verified it. Only the build MAY write such a record; a session MUST be unable to. The
  record is keyed by the TREE rather than the commit hash the GM named, deliberately: two merges of
  the same work with the same main produce different commit hashes and identical trees, and it is
  the content - not the commit's timestamp - that the gate verified. This is the same rule
  `gate-stamp` already applies (byte-identical Python).

**Which `make done` goes remote**

- **FR-017**: The `make done` that runs remotely is the one that is merging work back into main: the
  stop-work ritual's push, on the gated route. A `make done` invoked on its own, not as part of a
  push, runs locally as it does today, free and unprompted, and its green result counts as a local
  verification under FR-012.
- **FR-018**: There is NO local override of the gated route. A gated-route delta that cannot be
  dispatched does not merge; the work stays in the clone until it can be.
- **FR-019**: A dispatched run MUST behave like today's backgrounded gate from the session's side:
  one command that returns the build's exit status, with the build's log streamed into the
  command's output, so the existing background-and-act-on-notification loop and the existing hooks
  work unchanged. The session MUST NOT need to poll.

**Audit and cost**

- **FR-020**: Every remote run MUST leave a local run-log entry marked as remote, carrying the build
  id, minutes billed, cost at the project's rate, and outcome. `make audit` MUST show remote runs
  and a month-to-date cost total from them.
- **FR-021**: A dispatch refused because the monthly hard stop has tripped MUST say so and name the
  re-enable action.

**Guards**

- **FR-022**: Every new refusal in this feature is a guard under constitution XVIII: it ships with a
  test that proves it FIRES on its case and a test that proves it STAYS QUIET on correct work, and
  those tests run in the gate.
- **FR-023**: The new make targets are operations under feature 127: reachable only through this
  project's make, refused elsewhere, and named in every refusal that applies to them.

**The full sweep on CodeBuild** (second request)

- **FR-024**: The merge action AND the iteration check MUST accept `FULL=1` (third request; FR-015
  is amended accordingly). The prompt - the
  explanation, the default of cancel, the written reason, the log entry, the refusal when no
  terminal is attached - runs LOCALLY, unchanged, before any dispatch.
- **FR-025**: A `permitted` answer MUST be committed and shipped in the tree the build tests. The
  build MUST run the full scope only when that tree carries a `permitted` entry whose recorded
  commit is an ancestor of the tree under test and whose target is the full sweep; otherwise it
  MUST refuse the full scope and fail. The build MUST NOT accept the reason from an environment
  variable alone.
- **FR-026**: The existing local refusal of a non-interactive FULL run with `REF_WHY` on the command
  line MUST remain exactly as it is.
- **FR-027**: The verified-tree record for a FULL run MUST say so, and a reference-scope record MUST
  NOT satisfy a FULL merge's short-circuit (a FULL record satisfies either).
- **FR-028**: The bookends `perf-gate` pairs MUST both be build-machine snapshots produced INSIDE
  the remote FULL run: the `-end` on the merge result, and the `-start` taken by the same build on
  the unmodified code (the main it merged, before the merge - the retroactive baseline `perf-gate`
  already documents). Both MUST return to the clone's `dev/perf-log/` carrying the machine identity
  that took them. **No bookend may be a separate remote dispatch; FR-010's two permitted remote
  runs stand unchanged.**
- **FR-029**: `perf-gate` MUST compare only snapshots from the same machine class, and MUST refuse
  with a message naming the mismatch when asked to pair a laptop snapshot with a build snapshot.
  Laptop-era snapshots stay as history.

**Sync at the tooling level** (second request)

- **FR-030**: At the start of EVERY session turn, regardless of the clone's working-tree state, the
  tooling MUST fetch GitHub `main`, fast-forward `/gm-assistant` to it under the ritual lock
  (stopping with a message if it cannot), and run render-sync there - so the mirror and the GM's
  browsed renders never lag GitHub `main` by more than one turn. The clone-side merge keeps today's
  behavior: it runs on a clean clone and is skipped, with the existing message, on a dirty one. The
  existing prompt hook is the mechanism and is changed to make the mirror steps unconditional.
- **FR-031**: The GM's own laptop pushes to GitHub `main` MUST flow through the same path with no
  special handling.
- **FR-032**: CLAUDE.md and `docs/session-clones.md` MUST describe the post-feature flow - GitHub
  `main` as the integration point, the mirror, the two routes, `FULL=1` remote - and MUST NOT
  retain the retired local-main-as-integration-point instructions.

**Local checks first, build warmed in parallel** (third request) - the general pattern for EVERY
remote target

- **FR-033**: Every dispatch MUST run the cheap local checks (lint, format, types - seconds) before
  anything touches AWS, and MUST stop there, having started nothing, if they fail.
- **FR-034**: Every dispatch - and every local `make done FULL=1` - MUST run the reference
  settlement(s) first and MUST NOT release the build (or start the suite) until every one of them
  passes. For `FULL=1` this step is NOT skipped by the prompt: the
  prompt authorizes the expense, the reference check still runs. `REF_OK` remains the one, separate,
  logged way to skip the reference step, exactly as for every other expensive target. (This fixes
  the current behavior, where `done FULL=1` runs `bypass-audit` in place of `reference`.) As
  reference settlements are added for further tiers, this step runs all of them; running them in
  parallel is permitted.
- **FR-035**: Once the cheap checks pass, the dispatch MUST start the build immediately and the
  build MUST park at its first step, waiting for a go/abort signal, so that provisioning and source
  fetch overlap the local reference check. On a local failure the dispatch MUST stop its own build
  at once; on success it MUST release it. Whether the parked start actually saves time is measured
  (SC-011), not assumed.
- **FR-036**: A parked build MUST abort itself after a bounded wait (order of two minutes) if no
  signal arrives, so a dead dispatcher can cost at most that.
- **FR-037**: A dispatcher MUST only ever stop the build it started. Nothing shared exists between
  sessions on the AWS side: each build is its own; the merge project's single slot serializes merges
  and a parked merge build holds it for at most the local reference time - or FR-036's park timeout
  if its dispatcher dies, during which another session's merge queues unbilled. The only
  cross-session coordination remains the local ritual lock, unchanged.

### Scope Boundaries

**In scope**: `make done` in reference scope AND `make done FULL=1` as the merge gate on CodeBuild,
the FULL prompt kept local; the iteration check in either scope; the local-checks-first-with-
parked-build pattern for every dispatch; the dispatch conditions; the two
routes to main and the mirror; the tooling-level sync flow; the verified-tree record; the
performance bookends on CodeBuild with per-machine identity; the audit and cost visibility; the
build image and its rebuild target; a measured remote baseline for both scopes.

**The performance integration, previously deferred, is now in scope.** The GM's first request said
*"performance checks ... that is going to need to be integrated into this AWS code"*, and the first
version of this spec deferred it because `perf-gate` only runs inside `FULL=1`. The second request
puts `FULL=1` on CodeBuild, which removes the reason for the deferral: FR-028 and FR-029 deliver it,
and the *"reconstituted"* numbers are the build-machine bookends.

**Out of scope, stated so it is not reopened by accident**:

- `make cohort`, `cache-audit`, and every other prompted target beyond `make done FULL=1` stay local.
  The GM's second request named *"the full sweep"*; the mechanism it specifies (prompt locally,
  ship the answer in the tree, dispatch) generalizes to any prompted target for the cost of a
  registry row, and extending it is a later, explicit decision.
- Running Claude Code sessions on AWS. The GM chose to keep sessions local.
- Any change to what the gate CHECKS. This feature changes where it runs and when.
- The webapp's `make done`. It has never been slow enough to matter.
- Bringing the cost controls into the repository as code. Not asked for; the controls exist and are
  described in the baseline table. Mentioned to the GM as an aside, not built.

### Key Entities

- **Delta**: the changes this clone's own commits introduce relative to main. The single input to
  every dispatch decision.
- **Engine path list**: the one explicit list of diagram-skill paths whose change requires the gate.
- **Verification state**: per session - the most recent verification event (green local target /
  failed gate / none since last edit).
- **Verified-tree record**: written only by a green build; keyed by the exact tree that build
  produced by merging main; carries the build id, time, and SCOPE (reference or full).
- **Permitted entry**: the bypass-log entry an operator's answer at the local FULL prompt produces;
  committed; the build's evidence that the full scope was authorized.
- **Machine identity**: what a performance snapshot records about where it was taken; the key
  `perf-gate` pairs bookends by.
- **Route**: DIRECT or GATED, derived from the delta.
- **Remote run-log entry**: the local audit record of a remote build.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A finished diagram-code feature reaches main through exactly one paid build, and the
  merge that lands is byte-identical to the tree that build verified.
- **SC-002**: Zero builds are started for: a delta outside the diagram skill; a docs-only diagram
  delta; a delta consisting only of merged-in main; a feature with open tasks; a `make done` run
  straight after a failed `make done`. One test per case, each asserting the build list did not grow.
- **SC-003**: A tree verified by the iteration check merges with zero additional builds when main
  has not moved.
- **SC-004**: The wall time of `make done` on CodeBuild is measured and recorded in the skill's
  dated timing ledger (`.claude/skills/diagram/timings.md`) alongside the laptop figure; the number
  decides nothing in this spec and is not guessed here.
- **SC-005**: `make audit` shows every remote run with its cost and a month-to-date total that
  agrees with the CodeBuild console to within one run's rounding.
- **SC-006**: Every local target's wall time - `make done` included - is unchanged within noise, and
  none of them makes a network call.
- **SC-007**: Every new guard has a fires/stays-quiet test pair in the gate, and deleting the guard
  turns the gate red.
- **SC-008**: A `FULL=1` merge produces exactly one build that ran every pool map, the ratchet, both
  coverage floors and `perf-gate`; cancelling at the prompt produces zero builds; a mailbox without
  the committed reason produces a build that refused the full scope.
- **SC-009**: After a push to GitHub `main` from outside any session, one session turn later
  `/gm-assistant` and its renders reflect it whatever state the clone is in, and a CLEAN clone
  reflects it too - verified by commit hash and by a render's content hash - with no command run
  by hand.
- **SC-010**: Every `perf-gate` verdict pairs two build-machine snapshots from one FULL run, and
  `perf-report` names the machine on every row. No remote run exists whose only job is a bookend.
- **SC-011**: A dispatch whose lint fails starts zero builds; one whose reference check fails
  starts one build and stops it within seconds of the failure; the parked start's saving (wall
  time to the gate's first test, parked vs not) is measured and recorded in `timings.md`, and the
  cost of an aborted parked build is recorded beside it.
- **SC-012**: `make done FULL=1`, local or remote, refuses to run the suite when the reference
  settlement is red and `REF_OK` is not set - demonstrated by a test that turns the reference map
  red and runs it.

## Assumptions

- **FR-011 for work with no active feature is the session's reading, flagged for the reviewer.** The
  GM's condition is that a feature be *"actually complete and shippable"* before its merge costs
  money. Spec-kit tracks completeness for spec-kit features (`tasks.md`). Tweak-and-iteration work in
  the diagram skill - CLAUDE.md's "fixing one bug, regenerating one item" - has no task list, and the
  GM did not say what "complete" means for it. This spec reads it as: with no active feature there is
  nothing for the completeness check to inspect, so it passes, and the other conditions (our own
  engine code, a green local check, no failed gate since) still bind. The alternative, if the
  reviewer or the GM prefers it: an affirmative declaration at the prompt for untracked work, logged
  like every other answer. Cheap to switch.
- **FR-012's third case is the session's reading, flagged for the reviewer.** The GM stated two
  cases: a failed `make done` most recently means refuse; a green local test most recently means
  dispatch. The case where a source edit happened AFTER the green local test is not stated. This spec
  reads it as refuse, because the green run vouched for different code - the same reasoning
  `gate-hooks.sh` already applies to `-k` subsets. If the reviewer finds this an addition, the
  fallback is to treat "green local test at any point since the last failed gate" as sufficient.
- **The public repository.** `EliAndrewC/gm-assistant` is public, which is what makes the ruleset on
  `main` available on the GM's plan. Mailbox branches are therefore public too; nothing secret is
  tracked, and `development-secrets.ini` stays gitignored.
- **The mirror is updated every turn and by every landing**, under the same lock render-sync uses
  today (FR-030). The existing prompt hook is the mechanism, MODIFIED by this feature so the fetch,
  mirror fast-forward and render-sync are unconditional; the clone-side merge keeps today's
  dirty-clone skip.
- **"Machine identity" for a snapshot** is the compute type plus the image digest for a build, and
  the hostname plus CPU model for the laptop - enough to tell the two apart and to notice when the
  build image changes under a comparison. Exact fields are the plan's to choose.
- **The GM's laptop-side "push main to GitHub" job goes away for this repository.** The memory note
  and CLAUDE.md that describe it are updated by this feature. `/host-l7r-repo` is unaffected.
- **Bandwidth.** A mailbox push carries only the clone's new commits; the build clones shallowly.
  Neither is expected to be measurable next to provisioning, and the measurement task will say.
- **The build image is built by CodeBuild itself** from `setup-dev-env.sh`, so the laptop needs no
  Docker. Building it is a paid operation and gets a make target with the same refusal-and-log
  treatment as every other.
- **Existing infrastructure is reused, not recreated**: the two projects, the IAM user, the secret,
  the budgets and alarms from 2026-08-24 - reused as they stand; this feature neither re-provisions
  nor re-declares them.
- **Nothing in this feature touches map geometry, and no failing seed is addressed.** The standing
  scope limit - a working reference hamlet at one seed - is unchanged.

## Review history

### Second amendment (GM's third request, 2026-08-24) - rounds start again at 1

Added: Decisions 11-12, User Story 8, FR-033..FR-037, SC-011..SC-012, a baseline row recording
that `FULL=1` does not check the reference map first today; FR-015 and FR-024 reopened so the
iteration check accepts `FULL=1` (the second amendment's round-2 cut is withdrawn on the GM's own
words); FR-010 unchanged (still the two lengthy runs, now on both paths).

- **Second-amendment round 1** - `FAITHFUL`, with three in-passing corrections applied (FR-037 now
  names the park timeout as the worst case a dead dispatcher holds the merge slot; the baseline row
  cites the `done:` target rather than a line number; FR-034's MUST binds a local `FULL=1` too).
  The reviewer verified the Makefile claim itself and judged the parked-build realization faithful
  because the spec discloses where it falls short of the GM's premise (a started build costs its
  partial minute; the saving is measured by SC-011, not assumed).

### First amendment (GM's second request, 2026-08-24)

Added: Decisions 9-10, User Stories 6-7, FR-024..FR-032, SC-008..SC-010, three entities, two
assumptions; the performance deferral withdrawn and delivered by FR-028/FR-029; `FULL=1` moved from
out of scope to in scope with the local prompt kept; cohort and the other prompted targets remain
out of scope by name.

- **First-amendment round 1** - `CHANGES REQUIRED` (2 findings). (1) FR-028 / US6 #6 / SC-010 had
  created a THIRD paid dispatch - a standalone remote `-start` bookend at feature start - that
  contradicted FR-010 and the GM's *"only doing this for actual make done actions that are merging
  stuff back into main"*, and would have had to drive through FR-011 and FR-012 to run at all.
  Restated: both bookends are taken INSIDE the FULL build (the `-start` on the pre-merge main, the
  retroactive baseline `perf-gate` already documents); no bookend is a dispatch of its own. (2)
  FR-030 claimed an every-turn guarantee from a hook that skips sync-in on a dirty clone - most of
  any working session. Split: the fetch, mirror fast-forward and render-sync are unconditional
  every turn; only the clone merge keeps the mid-task skip. US7 gained the dirty-clone scenario;
  SC-009 restated. The reviewer's aside - `bypass-audit` prints a stale `bypass-log.jsonl` path in
  a message this feature makes load-bearing - is a Principle XIV fix, added as a task.
- **First-amendment round 2** - `CHANGES REQUIRED` (2 findings, both one edit). (1) FR-024 had extended
  `FULL=1` to the iteration check - unrequested, a new mid-feature paid path, and contradicting
  FR-015 - cut back to the merge action alone. (2) The mirror Assumption still said "every
  sync-in ... nothing new has to be remembered", the premise round 1 removed; restated to say the
  hook is modified and the mirror steps are unconditional.
- **First-amendment round 3** - `FAITHFUL`. Both edits verified; no residue; every FR citation resolves;
  each clause of the second request mapped to a requirement and each amendment requirement back to
  a clause of one of the two requests.

### Original spec

- **Round 3** - `FAITHFUL`. Both round-2 edits verified in the text; every FR citation outside the
  Requirements list resolves; the performance deferral's load-bearing fact (`perf-gate` is a `FULL=1`
  phase only) checked against the Makefile.
- **Round 1** (FR numbers below are round-1 numbering; FR-021/FR-022 were since renumbered) -
  `CHANGES REQUIRED` (5 findings, 3 nits). (1) FR-017 made EVERY `make done` remote
  where the GM had said *"only ... actual make done actions that are merging stuff back into
  main"*, and FR-018 then turned today's free local gate into a prompted override - restated: the
  merging `make done` (the push) goes remote, a plain `make done` stays local and free, and there is
  no local override of the gated route. (2) FR-011's "no active feature = complete by committing"
  was the session completing the GM's thought - moved to Assumptions, flagged, alternative stated.
  (3) FR-021 answered *"that is going to need to be integrated into this AWS code"* with a MUST NOT -
  rewritten as a visible deferral that quotes the clause and carries the machine-identity rule
  forward rather than as a bar. (4) FR-022 (cost controls as repo code) was unrequested - removed,
  listed out of scope, kept as an aside for the GM. (5) FR-008's coupling to `gate-stamp` could have
  NARROWED a Principle XIII guard as a side effect - cut; the list governs dispatch only and may not
  shrink what `gate-stamp` hashes. Nits: `timings.md` located correctly; the tree-vs-commit-hash
  departure now carries its why; the heading counts both delegated decisions.
- **Round 2** - `CHANGES REQUIRED` (2 findings, both one-line): an Assumptions sentence still said
  "FR-022 brings their definitions into the repository" - a dangling pointer to the deleted
  requirement that would have reinstated the unrequested infrastructure-as-code scope - and the
  baseline table's performance row pointed at FR-021, which had become the hard-stop refusal. Both
  fixed. The reviewer confirmed all five round-1 findings resolved in the text, and judged the
  merge-still-dispatches-after-a-green-local-run edge case faithful on the GM's own words (the
  short-circuit the GM described is against a *"successful remote run"*).
