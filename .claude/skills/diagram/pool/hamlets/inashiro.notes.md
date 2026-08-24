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
- **Dry hem plots run ~4.5x the size of Ikegami's** (median 7,711 sq ft against 1,707; the coarsest of the four scripted hamlets - Kashikawa 6,221, Mizuguchi 6,092, Sawada 6,913. This bullet read "~3.5x" until a settlement-review re-measured it on the SHIPPED manifests, 2026-08-18: a standing known-open carries the current number or it is not a measurement) and chain single-file rather than packing two or
  three deep, so the hem reads as large fields rather than household strips (`settlement-review`,
  2026-08-11). Parcel size, not acreage - the total is comparable. It wants a researched constant of
  its own.
- The **lane stand-off** is wider than an authored map's, because `LANE_CLEARANCE` is set to work
  around the engine's "placement tests a different footprint than the one drawn" debt.

- 2026-08-15 (bead recolor + water-honesty review): known residue - the pocket pond at (2144, 1724)
  has the margin-drain stroke and some hinterland tufts painting over its fill. Logged in
  future-work/ ("Pocket ponds carry ink-on-water of their own"); not part of the bead delta.

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
  pixel; three dry woodland parcels (250/250/160 ft) on the merged roll (the count is roll-derived and has moved since - see the later entries); the pocket pond re-seated to (2092, 1671)
  with no ink-on-water residue (the 2026-08-15 logged item cleared with the re-roll). Review log:
  full DELTA caught the two marsh-seated parcels (one 100% wet with zero crowns) that drove the
  marsh keep-out; follow-up pass on the re-seat. Reviewer note logged in future-work/: stand
  crowns are ink-only, so no manifest check can count a coppice canopy.

- 2026-08-16 (second known-opens round - flooded-sliver demotion, well/check alignment,
  recorded woodland canopy, trim dedup; this map re-rolled): pointed plots (interior angle
  < 25 deg) no longer take the FLOODED tint and the painted tint is recorded as
  `flooded_plots` (gate `flooded_plots_read_as_basins` at 15 deg); the well minimax and
  rescue read `settlement.surface_water_dist` - the watered check's own predicate - so wells
  stop chasing stream-watered houses; woodland stands record their crowns (`tree_crowns` +
  per-parcel count, gate `woodland_commons_visibly_stocked`) and register as placer
  keep-outs; the trim corner's duplicate vertices are merged (`dedup_ring`).
  Map-specific: 6 basin-shaped flooded strips survive the demotion, all at the drainage toe;
  the wells re-seated to the taper-shadow south group (73-180 ft worst-walk) while the
  channel-fronting north row is correctly excluded; the woodland derivation settled at
  THREE stands (250/90, 250/88, 160/33 crowns) - a fourth 160 ft stand appeared mid-round on
  the dry shelf between collector and marsh (review-verified 27 ft clear of the reeds) and
  did not survive the final set-back calibration; the count is roll-derived, the invariants
  (dry, on-frame, recorded canopy) are what hold.

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

