# Phase 0 research: derived lanes, and settlement form as a rolled knob

**Feature**: 126-derived-lanes-and-form
**Date**: 2026-08-23

Five questions had to be answered before any code moved, because this is an ORDERING change and the
documented failure mode is discovering the ordering one gate failure at a time.

---

## R1 - What does `stage_homesteads` actually take from `stage_ways`?

**Method**: read every reference to a lane or to `plan.seat` in `stage_homesteads` and its helpers,
rather than assuming from the stage names.

**Finding: far less than the stage order implies. Three dependencies, and one of them is not a lane
dependency at all.**

| Consumer | Depends on | Verdict once the skeleton moves |
|---|---|---|
| `front_row()` | `plan.envelope` (the FIELD OUTLINE) and `plan.seat` | **No lane dependency.** Already derives from the field, not from a way. Survives untouched. |
| `s.cluster_seeds(...)` (the cloud pass) | `plan.seat`, rolled shape | **No lane dependency.** Survives untouched. |
| `_lane_dist(s, fx, fy) <= _FRONT_ROW_LANE_CAP` | drawn `M["lanes"]` | A *relaxing filter* on front-row seats past the first 5. Loses its subject. |
| `lane_frontage(s, seat)` | drawn `M["lanes"]`, internal only | An entire seat pass along lane verges. Loses its subject. |
| `s.trim_lane_stubs()` | drawn lanes | Runs at the END of the stage, after placement. Unaffected by the move. |

**The decisive one is `plan.seat`, and it is NOT a lane.** `stage_ways` calls `seat_cluster(...)` and
assigns `plan.seat` as a side effect. The seat band - center, along/out axes, lateral and depth
extents - is what `front_row` and the cloud both stand on. So `seat_cluster` must stay BEFORE the
houses. That single fact determines the shape of the split: the pre-house stage does not vanish, it
loses only its internal skeleton.

**Consequence for the two lane-dependent items:**

- `lane_frontage` already documents its own replacement. Its docstring: *"The connector is skipped:
  it is the track OUT of the settlement, and lining it with farmhouses would string the hamlet along
  the road instead of nucleating it (that is the `linear` settlement form, a different archetype)."*
  So the pass is not deleted, it is made form-conditional and pointed at the connector: **skipped for
  nucleated, used against the connector for linear.**
- `_FRONT_ROW_LANE_CAP` exists to pull front-row seats toward tracks that were laid before them. With
  no internal tracks at seat time it has almost nothing to measure against, and keeping it would
  filter the row against the connector alone. **It is retired for nucleated and dispersed** - it was
  compensation for lanes-first, and removing lanes-first removes its reason. This is a RETIREMENT,
  not a re-tuning: `homesteads.py` records two prior dead-end attempts at tuning this cap, and this
  feature must not pull that lever a third time.

**Alternative considered and rejected**: keep the skeleton first and merely improve its sizing so it
reaches the houses. Rejected because it is what feature 123 already tried - the skeleton is sized on
the seat band while the houses spread wider, and seventeen recorded attempts failed to close that
gap. Predicting where houses will go is strictly harder than looking at where they went.

---

## R2 - The DISPERSED form (散村)

**Answer: decisive, and better attested than expected. Implement it.**

The Tonami Plain in Toyama is the canonical Japanese dispersed settlement (*sankyoson*): **over 7,000
farmhouses scattered across roughly 220 km²**, on an alluvial fan built by the Shogawa and Oyabe
rivers. The pattern is over 500 years old.

**The mechanism is irrigation, and it is exactly our terrain.** Farmers built their houses *in the
middle of their own cultivated fields* in order to manage water for those fields directly. The fan's
soils drain well - which is a problem for wet paddy, not a benefit - so water control is per-holding
and constant, and living on your own holding is how you do it. Farmhouses therefore scattered
**naturally**, rather than by design. In the Edo period each farm was granted the land it had
reclaimed, which entrenched the pattern.

