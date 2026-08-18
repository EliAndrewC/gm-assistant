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
  clipped against the neighbor's convex hull, every pair summed), so a pass is a real verdict.

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

### DONE 2026-08-17: the paddy size floor, and the well fix it had to wait behind

The GM's question - *"most of the rice paddy fields are rectangular, but then there are a few very
small triangles ... should there be a minimum rice paddy size?"* - produced `_TOE_MIN_AREA` (0.25 of
a comb fan's own design cell, gate at 0.20). Findings, both declined alternatives (an absolute
acreage floor; a four-sides rule) and the two derivations of 0.25: `research/fields.md`, "Minimum
basin SIZE". Two second-order defects the `settlement-review` pass caught became
`_WELD_MIN_SOLIDITY` / `_TINT_MIN_SOLIDITY`, the first guards in this engine to measure a SHAPE
rather than an apex.

**The process note worth keeping, because it is the transferable part.** The floor shifts the drawn
plot count, which rotates the shared placement stream, and on cohort seed 41 the rotated roll seated
a well outside the house cloud and tripped `crop_not_held_open_by_one_feature` - taking seeds 1-48
from 45/48 to 44/48. The paddy work was CORRECT and the failure was not a paddy defect at all: the
field geometry was byte-identical either way, and what moved was a well landing on a pre-existing
weakness in `place_wells`. Rather than waive the seed or fold a placement fix into a fabric feature,
the GM's call was to **take the well fix as its own piece of work first and land the floor on top** -
which is why `e0fb2417` (the well tie-break, byte-identical on every shipped map) precedes the floor
in history. The general lesson: when a fabric change trips a check in a different subsystem, measure
whether the geometry moved before assuming the change is at fault, and separate the commits.

### OPEN, each with its measurement: four things the 2026-08-18 review round raised and left

All four came from `settlement-review` on the paddy size floor and are NOT in that feature's scope;
each is here with the number that establishes it, per Principle XIV's deferral bar.

- **A tip-angle companion to the area floor.** The area rule cannot reach a dart: Mizuguchi's ring at
  (1021-1084, 968-1012) is 0.69 of a cell and reads as an arrowhead, and the sharpest interior angles
  on that sheet are 27.4 / 27.6 / 30.4 deg on basins of 0.55-0.72 cell. A minimum tip angle of
  ~25-30 deg would catch the family without re-imposing the grid the four-sides rule was declined
  for. **Not** the declined rule - a 5-sided basin with an 8 ft shortest side is fine.
