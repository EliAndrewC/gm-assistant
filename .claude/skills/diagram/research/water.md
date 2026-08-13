# Water: the research behind the flow, channel and wetland rules

*The research behind the rules in [`../settlements/water.md`](../settlements/water.md). Findings, anchors and disclosed departures live here so the rule file stays operational; this file is where citations and deeper historical context get added as they accumulate.*

**Load this file when:** you are changing a water rule, a width, or a check threshold - or you want the historical basis before overriding one. Not needed to simply DRAW water from the rules file.

Every entry: what the research found, the decision it drove, and any deliberate departure from literal reality. Anchors are stable - rules link to them by `#slug`.

---

## Water-width ladder - the real-world tiers

**Grounds:** `irrigation_channels_hairline`, `watercourses_wider_than_ditches`, `moat_is_heaviest_watercourse`, `moat_dwarfs_ditches`

**Evidence:** attested

**Sources:** not recorded - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

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

**Evidence:** attested, corroborated

**Sources:** not recorded - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

- *The physics (the load-bearing "why").* Water balance at a stable level: `outflow = inflow + rain - evaporation - seepage`. With NO outlet, `outflow = 0` forces `inflow = evaporation + seepage`; a real perennial stream delivers far more than a moat's surface can evaporate or its bed can seep, so storage climbs and the moat **overtops its banks** - "the level just keeps rising" is not a steady state, it is flooding. (A stream's upstream profile is set by its own bed slope, not the pond it enters - raising the moat only backs water up a short distance at the mouth, it cannot lift the whole feeder, so you cannot absorb continuous inflow by "raising the stream too.") The terminal-pond regime is real but belongs to a **spring/rain-fed** moat in an **arid** climate where small diffuse input is balanced by evaporation; a wet rice climate (modest evaporation; a high water table and puddled paddies that seal seepage) cannot absorb a live stream, so a stream-fed moat there MUST shed the surplus through a channel.

- *What the research found (China first: Beijing's gated water-passes + the Forbidden City moat; Japan agreeing: Edo/Matsue jokamachi moats).* Flow-through was the standard, engineered deliberately. **Beijing** admitted water through gated wall passes, branched it into through-city rivers, and discharged SE to the Tonghui/Grand Canal; the **Forbidden City** moat is fed from the Jade Spring and "flows in from the NORTHWEST and discharges to the SE" - inlet one corner, outfall the diagonal. Flushing mattered for sanitation (a stagnant moat stank and bred summer fevers; the remedy was flow-through + annual dredging), for **storm drainage** (a city moat doubled as the flood sluice - a drain with no outfall is not a drain), for a fire-water reserve, and for irrigation offtake. The pond-like look is legitimately achieved by an **overflow weir/sluice** that holds a set level and sheds only the surplus (Beijing's gated behavior) - placid surface, real outlet underneath. A closed moat with a live feeder and no outlet is historically wrong.

## The diverted-stream moat is a historical type

**Grounds:** Tango's stream-fed ring

**Evidence:** attested, corroborated

**Sources:** not recorded - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

- *The diverted-stream moat is itself a historical type (GM asked whether Tango's arrangement - a stream seemingly turned into the moat, then resuming its course - was real, 2026-07-23).* It is, and commonly so: a dry-site Chinese seat dug its *hucheng he* by turning a nearby stream through the ring (the Forbidden City's NW-in / SE-out flush is the model Tango already encodes), and Japanese castle towns fed moats by the same river diversions (Edo turned the Hirakawa into its moat spiral). Two honesty notes, both deliberate: (1) **no relic of the stream's pre-diversion bed is drawn through the city** - after centuries of urban buildup the abandoned course is built over, so its absence is realistic, not an omission (do not "fix" this by threading an old channel through the blocks); (2) the ring splits the feeder's flow into two live arcs (west-about and east-about) that rejoin at the outfall, which is why irrigation taps on BOTH flanks can legitimately draw "with the current" (`moat_channels_flow_with_current`).

## One name per river - and why that is anti-historical

**Grounds:** prose, titles and notes wherever a river is named

**Evidence:** attested, corroborated, liberty

**Sources:** not recorded - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

