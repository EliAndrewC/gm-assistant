# Homesteads: the research behind the farmhouse, yard, garden and grove rules

*The research behind the rules in [`../settlements/homesteads.md`](../settlements/homesteads.md). Findings, anchors and disclosed departures live here so the rule file stays operational; this file is where citations and deeper historical context get added as they accumulate.*

**Load this file when:** you are changing a homestead rule, a size or a prevalence - or you want the historical basis before overriding one.

Every entry: what the research found, the decision it drove, and any deliberate departure from literal reality. Anchors are stable - rules link to them by `#slug`.

---

## Homestead groves (yashikirin) - the real scale and prevalence

**Grounds:** `groves_on_windward_side`, `grove_prevalence`, the size-adaptive L-belt

**Evidence:** attested

**Sources:** not recorded - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

## The threshing yard's sun, and how far a farmhouse shades

**Grounds:** the sun-corridor keep-out in the nucleated bundle placer; `yards_unshaded_by_neighbors`

*What prompted it (GM 2026-08-13):* "Would threshing fields be directly to the north of another
house? Or would the shadow from the farmhouse directly to the south block too much light?"

*The house's height, DERIVED rather than assumed.* A thatched (*kayabuki*) roof has to be pitched
**45 degrees or steeper** - that is what the material demands, and it is why a minka carries such a
large dark loft. Our minka is 46 x 28 ft, so with the ridge along the long axis the roof rises about
**14 ft** from eaves to ridge; on a ~7 ft eaves wall that puts the ridge at roughly **20-22 ft**,
which agrees with surviving farmhouses (~6-7 m).

