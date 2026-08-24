#!/usr/bin/env python3
"""Decide whether a Bash command STARTS an operation that must go through make (feature 127).

WHY THIS IS A FILE AND NOT A `case` IN THE HOOK. The first version matched substrings anywhere in
the command text, and inside one hour it fired on three pieces of correct work:

  - `grep -n 'def stage_ways' l7r/diagram/hamletgen/ways.py`  - a READ, blocked for naming a path
  - a `git commit` whose MESSAGE quoted the patterns being matched
  - a test harness passing a blocked command as a STRING to check that it gets blocked

All three are the same defect: **a mention is not an invocation.** A guard that fires on correct work
is the one failure this feature cannot have, because it is exactly what teaches a session to reach
for the escape as a matter of routine - which is tier 2 of the threat model, the workaround that
actually happened three times.

So matching is anchored to COMMAND POSITIONS: the start of the input, or just after a `;`, `|`, `&&`,
`||` or newline, skipping any leading `timeout`, `env` or `VAR=value` prefixes. A quoted string, a
heredoc body and a commit message all fail that test by construction, and no list of exceptions has
to be maintained for them.
"""

from __future__ import annotations

import json
import re
import sys

# a command position: start of input or after a separator, then optional leading noise
_POS = r"(?:^|[\n;|]|&&|\|\|)\s*(?:timeout\s+\S+\s+|env\s+|[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*"
_PY = r"(?:\S*/)?python3?"

# a guard file, as the TARGET of a write - the filename adjacent to the operator that writes it
_GUARD = r"[\w./-]*(?:Makefile|[\w-]*-hooks\.sh|settings\.json)"
_GUARD_WRITE = (
    rf">>?\s*{_GUARD}(?:\s|$)",                    # cat > Makefile ; echo x >> scripts/a-hooks.sh
    rf"sed\s+-i\b[^;|&]*?{_GUARD}(?:\s|$)",        # sed -i 's/a/b/' scripts/a-hooks.sh
    rf"tee\s+(?:-a\s+)?{_GUARD}(?:\s|$)",          # tee Makefile
    rf"{_GUARD}[\"\']\s*\)?\s*\)?\s*\.write_text",  # Path("...Makefile").write_text(
)


def _strip_heredocs(cmd: str) -> str:
    """A heredoc body is the payload of a command, never a command. Removed before matching."""
    return re.sub(r"<<-?\s*['\"]?(\w+)['\"]?\n.*?\n\s*\1\b", " <<BODY ", cmd, flags=re.S)


def classify(cmd: str) -> str:
    if not cmd or "GUARD_EDIT_OK" in cmd:
        return "ok"
    raw = cmd
    c = _strip_heredocs(cmd)

    def at(pat: str) -> bool:
        return re.search(_POS + pat, c) is not None

    if at(r"make\s+(?:-\S+\s+)*(?:-f|--file|--makefile)(?:[=\s]|$)"):
        return "foreign-makefile"
    if at(rf"{_PY}\s+(?:-\S+\s+)*-m\s+l7r\.diagram\.") or at(rf"{_PY}\s+\S*l7r/diagram/(?:pipeline/regen|hamletgen/__main__)\.py"):
        return "engine-entry-point"
    if at(rf"(?:{_PY}\s+(?:-\S+\s+)*-m\s+)?pytest\b"):
        return "bare-pytest"
    # AN OVERRIDE COUNTS WHEREVER IT SITS ON THE COMMAND. `REF_WHY=x make done` puts it in front;
    # `make done FULL=1 REF_WHY=x` passes it as a make argument. Both skip the prompt, so both are
    # tier 2 - the first cut only matched the leading form and the suite caught it immediately.
    if re.search(r"\b(?:REF_WHY|REF_OK|GATE_OK)=", c) and (at(r"make\b") or re.search(_POS + r"(?:REF_WHY|REF_OK|GATE_OK)=", c)):
        return "inline-override"
    # GUARD-WRITE READS THE RAW COMMAND, NOT THE STRIPPED ONE, and this is the one place that is
    # right: everywhere else a heredoc body is prose to ignore, but here it is the payload that does
    # the writing - `python3 - <<PY ... write_text("...Makefile") ... PY` is exactly the route that
    # slipped past layer 3 all day.
    #
    # THE GUARD FILE MUST BE THE TARGET OF THE WRITE, not merely present somewhere. The first cut
    # asked "does a guard filename appear AND does a write appear", which blocked a command creating
    # an ordinary test file whose DOCSTRING mentioned a hook by name. Third time this feature has
    # made the mention-versus-invocation mistake - a grep, a commit message, and now a docstring -
    # which is worth stating plainly: proximity is the signal, presence never is.
    if any(re.search(pat, raw) for pat in _GUARD_WRITE):
        return "guard-write"
    return "ok"
    raw = cmd
    c = _strip_heredocs(cmd)

    def at(pat: str) -> bool:
        return re.search(_POS + pat, c) is not None

    if at(r"make\s+(?:-\S+\s+)*(?:-f|--file|--makefile)(?:[=\s]|$)"):
        return "foreign-makefile"
    if at(rf"{_PY}\s+(?:-\S+\s+)*-m\s+l7r\.diagram\.") or at(rf"{_PY}\s+\S*l7r/diagram/(?:pipeline/regen|hamletgen/__main__)\.py"):
        return "engine-entry-point"
    if at(rf"(?:{_PY}\s+(?:-\S+\s+)*-m\s+)?pytest\b"):
        return "bare-pytest"
    # AN OVERRIDE COUNTS WHEREVER IT SITS ON THE COMMAND. `REF_WHY=x make done` puts it in front;
    # `make done FULL=1 REF_WHY=x` passes it as a make argument. Both skip the prompt, so both are
    # tier 2 - the first cut only matched the leading form and the suite caught it immediately.
    if re.search(r"\b(?:REF_WHY|REF_OK|GATE_OK)=", c) and (at(r"make\b") or re.search(_POS + r"(?:REF_WHY|REF_OK|GATE_OK)=", c)):
        return "inline-override"
    # GUARD-WRITE READS THE RAW COMMAND, NOT THE STRIPPED ONE, and this is the one place where that
    # is right. Everywhere else a heredoc body is prose to be ignored; here it is the payload that
    # does the writing - `python3 - <<PY ... write_text("...Makefile") ... PY` is precisely the route
    # that slipped past layer 3 all day. Stripping it would reopen the hole that stripping was added
    # to close, in the same commit. The residual cost is that prose ABOUT writing a guard file can
    # trip this; GUARD_EDIT_OK covers it, and that is the cheaper error of the two.
    if re.search(r"(?:Makefile|-hooks\.sh|settings\.json)", raw) and re.search(r"(?:^|\s)>>?\s|sed\s+-i|write_text|(?:^|\s)tee\s", raw):
        return "guard-write"
    return "ok"


if __name__ == "__main__":
    try:
        payload = json.load(sys.stdin).get("tool_input", {}).get("command", "")
    except Exception:
        payload = ""
    print(classify(payload))
