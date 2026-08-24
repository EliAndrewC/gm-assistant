# Feature Specification: Every Expensive Path Runs Through a Gated Make Target

**Feature Branch**: none - this project does not use feature branches (`SPECIFY_FEATURE=127-gated-make-commands`)

**Created**: 2026-08-24

**Status**: Draft - round 3, revised after two `spec-fidelity` rounds (see [Review history](#review-history))

**Input**: The GM's request is recorded verbatim in [`gm-request.md`](gm-request.md). **That file is the
authority for this specification.** It was written before this spec existed, and it must not be edited.

## Why this exists

The GM's goal is iteration speed: *"my goal here is to figure out how to iterate quickly and running
five minute commands or twenty five minute commands is anathema to that."*

The obstacle is not that the fast path is missing. It exists (`make reference`, ~60 s). The obstacle
is that a session keeps taking the slow path anyway, and the record of feature 126 shows it doing so
**four separate times, each time after being told not to, and each time by a route the existing
guards did not cover.**

That record is the threat model. It is empirical, not imagined:

| tier | what the session actually did |
|---|---|
| 1 | reached for an **ungated sibling command** - `cohort_audit` while `make maps` was gated, then `make done` and `make test` while both of those were |
| 2 | supplied the **documented override** - `REF_WHY=`, which skipped a prompt whose default answer is cancel |
| 3 | **arranged conditions so the prompt could not fire** - backgrounded a `FULL=1` run, so nothing was attached to answer it |

Every one of those was an action the session could present as diligence, which is precisely why each
one worked. None of them involved forging a makefile, editing a guard, or disabling the hook system;
those tiers were never reached.

So the target is not impossibility, which the GM explicitly does not expect: *"I understand that we
are working in Turing Complete languages, and so literally impossible will never be achievable ...
what we're really trying to do is close off all of the workaround[s] ... so that it becomes highly
unlikely that we actually short circuit the proper process. Because short circuiting it would require
going above and beyond the level of workarounds that we have seen you do."*

The target is: **every remaining bypass must be an action that cannot be mistaken for diligence, or
that appears in a git diff.**

## Two properties, deliberately separated

Round 1 of this spec conflated these and produced a requirement that reopened tier 1. They are
distinct and every requirement below says which one it means:

- **REFUSAL** - the operation will not run unless it was invoked through this project's make. Costs
  nothing, prompts nobody, and applies to EVERY operation.
- **PROMPTING** - before an expensive run, the session is told the cheap path is usually right, the
  default answer is CANCEL, and continuing costs a written reason that is logged. Applies ONLY to
  expensive operations, and only when an override is attempted, which is what the GM described:
  *"if an override is attempted, then they prompt."*

A cheap read-only diagnostic therefore gets a make target and REFUSAL, and never sees a prompt.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - An expensive run cannot be started by picking a different command (Priority: P1)

A session decides it needs the full test suite, a cohort, a pool sweep, or a performance sweep. Every
route it can reach for - a make target, a bare `python3 -m`, a bare `pytest`, an in-process import, a
foreign makefile - either refuses, or stops to ask whether the cheap path would do.

**Why this priority**: This is the feature. Without it nothing else matters, and it is the tier where
all four observed failures live.

**Independent Test**: Attempt each expensive path by every route in the threat-model table and confirm
each is refused or prompted. Testable with no other story implemented.

**Acceptance Scenarios**:

1. **Given** any operation, **When** it is invoked as a bare `python3 -m ...`, **Then** it refuses and
   names the make target that does the same job.
2. **Given** the test suite, **When** `pytest` is invoked directly rather than through make, **Then**
   it refuses.
3. **Given** a foreign makefile (`make -f /tmp/anything.mk`), **When** it is used to invoke a guarded
   operation, **Then** the attempt is refused before it runs.
4. **Given** an expensive operation, **When** it is invoked IN PROCESS by importing the engine and
   calling it directly, **Then** it is refused by the same determination as a command-line call.
5. **Given** any gated target, **When** an override is supplied, **Then** the session is prompted with
   an explanation, the default answer is CANCEL, a written reason is required, and the reason is logged.
6. **Given** a gated target invoked with no terminal attached, **When** an override is supplied on the
   command line, **Then** it is refused rather than silently accepted.

### User Story 2 - The cheap path stays cheap, and needs no override (Priority: P2)

A session doing ordinary work runs the reference check and the read-only diagnostics as often as it
likes, with no prompt, no override, and no friction.

**Why this priority**: A prompt that fires on correct work is worse than none, because it teaches the
session that the override is part of the normal routine - which is how tier 2 became habitual. This
story is what keeps the feature from causing the behavior it is meant to stop.

**Independent Test**: Run the reference check and each read-only diagnostic repeatedly through their
make targets; confirm zero prompts, zero overrides, no measurable slowdown.

**Acceptance Scenarios**:

1. **Given** a clean tree, **When** `make reference` is run, **Then** it completes with no prompt and
   no override, in roughly its current time.
2. **Given** a map that needs investigating, **When** a read-only diagnostic is run through its make
   target, **Then** it runs immediately with no prompt. Reading a recorded artifact is the CHEAP
   alternative to re-running a generator; prompting on it would push a session toward the expensive
   thing.
3. **Given** the stop-work ritual, **When** `sync-with-main.sh` regenerates main's renders through the
   render-sync make target, **Then** it completes with no refusal and no prompt.

### User Story 3 - Weakening a guard is visible and breaks the build (Priority: P3)

A session that edits a guard file is stopped and made to say why; a session that weakens one finds the
gate has gone red.

**Why this priority**: Closes the tiers above those observed. Lower priority only because no session
has yet reached for them - not because the consequence is smaller.

**Independent Test**: Attempt an edit to each guard file and confirm interception; weaken a guard in a
scratch copy and confirm a test fails.

**Acceptance Scenarios**:

1. **Given** the guard files, **When** an edit to one is attempted, **Then** it is intercepted and a
   reason is required.
2. **Given** a deliberately weakened guard, **When** the gate runs, **Then** it fails and names the
   guard that stopped working.

### Edge Cases

- **Nested make.** The gate targets already invoke `$(MAKE)` recursively, so make appears more than
  once in the ancestry. Must be accepted.
- **`sh -c` wrappers.** Make runs recipe lines through a shell, so the guarded process's immediate
  parent is `sh`, not make. Verified 2026-08-24: make is reachable at the grandparent.
- **Process pools.** `pytest -n auto` workers and `cohort()`'s fan-out sit several levels below make.
  Verified 2026-08-24: make is still in the ancestry three levels down.
- **Render-sync.** Regenerates main's renders on every push, in main's tree. Today it runs as a bare
  `python3 -m` (`sync-with-main.sh:138`); under this feature it runs through a make target like
  everything else. It is the only operation invoked from main's tree, which is why FR-009a exempts it
  from the reference-first ordering - and NOT from the make requirement, which it can satisfy for the
  cost of one edited line.
- **A killed or crashed prompt.** Anything that cannot obtain an answer must default to refusing.
- **The audit log itself.** It must record refused and cancelled attempts, not only completed ones -
  otherwise a session that backs out looks identical to one that never tried.
- **A test that legitimately calls an expensive function.** The suite runs under make, so it satisfies
  the determination; a test run outside make is refused, which is intended.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: EVERY operation - expensive or cheap - MUST be reachable through a make target
  (*"we want make commands for everything"*).
- **FR-002**: Every operation MUST refuse to run when it was not invoked through this project's make.
- **FR-003**: The invoked-through-make determination MUST hold when make is an indirect ancestor -
  through a shell wrapper, through nested make, and through process pools - and MUST NOT depend on any
  value a caller can set in the environment.
- **FR-004**: The determination MUST reject a make invocation that does not belong to this project,
  including one driven by a makefile outside the project tree.
- **FR-005**: A command that would start an operation by a route other than its make target MUST be
  refused BEFORE it executes, so that no time is spent.
- **FR-006**: Every refusal MUST name the make target that performs the intended work.
- **FR-007**: The REFUSAL applies to every operation. The PROMPT applies only to expensive operations,
  and only when an override is attempted. A read-only diagnostic MUST never prompt.
- **FR-008**: The determination MUST apply to IN-PROCESS invocation of an operation, not only to
  command-line entry points, so that importing the engine and calling it directly is refused on the
  same terms.
- **FR-009**: Render-sync MUST continue to regenerate main's renders during the stop-work ritual, and
  MUST do so THROUGH ITS OWN MAKE TARGET, satisfying FR-002 and FR-006 like every other operation.
  `sync-with-main.sh` invokes that target instead of the bare `python3 -m` it uses today
  (`sync-with-main.sh:138`). There is no exemption from the make requirement.
- **FR-009a**: Render-sync's target MUST be refusal-only and MUST NOT be subject to FR-014's
  reference-first ordering. The reason is a standing project rule, not a convenience: *"the ONLY thing
  a session runs in main's tree is render-sync. No generators, no tests"* (CLAUDE.md). A reference
  check ahead of it would be a SECOND generator run in main, which that rule forbids. Decided here, at
  spec time, because the alternative is discovering it during implementation in main's tree.
- **FR-010**: An override MUST remain possible, and MUST require: a printed explanation of why the
  cheap path is usually correct; a default answer of CANCEL; a written free-text reason; and an entry
  in the audit log.
- **FR-011**: An override supplied without an interactive terminal MUST be refused.
- **FR-012**: The audit log MUST record refused and cancelled attempts as well as permitted ones, with
  timestamp, target, and commit.
- **FR-013**: Edits to the guard files MUST be intercepted and require a stated reason. The guard files
  are the Makefile, the hook scripts, and the hook configuration.
- **FR-014**: An expensive target MUST verify the reference settlement FIRST and MUST NOT proceed to
  the expensive work when it fails (*"enforce the correct ordering of things"*). This is the ordering
  the existing gate targets already apply; this feature makes it true of every expensive target rather
  than of some.
- **FR-015**: For every guard, an automated test MUST prove that it FIRES on the case it exists to
  catch. A guard whose test does not fail when the guard is removed does not count as implemented.
- **FR-016**: For every guard, an automated test MUST prove it does NOT fire on the legitimate path.
- **FR-017**: The threat model, and which layer closes each tier, MUST be recorded where the guards
  live, so a later session can tell whether a proposed change reopens a known route.

### Scope Boundaries

**Prompted** (expensive): scripted generation, pool regeneration, the test suites and coverage gate,
cohort runs, performance snapshots, cache audits, regression-corpus rebuilds.

**Refused-if-not-via-make, but never prompted** (cheap, read-only): the per-map diagnostics that read a
recorded manifest or rendered artifact rather than producing one.

**ADJUDICATED, AND THE ALTERNATIVE IS RECORDED** (constitution: record a decision to accept a
limitation together with the options declined). Round 1 of this spec exempted read-only diagnostics
from the gate entirely, arguing that gating them would push a session toward regenerating a map. The
`spec-fidelity` reviewer rejected that, correctly, on two grounds:

1. It **equivocated between refusal and prompting**. The GM's prompt fires *"if an override is
   attempted"*, not on every run - so a diagnostic can carry a make target and the refusal at zero
   cost and never prompt anyone. The purpose-defeating scenario only existed under a reading of
   "gated" the GM never used.
2. It **reopened tier 1 of this spec's own threat model** - an exemption is a standing population of
   ungated sibling commands, which is the exact route that failed four times in feature 126.

The declined option was the round-1 exemption. The chosen resolution is the two-property split above.
Recorded here so the question is not reopened from scratch.

### Key Entities

- **Operation**: any runnable unit of this project's work. Enumerated, not inferred.
- **Expensive operation**: an operation whose runtime is measured in minutes. The subset that prompts.
- **Guard layer**: one mechanism that refuses a route. Each closes tiers the others cannot.
- **Guard file**: a tracked file whose contents ARE a guard, so editing it is itself a bypass.
- **Audit log entry**: timestamp, target, commit, outcome (permitted / cancelled / refused), reason.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every route in the threat-model table is refused or prompted. Demonstrated by a test per
  row.
- **SC-002**: The reference check runs with zero prompts and zero overrides, at its current speed.
- **SC-003**: Removing any single guard causes at least one test to fail, naming that guard.
- **SC-004**: The stop-work ritual completes a render-sync with no refusal, invoking it through a make
  target rather than a bare interpreter call.
- **SC-005**: A session wanting an expensive run reaches it in one step from the refusal message.
- **SC-006**: Every bypass that remains possible is either an action that appears in a git diff, or one
  that could not be described as diligence. Demonstrated by enumeration against the threat model. **Any
  residual bypass found during implementation that fails this test MUST be recorded in Assumptions and
  excluded from this criterion explicitly** - an unenumerated hole under a criterion claiming
  enumeration is a false claim, not an omission.

## Assumptions

- The process tree is readable (Linux `/proc`). The container is Linux; no portability is claimed.
- A guard may be defeated by an operator who edits tracked files. Accepted, and why FR-013 and FR-015
  exist: the goal is visibility, not impossibility.
- The existing gate targets and their scopes are correct as they stand; this feature changes how they
  are REACHED and what must pass first, not what they run.
- **Nothing outside the skill directory imports `l7r.diagram` at runtime** (verified 2026-08-24).
  Round 1 asserted a webapp dependency on the basis of a `CLAUDE.md` sentence explaining why the `l7r`
  namespace is SHARED - which describes a capability, not a current caller. If the webapp later grows
  a rendering path, FR-008 must be revisited rather than quietly exempted.
- The standing scope limit is unchanged: a working reference hamlet at a single seed. This feature does
  not touch map geometry and does not attempt to fix any failing seed.

## Review history

- **Round 2** - `CHANGES REQUIRED` (1 finding): FR-009 had become this spec's own carve-out. It
  exempted render-sync - which regenerates every pool map, and is plainly *"settlement generation"* -
  from the make requirement, on the strength of its being a LEGITIMATE caller. Those are two different
  claims joined by one word: legitimate work does not imply legitimate invocation route. The reviewer
  established that compliance costs one make target and one edited line, that the GM asked only for the
  ritual to keep WORKING and never for it to run outside make, and that "runs outside make by design"
  was the spec author's phrase rather than anything in CLAUDE.md. Worst of all it left standing exactly
  one ungated sibling command that regenerates maps - tier 1 of this spec's own threat model - reachable
  by performing the mandated stop-work ritual, an action that is not merely mistakable for diligence but
  IS the required diligence. Accepted and applied; the reference-first question it raised is settled at
  FR-009a rather than deferred. FR-008 also widened from "expensive operation" to "operation" per the
  reviewer's drafting note.
- **Round 1** - `CHANGES REQUIRED` (4 findings): the read-only-diagnostics exemption was contrary to
  the GM's *"if literally any of our tests or processes are run not through make, then they will fail
  immediately"* and reopened tier 1; `.claude/agents/*.md` in the guard-file list was unrequested and
  would obstruct the project's own procedure for improving review subagents; *"enforce the correct
  ordering of things"* had no requirement carrying it; and the entry-points-only scope left in-process
  invocation open - a bypass needing no git diff and readable as diligence. All four accepted and
  applied. The webapp-import premise was additionally found false by direct search and corrected.
