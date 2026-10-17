#!/usr/bin/env bash
# Tests for subagent-cache-hooks.sh. Feeds the hook PreToolUse payloads for Agent launches and asserts
# whether it blocks. Run: scripts/test-subagent-cache-hooks.sh   (exit 0 = all green)
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/subagent-cache-hooks.sh"
SUBAGENT_CACHE_STATE_DIR=$(mktemp -d); export SUBAGENT_CACHE_STATE_DIR
trap 'rm -rf "$SUBAGENT_CACHE_STATE_DIR" /tmp/sc.err.$$' EXIT
PASS=0; FAIL=0

run() {  # session, prompt, [subagent_type] [tool_name] -> hook exit code
  python3 -c 'import json,sys
ti = {"prompt": sys.argv[2], "description": "d"}
if sys.argv[3] != "none": ti["subagent_type"] = sys.argv[3] or "general-purpose"
print(json.dumps({"session_id": sys.argv[1], "tool_name": sys.argv[4] or "Agent", "tool_input": ti}))' \
    "$1" "$2" "${3:-}" "${4:-}" | "$HOOK" pretool 2>/tmp/sc.err.$$
}

check() { # label, expected(ok|blocked), session, prompt, [subagent_type] [tool_name]
  run "$3" "$4" "${5:-}" "${6:-}"; local rc=$?
  if { [ "$2" = ok ] && [ "$rc" -eq 0 ]; } || { [ "$2" = blocked ] && [ "$rc" -eq 2 ]; }; then
    echo "  ok      $1"; PASS=$((PASS+1))
  else
    echo "  FAIL    $1 (expected $2, rc=$rc)"; sed 's/^/          /' /tmp/sc.err.$$; FAIL=$((FAIL+1))
  fi
}

# The motivating shape: a long shared rubric FIRST, the varying file name LAST (shrine reviews,
# 2026-10-17) - textbook prefix order, and still uncached across launches.
RUBRIC=$(python3 -c 'print("\n\n".join(f"Rule {i}: " + "check the option text for confusing wording and category errors. " * 5 for i in range(12)))')
P1="$RUBRIC

SECTION UNDER REVIEW: /tmp/review/worship.txt"
P2="$RUBRIC

SECTION UNDER REVIEW: /tmp/review/grounds.txt"
P3="$RUBRIC

SECTION UNDER REVIEW: /tmp/review/approach.txt"

echo "1. a repeated shared block is blocked on the second launch"
check "first launch with the rubric is fine" ok s1 "$P1"
check "second launch repeating it is blocked" blocked s1 "$P2"
grep -q "subagent system" /tmp/sc.err.$$ && { echo "  ok      tip names the agent definition fix"; PASS=$((PASS+1)); } || { echo "  FAIL    tip missing the definition fix"; FAIL=$((FAIL+1)); }
grep -q "CACHE_OK" /tmp/sc.err.$$ && { echo "  ok      tip documents the escape"; PASS=$((PASS+1)); } || { echo "  FAIL    escape not documented"; FAIL=$((FAIL+1)); }
grep -q '"fork"' /tmp/sc.err.$$ && { echo "  ok      tip offers fork"; PASS=$((PASS+1)); } || { echo "  FAIL    fork not offered"; FAIL=$((FAIL+1)); }
check "blocks only once per session" ok s1 "$P3"
check "(legacy Task tool name: first launch)" ok s1b "$P1" "" Task
check "the legacy Task tool name is covered too" blocked s1b "$P2" "" Task
check "(untyped launch: first)" ok s1c "$P1" none
check "an untyped launch is covered too" blocked s1c "$P2" none

echo "2. what must NOT block"
check "short varying prompts (a typed review agent's normal launch)" ok s2 "Review /tmp/a.txt against the catalog."
check "the same short prompt again" ok s2 "Review /tmp/a.txt against the catalog."
check "a different session sending the same rubric" ok s3 "$P2"
check "CACHE_OK escape on a repeat" ok s4 "$P1"
check "(repeat with CACHE_OK)" ok s4 "CACHE_OK: definition edited this session.

$P2"
check "fork launches are exempt" ok s5 "$P1" fork
check "(fork repeat)" ok s5 "$P2" fork
check "typed launches are exempt (per-task context, e.g. the GM's request each spec-fidelity round)" ok s5b "$P1" spec-fidelity
check "(typed repeat)" ok s5b "$P2" spec-fidelity
check "a non-Agent tool is ignored" ok s6 "$P1" "" Read
check "(non-Agent repeat)" ok s6 "$P2" "" Read
SMALL="Shared preamble that is long enough to count as a paragraph but well under the two thousand character threshold, so repeating it costs less than a blocked turn would. It is repeated on purpose here.

"
check "a repeated block under the threshold" ok s7 "${SMALL}Task one."
check "(its repeat)" ok s7 "${SMALL}Task two."
check "malformed input is not an error" ok s8 ""

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ]
