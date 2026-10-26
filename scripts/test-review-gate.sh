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
# Each case ships CODE beside its spec (`echo impl >> seed.txt`): a delta of a new spec directory
# alone is now the number claim and passes (section 4), so without the code these cases would test
# the exemption while claiming to test the requirement - the diagram repository's same finding.
mkrepo a; echo "# spec" > specs/900-x/spec.md; echo impl >> seed.txt; git add -A; git commit -qm s
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

mkrepo g2; echo "# spec" > specs/900-x/spec.md; git add -A; git commit -qm s
if ( cd "$T/g2" && REVIEW_GATE_OK=1 "$GATE" main..HEAD >/dev/null 2>&1 ); then
  echo "  FAIL    an escape with no reason was accepted"; FAIL=$((FAIL+1))
else echo "  ok      ...but an escape with no REASON is refused"; PASS=$((PASS+1)); fi

echo
echo "3. A VERDICT, not a mention (ported from the diagram repository, its feature 156)"
mkrepo v1; printf '# spec\n\n## Review history\n- **Round 1: NOT FAITHFUL.** FR-003 carved out a case.\n' > specs/900-x/spec.md
echo impl >> seed.txt; git add -A; git commit -qm s
check "a spec whose only verdict is NOT FAITHFUL" v1 blocked
mkrepo v2; printf '# spec\n\nThis feature is faithful to nothing in particular: FAITHFUL is just a word here.\n' > specs/900-x/spec.md
echo impl >> seed.txt; git add -A; git commit -qm s
check "a spec that only MENTIONS the word" v2 blocked
mkrepo v3; printf '# spec\n\n- **Round 1: NOT FAITHFUL.** x\n- **Round 2 (spec-fidelity): FAITHFUL.** fixed\n' > specs/900-x/spec.md
git add -A; git commit -qm s
check "a rejected round followed by a FAITHFUL one" v3 ok

echo
echo "4. THE NUMBER CLAIM passes, and only the number claim (diagram feature 165; here 2026-10-26)"
# A spec already in main, unreviewed: what a claim leaves behind for the implementation push.
prerepo() { # repo
  rm -rf "$T/$1"; mkdir -p "$T/$1/specs/900-x"; cd "$T/$1" || return 1
  git init -q .; git config user.email t@t; git config user.name t
  echo base > seed.txt; echo "# a spec claimed earlier, still unreviewed" > specs/900-x/spec.md
  git add -A; git commit -qm base; git branch -q -M main; git checkout -q -b work
}
mkrepo n1; mkdir -p specs/901-new; echo "# spec" > specs/901-new/spec.md; echo req > specs/901-new/gm-request.md
git add -A; git commit -qm claim
check "one new spec directory, no verdict: the claim passes" n1 ok
mkrepo n2; mkdir -p specs/901-new; echo "# spec" > specs/901-new/spec.md; echo work >> seed.txt
git add -A; git commit -qm claim-plus
check "...plus one file elsewhere: refused" n2 blocked
mkrepo n3; mkdir -p specs/901-new specs/902-other; echo "# spec" > specs/901-new/spec.md; echo "# spec" > specs/902-other/spec.md
git add -A; git commit -qm two-claims
check "...two new spec directories at once: refused" n3 blocked
mkrepo n4; mkdir -p specs/901-new; echo notes > specs/901-new/plan.md
git add -A; git commit -qm no-spec
check "...a new directory with no spec.md is no claim (and owes nothing: no spec to judge)" n4 ok
prerepo n5; echo "- [ ] T1" > specs/900-x/tasks.md; git add -A; git commit -qm tasks
check "...adding tasks.md to a claimed, unreviewed spec owes the verdict" n5 blocked
prerepo n6; echo code > seed.txt; echo more >> specs/900-x/spec.md; git add -A; git commit -qm impl
check "...and so does editing it alongside code" n6 blocked

echo
echo "5. GRANDFATHERED: a spec first committed before the gate existed (2026-08-24)"
rm -rf "$T/o1"; mkdir -p "$T/o1/specs/001-old"; cd "$T/o1" || exit 1
git init -q .; git config user.email t@t; git config user.name t
echo "# an old spec" > specs/001-old/spec.md; git add -A
GIT_AUTHOR_DATE=2026-07-01T12:00:00 GIT_COMMITTER_DATE=2026-07-01T12:00:00 git commit -qm old
git branch -q -M main; git checkout -q -b work
echo notes > specs/001-old/research.md; git add -A; git commit -qm touch
check "a push touching a pre-gate spec's directory" o1 ok

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ]
