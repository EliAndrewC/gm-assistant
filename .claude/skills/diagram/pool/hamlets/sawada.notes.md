# Design notes: Sawada (沢田, "marsh paddy") - scripted hamlet, the OFF-MAP drain

*One of four demo maps from the scripted-generation experiment (2026-08-11). See
[`../../hamletgen/`](../../hamletgen/) for the pipeline and
[`inashiro.notes.md`](inashiro.notes.md) for the head-to-head with the authored Ikegami.*

**Kanji triangle**: 沢 *sawa* "marsh, mountain stream" + 田 *ta/da* "paddy". Sawada, "the paddy by
the marsh" - the name states what the map has to draw correctly: the reclaimed rice stops where the
undrained valley toe begins.

**Subject**: ~19 households, land falling to the northwest, and the largest of the four combs.

**What it is here to show**: the OTHER water sink. Sawada has no pond. Its collector runs on past
the last paddy as a brook and leaves the frame, to join a stream or another farm's ditch somewhere
the map does not have to care about - which is what most real valleys do, and which the GM's brief
named as the equally-ordinary alternative to a tameike. The brook's LENGTH is derived from the
distance to the canvas edge along the fall, not from a constant: `draw_comb_field`'s own brook runs
a fixed 520 px, which is a number tuned against the canvases the authored maps happened to use and
stops in open ground on a wider one.

Below the drain, the un-reclaimed toe is reed marsh - the `hinterland` scatter's contour band, on
the low side where the gate requires it.

**Known open**: shares Inashiro's two - the bare comb floor on the fan's shoulders (inherited from
`build_comb`), and a windward quarter derived from the slope rather than declared regionally.

- 2026-08-15 (supply-bank hem re-roll): bunds hem onto the supply channels' banks; the map
  re-rolled downstream. `settlement-review` (DELTA) confirmed the banks read correctly on every
  straight run and caught the two things the first cut missed, both fixed the same day: junction
  WEDGE plots whose corners were dry while their edges crossed the water (the carve and the gate
  now walk every bund EDGE at a 3 px step - pre-fix manifest frozen as
  `pool/regressions/paddy_bunds_clear_the_supply_channels_fires_on_edge_crossing_sawada.json`),
  and the collapsed micro-plot jumble in the branch-6/canal wedge (gone with the edge-walk drops;
  the drain-hem pass was the fourth quad producer needing the same guard). The dry SE arm the
  review flagged got its well via the coverage-greedy well sort.

- 2026-08-16 (the fork draws both arms - engine change, this map re-rolled): the GM's Inashiro
  question settled in research/water.md "The head-race forks - supply commands both flanks";
  every `OFFTAKE_LADDER` row now draws canal B, gated by `comb_supply_commands_both_flanks`.
  This map re-rolled three times as review fallout was fixed at the engine (canal-B thread
  tails via interpolated piece boundaries, minimax worst-served well placement, the notice
  board's grove-clump keep-out, accidental-lane-crossing guards). Review log: round-2 DELTA
  flagged a copse clump swallowing the notice board and two lane arms crossing mid-run (both fixed at the engine); round-3 follow-up in the session of 2026-08-16.

- 2026-08-16 (known-opens round - floor trim, woodland re-seat, seeding trace; this map
  re-rolled): the ledger's four fork-re-roll defects were closed in one session. The comb floor is
  now TRIMMED to the collector's command area (`floor_overhang`, gate
  `comb_floor_ends_at_the_collector`); woodland commons seat inside the predicted kept window AND
  off the marsh (`open_ground_patches` frame + marsh keep-outs, shrink ladder 250 -> 200 -> 160 ->
  125 ft; gates `woodland_commons_within_the_frame` / `woodland_commons_on_dry_ground`); and
  `meta.cluster_seeding` records the seeding mode always ("frontage" on this roll).
  Map-specific: the corrected derivation's honest woodland count is ONE 125 ft parcel on the dry
  shoulder between marsh and placard (the ask was 3; this composition's dry in-frame ground is
  genuinely tight, and its name story is the marsh, not oaks). Review log: full DELTA verified the
  trim and the frame fix, and caught the 97%-marsh parcel that drove the marsh keep-out;
  follow-up pass on the re-seat.

