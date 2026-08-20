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

## 2b. The packer must RESERVE ways, not merely avoid collisions - DEFERRED WITH MEASUREMENT
(2026-08-18, feature 125. Deferred under constitution Principle XIV's named exception - it is a
stage-reordering / new-reservation-stage change - and this entry is the deliverable that deferral
owes: the measurement, the mechanism, the sketch, and the alternatives already priced and declined.)

**The symptom.** `farmhouses_reach_a_way` fails on cohort seeds 5, 8 and 25 - 2, 2 and 4 farmhouses
standing 172-237 ft from any way. It is the entire non-peer residue of the 48-seed sweep (43/48).

**What it is NOT**, each ruled out by measurement rather than by argument:

- Not a CONNECTIVITY split. The main component equals the full lane set on all three seeds
  (`lanes 7 main 7`, `10/10`, `8/8`), unlike seeds 39 and 9 earlier in the same feature, which were
  component splits and were fixed as such.
- Not the straggler pass giving up early. It produced 391-1,572 candidate runs PER stranded house.
- Not the acceptance criteria being too strict. Of those thousands of runs, every single one met the
  network (`net = 0 ft`, bound 30) and every single one was perfectly direct (`1.00`, bound 2.0).
  What failed was reach: the best run came within 132, 167, 173 and 210 ft of the house it was drawn
  for, against a 100 ft bound. The runs are fine; they are just nowhere near the house.
- Not the router's lattice resolution, though the arithmetic is seductive. `_route` inflates its
  planning clearance to `gap + cell * 0.71` so a free cell means every point in it is clear - 11.1 ft
  at the default 10 ft cell, i.e. it demands a 22 ft corridor for a footpath, while `MIN_WEB_GAP` is
  18. Measured end to end at a 5 ft cell (7.6 ft clearance): **the unserved count did not move**, and
  seed 5's build went 159.9s -> 672.3s, a 4.2x. Reverted; the dead end is recorded at the call site
  in `hamletgen/ways.py` so nobody pulls that lever twice.

**RETRACTED: IT IS NOT A CRESCENT DEFECT.** I reported the correlation below as the strongest result
of the day and it is confounded. `plan.cluster_shape` feeds exactly one thing - `cluster_seeds`, the
CLOUD pass - and the cloud runs only for households the front rows do not seat. Measured on eight
crescent seeds including all three failures: **every one seeds by `frontage`, the cloud never runs,
and `meta.cluster_shape` is stamped on none of them.** A knob that is never read cannot cause a
failure. A sixth fix attempt confirmed it from the other side: softening the crescent bow from 0.50 to
0.30 changed nothing at all, because the code path is dead on these maps.

The arithmetic was never strong either, which is the lesson worth keeping. Three failures landing
inside seventeen crescents out of forty-eight seeds is p ~ 0.04 - suggestive, not decisive - and I
treated it as decisive because it arrived after four failed attempts and I wanted a lead. The base
rate check I ran on `out < 0` (90 of 128 seats) is the one I should also have run here: ask what
fraction of the population looks like the signal BEFORE calling it one.

**A real defect fell out of the retraction, though.** `cluster_shape` is rolled per settlement, is
reported in the cohort audit's header for every seed, and on the evidence above is honored on NONE of
them - the front rows plus lane frontage seat every household, so round, elongated, crescent and split
all draw the same cluster. `homesteads.py` already carries a known-open note about the shape leaving no
trace when the cloud does not run (Kashikawa, 2026-08-16); what is new is that this looks like the
NORMAL case rather than an edge one. It belongs with `plot_regularity` in 2e: four `meta` lines that
read as variance the pool is not spending. Worth a census across all 48 seeds before anything is
built on the shape knob.

**The observation below stands as an observation only** - the three failing seeds happen to be
crescent-rolled, and that fact is now known to be a coincidence of the seed roll rather than a cause:

**IT IS A CRESCENT DEFECT, and that is the sharpest thing known about it** (measured 2026-08-19,
and it took three failed spacing fixes to go looking). Across all 48 cohort seeds:

| cluster shape | seeds | reach failures |
|---|---|---|
| crescent | 17 | **3** (seeds 5, 8, 25) |
| round | 21 | 0 |
| elongated | 10 | 0 |

**0 of 31 non-crescent seeds fail.** Every stranded house also sits on the same side of the seat band:
`out` between -50 and -147 against served houses at `out` >= +32, i.e. on the far side of the anchor,
in the arm the crescent wraps around.

And the web's coordinate frame is NOT the problem, which rules out the obvious follow-up: projected
onto the margin frame the stranded houses land at **stand 46-57 inside a 42-273 stand range**, and at
arcs inside the frame's own 521-1052 span. The back-lane cuts and their extents therefore RUN ACROSS
these houses - the line is drawn over them and then clipped out by the fabric it cannot pass, which is
the same 1.4-1.9 ft corridor measured below. (An earlier crescent fix widened the frame ALONG the arc
for exactly this class of failure - `ways.py` records it, worst house 431 ft - so widening it again is
not the answer; the frame already reaches.)

So the shape of the real defect is: **a crescent's inner arm packs against itself, and only there.**
Whatever a post-pack repair does, seeds 5, 8 and 25 are its test bed and the other 45 seeds are its
regression bed - and any fix that does not distinguish the crescent's inner arm from the rest of the
cluster is spending disruption across 48 maps to fix 3.

**A FIFTH attempt, and a CORRECTION to my own reasoning above.** Having found that the stranded
houses sit at `out` -50..-147 while served houses sit at `out` >= +32, I filtered those seats out of
`front_row`. Cohort: 43/48, the same five seeds. Then I measured what I should have measured first:
**90 of 128 front-row seats offered on seed 8 are at out < 0.** The split I had treated as a signal
has a base rate of 70% - I compared the stranded houses against the SERVED ones and never asked what
fraction of all offered seats look like that. The inference was unsound and the number is not evidence
of anything on its own. (What the filter does do is work: with it, front_row offers 0 of 97 negative
seats and all 11 households still place - so this is a wrong conclusion, not a broken edit.)

What the fifth attempt DID establish is worth more than what it disproved: with those seats removed
from `front_row`, the same households are seated in the same region by the CLOUD pass, and the same
three seeds fail with houses at the same distances. **So no seat GENERATOR is the culprit.** The seat
BAND itself extends over ground the way network cannot serve, and every generator that draws from the
band inherits it. That is why five attempts aimed at spacing, at the slide, and at one generator have
each moved exactly nothing.

**RETRACTED A SECOND TIME, AND THIS ONE INVALIDATES THE WHOLE ENTRY BELOW: THERE IS PLENTY OF ROOM.**
The "1.4-1.9 ft corridor" measurement that this entry is built on, and that justified all six fix
attempts, is an artifact of how I measured it. I walked outward from each house CENTER and took the
clearance to ALL fabric - which includes the steading's OWN house, yard and garden. Every farmhouse on
every map is surrounded by its own bundle by construction, so that measurement returns a ~1.5 ft pinch
for a house standing alone in an empty field. It says nothing about whether a way can reach it.

Re-measured with the steading's own bundle excluded, which is what the straggler pass itself does:

| house | corridor, all fabric | corridor, own bundle excluded |
|---|---|---|
| seed 5 (1262, 848) | 1.4 ft | **119.6 ft** |
| seed 5 (1130, 839) | 1.7 ft | **68.1 ft** |
| seed 8 (1612, 646) | 1.9 ft | **63.5 ft** |
| seed 8 (1584, 742) | 1.8 ft | **69.7 ft** |

A footpath needs about 11. **So the ground is wide open and this is not a packing defect at all** - which
is why every spacing lever moved nothing, and the six null results should have made me re-examine the
premise long before I re-examined the levers. The failure is in the footpath logic, and it is a bug
rather than a physical impossibility: 60-120 ft of clear ground and the pass still leaves the house
unserved.

**TWO MORE ATTEMPTS AND WHAT THEY ESTABLISHED** (2026-08-19, attempts seven and eight, both reverted):

- **A seat-time reachability test, straight-line form** - refuse a seat whose line back to the
  cluster's middle crosses crop. **42/48**, adding a `bridges_span_their_water` and a `field_ringed`
  failure while fixing none of the three seeds. The proxy is wrong in an instructive way: the line from
  a seat to the cluster's middle can miss the paddy entirely while every route to a WAY still crosses
  it.
- **The same test done properly** - one flood fill per map over a 24 ft grid, marking the dry ground
  walkable from the cluster's middle, then refusing seats outside it. **43/48**, and it did not exclude
  a single stranded house. **That is the load-bearing result: those houses ARE inside the walkable dry
  region.** They are not cut off and they are not sealed in. The way network simply never extends round
  to their margin, and the footpath router's search box never spans the detour that would reach them.

So the defect is not the packer, not the seat generators, not the seat band, and not the ground. It is
that no way is ever DRAWN on the far margin, and nothing searches far enough to connect one.
(`_route` also cannot be brute-forced into finding it: it caps its lattice at 90,000 cells, so a
search box wide enough to go round a field returns empty by construction rather than by geometry -
worth knowing before anyone tries simply enlarging `pad_mult`.)

**THE ROUTER CANNOT ANSWER THIS QUESTION AT ALL, and that is a design constraint on the fix rather
than a fact about the ground.** I tried to settle "is there a lane-width corridor round the field?" by
running `_route` at every combination of resolution and box size. Every one returns none - and the two
ends fail for OPPOSITE reasons, which is what makes the tool unusable here rather than the answer no:

- **Fine cells cannot span the detour.** `_route` caps its lattice at 90,000 cells, so a box wide
  enough to reach round a field returns empty by construction. pad_mult 8 and 20 are refused before
  any geometry is examined.
- **Coarse cells cannot fit the gap.** The planning clearance is `gap + cell * 0.71`, so a 40 ft cell
  demands a **64 ft corridor** for a footpath that needs 11. At that size it would refuse a village
  street.

There is no setting where both hold, so the router can neither confirm nor deny a way round. (The
flood fill says the dry GROUND is connected; the router says nothing, because it also counts fabric
and cannot be run at a scale where its own clearance is honest.)

**So the fix may not ask the router where the way goes.** A shape-aware skeleton has to PLACE the way
from the geometry it already has - the field margin, which `_margin_frame` already follows all the way
round - and then let clipping decide what survives, exactly as `stage_ways` does for the skeleton
today. Any design that says "search for a route to the stranded house" runs into the wall above.

**AND THE LEDGERED CANDIDATE WAS BUILT AND MEASURED TOO - it does not work as stated.** A
`_serve_far_margin` pass was implemented exactly as the entry proposes: for a house still unserved,
lay a SHORT run at its own frame position (arc +/- one bundle pitch at its own stand), placed from
geometry rather than searched for, then let the join and bridge passes connect the island.

- Run BEFORE the repair passes it is a disaster - **17/48**, with 23 seeds failing
  `lanes_reach_something`, because it fires for houses the bridges and footpaths were about to serve
  and every speculative run is a tread fronting nothing. (An ordering error, and the same lesson
  feature 123 already paid for: a repair pass must run after the things it repairs.)
- Run AFTER every repair, firing only for houses still unserved, it is **43/48 - exactly baseline,
  fixing nothing**, because no run survives clipping to be laid.

