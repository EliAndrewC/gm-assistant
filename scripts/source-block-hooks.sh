#!/usr/bin/env bash
# source-block-hooks.sh - the GM's own writing is not editable (constitution V, NON-NEGOTIABLE).
#
# Text between <!-- SOURCE: GM NOTES - DO NOT MODIFY --> and <!-- END SOURCE --> is the GM's original
# prose. It must never be modified, rephrased, summarized, reworded or "improved". Only the GM edits
# it, and only when they say so.
#
# WHY A HOOK FOR A RULE NOBODY HAS BROKEN. Because it is the one rule where breaking it is both easy
# and hard to notice. A session tidying a document, fixing a spelling, or rewrapping a paragraph
# passes straight through a SOURCE block without registering that the register changed - and the
# damage is to the GM's own words, in a file they trust to hold them verbatim. Every other guard here
# protects time; this one protects the thing the project exists to serve.
#
# It also removes a live hazard this repo now carries: `house-style-hooks.sh` flags British spellings,
# and the GM's prose is full of legitimately British spellings. A session "fixing" one inside a SOURCE
# block would be doing exactly what Principle V forbids while believing it was following CLAUDE.md.
#
# HOW IT DECIDES. For an Edit, the old_string must not fall inside a SOURCE block in the target file;
# for a Write, the new content must not alter any SOURCE block the file already had. Both are checked
# against the file ON DISK, so this is a real containment test rather than a guess from the payload.
#
# ESCAPE: SOURCE_EDIT_OK, for the case the constitution names - "only when they explicitly instruct
# you to do so". The escape exists because that instruction is real and a hook cannot hear it; using
# it puts the GM's instruction in the diff, which is where it belongs.
set -uo pipefail

MODE="${1:-pretool}"
[ "$MODE" = pretool ] || exit 0
INPUT=$(cat)

REPORT=$(printf '%s' "$INPUT" | python3 -c '
import json, re, sys, pathlib
try:
    d = json.load(sys.stdin)
except Exception:
    print(""); raise SystemExit
inp = d.get("tool_input", {}) or {}
path = inp.get("file_path", "") or ""
old = inp.get("old_string") or ""
new = inp.get("content") or ""
if "SOURCE_EDIT_OK" in (inp.get("new_string") or "") + new:
    print(""); raise SystemExit
try:
    disk = pathlib.Path(path).read_text(encoding="utf-8")
except Exception:
    print(""); raise SystemExit
BLOCK = re.compile(r"<!--\s*SOURCE: GM NOTES.*?<!--\s*END SOURCE\s*-->", re.S | re.I)
blocks = [m.group(0) for m in BLOCK.finditer(disk)]
if not blocks:
    print(""); raise SystemExit
if old:                                    # Edit: is the anchor inside a protected block?
    for b in blocks:
        if old.strip() and old.strip() in b:
            print(f"an Edit whose anchor lies inside a SOURCE block in {pathlib.Path(path).name}")
            raise SystemExit
if new:                                    # Write: does every existing block survive verbatim?
    missing = [b for b in blocks if b not in new]
    if missing:
        print(f"a Write that would change or drop {len(missing)} SOURCE block(s) in {pathlib.Path(path).name}")
        raise SystemExit
print("")
')

[ -z "$REPORT" ] && exit 0

cat >&2 <<TAIL
BLOCKED: $REPORT

That text is the GM's own writing. Constitution V (NON-NEGOTIABLE): content between
<!-- SOURCE: GM NOTES - DO NOT MODIFY --> and <!-- END SOURCE --> must never be modified, rephrased,
summarized, reworded, or "improved". Only the GM edits it.

This includes edits that feel like housekeeping:

  - "fixing" a British spelling. Their prose is theirs; house style governs OUR text, not theirs.
  - rewrapping, re-punctuating, or tightening a sentence.
  - updating a SOURCE block to match the current l7r.md. Drift is EXPECTED - a block is a frozen
    point-in-time snapshot, not a live mirror. The canonical for any topic is always l7r.md.

If the GM has actually told you to edit it, put SOURCE_EDIT_OK in the edit with their instruction, so
the reason is in the diff.

(scripts/source-block-hooks.sh; constitution V)
TAIL
exit 2