- 2026-08-17 (SHARED BUNDS - GM report; this map re-rolled, and every scripted hamlet with it):
  the GM found "tiny little standalone rectangles" of earthen bunds sitting in the middle of the
  paddy field, and named the rule they broke: "it should basically always be the case that two
  adjacent rice paddies share a single earthen wall rather than two different earthen walls."
  Their suspicion was that it clustered where the irrigation channels narrow and wind, which was
  the right correlation off the wrong cause - the channels are simply where the carve leaves
  awkward ground, and the awkward ground is what the wedge filler was seating rectangles in.

  Root cause: `_fill_wedges` sampled the fan's bare ground on a 12 px grid, boxed each cluster of
  SAMPLES, and shrank the box toward its own centroid until it lapped its neighbors only
  shallowly. Sizing from the samples rather than from the pocket's walls left a ribbon of bare
  floor on all four sides of every filler - the standalone rectangle - and the shallow-lap
  acceptance (every probe up to 12 real ft inside a neighbor, only one probe required on bare
  ground) let a filler ring land a plot-width INSIDE a basin, drawing a wall in the middle of
  someone's paddy. Attribution on the pre-fix map: all ten fully-isolated rings were fillers.

  Fix: `waterfields/seams.py::close_seams` replaces it and asks a different question. It computes
  the bare ground exactly - envelope minus everything planted, minus the drawn channels and their
  banks, minus ground outside the command area - then PLANTS every pocket wide enough to hold a
  basin (subdivided at the fan's own grain, so its outline IS the surrounding bunds) and ABSORBS
  every pocket too thin to plant into the basin it shares the most bund with. It runs LAST, after
  `_comb_toe_and_hem`, because that pass drops acute slivers and re-hems bunds onto the drain and
  so opens fresh bare ground of its own; the channel bends are swept BEFORE it, so it holds its
  basins off the water the map will actually paint. Research + rule: `research/fields.md` "Bunds
  are shared, and the fabric is continuous". Gate: `paddy_plot_seams_shared` (written RED against
  this map first; pre-fix manifests frozen as
  `pool/regressions/paddy_plot_seams_shared_fires_on_the_pre_fix_{inashiro,kashikawa,mizuguchi,sawada}.json`).

  This map: 597 -> 629 basins, planted share of the comb floor 91.3% -> 96.1% (+1.00 acre), doubled
  bunds 52 -> 0, and every remaining bare component over 50 sq ft sits inside a drawn channel's
  bank margin. Five shapely artifacts had to be beaten out along the way and each is commented at
  its site: hairline spikes where a difference grazes a boundary (the opening is intersected back
  with its input so it can only REMOVE ground), round joins exploding 4-vertex basins into 130
  near-duplicate vertices (mitre), flat segment caps leaving an uncovered wedge on the outside of
  every channel bend (a disc at each interior vertex), a merely-touching union returning a
  MultiPolygon (dilate the scrap 0.02 px), and Douglas-Peucker folding a thin weld through itself.

  Review log: DELTA pass. CAUGHT one new defect - basin #570 recorded as a self-intersecting ring:
  the union was valid and `_ring`'s 0.1 px rounding crossed it afterwards, so the weld now
  round-trips the ring it will actually record and declines in favor of the runner-up basin if it
  does not survive. Ink-invisible under a 1.5 px stroke, which is exactly why it needed catching in
  geometry rather than by eye. Two items put on record as PRE-EXISTING with measurements, both
  belonging to the carve's toe geometry rather than to this pass:
  * `plot_rings` are a paint-order STACK, not a partition - 39 pairs lap, double-counting 0.10
    acre of the recorded fabric. Invisible in ink (one `<polygon>` per plot carrying fill and
    stroke in index order, so the later basin paints out the covered bund) and this change HALVED
    it (8,583 -> 4,445 sq ft), but a future rule measuring basin-to-basin geometry from the
    manifest is measuring a fabric that intersects itself.
  * the two fan-toe SUNBURSTS (~1893,1650 and ~2430,1845): 8-10 bunds 130-254 ft long converging
    on a ~10 ft stretch of collector bank at 7.5-14 deg apexes. Pre-existing (7 such plots before,
    8 now) and the one place the fabric still reads machine-drawn. `_comb_toe_and_hem`'s own
    comment already names the cause - the carve opens a sector whose boundary has collapsed onto
    the drain - and calls the real fix a change to the carve's SECTOR geometry. Needs a GM ruling
    on whether a fan toe may converge like this before anyone re-cuts it.
  Also noted: the re-pack cost the northernmost homestead its farm shed (4 -> 3 of 15 households,
  against the project's ~30% storehouse figure) - inside the noise at this size, but it went the
  wrong way.

- **2026-08-17, the channel TAPER LAW** (GM asked whether a supply ditch should keep thinning rather
  than reach a minimum and stop, and whether the widths were researched at all). Two changes, both
  engine-wide, this map the motivating artifact. (1) Width goes as sqrt(discharge) and discharge runs
  linearly along one of these strokes, so the width SQUARED now interpolates - `waterfields.taper_w`,
  shared by the drawn stroke, both bank clearances the gate reads, the seam buffer, the carve's burial
  filter and the keep-out corridor. (2) The ladder is parameterized by ARC LENGTH rather than vertex
  index - `waterfields.taper_pieces`. The research, the sources and the disclosed departures are in
  [`../../research/water.md`](../../research/water.md); the finest DRAWN channel deliberately still
  STOPS at the ~1 m lateral tier, because below it lie the ~0.3 m field ditch (one pixel here) and,
  in a pre-modern system, plot-to-plot *tagoshi* cascade rather than any channel at all.

  Review log: DELTA pass, and it earned its keep - it CAUGHT that change (2) was missing entirely.
  With only the law in, the renderer was still slicing by vertex index, whose slices covered
  7.0-33.0% of a run apiece, so the ink missed the law by up to 1.94 px, the last third of two of the
  five delivery ditches was still drawn at a FLAT minimum (i.e. the GM's original complaint survived
  the fix meant to cure it), and the 2-point west-fork stub was inked end to end at its TAIL width,
  3.6 px against a declared 7.2. It also caught that `taper_w`'s docstring quoted the FORMULA's
  numbers as measurements of this map; they are now measured in the ink (7.7 / 7.1 / 6.1 / 4.8 / 3.7
  px at tenths 0.10 / 0.25 / 0.50 / 0.75 / 0.90 of a delivery ditch - the MEDIAN across the five,
  which tracks the law within ~0.1 px at the first four tenths but spans 3.46-4.13 against the law's
  3.81 at 0.90, where the tail segments are coarse. A second pass caught the first correction still
  quoting the FORMULA at the 0.25 tenth, 7.1 against an ink median of 7.0 - the same defect class
  twice, which is why `taper_w` now says in so many words to re-measure in the SVG.)
  And it caught that the committed `.png` was STALE while `tools/crop_map.py` crops the PNG - so the
  author's own visual checks had been of the pre-change image. Re-rendered.

  Confirmed clean by the same pass: no bund drawn inside the blue ALONG A RUN, and no bare stripe
  anywhere (the tightest along-run clearance is +0.20 px, against a `BANK_MARGIN` of 0.75 - about half
  the designed abutment eaten, none of it crossed). The along-run qualifier is load-bearing and the
  re-review supplied it: 12 ring points do sit inside a drawn stroke, every one where a ring crosses a
  ditch's terminal ROUND CAP (worst -1.16 px at (2252.2,1606.0)), and the same measurement on the
  pre-taper manifest gives 30 such points - so this change more than halved a pre-existing condition
  rather than introducing one. The collector reads as GATHERING under the mirrored law; and
  `tools.scatter_audit` came back 0 violations over 272,672 bases with a flat near-margin density
  profile (1157 / 1111 / 1120 at 0-15 / 15-30 / 30-45 px), so widening every watercourse produced no
  sterile halo.

  Two items on record as this change's RIPPLE, neither a defect: the re-pack consumed the 18-crown
  woodland stand at (1559,1651)-(1684,1776) - the collector's keep-out grew over the dry shelf, and
  the three surviving stands (90/86/91 crowns) still stock the commons, but the reason that parcel is
  now absent is geometric slack rather than anything about the place; and the title placard moved
  576 px west onto clean hinterland. One PRE-EXISTING item wants a GM ruling, recorded in
  `research/water.md`: a delivery ditch's flat `4.0 * grain` head is drawn WIDER than the tapering
  supply canal feeding it low in the tree, so the rank read inverts there - which is the one thing
  width-as-rank exists to convey.

  SECOND review pass (verifying the arc fix): **pass**. It matched all 156 tapering pieces in the SVG
  against `taper_pieces` by exact path data - every piece present, every width right - and confirmed
  the three fixes in the ink: no flat-minimum tail on any of the five delivery ditches (ch4 now 36
  distinct widths 7.92 -> 3.24, ch7 22 widths 7.85 -> 3.42), the 2-point stub drawing 5.6 against a
  predicted 5.57, and no beading or doubled opacity from the many extra round caps (154 water strokes,
  exactly one per piece, no two sharing geometry). It also confirmed the blast radius: `houses`,
  `lanes`, `wells`, `bridges`, `threshing_yards`, `gardens`, `byres`, `farm_sheds` and `kosatsuba` are
  untouched - the re-pack stayed inside the field and ground-cover fabric.

  It CAUGHT four things, all now fixed or recorded: a stale "SAME 7 piece slices" docstring left in
  `_watercourse_segs` contradicting its own body; `taper_w`'s corrected numbers still quoting the
  FORMULA at the 0.25 tenth (7.1 against an ink median of 7.0) and the "within ~0.1 px" claim failing
  at 0.90 by up to 0.35 - the same defect class the FIRST pass caught, which is why that docstring now
  says outright to re-measure in the SVG; the piecewise-vs-continuous half-width bound now recorded in
  `taper_pieces` (up to 1.19 px on the 2-point stub, which eats its abutment to +0.25 against a
  designed 0.75 - nothing crosses, and the closing fix plus its cost is written down there); and the
  collector's residual 1.64 px step notch at (1521.7,1540.7), which per-segment splitting did not
  remove because that stroke carries only 10 vertices over 1240 px (the lever is densifying the
  polyline, not the piece count). Delivery ditches, whose vertices are 3-30 px apart, are clean at a
  worst 0.78 px step.

- **2026-08-17, the net is drawn at TRUE SIZE** (GM ruling, on the measurement the taper work turned
  up: *"we can narrow the widths to be more realistic... update the net to be actual size (at least
  for hamlets)"*). The comb net was 5-6x oversize - this fan wants a ~5 ft head-race and was drawn at
  14. Widths now live in `waterfields/frame.py` as TRUE FEET and convert at draw time through
  `chan_px(ft, grain)`, so the same real channel is the same real size on every sheet. On this map
  (1 ft/px): head-race **14 -> 6.0 px**, canal A **12.4 -> 4.5**, delivery ditches **8.0 -> 2.5** at
  the head and **3.0 -> 1.5** at the tail, drain outfall **12.0 -> 5.5**. The paddy fabric now
  dominates the sheet and the water reads as a fine engineered net over it rather than as blue ropes
  laid across the crop. Scale enters in exactly one place - `MIN_CHANNEL_PX` (1.5) - which is what
  will keep the coarser tiers drawable when they convert; the FEET are not the lever for that.

  Same commit: **a delivery is never drawn wider than the canal feeding it** (`DELIVERY_PARENT_FRAC`
  0.8, `SUB_PARENT_FRAC` 0.75), capping a delivery's head against its parent's LOCAL width at the
  takeoff. That closes the rank inversion two review passes flagged at (2524.8,1540) - 7.96 px
  against a parent at 5.73 - and it is deliberately a CAP rather than conservation at the junction,
  which the GM ruled against on 2026-08-16. Measured after: zero inversions, every delivery head
  1.8-2.5 px against parents of 2.2-4.5 px.

  Review log: **pass** on the headline question - *"the sheet now reads more like a real paddy fan
  than it did... I would not go back"* - with the width ladder judged to have stopped carrying rank
  at fit zoom, which drove the head-race from 5.0 to **6.0** ft: at 5.0 the top three tiers sat
  within 1 ft of each other, so the bunsuiguchi, the one junction where hierarchy most wants to
  read, read least. 6.0 is `sqrt(4.5^2 + 4.0^2)`, i.e. where the engine's own width-goes-as-sqrt(Q)
  law puts a trunk feeding those two arms - tier selection using the law as a sanity check, NOT
  conservation-at-junctions. The pass also verified, by measuring the SVG's per-piece widths rather
  than the manifest: zero inversions at all six junctions; **0 of 640 plot rings inside the blue**
  against 10 (worst -1.73 px) before, with the tightest along-run clearance +0.77 px against a
  designed 0.75; footbridge decks tracked the widths down (spans 18.4 -> 10.5, landings a uniform
  3.0-4.5 ft); and `scatter_audit` clean at 0 violations over 270,741 bases with a flat near-margin
  density profile, so narrowing every watercourse produced no sterile halo.

  It CAUGHT four things, all now fixed: the `taper_w` worked example false for the THIRD time (its
  magnitudes are now asserted in `test_the_delivery_taper_holds_then_dwindles` and the docstring
  states only the shape - a number in prose is not falsifiable, a number in a test is); the drain's
  mouth drawn at a flat 2.5 px against a 5.5 px collector, a pinch on the sheet's most visible water
  feature, now derived from `DRAIN_FT[1]` (the TOPOLOGY record stays hairline - writing the drawn
  width there fires `irrigation_channels_hairline` and `watercourses_wider_than_ditches` on 14
  cohort maps apiece, measured); a doc-says-LOCAL / code-uses-HEAD divergence on `SUB_PARENT_FRAC`,
  resolved in the docs' favor after the code version was tried and rejected the cohort (a sub-ditch
  sized off its parent's local width has 0.14 px of room above the floor, and
  `delivery_ditches_taper` failed 22 of 24 maps); and an overstatement that the delivery cap "only
  bites where the parent has already dwindled" when it binds on three of five.

  RIPPLE, which this file's practice requires and the first draft omitted: `SPUR_SETBACK` **14 -> 17**
  in `hamletgen/consts.py`, forced by this change and recorded at the constant - narrower channels
  let the carve plant closer to the water, so the field's DRAWN extent grew and ground a spur tip had
  legitimately occupied became rice (cohort seed 11, tip 2.7 px from an outline vertex against a
  4.5 px allowance). Also: 1 house moved 67 px, 1 byre 136 px, 2 wells 14 px, the notice board 13 px,
  the threshing yard 64 px, 6 gardens re-seated, `gardens` 17 -> 18, `flooded_plots` 5 -> 2,
  `wet_plots` 25 -> 24, `tree_crowns` 10,473 -> 10,632. Every moved item is on open cluster ground,
  fronting a lane, clear of the crop and the grove.

  Recorded and NOT fixed, each with its sketch, in `research/water.md` "What drawing at TRUE SIZE
  left open": the dry-hem stand-off is pinned to the channel CENTERLINE and so did not track the
  narrowing (identical before and after while the water inside it shrank threefold - a
  derive-don't-pin violation); the delivery taper is now a 1.0 px event and sub-perceptual below the
  canal tier; eight of fifteen footbridges now deck water 1.7-2.3 ft wide, which a farmer would step
  over; and `MIN_CHANNEL_PX` (1.5) lands exactly on `aze_w` (1.5), so the finest water tier is drawn
  at the paddy bund's stroke width and separated from it only by hue.

  RULED the same day, and the reason this map is where it is written down: the GM looked at the
  finished sheet and asked whether the channels actually narrow - *"Is that getting narrower as it
  goes down into the fields, or along the edge at the top, though? It doesn't visually look like it
  is."* They do not, and measuring said so plainly: a delivery sheds **1.0 px over ~500 px** and
  canal A **3.0 over 1,504**, both 0.20 px per 100 px against 0.93 before true size, with canal B
  (2.5 over 343) the only stroke that reads as tapering. The head-to-tail RATIO is honest; the
  GRADIENT is not, and the two had been conflated - including in this file's own first draft, which
  claimed the taper "still reads on the canals". It does not; canal A's gradient is a delivery's.
  **x1.5 and x2 legibility multipliers were priced (gradients 0.39 and 0.52) and the GM chose true
  size.** So the invisible taper is a deliberate, costed trade rather than an open defect, and every
  doc that used to promise a reader they would see it has been corrected. Do not re-inflate the net.

- **2026-08-17, the three consequences of true size** (GM: *"Yes please tackle those now"*, on the
  items the true-size review left recorded-not-fixed). Two fixed, one accepted with evidence:

  **The dry-crop hem now stands off the canal's BANK, not its centerline** (`CANAL_BERM_FT` = 5.0 ft,
  a ~1 m embankment top per GB50288 plus room to dredge). The old flat offset from the centerline did
  not track the narrowing - measured identical before and after while the water inside it shrank
  threefold - so canal A ran hard against the paddy on one side with a ~15 ft empty verge on the
  other. Bare berm now ~4.9 ft median along canal A, **minimum 2.0 ft** at the bunsuiguchi throat;
  hem 24 cells here.

  That minimum took a review to reach and the bug was mine. `supply_bank_clearance` reports `past`
  for a stroke when the point lies beyond that stroke's ends, and the berm helper skipped past
  strokes on the reasoning that "some other stroke governs that ground" - true along a run, FALSE AT
  A FORK, where the pieces meet end to end and every one of them reports past. So at the one junction
  this berm exists to protect, the helper found no governing stroke, returned no berm at all, and a
  hem corner shipped **0.70 ft** off the head-race's painted bank. It now falls back to the nearest
  past stroke when nothing governs. The residual 2.0 ft is geometric rather than a bug: the stand-off
  is applied along ONE canal's normal and cannot clear a stroke crossing at an angle.

  **Planks only where you cannot stride** (`FOOTPLANK_MIN_FT` = 3.0 ft, `worth_planking`, called by
  the placer AND by `long_ditches_have_a_footbridge` so they cannot disagree). This map: **15 planks
  -> 7**, removing exactly the eight that decked delivery ditches 1.8-2.5 ft wide.

  A review caught the first version measuring the wrong thing: `worth_planking` judged the DITCH's
  widest point while the placer seated by arc fraction, so two survivors decked 2.80 and 2.40 ft -
  narrower than decks the same rule had just removed. The placer now evaluates each candidate seat's
  OWN taper width. Local water under the seven planks as shipped: **2.42 / 3.00 / 3.22 / 3.36 / 3.62
  / 3.99 / 4.34 ft**.

  Getting there took three passes, and the interesting part is that my diagnosis of the LAST one was
  wrong until a review corrected it. Making seat width a hard refusal produced the classic placer/check
  split immediately - cohort seeds 41 and 43 had a long ditch the GATE demanded a plank on and the
  placer would not lay, because its other constraints (houses, hem crop, other decks, oblique
  confluences) ruled out every wide seat. So the placer ORDERS candidate seats wide-first rather than
  refusing narrow ones, and `_ditch_plankable` was tightened to match from the other side: useful
  ground AND enough water at the SAME sample, so the gate stops demanding crossings on ditches that
  are only wide at one end and only crossable at the other.

  That left one plank at 2.42 ft, which I recorded as the price of the fallback. **It was not.** The
  review traced it to the SLOT COUNT: `n` came from the ditch's whole LENGTH, so a main whose only
  qualifying water is its head still drew two slots, and the second fell through the wide-first sort
  onto 2.42 ft - bunched 120 ft from its neighbor while a 349 ft gap sat beside it. `n` is now
  measured over the QUALIFYING run, which collapses it to 1 there. Final: **6 planks, every one over
  3.00 ft or more** (3.00 / 3.22 / 3.36 / 3.62 / 3.99 / 4.34). The fallback stays as the safety net it
  was meant to be, and no longer has to excuse anything. *The transferable bit*: on a tapering ditch
  the widest seat is always the HEAD, and a head is always a junction - so "prefer wide seats" pulls
  planks onto junction nodes and bunches them, which is a second-order effect of the width rule that
  only a spacing measurement reveals.

  **`MIN_CHANNEL_PX` stays 1.5, and that is now evidence-backed rather than inertia.** It collides
  exactly with `aze_w`, so the finest water tier is the paddy bund's stroke width and differs only by
  hue; 1.2 fixes that and is truer. It was implemented and REVERTED: the constant feeds
  `supply_bank_clearance`, so it moves every supply-side bund, and isolating it against the cohort
  showed **1.2 costs seeds 19 and 22 to `paddy_plot_seams_shared` (22/24 -> 20/24)**. The lever, if it
  is ever worth closing, is `AZE_FT` (1.5 by its own research, with room to go to ~1.3), which changes
  a stroke width and no clearance at all.

  Cohort: **22/24 against a 22/24 baseline** rolled in a detached worktree, with the residue check-for-
  check IDENTICAL (`field_ringed` + `paddy_bunds_clear_the_supply_channels`, same two seeds). Gate
  green. No regression on any axis - which took four calibrations of ONE threshold to reach, and they
  are worth the ink because every wrong setting failed the same way.

  The hem guard re-measures the berm rule from a DIFFERENT REFERENCE - anywhere on the cell, against
  the NEAREST stroke, rather than at a boundary point against ITS OWN - so it is a FLOOR under that
  rule, never a restatement of it, and its threshold has to be sized to the defect rather than
  inherited from the rule. At the FULL berm the hem collapsed **23 cells -> 8**. At HALF it wiped
  **347 px** off the fork triangle and the freed ground re-packed the wells until one stood 84 px out
  holding the map's frame open (seed 4). At a QUARTER it still dropped four cells on seed 41, whose
  wells moved the same way and broke the 4-of-4 ratchet in `tests/hamletgen/test_driver.py`. At
  **0.5 px** - the same margin `_quad_in_supply` uses - it drops only ground genuinely in the water,
  which is all that was ever wrong.

  **The through-line: a guard that DELETES a map feature hands its footprint to the next placer, so
  its blast radius is never confined to the thing it deletes.** Every one of those three failures was
  freed ground re-packing something else. The same instinct is why the berm moves the hem's INNER edge
  only and leaves its outer reach fixed - the recovered strip goes to the crop rather than becoming
  open ground for a placer to wander into.

  Corners alone also missed the original defect - an EDGE can cross a stroke between two dry corners,
  the trap `_quad_in_supply` already documents - and testing corners only shipped
  `dry_plots`/`field_ditches` overlaps on three cohort seeds.

  Review log: **pass, no errors**, over three passes (the first two reviewed a map that was still
  moving under them, which is itself worth remembering - hand a reviewer a settled artifact). What the
  final pass CAUGHT: the 2.42 ft plank's real root cause, which was the slot count and not the
  gate/placer fallback I had written into the notes, together with the 120 ft plank bunching and its
  mechanism (widest seat = head = junction); and **two more short berm corners at the fork that I had
  not measured** - 2.19 ft at (1486.6, 584.0) and 2.90 ft at (1600.9, 490.6) beside the 2.00 ft at
  (1590.0, 489.8). So the fork residue is three corners, not one. Earlier passes caught the `past`-at-
  a-junction bug and the ditch-vs-seat width scope.

  Independently reproduced and closed by that pass, none of it taken on trust: the 2.00 ft berm
  minimum against a 4.89 ft median held over a 1,592 ft chain; the plank widths; **full pedestrian
  connectivity by flood fill** - all 15 houses, both wells, all 3 lane heads and 49 of 50 field
  parcels reachable, with the two NE households routing over both fork planks at a 1.36-1.39 path
  ratio, i.e. no real detour (this closes the "two households across an unbridged brook" finding from
  an earlier roll); the hem's INNER rank gap-free from arc 25 to 1,592 ft, so the dropped cells read
  as patchwork rather than holes; and `scatter_audit` clean at 0 violations over 270,493 bases with
  density RISING outward from the water keep-out.

  Two things left open, both recorded rather than fixed. **The three fork corners** sit under the 1 m
  embankment top `CANAL_BERM_FT` cites, at the map's one hydraulic control point; invisible at fit
  zoom, and the reviewer's suggested fix is better than raising the `_in_berm` floor (whose costs are
  priced above) - CHAMFER the offending corner in a repair pass, which frees a few square feet instead
  of a whole cell and so cannot re-pack the map. **Farm sheds are 6 of 15 = 40% here** against a
  ~30% figure, but the pool-wide rate is **129/486 = 26.5%** spanning 13% to 40%, and 6 of 15 from a
  p=0.30 binomial is unremarkable (p~0.15). Recommendation on record: do NOT pin a per-map floor -
  that converts a researched rate into a quota and gives every hamlet the same 4-5 sheds, which is the
  twin problem arriving by the back door. If the pool wants to sit nearer 30% the honest lever is the
  per-household probability, and it is currently 3.5 points UNDER target, not over.

