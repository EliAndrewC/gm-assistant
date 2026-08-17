#!/usr/bin/env python3
"""Differential audit of the generation cache: does using it ever change what a map looks like?

    python3 -m l7r.diagram.tools.cache_audit                 # 3 mutations against a representative subset (~7 min)
    python3 -m l7r.diagram.tools.cache_audit --trials 6      # more mutations
    python3 -m l7r.diagram.tools.cache_audit --all           # every map in the pool (slow)

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

AND THE SITE IS CHOSEN FROM WHAT THE MAPS ACTUALLY RUN, not from a hand-picked file (2026-08-17).
Both halves of that sentence were paid for:

  - A hand-picked TARGET file was wrong twice, both times because the file became a DIRECTORY (the
    settlement.py package split, then _geom.py's). Each time the audit crashed on its next mandatory
    run. The target is a PACKAGE now, so a refactor inside it cannot break the tool.
  - Choosing at random inside one file wasted most of the run: measured against the whole
    `settlement/` package, only **684 of its 4,306** numeric literals sit in code these maps
    execute, and the file that had been picked offered **7**. A 3-trial run therefore took 19
    attempts and eleven minutes to audit the cache three times.

So a coverage pass over the audited gens (~75s, paid once) says which lines actually run, and
`numeric_sites` offers only literals on those lines that are NOT default arguments. Excluding the
rest is provably safe rather than merely convenient: a literal in code that never runs leaves every
artifact identical, so a cached sweep and a fresh sweep agree whatever the key does - there is no
cache defect it could have hidden. Coverage alone is not enough, though, and the trap is worth
naming: a DEFAULT argument's literal is evaluated at definition time, so its line reads as executed
even when nothing ever calls the function.

The vacuity retry stays as the backstop, because a literal can be executed and still move nothing
(a clamp that dominates it, a value that rounds away). It is the belt to coverage's braces.

MEASURED AFTER THE REWRITE, so the next reader plans against numbers rather than hopes: the pool is
**1,147 candidates across 40 executed engine files** (settlement 660, hamletgen 244, waterfields
241, sitegen 2), and `--trials 3` audited **3 of 3 with none vacuous and none skipped**, each
mutation moving all four artifacts, landing in three different subsystems (a placer spiral, a civic
fixture, a hinterland scatter). Total ~7 minutes: ~75s for the coverage pass, then 100-135s per
trial - a trial costs two full sweeps, and it is SLOWER than the old one because a site in hot
placement code genuinely makes generation more expensive, which is the price of the site meaning
something. Against the old design's 11 minutes for the same three audits plus sixteen wasted
attempts, and all three of those in one geometry file.

It is deliberately NOT part of `make done`: it costs minutes, and the gate already guarantees
correctness by regenerating from scratch. Run it when you have changed the cache, changed how
generation is driven, or simply want the reassurance.
"""

from __future__ import annotations

import argparse
import ast
import glob
import json
import os
import pathlib
import random
import shutil
import subprocess
import sys
import tempfile
import time

from l7r.diagram.pipeline import poolmaps

HERE = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
)  # the skill root; this module lives in l7r/diagram/tools/ - FOUR levels up since feature 119, not two
# The LIVE pool is the scripted maps - the hand-authored maps froze on 2026-08-16 and are never
# regenerated (poolmaps.py) - so the audit sweeps those: sawada is the biggest, inashiro the
# cheapest.
SUBSET = ("sawada", "inashiro")

# The trees mutations are drawn from - DIRECTORIES on purpose (see the module docstring): a
# file-shaped target has been invalidated by a package split twice, and each time the audit crashed
# on its next mandatory run rather than degrading.
#
# These four are what DRAWS a map, which is the whole membership rule. Deliberately absent:
# `check_village` (the gate reads a manifest, it never writes one, so mutating it moves no
# artifact), `tools` (diagnostics), and `pipeline` (the driver and the cache ITSELF - perturbing the
# thing under audit is not a test of it).
ENGINE = os.path.join("l7r", "diagram")
ENGINE_TREES = ("settlement", "waterfields", "sitegen", "hamletgen")

