# EXPERIMENT: scripted hamlet generation

*Started 2026-08-11 at the GM's direction. Status: **proof of concept, not adopted**. Nothing in the
current method has changed.*

**Load this file when:** you are deciding whether to extend, adopt, or abandon the scripted
generation path, or you are about to work on [`hamletgen/`](l7r/diagram/hamletgen/). To DRAW a map today,
ignore this file - [`SKILL.md`](SKILL.md) and [`settlements.md`](settlements.md) are unchanged and
still describe the live method.

## The question

The GM's framing: a Mode B map is currently made by hand - a session writes a `.gen.py` choosing the
canvas, the sluice, the cluster center, the lane polylines, the pond rectangle, the woodland patches
and the windbreak belt as literal coordinates, then iterates against `check_village/` until the
gate goes green. It works. It is slow. *"It might be faster to create a scripted process."*

The instruction was to try it on the simplest tier - a rice hamlet, with `pool/hamlets/ikegami` as
the reference subject - and to build something with **tunable knobs** rather than one map's worth of
special cases, on the understanding that unusual places (the GM's example: a hamlet on red clay)
would still be generated normally and then modified by hand.

## What exists now

- **[`hamletgen/`](l7r/diagram/hamletgen/)** - the generator. An eleven-stage pipeline (`STAGES`), each stage
  a function of `(settlement, plan)`, run in the order the engine's DRAW ORDER map requires: the
  water frame, the field, the sink, the ways, the homesteads, their appurtenances, the notice board,
  the hinterland, the woodland, the windbreak, the crossings, the frame.
- **[`tests/hamletgen/`](tests/hamletgen/)** - unit tests for the derivations and the failure modes.
- **[`pool/hamlets/`](pool/hamlets/)** - four generated maps living beside the hand-authored hamlets
  (`meta.generated_by` marks a scripted map), each a nine-line `.gen.py`:
  **Inashiro** (the head-to-head with Ikegami), **Sawada**, **Mizuguchi**, **Kashikawa**. They are
  regenerated and gated by `tests/test_villages.py` like every other pool map.

A whole hamlet is this much source:

```python
generate(HamletSpec(name="Inashiro", seed=4, households=15, down_deg=90, water_sink="pond"),
         out_base=os.path.join(HERE, "inashiro"))
```

Everything else - the canvas, the intake, the field's size and shape, the cluster's margin, the lane
skeleton, the connector's bearing, the pond's set-back, the woodland patches, the windbreak's
footprint, the wells - is derived from geometry already on the map, or rolled from the seed.

## It builds on the knob engine; it does not replace it

`Settlement.roll_village` (feature 005) already rolls a gate-passing hamlet from a seed, and
`pool/hamlets/honda` and `shimizu` are the shipped proof. **That work is the foundation of this
one.** What this module adds is the gap between what `roll_village` produces and what an authored
map like Ikegami contains:

| | Ikegami (authored) | `roll_village` | `hamletgen` |
|---|---|---|---|
| drainage tameike at the low foot | yes | source pond only | derived from the drain outfall |
| connector track running off-map | yes | none | derived, steered clear of crops |
| managed-woodland patches | yes, hand-placed | none | found by an open-ground scan |
| draft byres | yes | none | yes |
| field sized to household count | a hand-tuned `field_fall` | a hand-passed `field_fall` | SOLVED to a real acreage |
| cluster siting | hand-picked center | a lateral margin band | the 背山面水 margin, drain- and hem-aware |

## The evidence

**A cohort of twenty hamlets from consecutive seeds, none of them looked at, all put through the
full `check_village/` gate.** That is the test that matters: one good map proves a person can
drive the script to a good map; a correct cohort proves the script is doing the work.

    python3 -m l7r.diagram.hamletgen --batch 20

Household counts land exactly on the declared figure on essentially every map, and the paddy
acreage lands on the target the household count implies - the four demo maps come out at 19.4
against 19.5, 26.0 against 26.0, 15.7 against 15.6 and 24.7 against 24.7 acres.

**36 of 36: 24 of 24 on seeds 1-24, and 12 of 12 on a HELD-OUT cohort (seeds 101-112)**, measured
2026-08-12. It was 7 of 12 when the experiment was first reported.

**THE TWO COHORTS, since the numbers below are quoted in their terms.** A *cohort* is N hamlets
rolled from consecutive seeds and put through the whole gate. There are two, and the split is the
point: the **FITTED** cohort (seeds 1-24) is the set every fix was developed against, so its pass
rate is measured on the very maps the code was tuned to; the **HELD-OUT** cohort (seeds 101-112) is
never debugged against and only ever run to measure. The terms are borrowed from statistics -
training set and test set - and the held-out one has earned its keep three times, catching the belt
derivation, the connector routing and the cluster siting after each had passed all 24 fitted seeds.

Both cohorts matter and the held-out one is the honest measure - seeds 1-24 are the set the fixes
were made against, and a rate measured on the seeds you debugged is a fitted number. The held-out
dozen earned its keep: three of its failures were general bugs the tuning set never showed (a
clamped pond put back on the crop it had just cleared, a cluster band seated off the canvas edge
which built 7 farmhouses of 18, and a carried-way deck under-sized where the water bends). Run
`tools/cohort_audit.py --count 12 --seed <anything>` for a fresh set whenever the rate needs
re-measuring; that number is worth more than this paragraph. `tests/hamletgen/` pins 4 of 4 as a
ratchet.

Every map seats its declared households exactly, lands its acreage on the figure the household count
implies, and clears all ~185 gate checks.

## The boundary case that cost the most, and what fixed it

A fan can put its collector's outfall exactly ON the field outline - inside by the geometry, outside
by the rounding. `streams_avoid_fields` exempts a drain brook's anchored leg by trimming leading
vertices STRICTLY INSIDE the outline, so such a brook is measured from its own anchor point, and
then no route out of it can pass: the collector runs ALONG the boundary there, so every bearing
within `drainage_junction_smooth`'s 65 degrees of it clips the crop and every bearing that clears
the crop is a hairpin. Measured: the clear bearings began 73 degrees off the drain's heading.

Four routing-side attempts failed before the answer turned out to be one line in the CHECK: an
outfall on the boundary is just as anchored as one inside it, so the trim now tolerates 2 px. The
rule the check exists for - a stream RE-ENTERING or cutting across the crop - is untouched, and the
whole pool, the check tests and the 695-manifest regression corpus stayed green.

The lesson is the one this feature kept teaching: when a placer and a check disagree, the bug is as
likely to be in the check's tolerance as in the placer's geometry - and a routing search that cannot
win is worth suspecting before its twentieth variation.

## Raising the rate (2026-08-11)

The GM's follow-up was the two items above: fix the engine defects on their own, and take the
cohort to 100%. What the second one taught is worth as much as the number.

**Nine of the eleven fixes were one of three shapes**, and none of them was "tune a constant":

- **A test that measured the wrong thing.** `crosses_poly` took a fixed 60 samples whatever the
  segment measured, so a 4,000 px connector was sampled every 67 px and stepped clean over a field.
  A way was routed by the straight CHORD to its endpoint and then drawn as a polyline bowing 40 px
  either side of it. A probe must measure what will be drawn, at a resolution finer than the thing
  it is testing.
- **A test that could never pass, which looks exactly like one that always does.** The drain
  brook's bearing sweep tested the leg starting at the drain OUTFALL - inside the field by
  definition - so every bearing was rejected and the sweep fell through to an untested fallback.
  The fan disqualifier had the identical shape earlier. Assert that a filter accepts something.
- **A feature sized off an aggregate that an outlier could stretch.** The windbreak and the copse
  were sized off the MAXIMUM extent of the house cloud, so one strewn farmstead turned the belt into
  a 2,392 px green blanket. Percentiles were tried and are the wrong cure: bounding the SEATS to the
  cluster band removed the outliers at source, and the percentiles then only made the belt too small
  to shelter anything.

**And the second-order effects are the reason a cohort beats a map.** The green blanket did not fail
as "your windbreak is too big" - it failed as `title_clear_of_features`, because with the head of
the sheet under trees there was no blank ground left for the map's own name. Three checks away from
its cause. A single map would have been fixed at the symptom.

## What the experiment found in the EXISTING engine

Six things, found by building on shipped code rather than by auditing it. **Five are fixed**
(2026-08-11 and 2026-08-12, at the GM's direction, each with the full pool sweep); the sixth is
half-fixed at the engine, and its remaining half is now a measured, scoped pool job rather than a
vague debt.

1. **FIXED. `draw_comb_field` never registered its dry hem in `s.dry_polys`.** It appended to `block_polys`
   only. `dry_polys` is the registry the GROVE, LANE and threshing-yard filters read, so a map built
   through `draw_comb_field` has hem plots that stop a house but not a tree. Every hand-authored
   comb gen in the pool compensates with its own `s.dry_polys.append(...)` line; the two seed-rolled
   maps (Honda, Shimizu) do not, and pass only because their clusters happen to sit away from the
   hem. This is exactly the shape the skill's dev notes call out - placement and its check reading
   different sources. The engine registers it in both now, with a ratchet in `tests/settlement/`.
2. **HALF FIXED, and the other half is now measured. A way's no-build corridor was sized against
   the house the placer TESTS, not the one it DRAWS.** `_near_corridor` measures a candidate's
   CENTRE against the corridor, and the placer passed the 46x28 ft base rect while wealth variation
   renders up to ~1.33x that - so at the authored clearance of 32 a well-off farmhouse's drawn
   corner ended 2.4 px from a track's centerline while its centre stood a legal 34 px off.
   - **Fixed at `_fits`:** a lane now registers its DRAWN TREAD beside its soft corridor, and
     `_fits` tests the candidate's whole footprint against it, with the same 2 px hair
     `houses_clear_of_lanes` allows and the same `skip` semantics `_near_corridor` uses (a frontage
     row is excused from the way it fronts - matched by geometry, not identity, which is the
     footgun that once cost the pool two thirds of its commercial frontage). Ratcheted in
     `tests/settlement/`, and **no pool manifest moved a byte**.
   - **The registry is deliberately lanes-only.** Street, alley, road, ring road and towpath were
     wired up and reverted the same day: each already inflates its corridor by a half-diagonal's
     worth of margin to cover this by hand, so the tread changes no verdict they were getting
     wrong, and the extra tightening cost Tango a public well - straight into the documented
     well-versus-collision-circle squeeze.
   - **Still open, and now precisely characterized:** a homestead BUNDLE never goes through `_fits`
     at all. It is seated by its own geometry (`_bundle_fits`), and the house inside it is offset
     from the seed point AND scaled by the wealth/length jitter, so the rect the placer clears is
     neither the size nor the position of the rect the map draws. Instrumenting one failing seed
     showed `_fits` was never called at the offending house's position with its own w/h. Testing
     the drawn house rect inside `_bundle_fits` DOES fix it - and re-rolls Ikegami, Kuwabata,
     Tanada and Hoshigaoka, breaking Hoshigaoka's gate. That is a reviewed pool job, one
     `settlement-review` per map, and it is the natural companion to replacing the collision circle.
     `hamletgen` therefore keeps `LANE_CLEARANCE = 48` - with the reason now stated correctly at
     the constant, which it was not before.
   - **DONE 2026-08-17 (feature 121), and the paragraph above is wrong twice.** (a) The divergence
     is the RAKE, not offset or scale: the bundle's house rect matches the drawn record's position
     and size to 0.0000 px, and `_house_rot`'s +/-5 deg is worth 2.56 px of corner bulge. (b) The
     four maps it was blocked on all froze on 2026-08-16 and are never regenerated, so the cost it
     quotes had already evaporated. Two further defects turned up during the fix: `_on_a_tread` was
     passing `rot=0.0` unconditionally, and `houses_clear_of_lanes` built its own axis-aligned
     corners beside the rake-aware `rect_corners` - the gate had the same blindness as the placer.
     `LANE_CLEARANCE` is now derived at **40**, and correctness lives in the tread test rather than
     in the corridor's width. Full record: `specs/121-placer-drawn-footprint/research.md` D1, D6, D7.
3. **FIXED. The pool sweep could not SEE these maps, and said nothing.** `test_villages._is_village_gen`
   decides what to regenerate and gate by looking for the string `settlement import` in a gen's
   source. These gens import `hamletgen`, so four maps sat in the pool being regenerated by nobody
   and gated by nothing, with the whole sweep green - "a check that never runs looks exactly like a
   check that passes", applied to the entire sweep. FIXED: the discriminator now takes a list of
   Mode B engine modules, and `test_every_pool_gen_is_swept_or_declared_a_compound` fails by name if
   a pool gen is matched by neither the sweep nor the declared Mode A compound list.
4. **FIXED. `roll_village` sized its cluster band at 56 ft per household**, which is the FARMHOUSE -
   but the to-scale tiers place a BUNDLE (house plus threshing yard plus dooryard garden, ~71 x 57
   ft) and `_fits` then spaces bundles by circumscribed circles, so the honest pitch is ~92 ft. The
   symptom is not a shortfall, which is what hid it: the caller keeps seeding until the quota is
   met, so the count comes out right and the cluster ends up packed solid, and the map fails
   `settlement_has_wells` because `open_seat` can find nowhere in it to put one. Correcting it
   exposed two more things sized off the band rather than off the map - the communal windbreak,
   which stood where the cluster was ASKED to be rather than where it landed, and the rolled well
   grid, laid over the house bbox GROWN by 10 px so a well seated just outside the settlement
   dragged the frame after it. Both read the placed houses now.
5. **FIXED. A plank footbridge slid clear of houses and unwalkable banks, but not of three other
   things**: the dry HEM (a board lying on the barley), ANOTHER DECK (two planks drawn on top of
   each other where two ditches run close), and a CONFLUENCE (the deck is sized from this ditch's
   nominal width, so where another course joins, the water is wider than the deck and the abutment
   stands in it).
6. **FIXED. `build_comb`'s `grain` documentation and the pool's calibration disagreed.** Its
   docstring prescribes `2 / ftpx`, so a "too narrow to plant" threshold means the same real size at
   every scale - 2.0 for a 1 ft/px hamlet - while every authored hamlet passes the default 1.0,
   which at this scale halves both the thresholds and the ditch widths. Two things blocked the
   principled value and both are now fixed: `channel_footbridges` and `bridges()` sized their decks
   from a nominal width rather than the water actually beneath them, so wider ditches got planks
   whose abutments stood in the channel; and the windbreak belt was derived from the house cloud's
   EXTREMES, which at the coarser grain could put the belt off a tall narrow cluster entirely.
   `hamletgen` now runs at the principled 2.0. The POOL's hand-authored hamlets stay at 1.0 until
   someone re-rolls them - visible change, one `settlement-review` per map - and `build_comb`'s
   docstring now carries that account rather than the bare mismatch, so a gen passing 1.0 is doing
   so knowingly.

## The independent review, and what it changed

`settlement-review` was run on Inashiro against Ikegami (Constitution Principle I - the author is
not a reliable reviewer of their own visual output). It found **four errors on a map with a green
gate**, and every one of them was a real defect that no check could see. All four are fixed:

1. **The windbreak belt was 91% outside the drawn frame** - 125 of 137 clumps above the top edge, so
   what the sheet showed was a row of crowns sliced flat. A belt that is a correct belt and not on
   the map.
2. **Three of four woodland patches were off the frame, in a straight row along the canvas margin at
   identical height.** Cause: the patch scoring MAXIMIZED distance from the crop, which drives every
   candidate to the far canvas edge where the crop then discards it. A hamlet's coppice is walked to
   daily; the scoring now prefers the nearest qualifying ground on the settlement's own back slope.
3. **The lane skeleton did not organize the settlement** - median house-to-lane 94 ft against
   Ikegami's 55, with a lane dead-ending in open ground. Houses are now offered seats along both
   verges of every internal lane before the shape fill, so they front the lanes they are on.
4. **The field outline was a byte-for-byte translation of Ikegami's**, vertex for vertex, because
   the reference fan lengths ARE Ikegami's and the size multiplier came out at 1.0. A cohort whose
   maps share their largest object is a cohort of re-skins, so the fan's ASPECT is now rolled too -
   trading fall length against canal length leaves the area alone and changes the silhouette.

Two of its measurements are worth keeping as the honest scoreboard: the bare comb floor is **8.4% of
the field envelope against Ikegami's 7.7%** (i.e. inherited, not caused here, exactly as the notes
claimed), and the acreage win verified independently - **18.3 acres drawn against a computed 19.5
target, where Ikegami draws 15.4 against a stated ~20**.

It also raised two things left OPEN, both recorded rather than fixed:

- **Dry hem plots are ~3.5x Ikegami's** (median ~6,100 sq ft against 1,770), chained single-file
  rather than packed two or three deep, so the hem reads as somebody else's fields rather than as
  household strips of barley and millet. Total acreage is comparable - this is a PARCEL-SIZE choice.
  It wants a researched constant of its own, the way `GROSS_ACRES_PER_HOUSEHOLD` has one.
- **The lane stand-off is a symptom of the engine debt.** `LANE_CLEARANCE` is 48 px here against the
  authored maps' 32, purely to work around "placement tests a different footprint than the one
  drawn". Fixing that debt in the engine would let the clearance drop and the frontage tighten.

**A second pass (2026-08-12)** reviewed the same map after the grain moved to 2.0 and the belt was
re-derived. It confirmed both changes on the render - the doubled ditches still read as ditches
(main 12.4 -> 3.2 ft against Ikegami's 6.2 -> 1.6, all under a farmhouse's short wall), the plot
fabric did not open up (21.3% of the envelope more than 10 ft from a bund, against Ikegami's 18.0%),
the planks still land dry, and the belt now genuinely follows the cluster's fringe through a 130 ft
jog instead of ignoring it. It found two things:

- **The lane skeleton serves only the middle of the settlement**, and this is the sharpest open
  weakness the experiment has. House-to-nearest-way on Inashiro: median 80 ft against Ikegami's 55,
  and the worst four at 218, 267, 308 and 330 ft against Ikegami's worst of 125 - eight of fifteen
  farmsteads with no lane at all. The cause is an ordering one and is not fixed by lengthening the
  arms (tried: the skeleton is already clipped by the crop long before it runs out of layout). Lanes
  must be laid BEFORE the houses so the houses pack around them, so the skeleton is sized from the
  cluster band the seat asked for - while the front row is deliberately offered `lat * 1.6` of the
  field outline and the fill spills further still. The honest fix is a second pass that adds lane
  after the homesteads land, serving whatever the fill actually produced; that is real work and it
  is listed under "If this is continued".
- **A flank-seated cluster makes its declared wind circular.** `stage_ways` re-reads the windward
  quarter off the site's own back when the seat and the rolled wind disagree by more than ~70 deg,
  which is right - but it means that on a map like Inashiro the belt is west because the cluster's
  back is west, and the wind was named to match. Recorded in the map's own notes, where the claim
  that the wind comes off the slope was stated without that qualification.

## Where it is weaker than a person

Recorded honestly, because these are the things that decide whether to adopt it:

- **The wind is derived from the slope**, not from the region. Cold air drains downhill, so the
  local cold wind comes off the high ground - which is real, and it is what makes "back to the hill"
  and "back to the wind" one fact. But it means the map declares an exposure implied by its own
  layout rather than a fact about the province. A GM who knows the real prevailing wind should pin
  it on the spec.
- **No sense of PLACE.** The script produces a correct hamlet; it does not produce Ikegami, which is
  named for its relationship to its pond. Naming, the one distinguishing feature, the reason this
  hamlet is worth a map - all still a person's job.
- **It cannot do the unusual.** By design (the GM's red-clay example): generate the ordinary case,
  then modify by hand.
- **Inherited artifacts remain.** The bare paddy-green "floor" on a comb fan's shoulders, where the
  carve does not tessellate into plots, comes from `build_comb` and shows on the authored maps too.

## How the checks are used, which was one of the GM's open questions

Per ROUND, on the finished map - not per placement. The reason is structural: the placer already
refuses an overlapping seat, so the overlap checks are a formality that should never fire, and
running the gate per house would cost a full gate run to re-prove what placement guarantees. What
the gate actually catches is EMERGENT - acreage against household count, a marsh that ended up
uphill, a windbreak on the lee side, a connector that stopped short of the frame - and those are
properties of a finished map.

Where a stage can fail locally and recover, it retries **inside the stage against the placer's own
verdict**, which is both cheaper and more precise than a gate run: the cluster widens its band and
draws more candidates when houses are refused; the pond walks downslope until its rim clears; the
wells relax their neighborhood test and then ask `open_seat`.

**The gate earned its keep.** Every one of the design decisions above was forced by a real failure
across the cohort, not by taste. The full list of what the cohort caught, in order: a fan starved of
acreage by an intake at mid-slope; a pond laid over the crop; a manifest gated before `finish()`
flushed it; a connector bridging a drainage ditch at an oblique angle; a woodland patch holding the
map's frame open; a windbreak standing in the barley; a cluster seated INSIDE a concave field
margin; a supply canal's tail dying in bare ground; a well out in the fields; a brook turning
through an acute hairpin. A person authoring one map meets perhaps two of those.

## The sun corridor, and the migration it starts (2026-08-13)

The GM asked whether a threshing yard would sit directly north of a neighbour's farmhouse, or
whether that house's shadow would take its light. It would: thatch is pitched 45 degrees or steeper,
so a 46 x 28 ft minka's ridge stands ~20 ft up, and at 38N in the threshing month that is 21 ft of
shadow at noon and 39 ft by 9am. The full derivation and sources are in
[`research/homesteads.md`](research/homesteads.md), "The threshing yard's sun".

**Every hand-authored nucleated map in the pool breaks it** - Ueda 45 of 85 yards shaded at noon,
Hoshigaoka 31 of 70, Ubame 21 of 36, the hamlets 3-10 each, with neighbours' walls commonly 2-8 ft
off a yard's edge. The GM's decision was NOT to re-pack them by hand: the rule binds the SCRIPTED
path, and each legacy map inherits it when it is converted. `hamletgen` calls `s.sun_corridor(39)`;
`yards_unshaded_by_neighbors` is gated on `meta.generated_by`, which only a generator sets. **This is
the first rule the scripted tier holds ahead of the pool, and the pattern is written up in the
skill's [`CLAUDE.md`](CLAUDE.md)** under "MIGRATION: new rules land in the SCRIPTED path first".

**Result on the scripted maps: 0 shaded yards, from 3-6 each before, with every household still
seated.** Two implementation notes worth keeping:

- The placer must read the neighbours' yards off the PLACED BUNDLES' `geom`, not off
  `M["threshing_yards"]` - yards are not drawn until `farmsteads()` flushes, long after the last
  house is seated, so the manifest list is empty while placement runs and the first version cleared
  only about half the shadows.
- The placer runs 2 ft stricter than the check on BOTH axes. It measures the bundle rects it is
  about to commit; the check measures the yard record finally drawn, and they differ by fractions of
  a pixel - seats at 39.0 ft and at 0.35 px of lateral overlap passed one and failed the other on
  cohort maps.

**THE RESIDUE IS CLOSED: 24/24 fitted and 12/12 held out** (GM: "the point of a deterministic
scripted process is consistency"). Landing the sun corridor cost three fitted seeds and then a
held-out one, and every cure was a different lesson:

- **Seeds 11 and 18 were the same bug, and it was the PITCH.** `BUNDLE_PITCH` was 92 ft, calibrated
  before the corridor existed; a row now needs house (28) + yard (~26) + 39 ft of sun + gaps, about
  100. Asking the band for less than a row needs does not tighten the cluster - it spills the
  overflow OUTSIDE the band, which is how seed 18 grew a two-farm satellite 500 px off the nucleus
  (777 px from water against a 760 px reach, every legal well seat around it taken by its own two
  courtyards) and seed 11 lapped a garden onto a neighbour. Raising the pitch to 100 fixed both at
  once. Chasing either symptom - the well, the garden - would have fixed neither.
- **Seed 8 was a knife edge, and a margin was the WRONG cure.** A plank's bank sample sat 54.97 px
  from the nearest house at placement and 55.02 at the check, against a 55 px village reach: the
  0.05 px is `bridge()` rounding the deck's recorded POSITION. Widening placement's sample by 2 px
  was tried first and made it worse - sampling further is not strictly stricter, because past a
  strip of scrub the sample lands back INSIDE the field, so the wider test passed the very plank the
  check rejects. The cure is to test the exact rounded values the manifest will carry, which makes
  the two sides bit-identical. A margin papers over a knife edge; identical inputs remove it.
- **Seed 103 (held out) was a feature the FRAME could not see.** Its notice board sat 87 px north of
  the northernmost farmhouse on a lane arm serving nobody, and `crop_to_content` ignores linear
  runners, so board and caption fell off the sheet. Adding `kosatsuba` to the crop's hard set was
  tried and is worse - it then holds the frame open by itself, which
  `crop_not_held_open_by_one_feature` exists to stop. The board is re-seated on the nearest verge
  inside the house cloud instead. Popping the board's record left its CAPTION behind, which kept the
  check red after the board had moved: a feature and its deferred caption are removed together.

## A SECOND FIELD ARCHETYPE: the polder (2026-08-13, in progress)

The GM asked for the scripted process to support other hamlet TYPES, naming Kuwabata. The pool's
hamlets span five field archetypes and this generator drew one:

| hamlet | archetype |
|---|---|
| Ikegami, Moritono, Honda, Shimizu | valley comb fan (what the script made) |
| Enokida | `polder_grid` |
| **Kuwabata** | `mulberry_dike_fishpond` |
| Tanada | `contour_terraces` |
| Yatsuda | `ribbon_valley` |

**Kuwabata decomposes into two pieces**, which is what makes it a good target: it is polder geometry
carried to the 桑基魚塘 end state - the `mulberry_fishpond` overlay at `eligible="all"`. Its own notes
insist that end state is the deliberate EXCEPTION and the scattered overlay the norm, so the overlay
belongs in this generator as a KNOB, not as a map type. The substrate is the prerequisite either
way, so the polder went first.

**Where it stands: the polder DRAWS and is down to two named failures.** `field_archetype` is a spec
knob (`valley_paddy` | `polder_grid`), pinnable and validated; a rolled 16-household polder lands
**20.7 acres against a 20.8 target and seats 16 of 16 households**. Four things had to be derived
rather than copied from Enokida, and each was the same lesson the valley path taught:

- **The block's ORIGIN is derived from the fall**, not pinned to a corner. `build_polder` grows its
  grid from the high corner along the fall, so Enokida's north-west corner only works at
  `down_deg=90`; at 0 the same corner threw the block off the top of the canvas - bunds at y=-124,
  the drain outfall at y=-407, water visibly running backwards. Centring the block and stepping back
  half its extent along each axis works at any bearing, recomputed per bisection candidate.
- **The header reservoir is seated at the dike's own inlet sluice.** Two earlier tries measured only
  in the fall frame: one blended the high corner with the centroid and put the reservoir inside the
  crop, the next centred it across the block's head and left the inlet channel dangling short of the
  envelope. `build_polder` says where the dike is cut for water; the pond is what that sluice draws
  from, so the sluice is the anchor both ends agree on.
- **The dike is gapped wherever a channel actually crosses it**, not only at the two sluices the net
  names - anywhere else the earthwork is drawn straight over running water.
- **The lane arms clip against marsh already drawn.** On a polder the reservoir's reed fringe is laid
  before the ways, and an arm ran through it.

**BOTH OF THOSE ARE NOW FIXED**, and one of them was an engine omission rather than anything this
generator did:

- **`paddy_bunds_clear_the_collector` was `build_polder` never calling `hem_to_bank`.** That pass
  lifts a parcel vertex out of the collector's stroke, and its own docstring names POLDER as one of
  the three engines that need it - *"the collector IS the polder's bottom side, so the parcels front
  it directly and float error alone put a vertex a half-pixel past"* - but the call existed only in
  the comb, the terraces and the ribbon. It bit on 2 of 12 grid shapes. Fixed at the engine, and
  **Enokida and Kuwabata are byte-identical**, because the pass only lifts vertices that breach.
  One trap on the way: the first version passed the TERRACES' 1.5 -> 5.0 width taper, copied from
  the call above it, while this drain is 5.0 throughout - so it under-lifted along most of its run
  and the bunds it was added to clear stayed in the stroke. A lift has to measure against the widths
  the ditch is actually drawn at.
- **`watercourse_ends_reach_water` was the reservoir's seat.** `build_polder` puts its sluice on the
  dike line, up to 70 px from the perimeter feeder's own head, and the feeder's head sits just
  outside the planted extent - so the ring's head dangled with the inlet water stopping short of it.
  The pond now sits on the far side of that head, along the head-to-sluice line, so the inlet channel
  runs straight THROUGH the head on its way in: the ring is charged where it begins. Snapping the
  sluice onto the head instead was tried and is worse - it drags the mouth across the grid and puts
  a farmstead on it.

**Also fixed while sweeping bearings the first pass never tried:** the dike's own caption could land
outside the frame (`labels_within_image` at down_deg=270), because `perimeter_dike` captions itself 8
px above its band and a dike is not in the crop's hard set. Adding `dikes` to that set was tried
twice - once alone (no effect at all, because `_crop_boxes` reads `poly` and a dike records
`outline`, so the extractor could not see it - the same blindness the OVERLAP extractor had) and once
with the extractor taught to read `outline` (the band then holds the frame open past the content and
every bearing fails `crop_hugs_content`, and both pool polders move). The scripted tier draws its
dike **unlabelled** instead: a perimeter dike is the most legible thing on a polder sheet and does
not need naming.

**WHERE IT STANDS: 11 of 12 cardinal-bearing polders pass** (was 4). Four fixes, and the first was
the one the previous pass could not find:

- **The inlet's field end is CONSTRUCTED, not clipped** - which is why moving the sluice never
  helped. `draw_comb_field` builds it as `net["channels"][0]["pts"][-1]` stepped **70 px straight
  downhill**. That is a COMB's geometry: a head-race ends at the field's head, so downhill runs into
  the crop. A polder's "main" is the ring canal running ALONG the high edge, so its last point is a
  corner and the same step skims the boundary - the mouth landed 2.6 px inside where the rule wants
  10. It now checks the envelope and, only if that step does not land well inside, pulls the end in
  on the nearest edge's inward normal. **Every comb map is byte-identical**, because their downhill
  step was already clear. This killed BOTH `channel_field_anchored` and
  `watercourse_ends_reach_water` on all twelve.
- **A polder has no field spur.** The valley hamlet's spur runs from the cluster to the paddy's
  edge; a polder is ringed by its dike and, inside that, the ring canal, so the way in is over the
  dike at its sluice gaps. Drawn anyway it was worse than pointless: every near target crosses the
  ring canal, so the least-bad candidate ran from the cluster straight ACROSS the block to a vertex
  on the far side (`fields_clear_of_road`, 4 of 12).
- **Lane arms are clipped against the WET field, not only the dry plots.** `crop_polys` returns
  `dry_plots`; the connector always listed the envelope and the arms never did. Invisible on a
  valley map, where the arms point away from the fan.
- **The polder's out-of-crop ditch runs are no-build corridors**, the loop the valley path already
  had and that was never carried across - a polder's ring canal hugs the envelope edge and its outer
  stretches lie on the open margin where the village stands.

**THE LAST ONE IS GONE TOO, and it was two lists rather than one.** The byre sat on a water line
that my corridor loop never reserved, for two compounding reasons: the loop tested each segment's
MIDPOINT (so a segment straddling the envelope, half of it out on the margin where the village
stands, reserved nothing), and it iterated `field_ditches` only - while the line the byre sat on was
in `M["channels"]`, the inlet link and topology hairline `draw_comb_field` records. Reserving a
segment unless BOTH ends are inside, over both lists, closed it. **12 of 12 cardinal polders**, and
then **48 of 48** over 8 seeds x 4 bearings plus the household band's ends.

**Then the cohort said no, and it was right.** `polder_grid` was promoted into `ROLLED_ARCHETYPES`
(with polder falls constrained to the four cardinals - a wei-tian polder is a SURVEYED orthogonal
module laid to the survey grid, which is what the archetype IS, not a workaround for
`polder_fills_its_bbox`). The fitted cohort fell to **19 of 24**. `cohort_audit` varies HOUSEHOLDS
per seed and rolls water_sink, cluster_shape and lane_skeleton; the 48-map sweep pinned households
at 16 and took the defaults. A fixed-parameter sweep is not evidence of consistency - the same
lesson the held-out cohort taught the valley tier three times, now taught by the fitted one.

So `polder_grid` is **demoted back to opt-in** and the bar for promotion is a green COHORT, not a
green sweep. The valley tier is 24/24 and 12/12 again.

**WHERE THE POLDER ACTUALLY STANDS (2026-08-15, end of the session's work):**

| measure | state |
|---|---|
| valley tier (the shipped one) | **24/24 fitted, 12/12 held out** - untouched throughout |
| hand-authored pool | **byte-identical**, verified after every engine change |
| polder, cohort-style households, 8 seeds x 4 cardinal falls | **29 of 32** |
| polder, in the ROLL | **not promoted** - opt-in via `field_archetype="polder_grid"` |

**Fixed in this stretch, all with the pool unmoved:**

- `watercourse_ends_reach_water` - the inlet channel now meets the ring canal's head. The end is
  CONSTRUCTED (`fork` stepped 70 px downhill), not clipped, and the 20 px bow that
  `channel_winds_gently` requires pushed the drawn line ~17.6 px off the head against a 12 px touch
  tolerance. The head is inserted as a vertex when the run misses it, under an explicit
  `join_head=True` flag that only the polder passes. **Three attempts to condition it on the
  check's own clauses each missed one** - distance alone moved Ubame and four others, "outside the
  envelope" moved Honda and Shimizu, and replicating the vis_bbox/edge/junction trio still moved
  them, because the check reads crop bounds and per-field bboxes that do not exist at draw time.
  Replicating a check inside the code it governs is the trap the skill's notes name repeatedly; the
  flag cannot drift.
- `polder_fills_its_bbox` - `edge_wander` is fitted to the block instead of fixed at Enokida's 0.5.
  The wobble is a fixed size in cells, so on a small grid it eats a much larger share of the bbox
  (measured: a 9x5 fills 79% where the rule wants 82%, while Enokida's 15x8 clears it). The wander
  walks down 0.5 -> 0.12 until the block reads as surveyed.
- Earlier the same day: the byre-on-the-water (a corridor loop testing segment MIDPOINTS and
  iterating one water list of two), and `build_polder`'s ring closing on a 75-degree stub.

**WHAT IS STILL BROKEN: 3 of 32, all `title_clear_of_features`, all on one seed** (seed 8 at 11
households, three of four falls). The map's title lands on the WINDBREAK BELT. `stage_woodland`
reserves blank ground for the name (`title_pocket`) and keeps the woods out of it, but the belt is
drawn later by `village_grove`, which takes only a polygon and honours no keep-out list - so on a
tightly framed map the belt covers the reservation and `title()` has nowhere clear to sit. The fix
in progress was to dent the belt's vertices out of the pocket; it was not applied. A cleaner
alternative worth considering first: give `village_grove` a keep-out list, since this is the second
feature (after the woodland patches) that needs to stay off reserved ground.

**NOT diagnosed:** whether the same title collision appears on valley maps at unusual framings - it
has not, in 36 cohort maps, but the belt/pocket conflict is not polder-specific in principle.

Diagonal bearings additionally fail `polder_fills_its_bbox`, which is a fair statement about the
archetype - a wei-tian polder is a SURVEYED orthogonal block and a diagonal one does not fill its own
bbox - so the tier should roll polders on cardinal falls only when it does start rolling them.

**The roll is deliberately still valley-only** (`ROLLED_ARCHETYPES`). A rolled archetype with known
failures would mix them into the valley tier's 36/36 and destroy the one number that says the
scripted process is consistent. Moving `polder_grid` into that tuple, once its own cohort is green,
is the whole ceremony.

## If this is continued

In rough order of value:

0. ~~**Raise the cohort pass rate to 100%**~~ - WORKED ON 2026-08-11, see "Raising the rate" below.
1. ~~**Fix the engine defects above**~~ - DONE 2026-08-11 (four), 2026-08-12 (the grain, and the
   lane half of the footprint debt); see the section above.
2. **Make the placer test the footprint it DRAWS, and retire the collision circle** - the one piece
   of engine work this experiment left on the table, and the skill's dev notes were already asking
   for it before the experiment started. Do both halves in ONE pool re-roll: the drawn house rect
   inside `_bundle_fits`, and the circumscribed circles replaced by a real `sat_overlap` on rotated
   corner quads. Four hamlets and a village re-roll for the first; the second moved Tango +21
   houses, +20 buildings and +23 wells in a trial. Budget a `settlement-review` per affected map.
3. **A second lane pass, after the homesteads land.** The one place the scripted maps are clearly
   behind the hand-authored ones (median house-to-way 80 ft against Ikegami's 55, worst 330 against
   125). The skeleton has to be laid before the houses so they pack around it, so it is sized from
   an estimate; nothing currently goes back and serves the cluster that actually formed.
4. **Extend to the village tier** - the same pipeline plus a headman, a shrine with its torii count,
   a burial ground and tax-free plots. Most of the machinery already exists in `roll_village`.
5. **Merge, rather than keep two paths.** If this is adopted, `hamletgen`'s derivations belong
   inside `roll_village` so there is one scripted path, not two.
6. **A `--seeds` sweep that reports the failure HISTOGRAM across a hundred maps**, so a rule change
   is scored against the cohort rather than one map.

## Three lessons that outlived their bugs

Worth carrying to any future generator work, whatever happens to this one:

- **A probe must measure the thing that will be DRAWN.** The connector track was routed by testing
  the straight chord to its endpoint and then drawn as a wandering polyline bowing ~40 px either
  side of it - so a track whose chord cleared the crop was drawn straight through it. Three checks
  failed on five maps for that one reason. The skill's dev notes already state this rule for label
  probes; it applies to routing identically.
- **A fallback that ignores the constraints is worse than no fallback.** When no bearing was clear,
  the connector fell back to a fixed ray away from the field, which consulted nothing - so exactly
  on the maps where routing was hard, the track was drawn through everything. Scoring every
  candidate and keeping the LEAST-BAD one means a hard map degrades by one crossing instead of by
  all of them, and the failure is visible rather than disguised.
- **A filter that rejects EVERYTHING decides nothing, and looks identical to one that works.** The
  fan disqualifier asked whether a supply canal ends outside the ground it waters - and tested both
  ends, when a canal's upstream end is the head sluice and is outside the plots by construction. It
  therefore answered "illegal" for every candidate, so the search fell through to picking on acreage
  alone while appearing to enforce a rule, and paid for five aspect searches per map to do it. This
  is the skill's "a check that never runs looks exactly like a check that passes", one step along:
  a check that ALWAYS fires is just as blind, and neither shows up as an error. When you add a
  filter, assert that it accepts something.
- **The number that is wrong is rarely the one that fails.** A cluster band sized at 56 px per
  household instead of ~92 does not fail as a shortfall - the caller keeps seeding until the count
  is met - it fails as a cluster packed so solid that no wellhead can be seated anywhere in it, and
  the gate reports `settlement_has_wells`. When a check fails for a reason that makes no sense,
  suspect a sizing constant upstream of it.
