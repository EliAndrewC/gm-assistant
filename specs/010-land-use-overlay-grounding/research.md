# Phase 0 Research: Land-Use Overlay Historical Grounding

**This is the Principle XII OPENING BOOKEND.** Each element states what the historical reality was
(China-first, Japan corroborating), whether the proposed design matches it, and what DETERMINES the
element in reality. Designs that do not match are changed or dropped HERE.

**Headline result: the research REFUTED the feature's own premise for `mulberry_fishpond`.** The design
this spec was written to implement (drop the overlay entirely) is wrong and has been reversed. See D2.

Research was conducted by independent web research, not asserted from memory. Sources are listed per
finding. Access failures and weak evidence are flagged rather than smoothed over.

---

## The organizing finding

All three surviving land uses have the same two-term shape:

> **Topography sets which plots are ELIGIBLE. Economy decides how many of the eligible plots CONVERT.**

This is the single most useful result for the generator, because it says the current implementation is
wrong in a specific and fixable way: it has **only the economic term** (a `fraction` applied by uniform
random sample) and **no topographic filter at all**. The fix is not to replace the fraction with
topography - it is to add the topographic filter that was missing and let the fraction keep meaning what
it should have meant all along, a share of the *eligible* ground.

The evidence for the second term being real and large: Shunde county went from ~4.6% dike-pond in 1581 to
rice being under one-tenth of land by c. 1900 on **identical terrain**. Silk prices moved; the hydrology
did not.

---

## D1. Lotus (Nelumbo nucifera, 藕田)

### What the historical reality was

Chinese agronomy splits lotus into two ecotypes with **different siting logic**, and our assumed claim
("lotus took the low ground too wet for rice") is true of one and false of the other:

| | 浅水藕 shallow-water | 深水藕 deep-water |
|---|---|---|
| Working depth | 10-20 cm | 30-50 cm (tolerates 1-1.2 m) |
| Where it goes | **ordinary paddy**, rotated with rice | low bottoms, pond margins, lake edges |
| Sited by | grower's choice / market | the ground itself |

Paddy rice optimum is ~5-9 cm ponding. So even shallow lotus wants roughly double rice's water; deep-water
lotus wants 5-10x it and cannot be conjured on high ground.

Corroborating case (Japan, and note the date): **Kasumigaura, Ibaraki** converted to lotus in the 1970s
under rice production-adjustment policy, chosen because it "was the best match for Kasumigaura's low-lying
wetlands" and for flood resistance. Working depth 50-60 cm - deep-water type. Vietnam's contemporary
conversions give both motives in the same breath: low-lying paddies performed poorly for rice **and**
lotus paid better.

### Does the proposed design match?

**Partly - and the correction is narrower than the spec assumed.** Binding lotus to the low/wet ground
correctly models **deep-water lotus** and is a real, well-attested system. But it does NOT model
shallow-water lotus, which sits in perfectly good paddy by economic choice and rotates with rice
(稻藕轮作). Both coexisted.

**Decision: model deep-water lotus only; do not model shallow-water lotus.** Recorded as a deliberate
departure, not an oversight. Reasons: (a) shallow-water lotus is driven by an economic layer the generator
does not have, (b) modeling it as a uniform random scatter is precisely the thing being removed, and (c) a
multi-year rice-lotus rotation renders as a plot-by-plot patchwork that would be visually
indistinguishable from the bug we are fixing. If an economic layer ever lands, this is where it plugs in.

### Contiguity and extent

Deep-water lotus is **clustered by necessity** - low bottoms are contiguous by nature. Shallow lotus can
legitimately sit beside rice because the paddy bund lets each basin hold an independent water level; this
bund mechanic is an inference from drainage physics, not a direct citation.

Extent: China ~300,000 ha lotus (200,000 ha rhizome) against ~29.4 million ha rice = **~1% nationally**.
That national figure is far too low for a village that actually grows it; a few percent up to perhaps
10-15% of field area is defensible for a lotus-growing Yangtze village. **This range is interpolation, not
a sourced figure, and is the weakest number in this document.**

### Honest limitation

The agronomy is solid; the *pre-modern village-scale practice* is not directly sourced. The clearest
"lotus takes the bad rice ground" conversions in the record are 20th-century and policy-driven. China has
the matching category 冷浸田 (cold-seepage waterlogged paddy) with conversion to aquatic vegetables as
recognized remedy, but that is modern extension advice. **Treat as agronomically sound, historically
unverified at Song/Ming village scale.**

> **WHAT DETERMINES THIS IN REALITY: topography** for the deep-water lotus we model (economy for the
> shallow-water lotus we deliberately do not).

---

## D2. Mulberry-dike fish-pond (桑基魚塘) - **PREMISE REFUTED**

### What this feature originally claimed

That the dike-pond system was "a wholesale landscape conversion, not a land use you sprinkle," so a
scatter of ponds among rice "never existed" and the overlay had to be deleted.

### What the research actually found

