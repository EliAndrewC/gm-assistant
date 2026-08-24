# Tasks: The Merge Gate Runs on AWS CodeBuild, and Only When It Must

**Spec**: [spec.md](spec.md) (APPROVED - `spec-fidelity` FAITHFUL, round 3) | **Plan**: [plan.md](plan.md)

> [!IMPORTANT]
> **NOT STARTED, BY THE GM'S INSTRUCTION.** *"you can write the SpecKit feature, you cannot actually
> automate it yet."* No task below is ticked and none may be begun until the GM says go. When they
> do: sync the clone in first (`scripts/sync-with-main.sh sync-in`), re-read the Makefile and
> `sync-with-main.sh` - both are live and were reworked the day this was written - and take the
> baseline (T001) before the first edit.
>
> **TICK THESE AS YOU GO.** A task is ticked when its verification passed, not when its code was
> written. This list is externalized working memory (feature 126 left 42 tasks and zero ticks).

## Rules governing this list

- **Every refusal is TWO tasks** (constitution XVIII): FIRES on its case, STAYS QUIET on correct
  work. A guard appearing once is a planning error.
- **Every remote path is TWO tasks**: proven on the CHECK project (cannot write to main) before the
  MERGE project is wired. This is the feature's analogue of "reference settlement, then the pool".
- **Paid tasks are marked 💵 with an estimate.** Nothing else in this list spends money. The
  estimates assume `xlarge` at $0.08/min and the laptop's 5.5-minute gate; T-measure replaces them.
- **`make done` locally remains the check throughout** - free, and the thing SC-006 says must not
  slow down.

---

## Phase 1: Setup and baseline

