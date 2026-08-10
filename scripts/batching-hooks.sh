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
# WHY ONLY RECON-SHAPED CALLS ARE BLOCKED, AND THE RE-ARM BACKS OFF (GM 2026-08-10). A profile
# of the 021 capital-housing session: 752 tool turns, 52 blocks - and 49 of the 52 landed on a
# call that was NOT the problem. 21 were patch/regen heredoc scripts (real work) and 28 were
# commands that had already folded several lookups with &&/; (exactly the requested behavior);
# only 3 were naked single greps. A patch-grind loop (check output -> patch -> regen -> check)
# accumulates cheap DEPENDENT turns the window cannot tell from batchable recon, so the hook
# fired ~once per 14 turns, cost ~9 minutes of pure block latency, and induced gaming (a padded
# no-op turn to age the counter). Three fixes, same teeth for the recon-run case it exists for:
#   1. only a recon-SHAPED call is ever blocked (Read/Grep/Glob, or a Bash command with no
#      heredoc / fold / multi-line / test-or-patch marker) - blocking the patch script that
#      arrives one turn AFTER the batching opportunity passed just gets it re-sent verbatim;
#   2. the bar re-arms higher after each firing (REARM doubles toward WINDOW) and decays back to
#      THRESHOLD as turns batch - a reminder that fires 5 times a session teaches, one that
#      fires 52 times gets routed around;
#   3. every known counter-strategy is IN the block message (fold the retry-patch, act-on-read
#      in the same command, never pad with no-ops) so no session has to rediscover them.
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
# A BACKGROUNDED call is never recon. It returns to the model in milliseconds, so the duration test
# reads it as the cheapest kind of turn - but launching the gate with run_in_background is exactly
# the behavior the loop rules ASK for, and the first version of this window duly blocked one
# (2026-08-08, minutes after shipping). Boolean field, so it needs its own matcher.
is_background() { printf '%s' "$INPUT" | grep -q '"run_in_background"[[:space:]]*:[[:space:]]*true'; }

# Only a recon-SHAPED call is a valid block target (GM 2026-08-10). Read/Grep/Glob are
# single-purpose reads. A Bash command is recon only when it shows NONE of the substantive
# markers: a heredoc, an &&/; fold (which IS the requested batching), a multi-line script
# (escaped \n in the JSON), or a test/format/patch/commit runner. Every other tool (Edit,
# Write, Agent, Task*, ...) mutates or delegates - real work, never the right thing to block.
# Scans the raw JSON rather than extracting the command: markers collide with nothing else in
# the event payload, and a rare false pass just keeps the hook quiet (it fails open).
is_recon_call() {
  case "$TOOL" in
    Read|Grep|Glob) return 0 ;;
    Bash) ;;
    *) return 1 ;;
  esac
  if printf '%s' "$INPUT" | grep -qE '<<|&&|;|\\n|pytest|make |git commit|git add|python3? -|ruff|mypy'; then
    return 1
  fi
  return 0
}

SID=$(json_str session_id); SID=${SID:-nosession}
TOOL=$(json_str tool_name); TOOL=${TOOL:-unknown}
mkdir -p "$STATE_DIR"
# .state2, not .state: the file format changed with the rolling window (2026-08-08) and a
# half-read old file would be counted as history. A new name retires them without a migration.
# .state3: the format grew a REARM field in position 3 (2026-08-10) - REARM sits BEFORE the
# history because HIST may be empty, and a trailing empty field would make read shift REARM into
# HIST's slot. Same retire-by-rename doctrine as the .state -> .state2 change.
STATE="$STATE_DIR/${SID//[^A-Za-z0-9_-]/_}.state3"

