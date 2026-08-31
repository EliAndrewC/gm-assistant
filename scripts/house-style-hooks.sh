#!/usr/bin/env bash
# house-style-hooks.sh - the two house-style rules that a regex can actually decide.
#
# CLAUDE.md states both project-wide, for EVERYTHING: generated content, prose, docs, specs, skill
# files, tests, comments, and code identifiers.
#
#   1. Hyphens only - no em-dash (U+2014) or en-dash (U+2013), anywhere.
#   2. American spellings, never British ones. The word list is CLAUDE.md's own.
#
# WHY THESE TWO AND NOT THE REST OF THE STYLE GUIDE. They are decidable without judgment. The rules
# next to them are NOT, and enforcing those would be a mistake: "people" has a caste meaning but is
# correct in narrative and vow voice; office-holders are they/them generically but named characters
# keep their pronouns. A hook cannot see voice, and one that fires on correct prose teaches a session
# to bypass every hook - which this project has already paid for.
#
# THE VIOLATIONS ARE REAL, not hypothetical (audit 2026-08-24): `licence` shipped in
# specs/123-lane-web-and-cluster-shape/tasks.md and `centre` in specs/125-lanes-do-not-break/spec.md,
# both against a rule documented project-wide since long before either.
#
# TWO EXEMPTIONS, and both are load-bearing:
#
#   - THE GM'S OWN WRITING. Never "correct" text inside a <!-- SOURCE: GM NOTES --> block, or in
#     l7r.md, or a direct quotation of either. Their prose is theirs.
#   - A FILE THAT STATES THE RULE quotes the forbidden words by necessity - CLAUDE.md lists every
#     British spelling it forbids. Flagging those would make the rule unwritable.
set -uo pipefail

MODE="${1:-pretool}"
[ "$MODE" = pretool ] || exit 0
INPUT=$(cat)

REPORT=$(printf '%s' "$INPUT" | python3 -c '
import json, re, sys
try:
    d = json.load(sys.stdin)
except Exception:
    print(""); raise SystemExit
inp = d.get("tool_input", {}) or {}
path = inp.get("file_path", "") or ""
body = (inp.get("new_string") or "") + (inp.get("content") or "")

# A BASH HEREDOC IS A WRITE TOO. This hook matched only the Edit/Write tools at first, so
# `python3 - <<PY ... write_text(prose) ... PY` walked straight past it - and the author did exactly
# that, minutes after shipping the guard, to write a spec. Same hole layer 3 had, same fix: look at
# what the command actually writes. Only heredoc BODIES are inspected, because that is where prose
# travels; a redirect of a single echo is not worth the false positives.
if not body and d.get("tool_name") == "Bash":
    cmd = inp.get("command", "") or ""
    bodies = re.findall(r"<<-?\s*[\x27\x22]?\w+[\x27\x22]?\n(.*?)\n\s*\w+\b", cmd, re.S)
    body = "\n".join(bodies)
    # the target matters as much as the text: a heredoc writing the GM own words is exempt below,
    # so pick up any path the command mentions
    path = path or " ".join(re.findall(r"[\w./-]+\.(?:md|py|sh|toml|json)", cmd))
if not body:
    print(""); raise SystemExit
# the GM own writing, and the files that must quote the rule
# gm-request.md is a verbatim transcript of the GM speaking - correcting it would defeat its purpose
if "/host-l7r-repo" in path or path.endswith("l7r.md") or "gm-request.md" in path:
    print(""); raise SystemExit
# GUARD_EDIT_OK: fixing a guard that FIRES ON CORRECT WORK. `test-house-style-hooks.sh` was exempt
# but it is a two-line wrapper; the cases it runs live in `test_hooks_cases.py`, which has to quote
# every forbidden spelling in order to assert that they block. Adding a case to this guard was
# therefore blocked BY this guard - the "check the escape first, or the guard cannot be repaired
# through the channel it guards" failure, met head on while adding the doubled-l family.
if re.search(r"(^|/)(CLAUDE\.md|constitution\.md|l7r-style\.md|house-style-hooks\.sh|test-house-style-hooks\.sh|test_hooks_cases\.py)$", path):
    print(""); raise SystemExit
# a SOURCE block inside the added text is the GM speaking; drop it before looking
body = re.sub(r"<!--\s*SOURCE: GM NOTES.*?<!--\s*END SOURCE\s*-->", " ", body, flags=re.S | re.I)

hits = []
if "—" in body: hits.append("em-dash (U+2014)")
if "–" in body: hits.append("en-dash (U+2013)")
BRIT = ("colour","colours","centre","centres","centred","behaviour","behaviours","neighbour",
        "neighbours","neighbourhood","analyse","analysed","organise","organised","recognise",
        "recognised","defence","licence","practise","sceptic","storey","whilst","travelled",
        "modelled","programme","metre","litre","mould","plough","kerb","draught","ageing",
        "marvellous","jewellery","skilful","artefact","demesne","labelled","labelling","judgement",
        "catalogue","honour","honours","grey",
        # GUARD_EDIT_OK: STRENGTHENING this guard, not relaxing it - adding words it should always
        # have caught. CLAUDE.md states the doubled-`l` family as a RULE and then enumerates only
        # four of its members, so the prose and the list disagreed and the list won. Measured
        # 2026-08-31: `cruellest` twice and `duelling` once shipped into webapp/l7r/mention/lore/
        # through a green gate and were caught by a prose reviewer, not by this hook. A rule
        # stated beside a list that does not implement it is not enforced. Add to this list
        # whenever you meet another member of the family.
        "cruellest","crueller","cruelly","duelling","duelled","cancelled","cancelling",
        "travelling","modelling","fuelled","fuelling","signalled","signalling","counselled",
        "counselling","totalled","marvelled","equalled","quarrelled","levelled","rivalled")
# GUARD_EDIT_OK: STRENGTHENING - the exact-word match let INFLECTIONS through.
# `\bcatalogue\b` does not match `catalogued`, so `catalogued` shipped into
# webapp/l7r/mention/lore/ and was caught by a prose reviewer rather than here, exactly like the
# doubled-l family before it. Allowing the four regular English suffixes closes the class rather
# than the instance - `catalogues`, `catalogued`, `cataloguing`, `colours`, `moulded`, `kerbs`.
# Chosen over a bare `[a-z]*` tail, which would flag `greyhound`, an ordinary American word.
for w in BRIT:
    if re.search(rf"\b{w}(?:s|d|ed|ing)?\b", body, re.I):
        hits.append(w)
print(" | ".join(hits[:6]))
')

[ -z "$REPORT" ] && exit 0

cat >&2 <<TAIL
BLOCKED: house style ($REPORT).

CLAUDE.md, project-wide and for everything - generated content, prose, docs, specs, tests, comments
and code identifiers alike:

  - HYPHENS ONLY. No em-dash (U+2014), no en-dash (U+2013). Use " - ".
  - AMERICAN SPELLINGS. color, center, gray, honor, judgment, catalog, labeled, behavior, neighbor,
    analyze/organize/recognize, artifact, defense, license, practice, skeptic, story, while,
    traveled, modeled, program, meter, liter, mold, plow, curb, draft, aging, marvelous, jewelry,
    skillful. And "domain", never "demesne".

NOT flagged, deliberately: the GM's own writing (a SOURCE block, l7r.md, or a direct quotation of
either), and the files that must quote the rule to state it.

If this fired on a legitimate quotation of the GM, that is a bug in this hook worth fixing rather
than working around.

(scripts/house-style-hooks.sh; CLAUDE.md "Generation Behavior")
TAIL
exit 2
