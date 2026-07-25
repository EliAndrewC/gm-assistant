# /diagram engine - dev loop

Guidance for *working on the diagram engine* (`settlement.py`, `check_village.py`, the pool
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
numbers. A single map's regen + gate is ~1-7s:

    DIAGRAM_SKIP_RENDER=1 python3 pool/<type>/<map>.gen.py && python3 check_village.py pool/<type>/<map>.json

The full pool sweep - `make done`, which runs `test_villages.py` to regenerate EVERY map and gate
it - is **~80 seconds**. (Measured 2026-07-25: it had drifted to 112-215s across six runs, well past
the "~1 minute" this file used to claim from 2026-07-20; indexing the two worst checks that same day
brought it back to 77s. Re-measure and update this number when it drifts again - a stale figure here
is what makes a session mis-plan its loop.) So run the red/green loop against the ONE map
(or fixture) that shows the defect, where cycles are near-free, and reserve the full sweep for AFTER
that map is green. The sweep is MANDATORY, though, whenever shared engine code changed
(`settlement.py`, `check_village.py`, `waterfields.py`): every pool map is a downstream artifact of
the engine, so the sweep is what proves "no other map regressed" instead of hoping it.
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

## When a check is slow, INDEX it - do not coarsen it

The gate's cost is dominated by a handful of checks that ask a local question with a global scan.
Profile before guessing (`cProfile` around `check_village.gate` on `tango.json`, the worst case):
2026-07-25 found `city_fan_heads_quilted` testing ~3,000 canal-side samples against EVERY plot
polygon and ditch (14M `seg_dist` calls, ~58% of a 17s city gate) and `structures_clear_of_dry_plots`
testing every structure against every dry plot (3.5M `segments_cross` calls). Both were fixed with
`GridIndex` (a uniform-grid spatial index at the top of `check_village.py`): insert each feature
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

## Run the cheap linters BEFORE the full gate

`make done` runs lint -> format -> typecheck -> test+coverage and STOPS at the first failure, so a
trivial formatting or type slip makes you pay a full ~1-min gate run to discover it, fix, and pay
again - the failures surface one per gate run, not all at once. After writing engine code and
BEFORE `make done`, run the seconds-long prefix yourself:

    python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy

That catches format + lint + type errors in one cheap shot (a common one: a local variable name
like `a`/`ux` that collides with an existing binding in the huge `gate()` scope - mypy flags it,
the full gate would too but slower). Only then spend the gate run on tests + coverage.

## Update the predictably-affected tests in the SAME edit

Touching a `settlement.py` method breaks its unit tests deterministically - you know which ones
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

    python3 check_village.py pool/<type>/<map>.json | grep -c "<check_name>"     # 0 = never ran

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
under "PLANK BRIDGES"): the generator in `settlement.py` and the validator in `check_village.py`
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
