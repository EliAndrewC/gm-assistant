#!/usr/bin/env python3
"""Generation-identity oracle for feature 025 (settlement.py -> settlement/ package).

One-shot migration tooling - lives in the feature dir, never imported by engine code, not under
the coverage gate (same standing as 022's oracle_sweep.py).

    python3 oracle_gen.py capture   # freeze artifact hashes -> oracle_gen_pre.json
    python3 oracle_gen.py compare   # re-generate, diff against the baseline, exit non-zero on drift

What it proves: for every LIVE scripted pool gen (poolmaps.classify == "scripted"; the frozen
legacy maps never run, by doctrine) plus a fixed-seed hamletgen cohort, the emitted .json manifest
and .svg are byte-identical before and after the package split - EXCEPT the svg's
`<!-- render-cache: ... -->` stamp line, which is stripped before hashing: the stamp hashes the
engine-source fingerprint and therefore legitimately changes when settlement.py becomes a package,
while the drawn bytes must not. The .png is not hashed - every generator writes svg+png together
(settlement.finish), so svg identity is the proof (render_cache.py's own doctrine).

The pool gens are regenerated via regen.py --no-cache (which skips FROZEN maps itself); the
cohort runs hamletgen.py at pinned seeds into a scratch dir so paths the pool gens do not take
(rolled knobs at other seeds) are covered too.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SKILL = os.path.join(REPO, ".claude", "skills", "diagram")
BASELINE = os.path.join(HERE, "oracle_gen_pre.json")
COHORT_DIR = "/tmp/l7r-025-cohort"
if SKILL not in sys.path:
    sys.path.insert(0, SKILL)

# Pinned cohort: (seed, households). Seeds chosen to differ from the pool gens' own so rolled
# knobs (water_sink, cluster_shape, field_archetype, down_deg, windward) take other branches.
COHORT = [(3, 9), (8, 15), (13, 21), (18, 12), (27, 18)]


def stamp_stripped_sha(path: str) -> str:
    with open(path, "rb") as fh:
        lines = [ln for ln in fh.read().splitlines(keepends=True) if b"render-cache:" not in ln]
    return hashlib.sha256(b"".join(lines)).hexdigest()


def scripted_gens() -> list[str]:
    import poolmaps

    gens = sorted(glob.glob(os.path.join(SKILL, "pool", "*", "*.gen.py")))
    return [g for g in gens if poolmaps.classify(g) == "scripted"]


def generate() -> dict[str, dict[str, str]]:
    gens = scripted_gens()
    subprocess.run([sys.executable, "regen.py", "--no-cache", *[os.path.relpath(g, SKILL) for g in gens]], cwd=SKILL, check=True, capture_output=True, text=True)
    os.makedirs(COHORT_DIR, exist_ok=True)
    results: dict[str, dict[str, str]] = {}
    for g in gens:
        stem = g[: -len(".gen.py")]
        results[os.path.relpath(stem, SKILL)] = {"json": stamp_stripped_sha(stem + ".json"), "svg": stamp_stripped_sha(stem + ".svg")}
    for seed, households in COHORT:
        stem = os.path.join(COHORT_DIR, f"oracle-s{seed}-h{households}")
        subprocess.run(
            [sys.executable, "hamletgen.py", "--name", f"Oracle-s{seed}", "--seed", str(seed), "--households", str(households), "--out", stem],
            cwd=SKILL,
            check=True,
            capture_output=True,
            text=True,
        )
        results[f"cohort/s{seed}-h{households}"] = {"json": stamp_stripped_sha(stem + ".json"), "svg": stamp_stripped_sha(stem + ".svg")}
    return results


def main(argv: list[str]) -> int:
    mode = argv[0]
    results = generate()
    if mode == "capture":
        with open(BASELINE, "w") as fh:
            json.dump(results, fh, indent=0, sort_keys=True)
        print(f"captured {len(results)} artifacts -> {BASELINE}")
        return 0
    with open(BASELINE) as fh:
        base = json.load(fh)
    bad = 0
    for key in sorted(set(base) | set(results)):
        old, new = base.get(key), results.get(key)
        if old is None or new is None:
            print(f"{'NEW' if old is None else 'GONE':8s} {key}")
            bad += 1
        elif old != new:
            what = ",".join(k for k in ("json", "svg") if old[k] != new[k])
            print(f"DIFF     {key} ({what})")
            bad += 1
    print(f"{len(results)} artifacts compared, {bad} drifted")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
