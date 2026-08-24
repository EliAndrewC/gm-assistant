#!/usr/bin/env bash
# readme-hooks.sh - a PreToolUse hook that stops a session writing a README (constitution XVII).
#
# WHY, and the reason is mechanical rather than stylistic. A README is NOT loaded into a session's
# context. A directory CLAUDE.md IS, automatically, whenever work happens in that directory. So
# anything a session must KNOW in order to act correctly is invisible in a README - it gets found
# only by a session that happens to look.
#
# THE MOTIVATING CASE (2026-08-24). dev/perf-log/README.md carried the rule that an append-only
# shared log must be a DIRECTORY, because two clones appending to one file conflict on every push. A
# session read that file during an unrelated audit, QUOTED FROM IT, and hours later created a
# single-file run-log.jsonl - breaking a rule it had read the same day. Had the file been a CLAUDE.md
# it would have been in context at the moment the decision was made.
#
# The GM's rule, plainly: "you personally should literally never touch a readme file because a readme
# file is something that should be written by a human for a human."
#
# NO ESCAPE HATCH, deliberately. Every other guard here has one because its rule has real exceptions.
# This one does not: there is no case where a session needs to write a README, because everything a
# session would put there belongs somewhere a session will actually read. If the GM wants one, the GM
# writes it - which is not something a hook can or should try to detect.
set -uo pipefail

MODE="${1:-pretool}"
[ "$MODE" = pretool ] || exit 0
INPUT=$(cat)

HIT=$(printf '%s' "$INPUT" | python3 -c '
import json, re, sys
try:
    d = json.load(sys.stdin)
except Exception:
    print(""); raise SystemExit
inp = d.get("tool_input", {}) or {}
if d.get("tool_name", "") in ("Write", "Edit", "NotebookEdit"):
    p = inp.get("file_path", "")
    # A README IS `README` OR `README.<ext>` - not anything that merely STARTS with the word. The
    # first cut used README[^/]*$ and blocked `scripts/readme-hooks.sh`, which is to say this hook
    # could not be edited or tested through the channel it guards. Sixth instance in this repo of a
    # matcher that confused a name with the thing it names.
    print(p if re.search(r"(^|/)README(\.[A-Za-z0-9]+)?$", p, re.I) else "")
    raise SystemExit
cmd = inp.get("command", "") or ""
# a shell command that WRITES a readme - the name adjacent to the operator, never merely present,
# so `cat README.md` and `git log README.md` pass. Same mention-versus-invocation rule the
# make-only hook had to learn four times.
pat = r"(?:>>?\s*|sed\s+-i\b[^;|&]*?|tee\s+(?:-a\s+)?|cp\s+\S+\s+|mv\s+\S+\s+)[\w./-]*README(?:\.[A-Za-z0-9]+)?(?=\s|$)"
m = re.search(pat, cmd, re.I) or re.search(r"README(?:\.[A-Za-z0-9]+)?[\x27\x22]\s*\)?\s*\)?\s*\.write_text", cmd, re.I)
print(m.group(0) if m else "")
')

[ -z "$HIT" ] && exit 0

cat >&2 <<TAIL
BLOCKED: writing a README ($HIT).

A README is not loaded into a session's context. A directory CLAUDE.md is - automatically, whenever
work happens in that directory. So anything you would put in a README is invisible to the next
session unless it happens to look, which is to say by luck.

Put it where it will actually be read:

  - a CLAUDE.md in the directory it governs, for a rule that must be known while working there
  - a topic doc referenced from a CLAUDE.md, when it is long enough that always loading it is waste

WHAT THIS COST, once: dev/perf-log/README.md carried "an append-only shared log must be a DIRECTORY,
because concurrent clones conflict on every push". A session read that file, quoted it, and hours
later created a single-file run-log.jsonl. Had it been a CLAUDE.md the rule would have been in
context when it mattered. It is one now.

No escape hatch here, on purpose. A README is written by a human for a human; if the GM wants one,
the GM writes it.

(scripts/readme-hooks.sh; constitution XVII, GM 2026-08-24)
TAIL
exit 2
