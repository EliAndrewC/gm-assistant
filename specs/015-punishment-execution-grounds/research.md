# Phase 0 Research: Punishment Spots and Execution Grounds

**Feature**: 015-punishment-execution-grounds | **Date**: 2026-07-25

This is the **opening gate** required by Constitution Principle XII. For each element the feature adds, it states what the historical reality was (China-first, Japan corroborating, per the `/diagram` doctrine), whether the proposed design matches it, and **what determines the element in reality** - the governing variable, which is the thing a generator most often gets wrong.

---

## 0. The question that had to be answered first: does a county seat have an execution ground at all?

This is where China and Japan genuinely disagree, and getting it wrong would misplace the entire feature.

**Japan.** Executions were pushed *out* of the settlement to avoid *kegare* (death pollution). Edo's three grounds - Suzugamori on the Tokaido at the south entrance, Kozukappara on the Oshu/Nikko kaido at the north, Itabashi on the Nakasendo at the northwest - all sat at highway entrances outside the center; the sources are explicit that criminals were executed on the outskirts "to avoid the spiritual pollution of the city." Castle towns had a ground; villages had none, and village authority topped out at banishment.

**China.** The classical penalty is 棄市 *qishi*, "abandon in the marketplace." Qing Beijing's Caishikou was the vegetable market at a crossroads outside Xuanwumen. Critically for us, a county magistrate could **not confirm** a death sentence: capital cases climbed prefecture to provincial judicial commissioner to governor to the Board of Punishments to the emperor's autumn check-marking (*qiushen*, the autumn assizes). But the confirmed sentence came back **down**, and the execution was carried out **at the county seat where the crime happened**, because local deterrence was the entire point of a public execution.

**Reconciliation, and why it is not a fudge.** `settlements.md` already states the town doctrine: *"what would a Chinese county seat administered by samurai do?"* Applied here it gives a single coherent answer rather than a split-the-difference one:

- **China supplies the jurisdiction and therefore the existence**: the county seat has a ground, because that is where confirmed sentences are executed.
- **Japan supplies the siting**: *kegare* pushes it from the marketplace out past the built edge.

**This also explains a canon line we already had and had never used.** `budgets.md` funds "prisoner food, jail upkeep, court materials" at county level - a jail with no execution line - while "ceremonial executions" appear only in the domain and Imperial budgets. Read through the Chinese system that is exactly right: **the county jail is a holding pen for the condemned while the warrant travels**, not a punishment in itself. The `/diagram` SKILL.md already records the same shape for Mode A ("Edo detention was a holding function, not imprisonment-as-punishment"). The paperwork goes up and comes back; the prisoner stays put; the county pays to feed them and nothing more.

**Governing variable**: **jurisdiction, not population.** A settlement has an execution ground if and only if it is a seat where a magistrate's court sits - county town and above. That is why hamlets and villages get nothing, and why the feature is gated on tier rather than on inhabitant count.

**Design matches**: yes. Execution grounds at county town, provincial city, and capital; none below.

---

## 1. The punishment spot (in-town)

**China (primary).** The 枷 *jia*, the cangue: a heavy wooden collar worn for one to six months depending on the offense, with **the offender's name, the crime, and the sentence length inscribed on the boards in large characters so the public could read the case**. The offender was paraded to and displayed at a central location - a marketplace or a crossroads - or before an official gate. The bamboo beating (*chi* / *zhang*) was by contrast administered **inside the yamen courtyard**, in front of the magistrate's bench.

**Japan (corroborating).** Flogging (*tataki*, introduced 1720, up to 100 lashes for commoners) and handcuffing (*tegusari*, 30-100 days) sat at the bottom of the Edo punishment ladder, below confiscation, exile, and penal labor. Exposure (*sarashi*) as a public-shaming sentence is the same institution as the cangue by another route.

**What this changed in our design.** The original sketch had the punishment spot as a place where beating happens. The Chinese evidence splits it: **the beating is a court act and happens inside the magistracy** (which is Mode A, already drawn, and unchanged by this feature), while **the street installation is a display device**. So the in-town feature is primarily a *display* - the cangue frame and its inscribed board - with a flogging post attached because the Japanese side did whip at the public post. The spot is furniture for the sentence's *audience*, not for its execution.

