# Flophouse / cheap-lodging research findings (2026-07-22)

Research pass evaluating the map convention for cheap traveler/peasant lodging ("flophouses")
against premodern East-Asian historical norms, per the GM's request to sanity-check a handwaved
rule. **China-first** (Song/Ming rice-south, the physical/economic layer), Japan corroborating
(Edo *kichin-yado*, cultural surface). Deep-research pass: 6 search angles, 19 sources fetched, 63
claims extracted, 25 adversarially verified (3-vote, 2/3-to-kill), 23 confirmed / 2 refuted.

## Decision (GM, 2026-07-22)

**KEEP the current rule as-is: 1 flophouse inside + 1 outside each city gate (a town keeps its 1).**
No layout change. The reasoning, preserved as the rule's grounding:

- **The density is genuinely unknowable, so any figure is an extrapolation** - the ruling class paid
  little attention to peasant lodging and did not record its numbers or placement (this research
  confirms it: gazetteers foreground official post-stations, never counting commercial flophouses).
- **Rokugan is deliberately a more peasant-attentive setting than the historical societies it draws
  on** - we put more thought into peasant life than real-world rulers did - so leaning to the higher,
  more-generous end of a genuinely-uncertain range is an intentional demographic choice, not an
  oversight. The number is *"extrapolated by combining historical precedent with Rokugani
  demographics,"* which is the honest frame for a figure the sources cannot pin down.
- **The placement half is historically supported outright:** cheap inns clustered at the gate-suburb
  (*guanxiang*) and along arrival roads, so an outside-gate flophouse is on solid ground. Only the
  perimeter *symmetry* (every gate, not just the busiest) is the stylization - and it is a small,
  legible one we accept for the reasons above.
- **One rationale is corrected, not kept:** the old "stranded outside by the dusk gate-curfew"
  justification is a *Tang* artifact (the curfew had relaxed by the Song/Ming rice-south period we
  model). The better *why* for the outside-gate inn is **convenience lodging at the busy market gate**
  for peasants, carters, and peddlers - plus the gate-suburb clustering pattern. Update the docs'
  rationale accordingly; the layout is unchanged.

Options B/D below (concentrate on one gate; draw a distinct animal-yard cart-inn) were considered and
**declined** in favor of keeping the readable symmetric rule.

**Size (asked 2026-07-22): the ~104 x 46 ft flophouse glyph is reasonable, if slightly generous.**
It is ~3.7x a farmhouse footprint and reads as a large barn-like dormitory (which is what the
docstring already calls it). Sanity check: a communal sleeping platform for the research's ~10-30
occupants runs ~75 ft, which the 104 ft length fits with room for a hearth/entry; and at ~30
occupants it works out to ~160 sq ft/person - *denser* than a farmhouse's ~260 sq ft for a family of
5, exactly as communal doss-house lodging (no private rooms or yards) should be. So the size errs
generous rather than cramped, which suits the legibility license and the peasant-attentive framing.
No size change.

---

**Original status when written: FINDINGS ONLY.** The options below were the menu the GM chose from;
option A (keep, with documented reasoning) was selected.

## What the maps do now (the convention under evaluation)

- **Town** (`town_has_flophouse`): 1 market-day flophouse, default-on, at the gate market of a
  walled town / along the road of an unwalled one. `meta(flophouses=N)` to change.
- **City** (`city_has_flophouse`, `city_flophouse_inside_walls`, `city_flophouse_outside_each_gate`,
  `city_flophouse_in_humble_quarter`): **one flophouse just outside EVERY gate** (within ~520px,
  for travelers who reach a shut gate) **plus at least one inside** the walls in a humble quarter
  (laborer/agrarian, never by temple/merchant/samurai/burakumin). In practice Tango and Nagahara
  (2 gates each) each carry **4 flophouses: 2 inside + 2 outside** (one outside per gate).
- Stated rationale in `settlements.md`: the outside-gate flophouse serves **late arrivals who miss
  the dusk gate-closing**; the inn + stables + yard sit inside for secure overnight animal holding.

