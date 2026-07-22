# Phase 0 Research: Paddy-Dominant Near-Ring Farmland

**Feature**: 014-paddy-dominant-near-ring | **Date**: 2026-07-22

This is the Principle XII **opening gate** for the composition correction, plus the mechanism decision. It supersedes exactly one decision in [feature 013's research.md](../013-near-ring-farmland/research.md) - the near-ring land-use *composition* - and references (does not repeat) 013's still-valid grounding: site selection, the von Thünen intensity gradient, the tunable `near_ring_density` knob, and the frame math. The closing gate (re-examine the rendered PNGs, confirming paddy now dominates) is carried in `plan.md` / `tasks.md`.

## Part A - Historical grounding (Principle XII opening gate)

### The element being changed: the MIX of the packed near ring (dry-grain-dominant -> paddy-dominant)

**What the historical reality was.** A market town or county seat in wet-rice China (Song/Ming, Rokugan's geographic model) or Japan sat in the middle of its **best rice land** - it grew in the alluvial basin, at the river confluence, on the valley floor, *because that flat waterable ground grows wet rice*. So the land immediately around the settlement - the flat, waterable near ring the frame shows - was **overwhelmingly wet paddy**. This is the same site-selection logic 013 used to justify densifying the near ring at all; carried to its honest conclusion, it says the near ring is not merely *cultivated* but specifically *paddy*. Dryland grain (barley, millet, soybean, the other Five Grains) was real but **secondary**, worked on the higher and drier ground the irrigation could not command - the terraced lower slopes, the levee backs, the un-waterable margins - not blanketing the flat valley floor. The one dry land-use that genuinely pressed right up against the town wall is **intensive vegetable / market gardening**: the von Thünen inner ring, small night-soil-fed truck plots feeding the urban market, worth the manure and labor precisely because they are close to the buyers.

**Whether the (013) design matched it.** No - and that is why this feature exists. 013 made the near ring **dry-grain-dominant**: it held the paddy fixed and filled the flat ground with dryland grain (barley/millet/soybean hatake), because dry cropland is exempt from the water-source rule and needed no plumbing. The rendered Hirameki/Hoshizora maps read as a town ringed by dry grain fields - historically backwards. 014's design (paddy dominant on the flat waterable ground, dry grain demoted to the drier margins, gardens near the town) matches the reality; 013's did not.

**What determines the element in reality.** Water and micro-topography, read at the near-ring scale:
- The flat, **waterable** valley floor -> **wet paddy** (the dominant use, because that is why the town is there).
- The higher / drier / un-irrigable margins and lower slopes -> **dryland grain** (secondary).
- The ground **immediately against the town** -> **intensive vegetable/market gardens** (von Thünen inner ring, night-soil-fed).
- Hill slopes, wet toe, far margins -> tree crops / woodland / scrub / fallow (unchanged from 013).

### The number 013 mis-applied (corrected)

`budgets.md` ("Rice and arable-land math") says only ~1/3 of rice-*suitable* land is active wet paddy in any year. 013 leaned on this to normalize a dry-heavy near ring. But that ~1/3 is a **domain-wide average over 560 sq mi that includes the hills, the dry margins, and the labor-fallow** - the land that is rice-*suitable* in principle but not flat/waterable/worked this year. The near ring of a valley-bottom town is the **opposite extreme**: the flattest, most waterable, most intensively worked ground on the whole domain. Its paddy share should therefore be **far above** the ~1/3 domain average, not below it. Applying a domain-wide average to the single most paddy-favorable location on the domain was the analytical error; 013 compounded it by choosing the dry reading for engineering convenience.

### Rejected design (recorded per Principle XII so it is never reinvented)

- **Rejected: dry-grain-dominant near ring (the feature-013 outcome).** Historically backwards for a wet-rice basin. The flat waterable valley floor around a rice-growing county seat is paddy; dryland grain belongs on the drier margins and lower slopes; market gardens belong against the town. 013 chose the dry reading **only** because dry cropland is exempt from `fields_show_water_source` and so needed no plumbed irrigation - a drawing convenience, never a historical finding. 013's `research.md` Element 3 and `FR-003` ("densification carried substantially by dry-field plots") stated this convenience as if it were grounded; it was not. Any future pass that is tempted to fill a wet-rice near ring with dry grain "because paddy needs water plumbing" must stop here: the honest answer is to plumb the paddy (or, where there is genuinely no water to draw from, to draw a *thinner* near ring at a lower tier), not to substitute dry grain for the dominant crop.

### What stays (inherited from 013, still correct)

- The near ring reads **packed**, not sparse (013's win; FR-005 keeps the cultivated-fraction floor).
- Topography governs: no paddy on hill slopes; scrub/fallow at the far margins and wet toe.
- **Tunability**: the `near_ring_density` knob (dense/medium/thin) and the dial-down (Hoshizora, a grazing/relay town) remain - now expressed as *paddy-led* cultivation that thins with the tier, not as dry grain.
- **Calibrated liberty on the degree of density** (013): unchanged. 014 does not re-open how *packed* the ring is, only *what crop* dominates it - and paddy-dominance in a wet-rice basin's near ring is not a matter of degree that needs liberty; it is the straightforward reading.

### The honest constraint (why this is real work, not a repaint)

Wet paddy needs a **plumbed water source the validator checks** (`fields_show_water_source`). 013's dry fill had none. So making the near ring paddy-dominant means generating *real, watered* paddy near each settlement - the harder path. Where a map genuinely has no water in-frame for the new paddy to draw from, the honest result is a **thinner / lower-tier** near ring, **not** fake paddy and **not** a dry-grain substitute. This constraint is a feature, not a bug: it keeps the map hydrologically honest.

## Part B - Mechanism decision

An engine recon (read-only over `check_village.py`, `settlement.py`, `waterfields.py`, the four town/city gens) settled the constraints that fix the mechanism:

- **The paddy water-source predicate is narrow but abutment-friendly.** `fields_show_water_source` passes a `kind=="paddy"` field iff (1) a recorded `M["channels"]` entry ends inside it, OR (2) an outline vertex is within **18px of a stream centerline**, OR (3) a vertex sits in the **pond's 1.0-1.10x ring**, OR (4) the field **runs off the map edge** (exempt). The **moat, comb drains, comb envelopes, and field ditches do NOT count** - only streams, channels-ending-inside, and the pond. So new paddy can be watered *without drawing a channel* only where it can touch a stream or pond (or run off-edge).
- **A channel-free paddy-basin primitive already exists**: `paddy_field(shape, ...)` (`settlement.py:896`) takes a bbox or polygon, quilts it into flooded bunded plots via `_paddy_plots`/`_paddy_surface` (the true premodern paddy look), and records a **minimal** `kind="paddy"` field (name, outline, bbox - **no** channels, ditches, floor, or vis_bbox). Because it records no ditches, it is **vacuously exempt** from `field_ditches_reach_source_and_sink`, `paddy_fan_has_floor`, `field_outline_matches_planting`, and the channel-anchor checks. It is currently test-only; no pool gen uses it. This is the ready-made basin drawer for a near-ring paddy filler.
- **`build_comb` fans auto-wire all their water** (`draw_comb_field` records the source channel + ditches + floor), so *enlarging* a comb (via `field_fall` / `canal_a_len` / `offtakes_a`) grows real, water-legal paddy for free - but it is per-map, seed-swept hand-tuning that can re-expose tessellation holes.
- **A paddy-dominance check is a near-verbatim clone** of `near_ring_cultivated_fraction`'s 25px band sampler (`check_village.py:5660`), tallying paddy-outline cells vs dry-grain `dry_plots` (`crop != "garden"`) cells instead of one combined count.
- **City cost**: `city_outside_fields_have_farmhouses` requires every extramural city paddy to have >=2 farmhouses within 165px unless it runs off-edge; `common_fields_vary_orientation` caps town paddy bboxes at 80000px unless orientations alternate; `pond_clear_of_paddies` + `streams_avoid_fields` mean a basin must abut (not straddle) its water body.

### Decision: a `near_ring_paddy` basin filler (primary) + comb enlargement (per-map supplement) + demote the 013 dry fill

**Decision.** Make near-ring paddy the dominant use by three coordinated moves:
1. **Add `Settlement.near_ring_paddy(bbox, ...)`** - a filler modeled on `near_ring_cropland` but drawing **flooded paddy basins** (reusing the `paddy_field` tile primitives). It places a basin only where it can be **legitimately watered**: abutting an existing stream (within ~18px, without the stream crossing the basin), or in the pond's 1.0-1.10x ring, or running off the map edge - and **skips any cell with no reachable water** (that ground falls to the demoted dry/garden fill or stays scrub). It records `kind="paddy"` fields with **no channels** (staying out of the ditch/anchor/downhill machinery), keeps basins off the pond core, under the town orientation cap, and - on cities - either off-edge or farmhouse-ringed.
2. **Enlarge/add the existing hand-authored combs per map** where the flat near-ring floor has water the filler can't cheaply abut, so real irrigated paddy claims more of the floor (auto water-legal via `draw_comb_field`). Per-map tuning in the gate loop.
3. **Demote `near_ring_cropland` (the 013 dry fill)** to two reduced passes: an **outer-margin grain pass** on the drier/higher ground (near `M["hill"]` / the frame margin, the flat valley floor added to its `avoid`) and a **near-town garden band** (a tight bbox hugging the wall / structure halo, `garden_frac` ~0.85 so it reads as gardens). This puts grain on the margins and gardens by the town.

**New check.** `near_ring_paddy_dominant` (town + city): clone the 25px near-ring band + `committed` mask, tally paddy-outline cells vs dry-grain cells, require **paddy cells > dry-grain cells** (scaled per `near_ring_density` tier so a thin map is paddy-led but sparser, never dry-dominant). Ship a frozen dry-dominant (013-style) manifest as a negative regression fixture.

**Rationale.** This satisfies Part A: paddy becomes the dominant, *real* (plumbed) near-ring use; grain retreats to the margins; gardens sit by the town. It is honest about water - the filler never conjures paddy where no water reaches (the spec's edge case: where a map genuinely lacks near-ring water, the honest result is a thinner/lower-tier ring, not fake paddy). It is in-grain: the basin drawer and the check both reuse existing primitives, and comb enlargement is the settled paddy doctrine. It touches shared engine code once and lets the gate turn every pool map into a checked artifact.

**Alternatives considered.**
- *Pure comb-enlargement (Option A only)*: honest and auto-water-legal, but a comb is a *fan* radiating from one sluice - enlarging it does not uniformly fill the near ring, and it is fragile per-map seed-tuning on every fan of every map. Kept as a *supplement*, rejected as the sole mechanism.
- *Per-basin intake channels* (draw a short channel to water each far-from-water basin): would let paddy fill the whole floor, but every channel drags in `channels_flow_downhill` + anchor + collision constraints, and many short channels per map is fragile and cluttered. Rejected; the filler stays channel-free and simply declines to place paddy where no stream/pond/edge is reachable.
- *Keep 013's dry fill, just relabel*: rejected outright (Part A) - the dry-grain-dominant near ring is the ahistorical thing being corrected.

**The honest limit (disclosed).** The filler makes paddy dominant on the *waterable* flat ground; ground with no reachable water cannot become paddy. In a real wet-rice basin the irrigation network reaches nearly the whole valley floor, and the combs' streams/ponds stand in for it - but if a specific map's near ring has too little reachable water to make paddy dominant without faking it, the correct answer is to draw that map at a **lower `near_ring_density` tier** (a thinner, more honestly-marginal ring), not to invent water. The check enforces dominance; it does not force a specific paddy *quantity*.
