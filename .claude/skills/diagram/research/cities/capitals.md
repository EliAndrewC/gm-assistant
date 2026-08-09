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

**Grounds:** `citybudget.CASTLE_PX2` / `CASTLE_HA_MIN` / `CASTLE_HA_MAX` and the castle budget line - **SHIPPED in feature 018**

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

## NEITHER tradition walls its wards: the answer is a MESH of night-barred gates

**Grounds:** the capital's ward structure - pending the GM's decision, this entry is the research they asked for before one is made

**Evidence:** attested, corroborated (independently, in both traditions)

**Sources:** `edo-machi-kido`, `qing-zhalan`, `jokamachi-zoning`, `pingjiang-tu`

The GM's instinct (2026-08-08) was that one large sealed samurai neighborhood is probably wrong and many smaller wards more likely, and asked for real research before deciding. **The research says the instinct is right about the first half and the second half is still not quite the shape of it.** What both traditions actually have is not smaller *enclosures* but a **dense mesh of small gates barred at night**, hung across street and lane mouths, with no continuous fence at all.

**Japan (Edo).** Every **machi** (町) block was closed by a **kido**, open from about 4 in the morning until about 10 at night. Below that, every *nagaya* tenement row and every *roji* lane had its own **roji-kido / nagaya-kido**, locked at roughly 6 pm and reopened around 6 am, with the keys held by the nagaya owner or by trusted neighbors. The system was self-governing - the block was collectively responsible for its own gate - and it is credited with much of Edo's night-time public order.

**China (Ming/Qing).** The Tang walled-ward (*fang*) system was torn down by the Song, and post-Song wards survive only as **name plaques rather than enclosures** (`pingjiang-tu`). What replaced them is the same answer Edo reached: Qing Beijing built **zhalan** (栅栏, palings) closing each street at night against thieves - the commercial street **Dashilan** (大栅栏, "Big Palings") is named for its gate and still carries the name. It was backed by a real curfew: the dusk drum at 8 pm and the dawn bell at 4 am, 40 lashes for being abroad between 9 pm and 3 am (50 in the capital), and barricaded sentry points set up along the major thoroughfares every evening.

**Two traditions, no contact, same institution.** That is the strongest corroboration in this file.

**And the samurai quarter is not ONE quarter.** The jokamachi pattern was for **chonin to live in wards forming narrow strips that SEPARATE different groups of samurai**, those strips running along the major thoroughfares where their trades were most useful to everyone. Within the *buke-chi*, the separation that exists is **per-compound** - "larger compounds separated by walls and gates" - not a district palisade. So a castle town has *several* samurai districts interleaved with commercial strips, each samurai plot walled in its own right.

**What this implies for the tier (recommendation, not yet a decision).**

