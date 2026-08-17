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

## DONE 2026-08-17: cohort seed 2's four drainage failures - ONE defect, and the ledger's sketch was right

Filed 2026-08-16 (fan-toe pond session) as four failures on `--batch 1 --seed 2` -
`drainage_discharges_downhill`, `drainage_junction_smooth`, `features_do_not_overlap`,
`watercourses_flow_downstream` - with the guess that they were "ONE routing defect, not four". They
were, and the landing site named in the sketch (`hamletgen/sink.py::stage_sink`'s offmap bearing
search) was the right one. Two things the sketch did not predict:

**Seed 2 had stopped failing before anyone picked it up, and that proved nothing.** Commit 411b9d7
(the comb net at TRUE SIZE) moved the fan geometry, and seed 2 went green at HEAD - the marginal-seed
ROTATION this file warns about, arriving on the one seed a ledger entry was watching. The defect was
untouched. It only reproduces at `a43c955` (the last commit before the true-size change), which is
where it was diagnosed and where the fix was verified: **4 failures there, 0 with the two changes
below, nothing else altered.** A ledgered seed that quietly goes green is NOT evidence the entry is
closed - re-check at the commit the entry was filed against.

**The root cause is a measurement mismatch, not a scoring gap.** The placer read the drain
collector's heading off its FINAL VERTEX PAIR; `drainage_junction_smooth` reads the same corner over
a 40 px chord (`_flow_dir(span=40.0)`). A comb's collector ends in a hook a couple of px long, so on
seed 2 the two definitions of "the direction this ditch is running" disagreed by **76.1 deg**
(last-pair 347.1, span 63.3). Consequences, both from that one number:

- The route continuing straight along the collector scored a PERFECT junction (turn 0.0) by the
  placer and a 76.1 deg kink by the gate - so the search elected it. It ran **1,100 px uphill**,
  147.9 deg off the fall, back across the dry plots it had already passed. That is three of the four
  failures; `features_do_not_overlap` was the symptom of the other two.
- The genuinely smooth route (2.2 deg by the gate, descending 680 px, 5.7 deg off the fall) was the
  very FIRST candidate tried, and was refused for a 73.9 deg turn it does not have.

**The two changes** (`hamletgen/sink.py`), both "adjudicate against the gate, never a re-statement of
it" in its cheap form:

