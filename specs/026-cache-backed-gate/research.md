# Phase 0 Research: Cache-Backed Gate (026)

All unknowns from the Technical Context resolved. Decision / Rationale / Alternatives per item.

## R1. What the dependency-state key input is made of

**Decision**: Two components, hashed into the existing key alongside `sys.version` and the resvg
version:

1. **The installed-distribution set**: sorted `(name, version)` of every installed Python
   distribution, via `importlib.metadata.distributions()`. This is an in-process `pip freeze`.
2. **The renderer font files**: the bytes of the DejaVu face(s) the drawing code loads. PIL opens
   font files in C, invisible to the run's opened-file capture, and text metrics feed label boxes
   and therefore manifests - this is exactly the PIL layout-engine incident channel (16 manifests
   rewritten by a container rebuild with no code change).

**Rationale**: What runs is what is *installed*, not what the lockfiles say - a one-off exploratory
`pip install` (explicitly blessed by project doctrine) changes behavior without touching any
lockfile, so hashing lockfile bytes would miss it. The distribution enumeration costs ~10-50 ms
once per key computation, negligible against a 1-20 s gen. Failure direction: if enumeration or a
font path fails, the component degrades to a per-run random marker - i.e. permanent miss, never
staleness - the same conservative convention `split_sources` already uses for unparseable files.

**Alternatives considered**: hashing the two webapp lockfiles (`webapp/requirements.txt`,
`requirements-dev.txt`) - rejected as both over- and under-inclusive (misses ad-hoc installs;
invalidates the diagram pool on webapp-only dep bumps, though that cost would have been
acceptable). Hashing only the packages the engine imports - rejected: predicting what matters is
the exact failure mode gencache's docstring forbids ("nothing here predicts").

## R2. How the gate obtains a map: subprocess-on-miss, restore-on-hit

**Decision**: A new gate-facing function in `gencache.py` (working name `gate_obtain(gen) ->
(manifest_path, how)`) with three paths:

- **HIT (entry valid AND carries coverage data)**: restore the entry's artifacts to the pool paths
  (byte-identical no-op in the common case), copy the entry's coverage data file into the skill
  dir as a fresh parallel-suffix file (`.coverage.gatehit-<map>-<pid>`), return the manifest. No
  generation executes.
- **MISS (key moved, entry absent/corrupt, or entry lacks coverage data)**: run the generation in
  a subprocess under `python3 -m coverage run --parallel-mode` driving the existing
  `run_and_record` + `store` path, then attach the child's coverage data file and its measured CPU
  seconds to the entry. The child's parallel data file also stays in the skill dir so the current
  run's coverage picks it up.
- **BYPASS (`GATE_NO_CACHE=1`)**: always the miss path.

`test_villages.py`'s `_regen_and_gate` calls `gate_obtain` instead of `runpy.run_path`, then runs
`check_village` on the manifest IN-PROCESS exactly as today - **checking is never cached** on
either path.

**Rationale**:
- Per-map coverage capture requires a dedicated coverage recorder per generation; a second
  in-process `Coverage` object under an active pytest-cov session is unsupported/fragile, so the
  subprocess is the only clean recorder. It costs one interpreter start + import per MISS
  (~1-1.5 s), paid only when regeneration (1-20 s) is happening anyway.
- Entries created by the ITERATION path (`regen.py`) carry no coverage data - deliberately, so the
  iteration loop pays zero overhead. The gate treats such entries as misses and refreshes them
  with coverage; the second gate run then hits.
- Reusing `run_and_record`/`store` means `cache_audit.py` audits the same machinery the gate now
  trusts - one path, one audit.

**Alternatives considered**: in-process generation on miss with no coverage storage (first gate
after any iteration-path regen would fail the floors); reading executed lines out of pytest-cov's
own data mid-run (process-wide, only flushed at session end - impossible per-map); trusting
`run_and_record`'s `sys.monitoring` dep capture as coverage (function-level, floors are
line-level).

## R3. How carried coverage data reaches the coverage report

**Decision**: Both hit-restored and miss-produced files are parallel-mode data files
(`.coverage.<suffix>`) in the skill dir. The Makefile `test` target gains one line before its two
`coverage report` calls: `python3 -m coverage combine --append` (quiet, tolerant of nothing to
combine). pytest-cov may or may not have already swept the files into `.coverage` (it globs
`data_file + ".*"` at session end); the explicit append-combine makes the merge deterministic
either way - if pytest-cov already consumed them it is a no-op, if not it merges the leftovers.

