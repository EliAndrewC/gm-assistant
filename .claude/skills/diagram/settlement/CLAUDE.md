# settlement/ - the Mode B drawing engine as a package

Split from the 16,016-line `settlement.py` by feature 025 (constitution Principle X clause 13 -
the cost being managed is context-window tokens). **Load only the file the task calls for**; this
index is the map. `import settlement` still exposes the full legacy surface via `__init__.py`,
and `settlement.Settlement` is the same single class - its 338 methods are grouped into subsystem
MIXIN classes composed in `core.py`, so class-level monkeypatching and subclassing behave exactly
as before.

Two invariants the split does NOT touch:

- **DRAW ORDER is a runtime contract.** Features are layered by the record streams (`add` /
  `add_top` / `add_wall`, in `core.py`) and assembled by `finish()` (in `finish.py`); the DRAW
  ORDER map documentation lives in the skill's `CLAUDE.md`. The mixin grouping changes where a
  method's TEXT lives, never when it runs.
- **Knob doctrine** (feature 005): knobs are rolled via `scope_seed`/`knob_rng` in `_knobs.py`;
  a knob's value depends only on (map seed, knob name), never on draw order.

## Look here when

| file | look here when |
|---|---|
| `__init__.py` | you need the re-export list or the import-time main-tree guard; never add logic here |
| `_geom/` | the geometry/spatial subsystem - a PACKAGE with its own [`CLAUDE.md`](_geom/CLAUDE.md) index since feature 117. Read that first, then load one of: `base.py` (the `Pt`/`Poly`/`Manifest` aliases, the import-time main-tree guard, the palette), `primitives.py` (point/segment/ring math), `overlap.py` (corner rings + the collision/gap/region predicates), `indexes.py` (the `boxed_*` prefilters, `PointGrid`, `Indexed`), `seatmemo.py` (`SeatMemo`), `labels.py` (the caption standoff ladder, the two caption sizes, tilt/quad/AABB), `ways.py` (the travelled ways, the kido bar, the crossing constants), `walls.py` (walls, ward closure, torii-vs-wall clearance), `extents.py` (a recorded feature's drawn extent), `curves.py` (fillets, smoothing, organic jitter), `village.py` (`village_population`, `BUNDLE_PITCH_FT`) |
| `_knobs.py` | the knob engine (`Knob`, `register_knob`, `resolve_knob`, `scope_seed`, `knob_rng`, layout validators, `skeleton_layout`) and roll/size helpers (`roll_torii_count`, `execution_ground_ft`, wall/bridge/moat/crop helpers) |
| `core.py` | `class Settlement(...)` itself: `__init__`, the record streams (`add`/`add_top`/`add_wall`/`add_label`), meta/header, knob resolve + rng scoping, viewport/crop |
| `fields/` | the field subsystem - a PACKAGE with its own [`CLAUDE.md`](fields/CLAUDE.md) index since feature 112. Read that first, then load one of: `paddy.py` (paddy/water/fallow field bodies + plot geometry), `comb.py` (the comb-field builder, base fill, bund junctions, furrows), `landuse.py` (mulberry/lotus/tea overlays), `features.py` (feature-012 in-field pond/rock/grave island + every pond glyph) |
| `water_ways.py` | focal features (mill/market/halls), streams/rivers/channels + water clipping, lanes/streets/kido/wards/quarters/alleys |
| `shrines_wells/` | the shrines/wells subsystem - a PACKAGE with its own [`CLAUDE.md`](shrines_wells/CLAUDE.md) index since feature 116. Read that first, then load one of: `shrines.py` (shrine halls + the two simple glyphs, the hill, the hall caption), `torii.py` (the arch and the whole avenue engine - count, stride, threshold, wall clearance), `wellground.py` (whether ground may take a wellhead at all: the index, `frozen_terrain`, the wet-toe and scrub refusals - the hub), `wells.py` (the wellhead glyph and the four placement passes), `seats.py` (`open_seat` + `_footprint_clear`), `byres.py` (draft-animal sheds), `woods.py` (tree stands, the fringe, `forest`) |
| `structures/` | the structures subsystem - a PACKAGE with its own [`CLAUDE.md`](structures/CLAUDE.md) index since feature 114. Read that first, then load one of: `compounds.py` (manor, merchant estates), `ground.py` (roads, pasture), `urban.py` (the `URBAN` palette, generic `building`, per-building seating), `servants.py` (servant ranges + their door/solid probes), `packing.py` (the rowpack/pack placement engines, `_shortfall`), `captions.py` (label-blocker plumbing and the caption-seat probes), `fixtures.py` (theater, fire tower, kosatsuba, drum tower, punishment-spot and notice-board siting) |
| `trades.py` | trade works: brewery, dye yard, lumber, oil press, pawnshop, bathhouses, farrier, kiln, charcoal yard, refining forge, tanning yard, border lines |
| `homestead_parts.py` | threshing yards, gardens, farm sheds, homestead groves, the village grove, canopy/corridor keepouts |
| `land.py` | perimeter dikes + dike-top housing, commons, marsh, toe bands, hinterland, near-ring cropland/paddy, farmstead nudge plumbing |
| `civic_grounds/` | the civic-grounds subsystem - a PACKAGE with its own [`CLAUDE.md`](civic_grounds/CLAUDE.md) index since feature 115. Read that first, then load one of: `funerary.py` (cemetery, mausoleum, cremation ground, ossuary), `justice.py` (punishment spots, execution grounds, boundary markers), `civic.py` (granary, merchant storehouses/residences, districts, terraces, the temple-precinct interior), `lodging.py` (flophouse, inn, stables, animal ground, the deferred yard flush), `stable_yard.py` (the stable yard itself - read its RNG rules before editing) |
| `city/` | the provincial-city subsystem - a PACKAGE with its own [`CLAUDE.md`](city/CLAUDE.md) index since feature 113. Read that first, then load one of: `walls.py` (ring road, city wall, towers, wall walk), `moat.py` (moat, water gates, sluices, the inwall drain), `canals.py` (canal, towpath, farmland ring), `waterfront.py` (quay, aqueduct, docks, jetty, log boom), `bridges.py` (bridges, channel footbridges), `civic.py` (the governor's mansion) |
| `castle_civic.py` | castle, ministries, dojos + martial halls + hanko, the caption/label-spot engine, forest patches, freestanding walls, flower fields |
| `houses.py` | house drawing + placement machinery (corridors, keepouts, treads, `_fits`, frontage), `try_place`, cluster seeds, plot texture, water-source anchors |
| `rolling/` | the rolling / homestead-solver subsystem - a PACKAGE with its own [`CLAUDE.md`](rolling/CLAUDE.md) index since feature 118. Unlike the residue-bucket packages this one is a CHAIN, and its six modules are its links: read that index first, then load one of `roll.py` (`roll_village` and its seven stages - knobs, field, cluster band, lanes/headman/seeds, wells, windbreak, civic), `seeds.py` (the settlement-FORM seed generators and the perimeter ring), `bundle.py` (what a homestead bundle IS - pure geometry), `fit.py` (may it stand here? every keep-out predicate and the two caches), `place.py` (the spiral searches and compaction slides - the package's hub), `farmsteads.py` (the deferred flush: what gets DRAWN, and in what order) |
| `finish.py` | labels + titles, blank-spot search, `finish()` (layer assembly + svg write), `render_png` |

## Mixins and mypy

Every mixin method is annotated `self: "Settlement"` with `from .core import Settlement` under
`TYPE_CHECKING` - that is what lets `mypy --strict` resolve cross-subsystem attribute access with
zero runtime import cycle. When adding a method to a mixin, keep that pattern; when adding a new
subsystem file, add its mixin to the `class Settlement(...)` bases in `core.py` and a row here.

## Monkeypatching a module-level name

Submodules bind helper names at import (`from ._geom import poly_gap`), so patching
`settlement.poly_gap` does not reach a mixin that already imported it - patch the DEFINING
submodule (since feature 117 that is one level deeper: `settlement._geom.overlap.poly_gap`, not
`settlement._geom.poly_gap` - the package index says which submodule defines what) or, for anything
reached via `self.`, patch
`settlement.Settlement` (class-level patching is unaffected by the split). As of the split, no
test in the suite patches a settlement module-level name (census in
`specs/025-human-scale-splits/consumer-census.json`).

## Coverage

The package holds the 94% RATCHET floor from the 2026-08-16 legacy freeze (see
`SETTLEMENT_COV_FLOOR` in the Makefile): the uncovered town/city/capital wings live mostly in
`city/`, `castle_civic.py`, and parts of `structures/`/`civic_grounds/`, and re-cover as
those tiers convert to scripted generation. Raise the floor with each conversion; never lower it.
