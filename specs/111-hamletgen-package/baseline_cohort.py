#!/usr/bin/env python3
"""Write the fixed-seed cohort's manifests, which `hamletgen.cohort()` itself discards.

WHY THIS EXISTS. Feature 111's oracle is byte-identical manifests (spec FR-004), and the four live
hamlets only exercise four seeds. `hamletgen.cohort()` rolls N seeds and gates every one, but it
passes `out_base=None`, so each roll finishes into a temp dir and is thrown away - the report line
survives, the manifest does not. This script re-runs the SAME rolls with an `out_base`, so the
cohort's geometry can be diffed and not just its pass/fail verdict.

It deliberately duplicates `cohort()`'s seed/household formula rather than importing it, because
importing the loop would mean not writing the files. Keep the two in sync: if `cohort()`'s formula
changes, this is a verification artifact of a feature that predates the change - re-capture the
baseline rather than editing this.

Run it from inside the tree being measured (a scratch copy per quickstart.md), not from the clone:

    python3 <spec>/baseline_cohort.py --out /path/to/cohort [--count 24] [--first-seed 1]
"""

from __future__ import annotations

import argparse
import os
import sys


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", required=True, help="directory to write cohort-NN.json/.svg into")
    ap.add_argument("--count", type=int, default=24)
    ap.add_argument("--first-seed", type=int, default=1)
    ap.add_argument("--tree", default=os.getcwd(), help="the diagram-skill tree to import hamletgen from (default: cwd)")
    args = ap.parse_args(argv)

    sys.path.insert(0, os.path.abspath(args.tree))
    import hamletgen as hg

    os.makedirs(args.out, exist_ok=True)
    failures = 0
    for i in range(args.count):
        seed = args.first_seed + i
        # mirrors hamletgen.cohort() exactly - see the module docstring
        households = 10 + (seed * 7) % 11
        spec = hg.HamletSpec(name=f"Cohort-{seed:02d}", seed=seed, households=households)
        report = hg.generate(spec, out_base=os.path.join(args.out, f"cohort-{seed:02d}"), render=False)
        print(report.line())
        failures += 0 if report.ok else 1

    print(f"\n{args.count - failures}/{args.count} passed the full gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
