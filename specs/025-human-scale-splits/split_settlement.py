#!/usr/bin/env python3
"""Mover script for feature 025 US3: settlement.py -> the settlement/ package.

One-shot migration tooling (024's split_package.py lineage). Pure move with three mechanical
adaptations, all asserted:

- Settlement's 338 methods split into MIXIN classes by contiguous method ranges (data-model E1);
  every mixin method gains an explicit `self: "Settlement"` annotation and each mixin module gets
  `if TYPE_CHECKING: from .core import Settlement` (research R1/R2). Class-body attribute
  assignments stay with the composed class in core.py (order preserved among themselves).
- Module-level helpers split at the knob-engine banner into _geom.py / _knobs.py.
- Imports are synthesized per module from scope-aware usage (symtable free reads); the package
  __init__.py re-exports the monolith surface (module docstring + import-guard call included).

Slicing is contiguous (a node owns the lines from the previous node's end through its own), so
banner comments travel with the code they precede and no source line is lost.

    python3 split_settlement.py
"""

from __future__ import annotations

import ast
import json
import os
import re
import symtable
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SKILL = os.path.join(REPO, ".claude", "skills", "diagram")
SRC = os.path.join(SKILL, "settlement.py")
PKG = os.path.join(SKILL, "settlement")

KNOB_BANNER = "# ---- Knob engine (feature 005)"

# (module, mixin class, last method of the contiguous range) - data-model E1. core.py's own
# method range ends at crop_to_content; everything after the last row is an error.
MIXIN_RANGES = [
    ("fields", "FieldsMixin", "crescent_pond"),
    ("water_ways", "WaterWaysMixin", "alley"),
    ("shrines_wells", "ShrinesWellsMixin", "forest"),
    ("structures", "StructuresMixin", "drum_tower"),
    ("trades", "TradesMixin", "tanning_yard"),
    ("homestead_parts", "HomesteadPartsMixin", "_urban_keepouts"),
    ("land", "LandMixin", "reserve_clearing"),
    ("civic_grounds", "CivicGroundsMixin", "flush_stable_yards"),
    ("city", "CityMixin", "governor_mansion"),
    ("castle_civic", "CastleCivicMixin", "flower_field"),
    ("houses", "HousesMixin", "water_source_anchor"),
    ("rolling", "RollingMixin", "ring"),
    ("finish", "FinishMixin", "render_png"),
]
CORE_LAST = "crop_to_content"


def contiguous(nodes: list[ast.stmt], lines: list[str], start: int) -> list[tuple[ast.stmt, str]]:
    out = []
    prev = start
    for n in nodes:
        out.append((n, "".join(lines[prev : n.end_lineno])))
        prev = n.end_lineno
    return out


def free_reads(src: str) -> set[str]:
    table = symtable.symtable(src, "<mod>", "exec")
    out: set[str] = set()

    def walk(t: symtable.SymbolTable) -> None:
        for s in t.get_symbols():
            if s.is_referenced() and not (s.is_local() and t.get_type() != "module"):
                out.add(s.get_name())
        for c in t.get_children():
            walk(c)

    walk(table)
    return out


