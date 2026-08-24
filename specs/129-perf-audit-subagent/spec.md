# Feature Specification: The Performance Audit Subagent

**Feature Branch**: none - this project does not use feature branches (`SPECIFY_FEATURE=129-perf-audit-subagent`)

**Created**: 2026-08-24

**Status**: REVISED after the GM's 2026-08-24 band ruling; re-reviewed, 4 findings applied. Two questions routed to the GM (the >10% measurement scope, and storage). (Was FAITHFUL at round 3 against the earlier request.) NOT implemented, at the GM's explicit instruction (*"Do not start
work on the spec"*). The measurements below were taken before implementation precisely so they would
be in hand when it begins.

**Input**: [`gm-request.md`](gm-request.md), verbatim and unedited.

**Supersedes**: the two-band slowdown rule added to constitution VI earlier the same day (v1.16.0).
That rule stands until this feature ships; this replaces it.

## The feature, in one sentence

A performance increase must be **explained and independently confirmed** at any size, **audited to a
higher bar against deeper data** above 5%, and **personally signed off by the GM before it reaches
main** above 10% - and none of it may be something the session that caused the slowdown can grant
itself.

## The bands

Set by the GM on 2026-08-24, in the ruling that supersedes the band design in their earlier request.

| increase | what it takes |
|---|---|
| **any increase** | an explanation, **with a `perf-audit` subagent confirming it**. |
| **> 5%** | more advanced analysis and a higher bar of justification: the subagent must affirmatively find the increase **necessary**, **commensurate** with the functionality gained, and that there is **no good way around it**. |
| **> 10%** | **the GM signs off personally, before the work is committed back to main.** |

**THE SUBAGENT IS ON EVERY INCREASE, NOT ONLY THE BIG ONES.** This is the load-bearing change from the
earlier design and the thing an implementer is most likely to get wrong by carrying the old shape
forward. The GM's earlier request put the subagent at the 5% trigger; the ruling moves it to *"any
increase: explanation, with a subagent reviewer confirming"*, and makes 5% the point where the
ANALYSIS DEEPENS and the JUSTIFICATION BAR RISES rather than the point where review begins.

**The three bands are a LADDER, and each rung keeps everything below it.** What escalates:

1. **Any increase** - the session writes what caused it; a subagent confirms the explanation is
   consistent with the measured evidence. The question is narrow: *does the stated cause match what the
   data shows?* Tier-1 evidence (the per-stage delta, which costs nothing) is normally enough.
2. **Above 5%** - the subagent no longer merely confirms a story, it independently ADJUDICATES the
   three criteria, and may demand deeper evidence than the stage delta when the stage delta cannot
   settle the question. A confirmed explanation is not a passed audit.
3. **Above 10%** - everything above, plus the GM personally. **The enforcement point is the PUSH, not
   the gate**, because the GM's words are "before it is committed back to main". That makes it a
   `sync-with-main.sh` concern alongside the existing review gate, not a `make done` concern.

**WHICH NUMBER EACH BAND MEASURES.** The **any-increase** and **>5%** bands apply to **any individual
seed OR the total** - whichever crosses first.

The **>10%** band is on the **TOTAL only** - and this is the AUTHOR'S CARRY-FORWARD, not the GM's
instruction. **OPEN GM QUESTION, alongside storage.** What the record supports is that the GM chose
the NUMBER 10 (over a priced 25); the total-only scope came from the author's rationale in that
amendment, and it was reasoned for a band whose consequence was BLOCKING A MERGE. The ruling changed
that consequence to personal sign-off and says nothing about which number is measured.

**The concrete consequence, so the question is answerable rather than abstract**: a single seed above
10% would NOT require sign-off. Feature 128 is the worked example - total -29.9%, seed 47 +30.7% - so
it would owe the escalated audit and never reach the GM. That may be exactly right; it is not
something the GM said.

Retained as-is rather than flipped, because flipping it would be the mirror error - substituting the
author's judgment in the other direction.

The per-seed-OR-total scope for bands 1 and 2 is stated here rather than delegated to implementation.
An earlier draft left it "to be settled against the noise floor", which sounds neutral and is not: the
measured per-seed noise is higher than the total's, so every re-measurement argues for narrowing the
band to the total, and the GM's words are *"any increase whatsoever"*. The scope is not
implementation's to choose. **Note the honest limit of that reasoning**: the GM's instruction was "any
increase"; that it is measured per seed OR total is the author's inference from those words plus the
per-seed rule being replaced. Sound, and retained - but an inference.

**A COST THIS DESIGN CARRIES, recorded as an observation and NOT as an argument for narrowing it.**
The GM's own reasoning is that nearly every feature adds code and therefore time, so the any-increase
band will fire on most features - and each firing now costs a subagent round trip. That is what was
asked for and it is not the spec's to trim. What the spec CAN do, and requires, is make the common
case cheap: the band-1 question is narrow, its evidence is already recorded at zero overhead, and the
artifact arrives pre-populated. If the round trip nonetheless proves burdensome in practice, that is a
report to the GM with the measured cost, not a threshold quietly raised.

## Measured evidence, taken before implementation

Everything in this section is a stopwatch, not an estimate. It exists because the design decisions
below turn on these numbers and the first version of this analysis got one of them wrong by asserting
"substantially" without measuring.

### THE TOOLING ALREADY PROFILES, at stage granularity, for free

**Read this before considering any new profiler.** Every `perf_snapshot` record already carries a
per-stage breakdown of each seed, recorded at zero measurable overhead, and already stored
one-file-per-run. From the noise runs taken for this spec, seed 25:

    seconds: 80.8
    stages: {web: 62.62, notice: 5.44, field: 4.55, track: 3.24, hinterland: 3.00,
             homesteads: 0.91, appurtenances: 0.53, woodland: 0.20, crossings: 0.16,
             windbreak: 0.05, seat: 0.04, sink: 0.01, water_frame: 0.00, frame: 0.00}

**That is 78% of the seed in one stage, and it is already on disk, before/after, for every run this
project has ever recorded.** A before/after stage delta is a profile in every sense that matters to
the audit question the GM asked: it says which part of the build grew and by how much.

This was missed by the first draft of this spec, which went straight to proposing a new profiling
subsystem. **The first implementation task is therefore NOT "choose a profiler" - it is "determine
what the existing stage timings cannot answer".** A new profiler is justified only against that gap.

The likely gap, stated so it can be tested rather than assumed: stage timings say WHICH stage grew,
not WHICH FUNCTION inside it. When a feature adds a check or a placement rule inside `web`, the stage
delta will show `web` grew and stop there. Whether that is enough for the audit's "necessary and
commensurate" judgment is an open question - and it may well be enough, because the audit is about
whether the new functionality justifies its cost, not about micro-optimizing.

**A tiered design is therefore the leading candidate**, and it satisfies the GM's "automatically
generates a profile" at zero cost in the common case:

1. **Always**: the stage delta, already recorded, no overhead, no new dependency.
2. **Only when the stage delta does not explain the change**: a function-level profile of the one
   stage that grew.

### If a function-level profiler IS needed, cProfile's cost is not yet established

| workload | plain | under cProfile | overhead |
|---|---|---|---|
| the check battery on a real manifest (mixed engine work) | 2.27 s | 6.72 s | +196% |
| a pure geometry loop (`_fabric_hits`, 9.5M calls/sec unprofiled) | 0.72 s | 2.45 s | +242% |

**NEITHER FIGURE IS THE ONE THAT MATTERS, and the first draft of this spec drew a conclusion from
them anyway.** `make perf` times GENERATION; both rows above measure checking and geometry helpers,
because those can be driven in-process. Generation includes SVG string building and subprocess
rendering, which cProfile taxes far less than a tight call loop, so the real figure is probably lower -
possibly much lower than the 20% line the GM set as the point where always-on becomes attractive.

**FR-012 requires the real number before this question is settled.** The heading above says "not yet
established" rather than "always-on is out" deliberately: the earlier draft asserted "It is 3x, not
20%" in the same breath as admitting it had not measured the right thing.

**And the break-even depends on how often a profile is actually wanted, which the first draft got
wrong too.** It assumed profiles are needed only on 5% audit trips - roughly one run in three at
break-even. But US1 wants a stage breakdown on the >0% band, which fires on most features. If the
audit ends up wanting function-level data at that same rate, demand approaches one profile per run and
the arithmetic flips toward always-on, which is the direction the GM's own reasoning pointed. **Only
tier 1 above escapes this**, because it costs nothing and so has no break-even at all.

For reference, the arithmetic if it is ever needed: a 4-seed run is ~4.5 min; always-on at 3x adds
~9 min per run; a trip needs two profiled runs (baseline in a worktree plus current), ~+27 min. Break-
even is one trip in three runs.

### A sampling profiler, if tier 2 is needed and cProfile is too dear

A sampling profiler costs single-digit percent instead of 200%, which would let tier 2 simply be
always-on. **Measured obstacle**: `py-spy` 0.4.2 installs cleanly
(`pip install --break-system-packages py-spy`) but **cannot attach in this container** -
`Failed to suspend process` unprivileged, `Permission denied (os error 13)` under `sudo`. The
container lacks `SYS_PTRACE`.

Routes, if and only if tier 2 turns out to be needed:

1. **A `sys.monitoring` sampler.** Python 3.14 is the pin and `sys.monitoring` is present (verified).
   Stdlib, no ptrace, no capability change, no new dependency, nothing outside this repository.
2. **`--cap-add SYS_PTRACE`** in [`scripts/launch-container.sh`](../../scripts/launch-container.sh)
   plus py-spy. **This is a GM-FACING CHANGE, not an implementation detail** - the GM launches the
   container, it grants a capability the container does not currently have, and it needs a rebuild.
   It should be proposed to them rather than chosen by a session.
3. **Triggered cProfile**, per the break-even above.

Route 1 is ranked first now precisely because route 2 changes something the GM owns. An earlier draft
had that ordering backwards.

### The noise floor

**Three `make perf` runs, same commit (`4ecdced`), no code change between them**, taken 2026-08-24
specifically so this feature's thresholds could be set against a measured floor rather than a guess:

| seed | run a | run b | run c | spread | sd/mean |
|---|---|---|---|---|---|
| 4 | 26.9 s | 26.8 s | 27.1 s | 1.1% | 0.6% |
| 25 | 80.8 s | 80.5 s | 80.8 s | 0.4% | 0.2% |
| 39 | 70.8 s | 70.7 s | 71.9 s | 1.7% | 0.9% |
| 47 | 88.7 s | 89.3 s | 89.3 s | 0.7% | 0.4% |
| **TOTAL** | **267.2 s** | **267.3 s** | **269.1 s** | **0.7%** | **0.4%** |

**Worst per-seed spread 1.7%; total spread 0.7%.**

**This machine is quiet, and the GM's 1% instinct survives contact with the data - on the TOTAL.**
The author had flagged a concern before measuring, that a >0% band might sit below the noise floor and
so fire on noise every run, which is the project's stated recipe for training a session to bypass
guards. **That concern was wrong for the total** and is recorded here as wrong so it is not raised
again: at 0.7% spread, any total increase of about 1% or more is a real signal.

**It is NOT wrong per seed.** Seed 39 varies by 1.7% between identical runs, so a per-seed band set at
"any increase" would fire on the machine roughly as often as on the code.

**What follows for the bands.** The NUMBERS below may be re-derived if the machine changes and the
floor is measured again. **The SCOPE of the any-increase band may not** - that it covers any seed or the total
is the GM's instruction, and lines further down reserve any narrowing of it to the GM:

- **The ANY-INCREASE band applies to EITHER measurement - per seed OR total.** The GM said *"any
  increase whatsoever"*, and the rule being replaced was itself per-seed (*"Any seed more than 5%
  slower must be DIAGNOSED"*), so scoping the replacement to the total alone would shrink the very
  surface the GM was changing. A 1.9% seed is exactly the creep this mechanism exists to catch.
- **The 1.7% per-seed floor is a CAVEAT AN EXPLANATION MAY CITE, not a threshold below which nothing
  is owed.** "This seed rose 1.2%, which is inside the 1.7% spread measured on identical runs" is a
  perfectly good EXPLANATION - but under the GM's ruling an explanation is only half the band, and a
  subagent still confirms it. A sentence on the record does not end the matter. What is not acceptable
  is the increase going unremarked because it fell under a bar.
- **The 5% ESCALATION trigger is comfortably above the floor** - 3x the worst per-seed spread and 7x
  the total spread - so the DEEPER audit fires on code, not on weather. The band-1 confirmation will
  sometimes fire on weather, and the spec accepts that: see "A COST THIS DESIGN CARRIES".

**An earlier draft of this spec said the per-seed line should be "advisory below about 2%".** That was
an exception carved against the GM's own words on the strength of a measurement, caught by the
fidelity review, and it is recorded here rather than quietly deleted because it is the precise shape
constitution XVI exists to stop: a measured fact used to justify narrowing an instruction. If the
per-seed floor ever does look genuinely unworkable, **that is a question for the GM**, not a decision
for the spec.

**Re-measure the floor when the machine changes.** These numbers are a property of this container on
this host, not of the code. If perf measurement ever moves to a remote runner (see the peer session's
CodeBuild feature), the floor moves with it and every threshold here is up for re-derivation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - An increase of any size is explained AND confirmed (Priority: P1) MVP

**Independent Test**: a run whose measurement rises by any amount above zero produces a written
explanation AND a subagent confirmation of it, and the tooling declines to proceed without both.

**Acceptance Scenarios**:

1. **Given** a run 1% slower, **When** the gate is consulted, **Then** it requires a written
   explanation - the band is *any* increase, not a "meaningful" one.
2. **Given** a written explanation and no subagent confirmation, **When** the gate is consulted,
   **Then** it still refuses. The GM's words are *"explanation, with a subagent reviewer confirming"*;
   the explanation alone is half the band.
3. **Given** a subagent that finds the explanation INCONSISTENT with the measured evidence, **When**
   the gate is consulted, **Then** it refuses - a returned confirmation is not a positive one.
4. **Given** a run that is faster or unchanged, **When** the gate is consulted, **Then** nothing is
   owed and nothing is printed that looks like a problem.

**The diagnosis must be CHEAP in the common case.** The GM's own reasoning is that nearly every
feature adds code and therefore time - *"any new thing that we add to the map will increase the amount
of time that we are taking because we are adding new code"* - so this band will fire on most features.
An artifact that demands an essay every time becomes a rubber stamp, which is the exact failure this
mechanism exists to prevent. So the artifact SHOULD be pre-populated with the measured delta and the
stage breakdown, so the session never retypes a number the tooling already knows.

**But a pre-populated artifact is not a completed diagnosis.** The constitution's own definition, which
this amendment builds on, is that *"Diagnosed means explained and either fixed or accepted in writing
with the number; it does not mean noticed"* - and a machine-generated line is precisely *noticed*. The
diagnosis is complete only when a session has written what CAUSED the change. Pre-population is a
convenience that removes typing, never the explanation.

(An earlier draft said prose was required "only where the number is surprising". That weakened FR-001
while claiming not to, and the fidelity review caught it.)

### User Story 2 - Above 5%, the analysis deepens and the bar rises (Priority: P1)

**This story is an ESCALATION of User Story 1, not the introduction of review.** Review already
happened at any increase. What changes here is that the subagent stops confirming the session's
account and starts adjudicating the increase on its own terms, and that it may demand evidence beyond
the free per-stage delta.

**Independent Test**: a run over 5% cannot proceed on a confirmed explanation alone; it requires an
audit record in which the subagent independently finds the increase necessary, commensurate, and
unavoidable, citing before/after data.

**Acceptance Scenarios**:

1. **Given** a run over the threshold and only a band-1 confirmation, **When** the gate is consulted,
   **Then** it refuses and names the exact command that produces the deeper audit. A confirmed
   explanation is not a passed audit.
1a. **Given** a run over the threshold whose stage delta does not explain the change, **When** the
   audit is produced, **Then** deeper evidence is available to the subagent without a session having
   to re-run anything by hand.
2. **Given** an audit, **When** it is checked, **Then** it is valid only for the commit and the
   percentages it actually audited - a stale, reused, or pre-manufactured audit is refused.
3. **Given** the audit subagent, **When** it runs, **Then** it has before/after profiles available to
   it without needing to ask for a re-run.
4. **Given** an audit that CONCLUDES THE INCREASE IS NOT JUSTIFIED, **When** the gate is consulted,
   **Then** it refuses - a returned verdict is not the same as a passing verdict.

### User Story 3 - Neither the confirmation nor the audit is something the session that caused the slowdown can grant itself (Priority: P2)

The GM was explicit that strictness here is wanted but that they do not know if it is achievable:
*"I don't know if there is a way for our tooling to only accept this kind of flagging from the
subagent rather than from the main session. But if this is possible, then I would like that. If it is
not possible to strictly enforce that, then I would still like there to be some sort of prompting that
makes it unlikely that we will bypass this."*

**So this story has a MEASUREMENT as its first task, and its design follows the answer.**

The harness sets `CLAUDE_CODE_SESSION_ID`, `CLAUDE_PID` and `CLAUDE_CODE_CHILD_SESSION` in every
shell - verified this session in the main session's own environment. **Whether a subagent's shell
carries a DIFFERENT session id is unknown and is the load-bearing unknown of this feature.**

- **If it differs**: strict enforcement is achievable. The audit target refuses any invocation whose
  session id matches the session that recorded the bookend, and the audit record carries the auditing
  session's id so the pairing is checkable afterwards.
- **If it does not differ**: fall back to what the GM described - the target prompts, states plainly
  that the main session must not continue, names the escape hatch, and defaults to declining.

**Acceptance Scenarios**:

1. **Given** the strict route is available, **When** the main session runs the confirmation command OR
   the audit command, **Then** it is refused, and the refusal names how to have the subagent run it
   instead. **Both bands, not just the audit** - the band-1 confirmation is the one that fires on
   nearly every feature, so exempting it would exempt the common case.
2. **Given** either route, **When** an audit is granted, **Then** who granted it is recorded, so a
   bypass is visible afterwards even if it could not be prevented.

### Edge Cases

- **A slowdown with no baseline to compare against.** Already handled by `perf-gate`, which refuses
  and prints the worktree recipe. Unchanged.
- **The audit subagent cannot reach a verdict** (the profiles are inconclusive). It must be able to
  return "cannot determine" and that must NOT read as approval.
- **A run that is faster overall but slower on a seed.** Feature 128's exact shape - total -29.9%,
  seed 47 +30.7%. The per-seed bands still apply in full: that seed owes an explanation AND a
  confirmation, and being over 5% it owes the escalated audit too. Only the >10% GM sign-off is
  total-only, so feature 128 would NOT have needed the GM. Worth stating explicitly because the superseded constitution line said "a single seed
  never blocks a merge on its own", and a reader carrying that across would get this backwards.
- **The profiler itself perturbs the measurement.** The timing number and the profile must not come
  from the same run unless the profiler's overhead is small enough to be irrelevant - which is the
  whole reason route 1/2 above is preferred over route 3.
- **A machine under load.** See the noise floor above; this is why it was measured first.

## Requirements *(mandatory)*

- **FR-001**: Any measured increase above 0% - **on any individual seed OR on the total** - MUST
  require BOTH a written explanation AND a `perf-audit` subagent's confirmation of it before the work
  ships. Neither half alone satisfies the band (GM: *"any increase: explanation, with a subagent
  reviewer confirming"*). The per-seed noise floor may be CITED in an explanation; it is never a
  threshold below which nothing is owed.
- **FR-002**: An increase above 5% - **on any individual seed OR on the total**, the same scope as
  FR-001 - MUST require an ESCALATED audit that goes beyond FR-001's confirmation: the subagent
  independently adjudicates rather than confirming the session's account, and MUST NOT be satisfiable
  by the main session's own assertion in the ordinary path. A band-1 confirmation MUST NOT satisfy
  this band.
- **FR-003**: The audit MUST be based on before/after data that shows WHERE the time went - at
  minimum the per-stage breakdown - and never on the top-line number alone. The GM:
  *"the subagent can look at the before and after and have its independent verification and validation
  based on actual data."*
- **FR-003a**: At the >5% band, the audit record MUST address the GM's three criteria SEPARATELY and
  explicitly, and MUST be refused if any one of them is unaddressed. This is the "higher level of
  justification" the GM's ruling calls for, and it is what distinguishes band 2 from band 1's
  confirmation:
  1. **necessary** - the work causing the increase genuinely has to happen;
  2. **commensurate** - the cost is proportionate to the functionality gained;
  3. **no good way around it** - a cheaper implementation was considered and does not exist.

  These are the GM's own words (*"necessary and commensurate to the increase in functionaltiy and that
  there's no good way around this"*) and until this requirement they appeared in this document only as
  a block quote - specifying WHO audits and on WHAT DATA, but never what the verdict must decide.
- **FR-004**: A profile MUST be produced automatically as part of running the tooling, without the
  session having to remember to ask. The existing per-stage breakdown already satisfies this at tier
  1; anything further must be justified against what that breakdown cannot answer (FR-012a).
**A REVIEW RECORD means EITHER artifact** - the band-1 confirmation or the band-2 audit. The
requirements below deliberately name the pair rather than "the audit", because when review existed
only above 5% they said "audit" and the ruling has since put a reviewer on every increase. Left
unamended they would have exempted every band-1 confirmation from identity enforcement, commit
binding and logging - which would let a session self-issue the very check the ruling added.

- **FR-005**: A review record - confirmation or audit - MUST be bound to the commit and the specific measurements it covers,
  and MUST be refused when either has moved. This holds whether or not identity enforcement proves
  possible, and is the part a session cannot fake without writing a false statement into a logged,
  committed file.
- **FR-006**: The audit's verdict MUST be able to be NEGATIVE or INCONCLUSIVE, and neither may permit
  the work to proceed.
- **FR-007**: Every review record of either band, and every bypass of one, MUST be logged with who granted it, following the
  existing one-file-per-run convention in `dev/perf-log/` and `dev/bypass-log/` so concurrent clones
  never conflict.
- **FR-008**: The tooling MUST first determine whether a subagent's shell is distinguishable from the
  main session's, and MUST implement strict enforcement **for review records of BOTH bands** if it is. If it is not, the prompting fallback
  applies and the finding MUST be recorded so it is not re-investigated from scratch.
- **FR-009**: Above 10% on the total, no audit verdict is sufficient: **the GM signs off personally,
  and does so BEFORE the work is committed back to main.** The enforcement point is therefore the
  PUSH, not the gate - a `sync-with-main.sh` concern alongside the existing review gate, because a
  session can pass `make done` and only then discover it may not push. No longer pending: the GM ruled
  on 2026-08-24, and their ruling is sharper than the caution it replaces.
- **FR-009a**: The sign-off MUST be recorded in a form that is bound to the same commit and numbers as
  FR-005 requires of a review record, so a sign-off cannot be reused for a later, larger increase.
- **FR-009b**: `make done` MUST PRINT that a delta will need the GM's personal sign-off before it can
  be pushed, even though enforcement lives at the push. Costs nothing, and removes the surprise of
  passing the gate and only then being refused - the same reason every refusal in this project names
  the target that does the job.
- **FR-010**: Each guard added by this feature MUST ship with a test companion that proves it FIRES
  and that it does NOT fire on the legitimate path, and that companion MUST run in the gate
  (constitution XVIII).
- **FR-011**: Committed derived evidence MUST be bounded at kilobytes per audit event. (The earlier
  wording, "MUST NOT bloat the repository", could not be tested.)
- **FR-011a** (RECOMMENDATION, pending the GM's storage ruling - not a MUST): raw profile artifacts
  are gitignored rather than committed. The GM named three candidates - committing them, committing
  ZIPPED versions, or a second repository - and stating this as a requirement would foreclose the
  zipped option by fiat in a document that elsewhere calls the storage question the GM's to answer.
  See "The storage decision".
- **FR-012**: If a function-level profiler is adopted, its true overhead on the real `make perf`
  workload MUST be measured and recorded before the route is fixed. The figures in this document were
  measured on the check battery and on geometry helpers, which is not what `make perf` times.
- **FR-012a**: Before any new profiler is proposed, the implementation MUST determine in writing what
  the EXISTING per-stage timings cannot answer for the audit. A new profiling subsystem is justified
  only against that gap.

## The storage decision

The GM raised repository growth directly and leaned toward a second repository: *"maybe we have a
second repository of these. that we push to? ... that one seems like it might be good. because I'm
sensitive to how big this repository can get."*

**OPEN GM DECISION - not settled by this spec.** The GM leaned toward a second repository and asked
what the author thought; the author's recommendation is below, but the GM raised it, is available to
rule on it, and this document does not get to close a question they opened.

**The author's recommendation: NOT a second repository.** The reasoning, which is directly responsive
to the GM's stated concern - repository growth - rather than merely asserting the numbers are small:
**gitignoring the raw profiles removes the growth entirely**, because nothing large is ever committed
in the first place. What remains committed is kilobyte-scale derived evidence. The supporting detail:

- **The artifacts are small.** A `.prof` for a real run is on the order of hundreds of KB raw and tens
  of KB gzipped; a speedscope JSON is comparable. An audit event needs before+after across the seed
  set - on the order of 100 KB gzipped, on the rare occasions it happens.
- **Raw profiles are transient.** A raw profile from six months ago, against code that no longer
  exists, is nearly useless. The durable artifact is the DERIVED evidence - "this stage went from 4%
  to 19% of the build because X" - which stays true and is a few KB.
- **So: gitignore the raw profiles, commit the derived evidence table** the audit cites. The project
  already has this exact pattern: renders are gitignored and render-synced into main.
- **A second repository costs** authentication, another clone in the container, another sync step in
  the stop-work ritual, and a new way for two repositories to drift. That is a lot of moving parts for
  a problem measured in kilobytes.

**It becomes worth revisiting** if raw profiles ever need to be shared across machines - and even
then, the render-sync pattern is the cheaper precedent to copy.

### Scope Boundaries

**In scope**: the three bands; the profiling mechanism and its measured overhead; the `perf-audit`
subagent definition; the audit record format and its binding to commit + numbers; the identity
determination and whichever enforcement it permits; the storage split; the guard tests; the
constitution amendment.

**Out of scope**, so the reviewer can hold the author to it:

- **Making anything faster.** This feature measures and adjudicates; it does not optimize.
- **The CodeBuild merge gate** (a peer session's `specs/128-codebuild-merge-gate`). If remote runs
  change where perf is measured, that is a later integration, not this feature.
- **Extending any of this beyond the diagram generators.** The bookends are a generator rule.
- **The spec-number collision** between the two `specs/128-*` directories. Noted, deliberately not
  resolved here.

## Success Criteria *(mandatory)*

- **SC-001**: A 1% increase is refused without a written explanation, AND refused when the explanation
  exists but no subagent has confirmed it.
- **SC-002**: An increase over 5% is refused when only a band-1 confirmation exists - the escalated
  audit is a distinct artifact and a distinct bar.
- **SC-002a**: An increase over 10% on the total cannot be PUSHED without the GM's recorded sign-off,
  and the refusal happens at push time rather than only at gate time.
- **SC-003**: An audit record is refused once the commit or the audited numbers change.
- **SC-004**: A negative or inconclusive audit does not permit the work to proceed.
- **SC-005**: The profiler's overhead on the real `make perf` workload is measured and recorded, and
  the chosen route is justified against that number.
- **SC-006**: Deleting any guard this feature adds turns at least one test red, naming it.
- **SC-007**: The repository grows by kilobytes, not megabytes, per audit event.
- **SC-008**: The identity question is answered in writing, with the answer recorded whichever way it
  went.

## Assumptions

- The reference seed set stays [4, 25, 39, 47] unless the noise floor says otherwise.
- `dev/perf-log/` stays one-file-per-run, so concurrent clones never conflict.
- The 10% threshold, set by the GM 2026-08-24, is a **GM SIGN-OFF TRIGGER, not a ceiling** - they
  confirmed in the same message that *"there is no ceiling for allowing it to go forward so longer as
  the subagent reviewer agrees"*. "Cap" and "outer bound" are the vocabulary of the constitution rule
  this feature supersedes, where over-10% meant a Principle XIII regression with three exits. That
  mechanism is gone; do not carry its words forward.


## Review history

- **Round 1** - `CHANGES REQUIRED` (7 findings), all accepted and applied. The review was given the
  GM's request verbatim plus an explicit list of the author's own claims to attack.

  1. **The per-seed carve-out contradicted the GM's words.** The draft applied the >0% band to the
     TOTAL only and made the per-seed line "advisory below about 2%", justified by the measured 1.7%
     per-seed noise. The reviewer pointed out that the rule being REPLACED was itself per-seed, so
     this shrank the very surface the GM was changing, and that the draft contradicted itself - the
     bands table said the measurement was "left to implementation" while the noise section prescribed
     it. This is the strongest finding and the exact shape constitution XVI exists to stop: a measured
     fact used to narrow an instruction. The floor is now a caveat a diagnosis may CITE.
  2. **"Prose required only where the number is surprising" weakened FR-001 while denying it** - the
     constitution's own definition is that diagnosis means explained, not noticed, and a
     machine-written line is precisely noticed.
  3. **No requirement encoded what the audit must DECIDE.** The GM's three criteria - necessary,
     commensurate, no way around it - appeared only as a block quote. Now FR-003a.
  4. **The cProfile conclusion was asserted ahead of the measurement the same section demanded**, and
     the break-even counted the wrong trip rate: US1 wants a breakdown on the >0% band, which fires on
     most features, so profile demand approaches one per run and the arithmetic tilts toward always-on -
     the direction the GM's own reasoning pointed.
  5. **THE TOOLING ALREADY PROFILES.** Every `perf_snapshot` record carries a per-stage breakdown at
     zero overhead - seed 25 spends 62.6 s of 80.8 s in `web` - and the draft proposed a whole new
     profiling subsystem without mentioning it. It also ranked a container capability change first,
     which is a GM-facing change rather than an implementation detail. The spec is now built on a
     tiered design whose first tier is free, and the first implementation task is to establish what
     the existing timings CANNOT answer.
  6. **FR-011 was untestable** ("MUST NOT bloat the repository") and closed a question the GM had
     opened and leaned the other way on. Now a testable property plus an explicit open GM decision.
  7. **The >10% cap was presented as if it came from this request.** It did not; it is carried over
     and is in tension with "allow it to go forward". Now flagged for GM confirmation.

  The reviewer independently verified the noise table against the recorded snapshots (exact, nothing
  rounded in the author's favor) and confirmed the break-even arithmetic given its inputs.

- **Round 2** - `CHANGES REQUIRED` (2 findings), both accepted and applied. The reviewer verified all
  seven round-1 repairs in the BODY rather than trusting this history, and confirmed five were clean.

  1. **The instruction-narrowing survived in the two places implementation actually reads.** The
     noise-floor section had been fixed, but the BANDS TABLE still delegated "which number each band
     measures" to implementation, FR-001 did not name a measurement at all, and a hedge invited
     re-measurement to reopen the scope. The same shape as round 1's finding, one level down: the
     prose was right and the normative text was silent. Both now state per-seed OR total explicitly,
     and the hedge is narrowed to the floor's numbers rather than the band's scope.
  2. **FR-011 foreclosed one of the GM's three storage options by fiat** while the storage section
     declared the question open. The GM named committing, committing ZIPPED, and a second repository;
     a MUST against committing raw artifacts silently killed the zipped option. Split into a testable
     normative half and a recommendation pending the GM's ruling.

  The reviewer also confirmed the "an earlier draft said X" retractions are useful rather than
  clutter, that FR-003's rewording no longer contradicts the tier-1 design, and that the spec no
  longer rests on any of the author claims round 1 refuted.

- **Round 3** - **`FAITHFUL`**. Both round-2 repairs verified in the body, in all three places
  implementation reads. The reviewer independently confirmed against `constitution.md` that the
  spec's "because the GM set it that way" is factually accurate on both counts - the superseded rule
  really was per-seed (line 579) and the 10% cap really was on the total (line 584) - and that SC-007
  forecloses none of the GM's three storage options.

  It raised two non-blocking clarity notes, both applied rather than left: the Edge Cases bullet
  mentioned only the diagnose consequence of the per-seed band (now says it audits too, because a
  reader carrying the superseded "a single seed never blocks a merge" line across would get it
  backwards), and FR-002 inherited its scope from the bands section rather than restating it as
  FR-001 does.

  **Implementation may proceed on this spec** - subject to the two rulings it routes to the GM: the
  >10% cap (FR-009) and the storage question (FR-011a). Neither blocks anything but the shape of the
  work. **NOT STARTED, at the GM's explicit instruction.**

- **Post-round-3 REVISION, 2026-08-24** - the GM ruled on the two questions this spec routed to them,
  and the ruling revised the bands rather than merely answering them. The spec was reopened.

  **What changed**: a subagent now confirms EVERY increase, not only those above 5% - so 5% became
  the point where the analysis deepens and the justification bar rises, rather than the point where
  review begins. And the >10% row, which this spec had carried as the author's caution marked pending,
  is now the GM's own instruction and a sharper one: personal sign-off, **before the work is committed
  back to main**, which names the PUSH as the enforcement point rather than the gate.

  **What did not change**: the GM confirmed the reading that their earlier request had no ceiling
  (*"Yes it is correct that there is no ceiling for allowing it to go forward so longer as the
  subagent reviewer agrees"*) - and then chose to add one anyway on reflection. The distinction
  matters for anyone reading the history: the spec was right that the ceiling was absent, and the
  ceiling now exists because the GM put it there, not because the author kept it.

  The storage question (FR-011a) remains open and is untouched by this ruling.

- **Post-ruling review, round 1** - `CHANGES REQUIRED` (4 findings), all applied. Treated as a first
  review against CHANGED instructions rather than a fourth pass at the old ones, because the GM's
  ruling revised the bands.

  1. **Assumptions still called 10% a "cap" and an "outer bound"** - the vocabulary of the
     constitution rule this feature supersedes, where over-10% meant a Principle XIII regression with
     three exits. Under the ruling it is a SIGN-OFF TRIGGER and the GM confirmed there is no ceiling.
     Two mechanisms in one document.
  2. **The noise-floor section still described the any-increase band as diagnosis-only**, and said a
     cited noise floor "took a sentence, and it is on the record" - which under the ruling does not
     end the matter, because a subagent must confirm it. Self-contradiction sitting in the one section
     an implementer reads for thresholds.
  3. **The anti-self-grant machinery reached only "the audit".** FR-005, FR-007, FR-008 and US3 were
     all written when review existed only above 5%, so the band-1 confirmation - the one that fires on
     nearly every feature - fell outside identity enforcement, commit binding and logging. A session
     could have self-issued every confirmation and satisfied the letter of the requirements. **This is
     the third time in this document that prose was right while the normative text stayed silent**;
     the fix defines "review record" to mean either artifact.
  4. **The >10% band's TOTAL-only scope was attributed to the GM.** The record supports the GM
     choosing the NUMBER; the aggregate scope was the author's rationale, reasoned for a band that
     BLOCKED A MERGE, and the ruling changed that consequence. Relabeled as the author's
     carry-forward and routed to the GM as a second open question, with the concrete consequence
     stated: a single seed above 10% would not reach them.

  Also applied, from the reviewer's non-blocking aside: `make done` now owes a printed warning that a
  delta will need GM sign-off before push (FR-009b), so the gate does not pass work that the push will
  refuse.
