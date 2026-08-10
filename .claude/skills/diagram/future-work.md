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
  (locators, why_placed.py) instead of guessing coordinates - every hand-guessed seat this
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
