# `pipeline/` - how a pool map gets regenerated, cached, rendered and indexed

The BUILD side of the skill. The other three sides are the drawing engines (`settlement/`,
`waterfields/`, `hamletgen/`, `compound.py`), the gate (`check_village/`), and the by-hand
diagnostics ([`../tools/`](../tools/CLAUDE.md)).

Run these as modules, from the skill root:

    python3 -m pipeline.regen pool/hamlets/sawada.gen.py       # ~20s cold, ~1s cached
    python3 -m pipeline.regen pool/*/*.gen.py                  # every LIVE map, fanned out
    python3 -m pipeline.regen --no-cache pool/hamlets/inashiro.gen.py

| module | what it is | measured for coverage |
|---|---|---|
| `gencache` | the generation cache: the KEY, `store`/`load`, and `gate_obtain` (the gate rides this cache since feature 026) | no - a driver |
| `regen` | the ITERATION path: regenerate a map, or skip it when nothing it depends on changed | no - a driver |
| `render_cache` | main's renders: a content-hash short-circuit so main regenerates its own renders from its own tip after the stop-work push | yes |
| `poolmaps` | the SINGLE source of truth for which pool maps are LIVE and which are FROZEN museum pieces | yes |
| `pool_index` | writes `pool/index.html`, the browsable index over the whole pool | yes |

## The two engine-tree walks must stay in step

`gencache.engine_files()` and `render_cache.engine_fingerprint()` are separate functions answering
the same question - "which .py files determine what a map comes out as?" - and they prune the same
way: `pool/`, `wip/`, `tests/`, `__pycache__`, dot-dirs and dot-files, plus any `test_*` directory
or `test_*.py` file. **If you change one, change the other**, and extend both ratchet tests
(`test_engine_files_prunes_the_tests_tree`, `test_engine_fingerprint_covers_and_skips`).

Two properties of that walk are load-bearing, and each was learned the expensive way:

- **It recurses.** A root-only listing silently stopped keying the cache on the main engine when
  `settlement/` became a package (feature 025), serving stale maps after engine edits. Nested
  packages count too - `settlement/fields/` (feature 112) is inside both walks, and a
  directory-shaped rule that dropped it would leave every map cached through an edit to the field
  engine, which is a quiet failure.
- **It prunes `tests/`.** Before the 2026-08-16 reorganization every test was a root-level
  `test_*.py`, so the name filter covered them all. Under `tests/` the helpers (`_builders.py`,
  `__init__.py`) match no name filter, and counting them as engine inputs would invalidate every
  map in the pool on any edit to a test helper. Same class of bug as the dot-file filter, which
  exists because the gate's own scratch drivers used to land in the skill dir and poison every
  concurrent key computation, so nothing ever hit.

Everything else here is still walked, including `tools/` and this package's own siblings. That is
deliberate conservatism: the cheap failure is regenerating a map that did not need it; the
expensive one is serving a stale map. `gencache` and `regen` exclude themselves (`_NOT_ENGINE`,
matched by basename) because the cache cannot be its own input, and `render_cache` excludes itself
for the same reason.

## Before you trust a cache change, audit it

`python3 -m tools.cache_audit` (~10 min) perturbs a random numeric literal inside a `settlement/`
function, sweeps the pool with the cache and again with `--no-cache`, and demands byte-identical
artifacts. It never looks at the key, so it cannot share the key's blind spots. Since the gate
TRUSTS the cache (feature 026), this is the empirical backstop for the key itself - which makes
running it after a change here more important, not less.

The full reasoning - what the key covers, the soundness argument, the concurrency and
container-rebuild cases, and THE TRAP that costs three wrong conclusions per session if you do not
know it - is in `gencache.py`'s own docstring and in the skill's [`../CLAUDE.md`](../CLAUDE.md).
