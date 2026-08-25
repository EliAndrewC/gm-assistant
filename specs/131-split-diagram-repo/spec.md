# Feature Specification: The Diagram Skill Becomes Its Own Repository

**Feature Branch**: none - this project does not use feature branches (`SPECIFY_FEATURE=131-split-diagram-repo`)

**Created**: 2026-08-24

**Status**: APPROVED by `spec-fidelity` (round 3, verdict FAITHFUL). **Specified and planned; implementation waits
for the GM's "go"** - the same standing as feature 130, whose implementation this feature must
precede.

**Input**: The GM's request is recorded verbatim in [`gm-request.md`](gm-request.md). That file is
the authority. **Blocks**: `129-perf-audit-subagent` and `130-codebuild-merge-gate` - FR-005 puts a `Blocked by:
131` line in each spec header (done alongside this spec) and a `T000` verify-the-blocker task at the
top of each `tasks.md` (130 has one; 129 has no `tasks.md` yet, so its `T000` is written when its
tasks are generated).

## Why this exists

The GM's words: *"It has grown into a project into its own right, and the fact that we are now
having to do so much work in order to just distinguish the diagram skill from other parts of the
repository with completely different rules suggests to me that it should become its own repo."*

The evidence is on the record. Feature 127's guards are every one scoped to
`.claude/skills/diagram`. Feature 130 spends an engine-path list, a route derived from "is this
delta diagram code", a `gate-stamp` area table, and a whole second push route on the single job of
keeping the diagram's CI away from the rest of the repository. The skill already has its own
Makefile, `pyproject.toml`, test suite, coverage policy, dev-loop docs, migration plan, timing
ledger, three append-only logs, and 46 of the repository's 51 spec-kit features. The rules the GM
wants for it - spec-kit mandatory for any change, everything through make, CodeBuild as the merge
gate - are rules for a repository, and the content skills and the webapp should not carry them.

## What "split" means here - the decisions, and the ones flagged as the session's

1. **A new GitHub repository holds the diagram project with its history.** The diagram directory,
   its spec-kit features, and the repository-level machinery it depends on are extracted with
   history preserved (every commit that touched them survives, with its date, author and message).
   gm-assistant keeps its own history untouched; the extracted material is then removed from
   gm-assistant in an ordinary commit.
2. **The internal layout is IDENTICAL.** In the new repository the skill still lives at
   `.claude/skills/diagram/`, so it remains a Claude Code skill invoked as `/diagram`, and nothing
   in the engine (`SKILL = dirname(dirname(HERE))` bootstraps in every pool generator), the
   feature-127 guards (`make-only-hooks.sh`, `guard-file-hooks.sh`, `_invocation.py`), the
   Makefile, or a thousand commits of path comments changes. *Declined*: promoting the skill to the
   repository root - it would rewrite every one of those and buy nothing but a shorter path.
3. **The repository-level machinery goes to BOTH repositories, item by item, and nothing
   gm-assistant's remaining content uses is removed from it.** (Session's call - the GM was asked
   and had not answered.) The disposition per item is the table under FR-001. In short: the
   diagram-only guards MOVE; everything the content skills, the webapp, spec-kit or the container
   need is COPIED TO BOTH; the constitution, the spec-kit scripts and templates, `docs/l7r-style.md`,
   `docs/session-clones.md`, `docs/spec-kit-and-reviews.md`, `container-scripts/`, and the root
   `ruff.toml` fence are all in that second group. *Why copies, not a shared package*: the two
   projects' rules are diverging on purpose, and a shared package would re-couple them the day one
   needed a rule the other did not.
