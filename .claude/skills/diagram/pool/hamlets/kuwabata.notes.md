# Design notes: Kuwabata (桑畑, "mulberry field"), the CASH-CROP hamlet

*Reconstructed 2026-08-08 from the generator's docstring and comments.*

**Subject**: a hamlet of 16 households on polder geometry carried to the dike-pond system's rare
**wholesale-conversion end state** - 桑基魚塘, the full `mulberry_dike_fishpond` overlay at
`eligible="all"`. Almost every former paddy cell has been dug into a fish pond and the spoil piled
into a mulberry-planted dike around it.

**Why it exists**: to draw the END STATE, which is deliberately the exception. The **scattered**
overlay is the norm; see `research.md` D2 of `specs/010-land-use-overlay-grounding` for why. Reading
this map as typical would be the mistake it is here to make visible.

## The economy (GM-confirmed 2026-07-24)

Kuwabata is a **cash-crop settlement, not a subsistence one** - the rice-farmer's analog of the
tobacco or indigo switch. The ponds are stocked artificial fisheries (historically carp polyculture),
and the household economy closes a loop: mulberry leaves feed silkworms, silkworm waste feeds the
fish, dredged pond mud fertilizes the mulberries. **Silk is the bigger earner**; fish go to market;
grain is bought in. Historically, gazetteers found the total absence of rice remarkable enough to
record - which is the fact this map is drawing.

## Water

Polder water discipline: in at the **high corner**, a perimeter feeder supplies the block, out at the
**low corner**. The village lines the dry perimeter dike on the east side.

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
