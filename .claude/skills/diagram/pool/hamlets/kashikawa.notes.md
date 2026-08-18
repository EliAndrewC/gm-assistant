# Design notes: Kashikawa (樫川, "oak river") - scripted hamlet, the top of the band

*One of four demo maps from the scripted-generation experiment (2026-08-11). See
[`../../hamletgen/`](../../hamletgen/) for the pipeline and
[`inashiro.notes.md`](inashiro.notes.md) for the head-to-head with the authored Ikegami.*

**Kanji triangle**: 樫 *kashi* "evergreen oak" + 川 *kawa* "river". Kashikawa, "oak river" - named
for the oaks on the high ground the settlement backs onto, which the map draws as its managed
coppice patches and its fengshui belt.

**Subject**: ~20 households - the ceiling of the hamlet band, above which a place needs a headman, a
shrine and tax-free plots and is a village instead - on land falling to the northeast, draining off
the frame.

**What it is here to show**: the size end of the range. As first rolled (2026-08-11) it was also
the one place the pipeline was allowed to miss - 18 farmhouses seated against 20 declared, inside
the gate's 0.85-1.05 band but at the bottom of it - and the notes presented that shortfall as the
honest report it was. The 2026-08-15 re-carve (supply-bank bund hem + the padded well sweep)
re-rolled the whole map and the cluster now seats **all 20**, so the allowed-miss demonstration is
history rather than the map's current state; the reporting machinery is unchanged and a future
re-roll that misses will say so again.

