#!/usr/bin/env bash
# sync-with-main.sh - keep a session clone and main in sync: pull main's tip into the clone
# (sync-in) and push the clone's committed work back (push). Encodes the stop-work procedure from
# CLAUDE.md as a script. (Renamed from ritual.sh, GM 2026-07-21: name the purpose, not the culture; and the word "ritual" left the process vocabulary on 2026-08-25 - rituals belong to Rokugan, merging into main is a procedure.)
#
# WHY (GM 2026-07-21): "if you're having to just remember to run the right commands in the right
# order then that seems error prone" - it was. Incidents that shaped this script, all from sessions
# hand-typing the procedure: a push raced another session because the flock was skipped; a render
# rsync ran from the wrong cwd and copied nothing; a cp with 2>/dev/null swallowed its own failure
# and the GM saw stale maps. The DOCTRINE lives in CLAUDE.md ("Session clones" / "Stop-work
# procedure") - this script is that doctrine made mechanical; if the two ever disagree, CLAUDE.md wins
# and this script has a bug.
#
# NO RENDER-SYNC ANY MORE (GM 2026-08-25, the first session after feature 131). The third subcommand
# used to regenerate main's diagram renders in place after every push - gitignored PNG/SVG the GM
# browsed in main's tree. Every one of those artifacts left with the diagram skill for
# https://github.com/EliAndrewC/diagram, and nothing left in this repository derives a gitignored
# artifact that main has to hold: the webapp's pools are tracked files, the name/weather/dream
# skills generate into tracked files or into chat. So the stop-work procedure here is push, full stop.
# `done` survives as the documented name of "the stop-work command" and is now an alias of `push`.
# The diagram repository keeps its own copy of this script with render-sync in it.
#
# Run from anywhere INSIDE a session clone. Subcommands:
#   sync-in         start-of-work pull from main (near-free; almost always a fast-forward)
#   push            stop-work: refuse dirty tree, locked pull+push, overlap advisory (exit 3 =
#                   the pull merged other sessions' edits into files your commits touched -
#                   rerun the relevant gate NOW and fix forward)
#   done            alias of push (the stop-work command CLAUDE.md names)
set -euo pipefail

die() { echo "sync-with-main: $*" >&2; exit 1; }

# THE ROOT IS DERIVED, NOT HARDCODED (feature 131, 2026-08-25). A session clone lives at
# <main>/.clones/<name>, so main is the clone's grandparent - true for gm-assistant at /gm-assistant
# and for the diagram repository at /diagram, with no per-repo edit. CLONE_MAIN stays as the test
# seam. Before this the script hardcoded /gm-assistant, which is the kind of reference the split
# had to sweep; deriving it means the NEXT move is free.
ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || die "not inside a git checkout"
if [ -n "${CLONE_MAIN:-}" ]; then MAIN=$CLONE_MAIN
elif [ "$(basename "$(dirname "$ROOT")")" = ".clones" ]; then MAIN=$(dirname "$(dirname "$ROOT")")
else MAIN=$ROOT; fi
LOCK=$MAIN/.clones/.sync.lock   # keep this NAME: it is the cross-session lock convention in docs/session-clones.md - every session must lock the SAME file or the pull+push stops serializing (renamed from .ritual.lock 2026-08-25; a session on the old script name is briefly unserialized against one on the new - accepted, one-time)

