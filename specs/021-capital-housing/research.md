# Phase 0 Research: Capital Housing Layer (021)

The Principle XII **opening bookend**. For each element: what the historical reality was
(China first, Japan corroborating), whether the design matches it, and what DETERMINES the
element in reality. Items marked **[standing]** cite research already recorded for features
016-020 (pointer given; not re-derived). Items marked **[new]** were researched for this
feature and the finding is recorded here in full; the durable copy lands in
`research/cities/capitals.md` / `settlements/ways.md` as part of implementation
(record-the-why).

## 1. Rank-graded samurai districts [standing]

`research/cities/capitals.md`, "The capital's samurai are senior-heavy". Both traditions
grade proximity by rank: Edo's daimyo and upper hatamoto ringed the castle with lower
samurai further out; Chinese administrative cities seated officials nearest the yamen.
The capital INVERTS the provincial senior/junior mix (70% senior R5+ vs 27% provincial), so
walled yashiki and detached houses are the majority fabric, retainer terraces the minority.
**Determined by**: rank (proximity = precedence), the court as the point of the posting.
**Design matches**: several districts interleaved with commoner strips (the jokamachi
pattern), not one sealed quarter - the ward-mesh research. Gradient rule: yashiki band
nearest castle/government ward, detached band next, terraces at the band edge, machi beyond.

## 2. Retainer terraces (kumi-yashiki / nagaya) [new detail on a standing anchor]

The budget's `C_TERRACE` anchor (Shibata ashigaru-nagaya: 8 households, 143 x 21 ft, 18 ft
frontage each) is already recorded. New form detail for the GLYPH: a nagaya unit was a
single-file row-house cell - 4.5-8 tatami of living space (~10 m^2 common) behind an
earth-floored entry, family of 3-4, insubstantial cross-walls, amenities shared - so the
terrace draws as ONE long roof subdivided by party walls (drawn seams), not as detached
cottages at row pitch. Kanazawa's detached ashigaru houses are the recorded EXCEPTION, not
the norm. **Determined by**: economy (shared walls and roof are what a junior stipend buys)
and organization (units allotted by the lord, hence uniform).
**Design matches**: rows of `s.terrace` units, uniform frontage ~18 ft, party-wall seams,
modest yards where depth allows. **Rokugan correction stands**: these house junior SAMURAI
(Ranks 1-4); ashigaru are peasants and have no capital quarter (GM 2026-08-08).

## 3. Commoner machi rows [standing]

Feature 016/017 city row doctrine (Tango): rows touch, roji gaps are features, businesses
front streets, poor housing interior, 5.6x gross-up measured. Reused at 3 ft/px unchanged -
the spec's "no new packing paradigm" assumption. **Determined by**: street frontage economics.

## 4. Cistern-wells (josui-ido) and the service band [standing research, new placement rule]

The 020 aqueduct research ("How a josui actually ran"): from the Okido/terminal basin the
water entered BURIED mokuhi (wooden pipe) mains under the streets and was drawn from
josui-ido - cistern-wells tapping the main, indistinguishable at street level from a
draw-well but plumbed, not dug. Edo's Kanda/Tamagawa systems watered the LOW city this way
while the high city kept dug wells. **Determined by**: elevation and main reach - pipes ran
at grade from the terminus, so the service band is the street-connected fabric near and
below the entry gate, not a radius in open ground.
**Placement rule chosen (calibrated liberty, disclosed)**: the service band is the fabric
within ~600 real ft of street-path from the settling basin's gate, biased toward the
commoner machi (which lack private wells); wells inside the band record `kind: "cistern"`,
all others stay dug draw-wells. The 600 ft figure is a chosen point inside a plausible range
(Edo mains ran much further; a domain capital's young system plausibly serves its gate
quarter first) - recorded beside the rule in code and in research/cities/capitals.md.

## 5. Fire towers and the watch [new]

