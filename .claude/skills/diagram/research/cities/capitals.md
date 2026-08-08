# Domain capitals: the research behind the castle-town tier

*The research behind the rules in [`../../settlements/capitals.md`](../../settlements/capitals.md). Findings, anchors and disclosed departures live here so the rule file stays operational; this file is where citations and deeper historical context get added as they accumulate.*

**Load this file when:** you are changing a capital-tier rule, questioning one, or adding to the record - never merely to draw a map.

Every entry: what the research found, the decision it drove, and any deliberate departure from literal reality. Anchors are stable - rules link to them by `#slug`.

---

## At the capital tier Japan leads and China is the tiebreaker

**Grounds:** the whole tier - the castle, the rank-graded samurai rings, the teramachi rim, the ote-suji government avenue

**Evidence:** liberty (a disclosed inversion of the project's standing research order)

**Sources:** `jokamachi-wiki-corpus`, `liufang-yamen`

**The standing rule is China first, Japan as tiebreaker** ([`../../SKILL.md`](../../SKILL.md)). **The capital tier inverts it, and the inversion is recorded here rather than taken silently.**

The reason is that the subject is a *daimyo's castle town*, which is a Japanese institution. The Chinese prefectural seat has a yamen, and sometimes a walled inner citadel, but it has no tenshu, no rank-graded concentric samurai rings, and no teramachi rim - because imperial China had no resident hereditary military aristocracy to house. Its local officials were rotating appointees who lived *in* the yamen.

Where China does have something to say the finding still uses it, and the two agree more often than the inversion suggests - see the nested-citadel and ministry-siting entries below, both of which are `corroborated`. What Japan supplies is the FORM of the tier.

**This disturbs nothing below it.** A village, a county town and a provincial city are all administrative and agrarian settlements where the Chinese reality genuinely is the better guide, and they keep the standing order.

## Both traditions nest a walled citadel in the seat, so a CENTERED castle is the median form

**Grounds:** `castle_seat="ring"` as the default; the concentric quarter doctrine

**Evidence:** attested, corroborated

**Sources:** `jokamachi-wiki-corpus`, `beijing-imperial-city`

**Japan.** A jokamachi was established "with the lord's castle in the center," and the town was zoned in concentric rings by status, closeness to the castle tracking rank:

- **samurai innermost**, "retainers with higher position had a closer location to the castle" (surviving place names *Sange*, *Kamiyashiki-cho*)
- **ashigaru in a middle band** (*Ban-cho*, *Teppo-cho*)
- **merchants and artisans outside the samurai town**, segregated by trade (*Gofuku-machi* drapers, *Kaji-machi* smiths)
- **teramachi at the outer rim**, where "spacious temples formed part of the city defenses"

Two further details drive rules of their own: main roads were deliberately routed past the castle's **front** rather than its rear, "to indicate the glory of the ruler"; and total enclosure of the whole town (*sogamae* - moat plus earth mounds) became increasingly common, Odawara and Osaka being the exemplars. The sogamae is what makes our single-rampart capital honest: a castle town that walls its whole population is an attested form, not a convenience.

**China.** The prefectural seat nested the same way - **yacheng** (the administrative city) inside **zicheng** (the inner city) inside **luocheng** (the outer city). Tang Yangzhou grew its luocheng as the residential and commercial annex outside the fortified zicheng.

**The decision.** The centered castle is not an import we are choosing; it is what both traditions do, so `castle_seat="ring"` is the DEFAULT and the edge castle is the variant.

## The EDGE castle is real, and it comes with water

**Grounds:** `castle_seat="edge"`, and its coupling to `river=`/coast

**Evidence:** attested

**Sources:** `okayama-castle`, `kitsuki-castle`

The cases where the castle sits on a flank rather than in the middle are the cases where a river or the sea does the defensive work on that side:

- **Okayama** - Ukita Hideie diverted a branch of the Asahi River to serve as the moat along the castle's northeastern flank.
- **Kitsuki** - the castle stands on a promontory between the mouths of the Yasaka and Takayama rivers where they open into Morie Bay, with the samurai quarters and temples on the hills around.

**The decision.** The edge mode is COUPLED to water. A dry inland capital takes the ring; a river or coastal capital may take either, and if it takes the edge, the castle's own outer moat becomes that stretch of the city's perimeter rather than a second line inside it. **A castle on a dry edge is refused** - it is not a variant, it is a weak wall.

## A median castle is ~85% of an entire provincial city

**Grounds:** `castle_px2` and its default; the capital's derived wall size

**Evidence:** attested (two anchors), interpolated (the median pick between them)

**Sources:** `hirosaki-castle`, `himeji-castle`

| Anchor | Daimyo | Total enceinte | Notes |
|---|---|---|---|
| **Hirosaki** | Tsugaru, 47,000 koku | **~50 ha / 123 acres** | includes the moats; the keep itself ~0.6 ha |
| **Himeji** | Ikeda, ~520,000 koku | **233 ha / 576 acres**, 4,200 m circumference | 107 ha inside the middle moat; 950-1,600 m E-W by 900-1,700 m N-S |

Himeji also anchors the moat glyph: average width **20 m (66 ft)**, max 34.5 m, depth ~2.7 m. Our provincial-city moat default is 26 px = 78 ft at 3 ft/px, so the same glyph carries to the castle's own moat unchanged.

**The decision.** Take Hirosaki's ~50 ha as the MEDIAN capital's castle:

    50 ha = 123.5 acres = 5.38M sq ft = ~598,000 px^2 at 3 ft/px

Tango's entire walled interior is 701,282 px^2, so **a median castle is ~85% of a whole provincial city**. This is the single most consequential number in the capital budget, and it is why a capital's wall cannot be sized by population alone: the ring encloses roughly four provincial cities of inhabitants plus most of a fifth in castle.

`castle_px2` is therefore a DECLARED program line (the pattern `temple_precinct_px2` set for Minami's eight Fox precincts), defaulting to ~598,000 with the 50-230 ha band documented - so a grand old Clan seat can declare a Himeji and a poor frontier house can declare less.

**THE KEEP IS NOT THE CASTLE.** The ~50 ha is the whole enceinte, every bailey plus all three moats. Hirosaki's tenshu occupies ~0.6 ha, about **1.2%** of the works. Any reasoning that treats "the keep" as the large thing is measuring the wrong object - which is exactly the error the ministry-siting question below turned on.

## Our capital is a Hikone-scale market town carrying a quarter of Hikone's samurai

**Grounds:** the caste inventory; the refusal to copy jokamachi proportions

**Evidence:** attested (the census), setting-canon (the ratio it is compared against)

**Sources:** `hikone-castle-town`

Hikone (Ii, 300,000 koku) counted **15,371 townspeople in 53 separate wards** in the 1695 census - *chonin* only, not the samurai. Our capital holds ~10,800 non-samurai inhabitants against ~1,560 samurai. So the commercial town is ~70% of Hikone's, while the samurai burden is far lighter.

That is exactly the "deliberately restrained echo" `l7r.md` claims - historical castle towns ran 30-60% samurai, and Rokugan's capitals at ~13% "are far more commercial." **The consequence for the map is that we cannot copy a jokamachi's proportions: ours is a merchant city with a castle in it, not a garrison with a market attached.** The samurai rings are real but thin; the machi are the bulk of the fabric.

Hikone's **53 wards** is also the anchor for how many named machi a capital carries.

## The ministries sit OUTSIDE the castle, flanking the approach avenue

**Grounds:** the government ward and the ote-suji avenue; the six `s.ministry` compounds at capital scale

**Evidence:** attested, corroborated

**Sources:** `beijing-imperial-city`, `liufang-yamen`, `nagoya-castle`, `matsumoto-goten`

**Both traditions answer the same way, and the split is by SCALE, not by culture.** The rule in both is: *the ruler's own hall stays inside; the bureaucracy moves out as it grows.*

- **China, county scale** - there are no separate ministry buildings at all. The six *fang* (六房) are **rooms**: "six rooms and three shifts" (六房三班), side halls flanking the yamen's courtyards. Pingyao's county yamen runs 300+ rooms across its courts.
- **China, capital scale** - the Six Ministries become their own compounds, and they line the **Corridor of a Thousand Steps** (千步廊) outside Chengtianmen: flanking the ceremonial approach avenue, OUTSIDE the palace's own walls.
- **Japan, castle town** - the *goten* (honmaru or ninomaru palace) is where the daimyo lived and conducted official business, inside the works. But the offices around it spilled out as they grew: Nagoya kept its **Sannomaru Oyakata** mansions in the third bailey, and at Matsumoto, when the ninomaru proved too small, **the county office and the town office were moved out into the town** (to Rokku town) and the daimyo's conference hall to another.

**The decision.** A government ward outside the castle's outermost gate, the six ministries flanking the *ote-suji* approach avenue. Three reinforcing reasons:

1. It is what both traditions do at exactly this tier - the tier at which the bureaucracy is finally large enough to warrant its own compounds. Given how much of this tier is extrapolation, the answer both anchors converge on is the one to take.
2. It makes the castle's FRONT the map's compositional axis, which is the jokamachi rule above ("main roads deliberately passed through the castle's front side to indicate the glory of the ruler"). A ceremonial avenue with paired ministry compounds is the single most legible way for a map to say *daimyo's seat* rather than *big city*.
3. It keeps the castle interior implied, which is the entire point of the empty-interior treatment, and `s.ministry` works unchanged.

The **domain school** sits on the same avenue: the *hanko* was built in the castle town for the domain's own retainers, so it belongs with the government it serves.

**The retroactive confirmation.** This also explains why our county town is right to hold its whole administration inside the magistrate's manor rather than drawing six offices: at that scale China genuinely has no separate offices, only rooms. The tier ladder - rooms in a manor, then compounds around a yamen, then compounds on a ceremonial avenue - is the same institution growing, not three unrelated conventions.
