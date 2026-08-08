# Research: Domain-capital space budget

**Phase 0. This file is the Principle XII OPENING GATE.** For every element the budget prices it states what the historical reality was, whether the design matches it, and **what determines the element in reality** - because a generator usually gets the *existence* of a thing right and its *governing variable* wrong.

The full findings, with sources and disclosed departures, live in [`research/cities/capitals.md`](../../.claude/skills/diagram/research/cities/capitals.md). This file does not restate them; it records what each budget NUMBER rests on and where the design was changed to match.

---

## A. The one disclosed inversion: Japan leads at this tier

The project's standing order is China-first, Japan as tiebreaker. **The capital tier inverts it**, because the subject is a daimyo's castle town - a Japanese institution. A Chinese prefectural seat has a yamen and sometimes a walled inner citadel, but no tenshu, no rank-graded concentric samurai rings, and no teramachi rim, because imperial China had no resident hereditary military aristocracy to house; its local officials were rotating appointees who lived *in* the yamen.

China is still used where it has something to say, and on the two structural questions the two traditions **agree**, which is why the inversion costs little: both nest a walled citadel in the seat, and both put the bureaucracy's own compounds outside the ruler's enclosure once it is large enough to have them.

The tiers below keep the standing order. Recorded as a `liberty` in the research file rather than taken silently.

## B. Element by element

### The castle line (`castle_px2`, default ~598,000 px^2)

- **Historical reality**: Hirosaki's whole enceinte - every bailey plus all three moats - is **~50 ha / 123 acres** at a 47,000-koku daimyo. Himeji, at the grand end, is 233 ha with a 4,200 m circuit (107 ha inside the middle moat).
- **Does the design match**: yes, and the default is deliberately the *modest* anchor. 50 ha at 3 ft/px is ~598,000 px^2, against Tango's entire 701,282 px^2 interior - so a median castle is ~85% of a whole provincial city.
- **What determines it in reality**: the daimyo's rank and the works' generation, NOT the town's population. This is exactly why it is a **declared line with a documented 50-230 ha band** rather than a constant scaled off population - the governing variable is not the one a per-capita model would use.
- **The trap this avoids**: the keep is not the castle. Hirosaki's tenshu is ~0.6 ha, **1.2%** of the works. A model that priced "the keep" would undersize the line by two orders of magnitude.

### Housing: the two new ground-cost constants

- **`C_YASHIKI` ~4,150 px^2.** Anchor: the Fukui archive's **Suginuma plan** (a 1,000-koku retainer, 1839), a 28 x 32.5 ken plot = ~167 x 194 ft = 3,600 px^2, plus ~1.15x for street margin. **What determines it**: RANK and the walled plot's own perimeter - the wall IS the boundary, so it carries far less shared-margin overhead than a detached house in an open lot, which is why the gross-up is 1.15x and not the 7.5x a detached house takes.
- **`C_TERRACE` ~660 px^2.** Bracketed by Shibata's ICP *ashigaru-nagaya* (8 households, 143 x 21 ft, 18 ft frontage = 378 sq ft each) below and the detached samurai house (2,322 sq ft drawn, matching the Matsue mid-rank residence's ~220 m^2) above. **Flagged as the softest number in the feature**: both ends are measured, its position between them is a judgment.
- **Gross-up ratios**, measured from the three shipped cities: **5.6x** drawn footprint for packed rows, **7.5x** for detached samurai houses. The spaced ratio being higher is the model working correctly - a house in a yard wastes more ground per roof than a party wall does.
- **Both constants are provisional by design** and must be re-derived against the first drawn capital, exactly as `C_PACKED`/`C_SPACED` were back-predicted from Tango.

### The samurai rank split - a design CHANGED at this gate

