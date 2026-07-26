# Fields: the research behind the paddy, plot and crop rules

*The research behind the rules in [`../settlements/fields.md`](../settlements/fields.md). Findings, anchors and disclosed departures live here so the rule file stays operational; this file is where citations and deeper historical context get added as they accumulate.*

**Load this file when:** you are changing a field rule, a plot size, a crop ratio or a check threshold - or you want the historical basis before overriding one. Not needed to simply DRAW a field from the rules file.

Every entry: what the research found, the decision it drove, and any deliberate departure from literal reality. Anchors are stable - rules link to them by `#slug`.

---

## In-field features - flat flooded paddy hosts obstacles least

**Grounds:** `paddy_features_match_archetype`, `field_ponds_on_low_ground`

- *What the research found.* Flat, flooded valley-bottom paddy is the archetype that hosts non-rice obstacles LEAST - it is the most valuable, most intensively worked, and wet. Grave mounds and feng-shui knolls are MARGIN/slope features in the rice south (feng-shui wants a backing hill + downslope water view, so the dead go on the slope, not the wet center); rock outcrops are a TERRACE feature (bedrock the risers wrap around) and are absent on alluvial valley/polder and delta dike-pond; small OPEN-WATER ponds (a low pocket / header tameike / half-moon by a hall) are the one thing that genuinely belongs in the wet middle. The per-archetype matrix (research.md) is encoded in `_PADDY_POND_KINDS` / `_PADDY_ROCK_KINDS` / `_PADDY_GRAVE_KINDS` and enforced by `paddy_features_match_archetype`.

- *CALIBRATED LIBERTY (GM 2026-07-20, disclosed).* The in-field grave ISLAND (the "graves among the paddy" look) is a north-China-dry-plain / Japanese-corroborated signature, NOT the rice-south default (which is margin/slope). The GM approved "both", so it is drawn rarely (~30% on valley/terraces/ribbon) as a deliberate departure, recorded here and in research.md D1, not an oversight.

## Paddy plots - irregular patchwork, and why the grid is anachronistic

**Grounds:** `_paddy_plots`, the `plot` grain

Pre-modern paddies were fitted to the land and water by piecemeal reclamation and inheritance, so plots are odd-sized and odd-shaped with bunds meeting at **T-junctions**; the tidy rectangular grid is a **modern (Meiji/Showa) land-consolidation (*kochi seiri*) artifact** and reads as anachronistic.

What the research found: what separated real paddies was the *aze* (China: *tiangeng*) - a puddled-mud ridge roughly 1-2 ft wide and ~1 ft high, re-plastered each spring (*azenuri*) so each basin holds its 4-6 inches of water; the walking bunds (*azemichi*) ran ~2-5 ft.

## Nitrogen - a flooded paddy makes its own

**Grounds:** the ~6% soy share; azemame as a food crop

- *Nitrogen - the paddy makes its OWN, so soy is food not fertiliser.* A flooded paddy is near self-sustaining for nitrogen: the standing water hosts N-fixing **cyanobacteria + *azolla*** and the **irrigation water carries in silt/nutrients** from upstream - which is why paddies crop continuously for centuries where dry-field monoculture exhausts the soil. Legumes entered as **winter green manure grown IN the drained paddy** (*renge* / Chinese milk vetch, plowed under before spring flooding) + applied night soil / ash / fish-and-oilseed cake - NOT soy on the margins washing in. So the ~6% soy is a **food crop** (dry fields, and characteristically on the paddy bunds - *aze-mame*, "ridge beans"), NOT the paddy's nitrogen supply.

## Why ruled rows waited for Meiji

**Grounds:** `_paddy_surface` (no ruled rows on a wet paddy)

- *WHY rows waited for Meiji when row planting is ancient (GM 2026-07-23 - the idea was never the bottleneck, the economics were).* Dry-crop rows are FREE: the seed goes into a plowed furrow, and the furrow IS the row. Wet rice is TRANSPLANTED into a puddled flooded sheet with no furrows and no guide lines, so rows must be PURCHASED - marked ropes or a rolled gridding frame, plus every planter aligning to them - and the bill lands in the year's tightest labor window (the whole village transplants in days, on a shared water schedule). And for centuries the purchase bought nothing: rows pay when a tool travels BETWEEN them (the ancient dry-field hoe/cultivator), but nothing could travel between rows in a flooded paddy - weeding was by hand and foot either way. What changed in Meiji was the arrival of the between-rows tool for mud: the hand-pushed ROTARY PADDY WEEDER, which only works on plants ruled in both directions - so *seijoue* + marking frame + rotary weeder spread as ONE package, pushed by state extension hard enough that police sometimes stood over farmers to enforce straight lines ("saber farming"), itself evidence the private payoff was marginal before the full package. Traditional transplanting was NOT chaos though: clump spacing was roughly even (a practiced hand keeps density consistent - density drives yield), just never ruled - which is exactly what the sparse unruled shoot-mottle renders.

## Water-first v2 - pond, distribution and the three layout modes

**Grounds:** `waterfields.py`; `build_comb` / `build_terraces` / `build_ribbon`

