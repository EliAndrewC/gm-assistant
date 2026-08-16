# Fields: the research behind the paddy, plot and crop rules

*The research behind the rules in [`../settlements/fields.md`](../settlements/fields.md). Findings, anchors and disclosed departures live here so the rule file stays operational; this file is where citations and deeper historical context get added as they accumulate.*

**Load this file when:** you are changing a field rule, a plot size, a crop ratio or a check threshold - or you want the historical basis before overriding one. Not needed to simply DRAW a field from the rules file.

Every entry: what the research found, the decision it drove, and any deliberate departure from literal reality. Anchors are stable - rules link to them by `#slug`.

---

## In-field features - flat flooded paddy hosts obstacles least

**Grounds:** `paddy_features_match_archetype`, `field_ponds_on_low_ground`

**Evidence:** corroborated, liberty

**Sources:** not recorded - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

- *What the research found.* Flat, flooded valley-bottom paddy is the archetype that hosts non-rice obstacles LEAST - it is the most valuable, most intensively worked, and wet. Grave mounds and feng-shui knolls are MARGIN/slope features in the rice south (feng-shui wants a backing hill + downslope water view, so the dead go on the slope, not the wet center); rock outcrops are a TERRACE feature (bedrock the risers wrap around) and are absent on alluvial valley/polder and delta dike-pond; small OPEN-WATER ponds (a low pocket / header tameike / half-moon by a hall) are the one thing that genuinely belongs in the wet middle. The per-archetype matrix (research.md) is encoded in `_PADDY_POND_KINDS` / `_PADDY_ROCK_KINDS` / `_PADDY_GRAVE_KINDS` and enforced by `paddy_features_match_archetype`.

- *CALIBRATED LIBERTY (GM 2026-07-20, disclosed).* The in-field grave ISLAND (the "graves among the paddy" look) is a north-China-dry-plain / Japanese-corroborated signature, NOT the rice-south default (which is margin/slope). The GM approved "both", so it is drawn rarely (~30% on valley/terraces/ribbon) as a deliberate departure, recorded here and in research.md D1, not an oversight.

## Paddy plots - irregular patchwork, and why the grid is anachronistic

**Grounds:** `_paddy_plots`, the `plot` grain

**Evidence:** attested

**Sources:** not recorded - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

Pre-modern paddies were fitted to the land and water by piecemeal reclamation and inheritance, so plots are odd-sized and odd-shaped with bunds meeting at **T-junctions**; the tidy rectangular grid is a **modern (Meiji/Showa) land-consolidation (*kochi seiri*) artifact** and reads as anachronistic.

What the research found: what separated real paddies was the *aze* (China: *tiangeng*) - a puddled-mud ridge roughly 1-2 ft wide and ~1 ft high, re-plastered each spring (*azenuri*) so each basin holds its 4-6 inches of water; the walking bunds (*azemichi*) ran ~2-5 ft.

### Bunds are SHARED, and the fabric is continuous

**Grounds:** `paddy_plot_seams_shared`; `waterfields/seams.py::close_seams`

**Evidence:** follows from the *aze*'s construction and maintenance, above

*What the research found.* The *aze* is the wall BETWEEN two basins, and it is built once. Three
things make a second, parallel ridge with a strip of ground between it and the first impossible in
practice. It doubles the *azenuri* - the spring re-plastering, the single largest maintenance job
the bund network carries - for no gain. It holds no water: neither basin's rim is improved by a
wall standing off in the middle of a strip. And the strip itself is idle land inside an irrigated
command area, which is the most valuable ground on the map - the same land hunger that keeps field
margins down to one scythe swath (`research/vegetation.md`) does not tolerate a few feet of bare
mud between two paddies. What real paddy fabric looks like is therefore ONE connected bund network
whose lines meet at **T-junctions**; a free-standing four-sided ring inside it is not a paddy at
all. The odd, piecemeal parcels that fabric produces are the honest look - and note that the
detached, individually-walled rectangle is exactly the *kochi seiri* read this section already
flags as anachronistic, arrived at from the other direction.