1. `drain_heading` measures over `GATE_FLOW_SPAN` (40 px), mirroring `_flow_dir`, so the placer
   optimizes the number the gate computes. Held by
   `test_the_drain_heading_is_read_over_the_gates_span_not_the_final_vertex_pair` (fails on the old
   last-pair code: -63.4 deg against the span's -5.4).
2. The `bad` score gained the two terms nothing else covered - net descent along the fall, and
   divergence of the net upstream->downstream bearing from the map's flow, mirroring
   `drainage_discharges_downhill` and `watercourses_flow_downstream`. **Downhill was never scored at
   all**, and it is reachable precisely because candidate bearings are tried around the DRAIN'S OWN
   HEADING as well as the fall: a collector runs cross-slope by design (`drain_runs_cross_slope`), so
   "continue along the collector" can sit 90+ deg off the fall before any swing is added. Defense in
   depth for the class, not just for this instance - (1) alone fixes seed 2.

Measured on seed 2 at `a43c955`: 28 of 72 candidates satisfy all three gate predicates, so the search
had plenty of legal routes and was simply scoring them against the wrong corner.

**The least-bad fallback (`best`) was NOT taken** - the ledger's other hypothesis. Its
`# pragma: no cover` is still accurate: seed 2 found a bad==0 candidate, it was just the wrong one.

**Why this was worth doing BEFORE the village tier**, since that is what it was queued behind.
`stage_sink` is tier-agnostic and a village drains a bigger, differently-shaped fan through the same
offmap branch, so it meets this more often, not less. More to the point, the cohort baseline is the
instrument every village-tier change will be judged with, and a baseline carrying an undiagnosed
four-check failure cannot tell a regression from the weather.

**Measured, baseline first, in a detached worktree at the same HEAD (Principle XIII):**

| | `--batch 48` | `--batch 24` (pinned) | live pool maps |
|---|---|---|---|
| unmodified HEAD | 45/48, seeds 22, 24, 26 | 22/24 | - |
| with the fix | 45/48, **same three seeds** | 22/24, `NO NEW REGRESSIONS` | kashikawa + sawada **byte-identical** |

The only two LIVE maps that drain offmap are kashikawa and sawada, and both regenerate byte-for-byte
unchanged - their collectors' final segments already agreed with the 40 px chord - so **no ink moved
in the pool and no `settlement-review` is owed**. Within the cohort, 6 of the 28 offmap brooks (seeds
19, 27, 37, 38, 39, 42) took a different route, with every one of the 48 verdicts unchanged.

**Honest scope of the verification.** At current HEAD the defect fires on NO seed in 1-48 - every
brook already descended (min +134.4 px) and stayed within 72.6 deg of the flow - which is the same
rotation that took seed 2 green. So the cohort proves the fix costs nothing; what proves it WORKS is
`a43c955`, the commit where the defect reproduces: 4 failures before, 0 after, no other change. The
frozen fixture `pool/regressions/drainage_discharges_downhill_fires_on_cohort_seed_2s_uphill_brook.json`
is that manifest, and it still fires all four names under the current battery.

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

### DECIDED 2026-08-17: `plot_rings` STAYS a paint-order stack - documented, with a lap ceiling

On Inashiro 39 ring pairs lap, double-counting **0.10 acre** of the recorded fabric (worst: a
21.3 x 41 ft slab between #471 and #529). This is invisible in ink and correctly so - each plot is
one `<polygon>` carrying fill AND stroke, emitted in index order, so the later basin paints out the
bund it covers and the pair reads as the single shared wall it should be. `paddy_plot_seams_shared`
therefore judges near-CONTAINMENT rather than depth, deliberately (its comment carries the
reasoning, and the fixed map's deepest legal lap covers 41% of a ring).

**The GM chose to ACCEPT the limitation and document it** (2026-08-17, on being shown the three
options priced below). What shipped:

- **The contract is written where the record is** - `settlement/fields/comb.py::_comb_record_field`,
  at the `plot_rings` key itself: this is a paint-order stack, dissolve (later ring wins) before
  computing acreage, per-field yield or basin-to-basin adjacency. *(Note for anyone following the
  old sketch below: the record is assembled in `_comb_record_field`, NOT `_comb_draw_paddies`,
  which only paints.)*
- **A ceiling keeps the note true** - `paddy_plot_rings_overcount_stays_marginal` (segment 0605)
  fires when the pairwise lap passes **4.0%** of the recorded fabric. Measured over the four
  scripted hamlets and a 48-seed cohort: 0.53 / 0.54 / 0.79 / 1.06% on the pool, cohort median
  ~0.9%, tail 1.49 / 1.51 / 1.57 / 2.49%. The measurement is a deliberate UPPER bound (each pair
  clipped against the neighbour's convex hull, every pair summed), so a pass is a real verdict.

**What it costs, observably:** anyone summing `plot_rings` areas without dissolving over-counts by
up to 4% (up to 2.5% on anything shipped today), and ring adjacency does not imply visible
adjacency. Nothing in the gate measures acreage off these rings today, so the cost is latent until
the first rule that does.

**The two declined alternatives, so this is not reopened from scratch:**

- **TRIM each ring to its visible extent at record time** (making the manifest a true partition).
  Declined on two costs, neither of which was visible when the option was written: half the
  record's current consumers want the STACK - `bund_beans_on_bunds` is built on burial (a bead is
  legal iff no ring painted later buries it), and `paddy_plot_seams_shared`, the supply-bank bund
  rule, `field_ponds_sunk_into_one_plot` and `comb_supply_commands_both_flanks` all read the drawn
  vertices - so the trim is a re-derivation of a check with its own GM-caught defect history, not a
  three-line change. And the holding check it needs (ring area sum equals union area) requires
  polygon booleans: shapely is an ENGINE dependency (`waterfields/seams.py`) and `check_village` is
  hand-rolled geometry throughout, so this would put a new dependency on the gate's path.
- **Record BOTH** (keep `plot_rings`, add a derived visible-extent key). Declined on size:
  `plot_rings` is already 25-40% of a hamlet manifest (Inashiro 53 KB of 206; Kashikawa 69 KB of
  242), so a parallel copy adds that again for a partition nothing reads yet.

**And one thing the ceiling deliberately does NOT do:** fire on the pre-`close_seams` Inashiro
frozen in `pool/regressions/`. That manifest scores 2.58% against a live worst of 2.49% - the
populations overlap, so a map-wide lap fraction cannot separate that defect from ordinary fabric,
and a ceiling tuned to catch it would fail a cohort seed that passes today. `paddy_plot_seams_shared`
is the rule that discriminates it. The new rule's teeth are therefore a synthetic break in
`tests/check_village/test_segments_08_town_and_fire.py`, not a frozen fixture.

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

### STILL OPEN after the 2026-08-17 well tie-break: cohort seed 62's northern lobe

`hamletgen.place_wells` now prefers a seat INSIDE the house cloud over one in the sweep box's 120 px
pad when the two tie on the minimax-need bucket (see the comment at the sort - it exists because
cohort seed 41 seated a well 76 px north of the household it served and held the whole frame open).
Two things that fix did NOT do, both measured rather than assumed:

- **The four shipped hamlets are byte-identical across it.** Their wells were already interior
  seats, so the guard is inert on every map in the pool - which is why the change shipped with no
  `settlement-review` pass: no map's ink moved.
- **Seed 62 still fails `crop_not_held_open_by_one_feature`** with the same message it failed with at
  baseline (`wells[1] stands 65px past the next feature`, 24-seed window from 41: 20/24 before, 20/24
  after). Its well[1] at (2215, 594) is genuinely outside the cloud (which starts at y=670) and there
  is **no interior seat in its minimax bucket** - the northern lobe is served from the pad or not at
  all. So the tie-break cannot reach it: this is the "nothing inside serves these households" case,
  and a tie-break by construction only decides ties.

**What would actually close it**, when someone takes the northern-lobe case on: make the objective
itself frame-aware rather than only the tie-break - score a seat by `_worst_after` PLUS the crop
extent it would add, so a pad seat has to buy enough coverage to pay for the frame it drags out. That
is a change to the objective three settlement-reviews have already shaped, so it wants its own pass
and a per-map review. Until then seed 62 is a pre-existing ledgered failure, not a regression, and it
is the reason the cohort rate is 45/48 rather than 46/48.

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
`python3 -m l7r.diagram.hamletgen --batch 1 --seed 9`. Instrument `close_seams`'s bare-ground pass to dump the
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
- **`pasture` -> `land/cover.py`.** It is a land surface, and `cover.py` already holds the commons
  and the hinterland layout (marsh and the toe band sit next door in `land/wet.py`). Same module
  today. Destination updated by feature 120, which split `land.py` into a package; the move itself
  was explicitly left out of that feature's scope, because a cross-package relocation does not
  belong in a split whose whole safety argument is that nothing moves but text.
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

## The gate's 15 over-150-line segment functions (found by feature 122, deliberately NOT fixed there)

This file records "the largest function in the engine is now `_bundle_geom` at 81 lines, so nothing
is over the ~150-line bar features 112/115 converged on and there is no standing clause-12
candidate". That is true, and it is scoped to the ENGINE. **The GATE was never measured**, and it
has fifteen segment functions over the bar:

| lines | segment | file |
|---|---|---|
| 293 | `_seg_0555_007__execution_ground_outside_the_settlement` | `segments_09a_justice_grounds_and_land_fall.py` |
| 273 | `_seg_0324__field_ditches_terminate` | `segments_05c_streams_and_field_ditches.py` |
| 255 | `_seg_0581__polder_dike_is_earthwork` | `segments_11b_polder_dikes_and_waivers.py` |
| 248 | `_seg_0571__torii_count_canonical` | `segments_11a_taxfree_terraces_and_dikeponds.py` |
| 228 | `_seg_0580__dikepond_is_ponds_in_a_block` | `segments_11a_taxfree_terraces_and_dikeponds.py` |
| 227 | `_seg_0563_072__city_neighborhoods_have_wells` | `segments_10b_city_civic_and_commerce.py` |
| 221 | `_seg_0556__walled_town_has_wall` | `segments_09a_justice_grounds_and_land_fall.py` |
| 208 | `_seg_0033__hard_features_within_frame` | `segments_01a_city_ring_and_frame.py` |
| 199 | `_seg_0104__city_wall_tower_coverage` | `segments_02a_capital_budget_and_ministries.py` |
| 196 | `_seg_0563_325__city_moat_feeder_matches_width` | `segments_10g_city_streets_and_docks.py` |
| 195 | `_seg_0275__labels_clear_of_other_buildings` | `segments_04a_margins_lanes_and_wells.py` |
| 185 | `_seg_0603__paddy_plot_seams_shared` | `segments_08d_kosatsuba_and_paddy_basins.py` |
| 183 | `_seg_0127__city_fan_heads_quilted` | `segments_02c_walls_gates_and_housing.py` |
| 153 | `_seg_0563_335__city_streets_connected` | `segments_10h_city_torii_and_estate_grounds.py` |
| 151 | `_seg_0108__merchant_estate_wall_clear_of_water` | `segments_02b_capital_ways_and_burial.py` |

**Why 122 left them, which is the part worth keeping.** 122's whole safety argument is that it moved
whole functions and changed no character inside one - which let it prove itself with a byte-identity
oracle over 24,354 content lines plus an identical 1,377-row `GATE_SEGMENTS`. Decomposing a check
BODY is the opposite kind of edit: it changes text inside a function, so neither oracle can hold it,
and folding the two together would have meant a 24,000-line diff whose correctness rested on reading
rather than on a check. Doing them in one feature would have bought nothing and cost the proof.

**The bar these should be measured against is NOT the engine's.** A segment is a check, and a check
that is long because it walks a lot of geometry to reach one verdict is not the same defect as a
draw method doing eight things. Before decomposing any of these, ask which it is:
`_seg_0571__torii_count_canonical` at 248 lines is likely one long enumeration (the numerology has
cases), while `_seg_0555_007__execution_ground_outside_the_settlement` at 293 is the check with six
interacting rules that `dev/diagnostics.md` describes needing `site_justice.py` to adjudicate, and
that one probably does decompose into named predicates.

**Pre-flight, both cheap, both mandated by the 115/118 lesson** (recorded in `dev/pool.md`, where
each of them changed the plan once): measure the RNG surface - free here, since a check draws
nothing - and count the closures. Then decompose behind the same registry contract, with one trap
worth stating out loud: the numeric key in the NAME is the execution position, so a helper extracted
out of a segment must NOT be named `_seg_*`, or the registry will try to run it as a segment.

## DONE 2026-08-17 (same day): two farmhouses could MERGE - now ruled and gated

Feature 121 made the placer test the raked quad it draws against the lane TREAD, and made
`houses_clear_of_lanes` read the same corners. **House-to-house separation was not touched**, and it
is still adjudicated on the whole-bundle BBOX (`_bundle_side_fits`), which knows nothing about
either house's rake.

Caught by `settlement-review` on Mizuguchi: the pair at (829.4, 1682.7) and (771.5, 1693.6) had
their raked-corner gap fall **3.6 -> 2.0 ft** when the re-pack flipped one house's rake from -4.0 to
+4.4 deg, so the two now diverge instead of running parallel. At 1 px = 1 ft that is two pixels
between two dark roof strokes - at fit zoom they merge and read as ONE long building. Two feet
between thatched eaves is not a thing a hamlet does.

**It is a lone outlier, which makes it cheap.** Minimum raked-corner house-to-house gap across the
four scripted hamlets: Inashiro 28.8, Kashikawa 25.5, Sawada 23.0, **Mizuguchi 1.96**. A rule with
15+ ft of headroom catches it and disturbs nothing else.

**Not a regression, deliberately not folded into 121**: no check fires (there is no house-to-house
gap rule at all), and the cohort is 22/24 before and after with the same two seeds. It is a NEW
rule, and 121 was already carrying three fixes.

**Sketch (check before fix).** Add a gap verdict over `M["houses"]` pairs using the existing
`within_edge_gap(a, b, N)` - it already measures real footprints, and `farm_sheds_attached` is the
model to copy. Confirm it fires on Mizuguchi and on nothing else in the pool. Then require the same
clearance in `_bundle_common_fits` against every placed house's raked quad: `_sun_corridor_ok`
already reads neighbours' geometry off `M["houses"]` during placement, so both the precedent and the
plumbing exist. Ground the number in **"two thatched roofs must shed separately"** - the principle
[`research/buildings.md`](research/buildings.md) already records for a building standing against a
compound wall - plus the drawn-scale fact that two strokes 2 px apart merge to the eye.

### The density that is actually available, and it is not the pitch

Recorded here because feature 121 declined the obvious move and the reasoning should not be lost.
`BUNDLE_PITCH` is **not** padding to be recovered: it is set by the threshing yard's sun (45-degree
*kayabuki* thatch, ~20 ft ridge, 39 ft of shadow at 9am at 38N in the 10th month). Lowering it puts
houses in each other's drying shadow. The honest way to pack a nucleus tighter is what real
*yashiki* lots did - **STAGGER the rows east-west** rather than space them further apart, which
costs no sunlight at all. The placer is free to; nothing asks it to yet. That belongs to the village
tier's own work. (`research/homesteads.md` "The threshing yard's sun";
`specs/121-placer-drawn-footprint/research.md` D2.)

## RULED 2026-08-17 (same day): Kashikawa's hamlet-of-one

Raised by `settlement-review`, **not caused by** feature 121 (the house is byte-identical across the
re-pack). The farmstead at (1352.4, 3062.7) stands **469 ft** from its nearest neighbour - the
next-most-isolated house is 128 ft - and **385 ft from any lane, with no way reaching it at all**, on
a map that declares `meta.nucleated: true`. It is coherent in itself (50 ft from the stream, its own
byre).

What makes it worth a ruling rather than a shrug: the re-pack moved the other 19 houses a median of
362 ft and left this one exactly where it was, so the placer had every opportunity to fold it into
the nucleus and did not. **Needs one line either way** - an outlying holding by intent, or a seeding
gap - because an undocumented oddity is indistinguishable from a bug next session.

### How both of the above were closed (2026-08-17)

**The merge: a rule now exists, and it was never a one-off.** `farmhouses_shed_separately` measures
the true gap between two raked farmhouse footprints (`within_edge_gap`, the gap-verdict helper) and
fires below **8 ft** wall to wall - two drip lines plus a footpath, grounded in the same "two roofs
shed separately" principle `research/buildings.md` records for a building against a compound wall.
The constant lives ONCE, in `_geom/village.py`, and both the placer and the gate read it.

The check was written FIRST and confirmed red on the shipped Mizuguchi and green on the other three
maps. Then the placer got the matching rule (`_house_too_near_a_neighbor`, stricter by 2 ft - the
`_sun_corridor_ok` convention). The pre-rule Mizuguchi manifest is frozen in `pool/regressions/`, so
this is pinned by a whole real map rather than only by a synthetic pair.

**The measurement that justifies the rule existing at all**: across the 24-seed cohort, before the
fix, there were **11 farmhouse pairs under 8 ft** on eight different seeds, the worst at **1.35 ft**.
The review caught one instance; the check revealed it was systemic and invisible - `no_structure_overlaps`
only fires at zero, and bundles are spaced by their whole-bundle BBOX, which knows nothing about
either house's rake. Cohort after: 24/24 with the new rule live.

**The hamlet-of-one: half fixed itself, half accepted.** The front-row density fix pulled the
cluster toward the paddy and Kashikawa's outlier went from 469 ft to **170 ft** from its nearest
neighbour - ordinary outer-edge spacing - without the house moving at all. Its remaining 385 ft from
any lane is ACCEPTED: a lane may not run through the flooded paddy, and field workers reach that
ground along the bunds, so an edge farmstead is reached the way the fields are. Declined: folding it
into the nucleus, drawing it a spur lane across the crop, and a "every farmhouse within N ft of a
way" check that would fire on this legitimate case and nothing else. Full ruling in
`pool/hamlets/kashikawa.notes.md`.
## OPEN: two `s.kiln` glyph defects (settlement-review on Ubame, 2026-08-17)

Both found on Ubame's new potters' kiln works and both deliberately NOT fixed there: they are
defects in `settlement/trades.py::kiln`, not in that map, and a shared-glyph change made under a
one-off content edit lands on Tango, Minami, Nagahara and `wip/shiro-daika` as well. The three
pool cities are frozen and would keep their committed ink either way, which is exactly why the
fix wants its own pass with its own sweep rather than riding along.

1. **The smoke wisp ignores the map's declared wind.** The plume is authored in the glyph's LOCAL
   frame (`q 2 -3.5 0.5 -7`, toward local -y), so it rotates with the kiln. On Ubame, at
   `rot=351.9`, that puts it at world bearing NNW - blowing INTO the declared `windward="NW"`, and
   pointing at the magistrate's manor. The SITING is right (the works is downwind of every
   dwelling) and only the ink contradicts it, which is the worst version: a reader who trusts the
   drawing reads the nuisance axis backwards. **Fix sketch**: derive the wisp's bearing from
   `meta["windward"]` in world coordinates and counter-rotate it out of the glyph's group, the way
   `_trade_record`'s `lab_off` already counter-rotates a caption. Then the plume becomes free
   evidence for the reader instead of a contradiction. Every settlement that draws smoke has the
   same latent bug; the kiln is just where a map finally rotated far enough to expose it.
