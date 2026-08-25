#!/usr/bin/env bash
# review-gate.sh - the independent review this project mandates, checked at SHIPPING time.
# (GUARD_EDIT_OK - feature 131 follow-up, 2026-08-25: the second check, a Mode B settlement map
# reviewed before it ships, left with the diagram skill; this repository has no pool maps.)
#
# It is constitutional and it was unenforced (audit 2026-08-24). It had already been skipped in
# practice, which is why it is checked by a script rather than trusted to a habit.
#
#   A SPEC-KIT SPEC IS REVIEWED BEFORE IMPLEMENTATION (constitution XVI). The reviewer catches what
#   the author cannot: on feature 127 it found two carve-outs in consecutive rounds, one of which
#   the author had flagged as a judgment call without being able to see why it was wrong. Nothing
#   compelled that review to happen.
#
# HOW IT DECIDES, and it is deliberately coarse. This checks that the RECORD exists, not that the
# review was good - a script cannot judge that. A spec must carry a FAITHFUL verdict. Coarse is
# the right setting: the expensive failure here is forgetting entirely, not reviewing badly.
#
# ESCAPE: REVIEW_GATE_OK with a reason, because there are real cases - a spec superseded before
# implementation. Using it puts the reason in the push.
set -uo pipefail

RANGE="${1:-origin/main..HEAD}"
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT" || exit 0

[ -n "${REVIEW_GATE_OK:-}" ] && { printf 'review-gate: BYPASSED - %s\n' "$REVIEW_GATE_OK"; exit 0; }

changed=$(git diff --name-only "$RANGE" 2>/dev/null || true)
[ -z "$changed" ] && exit 0
fail=""

# --- every spec.md being shipped carries a fidelity verdict -----------------------------------
for spec in $(printf '%s\n' "$changed" | grep -E '^specs/[^/]+/spec\.md$' || true); do
  [ -f "$spec" ] || continue
  if ! grep -qE 'FAITHFUL' "$spec"; then
    printf '\n\033[1mREVIEW GATE: %s has no fidelity verdict.\033[0m\n' "$spec"
    printf 'Constitution XVI: a specification is reviewed against the GM'"'"'S OWN WORDS before\n'
    printf 'implementation, by someone other than its author. Run the `spec-fidelity` subagent in\n'
    printf 'Mode 2, give it the GM request VERBATIM (not the plan - a spec checked against its own\n'
    printf 'plan is tested for self-consistency, which a wrong spec passes), and record the verdict\n'
    printf 'in a "## Review history" section.\n'
    fail="$fail $spec"
  fi
done

if [ -n "$fail" ]; then
  printf '\n\033[1mreview-gate FAILED:%s\033[0m\n' "$fail"
  printf 'If a case is genuinely exempt - a spec superseded before implementation -\n'
  printf 'set REVIEW_GATE_OK="<reason>" so the reason ships with the push.\n\n'
  exit 1
fi
printf 'review-gate: clean\n'