**Every house has its own grove.** The homestead woodland is called *kainyo* in the region, and it
shelters the house from winter seasonal winds and snowstorms, and from summer sun.

**Why this matters for us**: our comb field IS an alluvial fan, and our engine already models
per-farmstead shelter groves - `hinterland.py` branches on exactly this, noting that *"a nucleated
settlement shelters behind ONE grove rather than per-house belts"*. So the dispersed form's
distinguishing feature is already implemented as the non-nucleated branch of code we run today. The
form is cheaper to add than its visual distinctiveness suggests.

**Note the correction to our own terminology**: the project has been calling the homestead grove
*yashikirin*. That is a valid general term, but the Tonami regional term for this specific feature is
*kainyo*. Both are real; no renaming is required, but the research record should carry both.

---

## R3 - The LINEAR form (路村 / row village)

**Answer: supportable, implement it, but it is the weakest-attested of the three and should be the
rarest roll.**

Elongated settlements strung along a linear feature - a road, a riverbank, a valley floor - are a
standard morphological category. The German *Reihendorf* ("row village") is the well-documented
type: one or two rows of houses or farmsteads either side of a village street, **with each holding's
farmland adjacent to its dwelling**, which saves travel time and transport effort. That last clause
is the functional argument, and it transfers directly to a rice hamlet strung along a track between
its paddies.

**Honest limitation**: the English-language record for the specific Chinese term 路村 was thin in this
pass, and the strongest documentation for the row form is European (*Reihendorf*). The functional
logic - frontage on the through-route, holding behind the house - is not culturally specific, and the
project's China-first rule is satisfied by the fact that elongated road- and river-following forms
are attested in the Chinese village-morphology literature. But this is weaker ground than R2, and the
roll weights should reflect that rather than pretending three equally-attested forms.

**Consequence**: linear is the one form where the road genuinely IS first, which is why it is the one
form that keeps a frontage seat pass - pointed at the connector, which is exogenous and exists before
the houses.

---

## R4 - The directional shadow corridor

**The existing scalar**: `BUNDLE_PITCH = 100.0` ft, justified by the threshing yard's sun - a
*kayabuki* thatch pitched 45 degrees or steeper puts the ridge about 20 ft up, and at 38N in the 10th
month that throws **39 ft of shadow by 9am**.

**Recovering the geometry from that number.** Shadow length `L = h / tan(alt)`. With `L = 39` and
`h = 20`, `tan(alt) = 20/39 = 0.513`, so the solar altitude in question is about **27 degrees**. That
is consistent with mid-morning in the 10th month at 38N, so the existing constant is internally
sound and can be reused rather than re-derived.

**What the scalar throws away is DIRECTION.** A shadow does not fall in a circle. At 38N:

- At 9am the sun bears roughly ESE, so the shadow runs **WNW**, about 39 ft.
- At solar noon the sun bears due south and stands highest, so the shadow runs **due north** and is
  at its **shortest**.
- At 3pm the sun bears roughly WSW, so the shadow runs **ENE**, about 39 ft again.

So over the drying day the shadow sweeps a **fan through the northern semicircle**, from WNW through
N to ENE, reaching about 39 ft at the ends of the arc and less in the middle. **Due east and due west
are never shadowed at all.**

**The rule this yields**: a farmhouse shades a drying yard only when the yard lies in that northern
arc, within the arc's reach for that bearing. Two farmsteads standing side by side on an **east-west**
line never shade each other's yards at any hour, so their spacing is bounded only by footprint plus
working room - not by the sun. Two farmsteads on a **north-south** line must keep the full reach.

**Therefore**: replace the uniform 100 ft with a bearing-dependent requirement - full reach to the
north, footprint-plus-working-room to the east and west, interpolated between. This is precisely the
unimplemented step the constant's own comment names: *"THE HONEST WAY TO GET MORE DENSITY HERE is
what real yashiki lots did: STAGGER east-west rather than space rows further apart. The placer is
free to; nothing asks it to yet."*

