# Design notes: Mizuguchi (水口, "water mouth") - scripted hamlet, water entering from the west

*One of four demo maps from the scripted-generation experiment (2026-08-11). See
[`../../hamletgen/`](../../hamletgen/) for the pipeline and
[`inashiro.notes.md`](inashiro.notes.md) for the head-to-head with the authored Ikegami.*

**Kanji triangle**: 水 *mizu* "water" + 口 *kuchi/guchi* "mouth". Mizuguchi, "the water mouth" - the
intake itself, the sluice where the brook is turned into the head-race. A hamlet named for the one
piece of engineering that makes it possible.

**Subject**: the smallest of the four - ~12 households on land falling due EAST, so its head sluice
stands on the western margin and the comb fans away from it across the map.

**What it is here to show**: that the pipeline is not oriented. Every stage works in the fall frame,
so a map whose land falls east is not a special case: the intake is still at the head, the drain
still crosses the low side, the marsh is still on the toe, and the cluster still takes a margin with
its back to the high ground. Its lane skeleton and cluster shape are rolled, not chosen, and
re-rolls move them - this paragraph deliberately records the mechanism and NOT the current
outcome, because concrete claims here went stale twice (the 2026-08-15 review caught a
`cross`/round claim, the 2026-08-16 one a west-margin band claim).

**Known open**: shares Inashiro's two - the bare comb floor on the fan's shoulders (inherited from
`build_comb`), and a windward quarter derived from the slope rather than declared regionally. Also:
a hamlet NAMED for its sluice draws no sluice glyph at the intake (the brook necks into the
head-race) - a pipeline note, logged in `future-work.md`.

- 2026-08-15 (supply-bank hem re-roll): bunds hem onto the supply channels' banks; the map
  re-rolled downstream and gained a second well. `settlement-review` (DELTA) passed the
  bund/channel read and caught both wells serving the same lobe - fixed the same day by making
  every well after the first take the legal seat FARTHEST from the wells already placed
  (`hamletgen.place_wells`), which put the second well by the eastern houses. It also caught this
  file's stale `cross`/round claim and a gen docstring copied from Inashiro's - both fixed.

- 2026-08-16 (the fork draws both arms - engine change, this map re-rolled): the GM's Inashiro
  question settled in research/water.md "The head-race forks - supply commands both flanks";
  every `OFFTAKE_LADDER` row now draws canal B, gated by `comb_supply_commands_both_flanks`.
  This map re-rolled three times as review fallout was fixed at the engine (canal-B thread
  tails via interpolated piece boundaries, minimax worst-served well placement, the notice
  board's grove-clump keep-out, accidental-lane-crossing guards). Review log: round-2 DELTA
  flagged the exterior second well (fixed: minimax moved it to serve the worst-served west house, 532 -> 444 ft); round-3 follow-up in the session of 2026-08-16.

- 2026-08-16 (known-opens round - floor trim, woodland re-seat, seeding trace; this map
  re-rolled): the ledger's four fork-re-roll defects were closed in one session. The comb floor is
  now TRIMMED to the collector's command area (`floor_overhang`, gate
  `comb_floor_ends_at_the_collector`); woodland commons seat inside the predicted kept window AND
  off the marsh (`open_ground_patches` frame + marsh keep-outs, shrink ladder 250 -> 200 -> 160 ->
  125 ft; gates `woodland_commons_within_the_frame` / `woodland_commons_on_dry_ground`); and
  `meta.cluster_seeding` records the seeding mode always ("frontage" on this roll).
  Map-specific: the SE bare-green needle (~350 ft of floor past the drain's thin head - this map's
  own ledger item) is gone, and the trim frees command-area ground the placers RE-USE (what stands
  there is roll-dependent - the merged roll seats two farmsteads and the second well on it); three
  dry woodland parcels (250/250/160 ft). Review log: full DELTA verified the trimmed corner
  reads as worked field (bund-edged hem staircase, not a cut) and caught the marsh-seated parcel
  that drove the marsh keep-out; follow-up pass on the re-seat. Cosmetic residue logged, not
  fixed: the collector's blue stroke fades out along the hem staircase at the trimmed corner
  (topology green, ink only).

