# Contracts: the make targets, the build specs, and the scripts they call

## New make targets (diagram skill `Makefile`) - operations under feature 127

| target | cost | prompts? | what it does |
|---|---|---|---|
| `ci-merge` | paid | no | The merge action's gated route. Called by `sync-with-main.sh push`, not by hand. Computes the Delta and the DispatchDecision; on DISPATCH pushes the mailbox branch, starts a build on `gm-assistant-merge`, streams the log, writes the run-log entry, exits with the build's status. On SKIP-VERIFIED exits 0 having pushed nothing (the caller pushes directly). On REFUSE exits 1 with every condition printed. |
| `ci-check` | paid | no | The iteration check (FR-015). Same as `ci-merge` minus the feature-complete condition and minus any push to main; runs on `gm-assistant-check`. |
| `ci-image` | paid | **yes** - cancel-by-default, reason logged, refused non-interactive | Rebuilds the build image on CodeBuild from `Dockerfile.ci` and pushes it to ECR. Rare. |
| `ci-status` | free | no | Read-only: prints the VerificationState, the Delta and route, whether the would-be tree is verified, and month-to-date remote spend. The "why won't it dispatch" diagnostic - exists so no session reaches for an override to find out. |

Changed targets:

| target | change |
|---|---|
| `quick`, `reference`, `test-file` | on exit 0, write VerificationState `green-local` |
| `done` (local) | on green, write `green-local`; on red, write `failed-gate`; otherwise unchanged |
| `audit` | adds "Remote spend" - month-to-date `cost_usd` over remote entries |

## `sync-with-main.sh push` - the merge action

```
push:
  refuse dirty tree                                   (unchanged)
  duplicate-defs selftest + check                     (unchanged)
  review-gate                                         (unchanged)
  git fetch origin                                    (NEW - the delta is against the LATEST main)
  route = make ci-status ROUTE=1                      (NEW)
  DIRECT:  gate-stamp --check origin/main             (unchanged for the webapp area; vacuous for diagram by construction)
           flock: git pull --no-rebase origin main && git push origin HEAD:main
  GATED:   make ci-merge                              (dispatch / skip-verified / refuse)
           on 0: flock: git pull --ff-only origin main   (the build already landed the merge; this brings the clone to it)
                 or, on SKIP-VERIFIED: flock: git pull --no-rebase origin main && git push origin HEAD:main
  then:    flock: git -C /gm-assistant pull --ff-only origin main    (NEW - refresh the mirror)
  overlap advisory                                    (unchanged)
render-sync:                                          (unchanged - runs in the mirror)
```

## `buildspec/merge.yml` (in the repo; the project's inline placeholder is replaced by it)

```
env:  GITHUB_TOKEN (Secrets Manager), GIT_SHA, MAILBOX, CI_BUCKET, RATE_PER_MIN
phases:
  install:   git clone --filter=blob:none https://x-access-token:$GITHUB_TOKEN@github.com/EliAndrewC/gm-assistant
             git checkout $GIT_SHA   (must equal the tip of $MAILBOX - refuse otherwise)
  pre_build: git merge --no-edit origin/main || { echo "CONFLICT"; exit 1; }
             tree=$(git rev-parse HEAD^{tree})
  build:     cd .claude/skills/diagram && GM_ASSISTANT_ALLOW_MAIN=  make $MAKE_TARGET   (`done`, or `done FULL=1` only when the tree carries the committed permitted entry - R11)
  post_build (only if build succeeded):
             write verified/$tree.json to $CI_BUCKET
             git push origin HEAD:main || { echo "main moved; re-run"; exit 1; }
             git push origin --delete $MAILBOX
```

`buildspec/check.yml` is identical minus the two pushes. Both are the SAME `make done` the laptop
runs; nothing about what the gate checks changes.

## `Dockerfile.ci`

`FROM` the CodeBuild standard image; `RUN container-scripts/setup-dev-env.sh --image` - the existing
setup script with a flag that skips the parts that only make sense on the laptop (the `claude()`
wrapper, `.bashrc`). Python 3.14, resvg + DejaVu, Playwright with deps, the pinned requirements.

## The dispatcher module: `l7r/diagram/ci/` (engine-adjacent, 100% covered, `mypy --strict`)

```
delta.py       compute_delta(root, base_ref) -> Delta         pure: git plumbing via subprocess, fixtures for tests
state.py       read/write VerificationState; current_hash(root)   reuses scripts/gate-stamp.hash_files
decision.py    decide(delta, state, verified, breaker, mode) -> DispatchDecision   pure
dispatch.py    start/stream/record - the boto3 boundary, tested via saved fixtures (recorded API responses)
__main__.py    argparse: merge | check | status | image; assert_via_make at the top
```

Registered in `_invocation.OPERATIONS` as `("ci-merge", "expensive")` etc. so a bare
`python3 -m l7r.diagram.ci` is refused and named.

## Amendment: the full sweep, the bookends, and sync-in

| target | cost | prompts? | what it does |
|---|---|---|---|
| `ci-merge FULL=1` (merge action only; `ci-check` stays reference scope, FR-015) | paid (~6+ min) | **yes, locally** - the existing `bypass-audit` prompt, cancel by default, reason logged | On `permitted`: commits the bypass-log entry (`chore: authorize FULL sweep - <reason>`), pushes the mailbox, dispatches with `MAKE_TARGET="done FULL=1"`. The build's `bypass-audit` opens the full scope only to that committed entry (R11). |

`buildspec/merge.yml` / `check.yml` gain: `make $MAKE_TARGET` instead of a fixed `make done`; on a FULL run `perf-gate` takes the `-start` in a worktree at the pre-merge `origin/main` and the `-end` on the merge (no standalone bookend run); on a
FULL run, upload `dev/perf-log/*` produced in the build as artifacts; the dispatcher downloads them.

`sync-with-main.sh sync-in` becomes:

```
git fetch origin                                                     (GitHub)
flock $LOCK git -C /gm-assistant pull --ff-only origin main || die "mirror cannot fast-forward - someone committed in /gm-assistant"
render_sync                                                          (in the mirror, cache-short-circuited)
[clean clone only] git pull --no-rebase origin main                  (unchanged)
```

`perf-gate` pairs `-start`/`-end` on `(host, image)` and refuses a cross-machine pair by name.

## Second amendment: the dispatch sequence (every remote target), and FULL on both paths

`ci-merge` / `ci-check`, in either scope, run this sequence (FR-033..FR-037):

```
0. [FULL only] bypass-audit prompt, locally; cancel -> stop.          (existing)
1. conditions (route, feature-complete for merge, state, verified?)   (FR-007..FR-013; free)
2. lint + format + typecheck locally                                  (~5 s; fail -> stop, NO build)
3. start_build(project, sourceVersion=mailbox) -> build_id            (build parks at step "wait-go")
4. make reference locally (all tiers' reference maps, parallel OK)    (~26 s today)
5a. any red -> stop_build(build_id); state <- failed-gate; report     (queued: free; started: partial minute)
5b. all green -> put s3://bucket/go/<build_id>; stream log; exit with build status
```

`buildspec/*.yml` gain a first phase `wait-go`: poll `go/<build-id>` every 2 s for ≤ 120 s; absent
-> `exit 1` "aborted: no go signal"; present -> delete it and continue. Then, for FULL: `make done
FULL=1` where `done` now runs `bypass-audit` (build-side door, R11) THEN `reference` THEN the phases.

`ci-check FULL=1` is back (third request): same sequence, check project, no push to main, FULL
verified record written on green.
