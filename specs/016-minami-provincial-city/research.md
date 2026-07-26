# Phase 0 research: Minami, the Fox Clan provincial city

*Principle XII opening bookend. For each element this feature adds or changes: what the historical reality was (China first, Japan corroborating), whether the proposed design matches it, and what DETERMINES the element in reality. Findings that led to rejecting or revising a design are recorded too. The closing bookend - re-examining the rendered PNG against these findings - is the last task in `tasks.md`.*

Entries below follow the `research/README.md` four-field format and are destined for `research/religion-and-death.md` (temple program) and `research/urban-features.md` (timber works) once implemented.

---

## Finding 1 - Many modest temples per walled city is the HISTORICAL norm; our two-complex default is the outlier

**Grounds:** the eight-precinct Fox temple program; the proposed multi-temple-justification check; `CityProgram.temple_precincts`

**Evidence:** attested, corroborated

**Sources:** `kanazawa-teramachi`, `takada-teramachi`, `takayama-teramachi`, `jokamachi-wiki`, `pingyao-chenghuangmiao`

**What determines it in reality:** patronage and institutional history - each temple is a separate FOUNDATION with its own patron, sect, and endowment. Temple count tracks how many distinct patrons a place has accumulated, not its population. That is why it does not scale smoothly with city size.

*What the research found.* The expectation going in was that eight temples in a 2,600-person seat would be a stretch requiring a disclosed liberty. **The opposite is true.** Japanese castle towns concentrated their temples into a designated *teramachi* quarter at the outer rim of the *jokamachi*, where the spacious precincts formed part of the city's defenses. The attested counts are large: **Kanazawa ~70 temples** in its Teramachi, **Kyoto ~80** in its temple street, **Takada ~25 relocated in a single 1614 wave**, and - the anchor that matters for our tier - **Takayama's Teramachi is "over 10 temples and shrines"** in a small castle town. On the China side, the standard Ming county-seat kit carried the Confucian school-temple (*wenmiao*) and the City God temple (*chenghuangmiao*) as separate mandatory foundations before any Buddhist or Daoist house was counted, and Pingyao's City God temple is itself **a complex of three distinct temples** (City God proper, Caishen the god of wealth, Zaojun the kitchen god) on one site.

*The decision it drove.* Eight modest precincts in a provincial city is **inside the attested band, not a liberty** - Takayama is the size-matched anchor at 10+. The existing "two major complexes" default is where the real liberty sits, and `research/religion-and-death.md` already admits as much from the other direction ("L7R deliberately over-sizes - every city temple is a major complex in a way history would usually lack," clergy at 2-5x historical density). **So Minami is not an exception that strains history; it is the pool's first city that moves TOWARD it.** The doctrine wording must say this plainly, or a future reader will "correct" Minami back toward the default.

*Deliberate departure, disclosed.* We keep the two-complex default for non-Fox cities anyway, because it is a game-legibility choice (a few named, visitable temples beat a dozen anonymous ones) rather than a historical claim - and because it is already load-bearing for the two shipped maps. Minami's eight is licensed by setting canon rather than by a decision to become more accurate everywhere.

*What was NOT relied on.* No per-county-seat temple census was found in a Ming-Qing gazetteer study; searches returned categorization practice (Three Officials temples listed under "Altars and Shrines" rather than "Buddho-Daoist Temples") but no counts. The count band therefore rests on the Japanese *teramachi* figures, with China supplying the mandatory-foundations structure rather than a number. Recorded so nobody later cites a Chinese count that was never found.

---

## Finding 2 - Temples as economic institutions with hereditary trades: attested in both traditions

**Grounds:** the Fox "which temples do X" economy; siting precincts by their TRADE rather than in one temple quarter; the temple-family housing program

**Evidence:** attested, corroborated, setting-canon

**Sources:** `chinaknowledge-tang-econ`, `inexhaustible-treasuries`, `tontine-monastery-lending`, `pawnbroking-history`

