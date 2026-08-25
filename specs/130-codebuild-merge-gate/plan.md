# Implementation Plan: The Merge Gate Runs on AWS CodeBuild, and Only When It Must

**Spec**: [spec.md](spec.md) - APPROVED, `spec-fidelity` verdict FAITHFUL at round 3.
**Request**: [gm-request.md](gm-request.md) - verbatim, the authority. Not to be edited.
**Status**: PLANNED, NOT IMPLEMENTED. The GM: *"you can write the SpecKit feature, you cannot
actually automate it yet."* Implementation starts on a separate go from the GM.

## Summary

The stop-work ritual's push gains a second route. A delta with diagram engine code in it goes to
CodeBuild: the clone's HEAD is pushed to a GitHub mailbox branch, a build on the concurrency-1
merge project merges the latest GitHub `main` into it, runs the same reference-scope `make done`
the laptop runs, and on green fast-forward-pushes the merge to `main` and records the tree as
verified. A delta without engine code pushes directly to GitHub `main`, as today, for free. Five
conditions are checked locally before a cent is spent, a green iteration run short-circuits the
merge for the same tree, and every remote run lands in the local audit with its cost. GitHub `main`
becomes the integration point; `/gm-assistant` becomes a mirror that render-sync runs in.

**Amended on the GM's second request (same day):** the full sweep (`make done FULL=1`) goes to
CodeBuild too - its cancel-by-default prompt runs locally, the `permitted` answer is committed into
the tree the build tests, and the build opens the full scope only to a tree carrying it. That puts
`perf-gate` on CodeBuild, so the performance bookends move there and snapshots carry machine
identity. And sync-in becomes the whole flow - fetch GitHub main, fast-forward the mirror,
render-sync there, merge into the clone - run by the prompt hook that already runs sync-in every
turn, so nothing is remembered.

**Amended a second time on the GM's third request:** FULL is available during iteration too
(`ci-check FULL=1`), every dispatch runs lint locally, then starts the build PARKED at a go/abort
wait while the reference settlement(s) run locally, and releases or stops it by the result - and
`done FULL=1` now runs the reference check after its prompt instead of in place of it (R15).

Nothing about what the gate CHECKS changes, except that the reference-first stop now also applies
to FULL. No map geometry changes. No failing seed is addressed.

## Technical Context

**Language/Version**: Python 3.14 (the dispatcher, `mypy --strict`, 100% coverage); Bash (two
existing scripts change, one hook test companion per new guard); GNU Make; YAML (two buildspecs);
Dockerfile.

**Primary Dependencies**: `boto3` (NEW - pinned; R10), git >= 2.38 for `merge-tree --write-tree`
(container has 2.53; `git merge-tree --write-tree origin/main HEAD` verified to run). The build image carries what `setup-dev-env.sh` installs today.

**Storage**: `.git/verification-state.json` per clone; `dev/run-log/` (existing, gains remote
entries); S3 `verified/<tree>.json` written only by the build; a GitHub mailbox branch per clone,
deleted on success.

**Testing**: pytest for `l7r/diagram/ci/` with the boto3 boundary behind SAVED FIXTURES (recorded
`start_build` / `batch_get_builds` / `get_log_events` responses from this session's smoke builds -
never a mock of the transport); `scripts/test-*-hooks.sh` companions for every new refusal;
`make hooks-test` runs them in the gate.

**Target Platform**: Linux container (session side); CodeBuild Linux `xlarge` (build side) - the
compute type is chosen by measurement (R9), not here.

**Project Type**: developer tooling for this repo, plus two CI job definitions.

**Performance Goals**: the local ladder unchanged within noise (SC-006) - the only new local work
is one content hash (the same one `gate-stamp` already computes at push) and a few git plumbing
calls. Remote `make done` wall-clock: MEASURED, recorded, not targeted.

**Constraints**: nothing runs on AWS unless every condition in FR-007..FR-013 passes; the local
non-interactive-FULL refusal stays exactly as it is and the build opens the full scope only to a
committed `permitted` entry (R11); the session's credential cannot write a verified record (R8,
needs one admin-key IAM edit); no polling in command text (R5); a laptop `-start` never pairs with a
build `-end` (R12).

