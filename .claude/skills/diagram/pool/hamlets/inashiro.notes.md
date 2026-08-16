# Design notes: Inashiro (稲代, "rice-field") - the SCRIPTED hamlet

*The head-to-head map of the scripted-generation experiment (2026-08-11).*

**Subject**: a small outlying rice-farming community of ~15 households / ~75 inhabitants, belonging
to a village district whose headman lives in the main village. Like every hamlet it has no headman
of its own, no shrine, no tax-free plots and no burial ground.

**Kanji triangle**: 稲 *ina* "rice plant" + 代 *shiro* "paddy" (as in 苗代 *nawashiro*, a seedbed).
稲代 Inashiro, "the rice-field" - the plainest possible name for the plainest possible hamlet, which
is the point: this map exists to be ordinary.

## Why it exists

It is the deliverable of the experiment in [`../../hamletgen/`](../../hamletgen/): can a SCRIPT
do what a session currently does by hand? Inashiro was given deliberately the same brief as the
hand-authored [`../hamlets/ikegami.gen.py`](../hamlets/ikegami.gen.py) - ~15 households, land
falling due south, a brook off the northern high ground feeding one comb field, the field draining
at its low foot into a *tameike* - so the two maps can be read side by side.

The comparison is the evidence:

| | Ikegami (authored) | Inashiro (scripted) |
|---|---|---|
| generator | 239 lines, ~40 literal coordinates | 9 lines, no coordinates |
| paddy acreage | 15.3 acres against a stated target of ~20 | 18.4 acres against a computed 19.5 |
| households seated | 15 of 15 | 15 of 15 |
| gate | green | green |

## What the script decided, and from what

Every position on this sheet is derived from geometry already on the map. The order is the
pipeline's, and it is the same order a person follows:

1. **The fall and the drainage bearing** are declared (due south). Everything downstream reads them.
2. **The intake** sits at the head of the ground the field will occupy - gravity, not a knob. Its
   lateral position on that head margin is rolled.
3. **The field** is SOLVED rather than sized by eye: the comb is rebuilt at a bisected size
   multiplier until the drawn plot area lands within a few percent of ~1.3 gross acres per
   household. (Ikegami's own docstring asks for ~20 acres and its closing line reports 15.3; nothing
   catches that, because no check reads acreage and `field_fall` is a pixel length tuned by eye.)
4. **The tameike** walks downslope from the drain's own outfall until its rim is genuinely clear of
   the field envelope, and stops at the first position that is.
5. **The cluster** is seated on the field margin whose outward normal best faces the cold wind -
   背山面水, back to the hill and face to the water - excluding any margin below the drain (the wet
   toe is not building ground) and any whose back is already under the dry hem.
6. **The lanes** come before the houses, because a lane is a no-build corridor the homesteads front:
   a rolled skeleton in the cluster's own frame, a spur to the nearest reachable point of the field,
   and the connector track out to the frame, its bearing swung away from the crop until it clears.
7. **The homesteads** fill to the declared household count, widening the band and drawing more
   candidates when the placer refuses, rather than re-rolling the map.
8. **Wells and byres** drop into the courtyards the finished layout left.
9. **The hinterland**, then the **woodland patches** (found by scanning for ground still open), then
   the **windbreak belt**, shaped to the houses that actually landed.

## Known open

- The **bare comb floor** on the fan's shoulders - paddy-green ground inside the field envelope
  where the carve did not tessellate into plots - is inherited from the shared `build_comb` engine,
  not from the scripted pipeline; Ikegami shows the same thing at the foot of its fan.
- The wind is derived from the slope (cold air drains downhill off the high ground), which makes the
  windbreak's side a consequence of the terrain rather than an independent regional fact. A GM who
  knows the real prevailing wind for the province should pin it on the spec.
- **On THIS map the wind is a restatement of the seat, not of the slope.** The fall is 90 deg, from
  which `windward_for` can only return N, NW or NE - and the manifest declares **W**, because the
  cluster came to rest on a flank margin and `stage_ways` re-reads the windward quarter off the
  site's own back when the two disagree by more than ~70 deg (a house whose back is to the wrong
  quarter has its shelter belt planted in the rice). That override is right, and it does mean the
  belt's side here is circular: the belt stands west because the cluster's back is west, and the
  wind was then named to match. On a cluster seated on the field's UPSLOPE margin the two rules
  agree and the declared wind carries real information; on a flank seat it does not.
- **Dry hem plots run ~3.5x the size of Ikegami's** and chain single-file rather than packing two or
  three deep, so the hem reads as large fields rather than household strips (`settlement-review`,
  2026-08-11). Parcel size, not acreage - the total is comparable. It wants a researched constant of
  its own.
- The **lane stand-off** is wider than an authored map's, because `LANE_CLEARANCE` is set to work
  around the engine's "placement tests a different footprint than the one drawn" debt.

