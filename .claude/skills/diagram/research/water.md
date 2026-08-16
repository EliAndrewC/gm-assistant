# Water: the research behind the flow, channel and wetland rules

*The research behind the rules in [`../settlements/water.md`](../settlements/water.md). Findings, anchors and disclosed departures live here so the rule file stays operational; this file is where citations and deeper historical context get added as they accumulate.*

**Load this file when:** you are changing a water rule, a width, or a check threshold - or you want the historical basis before overriding one. Not needed to simply DRAW water from the rules file.

Every entry: what the research found, the decision it drove, and any deliberate departure from literal reality. Anchors are stable - rules link to them by `#slug`.

---

## Water-width ladder - the real-world tiers

**Grounds:** `irrigation_channels_hairline`, `watercourses_wider_than_ditches`, `moat_is_heaviest_watercourse`, `moat_dwarfs_ditches`

**Evidence:** attested

**Sources:** [`gb50288`](SOURCES.md#gb50288), [`nougyoudoboku-matsutan`](SOURCES.md#nougyoudoboku-matsutan), [`toro-site`](SOURCES.md#toro-site), [`lacey-regime`](SOURCES.md#lacey-regime) (2026-08-17: the tiers below were re-consulted and sourced - they had stood unsourced since they were written)

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

## A channel taper is a SQUARE ROOT, not a straight line

**Grounds:** `waterfields.taper_w`, and every consumer of a local channel width - `field_channel`'s drawn stroke, `drain_bank_clearance` / `supply_bank_clearance` (shared with the gate), `_drain_bank`, `close_seams`' water buffer, the carve's bund-burial filter, `_watercourse_segs`' keep-out corridor

**Evidence:** attested, derived

**Sources:** [`lacey-regime`](SOURCES.md#lacey-regime), [`tabayashi-1986`](SOURCES.md#tabayashi-1986), [`nougyoudoboku-suikou`](SOURCES.md#nougyoudoboku-suikou)

*What prompted it (GM 2026-08-17).* The GM asked whether the supply ditches were right to thin as they
feed the paddies (they are - that is Tabayashi's rule, already encoded), and then whether it is correct
for one to "reach what looks like the current minimum width and then just stop, or if they should
continue getting thinner for some time" - and whether the widths were researched at all or invented.
Half of the answer was already here (the taper RULE is Tabayashi's, the width LADDER was written down
but unsourced); the taper's SHAPE had never been examined.

*What the research found.* Two relations, and between them they fix the profile completely.

- **Width goes as the square root of discharge.** Lacey's regime equation for an unlined alluvial
  canal - which is exactly what these are - gives wetted perimeter `P = 4.75 * sqrt(Q)`, and the
  regime power laws put width at `Q^0.5` against depth `Q^0.33` and velocity `Q^0.17`. This is not a
  new finding so much as a *recovered* one: [the water-width ladder above](#water-width-ladder-the-real-world-tiers)
  has always asserted "channel width scales with the square-root of the command-area flow it carries".
- **Discharge falls linearly along the run.** A delivery ditch sheds water through one *mizuguchi* per
  plot into a row of near-equal paddies, so it loses about the same flow per unit length; the collector
  gathers tail-water the same way in reverse. Uniform shedding over a run is Q linear in the fraction
  travelled.

*The decision it drove.* `w(t) = sqrt(w0^2 + (w1^2 - w0^2) * t)` - the width SQUARED interpolates
linearly, because the width squared is what tracks the discharge. One shared helper, `taper_w`, because
seven call sites needed the local width and every one of them had re-derived the straight line
separately; the bund bank-clearance the gate reads is one of them, so two formulas here would draw a
bund inside the water.

*What was wrong before.* Interpolating the WIDTH linearly quietly asserts `Q` proportional to `w`,
which is a different law and not one anything in the hierarchy obeys. It also looks wrong in exactly
the way the GM caught: a straight line spreads the whole narrowing evenly along the run, so the stroke
thins imperceptibly for its entire length and then stops dead at a still-substantial width. Under the
true law the ditch keeps most of its working width while it still has most of its water to deliver, and
then dwindles hard over the last stretch - which is what "the water is leaving it" ought to look like.
Measured on Inashiro's delivery ditches (8.0 -> 3.0 ft):

  | fraction along | 0 | 0.25 | 0.5 | 0.75 | 0.9 | 1.0 |
  |---|---|---|---|---|---|---|
  | old (linear) | 8.00 | 6.75 | 5.50 | 4.25 | 3.50 | 3.00 |
  | new (sqrt) | 8.00 | 7.09 | 6.04 | 4.77 | 3.81 | 3.00 |

  The same law runs the collector in reverse (3.0 -> 12.0 ft: 8.75 rather than 7.50 at mid-run), so a
  drain now visibly *gains* body in its first stretch, which is where a collector picks up the largest
  share of its catchment. It barely moves a SHALLOW taper - canal A's 12.4 -> 10.1 ft pieces shift by
  under 0.1 ft - which is the right behavior: the law only bites where a stroke really is shedding most
  of what it carries.

*A LAW IS NOT DELIVERED UNTIL ITS SAMPLING IS RIGHT (settlement-review 2026-08-17, and the half of
this work that nearly shipped broken).* The law above went in and the map still looked much as it had.
The cause was not the law: `field_channel` cut each stroke into 7 equal slices of the **vertex INDEX
range** and gave slice *k* the width at `(k + 0.5) / 7`, which is the width at that point of the run
only if the vertices are evenly spaced along it. The carve's are not - one delivery ditch's seven
slices covered 7.0 / 9.2 / 3.2 / 4.2 / 15.9 / 27.5 / **33.0%** of its length. So the drawn width
missed the law by up to **1.94 px (24-44% of the local width)**, the last third of the ditch was
inked at a FLAT minimum - reproducing the exact "reaches the minimum width and then just stops"
reading this work set out to fix - and a 2-point stub had six empty slices and was drawn end to end
at its TAIL width, 3.6 px where its record declared a 7.2 px head. `taper_pieces` now emits one
piece per SEGMENT at its arc-midpoint width. Measured after: 7.7 / 7.1 / 6.1 / 4.8 / 3.7 px at
tenths 0.10 / 0.25 / 0.50 / 0.75 / 0.90, i.e. the ink tracks the law within ~0.1 px.

Two transferable points, both instances of rules this engine already carries. First, `banks.py`,
`seams.py` and `carve.py` all took their local width at the ARC fraction while the renderer took it
by index - so the ink and the bank geometry the bunds are laid against were never the same curve,
which is "placement and its check must read the SAME source" wearing a different hat. Second, the
docstring recording this law was written with the FORMULA's numbers and was therefore false about
its own example map until the sampling was fixed: **a measured claim must be measured in the
artifact, not computed from the rule it is describing.**

*The departure we are taking knowingly.* This corrects the taper's SHAPE and the tier ORDERING, not the
absolute widths - and the absolute widths are inflated. See the disclosed-departure entry below.

*Still OPEN, and it wants a GM ruling (raised by the same review).* A delivery ditch's head is a flat
`4.0 * grain` while its parent supply canal tapers below that, so low in the tree the LATERAL is drawn
wider than the canal feeding it - on Inashiro at (2524.8, 1540) the lateral leaves at **7.96 px**
against a parent drawn **5.73** and continuing at **5.35**. This is not the junction-conservation
question already ruled on (drawn width is RANK, not discharge - see that entry); it is the rank READ
inverting, which is the one thing width-as-rank exists to convey. It predates this work, and the arc
fix nudged it the WRONG way (it was 7.75 against 5.70; ratio 1.36 -> 1.39), because that lateral's
first segment is only 6 px long, so its arc midpoint sits at t ~ 0.01 and the head piece is inked at
nearly the full flat head. The fix, if wanted, is to cap a delivery's head at some fraction of its parent's LOCAL
width - which would make every delivery's width depend on where it takes off, and re-roll the pool.

## Where the drawn net STOPS - the tier below the last ditch we can draw

**Grounds:** the `w_tail` floors in `build_comb` (delivery ditches to 1.5 * grain, supply canals to 1.6, the collector's head at `DRAIN_W_HEAD`)

**Evidence:** attested

**Sources:** [`gb50288`](SOURCES.md#gb50288), [`nougyoudoboku-matsutan`](SOURCES.md#nougyoudoboku-matsutan), [`nougyoudoboku-suikou`](SOURCES.md#nougyoudoboku-suikou), [`tabayashi-1986`](SOURCES.md#tabayashi-1986)

*The question (GM 2026-08-17).* Should a delivery ditch keep thinning past its drawn minimum - taper away
to a point - rather than ending at a visible width?

*What the research found: no, and the reason is that there is a whole further TIER, not a vanishing.*
Both reference traditions terminate the fixed net at a channel with a real working cross-section, and
then hand over to something that is not a channel at all.

- **The tier ladder is explicit and finite.** China names five fixed grades - 干渠 / 支渠 / 斗渠 / 农渠 /
  毛渠 (main / branch / lateral / farm / field), the *maoqu* being "the last grade of fixed channel, the
  small ditch that carries water into each individual plot". Japan's design vocabulary is the same
  shape with three: 幹線用水路 -> 支線用水路 -> 末端用水路 (*matsutan yosuiro*, the terminal channel),
  mirrored on the drainage side as 末端 -> 支線 -> 幹線排水路. A terminal channel is not a taper's
  vanishing point; it is a designed object with a section sized to peak demand, its bed set -5 to +10 cm
  against the paddy surface so a farmer can both run water in and get a foot in it to clean it.
- **The finest tier is far below our visibility floor.** The ladder above puts a field ditch at ~0.3 m -
  about **1 ft, i.e. one pixel at hamlet scale** and a third of a pixel at city scale. The tier we
  actually stop at, ~1 m / ~3 ft, is the *distribution lateral*, and drawing one grade finer would put
  the stroke below the sanctioned ~2.5 px minimum-visibility floor and collapse the hierarchy the
  water-width ladder exists to keep legible.
- **And in a PRE-MODERN system the last tier is frequently not a channel at all.** Before land
  consolidation, Japanese paddy was watered 田越し灌漑 (*tagoshi kangai*) - plot-to-plot: water enters
  the head paddy of a string and cascades down through the *aze* from one plot to the next, so the
  interior plots have no ditch of their own to draw. Tabayashi records the same relationship from the
  tenure side: the ditches that bring water to the plot inlets "are often considered parts of the paddy
  fields they serve". Our comb already models this - a column cascades several to ~10 rows past where
  its ditch stops - so the drawn ditch ending mid-field IS the handoff to the cascade, not a line that
  was left unfinished.

*The decision it drove.* Keep the floor: the finest DRAWN channel ends at the lateral tier (~3 ft) with
a blunt end, because that is a real terminal channel handing its flow to a *mizuguchi* and a cascade,
and both of those are below what this sheet can render. The taper LAW change above is what makes that
ending read correctly - the stroke now arrives at the floor by dwindling rather than by drifting.

*Correction recorded.* The 1.5-value floor used to be justified in a comment as "~1.5 ft across the
top - a hoe-width bottom plus side slopes", i.e. as the smallest *maintainable field ditch*. That
reasoning was for the wrong tier, and it also silently disagreed with what gets drawn: the scripted
tier passes `grain = 2 / ftpx`, so `1.5 * grain` is **3.0 ft**, not 1.5. The drawn value was right and
its stated reason was wrong - the number is the ~1 m distribution lateral, and the ~0.3 m field ditch
is the tier we deliberately do not draw.

## The bund runs along the channel bank, and the mizuguchi is too small to draw

**Grounds:** `supply_bank_clearance` and `paddy_bunds_clear_the_supply_channels`; `_drain_bank` / `drain_bank_clearance` and `paddy_bunds_clear_the_collector`; `aze_w`

**Evidence:** attested

**Sources:** [`nougyoudoboku-suikou`](SOURCES.md#nougyoudoboku-suikou), [`aze-standard`](SOURCES.md#aze-standard), [`toro-site`](SOURCES.md#toro-site)

*The question (GM 2026-08-17).* We draw the earthen bunds running along the banks of the irrigation
channels. Is that correct - and is the water reaching the paddies through gaps too small to render?

*What the research found: yes to both, and the second is precisely quantified.*

- **A continuous bund along the channel is right.** The paddy's own *aze* IS the channel's bank - a
  basin has to be watertight on every side, and the side that faces the ditch is no exception, or the
  plot would simply drain into it. Japanese design puts the terminal channel's bed at -5 to +10 cm
  relative to the field surface with the bund between them, which only works if the bund is unbroken
  except where an opening is deliberately made. The attested pre-modern case says the same: at Toro the
  canal *and* the bunds were revetted together with the same *yaita* sheet boards, i.e. a bank and a
  bund built as one structure.
- **The opening is the *mizuguchi* (水口), and it is sub-pixel.** Standard practice is **one intake per
  plot** (a second only when they would stand more than 50 m apart), of **width within 50 cm**, its
  sill 0-10 cm above the field surface so the inflow does not scour the bed, passing water at about
  0.4 m/s. The plot's outlet - 水尻 / 落水口, an overflow set 5-10 cm below the field surface - is the
  same size. At the hamlet scale of 1 ft per pixel a 50 cm notch is **0.5 px wide**; at provincial-city
  scale (3 ft/px) it is 0.17 px.
- **For calibration, the bund itself is standard too.** The outer *aze* is a trapezoid of 30 cm top
  width and 30 cm height at 1:1 side slopes - so ~1 ft across the crest and ~3 ft at the base (colder
  regions go to ~50 cm x 40 cm for deep-water irrigation and frost heave). Our `aze_w` of ~1.5 real ft
  sits between the crest and the base, which is the honest way to draw a trapezoid as one line.

*The decision it drove (a deliberate NON-render, recorded so it is not "fixed" later).* The *mizuguchi*
and *shirimito* are **never drawn at any Mode B scale**, and no check demands them. A 0.5 px notch
cannot be rendered, and a legible one would be a ~6x size inflation on the most numerous feature on the
map - one per paddy, on a map with hundreds. The bund is therefore drawn CONTINUOUS along every channel
bank, and the reader is expected to understand that water crosses it through openings below the
resolution of the sheet, exactly as they understand that a drawn farmhouse has a door. This joins the
standing list of things a settlement map states rather than depicts. **Do not "fix" the unbroken bund by
notching it**, and do not read the unbroken bund as a claim that the paddies are unwatered.

## The comb net's ABSOLUTE widths are inflated ~5-6x, deliberately - and this is the open question

**Grounds:** the channel widths in `build_comb` (head-race 7.0, canal A 6.2, canal B 5.6, delivery 4.0, `DRAIN_W_TAIL` 6.0, all x grain)

**Evidence:** derived (a measurement against the sources, not a rule change)

**Sources:** [`lacey-regime`](SOURCES.md#lacey-regime), [`fao-paddy-duty`](SOURCES.md#fao-paddy-duty)

*What the check was.* Having sourced the taper law, the same sources price the absolute widths, which
nothing had ever done. FAO puts a paddy's net irrigation need near 1 L/s/ha continuous, with the
puddling peak the figure that actually sizes a supply canal - call it ~3 L/s/ha. Inashiro's fan is a
20.9-acre (~8.5 ha) command area, so its head-race carries on the order of 0.025 m3/s at peak. Lacey
gives a wetted perimeter of ~0.75 m for that; Manning on a hand-dug 1:1 earthen trapezoid at a 1/500
grade agrees at ~0.6 m top width. **The true head-race for this hamlet is about 2 to 2.5 ft. We draw
14 ft.** The whole ladder is scaled to match, so every drawn channel is roughly 5-6x its true size.

*Why this is not a bug, and what it costs.* The true figures are also the reason: at 1 ft/px a truthful
head-race is a 2.5 px line, a truthful delivery ditch ~1.5 px, and the field ditch below them 1 px - so
truth-to-scale would compress the entire irrigation hierarchy into two pixels of range and erase the
tiering that [the water-width ladder](#water-width-ladder-the-real-world-tiers) exists to keep legible.
This is the sanctioned "drawn larger than true scale for legibility while keeping RELATIVE sizes roughly
honest" carve-out, and the relative honesty does hold: head-race > supply canal > delivery ditch >
terminal lateral, in the same order and roughly the same ratios as the real ladder.

*What is NOT settled.* The ladder's *magnitude* has never been a GM decision - it was authored by eye and
has simply never been priced until now. A 5-6x inflation is a good deal larger than the "minimum
visibility floor" the stroke convention in [`../settlements/water.md`](../settlements/water.md) claims to
be operating under, which honestly describes a 2.5 px floor on the FINEST tier and not a uniform scaling
of the whole net. So the convention as written and the code as drawn are not the same policy.
**Open for the GM**, with the trade stated: drawing nearer to true scale would make the comb net much
fainter and flatten the hierarchy, and would re-roll every scripted map; leaving it is a legibility
exaggeration on the most-repeated feature of a to-scale map. Nothing was changed here either way - this
entry records the measurement so the decision is made on numbers rather than on eye.

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

## Drawn width is RANK, not discharge - junctions do not conserve it (GM ruling 2026-08-16)

*The question.* All four reviewers of the fork re-roll independently flagged the head junction:
the brook arrives at 7 px, becomes a 14 px head-race below the sluice, and forks into arms
starting 12.4 + 11.2 px - drawn capacity appears to GROW downstream at every junction, and the
fork feature made that junction the focal water feature of every comb map.

*The ruling (GM 2026-08-16, options weighed: keep / intake stilling pool / conserve-at-fork).*
**Keep the convention.** A stroke's drawn width depicts its rank and local importance in the
irrigation hierarchy (the 2026-07-21 taper rule: widest at its head, dwindling as it sheds water
to its offtakes), sized per stroke with no cross-junction coordination - because width-as-rank is
what keeps the hierarchy legible at fit zoom, and conservation would chain every drawn width down
from the brook's 7 px and thin the far arms to hairlines. The intake jump also has a real
reading: a sluice-fed head-race genuinely IS wider and slower than the stream that feeds it
(engineered cross-section, ponding above the weir), so width-not-discharge is not merely a
stylization there. The arms each drawn narrower than their trunk is honest; only their SUM
exceeding it is convention. **Reviewers: do not flag in/out width totals at junctions** - judge
each stroke's own taper (head wider than tail) and the hierarchy read (trunk > branch >
delivery), never the conservation arithmetic.

## The head-race forks - supply commands both flanks

**Grounds:** `comb_supply_commands_both_flanks`; `hamletgen.OFFTAKE_LADDER` (every row now inks canal B); `build_comb`'s two-canal fork and the `fork` point it records on the field

**Evidence:** attested

**Sources:** `mbalib-canal-layout`, `saitama-minuma-tsusenbori`, `jsidre-minumadai` (Isawa corroboration in prose below)

*What the research found (GM asked 2026-08-16, after noticing Inashiro's channel turns along one margin but never splits the way other maps' channels do).* Gravity irrigation has one governing constraint: a canal commands only the ground BELOW it. Chinese canal doctrine states it as placement law - "干渠主要布置在灌区较高的地带，以便自流控制较大的灌溉面积" (main canals sit on the district's high ground so gravity commands the largest area) - and repeats it at every tier of the hierarchy ("布置在各自控制范围内较高地带": each canal on the high ground of its OWN command area), mains and branch canals along contours and ridge lines, field channels across them. The Kishu-school exemplar the comb layout already cites goes further: **Minuma-dai (1728) deliberately DIVIDES its head channel into TWO canals** - the east-edge and west-edge canals (東縁/西縁) - running along the two elevated margins of the reclaimed lowland so water can enter the paddies from both sides, with the Shiba River down the central lowland as the drain ("見沼代用水東縁・西縁は台地の縁に沿って流れ、芝川は低地の中央を流れる"). At fan scale the same shape appears as radial canals: the Isawa fan (one of Japan's largest, ~15,000 ha) is watered by weir canals leaving the fan head and spreading over the fan (MLIT Isawa pages, consulted via search 2026-08-16).

*The decision it drove.* A comb fan is planted on BOTH sides of its *bunsuiguchi* - the engine's own model already said so (`build_comb` carves canal B as a supply thread that shapes the far margin's plots and keeps deliveries off it) - so the DRAWN net must show both arms of the fork. Every `hamletgen.OFFTAKE_LADDER` row now gives canal B an offtake (~0.55), which inks the second arm partway down its margin, tapering to a thread per the Tabayashi taper rule. The hamlet rows' old `offtakes_b=()` was inherited from Ikegami's authored choice, and it left the modeled net and the inked net disagreeing: measured on the motivating map (Inashiro), **255 ft of planted paddy west of the fork carried 0 ft of drawn supply** while the east flank showed 994/995. Post-fix, every live hamlet's short flank carries ~170-200 ft of drawn supply against ~250-260 ft of paddy. Two terminations are honest, and the pool shows both: where the dug arm runs past its last offtake, the tail tapers to a thread and dies at the crop (Inashiro, Kashikawa, Mizuguchi); where the dug arm ENDS at its offtake, the canal hands its whole flow to the delivery and stops at the junction (Sawada) - what is dishonest is only a working-width canal chopped mid-margin, which the interpolated piece slicing in `build_comb` now prevents. Gated by `comb_supply_commands_both_flanks`: it reads the recorded fork and, on every flank with more than ~150 ft of paddy (cross-slope from the fork), demands drawn main/branch supply reaching at least 80 ft or 30% of that flank's extent.

*When a single arm IS honest.* The command principle cuts both ways: a tract lying wholly on ONE side of its supply needs no second arm - a ribbon strip along a contour canal, a terrace flight, a polder ring. None of those record a fork, so the check does not touch them; and a fan whose far flank is a sliver (under the 150 ft demand line) legitimately runs one arm. The frozen legacy hamlets keep their single-arm draws as exhibits - conversion, not retrofit, is their fix, per the migration doctrine.
