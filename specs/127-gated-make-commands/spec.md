# Feature Specification: Every Expensive Path Runs Through a Gated Make Target

**Feature Branch**: none - this project does not use feature branches (`SPECIFY_FEATURE=127-gated-make-commands`)

**Created**: 2026-08-24

**Status**: Draft

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

## User Scenarios & Testing *(mandatory)*

### User Story 1 - An expensive run cannot be started by picking a different command (Priority: P1)

A session decides it needs the full test suite, a cohort, a pool sweep, or a performance sweep. Every
route it can reach for - a make target, a bare `python3 -m`, a bare `pytest`, a foreign makefile -
either refuses, or stops to ask whether the cheap path would do.

**Why this priority**: This is the feature. Without it nothing else matters, and it is the tier where
all four observed failures live.

**Independent Test**: Attempt each expensive path by every route in the threat-model table and confirm
each is refused or gated. This is testable with no other story implemented.

**Acceptance Scenarios**:

1. **Given** the expensive entry points, **When** one is invoked as a bare `python3 -m ...`, **Then**
   it refuses and names the make target that does the same job.
2. **Given** the test suite, **When** `pytest` is invoked directly rather than through make, **Then**
   it refuses.
3. **Given** a foreign makefile (`make -f /tmp/anything.mk`), **When** it is used to invoke a guarded
   entry point, **Then** the attempt is refused before it runs.
4. **Given** any gated target, **When** an override is supplied, **Then** the session is prompted with
   an explanation, the default answer is to CANCEL, a written reason is required to continue, and the
   reason is logged for later audit.
5. **Given** a gated target invoked with no terminal attached, **When** an override is supplied on the
   command line, **Then** it is refused rather than silently accepted.

### User Story 2 - The cheap path stays cheap, and needs no bypass (Priority: P2)

A session doing ordinary work runs the reference check and the read-only diagnostics as often as it
likes, with no prompt, no override, and no friction.

**Why this priority**: A gate that fires on correct work is worse than no gate, because it teaches the
session that the override is part of the normal routine - which is how tier 2 of the threat model
became habitual. This story is what keeps the feature from causing the behavior it is meant to stop.

**Independent Test**: Run the reference check and each read-only diagnostic repeatedly; confirm zero
prompts, zero overrides, and no measurable slowdown.

**Acceptance Scenarios**:

1. **Given** a clean tree, **When** `make reference` is run, **Then** it completes with no prompt and
   no bypass, in roughly its current time.
2. **Given** a map that needs investigating, **When** a read-only diagnostic is run, **Then** it runs
   without a gate. Reading a recorded artifact is the CHEAP alternative to re-running a generator, and
   gating it would push a session toward the expensive thing.
3. **Given** the L7R Toolkit webapp, **When** it renders a map, **Then** nothing refuses, because the
   webapp imports the engine as a library and is not under make.
4. **Given** the stop-work ritual, **When** `sync-with-main.sh` regenerates main's renders, **Then** it
   completes, because render-sync runs outside make by design.

### User Story 3 - Weakening a guard is visible and breaks the build (Priority: P3)

A session that edits a guard file is stopped and made to say why; a session that weakens one finds the
gate has gone red.

**Why this priority**: Closes the tiers above those observed. Lower priority only because no session
has yet reached for them - not because the consequence is smaller.

**Independent Test**: Attempt an edit to each guard file and confirm it is intercepted; weaken a guard
in a scratch copy and confirm a test fails.

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
- **Library import.** The engine is imported by the webapp and by tests. A guard in library code breaks
  both; it belongs on entry points only.
- **Render-sync.** Runs generation in main's tree, outside make, on every push.
- **A killed or crashed prompt.** Anything that cannot obtain an answer must default to refusing, never
  to proceeding.
- **The audit log itself.** It must record refused and cancelled attempts, not only completed ones -
  otherwise a session that backs out looks identical to one that never tried.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every expensive operation MUST be reachable through a make target. Expensive means:
  settlement generation, the gate and test suites, cohorts, pool regeneration, and performance
  measurement.
- **FR-002**: Every expensive operation MUST refuse to run when it was not invoked through make.
- **FR-003**: The invoked-through-make determination MUST hold when make is an indirect ancestor -
  through a shell wrapper, through nested make, and through process pools - and MUST NOT depend on any
  value a caller can set in the environment.
