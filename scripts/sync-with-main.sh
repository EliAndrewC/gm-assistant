#!/usr/bin/env bash
# sync-with-main.sh - keep a session clone and main in sync: pull main's tip into the clone
# (sync-in), push the clone's committed work back (push), and refresh main's diagram renders
# (render-sync). Encodes the stop-work ritual from CLAUDE.md as a script. (Renamed from ritual.sh,
# GM 2026-07-21: name the purpose, not the culture.)
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
# RENDER MODEL (GM 2026-07-22): renders no longer flow clone -> main by copy. render-sync
# REGENERATES main's diagram renders in place from main's own committed tip (via pipeline/render_cache.py),
# so a render in main is a pure function of main's code and can never be a stale copy. A content
# hash stamped into each derived svg makes the regen a cheap no-op when nothing a map depends on
# changed. This retired the whole copy machinery: no clone-side pre-render, no rsync, no tip-guard,
# no byte-verify, and sync-in no longer pulls renders into the clone.
#
# Run from anywhere INSIDE a session clone. Subcommands:
#   sync-in         start-of-work pull from main (near-free; almost always a fast-forward)
#   push            stop-work: refuse dirty tree, locked pull+push, overlap advisory (exit 3 =
#                   the pull merged other sessions' edits into files your commits touched -
#                   rerun the relevant gate NOW and fix forward)
#   render-sync     locked, cache-short-circuited regen of main's diagram renders IN PLACE from
#                   main's tip (GM_ASSISTANT_ALLOW_MAIN=1 for that one sanctioned regen-in-main)
#   done            push, then render-sync (the common full stop-work)
set -euo pipefail

MAIN=${CLONE_MAIN:-/gm-assistant}   # CLONE_MAIN: test seam only; production is always /gm-assistant
LOCK=$MAIN/.clones/.ritual.lock   # keep this NAME: it is the cross-session lock convention in CLAUDE.md - renaming it would stop serializing against other sessions
POOL=.claude/skills/diagram/pool
SKILL_DIR=.claude/skills/diagram
RENDER_CACHE_MOD=pipeline.render_cache   # run as a MODULE from SKILL_DIR: it imports its package siblings relatively