Then the decisive measurement: at the stranded houses' own arcs, a margin line of +/- one bundle pitch
yields **no clear run at ANY stand offset (0, +40, +70, -40 ft) and at either clearance** (the web's
7 ft or the footpath's 4 ft). Nothing is drawable along the margin there at all.

Put beside the 60-120 ft of open ground measured around those same houses, that says the open ground is
**not aligned with the margin** - the frame's arc direction at those points heads into the paddy, even
though `frame(project(house))` returns the house itself to within 0-28 ft. So a shape-aware skeleton
that follows the MARGIN will not reach them either. Whatever serves these houses has to be oriented by
the local dry ground rather than by the field edge, and nothing in the engine currently computes that.

**ATTEMPTS TEN AND ELEVEN, and a FOURTH correction to my own measurements.**

- **Ten: a bearing scan.** For a still-unserved house, scan 36 bearings from the door, take the
  direction whose corridor is genuinely open, lay a run down it. **43/48 - baseline, fixing nothing.**
- **The correction that explains it.** The "60-120 ft of open ground beside each stranded house" that
  motivated attempt ten measures clearance to FABRIC ONLY and ignores crop entirely. That open ground
  is largely the flooded paddy. Fourth instance in one day of the same error: a measurement that
  cannot tell the failing case from a healthy one. (An erosion test has the mirror flaw - it says the
  dry ground stays connected at a 20 ft erosion radius, but it counts only crop, so it is answering
  about mud, not about where a way can run.)
- **Eleven: ONE map-wide walk instead of a bounded search** - a single BFS over the whole map at 8 ft
  cells, blocked by crop at `WEB_HARD_GAP` and by fabric at `FOOTPATH_FABRIC_GAP`, seeded from every
  drawn way, then the gradient walked back from the nearest reachable cell and string-pulled. This is
  the one design the router structurally cannot express, and the diagnostic behind it is the most
  encouraging result in the whole entry: **on seed 5, three of four unreachable farmhouses have a
  genuinely walkable path 248-360 ft long that no bounded search can see.** Built as a lazy last-resort
  pass (3 cohort seeds in 48 ever build the grid): **41/48, neutral - it fixed none of the three.**

Why eleven did not land, for whoever picks it up: the reachable cells sit 90-100 ft from the house,
right at the `WEB_REACH_FT` bound, and the run has to survive `_reach(house, run) <= 100` after a
string-pull at footpath clearance. So the path exists, is found, and is then rejected or trimmed at
the last step. That is a much smaller gap than anything else in this entry - **the next session should
start by instrumenting what happens to those found paths between the walk and `_draw_web`**, not by
inventing a twelfth approach.

**A NOTE ON THE MOVING BASELINE.** Three sessions were writing to this tree while these attempts ran,
and the cohort moved twice underneath them (a cluster-shape binding, then field bund/seam work). The
43/48 figures above and the 41/48 ones below are against DIFFERENT tips. Per-seed reach behavior on
5, 8 and 25 was stable throughout, which is why the attempts remain comparable; nothing else in the
residue is.

**TWELVE: the walk with its selection bug fixed - and the result that ENDS this line of attack.**
Attempt eleven chose the reachable cell nearest the NETWORK; it should choose the one nearest the
HOUSE, or the path lands where the network already is and fails its own reach test. Fixed, plus a
second input bug of the same family (the pass was handed `walls`, every fabric polygon, where a
footpath's obstacle set excludes grazing commons and tree belts). **41/48 both times - no reach seed
moved, and it introduced a `fields_clear_of_road` failure of its own.**

**WHY NO WAY-DRAWING PASS CAN EVER FIX THESE THREE SEEDS.** The gate fails a SEED if any one of its
houses is unserved, and the instrumented walk splits the eight stranded houses cleanly:

| seed | stranded houses | have a walkable path | have NONE |
|---|---|---|---|
| 5 | 4 | 3 (reach 32, 51, 78 ft against a 100 ft bound) | **1** |
| 8 | 2 | 0 | **2** |
| 25 | 2 | 0 | **2** |

**Five of the eight have no walkable cell within 110 ft at any clearance a footpath needs.** No path
exists to be drawn, so no pass that draws paths - the web, the bridges, the joiners, the stragglers, a
margin pass, a bearing scan, a map-wide walk - can serve them. And because one unserved house fails
the whole seed, serving seed 5's three changes the cohort by nothing. That is why twelve attempts
produced twelve null results: they were all the same kind of answer to a question that is not about
drawing ways.

**SO THE FIX IS AT SEAT TIME, and my two attempts at that were both testing the wrong thing.** Attempt
seven (line to the cluster crosses crop) and attempt eight (flood fill over dry ground) BOTH counted
only crop. The houses that cannot be reached are blocked by FABRIC - other steadings - not by water,
which is why a crop-only test cleared every one of them. A seat-time test has to ask what this walk
asks: is there a corridor at footpath clearance, counting the steadings already placed?

That is harder than it sounds and is the real content of the remaining work: fabric does not exist yet
when seats are chosen, since houses are placed one at a time. So the test must be INCREMENTAL - when
seating house N, is it still reachable given houses 1..N-1 - and a full BFS per candidate seat is far
too expensive (hundreds of candidates per map, a six-figure cell count each). Finding a cheap
incremental reachability test, or a placement order that cannot strand, is the feature.

**THIRTEEN: the incremental seat test the twelve pointed to - and the reason a seat-time filter
cannot work at all.** The design was sound on paper: a whole-cluster reachability test cannot be asked
while houses are placed one at a time, but if every seat can walk to one ALREADY STANDING then the
cluster is connected by induction, and the per-candidate cost is one line rather than a flood fill.
Both forms were measured:

- **Line form (does the walk to the nearest standing steading avoid the crop): 41/48, same seeds.**
- **Width form** (the samples must CLEAR the crop by two footpath clearances plus a tread, since a
  line with no width threads a one-foot gap between basins that nobody can walk): **41/48, same
  seeds, plus a `houses_clear_of_lanes` failure of its own.**

**And the null result explains itself.** The chain test counts CROP, and these houses ARE crop-connected
to a neighbor - they sit beside other steadings. What leaves no corridor is the FABRIC: the neighbors'
yards and gardens fill the gaps. But a fabric-aware chain test cannot work either, and not for want of
tuning: every seat is adjacent to its neighbor's own yard by construction, so counting fabric refuses
almost every seat on every map.

**That is the real shape of the problem, and it rules out the whole seat-time family**: whether a way
can reach a steading depends on the FINAL fabric, and no test asked while the fabric is still being
laid can know it. Ignore fabric and the filter is too permissive (measured, three times); include it
and it is too strict (by construction). So the remaining design is a POST-placement repair - place as
now, then find the houses no way can reach and RE-SEAT those two or three - which needs the ability to
remove a placed bundle and re-place it, something the engine cannot currently do. That is the feature,
and it is bigger than any of the thirteen attempts here.

**FOURTEEN AND FIFTEEN: re-roll the map with the unservable ground forbidden - the last mechanism,
and the most informative failure of the fifteen.** The engine cannot remove a placed bundle, but
`generate` already gates in-process, so a map that strands a farmhouse can simply be BUILT AGAIN with
that ground refused by the seat loops (`unreached_houses` mirrors the gate's own reach and its 40 ft
notion of connected, so the retry forbids exactly what the rule condemns).

It works, partially, and that is what makes it worth recording:

- **One round re-seats every household and takes seed 5's stranded count from 9 to 2.** Not zero, so
  `farmhouses_reach_a_way` stays red - and a retry scored on CHECKS FAILED therefore discards its own
  progress, which is a trap worth naming.
- **Scored on houses stranded instead, and iterated up to four rounds with the forbidden ground
  accumulating** (a steading moved off one pocket must not be seated back onto an older one):
  **41/48, the same three seeds.** It converges toward a floor it never reaches. Seed 8 went 3 -> 4 on
  one round and seed 25 stayed at 12.

**SIXTEEN: the band aspect, now that it is a LIVE knob** (the hamlets session bound
`CLUSTER_BAND_ASPECT` per shape on 2026-08-19, which is what makes this different from attempt six -
that one moved the crescent BOW in `cluster_seeds`, dead code on every one of these maps). All three
failing seeds are crescent, so the band is the one upstream lever left that does not need a GM ruling.
Measured on seeds 5 / 8 / 25, houses stranded:

| crescent aspect | seed 5 | seed 8 | seed 25 |
|---|---|---|---|
| 3.0 (shipped) | 9 | 3 | 12 |
| 2.6 | 9 | 7 | 11 |
| 2.2 | 4 | 6 | 11 |

**No value reaches zero on any seed**, and what helps one hurts another - 2.2 more than halves seed 5
and doubles seed 8. This tests directly the "a band that does not wrap onto an unservable margin"
option listed below as a remaining possibility, and closes it: reshaping the band redistributes which
houses are stranded without making the ground servable.

**SEVENTEEN: the garden/yard SIDE, which is the only lever that changes what a footpath must CROSS
rather than where it starts.** The bundle picks its garden side by shading alone, ties broken by a
fixed preference order - so nothing ever asked whether the garden and yard end up BETWEEN the steading
and the rest of the cluster, which is precisely the fabric a path cannot cross. A tiebreak preferring
a side that leaves the cluster-ward approach open (sun still deciding first, so no bed loses light):
**seeds 5 / 8 / 25 measured 10 / 3 / 12 stranded against a 9 / 3 / 12 baseline** - seed 5 slightly worse, the other two unmoved. Reverted.

**ONE HYPOTHESIS TESTED AND REJECTED, recorded so nobody assumes it:** that the cohort's household
counts come from a TEST-HARNESS formula (`10 + (seed * 7) % 11`) rather than anything researched, so
the failing seeds might simply ask more households than their ground can seat servably. They do not.
The three failures sit at 11, 12 and 20 households, and every count from 10 to 20 appears 4-5 times
across the 48 seeds with no other failure at any of them. The ground is not over-subscribed and the
harness is not asking for the impossible; two hamlets of 20 households pass while seed 25's fails.

**READ THIS BEFORE TRUSTING ANY "N STRANDED" NUMBER IN THIS ENTRY. The proxy those numbers come from
is WRONG, and it steered three of the attempts** (found by the hamlets session, 2026-08-20, from a
single line in one of my status messages). I measured "houses stranded" with a hand-rolled helper that
re-implements `farmhouses_reach_a_way` - union-find over lanes at a 40 ft join, then distance to the
connector's component. Validated against the gate at last, on six seeds:

| seed | my proxy | the gate |
|---|---|---|
| 5 | 6 | reach RED - agrees |
| 8 | 3 | **reach PASSES** |
| 25 | 8 | **reach PASSES** |
| 2 | 4 | **reach PASSES** |
| 13 | 5 | **reach PASSES** |
| 40 | 8 | **reach PASSES** |

**It over-counts on five of six, and never reads zero even on a clean map.** So:

- **Attempt 16's band-aspect table is void.** Its whole conclusion was "no value reaches zero on any
  seed" - and the instrument cannot read zero. That lever is NOT ruled out; it is unmeasured.
- **Attempts 14 and 15 scored a retry loop on it**, deliberately switching from checks-failed to
  houses-stranded. The loop's accept/reject decisions were driven by a number that does not track the
  rule, so "converges to a floor it never reaches" is unsupported.
- **Attempt 17's verdict (10/3/12 against 9/3/12) is a one-house difference** on an instrument with
  this much drift, which is noise.

The tally "seventeen attempts, none moved it" is therefore softer than it reads: fourteen stand,
three rest on a broken instrument. This is the project's own rule about diagnostics - *a diagnostic
OBSERVES, it never restates* (`tools/CLAUDE.md`) - broken by me, in the way that doc predicts: I
re-derived a rule instead of calling it, and it drifted. **The remedy is one line: assert the proxy
agrees with `gate` on a handful of seeds before quoting it.**

**A SECOND `trim_lane_stubs()` AFTER THE REPAIR PASSES IS CATASTROPHIC - measured 43/48 -> 9/48, with
37 seeds failing `farmhouses_reach_a_way`.** It looks obviously right (the trim runs BEFORE the
repairs, so nothing cleans up after them, and a repair-laid link that ends up reaching nothing keeps
its full length). It is not: the trim's own rule is "this end reaches no way within 40 ft and no
farmhouse within 90", and a freshly drawn LINK routinely has an end just outside that - it is the join
itself. Trimming after the repairs therefore eats the connections the repairs exist to make. If a
repair-laid tread needs cleaning up, it needs a targeted pull-back that knows the lane is a join, not
the blanket trim.

## 2b-i. THE SKELETON MUST FOLLOW THE MARGIN - a working partial, 2 of 3 seeds, NOT shipped
(2026-08-20. This is the closest anything has come to the reach residue in eighteen attempts, and it
came out of the GM's question about placement ORDER. It is written up in full because it WORKS and is
held back only by two failures it exposes elsewhere - Principle XIII, no new regressions.)

**THE DEFECT.** `stage_ways` builds the cluster's internal lanes with `skeleton_layout` (a spine, a T,
a Y, a cross - straight lines in a local frame) and maps them to screen with `to_screen`, which is a
LINEAR map through the seat band's fixed `along`/`out` axes. So the skeleton follows the margin's
DIRECTION but not its CURVATURE: on a cluster seated where the field edge bends, the "spine along the
margin" is a straight chord across a bent band, it leaves the margin, and the far arm of the band gets
no lane at all. That is where the unreachable farmhouses stand. `_margin_frame` exists for precisely
this and says so in its own docstring - *"the margin CURVES, so anything meant to run parallel to the
field has to be built on the edge itself rather than ruled straight across it"* - and the lane WEB
already obeys it. The skeleton never did.

**THE CHANGE** (three lines, in `stage_ways`, replacing the `_raw_arms` construction):

    _sk_frame = _margin_frame(plan, max(seat["lat"] * CLUSTER_SPAN_FACTOR, seat["lat"] + BUNDLE_PITCH))
    _sk_arc0, _sk_stand0 = _sk_frame.project((cx, cy))

    def _on_margin(p):          # local +x runs along the band, local +y toward the field
        return _sk_frame(_sk_arc0 + p[0], _sk_stand0 - p[1])

    _raw_arms = [[_on_margin((p[0], p[1])) for p in lane_pts] for lane_pts in layout["lanes"]]

`_margin_frame` takes `near=()` by default, so it can be built at stage 4 before any house exists.

**WHAT IT DOES.** Cohort 43/48, same total as baseline, but the composition moves:

- **seed 8: reach RED -> PASSES.**
- **seed 25: reach RED -> PASSES.**
- seed 5: still red (2 houses, worst 287 ft).
- NEW: seed 14 `captions_clear_the_ways_they_stand_on` (a caption 5 ft from a lane tread), seed 26
  `lanes_reach_something` (a 171 ft web lane whose far end stands 59 ft from any way, 156 ft from any
  house).

**WHY IT IS NOT SHIPPED.** Two new failures is a regression whatever else the change fixes. Both look
like consequences of arms now curving rather than deep problems, and both resisted the obvious cures:

- A second `trim_lane_stubs()` after the repair passes: **43/48 -> 9/48**, 37 seeds losing reach,
  because the trim's rule ("this end reaches no way within 40 ft") eats the freshly drawn LINKS that
  are the joins themselves.
- Guarding the straggler end-trim so it cannot undo its own acceptance (real bug, kept in spirit but
  it is not seed 26's cause): no change to the residue.
- Trimming a web lane's FAR end to service inside `_lay_web_lane` (its acceptance requires only ONE
  end to join, so the other is free to stop anywhere): no change to the residue.

**WHERE TO PICK IT UP.** Seed 26's lane is drawn by `_lay_web_lane` from `stage_web` - traced, not
inferred - so it is laid BEFORE `trim_lane_stubs` and the trim should already be catching it; find out
why it does not. Seed 14's caption is the kosatsuba, whose seat ladder now scores against curved
treads. Fix those two and this lands, and it is worth landing: it is the only change in eighteen
attempts that has moved a reach seed at all, let alone two.

**THE ORDERING LEAD, and it is the GM's, not mine (2026-08-20).** Asked why the map could not simply
be made larger, and whether the real issue was placement ORDER. Both halves land:

- **The map is NOT size-limited.** `canvas_for` errs deliberately large and `crop_to_content` throws
  the unused canvas away. "Fewer households" was never about running out of room, and my having
  offered it as an option came from my conclusion rather than from the code.
- **`STAGES` lays the field BEFORE the ways and the houses.** The settlement takes whatever margin the
  field leaves it - so where that margin turns, the cluster turns with it.

Measured, field-edge turn across the cluster band: **seed 5 = 111.4 deg, seed 25 = 112.9 deg**, against
**0.2-10.5 deg on eight passing seeds**. Two of the three failing seeds seat their cluster on a CORNER
of the field; every passing seed measured sits on a nearly straight margin. (Seed 8 is 1.2 deg and does
not fit, so this is a mechanism for two of three, not a single cause.)

That reframes the entry below. "The ground admits no servable arrangement" is too strong and is
withdrawn: the ground is chosen by an earlier stage that does not know a settlement is coming. The
honest statement is that GIVEN the field as laid, the placement produces stranded houses and none of
seventeen searches found a servable arrangement - and my own re-roll attempt taking seed 5 from 9
stranded to 2 was evidence against impossibility that I reported as impossibility anyway. Fifth
over-claim of the session, same shape as the other four.

**Where a session should start on this**: `seat_cluster` chooses the cluster anchor by scoring outline
segments, with no term for how much the edge TURNS across the band it is about to occupy. Adding one -
prefer a straight margin, refuse a corner - is a bounded change in `cluster.py` and is aimed at the
two seeds the measurement explains. It is untried.

**THE TERMINAL RESULT.** Fifteen attempts across every mechanism the engine offers - four on spacing
and packing, three on drawing ways (margin runs, bearing scans, a map-wide flood), four on seat-time
filters (crop line, flood fill, chain, width-aware chain), two on re-rolling with ground forbidden, and
two on vetoing a crossing - and not one moved seeds 5, 8 or 25. Taken together with the measurement
that five of the eight stranded houses have NO walkable cell within 110 ft at any footpath clearance,
the conclusion is not "we have not found the trick yet". It is that **on these seeds the field shape,
the cluster band and the household count together admit no arrangement in which every household is
servable under the current rules.** Something upstream has to give: fewer households on that ground, a
band that does not wrap onto an unservable margin, or a field whose far side is not cut off. All three
are generator-design decisions, not lane or placement bugs, and all three are the GM's call rather than
a fix to slip in.

**The candidate that fitted every measurement until it was built**, ledgered jointly with the hamlets session: make the LANE
SKELETON shape-aware, so that a cluster wrapping a field gets a way on the margin it wraps onto,
instead of a skeleton laid independently of the band. It is the first idea in eight attempts that
addresses the geometry rather than a symptom.

**Where a session should start**, given the straggler pass produces 391-1,572 candidate runs per house
that all meet the network at 0 ft and are all perfectly direct at 1.00, while the best of them comes no
closer than 132-210 ft to the house it was drawn for: the runs are being CLIPPED at the house end.
`clear_runs` clips the drawn tread against `others`, which includes the steading's OWN yard and garden,
while the door search and the router use `passable`, which excludes them. That asymmetry is deliberate
and documented - the yard is private ground the household crosses on foot - but it means the tread can
only begin outside the steading's own bundle, and something is pushing that start far further out than
a yard's width. Measure where the surviving run actually starts and what clipped the stretch before it.

**Everything below this line was written under the wrong premise.** It is kept because the six attempts
and their numbers are still true as records of what does NOT change these maps, and because the
reasoning error is the most useful thing in the entry: I measured a quantity that could not distinguish
a sealed block from an ordinary farmstead, and then built six experiments on it.

**What it IS.** The homestead packer's only inter-bundle rule is that two bundle bboxes must not
overlap, with two PIXELS of tolerance (`_bundle_side_fits`, the closing `all(...)`). So a run of
steadings packs into a solid mass. Measured on the stranded houses: the widest escape corridor across
**all 72 bearings** pinches to **1.4-1.9 ft**, and the straight line to the nearest way pinches to
**0.1-1.1 ft**. A footpath needs about 11 (two `FOOTPATH_FABRIC_GAP` clearances plus its tread). These
houses are not far from a way by accident of layout: **no way can be drawn to them at all**, which is
exactly why the straggler pass generates thousands of impeccable runs that are all in the wrong place.
There IS clear ground 10 ft from each front door - it simply goes nowhere.

**The alternative already priced and DECLINED: a uniform minimum gap between steadings.** The obvious
fix is to make the packer keep `n` feet between neighboring bundles' solid parts (groves excluded, so
they still merge into one windbreak, and a footpath crosses grove and commons freely anyway). It was
built, opted into by the scripted tier the way `sun_corridor` is, and measured on the full cohort:

| | passes | reach | windbreak | other |
|---|---|---|---|---|
| baseline (no gap) | **43/48** | 3 | 1 | harvest 1 |
| 18 ft gap (`MIN_WEB_GAP`) | **37/48** | **3 - the same three seeds** | 5 | harvest 1, bridges 1, lane-ends 1 |

It fixed **nothing** and cost **six** new failures. A 12 ft gap was measured too and is no better
(seed-level 1/3/2 against a 2/2/2 baseline, which is rotation, not improvement - the rule re-packs the
map, so the houses are not the same houses and only the cohort rate means anything). The lesson is
that inflating every gap uniformly does not put a way where one is needed: it loosens the whole
cluster, moves the pinch somewhere else, and breaks the belt and the bridges on the way past.

