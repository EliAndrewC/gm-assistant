#!/usr/bin/env python3
"""One-shot mover for feature 024 stage 2: check_village.py (37,346 lines post-stage-1) becomes
the check_village/ package. Everything moves VERBATIM by contiguous line ranges - concatenating
the generated files' body regions in file order reproduces the monolith's definition order
exactly - and only the import lines are regenerated, per module, from free-name analysis.

    python3 split_package.py            # writes check_village/, deletes check_village.py

Import generation is deliberately conservative: free names are approximated as (all Name loads
in a statement) minus (all names bound anywhere inside it), which can OVER-import (a shadowed
name) but never under-import silently - over-imports are then removed by `ruff check --fix`
(F401), and a genuine miss explodes as NameError in the very next oracle run. Cross-module
references must point BACKWARDS in file order (hard-failed otherwise), so the package cannot
have import cycles.

Retired the moment the transform lands (like 022/023's tools); the package is then the
hand-maintained truth.
"""

from __future__ import annotations

import ast
import builtins
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SKILL = f"{REPO}/.claude/skills/diagram"
MONO = f"{SKILL}/check_village.py"
PKG = f"{SKILL}/check_village"

# The common region (everything before the first _seg_) is a dependency MESH - contiguous cuts
# leave 9 forward-reference edges (GridIndex, footprint_on_line, point_in_poly, ...), so it is
# packed by SCC condensation in topological order instead: functions/classes move freely, every
# constant lands at or after its dependencies, and within a file statements keep source order
# (any subsequence of a valid execution order is valid once cross-file deps point backwards).
COMMON_TARGET_LINES = 800
COMMON_NAMES = [  # marquee member -> file theme (applied in pack order, first match wins)
    ("rect_corners", "geometry"),
    ("matrix_violations", "overlap_policy"),
    ("GridIndex", "spatial"),
    ("check_fire_features", "features"),
    ("city_capacity", "capacity"),
]

# contiguous segment-region cuts: (segment-name prefix that OPENS the file, module name, parts)
SEG_CUTS = [
    ("_seg_0000", "segments_01_city_frame_and_yards", 1),
    ("_seg_0097", "segments_02_capital_and_walls", 1),
    ("_seg_0133_031", "segments_03_structures_and_wards", 1),
    ("_seg_0268", "segments_04_homesteads", 1),
    ("_seg_0285_092", "segments_05_fields_and_funerary", 1),
    ("_seg_0334", "segments_06_ways_and_bridges", 1),
    ("_seg_0410", "segments_07_water", 1),
    ("_seg_0513", "segments_08_town_and_fire", 1),
    ("_seg_0555_000", "segments_09_justice_and_tanning", 1),
    ("_seg_0563_000", "segments_10_city_battery", 3),  # 377 segs / 5,943 lines -> _a/_b/_c
    ("_seg_0564", "segments_11_polders_and_edges", 1),
]

BUILTINS = set(dir(builtins)) | {"__file__", "__name__", "__doc__"}


