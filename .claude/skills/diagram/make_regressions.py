#!/usr/bin/env python3
"""Backfill / regenerate the regression-fixture corpus in pool/regressions/.

Every negative fixture in test_checks.py feeds the gate a manifest built to TRIP one or more
named checks. This tool captures those manifests (by spying on check_village.gate while the
fixtures run) and freezes each as a standalone pool/regressions/<name>.json, tagged with the
checks it must fire (`_regression.fires`). test_regressions.py then replays the whole corpus.

This exists for the BACKFILL (turning the in-test synthetic manifests into on-disk fixtures) and
so the corpus can be regenerated if the fixtures change. The GOING-FORWARD discipline is simpler:
when a real generated map exposes a check gap, drop its manifest straight into pool/regressions/
with a `_regression` block - no tooling needed. Run:  python3 make_regressions.py
"""
import ast
import copy
import inspect
import json
import os
import textwrap

import check_village
import test_checks

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "pool", "regressions")


def positive_targets(fn):
    """Check names a test asserts are PRESENT in the failures (`"x" in f(M)` and loop-driven
    `for name in (...): assert name in fails`), skipping the `not in` (passes) assertions."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
    loops, targets = {}, []

    class V(ast.NodeVisitor):
        def visit_For(self, node):
            if isinstance(node.target, ast.Name) and isinstance(node.iter, (ast.Tuple, ast.List)):
                vals = [e.value for e in node.iter.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
                if vals:
                    loops[node.target.id] = vals
            self.generic_visit(node)

        def visit_Compare(self, node):
            if len(node.ops) == 1 and isinstance(node.ops[0], ast.In):
                left = node.left
                if isinstance(left, ast.Constant) and isinstance(left.value, str):
                    targets.append(left.value)
                elif isinstance(left, ast.Name) and left.id in loops:
                    targets.extend(loops[left.id])
            self.generic_visit(node)

    V().visit(tree)
    return targets


def main():
    os.makedirs(OUT, exist_ok=True)
    # wipe ONLY the previously auto-captured fixtures (tagged with a test_checks.py source); leave
    # hand-dropped real-map captures (any other source) untouched so a regen never clobbers them.
    for fn_name in os.listdir(OUT):
        if not fn_name.endswith(".json"):
            continue
        p = os.path.join(OUT, fn_name)
        with open(p) as fh:
            src = json.load(fh).get("_regression", {}).get("source", "")
        if src.startswith("test_checks.py::"):
            os.remove(p)

    captures = []
    orig = check_village.gate

    def spy(M, verbose=True):
        snap = copy.deepcopy(M)
        res = orig(M, verbose=False)
        captures.append((snap, set(res)))
        return res

    check_village.gate = spy
    try:
        fns = [v for k, v in sorted(vars(test_checks).items())
               if k.startswith("test_") and callable(v)]
        written, covered, gaps = 0, set(), []
        for fn in fns:
            tgs = positive_targets(fn)
            if not tgs:
                continue
            captures.clear()
            fn()
            groups = {}   # capture-index -> set(target checks fired by that manifest)
            for t in tgs:
                idx = next((i for i, (m, fs) in enumerate(captures) if t in fs), None)
                if idx is None:
                    gaps.append((fn.__name__, t))
                    continue
                groups.setdefault(idx, set()).add(t)
            base = fn.__name__[len("test_"):]
            multi = len(groups) > 1
            for n, idx in enumerate(sorted(groups)):
                M, _fs = captures[idx]
                M["_regression"] = {"fires": sorted(groups[idx]),
                                    "source": f"test_checks.py::{fn.__name__}"}
                name = base + (f"_{n + 1}" if multi else "")
                with open(os.path.join(OUT, name + ".json"), "w") as fh:
                    json.dump(M, fh, indent=1)
                written += 1
                covered |= groups[idx]
    finally:
        check_village.gate = orig

    all_checks = set()
    for line in open(os.path.join(HERE, "check_village.py")):
        line = line.strip()
        if line.startswith('check("'):
            all_checks.add(line.split('"')[1])
    missing = sorted(all_checks - covered)
    print(f"wrote {written} regression fixtures -> pool/regressions/")
    print(f"distinct checks covered by a fixture: {len(covered)} / {len(all_checks)} defined")
    if missing:
        print(f"checks with NO negative fixture (integration-only): {missing}")
    if gaps:
        print(f"WARNING - asserted targets that did not fire: {gaps}")


if __name__ == "__main__":
    main()
