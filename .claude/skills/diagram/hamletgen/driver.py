"""The pipeline itself: STAGES, and everything that drives it.

Split from hamletgen.py by feature 111; bodies verbatim. See hamletgen/CLAUDE.md.
"""

from __future__ import annotations

import argparse
import os
from collections.abc import Sequence
from dataclasses import dataclass

from settlement import Settlement

from .consts import REF_HOUSEHOLDS
from .frame import stage_crossings, stage_frame, stage_notice
from .hinterland import stage_hinterland, stage_windbreak, stage_woodland
from .homesteads import stage_appurtenances, stage_homesteads
from .plan import HamletSpec, SitePlan, plan_site
from .sink import stage_sink
from .water import stage_field, stage_water_frame
from .ways import stage_ways

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

    from check_village import gate

    plan = plan_site(spec)
    s = build(plan)
    if out_base is not None:
        s.finish(out_base, render=render)
    else:
        with tempfile.TemporaryDirectory() as tmp:
            s.finish(os.path.join(tmp, "scratch"), render=False)
    return Report(plan=plan, failures=sorted(gate(s.M)), path=out_base)


def cohort(count: int, first_seed: int = 1, households: int | None = None) -> list[Report]:
    """Roll `count` hamlets from consecutive seeds and gate every one.

    This is the experiment's actual evidence. A generator that produces ONE good map has shown that
    a person can drive it to a good map; a generator that produces a cohort of correct maps from
    seeds nobody looked at has shown that the SCRIPT is doing the work."""
    out = []
    for i in range(count):
        seed = first_seed + i
        hh = households if households is not None else 10 + (seed * 7) % 11
        out.append(generate(HamletSpec(name=f"Cohort-{seed:02d}", seed=seed, households=hh), out_base=None))
    return out


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
    args = ap.parse_args(list(argv) if argv is not None else None)

    if args.batch:
        reports = cohort(args.batch, first_seed=args.seed)
        for r in reports:
            print(r.line())
        good = sum(1 for r in reports if r.ok)
        print(f"\n{good}/{len(reports)} passed the full gate")
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
