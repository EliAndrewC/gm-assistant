# Design notes: Moritono ("forest gate"), the hamlet under the Shirin Forest

*Reconstructed 2026-08-08 from the generator's docstring and comments.*

**Subject**: a small outlying farming hamlet of ~16 households under the Shirin Forest, redone under
the water-first to-scale rules like Ikegami.

**Why it exists**: it carries two features no other hamlet has, and both survived the rebuild -
the **Shirin Forest** filling the east (the high, wooded ground), and the county magistrate's walled
**hunting lodge** at the forest's edge. The lodge is a samurai estate **adjacent to** the hamlet, not
part of it; that distinction is the point, and a reviewer should not read it as hamlet property.

Moritono is also the pool's **atypical legacy hamlet**: it keeps the old (non-bundle) homestead path
where the other to-scale hamlets opt in via `toscale=True`.

## What makes it a hamlet, not a village

A hamlet is a small outlying community belonging to a village district, and the absences are the
definition: **no headman of its own** (its overseer, the district headman, lives in the main
village), **no shrine** (`religious_matches_scale`), **no tax-free plots**, and **no graveyard** -
its dead go to the village district's burial ground. Drawn at 1 ft/px, twice a village's pixel
scale, which keeps a ~15-household map a sensible size; the to-scale homestead bundle carries its
dimensions in FEET and draws them at `ftpx`, so the same 46x28 ft minka is 46 px here against 23 px
on a village sheet.

## Water

**East -> west**, which is unusual in the pool (`down_deg=180`): the land falls from the high wooded
east to the low west. A brook out of the forest feeds a **tameike source pond** at the field's east
head, the comb supply net distributes the water westward, the field drains at its low west foot into
a valley brook off-map, and the un-reclaimed low toe is reed marsh.

## Known open

- **No `notes.md` existed for this map until 2026-08-08**, so anything settled between its authoring
  and that date lives only in gen comments and may not be recorded here. Treat gaps as unrecorded
  rather than as decided.
