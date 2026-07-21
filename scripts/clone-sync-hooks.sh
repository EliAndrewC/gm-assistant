#!/usr/bin/env bash
# clone-sync-hooks.sh - Claude Code harness hooks enforcing the session-clone sync discipline.
#
# WHY (GM 2026-07-21): sync-in at the start of each work unit "has been getting skipped a lot and
# I'm not sure how to enforce it" - memory-dependent steps do get skipped, so the harness enforces
# them instead. Wired from .claude/settings.json (project settings, committed):
#
#   UserPromptSubmit -> `prompt` mode: every time the GM sends a message, this session's known
#     clone is auto-synced with main (git pull + render pull-in via sync-with-main.sh sync-in) -
#     but ONLY when its tree is clean; a dirty tree means mid-task, and yanking main's tip into
#     half-done work would be sabotage. Stdout is injected into the model's context, so the model
#     also SEES the sync happen (or why it was skipped).
#
#   PreToolUse (Edit|Write|NotebookEdit) -> `pretool` mode: the backstop for the first edit of a
#     session (before any mapping exists) and for anything the prompt hook missed. Editing a file
#     inside a clone whose tree is CLEAN (= a work-unit boundary, nothing in flight) while its
#     HEAD is behind main's is blocked (exit 2) with instructions to run sync-in. A dirty tree is
#     always allowed - that is mid-task work. This call also records the session->clone mapping
#     (keyed by session_id under .clones/.session-clones/) that the prompt hook reads.
#
# HEAD equality, not timestamps, is the freshness test: it is the same invariant render-sync's
# tip-guard uses, needs no clock, and cannot rot. Renders stay safe separately - sync-in pulls
# main's renders into the clone, and render-sync always REGENERATES before copying out.
set -euo pipefail

MAIN=/gm-assistant
MAPDIR=$MAIN/.clones/.session-clones
MODE=${1:-}
INPUT=$(cat 2>/dev/null || true)

field() { # field <dotted.path> - pull a string field out of the hook's stdin JSON
  printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    for k in '$1'.split('.'):
        d = d.get(k, {}) if isinstance(d, dict) else {}
    print(d if isinstance(d, str) else '')
except Exception:
    print('')"
}

case $MODE in
  pretool)
    fp=$(field tool_input.file_path)
    case $fp in
      "$MAIN"/.clones/*/*) ;;
      *) exit 0 ;;  # not a clone file - this hook has no opinion
    esac
    rest=${fp#"$MAIN"/.clones/}
    clone=$MAIN/.clones/${rest%%/*}
    [ -d "$clone/.git" ] || exit 0
    sid=$(field session_id)
    if [ -n "$sid" ]; then
      mkdir -p "$MAPDIR"
      printf '%s' "$clone" > "$MAPDIR/$sid"
    fi
    # dirty tree = mid-task: always allowed (never stall in-flight work on a moving main)
    [ -n "$(git -C "$clone" status --porcelain 2>/dev/null)" ] && exit 0
    if [ "$(git -C "$clone" rev-parse HEAD 2>/dev/null)" != "$(git -C "$MAIN" rev-parse HEAD 2>/dev/null)" ]; then
      echo "BLOCKED: $clone has a clean tree (a new work unit) but its HEAD is behind main - new work must not build on a stale base. Run: cd $clone && scripts/sync-with-main.sh sync-in   (CLAUDE.md 'Session clones' / sync-in rule)" >&2
      exit 2
    fi
    exit 0
    ;;
  prompt)
    sid=$(field session_id)
    [ -n "$sid" ] && [ -f "$MAPDIR/$sid" ] || exit 0  # no known clone yet - silent (the pretool backstop covers the first edit)
    clone=$(cat "$MAPDIR/$sid")
    [ -d "$clone/.git" ] || exit 0
    if [ -n "$(git -C "$clone" status --porcelain 2>/dev/null)" ]; then
      echo "clone-sync: $clone has uncommitted work (mid-task) - auto sync-in skipped; finish and run sync-with-main.sh done"
      exit 0
    fi
    if out=$(cd "$clone" && scripts/sync-with-main.sh sync-in 2>&1); then
      echo "clone-sync: auto-synced $clone with main (git + renders)"
    else
      echo "clone-sync: auto sync-in FAILED in $clone - resolve before modifying the repo: $(printf '%s' "$out" | tail -2)"
    fi
    exit 0
    ;;
  *)
    echo "clone-sync-hooks: unknown mode '$MODE' (want: prompt | pretool)" >&2
    exit 1
    ;;
esac
