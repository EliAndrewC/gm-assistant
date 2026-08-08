# The government quarter: the research behind the ministries and martial training

*The research behind the rules in [`../../settlements/cities/government.md`](../../settlements/cities/government.md). Findings, anchors and disclosed departures live here so the rule file stays operational; this file is where citations and deeper historical context get added as they accumulate.*

**Load this file when:** you are changing a government-quarter rule or the dojo/martial-hall counts - or you want the historical basis before overriding one.

Every entry: what the research found, the decision it drove, and any deliberate departure from literal reality. Anchors are stable - rules link to them by `#slug`.

---

## Martial training is an URBAN institution

**Grounds:** `city_has_martial_hall`, the rolled private-dojo count

**Evidence:** attested, corroborated, setting-canon - **plus one `reconstruction` that used to be mis-classed as a finding; see "What the research did NOT find" below**

**Sources:** not recorded - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

**What the research found.** The standalone dojo with a resident sensei and enrolled students is an urban institution in both anchor cultures. In Edo Japan formal martial instruction lived in the **castle town**: the domain school (*hanko*) and its martial hall (*bugeijo*) were built in castle towns for the domain's own retainers, and by late Edo nearly every one of the ~260 domains had one. Private commercial halls - *machi-dojo*, run by low-income bushi and eventually by commoners teaching for a living - are a **late phenomenon and a metropolitan one**: the boom runs roughly 1830-1860 and its famous examples (the Three Great Dojo of Edo; Chiba Shusaku's Genbukan claimed ~3,600 disciples over its life) sit in a city of a million. The Chinese anchor is starker: military examinations were held at county and prefectural level and candidates prepared at schools, but there was no dense network of private martial academies at a county seat - drill happened at garrison grounds.

**What the research did NOT find, corrected 2026-08-08.** The rule file used to state a decision of "roughly one martial establishment per ~100 resident samurai" in the same voice as the paragraph above, and the GM caught it: *"I don't know where the 1 per resident samurai number came from since I don't recall that offhand, so do you know whether there's a historical basis for that?"* **There is none.** That ratio was worked forward from budgets.md's samurai counts and then sanity-checked against the tier ladder - honest arithmetic, but a `reconstruction` sitting inside an `attested` entry with no marker saying so, which is precisely how an unsourced number acquires the authority of a finding.

The attested content is narrower and supports a different shape: **one state institution per castle town** (the *hanko* pattern, which is a program item rather than a count that scales) and a **deliberately thin private tail** (because the *machi-dojo* boom needed a metropolis). The shipped generator already rolled 1-per-200 for the private halls, so nothing drawn was ever wrong - but the ~1-per-100 read was the only argument for enriching that tail at the capital tier, and it does not survive being asked for its source. The capital therefore keeps the 1-per-200 roll and gains the domain school instead ([`../../settlements/capitals.md`](../../settlements/capitals.md)).

**The transferable lesson:** an entry's `**Evidence:**` line classes the entry as a whole, so a single reconstructed NUMBER can ride inside an otherwise attested finding undetected. When an entry mixes classes, say which sentence is which - the way this one now does.

## Servant housing in the samurai ward - servants are drawn as WALLS, not as houses

**Grounds:** `city_samurai_ward_residents_only`, the `servant` kind inside a declared ward, budgets.md's servant families

**Evidence:** attested (both traditions, independently), with one disclosed liberty

**Sources:** `jta-nagayamon`, `jta-ashigaru-kaga`, `fukui-bushi-jutaku`, `matsue-bukeyashiki`, `hikone-ashigaru`, `shibata-ashigaru-nagaya`, `bukeyashiki-wiki`, `buke-hokonin-wiki`, `neixiang-yamen`, `pingyao-yamen`, `daozuofang`, `pingjiang-tu`

### What the research found

**Japan (the cultural surface, so it decides the drawn form).** Domestic servants of a samurai household - *genan/gejo*, *chugen*, *komono* - lived INSIDE their master's walled plot, never in their own street-fronting house in the *buke-chi*. They were live-in staff on annual contracts (the *degawari* changeover, 4th day of the 3rd month) hired out of the merchant quarter through labor brokers, so a castle town's servant *population* is partly recruited from the *chonin-chi* while its servant *housing* sits inside samurai walls. Three plan positions, in descending order of household size:

