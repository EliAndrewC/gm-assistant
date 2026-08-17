# /diagram - deferred engineering (things we intend to pick up)

Load this file when planning the next diagram feature, or when the GM asks "what were we
going to fix about the process?" Update it WHENEVER map work runs long - each entry should
name the pain, the evidence, and the sketch of the fix.

## 1. Parametric feature bundles (gate wards, rim bands) - HIGH VALUE
The 021 wall resize (2026-08-10) invalidated ~hundreds of hand-typed coordinates and cost
hours of migrate-regen-check cycles. The pieces that were FORMULA-DRIVEN from the wall
parameters (rim temples, moat, ring road, wall towers) migrated instantly and for free; every
literal coordinate had to be re-typed one check-failure at a time - and a careless bulk
shifter corrupted list multipliers (`* -144`) and took extra rounds to repair.
**Fix sketch**: a `gate_ward(gate, ...)` helper that lays a whole guan-xiang bundle (market
frontage, flophouse, inn+stables+yard, its lanes, its district poly) RELATIVE to whichever
gate it is handed; a sibling for ring-adjacent band fills. A layout change then becomes a
parameter change. Extract the helper the NEXT time a gate bundle is authored or moved.

## 2. Fabric-first generation (the GM's ordering question, 2026-08-10) - RESEARCH DIRECTION
Today's order is shell-first: wall/roads/water, then fabric fitted inside, with the wall
PRE-SIZED from a budget density constant. The constant was wrong once (Tango's 690 vs the
capital's as-built 1,367) and the failure mode was structural: fabric could not fit, overflow
silently went extramural. A fabric-first order - grow streets/quarters/temples roughly
radially, THEN wrap wall/moat/ring around the built hull - makes wall-sizing correct BY
CONSTRUCTION. Known hard parts (the GM named them): gate-anchored programs (guard houses,
inspection stations, caravan clusters) need the gates, so it becomes two-pass - grow fabric,
choose gates on the hull, then place gate programs and re-arrange locally; ring/moat must
wrap an irregular hull rather than an ellipse. This is a full feature with its own spec, not
a mid-feature pivot. Candidate: the next city-tier map.

## 3. Author-loop pace: log of what ran long (keep appending)
- 021 resize re-lay (2026-08-10): ~4h of migrate-grind. Root cause: literalness (see #1),
  plus one avoidable class - bulk text-shifters that touched non-coordinate numbers. Any
  future bulk transform must be coordinate-aware (pairs/boxes only) and verified by
  `grep -E '\* -|court_every=[0-9]{3}'` before regen.
- Regen+gate cycle is ~10s for the whole capital; the cost is the NUMBER of author cycles,
  never the generator. Batch many fixes per cycle; measure with the check's own data
  (locators, tools/why_placed.py) instead of guessing coordinates - every hand-guessed seat this
  feature landed on something.

## 4. WALL SIZE SETTLES FIRST, against a slack threshold (GM process rule, 2026-08-10)
Measured at the moment the GM called it from the render: 41% of the walled interior was
claimed-open commons, and hours of fine adjustments (junction snaps, well boxes, kido
reserves) had been tuned against a wall that was about to be wrong. The rule: **an interior
slack check (claimed-open + unclaimed <= ~15% of interior) is an EARLY reconciliation gate**
- run it, and re-derive the wall, BEFORE any fine iteration. Fine adjustments are downstream
of the wall; the wall must never be adjusted after them. Implement as
`capital_interior_slack_in_band` beside the packed-split check, and write the ordering into
the capital-build sequence in `settlements/capitals.md`. (This is also the strongest single
argument for the fabric-first ordering in #2: a wall wrapped around a grown fabric has the
right slack by construction.)

## 5. Interior fullness DEFERRED on Shiro Daika (GM 2026-08-10, end of the resize day)
After the third wall derivation the slack check passes (<=15% claimed-open) but the render
still reads empty to the GM's eye: bare-rendered commons, the model's 20% circulation, and a
fabric that packs naturally denser than the model prices. Options weighed: a third shrink
(hour-plus migration each, diminishing returns), raising population (rejected - 12,360 is
budgets.md-anchored research), or defer. DEFERRED by GM choice: ship the green map as the
first pass; **wall-to-fabric fullness is the headline requirement of the fabric-first
feature (#2)**. Cosmetic option noted: a faint ground tint for kept commons (between blank
and scrub). When fabric-first is specced, start from this map's slack profile as the
motivating example.

### 2026-08-10 addendum: the first pass SHIPPED against #5

Shiro Daika went out green with three waivers (packed_inwall ~1,930/2,100, census ~130 short,
rotating ~1.5 ac pockets) - the deferred-fullness gap made concrete. Fixture:
`pool/regressions/capital_fullness_deferral_fires_on_the_first_pass_shiro_daika.json`. Two fresh
data points for the fabric-first design:

- Realized machi density is bounded by the SERVICE fabric, not the packer: streets + kido
  reserves + well courts + hand roji took ~8% of C_PACKED at the settled wall. A fabric-first
  pass must budget service ground per district (wells per ~20 households, roji per 95 px reach)
  BEFORE deriving the wall, or the same gap reappears.
- The endgame grind was dominated by cross-coupled reflows: every well/claim/alley edit re-rolls
  neighboring packs, so single-defect fixes rotate the defect population instead of shrinking it
  (three "dead cores" moved five times). Fabric-first should place service features and packs in
  one deterministic order per district, so a local edit stays local.

## DONE: azemame record hygiene - water-buried beads (2026-08-15, same day)

Resolved the day it was filed, on the GM's ask ("fix the water-buried beads so the record stays
honest"). `_bund_beans` now drops beads under the ditch net's late strokes, `draw_comb_field` drops
beads inside the source pond / pocket ponds (the flavor pass moved above the bead line so pocket
ponds exist before beads commit), and `bund_beans_on_bunds` reads the painted truth from
`drawn_channels` (post-clip strokes, late flag) / `pond` / `field_ponds`. Regression fixture:
`pool/regressions/bund_beans_on_bunds_fires_on_water_buried_beads_inashiro.json`.

## DONE 2026-08-16: pocket ponds carry ink-on-water of their own (settlement-review, 2026-08-15)

Found while confirming the azemame water-honesty fix: Inashiro's pocket pond at (2144, 1724) has
the field-foot margin drain stroke painting across its lower-left quadrant, and hinterland
scrub/grass tufts drawn on top of its fill (the pond's lower half hangs outside the field envelope
over hinterland ground, and the late drain + phase-5 scatter both lap it). Same principle the bead
fix established - no ink over water, no water under ink - one class over: the pocket pond needs a
keep-out the hinterland scatter and the late water honor (or `_plot_pond` should refuse a plot
whose ellipse leaves the field envelope). Barely visible at fit zoom; logged rather than fixed
because it is baseline-adjacent, not part of the bead delta.

**Resolved by the 2026-08-16 re-rolls without dedicated code**: the pond re-seated to (2092,
1671) and two independent review passes confirmed no drain stroke and no scatter tuft crosses
its fill on the shipped roll (the scatter water-skip fix and the re-seat between them cover the
class). If a future roll regresses it, the fix direction in the paragraph above still applies.

## Review residue from the supply-bank hem re-roll (settlement-review, 2026-08-15)

Three judgment items the four DELTA reviews surfaced that are real but were deliberately logged
rather than fixed with the hem work (none is a gate failure; each is an idea for the next pass at
its area):

- **A sluice-gate glyph at the hamlet intake.** Mizuguchi is NAMED for its sluice (水口) and draws
  none - the brook simply necks into the head-race. The engine has sluice-gate furniture at other
  water handoffs; the comb intake could carry one at every tier, and on Mizuguchi it is the point
  of the map.
- **DONE 2026-08-16: Kashikawa's woodland commons all land off-frame.** Resolved with the
  known-opens round below: the decision went to seating (the frame stays tight to the working
  settlement; the coppice moves), `open_ground_patches` confines the scan to the predicted kept
  window, and `woodland_commons_within_the_frame` gates it.
- **The kept/dropped read along hemmed ditch banks.** Inashiro's first lateral carries an
  alternating chain of kept bank plots and dropped slivers that reads as a dashed line of boxes; a
  coarser keep-or-drop over a whole bank strip would read cleaner. Same area as the hem work but a
  presentation refinement, not a correctness one.

## Review residue from the canal-B fork re-roll (settlement-review + cohort, 2026-08-16)

The fork feature (research/water.md "The head-race forks - supply commands both flanks") re-rolled
the four live hamlets three times; the review rounds' errors are fixed (thread tails, minimax
wells, the board's clump keep-out, the lane-crossing guards).

### DONE 2026-08-16 (the known-opens session, same day): four ledger items closed

- **The hairline bund-in-supply-stroke on rolled seeds (25, 34; 41@hh15)** - diagnosed to the end:
  the placer exempts a carved corner projecting epsilon PAST a branch tail (`past`), and the
  manifest's 0.1 px rounding collapses corner and stroke tail onto the same coordinates, so the
  gate saw t = 1.0 exactly and fired at gap 0 on a corner the placer legally allowed. One
  predicate, two verdicts, split by the round-trip. Fixed IN the shared predicate:
  `supply_bank_clearance`'s `past` is arc-based with `_PAST_EPS` (0.25 px) slack at both ends.
  48-seed cohort re-swept: pass rate unchanged (45/48), the named seeds clean, ratchet seeds 41-44
  clean. (The marginal cohort seeds rotated, as engine changes always rotate them.)
- **`meta.cluster_shape` silent non-recording** - `stage_homesteads` now records
  `meta.cluster_seeding` always ("cloud" when the cluster-seeds cloud ran and honored the knob,
  "frontage" when the rows/frontage passes seated everything); gate
  `settlement_records_cluster_seeding` holds the declaration-exists invariant.
- **Mizuguchi's SE floor wedge** - generalized and fixed: ALL FOUR live hamlets carried floor past
  the flat-extended collector line (0.7-1.8% of floor area, worst 350-548 px; only Mizuguchi's was
  needle-shaped enough to catch a reviewer's eye). `build_comb` now trims the envelope to the
  collector's command area via `floor_overhang` (shared predicate), gated by
  `comb_floor_ends_at_the_collector`. Pre-fix Mizuguchi frozen in `pool/regressions/`.
- **Sawada's cropped-out woodland commons** (and Kashikawa's, and Mizuguchi's) -
  `open_ground_patches` now confines the scan to the predicted kept window (computed from the same
  `_crop_boxes` source the crop reads, + the shared `CROP_MARGIN`), gated by
  `woodland_commons_within_the_frame`. The review of the fix then caught the second-order defect
  the same day: the confinement pushed parcels onto the WET TOE (Inashiro seated one 100% in the
  marsh with zero crowns of ink). So the scan also treats every recorded marsh poly as a keep-out,
  a shrink ladder (250 -> 200 -> 160 -> 125 ft) re-scans slots the full size cannot seat, and
  `woodland_commons_on_dry_ground` (max 30% wet) gates it - a map whose dry window holds fewer
  parcels than asked honestly seats fewer (Kashikawa 1, Sawada 1). Pre-fix manifests frozen.

### Still open

- **DONE 2026-08-16: the in/out width ladder at junctions - RULED, keep the convention.** The GM
  weighed keep / intake-stilling-pool / conserve-at-fork and ruled that drawn width depicts rank,
  not discharge (full reasoning recorded in research/water.md "Drawn width is RANK"); the
  settlement-review doctrine now says junction conservation is not a finding, so reviewers stop
  re-flagging it. No ink changes.
- **DONE 2026-08-16 (second ledger round): collector-junction wedge plots in the water-gray
  fill.** The tint was ink-only, so first the PICTURE became a record: `draw_comb_field` writes
  `flooded_plots` (the painted-blue centroids; `wet_plots` stays the topography record), the
  bead-honesty precedent. Then the shared predicate `pointed_ring` (waterfields.banks) splits
  needles from basins by interior angle - measured pool-wide the seam wedges run 7-23 deg
  against 45+ for honest hem strips - and the carve demotes the tint at 25 deg (position-keyed
  green, no extra RNG draw) while `flooded_plots_read_as_basins` fires at 15 (placer stricter
  than gate, the supply-bank calibration). Review-verified by full SVG fill census on Sawada:
  4 painted tints, 4 records, min angle 25.0+ (the exactly-25.0 survivor pair at the west seam
  is an ACCEPTED boundary case - it reads as a flooded plot, not a pond). Pre-fix Sawada frozen
  with its tint reconstructed from the committed SVG.
- **DONE 2026-08-16 (second ledger round): the well minimax counts stream-watered houses.**
  `settlement.surface_water_dist` is now the ONE predicate (channels + streams + moat polylines
  + the pond rim, exactly the records the check reads); `settlement_dwellings_watered` calls it
  for its verdict, and `place_wells` uses it twice - the worst-served objective maxes over the
  NEEDY houses only, and the rescue pass skips a house surface water already serves (the
  Kashikawa SW-pocket ruling, now structural). Review-verified on all four maps: wells land
  among the households that need them and none is squandered on channel-fronting rows.
  Cohort rate after the round: 43/48 vs the 45/48 baseline - the two motivating seeds now pass
  (25's hairline, 24's shade), and the residue delta is the marginal-seed rotation class
  (field_ringed borderline flips from the envelope dedup, one well-frame flip from the seat
  re-ranking); no shipped map is affected, and each residue check has live teeth.
- **DONE 2026-08-16 (second ledger round): the envelope trim deposits near-duplicate
  vertices.** `dedup_ring` (waterfields.banks) merges consecutive vertices closer than 1 px,
  closing pair included, right after the trim - the same idiom as the bowtie pass's collapsed
  plot vertices.
- **DONE 2026-08-16 (second ledger round): woodland stand crowns are ink-only.**
  `commons(role="woodland")` now records every drawn crown into `tree_crowns` (the same flat
  [x, y, r] run the homestead groves use) plus a per-parcel `crowns` count, and
  `woodland_commons_visibly_stocked` holds the declaration-exists invariant (missing count =
  regenerate; under 5 crowns = a claimed woodland the drawing does not deliver) -
  review-verified recorded-vs-drawn agreement (35=35, 15=15 on Kashikawa). The placer-side
  half landed too: a woodland parcel's poly registers in `block_polys`. Second-order fallout
  fixed in the same round: with the wells realigned, Kashikawa's kept window closed at every
  shrink rung and the oak map went woodless - so the scan gained a last-resort SET-BACK
  profile (40/100 px, still 2.9x/1.4x above the gate's own 14/69 floors) that runs only when
  the generous 80/180 profile seats nothing.

## Cohort seed 2: pre-existing drainage-routing failures (found 2026-08-16, fan-toe pond session)

`python3 -m hamletgen --batch 1 --seed 2` fails FOUR checks - `drainage_discharges_downhill`,
`drainage_junction_smooth`, `features_do_not_overlap`, `watercourses_flow_downstream` - and fails
them IDENTICALLY on unmodified HEAD with the pond fix stashed, so it is a pre-existing engine
issue, not fallout. Spec: 13 households, fall=135 (SE), wind=NW, `water_sink="offmap"`, round
cluster, T lanes. No pool map hits it; it only surfaces in the cohort, which is exactly what the
cohort is for.

Sketch for the picking-up session (the open-decision rule - carry the sketch, not just the
question): the failure cluster smells like ONE routing defect, not four - the offmap sink brook
for this fan geometry likely lands on ground that makes its junction acute and its run uphill,
with the overlap a symptom of the same bad route. Landing site: `hamletgen/sink.py::stage_sink`
offmap branch (the swing-major bearing/junction search and its `bad` scoring); reproduce with the
seed-2 roll above, read which route was chosen and which candidate SHOULD have won, and check
whether the least-bad fallback (`best`) was taken - the `# pragma: no cover` on that path says no
cohort fan exercised it when it was written, and seed 2 may be the first. Hold it with a frozen
cohort-2 manifest in `pool/regressions/` once diagnosed (fires: the four names above).

## Fold settlement/city/civic.py into castle_civic.py (feature 113, 2026-08-16)

Left deliberately undone by the `settlement/city/` package split, with the reasoning recorded so
the next session does not have to re-derive it.

`governor_mansion` is the only member of `settlement/city/civic.py`. It calls `self.manor(...)` and
re-keys the record out of `M["manors"]` - it is a STRUCTURE reusing the manor glyph, not city
infrastructure, so it belongs with the castle, the ministries and the dojos in
`settlement/castle_civic.py` rather than beside walls and moats. The size works: 903 + 21 = 924
lines, still under the clause-13 bar.

**Why 113 did not just do it.** Feature 113's whole value proposition was "provably nothing moved"
- a pure move verified by byte-identity. Relocating a method to a DIFFERENT mixin widens the
composed-surface guard across two mixins at exactly the moment the guard is meant to be pinning one,
and makes the stage something other than a pure move (112 research R5 on why that property is worth
protecting). Isolating the orphan in its own module was the cheap way to keep the index honest now
and make the relocation a one-file change later.

**What the move costs**: shift the method, drop `CityCivicMixin` from the `CityMixin` bases in
`settlement/city/__init__.py`, move `governor_mansion` out of `_CITY_SURFACE` in
`tests/settlement/test_city.py` and into whatever guard `castle_civic.py` carries, delete the
`civic.py` row from `settlement/city/CLAUDE.md`. Verify with the same byte-identity sweep - the
drawing must not change. `specs/113-city-package/quickstart.md` has the harness.

## Review residue from the shared-bund re-roll (settlement-review + cohort, 2026-08-17)

Both items are the CARVE's fan-toe geometry, not the seam pass that surfaced them, and both are
measured rather than impressionistic. Full context in `pool/hamlets/inashiro.notes.md` (2026-08-17)
and `research/fields.md` "Bunds are shared, and the fabric is continuous".

### `plot_rings` is a paint-order STACK, not a partition

On Inashiro 39 ring pairs lap, double-counting **0.10 acre** of the recorded fabric (worst: a
21.3 x 41 ft slab between #471 and #529). This is invisible in ink and correctly so - each plot is
one `<polygon>` carrying fill AND stroke, emitted in index order, so the later basin paints out the
bund it covers and the pair reads as the single shared wall it should be. `paddy_plot_seams_shared`
therefore judges near-CONTAINMENT rather than depth, deliberately (its comment carries the
reasoning, and the fixed map's deepest legal lap covers 41% of a ring).

`close_seams` HALVED the double-count (8,583 -> 4,445 sq ft) as a side effect, so this is moving the
right way on its own. What is still owed is a decision, not a fix: either trim a lapped ring to its
visible extent at record time - which makes the manifest a true partition and lets any future
basin-to-basin rule trust it - or state in the field record's own comment that `plot_rings` is a
paint-order stack, so the next session measuring area or adjacency from it knows to dissolve first.
**Implementation sketch** (per the open-decision rule): the trim lands in
`settlement/fields/comb.py::_comb_draw_paddies`, where the record is written and draw order is
already known; hold it with a check that the rings' area sum equals their union's area; the
deliberate exclusion is the drain hem, which is recorded separately and does not participate.

### DONE 2026-08-17: the fan-toe SUNBURST - RULED and fixed

The GM ruled on the realism question directly: *"It sounds like you are telling me that this is
based on a shape which is realistic, but that the degree to which it is true, like the angles in
particular are themselves not realistic ... I would like for us to be rendering things that are
realistic. So if this is a thing that needs to be fixed, then I would like it to be fixed."*

The research agreed with that reading and is recorded in full in `research/fields.md` ("A basin
never tapers to a point - the fan toe truncates"): the fan's radial convergence is authentic and
narrow strips are authentic, so the rule is deliberately NOT a minimum width; what no real basin
does is taper to zero, because the last yards of a 7.5 deg wedge are an aze on each side with no
floor between them. Three placers now refuse a needle apex at 25 deg (`pointed_ring`'s existing
pool-measured calibration - no third magic number), the gate `paddy_plots_are_workable_basins`
fires at 15, and the four pre-fix manifests are frozen in `pool/regressions/`. The carve's own
sector geometry was NOT re-cut: the needles turned out to come from the toe drop's thickness proxy,
from `_plant`, and above all from `_absorb`'s welds, so the sector change this entry anticipated
was never needed.

**The one methodological note worth keeping:** two rounds of fixing were spent guessing where the
survivors came from (the carve, then the hem - both wrong) before a provenance probe classified
every remaining needle in one run as `carved_grown`, i.e. made by a weld. Instrument first.

### OPEN (low priority): the flooded tint discriminates on TRUNCATION DEPTH, not on taper

Recorded as a deliberate choice with its trigger, not as a defect. `tapers_to_a_point` demotes a
tinted plot whose END is under 5 ft; a plot converging just as sharply but cut off higher keeps the
tint. Measured on Inashiro: the demoted #456 converges at 19.2 deg with a 3.4 ft end, while #458
keeps its tint at 18.5 deg with a 10.4 ft end - **the sharper taper is the one that stays blue**, and
only truncation depth separates them.

That is intended (`research/fields.md`: a basin never tapers to a point, and the fan toe TRUNCATES;
10.4 ft less two aze leaves ~7.4 ft of standing water, a workable basin, and it reads as a wedge with
a flat end at fit zoom). **The trigger to revisit** is a roll that produces a 5-8 ft end which still
reads as a point on the sheet - the band is empty on today's maps, so the rule is untested there.

**Implementation sketch** (per the open-decision rule): `tapers_to_a_point` already COMPUTES the
convergence angle, so switching from truncation to taper is dropping its `end` precondition and
firing on the angle alone - measured separation on Inashiro is clean (18.5 / 19.2 deg for the two
wedges against 0.8-10.2 for the honest quads #526/#527). What holds it: the `_TINT_*` tests in
`tests/waterfields/test_seams.py`, which would need a case for an untruncated sharp wedge. The
deliberate exclusion is the far-width ratio - keep it either way, or parallel-sided strips score as
maximally pointed (ring #633 did, at converge 0.0 exactly).

### DONE 2026-08-17: cohort seeds 9 and 11 - and the "genuine conflict" was two bugs

**The conclusion recorded below was WRONG, and how it was wrong is worth more than the fix.** The
entry called the seeds 9/11 regression a genuine two-sided conflict between the needle rule and the
shared-bund rule, on the strength of FOUR measured configurations that all failed, and pointed the
fix at the carve's sector geometry. The table was accurate and the inference from it was not. Two
ordinary bugs were producing it:

1. **A unit error made the escape hatch a silent no-op.** `_absorb`'s tail trim was handed
   `3.0 * g` as "the 3 ft the seam rule ignores". But `grain` is `2 / ftpx`, so px-per-foot is
   `g / 2` and 3 ft is `1.5 * g` - the value passed was DOUBLE. At a hamlet's ftpx 1.0 that fed
   6.0 px to an opening meant to shed the tail of a strip whose entire mean width was 5.6 px, so it
   annihilated every scrap it touched and returned nothing, every time. The retry looked like it was
   running and was doing nothing. Same shape as "a check that never RUNS looks exactly like a check
   that passes", one layer down in the placer.
2. **The guard measured a different ring than the rule it protects.** It took
   `min(raw, dedup_ring(...))` while `paddy_plots_are_workable_basins` reads the deduped ring only.
   Stricter, yes - but stricter on a DIFFERENT MEASUREMENT, which is not a margin. Placer-stricter-
   than-gate means a stricter threshold on the same measurement (18 vs 15), never a second
   measurement bolted alongside it.

With the width corrected the same weld the "conflict" was built on comes out at a **77.1 deg apex**
- not marginal, not a trade. Measured across trim widths 1.5/2.0/3.0/4.0 px it is 77.1 at every one,
keeping 96/92/81/42% of the strip. Seeds 9 and 11 pass both rules; the carve's sector geometry was
never implicated.

**The methodological cost, recorded because it repeated inside one session.** Two separate wrong
conclusions came from probes that MIS-ATTRIBUTED their own output. The first counted every
`_absorb` decline as "declined by the new guard" when most were the pre-existing MultiPolygon/
bow-tie rejections. The second printed `min(raw, dedup)` as the apex VALUE next to the raw ring's
worst VERTEX - two different rings - which produced a confident, wrong finding ("the apexes are
90-100 px away, so they are pre-existing artifacts") that was written into a code comment before
being checked. Both are the diagram CLAUDE.md's own rule - *a diagnostic that restates what it
observes will lie to you* - and the tell in both cases was the same: the probe reported a number
and a location that came from different computations. **Print the value and its provenance from one
expression, or do not print the location.**

*Superseded entry, kept for the measurements and as the record of the wrong turn:*

### OPEN, and it is the carve after all: cohort seeds 9 and 11 (2026-08-17)

The needle fix left **two cohort seeds failing `paddy_plot_seams_shared`** that passed before it
(24-seed cohort 22/24 -> 20/24; the pre-existing failures on seeds 22 and 24 are unchanged, and all
four shipped hamlets are green). This is a REAL regression of an existing rule on two seeds, ledgered
rather than hidden, and the diagnosis is complete even though the fix is not.

**It is a genuine two-sided conflict, proved by A/B rather than argued.** On both seeds the carve
leaves a TAPERING scrap between two basins, and every resolution of it breaks one rule or the other:

| `_absorb` behavior | seed 9 / 11 outcome |
|---|---|
| decline a weld that needles the host | `paddy_plot_seams_shared` - the strip lies bare between two walls |
| accept any weld (guard off) | `paddy_plots_are_workable_basins` - the host is drawn out to a needle |
| accept the LEAST-BAD weld, unfloored | worse still: breaks 3 of the 4 SHIPPED maps on the needle rule |
| accept the least-bad weld only above the gate line **(shipped)** | seeds 9/11 still seam-fail: no candidate clears 15 deg |

So there is no threshold and no choice of neighbor that resolves it - measured, not assumed. **The
scrap should never have existed**, which means the fix is upstream in the carve's sector geometry:
exactly what this entry's original text predicted ("the carve opens a sector whose boundary has
already collapsed onto the drain"). For 22 of 24 seeds that change turned out to be unnecessary;
for these two it is the only thing left.

**Implementation sketch** (per the open-decision rule - carry the sketch, not just the question):
the landing site is `waterfields/carve.py`'s sector opening, and the reproduction is
`python3 -m hamletgen --batch 1 --seed 9`. Instrument `close_seams`'s bare-ground pass to dump the
offending pocket (seed 9 has it near the `paddy_plot_seams_shared` report at 1161,1866) and check
whether its taper comes from a sector whose boundary thread has been clipped onto the collector -
the same degenerate-sector signature `_comb_toe_and_hem`'s comment names at Ubame's west corner.
What holds it: the two seeds must pass BOTH `paddy_plot_seams_shared` and
`paddy_plots_are_workable_basins`, and the four shipped hamlets must stay green. Deliberate
exclusion: do NOT reach for another apex threshold - all four configurations above were measured
and none works.

*Original entry, kept for the measurements:*

### The fan-toe SUNBURST - needs a GM ruling before anyone re-cuts it

At two places on Inashiro (~1893,1650 and ~2430,1845) eight to ten bunds 130-254 ft long converge
on a ~10 ft stretch of the collector bank, at apex angles of 7.5 / 9.5 / 9.8 / 10.6 / 13.5 / 14.3
deg. No node carries five plots at one point, so it is staggered rather than a literal star, but at
fit zoom it is the one place the paddy fabric still reads machine-drawn. **Pre-existing** - 7 plots
under 15 deg before the re-roll, 8 after - and every scripted hamlet has the same shape.

`_comb_toe_and_hem`'s own comment already names the cause and the fix: the carve opens a sector
whose boundary has already collapsed onto the drain, and "the real answer there is for the carve to
stop opening a sector whose boundary has already collapsed onto the drain, which is a change to the
carve's sector geometry". Before spending that, ask the GM whether a fan toe is ALLOWED to converge
like this - a real cascade fan does narrow to its outfall, and the honest question is whether this
narrows too tidily. The answer settles all four scripted hamlets at once.

### Three members that are in `settlement/structures/` only because of where feature 025 cut

Feature 114 split `settlement/structures.py` into a package and, in doing so, isolated the members
that do not belong to the structures subsystem at all - so each of these is now a one-file change
plus one row of `settlement/structures/CLAUDE.md`. None was moved by 114 itself, deliberately: a
cross-mixin relocation would have made that feature's byte-identity oracle answer two questions at
once, so a dirty diff could not have distinguished "the composition is wrong" from "moving `road`
changed something".

- **`road` -> `water_ways.py`.** It is a way, and `water_ways.py` is already the ways module (lanes,
  streets, alleys, kido). It sits in `structures/ground.py` today.
- **`pasture` -> `land.py`.** It is a land surface, and `land.py` already holds the commons, marsh,
  toe bands and hinterland. Same module today.
- **`structures/captions.py` -> `castle_civic.py`, but this one is an OPEN QUESTION, not a pending
  move.** `castle_civic.py` holds `place_caption` (the draw-time seat ladder) while `captions.py`
  holds the probes underneath it - so folding them gives one caption subsystem, but three of the
  five probes are consumed by siters that live in `structures/fixtures.py`. The implementation
  sketch, the thing that holds it (the composed-surface guard, which fails naming the five names if
  they move out without the frozenset being updated in the same commit) and the one deliberate
  exclusion (`_under_a_caption`) are all in `settlement/structures/CLAUDE.md` under "Three
  placements you will want to fix".

The two straight moves are cheap and safe on their own: every consumer reaches these members through
`self.` on the composed `Settlement`, so no call site changes - the move is the member's text, its
row in the two indexes, and the name migrating between the two mixins' surface frozensets.

## Feature 115's leftovers (civic_grounds/)

Same shape as feature 114's above: pending PARENT-level relocations that were deliberately not
folded into the split, because moving a member between parent-level mixins would have made the
byte-identity oracle answer two questions at once.

- **`_ward_fence_cap` -> `water_ways.py`.** It is a ward-fence predicate and `water_ways.py` is
  already the wards/fences module. It sits in `civic_grounds/funerary.py` today because `mausoleum`
  is its caller inside the package being cut (the placement-follows-the-caller rule). Its other
  consumer, `structures/compounds.py`, reaches it through the composed `Settlement` and is unaffected
  either way.
- **`precinct_interior` -> `shrines_wells/`.** It draws a sovereign temple precinct's INTERIOR
  program (abbot's residence, order administration, library, two dormitories, kitchen/refectory), so
  it is religious ground; `civic_grounds/civic.py` holds it as the institutional-works member.
  Feature 116 has since made `shrines_wells` a package, so the destination is now a specific file -
  `shrines_wells/shrines.py` is the closest fit. Note it calls `self.cemetery`, which stays in
  `civic_grounds/funerary.py`; that cross-package `self.` call is already normal and needs no import.

Both are cheap: every consumer reaches these through `self.`, so the move is the member's text, its
row in the two indexes, and the name migrating between the two mixins' surface frozensets.

## DONE (feature 118): `rolling.py::roll_village` - and the measurement worth keeping

**Closed 2026-08-17.** `roll_village` went 256 lines -> a 60-line orchestrator over seven `_roll_*`
stages, cut at the banner comments it already carried, inside the new `settlement/rolling/` package.
The largest function in the engine is now `_bundle_geom` at 81 lines, so nothing is over the
~150-line bar features 112/115 converged on and there is no standing clause-12 candidate. Method and
oracle: `specs/118-rolling-package/`.

The two pre-flight checks this entry used to prescribe were both run, and **one of them overturned
the prediction written here** - which is the whole argument for measuring rather than reasoning, so
both results are kept:

- **The RNG surface, MEASURED: `roll_village` draws NOTHING from the main stream.** All four
  generators it builds are seeded from `self.seed` (`knob_rng` for the water source, `self.seed ^
  0x1A7D` for the land-use overlay, `self.seed * 2654435761` for the cluster seeds,
  `self.seed * 977 + 13` for the torii count) and its knobs go through `scope_seed`. Every
  main-stream draw happens inside a callee, so **the sequence of those calls IS the output**, and any
  stage split preserving the sequence preserves every byte. This entry had predicted the opposite
  ("a *seeding* routine, so its draw density is likely much higher and the answer may well go the
  other way"). It is a fact about the ENGINE rather than about the refactor, so it now lives in
  `settlement/rolling/CLAUDE.md`, where the next session to move a stage boundary will find it.
- **Closures, MEASURED: exactly one** - `to_screen`, over six frame values, against
  `_stable_yard`'s eight-over-a-shared-lattice. It became the frozen `_MarginFrame` dataclass.

**The transferable rule, now that this is the second data point.** The two checks cost about five
minutes between them and each time they changed the plan: 115's had to be amended mid-flight for
skipping one, and 118 was safe to attempt only because it ran both first. Run them before
decomposing any engine function - and write the ANSWER somewhere the CODE lives, not only in the
spec, because the next session reads the module, not the feature directory.

## `wip/shiro-daika.gen.py`'s cost is UNKNOWN and unbounded

Feature 112 recorded it as "over 6 minutes"; feature 115 discovered that figure is an **aborted
lower bound** - 112 stopped the map at six minutes without output and never learned the real number.
115 got it to **10m35s of CPU at 100%, still with no output**, and stopped it for the same reason.
Nobody has ever let this map finish.

That matters beyond curiosity: `precinct_interior`'s only consumer in the entire tree is this map,
so any future refactor touching it has no artifact-level oracle available at a known price. Two
follow-ups, either of which closes it:

- Run it to completion once, unattended, and record the actual cost here.
- Profile it. A capital map costing more than 3x the entire 28-map pool is itself a finding - the
  "one performance bug this engine keeps growing" section of `CLAUDE.md` describes the shape it is
  most likely to be.
