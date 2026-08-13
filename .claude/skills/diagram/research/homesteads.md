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
