# Minami - notes

Mode B provincial city, 1 px = 3 ft, walled, `wall_defense="peaceful"`, river port on the
Hayakawa, Fox clan (Nanke lineage), population **2,600**. Feature `specs/016-minami-provincial-city`.

`ALL CHECKS PASSED`; `check_village.py pool/provincial-cities/minami.json --capacity` reads
**SIZED_AND_PACKED**, and the map draws **exactly 520** dwellings against its 520 target - the
population check allows NO band (see below).

## What this map is the worked example of

- **The eight-precinct Fox temple program.** Seven modest precincts for the Fortunes of Good Luck
  plus a slightly larger Inari - every one smaller than the single great complex an ordinary clan's
  city builds - scattered by TRADE rather than belted into a rim teramachi, because each is an
  economic house sited where its business is. Declared via `meta(temple_exception="fox_structure")`.
- **The `peaceful` wall tier** - first map in the pool to exercise it.
- **The first non-3,000 population**, and the first city with `CityProgram.extras`.
- **Clergy outside the lay caste table**: 8 precincts x 6 hereditary temple families = 48 households
  (only the Three Bonds are celibate), so the lay figure is set 240 below the declared total and the
  two add back up: 472 lay + 48 temple = 520 dwellings x 5 = 2,600.

## The wall is sized to the population, not the other way round

This is the load-bearing decision, and it was got wrong once before it was got right.

An earlier pass found the map holding ~440 dwellings against the 504 the budget predicted, and
resolved it by **lowering the population to ~2,240 and pinning the ring at its old value**. That is
the wrong direction: the declared figure is the spec's (FR-010), and if the enclosure cannot hold it
then the enclosure is what is wrong. The skill's own doctrine says as much - if the capacity report
wants a resize, fix the budget model, not the map.

So `LAY_POP` is 2,360 and the ring comes from `plan_city` again (FR-011): **431x400 -> a CIRCULAR
462x462**, interior 533k -> 660k px^2. The circle is forced by the river: at aspect 0.93 the west
wall had closed to 3px of the wharf, so the city could not grow westward at all, and raising the
aspect spends the same interior on a rounder ring - rx FALLS (the wall steps back off the bank) while
ry rises into open country. A river city grows along its valley, not into its own landing. Two budget
corrections paid for the extra ground, both measured off this map:

- **`temple_precinct_px2` 3,400 -> 11,600.** 3,400 priced the walled compound alone (~0.70 acre) and
  left out everything else a precinct plants in the fabric, which is what a wall has to enclose:
  hall compound block ~5,125, torii approach and its stand-clear ~1,720, caption band ~4,000,
  wayside shrines ~1,790. **The halls did not grow; only the accounting did.**
- **A `laneway excess` extras line, 34,000 px^2.** `citybudget` allows a flat 7% of interior for
  circulation (43,675 here) and Minami draws more, because eight precincts sited by trade all have to
  be reached: the ring, street and roji BEDS alone measure 56,936. Only that measured excess is
  charged, and conservatively - it counts neither the trunk road's in-wall run nor any frontage
  standoff band.

**No fragmentation premium, and no caption premium.** An earlier attempt was going to price the
~12% packing shortfall as a budget line; it is gone because the shortfall was never the wall (see
below). And a caption band must never drive the wall size - that would inflate a to-scale plan for a
cartographic reason, which is the one thing a to-scale mode may not do. Captions are MOVED instead.

## The declared population is EXACT (GM 2026-07-27)

