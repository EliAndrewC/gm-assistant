# Future work: cross-cutting

**Things that are not about one kind of map**: the gate, the caches and the render pipeline, engine
module organization, and generation doctrine that applies at every tier.

The test for this file is simple - if fixing it would change maps of more than one type, or would
change no map at all (tooling, structure, checks), it belongs here.

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

## 2g. The render cache serves a PNG made from a DIFFERENT SVG (recurs; five times on 2026-08-19/20)
`test_every_live_pool_png_matches_its_own_svg_viewbox` fails whenever a change moves a map's geometry:
the gen re-renders the SVG while the PNG comes back from the render cache, so the pair disagree on
aspect (kashikawa, 2600x3962 against the 3864 its own viewBox implies). Deleting the PNG and running
`regen --no-cache` fixes that pair - and the next `make done` re-breaks it, because the gate regenerates
too and the cache serves the same stale PNG again.

It bit five times in two days across three sessions, always after someone moved geometry, and each time
it was fixed by hand rather than diagnosed. **It is a cache-key defect, not a map defect**: the PNG's
entry is being treated as valid for an SVG it was not rendered from. Start at `pipeline/render_cache.py`
and ask what the PNG half of an entry is keyed on, and whether the SVG's own bytes are in that key -
`dev/cache.md` already records that an entry has "TWO independently-perishable halves" and that the
artifact half staying valid says nothing about the other half. This looks like the same shape one level
down: the SVG half is refreshed, the PNG half is not, and nothing notices until a test compares them.

## Three members that are in `settlement/structures/` only because of where feature 025 cut

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

## 8. `TWIN_AXES` believes a declared knob over the drawn shape

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
the cloud record what it actually produced.

**RULED BY THE GM 2026-08-24: the twin detector measures WHAT WAS DRAWN, not what was asked for.**
The GM's reasoning, which generalizes past this one axis: *"the thing that we are detecting when we
are doing automated checks is we should be running the automated checks against what is actually
being rendered, not just checking to see whether what was asked for was valid and then doing
something else and then not checking whether what we did matches our specifications."*

A knob records an INTENTION. A check that reads the knob is asking whether we meant well, and it
passes cleanly on a map that drew something else entirely - which is the failure mode this project
has hit repeatedly under a different name (`cluster_shape` was rolled, printed in every cohort header,
and read by nothing for months). So: prefer the measurement wherever both exist. **Not implemented
yet** - recorded here as DECIDED-AND-PENDING per the same 2026-08-24 direction that a code change
should not be started mid-feature.