- 2026-08-16 (second known-opens round - flooded-sliver demotion, well/check alignment,
  recorded woodland canopy, trim dedup; this map re-rolled): pointed plots (interior angle
  < 25 deg) no longer take the FLOODED tint and the painted tint is recorded as
  `flooded_plots` (gate `flooded_plots_read_as_basins` at 15 deg); the well minimax and
  rescue read `settlement.surface_water_dist` - the watered check's own predicate - so wells
  stop chasing stream-watered houses; woodland stands record their crowns (`tree_crowns` +
  per-parcel count, gate `woodland_commons_visibly_stocked`) and register as placer
  keep-outs; the trim corner's duplicate vertices are merged (`dedup_ring`).
  Map-specific: the seam needles by the head junction are green now (3 basin-shaped flooded
  strips survive, review-verified tint-vs-record agreement); the two wells re-seated under the
  aligned objective - one per well-dependent lobe, none on the stream-served west lobe; the
  three woodland stands kept their seats with recorded canopies (89/90/30 crowns; the 89/90
  twin-ness of the two big stands is a logged cosmetic nitpick).

- 2026-08-16 (fan-toe pond fix, same session as Inashiro's; this map re-rolled): the same bbox-fit
  defect - this map's pond (31.3 x 32.0 at (1570, 875)) was crossed by bund lines. Under the
  polygon-fit `_plot_pond` the original plot refused and the pond moved to (1392.4, 1188.3),
  12.8 x 10.7, sunk into one 65 x 54 ft low plot at the field's eastern foot; the old site healed
  completely (bunds and beans re-tiled). DISCLOSED FALLOUT: a grave island appeared at
  (1066, 1065) - `rng.sample` consumes a different number of draws than `rng.choice`, so the
  downstream 30% grave roll inside the feature-012 scope flipped. Accepted and documented at the
  point of change (the blast radius is one field's own flourishes; the grave is legitimate and
  gate-eligible). OPEN DECISION, with sketch: if in-field flourish coupling ever bites again,
  give each sub-feature its own stream in `_paddy_features` (random.Random(seed ^ 0x9AD1 ^
  per-feature salt) for pond, rock and grave each) - lands in settlement/fields.py, held by
  test_paddy_features_cover_every_archetype_branch, costs one more pool-wide flourish re-roll.
  Review log: DELTA pass; the reviewer caught the grave island (undisclosed in the brief) and
  verified pond containment, old-site healing and 0 scatter violations; the rim kisses its bund
  at 0.65 px (nitpick, physically fine - dug up to the bund).

## 2026-08-17 - re-packed twice: feature 121, then the front-row cap

**Read this entry, not an earlier draft of it.** A first version was written after the feature-121
re-pack and was refuted by the very next roll - it quoted lane-2 frontage clearances of
11.8/8.9/8.1/15.2/9.8 ft and left an OPEN item about a merging pair at (829.4,1682.7)/(771.5,1693.6).
Neither survives: the map re-rolled twice more the same day, those two houses do not exist, and the
closest house to any lane is now 42 ft. Rewritten from the shipped manifest.

WHAT HAPPENED, in order. Feature 121 made the placer test the rake it draws and dropped
`LANE_CLEARANCE` 48 -> 40. Then `front_row` began sampling seats by bundle pitch instead of by
household count, to stop a starved row leaving a big field under-ringed - and, uncapped, it seated
every household by itself. Mizuguchi came out **891 x 123 ft, aspect 7.24**, with an rms residual of
22 ft about a smooth curve: no house stood behind any other anywhere on the map. Its copse collapsed
11 -> 4 clumps and its byres were pushed out of the courtyards into the windbreak, because a
one-rank cluster has no interior gap ground. Then the front row was capped at one rank's worth of
the band, and the surplus went back to the flanking pass, which seats BEHIND.

WHERE IT LANDED (settlement-review, verified against a correctly-registered render):

- cluster **511 x 276 ft, aspect 2.01** (eigen) / 1.85 (extent), against 7.24 in the ribbon state and
  5.85 before any of it. rms residual about a best-fit curve **22 -> 68.9 ft**, max 140 - larger than
  a farmhouse's own 28 ft depth, so the houses are genuinely off any single line.
- **four depth bands** to the field outline: 18/41/58/58, then 96/101/116/128, then 193/193/216,
  then 297 ft. Everything past 150 ft (the front row's furthest standoff) was seated by the flanking
  pass - the mechanism working as intended.
- copse **4 -> 18 clumps**, threading the courtyards the ranks reopened; better than the 11 it had
  before any of this. Nobody touched the grove code - it followed the cluster.
- all three byres out of the windbreak (32/89/145 ft from the nearest clump, none under canopy). One
  is a textbook courtyard stall between four homesteads; two sit in an open western pocket 84-85 ft
  from the nearest house, so the recovery on this symptom is partial where the copse's is complete.
- minimum house-to-house footprint gap **2.0 -> 10.8 ft**, rest at 27+ ft. The merge is gone.
- notice board at the traffic optimum: 10 of 12 houses within 250 ft, equal to the best point on the
  map, even though every house it is measured against moved.

THE COST, recorded rather than left implied: fronting loosened. Median house-to-lane is back to
~98 ft (4 of 12 within 60) from the ribbon's 77 (10 of 12). The ribbon's tighter fronting was an
artifact of the defect, not a baseline worth keeping - but ~98 is the figure an early review
criticized against Ikegami's 55, and the flanking pass is where a future tightening belongs, since
it is the pass now doing the seating.

THE MERGE RULE ITSELF is `farmhouses_shed_separately` (8 ft wall to wall, two thatched drip lines
plus a footpath). The pre-rule manifest is frozen in
`pool/regressions/farmhouses_shed_separately_fires_on_the_pre_rule_mizuguchi.json` - which matters
more than it looks, because this map has since re-rolled twice and the motivating pair no longer
exists anywhere but that fixture.

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

RIPPLE ON THIS MAP: lane 2 shortened; byres re-sited and their SERVICE improved - mean house-to-
nearest-byre 126 -> 109 ft, median 143 -> 101, households within 150 ft 8/12 -> 10/12, worst walk
235 -> 165. (An intermediate version of the byre fix made those numbers WORSE: it maximised spread
among the byres rather than service to the houses, which a review caught. The borrow-coverage term
is what fixed it.) Houses and the cluster's four depth bands are untouched. Review: PASS.

THE CROWN-PARSE DEFECT WAS FOUND HERE and is worth remembering: `scatter_audit` reported
"crown checked, 0 violations" while seeing 63% of this map's crowns, because `CROWN_FILLS` claimed
to be exhaustive and was not. It is now checked against real ink rather than asserted.
MECHANISM: feature 121 made the placer test its raked quad against the LANE TREAD, but house-to-
house separation is still adjudicated on the whole-bundle BBOX (`_bundle_side_fits`), which knows
nothing about either house's rake. Measured across the four scripted hamlets, this is a lone
outlier - inashiro/kashikawa/sawada sit at 28.8/25.5/23.0 ft minimum and only mizuguchi has a pair
under 6 ft - so a rule with a lot of headroom would catch it and disturb nothing else.

SKETCH (check before fix, per the project rule): add a gap verdict using the existing
`within_edge_gap(a, b, N)` helper over `M["houses"]` pairs - it already measures real footprints -
confirm it fires on mizuguchi and on nothing else in the pool, then require the same clearance in
`_bundle_common_fits` against every placed house's raked quad (the sun-corridor rule already reads
neighbors' geometry off `M["houses"]`, so the precedent and the plumbing both exist). Ground the
number in "two thatched roofs must shed separately" - the principle research/buildings.md already
records for a building against a compound wall.

DEFERRED DELIBERATELY: this is a NEW rule, not a regression (no check fires, and the gate is 22/24
before and after), so it was not folded into feature 121's scope.

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

**On this map, measured on the SHIPPED manifest against main's tip.** 519 -> 511 basins; smallest
surviving basin 407 sq ft = 0.273 of the design cell, and **zero** basins under 0.25; acreage
715,843 -> 715,849 sq ft (6 sq ft in 716k, conserved); 12 of 12 households; field outline unchanged.

**THE CLUSTER DID NOT MOVE AT ALL - 12 of 12 houses unmoved, and an earlier draft of this entry
claimed otherwise** (settlement-review 2026-08-18 diffed it key by key). Houses, gardens, farm sheds,
byres, wells, threshing yards, lanes and the kosatsuba are byte-identical to main's tip. Only the
fabric, the windbreak (131 -> 127 clumps), the crowns and the view-derived records moved. The draft
also said "gardens 16 -> 17" (14 -> 14), "farm sheds 2 -> 1" (3 -> 3) and "byres and both wells
re-seated" (identical). Those were pre-merge numbers that survived the merge; the lesson is that a
notes entry must be re-measured on the shipped artifact after any merge, because it is the record the
next session diffs against.

**The byre defect this map was the motivating case for is fixed** - by a peer's rule, taken over mine
in `eacc48e4`: minimax spread plus a borrow-reach tie-break, so a shared shed has neighbors close
enough to borrow from. Median nearest-byre **101 ft, max 165**, against 373/771 before.

**The windbreak's off-canvas clumps are gone (23 -> 0) - but the first fix for it was wrong** and
this map is where the cost showed: it deleted 40 clumps to remove 3 invisible ones and punched a
~100 ft hole through the wind wall. See the shared entry below.

**Still open here**, both raised by review and neither reachable by the area floor: the dart-shaped
ring at (1021-1084, 968-1012), 0.69 of a cell, which wants a tip-angle companion rule rather than the
declined four-sides rule; and the three woodland commons sitting on an exact (+270, -270) lattice,
which read as three stamps of one wood. Both are in `future-work.md`.
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

## Feature 123 - the lane web (back_lane)

**5 of this map's 12 farmhouses stood more than 100 ft from any way. Now none do** - the worst is
80 ft and the median 61 - **and every lane on the sheet belongs to one connected
network**, which is the part that took two review rounds to get right.

The research is decisive that a house in a nucleated cluster is reached: "every house in the
nucleated village is accessible via the interconnected system of narrow lanes and alleys". The FORM
is a seeded knob, because the record supports two and two supportable answers become variance rather
than a choice (Principle XII). This map rolled **`back_lane`**, which runs PARALLEL to the field margin behind the ranks of plots, tied to the rest by cross-links - the planned form the sources call a "rectangular framework", the one that says the place was LAID OUT. It carries **4 web
lanes** of 8.

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

## Feature 124 - a farmhouse fronts one lane end, not three

A `settlement-review` read this map's east node at 3x zoom as **a broom**: ways leaving one point
within about 23 degrees of each other, two of them ending blunt, and **all of them claiming the same
farmhouse** - at 66.9, 55.1 and 40.0 ft. Three ends, one house answering for all three.

Two rules should have caught it. `lanes_reach_something` lets an end discharge its obligation by
stopping at a farmhouse and never said a house could only do that once. The lane web's shadow rule
tests a new web run against what is already drawn - but both offending arms are SKELETON lanes, laid
before the houses exist, so they are never tested against each other.

The fix is one clause in `trim_lane_stubs`, which was already the right place: it runs after
placement, only ever SHORTENS (so it cannot invalidate a seated house), and rewrites ink in the
stream slots a lane already owns. Its house test is now **exclusive** - the end nearest a farmhouse
keeps it, and any end standing alongside it and pointing the same way must find its own reason to
exist or be trimmed until it does. Below one homestead's frontage the existing floor drops it, which
is what the reviewer proposed.

**A house reached from OPPOSITE quarters is a corner, and stays legal.** Without that clause the rule
flags most of a nucleated cluster's middle. And "blunt" means what `_FRAY_DEG` already means: the
ends in question stood 21.6 and 24.3 ft from another way and near-parallel to it, so they had not MET
it - proximity is not arrival, which this engine had already learned once.

This map now has no fan, and every farmhouse is still reached: worst 80 ft, median 61.