The GM's own framing, verbatim: *"a flophouse outside the city walls for late arrivals and inside
the city walls for peasant visitors, and probably each entrance should have the pair of those
things."* That is essentially what is encoded.

## Findings, by how well the evidence holds

### Well-documented (high confidence)

1. **The gate curfew was real and strong under the Tang, but had substantially RELAXED by the
   Song** - which weakens the "stranded outside the walls at dusk" rationale precisely for the
   period Rokugan is modeled on. Tang cities beat a gate-closing drum at dusk and a gate-opening
   drum ~4 a.m.; ward gates locked, mounted soldiers patrolled, and violators were flogged (Tang
   ~20 strokes; Ming 40-50 for the 9pm-3am watches). But under the Song the walled-ward (*fangshi*)
   system collapsed, ward walls came down, the Kaifeng curfew was formally abolished in 1063, and
   night markets ran at all hours. **So the curfew-stranding demand driver is a Tang phenomenon;
   for the Song/Ming rice-south model it is weak and regionally variable.** (8 claims, all 3-0.)

2. **The cheap tier served exactly the low-status clientele the convention targets** - carters and
   cart-bosses (*che laoban*), itinerant peddlers (*xingfan*), and farmers (*nongmin*) - on communal
   sleeping platforms holding ~10-30 people (originally mixed-sex, a cloth curtain screening a corner
   for women: the archetypal flophouse arrangement). The Chinese **cart-inn (*dachedian* 大车店) was
   a distinct animal-yard type**: a spacious compound, front court for grain/fodder, rear court with
   stables, hitching posts, feed troughs, water vats - a roadside *service node* that drew repair
   trades, markets, folk medicine, prostitution, and bandits around it, not a single building.
   (5 claims, all 3-0.) *Caveat: the heated* kang *and this whole inventory are cold-north Manchurian
   features; a rice-south equivalent (*jimaodian* 鸡毛店 "chicken-feather inn") would use straw/board
   bunks. Transfer the pattern, not the* kang.

3. **Japan corroborates the "sleep-on-straw for a few coins" core AND the route-node (not
   gate-symmetric) siting.** *Kichin-yado* (木賃宿, "firewood fee") were unambiguously the cheapest
   self-cater tier - a hearth and firewood but no meals, travelers cooking their own provisions
   (~50 mon vs. the meal-providing *hatago* at ~300 mon). Both attached to *shukuba* **post-stations
   spaced along the highways** (the Edo Five Routes), i.e. Japanese roadside lodging keyed to
   travel-route nodes, not city gates. (5 claims, all 3-0.)

### Reasonable inference (medium confidence)

