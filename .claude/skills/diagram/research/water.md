# Water: the research behind the flow, channel and wetland rules

*The research behind the rules in [`../settlements/water.md`](../settlements/water.md). Findings, anchors and disclosed departures live here so the rule file stays operational; this file is where citations and deeper historical context get added as they accumulate.*

**Load this file when:** you are changing a water rule, a width, or a check threshold - or you want the historical basis before overriding one. Not needed to simply DRAW water from the rules file.

Every entry: what the research found, the decision it drove, and any deliberate departure from literal reality. Anchors are stable - rules link to them by `#slug`.

---

## Water-width ladder - the real-world tiers

**Grounds:** `irrigation_channels_hairline`, `watercourses_wider_than_ditches`, `moat_is_heaviest_watercourse`, `moat_dwarfs_ditches`

| Tier | Real width | x field-ditch (true) |
  |---|---|---|
  | Field ditch (waters one paddy) | ~0.3 m | 1x |
  | Distribution lateral | ~1 m | ~3x |
  | Village creek / brook (natural) | ~2 m | ~6x |
  | Main irrigation canal (*yosui*) | ~5 m | ~15x |
  | Town river | ~20 m | ~65x |
  | Provincial-city moat (Himeji-tier) | ~20-35 m | ~70-115x |
  | Grand-city moat (Osaka-tier) | ~75 m | ~250x |
  | *Tameike* pond (areal - draw as polygon) | ~150-200 m across | ~1.5-2x a paddy |

  Anchors: headwater streams cluster near ~0.32 m; Himeji's moats average ~20 m (max 34.5 m); Osaka's outer moat is ~70-90 m; *tameike* reservoirs run ~3-26 ha (~150-600 m across). A field ditch is **~1/300 of the 1-cho (~100 m) paddy it feeds** - at true scale a hairline, essentially invisible.

## A fed closed moat must drain - the physics and the precedent

**Grounds:** `city_moat_has_outfall`; Tango's SE outfall stream

- *The physics (the load-bearing "why").* Water balance at a stable level: `outflow = inflow + rain - evaporation - seepage`. With NO outlet, `outflow = 0` forces `inflow = evaporation + seepage`; a real perennial stream delivers far more than a moat's surface can evaporate or its bed can seep, so storage climbs and the moat **overtops its banks** - "the level just keeps rising" is not a steady state, it is flooding. (A stream's upstream profile is set by its own bed slope, not the pond it enters - raising the moat only backs water up a short distance at the mouth, it cannot lift the whole feeder, so you cannot absorb continuous inflow by "raising the stream too.") The terminal-pond regime is real but belongs to a **spring/rain-fed** moat in an **arid** climate where small diffuse input is balanced by evaporation; a wet rice climate (modest evaporation; a high water table and puddled paddies that seal seepage) cannot absorb a live stream, so a stream-fed moat there MUST shed the surplus through a channel.

- *What the research found (China first: Beijing's gated water-passes + the Forbidden City moat; Japan agreeing: Edo/Matsue jokamachi moats).* Flow-through was the standard, engineered deliberately. **Beijing** admitted water through gated wall passes, branched it into through-city rivers, and discharged SE to the Tonghui/Grand Canal; the **Forbidden City** moat is fed from the Jade Spring and "flows in from the NORTHWEST and discharges to the SE" - inlet one corner, outfall the diagonal. Flushing mattered for sanitation (a stagnant moat stank and bred summer fevers; the remedy was flow-through + annual dredging), for **storm drainage** (a city moat doubled as the flood sluice - a drain with no outfall is not a drain), for a fire-water reserve, and for irrigation offtake. The pond-like look is legitimately achieved by an **overflow weir/sluice** that holds a set level and sheds only the surplus (Beijing's gated behavior) - placid surface, real outlet underneath. A closed moat with a live feeder and no outlet is historically wrong.

## The diverted-stream moat is a historical type

**Grounds:** Tango's stream-fed ring

- *The diverted-stream moat is itself a historical type (GM asked whether Tango's arrangement - a stream seemingly turned into the moat, then resuming its course - was real, 2026-07-23).* It is, and commonly so: a dry-site Chinese seat dug its *hucheng he* by turning a nearby stream through the ring (the Forbidden City's NW-in / SE-out flush is the model Tango already encodes), and Japanese castle towns fed moats by the same river diversions (Edo turned the Hirakawa into its moat spiral). Two honesty notes, both deliberate: (1) **no relic of the stream's pre-diversion bed is drawn through the city** - after centuries of urban buildup the abandoned course is built over, so its absence is realistic, not an omission (do not "fix" this by threading an old channel through the blocks); (2) the ring splits the feeder's flow into two live arcs (west-about and east-about) that rejoin at the outfall, which is why irrigation taps on BOTH flanks can legitimately draw "with the current" (`moat_channels_flow_with_current`).

