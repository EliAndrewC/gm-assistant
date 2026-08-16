# Design notes: Mizuguchi (水口, "water mouth") - scripted hamlet, water entering from the west

*One of four demo maps from the scripted-generation experiment (2026-08-11). See
[`../../hamletgen.py`](../../hamletgen.py) for the pipeline and
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
  own ledger item) is gone, and the freed common now carries two byres and their fodder plots;
  three dry woodland parcels (250/250/160 ft). Review log: full DELTA verified the trimmed corner
  reads as worked field (bund-edged hem staircase, not a cut) and caught the marsh-seated parcel
  that drove the marsh keep-out; follow-up pass on the re-seat. Cosmetic residue logged, not
  fixed: the collector's blue stroke fades out along the hem staircase at the trimmed corner
  (topology green, ink only).
