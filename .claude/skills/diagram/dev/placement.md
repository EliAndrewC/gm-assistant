# Placement: draw order, footprints, and the keep-clear contract

**Load this file when:** You are adding a new map feature, changing where something is placed or drawn, or wondering why the placer allowed an overlap the gate then caught. Read the DRAW ORDER section before moving any placement.

Split out of [`../CLAUDE.md`](../CLAUDE.md) so it is not in every diagram session's
context. The text is verbatim; the short always-on version of each rule stays in the index.

## DRAW ORDER: read this BEFORE changing where anything is placed or drawn

Most of what a Mode B feature gets wrong is not geometry, it is ORDER. A drawing method sees only
what is in `self.M` at the moment it runs, and a placement method avoids only what is in the
registries at the moment it runs - so "tree not drawn on a roof" and "building not placed under a
canopy" are the SAME rule enforced from two different points in the sequence. This map cost four
fail-read-fix cycles to reconstruct on 2026-07-25; it is written down so nobody pays for it twice.

**The three registries, and who honors them:**

| registry | holds | consulted by |
|---|---|---|
| `block_polys` | no-build polygons (field envelopes, the wood, dry plots, the manor court) | `_rect_blocked` tests a whole FOOTPRINT (homestead bundles); `_fits` -> `_in_blocked` tests only the candidate's CENTER (urban packs) |
| `placed` | `(x,y,w,h)` of everything already standing | `_fits` keeps each candidate a half-diagonal + 4px clear |
| `grove_rects` | tree footprints, deliberately kept OUT of `placed` so adjacent groves may abut | `_fits` (same clearance rule), `_east_trees` (garden morning-sun) |

**That `_fits` asymmetry is the trap.** A block poly stops a farmstead whose footprint merely touches
it, but stops an urban building only when its CENTER lands inside - so a wide building can put half
its roof over blocked ground. If a feature must keep whole footprints out, `placed`/`grove_rects`
(distance-based) is the registry that does it; `block_polys` alone is not enough.

**SEE IT BEFORE YOU READ IT.** `dev/placement-stages/hamlet-placement.html` is Inashiro rolled one
stage at a time, with a plate of the map after each of the thirteen stages and a note on why that
stage sits where it does. Regenerate it with `python3 -m l7r.diagram.tools.placement_stages` whenever
`STAGES` changes - it is generated, never hand-edited, and its per-stage prose is keyed by function
name so a renamed or new stage shows up as missing rather than silently inheriting its neighbour's.
The page is the picture; this document is the rulebook.

**THE SCRIPTED ORDER IS `STAGES` IN `hamletgen/driver.py`, and it is the authority for a scripted
tier.** The phase list below describes the HAND-AUTHORED gens (Moritono is its clean example) and
remains true of them; it is a phase model, not a stage list, and it does not match the scripted
sequence one-to-one. Where the two disagree, `STAGES` wins for anything under `hamletgen/`:

| # | stage | what it puts on the map |
|---|---|---|
| 1 | `stage_water_frame` | **nothing - it draws no ink at all.** Settles the drainage bearing and the land's fall and writes twelve values to `meta`; every later stage reads them |
| 2 | `stage_field` | the water skeleton AND the paddy - `build_comb` returns canals and plots from one call, so intake, head race and field ditches arrive here, not in stage 1 |
| 3 | `stage_sink` | tail drain, pond or off-map outfall |
| 4 | `stage_ways` | the CONNECTOR and the field spur only - the EXOGENOUS ways, which genuinely predate the settlement. The internal skeleton moved to stage 7 in feature 126 |
| 5 | `stage_homesteads` | the farmhouses |
| 6 | `stage_appurtenances` | yards, gardens, byres, wells, sheds |
| 7 | `stage_web` | ALL the endogenous ways - the internal skeleton AND the lane web, both derived from where the houses actually landed. No-op for a dispersed hamlet, which has no internal network |
| 8 | `stage_notice` | the kosatsuba, which stands ON a way and so waits for the web |
| 9 | `stage_hinterland` | scrub and rough grazing |
| 10 | `stage_woodland` | woodland commons |
| 11 | `stage_windbreak` | the shelter belt |
| 12 | `stage_crossings` | planks and decks over every way that crosses water |
| 13 | `stage_frame` | crop to content, title, scalebar |

**WAYS ARE SPLIT BY PROVENANCE, NOT BY TIMING** (feature 126, 2026-08-23). The GM asked whether
laying lanes before houses reflects how lanes form, and it does not - a lane between farmsteads is
trodden by the households already living there. So the question a new way must answer is not "does
this reserve ground or fill it" but **"did this way exist before the settlement did?"**

- **Exogenous** - the connector to the off-map road, the field spur. These predate the houses and
  are laid before them; houses may legitimately front them, which is what the LINEAR form is.
- **Endogenous** - the internal skeleton, the lane web. These are worn by the settlement, so they
  are derived from where the houses actually went.