- **DONE 2026-08-18: the woodland commons sat on an exact lattice - and two hamlets had no woodland
  at all.** Ledgered as two items; one measurement pass showed they were one defect wearing two
  faces, plus a second, worse one underneath.

  *The lattice.* Mizuguchi's three parcels were identical 250 x 250 ft squares at (456,967),
  (726,697), (996,427) - offsets of exactly (+270,-270) each - reading as three stamps of one wood
  marching up a ruled diagonal; Inashiro had the same chain at (+270,+270). Not a tendency but a
  construction: `open_ground_patches` samples a uniform 90 px lattice, scores every seat by ONE
  monotone function (near the cluster, leaning upslope) and takes the best remaining seat outside a
  FIXED separation radius, so each pick lands just past the previous one's exclusion circle in the
  direction the score rises. Fixed as sketched - the accepted seat is nudged up to half a step off
  the lattice and the parcel's size rolled +/-15%, both from `_hjit` (positional, so a map is
  unchanged by regeneration and two maps differ from each other), and every nudge is re-asked
  through the qualification predicate, so it can only move a legal seat to another legal seat.

  *The size roll must vary BOTH ways.* First cut rolled `1.0 - 0.2*hjit` - shrink only - which
  compounded with the existing shrink ladder and produced a 116 ft "commons" on Mizuguchi, a copse
  rather than a commons. `0.85 + 0.3*hjit` instead; growth is safe because the predicate re-asks.

  *What was underneath.* Kashikawa - the map NAMED 樫川, "oak river" - shipped **zero** woodland
  parcels, and had at HEAD too; Sawada one. Census over the scan lattice, every rung of the shrink
  ladder and both set-back profiles: Kashikawa **0 qualifying seats out of 231-286**, Sawada 1, with
  the crop clause alone refusing 93-97% and the best achievable clearance NEGATIVE (the square
  overlapped a paddy). So neither the shrink ladder nor the set-back relaxation - both added FOR
  Kashikawa, in two separate rounds - could ever have worked: the binding constraint was never the
  set-back. Two hypotheses tested and killed before the right one: that the scan's `crops` list
  reading `plan.envelope` diverged from the check's paddy outlines (it does not - seat counts match
  exactly, 16/16, 29/29, 35/35, 47/47 on Mizuguchi), and that the frame should give (it may not -
  `crop_to_content`'s docstring carries the GM's ruling that the frame stays tight to real content
  and commons clip like the marsh).

  The actual divergence: **the scan mirrored the check's formula but not its WINDOW.**
  `woodland_commons_within_the_frame` asks for 70% of the parcel's bbox inside the view and says in
  as many words that a parcel clipping at the edge "reads as 'more wood that way' and is fine"; the
  scan demanded the whole square inside the kept window plus a further 16 px. Being stricter than
  your own gate is not the safe direction - it cost two of four hamlets their woodland. The seat is
  now judged by AREA the way the check judges it (center may sit 0.6*half outside, exact bbox
  fraction >= 0.8 - the check's 0.7 plus slack, since this window is a PREDICTION of the crop). The
  exact fraction, not a per-axis box: two 0.4*half overhangs pass a box test at 0.64 inside and ship
  a check failure. **Kashikawa 0 -> 2 parcels, Sawada 1 -> 1** (Sawada's ground is genuinely that
  tight; its earlier 2 -> 1 loss is closed as "the land is committed", not re-opened), Inashiro and
  Mizuguchi 4 -> 4 at varied sizes and off the lattice. All four maps gate green.
- **DONE 2026-08-18: `byre_form` is a KNOB** (Principle XII's two-supportable-answers rule). Both
  forms are attested - the ox under the farmhouse roof in the wealthier magariya (曲家) /
  sanheyuan pattern, and a detached shed on common ground where a team is shared - and the engine
  had only the second, silently and everywhere. Registered in `_knobs.py` and rolled per settlement
  from the map's own seed; `draft_byres` branches on it. `courtyard` follows the WEALTH (owners
  straight down the wealth ranking, no minimax spread, no inter-byre separation, the spiral held to
  the owner's own yard); `detached_commons` follows the SHARING and is byte-identical to the old
  behavior, which is why it stays the default. Rolled results: Sawada `courtyard` (byres a tight
  50-51 ft from their owner), Inashiro and Kashikawa `detached_commons` (53-102 ft, unchanged) - a
  visible difference between two same-region hamlets, which is the point.

  **A second defect was found doing it and is fixed in the same work** (Principle XIV). The overlap
  registry's entry for `byres` read *"a draft-ox byre is an ANNEX abutting its own farmhouse
  (draft_byres places it against the wall)"* - a description of code that had not existed for a long
  time, since the placer spirals a DETACHED shed out past the homestead and spreads the set by
  minimax across the cluster. Nothing noticed because nothing measured it, and the stale comment is
  very likely why the form was never questioned in the first place. The entry now states the
  property that holds under EITHER form, and the form-specific geometry is gated rather than
  asserted in prose.

  Gated by `_seg_0609__byres_stand_in_their_declared_form`, two checks: `byre_form_declared` (a map
  that draws byres and names no form leaves the geometry half permanently skipped - the
  `if meta.get(...)` failure mode) and `courtyard_byres_annex_their_homestead`. The span the check
  measures is `courtyard_annex_span`, the SAME expression the placer's spiral uses, exported from
  `byres.py` so the two cannot drift. Teeth proven by sabotage rather than by coverage: the
  declaration stripped FIRES, a byre dragged 260 ft off FIRES (124 ft against a ~44 ft span), a 25 ft
  nudge correctly does NOT. Both frozen into `pool/regressions/`. `detached_commons` deliberately has
  no geometry check - "the shed is on the shared ground" is not a claim about any one homestead, so
  mislabeling a courtyard map as detached passes, and that is recorded at the check rather than left
  to be discovered.

### RESOLVED 2026-08-18 (was BLOCKING): cohort seed 5's drain, and the well tie-break's cost

Seed 5's unplanked drain resolved itself in the merge: a peer's front-row rank cap moved the houses
enough to reopen the plank seats. Recorded because the diagnosis still stands and the split it
describes is real - the CHECK's useful-ground verdict and the PLACER's are evaluated against
different spans (the placer uses the confluence-widened one), so the two can disagree again. One real
defect was found while chasing it and IS fixed: the obliqueness ceiling was measured against the
ditch's HEAD width, meaningless on a collector that starts as a thread and earns its section at the
outfall; it now measures against `max(w, w_tail)`, the same section `worth_planking` uses.

**DONE 2026-08-18, and the ledgered MEASUREMENT was wrong** - worth more than the fix. The entry
read: the tie-break traded a Sawada well from a seat with 11 households within 300 ft to one with 5,
worst walk 364 -> 493 ft, with the same shape on Inashiro. Both numbers counted **every** house.
`place_wells`'s objective deliberately does not: `settlement_dwellings_watered` treats a house within
~760 ft of a stream, channel or pond as watered, so those houses drop out of the minimax (the
GM-settled "no redundant well beside a living stream"), and the comment directly above the objective
warns in as many words against the objective and the check reading two definitions of "needs a well".
Re-measured with the check's own predicate: Sawada's 493 ft house is **308 ft from the stream**, 13
of its 19 houses are surface-watered, and the worst walk among houses that actually need a well is
**122 ft**. Inashiro the same shape - 430 ft house, 304 ft from water, worst NEEDY walk 180 ft. There
was no coverage defect on either map. Filed as a lesson: a metric that ignores a documented exclusion
will manufacture a defect, and this one survived a review round and a ledger entry before anyone
re-derived it.

The tie-break WAS nonetheless mis-ordered, and the sketch was also wrong. Distance to the cluster
CENTROID is a poor last key - on a two-lobed cluster the centroid is the empty ground between the
lobes, so it prefers the gap - but replacing it with distance to the nearest house (the sketch) is
the same mistake inverted: minimized by hugging one outlying farmhouse. Measured, that swap improved
Kashikawa (worst 386 -> 304 ft) and **worsened Mizuguchi** (203 -> 234 ft), which is a regression on
a shipped map, and left Sawada byte-identical - the tie-break was never what decided Sawada's wells.

The real arbitrariness was upstream: the primary key buckets `_worst_after + _extent_added` into 66 px
steps so the frame term can outrank small coverage differences, and INSIDE a bucket the ordering was
whatever the last key said. So the third key is now `_worst_after` itself - the actual objective, at
full resolution - with the neighborhood measure (distance to the `want_near`-th nearest house, the
rung's own "is this in a neighborhood" test) only breaking exact ties. The bucket keeps doing its job;
it simply no longer hands the choice inside it to a proxy. Measured across the four hamlets:
Kashikawa worst 386 -> 304 ft, Inashiro mean 212 -> 210 ft, Mizuguchi and Sawada byte-identical to
HEAD. **No map worse on any of the three metrics.**

### DONE 2026-08-17: `_outside_cloud` now tests the CROP's box, not a box of house centers

Filed the same day it was found and fixed the same day, once cohort seed 29 turned the predicted
flaw into a real failure. The tie-break asked whether a well seat lay inside the AABB of house
CENTERS, and settlement-review (Inashiro) named the hole before it bit: an AABB cannot tell "in the
settlement" from "in the box", so the ~345 px of grove and scrub BETWEEN a two-lobed cluster's lobes
scored as interior. Seed 29 then seated a well 64 px north of every other feature, inside the
centers' box, holding the whole frame open (`crop_not_held_open_by_one_feature`).

It now asks `s._crop_boxes(city=False)` - the source `crop_to_content` itself reads - so "outside the
settlement" means outside the box the crop will actually set, and it picks up the houses' DRAWN
extents plus their yards, gardens, sheds and byres instead of one point per house. The box can only
GROW after well placement (woodland and the pond come later), so the test errs in the safe direction.

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
already reads neighbors' geometry off `M["houses"]` during placement, so both the precedent and the
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
re-pack). The farmstead at (1352.4, 3062.7) stands **469 ft** from its nearest neighbor - the
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
neighbor - ordinary outer-edge spacing - without the house moving at all. Its remaining 385 ft from
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

## MOSTLY DONE 2026-08-18: three found by the 2026-08-17 review round (see the status on each)

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

### 2. DONE 2026-08-18 - a lane dead-ends 90 ft past its own junction (Sawada)

Lane 2's end lies 0.3 ft off lane 0's centerline - a clean T - and then lane 0 continues **81 ft
past that node** to a free end 12.6 ft to the side of lane 2, on a bearing ~9 degrees off it. On the
sheet that is two near-parallel tracks with a hairline sliver between them, ending in a blunt cap in
open ground that serves no house, reaches no field and connects to nothing. Both arms are legal ways
with legal clearances, so nothing fires.

**Sketch**: require a dangling lane end to terminate ON something - a homestead frontage, the field
edge, or another way - and trim the overshoot at the junction. `connector_lane_runs_off_edge`
already makes exactly this kind of "must end somewhere" demand for the connector; this is its
internal-lane counterpart.

### 3. RESOLVED BY MEASUREMENT 2026-08-18 - the "adaptive" garden side IS adapting

**It reproduces neither as first reported nor as re-reported, and the code's promise is being kept.**
`bundle.py` says the nucleated garden takes "an ADAPTIVE sunny side (chosen by the placer for fit +
no shading), so the gardens VARY instead of all sitting east between houses". Measured on the
shipped manifests, in the placer's own side vocabulary (`_NUC_SIDES = SE, SW, E, W`), counting each
bed by its offset from its own house:

| map | SE | SW | E | W |
|---|---|---|---|---|
| Inashiro | 2 | 11 | 1 | 4 |
| Kashikawa | 10 | 9 | 4 | 1 |
| Mizuguchi | 9 | 5 | 0 | 0 |
| Sawada | 8 | 0 | 7 | 7 |

All four sides appear, no map repeats one stamp, and the earlier "21 of 23 SE" and "18 of 19 E"
readings are both artifacts of measuring in a frame that was not the placer's. **No GM ruling is
wanted here after all** - the variation the comment promises is what the maps draw. Mizuguchi uses
only two sides, which is the one thing worth re-checking if the cluster ever tightens further.

THE LESSON, since this is the third time on this one item: a claim about WHICH candidate a placer
took has to be measured in the placer's own vocabulary, or it measures the measurer's frame.

### 4. DONE 2026-08-18 - `scatter_audit` reported `crown=0` on a map recording 2,665 crowns

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

### 5. DONE 2026-08-18 - the shared byres end-loaded onto one flank of the cluster

Kashikawa's four shared draft-animal byres sit at cluster-axis positions -442, -430, -340, -300 in a
settlement spanning -478..+516 - all four inside the SW 143 ft of 994 ft, leaving fifteen of twenty
households 400-900 ft from the nearest one. `settlements/homesteads.md` makes these SHARED sheds
precisely so a poorer neighbor can borrow or hire a team, so end-loading them defeats the sharing
the feature exists to depict. Pre-existing (the previous roll had them at -799..-492, one past the
westernmost house), but the tighter cluster makes it obvious.

**Mechanism**: the placer walks homesteads in seat order and takes the first clear gap, so byres
drain toward whichever end still has open verge. **Sketch**: spread the seats over the cluster's
principal axis before spiraling, the way the well siting already does its minimax.

### 6. DONE 2026-08-18 - the kura flag is stable against regeneration but NOT against re-packing

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

## ONE DONE, ONE OPEN: two more from the Sawada re-review (2026-08-17)

### 7. DONE 2026-08-18 - the title placard printed over a woodland commons parcel

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

## THE THREE QUESTIONS - ALL RESOLVED (2026-08-18)

These were collected as "rulings wanted" and put to the GM. **Two of the three should never have
been asked**, and the GM's answer changed how this project handles the whole category. The record of
what was asked, what came back, and why, is kept below because the resolution doctrine is worth more
than the three answers.

**What the GM ruled about the ASKING** (now constitution Principle XII, v1.9.0, and the root
`CLAUDE.md`):

1. **Research precedes a ruling.** A design question of this kind goes to historical research FIRST.
   The GM is to be asked only once a research pass has been made and come back inconclusive, and the
   ask must say what was searched, what was found, and why it is still unsettled. A and C were both
   answerable from the record and neither should have reached the GM's desk.
2. **Two supportable answers become a KNOB, not a choice.** Where research says a thing was done two
   ways, the generator does not pick one - it varies, per settlement, on a seeded knob. This is not a
   tie-breaking convenience; it is the point of the project. In the GM's words, the goal is
   settlements that are *"within historical norms while being as different from one another as is
   justifiable by our historical research, for the benefit of players who need to be able to look at
   different maps and distinguish them from one another at a glance."* Calibrated liberty still
   covers a DEGREE along a continuum; it no longer covers a choice between two distinct FORMS.

So the resolution ladder for anything of this shape, from now on: **research it -> if decisive,
implement the answer -> if two forms are supportable, add a knob -> only if the record is silent
does the GM rule.**

### A. RESOLVED BY RESEARCH - a byre belongs beside a wellhead. Nothing to change.

The research is not close, and it is recorded in full at
[`research/homesteads.md`](research/homesteads.md) "May a byre stand beside a wellhead?". The short
version: in the Japanese *magariya* the draft animal lives **under the farmhouse's own roof** (the
*umaya* stable wing takes the south face for the sunlight), and a house well sat in the rear corner
of the *doma* - i.e. animal and well inside one building. Chinese vernacular grouped the cattle shed
with the pigsty and the latrine, because both ends feed the manure economy; nothing in the
vernacular or geomantic material holds livestock away from drinking water, and public watering
troughs were sited AT wells wherever water infrastructure existed at all. A byre 38 ft from a
communal well is comfortably inside the norm; separating them would be drawing a modern sanitary
intuition. `_fits` already prevents the only thing that was ever a defect - an actual overlap with
the wellhead footprint. **No engine change. Not to be re-opened on the next re-pack.**