2. **The two-cottage case is mirrored, with the well centered above it.** `cxs_ = {2: (-f(22),
   f(22))}` puts the pair symmetrically about the works' axis, and the private well's saturated
   blue disc sits centered above them - a bright centered mark over a symmetric pair, which is the
   composition the mirror rule warns about. It does not resolve into a face (one disc, not two),
   but at fit zoom the well becomes the loudest thing in the works and the eye lands on its least
   important object. **Fix sketch**: offset the 2-cottage case the way the 3-cottage case already
   is asymmetric in effect, or move the private well off the axis. Cheap, but it changes every
   two-cottage works, so it belongs with item 1 in one pass.

## OPEN, all PRE-EXISTING: three found by the 2026-08-17 review round

None of these came from that day's changes - each was verified byte-identical to the prior roll -
and each is a form defect the gate structurally cannot see. Logged rather than fixed in-flight,
because widening scope mid-fix is exactly what produced the cluster-flattening regression that same
day: the density fix was landed on a `field_ringed` count, which is monotone in "more front row" and
could never push back, and it took three reviews to notice the cluster had become a ribbon.

### 1. RETRACTED - the flooded tint census does NOT reproduce; keep only the test sketch

Rendering exactly `#93B7AC`, the PNG carries **three** substantial regions plus fragments;
`M["flooded_plots"]` records **two**, and neither recorded centroid matches the third painted bbox
(675-722 x 2329-2362 does not overlap either in y). Only two SVG elements carry that fill under a
straightforward parse, so the third comes from a path form the decomposition does not reach.

