"""The pipeline itself: STAGES, and everything that drives it.

Split from hamletgen.py by feature 111; bodies verbatim. See hamletgen/CLAUDE.md.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import os
from collections.abc import Sequence
from dataclasses import dataclass

from l7r.diagram.settlement import Settlement
from l7r.diagram.sitegen.jobs import default_jobs as default_jobs  # noqa: PLC0414 - explicit re-export so `hamletgen.default_jobs` still resolves under --strict

from .consts import REF_HOUSEHOLDS
from .frame import stage_crossings, stage_frame, stage_notice
from .hinterland import stage_hinterland, stage_windbreak, stage_woodland
from .homesteads import stage_appurtenances, stage_homesteads
from .plan import HamletSpec, SitePlan, plan_site
from .sink import stage_sink
from .water import stage_field, stage_water_frame
from .ways import stage_ways, stage_web

# THE PIPELINE. Read top to bottom: this is the generator.
#
# THE ORDER IS THE DESIGN, and this tuple is where it lives (feature 111). Water first, then the
# field the water shapes, then the sink the field drains to, then the ways, then the homesteads
# that front the ways, then their appurtenances, then ground cover, then the woods, then the
# frame. It is the same order a human follows and the same order the skill's DRAW ORDER map
# requires (.claude/skills/diagram/CLAUDE.md) - so a change here is a change to that map, and the
# two must move together.
#
# It stays a LITERAL tuple, deliberately, rather than being derived by scanning the submodules for
# `stage_*` functions. Constitution clause 14 says derive a registry that merely restates what the
# code already declares; this one does not - the SEQUENCE is a decision no amount of introspection
# could recover, which is exactly the ordered-data case the clause carves out. Adding a stage means
# deciding where in this list it goes.
STAGES = (
    stage_water_frame,
    stage_field,
    stage_sink,
    stage_ways,
    stage_homesteads,
    stage_web,
    stage_appurtenances,
    stage_notice,
    stage_hinterland,
    stage_woodland,
    stage_windbreak,
    stage_crossings,
    stage_frame,
)


# ---- driving it ---------------------------------------------------------------------------------


@dataclass
class Report:
    """What one generated hamlet came out as - the row of the cohort table."""

    plan: SitePlan
    failures: list[str]
    path: str | None = None

    @property
    def ok(self) -> bool:
        return not self.failures

    def line(self) -> str:
        p = self.plan
        return (
            f"{p.spec.name:<18} seed={p.spec.seed:<4} hh={p.placed}/{p.spec.households:<3} "
            f"acres={p.acres:5.1f}/{p.target_acres:5.1f} fall={int(p.down_deg):<4} wind={p.windward:<3} "
            f"sink={p.water_sink:<7} {p.cluster_shape[:9]:<10} {p.lane_skeleton:<6} "
            f"{'OK' if self.ok else 'FAIL: ' + ', '.join(self.failures[:4])}"
        )


def build(plan: SitePlan) -> Settlement:
    """Run every stage, in order, against a fresh `Settlement`."""
    s = Settlement(W=plan.W, H=plan.H, seed=plan.spec.seed)
    for stage in STAGES:
        stage(s, plan)
    return s


def generate(spec: HamletSpec, out_base: str | None = None, render: bool = True) -> Report:
    """Build a hamlet, FINISH it, gate it, and report. Writes svg/png/json when `out_base` is given.

    THE MANIFEST IS NOT COMPLETE UNTIL `finish()` RUNS, and that cost an hour of chasing a phantom
    defect. `finish` is not just "write the file": it flushes the deferred tree canopies, seats the
    deferred captions, and splices the shared water block - which is where a pond's fill records the
    draw position `pond_fill_covers_channel_mouths` reads. Gating the in-memory manifest before that
    reported a broken pond on every map with a pond, and the maps were fine. So the finish always
    runs; a cohort member with nowhere to go finishes into a scratch directory and is thrown away.

    The gate then runs IN-PROCESS on that finished manifest, which is what makes it cheap to roll a
    dozen hamlets and ask how many of them are actually correct."""
    import tempfile

    from l7r.diagram.check_village import gate

    plan = plan_site(spec)
    s = build(plan)
    if out_base is not None:
        s.finish(out_base, render=render)
    else:
        with tempfile.TemporaryDirectory() as tmp:
            s.finish(os.path.join(tmp, "scratch"), render=False)
    return Report(plan=plan, failures=sorted(gate(s.M)), path=out_base)


def cohort(count: int, first_seed: int = 1, households: int | None = None, jobs: int | None = None) -> list[Report]:
    """Roll `count` hamlets from consecutive seeds and gate every one.

    This is the experiment's actual evidence. A generator that produces ONE good map has shown that
    a person can drive it to a good map; a generator that produces a cohort of correct maps from
    seeds nobody looked at has shown that the SCRIPT is doing the work.

    THE ROLLS FAN OUT ACROSS PROCESSES (2026-08-16), because a cohort is the verification step of
    every placement-rule change and it was the single biggest sink in the one measured: the fan-toe
    pond fix spent 17.3 min of its 45.7 on two SERIAL 24-seed rolls, ~11 min of that as critical-path
    idle - 20% of the whole task, for work that is embarrassingly parallel. `regen.py` and
    `cohort_audit.py` were given the same fan-out in the 2026-08-15 timings round and this CLI was
    simply missed. Safe by the same argument they use: a map is a pure function of its spec (the
    seed fixes every draw - see "RANDOMNESS IS POSITIONAL OR SCOPED" in the skill's CLAUDE.md), so
    parallelism can only change the wall clock, never a verdict. `generate` IS the worker - it takes
    one spec, defaults `out_base` to None, and is picklable - so there is no wrapper to keep honest.
    Results come back in seed order, so a fanned-out run reads exactly like a serial one.

    `jobs=1` forces the serial path, which is what the in-gate callers want: a pytest worker that
    spawns its own pool is competing with the other 21 (the "CPU inflates 2-4x inside the gate"
    entry in the skill CLAUDE.md)."""
    specs = [
        HamletSpec(
            name=f"Cohort-{first_seed + i:02d}",
            seed=first_seed + i,
            households=households if households is not None else 10 + ((first_seed + i) * 7) % 11,
        )
        for i in range(count)
    ]
    jobs = default_jobs(count) if jobs is None else max(1, jobs)
    if jobs == 1:
        return [generate(spec, out_base=None) for spec in specs]
    with concurrent.futures.ProcessPoolExecutor(max_workers=jobs) as ex:
        return list(ex.map(generate, specs))


# THE FITTED COHORT'S KNOWN FAILURES, pinned. Constitution Principle XIII requires a regression to
# be judged against a MEASURED baseline - and until 2026-08-17 no such baseline existed anywhere in
# the tree, so every session either re-measured it by hand (a detached worktree and a full 24-map
# roll, minutes each time) or carried "22 of 24, seeds 22 and 24" in its head. Worse, the summary
# line reads `22/24 passed` whether the two failures are the expected ones or two brand-new ones, so
# a real regression and the steady state are INDISTINGUISHABLE at a glance. That is the exact shape
# the principle exists to stop, left unenforced in the principle's own test bed.
#
# Keyed by seed, valued by the BASE check names (the `[instance]` suffix varies with the map's own
# feature ids and is not part of the identity). Keep this pinned to the FITTED cohort only - the
# held-out range is measured, never tuned, so pinning it would defeat its purpose.
COHORT_BASELINE: dict[int, frozenset[str]] = {
    22: frozenset({"field_ringed"}),
    24: frozenset({"paddy_bunds_clear_the_supply_channels"}),
}
COHORT_BASELINE_SIZE = 24  # the pin describes exactly `--batch 24` from seed 1


def baseline_verdict(reports: Sequence[Report], pin: dict[int, frozenset[str]] | None = None) -> tuple[list[str], bool]:
    """Judge a canonical cohort against `COHORT_BASELINE`: `(lines to print, is_clean)`.

    `pin` is injectable so the LOGIC can be tested without pinning the tests to today's baseline -
    otherwise every honest cohort improvement would break this function's own tests, which is how a
    guard ends up loosened to keep the suite quiet.

    Two ways to be dirty, and BOTH are failures, for the same reason `waivers_are_live` fails on a
    waiver whose defect was fixed: a baseline nobody maintains stops being a baseline.

    - A NEW failure (a seed or a check the pin does not cover) is a regression. Blocking.
    - A pinned failure that now PASSES means the pin is stale and is quietly excusing a seed that no
      longer needs it. Blocking too, with the edit to make - otherwise the pin only ever loosens,
      and the next real regression on that seed is invisible."""
    base = COHORT_BASELINE if pin is None else pin
    actual = {r.plan.spec.seed: {f.split("[")[0] for f in r.failures} for r in reports if r.failures}
    new = {seed: sorted(checks - base.get(seed, frozenset())) for seed, checks in actual.items()}
    new = {seed: checks for seed, checks in new.items() if checks}
    gone = {seed: sorted(expected - actual.get(seed, set())) for seed, expected in base.items()}
    gone = {seed: checks for seed, checks in gone.items() if checks}
    if not new and not gone:
        return [f"cohort matches the pinned baseline ({len(base)} expected failures) - NO NEW REGRESSIONS"], True
    lines: list[str] = []
    for seed, checks in sorted(new.items()):
        lines.append(f"REGRESSION seed {seed}: {', '.join(checks)} - not in the pinned baseline")
    for seed, checks in sorted(gone.items()):
        lines.append(f"STALE PIN seed {seed}: {', '.join(checks)} now PASSES - remove it from COHORT_BASELINE in hamletgen/driver.py")
    if new:
        lines.append("A new cohort failure BLOCKS the merge (constitution Principle XIII): fix it, revert, or get an explicit GM waiver.")
    return lines, False


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate a Rokugani rice hamlet from a seed, and gate it.")
    ap.add_argument("--name", default="Hamlet")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--households", type=int, default=REF_HOUSEHOLDS)
    ap.add_argument("--down-deg", type=float, default=None)
    ap.add_argument("--sink", choices=("pond", "offmap"), default=None)
    ap.add_argument("--windward", default=None)
    ap.add_argument("--out", default=None, help="write <out>.svg/.png/.json")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--batch", type=int, default=0, help="roll N hamlets from consecutive seeds and gate them all")
    ap.add_argument("--jobs", type=int, default=None, help="worker processes for --batch (default: cpus - 2, capped at the cohort size; 1 for serial)")
    args = ap.parse_args(list(argv) if argv is not None else None)

    if args.batch:
        reports = cohort(args.batch, first_seed=args.seed, jobs=args.jobs)
        for r in reports:
            print(r.line())
        good = sum(1 for r in reports if r.ok)
        print(f"\n{good}/{len(reports)} passed the full gate")
        # The RATE is not the verdict - the failing SET is. `22/24` reads identically whether the
        # two are the pinned pre-existing ones or two fresh regressions, which is why the pin exists.
        if args.seed == 1 and args.batch == COHORT_BASELINE_SIZE:
            lines, clean = baseline_verdict(reports)
            for line in lines:
                print(line)
            return 0 if clean else 1
        print(f"(no pinned baseline for this range - it describes --batch {COHORT_BASELINE_SIZE} from seed 1)")
        return 0 if good == len(reports) else 1

    report = generate(
        HamletSpec(name=args.name, seed=args.seed, households=args.households, down_deg=args.down_deg, water_sink=args.sink, windward=args.windward),
        out_base=args.out,
        render=not args.no_render,
    )
    print(report.line())
    for f in report.failures:
        print("  FAIL", f)
    return 0 if report.ok else 1