<details><summary>The question as it was originally posed (kept for the record)</summary>

#### A. Does a byre belong beside a wellhead? (Kashikawa)

The byre-owner spread put one draft-animal shed **38 ft** from a communal wellhead; the other three
stand 168-317 ft from any well. Nothing governs it: `settlements/homesteads.md` puts byres and wells
in the same interstitial courtyard ground, so the two meeting is structural rather than accidental,
and `_fits` already keeps the shed off the wellhead's own footprint - this can never become an
overlap, only an adjacency.

**The two readings**: (a) the beasts are watered at the well, so that is exactly where a byre goes -
which is the reading the reviewer and I would both take; (b) a wellhead is drinking water for the
settlement and wants a small apron clear of livestock. Either is defensible; what matters is that
one of them is written down, because the next re-pack produces the same adjacency and the next
session will otherwise re-open it from scratch.

</details>

### B. RULED BY THE GM - KEEP THE KNOB, and make the drawing match it.

This one WAS a real ruling: it is a question about what our own generator promises, not about
history, so no research pass could have settled it. **The GM keeps the declared knob as the twin
detector's axis**, with a reason that generalizes well past the twin detector:

> "When we ask for something, we want to get the thing that we asked for. And when we do not ask for
> something and the knob is set randomly, then we still want what is drawn to match what was randomly
> selected for the knob value."

