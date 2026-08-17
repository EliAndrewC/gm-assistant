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

**On this map.** 519 -> 511 basins (-8, 1.54%); smallest surviving basin 405 sq ft, 0.273 of the
cell. Acreage conserved to 6 sq ft in 715,849; 12 of 12 households; field outline unchanged.

**What the review measured, which is the answer to the GM's real worry.** The fear with any size
floor is that it tidies the mosaic into the consolidation grid. It did not: near-rectangular rings
229 -> **229** (44% -> 45%), 4-sided share 74% -> 75%, area CV 0.38 -> **0.37**, median 1,365 ->
1,370 sq ft, max unchanged. The only number that moved is the bottom of the distribution: min area
237 -> **405 sq ft**. The floor amputated the tail and touched nothing else. Literal 3-sided rings
**2 -> 0**; snipped-corner quads 8 -> 6; prong vertices 41 -> 38.

**And what it caught, which became a second guard.** Absorption ranks candidate hosts by shared bund
length, which is blind to the shape the union comes out as - so a 306 sq ft fragment went to the
lumpiest basin on the sheet and made it worse: 26 vertices, eight reflex corners, four out-and-back
prongs 5-11 ft wide that each draw as a bund with a FREE END sticking into the paddy. The GM's
"rendering artifact" complaint, transplanted from area to outline. Both guards already in the ladder
measure an APEX and neither can see a blunt lobe, so the fix measures **solidity** (area / convex
hull): `_WELD_MIN_SOLIDITY` = 0.85, chosen off a wide gap in the measured population (eighteen of
twenty welds scored >= 0.90, the two the reviewer picked out by eye scored 0.731 and 0.78). It is a
preference and not a veto - the next-best host is tried and the least-lumpy candidate taken only if
none is clean - because refusing outright trades a lump for a doubled bund, which the apex guard
already learned is worse. After the guard the fragment goes to a 0.919-solidity neighbor and the
lumpy basin is left at its pre-existing shape.

**Logged, not fixed.** The dart-shaped ring at (1021-1084, 968-1012) is 1,034 sq ft - 0.69 of a
cell, nearly three times the floor - and reads as an arrowhead; it is byte-identical before and
after, so it is pre-existing and out of this change's scope. The reviewer's broader point stands and
is worth a GM ruling some day: the floor is an AREA rule and some remaining offcuts are a SHAPE
problem (a 436 sq ft parallelogram at (1486, 1138) meeting a wedge at a 27.4 deg needle; a quad at
(1594, 836) whose fourth side is 3.1 ft). A minimum-side or tip-angle companion is the shape of that
rule - not the declined four-sides rule, which is a different thing.

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