The shogunate MANDATED watchtowers in 1723; each machi kept its hinomi-yagura (tallest
structure in the neighborhood), and the ward's jishinban (guard office at the kido gate)
carried a roof ladder so the gate watch doubled as fire watch. So fire cover is a PER-MACHI
institution, not a city-wide grid - which the existing city fire-tower doctrine (fixed watch
radius in world px) approximates acceptably at ~10-15 towers for the capital's ~5x area
(the recorded counts-table row). **Determined by**: machi organization + fixed sight radius.
**Design matches**: existing `s.fire_tower` vocabulary at the doctrinal count, seated in the
dense fabric per the keep-clear contract; no new glyph. The kido/jishinban pairing is noted
in doctrine (a capital kido may draw its guard box, existing vocabulary).

## 6. Kido ward-gate mesh [standing]

020 research "Neither tradition walls its wards": Edo kido open ~4am-10pm at machi mouths,
roji-kido on tenement lanes, Qing zhalan street palings; no continuous ward fence; yashiki
walls seal samurai streets; `ward_style="mesh"` default, `"fang"` reserved as the Lion
variant knob (NOT this feature). **Determined by**: curfew institutions, block-level
collective responsibility. **Design**: `s.kido` at higher count with a mouth-of-machi
placement rule; 021 implements the mesh exactly as the recommendation records.

## 7. Sovereign precinct interiors [standing canon, form from Mode A doctrine]

GM temple-density canon: capital sovereign temples are head houses, Grand Abbot + 50+ monks
each, initiates 2x living out. The precinct program (residence, administration hall,
library/sutra hall, monk dormitories, kitchen/refectory) is the standard Zen/Chinese
monastic seven-halls plan both traditions share; the 020 reservation (~390x300 ft each) was
sized for it. **Determined by**: monastic institution scale (headcount) and liturgical
program. **Design matches**: draw the halls INSIDE the reserved rectangles, densest at the
hall axis, dormitories rearward, per the Mode A temple doctrine (`buildings/`); the map-scale
glyphs are footprint boxes in the religious palette, labeled sparingly (caption-loudness).

## 8. Monzen neighborhoods [standing]

020 patron-temple research: a great temple grows its monzen-machi - the lay commercial
quarter at its gate, open (never walled), fronting the approach the torii face. Hotei's
adjacency to Tokiwa is Tokiwa's bodaiji patronage (adopted canon). **Determined by**:
pilgrim/festival traffic through the gate. **Design**: lay rows front each sovereign
temple's approach; patron temples get modest frontage rows only where ground allows.

## 9. Teramachi backstrip [standing]

The rim temples are part of the defensive belt (019/020 research); the review's deferral:
keep the strip BEHIND them lean - historically the rampart's inner service road and the
temples' own back ground, not housing depth. **Determined by**: the defensive rim function.
**Design**: the backstrip stays open ground/back gardens within a lean bound; a check pins
it so 021's packs cannot silt it up.

## 10. Wind bearing and nuisance trades [new]