Why it matters more than a count: `flooded_plots_read_as_basins` adjudicates the RECORDED set, so a
basin painted outside it is invisible to the rule - and **all three painted wedges taper to a
point**, which is the composition `research/fields.md` names in "A basin never tapers to a point".
On the one map briefed as pond-free, the sharpest of them reads at zoom as a small triangular pond
at a ditch mouth.

**Sketch**: make the census a TEST - count painted `#93B7AC` regions in the SVG and assert equality
with `len(flooded_plots)` - then apply `_TINT_END_FT` at whichever emitter paints the unrecorded
ones, not only at the one `flooded_plots` records. The 2026-08-16 entry established "4 painted, 4
recorded, 1:1" as the guard by hand; this makes it a check.

### 2. A lane dead-ends 90 ft past its own junction (Sawada)

Lane 2's end lies 0.3 ft off lane 0's centerline - a clean T - and then lane 0 continues **81 ft
past that node** to a free end 12.6 ft to the side of lane 2, on a bearing ~9 degrees off it. On the
sheet that is two near-parallel tracks with a hairline sliver between them, ending in a blunt cap in
open ground that serves no house, reaches no field and connects to nothing. Both arms are legal ways
with legal clearances, so nothing fires.

**Sketch**: require a dangling lane end to terminate ON something - a homestead frontage, the field
edge, or another way - and trim the overshoot at the junction. `connector_lane_runs_off_edge`
already makes exactly this kind of "must end somewhere" demand for the connector; this is its
internal-lane counterpart.

