#!/usr/bin/env python3
"""Regenerate a map, skipping the work when nothing that map depends on has changed.

    python3 -m pipeline.regen pool/hamlets/sawada.gen.py                # cached when possible
    python3 -m pipeline.regen pool/*/*.gen.py                           # every LIVE map, fanned out
    python3 -m pipeline.regen --no-cache pool/hamlets/inashiro.gen.py   # force the work
    python3 -m pipeline.regen --jobs 1 pool/*/*.gen.py                  # serial

FROZEN legacy maps are skipped (printed as `FROZEN`), not regenerated: the hand-authored pool
froze on 2026-08-16 (migration-plan.md "The accepted trade") and the engine has been free to
drift since, so re-running a legacy gen would rewrite committed exhibit artifacts with output
nobody has reviewed. `--frozen-ok` overrides for a deliberate, GM-sanctioned re-render.

This is the ITERATION path: it never records coverage, so it stays as fast as a regen can be. The
gate (`tests/test_villages.py`) rides the SAME cache since feature 026, via `gencache.gate_obtain` - a
verified hit skips generation only (the check battery always runs), a miss regenerates in a
coverage-recording subprocess, and `GATE_NO_CACHE=1` bypasses. See gencache.py for why the key is
safe and what it covers.

Multiple maps regenerate in parallel worker processes (2026-08-15; the timings ledger flagged the
serial sweep as the biggest available win). This is safe because each map is a pure function of its
own sources - workers share nothing - and gencache.store publishes entries atomically
(temp-then-replace, meta.json last), a property it already needed for two runs in one tree. Each
map's output is captured in its worker and printed whole, in argument order, so parallel runs read
like serial ones instead of interleaving.

Every run says which path it took, because a silent cache is how you end up staring at a stale PNG
wondering why your change did nothing.
"""

from __future__ import annotations

import concurrent.futures
import contextlib
import io
import os
import sys
import time

from . import gencache, poolmaps


def regen(gen: str, use_cache: bool = True) -> tuple[str, float]:
    started = time.time()
    if use_cache and gencache.load(gen):
        return "CACHED", time.time() - started
    deps = gencache.run_and_record(gen)
    gencache.store(gen, deps)
    return "REGENERATED", time.time() - started


def regen_captured(gen: str, use_cache: bool) -> tuple[str, float, str]:
    """`regen`, with the gen's own stdout captured so parallel workers cannot interleave it."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        how, took = regen(gen, use_cache)
    return how, took, buf.getvalue()


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    use_cache = "--no-cache" not in argv
    jobs = None
    if "--jobs" in argv:  # --jobs N (the only flag with a value, so a hand-rolled parse suffices)
        jobs = int(argv[argv.index("--jobs") + 1])
        args.remove(str(jobs))
    if not args:
        print(__doc__)
        return 2
    gens = [g for g in args if g.endswith(".gen.py")]
    for skipped in (g for g in args if not g.endswith(".gen.py")):
        print(f"skipping {skipped}: not a .gen.py")
    if "--frozen-ok" not in argv:
        frozen = {g for g in gens if poolmaps.classify(g) == "legacy"}
        for g in sorted(frozen):
            print(f"{'FROZEN':12s} {os.path.basename(g)[: -len('.gen.py')]:16s} legacy hand-authored map (frozen 2026-08-16, migration-plan.md) - not regenerated; pass --frozen-ok to force")
        gens = [g for g in gens if g not in frozen]
    if not gens:
        return 0
    if jobs is None:  # leave two cpus for the harness and whatever else shares the box
        jobs = max(1, min(len(gens), (os.cpu_count() or 2) - 2))
    if jobs == 1 or len(gens) == 1:
        results = [regen_captured(gen, use_cache) for gen in gens]
    else:
        with concurrent.futures.ProcessPoolExecutor(max_workers=jobs) as ex:
            results = list(ex.map(regen_captured, gens, [use_cache] * len(gens)))
    for gen, (how, took, out) in zip(gens, results, strict=True):
        if out:
            print(out, end="")
        name = os.path.basename(gen)[: -len(".gen.py")]
        print(f"{how:12s} {name:16s} {took:5.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
