# Design notes: Honda ("main paddy"), a hamlet rolled ENTIRELY from a seed

*Reconstructed 2026-08-08 from the generator's docstring and comments.*

**Subject**: a hamlet of 18 households generated with **zero hand-placed coordinates** (feature 005
US2, SC-004).

**Why it exists**: the spec is deliberately minimal - a name, a canvas, a seed, a household count and
a fall direction. Every knob (`cluster_position`, `cluster_shape`, `lane_skeleton`,
`water_source_position`, `plot_size`, `plot_regularity`, `grain_drift`) is ROLLED from the seed and
drives the geometry through the resolvers. **Its sibling `shimizu.gen.py` uses a different seed and
rolls a visibly different combination** - the pair together is the demonstration, not either alone.

Read that as a constraint when reviewing: a feature sitting somewhere odd here is the roll, not an
authoring choice, and the fix belongs in the knob's `typing_rule` rather than in a coordinate.

## The name

Named for its defining feature: the district's **oldest cleared fields** - a broad paddy fan in large
consolidated blocks, whose lowest, wettest edge has been converted to the pinned
mulberry-and-fishpond system.

## What makes it a hamlet, not a village

A hamlet is a small outlying community belonging to a village district, and the absences are the
definition: **no headman of its own** (its overseer, the district headman, lives in the main
village), **no shrine** (`religious_matches_scale`), **no tax-free plots**, and **no graveyard** -
its dead go to the village district's burial ground. Drawn at 1 ft/px, twice a village's pixel
scale, which keeps a ~15-household map a sensible size; the to-scale homestead bundle carries its
dimensions in FEET and draws them at `ftpx`, so the same 46x28 ft minka is 46 px here against 23 px
on a village sheet.

## Known open

- **No `notes.md` existed for this map until 2026-08-08**, so anything settled between its authoring
  and that date lives only in gen comments and may not be recorded here. Treat gaps as unrecorded
  rather than as decided.