`population_consistent_with_housing` used to allow 7%. That band is gone - `population_tol` defaults
to `0.0` - so this map draws 520 dwellings on the nose, not "about 520". The gen ends with
`fill_exactly()`, which asks one caste at a time for precisely the shortfall (top_up stops the moment
that caste's tally reaches the figure asked, so it cannot overshoot), smallest footprints first.
Two traps it has to survive, both commented at the call site: **count what the CHECK counts** (the
local `DWELL` tuple, and a city with an agricultural district also counts in-wall farmhouses), and
**respect the caste CEILINGS**, or the total closes while a caste leaves its band.

## The five things that cost the most to learn

1. **THE REGISTRY MAP.** Verified against `settlement.py`, not assumed:

   | placer | `block_polys` | `corridors` | `placed` |
   |---|---|---|---|
   | `rowpack` | YES (`_in_blocked`) | **NO** | yes |
   | `top_up`, `place_wells`, the `_fits` packs | yes | YES (`_near_corridor`) | yes |

   Both are **center**-tested; the difference is shape, not footprint-vs-center. So anything that
   must be kept clear of BOTH the terraces and the fills needs BOTH entries - a corridor alone lets
   the rows walk through it, a block poly alone lets the fills do it. And because both are
   center-tested, a band must be sized to the caption's half-extent PLUS the widest kind's
   (`merchant_house` 16.7x11.3, a wellhead r=8), or a wide roof whose center clears it still
   overhangs.

2. **`top_up`'s 3px standoff is why its fills were detached** - which starved the dwelling count AND
   held `city_row_housing_touches` down, since a detached fill can never touch. A final party-wall
   pass at **gap=2.4** is the measured threshold: below it, a fill seated behind a row blocks its
   doorway (`city_house_doors_unblocked`) and stacks terraces three deep
   (`city_rows_max_two_deep`).

3. **`city_row_housing_touches` cannot be won by adding rows** - they raise numerator and
   denominator alike; the lever is trimming the top_up fill TARGETS, since a fill can never touch.
   The per-caste targets now sit at their band FLOORS and `fill_exactly()` closes the total, which
   keeps the ratio high and the figure exact at the same time.

4. **Wells must be seated BEFORE the terraces close.** By the time the fine passes run, `open_seat`
   reports the ground genuinely full and six tight `place_wells` passes added zero wells. The extra
   draw-points for the courts serving 30+ households are seated early, and each seat is ASKED of
   `open_seat` rather than hand-picked.

5. **A stale reservation is worse than none.** A `label_ground` entry left at a caption's old seat
   reserves ground the caption no longer occupies - which is exactly what left the fire tower's
   caption unprotected after the tower itself moved.

## Things not to redo

- **Do NOT shift the x1300 roji.** Moving it 10px east reflowed every rowpack in the western
  quarters and took caption collisions from 2 to 15. A lane is load-bearing for everything that
  packs around it.
- **The SE ward is CORRECTLY low-density.** Samurai plots are `C_SPACED` 2,480 px^2 against a
  commoner's `C_PACKED` 690, and the quarter also carries the yamen, six ministries, the mausoleum,
  the martial hall and two dojos. Chasing density there fights the budget. Servants do not belong
  inside a gated ward either - terracing them there starved both samurai checks.
- **A gate market straddles its road.** `s.frontage` seats a rank on EACH side of its line ~15px
  out; the ranks are 31px apart and the band that is both clear of the roadbed and inside the 28px
  fronting rule is only 14 wide, so no offset puts both ranks in it. Putting the line ON the road
  (with `skip=ROAD`) is the answer, and is what a guan-xiang market looks like anyway.
- **No extramural streets.** `city_streets_clear_of_wall` forbids a lane outside the rampart, and
  two free-standing market streets also split `city_streets_connected` into three groups.
- **Ring-relative features scale with the ring** (`_ring_rel`: the ward fence, its kido, the cargo
  canal, the water gate, the dock, its bridge), and roji outer ends SOLVE onto the ring bed
  (`_ring_y`), because the ring road is a 20-gon whose chords sit inside the ellipse - an ellipse
  estimate lands 3-4px past the bed, which the gate reads as a lane poking past its junction. Both
  exist so a re-derived wall moves them instead of leaving numbers to re-solve by hand.
- **`city_capacity` runs under the check name `city_wall_sized_to_population`.** Grepping the gate
  for "city_capacity" returns 0 and reads as a check that never runs. Its CLI is
  `check_village.py <m>.json --capacity [--capacity-map]`, and its per-quarter density table is the
  tool that answers "wall or packing?".
- **`city_samurai_estates_outside` caps the drawn country seats at 3** - they are dispersed across
  the rural district, so a city shows a token few. Do not add more to carry the samurai caste band.

## Process note

Two sessions edited this generator concurrently for several hours (the first was believed crashed
but was live, PID 107349). During that window the generator LOOKED nondeterministic - identical
source hash, different manifest - because the source was changing between runs. It is deterministic:
identical source gives byte-identical output, verified. Before inheriting a clone, check
`ps -eo pid,etime,cmd | grep claude`.

## What the closing bookend and the independent review found (2026-07-27)

`check_village` was green the whole time. Both passes below looked at the RENDER.

- **The gate was a breach, not a gate.** Every city in the pool opened a `2 x 38` px hole with piers
  `+-35` px apart - **228 ft** of opening, **210 ft** between the piers, against a 26 ft trunk road.
  The 2026-07-22 to-scale pass had converted the gate furniture's FOOTPRINTS to real feet and left
  the OFFSETS that position them as fixed pixels; `road_half` spent a `road_width` default that is a
  width in FEET as PIXELS. Now 30 ft clear with 15 ft piers, water gate 60 ft, all through `px()`.
  Deliberately NO new check - see `settlements/cities/defenses.md` for why one could not catch it.
- **Five caption collisions**, four invisible to `no_label_overlaps`: its 2 px horizontal slack is
  sized for estimation error, and both the bold-serif and italic faces put ink outside the measured
  box. `oil press` x `Temple of Bishamon` (0.7 px), `Temple of Daikoku` x `graveyard` (a 2.0 px gap
  that reads run-on), `punishment ground` and `dojo` both through the ward kido's guard post, and
  `boundary stone` through a gate-market stall.
- **`kido` and `docks` were unclassified for labels.** The ratchet iterates the overlap registry and
  `matrix_extents` SKIPS the permissive classes, so every `FIXTURE` key is unreachable by it - the
  identical hole `wells` fell through a day earlier. Classifying `docks` immediately caught a real
  pre-existing collision on Nagahara (`dye works` over its dock). Six FIXTURE keys are still
  unclassified, written down as knowingly open in `check_village.py`.
- **The dock basin had no caption at all** and reads as an ornamental pond. Now "cargo basin".

### Still wrong, recorded rather than fixed

- **The three country estates are invisible** - one painted over by a paddy (draw order: the compound
  is emitted ~121k SVG characters before the plot that covers it), two outside the rendered view. The
  caption names three and points at none, and the caste band counts all three. Both fixes reflow the
  rural belt, and `farmsteads()` on the city path spaces house-to-house without measuring the ANNEX
  envelope, so any reflow drops a pair whose garden overlaps a neighbor's shed by a fraction of a
  pixel. The fix that holds is the packer's annex clearance. Full reasoning at the `EST` block.
- **The timber and charcoal ground is drawn as a livestock pen.** `s.animal_ground(...)` records into
  `stable_yards` with troughs, hitching rails and dung heaps - so the map's declared economic
  centerpiece, 3.7 acres and an 18,100 px^2 budget line, is indistinguishable from the north gate's
  marshalling yard. Needs a `timber_yard` glyph (log ricks, sawpit, charcoal godowns) on the same
  deferred `flush_stable_yards` path, plus the charcoal kiln the docstring promises and the map lacks.
- **The budget charges two gate marshalling grounds and one is drawn** (4,536 px^2 of wall bought for
  ground that is not there).

### 2026-08-02 - the log boom redesigned from a mid-stream chain to a shore-fast pen

The GM's finding on the first drawn boom: "it just looks like a bunch of logs in the middle of
the river." The research pass behind the fix is recorded in `research/urban-features.md` ("The
log boom"); the short form: a boom is a floating fence - anchored to nothing it holds nothing -
and attested booms anchor to the bank and run ALONG a navigated river, the pen between chain and
shore, with the fairway kept clear by law. The redrawn glyph is a pen: chain on the offshore
edge, end-booms closing to the east bank, mooring posts and pile clusters, raft-mats packed
near-solid, ~40 ft of held water = a third of the 120 ft channel. Three checks now hold it
(`log_boom_moored_to_the_bank`, `log_boom_leaves_the_fairway`,
`log_boom_serves_the_lumber_yard`), and the pre-fix capture is frozen in `pool/regressions/`.
**The full-span catch boom is deliberately absent**: that form (the Kiso *tsunaba* - a rope bank
to bank catching the loose-log drive) belongs at the Fox gorge mouth upstream on an unnavigated
reach, where loose logs become the rafts that arrive here - it is off-map lore, not port
furniture, and Minami's river carries wharf/dock/canal traffic that a spanning boom would dam.
Post-review adjustments (settlement-review 2026-08-02): pen head held ~45 ft below the last
wharf jetty so the jetty keeps its berth, and the zaimokuya slid to its bank frontage so pen and
yard read as one works across ~40 ft of haul ground.
