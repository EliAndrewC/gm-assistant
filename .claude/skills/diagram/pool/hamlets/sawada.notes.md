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

RETRACTED 2026-08-17 (same day), and the retraction is the point. The entry that stood here asked
for a ruling on "18 of 19 gardens on the E wall, which `_find_garden_spot` treats as the LAST
RESORT" plus "groves = 0". A second review reconstructed every bed's candidate signature from
`geom.gardens` against `_find_garden_spot`'s own `sides` table and the manifest refutes both halves:

- **21 SE, 2 SW, 0 E, 0 W.** ZERO beds took the last-resort E-wall candidate, in this roll or the
  previous one. SE is candidate #4 of 11 and is explicitly sanctioned. The windward wall is free.
- **`groves` is 0 for a documented and unrelated reason**: a `_nucleated` bundle emits no
  `grove_n`/`grove_w` at all (`bundle.py` - "the houses stand close and SHELTER EACH OTHER... The
  windbreak becomes a VILLAGE-EDGE belt placed in the second pass"). Sawada is nucleated, so no
  garden placement could ever have produced a per-house grove here - and the map DOES carry the
  belt the doctrine promises, 1,774 x 150 ft at aspect 11.8 on the windward side.

A ruling on that premise would have been a ruling about nothing, and it was written into this file
on one reviewer's measurement without being checked. Recorded rather than deleted: the lesson is
that a review finding is evidence, not a verdict, and a claim about WHICH candidate the placer took
is cheap to verify against the placer's own table.

THE REAL UNIFORMITY FINDING, which the wrong one was hiding: 21 of 23 beds sit SE, and `bundle.py`
promises the nucleated garden goes on "an ADAPTIVE sunny side (chosen by the placer for fit + no
shading), so it packs into a real nucleus and the gardens VARY instead of all sitting east between
houses." The adaptive choice is choosing the same side nearly every time, so all 19 homesteads read
as one stamp repeated. That is a genuine gap between the code's stated intent and its behavior, and
it is logged in `future-work.md` rather than ruled here.

## 2026-08-18 - where the ox sleeps, and a well objective that measured the wrong houses

WHAT CHANGED, ACROSS ALL FOUR SCRIPTED HAMLETS (2026-08-18)

- **`byre_form` is a knob now, and this map rolled `courtyard`.** The doctrine had been quietly
  self-contradictory: the *doma* rule says the draft ox is stalled under the farmhouse roof, while
  the byre placer drew a detached shed on the shared ground. Both are attested - a household that
  OWNS its team houses it in its own homestead (the *magariya* 曲家, whose short arm IS the stable;
  the animal range of the north-China *sanheyuan*), while a team that is SHARED or hired stands
  where the borrowing household can reach it - so per Principle XII it becomes a per-settlement
  roll rather than a ruling. `courtyard` follows the wealth (owners straight down the ranking, no
  spread objective, the spiral held to the owner's own yard); `detached_commons` follows the sharing
  and is unchanged and still the default.
- **and the overlap registry had been describing code that no longer existed.** Its entry for
  `byres` read "a draft-ox byre is an ANNEX abutting its own farmhouse (draft_byres places it
  against the wall)" - which the placer stopped doing long ago. Nothing caught it because nothing
  measured it, and that stale sentence is very likely why nobody questioned the form. The entry now
  states what holds under either form, and the geometry is GATED
  (`byres_stand_in_their_declared_form`) rather than asserted in prose.
- **the well tie-break's last key is the objective itself, not a proxy.** The primary key buckets
  coverage-plus-frame into 66 px steps so the frame term can outrank small coverage differences, and
  inside a bucket the order was distance to the cluster CENTROID - which on a two-lobed cluster is
  the empty ground between the lobes. It is now `_worst_after` at full resolution, with the
  neighborhood measure breaking exact ties.