**Deliberate departure from literal reality, recorded**: we evaluate the arc rather than simulating
the sun's position continuously. A continuous simulation would be more precise and would change no
placement decision at map scale, because the reach varies by a few feet across the arc while our
smallest placement quantum is a house width. The arc is the cheaper model and the honest one.

**Alternative considered and rejected**: keep the scalar and merely lower it. Rejected explicitly by
the existing comment, which warns that lowering the asked pitch does not make the cluster tighter -
it makes the placer spill the overflow outside the band, which is how one cohort seed grew a two-farm
satellite 500 px off the nucleus.

---

## R5 - Should the access rules become form-conditional, or should dispersed maps declare a waiver?

**Decision: form-conditional, keyed on the declared form in `meta`.**

`farmhouses_reach_a_way` (0610) and `lanes_reach_something` (0607) currently gate on
`M["meta"].get("generated_by")` - that is, they apply to every scripted map. Their own justification
is explicitly about ONE form: *"Every house in the nucleated village is accessible via the
INTERCONNECTED system of narrow lanes and alleys."* The premise is nucleated; the application is
universal. A correct dispersed hamlet would fail both.

**Why form-conditional rather than a waiver.** The gate has a waiver mechanism, and it is the wrong
tool here. A waiver says *"this map breaks a rule that is true of it, and here is why we accept
that"*. That is not the situation: a dispersed hamlet does not break the access rule, **the access
rule is not about it**. Encoding that as a waiver would file every dispersed map as a known
exception, which is exactly the "documented regression" the constitution refuses - and it would make
the cohort's waiver list grow with a form we chose deliberately.

**The rule keeps its teeth where it has them.** Conditioning is not weakening: for a nucleated map -
which is still the majority form and the one the research calls decisive - 0610 is unchanged. What
changes is that the check now states the form it applies to, which is what it always meant.

**0611** (`lane_ends_front_different_houses`) is a rule about lanes that EXIST, so it needs no
condition: a dispersed map with no internal lanes satisfies it vacuously.

---

## R6 - The settled sequence

The pipeline goes from 13 stages to 13 stages. `stage_ways` splits by provenance; the internal
skeleton folds into the existing derived-ways stage rather than becoming a fourteenth.

| # | stage | change |
|---|---|---|
| 1 | `stage_water_frame` | **+ rolls `settlement_form`** and writes it to `meta`. It is the metadata stage, and every later stage needs the form. |
| 2 | `stage_field` | unchanged |
| 3 | `stage_sink` | unchanged |
| 4 | `stage_track` | **renamed from `stage_ways`, and reduced**: keeps `seat_cluster` (which sets `plan.seat`, and which the houses need), the watercourse list, the CONNECTOR and the field SPUR. Loses the internal skeleton. |
| 5 | `stage_homesteads` | **form-conditional seating**: front row + cloud for nucleated; connector frontage for linear; spread for dispersed. `_FRONT_ROW_LANE_CAP` retired. |
| 6 | `stage_appurtenances` | unchanged |
| 7 | `stage_lanes` | **renamed from `stage_web`, and widened**: now derives the internal skeleton AND the web from the placed houses, via the existing `web_cuts`. No-op for dispersed. |
| 8-13 | notice, hinterland, woodland, windbreak, crossings, frame | unchanged |

**The one real casualty**: the connector currently starts at *"the skeleton's own gateway (the
downslope exit the layout defines)"*. With no skeleton at that point, it must start from the seat
band's own downslope edge, which `seat_cluster` already provides. This is the single place where the
reorder forces a genuine behavior change rather than a move.

**Why the skeleton folds into the web rather than staying its own stage**: both are now endogenous,
both derive from the same house coordinates, and `web_cuts` is already a pure 1-D solver that serves
two lane forms off one implementation. Keeping them apart would mean two stages solving the same
problem from the same input, in sequence, which is how the reach mismatch arose in the first place.

---

## R7 - The mandated baseline procedure does not work in a bare worktree (found 2026-08-23)

