#!/usr/bin/env bash
# Tests for review-gate.sh (constitution XVI).
# Run: scripts/test-review-gate.sh   (exit 0 = all green)
#
# TWO DIRECTIONS (constitution XVIII). Section 2 carries the cases that must NOT block, and they
# matter more here than anywhere else in the repo: a shipping gate that fires on correct work stops a
# push at the END of a feature, when the session most wants it over with, which is exactly when a
# bypass gets reached for without much thought.
#
# The pool-map cases (a re-rolled Mode B map with no review logged) left with the diagram skill on
# 2026-08-25 (feature 131 follow-up); this repository has no pool maps for the gate to watch.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GATE="$HERE/review-gate.sh"
PASS=0; FAIL=0
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT

# A repo whose `main` already holds the pre-existing state, then a `work` branch to change on.
mkrepo() {
  rm -rf "$T/$1"; mkdir -p "$T/$1/specs/900-x"; cd "$T/$1" || return 1
  git init -q .; git config user.email t@t; git config user.name t
  echo base > seed.txt
  git add -A; git commit -qm base; git branch -q -M main; git checkout -q -b work
}

check() { # label repo expected
  local rc; ( cd "$T/$2" && "$GATE" main..HEAD >/dev/null 2>&1 ); rc=$?
  if { [ "$3" = ok ] && [ "$rc" -eq 0 ]; } || { [ "$3" = blocked ] && [ "$rc" -ne 0 ]; }; then
    echo "  ok      $1"; PASS=$((PASS+1))
  else echo "  FAIL    $1 (expected $3, rc=$rc)"; FAIL=$((FAIL+1)); fi
}

echo "1. IT FIRES on work that skipped a mandated review"
mkrepo a; echo "# spec" > specs/900-x/spec.md; git add -A; git commit -qm s
check "a spec with no fidelity verdict" a blocked

echo
echo "2. IT STAYS QUIET on work that did the review"
mkrepo c; printf '# spec\n\n## Review history\nRound 1 - FAITHFUL\n' > specs/900-x/spec.md
git add -A; git commit -qm s
check "a spec carrying a FAITHFUL verdict" c ok

mkrepo e; echo hi > seed2.txt; git add -A; git commit -qm doc
check "a change touching no spec" e ok

mkrepo h; mkdir -p specs/900-x/sub; echo notes > specs/900-x/research.md; git add -A; git commit -qm research
check "a spec directory change that is not spec.md" h ok

mkrepo g; echo "# spec" > specs/900-x/spec.md; git add -A; git commit -qm s
if ( cd "$T/g" && REVIEW_GATE_OK="superseded before implementation" "$GATE" main..HEAD >/dev/null 2>&1 ); then
  echo "  ok      the documented escape"; PASS=$((PASS+1))
else echo "  FAIL    the escape did not work"; FAIL=$((FAIL+1)); fi

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ]
