# `/diagram` iteration timings - a dated ledger

**Load this file when:** you are about to do performance work, you want to know what a loop costs
before choosing one, or you suspect something got slower.

Iteration cost is the main thing standing between this project and correctness. A 15-second loop
gets iterated in; a 4-minute loop gets guessed around, and guess-and-check is what turns a simple
request into a multi-hour slog. So the numbers are tracked rather than remembered.

**Re-measure with `python3 timings.py`** (`--quick` for the inner loops, ~2 min; the full set is
~12 min). It APPENDS a dated block below. **Never rewrite or prune old blocks** - the trend is the
product. Add `--note "what changed"` when a row is meant to show the effect of something.

**Run it** after performance work, after adding a tier or archetype to the generator, and whenever
a loop starts feeling slow.

## How to read it

- **Wall clock, on this container.** The context line records cpus / python / resvg / commit,
  because a container rebuild moves all of these and the timings with them. Compare rows measured on
  the same context; across a rebuild, treat a jump as unexplained until proven otherwise.
- **`full_gate` drifts upward for honest reasons.** It carries every unit test in the skill (2,863
  at last count) and grows as rules are added. A rise there is not automatically a regression - but
  it IS a budget, and when it stops fitting in the pause between turns it needs work regardless of
  whose fault it is.
- **Score a performance change on the ONE benchmark it targets**, not on `full_gate`.
- A benchmark that FAILED is recorded and marked. A timing measured off a broken tree is worse than
  no timing.

## What the first breakdown showed (2026-08-15)

The point of recording parts rather than totals, immediately borne out - three of these four are
things nobody would have guessed from the totals alone.

- **The gate is not the cost; generation is.** On the inner loop, all 189 checks run in **0.7 s (5%)**
  while composing and drawing the map takes **11.6 s (82%)**. Optimizing the validator cannot help.
  This also means checks are nearly free to ADD, which is the opposite of the assumption that has
  been quietly shaping how carefully we ration them.
- **`full_gate` is 99% pytest.** Lint, format and typecheck together are **1.8 s** of a 4 min 15 s
  gate. Any work on gate speed is work on the test suite, full stop - and conversely, after a
  change that touches no covered module, the three cheap phases can be run alone for 1.8 s instead
  of re-running the whole gate.
