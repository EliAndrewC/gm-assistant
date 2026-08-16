# /diagram engine - dev loop

Guidance for *working on the diagram engine* (the `settlement/` package, the `check_village/` package, the pool
generators), as opposed to *invoking* `/diagram` to draw a map (that is `SKILL.md`). This file
auto-loads whenever a session edits files in this directory - which is exactly when it applies.

The project-wide iteration doctrine lives in the root [`CLAUDE.md`](../../../CLAUDE.md)
"Iteration-loop efficiency" section (batch recon into fewer bigger turns; iterate on the ONE
motivating artifact, then run the full test bed once at the end; background the final gate; never
cut the ritual/guardrail steps). Read that first; this file carries the concrete diagram numbers
and the DIAGRAM-SPECIFIC lessons that section does not cover - each earned by costing real
round-trips.

## Gate and sweep timings (the motivating-artifact loop, concretely)

The root "iterate on the motivating artifact, sweep once at the end" rule has these diagram
numbers. A single map's regen + gate is ~1-7s; the heaviest LIVE maps are the scripted hamlets
(Sawada ~20s, Kashikawa ~16s solo CPU - `GEN_TIME_BUDGETS` says why that is inherent, not a bug).
The old heavy maps (Minami ~14.5s, Nagahara / Tango / Kikuta / Hoshizora ~10s after three
optimization passes) are FROZEN since 2026-08-16 and never regenerate - see "The legacy pool is
FROZEN" below:

    DIAGRAM_SKIP_RENDER=1 python3 pool/<type>/<map>.gen.py && python3 -m check_village pool/<type>/<map>.json