*What the research found:* one-river-many-names was the NORM in the pre-modern world, in both reference cultures. China: the Yangtze never had a single pre-modern name - its course ran Tuotuo He / Tongtian He / Jinsha Jiang, then regionally Chuan Jiang (Sichuan) / Jing Jiang (Hubei) / Xunyang Jiang / Yangzi Jiang (originally only the Nanjing-Shanghai reach; modern standardization settled on Chang Jiang). Japan: per-stretch renaming was standard practice - the Chikuma-gawa becomes the Shinano-gawa at the Shinano/Echigo provincial border, the Seta/Uji/Yodo system renames at each confluence, and within Edo itself one river carried different names neighborhood by neighborhood (Asakusa-gawa / Ryogoku-gawa / Okawa / Sumida-gawa, all the same water). The mechanism: pre-modern river names were LOCAL - people named the reach they lived on and used, and nobody needed a whole-course name because nobody administered or traveled the whole course; names broke at both political borders and confluences. One-name-per-river is a modern bureaucratic artifact (national mapping agencies, Japan's 1896/1964 River Laws, the PRC settling on Chang Jiang).

## Marsh - wet rice is reclaimed FROM wetland

**Grounds:** `s.marsh(poly)`, `marsh_on_low_ground`

**Evidence:** attested

**Sources:** [`aas-rice-technology`](SOURCES.md#aas-rice-technology)

This is grounded in the fact that **wet rice is reclaimed FROM marsh**: the lower-Yangzi / Tai-Lake paddies are embanked **polders (圩田/围田)** diked out into marsh and lake, and where reclamation stops (or the ground is too wet to manage) it *stays* reed wetland (abandoned paddy reverts to marsh).

Sources: rice domesticated in "naturally marshy areas" + paddy-as-reclaimed-marsh (AAS "Rice, Technology, and History"); Tai-Lake polders diked from marsh/lake; abandoned paddies revert to wetland.

## The wet toe is as wide as the FAN, not as wide as the valley

**Grounds:** `Settlement.toe_band` (the cross-slope extent of `hinterland()`'s reed marsh)

*What prompted it (GM 2026-08-12):* the toe band was being drawn from the CANVAS CORNERS, so it
crossed the map edge to edge and a settlement whose fall pointed at its own frame had no dry exit
anywhere - every connector had to turn away over the settlement's back, which contradicts the
water-mouth doctrine. The GM asked where the wall-to-wall wetness had been established, and the
honest answer was: nowhere. It arrived as a side effect of the 2026-07 fix that made the toe a
CONTOUR band so it would rotate with the fall (the rotation was the point, and it was right); the
only stated rule was and is `marsh_on_low_ground` - the marsh lies downhill of the field. The GM's
instinct was to derive the width from what the fan waters, and asked for it to be checked against
real farmland first.

*What the research found:* real wet toes are FEATURE-bounded, not valley-bounded, and two separate
landforms say so.

- **The alluvial fan (扇状地), which is the landform our comb fans actually depict.** Its three zones
  are canonical in Japanese physical geography: at the **扇頂** (apex) the gradient is steep; across
  the **扇央** (mid-fan) the river water sinks into coarse gravels, so streams run dry and the ground
  is poor for paddy - historically woodland, then mulberry (桑畑), now orchards; and at the **扇端**
  (toe) that water re-emerges in a **spring line, 湧水帯**, which is why settlements and paddy have
  clustered there since antiquity. The decisive point for us is WHERE that line runs: it emerges
  where the permeable fan deposits meet the impermeable floor beneath, so it follows the fan's own
  geometry rather than the width of the valley the fan sits in. The wetland literature says the same
  from the other direction - slope wetlands form at breaks in slope where groundwater discharges,
  and are typically found *on the perimeter of* permeable alluvial fans.
- **And the mechanism is fed by the command area itself.** In fan-country paddy districts, river
  infiltration *and seepage from the rice fields* are the significant sources of groundwater
  recharge - the water that emerges below is largely the water the fan put in. Canal and field
  seepage causing waterlogging below an irrigated command is the same relationship in the modern
  engineering literature. So the wet ground below a fan is downstream of what the fan waters in a
  causal sense, not merely a coincidence of elevation.
- **The one landform that could have contradicted it does not.** On a floodplain the wet ground is
  the **後背湿地** (backswamp) - but it is bounded by the **自然堤防** (natural levees) that make it,
  which is again a feature boundary rather than the valley's width, and in Japan most backswamp was
  itself converted to paddy rather than left as reed waste. Neither landform gives us wetness from
  valley wall to valley wall.

*The decision:* `toe_band` takes its cross-slope extent from the CULTIVATED extent (the fan's plots
plus the dry hem) with a `pad` shoulder each side for the seepage spreading a little past the
watered ground, clamped to the canvas. The `pad` is the same 90 px the band already used for its
uphill overlap, so the shoulder is not a new magic number.

*The departure we are taking knowingly:* a real spring line is an ARC following the fan's toe, and
ours is a straight contour band with square lateral ends. Curving it would be more faithful; the
band is a ground-cover region whose reeds are scattered and feathered to nothing at the margin, so
the square end is not visible as an edge. Revisit if a map ever shows one.

*What it changed:* dry ground appears at both lateral ends of every toe (Ikegami's spans x 402-1799
on a 1900 px canvas, where it used to run -120 to 2020), and with it the settlements get their
downslope exits back. Two connectors that had been turned out sideways purely because the old band
left no legal southern route - Ikegami's and Akagahara's - were restored to their original routes,
which are dry for their whole length under the researched width. Moritono's re-route stands: its
fall is west, and its original track ran down the wet side.

*Sources:* 扇状地 (Japanese Wikipedia) on 扇頂/扇央/扇端 and the 扇端 spring line; MLIT land-classification
teaching material "扇状地と人々の暮らし"; Woods, Westbrook et al., "Hydrologic interactions between an
alluvial fan and a slope wetland" (Wetlands, 2006) on slope wetlands at fan perimeters; the Tedori
River alluvial fan groundwater studies (Paddy and Water Environment) on paddy-field seepage as a
recharge source; 後背湿地 / 自然堤防 (Japanese Wikipedia, GSI) on backswamp formation and land use.

## No toe marsh at town/city scale - the drainage-investment gradient

**Grounds:** village/hamlet gens draw a toe marsh; town/city gens draw none

**Evidence:** attested, corroborated

**Sources:** not recorded - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

*What the research found:* the real pattern is a **gradient of drainage investment and land value**. VILLAGES had neither the capital nor the incentive to eliminate every wet margin: residual wet ground at the low edge of village land is very well attested (Japanese *yatsuda* valley-bottom paddies were essentially managed marsh; reed beds were harvested village commons under *iriai* tenure - thatch, screens, annual burning; poorly drained *fukada* "deep fields" persisted until Meiji-and-later drainage projects), and crucially it was USED wet ground - reed bed, wet meadow, more paddy at the reclamation frontier - which is exactly what our sparse harvestable-reed rendering reads as. TOWNS/CITIES commanded corvee-scale hydraulic engineering and premium peri-urban land: ditch discharge went into an engineered moat/canal/river network (Suzhou's canal grid; Edo's canals and the immediate infill of the Hibiya inlet after 1590), and the outskirts were intensively worked (suburban vegetable belts fed by urban night soil; Edo-period reclamation waves around Osaka and Edo). Where wetness DID persist near a city it was **bounded and purposed** - a moat, a lotus/fish pond, a flood basin, a deliberate defensive inundation - never a diffuse seepage marsh below a ditch.

## Defensive marshland - the engineered wet belt

**Grounds:** `marsh(poly, role="defense")`, `defense_marsh_girds_the_walls`

**Evidence:** attested, corroborated

**Sources:** not recorded - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

*What the research found:* the Northern Song built an artificial marsh-and-pond belt across the northern Hebei frontier (from 989, He Chengju's lake chain) specifically as anti-cavalry terrain; Japanese *numajiro* "marsh castles" (Bitchu Takamatsu, besieged by water 1582) used surrounding marsh as their primary defense; and flooded paddies around castle towns functioned as a de facto glacis. The constant: peri-urban wetness that survives is PURPOSED - so a defensive belt is military ground, not waste.

## Canal junction angles - an offtake leaves pointing downstream

**Grounds:** `moat_junctions_swept_with_the_current`, `settlement.moat_swept_tap`, `city_moat_junction_angles`

**Evidence:** attested

**Sources:** not recorded - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

Canal practice: an offtake leaves its parent at an ACUTE angle pointing downstream - best alignment 0 deg separating out in transition, studied optimum 15-45 deg, explicitly "30 or 45 **instead of 90**"

## Irrigation topology - one pond outlet that branches

**Grounds:** the `channel()` layout; Kikuta's `OUTLET`

**Evidence:** attested

**Sources:** not recorded - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

A *tameike* reservoir has a SINGLE outlet sluice (*hi*) - occasionally two - so all its irrigation leaves by one main channel (*yosui*) that then FORKS downstream to the fields, dividing at junctions; it is NOT several independent pipes drilled into the pond.
