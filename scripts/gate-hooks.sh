#!/usr/bin/env bash
# gate-hooks.sh - Claude Code harness hook that BLOCKS `make done` when the only local test run
# since the last edit was a `-k` SUBSET.
#
# WHY (GM 2026-08-08). The dev-loop doc has said this since 2026-07-25, in its own section heading:
# "Before the gate, run the WHOLE affected test file - not a `-k` subset". The reasoning is that a
# `-k` filter selects the tests you were THINKING about, and the ones a change breaks are by
# definition the ones you were not. It is written down, it is correct, and a session followed it
# with `-k "kura_side or punishment"`, went to the gate, and the gate died on
# `test_place_punishment_spot_probes_for_a_clear_caption_seat` - a test in the same file, on the
# same function, that the filter did not select. That cost a full gate cycle: 3.9 minutes of idle
# plus the fix turns, on a change whose whole-file run takes ~45 seconds.
#
# Same lesson as batching-hooks.sh and no-poll-hooks.sh, for the third time: a rule that lives only
# in a document is not a control. This is the control.
#
# WHAT IT DOES. It watches Bash commands:
#   - a pytest run WITH `-k`      -> remembers "the last local test run was a subset"
#   - a pytest run WITHOUT `-k`   -> clears that (a whole-file/whole-suite run happened)
#   - an Edit/Write to a .py file -> clears it too: any local run now PREDATES the current code, so
#                                    it cannot vouch for it either way and the state is meaningless
#   - `make done` (the gate)      -> if the flag is set, BLOCK once, then clear it
# It blocks at most ONCE per subset run, so it can never deadlock: re-issuing the gate goes through.
#
# ESCAPE HATCH: put GATE_OK in the command with a reason (e.g. a docs-only diff, or a change whose
# affected test file genuinely ran green under a different invocation).
#
# LIMITATION, stated rather than hidden: the classifier is a substring test, so a command that merely
# MENTIONS pytest (a grep for it, a doc edit quoting it) is read as a run. That direction fails SAFE -
# a mention without `-k` only clears a flag, and a mention with `-k` costs at most one block, which
# GATE_OK clears. Tightening it to a real command parse is not worth the false-negative risk.
#
# Wired from .claude/settings.json. Tested by scripts/test-gate-hooks.sh.
set -euo pipefail

MODE=${1:-}
INPUT=$(cat 2>/dev/null || true)
STATE_DIR=${GATE_STATE_DIR:-/tmp/claude-gate}

json_str() { printf '%s' "$INPUT" | grep -o "\"$1\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" | head -1 | sed 's/.*:[[:space:]]*"//; s/"$//'; }
# The command can contain escaped quotes and newlines, so take everything between "command":" and
# the closing quote of that field rather than trying to be clever - only substring tests follow.
json_cmd() { printf '%s' "$INPUT" | tr '\n' ' ' | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\(.*\)".*/\1/p' | head -1; }

SID=$(json_str session_id); SID=${SID:-nosession}
TOOL=$(json_str tool_name); TOOL=${TOOL:-unknown}
mkdir -p "$STATE_DIR"
STATE="$STATE_DIR/${SID//[^A-Za-z0-9_-]/_}.subset"

case "$MODE" in
  pretool)
    CMD=$(json_cmd)
    case "$TOOL" in
      Edit|Write|NotebookEdit)
        # a source edit invalidates every earlier local run, subset or not
        fp=$(json_str file_path)
        case "$fp" in *.py) rm -f "$STATE" ;; esac
        exit 0
        ;;
    esac
    [ "$TOOL" = Bash ] || exit 0
    case "$CMD" in *GATE_OK*) rm -f "$STATE"; exit 0 ;; esac

    # the GATE itself
    case "$CMD" in
      *"make done"*|*"make -C"*done*)
        if [ -f "$STATE" ]; then
          WAS=$(cat "$STATE" 2>/dev/null || true)
          rm -f "$STATE"          # block ONCE - re-issuing the gate goes straight through
          echo "BLOCKED: the only local test run since your last edit was a \`-k\` SUBSET (${WAS:-pytest -k ...}). A subset selects the tests you were THINKING about; the ones a change breaks are the ones you were not - which is exactly how a session ran \`-k \"kura_side or punishment\"\`, went to the gate, and lost a full 3.9-minute gate cycle to a test in the SAME file it had not selected. Run the WHOLE test file(s) for the modules you touched first - \`python3 -m pytest tests/test_<mod>.py -q -n auto --no-cov\` - then run the gate. (CLAUDE.md, 'Before the gate, run the WHOLE affected test file'. Override: put GATE_OK in the command with a reason. GUARD_EDIT_OK 2026-08-25: pointer retargeted after the diagram skill moved out.)" >&2
          exit 2
        fi
        exit 0
        ;;
    esac

    # a local pytest run: subset or whole?
    case "$CMD" in
      *pytest*)
        case "$CMD" in
          *" -k "*|*" -k="*)  printf '%s' "$CMD" | head -c 120 > "$STATE" ;;
          *)                  rm -f "$STATE" ;;   # a whole-file / whole-suite run vouches for the code
        esac
        ;;
    esac
    exit 0
    ;;
  status)
    if [ -f "$STATE" ]; then echo "subset_pending=1 cmd=$(cat "$STATE")"; else echo "subset_pending=0"; fi
    ;;
  *)
    echo "gate-hooks: unknown mode '$MODE' (want: pretool | status)" >&2
    exit 1
    ;;
esac
exit 0
