# Design notes: Tanada (棚田), the TERRACED HILL hamlet

*Reconstructed 2026-08-08 from the generator's docstring and comments.*

**Subject**: a hamlet of 14 households on **stacked contour terraces** stepping down a hillside,
`field_archetype='contour_terraces'`.

**Why it exists**: it is the **FIRST field-GEOMETRY archetype beyond the valley-bottom comb** - the
archetype for HILL ground, where flat paddy is impossible. China-first grounding: the Yuanyang and
Longsheng rice terraces.

## Water

Water enters at the **high catchment**, runs down a **flank supply channel**, and **cascades terrace
to terrace** to a drain at the foot. The hamlet sits on the dry low-flank shoulder beside the steps -
not among them, because the steps are the only cultivable ground there is.

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