- **Cohorts run serially, and that is the biggest available win.** 24 maps at 12.4 s each is 5
  minutes of wall clock on a 22-cpu box that sits idle for all of it. The same work fanned out
  should land near 40 s. This is the verification loop of every future conversion, so it gets slower
  and more central as the migration proceeds. NOT DONE - flagged here as the first thing to reach for
  when we turn to efficiency. **(DONE same day: `cohort_audit.py` and `regen.py` now fan out across
  worker processes - cpus minus 2 by default, `--jobs 1` for serial. Safe because a map is a pure
  function of its spec, verified by diffing parallel against serial output. Measured in the next
  ledger block; a fanned-out loop's floor is its single slowest map.)**
- **The gen cache is earning its keep**: the heaviest hand-authored map costs **15.5 s** cold and
  **1.3 s** warm, a 12x saving on every regeneration that did not need to happen.

## What we are watching

- **`hamlet_gen_gate` must stay in the tens of seconds.** The whole scripted-generation migration is
  premised on it. If it reaches minutes, the central claim is gone.
- **`full_gate` grows for honest reasons** - it carries every unit test in the skill and grows as
  rules are added. Treat it as a budget, not a score. It reached 4 min 15 s while the skill's
  CLAUDE.md still described it as "~2 to 2.5 minutes" (2026-08-08); nobody was wrong, nobody
  re-measured, and that drift is why this ledger exists.
- **Every conversion adds maps to sweep and checks to run.** These numbers only go up as the
  migration proceeds, so the budget has to be watched on the way rather than rediscovered at the top.

---

## Ledger

### 2026-08-15

*22 cpus, python 3.14.4, resvg 0.46.0, at commit `60f62b0` - 28 map gen scripts (24 hand-authored + 4 scripted), 2863 tests.* Baseline. First block with breakdowns.

| loop / part | what | wall clock | share |
|---|---|---|---|
| **`hamlet_gen_gate`** | scripted hamlet: one map, generated + gated + rendered (THE inner loop) | **14.2 s** | |
| &nbsp;&nbsp;↳ generate (compose + draw) | | 11.6 s | 82% |
| &nbsp;&nbsp;↳ gate (check_village, 189 checks) | | 0.7 s | 5% |
| &nbsp;&nbsp;↳ render PNG (resvg) | | 1.9 s | 13% |
| **`cohort_4`** | cohort of 4 hamlets (does a fix generalize?) | **44.3 s** | |
| &nbsp;&nbsp;↳ per map | | 11.1 s | - |
| &nbsp;&nbsp;*parts do not sum to the total: `per map` is the average, not a component* | | | |
| **`map_regen_minami`** | heaviest hand-authored map through `regen.py` | **15.5 s** | |
| &nbsp;&nbsp;↳ cold (cache miss: compose + draw + gate) | | 15.5 s | 100% |
| &nbsp;&nbsp;↳ warm (cache hit) | | 1.3 s | - |
| &nbsp;&nbsp;*the total is the COLD run; the warm row is what the cache buys* | | | |
| **`cohort_24`** | cohort of 24 hamlets (the bar for an archetype) | **4 min 58.7 s** | |
| &nbsp;&nbsp;↳ per map | | 12.4 s | - |
| &nbsp;&nbsp;*parts do not sum to the total: `per map` is the average, not a component* | | | |
| **`pool_sweep`** | regenerate + gate all hand-authored maps, 22 workers | **40.6 s** | |
| &nbsp;&nbsp;↳ test_a_map_is_immune_to_an_upstream_change_in_the_nu | | 32.5 s | - |
| &nbsp;&nbsp;↳ test_village_passes_gate[sawada.gen.py] | | 21.8 s | - |
| &nbsp;&nbsp;↳ test_village_passes_gate[minami.gen.py] | | 18.8 s | - |
| &nbsp;&nbsp;↳ test_village_passes_gate[kashikawa.gen.py] | | 17.5 s | - |
| &nbsp;&nbsp;↳ test_village_passes_gate[tango.gen.py] | | 17.1 s | - |
| &nbsp;&nbsp;↳ test_village_passes_gate[nagahara.gen.py] | | 15.8 s | - |
| &nbsp;&nbsp;↳ test_village_passes_gate[inashiro.gen.py] | | 14.5 s | - |
| &nbsp;&nbsp;↳ test_village_passes_gate[hoshizora.gen.py] | | 12.8 s | - |
| &nbsp;&nbsp;*parts are the 8 slowest tests' own CPU time; they overlap in wall clock because the sweep runs parallel* | | | |
| **`full_gate`** | `make done` - the whole gate | **4 min 15.1 s** | |
| &nbsp;&nbsp;↳ lint (ruff check + duplicate-def scan) | | 1.5 s | 1% |
| &nbsp;&nbsp;↳ format (ruff format --check) | | 0.1 s | 0% |
| &nbsp;&nbsp;↳ typecheck (mypy --strict, 9 modules) | | 0.2 s | 0% |
| &nbsp;&nbsp;↳ test (pytest -n auto + 100% coverage gate) | | 4 min 13.4 s | 99% |

### 2026-08-15

*22 cpus, python 3.14.4, resvg 0.46.0, at commit `9778593` - 28 hand-authored maps, 2863 tests.* cohort_audit.py + regen.py fan out across processes (cpus-2); cohort/sweep wall clock now bounded by the slowest single map

| loop / part | what | wall clock | share |
|---|---|---|---|
| **`hamlet_gen_gate`** | scripted hamlet: one map, generated + gated + rendered (THE inner loop) | **14.2 s** | |
| &nbsp;&nbsp;↳ generate (compose + draw) | | 11.6 s | 81% |
| &nbsp;&nbsp;↳ gate (check_village, 189 checks) | | 0.7 s | 5% |
| &nbsp;&nbsp;↳ render PNG (resvg) | | 1.9 s | 14% |
| **`cohort_4`** | cohort of 4 hamlets (does a fix generalize?) | **13.8 s** | |
| &nbsp;&nbsp;↳ per map | | 3.4 s | - |
| &nbsp;&nbsp;*parts do not sum to the total: `per map` is the average, not a component* | | | |
| **`map_regen_minami`** | heaviest hand-authored map through `regen.py` | **14.2 s** | |
| &nbsp;&nbsp;↳ cold (cache miss: compose + draw + gate) | | 14.2 s | - |
| &nbsp;&nbsp;↳ warm (cache hit) | | 1.3 s | - |
| &nbsp;&nbsp;*the total is the COLD run; the warm row is what the cache buys* | | | |
| **`cohort_24`** | cohort of 24 hamlets (the bar for an archetype) | **28.5 s** | |
| &nbsp;&nbsp;↳ per map | | 1.2 s | - |
| &nbsp;&nbsp;*parts do not sum to the total: `per map` is the average, not a component* | | | |
| **`pool_sweep`** | regenerate + gate all hand-authored maps, 22 workers | **46.0 s** | |
| &nbsp;&nbsp;↳ test_a_map_is_immune_to_an_upstream_change_in_the_nu | | 37.8 s | - |
| &nbsp;&nbsp;↳ test_village_passes_gate[sawada.gen.py] | | 30.8 s | - |
| &nbsp;&nbsp;↳ test_village_passes_gate[minami.gen.py] | | 25.4 s | - |
| &nbsp;&nbsp;↳ test_village_passes_gate[tango.gen.py] | | 25.2 s | - |
| &nbsp;&nbsp;↳ test_village_passes_gate[kashikawa.gen.py] | | 23.6 s | - |
| &nbsp;&nbsp;↳ test_village_passes_gate[kikuta.gen.py] | | 23.0 s | - |
| &nbsp;&nbsp;↳ test_village_passes_gate[inashiro.gen.py] | | 21.6 s | - |
| &nbsp;&nbsp;↳ test_village_passes_gate[nagahara.gen.py] | | 20.5 s | - |
| &nbsp;&nbsp;*parts are the 8 slowest tests' own CPU time; they overlap in wall clock because the sweep runs parallel* | | | |
| **`full_gate`** | `make done` - the whole gate | **4 min 10.2 s** | |
| &nbsp;&nbsp;↳ lint (ruff check + duplicate-def scan) | | 1.4 s | 1% |
| &nbsp;&nbsp;↳ format (ruff format --check) | | 0.1 s | 0% |
| &nbsp;&nbsp;↳ typecheck (mypy --strict, 9 modules) | | 0.2 s | 0% |
| &nbsp;&nbsp;↳ test (pytest -n auto + 100% coverage gate) | | 4 min 08.5 s | 99% |