- **Historical reality**: a jokamachi's samurai quarters were rank-graded, with the lowest stratum (*ashigaru*, *kachi*, *doshin*) in terraced *kumi-yashiki* on the town fringe and everyone above in walled plots.
- **The design as first drafted did NOT match, twice over**, and was corrected here rather than implemented:
  1. **Wrong caste.** It called the terraces "ashigaru". `budgets.md` is explicit that **in Rokugan ashigaru are peasants, not samurai** - the original L5R usage, departing from historical Japan - and `l7r.md` puts them in the villages as rural militia at ~10% of farmers. A capital has no ashigaru quarter at all. Renamed to a **retainer terrace** for junior (Rank 1-4) samurai.
  2. **Wrong quantity, in the opposite direction.** Checking the caste error sent the research to `budgets.md`'s rank table, which shows the capital is **70% senior (R5+) / 30% junior** against a provincial city's **27% / 73%**. The mix does not scale, it inverts - a capital posting is prestigious even when the job is menial, and the capital absorbs the rank-by-association cohort. So the terraced texture is the *minority* here, not the dominant one the draft assumed.
- **What determines it in reality**: RANK, and specifically the local rank *distribution* - which is a property of the settlement's administrative weight, not of its size.
- **The split the budget uses**, read straight off the capital column of the rank table so it is traceable rather than invented:

  | band | ranks | share of 800 working | housing type |
  |---|---|---|---|
  | upper | R8-12 (1+8+7+25+119 = 160) | **20%** | walled yashiki (`C_YASHIKI`) |
  | middle | R5-7 (127+134+142 = 403) | **50%** | detached house (`C_SPACED`) |
  | junior | R1-4 (103+72+47+15 = 237) | **30%** | retainer terrace (`C_TERRACE`) |

### `SAMURAI_INWALL_FRAC` for a capital (~0.85, against the provincial 2/3)

- **Historical reality**: the whole point of a castle town is that the daimyo concentrated his retainers into it - "by physically separating retainers from their samurai masters the daimyo was able to subject all soldiers to his direct rule."
- **Does the design match**: yes, and it is why the capital's figure must be HIGHER than a provincial city's. The provincial 2/3 exists because cramped city lots push the wealthiest samurai to country estates; at a capital the walled yashiki removes that push for exactly the senior cohort that would otherwise leave.
- **What determines it in reality**: proximity to the court, i.e. the political value of attendance - not land price.
- **Confidence**: GM-approved, and an estimate. It moves ~40 households of the priciest housing type, so it is a first candidate for re-derivation against the drawn map.

### The civic program

- **Historical reality**: civic ground is a **floor, not per-capita** - a seat carries its full mandatory program regardless of population. The historical civic share of a Chinese county seat is ~10% (range 5-15%). At capital scale the program grows by *institutions added*, not by headcount: the domain ministries, the House Chancellery, the Imperial Magistrate's compound, the Emperor's granaries, the domain school, the sovereign temples, the domain granary and its brokers' row.
- **Does the design match**: yes. Each institution is its own line at its own footprint, so a program change reprices honestly, and the total lands inside the historical band.
- **What determines it in reality**: administrative RANK and the institutions that rank carries. A capital does not get a bigger yamen; it gets a castle, a chancellery, and a foreign magistrate.
- **The ministries sit OUTSIDE the castle** and are therefore priced against city ground rather than castle ground. Both traditions converge on this at exactly this tier: Beijing's Six Ministries lined the Corridor of a Thousand Steps outside Chengtianmen, and a jokamachi's offices spilled out of the ninomaru into the town as they grew (Matsumoto moved its county and town offices to Rokku town outright). **What determines it**: the size of the bureaucracy - at county scale China has no separate offices at all, only the six *fang* as ROOMS in the yamen, which is why our county town draws none.
- **The granary and armory are INSIDE the castle and NOT priced separately** (GM 2026-08-08) - they sit inside the castle's single declared line, and belong to its Mode A sheet.

### The Emperor's granaries (`imperial_granary_seat`)

- **Historical reality**: `budgets.md` funds a separate Imperial granary operation under the Imperial Magistrate, with its own staff and materials.
- **What determines it**: the **threat model**, which is what settled an otherwise arbitrary placement. An invading neighbor would not attack the Emperor's stores, so they face brigands rather than besiegers - a stout wall and a watch suffice, and there is no case for spending castle ground on them.
- **Does the design match**: yes, and because both plausible sitings are real answers (beside the overseeing magistrate; on the water, since grain moves by boat) the seat is a **knob with no privileged default** rather than a fixed rule.