RIPPLE ON THIS MAP: This map rolled `courtyard` and is the only pool sheet that exercises it. All
4 byres now stand as their owner's stable wing - attached to a side wall with a 3 ft drip line,
rotation locked to the house, each recording the homestead it belongs to. Before the fix this map
seated 3 of its 4 and stood them 8.9-23.0 ft off the BACK corner at rot 0, a range that overlapped
the detached maps' and so bought the knob nothing. The wells did not move: [[1605, 2308], [1583,
2066], [1363, 2000]], byte-identical to before this round. Worst walk 493 ft, mean 213 ft, and
among the 6 of 19 houses that actually need a well (the rest are within reach of surface water,
which the objective excludes by design) the worst is 122 ft. The belt carries a pre-existing gap
at y=2321 that this round did NOT cause and did not fix: it survives the flow-around change, so
its cause is not a structure. Ledgered.

**THE LEDGERED DEFECT ON THIS MAP DID NOT EXIST.** The entry said the tie-break traded a well from a
seat with 11 households within 300 ft to one with 5, worst walk 364 -> 493 ft. That counted EVERY
house. `place_wells` deliberately does not: a house within ~760 ft of a stream, channel or pond is
watered (`settlement_dwellings_watered`, the GM-settled "no redundant well beside a living stream"),
and those houses drop out of the minimax - the comment directly above the objective warns against
exactly this, two definitions of "needs a well". Re-measured with the check's own predicate: the
493 ft house is **308 ft from the stream**, 13 of 19 houses here are surface-watered, and the worst
walk among houses that actually need a well is **122 ft**. A metric that ignores a documented
exclusion will manufacture a defect, and this one survived a review round and a ledger entry.

## 2026-08-18 - the woodland commons: off the lattice, and two hamlets that had none

WHAT CHANGED, ACROSS ALL FOUR SCRIPTED HAMLETS (2026-08-18)

Two ledgered defects that turned out to be one, with a worse one underneath.

- **the commons are off the lattice, and no two are the same size.** `open_ground_patches` samples a
  uniform 90 ft lattice, scores every seat by ONE monotone function (near the cluster, leaning
  upslope) and takes the best seat outside a FIXED separation radius - three ingredients that do not
  merely tend toward an even chain, they produce one by construction. Mizuguchi shipped the proof:
  three IDENTICAL 250 ft squares stepping (+270,-270) twice; Inashiro had the same chain the other
  way. The accepted seat is now nudged up to half a step off the lattice and its size rolled +/-15%,
  both from the map's own position hash, and every nudge is re-asked through the same qualification
  test - it can only move a legal seat to another legal one.
- **a hamlet at the top of the band had no wood at all.** Kashikawa - the map NAMED 樫川, "oak
  river" - seated ZERO parcels out of 231-286 candidate seats, at every rung of the shrink ladder
  and both set-back profiles. The scan demanded the whole square inside the predicted crop window
  plus a further 16 ft, while its own gate check asks that **70% of the parcel's bbox** be inside
  the view and says outright that a parcel clipping at the edge "reads as 'more wood that way' and
  is fine". The scan mirrored the check's formula but not its WINDOW, and now judges a seat by area
  the way the check does.

RIPPLE ON THIS MAP: One parcel, 136 ft, up from 125. This map offers exactly one qualifying seat
in the whole scan - genuine scarcity, not a placer bug.

## 2026-08-18 - the six-defect pass

WHAT CHANGED, ACROSS ALL FOUR SCRIPTED HAMLETS (2026-08-18)

Six known /diagram defects were cleared in one pass, plus one regression caused inside it. In the
order they matter to a reader of these maps:

- **the front row is ONE RANK.** `front_row` had begun sampling seats by density (to stop a starved
  row leaving a big field under-ringed) and, uncapped, seated every household by itself - every
  cluster came out a single file along the paddy. It now returns seats center-out and stops at one
  rank's worth of the band; the surplus falls to the flanking and cloud passes, which seat BEHIND.
