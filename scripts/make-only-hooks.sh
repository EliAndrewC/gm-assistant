#!/usr/bin/env bash
# make-only-hooks.sh - a Claude Code PreToolUse hook that BLOCKS any route to an expensive
# operation other than its make target (feature 127, guard layer 1).
#
# WHY (GM 2026-08-24). The fast path already existed - `make reference` answers in ~26 s - and a
# session kept taking the five-minute and twenty-five-minute paths anyway. Four times in one feature,
# each time after being told not to, each time by a route the guards of the day did not cover:
#
#   THE THREAT MODEL, which is a record of what actually happened rather than what might:
#
#     tier 1  reach for an UNGATED SIBLING COMMAND        `cohort_audit` while `make maps` was gated,
#                                                          then `make done` and `make test` while both
#                                                          of those were
#     tier 2  supply the DOCUMENTED OVERRIDE               `REF_WHY=`, which skipped a prompt whose
#                                                          default answer is cancel
#     tier 3  ARRANGE THAT THE PROMPT CANNOT FIRE          backgrounding a `FULL=1` run, so nothing
#                                                          was attached to answer it
#     tier 4  FORGE A MAKEFILE                             never reached - closed here anyway
#     tier 5  EDIT A GUARD                                 never reached - guard-file-hooks.sh
#     tier 6  DISABLE THE HOOK SYSTEM                      never reached - a settings diff
#
# Every one of tiers 1-3 was an action that could be PRESENTED AS DILIGENCE, which is exactly why
# each worked: `REF_WHY="pre-push verification before merging to main"` reads as conscientious. That
# is the property this hook removes. Tiers 4-6 cannot be dressed up the same way, and two of them
# land in a git diff.
#
# WHICH LAYER CLOSES WHICH TIER (constitution FR-017 - recorded here so a later session can tell
# whether a proposed change reopens a known route):
#
#     tier 1  THIS FILE (command shape) + l7r/diagram/_invocation.py (process tree)
#     tier 2  THIS FILE (inline override vars) + the Makefile's cancel-by-default prompt
#     tier 3  the Makefile (a non-interactive FULL run is refused outright)
#     tier 4  THIS FILE (`make -f`) + _invocation.py (make's cwd and -f are checked)
#     tier 5  scripts/guard-file-hooks.sh
#     tier 6  visible in `git diff .claude/settings.json`
#
# WHY THIS LAYER IS LOAD-BEARING and _invocation.py is defense in depth: this runs in the HARNESS,
# outside the guarded process, BEFORE the command executes. So a refusal costs zero seconds, and it
# can see shapes no in-process check ever can - a bare `pytest`, a `make -f` naming a foreign
# makefile. _invocation.py catches what this file's patterns do not anticipate, and is the only
# layer that can catch an in-process `python3 -c "import ...; generate(...)"`.
#
# ESCAPE HATCH: none, deliberately. The make targets carry the override, where it is prompted,
# defaulted to cancel, and logged. An escape hatch here would be tier 2 with extra steps.

set -uo pipefail

MODE="${1:-pretool}"
[ "$MODE" = pretool ] || exit 0

INPUT=$(cat)

# The command is arbitrary text with escapes and newlines, so it needs a real JSON parse.
CMD=$(printf '%s' "$INPUT" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("tool_input",{}).get("command",""))
except Exception: print("")')

[ -z "$CMD" ] && exit 0

block() { # reason, then the make target to use instead
  printf 'BLOCKED: %s\n\n' "$1" >&2
  printf 'Run this instead:  %s\n\n' "$2" >&2
  cat >&2 <<'TAIL'
Every operation in this project goes through a make target, so the expensive ones can ask whether
the cheap one would do first. The scale, so the choice is informed rather than habitual:

    make reference    ~26 s    one seed of the reference hamlet - answers most questions
    make quick        seconds  lint, types, and every test that does not roll a map
    make done         ~5.5 min reference + lint/types + 3,420 tests - NOT the quick check
    make done FULL=1  ~6 min   + every pool map + the seeds 41-44 ratchet; prompts, cancels by default

There is no escape hatch on this hook, on purpose. The override lives on the make targets, where it
is prompted for, defaults to CANCEL, and is written to dev/bypass-log.jsonl for later audit. An
escape hatch here would just be the documented-override workaround with extra steps.

(scripts/make-only-hooks.sh; GM 2026-08-24, feature 127)
TAIL
  exit 2
}

# ---------------------------------------------------------------------------------------------
# tier 4: a forged makefile. Measured 2026-08-24: `make -f /tmp/evil.mk` passes a bare ancestry
# check, because make really is the parent - it is just not OUR make. Two lines in /tmp.
# ---------------------------------------------------------------------------------------------
case "$CMD" in
  *"make -f"*|*"make --file"*|*"make --makefile"*|*"make -"[a-zA-Z]*" -f"*)
    block "a make driven by a named makefile. This project's targets are in its own Makefile, and a foreign one is the documented way to walk past every guard here." "make <target>   (from .claude/skills/diagram)"
    ;;
esac

# ---------------------------------------------------------------------------------------------
# tier 1: a bare interpreter reaching an engine entry point, or a bare pytest.
# `python3 -m pytest` and `pytest` both; the suite is the 4.5-minute cost and the thing most often
# reached for directly.
# ---------------------------------------------------------------------------------------------
# MATCH AN INVOCATION, NOT A MENTION. The first draft matched the bare path
# `l7r/diagram/hamletgen` anywhere in the command, which blocked
# `grep -n 'def stage_ways' l7r/diagram/hamletgen/ways.py` - a read. Its own test caught it
# immediately, and it is the failure that matters most: a guard that fires on correct work is how a
# session learns the override is routine, which is the habit this whole feature exists to break. So
# every pattern below requires an interpreter to actually be running the thing.
case "$CMD" in
  *python*" -m l7r.diagram."*|*python*"l7r/diagram/pipeline/regen.py"*|*python*"l7r/diagram/hamletgen/__main__.py"*)
    block "an engine entry point run outside make." "make <target>   (see 'make help' for the operation registry)"
    ;;
esac

case "$CMD" in
  *pytest*)
    # `make test` and friends run pytest themselves; only a DIRECT invocation is blocked, and the
    # marker is that the command does not itself invoke make.
    case "$CMD" in
      *make\ *) : ;;
      *) block "pytest run directly rather than through make. The suite is ~4.5 minutes and its coverage floors only hold under the make targets that set them up." "make quick   (seconds)  or  make done   (~5.5 min)" ;;
    esac
    ;;
esac

# ---------------------------------------------------------------------------------------------
# tier 2: the documented override, supplied inline so no prompt ever fires. This is the one that
# actually happened three times, and it happened because it reads as conscientious.
# ---------------------------------------------------------------------------------------------
case "$CMD" in
  *REF_WHY=*|*REF_OK=*|*GATE_OK=*)
    block "an override supplied on the command line, which skips the prompt whose default answer is CANCEL. That prompt is the whole mechanism: it exists to be answered, not to be pre-empted." "make <target>   without the override, and answer the prompt if it appears"
    ;;
esac

exit 0