- 2026-08-16 (second known-opens round - flooded-sliver demotion, well/check alignment,
  recorded woodland canopy, trim dedup; this map re-rolled): pointed plots (interior angle
  < 25 deg) no longer take the FLOODED tint and the painted tint is recorded as
  `flooded_plots` (gate `flooded_plots_read_as_basins` at 15 deg); the well minimax and
  rescue read `settlement.surface_water_dist` - the watered check's own predicate - so wells
  stop chasing stream-watered houses; woodland stands record their crowns (`tree_crowns` +
  per-parcel count, gate `woodland_commons_visibly_stocked`) and register as placer
  keep-outs; the trim corner's duplicate vertices are merged (`dedup_ring`).
  Map-specific: THE no-pond map - of 7 painted blue plots, the pointed fan-seam needles (reading
  as tiny triangular ponds at the collector junctions) are demoted to green; 4 basin-shaped
  flooded strips survive (SVG fill census: 4 painted, 4 recorded, 1:1) and read as wet paddy
  rows. The exactly-25.0-deg survivor pair at the west seam is the ACCEPTED boundary case - it
  composes as one flooded plot, not a pond. A second 125 ft coppice seated in the SW corner
  (18 crowns, the review's "form done right") beside the original dry-shoulder parcel (12
  crowns - straggly per the review, logged as cosmetic).

## 2026-08-17 - the fan-toe needle fix, and the tint threshold it collided with

