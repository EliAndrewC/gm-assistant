# hamletgen/ - the scripted hamlet generator as a package

Split from the 2,913-line `hamletgen.py` monolith by feature 111 (constitution Principle X
clause 13: files stay at human scale - the cost being managed is context-window tokens), following
the `check_village/` and `waterfields/` exemplars. **Load only the file the task calls for**; this
index is the map. `import hamletgen` still exposes the whole consumed surface via `__init__.py`
(star-import re-exports, clause 14), and the CLI is now `python3 -m l7r.diagram.hamletgen`.

Read the package docstring in `__init__.py` first if you have not worked on this engine before: it
carries the four doctrine paragraphs (WHAT THIS IS, THE ORDER IS THE DESIGN, DERIVE NEVER PIN, THE
CHECKS ARE THE ORACLE) that explain why the generator is shaped the way it is.

**Tiers share a library, and the rule is MOVE, never copy** (GM 2026-08-17, feature 119). The
tier-agnostic machinery this package used to own - the geometry helper set, `Pt` / `Poly` /
`SQ_FT_PER_ACRE`, `default_jobs` - now lives in [`../sitegen/`](../sitegen/CLAUDE.md), which the
village, town and city generators will import alongside this one. When a later tier needs a stage
that currently lives here, **move it into `sitegen` and have both tiers import it**; do not copy it.
Copying is how two tiers quietly drift apart, and the drift stays invisible until the maps disagree.
`sitegen` never imports `hamletgen` - the direction is one-way and a test asserts it.

Three invariants the split does NOT touch:

- **`STAGES` in `driver.py` IS the pipeline contract.** The order is a design decision, shared with
  the skill CLAUDE.md's DRAW ORDER map - not something to be derived by introspection, and not
  something to reorder casually. The comment above the tuple says so at the point of change.
- **DERIVE, NEVER PIN.** Every position in this package is computed from geometry already on the
  map. A hard-coded coordinate silently becomes false when the thing it referenced moves; that is
  the project's standing rule and it is also what lets one script run at any size, seed or fall
  direction.
- **The checks are the oracle, per ROUND not per placement.** `generate()` runs
  `check_village.gate()` in-process on the finished manifest. The placer already refuses an
  overlapping seat, so overlap checks are a formality; what the gate catches is emergent (acreage
  vs household count, a marsh uphill, a windbreak on the lee side).

## Look here when

