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

## Pocket ponds carry ink-on-water of their own (settlement-review, 2026-08-15)

Found while confirming the azemame water-honesty fix: Inashiro's pocket pond at (2144, 1724) has
the field-foot margin drain stroke painting across its lower-left quadrant, and hinterland
scrub/grass tufts drawn on top of its fill (the pond's lower half hangs outside the field envelope
over hinterland ground, and the late drain + phase-5 scatter both lap it). Same principle the bead
fix established - no ink over water, no water under ink - one class over: the pocket pond needs a
keep-out the hinterland scatter and the late water honor (or `_plot_pond` should refuse a plot
whose ellipse leaves the field envelope). Barely visible at fit zoom; logged rather than fixed
because it is baseline-adjacent, not part of the bead delta.

## Review residue from the supply-bank hem re-roll (settlement-review, 2026-08-15)

Three judgment items the four DELTA reviews surfaced that are real but were deliberately logged
rather than fixed with the hem work (none is a gate failure; each is an idea for the next pass at
its area):

- **A sluice-gate glyph at the hamlet intake.** Mizuguchi is NAMED for its sluice (水口) and draws
  none - the brook simply necks into the head-race. The engine has sluice-gate furniture at other
  water handoffs; the comb intake could carry one at every tier, and on Mizuguchi it is the point
  of the map.
- **Kashikawa's woodland commons all land off-frame.** The crop is content-derived and the three
  coppice patches sit past it, so the "oaks on the high ground" of the name story are implied
  rather than drawn. Worth deciding whether commons should count toward the content bbox, or be
  seated with a preference for on-frame ground.
- **The kept/dropped read along hemmed ditch banks.** Inashiro's first lateral carries an
  alternating chain of kept bank plots and dropped slivers that reads as a dashed line of boxes; a
  coarser keep-or-drop over a whole bank strip would read cleaner. Same area as the hem work but a
  presentation refinement, not a correctness one.

## Review residue from the canal-B fork re-roll (settlement-review + cohort, 2026-08-16)

The fork feature (research/water.md "The head-race forks - supply commands both flanks") re-rolled
the four live hamlets three times; the review rounds' errors are fixed (thread tails, minimax
wells, the board's clump keep-out, the lane-crossing guards). What remains, recorded as debt:

- **A hairline bund-in-supply-stroke on ~2 of 48 rolled seeds** (25, 34; also seed 41 at
  hh=15). One plot vertex sits ~0.06 px inside a canal-B stroke's drawn width - manifest
  rounding scale, but `paddy_bunds_clear_the_supply_channels` rightly fires. The offending
  rings are SMALL plots near the fork (likely `_fill_wedges` fillers or a piece-joint
  governance gap in `clear_supply`'s per-piece `past` exemption - diagnosis half-done, see the
  session log). The pool and the cohort ratchet (seeds 41-44) are clean; fix before shipping
  any map rolled from a fresh seed, or when converting the village tier.
- **`meta.cluster_shape` records only when the cluster-seeds cloud actually runs** (Kashikawa:
  front rows + frontage seated all 20 houses, so a rolled knob went unhonored with no trace).
  A knob that can silently not-record is the "check that never runs" shape - record either the
  knob or the seeding mode, always.
- **Mizuguchi's SE floor wedge** - the field outline juts ~350 ft beyond its own drain as a bare
  green needle (grew ~33% in the re-roll). Wants the marsh treatment or trimming to the drain.
- **Sawada's woodland commons mostly crop out of the view** (two of three parcels wholly above
  the frame; the third half-cropped, hosting the title placard). Either the crop admits them or
  they seat inside the ground the crop keeps.
- **The in/out width ladder at junctions**: the 14 px head-race is fed by a 7 px brook and
  splits into arms summing 23.6 - drawn capacity grows downstream at every junction. All four
  round-2/3 reviewers flagged the same thing; it is the sanctioned linework convention (GM
  2026-07-21) but the fork makes the head junction the map's focal water feature, so it wants a
  conscious ruling either way.
- **Collector-junction wedge plots render in the water-gray fill** and at fit zoom read as tiny
  triangular ponds - conspicuous on Sawada, whose brief is "no pond".