## 2026-08-17 - the fan-toe SUNBURST, ruled and fixed

The GM ruled on the open question the previous entry left: *"I would like for us to be rendering
things that are realistic. So if this is a thing that needs to be fixed, then I would like it to be
fixed."* Their framing was also the right diagnosis - the shape is realistic, the angles are not.

The research (recorded in full in `research/fields.md`, "A basin never tapers to a point - the fan
toe truncates") split the question in two, and the split is what kept the fix from destroying
something real. Radial convergence at the outfall is authentic - a cascade fan does narrow to its
collector - and so is narrowness itself: the strips at Shiroyone Senmaida and in the Cordilleras
really are a few feet wide. So the rule is deliberately **not** a minimum plot width, which is the
obvious rule and would have been wrong. What no real basin does is taper to ZERO: at a 7.5 deg apex
the plot is 5 ft wide 40 ft back from its point and 2.6 ft at 20 ft, and an aze is ~1.5 ft of
puddled mud on EACH side, so the last yards are two bunds with no floor between them - unlevelable,
unfloodable, untransplantable.

Inashiro carried **17** rings under the 15 deg gate line (the map-wide count; the two named
sunbursts are where they cluster). It now carries none - the review measured the sharpest apex going
**0.9 -> 27.9 deg** on the gate's own metric, clearing even the placer's stricter 25 deg line
everywhere - and the household count, the acreage (20.1 against a 19.5 target) and every check are
green.

**But this was a RE-ROLL, not a local edit**, and the notes are the record a future session diffs
against: the RNG stream shifted, so the view moved, 5 houses moved up to 68 ft, both wells, all 3
byres, both village groves, 6 threshing yards and 12 gardens re-seated, the notice board moved 52 ft,
and **farm sheds fell 5 -> 3 of 15 households** (33% -> 20%, against the project's ~30% storehouse
figure). The shed count went the wrong way in the previous re-roll too and nothing gates it - two
rolls in a row is worth a look even if small-n noise is a fair defense.

**The carve's sector geometry was NOT re-cut.** The previous entry expected that to be the fix, on
the strength of `_comb_toe_and_hem`'s own comment. It was wrong - or at least unnecessary. The
needles came from three much smaller places, and finding the third one is the part worth carrying:

1. The toe pass dropped unbundable slivers by an INRADIUS proxy, which is a *thickness*. A needle
   that is LONG (130-254 ft here) passes a thickness test on the strength of its middle. A
   thickness test cannot see a taper. Fixed 17 -> 8.
2. It also ran BEFORE `hem_to_bank`, so it judged a ring the very next loop rewrote. Reordered.
3. `_plant` and `_absorb`. Fixing `_plant` took 8 -> 6, and the survivors were then classified by
   instrumenting `close_seams` and tagging every needle by origin: **all of them `carved_grown`** -
   perfectly good basins that *welding a toe scrap into them* had drawn out to a point. `_absorb`
   now declines such a weld in the same ladder that already declines MultiPolygon, holed and
   bow-tie unions, and the runner-up basin takes the scrap.

**Two guesses cost a regeneration cycle each** (the carve, then the hem) before one provenance
probe answered it outright. Instrument before the second guess, not after the third.

Deliberate residue *in the engine*: a strip that needles every basin it touches stays bare, with the
fan's base floor showing through - the "odd corner left unpaddied" the research describes, and the
same treatment the thin slivers have always had. **It did not materialize on this map** - the review
measured bare ground outside the channel margins going *down*, 811 -> 531 sq ft, with nothing wider
than 3.2 ft and no fragment within 120 ft of either sunburst. The Sawada review then confirmed why it
is invisible where it does occur: the fan's floor fill is the *same* RGB as a plot interior, measured
at the pixel.

Review log: DELTA pass, verdict **pass**. It independently re-derived every headline number and
CAUGHT two things this session had not: (a) a **pre-existing self-intersecting carve ring** at
(2397,1790)-(2437,1852) - the bow-tie class the previous pass fixed on the *weld* path, which the
carve/hem path still emits and `dedup_ring`'s 1.0 ft eps does not collapse at 4.5 ft; (b) the farm
shed drift above. It also noted the paint-order lap halved again (4,441 -> 2,660 sq ft) as a side
effect. The bow-tie is logged, not fixed - it predates this change and belongs with the carve work
that cohort seeds 9 and 11 also point at (`future-work/`).

### 2026-08-17 addendum - the cohort regression closed, and it was not a conflict

The fan-toe fix above shipped with two cohort seeds (9, 11) regressing on `paddy_plot_seams_shared`,
and the first diagnosis called it a genuine two-sided conflict between the needle rule and the
shared-bund rule - four configurations measured, all failing, fix pointed at the carve's sector
geometry. **That was wrong.** Two ordinary bugs were producing it:

- `_absorb`'s tail trim was passed `3.0 * g` for "3 ft", but `grain` is `2 / ftpx`, so 3 ft is
  `1.5 * g`. The doubled value fed a 6.0 px opening to a strip whose whole mean width was 5.6 px,
  so the escape hatch annihilated every scrap and silently did nothing.
- The weld guard measured `min(raw, deduped)` while the gate reads the deduped ring only - stricter,
  but on a different measurement, which is not a margin.

Corrected, the same weld comes out at a **77.1 deg apex** at every trim width tried. The cohort is
back to **22/24 with the identical two pre-existing failures (seeds 22, 24) as the measured
baseline** - not a rotation, the same seeds failing the same checks - so there are zero new
regressions and the work is mergeable under constitution Principle XIII.

Also in this round: `_TINT_MIN_APEX` moved 25 -> 40 deg (the Sawada review's error), and the map was
re-rolled onto another session's per-segment `taper_pieces` change.

### 2026-08-17 - the tint rule, corrected by review (round 2)

The `_TINT_MIN_APEX` 25 -> 40 move recorded above did not survive its own review, and the reasoning
is worth keeping because the *first* fix was aimed at the wrong property.

The Sawada review had found the demotion structurally dead (its threshold had become equal to the
placer's new apex floor, so it could never fire). Raising it to 40 restored firing but **measured
wrong in both directions** on this map: it demoted plot 522, a 35.5 x 118.3 ft strip along the
collector keeping 82% workable floor after the aze allowance - an honest basin - while still passing
plot 456, which tapers **30.0 -> 3.4 ft over 75 ft** and scores 49.6 deg only because its needle is
TRUNCATED 8 ft short of the point. An interior corner angle cannot see a taper whose tip is cut off.
The claim that 25-40 was an empty band was also false: 15 plots sit in it here, 4 of them on the
drain.

**The discriminator is the END, not the corner.** Threshold back to 25; the ring is deduped at
`_TINT_END_FT` (5 ft - two aze at 1.5 ft leave ~2 ft of standing water between them, so a narrower
end is not an end but a point) before the apex is taken, which collapses the truncation and lets the
wedge show its real apex. Verified on the re-roll: **5 flooded plots, none of them a truncated
needle** - the end-collapsed apex equals the gate-ring apex for every one, so nothing is hiding a
point under a chamfer - and the 32.7 deg honest strip keeps its tint. (An earlier draft of this
entry said "none with a sub-5 ft end", which is stronger than the evidence and wrong: #454 closes
with a 1.1 ft edge and #522 carries 0.1-2.1 ft steps. Those are blunt chamfers on a staircase, not
ends. Corrected after the round-3 review measured them.) This also removes the threshold race for good - the demotion now measures a DIFFERENT ring
from the placer's guard rather than sitting one number away from it.

Review catch-rate: round-2 DELTA - CAUGHT the truncated-needle blind spot (with a live blue instance
on the shipped sheet) and measured the overcorrection exactly, by re-running the generator with the
threshold patched back and verifying the rings came out identical. Confirmed clean: no hole and no
doubled bund at the weld (bare ground 1742.1 -> 1742.4 sq ft, widest fragment 3.2 ft map-wide, 0.64
ft at the weld), both fan toes reading as real cascade toes (min apex map-wide 27.5 deg, busiest
collector node 3 plots against the ledgered 8-10), and `scatter_audit` 0 violations.

Still open, unchanged by this round: the self-intersecting carve ring at (2397,1790) (`drain_hem[20]`,
`Polygon.is_valid == False`, identical at HEAD) - ledgered with the carve work, not this delta.

### 2026-08-17 - round 3: the tint rule's implementation was fabricating apexes

Verdict **pass, no errors** - but the review found the end-width rule's IMPLEMENTATION unsound, and
it was a landmine rather than a shipped defect, which is the kind worth spending a round on.

`dedup_ring(r, end)` was standing in for "collapse the truncation", but it is a GLOBAL operation: it
merges short edges anywhere on a ring, so a staircase of chamfers mid-wall fuses into a spike that
was never drawn. Four measured instances on one roll - ring #550, whose sharpest REAL corner is 86.7
deg, reported 2.3 after merging 4.0 / 2.4 / 4.2 ft edges, and ring #622 (83.7 -> 20.1) sat at the
east toe inside the flooded candidate zone, one roll from demoting an honest basin. Same
overcorrection class this rule had already been caught on twice.

Replaced with `tapers_to_a_point` (banks.py), which asks the question locally and per-edge: a short
edge is an END only if both the sides it caps are real basin walls (>= 4x the end width) and the
ring is genuinely wider back there (far width >= 3x the end edge). Then the angle between the two
arms is the apex the wedge would have had if the toe had not cut it off - truncation-invariant, and
it cannot invent a corner the drawing does not contain.

**A bug in the fix, found by measuring rather than reasoning**: the first version tested only the
arm-length condition, and the angle between two BACKWARD arms is the apex angle only when they
DIVERGE - for parallel sides it is 0.0, which scores as maximally pointed while describing a strip of
constant width. Ring #633 is exactly that (parallel sides, 2.3 ft chamfer, converge 0.0 measured).
The far-width ratio is what distinguishes "narrow here, wide there" from "narrow everywhere".

Result: #550 and #633 are no longer flagged; the five that remain are genuine truncated tapers (end
2.1-4.7 ft, far width 15.5-32.2 ft, converge 11.5-22.1 deg) and only #456 among them wears the tint,
so **no shipped plot changed** - the fix removes a latent misfire, not a visible defect.

**Deliberate decision - end width, NOT taper.** The review noted that #458 keeps its tint with a 10.4
ft end while converging at 18.5 deg, marginally MORE sharply than the demoted #456 (19.2 deg, 3.4 ft
end); the only thing separating them is how deep the toe cut. That is the intended reading:
`research/fields.md` says a basin never tapers to a point and the fan toe TRUNCATES, and 10.4 ft less
two aze still leaves ~7.4 ft of standing water - a workable basin, which is what it reads as at fit
zoom. Revisit only if a roll produces a 5-8 ft end that reads as a point; see future-work/ for the
sketch, since the convergence measure now exists and switching is a one-line change.

## 2026-08-18 - where the ox sleeps, and a well objective that measured the wrong houses

WHAT CHANGED, ACROSS ALL FOUR SCRIPTED HAMLETS (2026-08-18)

- **`byre_form` is a knob now.** The doctrine had been quietly self-contradictory: the *doma* rule
  says the draft ox is stalled under the farmhouse roof, while the byre placer drew a detached shed
  on the shared ground. Both are attested - a household that OWNS its team houses it in its own
  homestead (the *magariya* 曲家, whose short arm IS the stable; the animal range of the north-China
  *sanheyuan*), while a team that is SHARED or hired stands where the borrowing household can reach
  it - so per Principle XII it becomes a per-settlement roll rather than a ruling.
- **and the overlap registry had been describing code that no longer existed** - its `byres` entry
  claimed the byre "abuts its own farmhouse (draft_byres places it against the wall)", which the
  placer stopped doing long ago. Now corrected and GATED rather than asserted in prose.
- **the well tie-break's last key is the objective itself, not a proxy** - `_worst_after` at full
  resolution inside the 66 px bucket, instead of distance to the cluster centroid.

RIPPLE ON THIS MAP (re-measured 2026-08-18 after the round-2 review): 3 byres at the placer's
target of 3, form `detached_commons`, owned by the houses ranking [4, 11, 13] by footprint of 15 -
the owner ranking was reading a `wealth` field that is 1.0 on every scripted house, so it had
collapsed to smallest-x and was handing oxen to the west edge. The shelter belt carries 194 clumps
with a minimum canopy depth of 28.0 ft measured ACROSS the wind, which is the measure that means
anything on a diagonal belt; the per-latitude framing an earlier entry used flags healthy belts
and misses thin windows. Worst walk among the 5 houses that actually need a well: 180 ft.

## 2026-08-18 - the woodland commons: off the lattice, and two hamlets that had none

WHAT CHANGED, ACROSS ALL FOUR SCRIPTED HAMLETS (2026-08-18)

Two ledgered defects that turned out to be one, with a worse one underneath.

- **the commons are off the lattice, and no two are the same size.** `open_ground_patches` samples a
  uniform 90 ft lattice, scores every seat by ONE monotone function (near the cluster, leaning
  upslope) and takes the best seat outside a FIXED separation radius - three ingredients that do not
  merely tend toward an even chain, they produce one by construction. Mizuguchi shipped the proof:
  three IDENTICAL 250 ft squares stepping (+270,-270) twice; THIS MAP had the same chain the other
  way. The accepted seat is now nudged up to half a step off the lattice and its size rolled +/-15%,
  both from the map's own position hash (so a map is unchanged by regeneration and two maps differ
  from each other), and every nudge is re-asked through the same qualification test - it can only
  move a legal seat to another legal one.
