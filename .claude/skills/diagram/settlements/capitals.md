# The domain-capital tier (`meta(scale="capital")`)

*Part of the Mode B settlement docs. The index, the `meta()` knobs, the workflow and the validator contract live in [`../settlements.md`](../settlements.md). Everything a capital SHARES with a provincial city - defenses, urban fabric, hinterland, river cities, the shared town/city vocabulary - is in [`cities.md`](cities.md) and [`urban-features.md`](urban-features.md), and a capital inherits all of it unless this file says otherwise.*

**Load this file when:** the subject is a domain capital.

> **STATUS: DESIGN RECORD, NOT YET IMPLEMENTED.** No `scale="capital"` exists in `settlement.py` or `check_village.py`, no capital is in the pool, and nothing below is gated. This file records what the tier WILL be, and every decision in it is settled with the GM (2026-08-08) and grounded in [`../research/cities/capitals.md`](../research/cities/capitals.md). Implementation goes through spec-kit as feature work, per the root [`CLAUDE.md`](../../../../CLAUDE.md).

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

## Scale and the wall

**`ftpx=3`, unchanged from the provincial tier**, and the render width rises instead (~4,600-4,800 px, vs 2,600). Dropping to 4 or 5 ft/px would shrink every glyph with `bscale = 1/ftpx` - a 34x24 ft laborer house becomes 6.8x4.8 px - and the to-scale doctrine forbids rescuing that by drawing things bigger. Keeping the grain also keeps a merchant house the same size on every map in the pool, which is what lets a capital be compared to a provincial city by eye. `render_png` already takes the width; `DIAGRAM_PNG_WIDTH` already exists.

**The wall is a budget output, never a hand-picked number** - the same rule as [`cities/sizing.md`](cities/sizing.md), and it binds harder here, because **a median castle is ~85% of an entire provincial city's interior** ([research](../research/cities/capitals.md#a-median-castle-is-85-of-an-entire-provincial-city)). A capital's ring encloses roughly four provincial cities of inhabitants plus most of a fifth in castle, so population alone predicts it badly.

Rough expectation, to be REPLACED by `plan_city`'s output: interior ~3.6M px^2, radii ~2.27x Tango's (rx ~1,115, ry ~1,046), ~1.27 mi across, ~4 mi circuit.

## The castle

Drawn as an **enceinte, not as a keep**. At 3 ft/px a tenshu footprint is just another building box (Hirosaki's is ~0.6 ha, **1.2%** of its castle), so what makes a castle read as a castle is its works: concentric baileys as walled open ground, *masugata* dogleg gate approaches, the batter of the ishigaki, its own moat. The tenshu and *goten* footprints are marked; everything else is implied, exactly as the governor's mansion and the magistrate's manor imply their interiors, and a separate Mode A sheet follows later.

**The granary and the armory are INSIDE the castle and are NOT drawn** (GM 2026-08-08). They are real and they are in the works, but they belong to the castle's own Mode A sheet, exactly as a magistrate's manor and a governor's mansion keep their interiors off the settlement map. This is the general rule for anything inside the enceinte: **the only things marked are the works themselves plus the tenshu and goten footprints.** It also settles where the domain's siege stock lives, and leaves the wharf kura (below) to carry the transhipment story.

`castle_px2` is a **declared program line**, defaulting to ~598,000 px^2 (~50 ha) with a documented 50-230 ha band.

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

**Still to research before this is drawable** - the FORM, which is not obvious and matters a lot on a map: a *josui* was largely a **buried** conduit feeding open draw-basins, so what is actually visible may be only the intake works, the approach outside the wall, and the basins. If most of it is underground, the aqueduct is a small number of legible fixtures rather than a line across the map, and the budget line changes accordingly.

## Wharf and the tax-rice warehouses

**Wanted (GM 2026-08-08).** The whole domain's tax rice - six provinces' worth - lands at the capital, and Shiro Daika sits on a NE-SW river. With the castle holding the siege stock (above), the wharf carries **transhipment**: a dock basin, jetties, and a *kurayashiki* warehouse district on the water.

Nagahara already supplies most of the vocabulary (`s.dock`, `s.jetty`, `s.canal`, `s.water_gate`) - see [`cities/river-cities.md`](cities/river-cities.md). What is new is the SCALE of the kura district and the question of where the **Emperor's local granaries** sit, which the Imperial Magistrate oversees separately from the domain's own stores. Both need a research pass before the budget prices them.

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

Note the pool's defense tiers after this: `peaceful` (Minami), `siege` (Tango, Nagahara, Shiro Daika). **The DEFAULT tier, `garrison`, still has no worked example anywhere.**

## Open, still to settle

- **Lineage names** for the cosmopolitan-lineage compounds (5-6, per `l7r.md`'s chancellery size).
- **Perf.** ~2,472 dwellings against Minami's 541. `_fits` is spatially indexed so per-seat cost is roughly flat, but `fill_exactly` and the `SeatMemo` re-visit dynamics are unmeasured at this volume. Budget a perf pass and a `GEN_TIME_BUDGETS` entry.
- **Per-household ground costs at capital scale** - the budget model has no row for a walled yashiki or a retainer terrace, and without both the derived wall is wrong in the hardest direction to notice.
- **Aqueduct FORM** (how much of a *josui* is visible), and the **wharf / kurayashiki** program including where the Emperor's granaries sit - both flagged in their sections above.
- **Gate count**, and which gate is the *ote* on the ceremonial axis (it interacts with the river and the Imperial road).
- **Whether the tight-crop-to-the-wall convention survives** four gate-suburbs at this scale.
- **The provincial-tier ward question** raised by the ward research - separate from this tier, and not to be fixed in passing.

**Resolved since the first draft:** ward structure (researched, recommendation above), clan character (labels only), the granary and armory (inside the castle, not drawn), the aqueduct (yes, in addition to wells), and the "ashigaru terrace" error (corrected to retainer terraces).