# A sweep that has not finished in this many seconds is treated as a failed trial rather than
# waited out. Only needed since the mutation site became the whole engine: a perturbed literal
# anywhere in the package can, in principle, put a placer into a much longer search, and a hung
# audit looks exactly like a slow one.
SWEEP_TIMEOUT_BASE, SWEEP_TIMEOUT_PER_MAP = 60, 180


def gens(all_maps: bool) -> list[str]:
    out = []
    for gen in sorted(glob.glob(os.path.join(HERE, "pool", "*", "*.gen.py"))):
        if poolmaps.classify(gen) != "scripted":
            continue  # frozen legacy maps are never regenerated; compound gens have no manifest
        if all_maps or os.path.basename(gen)[: -len(".gen.py")] in SUBSET:
            out.append(gen)
    return out


def executed_lines(paths: list[str]) -> dict[str, set[int]]:
    """Which ENGINE lines the audited maps actually RUN, as {path relative to HERE: {lineno}}.

    Measured by running each gen under `coverage`, which is an observation of the GENERATOR and
    never consults the cache - so using it to pick sites cannot share the blind spots of the thing
    being audited. Rendering is skipped: the audit compares `.json` and `.svg` only (the PNG is a
    pure function of the SVG), so the renderer's lines are not sites worth mutating anyway.

    `COVERAGE_FILE` points at a temp dir, so a repo `.coverage` from a gate run is never clobbered.

    THE MEMBERSHIP RULE IS STATED TWICE, AT BOTH ENDS, AND BOTH TIMES ON PURPOSE - this skill's
    `pyproject.toml` carries a `[tool.coverage.run] source` list, and leaving either end to it was
    wrong in a different direction each time:

    - `--include` is IGNORED whenever `source` is set, so the first draft's include flag did nothing
      and the census offered 1,460 candidates across 101 files, most of them in `check_village`,
      whose literals cannot move an artifact at all.
    - the config's `source` list does not name `waterfields`, so its lines were never measured and
      the comb-field engine - which draws every paddy on these maps - contributed ZERO candidates.
      A tool silently blind to a whole engine is the same defect as a check that never runs.

    So `--source` names the trees explicitly (overriding the config), and the RESULT is filtered by
    the same rule, where no config can reach it.
    """
    tmp = tempfile.mkdtemp(prefix="cache-audit-cov-")
    env = {**os.environ, "COVERAGE_FILE": os.path.join(tmp, "data"), "DIAGRAM_SKIP_RENDER": "1"}
    source = ",".join(os.path.join(ENGINE, tree) for tree in ENGINE_TREES)
    for gen in paths:
        subprocess.run([sys.executable, "-m", "coverage", "run", "-a", f"--source={source}", gen], cwd=HERE, env=env, capture_output=True)
    out = os.path.join(tmp, "cov.json")
    subprocess.run([sys.executable, "-m", "coverage", "json", "-o", out], cwd=HERE, env=env, capture_output=True)
    try:
        files = json.loads(pathlib.Path(out).read_text())["files"]
    except OSError, KeyError, json.JSONDecodeError:  # pragma: no cover - defensive
        return {}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    drawn = tuple(os.path.join(ENGINE, tree) + os.sep for tree in ENGINE_TREES)
    rels = {os.path.relpath(os.path.join(HERE, k), HERE): v for k, v in files.items()}
    return {rel: set(v["executed_lines"]) for rel, v in rels.items() if rel.startswith(drawn)}


