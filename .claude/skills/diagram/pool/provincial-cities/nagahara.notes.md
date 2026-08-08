# Design notes: Nagahara, the RIVER city on the Hayakawa

*Reconstructed 2026-08-08 from the generator's docstring and comments, which until then were the
only record of this map's intent. Everything below is sourced from `nagahara.gen.py`.*

**Subject**: a walled provincial city of ~3,000 depicted, drawn at 1 px = 3 ft, standing on the WEST
BANK of the Hayakawa. Crab clan, `wall_defense="siege"`, no Imperial road. Hayakawa county (the
separate Mode A sheet [`pool/magistracies/hayakawa-magistracy`](../magistracies/hayakawa-magistracy.svg))
is named for the same river and feeds its taxes here.

**Why it exists**: Nagahara is **the norm, and Tango is the exception**. This is the pool's model of
the ordinary river city, against which Tango's unusual choices are meant to read as unusual.

## The river doctrine, which is this map's organizing fact

The trunk river **never runs through the walls**. The historical pattern is imperial China first with
Japan agreeing - Xiangyang's Han-river face, Pingyao on the Fen, Okayama on the Asahi - and the
counter-example is decisive: Kaifeng, the one great city that let a river in, was devastated seven
times. So:

- the city stands ON the bank; the river IS the water defense on its east flank;
- the **dug moat covers the three landward faces**, tapping the river upstream (NE) and returning
  downstream (SE) so the current flushes it;
- the junction feet **tilt with the current** - inlet near-square, outlet swept downstream.

**The one way water enters the walls** is a CARGO CANAL through a WATER GATE - the Suzhou Pan Gate
*shuimen* pattern, a grated arch with a sluice - feeding an in-city DOCK BASIN in the merchant
district. Outside the river gate lies the WHARF suburb, the riverfront *guan-xiang*: jetties,
warehouses, the gate market.

**THE DEAD CROSS THE RIVER.** The funerary complex sits on the far bank. Two reasons, and the second
is the one worth keeping: the moat's water set-back leaves no dry ground on the landward fringes, and
carrying the dead over water suits the geography of the afterlife anyway.

## GM decisions (settled - not open for re-litigation)

| Decision | Value | What it drove |
|---|---|---|
| Walls | closed ring, siege-grade | densely towered - the visible contrast with Minami's peaceful rampart |
| Imperial road | **none** - the highway passes ~10 miles north | a NORTH ROAD leaves the north gate slanting north-west to meet it off-map; the EAST ROAD crosses the Hayakawa on a timber bridge at the river gate |
| Gates | north + east river gate, plus a water gate south of it | the water gate is the canal's only mouth |
| Clan | Crab | temples to Bishamon + Ebisu; estates orient toward Otosan Uchi (NE) |
| Land fall | `water_flow=90` - south | downstream is south, which is what puts the burakumin quarter where it is |
| Wall size | **budget-first** (feature 009) | the space budget is computed BEFORE anything is placed and the rampart is sized from it: 452x421 |

## Quarters

| Quarter | Contents |
|---|---|
| W | the samurai/government ward - yamen + five ministries behind a kido-gated fence |
| NW | the temple neighborhood: **Suitengu** (the river fortune - the point of siting it here) and Ebisu, with the Ministry of Rites |
| NE | laborer terraces |
| E-central | the merchant district around the dock basin |
| SE | the burakumin neighborhood, **DOWNSTREAM** - polluting trades below the city, historically exact |
| S-central | laborer/servant rows |
| across the river (SE) | the samurai country estates, commuting over the bridge, per the estate doctrine |

## Deliberate choices

- **Kido reservations ask the ENGINE for the ground each ward gate will take**, rather than a
  symmetric square guessed to be big enough at any angle: the glyph's angle follows the LANE it bars
  and its guard box slides clear of the roadbed, so only the engine knows its real extent.
- **The ring inset matches the ACTUAL ring road (22, post-shrink)**, not the stale default of 34 -
  the gate guard houses and inspection stations pull in to the patrol road's centerline, which also
  keeps each inspection inside the gate radius.
- **The civic aprons are swapped in two phases.** A 30 px apron around each ministry and the yamen
  during the budget-first ring (a rotated `samurai_large`'s bbox reaches ~16.7 px past its center, so
  the 14 px office standoff needs 30.7-), then swapped in place to 16 before the top-up fills, which
  place axis-aligned and enforce their own 15 px AABB gap. **Replaced index for index**, never
  del+append: `_poly_bboxes` invalidates on list LENGTH change only, so a same-count rebuild would
  leave every later bbox misaligned.

## Review log

- **2026-08-08 RNG re-roll** (positional/scoped randomness, engine-wide). A `-109 deg` servant range
  seated 13.96 px from the Ministry of Works - clear on `servant_ranges`' rotated-rect probe, abutting
  on `city_government_offices_dont_abut`'s axis-aligned measure. Fixed in the ENGINE, not here: the
  probe now measures the box the check measures. Nothing in this gen changed for it.
- **2026-08-08 caption pass.** The Governor's Mansion caption moved inside the walled court (11 pt),
  which freed the band above the wall; the re-pack filled it with a full row of housing 64 ft off the
  wall, which is the point of the change.

## Known open

- **No `notes.md` existed for this map until 2026-08-08**, so anything settled between its authoring
  and that date lives only in gen comments and may not be recorded here. Treat gaps as unrecorded
  rather than as decided.
- The 2026-08-08 settlement-review of Minami/Nagahara flagged two things here worth a look when the
  map is next opened: **"Temple of Ebisu" sits 212 ft from its own hall**, across a street in the next
  block, where every other hall caption on the two city sheets sits 37-58 ft off its hall; and the
  **two visible samurai estates stand as empty boxes in a featureless plain** with the "samurai
  estates" caption 460 ft below the nearest of them. Both predate the RNG work and neither is fixed.
