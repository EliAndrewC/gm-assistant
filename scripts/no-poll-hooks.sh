#!/usr/bin/env bash
# no-poll-hooks.sh - a Claude Code PreToolUse hook that BLOCKS busy-wait polling in Bash calls.
#
# WHY (GM 2026-07-25, from a transcript profile of a 31-minute feature): 10.9 minutes of it - 35% of
# the whole task - was spent polling a background gate that had ALREADY FINISHED. The session
# backgrounded `make done` correctly and then blocked on this:
#
#     for i in $(seq 1 80); do if ! pgrep -f "make done" >/dev/null 2>&1; then break; fi; command sleep 5; done
#
# Two independent faults, and each one alone was enough to waste the time:
#
#   1. `pgrep -f "make done"` MATCHES ITS OWN SHELL. The pattern is an argument of the very command
#      line being searched for, so pgrep always finds the polling process itself and the `break`
#      can never fire. Both waits ran their full iteration budget: the gates took 97s and 98s, the
#      waits took 351s and 401s. This is not a rare footgun - `pgrep -f <literal>` issued from a
#      shell is self-matching BY CONSTRUCTION, every time.
#   2. POLLING WAS NEVER NEEDED. The harness sends a completion notification and re-invokes the
#      session when a backgrounded command finishes; the Bash tool's own docs say not to poll for
#      it. The correct shape is: background the work, do something useful, act on the notification.
#
# It also defeats the harness's own foreground-`sleep` guard: plain `sleep` is blocked, and
# `command sleep` / `/bin/sleep` / `env sleep` exist here only as ways around that block.
#
# This is a CONTROL, not a reminder, for the same reason batching-hooks.sh is: the project had a
# documented "background the final gate" rule at the time, and the session followed it and then
# blocked on the gate anyway. Instructions you must remember perfectly every time are a worse
# design than a thing that simply cannot happen.
#
# ESCAPE HATCH: genuine waits on EXTERNAL state the harness cannot notify about (a dev server's
# port opening, a remote queue) are legitimate - put the token POLL_OK in the command, ideally as a
# comment naming what is being waited on. The token is deliberately explicit so the choice is
# visible in the transcript rather than habitual.
#
# Wired from .claude/settings.json alongside batching-hooks.sh / clone-sync-hooks.sh (every session
# runs MAIN's copy via an absolute path, so a change here takes effect everywhere at once).
# Tested by test-no-poll-hooks.sh - keep it green.
set -euo pipefail

MODE=${1:-pretool}
INPUT=$(cat 2>/dev/null || true)
[ "$MODE" = "pretool" ] || exit 0

# The command is nested (tool_input.command) and is arbitrary text with escapes and newlines, so it
# needs a real JSON parse - grep would mangle it. Only Bash calls reach this hook, and those already
# cost seconds, so python's startup is not a factor here (batching-hooks.sh, which fires on every
# Read/Grep/Glob too, avoids python for exactly that reason).
CMD=$(printf '%s' "$INPUT" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("tool_input",{}).get("command",""))
except Exception: print("")' 2>/dev/null || true)
[ -n "$CMD" ] || exit 0

# Explicit, visible opt-out for a real external-state wait.
case "$CMD" in *POLL_OK*) exit 0 ;; esac

block() {
  echo "BLOCKED (no-poll): $1

$2

Do this instead: background the work (run_in_background), spend the turn on something useful - docs,
the commit message, the next edit - and act on the completion notification when it arrives. The
harness re-invokes you; you never have to watch for it. If you truly must wait on EXTERNAL state the
harness cannot see (a server port, a remote queue), put POLL_OK in the command with a note saying
what you are waiting for.

(scripts/no-poll-hooks.sh. Measured 2026-07-25: two such waits cost 10.9 minutes - 35% - of a
31-minute feature, watching gates that had finished in 97s and 98s.)" >&2
  exit 2
}

# ---- 1. pgrep/pkill -f with a LITERAL pattern: self-matching by construction ---------------------
# The pattern is part of this very command line, so pgrep -f finds this shell and reports "running"
# forever. A pattern built from a variable ($VAR - the literal text on the command line is the
# variable name) or written with the bracket trick ([m]ake) does not self-match, so both are allowed.
if printf '%s' "$CMD" | grep -Eq '\b(pgrep|pkill)\b[^|;&]*[[:space:]]-[a-zA-Z]*f'; then
  PAT=$(printf '%s' "$CMD" | grep -Eo '\b(pgrep|pkill)\b[^|;&]*' | head -1)
  case "$PAT" in
    *'$'* | *'['*) ;; # variable or bracket-trick pattern: cannot match its own command line
    *) block "\`pgrep -f\` / \`pkill -f\` with a literal pattern always matches ITS OWN shell." \
        "The pattern you are searching for is an argument of the command line you are running, so pgrep
finds this very process and reports the job as still running - the loop can never exit early. That
exact bug cost 10.9 minutes on 2026-07-25.

If you genuinely need to test whether a PID is alive, use \`kill -0 <pid>\` or read /proc/<pid>; to
match a command line without self-matching, use the bracket trick (pgrep -f '[m]ake done')." ;;
  esac
fi

# ---- 2. a loop containing a sleep: a busy-wait ---------------------------------------------------
SLEEP_RE='(^|[;&|(]|[[:space:]]|\bdo\b|\bthen\b)[\\]?((command|env|busybox)[[:space:]]+)?(/(bin|usr/bin)/)?sleep[[:space:]]+[0-9.]'
if printf '%s' "$CMD" | grep -Eq '(^|[;&|[:space:]])(while|until|for)[[:space:]]' && printf '%s' "$CMD" | grep -Eq "$SLEEP_RE"; then
  block "this is a busy-wait loop (a loop containing \`sleep\`)." \
    "Waiting in a loop burns wall-clock at full model-turn cost and, for anything the harness tracks, it
is pure waste: a backgrounded Bash command notifies you the moment it exits."
fi

# ---- 3. sleep invoked in a form that only exists to dodge the harness's foreground-sleep guard ----
if printf '%s' "$CMD" | grep -Eq '(^|[;&|(]|[[:space:]])([\\]|(command|env|busybox)[[:space:]]+|/(bin|usr/bin)/)sleep[[:space:]]+[0-9.]'; then
  block "\`sleep\` was invoked in a form that evades the harness's foreground-sleep block." \
    "The harness blocks foreground \`sleep\` on purpose; \`command sleep\`, \`/bin/sleep\` and \`env sleep\`
are the same thing wearing a hat. Whatever you were about to wait for, there is a better signal for
it - a completion notification for harness-tracked work, or POLL_OK for genuinely external state."
fi

exit 0
