#!/usr/bin/env python3
"""Regenerate and check the pool maps, choosing its own scope from how the LAST run went.

    python3 -m l7r.diagram.tools.mapcheck                  # decide for me (the normal call)
    python3 -m l7r.diagram.tools.mapcheck --scope reference # force the cheap one
    python3 -m l7r.diagram.tools.mapcheck --scope all       # force the whole tier
    python3 -m l7r.diagram.tools.mapcheck --tier hamlets    # (default: every tier with live gens)

WHY THIS EXISTS (GM, 2026-08-23). The rule it replaces was "prove it on the reference settlement
first, then sweep", and the rule was correct and did not work - it was written into the constitution
and violated by its own author six hours later, at a cost of five 10-12 minute four-map cycles
chasing a defect the reference hamlet answered in 67 seconds. *"Just remembering to do the right
thing always is much worse than having good tooling."* So the choice is not offered any more.

THE STATE MACHINE, which is the whole idea:

    previous run PASSED  ->  run the WHOLE tier, and report EVERY failure together
    previous run FAILED  ->  run the REFERENCE map alone and STOP if it fails;
                             only if it passes, go on to the rest
    no previous run      ->  treat as FAILED

One piece of state drives both the scope and the verbosity, and it drives them the same way for the
same reason. A failed previous run means you are mid-fix and want the fastest possible signal, so the
run is narrow and stops at the first problem. A passed previous run means you are verifying breadth,
so it is wide and collects everything - which is exactly what `make done` already does and says
("reports ALL failures together - fix everything it lists, then re-run once").

WHY UNKNOWN COUNTS AS FAILED: a fresh clone or a new session is when you are LEAST sure of the tree,
and the insurance costs one reference map. Guessing optimistically there is how a session starts its
day with a ten-minute sweep it did not need.

WHY THE OVERRIDE EXISTS: `--scope` says what you mean when you know better. An adaptive default is
right; removing the ability to be explicit is not, because a tool that cannot be told the truth gets
worked around instead of used.

IT IS PER-TIER BY CONSTRUCTION, not hardcoded to hamlets: villages, towns and cities are coming, and
a tier table costs the same today and saves a rewrite later. Add a tier by adding a row to `TIERS`.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if SKILL not in sys.path:
    sys.path.insert(0, SKILL)

STATE = os.path.join(SKILL, ".mapcheck.json")

# THE REFERENCE MAP OF EACH TIER - the one a fix is proven on before anything else runs.
# Inashiro because it is the tier's canonical hamlet (constitution VI); when a tier gains live
# scripted maps, give it a row here and pick the reference deliberately rather than alphabetically.
TIERS: dict[str, str] = {"hamlets": "inashiro"}


def _live_gens(tier: str) -> list[str]:
    """Every gen in the tier that is not frozen, reference first."""
    from l7r.diagram.pipeline.poolmaps import LEGACY_FROZEN_GENS

    d = os.path.join(SKILL, "pool", tier)
    if not os.path.isdir(d):
        return []
    gens = sorted(f for f in os.listdir(d) if f.endswith(".gen.py") and f not in LEGACY_FROZEN_GENS)
    ref = f"{TIERS.get(tier, '')}.gen.py"
    gens.sort(key=lambda f: (f != ref, f))  # reference first, so a narrow run is a prefix of a wide one
    return [os.path.join("pool", tier, f) for f in gens]


def _load() -> dict[str, object]:
    try:
        with open(STATE) as fh:
            return dict(json.load(fh))
    except Exception:
        return {}


def _save(ok: bool, scope: str, failed: list[str]) -> None:
    with open(STATE, "w") as fh:
        json.dump({"ok": ok, "scope": scope, "failed": failed, "utc": time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())}, fh, indent=2)
        fh.write("\n")


def _run(gens: list[str], stop_early: bool) -> tuple[bool, list[str]]:
    """Regenerate these gens; return (all_ok, names that failed).

    Runs one gen at a time when stopping early, so 'stop at the first problem' actually stops before
    paying for the rest - which is the entire point of the narrow mode."""
    failed: list[str] = []
    batches = [[g] for g in gens] if stop_early else [gens]
    for batch in batches:
        proc = subprocess.run([sys.executable, "-m", "l7r.diagram.pipeline.regen", *batch], cwd=SKILL, capture_output=True, text=True)
        out = proc.stdout + proc.stderr
        print(out.rstrip())
        for line in out.splitlines():
            if "FAIL" in line:
                name = line.split()[0].strip()
                if name and name not in failed:
                    failed.append(name)
        if proc.returncode != 0 and not failed:
            failed.append(os.path.basename(batch[0]))
        if failed and stop_early:
            break
    return (not failed), failed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scope", choices=("auto", "reference", "all"), default=os.environ.get("SCOPE", "auto"))
    ap.add_argument("--tier", default=None, help="one tier (default: every tier with live gens)")
    a = ap.parse_args(argv)

    tiers = [a.tier] if a.tier else list(TIERS)
    prev = _load()
    prev_ok = bool(prev.get("ok"))
    recovering = a.scope == "reference" or (a.scope == "auto" and not prev_ok)

    if a.scope == "auto":
        why = "last run PASSED" if prev_ok else ("no previous run" if not prev else f"last run FAILED on {prev.get('failed')}")
        print(f"\033[1mmapcheck\033[0m: {why} -> {'reference map first, stopping at the first problem' if recovering else 'whole tier, reporting every failure'}\n")

    all_failed: list[str] = []
    for tier in tiers:
        gens = _live_gens(tier)
        if not gens:
            continue
        ref = gens[:1] if recovering or a.scope == "reference" else gens
        ok, failed = _run(ref, stop_early=recovering)
        all_failed += failed
        if not ok:
            break
        # THE REFERENCE MAP PASSED, SO EARN THE REST. This is the sequential cost the GM priced and
        # accepted: a reference run that passes costs ~1 min before the wide one starts, and a
        # reference run that FAILS saves the wide one entirely.
        if a.scope != "reference" and recovering and len(gens) > 1:
            print("\n\033[1mreference map is clean\033[0m - going on to the rest of the tier\n")
            ok2, failed2 = _run(gens[1:], stop_early=False)
            all_failed += failed2
            if not ok2:
                break

    ok = not all_failed
    _save(ok, "reference" if recovering and a.scope == "reference" else "all", all_failed)
    print("\n\033[1mmaps clean\033[0m" if ok else f"\n\033[1mmaps FAILED\033[0m: {', '.join(all_failed)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