**Scale/Scope**: 4 new make targets (`ci-merge`, `ci-check`, `ci-status`, `ci-image`),
2 changed scripts (`sync-with-main.sh` sync-in and push; `perf_snapshot.py` machine identity), 5
changed targets (`quick`/`reference`/`test-file`/`done` state; `perf-gate` same-machine pairing;
`bypass-audit` the build-side door), 1 new Python package of ~5 modules, 2 buildspecs, 1
Dockerfile, 1 IAM policy edit, CLAUDE.md + `docs/session-clones.md` + the memory note rewritten
for the post-feature flow.

**Single-artifact target**: **not applicable - argued, not skipped.** No generator changes. The
analogue - the one thing proven before anything widens - is `make done` on the laptop remaining
green and its wall-clock unchanged, checked at every step; and on the remote side, ONE build on the
check project proving the buildspec end to end before the merge project is wired.

**Every step is two steps.** The generator rule does not bind (nothing is generated). Its analogue
here, enforced in tasks: every refusal is TWO tasks (FIRES / STAYS QUIET, constitution XVIII), and
every remote path is TWO tasks (the check project first, then the merge project), because the check
project cannot write to main and is therefore the safe place to be wrong.

## Performance bookends

**For THIS feature: not applicable as a generator measurement** - it does not touch the generator.
Numbers taken because the spec demands them: local `make done` wall-clock before and after (SC-006),
remote `make done` in both scopes on `xlarge` and `2xlarge` (SC-004, R9), all in `timings.md`.

**For every LATER feature: the bookends move to CodeBuild, inside the FULL build** (FR-028/FR-029,
R12). The FULL build's `perf-gate` takes BOTH: `-start` in a detached worktree at the pre-merge
`origin/main` (the retroactive baseline the target's own message already documents), then `-end` on
the merge result; both come back to `dev/perf-log/` as artifacts, both carry machine identity, and
`perf-gate` refuses a cross-machine pair. There is NO standalone remote bookend run - FR-010's two
permitted remote runs are the only ones. The first build-machine pair is produced by this feature's
own FULL merge (T063); that is the *"reconstituted"* number.

## Constitution Check

- **I. Accessibility-First Viewports**: no UI. N/A.
- **II. Bold, Intentional Design**: no UI. N/A. Refusal text follows the existing hook voice: what
  was refused, why, and the one command to run instead.
- **III. Pool Data Conventions**: no pool data. N/A.
- **IV. One Canonical Home for GM Source**: nothing moved; `gm-request.md` is a verbatim transcript
  inside the feature, not a relocation. N/A.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: no SOURCE block touched; `gm-request.md`
  treated as equivalent - never edited.
- **VI. Verify Before Reporting Done**: verification named per task; the check project is proven
  before the merge project; `make done` locally is the cheap check throughout. Delegated work
  (any subagent) is spot-checked by reading the artifact.
- **VII / VIII / IX**: nothing generated, no in-world prose, no setting content. N/A.
- **X. Python Discipline (NON-NEGOTIABLE)**: `l7r/diagram/ci/` is `mypy --strict`, 100% covered,
  added to `pyproject.toml`'s `[tool.coverage.run] source` list by module name (that list is
  deliberately explicit - R-note in pyproject). External boundary (AWS) via saved fixtures. No file
  approaches ~1,000 lines. `boto3` pinned.
- **XI. Japanese Authenticity**: no kanji. N/A.
- **XII. Historical Grounding (NON-NEGOTIABLE)**: no claim about the world. The measure-before-
  assert analogue IS honored: every mechanism in research.md was exercised (R1, R2, R3, R5, R6, R7).
- **XIII. No Known Regressions (NON-NEGOTIABLE)**: baseline in a detached worktree before the first
  edit (T001), every worktree failure checked against the clone before being called pre-existing.
  The specific regression risk is a refusal firing on legitimate work - covered by the STAYS QUIET
  half of every guard pair - and the local ladder slowing, covered by SC-006's timing.
- **XIV. Fix Defects Where You Find Them (NON-NEGOTIABLE)**: expected to surface things in
  `sync-with-main.sh` and the hooks while rerouting them; fixed in this feature.
- **XV. Keep Going (NON-NEGOTIABLE)**: one planned stop, and it is the GM's, not the session's: R8's
  IAM edit needs the admin key. The task says exactly what to run; everything not depending on it
  proceeds.
