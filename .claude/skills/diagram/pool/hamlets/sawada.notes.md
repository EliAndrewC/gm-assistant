# Design notes: Sawada (沢田, "marsh paddy") - scripted hamlet, the OFF-MAP drain

*One of four demo maps from the scripted-generation experiment (2026-08-11). See
[`../../hamletgen.py`](../../hamletgen.py) for the pipeline and
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
