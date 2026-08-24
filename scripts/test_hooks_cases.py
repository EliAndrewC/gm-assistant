#!/usr/bin/env python3
"""Case tables for the three guards added by the 2026-08-24 enforcement audit.

WHY ONE FILE FOR THREE HOOKS. The older suites are each a bash script of `check` lines, which suits a
hook whose input is a single command string. These three take structured tool payloads - file paths,
edit anchors, whole file contents - and expressing those in bash quoting was the larger half of the
work with none of the value. The `test-<name>-hooks.sh` companions still exist and still run, because
that convention is what `make hooks-test` and the companion guard look for; they delegate here.

TWO DIRECTIONS FOR EVERY GUARD. Each table carries the cases it must FIRE on and the cases it must
stay QUIET on, and the quiet half is deliberately the longer one. Every false positive this project
has paid for is in these tables as a regression case - a commit message that quoted a blocked
command, a grep that named a path, a docstring, a fixture argument, a hook whose matcher blocked its
own repair. The shared lesson has a name now: **a mention is not an invocation.**
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent


def cmd(c: str) -> str:
    return json.dumps({"tool_name": "Bash", "tool_input": {"command": c}})


def edit(path: str, old: str = "", new: str = "") -> str:
    return json.dumps({"tool_name": "Edit", "tool_input": {"file_path": path, "old_string": old, "new_string": new}})


def write(path: str, content: str) -> str:
    return json.dumps({"tool_name": "Write", "tool_input": {"file_path": path, "content": content}})


REPO_SAFETY = [
    # (label, payload, expected)
    ("force push, long flag", cmd("git push --force origin main"), "blocked"),
    ("force push, short flag", cmd("git push -f"), "blocked"),
    ("force push, with-lease", cmd("git push --force-with-lease origin HEAD:main"), "blocked"),
    ("flag before the verb", cmd("git --force push origin main"), "blocked"),
    ("an ordinary push", cmd("git -C /gm-assistant/.clones/x push origin HEAD:main"), "ok"),
    ("the stop-work ritual", cmd("./scripts/sync-with-main.sh done"), "ok"),
    # the seventh mention-versus-invocation case: a message ABOUT the rule
    ("a commit message quoting the rule", cmd('git commit -m "never git push --force here"'), "ok"),
    ("a heredoc message quoting it", cmd("git commit -F - <<MSG\nblocks git push --force\nMSG"), "ok"),
    ("git write to the GM repo", cmd("git -C /host-l7r-repo commit -m x"), "blocked"),
    ("git add to the GM repo", cmd("cd /host-l7r-repo && git add setting/l7r.md"), "blocked"),
    # read-only git there is explicitly ALLOWED by CLAUDE.md
    ("git log on the GM repo", cmd("git -C /host-l7r-repo log --oneline -5"), "ok"),
    ("git diff on the GM repo", cmd("git -C /host-l7r-repo diff"), "ok"),
    ("the documented escape", cmd("git -C /host-l7r-repo status  # HOST_GIT_OK: read-only"), "ok"),
]

HOUSE_STYLE = [
    ("a British spelling in a spec", edit("/r/specs/x/spec.md", new="the licence is granted"), "blocked"),
    ("another, in prose", edit("/r/docs/a.md", new="the centre of the map"), "blocked"),
    ("demesne", edit("/r/docs/a.md", new="the lord's demesne"), "blocked"),
    ("an em-dash", edit("/r/docs/a.md", new="a dash — here"), "blocked"),
    ("an en-dash", edit("/r/docs/a.md", new="a range 1–2"), "blocked"),
    ("American spellings", edit("/r/docs/a.md", new="the center is gray, the color honors judgment"), "ok"),
    # the files that must QUOTE the forbidden words in order to state the rule
    ("CLAUDE.md stating the rule", edit("/r/CLAUDE.md", new="never write colour or centre"), "ok"),
    ("the constitution stating it", edit("/gm/.specify/memory/constitution.md", new="forbid licence"), "ok"),
    # the GM's own writing is theirs
    ("the GM's canonical file", edit("/host-l7r-repo/setting/l7r.md", new="the colour of the sky"), "ok"),
    ("a SOURCE block in our file", edit("/r/docs/a.md", new="<!-- SOURCE: GM NOTES - DO NOT MODIFY -->the colour<!-- END SOURCE -->"), "ok"),
]


def source_block_cases(tmp: pathlib.Path) -> list[tuple[str, str, str]]:
    doc = tmp / "doc.md"
    doc.write_text(
        "intro\n<!-- SOURCE: GM NOTES - DO NOT MODIFY -->\n"
        "The colour of the sky was grey.\n<!-- END SOURCE -->\nours: the color is gray.\n",
        encoding="utf-8",
    )
    keep = (
        "intro\n<!-- SOURCE: GM NOTES - DO NOT MODIFY -->\n"
        "The colour of the sky was grey.\n<!-- END SOURCE -->\nnew tail\n"
    )
    return [
        # the exact interaction that makes this guard necessary: house style WANTS to fix these
        ("editing the GM's words", edit(str(doc), "The colour of the sky was grey.", "The color was gray."), "blocked"),
        ("a Write that drops the block", write(str(doc), "intro\nrewritten\n"), "blocked"),
        ("editing OUR text in the same file", edit(str(doc), "ours: the color is gray.", "ours: the color is slate."), "ok"),
        ("a Write that preserves it verbatim", write(str(doc), keep), "ok"),
        ("the documented escape", edit(str(doc), "The colour of the sky was grey.", "SOURCE_EDIT_OK - the GM asked"), "ok"),
        ("a file with no SOURCE block", edit(str(tmp / "none.md"), "x", "y"), "ok"),
    ]


def run(hook: str, cases: list[tuple[str, str, str]]) -> int:
    script = HERE / f"{hook}-hooks.sh"
    bad = 0
    print(f"{hook}-hooks.sh")
    for label, payload, want in cases:
        proc = subprocess.run([str(script), "pretool"], input=payload, capture_output=True, text=True, check=False)
        got = "blocked" if proc.returncode else "ok"
        ok = got == want
        bad += 0 if ok else 1
        print(f"  {'ok    ' if ok else 'FAIL  '} {label}" + ("" if ok else f"  (expected {want}, got {got})"))
    print(f"  {len(cases) - bad} passed, {bad} failed\n")
    return bad


def main() -> int:
    which = sys.argv[1] if len(sys.argv) > 1 else ""
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        (tmp / "none.md").write_text("no blocks here\n", encoding="utf-8")
        tables = {
            "repo-safety": REPO_SAFETY,
            "house-style": HOUSE_STYLE,
            "source-block": source_block_cases(tmp),
        }
        if which not in tables:
            print(f"usage: {sys.argv[0]} <{'|'.join(tables)}>")
            return 2
        return 1 if run(which, tables[which]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