### 3. NOT REPRODUCED as written - the "adaptive" garden side needs re-measuring

`bundle.py` promises the nucleated garden goes on "an ADAPTIVE sunny side (chosen by the placer for
fit + no shading), so it packs into a real nucleus and the gardens VARY instead of all sitting east
between houses." Measured on Sawada: **21 of 23 beds SE, 2 SW, 0 E, 0 W**. The adaptive choice is
choosing the same side nearly every time, so every homestead reads as one stamp repeated - house,
yard directly below, bed to the lower-right.

Note this is the finding that a WRONG one was hiding: an earlier review reported "18 of 19 on the E
wall, the last-resort candidate", that claim went into `sawada.notes.md` unverified, and a later
review reconstructed each bed's candidate signature and refuted it (zero beds took the E-wall
candidate; `groves = 0` is the documented nucleated-bundle behavior, not a symptom). A review
finding is evidence, not a verdict.

**Sketch**: decide first whether the variation is meant to be real or the comment is aspirational -
that is a GM-facing question, not a code one. If real, the shading/fit score is presumably
near-constant across sides for a compact bundle, so it wants a tie-break that varies (the
position-seeded `_hjit` idiom) rather than a strict preference order.

## OPEN: three more from the 2026-08-17 re-review round

### 4. `scatter_audit` reports `crown=0` on a map recording 2,665 crowns

