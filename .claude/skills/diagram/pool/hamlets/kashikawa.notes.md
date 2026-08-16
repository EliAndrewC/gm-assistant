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
`build_comb`), and a windward quarter derived from the slope. The woodland commons went
3 parcels (250 ft, off-frame) -> ONE on-frame 160 ft parcel in the 2026-08-16 fix round - the
shrink ladder doing its job, not a shortfall: the dry, open, in-frame ground holds exactly that.
The surviving coppice stands on the dry footslope strip by the bog toe, downhill of the cluster -
the margin not worth tilling, which is where a commons woodlot really goes - while the name's
high-ground oaks stay implied beyond the SW frame.

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
  bog parcel (250 ft recorded, 2 crowns drawn vs its sibling's 53) is gone and the map honestly
  seats ONE dry 160 ft oak stand. Review log: full DELTA caught the phantom parcel and this
  file's stale off-frame paragraph (both fixed same day); follow-up pass on the re-seat.
