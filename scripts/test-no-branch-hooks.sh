#!/usr/bin/env bash
# test-no-branch-hooks.sh - prove no-branch-hooks.sh still bites, and still lets the legitimate
# cases through. A guard nobody tests is a guard that quietly stops guarding (the same reasoning
# that put a --selftest in check-duplicate-defs.py).
set -u
HOOK="$(cd "$(dirname "$0")" && pwd)/no-branch-hooks.sh"
pass=0 fail=0

run() {  # run <command-string> -> sets RC
  printf '{"tool_input":{"command":%s}}' "$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$1")" \
    | "$HOOK" pretool >/dev/null 2>&1
  RC=$?
}

expect_block() {
  run "$1"
  if [ "$RC" -eq 2 ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL: expected BLOCK, got rc=$RC for: $1"; fi
}
expect_allow() {
  run "$1"
  if [ "$RC" -eq 0 ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL: expected ALLOW, got rc=$RC for: $1"; fi
}

# --- blocked: every spelling of "make a branch"
expect_block 'git checkout -b 017-new-feature'
expect_block 'git checkout -B 017-new-feature'
expect_block 'git switch -c 017-new-feature'
expect_block 'git switch -C 017-new-feature'
expect_block 'git switch --create 017-new-feature'
expect_block 'cd /gm-assistant/.clones/x && git checkout -b foo && echo done'

# --- allowed: everything that is not branch CREATION
expect_allow 'git checkout main'
expect_allow 'git switch main'
expect_allow 'git branch -d 016-old-feature'
expect_allow 'git branch --list'
expect_allow 'git checkout -- somefile.py'
expect_allow 'git log --oneline -5'

# --- allowed: the visible escape hatch, and other repos
expect_allow 'git checkout -b bisect-tmp   # NO_BRANCH_OK throwaway bisect'
expect_allow 'git -C /host-l7r-repo checkout -b whatever'

# --- allowed: wrong mode, or no command at all
printf '{"tool_input":{"command":"git checkout -b x"}}' | "$HOOK" posttool >/dev/null 2>&1
[ $? -eq 0 ] && pass=$((pass+1)) || { fail=$((fail+1)); echo "FAIL: posttool mode should be a no-op"; }
printf '{}' | "$HOOK" pretool >/dev/null 2>&1
[ $? -eq 0 ] && pass=$((pass+1)) || { fail=$((fail+1)); echo "FAIL: empty input should be a no-op"; }

echo "test-no-branch-hooks: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