def numeric_sites(source: str, executed: set[int]) -> list[tuple[int, int, int, str]]:
    """(lineno, col, end_col, text) for every numeric literal a mutation could actually move a map
    with - which is a much smaller set than "every numeric literal", and that gap was the whole cost.

    Two filters, both of them measured rather than reasoned (see the module docstring):

    - **On a line in `executed`.** A literal in code no audited map runs cannot change an artifact,
      so mutating it burns a sweep pair to prove nothing. Excluding it is provably safe: with the
      artifacts identical, cached and fresh sweeps agree whatever the key does.
    - **Not a DEFAULT argument.** Its literal is evaluated at definition time, so the line reads as
      executed even when nothing calls the function - coverage cannot see that it is inert, and when
      every caller passes the argument explicitly, perturbing it moves nothing.

    Deduplicated and sorted: `ast.walk` reaches a nested function twice (once through its parent),
    and a seeded run must offer the same pool in the same order every time.
    """
    sites = set()
    for fn in ast.walk(ast.parse(source)):
        if not isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        defaults = {id(n) for d in (fn.args.defaults + fn.args.kw_defaults) if d is not None for n in ast.walk(d)}
        for node in ast.walk(fn):
            if not isinstance(node, ast.Constant) or isinstance(node.value, bool) or not isinstance(node.value, int | float):
                continue
            if node.end_lineno != node.lineno or not (1 < abs(node.value) < 10000):
                continue
            if id(node) in defaults or node.lineno not in executed:
                continue
            sites.add((node.lineno, node.col_offset, node.end_col_offset, repr(node.value)))
    return sorted(sites)


def mutate(source: str, site: tuple[int, int, int, str]) -> str:
    lineno, col, end_col, text = site
    lines = source.splitlines(keepends=True)
    value = ast.literal_eval(text)
    new = repr(value + (1 if isinstance(value, int) else 0.5))
    lines[lineno - 1] = lines[lineno - 1][:col] + new + lines[lineno - 1][end_col:]
    return "".join(lines)


