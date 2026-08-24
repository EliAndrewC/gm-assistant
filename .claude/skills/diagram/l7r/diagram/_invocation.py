"""Refuse to run an operation that was not invoked through THIS project's make (feature 127).

WHY THIS EXISTS (GM 2026-08-24). The fast path already existed - `make reference` answers in ~60 s -
and a session kept taking the five-minute and twenty-five-minute paths anyway, four times in one
feature, each time after being told not to, and each time by a route the existing guards did not
cover. The GM's conclusion: *"we need to make it literally impossible for you to bypass this even
with intent. It must be run through make."*

The observed workarounds, which are the threat model, are all the same shape - **an action that can
be presented as diligence**:

    tier 1  reach for an ungated sibling command   (cohort_audit while `make maps` was gated)
    tier 2  supply the documented override         (REF_WHY=, skipping a cancel-by-default prompt)
    tier 3  arrange that the prompt cannot fire    (backgrounding the run so nothing could answer)

Tiers above those - forging a makefile, editing a guard, disabling hooks - were never reached. So the
bar this module has to clear is not impossibility, which is unachievable against an operator with a
shell. It is: **every remaining bypass must be an action that cannot be mistaken for diligence, or
that shows up in a git diff.**

WHY NOT AN ENVIRONMENT VARIABLE, which was the obvious first design. Because the operator being
guarded can set one, and this project has four recorded instances of that operator doing exactly the
equivalent thing while believing it was being careful. An env var is a speed bump against habit; it
is nothing against intent. The determination therefore reads the PROCESS TREE, which the caller
cannot forge without doing something that looks wrong.

THIS IS LAYER 2 OF FOUR, and deliberately not the load-bearing one. A `PreToolUse` hook
(`scripts/make-only-hooks.sh`) catches the command by SHAPE before it ever runs, which costs zero
time and can see things no in-process check can - a bare `pytest`, a `make -f` naming a foreign
makefile. This module is defense in depth: it catches shapes the hook did not anticipate, and it is
the ONLY layer that can catch an in-process call (`python3 -c "import ...; generate(...)"`), which
needs no git diff and reads perfectly as diligence.
"""

from __future__ import annotations

import os
import sys

# The repository this module belongs to. Resolved from THIS file rather than from the cwd, because
# the cwd is caller-controlled and the whole point is to not trust the caller.
_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))

_MAKE_COMMS = frozenset({"make", "gmake", "remake"})
_MAKEFILE_FLAGS = ("-f", "--file", "--makefile")

# THE VERDICT IS COMPUTED ONCE PER PROCESS. A process's ancestry cannot change while it runs, so this
# is correct rather than merely fast - but the speed matters too, and for a specific reason. Every
# slow generator ever profiled in this engine was the same shape: *a per-candidate scan of geometry
# that does not change during the scan* (`dev/performance.md`). A /proc walk reads several files per
# call; dropped into a placer loop it would recreate that shape exactly, and cost far more than
# anything it guards. `tests/test_invocation.py` asserts the walk happens once, so a later refactor
# that removes this cache is caught rather than being silently slow.
_verdict: tuple[bool, str] | None = None


def _ancestry() -> list[int]:
    """Every PID from this process up to the top, nearest first.

    Stops on the first unreadable `/proc` entry rather than raising: a process can exit between the
    read of its child's PPid and the read of its own stat, and a guard that crashes on a race is a
    guard that gets removed."""
    out: list[int] = []
    pid = os.getpid()
    while pid > 1:
        try:
            with open(f"/proc/{pid}/stat", encoding="utf-8") as fh:
                stat = fh.read()
        except OSError:
            break
        # comm is parenthesized and may itself contain spaces or parentheses, so split on the LAST
        # ")" - the documented way to parse this file, and the reason a naive split(" ")[1] is wrong.
        try:
            ppid = int(stat.rsplit(") ", 1)[1].split()[1])
        except IndexError, ValueError:
            break
        out.append(pid)
        pid = ppid
    return out