- 2026-08-15 (bead recolor + water-honesty review): known residue - the pocket pond at (2144, 1724)
  has the margin-drain stroke and some hinterland tufts painting over its fill. Logged in
  future-work.md ("Pocket ponds carry ink-on-water of their own"); not part of the bead delta.

- 2026-08-16 (the fork draws both arms): the GM noticed the head-race turns southeast along the
  northeast margin but never SPLITS toward the west side the way other maps' channels do, and asked
  for research. Settled in research/water.md "The head-race forks - supply commands both flanks":
  a gravity canal commands only ground below it, Minuma-dai (1728) deliberately divides its head
  into two margin canals, and `build_comb` was already carving canal B as a supply thread the
  hamlet tier never inked - measured here, ~255 ft of planted paddy west of the fork against 0 ft
  of drawn water. Every `OFFTAKE_LADDER` row now draws canal B (one offtake at ~0.55; the arm runs
  partway down the west margin and tapers), gated by `comb_supply_commands_both_flanks` (the
  pre-fix manifest is frozen in `pool/regressions/`). The map re-rolled downstream of the carve;
  `place_wells`' greedy coverage also gained a ~66 px bucket with center tie-break after the
  Sawada re-roll parked a well past the frame (`crop_not_held_open_by_one_feature`).

- 2026-08-15 (supply-bank hem): the GM caught the bunds bordering the irrigated channels drawn
  down the MIDDLE of the water rather than along its edge - `_carve`'s `bnd` returned thread/canal
  centerlines and the supply strokes are drawn centered on those same lines, so the pre-fix sheet
  carried 266 sampled bund points inside a supply stroke (the worst ON the centerline of a ~12 px
  channel). `build_comb(supply_banks=True)` now holds every carved corner off every supply stroke
  by its local half-width + `BANK_MARGIN`*grain, perpendicular - so the bordering bunds run
  parallel to and along the banks - and quads wedged between a parent channel and its child ditch
  near a takeoff (ground narrower than the two banks; no legal corner exists) are dropped for the
  base floor to show, the same idiom as the toe slivers. Second pass the same day (via Sawada's
  review): both the carve's drop test and the gate walk every bund EDGE at a 3 px step, not just
  the vertices - an acute junction wedge can keep every corner dry while its edges cross the
  water. Gate: `paddy_bunds_clear_the_supply_channels` (scripted maps only, per the migration
  doctrine; pre-fix manifests are frozen in `pool/regressions/`). The whole map re-rolled
  downstream of the carve. `settlement-review` (DELTA) passed the delta and caught `_fill_wedges`
  nesting 12 fillers wholly inside carved paddies (pre-existing, verified against the frozen
  manifest) - fixed the same day: a filler must now cover at least one probe of genuinely bare
  ground.

## 2026-08-16 - scatter water-skip fix (engine-wide, found here)

GM spotted scrub between the dry hem plots and the supply channels; the investigation found 27
tufts standing ON the head-race's drawn water. Root cause: `_on_watercourse` read only the
hairline topology `channels` record (w 2.5) while the drawn laterals live in `drawn_channels` up
to 14 ft wide (the "same manifest source" trap). Fixed in `settlement._watercourse_segs` +
`_on_watercourse` (drawn piece-tapered widths, pre-boxed grid at the scatter sites); ink-only,
manifest byte-identical. The remaining sparse tufts on the bare strips beside the channels are
DELIBERATE - no bank-margin rule exists; that open decision is recorded in
`research/vegetation.md` "Scrub stays off open water". settlement-review DELTA: PASS
(banks read as honestly vegetated, no sterile halo; marsh tufts correctly untouched).
(Superseded the same day: the open decision was resolved - see the cut-bank entry below.)

## 2026-08-16 - cut-bank margin (engine-wide, decided here)

The GM saw the remaining tufts on the berm strips between the dry hem plots and the supply
channels and resolved the open decision left by the scatter water-skip fix above: an irrigation
channel's bank is maintained ground (walked for sluice work, scythed for fodder), so the commons
scatter now stands its bases `_BANK_MARGIN_FT` (6 ft - one scythe swath, the crop margin's own
figure) off every drawn channel edge (`channels` + `drawn_channels` at drawn piece-tapered
widths). Streams and the reed marsh are deliberately unchanged - natural banks keep their
vegetation to the water's edge. Ink-only; the manifest is byte-identical. Automated check:
`test_commons_keeps_scrub_a_cut_bank_off_the_channels_but_not_the_streams` (written red-first
against the pre-fix scatter; also pins the no-margin-on-streams half). Why in
`research/vegetation.md` "The cut bank". settlement-review DELTA: PASS (parsed all 231k scrub
bases against the exact keep-out geometry - zero inside; density flat beyond the margin, so no
sterile halo; brook/marsh/pond fringes confirmed untouched). One intent put on record at the
reviewer's ask: the field-toe COLLECTOR drain takes the margin too, deliberately - its bank is
walked for the outfall sluice, the same maintained-ground economics as the supply banks; only
the natural brook and the reeds keep a wild edge.