## One name per river - and why that is anti-historical

**Grounds:** prose, titles and notes wherever a river is named

*What the research found:* one-river-many-names was the NORM in the pre-modern world, in both reference cultures. China: the Yangtze never had a single pre-modern name - its course ran Tuotuo He / Tongtian He / Jinsha Jiang, then regionally Chuan Jiang (Sichuan) / Jing Jiang (Hubei) / Xunyang Jiang / Yangzi Jiang (originally only the Nanjing-Shanghai reach; modern standardization settled on Chang Jiang). Japan: per-stretch renaming was standard practice - the Chikuma-gawa becomes the Shinano-gawa at the Shinano/Echigo provincial border, the Seta/Uji/Yodo system renames at each confluence, and within Edo itself one river carried different names neighborhood by neighborhood (Asakusa-gawa / Ryogoku-gawa / Okawa / Sumida-gawa, all the same water). The mechanism: pre-modern river names were LOCAL - people named the reach they lived on and used, and nobody needed a whole-course name because nobody administered or traveled the whole course; names broke at both political borders and confluences. One-name-per-river is a modern bureaucratic artifact (national mapping agencies, Japan's 1896/1964 River Laws, the PRC settling on Chang Jiang).

## Marsh - wet rice is reclaimed FROM wetland

**Grounds:** `s.marsh(poly)`, `marsh_on_low_ground`

This is grounded in the fact that **wet rice is reclaimed FROM marsh**: the lower-Yangzi / Tai-Lake paddies are embanked **polders (圩田/围田)** diked out into marsh and lake, and where reclamation stops (or the ground is too wet to manage) it *stays* reed wetland (abandoned paddy reverts to marsh).

Sources: rice domesticated in "naturally marshy areas" + paddy-as-reclaimed-marsh (AAS "Rice, Technology, and History"); Tai-Lake polders diked from marsh/lake; abandoned paddies revert to wetland.

## No toe marsh at town/city scale - the drainage-investment gradient

**Grounds:** village/hamlet gens draw a toe marsh; town/city gens draw none

*What the research found:* the real pattern is a **gradient of drainage investment and land value**. VILLAGES had neither the capital nor the incentive to eliminate every wet margin: residual wet ground at the low edge of village land is very well attested (Japanese *yatsuda* valley-bottom paddies were essentially managed marsh; reed beds were harvested village commons under *iriai* tenure - thatch, screens, annual burning; poorly drained *fukada* "deep fields" persisted until Meiji-and-later drainage projects), and crucially it was USED wet ground - reed bed, wet meadow, more paddy at the reclamation frontier - which is exactly what our sparse harvestable-reed rendering reads as. TOWNS/CITIES commanded corvee-scale hydraulic engineering and premium peri-urban land: ditch discharge went into an engineered moat/canal/river network (Suzhou's canal grid; Edo's canals and the immediate infill of the Hibiya inlet after 1590), and the outskirts were intensively worked (suburban vegetable belts fed by urban night soil; Edo-period reclamation waves around Osaka and Edo). Where wetness DID persist near a city it was **bounded and purposed** - a moat, a lotus/fish pond, a flood basin, a deliberate defensive inundation - never a diffuse seepage marsh below a ditch.

## Defensive marshland - the engineered wet belt

**Grounds:** `marsh(poly, role="defense")`, `defense_marsh_girds_the_walls`

*What the research found:* the Northern Song built an artificial marsh-and-pond belt across the northern Hebei frontier (from 989, He Chengju's lake chain) specifically as anti-cavalry terrain; Japanese *numajiro* "marsh castles" (Bitchu Takamatsu, besieged by water 1582) used surrounding marsh as their primary defense; and flooded paddies around castle towns functioned as a de facto glacis. The constant: peri-urban wetness that survives is PURPOSED - so a defensive belt is military ground, not waste.

## Canal junction angles - an offtake leaves pointing downstream

**Grounds:** `moat_junctions_swept_with_the_current`, `settlement.moat_swept_tap`, `city_moat_junction_angles`

Canal practice: an offtake leaves its parent at an ACUTE angle pointing downstream - best alignment 0 deg separating out in transition, studied optimum 15-45 deg, explicitly "30 or 45 **instead of 90**"

## Irrigation topology - one pond outlet that branches

**Grounds:** the `channel()` layout; Kikuta's `OUTLET`

A *tameike* reservoir has a SINGLE outlet sluice (*hi*) - occasionally two - so all its irrigation leaves by one main channel (*yosui*) that then FORKS downstream to the fields, dividing at junctions; it is NOT several independent pipes drilled into the pond.