- **Pond**: a valley-head *tameike* behind an earthen dike, sitting ABOVE its fields ("located at a valley head and constructed by dividing off the valley mouth with an earthen dike... at elevations higher than the surface of the paddy fields they serve" - Tabayashi 1986, Geographical Review of Japan 60(1)). ONE outlet: an inclined intake (shahi) feeding a bottom conduit (sokohi) through the dam; the spillway is flood-safety, never distribution (Kagawa pref. tameike docs). Parent/child pond linkage (oyaike/koike, Kagawa; "melon-on-the-vine" in China) is attested flavor for larger systems.
   - **Distribution**: sluice -> head-race -> division point (bunsuiguchi) -> a branching TREE. "Main canals **gradually decrease in size as they are tapped by branch canals**" (Tabayashi) - hence the drawn taper. The smallest ditches "are often considered parts of the paddy fields they serve" - hence ditch-as-plot-boundary. SPARSE is correct: a village digs the minimum network; a ditch beside every paddy (yohaisui bunri) is a Meiji land-readjustment (1899/1905) anachronism.
   - **Layout modes** (terrain-driven; the GM wants all three eventually):
     - **COMB (the default)**: supply canals along the HIGH margins, delivery ditches perpendicular down-slope, one drain along the low line. Grounding: the Edo Kishu-school layout (Minuma-dai 1728: supply on the elevated margins, drainage channel on the lowest line, water reused downstream) AND codified Chinese canal doctrine (mains along contours/ridges on high ground, field channels perpendicular to contours). Chinese *beitang* pond systems - the direct tameike analogue - were THE dominant village-scale mode in rice China (8.3M ponds serving ~39% of irrigated area into the 1950s, ~71% in hilly regions); the GM chose the Chinese default deliberately (Rokugan demographics anchor to Song/Ming China).
     - **FAN (supported option, not default)**: gently-descending canals radiating from a valley-mouth apex - the Dujiangyan / Tedori-alluvial-fan geometry. Correct where the land fans out below the pond.
     - **JORI GRID (future option, recorded on GM request - NOT implemented)**: from the 7th century much of Japan's long-settled PLAINS carried an astronomically-oriented 109 m grid (jori-sei: 1-cho squares in 6x6-ri blocks, cut into ~12 x 109 m tan strips). A plains village in an ancient core province shows semi-regular GRIDDED paddies, not organic patchwork - Rokugan analog: ancient heartland provinces (e.g. Crane/Phoenix cores). The organic warp-thread patchwork is correct for terrain-following villages like Kikuta.

## Plot sizes, pond sizing and acreage from population

**Grounds:** the v2 carve targets

- **Plots**: pre-modern 0.02-0.25 acre, irregular; v2 carves ~0.1-0.15 acre, ~9 scattered plots per household (fragmented holdings were normal). STRAIGHT rectangular channels/plots are post-1900 consolidation (the Tedori fan's ditches were only straightened in the early 1900s) - the organic waver is period-correct, do not "clean it up".

- **Pond sizing (the rule)**: sole-storage tameike run ~2,000-2,500 m3 of storage per irrigated ha (typical depth 2-4 m); a STREAM-FED pond refilling 1-2x a season is comfortable at ~1,200-1,500 m3/ha. Hoshigaoka: 31.8 ha of paddy -> ~1.5 ha pond surface (rx=145, ry=92 px at 1px=2ft) ~ 47,000 m3 at ~3 m ~ 1,470 m3/ha + feeder stream. The first draft's 0.84 ha pond (~790 m3/ha) was honestly undersized - keep pond area proportional to command area.

- **Acreage from population (the sizing rule)**: a person eats ~1 koku/yr; pre-modern yield ~1.3 koku/tan; coarse grain fills part of the diet while ~45% of rice goes to tax -> ~0.8-1.0 tan gross paddy per person -> 350 people ~ 280-350 tan = **69-86 acres** (+ dry margins later). WIP Kikuta lands ~79 acres / ~600 plots.

## Where dry (hatake) crops go - the topographic catena

**Grounds:** the `dry_band` knob

WHERE dry crops go: wet-rice villages sort by a topographic CATENA - irrigated paddy holds the flat valley bottom / plain; DRY fields (hatake) take the HIGHER, well-drained ground the water cannot command (river terraces, natural levees / micro-highs threading the plain, alluvial-fan edges, lower slopes, AND the slightly-raised ground the homesteads sit on); coppice woodland (satoyama) crowns the hills above. Sources: satoyama land-use literature ("wet-rice in the plains and valley bottoms... satoyama woodlands/grasslands for dry-field crops"; "large middle river terraces... large areas of crop fields and small areas of paddy"); Kanto-plain historical-GIS land-use studies. So dry fields are NOT one neat strip - historically they sit in SEVERAL positions, above all AROUND the houses ("each family has some paddy and some hatake", the household's dry plots near its home).

## Free lore hooks, and the sources

**Grounds:** /law, /calendar, village detail

- **Free lore hooks from the sources** (for /law, /calendar, village details): drought rotation in fixed village turns; water-heads (mizugashira) elected to run the flow; supply turns timed by BURNING INCENSE STICKS (senkomizu); upstream villages leveraging position in water disputes; a village trading pond-management duty for water rights.
   - Sources: Tabayashi 1986 (jstage grj1984b/60/1), Kagawa pref. tameike structure pages, JSIDRE on Minuma-dai, MAFF agricultural-water history PDF, Shiroyone terraced-paddies (NIES), jori-sei (Japanese Wiki Corpus + Tsukuba field-trace surveys), beitang studies (Nature Comms 2023; Jiang-Huai pond irrigation, PMC6695888), Chinese canal-layout doctrine (灌溉渠道 refs).
