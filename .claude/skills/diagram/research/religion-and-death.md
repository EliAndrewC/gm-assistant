# Religion and the dead: the research behind the shrine, torii and funerary rules

*The research behind the rules in [`../settlements/religion-and-death.md`](../settlements/religion-and-death.md). Findings, anchors and disclosed departures live here so the rule file stays operational; this file is where citations and deeper historical context get added as they accumulate.*

**Load this file when:** you are changing a religious or funerary rule, a size, a count or a check threshold - or you want the historical basis before overriding one. Not needed to simply DRAW these features.

Every entry: what the research found, the decision it drove, and any deliberate departure from literal reality. Anchors are stable - rules link to them by `#slug`.

---

## City temple size - the deliberate L7R liberty

**Grounds:** the ~15-30 monks per provincial-city complex

**Evidence:** attested, liberty

**Sources:** not recorded - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

Historically the median temple was **tiny**: Edo Japan ran 90,000+ parish temples at 1-2 priests each, and small hereditary Chinese temples held a handful of monks; only the famous pilgrimage complexes ran large (the great Song public monasteries several hundred, Daxiangguo and Shaolin 1,000+). **L7R deliberately over-sizes - every city temple is a major complex** in a way history would usually lack. A **provincial city** (~3,000 inhabitants) has **~15-30 monks per complex** (a serious Ming urban monastery's scale); a **domain capital** (~12,000) has **~50+ monks per complex**. That puts clergy at ~1-2% of city population against the historical ~0.2-0.4% (Song China) - a deliberate **2-5x density**, softened in-world by the temples serving the whole province's worship, not just the walled city.

## Many modest temples per walled city is the historical norm

**Grounds:** the eight-precinct Fox temple program (Minami); `city_multi_temple_exception_declared`; `CityProgram.temple_precincts` / `temple_precinct_px2`

**Evidence:** attested, corroborated

**Sources:** `kanazawa-teramachi`, `takada-teramachi`, `takayama-teramachi`, `jokamachi-wiki`, `pingyao-chenghuangmiao`

*What determines it in reality:* patronage and institutional history. Each temple is a separate FOUNDATION with its own patron, sect and endowment, so temple count tracks how many distinct patrons a place has accumulated - which is why it does not scale smoothly with population.

*What the research found.* The expectation going in was that eight temples in a 2,600-person seat would need a disclosed liberty. **The opposite is true.** Japanese castle towns concentrated their temples into a designated *teramachi* at the outer rim of the jokamachi, where the spacious precincts formed part of the city defenses: **Kanazawa ~70**, **Kyoto ~80**, **Takada ~25 relocated in one 1614 wave**, and - the size-matched anchor - **Takayama, a SMALL castle town, "over 10 temples and shrines"**. On the China side the standard Ming county-seat kit carried the Confucian school-temple (*wenmiao*) and the City God temple (*chenghuangmiao*) as separate mandatory foundations before any Buddhist or Daoist house was counted, and Pingyao's City God temple is itself a complex of THREE distinct temples on one site.

*The decision it drove.* Eight modest precincts is **inside the attested band, not a liberty**. The existing "two major complexes" default is where the real liberty sits - this file already admits as much from the other direction (see "City temple size", which records our deliberate 2-5x clergy over-density). So the doctrine says plainly that Minami moves TOWARD history, or a future reader will "correct" it back. We keep the two-complex default for non-Fox cities anyway, because it is a game-legibility choice (a few named, visitable temples beat a dozen anonymous ones), not a historical claim.

*What was NOT relied on.* No per-county-seat temple census was found in a Ming-Qing gazetteer study; searches returned categorization practice (Three Officials temples filed under "Altars and Shrines" rather than "Buddho-Daoist Temples") but no counts. The band therefore rests on the Japanese teramachi figures, with China supplying the mandatory-foundations STRUCTURE rather than a number. Recorded so nobody later attributes a Chinese count that was never found.

## Temples as economic institutions with hereditary householder clergy

**Grounds:** siting the Fox precincts by TRADE rather than in a rim-belt teramachi; ~5-9 `monk_house` per precinct; `CityProgram.monk_houses_per_precinct`

**Evidence:** attested, corroborated, setting-canon

**Sources:** `chinaknowledge-tang-econ`, `inexhaustible-treasuries`, `tontine-monastery-lending`, `pawnbroking-history`, `zhengyi-householder-priests`, `kannushi-wiki`, `jodo-shinshu-marriage`, `tricycle-temple-wives`

*What determines it in reality:* endowment decides the TRADES (a monastery with land, dependents and tax exemption must deploy its capital), and the ordination rule decides the HOUSING (celibacy means cloister; hereditary ordination means householders).

*The economy.* Chinese Buddhist monasteries were major economic actors: their land and dependent labor funded **mills, oil presses and other enterprises**; the **Inexhaustible Treasuries** were interest-earning endowments, the Chang'an one liquidated by Xuanzong in **713** as fraudulent banking; **pawnbroking before the Tang was limited to Buddhist monasteries**, and by the Song lay investors partnered with monasteries specifically to open pawnshops inside monastic tax exemption (a 1202 document records ten men forming a *ju* to fund one). `l7r.md`'s Fox economy - the Seven Temples holding forest usufruct, moneylending with Fukurokujin and Ebisu, wedding loans with Benten - is a direct match, down to which institution lends.

*The decision it drove.* The eight precincts distribute **by trade across the quarters** rather than gathering into one belt, because each is an economic house sited where its business is. The Japanese rim-belt teramachi is the considered alternative and is deliberately NOT taken: it is a castle-town DEFENSIVE arrangement, and these temples are commercial institutions first. Consequence for the gate: a trade-sited precinct is sometimes the only temple in its quarter, so `city_temple_neighborhood_has_shrines` applies per CLUSTER and lone precincts are correctly exempt - the same treatment Tango's converted-estate Bishamon already gets.

*The housing inversion.* **China first: Zhengyi Daoist priests are almost always married - marriage is required for the highest rank - and they RESIDE IN HOUSEHOLDS rather than a monastery, transmitting ordination hereditarily.** Japan corroborates twice: Shinto priests marry and their children inherit, some shrine priesthoods held in one family for as many as **100 generations** (the hereditary office was abolished in **1871** but persists by preference); and **Jodo Shinshu** was the one tradition the Tokugawa exempted so a temple head could marry and keep priestly status, producing the *bomori* and eldest-son succession. `l7r.md`'s Fox rule - only the Three Bonds celibate, every other position hereditary, "the temple's revenue sources are effectively family businesses passed down along bloodlines" - is essentially that arrangement with a small celibate administrative core. So a Fox precinct is a small walled workplace ringed by its temple families, and the budget's clergy line scales with precinct count instead of sitting at the retired constant 5. *Departure, disclosed:* the drawn `monk_house` stays deliberately identical to a laborer house - the eye should not be able to pick temple families out of the fabric, because in reality it could not. Only the manifest knows.

## The graveyard ceiling does not scale with temple count

**Grounds:** `city_graveyard_count` (2-4 at city scale), left UNCHANGED at eight precincts

**Evidence:** reconstruction, setting-canon

**Sources:** not recorded - reasoned from the two findings above plus the existing funerary doctrine

*What determines it in reality:* parish structure and burial LAND, not the number of foundations. A burial ground needs suitable ground outside the built area and serves a catchment; several foundations routinely shared one.

*What was reasoned.* The tempting change is to scale the 2-4 ceiling with the eight precincts. That is wrong twice over: the Fox precincts are economic institutions holding forest usufruct, **not eight parishes**, so they have no separate congregations of dead; and the existing city funerary doctrine already sites burial grounds by ground suitability (off the fields, downstream, across the water where the bank allows), which constrains LAND rather than counting temples. Eight small precincts sharing three burial grounds is the ordinary arrangement.

*The decision it drove.* The ceiling stands unchanged, and the reason is recorded next to the rule so the next many-temple city does not "fix" it. **This is a case where the research led to REJECTING a change**, which the constitution requires be written down as explicitly as an accepted one.

## Torii are VOTIVE DONATIONS - the count records patronage

**Grounds:** `torii_count_canonical`, `roll_torii_count`, `torii_match_roll`

**Evidence:** attested, reconstruction, liberty

**Sources:** not recorded - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

*What the research found:* torii were VOTIVE DONATIONS, not shrine construction - a shrine's count records its accumulated patronage (ujiko subscriptions, grateful merchants, the local lord), a culture that boomed in the Edo period. The historical distribution: **1 torii is the overwhelming mode** (~90%+ of true village shrines); **0 is the norm only BELOW the shrine tier** (hokora/wayside god-shelves, which vastly outnumbered real shrines - a proper shrine with none was rare enough that each had a story); **2-3** is the ranked-shrine tier (the numbered ichi/ni/san-no-torii on long approaches, 3 the conventional ceiling); and the **dozens-plus tail is specifically the Inari donation-row cult** (Edo-onward, a handful to a few dozen at a modest rural Inari, hundreds only at famous cult sites, ~10,000 at Fushimi). No scholarly per-shrine census exists - the shape is assembled from normative statements plus attested examples.

## Torii spacing - two regimes and nothing in between

**Grounds:** `torii_avenue_pitch_capped`, `settlement._avenue_pitch`

**Evidence:** attested, reconstruction

**Sources:** not recorded - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

- **How far apart, and how far from the hall - the spacing research** (GM asked 2026-07-25; drove `torii_avenue_pitch_capped` and `settlement._avenue_pitch`). *What the research found:* real torii spacing has exactly **two regimes and nothing in between**. (1) **Donation rows**: Fushimi Inari's *Senbon Torii* section runs ~800 gates along ~400 m in two parallel rows - a pitch on the order of **0.5-1 m** - and where the row loosens further up the mountain the gates are described as "at times tightly packed and at times irregularly spaced and **several yards apart**", i.e. ~3-9 m at the loose end. (2) **Ranked gates** (*ichi-* / *ni-* / *san-no-torii*) are landmarks strung along a whole approach, not a corridor: Nagao Shrine's ichi->ni is **200 m**, Meiji Jingu's three span a ~10-minute walk (~250 m apart), and Kasuga Taisha's ichi-no-torii stands **1.3 km** from the shrine. At 1-3 ft/px a ranked pair is off the map at every settlement scale. *The decision:* since Rokugan's 1/3/7 set is neither regime, the pitch is an explicit house rule (~20 ft, cap 32 ft) rather than a copied fact - documented as a deliberate invention so nobody re-derives it expecting a source. *The approach GAP, by contrast, is grounded and scales correctly as it stands:* a village shrine's arch sits ~20 ft off its hall (a small *keidai* with the hall right there), while a city temple's innermost arch stands 76-120 ft out - a real gate-to-hall courtyard, and comfortably inside the norm for a proper precinct (a Nara-period provincial temple's *kokubunji* precinct ran ~218 m per side). That gradient is deliberate and was left alone.

