# Quickstart: verifying feature 128 by hand

Everything here is in a session clone. Nothing here spends money except §4 and §5, and each says
what it costs.

## 1. The delta and the route (free)

```
make ci-status
```

Expect: the merge base, the list of files this clone changed, which of them are engine paths, the
route (DIRECT / GATED), the VerificationState, whether the would-be tree is already verified, and
month-to-date remote spend. Change a `.md` under the skill and re-run: still DIRECT. Touch a `.py`:
GATED.

## 2. The refusals (free - each must start NO build; check the CodeBuild console shows none)

| set up | run | expect |
|---|---|---|
| a docs-only delta | `scripts/sync-with-main.sh push` | pushes directly; "no diagram code in your delta" |
| an engine delta, `tasks.md` with an open box, `SPECIFY_FEATURE` set | same | REFUSE feature-complete, names the open tasks |
| an engine delta, last event `failed-gate` | same | REFUSE green-local-since-edit, names `make quick` |
| an engine delta, `make quick` green, then edit a `.py` | same | REFUSE: hash mismatch, "green run vouched for different code" |
| the breaker tripped (attach the deny policy by hand, admin key) | same | REFUSE breaker, names the IAM detach action |

## 3. The verification state (free)

`make quick` -> `cat .git/verification-state.json` shows `green-local` with the current hash.
Break a test, `make done` locally -> `failed-gate`. Fix it, `make reference` -> `green-local`.

## 4. The iteration check (~$0.45 per run at xlarge, until measured)

```
make ci-check
```

Expect: the mailbox branch appears on GitHub; a build on `gm-assistant-check`; the log streams into
the terminal; exit status equals the build's; a run-log entry with `where: codebuild` and a cost;
on green an object `verified/<tree>.json` in the bucket. `make ci-status` now says the tree is
verified.

## 5. The merge (one paid build, or none if §4 just ran on the same tree)

```
scripts/sync-with-main.sh done
```

Expect, if §4 verified this tree and main has not moved: "SKIP-VERIFIED", a direct push, no build.
Otherwise: a build on `gm-assistant-merge` that merges main, gates, pushes `HEAD:main`, deletes the
mailbox; the clone fast-forwards to it; `/gm-assistant` fast-forwards to it; render-sync runs there.
`git -C /gm-assistant log -1` and GitHub's `main` show the same commit.

## 6. What the guards must refuse (free)

- `python3 -m l7r.diagram.ci merge` outside make -> refused, names `make ci-merge`.
- `make ci-image` backgrounded -> refused (no terminal to answer the prompt).
- A hand-written `verified/<tree>.json` uploaded with the session's key -> `AccessDenied`.
- `git push --force origin main` from anywhere -> refused by the hook locally, and by the ruleset if
  it ever reached GitHub.

## 7. The full sweep on CodeBuild (amendment; one FULL build ≈ $0.50-1.00 until measured)

```
scripts/sync-with-main.sh done FULL=1        (the merge action only - the iteration check stays reference scope)
```

- Press Enter at the prompt: "Cancelled - good call", `cancelled` logged, NO build.
- Give a reason: a commit `chore: authorize FULL sweep - <reason>` appears, the mailbox is pushed,
  the build log shows `bypass-audit: permitted entry <file> authorizes FULL`, every pool map and
  the ratchet run, `perf-gate` runs, snapshots land in `dev/perf-log/` with `host: codebuild:...`.
- Backgrounded (`... > log 2>&1 &`): refused locally by the existing guard; NO build.
- Hand-push a mailbox WITHOUT the entry and start a FULL build from the console: the build refuses
  the full scope and fails - `verified/` gets no FULL record.

## 8. Sync at the tooling level (amendment; free)

Push a docs commit to GitHub `main` from your laptop. Send any message to a session. Then:
`git -C /gm-assistant log -1`, the clone's `git log -1`, and the mirror's `pool/index.html` mtime
all reflect it. Commit by hand in `/gm-assistant` (don't - but for the test): the next turn's
sync-in stops with "mirror cannot fast-forward".