Caught on Kashikawa: the audit parsed `blade=312447 dot=17240 pine=1517 crown=0 reed=72420` and
exited 0, on a map whose manifest carries 2,665 tree crowns. Its exit-2 guard fires only on a ZERO
TOTAL, so **one blind family looks exactly like a clean family** - the "a check that never runs looks
exactly like a check that passes" shape, one level down inside a tool that is itself used as
evidence. Every review that has quoted "scatter_audit: crown checked, 0 violations" on a hamlet may
have been quoting a family the parser never saw.

**Sketch**: find out whether the village-grove crown emission still matches the parser's styling
(the belt and copse crowns are emitted differently from woodland-stand crowns, which is the likely
cause), then make a family that parses ZERO bases on a map that RECORDS that feature a failure, not
a silence. Per-family, not just per-total.

### 5. The shared byres end-load onto one flank of the cluster

Kashikawa's four shared draft-animal byres sit at cluster-axis positions -442, -430, -340, -300 in a
settlement spanning -478..+516 - all four inside the SW 143 ft of 994 ft, leaving fifteen of twenty
households 400-900 ft from the nearest one. `settlements/homesteads.md` makes these SHARED sheds
precisely so a poorer neighbor can borrow or hire a team, so end-loading them defeats the sharing
the feature exists to depict. Pre-existing (the previous roll had them at -799..-492, one past the
westernmost house), but the tighter cluster makes it obvious.

