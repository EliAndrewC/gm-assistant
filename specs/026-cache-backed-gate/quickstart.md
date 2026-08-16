# Quickstart: Cache-Backed Gate (026)

From `.claude/skills/diagram/` inside a session clone:

```bash
make done                      # warm cache: hits skip generation, checks still run, floors enforced
GATE_NO_CACHE=1 make done      # bypass: regenerate everything (use after a pip-level change,
                               # a container rebuild, or when you suspect the cache)
python3 regen.py pool/*/*.gen.py   # iteration path - unchanged, never pays coverage overhead
python3 cache_audit.py         # empirical byte-identity audit (~10 min) - MANDATORY after any
                               # change to gencache.py or to how generation is driven
python3 timings.py             # ledger run; now includes warm_gate beside the cold full_gate
```

What changed (2026-08-16, GM decision reversing 2026-08-08):

- The gate consults the gen cache. A verified HIT loads the cached manifest and runs ALL current
  checks against it; only generation is skipped. Any doubt (key moved, corrupt entry, no stored
  coverage, bypass set) regenerates exactly as before.
- The key now covers installed package versions + renderer fonts, so a dependency change
  invalidates automatically (the PIL-incident class).
- Coverage floors still hold on hits: each miss stores its generation's line coverage in the
  entry; each hit replays it into the run's combine.
