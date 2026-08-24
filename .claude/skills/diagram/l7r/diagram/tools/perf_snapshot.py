#!/usr/bin/env python3
"""Time the REFERENCE HAMLET across several seeds, and keep the results as a trend.

    python3 -m l7r.diagram.tools.perf_snapshot --record --label 126-start
    python3 -m l7r.diagram.tools.perf_snapshot --report
    python3 -m l7r.diagram.tools.perf_snapshot --report --against 126-start

WHY THIS EXISTS (GM, 2026-08-23): *"we often will end up degrading performance without even
realizing it"* - which had just happened. Feature 126 moved the lane skeleton after the houses and
took one seed from 65s to 160s; nothing noticed until a 48-map cohort stalled a 20-worker pool for
thirty minutes and was killed twice without producing a result.

WHAT IT MEASURES, AND WHY IT IS SEEDS RATHER THAN MAPS. The reference hamlet is Inashiro's spec -
15 households, fall 90, a pond sink - rolled across a fixed set of SEEDS. One map proves nothing
about performance: a seed can be pathologically good as easily as pathologically bad, and the same
generator that finishes Inashiro's own seed in 30s takes 160s on seed 25. Holding the spec fixed
and varying only the seed is what makes two snapshots comparable while still crossing the rolled
knobs (the settlement form, the cluster shape, the lane skeleton), so a change that is fast on the
form you were thinking about and slow on the other two cannot hide.

HOW IT RELATES TO `GEN_TIME_BUDGETS` (tests/test_villages.py), which it does NOT replace. That is a
CEILING on the pool's own gens, and it fires when a single map goes pathological. This is a TREND
across seeds, and it answers a different question: not "is any map broken" but "is the generator
getting slower, and since when". Keep both.

WHY A DIRECTORY OF FILES rather than one appended log (GM's design): several session clones change
this engine at once, and an append-only shared file conflicts on every concurrent push. One file per
snapshot, named for the feature and the clone that produced it, never conflicts - git merges
disjoint new files without help - and the filename itself reconstructs who changed what, when.

It is a by-hand tool (see `pyproject.toml`'s coverage `source` list, which names the measured tools
one by one), so it is not under the 100% rule.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if SKILL not in sys.path:
    sys.path.insert(0, SKILL)

LOG_DIR = os.path.join(SKILL, "dev", "perf-log")

# THE REFERENCE HAMLET. Inashiro's own spec, held fixed so snapshots stay comparable across months.
# Changing any of this invalidates the trend, so do not tune it to make a number look better - add a
# second reference instead, and say in its docstring what it is for.
REFERENCE = {"name": "Inashiro", "households": 15, "down_deg": 90, "water_sink": "pond"}

# FOUR SEEDS, CHOSEN TO SPREAD ACROSS THE ROLLED KNOBS rather than to be fast. Seed 4 is Inashiro's
# own; 25 and 47 were the two slowest seeds found when this tool was written (160s and 86s), and 39
# was among the fastest (34s). A set that contained only comfortable seeds would report health that
# the cohort does not have - which is the exact failure this tool exists to prevent.
DEFAULT_SEEDS = (4, 25, 39, 47)


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", "-C", SKILL, *args], capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:  # pragma: no cover - a snapshot must never fail the gate it rides on
        return ""


def _where() -> str:
    """Which TREE this snapshot was taken in - the clone name, or the worktree's own directory.

    Not just cosmetic. The first snapshot ever recorded was taken in a detached baseline worktree and
    this returned "main", which in a project where main is never a workspace is a claim that would
    mislead anyone reading the trend later. A worktree reports its own directory name instead, so
    `base125` reads as what it is."""
    if "/.clones/" in SKILL:
        return SKILL.split("/.clones/")[1].split("/")[0]
    top = _git("rev-parse", "--show-toplevel")
    return os.path.basename(top) if top else "unknown"


def measure(seeds: tuple[int, ...]) -> list[dict[str, object]]:
    """Roll the reference hamlet on each seed, timing every stage."""
    from l7r.diagram.hamletgen import HamletSpec, plan_site
    from l7r.diagram.hamletgen.driver import STAGES
    from l7r.diagram.settlement import Settlement

    rows: list[dict[str, object]] = []
    for seed in seeds:
        plan = plan_site(HamletSpec(seed=seed, **REFERENCE))  # type: ignore[arg-type]
        s = Settlement(W=plan.W, H=plan.H, seed=plan.spec.seed)
        s._avoid_seats = []  # type: ignore[attr-defined]
        stages: dict[str, float] = {}
        for st in STAGES:
            t0 = time.time()
            with redirect_stdout(io.StringIO()):
                st(s, plan)
            stages[st.__name__.replace("stage_", "")] = round(time.time() - t0, 2)
        rows.append(
            {
                "seed": seed,
                "seconds": round(sum(stages.values()), 1),
                "form": getattr(plan, "settlement_form", "n/a"),
                "shape": plan.cluster_shape,
                "houses": len(s.M.get("houses", [])),
                "asked": plan.spec.households,
                "stages": stages,
            }
        )
        print(f"  seed {seed:>3}  {rows[-1]['seconds']:>6.1f}s  {rows[-1]['form']:<10} houses={rows[-1]['houses']}/{plan.spec.households}", flush=True)
    return rows


def record(label: str, seeds: tuple[int, ...]) -> str:
    os.makedirs(LOG_DIR, exist_ok=True)
    print(f"reference hamlet ({REFERENCE['name']} spec) across seeds {list(seeds)}:", flush=True)
    rows = measure(seeds)
    totals = [float(r["seconds"]) for r in rows]  # type: ignore[arg-type]
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    clone = _where()
    snap = {
        "label": label,
        "utc": stamp,
        "clone": clone,
        "commit": _git("rev-parse", "--short", "HEAD"),
        "subject": _git("log", "-1", "--pretty=%s"),
        "cpus": os.cpu_count(),
        "machine": platform.machine(),
        "reference": REFERENCE,
        "seeds": list(seeds),
        "total_seconds": round(sum(totals), 1),
        "median_seconds": round(statistics.median(totals), 1),
        "worst_seconds": round(max(totals), 1),
        "rows": rows,
    }
    path = os.path.join(LOG_DIR, f"{stamp}-{label}-{clone}.json")
    with open(path, "w") as fh:
        json.dump(snap, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"\ntotal {snap['total_seconds']}s  median {snap['median_seconds']}s  worst {snap['worst_seconds']}s")
    print(f"wrote {os.path.relpath(path, SKILL)}")
    return path


def _load() -> list[dict[str, object]]:
    if not os.path.isdir(LOG_DIR):
        return []
    out = []
    for fn in sorted(os.listdir(LOG_DIR)):
        if fn.endswith(".json"):
            with open(os.path.join(LOG_DIR, fn)) as fh:
                out.append(json.load(fh))
    return out


def report(against: str | None) -> int:
    snaps = _load()
    if not snaps:
        print("no snapshots yet - run: make perf")
        return 0
    print(f"{'utc':<18}{'label':<18}{'commit':<10}{'total':>8}{'median':>8}{'worst':>8}")
    for s in snaps:
        print(f"{str(s['utc']):<18}{str(s['label'])[:17]:<18}{str(s['commit']):<10}{float(s['total_seconds']):>7.1f}s{float(s['median_seconds']):>7.1f}s{float(s['worst_seconds']):>7.1f}s")

    base = None
    if against:
        base = next((s for s in snaps if str(s["label"]) == against), None)
        if base is None:
            print(f"\nno snapshot labelled {against!r}")
            return 1
    elif len(snaps) >= 2:
        base = snaps[-2]
    if base is None or base is snaps[-1]:
        return 0

    cur = snaps[-1]
    print(f"\n{cur['label']} vs {base['label']}:")
    bad = 0
    by_seed = {int(r["seed"]): r for r in base["rows"]}  # type: ignore[index,call-overload]
    for r in cur["rows"]:  # type: ignore[union-attr]
        b = by_seed.get(int(r["seed"]))  # type: ignore[index,call-overload]
        if not b:
            continue
        was, now = float(b["seconds"]), float(r["seconds"])  # type: ignore[index,arg-type]
        pct = (now - was) / was * 100.0 if was else 0.0
        # 5% IS THE PROJECT'S OWN THRESHOLD for a whole-process speedup mattering; the same figure is
        # used here in the other direction, so a slowdown is called out at the size a speedup counts.
        flag = "  <-- SLOWER" if pct > 5.0 else ("  faster" if pct < -5.0 else "")
        bad += 1 if pct > 5.0 else 0
        print(f"  seed {int(r['seed']):>3}  {was:>6.1f}s -> {now:>6.1f}s  {pct:+6.1f}%{flag}")  # type: ignore[index,call-overload]
    if bad:
        print(f"\n{bad} seed(s) more than 5% slower - diagnose before shipping (constitution VI).")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--record", action="store_true", help="time the reference hamlet and write a snapshot")
    ap.add_argument("--report", action="store_true", help="print the trend, and the latest against a baseline")
    ap.add_argument("--label", default="adhoc", help="what this snapshot is, e.g. 126-start / 126-end")
    ap.add_argument("--against", default=None, help="label of the snapshot to compare the latest against")
    ap.add_argument("--seeds", default=None, help="comma-separated seeds (default: the reference set)")
    a = ap.parse_args(argv)
    seeds = tuple(int(x) for x in a.seeds.split(",")) if a.seeds else DEFAULT_SEEDS
    if a.record:
        record(a.label, seeds)
    if a.report or not a.record:
        return report(a.against)
    return 0


if __name__ == "__main__":
    from l7r.diagram._invocation import guard

    # REFUSE unless invoked through this project's make (feature 127). At the TOP of the
    # entry point, never in a loop - the determination reads /proc and is cached per process.
    guard("l7r.diagram.tools.perf_snapshot")
    raise SystemExit(main())