- **a lane must reach something.** Internal lane ends ran the full cluster band into open grass,
  serving no house and meeting no way, because lanes are laid BEFORE the houses they serve.
  `trim_lane_stubs` now pulls such an end back AFTER the farmstead flush - rewriting the ink in the
  stream slots the lane already owns, so nothing re-layers - and stops at the last homestead served
  rather than at the rule's edge. A near-parallel contact does not count as arrival (a lane that
  MEETS another crosses it; one that FRAYS runs alongside). A fragment below one homestead's
  frontage (~71 ft) is dropped: it can front nobody. `lanes_reach_something` gates it.
- **byres are shared, so they spread.** Owners are chosen by a maximin spread, then - among the
  near-best - by how many households stand within borrowing distance. Spread alone picked the most
  ISOLATED homestead, which is the inverse of a shared shed.
- **the title placard may not sit on a woodland commons.** Dense canopy is an obstacle to the title
  the way a grove already was; only the sparse grazing scrub is not.
- **`scatter_audit` could not see tree crowns.** Its palette had drifted from the engine's; it now
  imports `CROWN_FILLS`, and a coverage guard fails when the two disagree.
- **the SVG emits the rake it placed** (`.1f` / `.2f`, not whole pixels and whole degrees), and the
  gate reads the same raked corners the placer does.

RIPPLE ON THIS MAP: the title placard no longer sits on the dry-shoulder woodland parcel - it
covered 64-68% of it, with a dozen crowns ghosting up through the title card, and the overlap is
now zero. The west fork was the map that motivated the lane trim: lane 0 ran 90 ft past its own T
with lane 2 and died 13 ft from it on an 8-degree divergence, reading as one track fraying rather
than a fork. Byres went from 20% of the settlement's length to spanning it. Cluster elongation
4.60 -> 3.49, with a real back rank. Review: needs-work on the fork, now fixed.

THE FORK IS WHY THE CHECK LEARNED ABOUT ANGLES: `_reaches` counted ANY way within 40 ft as arrival,
including the lane an arm had already met at its own junction - so the defect satisfied the test
written for it. Proximity is not arrival.
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

**On this map, measured on the SHIPPED manifest against main's tip.** 843 -> 818 basins (the largest
share in the pool); smallest surviving basin 379 sq ft against a 372 sq ft floor; total plot area
+0.001% - absorbed, not deleted; 19 of 19 households; field outline unchanged.

**The cluster partly re-packs: 14 of 19 houses unmoved, min-max displacement 135 px.** An earlier
draft said "6 of 19 move, up to 78 px ... the view holds" - wrong on both counts, and the metric is
why: 78 px was each new house's distance to the NEAREST OLD one. Lane frontage improved most here,
median **118 -> 91 ft**.

**Three defects review caught on this sheet, all fixed:**

- **A flooded plot fused to the drain outfall read as a POND**, on the one map whose whole brief is
  that it has none. Every tint predicate passed it correctly - min apex 81.4 deg, solidity 0.910 -
  because the defect is SITING, not shape. A fourth clause now demotes a blue plot within 1.5 plot
  widths of the collector's terminus; the closing rank ALONG the drain keeps its tint.
- **A self-intersecting bow-tie ring at (167, 2558)**, invisible in ink (the neighbor overpaints the
  stray edge) but not a simple polygon, so every shape metric on it was meaningless. Now REPAIRED by
  `buffer(0)` rather than dropped - dropping cost 12 cohort seeds, then 2 more purely to RNG
  rotation. Zero self-intersecting rings on all four maps.
- **The windbreak lost 46% of its canopy to the first version of the frame fix.** Restored to 171
  clumps; see the shared entry below.

**Still open**, raised by review and left with its measurement: the woodland commons went 2 -> 1
parcels this roll (a 54-crown stand at (230, 3040) did not re-seat), and the SE pocket's two
households still sit 240-292 ft from any internal lane. Both in `future-work.md`.
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