die() { echo "sync-with-main: $*" >&2; exit 1; }

ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || die "not inside a git checkout"
case "$ROOT" in
  "$MAIN") die "this is MAIN, not a clone - the ritual runs from a session clone (CLAUDE.md 'Session clones')" ;;
  "$MAIN"/.clones/*) ;;
  *) die "$ROOT is not a session clone under $MAIN/.clones/" ;;
esac
# 'gm-assistant' is a FORBIDDEN clone name (GM 2026-07-22): it is the repository, not a session,
# and being the old unnamed-default is what let two sessions collide in one working tree. The
# ritual refuses to run from it so no work can be pushed out of it - rename the session distinctly.
[ "$(basename "$ROOT")" = "gm-assistant" ] && die "'.clones/gm-assistant' is a FORBIDDEN clone name - 'gm-assistant' is the repository, not a session. Ask the GM to /rename this session to something distinct, then run the ritual from .clones/<that-name>. (CLAUDE.md 'Session clones')"
cd "$ROOT"

sync_in() {
  git pull --no-rebase origin main
  # No render pull-in anymore (GM 2026-07-22): its old rationale was that a clone's stale renders
  # would flow back into main via render-sync's copy - but render-sync no longer copies anything,
  # it REGENERATES main in place, so nothing flows clone -> main and the clone never needs main's
  # renders. A clone regenerates whatever map it iterates on; the GM browses renders in main.
  date > "$ROOT/.git/sync-with-main.stamp"
  echo "sync-with-main: clone synced with main (git)"
}

push_cmd() {
  [ -z "$(git status --porcelain)" ] || die "uncommitted changes - commit first (the ritual never writes your commit for you)"
  # DUPLICATE-DEF GUARD (GM 2026-07-24): a cross-session merge gave test_settlement.py two
  # _city() helpers - the later silently shadowed the earlier and broke a seeded test - and ruff
  # F811 cannot see this class (pyflakes only flags UNUSED redefinitions; an early helper is
  # always used before the shadow). Screened HERE so every push is covered, merges and
  # docs-only pushes included - the gates do not necessarily run for those. The selftest runs
  # first: a checker that cannot prove it still bites is the failure mode that motivated it.
  python3 "$ROOT/scripts/check-duplicate-defs.py" --selftest >/dev/null || die "check-duplicate-defs selftest failed - the guard itself is broken; fix scripts/check-duplicate-defs.py before pushing"
  python3 "$ROOT/scripts/check-duplicate-defs.py" "$ROOT" || die "duplicate top-level definitions (above) - a later def silently shadows the earlier; fix before pushing"
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
  flock "$LOCK" sh -c 'git pull --no-rebase origin main && git push origin HEAD:main'
  theirs=$(git diff --name-only "$before"..HEAD | sort -u)
  date > "$ROOT/.git/sync-with-main.stamp"  # post-push the clone is at main's tip = synced by definition
  overlap=$(comm -12 <(printf '%s\n' "$ours") <(printf '%s\n' "$theirs"))
  if [ -n "$overlap" ]; then
    echo "sync-with-main: PUSHED, but the pull auto-merged other sessions' edits into files your commits touched:" >&2
    printf '  %s\n' $overlap >&2
    echo "sync-with-main: rerun the relevant gate NOW and fix forward (CLAUDE.md stop-work step 3)" >&2
    # ...AND SAY THAT MAIN'S PICTURES ARE NOW STALE. `done` is push-then-render-sync, so this exit
    # skips render-sync and main keeps whatever renders it had - silently. The GM browses renders in
    # main, and on 2026-08-12 that cost a round trip: two syncs in a row hit this branch, so a map
    # whose connector had been re-routed right across the sheet still showed the old route, and the
    # GM reported the change had not happened. Regenerating from a tip whose gate has not been
    # re-run would be the wrong cure, so the exit stays - but the tip belongs in the message rather
    # than in a doc nobody re-reads (project rule: tips live in error output).
    echo "sync-with-main: NOTE - render-sync did NOT run, so main's diagram renders are now STALE." >&2
    echo "sync-with-main: once the gate is green again, run:  scripts/sync-with-main.sh render-sync" >&2
    exit 3
  fi
  echo "sync-with-main: pushed clean (no overlap with incoming changes)"
}

render_sync() {
  # REGENERATE main's diagram renders IN PLACE from main's own tip (GM 2026-07-22, replacing the
  # old build-in-clone-then-rsync-copy machinery). Renders now become a pure function of main's
  # committed code - nothing is copied, so nothing can be copied stale (the fragility that copy
  # approach had: whether a clone had touched a given render was situational, so a stale copy
  # could linger in main). pipeline/render_cache.py runs each generator FROM ITS OWN DIRECTORY (the Mode A
  # cwd trap) and short-circuits on a content hash stamped into each derived svg: an unconditional
  # post-push regen is therefore cheap - only maps whose source actually changed re-run, so a push
  # that touched no map's inputs costs ~0.3s while still self-healing every render from tip.
  #
  # Under the ritual LOCK for the whole regen: main is a push-to-checkout target (updateInstead),
  # so another session's push mid-regen would rewrite the engine under us and mix tips across maps.
  # GM_ASSISTANT_ALLOW_MAIN=1 stands the engine's main-tree guard down for this ONE sanctioned
  # regen-in-main. No tip-guard is needed - regenerating whatever tip main currently holds is
  # correct, and a second runner finds every stamp fresh and skips (the cache makes redundant
  # regens ~free, which is what retires the old TIP-GUARD/last-writer-wins hazard entirely).
  (cd "$MAIN/$SKILL_DIR" && flock "$LOCK" env GM_ASSISTANT_ALLOW_MAIN=1 python3 -m "$RENDER_CACHE_MOD" --pool "$MAIN/$POOL" --main-repo "$MAIN")
  # A generator writes its TRACKED .json (and a Mode A its tracked .svg) alongside the gitignored
  # renders; a deterministic gen reproduces those byte-identically, so main stays clean. If any
  # tracked pool file is left dirty, a generator is nondeterministic - surface it loudly (it would
  # also block the next session's updateInstead push), but do not auto-revert: the GM decides.
  local dirty
  dirty=$(git -C "$MAIN" status --porcelain -- "$POOL" | grep -E '^[ MARC]M ' || true)
  if [ -n "$dirty" ]; then
    echo "sync-with-main: WARNING - regen left tracked pool files dirty in main (a generator is nondeterministic):" >&2
    printf '%s\n' "$dirty" >&2
    echo "sync-with-main: investigate before the next push - main must be clean for updateInstead" >&2
  fi
}

case "${1:-}" in
  sync-in)     sync_in ;;
  push)        push_cmd ;;
  render-sync) render_sync ;;
  done)        push_cmd; render_sync ;;
  *)           die "usage: sync-with-main.sh sync-in | push | render-sync | done" ;;
esac
