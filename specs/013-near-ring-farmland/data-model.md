# Data Model / Contracts: Near-Ring Farmland Density

**Feature**: 013-near-ring-farmland | **Date**: 2026-07-22

This engine change has no external API. The "contracts" are the three internal surfaces it adds - the `meta` knob, the fill method, and the validator check - plus the derived region and cover sets they share. Exact names/values below are the plan's recommendation; `/speckit-tasks` and implementation may refine within the stated intent.

## Entity 1 - `near_ring_density` (per-map `meta` knob)

- **Kind**: a `meta()` kwarg on the settlement, read via `meta.get("near_ring_density", <dense default>)` (the established per-map pattern, cf. `agricultural_district`, `wall_defense`). NOT a rolled `Knob`.
- **Scope**: `scale="town"` and `scale="city"` only. Ignored (and unread) at village/hamlet scale.
- **Value space (recommended, tiered enum)**:
  - `"dense"` - well-sited basin/valley default. The near ring reads packed; near-ring bare/scrub is minimal.
  - `"medium"` - a mixed locale; a genuine blend of cultivated and rough ground.
  - `"thin"` - a dry rain-shadow / marginal / frontier locale; the near ring stays scrubbier, closer to today's look.
  - (An alternative float form `0.0-1.0` is acceptable if implementation prefers a continuous target; the tiered enum is recommended for legibility and because the check threshold is keyed off it.)
- **Default**: `"dense"`. A map that declares nothing gets the packed look (FR-005). This default encodes the calibrated-liberty choice (research.md).
- **Validation**: an unknown value is a gen error (fail loud, not silently default). The default constant and the tier->threshold mapping carry a record-the-why comment pointing at research.md Part A + the calibrated-liberty disclosure.

## Entity 2 - The flat near-ring band (derived region, not stored)

- **Definition**: the framed view MINUS all of:
  - the inflated hill: any point with `in_ellipse(x, y, M["hill"], 1.45)` (the existing not-hill predicate),
  - the wet toe / marsh and watercourse `block_polys`, and the moat / streams / irrigation channels,
  - for a walled map, the wall interior (fill is OUTSIDE the wall),
  - the 30-ft urban-clearance halo around every structure (`_urban_keepouts`),
  - existing fields (paddy envelopes) and their no-build corridors, lanes/streets/roads.
- **Near-ring bound**: the frame edge at the scales we draw (town ~0.5 mi, city ~1.5 mi across), optionally clamped to a radius `R` from the settlement centroid. Whether `R` is needed (vs "the whole in-frame flat complement") is a data-model decision to settle during implementation; default is "the whole in-frame flat complement," since at these scales the frame IS the near ring.
- **Relationships**: this is exactly the complement the coverage checks already sample, so it is derived at fill time and at check time from the same primitives - it is not persisted in the manifest.

## Entity 3 - `near_ring_cropland(...)` (fill method on `Settlement`)

- **Signature (recommended)**: `s.near_ring_cropland(density=<resolved tier>, *, ring_farms=<bool|count>, seed=..., avoid=(), ...)`.
- **Behavior**: tiles ridge-cultivated **dry-field** rectangles (furrowed hatake, `DRY_CROPS` variety, honoring the "~1 in 6" crop-mix convention) and garden-grain plots over the derived band (Entity 2), at a spacing/coverage set by `density`. Skips every keep-out. Optionally rings the new fill with farmsteads via `ring()`/`try_place`.
- **Records**: each plot into `M["dry_plots"]` (shape `{"poly", "crop", "fill", "furrow", "theta"}`, matching `_dry_fields`) AND `s.dry_polys` (footprint-aware no-build). Any rung farmsteads into `M["houses"]` etc. as the existing bundle does.
- **Draws NO water**: no channel, sluice, or drain. Dry cropland is structurally exempt from `fields_show_water_source`, `city_moat_irrigates_fields`, and the paddy farmstead-density checks (`kind != "paddy"`).
- **Invariants** (must hold post-call, verified by existing checks): no dry plot overlaps a structure/road/street/stream/channel/wall/moat; no dry plot on the hill (close the recon-noted gap - `no_field_on_hill` currently checks only `M["fields"]`, not `M["dry_plots"]`; extend or add a `dry_plots_off_hill` guard); at least one paddy field still runs off the map edge (FR-008, unaffected since paddy is untouched).

## Entity 4 - `near_ring_cultivated_fraction` (validator check)

- **Kind**: a `check("near_ring_cultivated_fraction", ok, detail)` call in `check_village.py`, a restricted clone of `town_margins_clothed` (`~:5412`).
- **Scope**: town + city manifests only.
- **Sample region**: the flat near-ring band (Entity 2), on the same 25px grid the sibling checks use.
- **Cover set (CULTIVATED only)**: paddy `M["fields"]` envelopes (`kind=="paddy"` and vegetable), `M["dry_plots"]`, `M["gardens"]`. Explicitly NOT counted as cultivated: `commons`/scrub, `pasture`, `forest_patch`, structures, roads, water.
- **Pass condition**: cultivated-fraction over the sampled near-ring cells `>= threshold(near_ring_density)`, where the threshold is high for `"dense"`, moderate for `"medium"`, and low for `"thin"`. The `"thin"` threshold is a floor low enough that a genuinely marginal map passes; the intent is that a `"dense"` map cannot pass while sparse (that is the teeth), and a `"thin"`-declared map is not forced to be packed.
- **Failure detail**: reports the measured cultivated-fraction, the threshold, the declared tier, and points the author at the fix (call `near_ring_cropland` / thin the near-ring commons / declare a lower tier).
- **Negative fixture (REQUIRED, FR-010)**: `pool/regressions/near_ring_cultivated_fraction_fires_on_sparse_hirameki.json` (and/or a city variant) - a pre-densification manifest of a `"dense"`-declared map, saved to prove the check fires on the sparse case. (Coverage alone does not prove teeth - the diagram-regression convention.)

## Entity 5 - Doctrine record (settlements.md)

- **New rule**: the near-ring-density doctrine (fill the flat near ring; push scrub to margins/non-arable; quilt not monoculture; topography governs; tunable) with a "Historical grounding" note carrying research.md Part A (site selection, von Thünen, labor-limited fallow relocation, the quilt, calibrated liberty on degree).
- **Revised line**: `settlements.md:195` "We do not draw all the farmland. A town's fields are a representative sample; the rest is implied off-map" -> narrowed so the *near-ring flat ground* reads as packed cultivation while the *far* countryside is still implied off-map (at least one field still runs off the edge).

## State / flow

There is no stateful entity or transition. The flow is: gen declares `meta(near_ring_density=...)` (or omits it -> dense) -> gen calls `s.near_ring_cropland(...)` after its paddy combs and before/around its (now margin-only) `s.commons` -> manifest carries the extra `dry_plots`/`gardens` -> `near_ring_cultivated_fraction` (plus every existing check) validates it -> render -> Principle XII closing-gate human review of the PNG.
