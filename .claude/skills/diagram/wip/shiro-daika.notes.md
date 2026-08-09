# Shiro Daika - notes

Mode B **domain capital** (the first at this tier), 1 px = 3 ft, walled, `wall_defense="siege"`,
river city, Scorpion (the Daika vassal house of the Bayushi), population **12,360**. Features
`specs/018-capital-space-budget` (the budget), `specs/019-capital-skeleton-castle` (skeleton +
castle), `specs/020-capital-ground-layer` (this layer). **A `wip/` DRAFT until feature 021's
housing lands** - it fails exactly one check (`imperial_road_town_has_farrier`), correctly: no
relay stables until there is fabric. Do not fix that by drawing the farrier; the cascade
(forge -> stables -> wells) was tried and is the engine refusing a half-populated city.

## What this map is the worked example of

- **Budget-first sizing at the capital tier**: the wall is an output of `plan_capital`
  (`CapitalProgram(population=12_360, river=True, castle_seat="ring",
  imperial_granary_seat="wharf")`), never a guess - a median castle alone is ~85% of a
  provincial city's interior, so population predicts the ring badly.
- **The blank castle** (019): enceinte, moat, gates, ishigaki doubling - and an empty court, by
  doctrine (nothing shown beats the wrong thing shown; the bailey-wall experiment ran and
  answered no).
- **The government ward** (020): six ministries in two files flanking the ote-suji, House
  Chancellery + Domain School continuing the axis south of the kagi-no-te bend - the Beijing
  Corridor-of-a-Thousand-Steps / jokamachi convergence.
- **The lineage compounds** (020): eight named walled yashiki in three drawn size bands (the
  fourth band is the castle - ruling daika gets NO compound), sizes tracking households HOUSED,
  never the head's rank: kurogi is a full chancellor on a visibly smaller plot because his
  people live out in Moriguchi.
- **Two-places-for-grain** (020): siege stock implied inside the castle; the working domain
  granary at the wharf; the Emperor's granaries separate again (they face brigands, not
  besiegers), exercising `imperial_granary_seat="wharf"`.
- **The towpath and the aqueduct** (020): the first uses of both glyphs - a river gets a
  towpath, not a road; the aqueduct is open outside the wall only, no arcade, gate terminus.

## Load-bearing decisions

- **The kagi-no-te.** The first cut ran the Imperial road straight through the castle (and
  nothing could see it - the 019 review's headline find). The road now bends west past the
  castle's front at y=1560, and 020 moved that bend south from 1420 so the ote-suji stub carries
  three ministry compounds a side with the 14px office standoffs.
- **One shared crossing source.** `bridges()` and `roads_bridge_water` both read
  `settlement.bridge_carried_ways` / `bridge_crossed_waters` - the fix for the two hand-kept
  lists that agreed and were both wrong (four of six crossings unbridged with a green gate).
  The aqueduct is in the same source, so a future way over it demands a deck automatically.
- **The east crop margin (`east=700`).** The default content crop cut the aqueduct's intake and
  the east road's river bridge clean off the sheet; User Story 3 is a reader tracing the water,
  so the frame pays for the intake.
- **Sovereign-temple precincts are RESERVED, not drawn.** Each head house shows its hall only,
  but ~390x300 ft of precinct ground is held in both placement registries now, because this is
  the ground-reserving layer and 021's packs would otherwise legally seat commoner rows 66 ft
  from a grand abbot's wall. Feature 021 draws the complex (residence, administration, library,
  monk housing) inside that reservation.
- **Benten's torii pinned to 7.** The per-temple roll gave the PRIMARY sovereign temple a
  3-arch stub while co-sovereign Jurojin rolled the full avenue - the declared hierarchy read
  inverted, so the primary is pinned (`torii_count=7`, Nagahara's donation-row stride).

## Review log

- **2026-08-09, settlement-review (feature 019, FULL)**: the Imperial road ran THROUGH the
  castle - fixed with the kagi-no-te; bailey walls judged and removed; two findings deferred to
  020 (blind bridging, mis-zoned civic quarter), both since cleared.
- **2026-08-09, settlement-review (feature 020, DELTA)**: verdict needs-work; all structural
  form confirmed (government ward, lineage bands, wharf chain, towpath, aqueduct). Acted on:
  "Shiro Daika Castle" caption failed the kanji triangle (shiro = castle) -> "Shiro Daika"
  plain; "Imperial Magistrate" renamed to the institution ("Imperial Magistrate's Compound");
  sovereign-temple precinct ground reserved; "aqueduct" intake note added; Benten pinned to 7
  arches; this notes file created. Deferred to 021, per the review: keep the strip behind the
  teramachi rim lean, declare a wind bearing before nuisance trades land, close the
  `graveyard: true` claims when precincts are drawn, and one deliberate caption-loudness pass.
- **2026-08-09, GM pass (nine questions)**: the House Chancellery compound REMOVED - the
  council meets in the castle (researched: Hyojosho/Roju in Edo castle, Grand Secretariat in
  the palace; check inverted to `capital_chancellery_meets_in_the_castle`). The moat's water
  drawn: sluiced river FEEDER at the southeast approach, DRAIN off the southwest arc to the
  fields (the castle's inner moat stays standing groundwater, scum and carp included - that is
  period-accurate and recorded). The aqueduct terminus gained its TERMINAL BASIN so the supply
  no longer reads as a brook feeding the moat. The Domain School redrawn as `s.hanko` (letters
  + bugeijo, not a ministry box). The dock basin removed (in-city canal vocabulary, wrong on a
  diagonal riverbank); granary rows turned BANK-PARALLEL onto the wharf via granary(rot=...),
  captions pluralized ("domain granaries" / "Imperial granaries" - staging/working stores; the
  siege reserve stays in the castle, implied). Tokiwa re-seated off the patrol road, and the
  ring_road_kept_clear check factored to run at capital scale WITH manors in its victim list -
  the two stacked gaps the GM's quibble exposed. Teramachi rim explained (defensive perimeter
  temples are the castle-town pattern; the two sovereign temples ARE the "two main"), offered
  as a re-seat if the GM prefers a gathered quarter. Follow-up: the Imperial granaries gained
  their OWN jetty - the Emperor's grain moves by boat (that is what the "wharf" seat means), so
  it does not borrow the domain quay 200 ft downstream.