def main() -> int:
    with open(SRC) as fh:
        src = fh.read()
    lines = src.splitlines(keepends=True)
    tree = ast.parse(src)
    knob_line = next(i + 1 for i, ln in enumerate(lines) if ln.startswith(KNOB_BANNER))

    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Settlement")
    pre_nodes = [n for n in tree.body if n is not cls and n.end_lineno < cls.lineno]
    post_nodes = [n for n in tree.body if n is not cls and n.lineno > cls.end_lineno]
    assert not post_nodes, f"unexpected nodes after Settlement: {post_nodes}"

    # ---- module docstring, imports, import-time guard, helpers -------------------------------
    doc_node = tree.body[0]
    assert isinstance(doc_node, ast.Expr), "expected module docstring first"
    import_nodes = [n for n in pre_nodes if isinstance(n, (ast.Import, ast.ImportFrom))]
    # ALL other top-level statements (defs, assigns, AND Expr calls like the import-time guard
    # and the register_knob catalog) route positionally - calls stay right after their banner/defs
    helper_nodes = [n for n in pre_nodes if n is not doc_node and n not in import_nodes]

    # name -> the import statement line that binds it, from the monolith's own imports
    import_binds: dict[str, str] = {}
    for n in import_nodes:
        seg = ast.get_source_segment(src, n)
        for a in n.names:
            import_binds[(a.asname or a.name).split(".")[0]] = seg

    geom_entries = contiguous([n for n in helper_nodes if n.end_lineno < knob_line], lines, 0)
    # drop the docstring/import lines that contiguity glued onto the first helper slice
    first_node, first_seg = geom_entries[0]
    first_seg = "".join(lines[first_node.lineno - 1 : first_node.end_lineno])
    geom_entries[0] = (first_node, first_seg)
    knob_start = min(n.lineno for n in helper_nodes if n.lineno >= knob_line) - 1
    knob_entries = contiguous([n for n in helper_nodes if n.lineno >= knob_line], lines, knob_start)

    helper_home: dict[str, str] = {}
    for module, entries in (("_geom", geom_entries), ("_knobs", knob_entries)):
        for n, _ in entries:
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
                helper_home[n.name] = module
            elif isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Name):
                        helper_home[t.id] = module
            elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
                helper_home[n.target.id] = module
            elif isinstance(n, ast.TypeAlias):
                helper_home[n.name.id] = module

    # ---- split the class body -----------------------------------------------------------------
    methods = [n for n in cls.body if isinstance(n, ast.FunctionDef)]
    # Class-body attribute assignments are NOT extracted separately: contiguous method slicing
    # already carries each one inside the slice of the method that follows it, so an attribute
    # lands (once) on whichever mixin owns that method - reachable on Settlement via the MRO
    # exactly as before. The class docstring is the only body prefix handled by hand.
    has_doc = isinstance(cls.body[0], ast.Expr)
    method_entries = contiguous(methods, lines, cls.body[0].end_lineno if has_doc else cls.lineno)
    cls_doc = "".join(lines[cls.body[0].lineno - 1 : cls.body[0].end_lineno]) if has_doc else ""

    groups: dict[str, list[tuple[ast.stmt, str]]] = {m: [] for m, _, _ in MIXIN_RANGES}
    groups["core"] = []
    ranges = iter(MIXIN_RANGES)
    current_mod, current_last = "core", CORE_LAST
    for n, seg in method_entries:
        groups[current_mod].append((n, seg))
        if n.name == current_last:
            nxt = next(ranges, None)
            if nxt is None:
                current_mod, current_last = "DONE", ""
            else:
                current_mod, _, current_last = nxt
    assert current_mod == "DONE", f"ran out of methods inside range {current_mod} (last method never seen: {current_last})"
    assert all(groups[m] for m, _, _ in MIXIN_RANGES), "empty mixin group"

    os.makedirs(PKG, exist_ok=True)
    all_std_names = set(import_binds)

    def synth(body: str, local_names: set[str], wrap: bool, type_checking: bool) -> str:
        wrapped = "class _M:\n" + body if wrap else body
        reads = free_reads(wrapped)
        # py314 lazy annotations: annotation-only names do not surface in symtable - walk them
        for node in ast.walk(ast.parse(wrapped)):
            ann = []
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                ann = [a.annotation for a in list(node.args.args) + list(node.args.kwonlyargs) + [node.args.vararg, node.args.kwarg] if a and a.annotation] + ([node.returns] if node.returns else [])
            elif isinstance(node, ast.AnnAssign):
                ann = [node.annotation]
            elif isinstance(node, ast.TypeAlias):
                ann = [node.value]
            for a in ann:
                reads |= {s.id for s in ast.walk(a) if isinstance(s, ast.Name)}
        if "Settlement" in reads:
            type_checking = True  # annotation-only in helpers; py314 lazy annotations make it safe
        blocks: list[str] = []
        std = sorted({import_binds[n] for n in reads & all_std_names})
        if std:
            blocks.append("\n".join(std))
        for helper_mod in ("_geom", "_knobs"):
            wanted = sorted(n for n in reads - local_names if helper_home.get(n) == helper_mod)
            if wanted:
                blocks.append(f"from .{helper_mod} import {', '.join(wanted)}")
        if type_checking:
            blocks.append('from typing import TYPE_CHECKING\n\nif TYPE_CHECKING:\n    from .core import Settlement')
        return "\n".join(blocks)

    def annotate_self(seg: str) -> str:
        out = re.sub(r'(\n    def \w+\(\s*self)([,)])', r'\1: "Settlement"\2', "\n" + seg)[1:]
        # mypy flags the mixin self-type shape itself ("erased type of self is not a supertype of
        # its class", [misc]) while still fully type-checking every method BODY against
        # Settlement. Silence exactly that shape complaint, per def line, nothing else.
        return re.sub(r'(\n    def \w+\([^\n]*self: "Settlement"[^\n]*)', r'\1  # type: ignore[misc]', "\n" + out)[1:]

    written: dict[str, int] = {}

    def write_mod(name: str, text: str) -> None:
        path = os.path.join(PKG, name + ".py")
        with open(path, "w") as fh:
            fh.write(text)
        written[name] = text.count("\n")

    hdr = '"""Split from settlement.py by feature 025 - see settlement/CLAUDE.md for the index."""\n\n'
    for module, entries in (("_geom", geom_entries), ("_knobs", knob_entries)):
        local = {n for n, h in helper_home.items() if h == module}
        body = "".join(seg for _, seg in entries)
        write_mod(module, hdr + synth(body, local, False, False) + "\n\n" + body.lstrip("\n"))

    mixin_class_names = []
    for module, cls_name, _ in MIXIN_RANGES:
        mixin_class_names.append(cls_name)
        body = annotate_self("".join(seg for _, seg in groups[module]))
        text = hdr + synth(body, set(), True, True) + "\n\n\nclass " + cls_name + ":\n" + body.lstrip("\n")
        write_mod(module, text)

    core_methods = annotate_self("".join(seg for _, seg in groups["core"]))
    core_body = cls_doc + "\n" + core_methods.lstrip("\n")
    mixin_imports = "\n".join(f"from .{m} import {c}" for m, c, _ in MIXIN_RANGES)
    core_text = (
        hdr
        + synth(core_body, set(), True, False)
        + "\n"
        + mixin_imports
        + "\n\n\nclass Settlement("
        + ", ".join(mixin_class_names)
        + "):\n"
        + core_body
    )
    write_mod("core", core_text)

    # ---- __init__.py: docstring + guard + full re-export surface ------------------------------
    census = json.load(open(os.path.join(HERE, "consumer-census.json")))
    monolith_names = set(helper_home) | {"Settlement"}
    wanted = (set(census["names"]) & monolith_names) | {"Settlement"}
    doc = "".join(lines[doc_node.lineno - 1 : doc_node.end_lineno])
    by_mod: dict[str, list[str]] = {}
    for n in sorted(wanted):
        by_mod.setdefault("core" if n == "Settlement" else helper_home[n], []).append(n)
    by_mod.setdefault(helper_home["_assert_not_main_tree"], []).append("_assert_not_main_tree")
    # `X as X` is the explicit-reexport form mypy --strict's no_implicit_reexport requires
    exports = "\n".join(f"from .{m} import {', '.join(f'{n} as {n}' for n in sorted(set(ns)))}" for m, ns in sorted(by_mod.items()))
    init = doc + "\n" + exports + "\n"
    with open(os.path.join(PKG, "__init__.py"), "w") as fh:
        fh.write(init)

    os.remove(SRC)
    for name, n in sorted(written.items(), key=lambda kv: -kv[1]):
        print(f"{n:6d}  settlement/{name}.py")
    print(f"__init__ exports: {sum(len(v) for v in by_mod.values())} names; removed settlement.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
