#!/usr/bin/env bash
# Tests for batching-hooks.sh. Simulates PreToolUse/PostToolUse event sequences and asserts when a
# block fires. Run: scripts/test-batching-hooks.sh   (exit 0 = all green)
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/batching-hooks.sh"
PASS=0; FAIL=0

setup() {  # fresh state dir + fast thresholds so the tests do not sleep for real
  STATE_DIR=$(mktemp -d)
  export BATCH_STATE_DIR="$STATE_DIR" BATCH_THRESHOLD=3 BATCH_WINDOW=6 BATCH_CHEAP_MS=2000 BATCH_SAME_TURN_MS=300
}
teardown() { rm -rf "$STATE_DIR"; }
ev() { printf '{"session_id":"t1","tool_name":"%s"}' "$1"; }

# one serial turn: a pre, a quick call, a post - with a gap first so it counts as a NEW turn
serial_turn() {
  sleep 0.35                                   # > SAME_TURN_MS: a new turn
  "$HOOK" pretool <<<"$(ev Read)" 2>/tmp/bt.err
  local rc=$?
  [ $rc -ne 0 ] && return $rc
  "$HOOK" posttool <<<"$(ev Read)" >/dev/null 2>&1   # immediate post = a fast call
  return 0
}

check() { # label, expected(ok|blocked), actual_rc
  if { [ "$2" = ok ] && [ "$3" -eq 0 ]; } || { [ "$2" = blocked ] && [ "$3" -ne 0 ]; }; then
    echo "  ok    $1"; PASS=$((PASS+1))
  else
    echo "  FAIL  $1 (expected $2, rc=$3)"; [ -s /tmp/bt.err ] && sed 's/^/        /' /tmp/bt.err; FAIL=$((FAIL+1))
  fi
}

echo "1. a run of serial single-call turns blocks at the threshold"
setup
serial_turn; check "turn 1 allowed" ok $?
serial_turn; check "turn 2 allowed" ok $?
serial_turn; check "turn 3 allowed" ok $?
serial_turn; check "turn 4 BLOCKED (streak hit 3)" blocked $?
grep -q "send them TOGETHER" /tmp/bt.err && { echo "  ok    block message says what to do"; PASS=$((PASS+1)); } || { echo "  FAIL  block message unhelpful"; FAIL=$((FAIL+1)); }
teardown

echo "2. it never deadlocks: the call right after a block is allowed through"
setup
serial_turn; serial_turn; serial_turn
serial_turn; check "blocked once" blocked $?
serial_turn; check "next call allowed (no deadlock)" ok $?
serial_turn; check "and the one after that" ok $?
teardown

echo "3. a batched turn is never interrupted below the threshold"
# NOTE the semantics this pins down: PreToolUse must decide on the FIRST call of a turn, when it
# cannot yet know whether a second call is coming in the same message. So a batch that begins
# exactly at the threshold has its first call blocked - the model re-sends the batch and it goes
# straight through (test 2 proves no deadlock). That is the intended flow, not a bug: the block is
# what prompts the batch. Below the threshold a batch is never interrupted, which is the common case.
setup
batched_turn() {  # two calls in one turn; echoes the rc of each
  sleep 0.35
  "$HOOK" pretool <<<"$(ev Read)" 2>/tmp/bt.err; local r1=$?
  "$HOOK" pretool <<<"$(ev Grep)" 2>/dev/null;   local r2=$?
  "$HOOK" posttool <<<"$(ev Read)" >/dev/null 2>&1
  "$HOOK" posttool <<<"$(ev Grep)" >/dev/null 2>&1
  echo "$r1 $r2"
}
serial_turn; serial_turn                       # window "11", under the threshold of 3
read -r r1 r2 <<<"$(batched_turn)"
check "batch below the threshold is never interrupted (call 1)" ok "$r1"
check "batch below the threshold is never interrupted (call 2)" ok "$r2"
teardown

echo "4. THE REGRESSION: one batched turn no longer absolves the serial run around it"
# The 2026-08-08 finding, and the reason the streak became a window. Under the old CONSECUTIVE
# counter the batch below reset the count to zero, so the two serial turns after it sat at 2 and
# never tripped - which is how a session made 147 single-call round trips out of 162 and was
# blocked twice. In a rolling window the batch is one '0' among the last six and the serial turns
# on either side of it still count.
setup
serial_turn; serial_turn                       # window "11"
read -r r1 r2 <<<"$(batched_turn)"             # window "110"
check "the batch itself is allowed" ok "$r1"
serial_turn; check "serial turn after the batch allowed (window '1101')" ok $?
serial_turn; check "BLOCKED - the batch did not erase the serial turns around it" blocked $?
grep -q "of the last" /tmp/bt.err && { echo "  ok    block message reports the window"; PASS=$((PASS+1)); } || { echo "  FAIL  block message does not report the window"; FAIL=$((FAIL+1)); }
teardown

echo "5. a SLOW call is real work, not a batchable turn"
setup
serial_turn; serial_turn                       # window "11"
slow_turn() { sleep 0.35; "$HOOK" pretool <<<"$(ev Bash)" 2>/tmp/bt.err || return $?; sleep 2.1; "$HOOK" posttool <<<"$(ev Bash)" >/dev/null 2>&1; }
slow_turn; check "the slow turn itself is allowed" ok $?   # window "110"
serial_turn; check "serial turn after it allowed" ok $?
serial_turn; check "BLOCKED at 3 serial turns inside the window" blocked $?
teardown

echo "6. a window of nothing but real work never blocks"
setup
slow_turn; slow_turn; slow_turn; slow_turn; slow_turn; slow_turn; slow_turn
slow_turn; check "7 slow turns, no block" ok $?
teardown

echo "7. sessions are independent"
setup
serial_turn; serial_turn; serial_turn
sleep 0.35
"$HOOK" pretool <<<'{"session_id":"other","tool_name":"Read"}' 2>/dev/null
check "a different session is unaffected" ok $?
teardown

echo
if [ "$FAIL" -eq 0 ]; then echo "test-batching-hooks: all $PASS checks passed"; exit 0; fi
echo "test-batching-hooks: $FAIL FAILED, $PASS passed"; exit 1