**Mechanism**: the placer walks homesteads in seat order and takes the first clear gap, so byres
drain toward whichever end still has open verge. **Sketch**: spread the seats over the cluster's
principal axis before spiraling, the way the well siting already does its minimax.

### 6. The kura flag is stable against regeneration but NOT against re-packing

`homesteads.md` says the position-seeded kura roll (`_hjit(x, y, 3.0) < 0.30`) makes the flag
"stable across regenerations". Measured, the hash itself is honest - 0.2993 over 200k realistic
coordinates, and the live pool sits at 343/1208 = 28.4% against the 30% knob. But a placer that
RE-SEATS a house re-rolls that house's kura, so a re-pack redistributes wealth wholesale
(Kashikawa 25% -> 15% in one roll, a -1.5 sigma 20-draw sample, not a bug).

Not a defect and not worth a check - but the doc's claim is wrong as written, and someone will one
day chase a "disappearing kura" because of it. **Sketch**: one clause in `homesteads.md`, or key the
roll on something the placer does not move (a household index) if stability is actually wanted.

### Corrections to items 1 and 3 above (2026-08-17, same day)

Both were logged from measurements that do not survive re-measurement, and saying so is the point -
a logged defect that does not exist costs a future session exactly as much as an unlogged one that
does, and this file's own retraction of the E-wall garden claim two entries up is the same lesson.

