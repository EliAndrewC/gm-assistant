# Research: The Merge Gate Runs on AWS CodeBuild, and Only When It Must

Every finding below is either MEASURED (a command was run and its output is quoted) or VERIFIED
(a mechanism was exercised locally). Nothing here is reasoned from documentation alone; where a
number is still unmeasured it says so and names the task that measures it.

## R1 - "Our work" is the diff from the merge base, not from where main was

**Decision**: the delta is `git diff --name-only $(git merge-base origin/main HEAD) HEAD`, equivalently
`git diff --name-only origin/main...HEAD` (three-dot).

**Verified** 2026-08-24 in the clone: after a sync-in that merged main, both forms list only the files
this clone's own commits changed; a clone whose HEAD equals main (just after a push) lists nothing.
A merge commit of main into the clone moves the merge base forward to main's tip, so the content main
contributed drops out of the delta automatically - no per-commit filtering of merge commits is
needed. The alternative (`git log --no-merges --name-only origin/main..HEAD`) was rejected: it
double-counts a file touched in two of our commits and reverted in a third, and misses nothing the
merge-base diff catches.

**Consequence for FR-007**: correct by construction as long as `origin/main` is the LATEST main at
dispatch time - which is why dispatch fetches first (R7).

## R2 - The verified record is keyed by the tree, and that is content identity

**Verified** 2026-08-24: `git commit-tree -p HEAD -m x HEAD^{tree}` produces a commit with a new hash
and the identical tree `1fe47e49...`. Two merges of the same work with the same main are exactly this
case (different timestamps, same content). Keying by commit would re-run the gate for a tree it has
already verified, which is the redundancy the GM asked to remove.

**Decision**: the build records `verified/<tree-sha>.json` after a green gate; the merge action
computes the tree the push WOULD produce (`git merge-tree --write-tree origin/main HEAD`, git >= 2.38,
no checkout needed) and looks it up before dispatching. `git merge-tree` also reports conflicts
without touching the working tree, which is the local pre-check that saves a paid build on a conflict.

## R3 - A non-fast-forward push is the compare-and-swap; no lock is needed on GitHub

**Verified**: git refuses a non-fast-forward push by default, and the `main` ruleset (created
2026-08-24: block force pushes, restrict deletions) removes the `--force` escape for every credential
including the build's. So if main advanced between the build's fetch and its push, the push fails
and the build fails with it - nothing untested lands. Concurrency 1 on the merge project makes this
rare; the ruleset makes it safe.

**Consequence for FR-003**: the build MUST push with plain `git push origin HEAD:main` and treat a
rejection as a build failure with the message "main moved; re-run". No retry loop inside the build -
a retry would re-merge and re-test, which is a new build's job and a new build's cost line.

## R4 - Source reaches the build by a mailbox branch, not a tarball

**Decision**: the clone pushes `HEAD:refs/heads/session/<clone-name>` to GitHub; the build fetches
that ref. Declined: uploading a tarball or `git bundle` to S3. The mailbox costs nothing extra (the
repository is public; the GitHub token is already provisioned; S3 would need a second credential path
into the build), gives the build real git history for the merge, and is what every CI on GitHub does.
The branch is deleted by the build on success and left in place on failure so the session can inspect
what was tested.

**Cost**: a push carries only the clone's new objects. Unmeasured but bounded by the size of the
delta; the measurement task records it alongside provisioning.

## R5 - Streaming the build log back is a poll of CodeBuild, inside one process, and that is allowed

**Measured** 2026-08-24 (smoke tests in this session): `start_build` returns a build id immediately;
`batch_get_builds` reports phase-by-phase status; CloudWatch `get_log_events` on the build's stream
returns lines as they are written. A dispatcher that loops on these with a 10-second sleep, prints new
log lines, and exits with the build's status behaves exactly like today's backgrounded `make done`
from the session's side (FR-019).