**What determines it in reality:** endowment. A monastery with land, dependents and tax exemption accumulates capital it must deploy; the trades it enters are whatever its endowment physically supports (water for mills, presses, storage for pledges).

*What the research found.* Chinese Buddhist monasteries were major economic actors, not merely religious ones. Their land and dependent labor "gave them enough revenue to set up **mills, oil presses, and other enterprises**." The **Inexhaustible Treasuries** (無盡藏) were interest-earning endowments funding recurring needs - the Chang'an treasury grew so large that Emperor Xuanzong liquidated it in **713** on the grounds that its banking was fraudulent. **Pawnbroking in China was, prior to the Tang, limited to Buddhist monasteries**, and monasteries lent money in the pawnbroker's role; by the Song, lay investors partnered with monasteries specifically to open pawnshops **inside monastic tax exemption** (a 1202 document records ten men forming a *ju* 局 to fund one).

*The decision it drove.* `l7r.md`'s Fox economy - the Seven Temples holding forest usufruct, moneylending sitting with Fukurokujin and Ebisu, wedding loans with Benten, "which temples do X, not which merchant families" - is a **direct match** for the attested Chinese monastic economy, right down to which institution does the lending. This settles a layout question the spec left open: the eight precincts are **distributed by TRADE across the quarters** rather than gathered into one *teramachi* belt, because each is an economic house sited where its business is (the lending temples by the market, the timber-usufruct temples toward the river works). The Japanese rim-belt *teramachi* is the alternative and is deliberately NOT taken - it is a defensive arrangement from a castle town, and Minami's temples are commercial institutions first.

*Consequence for the map that must not be lost:* a temple sited by its trade will sometimes be the ONLY temple in its quarter, so `city_temple_neighborhood_has_shrines` (>= 3 wayside shrines near any >= 2-temple cluster) applies per cluster, and lone precincts are correctly exempt - the same treatment Tango's converted-estate Bishamon already gets.

---

## Finding 3 - Householder clergy living out among the laity: the Fox structure is the Zhengyi pattern

**Grounds:** ~5-9 `monk_house` per precinct (vs the standard 2-3); `city_temples_have_monk_housing`; the adept-monk budget line scaling with precinct count

**Evidence:** attested, corroborated, setting-canon

**Sources:** `zhengyi-householder-priests`, `kannushi-wiki`, `jodo-shinshu-marriage`, `tricycle-temple-wives`

**What determines it in reality:** the ordination rule. Where celibacy is required, clergy live in cloister and the precinct houses them; where ordination is hereditary, clergy are householders and the precinct is a workplace, not a dormitory. The housing pattern follows directly from which rule applies.

*What the research found.* **China first: Zhengyi Daoist priests are almost always married - marriage is a requirement for the highest rank - and they RESIDE IN HOUSEHOLDS rather than in a monastery, transmitting ordination hereditarily within the family.** Japan corroborates twice over: **Shinto** priests marry and their children inherit the position, with some shrine priesthoods held in one family for as many as **100 generations** (the hereditary office was formally abolished in **1871** but persists by local preference); and **Jodo Shinshu** was the single tradition the Tokugawa government exempted so a temple head could be married and keep priestly status, producing the *bomori* (temple wife) institution and eldest-son succession.

*The decision it drove.* `l7r.md`'s Fox rule - **only the Three Bonds (High Monk, Temple Master, Chief of Discipline) are celibate**, every other position hereditary, "the temple's revenue sources are effectively family businesses passed down along bloodlines within the temple" - is essentially the Zhengyi householder-priest arrangement with a small celibate administrative core. So the housing inversion is not a game contrivance: **a Fox precinct is a small walled workplace holding three residents, ringed by the ordinary houses of the families who actually run its trades.** That is why the monk-house count per precinct rises from the standard 2-3 to ~5-9, and why the budget's adept-monk line must scale with precinct count instead of sitting at a constant 5.

*Departure, disclosed:* the drawn `monk_house` remains deliberately identical to a laborer house (existing doctrine) - the eye should not be able to pick temple families out of the fabric, because in reality it could not. Only the manifest knows.