4. **The renders move with the repository.** (Session's call.) The GM browses renders in the
   diagram project's `main`; there is no reason for them to live anywhere else.
5. **Both repositories keep the constitution as it stands at extraction**, and diverge from there.
   The diagram repository is the one most of its principles were written for; gm-assistant keeps it
   because nothing in it is wrong for the content skills, and trimming is a later, deliberate act.
6. **The `l7r` namespace stays; the cross-tree import it enabled becomes moot.** (Session's call -
   the GM said nothing about feature 119.) Feature 119 made `l7r` a PEP 420 namespace portion so the
   webapp *could* import `l7r.diagram`. Nothing does (verified 2026-08-24 for feature 127). After
   the split the two portions are never on one `sys.path`; each repository's guard test stays true
   and nothing changes. If the webapp ever needs to render a map, it installs the diagram engine as
   a package - recorded in the LIVE docstring of `webapp/l7r/app.py` and the new CLAUDE.md, never by
   editing feature 119's dated spec.
7. **The CodeBuild infrastructure repoints, it is not rebuilt.** The two projects, the IAM user, the
   bucket, the budgets and alarms (2026-08-24) carry over; the GitHub token and the `main` ruleset
   are per-repository and must be created for the new one by the GM.
8. **Sequencing**: after the in-flight hamlet features land and before 129 or 130 are implemented.
   The GM chooses the moment; the feature itself lists what "quiet" has to mean (no other session
   with an unpushed diagram clone).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A session works on the diagram project in its own repository (Priority: P1)

A session opens the new repository, creates its clone under `.clones/`, syncs in, edits the engine,
runs `make reference`, `make quick`, `make done`, and ships through the stop-work ritual - exactly
as it did in gm-assistant, with every guard, hook, log and gate behaving identically.

**Why this priority**: This is the split. If the working loop is not identical, the split cost
something the GM did not ask to pay.

**Independent Test**: In the new repository, run `make done` and `make hooks-test`: green, same
counts as the last green gate in gm-assistant. Run each feature-127 refusal case from its
quickstart: refused, same messages.

**Acceptance Scenarios**:

1. **Given** the new repository at its first commit, **When** `make done` runs in a clone, **Then**
   it is green with the same test count and the same wall-clock as the last gm-assistant gate.
2. **Given** the new repository, **When** `git log --follow` is run on any engine file, **Then** its
   full history from gm-assistant is present.
3. **Given** a session in the new repository, **When** it runs the stop-work ritual, **Then** the
   ritual, the clone-sync hooks, gate-stamp, review-gate and render-sync all work unchanged.
4. **Given** the new repository, **When** the GM opens its `main`, **Then** the renders are there
   and `render-sync` regenerates them.
5. **Given** a `/diagram` invocation in a session on the new repository, **When** it runs, **Then**
   the skill loads from `.claude/skills/diagram/SKILL.md` as before.

---

### User Story 2 - gm-assistant keeps working for everything that is not the diagram (Priority: P1)

A session in gm-assistant generates an NPC, edits a wiki page, runs the webapp's `make done`, and
ships through the ritual. Nothing it uses has gone; nothing diagram-specific fires.

**Acceptance Scenarios**:

1. **Given** gm-assistant after the removal commit, **When** `webapp/make done` runs, **Then** it is
   green.
2. **Given** gm-assistant, **When** a session edits a content skill and ships, **Then** the
   clone-sync, house-style, source-block, readme and repo-safety hooks fire as before and the
   diagram-only hooks are absent (not present-and-broken).
3. **Given** gm-assistant's CLAUDE.md, **When** read, **Then** it no longer describes the diagram
   loop, points at the new repository for it, and its skills table lists `/diagram` as "moved".
4. **Given** the 5 non-diagram spec-kit features, **When** listed, **Then** they are still in
   gm-assistant's `specs/` with their numbers, and the 46 diagram ones are in the new repository's.

---

### User Story 3 - The two dependent features know they are blocked, and tooling can tell (Priority: P2)

Features 129 and 130 each carry a `Blocked by: 131-split-diagram-repo` line and a first task that
checks the split landed. A session that starts implementing either in gm-assistant is told to go to
the new repository.

**Acceptance Scenarios**:

1. **Given** `specs/129-*/spec.md` and `specs/130-*/spec.md`, **When** read, **Then** each has the
   `Blocked by` line in its header and a `T000` verify-the-blocker task.
2. **Given** a session in gm-assistant, **When** it sets `SPECIFY_FEATURE=130-...` after the split,
   **Then** the feature directory is not there - it moved - and the message says where.

---

### User Story 4 - Everything that pointed at the old location now points at the new one (Priority: P2)

Memory notes, CLAUDE.md files, the container launch, the CodeBuild projects, and the GitHub
token/ruleset all reference the new repository; no path or URL still says the diagram lives in
gm-assistant.

**Acceptance Scenarios**:

1. **Given** the container launch script, **When** run, **Then** both repositories are mounted (or
   the new one is, with the mount documented) and `setup-dev-env.sh --check` passes in each.
2. **Given** the session memory directory for the new repository's path, **When** a session starts
   there, **Then** the diagram-relevant notes are present (copied, with their index).
3. **Given** the CodeBuild projects, **When** inspected, **Then** `GITHUB_REPO` names the new
   repository and the secret holds a token scoped to it.
4. **Given** a grep for `gm-assistant/.claude/skills/diagram` across both repositories and the
   memory directory, **When** run after the sweep, **Then** it finds only historical records (spec
   review histories, logs) and no live instruction.

---

### Edge Cases

- **A session mid-feature in gm-assistant's diagram directory when the split lands.** Its clone's
  work is not lost - it is in gm-assistant's history - but it cannot push to the moved directory.
  The feature lists the migration: push the clone's diagram commits to a branch, `filter-repo` them
  the same way, and land them in the new repository. Better: the GM sequences the split for a
  moment with no such session (decision 8).
- **Shared-history size.** The diagram history is ~1,100 commits of a 277 MB `.git`; renders are
  gitignored so most of the bulk is pool manifests and stage plates. Extraction keeps only paths
  that move, so the new repository is smaller than gm-assistant, not larger.
- **Two constitutions, one `/speckit-constitution` skill.** Each repository amends its own; the
  version numbers diverge after 1.15.0 and that is expected.
- **The memory directory is keyed by project path.** A new path gets an empty memory; the
  diagram notes (32 files) are copied, not moved - gm-assistant sessions still need some of them
  (the NPC/portrait notes reference nothing diagram; the split notes reference both).
- **Cross-references from the diagram research to `/setting/` and `/cosmology/`.** They become
  GitHub URLs into gm-assistant per the no-local-paths rule; the research itself moves.
- **The `/diagram` skill's `SKILL.md` frontmatter** is what makes it a slash command; it is
  unchanged because the path is unchanged.

## Requirements *(mandatory)*

- **FR-001**: A new GitHub repository MUST contain, with the full commit history of every file:

  | item | disposition |
  |---|---|
  | `.claude/skills/diagram/` (same path) | MOVE |
  | the 46 diagram spec-kit directories, and `131-split-diagram-repo` itself | MOVE |
  | `scripts/`: `make-only-hooks.sh`, `_hookmatch.py` + `test-make-only-hooks.sh` | MOVE (session's call: its engine-entry-point and `REF_WHY` clauses are diagram-scoped and are why it exists; its bare-pytest, `make -f` and shell-redirect guard-write patterns are repository-wide, so gm-assistant loses the SHELL route to guard files while `guard-file-hooks.sh` keeps the Edit/Write route guarded) |
  | `scripts/`: `gate-hooks.sh`, `guard-file-hooks.sh`, `review-gate.sh`, `gate-stamp.py` + companions | COPY TO BOTH, each trimmed to its repository's areas: gm-assistant's `gate-stamp.py` keeps only the `webapp` area and the new repository's only `diagram`; `review-gate.sh`'s pool-manifest clause is diagram-only, its FAITHFUL-verdict clause is both; `guard-file-hooks.sh`'s diagram-Makefile pattern is diagram-only, its `scripts/*-hooks.sh` and `settings.json` patterns are both; `gate-hooks.sh` guards any `make done`, including the webapp's |
  | `scripts/`: `clone-sync`, `house-style`, `source-block`, `readme`, `repo-safety`, `no-branch`, `no-poll`, `batching` hooks + companions, `sync-with-main.sh`, `check-duplicate-defs.py`, `uncovered-in-diff.py` (both Makefiles call it), `launch-container.sh` | COPY TO BOTH |
  | `.claude/settings.json` | REWRITTEN in each: hook wiring trimmed to that repository's guards, the 13 absolute `/gm-assistant/scripts/...` paths repointed |
  | `.claude/agents/`: `building-review.md`, `settlement-review.md`, `size-audit.md` | MOVE |
  | `.claude/agents/`: `backstory-review.md`, `frontend-review.md` | STAY |
  | `.claude/agents/spec-fidelity.md` | COPY TO BOTH |
  | `.specify/` - the constitution, scripts, templates, extensions | COPY TO BOTH |
  | `docs/iteration-loop.md`, `docs/container.md` | COPY TO BOTH (each trimmed to its repository's loop) |
  | `docs/session-clones.md`, `docs/spec-kit-and-reviews.md`, `docs/l7r-style.md` | COPY TO BOTH (`l7r-style.md` is content-side; the diagram research quotes it) |
  | `container-scripts/` (`setup-dev-env.sh`, `append-system-prompt.md`) | COPY TO BOTH |
  | root `ruff.toml` (the fence its header describes) | COPY TO BOTH |
  | `CLAUDE.md` | REWRITTEN in each |
  | the 5 non-diagram spec-kit directories, `webapp/`, the content skills, `setting/`, `cosmology/`, `campaigns/`, `hooks/`, `notes/`, `weather/` | STAY |

- **FR-002**: gm-assistant MUST have the MOVE items removed in one ordinary commit that names the
  new repository, and MUST keep every COPY and STAY item working: `webapp/make done` green, the
  retained hooks wired and firing, spec-kit runnable for its own features, the constitution in
  place. **gm-assistant's retained guards MUST still be RUN** (constitution XVIII): the `hooks-test`
  target that today lives only in the diagram Makefile is copied into `webapp/Makefile` as a phase
  of its `make done`, so a copied guard whose companion breaks turns gm-assistant's gate red exactly
  as it does the diagram's.
- **FR-003**: The working loop in the new repository MUST be identical: the same make targets, the
  same guards, the same hooks wired in `.claude/settings.json`, the same `make done` count, the same
  stop-work ritual, the same render-sync into the repository's `main`.
- **FR-004**: The five non-diagram spec-kit features MUST stay in gm-assistant; the 46 diagram ones
  and this feature's own directory MUST move, keeping their numbers. How numbering continues is the
  session's call, flagged in Assumptions.
- **FR-005**: Features 129 and 130 MUST carry `Blocked by: 131-split-diagram-repo` in their spec
  headers (added alongside this spec) and a `T000` task verifying the split landed at the top of
  their `tasks.md` - 130's now, 129's when its tasks are generated - and MUST move to the new
  repository with everything else.
- **FR-006**: Every live reference to the old location - `.claude/settings.json` (13 absolute hook
  paths), CLAUDE.md in both repositories, `docs/session-clones.md`, `docs/container.md`, `scripts/launch-container.sh`, the container
  system-prompt file, the session memory notes and their index, the CodeBuild projects' variables,
  the diagram research's references into gm-assistant's setting files - MUST be updated. Historical
  records (spec review histories, run logs, commit messages) are left as they are.
- **FR-007**: The CodeBuild projects MUST be repointed at the new repository; the GitHub token and
  `main` ruleset MUST be created for it (GM actions, listed as such). Feature 130's whole flow -
  GitHub `main` as the integration point, the mirror, the routes - then belongs to the new
  repository; gm-assistant keeps its current local-main ritual unchanged. Revoking the old token is
  housekeeping the GM may do; it is not required here.
- **FR-008**: Both repositories MUST start from the constitution AS IT STANDS at extraction,
  unchanged in either (it is already past 1.15.0 in a peer feature's citation; the number is not
  pinned here).
- **FR-009**: The `l7r` namespace portion MUST remain valid in each repository (each guard test
  stays). The post-split coupling (a package dependency, if ever) is recorded in the live
  docstring of `webapp/l7r/app.py` and the new repository's CLAUDE.md; feature 119's spec is a
  dated record and is not edited (FR-006).
- **FR-010**: The memory directory for the new repository's path MUST receive copies of the
  diagram-relevant notes and an index; gm-assistant's memory MUST gain a note saying where the
  diagram went.
- **FR-011** (session's call, see Assumptions): The split MUST be rehearsed on a throwaway copy first and verified end to end (US1,
  US2) before the real extraction, because the real one is the one step here that is hard to walk
  back once other sessions have started from it.
- **FR-012**: Nothing in the engine, the pool, or the gate changes. No map geometry changes.

### Scope Boundaries

**Out of scope**: promoting the skill to the repository root; a shared package for the hooks;
trimming either constitution; installing the diagram engine into the webapp; any change to
feature 129's or 130's content beyond the `Blocked by` line and the T000 task; migrating the
`l7r` setting notes (they stay in the GM's `l7r` repo, unaffected).

### Key Entities

- **Moved set**: the paths extracted with history (FR-001).
- **Retained copies**: the scripts gm-assistant keeps (FR-002).
- **Reference sweep**: every live pointer at the old location (FR-006).
- **Blocked-by line**: the header convention that stands in for a spec-kit dependency mechanism,
  which spec-kit does not have.

## Success Criteria *(mandatory)*

- **SC-001**: `make done` in the new repository is green with the same test count as the last green
  gate in gm-assistant, and `make hooks-test` reports the same number of guard suites.
- **SC-002**: `git log --follow` on ten randomly chosen engine files shows their full history.
- **SC-003**: `webapp/make done` in gm-assistant is green, its `hooks-test` phase reports every
  retained guard suite green, and no diagram-only hook is wired there.
- **SC-004**: The reference sweep grep (US4 #4) finds zero live instructions pointing at the old
  location.
- **SC-005**: A feature-127 quickstart pass in the new repository reproduces every refusal.
- **SC-006**: The rehearsal (FR-011) passed all of the above before the real extraction ran.

## Assumptions

- **Repository name**: `EliAndrewC/l7r-diagram` (session's guess, from the GM's `l7r` and
  `gm-assistant` naming; a one-word change if the GM prefers otherwise).
- **Copies, not a shared package** (decision 3) and **renders move** (decision 4) are the session's
  calls on two questions the GM was asked and had not yet answered; both are cheap to reverse.
- **"Quiet point"**: no session holds an unpushed clone with diagram changes. The GM knows the
  sessions; the task list asks them to confirm before the real extraction.
- **The GM creates the repository, the token, and the ruleset**; the session does the extraction,
  the sweep, the CodeBuild repoint and the verification.
- **Numbering after the split (session's call, GM to confirm at "go")**: the diagram repository
  continues from 132; gm-assistant restarts at **200**, so every "feature NNN" in memory notes,
  review histories and logs stays globally unique and the claim-in-main protocol keeps working
  unchanged in each repository. *Declined*: both continuing from 132 (overlapping numbers make every
  existing cross-reference ambiguous the day it happens).
- **The rehearsal (FR-011) is the session's call.** The GM did not ask for it. Its narrower
  rationale: gm-assistant's history is untouched and the removal commit is revertible, so the only
  one-way step is other sessions starting from the new repository - and a rehearsal on a throwaway
  is the cheapest way to make sure the path list is complete before that moment. Drop it if the GM
  prefers; the ordering (extract and verify before removal, before telling anyone) stays either way.
- **Spec-kit has no dependency mechanism.** The `Blocked by` header line plus a verify task is the
  convention this feature establishes; it is checkable by tooling later if wanted.

## Review history

- **Round 1** - `CHANGES REQUIRED` (5 findings). (1) FR-001/FR-002 moved `.specify/`, `docs/`,
  `container-scripts/` and `ruff.toml` out of gm-assistant as originals - stripping its
  constitution, spec-kit scripts, style guide and review pre-authorization - while US2 claimed
  nothing it uses had gone; replaced by a per-item MOVE / COPY TO BOTH / STAY table, and FR-008's
  stale version pin dropped. (2) FR-009 required editing feature 119's dated spec, against FR-006
  and the project's own rule; now the live docstring and CLAUDE.md carry it, and decision 6's
  heading ("retired") matched neither - retitled and flagged as the session's call. (3) The header
  asserted the `Blocked by` lines were already present when they were not at review time; made
  accurate, and FR-005 says where 129's `T000` goes given it has no `tasks.md`. (4) FR-004's
  overlapping-numbering policy was an unflagged decision and 131's own directory was unaccounted
  for; the directory moves, and numbering is now an Assumption (diagram continues from 132,
  gm-assistant restarts at 200) with the overlap alternative declined. (5) FR-011's rehearsal was an
  unflagged addition; flagged, with its narrower rationale. Also on the reviewer's aside: FR-007
  says feature 130's flow belongs to the new repository and drops the token-revoke requirement.
- **Round 2** - `CHANGES REQUIRED` (2 findings, both in the disposition table). (1) Four of the six
  "diagram-only" guards are repository-wide (`gate-stamp.py` has a webapp area and the ritual dies
  without it; `review-gate.sh`'s FAITHFUL clause covers every spec; `gate-hooks.sh` guards the
  webapp's `make done` too; `guard-file-hooks.sh` guards `scripts/` and `settings.json`) - now COPY
  TO BOTH, each trimmed to its repository's areas, with only `make-only-hooks.sh`/`_hookmatch.py`
  moving; and gm-assistant's copied guards now have a runner (`hooks-test` copied into
  `webapp/Makefile`), since XVIII's "that test runs" was otherwise false there. (2)
  `.claude/settings.json` and `.claude/agents/` had no row - added (settings rewritten in each;
  three agents move, two stay, `spec-fidelity` in both) and `settings.json` named in FR-006.
- **Round 3** - `FAITHFUL`. Both fixes verified against the clone (the `webapp` area of
  `gate-stamp.py`, the 13 hook paths, `_hookmatch.py`'s single caller); every MOVE row walked for
  remaining consumers - none. Two asides applied: `uncovered-in-diff.py` (called by both Makefiles)
  gets a COPY TO BOTH row; `make-only-hooks.sh`'s MOVE is labeled the session's call with what
  gm-assistant loses (the shell route to guard files).