**A scattered handful of dike-ponds among rice is not merely plausible - it is the system's NORMAL state.**
The wall-to-wall pond landscape is the end state of a ~300-year process in two or three townships, not the
default form.

| Shunde county, Guangdong | Dike-pond area | Share of cultivated land |
|---|---|---|
| 1581 | 40,084 mu | **~4.6%** |
| 1642 | 58,094 mu | ~6.7% |
| c. 1900 | - | rice under one-tenth of total |

Decisively: **county-level ~5% contained townships above 50% in the same year** - Longshan township in
Shunde was already over half pond agriculture in 1581. The mixed landscape and the converted landscape
existed a few miles apart.

Even in the 1980s heartland, a survey of the main dike-pond region (86,632 ha) found **rice and
miscellaneous agriculture still at 35%**, the same share as the fishponds themselves; mulberry was only
12%. And at Lake Tai - the better model for a mixed landscape - **mulberry went onto the banks of the
*tang* while rice remained the main crop of the polder**, permanently, in the same polder.

The conversion technique is inherently incremental: 挖塘培基, dig one low plot into a pond and pile the
spoil into a dike around it - **a single-plot job a household can do in one dry season**. That is why it
spread as a patchwork. Gazetteers found *total* absence of rice remarkable enough to record
(*"境內無稻田，仰糴於外"* - no paddy within its bounds, it buys grain from outside).

### Does the proposed design match?

**No. The proposed design (delete the overlay) is REJECTED by the evidence and is hereby reversed.**
`mulberry_fishpond` stays as an overlay. The original justification was simply factually wrong.

But the *current implementation* is also wrong, in the same way lotus is: conversion targeted
**低洼易有洪患之处**, low-lying flood-prone spots, as a flood-adaptation that drained the hollow while
raising the dike. So the overlay needs the **same topographic filter** - eligible plots are the low/wet
ones - plus **clustering**, because plot-by-plot household conversion spreads outward in patches rather
than sprinkling uniformly.

### The negative result that pins the two-term model

The outer-delta **沙田 shatian** - sandy flats reclaimed from the estuary - were equally low and equally
wet, and **stayed in rice**. "Low and wet" is necessary but *not sufficient*; the dike-pond zone
additionally had smallholder/lineage tenure inside an established polder and water access to Canton.

### Scope caveat worth keeping

At a *late-Qing Shunde/Nanhai core* village, scattered ponds among rice would be wrong - there it was
ponds among ponds with grain imported. The mixed picture is right for the Ming, for the delta outside the
core counties in every period, and for Lake Tai in every period. Rokugan villages are Ming-analog and are
not the Pearl-delta silk core, so **the mixed overlay is the right default and the archetype is the
exception** - the opposite of what this spec assumed.

Historians genuinely disagree on weighting: Chinese ecological scholarship leads with physical adaptation,
economic historians (Marks, *Tigers, Rice, Silk, and Silt*) with commercialization, noting the pond is
constant while the dike crop tracks the market (fruit-dike 果基 early Ming -> mulberry late Ming ->
sugarcane 1930s after the silk crash).

> **WHAT DETERMINES THIS IN REALITY: economy, with topography as a hard filter rather than a driver.**

---

## D3. Tea fringe (茶)

### What the historical reality was

Confirmed, with **one word of the assumed claim corrected**. Robert Fortune, eyewitness, Ningbo green-tea
district, 1843:

> "The tea plantations in the north of China are always situated on the lower and most fertile sides of
> the hills, and **never on the low lands**."

So tea is **lower-to-mid slope, on the fertile hillside** - not the upper slope, and not marginal ground.
The upper slopes were forest, sweet potato and peanut. Independently attested by two FAO GIAHS dossiers
giving the vertical zonation as forest above / tea mid-slope / cropland and village below.

Form is smallholder, not plantation: "every cottager, or small farmer, has two or three patches of tea
shrubs growing on the hill sides," bushes in rows ~4 ft apart. **Recognizable rows, acre-scale patches,
several per household, dotted across a hillside** - not one contiguous block.

### Does the proposed design match?

**Yes, and no code change is needed.** The engine already places tea on `dry_plots`, the field's dry high
margin - which is precisely the band immediately above where gravity-fed irrigation stops. Fortune's line
and the GIAHS zonation put tea exactly there. The research states the boundary rule outright: **"the line
is the highest irrigation ditch."**

The one required change is to **prose, not code**: any description calling this the "upper slope" is
wrong and must say lower-to-mid fertile hillside, above the highest ditch.

### Two anachronism traps to record

1. **Contour-terraced tea is post-1949** - a state program scaled through the "Study Dazhai" campaigns.
   Fortune describes terraces for *rice* and loose rows of bushes for tea. **Neat benched tea hillsides
   must not appear; terraced paddy should.** (Our tea rows are loose lines - already correct.)
2. **No tea on Chinese paddy bunds.** Japanese 畦畔茶 (bund-margin tea) is well attested; the Chinese
   equivalent is not. A real China/Japan divergence - do not project the Japanese practice westward. (We
   do not draw bund tea - already correct.)