def _bound(node: ast.AST) -> set[str]:
    out: set[str] = set()
    for n in ast.walk(node):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(n.name)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                a = n.args
                out |= {x.arg for x in a.args + a.posonlyargs + a.kwonlyargs}
                out |= {x.arg for x in (a.vararg, a.kwarg) if x}
        elif isinstance(n, ast.Lambda):
            a = n.args
            out |= {x.arg for x in a.args + a.posonlyargs + a.kwonlyargs}
            out |= {x.arg for x in (a.vararg, a.kwarg) if x}
        elif isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            out.add(n.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            out |= {(a.asname or a.name).split(".")[0] for a in n.names}
        elif isinstance(n, ast.ExceptHandler) and n.name:
            out.add(n.name)
        elif isinstance(n, (ast.Global, ast.Nonlocal)):
            out |= set(n.names)
    return out


def _loads(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


def _toplevel_defined(stmts: list[ast.stmt]) -> list[str]:
    out: list[str] = []
    for s in stmts:
        if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.append(s.name)
        elif isinstance(s, ast.Assign):
            for t in s.targets:
                for el in (t.elts if isinstance(t, (ast.Tuple, ast.List)) else [t]):
                    if isinstance(el, ast.Name):
                        out.append(el.id)
        elif isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name):
            out.append(s.target.id)
        elif isinstance(s, ast.For) and isinstance(s.target, ast.Name):
            out.append(s.target.id)
    seen: set[str] = set()
    return [n for n in out if not (n in seen or seen.add(n))]


def _pack_common(common: list[ast.stmt]) -> list[tuple[str, list[ast.stmt]]]:
    n = len(common)
    defined = [set(_toplevel_defined([s])) for s in common]
    refs = [_loads(s) - _bound(s) for s in common]
    deps: list[set[int]] = []
    name_at: dict[str, int] = {}
    for i, d in enumerate(defined):
        for nm in d:
            name_at.setdefault(nm, i)
    for i in range(n):
        deps.append({name_at[nm] for nm in refs[i] if nm in name_at and name_at[nm] != i})

    # Tarjan SCC (iterative)
    index_of: dict[int, int] = {}
    low: dict[int, int] = {}
    on: set[int] = set()
    stack: list[int] = []
    sccs: list[list[int]] = []
    counter = [0]

    def strong(v: int) -> None:
        work = [(v, iter(sorted(deps[v])))]
        index_of[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on.add(v)
        while work:
            node, it = work[-1]
            advanced = False
            for w in it:
                if w not in index_of:
                    index_of[w] = low[w] = counter[0]
                    counter[0] += 1
                    stack.append(w)
                    on.add(w)
                    work.append((w, iter(sorted(deps[w]))))
                    advanced = True
                    break
                elif w in on:
                    low[node] = min(low[node], index_of[w])
            if advanced:
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[node])
            if low[node] == index_of[node]:
                comp = []
                while True:
                    w = stack.pop()
                    on.discard(w)
                    comp.append(w)
                    if w == node:
                        break
                sccs.append(sorted(comp))

    for v in range(n):
        if v not in index_of:
            strong(v)

    scc_of = {v: k for k, comp in enumerate(sccs) for v in comp}
    scc_deps: list[set[int]] = [set() for _ in sccs]
    for v in range(n):
        for w in deps[v]:
            if scc_of[w] != scc_of[v]:
                scc_deps[scc_of[v]].add(scc_of[w])
    import heapq

    indeg = {k: len(d) for k, d in enumerate(scc_deps)}
    users: list[set[int]] = [set() for _ in sccs]
    for k, d in enumerate(scc_deps):
        for j in d:
            users[j].add(k)
    heap = [(min(sccs[k]), k) for k in indeg if indeg[k] == 0]
    heapq.heapify(heap)
    order: list[int] = []
    while heap:
        _, k = heapq.heappop(heap)
        order.append(k)
        for u in users[k]:
            indeg[u] -= 1
            if indeg[u] == 0:
                heapq.heappush(heap, (min(sccs[u]), u))
    assert len(order) == len(sccs), "cycle survived SCC condensation - impossible"

    files: list[list[int]] = [[]]
    size = 0
    for k in order:
        span = sum((common[v].end_lineno or 0) - common[v].lineno + 1 for v in sccs[k])
        if size and size + span > COMMON_TARGET_LINES:
            files.append([])
            size = 0
        files[-1].extend(sccs[k])
        size += span
    out: list[tuple[str, list[ast.stmt]]] = []
    used: set[str] = set()
    for fi, members in enumerate(files):
        members.sort()
        names = set().union(*(defined[v] for v in members), set())
        theme = next((t for m, t in COMMON_NAMES if m in names and t not in used), f"helpers_{'abcdef'[fi]}")
        used.add(theme)
        out.append((f"common_{fi + 1:02d}_{theme}", [common[v] for v in members]))
    return out


def main() -> None:
    src = open(MONO).read()
    lines = src.splitlines(keepends=True)
    tree = ast.parse(src)
    body = tree.body

    assert isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant), "expected module docstring"
    docstring_node = body[0]
    imports = [s for s in body if isinstance(s, (ast.Import, ast.ImportFrom))]
    assert all(s.lineno < 70 for s in imports), "unexpected late top-level import"
    import_map: dict[str, str] = {}  # bound name -> source module ('' means plain `import name`)
    for s in imports:
        if isinstance(s, ast.Import):
            for a in s.names:
                import_map[(a.asname or a.name).split(".")[0]] = ""
        else:
            for a in s.names:
                import_map[a.asname or a.name] = s.module or ""

    rest = [s for s in body if s is not docstring_node and s not in imports]

    # ---- carve the top-level statements into ordered (module, stmts) regions -------------
    def first_name(s: ast.stmt) -> str:
        if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return s.name
        if isinstance(s, ast.Assign) and s.targets and isinstance(s.targets[0], ast.Name):
            return s.targets[0].id
        if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name):
            return s.target.id
        return ""

    regions: list[tuple[str, list[ast.stmt]]] = []
    seg_start = next(i for i, s in enumerate(rest) if isinstance(s, ast.FunctionDef) and s.name.startswith("_seg_"))
    common, tail = rest[:seg_start], rest[seg_start:]

    regions.extend(_pack_common(common))

    seg_end = max(i for i, s in enumerate(tail) if isinstance(s, ast.FunctionDef) and s.name.startswith("_seg_"))
    segs, after = tail[: seg_end + 1], tail[seg_end + 1 :]
    assert all(isinstance(s, ast.FunctionDef) and s.name.startswith("_seg_") for s in segs), "non-segment statement inside the segment region"
    cut_idx = [next(i for i, s in enumerate(segs) if s.name.startswith(pfx)) for pfx, _, _ in SEG_CUTS]  # type: ignore[union-attr]
    assert cut_idx[0] == 0 and cut_idx == sorted(cut_idx)
    for j, (_, mod, parts) in enumerate(SEG_CUTS):
        chunk = segs[cut_idx[j] : cut_idx[j + 1] if j + 1 < len(cut_idx) else len(segs)]
        if parts == 1:
            regions.append((mod, chunk))
        else:
            per = (len(chunk) + parts - 1) // parts
            for p in range(parts):
                sub = chunk[p * per : (p + 1) * per]
                assert sub
                regions.append((f"{mod}_{'abc'[p]}", sub))

    # registry region: _GateSeg .. the Delete after the _SEG_DEPS loop; driver: rest; __main__: final If
    gs = next(i for i, s in enumerate(after) if isinstance(s, ast.ClassDef) and s.name == "_GateSeg")
    assert gs == 0
    del_i = next(i for i, s in enumerate(after) if isinstance(s, ast.Delete))
    final_if = after[-1]
    assert isinstance(final_if, ast.If) and "__main__" in ast.unparse(final_if.test)
    regions.append(("registry", after[: del_i + 1]))
    regions.append(("driver", after[del_i + 1 : -1]))

    # ---- per-module import generation -----------------------------------------------------
    where: dict[str, str] = {}
    for mod, stmts in regions:
        for n in _toplevel_defined(stmts):
            where.setdefault(n, mod)

    order = {mod: i for i, (mod, _) in enumerate(regions)}

    def imports_for(mod: str, stmts: list[ast.stmt]) -> str:
        defined = set(_toplevel_defined(stmts))
        needed: set[str] = set()
        for s in stmts:
            needed |= _loads(s) - _bound(s)
        needed -= defined | BUILTINS
        plain: list[str] = []
        froms: dict[str, list[str]] = {}
        rels: dict[str, list[str]] = {}
        unresolved: list[str] = []
        for n in sorted(needed):
            if n in where and where[n] != mod:
                src_mod = where[n]
                assert order[src_mod] < order[mod], f"{mod} needs {n} from LATER module {src_mod} - cycle"
                rels.setdefault(src_mod, []).append(n)
            elif n in import_map:
                m = import_map[n]
                (plain.append(n) if m == "" else froms.setdefault(m, []).append(n))
            else:
                unresolved.append(n)
        assert not unresolved, f"{mod}: unresolved names {unresolved}"
        out = [f"import {n}\n" for n in sorted(plain)]
        out += [f"from {m} import {', '.join(sorted(ns))}\n" for m, ns in sorted(froms.items())]
        out += [f"from .{m} import {', '.join(sorted(ns))}\n" for m, ns in sorted(rels.items(), key=lambda kv: order[kv[0]])]
        return "".join(out)

    # ---- emit ------------------------------------------------------------------------------
    if os.path.isdir(PKG):
        shutil.rmtree(PKG)
    os.makedirs(PKG)

    DOCS = {
        "common_01_policy": "Shared types, core geometry, and the overlap/label/matrix policy engine (feature 024 package split; bodies verbatim from check_village.py).",
        "common_02_spatial": "Segment/rect/poly distance helpers, the GridIndex spatial index, and placement constants (feature 024 package split; bodies verbatim).",
        "common_03_features": "Theater/fire/ward/street/lane/crop feature helpers and DEFAULT_MANIFEST (feature 024 package split; bodies verbatim).",
        "common_04_capacity": "The walled-city capacity model, waiver constants, and the gate-scope plumbing (_UnboundType/_UNBOUND/_kept) (feature 024 package split; bodies verbatim).",
        "registry": "The ordered gate-segment registry. Row order IS the legacy execution order - the whole contract of feature 022.",
        "driver": "gate() - the registry driver - plus the twin-detector helpers and the CLI main() (feature 024 package split; bodies verbatim).",
    }

    def stmt_slice(s2: ast.stmt) -> str:
        start, end = s2.lineno - 1, s2.end_lineno
        while start > 0 and lines[start - 1].lstrip().startswith("#"):
            start -= 1
        return "".join(lines[start:end])

    for mod, stmts in regions:
        if mod.startswith("common_"):
            body_text = "\n\n".join(stmt_slice(s2).strip("\n") for s2 in stmts)
        else:
            start, end = stmts[0].lineno - 1, stmts[-1].end_lineno
            while start > 0 and (lines[start - 1].lstrip().startswith("#") or not lines[start - 1].strip()):
                start -= 1
            body_text = "".join(lines[start:end]).strip("\n")
        if mod.startswith("common_"):
            marquee = ", ".join(_toplevel_defined(stmts)[:8])
            doc = f"Shared gate helpers ({mod.split('_', 2)[-1].replace('_', ' ')}): {marquee}, ... - bodies verbatim from check_village.py (feature 024 package split; SCC-packed, see split_package.py)."
        else:
            doc = DOCS.get(mod, f"Gate segments ({mod.split('_', 2)[-1].replace('_', ' ')}) - bodies verbatim from check_village.py (feature 024 package split; registry order preserved).")
        head = f'"""{doc}"""\n\n'
        if mod == "registry":
            head += (
                "# CLAUSE-13 JUSTIFICATION (constitution Principle X): this file exceeds the ~1,000-line\n"
                "# file threshold DELIBERATELY. GATE_SEGMENTS is ordered DATA, not logic - its row order is\n"
                "# the execution contract (feature 022), and splitting the tuple across files would make\n"
                "# that order un-auditable for zero token benefit: nobody reads the registry linearly, and\n"
                "# gate(M, only=...) is how a row is found in practice.\n\n"
            )
        text = head + imports_for(mod, stmts) + "\n\n" + body_text + "\n"
        open(f"{PKG}/{mod}.py", "w").write(text)
        print(f"{mod}.py: {text.count(chr(10))} lines, {len(stmts)} top-level stmts")

    # __init__: package docstring (the monolith's) + explicit re-export of every name
    doc_text = "".join(lines[docstring_node.lineno - 1 : docstring_node.end_lineno])
    init = [doc_text, "\n"]
    for mod, stmts in regions:
        names = _toplevel_defined(stmts)
        if names:
            init.append(f"from .{mod} import {', '.join(names)}\n")
    open(f"{PKG}/__init__.py", "w").write("".join(init))
    print(f"__init__.py: {len(regions)} re-export lines")

    # __main__: the guard block verbatim, generated imports INSIDE the guard, pool path fixed up
    m_body = "".join(lines[final_if.body[0].lineno - 1 : final_if.end_lineno])
    old = "here = os.path.dirname(os.path.abspath(__file__))"
    assert m_body.count(old) == 1
    m_body = m_body.replace(old, "here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # __file__ moved one level down into the package (feature 024)")
    needed = (_loads(final_if) - _bound(final_if) - BUILTINS) & (set(where) | set(import_map))
    pkg_names = sorted(n for n in needed if n in where)
    ext = sorted(n for n in needed if n not in where and import_map.get(n) == "")
    im = "".join(f"    import {n}\n" for n in ext) + f"    from check_village import {', '.join(pkg_names)}\n"
    open(f"{PKG}/__main__.py", "w").write('"""CLI entry: python3 -m check_village <manifest.json> [--capacity [--capacity-map]]."""\n\nif __name__ == "__main__":\n' + im + "\n" + m_body)
    print("__main__.py written")

    os.remove(MONO)
    for p in os.listdir(f"{SKILL}/__pycache__"):
        if p.startswith("check_village."):
            os.remove(f"{SKILL}/__pycache__/{p}")
    print("monolith removed")


if __name__ == "__main__":
    main()