Read that carefully, because it is *not* "the knob wins over the geometry" - it is **the knob and the
geometry must not be allowed to disagree**. A rolled `cluster_shape="round"` on a 3.48:1 band is a
BUG in the placer, and switching the detector to measure the bbox would have hidden it rather than
fixed it. The knob stays the axis precisely so that a disagreement stays visible, and it carries
distinctions (crescent / split / elongated) that a bbox aspect cannot express.

**The consequence, and it is an engine obligation:** whatever `cluster_shape` is rolled, the placer
must actually produce it. The immediate contradiction is closed (the declaration is recorded only
when the cloud shaped the cluster), but that is a mitigation - it makes the knob silent rather than
wrong. Honoring the rolled shape in the nucleated placer is live work; see the ledger below.

<details><summary>The question as it was originally posed (kept for the record)</summary>

#### B. Is the twin detector's cluster axis about what was ASKED for, or what was DRAWN?

`check_village/driver.py`'s `TWIN_AXES` reads *"the declared knob if present, else the cluster-bbox
aspect"*. So when a map records `meta.cluster_shape`, the twin-distinctness axis believes the ROLLED
KNOB over the geometry. That is the derive-don't-pin rule inverted, and it bit once already: a
placer change that never touched the twin detector made Sawada declare "round" while drawing a
3.48:1 band. The declaration is now only recorded when the cloud actually shaped the cluster, so the
immediate contradiction is closed - but the general preference stands, and nine pool maps declare a
shape.