4. **The cheap Chinese tier was sited by travel-distance staging + the gate-suburb, NOT by a
   systematic inside-vs-outside-each-gate split.** Cart-inns were spaced roughly **every 40 li** (a
   loaded cart's half-day, mirroring the courier-station *yizhan* stages) and clustered *于交通要道
   和城关附近* - **along the arterial roads AND near the gate-suburb (*guanxiang* 城关)**, not purely
   open road and not intramurally. This layers on a much older pattern: *Zhouli* relay rest-houses
   every 10 li along the roads, and the Southern-Dynasties *dizhan* (邸店) fusing lodging with
   warehousing/trade. **This supports a "gate-suburb flophouse" and "along the arrival road" - but
   not a symmetric one-per-gate scheme.** (Confirmed 3-0 where verified; see refutations below.)
   *Caveat: the richly-documented* dachedian *is a late-Qing/Republican NORTHEAST-China freight-road
   institution, so it is corroborating detail transferred to a Song/Ming rice-south model, not
   direct evidence for that period.*

### Genuinely thin / unknown (low confidence - the honest gap)

5. **Number/density per settlement is NOT established by the surviving record.** None of the 23
   confirmed claims - nor any refuted one - supplies a gazetteer count, guild roster, or per-gate
   tally of cheap inns for a settlement of any size. The record shows clustering into service nodes
   and route-stage spacing, which *weakly* favors a clustered "lodging district" at the busy
   gate-suburb over an even one-per-gate distribution, **but this is inference from clustering
   behavior, not a measured density.** As the GM anticipated, the peasant/low-status lodging record
   is genuinely thin: cheap inns rarely appear in gazetteers (方志), which foreground official
   post-stations (驿) and higher-status *dizhan*/*kezhan*.

### Refuted - do NOT rely on these

- **"Cart-inns sat both along routes AND at the gate-quarter, paired and spaced every 40 li"** was
  voted down **0-3.** The 40-li spacing is a *route-stage* logic; grafting it onto a gate-pairing
  scheme is not supported. This is the specific reading closest to our "pair at every gate" rule,
  and it failed verification.
- **"The cart-inn was categorically the cheapest tier, with free hot food and rooms cheaper than an
  ordinary *kezhan*"** was voted down **0-3.** Treat the cart-inn as *a* cheap animal-yard type, not
  as *the* cheapest tier.

## Assessment: is the convention within norms?

**Directionally yes, but its symmetry is a stylization the evidence does not support.**

- **Supported:** cheap inns *did* concentrate in the gate-suburb (*guanxiang*) and along the
  arrival roads; a modest intramural cheap inn near a gate is plausible under the Song+ relaxation
  that put commerce inside the walls at all hours. The clientele (carters, peddlers, market-day
  farmers) and the animal-yard cart-inn type are solidly attested.
- **Not supported:** a systematic **one-outside-EACH-gate + one-inside** pairing. The evidence
  favors **clustering at the busiest gate / principal arrival road** (an "inn street" service node)
  over even distribution around the perimeter. And the **"stranded outside at dusk" rationale is
  weak** for the modeled Song/Ming period, since the curfew had relaxed - convenience/route-stage
  logic, not gate-closing, is the better driver.

So the current 4-per-city (2 in + 2 out, symmetric) reads as *too even and too many*, and rests
partly on a curfew rationale that is a Tang artifact.

## Options for adjustment (PENDING GM DECISION - not applied)

Ranked from lightest touch to fullest realism:

- **A. Do nothing.** The convention is directionally plausible and the symmetry is a legible
  cartographic stylization. Historical accuracy of low-status lodging is genuinely unknowable at
  the density level, so a clean symmetric rule is defensible as "close enough + readable."
- **B. Concentrate on the main arrival gate (what the research points to).** Bias cheap lodging to
  the **principal road-gate and its extramural *guanxiang*** as a small cluster - say 2-3 cheap
  inns, with the **cart-inn + animal yard extramural** - plus maybe **one humble inn inside near
  that same gate**. Leave the quieter gates *without* a paired flophouse. This drops a city from ~4
  evenly-spread to ~3-4 clustered at one gate, and matches the route-node + gate-suburb evidence.
- **C. Re-theme the rationale even if the layout barely changes.** Drop the "stranded by the dusk
  curfew" justification (a Tang artifact) in favor of "convenience lodging at the busy arrival gate
  for market-day peasants, carters, and peddlers." Cheap to do; corrects the *why* in the docs.
- **D. Add the animal-yard cart-inn as a distinct extramural type.** Right now the map pairs a
  flophouse with an inn+stables at each caravan cluster; the research says the *dachedian* is one
  integrated animal-yard lodging compound (front fodder court, rear stable court), extramural,
  drawing a service-node cluster. Could be modeled as a single labeled compound at the main gate's
  *guanxiang* rather than three separate glyphs. (Larger art/gen change.)

My recommendation if we change anything: **B + C** (concentrate at the main gate, re-theme the
rationale), which is the smallest change that moves us from "stylized-and-slightly-wrong" to
"stylized-but-grounded." But **A is genuinely defensible** given how thin the density record is -
this is exactly the nitty-gritty the GM flagged as often unknowable.

## Companion decision: gate markets at EVERY gate (2026-07-22)

A follow-up question - *would a city have a gate market at each gate?* - is the same *guanxiang*
(关厢) institution as the extramural lodging above, so it is recorded here. A focused search pass
(Baidu Baike 关厢; Beijing gate-suburb histories; Shanghai/Beijing wall-and-gate sources) found:

- **The *guanxiang* is a road-driven extramural suburb** - the main street plus residents-and-shops
  within ~2-3 *li* outside a gate, formed as built-up density pushed *outward along the road*. It is
  literally the gate market + gate suburb, the same cluster the cheap inns sit in.
- **It formed at every *trafficked* gate, not just one.** Old Beijing's sixteen gates each had a
  named *guanxiang* (Guang'anmen, Deshengmen, Yongdingmen, ...). This is stronger than the lodging
  pass's low-confidence "clusters at the busiest gate" inference: markets were more distributed than
  cheap inns.
- **They varied in scale** - a busy gate grew a 大关厢 ("big *guanxiang*") with many shops; a quieter
  gate a small one - and gates specialized (Beijing's grain gate, coal gate, wine gate).

**Decision (GM): a gate market forms outside EVERY city gate, scaled to that gate's traffic** - the
check `city_has_gate_market` was tightened from ">= 3 shops outside *a* gate" to ">= 3 outside *each*
gate" (mirroring `city_flophouse_outside_each_gate`). This is *better*-grounded than the old
one-gate rule, and it removes an inconsistency (the map already put a flophouse outside every gate
but a market at only one). Applied: **Tango** gained a smaller north-gate market (its two gates both
sit on the N-S Imperial road; the south market stays the larger); **Nagahara**'s north (highway)
gate gained a small stall cluster to sit alongside its river-gate WHARF suburb. The scale asymmetry
(big vs. small) is deliberate and matches the 大关厢/small distinction. The rule is scoped to
**main-road gates** (GM 2026-07-22): a purely military SALLY gate is traffic-free - it opens onto
empty field for siege sorties, with no road, market, flophouse, or caravan - so it carries no
*guan-xiang* and is exempt. The pool cities have no sally-gate (every drawn gate is a main road/river
gate, all held in `M["gates"]`), so "every gate in `gates`" already equals "every main-road gate."
A future sally-gate knob would store its gates separately, and the market/flophouse/caravan checks
(which iterate `gates`) would skip them automatically.

The *reliability* caveat mirrors the lodging findings: the *guanxiang* is best-documented for the
great capitals (Beijing), and the exact per-gate scale for a mid-size provincial seat is thinner -
but the road-driven formation principle is clear and consistent, and it points to a market at each
of a city's (road-carrying) gates. Sources: [关厢 (Baidu Baike)](https://baike.baidu.com/item/%E5%85%B3%E5%8E%A2/10087890),
[京城关厢传奇 (163.com)](https://www.163.com/dy/article/G9AGFITN0517QQCQ.html),
[Shanghai City Wall and Gates (Visualising China)](https://visualisingchina.net/blog/2020/10/29/shanghai-city-wall-and-gates/),
[City Wall and City Gate of Beijing](https://www.beijingtrip.com/feature/city-wall.htm).

## Sources & reliability

Curfew and Japanese-lodging findings rest on reputable secondary sources with multiple independent
corroboration (high). Several cart-inn spatial/ethnographic details rest on Chinese
wiki-encyclopedia pages (zh.wikipedia, Baidu Baike) - adequate for mundane facts, not primary. Key
sources: SCMP and encyclopedia.com on the Tang curfew; zh.wikipedia + Baidu Baike on *dachedian*;
japanesewiki / Wikipedia (Hatago) / ryokan.or.jp on *kichin-yado* and *shukuba*;
chinawriter.com.cn on inn typology.

**Dominant caveat:** time/region skew. The best-documented cheap-inn type (*dachedian*) is
late-Qing/Republican Northeast China, not Song/Ming Jiangnan; its detail is trustworthy for what it
describes but is *corroborating*, not direct evidence for the modeled period. Open questions worth a
later pass: an actual gazetteer/guild count of commercial (not official) lodging for a Song/Ming
walled town; the physical form of the rice-south *jimaodian* without the northern *kang*; and
whether any positive evidence exists for cheap inns *inside* the walls near a gate (vs. the absence
found here).
