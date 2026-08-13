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
neither had ever seen a lane. This map's connector ran 1,163 px through the reed toe - over half its length (it wound S to y=2740; the toe starts at y=1580), so it was briefly re-routed to leave west.

**That re-route was then UNDONE, and the original S back-slope route restored** (same day), for the
reason recorded on Ikegami: the toe band was taking its width from the canvas rather than from the
ground the fan waters, which was never a rule. Researched and corrected - an alluvial fan's spring
line follows the fan's toe. Akagahara's toe now ends at x=407 and the back-slope thread through its
strewn farms is dry for its whole length. See `research/water.md`, 'The wet toe is as wide as the FAN'.

The route is not a near miss: it keeps well clear of the recorded marsh polygon along its whole
length. A `settlement-review` pass on the result is logged in the session that made the change; its
open points were that the turn should read as terrain rather than as a bend made to satisfy a rule,
and that the toe band spanning the full canvas is itself what leaves a valley map no downslope exit.

## Two review findings fixed (2026-08-12)

`settlement-review` on the narrowed toe raised two things that pre-dated that change, and both are
now fixed at the ENGINE rather than on this map, so no other map can grow them either:

- **A wellhead stood in the reeds** at (1763,1757), inside the toe and ~50 ft from the drainage
  pond. The cause was DRAW ORDER: wells are placed early, the marsh is drawn late by `hinterland()`,
  so the reeds appeared around a well that was sited before they existed. `_well_ground_clear` now
  consults `toe_band()` - derivable in advance, which is why it was factored out - and the placer
  re-sites the well up among the dwellings. New check `wells_off_the_wet_toe` holds the line, and
  the pre-fix manifest is frozen in `pool/regressions/`. **What it cost:** that well was the nearest
  water for the two SE ring farms (111 px), and they are now 741 and 622 px from one. That is
  accepted rather than patched - this gen's own comment says the wells "serve the DENSE W-margin
  cluster (the E/N ring farms draw from the field ditches beside them)", and `farm_wells_within_reach`
  exempts map-edge steadings for the same reason - so the reed well was a stray of the grid, not
  their supply. The grid put a replacement at (278,1188) among the west row. Note the check measures ground below the
  crop's LOWEST point, not the toe polygon: the band's uphill lip tucks under the field by design
  and carries no reeds, so testing the polygon would flag legitimate wells on that lip.
- **The connector read as a map border.** 123 px of drift over 2,440 px - a ~3 degree lean with no
  reversal, drawn parallel to the left frame - against a gen comment that had always claimed it
  "winds". It now MEANDERS within its own corridor: +-20 px of reversal about the old line, five
  direction changes, sinuosity 1.0001 -> 1.0018, max lateral deviation 10.9 -> 34.2 ft. Endpoints
  unchanged.

  **The first attempt at that was worse than the defect.** Bulging east to x=400 swept the wellhead
  at (373,814) and the farm at (389,1189) out of existence - 4 wells became 2, 15 houses became 14,
  worst house-to-well went 536 -> 1,129 ft - and the GATE PASSED ALL OF IT, because the coverage
  checks have tolerances a strewn hamlet stays inside. A way re-shaped for legibility has to be
  measured against the placements it displaces, not just gated. The shipped meander keeps its
  eastward peaks at y=520 and y=1000, where the row leaves room.

Still open from that review, and NOT fixed:

- The track passes the west row at 52-137 ft to the walls but does not thread the six N and E farms,
  which have no drawn way of their own.
- Its bends are keyed to where there is ROOM rather than to something a walker goes to. Keying the
  eastward swings to the notice board (388,582) and the well (373,814), and the westward ones to the
  groves, would make the shape read as history rather than as clearance.
- The mid-row well stands across the track from every dwelling. Not an oversight - see the gen: the
  verge between lane and steadings is full, and seven candidate seats along it were all refused.
- Three east-row farms are 501 / 622 / 741 ft from a well. `farm_wells_within_reach` encodes the
  500 ft doctrine but is gated to town/city scale, so nothing enforces it at hamlet scale - the
  argument for these three (map-edge steadings, field ditches 116-315 ft off) is sound but it is an
  argument, not a check. Whether a dispersed hamlet's ring farms are expected to have a well at all
  is a GM ruling that would generalize to every dispersed map.