**Known open**: Inashiro's two - the bare comb floor on the fan's shoulders (inherited from
`build_comb`), and a windward quarter derived from the slope. The woodland commons are
DERIVED, not authored - their count and sizes move with the roll (this file went stale on the
concrete number three rounds running, so it records the mechanism now): the shrink ladder
(250 -> 200 -> 160 -> 125 ft) and, when the generous crop set-backs would leave the oak map
woodless, a last-resort set-back profile (40/100 px against the gate's 14/69 floors) give the
dry, open, in-frame ground exactly the stands it can carry. The stands favor the unplowable
margins; whatever fraction of the name's high-ground oaks the window cannot hold stays implied
beyond the frame.

- 2026-08-15 (supply-bank hem re-roll): bunds hem onto the supply channels' banks
  (`build_comb(supply_banks=True)`, gate `paddy_bunds_clear_the_supply_channels`); the whole map
  re-rolled downstream. `settlement-review` (DELTA) passed the bund/channel read and the three
  re-seated wells, and caught this file's stale shortfall claim plus a gen docstring that was a
  copy of Inashiro's - both fixed the same day.

- 2026-08-16 (the fork draws both arms - engine change, this map re-rolled): the GM's Inashiro
  question settled in research/water.md "The head-race forks - supply commands both flanks";
  every `OFFTAKE_LADDER` row now draws canal B, gated by `comb_supply_commands_both_flanks`.
  This map re-rolled three times as review fallout was fixed at the engine (canal-B thread
  tails via interpolated piece boundaries, minimax worst-served well placement, the notice
  board's grove-clump keep-out, accidental-lane-crossing guards). Review log: round-2 DELTA
  flagged the blunt canal-B cap (fixed: the arm now tapers 7.2 -> 3.2 past its offtake); round-3 follow-up in the session of 2026-08-16.
- 2026-08-16 (round-3 review QUESTIONABLE, settled): the SW five-house pocket has no well of its
  own DELIBERATELY - its houses stand 77-182 ft from the drawn stream head and intake channel
  (measured from the manifest), and `settlement_dwellings_watered` counts surface water within
  ~760 ft as watering, so a well there would be redundant infrastructure beside a living stream.
  The minimax well objective still counts those houses (a known, harmless inefficiency - logged
  in future-work.md); their real water is the stream, the period-correct arrangement.


- 2026-08-16 (known-opens round - floor trim, woodland re-seat, seeding trace; this map
  re-rolled): the ledger's four fork-re-roll defects were closed in one session. The comb floor is
  now TRIMMED to the collector's command area (`floor_overhang`, gate
  `comb_floor_ends_at_the_collector`); woodland commons seat inside the predicted kept window AND
  off the marsh (`open_ground_patches` frame + marsh keep-outs, shrink ladder 250 -> 200 -> 160 ->
  125 ft; gates `woodland_commons_within_the_frame` / `woodland_commons_on_dry_ground`); and
  `meta.cluster_seeding` records the seeding mode always ("frontage" on this roll).
  Map-specific: the envelope trim was provably surgical (NE extent 2726 -> 2484, all 750 plots and
  the wet plots byte-identical, one footbridge on the removed ground gone with it); the phantom
  bog parcel (250 ft recorded, 2 crowns drawn vs its sibling's 53) is gone and the roll then
  seated one dry 160 ft oak stand (the derivation has moved since - see the later entries). Review log: full DELTA caught the phantom parcel and this
  file's stale off-frame paragraph (both fixed same day); follow-up pass on the re-seat.

- 2026-08-16 (second known-opens round - flooded-sliver demotion, well/check alignment,
  recorded woodland canopy, trim dedup; this map re-rolled): pointed plots (interior angle
  < 25 deg) no longer take the FLOODED tint and the painted tint is recorded as
  `flooded_plots` (gate `flooded_plots_read_as_basins` at 15 deg); the well minimax and
  rescue read `settlement.surface_water_dist` - the watered check's own predicate - so wells
  stop chasing stream-watered houses; woodland stands record their crowns (`tree_crowns` +
  per-parcel count, gate `woodland_commons_visibly_stocked`) and register as placer
  keep-outs; the trim corner's duplicate vertices are merged (`dedup_ring`).
  Map-specific: the wells realigned (the SW stream-watered pocket now shapes the objective the
  settled ruling described: three wells in the NE cluster at 69-298 ft, none by the stream
  frontage) and the tighter window went WOODLESS at every shrink rung - the motivating case for
  the last-resort set-back profile. The stands re-derived twice more inside the round as the
  profile calibrated (a mid-round 35-crown 160 ft footslope stand was review-verified for
  recorded-vs-drawn crown agreement, 35=35 / 15=15); the shipped roll seats TWO 125 ft stands
  (15 and 17 crowns), dry and on-frame - the exact stands are roll-derived, the invariants
  (dry, on-frame, recorded canopy, check-legal set-backs) are what hold.

## 2026-08-17 - re-packed by feature 121 (the placer tests the rake it draws)

19 of 20 houses re-seated (median 362 ft, max 866 - a full re-seed, not a nudge); the SW outlier at
(1352.4, 3062.7) is byte-identical. Household, garden, yard, well and shed counts all unchanged.

WHY: the bundle placer used to clear an axis-aligned rect for a house the map draws raked by up to
+/-5 deg, and `houses_clear_of_lanes` measured an axis-aligned rect too. Both read the drawn raked
corners now, so `LANE_CLEARANCE` stopped being what holds a house off a lane and dropped 48 -> 40 px
(derived: longest drawn minka's half-diagonal 34.7 + the lane's half-tread 5).

MEASURED HERE (settlement-review, DELTA): house-corner-to-tread min 13.0 -> 5.2 ft, median 35.0 ->
29.1, and **0 on the tread** before and after. Cluster density 1.42 -> 1.45 houses/acre - it
compacted rather than re-composed. Bundle spacing IMPROVED: sub-5-ft bundle pairs 10 -> 7, min gap
2.0 -> 2.4 ft. The windbreak re-derived and stayed a belt (aspect 0.10) with no house corner under a
crown. Nothing else drifted onto a lane - the closest accessory is a threshing yard at 18.4 ft.

Review verdict: PASS, no errors.

OPEN, ruled nowhere (raised by that review, NOT caused by this change - the house is
byte-identical): the SW farmstead at (1352.4, 3062.7) stands 469 ft from its nearest neighbor and
385 ft from any lane, with no way reaching it, on a map declaring `nucleated: true`. The re-pack
moved the other 19 houses a median of 362 ft and left it, so the placer had every chance to fold it
in. Needs a one-line ruling: outlying holding by intent, or a seeding gap.

## 2026-08-17 (later) - the outlying farmstead: SUPERSEDED, see the note at the end

The settlement-review of the feature-121 re-pack asked for a ruling on the farmstead at
(1352, 3063): 469 ft from its nearest neighbor, 385 ft from any drawn way, with no track reaching
it, on a map declaring `nucleated: true`. Two separate complaints were tangled together, and they
have different answers.

**The isolation is GONE, and not by touching this house.** The front-row density fix (front_row now
samples by one-bundle-pitch spacing along the field edge instead of by household count) pulled the
rest of the cluster toward the paddy, and this farmstead's nearest neighbor is now **170 ft**
against 111 / 110 / 105 for the next three - an ordinary outer-edge spacing, not a hamlet of one.
The house itself did not move; the settlement grew toward it.

**The way-access is ACCEPTED, deliberately.** It still stands 385 ft from any lane against 41-70 ft
for its neighbors, and that is correct rather than an oversight: a lane must NOT run through the
flooded paddy (`settlements/ways.md`), and people cross into the fields on foot **along the bunds**.
An edge farmstead standing at the paddy margin is reached the same way every field worker reaches
the same ground. Drawing a lane out to it would put a no-build corridor across the crop to serve one
household - the opposite of the rule.

**What was declined**: (a) folding the house into the nucleus - it sits 50 ft from the drawn stream
with its own byre, which is a coherent holding, and the placer had every chance to move it and did
not; (b) drawing a spur lane to it - see above, it would cross the paddy; (c) a check requiring every
farmhouse within N ft of a way - it would fire on exactly this legitimate case and on nothing else.

~~Ruled 2026-08-17. Not to be reopened as a bug.~~

**SUPERSEDED THE SAME DAY - do not quote the ruling above.** The front-row cap re-packed this map
again and **there is no house at (1352, 3063) any more**. The westernmost farmhouse is now at
(1634, 3141), 68 ft from the spine. Measured across the shipped manifest: no farmhouse on this map
is more than **103 ft** from a way by center, or **71.7 ft** by corner-to-tread. The section above
says "The house itself did not move; the settlement grew toward it" and "It still stands 385 ft from
any lane" - both are false of the map that ships.

The paddy argument it rests on is still SOUND as reasoning (a lane may not cross the flooded paddy,
and field workers reach that ground along the bunds); it simply has nothing left to cover here. It
is kept for provenance rather than deleted, because the failure mode being guarded against is a
future session quoting "not to be reopened as a bug" at a genuinely stranded farmstead on some later
roll. If one appears, rule it fresh.

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

RIPPLE ON THIS MAP: the notice board's caption was 90 degrees out and is fixed - `kosatsuba` used
`label_tilt`, which FOLDS mod 90 because a building has two edge families, where a board has ONE
meaningful axis (its face). It now uses `linear_tilt` and reads level beside a 49.3-degree board,
matching neither lane, so nothing on the sheet can steal it. Byres went from occupying 14% of the
settlement's length to spanning it. Every farmhouse is now within ~97 ft of a way by centre.
Review: PASS.

OPEN, wanting a one-line ruling rather than a fix: the maximin spread put a byre 38 ft from a
communal wellhead (the other three are 168-317 ft from any well). Nothing governs it - `homesteads.md`
puts byres and wells in the same interstitial courtyard ground, so the adjacency is structural. The
reading I would take is "the beasts are watered at the well, that is where a byre goes". Recording
the decision matters more than which way it goes, because the next re-pack will produce it again.
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

**On this map, measured on the SHIPPED manifest against main's tip.** 827 -> 814 basins; smallest
surviving basin 0.254 of the design cell; acreage, 20 of 20 households and the field outline all
hold.

**The cluster barely moved: 19 of 20 houses unmoved, min-max displacement 8 px** - worth recording
precisely because Inashiro's re-packed wholesale at 304 px on the same rule. Gardens, yards, sheds,
byres, wells and the kosatsuba are unchanged; the windbreak went 212 -> 190 clumps and `meta.view`
shifted. The ripple is real and its SIZE is map-specific; do not generalize from one map in either
direction.

This map needed no `settlement-review` pass this round: its cluster is effectively unchanged and the
fabric rule was reviewed on Inashiro, Mizuguchi and Sawada.
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
