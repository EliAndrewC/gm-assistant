#!/usr/bin/env bash
# ritual.sh - the session-clone git ritual, encoded as a script.
#
# WHY (GM 2026-07-21): "if you're having to just remember to run the right commands in the right
# order then that seems error prone" - it was. Incidents that shaped this script, all from sessions
# hand-typing the ritual: a push raced another session because the flock was skipped; a render
# rsync ran from the wrong cwd and copied nothing; a cp with 2>/dev/null swallowed its own failure
# and the GM saw stale maps; a Mode A generator run from the skill dir wrote its cwd-relative
# outputs to the wrong path, which then got committed. The DOCTRINE lives in CLAUDE.md ("Session
# clones" / "Stop-work ritual") - this script is that doctrine made mechanical; if the two ever
# disagree, CLAUDE.md wins and this script has a bug.
#
# Run from anywhere INSIDE a session clone. Subcommands:
#   sync-in         start-of-work pull from main (near-free; almost always a fast-forward)
#   push            stop-work: refuse dirty tree, locked pull+push, overlap advisory (exit 3 =
#                   the pull merged other sessions' edits into files your commits touched -
#                   rerun the relevant gate NOW and fix forward)
#   render-sync     tip-guarded, locked, checksum-VERIFIED copy of the diagram pool renders into
#                   main. --regen first regenerates every map, running each gen from its OWN
#                   directory (Mode A outputs are cwd-relative - the trap this kills).
#   done            push, then render-sync (the common full stop-work)
set -euo pipefail

MAIN=/gm-assistant
LOCK=$MAIN/.clones/.ritual.lock
POOL=.claude/skills/diagram/pool

die() { echo "ritual: $*" >&2; exit 1; }

ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || die "not inside a git checkout"
case "$ROOT" in
  "$MAIN") die "this is MAIN, not a clone - the ritual runs from a session clone (CLAUDE.md 'Session clones')" ;;
  "$MAIN"/.clones/*) ;;
  *) die "$ROOT is not a session clone under $MAIN/.clones/" ;;
esac
cd "$ROOT"

sync_in() {
  git pull --no-rebase origin main
}

push_cmd() {
  [ -z "$(git status --porcelain)" ] || die "uncommitted changes - commit first (the ritual never writes your commit for you)"
  # files OUR unpushed commits touch, captured BEFORE the pull so the overlap test is honest
  local base ours theirs overlap
  base=$(git rev-parse origin/main)
  ours=$(git diff --name-only "$base"...HEAD | sort -u)
  # pull+push as ONE locked unit: no other session can slip a push into the gap (CLAUDE.md step 2)
  flock "$LOCK" sh -c 'git pull --no-rebase origin main && git push origin main'
  theirs=$(git diff --name-only "$base" origin/main | sort -u)
  overlap=$(comm -12 <(printf '%s\n' "$ours") <(printf '%s\n' "$theirs"))
  if [ -n "$overlap" ]; then
    echo "ritual: PUSHED, but the pull auto-merged other sessions' edits into files your commits touched:" >&2
    printf '  %s\n' $overlap >&2
    echo "ritual: rerun the relevant gate NOW and fix forward (CLAUDE.md stop-work step 3)" >&2
    exit 3
  fi
  echo "ritual: pushed clean (no overlap with incoming changes)"
}

regen() {
  # every gen runs from ITS OWN directory: Mode B gens are cwd-independent (they use __file__),
  # Mode A gens write cwd-relative - running them anywhere else scatters outputs (the trap).
  local g d
  for g in "$POOL"/*/*.gen.py; do
    d=$(dirname "$g")
    ( cd "$d" && python3 "$(basename "$g")" >/dev/null ) || die "generator failed: $g"
  done
  echo "ritual: all pool generators re-run"
}

render_sync() {
  [ "${1:-}" = "--regen" ] && regen
  # TIP-GUARD + copy under the lock; -rt not -a (rootless-podman ownership); no --delete (a clone
  # that never built another session's map must not wipe main's render of it). CLAUDE.md step 5.
  flock "$LOCK" sh -c "
    [ \"\$(git -C '$ROOT' rev-parse HEAD)\" = \"\$(git -C '$MAIN' rev-parse HEAD)\" ] \
      || { echo 'ritual: TIP-GUARD refused - clone is not at main HEAD; pull, re-gate, re-render first' >&2; exit 1; }
    rsync -rt --include='*/' --include='*.svg' --include='*.png' --exclude='*' '$ROOT/$POOL/' '$MAIN/$POOL/'
  "
  # VERIFY every render the clone has: report from checksum evidence, never from rsync exiting 0
  local f rel bad=0 n=0
  while IFS= read -r f; do
    rel=${f#"$ROOT/$POOL/"}
    n=$((n + 1))
    if ! cmp -s "$f" "$MAIN/$POOL/$rel"; then
      echo "ritual: VERIFY FAILED: $rel differs between clone and main after copy" >&2
      bad=1
    fi
  done < <(find "$ROOT/$POOL" -name '*.png' -o -name '*.svg')
  [ "$bad" = 0 ] || exit 1
  echo "ritual: render sync verified - $n files byte-identical in main"
}

case "${1:-}" in
  sync-in)     sync_in ;;
  push)        push_cmd ;;
  render-sync) shift; render_sync "${1:-}" ;;
  done)        push_cmd; render_sync ;;
  *)           die "usage: ritual.sh sync-in | push | render-sync [--regen] | done" ;;
esac
