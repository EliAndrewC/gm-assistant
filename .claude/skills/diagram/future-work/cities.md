# Future work: cities (towns, provincial cities, capitals)

**Everything to do with an urban settlement**: walls and gates, wards and quarters, streets and
storefronts, the castle and its moat, ministries and precincts.

Provincial cities and capitals share one file because they are largely scaled versions of one
another (GM 2026-08-24).

**TOWNS ARE FILED HERE, and that is a judgment call worth flagging.** The GM's split named farming
communities and cities; towns sit between. They are filed here because their open defects are urban
in kind - storefronts, streets, inns, kiln glyphs - even though a town's population is still mostly
farmers. Move them if that reads wrong.

**Much of this file predates scripted generation.** Only hamlet `valley_paddy` is SHIPPED; village,
town, city and capital are all NOT STARTED ([`../migration-plan.md`](../migration-plan.md)). Entries
here that assume a NEXT hand-authored map are annotated: the task is dead, the insight is an input to
the tier's conversion.

## 1. Parametric feature bundles (gate wards, rim bands) - HIGH VALUE

> **PREMISE RETIRED (audit 2026-08-24).** This entry assumes a NEXT hand-authored map: its fix
> sketch says "extract the helper the next time a gate bundle is authored or moved". There will not
> be one. The 19 hand-authored maps are FROZEN (never regenerated, never re-gated), and
> [`migration-plan.md`](migration-plan.md) makes conversion - not retrofit - the answer for every
> tier above hamlet. So the TASK as written is dead.
>
> The INSIGHT is not, and is why this is annotated rather than deleted: "a layout change should be a
> parameter change, not hundreds of re-typed coordinates" is precisely what a scripted city generator
> has to get right, and this entry records what it cost when it was got wrong. Read it as an input to
> the city-tier conversion, not as a job queued against the current pool.

The 021 wall resize (2026-08-10) invalidated ~hundreds of hand-typed coordinates and cost
hours of migrate-regen-check cycles. The pieces that were FORMULA-DRIVEN from the wall
parameters (rim temples, moat, ring road, wall towers) migrated instantly and for free; every
literal coordinate had to be re-typed one check-failure at a time - and a careless bulk
shifter corrupted list multipliers (`* -144`) and took extra rounds to repair.
**Fix sketch**: a `gate_ward(gate, ...)` helper that lays a whole guan-xiang bundle (market
frontage, flophouse, inn+stables+yard, its lanes, its district poly) RELATIVE to whichever
gate it is handed; a sibling for ring-adjacent band fills. A layout change then becomes a
parameter change. Extract the helper the NEXT time a gate bundle is authored or moved.

## 4. WALL SIZE SETTLES FIRST, against a slack threshold (GM process rule, 2026-08-10)

> **STILL OPEN, but read the era (audit 2026-08-24):** this is a PROCESS RULE for hand-authoring a capital, and the capital tier is NOT STARTED (migration-plan.md). It binds whoever hand-authors the next capital - if anyone does - and should be folded into the city/capital generator's design rather than left as a rule someone must remember.

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

> **STILL OPEN, but read the era (audit 2026-08-24):** this is scoped to `wip/shiro-daika.gen.py`, which is a hand-authored capital sitting OUTSIDE the pool and outside the gate. It is real deferred work, but it is deferred against an artifact nothing currently regenerates or checks.

After the third wall derivation the slack check passes (<=15% claimed-open) but the render
still reads empty to the GM's eye: bare-rendered commons, the model's 20% circulation, and a
fabric that packs naturally denser than the model prices. Options weighed: a third shrink
(hour-plus migration each, diminishing returns), raising population (rejected - 12,360 is
budgets.md-anchored research), or defer. DEFERRED by GM choice: ship the green map as the
first pass; **wall-to-fabric fullness is the headline requirement of the fabric-first
feature (#2)**. Cosmetic option noted: a faint ground tint for kept commons (between blank
and scrub). When fabric-first is specced, start from this map's slack profile as the
motivating example.

## 2026-08-10 addendum: the first pass SHIPPED against #5

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
