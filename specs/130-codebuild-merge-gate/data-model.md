# Data model: feature 128

Five small records. None is a database; each is a file or an object with a fixed shape, and the
shape is what the tests pin.

## Delta (computed, never stored)

```
Delta
  base:        commit   merge-base(origin/main, HEAD)
  files:       [path]   git diff --name-only base HEAD
  engine:      [path]   subset matching ENGINE_PATHS
  route:       DIRECT | GATED     GATED iff engine is non-empty
  reason:      str      one line saying why (which files decided it)
```

`ENGINE_PATHS` (FR-008), one list in one place, dispatch only:

```
.claude/skills/diagram/l7r/**/*.py
.claude/skills/diagram/tests/**            (a test change can change what the gate proves)
.claude/skills/diagram/pool/**/*.gen.py
.claude/skills/diagram/pool/**/*.json      (a manifest is a generator's output under test)
.claude/skills/diagram/Makefile
.claude/skills/diagram/pyproject.toml
.claude/skills/diagram/requirements*.txt
```

Everything else under the skill is NOT engine: `*.md` anywhere, `dev/**` (the three append-only logs,
the stage plates), `future-work/`, `settlements/`, `buildings/`, `research/`, `pool/**/*.notes.md`,
`pool/**/*.png`, `pool/**/*.svg`. The list is asserted by a test that walks a fixture of every path
kind and pins its classification, so a new kind of file cannot be silently engine or silently docs.

## VerificationState (per clone, `.git/verification-state.json`)

```
VerificationState
  event:   green-local | failed-gate
  target:  quick | reference | test-file | done | ci-check | ci-merge
  utc:     iso8601
  hash:    sha256   gate-stamp.hash_files(_py_files(root, diagram area)) at the time of the event
  commit:  short sha
```

Transitions (FR-012):

| current | on | becomes |
|---|---|---|
| any | `quick` / `reference` / `test-file` / local `done` exit 0 | green-local (hash = now) |
| any | local `done` exit non-zero, remote build not SUCCEEDED | failed-gate |
| green-local, hash != now | dispatch attempted | refuse: "green run vouched for different code" |
| green-local, hash == now | dispatch attempted | permitted |
| failed-gate | dispatch attempted | refuse: "last gate failed; run a local target first" |
| absent | dispatch attempted | refuse: "no local check recorded" |

## VerifiedRecord (S3, `verified/<tree-sha>.json`, written ONLY by the build)

```
VerifiedRecord
  tree:      sha1     the tree the build pushed (merge) or would have pushed (check)
  build_id:  str      gm-assistant-<project>:<uuid>
  project:   merge | check
  utc:       iso8601
  main:      sha1     the main commit merged in
  work:      sha1     the mailbox commit tested
  minutes:   number   billed build minutes (phases summed, rounded up)
```

Looked up by the merge action with the tree from `git merge-tree --write-tree origin/main HEAD`.
Never deleted; a bucket lifecycle rule expires objects after 14 days, which is longer than any
work-in-progress should sit unmerged.

## RemoteRunLogEntry (local, `dev/run-log/<utc>-<pid>.json`, the existing shape plus four fields)

```
RunLogEntry (existing)
  utc, target, scope, seconds, result, commit
RemoteRunLogEntry = RunLogEntry +
  where:     codebuild
  build_id:  str
  minutes:   number     billed
  cost_usd:  number     minutes * RATE_PER_MIN for the project's compute type
```

`make audit` sums `cost_usd` for the current month over entries with `where == codebuild` and prints
it under a new "Remote spend" heading. The rate lives in ONE place (the dispatcher's config) and is
the same number the Lambda alert uses.

## DispatchDecision (printed, and logged as the `reason` on the run-log entry)

```
DispatchDecision
  conditions: [ (name, passed: bool, why: str) ]
     route-is-gated, feature-complete (merge only), green-local-since-edit,
     tree-not-already-verified, breaker-not-tripped
  estimate:   { minutes, cost_usd, month_to_date_usd }
  verdict:    DISPATCH | SKIP-VERIFIED | REFUSE(<first failing condition>)
```

Every condition is evaluated and printed even after one fails, so the session sees the whole picture
in one turn (the project's "report ALL failures together" rule).