**THE OBVIOUS SKETCH IS ALREADY MEASURED AND ALREADY FAILED - read this before proposing it again.**
The natural fix is "reserve corridors across the cluster before the homesteads pack, and let the
packer treat them as keep-clear the way it treats a paddy". That is feature 123's FIRST attempt, and
`stage_web`'s own docstring carries the numbers: given a normal corridor it pushed the houses outward
and the four hamlets' long axes grew **51%, 58%, 15% and 97%** - sprawl no check measures - and given
a narrow one **the houses collided with it instead**. The web was moved to run AFTER the houses for
exactly this reason. I wrote the reservation sketch into this entry on 2026-08-18 without having read
that docstring, and it is wrong; it is corrected here rather than deleted, because a plausible fix
that has already been measured as failing is precisely the thing a later session will otherwise spend
a day rediscovering.

It also carries the better ARGUMENT against reservation, which is not a measurement at all: an alley
in these settlements *is* the residual gap between two plots - "colonized as semi private space by the
adjoining house" - rather than a corridor set aside in advance. A generator that reserves its lanes
first is drawing a planned town, not a grown hamlet.

**A THIRD attempt, measured 2026-08-19: the same gap as a SLIDE LIMIT rather than a verdict.** The
mechanism is `_slide_nuc`, which shoves each bundle at its nearest neighbor in 2 ft steps until the
bbox rule bites - so the fix that refuses nothing is to stop that slide short of sealing a block,
leaving the bundle at the last position that was already legal. It looked strictly safer than the hard
constraint, because it cannot cost a seat. **Cohort: 42/48 against the 43/48 baseline** - it fixed none
of the three reach seeds and added a `village_windbreak_is_continuous` failure on seed 4. Reverted.

**A FOURTH attempt, aimed by the crescent finding: the same slide limit confined to the INNER ARM.**
This is the one the evidence pointed at - every stranded house sits at out -50..-147, so the limit was
applied only on that side of the seat band, leaving the other 45 maps untouched. **Cohort: 43/48, the
same five seeds as the baseline.** The confinement did its job - the map-wide version's seed-4
windbreak casualty is gone, so it costs nothing - and it still fixed nothing.

That is four independent spacing attempts (hard 18 ft: 37/48; hard 12 ft: no gain; slide limit 12 ft:
42/48; inner-arm slide limit 12 ft: 43/48 and neutral), none of which moved a single one of the three
failing seeds. The conclusion is stronger than
"the uniform gap is the wrong number": **spacing is the wrong LEVER entirely.** Whatever seals those
blocks is not a shove-until-collision that a smaller shove would prevent - the fourth attempt stopped
the shove precisely where the defect lives and the same three houses came out unreachable, which means
they were never packed tight BY THE SLIDE. Something seats them there in the first place, and the next
session should start at the seed positions the nucleated placer offers on a crescent's inner arm
(`front_row` / `_place_bundle_nucleated`'s offset search), not at the compaction that follows.

**So the candidate that remains is a POST-PACK repair, not a pre-pack reservation**: pack as now, then
detect a block whose interior has no walkable corridor (the 1.4-1.9 ft pinch measured above is a
cheap, decisive test) and RE-SEAT the two or three steadings whose shift opens one, rather than
inflating every gap on the map. That keeps the compactness the current order buys, spends the
disruption only where a block is genuinely sealed, and leaves the alley as residual ground everywhere
else. Unmeasured, and it is a placement-engine change, which is what makes this a feature rather than
a fix.

**One number worth having before that work starts**: how wide is a real one of these alleys? Ours
needs about 11 ft for a footpath (two `FOOTPATH_FABRIC_GAP` clearances plus a 3 ft tread) and about
20 ft for a web lane, while the vernacular record describes lanes a person wide. If the true figure is
nearer 4-6 ft than 11, part of this defect is our own clearances rather than the packing, and that is
a research question with a cheap answer.

**Cost estimate**: a new pre-homestead stage, a keep-clear registry entry, the `STAGES` tuple, a
re-roll of the four live hamlets and a full cohort sweep, plus one `settlement-review` per pool map.
Its own spec-kit feature.

## 2c. The way-repair passes want ONE design, not three passes patching each other - DEFERRED
(2026-08-19, feature 125, from two `settlement-review` passes on Sawada and Kashikawa. Deferred under
Principle XIV's architectural exception; four fixes were BUILT and MEASURED here before deferring, and
every one is recorded below with what it cost, because each looked obviously right going in.)

**The four defects the reviews found**, none of which a green gate can see:

1. **A hole at a CORNER is invisible to `lanes_do_not_break_mid_run`.** The rule requires BOTH ends to
   aim at each other, so it catches a straight street with a hole and misses an L with one. Kashikawa:
   lane 7 arrives at -67.3 deg facing the other cap dead on (-67.4) while lane 6 leaves at +15 deg
   because it is turning. That 28.1 ft of bare grass is the ONLY thing joining three farmhouses to the
   connector's component - drop the join tolerance and the map is two networks with houses at 267, 161
   and 116 ft from the real one.
2. **The same break gets repaired twice, around a needle of grass.** `_join_orphan_ways` links two
   components, then `_bridge_collinear_breaks` closes the same break with the straight span the street
   wants. Sawada ships both: a triangle 110 ft long, 37.7 ft at its widest, ~2,072 sq ft, converging on
   the cluster's main junction, reading as a street that forks and rejoins around nothing.
3. **A 4 ft fragment ships on a map whose own constant names it as fixed.** `_WEB_MIN_FT`'s `earns`
   escape hatch is order-dependent by construction - it asks whether a run brings a house inside reach
   GIVEN THE NETWORK AT THAT MOMENT - and nothing re-asks once later passes make it redundant.
4. **A dead band from 0 to 40 ft that neither half owns.** The generator calls anything within
   `_LANE_JOIN_FT` (30) joined; the check ignores anything under `_LANE_JOIN` (40); the ink joins at 0.
   Sawada's west alley ships as THREE pieces with holes of 29.2 and 16.7 ft across clear grass. All
   four of that map's gaps measure 16.7 / 28.0 / 29.2 / 29.6 - every one just under the generator's
   threshold, which is a consumed tolerance rather than a coincidence.

**What was built, measured, and REVERTED** - the useful half of this entry:

| attempt | what happened |
|---|---|
| Extract the `WEB_SHADOW_FT` anti-doubling test and make the bridge pass obey it (defect 2) | Refuses the bridge - but the thing shadowing it IS the redundant link, so the 110 ft hole simply stayed open. Traded a cosmetic defect for a structural one. |
| Lower the repair floor to `_WAY_HOLE_FT` = 12 ft (defect 4) | Correct in itself and kept in the sketch below, but on its own it closes nothing: the gaps it newly admits are corner gaps, which the both-ends aim test still rejects. |
| Relax the aim test to "either end aims" (defect 1) | Gives the rule real teeth - it immediately fired on genuine holes in Sawada and Kashikawa - and needs a companion guard, because two ways that already TOUCH then read as a long aiming gap that the touching span itself fills. With the guard it is right, and the generator still could not close what it now reports. |
| Two cleanup sweeps: drop doubled ways, drop unearned debris (defects 2 and 3) | **Regressed both maps.** The guards asked "is every house still near a lane" while the gate asks "near the CONNECTED network", so the sweep deleted the way joining a sub-network: Kashikawa 0 -> 6 unreached houses, worst 516 ft. Matching the gate's own 40 ft join tolerance fixed that specific hole and the maps still failed. |

Everything above is reverted; the pool is back to four green maps. The reason it is deferred rather
than pushed through is what the table shows: each fix is individually sound and they interact, because
three passes (`_join_orphan_ways`, `_bridge_collinear_breaks`, `_serve_stragglers`) each repair the map
against a model of it that the other two invalidate, and a cleanup afterwards cannot reconstruct which
way was the detour.

**The sketch.** One repair stage that plans against a single model instead of three passes patching each
other: build the way graph once (nodes = ends and junctions, edges = drawn treads, joined at ONE declared
tolerance shared with the gate); ask it what is actually broken - components that should be one, holes
whose corridor is walkable, runs no house depends on; then emit a repair SET, choosing per break the
straight span over the detour BEFORE either is drawn, rather than drawing both and trying to tell them
apart afterwards. The check relaxation (either-end aims, plus the already-touching guard) lands with it,
because rule and repair have to agree on what a hole is.

**Cost estimate**: a rewrite of the three repair passes into one graph-based stage, its tests, a pool
re-roll, a cohort sweep and one `settlement-review` per map. Its own spec-kit feature.

**Also found by these reviews and NOT part of the above** (smaller, independent, worth their own fixes):
`M["lane"]` holds the LAST lane drawn rather than the village street, and five consumers read it as the
street - two gate checks are adjudicating grove shading and structure-vs-street against a 45 ft orphan on
Sawada, so they run, pass, and test the wrong geometry; a skeleton arm overruns its last steading by 85 ft
because `_trim_to_service` only runs on web lanes; and `plot_regularity` is recorded in `meta` as though
rolled while `water.py` passes the literal `"organic"`, so it can never vary.

## 2d. "How far past its last steading may a way run?" - a RESEARCH question, not a bug
(2026-08-19, from the same two reviews. Recorded here rather than fixed because the ladder in
constitution Principle XII puts research BEFORE a number, and this is a calibration with no obviously
correct value - unlike `M["lane"]`, which was a plain correctness bug and was fixed in the same pass.)

**The measurement.** `trim_lane_stubs` pulls back any internal lane end that reaches nothing, where
"reaching" a farmhouse means within `house_reach = 90 ft` OF ITS CENTER. Two arms survive that test
and still read as blunt treads dying in grass:

- Sawada `lanes[2]`, NW terminus (1335.0, 2077.3): the main street stops **85 ft past its last
  steading** (house center 1417, 2054) and ~30 ft short of the paddy bund it is aimed at, 103 ft from
  any other way.
- Kashikawa `lanes[2]`, end (2346.6, 2569.8): **81.7 ft from the house center but 55 ft from its
  wall**, and lying 75.7 ft to one side of that house, level with its threshing yard rather than
  facing the dooryard. Nearest other way 119 ft.

**Why it is not a one-line fix.** The obvious move - measure to the drawn CORNERS the way feature 121
made `houses_clear_of_lanes` do - pushes the wrong way on its own: the wall is nearer than the center,
so at an unchanged 90 ft MORE ends would count as serving and FEWER would be trimmed. Fixing this
means measuring to the footprint AND re-deriving the threshold, i.e. answering "how far beyond the
last house does a village lane actually run before it becomes a field track?" That is a question about
how these places were built, so it gets a research pass first, and if the record supports two forms
(a lane that stops at the last dooryard, and one that runs on to the field edge) it becomes a KNOB
rolled per settlement rather than a number someone picked.

Note the gate already carries this mechanism in a comment beside `_BREAK_GAP_FT` - "an end 83 ft from
a house CENTRE counts as fronting it, even when that is 55 ft from the wall, i.e. out past the
dooryard". Kashikawa is that comment realized in ink. The comment predicted the defect and nothing
acted on it, which is its own small lesson.

## 2e. `plot_regularity` is recorded as though rolled and is a literal
(2026-08-19, from the Kashikawa review.) `meta.plot_regularity` reads like a rolled knob and the comb
path passes the literal `"organic"` (`hamletgen/water.py`), so it can never vary. Alongside it, all
four scripted hamlets record `plot_size: medium` (a 2-in-4 weight, so 4/4 is about a 6% draw),
`field_archetype: valley_paddy` (documented - polder is opt-in) and `cluster_seeding: frontage`
(derived, not rolled). None of that is wrong; what is wrong is that a reader meets four `meta` lines
that look like evidence of variance the pool is not actually spending. Under the two-supportable-forms
rule these are candidate knobs - regular versus irregular plot layout is exactly the kind of thing the
record may well attest both ways - so the fix is a research pass per field, not a quiet default. Until
then, do not read those `meta` lines as proof the maps differ along those axes.

## DONE 2026-08-19: `cluster_shape` was the same defect as 2e, one tier worse - it WAS rolled and read by nothing

The entry above says a `meta` line can look like evidence of variance the pool is not spending.
`cluster_shape` was the acute case: genuinely rolled per settlement from `CLUSTER_SHAPES`, printed in
every cohort-audit header, and consumed by exactly one caller - `cluster_seeds`, the CLOUD seeding
pass, which only runs for households the front rows and lane frontage do not seat. **Census over 48
cohort seeds plus the four pool hamlets: the rows seat every house on 47 of 48 seeds, so the cloud
ran on ONE (seed 34) and `meta.cluster_shape` was stamped on one.** Round, elongated and crescent all
drew the same 3:1 band. That is why a peer session was able to spend an attempt blaming the knob for
a placement failure and then retract it: nothing read it, so it could not have caused anything.

Fixed by binding the shape where the shape is actually decided - the seat BAND (`CLUSTER_BAND_ASPECT`,
consumed in `seat_cluster`) and the front row's wrap along it (`CLUSTER_ROW_SPAN`, consumed in
`front_row`). Area is held constant, so only the ratio moves; crescent keeps the old hardcoded 3.0 and
is byte-identical to what it drew before.

**AS SHIPPED, ONLY ELONGATED BINDS.** Round is reverted to crescent's 3.0/1.6 because every value that
bound it cost a cohort seed (1.4/0.9 -> seeds 17/39/47; 2.2/1.2 -> 47; 1.8/1.0 -> 11/38/45), and each
of those is downstream of a defect in another subsystem rather than of the ratio. The numbers and the
re-sweep instruction live in the `CLUSTER_BAND_ASPECT` docstring. What ships regardless is the
HONESTY: the declaration is validated against the drawing, so a knob that does not bind can no longer
look like one that does.

