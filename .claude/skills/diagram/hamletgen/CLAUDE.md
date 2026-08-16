# hamletgen/ - the scripted hamlet generator as a package

Split from the 2,913-line `hamletgen.py` monolith by feature 111 (constitution Principle X
clause 13: files stay at human scale - the cost being managed is context-window tokens), following
the `check_village/` and `waterfields/` exemplars. **Load only the file the task calls for**; this
index is the map. `import hamletgen` still exposes the whole consumed surface via `__init__.py`
(star-import re-exports, clause 14), and the CLI is now `python3 -m hamletgen`.

Read the package docstring in `__init__.py` first if you have not worked on this engine before: it
carries the four doctrine paragraphs (WHAT THIS IS, THE ORDER IS THE DESIGN, DERIVE NEVER PIN, THE
CHECKS ARE THE ORACLE) that explain why the generator is shaped the way it is.

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
| `__init__.py` | you need the package docstring, the `sys.path` bootstrap, or the re-export mechanism - star imports carry every submodule's public names, an aliased block carries the four consumed underscore names (guard: `test_hamletgen_surface.py`); never add logic here |
| `__main__.py` | the `python3 -m hamletgen` entry point needs changing (it is a shim; `main` itself lives in `driver.py` because consumers reach `hamletgen.main`) |
| `consts.py` | a researched number needs reading or changing: `GROSS_ACRES_PER_HOUSEHOLD`, `LANE_CLEARANCE`, `SPUR_SETBACK`, `SUN_CORRIDOR_FT`, `POLDER_CELL_FT`, `POND_SETBACK_LIMIT`, `CROP_MARGIN`, the archetype/ladder/bearing/wind tables (`FIELD_ARCHETYPES`, `ROLLED_ARCHETYPES`, `OFFTAKE_LADDER`, `FALL_BEARINGS`, `WIND_VECTORS`, `CLUSTER_SHAPES`, `LANE_SKELETONS`, `PLOT_SIZES`), and the `Pt`/`Poly` aliases. **Every constant carries the reasoning that fixed it** - keep it that way (the project's record-the-why rule) |
| `plan.py` | the caller-facing spec or the derived plan: `HamletSpec` (what a pool `.gen.py` writes), `SitePlan` (everything derived from it), `plan_site`, `canvas_for`, `offtakes_for`, `windward_for` |
| `geom.py` | a shared geometry predicate or measure: `poly_area`, `net_acres`, `centroid`, `unit`, `crop_polys`, `pull_clear`, `crosses_disc`, `crosses_poly` (and `point_in_poly`, re-exported from `settlement`) |
| `water.py` | STAGE 1-2 - the irrigation skeleton and the field it shapes: `stage_water_frame`, `stage_field`, `stage_polder`, `fit_field` (which SOLVES for a real acreage instead of taking a hand-tuned pixel fall), `fit_polder`, `head_sluice`, `feed_brook`, `tail_dangles`, `net_bends_acutely` |
| `sink.py` | STAGE 3 - where the runoff goes: `stage_sink`, the tameike derived from the drain outfall, `drain_outfall`, `drain_heading`, `edge_run`, `pond_clear_of_crop`, `pond_setback` |
| `cluster.py` | STAGE 4a - where the settlement sits: `seat_cluster` (the 背山面水 margin band), `below_drain`, `back_fouled`, and the spur helpers `_fork_spur`, `_arm_hit`, `_arm_crossing_accidental` |
| `ways.py` | STAGE 4b - the lanes and what makes a path legal: `stage_ways`, `connector_track` (derived, steered clear of crops), `push_out_of`, `route_around`, `clip_to_clear`, `path_violations`, `crossing_lands_on_crop`, `shallow_crossing` |
| `homesteads.py` | STAGE 5-6 - the houses and what stands among them: `stage_homesteads`, `front_row`, `lane_frontage`, `stage_appurtenances`, `place_wells`, `well_target` |
| `hinterland.py` | STAGE 7 - the ground between everything: `stage_hinterland`, `open_ground_patches` (the scan that seats woodland commons on dry ground inside the predicted crop window), `stage_woodland`, `stage_windbreak`, `belt_polygon`, plus the title-pocket helpers `content_box`, `title_pocket`, `_clear_gap`, `_near_line` |
| `frame.py` | STAGE 8 - `stage_crossings`, `stage_notice` (the kosatsuba), `stage_frame` (crop-to-content and the title) |
| `driver.py` | the pipeline and everything that drives it: the `STAGES` tuple, `Report`, `build`, `generate` (which finishes AND gates in-process), `cohort` (fanned out across processes since 2026-08-16 - `generate` IS the worker; `jobs=1` forces serial, which is what in-gate callers want), `default_jobs` (the one cpus-minus-2 rule, reused by `cohort_audit.py`), `main` |

## Adding a stage

Write the `stage_<name>(s, plan)` function in whichever submodule covers its theme (or a new one,
if it is genuinely a new concern), then add it to `STAGES` in `driver.py` **at the position the
draw order requires** - not at the end. Update the skill CLAUDE.md's DRAW ORDER map in the same
change, and add the stage's row to the table above.

Sub-stage helpers extracted from a long stage are named for what they do (`_seat_*`, `_fit_*`,
`_route_*`) and keep the extraction mechanical: same code order, same RNG draw order, same
float-operation order. The generator is seeded and deterministic, so any reordering shifts every
downstream coordinate.

## Verifying a change

The oracle is the manifest, not the render. `specs/111-hamletgen-package/quickstart.md` holds the
byte-identity harness: roll the four live hamlets and a 24-seed cohort in a scratch copy and diff
the manifests. For a change that is SUPPOSED to alter output, roll the cohort and read the gate
verdicts (`python3 -m hamletgen --batch 24`), then re-roll the pool hamlets and run
`settlement-review` before shipping.