*The decision it drove (GM 2026-08-17, on Inashiro:* "a tiny little standalone rectangle of earthen
walls is just smack dab in the middle of where the field should be ... it should basically always
be the case that two adjacent rice paddies share a single earthen wall rather than two different
earthen walls"*).* Two halves. **Generation**: `waterfields/seams.py::close_seams` replaced the
wedge filler. It takes the bare ground exactly as the carve left it - the command area, minus
everything planted, minus the drawn channels and their banks - then PLANTS every pocket wide enough
to hold a basin (so the new basin's outline IS the surrounding bunds) and ABSORBS every pocket too
thin to plant into the neighbour it shares the most bund with (so the two walls become one). Its
postcondition is that no square foot inside the command area is bare. **Checking**:
`paddy_plot_seams_shared` fails a plot that runs a bund alongside a neighbour's across dry floor,
or that draws a whole ring inside a neighbouring basin.

*Disclosed departures.* (1) A **shallow lap** is left alone, in both halves: a plot drawn over part
of its neighbour paints out the bund it covers, so the pair still reads as one shared wall. Only
near-containment is a fault. (2) The rule's upper bound is 24 real ft of gap - wider than that the
ground between two basins is bare FLOOR, which is `paddy_fan_gapless`'s rule, and stating it twice
at two tolerances is how checks start disagreeing. (3) A pocket **too thin to bund** is absorbed
rather than planted, matching the fan toe's existing thickness rule (`_TOE_MIN_THICKNESS`) - a
needle basin cannot be leveled or bunded at any sane cost.

## Nitrogen - a flooded paddy makes its own

**Grounds:** the ~6% soy share; azemame as a food crop

**Evidence:** attested

**Sources:** not recorded - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

- *Nitrogen - the paddy makes its OWN, so soy is food not fertiliser.* A flooded paddy is near self-sustaining for nitrogen: the standing water hosts N-fixing **cyanobacteria + *azolla*** and the **irrigation water carries in silt/nutrients** from upstream - which is why paddies crop continuously for centuries where dry-field monoculture exhausts the soil. Legumes entered as **winter green manure grown IN the drained paddy** (*renge* / Chinese milk vetch, plowed under before spring flooding) + applied night soil / ash / fish-and-oilseed cake - NOT soy on the margins washing in. So the ~6% soy is a **food crop** (dry fields, and characteristically on the paddy bunds - *aze-mame*, "ridge beans"), NOT the paddy's nitrogen supply.

## Why ruled rows waited for Meiji

**Grounds:** `_paddy_surface` (no ruled rows on a wet paddy)

**Evidence:** attested

**Sources:** not recorded - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

- *WHY rows waited for Meiji when row planting is ancient (GM 2026-07-23 - the idea was never the bottleneck, the economics were).* Dry-crop rows are FREE: the seed goes into a plowed furrow, and the furrow IS the row. Wet rice is TRANSPLANTED into a puddled flooded sheet with no furrows and no guide lines, so rows must be PURCHASED - marked ropes or a rolled gridding frame, plus every planter aligning to them - and the bill lands in the year's tightest labor window (the whole village transplants in days, on a shared water schedule). And for centuries the purchase bought nothing: rows pay when a tool travels BETWEEN them (the ancient dry-field hoe/cultivator), but nothing could travel between rows in a flooded paddy - weeding was by hand and foot either way. What changed in Meiji was the arrival of the between-rows tool for mud: the hand-pushed ROTARY PADDY WEEDER, which only works on plants ruled in both directions - so *seijoue* + marking frame + rotary weeder spread as ONE package, pushed by state extension hard enough that police sometimes stood over farmers to enforce straight lines ("saber farming"), itself evidence the private payoff was marginal before the full package. Traditional transplanting was NOT chaos though: clump spacing was roughly even (a practiced hand keeps density consistent - density drives yield), just never ruled - which is exactly what the sparse unruled shoot-mottle renders.

## Water-first v2 - pond, distribution and the three layout modes

**Grounds:** `waterfields.py`; `build_comb` / `build_terraces` / `build_ribbon`

**Evidence:** attested, corroborated

**Sources:** [`tabayashi-1986`](SOURCES.md#tabayashi-1986), [`kagawa-tameike`](SOURCES.md#kagawa-tameike), [`jsidre-minumadai`](SOURCES.md#jsidre-minumadai), [`japanese-wiki-corpus`](SOURCES.md#japanese-wiki-corpus), [`beitang-studies`](SOURCES.md#beitang-studies)

- **Pond**: a valley-head *tameike* behind an earthen dike, sitting ABOVE its fields ("located at a valley head and constructed by dividing off the valley mouth with an earthen dike... at elevations higher than the surface of the paddy fields they serve" - Tabayashi 1986, Geographical Review of Japan 60(1)). ONE outlet: an inclined intake (shahi) feeding a bottom conduit (sokohi) through the dam; the spillway is flood-safety, never distribution (Kagawa pref. tameike docs). Parent/child pond linkage (oyaike/koike, Kagawa; "melon-on-the-vine" in China) is attested flavor for larger systems.
   - **Distribution**: sluice -> head-race -> division point (bunsuiguchi) -> a branching TREE. "Main canals **gradually decrease in size as they are tapped by branch canals**" (Tabayashi) - hence the drawn taper. The smallest ditches "are often considered parts of the paddy fields they serve" - hence ditch-as-plot-boundary. SPARSE is correct: a village digs the minimum network; a ditch beside every paddy (yohaisui bunri) is a Meiji land-readjustment (1899/1905) anachronism.
   - **Layout modes** (terrain-driven; the GM wants all three eventually):
     - **COMB (the default)**: supply canals along the HIGH margins, delivery ditches perpendicular down-slope, one drain along the low line. Grounding: the Edo Kishu-school layout (Minuma-dai 1728: supply on the elevated margins, drainage channel on the lowest line, water reused downstream) AND codified Chinese canal doctrine (mains along contours/ridges on high ground, field channels perpendicular to contours). Chinese *beitang* pond systems - the direct tameike analogue - were THE dominant village-scale mode in rice China (8.3M ponds serving ~39% of irrigated area into the 1950s, ~71% in hilly regions); the GM chose the Chinese default deliberately (Rokugan demographics anchor to Song/Ming China).
     - **FAN (supported option, not default)**: gently-descending canals radiating from a valley-mouth apex - the Dujiangyan / Tedori-alluvial-fan geometry. Correct where the land fans out below the pond.
     - **JORI GRID (future option, recorded on GM request - NOT implemented)**: from the 7th century much of Japan's long-settled PLAINS carried an astronomically-oriented 109 m grid (jori-sei: 1-cho squares in 6x6-ri blocks, cut into ~12 x 109 m tan strips). A plains village in an ancient core province shows semi-regular GRIDDED paddies, not organic patchwork - Rokugan analog: ancient heartland provinces (e.g. Crane/Phoenix cores). The organic warp-thread patchwork is correct for terrain-following villages like Kikuta.

## Plot sizes, pond sizing and acreage from population

**Grounds:** the v2 carve targets

**Evidence:** researched

**Sources:** not recorded - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

- **Plots**: pre-modern 0.02-0.25 acre, irregular; v2 carves ~0.1-0.15 acre, ~9 scattered plots per household (fragmented holdings were normal). STRAIGHT rectangular channels/plots are post-1900 consolidation (the Tedori fan's ditches were only straightened in the early 1900s) - the organic waver is period-correct, do not "clean it up".

- **Pond sizing (the rule)**: sole-storage tameike run ~2,000-2,500 m3 of storage per irrigated ha (typical depth 2-4 m); a STREAM-FED pond refilling 1-2x a season is comfortable at ~1,200-1,500 m3/ha. Hoshigaoka: 31.8 ha of paddy -> ~1.5 ha pond surface (rx=145, ry=92 px at 1px=2ft) ~ 47,000 m3 at ~3 m ~ 1,470 m3/ha + feeder stream. The first draft's 0.84 ha pond (~790 m3/ha) was honestly undersized - keep pond area proportional to command area.

- **Acreage from population (the sizing rule)**: a person eats ~1 koku/yr; pre-modern yield ~1.3 koku/tan; coarse grain fills part of the diet while ~45% of rice goes to tax -> ~0.8-1.0 tan gross paddy per person -> 350 people ~ 280-350 tan = **69-86 acres** (+ dry margins later). WIP Kikuta lands ~79 acres / ~600 plots.

## Tract sizes - no settlement-class cap

**Grounds:** comb-fan sizing (`field_fall`) on every map tier; the pending town-paddy recalibration (GM 2026-08-02, decision open)

**Evidence:** researched

**Sources:** [`li-bozhong-jiangnan`](SOURCES.md#li-bozhong-jiangnan), [`skinner-marketing`](SOURCES.md#skinner-marketing), [`aric-land-history`](SOURCES.md#aric-land-history), [`mdpi-kunisaki`](SOURCES.md#mdpi-kunisaki), [`buck-survey`](SOURCES.md#buck-survey)

The PLOT question (one leveled cell, ~0.05 ac) is settled above; this entry is the layer above it - the TRACT: one contiguous field system (a comb fan, a terrace flight, a polder) and how much ground it commands. Asked by the GM 2026-08-02 after Hoshizora's west comb read as "extremely unusual": *what range of rice paddy sizes might we see in a mixed-use settlement - partially urban, partially pastoral grazing, partially food-growing farms?*

- *Per-household paddy (China first).* Mid-Qing Jiangnan farms averaged ~10 *mu* per farmer - Li Bozhong's "ten *mu* per farmer" - at the Ming-Qing *mu* of ~614 m2, so **~1.5 acres of intensively worked wet rice per farm household**; Buck's surveys corroborate that a holding was scattered over several parcels. Japan corroborates: the Edo average farm household held ~1 *cho* (~2.45 ac) TOTAL, paddy plus dry, putting its paddy share in the same ~1-1.5 ac. The working band: **~1-2.5 acres of paddy per farm household** - the same number the diet-side acreage-from-population rule above reaches independently (~0.8-1.0 *tan*/person x ~4.5-person households).

- *The communal-system floor.* A comb fan is communal waterworks - weir, head-race, canal fork, tapering deliveries, a drain collector. The smallest attested community systems are pond/tank-fed: small *tameike* systems run ~10 ha each (Kunisaki's Tsunai ward: 5 systems totaling 50 ha across 11 farmers), and traditional village tanks typically command tens of hectares, well under 200. Even a handful of cooperating households implies ~1.5 ac each, so **the floor for a system that justifies drawn head-race-and-collector infrastructure is roughly 3-8 ha (~8-20 ac) - exactly the hamlet tier**. Nobody builds a weir and a canal fork for 2 acres; ground that size is ONE household's holding, watered by a single ditch. The GM's framing is the right mental model: a hamlet IS a small paddy tract with farmhouses around it, and a hamlet-sized tract is the honest minimum for any fully-drawn fan, wherever it appears.

- *The town edge has NO tier of its own.* A market town / county seat is the CENTER of a farmed hinterland (Skinner: the standard marketing community is ~18 villages over ~300-500 km2), and cultivation historically pressed against the built edge - Chinese county seats with farmland to the walls and farmers walking out from town; Japanese post towns strung along highways through continuous paddy. Tract size is set by water, terrain, and mouths fed - never by settlement class. A mixed-use edge (urban core + hay/grazing + farms, the Hoshizora premise) legitimately carries anything from a hamlet-grade fan (~8-20 ac) where irrigable ground is short, through village-grade tracts (~50-90 ac), up to open farmland bounded only by the frame; the attested LOW end is terrain-limited (the upland Kiso post towns), and even there the limit is the terrain, not the town-ness. Small is legal where the map shows the terrain reason (hay country, forest, slope); tiny-with-full-waterworks is not attested anywhere.

- *What the pool draws today (audited 2026-08-02; shoelace area of each paddy `outline` x ftpx^2).* Hamlets 7.7-35.3 ac for 14-18 steadings (~0.5-2.2 ac/household - in-band). Villages 54.9-86.8 ac for 55-85 (~0.9-1.3 - in-band). Provincial cities 40.6-61.6 ac in 6-10 edge fans of 2.8-10.1 ac each, every fan visibly RUNNING OFF the frame - the truncation itself says "slice of a larger field", so the small on-frame acreage is honest. Towns are the outlier: Hoshizora 2.4 ac total against 45 depicted farmsteads, Ubame 4.0 against 35, Hirameki 8.2 against 73 - **0.05-0.11 ac per depicted farm household, 15-30x under the band; each town's whole drawn paddy is smaller than ONE real household's holding**. The cause is mechanical, not doctrinal: the town gens hand-cap `field_fall` at 145-320 px and hand-set `row_step=(52,72)` outside the `paddy_grain` lineage. The "town map shows a slice of the county's farmland" doctrine covers a fan that runs off-frame (hoshizora-ne, ubame-south do) but NOT an enclosed one - hoshizora-west is bounded by stream, road, monastery, and laborers' quarter on all four sides and therefore reads as a complete, absurdly small farm.

- *The decision (GM 2026-08-03).* The accidental town cap is dropped and the ladder is: **8 acres is the hard floor for any ENCLOSED fan** (one that does not run off the frame), reserved for mixed-use / terrain-limited maps that SHOW the reason there is no more irrigable ground (Hoshizora's relay hayfields + grazing + forest, `near_ring_density="thin"`); **~20 acres is the ordinary small end for a non-specialized town** - in practice drawn as a modest enclosed fan plus off-frame slices, since 20 enclosed acres at 1 ft/px is ~a third of a town canvas and a real town sits amid continuous farmland anyway; villages stay population-sized at ~50-90 ac; cities keep the off-frame slice convention. Off-frame slices stay exempt from the floor ON-MAP (the truncation says "more beyond"); the floor bites exactly where an enclosed fan reads as a complete system. An enclosed fan's own ring reads as ~1-2.5 ac/household for the steadings living off it; the rest of a town's depicted farmers read as working the off-frame fields, which is why `town_has_field_off_edge` matters on every town map. *Landed 2026-08-03:* the ring placer's road-severed filter + `farmsteads_reach_their_fields_unsevered` (hoshizora's lone south-of-road farmhouse is gone), and Tango's four offenders (fn1/fn2/fs1 as off-view slices, nw1 as the in-wall exemption). *Pending with the town recompositions* (the floor check itself waits in [`../pending-enclosed-fan-floor.md`](../pending-enclosed-fan-floor.md)): the three towns' fans, the town combs' `paddy_grain`/`grain=2` lineage move, and with it the bund-vs-drain stroke fix (the 1 ft/px bund and drain rendered at equal ~1.5 px weight because the town gens passed `grain=1` where the engine's docstring calls for `grain = 2/ftpx`).

## Where dry (hatake) crops go - the topographic catena

**Grounds:** the `dry_band` knob

**Evidence:** researched

**Sources:** not recorded - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

WHERE dry crops go: wet-rice villages sort by a topographic CATENA - irrigated paddy holds the flat valley bottom / plain; DRY fields (hatake) take the HIGHER, well-drained ground the water cannot command (river terraces, natural levees / micro-highs threading the plain, alluvial-fan edges, lower slopes, AND the slightly-raised ground the homesteads sit on); coppice woodland (satoyama) crowns the hills above. Sources: satoyama land-use literature ("wet-rice in the plains and valley bottoms... satoyama woodlands/grasslands for dry-field crops"; "large middle river terraces... large areas of crop fields and small areas of paddy"); Kanto-plain historical-GIS land-use studies. So dry fields are NOT one neat strip - historically they sit in SEVERAL positions, above all AROUND the houses ("each family has some paddy and some hatake", the household's dry plots near its home).

## Free lore hooks, and the sources

**Grounds:** /law, /calendar, village detail

**Evidence:** researched

**Sources:** [`tabayashi-1986`](SOURCES.md#tabayashi-1986), [`kagawa-tameike`](SOURCES.md#kagawa-tameike), [`jsidre-minumadai`](SOURCES.md#jsidre-minumadai), [`maff-water-history`](SOURCES.md#maff-water-history), [`nies-shiroyone`](SOURCES.md#nies-shiroyone), [`japanese-wiki-corpus`](SOURCES.md#japanese-wiki-corpus), [`beitang-studies`](SOURCES.md#beitang-studies)

- **Free lore hooks from the sources** (for /law, /calendar, village details): drought rotation in fixed village turns; water-heads (mizugashira) elected to run the flow; supply turns timed by BURNING INCENSE STICKS (senkomizu); upstream villages leveraging position in water disputes; a village trading pond-management duty for water rights.
   - Sources: Tabayashi 1986 (jstage grj1984b/60/1), Kagawa pref. tameike structure pages, JSIDRE on Minuma-dai, MAFF agricultural-water history PDF, Shiroyone terraced-paddies (NIES), jori-sei (Japanese Wiki Corpus + Tsukuba field-trace surveys), beitang studies (Nature Comms 2023; Jiang-Huai pond irrigation, PMC6695888), Chinese canal-layout doctrine (灌溉渠道 refs).