1. **No continuous ward fence at capital scale.** Replace it with kido at the block and lane mouths - which is the glyph `s.kido` already draws, at a far higher count and a different placement rule. No new vocabulary.
2. **Several samurai districts, separated by commoner strips on the thoroughfares** - not one contiguous sealed quarter.
3. **The walled compound does the sealing**, which dovetails with [the inverted no-manor-inside-the-wall rule](../../settlements/capitals.md#rules-that-invert): a capital's senior retainers live in walled yashiki, and those walls ARE the boundary that a fence was standing in for.
4. **The bell-and-drum tower acquires a documented job.** We already draw one ([`../../settlements/urban-features.md`](../../settlements/urban-features.md)); the curfew above is what it is FOR - it sounds the hour the gates close and the hour they open.

**The honest tension, flagged rather than buried.** The provincial tier currently seals its samurai/government quarter with a continuous palisade (`city_samurai_ward_sealed` and its whole family of checks), justified in [`../../settlements/cities/government.md`](../../settlements/cities/government.md) by the same observation that the Tang *fang* system does not apply. This research says the continuous fence is more than history supports even there. **That is a question for the provincial tier, not a defect to fix in passing** - three shipped cities depend on those checks, and the capital can adopt the mesh without the provincial maps changing at all. Raise it with the GM separately.

## The capital's samurai are SENIOR-heavy, which INVERTS the provincial housing mix

**Grounds:** the capital's samurai housing variation; the (corrected) retainer-terrace expectation

**Evidence:** setting-canon

**Sources:** budgets.md, "Samurai rank distribution"

Working the capital column of budgets.md's rank table, against the provincial column:

| | R5+ (senior) | R1-4 (junior) |
|---|---|---|
| **Capital** (800 working) | 563 - **70%** | 237 - **30%** |
| **Provincial city** (225 working) | 61 - **27%** | 164 - **73%** |

**The mix does not scale, it inverts.** budgets.md says so in words too - the capital "is staffed with the senior cohort," and "low-rank samurai compose a lower proportion of retainers in the capital than in the provinces" - because a capital posting is prestigious even when the job is menial, and because the capital absorbs the rank-by-association cohort (the Doctrine of Three Steps puts the daimyo's kin at Rank 9+ holding no office at all).

**The consequence for the map.** `city_samurai_housing_varied` wants a MINORITY of large senior houses among many small junior ones, which is right for a provincial city at 27% senior. At capital scale that flips: roughly **~218 senior against ~94 junior households** of the ~312 total, so large houses and walled yashiki are the MAJORITY of the samurai fabric and the small houses are the minority.

**This is also what corrects a modeling error made on 2026-08-08** and caught by the GM. The first draft of the capital program expected "ashigaru terraces" - dense uniform rows of low-rank warrior housing, on the historical *kumi-yashiki* pattern. That was wrong twice over:

- **Wrong caste.** budgets.md is explicit that **in Rokugan ashigaru are PEASANTS, not samurai** - "the original L5R usage, which departs from historical Japan, where ashigaru formed the lowest stratum of the samurai class." The historical *kumi-yashiki* housed the lowest *samurai*, so the institution has no Rokugani counterpart under that name.
- **Wrong place, and wrong quantity.** l7r.md puts ashigaru in the villages - about 10% of farmers, licensed or unlicensed, trained by the county magistrate. They are rural peasant militia, not a resident urban caste, so a capital has no ashigaru quarter to draw. And the slot they would have filled is the one the rank table shows is *smallest* here, not largest.

What genuinely occupies that structural position is a **retainer terrace**: modest housing for the capital's ~94 junior (Rank 1-4) samurai households - castle guards, household retainers of the daimyo's retinue, and junior officials in training. A real feature, correctly named, and a minority texture rather than a dominant one.

## The aqueduct is OPEN outside the wall and BURIED inside it - and the boundary is the gate

**Grounds:** the capital's aqueduct; the retained well network

**Evidence:** attested

**Sources:** `edo-josui`, `kanda-kakehi`

The GM's preference (2026-08-08) is for an above-ground aqueduct where the history allows one, because it makes a better map - but asked for the possibility space first. **The space is real and generous, and it has a sharp boundary in a surprising place.**

The Edo *josui* is two systems with the **city gate** between them:

- **OUTSIDE, an open channel.** The Tamagawa Josui runs ~43 km from Hamura to the Yotsuya Gate (*Yotsuya Okido*) as an open cut "excavated without timbering" - an earth canal, entirely above ground, terminating AT a gate of the city.
- **CROSSING a watercourse, an open flume on a bridge - the *kakehi* (懸樋).** Where the Kanda Josui had to cross the Kanda River at Ochanomizu it was carried over on a flume; the bridge downstream is called **Suidōbashi**, "aqueduct bridge," for exactly that reason, and Hiroshige drew the crossing in *Famous Places of the Eastern Capital: Ochanomizu*. This is the single most visually striking element in the whole system and it is fully attested.
- **INSIDE, buried conduit.** Within the city the water runs in **stone (*sekihi*) and wooden (*mokuhi*) pipes laid underground** - ~67 km of them in Edo - feeding **over 3,600 draw-wells** (*jōsui ido*) and cisterns from which residents drew as they needed. The wooden pipe work was specialist enough that ship's carpenters were the trade that laid it.

**No arcades.** There is no East Asian equivalent of the Roman arcaded aqueduct. The vocabulary is: gravity canal at grade, buried pipe, and a flume bridge only where a watercourse must be crossed. **Do not draw arches** - that is the one form the possibility space excludes.

**Why the inside is buried** (inference, not attested): a dense wooden city needs its street surface, and open water threaded through the fabric is both an obstruction and a contamination problem. The boundary is functional, not arbitrary.

**The decision.** Draw it above ground wherever history put it above ground - which is most of its interesting length, and all of its drama:

1. the **intake works** on the river,
2. the **open approach canal** running to the wall,
3. a ***kakehi* flume** where it crosses a watercourse, if the geography gives us one,
4. its **terminus at a gate**.

Inside the wall the system is honestly buried, and it is represented by what a resident would actually see: **its draw-points**. Those are wells, which we already draw - so the recommendation is a distinguishable aqueduct-fed draw-basin rather than a fake surface channel. The existing well network does not go away; the aqueduct is laid on top of it.

## The wharf is the COLLECTING end, and "kurayashiki" is the wrong word for it

**Grounds:** the wharf and tax-rice warehouse district; the domain granary

**Evidence:** attested, with one flagged divergence from setting canon

**Sources:** `osaka-kurayashiki`, `asakusa-kuramae`, `kuramai`

**The correction first, because it was in our own draft.** A ***kurayashiki*** (蔵屋敷) is a daimyo's warehouse-and-residence **at the market** - Osaka, around Nakanoshima, more than 110 of them at the early-1800s peak - where tax rice was auctioned to brokers against tradeable rice bills. By 1700 virtually every western daimyo shipped tax rice there. **That is the SELLING end, and a domain capital is not it.** Calling Shiro Daika's waterfront a kurayashiki district would be wrong twice: wrong word, and wrong economic role.

**What a domain capital actually holds.** Peasants pay tax rice up to the **domain granary**, and the domain pays its samurai their stipends out of it (***kuramai***, the rice stipend). So the capital is the **collecting-and-disbursing** end: rice arrives from the provinces, most of it goes straight back out as stipends, and the surplus ships downriver to the market.

**The model to copy is Asakusa Okura / Kuramae.** The shogunate's own rice granaries stood on the Sumida, and the district in front of them is literally named **Kuramae** (蔵前), "before the storehouses." There sat the ***fudasashi*** - brokers who warehoused stipend rice for a fee, converted it to cash, and lent against it, becoming rich enough that the theaters and geisha houses of neighboring Asakusa grew up on their money.

**That gives the capital a chain of three features linked by one mechanism**, which is the sort of thing that makes a map read as a real place:

    river wharf -> the domain granary -> the brokers' row in front of it -> the entertainment district next door

**The flagged divergence, which is the GM's call and not mine to invent.** In Edo the arbitrage between rice and coin made *chonin* brokers rich. In L7R, budgets.md hands that income to the **Ministry of Retainers** - "~1,600 (rice/coin arbitrage on capital stipend throughput of ~28,000)" - a samurai ministry, not a merchant street. So our brokers' row may be a ministry annex rather than a commercial quarter, and if it is, the Edo causal chain from broker wealth to the entertainment district weakens. The two can coexist (the ministry takes the denomination cut; merchant brokers still trade), but which one the map depicts changes what is drawn there. **Ask before building it.**

**The Emperor's granaries are separate**, and their siting is an inference. budgets.md gives the Imperial Magistrate a ~450-koku line for "local Imperial granary supervision," with "separate granary staff, materials, and operations," so they are distinct stores under a foreign authority - but nothing in the sources says where a capital would put them. Adjacent to the Imperial Magistrate's compound, or with their own water access, are both plausible; pick one and record it as a choice rather than a finding.

## Per-household ground costs for the two housing types the budget model has never seen

**Grounds:** `citybudget.C_YASHIKI`, `citybudget.C_TERRACE`, `CAPITAL_RANK_BANDS`, `CAPITAL_SAMURAI_INWALL_FRAC` - **SHIPPED in feature 018**, and both constants remain PROVISIONAL pending re-derivation against the first drawn capital

**Evidence:** attested (both size anchors), interpolated (the gross-up ratios, measured from the pool)

**Sources:** `fukui-bushi-jutaku`, `shibata-ashigaru-nagaya`, `matsue-bukeyashiki` - all three already cited by [`government.md`](government.md)

`citybudget.py` prices exactly two kinds of dwelling: `C_PACKED` (690 px^2 gross, a row house) and `C_SPACED` (2,480, a detached samurai house). A capital adds two more, and without rows for both the derived wall is wrong in the direction hardest to notice.

**The gross-up ratios, measured from the three shipped cities** (drawn footprint -> the model's gross cost, which is footprint plus its share of eaves, roji and margins):

| | measured drawn footprint | model gross | ratio |
|---|---|---|---|
| packed row (caste-weighted) | 124 px^2 | `C_PACKED` 690 | **5.6x** |
| samurai house (75/25 junior/senior) | 330 px^2 | `C_SPACED` 2,480 | **7.5x** |

The spaced ratio is the higher one, which is the model working correctly: a detached house in a yard wastes more ground per roof than a party-wall terrace.

**`C_YASHIKI` - the walled samurai compound inside the wall.** The anchor is already in our own research: the Fukui archive's **Suginuma plan** (a 1,000-koku retainer, 1839) is a **28 x 32.5 ken plot = ~167 x 194 ft**, which at 3 ft/px is **3,600 px^2**. That is a PLOT, so it already contains its own yard - the walled perimeter IS the boundary, so it carries far less shared-margin overhead than a detached house. Applying only a modest ~1.15x for street margin:

    C_YASHIKI ~= 4,150 px^2

Sanity checks against things we already draw: 1.7x an ordinary in-wall samurai house's gross (right for a chancellor against a bushi), 1.3x the drawn merchant-estate court (2,852 px^2, 0.59 acre - right for a chancellor against a very rich merchant), and comfortably under the extramural country manor (~4,900 px^2, ~1 acre), which has land a city plot does not.

**`C_TERRACE` - the retainer terrace.** The anchor is likewise ours already: Shibata's ICP *ashigaru-nagaya* is **8 households under one roof, 143 x 21 ft, 18 ft of frontage each** = 378 sq ft per household = **42 px^2**. But that is the *lowest* stratum, and our retainer terrace houses **Rank 1-4 samurai** - poor, but a band reaching 16 koku at the top. It should therefore sit above the historical ashigaru unit and below the detached samurai house (2,322 sq ft drawn, which matches the Matsue mid-rank residence's ~220 m^2 almost exactly). Taking ~110 px^2 drawn (~990 sq ft, just above our laborer row house at 891) at a row-housing gross-up:

    C_TERRACE ~= 660 px^2

**Confidence, stated honestly.** Both SIZE anchors are attested and measured. The two DERIVED constants are interpolations, and **`C_TERRACE` is the softer of the two** - it is bracketed by real numbers at both ends but its position between them is a judgment. `C_YASHIKI` rests directly on a measured plan and is firmer. Both should be re-derived against the first capital's drawn map, exactly as `C_PACKED`/`C_SPACED` were back-predicted from Tango.

**What it makes the wall.** Pricing the capital inventory with these rows - 2,160 packed households, a samurai cohort split by rank into ~60 walled yashiki / ~160 detached / ~94 terraced, the ~598,000 px^2 castle, ~180,000 of expanded civic program, and the 7% circulation fraction - gives a required interior of **~3.2M px^2** and a derived ring of about **rx 1,056 / ry 982 px**: roughly **1.2 x 1.1 miles across, a ~3.6 mile circuit**. Two consequences worth knowing before the feature starts:

- **The existing 3,200 x 2,700 canvas still fits it** (it needs ~2,412 x 2,264 including the moat-and-margin clearance), so no canvas change is required.
- **`plan_city` will refuse it outright.** `POP_MIN, POP_MAX = 2000, 4000` raises rather than clamping - correctly, since it says capitals are a future tier - so the capital tier needs its own band and its own caste table, not a widened provincial one.

**One knob this exposes.** `SAMURAI_INWALL_FRAC` is 2/3 for a provincial city, the rest holding extramural estates they commute in from. A capital should run HIGHER - proximity to the daimyo's court is the whole point of the posting, and the walled yashiki is what makes staying in-wall attractive to exactly the senior cohort that would otherwise build outside. ~0.85 is my estimate; it is a guess, and it moves ~40 households of the priciest housing type, so it is worth the GM's eye.

## The brokers' row is MERCHANT, and the ministry's cut is narrower than it looks

**Grounds:** the wharf brokers' row; the entertainment district's siting

**Evidence:** setting-canon (GM ruling), corroborated by the Edo pattern

**Sources:** `asakusa-kuramae`, budgets.md "Domain ministry budgets"

**GM ruling, 2026-08-08.** The brokers' row is a **merchant** quarter, not a Ministry of Retainers annex - and the reason is a distinction the budget line does not spell out on its face.

budgets.md credits the Ministry of Retainers with "~1,600 (rice/coin arbitrage on capital stipend throughput of ~28,000)." **That figure covers the PAYING of stipends only** - the denomination decisions, the rice-versus-coin split, the payment-day logistics that the ministry administers. It is not a general franchise over rice finance. Everything else - the contracts, the clearinghouse business, the lending against next year's stipend, the arbitrage a samurai household does on its own account - sits outside it, and **the merchant class has grown rich on that in Rokugan exactly as the *fudasashi* did in Edo.**

So the Edo causal chain survives intact, and with it the reason the entertainment district belongs beside the granary: **the brokers' money is what builds the theaters.** Draw the row as merchant frontage - shops and merchant houses, with the wealth band skewed high - not as state violet.

**Why this matters beyond one row of buildings.** It resolves an apparent conflict between setting canon and the historical model without weakening either, and the resolution is a general one: *a ministry line item in budgets.md prices the ministry's own administrative function, not the whole economic activity that function touches.* Read another ministry's "informal income" line the same way before concluding that a trade is state-run.

## The Emperor's granaries are separate, because they face a different THREAT

**Grounds:** `imperial_granary_seat` (proposed knob); the Imperial Magistrate's compound

**Evidence:** setting-canon (GM ruling), reconstruction (the siting)

**Sources:** budgets.md "Imperial magistrates and their staff"

**GM ruling, 2026-08-08**, and the reasoning is a threat model rather than a plan:

> The Emperor's granaries do not need to be as guarded as the daimyo's, because an invading neighbor would be unlikely to attack the Emperor's granaries. They need protection from brigands, not from besiegers.

That single distinction settles what was otherwise an arbitrary placement. The daimyo's siege stock has to be inside the castle because a siege is exactly what it is for; the Emperor's stores face **theft, not investment**, so a stout wall and a watch is sufficient and there is no reason to spend castle ground on them. **They therefore sit outside the castle, as their own modest walled compound.**

Where that compound goes is a **tunable knob**, because both plausible sitings are real answers and different cities will have made different choices:

- **beside the Imperial Magistrate's compound** - the official who oversees them is right there, which is the administratively obvious arrangement; or
- **on the water** - granaries want the wharf, since grain arrives and leaves by boat.

Proposed as `meta(imperial_granary_seat="magistrate" | "wharf")`, with neither as a strong default. This is the same shape as the castle-seat knob: a genuine either/or that gives two capitals different skeletons for a documented reason rather than a die roll.

## A river gets a TOWPATH, not a road - and they are not the same feature

**Grounds:** the riverside way at a river capital; the wharf district's landward edge

**Evidence:** attested, corroborated (by opposite reasoning in the two traditions)

**Sources:** `shaoxing-towpath`, `edo-river-transport`

The GM asked (2026-08-08) whether a road would run along the river, or whether the river replaces it. **Three different features get confused under "riverside road", and only two of them belong.**

**1. A trunk road paralleling the river: NO.** Water carried bulk far more cheaply than any cart, so a highway shadowing a navigable river is redundant - the river IS that route, and the road network exists to reach what the water does not. Japan makes the point at its sharpest: roads there did not follow rivers, and at the Oi-kawa on the Tokaido **bridges and ferries were deliberately PROHIBITED** so the river would serve as a checkpoint delaying an invader. A road meets a river to cross it, not to accompany it.

**2. A TOWPATH on one bank: YES - and this is the real riverside way.** The Chinese ***qiandao*** (纤道) is ancient and substantial: Shaoxing's, on the Eastern Zhejiang Canal, dates to **815 CE** and runs **over 40 km**; Marco Polo saw barges hauled along it by teams of horses. Its form is worth knowing because it is not road-shaped - it comes in two kinds, one on the bank as expected, and one built **out in the water parallel to the bank**, slab stones laid on stone piers about half a metre above the surface.

**What determines it**: upstream haulage. A towpath exists *because* of the boats, not instead of them - downstream traffic drifts, upstream traffic is pulled. So it **supplements** water transport, which is exactly the GM's intuition, and it is narrow, single-bank, and goes only where the boats go.

**3. A quay street inside the city (河岸, *kashi*): YES, but it is wharf frontage, not a route.** It serves the dock, the granary and the brokers' row; it belongs to the wharf district and is already in that program.

**The decision.** A river capital draws a **towpath** on the wharf's own bank - a narrow hauling path, drawn distinctly from a road (no roadbed, no dashed lane centerline), running to the wharf and no further - plus the quay frontage inside the wall. It does **not** draw a trunk road paralleling the river. The domain's overland roads leave in the directions the water does not serve, which for Shiro Daika is exactly what the GM's road list already says: east to the Fox lands and southwest into the domain, with the Imperial road running north-south.

**A drawable option held in reserve**: the piers-in-the-water towpath is a striking, genuinely attested form. It is not the default - the bank-side path is the common case - but it is available for a capital whose bank is too steep or too built-up to carry one.

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

## Wall geometry: rectangles and terrain loops - the circle is the form BOTH anchors decline

**The question that prompted this** (GM 2026-08-09): should the castle enceinte - and by
extension the governor's mansion - be rectangular or rounder? The working assumption was: small
compounds (magistrate manors, governor mansions, country estates) rectangular; large enclosures
(provincial-city walls, capital walls, castle walls) more circular.

**The finding: the assumption holds for small compounds and INVERTS for large walls.** In both
anchor traditions, enclosures stay rectilinear or go terrain-irregular as they grow. They never
become circular BY DESIGN - a bigger wall in East Asia is a bigger rectangle or a longer terrain
loop, not a rounder ring.

- **China: square at EVERY tier, by cosmology and by formwork.** The Kaogongji's ideal capital
  is a square, three gates a side, nine crossing streets, the palace at the center - and the
  cosmology behind it is explicit: **round heaven, SQUARE earth**, so a wall (a thing of the
  earth) takes Earth's shape. The built record follows the ideal from county seat to imperial
  capital - Chang'an, Ming Beijing, Xi'an, Pingyao, Suzhou are all rectangles - so the shape is
  RANK-INDEPENDENT: a bigger administrative seat gets a bigger rectangle, never a rounder one.
  Deviation comes from TERRAIN, not from size: Nanjing's 35 km Ming circuit bends around its
  lakes, hills and river frontage, and is "circular" only in the closed-circuit sense of the
  word. The yamen and every government compound inside are strictly rectangular and axial.
- **Japan: angular masonry inside, a terrain loop outside.** A castle's nawabari adapts its
  baileys to the ground (the rinkaku/teikaku/renkaku taxonomies are all polygonal-irregular),
  the ishigaki runs in straight revetted segments with hard corners carrying yagura, and a
  tenshu's base is rectangular. The plains castles our capital resembles (Nagoya, Osaka, Nijo)
  approach clean rectangles. The town's own enclosure, the sogamae, is the OTHER shape: Odawara's
  9 km circuit runs from Mount Hachiman to the sea in a horseshoe - an organic terrain-following
  loop, neither square nor circle.
- **The military logic, and why East Asia never needed the circle.** A corner is the weak point
  of a curtain (dead ground at the angle, a miner's favorite target), and Europe cured that by
  CURVING - round flanking towers, shell keeps, and the organic ovals of medieval town walls.
  East Asia cured the same problem by FLANKING instead: Chinese walls carry mamian ("horse-face")
  bastions and corner towers on straight curtains, Japanese walls carry corner yagura and
  masugata gate courts - because hangtu rammed-earth formwork and ishigaki masonry both want
  straight runs, and the cosmology wanted the square anyway. Same problem, different cure, and
  the cure is why big East Asian walls stay angular.
- **The attested circles, and why neither is our case.** Shanghai's 1553 county wall was
  genuinely round - thrown up in one season against the wokou pirate raids, and a circle
  encloses the most area per foot of wall, so the round wall is the SPEED-AND-ECONOMY form, not
  a prestige form. The Hakka tulou are round communal fortress-HOUSES (a clan under one roof,
  wedge apartments with no hierarchy and no weak corner) - and even tulou are as commonly
  rectangular. Both are emergency/communal forms from the empire's margins; neither is how a
  daimyo's seat or a governor's city announces itself.

**Decisions:**

1. **The castle enceinte stays RECTANGULAR** - the drawn form is confirmed, not merely kept. A
   round keep would be reading European castle grammar into an East Asian map.
2. **Every government compound stays rectangular** - yamen, magistrate manors, governor
   mansions, lineage yashiki, country estates. The GM's working assumption for small compounds
   was correct, and nothing changes.
3. **Our city walls draw as ~elliptical polygon rings** (Tango, Nagahara, Minami, Shiro Daika) -
   now recorded as a disclosed HOUSE STYLE rather than a researched form. Of the attested
   shapes it sits closest to the Japanese sogamae terrain loop (an organic closed circuit), and
   furthest from the Chinese square. If a future map wants the China-first form, the grounded
   options are the rectangle (flat open ground) or an irregular terrain-following loop (river or
   hill ground) - not a truer circle. Reshaping the four shipped cities would re-roll the pool
   and is a GM decision to make deliberately, not a drift to make silently.

## The chancellery meets IN the castle - executive out, council in

**The question** (GM 2026-08-09): would the House Chancellery actually have its own meeting
building outside the castle? The GM's working assumption was that chancellery meetings happen in
the castle itself - and feature 020 had drawn a chancellery compound on the government avenue.

**The GM's assumption is right, and both anchors agree.** In Edo, the Hyojosho (the supreme
judicial council of the Roju and commissioners) sat WITHIN Edo castle, and the Roju - the
shogunate's governing council - worked from the castle's own offices; a daimyo's karo council
met in the goten's audience halls. In China the Grand Secretariat (neige), the emperor's
council-of-state, sat INSIDE the palace precinct, while the Six Ministries stood outside on the
approach. The split both traditions converge on is clean: **the EXECUTIVE bureaus (clerks,
archives, public business) stand outside the works; the ruler's COUNCIL meets beside the ruler,
inside.** A deliberative body of 5-10 lineage representatives generates no street traffic and
holds no archives of its own - it is a chamber, not a compound.

**Decision:** the House Chancellery compound came OFF the map; the council chamber is part of
the castle's implied goten (never drawn, per the blank-castle doctrine). The check inverted with
it: `capital_chancellery_meets_in_the_castle` now fires if a chancellery compound is drawn
outside. The inventory table in `settlements/capitals.md` moves the chancellery inside.

## Moat water: drawn connections outside, standing water inside - and yes, it scums

**The questions** (GM 2026-08-09): does the inner (castle) moat need to connect to anything?
How is the water kept in, and kept from stagnating? And why was the CITY moat not simply
connected to the river, as Minami's and Nagahara's are?

**The city moat: river-fed flow-through, and the connection is drawn.** Japanese wet moats
filled from whatever water stood nearest - rivers and streams most commonly, wetlands and lakes,
even the sea (Takamatsu's moat is seawater and its fish are ocean fish; Imabari's mixes tidewater
with springs rising inside the moat itself) - and moat water was USED: drawn for irrigation,
managed for flood control, boated for commerce. Minami and Nagahara back onto their rivers, so
their moat FEET are the connection and nothing extra needs drawing. Shiro Daika's ring stands
~200 px off its bank, so the connection is a pair of engineered channels, now drawn - and the
first cut got them WRONG twice, which the GM's eye caught: a 48 ft thread of a leat, tapping
the river at its CLOSEST approach (southeast). Closest is not upstream: with the land falling
NE -> SW, water entering at the low southeast corner cannot climb the east arc, so the whole
northern ring would have been a dead arm. And the thread read nothing like the pool's own
precedent - TANGO, the other stand-off closed ring, takes moat-width (66 ft) feeder and outfall
channels, so the moat reads as flowing through. The corrected form: a 66 ft sluiced feeder taps
the river's HIGH upstream reach and feeds the ring's northeast arc, the water descends BOTH
ways round the circuit, and the 66 ft drain leaves the low southwest arc for the fields - moat
water irrigating the land below is attested use, and river -> moat -> fields runs downhill the
whole way. The
gate learned one rule for this: a stream may ROOT on the trunk river (`stream_runs_off_edge`'s
river-tap clause) - the river is itself edge-sourced, so a leat rooted on it has a real source.

**The castle's inner moat: standing water, and that is period-accurate.** An inner moat dug
below the water table holds groundwater and rain; springs rising in the moat bed (Imabari's do)
keep some circulation, and hillside castles sectioned their moats with low dams into stepped
pools. There is no underground aqueduct feeding it - a besieged castle wants water that cannot
be cut off, which is exactly what groundwater is. Keeping it IN is the easy half (the moat floor
sits below the table; earthen moats hold water the way any pond does). Keeping it CLEAN mostly
did not happen: duckweed, algae and pond scum on a quiet moat are the historical look - Edo's
surviving moats bloom green to this day - managed only by occasional dredging (the same sarae a
canal got) and by the carp everyone kept in them. So the inner moat connects to NOTHING, and a
GM describing it as still, green-skinned water with fat carp under the lilies is being accurate,
not unflattering. Nothing to draw; recorded so nobody "fixes" it later.

## The aqueduct supplies the CITY - the moat spill was a drawing artifact

**The question** (GM 2026-08-09): the aqueduct exists because a capital outgrows its wells, but
the drawn cut appeared to feed the city moat instead of supplying the city. Which is it?

It supplies the city - the confusion was the terminus rendering, not the design. The system is
Edo's: OPEN cut outside the wall, BURIED pipe inside it, the GATE as the boundary; what a
resident sees inside is the draw-basins (feature 021's, with the wells). The open cut therefore
ENDS at the gate by design, and the first rendering just stopped there - which read as a brook
dribbling into the moat. The fix is the historical furniture: a TERMINAL BASIN (head-tank) at
the gate end, the settling tank where the open cut hands off to the buried pipe - Edo's josui
ended in exactly such tanks. The glyph now draws it, standing clear of the moat. (Any real
josui also spilled surplus somewhere, and the moat is where a surplus WOULD go - but the drawing
should say "supply enters here", not "stream joins moat".)

## The domain school is the hanko: a school of letters WITH the martial wing

**The question** (GM 2026-08-09): is the "Domain School" an office-like building (ministry
glyph) or the capital equivalent of the provincial martial hall?

Both, because that is what a hanko WAS: a school of LETTERS first, with a martial wing
(bugeijo) on the same grounds - Aizu's Nisshinkan, Mito's Kodokan and Kagoshima's Zoshikan all
pair lecture halls with fencing floors and an archery range. The provincial "martial hall" this
engine already draws is exactly that martial wing at the tier below (cities/government.md); the
capital shows the whole institution. **Decision:** a dedicated `s.hanko` glyph - the
martial-hall vocabulary (state violet, dojo hall with kamiza, archery lane with azuchi) plus
the larger civil lecture hall - recorded in `M['martial_halls']` with `kind='hanko'`, replacing
the ministry box the first draft used.

## Why the temples belt the wall instead of clustering in a temple quarter

**The question** (GM 2026-08-09): why seven temples strewn through the city rather than two
main temples plus smaller ones in a temple neighborhood?

The structure IS "two main + the rest" - the two sovereign temples (Benten, Jurojin) are the
capital's great complexes, flanking the government axis at equal offsets, and the five modest
halls are the "everything else." What differs from the provincial pattern is WHERE the rest
stand: belted along the rampart's inner face as a teramachi rim, not gathered into one
neighborhood. That is the attested CASTLE-TOWN pattern, and it is defensive: a jokamachi
deliberately placed its temple districts along the perimeter and the approaches, because temple
precincts are the town's only large walled compounds outside the castle - each one a ready-made
strongpoint and muster ground covering a stretch of wall, and their graveyards and groves a
firebreak. A provincial city clusters its temples into a lane (Nagahara's temple neighborhood)
because it has only a few and they serve street life; a capital has enough to spend them on the
defenses. The rim is the settled 018 decision (settlements/capitals.md, "Placements that
change") - recorded here at full length because the question deserved the reasoning, not a
pointer. If the GM prefers a gathered temple quarter anyway, that is a one-session re-seat and
the checks do not currently care - say the word.

## Street widths: the ote-suji is a grand street, not an imperial boulevard

**The question** (GM 2026-08-09): is the width of the avenue into the castle realistic? "It
looks huge."

It was huge, for two stacked reasons. The honest one first: the engine's convention is REAL
FEET through `lw()` - `s.road`'s default is `lw(26)`, 26 ft, the Tokaido's own width - and the
first draft passed the ote-suji `width=32` in raw PIXELS, which at 3 ft/px drew a 96 ft
boulevard, nearly 4x the Imperial highway beside it. A unit slip, not a decision.

The researched band, once the units are honest: Edo's post-Meireki street plan - the SHOGUN'S
million-person capital - made Honcho-dori 13.8 m (~45 ft) and Nihonbashi-dori 18.2 m (~60 ft),
and those were its grandest ordinary avenues; the wider hirokoji were firebreaks, not streets.
The truly vast processional ways (Heian-kyo's 84 m Suzaku-oji, Chang'an's ~150 m Suzaku Avenue)
are the ancient CONTINENTAL-capital form - the Chinese cosmological city - and no jokamachi
ever built one. So a domain capital's ceremonial approach sits at the Honcho class: **45 ft**,
half again the 26 ft highway it meets - grander by proportion, not by absurdity. The map now
draws exactly that (`width=s.lw(45)`), with the ministry files pulled in to a ~21 ft setback so
they front the avenue like a corridor instead of floating beside a runway.

**The transferable rule:** pass `s.lw(real_ft)` to every way's width, never raw pixels - the
default's docstring already cites its source, and any hand width should be able to as well.

## Dimensional audit of the drawn capital (GM-prompted, 2026-08-09)

**The question**: are the ministries, lineage estates, walls, river and the rest realistically
sized? Every drawn family converted at 3 ft/px and checked against its anchor. One feature
failed and was fixed; the rest hold.

| feature | drawn | anchor | verdict |
|---|---|---|---|
| wall ring | 6,174 x 5,742 ft (1.17 x 1.09 mi, ~3.6 mi circuit) | the 018 budget's own prediction (~1.2 x 1.1 mi), Hikone-anchored | HOLDS - the budget is the anchor |
| castle | 2,550 x 2,100 ft = 49.7 ha | the declared castle_px2 line, researched band 50-230 ha | HOLDS (low end = median form) |
| city moat 66 ft / castle moat 80 ft | | researched in `castle()`: a castle moat outranks the city's ~66 ft | HOLDS |
| river | 120 ft | `river()`'s researched default ("a serious provincial river") | HOLDS |
| ministries | 224 x 148 ft each | the provincial research (`cities/government.md`) - "a capital does not get a bigger yamen" (018) | HOLDS |
| grand lineage estates | 1.29-1.61 ha | Edo kami-yashiki of small daimyo: ~2,500-7,000 tsubo (0.8-2.3 ha) | HOLDS, mid-band |
| kurogi estate | 0.76 ha (~2,300 tsubo) | upper-hatamoto class - a chancellor housing few | HOLDS |
| modest lineage houses | 0.32-0.37 ha (~970-1,120 tsubo) | the Suginuma 1,000-koku plot (0.30 ha) - C_YASHIKI's own anchor | HOLDS, dead on |
| Imperial Magistrate | 300 x 225 ft = 0.63 ha | Ubame's county magistracy manor (360 x 216 ft = 0.72 ha); ~68 staff + family | HOLDS - same institutional class |
| sovereign temple halls | 150 x 100 ft | the shrine_hall guard's researched kondo ceiling (largest real main halls ~150-190 ft) | HOLDS |
| granary kura | 60 x 36 ft per store | the town granary research (58 x 34 family) | HOLDS |
| ote-suji 45 ft / roads 26 ft / ring 20 ft / brokers' lane 24 ft | | Honcho-dori / Tokaido / patrol-lane conventions | HOLDS (see "Street widths") |
| towpath 8 ft | | Shaoxing's stone qiandao ~5-6.5 ft; ours carries horse teams | HOLDS, upper band |
| aqueduct cut 10 ft | | josui earth cuts ~1-3 ken (6-18 ft) | HOLDS, mid-band |
| moat feeder leat 48 ft | | Tango's 66 ft feeder; moat-class water | HOLDS |
| jetties 60-66 ft | | Nagahara's wharf convention | HOLDS |
| **hanko** | **was 240 x 150 ft = 0.33 ha** | attested band: Choshu's FIRST Meirinkan 940 tsubo (0.31 ha, 1718) -> Nisshinkan 2.65 ha -> rebuilt Meirinkan ~5 ha | **FAILED - bottom of the band** for a schooling-magnet capital of a ~200k-koku-class domain; **fixed to 400 x 260 ft (~1 ha, ~3,000 tsubo)** - mid-band, half Nisshinkan, without claiming its fame |

**The method note worth keeping**: most sizes held because they were INHERITED from already-
researched anchors (the budget, the provincial ministry, C_YASHIKI, the glyph guards). The two
that failed at this tier - the ote-suji and the hanko - were both NEW hand-set numbers with no
anchor cited at the point of use. A size that cannot cite its anchor is the one to audit first.
