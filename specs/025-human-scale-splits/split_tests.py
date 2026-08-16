#!/usr/bin/env python3
"""Test-file splitter for feature 025 (US2: test_checks.py, US4: test_settlement.py).

One-shot migration tooling. Splits a flat pytest module into a package directory:

- module docstring        -> <pkg>/__init__.py (with the stale direct-run line updated)
- shared builders/assigns -> <pkg>/_builders.py (verbatim, original order)
- each test_* function    -> the module named by the assignment map (verbatim body)
- import lines            -> synthesized per module from actual name usage
- `if __name__` block     -> DROPPED (runner convenience superseded by pytest; recorded in
                             research.md R13)

Slicing is CONTIGUOUS: every top-level node owns the source lines from the previous node's end
to its own end, so inter-node comments (section banners) travel with the node that follows them
and no line of the original is silently lost. `Path(__file__).parent` is rewritten to
`.parent.parent` (the package is one level deeper); the rewrite count is asserted.

    python3 split_tests.py test_checks   # uses test_checks_mapping.json, writes test_checks/
"""

from __future__ import annotations

import ast
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SKILL = os.path.join(REPO, ".claude", "skills", "diagram")

STDLIB = ("json", "math", "os", "pathlib", "random", "re", "sys", "tempfile")
FIRSTPARTY = ("check_village", "settlement", "waterfields", "hamletgen")


def dest_module(pkg: str, src_mod: str) -> str:
    """check_village source file -> test module name (US2 naming; US4 passes settlement names)."""
    if src_mod in ("CROSS", "driver.py", "__main__.py"):
        return "test_driver_and_fixtures.py"
    stem = src_mod[: -len(".py")]
    if stem.startswith("common_"):
        return "test_common_" + stem.split("_", 2)[2] + ".py"
    return "test_" + stem.lstrip("_") + ".py"


def used_names(nodes: list[ast.AST]) -> set[str]:
    names: set[str] = set()
    for node in nodes:
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name):
                names.add(sub.id)
    return names


def synth_imports(names: set[str], builder_names: set[str], pkg: str) -> str:
    lines = [f"import {m}" for m in STDLIB if m in names]
    block = "\n".join(lines)
    if "pytest" in names:
        block += ("\n\n" if block else "") + "import pytest"
    fp = [f"import {m}" for m in FIRSTPARTY if m in names]
    wanted = sorted(names & builder_names)
    if wanted:
        fp.append(f"from {pkg}._builders import {', '.join(wanted)}")
    if fp:
        block += ("\n\n" if block else "") + "\n".join(fp)
    return block


def main(stem: str) -> int:
    pkg_dir = os.path.join(SKILL, stem)
    src_path = os.path.join(SKILL, stem + ".py")
    with open(src_path) as fh:
        src = fh.read()
    lines = src.splitlines(keepends=True)
    with open(os.path.join(HERE, f"{stem}_mapping.json")) as fh:
        assign: dict[str, str] = json.load(fh)["assign"]
    tree = ast.parse(src)

    # contiguous slices: node i owns (prev end, own end]
    slices: list[tuple[ast.stmt, str]] = []
    prev_end = 0
    for node in tree.body:
        seg = "".join(lines[prev_end : node.end_lineno])
        prev_end = node.end_lineno
        slices.append((node, seg))
    tail = "".join(lines[prev_end:])  # trailing comments after the last node
    assert not tail.strip(), f"unrouted trailing content: {tail[:200]!r}"

    routed: dict[str, list[tuple[ast.stmt, str]]] = {}
    builder_defs: set[str] = set()
    init_doc = ""
    dropped_main = 0
    for node, seg in slices:
        if isinstance(node, ast.Expr) and node is tree.body[0]:
            init_doc = seg
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            assert not seg.strip().startswith("#"), f"comment glued to import would be lost: {seg!r}"
            continue
        if isinstance(node, ast.If) and getattr(getattr(node.test, "left", None), "id", "") == "__name__":
            dropped_main += 1
            continue
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            mod = dest_module(stem, assign[node.name])
        else:
            mod = "_builders.py"
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                builder_defs.add(node.name)
            elif isinstance(node, ast.Assign):
                builder_defs.update(t.id for t in node.targets if isinstance(t, ast.Name))
        routed.setdefault(mod, []).append((node, seg))

    os.makedirs(pkg_dir, exist_ok=True)
    fixed_doc = init_doc.replace(f"python3 -m pytest {stem}.py", f"python3 -m pytest {stem}/").replace(f"python3 {stem}.py", f"python3 -m pytest {stem}/")
    with open(os.path.join(pkg_dir, "__init__.py"), "w") as fh:
        fh.write(fixed_doc)

    parent_rewrites = 0
    for mod, entries in sorted(routed.items()):
        nodes = [n for n, _ in entries]
        body = "".join(seg for _, seg in entries)
        n = body.count("pathlib.Path(__file__).parent")
        if n:
            body = body.replace("pathlib.Path(__file__).parent", "pathlib.Path(__file__).parent.parent")
            parent_rewrites += n
        names = used_names(nodes)
        header = f'"""Split from {stem}.py by feature 025 - see {stem}/CLAUDE.md for the index."""\n\n'
        imports = synth_imports(names, builder_defs if mod != "_builders.py" else set(), stem)
        with open(os.path.join(pkg_dir, mod), "w") as fh:
            fh.write(header + imports + "\n\n" + body.lstrip("\n"))
    print(f"wrote {len(routed)} modules + __init__ to {pkg_dir}; dropped __main__ blocks: {dropped_main}; __file__ rewrites: {parent_rewrites}")
    os.remove(src_path)
    print(f"removed {src_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