| file | look here when |
|---|---|
| `__init__.py` | you need the package docstring, the `sys.path` bootstrap, or the re-export mechanism - star imports carry every submodule's public names, an aliased block carries the four consumed underscore names (guard: `tests/hamletgen/test_surface.py`); never add logic here |
| `__main__.py` | the `python3 -m l7r.diagram.hamletgen` entry point needs changing (it is a shim; `main` itself lives in `driver.py` because consumers reach `hamletgen.main`) |
| `consts.py` | a researched number needs reading or changing: `GROSS_ACRES_PER_HOUSEHOLD`, `LANE_CLEARANCE`, `SPUR_SETBACK`, `SUN_CORRIDOR_FT`, `POLDER_CELL_FT`, `POND_SETBACK_LIMIT`, `CROP_MARGIN`, the archetype/ladder/bearing/wind tables (`FIELD_ARCHETYPES`, `ROLLED_ARCHETYPES`, `OFFTAKE_LADDER`, `FALL_BEARINGS`, `WIND_VECTORS`, `CLUSTER_SHAPES`, `LANE_SKELETONS`, `PLOT_SIZES`), and the `Pt`/`Poly` aliases (which now LIVE in [`../sitegen/types.py`](../sitegen/CLAUDE.md) and are re-exported here, so `from .consts import Poly, Pt` still works). **Every constant carries the reasoning that fixed it** - keep it that way (the project's record-the-why rule). The bearing and wind tables are the standing candidates to move down into `sitegen` when the village tier makes them a second consumer |
| `plan.py` | the caller-facing spec or the derived plan: `HamletSpec` (what a pool `.gen.py` writes), `SitePlan` (everything derived from it), `plan_site`, `canvas_for`, `offtakes_for`, `windward_for` |
| *(moved)* | geometry predicates and measures now live in the shared [`../sitegen/geom.py`](../sitegen/CLAUDE.md) - feature 119 |
| `water.py` | STAGE 1-2 - the irrigation skeleton and the field it shapes: `stage_water_frame`, `stage_field`, `stage_polder`, `fit_field` (which SOLVES for a real acreage instead of taking a hand-tuned pixel fall), `fit_polder`, `head_sluice`, `feed_brook`, `tail_dangles`, `net_bends_acutely` |
| `sink.py` | STAGE 3 - where the runoff goes: `stage_sink`, the tameike derived from the drain outfall, `drain_outfall`, `drain_heading` (which measures over `GATE_FLOW_SPAN`, the gate's own 40 px chord - read its docstring before touching the offmap route search, it is where a 76 deg disagreement with `drainage_junction_smooth` came from), `edge_run`, `pond_clear_of_crop`, `pond_setback` |
| `cluster.py` | STAGE 4a - where the settlement sits: `seat_cluster` (the 背山面水 margin band), `below_drain`, `back_fouled`, and the spur helpers `_fork_spur`, `_arm_hit`, `_arm_crossing_accidental` |
| `ways.py` | STAGES 4b and 5b - the lanes and what makes a path legal. **Two stages, and the order between them is the whole design**: `stage_ways` (4b) lays the SKELETON and the connector BEFORE the houses, so the homesteads front them; `stage_web` (5b) lays the LANE WEB AFTER the houses, because a web laid first competes for ground with the very houses it exists to serve (measured: it grew the four pool clusters' long axes 15-97%, sprawl no check measures). Also `_margin_frame` (outline coordinates: arc along the field edge, standoff out from it, plus the `project` inverse), `clear_runs` (every clear stretch of a through-lane, with a tight second obstacle family for the settlement's own fabric), `_serve_stragglers` (the footpath to an outlying steading), `_homestead_polys`: `stage_ways`, `connector_track` (derived, steered clear of crops), `push_out_of`, `route_around`, `clip_to_clear`, `path_violations`, `crossing_lands_on_crop`, `shallow_crossing` |
| `homesteads.py` | STAGE 5-6 - the houses and what stands among them: `stage_homesteads`, `front_row`, `lane_frontage`, `stage_appurtenances`, `place_wells`, `well_target` |
| `hinterland.py` | STAGE 7 - the ground between everything: `stage_hinterland`, `open_ground_patches` (the scan that seats woodland commons on dry ground inside the predicted crop window), `stage_woodland`, `stage_windbreak`, `belt_polygon`, plus the title-pocket helpers `content_box`, `title_pocket`, `_clear_gap`, `_near_line` |
| `frame.py` | STAGE 8 - `stage_crossings`, `stage_notice` (the kosatsuba), `stage_frame` (crop-to-content and the title) |
| `driver.py` | the pipeline and everything that drives it: the `STAGES` tuple, `Report`, `build`, `generate` (which finishes AND gates in-process), `cohort` (fanned out across processes since 2026-08-16 - `generate` IS the worker; `jobs=1` forces serial, which is what in-gate callers want) and `main`. `default_jobs` - the one cpus-minus-2 rule, reused by `cohort_audit.py` - moved to [`../sitegen/jobs.py`](../sitegen/CLAUDE.md) and is imported back in here, so `hamletgen.default_jobs` still resolves |

## Adding a stage

Write the `stage_<name>(s, plan)` function in whichever submodule covers its theme (or a new one,
if it is genuinely a new concern), then add it to `STAGES` in `driver.py` **at the position the
draw order requires** - not at the end.

**Before/after the houses is a real decision, not a detail.** Feature 123 is the worked example: a
stage that RESERVES ground (a no-build corridor the houses pack around) belongs before
`stage_homesteads`; a stage that FILLS ground left over belongs after it. Getting that backwards
does not fail loudly - it just makes the settlement bigger and looser, and no check measures that.

Update the skill CLAUDE.md's DRAW ORDER map in the same change, and add the stage's row to the
table above.

Sub-stage helpers extracted from a long stage are named for what they do (`_seat_*`, `_fit_*`,
`_route_*`) and keep the extraction mechanical: same code order, same RNG draw order, same
float-operation order. The generator is seeded and deterministic, so any reordering shifts every
downstream coordinate.

## REPRODUCE A COHORT FAILURE WITH THE ENTRY POINT THAT PRODUCED IT

Two ways to get a green you have not earned, both of which have bitten inside one feature.

- **The in-gate ratchet rolls seeds 41-44**, not 1-4: `tests/hamletgen/test_driver.py`'s
  `test_a_rolled_cohort_passes_the_whole_gate` calls `cohort(4, first_seed=41, jobs=1)`. Feature 123
  was validated against 1-4 for most of its life, passed 4/4 there, and failed in the gate - which
  reads as a mysterious gate failure rather than as checking the wrong maps.
- **`build()` is not `generate()`, and "nearest lane" is not "nearest lane IN THE NETWORK".** The
  sweep gates the FINISHED manifest and several checks measure against the connected component
  containing the connector; a hand-rolled diagnostic that stops at `build()` and measures distance to
  any drawn polyline answers a different question. That is how one of feature 123's failing seeds got
  reported as having zero unserved houses when the sweep said nine.

  (An earlier version of this note blamed differing HOUSEHOLD COUNTS between `cohort()` and
  `cohort_audit`. That was wrong - both are `10 + (seed * 7) % 11`, identical - and it is recorded
  here rather than silently deleted, because a plausible wrong cause is what stops anyone looking for
  the real one.)

**So: reproduce with the same entry point.** If the gate found it, call `cohort(..., first_seed=41)`;
if `cohort_audit` found it, call `generate()` on the same spec and gate the finished manifest.

## Verifying a change

The oracle is the manifest, not the render. `specs/111-hamletgen-package/quickstart.md` holds the
byte-identity harness: roll the four live hamlets and a 24-seed cohort in a scratch copy and diff
the manifests. For a change that is SUPPOSED to alter output, roll the cohort and read the gate
verdicts (`python3 -m l7r.diagram.hamletgen --batch 24`), then re-roll the pool hamlets and run
`settlement-review` before shipping.
