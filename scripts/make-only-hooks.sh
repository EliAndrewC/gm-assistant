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

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# DETECTION LIVES IN _hookmatch.py, and the reason is written there: substring matching false-
# positived on a grep, on a commit message, and on this hook's own test harness, all within an hour.
# Matching is anchored to real command positions instead. Keeping it in a file also means it can be
# unit-tested and read without bash quoting in the way.
VERDICT=$("$HERE/_hookmatch.py" 2>/dev/null || echo ok)

block() { # reason, then the make target to use instead
  printf 'BLOCKED: %s\n\n' "$1" >&2
  printf 'Run this instead:  %s\n\n' "$2" >&2
  cat >&2 <<'TAIL'
Every operation in this project goes through a make target, so the expensive ones can ask whether
the cheap one would do first. The scale, so the choice is informed rather than habitual:

    make reference    ~26 s    one seed of the reference hamlet - answers most questions
    make quick        ~4 min   lint, types, and every test that does not roll a map, stops at first
    make done         ~5.5 min reference + lint/types + 3,420 tests - NOT the quick check
    make done FULL=1  ~6 min   + every pool map + the seeds 41-44 ratchet; prompts, cancels by default

If this fired on correct work, that is a BUG in the hook and worth fixing rather than working
around - put GUARD_EDIT_OK in the command with a reason, and say what it false-positived on.

(scripts/make-only-hooks.sh; GM 2026-08-24, feature 127)
TAIL
  exit 2
}

case "$VERDICT" in
  foreign-makefile)
    block "a make driven by a named makefile. This project's targets are in its own Makefile, and a foreign one is the documented way to walk past every guard here." "make <target>   (from .claude/skills/diagram)" ;;
  engine-entry-point)
    block "an engine entry point run outside make." "make <target>   (see future-work/ and the Makefile for the operation list)" ;;
  bare-pytest)
    block "pytest run directly rather than through make. The suite is ~4.5 minutes and its coverage floors only hold under the make targets that set them up." "make quick   (~4 min, stops at the first failure)  or  make done   (~5.5 min)" ;;
  inline-override)
    block "an override supplied on the command line, which skips the prompt whose default answer is CANCEL. That prompt is the whole mechanism: it exists to be answered, not pre-empted." "make <target>   without the override, and answer the prompt if it appears" ;;
  guard-write)
    block "a GUARD FILE written from a shell command. Layer 3 only sees the Edit and Write tools, so this route slips past it - the same ungated-sibling shape this feature exists to close." "the Edit tool, or add GUARD_EDIT_OK with a reason" ;;
esac

exit 0
