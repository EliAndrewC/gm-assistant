# The domain-capital tier (`meta(scale="capital")`)

*Part of the Mode B settlement docs. The index, the `meta()` knobs, the workflow and the validator contract live in [`../settlements.md`](../settlements.md). Everything a capital SHARES with a provincial city - defenses, urban fabric, hinterland, river cities, the shared town/city vocabulary - is in [`cities.md`](cities.md) and [`urban-features.md`](urban-features.md), and a capital inherits all of it unless this file says otherwise.*

**Load this file when:** the subject is a domain capital.

> **STATUS: the budget (018), the SKELETON + castle (019) and the GROUND-RESERVING LAYER (020) are shipped; the HOUSING is not.**
>
> **Shipped and gated**: the space budget and tier knobs (`citybudget.CapitalProgram` / `plan_capital`, the caste table and rank split, `C_YASHIKI` / `C_TERRACE`, `castle_px2`, `castle_seat`, `imperial_granary_seat`, `--tier capital`, `capital_declares_a_budget` + `capital_wall_matches_budget`); the tier's drawing predicates (`CITY_TIER_SCALES`); **`Settlement.castle`** - the enceinte, its moat and gates, blank inside; and feature 020's ground-reserving layer - the government ward on the ote-suji (`capital_has_six_ministries` and family), the lineage compounds (`meta(lineages=..., ruling_lineage=...)` + the band checks), `manor(ink=...)` for the Imperial Magistrate, `granary(append=True)` -> `M['granaries']`, `s.towpath`, `s.aqueduct`, the shared crossing source (`bridge_carried_ways` / `bridge_crossed_waters` - ONE source for both the drawer and the checker), and the waterfront checks (`capital_no_road_parallels_river`, `capital_has_aqueduct` + terminus/outside-the-wall). See [`specs/018-capital-space-budget/`](../../../../specs/018-capital-space-budget/), [`specs/019-capital-skeleton-castle/`](../../../../specs/019-capital-skeleton-castle/) and [`specs/020-capital-ground-layer/`](../../../../specs/020-capital-ground-layer/).
>
> **NOT yet built (feature 021, the HOUSING)**: all housing (rank-graded samurai districts, walled yashiki, retainer terraces, commoner machi), the public wells and the aqueduct's in-wall draw-basins, the fire towers, the kido mesh, the entertainment district, the relay stables + farrier, and the rest of the capital check block (population fill among them).
>
> **The worked map is a DRAFT parked outside `pool/`** at [`wip/shiro-daika.gen.py`](../wip/shiro-daika.gen.py), because `test_villages.py` sweeps `pool/*/*.gen.py` and a map that is not green would turn `make done` red for every session. It fails exactly one check - `imperial_road_town_has_farrier` - and that failure is CORRECT: the map has no relay stables because it has no housing fabric. **Do not fix it by drawing the farrier**; that was tried and cascaded (forge -> stables -> wells), which is the engine correctly refusing to call a half-populated city coherent. Feature 021 makes it green and moves it into `pool/capitals/`.
>
> Every decision here is settled with the GM (2026-08-08/09) and grounded in [`../research/cities/capitals.md`](../research/cities/capitals.md).

**Research:** the historical basis for every rule here - what was found, the decision it drove, and every disclosed departure - is in [`../research/cities/capitals.md`](../research/cities/capitals.md). Load it when you are CHANGING a rule or questioning one, not to follow it.

---

## What a domain capital is

A capital is the daimyo's castle-town seat: **~12,360 inhabitants, 2,472 dwellings exactly** (the settled 12,000 of `budgets.md`'s Capital city table, plus the ~360 relocated non-working samurai; the ~45 foreign Imperial cohort sits inside that figure). It is **~5% of the whole domain's population**.

