#!/usr/bin/env python3
"""Fail when a Python module defines the same TOP-LEVEL function or class twice.

WHY (GM 2026-07-24): a cross-session merge left test_settlement.py with two `_city()` helpers -
each session's own gate was green (each tree had one), the auto-merge kept both, and the later
definition silently SHADOWED the earlier, breaking a seeded-roll test in a way that looked like
an engine bug. Ruff's F811 cannot catch this class: pyflakes only flags a redefinition when the
first binding was never used, and a helper defined early in a test module is always used by the
tests between the two definitions. So this checker AST-walks every module's top level and flags
any name bound twice by a plain `def` / `async def` / `class`.

Deliberately NOT flagged (legitimate redefinition patterns):
- defs nested inside module-level `if` / `try` blocks (conditional/platform definitions) - only
  statements directly in the module body are examined;
- `@overload`-decorated stubs (the typing pattern is N stubs + one implementation).

Scanned: webapp/ and .claude/skills/ under the given root (including the pool gen scripts - a
duplicate inside one gen is the same latent bug). Paths are filtered RELATIVE to the scan root,
so the checker works identically from main or from inside a session clone (the first draft put
".clones" in an absolute-parts skip set and silently scanned NOTHING when run inside a clone -
a false green; hence the scanned-files floor and the --selftest below).

Run `--selftest` first (sync-with-main.sh does): it plants a duplicate in a temp tree and
verifies the checker fires, then verifies a clean tree passes - a checker that cannot prove it
still bites is exactly the failure mode that motivated it. A run that scans ZERO files also
fails loudly (wrong root beats silent success).

Invoked by: the diagram Makefile `lint` target, and scripts/sync-with-main.sh before EVERY push -
the push guard is the point: the motivating duplicate arrived via a merge, where no gate
necessarily runs (docs-only pushes skip gates by policy).
"""

from __future__ import annotations

import ast
import sys
import tempfile
from pathlib import Path

SCAN_ROOTS = ("webapp", ".claude/skills")
SKIP_PARTS = {"__pycache__", ".git", "node_modules"}


def duplicate_defs(path: Path) -> list[tuple[str, int, int]]:
    """(name, first_lineno, dup_lineno) for every top-level name bound twice in this module."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    seen: dict[str, int] = {}
    out: list[tuple[str, int, int]] = []
    for node in (
        tree.body
    ):  # module top level ONLY: if/try-nested defs are conditional by design
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if any("overload" in ast.unparse(dec) for dec in node.decorator_list):
            continue
        if node.name in seen:
            out.append((node.name, seen[node.name], node.lineno))
        else:
            seen[node.name] = node.lineno
    return out


def run(root: str = ".", scan_roots: tuple[str, ...] = SCAN_ROOTS) -> tuple[int, int]:
    """(problem_count, scanned_file_count) over every .py under root's scan dirs."""
    bad = 0
    scanned = 0
    for scan in scan_roots:
        base = Path(root) / scan
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.py")):
            if SKIP_PARTS.intersection(
                p.relative_to(base).parts
            ):  # RELATIVE parts - see docstring
                continue
            scanned += 1
            try:
                found = duplicate_defs(p)
            except (
                SyntaxError
            ) as exc:  # a truncated merge artifact is exactly worth failing on
                print(f"{p}: unparseable ({exc})")
                bad += 1
                continue
            for name, first, dup in found:
                print(
                    f"{p}:{dup}: duplicate top-level def '{name}' (first defined at line {first}) - the later definition silently shadows the earlier one"
                )
                bad += 1
    return bad, scanned


def selftest() -> int:
    """Prove the checker bites: a planted duplicate must fire; a clean tree must pass."""
    with tempfile.TemporaryDirectory() as td:
        pkg = Path(td) / "webapp"
        pkg.mkdir()
        (pkg / "dup.py").write_text(
            "def f():\n    return 1\n\n\ndef g():\n    return f()\n\n\ndef f():\n    return 2\n"
        )
        (pkg / "clean.py").write_text(
            "def a():\n    return 1\n\n\nclass B:\n    def a(self):  # a method may share a module-level name\n        return 2\n"
        )
        bad, scanned = run(td)
        if bad != 1 or scanned != 2:
            print(
                f"check-duplicate-defs SELFTEST FAILED: expected exactly 1 problem over 2 files, got {bad} over {scanned}",
                file=sys.stderr,
            )
            return 1
    print(
        "check-duplicate-defs: selftest ok (planted duplicate fires, clean module passes)"
    )
    return 0


def main(argv: list[str]) -> int:
    if argv and argv[0] == "--selftest":
        return selftest()
    root = argv[0] if argv else "."
    bad, scanned = run(root)
    if scanned == 0:
        print(
            f"check-duplicate-defs: scanned ZERO files under {root!r} - wrong root? failing loudly (the first draft passed by scanning nothing)",
            file=sys.stderr,
        )
        return 1
    if bad:
        print(
            f"check-duplicate-defs: {bad} problem(s) over {scanned} files - a shadowed helper breaks whoever still calls the old one",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