**The ruling wanted**: prefer the MEASUREMENT when both exist (the twin detector asks "does this
read as its own place?", and a reader sees the drawing) - or keep the knob because it carries more
than a bbox aspect can (crescent / split / elongated are distinctions the measurement cannot make).
The second is a real argument, which is why this is a ruling and not a fix.

</details>

### C. RESOLVED BY RESEARCH - the back rank IS served, and the FORM of the service is a knob.

The research is recorded at [`research/homesteads.md`](research/homesteads.md) "Is every farmhouse
reached by a lane, and in what FORM?", and it split cleanly along the two axes the new ladder is
built for:

- **Decisive:** a house in a nucleated cluster is reached by a way. "Every house in the nucleated
  village is accessible via the interconnected system of narrow lanes and alleys" - compactness is
  what the lane network is FOR. So the current state (nine of Sawada's nineteen houses more than
  120 ft from any way, a whole SE block touched by nothing) is a **defect with a research basis**,
  not a defensible depiction, and the "people just walk" reading is retired.
- **Two supportable FORMS**, so per the GM's ruling this becomes a seeded knob rather than a pick:
  **(1) alleys off the spine** - narrow laterals between plots, colonised as semi-private space by
  the houses they pass; the accretive Chinese gridiron form. **(2) a back lane** - a way parallel to
  the main lane behind the plots, which typically doubles as the edge between village and fields;
  the planned form, with rear-access ground behind housing lots separately attested in traditional
  Manchu villages.

The two forms also read differently at a glance, which is the whole point: a back lane says the
place was laid out, alleys say it grew. That is exactly the kind of variance a player should be able
to see.

**IMPLEMENTED** as feature 123 (`specs/123-lane-web-and-cluster-shape/`), except item 4:

1. DONE - a `lane_web` knob rolls per settlement over the two forms and is recorded as
   `meta.lane_web`.
2. DONE - `stage_web` in `hamletgen/ways.py`, laid AFTER the homesteads are seated and derived from
   where they actually landed. **The after is load-bearing**: laid before them, as every other lane
   is, the web competed for ground with the very houses it existed to serve and grew the four pool
   clusters' long axes 15-97%. The whole sequence of dead ends is in that feature's `research.md`.
3. DONE - `farmhouses_reach_a_way`, the converse of `lanes_reach_something`, at a threshold derived
   from `BUNDLE_PITCH` rather than chosen. It was written first and proved red on all four pool
   manifests, which are frozen in `pool/regressions/` as its negative fixtures.
5. KNOWN AND LEDGERED - **four cohort seeds, all `shape=crescent`, still strand houses.** A
   crescent cluster wraps around the paddy and puts a few steadings on the far arm, ACROSS the
   field from the rest; probed directly, a footpath to them is blocked by the crop even with every
   yard, garden and grove removed from the obstacle list. The web is built in coordinates that
   follow the field margin, and those houses are not on it. Three fixes were tried and moved the
   numbers by zero feet (the distances were byte-identical across all three, which is the
   diagnostic). Not forced, because the honest reading is that it is item 4 wearing a different
   hat: a shape that strands houses across its own field is a PLACEMENT defect, and a lane rule
   bent to compensate for one is the exact bug the last two features were spent removing. Full
   record, including the alternatives priced and declined, in
   `specs/123-lane-web-and-cluster-shape/tasks.md`.
4. NOT DONE - B's obligation, that the placer honor the rolled `cluster_shape`, is untouched and
   wants its own feature. `stage_homesteads` still seats by rows and frontage and records
   `meta.cluster_seeding`, which says in writing that the rolled knob went unhonored. Note this is
   NOT a regression introduced here - it is the pre-existing state the GM's ruling B calls out.

<details><summary>The question as it was originally posed (kept for the record)</summary>

#### C. Does a hamlet's back rank get a way, or is it walked to? (doctrine, tier-wide)

Raised on Sawada, true of every scripted hamlet: nine of nineteen houses stand more than 120 ft from
any way, and the whole SE block is touched by no lane. Inashiro is 6 of 15 with a worst of 254 ft (345 ft when this was written; re-measured on the shipped manifest 2026-08-18),
Mizuguchi 4 of 12. This is not a defect of any one map and it is not delta-caused - the front-row
cap is what put a genuine back rank there in the first place, which is what we wanted.

**The ruling wanted**: either a hamlet's back block earns a spur (an engine change, and one that
would have to avoid the paddy the way the connector does), or a back rank is understood to be
reached along unfigured footpaths between the homesteads and nothing is drawn. The second is what
the maps currently depict, and it is defensible - a lane is a cart way, and people walk. Say which,
and `lanes_reach_something`'s house threshold stops being a number nobody has justified.

</details>

## OPEN, from the 2026-08-18 settlement-review round (four maps, four independent agents)

The round is worth its own heading because of what it caught: **every defect below and every one
fixed that day was invisible to a green gate and a 48-seed cohort at baseline.** The worst of them -
the `courtyard` byre form seating nothing at all on Mizuguchi, 3 byres -> 0 - passed 189 checks, all
48 seeds, AND a check written in the same commit specifically to catch it, because that check was
guarded on `M.get("byres")` and an empty list skipped it. Four reviewers found it independently.
Fixed items are recorded at their point of change; these are the ones deliberately NOT fixed.

### A. Every woodland commons is an axis-aligned SQUARE - 12 of 12 across the four hamlets

`rot: 0`, `w == h`, on every parcel the engine has ever drawn (Inashiro 254/232/258/149, Mizuguchi
219/242/265/288, Kashikawa 117/125, Sawada 136). The 2026-08-18 work fixed WHERE they sit and HOW BIG
they are; the SHAPE is untouched, and the reviewer's point is that the chain was the artifact a
MANIFEST reader saw while the square is the one a SHEET reader sees - the crown scatter only partly
disguises it, and a parcel's top and left edges read as ruled lines at fit zoom.

**THE DEFERRAL GOT COSTLIER, not cheaper** (round-2 review, Inashiro): four IDENTICAL squares read as
one repeated stamp, but four DIFFERENTLY-SIZED perfect squares read as a lattice with a size knob
bolted on - because the varying dimension proves the constant one was a choice. The size-variance
work made the shape more conspicuous, so this should be picked up sooner rather than later.

**Why deferred**: this is a new generative dimension, not a tuning change - `open_ground_patches`
builds an axis-aligned quad by construction and every keep-out test downstream assumes that box.
**Research first, and it looks decisive**: *iriai* boundaries were customary and described by ridge,
stream and path, and satoyama coppice sits on the slope break above the paddy - so "no fixed shape"
is very likely the answer, which per Principle XII makes this a KNOB (roll an aspect ratio and a
bearing per parcel) rather than a number. **Sketch**: roll `aspect` in ~1.0-2.2 and `bearing` off the
fall line per parcel from `_hjit`; emit the rotated quad; `_ok` already tests a center plus a half
extent, so give it the rotated half-extents. Do NOT square-to-rectangle uniformly - the point is that
two hamlets differ.

### B. Kashikawa's woodland sits DOWNSLOPE, against doctrine stated in three places