**Governing variable**: **foot traffic.** Both traditions site the display where the most people pass - market, crossroads, official gate - not where it is administratively convenient. This is the same criterion the existing `kosatsuba_by_the_road` check already encodes for the notice board.

**Explicit non-duplication.** The settlement notice board (*kosatsuba*) **already exists** in the engine at every tier, auto-sited by traffic, and `settlements.md` already documents that the town board and the magistrate's manor-gate board are two distinct institutions. The punishment spot is a **third** thing and must not draw a fourth board: the crime text rides on the cangue itself, exactly as the historical inscription did.

**Design matches**: yes, after the beating/display split.

**Size.** A cangue frame plus a post and a kneeling stone is small: a ~30 x 12 ft installation, inside the 20-40 ft frontage band the spec asked for.

---

## 2. The execution ground (out-of-town)

**Size anchor.** Suzugamori measured **74 x 16.2 m (~243 x 53 ft, ~0.3 acre)** and served Edo, a city of one million, for 220 years. That is the single hardest number available, and it is *small* - the deterrent is the sight of the posts from the highway, not acreage. Kozukappara was the same kind of roadside strip on the opposite approach.

**Volume, which is what actually sets the tier sizes.** Formal execution rates in comparable premodern states run on the order of 1-3 per 100,000 per year. A county in the median domain is one town + 6 villages + 36 hamlets, ~7,000-8,000 inhabitants, so the formal channel produces an execution roughly **once every 5-10 years**. Banditry adds to it - `professions.md` gives ~200 bandits per domain across 36 counties, ~5 per county, ~1 violent - and bandit executions arrive in batches when a gang is swept up. A provincial city aggregates ~40,000 and sees on the order of one a year; a domain capital aggregates 250,000 plus the ceremonial cases the domain Justice budget names, so a handful a year.

**What the volume means for the drawing, and this is the important part**: a county execution ground is **a weedy, half-forgotten patch with a rotting post and a socket stone full of rainwater**, not an installation. It should read as disused. Only at city and capital scale does it earn screening and permanent furniture. A generator that drew a county ground as a busy scaffold would be asserting something false about how often the Empire kills people.

**Tier sizes** (scaled from the Suzugamori anchor by the volume ladder above):

| Tier | Footprint | Character |
| --- | --- | --- |
| County town | ~60 x 60 ft | Unfenced bare patch, posts and pit, disused |
| Provincial city | ~100 x 60 ft | Screened on three sides, road side open |
| Domain capital | ~150-250 ft along the road x 50-80 ft deep | Suzugamori scale, permanent furniture |

**Governing variable**: **the road, and pollution direction.** Not population and not the settlement's geometric edge. The ground exists to be seen by travelers arriving, so it sits on the busiest road; and *kegare* puts it downwind, downstream, and on the outcast side. A generator that placed it at "the far edge of the map" would have the existence right and the governing variable wrong.

