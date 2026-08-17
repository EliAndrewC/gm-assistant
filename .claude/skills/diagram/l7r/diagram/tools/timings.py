"""Measure the /diagram iteration loops - TOTAL AND BREAKDOWN - and append a dated block to `timings.md`.

WHY THIS IS A SCRIPT AND NOT A PARAGRAPH. Iteration cost is the project's main stumbling block: the
difference between a 15-second loop and a 4-minute one decides whether a session iterates or
guesses, and guess-and-check is what turns a simple request into a multi-hour slog. So the numbers
are tracked, not recalled. Hand-measured numbers written into prose rot silently and in one
direction - on 2026-08-15 the skill's CLAUDE.md still said the full sweep was "~2 to 2.5 minutes"
when it had grown past four. Nobody was wrong; nobody re-measured.

WHY EVERY BENCHMARK IS BROKEN DOWN (GM, 2026-08-15). A total tells you a loop is slow; it does not
tell you what to do about it. This is an Amdahl's-law problem: optimizing a phase that is 5% of the
wall clock cannot help no matter how well it is done, and the only way to know which phase dominates
is to record the parts alongside the whole. The breakdown here is deliberately COARSE - phases, not
functions. Function-level profiling is the right tool once a phase is identified as the target, and
the wrong tool for a standing record that has to stay cheap enough to actually re-run.

    python3 -m l7r.diagram.tools.timings            # everything (~12 min)
    python3 -m l7r.diagram.tools.timings --quick    # the inner loops only (~1 min)
    python3 -m l7r.diagram.tools.timings --dry-run  # list what would run

Run it after performance work, after adding a tier or archetype, and whenever a loop feels slow. It
APPENDS - never rewrite or prune old blocks, since the trend is the product.

NOT UNDER THE COVERAGE GATE, following `cohort_audit.py`'s precedent: this module's whole behavior is
shelling out to the gate and reading a wall clock, so a unit test could only assert that a mock was
called. It IS under mypy --strict, per the pyproject policy that new modules start strict.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parents[3]  # the skill root; this module lives in l7r/diagram/tools/ - FOUR levels up since feature 119, not two
LEDGER = HERE / "timings.md"
PY = sys.executable


@dataclass
class Result:
    """One measured loop: its wall clock, and where that time went.

    `parts` sums to roughly `total` - not exactly, since some parts are measured by difference and
    some parents carry setup the parts do not. `note` says so where it matters."""

    key: str
    what: str
    total: float
    parts: list[tuple[str, float]] = field(default_factory=list)
    ok: bool = True
    note: str = ""
    # Percentage shares only mean something when the parts are SEQUENTIAL COMPONENTS of the total.
    # For a parallel sweep the parts overlap (they summed to >300% of wall clock in the first block),
    # and for an average or a cache-hit row the part is not a component at all.
    shares: bool = True


def sh(cmd: list[str], env: dict[str, str] | None = None) -> tuple[float, bool, str]:
    """Wall-clock a command. Returns (seconds, ok, combined output)."""
    start = time.monotonic()
    proc = subprocess.run(cmd, cwd=HERE, env={**os.environ, **(env or {})}, capture_output=True, text=True)
    return time.monotonic() - start, proc.returncode == 0, (proc.stdout or "") + (proc.stderr or "")


NO_RENDER = {"DIAGRAM_SKIP_RENDER": "1"}


def bench_hamlet(outdir: str) -> Result:
    """The inner loop, split into the three things it actually does.

    Measured by difference because the generator gates its own output and there is no flag to stop
    it - which is correct for the generator (an ungated map is not a result) and merely inconvenient
    here. RENDER is the difference between a run with and without the PNG; GATE is `check_village`
    run alone on the manifest that run produced; GENERATE is what is left."""
    out = str(Path(outdir) / "bench")
    argv = [PY, "hamletgen.py", "--name", "Bench", "--seed", "5", "--households", "14", "--out", out]
    with_png, ok_a, _ = sh(argv)
    without_png, ok_b, _ = sh(argv, NO_RENDER)
    gate, ok_c, _ = sh([PY, "-m", "l7r.diagram.check_village", out + ".json"])  # a package since 024, not a file
    return Result(
        "hamlet_gen_gate",
        "scripted hamlet: one map, generated + gated + rendered (THE inner loop)",
        with_png,
        [
            ("generate (compose + draw)", max(without_png - gate, 0.0)),
            ("gate (check_village, 189 checks)", gate),
            ("render PNG (resvg)", max(with_png - without_png, 0.0)),
        ],
        ok_a and ok_b and ok_c,
    )


def bench_cohort(count: int, quick: bool) -> Result:
    """A cohort of N hamlets. The per-map figure is the one to watch: it is the inner loop times the
    bar an archetype has to clear, and it sets what a conversion costs to verify."""
    secs, ok, _ = sh([PY, "-m", "l7r.diagram.tools.cohort_audit", "--count", str(count), "--seed", "1"])
    return Result(
        f"cohort_{count}",
        f"cohort of {count} hamlets" + (" (does a fix generalize?)" if quick else " (the bar for an archetype)"),
        secs,
        [("per map", secs / count)],
        ok,
        note="parts do not sum to the total: `per map` is the average, not a component",
        shares=False,
    )


def bench_cache(outdir: str) -> Result:
    """The gen cache, measured honestly: the second regen is the one that can hit.

    A cold regen is FORCED first (`--no-cache`) or this measures whatever the cache happened to
    hold and reports it as the cache's speed. The subject moved from frozen Minami to Sawada at
    the 2026-08-16 legacy freeze - a frozen map just prints FROZEN in 0.1 s, which the first
    post-freeze ledger block duly recorded as the finding."""
    cold, ok_a, _ = sh([PY, "-m", "l7r.diagram.pipeline.regen", "--no-cache", "pool/hamlets/sawada.gen.py"], NO_RENDER)
    warm, ok_b, out = sh([PY, "-m", "l7r.diagram.pipeline.regen", "pool/hamlets/sawada.gen.py"], NO_RENDER)
    hit = "CACHED" in out
    return Result(
        "map_regen_sawada",
        "heaviest LIVE scripted map through `regen.py`",
        cold,
        [("cold (cache miss: compose + draw + gate)", cold), ("warm (cache hit)" if hit else "warm (STILL A MISS)", warm)],
        ok_a and ok_b,
        shares=False,
        note="the total is the COLD run; the warm row is what the cache buys" + ("" if hit else " - and it did NOT hit, which is itself the finding"),
    )


def bench_pool_sweep() -> Result:
    """Every hand-authored map regenerated and gated - the byte-identity proof after an engine change.

    Broken down by the slowest maps, via pytest's own durations, because the sweep is dominated by a
    handful of heavy city maps rather than spread evenly over the 23."""
    secs, ok, out = sh([PY, "-m", "pytest", "tests/test_villages.py", "-q", "-n", "auto", "--no-cov", "--durations=8"], GATE_COLD)
    parts: list[tuple[str, float]] = []
    for line in out.splitlines():
        m = re.match(r"\s*([\d.]+)s\s+call\s+.*::(\S+)", line)
        if m:
            parts.append((m.group(2)[:52], float(m.group(1))))
    return Result(
        "pool_sweep",
        "regenerate + gate every LIVE scripted map, parallel workers (GATE_NO_CACHE=1: cold)",
        secs,
        parts[:8],
        ok,
        note="parts are the 8 slowest tests' own CPU time; they overlap in wall clock because the sweep runs parallel",
        shares=False,
    )


GATE_COLD = {"GATE_NO_CACHE": "1"}  # the gate-cache bypass (026): every live map regenerates


def bench_gate(bypass: bool = True) -> Result:
    """`make done`, phase by phase.

    The phases are timed individually rather than by running `make done` - the target is just a loop
    over these four, so the sum IS the gate, and measuring this way costs one gate instead of two.

    With `bypass` (the default, keyed `full_gate`) the sweep regenerates every live map under
    GATE_NO_CACHE=1 - the COLD measurement, comparable with every pre-026 ledger row. `warm_gate`
    is the same run immediately after, when the cold run has just stored every entry, so the pair
    measures exactly what the cache-backed gate (feature 026) buys."""
    parts: list[tuple[str, float]] = []
    ok = True
    for phase, label in (
        ("lint", "lint (ruff check + duplicate-def scan)"),
        ("format", "format (ruff format --check)"),
        ("typecheck", "typecheck (mypy --strict, 9 modules)"),
        ("test", "test (pytest -n auto + 100% coverage gate)"),
    ):
        secs, phase_ok, _ = sh(["make", phase], GATE_COLD if bypass else None)
        parts.append((label, secs))
        ok = ok and phase_ok
    if bypass:
        return Result("full_gate", "`make done` - the whole gate (GATE_NO_CACHE=1: cold, comparable with pre-026 rows)", sum(p[1] for p in parts), parts, ok)
    return Result("warm_gate", "`make done` again, warm gen cache - what feature 026 buys", sum(p[1] for p in parts), parts, ok)


def context() -> dict[str, str]:
    """What the numbers depend on. A container rebuild moves these, and the timings with them."""

    def first_line(cmd: list[str]) -> str:
        try:
            return subprocess.run(cmd, capture_output=True, text=True, cwd=HERE, timeout=30).stdout.strip().splitlines()[0]
        except OSError, subprocess.SubprocessError, IndexError:
            return "?"

    tests = "?"
    try:
        out = subprocess.run([PY, "-m", "pytest", "--collect-only", "-q"], capture_output=True, text=True, cwd=HERE, timeout=300).stdout
        m = re.search(r"(\d+) tests? collected", out)
        tests = m.group(1) if m else "?"
    except OSError, subprocess.SubprocessError:
        pass
    return {
        "cpus": str(os.cpu_count() or "?"),
        "python": sys.version.split()[0],
        "resvg": first_line(["resvg", "--version"]),
        "commit": first_line(["git", "rev-parse", "--short", "HEAD"]),
        "tests": tests,
        "maps": str(len(list((HERE / "pool").glob("*/*.gen.py")))),
    }


def fmt(seconds: float) -> str:
    return f"{seconds:.1f} s" if seconds < 90 else f"{int(seconds // 60)} min {seconds % 60:04.1f} s"


def render_block(results: list[Result], ctx: dict[str, str], note: str) -> str:
    lines = [
        "",
        f"### {date.today().isoformat()}",
        "",
        f"*{ctx['cpus']} cpus, python {ctx['python']}, resvg {ctx['resvg']}, at commit `{ctx['commit']}` - {ctx['maps']} pool gen scripts, {ctx['tests']} tests.*" + (f" {note}" if note else ""),
        "",
        "| loop / part | what | wall clock | share |",
        "|---|---|---|---|",
    ]
    for r in results:
        flag = "" if r.ok else " **(FAILED - number is not trustworthy)**"
        lines.append(f"| **`{r.key}`** | {r.what} | **{fmt(r.total)}** |{flag} |")
        for label, secs in r.parts:
            share = f"{100 * secs / r.total:.0f}%" if (r.shares and r.total > 0) else "-"
            lines.append(f"| &nbsp;&nbsp;↳ {label} | | {fmt(secs)} | {share} |")
        if r.note:
            lines.append(f"| &nbsp;&nbsp;*{r.note}* | | | |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Measure the /diagram iteration loops, with breakdowns.")
    ap.add_argument("--quick", action="store_true", help="inner loops only (~1 min)")
    ap.add_argument("--dry-run", action="store_true", help="list what would run")
    ap.add_argument("--note", default="", help="one clause on what changed since the last block")
    args = ap.parse_args(argv)

    outdir = tempfile.mkdtemp(prefix="diagram-timings-")
    try:
        plan: list[tuple[str, object]] = [
            ("hamlet_gen_gate", lambda: bench_hamlet(outdir)),
            ("cohort_4", lambda: bench_cohort(4, quick=True)),
        ]
        if not args.quick:
            plan += [
                ("map_regen_sawada", lambda: bench_cache(outdir)),
                ("cohort_24", lambda: bench_cohort(24, quick=False)),
                ("pool_sweep", bench_pool_sweep),
                ("full_gate", bench_gate),
                ("warm_gate", lambda: bench_gate(bypass=False)),
            ]
        if args.dry_run:
            for key, _ in plan:
                print(key)
            return 0
        results: list[Result] = []
        for key, fn in plan:
            print(f"  running {key} ...", flush=True)
            result = fn()  # type: ignore[operator]
            print(f"  {key:20} {fmt(result.total):>14}{'' if result.ok else '   FAILED'}", flush=True)
            for label, secs in result.parts:
                print(f"      {label:46} {fmt(secs):>12}")
            results.append(result)
        with LEDGER.open("a") as fh:
            fh.write(render_block(results, context(), args.note))
        print(f"\nappended to {LEDGER.name}" + ("  (QUICK set only - not a full row)" if args.quick else ""))
        return 0
    finally:
        shutil.rmtree(outdir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