def sweep(paths: list[str], use_cache: bool) -> bool:
    cmd = [sys.executable, "-m", "l7r.diagram.pipeline.regen", *([] if use_cache else ["--no-cache"]), *paths]
    timeout = SWEEP_TIMEOUT_BASE + SWEEP_TIMEOUT_PER_MAP * len(paths)
    try:
        return subprocess.run(cmd, capture_output=True, text=True, cwd=HERE, timeout=timeout).returncode == 0
    except subprocess.TimeoutExpired:  # a perturbed literal can put a placer into a far longer search
        return False


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
    print(f"auditing {len(paths)} maps against {args.trials} mutation(s) of {ENGINE}/")
    print("measuring which engine lines these maps execute...")
    executed = executed_lines(paths)
    sites: list[tuple[str, int, int, int, str]] = []
    originals: dict[str, str] = {}
    for rel in sorted(executed):
        src = pathlib.Path(os.path.join(HERE, rel)).read_text()
        found = numeric_sites(src, executed[rel])
        if found:
            originals[rel] = src
            sites += [(rel, *s) for s in found]
    # A census that silently returns nothing is indistinguishable from a clean bill of health - the
    # exact shape this tool's own vacuous trials had. Refuse rather than audit an empty pool.
    if not sites:
        print(f"REFUSING: the coverage pass found no mutable literal in {ENGINE}/ that these maps execute.")
        print("         Either the coverage run failed, or ENGINE points somewhere the maps never reach.")
        return 1
    print(f"  {len(sites)} candidate literals across {len(originals)} executed engine files")
    rng = random.Random(args.seed)

    failures, skipped, done = [], 0, 0
    try:
        print("\nestablishing a clean baseline...")
        sweep(paths, use_cache=True)
        # The UNMUTATED artifacts, so each trial can report whether its mutation actually moved
        # anything. Without this a trial that changed no byte - a literal on a line these maps never
        # execute, or one that rounds away - prints exactly the same `[OK ]` as a trial that really
        # exercised the key, and a whole run can pass having proven nothing. Same shape as the
        # skill's "a check that never RUNS looks exactly like a check that passes", here in the very
        # tool that exists to keep the cache honest.
        clean = snapshot(paths, "/tmp/audit-clean")
        vacuous = 0
        while done < args.trials and sites:
            rel, *rest = sites.pop(rng.randrange(len(sites)))
            site: tuple[int, int, int, str] = (rest[0], rest[1], rest[2], rest[3])
            path = pathlib.Path(os.path.join(HERE, rel))
            where = f"{os.path.relpath(rel, ENGINE)}:{site[0]}"
            path.write_text(mutate(originals[rel], site))
            try:
                ast.parse(path.read_text())
            except SyntaxError:  # pragma: no cover - defensive
                path.write_text(originals[rel])
                skipped += 1
                continue
            started = time.time()
            ok_cached = sweep(paths, use_cache=True)
            with_cache = snapshot(paths, "/tmp/audit-a")
            ok_fresh = sweep(paths, use_cache=False)
            without = snapshot(paths, "/tmp/audit-b")
            if not (ok_cached and ok_fresh) or not with_cache:
                # The mutation broke generation (or hung it past SWEEP_TIMEOUT). Not a cache
                # finding - now a routine outcome rather than a rarity, since a site can land
                # anywhere in the engine rather than in one hand-picked geometry file.
                print(f"  [skip] {where}: {site[3]} -> perturbed | a sweep failed or timed out | {time.time() - started:.0f}s")
                skipped += 1
                path.write_text(originals[rel])
                continue
            differing = sorted(k for k in with_cache if with_cache[k] != without.get(k))
            moved = sorted(k for k in with_cache if with_cache[k] != clean.get(k))
            if not moved and not differing:
                # A mutation that moved NO artifact tested nothing: the sweeps agreed because there
                # was nothing to disagree about. Counting it toward --trials is how a run of three
                # ends up having audited one - measured on this tool's first run against the
                # feature-117 target, where 2 of 3 trials were vacuous and printed an identical
                # `[OK ]`. So it is a skip, not a trial. (`differing` is still checked first: a
                # mutation that moved nothing and STILL produced disagreeing sweeps is a genuine
                # finding and must never be swallowed by this branch.)
                vacuous += 1
                print(f"  [----] {where}: {site[3]} -> perturbed | moved nothing, so it tested nothing - not counted | {time.time() - started:.0f}s")
                path.write_text(originals[rel])
                continue
            done += 1
            verdict = "OK " if not differing else "STALE"
            print(f"  [{verdict}] {where}: {site[3]} -> perturbed | moved {len(moved)} of {len(with_cache)} artifacts | {time.time() - started:.0f}s")
            if differing:
                failures.append(((rel, *site), differing))
                print(f"          CACHE SERVED STALE ARTIFACTS: {differing}")
            path.write_text(originals[rel])
    finally:
        for rel, src in originals.items():  # every file a trial touched, not just the last one
            pathlib.Path(os.path.join(HERE, rel)).write_text(src)
        sweep(paths, use_cache=False)
        shutil.rmtree("/tmp/audit-a", ignore_errors=True)
        shutil.rmtree("/tmp/audit-b", ignore_errors=True)
        shutil.rmtree("/tmp/audit-clean", ignore_errors=True)
        dirty = subprocess.run(["git", "status", "--short", "pool", ENGINE], capture_output=True, text=True, cwd=HERE).stdout
        print(f"\nrestored {ENGINE}/; pool + engine dirty after restore: {dirty.strip() or 'NONE'}")

    print(f"\n{done} mutation(s) audited, {skipped} skipped, {vacuous} vacuous (moved nothing, retried), {len(failures)} FAILED")
    if done < args.trials:
        print(f"WARNING: only {done} of {args.trials} requested trials moved an artifact - the candidate literals ran out.")
        print(f"         Every remaining literal in {ENGINE}/ either moves nothing or breaks generation,")
        print("         which is a finding in itself: re-read the [----] and [skip] lines above.")
    if failures:
        print("A failure means a cached sweep and a fresh sweep disagreed - the cache is serving stale maps.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