**It does not bind above the lane skeleton, and that is recorded rather than hidden.** On a large
hamlet the skeleton seats most of the cluster and spreads it whatever the band says - Kashikawa's 20
households draw 1.0:1 while the roll said `elongated`. So the generator stamps `cluster_shape` only
when the drawn aspect is within tolerance of the declared one, stamps `cluster_shape_unhonored`
otherwise, and always records `cluster_aspect_drawn`. Gate `cluster_shape_matches_the_drawing` (0615 - 0614 collided with a THIRD session's `paddy_bunds_do_not_stagger`; git merged both files cleanly and the tree simply would not import, which only the derived registry knew)
holds both halves: a stamped shape whose drawing contradicts it fails, and a map recording NEITHER key
fails - because a knob that never binds has to stay distinguishable from one that always does, which
is the whole lesson of this entry and 2e.

Priced and declined: making the skeleton itself shape-aware (a `T` on an elongated roll laid along the
long axis rather than across it). That is a lane-topology change, it lands in the middle of the peer
session's lane work, and the honest declaration already stops the manifest lying.

**And it is NOT the next step - that was written here for about an hour and is now falsified.** The
peer session built the idea in miniature the same day (`_serve_far_margin`, a short run laid at the
unserved house's own frame position rather than searched for) and it fixes nothing: run before the
repair passes it collapses the cohort to 17/48 by drawing speculative treads fronting nothing; run
after them, for houses still unserved, it is 43/48 - exactly baseline - because no run survives
clipping. The measurement under that result is the useful part: at the stranded houses' own arcs, a
margin line of +/- one bundle pitch yields NO clear run at any stand offset (0, +40, +70, -40 ft) at
either the web's 7 ft clearance or the footpath's 4 ft. Nothing is drawable along the margin there.
Put beside the 60-120 ft of open ground that surrounds those same houses, the conclusion is that **the
open ground is not aligned with the margin** - the frame's arc direction at those points heads into
the paddy. So a skeleton following the field margin, shape-aware or not, cannot reach them. Whatever
serves these houses must be oriented by the LOCAL DRY GROUND, which nothing in the engine computes
today. That is a bigger piece of work than either session had priced.

**What the peer session has already RULED OUT on this (2026-08-19, eight measured attempts, all
reverted).** Do not re-price a shape-aware skeleton as more promising than it is without reading
these first - and do not re-try any of them:

- three spacing variants, a slide limit, an inner-arm-confined slide limit, a `front_row` filter of
  negative-`out` seats (43/48, fixed nothing), a straight-line-crosses-crop seat test (42/48, added a
  bridges and a field_ringed failure), and a one-flood-fill-per-map dry-region seat test (43/48,
  rotated seed 10's windbreak into a seed 47 break failure, fixed nothing).
- **The flood-fill attempt is the informative one, and it kills the obvious theory**: the stranded
  houses ARE inside the dry region walkable from the cluster's middle. They are not cut off. The way
  network simply never extends round to them, and the footpath router's search box never spans the
  detour.
- On seeds 5/8/25 specifically: a web line IS planned 17-33 ft from every stranded house and clipping
  destroys it entirely (zero surviving runs); 36-56 of 59 points on the line to the nearest existing
  way lie inside the paddy; `_route` finds no path at any lattice resolution or box size up to
  pad_mult 3.0. The houses sit on the FAR MARGIN, across the water from the network, with dry ground
  connecting them the long way round that nothing currently searches far enough to find.
- This looked like the case FOR a shape-aware skeleton - put a way on that margin - and the peer
  session then built it and disproved it the same day (attempt nine; see the paragraph above). The
  margin is not where the open ground is. Read that before reviving any margin-following idea.

**RETRACTED, and the retraction matters more than the claim**: an earlier peer measurement of a
"1.4-1.9 ft corridor, the packer seals them in" - which justified the entire spacing line of attack -
was an artifact. It walked outward from each house CENTER against ALL fabric, including the
steading's own house, yard and garden, and every farmhouse is surrounded by its own bundle by
construction, so it returns ~1.5 ft for a house standing alone in an empty field. Re-measured with
the own bundle excluded: 63-120 ft. **There was never a packing problem.** Third retraction of the
day from that session, and all three share one shape - a quantity was measured that could not
distinguish the failing case from a healthy one. That is the failure mode to design against here,
not any particular wrong number.

## DONE 2026-08-19: the woodland scan vetted a SQUARE while the gate measured a ROTATED BBOX

Found by chasing what looked like a cluster regression (cohort seed 33 newly failing
`woodland_commons_within_the_frame` at 67% inside the view) and turned out to be neither new nor
about clusters. `open_ground_patches` accepts a seat through `_ok`, which tests an axis-aligned
SQUARE of the parcel's long half; the parcel is then DRAWN as a rectangle rotated to `_bear`. Rotating
a box grows its axis-aligned bbox - by up to sqrt(2), at 45 degrees, even for a square - and the gate
measures that bbox. So a seat could pass the scan at 0.8 of a square and draw a parcel 0.67 inside the
window. The replaced line's own comment said "the scan already tested this seat at REACH, so the
rotated parcel fits": an assumption written as a fact, and wrong.

Latent since the aspect/bearing work landed earlier the same day. The cluster change did not cause it;
it walked one parcel to the frame edge, where the discrepancy finally exceeded the slack. **Seed 33 was
the messenger, not the defect** - worth remembering next time a cohort seed rotates under an unrelated
change.

FIXED by computing `_bear` before the aspect ladder (it never depended on the aspect) and testing each
rung on the true rotated bbox, plus a local shrink ladder so a seat near the edge yields a SMALLER
coppice rather than none.

**The prediction slack was measured and mostly removed, and the first attempt at this fix FAILED
because of it.** Instrumenting seed 33 showed the predicted kept window is byte-identical at all 16
`_crop_boxes` calls across the build AND equal to the final `meta.view` - everything that sets the
frame is already placed when the woodland scan runs, so the "prediction" does not drift at all. The
first cut kept the neighboring 0.8 floor on the rotated bbox; that paid 10 points of slack for drift
that does not happen and DELETED seed 33's woodland outright, which is a worse map than the clipped
parcel the fix was for. 0.72 - a 2-point cushion over the gate's 0.7 for float ordering - keeps the
coppices and still cannot draw an off-frame one. Do not raise it back to 0.8 without re-measuring the
window drift first; the drift is the only thing that would justify it, and it is zero.

**Watch the invisible half of this rule.** `woodland_commons_within_the_frame` fails a parcel that is
DRAWN and mostly off-frame; it says nothing about a parcel never drawn. So any tightening of the scan
can convert a visible failure into an invisible one and read as success. That is why the fix was
verified with a PARCEL COUNT census across seeds and not with the gate alone - the gate is green in
both worlds. Same family as the `cluster_shape` census (a knob honored on 1 of 48 seeds, nothing
failing) and as `CLUSTER_DRAWN_ASPECT` (a guard comparing the drawn aspect against a mechanism
parameter): a measurement that cannot distinguish the healthy case from the broken one.

## DONE 2026-08-19: the streams were invisible to every way-vs-water test

`shallow_crossing` exists in `hamletgen/ways.py`, is correct, and is wired into `path_violations`
with a 42-degree limit. It had never once seen a stream. The water lists the way code builds are
`plan.watercourses` (the planned irrigation net) and `drawn_channels` (the drawn one); `M["streams"]`
- the feed brook and any natural course - was in neither, so a lane could cross a brook at any angle
with nothing objecting. On cohort seed 47 a way crosses a 7 px stream at **17 degrees**, which is a
lane running nearly PARALLEL to the water rather than over it, and `bridges_span_their_water` failed
the 57.6 px deck it produced - with the guard written for exactly that case sitting one list away.

FIXED by `drawn_water_segs(s)`, which returns channels AND streams, replacing the inline
`drawn_channels` comprehension in the web-lane path and feeding a new `waters=` argument to
`connector_track` (which took `plan` but not `s`, and so could not have seen the streams even in
principle). `trades.py` already read both records together - this is that pattern applied where the
ways are laid.

**The same defect family as everything else this feature turned up, and that is now four in one
day:** a guard keyed on the wrong input, measuring something other than what it protects.
`cluster_shape` fed a pass that never ran; the first honesty guard compared a drawn aspect against a
mechanism parameter; the woodland scan vetted a square while the gate measured a rotated bbox; the
way code's shallow-crossing guard never received the streams. In every case the check was GREEN and
the thing it existed to catch was happening.

**WHAT THIS DOES NOT FIX, and who owns it.** Seed 47 still fails. The offending way is a WEB lane
laid by one of the gap-bridging passes (`_join_orphan_ways` / `_bridge_collinear_breaks`), whose job
is to span a break - so it spans, and the stream list does not stop it because those passes are not
asking the shallow-crossing question at all. Wiring them into it is a lane-topology change in
`hamletgen/ways.py`, which the Diagram architecture session owns and was actively editing; doing it
from here would have been two sessions in one subsystem. **Handed over rather than half-done.** The
measurement to start from: seed 47, lane 2, `web: True`, w=6, 3 points, segment 0 running
(2473,382)->(2522,160) at bearing -77.4 against a stream bearing ~86 - a 17 degree crossing, deck
(2503,245) span 57.6 on ~7 px of water.
## 2f. The shallow-crossing veto must be STREAM-scoped, not water-scoped (measured)
(2026-08-19. The hamlets session found that `shallow_crossing` is wired into `path_violations` but not
into `_join_orphan_ways`, which goes straight to `_draw_web`; cohort seed 47 shipped a way meeting a
stream at 17 degrees, surfacing as `bridges_span_their_water` failing a 57.6 px deck over 7 px of
water. Handed to me as lane topology. This entry is what I learned trying to close it.)

**Two things are settled and worth having before anyone tries again:**

1. **Only the LINK pass needs the veto.** `_bridge_collinear_breaks` hands its `water` to `_route`,
   which refuses to cross a watercourse at ANY angle - so a bridge never crosses water and a veto
   there is unreachable code. `_join_orphan_ways` deliberately passes an EMPTY water list ("a link may
   go the long way round, and may be planked"; `stage_crossings` decks it afterwards), which is why it
   is the pass that can lay a way down the length of a brook.
2. **A BLANKET veto is far too costly: 41/48 -> 26/48, with 21 seeds failing `farmhouses_reach_a_way`.**
   Placement makes no difference - refusing the chosen link and returning abandons the pass over one
   bad candidate, and moving the test into the candidate loop so it tries the next route measures
   exactly the same. The cause is the water list: `plan.watercourses + drawn_water` is the whole
   irrigation net, and a link joining two halves of a hamlet crosses field ditches constantly, often
   obliquely. Demanding a square crossing of every ditch strands the components the pass exists to
   join - which is a worse defect than the one being fixed.

**AND SCOPING IT TO STREAMS DOES NOT SAVE IT EITHER - measured: 32/48, with 14 seeds failing
`farmhouses_reach_a_way` against a baseline of 3.** Reading `M["streams"]` directly (so ditches stay
plankable and only natural courses are vetoed), asked in the candidate test so a refusal tries the next
route rather than abandoning the pass, still strands eleven more seeds than the defect costs. The
reason is structural rather than a matter of degree: **a stream is frequently the very thing separating
the two halves a link exists to join.** The link must cross it, and where the components lie it often
cannot cross square.

**So refusing the way is the wrong lever at ANY scope** - blanket 41 -> 26, stream-only 41 -> 32, both
far worse than the defect. And that reframes the defect: seed 47's way is LEGITIMATE. What failed is
`bridges_span_their_water` - the DECK for an oblique crossing, which needs
(width + deck_w x |cos|) / sin plus a landing each side and so lands an abutment in the water. The fix
belongs in how an oblique crossing is DECKED, or in steering the link to meet the water square where it
can, and not in whether the link is drawn at all.

**Superseded, and kept because it is what the numbers looked like after only the first measurement: the
veto has to be scoped to the water that actually needs a real deck** - the streams and the
larger channels, not every puddled aze ditch a plank spans. That needs the hamlets session's
`drawn_water_segs` (channels AND streams) to land first, so the two lists can be told apart at the
call site; wiring a veto against today's undifferentiated list cannot be made safe. Reverted; nothing
of it ships.

## OPEN 2026-08-19 (latent, with the measurement): the oblique-deck growth loop fails SILENTLY

Found while chasing cohort seed 47's `bridges_span_their_water`, and it is only latent because the
round cluster binding that steered a lane onto that crossing was reverted. It will surface again the
moment round binds, so it is written down rather than left to be rediscovered.

`bridges()` (settlement/city/bridges.py) sizes an oblique deck correctly - `(ww + rw*|cos|)/sin +
2*LANDING_FT`, which for seed 47 gives exactly the 57.6 px it drew. The formula solves against the ONE
segment the way cuts, so a bending watercourse can still put a corner in water, and a growth loop
exists for that: `for _grow in range(14): _try = _span * (1.0 + 0.12*_grow)` ... `break` on success.

**It breaks on success and does nothing on failure.** When all 14 steps fail, `_span` keeps its
original value and `self.bridge(...)` draws the undersized deck anyway. The pass reports a bridge; the
gate then fails it. Same family as everything else this feature turned up - the failure path looks
exactly like the success path from outside.

**And on seed 47 growth CANNOT work, so the loop is the wrong lever there.** The way crosses at 17
degrees, so the deck lies nearly ALONG the stream; lengthening it drives its ends further down the
water rather than clear of it. 2.56x is not too small a ceiling, it is the wrong axis.

WHAT THE FIX IS NOT. A peer session measured the two obvious lane-side answers and both are far worse
than the defect: a blanket `shallow_crossing` veto in the link pass takes the cohort 41/48 -> **26/48**
(21 seeds failing reach), and a stream-only veto - ditches still plankable, asked in the candidate
loop so a refusal tries the next route - takes it to **32/48** (14 seeds). The reason is structural: a
stream is frequently the very thing separating the two halves a link exists to join, so the link must
cross it and often cannot cross square. **The lane is legitimate; the deck is what is wrong.**

THE TWO CANDIDATE FIXES, neither costed yet:
1. **Bend the way onto a square crossing.** What a real track does - the road turns to meet the
   bridge, crosses, and turns back. Lane geometry, and it must be a local bend rather than a veto,
   since vetoing is what measured 26/48 and 32/48.
2. **Orient the deck square to the water** and let the way meet it at an angle. Geometrically simple
   and historically right, but `bridges_align_with_their_way` currently forbids it - that check would
   need a stated exception for a near-parallel approach, which is a rule change, not a patch.

Whichever is chosen, the growth loop needs a real failure branch: if no step clears the water, that is
a fact the pass knows and currently discards.

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

## MOSTLY DONE 2026-08-19: paddy bunds that step sideways - the staircase is gone, 7 corners remain

**The report (GM 2026-08-18, on Inashiro).** *"The earthen wall is kind of going in a southward
direction, and then instead of just continuing on and meeting at the four way intersection between
the north south earthen walls and the east west earthen walls, it just goes sharply to the left
before going down."* Research, mechanism and the shipped design are in `research/fields.md`, "A bund
runs on, or it turns for a reason"; the numbers and the two dead ends are here.

**What shipped**, in the order of how much each mattered, measured against the maps as they shipped on 2026-08-18 (a peer session's lane-web work re-rolled all four the same day, so the rows are the effect of THESE changes, not of the day's total):

| | inashiro | kashikawa | mizuguchi | sawada |
|---|---|---|---|---|
| before | 26 | 37 | 20 | 24 |
| `_absorb` jog guard alone | 23 | 33 | 17 | 16 |
| + `_unjog` (trade the corner) | 2 | 3 | 4 | 3 |
| + `_seam_cuts` (cut at the fabric's own seams) | **0** | **1** | **5** | **1** |

**Rings carrying MORE THAN ONE step - the staircase itself - went 6 / 9 / 4 / 7 to 0 / 0 / 0 / 0.**
Regeneration is unchanged (20.4 / 26.0 / 17.6 / 29.1 s against a 21.1 s baseline on Inashiro).

### Still open: isolated steps, and why each is refused

**Two counts, and they are measured at different thresholds - say which, or the numbers look wrong**
(settlement-review caught this file quoting one and meaning the other, 2026-08-19). At the GATE's
line (run 8 ft, link 25 ft, offset 3 ft) the four maps carry **0 / 1 / 5 / 1 = 7**. At the PLACER's
stricter line, which is what `tools/jogs.py` runs (run 6 ft, link 30 ft, offset 2 ft), they carry
**2 / 2 / 9 / 3 = 16**, the largest 16.0 ft at Mizuguchi (1571.7, 897.6). The table above is the gate
column. `python3 -m l7r.diagram.tools.jogs pool/hamlets/*.json` prints the placer column.

Every one is a SINGLE step on a single ring - no POOL map carries a flight of them, though the 48-seed
cohort does; see "LIVE RESIDUE ON THE COHORT" at the end of this section. Traced, they are
refused by guards that each protect a rule `_unjog` would otherwise break, so none is a matter of
loosening a number:

- **the neighbour would be split in two** by giving up the corner (`qp.difference(traded)` returns a
  MultiPolygon) - the dominant one on Mizuguchi. A possible answer, untried: keep the largest part
  for the neighbour and hand the orphaned fragment to the basin that cut it, so the bite widens
  rather than the neighbour splitting.
- **the new wall would land in a delivery ditch or off the command area** - the chord cuts a corner
  the carve had wrapped around a bank. Routing the new wall ALONG the bank instead of straight would
  answer it, and is a bigger change than it sounds.
- **the repair would draw a basin out to a needle**, judged at the gate's own 15 deg.

**And the gate check is the last step of this work.** `paddy_bunds_do_not_jog` is written, has seven
unit tests, and a frozen pre-fix Inashiro fixture; it is held out of `check_village` only because
those 7 would fail the pool on day one. Landing it means either driving the 7 to zero by the routes
above, or - the honest alternative - writing the rule as the STAIRCASE rule the GM actually
reported: no plot ring may carry more than one step, which is at zero on the POOL today and would have
fired on 26 rings across the four maps before this work.

**LIVE RESIDUE ON THE COHORT (2026-08-19, unfixed, owned by the waterfields session).** That rule
landed as gate **0614 `paddy_bunds_do_not_stagger`**, and it is at zero on the four pool maps - but the
48-seed cohort carries two failures. Recorded here because a peer session found them and reported them
in a message, and a number that lives only in a chat message is not a measurement:

    Audit-12   1 basin, bund steps sideways 4 times, at (1316, 939)
    Audit-39   1 basin, bund steps sideways 2 times, at (1305, 2081)

Both are **pre-existing rather than regressions** - a baseline comparison in a detached worktree showed
zero new failures - and both are independent of the three `farmhouses_reach_a_way` seeds (5, 8, 25);
full cohort 43/48. **Audit-12 matters more than its count suggests**: FOUR steps on one ring is a longer
staircase than anything the pool ever showed, so it is a better specimen of the GM's original defect
than the map the fix was built against, and it should be the case any retry is measured on. The fix
site is the one the check's own failure message names - `close_seams` / `_seam_cuts`, where the weld
pitch goes out of register with the fabric. Do NOT reach for the threshold: "more than one step on a
ring" is the deliberate line, and retuning it is the one dial that guts the check.

### Two dead ends, both implemented, measured and reverted

Neither is a reason not to try again - both got most of the way - but each broke something specific.

1. **`_share` - partition a scrap among the basins along it by NEAREST BASIN.** Took Inashiro 23 -> 7
   and visibly removed the staircase, and it is the right idea in the abstract: each basin takes the
   ground in front of its own bund, so its wall moves outward across its whole frontage. Measured
   failure: `_absorb` refuses 960 of 2,685 welds against 5 of 370 without it, leaving 16,767 px2 of
   bare ground inside the command area against 1,760, and **492 of those refusals had NO ADJACENT
   BASIN AT ALL** - `_absorb` ranks the basins whose bund forms part of a scrap, so a piece touching
   only its siblings has nothing to rank. Guarding the stranding (abandon the partition when a piece
   reaches no basin; fold recovery ground into the neighbouring piece) took bare ground to ~4,900 px2
   and refusals to 281, but then the partition switches itself off exactly where the ground is
   awkward, which is exactly where the staircase is. It is also fragile against GEOS: three separate
   `TopologyException` sites in one afternoon, including inside `_absorb`'s ranking loop.
   **`_seam_cuts` is the same insight applied one stage earlier, at a tenth of the machinery** - the
   pitch, not the partition - which is why it worked.
2. **Dropping a step's vertices from every ring that carries them.** Looks partition-preserving and
   is not: the two rings either side of a wall have DIFFERENT neighbouring vertices, so the chords
   they close over differ, and Inashiro rings 460 and 592 lost 400 px2 and gained 259 - the
   difference being bare floor. `_unjog` trades the corner as a POLYGON instead, which conserves
   ground by construction whatever the two rings look like.

Two smaller levers were measured as dead and are recorded at the point of change in `seams.py`:
letting the basin on the OTHER side of a wall attempt the repair (one step in four maps, 70% of the
regeneration), and re-offering a partition piece no basin would take.

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

- **DONE 2026-08-19: flooded-basin tint on a long wedge.** Raised twice - first as a hue-separation
  nitpick, then again by a second review that measured it properly: Inashiro's two tinted plots ran
  114 x 18.9 ft and 139 x 24.8 ft, aspects 6.0 and 5.6, and read at fit zoom as blue daggers of water
  rather than as basins holding it. It was never a hue problem. The tint's demotion ladder had four
  clauses (apex, truncated end, solidity, siting at the outfall) and every one of them asks about a
  POINT, so a long parallel-sided wedge passes them all. Fixed by a fifth clause measuring
  PROPORTION - `_TINT_MAX_ASPECT`, 4.0 on the minimum rotated rectangle, far above the ~1 a leveled
  basin runs at. It demotes exactly the offenders: Inashiro 2 tinted plots -> 0 and Sawada 1 -> 0,
  while Kashikawa's and Mizuguchi's single tinted basins are untouched. Inashiro now carries no blue
  basin at all, which is the honest answer when neither candidate reads as one - the tameike and the
  pocket pond still carry the map's water.
- **Byres buried in canopy.** Two of three byres carry ~45 crowns within 40 ft while the third
  stands clear, so at fit zoom the sheet reads as one byre rather than three. Nothing overlaps (that
  is gated); it is a legibility consequence of the grove scatter, and it belongs with the byre-siting
  work above rather than with the groves.


## OPEN after the 2026-08-18 round-2 reviews (everything else from that round is FIXED)

Round 2 confirmed five defects and refuted one; all five are fixed at their point of change, and the
rulings the GM asked me to make are recorded there too. What is left:

### CORRECTED - cohort seed 10's belt hole is a SUN CORRIDOR, not a polygon pinch

**The earlier entry here was wrong about the mechanism and would have sent the next session to the
wrong file.** It said `belt_polygon`'s near-face sampling pinches. It does not: the band is built as
a constant-depth ribbon (near face at u+36, far at u+146, so 110 px everywhere), and the clumps in
the gap were being FILTERED OUT, not left outside a narrow polygon.

**Measured cause.** `village_grove` keeps clumps out of the ~24 px strip SOUTH of every threshing
yard and garden, so a tree cannot shade the drying ground. On seed 10 a yard sits just north of the
belt line and its sun corridor runs straight through the wall. Instrumenting the fill and printing
the rejecting predicate for every grid point in the gap gave `SUN` for almost all of them and
`corridor` for one. **And the hole matters**: the gap spans across-wind 1739-1779 and there is a
farmhouse at across-wind 1751 - directly downwind of it. The wall is breached at one of the few
places it is actually sheltering someone.

**THREE FIXES ATTEMPTED, all recorded so nobody repeats them:**

1. *Widen the re-seat radii* (to `step * 2.2` = 44 px, past the corridor's ~25 px half-width). No
   change at all - and the reason is attempt 2.
2. *Fold the three ad-hoc nudge blocks into one predicate pair and let the sun corridor re-seat.*
   This found a REAL defect and is KEPT: the interior test (`edge_dist > clump`) was written for the
   lane case - a lane that ends at the belt is an edge, one that crosses it is an obstacle - and was
   being applied to every local blocker. A belt is 110 px deep and a clump is 28, so it left only
   the middle 54 px eligible, and every sun-corridor clump measured 2-27 px from a face. **The
   search was never running.** It is now scoped to lanes.
3. *With the search actually running*, the gap MOVED (1266 -> 1250) and stayed 40 ft. A yard's sun
   corridor crosses the belt's whole depth, so filling that across-wind range needs a clump at that
   y but clear of the corridor in x, and every candidate within reach is blocked by something else.

**What is left, and the honest shape of it**: this is a genuine conflict between two rules, not a
bug in either. The sun corridor protects a yard's drying sun; the belt protects the houses from
wind; on this composition they want the same ground. **Sketch**: let a re-seated clump sit slightly
OUTSIDE the belt polygon - the polygon is our own derived construct, not a property of the world,
and a real planted belt bulges around an obstacle rather than admitting a hole. That is a change to
what the belt outline MEANS, so it wants its own pass and its own review, which is why it is here
rather than in the diff.

Cohort effect of what was kept: 35/48 before and after, so no regression and no seed rescued - the
value is the disabled-search defect, not this seed.

### The belt and the copse share one crown vocabulary

Sawada's two grove records sit 23 ft apart with half the copse's clumps touching the belt's, so the
manifest declares two features and the sheet shows one wood. A planted *yashikirin* windbreak was
typically one tall species in a row against mixed broadleaf coppice, so the honest fix is a
different crown treatment for the belt - darker, taller, ranked - rather than a separation distance.
That would also make the belt's form legible: Sawada's measures 906 x 199 ft at aspect 4.5, which is
a textbook belt that currently does not read as one.

**Why deferred**: it changes how every grove on every map is drawn, at every tier, which is a
visual-doctrine pass rather than a defect fix. Ledgered with the measurement so it is not rediscovered.

### The grazing commons are a tiling, not a landscape

Every hamlet's `commons` records partition the whole frame remainder into four rectangles plus a
leftover. Nothing on the sheet is wrong - the scatter reads as continuous rough grazing and carries
no boundary ink - but the RECORD is bookkeeping rather than places, and nothing distinguishes
hill-foot rough grazing from the beaten ground by the houses. Raised by two reviewers independently,
both as a note rather than an error. Worth knowing before any rule starts reading `commons` as
though each entry were a distinct place.

### Seed 31's threshing yard laps a paddy - and TWO fixes for it FAILED, recorded so nobody re-tries them

`harvest_yards_clear_of_paddies` has failed on cohort seed 31 since before the 2026-08-18 work
began (it is in that session's first baseline, so it is pre-existing rather than a regression). The
yard at (2040, 1898), 32 x 22, puts a corner at (2024, 1908) inside a drawn basin.

**Fix attempt 1 - `_yard_fits` in `homestead_parts.py`: DEAD CODE on this path.** The reasoning was
right (the check tests the yard's CORNERS against each paddy's recorded `outline`, while that
function tested the yard's CENTRE with a circle against `field_polys`, the smoothed ENVELOPE - two
sources and two geometries). The measurement that killed it: **`_yard_fits` is called ZERO times on
a hamlet roll**. Hamlets seat homesteads through the bundle solver, not through that function.

**Fix attempt 2 - the same test in `rolling/fit.py::_bundle_common_fits`: correct path, still no
effect, and reverted.** That predicate IS the one hamlets use (6,104 calls on seed 31, with the
paddy outline available on every one of them). But the rect it tests is not the rect that ships:
probing yards within 30 ft of the target showed the tested rect as **(2055.4, 1921.7, 33.9, 27.8)**
against a recorded **(2040, 1898, 32, 22)**. `farmsteads()` runs a south-nudge relaxation AFTER the
fit, so the bundle moves and its yard is drawn from the moved geometry. Reverted rather than kept,
because it cannot catch what it aims at and it costs a per-paddy-outline test inside a hot loop.

**So the defect is the familiar one a layer further in**: the placer tests a RESERVATION and the
engine draws something else, which is exactly what feature 121 fixed for houses ("the placer tests
the rake it draws"). **Sketch**: re-assert the bundle's yard against the fields AFTER the relaxation
nudge - in `farmsteads()` where `_attach_yard(rec["x"], rec["y"], geom["yard"])` is called, the geom
is final, so the test belongs there and costs one check per homestead rather than one per candidate
seat. If it refuses, the nudge should be undone rather than the yard dropped.

## DONE 2026-08-19: the gen-time budgets had drifted from protection into a coin toss

`GEN_TIME_BUDGETS` (tests/test_villages.py) exists to catch a pathological gen - the 2026-08-02 Minami
bug, 45 minutes of re-scanning static geometry per candidate seat, which nothing flagged. Its stated
policy is "~4x the solo measurement". The solo measurements it multiplied were from 2026-08-12 and had
since roughly DOUBLED as features landed:

    kashikawa 32.2s measured vs ~16s claimed    sawada 30.6s vs ~20s
    inashiro  22.4s vs ~11s                     mizuguchi 18.9s, no entry at all

So 4x-of-old had quietly become ~2x-of-current. And the assertion does not run solo: it runs inside
`pytest -n auto`, where CPU per gen inflates ~2.5x from cache and hyperthread contention (measured
in-gate 57.4s vs 22.4s solo on inashiro; 83.1s vs 32.2s on kashikawa). A budget below the contention
multiple **fails on a busy box and passes on an idle one** - it cost three false gate failures in one
session, each initially read as a possible perf regression, and each costing a full gate cycle to
disprove.

Recalibrated against measured solo times, same policy multiplier, and `mizuguchi` given the entry it
never had. Verified on BOTH trees (clone and a detached worktree at main's tip) before touching
anything, because "raise the limit until it passes" and "fix a miscalibrated guard" are the same
edit and only the measurement tells them apart.

**CORRECTION, made the same day**: the first version of this entry said both trees "measured the
same", so the drift was none of this session's doing. That rested on whole-gen timings, which are too
coarse to see one stage move. A per-STAGE profile of the real pool specs shows this session DOES add
cost - build-stage totals mine vs main's tip: kashikawa 29.6s vs 21.8s (+36%), inashiro 20.7s vs 17.9s
(+16%), sawada 61.7s vs 57.2s (+8%). So the budgets absorb a genuine increase as well as the older
drift. It is not pathological - no stage explodes on a corpus map, and `stage_web` is faster on
kashikawa (1.95s vs 2.16s) - but "unchanged" was the wrong word and the number belongs here.

**DIAGNOSED TO ROOT CAUSE 2026-08-19, and it belongs to the web's candidate GENERATION, not to any
slow predicate.** On an arbitrary spec - `HamletSpec(seed=7, households=20)`, default fall and sink,
which is NOT a pool map and NOT a cohort seed (their household counts are `10 + (seed*7) % 11`) -
`stage_web` costs 21.3s against main's 0.26s. Counted rather than profiled, because two profilers
failed silently first (a filter that matched no rows, then a cProfile run that timed out with no
output):

                        clear_runs calls    runs returned    lanes laid    time
        main's tip                   366              177             3     0.26s
        this session             118,128           43,438             2    21.31s
                                  (323x)           (245x)

**So it is not that each scan got slower - the CANDIDATE SET exploded 323x.** Both trees roll
`shape=round` here; mine binds round at 2.2/1.2 where main used the flat 3.0/1.6, and a compact cluster
of 20 households packs far more inter-steading gaps. The web's cut generation is super-linear in those
gaps, so tightening the cluster multiplies the candidate lines rather than adding to them. 118,128
scans to lay 3 lanes is the shape this skill's CLAUDE.md names - "a per-candidate scan of geometry that
does not change during the scan" - but the multiplier is upstream of the scan, in how many candidates
exist.

**NOT A LIVE DEFECT, and the corpus numbers are the reason**: pool specs are flat (kashikawa 1.95s mine
vs 2.16s main; inashiro 0.31s both), and all 48 cohort seeds pass with no time budget complaining.
Nothing shipped is slow because of this.

**WHY IT IS RECORDED RATHER THAN FIXED, and who owns it.** A hoist or an index - the fix this session
was scoped to make, since it changes no output - would make each of the 118,128 calls cheaper and leave
the 323x intact. Cutting the call count means changing WHICH runs the web generates, which is lane
semantics and belongs to the session that owns `stage_web`. That boundary was agreed explicitly rather
than assumed. **The reason to care anyway**: the village tier is about to inherit this stage, and a
stage that varies 323x on an input one seed from the test bed will not stay off-corpus forever - a
village is a compacter settlement than a hamlet by definition.

**Reproduce in seconds** (do not reach for a profiler): wrap `ways.clear_runs` and `ways._lay_web_lane`
with counting shims, walk `hamletgen.driver.STAGES` to `stage_web`, and time that one call with
`resource.getrusage().ru_utime`. The crude counter answered in seconds what two profilers could not.

**Same family as the rest of this day's findings**: a guard whose INPUT is not the quantity its
calibration describes. The budget describes solo CPU; the assertion measures parallel-run CPU. It was
green or red depending on the machine rather than on the code.

**Open, and worth someone's afternoon**: why solo doubled in a week. It tracks the features that
landed (lane web, byres, woodland scan, cluster shape), so it is probably real work and not waste -
but nobody has measured which STAGE owns the growth, and `tools/timings.py` answers exactly that.

## DONE 2026-08-19: coverage that depends on whether the GEN CACHE was warm

A gate run failed on coverage - `hamletgen/ways.py` 881-888, the snap arm of `_lay_web_lane` - against
a tree whose Python was **byte-identical to the gate that had just passed**. Only markdown and two
docstrings had changed since.

The mechanism: that branch has no unit test and was covered only by REGENERATING a pool map inside
`test_villages.py`. A gate run that follows a `consts.py` value change invalidates the gen cache, so the
maps really are rebuilt and the line executes. A gate run on an otherwise unchanged tree serves those
maps from the cache, the generator never runs, and the line is uncovered. **Same code, same seeds,
coverage green or red depending on whether a cache happened to be warm** - and it presents as a
mystery regression, which is how twenty minutes went on diffing a tree against itself.

Fixed the way the other two of these were fixed today: the branch now has a direct unit test
(`test_a_web_lane_end_already_near_the_network_is_SNAPPED_onto_it`), so its coverage no longer depends
on cache state.

**This is the same defect family as the rest of the day, aimed at the test bed instead of the engine**:
the coverage number's INPUT is not the quantity it is taken to describe. It is read as "is this branch
tested" and it actually measures "did this branch execute during this run", which for cache-served work
is a different question. Three branches in `ways.py` and one in `hinterland.py` were in that state
before today - all four had real behaviour, none had a test, and all four looked tested.

**Worth a sweep by whoever next has an afternoon**: any branch whose only coverage comes from a pool
regeneration is in this state. `pipeline/regen.py` prints CACHED / REGENERATED per map, so a cheap probe
is to run the gate twice in a row on an unchanged tree and diff the two coverage tables - anything that
appears in the second run's missing list is cache-covered rather than tested.

## OPEN 2026-08-19, HANDED TO THE WATERFIELDS OWNER: the FLOODED paddy tint has collapsed to zero pool-wide

Found by settlement-review on Sawada, confirmed across all four scripted hamlets. SVG fill census on the
shipped renders: **sawada 0 FLOODED against 813 rice fills, inashiro 0/627, kashikawa 1/806, mizuguchi
1/512**. `flooded_plots` is ABSENT from sawada's and inashiro's manifests entirely, so
`flooded_plots_read_as_basins` has no input and cannot fire - the "a check that never runs looks exactly
like a check that passes" shape, reached because the feature it guards vanished rather than because
anyone waived it. Sawada's own notes record the opposite state as recently as 2026-08-16: "4 basin-shaped
flooded strips survive (SVG fill census: 4 painted, 4 recorded, 1:1)". Nothing in the review log records
the drop.

It matters most on the map it is missing from: 818 basins over ~60% of Sawada's sheet are now one flat
green, and the uniform green is deliberate (`RICE_GREENS` holds the same green three times - "rice at ONE
stage"), so the FLOODED tint on the low plots by the drain is the ONLY in-field water texture the
doctrine allows a paddy. On the map named 沢田, "marsh paddy", there is none.

**MEASURED CAUSE - and MY FIRST MEASUREMENT OF IT WAS WRONG, corrected here by the waterfields owner
who re-measured it.** What I published (and pushed) was "1,329 candidates reach the seams pass, ~1,261
killed by solidity/outfall/aspect". **That 1,329 is not a candidate count.** `pointed_ring` has SEVEN
call sites inside `seams.py` (732, 759, 783, 846, 897 twice, 991) and only the last is the tint ladder,
so wrapping the function counted the entire weld/gate/toe machinery. The owner reproduced my exact 1,329
by patching it the same naive way, which is how the error was caught.

THE REAL NUMBERS (Sawada seed 6, exact spec from its gen file, instrumented on the ladder's own
exclusive predicate `tapers_to_a_point` - one call site, line 992 - and by wrapping `comb.close_seams`
rather than `seams.close_seams`, since `comb.py` did `from .seams import close_seams` at import so
patching the seams attribute silently does nothing):

    FLOODED entering close_seams:    2  of 706 plots
    FLOODED leaving close_seams:     0  of 812 plots
    painted in the SVG:              0
    plot-shapes the ladder judged:  10        (not 1,329)
    of those 10: solidity killed 3, aspect killed 1 (one plot both), taper 0, outfall 0

**So the carve hands the ladder two blue plots in seven hundred.** The ladder is not massacring
candidates - there are never more than a handful. Solidity does dominate among the demotions (3 of 4),
which was my guess, but demotions are not what empties the map.

**THE ACTUAL MECHANISM IS UPSTREAM, in `carve.py:338` and `:356`:**

    abuts = li == nlev - 1                                     # ONE plot per column - the last level
    fill  = FLOODED if (abuts and R.random() < 0.45) else ...  # then a coin flip on that handful

Eligibility is one plot per column reaching the collector - about five per hamlet - and 45% of five is
two. A five-clause ladder applied to two plots reaches zero routinely. Sawada's "4 painted, 4 recorded"
on 2026-08-16 was the same fragile draw landing better, NOT a healthier system.

**DO NOT RELAX SOLIDITY OR ASPECT.** Each is doing its job on a genuine offender, and relaxing 0.85 buys
back at most three plots on Sawada while re-admitting the pond-like blobs it was added for. The question
the fix must answer is what blue MEANS: the doctrine in the code says "the closing rank pooling before
the outfall", which is a RANK, while the implementation tints a 45% random sample of one-plot-per-column.
Those are different pictures, and the second cannot survive any demotion ladder at all.

**THE DURABLE HALF, also not yet done and worth more than the tint**: there is no gate that fires when a
paddy map with `wet_plots` populated paints ZERO flooded basins. That absence is why a documented feature
went 4 -> 0 with nothing noticing, and it is the exact defect family this whole day has been about - an
absent key is indistinguishable from a satisfied check. The rule wants writing WITH the fix, because
adding it today would simply fail all four maps. Suggested shape: on `generated_by` + hamlet/village +
`wet_plots` non-empty, require `flooded_plots` to be present and non-empty, or an explicit meta key
recording that the ladder rejected every candidate and why. **AMENDED by the owner, and the amendment is
the load-bearing part**: assert against the CARVE'S CANDIDATE COUNT as well, because a map can honestly
have no eligible plot, and a check that cannot tell "no candidates" from "every candidate demoted" will
be waived the first time it fires on a legitimately dry map.

**THE OWNER'S RECOMMENDED ANSWER, and the one item on this page that genuinely IS a GM ruling**
(2026-08-19): tint the **CLOSING RANK as a coherent group** - which is what the code's own doctrine
already claims blue means - and change none of the five demotion clauses. Note why this one goes to the
GM when the furrow question two sections down does NOT: Principle XII's knob rung covers two attested
FORMS of the same thing, and this is not that. It is a question about what a feature MEANS, and the
record cannot answer it because the record never had our palette. So it is genuinely a ruling, it is
queued, and nothing should be built on a guess about it.

**AND IT GATES THREE OTHER ITEMS, so do not fix them one at a time.** The tint eligibility, the
`hem_block_len` knob, the paddy WIDTH floor and the 0614 cohort residue all land in the same toe pass,
and the waterfields session has batched them deliberately as ONE feature. Fixing any one alone means
rewriting that pass again for the next - which is the specific waste this note exists to prevent.

## OPEN 2026-08-19: the dry-hem furrow variety falls off a ONE-FOOT CLIFF at 56 ft, and its check goes blind with it

The furrow-angle machinery in `waterfields/carve.py:834-838` is a maximize-separation algorithm: it
collects the angles of already-placed plots within `ADJ2` (56 px), takes the WIDEST angular gap between
them, and seats the new plot's furrows in the middle of it. When it works it works well. **When `nb`
comes back empty it degenerates silently**: `edges` is just `[lo, hi]`, the widest gap is the whole
allowance, and every plot gets `(lo+hi)/2` - which is exactly `theta0`, the contour angle - plus a
`R.uniform(-0.03, 0.03)` jitter worth +/-1.7 degrees.

**ADJ2 is 56 px and the plots are now 54-59 px apart, so which side of the cliff a map lands on is
luck:**

    kashikawa  closest centers 54.4 ft  -> neighbors seen  -> furrow spread 33.98 deg   healthy
    mizuguchi  closest centers 55.7 ft  -> neighbors seen  -> furrow spread 32.37 deg   healthy
    sawada     closest centers 57.0 ft  -> NONE seen       -> furrow spread  3.27 deg   collapsed
    inashiro   closest centers 58.5 ft  -> NONE seen       -> furrow spread  3.15 deg   collapsed

A one-foot difference in plot spacing is the whole distance between a patchwork of family strips and one
ruled hatch laid across the hem. `settlements`' own doctrine calls for the patchwork
(`segments_05c`: "Fragmented dry holdings were a mosaic of family strips, each plowed to its OWN
orientation"), and `meta.dry_furrows_vary` is declared True on all four - so two of them declare a
variety they do not draw.

**AND THE CHECK GOES BLIND AT THE SAME MOMENT, FOR THE SAME REASON.**
`dry_plot_furrows_vary` compares only plot pairs whose CENTERS lie within `min(50.0, 1.25 * mean_side)`.
Mean side is 81-87 ft on all four, so the formula wants ~102 and the **cap forces 50** - below every
map's closest spacing. It compares ZERO pairs on all four maps and has been vacuous the whole time.

The generator's own comment explains the pairing and it is sound reasoning: the radius "stays UNSCALED:
`dry_plot_furrows_vary` judges adjacency at this px radius on every map, and a generator that varies over
a WIDER circle than the check demands is safely conservative". 56 > 50, so the generator IS the wider of
the two, exactly as intended. **What defeats it is that BOTH are absolute px radii while the thing they
measure grew.** The two guards were calibrated against each other rather than against the plots, so when
the plots outgrew them they went silent together and neither could catch the other.

That is the day's pattern in its purest form: a check and a generator agreeing perfectly with each other
about a quantity that no longer describes the map.

**FIX DIRECTION, and it must land on BOTH SIDES AT ONCE** (fixing only the check turns the gate red on two
maps whose generator cannot produce variety): scale both radii to the plots actually on the map - the
check's own `1.25 * mean_side` is the right shape, so uncap it, and give the generator the same measure
plus a margin so it stays the wider of the two. Then re-measure the spread on all four; the two healthy
maps show what the machinery does when it can see its neighbors.

**FIXED, AND THE NUMBER IS OVER-CORRECTED - the fix stays in, the value is queued to the GM.** Scaling
both radii to the plots landed all four maps at 96-104 deg of spread (from 3.15/3.27 on the two collapsed
ones and ~33 on the two healthy ones). That is strictly better than 3 deg and the two-sided blindness was
a genuine bug worth fixing regardless - but 3 deg being wrong does not make 102 right, and the waterfields
owner supplied the prior that says it is not:

  - In an open-field system the strips group into **FURLONGS, and a furlong shares ONE orientation**; the
    direction changes BETWEEN furlongs, chosen from the lie of the land for drainage. Coherent block,
    varied blocks - not varied neighbors.
  - The physical reason is the decisive one: adjacent strips at a large angle **drain into each other**,
    and a plowman turns at a **shared headland**. Two neighbors 100 deg apart have neither. That is not a
    stylistic objection, it is what furrows are for.
  - Our own code already says it. `carve.py:656`: "the furrow direction is the contour heading, varied per
    plot" - varied AROUND the contour, not maximally separated from the neighbor. With
    `furrow_spread = 1.1` rad (+/-63 deg), a 96-104 deg spread means the algorithm is pushing neighbors to
    opposite ends of the permitted band: the band's outer limit doing the work rather than the contour.

So the algorithm's SHAPE is suspect, not only its radius - maximize-separation produces exactly the
neighbor-vs-neighbor contrast the furlong evidence argues against. The likely target is a modest spread
around a block-coherent grain, with the larger changes between GROUPS of plots rather than between every
adjacent pair.

**SUPERSEDED 2026-08-19 - do not act on this paragraph.** It read: *"Neither session is picking the
number. It is a legibility-vs-accuracy trade of the kind this project sends to the GM rather than
deciding quietly ... Queued to him beside the FLOODED-tint decision."* It was withdrawn from the GM's
queue the same evening, and the error is kept because it misreads Principle XII rather than the
evidence. The ladder is: research it -> decisive means implement what it says -> **two supportable
forms means roll a KNOB per settlement** -> only a SILENT record earns a GM ruling. The waterfields
owner jumped to the fourth rung because the NUMBER felt like a judgment call - and it only felt that
way because they were trying to pick ONE spread for every hamlet, which is precisely what that rung
exists to prevent. The record here is neither silent nor decisive-for-one-form, so this is the knob
rung. See "THE ANSWER IS A KNOB" below, which is the live disposition.

**REVIEWED, AND THE VERDICT IS SHARPER THAN EITHER SESSION'S GUESS: the RANGE is right, the
DISTRIBUTION is wrong** (settlement-review with a research pass, 2026-08-19). ~102 deg reads as a mosaic
rather than chaos - the hem never fragments, every parcel's hatch is internally clean, and the two
already-healthy maps were not damaged (Kashikawa "reads as a genuinely handsome quilt"). So do NOT narrow
the allowance.

What is wrong is the SHAPE of the angle field. `_dry_fields` maximizes separation - it seats each plot in
the widest gap its neighbors leave - and the measured signature is a **hole at zero**: Sawada's median
neighbor delta is 52.1 deg out of a 126 deg fan and NO pair is under 13.9. A real hem's neighbor-delta
histogram is bimodal, a pile near 0 (same block, same owner, same outfall) with a few big jumps at block
seams. The sourced record is decisive on the mechanism:

  - a FURLONG is "a group of strips or lands all oriented in the same direction", and "adjacent furlongs
    often ran at different angles to one another, which is why you sometimes see ridge and furrow
    changing direction as you cross a field boundary" (Nottingham/Laxton; Evershot; Fieldworthy). The
    variety lives at BLOCK scale with agreement INSIDE a block.
  - blocks were "orientated in such a way as to take advantage of the topology of the land and so further
    assist the drainage" - direction is DERIVED from slope and outfall, not free.
  - strips were long and narrow "to reduce the number of times the plough-team had to turn", sharing a
    headland at each end (DigVentures), and were "separated from their neighbours by a double furrow, or
    ... an unploughed grass balk" (How-to History) - a boundary form that only exists between PARALLEL
    strips.
  - the East Asian record does not overturn it: contour ridging is the documented STEEP-SLOPE measure
    (FAO Nishi-Awa), which `fields.md` already declines to apply on a gentle hem, and fragmented
    smallholdings make per-parcel choice more available - but shared slope, a shared outfall and a shared
    parcel shape still push neighbors toward agreement. The East Asian record is SILENT on the angle
    field specifically.

**AND THE CHECK CODIFIES THE WRONG MODEL.** `dry_plot_furrows_vary` forbids two plots within ~50 px from
running within ~6 deg - i.e. it forbids the attested arrangement outright, which is precisely why the
generator has to anti-correlate. Fixing the generator without re-scoping the check would just make the
gate red on the correct answer.

**THE ANSWER IS A KNOB (Principle XII), not a number.** The record supports BOTH a furlong-block hem (3-6
adjacent parcels sharing a direction, changing at seams) and a fully fragmented per-parcel hem, and at
~1,500 ft of hem those give 2-5 direction domains versus 28 - instantly distinguishable at fit zoom, which
is the different-but-plausible-places goal exactly. Sketch from the reviewer: roll `hem_block_len` from
the seed (1 = today, 3-6 = furlong-like), assign a direction per BLOCK, seat blocks by maximize-separation,
let parcels inside a block share it with a small jitter - and re-scope `dry_plot_furrows_vary` to compare
BLOCKS, or it fires on every block interior.

**ONE CONCRETE DEFECT THE GREEN GATE PERMITS, worth fixing whatever happens to the knob**: a 13.9 deg
neighbor pair reads as one plot bisected rather than two holdings - Sawada's stacked pair at (740,3097)
and (742,3028), and Mizuguchi's twin at 11.5 deg. The gate's 6 deg floor is a CONSERVATION threshold, not
a legibility one, so roughly 6-20 deg is the worst of both worlds: too different to be one block, too
similar to read as two. Do not simply raise the 6 deg - that punishes the honest near-parallel case. Give
the GENERATOR a minimum separation (~20 deg) for edge-adjacent parcels, or adopt the block model, where
near-parallel neighbors become correct and the jump moves to the seam.

**Owner: `waterfields/`, taking BOTH halves.** The furrow angle sits three lines from the tint eligibility
that session is about to change, so splitting them would be worse than either session holding both. A
caution recorded with it: a VISUAL reviewer can say whether 102 deg looks tidy - a map where every plot is
distinguishable does look tidy - but cannot say whether two adjacent plots at that angle could both drain,
which is the question that decides it.

## OPEN 2026-08-19: the kura roll under-delivers 2.2x, the fix WORKS, and it exposes a packing defect that blocks it

Two findings, and the second is why the first is not shipped. Both measured; the fix is written out below
so the next session re-applies rather than re-derives it.

**FINDING 1 - the kura (farm shed) rate is 13.6% against a documented ~30%.** Counted on the shipped
pool: 9 for 66 farmhouses - inashiro 3/15 (20.0%), sawada 5/19 (26.3%), kashikawa 1/20 (5.0%), and
**mizuguchi 0 of 12**. A twenty-household hamlet in which nobody stores grain. Two compounding causes:

  1. **ALIASING.** The roll is `self._hjit(x, y, 3.0) < 0.30` and `_hjit` is the GLSL
     `fract(sin(dot) * 43758.5453)` hash. It is sampled along a front row that steps down a field margin
     at near-uniform pitch - the textbook worst case, because the argument advances by a near-constant
     number of cycles per step so successive samples drift instead of decorrelating. Measured at ~105 ft
     along a cluster's own axis it returns mean 0.628 and 18% under 0.30, not 0.5 and 30%.
  2. **THE ROLL IS UNAUDITABLE**, which is why a 2.2x shortfall sat in the pool with every check green.
     It is evaluated at the CANDIDATE coordinate and `_place_bundle` then MOVES the bundle, so the
     position that decided is not the position recorded. Nothing in the artifact can reproduce it.

**THE FIX, verified and then reverted.** Add an avalanche integer hash and key the roll on the household
COUNT (which `settlements/homesteads.md` already names as the alternative, and which makes the decision
reproducible from the manifest):

    @staticmethod
    def _nth_roll(n: int, salt: int) -> float:
        v = (int(n) * 2654435761 + int(salt) * 40503) & 0xFFFFFFFF
        v ^= v >> 15
        v = (v * 2246822519) & 0xFFFFFFFF
        v ^= v >> 13
        v = (v * 3266489917) & 0xFFFFFFFF
        v ^= v >> 16
        return (v & 0xFFFFFFFF) / 4294967296.0

    # at houses.py's kura line, replacing the _hjit call:
    _shed = kind == "plain" and (role == "headman" or self._nth_roll(len(self.M.get("houses") or []), 3) < 0.30)

Measured: the hash returns mean 0.4989 and 29.65% under 0.30 over 2,000 draws (against 0.628/18%), and
the pool goes to **23/66 = 34.8%** - inashiro 40.0, kashikawa 30.0, mizuguchi 41.7 (from zero), sawada
31.6. Slightly over 30 because `headman` keeps an unconditional kura, which is a role rather than a roll.
**Do NOT replace `_hjit` generally** - it is correct for a per-feature ATTRIBUTE (house aspect, garden
size) where neighbors differing is the point and the samples are scattered. It is wrong for a per-household
RATE.

**FINDING 2, and the blocker: a RAKED house corner bulges into a NEIGHBOR'S GARDEN, and the packer cannot
see it.** With the kura rate corrected, Kashikawa fails `features_do_not_overlap` and
`gardens_clear_of_structures` at (2309,2814). Measured: the garden (15.2 x 24.2, owned by the house at
(2271.3,2785.8)) sits 2.1 ft clear IN Y of the neighbor house at (2329.6,2842.0) on axis-aligned rects -
so the boxes do NOT overlap - but the gate reads `rect_corners` WITH the rake, and +/-5 deg on a 57.6 ft
house swings a corner ~2.5 ft. The 2.1 ft margin is eaten.

`rolling/fit.py` states the scope honestly: the tread test is "THE HOUSE ONLY ... The yard, garden and
grove are drawn axis-aligned, so for them the rect already IS the drawn footprint", and bundle separation
is by whole-bundle BBOX, which (its own comment, line 172) "knows nothing about either house's rake".
There is a rake-aware rule for house-to-HOUSE (`FARMHOUSE_EAVE_GAP_FT`, added when a re-pack left two
roofs 2.0 ft apart) and none for house-to-neighbor's-GARDEN. **This is the same placer-vs-check mismatch
the whole day has been about** - the placer measures unraked rects, the gate measures drawn ones - and it
was simply latent until tighter packing found it.

**Why the kura fix is reverted rather than shipped**: Principle XIII, and the honest fix for finding 2 is
a rake-aware garden clearance in the bundle fit, which `fit.py` warns "would re-pack every nucleated map"
- too wide to land and verify in the same sitting. Re-apply the patch above WITH that clearance, and
expect the whole pool to move.

## OBSERVATION 2026-08-19: two DIFFERENT failure shapes, and conflating them costs the second lesson

Across two sessions this day produced five retractions and roughly a dozen engine defects. It is tempting
to write them up as one pattern. They are TWO, and the waterfields session corrected me when I collapsed
them - the correction is the useful part, so it is recorded rather than smoothed away.

**SHAPE 1 - the instrument cannot discriminate.** A measurement whose INPUT cannot contain the failure it
names. `cluster_shape` fed a pass that never ran (honored on 1 of 48 seeds). The honesty guard compared a
drawn aspect against a mechanism parameter, then compared it on the PAGE's axes so a diagonal band read as
1.22 instead of 3.83. The woodland scan vetted a square while the gate measured a rotated bbox. The
way-vs-water tests never received `M["streams"]`. `dry_plot_furrows_vary` compared zero pairs. The paddy
floor gates AREA while the defect is WIDTH. The gen-time budgets described solo CPU while measuring
parallel-run CPU. Four branches were "covered" only by a warm gen cache. And my own count of 1,329 tint
candidates was seven call sites of a shared predicate.
**Remedy: a second measurement that has to disagree** - a detached-worktree baseline, a control assertion
that the setup produces the thing being tested, an independent reviewer looking at the drawing.

**SHAPE 2 - the instrument is fine and the ATTRIBUTION is wrong.** The waterfields session measured a real
ripple correctly and assigned it to the wrong cause, because the baseline was an older HEAD and a peer's
lane-web feature had landed inside the window. The number was right; the story about what produced it was
not.
**Remedy is different and does not follow from the first: NAME THE COMMIT a measurement is taken against.**
No amount of instrument-sharpening prevents this one - a session doing shape-1 discipline perfectly still
gets it wrong this way, which is exactly what happened.

Keep them apart in any future write-up. "Check your instruments" does not cover shape 2, and a session
that has internalised only shape 1 will still misattribute a correct number.

## OPEN 2026-08-19: every lane junction draws a cap bead, and one back lane halves its width mid-run

Settlement-review on Inashiro, and the GM has named this class before ("really looks like a rendering
error"). Two defects at the same junctions.

**THE BEAD.** `water_ways.lane()` emits each lane as TWO consecutive records - a soft worn-earth shoulder
(`width + 2.5`, opacity 0.4, `stroke-linecap="round"`) and then the packed-earth tread (`width`, opacity
0.9) - both into the same `add` stream. So the records interleave PER LANE: A-shoulder, A-tread,
B-shoulder, B-tread. Where B meets A, **B's round-capped shoulder is painted over A's finished tread**,
and the reader sees a circular seam across the roadway. Measured on Inashiro at (1185.0,785.0) where
`lanes[3]` meets `lanes[4]`, and again at (1249,801), (1270,1183), (1279,1312).

**THE WIDTH STEP.** Compounding it at the same node: `lanes[3]` is `w=6` (drawn 8.5/6.0) and `lanes[4]` is
`w=3` (drawn 5.5/3.0), so one continuous ~230 ft back-lane run **halves its width where nothing happens**.
`ways.py:695` gives a link the width of the way it JOINS and leaves its far neighbour at 3.

**TWO CANDIDATE FIXES, PRICED, NEITHER TAKEN TONIGHT:**

1. **Paint all lane SHOULDERS before all lane TREADS.** Removes the bead completely and moves no geometry,
   which is what makes it attractive. But it needs a deferred flush - shoulders at `lane()` time, treads
   collected and emitted later - and lane z-order is part of the DRAW ORDER contract in the skill's
   CLAUDE.md. That doc's own rule is that an ordering change wants every dependent path read in ONE
   batched pass before it is attempted, because the failure mode is discovering the order one gate
   failure at a time. Several features deliberately layer between or above lanes (the kido bar, crossing
   decks, the notice board's caption), so this is a read-everything-first change, not a one-liner.
2. **Draw each connected chain as ONE stroked path.** Removes the bead AND the width step together, since
   a chain has one width, and is the more honest model - a web of lanes IS a network, not a pile of
   independent strokes. Bigger: it needs the chains computed (the connected components the joiners
   already build) and every per-record consumer checked, since `M["lanes"]` records would change shape.

**Not attempted at the end of a long session on a documented contract.** Deferred with the measurement per
Principle XIV's architectural clause. The bead is cosmetic but it is the GM-named "looks like a rendering
error" class, so it should not sit indefinitely.

## OPEN 2026-08-19 (waterfields): the paddy area floor cannot see WIDTH, so the NE margin frays into needles

Settlement-review on Kashikawa. `paddy_basins_are_worth_their_bund` gates basin AREA, and the defect is
WIDTH. The basin at **(2273,1985) is 5.9 ft wide by 53 ft long** - 8.9:1, 312 sq ft, **0.21 of the design
cell against a 0.20 floor, so legal by 0.01** - and it is narrower than the two bund strokes that bound
it, so it draws as a doubled line rather than as a basin. Not alone: **9 basins under 12 ft wide and 30
under 16 ft** (median width 29.1), concentrated at x 2070-2300, y 1550-2110 where the comb meets the drain
hem. At 3x that wedge reads as lattice damage - needles, a 4-5 way bund starburst near (2054,1516), and
slivers whose two long sides overlap into what looks like a bund dead-ending mid-basin.

This is the GM's original complaint ("looks like a rendering artifact rather than something from our
historical research") surviving the fix aimed at it, because the fix measured the wrong quantity: a
scrap's AREA can clear the floor while its WIDTH makes it undrawable. Same family as everything else in
this file.

FIX DIRECTION (from the reviewer): add a minimum working width - `area / longest side` - to the toe pass
AND to the gate, derived rather than picked; a basin must be wide enough to stand in and puddle, which
puts it somewhere in the 12-16 ft band. `research/fields.md` "Minimum basin SIZE" already holds the
reasoning frame, including the point that the alternative to a scrap is making its neighbour bigger.
**Owner: `waterfields/`** - same subsystem as the FLOODED tint and `hem_block_len`, and the toe pass is
where all three meet.

## OPEN 2026-08-19 (small, unclaimed): the notice-board caption's halo notches the lane it stands on

Settlement-review on Inashiro. The kosatsuba caption is seated directly above or below the glyph
(`fixtures.py`: `(x, y - hh - 11)` or `(x, y + hh + 11)`) and drawn with a 3 px background halo
(`paint-order="stroke" stroke="#EFE3C2"`). On Inashiro the board sits at (1224,1009) and `lanes[1]` passes
x~1235 at that y with w=5, so the halo knocks a visible notch out of the map's busiest internal lane,
between the words "notice" and "board". Verified in the ink at 9x. It is the founding-run "caption pierced
by its own feature" defect inverted - here the caption does the piercing.

FIX DIRECTION (reviewer's): seat the caption on the side away from the way - this board has ~40 ft of
clean dooryard to the west - or draw captions before the lane fill so the lane wins.

**MOSTLY FIXED 2026-08-19 - lateral seats, scored on the caption's own BOX.** Candidates are now below /
above / east / west, and the score is the clearance of the whole TEXT BOX rather than of its anchor,
because the halo is what notches the lane and the halo follows the box. Half-width is estimated from the
string (8 pt italic at ~0.28 em/char predicts 26.9 px against a measured 26.4) since the seat must be
chosen before the text is laid out. Below is tried first, so an unblocked board does not move.

    inashiro  was notching -> 19.2 ft clear    mizuguchi -1.9 ft OVERLAPPING -> 9.7 ft clear
    sawada     6.9 ft unchanged                kashikawa  0.2 ft unchanged (see below)
    Gate green (3434), cohort 43/48, zero regressions, captions present on all four.

**FIXED, AND MY EARLIER CONCLUSION HERE WAS WRONG - corrected rather than quietly replaced.** This entry
previously said a tilted board "cannot be moved by either obvious lever, which is now proved rather than
suspected", on the strength of three no-op measurements. That inference was bad: I concluded NO SEAT IS
BETTER from THE SEATS I TRIED WERE NOT BETTER. Enumerating all ten candidates on Kashikawa shows a good
one exists.

    above=False  gap 11 -> 2.0 ft   gap 16 -> -1.0   gap 21 -> 1.0   gap 28 -> -0.3   gap 36 -> 7.7
    above=True   gap 11 -> -2.2     gap 16 -> -0.8   gap 21 -> 0.5   gap 28 -> 5.6    gap 36 -> -2.0

**Clearance is NOT MONOTONIC in the offset**, because a board sited at the traffic optimum has ways on
more than one side - moving away from one walks toward another. A ladder that stopped at 21 took the first
rung and left the caption on the tread; the good pocket is at 36. Extending the ladder past the dip moves
Kashikawa from **0.2 ft to 6.9 ft** (hug 36.8, which the pool already carries - inashiro and mizuguchi sit
at 41.0 and pass `label_hugs_its_referent`).

What WAS true and remains true: the LATERAL slide is geometrically incapable of helping, because
`kosatsuba_faces_the_road` makes the baseline parallel to the lane, so sliding along it holds the
perpendicular distance constant. That lever stays reverted. The `gap` axis is perpendicular to the
baseline and is the one that works.

    inashiro  notching -> 19.2 ft      mizuguchi -1.9 (overlapping) -> 9.7 ft
    kashikawa 0.2 -> 6.9 ft            sawada 6.9 ft unchanged

**THE RULE IS NOW ENFORCED**: gate 0617 `captions_clear_the_ways_they_stand_on` fails any caption whose
recorded BOX comes within 2 ft of a lane's tread edge - the halo follows the box, and 2 ft is the 3 px
halo plus antialiasing either side. Fixture frozen; it is a CONSTRUCTED break (the caption placed on the
busiest lane) rather than a replayed original, because the board and lanes have moved across many
regenerations and the pre-fix geometry is no longer reachable from the manifest - the provenance note
says so.

**AND THE RULE IS STILL NOT ENFORCED.** Nothing checks that a caption's halo clears a way. 0.2 ft passes
today and is one re-pack from a defect with nothing that would notice - the same silent-flip shape as the
56 px furrow radius against 54-59 px plot spacing. Write the check WITH the tilted-frame fix; adding it
now would fail Kashikawa.

**A NEAR-MISS WORTH KEEPING.** While adding the lateral seats I put `self.label(...)` one indent level too
deep, inside the final `else:`, so any board on the TILTED branch drew its glyph and silently lost its
caption - Kashikawa shipped a 12 x 5 ft mark that nothing on the sheet identifies, with every check green.
It surfaced only because the clearance probe reported caption COUNT alongside distance and returned a
sentinel rather than a number; reading that sentinel as "infinitely clear" would have shipped it. The line
carries a comment now, because an indent level is exactly what a later refactor re-breaks.

**And a process note on this entry itself**: two scripted attempts to update it reported success and
changed nothing, while the code commits went through - so for two commits the ledger described work that
was already done as "not done here". Anchor-based patching of prose fails silently in a way that anchor-
based patching of code does not, because nothing later imports a paragraph. Verify the grep after editing
a ledger entry, or edit it by hand.

## OPEN 2026-08-19: gate 0617 finds caption notches on five cohort seeds the seat ladder cannot clear

`captions_clear_the_ways_they_stand_on` shipped with the caption-seat work and fires on cohort seeds
**1, 7, 14, 33, 36**. The cohort reads 38/48 against 43/48 - and that is a MEASUREMENT changing, not maps
getting worse. A new check cannot regress a seed in the passed-before/fails-after sense: it was never
green there because it was never run there. Same handling as `paddy_bunds_do_not_stagger` (0614), which
ships while firing on seeds 12 and 39.

**They are genuine.** Spot-checked by rebuilding each seed and measuring the caption box against the lane
tread directly: seed 1 **-0.5 ft** and seed 7 **-1.3 ft**, i.e. the halo is ON the tread. Both boards are
raked (rot 51.6 and 52.1). The four pool maps all clear comfortably (19.2 / 9.7 / 6.9 / 6.9 ft), so the
seat ladder works where there is anywhere to go and fails where the board sits in a tight lane crotch.

**A DISCREPANCY, CHASED AND RESOLVED - and it was my probe that was wrong, not the rule.** Seed 14 fired
in the gate while an independent probe of mine measured its worst caption-to-tread at +14.5 ft. Two
instruments on one manifest disagreeing is not something to tune around, so I re-measured per LABEL: seed
14's notice-board caption is at **-1.6 ft**, squarely on the tread. The check is right and correctly
scoped - it fires on the FIXTURE's caption, not on the title placard or scalebar, which was the failure
mode I was worried about. All five seeds are genuine notches (seed 1 -0.5, seed 7 -1.3, seed 14 -1.6).

That is the tenth measurement of mine to mislead in one session, and the tenth caught only by taking a
second one. It is worth stating the rule that keeps working: when a check and a probe disagree, re-measure
the QUANTITY THE CHECK NAMES, per record, before believing either.

**THE PROPER FIX, once the discrepancy is settled**: the kosatsuba hand-rolls its caption seat, while the
engine already has an outward-walking search for exactly this - `clear_label_seat` in
`structures/captions.py`, used through `place_caption`, which scores candidates against `label_blockers`
and walks a standoff ladder. Routing the board's caption through that engine instead of a bespoke
five-rung ladder is the change that would clear the tight seeds, and it deletes code rather than adding
it. What has to be handled: the board's caption carries the board's TILT, and `place_caption` takes a
`rot`, so the tilt survives - but the interaction with `linear_tilt`'s clamp needs checking before the
swap.

## OPEN 2026-08-19: the five caption notches need a 2D seat search, and the engine's own search is not a drop-in

Follow-up to gate 0617, which catches genuine caption-on-tread notches on cohort seeds 1, 7, 14, 33 and
36. Two findings about how to clear them, so the next attempt does not repeat mine.

**ALL FIVE FAILING BOARDS ARE TILTED** - sampled at rot 51.6 (seed 1), 52.1 (seed 7) and 128.9 (seed 14).
They therefore take `fixtures.py`'s TILTED branch, and that branch searches a SINGLE AXIS: perpendicular
to the board's baseline, both ways, at five distances. The untilted branch searches FOUR directions. A
board whose perpendicular line runs between two lanes has no distance along that line which clears,
however many rungs the ladder gains.

So the tilted search wants to be **2D - gap x lateral**. This does NOT contradict the earlier finding that
the lateral slide is useless: it is useless ALONE, because `kosatsuba_faces_the_road` makes the baseline
parallel to the lane, so sliding at a fixed gap holds the perpendicular distance exactly constant. At a
LARGE gap it becomes a different question, because the caption is then beside a different stretch of
frontage. **Try the 2D grid before adding rungs to the 1D one.**

**THE ENGINE'S EXISTING OUTWARD SEARCH IS NOT A DROP-IN**, which corrects a suggestion I made one commit
earlier. `clear_label_seat` (`structures/captions.py`) rings outward through 16 rings and is exactly the
right shape - it exists because verge-hugging features sit at the busiest node and nine rings ran out on
Minami. But `label_blockers` collects only manifest dicts carrying x/y/w/h, and **a lane record has `pts`
and no x/y, so lanes are NOT blockers**. Routing the board's caption through it would dodge structures and
still notch the tread. Making lanes blockers is a change to every caption in the engine and wants its own
pass with its own oracle.

**A CAVEAT ON MY EVIDENCE, recorded because it would otherwise read as stronger than it is**: I did extend
both ladders (tilted gap to 60; untilted four directions x six distances to 60 px) and measured no change
on the five seeds - but an auto-sync reverted that edit before it was committed, so **that measurement is
not reproducible from the current tree and should be re-taken rather than trusted**. The rot values above
were measured independently and do stand.

## 2026-08-19: the caption seat search, seven attempts - what worked, and THREE CLAIMS OF MINE THAT WERE WRONG

Gate 0617 caught caption-on-tread notches on cohort seeds 1, 7, 14, 33, 36. **All five are now clear
(38/48 -> 43/48, zero new failures).** Getting there took seven attempts, and the reason it took seven -
two of them measuring code that was never applied - is the useful part. Three claims of mine in this
section were wrong; they are corrected below rather than edited away, in the order I made them.

**WRONG CLAIM 1: "all five failing boards are TILTED".** They are not. `linear_tilt` **CLAMPS** past 45
degrees rather than folding - its own docstring says so at length and warns it must never be confused with
`label_tilt`, which folds. So boards at rot 51.6, 128.9 and -83.3 all return tilt **0.0** and take the
UNTILTED branch. I read `rot`, inferred the branch, and spent two attempts improving a code path those
seeds never execute. **rot is not tilt past the clamp.**

**WRONG CLAIM 2: "the outward walk is a no-op".** It was measured against a tree an auto-sync had reverted
mid-experiment, so the measurement was of the old code. Applied properly to the UNTILTED branch it fixes
three of the five seeds. A measurement taken against an uncommitted edit is worth nothing; commit first,
then measure - which is now how this session does it.

**WHAT ACTUALLY LANDED - and read WRONG CLAIM 3 below before trusting items 3 and 4 of this list.**
They are described here as verified. Two of them were not in the tree when that was written.

1. **The scorer reads the lane's tread EDGE**, which is what gate 0617 reads. It read the CENTERLINE -
   `street_runs` returns polylines with no widths - so it was optimistic by half a lane width (~2.5-3 px)
   and every "best" seat was best by a measure the rule does not use. The placer-and-check-read-one-source
   rule, broken in code written to enforce it.
2. **The untilted search walks outward** (four directions x six distances to 60 px) instead of sampling
   four fixed points, the way `clear_label_seat` rings out for verge-hugging features and for the same
   documented reason: such a feature sits at the busiest node, so its surroundings are the most crowded
   ground on the map.
3. **`label_above` CONSTRAINS the search instead of replacing it.** Its caller sets it from
   `label_seat_clear` - a two-seat verdict about STRUCTURES that knows nothing about lanes - so reading it
   as "place exactly here" skipped the lane search entirely on the boards that set it.
4. **Structures and ways are ONE search.** Every candidate is filtered by the engine's own
   `label_seat_clear`/`label_blockers` and then scored on lane clearance, with the flag kept only as the
   fallback when nothing clears the structures. Honoring the two constraints in separate places is what
   left seats with 22-61 ft of clearance unused.

**WRONG CLAIM 3, and it is the one that cost the most: TWO OF THE FOUR "VERIFIED" CHANGES WERE NEVER IN
THE TREE.** Items 3 and 4 above were written up as landed and verified. They were not. `git log` shows
`136e0398` -> `9805d654` with neither commit in between, and the working file still read
`_lx, _ly = max(_cands, key=_box_clearance)` - the unconstrained line both items claim to have replaced.
Both patch scripts printed success and the `git commit` appeared to run. So the cohort runs that produced
"seeds 14 and 36 still notch after all four changes" were measuring **two changes, not four**, and the
conclusion drawn from them - that the design did not work and my model of the code path must be wrong -
was false. The design was right; the code was absent.

This is the same family as WRONG CLAIM 2 one section up (a measurement against a reverted tree), which
means the lesson did not take the first time. It has now: **after an edit, confirm the string is in the
file, the commit exists, AND the diffstat names the file.** All three. A script's success message and a
clean `git commit` are each, separately, worth nothing.

**WHAT THE INSTRUMENTATION FOUND (one run, and it was decisive).** The previous entry's next step was
right - stop pulling levers, log the actual candidate list. For seed 14: 24 candidates, 3 clearing the
structure filter, the best of those with **7.8 ft** of lane clearance - and the caption drawn at a seat
with **-1.2 ft**. The good seat was being found and then discarded. That is item 3's diagnosis exactly,
which is what pointed at the code being missing rather than the model being wrong.

**THE ROOT CAUSE IS UPSTREAM OF EVERYTHING ABOVE.** `place_kosatsuba` computes `lab` by testing
`label_seat_clear` at the DEFAULT distance only - `y +/- h/2 + 11` - and passes that verdict on as
`label_above`. So a board whose below-seat is blocked at 11 px and perfectly clear at 35 px gets flagged
"above", and the flag then forced the caption to the far side. The premise the flag encodes ("below is
unusable") is a narrower claim than the one it is read as. The fix is not to weaken the flag but to stop
computing it from a question that cannot see the answer: **`kosatsuba` now asks the structure question
itself, of every candidate in its outward walk, and `place_kosatsuba` no longer passes `label_above` at
all.** `lab` is still used, one line up, to prefer a BOARD POSITION where some caption seat exists -
a different question, and a good one.

**`label_above` STAYS A HARD CONSTRAINT for anyone who sets it.** The first version of this fix made the
flag advisory, and `test_kosatsuba_records_a_blocking_struct` caught it immediately (507.1 > 500) - the
test calls `kosatsuba` directly and pins the flag's contract, which exists for the gate-adjacent case its
docstring describes, where the caller knows something the manifest does not. That test was right and the
change was too broad: an external caller's knowledge is not a hint. So the flag now NARROWS the candidate
pool rather than naming a point, and the lane score still chooses within the allowed side.

**RESULT: 43/48, all five caption notches cleared, zero new failures against baseline.** Seeds 14 and 36
are FIXED - the entry above saying they "remain" and are "not understood" was measuring absent code.

## 2026-08-20: the notice-board caption, ATTEMPTS 8-13 - and the one that was never in the seat search

Continues the seven-attempt entry above. What follows cost six more attempts and the whole of it was
spent in the wrong place, so the shape of the mistake is the deliverable.

**THE FINDING THAT STARTED IT (settlement-review, Inashiro).** `label_hugs_its_referent` was never
measured on a notice-board caption in the history of this engine. Segment 262 opens
`if len(L) < 7 or not L[6]: continue`, and `kosatsuba()` never passed `ref=`, so element [6] was null
on every board caption ever drawn. The rule was not lenient - it was ABSENT - and a comment in
`fixtures.py` asserted that two named maps "sit at 41.0 and pass `label_hugs_its_referent`" when
nothing had ever measured them. Adding `ref=` immediately showed 68.5 px of drift on three pool maps
against a 24 px cap. Textbook "a check that never RUNS looks exactly like a check that passes", and
it took an outside reviewer rather than the gate.

**THEN FOUR ATTEMPTS THAT WERE ALL THE SAME MISTAKE.** Cohort readings, in order: 43 (baseline) ->
39 -> 41 -> 42 -> 42 -> 43+. Each attempt fixed a real defect and each left the total short:

1. **Maximizing an unbounded quantity.** `max(_ok, key=_box_clearance)` with clearance rising
   monotonically along the outward ladder, so the LAST rung always won - 60 px of drift and a copse
   clump through the text, to buy 11 ft of surplus over a 2 ft bar. Fixed by satisficing.
2. **A satisficing bar above what the ground offers.** Target set to 5 ft "for headroom", never
   checked against real seats. Seed 14's two best seats are hug 0.0 at 4.8 and 3.3 ft - both legal -
   and the 5 ft bar threw both away and fell through to the fallback. *A satisficing bar above what
   the ground offers is just a maximizer with extra steps.* Now 3.0 (the gate's 2 plus 1).
3. **A hug measure that disagreed with the gate's.** Mine was an axis-aligned box; segment 262 uses
   the rotated QUAD. At -37 degrees the box overstates the gap, so on seed 46 every seat looked
   illegal, the legal pool emptied, and the fallback took a distant seat that failed the real check.
4. **A ring asserted to be a subset instead of constructed as one** - see below.

**THE ACTUAL DEFECT WAS NOT IN THE SEAT SEARCH, AND EIGHT ATTEMPTS WERE.** Read off the engine's own
candidate evaluation (an env-gated dump inside `kosatsuba`, not a reconstruction): seed 14's board has
48 candidate seats, **11 clear structures and every one of them sits west or south where the lanes
run** - best clearance 1.0 ft against a 2 ft bar - while every seat with real room (14.3, 14.2, 8.6,
5.8 ft) is blocked by a building. The board is in the wrong PLACE to be captioned. No seat search can
fix that. `place_kosatsuba` now ranks board positions by whether the caption is SITABLE - structures
AND lanes - ahead of the old structures-only `lab` term, which only ever tested the two default seats.

**THREE MIRRORS, ALL PLAUSIBLE, ALL WRONG** - the reason it took so long to see:

| mirror | how it lied |
|---|---|
| envelope-turn metric | snapped to the nearest VERTEX, so a square anchored mid-edge read 180 degrees where the truth is 0 |
| seat enumerator v1 | omitted the STRUCTURE filter entirely, so it reported ten usable seats where the engine had none |
| seat enumerator v2 | reconstructed coordinates from the RECORDED 12x5, but the drawn `hw/hh` differ, so only 5 of 48 candidates matched and "not offered" was indistinguishable from "my coordinates are wrong" |

Each looked right and each pointed somewhere wrong. The env-gated dump answered it in ONE run.
**When a reconstruction and the engine disagree, stop reconstructing** - print from inside.

**THE STRUCTURAL FIX, which matters more than the bug.** The lane measure is now a METHOD,
`Settlement.caption_lane_clearance`, shared by the seat search and the siting preference. That single
quantity had been re-derived three times in this one function and came back different every time:
the lane CENTERLINE instead of the tread EDGE (four attempts lost to it), an axis-aligned box instead
of the rotated quad, and a near ring at 45 degrees instead of the annulus's own bearings. A rule that
says "the placer and its check must read one source" does not hold by being written down; it holds
when there is only one source to read.

## 2026-08-20: THE INSTRUMENT-DISCRIMINATION FAMILY - five instances, three sessions, one day

Named by the Inashiro session, and recorded here because it is now clearly the dominant failure mode
across this whole effort - more costly than any individual bug any of the three sessions fixed. **The
failure is never in the measuring. It is in the step immediately after, where an accurately-observed
narrow fact is promoted into a broad claim it does not establish.** Every instance passed review at the
time because the underlying number was correct.

| # | the true observation | the unsupported promotion | what it cost |
|---|---|---|---|
| 1 | 7 call sites of `pointed_ring` | "1,329 tint candidates" | a wrong ledger entry, caught by a peer; real figures 2 of 706 entering, 10 shapes judged |
| 2 | a cohort run measured 41/48 | "the unified seat search does not help" | two attempts spent looking for geometric causes; the code was never in the tree |
| 3 | three of 48 seeds are crescent-rolled and fail | "it is a crescent defect" | p ~ 0.04 treated as decisive; a sixth fix attempt against dead code |
| 4 | 60-120 ft of clearance to FABRIC beside each stranded house | "the ground is wide open" | attempt ten; the open ground was flooded paddy, which the measurement did not count |
| 5 | "not in my tree, I have not touched `waterfields/` all session" | "those items are unclaimed" | three sessions nearly rewrote `carve.py` twice |

Instance 5 is the one worth dwelling on, because it is the only one that is not a measurement at all -
it is a **coordination** instance, which shows the family is about inference rather than instruments.
A peer's report about its own working directory is a true statement with a narrow scope; "unclaimed" is
a statement about three sessions. I had better evidence to hand (my own earlier message assigning those
items) and overrode it with the weaker source. Also note instance 4's mirror, recorded in 2b: an
erosion test that says the dry ground stays connected, but counts only crop - so it answers about mud,
not about where a way can run.

**THE REMEDIES, both cheap, and each would have caught a different subset:**

1. **Name the commit a measurement was taken against.** Catches 2 (and the architecture session's own
   retraction, which baselined against a HEAD older than the lane-web feature). A measurement whose
   tip is not stated is not a measurement yet.
2. **Ask what fraction of the POPULATION looks like the signal, before calling it one.** Catches 3 and
   4. The base rate is the check, and it is one line.
3. **For coordination specifically: "not in my tree" and "unclaimed" are different sentences.** A peer
   cannot see the other peers. Only the session that ASSIGNED an item knows who owns it, so ownership
   questions go to the assignment record, never to a third party's working directory.

**A SIXTH INSTANCE, AND IT IS A DIFFERENT KIND OF CLAIM: the SET RELATION.** The five above are all
"measured the wrong quantity". This one is "asserted a relation instead of constructing it", and it
belongs in the same family because it fails the same way - the reasoning is valid, the object it is
about is not what you think it is.

Ranking board positions by caption feasibility, I probed a NEAR RING of 8 seats rather than all 48,
and justified it: the full candidate set is a SUPERSET of the ring, so ring-feasible implies
search-feasible, which is the one-way guarantee a PREFERENCE needs. The argument is sound. **My ring
was not a subset** - it used 45-degree diagonals while the search's annulus runs
30/60/120/150/210/240/300/330 - so a board could be ranked sitable on a seat the search never offers.
Seed 14 did not move, and the cohort read 42/48 twice running for two entirely different reasons.
Rebuilt as exactly the twelve zero-standoff members of the real candidate list, seed 14 passes.

So the discipline has two halves, pointed at two kinds of claim:

- **Measure what the RULE measures** - not a near-enough quantity wearing the same name.
- **CONSTRUCT the subset; do not assert it.** Where an optimization rests on set containment, build
  the smaller set FROM the larger one in code, so the relation cannot quietly stop being true when
  someone edits the larger one.

**And one that generalizes past this project: validate an instrument on inputs whose answer you already
know, BEFORE you point it at the unknown.** The `seat_cluster` edge-turn metric written the same day
snapped to the nearest envelope vertex, so a square anchored mid-edge reported 180 degrees where the
truth is 0 - it would have reported a corner on every map in the cohort and "confirmed" the hypothesis
it was built to test. Three known shapes (square mid-edge 0, square spanning a corner 90, square
half-lap 180) caught it in one run. **An instrument that cannot fail its own sanity case is not
evidence, and a hypothesis confirmed by an untested instrument is worse than no result** - it ends the
investigation.
