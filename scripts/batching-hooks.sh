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
# WHY IT IS A ROLLING WINDOW, NOT A CONSECUTIVE STREAK (GM 2026-08-08). The first version counted
# CONSECUTIVE serial turns and reset to zero on any batched turn or any slow call. A profile of the
# label-resize session says that let almost everything through: **147 of 162 tool round trips (91%)
# made exactly one call**, costing **22.7 minutes of model latency for 4.0 minutes of work** - and
# in all of it the hook fired TWICE. The 15 batched turns were sprinkled through the serial runs,
# and each one erased a streak of 5 that was one turn from tripping. A single well-behaved turn
# should not buy absolution for the ten around it.
#
# So the counter is now "how many of the last WINDOW turns were serial-and-cheap", and a batched or
# slow turn merely ages out of the window instead of clearing it. THRESHOLD came down 6 -> 3 at the
# same time: at 9.2s of latency per round trip, a block costs one trip and saves two whenever it
# turns the next three single calls into one message, so it pays for itself immediately.
#
# Wired from .claude/settings.json alongside clone-sync-hooks.sh. Tested by test-batching-hooks.sh.
set -euo pipefail

MODE=${1:-}
INPUT=$(cat 2>/dev/null || true)

THRESHOLD=${BATCH_THRESHOLD:-3}      # serial cheap turns WITHIN THE WINDOW before a block
WINDOW=${BATCH_WINDOW:-6}            # how many recent turns the threshold is counted over
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
# .state2, not .state: the file format changed with the rolling window (2026-08-08) and a
# half-read old file would be counted as history. A new name retires them without a migration.
STATE="$STATE_DIR/${SID//[^A-Za-z0-9_-]/_}.state2"

# state: last_pre_ms calls_this_turn history   (history = one char per TURN, oldest first,
# '1' = serial and cheap, '0' = batched or real work; at most WINDOW chars)
read -r LAST_PRE CALLS HIST < "$STATE" 2>/dev/null || true
LAST_PRE=${LAST_PRE:-0}; CALLS=${CALLS:-0}; HIST=${HIST:-}
HIST=${HIST//[^01]/}                  # a stray token can never be read as serial turns
NOW=$(now_ms)
serial_turns() { local z=${HIST//0/}; echo "${#z}"; }

case "$MODE" in
  pretool)
    GAP=$((NOW - LAST_PRE))
    if [ "$LAST_PRE" -gt 0 ] && [ "$GAP" -lt "$SAME_TURN_MS" ]; then
      CALLS=$((CALLS + 1))             # a batched turn - posttool records it as a '0'
    else
      CALLS=1
    fi
    N=$(serial_turns)
    if [ "$CALLS" -eq 1 ] && [ "$N" -ge "$THRESHOLD" ]; then
      printf '%s %s %s\n' "$NOW" "$CALLS" "" > "$STATE"   # clear the window: no deadlock, one block per THRESHOLD
      echo "BLOCKED: $N of the last ${#HIST} turns EACH made a single quick read-only call - $N model round trips (~$((N * 9))s) for a few seconds of actual work. These reads/greps do not depend on each other; send them TOGETHER. Put every remaining lookup you already know you need into ONE message as parallel tool calls (or fold several greps into a single Bash command). Then continue. (CLAUDE.md 'Batch the rendered-map inspection' / 'Batch into fewer, bigger turns'. Measured 2026-08-08: 147 of 162 round trips made a single call - 22.7 minutes of latency for 4.0 minutes of work. This hook re-arms after another $THRESHOLD serial turns.)" >&2
      exit 2
    fi
    # A NEW TURN APPENDS ITS OWN (provisional) ENTRY HERE, after the check above has read the
    # window. It cannot be left to posttool: on a batched turn the FIRST posttool already sees
    # CALLS=2, so it would rewrite the PREVIOUS turn's entry and the batch would silently eat a
    # serial turn instead of recording itself (caught by test 4, 2026-08-08). Provisional '0' -
    # posttool promotes it to '1' only if the turn really was one quick call.
    if [ "$CALLS" -eq 1 ]; then
      HIST="${HIST}0"
      if [ "${#HIST}" -gt "$WINDOW" ]; then HIST=${HIST: -$WINDOW}; fi
    fi
    printf '%s %s %s\n' "$NOW" "$CALLS" "$HIST" > "$STATE"
    ;;
  posttool)
    # EXACTLY ONE history entry per TURN. The first call of a turn appends its verdict; a second
    # call in the same turn rewrites that entry to '0', because the turn turned out to be batched.
    # (Appending per CALL instead would let one 3-call turn flush the whole window with zeros.)
    DUR=$((NOW - LAST_PRE))
    if [ "$CALLS" -le 1 ] && [ "$DUR" -lt "$CHEAP_MS" ]; then
      HIST="${HIST%?}1"               # one call and it was quick: a batchable turn
    else
      HIST="${HIST%?}0"               # batched (the behavior we want) or real work
    fi
    printf '%s %s %s\n' "$LAST_PRE" "$CALLS" "$HIST" > "$STATE"
    ;;
  status)   # for the tests and for a session that wants to see where it stands
    echo "tool=$TOOL history=$HIST serial=$(serial_turns) calls_this_turn=$CALLS threshold=$THRESHOLD window=$WINDOW state=$STATE"
    ;;
  *)
    echo "batching-hooks: unknown mode '$MODE' (want: pretool | posttool | status)" >&2
    exit 1
    ;;
esac
exit 0