# state: last_pre_ms calls_this_turn rearm history   (history = one char per TURN, oldest first,
# '1' = serial and cheap, '0' = batched or real work; at most WINDOW chars)
read -r LAST_PRE CALLS REARM HIST < "$STATE" 2>/dev/null || true
LAST_PRE=${LAST_PRE:-0}; CALLS=${CALLS:-0}; HIST=${HIST:-}
case "${REARM:-}" in ''|*[!0-9]*) REARM=$THRESHOLD ;; esac
if [ "$REARM" -lt "$THRESHOLD" ]; then REARM=$THRESHOLD; fi
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
    BG=0; if is_background; then BG=1; fi
    N=$(serial_turns)
    if [ "$CALLS" -eq 1 ] && [ "$BG" -eq 0 ] && [ "$N" -ge "$REARM" ] && is_recon_call; then
      REARM=$((REARM * 2))
      if [ "$REARM" -gt "$WINDOW" ]; then REARM=$WINDOW; fi   # a bar above the window could never fire
      printf '%s %s %s %s\n' "$NOW" "$CALLS" "$REARM" "" > "$STATE"   # clear the window: no deadlock
      {
        echo "BLOCKED: $N of the last ${#HIST} turns EACH made a single quick read-only call, and this call is shaped like another one - $N model round trips (~$((N * 9))s) for a few seconds of actual work. Batch instead; the playbook:"
        echo " - Independent lookups you ALREADY know you need: send them TOGETHER, as parallel tool calls in one message or one Bash command folding several greps."
        echo " - Dependent follow-up: fold the ACTION into the same command as the read. After a patch MISS, send anchor-grep + corrected patch + regen + check as ONE script with asserts - not grep now, patch next turn."
        echo " - About to read a result and then act on it? Put the action in the same command (grep the anchor && apply && re-run the check)."
        echo " - NEVER pad with no-op turns to age the window - a wasted turn costs the same round trip as recon, and only quick single reads are ever blocked (heredocs, &&/; folds, pytest/make/git-commit runs always pass), so there is nothing to game."
        echo "Then continue. The bar re-arms at $REARM serial turns of the last $WINDOW and decays back to $THRESHOLD as you batch. (CLAUDE.md 'Batch into fewer, bigger turns'; measured 2026-08-08: 147 of 162 round trips single-call - 22.7 min of latency for 4.0 min of work; 2026-08-10: 49 of 52 blocks hit already-substantive calls, hence the shape test.)"
      } >&2
      exit 2
    fi
    # A NEW TURN APPENDS ITS OWN (provisional) ENTRY HERE, after the check above has read the
    # window. It cannot be left to posttool: on a batched turn the FIRST posttool already sees
    # CALLS=2, so it would rewrite the PREVIOUS turn's entry and the batch would silently eat a
    # serial turn instead of recording itself (caught by test 4, 2026-08-08). Provisional '0' -
    # posttool promotes it to '1' only if the turn really was one quick call.
    if [ "$CALLS" -eq 1 ]; then
      HIST="${HIST}0"     # provisional; a backgrounded call is left at '0' by posttool
      if [ "${#HIST}" -gt "$WINDOW" ]; then HIST=${HIST: -$WINDOW}; fi
    fi
    printf '%s %s %s %s\n' "$NOW" "$CALLS" "$REARM" "$HIST" > "$STATE"
    ;;
  posttool)
    # EXACTLY ONE history entry per TURN. The first call of a turn appends its verdict; a second
    # call in the same turn rewrites that entry to '0', because the turn turned out to be batched.
    # (Appending per CALL instead would let one 3-call turn flush the whole window with zeros.)
    DUR=$((NOW - LAST_PRE))
    if [ "$CALLS" -le 1 ] && [ "$DUR" -lt "$CHEAP_MS" ] && ! is_background; then
      HIST="${HIST%?}1"               # one call and it was quick: a batchable turn
    else
      HIST="${HIST%?}0"               # batched (the behavior we want) or real work
      if [ "$REARM" -gt "$THRESHOLD" ]; then REARM=$((REARM - 1)); fi   # backoff decays as turns batch
    fi
    printf '%s %s %s %s\n' "$LAST_PRE" "$CALLS" "$REARM" "$HIST" > "$STATE"
    ;;
  status)   # for the tests and for a session that wants to see where it stands
    echo "tool=$TOOL history=$HIST serial=$(serial_turns) calls_this_turn=$CALLS threshold=$THRESHOLD rearm=$REARM window=$WINDOW state=$STATE"
    ;;
  *)
    echo "batching-hooks: unknown mode '$MODE' (want: pretool | posttool | status)" >&2
    exit 1
    ;;
esac
exit 0
