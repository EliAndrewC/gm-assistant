#!/usr/bin/env bash
# Tests for make-only-hooks.sh. Feeds PreToolUse events and asserts which commands are blocked.
# Run: scripts/test-make-only-hooks.sh   (exit 0 = all green)
#
# TWO DIRECTIONS, ALWAYS (feature 127, FR-015 + FR-016). Section 1 proves the hook FIRES on every
# row of the threat model. Section 2 proves it STAYS QUIET on ordinary work - and that half is not a
# formality. A guard that fires on correct work teaches a session that the override is part of the
# normal routine, which is precisely how the documented-override workaround became habitual in the
# feature that motivated this one. A false positive here is a worse outcome than a false negative.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/make-only-hooks.sh"
PASS=0; FAIL=0

ev() { python3 -c 'import json,sys; print(json.dumps({"session_id":"m1","tool_name":"Bash","tool_input":{"command":sys.argv[1]}}))' "$1"; }
run() { ev "$1" | "$HOOK" pretool >/tmp/mo.out 2>/tmp/mo.err; echo $?; }

check() { # label expected(ok|blocked) command
  local rc; rc=$(run "$3")
  if { [ "$2" = ok ] && [ "$rc" -eq 0 ]; } || { [ "$2" = blocked ] && [ "$rc" -ne 0 ]; }; then
    echo "  ok      $1"; PASS=$((PASS+1))
  else
    echo "  FAIL    $1 (expected $2, rc=$rc)"; FAIL=$((FAIL+1))
  fi
}

names_a_target() { # the refusal must say what to run instead (FR-006)
  local rc; rc=$(run "$2")
  if [ "$rc" -ne 0 ] && grep -q "Run this instead" /tmp/mo.err && grep -q "make " /tmp/mo.err; then
    echo "  ok      $1"; PASS=$((PASS+1))
  else
    echo "  FAIL    $1 (refusal did not name a make target)"; FAIL=$((FAIL+1))
  fi
}

echo "1. IT FIRES - every row of the threat model (FR-015)"
check "tier 1: a cohort run bare"              blocked "python3 -m l7r.diagram.tools.cohort_audit --count 48"
check "tier 1: the generator run bare"         blocked "python3 -m l7r.diagram.hamletgen --batch 24"
check "tier 1: a pool sweep run bare"          blocked "python3 -m l7r.diagram.pipeline.regen pool/hamlets/inashiro.gen.py"
check "tier 1: regen by script path"           blocked "python3 l7r/diagram/pipeline/regen.py pool/hamlets/x.gen.py"
check "tier 1: bare pytest"                    blocked "python3 -m pytest -n auto"
check "tier 1: bare pytest, plain name"        blocked "pytest tests/hamletgen -q"
check "tier 2: the documented override"        blocked "make done FULL=1 REF_WHY=pre-push verification"
check "tier 2: the reference-gate override"    blocked "REF_OK=1 make maps"
check "tier 2: the -k gate override"           blocked "GATE_OK=1 make done"
check "tier 4: a forged makefile"              blocked "make -f /tmp/evil.mk probe"
check "tier 4: --file spelling"                blocked "make --file /tmp/evil.mk probe"
check "tier 4: --makefile spelling"            blocked "make --makefile=/tmp/evil.mk probe"

echo
echo "2. IT STAYS QUIET - ordinary work must never be blocked (FR-016)"
check "the cheap check"                        ok "make reference"
check "the gate"                               ok "make done"
check "the full gate, no inline override"      ok "make done FULL=1"
check "a map sweep"                            ok "make maps"
check "the linters"                            ok "python3 -m ruff check . && python3 -m mypy"
check "git"                                    ok "git -C /gm-assistant/.clones/x status --porcelain"
check "the stop-work ritual"                   ok "./scripts/sync-with-main.sh done"
check "reading a source file"                  ok "grep -n 'def stage_ways' l7r/diagram/hamletgen/ways.py"
check "a hook's own test"                      ok "scripts/test-make-only-hooks.sh"
check "an unrelated python one-liner"          ok "python3 -c 'print(1)'"
# The word 'pytest' appearing inside a make invocation is the gate doing its job, not a bypass.
check "make running pytest internally"         ok "make test  # runs pytest under the hood"

echo
echo "3. THE REFUSAL IS USEFUL (FR-006) - it must name the target, not just say no"
names_a_target "a blocked cohort names a target"  "python3 -m l7r.diagram.tools.cohort_audit"
names_a_target "a blocked pytest names a target"  "pytest -q"
names_a_target "a forged makefile names a target" "make -f /tmp/evil.mk x"

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ]
