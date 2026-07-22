# Phase 0 Research: Near-Ring Farmland Density

**Feature**: 013-near-ring-farmland | **Date**: 2026-07-22

This document is the Principle XII **opening gate** (historical grounding before design) plus the resolution of the plan's open mechanism questions. Per Principle XII it states, for each element the feature changes: what the historical reality was (China-first, Japan corroborating), whether the design matches it, and what determines the element in reality. The closing gate (re-examine the rendered PNGs) is carried in `plan.md` and `tasks.md`.

## Part A - Historical grounding (Principle XII opening gate)

### Element 1: Near-ring land cover flips from scrub-dominant to cultivation-dominant

**What the historical reality was.** A market town or administrative seat in wet-rice China (Song/Ming, Rokugan's geographic model) sat in the middle of its most intensively worked land. Settlements are not sited at random: they grow where the land is best - alluvial basins, river confluences, valley floors with water and flat ground - because that is what feeds a concentrated population. The immediate ring around such a settlement was cultivated to a degree that astonished European observers: near-continuous paddy on the flat, terraced lower slopes, market gardens against the walls, and dryland plots on the drier margins. The denuded scrub that is genuinely the dominant cover in south China is a fact about the **hills between valleys and the ground far from settlement**, stripped for fuel and timber over ~1,000 years - not about the half-mile around a county seat on good bottomland.

**Whether the proposed design matches it.** Yes. The feature makes the flat, waterable near-ring ground read as predominantly cultivated (paddy + dry fields + gardens), and relocates scrub/rough-grazing to the frame margins and non-arable ground (hill slopes, the wet drainage toe). This corrects a placement error in the current engine, which applies the (real) denuded-scrub fact to the near ring where it does not belong. The current maps are the design that does NOT match; this feature is the correction.

**What determines the element in reality.** Three variables, in order:
1. **Site selection** - the settlement is on the good land, so the local arable fraction is far above the domain-wide ~4% rice-suitable average (`budgets.md`, "Rice and arable-land math"; the 4% averages over 560 sq mi of mixed terrain per median domain, the wrong figure for a settlement's immediate hinterland).
2. **Distance (von Thünen intensity gradient)** - the labor/transport cost of reaching a field rises with distance, so the nearest ground is worked hardest and the labor-limited fallow accumulates at the far margins and on the poorer soils, NOT in the near ring. Chinese wet-rice farmers intensified existing fields rather than extending the cultivated area.
3. **Topography and water** - only flat, waterable ground becomes paddy (Element 3).

### Element 2: The labor-limited fallow is relocated, not deleted

**What the historical reality was.** `budgets.md` establishes Rokugan as **labor-limited, not land-limited**: ~15% arable, ~4% rice-suitable, of which only ~1/3 is active wet paddy in any given year, leaving "large amounts of fallow land in every domain." This is a load-bearing setting fact and must not be contradicted. But the fallow is distributed by the intensity gradient: it sits at the edges of each settlement's catchment and on the poorer soils, because those are the fields not worth the walk. It does not sit in a ring hugging the town.

**Whether the proposed design matches it.** Yes, and this is the subtle point that makes densifying the near ring *more* faithful to the model, not less. The fallow still exists on the map - as the scrub/rough-grazing at the frame margins, as the occasional fallow/rotation plot inside the quilt, and as the implication beyond the off-map field edge. The feature moves the fallow to where the model actually puts it (the margins), rather than erasing it. A map that densified the near ring AND removed all fallow/scrub from the frame would violate this element; the design keeps the fallow, relocated.

**What determines the element in reality.** Labor supply against a fixed catchment: the number of farming households feeding the settlement can only work so much land, so the marginal ground goes fallow first - and the marginal ground is the far and the poor ground, by the same distance/quality logic as Element 1.

### Element 3: The dense near ring is a quilt (paddy + dry fields + gardens + fallow minority), not a paddy monoculture

**What the historical reality was.** Intensive East-Asian near-settlement agriculture was polycultural and vertically organized by micro-topography: wet paddy on the flat, waterable ground; dryland fields (soybean, azuki, barley/wheat aftercrop, the other Five Grains) on the drier and slightly higher ground, whose runoff and household fertilizer cycling renewed the paddies; kitchen/market gardens (vegetables, intensively manured) close against the dwellings; and a minority of ground in fallow or rotation. `budgets.md` makes this explicit: of the rice-suitable land only ~1/3 is wet paddy, the rest being "hillside soybean and azuki fields... the dryland fields for aftercrops and other Five Grains... the small share of upland-rice rotation, and the labor-fallow margins." The existing engine already encodes a piece of this as the "~1 in 6 plots is a dry/hedge crop" convention (`settlements.md`, Fields).

**Whether the proposed design matches it.** Yes. The densified near ring is specified as a quilt (FR-003), not wall-to-wall rice: the existing paddy combs stay, and the densification is carried substantially by dry-field plots + gardens + a fallow minority - which is both historically the correct land-use for intensification (the dryland supporting crops) and the component that does NOT require an irrigation channel, so it can fill flat ground the combs do not reach without inventing implausible water. Wall-to-wall paddy would violate this element.

**What determines the element in reality.** Micro-topography and water: the wettest flat ground is paddy, the drier/higher-but-still-flat ground is dry field, the ground against the houses is garden, and the least-worth-working ground is fallow. This is why the fill must be topography-aware (Element 4), not a uniform green wash.

### Element 4: Topography still governs - no paddy on slopes

**What the historical reality was.** Wet paddy requires flat, bunded, waterable ground; it cannot sit on an ordinary hill slope without terracing, and terracing is a specific, labor-expensive response chosen when flat land runs out, not the default around a well-sited lowland town. Slopes in the near ring carried dry fields, tree crops (tea, tung, tea-oil), managed woodland/coppice, or scrub - never open flooded paddy. The engine already forbids paddy on hills (`settlements.md`, Fields: "No paddy on hills... Hills carry grass, woods, and shrines only").

**Whether the proposed design matches it.** Yes. Densification targets only the flat, waterable ground; hills in-frame keep their slopes in dry fields / tea / woodland / scrub (FR-004). The near-ring fill must be topography-aware and must not place paddy (or, on steep ground, any field) on a hill slope.

**What determines the element in reality.** Slope and water table: flat + waterable = paddy-capable; sloped = dry crops / tree crops / woodland / scrub.

### Calibrated liberty (Principle XII, 2026-07-19 clause) - the DEGREE of near-ring density

The three conditions for calibrated liberty hold, so a favorable reading is chosen deliberately and disclosed here and (at implementation) beside the rule in code:

1. **Plausibly true**: that a well-sited settlement's near ring was intensively cultivated is well supported (site selection + von Thünen + the Chinese "intensify existing fields" preference).
2. **Degree genuinely unclear / region-dependent**: the exact fraction of the near ring under cultivation varied by region, period, terrain, and how prosperous the locale was. There is no single historical number for "percent of the half-mile around a county seat that was cultivated," and Rokugan is explicitly a labor-limited economy with slack.
3. **A particular reading serves the project's goals**: reading the near ring as *densely* cultivated (rather than middling) makes the town/city maps read as embedded in farmland, which is the GM's stated goal and improves legibility and the sense of place.

**The chosen reading and its range.** The dense default targets a near ring that reads as predominantly cultivated - roughly, the majority of flat, non-settlement, non-water, non-hill ground within the frame is field/farmstead/garden rather than scrub. The plausible range runs from "middling" (a genuine mix of cultivated and rough ground, appropriate to a dry or marginal locale) to "near-saturated" (almost no rough ground on the flat, appropriate to a rich, populous basin). We pick the dense end as the DEFAULT for a well-sited town and expose a knob to dial toward the middling/thin end for a deliberately marginal one (Element 5) - so the liberty is a default, not a hard-coded universal, and the range itself is represented in the product.

### Element 5: Tunability is itself historically grounded

Not every town sits on prime bottomland. A dry rain-shadow locale (the setting already models this with pond-fed *tameike* villages like Kikuta) or a marginal/frontier domain genuinely had a thinner, scrubbier surround. So the intensity is a per-map knob defaulting to dense (well-sited) and dialable down (FR-005). This is not a hedge; it is the honest representation of the plausible range from the calibrated-liberty clause, and it prevents the over-correction of forcing every town into one packed look (which would itself be unhistorical).

### Grounding that would REJECT a design (recorded so a future pass does not reinvent it)

- **Rejected: "delete the scrub / make the whole frame farmland."** This would contradict Element 2 (the labor-limited fallow is real and must appear) and Element 4 (slopes and the wet toe are not farmland). Scrub stays; it is relocated, not removed.
- **Rejected: "fill the near ring with more wet paddy."** This would contradict Element 3 (monoculture) and Element 4 (paddy needs flat waterable ground and cannot go everywhere), and would force implausible water sources for every new field (each paddy needs a visible water source per the engine's own rule). The intensification is carried by dry fields + gardens + fallow, with paddy only where water and flat ground already justify it.
- **Rejected: "one global density for all towns."** Contradicts Element 5 and the calibrated-liberty range.

## Part B - Mechanism decision

An engine-lever recon (read-only, over `settlement.py`, `waterfields.py`, `check_village.py`, `settlements.md`, and the four town/city gens) settled the following facts that constrain the mechanism:

- **Fields are 100% per-gen hand-authored** `build_comb` water-first paddy fans; there is no engine auto field-generation, and every paddy fan needs a hand-wired water source and a drain that reaches a sink (`fields_show_water_source`, `check_village.py:5572`). Auto-generating valid paddy is therefore not in-grain and not attempted.
- **Dry cropland is the water-source escape hatch.** `fields_show_water_source` is scoped to `kind=="paddy"`; dry hem plots (`_dry_fields`, `waterfields.py:990`) live in `M["dry_plots"]` and vegetable tracts (Tango's per-gen `veg_tract`) are `kind="vegetable"` - both are structurally exempt from every water-source / moat-irrigation / paddy-farmstead-density requirement, need no channel/sluice/drain, and are already protected as no-build cropland via `s.dry_polys` (`structures_clear_of_dry_plots`, `groves_clear_of_dry_plots`).
- **Towns/cities hand-place their scrub** via `s.commons([...])` polys (only hamlets/villages call `hinterland()`); reducing near-ring scrub is just drawing fewer/smaller commons polys at the frame margins - but the vacated ground must then be clothed by *something*, because the grid-sampled coverage checks (`town_margins_clothed` <=20% bare, `check_village.py:5412`; `margins_form_continuous_ring` <=12% bare) count fields/dry_plots/gardens as valid cover. This is the feature's opening: replace near-ring scrub with cultivated cover.
- **A "not-hill" predicate already exists**: `in_ellipse(x, y, M["hill"], 1.45)` is used as the inflated hill keep-out in `town_margins_clothed`; the wet toe/marsh and watercourses are registered `block_polys`; the 30-ft urban halo is `_urban_keepouts`. So "flat, waterable, non-settlement near-ring ground" is derivable as the frame complement of those, exactly as the existing coverage checks already sample it.
- **A cultivated-fraction check is a near-verbatim clone** of the `town_margins_clothed` grid-sampler, restricted to the near-ring annulus and counting only *cultivated* cover.
- **Farmstead caps do not block densification**: `town_farmers_plurality` is only helped by more farmhouses, and the density checks are floors. At **town** scale added farmhouses count toward the depicted population (so a large increase needs the declared `population` re-reconciled); at **city** scale farmhouses do not count toward the figure (free to ring densely).
- **Per-map tuning is a `meta()` kwarg** read via `meta.get(...)` (the established pattern, cf. `agricultural_district`, `wall_defense`), not a rolled `Knob`.

### Decision: Mechanism C (hybrid) - engine-tiled dry/garden near-ring fill; paddy stays hand-authored

**Decision.** Add one parametric, channel-free `Settlement` method that tiles **dry-field + garden** cropland over the auto-derived flat near-ring band (frame, within the near ring, minus the inflated hill, the wet toe/marsh, watercourses, and the urban halo), recording into `M["dry_plots"]` + `s.dry_polys`. Keep **paddy** strictly per-gen hand-authored (the water-anchored, seed-swept part). Gate the fill intensity on a new `meta(near_ring_density=<tier>)` kwarg defaulting to dense. Add a `near_ring_cultivated_fraction` coverage check (a restricted clone of `town_margins_clothed`) that requires the flat near-ring to be predominantly cultivated at the dense default and permits a thinner ring when dialed down, with a saved sparse negative regression fixture. Redesign the motivating maps (Hirameki town, Tango city) to drop their near-ring `s.commons` polys and call the new fill, and sweep the whole pool.

**Rationale.** This satisfies every Principle XII element (Part A): the dry/garden fill IS the historically correct intensification component (the dryland supporting crops + market gardens), it needs no invented water (escape hatch), it is topography-aware via the ready-made hill/water/urban keep-outs (Element 4), it leaves paddy where the hydrology is already right (Element 3, quilt), and it is tunable (Element 5). It reuses primitives that already exist (`_dry_fields`/`veg_tract` tiling, `dry_polys` no-build, `_urban_keepouts`, the `in_ellipse(...,1.45)` not-hill test, the coverage-check grid-sampler, the dry-plot water exemption), so it touches shared engine code once and lets the existing validator gate turn every pool map into a checked downstream artifact - exactly the codebase idiom.

**Fallow is represented by the sub-100% threshold, not a new glyph.** Rather than invent a fallow-plot mechanism (the recon confirms none exists, and `land_use_overlay` deliberately rejects rotation semantics under Principle XII), "the fallow minority" is represented by (a) the cultivated-fraction threshold being a strong majority rather than 100%, leaving room for genuine rough/fallow patches, and (b) the existing "~1 in 6 dry plots" crop variety. This keeps the near ring a quilt (Element 3) and the labor-limited fallow visible (Element 2) with zero new drawing vocabulary and zero Principle XII rotation risk.

**Alternatives considered.**
- *Mechanism A (engine auto-tiles everything including trying to place paddy)*: rejected - auto-generating valid water-first combs is not feasible in-grain (seed-swept hydrology) and would risk implausible water (a Part A rejection).
- *Mechanism B (pure per-gen authoring, no engine method, doctrine + check only)*: rejected as the primary path - it pays the full hand-authoring cost on every existing and future map and each paddy fan needs bespoke water; it also most directly collides with the `settlements.md:195` "representative sample" doctrine. (Its check half is retained; only its "no engine method" stance is rejected.)

**One doctrinal revision to make (flagged for the GM).** `settlements.md:195` currently reads "We do not draw all the farmland. A town's fields are a representative sample; the rest is implied off-map." Mechanism C narrows this for the **near ring** specifically: the near-ring flat ground now reads as packed cultivation, while the *far* countryside is still implied off-map (and at least one field still runs off the edge per FR-008). The doctrine line will be revised to say exactly that. This is the natural consequence of the feature and is called out here so it is a conscious change, not a silent contradiction.
