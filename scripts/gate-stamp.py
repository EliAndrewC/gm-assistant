#!/usr/bin/env python3
"""Prove that a green gate ran against exactly the Python being pushed.

WHY THIS EXISTS. Constitution Principle XIII says work is not done while a known regression exists
and nothing merges carrying one, and its enforcement clause says the stop-work ritual "does not run
to completion on a red or regressed state". That sentence was ASPIRATIONAL: `sync-with-main.sh`
refuses a dirty tree and screens for duplicate defs, but it never knew whether a gate had run at
all, let alone whether it passed. Compliance was a session choosing to comply - which is the exact
"someone has to remember" shape the principle was written to abolish (GM, 2026-08-17).

WHAT IT ACTUALLY PROVES, stated honestly because a guard that overclaims is worse than none: that
`make done` COMPLETED GREEN in an area while that area's Python was byte-for-byte what is now being
pushed. It does not prove the cohort was run (that is a separate, minutes-long sweep - see
`hamletgen.baseline_verdict` for the pin that guards it), and it cannot prove you ran the RIGHT
gate for a change spanning areas. It closes the common case: pushing Python no gate has seen.

WHY PYTHON ONLY, and why per-area. CLAUDE.md's "docs-only diffs skip the gate" is a real rule, so
hashing everything would block a legitimate markdown edit made after a green gate - and then the
first thing anyone learned would be how to bypass the guard. Per-area, because the repo has two
independent gates (the diagram skill and the webapp); a repo-wide hash would let a webapp change be
blocked by a gate that never covers it, and vice versa.

Areas with no gate of their own (specs/, scripts/) are deliberately NOT gated: inventing a
requirement nobody can satisfy is how a guard gets disabled.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

# area name -> repo-relative root. Each must have a Makefile whose `done` target stamps it.
AREAS = {"diagram": ".claude/skills/diagram", "webapp": "webapp"}


def _git(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


def _root() -> Path | None:
    try:
        return Path(_git("rev-parse", "--show-toplevel").strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None  # not a git checkout: the guard is a no-op rather than an obstacle


def _py_files(root: Path, area_path: str) -> list[Path]:
    """Tracked AND untracked-but-not-ignored .py under `area_path` - a new module nobody has added
    yet is still Python the gate ran on, and omitting it would let an untracked file slip past."""
    out = _git("ls-files", "-co", "--exclude-standard", "--", f"{area_path}/*.py", cwd=root)
    return sorted({root / line for line in out.splitlines() if line.strip()})


def hash_files(files: list[Path]) -> str:
    """Content hash of `files`, order-independent (each path is hashed with its own bytes)."""
    h = hashlib.sha256()
    for path in sorted(files):
        h.update(str(path).encode())
        h.update(b"\0")
        h.update(path.read_bytes() if path.is_file() else b"<missing>")
        h.update(b"\0")
    return h.hexdigest()


def _stamp_path(root: Path, area: str) -> Path:
    return root / ".git" / f"gate-green-{area}"


def write_stamp(area: str) -> int:
    root = _root()
    if root is None:
        return 0
    _stamp_path(root, area).write_text(hash_files(_py_files(root, AREAS[area])))
    return 0


def check(base: str) -> int:
    """Refuse areas whose Python changed since `base` without a matching green stamp."""
    root = _root()
    if root is None:
        return 0
    changed = _git("diff", "--name-only", f"{base}...HEAD", cwd=root).splitlines()
    bad: list[str] = []
    for area, area_path in AREAS.items():
        if not any(c.startswith(area_path + "/") and c.endswith(".py") for c in changed):
            continue
        stamp = _stamp_path(root, area)
        want = hash_files(_py_files(root, area_path))
        if not stamp.is_file():
            bad.append(f"{area}: no green gate has been recorded at all")
        elif stamp.read_text().strip() != want:
            bad.append(f"{area}: the last green gate ran against DIFFERENT Python than you are pushing")
    if not bad:
        return 0
    print("gate-stamp: refusing to push Python that no green gate has seen (constitution Principle XIII):", file=sys.stderr)
    for line in bad:
        print(f"  {line}", file=sys.stderr)
    print("gate-stamp: run `make done` in that area and push again - it stamps on success.", file=sys.stderr)
    print("gate-stamp: a cohort/sweep regression is NOT covered here; check it separately.", file=sys.stderr)
    print("gate-stamp: escape hatch, with a reason: GATE_STAMP_OK='<why this push is safe>'", file=sys.stderr)
    return 1


def selftest() -> int:
    """Prove the hash still BITES - a checker never seen failing is not a checker.

    (Same discipline as `check-duplicate-defs.py --selftest`, which `push_cmd` runs first for
    exactly this reason.)"""
    with tempfile.TemporaryDirectory() as tmp:
        a, b = Path(tmp) / "a.py", Path(tmp) / "b.py"
        a.write_text("x = 1\n")
        b.write_text("y = 2\n")
        before = hash_files([a, b])
        if hash_files([b, a]) != before:
            print("gate-stamp selftest: hash is order-dependent", file=sys.stderr)
            return 1
        a.write_text("x = 2\n")
        if hash_files([a, b]) == before:
            print("gate-stamp selftest: a changed .py did NOT change the hash", file=sys.stderr)
            return 1
        a.unlink()
        if hash_files([a, b]) == before:
            print("gate-stamp selftest: a deleted .py did NOT change the hash", file=sys.stderr)
            return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", choices=sorted(AREAS), help="record a green gate for this area")
    ap.add_argument("--check", metavar="BASE", help="refuse changed-Python areas with no matching stamp (BASE is usually origin/main)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    if args.write:
        return write_stamp(args.write)
    if args.check:
        return check(args.check)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