Measured against the cluster centroid with the map's own fall vector: parcel 1 is 505 ft downslope,
parcel 2 is 887 ft downslope and stands 75 ft from the reed marsh. `settlements/vegetation.md` says
woodland goes "on the higher / farther ground", `research/fields.md` says "satoyama crowns the hills
above", and `hinterland.py`'s own comment says "the back slope behind the houses". The scorer is
`-hypot(dist_to_cluster) + 0.35 * upslope`, so a 90 px step toward the cluster outbids 257 px of
height and the upslope term never binds.

**Why this needs a RULING and not a tweak**: raising the weight until it binds returns Kashikawa to
ZERO parcels - its only in-frame upslope ground is a shallow SW triangle already taken by the
connector lane, the SW homesteads and the belt rect - which is the exact defect closed this morning.
The two honest options are (a) raise the weight AND add an explicit, commented "no upslope seat
qualified, taking the best cross-slope seat" fallback so the downslope outcome is a recorded decision
rather than an accident, or (b) keep the scorer and correct the prose, including this map's own kanji
paragraph, which currently claims the sheet draws the high-ground oaks. **Both files must not go on
saying opposite things.**

### C. `surface_water_dist` reads `channels`, but a comb map's watercourses live in `drawn_channels`

The predicate behind the well objective's exclusion set reads `M["channels"] + M["streams"]`. On
Sawada `channels` holds ONE 160 ft intake stub while the 13 real watercourses are in
`drawn_channels`; every house is within 63-361 ft of one of those. So which houses count as "needing
a well" is decided by **which manifest container a watercourse happens to be recorded in**, not by
what kind of water it is. If `drawn_channels` counted, 19 of 19 Sawada houses would be watered and
the objective would have no clients at all.

**The exclusion is probably RIGHT and the mechanism is definitely wrong.** Research points to a real
distinction - domestic water from a well or spring, ditch water for washing at a dedicated *kawado*
stand - which would make excluding irrigation ditches correct. But then the intake stub should be
excluded too, and the reason should be written down instead of being an accident of manifest shape.
**Sketch**: decide the predicate on the water's KIND, not its container; document the ruling at
`surface_water_dist`; expect the needy set to grow on comb maps and re-measure the cohort.

### D. DONE / HANDED OVER 2026-08-18 - the two lane-topology defects

Both were re-measured after the peer session's lane-web feature merged, and both moved:

- **Kashikawa's 223 ft duplicate lane is GONE**, verified by the round-2 review. The peer's
  `trim_lane_stubs` pulled lane 1 back from 354 ft to 146 ft, and lane 2 now starts 16.3 ft along
  lane 1's own centerline with 0.3 ft of perpendicular offset - one continuous ~377 ft way with a
  small overlap at the joint, not two parallel ways. A pairwise shadow test over all 10 lanes found
  no remaining pair above 35% except short cross-links meeting their parent at 69-85 degrees, which
  read as links. Nothing to fix.
- **Sawada's 110 ft spine hole is CLOSED, and what replaced it is milder but still wrong.** Lane 2's
  end is now the exact start of web lane 6, which runs 104 ft to a point lying ON lane 4, whose far
  end passes 1.29 ft from lane 0's start - genuinely connected. But travelling the spine you arrive
  at 46.7 deg, turn ~90 deg back up at -43 deg for 40 ft of alley, then leave at 25.4 deg, with a
  33 ft stub off the apex: it draws as an arrowhead, not the `Y` the manifest declares. **Owned by
  the peer session** (`ways.py` / `water_ways.py` are theirs, and their check 0612
  `lanes_do_not_break_mid_run` is red-first against the pre-fix version of exactly this). Re-scoped
  for them as: a skeleton arm may not be joined to another by a right-angle jog through a web alley.

Keeping the entry rather than deleting it, because the OLD numbers were quoted to the peer and to a
reviewer, and a future session searching for "the 110 ft hole" needs to find that it is closed.

### E. RE-DESCRIBED 2026-08-18 - belt continuity is ungated, and a bare LATITUDE is the wrong measure

The original entry said Mizuguchi (y=1896) and Sawada (y=2321) carry "zero-canopy latitudes". Two
round-2 reviewers independently showed that framing is wrong, and both did the measurement I did not:

- **A bare latitude is not a hole in a wind wall.** Wind crossing y=1896 still meets canopy north and
  south of it. Measured the right way - bare COLUMN along the wind axis - Mizuguchi's belt is
  continuous: 26 ft bare in total, one notch at x 765-791, on 717 ft of belt, inside the pool's own
  documented baseline. A per-latitude rule would flag that healthy belt.
- **Sawada's gap is where the road goes.** The notch spans y 2317-2376 at x 1924-2023, and the
  connector track leaves at (1951,2318) on a 38 deg bearing straight through it. A wind wall with a
  gate-gap for the cart track is what a real one has. The open question is not the gap; it is that
  *nothing makes that coincidence stable*.
- **What IS worth gating, and what the real defect looked like**: Inashiro's belt was measured at 17.1
  ft minimum canopy after my fix and **4.8 ft** after the peer's lane web landed, with a 45 ft band at
  y 660-720 down to ONE clump. That is a genuine breach, and no check saw it.

**Sketch, corrected**: `village_windbreak_is_continuous` measuring canopy DEPTH per column ACROSS the
wind, not coverage per latitude - a latitude rule flags healthy diagonal belts and misses thin
windows. Gate key **0613** (0612 went to the peer). Red-first against Inashiro's y 660-720 band.
Claimed by this session, explicitly, after offering it to the peer and being told to take it.

### F. Woodland is stocked like parkland, not like a wood

Sawada's parcel: 19 crowns over 127 x 127 ft = 1 crown per 852 sq ft, against the copse's ~1 per 287.
`woodland_commons_visibly_stocked` tests `crowns >= 5`, a COUNT, so it cannot see density. A coppice
is a thicket cut on rotation. **Sketch**: raise stand density inside a woodland parcel and make the
check area-scaled rather than a flat floor; watch `woodland_clear_of_grove` and
`structures_clear_of_trees` for fallout.

