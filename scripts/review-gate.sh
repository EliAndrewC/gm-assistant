#!/usr/bin/env bash
# review-gate.sh - the two independent reviews this project mandates, checked at SHIPPING time.
#
# Both are constitutional and both were unenforced (audit 2026-08-24). Both have already been skipped
# in practice, which is why they are checked by a script rather than trusted to a habit.
#
#   1. A SPEC-KIT SPEC IS REVIEWED BEFORE IMPLEMENTATION (constitution XVI). The reviewer catches
#      what the author cannot: on feature 127 it found two carve-outs in consecutive rounds, one of
#      which the author had flagged as a judgment call without being able to see why it was wrong.
#      Nothing compelled that review to happen.
#
#   2. A MODE B SETTLEMENT MAP IS REVIEWED BEFORE IT SHIPS (CLAUDE.md, Principle I's rationale). On
#      2026-07-27 three provincial-city maps went out unreviewed and nothing warned.
#
# HOW IT DECIDES, and it is deliberately coarse. This checks that the RECORD exists, not that the
# review was good - a script cannot judge that. A spec must carry a FAITHFUL verdict; a changed pool
# manifest must have its `.notes.md` touched in the same push. Coarse is the right setting: the
# expensive failure here is forgetting entirely, not reviewing badly.
#
# ESCAPE: REVIEW_GATE_OK with a reason, because there are real cases - a spec superseded before
# implementation, a manifest changed by a mechanical sweep. Using it puts the reason in the push.
set -uo pipefail

RANGE="${1:-origin/main..HEAD}"
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT" || exit 0

[ -n "${REVIEW_GATE_OK:-}" ] && { printf 'review-gate: BYPASSED - %s\n' "$REVIEW_GATE_OK"; exit 0; }

changed=$(git diff --name-only "$RANGE" 2>/dev/null || true)
[ -z "$changed" ] && exit 0
fail=""

# --- 1. every spec.md being shipped carries a fidelity verdict --------------------------------
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

# --- 2. a re-rolled pool map has a review logged beside it ------------------------------------
for man in $(printf '%s\n' "$changed" | grep -E '^\.claude/skills/diagram/pool/.*\.json$' || true); do
  notes="${man%.json}.notes.md"
  [ -f "$notes" ] || continue          # a map with no notes file predates the convention
  if ! printf '%s\n' "$changed" | grep -qxF "$notes"; then
    printf '\n\033[1mREVIEW GATE: %s changed, but %s did not.\033[0m\n' "$(basename "$man")" "$(basename "$notes")"
    printf 'A Mode B map gets an independent `settlement-review` before it ships - the author is not\n'
    printf 'a reliable reviewer of their own visual output. Log the pass in the notes file'"'"'s Review\n'
    printf 'section. On 2026-07-27 three city maps shipped unreviewed and nothing warned.\n'
    fail="$fail $(basename "$man")"
  fi
done

if [ -n "$fail" ]; then
  printf '\n\033[1mreview-gate FAILED:%s\033[0m\n' "$fail"
  printf 'If a case is genuinely exempt - a superseded spec, a mechanical sweep across every map -\n'
  printf 'set REVIEW_GATE_OK="<reason>" so the reason ships with the push.\n\n'
  exit 1
fi
printf 'review-gate: clean\n'
