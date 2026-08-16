# Contract: the gate ↔ gen-cache interface (026)

## `gencache.gate_obtain(gen: str) -> tuple[str, str, float | None]`

Returns `(manifest_path, how, gen_cpu_s)` where `how` is `"HIT"` or `"REGENERATED"` and
`gen_cpu_s` is the child-measured CPU seconds on a miss, `None` on a hit.

Guarantees:

1. On `"HIT"`: no generation code executed in any process; the pool artifacts equal the entry's
   bytes; a parallel coverage data file carrying the generation's line coverage exists in the
   skill dir for the current run's combine.
2. On `"REGENERATED"`: the entry was rebuilt via the same `run_and_record` + `store` path
   `regen.py` and `cache_audit.py` use, in a `coverage run --parallel-mode` subprocess, and now
   carries `coverage.data` + `gen_cpu_s`.
3. `GATE_NO_CACHE=1` in the environment forces `"REGENERATED"` unconditionally.
4. Any defect in the entry (missing artifact, unreadable meta, absent/empty coverage data, key
   mismatch, including the dependency-state component) yields `"REGENERATED"` - the failure
   direction is always regeneration, never staleness.
5. The caller (the sweep) runs the check battery in-process on `manifest_path` on BOTH paths.

## Environment variables

| var | consumer | effect |
|---|---|---|
| `GATE_NO_CACHE=1` | `gate_obtain` | bypass: full regeneration regardless of cache state |
| `DIAGRAM_SKIP_RENDER=1` | gen child | unchanged - the sweep still skips the PNG raster |
| `DIAGRAM_ALLOW_SLOW_GENS=1` | sweep budget assert | unchanged; still must not silence the guard's own self-test |

## Pinning tests (replace `test_the_gate_never_reads_the_cache`)

| test | pins | teeth demonstration |
|---|---|---|
| `test_the_gate_reuses_a_verified_hit` | guarantee 1 (no generation on hit) | make `gate_obtain` ignore the entry -> fails |
| `test_a_hit_still_runs_current_checks` | guarantee 5 (a bad cached manifest still fails the gate) | short-circuit checking on hit -> fails |
| `test_gate_bypass_forces_regeneration` | guarantee 3 | ignore the env var -> fails |
| `test_an_entry_without_coverage_data_is_a_gate_miss` | guarantee 4 | accept coverage-less entries -> fails |
| `test_a_dependency_change_invalidates_every_entry` | R1 keying | drop deps from the key -> fails |
| `test_gate_miss_stores_coverage_the_next_hit_replays` | guarantees 1+2 composition | stop storing/restoring coverage -> fails |

Each teeth demonstration is performed once during implementation (revert the behavior, watch the
test fail, restore) per the check-before-fix / proven-teeth discipline; the tasks file records the
demonstration.
