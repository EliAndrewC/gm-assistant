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
#
# GUARD_EDIT_OK (2026-10-26, GM: "the diagram repo has a better approach for this ... steal and
# implement here as well"): the number claim, the judged directory, the verdict-not-a-mention test,
# the three-dot range and the reasoned escape are the diagram repository's review-gate.sh (its
# features 156, 165 and 170), ported. The grandfather date is this repository's own.
set -uo pipefail

# THREE DOTS, the merge base (diagram, 2026-09-26). The gate runs BEFORE sync-with-main's locked
# pull, and a two-dot diff compares TREES - so every spec another session pushed since this clone
# last synced read as this clone's change.
RANGE="${1:-origin/main...HEAD}"
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT" || exit 0

# A REASON, not just a value (diagram feature 170): `REVIEW_GATE_OK=1` explains nothing to whoever
# audits the push later, which is the whole point of the escape. Two words, eight characters.
if [ -n "${REVIEW_GATE_OK:-}" ]; then
  if [ "$(printf '%s' "$REVIEW_GATE_OK" | wc -w)" -lt 2 ] || [ "${#REVIEW_GATE_OK}" -lt 8 ]; then
    printf 'review-gate: REVIEW_GATE_OK needs a REASON, not just a value - two words and eight characters.\n' >&2
    printf 'It ships with the push and is what a later audit reads, so say what makes this case exempt.\n' >&2
    exit 1
  fi
  printf 'review-gate: BYPASSED - %s\n' "$REVIEW_GATE_OK"
  exit 0
fi

changed=$(git diff --name-only "$RANGE" 2>/dev/null || true)
[ -z "$changed" ] && exit 0
fail=""

# THE NUMBER CLAIM IS NOT AN IMPLEMENTATION (diagram feature 165, the GM's ruling 2026-08-30).
# `docs/session-clones.md` has a session push a new `specs/NNN-slug/` the moment `spec.md` is written,
# and this gate refused that push every time, for lacking a verdict a spec written a minute ago cannot
# carry (here: feature 230's claim, 2026-10-26, which needed the escape). So a delta that is EXACTLY
# one new spec directory - every path under it an ADDITION, `spec.md` among them, nothing anywhere
# else - passes. No implementation can ride in such a delta, so reviewed-before-implementation holds
# by construction; the moment one other file joins it, the verdict is required again.
claim_only=""
spec_dirs=$(printf '%s\n' "$changed" | sed -n 's|^\(specs/[^/]*\)/.*|\1|p' | sort -u)
if [ -n "$spec_dirs" ] && [ "$(printf '%s\n' "$spec_dirs" | wc -l)" -eq 1 ] \
   && ! printf '%s\n' "$changed" | grep -qv '^specs/' \
   && ! git diff --name-status "$RANGE" -- "$spec_dirs" 2>/dev/null | awk '{print $1}' | grep -qv '^A$' \
   && git diff --name-status "$RANGE" -- "$spec_dirs/spec.md" 2>/dev/null | grep -q '^A'; then
  # THE SPEC ITSELF MUST BE ONE OF THE NEW FILES: adding only `tasks.md` to a directory main already
  # holds is also "every file new", and that is the implementation push, which owes the verdict.
  claim_only=1
  printf 'review-gate: NUMBER CLAIM - %s alone, every file new. The fidelity verdict is owed before\n' "$spec_dirs"
  printf '             implementation, not before the number is reserved.\n'
fi

# --- every spec being shipped carries a fidelity verdict --------------------------------------
# WHICH SPECS ARE JUDGED: every feature directory the delta touches, not only a changed spec.md.
# Without that, the claim exemption opens a hole one step removed - claim with an unreviewed spec,
# then push the implementation, whose delta touches tasks.md and the code but not spec.md.
touched=$(printf '%s\n' "$changed" | sed -n 's|^\(specs/[^/]*\)/.*|\1/spec.md|p' | sort -u)
for spec in $([ -z "$claim_only" ] && printf '%s\n' "$touched" || true); do
  [ -f "$spec" ] || continue
  # GRANDFATHERED: a spec first committed before this gate existed (2026-08-24) predates the rule and
  # has no review to record - measured 2026-10-26, exactly 001, 002, 003, 004 and 011. Judging their
  # directories would block any later push touching them for a verdict nobody can give.
  first=$(git log --diff-filter=A --format=%cs -- "$spec" 2>/dev/null | tail -1)
  if [ -n "$first" ] && [[ "$first" < "2026-08-24" ]]; then continue; fi
  # A VERDICT, not a MENTION (diagram feature 156): "NOT FAITHFUL" - a spec a reviewer REJECTED - and
  # prose that merely discusses the word both satisfied a bare `grep FAITHFUL`. The occurrence must
  # survive dropping negated lines and sit on a line naming the review (a status, a round, a verdict).
  if ! grep -E 'FAITHFUL' "$spec" | grep -viE 'NOT[[:space:]]+\**FAITHFUL' | grep -qiE 'status|verdict|round|spec-fidelity'; then
    printf '\n\033[1mREVIEW GATE: %s has no fidelity verdict.\033[0m\n' "$spec"
    printf 'Constitution XVI: a specification is reviewed against the GM'"'"'S OWN WORDS before\n'
    printf 'implementation, by someone other than its author. Run the `spec-fidelity` subagent in\n'
    printf 'Mode 2, give it the GM request VERBATIM (not the plan - a spec checked against its own\n'
    printf 'plan is tested for self-consistency, which a wrong spec passes), and record the verdict\n'
    printf 'in a "## Review history" section, e.g. "- **Round 2 (spec-fidelity): FAITHFUL.**"\n'
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