### G. Two glyph-vocabulary collisions (cosmetic, both flagged twice)

The byre and the notice board are both a small tan box with a dark bar at fit zoom, and there are
several byres to one board; the board's caption disambiguates it, nothing disambiguates a byre. And
the windbreak belt and the copse share one crown vocabulary - on Sawada their centroids are 23 ft
apart and half the copse's clumps touch the belt's, so the manifest declares two features and the
sheet shows one wood. A planted belt was typically one tall species in a row against mixed broadleaf
coppice, so the fix is a different crown vocabulary for the belt, which would also make its
(excellent, 906 x 199 ft, aspect 4.5) form legible.

## OPEN 2026-08-18: paddy bunds still step sideways - the placement half of the GM's report

**The report (GM 2026-08-18, on Inashiro).** *"The earthen wall is kind of going in a southward
direction, and then instead of just continuing on and meeting at the four way intersection between
the north south earthen walls and the east west earthen walls, it just goes sharply to the left
before going down, thus making these extremely irregular shapes. This really, really looks like a
rendering error."*

**The measurement, which is the part worth keeping.** Snapshotting `close_seams`'s input and output
on Inashiro: **0 steps on the 543 carved rings, 26 on the 634 it hands back** - 20 welded into
carved basins by `_absorb`, 8 on pockets `_plant` planted. Every frozen pre-`close_seams` fixture in
`pool/regressions/` scores 0. The carve does not make this shape; the seam pass does.

**The mechanism.** A thin residual strip between two carved rows is one connected scrap. `_plant`
grids a pocket from the POCKET'S OWN bounding box at `plot_across` (48 ft on a hamlet), which is
where neither the row above nor the row below has a seam, and hands the too-thin cells back as
offcuts. `_absorb` then welds each offcut into whichever basin shares the most bund with it -
alternately the row above and the row below - and the wall between the rows comes out a staircase.
Inashiro's east flank at (2283-2474, 1718) is four rectangular tabs in a row, which is the one the
GM circled.

**What landed** (2026-08-18): `waterfields/banks.py::jog_steps` / `jog_vertices`, the predicate; a
jog guard in `_absorb`'s ladder, ranked with the needle and lump guards and preferring the
least-jogging weld among the fallbacks; and `tools/jogs.py`, the by-hand report. Measured on the
four scripted hamlets: **26 -> 23, 37 -> 33, 20 -> 17, 24 -> 16** steps at the intended gate
thresholds, no regression on any other check, and no measurable cost (regeneration 21.1 s before,
20.8 s after on Inashiro). The research is in `research/fields.md`, "A bund runs on, or it turns for
a reason".

**What is left, and it is the bulk of it**: get the four maps to zero, then move the rule out of
`tools/jogs.py` into `check_village` as `paddy_bunds_do_not_jog` (3 ft offset, 8 ft runs, 25 ft link
cap, headings compared over the full circle), with a frozen pre-fix Inashiro fixture in
`pool/regressions/`. The check text, its seven unit tests and the fixture were all written and
proven to fire before being backed out with the failed attempts below; recover them from this
commit's parent if the next session wants them rather than rewriting.

**TWO DEAD ENDS, both implemented, measured and reverted.** Neither is a reason not to try again -
both got most of the way - but each broke something specific, and the next attempt should start by
answering the specific thing.

1. **`_share` - partition a scrap among the basins along it by NEAREST BASIN. Tried TWICE, and the
   second attempt is the one to read.** The idea is right and the first numbers said so: each basin
   takes the ground in front of its own bund, so its wall moves outward across its whole frontage and
   stays one line, and the T-junctions that leaves are what the research says real fabric looks like.
   Inashiro went 23 -> 7 and the staircase the GM circled disappeared from the render. Grown by
   dilating each basin's frontage in one-foot rounds (flat caps and mitre joins, or the band
   boundaries come back as thirty-vertex arcs), bounded to 16 ft of reach since a scrap is thinner
   than a plot everywhere, then straightened with Douglas-Peucker at 0.9 of the step - straightening
   at the FULL step moves a wall past the 3 ft `paddy_plot_seams_shared` treats as one line and broke
   it. Cost: about 10% of the regeneration.

   **What it breaks, and what the second attempt found out about WHY** - this is the part worth
   keeping, because the first write-up guessed and the guess was wrong. It is not hairline vertex
   noise (that was the visible symptom). Instrumented on Inashiro:

   - **`_absorb` refuses 960 of 2,685 welds with the partition, against 5 of 370 without it** - 36%
     against 1.4%. The pass leaves **16,767 px2 of bare ground inside the command area against
     1,760** with no partition at all, worst single pocket 2,499 px2 against 245. Every one of those
     pockets is a doubled bund, which is what `paddy_plot_seams_shared` fires on.
   - **492 of the 960 refusals had NO ADJACENT BASIN AT ALL.** That is the mechanism: `_absorb` ranks
     the basins whose bund forms part of the scrap, so a piece touching only its SIBLINGS has nothing
     to rank and is refused outright. Two things strand pieces that way - a frontage's claim can come
     back in two parts (it turns a corner and pinches off), and the recovery pieces for ground the
     straightening gave up sit between other pieces by construction.
   - **Both are fixable and were fixed**: abandon the partition for any scrap where a piece reaches no
     basin, and FOLD the recovery ground into the neighbouring piece (by shared boundary, the same
     rule `_absorb` uses one level down) instead of offering it separately. That took bare ground
     16,767 -> ~4,900 px2 and refusals 960 -> 281.
   - **And it still is not enough.** With both guards the partition applies to a minority of scraps,
     `paddy_plot_seams_shared` still fails on all four hamlets, and the jog counts come out
     38 -> 25, 45 -> 42, 30 -> 24, 21 -> 21 at the tool's thresholds - a real improvement, but a
     fraction of the unguarded 23 -> 7, because the guards switch the partition off exactly where the
     ground is awkward, which is exactly where the staircase is.
   - **It is also fragile against GEOS**: three separate `TopologyException: side location conflict`
     sites in one afternoon's sweeps (inside `_share`, inside the stranding test, and inside
     `_absorb`'s own ranking loop, which had never needed a guard in its life). Each one was guarded
     and the next appeared. A tidying pass that needs a net under every boolean it touches is telling
     you something.

   **The conclusion the second attempt reached, which is a change of direction rather than another
   guard.** The partition is fighting `close_seams`'s architecture: it splits ground that the weld
   ladder is built to take WHOLE, and the ladder's guards - needle, lump, jog - are all calibrated to
   a scrap, not to a quarter of one. **The next attempt should go upstream instead.** The 48-ft pitch
   that misaligns the strip is `_plant`'s, and `_plant` grids a pocket from the POCKET'S OWN bounding
   box: cut it at the SURROUNDING FABRIC'S seams instead - the vertices the adjacent basins already
   carry on the pocket boundary - and the offcuts come out where the rows actually break, so welding
   one cannot step a wall in the first place. That is a smaller change, it needs no new booleans, and
   it attacks the mechanism rather than the residue.

