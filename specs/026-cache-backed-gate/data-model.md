# Data Model: Cache-Backed Gate (026)

## Cache entry (extended)

A gen-cache entry today: artifacts (`<map>.json`, `<map>.svg`, optional `<map>.png`) plus
`meta.json` (the key inputs), published atomically temp-then-replace with `meta.json` last.

Extensions (all OPTIONAL - an entry without them is valid for the iteration path and a MISS for
the gate):

| field / file | type | meaning |
|---|---|---|
| `coverage.data` | coverage.py data file | line coverage of the generation subprocess that built this entry, recorded under the same key |
| `meta.json: gen_cpu_s` | float | the child's `time.process_time()` for the generation, for the budget assert on the run that built the entry and for diagnostics after |
| `meta.json: deps` | string (hash) | the dependency-state component of the key: sha of the sorted installed-distribution `(name, version)` list + renderer font file bytes |

**Validation rules**:
- `deps` participates in key equality exactly like every existing component - any byte of it moving
  is a miss for every consumer (gate AND iteration path).
- `coverage.data` present but unreadable/empty => the gate treats the entry as a MISS (conservative
  direction), and the refresh overwrites it.
- The atomic-publish invariant is preserved: `coverage.data` and `gen_cpu_s` are written into the
  entry's temp dir BEFORE the final `meta.json` publish, so a concurrent reader still sees a
  complete entry or none.

## State transitions (per map, per gate run)

```text
                         GATE_NO_CACHE=1 ──────────────► MISS path
entry absent / key moved / corrupt ───────────────────► MISS path
entry valid, no coverage.data (iteration-made) ───────► MISS path (refresh adds coverage)
entry valid + coverage.data ──────────────────────────► HIT path

MISS path: subprocess `coverage run --parallel-mode` -> run_and_record + store
           -> entry now carries coverage.data + gen_cpu_s
           -> child's parallel data file remains for this run's combine
           -> budget assert on child-reported CPU
HIT path:  restore artifacts to pool paths; copy coverage.data in as
           `.coverage.gatehit-<map>-<pid>`; no generation executes; no budget assert
BOTH:      check_village runs IN-PROCESS on the manifest (checking is never cached)
```

## Key entities and their homes

- **Dependency-state input**: computed in `gencache.py` beside the existing
  `sys.version`/resvg-version inputs; one function, unit-tested, conservative on failure.
- **`gate_obtain()`**: `gencache.py` (owns entry layout); consumed by `test_villages.py`.
- **Bypass**: `GATE_NO_CACHE` env var, read only by `gate_obtain`; tests own their environment
  (delenv/setenv) so the bypass can never silence the tests that prove the cache path works.
- **Combine step**: one `coverage combine --append` line in the Makefile `test` target, before the
  two `coverage report` calls.