**Recorded because it cost a gate cycle and will cost the next session one too.**

Principle XIII requires the pre-change baseline be taken on unmodified code in a **detached
worktree**, never by stashing. Done exactly as written, `make done` in that worktree fails two tests
that are green in the clone:

```
AssertionError: no live scripted map had both a .svg and a .png - the guard checked nothing
    tests/pipeline/test_render_cache.py:278
AssertionError: no live scripted map had both a .svg and a .json - the guard checked nothing
    tests/tools/test_scatter_audit.py:271
```

**Neither is a code failure.** Rendered artifacts are gitignored, so a freshly-created worktree
contains no `.png` or `.json` for any pool map. Both tests are written to refuse to pass VACUOUSLY -
they assert that they actually checked something - which is good test design and exactly why they
fire here. The worktree simply has nothing for them to check.

**Consequence for this feature's baseline**: the cohort number (44/48) is valid from the worktree,
because `cohort_audit` generates what it measures. The GATE baseline is taken from the clone's own
green `make done` on the same commit (`8ec2a91`), which is sound because the comparison at the end is
also clone-side - like for like, with the same artifacts present.

**Consequence for the procedure**: a worktree baseline must either regenerate the pool first, or
accept that these two artifact-dependent guards cannot run there. Worth carrying into the project's
baseline guidance rather than rediscovering; a session that reads two failures on unmodified code and
believes them will either "fix" a non-defect or conclude HEAD is broken.

---

## R8 - US3 WAS ALREADY IMPLEMENTED, and R4 was written from a stale comment

**A correction to this document, recorded rather than quietly edited, because the wrong version was
the basis for a whole user story.**

R4 derived a directional shadow corridor and proposed replacing the uniform `BUNDLE_PITCH`
separation with it. That proposal rested on the constant's own comment - *"THE HONEST WAY TO GET
MORE DENSITY HERE is what real yashiki lots did: STAGGER east-west rather than space rows further
apart. The placer is free to; nothing asks it to yet."* Reading the placer rather than the comment
shows the comment is out of date. Three separate mechanisms already do the work:

1. **`_sun_corridor_ok` (`settlement/rolling/fit.py`)** keeps `SUN_CORRIDOR_FT = 39.0` of open
   ground SOUTH of every threshing yard, and tests **both directions** - this house may not shade a
   yard already placed, and this yard may not be shaded by a house already standing. It carries the
   same 45-degree kayabuki / ~20 ft ridge / 38N / 10th-month derivation R4 recovered independently,
   and `stage_homesteads` opts into it unconditionally. The gate check
   `yards_unshaded_by_neighbors` enforces it on the finished manifest.
2. **`_yard_sun_conflict`** additionally stops a GROVE sitting in a neighbor's yard corridor, and
   `_garden_shaded` stops a farmhouse shading a neighbor's dooryard garden.
3. **Feature 121** already retired the circumscribed-circle separation in favour of real rotated
   footprints, so pairwise spacing is footprint-based, not radius-based. `_house_too_near_a_neighbor`
   is an EAVE-DRIP rule (two thatched roofs must shed separately), not a sun rule, and it is already
   only a couple of feet.

**So `BUNDLE_PITCH` is already what R4 said it should become**: a ROW-PLANNING constant, not an
omnidirectional pairwise separation. Nothing pays 100 ft east-west; the row is planned at that pitch
because a row needs house depth plus yard plus the 39 ft of sun, and the pairwise tests are
independent of it.

**Decision: make NO code change for US3.** Implementing the R4 corridor would be a second
implementation of a rule the checker already owns, which is precisely the failure the project warns
about - *"a tool that re-derives a rule will eventually disagree with the checker and then tell you
the wrong thing with total confidence."* SC-005 (no drying yard shaded by a neighboring farmhouse)
is already satisfied and already gated; SC-006 (a pair closer than the uniform pitch) is satisfied by
construction, because the uniform pitch never governed the pair.

**What SHOULD change is the stale comment**, so the next reader is not sent down this path again.
