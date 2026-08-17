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

## 2026-08-17 - re-packed by feature 121 (the placer tests the rake it draws)

6 of 12 houses moved. All 12 households had a dooryard garden before AND after; what changed is that
the number with a SECOND bed went 2 -> 4 (`gardens` counts BEDS, not households - a distinction
worth keeping straight, since garden AREA per household went DOWN for both gainers, 1006 -> 724 sq
ft at h0). The tighter corridor bought bed COUNT, not ground.

WHY the corridor changed: see kashikawa.notes.md's entry of the same date, or
specs/121-placer-drawn-footprint/research.md D1/D6/D7.

MEASURED HERE (settlement-review, DELTA): all six moved houses moved TOWARD their lane. Lane-2
frontage clearance went 13.6/16.8/17.1/21.6/14.5 ft to 11.8/8.9/8.1/15.2/9.8 - close fronting that
still leaves a verge, nothing crowding or overhanging.

Review verdict: SHIP WITH NOTES.

OPEN, and it is the same defect class one level down - TWO FARMHOUSES CAN MERGE. The pair at
(829.4, 1682.7) and (771.5, 1693.6) had their raked-corner gap fall 3.6 -> 2.0 ft, because the
re-pack flipped h5's rake from -4.0 to +4.4 deg so the two houses now diverge instead of running
parallel. At 1 px = 1 ft that is two pixels between two dark roof strokes: at fit zoom they merge
and read as ONE long building, and two feet between thatched eaves is not a thing a hamlet does.

MECHANISM: feature 121 made the placer test its raked quad against the LANE TREAD, but house-to-
house separation is still adjudicated on the whole-bundle BBOX (`_bundle_side_fits`), which knows
nothing about either house's rake. Measured across the four scripted hamlets, this is a lone
outlier - inashiro/kashikawa/sawada sit at 28.8/25.5/23.0 ft minimum and only mizuguchi has a pair
under 6 ft - so a rule with a lot of headroom would catch it and disturb nothing else.

SKETCH (check before fix, per the project rule): add a gap verdict using the existing
`within_edge_gap(a, b, N)` helper over `M["houses"]` pairs - it already measures real footprints -
confirm it fires on mizuguchi and on nothing else in the pool, then require the same clearance in
`_bundle_common_fits` against every placed house's raked quad (the sun-corridor rule already reads
neighbours' geometry off `M["houses"]`, so the precedent and the plumbing both exist). Ground the
number in "two thatched roofs must shed separately" - the principle research/buildings.md already
records for a building against a compound wall.

DEFERRED DELIBERATELY: this is a NEW rule, not a regression (no check fires, and the gate is 22/24
before and after), so it was not folded into feature 121's scope.