## 2026-08-16 - dry-hem seams are shared lines (engine-wide, found here)

GM: "The dry crop fields... do not seem to perfectly align with one another. A few of them seem to
overlap slightly, and a few of them seem to have little bits of space between them because the
borders of those crop fields are not exactly at the same angle." Root cause in
`waterfields._dry_fields`: each hem column offset its quad along its OWN chord's normal, so both
quads at a shared boundary point pushed that point in slightly different directions wherever the
supply canal bent - a bare wedge on a convex bend, a lap on a concave one, ~bend-angle x depth px
wide at the ragged edge. Measured here pre-fix: 7 plot pairs overlapped outright, worst 245 sq ft.
All four scripted hamlets (Inashiro, Kashikawa, Mizuguchi, Sawada) had the defect.

Fix: `waterfields._miter_normals` - ONE mitred upslope normal per boundary point (1/cos(half-bend)
scaled like a stroked polyline's miter join, capped 2x, with a 180-degree-fold fallback), so every
seam is a single straight line both quads lie on; the ragged outer edge now steps ALONG the shared
seam lines instead of opening wedges. Gate: `dry_plot_seams_shared` (segment 0596; two clauses -
shrunk-`sat_overlap` for laps, collinearity-from-a-shared-corner for gap wedges), written RED
against this map first; the pre-fix manifest is frozen as
`pool/regressions/dry_plot_seams_shared_fires_on_the_pre_fix_inashiro.json`. RNG stream untouched
(same draw sequence), so the ripple was `dry_plots` only here; Kashikawa/Sawada also re-derived
`commons`, and Mizuguchi's cluster re-seated (hem corners feed `seat_cluster` scoring).
`settlement-review` (DELTA, one agent per map): all four PASS - seams collinear to ~0.1 px,
raggedness preserved, Mizuguchi's re-seated cluster coherent (wells, lanes, kosatsuba re-checked).

- 2026-08-16 (known-opens round - floor trim, woodland re-seat, seeding trace; this map
  re-rolled): the ledger's four fork-re-roll defects were closed in one session. The comb floor is
  now TRIMMED to the collector's command area (`floor_overhang`, gate
  `comb_floor_ends_at_the_collector`); woodland commons seat inside the predicted kept window AND
  off the marsh (`open_ground_patches` frame + marsh keep-outs, shrink ladder 250 -> 200 -> 160 ->
  125 ft; gates `woodland_commons_within_the_frame` / `woodland_commons_on_dry_ground`); and
  `meta.cluster_seeding` records the seeding mode always ("frontage" on this roll).
  Map-specific: the west-edge floor strip (12 vertices, worst ~357 px past the flat-extended drain
  line - the same class as Mizuguchi's needle, unnoticed until the check swept) is trimmed to the
  pixel; three dry woodland parcels (250/250/160 ft) on the merged roll (a 125 ft fourth existed on the pre-merge roll and did not survive the concurrent-session merge re-roll - the dry window holds three); the pocket pond re-seated to (2092, 1671)
  with no ink-on-water residue (the 2026-08-15 logged item cleared with the re-roll). Review log:
  full DELTA caught the two marsh-seated parcels (one 100% wet with zero crowns) that drove the
  marsh keep-out; follow-up pass on the re-seat. Reviewer note logged in future-work.md: stand
  crowns are ink-only, so no manifest check can count a coppice canopy.

- 2026-08-16 (fan-toe pond fix - GM report; this map re-rolled): the GM flagged the circular pond
  mid-paddy on the southern edge as straightforwardly a mistake. `_plot_pond` sized its ellipse
  from the host plot's BOUNDING BOX, and the low plot it drew was a fan-toe WEDGE whose bbox is
  several times the wedge itself, so the pond (33.7 x 24.7) spilled across three neighboring wedge
  plots and two drain-hem plots with spoke bunds drawn through open water -
  `field_ponds_on_low_ground` green throughout (it reads the host plot's wet flag, not the
  ellipse's extent). Fix: `_plot_pond` centers on the plot CENTROID and shrinks to fit the plot
  POLYGON (refusing below the 10 x 7 px legibility floor), `_paddy_features` tries the low plots
  in random order until one accepts, and the new gate check `field_ponds_sunk_into_one_plot`
  (segment 0577.5) holds it - written RED against this map first, pre-fix manifest frozen as
  pool/regressions/field_ponds_sunk_into_one_plot_fires_on_the_fan_toe_inashiro.json. Placement
  and check read the same `seg_in_ellipse_core` predicate, so siting and verdict cannot disagree.
  This map: pond re-seated in the SAME toe plot at 16.1 x 11.8; manifest delta = field_ponds +
  bund_beans only. Review log: DELTA pass, nothing new caught; sub-pixel rim/bund tangency
  (0.44 px) logged as a nitpick - if `_plot_pond` ever gains a margin knob, ~2 px buys visible
  daylight.