- [ ] T001 Take the regression baseline on UNMODIFIED code in a detached worktree (`git worktree add --detach /tmp/base128 HEAD`; `( cd /tmp/base128/.claude/skills/diagram && make done )`), check each worktree failure against the clone before calling it pre-existing (constitution XIII, the 2026-08-24 clause), and record the verdict AND the wall-clock under Baseline below (SC-006's "before")
- [ ] T002 Record local `make done` wall-clock in `.claude/skills/diagram/timings.md` as a dated block with `--note "128-start, laptop"` (never in prose)
- [ ] T003 [P] Add `boto3` to `container-scripts/setup-dev-env.sh` and pin it in the diagram skill's requirements (research R10); run `setup-dev-env.sh --check`
- [ ] T004 [P] Record the AWS smoke-build API responses from this session (`start_build`, `batch_get_builds` phases, `get_log_events`, an `AccessDeniedException` shaped like the breaker) as JSON fixtures under `.claude/skills/diagram/tests/ci/fixtures/` - the saved-fixture boundary Principle X requires; `tempadmin` is NOT needed, the `gm-assistant-ci` key can replay them
- [ ] T005 [P] Write `l7r/diagram/ci/CLAUDE.md`: what each module is for, the ONE rate constant and where it is mirrored (the Lambda's `RATE_PER_MIN`), the five dispatch conditions and the GM's words each rests on, and the threat model (a session that wants the paid run and should not have it - the same shape as feature 127's)

## Phase 2: Foundational (blocks every story)

- [ ] T006 Create `l7r/diagram/ci/delta.py`: `ENGINE_PATHS` (the one list, data-model.md) and `compute_delta(root, base_ref)` via `git merge-base` + `git diff --name-only` (research R1); pure, subprocess output as fixtures
- [ ] T007 **FIRES/QUIET pair for the classifier**: `tests/ci/test_delta.py` walks a fixture containing every path KIND (engine `.py`, a test, a `.gen.py`, a manifest `.json`, the Makefile, `pyproject.toml`; and every non-engine kind - `SKILL.md`, `dev/run-log/*.json`, `future-work/*.md`, `settlements/*.md`, `pool/**/*.notes.md`, `.png`, `.svg`, a file outside the skill) and pins each classification, so a new kind cannot be silently either
- [ ] T008 Create `l7r/diagram/ci/state.py`: read/write `.git/verification-state.json` (data-model.md shape), `current_hash(root)` imported from `scripts/gate-stamp.py`'s `hash_files`/`_py_files` (research R6 - do NOT reimplement the hash)
- [ ] T009 Create `l7r/diagram/ci/decision.py`: `decide(delta, state, verified, breaker, mode) -> DispatchDecision`, pure, evaluating EVERY condition even after one fails (the "report all failures together" rule), verdict = first failure / SKIP-VERIFIED / DISPATCH
- [ ] T010 `tests/ci/test_decision.py`: one case per row of the VerificationState transition table, one per route, SKIP-VERIFIED, breaker, and the merge-vs-check difference (FR-011 applies to merge only)
- [ ] T011 Create `l7r/diagram/ci/dispatch.py`: the boto3 boundary - push mailbox, `start_build`, stream log with a 10 s cadence, exit with the build's status, look up `verified/<tree>.json`, write the remote run-log entry (data-model.md `RemoteRunLogEntry`); tested against T004's fixtures
- [ ] T012 Create `l7r/diagram/ci/__main__.py` (`merge | check | status | image`) with `assert_via_make` at the TOP and a comment saying so; add the four rows to `_invocation.OPERATIONS`; add `l7r.diagram.ci` to `pyproject.toml` coverage `source`
- [ ] T013 **FIRES**: `python3 -m l7r.diagram.ci status` outside make is refused and names `make ci-status` (extend `tests/test_invocation.py` or `scripts/test-make-only-hooks.sh`, whichever already holds the registry cases)
- [ ] T014 **STAYS QUIET**: `make ci-status` runs, prints the Delta, route, state, verified-lookup and month-to-date spend, and makes NO AWS call when the route is DIRECT (assert with the fixture client's call log)
- [ ] T015 Makefile: `quick`, `reference`, `test-file` write `green-local` on exit 0; local `done` writes `green-local` on green and `failed-gate` on red; add `ci-status`, `ci-check`, `ci-merge`, `ci-image` targets per [contracts/make-targets.md](contracts/make-targets.md); `.PHONY` and `help` updated
- [ ] T016 **FIRES**: a test in `tests/ci/` that runs `make quick` (under make, via subprocess from the suite) and asserts the state file appears with the current hash; then edits a `.py` in a temp copy and asserts `decide` refuses with the hash-mismatch reason
- [ ] T017 **STAYS QUIET**: local `make done` wall-clock re-measured after T015 and within noise of T002 (SC-006); the state write is one hash and must not show up

## Phase 3: User Story 3 - The iteration check (P2, but FIRST - it is the safe remote path) 🎯

**Goal**: one paid build on the CHECK project proves the buildspec, the image, the streaming, the
verified record and the audit entry, with no path to main.
**Independent test**: [quickstart.md](quickstart.md) §4.

- [ ] T018 [US3] Write `Dockerfile.ci` (`FROM` the CodeBuild standard image; `RUN container-scripts/setup-dev-env.sh --image`) and add the `--image` mode to `setup-dev-env.sh` (skips the `claude()` wrapper and `.bashrc`)
- [ ] T019 [US3] 💵 (~$1, one image build) `make ci-image`: prompted, cancel-by-default, reason logged via the existing `LOGBYPASS`, refused non-interactive; builds on the check project and pushes to ECR; update both projects' `image` to the ECR URI
- [ ] T020 [US3] **FIRES**: `make ci-image` with no terminal is refused (same shape as `bypass-audit`; extend that test)
- [ ] T021 [US3] **STAYS QUIET**: `make ci-image` in a terminal with a reason proceeds and logs `permitted`
- [ ] T022 [US3] Write `buildspec/check.yml` per the contract: clone via the token, checkout `$GIT_SHA` (refuse if it is not the mailbox tip), `git merge --no-edit origin/main || exit 1` with "CONFLICT" in the log, `make done` in the skill directory, on green write `verified/<tree>.json`; point the check project at the repo buildspec
- [ ] T023 [US3] **Admin-key task (GM)**: bucket policy denying `s3:PutObject` under `verified/` to every principal except `gm-assistant-codebuild-role` (research R8). Ticked only when a `put_object` with the session's key returns `AccessDenied`
- [ ] T024 [US3] 💵 (~$0.45) First end-to-end `make ci-check` on a real engine delta: mailbox branch appears, build streams, exit status matches, `verified/<tree>.json` exists, run-log entry has `where: codebuild`, `minutes`, `cost_usd`; record the wall-clock in `timings.md`
- [ ] T025 [US3] 💵 (~$0.10) `make ci-check` on a delta whose merge with main CONFLICTS (make one deliberately in a scratch commit): build fails inside its first minute with "CONFLICT", no record written, state becomes `failed-gate`
- [ ] T026 [US3] **FIRES**: `make ci-check` refuses on a DIRECT-route delta, on `failed-gate`, and on a hash mismatch - each asserting the fixture client saw NO `start_build`
- [ ] T027 [US3] **STAYS QUIET**: `make ci-check` on an engine delta with a fresh green local check dispatches (fixture client sees exactly one `start_build`)
- [ ] T028 [US3] 💵 (~$1.20) T-measure: the same `make done` on `2xlarge`; record both numbers and provisioning with the custom image in `timings.md`; choose the compute type by the number and set it on both projects; update the rate constant AND the Lambda's `RATE_PER_MIN` if it changes (spec baseline table says where)

## Phase 4: User Story 1 - The merge (P1)

**Goal**: the gated route lands work on GitHub `main` through the merge project; the direct route
still lands docs for free.
**Independent test**: [quickstart.md](quickstart.md) §2 and §5.

- [ ] T029 [US1] Switch this clone's `origin` to GitHub and document the one-time `git remote set-url origin ssh://git@github.com/EliAndrewC/gm-assistant` for existing clones in `docs/session-clones.md`; change the clone-creation instruction in CLAUDE.md (research R7)
- [ ] T030 [US1] `sync-with-main.sh push`: `git fetch origin` first; route via `make ci-status ROUTE=1`; DIRECT = today's flock'd pull+push against GitHub; GATED = `make ci-merge`, then `git pull --ff-only origin main` (or the direct push on SKIP-VERIFIED); then `flock` + `git -C /gm-assistant pull --ff-only origin main` to refresh the mirror; overlap advisory unchanged; render-sync unchanged (contract)
- [ ] T031 [US1] Create `scripts/test-sync-with-main.sh` (does not exist today): the route decision, the mirror refresh, and the `--ff-only` failure message, driven with `CLONE_MAIN` pointed at temp repos - and confirm `make hooks-test` picks it up (its glob is `*-hooks.sh` + `review-gate.sh`; extend the glob or name the file to match, and say which in a comment)
- [ ] T032 [US1] **FIRES**: a docs-only delta pushed through `sync-with-main.sh push` starts no build (fixture client log empty) and lands directly
- [ ] T033 [US1] **FIRES**: an engine delta with an open task in the named feature's `tasks.md`, or with no FAITHFUL verdict, or with NO feature named at all, is refused naming the reason and starts nothing (fourth request: the gated route requires a complete spec-kit feature); **STAYS QUIET**: a direct-route delta needs no feature
- [ ] T034 [US1] Write `buildspec/merge.yml` = check + `git push origin HEAD:main` (a rejection fails the build with "main moved; re-run", no retry) + delete the mailbox; point the merge project at it
- [ ] T035 [US1] 💵 (~$0.45, or $0 if T024's tree is unchanged) First real merge through `sync-with-main.sh done` on THIS feature's own work: build lands on GitHub `main`, clone fast-forwards, `/gm-assistant` fast-forwards, render-sync runs in the mirror, GitHub and the mirror show the same commit
- [ ] T036 [US1] 💵 (~$0.10) Non-fast-forward case: push an unrelated docs commit to GitHub `main` from a second clone while a merge build is between fetch and push (a `sleep` in a scratch buildspec is acceptable here - it is the build, not the session, that waits); the build fails with "main moved"; nothing landed twice
- [ ] T037 [US1] **STAYS QUIET**: the spec-number claim push (a fresh `specs/NNN/` only) still goes through the direct route with no build - this is the push every feature makes minutes after it starts

## Phase 5: User Story 2 - No re-dispatch after a failed gate (P1)

- [ ] T038 [US2] **FIRES**: after a remote build ends FAILED/TIMED_OUT/STOPPED, state is `failed-gate`; `make ci-merge` and `make ci-check` both refuse naming `make quick`
- [ ] T039 [US2] **STAYS QUIET**: `make quick` green -> dispatch permitted; `make reference` green -> permitted; a local green `make done` -> permitted
- [ ] T040 [US2] The edit-after-green case refuses with the hash reason (the Assumptions reading; flagged, not widened)

## Phase 6: User Story 3 (second half) - The short-circuit at merge time

- [ ] T041 [US3] `make ci-merge` computes the would-be tree with `git merge-tree --write-tree origin/main HEAD` (research R2), looks up `verified/<tree>.json`, and on a hit prints SKIP-VERIFIED naming the build id
- [ ] T042 [US3] 💵 ($0 expected) `make ci-check` green, then immediately `sync-with-main.sh done` on the same tree: no build, direct push, the run-log entry says `skip-verified:<build id>` (SC-003)
- [ ] T043 [US3] **FIRES**: advance main with an unrelated commit; the same `sync-with-main.sh done` now dispatches (tree differs)

## Phase 7: User Story 4 - Audit and cost

- [ ] T044 [US4] `make audit` gains "Remote spend": every `where: codebuild` entry with minutes and cost, and a month-to-date total; cross-check the total against the CodeBuild console once and record the comparison here (SC-005)
- [ ] T045 [US4] The pre-dispatch printout (FR-014): estimate, month-to-date, each condition with its why - asserted in `test_decision.py` against a golden text
- [ ] T046 [US4] **FIRES**: an `AccessDeniedException` naming `codebuild:StartBuild` (fixture) is reported as the breaker with the IAM detach instruction (FR-021); any other AWS error is reported as itself
- [ ] T047 [US4] **STAYS QUIET**: a successful `start_build` fixture produces no breaker text

## Phase 8: Guards and docs

- [ ] T048 `make hooks-test` green with every new companion; delete each new guard in a scratch copy and watch its test go red (the T034-of-127 discipline), record the list of guard/test pairs here
- [ ] T049 CLAUDE.md "Session clones" and "WHAT IS ENFORCED, AND WHERE": the two routes, the mirror, `origin` = GitHub, the GM's laptop GitHub push retired for this repo; `docs/session-clones.md` the same in full; the diagram skill `CLAUDE.md` command map gains the four `ci-*` targets with measured times
- [ ] T050 `.claude/skills/diagram/dev/loop.md`: when to use `make ci-check` vs local (the dispatch conditions ARE the answer - a session does not decide), and the cost of each remote target from `timings.md`
- [ ] T051 Memory: update `project-aws-codebuild-ci` and `feedback-user-handles-git` (the GM no longer pushes gm-assistant's main to GitHub; `/host-l7r-repo` unchanged)
- [ ] T052 Report to the GM with the implementation: the two flagged readings (FR-011 no-active-feature; FR-012 edit-after-green), the retired laptop push job, the measured numbers, and the aside that the cost controls could be brought into the repo if wanted

## Closing audit (constitution VI)

- [ ] T053 Audit `dev/bypass-log/` entries added during this feature and state here whether each was justified (`make ci-image`'s prompt logs there too)
- [ ] T054 Baseline vs end: local `make done` wall-clock (T002 vs now) in `timings.md`; regression check against T001 in the clone; `sync-with-main.sh done` - through the NEW gated route, which is this feature's own first production use

---

## Baseline (T001/T002 - fill in before the first edit)

| | value |
|---|---|
| worktree gate verdict | |
| failures checked against the clone | |
| local `make done` wall-clock | |

## Guard/test pairs (T048 - fill in)

| guard | companion | deleted-guard test went red? |
|---|---|---|

---

## Amendment phases (GM's second request, 2026-08-24)

## Phase 9: User Story 6 - The full sweep on CodeBuild

- [ ] T055 [US6] `bypass-audit`: add the build-side door (plan, design note 6) - when `CODEBUILD_BUILD_ID` is set, accept the full scope ONLY if a `permitted` entry in `dev/bypass-log/` has target `done FULL`, `commit` an ancestor of HEAD and not of `origin/main`; otherwise refuse with a message naming the missing entry. The local non-interactive refusal is untouched (FR-026)
- [ ] T056 [US6] **FIRES**: build-side door refuses with no entry, with a `cancelled` entry, with an entry whose commit is on main, and with `REF_WHY` in the environment alone (extend `scripts/test-*` or `tests/ci/test_bypass_door.py`, driven by a temp repo)
- [ ] T057 [US6] **STAYS QUIET**: a committed `permitted` entry authored by this work opens the full scope; locally the interactive prompt behaves exactly as before (re-run 127's existing bypass tests unchanged)
- [ ] T058 [US6] `ci-merge` AND `ci-check` accept `FULL=1` (third request - FR-015/FR-024): run the local prompt FIRST; on `permitted`, commit the entry (`chore: authorize FULL sweep - <reason>`), then dispatch with `MAKE_TARGET="done FULL=1"`; on `cancelled`/refused, dispatch nothing
- [ ] T059 [US6] **FIRES**: `ci-merge FULL=1` / `ci-check FULL=1` with no terminal are refused locally, no build (fixture client sees nothing); cancelling at the prompt: no build
- [ ] T060 [US6] Buildspecs run `make $MAKE_TARGET`; on FULL upload `dev/perf-log/*` as artifacts; the dispatcher downloads them into the clone
- [ ] T061 [US6] Verified record gains `scope`; FR-027's rule in `decision.py` (a reference record does not satisfy a FULL merge; a FULL record satisfies either) with a test each way
- [ ] T063 [US6] 💵 (~$1) First FULL run, through the MERGE project on this feature's own final push (there is no check-project FULL - FR-015 - so the two-step rule is met by T024/T035 having proven the buildspec in reference scope first): prompt answered, entry committed, every pool map + ratchet + floors + `perf-gate` with BOTH bookends taken in-build, snapshots came back; wall-clock in `timings.md`. Replaces T054's plain push as the feature's first production use
- [ ] T064 [US6] `perf_snapshot.py`: `host` and `image` fields (plan, design note 7); `perf-gate` pairs on `(host, image)` and refuses a cross-machine pair naming both
- [ ] T065 [US6] **FIRES**: `perf-gate` with a laptop `-start` and a build `-end` refuses; **STAYS QUIET**: two build snapshots on the same image pair
- [ ] T066 [US6] Inside the FULL buildspec, `perf-gate` takes BOTH bookends itself: `-start` in a detached worktree at the pre-merge `origin/main`, `-end` on the merge (plan, design note 7) - no standalone remote bookend run exists (FR-028); the first build-machine pair is produced by T063 and is the "reconstituted" number

## Phase 10: User Story 7 - Sync at the tooling level

- [ ] T067 [US7] `sync-with-main.sh sync_in()`: fetch GitHub -> `flock` mirror `--ff-only` (die with the message on failure) -> render-sync in the mirror -> clone merge (clean clone only); the mirror steps run even for a dirty clone (plan, design note 8)
- [ ] T068 [US7] **FIRES**: a hand commit in a temp "mirror" makes sync-in stop with "mirror cannot fast-forward" (in `scripts/test-sync-with-main.sh`, temp repos via `CLONE_MAIN`)
- [ ] T069 [US7] **STAYS QUIET**: with nothing changed, sync-in's wall-clock is within noise of today's; with a GitHub-side commit, the mirror, its renders and the clone all reflect it after one prompt (SC-009 - verify by commit hash and a render's content hash)
- [ ] T070 [US7] `clone-sync-hooks.sh` `prompt` mode: on a DIRTY clone run `sync-with-main.sh sync-in --mirror-only` instead of exiting early; on a clean clone the full sync-in (R13, FR-030). **FIRES**: a dirty-clone turn still advances the mirror (extend `scripts/test-clone-sync-hooks.sh`); **STAYS QUIET**: the clone itself is not touched
- [ ] T071 [US7] CLAUDE.md "Session clones" rewritten for the post-feature flow (FR-032): GitHub `main` is main; `/gm-assistant` is a mirror nobody pushes to; `origin` = GitHub; sync-in is the whole flow and the hook runs it; two routes; `FULL=1` remote with the local prompt; the GM's laptop pushes flow in like anything else. `docs/session-clones.md` in full. Remove the retired local-main instructions rather than annotating them. (Supersedes T049's scope.)
- [ ] T072 [US7] Memory notes updated: `project-session-clone-workflow`, `feedback-user-handles-git`, `project-aws-codebuild-ci`

- [ ] T073 Principle XIV: `bypass-audit` prints `logged to dev/bypass-log.jsonl` but `LOGBYPASS` writes `dev/bypass-log/<ts>-<pid>.json` - fix the message (found by the amendment's fidelity reviewer; FR-025 makes that message load-bearing)

## Phase 11: User Story 8 - Local checks first, the build parked in parallel (third request)

- [ ] T074 [US8] Makefile `done`: with `FULL`, run `bypass-audit` THEN `reference` (R15, FR-034) - the prompt authorizes the expense, the reference check still gates; `REF_OK` skips only the reference step and logs as it does elsewhere. **FIRES**: a red reference map + `FULL=1` + an answered prompt stops before the suite (SC-012); **STAYS QUIET**: green map proceeds; `REF_OK=1` proceeds with its own logged reason
- [ ] T075 [US8] Dispatcher sequence per the contract: conditions -> lint/format/typecheck locally -> `start_build` -> `make reference` locally -> `stop_build`/`go` (FR-033, FR-035). **FIRES**: lint failure starts no build (fixture client log empty); **STAYS QUIET**: lint pass starts exactly one
- [ ] T076 [US8] Buildspecs gain the `wait-go` first phase: poll `go/<build-id>` every 2 s, ≤ 120 s, absent -> fail "aborted: no go signal", present -> delete and continue (FR-036). Verified on the check project with a deliberately withheld signal 💵 (~$0.16 - the whole point is that this is the maximum a dead dispatcher can cost)
- [ ] T077 [US8] **FIRES**: local reference failure -> `stop_build` on OUR id within seconds, run-log entry `aborted-local-reference` with the partial cost; **STAYS QUIET**: the dispatcher never calls `stop_build` with any id but its own (assert on the fixture client)
- [ ] T078 [US8] 💵 (~$0.50) SC-011 measurement: parked vs unparked wall time to the gate's first test on the check project; record both and the abort cost in `timings.md`; if the saving is under ~10 s, drop the parking step and record the decision (research R14 says so in advance so the number, not the sunk work, decides)
- [ ] T079 [US8] Reference step runs every tier's reference map (today: Inashiro; `mapcheck.py`'s tier table is the source) and may run them in parallel - assert the dispatcher calls `make reference`, not a hand-rolled list
- [ ] T080 [US8] `ci-check FULL=1` end to end on the check project 💵 (~$1): prompt, committed entry, parked build, local reference, release, FULL suite with both bookends, FULL verified record (restores the check-first proof for FULL that the first amendment's round 2 removed)
- [ ] T081 [US8] Docs: the dispatch sequence and the parked-build cost in `l7r/diagram/ci/CLAUDE.md` and `dev/loop.md`; the FULL-runs-reference-first correction in the Makefile comments (the "reference gates everything expensive" block currently claims it for `done` without qualification)

## Phase 12: Fourth request - every expensive operation, and the feature-required rule

- [ ] T082 `ci-check TARGET=<operation>` for every `expensive` row of `_invocation.OPERATIONS` (`cohort N=48`, `cache-audit`, `regressions`, ...): same dispatch sequence, the operation's report returned as a build artifact into the clone; **FIRES**: a cheap/read-only operation as TARGET is refused; **STAYS QUIET**: `cohort` dispatches. 💵 (~$2) one `cohort N=48` on `xlarge` measured and recorded in `timings.md` - the number the whole feature was first argued from
- [ ] T083 FR-011 as ruled: the gated merge requires `SPECIFY_FEATURE`/`feature.json` naming a feature whose `tasks.md` has no open box and whose `spec.md` carries FAITHFUL; CLAUDE.md's "tweaks need no spec-kit" gains the diagram-skill exception (FR-032)

