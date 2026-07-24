# Town deep audit - Hoshizora + Hirameki (2026-07-24)

A granular audit of the two town-scale pool maps against (a) the project's own documented
research (budgets.md, settlements.md, buildings.md, the gens' docstrings) and (b) fresh
historical research on Edo-period county-seat-class towns (jin'ya/daikansho seats, zaigomachi,
shukuba) with Ming/Qing market towns as the China cross-check. Requested by the GM 2026-07-24.
Companion to `town-checks-audit.md` (which audited the CHECK suite; this audits the MAPS and
the research behind them).

Verdict up front: the two maps are in strong shape - every doctrine-required feature is
present, the population model is coherent and documented, and most deviations from history
carry recorded whys. The audit found ONE structural question (street-fabric gap width), THREE
internal inconsistencies (servant convention, stale bscale text, gate-market authored-vs-landed),
ONE undocumented size table (the URBAN glyph footprints), and a short list of well-attested
county-town features we neither draw nor document as omitted (kosatsuba first among them).

## 1. Population audit

Model (documented, settlements.md "Population is DWELLINGS x ~5" + both gen docstrings):
the ~1,200 county population is a budgets.md-derived 238 households; town maps declare the
DEPICTED population (dwellings x 5) because most of the ~156 farm households sit off-map;
non-farmer castes are drawn at their FULL documented counts - so the GM's audit question
"do the non-farmer counts hold?" is exactly what the design promises. It largely does:

| Caste | budgets.md hh | gate band | Hoshizora drawn | Hirameki drawn | verdict |
|---|---|---|---|---|---|
| merchant | 24 | 20-28 | 24 (21+3 large) | 22 (18+4 large) | PASS both |
| laborer | 28.8 | 25-35 | 25 (22+3 large) | 28 (25+3 large) | PASS; Hoshizora sits at the band floor, ~4 under budget |
| servant | 13.2 total / ~5 standalone | 9-17 | 16 | 13 | see inconsistency 6.1 |
| burakumin | 12 | 10-14 | 11 | 14 | PASS both |
| samurai | 4 hh (~20 people) | 5-10 | 8 (6+2 large) | 9 (7+2 large) | sanctioned but under-explained, see 6.3 |
| farmers | 156 (sampled) | plurality only | 51 farmhouses | 75 farmhouses | PASS by design (off-map remainder documented) |
| declared pop | - | +-7% | 680 = 135 dw x 5 | 820 = 161 dw x 5 | PASS both (arithmetic exact) |

Business premises (not household-gated): Hoshizora 6 shops + 24 dual-use merchant houses
~= 30 commercial premises; Hirameki 7 + 22 ~= 29. A zaigomachi of ~1,000-1,500 typically ran
a few dozen commercial households, many part-farming - both towns are inside the band.

## 2. Building-size audit (1 px = 1 ft, toscale=True)

Sizes WITH a recorded research anchor - all check out against independent references:

- **Farmhouse 46x28 ft base** (minka anchor, length-dominant jitter, aspect cap 2.7:1) - good.
- **Merchant kura annex 20x14 ft** - a real dozo is ~2x3 ken (12x18 ft); excellent match.
- **Caravan inn 66x48 ft** - a large 2-story hatago ran ~30-40 ft frontage; 66 ft is the big
  post-road tier; documented why exists. PASS.
- **Stables 92x44 ft** ("full wagon-train") - PASS as the relay function's single glyph.
- **Flophouse 104x46 ft** - real kichin-yado were ordinary house-scale; 104 ft is generous,
  but the recorded why ("long dormitory, beds dozens, volume at rock-bottom price") covers the
  choice. PASS with note.
- **Theater ground 150x105 / 120x84 ft, stage ~0.5w x 0.26h** - temple-precinct opera/kagura
  stage doctrine; a real kagura-den runs ~30-40 ft, our stage ~60-75 ft - mildly large, inside
  the legibility license. PASS with note.
- **Cremation core 75 ft, ossuary mound 22 ft** - both documented mid-band of real ranges. PASS.
- **Magistrate manor: Hoshizora 250x180 ft (~1.0 acre), Hirameki 360x216 (~1.8 acres)** -
  Takayama Jin'ya (the surviving Hida daikansho) runs just under an acre for the office core;
  1 acre for a quiet interior seat and 1.8 for a walled border town with garrison are right.
  Interior program is separately grounded in buildings.md (Harima worked example). PASS.
- **Monastery halls: Bishamon 132x86 / 150x98 ft, Benten relic 60x40 ft** - large for a real
  county-town temple, but the L7R temple canon (settlements.md: "L7R deliberately over-sizes -
  every city temple is a major complex", clergy at 2-5x historical density) is exactly the
  documented deviation that covers it, and the little Benten hall shows the small tier exists.
  PASS as documented Rokugan convention. (Minor doc gap: town-tier monk COUNTS are never
  stated; cities get 15-30/complex, capitals 50+. Worth one line in settlements.md someday.)
- **Fire tower frame 26 ft square** - a real hinomi-yagura base is nearer 12-15 ft; the
  legibility license ("a single tower stands in for the whole watch") plausibly covers 2x on
  a location-marker feature. PASS with note.

Sizes WITHOUT a recorded research anchor - the URBAN glyph table (settlement.py URBAN dict)
carries one-line labels but no researched why for its numbers:

| glyph | ft | vs research |
|---|---|---|
| merchant 54x36, shop 48x32 | 1,944 / 1,536 sq ft | The AREA is honest for a prosperous shophouse, but the ASPECT is inverted: a real machiya was frontage-taxed at ~18 shaku (~18 ft) wide by 60-100 ft DEEP; ours are 3x the standard frontage and shallow. 24 such fronts make the drawn street ~3x longer than the real street it depicts. |
| laborer 34x24 | 816 sq ft | A real urban laborer lived in a nagaya unit of ~114-190 sq ft; a detached 816 sq ft cottage is defensible for a COUNTRY town backstreet (zaigomachi laborers were often part-farmers), but the glyph is doing that work undocumented. |
| servant 30x22, samurai 56x40, samurai_large 82x58, merchant_large 86x60 | - | All plausible against jokamachi references; merchant_large ~= a honjin-class house. No recorded anchors. |
| burakumin 38x26 | 988 sq ft | LARGER than the laborer glyph (816 sq ft). Historically inverted - burakumin housing was the poorest tier. Presumably sized for the dashed-outline glyph to read; undocumented. |

Recommendation 8.2 covers the fix (record the table's whys; decide the frontage question).

## 3. Urban fabric - detached vs row-fronted

Measured: Hoshizora 71 urban buildings, nearest-neighbor edge gaps min 3 / median 23 / max
72 ft, ZERO touching pairs. Hirameki 70 urban, min 6 / median 19 / max 76 ft, ZERO touching.

What the research says: DETACHED IS CORRECT at this tier. The machiya typology literature
(Izumida, "Machiya: A Typology of Japanese Townhouses") records that machiya in the planned
towns - jokamachi, shukuba-machi, and by extension zaigomachi - were single DETACHED houses
with no shared party walls (standard frontage 5.4 m / 18 shaku, ~3-shaku setbacks), unlike
the contiguous party-wall fabric of the big cities that drives our CITY row-packing doctrine
(`city_row_housing_touches`). So towns using plain `pack` while cities use `rowpack` is
historically right - but it is NOWHERE documented as the deliberate town/city split, and the
city doctrine's own text ("urban commoners did not build detached-with-yard") reads as if it
indicts the town maps too. It should not: record the split.

The one honest quibble: real detached machiya stood a few feet apart (eave gaps ~3-6 ft);
our medians of 19-23 ft read as a loose village street, especially on Hoshizora's road
frontage. Half of that is the inflated 54-ft frontage stretching the street (section 2);
tightening frontage widths would tighten the gaps for free.

## 4. Granular non-residential inventory

Per feature, per map: what stands, what doctrine demands, what history supports.

| Feature | doctrine | Hoshizora | Hirameki | verdict |
|---|---|---|---|---|
| Magistrate manor | required, gate faces town/road | 250x180, rot -30, faces road | 360x216 on the hill | PASS |
| Monasteries | 2 per town (clan's patron fortunes) | 1 (Bishamon) - documented exception, quiet interior seat | 2 (Bishamon + Benten relic) - documented changed-hands override | PASS, both exceptions recorded in the gens |
| Monastery graveyards | required, opt-out | present | Bishamon yes; Benten opted out (documented: dead go to the Bishamon parish ground) | PASS |
| Torii | roll-gated; 1-2 or exactly 7 | 3 (authored stop at theater court, documented) | 10 = Bishamon 3 + Benten 7 | PASS, numerology canon held |
| Theater stage | required, by/facing temple | 120x84 by the monastery | 150x105 facing Benten | PASS |
| Flophouse | default 1, at arrival point | 104x46 SW road approach | 104x46 outside the gate | PASS |
| Caravan inn + stables | exactly 1, fronting road, open ground | inn 66x48 + stables 92x44 | same | PASS |
| Merchant kura | >= 3 | 6 | 6 | PASS |
| Granary | opt-in (transit hubs only); default lives in the yamen | not set | not set | PASS (doctrine documented) |
| Gate market | walled only, >= 3 businesses within 420 ft of gate | n/a (unwalled) | 4 merchants at 129-217 ft + flophouse | PASS the check; see 6.4 |
| Burakumin neighborhood | segregated, >= 40 ft | NE edge, 11 | outside wall, 14, 842+ ft from gate | PASS |
| Fire furniture | walled-only tower (2026-07-24 revert) | none (correct) | 1 tower in commoner core | PASS |
| Cremation ground + ossuary | required, edge, >120 ft from dwellings | present | present | PASS |
| Wells | ~1 per 10-20 hh + farm reach rule | 24 (1 per 5.6 hh - over-provisioned by the farm-reach rule; fine) | 16 (1 per 10) | PASS |
| Bridges | wherever road crosses water | 0 (no crossings; road parallels stream) | 0 (streams outside, streets clear) | PASS |
| Barns/pasture | post-relay towns only | 5 barns + 2 pastures (Imperial Road relay, documented) | none (correct) | PASS |
| Small wayside shrines | city tier: >= 3 near temple neighborhoods; town tier: NO RULE | 0 | 0 | gap - see 7.5 |

## 5. Gate market, granularly (the GM's example question)

Authored: `s.pack(..., ["merchant"]*6 + ["shop"]*6, face_streets=True)` - 12 businesses.
Landed: 4 merchants, 0 shops (the packer ran out of street frontage in the 460x170 ft rect
and silently dropped 8). The check floor is >= 3, so the gate passed.

Is 4 + flophouse reasonable for ~1,200? The doctrine text asks for "a *small* gate market of
a few shophouses" - 4 satisfies the letter. Historically the guan-xiang of even a modest
Chinese county seat, and the gate-front machiya strip of a Japanese one, ran from a handful
to a few dozen structures; 4 is the thin end but defensible for a border town whose gate
shuts at dusk. The REAL finding is authored-vs-landed drift: the map's author believed this
gate market was 3x the size it is. Either widen the pack rect / add a second row so ~8-12
land, or reduce the request to match the ground truth - and consider a pack-shortfall warning
(the "no silent caps" principle applied to `s.pack`).

**RESOLVED (GM decision 2026-07-24, follow-up conversation):** budgets.md confirms towns levy
NO import tariffs (the whole apparatus - Yasuki Taka gate collection, tariff-audit yoriki - is
provincial-city/capital-only, ~2,700 collection points vs an impossible ~14,400 town gates),
so the doctrine's tax-dodge rationale was corrected to traffic + market-day + night-arrival
drivers, and the size guidance settled at **typically ~4-8 premises, floor >= 3, scaling with
gate traffic not population**. The 4 landed premises turn out to be the honest ground truth:
2 come from the MAIN-street frontage stringing through the gate and 2 from the pack, and a
placement probe showed every other road-front spot genuinely blocked (the s1 paddy comb +
collision radii - the suburb is FULL). The gen now authors exactly what lands, declared
population synced to the depicted 785 (the earlier-ending pack shifts the RNG; the farm rings
settle at 71 farmhouses). Run-off-frame truncation is a CITY device (their canvas extends past
the cropped view); a town canvas IS the view and `_fits` keeps builds 26px clear of the edge,
so the town-tier continuation signal is the road running off the edge. `_shortfall` warnings
now print from `pack`/`frontage` (the "no silent caps" fix) - and immediately revealed the
request-as-budget idiom across the pool gens (Hirameki MAIN frontage 8/24, tenements 19/26;
Hoshizora road core 27/44; the city gens' capacity fills up to 3/600). The idiom got a name:
`fill=True` declares a request a capacity budget ("place up to N") and silences the warning;
an UNMARKED warning is a standing TODO to decide drift-vs-budget. The town gens' budget
sites are annotated; the CITY gens still print theirs - left loud on purpose for the city
session to annotate (or trim) with its own knowledge of which numbers are load-bearing.

## 6. Internal inconsistencies

1. **Servant convention contradicts the gate band and both maps.** settlements.md's modeling
   convention says only the ~5 "miscellaneous" servant households stand alone ("the rest
   aren't drawn" - they live inside employer compounds), but `town_caste_count[servant]`
   demands 9-17 and the maps draw 16 (Hoshizora) / 13 (Hirameki) - the FULL budgets.md
   servant count as standalone cottages. One of the three must move: either the doctrine
   text is stale (band + maps are the intent) or the maps over-draw servants ~3x.
2. **Stale bscale paragraph.** settlements.md "Town scale != village scale" still instructs
   `s.bscale ~= 0.82` and cites Hirameki as `Settlement(2600, 1820, ...)`; the scale-ladder
   pass retired 0.82 (bscale = 1/ftpx = 1.0 at town scale; the modernized bullet elsewhere in
   the same file says the old values "are gone") and Hirameki's canvas is (2600, 2000).
3. **Samurai houses vs households.** budgets.md gives ~4 samurai households; the documented
   convention draws 5-10 houses with the working platoon barracked (undrawn) inside the
   manor. The convention is recorded but its WHY is not - why do 4 households show as 8-9
   houses? (Plausible reconstruction: the ~20 resident samurai include singles/retainers
   householding separately - but that is a guess, and Principle "record the why" says write
   it down or change the band.)
4. **Gate-market authored-vs-landed** (section 5).

## 7. Missing-feature candidates (new research)

Attested for exactly this settlement class and neither drawn nor documented as omitted:

1. **Kosatsuba (official notice board) - the strongest add.** Every Edo town and village kept
   the official edict board at a prominent main-road spot (gate, bridge, center); it was the
   state's voice in the settlement, deliberately imposing. For a setting whose towns ARE
   magistrates' seats, this is high-flavor, tiny (a roofed board ~10-15 ft), and trivially
   placeable: by Hirameki's gate, on Hoshizora's Imperial Road frontage near the manor lane.
2. **Sake/miso/soy brewery (sakagura).** The classic county-town industry; the richest rural
   merchant was typically the brewer-landlord (gono), and in-country brewing was licensed and
   ubiquitous. Our merchant_large glyph could simply BE this with a label + an extra kura, on
   one map. Alternatively document "trades are abstracted into the generic merchant/shop
   glyphs" once, and this and the next two items all inherit the answer.
3. **Teahouse/chaya + market-day food stalls.** The refreshment side of the periodic-market
   economy (the flophouse covers only lodging). Historically inseparable from a market
   street; abstraction into `shop` is fine if documented.
4. **Blacksmith/farrier.** With a horse-relay function (Hoshizora's barns + stables) a
   farrier is near-obligatory historically; same abstraction answer available.
5. **Small wayside shrines at town tier.** The city tier documents and gates a smattering of
   small shrines near the temple neighborhoods (>= 3); towns have no rule and draw zero. A
   real 1,200-person town would keep its ujigami and roadside shrines even with the Fortune
   monasteries carrying formal worship. Port a 1-2 shrine expectation down, or document that
   at town scale shrine worship is folded into the monasteries.
6. **The market ground itself.** Doctrine implies market-day commerce (flophouse grounding,
   gate market) but never says WHERE the periodic market physically happens. Historically the
   street IS the market (machi street markets; stalls in front of the shophouses) - which is
   what the maps implicitly show. One recorded sentence would close it; no drawing needed.

Considered and REJECTED (recorded so they are not re-litigated):

- **Water mill (suisha)**: large-scale waterwheel rice milling is a late-Edo/19th-century
  industrialization; borderline anachronistic for the Sengoku-flavored setting. Skip.
- **Public bathhouse (sento)**: a big-city institution in the period; a 1,200-person county
  seat bathed at home/at the inn. Skip.
- **Execution ground**: county justice is real, but the site was typically outside town at a
  riverbank/boundary, tiny, and grim; GM call whether it ever earns a glyph. Default skip.
- **Terakoya schooling**: happened INSIDE temple precincts; already covered by the monastery
  glyph. No separate building.

## 8. Recommendations, ranked

1. **[DONE 2026-07-24]** Add the **kosatsuba** to both maps - `s.kosatsuba(...)` glyph (true
   ~12x5 ft), `town_has_kosatsuba` default-on + `kosatsuba_by_the_road` siting check (within
   ~60 ft of a road/street), `meta(kosatsuba=False)` opt-out. Placement follows the follow-up
   research: the TOWN board is a traffic institution (highway frontage / main street by the
   gate), distinct from the manor-gate board (Mode A) which posts the bench's output - the
   two-board split is documented in settlements.md "Notice board (kosatsuba)" and cross-noted
   in buildings.md. Hoshizora: SW road frontage at the theater/flophouse arrival node;
   Hirameki: main street just inside the front gate.
2. **Record the URBAN size table's whys** in settlements.md (the one undocumented size
   table), and decide the merchant frontage question: either accept wide-shallow shophouse
   glyphs as a legibility convention (document it), or move toward narrower/deeper frontage
   (which also tightens the street-gap finding in section 3 for free).
3. **Resolve the servant contradiction** (6.1) - likely by fixing the doctrine text to match
   the band + maps, since the drawn 13-16 equals the full budgets.md count.
4. **Document the town/city fabric split** (detached provincial machiya vs city row-packing)
   with the Izumida grounding, so the city doctrine's "did not build detached" line stops
   implicitly indicting the town maps.
5. **[DONE 2026-07-24]** Fix the Hirameki gate market authored-vs-landed drift (5) - resolved
   with the traffic-not-taxes doctrine correction, authored=landed, and the `_shortfall`
   warning in `pack`/`frontage`; see the RESOLVED block in section 5.
6. Refresh the **stale bscale paragraph** (6.2).
7. Decide the **abstraction doctrine** for named trades (brewery/chaya/farrier/pawnshop):
   one documented sentence, or promote the brewery to a drawn feature on one map.
8. Decide **town-tier small shrines** (7.5).

## Sources (external, this audit's new research)

- Izumida, "Machiya: A Typology of Japanese Townhouses" (detached provincial machiya, 18-shaku
  frontage, frontage taxation): https://www.researchgate.net/publication/280014082
- Kosatsuba: https://www.nakasendoway.com/kosatsuba-official-notice-boards/ and
  https://www.japanesewiki.com/history/Kosatsu%20(street%20bulletin%20board%20in%20important%20streets%20and%20crossings).html
- Hatago counts (Hara 16 / Tsumago 31 / Miya 248, 1843): https://en.wikipedia.org/wiki/Hatago
- JAANUS hi-no-mi yagura (fire-tower dimensions): https://projects.mcah.columbia.edu/jaanus/node/4095
- Rural brewing / fermentation towns: https://www.tsunagujapan.com/fermentation-town-sake-miso-beer-and-more-in-the-rustic-streets-of-nuttari/
- Edo pawnshops (2,700+ in Edo): https://darumapedianews.blogspot.com/2015/07/edo-shichiya-pawn-shop.html
- Waterwheel rice milling as a late-Edo development: https://sake-museum.jp/en/saketalk/1010/
- Takayama Jin'ya (daikansho scale + fire-prevention water system): https://en.wikipedia.org/wiki/Takayama_Jin%27ya
