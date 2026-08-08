# Design notes: Enokida (榎田), the POLDER-GRID hamlet

*Reconstructed 2026-08-08 from the generator's docstring and comments.*

**Subject**: a hamlet of 16 households on a rectilinear block of paddies, `field_archetype='polder_grid'`.

**Why it exists**: it is the pool's **second field-GEOMETRY archetype** - the planned, surveyed
opposite of the organic valley comb. China-first grounding: the *wei-tian* 圩田 polders of the
lower-Yangtze lake plains. A straight ditch-grid module whose bays subdivide into a varied parcel
patchwork, all inside a perimeter dike on flat reclaimed LOW ground.

## Water

Water enters the **high corner**, a perimeter feeder supplies the grid, and it drains to the **low
corner**. The village lines the dry perimeter dike on the east side - on the dike because that is
the dry ground a polder has.

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
