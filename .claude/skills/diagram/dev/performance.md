# Performance: the two shapes this engine keeps growing

**Load this file when:** A gen or a check got slow (or "hangs"), you are about to optimize one, or a GEN_TIME_BUDGETS entry tripped.

Split out of [`../CLAUDE.md`](../CLAUDE.md) so it is not in every diagram session's
context. The text is verbatim; the short always-on version of each rule stays in the index.

## Shape one: a per-candidate scan of geometry that does not change during the scan

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
`tests/test_villages.py`) so the next silent 45-minute-class regression fails loudly by name instead of
being waited out; `DIAGRAM_ALLOW_SLOW_GENS=1` overrides once you are certain perf is fine, and a
legitimately-outgrown map gets a bigger budget entry WITH its reason. **Budgets are calibrated
against the GATE, not a solo run** - under `pytest -n auto` a gen's own CPU time inflates 2-4x
through cache contention, which is why each entry is ~4x its recorded solo measurement.

**A GEN'S CPU TIME INFLATES 2-4x INSIDE THE GATE, so budgets are calibrated against the GATE, never
a solo run** (`tests/test_villages.py` says this at the table; both halves of it were found the same day,
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

`test_matrix_survives_geometry_far_off_the_canvas` in `tests/check_village/` is the guard, timed rather
than structural on purpose: the failure mode is unbounded work, and the correct-vs-broken margin is
a fraction of a second against effectively forever.