**Item 1 does NOT reproduce.** The three-painted-versus-two-recorded census was taken on a STALE
PNG - the render that had drifted from its own SVG. Re-taken on fresh ink: **2 painted regions, 2
recorded, 1:1**, at svg-coords x55-126 y2558-2626 and x699-786 y2264-2283, matching the recorded
centroids (84.4, 2607.2) and (754.5, 2267.6) exactly. The current SVG contains exactly two `#93B7AC`
elements. The "third region" and "a path form the decomposition does not reach" existed only in the
stale image. **What is still worth doing is the SKETCH, not the defect**: a test that counts painted
`#93B7AC` regions and asserts equality with `len(flooded_plots)` would have caught the staleness
itself, which is a better reason to write it than the one it was logged under.

**Item 3 does not reproduce AS WRITTEN.** "21 of 23 beds SE" was measured on the pre-cap roll; the
front-row cap moved 19 of 19 houses and re-rolled `_garden_beds`' position hash. Measured on the
shipped roll the spread is roughly **8 SE / 7 E / 7 W of 22 beds** - which is variation, not a
monoculture. The re-measurement was taken in the reviewer's own frame rather than
`_find_garden_spot`'s `sides` convention, so it is not authoritative either. **Re-measure in the
placer's own frame before acting**, and do not quote either number as established.

The general rule both of these earn: **a review finding measured on an artifact is only as current
as that artifact.** Two of this round's findings were taken on a stale render and one on a
superseded roll; all three read as solid until re-measured.

## OPEN: two more from the Sawada re-review (2026-08-17)

### 7. The title placard prints over a woodland commons parcel - and the keep-out is ONE-DIRECTIONAL

On Sawada, **71% of the 125 ft woodland commons at (912, 2012) lies inside the title+scalebar box**,
and 12 crown centers under it ghost through as pale circles inside the cartouche while 4-5 peek out
along its edge. Two failures at once: one of only two woodland commons on the sheet is two-thirds
invisible, so its "stocked" record is not what a reader sees, and the title itself reads as smudged.
Pre-existing in kind (57% before) but the re-pack made it worse by re-seating the parcel 90 px
further into the box.

**The mechanism is NOT the one it looks like, so do not apply the obvious fix.** `title_pocket` is
already the first entry in `open_ground_patches`' `keep_rects`, so the coppice scan does avoid the
reserved cartouche ground. But `title_pocket`'s own docstring says it is "a reservation, not a
placement: `title()` still does its own search and may well sit somewhere else" - and when it does,
it lands on ground the woodland was entitled to take. The keep-out runs one way only.

**Sketch**: the fix belongs at the TITLE's scan, not at the woodland placer - `_blank_label_spot`
must count woodland-commons crowns as an obstacle, the way it already counts the distinct wet
surfaces. Note the blast radius before starting: that scan sites the cartouche on every map, so this
is a change that can move titles pool-wide, and it wants its own before/after over the live maps.

### 8. `TWIN_AXES` believes a declared knob over the drawn shape

The cap pushed the surplus households into the cloud pass, so Sawada's `cluster_seeding` flipped
`frontage` -> `cloud` and `meta.cluster_shape: "round"` is now emitted for the first time. The drawn
cluster is **808 x 235 ft, 3.48:1**. That would be harmless bookkeeping except `check_village/driver.py`'s
`TWIN_AXES` reads *"the declared knob if present, else the cluster-bbox aspect"* - so the
twin-distinctness axis now reports **round** on the strength of a rolled knob, where before the cap
it fell through to the MEASUREMENT and would have said elongated.

This is the derive-don't-pin rule inverted: a declaration is being trusted over the geometry it is
supposed to describe, and the flip was a side effect of a placer change that never touched the twin
detector. **Sketch**: prefer the measurement when both exist (a knob says what was ASKED for, the
bbox says what was DRAWN, and the twin detector's question is about what a reader sees) - or make
the cloud record what it actually produced. Either way it wants a GM ruling on which the axis is
for, since it changes what "reads as its own place" is measured against.