### The aqueduct

- **Historical reality**: the Edo *josui* is two systems with the city GATE between them - ~43 km of OPEN earth cut outside (Tamagawa Josui, "excavated without timbering"), and ~67 km of BURIED stone and wooden pipe inside, feeding 3,600+ draw-wells. Where it crossed a watercourse it went over on an open flume, the *kakehi* at Ochanomizu, which is why the bridge downstream is called Suidobashi.
- **What determines it**: gravity and the city surface. The outside is open because an earth canal is cheap over open country; the inside is buried because a dense wooden city needs its street surface.
- **Consequence for THIS feature**: the buried in-wall conduit **consumes almost no interior ground**, so the aqueduct's budget line is small - its works, not its length. Getting this wrong in the other direction (pricing a surface channel across the interior) would have inflated the wall.
- **A negative finding worth as much as the positives**: there is no East Asian arcaded aqueduct. Arches are the one form the space excludes. Recorded so a later feature does not draw them.

### Circulation

- **Reused, not re-derived**: the provincial 7% of interior at drawn widths (measured 6.8-7.0% on both shipped cities), against a historical envelope of 10-20%.
- **Why reuse**: there is no measured capital figure and there cannot be one until a capital is drawn. Reusing a measured constant is more honest than inventing an unmeasured one, and this is recorded in the spec's Assumptions as something the first drawn capital may revise.

## C. Calibration: what the model produces

Pricing the capital inventory with the above:

| block | ground (px^2) |
|---|---|
| packed row housing (2,160 households) | 1,490,400 |
| samurai: ~53 walled yashiki / ~134 detached / ~78 terraced (265 in-wall of 312) | 603,750 |
| castle (declared line) | 598,000 |
| capital civic program | ~130,650 |
| water (cargo canal + dock basin) | ~5,800 |
| adept-monk houses | ~3,450 |
| **fixed subtotal** | **~2,832,000** |
| required interior after 7% circulation | **~3,045,000** |

Derived wall: **rx ~1,029 / ry ~957 px** - about 1.17 x 1.09 miles across, a ~3.5 mile circuit.

**Two consequences that mattered to the design:**

- **The existing 3,200 x 2,700 canvas still fits it** (it needs ~2,358 x 2,214 including the moat-and-margin clearance), so adopting the tier forces no canvas change - which is why `WALL_MARGIN_PX` needs no capital variant.
- **`plan_city` would refuse it outright.** `POP_MIN, POP_MAX = 2000, 4000` raises rather than clamping. That behavior is correct and is preserved; it is also the concrete reason the capital gets a parallel entry point rather than a widened band.

## D. Decisions

| Decision | Rationale | Alternatives considered |
|---|---|---|
| Parallel `CapitalProgram` + `plan_capital()` | The provincial path executes zero new branches, so byte-identity is structural rather than tested. The tiers differ in inventory structure, so a shared function would be mostly branching. | Tier discriminator on `CityProgram`; subclassing. Both rejected in [plan.md](plan.md). |
| Castle as a DECLARED line, not a constant | Its governing variable is the daimyo's rank, not the population. | A population-scaled castle - rejected as modelling the wrong variable. |
| Rank split read off `budgets.md`'s capital column | Traceable to a published table rather than invented; makes the senior/junior inversion fall out rather than be asserted. | A flat 70/30 with no band structure - rejected as losing the three housing types. |
| Reuse the provincial circulation fraction and budget tolerances | Both are calibrated against real maps; no capital map exists to calibrate against yet. | Inventing capital-specific figures - rejected as less honest than reusing measured ones. |
| `agricultural_district` present-but-always-False on `CapitalProgram` | Lets the shared serializer stay tier-agnostic. Validated False, not merely defaulted. | Branching the serializer on tier - rejected as putting capital-aware code on the provincial path. |