*The shadow, computed for the season that matters.* Threshing and drying are 9th-10th month work.
At 38N (mid-empire on the weather skill's east-coast analog) in the 10th month, a 20 ft ridge casts:

| solar time | sun elevation | shadow |
|---|---|---|
| noon | 43 deg | **21 ft** |
| 10:00 / 14:00 | 35 deg | 28 ft |
| 9:00 / 15:00 | 27 deg | **39 ft** |
| 8:00 / 16:00 | 17 deg | 65 ft |

*The decision:* a yard needs **39 ft of clear ground to its south** - the 9-to-3 window, which is
the drying day that matters. Inside ~21 ft the yard is shaded even at noon. The rule is a keep-out
corridor south of every threshing yard, and a neighbouring FARMHOUSE may not stand in it.

*Why this was missed for so long, which is the useful part.* The engine already reasoned exactly
this way about GROVES - `yards_unshaded_by_groves` keeps a strip south of each yard clear, with the
comment "a neighbour's grove there would shade it" - and simply never applied it to houses, which
are taller than a grove clump and shade further. A rule stated for one obstacle and not for the
obvious other is the same shape as the way-list defects: the check could not see the case, so it
looked like a passing check.

*And the row pitch was already right.* `BUNDLE_PITCH_FT` is 92 ft, while house depth (28) + yard
depth (~26) + 39 ft of sun comes to ~93. The spacing reserved the room; the packer just never
aligned rows, so a neighbour dropped into the gap the pitch had set aside. Measured across the pool
before the fix: a neighbour's wall commonly stood **2-8 ft** south of a yard's edge, and on the
dense nucleated maps that was most yards (Ueda 45 of 85 shaded at noon, Hoshigaoka 31 of 70, Ubame
21 of 36). The provincial cities were clear (0-1 each) because their farm belt is loose.

*The departure we take knowingly:* the corridor is measured on the yard's own cross-slope span, as a
rectangle, not as a true solar wedge that swings through the day; and real *yashiki* lots also
resolved this by STAGGERING east-west rather than by spacing rows, which the placer is free to do
since the corridor only forbids the shadow, not the neighbour.

*Sources:* the 45-degree thatch pitch from the *kayabuki* literature (a steep pitch is required of
thatch, hence the large loft); solar elevations computed for 38N at the 10th-month declination;
minka ridge heights cross-checked against surviving farmhouses.

- *Historical scale - the real numbers (research grounding, for calibrating the glyph).* A homestead grove is a substantial STAND, not a few trees. The best hard data is a 1987 survey of Kashima in the Tonami plain (the classic *kainyo* dispersed-farmstead country, 46 households): **~33 trees of trunk diameter >= 10 cm per homestead**, of which cedar (*sugi*) was ~48% (**~16 cedars per house**), the rest spread over ~83 other species; **~6 species per homestead** (range 1-14); a large/notable homestead ran **200+ trees across 31 species**. That count is trunks >= 10 cm ONLY - it EXCLUDES the bamboo stand (hundreds of culms), saplings, and the trimmed hedge layer - so the honest figure for a typical grove is **~30-40 mature trees + a bamboo grove + understory**, and a big one **100-200+**. The grove canopy footprint is therefore the LARGEST homestead appurtenance - **bigger than the farmhouse**, and far bigger than the garden or threshing yard - wrapping the N/W as a belt several trees deep. The map need not draw every tree (houses/yards are already oversized symbols), but per Principle "relative sizes roughly honest" the grove glyph must read at the RIGHT relative scale: clearly the dominant homestead feature, a dense stand suggesting dozens of trees - not a garden-sized clump of 5-10. *(Cross-check on the windward rule: Okinawa's homestead groves sit on the E/N sides, because the islands' damaging wind is the typhoon/NE monsoon, not the mainland NW - same logic, different geography, which is exactly why `windward` is a per-map knob.)*

## May a byre stand beside a wellhead? (researched 2026-08-18)

**Answer: yes, and the vernacular puts them far closer than our maps do. No GM ruling wanted.**

A `settlement-review` flagged a shared draft-animal byre standing 38 ft from a communal wellhead on
Kashikawa and asked for a ruling. Under the constitution's Principle XII rule that research precedes
a ruling, this was searched first, and the record is not ambiguous.

**Japan (the closest analogue, and the strongest signal).** In the *magariya* L-plan farmhouse the
draft animal lives **under the house's own roof**: the stable wing (*umaya*) meets the dwelling
(*omoya*) at right angles and extends off its SOUTH face, deliberately taking the best sunlight,
"indicating how valuable horses were". And the well (*ido*), where a house had one, sat "in the rear
corner of the earthen-floored *doma* or in a rear projection room" - i.e. **inside the same
building**. A household's horse and a household's well were therefore separated by the width of a
farmhouse, on the order of 20-40 ft, as a matter of course. This is also why our own doctrine draws
no European multi-stall barn (see the draft-animals-live-in-the-house rule in
[`../settlements/homesteads.md`](../settlements/homesteads.md)).

**China (the guiding star).** Vernacular villages **co-located the animal facilities with the
latrine** - cattle sheds, chicken houses and pigsties grouped with the privy - because both ends of
that group feed the same manure economy that kept the soil fertile for four thousand years
("treasure nightsoil as if it were gold"). That is a positive siting rule about the muck cluster,
and it is worth knowing; what it is NOT is a rule holding livestock away from drinking water. No
separation doctrine turned up in the geomantic or vernacular-layout material.

**Elsewhere, corroborating.** The public watering trough at a village or town water point - "a
trough, preferably with a well and a pump" - is a widespread and well-documented arrangement. Where
communities invested in water infrastructure at all, watering the beasts AT it was the norm rather
than a transgression.

**What is genuinely true and worth not over-reading:** livestock near a shallow, unsealed well IS a
real contamination vector, and modern rural-water studies in China measure exactly that. But that is
a public-health finding about the *consequences*, not evidence that the builders sited to avoid it.
A generator that separated byre from well would be drawing a modern sanitary intuition, not a
Rokugani village.

**The decision, therefore:** the beasts are watered at the well, and a byre near one is correct.
Nothing is changed in the placer; `_fits` already prevents an actual overlap with the wellhead's
footprint, which is the only part that was ever a defect. Recorded so the next re-pack does not
re-open it.

## Is every farmhouse reached by a lane, and in what FORM? (researched 2026-08-18)

**Answer: access is decisive (implement it); its FORM has two supportable shapes (make it a knob).**
This one is worth reading as the worked example of the constitution's research-then-knob ladder,
because the research came back decisive on one axis and genuinely two-formed on the other.

**Decisive: a house in a nucleated cluster IS reached by a way.** The Chinese material is explicit -
"the organisation of the village plan as a gridiron of narrow lanes is functionally the most
efficient form of compact settlement", and "every house in the nucleated village is accessible via
the interconnected system of narrow lanes and alleys". This is not a planner's ideal imposed after
the fact; it is what compactness is FOR. The lanes are also socially live rather than purely
circulatory - the narrow lateral ones are "colonised as semi-private space by the adjoining house",
which is why they are narrow, irregular, and sometimes barely more than the gap between two walls.
Our own doctrine already said as much in one line ("a nucleated village is threaded with lanes") but
the generator was not honoring it: a back-rank house could sit with no way touching it at all.
That is now a defect with a research basis, not a matter of taste.

**Two supportable forms for delivering that access.** Both are attested, and neither dominates:

1. **Alleys off the spine.** Narrow lateral lanes branch from the through-lane between house plots
   and run back to serve the rank behind. This is the Chinese gridiron-of-lanes form, and the one
   whose laterals get colonised as semi-private space by the houses they pass.
2. **A back lane.** A way parallel to the main street, behind the plots, serving their rear. This is
   documented as a planned-village device - "back lanes on each side of the main street which,
   together with the main street itself, provides a rectangular framework" - and it typically
   "divided the village from the main agricultural area", i.e. it doubles as the field-ward edge.
   Rear-access ground behind the housing lots is separately documented in traditional Manchu
   villages in northeast China, so this is not a purely European shape.

Note what distinguishes them: a back lane implies PLANNING (someone laid the framework out at once,
and the plots are regular), while alleys off a spine imply ACCRETION (each household cut its own way
to the road, and the result is irregular). A Rokugani hamlet can plausibly be either, so this is
exactly the axis the project wants varied between maps rather than settled once.

**Therefore:** the generator must guarantee every farmhouse is served by a way, and must choose
between the two forms per settlement via a seeded knob. Per Principle XII this is NOT a question to
put to the GM - the research decided the part that was decidable and identified the part that is
genuinely two-formed, and the two-formed part becomes variance.

**Sources:** the lane-gridiron and semi-private-lateral findings are from the nucleated-village
morphology literature; the back-lane framework from planned-village morphology (see
[`SOURCES.md`](SOURCES.md)); rear-access in Manchu villages from Ushijima, "Spatial composition and
premise arrangement of traditional Manchu village in Northeast China", *Japan Architectural Review*
(2020).