The older reserve-vs-fill rule was a good approximation and got the WEB right for the right reason,
but it kept the skeleton first, and the skeleton was sized on the seat band while the houses spread
wider than the band - which is why it could not be guaranteed to reach them, and is the root of the
`farmhouses_reach_a_way` defect that survived seventeen attempts.

**A recorded dead end that no longer applies**: feature 123 tried sizing the skeleton over the
ground the houses take and reverted it, because longer arms offered more frontage seats and the
cluster stretched to meet them. That was a FEEDBACK loop, and it existed only because the skeleton
was laid before the houses and its arms generated seats. Laid afterwards there are no seats to
generate, so the loop is severed rather than re-entered.

**STAGE 1 DRAWS NOTHING, and both this table and the walk-through page used to claim otherwise.**
Corrected 2026-08-23, after the GM reported the walk-through's first plate as blank: it was blank
because `stage_water_frame` emits zero SVG records: it sets `meta` and pins knobs, and that is all.
The water a reader expects to see there is drawn one stage later. Worth carrying beyond this one
row - **a stage's name is not evidence of what it draws.** The cheap check is a record-count delta
across `out`/`top`/`walls`/`toplabels` around the call, which is now what `placement_stages.py` uses
to decide whether a stage gets a plate or a no-ink card, so a stage that draws nothing announces
itself on the page instead of rendering an empty square that reads as a broken image.

**Two places the phase model below is actively WRONG for a scripted hamlet**, found by auditing it
against `STAGES` on 2026-08-20 rather than by a failure - which is the point of writing it down:

- It puts `place_kosatsuba()` in phase 4 with the other structures. In the scripted tier the notice
  board is stage 8, AFTER the web, and it has to be: the board stands on a way, so it cannot be
  sited until the ways are final. It is the clearest case on the map of a feature whose position is
  defined by something drawn later than itself.
- It has one "ground cover" phase and one "communal vegetation" phase. The scripted tier splits
  those into three ordered stages - hinterland, then woodland, then windbreak - and the order among
  them matters (woodland after hinterland so the coppice sits in real open ground rather than ground
  the scrub was about to take).

**The order a Mode B gen runs in** (Moritono is the clean example):

1. **terrain + water** - fields, channels, streams, pond, marsh
2. **big terrain features** - `forest()` / `forest_patch()`. EARLY, because the settlement is sited
   against them; their FLOOR draws here but their CANOPY is deferred (see 7)
3. **ways** - road, lanes, streets. This is the ground-RESERVING half: the skeleton and the
   connector, laid so the homesteads front them
4. **structures** - `manor()`, `farmsteads()`, urban packs, `place_wells()`, `draft_byres()`,
   `place_kosatsuba()`. Inside `farmsteads()` the bundle path records grove rects first (the garden
   relaxation needs them), then draws yards/gardens/houses, then draws the yashikirin arms LAST
4b. **the LANE WEB** (scripted hamlets, `stage_web`) - the ground-FILLING half of the ways, and the
   one stage that deliberately runs after the structures it serves. It threads lanes through the
   room the seated cluster left, so every farmhouse is within reach of one, and it reads the drawn
   houses, yards, gardens and groves as obstacles rather than reserving anything from them
5. **ground cover** - `hinterland()` scrub + marsh (skips structures via `_urban_keepouts`)
6. **communal vegetation** - `village_grove()`. LATE, so its per-crown filter sees every structure
7. **crop** - `crop_to_content()` / `crop_city()`, which first run `flush_stable_yards()` and
   `flush_tree_stands()`: the deferred yard furniture and every wood's canopy draw HERE, against the
   complete map. `finish()` re-runs the tree flush as a backstop for a gen that never crops
8. `title()`, `finish()`

**The two rules that fall out of it:**

- **Must not be drawn ON something?** Run AFTER it, or defer to the flush. Drawing early and letting
  the later feature paint over it hides the overlap instead of preventing it - which is exactly what
  the yashikirin used to do, leaving crowns geometrically under roofs while looking fine.
- **Must FILL ground that is left over?** Run AFTER placement and read the drawn features as
  obstacles. This is the mirror of the rule below and it is easy to get backwards, because getting
  it backwards does not fail loudly: feature 123 laid the lane web before the houses, which is what
  the ways stage does, and the web then competed for ground with the very houses it existed to
  reach - the four pool clusters' long axes grew 15-97% and nothing in the gate measures sprawl.
- **Must RESERVE ground?** Run BEFORE placement AND register in a registry that the placer in
  question actually honors (see the asymmetry above).

**Changing any of this deserves a design pass first.** Read the paths above and settle the ordering
on paper before editing - the failure mode is discovering the sequence one gate failure at a time,
which is what turned a small rule into four fix-fail-read cycles. If a change needs a feature to
move between phases, say so explicitly in the commit: phase moves are the changes most likely to
have effects far from the diff.

## CENTER vs FOOTPRINT: the three ways placement and the checks disagree

The GM, 2026-07-26, after the overlap matrix kept finding things the placer had allowed: *"if
placement is only testing the house's center while the matrix tests its footprint, then maybe the
placement test is wrong? Are there other placement checks which are only checking the center? That
could explain a lot of overlap issues as well as a lot of inefficiencies."* Both halves were right,
and there turned out to be **three** distinct disagreements, not one. Know which you are looking at
before you touch anything.

