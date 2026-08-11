#!/usr/bin/env python3
"""Roll a cohort of scripted hamlets, gate every one, and report WHY each failure happened.

`hamletgen.py --batch N` answers "how many pass". This answers the next question - "what exactly is
colliding with what" - which is the one you need to fix them. For every failing map it prints the
check's own message (not a re-derivation of it) plus, for the overlap checks, the manifest keys and
coordinates of the offending pair, so a fix can be aimed rather than guessed at.

WHY THIS EXISTS RATHER THAN A GREP OVER THE GATE OUTPUT: the gate prints one line per check across
~185 checks per map, so a twelve-map cohort is ~2,200 lines of PASS to read a dozen FAILs out of.
And a diagnostic that re-implements a check drifts from it (the skill's dev notes have three
incidents on record), so this one only ever quotes what the gate said.

    python3 cohort_audit.py                 # 12 hamlets from seed 1
    python3 cohort_audit.py --count 24 --seed 1
    python3 cohort_audit.py --only features_do_not_overlap   # just the maps failing one check
"""

from __future__ import annotations

import argparse
import collections
import contextlib
import io
import os
import sys
from collections.abc import Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:  # pragma: no cover - a script, run from anywhere
    sys.path.insert(0, HERE)

import hamletgen as hg  # noqa: E402


def audit(count: int, first_seed: int, only: str | None = None) -> int:
    """Roll `count` hamlets, gate each, and print the failures with the gate's own messages."""
    import tempfile

    from check_village import gate

    tally: collections.Counter[str] = collections.Counter()
    failing = 0
    for i in range(count):
        seed = first_seed + i
        households = 10 + (seed * 7) % 11
        plan = hg.plan_site(hg.HamletSpec(name=f"Audit-{seed:02d}", seed=seed, households=households))
        settlement = hg.build(plan)
        with tempfile.TemporaryDirectory() as tmp:
            settlement.finish(os.path.join(tmp, "scratch"), render=False)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            failures = sorted(gate(settlement.M))
        if only:
            failures = [f for f in failures if f.startswith(only)]
        if not failures:
            continue
        failing += 1
        tally.update(f.split("[")[0] for f in failures)
        print(f"\n--- Audit-{seed:02d}  seed={seed} households={households} fall={int(plan.down_deg)} sink={plan.water_sink} shape={plan.cluster_shape} lanes={plan.lane_skeleton}")
        for line in buf.getvalue().splitlines():
            if line.startswith("FAIL") and (not only or only in line):
                print("   ", line.strip()[:400])
    print(f"\n{count - failing}/{count} passed the whole gate")
    if tally:
        print("residue by check:")
        for name, n in tally.most_common():
            print(f"  {n:3d}  {name}")
    return 0 if failing == 0 else 1


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--count", type=int, default=12)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--only", default=None, help="report only failures of this check")
    args = ap.parse_args(list(argv) if argv is not None else None)
    return audit(args.count, args.seed, args.only)


if __name__ == "__main__":
    raise SystemExit(main())
