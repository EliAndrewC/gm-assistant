#!/usr/bin/env bash
# Tests for readme-hooks.sh (constitution XVII).
# Run: scripts/test-readme-hooks.sh   (exit 0 = all green)
#
# TWO DIRECTIONS, as every guard in this repo must have. Section 2 matters most: the make-only hook
# had to learn the mention-versus-invocation lesson FOUR times (a grep, a commit message, a docstring,
# a fixture name), so this one is born knowing it - READING a README, or naming one in a git command,
# must never be blocked.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/readme-hooks.sh"
PASS=0; FAIL=0

tool_ev() { python3 -c 'import json,sys; print(json.dumps({"tool_name":sys.argv[1],"tool_input":{"file_path":sys.argv[2]}}))' "$1" "$2"; }
bash_ev() { python3 -c 'import json,sys; print(json.dumps({"tool_name":"Bash","tool_input":{"command":sys.argv[1]}}))' "$1"; }

check() { # label expected payload
  local rc; printf '%s' "$3" | "$HOOK" pretool >/dev/null 2>/tmp/rm.err; rc=$?
  if { [ "$2" = ok ] && [ "$rc" -eq 0 ]; } || { [ "$2" = blocked ] && [ "$rc" -ne 0 ]; }; then
    echo "  ok      $1"; PASS=$((PASS+1))
  else echo "  FAIL    $1 (expected $2, rc=$rc)"; FAIL=$((FAIL+1)); fi
}

echo "1. IT FIRES on any attempt to WRITE a README"
check "Write tool"                 blocked "$(tool_ev Write /repo/README.md)"
check "Edit tool"                  blocked "$(tool_ev Edit /repo/dev/README.md)"
# EVERY SPELLING, because the GM enumerated them and a case-insensitive flag is an assertion until
# it is tested. A later "tidy-up" of the regex that dropped re.I would pass every other case here.
check "README (no extension)"      blocked "$(tool_ev Write /repo/README)"
check "readme"                     blocked "$(tool_ev Write /repo/readme)"
check "Readme"                     blocked "$(tool_ev Write /repo/Readme)"
check "ReadMe"                     blocked "$(tool_ev Write /repo/ReadMe)"
check "readme.md"                  blocked "$(tool_ev Write /repo/readme.md)"
check "ReadMe.md"                  blocked "$(tool_ev Write /repo/ReadMe.md)"
check "Readme.MD"                  blocked "$(tool_ev Write /repo/Readme.MD)"
check "README.rst"                 blocked "$(tool_ev Write /repo/README.rst)"
check "README.txt"                 blocked "$(tool_ev Write /repo/README.txt)"
check "readme.markdown"            blocked "$(tool_ev Write /repo/readme.markdown)"
check "redirect"                   blocked "$(bash_ev 'cat > docs/README.md')"
check "append"                     blocked "$(bash_ev 'echo x >> docs/README.md')"
check "sed -i"                     blocked "$(bash_ev 'sed -i s/a/b/ dev/README.md')"
check "cp onto one"                blocked "$(bash_ev 'cp a.md dev/README.md')"

echo
echo "2. IT STAYS QUIET - reading, searching and versioning a README are all fine"
check "reading one"                ok "$(bash_ev 'cat README.md')"
check "grepping one"               ok "$(bash_ev 'grep -n rule dev/perf-log/README.md')"
check "git log on one"             ok "$(bash_ev 'git log --oneline README.md')"
check "writing a CLAUDE.md"        ok "$(tool_ev Write /repo/dev/CLAUDE.md)"
check "writing a normal doc"       ok "$(bash_ev 'cat > docs/session-clones.md')"
check "a filename merely starting readme-ish" ok "$(tool_ev Write /repo/readme-hooks-notes.md)"

echo
echo "3. THE REFUSAL SAYS WHERE TO PUT IT INSTEAD"
printf '%s' "$(tool_ev Write /repo/README.md)" | "$HOOK" pretool >/dev/null 2>/tmp/rm.err || true
if grep -q "CLAUDE.md in the directory it governs" /tmp/rm.err; then
  echo "  ok      names the alternative"; PASS=$((PASS+1))
else echo "  FAIL    refusal does not say where knowledge belongs"; FAIL=$((FAIL+1)); fi

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ]
