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
grep -q "patch MISS" /tmp/bt.err && { echo "  ok    block message carries the retry-patch fold tip"; PASS=$((PASS+1)); } || { echo "  FAIL  no retry-patch tip in the message"; FAIL=$((FAIL+1)); }
grep -q "pad with no-op" /tmp/bt.err && { echo "  ok    block message forbids padding the window"; PASS=$((PASS+1)); } || { echo "  FAIL  no anti-padding tip in the message"; FAIL=$((FAIL+1)); }
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

echo "8. a BACKGROUNDED call is never counted as recon, and is never blocked"
# Found in use, minutes after the window shipped: `make done` launched with run_in_background
# returns to the model in milliseconds, so the duration test reads the cheapest possible turn -
# and the hook blocked the one thing the loop rules most want you to do.
setup
bg_turn() { sleep 0.35; "$HOOK" pretool <<<'{"session_id":"t1","tool_name":"Bash","tool_input":{"command":"make done","run_in_background":true}}' 2>/tmp/bt.err; local rc=$?; [ $rc -ne 0 ] && return $rc; "$HOOK" posttool <<<'{"session_id":"t1","tool_name":"Bash","tool_input":{"command":"make done","run_in_background":true}}' >/dev/null 2>&1; return 0; }
serial_turn; serial_turn; serial_turn          # window "111" - the very next serial call blocks
bg_turn; check "the backgrounded launch is NOT blocked, even standing at the threshold" ok $?
serial_turn; check "a real serial call right after it still blocks" blocked $?
teardown
setup
bg_turn; bg_turn; bg_turn; bg_turn; bg_turn; check "a run of backgrounded launches never blocks" ok $?
teardown
# NOTE what this does NOT claim: a backgrounded turn is still a TURN, so it ages the window like any
# other. Five of them push a serial turn out of a window of six, which is correct - the window asks
# "how much of my RECENT work was one-call recon", and work you did five turns ago is not recent.

echo "7. sessions are independent"
setup
serial_turn; serial_turn; serial_turn
sleep 0.35
"$HOOK" pretool <<<'{"session_id":"other","tool_name":"Read"}' 2>/dev/null
check "a different session is unaffected" ok $?
teardown

bash_turn() {  # one Bash turn with the given command string (plain chars only)
  sleep 0.35
  printf '{"session_id":"t1","tool_name":"Bash","tool_input":{"command":"%s"}}' "$1" | "$HOOK" pretool 2>/tmp/bt.err
  local rc=$?
  [ $rc -ne 0 ] && return $rc
  printf '{"session_id":"t1","tool_name":"Bash","tool_input":{"command":"%s"}}' "$1" | "$HOOK" posttool >/dev/null 2>&1
  return 0
}

echo "9. only a recon-SHAPED call is ever blocked (GM 2026-08-10)"
# The 021 profile: 49 of 52 blocks landed on heredoc patch scripts or already-folded commands.
# The batching opportunity is BEHIND a substantive call - blocking it just re-sends it verbatim.
setup
serial_turn; serial_turn; serial_turn          # window "111" - bar is armed
bash_turn "python3 - <<PYEOF_INNER"; check "a heredoc patch script passes at the armed bar" ok $?
bash_turn "grep -n foo x.py && sed -n 1,4p y.py"; check "an &&-fold (the requested batching) passes" ok $?
bash_turn "python3 -m pytest test_checks.py -q"; check "a test run passes" ok $?
sleep 0.35
printf '{"session_id":"t1","tool_name":"Edit","tool_input":{"file_path":"x.py"}}' | "$HOOK" pretool 2>/tmp/bt.err
check "an Edit (real work) passes" ok $?
printf '{"session_id":"t1","tool_name":"Edit","tool_input":{"file_path":"x.py"}}' | "$HOOK" posttool >/dev/null 2>&1
bash_turn "grep -n foo settlement.py"; check "a naked single grep IS blocked" blocked $?
teardown

echo "10. after a block the bar re-arms HIGHER (3 -> 6), so a grind session is not blocked forever"
setup
serial_turn; serial_turn; serial_turn
serial_turn; check "first block at 3" blocked $?
serial_turn; serial_turn; serial_turn          # window "111" again
serial_turn; check "NOT re-blocked at 3 - the bar doubled (would have re-fired pre-backoff)" ok $?
serial_turn; serial_turn                       # window "111111": the whole window is serial
serial_turn; check "re-blocked only at the full window of 6" blocked $?
teardown

echo "11. the raised bar DECAYS back to the threshold as turns batch"
setup
serial_turn; serial_turn; serial_turn
serial_turn; check "block raises the bar to 6" blocked $?
slow_turn; slow_turn; slow_turn                # three real-work turns: bar decays 6 -> 5 -> 4 -> 3
serial_turn; serial_turn; serial_turn          # window "000111"
serial_turn; check "blocked at 3 again - the bar decayed home" blocked $?
teardown

echo
if [ "$FAIL" -eq 0 ]; then echo "test-batching-hooks: all $PASS checks passed"; exit 0; fi
echo "test-batching-hooks: $FAIL FAILED, $PASS passed"; exit 1