### 2026-08-18 - the windbreak frame fix, corrected: CLIPPING IS THE DOCTRINE

Recorded once here and referenced from all four hamlet notes, because the mistake was general.

A review asked for a belt whose clumps were "touching the frame" to be contained. The fix inset the
allowed window by a canopy reach, which required the WHOLE crown to be inside - and that is
backwards. `settlements/presentation.md` (GM 2026-07-20) says the belt CLIPS at the view edge and
"a partially visible belt reads as 'the wood continues'"; `hard_features_within_frame` demands
partial visibility of a village grove rather than containment. Only a clump with **no visible ink**
is waste.

The cost of getting it backwards, measured by two independent reviews: Mizuguchi dropped **40
clumps to remove 3 invisible ones** - 37 at least partly visible, 12 not even touching the frame -
leaving a ~100 ft bare channel through the middle of the wind wall on the windward side; Sawada lost
**46% of its canopy** and its belt became shorter than the cluster it shelters.

Inverted to skip only a clump lying WHOLLY outside the frame. Result across the pool: **zero
invisible clumps on all four maps**, belt gaps 26-37 px against a 30 px baseline, and clump counts
164 -> 169 (Inashiro), 212 -> 190 (Kashikawa), 131 -> 127 (Mizuguchi), 231 -> 171 (Sawada) - the
Sawada figure being the re-pack's own effect on the house cloud the belt derives from, not the clip.

**The transferable part**: the first review's complaint was itself against a documented rule, and
following it literally made three maps worse. A reviewer's finding is evidence, not a verdict - check
it against the doctrine file before acting on it.

## Feature 123 - the lane web (alleys)

**10 of this map's 19 farmhouses stood more than 100 ft from any way. Now none do** - the worst is
77 ft and the median 44 - **and every lane on the sheet belongs to one connected
network**, which is the part that took two review rounds to get right.

The research is decisive that a house in a nucleated cluster is reached: "every house in the
nucleated village is accessible via the interconnected system of narrow lanes and alleys". The FORM
is a seeded knob, because the record supports two and two supportable answers become variance rather
than a choice (Principle XII). This map rolled **`alleys`**, which narrow LATERALS threading back between columns of houses, hung off the skeleton - the accretive Chinese gridiron, the form that says the place GREW. It carries **11 web
lanes** of 15.

**Four things here are load-bearing, and each was learned by getting it wrong first.**

*The web is laid last of the built things* - after the houses AND their byres, sheds and wells. Laid
before the houses it reserved ground from a cluster not yet packed and grew the four hamlets' long
axes 15-97%; laid between the two it exiled byres up to 210 ft and erased feature 121's
borrow-coverage fix. Reviewers verified the final order costs nothing: byres and wells are
byte-identical to the pre-web manifest, coordinate for coordinate.

*Connectivity is decided before any ink.* Candidate runs grow outward from the skeleton and only the
reachable ones are drawn, because a lane once drawn cannot be taken back.
`farmhouses_reach_a_way` enforces the same thing from the other side - it measures to the connected
COMPONENT containing the connector, since a check an island can satisfy rewards drawing an island,
which is exactly what the first version did. Orphaned SKELETON arms are linked too; the transitive
check found some, which no rule could see before.

*A lane is not drawn where a reader would see one lane twice.* A run that shadows an existing way -
by fraction OR by one unbroken bundle pitch - is refused, and so is one that would run the length of
the shelter belt rather than crossing it.

*A house is served with margin, not to the millimetre.* The footpath pass triggers at nine tenths of
the reach, so no house passes by inches and none gets a path drawn to cure a rounding error.

Where the regular web still cannot reach a steading, that house gets what an outlying farmstead
really has: a footpath of its own, routed round the neighboring plots rather than ruled at them,
stopping at its first contact with the network, and planked where it crosses a ditch.