Commercially a capital is "just a larger version of a provincial city" (`l7r.md`), and its caste mix is the same shape at 4x scale - but it carries three things a provincial city does not: **the castle**, the **domain-tier government** (a daimyo rather than a governor, with the House Chancellery and the Imperial Magistrate's office beside it), and its role as the domain's **schooling-and-retirement magnet**, which is what lifts its samurai share from ~10% to ~13%.

**Critically, it is a merchant city with a castle in it, not a garrison with a market attached.** Historical castle towns ran 30-60% samurai; ours run ~13%, which `l7r.md` calls a deliberately restrained echo. So the rank-graded samurai rings are real but THIN, and the machi are the bulk of the fabric. See [the Hikone anchor](../research/cities/capitals.md#our-capital-is-a-hikone-scale-market-town-carrying-a-quarter-of-hikones-samurai).

| Caste | Households | vs provincial |
|---|---|---|
| Servants | 480 | x4 |
| Laborers | 960 | x4 |
| Merchants | 600 | x4 |
| Burakumin | 120 | x4 |
| Samurai (domestic) | 240 | x4 |
| Samurai (relocated, non-working) | +72 | new to the tier |
| Samurai (foreign - the Imperial Magistrate's office) | +12 | a 5-yoriki sub-station at provincial tier |
| Farmers | **0** | unchanged - the wall encloses no farmland |

Wealth bands that drive glyph variety: **48** very-rich merchant households (vs 12), 72 rich merchants, 120 master laborers.

## Wall and compound geometry: rectangles, not circles

**Small compounds AND large enclosures are both rectilinear in the anchor traditions** (GM asked
2026-08-09; [research](../research/cities/capitals.md#wall-geometry-rectangles-and-terrain-loops---the-circle-is-the-form-both-anchors-decline)).
China walls every tier square by cosmology (round heaven, SQUARE earth - Kaogongji's ideal
capital, and the built record from Pingyao to Beijing agrees); Japan builds angular terrain-fit
baileys inside and an organic sogamae loop around the town. Neither goes circular as walls grow -
the attested round walls (Shanghai 1553, the Hakka tulou) are speed-and-economy or communal-clan
forms, not seats of rank. So: **the castle enceinte and every government compound stay
rectangular**; a round keep would be European grammar. The pool's ~elliptical city rings are a
disclosed house style (closest to the sogamae loop), kept deliberately - reshaping shipped maps
is a GM call.

## Scale and the wall

**`ftpx=3`, unchanged from the provincial tier**, and the render width rises instead (~4,600-4,800 px, vs 2,600). Dropping to 4 or 5 ft/px would shrink every glyph with `bscale = 1/ftpx` - a 34x24 ft laborer house becomes 6.8x4.8 px - and the to-scale doctrine forbids rescuing that by drawing things bigger. Keeping the grain also keeps a merchant house the same size on every map in the pool, which is what lets a capital be compared to a provincial city by eye. `render_png` already takes the width; `DIAGRAM_PNG_WIDTH` already exists.

**The wall is a budget output, never a hand-picked number** - the same rule as [`cities/sizing.md`](cities/sizing.md), and it binds harder here, because **a median castle is ~85% of an entire provincial city's interior** ([research](../research/cities/capitals.md#a-median-castle-is-85-of-an-entire-provincial-city)). A capital's ring encloses roughly four provincial cities of inhabitants plus most of a fifth in castle, so population alone predicts it badly.

Rough expectation, to be REPLACED by `plan_city`'s output: interior ~3.6M px^2, radii ~2.27x Tango's (rx ~1,115, ry ~1,046), ~1.27 mi across, ~4 mi circuit.

## The castle

Drawn as an **enceinte, and BLANK INSIDE** - walls and moat only, exactly as a governor's mansion and a magistrate's manor are drawn (GM 2026-08-08). **No building of any kind is placed inside it on the city map** - not the tenshu, not the goten, not the granary or the armory.

### WHY blank: the sync argument (general doctrine, not a castle rule)

The GM's reasoning generalizes to every compound this project draws as an implied interior, so it belongs here as doctrine:

> *"I plan to also show a separate diagram for them. And if we fill in any details at all on the map, then the diagram will need to match and be kept in sync with the map, which will add a layer of difficulty... I'd rather nothing be shown than the WRONG thing be shown."*

Any interior detail on the settlement map becomes a **constraint on the Mode A sheet** that must later be drawn to match it - and a constraint nothing enforces, so the two drift silently and the map ends up asserting something the compound plan contradicts. An empty compound asserts nothing and can never be wrong. **The cost of the blank is legibility; the cost of the detail is a contradiction nobody catches.** The blank wins until a real sync mechanism exists.

A future automated cross-check (a Mode A sheet's own footprints projected onto the Mode B compound) would let this relax, and the GM wants that eventually. Until then: **walls only**.

### What that leaves, and the one open question

`castle_px2` is a **declared program line**, defaulting to ~598,000 px^2 (~50 ha) with a documented 50-230 ha band - and that ground is spent whether or not anything is drawn on it, because the budget prices the WORKS, not their contents.

**DECIDED AND ANSWERED - the experiment ran, and the walls are OUT (2026-08-09).**

The GM authorized one attempt ("let's make one attempt and if it doesn't work then we'll just remove them"). Two renders were made and the answer is no.

- **Attempt 1** drew the wards CONCENTRIC and axis-shared. It read as a **bullseye** - a target symbol, not a fortress.
- **Attempt 2** fixed the obvious errors: the wards were OFFSET toward the far side from the ote-mon (so an attacker crosses the whole works under fire), the wall weights were graded, and the masugata was enlarged until it was actually visible. A real improvement, and **still nested rectangles**.

**The finding, which is what generalizes: rectangles inside rectangles read as ABSTRACTION however they are arranged.** What makes a castle read as a castle is irregular ward outlines, substantial water *between* the wards, and corner yagura - and none of those survive being drawn walls-only at 3 ft/px. So the internal works bought nothing and cost a Mode A sync surface, and the blank rule wins on its own terms rather than by argument.

**`Settlement.castle(baileys=...)` therefore defaults to False.** The knob stays, because the finding is about THIS drawing vocabulary rather than a law - a future castle with irregular wards could revisit it.

**One thing DID survive the experiment**: the **ishigaki doubling** on the outer enceinte - a battered stone rampart drawn as a doubled line reads as mass where a single stroke reads as a fence. That is the OUTER wall, so it adds no sync surface the wall did not already have. It is kept.

**A caveat on the verdict's strength, stated because it matters for feature 020**: the blank castle was judged inside a blank city, where everything reads as empty. Once the fabric lands and the castle is the one large walled thing at the heart of a dense map, it will read considerably better than it does now. If it still reads as a void THEN, that is the point to revisit - not now.
**Build order consequence:** the castle glyph is the FIRST thing feature 019 builds, ahead of the city fabric, precisely so this call can be judged off an early render rather than at the end of a long build.

### The inventory: what is INSIDE (never drawn on the city map) vs OUTSIDE (must be)

This is the list the GM asked for - the point of the blank is that we still know what it contains.

| INSIDE the castle - implied, drawn only on its own Mode A sheet | OUTSIDE - drawn in the city like any other feature |
|---|---|
| the **tenshu** (keep) | the **six domain ministries** + government ward, on the ote-suji avenue |
| the **goten** - the daimyo's residence and audience halls | the **House Chancellery** |
| the **domain granary, SIEGE stock** | the **domain granary, STIPEND rice + transhipment**, at the wharf |
| the **armory** | the **brokers' row** (merchant) beside that granary |
| the **treasury** | the **Imperial Magistrate's compound** (foreign sovereign ground) |
| the **castle guard's barracks** (the daimyo's own retinue) | the **Emperor's granaries** (`imperial_granary_seat`: magistrate or wharf) |
| the daimyo's **stables** and **private gardens** | the **domain school** (*hanko*) |
| the castle's **wells and cisterns** | the **state martial hall** + rolled private dojos |
| | the **8 lineage compounds** (daika, the ninth, IS the castle) |
| | the **2 sovereign temples** + the teramachi rim |
| | the **wharf**, dock, jetties, quay frontage, towpath |
| | the **aqueduct**: intake, open canal and kakehi outside; draw-basins inside |
| | all **samurai districts** - walled yashiki, detached houses, retainer terraces |
| | all **commoner machi**, markets, the road ribbon, entertainment district |
| | the **bell-and-drum tower**, fire towers, public wells |
| | **burakumin quarters**, tanning yards, the execution ground |
| | **gate furniture**, gate markets, flophouses, caravan clusters |

**The one that matters most**: the domain's rice appears TWICE, in two places, for two reasons - siege stock inside the castle, working stipend-and-transhipment rice at the wharf. Drawing only one of them would misrepresent how the domain actually holds its grain.

**Two seats, and they are not symmetric:**

- **`castle_seat="ring"` (DEFAULT).** Closed elliptical rampart as today; the castle stands inside with its own moat and walls; the quarters wrap concentrically. Both traditions nest their citadel this way ([research](../research/cities/capitals.md#both-traditions-nest-a-walled-citadel-in-the-seat-so-a-centered-castle-is-the-median-form)), so this is the median form and not one of two coin-flip options.
- **`castle_seat="edge"`.** The castle occupies one arc of the perimeter and its own outer moat FORMS that stretch of the city's defense. **Requires water on that flank** (`river=` or a coast) - every attested edge castle is a river or sea castle, and a castle on a dry edge is not a variant but a weak wall.

**Build order:** the ring first. The edge mode is both the rarer form and the bigger engine change (an open wall arc closing onto the castle works, structurally the same problem `s.moat(river=...)` already solved), and the skill's own recorded lesson is to **lock the rules in against ordinary settlements before bending them for exceptions** ([`../CLAUDE.md`](../CLAUDE.md), "Declared overrides").

## The government ward

**The six domain ministries sit OUTSIDE the castle's outermost gate, flanking the *ote-suji* approach avenue** - not inside the works. Both traditions converge on this at exactly this tier ([research](../research/cities/capitals.md#the-ministries-sit-outside-the-castle-flanking-the-approach-avenue)): Beijing's Six Ministries lined the Corridor of a Thousand Steps outside Chengtianmen, and a jokamachi's offices spilled out of the ninomaru into the town as they grew.

This makes the castle's **front** the map's compositional axis, which is the jokamachi rule that main roads ran past the castle's front "to indicate the glory of the ruler." A ceremonial avenue with paired ministry compounds is the most legible way for a map to say *daimyo's seat* rather than *big city*. It also keeps the castle interior implied and `s.ministry` working unchanged.

The **domain school** sits on the same avenue.

## Compounds with no provincial equivalent

1. **The Imperial Magistrate's compound** - ~56 staff plus ~12 family; `budgets.md` funds "manor maintenance, grounds, stable, fortified walls, ceremonial halls" at 700 koku/yr. **Foreign sovereign ground**, and it should read as such - its own ink, the way state violet marks the martial hall.
2. **The Emperor's local granaries**, which that magistrate oversees - distinct from the domain's own granary complex, itself new (the capital is where the domain's tax rice lands).
3. **The House Chancellery** - a council hall for the domain's 5-10 lineage representatives.
4. **Cosmopolitan lineage compounds.** `l7r.md`: cosmopolitan lineages are "based in their domain's capital." Named, labeled walled yashiki in the samurai ward. This is the tier's best flavor feature - it is what makes a capital read as a SPECIFIC domain's seat rather than a generic large city.
5. **The domain school** - the *hanko*, the reason samurai families across the domain send children here.
6. **Inkyo retirement housing**, temple-adjacent, for the relocated elders.
7. **Sovereign temples with Grand Abbots.** `l7r.md`: "the Temple of Bishamon refers to the sovereign temple in the domain capital"; "every domain capital has at least two grand abbots." Head house of the domain's whole Order - abbot's residence, order administration, library. A different program, not a scaled precinct.
8. **A Witch Hunter's office** - rolled/optional (Hantei ordered one per capital; some orders were later rescinded).
9. **Trade-named machi** - *Kaji-machi*, *Gofuku-machi* and the like, from the attested occupational segregation. Cheap to draw, high payoff.

## Ward structure: a MESH of night-barred gates, not walled quarters

**Recommendation, pending the GM's decision** - this is the research pass the GM asked for before any decision on how many walls the city has. Full finding: [research](../research/cities/capitals.md#neither-tradition-walls-its-wards-the-answer-is-a-mesh-of-night-barred-gates).

Both traditions reach the same institution independently, and it is not enclosure. Edo barred every **machi** block with a **kido** (open ~4 am to ~10 pm) and every tenement lane with its own **roji-kido** (locked ~6 pm to ~6 am, keys with the nagaya owner or trusted neighbors), the block collectively responsible for its own gate. Qing Beijing, having torn down the Tang *fang* walls in the Song, closed each street at night with **zhalan** palings - the street Dashilan (大栅栏, "Big Palings") is named for its gate - backed by a real curfew (dusk drum at 8 pm, dawn bell at 4 am, 40 lashes for being abroad at night).

So, at capital scale:

1. **No continuous ward fence.** Kido at the block and lane mouths instead - the glyph `s.kido` already draws, at far higher count and a different placement rule. **No new vocabulary.**
2. **SEVERAL samurai districts, interleaved with commoner strips** along the major thoroughfares (the attested jokamachi pattern), not one contiguous sealed quarter.
3. **The walled compound does the sealing** - which is exactly what the inverted no-manor-inside-the-wall rule below provides.
4. **The bell-and-drum tower gets a documented job**: it sounds the curfew the kido enforce.

**Flagged, not acted on:** this research says the provincial tier's continuous palisade (`city_samurai_ward_sealed` and family) is more than history supports there either. That is a separate question for the provincial tier - three shipped cities depend on those checks, and the capital can adopt the mesh without any of them changing.

## Placements that change

- **Teramachi rim.** Temples belt the inner face of the rampart as part of the defenses, rather than gathering in one quarter ([research](../research/cities/capitals.md#both-traditions-nest-a-walled-citadel-in-the-seat-so-a-centered-castle-is-the-median-form)).
- **Rank-graded samurai districts.** Proximity to the castle tracks rank, and the districts are several rather than one - see the ward section above.
- **Retainer terraces.** Modest terraced housing for the capital's **~94 junior (Rank 1-4) samurai households** - castle guards, household retainers of the daimyo's retinue, junior officials in training. **NOT "ashigaru" anything** (GM 2026-08-08): in Rokugan ashigaru are **peasants**, not samurai, and l7r.md puts them in the villages as rural militia, so a capital has no ashigaru quarter at all. The historical *kumi-yashiki* housed the lowest *samurai*, which is the slot the retainer terrace fills.

## Rules that INVERT

- **`city_samurai_housing_varied` bans `s.manor(...)` inside the wall ring** - in a provincial city the only walled samurai compound is the governor's. Backwards here: karo, councilors and chancellors live in walled yashiki INSIDE the wall, and that is both the defining texture of a castle town and the mechanism for the lineage compounds above.
- **The senior/junior housing mix inverts** ([research](../research/cities/capitals.md#the-capitals-samurai-are-senior-heavy-which-inverts-the-provincial-housing-mix)). budgets.md's rank table puts the capital at **70% senior (R5+) / 30% junior**, against the provincial city's **27% / 73%** - a capital posting is prestigious even when the job is menial, and the capital absorbs the rank-by-association cohort. So large houses and walled yashiki are the MAJORITY of the samurai fabric here (~218 senior against ~94 junior households of ~312), where `city_samurai_housing_varied` wants senior houses to be a minority. **The retainer terraces are the minority texture, not the dominant one.**
- **`city_has_governor_mansion` / `city_governor_mansion_large`** - a capital has no governor.

## Counts that multiply

| Feature | Provincial | Capital |
|---|---|---|
| Gates | 2 | 4+ (Imperial road N-S, domain road E-W) |
| Walled merchant estates | rolled 1-3 of 12 rich families | 48 rich families; needs its own roll column, ~4-8 |
| Martial establishments | 1 state hall + 1-2 rolled | 1 domain school + the SAME 1-per-200 roll (~7-8) - see below |
| Fire towers | 2-3 | ~10-15 (the watch radius is fixed in world px; area is ~5x) |
| Public wells | 87 (Tango) | ~160-240 (1 per 10-20 households) |
| Theater stages | 1 | several, plus an entertainment district (`l7r.md`: "numerous entertainers") |
| Burakumin quarters | 1 in-wall | likely 2, with 2 tanning yards |
| Merchant kura | >= 5 | ~20 |
| Named machi | not modeled | Hikone's 53 wards is the anchor |

Everything per-gate (gate market, outside flophouse, caravan cluster, kosatsuba, inspection station) scales for free once gates are a count rather than a pair.

## Martial training: the private-dojo roll does NOT change at this tier

**The capital keeps the same 1-per-200-samurai private-dojo roll as a provincial city** (~7-8 halls at ~1,560 resident samurai). What it gains is not more private halls but the **domain school**, and that is the historically grounded distinction: the *hanko* and its *bugeijo* were built in **castle towns**, and private *machi-dojo* are a late, metropolitan phenomenon. See [`cities/government.md`](cities/government.md), "Historical grounding: martial training", which now separates what is attested from what was extrapolated.

## Water: an AQUEDUCT, in addition to the wells

**Decided (GM 2026-08-08): a capital carries an aqueduct system on top of its wells** - larger cities outgrow what wells alone can supply, and the great castle towns built conduits for exactly this reason (Edo's Kanda and Tamagawa *josui*, Odawara's *sosui*).

The wells do not go away: 2,472 households at the provincial rate of 1 per 10-20 households still puts ~160-240 draw-points across the commoner quarters, and the existing `city_neighborhoods_have_wells` / `city_well_density_sufficient` / `city_wells_in_block_interiors` family carries over unchanged.

**The form is settled** ([research](../research/cities/capitals.md#the-aqueduct-is-open-outside-the-wall-and-buried-inside-it---and-the-boundary-is-the-gate)): the historical system is **open outside the wall and buried inside it, with the city GATE as the boundary**. That gives the GM's above-ground preference most of the interesting length, honestly:

1. the **intake works** on the river;
2. the **open approach canal** running to the wall (Edo's ran 43 km as a plain earth cut);
3. a ***kakehi*** - an open flume carried across a watercourse on a bridge - where the geography needs one. This is the most striking element in the system and fully attested: Edo's Suidōbashi, "aqueduct bridge," is named for it and Hiroshige drew it;
4. its **terminus at a gate**.

**NO ARCADES.** There is no East Asian arcaded aqueduct - the vocabulary is gravity canal at grade, buried pipe, and a flume bridge only where water must be crossed. Arches are the one form the possibility space excludes.

Inside the wall the conduit is honestly buried, and is represented by what a resident actually sees: **its draw-points**. So the in-wall aqueduct reads as a distinguishable aqueduct-fed draw-basin among the ordinary wells, not as a fake surface channel.

## Wharf and the tax-rice warehouses

**Wanted (GM 2026-08-08), and the research changes its shape** ([research](../research/cities/capitals.md#the-wharf-is-the-collecting-end-and-kurayashiki-is-the-wrong-word-for-it)).

**Do NOT call this a *kurayashiki* district** - an earlier draft of this file did, and it was wrong twice. A kurayashiki is a daimyo's warehouse-residence **at the market** (Osaka, 110+ of them at peak), where tax rice was *sold*. A domain capital is the **collecting-and-disbursing** end: rice comes up from the six provinces into the **domain granary**, most goes straight back out as samurai stipends (*kuramai*), and the surplus ships downriver.

The model is **Asakusa Okura / Kuramae** - the ruler's own riverside granaries, with the district in front of them named "before the storehouses." That yields a chain of three features linked by one mechanism, which is what will make this waterfront read as a real place:

    river wharf -> the domain granary -> the brokers' row in front of it -> the entertainment district next door

Nagahara supplies most of the vocabulary already (`s.dock`, `s.jetty`, `s.canal`, `s.water_gate`) - see [`cities/river-cities.md`](cities/river-cities.md). The castle keeps the siege stock (above), so the waterfront carries the working rice.

**The brokers' row is MERCHANT** (GM 2026-08-08), so draw it as merchant frontage with the wealth band skewed high - not state violet. budgets.md's "rice/coin arbitrage" line for the Ministry of Retainers covers **the paying of stipends only** (denomination, the rice-versus-coin split, payment-day logistics); the contracts, clearinghouse business and lending sit outside it, and the merchant class has grown rich on them exactly as the *fudasashi* did. So the Edo chain holds and the entertainment district belongs beside the granary because **the brokers' money is what builds the theaters**. [Research](../research/cities/capitals.md#the-brokers-row-is-merchant-and-the-ministrys-cut-is-narrower-than-it-looks) - and note the general reading it establishes: a ministry line prices the ministry's own administrative function, not the whole trade it touches.

**The Emperor's granaries are SEPARATE and OUTSIDE the castle** (GM 2026-08-08), because they face a different threat: an invading neighbor would not attack the Emperor's stores, so they need protection from **brigands, not besiegers**. A stout wall and a watch suffice, and there is no reason to spend castle ground on them. Their seat is a **tunable knob**, both options being real answers: `meta(imperial_granary_seat="magistrate")` puts them beside the Imperial Magistrate's compound (the official who oversees them is right there), `"wharf"` puts them on the water (grain moves by boat). Neither is a strong default - like the castle seat, it is a genuine either/or that gives two capitals different skeletons for a documented reason.

## Settled defaults

- **No agricultural district.** A capital walls its farms out; the wall encloses all 12,360 inhabitants and no farmland.
- **The Imperial road always runs through**, so the commercial ribbon rule always applies ([`cities/fabric.md`](cities/fabric.md)).
- **Clan identity changes LABELS ONLY** (GM 2026-08-08). Scorpion, Crab or Crane, "all clans fundamentally have the same needs and the same shared material reality" - so the tier's layout, program and proportions are clan-independent, and what varies is dedications, names and the occasional individual city's character. Do not build clan-specific layout rules.

## The first worked example: Shiro Daika (planned)

The Daika domain is a **Bayushi vassal house of the Scorpion**, already established in the pool - [`pool/towns/ubame.gen.py`](../pool/towns/ubame.gen.py) is one of its county towns, in Moriguchi province, and its charcoal road runs "west toward Shiro Daika."

- **Clan:** Scorpion, so the two sovereign temples are **Benten and Jurojin** (`CLAN_FORTUNES`).
- **Borders the Crab to the SOUTH**, so `wall_defense="siege"` - built to survive one even after a long peace.
- **A river runs NE -> SW** (consistent with Ubame's NE-high land fall), so it is a **river city**, and `cities/river-cities.md` applies in full.
- **`castle_seat="ring"`** - the default, and no new wall geometry (Nagahara is already a river city with a closed ring).

### Shiro Daika's roads and gates (GM 2026-08-08)

Confirmed against the campaign map (Shiro Daika sits in Daika's red territory west of the Kitsune Mori, with Shiro Kyo to the northwest):

| Way | Bearing | Goes to |
|---|---|---|
| **Imperial road** | enters the **SOUTH gate**, runs N-S through the city | south into the domain; beyond the north gate it bends **northwest toward Shiro Kyo** |
| domain trunk road | **east** | Fox lands / the Kitsune Mori - the same charcoal road [`pool/towns/ubame.gen.py`](../pool/towns/ubame.gen.py) draws running "west toward Shiro Daika" |
| domain trunk road | **southwest** | the heart of the Daika domain |

So **four gates**: south (Imperial), north (Imperial), east, southwest. Only the Imperial road is labeled.

**The river gets a TOWPATH, not a road** (GM asked 2026-08-08 whether a riverside road would supplement or be replaced by the water; [research](../research/cities/capitals.md#a-river-gets-a-towpath-not-a-road---and-they-are-not-the-same-feature)). Water carried bulk far more cheaply than carts, so a trunk road shadowing a navigable river is redundant - Japan made the point at its sharpest by PROHIBITING bridges and ferries at the Oi-kawa so the river would work as a checkpoint. What is real is the Chinese *qiandao* (纤道) **towpath**: Shaoxing's dates to 815 CE and runs 40+ km, and Marco Polo saw barges hauled along it by teams of horses. It exists *because* of the boats - upstream haulage - so it supplements water transport exactly as the GM guessed. Draw it narrow, on the wharf's own bank, distinct from a road (no roadbed, no lane centerline), running to the wharf and no further; plus the quay frontage (*kashi*) inside the wall, which belongs to the wharf district. Do NOT draw a trunk road paralleling the river.

**This settles the *ote*.** The jokamachi rule is that the main road passes the castle's FRONT "to indicate the glory of the ruler", and the Imperial road connects at the south gate - so **the castle's ote-mon faces SOUTH**, and the ceremonial avenue with its flanking ministries runs south from the castle to that gate. That avenue is the map's compositional axis.

### Shiro Daika's lineage compounds (GM 2026-08-08)

The Daika house carries **nine** lineages - more than usual (Reiji has 7, Kitsune and Kyo 5) - and they are already in the chargen config (`webapp/development-defaults.ini`, `[house][[daika]]`), whose weights are percentages of the domain's samurai. Two config facts do all the work, so **none of this is invented**:

- `l7r.md`: a lineage at **>= 10% of the domain** usually holds a Chancellery seat. That gives exactly **six chancellors** - daika 19, hazama 16, utsuro 15, tokiwa 14, anzu 12, kurogi 11 - and leaves **yodo 5, nio 4, seki 4** off it, with correspondingly smaller holdings.
- `[provincial_lineages][[daika]]` marks **kurogi = Moriguchi province**, and the configspec states that a lineage with no entry is **cosmopolitan (capital-based)**. So kurogi is Daika's one **dynasty/provincial** lineage - its seat is out in Moriguchi (the province Ubame county sits in), not here.

That yields a compound hierarchy the map can draw at four visibly different sizes, with the size tracking a published number rather than a guess:

| Compound | Lineage | Character |
|---|---|---|
| **the castle** | **daika** (19) | the ruling lineage's seat IS the castle - it needs no separate yashiki |
| 4 grand chancellery yashiki | **hazama** (16), **utsuro** (15), **tokiwa** (14), **anzu** (12) | cosmopolitan chancellors, seated in the capital; the largest walled compounds after the castle |
| 1 smaller lineage estate | **kurogi** (11) | on the Chancellery and PROVINCIAL. **The chancellor still lives in the capital and still holds a lineage estate** (GM 2026-08-08) - a Chancellery seat is held in person. It is smaller only because it houses FEWER LINEAGE MEMBERS: most of the kurogi live out in Moriguchi province, around their own provincial city |
| 3 modest houses | **yodo** (5), **nio** (4), **seki** (4) | below the Chancellery threshold, so smaller holdings |

**Draw them labeled.** Eight named compounds graded by real weights (the ninth, daika, is the castle) is what will make this read as *Shiro Daika* rather than as a generic capital - and the kurogi case, a full chancellor on a visibly smaller plot because his people are elsewhere, is the kind of specific a generic city cannot fake.

**The size tracks HOUSEHOLDS HOUSED, not rank.** That is the rule the kurogi correction establishes: every chancellor is present in person, so a compound's footprint reads how many of that lineage live in the capital, not how important its head is. A provincial lineage is therefore small-but-grand rather than absent.

Note the pool's defense tiers after this: `peaceful` (Minami), `siege` (Tango, Nagahara, Shiro Daika). **The DEFAULT tier, `garrison`, still has no worked example anywhere.**

## Open, still to settle

- **Lineage names** for the cosmopolitan-lineage compounds (5-6, per `l7r.md`'s chancellery size).
- **Perf.** ~2,472 dwellings against Minami's 541. `_fits` is spatially indexed so per-seat cost is roughly flat, but `fill_exactly` and the `SeatMemo` re-visit dynamics are unmeasured at this volume. Budget a perf pass and a `GEN_TIME_BUDGETS` entry.
- **`SAMURAI_INWALL_FRAC` for a capital.** 2/3 at provincial tier; a capital should run higher (proximity to the court is the point of the posting, and the walled yashiki is what keeps the senior cohort in-wall). ~0.85 is an estimate, and it moves ~40 households of the priciest housing type.
- **Gate count**, and which gate is the *ote* on the ceremonial axis (it interacts with the river and the Imperial road).
- **Whether the tight-crop-to-the-wall convention survives** four gate-suburbs at this scale.
- **The provincial-tier ward question** raised by the ward research - separate from this tier, and not to be fixed in passing.

**Resolved since the first draft:** ward structure (researched, recommendation above), clan character (labels only), the granary and armory (inside the castle, not drawn), the aqueduct (yes, plus its form), the "ashigaru terrace" error (corrected to retainer terraces), the brokers' row (merchant), the Emperor's granaries (separate, knob-sited), and the per-household ground costs (below).

## Per-household ground costs (proposed `citybudget.py` rows)

Full derivation and confidence: [research](../research/cities/capitals.md#per-household-ground-costs-for-the-two-housing-types-the-budget-model-has-never-seen). The model prices only `C_PACKED` (690) and `C_SPACED` (2,480); a capital needs two more.

| new row | value | anchor |
|---|---|---|
| `C_YASHIKI` (walled samurai compound, in-wall) | **~4,150 px^2** | the Fukui **Suginuma plan**, a 1,000-koku retainer's 28 x 32.5 ken plot (~167 x 194 ft = 3,600 px^2), plus ~1.15x street margin |
| `C_TERRACE` (retainer terrace, Rank 1-4) | **~660 px^2** | Shibata's ICP *ashigaru-nagaya* (8 households, 143 x 21 ft, 18 ft frontage each) as the floor, the detached samurai house as the ceiling |

Gross-up ratios measured from the three shipped cities: **5.6x** drawn footprint for packed rows, **7.5x** for detached samurai houses. `C_TERRACE` is the softer of the two new numbers - bracketed at both ends by real measurements, but its position between them is a judgment. **Re-derive both against the first capital's drawn map**, exactly as `C_PACKED`/`C_SPACED` were back-predicted from Tango.

**What they make the wall:** required interior ~**3.2M px^2**, derived ring ~**rx 1,056 / ry 982 px** - about 1.2 x 1.1 miles across, a ~3.6 mile circuit. Two knock-ons: **the existing 3,200 x 2,700 canvas still fits it** (needs ~2,412 x 2,264 with moat and margin), and **`plan_city` will refuse a capital outright** - `POP_MIN, POP_MAX = 2000, 4000` raises rather than clamps, so the tier needs its own band and caste table rather than a widened provincial one.