case "$ROOT" in
  "$MAIN") die "this is MAIN, not a clone - the procedure runs from a session clone (CLAUDE.md 'Session clones')" ;;
  "$MAIN"/.clones/*) ;;
  *) die "$ROOT is not a session clone under $MAIN/.clones/" ;;
esac
# The repository's OWN NAME is a FORBIDDEN clone name (GM 2026-07-22, generalized 2026-08-25): it is
# the repository, not a session, and being the old unnamed-default is what let two sessions collide
# in one working tree. 'gm-assistant' stays forbidden everywhere for the same reason. The script
# refuses to run from such a clone so no work can be pushed out of it - rename the session distinctly.
case "$(basename "$ROOT")" in
  gm-assistant|"$(basename "$MAIN")") die "'.clones/$(basename "$ROOT")' is a FORBIDDEN clone name - it is the repository, not a session. Ask the GM to /rename this session to something distinct, then run the procedure from .clones/<that-name>. (CLAUDE.md 'Session clones')" ;;
esac
cd "$ROOT"

sync_in() {
  git pull --no-rebase origin main
  date > "$ROOT/.git/sync-with-main.stamp"
  echo "sync-with-main: clone synced with main (git)"
}

push_cmd() {
  [ -z "$(git status --porcelain)" ] || die "uncommitted changes - commit first (the script never writes your commit for you)"
  # DUPLICATE-DEF GUARD (GM 2026-07-24): a cross-session merge gave test_settlement.py two
  # _city() helpers - the later silently shadowed the earlier and broke a seeded test - and ruff
  # F811 cannot see this class (pyflakes only flags UNUSED redefinitions; an early helper is
  # always used before the shadow). Screened HERE so every push is covered, merges and
  # docs-only pushes included - the gates do not necessarily run for those. The selftest runs
  # first: a checker that cannot prove it still bites is the failure mode that motivated it.
  python3 "$ROOT/scripts/check-duplicate-defs.py" --selftest >/dev/null || die "check-duplicate-defs selftest failed - the guard itself is broken; fix scripts/check-duplicate-defs.py before pushing"
  python3 "$ROOT/scripts/check-duplicate-defs.py" "$ROOT" || die "duplicate top-level definitions (above) - a later def silently shadows the earlier; fix before pushing"
  # GREEN-GATE GUARD (constitution Principle XIII, GM 2026-08-17). The principle's enforcement
  # clause says this procedure "does not run to completion on a red or regressed state" - which was
  # ASPIRATIONAL until now: nothing here knew whether a gate had run, so compliance was a session
  # remembering to comply, the very shape the principle abolishes. Python-only and per-area, so a
  # docs-only push still skips the gate (CLAUDE.md) and a webapp change is not blocked by
  # another area's gate. Selftest FIRST, same reason check-duplicate-defs does it: a checker that cannot
  # prove it still bites is the failure mode that motivated it.
  if [ -n "${GATE_STAMP_OK:-}" ]; then
    echo "sync-with-main: green-gate guard BYPASSED - $GATE_STAMP_OK" >&2
  else
    python3 "$ROOT/scripts/gate-stamp.py" --selftest >/dev/null || die "gate-stamp selftest failed - the guard itself is broken; fix scripts/gate-stamp.py before pushing"
    python3 "$ROOT/scripts/gate-stamp.py" --check origin/main || die "push refused by the green-gate guard (above)"
  fi
  # files OUR unpushed commits touch, captured BEFORE the pull so the overlap test is honest.
  # INCOMING files = what the pull moves HEAD across - NOT a diff against post-push origin/main,
  # which contains our own commits and false-flags every push (the script's own first dogfood run
  # caught exactly that bug: a no-op pull reported our just-pushed files as overlap).
  local base before ours theirs overlap
  base=$(git rev-parse origin/main)
  before=$(git rev-parse HEAD)
  ours=$(git diff --name-only "$base"...HEAD | sort -u)
  # pull+push as ONE locked unit: no other session can slip a push into the gap (CLAUDE.md step 2).
  # HEAD:main, NOT main (GM 2026-07-27): `git push origin main` pushes the local REF NAMED main and
  # ignores what is checked out, so a session on any other branch silently pushed a stale ref and
  # got "! [rejected] main -> main (non-fast-forward)" while `git rev-list --count origin/main..HEAD`
  # reported it 4 ahead and 0 behind - every diagnostic says fast-forward and the error names a ref
  # you never touched. `HEAD:main` pushes what you actually committed.
  # THE MANDATED REVIEW IS CHECKED BEFORE THE PUSH, not after (feature 127 audit, 2026-08-24).
  # A spec ships with a fidelity verdict. It was constitutional and unenforced, and had already
  # been skipped in practice. Checked here because this is the moment work becomes everyone
  # else's problem.
  "$(dirname "$0")/review-gate.sh" || exit 1
  flock "$LOCK" sh -c 'git pull --no-rebase origin main && git push origin HEAD:main'
  theirs=$(git diff --name-only "$before"..HEAD | sort -u)
  date > "$ROOT/.git/sync-with-main.stamp"  # post-push the clone is at main's tip = synced by definition
  overlap=$(comm -12 <(printf '%s\n' "$ours") <(printf '%s\n' "$theirs"))
  if [ -n "$overlap" ]; then
    echo "sync-with-main: PUSHED, but the pull auto-merged other sessions' edits into files your commits touched:" >&2
    printf '  %s\n' $overlap >&2
    echo "sync-with-main: rerun the relevant gate NOW and fix forward (CLAUDE.md stop-work step 3)" >&2
    exit 3
  fi
  echo "sync-with-main: pushed clean (no overlap with incoming changes)"
}

case "${1:-}" in
  sync-in)     sync_in ;;
  push|done)   push_cmd ;;
  render-sync) echo "sync-with-main: render-sync no longer exists here - the diagram skill and its renders moved to https://github.com/EliAndrewC/diagram (feature 131); nothing in this repository derives a gitignored artifact into main. Use 'done'." >&2; exit 1 ;;
  *)           die "usage: sync-with-main.sh sync-in | push | done" ;;
esac