---

## Finding 4 - The graveyard ceiling does NOT scale with precinct count

**Grounds:** `city_graveyard_count` (2-4 at city scale) left unchanged

**Evidence:** reconstruction, setting-canon

**Sources:** not recorded - reasoned from Findings 1-3 plus the existing funerary doctrine

**What determines it in reality:** parish structure and burial land, not the number of foundations. A burial ground needs suitable ground outside the built area and serves a catchment; several foundations routinely shared one.

*What the research found / was reasoned.* The temptation is to scale the 2-4 graveyard ceiling to eight temples. That would be wrong on two counts. The Fox precincts are, per Finding 2, **economic institutions holding forest usufruct - not eight parishes**, so they have no separate congregations of dead to bury. And the existing city funerary doctrine already sites burial grounds by ground suitability (off the fields, downstream, across the water where the bank allows), which is a constraint on LAND, not on temple count. Eight small precincts sharing three burial grounds is the ordinary arrangement.

*The decision it drove.* `city_graveyard_count` stands at 2-4 unchanged, and the reason is recorded next to the rule so the next person to draw a many-temple city does not "fix" it. **This is a case where the research led to rejecting a change**, which the constitution requires be written down as explicitly as an accepted one.

---

## Finding 5 - Timber rafting, yards and charcoal: already grounded, no new research needed

**Grounds:** `s.lumber_yard` / `city_river_port_has_lumber_yard`; `s.kiln` / `city_kiln_outside_walls`; the timber/charcoal `extras` budget line

**Evidence:** attested (prior pass), setting-canon

**Sources:** carried from `research/urban-features.md` "TRADE WORKS"

*What the record already holds.* The 2026-07-24 trade-works pass established the lumber dealer (*zaimokuya*) as needing **a ~3,000-8,000 sq ft open yard with a river landing, at the edge of town near the downstream gate or wharf**, and gated `city_river_port_has_lumber_yard` on `meta(river_port=True)` precisely because "timber is the one trade that genuinely needs water transport at scale." It also established that **charcoal kilns are pushed outside the walls** by fire law and smoke, alongside tile, pottery and lime kilns.

*The decision it drove.* Minami declares `river_port=True` and inherits both rules unchanged - no new grounding required. What IS new is the SCALE: `l7r.md` has Fox charcoal burners outnumbering farmers and "significantly more" timber shipped downriver than the ~10,000 koku/yr moved by cart, so Minami's yards are the city's largest working ground rather than one trade among many. That justifies the declared in-wall timber/charcoal working ground as an itemized `extras` line - the storage and stacking end of a trade whose dirty end (the kilns) stays outside.

*Open question deferred, not silently resolved:* whether a log BOOM or raft-landing glyph is worth adding to the vocabulary, or whether the existing lumber yard plus jetties carries it. Decided at implementation against the rendered map; if a new glyph is added it takes a `_OVERLAP_STRUCTS` classification and a `_LABEL_GROUP` caption group per the KEEP-CLEAR CONTRACT.

---

## Finding 6 - Population 2,600 and the peaceful defense tier

**Grounds:** `CityProgram(population=2600)`; `meta(wall_defense="peaceful")`

**Evidence:** setting-canon

**Sources:** `l7r.md` clan population table; `budgets.md` provincial-city tier; `research/cities/defenses.md` (tier definitions, prior pass)

*The arithmetic.* `l7r.md` gives the Fox 150,000 humans in one domain over four provinces = ~37,500 per province, against the median province's ~42,000; `budgets.md` puts a provincial city at 2,000-4,000, average ~3,000. Scaling gives ~2,700; 2,600 is taken as the round figure inside the band. **No historical research is involved** - this is setting arithmetic, and is classed `setting-canon` rather than dressed up as a finding.

*The defense tier* is likewise a setting call: the Fox are a minor clan shielded by the wood and the Three Man Alliance rather than by fortification, and no army has come at Minami in centuries. The `peaceful` tier's crossfire spacing was researched in the prior defenses pass and is used unchanged - this feature only makes it the first tier setting a shipped map has actually exercised.