**Rationale**: relying on pytest-cov's combine glob alone is relying on an internal; the explicit
combine is one line and cannot double-count (coverage merge is a set-union of arcs/lines).
Absolute paths inside the data files are stable because the cache is per-clone and restored data is
only ever replayed in the clone that recorded it.

**Risk + early verification**: the first implementation task is a spike test proving a foreign
parallel data file present during a pytest-cov run ends up in the final report (this is the
load-bearing mechanism; if it failed we would need a rethink, so it is proven before anything is
built on it).

## R4. Gen time budgets under the subprocess

**Decision**: the child measures its own `time.process_time()` around the gen and reports it (in
the entry's meta); `_regen_and_gate` asserts the budget against the reported child CPU on a miss,
and asserts nothing on a hit (nothing ran). The budget guard's fire-and-override test keeps using
an in-child fake gen so the guard is still SHOWN to fire.

**Rationale**: `time.process_time()` in the parent cannot see child CPU; `resource.getrusage
(RUSAGE_CHILDREN)` aggregates across all children per worker and is ordering-sensitive. The child
self-reporting is exact and keeps the calibrate-against-the-gate doctrine unchanged (contention
inflates the child the same way it inflated in-process runs).

## R5. What still runs in-process, deliberately

- **The check battery** (both paths) - checks are never cached; new/changed checks always apply to
  whatever manifest the gate obtained.
- **The randomness-immunity test** - regenerates its subject twice in-process BY DESIGN (perturbed
  vs clean); out of scope, and its in-process execution incidentally keeps the hamlet-wing
  coverage warm on every run regardless of cache state (a second line of defense for the floors,
  noted but NOT relied on - its subject changes as tiers convert).
- **The regression replay** - reads frozen fixtures, never regenerates; unaffected.
- **The slow-gen budget self-test** - adapted to the subprocess runner, still proves the guard
  fires.

## R6. Doctrine and docs to update (the old rule's footprint)

Grep-verified footprint of "the gate never reads the cache":

- `gencache.py` docstring, "WHAT IT DELIBERATELY DOES NOT DO" - rewritten to the new contract
  (records the 2026-08-16 GM reversal + why, the bypass, the dependency-change procedure).
- `regen.py` docstring ("The gate deliberately does not come through here").
- `test_gencache.py::test_the_gate_never_reads_the_cache` - retired, replaced (see contracts).
- Skill `CLAUDE.md`: "**The cache is NEVER the source of truth**" paragraph and the sweep guidance
  around it; the "AUDIT IT" paragraph stays and gains the note that the gate now also rides the
  audited path.
- Root `CLAUDE.md`: no literal statement of the rule (verified - it defers to the skill docs); no
  edit needed beyond none.
- `docs/iteration-loop.md`: gains the GM's 2026-08-16 threshold rule (a >=5% whole-process speedup
  is always above the caring threshold; per-function micro-wins are not unless the function is the
  process) - recorded here because this is the project's home for measured loop-rule evidence.
- NEW dependency-change procedure text (skill CLAUDE.md, beside the cache section): after a
  pip-level change or container rebuild, run one bypassed sweep (`GATE_NO_CACHE=1 make done`) on
  the main-integration state; note that the installed-distribution keying makes the KNOWN channel
  automatic and the procedure is belt-and-suspenders for unknown ones.

## R7. Measurement (FR-010) and the two broken timings benchmarks

**Decision**: `timings.py` gains a `warm_gate` benchmark (prime the cache with one sweep, then run
`make done` and record it beside `full_gate`, which stays the bypassed/cold measurement so the
ledger keeps comparing like with like). Two existing benchmarks are repaired in the same pass,
found broken by the 2026-08-16 ledger run: `bench_hamlet` still invokes `check_village.py` as a
file (024 made it a package; becomes `python3 -m check_village`) and `bench_cache` targets frozen
Minami (retargeted to Sawada, the heaviest LIVE map). Both repairs are prerequisites for SC-001's
measurement being trustworthy.

## R8. Constitution Principle XII (historical grounding)

This feature changes no generator's assertions about the world: it is output-preserving by
construction (a hit serves bytes a from-scratch run would produce; `cache_audit.py` is the
empirical enforcement of exactly that property). Both bookends are therefore N/A - there is no new
element to ground and no rendered artifact changes. SC-002 (cache_audit green) is the standing
proof.
