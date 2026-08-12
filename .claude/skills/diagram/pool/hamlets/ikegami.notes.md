# Design notes: Ikegami ("above the pond"), the FIRST to-scale hamlet

*Reconstructed 2026-08-08 from the generator's docstring and comments.*

**Subject**: a small outlying farming community of ~15 households / ~75 people, and the map that
established the to-scale hamlet tier.

**Why it exists**: it is the reference hamlet - the first one drawn under the to-scale bundle at
1 ft/px, and the map the tier's rules were settled against. Moritono is the atypical legacy sibling
that deliberately keeps the old path.

## What makes it a hamlet, not a village

A hamlet is a small outlying community belonging to a village district, and the absences are the
definition: **no headman of its own** (its overseer, the district headman, lives in the main
village), **no shrine** (`religious_matches_scale`), **no tax-free plots**, and **no graveyard** -
its dead go to the village district's burial ground. Drawn at 1 ft/px, twice a village's pixel
scale, which keeps a ~15-household map a sensible size; the to-scale homestead bundle carries its
dimensions in FEET and draws them at `ftpx`, so the same 46x28 ft minka is 46 px here against 23 px
on a village sheet.

## Water (which is the name)

Ikegami sits **above** its pond. The land falls gently N (high) -> S (low): a brook from the higher
ground north feeds the head of the common field, comb supply canals distribute the water southward
across the paddies, and the field drains at its low south foot into a **tameike reservoir**. The
name states the relationship the map has to draw correctly - the settlement is upslope of its water,
not beside it.

## Known open

- **No `notes.md` existed for this map until 2026-08-08**, so anything settled between its authoring
  and that date lives only in gen comments and may not be recorded here. Treat gaps as unrecorded
  rather than as decided.

## Settled by the GM (2026-08-12): a path does not pass through marshland

The GM ruled that village paths, not just roads, must keep off marsh - `roads_clear_of_marsh` and
`fields_clear_of_road` had both built their way-list from the road and the town streets only, so
neither had ever seen a lane. This map's connector ran 744 px through the reed toe (it went S to y=2220; the toe starts at y=1490), so it was re-routed to leave along the
contour, above the reeds, and off the W edge instead of the SW.

The route is not a near miss: it keeps well clear of the recorded marsh polygon along its whole
length. A `settlement-review` pass on the result is logged in the session that made the change; its
open points were that the turn should read as terrain rather than as a bend made to satisfy a rule,
and that the toe band spanning the full canvas is itself what leaves a valley map no downslope exit.