**...or let the CACHE skip the work entirely** (2026-08-08). `regen.py` regenerates a map only if
something that map depends on actually changed, and prints `CACHED` or `REGENERATED` every time:

    python3 regen.py pool/hamlets/sawada.gen.py              # ~20s cold, ~1s cached
    python3 regen.py pool/*/*.gen.py                         # every LIVE map, fanned out (frozen legacy maps print FROZEN, skipped)
    python3 regen.py --no-cache pool/hamlets/inashiro.gen.py # force the work

Multi-map runs fan out across worker processes (cpus minus 2; `--jobs 1` for serial), as does
`cohort_audit.py` - since 2026-08-15, when the timings ledger showed the serial cohort was the
biggest available win. Wall clock for a fanned-out sweep is bounded by its single slowest map, so
per-map cost is what remains worth optimizing. Parallelism cannot change a verdict (each map is a
pure function of its spec; `gencache.store` publishes atomically), and the per-map output is
captured in the worker and printed in order, so a parallel run reads like a serial one.

The key covers the gen's bytes, the MODULE-LEVEL source of every engine module, the source of
every function that map actually EXECUTED, every non-source file the run opened, and the
interpreter/renderer versions - so an edit to any of the ~200 `settlement/` engine functions Minami
never runs leaves Minami cached, while an edit to one it does run, or to any module-level constant,
does not. `gencache.py`'s docstring carries the soundness argument; `test_gencache.py` is the
demonstration, and every test there that asserts a HIT also regenerates and compares bytes, because
"the key did not move" proves nothing on its own.

**The gate RIDES the cache since 2026-08-16 (feature 026, GM decision reversing the 2026-08-08
"gate never reads the cache" rule).** `test_villages.py` obtains each live map via
`gencache.gate_obtain`: a verified HIT - key match plus stored generation coverage - restores the
artifacts, replays the entry's coverage data into the run (so the coverage floors stay honest),
and skips GENERATION only. The full current check battery still runs against whatever manifest was
served - checking is never cached. Any doubt at all - key moved, entry incomplete, no stored
coverage (an iteration-made entry), or `GATE_NO_CACHE=1` - regenerates in a coverage-recording
subprocess exactly as a cold run would. Why this is safe to trust, one line each: generation is
deterministic, so a sound key implies byte-identical output; the key covers the dependency surface
BELOW the Python-source horizon (`_deps_state`: installed distributions + renderer font bytes -
the PIL layout-engine incident class); and `cache_audit.py` remains the standing empirical auditor
of the whole property. **After a dependency-level change** (a pip install/upgrade, a container
rebuild outside the lockfiles), run one bypassed sweep - `GATE_NO_CACHE=1 make done` - as
belt-and-suspenders for any channel the key cannot see. The contract's pinning tests are in
`test_gencache.py`; the decision's full reasoning in `specs/026-cache-backed-gate/`.

**AUDIT IT when you change the cache, or how generation is driven:** `python3 cache_audit.py`
(~10 min, or `--all` for the whole pool). It perturbs a random numeric literal inside a
`settlement/` function, sweeps the pool WITH the cache and again with `--no-cache`, and demands
byte-identical artifacts - so it tests the only property anyone cares about without ever looking at
the key, and cannot share the key's blind spots. Verified to have teeth: sabotaging `compute_key`
to return a constant makes it report STALE artifacts on the first mutation. This is deliberately
NOT in `make done` (minutes) - and since the gate trusts the cache (026), this audit is the
empirical backstop for the key itself, which makes running it after cache/driver changes MORE
important, not less.

**Concurrency and container rebuilds are covered, and asserted rather than assumed.** A
`.gencache` lives beside the engine, so it is per-CLONE: concurrent writers are two runs in one
working tree, which necessarily generate from the same sources and (generation being deterministic)
produce identical bytes. `store` writes every file via temp-then-`os.replace` and publishes
meta.json LAST, so a concurrent reader sees a complete entry or none. The interpreter and resvg
versions are in the key, because a container rebuild changes what a map comes out as - the PIL
layout-engine incident rewrote 16 manifests with no code change behind it.

**THE TRAP, which cost three wrong conclusions in one session.** A miss REBUILDS the entry against
whatever the sources say at that moment. So if you edit a file, regenerate (correctly a miss), then
`git checkout` the edit away, the next run is a *legitimate* miss - the stored entry was built
against code that no longer exists. Testing "does an edit to X invalidate?" therefore needs the
baseline re-established (run until you see `CACHED`) before each trial, or the previous trial's
cleanup produces the miss and you conclude the cache is broken when it is working perfectly.

**TIMINGS ARE TRACKED IN [`timings.md`](timings.md), MEASURED BY `python3 timings.py`** - one dated
block per run, each benchmark carrying its BREAKDOWN as well as its total, so a slow loop can be
attributed instead of merely noticed. Do not write fresh timings into prose here: this paragraph
used to say the full sweep was "~2 to 2.5 minutes" and was still saying it on 2026-08-15, when the
measured gate was past four. Nobody was wrong; nobody re-measured, and prose cannot tell you that.

Read the gate's own total as a BUDGET rather than a score - it carries every unit test in the skill
and grows as rules are added, for reasons unrelated to generator speed. **Score a perf change by A/B-ing the
ONE map against HEAD**, which is how both passes were measured.

**The one performance bug this engine keeps growing, and how to find it.** Every slow gen ever
profiled here has had the same shape: *a per-candidate scan of geometry that does not change during
the scan*. Minami silently became a **45+ minute** grind that way when the paddy-well rule landed
(`_well_ground_clear` rebuilt all 927 drawn basins per candidate seat, ~133k seats). The 2026-08-03
sweep then found four more instances, all in code that looked perfectly reasonable: `on_crop`
re-deriving every plot's bbox per seat, the ground-cover scatters testing every field/block polygon
per scatter POINT, `_near_corridor` walking every corridor segment, `_in_blocked` visiting every
keep-out. Together they were over half of the pool's runtime. The cures, in order of preference:
hoist the invariant out of the loop; add a bbox prefilter (`boxed_polys`/`boxed_hit`); index it
(`PointGrid`, or `Indexed` where the registry is mutated as you go). Never coarsen - see "When a
check is slow, INDEX it" below. The second pass (2026-08-04) found four more of the same shape:
the well memo's own FINGERPRINT (now a `frozen_terrain` scope, which asserts the invariant instead
of guessing it), `_fits` measuring every standing building, the ground-cover keep-outs, and a city
gen testing each candidate against every label on the map.

**The SECOND shape, found once the first was exhausted (2026-08-08): the same scan run again over
ground that has not changed.** Minami's dwelling `top_up` evaluated **511,519 candidate positions**
- effectively its whole runtime - and **64.6% of them were RE-visits of a seat an earlier pass had
already refused at the same tightness**, because the caller sweeps each caste's regions three times
over and again in `fill_exactly`, always on the same fixed 5x6 px lattice. `settlement.SeatMemo`
remembers refusals across calls: **21.0s -> 14.5s, and every manifest byte-identical**, because a
refusal only turns into a placement if an obstacle DISAPPEARS and nothing in a top-up phase removes
one. Three things about it are worth carrying to the next instance of this shape:

- **The memo ASSERTS the invariant instead of assuming it** (`sync()`), the same discipline
  `frozen_terrain` applies to the well memo. A registry that is rebound, truncated, or changed by
  anything but an append clears the memo - so a future gen that frees ground loses the SPEEDUP, not
  a hundred houses. That failure direction is the whole design.
- **Byte-identity is the oracle here, and it is a stronger one than the brief expected.** A memo
  that only skips work is output-preserving by construction, so any drift in a manifest is a
  soundness bug and not a judgment call - which is why this needed no `settlement-review` pass.
- **Measure the re-visit share PER GEN before wiring it in.** The same memo was fitted to Nagahara
  and Tango and made both SLOWER (9.56 -> 10.29s, 9.71 -> 10.19s): their re-visit shares are 3.1%
  and 0.0%, so every candidate paid the probe and almost none saved a test. Minami is the outlier
  because the Fox eight-temple doctrine leaves its packs unable to seat anything and its merchant
  target unmeetable. Below roughly a third re-visits, this is a pessimization.

Two levers deliberately NOT taken, so they are not re-derived: an `ok()`-level memo (that test is
pad-independent, so it is re-run once per pass) would spare 33,810 of the remaining 181,085
evaluations, but they are the CHEAPEST ones - and capping the unmeetable caste targets, which the
memo has already made nearly free. Both were measured, both are worth well under a second.

**And trust the A/B, not the profile's seconds.** cProfile charges its per-call overhead to
whatever has the most calls, which is exactly these tight inner loops - it valued the ground-cover
grid at 3-4s where the A/B measured 1.1s, and the well fingerprint at ~8s where the A/B measured
6.4s. Use the profile to find WHERE the time is; use `git stash` and two timed runs to find out
whether you actually saved any.

**If a gen ever "hangs", suspect that shape FIRST and profile before bisecting.** A timeout-based
bisect probe cannot distinguish "broken" from "slow", and one burned an hour here concluding an
innocent commit was the regression.

**And beware the CACHE you add to fix it** - two of the three staleness bugs in this file's history
came from the cure, not the disease (see `Indexed`, `_wgc_cache` and the comment in `_fits`). A
cache key built from lengths, record counts or object identity is a GUESS about content; `placed`
gets rebound to a filtered copy, and a field's `plot_polys` gets replaced with a same-length list,
and both guesses were wrong within a day. Prefer a registry that versions itself (`Indexed`), and
make sure the key is cheaper than the scan it guards - one fingerprint here cost more than the scan
it replaced.

Since 2026-08-03 the sweep ENFORCES a per-gen CPU budget (`GEN_TIME_BUDGETS` in
`test_villages.py`) so the next silent 45-minute-class regression fails loudly by name instead of
being waited out; `DIAGRAM_ALLOW_SLOW_GENS=1` overrides once you are certain perf is fine, and a
legitimately-outgrown map gets a bigger budget entry WITH its reason. **Budgets are calibrated
against the GATE, not a solo run** - under `pytest -n auto` a gen's own CPU time inflates 2-4x
through cache contention, which is why each entry is ~4x its recorded solo measurement.

**A GEN'S CPU TIME INFLATES 2-4x INSIDE THE GATE, so budgets are calibrated against the GATE, never
a solo run** (`test_villages.py` says this at the table; both halves of it were found the same day,
independently, by two sessions whose gates were slowing each other down). `process_time` is immune
to WAITING for a core but not to needing more cycles for the same work, and `-n auto` runs 22
workers here. Measured pairs, solo vs under-gate: hoshizora **12.4s / 35.7s**, kuwabata **16.8s /
36.4s**, enokida **19.9s / 31.9s**, kikuta **10.9s / 36.2s**, minami **~54s / 154.8s**. Which map
trips therefore depends on what else is on the box, so **diagnose before touching anything**: re-run
the named gen ALONE (`DIAGRAM_SKIP_RENDER=1 python3 -c "import time,runpy; t=time.process_time();
runpy.run_path('pool/<t>/<m>.gen.py', run_name='__main__'); print(time.process_time()-t)"`). Far
under budget alone means contention, not a regression.

The resolution, and one dead end worth not re-walking:

- **What the guard does now:** each entry is ~4x its SOLO measurement (~1.5x its worst observed
  under-gate time), which still nets the class of bug this exists for - the motivating regression
  ran ~250x over budget, not 20% over. An optimization pass the guard's first run prompted (the
  `on_crop` bbox hoist, ground-cover prefilters, a well-siting `PointGrid`) roughly halved every
  heavy gen, so the budgets sit on faster code too.
- **Do NOT try to auto-calibrate** by timing a proxy workload in the worker and scaling by the
  inflation it reports. The proxy has to stall the way a gen does and no cheap loop does: a tight
  arithmetic loop is L1-resident (1.56x under a controlled 20-way load, but 1.0x during a real
  sweep in which minami inflated 2.9x), while a DRAM-striding walk is already latency-bound and does
  not inflate at all (0.95x). A point sample after the gen cannot represent contention during it
  either. Tried and reverted 2026-08-03.
- **The override must not silence the guard's own self-test.** `DIAGRAM_ALLOW_SLOW_GENS=1` is
  documented for whole-sweep use, and it used to silence the budget for
  `test_slow_gen_budget_fires_and_the_override_silences_it` as well - so the one test proving the
  guard has teeth failed exactly when a session followed the advice, making the escape hatch a
  guaranteed red gate. The test now clears the variable for itself. Any future env-driven escape
  hatch needs the same treatment.
(Measured 2026-07-25: it had drifted to 112-215s across six runs, well past
the "~1 minute" this file used to claim from 2026-07-20; indexing the two worst checks that same day
brought it back to 77s. Re-measure and update this number when it drifts again - a stale figure here
is what makes a session mis-plan its loop.) So run the red/green loop against the ONE map
(or fixture) that shows the defect, where cycles are near-free, and reserve the full sweep for AFTER
that map is green. The sweep is MANDATORY, though, whenever shared engine code changed
(the `settlement/` package, the `check_village/` package, `waterfields.py`, a scripted engine): every LIVE
pool map is a downstream artifact of the engine, so the sweep is what proves "no other map
regressed" instead of hoping it. LIVE means the scripted maps only - the hand-authored pool is
FROZEN (see "The legacy pool is FROZEN" below) and is deliberately allowed to go stale.
Anti-patterns on record: the scale-bar feature used the full suite as its FIRST check of an engine
change - a failure that would have surfaced in ~6s on one map surfaced 17 minutes in; the
swept-collar check (11m07s wall) is the feature the project-wide 78%-turn-latency profile was taken
from.

## NEVER re-run what `make done` just ran, and never run pytest without `-n auto`

The single biggest time sink ever measured on this skill (2026-07-25, a 69-minute feature profiled
from the session transcript): **13.2 minutes - 19% of the whole feature's wall clock - went to one
`python3 -m pytest test_regressions.py` that `make done` had already run, in parallel, minutes
earlier.** Two compounding mistakes, both cheap to avoid:

- **`make done` runs `pytest -n auto`** (see the Makefile), which is ~7x faster than serial on this
  box: the 695-manifest regression replay is ~2 min under the gate and **13.4 min serial**. If you
  ever invoke pytest directly, pass `-n auto`. There is no reason to run it serially.
- **A green `make done` already covers `test_regressions.py`, `test_villages.py`, and every unit
  test.** Re-running any of them "to be sure" buys nothing - the gate is the proof. Re-run only what
  actually changed since the gate went green, and if that is markdown, re-run nothing (root
  CLAUDE.md, "docs-only diffs skip the gate").

## NEVER poll a backgrounded command - and it is now ENFORCED

Backgrounding the gate and then *watching* it is worse than running it in the foreground. Profile of
a 31-minute feature (2026-07-25): **10.9 minutes - 35% of the whole task - went to polling two gates
that had already finished.** The gates took 97s and 98s; the waits took 351s and 401s, both running
their full iteration budget because of this:

    for i in $(seq 1 80); do if ! pgrep -f "make done" >/dev/null 2>&1; then break; fi; command sleep 5; done

`pgrep -f "make done"` **matches its own shell** - the pattern is an argument of the very command
line being searched - so the `break` can never fire. And the loop was pointless anyway: a
backgrounded Bash command NOTIFIES you when it exits. Background the gate, spend the turn on the
docs or the commit message, and act on the notification.

[`scripts/no-poll-hooks.sh`](../../../scripts/no-poll-hooks.sh) (tested by `test-no-poll-hooks.sh`)
now BLOCKS the pattern at PreToolUse: `pgrep -f` / `pkill -f` with a literal pattern, any loop
containing a `sleep`, and the `command sleep` / `/bin/sleep` / `env sleep` forms that exist only to
dodge the harness's own foreground-sleep guard. A genuine wait on EXTERNAL state (a server port)
passes by putting `POLL_OK` in the command with a note saying what it waits for. Same rationale as
the batching hook: "background the final gate" was already written down here, and the session
followed it and then blocked on the gate anyway.

**And keep the backgrounded command simple enough that its EXIT CODE is real.** Run it as
`cd <dir> && make done > <log> 2>&1` and nothing more. A wrapper ending in `; echo EXIT=$?` makes the
SHELL exit 0 no matter what make did, so the harness notifies "exit code 0" for a gate that FAILED -
which happened on 2026-07-27: the paddy-well gate was reported green, its log's own last line was
`EXIT=2`, and the three failures it hid were pointing at a real design error in the new rule rather
than a slip. The log's tail is the authority; the notification is a summary of the wrapper. Put the
`cd` inside the same command too - a timed-out call can leave the shell's cwd somewhere else, and the
next `make done` then runs where there is no Makefile (or, worse, somewhere it should not).

## Before the gate, run the WHOLE affected test file - not a `-k` subset

That same profile paid an extra gate round trip (98s plus two turns) for a failure a local run would
have caught: the change altered geometry an existing test depended on, and the pre-gate check was
`pytest -k torii`, which did not include that test. The whole files for the modules you touched cost
~45s and reach every test the change can. So: cheap linters, then whole files, then the gate ONCE.

    python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy
    python3 -m pytest test_settlement.py test_checks/ -q -n auto --no-cov    # the files you touched, WHOLE
    make done                                                                  # once, backgrounded, not watched

### Probe vs survey: when `-x` pays (GM 2026-08-15)

Every test run is one of two things, and fail-fast is right for exactly one of them:

- **A PROBE** - "did anything break?", and you will fix whatever surfaces one at a time. Add `-x`:
  the first failure arrives in seconds and you were going straight back to the code anyway. This is
  the mid-iteration whole-file run after an engine change.
- **A SURVEY** - you need the failure SET to scope a problem: how far did this ripple, is this one
  bug or five? Run everything, no `-x`. The pattern of failures is the diagnostic.

The decision follows from RERUN COST: when a rerun is cheap, `-x` costs nothing; when a rerun
costs minutes, one complete run beats N fail-fast runs. That is why `make done` stays
report-everything (the GM's 2026-07-25 decision - every phase runs, all failures report together,
fix them all, re-run once) and why the coverage gate could not take `-x` anyway - coverage needs
the full run. Two caveats: a `-x` run that fails says nothing about the tests it never reached, so
it never substitutes for the whole-file pass before the gate - it is for iterating, not for
clearing; and under `-n auto`, xdist stops soon after the first failure rather than instantly,
which is still most of the saving.

## Ask the ENGINE where a feature fits - do not guess coordinates

When a map change ripples (an avenue shortens, ground frees, a pack seats more houses, a well goes
over its household cap), the fix needs a spot for one more feature. **Guessing coordinates and
regenerating is the most expensive loop in this skill**: 2026-07-25 spent three regenerate-and-check
cycles on two full batches of hand-picked well seats, every one refused. A scan of the MANIFEST
cannot predict `_fits` - those refusals came from a ward fence's 15px no-build corridor, which no
manifest records.

`s.open_seat(rect, w, h, clear_of=[...], well=True)` asks the engine's own `_fits`, at the point in
the gen where the feature would be placed, and returns the best clear seat (furthest from
`clear_of`, ties toward the rect center) or `None` if the ground is genuinely full. It found the
seat both hand-picked batches had missed, first try. Reach for it on any "this pocket needs one more
X" - and note the DRAW ORDER caveat: it can only see what has been drawn so far, so call it where
the feature belongs, not earlier.

## RANDOMNESS IS POSITIONAL OR SCOPED - never "wherever the stream happens to be"

The rule, and it governs every new draw you add: **a feature's randomness must depend on the feature,
not on how much randomness the map has drawn before it.** Two mechanisms, and one of them fits every
case.

- **A per-feature attribute** - a house's rake, its wall colour, whether it has a kura, which kind a
  ring seat gets - comes from **`self._hjit(x, y, salt)`**, which is a deterministic hash of the
  position. Its docstring has said why since it was written: "so it never ripples other placement or
  household counts". Pick an unused salt (1.0, 2.0, 3.0, 7.0, 11.0, 13.0, 21.0, 22.0 and 0.7/1.3/2.1
  are taken; `_quad` owns 71.0+).
- **A phase or a region** - a pack's seat jitter, a pasture's outline, a grove's crowns, a well grid,
  a ring's candidate seats - runs inside **`with self.rng_scope(name, *key)`**, whose stream is a hash
  of (map seed, name, key) and which restores the outer stream on the way out. Key it on the thing
  that identifies the instance: the bbox, the street run, the base polygon. Repeat calls on one key
  get their own numbers via a per-key counter, so two packs over the same ground do not twin.

**WHY (GM 2026-08-08), measured.** Everything drew from one global stream, so any change that altered
the NUMBER of draws made before a phase re-rolled that phase however unrelated it was. Injecting ONE
extra draw at the top of a gen and diffing every manifest key:

| tier | before | after |
|---|---|---|
| hamlet, village | 2 of 63-69 keys | **0 - isolated** |
| town, city | 12-15 of 71-101 keys | see below |

The cost was not theoretical. A caption resize in a city's temple quarter dropped a farm shed on a
garden **700 px away**, and the session that fixed it spent most of its time on maps it had not
meant to touch. Debugging a map you did not change is the expensive kind of work.

**HOW TO FIND THE NEXT ONE, because the method matters more than the list.** Run a gen twice - once
normally, once with one extra `random.random()` injected at `meta()` - and diff. Two probes, in this
order:

1. **Record-level**: for each manifest key, the first index whose record differs, and which FIELDS
   differ. `fields=['rot']` on the same x/y is an ATTRIBUTE drift (positional fix). A different x/y
   is a SEAT drift (scope the placer).
2. **Draw-site level**: wrap the `random` module functions to log the calling `file:line`, and find
   the first index where the two SEQUENCES disagree. That names the culprit exactly.

Use (1) first. Once the scopes are in, (2) starts reporting *consequences* - a grove whose crowns
differ because the buildings around it moved - and will send you chasing the wrong thing.

**Every one of these changes re-rolls the whole pool once**, so batch them: convert everything you
intend to, THEN regenerate and fix the fallout in one pass. Fixing fallout between conversions is
work you will throw away, because the next conversion produces a different fallout set.

## Ask the GEN who placed it - do not grep for the caller

The other half of the same lesson. `open_seat` answers "where does this fit?"; **[`why_placed.py`](why_placed.py)** answers *"who put this here?"* and *"what refused to put anything here?"* - the two questions you actually have when a map comes out wrong.

    python3 why_placed.py pool/provincial-cities/nagahara.gen.py --at 1102.6,1429.5
    python3 why_placed.py pool/provincial-cities/nagahara.gen.py --refused 1102.6,1429.5 --radius 12

`--at` prints every manifest record appended within the radius **with its call chain** - the gen
line to go and look at, and the engine method under it that chose the spot. `--refused` prints how
many `_fits` candidates were tested there, how many were refused, and **which sub-test said no**,
counted by cause.

WHY IT EXISTS (2026-08-08): a manifest record carries geometry and nothing about its provenance, and
~200 engine methods can append one. Chasing a single servant house that was abutting a ministry cost
about ten sequential greps through the `settlement/` package and the gen - `top_up`, then `servant_ranges`,
then the apron block polys, then `_fits` - and none of them answered it. A throwaway monkeypatch over
`M["buildings"]` answered it first try, in one run. This is that, made permanent.

**It OBSERVES, it never restates.** The refusal cause is read off the real `_in_blocked` /
`_near_corridor` / `_hard_clear` as they return; when `_fits` refuses and none of those did, it says
so in exactly those words rather than guessing which of the remaining clauses it was. Same discipline
as `site_justice.py` asking the gate instead of re-implementing it - a diagnostic that re-derives a
rule drifts from it and then tells you the wrong thing with total confidence.

Two notes worth having: `--refused` reporting **"no candidate was ever tested here"** is a different
finding from a refusal - the ground is UNVISITED, so look at the region the placer was given, not at
the keep-outs. And a `--at` miss usually just wants a bigger `--radius`: a re-pack moves things.

## Siting a feature with interacting rules: adjudicate against the GATE, never a re-statement of it

`open_seat` (above) answers "does this fit here?" - geometry only. When a feature's placement is
governed by many INTERACTING rules, that is not enough: the justice works (feature 015) must be
outside the wall, on the way out, past the boundary stone, clear of the community's dead, off the
farmland, on the outcast side, clear of every structure, and inside the map's current view. Use
[`site_justice.py`](site_justice.py):

    python3 site_justice.py pool/provincial-cities/nagahara.json execution_ground --limit=25
    python3 site_justice.py pool/towns/hirameki.json boundary_marker --ground=1620,1900

It proposes seats **cheapest-on-the-frame first** (`frame_cost=0` means the crop is unchanged by
that seat) and adjudicates each one by building a trial manifest and running `check_village.gate()`
on it, reporting the checks that fail there but not with the feature absent.

**The lesson, which generalizes past this feature.** Its predecessor was a scratchpad script that
re-implemented every rule as its own predicate, and it drifted *within a single session*: a
relaxation made to satisfy one map silently persisted and put Nagahara's boundary stone in a field
off the highway. The gate accepted it because the rule it broke was not yet checked, and only the
rendered PNG showed the problem. So a siting tool must never restate a rule - it must ASK the gate.
New rules are then picked up for free, and the tool cannot disagree with the checker. This is the
same trap as "placement and its check must read the SAME manifest source" (below), one level up.
The cheap geometric pass in that file is a RANKING only: it orders candidates to keep the number of
gate runs small, and it never rejects, so a stale heuristic costs runtime rather than correctness.

**The second trap, found the same way (2026-07-26): "adds no new failure" is only HALF of legal.**
The tool's baseline is the gate with the feature ABSENT - so for a feature whose absence is itself a
failure, the very check that governs it is already IN the baseline, and a seat that leaves it
failing adds nothing new and scores as legal. Every candidate stone therefore looked equally good,
and the tool duly recommended the one that put Ubame's dosojin among the west-end shops. `propose`
now also requires a seat to CURE the checks the absence causes, with "curable" derived from the gate
(a check some adjudicated seat clears) rather than declared - so the tool still names no rule of its
own. The general lesson: when an oracle scores a candidate as a DELTA against a baseline, ask what
the baseline is already failing, because a delta cannot see a rule the empty case breaks too.

**Known limit:** label collisions cannot be judged from a manifest - a label box is produced at draw
time, not recorded for a hypothetical placement - so `labels_clear_of_other_buildings` and
`no_label_overlaps` still surface only on regeneration. That is why `punishment_spot` and
`execution_ground` both take `label_above` / `label_xy`.

## Read derived geometry from the MANIFEST, not by re-running the generators

Second-biggest sink in that same profile: **7.6 minutes across three runs of a throwaway analysis
script that re-ran all 17 generators** to compute where trees overlapped buildings. Every one of
those runs was answering a question the manifests could answer directly - the same analysis reading
`pool/*/*.json` takes **0.2 seconds**. The pool JSON is the artifact: outlines, footprints, clump
centers, `tree_crowns`, ditch polylines are all in there. Re-run a generator when you need to change
what it DRAWS; read the manifest when you need to know what it drew. If the geometry you need is not
recorded, that is usually a sign the CHECK needs it too - record it once and both problems go away.

## DRAW ORDER: read this BEFORE changing where anything is placed or drawn

Most of what a Mode B feature gets wrong is not geometry, it is ORDER. A drawing method sees only
what is in `self.M` at the moment it runs, and a placement method avoids only what is in the
registries at the moment it runs - so "tree not drawn on a roof" and "building not placed under a
canopy" are the SAME rule enforced from two different points in the sequence. This map cost four
fail-read-fix cycles to reconstruct on 2026-07-25; it is written down so nobody pays for it twice.

**The three registries, and who honors them:**

| registry | holds | consulted by |
|---|---|---|
| `block_polys` | no-build polygons (field envelopes, the wood, dry plots, the manor court) | `_rect_blocked` tests a whole FOOTPRINT (homestead bundles); `_fits` -> `_in_blocked` tests only the candidate's CENTER (urban packs) |
| `placed` | `(x,y,w,h)` of everything already standing | `_fits` keeps each candidate a half-diagonal + 4px clear |
| `grove_rects` | tree footprints, deliberately kept OUT of `placed` so adjacent groves may abut | `_fits` (same clearance rule), `_east_trees` (garden morning-sun) |

**That `_fits` asymmetry is the trap.** A block poly stops a farmstead whose footprint merely touches
it, but stops an urban building only when its CENTER lands inside - so a wide building can put half
its roof over blocked ground. If a feature must keep whole footprints out, `placed`/`grove_rects`
(distance-based) is the registry that does it; `block_polys` alone is not enough.

**The order a Mode B gen runs in** (Moritono is the clean example):

1. **terrain + water** - fields, channels, streams, pond, marsh
2. **big terrain features** - `forest()` / `forest_patch()`. EARLY, because the settlement is sited
   against them; their FLOOR draws here but their CANOPY is deferred (see 7)
3. **ways** - road, lanes, streets
4. **structures** - `manor()`, `farmsteads()`, urban packs, `place_wells()`, `draft_byres()`,
   `place_kosatsuba()`. Inside `farmsteads()` the bundle path records grove rects first (the garden
   relaxation needs them), then draws yards/gardens/houses, then draws the yashikirin arms LAST
5. **ground cover** - `hinterland()` scrub + marsh (skips structures via `_urban_keepouts`)
6. **communal vegetation** - `village_grove()`. LATE, so its per-crown filter sees every structure
7. **crop** - `crop_to_content()` / `crop_city()`, which first run `flush_stable_yards()` and
   `flush_tree_stands()`: the deferred yard furniture and every wood's canopy draw HERE, against the
   complete map. `finish()` re-runs the tree flush as a backstop for a gen that never crops
8. `title()`, `finish()`

**The two rules that fall out of it:**

- **Must not be drawn ON something?** Run AFTER it, or defer to the flush. Drawing early and letting
  the later feature paint over it hides the overlap instead of preventing it - which is exactly what
  the yashikirin used to do, leaving crowns geometrically under roofs while looking fine.
- **Must RESERVE ground?** Run BEFORE placement AND register in a registry that the placer in
  question actually honors (see the asymmetry above).

**Changing any of this deserves a design pass first.** Read the paths above and settle the ordering
on paper before editing - the failure mode is discovering the sequence one gate failure at a time,
which is what turned a small rule into four fix-fail-read cycles. If a change needs a feature to
move between phases, say so explicitly in the commit: phase moves are the changes most likely to
have effects far from the diff.

## CENTER vs FOOTPRINT: the three ways placement and the checks disagree

The GM, 2026-07-26, after the overlap matrix kept finding things the placer had allowed: *"if
placement is only testing the house's center while the matrix tests its footprint, then maybe the
placement test is wrong? Are there other placement checks which are only checking the center? That
could explain a lot of overlap issues as well as a lot of inefficiencies."* Both halves were right,
and there turned out to be **three** distinct disagreements, not one. Know which you are looking at
before you touch anything.

**1. Center-tested keep-outs (UNDER-restrictive -> overlaps).** `_fits` tested a candidate's CENTER
against `block_polys` and the corridors, so a footprint could hang over blocked ground by up to half
its width. Fixed by SPLITTING the registry: `hard_polys` (crop, pond, bog, a field's own ditches) is
tested against the whole footprint; `block_polys` keeps the center test. **Do not merge them back.**
Footprint-testing all of `block_polys` was tried once and reverted, because it also contains SOFT
reservations - caption bands, civic aprons, fence standoffs - that a footprint routinely overhangs
by a few px, and tightening those cost Nagahara a well and pushed Hoshizora's punishment ground off
its street. The split is the fix; the conflation was the bug.

**2. Circumscribed-circle collision (OVER-restrictive -> wasted ground, and LOAD-BEARING).** Against
`placed` and `grove_rects`, `_fits` still uses half-diagonal circles, not real footprints. For a
46x28 house that is r=26.9 against a true half-width of 23, so two such houses are forced >=57.8 px
apart center to center where true touching is 28. It never permits a real overlap - it just wastes
up to ~2x the spacing, which is a real cause of "the packer says the ground is full" when it is not.

**The waste is real and large - measured on Tango, 2026-08-08.** A wrapper that computed the
diagnostic beside the real verdict (so the map generated was the real one) over 71,860 `_fits`
calls: **38.7% of all refusals come from the circle clause**, and **767 seats are refused by nothing
but the approximation** - a **+57.6%** increase in the pool of legal seats the placers see. That is
per-CALL, not per-building: it means far more choice for every scan, not 57% more houses.

**But do NOT swap it for a footprint test on its own.** Tried the same day: replacing the circles
with an exact axis-aligned box gap takes Tango's gate from clean to FIVE failures, two of them
genuine overlaps (`features_do_not_overlap`, `no_structure_overlaps`), plus a fire tower standing on
a wellhead and a well inside a building. The reason is that a circumscribed circle is
**rotation-invariant**, and that is exactly what has been absorbing item 3 below: houses are drawn
at +/-5 deg and buildings at 90/180 deg, where `w` and `h` swap outright, so an axis-aligned test on
the PLACEMENT dimensions is simply wrong for them. It was partly covering item 1 too - with tighter
packing, buildings landed on wells whose `block_polys` reservation is only center-tested.

**So item 2 is blocked on item 3, not on the cost of re-baselining** - which is what this entry used
to say, and it was the wrong diagnosis. The circles are not conservative padding; they are the
mechanism masking the rotation mismatch, and removing them converts a documented inefficiency into
shipped overlaps. The order is: fix **item 3** so the placer tests the rotated footprint it will
actually DRAW, then item 2 becomes a real `sat_overlap` on real corner quads, and only then does the
pool re-roll. Budget for that re-roll: the naive swap alone already moves Tango +21 houses (+8%),
+20 buildings (+3.2%) and +23 wells (+25%).

**3. Placement tests a DIFFERENT footprint than the one drawn (still open, but now measured).**
`_fits` is called with a farmhouse's BASE rect, but the drawn steading can exceed it - a wealth
render scale, an attached shed, a rotation. So a candidate that genuinely cleared every keep-out at
its placement size laps one at its drawn size, and no amount of fixing (1) reaches it. Hoshizora's
gen already works around this by inflating its hem plots ~8 px (`grow_poly`), which treats the
symptom locally. The real fix is for the placer to test the size it is going to DRAW.

**Two 2026-08-12 findings sharpen it, and one of them is already banked.** A WAY now records its
drawn TREAD (`_record_tread`) beside its soft corridor, and `_fits` tests the whole footprint
against the tread while the clearance keeps its centre test - the split that makes this safe where
footprint-testing all of `block_polys` was not, since a clearance is slack and a road surface is
not. Lanes only, deliberately: the other ways already pad their corridors by hand, and tightening
them cost Tango a public well. No pool manifest moved.

**But the BUNDLE path never reaches `_fits` at all**, which is the bigger half and was not visible
until a cohort went looking. `_bundle_fits` seats a homestead from its own geometry, and the house
inside it is offset from the seed point AND scaled by the wealth/length jitter - so the rect the
placer clears is neither the size nor the position of the rect that gets drawn. Instrumented on a
failing map: `_fits` was never called at the offending farmhouse's position with its own w/h, and
12 of 24 cohort maps put a house corner on a lane at the authored clearance. Testing the drawn house
rect inside `_bundle_common_fits` fixes it in three lines - and re-rolls Ikegami, Kuwabata, Tanada
and Hoshigaoka, breaking Hoshigaoka's gate. So it is a reviewed pool job (one `settlement-review`
per map), and the natural companion to item 2's collision-circle swap: do them in one re-roll rather
than two.

**The general lesson.** A point test is right for a SCATTER (each tuft is a point) and wrong for
anything with an extent. The same trap bit the ground-cover tiler: `near_ring_cropland` sampled a
cell's center and four corners, which a small keep-out sitting against an edge MIDPOINT slips
between - that is how a wellhead ended up 1 px inside a hatake plot. Region-vs-region helpers
(`quad_hits_poly`, `quad_hits_seg`, `point_quad_dist`) exist now; use them rather than adding sample
points.

## Centers, footprints, and aggregates: which one a rule is allowed to use

The GM, 2026-07-27, after the boundary-stone defect: *"I'm not sure it EVER makes sense to use a
center instead of a footprint... we've had a lot of bugs slip through because of using centers,
which makes me wonder whether we should just ban them."* An audit of all 42 center-distance sites
and 29 `point_in_poly`-on-a-center sites says: a blanket ban would break three things that are
right, and would still have missed the defect that prompted it. **Four families. Say which one your
rule is in, in a comment, at the point of the test.**

| family | measure | why | examples |
|---|---|---|---|
| **Gap VERDICT** - "N ft of clearance", "these must not overlap" | `edge_gap` / `within_edge_gap` / `sat_overlap` on real rotated corners. **Never** a center, **never** a circumscribed radius | the answer is a distance you could pace out between two walls | `execution_ground_outside_the_settlement`, `town_has_cremation_ground`, `burakumin_quarter_segregated`, `execution_ground_clear_of_the_dead`, `wells_among_dwellings`, `farm_sheds_attached` |
| **CLASSIFICATION / counting** - "which ward", "how many inside the wall", "what share of this quarter is civic" | center, deliberately | a building belongs to ONE ward; footprint-testing double-counts a building on a seam and the ward populations stop summing to the town | the 29 `point_in_poly(b["x"], b["y"], wall)` sites |
| **ASSOCIATION / reach** - "is there a well within reach", "do monk houses cluster at their temple", "is this yard on the water" | center, deliberately | the tolerance (75-480 px) dwarfs the footprints and the question is neighborhood membership, not clearance; converting them re-tunes ~21 calibrated constants to fix nothing | `settlement_dwellings_watered`, `city_monk_houses_by_their_temple`, `_ty_on_water` |
| **PREFILTER** in front of an exact test | circumscribed radius, deliberately | over-stating an extent can only ADMIT a pair the exact test then rejects - the index prunes, it never decides. Tightening these would start rejecting before the exact test runs | `fire_tower_standoff`, `no_structure_overlaps`, `city_house_doors_unblocked`, `within_edge_gap`'s own prefilter |
| **POINT FIXTURE** - a distance to a gate, torii, sluice gate or bridge | point, unavoidably | these are recorded as bare `[x, y]` in the manifest and have no footprint to test. If one ever gains `w`/`h`, the rules that measure to it become gap verdicts and move to row 1. **The kido left this row on 2026-07-27**: it never had `w`/`h` either, but it records `parts` - each drawn rect's rotated corner quad - and `guard`, so it always had a real footprint that nothing read. The trigger condition is therefore not "gains `w`/`h`" but "records ANY drawn extent"; check the record, not the two field names | `city_inspection_station_at_each_gate`, `city_kosatsuba_per_gate`, `city_temple_approach_has_torii`, `wall_towers_evenly_spaced` |

**The three conventions that were live before this, and what each cost.** Raw center-to-center
understates clearance by the sum of both half-extents, so a rule promising 120 ft delivered ~60;
`0.5 * math.hypot(w, h)` is the half-DIAGONAL, over by up to 41% on a square and more on a long
rect; `max(w, h) / 2` is the same error differently sized. The approximations' error **flips sign**
with the rule - subtracting too much makes a "must be far" rule strict and a "must be near" rule
lenient - so they are not even a uniform safety margin.

**The ratchet, not the doc.** `test_gap_verdicts_read_footprints_not_centers` plants two features at
exactly the offset where the conventions disagree and pins which verdict is right. Verified to have
teeth: of its nine entries, reverting the helper to raw centers breaks six and reverting it to
circumscribed radii breaks the other three - every entry is caught by one revert or the other. **Add
an entry when you add a gap rule** - a rule that lives only in this table has already been proven
not to hold.

**THE SWEEP IS DONE; DO NOT REDO IT, EXTEND IT.** Two passes, because the first one's METHOD had the
same shape of blind spot as the bug it was hunting. Pass 1 grepped `math.hypot(...["x"]...["x"]...)`
and found 42 sites across 34 checks. That regex cannot see a record compared against an unpacked
`(x, y)` tuple, which hid a second tranche of 45 sites across 36 checks - and one of them,
`tanning_yard_clear_of_dwellings`, was a live 120 ft gap verdict reading 150 ft where the yard's own
corner stood 76 ft from a farmhouse wall (Tango). Everything else in the second tranche classified
as point-fixture, association/reach, classification, or one SIDE test
(`dwellings_above_field_drain`, whose "is the house clearly on the wet side" question is a bearing,
and deliberately center-based). If you add a distance rule, put it in the right row of the table
above and give it a ratchet entry - that is cheaper than a third sweep.

**One measurement, not several.** `edge_gap` is now the only exact footprint-gap helper.
`_fr_gap`/`_fr_poly` - feature 016's own, written before it and doing the same job by the same
method - was folded in on 2026-07-27. Two CORRECT helpers for one question is how the three wrong
conventions got started; if you find yourself writing a third, use `edge_gap`.

**And a fourth axis, which no footprint discipline reaches: AGGREGATE PROXIES.** The boundary-stone
defect was not a footprint bug. `dist(stone, centroid) < dist(ground, centroid)` would stay green
with perfect geometry on both sides, because the centroid - an average of every dwelling - was
standing in for the built EDGE, and a settlement is not a disc. **Never let an aggregate stand in
for the distributed thing a verdict is about.** Measure to the nearest member (or, where the
settlement has a rampart, to the wall - the edge it actually has). `execution_ground_on_the_outcast_
side` still dots against the centroid and that is correct: a BEARING is an aggregate question. A
DISTANCE is not.

**Known debt, recorded as debt rather than design:** `_fits` center-testing `block_polys` (item 1
above). The honest reading is that those polygons are drawn wrong - keep-out plus slack baked in,
with the center test handing the slack back - and the principled fix is to shrink them to the true
keep-out and footprint-test. That re-tunes margins pool-wide, so it is a separate pass.

## Adding a new map feature: the KEEP-CLEAR CONTRACT (read this before writing the glyph)

The GM's observation, 2026-07-25, after the martial hall shipped sitting on Tango's ring road:
*"every time we add a new type of thing, I end up looking at the map and saying 'oh, this new thing
should not overlap with X'."* That is now a solved problem, and this is the whole of what you have
to do.

**One registry, and everything follows from it.** A new footprint feature goes in
`_OVERLAP_STRUCTS` (check_village/common_01_geometry.py) - or, if it is MEANT to overlap something, in
`_OVERLAP_EXEMPT` with the reason. You cannot forget: `every_feature_classified_for_overlap` fires
when a generator emits a feature key nobody classified. Membership alone then gates the feature off
**fifteen hazards** - the wall, the moat, the road, streets and alleys, streams, channels, the
cargo canal, the pond, manor walls, religious halls, gate furniture, torii arches, the ring road,
every other solid structure, and the 14px government-office standoff - because every one of those
checks builds its footprints from the registry via `solid_structs(M)`.

**The failure mode this replaced.** The `no_structure_on_*` battery was always registry-driven, but
a handful of keep-clear checks predated it and hand-listed their own keys. A feature could be
correctly classified, correctly cleared of all thirteen battery hazards, and still sit on the ring
road - because `ring_road_kept_clear` was reading eight keys nobody had updated. A check that never
sees your feature looks exactly like a check that passes, so this was invisible until the GM looked
at a rendered map. Four such checks now read `solid_structs(M)`: `ring_road_kept_clear`,
`city_government_offices_dont_abut`, `city_wells_in_block_interiors`, and the merchant-estate
court test.

**The ratchet.** `test_checks.py::test_every_solid_struct_is_gated_off_every_hazard` plants one
instance of EVERY registered key squarely on EVERY hazard and demands the hazard's check fire. If a
keep-clear check ever falls back to a hand list, that test names both the key and the hazard.
Verified to have teeth: reverting `ring_road_kept_clear` to its old list fails it with 21 keys
listed. **Adding a hazard row to `_HAZARDS` extends the contract to every existing feature at
once** - that is the cheap way to answer the next "should not overlap with X".

**The same contract covers CAPTIONS** (GM 2026-07-26). A feature protected from every solid
neighbor is still not protected from a label dropped on top of it, and
`labels_clear_of_other_buildings` had its own hand-written list of ~22 keys that had already fallen
behind twice - `martial_halls`/`dojos` had to be remembered into it, and a day later
`punishment_spots`/`execution_grounds`/`boundary_markers` were absent, so a foreign caption over an
execution ground shipped green. `_LABEL_GROUP` now maps each manifest key to the caption GROUP a
label must name to be allowed over it, `_LABEL_EXEMPT` excuses the few that do not need protecting
(with the reason), and `every_solid_feature_classified_for_labels` fires when a key is in neither.
The permission side is derived from the same registry - a group's name IS its caption word
("brewery", "martial hall", "execution ground") - so a classified feature can caption itself with
no second list to remember. The named branches in `_label_allows` survive only for SYNONYMS: a
caption reads "Temple of Benten" or "Governor's Mansion", not "temple" or "governor".

**RECORD A FOOTPRINT THE EXTRACTOR CAN READ - classification is only half.** GM, 2026-07-27: *"in
general we always want overlap checks to use full footprints."* `matrix_extents` reads `x`+`w`/`vw`,
a `poly`/`outline` ring, a stroked polyline, or a `parts` list of rotated quads. A record matching
NONE of those is extracted as nothing, and a feature the extractor never reaches is invisible to
every matrix check in both directions no matter how carefully it is classified and mounted - which
looks exactly like a feature with nothing wrong. Three keys were in that state until an audit went
looking (`kido`, which records only a center and its parts; `roads`, the multi-road list;
`flower_fields`, whose ring is called `outline`, not `poly`), and the ward gate had been hiding a
notice board sitting on its guard box and two guard boxes cut by their own ward fence. The audit is
cheap and worth re-running whenever a new key appears - per manifest, compare each classified key's
record count against `collections.Counter(k for k, *_ in matrix_extents(M))`; any key with records
and no extents is blind. And where one glyph draws SEVERAL rects, record them as `parts` (rotated
corner quads) rather than a bounding box, and split out any part that does not share the whole
feature's permissions - a gateway may stand on the fence it pierces, its watch box may not.

**The same disease turns up in PLACEMENT PROBES, where it is quieter.** `place_punishment_spot`
probes candidate boxes for its own caption before committing to one, and that probe had its own
hand-written list of nine manifest keys - `dye_yards` was never in it, so when a reflow put Minami's
punishment ground beside the dye works the probe reported a clear box and the gate reported a caption
on a dye works (2026-07-27). It now iterates **any manifest list of dicts carrying w/h**, so nothing
has to be remembered into it. Two sibling lessons from the same defect, both worth generalizing:

- **A probe must measure the box the CHECK will measure.** That probe sized its trial box with
  `_text_width` (the PIL glyph measurement) while `labels_clear_of_other_buildings` reads the box
  `_record_label` writes (`len(text) * size * 0.55`), which is ~2px wider per side at caption size. The
  probe cleared, the gate did not. Same rule as "placement and its check read the SAME manifest
  source", one level down: geometry, not just data.
- **A probe that gives up silently is worse than no probe.** When none of its nine candidate rings
  was clear it left `label_xy` as None and the caption fell back to the default seat - on top of three
  dwellings. It searches sixteen rings now, but the shape of the bug is the fallback, not the number.

**And a caption that is DEFERRED cannot be reserved by reading it back.** `place_caption` seats at
`finish()`, so `s.M["labels"][-1]` right after the call returns some *earlier* label, and a gen that
reserves that box reserves the wrong ground (tango's theater stage, 2026-07-27). Worse, the ladder
seats a deferred caption against a map that is already full, so it takes the LEAST-BAD spot rather
than a clear one. A deferred caption's ground has to be reserved by hand, BEFORE the packs run.

**So the checklist for a new feature is:** write the glyph; record it under a new manifest key; add
that key to `_OVERLAP_STRUCTS` and give it a caption group in `_LABEL_GROUP`; run the suite. If the
feature needs a keep-clear rule no existing hazard covers, add a hazard row rather than a bespoke
check with its own key list.

**The placement side, which the GM asked about next.** `_fits` tests an urban candidate's CENTER
against `s.bound`, `block_polys` and the corridors, and whole footprints only against `placed` /
`grove_rects` (see DRAW ORDER below). `open_seat` now closes the half of that gap that matters:
it verifies the whole FOOTPRINT against **the bound**, because a bound is a hard edge (the
ring-road loop, the wall) and a footprint crossing it is drawn on the patrol road at any overhang -
which is exactly how the martial hall got its seat. `block_polys` and corridors stay center-tested
even there, deliberately: those are soft RESERVATIONS (a label band, a civic apron, a fence
standoff) that a footprint routinely overhangs by a few px, and tightening them was tried and cost
Nagahara a well and pushed Hoshizora's punishment ground off its street. The bound-only rule
changes nothing in the pool. `footprint=False` gets the old center-only answer, i.e. what a pack
would take. (`test_open_seat_refuses_a_seat_whose_FOOTPRINT_crosses_the_bound` holds this.)

**Gap rules are in the table now, but one row each.** A clearance rule ("14px of daylight", not
"no overlap") is the other shape a keep-clear rule comes in, and it broke identically:
`city_government_offices_dont_abut` had never seen the martial hall or the dojo, so both shipped
inside its standoff. A `_HAZARDS` row expresses a gap simply by planting the struct NEAR the hazard
instead of on it, so the contract covers it - but unlike the overlap hazards, each new distance
rule still needs its own row. A row's fifth field lists keys the rule DELIBERATELY does not govern
(the funerary compounds are excluded from the office standoff: a clan crypt against the yamen is a
real adjacency), so a deliberate exclusion is visible in the contract rather than hidden in a
check.

## A side effect is not a rule - check what was actually DECIDED before you build on it

The toe marsh spanned the canvas edge to edge for weeks, and three separate pieces of work treated
that as the settled shape of wet ground: a routing rule, four re-routed connectors, and a claim to
the GM that "a real valley floor has a dry footslope on at least one side" offered as though it were
research. The GM asked where both halves came from. Neither survived:

- **The width was never decided.** It arrived with the 2026-07 fix that made the toe a CONTOUR band
  so it would rotate with the fall - that fix was right and the rotation was its point; the extent
  came from the canvas corners because that was the easy way to write the polygon. The only stated
  rule was `marsh_on_low_ground` (the marsh is downhill of the field), and this file's own Akagahara
  note already recorded the opposite of wall-to-wall wetness: low ground beside the drain that sits
  at rice height is DRY, and "do not fix the gap".
- **The justification was invented.** The footslope claim was a plausible-sounding generalization
  with nothing behind it. Under the record-the-why rule that makes it not a finding at all.

The research the GM then asked for settled it in the opposite direction from the code, and the fix
is now in `research/water.md` ("The wet toe is as wide as the FAN"): an alluvial fan's spring line
follows the FAN's toe, and a floodplain's backswamp is bounded by its natural levees - wet ground is
FEATURE-bounded in both landforms. `toe_band` derives its width from the ground the fan waters.

**Two transferable rules.** First, when a feature's extent comes from the CANVAS, suspect it: a
canvas is not a fact about the world, and every other feature here is derived from something on the
map. This is `feedback_derive_dont_pin` one level up - not a pinned coordinate but a pinned FRAME.
Second, and more expensive: when you are about to build on a property of the engine, check whether
anyone decided it. Two of the four connector re-routes it caused were pure waste - restored to their
original routes the same day, once the width was right - and they were re-routes of the GM's own
maps, each with a review pass spent on it.

## Declared overrides: a map may break a rule, but only IN WRITING

Every placement rule in this engine is a GENERALIZATION, and a specific place is allowed to have a
specific history that beats it. Tango's samurai take the southeast because the Emperor lies that
way, which pushes the outcast quarter opposite its own tanning yard. Hirameki's walls were thrown up
in a hurry when a war turned an interior county into a border one, which is why that town looks
non-standard in several ways. The GM's rule (2026-07-27): **rules and checks are overrideable - and
an override must carry a documented explanation.**

    s.meta(waivers={"tanning_yard_on_the_outcast_side": "The Emperor lies southeast of Tango ..."})

The gate then prints `WAIVE <check>` instead of `PASS`, lists every waiver again in a closing
summary, and keeps the name out of the failure list. Two meta-checks keep the hatch from rotting:

- **`waivers_are_documented`** - the value must be 60+ characters of actual REASON. "by design" and
  `True` both fail. The waiver text is the only record that the map broke the rule on purpose, so it
  states the place's history, not the fact of the exemption.
- **`waivers_are_live`** - the waiver must name a check that ACTUALLY FAILED on this map. A waiver
  whose defect was since fixed, whose check this scale never runs, or whose name is a typo is stale
  and fails. Waivers therefore rot loudly instead of accumulating into a map that is quietly exempt
  from rules nobody remembers it was breaking.

Neither meta-check is itself waivable, or the hatch would swallow its own guard
(`test_the_waiver_meta_checks_cannot_themselves_be_waived`).

**The process lesson behind the waivers** (GM 2026-07-27), which is worth more than the mechanism:
**lock the rules in against ORDINARY settlements first.** Tango and Hirameki were both drawn early
and both are atypical - Tango's samurai take the southeast because the Emperor lies that way,
Hirameki was walled in haste mid-war when a county turned into a border - so for a long time the
defaults were being bent to fit the exceptions instead of the other way round. Build the normal cases
until the rules are settled, then let the unusual ones earn waivers.

**When NOT to reach for it.** A waiver is for a place with a REASON, never for a map that is simply
inconvenient to fix, and never as a way to ship a red gate. If you find yourself writing the reason
and it is really "another session owns this file" or "re-siting is a lot of work", the honest move is
to fix the map or ask the GM - the mechanism is built to make that distinction visible, so using it
to paper over the second kind turns the whole audit trail into noise. And when a rule genuinely
needs to bend for a whole CLASS of maps rather than one place, change the rule, not each map.

**Freeze the pre-waiver manifest as a regression fixture.** A waived map no longer fails, so the
check has no live map holding it honest. Drop the manifest as it stood BEFORE the waiver into
`pool/regressions/` with a `_regression` block (see
`tanning_yard_on_the_outcast_side_fires_on_the_pre_waiver_tango.json`) so a refactor that neuters
the check is still loud.

## When a check is slow, INDEX it - do not coarsen it

The gate's cost is dominated by a handful of checks that ask a local question with a global scan.
Profile before guessing (`cProfile` around `check_village.gate` on `tango.json`, the worst case):
2026-07-25 found `city_fan_heads_quilted` testing ~3,000 canal-side samples against EVERY plot
polygon and ditch (14M `seg_dist` calls, ~58% of a 17s city gate) and `structures_clear_of_dry_plots`
testing every structure against every dry plot (3.5M `segments_cross` calls). Both were fixed with
`GridIndex` (a uniform-grid spatial index in `check_village/common_02_overlap_policy.py`): insert each feature
under the cells its influence bbox touches, query the cell, then run the SAME exact test on the few
candidates. Result: Tango 17.3s -> 2.9s, whole-pool gate 34.1s -> 11.8s, `make done` ~2min -> 77s,
with **byte-identical verdicts on all 695 manifests** (pool + regression corpus).

The rule that matters: **the index prunes, it never decides.** It is always tempting to make a slow
check cheap by making it coarser - testing a bounding polygon instead of the real features, sampling
fewer points, raising a tolerance. That trades correctness for speed and the loss is invisible until
a real defect slips through. Indexing costs ~15 lines and changes no verdict, so there is no reason
to reach for coarsening first. (Concretely: `structures_clear_of_trees` must test the recorded
CROWNS, not the stand outline, because placement drops crowns individually - an outline test would
fire on trees that were deliberately never drawn.)

Verify an optimization the same way: capture `sorted(gate(M))` for every manifest in `pool/**` before
the change, re-run after, and diff. Anything but "NONE" means the optimization changed behavior.
Run that sweep with `-n auto`-style parallelism or in the background - serial it is ~13 minutes.

### A `GridIndex` box is a COST, so clamp it - on insert AND on query

`GridIndex` allocates a dict entry per 120 px cell of the box it is handed, in both axes. That is
fine for anything on the map and catastrophic for anything that is not: the regression fixture
`city_geometry_within_canvas_fires_on_a_stray_vertex.json` plants a wall vertex at **9,000,000** on a
3,200 px canvas, so the moment `wall` became a SOLID in `OVERLAP_CLASS` and got stroked into quads,
one feature asked for ~5.6 billion cells. The gate ate gigabytes of RAM and the GM had to kill it by
hand (2026-07-26). **Negative fixtures contain deliberately insane geometry - any new code that
consumes raw manifest coordinates will meet it.**

Two rules, and the second is the one that is easy to half-do:

1. **Clamp the index box to the canvas** (`meta.W`/`meta.H`, generously - a couple of canvases of
   slack). Clamping only shrinks, and a polygon's on-canvas part is always inside the clamped box, so
   no real overlap can be lost. Geometry wholly off the canvas is skipped; that is
   `city_geometry_within_canvas`'s business, not the overlap matrix's.
2. **Clamp the QUERY box too.** `near_rect` walks the cells of the box it is *given*. Clamping only
   the insert leaves the query iterating exactly the same billions of cells - which is precisely the
   half-fix that shipped first here and looked plausible for a whole turn.

`test_matrix_survives_geometry_far_off_the_canvas` in `test_checks.py` is the guard, timed rather
than structural on purpose: the failure mode is unbounded work, and the correct-vs-broken margin is
a fraction of a second against effectively forever.

## Batch the rendered-map inspection

Reading a map means: render -> crop the region(s) of interest -> Read the PNG. The turn-latency
killer is doing this serially, one crop per turn (`crop -> Read -> crop -> Read ...`). ~78% of
wall time is model-turn latency (root CLAUDE.md, 2026-07-20 profile), so each extra round-trip is
pure cost. Instead: in ONE Bash call, crop EVERY region you want to look at (all four viewports of
a defect, before/after of several maps, the toe + the top + a control), then Read them together in
the next turn. A footbridge review that touched 3 maps should be ~2 turns of imagery, not ~10.
**Use [`crop_map.py`](crop_map.py) rather than re-writing the arithmetic** - it reads the viewBox
itself and takes as many regions as you like in one invocation, which is the batching win made easy:

    python3 crop_map.py pool/towns/hoshizora 1600,900,220 1200,400,150   # x,y,radius (world coords)
    python3 crop_map.py pool/hamlets/moritono --box 2100,150,2418,760 --zoom 1.5
    python3 crop_map.py pool/villages/ueda --whole --zoom 0.4            # whole map, downscaled

It prints one path per line - feed them straight to Read, together. (The conversion is
`(coord - viewBox_origin) * (png_w / viewBox_w)`; it was hand-written five times in one session,
once wrong, which is why it is a script now.)

## Invoking a review agent: SCOPE it, SPLIT it, and launch it EARLY

`settlement-review` is mandatory before a Mode B map ships, and it is also the single most expensive
thing a session waits on. Measured 2026-08-08, on a change that resized some captions: one agent,
two maps, a full audit - **12.3 minutes, 22% of the whole task's wall clock**, with this session idle
for 11.4 of them. The findings were right; two of the five had nothing to do with the change and had
been sitting in the pool for weeks.

Three rules, all of them free:

- **Say the SCOPE.** The agent now takes `DELTA: <what changed>` and reviews the change, whatever the
  re-pack moved, and whatever the change made incoherent - skipping the spelling/twin/nuisance/traffic
  sweeps and saying which it skipped. Reserve `FULL` for a new or heavily-rewritten map. A caption
  resize is a DELTA.
- **One map per agent, launched in parallel.** The sweeps share no work across maps, so handing two
  maps to one agent just serializes two audits behind one notification.
- **Launch it the moment the maps are final** - before the visual pass, the docs and the commit, not
  after them. Everything you do while it runs is free; everything you do after it is added on.

Same three rules apply to `building-review` and `backstory-review`.

## Run the cheap linters BEFORE the full gate

`make done` runs lint -> format -> typecheck -> test+coverage and STOPS at the first failure, so a
trivial formatting or type slip makes you pay a full ~1-min gate run to discover it, fix, and pay
again - the failures surface one per gate run, not all at once. After writing engine code and
BEFORE `make done`, run the seconds-long prefix yourself:

    python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy

That catches format + lint + type errors in one cheap shot. Only then spend the gate run on tests
+ coverage. (The old warning here about local names colliding "in the huge gate() scope" retired
with feature 022 - gate() is a registry of segment functions now, each with its own scope.)

## The gate is a REGISTRY - adding a check, and running one check by itself (feature 022)

`gate()` is no longer a 12,944-line function: it is a small driver over `GATE_SEGMENTS`, an
ordered registry of ~1,375 segment functions (per-check granularity since features 023/024) whose order IS the legacy execution order. What this
buys and how to work with it:

- **Run a subset**: `gate(M, only={"check_base_name", ...})` executes just the segments that can
  emit those names plus their dependency closure (median 7 segments), with verdicts guaranteed
  identical to the full run. Unknown names and META checks (`META_CHECKS` - whole-run state like
  `waivers_are_live`) raise ValueError rather than silently running nothing.
- **The regression replay runs targeted** (`test_regressions.py`): each fixture verifies only its
  `_regression.fires` (meta names fall back to the full gate). This is what took the 210
  frozen-city fixtures from ~480 s to ~58 s serial. The fixture format is unchanged.
- **Adding a check**: write a new `_seg_NNNN__<name>` -style function next to its neighbors, in whichever `check_village/segments_*` file covers its theme (`check_village/CLAUDE.md` is the index) (body
  reads its inputs as keyword params defaulting to `_UNBOUND`, returns `_kept(locals(), <names it
  binds>)`) and add its `_GateSeg` row at the right position in `GATE_SEGMENTS` - the row's
  `checks` names what it emits, `needs` what it reads from earlier segments, `writes` what it
  provides. Then extend `test_fixtures/gate_check_names.json` (the registry-pin test compares the
  two). The `every_feature_classified_*` and KEEP-CLEAR contracts above are unchanged.
- **The migration tooling** (one-shot, retired): `specs/022-gate-check-registry/` holds the
  transformer, the oracle sweeps (`oracle_sweep.py capture/compare/targeted`), and research.md
  with the dataflow model and the three holes the sweeps caught (helper-closure mutation,
  upward-exposed reads vs raw loads, comprehension-target scoping). Read R9 there before any
  future dataflow-over-gate work.
- **Never trust a dependency edge you have not swept**: the targeted-vs-full sweep over all 791
  fixtures is the empirical guard on the closure rules. If you change `needs`/`writes` semantics
  or add segments with unusual dataflow, re-run `oracle_sweep.py targeted`.
- **The city/capital battery is per-statement segments too (feature 023)**: 022 left the whole
  urban battery as ONE 1,040-statement segment (it was a single `if scale in ('city',
  'capital'):` statement in the legacy gate, so statement-granularity could not divide it) under
  a clause-12 debt annotation. Feature 023 paid the debt: `_seg_0563_NNN__<name>` segments carry
  the guard IN THE BODY (`if scale in ('city', 'capital') and ...:`; a few keep deliberate
  nested guards under `# noqa: SIM102` where a comment bank sits under the guard) so bodies
  moved verbatim, then ruff's SIM102 autofix combined the guards with identity re-proven by the
  oracle battery afterwards. Adding a
  city/capital check = write a small `_seg_0563_NNN`-style function with its guard in the body,
  same registry row mechanics as any other segment (tooling + census: `specs/023-split-city-
  mega-segment/`, retired one-shot like 022's).

## Update the predictably-affected tests in the SAME edit

Touching a `settlement/` method breaks its unit tests deterministically - you know which ones
before you run anything. `channel_footbridges` has `test_settlement.py::test_channel_footbridges_*`
and the `test_checks.py::_footbridge_map` fixture; changing placement semantics (e.g. "a plank now
needs cultivation on both banks") means those setups need cultivated ground added. Update them in
the same turn as the engine change, don't discover the breakage via a failed pool sweep. Grep for
the method name in `test_*.py` before editing.

## Converge on a new rule with ONE pool-wide dry-run, not one variant per turn

When adding a placement rule or check, the pool IS the test bed: the right predicate is the one
that flags exactly the defective features and spares every good one across all 13+ maps. Don't
test candidate rules one-per-turn against one map. Write ONE script that loads every pool manifest
and, for each candidate predicate (marsh-only vs both-banks-cultivated vs cultivated+village+dike
...), prints what each would drop/keep per map - then read it once and pick the winner. This is how
the footbridge rule's edge cases (polder toe-planks cross onto the DIKE; village-edge planks cross
to houses; dry-to-wet crossings) surfaced in one pass instead of five.

## A check that never RUNS looks exactly like a check that passes

Three separate times in one feature (2026-07-25, the water-flow work) the defect was **not a bad map
but a check that was silently not running**, and each time the gate was green throughout. The shape is
always the same: a rule gated on an OPTIONAL declaration that almost nothing declares.

- `meta(down_deg)` gated the whole drainage-slope block, `downhill_direction_valid` and
  `marsh_on_low_ground`. The two provincial cities declared none, so they were never validated by any
  of them - the code even said so out loud: *"maps without the tag are exempt (slope unknown)"*.
- The legacy `meta(downhill)` gated `channels_flow_downhill`. Only **2 of 17** maps declared it, so 15
  skipped that check entirely.
- `moat_channels_flow_with_current` needed a stream END within 35px of the moat ring. Nagahara's river
  ends off-map (it is the MOAT's ends that meet the river), so it **never ran there at all** - and on
  Tango it ran only because the feeder happened to be drawn before the outfall.

**The cheap diagnostic.** Coverage does not catch this: the gated branch is exercised by SOME map, so
the lines are covered while other maps never reach them. What catches it is asking, per map, whether
the check appears in the output at all:

    python3 -m check_village pool/<type>/<map>.json | grep -c "<check_name>"     # 0 = never ran

Run that across the pool for any check whose body sits behind `if meta.get(...)` or
`if <thing> is not None:`. A `0` on a map that plainly has the feature is the bug.

**The ratchet.** When a rule needs a declaration to work, add a check that the DECLARATION EXISTS -
otherwise the rule is optional in practice no matter how firmly it is written.
`settlement_declares_a_land_fall` is the model: it demands a map-level `down_deg` or a per-field fall
on every paddy, and says in its own message that a map declaring nothing SKIPS every drainage rule
while still showing green. Prefer this to widening the gate quietly.

## Build check-test manifests with the fixture builders

`test_checks.py` hands `gate()` hand-built manifests carrying only the keys the check under test
reads. That focus is right, but it has a tax: a record often must carry a key some OTHER check
indexes unconditionally (a threshing yard's `of`, a grove's `face`), and omitting it does not fail
your test - it raises a `KeyError` from an unrelated check, costing a fix-and-rerun cycle to
diagnose. Use the builders at the top of the file (`manifest`, `house`, `yard`, `garden`, `well`,
`grove`, `vgrove`, `bldg`); they carry the required keys and take `**kw` overrides.
`test_fixture_builders_survive_every_check` runs every check against one of each and is what keeps
them complete - if a check starts indexing a new required key, it fails there once instead of
ambushing the next person to write a test.

## Placement and its check must read the SAME manifest source

A recurring engine trap (footbridges 2026-07-22; recorded in [`settlements.md`](settlements.md)
under "PLANK BRIDGES"): the generator in `settlement/` and the validator in `check_village/`
must classify terrain from the SAME data, or they disagree and a feature the generator dropped is
demanded by the check (or vice versa). Read the MANIFEST fields (`M["fields"]` outlines +
`M["dry_plots"]`), NOT engine-internal blocking lists like `self.field_polys` that some gens leave
empty. When a new check pairs with new placement logic, factor the shared predicate so both sides
provably use it.

## A dirty tracked manifest with no code change behind it: suspect the MEASUREMENT, not the generator

`title()` sizes its placard by measuring the name's glyphs with PIL (`_text_width`), and that
measurement is recorded in the manifest - so anything environmental that shifts it by a fraction of a
pixel rewrites every titled map's bytes with no code change in the diff. That is what a container
rebuild did on 2026-07-25: PIL picks its layout engine by what is installed (RAQM where libraqm is
present, BASIC where it is not) and the two disagree at the subpixel level, so all 16 titled
manifests came back dirty at once. The fix was to PIN the engine - see `_text_width`'s docstring and
`test_text_width_is_pinned_to_the_basic_layout_engine`, which holds the pin so it cannot come loose
silently - and the pool is byte-reproducible on any container again.

The transferable part is the DIAGNOSIS, because `render-sync` reports this and a genuinely
nondeterministic generator in the same words. Diff the manifests SEMANTICALLY, key by key
(`json.load` both sides and compare) - never as text, since these are single-line JSON files where a
text diff always shows the whole file and tells you nothing. Only `title`/`scalebar` moving, by a
hair, uniformly across every map, is a measurement-environment signature; a house, a ditch, a crown
or a count moving is a real bug. And when a recorded value depends on something git does not carry,
pin the dependency rather than re-recording the drift - re-recording just waits for the next rebuild.

## An unmet ASK is a defect, and the gate now says so

`_shortfall` has recorded requested-vs-landed per placement run since 2026-08-05, and recording
turned out not to be enough on its own: Shiro Daika authored **283 frontage seats and drew 129**
behind a completely green gate, because nothing ever read the record back. The GM found it from
the render (*"they look more spaced out than I expected"*). `placement_runs_meet_their_ask` now
fails any run that lands under **60%** of its ask. The line is calibrated from the pool: the only
two shipped maps that miss an AUTHORED count miss it by a hair (Ubame 21/23, Hirameki 13/14),
while every genuine drift sits far below.

Three ways to clear it, and the failure message names all three:

- **Make room** - the honest fix when the ground really should hold them.
- **TRIM the ask** to what the ground holds. Slicing the item list to a PREFIX is
  geometry-preserving: a refusal does not consume an item, so a run handed exactly the number it
  used to place seats the same buildings in the same spots. Verified byte-identical.
- **`fill=True`** where the number was always a capacity budget ("place up to N"), which is the
  city gens' district-fill idiom. It is report-only in BOTH `pack` and `frontage` - it suppresses
  the record and changes no geometry - so declaring it on the three provincial cities moved only
  the `shortfalls` key of each manifest.

## A DIAGNOSTIC that restates what it observes will lie to you, or die

Three probes in one session, two of them wrong in ways that cost a full round trip each:

- `why_placed.py`'s `_fits` wrapper had **re-declared `_fits`'s parameter list**, so the day
  `_fits` gained a keyword the tool died with a `TypeError` in the middle of the gen it was
  supposed to be observing. It takes `*a, **kw` now. Same rule as `site_justice.py` asking the
  gate instead of re-deriving it: a tool that OBSERVES must not re-declare the thing it observes.
- A hand-rolled probe listed, for each refused seat, every corridor **covering** it - which is not
  the same set as the corridors that **refused** it, because it ignored `skip`. It named the very
  street being fronted as the culprit. Patch the real predicate and read its verdict; do not
  reconstruct the verdict beside it.
- The next probe measured refusals **near a point** rather than **inside the run**, so it charged
  a frontage row for refusals belonging to the pack that ran after it. Attribute by CALL (wrap the
  helper and tag everything inside it), not by proximity.

The good version of this is cheap: wrap `_shortfall` and walk `inspect.stack()` for the frame in
the GEN file, and every run is attributed to the exact gen line that wrote it - which is how 10
call sites across three shipped cities got classified in one run.

## The collision circle is now blocking FEATURES, not just wasting ground

The "CENTER vs FOOTPRINT" entry above records the circumscribed-circle collision as a documented
inefficiency: `_fits` measures a candidate against `placed` with half-diagonal circles, so a 46x28
house is forced 57.8 px from its neighbor where true touching is 28. Two 2026-08-11 findings move
it from *inefficiency* to *blocker*, and they are the same finding twice:

- **The capital cannot seat a wellhead.** Two machi blocks sit at 27 and 29 households per well
  against a cap of 26, and `open_seat(..., well=True)` refuses a probe at 12, 10 AND 8 px anywhere
  in either block. Tightening the derived well grid does add wells, but they land close enough to
  existing ones to trip `wells_not_clustered` before the deficit clears - the two rules meet with
  one household of daylight between them. Trimming the covering packs does nothing: both are
  capacity-bound and already placing fewer than asked.
- **The capital's new paddy cannot seat a farmhouse.** Ten positions around the field envelope,
  tried three ways (the perimeter ring, `open_seat`, and `try_place` directly): **6 of 10 refused
  by the collision circle**, 3 by a corridor, 1 by a keep-out.

So the next substantial engine job is the one this file already prescribes, in the order it
prescribes it: **item 3 first** - make the placer test the ROTATED footprint it is actually going
to draw - and only then item 2, replacing the circles with a real `sat_overlap` on real corner
quads. Both of the above clear as a side effect, and so does most of the frontage-seat fighting.
Budget for the pool re-roll: the naive swap alone moved Tango +21 houses, +20 buildings, +23 wells.

## Two placer bugs of the same shape: INDEX vs POP

`pack` and `frontage` POP each item they seat; `rowpack` walks an INDEX and leaves the list intact.
So the `_shortfall` call added to `rowpack` on 2026-08-11 - copied from its siblings - handed over
the WHOLE list as "what did not fit", and every run reported an ask of exactly double what the gen
gave it. The symptom is nastier than a wrong number: a run seating half its ask reads as seating a
quarter, and trimming the ask to the reported figure halves it again, so the correction has a fixed
point at 50% and never converges. Four rounds of automated trimming chased that before anyone read
the loop. **When you add bookkeeping to a placer, check whether it consumes its work-list or indexes
it** - and if a correction loop is not converging, suspect the measurement before the geometry.

## MIGRATION: new rules land in the SCRIPTED path first, and legacy maps inherit them on conversion

GM 2026-08-13, on finding that threshing yards sit in their neighbours' shadow pool-wide: *"rather
than try to fix our existing maps manually, we'll document the decision to NOT fix this specific map
feature on our manually generated maps, but we'll fix this kind of thing in our generation scripts
and thus ensure it will be fixed as we convert our existing maps to be generated by the new scripted
process."* The experiment is considered proven; converting the pool map-type by map-type is now the
direction of travel.

**The mechanism, and it is deliberately not a list.** A generator script tags its manifest
`meta(generated_by=...)`. A rule adopted ahead of the pool is gated on that tag, and the placement
half is OPT-IN at the engine (`s.sun_corridor(39)` is the first of these) so a legacy gen re-running
is byte-identical. A legacy map therefore keeps its packing until someone converts it, and starts
obeying every such rule the moment they do. Nobody has to maintain a set of exempt maps, and no
exemption can outlive the map it was written for.

**What this costs, and say it out loud when you use it:** the pool is knowingly inconsistent for as
long as the migration takes, and the gate will not tell you which maps are behind. Record the
measurement at the point of decision - the sun rule's entry in `settlements/homesteads.md` lists
every affected map and by how much - so a reader can see the size of the debt rather than discover
it. Reach for this pattern when a rule is right but re-packing the pool is the wrong trade; do NOT
reach for it to avoid fixing a map that is simply inconvenient, which is what waivers are for.

**Superseded by the freeze (2026-08-16) for the gating half:** legacy gens never re-run, so a new
rule needs no `meta.generated_by` gate and no opt-in placement flag to protect them - the
mechanism survives only where the regression corpus replays frozen fixtures through existing
gates. The "say the debt out loud" half stands: the pool is now PERMANENTLY inconsistent until
conversion, and that is the accepted trade, recorded in migration-plan.md section 2.

## The legacy pool is FROZEN (GM 2026-08-16)

Every hand-authored Mode B map - 9 hamlets, 4 villages, 3 towns, 3 provincial cities - is a
permanent EXHIBIT: never regenerated, never re-gated. They stay in `pool/index.html` and their
committed .json/.svg/.png stay exactly as shipped. `poolmaps.py` is the classification
(scripted / legacy / compound), shared by the `test_villages.py` sweep, by `regen.py` (which
prints `FROZEN` and skips; `--frozen-ok` overrides) and by `cache_audit.py`; the sweep's ratchet
keeps every pool gen accounted for.

WHY: hand-authoring is deprecated (the freeze decision is recorded in full in migration-plan.md
section 2), so every hour spent re-fitting a legacy map to a new placement rule, and every engine
change flag-gated to hold 19 deprecated compositions byte-identical, was payment on a process
being replaced. The fix for a frozen map that violates a post-freeze rule is CONVERSION, not
retrofit - do not "fix" a frozen map, and do not treat its rule violations as bugs.

The consequences, so nobody rediscovers them one gate failure at a time:

- **Engine changes no longer need byte-identity flags.** Change behavior freely; the scripted
  cohort and the gate hold the line. `meta.generated_by` gates already in checks stay (the
  regression corpus replays frozen fixtures through them), but NEW rules ship un-gated.
- **Coverage is per-module now.** The above-hamlet wings of the `settlement/` package (towns, cities, the
  capital) are exercised by nothing until their tiers convert, so the Makefile enforces 100% on
  every module except the `settlement/` package (combined), which holds a RATCHET floor (`SETTLEMENT_COV_FLOOR`) -
  raise it as tiers convert, never lower it (same discipline as the retired mypy ratchet).
- **Frozen manifests remain legal READ-ONLY fixtures** (test_checks reads hikari-no-sato.json;
  citybudget prices the tango/nagahara programs) - frozen bytes never change, so those tests stay
  green forever. But never write a test that RUNS a legacy gen or expects a frozen manifest to
  PASS the evolving gate: either one re-shackles iteration to the deprecated pool.
- **The renders are COMMITTED, write-once** (GM 2026-08-16): a frozen exhibit's svg/png cannot be
  faithfully re-derived once the engine drifts, so the 19 maps' renders are tracked in git - the
  one exception to "pool renders are ignored" (`.gitignore` carries the per-file `!` lines and the
  same instruction). When a map is CONVERTED to the scripted approach, remove its physical renders
  from git again (`git rm` the svg/png + delete its `!` lines): the converted map's renders are
  derived by a live generator and belong ignored like every other live map's.
- **The pool's committed artifacts must stay clean.** Any test or tool that runs a live gen for
  its own purposes (the randomness ratchet, the gencache round-trip) must leave the committed
  bytes exactly as it found them - byte-restore, not re-run, because the engine may have drifted
  since the artifact was committed.

## Scripted generation - read before touching `hamletgen.py`

**The experiment is over and the project has committed to it** (GM, 2026-08-15). The standing plan -
what is converted, what order the rest goes in, the bar a conversion has to clear, and the measured
iteration budget - is [`migration-plan.md`](migration-plan.md). **Update its status table as part of
finishing any conversion.**

[`hamletgen.md`](hamletgen.md) is the writeup; [`hamletgen.py`](hamletgen.py) is the generator and
[`pool/hamlets/`](pool/hamlets/) holds its demo maps beside the hand-authored hamlets (the pool is
foldered by tier, not by method; `meta.generated_by` marks a scripted map). The hand-authored pool
froze on 2026-08-16 (see "The legacy pool is FROZEN" above) - it is no longer held byte-identical,
its gens are simply never re-run - and a session drawing anything but a `valley_paddy` hamlet
still follows `settlements.md`.

It found SIX things in shipped engine code. Five are fixed with the full pool sweep (the hem
registry, the sweep's blind spot, the cluster-band pitch, the windbreak/well-grid derivations, the
footbridge arithmetic, and `build_comb`'s grain, which the scripted tier now passes at its
principled `2 / ftpx`); the sixth is half fixed and recorded under "CENTER vs FOOTPRINT" item 3
above. The two worth reading in full, because their SHAPE recurs:

- **FIXED: `draw_comb_field` used to append its dry hem only to `block_polys`, never to
  `s.dry_polys`.** But
  `dry_polys` is the registry the GROVE, LANE and threshing-yard filters read, so a map built
  through it has hem plots that stop a house and not a tree. Every hand-authored comb gen
  compensates with its own `s.dry_polys.append(...)`; the two seed-rolled maps (Honda, Shimizu) do
  not, and pass only because their clusters sit away from the hem. Same shape as "placement and its
  check must read the SAME manifest source", above.
- **FIXED: `roll_village` used to size its cluster band at a 56 px pitch per household**, which is the FARMHOUSE -
  but the to-scale tiers place a BUNDLE (house + threshing yard + dooryard garden, ~71 x 57 ft) and
  the placer spaces bundles by circumscribed circles on top of that. The band therefore asks for
  roughly three times what fits. It does not show up as a shortfall, because the caller keeps
  seeding until the count is met - it shows up as a cluster packed absolutely solid, in which
  `open_seat(..., well=True)` can find nowhere at all to put a wellhead. Honda seating 15 houses for
  18 households is the visible edge of it.

And one methodological result worth carrying to any future generator work: **a cohort is a much
stronger test bed than a map.** Twenty hamlets rolled from consecutive seeds and gated caught ten
distinct defects - an intake at mid-slope starving the fan, a pond laid over the crop, a cluster
seated inside a CONCAVE field margin (the outward normal was taken from the centroid, which is only
right for a convex polygon), a supply canal's tail dying in bare ground, a brook turning through an
acute hairpin, and the two engine bugs above. Authoring one map meets perhaps two of them. If you
add a placement rule, run it against a cohort, not against the map that motivated it.