**1. Center-tested keep-outs (UNDER-restrictive -> overlaps).** `_fits` tested a candidate's CENTER
against `block_polys` and the corridors, so a footprint could hang over blocked ground by up to half
its width. Fixed by SPLITTING the registry: `hard_polys` (crop, pond, bog, a field's own ditches) is
tested against the whole footprint; `block_polys` keeps the center test. **Do not merge them back.**
Footprint-testing all of `block_polys` was tried once and reverted, because it also contains SOFT
reservations - caption bands, civic aprons, fence standoffs - that a footprint routinely overhangs
by a few px, and tightening those cost Nagahara a well and pushed Hoshizora's punishment ground off
its street. The split is the fix; the conflation was the bug.

**2. Circumscribed-circle collision (OVER-restrictive -> wasted ground, and LOAD-BEARING).** Against
`placed` and `grove_rects`, `_fits` still uses half-diagonal circles, not real footprints. For a
46x28 house that is r=26.9 against a true half-width of 23, so two such houses are forced >=57.8 px
apart center to center where true touching is 28. It never permits a real overlap - it just wastes
up to ~2x the spacing, which is a real cause of "the packer says the ground is full" when it is not.

**The waste is real and large - measured on Tango, 2026-08-08.** A wrapper that computed the
diagnostic beside the real verdict (so the map generated was the real one) over 71,860 `_fits`
calls: **38.7% of all refusals come from the circle clause**, and **767 seats are refused by nothing
but the approximation** - a **+57.6%** increase in the pool of legal seats the placers see. That is
per-CALL, not per-building: it means far more choice for every scan, not 57% more houses.

**But do NOT swap it for a footprint test on its own.** Tried the same day: replacing the circles
with an exact axis-aligned box gap takes Tango's gate from clean to FIVE failures, two of them
genuine overlaps (`features_do_not_overlap`, `no_structure_overlaps`), plus a fire tower standing on
a wellhead and a well inside a building. The reason is that a circumscribed circle is
**rotation-invariant**, and that is exactly what has been absorbing item 3 below: houses are drawn
at +/-5 deg and buildings at 90/180 deg, where `w` and `h` swap outright, so an axis-aligned test on
the PLACEMENT dimensions is simply wrong for them. It was partly covering item 1 too - with tighter
packing, buildings landed on wells whose `block_polys` reservation is only center-tested.

**So item 2 is blocked on item 3, not on the cost of re-baselining** - which is what this entry used
to say, and it was the wrong diagnosis. The circles are not conservative padding; they are the
mechanism masking the rotation mismatch, and removing them converts a documented inefficiency into
shipped overlaps. The order is: fix **item 3** so the placer tests the rotated footprint it will
actually DRAW, then item 2 becomes a real `sat_overlap` on real corner quads, and only then does the
pool re-roll. Budget for that re-roll: the naive swap alone already moves Tango +21 houses (+8%),
+20 buildings (+3.2%) and +23 wells (+25%).

**3. Placement tests a DIFFERENT footprint than the one drawn (still open, but now measured).**
`_fits` is called with a farmhouse's BASE rect, but the drawn steading can exceed it - a wealth
render scale, an attached shed, a rotation. So a candidate that genuinely cleared every keep-out at
its placement size laps one at its drawn size, and no amount of fixing (1) reaches it. Hoshizora's
gen already works around this by inflating its hem plots ~8 px (`grow_poly`), which treats the
symptom locally. The real fix is for the placer to test the size it is going to DRAW.

**Two 2026-08-12 findings sharpen it, and one of them is already banked.** A WAY now records its
drawn TREAD (`_record_tread`) beside its soft corridor, and `_fits` tests the whole footprint
against the tread while the clearance keeps its center test - the split that makes this safe where
footprint-testing all of `block_polys` was not, since a clearance is slack and a road surface is
not. Lanes only, deliberately: the other ways already pad their corridors by hand, and tightening
them cost Tango a public well. No pool manifest moved.

**But the BUNDLE path never reaches `_fits` at all**, which is the bigger half and was not visible
until a cohort went looking. **DONE 2026-08-17 (feature 121)** - and the diagnosis this paragraph
used to carry was WRONG, so read the correction before quoting it anywhere.

*What it used to say:* the house inside the bundle "is offset from the seed point AND scaled by the
wealth/length jitter - so the rect the placer clears is neither the size nor the position of the
rect that gets drawn."

*What is true:* measured across `pool/hamlets/inashiro.json`, the bundle's house rect matches the
drawn record's position and size to **0.0000 px**. `hw`/`hh` are computed with their jitter BEFORE
`_place_bundle` is called, and `_bundle_geom` is rebuilt at the final slid position. **The
divergence was the RAKE, and only the rake** - `_house_rot`'s +/-5 deg, worth up to **2.56 px** of
corner bulge, which is exactly the 2.4 px `_on_a_tread`'s own docstring reports. Because the rake is
position-seeded it is knowable at seat time, so the fix needed no change to when rotation is
decided; a "different size, different place" diagnosis would have implied one.

*Three defects, not one, and the second two were unknown:*

1. the bundle path never tested a drawn surface at all - `_rect_blocked` ended at
   `_near_corridor(cx, cy)`, a bare center test. Now `_house_on_a_tread`.
2. **`_on_a_tread` itself passed `rot_rect(..., 0.0)`** - so the path that HAD the footprint test was
   measuring a square-on rect too. It takes `rot` now; `None` from a caller means UNKNOWN, not zero.
3. **the GATE was rake-blind** - `houses_clear_of_lanes`'s `_house_pts` built its own axis-aligned
   corner list beside `rect_corners`, which reads `rot` and is imported into the same module. So the
   check meant to catch the defect had the defect, and disagreed with the fixed placer about the
   same house. One measurement, not two (contract C7).
4. and the RENDERER rounded: the house glyph emitted `rotate({rot:.0f})`, whole degrees, against a
   placer and a gate working in floats - ~0.95 ft of drawn-corner displacement, invisible to every
   check because checks read the manifest and never the SVG. Found by `settlement-review`.

*The old cost estimate was stale in the other direction too*: it budgeted re-rolling Ikegami,
Kuwabata, Tanada and Hoshigaoka, all of which entered `LEGACY_FROZEN_GENS` on 2026-08-16 and are
never regenerated. Actual cost: three live scripted hamlets moved, one review each.

Measured: **10 of 24 cohort maps** put a house corner on a lane at a 32 px clearance before, **0**
after; cohort 22/24 both before and after, same two pre-existing failures on the same two seeds.
`LANE_CLEARANCE` is now derived (48 -> 40) and no longer the thing holding houses off lanes.

**The general lesson.** A point test is right for a SCATTER (each tuft is a point) and wrong for
anything with an extent. The same trap bit the ground-cover tiler: `near_ring_cropland` sampled a
cell's center and four corners, which a small keep-out sitting against an edge MIDPOINT slips
between - that is how a wellhead ended up 1 px inside a hatake plot. Region-vs-region helpers
(`quad_hits_poly`, `quad_hits_seg`, `point_quad_dist`) exist now; use them rather than adding sample
points.

## Centers, footprints, and aggregates: which one a rule is allowed to use

The GM, 2026-07-27, after the boundary-stone defect: *"I'm not sure it EVER makes sense to use a
center instead of a footprint... we've had a lot of bugs slip through because of using centers,
which makes me wonder whether we should just ban them."* An audit of all 42 center-distance sites
and 29 `point_in_poly`-on-a-center sites says: a blanket ban would break three things that are
right, and would still have missed the defect that prompted it. **Four families. Say which one your
rule is in, in a comment, at the point of the test.**

| family | measure | why | examples |
|---|---|---|---|
| **Gap VERDICT** - "N ft of clearance", "these must not overlap" | `edge_gap` / `within_edge_gap` / `sat_overlap` on real rotated corners. **Never** a center, **never** a circumscribed radius | the answer is a distance you could pace out between two walls | `execution_ground_outside_the_settlement`, `town_has_cremation_ground`, `burakumin_quarter_segregated`, `execution_ground_clear_of_the_dead`, `wells_among_dwellings`, `farm_sheds_attached` |
| **CLASSIFICATION / counting** - "which ward", "how many inside the wall", "what share of this quarter is civic" | center, deliberately | a building belongs to ONE ward; footprint-testing double-counts a building on a seam and the ward populations stop summing to the town | the 29 `point_in_poly(b["x"], b["y"], wall)` sites |
| **ASSOCIATION / reach** - "is there a well within reach", "do monk houses cluster at their temple", "is this yard on the water" | center, deliberately | the tolerance (75-480 px) dwarfs the footprints and the question is neighborhood membership, not clearance; converting them re-tunes ~21 calibrated constants to fix nothing | `settlement_dwellings_watered`, `city_monk_houses_by_their_temple`, `_ty_on_water` |
| **PREFILTER** in front of an exact test | circumscribed radius, deliberately | over-stating an extent can only ADMIT a pair the exact test then rejects - the index prunes, it never decides. Tightening these would start rejecting before the exact test runs | `fire_tower_standoff`, `no_structure_overlaps`, `city_house_doors_unblocked`, `within_edge_gap`'s own prefilter |
| **POINT FIXTURE** - a distance to a gate, torii, sluice gate or bridge | point, unavoidably | these are recorded as bare `[x, y]` in the manifest and have no footprint to test. If one ever gains `w`/`h`, the rules that measure to it become gap verdicts and move to row 1. **The kido left this row on 2026-07-27**: it never had `w`/`h` either, but it records `parts` - each drawn rect's rotated corner quad - and `guard`, so it always had a real footprint that nothing read. The trigger condition is therefore not "gains `w`/`h`" but "records ANY drawn extent"; check the record, not the two field names | `city_inspection_station_at_each_gate`, `city_kosatsuba_per_gate`, `city_temple_approach_has_torii`, `wall_towers_evenly_spaced` |

**The three conventions that were live before this, and what each cost.** Raw center-to-center
understates clearance by the sum of both half-extents, so a rule promising 120 ft delivered ~60;
`0.5 * math.hypot(w, h)` is the half-DIAGONAL, over by up to 41% on a square and more on a long
rect; `max(w, h) / 2` is the same error differently sized. The approximations' error **flips sign**
with the rule - subtracting too much makes a "must be far" rule strict and a "must be near" rule
lenient - so they are not even a uniform safety margin.

**The ratchet, not the doc.** `test_gap_verdicts_read_footprints_not_centers` plants two features at
exactly the offset where the conventions disagree and pins which verdict is right. Verified to have
teeth: of its nine entries, reverting the helper to raw centers breaks six and reverting it to
circumscribed radii breaks the other three - every entry is caught by one revert or the other. **Add
an entry when you add a gap rule** - a rule that lives only in this table has already been proven
not to hold.

**THE SWEEP IS DONE; DO NOT REDO IT, EXTEND IT.** Two passes, because the first one's METHOD had the
same shape of blind spot as the bug it was hunting. Pass 1 grepped `math.hypot(...["x"]...["x"]...)`
and found 42 sites across 34 checks. That regex cannot see a record compared against an unpacked
`(x, y)` tuple, which hid a second tranche of 45 sites across 36 checks - and one of them,
`tanning_yard_clear_of_dwellings`, was a live 120 ft gap verdict reading 150 ft where the yard's own
corner stood 76 ft from a farmhouse wall (Tango). Everything else in the second tranche classified
as point-fixture, association/reach, classification, or one SIDE test
(`dwellings_above_field_drain`, whose "is the house clearly on the wet side" question is a bearing,
and deliberately center-based). If you add a distance rule, put it in the right row of the table
above and give it a ratchet entry - that is cheaper than a third sweep.

**One measurement, not several.** `edge_gap` is now the only exact footprint-gap helper.
`_fr_gap`/`_fr_poly` - feature 016's own, written before it and doing the same job by the same
method - was folded in on 2026-07-27. Two CORRECT helpers for one question is how the three wrong
conventions got started; if you find yourself writing a third, use `edge_gap`.

**And a fourth axis, which no footprint discipline reaches: AGGREGATE PROXIES.** The boundary-stone
defect was not a footprint bug. `dist(stone, centroid) < dist(ground, centroid)` would stay green
with perfect geometry on both sides, because the centroid - an average of every dwelling - was
standing in for the built EDGE, and a settlement is not a disc. **Never let an aggregate stand in
for the distributed thing a verdict is about.** Measure to the nearest member (or, where the
settlement has a rampart, to the wall - the edge it actually has). `execution_ground_on_the_outcast_
side` still dots against the centroid and that is correct: a BEARING is an aggregate question. A
DISTANCE is not.

**Known debt, recorded as debt rather than design:** `_fits` center-testing `block_polys` (item 1
above). The honest reading is that those polygons are drawn wrong - keep-out plus slack baked in,
with the center test handing the slack back - and the principled fix is to shrink them to the true
keep-out and footprint-test. That re-tunes margins pool-wide, so it is a separate pass.

## Adding a new map feature: the KEEP-CLEAR CONTRACT (read this before writing the glyph)

The GM's observation, 2026-07-25, after the martial hall shipped sitting on Tango's ring road:
*"every time we add a new type of thing, I end up looking at the map and saying 'oh, this new thing
should not overlap with X'."* That is now a solved problem, and this is the whole of what you have
to do.

**One registry, and everything follows from it.** A new footprint feature goes in
`_OVERLAP_STRUCTS` (check_village/common_01_geometry.py) - or, if it is MEANT to overlap something, in
`_OVERLAP_EXEMPT` with the reason. You cannot forget: `every_feature_classified_for_overlap` fires
when a generator emits a feature key nobody classified. Membership alone then gates the feature off
**fifteen hazards** - the wall, the moat, the road, streets and alleys, streams, channels, the
cargo canal, the pond, manor walls, religious halls, gate furniture, torii arches, the ring road,
every other solid structure, and the 14px government-office standoff - because every one of those
checks builds its footprints from the registry via `solid_structs(M)`.

**The failure mode this replaced.** The `no_structure_on_*` battery was always registry-driven, but
a handful of keep-clear checks predated it and hand-listed their own keys. A feature could be
correctly classified, correctly cleared of all thirteen battery hazards, and still sit on the ring
road - because `ring_road_kept_clear` was reading eight keys nobody had updated. A check that never
sees your feature looks exactly like a check that passes, so this was invisible until the GM looked
at a rendered map. Four such checks now read `solid_structs(M)`: `ring_road_kept_clear`,
`city_government_offices_dont_abut`, `city_wells_in_block_interiors`, and the merchant-estate
court test.

**The ratchet.** `test_every_solid_struct_is_gated_off_every_hazard` (in `tests/check_village/`) plants one
instance of EVERY registered key squarely on EVERY hazard and demands the hazard's check fire. If a
keep-clear check ever falls back to a hand list, that test names both the key and the hazard.
Verified to have teeth: reverting `ring_road_kept_clear` to its old list fails it with 21 keys
listed. **Adding a hazard row to `_HAZARDS` extends the contract to every existing feature at
once** - that is the cheap way to answer the next "should not overlap with X".

**The same contract covers CAPTIONS** (GM 2026-07-26). A feature protected from every solid
neighbor is still not protected from a label dropped on top of it, and
`labels_clear_of_other_buildings` had its own hand-written list of ~22 keys that had already fallen
behind twice - `martial_halls`/`dojos` had to be remembered into it, and a day later
`punishment_spots`/`execution_grounds`/`boundary_markers` were absent, so a foreign caption over an
execution ground shipped green. `_LABEL_GROUP` now maps each manifest key to the caption GROUP a
label must name to be allowed over it, `_LABEL_EXEMPT` excuses the few that do not need protecting
(with the reason), and `every_solid_feature_classified_for_labels` fires when a key is in neither.
The permission side is derived from the same registry - a group's name IS its caption word
("brewery", "martial hall", "execution ground") - so a classified feature can caption itself with
no second list to remember. The named branches in `_label_allows` survive only for SYNONYMS: a
caption reads "Temple of Benten" or "Governor's Mansion", not "temple" or "governor".

**RECORD A FOOTPRINT THE EXTRACTOR CAN READ - classification is only half.** GM, 2026-07-27: *"in
general we always want overlap checks to use full footprints."* `matrix_extents` reads `x`+`w`/`vw`,
a `poly`/`outline` ring, a stroked polyline, or a `parts` list of rotated quads. A record matching
NONE of those is extracted as nothing, and a feature the extractor never reaches is invisible to
every matrix check in both directions no matter how carefully it is classified and mounted - which
looks exactly like a feature with nothing wrong. Three keys were in that state until an audit went
looking (`kido`, which records only a center and its parts; `roads`, the multi-road list;
`flower_fields`, whose ring is called `outline`, not `poly`), and the ward gate had been hiding a
notice board sitting on its guard box and two guard boxes cut by their own ward fence. The audit is
cheap and worth re-running whenever a new key appears - per manifest, compare each classified key's
record count against `collections.Counter(k for k, *_ in matrix_extents(M))`; any key with records
and no extents is blind. And where one glyph draws SEVERAL rects, record them as `parts` (rotated
corner quads) rather than a bounding box, and split out any part that does not share the whole
feature's permissions - a gateway may stand on the fence it pierces, its watch box may not.

**The same disease turns up in PLACEMENT PROBES, where it is quieter.** `place_punishment_spot`
probes candidate boxes for its own caption before committing to one, and that probe had its own
hand-written list of nine manifest keys - `dye_yards` was never in it, so when a reflow put Minami's
punishment ground beside the dye works the probe reported a clear box and the gate reported a caption
on a dye works (2026-07-27). It now iterates **any manifest list of dicts carrying w/h**, so nothing
has to be remembered into it. Two sibling lessons from the same defect, both worth generalizing:

- **A probe must measure the box the CHECK will measure.** That probe sized its trial box with
  `_text_width` (the PIL glyph measurement) while `labels_clear_of_other_buildings` reads the box
  `_record_label` writes (`len(text) * size * 0.55`), which is ~2px wider per side at caption size. The
  probe cleared, the gate did not. Same rule as "placement and its check read the SAME manifest
  source", one level down: geometry, not just data.
- **A probe that gives up silently is worse than no probe.** When none of its nine candidate rings
  was clear it left `label_xy` as None and the caption fell back to the default seat - on top of three
  dwellings. It searches sixteen rings now, but the shape of the bug is the fallback, not the number.

**And a caption that is DEFERRED cannot be reserved by reading it back.** `place_caption` seats at
`finish()`, so `s.M["labels"][-1]` right after the call returns some *earlier* label, and a gen that
reserves that box reserves the wrong ground (tango's theater stage, 2026-07-27). Worse, the ladder
seats a deferred caption against a map that is already full, so it takes the LEAST-BAD spot rather
than a clear one. A deferred caption's ground has to be reserved by hand, BEFORE the packs run.

**So the checklist for a new feature is:** write the glyph; record it under a new manifest key; add
that key to `_OVERLAP_STRUCTS` and give it a caption group in `_LABEL_GROUP`; run the suite. If the
feature needs a keep-clear rule no existing hazard covers, add a hazard row rather than a bespoke
check with its own key list.

**The placement side, which the GM asked about next.** `_fits` tests an urban candidate's CENTER
against `s.bound`, `block_polys` and the corridors, and whole footprints only against `placed` /
`grove_rects` (see DRAW ORDER above). `open_seat` now closes the half of that gap that matters:
it verifies the whole FOOTPRINT against **the bound**, because a bound is a hard edge (the
ring-road loop, the wall) and a footprint crossing it is drawn on the patrol road at any overhang -
which is exactly how the martial hall got its seat. `block_polys` and corridors stay center-tested
even there, deliberately: those are soft RESERVATIONS (a label band, a civic apron, a fence
standoff) that a footprint routinely overhangs by a few px, and tightening them was tried and cost
Nagahara a well and pushed Hoshizora's punishment ground off its street. The bound-only rule
changes nothing in the pool. `footprint=False` gets the old center-only answer, i.e. what a pack
would take. (`test_open_seat_refuses_a_seat_whose_FOOTPRINT_crosses_the_bound` holds this.)

**Gap rules are in the table now, but one row each.** A clearance rule ("14px of daylight", not
"no overlap") is the other shape a keep-clear rule comes in, and it broke identically:
`city_government_offices_dont_abut` had never seen the martial hall or the dojo, so both shipped
inside its standoff. A `_HAZARDS` row expresses a gap simply by planting the struct NEAR the hazard
instead of on it, so the contract covers it - but unlike the overlap hazards, each new distance
rule still needs its own row. A row's fifth field lists keys the rule DELIBERATELY does not govern
(the funerary compounds are excluded from the office standoff: a clan crypt against the yamen is a
real adjacency), so a deliberate exclusion is visible in the contract rather than hidden in a
check.

## The collision circle is now blocking FEATURES, not just wasting ground

The "CENTER vs FOOTPRINT" entry above records the circumscribed-circle collision as a documented
inefficiency: `_fits` measures a candidate against `placed` with half-diagonal circles, so a 46x28
house is forced 57.8 px from its neighbor where true touching is 28. Two 2026-08-11 findings move
it from *inefficiency* to *blocker*, and they are the same finding twice:

- **The capital cannot seat a wellhead.** Two machi blocks sit at 27 and 29 households per well
  against a cap of 26, and `open_seat(..., well=True)` refuses a probe at 12, 10 AND 8 px anywhere
  in either block. Tightening the derived well grid does add wells, but they land close enough to
  existing ones to trip `wells_not_clustered` before the deficit clears - the two rules meet with
  one household of daylight between them. Trimming the covering packs does nothing: both are
  capacity-bound and already placing fewer than asked.
- **The capital's new paddy cannot seat a farmhouse.** Ten positions around the field envelope,
  tried three ways (the perimeter ring, `open_seat`, and `try_place` directly): **6 of 10 refused
  by the collision circle**, 3 by a corridor, 1 by a keep-out.

So the next substantial engine job is the one this file already prescribes, in the order it
prescribes it: **item 3 first** - make the placer test the ROTATED footprint it is actually going
to draw - and only then item 2, replacing the circles with a real `sat_overlap` on real corner
quads. Both of the above clear as a side effect, and so does most of the frontage-seat fighting.
Budget for the pool re-roll: the naive swap alone moved Tango +21 houses, +20 buildings, +23 wells.

## Two placer bugs of the same shape: INDEX vs POP

`pack` and `frontage` POP each item they seat; `rowpack` walks an INDEX and leaves the list intact.
So the `_shortfall` call added to `rowpack` on 2026-08-11 - copied from its siblings - handed over
the WHOLE list as "what did not fit", and every run reported an ask of exactly double what the gen
gave it. The symptom is nastier than a wrong number: a run seating half its ask reads as seating a
quarter, and trimming the ask to the reported figure halves it again, so the correction has a fixed
point at 50% and never converges. Four rounds of automated trimming chased that before anyone read
the loop. **When you add bookkeeping to a placer, check whether it consumes its work-list or indexes
it** - and if a correction loop is not converging, suspect the measurement before the geometry.

## RANDOMNESS IS POSITIONAL OR SCOPED - never "wherever the stream happens to be"

The rule, and it governs every new draw you add: **a feature's randomness must depend on the feature,
not on how much randomness the map has drawn before it.** Two mechanisms, and one of them fits every
case.

- **A per-feature attribute** - a house's rake, its wall color, whether it has a kura, which kind a
  ring seat gets - comes from **`self._hjit(x, y, salt)`**, which is a deterministic hash of the
  position. Its docstring has said why since it was written: "so it never ripples other placement or
  household counts". Pick an unused salt (1.0, 2.0, 3.0, 7.0, 11.0, 13.0, 21.0, 22.0 and 0.7/1.3/2.1
  are taken; `_quad` owns 71.0+).
- **A phase or a region** - a pack's seat jitter, a pasture's outline, a grove's crowns, a well grid,
  a ring's candidate seats - runs inside **`with self.rng_scope(name, *key)`**, whose stream is a hash
  of (map seed, name, key) and which restores the outer stream on the way out. Key it on the thing
  that identifies the instance: the bbox, the street run, the base polygon. Repeat calls on one key
  get their own numbers via a per-key counter, so two packs over the same ground do not twin.

**WHY (GM 2026-08-08), measured.** Everything drew from one global stream, so any change that altered
the NUMBER of draws made before a phase re-rolled that phase however unrelated it was. Injecting ONE
extra draw at the top of a gen and diffing every manifest key:

| tier | before | after |
|---|---|---|
| hamlet, village | 2 of 63-69 keys | **0 - isolated** |
| town, city | 12-15 of 71-101 keys | see below |

The cost was not theoretical. A caption resize in a city's temple quarter dropped a farm shed on a
garden **700 px away**, and the session that fixed it spent most of its time on maps it had not
meant to touch. Debugging a map you did not change is the expensive kind of work.

**HOW TO FIND THE NEXT ONE, because the method matters more than the list.** Run a gen twice - once
normally, once with one extra `random.random()` injected at `meta()` - and diff. Two probes, in this
order:

1. **Record-level**: for each manifest key, the first index whose record differs, and which FIELDS
   differ. `fields=['rot']` on the same x/y is an ATTRIBUTE drift (positional fix). A different x/y
   is a SEAT drift (scope the placer).
2. **Draw-site level**: wrap the `random` module functions to log the calling `file:line`, and find
   the first index where the two SEQUENCES disagree. That names the culprit exactly.

Use (1) first. Once the scopes are in, (2) starts reporting *consequences* - a grove whose crowns
differ because the buildings around it moved - and will send you chasing the wrong thing.

**Every one of these changes re-rolls the whole pool once**, so batch them: convert everything you
intend to, THEN regenerate and fix the fallout in one pass. Fixing fallout between conversions is
work you will throw away, because the next conversion produces a different fallout set.

## ROUTING A WAY THROUGH GROUND THAT IS ALREADY FULL

Feature 123's lane web needed paths from outlying steadings to the network, and got there by three
successive answers, only the last of which works. Recorded because the first two look reasonable.

**A straight run, then a straight run plus fixed dog-legs.** Fails in both directions and for the
same reason - a fixed offset is not a length that means anything. 40/80/130 ft is a gentle correction
on a 300 ft path and a switchback on an 80 ft one, and a review caught the switchback: 271 ft of path
to join two points 77 ft apart, folded back through a windbreak. Scale the bend to the CHORD if you
try this, and bound directness (a path may not exceed ~2x its own straight line; every honest way on
these maps measures 1.00-1.34).

**A lattice router, string-pulled.** This is the one that works, and two details are load-bearing:

- **A diagonal may not cut a blocked corner.** Two cell centers can both be clear while the step
  between them clips the corner of a steading standing between them. Require both orthogonal
  neighbors on a diagonal move, or the planner "finds" routes that are not walkable and they fail
  their own acceptance test a moment later - which reads as a mysterious rejection, not as a
  planning bug.
- **String-pull at the clearance the lattice PLANNED with.** Validating shortcuts more strictly than
  the route was planned refuses every shortcut and leaves the raw lattice chain, whose diagonals then
  clip the corners the cell centers had cleared. One number, used by both.

**The lattice is an INDEX, not a decision** - the standing rule in this file's performance section
applies verbatim. Every shortcut is re-tested against the real geometry before it is taken, so the
drawn path is exactly as legal as one drawn by hand; the grid only proposes.

**And prefilter.** The clearance predicate gets called once per lattice cell per candidate per
target, and unprefiltered it scans every polygon in the settlement's fabric each time. That took a
hamlet from 15 s to 45 s and killed a cohort worker outright. A bounding-box test against the
polyline's own bounds prunes it; it never decides.

## A REPAIR PASS MUST RUN AFTER THE THINGS IT REPAIRS

Three ordering bugs in one feature, all the same shape, all silent. Writing the shape down because
fixing it three times separately is what a session does when it has not noticed the pattern.

1. **The lane web ran before the houses.** It reserved ground from a cluster that had not been packed
   yet, so it competed with the very houses it existed to serve - the four pool clusters' long axes
   grew 15-97%. No check measures sprawl, so nothing said a word.
2. **The web ran before the appurtenances.** Its corridor reserved courtyard ground ahead of the byre
   placer and exiled byres up to 210 ft, erasing a previous feature's borrow-coverage fix.
3. **The orphan-join ran before the bridges and the footpaths.** On cohort seed 39 it saw FOUR of the
   twelve lanes the map finishes with, found nothing to join, and the eight lanes added after it
   formed a second network of their own. Every house on that map is within 86 ft of a lane and twelve
   of them still counted as unreached, because the lane serving them was not on the connector's
   network.

**The rule.** Sort every stage into one of three kinds and place it accordingly:

- **RESERVES ground** (a no-build corridor the houses pack around) - runs BEFORE placement.
- **FILLS ground left over** (the lane web, ground cover) - runs AFTER placement, reading the drawn
  features as obstacles.
- **REPAIRS what the others produced** (joining orphans, closing breaks, trimming stubs) - runs LAST,
  after every pass that can create the thing it repairs. If a repair pass can be invalidated by a
  later stage, it either moves after that stage or runs twice.

**Why it stays silent.** Each of these produces a map that draws fine and gates green on everything
except the one rule that happens to measure the consequence - and two of the three had no rule at all
until this feature added one. The failure signature is a check firing on a map whose ink looks
correct: that is usually an ordering problem, not a geometry one.