The fan-toe SUNBURST ruling (full research in `research/fields.md`, "A basin never tapers to a
point"; engine changes in `_comb_toe_and_hem`, `close_seams` and `_absorb`). Sawada carried 7 rings
under the 15 deg gate line and now carries none, at a cost of **-0.27% cultivated area** - the
sunburst was bought out almost for free, because the needles were removed by re-subdividing and
absorbing rather than by deleting paddy.

**The review CAUGHT a real error this session would have shipped**, and it is the kind only a second
pair of eyes finds: the new placer floor `_TOE_MIN_APEX` was set to **25 deg**, which is exactly the
value `pointed_ring` used as the FLOODED-tint demotion threshold. After the fix no ring below 25 deg
exists anywhere, so the demotion became **structurally dead** - it could never fire on placer output
- while the sharpest survivors piled up on its boundary at 25.05 and 25.23 deg. One of them, a NEW
91 x 18 ft blue triangle at (350,2483), missed demotion by **0.05 deg** and shipped as the most
pond-like object on the one map whose brief is "no pond".

The first fix was to lift the demotion clear of the placer floor: `_TINT_MIN_APEX = 40.0`.
**Superseded the same day** - Inashiro's review measured that raising the threshold was wrong in
both directions (it demoted a 35.5 x 118.3 ft honest strip while still passing a plot that tapers
30.0 -> 3.4 ft, because a corner angle cannot see a taper whose tip is TRUNCATED), and that the
"empty 25-40 band" this reasoning rested on does not exist - 15 plots sit in it on Inashiro alone.
The rule now asks the right question instead: the threshold is back at **25**, and the ring is
DEDUPED AT AN END WIDTH (`_TINT_END_FT` = 5 ft, the narrowest end that can hold water: two aze at
1.5 ft leave ~2 ft of standing water between them) so a truncated needle shows the apex it really
has. That also un-deadens the predicate without a threshold race, because it is now a different
MEASUREMENT from the placer's guard rather than a number sitting beside it.

Two further items the review raised, logged rather than fixed:

- **The west seam HUB.** ~7 bunds still meet at one point one step inland from the fixed toe, with
  90-ft wedges running into it. Every apex is now legal, but the composition is the same read the GM
  objected to at the collector. Needs a ruling: does it govern only the toe, or every convergence
  node?
- **`wet_plots` fell 36 -> 21 (-42%)** while plot count rose 867 -> 881, because the dropped and
  absorbed needles were low-edge plots. No consequence here (no overlay, no pond), but
  `overlays_on_wet_ground_only` and the pond-siting checks draw eligibility from that set, so a
  converted map WITH overlays could see its eligible set halve as a silent side effect.

Catch-rate: round-N DELTA - CAUGHT the tint-threshold collision (above); raised the seam hub and the
`wet_plots` side effect; verified clean by its own measurements that the toe reads as a real cascade
toe, that no declined weld opened floor reading as a hole (floor fill = plot fill at the pixel), that
no new doubled bund appeared, and `scatter_audit` 0 violations.

## 2026-08-17 - re-packed by feature 121 (the placer tests the rake it draws)

14 of 19 houses moved; the windbreak re-derived, both woodland parcels re-seated, the viewport
shifted 20 px. Household count unchanged.

WHY the corridor changed: see kashikawa.notes.md's entry of the same date, or
specs/121-placer-drawn-footprint/research.md D1/D6/D7.

**`gardens` 23 -> 20 IS NOT THREE LOST GARDENS - do not re-open it.** `gardens` counts BEDS. Every
one of the 19 households has a bed before and after; what fell is bed FRAGMENTATION - households
drawn with two beds went 4 -> 1. Total dooryard area 12,221 -> 12,202 sq ft (-0.16%), mean per
household 643 -> 642. `_garden_beds` splits on `self._hjit(hx, hy, 8.0) < 0.26`, a POSITION hash, so
moving 14 houses re-rolled it; the settlement-review recomputed the hash independently and confirmed
the set that split is exactly the set the hash says should, with zero blocked by width guards.
Expected ~4.9 splits from 19, landed 1 - a ~2.5% lower-tail draw. Unlucky, not systematic, and a
re-roll would take the texture back.

MEASURED HERE: tightest raked-corner-to-tread gap 46.4 -> 27.3 ft, median house-to-lane 125 -> 121,
min 71 -> 51. Houses moved ONTO the lanes without crowding them. Farm sheds 4 -> 5 = 26% of
households, closer to the ~30%-had-a-storehouse research norm than the old 21%. `scatter_audit`
exit 0, 0 violations across 443,994 bases.

Review verdict: PASS.

FOUND BY THAT REVIEW AND FIXED IN THE SAME FEATURE: the house glyph emitted
`translate({cx:.0f},{cy:.0f}) rotate({rot:.0f})` - whole pixels and whole DEGREES - while the placer
clears and the gate measures full floats. Every one of the 19 drawn rakes differed from its recorded
rake, up to ~0.95 ft of drawn-corner displacement. Nothing was at risk here (tightest gap 27.3 ft),
but it is exactly the drawn-versus-placed divergence this feature exists to close, and no check can
see it because every check reads the manifest and never the SVG. Now `.1f` / `.2f`.

OPEN, pre-existing and tier-wide, raised for a ruling rather than a fix: 18 of 19 gardens sit on the
E wall, which `_find_garden_spot` treats as the LAST RESORT (keeping the garden off the windward
wall is what frees that wall for the grove). `windward="NE"` makes E windward here, so the last
resort is winning 18 times out of 19 - and `groves` is 0, as it is in 12 of the 13 pool hamlets.
Sawada is the map that shows why homestead groves never appear at hamlet tier.

## 2026-08-17 - the paddy size floor: a basin too small to be worth its own bund

The GM, reading a hamlet sheet: *"most of the rice paddy fields are rectangular, but then there are
a few very small triangles. Is that realistic? It looks like it is just a mistake, like, basically,
a rendering artifact rather than something that is from our historical research. Relatedly, should
there be a minimum rice paddy size?"*

Three answers came out of the research pass, and only one of them is yes. There is **no absolute
minimum** - Shiroyone Senmaida works 1,004 basins on ~4 ha, averaging ~18-20 m2, the smallest about
half a meter square - so a floor in acres was declined. **Four-sides-only** was declined too: it
would re-impose the *kochi seiri* consolidation grid the research already flags as the anachronism.
What is real is a **ratio**: on a terrace the wall is a riser the slope demands anyway, but on a
valley-floor fan the aze is the whole structure, built only to hold water and re-plastered every
spring, and the alternative to a scrap is never no-rice - it is making the basin next door bigger.
So a comb basin under **0.25 of the fan's own design cell** is dropped by the toe pass and absorbed
by `close_seams`; the gate `paddy_basins_are_worth_their_bund` fires under 0.20. The triangularity
was the symptom - a fragment clipped off the lattice at the fan boundary comes out triangular - and
the size was the cause. Full findings, both declined alternatives, the two derivations of 0.25 and
why the gate could not sit at 0.15: `research/fields.md`, "Minimum basin SIZE".

**On this map.** 843 -> 818 basins (-25, 2.97%, the largest share in the pool); 25 fragments into 20
hosts; smallest surviving basin 379 sq ft against a 372 sq ft floor. Acreage +0.001% - absorbed, not
deleted - 19 of 19 households, field outline unchanged.

**The cluster partly re-packs**, and the numbers here are the ones that taught the project to state
its metric (settlement-review, 2026-08-17). A first draft said "6 of 19 houses move, up to 78 px ...
the view holds". Both halves were wrong: 78 px was each new house's distance to the NEAREST OLD one,
which lets one old house partner several new ones; under a one-to-one matching the largest
displacement is **286 px** at minimum and 471 px on the min-total pairing, with a household leaving
the mid-string for the SE pocket (pocket 1 -> 2, string 10 -> 9). And `meta.view` GREW - it did not
hold - to contain exactly that move. Post-fix: **11 of 19 unmoved, min-max 540 px**, gardens
20 -> 23, farm sheds 5 -> 6.

**Lane frontage, fixed here rather than ledgered** (Principle XIV): front-row seats must lie within
150 px of a drawn lane, the first five exempt for `field_ringed`. This map improves most of the four
- **median 118 -> 77 ft**, houses past 150 px 6 -> 3 - and it is the map that showed the naive
version does nothing (a relaxation ladder simply re-seated the refused houses; recorded at the point
of change).

**Logged, not fixed.** The self-intersecting bowtie ring at (167, 2558) is byte-identical before and
after and worth naming because the new floor cannot reach it: its shoelace area is nearly 3x the
floor, so a bowtie passes as a comfortable basin. The two-household off-lane satellite (628 and
701 ft from any drawn lane, no path to it) and the windbreak sheltering 17 of 19 rather than 18 are
GM questions rather than defects - both are in `future-work.md`.
**The regression it caused, and how it was cleared.** The rule shifts the drawn plot count, which
rotates the shared placement stream, and on rolled cohort seed 41 the rotated roll seated a well
outside the house cloud and tripped `crop_not_held_open_by_one_feature` - seeds 1-48 went 45/48 ->
44/48. Measured in a detached worktree, seed 41's FIELD geometry was byte-identical either way, so
the failure was not a paddy defect at all: it was a well landing on a pre-existing weakness in
`hamletgen.place_wells`, whose minimax tie-break (distance to centroid) cannot express "this seat is
outside the settlement". The GM's call was to take that fix as its OWN piece of work first and land
the floor on top, which is why `e0fb2417` precedes this entry in history. With both in, seeds 1-48
are back to **45/48 with residue identical to baseline** - seed 41 passes and nothing else moved.
Cohort seed 62 still fails the same check and always did: its northern lobe has no interior seat in
its minimax bucket at all, so a tie-break cannot reach it (ledgered in `future-work.md`).