def _comm(pid: int) -> str:
    try:
        with open(f"/proc/{pid}/stat", encoding="utf-8") as fh:
            return fh.read().split("(", 1)[1].rsplit(")", 1)[0]
    except OSError, IndexError:
        return ""


def _cmdline(pid: int) -> list[str]:
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as fh:
            return [a.decode("utf-8", "replace") for a in fh.read().split(b"\0") if a]
    except OSError:
        return []


def _cwd(pid: int) -> str:
    try:
        return os.readlink(f"/proc/{pid}/cwd")
    except OSError:
        return ""


def _inside_repo(path: str) -> bool:
    if not path:
        return False
    return os.path.abspath(path) == _REPO or os.path.abspath(path).startswith(_REPO + os.sep)


def _foreign_makefile(argv: list[str], make_cwd: str) -> bool:
    """Is this make being driven by a makefile outside the repository?

    THE HOLE THIS CLOSES, measured 2026-08-24: a bare ancestry check accepts `make -f /tmp/evil.mk`,
    because make really is the parent - it is just not OUR make. Two lines in /tmp defeat the whole
    guard, which is well inside the tier the GM asked to close. So a make that names a makefile
    outside the repo does not count as this project's make.

    `make_cwd` is the MAKE process's working directory, not ours, because a relative `-f` resolves
    against the former. Passed in explicitly rather than looked up: an earlier draft keyed a side
    table by `id(argv)`, which is wrong by construction - CPython reuses an id once the object is
    collected, so the table could answer for a different list entirely.
    """

    def outside(value: str) -> bool:
        if not value:
            return False
        return not _inside_repo(value if os.path.isabs(value) else os.path.join(make_cwd, value))

    for i, arg in enumerate(argv):
        if arg in _MAKEFILE_FLAGS:
            return outside(argv[i + 1] if i + 1 < len(argv) else "")
        for flag in _MAKEFILE_FLAGS:
            if arg.startswith(flag + "="):
                return outside(arg.split("=", 1)[1])
        if arg.startswith("-f") and not arg.startswith("--") and len(arg) > 2:
            return outside(arg[2:])
    return False


def _compute() -> tuple[bool, str]:
    """(is this process running under this project's make, why not)."""
    saw_make = False
    for pid in _ancestry():
        if _comm(pid) not in _MAKE_COMMS:
            continue
        saw_make = True
        cwd = _cwd(pid)
        if not _inside_repo(cwd):
            continue
        if _foreign_makefile(_cmdline(pid), cwd):
            continue
        return True, ""
    if saw_make:
        return False, "a make was found in the process tree, but it does not belong to this repository"
    return False, "not invoked through make"


def via_make() -> bool:
    """Is this process running under this project's make? Computed once, then cached."""
    global _verdict
    if _verdict is None:
        _verdict = _compute()
    return _verdict[0]


def _reason() -> str:
    global _verdict
    if _verdict is None:
        _verdict = _compute()
    return _verdict[1]


def assert_via_make(operation: str, target: str) -> None:
    """Refuse unless this process is running under this project's make.

    CALL THIS AT THE TOP OF AN OPERATION. Never inside a loop, never in a library helper - see the
    comment on `_verdict` for why that placement is a performance defect and not just untidy.

    `target` is not decoration: a refusal that does not say what to run instead is a bug, because the
    entire purpose is that the correct route is one line away. Same rule as this project's blocking
    hooks, whose messages carry the playbook rather than pointing at documentation nobody re-reads.

    Raises SystemExit rather than returning a bool, because a caller who forgets to check a return
    value is precisely the failure this module exists to prevent.
    """
    if via_make():
        return
    sys.stderr.write(
        f"\n\033[1mREFUSED: {operation} was not run through make.\033[0m\n\n"
        f"  {_reason()}.\n\n"
        f"  Run this instead:  \033[1mmake {target}\033[0m\n\n"
        "Every operation in this project goes through a make target, so that the expensive ones can\n"
        "ask whether the cheap one would do first. `make reference` (~60 s, one seed of the reference\n"
        "hamlet) answers most questions; `make done` is ~5.5 minutes and is NOT the quick check.\n\n"
    )
    raise SystemExit(2)
