#!/usr/bin/env bash
# Tests for guard-file-hooks.sh (feature 127, layer 3).
# Run: scripts/test-guard-file-hooks.sh   (exit 0 = all green)
#
# TWO DIRECTIONS (FR-015 + FR-016). Section 2 carries the case the fidelity review put here: an edit
# to a review-subagent definition must NOT be intercepted. It was in the first draft of the spec and
# was removed as unrequested - editing an agent cannot start an expensive run, so a prompt there
# guards nothing and obstructs this project's own procedure for improving review subagents.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/guard-file-hooks.sh"
ROOT="$(cd "$HERE/.." && pwd)"
PASS=0; FAIL=0

ev() { python3 -c 'import json,sys; print(json.dumps({"session_id":"g","tool_name":sys.argv[3],"tool_input":{"file_path":sys.argv[1],"new_string":sys.argv[2]}}))' "$1" "$2" "${3:-Edit}"; }
run() { ev "$1" "${2:-x}" "${3:-Edit}" | "$HOOK" pretool >/dev/null 2>/tmp/gf.err; echo $?; }

check() { local rc; rc=$(run "$2" "${3:-x}" "${4:-Edit}")
  if { [ "$1" = ok ] && [ "$rc" -eq 0 ]; } || { [ "$1" = blocked ] && [ "$rc" -ne 0 ]; }; then
    echo "  ok      $1: $(basename "$2")"; PASS=$((PASS+1))
  else echo "  FAIL    expected $1 for $2 (rc=$rc)"; FAIL=$((FAIL+1)); fi; }

echo "1. IT FIRES on the files that ARE guards (FR-015)"
check blocked "$ROOT/.claude/skills/diagram/Makefile"
check blocked "$ROOT/scripts/gate-hooks.sh"
check blocked "$ROOT/scripts/make-only-hooks.sh"
check blocked "$ROOT/scripts/guard-file-hooks.sh"
check blocked "$ROOT/.claude/settings.json"
check blocked "$ROOT/.claude/settings.json" "x" "Write"

echo
echo "2. IT STAYS QUIET on everything else (FR-016)"
check ok "$ROOT/.claude/agents/frontend-review.md"
check ok "$ROOT/.claude/agents/spec-fidelity.md"
check ok "$ROOT/scripts/test-gate-hooks.sh"
check ok "$ROOT/scripts/test-make-only-hooks.sh"
check ok "$ROOT/.claude/skills/diagram/l7r/diagram/hamletgen/ways.py"
check ok "$ROOT/.claude/skills/diagram/tests/test_invocation.py"
check ok "$ROOT/CLAUDE.md"
check ok "$ROOT/specs/127-gated-make-commands/spec.md"

echo
echo "3. THE ESCAPE WORKS, and puts the intent in the diff"
check ok "$ROOT/.claude/skills/diagram/Makefile" "GUARD_EDIT_OK - adding a target for a new operation"
check ok "$ROOT/scripts/gate-hooks.sh" "GUARD_EDIT_OK - it was firing on correct work"

echo
echo "4. THE REFUSAL TELLS YOU WHAT TO DO"
rc=$(run "$ROOT/.claude/skills/diagram/Makefile")
if [ "$rc" -ne 0 ] && grep -q "GUARD_EDIT_OK" /tmp/gf.err && grep -q "fires on correct work" /tmp/gf.err; then
  echo "  ok      names the escape and distinguishes legitimate edits"; PASS=$((PASS+1))
else echo "  FAIL    refusal did not carry the escape or the categories"; FAIL=$((FAIL+1)); fi

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ]