- **a hamlet at the top of the band had no wood at all.** Kashikawa - the map NAMED 樫川, "oak
  river" - seated ZERO parcels out of 231-286 candidate seats, at every rung of the shrink ladder
  and both set-back profiles. The scan demanded the whole square inside the predicted crop window
  plus a further 16 ft, while its own gate check asks that **70% of the parcel's bbox** be inside
  the view and says outright that a parcel clipping at the edge "reads as 'more wood that way' and
  is fine". The scan mirrored the check's formula but not its WINDOW, and now judges a seat by area
  the way the check does.

RIPPLE ON THIS MAP: The ruled chain is gone. The pair that stepped exactly (+270,+270) at an
identical 250 ft is now part of a set of four at 128, 195, 222, 264 ft, with nearest-neighbor
strides of 552, 1103, 1420, 1591 ft - no repeated step, no shared size.

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

RIPPLE ON THIS MAP (re-measured 2026-08-18): woodland is [(142, 37), (243, 108), (264, 128)] -
each pair is (ft across, crowns) - stocked at 540-554 sq ft per crown, which is the stated density
rather than an artifact of how much of a parcel lies near a keep-out. Crown count used to be the
number of THROWS at a parcel, and `_sparse` rejected a share of them, so small parcels came out
both smaller AND thinner; it is a target now. Parcels under the 120 ft legibility floor are
DROPPED rather than drawn small.

