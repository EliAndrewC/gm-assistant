#!/usr/bin/env python3
"""Regenerate a map, skipping the work when nothing that map depends on has changed.

    python3 regen.py pool/provincial-cities/minami.gen.py      # cached when possible
    python3 regen.py pool/*/*.gen.py                           # the whole pool
    python3 regen.py --no-cache pool/towns/ubame.gen.py        # force the work

This is the ITERATION path. The gate (`test_villages.py`) deliberately does not come through here -
it always regenerates - so the cache can never put a wrong map past `make done`. See gencache.py
for why the key is safe and what it covers.

Every run says which path it took, because a silent cache is how you end up staring at a stale PNG
wondering why your change did nothing.
"""

from __future__ import annotations

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


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    use_cache = "--no-cache" not in argv
    if not args:
        print(__doc__)
        return 2
    saved = 0.0
    for gen in args:
        if not gen.endswith(".gen.py"):
            print(f"skipping {gen}: not a .gen.py")
            continue
        how, took = regen(gen, use_cache)
        name = os.path.basename(gen)[: -len(".gen.py")]
        print(f"{how:12s} {name:16s} {took:5.1f}s")
        saved += took if how == "REGENERATED" else 0.0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
