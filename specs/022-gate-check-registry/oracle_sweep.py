#!/usr/bin/env python3
"""Oracle sweeps for feature 022 (gate check registry). One-shot migration tooling - lives in the
feature dir, never imported by engine code, not under the coverage gate (plan.md, research.md R7).

    python3 oracle_sweep.py capture <out.json> [--limit N]   # freeze verdicts+stdout hashes
    python3 oracle_sweep.py compare <baseline.json>          # re-run, diff to zero
    python3 oracle_sweep.py targeted [--limit N]             # only= verdicts == full verdicts

capture/compare cover ALL regression fixtures + ALL pool manifests, in verbose mode, hashing
stdout - so "full-mode byte identity" is checked literally, not approximately. targeted runs every
fixture's declared fires through only= and demands the restricted verdict sets match the full
run's. Fan-out mirrors regen.py (processes; generation-free, so pure CPU on gate())."""

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
if SKILL not in sys.path:
    sys.path.insert(0, SKILL)


def manifest_paths() -> list[tuple[str, bool]]:
    """(path, is_fixture) for the whole oracle set: 791 fixtures + the pool maps."""
    fixtures = sorted(glob.glob(os.path.join(SKILL, "pool", "regressions", "*.json")))
    pool = sorted(p for p in glob.glob(os.path.join(SKILL, "pool", "*", "*.json")) if os.path.basename(os.path.dirname(p)) != "regressions")
    return [(p, True) for p in fixtures] + [(p, False) for p in pool]


def run_full(path: str) -> tuple[str, list[str], str]:
    """Full verbose gate on one manifest: (path, sorted failures, sha256 of stdout)."""
    import check_village

    with open(path) as fh:
        M = json.load(fh)
    M.pop("_regression", None)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fails = sorted(check_village.gate(M))
    return path, fails, hashlib.sha256(buf.getvalue().encode()).hexdigest()


def run_targeted(path: str) -> tuple[str, str]:
    """(path, verdict) where verdict is OK / FALLBACK(meta) / MISMATCH details."""
    import check_village

    with open(path) as fh:
        M = json.load(fh)
    fires = M.pop("_regression")["fires"]
    bases = {f.split("[")[0] for f in fires}
    meta = getattr(check_village, "META_CHECKS", frozenset())
    if bases & meta:
        return path, "FALLBACK"
    with contextlib.redirect_stdout(io.StringIO()):
        full = {f for f in check_village.gate(M, verbose=False) if f.split("[")[0] in bases}
        targ = {f for f in check_village.gate(M, verbose=False, only=bases) if f.split("[")[0] in bases}
    if full != targ:
        return path, f"MISMATCH full-only={sorted(full - targ)} targeted-only={sorted(targ - full)}"
    if not set(fires) <= targ:
        return path, f"MISMATCH fires not tripped: {sorted(set(fires) - targ)}"
    return path, "OK"


def _fan(fn, items):  # type: ignore[no-untyped-def]
    jobs = max(1, (os.cpu_count() or 2) - 2)
    with concurrent.futures.ProcessPoolExecutor(max_workers=jobs) as ex:
        return list(ex.map(fn, items, chunksize=8))


def main(argv: list[str]) -> int:
    mode = argv[0]
    limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else None
    if mode in ("capture", "compare"):
        paths = [p for p, _ in manifest_paths()][:limit]
        results = {os.path.relpath(p, SKILL): {"fails": f, "stdout": h} for p, f, h in _fan(run_full, paths)}
        if mode == "capture":
            with open(argv[1], "w") as fh:
                json.dump(results, fh, indent=0)
            print(f"captured {len(results)} manifests -> {argv[1]}")
            return 0
        with open(argv[1]) as fh:
            base = json.load(fh)
        bad = 0
        for key, rec in results.items():
            old = base.get(key)
            if old is None:
                print(f"NEW      {key} (not in baseline)")
                bad += 1
            elif old != rec:
                what = "verdicts" if old["fails"] != rec["fails"] else "stdout"
                print(f"DIFF     {key} ({what})")
                if old["fails"] != rec["fails"]:
                    print(f"  -{sorted(set(old['fails']) - set(rec['fails']))}\n  +{sorted(set(rec['fails']) - set(old['fails']))}")
                bad += 1
        missing = set(base) - set(results)
        for key in sorted(missing):
            print(f"MISSING  {key}")
        print(f"{'IDENTICAL on all' if not bad and not missing else 'DIFFS on'} {len(results) if not bad else bad} manifests")
        return 0 if not bad and not missing else 1
    if mode == "targeted":
        paths = [p for p, is_f in manifest_paths() if is_f][:limit]
        results = _fan(run_targeted, paths)
        mismatches = [(p, v) for p, v in results if v.startswith("MISMATCH")]
        fallbacks = sum(1 for _, v in results if v == "FALLBACK")
        for p, v in mismatches:
            print(f"{os.path.basename(p)}: {v}")
        print(f"{len(results)} fixtures: {len(results) - len(mismatches) - fallbacks} OK, {fallbacks} full-gate fallback, {len(mismatches)} MISMATCH")
        return 0 if not mismatches else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