1. **The perimeter *nagaya*** - a long, narrow, single-story range running along the INSIDE of the street boundary, forming the plot wall itself. The Fukui archive's reading of the Suginuma plan (1,000 koku, 1839: a 28 x 32.5 ken plot, ~167 x 194 ft) states plainly that the street-facing buildings *were the nagaya where the servants lived*.
2. **The *nagayamon* gate rooms** - where the range is short it survives only as the gatehouse: gatekeeper's room, *chugen* room, stable, storeroom, sometimes a projecting guard box, with barred lookout windows onto the street. Measured examples run **~15 ft deep by 70-80 ft long** (Omura Yahei, Kishu, 12 ken x 2.5 ken = 76 x 15 ft; the Tokyo ICP gate 72 x 15 ft). It is a barracks range with a hole cut in it, not a gate with rooms attached.
3. **Rooms off the kitchen** - below roughly 100-300 koku there is no room for a range at all, and the servants sleep in *nando* and service rooms under the main roof. Even at the top this persists for women: Aizu's Saigo Tanomo residence sorts its 38 rooms into reception, retainers' office, family, and maids'/servants' groups, all under one roof.

**Small uniform houses in ranks DO exist in a castle town - but never here.** *Ashigaru*, *kachi* and *doshin* got individual plots in dedicated collective blocks (*kumi-yashiki*) at the town's EDGE: Kanazawa put them on the fringe beyond the townspeople's quarter, Hikone ringed the whole town with ~700 households as a defensive screen, Sendai and Hachinohe placed them at the highway ends. Files of about ten identical plots per row, and the enclosure marks the rank - earthen wall for middle and up, board fence for lower, **hedge for the lowest, who were forbidden walls**. Form is a terraced range by default (Shibata's ICP *ashigaru-nagaya*: 8 households under one thatch roof, 143 x 21 ft, 18 ft frontage each) and detached-with-garden only in rich domains (Kaga, Hikone - both flagged as unusual in their own documentation).

**China (checked second, and it agrees).** An elite or official quarter reads as *a field of walled rectangles with a single dark notch each*. Household servants occupy the ***daozuofang*** - the south row whose windowless back IS the compound's street wall, its doors facing inward - and the rear service row (*houzhaofang*); the inner wings house family, not servants. The one attested staff-housing BUILDING is the Ming clerks' lodging (*lishe* / *gongxiefang*) - a single named courtyard INSIDE the yamen wall (Neixiang's west line; Pingyao's, built 1619 behind the west three chambers), not a district. The group numerous enough to have formed a servant quarter, the runners (*yayi*), was not housed by the state at all: their *banfang* were improvised sheds against the inside of the yamen wall, "no fixed position and no standard size", and they went home to houses scattered in the town.

**The two traditions therefore give the same drawing rule from opposite directions**, which is as strong as this kind of finding gets: service accommodation is part of the boundary or the interior of the compound it serves, and a rank of small uniform dwellings inside an elite quarter is the one thing neither tradition produces.

### The decision it drove

A `servant` dwelling inside a samurai ward is **not a freestanding house**. It is service accommodation BOUND to the samurai household it serves - drawn on that household's street edge as a long, thin range (the *nagayamon* proportion, ~15 ft deep), or not drawn at all for the smallest households, whose servants sleep under the master's roof.

The count is NOT the problem and must not be "fixed" by deleting servants: budgets.md gives a provincial city 120 servant families, of which **72 are attached to samurai households** (30 to wealthy samurai at property 2, 42 indentured to non-wealthy at property 1) against **60 samurai families** - about one servant household per junior samurai household and two per senior. They are property-holding families in the GM's economic model, so they are real households that must be housed, counted, and taxed. What was wrong on Minami (GM 2026-08-02) was purely the ARRANGEMENT: 33 servant households in the ward, only 7 of them within 30 ft of any samurai house, 9 more than 100 ft away (one at 415 ft), and 14 of them ranked in a dead-straight column hugging the inside of the west fence - the slot a whole-interior top-up sweep finds between the fence corridor and the first samurai row. Ranked, detached and unattached, they read as exactly what the fence exists to exclude, which is why the GM saw "more commoner houses in the samurai neighborhood" after the barred kinds were removed.

### Disclosed departures

- **Our in-city samurai houses are UNWALLED** (`city_samurai_housing_varied` forbids `s.manor` inside the rampart; the walled estates are extramural). Both traditions above put the servants inside a compound WALL that our city plans do not draw. The *nagaya* range is what resolves this without reversing the GM's settled doctrine: historically the range IS the wall, so drawing the range alone - a long thin building hard on the street line - carries the same read at 3 ft/px without introducing walled compounds into the ward.
- **Ashigaru blocks are not drawn** as a distinct texture at this tier. The edge-of-town *kumi-yashiki* is a real and attested pattern and would be the correct home for any genuinely ranked small housing; if a future map wants ranks of uniform small dwellings, they belong OUTSIDE the ward on the town fringe, not inside the fence.
