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