**Furniture, from the surviving Suzugamori remains plus the standard Edo kit**: stone bases with square mortises for the crucifixion posts (posts erected only when needed - which is why the *socket* is the permanent thing at a county ground), an iron stake for burning (Edo burned arsonists, which lands well in a setting whose towns fear a city-destroying fire), a sand bed with a head-hole for beheading, a head-display stand facing the road with the crime board beside it (*gokumon*, three days' exposure), a well for washing the blade and the ground, and a disposal pit.

**Design matches**: yes.

---

## 3. Separation from the community's dead

**Historical reality.** These are two different kinds of death and they were not co-located. The executed went into a pit **at the execution ground itself** - Kozukappara's burials were haphazard enough that the sources describe stench and scavenging, and a memorial hall was founded beside it in 1667 specifically because of it. The community's own dead went to temple graveyards elsewhere in the city entirely. The real separation was not a matter of feet; it was *a different part of the outskirts*, typically a different road out of town.

**Where we deliberately depart from literal reality, and why.** Our maps are a few thousand feet across, so "a different road out of town, a mile away" often does not fit. The rule is therefore a **minimum separation of 150 real ft** between an execution ground and any cemetery, cremation ground, ossuary, or mausoleum - a legibility floor, not a historical measurement. The disclosure that Principle XII and the record-the-why rule require: *the true separation was far larger; we compress it because the map is small, and we keep the relative ordering honest (the execution ground is always the further-out, more polluted of the two).* The number itself is calibrated against the project's existing pollution constant - the cremation ground and tanning yard already demand 120 ft clear of dwellings - and set one band above it, because 120 ft separates polluted ground from *clean* ground, whereas two polluted grounds at that spacing read as one precinct.

**Governing variable**: **kind of death, not distance.** Ancestral, tended dead versus disposed, unmourned dead. That is why the check is a separation rule against the whole family of funerary features rather than against the cemetery alone.

---

## 4. The boundary marker

**Japan (primary here; this one is a Japanese institution).** *Dosojin* / *sae no kami* - tutelary stones at village boundaries, mountain passes, and crossroads. The etymology is the point: *sae* means "to block," and the deity's job is to stop evil, pestilence, and pollution from entering the settlement. Usually a paired male-female figure carved on a single stone.

**Why the feature needs it.** It converts "outside the settlement" from a vague spatial claim into a **stated ritual boundary**, and it gives the map a visible reason why the execution ground is where it is. The ground is not merely far from the houses; it is *on the far side of the stone that keeps pollution out*.

**Governing variable**: **the road crossing the settlement's ritual boundary.** The stone marks where the road leaves clean ground.

**Size.** A real dosojin stone is ~2-4 ft - sub-glyph at every tier, so it is a **location marker** in the established sense (SKILL.md "to scale"): drawn at a legibility floor with the true footprint recorded separately, exactly as the wells and the kosatsuba already do.

---

## 5. Designs considered and rejected

- **A second notice board at the punishment spot.** Rejected: the *kosatsuba* already exists at every tier and `settlements.md` already distinguishes the town board from the manor-gate board. The crime text belongs on the cangue, which is where the sources put it. Adding a third board would be a modeling error dressed up as detail.
- **Beating administered at the street spot.** Rejected on the Chinese evidence: the bamboo was a court act inside the yamen. The street installation displays; it does not try.
- **Execution grounds at village tier.** Rejected: village authority topped out at banishment in Japan, and the Chinese chain confirms sentences far above county level. Gated off by check.
- **Siting the ground by "distance from the map edge" or by population.** Rejected: that gets the existence right and the governing variable wrong. Road and pollution direction decide.
- **Merging the execution ground with the existing cremation-ground / ossuary cluster** (tempting, since both are outside-the-walls death features and the cluster already exists on every pool map). Rejected: it is exactly the conflation the sources rule out, and the GM named it as the thing to avoid.

---

## 6. Closing gate commitment

Per Principle XII, before this feature is reported done we re-examine the **rendered PNGs** - not the manifests and not the checks - and confirm for each map: the ground reads as outside the settlement, reads as bare waste ground rather than a field, reads as disused at county tier, sits visibly on the road past the boundary stone, and is visibly a different place from the burial/cremation cluster. `check_village` proves internal consistency; only the picture can prove this.

---

## Sources

- [Suzugamori execution grounds](https://en.wikipedia.org/wiki/Suzugamori_execution_grounds) - the 74 x 16.2 m size anchor, the surviving crucifixion socket stone and burning stake, the well
- [Kozukappara execution grounds](https://en.wikipedia.org/wiki/Kozukappara_execution_grounds) - roadside siting at the north approach, burial practice, the 1667 memorial hall
- [Itabashi execution grounds](https://en.wikipedia.org/wiki/Itabashi_execution_grounds) - the third Edo ground, on the Nakasendo
- [Criminal punishment in Edo-period Japan](https://en.wikipedia.org/wiki/Criminal_punishment_in_Edo-period_Japan) - the punishment ladder, flogging and handcuffing, the three grounds
- [Edo-period village](https://en.wikipedia.org/wiki/Edo-period_village) - village authority topping out at banishment
- [Caishikou Execution Grounds](https://en.wikipedia.org/wiki/Caishikou_Execution_Grounds) - marketplace/crossroads siting outside the gate
- [jia, the cangue](http://www.chinaknowledge.de/History/Terms/penal_jia.html) - the inscribed boards, duration, Ming/Qing usage
- [qiushen, autumn assizes](http://www.chinaknowledge.de/History/Terms/qiushen.html) - the confirmation chain above the county magistrate
- [Dosojin](https://en.wikipedia.org/wiki/D%C5%8Dsojin) - boundary stones, *sae* "to block," siting at village edges and crossroads
