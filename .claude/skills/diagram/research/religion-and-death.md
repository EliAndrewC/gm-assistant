# Religion and the dead: the research behind the shrine, torii and funerary rules

*The research behind the rules in [`../settlements/religion-and-death.md`](../settlements/religion-and-death.md). Findings, anchors and disclosed departures live here so the rule file stays operational; this file is where citations and deeper historical context get added as they accumulate.*

**Load this file when:** you are changing a religious or funerary rule, a size, a count or a check threshold - or you want the historical basis before overriding one. Not needed to simply DRAW these features.

Every entry: what the research found, the decision it drove, and any deliberate departure from literal reality. Anchors are stable - rules link to them by `#slug`.

---

## City temple size - the deliberate L7R liberty

**Grounds:** the ~15-30 monks per provincial-city complex

Historically the median temple was **tiny**: Edo Japan ran 90,000+ parish temples at 1-2 priests each, and small hereditary Chinese temples held a handful of monks; only the famous pilgrimage complexes ran large (the great Song public monasteries several hundred, Daxiangguo and Shaolin 1,000+). **L7R deliberately over-sizes - every city temple is a major complex** in a way history would usually lack. A **provincial city** (~3,000 inhabitants) has **~15-30 monks per complex** (a serious Ming urban monastery's scale); a **domain capital** (~12,000) has **~50+ monks per complex**. That puts clergy at ~1-2% of city population against the historical ~0.2-0.4% (Song China) - a deliberate **2-5x density**, softened in-world by the temples serving the whole province's worship, not just the walled city.

## Torii are VOTIVE DONATIONS - the count records patronage

**Grounds:** `torii_count_canonical`, `roll_torii_count`, `torii_match_roll`

*What the research found:* torii were VOTIVE DONATIONS, not shrine construction - a shrine's count records its accumulated patronage (ujiko subscriptions, grateful merchants, the local lord), a culture that boomed in the Edo period. The historical distribution: **1 torii is the overwhelming mode** (~90%+ of true village shrines); **0 is the norm only BELOW the shrine tier** (hokora/wayside god-shelves, which vastly outnumbered real shrines - a proper shrine with none was rare enough that each had a story); **2-3** is the ranked-shrine tier (the numbered ichi/ni/san-no-torii on long approaches, 3 the conventional ceiling); and the **dozens-plus tail is specifically the Inari donation-row cult** (Edo-onward, a handful to a few dozen at a modest rural Inari, hundreds only at famous cult sites, ~10,000 at Fushimi). No scholarly per-shrine census exists - the shape is assembled from normative statements plus attested examples.

## Torii spacing - two regimes and nothing in between

**Grounds:** `torii_avenue_pitch_capped`, `settlement._avenue_pitch`

- **How far apart, and how far from the hall - the spacing research** (GM asked 2026-07-25; drove `torii_avenue_pitch_capped` and `settlement._avenue_pitch`). *What the research found:* real torii spacing has exactly **two regimes and nothing in between**. (1) **Donation rows**: Fushimi Inari's *Senbon Torii* section runs ~800 gates along ~400 m in two parallel rows - a pitch on the order of **0.5-1 m** - and where the row loosens further up the mountain the gates are described as "at times tightly packed and at times irregularly spaced and **several yards apart**", i.e. ~3-9 m at the loose end. (2) **Ranked gates** (*ichi-* / *ni-* / *san-no-torii*) are landmarks strung along a whole approach, not a corridor: Nagao Shrine's ichi->ni is **200 m**, Meiji Jingu's three span a ~10-minute walk (~250 m apart), and Kasuga Taisha's ichi-no-torii stands **1.3 km** from the shrine. At 1-3 ft/px a ranked pair is off the map at every settlement scale. *The decision:* since Rokugan's 1/3/7 set is neither regime, the pitch is an explicit house rule (~20 ft, cap 32 ft) rather than a copied fact - documented as a deliberate invention so nobody re-derives it expecting a source. *The approach GAP, by contrast, is grounded and scales correctly as it stands:* a village shrine's arch sits ~20 ft off its hall (a small *keidai* with the hall right there), while a city temple's innermost arch stands 76-120 ft out - a real gate-to-hall courtyard, and comfortably inside the norm for a proper precinct (a Nara-period provincial temple's *kokubunji* precinct ran ~218 m per side). That gradient is deliberate and was left alone.

## Burial-ground shape - Japan organic, China surveyed

**Grounds:** `s.cemetery(parish=False)` -> `organic`

*What the research found - the two reference cultures split.* **Japan** (the organic pole): commoner burial grounds were unplotted and terrain-following everywhere - Kyoto's great burial fields (Toribeno, Adashino, Rendaino) were open hillside/riverbank grounds shaped purely by terrain; a village kept an unsurveyed *sanmai* on waste land at its edge; Edo-period urban burial fragmented into many small temple graveyards packed incrementally (Osaka's excavated "seven graveyards" show crowded overlapping pits, not plots). Premodern Japan offers essentially NO surveyed rectangular commoner cemetery. **China** (the split case): ordinary family graves were scattered organically over unfarmable hillsides by feng shui - no communal commoner cemetery at all - BUT the institutional "common burial ground" for the poor and unclaimed dead genuinely WAS a surveyed rectangle: the Song state pauper cemeteries (*louzeyuan* 漏泽园, empire-wide by edict from 1104, continued as Ming *yizhong* 义冢 charity graveyards) were walled compounds on high barren ground with plots in ordered rows, numbered against the Thousand Character Classic, a drainage ditch every three rows, and a resident caretaker monk.