Cross-cultural consensus, checkable: stink trades (tanning, dyeing, rendering, kilns) sat at
the town's edge on the side the prevailing wind LEAVES, and downstream of the town's water
draws - Leeds/Newark-pattern collocation of leather+brewing downwind-and-downstream is the
generalized form, and tanneries "on the far end so the wind would not carry the smell" is
the stated period logic; Edo zoned by occupation with the offensive trades at the margins.
China sites cities to drain AWAY (fengshui's practical face) - same downstream logic.
**Determined by**: prevailing wind direction + river flow direction + caste segregation.
**Decision for Shiro Daika (recorded as the knob's worked example)**: continental east-coast
monsoon climate (the /weather analog framework): winter monsoon NW, summer SE; the WINTER
wind is the design wind (fire season, and the stronger, steadier flow). Declare
`wind_from="northwest"`. Nuisance sector = the lee-and-downstream arc: south to southwest,
riverward, BELOW the wharf (river flows NE->SW, so below-wharf is downstream of every draw
point and of the aqueduct intake by construction). The burakumin quarters and tanning yards
(2 + 2 per the counts table) seat in that arc. The knob is `meta(wind_from=...)`; the check
takes the declaration, never guesses. A map declaring no wind seats no nuisance trades -
declaration-existence check per the "a check that never runs" doctrine.

## 11. Wharf kashi fabric [standing]

020 research: Kuramae quay-side kura (the warehouse rows), the fudasashi brokers' row
(merchant, wealth-high - their money builds the theaters), the entertainment district
adjacency, and the internal-dock research's closing promise ("the landing IS the merchant
hub"). Chain order: wharf -> granaries -> brokers' row -> entertainment district.
**Determined by**: cargo flow (warehouses at the landing) and money flow (brokers beside
their ledgers, theaters beside the brokers). **Design matches**: draw in chain order along
the bank-top and the gate street, using existing vocabulary (kura, business rows, theater
stages) plus an entertainment-district grouping.

## 12. Relay stables and the farrier [standing rule, scale confirmed]

The tenma relay system: every post town stabled fresh horses (Tokaido stations at the
36-100 horse standard, lesser roads 25), with the shoeing forge at the stables - the
existing `imperial_road_town_has_farrier` doctrine encodes exactly this, and a domain
capital ON the Imperial road is a relay stop of the largest class. **Determined by**:
Imperial-road traffic volume. **Design**: existing farrier + stables vocabulary near a gate
on the Imperial road axis, at capital counts (stables sized up per the counts-table
"per-gate" scaling); this is the check the whole feature turns green honestly.

## 13. Named machi [decision: not this feature]

Hikone's 53 named wards is the recorded anchor for machi NAMES; naming Shiro Daika's wards
would add ~50 captions to a sheet whose loudness pass exists to REDUCE noise. Decision:
machi names stay un-drawn at map scale (they belong to a future gazetteer artifact, not the
diagram); recorded so the omission is deliberate.

## 14. Perf plan [engineering, not XII]

~2,472 dwellings vs Minami's 541. Method fixed in advance per the skill's CLAUDE.md: build
staged, measure the ONE gen solo (A/B with git stash, not profile seconds), check SeatMemo
re-visit share per caste pass before wiring the memo in (>1/3 re-visits or skip), reconcile
targets to drawable ground BEFORE packing (the unmeetable-target grind is the known failure),
and set the `GEN_TIME_BUDGETS` entry at ~4x the final solo time. Any new scan added by this
feature gets the bbox-prefilter/index treatment from the start.

## Sources (new items)

Nagaya form: [Nagaya (architecture)](https://en.wikipedia.org/wiki/Nagaya_(architecture)),
[Kanazawa Ashigaru Museum](https://visitkanazawa.jp/en/attractions/detail_10056.html),
[Shitamachi nagaya row houses](https://www.wayfarerdaves.com/low-city-living-edo-tokyos-shitamachi-nagaya-row-houses/).
Fire watch: [Edo firefighters](https://www.artelino.com/articles/edo_firemen.asp),
[hinomi-yagura](https://muza-chan.net/japan/index.php/blog/traditional-japanese-fire-lookout-tower),
[jishinban](https://projects.mcah.columbia.edu/jaanus/record/jishinbansho).
Nuisance siting: [medieval tanners](https://hs.imporinfo.com/2026/05/how-medieval-tanners-worked-smell-labor.html),
[downwind trades](http://ravenswing59.blogspot.com/2013/10/medieval-demographics-done-right-pt-ii.html),
[Edo occupational zoning](https://www.cnn.com/sponsor/edition/tmg/built-on-the-past).
Relay stables: [Shukuba](https://en.wikipedia.org/wiki/Shukuba),
[Tokaido](https://en.wikipedia.org/wiki/T%C5%8Dkaid%C5%8D_(road)).