CLOSED 2026-08-18, having first been STALE. This paragraph read "two houses stand past 200 ft from
any lane (max 345) at the north tip", and a settlement-review re-measured it that day: the figure was
254 ft, not 345, and the farther of the two houses was the map's SOUTHERNMOST, not at the north tip.
It had been describing a roll that no longer existed - the accepted-limitation note outliving the
composition it was written about, which is its own failure mode and the reason these paragraphs are
now generated from the shipped manifest rather than carried forward by hand.

Re-measured on the current sheet, the limitation is gone entirely: **no house stands more than 79 ft
from a lane**, against the 200 ft this paragraph once accepted. The lane WEB (a peer session's
feature 123/124, merged the same day) put a way behind the back rank, which is exactly what the
accepted limitation was standing in for. Nothing here was accepted in the end - it was fixed
elsewhere in the engine, and the note is kept only because deleting it would erase the fact that it
was wrong for two rounds before it became unnecessary.

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

**On this map, measured on the SHIPPED manifest against main's tip.** 640 -> 634 basins; smallest
surviving basin 0.262 of the 1,488 sq ft design cell; acreage 20.45 / 20.45 identical to two
decimals; 15 of 15 households; field outline unchanged.

**The cluster re-packs, and the metric matters.** 0 of 15 houses unmoved, **min-max displacement
304 px** under a one-to-one matching. Say which metric: an earlier draft reported "up to 149 px",
each new house's distance to the NEAREST OLD one, which lets a single old house partner several new
ones and under-reports by 2-4x. Gardens 18 -> 17, farm sheds 4 -> 3, both wells and the kosatsuba
re-seated, `meta.view` moved.

