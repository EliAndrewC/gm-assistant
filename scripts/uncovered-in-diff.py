#!/usr/bin/env python3
"""Print the lines YOU changed that no test covers, with their source text.

WHY (GM 2026-07-25): a coverage failure reports a bare line number somewhere in a 5,700-line
module, so the gate run that finds it is followed by a hunt and then a SECOND full gate run to
confirm the fix. Measured cost in one profiled feature: two of six `make done` runs (~4 min) were
that cycle. Intersecting the coverage miss with `git diff` turns "line 1603 is uncovered" into
"this line, that you just wrote, has no test" - so the retry is a certain fix rather than a guess.

Run from a package dir that has a .coverage data file (the Makefiles call it automatically when the
coverage gate fails):

    python3 scripts/uncovered-in-diff.py [--base HEAD]

Silent (exit 0) when there is nothing to say: no coverage data, no diff, or every changed line is
covered. It is a diagnostic, never a gate - it must never turn a green run red.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys


def changed_lines(base: str) -> dict[str, set[int]]:
    """{absolute path -> set of line numbers} added or modified vs `base`, from git's own diff.

    -U0 gives exactly the touched ranges with no context, so an untouched neighbor never gets
    blamed. Both the worktree and the index are included (a session about to be told its coverage
    is short has usually not committed yet)."""
    try:
        root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip()
        out = subprocess.run(["git", "diff", "-U0", base, "--"], capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {}
    files: dict[str, set[int]] = {}
    cur = ""
    for line in out.splitlines():
        if line.startswith("+++ b/"):
            cur = os.path.join(root, line[6:])
        elif line.startswith("@@") and cur:
            m = re.match(r"@@ -\S+ \+(\d+)(?:,(\d+))? @@", line)
            if m:
                start, count = int(m.group(1)), int(m.group(2) or 1)
                files.setdefault(cur, set()).update(range(start, start + count))
    return files


def uncovered() -> dict[str, set[int]]:
    """{absolute path -> set of uncovered line numbers} from the .coverage data file in cwd."""
    try:
        # --fail-under=0 because this runs precisely WHEN coverage is short: the project config sets
        # fail_under=100, and `coverage json` honors it and exits non-zero, which would otherwise
        # look to us like "no coverage data" exactly when there is some. check=False for the same
        # reason - the report is written regardless of the exit status.
        subprocess.run([sys.executable, "-m", "coverage", "json", "-q", "--fail-under=0", "-o", "/tmp/.uncovered-in-diff.json"], capture_output=True, check=False)
        with open("/tmp/.uncovered-in-diff.json") as fh:
            data = json.load(fh)
    except Exception:
        return {}
    return {os.path.abspath(f): set(d.get("missing_lines", [])) for f, d in data.get("files", {}).items()}


def main() -> int:
    base = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else "HEAD"
    diff, miss = changed_lines(base), uncovered()
    if not diff or not miss:
        return 0
    hits = [(path, sorted(diff[path] & miss[path])) for path in sorted(diff) if path in miss and diff[path] & miss[path]]
    if not hits:
        return 0
    total = sum(len(v) for _, v in hits)
    print(f"\n\033[1muncovered lines you changed ({total}) - these are what the coverage gate is failing on:\033[0m")
    for path, lines in hits:
        try:
            src = open(path).read().splitlines()
        except OSError:  # pragma: no cover - a deleted file cannot be uncovered
            continue
        print(f"  {os.path.relpath(path)}")
        for n in lines:
            text = src[n - 1].strip() if n <= len(src) else ""
            print(f"    {n:>6}  {text[:110]}")
    print("  -> add a test that reaches each, or delete the line if it is unreachable\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