2. **`_unjog` - repair what neither guard could avoid, by straightening a surviving step.** Took
   Inashiro from 5 to **0** and the whole gate green, which is why it is worth recording in detail.
   Two implementations. Dropping the step's two vertices from every ring that carries them is NOT
   partition-preserving - the two rings either side of a wall have different neighbouring vertices,
   so the chords they close over differ, and Inashiro's rings 460 and 592 lost 400 px2 and gained
   259, the difference being bare floor. The second implementation trades the corner explicitly
   (`traded = was.difference(now)`, then the neighbour unions or differences it), which conserves
   ground by construction and is the right shape. **What it broke**: on Mizuguchi,
   `paddy_bunds_clear_the_supply_channels` (a straightened wall moves, and can move into a delivery
   ditch) and `paddy_plots_are_workable_basins` (the repair can draw a basin out to a needle) - both
   have guards written for them in that reverted commit, judged at the GATE's thresholds since a
   repair is not a placement choice, and the guards were not enough on their own. It also needs the
   three refusals it already had - a T-junction, a repair that takes a basin under `_TOE_MIN_AREA`,
   and a one-basin wall where the cut would SHRINK the basin - and it must not rebuild the vertex
   index per plot (that alone took a regeneration from 26 s to 80 s).

**The order to do it in, revised after the second `_share` attempt**: `_plant`'s pitch first - cut a
pocket at the surrounding fabric's seams rather than at its own bbox - because that is the mechanism
and the other two are residue. Re-measure. Only then decide whether anything is left for a partition
or a repair pass, and expect the answer to be less than it looks now.

## OPEN 2026-08-18: the byre at the settlement EDGE - a knob candidate, and what to research first

Raised by `settlement-review` on Inashiro while it was checking the jog delta, so it is a finding
from outside the delta rather than part of it (which is the reviewer working as intended).

**The measurement.** Byre 0 sits at (1047.8, 989.5) - 70 ft past the westernmost house, INSIDE the
shelter belt, 29.3 ft from the nearest grove clump with 45 tree crowns within 40 ft - and reaches
**2 of 15 households within 200 ft**, against 5 for byre 1 and 6 for byre 2. `settlements/homesteads.md`
puts a shared draft-animal byre "in the COURTYARDS among the homesteads", and the 2026-08-18 pass
added a borrow-coverage term to stop the maximin spread picking isolated seats. On this roll the
spread term still wins at one seat of three. The notes ledger a version of this from an earlier roll
(a different byre, at the NE outlier), so what recurs is the CLASS, not the instance.

**The research question, and it is a research question rather than a ruling** (Principle XII): was a
shared ox shed ever sited at the settlement edge under the shelter planting - for shade, for manure
handling, for keeping the beasts out of the dooryard - as opposed to in a courtyard?
`research/homesteads.md` covers the byre-vs-well question and does not address byre-vs-edge, so the
search pass has not been run. **Run it before touching the placer.**

**The likely shape of the answer.** The reviewer's read, which I share on the evidence so far, is
that both sitings are defensible - which by Principle XII makes this a KNOB with per-settlement
variance rolled from the map's own seed (courtyard byre vs edge byre), not a fix, and a knob that
would visibly differentiate hamlets. What is NOT defensible on either reading is a byre reachable by
2 of 15 households while two other seats on the same map reach 5 and 6: whichever form the roll
picks, the coverage term has to bind. So the work is: research it; if it supports both forms, add the
knob AND make the borrow-coverage term binding within whichever form is rolled.

### Two nitpicks from the same review, neither worth its own feature

- **Flooded-basin tint vs channel hue.** The two water-tinted basins sit in the same hue family as
  the drawn channels, and at fit zoom the 19-ft-wide one at (2184.6, 1739.9) reads more as a sliver
  of open water than as a flooded basin. The geometry is right (19 x 114 ft, 28.5 deg apex - a real
  basin, and `flooded_plots_read_as_basins` agrees); it is a hue-separation question for
  `waterfields/palette.py`, and it should be answered for the whole tint at once rather than for one
  plot.
- **Byres buried in canopy.** Two of three byres carry ~45 crowns within 40 ft while the third
  stands clear, so at fit zoom the sheet reads as one byre rather than three. Nothing overlaps (that
  is gated); it is a legibility consequence of the grove scatter, and it belongs with the byre-siting
  work above rather than with the groves.

