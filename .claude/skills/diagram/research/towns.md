# The town tier: the research behind the layout, wall and market rules

*The research behind the rules in [`../settlements/towns.md`](../settlements/towns.md). Findings, anchors and disclosed departures live here so the rule file stays operational; this file is where citations and deeper historical context get added as they accumulate.*

**Load this file when:** you are changing a town rule, a count or a check threshold - or you want the historical basis before overriding one. Not needed to simply DRAW a town from the rules file.

Every entry: what the research found, the decision it drove, and any deliberate departure from literal reality. Anchors are stable - rules link to them by `#slug`.

---

## Chinese towns were PLANNED - the gate-to-yamen axis

**Grounds:** `businesses_front_streets`, `buildings_face_street`, `walled_town_has_main_street`

Chinese towns - Rokugan's geographic model - were *planned*, not organic: a main avenue ran from the principal (usually south) gate straight to the **government office (yamen)**, which sat on that axis facing south, with the grid divided into blocks by cross streets. Early (Tang) cities walled those blocks into curfew *wards*; by the Song the wards opened into **shop-lined streets** (merchant shophouses fronting the roadbed), and commerce spilled **outside the gates** along the approach road (the *guan-xiang* suburb). Japan copied the Tang grid for its imperial capitals (Nara/Kyoto) but laid out castle towns (*jokamachi*) as zoned districts - samurai by the castle, merchants in trade-blocks, temples at the edge - with deliberately kinked, defensive streets.

## The market-day flophouse - who actually stays over

**Grounds:** `town_has_flophouse` (default-on, `meta(flophouses=N)`)

A county seat exists partly *as* the periodic-market center for its hinterland: most peasants come from within a day's round-trip, but those at the far edge of the catchment stay over on market eve in cheap communal lodging - a *kichin-yado* ("firewood-fee inn"), where you sleep on straw under a roof for a sen a night.

## The gate market exists for TRAFFIC, not taxes

**Grounds:** `walled_town_has_gate_market` (>= 3 premises, typically ~4-8)

**The why is TRAFFIC, not taxes (GM 2026-07-24, correcting the rationale ported from the city tier):** towns levy NO import tariffs - budgets.md puts the entire tariff apparatus (the Yasuki Taka gate collection, the tariff-audit yoriki) at provincial-city and capital gates only, ~2,700 manageable collection points instead of an impossible ~14,400 town gates - and the county magistrate's jurisdiction is the whole COUNTY, so standing outside the gate crosses no tax or regulatory line at all. The honest drivers are the ones the city-tier research (flophouse-research.md) validated: through-road travelers (carters, peddlers) buying services without detouring inside, the market-day chokepoint where the rural catchment trades, and late arrivals who find the gate shut at dusk.



## A street is access infrastructure for the buildings it serves

**Grounds:** `streets_have_buildings`

The *why* is historical: a street is **access infrastructure for the buildings it serves**, and it is paved or worn into the ground by the foot traffic to and from them - Beijing's *hutong* alleys "emerged as access routes lined by contiguous courtyard residences," and a desire path forms only between real destinations. A planned grid line that never gets built up simply **isn't drawn** (an undeveloped block).

## A rampart's cost scales with its LENGTH

**Grounds:** `wall_hugs_the_town`, `wall_sections_irregular`

The *why* is pure economics: a rampart is the single most expensive thing a town builds (rammed earth or stone, maintained for centuries), and its cost scales with its **length**, so a town walls in exactly what it must defend and no more - the line is drawn to skirt the built-up area, not to inscribe a tidy circle around a lot of empty ground. Historically this is why town walls are *irregular*: they kink in to exclude a gully and bulge out around a quarter, following the settlement's actual footprint (and the terrain).