**Against the no-poll rule**: `scripts/no-poll-hooks.sh` inspects the COMMAND TEXT a session types
for `pgrep -f`, `sleep`-loops and the like. The dispatcher's polling is inside a Python process the
session started once and backgrounded, which is the sanctioned shape ("background the final gate and
act on the notification"). No `POLL_OK` is needed and none is added.

## R6 - The verification state reuses `gate-stamp`'s content hash rather than inventing one

**Verified**: `scripts/gate-stamp.py` exposes `hash_files(files)` and `_py_files(root, area)` -
order-independent content hash of every tracked-or-untracked `.py` in the diagram area, with a
selftest proving it bites on a changed or deleted file.

**Decision**: the verification state (FR-012) is a small JSON file in the clone's `.git/` -
`{event: green-local | failed-gate, target, utc, hash}` - written by the Makefile targets `quick`,
`reference`, `test-file` and `done` (the local one) on completion, where `hash` is that same content
hash at the time of the run. "A source edit resets the state" is then not an event to catch: at
dispatch time the current hash is recomputed and compared, and a mismatch is "no green local check
since the last edit". This is exactly how `gate-stamp --check` already reasons, and it needs no hook
to observe edits.

Declined: extending `scripts/gate-hooks.sh` (a `PreToolUse` hook keyed by session id under
`/tmp/claude-gate`). That state is per HARNESS SESSION and vanishes with `/tmp`; the verification
state has to be per CLONE and survive a session restart, because a merge can happen a day after the
local check that vouches for it.

## R7 - Moving `origin` to GitHub touches five call sites, all found

**Measured** (`grep -rn 'origin/main\|origin main' scripts/ .claude/skills/diagram/Makefile`):
`sync-with-main.sh` (sync-in pull, `gate-stamp --check origin/main`, the `base=` capture, the locked
pull+push), `review-gate.sh` (default range `origin/main..HEAD`), `gate-stamp.py` (`--check` takes
the base as an argument), and two comments. `no-branch-hooks.sh` and `repo-safety-hooks.sh` mention
the words only in prose.

**Decision**: a session clone's `origin` becomes GitHub (`ssh://git@github.com/EliAndrewC/gm-assistant`,
exactly what `/gm-assistant`'s own `origin` is today). Every `origin/main` reference then means
"GitHub main" with no edit, and sync-in pulls the latest main directly rather than through the
mirror. `/gm-assistant` keeps its remote and gains nothing: it is updated by `git -C /gm-assistant
pull --ff-only origin main` under the ritual lock after every landing, and render-sync runs there as
now. Existing clones need a one-time `git remote set-url origin <github>`; the clone-creation step
in CLAUDE.md changes from `git clone /gm-assistant` to a clone of GitHub (or a local clone followed by
the set-url, which is faster and keeps the objects local).

**What the direct route does**: `git push origin HEAD:main` from the clone, fast-forward only,
preceded by the same local guards as today. `updateInstead` on `/gm-assistant` becomes irrelevant
(nothing pushes to it any more) and is left configured - it is harmless.

## R8 - Only the build can write a verified record, and that is an IAM change

**Verified**: the build's service role (`gm-assistant-codebuild-role`) has `s3:PutObject` on the CI
bucket; the session's user (`gm-assistant-ci`) also has `s3:PutObject` on the whole bucket today.
FR-016 requires the session to be UNABLE to write a record.

**Decision**: the bucket policy denies `s3:PutObject` under `verified/` to everyone except the
service role. This is an infrastructure edit outside the session's own permissions - it needs the
`tempadmin` key reactivated for one call, and the task list says so explicitly. Until it is done,
FR-016's "MUST be unable" is not true, and the task is not ticked.

## R9 - What is still unmeasured, and which task measures it

| quantity | status | task |
|---|---|---|
| `make done` wall-clock on `xlarge` | unmeasured | T-measure (one paid build, ~$0.45) |
| same on `2xlarge` | unmeasured | T-measure (one paid build, ~$1.20) - decides the compute type |
| provisioning with the custom ECR image | unmeasured (20 s / 7 s on the stock image) | T-measure |
| mailbox push size and time | unmeasured | T-measure |
| local `make done` before/after this feature | to be taken in the baseline task | T-baseline |

The compute type is chosen AFTER T-measure, by the number, and recorded in `timings.md`.

## R10 - Dependencies

`boto3` is not in any lockfile today (installed ad hoc in this session). It becomes a container
dependency in `container-scripts/setup-dev-env.sh` and is pinned in the diagram skill's
`requirements` per Principle X. The build image needs no boto3: the build talks to S3 through the
AWS CLI that CodeBuild's environment already carries.
