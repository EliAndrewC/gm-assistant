#!/usr/bin/env bash
# batching-hooks.sh - Claude Code harness hooks that BLOCK long runs of serial single-call turns.
#
# WHY (GM 2026-07-25): a transcript profile of a 69-minute feature found the largest remaining cost
# was not tool speed but turn STRUCTURE - 139 tool calls at 1.00 calls per turn, of which 104
# finished in under 2 seconds. Those 104 calls did 29 SECONDS of work between them and cost ~23
# MINUTES of model round-trip latency. Runs of consecutive single greps/reads are visible all over
# that transcript (six greps in a row, eight file reads in a row, ten git inspections in a row),
# every one of them independent and batchable.
#
# The project docs have told sessions to batch recon since 2026-07-20 and it happened ZERO times in
# those 139 calls. That is the point: "document it and rely on remembering" is not a control. This
# hook makes it one, the same way the coverage gate makes Principle X one.
#
# HOW IT DECIDES. Two facts, both measured rather than guessed:
#   - Calls in the SAME turn arrive milliseconds apart (the model emits them in one message); calls
#     in DIFFERENT turns are separated by a full round trip (~13s in the profiled session). A
#     >1000x gap needs no cleverness to classify - anything under SAME_TURN_MS is one turn.
#   - "Cheap" is the call's MEASURED duration (PostToolUse - PreToolUse), not a guess from the tool
#     name. A grep that takes 90s is real work; a Bash that takes 0.1s is recon.
# A "serial cheap turn" is a turn containing exactly ONE call that took under CHEAP_MS. STREAK
# counts them consecutively; ANY batched turn (2+ calls) or any slow call resets it to zero.
#
# WHAT IT DOES. At THRESHOLD consecutive serial cheap turns it BLOCKS one call, explaining what to
# do. It then allows again and only re-blocks after another THRESHOLD, so it can NEVER deadlock a
# genuinely serial chain (each read depending on the last): the worst case is one interruption per
# THRESHOLD calls, and the remedy - "send the rest together" - is exactly the desired behavior, so
# no override syntax is needed.
#
# Wired from .claude/settings.json alongside clone-sync-hooks.sh. Tested by test-batching-hooks.sh.
set -euo pipefail

MODE=${1:-}
INPUT=$(cat 2>/dev/null || true)

THRESHOLD=${BATCH_THRESHOLD:-6}      # serial cheap turns before a block
CHEAP_MS=${BATCH_CHEAP_MS:-2000}     # a call this fast is recon, not work
SAME_TURN_MS=${BATCH_SAME_TURN_MS:-3000}  # calls closer together than this are one turn
STATE_DIR=${BATCH_STATE_DIR:-/tmp/claude-batching}

# Only two fields are needed, so pull them with grep rather than paying python's startup on EVERY
# tool call (this hook runs hundreds of times per session - it must be effectively free).
json_str() { printf '%s' "$INPUT" | grep -o "\"$1\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" | head -1 | sed 's/.*:[[:space:]]*"//; s/"$//'; }
now_ms() { echo $(($(date +%s%N) / 1000000)); }

SID=$(json_str session_id); SID=${SID:-nosession}
TOOL=$(json_str tool_name); TOOL=${TOOL:-unknown}
mkdir -p "$STATE_DIR"
STATE="$STATE_DIR/${SID//[^A-Za-z0-9_-]/_}.state"

# state: last_pre_ms calls_this_turn streak last_block_streak
read -r LAST_PRE CALLS STREAK LAST_BLOCK < "$STATE" 2>/dev/null || true
LAST_PRE=${LAST_PRE:-0}; CALLS=${CALLS:-0}; STREAK=${STREAK:-0}; LAST_BLOCK=${LAST_BLOCK:-0}
NOW=$(now_ms)

case "$MODE" in
  pretool)
    GAP=$((NOW - LAST_PRE))
    if [ "$LAST_PRE" -gt 0 ] && [ "$GAP" -lt "$SAME_TURN_MS" ]; then
      CALLS=$((CALLS + 1))
      [ "$CALLS" -ge 2 ] && STREAK=0   # a batched turn: this is the behavior we want, reward it
    else
      CALLS=1
    fi
    if [ "$CALLS" -eq 1 ] && [ "$STREAK" -ge "$THRESHOLD" ] && [ $((STREAK - LAST_BLOCK)) -ge "$THRESHOLD" ]; then
      printf '%s %s %s %s\n' "$NOW" "$CALLS" "$STREAK" "$STREAK" > "$STATE"
      echo "BLOCKED: the last $STREAK turns EACH made a single quick read-only call - $STREAK model round trips (~$((STREAK * 13))s) for a few seconds of actual work. These reads/greps do not depend on each other; send them TOGETHER. Put every remaining lookup you already know you need into ONE message as parallel tool calls (or fold several greps into a single Bash command). Then continue. (CLAUDE.md 'Batch the rendered-map inspection' / 'Batch into fewer, bigger turns'. Measured 2026-07-25: 104 sub-2-second calls cost 23 minutes of latency for 29 seconds of work. This hook re-arms after another $THRESHOLD.)" >&2
      exit 2
    fi
    printf '%s %s %s %s\n' "$NOW" "$CALLS" "$STREAK" "$LAST_BLOCK" > "$STATE"
    ;;
  posttool)
    DUR=$((NOW - LAST_PRE))
    if [ "$CALLS" -eq 1 ] && [ "$DUR" -lt "$CHEAP_MS" ]; then
      STREAK=$((STREAK + 1))          # one call, and it was quick: a batchable turn
    else
      STREAK=0; LAST_BLOCK=0          # real work, or a batched turn: streak over
    fi
    printf '%s %s %s %s\n' "$LAST_PRE" "$CALLS" "$STREAK" "$LAST_BLOCK" > "$STATE"
    ;;
  status)   # for the tests and for a session that wants to see where it stands
    echo "tool=$TOOL streak=$STREAK calls_this_turn=$CALLS threshold=$THRESHOLD state=$STATE"
    ;;
  *)
    echo "batching-hooks: unknown mode '$MODE' (want: pretool | posttool | status)" >&2
    exit 1
    ;;
esac
exit 0