**Two numbers earlier drafts of this entry got wrong, both corrected here rather than quietly
dropped.** (1) "Farmhouse rings all unchanged" was copied from the paddy-CELL note, where it is true
because that change draws the same number of everything; this rule changes the drawn plot COUNT and
so re-rolls the shared placement RNG. (2) A frontage figure of "108 ft, houses past 150 px 4 -> 2"
did not reproduce under any metric - it was taken before the well tie-break re-rolled the cluster on
top of it. **Lane frontage on the shipped roll is a median of 102 ft.** Against main's tip (84 ft)
that is WORSE in the middle and better in the tail; the front-row lane cap is doing its job on the
long strays and the cloud pass, which is uncapped, is now the binding one.

**The shed count is NOT a trend**, contrary to a third draft. The kura flip is position-seeded
(`_hjit(x, y, 3.0) < 0.30`), so any re-pack re-rolls all fifteen: P(X<=3 | n=15, p=0.30) = 0.297
against P(X>=6) = 0.278.

**The windbreak came out AHEAD**, 164 -> 169 clumps, after the belt fix was itself corrected - see
the shared entry below.
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
its minimax bucket at all, so a tie-break cannot reach it (ledgered in `future-work/`).

### The second well moved 48 px, and the frame reason does NOT apply here