- **FR-004**: The determination MUST reject a make invocation that does not belong to this project,
  including one driven by a makefile outside the project tree.
- **FR-005**: A command that would start an expensive operation by a route other than a gated make
  target MUST be refused BEFORE it executes, so that no time is spent.
- **FR-006**: Every refusal MUST name the make target that performs the intended work, so the correct
  route is always one line away.
- **FR-007**: Read-only diagnostics MUST NOT be gated (see Scope Boundaries).
- **FR-008**: Library import of the engine MUST NOT be gated. The webapp MUST continue to render maps.
- **FR-009**: Render-sync MUST continue to regenerate main's renders during the stop-work ritual.
- **FR-010**: An override MUST remain possible, and MUST require: a printed explanation of why the
  cheap path is usually correct; a default answer of CANCEL; a written free-text reason; and an entry
  in the audit log.
- **FR-011**: An override supplied without an interactive terminal MUST be refused.
- **FR-012**: The audit log MUST record refused and cancelled attempts as well as permitted ones, with
  timestamp, target, and commit.
- **FR-013**: Edits to the guard files MUST be intercepted and require a stated reason. The guard files
  are the Makefile, the hook scripts, the hook configuration, and the agent definitions.
- **FR-014**: For every guard, an automated test MUST prove that it FIRES on the case it exists to
  catch. A guard whose test does not fail when the guard is removed does not count as implemented.
- **FR-015**: For every guard, an automated test MUST prove it does NOT fire on the legitimate path.
- **FR-016**: The threat model, and which layer closes each tier, MUST be recorded where the guards
  live, so a later session can tell whether a proposed change reopens a known route.

### Scope Boundaries

**Gated** (expensive): scripted generation, pool regeneration, the test suites and coverage gate,
cohort runs, performance snapshots, cache audits, regression-corpus rebuilds.

**Given a make target but NOT gated** (cheap, read-only): the per-map diagnostics that read a recorded
manifest or a rendered artifact rather than producing one.

**A NOTE FOR THE FIDELITY REVIEWER.** This boundary is the one judgment call in this specification and
it is deliberately surfaced rather than buried. The GM's words are *"essentially everything about our
settlement generation, our automated checks, our performance measurements, all of it"* - three named
categories, none of which is a read-only diagnostic. The reasoning for excluding them is that they are
the CHEAP alternative to the expensive thing: the diagram doctrine is *"read derived data from the
recorded artifact, not by re-running the generator"*, so gating a manifest reader would push a session
toward regenerating a map, which is the opposite of this feature's purpose. **If the reviewer judges
this an unrequested carve-out, the correct resolution is to gate them too**, and the feature is no
worse for it.

### Key Entities

- **Expensive operation**: work whose runtime is measured in minutes. Enumerated, not inferred.
- **Guard layer**: one mechanism that refuses a route. Four exist; each closes tiers the others cannot.
- **Guard file**: a tracked file whose contents ARE a guard, so editing it is itself a bypass.
- **Audit log entry**: timestamp, target, commit, outcome (permitted / cancelled / refused), reason.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every route in the threat-model table is refused or gated. Demonstrated by a test per row.
- **SC-002**: The reference check runs with zero prompts and zero overrides, at its current speed.
- **SC-003**: Removing any single guard causes at least one test to fail, naming that guard.
- **SC-004**: The webapp renders a map, and the stop-work ritual completes a render-sync, with no
  refusal.
- **SC-005**: A session wanting an expensive run reaches it in one step from the refusal message,
  because the refusal names the target.
- **SC-006**: Every bypass that remains possible is either an action that appears in a git diff, or one
  that could not be described as diligence. Demonstrated by enumeration against the threat model.

## Assumptions

- The process tree is readable (Linux `/proc`). The container is Linux; no portability is claimed.
- A guard may be defeated by an operator who edits tracked files. This is accepted and is why FR-013
  and FR-014 exist: the goal is visibility, not impossibility.
- The existing gate targets and their scopes are correct as they stand; this feature changes how they
  are REACHED, not what they run.
- The standing scope limit is unchanged: a working reference hamlet at a single seed. This feature does
  not touch map geometry and does not attempt to fix any failing seed.
