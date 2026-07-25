#!/usr/bin/env bash
# Tests for no-poll-hooks.sh. Feeds the hook a PreToolUse payload for a Bash command and asserts
# whether it blocks. Run: scripts/test-no-poll-hooks.sh   (exit 0 = all green)
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/no-poll-hooks.sh"
PASS=0; FAIL=0

run() {  # feed a Bash command through the hook, return its exit code
  python3 -c 'import json,sys; print(json.dumps({"session_id":"t1","tool_name":"Bash","tool_input":{"command":sys.argv[1]}}))' "$1" \
    | "$HOOK" pretool 2>/tmp/np.err
}

check() { # label, expected(ok|blocked), command
  run "$3"; local rc=$?
  if { [ "$2" = ok ] && [ "$rc" -eq 0 ]; } || { [ "$2" = blocked ] && [ "$rc" -ne 0 ]; }; then
    echo "  ok      $1"; PASS=$((PASS+1))
  else
    echo "  FAIL    $1 (expected $2, rc=$rc)"; [ -s /tmp/np.err ] && sed 's/^/          /' /tmp/np.err; FAIL=$((FAIL+1))
  fi
}

echo "1. the exact 2026-07-25 bug and its relatives are blocked"
check "the real one: pgrep-self-match poll loop" blocked \
  'for i in $(seq 1 80); do if ! pgrep -f "make done" >/dev/null 2>&1; then break; fi; command sleep 5; done; tail -18 /tmp/out'
check "bare pgrep -f with a literal pattern" blocked 'pgrep -f "make done"'
check "pkill -f with a literal pattern" blocked 'pkill -f "cherryd"'
check "while + sleep busy-wait" blocked 'while [ ! -f /tmp/done ]; do sleep 2; done'
check "until + sleep busy-wait" blocked 'until curl -s localhost:8080 >/dev/null; do sleep 3; done'
check "for + sleep busy-wait" blocked 'for i in 1 2 3; do sleep 10; done'
check "command sleep (foreground-sleep guard bypass)" blocked 'command sleep 30'
check "/bin/sleep bypass" blocked '/bin/sleep 20'
check "env sleep bypass" blocked 'env sleep 15'
check "backslash-escaped sleep bypass" blocked '\sleep 12'

echo "2. the block explains the fault and the alternative"
run 'pgrep -f "make done"' >/dev/null
grep -q "matches ITS OWN shell" /tmp/np.err && { echo "  ok      names the self-match fault"; PASS=$((PASS+1)); } || { echo "  FAIL    self-match not explained"; FAIL=$((FAIL+1)); }
grep -q "completion notification" /tmp/np.err && { echo "  ok      points at the notification"; PASS=$((PASS+1)); } || { echo "  FAIL    no alternative offered"; FAIL=$((FAIL+1)); }
run 'while :; do sleep 5; done' >/dev/null
grep -q "POLL_OK" /tmp/np.err && { echo "  ok      documents the escape hatch"; PASS=$((PASS+1)); } || { echo "  FAIL    escape hatch not documented"; FAIL=$((FAIL+1)); }

echo "3. legitimate commands are NOT blocked (no false positives)"
check "the gate itself" ok 'make done'
check "pytest" ok 'python3 -m pytest test_settlement.py -n auto'
check "a loop with no sleep" ok 'while read -r line; do echo "$line"; done < /tmp/f'
check "a for loop over maps, regenerating each" ok 'for g in a b c; do python3 $g.gen.py && python3 check_village.py $g.json; done'
check "pgrep with the bracket trick" ok "pgrep -f '[m]ake done'"
check "pgrep -f on a variable pattern" ok 'pgrep -f "$PATTERN"'
check "pgrep without -f (matches process NAME, not the command line)" ok 'pgrep resvg'
check "running a script that happens to sleep internally" ok 'scripts/test-clone-sync-hooks.sh'
check "timeout wrapping a real command" ok 'timeout 60 ./slow-thing.sh'
check "git" ok 'git log --oneline -1'
check "a word merely containing sleep" ok 'grep -rn "sleepy" .'
check "the word sleep inside a string, not invoked" ok 'echo "do not sleep 5 here"'

echo "4. the escape hatch works for genuine external waits"
check "POLL_OK allows a real port wait" ok '# POLL_OK: waiting for the dev server port to open
until curl -s localhost:8080 >/dev/null; do sleep 2; done'
check "POLL_OK allows a bare sleep bypass" ok 'command sleep 5  # POLL_OK: external deploy settling'

echo
echo "no-poll-hooks: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