- **XVI. Build What Was Asked (NON-NEGOTIABLE)**: spec FAITHFUL at round 3 after five findings, four
  of them scope the session had added; the amendment for the GM's second request is under its own
  fidelity rounds (spec, Review history). Two readings remain flagged in the spec's Assumptions
  (FR-011 with no active feature; FR-012's edit-after-green case); both go to the GM with the
  implementation report, neither is widened during implementation. Any new exception goes to
  `spec-fidelity` Mode 1 before it is written.
- **XVII. A README Is Written By A Human**: no README created or edited; new docs are CLAUDE.md
  sections and `docs/` files.
- **XVIII. A Guard Ships With Its Test (NON-NEGOTIABLE)**: every refusal here is two tasks, and
  `make hooks-test` runs the companions.

**Gate: PASS.** Every N/A above is argued rather than asserted.

## Project Structure

### Documentation (this feature)

```
specs/130-codebuild-merge-gate/
├── gm-request.md            # verbatim - the authority
├── spec.md                  # APPROVED (FAITHFUL, round 3)
├── plan.md                  # this file
├── research.md              # R1-R10, measured/verified
├── data-model.md            # Delta, VerificationState, VerifiedRecord, RemoteRunLogEntry, DispatchDecision
├── contracts/make-targets.md
├── quickstart.md
├── checklists/requirements.md
└── tasks.md                 # /speckit-tasks
```

### Source Code

```
.claude/skills/diagram/
├── Makefile                          # + ci-merge ci-check ci-image ci-status; quick/reference/test-file/done write state; audit adds Remote spend
├── pyproject.toml                    # + l7r.diagram.ci in coverage source
├── l7r/diagram/_invocation.py        # + OPERATIONS rows for the ci targets
├── l7r/diagram/ci/                   # NEW
│   ├── CLAUDE.md                     #   index: what each module is for, the one rate constant, the threat model for the dispatch conditions
│   ├── __main__.py                   #   merge | check | status | image; assert_via_make at the top
│   ├── delta.py                      #   Delta + ENGINE_PATHS (the one list)
│   ├── state.py                      #   VerificationState; hash via scripts/gate-stamp.hash_files
│   ├── decision.py                   #   DispatchDecision (pure)
│   └── dispatch.py                   #   boto3 boundary: start, stream, record; the S3 verified lookup
├── tests/ci/                         # NEW - mirrors the package; fixtures/ holds recorded AWS responses
└── timings.md                        # + the remote/local make done rows

buildspec/
├── merge.yml                         # NEW
└── check.yml                         # NEW
Dockerfile.ci                         # NEW

scripts/
├── sync-with-main.sh                 # fetch first; route; ci-merge on GATED; mirror pull; origin = GitHub
├── test-sync-with-main.sh            # NEW - does not exist today; the route decision is a guard and ships with its test (XVIII); run by hooks-test
└── gate-stamp.py                     # unchanged in behavior; hash_files imported by state.py

container-scripts/setup-dev-env.sh    # + boto3; + --image mode for Dockerfile.ci
CLAUDE.md, docs/session-clones.md     # clone origin = GitHub; mirror; the GM's GitHub push job retired for this repo
```

**Structure Decision**: the dispatcher lives INSIDE the diagram skill (`l7r/diagram/ci/`) rather
than in `scripts/`, because feature 127's guards, registry, coverage gate and `assert_via_make` all
live there and a repo-level script would have to reinvent each. `sync-with-main.sh` reaches it the
way it already reaches render-sync: `make --no-print-directory ci-merge`.

## Design notes that the tasks depend on

1. **Order of conditions at dispatch** (FR-014 prints all; the first failure decides): route ->
   feature-complete (merge only) -> green-local-since-edit -> tree-verified? -> breaker. Breaker is
   last because it is the only one that costs an AWS call; the others are local and free.
2. **The breaker check is a dry `start_build`?** No - there is no dry-run API. The dispatcher calls
   `start_build`; an `AccessDeniedException` whose message names `codebuild:StartBuild` is reported
   as the breaker with the detach instruction (FR-021). Any other AWS error is reported as itself.
3. **Month-to-date spend** is summed from LOCAL run-log entries, not from AWS (no Cost Explorer
   call - it costs money). Cross-checked once against the console in SC-005.
4. **The mailbox branch name** is `session/<clone-name>`; `<clone-name>` is the clone directory's
   basename, which the clone-sync hooks already validate. A stale mailbox from a failed build is
   overwritten by the next push (mailbox branches are the one place a force push is fine, and the
   ruleset does not cover them).
5. **The mirror pull uses `--ff-only`.** If it ever fails, someone committed in `/gm-assistant`
   directly, which the existing guards forbid; the ritual stops and says so.
6. **The FULL door on the build side** (R11): `bypass-audit` gains one more branch, evaluated only
   when `CODEBUILD_BUILD_ID` is set AND a `permitted` entry exists in `dev/bypass-log/` whose
   `target` is `done FULL` and whose `commit` is an ancestor of `HEAD` and not an ancestor of
   `origin/main` (i.e. it was authorized by THIS work, not inherited). The env check alone is not
   the guard - a session can set it - the committed entry is; the env check only selects which
   message to print. Locally, with no such entry, the existing refusal text stands untouched.
7. **Machine identity** (R12): `perf_snapshot` already records `cpus` and `platform.machine()`;
   it gains `host` (the laptop's hostname, or `codebuild:<compute type>`) and `image` (the ECR
   image digest, or `laptop`). `perf-gate` pairs `-start`/`-end` by `(host, image)` and refuses
   otherwise, naming both. Snapshots taken in a build are S3 artifacts that `ci-merge`/`ci-check`
   download into `dev/perf-log/` before returning; the session commits them like any other. Inside
   a FULL build, `perf-gate` takes the `-start` itself: `git worktree add --detach /tmp/base
   origin/main && make perf LABEL=NNN-start` there, then `-end` on the merge - the same retroactive
   procedure its refusal message prints today, executed by the build.
8. **Sync-in is the whole flow, and the hook changes** (R13): `sync_in()` in `sync-with-main.sh`
   gains a `--mirror-only` form (fetch -> `flock` mirror `--ff-only` -> render-sync) and the full
   form adds the clone merge after it. `clone-sync-hooks.sh` `prompt` mode, which today exits early
   on a dirty clone, instead runs `sync-in --mirror-only` on a dirty clone and full `sync-in` on a
   clean one. The mirror is nobody's workspace, so refreshing it mid-task loses nothing; the clone
   merge keeps its skip because mid-task work is sacred.
9. **Every dispatch is lint -> start-and-park -> reference -> go/stop** (R14, FR-033..FR-037,
   third request). The parked build polls `go/<build-id>` in the CI bucket for ≤ 120 s; the
   dispatcher writes it after `make reference` passes locally, or calls `stop_build` on its own id
   the moment a reference map fails. Nothing is shared between sessions on AWS; a parked merge build
   holds the single merge slot ≤ 26 s. SC-011 measures whether parking earns its keep; if not, the
   step is dropped and the sequence is lint -> reference -> start.
10. **`done FULL=1` runs the reference check** (R15, FR-034): `bypass-audit` then `reference` then
   the phases, locally and in the build alike. Today the prompt REPLACES the reference step - the
   defect the GM's third request surfaced ("no way to short circuit that" was true only of
   reference scope).

## Complexity Tracking

| concern | why it is accepted |
|---|---|
| Two routes to main instead of one | The GM's cost rule requires that a docs-only push spend nothing; a single route through CodeBuild would spend ~$0.08 per docs push. The route is DERIVED from the delta, never chosen by the session, so it is not a "choice that gets chosen wrong under pressure". |
| `origin` moves to GitHub for every clone | The one design the GM described and delegated (spec, "the delegated decision"); five call sites, all found (R7); the alternative was priced and declined in the spec. |
| A second copy of the gate's definition (the buildspec) | It is not a second definition: the buildspec runs `make done`. It only says how to fetch, merge, and push. |
| One task needs the admin key (R8) | FR-016's "MUST be unable" is not achievable with the session's own permissions, by design. |
| A second acceptance path for FULL, on the build side | The GM asked for exactly this ("that part can be run locally, and then the actual dispatch"). It is gated on a committed tracked file, so using it without the prompt is a visible diff - the same bar as every other remaining bypass. The local refusal is untouched. |
| Bookends move machines mid-history | Laptop and build numbers were never comparable; pretending otherwise is the +51% slowdown feature 126 shipped unnoticed. The laptop history stays; the first build-machine `-start` is this feature's deliverable. |