`e0fb2417` gave `place_wells` a tie-break preferring a seat INSIDE the house-center cloud over one in
the sweep box's 120 px pad when the two tie on minimax need. On this map it fired mechanically and
for exactly its stated reason: the old seat sat at x=1148.7, **10 px west of `min(xs)`=1158.7** - so
outside the cloud - and both seats score in the SAME minimax bucket (187.9 // 66 == 146.2 // 66), so
`_outside_cloud` is what decided it, ahead of centrality. `wells[1]` (1148.7, 1538.7) ->
**(1192.7, 1560.7)**.

**What it bought here is the READ and the walk, NOT a tighter crop - and the distinction is recorded
because the write-up got it wrong first** (settlement-review, 2026-08-17). `meta.view` is
byte-identical across the change (`[1063, 360, 1678, 1796]`), and re-deriving the crop drivers with
the engine's own `crop_boxes` on both manifests puts the west edge on `gardens[13]` at x=1111.3, with
`gardens[15]` and `houses[12]` next: **the old well's box at 1136.3 was third-west and never a crop
driver at all.** There was no band of dead ground for it to hold open. The frame argument belongs to
cohort seed 41 and to Sawada, not to Inashiro. What DID improve is measurable in two other ways: the
worst-served household's walk fell **187.9 -> 146.2 ft**, and the seat moved off the scrub fringe
into swept dooryard (nearest commons scatter base **35.1 -> 57.5 ft**; the old seat had scrub within
44 ft on three sides).

**The ripple, small and worth recording because this file's practice requires it.** The wellhead's
keep-out suppressed four windbreak clumps that were the belt's easternmost outliers at that latitude
and re-seated four further west; `tree_crowns` went 11,550 -> **11,463** (-87). The belt stayed
continuous - 6/8/7/8/12/6 clumps per 40 px band from y 1400 to 1680, no hole and no notch - and the
vacated old seat did not ship as a bald patch: the windbreak closed over it with four new clumps plus
one copse clump. Nothing else on the sheet moved.

**A known bound of the tie-break, from the same review.** `_outside_cloud` tests the AABB of house
CENTERS, so it cannot tell "in the settlement" from "in the box". On this very map that box spans
y 492.7-1571.8 and therefore contains the ~345 px of grove and scrub between the north group (last
house y=868.8) and the south group (first house y=1215.6): a seat in that empty middle scores 0,
i.e. interior, identically to a courtyard seat. Harmless here because the `near[0] <= ~105 px` rung
binds first, and deliberately consistent with the rescue pass's own test - but on a genuinely
two-lobed cluster the tie-break would prefer inter-lobe emptiness over a courtyard just outside the
box. Also in `future-work/`.

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

**7 of this map's 15 farmhouses stood more than 100 ft from any way. Now none do** - the worst is
79 ft and the median 41 - **and every lane on the sheet belongs to one connected
network**, which is the part that took two review rounds to get right.

The research is decisive that a house in a nucleated cluster is reached: "every house in the
nucleated village is accessible via the interconnected system of narrow lanes and alleys". The FORM
is a seeded knob, because the record supports two and two supportable answers become variance rather
than a choice (Principle XII). This map rolled **`back_lane`**, which runs PARALLEL to the field margin behind the ranks of plots, tied to the rest by cross-links - the planned form the sources call a "rectangular framework", the one that says the place was LAID OUT. It carries **8 web
lanes** of 11.

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

*A house is served with margin, not to the millimeter.* The footpath pass triggers at nine tenths of
the reach, so no house passes by inches and none gets a path drawn to cure a rounding error.

Where the regular web still cannot reach a steading, that house gets what an outlying farmstead
really has: a footpath of its own, routed round the neighboring plots rather than ruled at them,
stopping at its first contact with the network, and planked where it crosses a ditch.

### 2026-08-18/19 - the earthen walls that zigzag: diagnosed, and fixed

Recorded here and referenced from the other three hamlet notes, because the defect and the fix are
engine-wide.

The GM, reading this sheet: *"the earthen wall is kind of going in a southward direction, and then
instead of just continuing on and meeting at the four way intersection between the north south
earthen walls and the east west earthen walls, it just goes sharply to the left before going down,
thus making these extremely irregular shapes. This really, really looks like a rendering error."*
The worst instance was the east flank at map (2283-2474, 1718): four rectangular tabs in a row, each
about 48 ft wide and 8.5 ft deep, welded alternately into the row above and the row below.

**It was a rendering error, and the provenance is measured**: snapshotting `close_seams`'s input and
output gives **0 steps on the 543 carved rings and 26 on the 634 it hands back**. The mechanism is a
PITCH: `_plant` gridded a pocket from the pocket's own bounding box at `plot_across` (48 ft), which
is where NEITHER adjacent row breaks, so every offcut landed mid-basin on both sides.

**The fix, in the order it matters** (steps at the rule's thresholds, all four scripted hamlets), measured against the maps as they shipped on 2026-08-18 (a peer session's lane-web work re-rolled all four the same day, so the rows are the effect of THESE changes, not of the day's total):

| | inashiro | kashikawa | mizuguchi | sawada |
|---|---|---|---|---|
| before | 26 | 37 | 20 | 24 |
| `_absorb` jog guard alone | 23 | 33 | 17 | 16 |
| + `_unjog` corner trade | 2 | 3 | 4 | 3 |
| + `_seam_cuts` (the pitch) | **0** | **1** | **5** | **1** |

And the number that answers the report: **no plot ring on any of the four carries more than one
step**, against 6 / 9 / 4 / 7 rings that did. The staircase is gone. What is left is single, small,
isolated corners - `python3 -m l7r.diagram.tools.jogs pool/hamlets/*.json` lists them and
[`future-work/`](../../future-work/) carries the residue with its refusal reasons.

**Two levers that did NOT work, both implemented and measured, so they are not pulled again**: a
nearest-basin partition of each scrap (`_share` - 23 -> 7 on this map, but it strands ground the weld
ladder cannot place and broke `paddy_plot_seams_shared` on three maps), and dropping a step's
vertices from every ring that carries them (not partition-preserving: rings 460 and 592 lost 400 px2
and gained 259, the difference being bare floor). Both are written up in `future-work/`.

**RIPPLE, measured against main's tip (47727a08) rather than against an older HEAD.** Rebuilding the
paddy fabric moves almost nothing else on this sheet: byres, wells, lanes, bridges, gardens,
threshing yards, farm sheds, dry plots and village groves are unchanged in count and seat (the two
wells shift 1 ft), one house of fifteen moves 39.6 ft and the other fourteen under 5 ft, `tree_crowns`
goes 8,388 -> 8,442 (+0.6%), and the view tightens 22 ft at the top and 23 at the bottom as the crop
follows the fabric in.

*That measurement corrects a settlement-review finding rather than confirming it, and the correction
is worth keeping.* The review (2026-08-19) reported a much larger ripple - all three byres re-sited,
a well moved 129 ft, `tree_crowns` +32%, lanes 11 -> 10 - and it measured honestly; its baseline was
simply an older HEAD, and a PEER session's lane-web feature landed in the same window. **When two
sessions ship into one tier on one day, a ripple measurement has to name the commit it is against or
it attributes the other session's work to yours.**

**And a process failure of mine, recorded because the fix is a habit rather than a rule.** The map
was regenerated three times WHILE that review was reading it, and for about two minutes the pool held
a fixed PNG beside an unfixed manifest - a reviewer sampling then would have measured the defect as
unfixed while looking at a fixed picture. The root CLAUDE.md already says a baseline belongs in a
`git worktree add --detach` precisely because "a stash mutates the tree under any review agent
currently reading it"; the same applies to a REGENERATION. Launch the review after the last regen, or
review a detached copy.


## 2026-08-19: the cluster-shape delta, and what the review round found in the ink beside it

**What changed on this map.** Five engine items landed, and for Inashiro specifically the first one is a
no-op by design: `cluster_shape` now BINDS (it was rolled per settlement, printed in every cohort-audit
header, and honored on 1 of 48 seeds, because it fed only a cloud-seeding pass that never runs), but
crescent keeps the old hardcoded 3.0 band, so this map's houses moved **0.00 ft** across the binding
commit and only `meta` grew - `cluster_shape: crescent`, `cluster_aspect_drawn: 3.18`. The other four:
woodland parcels are now vetted on their true ROTATED bbox rather than an axis-aligned square (the gate
measures the rotated one, so a parcel could be approved and drawn two-thirds off-frame); byres carry a
rolled FORM, and this map rolled `detached_commons`; the windbreak belt must be continuous across the
wind; and an oblique bridge deck may skew up to 7 deg toward square when a deck along the way cannot
clear the water.

**Verified rather than assumed** (settlement-review, this date): the belt is ONE unbroken run - 227
clumps, y-coverage 609-1536 as a single segment, max bare gap **0.0 ft** against a 30 ft allowance. All
three woodland parcels are on the sheet (100% / 100% / 83.2% of bbox in view), on dry ground (>700 ft
from either marsh), and visibly stocked (91 / 128 / 30 crowns). All six decks sit at 89.5-90.0 deg to
their local channel. The 2026-08-16 marsh-seated crownless parcel failure is absent in every form.

**THE RIPPLE - three defects the review found in ink this delta moved past, none of them caused by it:**

1. **The copse is drawn INSIDE the windbreak.** `village_groves[1]` (role `copse`, 11 clumps) is
   documented as the greenery filling the OPEN gaps among the houses, and `settlements/vegetation.md`
   says outright that the copse, not the belt, fills the inner gaps. Measured clump-to-nearest-belt-clump
   distance: 9, 8, 6, 4, 6, 4, 11, 9, 26, 30, 83 ft - **10 of 11 inside the belt's own 14 ft canopy**.
   The copse spans x 1096-1188 while the houses span 1108-1331, so every clump landed on the belt's
   ground at the cluster's west edge and the courtyards east of the first rank get nothing. A whole
   feature is invisible.
2. **Every lane junction draws a cap bead, and the back lane steps width mid-run.** Each lane is stroked
   outline then filled, so a second record's round cap outline paints over the first record's fill - a
   circular seam across the roadway at (1185,785), (1249,801), (1270,1183), (1279,1312). Compounding it,
   `lanes[3]` is w=6 and `lanes[4]` is w=3, so one continuous ~230 ft back-lane run halves its width at
   that same junction (`ways.py:695`, a link inherits the width of the way it joins and leaves its far
   neighbour at 3).
3. **The notice-board caption erases the lane it stands on.** The caption is centered on the glyph with a
   3 px background halo, and `lanes[1]` passes x~1235 at y=1009 with w=5 - so the halo knocks a visible
   notch out of the map's busiest internal lane, between "notice" and "board".

**And two calibration questions worth recording rather than silently fixing**: the woodland bearing
jitter is `fall + 90 +/- 20 deg`, and this map's fall is cardinal, so the maximum achievable rotation is
20 deg - the roll gave 0.1 / 5.9 / 11.1, and the first parcel is drawn effectively axis-aligned, which is
the "perfect rectangle" read earlier rounds objected to. Separately all three parcels came out at aspect
1.32 / 1.38 / 1.34 - a 4% spread from a range of 1.0-2.2, because the ladder collapses the roll toward
its floor. Neither is a form question: *iriai* boundaries followed ridge, stream and path, so nothing
rectilinear is attested and this is calibration.