> **WHAT DETERMINES THIS IN REALITY: topography** - tea took the best-drained *fertile* ground the water
> system could not reach. Economy decides whether a village grows tea at all; topography decides where the
> line falls, and the line is the highest irrigation ditch.

---

## D4. Rejected designs (recorded per Principle XII)

Grounding that led to REJECTING a design must be recorded, so a later pass does not reinvent it.

- **`rape` as an overlay (removed in the prior pass).** Rice and rape are the two halves of ONE rotation in
  the SAME plot - rice in summer, rape (油菜) in winter. The rotation is seasonally synchronized across the
  whole landscape, so at any instant the fields are all one or all the other. They are never both standing,
  at any percentage and in any pattern. This is why "make it contiguous and reduce it to 10%" was not a
  fix: it addressed the pattern while leaving the physics wrong. Do not re-add.
- **Shallow-water lotus (稻藕轮作) as a scatter in ordinary paddy.** Real, but deliberately not modeled -
  see D1. Rejected because it is economically driven with no economic layer to drive it, and would render
  indistinguishably from the uniform-random bug being fixed.
- **Deleting `mulberry_fishpond` from the overlay (this spec's own original US2).** Rejected by D2 on
  evidence. The premise - that a scatter of dike-ponds among rice never existed - was false.

---

## D5. Load-bearing engine assumption: is `FLOODED` a sound proxy for low/wet ground?

**Confirmed by code inspection.** All four field builders in `waterfields.py` mark `FLOODED` on the lowest
ground their geometry defines, so binding an overlay to it is a general rule and not a comb-only trick:

| Builder | Which plots get `FLOODED` |
|---|---|
| `build_comb` | plots whose bottom edge lies on the collector drain (45% of those abutting) |
| `build_terraces` | the lowest 3 terraces |
| `build_polder` | the lowest 2 rows |
| `build_ribbon` | the lowest 3 bands |

The comb builder's own comment already states the intent: *"only the level whose BOTTOM edge lies on the
collector floods (the wettest, lowest ground)... so a blue plot always abuts the drain."*

---

## Sources

Lotus: [Shungate / Kasumigaura](https://shun-gate.com/en/roots/roots_44/) ·
[Nelumbo nucifera (Wikipedia)](https://en.wikipedia.org/wiki/Nelumbo_nucifera) ·
[IRRI Rice Knowledge Bank, water management](http://www.knowledgebank.irri.org/step-by-step-production/growth/water-management) ·
[第一农经, 深水藕/浅水藕](http://m.1nongjing.com/201601/126293.html) ·
[Japan Times, lotus fields](https://www.japantimes.co.jp/life/2009/08/30/environment/avian-killing-fields-of-lotus/)

Dike-pond: [ISIS, Dyke-Pond System](https://www.i-sis.org.uk/DykePondSystem.php) ·
[Chi et al., Int. J. of the Commons 2024](https://thecommonsjournal.org/articles/10.5334/ijc.1300) ·
[维基百科 基塘农业](https://zh.wikipedia.org/zh-hans/%E5%9F%BA%E5%A1%98%E8%BE%B2%E6%A5%AD) ·
[羊城晚报 佛山桑基鱼塘](http://ysln.ycwb.com/content/2021-01/29/content_1444135.htm) ·
[顺德图书馆 桑園圍](https://www.sdlib.com.cn/home/article/detail/id/741.html) ·
[FAO GIAHS Huzhou](https://www.fao.org/giahs/around-the-world/detail/china-zhejiang-system/en) ·
[Tian Mengxiao, Sha Tian Town](https://elib.sfu-kras.ru/bitstream/handle/2311/111741/72_TIAN%20Mengxiao.pdf?sequence=1&isAllowed=y)

Tea: [Fortune, *Three Years' Wanderings* (Gutenberg)](https://www.gutenberg.org/files/54720/54720-h/54720-h.htm) ·
[FAO GIAHS Fuding white tea](https://www.fao.org/giahs/giahs-around-the-world/china-fuding-white-tea/en) ·
[FAO GIAHS Fuzhou jasmine](https://www.fao.org/giahs/giahs-around-the-world/china-fuzhou-jasmine-tea/en) ·
[PMC10490072, terracing history](https://pmc.ncbi.nlm.nih.gov/articles/PMC10490072/) ·
[PMC9548367, high-mountain tea](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9548367/)

### Access failures (flagged, not hidden)

MDPI, ScienceDirect, Springer, ResearchGate, UNESCO, Baidu Baike and Zhihu returned 403; two Chinese
history articles failed on connection/TLS. **The Shunde mu figures come from search-engine extraction
rather than pages read end to end - treat ~4.6% as order-of-magnitude.** Chinese sources mix 亩/顷/公顷
and often write 基塘 (all dike-ponds) where a reader assumes 桑基魚塘 specifically. Lu Yu's *Cha Jing* soil
rankings were snippet-only and are not relied on here.
