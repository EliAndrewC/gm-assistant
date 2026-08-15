#!/usr/bin/env python3
"""Regenerate a map, skipping the work when nothing that map depends on has changed.

    python3 regen.py pool/provincial-cities/minami.gen.py      # cached when possible
    python3 regen.py pool/*/*.gen.py                           # the whole pool, fanned out
    python3 regen.py --no-cache pool/towns/ubame.gen.py        # force the work
    python3 regen.py --jobs 1 pool/*/*.gen.py                  # serial

This is the ITERATION path. The gate (`test_villages.py`) deliberately does not come through here -
it always regenerates - so the cache can never put a wrong map past `make done`. See gencache.py
for why the key is safe and what it covers.

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

import gencache


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
