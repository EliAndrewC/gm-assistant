#!/usr/bin/env python3
"""Differential audit of the generation cache: does using it ever change what a map looks like?

    python3 cache_audit.py                 # 3 mutations against a representative subset (~10 min)
    python3 cache_audit.py --trials 6      # more mutations
    python3 cache_audit.py --all           # every map in the pool (slow)

WHY THIS EXISTS, AND WHY IT IS NOT A UNIT TEST. `test_gencache.py` tests the KEY - that the right
inputs move it. This tests the only thing anyone actually cares about: that a sweep WITH the cache
produces byte-identical maps to a sweep WITHOUT it. It never looks at the key at all, so it cannot
share the key's blind spots.

That distinction is not theoretical. On 2026-08-08 the cache under-keyed every map after the first
in a sweep - `sys.monitoring`'s DISABLE is permanent per code object, so map #2 onward recorded
almost no dependencies and would have read as a hit through nearly any engine change. Every unit
test passed throughout, because each builds a fresh module whose code objects were never disabled.
It took an end-to-end sweep to see it. This script is that sweep, generalized and repeatable.

THE MUTATIONS MUST CHANGE BEHAVIOR. A comment inserted into a function moves the key but leaves the
output identical, so both sweeps agree no matter how broken the cache is - the test would pass
vacuously. So this perturbs NUMERIC LITERALS inside function bodies, which is crude but genuinely
changes what gets drawn. A mutation that makes a gen raise is skipped, not counted.

It is deliberately NOT part of `make done`: it costs minutes, and the gate already guarantees
correctness by regenerating from scratch. Run it when you have changed the cache, changed how
generation is driven, or simply want the reassurance.
"""

from __future__ import annotations

import argparse
import ast
import glob
import os
import pathlib
import random
import shutil
import subprocess
import sys
import time

import poolmaps

HERE = os.path.dirname(os.path.abspath(__file__))
# The LIVE pool is the scripted maps - the hand-authored maps froze on 2026-08-16 and are never
# regenerated (poolmaps.py) - so the audit sweeps those: sawada is the biggest, inashiro the
# cheapest. The mutation target moved when feature 025 made settlement.py the settlement/ package
# (the file-shaped target crashed the audit, found by feature 026's mandatory run): _geom.py is
# the package module the live hamlets execute MOST (49 of sawada's recorded dep functions), and
# geometry literals genuinely move what gets drawn.
SUBSET = ("sawada", "inashiro")
TARGET = os.path.join("settlement", "_geom.py")


def gens(all_maps: bool) -> list[str]:
    out = []
    for gen in sorted(glob.glob(os.path.join(HERE, "pool", "*", "*.gen.py"))):
        if poolmaps.classify(gen) != "scripted":
            continue  # frozen legacy maps are never regenerated; compound gens have no manifest
        if all_maps or os.path.basename(gen)[: -len(".gen.py")] in SUBSET:
            out.append(gen)
    return out


def numeric_sites(source: str) -> list[tuple[int, int, int, str]]:
    """(lineno, col, end_col, text) for every numeric literal INSIDE a function body - the places a
    change actually alters what is drawn."""
    tree = ast.parse(source)
    sites = []
    for fn in ast.walk(tree):
        if not isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        for node in ast.walk(fn):
            if isinstance(node, ast.Constant) and isinstance(node.value, int | float) and not isinstance(node.value, bool) and node.end_lineno == node.lineno and 1 < abs(node.value) < 10000:
                sites.append((node.lineno, node.col_offset, node.end_col_offset, repr(node.value)))
    return sites


def mutate(source: str, site: tuple[int, int, int, str]) -> str:
    lineno, col, end_col, text = site
    lines = source.splitlines(keepends=True)
    value = ast.literal_eval(text)
    new = repr(value + (1 if isinstance(value, int) else 0.5))
    lines[lineno - 1] = lines[lineno - 1][:col] + new + lines[lineno - 1][end_col:]
    return "".join(lines)


def sweep(paths: list[str], use_cache: bool) -> bool:
    cmd = [sys.executable, os.path.join(HERE, "regen.py"), *([] if use_cache else ["--no-cache"]), *paths]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=HERE).returncode == 0


def snapshot(paths: list[str], where: str) -> dict[str, bytes]:
    os.makedirs(where, exist_ok=True)
    out = {}
    for gen in paths:
        for suffix in (".json", ".svg"):  # the PNG is a pure function of the SVG
            art = gen[: -len(".gen.py")] + suffix
            if os.path.isfile(art):
                out[os.path.basename(art)] = pathlib.Path(art).read_bytes()
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    paths = gens(args.all)
    target = pathlib.Path(os.path.join(HERE, TARGET))
    original = target.read_text()
    sites = numeric_sites(original)
    rng = random.Random(args.seed)
    print(f"auditing {len(paths)} maps against {args.trials} mutation(s) of {TARGET} ({len(sites)} candidate literals)")

    failures, skipped, done = [], 0, 0
    try:
        print("\nestablishing a clean baseline...")
        sweep(paths, use_cache=True)
        while done < args.trials and sites:
            site = sites.pop(rng.randrange(len(sites)))
            target.write_text(mutate(original, site))
            try:
                ast.parse(target.read_text())
            except SyntaxError:  # pragma: no cover - defensive
                target.write_text(original)
                skipped += 1
                continue
            started = time.time()
            ok_cached = sweep(paths, use_cache=True)
            with_cache = snapshot(paths, "/tmp/audit-a")
            ok_fresh = sweep(paths, use_cache=False)
            without = snapshot(paths, "/tmp/audit-b")
            if not (ok_cached and ok_fresh) or not with_cache:
                skipped += 1
                target.write_text(original)
                continue
            differing = sorted(k for k in with_cache if with_cache[k] != without.get(k))
            done += 1
            verdict = "OK " if not differing else "STALE"
            print(f"  [{verdict}] line {site[0]}: {site[3]} -> perturbed | {len(with_cache)} artifacts | {time.time() - started:.0f}s")
            if differing:
                failures.append((site, differing))
                print(f"          CACHE SERVED STALE ARTIFACTS: {differing}")
            target.write_text(original)
    finally:
        target.write_text(original)
        sweep(paths, use_cache=False)
        shutil.rmtree("/tmp/audit-a", ignore_errors=True)
        shutil.rmtree("/tmp/audit-b", ignore_errors=True)
        dirty = subprocess.run(["git", "status", "--short", "pool"], capture_output=True, text=True, cwd=HERE).stdout
        print(f"\nrestored {TARGET}; pool dirty after restore: {dirty.strip() or 'NONE'}")

    print(f"\n{done} mutation(s) audited, {skipped} skipped, {len(failures)} FAILED")
    if failures:
        print("A failure means a cached sweep and a fresh sweep disagreed - the cache is serving stale maps.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
