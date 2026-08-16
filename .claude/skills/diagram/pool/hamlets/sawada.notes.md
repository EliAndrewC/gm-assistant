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

Fixed by lifting the demotion clear of the placer floor: `_TINT_MIN_APEX = 40.0`, which sits inside
the gap `pointed_ring`'s own pool measurement reports (seam wedges 7-23 deg, honest flooded hem
strips 45+), so it demotes toe wedges that read as ponds and leaves genuine wet strips blue. The
gate stays at 15, preserving the placer-stricter-than-gate invariant the whole calibration rests on.
The four constants now read as one ladder - gate 15 < weld 18 < toe 25 < tint 40 - and
`_GATE_MIN_APEX` exists so they are all expressed against one number instead of each carrying a copy.

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
