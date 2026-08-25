#!/usr/bin/env bash
# guard-file-hooks.sh - a PreToolUse hook that intercepts edits to the files that ARE the guards
# (feature 127, layer 3).
#
# WHY. Layers 1 and 2 close every workaround tier this project has actually observed. The tiers ABOVE
# those - forge a makefile, edit a guard, disable the hook system - were never reached, and the
# reason is worth stating because it is what this layer preserves: none of them can be presented as
# diligence. `REF_WHY="pre-push verification"` reads as conscientious; quietly weakening the Makefile
# does not.
#
# So this layer is not about stopping a determined operator, which is impossible with a shell. It is
# about making sure the remaining routes stay UNMISTAKABLE - you cannot take one by accident, in a
# hurry, while believing you are being careful.
#
# NOT `.claude/agents/*.md`, deliberately. That was in the first draft of the spec and the fidelity
# reviewer removed it as unrequested: editing an agent definition cannot start a 25-minute run, so it
# bypasses nothing here, and this project has a STANDING PROCEDURE for improving review subagents
# that a reason-prompt would obstruct on every use. A guard with no threat behind it is pure friction,
# and friction is what teaches people to click past guards that matter.
#
# ESCAPE: put GUARD_EDIT_OK in the edit, with a reason. Editing a guard is legitimate - this feature
# does it constantly - and the point is that it be DELIBERATE and visible in the diff, not forbidden.
set -uo pipefail

MODE="${1:-pretool}"
[ "$MODE" = pretool ] || exit 0

INPUT=$(cat)

read -r FILE NEW <<<"$(printf '%s' "$INPUT" | python3 -c 'import json,sys
try:
    d = json.load(sys.stdin).get("tool_input", {})
    body = (d.get("new_string") or "") + (d.get("content") or "")
    print(d.get("file_path", "*"), "GUARD_EDIT_OK" in body)
except Exception:
    print("* False")')"

[ "$NEW" = "True" ] && exit 0

# GUARD_EDIT_OK (2026-08-25, feature 131 follow-up): the diagram skill's Makefile left with the
# skill; webapp/Makefile is the one that remains - it carries this repository's `guard` target
# (no gate runs from main) and the `done` gate itself, so it is held to the same standard.
case "$FILE" in
  */webapp/Makefile|*/scripts/*-hooks.sh|*/.claude/settings.json) ;;
  *) exit 0 ;;
esac

# A hook editing its own test file is how these get maintained; only the guards themselves are held.
case "$FILE" in */scripts/test-*-hooks.sh) exit 0 ;; esac

cat >&2 <<TAIL
BLOCKED: $FILE is a GUARD, not ordinary source.

The guards are what stop an expensive run being started by picking a different command. Weakening
one silently is the only remaining bypass that does not announce itself, so an edit here has to be
deliberate rather than incidental.

If the edit is legitimate - and it often is, these files get maintained like any other - put
GUARD_EDIT_OK in it with a short reason. That is not a formality: it puts the intent in the diff,
where the GM reads it.

Before you do, check which of these you are actually doing:
  - fixing a guard that fires on correct work        -> legitimate, and important; say so
  - adding a new guard or a new operation            -> legitimate; say so
  - making a guard stop blocking something you want  -> that is the thing this exists to catch

(scripts/guard-file-hooks.sh; feature 127)
TAIL
exit 2
