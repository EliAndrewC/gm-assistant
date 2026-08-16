#!/usr/bin/env python3
"""Gate-identity oracle for feature 025 (settlement.py -> settlement/ package).

One-shot migration tooling, 022's oracle_sweep.py method trimmed to what 025 needs: full-mode
verdict + stdout identity over every regression fixture and every pool manifest.

    python3 oracle_gate.py capture   # freeze verdicts + stdout hashes -> oracle_gate_pre.json
    python3 oracle_gate.py compare   # re-run, diff to zero, exit non-zero on drift

The gate itself does not import settlement at run time (it reads manifests), but its segment
files DO import settlement helpers at module import - so a broken re-export surface fails here
loudly, which is exactly the point.
"""

from __future__ import annotations

import concurrent.futures
import contextlib
import glob
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SKILL = os.path.join(REPO, ".claude", "skills", "diagram")
BASELINE = os.path.join(HERE, "oracle_gate_pre.json")
if SKILL not in sys.path:
    sys.path.insert(0, SKILL)


def manifest_paths() -> list[str]:
    fixtures = sorted(glob.glob(os.path.join(SKILL, "pool", "regressions", "*.json")))
    pool = sorted(p for p in glob.glob(os.path.join(SKILL, "pool", "*", "*.json")) if os.path.basename(os.path.dirname(p)) != "regressions")
    return fixtures + pool


def run_full(path: str) -> tuple[str, list[str], str]:
    import check_village

    with open(path) as fh:
        M = json.load(fh)
    M.pop("_regression", None)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fails = sorted(check_village.gate(M))
    return path, fails, hashlib.sha256(buf.getvalue().encode()).hexdigest()


def main(argv: list[str]) -> int:
    mode = argv[0]
    jobs = max(1, (os.cpu_count() or 2) - 2)
    with concurrent.futures.ProcessPoolExecutor(max_workers=jobs) as ex:
        rows = list(ex.map(run_full, manifest_paths(), chunksize=8))
    results = {os.path.relpath(p, SKILL): {"fails": f, "stdout": h} for p, f, h in rows}
    if mode == "capture":
        with open(BASELINE, "w") as fh:
            json.dump(results, fh, indent=0, sort_keys=True)
        print(f"captured {len(results)} manifests -> {BASELINE}")
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
            what = "verdicts" if old["fails"] != new["fails"] else "stdout"
            print(f"DIFF     {key} ({what})")
            bad += 1
    print(f"{len(results)} manifests compared, {bad} drifted")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
