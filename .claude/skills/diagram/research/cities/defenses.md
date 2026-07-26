# City defenses: the research behind the wall, gate and tower rules

*The research behind the rules in [`../../settlements/cities/defenses.md`](../../settlements/cities/defenses.md). Findings, anchors and disclosed departures live here so the rule file stays operational; this file is where citations and deeper historical context get added as they accumulate.*

**Load this file when:** you are changing a wall, gate or tower size, a defense tier or a spacing threshold - or you want the historical basis before overriding one.

Every entry: what the research found, the decision it drove, and any deliberate departure from literal reality. Anchors are stable - rules link to them by `#slug`.

---

## Gate structures - real footprints

**Grounds:** `s.px()` gate furniture footprints

**Evidence:** attested, corroborated

**Sources:** not recorded - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

- *What the research found (China first: Xi'an / Pingyao / Beijing walls; Edo sekisho secondary).* A gate guard duty room is a small 1-3 bay building (~15-35 ft); a gate inspection hall (sekisho/lijin bansho) ~25-45 ft; the wall's MAMIAN bastion (马面 - the projecting spur that carries the enemy-tower) is ~65x40 ft (Xi'an's are ~20 m wide projecting ~12 m), the tower building on it ~30-40 ft; a provincial GATE tower (城楼) ~52x30 ft (reserve the 120-130 ft towers for a capital); a corner tower ~50-66 ft. Well-attested: the mamian and the provincial gate-tower footprints; approximate (bay-count estimates): the guard/inspection buildings.

## Gate furniture at the throat - barbican and tax-barrier practice

**Grounds:** `city_gate_furniture_at_throat`

**Evidence:** attested, corroborated

**Sources:** not recorded - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

- *What the research found (China first: wengcheng 甕城 barbican + lijin 厘金 / chaoguan 鈔關 tax barriers; Japan's Hakone/Arai sekisho as the best-preserved architectural proof).* An inspection/tax barrier only works where traffic is forced single-file, and a walled city's gate passage is the ONE such chokepoint in the whole wall - set the station back and arrivals disperse into the street grid before ever reaching it, defeating its purpose. So guard + inspection cluster AT the gate opening, ~20-100 ft inside, flanking the road as it enters. Hakone is decisive: just inside each gomon the *Obansho* (papers/goods inspection office) and the *ashigaru* guardhouse stand OPPOSITE each other across the road, and nobody reaches the town beyond without passing between them. In a wengcheng the whole cluster reads most authentically inside the urn-courtyard between the two misaligned gates. "Set back a few hundred feet along the wall" is historically wrong.

## Wall towers - the mamian system and bowshot ranges

**Grounds:** `city_wall_tower_coverage`, the three DEFENSE TIERS

**Evidence:** attested

**Sources:** [`shen-kuo`](../SOURCES.md#shen-kuo)

- *What the research found (China first: the mamian 马面 wall-tower system; Warring-States through Ming).* The rule of thumb IS accurate, and it is the ORIGINAL design purpose of the projecting wall tower. Adjacent mamian bastions are spaced so their fields of **flanking fire (侧射) overlap** - an attacker at the curtain base between two towers is shot at from BOTH (Shen Kuo's 11th-c. Mengxi Bitan describes it as 矢石相及, "arrows and stones reach each other"). The spacing that achieves ">= 2 towers everywhere" therefore equals the effective **arrow range**: put towers a bowshot apart and every curtain point has two within a bowshot. Real spacings bracket the effective ranges: **Pingyao** ~50-60 m (>= 2 everywhere, an aimed-lethal bowshot), **Xi'an** ~120 m (= 2 x 60 m; the crossfire covers the curtain but the base near a tower has only that one at full reach - the sparser, peacetime-affordable ring). Effective bow ranges: **aimed-lethal ~60 m** (a war arrow kills reliably), **full war-bow reach ~100-150 m** (harassing fire).
