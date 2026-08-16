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
  pixel; three dry woodland parcels (250/250/160 ft) on the merged roll (the count is roll-derived and has moved since - see the later entries); the pocket pond re-seated to (2092, 1671)
  with no ink-on-water residue (the 2026-08-15 logged item cleared with the re-roll). Review log:
  full DELTA caught the two marsh-seated parcels (one 100% wet with zero crowns) that drove the
  marsh keep-out; follow-up pass on the re-seat. Reviewer note logged in future-work.md: stand
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
  SAMPLES, and shrank the box toward its own centroid until it lapped its neighbours only
  shallowly. Sizing from the samples rather than from the pocket's walls left a ribbon of bare
  floor on all four sides of every filler - the standalone rectangle - and the shallow-lap
  acceptance (every probe up to 12 real ft inside a neighbour, only one probe required on bare
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
  round-trips the ring it will actually record and declines in favour of the runner-up basin if it
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
that cohort seeds 9 and 11 also point at (`future-work.md`).
