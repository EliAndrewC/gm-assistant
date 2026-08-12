# EXPERIMENT: scripted hamlet generation

*Started 2026-08-11 at the GM's direction. Status: **proof of concept, not adopted**. Nothing in the
current method has changed.*

**Load this file when:** you are deciding whether to extend, adopt, or abandon the scripted
generation path, or you are about to work on [`hamletgen.py`](hamletgen.py). To DRAW a map today,
ignore this file - [`SKILL.md`](SKILL.md) and [`settlements.md`](settlements.md) are unchanged and
still describe the live method.

## The question

The GM's framing: a Mode B map is currently made by hand - a session writes a `.gen.py` choosing the
canvas, the sluice, the cluster center, the lane polylines, the pond rectangle, the woodland patches
and the windbreak belt as literal coordinates, then iterates against `check_village.py` until the
gate goes green. It works. It is slow. *"It might be faster to create a scripted process."*

The instruction was to try it on the simplest tier - a rice hamlet, with `pool/hamlets/ikegami` as
the reference subject - and to build something with **tunable knobs** rather than one map's worth of
special cases, on the understanding that unusual places (the GM's example: a hamlet on red clay)
would still be generated normally and then modified by hand.

## What exists now

- **[`hamletgen.py`](hamletgen.py)** - the generator. An eleven-stage pipeline (`STAGES`), each stage
  a function of `(settlement, plan)`, run in the order the engine's DRAW ORDER map requires: the
  water frame, the field, the sink, the ways, the homesteads, their appurtenances, the notice board,
  the hinterland, the woodland, the windbreak, the crossings, the frame.
- **[`test_hamletgen.py`](test_hamletgen.py)** - unit tests for the derivations and the failure modes.
- **[`pool/experiments/`](pool/experiments/)** - four generated maps, each a nine-line `.gen.py`:
  **Inashiro** (the head-to-head with Ikegami), **Sawada**, **Mizuguchi**, **Kashikawa**. They are
  regenerated and gated by `test_villages.py` like every other pool map.

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
full `check_village.py` gate.** That is the test that matters: one good map proves a person can
drive the script to a good map; a correct cohort proves the script is doing the work.

    python3 hamletgen.py --batch 20

Household counts land exactly on the declared figure on essentially every map, and the paddy
acreage lands on the target the household count implies - the four demo maps come out at 19.4
against 19.5, 26.0 against 26.0, 15.7 against 15.6 and 24.7 against 24.7 acres.

**The honest number is a pass RATE, and it is 22 of 24** on the first two dozen seeds (measured
2026-08-12, after the collision pass the GM asked for), plus 4 of 4 on the demo maps in
`pool/experiments/`. It was 7 of 12 when the experiment was first reported. Every map in the cohort
seats its declared households exactly and lands its acreage on target; twenty-two then clear all
~185 gate checks.

**The two that do not are worth more than the number**, because each is a specific, named thing:

| check | what it is |
|---|---|
| `field_ringed` | four farmhouses within 165 px of the field outline where five are wanted - the placer refuses a bundle that laps a bund, and on awkward near-ground five standoffs are still not enough |
| `streams_avoid_fields` | the outfall-on-the-outline case, diagnosed in its own section above; the fix belongs in the fan search, not in the routing |

`python3 cohort_audit.py --count 24` reproduces the table, with the gate's own message for each
failure.

**Precision, not just speed.** The clearest single result is the field sizing. Ikegami's own
docstring asks for ~20 acres of paddy for 15 households and its own closing line reports **15.3** -
a 24% miss that nothing catches, because `field_fall` is a pixel length tuned by eye and no check
reads acreage. `fit_field` bisects a size multiplier against the drawn plot area and lands the
target, because `build_comb` is pure and fast and a script can afford to solve what a person has to
estimate.

**Speed.** A hamlet generates and gates in ~11 seconds. The authored equivalent is a session's work.

## The one map that does not pass, and why it is worth knowing

A fan can put its collector's outfall exactly ON the field outline - neither inside nor out, within
rounding - while the crop wraps a lobe around it. `streams_avoid_fields` exempts a drain brook's
anchored leg by trimming leading vertices that are strictly INSIDE the outline, so a brook starting
on the boundary is never trimmed and every route from it reads as crossing the crop. There is no
bearing, junction distance or junction angle that fixes it: the START is the problem, and backing
the start up the drain until it is genuinely inside does not help either, because the collector
itself runs along the lobe.

The honest fix is upstream, in `fit_field`: a fan whose outfall lands on its own outline should be
disqualified the way one with a dangling supply-canal tail already is. That is a change to the fan
SEARCH rather than to the routing, so it re-rolls maps, and it is the obvious next move rather than
another routing patch. Recorded here rather than papered over.

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

Six things, found by building on shipped code rather than by auditing it. **Five are now fixed**
(2026-08-11, at the GM's direction, each with the full pool sweep); the sixth is a
documentation-versus-calibration mismatch recorded rather than resolved.

1. **FIXED. `draw_comb_field` never registered its dry hem in `s.dry_polys`.** It appended to `block_polys`
   only. `dry_polys` is the registry the GROVE, LANE and threshing-yard filters read, so a map built
   through `draw_comb_field` has hem plots that stop a house but not a tree. Every hand-authored
   comb gen in the pool compensates with its own `s.dry_polys.append(...)` line; the two seed-rolled
   maps (Honda, Shimizu) do not, and pass only because their clusters happen to sit away from the
   hem. This is exactly the shape the skill's dev notes call out - placement and its check reading
   different sources. The engine registers it in both now, with a ratchet in `test_settlement.py`.
2. **STILL OPEN. A lane's no-build corridor is sized against the house the placer TESTS, not the one it DRAWS.**
   `_fits` measures the 46x28 ft base rect while wealth variation renders up to ~1.33x that, so at
   the authored clearance of 32 a well-off farmhouse's drawn corner ended 2.4 px from a track's
   centerline while its center stood a legal 34 px off. This is the engine's known "placement tests
   a different footprint than the one drawn" debt; `hamletgen` works around it with a wider
   clearance rather than fixing it.
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
6. **RECORDED, NOT FIXED. `build_comb`'s `grain` documentation and the pool's calibration disagree.** Its docstring says
   a map should pass `2 / ftpx` so a "too narrow to plant" threshold means the same real size at
   every scale - 2.0 for a 1 ft/px hamlet. Every authored hamlet passes the default 1.0. At 2.0 the
   irrigation ditches come out twice as wide as Ikegami's and `channel_footbridges` lays planks too
   short for the water they span, so a plank's abutment stands in the ditch. This module follows the
   POOL (1.0) and says why at `GRAIN`; whichever is right, the two should not disagree silently.

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

## If this is continued

In rough order of value:

0. ~~**Raise the cohort pass rate to 100%**~~ - WORKED ON 2026-08-11, see "Raising the rate" below.
1. ~~**Fix the engine defects above**~~ - DONE 2026-08-11, five of six; see the section above.
2. **Extend to the village tier** - the same pipeline plus a headman, a shrine with its torii count,
   a burial ground and tax-free plots. Most of the machinery already exists in `roll_village`.
3. **Merge, rather than keep two paths.** If this is adopted, `hamletgen`'s derivations belong
   inside `roll_village` so there is one scripted path, not two.
4. **A `--seeds` sweep that reports the failure HISTOGRAM across a hundred maps**, so a rule change
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
