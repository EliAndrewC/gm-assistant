# Feature Specification: The Merge Gate Runs on AWS CodeBuild, and Only When It Must

**Feature Branch**: none - this project does not use feature branches (`SPECIFY_FEATURE=128-codebuild-merge-gate`)

**Created**: 2026-08-24

**Status**: APPROVED by `spec-fidelity` (round 3, verdict FAITHFUL). **This feature is SPECIFIED AND PLANNED ONLY.**
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
| the full pre-push sweep | did not exist as a separate thing | **`make done FULL=1`** ~6 min: adds every live pool map, the seeds 41-44 ratchet, both coverage floors, and `perf-gate`. It PROMPTS with a cancel-by-default question and REFUSES to run without a terminal. **Out of scope**: remote runs are non-interactive by construction, so the existing guard already refuses it there, and the GM has said the prerequisite targets are not ready. |
| what the push already checks | flock'd pull+push, render-sync | that, plus **`gate-stamp`** (a green `make done` must have run against byte-identical Python), **`review-gate`** (a spec carries a FAITHFUL verdict; a re-rolled map has its notes touched), duplicate-def screening. All local, all cheap, all kept. |
| performance | not tracked | **bookended per feature** (`make perf LABEL=NNN-start` / `-end`, `perf-report`), enforced by `perf-gate` inside `FULL=1` only. Snapshots are laptop measurements and are **only comparable on the same machine** (see the performance deferral in Scope Boundaries). |
| CodeBuild startup | "30-60 s" estimated | **20 s wall, 7 s provisioning**, measured on the stock image. With a custom image from ECR: unmeasured, expected 20-40 s. |
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
8. **Initial scope is the five-minute `make done` that precedes a push to main, and nothing
   larger.** *"at least in the initial phase only doing this for actual make done actions that are
   merging stuff back into main."*

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

### Edge Cases

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
- **`FULL=1` on the remote gate.** Refused by the existing `bypass-audit` guard (no terminal), so the
  remote gate can never run more than reference scope. Stated so nobody "fixes" it.
- **A green local `make done` followed by the merge action.** The local run counts as the green
  local check (FR-012) and satisfies today's `gate-stamp`; the merge action still dispatches, because
  the thing being verified is the merge with the LATEST main, sequentially, which a local run
  cannot be. The redundancy the GM wants removed is the one FR-013 removes: a tree already verified
  REMOTELY is not verified remotely again.
- **Performance snapshots on the build machine** would be a different machine's numbers. See the
  deferral in Scope Boundaries.
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
- **FR-010**: Only the lengthy run - the reference-scope `make done` - MAY run remotely. `quick`,
  `reference`, `test-file`, `durations`, `maps`, and every read-only diagnostic MUST stay local.
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

- **FR-015**: There MUST be a way to run the lengthy suite remotely mid-feature. It MUST merge the
  latest main into the work first, bail immediately on a conflict, and otherwise run the same
  reference-scope gate the merge route runs. It MUST satisfy every condition of FR-007 to FR-012
  except FR-011.
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

### Scope Boundaries

**In scope**: the reference-scope `make done` as the merge gate on CodeBuild; the iteration check;
the dispatch conditions; the two routes to main and the mirror; the verified-tree record; the audit
and cost visibility; the build image and its rebuild target; a measured remote baseline for
`make done`.

**Deferred, with the GM's clause quoted so the deferral is visible.** The GM said: *"we have added
things like performance checks to see that our performance has not degraded. And that is going to
need to be integrated into this AWS code. And, also, I guess, the numbers that we have already
gathered are not quite valid because they are gathered for my laptop, and so they will need to be, I
guess, reconstituted."* The performance checks are the `perf` bookends and `perf-gate`, and
`perf-gate` runs only inside `make done FULL=1` - which this feature does not run remotely, on the
GM's own instruction that the prerequisite targets are not ready. So the integration is NOT
delivered here. What this feature does carry forward for it: (a) the rule that a snapshot is only
comparable with a baseline from the same machine, so when `FULL=1` does go remote the build machine
gets its own `-start` baseline and its snapshots carry their machine identity; (b) the remote
`make done` wall-clock measured by this feature, which is the first "reconstituted" number. Nothing
in this feature runs `perf` or `perf-gate` remotely, and nothing forbids the later feature from
doing so.

**Out of scope, stated so it is not reopened by accident**:

- `make done FULL=1`, `make cohort`, `cache-audit`, and every other prompted target stay local. The
  GM: *"you genuinely should not be able to use our make commands to do work in AWS just yet because
  the prerequisite make targets which would need to be working or not working yet."* The existing
  refusal of a non-interactive FULL run already enforces this remotely.
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
  produced by merging main; carries the build id and time.
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
- **The mirror is updated by the session that landed work**, as part of the stop-work ritual, under
  the same lock render-sync uses today. Another session's stale mirror is harmless: the next sync-in
  pulls from GitHub, not from the mirror.
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
