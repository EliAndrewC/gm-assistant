# Design notes: Akagahara (赤ヶ原, "red plain"), the DISPERSED hamlet

*Reconstructed 2026-08-08 from the generator's docstring and comments.*

**Subject**: a hamlet of 15 households on iron-rich red clay, and the pool's test map for the
feature-005 `settlement_form="dispersed"` archetype - the *kainyo* strewn-farmstead pattern.

**Why it exists**: to prove the dispersed form. The farmsteads are **strewn around the field's dry
margins**, RINGING the paddy, each on its own dry patch nestled in **its own yashikirin windbreak
grove** - there is no communal wood, which is the visible difference from a nucleated village.

## Why they ring the field rather than line one margin

A dispersed farm needs about **twice the margin room** of a nucleated one - its own grove plus real
spacing, no tight packing - so 15 will not fit strewn down one margin of a correctly-sized (~20-acre)
field. They dot the N + W + E dry edges instead. Placement hugs the smoothed field outline, offset
outward ~64 px so each farm is field-adjacent, and `try_place` drops any that land on the wet south
toe.

## The name is drawn, not just asserted

赤 *aka* = red, 原 *hara* = plain/moor. Akagahara sits on iron-rich **red clay**: the surrounding
non-arable ground - the cut-over hill margins, the dry-field soil, the back-slopes - reads red-brown,
the tell that names the place. A red-clay ground wash is laid UNDER the crops and scrub, so the paddy
green and the grass glyphs sit on red earth while the flooded field stays green.

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

## Settled by the GM (2026-08-12): a path does not pass through marshland

The GM ruled that village paths, not just roads, must keep off marsh - `roads_clear_of_marsh` and
`fields_clear_of_road` had both built their way-list from the road and the town streets only, so
neither had ever seen a lane. This map's connector ran 1,163 px through the reed toe - over half its length (it wound S to y=2740; the toe starts at y=1580), so it was re-routed to leave along the
contour, above the reeds, and off the W edge instead of the S.

The route is not a near miss: it keeps well clear of the recorded marsh polygon along its whole
length. A `settlement-review` pass on the result is logged in the session that made the change; its
open points were that the turn should read as terrain rather than as a bend made to satisfy a rule,
and that the toe band spanning the full canvas is itself what leaves a valley map no downslope exit.