## Burial-ground shape - Japan organic, China surveyed

**Grounds:** `s.cemetery(parish=False)` -> `organic`

**Evidence:** attested, corroborated, liberty

**Sources:** not recorded - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

*What the research found - the two reference cultures split.* **Japan** (the organic pole): commoner burial grounds were unplotted and terrain-following everywhere - Kyoto's great burial fields (Toribeno, Adashino, Rendaino) were open hillside/riverbank grounds shaped purely by terrain; a village kept an unsurveyed *sanmai* on waste land at its edge; Edo-period urban burial fragmented into many small temple graveyards packed incrementally (Osaka's excavated "seven graveyards" show crowded overlapping pits, not plots). Premodern Japan offers essentially NO surveyed rectangular commoner cemetery. **China** (the split case): ordinary family graves were scattered organically over unfarmable hillsides by feng shui - no communal commoner cemetery at all - BUT the institutional "common burial ground" for the poor and unclaimed dead genuinely WAS a surveyed rectangle: the Song state pauper cemeteries (*louzeyuan* 漏泽园, empire-wide by edict from 1104, continued as Ming *yizhong* 义冢 charity graveyards) were walled compounds on high barren ground with plots in ordered rows, numbered against the Thousand Character Classic, a drainage ditch every three rows, and a resident caretaker monk.