---

## Sources to register in `SOURCES.md`

New keys used above, with what each was used FOR (per the SOURCES.md rule that the second field is what makes a stale citation visible):

| Key | Source | Used for |
|---|---|---|
| `kanazawa-teramachi` | VISIT KANAZAWA official guide, Teramachi Temple Area | ~70 temples clustered in one castle-town temple district |
| `takada-teramachi` | Joetsu Stories / Takada Teramachi tourism site | ~25 temples relocated to Takada in the 1614 wave |
| `takayama-teramachi` | Japan Travel, Takayama's historic Temple Town | "over 10 temples and shrines" in a SMALL castle town - the size-matched anchor |
| `jokamachi-wiki` | Japanese Wiki Corpus, *Jokamachi* | teramachi sited at the jokamachi's outer rim, precincts forming part of the defenses |
| `pingyao-chenghuangmiao` | Wikipedia, City God Temple of Pingyao | the City God temple as a complex of three distinct temples on one county-seat site |
| `chinaknowledge-tang-econ` | chinaknowledge.de, Tang-period economy | monastic land and dependents funding mills, oil presses and other enterprises |
| `inexhaustible-treasuries` | *Studies in Chinese Religions* 5(2), "Giving while keeping: inexhaustible treasuries and inalienable wealth in medieval China" | the 無盡藏 interest-earning endowment; Xuanzong's 713 liquidation |
| `tontine-monastery-lending` | The Tontine Coffee-House, "Buddhist Monastery Lending" | monasteries as pawnbrokers; the 1202 Song lay-partnership pawnshop *ju* |
| `pawnbroking-history` | Wikipedia, History of pawnbroking | pawnbroking limited to Buddhist monasteries prior to the Tang |
| `zhengyi-householder-priests` | Grokipedia, *Zhengyi Dao*; Patheos Taoism leadership/clergy | married priests residing in households, hereditary ordination within families |
| `kannushi-wiki` | Wikipedia, Shinto priest / Kannushi | hereditary shrine office, up to 100 generations; abolished 1871, persists by preference |
| `jodo-shinshu-marriage` | Seattle Betsuin, "Jodo Shinshu and Marriage" | the Tokugawa exemption permitting a married temple head to keep priestly status |
| `tricycle-temple-wives` | Tricycle, "Temple Wives of Japan" | the *bomori* institution and eldest-son succession |

Sources:

- [VISIT KANAZAWA - Teramachi Temple Area](https://visitkanazawa.jp/en/attractions/detail_10182.html)
- [Takada Teramachi](https://takada-teramachi.com/teramachi/)
- [Takayama's historic 'Temple Town'](https://en.japantravel.com/gifu/takayama-s-teramachi-gifu/13893)
- [Jokamachi - Japanese Wiki Corpus](https://www.japanesewiki.com/history/Jokamachi.html)
- [City God Temple of Pingyao](https://en.wikipedia.org/wiki/City_God_Temple_of_Pingyao)
- [Tang-Period Economy - chinaknowledge.de](http://www.chinaknowledge.de/History/Tang/tang-econ.html)
- [Giving while keeping: inexhaustible treasuries and inalienable wealth in medieval China](https://www.tandfonline.com/doi/abs/10.1080/23729988.2019.1639463)
- [Buddhist Monastery Lending - The Tontine Coffee-House](https://tontinecoffeehouse.com/2024/02/26/buddhist-monastery-lending/)
- [History of pawnbroking](https://en.wikipedia.org/wiki/History_of_pawnbroking)
- [Zhengyi Dao](https://grokipedia.com/page/Zhengyi_Dao)
- [Shinto priest - Wikipedia](https://en.wikipedia.org/wiki/Kannushi)
- [Jodo Shinshu and Marriage - Seattle Betsuin](https://seattlebetsuin.org/jodo-shinshu-and-marriage/)
- [Temple Wives of Japan - Tricycle](https://tricycle.org/magazine/japan-temple-wives/)
