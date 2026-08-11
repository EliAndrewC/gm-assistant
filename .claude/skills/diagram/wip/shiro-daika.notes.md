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
  it does not borrow the domain quay 200 ft downstream. The ote-suji was re-cut from 96 ft (a
  raw-pixel unit slip) to the researched 45 ft - Edo's own Honcho-dori class - with the
  ministry files pulled in to corridor setback; research/cities/capitals.md, "Street widths".
  A full dimensional audit followed (research/cities/capitals.md, "Dimensional audit"): every
  drawn family checked against its anchor at 3 ft/px; all hold except the hanko, enlarged from
  0.33 ha (the bottom of the attested band) to ~1 ha - mid-band between Choshu's first
  Meirinkan and Aizu's Nisshinkan, per the schooling-magnet doctrine. The moat plumbing was
  then corrected on the GM's eye: the feeder had tapped the river at its CLOSEST (southeast,
  downhill) approach with a 48 ft thread - the northern ring would have been a dead arm; it now
  taps the HIGH upstream reach at Tango's own moat-width 66 ft. A second GM pass settled the
  FINAL form: river-to-river like the sibling cities - the feeder runs monotonically down-map
  (every segment west and south, the declared bearing) into the EAST arc, and the drain leaves
  the southeast arc and rejoins the river below its bend, swept downstream, with the towpath
  crossing its mouth on a plank deck. The aqueduct now visibly REACHES the city: its last leg
  crosses the moat on a kakehi flume-deck (the Suidobashi form) and the terminal basin stands
  at the rampart's foot beside the north gate. And the angled-label rule gained the GM's
  full-tilt extension (linear_tilt_full, opt-in): the granary captions lie ALONG their -54 deg
  rows, past the 45-degree go-level clamp road captions keep. A further GM battery rebuilt the
  AQUEDUCT to the researched josui form (research: "How a josui actually ran") - shallow
  downstream peel off the river, short direct fall to the EAST gate, Okido-style terminal
  basin, no kakehi (nothing to cross), 021's draw-basins specified as josui-ido cistern-wells -
  and gave the castle its KARAMETE-MON (research: "A castle has TWO gates"): rear north gate,
  smaller tower, own moat deck, approach road T-ing onto the Imperial road, whose north-gate
  passage was also straightened onto perpendicular stubs (the bed rode the rampart stroke) and
  now carries a second "Imperial Road" caption on the Shiro Kyo branch. Yodo and Nio re-seated
  clear of the new ways. Two follow-ups the GM's eye caught: the karamete approach straightened
  into the CONTINUATION of the north gate's street (the first cut hung it off the diagonal and
  the beds read as overlapping roads - now city gate -> due south -> rear gate, with the
  through-road leaving at the junction), and the aqueduct's bank lines darkened/widened as a
  GLYPH CONVENTION (masonry brown, ~2 px reveal per side - the wellhead-vr precedent; true-scale
  berms would vanish at 3 ft/px). A further pass: the moat-form question researched and
  settled (research: "The moat RING and the river-flank moat are both real") - the complete
  ring + sluiced leats is the Chinese standard (Xi'an's 14.6 km full circuit) and correct for
  a rampart standing off its bank; Minami/Nagahara's river-flank arcs stay correct for walls
  ON the bank. And the GM's half-bridge catch became a general rule: bridges_span_their_water
  demands both deck ends past the crossed water's edge (the oblique-crossing span rule), with
  the towpath plank re-sized to comply. Then the temple pass: Jurojin's sando turned to
  face the kagi-no-te road and the general rule added (temple_torii_face_the_street, all
  tiers, with its two pool-taught refinements: a hall may face its own monzen lane, and a
  doorstep entrance arch is not an avenue); the GM's patron-temple reading ADOPTED as doctrine
  (research: "Temple approaches face their street, and the modest temples have PATRONS") -
  Hotei beside Tokiwa is Tokiwa's bodaiji, and the sovereign temples each grow their own
  monzen neighborhood in 021. The ote-suji's 45 ft over the Imperial road's 26 ft re-confirmed
  deliberate (the Honcho-dori research; the Imperial road matches every other map). And the
  internal-walls question settled (research: "Which districts get INTERNAL walls"): NOTHING is
  district-walled at this tier by default - yashiki walls seal the samurai streets, monzen
  neighborhoods stay open, precincts alone are walled - with ward_style="fang" (the Tang
  lifang) recorded as the Lion-variant knob. Documentation only; 021 draws the kido mesh. The two moat
  sluices now carry "sluice gate" labels (GM: the bare glyph read as a floating black bar -
  most of a real gate is in the water, so the word explains what the drawing cannot;
  sluice_gate(label=...) added engine-wide). Final GM battery of the day: estate captions moved INSIDE
  their blank courts (manor(label_inside=True) + capital_estate_labels_inside; the magistrate
  shortened to "Imperial Magistracy" to fit), the sluice glyph gained its lifting frame
  (crossbeam + windlass, the operator's above-water structure, at the glyph floor) and both
  boards slid off the junctions onto their channel runs, the granary rows moved to the QUAY
  (Kuramae unloads straight into the kura - raised floors are the flood answer, not distance),
  and the jetties shortened from causeway to landing-stage length (~39 ft, a third of the
  channel, per the fairway law). research/cities/capitals.md, "The sluice's lifting frame, the
  quay-side kura, and the boat-length jetty". Follow-ups on the GM's next look: the sluice frames now SPAN their
  channels bank-to-bank (sluice_gate span=; the fixed field-channel frame floated mid-water on
  a 66 ft leat and read as detached - research: the operator walks the crossbeam and winds the
  windlass, neither of ours denotes open/closed); the estate captions split over two lines for
  a bigger face; the HANKO's court went BLANK per the sync doctrine (a real hanko is
  building-dense - Nisshinkan's halls, dorms, pond, observatory - so a faithful interior is a
  dozen buildings and belongs to its Mode A sheet; the two-hall sketch was neither honest nor
  blank), its caption moving inside; and the aqueduct's two ends carry their words - "intake
  weir" at the river (the Hamura form) and "settling basin" at the gate. The GM's internal-dock
  question was then researched and answered with NO map change (research: "The internal dock
  and the bank quay"): the water-gate/dock-basin form the sibling cities draw belongs to still
  at-grade water, a live towpath river takes the kashi bank quay this map draws, and the
  grain-only look of the landing is the ground layer's emptiness - 021's brokers' row and
  warehouse frontage land on the bank top per the wharf-chain doctrine. Next battery: bridge
  decks now LAND - the GM's corner-at-the-water's-edge catch became engine and check law
  (research in settlements/ways.md: the abutment sill stands BACK from the channel edge so
  scour cannot undercut the bearing, so a carried deck runs LANDING_FT = 10 real ft of deck
  onto dry ground per side; bridges() solves the oblique span exactly, where the old flat
  +28px slack had left the east river deck landing 0.0 ft at its worst corner; the check
  measures the deck's FOUR REAL CORNERS with a 6 ft floor, footplanks floored at 2 ft with
  their deliberately short abutment kept per GM 2026-07-22; the pre-fix manifest is frozen as
  the flush-corner regression fixture). The towpath plank gained a visible ~2px bank rest.
  The three aqueduct words now share the duct's bearing and ~20px offset ("intake weir" and
  "settling basin" had been level while "aqueduct" lay along the cut), both sluice labels sit
  beside their glyphs (the drain's had drifted 71px out while the feeder's sat adjacent), and
  the drain sluice was reseated ON its leg's centerline - it sat 11px west of the channel.
  The GM's open/closed question: NEITHER glyph denotes state - both draw the same
  closed-board form, so there is no state difference for a label to explain. The engine-wide
  deck re-size was independently reviewed (settlement-review DELTA, 2026-08-09): kikuta
  confirmed a proven no-op (footplank-only sheet), Minami's three resized carried decks all
  pass - every span re-derives to the decimal and the oblique canal deck's corners clear
  their banks in pixels; one out-of-scope nitpick recorded (two plank-styled glyphs on
  Minami's east bank near (843,1312)/(843,1420) that can read as bridges over nothing -
  pre-existing, not deck records). Pre-021 sweep (GM asked what else must land first): the
  side-gate stub roads were the one defect - both the EAST and SOUTHWEST trunk roads STARTED
  at the gate point on the wall, so each gate opened onto 90 ft of bare ground 30px short of
  the ring road; both now run their first leg inside the gate to join the ring, and the rule
  is law at city+capital scale (gate_roads_join_the_ring, with the pre-fix manifest frozen as
  a regression fixture - no check had watched gate-to-ring connectivity, so it shipped green).
  The sluice DUTY CYCLE is researched and recorded (research: "How often is a sluice OPEN?"):
  the moat pair rests THROTTLED - a trickle in at the east, out at the southwest, trimmed not
  toggled - and a board moves for EVENTS (spate: intake hard down; drought: outfall shut;
  dredging: intake shut + outfall full open; siege: both shut), while field sluices are the
  scheduled kind (growing-season rotation of water rights). One closed-board glyph therefore
  stays the honest drawing; no open-variant needed. Nothing else blocks feature 021.

## Feature 021: THE SETTLED WALL - endgame grind (state 2026-08-10, late)

**Geometry (FINAL, GM-approved option A):** RX,RY = 1110,1150 at CX,CY = (1400,1313) - the
castle axis; straight Imperial road through both gates. Gates: N (1400,163), E (2510,1313),
S (1400,2463), SW (502,1989). Canvas (3200,3050). River (shifted course) stays. The THREE
STRUCTURAL LAWS ARE GREEN and must stay green: capital_interior_slack_in_band (<=15%
claimed-open, wall-settles-first), capital_wall_matches_budget (C_PACKED_CAPITAL 950,
CIRC 0.15, suburb 60/2160 - the GM's wharf-hamlet-only extramural ruling, all recorded in
research/cities/capitals.md + citybudget.py), and the packed split (in-wall 2100 / suburb 60).

**Where the grind stands:** ~24 singles. Bands: packed_inwall PASSES at 2100-scale when the
freed ring zones are packed (E machi extended to (1940,550,2405,1310) etc). detached stuck
~103/133: the moat-south band pack (640,1272,1140,1382) leaves most of its box UNVISITED
(why_placed says unvisited, not refused - investigate rowpack's early rows against the
castle-moat margin; workaround: widen east-street detached (2145,1255,2420,1415) and the
west pocket instead). suburb 55/60. census 2381/2472 - close LAST via one pack.

**Beware (hard-won today):** the W band is layered - the ORIGINAL west-rim machi
(430-590 x 750-1445, packs at lines ~779) is the real fabric; my crescent-machi south
(445-625 x 1450-2075) is kept; every other W addition was deleted. Wall W face curves hard:
x=500 at y640, 290 at y1300, 557 at y2060 - anything west of the face line clips. The SE
kido pair (2120,1770)/(2182,1725) needs its reserves BEFORE every machi pack (order bug,
fixed by putting them in the east-street district declaration block). Quay rows: river at
x~2295-2340 at y2270-2300 - packs east of that drown.

**Remaining after green:** exact census (2472, tol 0), lint+full test files, bare-ground
render check, re-run FULL settlement-review (the old review's findings partially stale now),
N-market/flop caption cuts + review errors (kosatsuba/punishment/execution + capital-tier
check gap, bell-drum tower, precinct walls, cistern kind/glyph, mirror precincts), perf
T024, captions T025, T026 pool move + full sweep, T028 XII, T029 record-the-why docs
(the THREE wall derivations + the slack law + extramural ruling), T030 ritual. Keep
appending pain points to future-work.md per the GM's standing instruction.

## FIRST PASS SHIPPED GREEN (2026-08-10, session diagram-city)

Gate: **0 FAIL** with three DOCUMENTED waivers, all one phenomenon - the first-pass fabric
under-fills the settled wall (~8% packed shortfall, ~130 census households, rotating ~1.5 ac
pockets) - which the GM deferred on 2026-08-10 to the fabric-first feature (future-work.md #2/#5).
Pre-waiver failing state frozen as
`pool/regressions/capital_fullness_deferral_fires_on_the_first_pass_shiro_daika.json` (fires all 3).

Everything else was fixed FOR REAL. The lessons that cost the most, so the next capital does not
re-pay them:

- **Street ends must be EXACT ring/junction intersections.** Snapping computed 1-decimal
  intersection points (segment vs polyline) killed the whole stub/near-miss/meet-through family in
  one pass; dist-N offsets flicker because street half-widths are feet-derived and tiny. When the
  band street's east end was later re-snapped, its SLOPE changed and every vertical street's end
  had to be re-derived - re-snap dependents in the same pass.
- **Well grids and packs form a circular dependency; the winning order:** hand alleys -> well
  grids split into inter-alley boxes (a band-wide box lands wells ON the hand alleys) -> packs
  (rows ring the pre-placed wells) -> engine-sited top-ups via `open_seat(w=8, h=8, well=True)`
  for the residual density pockets. A hand well at a coordinate a pack has already filled lands
  "on a building" forever (deterministic jitter - respacing barely moves it).
- **Well-court keep-outs EAT pack seats.** Three overlapping density-chasing boxes (spacing
  36/40/44) had silently halved the east machi's density (0.67/kpx2 vs 1.1+ elsewhere) - that WAS
  the packed_inwall deficit. Measure per-district density (dwellings per kpx2 across `districts`)
  before blaming the packer; the table names the sick district instantly.
- **The x1990 "band lane" ran through Hazama and Utsuro estates** (lineage_manor seat-scans made
  it look fine until a reflow) - deleted; the E machi got proper roji instead (pre-wells so the
  grid dodges them; ends snapped to the ring).
- **Gate-ward dwelling packs from the pre-ruling design were still in the gen but seating ZERO** -
  deleted as dead code; the drawn map already honored the wharf-only ruling (all extramural
  dwellings in the kashi/towpath belt, suburb band green at 60).
- **Claims are the tool for ground that is genuinely open by design** (drill grounds, moat
  firebreak, rampart approach, the S-gate column ground where the Imperial road crosses the band
  street) - `commons(..., render="bare")` claims it blank and the commons-frontage exemption
  clears the lined/bare-street checks. But a claim on PACK ground costs seats, and the empty-pocket
  population ROTATES on every reflow - claim the stable cores, waive the rotating residue.

Remaining before pool/ graduation (T026+): fold the queued review items (kosatsuba etc., above),
caption-loudness pass, perf A/B + GEN_TIME_BUDGETS entry, full sweep via make done, XII bookend,
then the move.

## THE GM's RENDER REVIEW (2026-08-10) - eleven defects, twelve new checks

The GM read the shipped first pass and listed everything wrong with it. Every item got a CHECK
first (red against the shipped map), then the fix - the standing order for this round. The
checks, and the lesson each one encodes:

**Water furniture had been left behind by a re-route.** The river's course moved during the wall
re-derivation and four features kept their old seats: the towpath ran 113-215px inland, a sluice
gate stood 245px from any water, the aqueduct's settling basin ended IN the moat, and one of two
tanning yards was beached 189px from its wash water. `towpath_hugs_the_bank`,
`sluice_gates_on_water`, `aqueduct_taps_water_lands_dry` and `tanning_yards_on_water` measure to
the CURRENT watercourse geometry, so a re-route now drags its furniture red instead of leaving it
stranded. **The general rule: a feature defined by a relationship to moving geometry must be
DERIVED from that geometry, never pinned to a coordinate that was correct once.**

**Street topology.** A service lane ran the full length of the Imperial road's kagi leg -
two ways drawn where the ground has one (`ways_not_inside_road_beds`); several street and alley
ends stopped a visible gap short of a street they pointed straight at, past the 30px near-miss
cap but plainly meant to join (`city_streets_reach_their_neighbors`, which also reads ALLEY ends);
and a street started 6px inside the castle moat's channel because the whole moat battery read
only the CITY moat, never the castle record (`ways_clear_of_castle_moat`).

**Wells: the accretion trap, and the fix that generalizes.** 27 hand-tuned `place_wells` boxes had
grown one at a time, each added to fix a local household count with no reference to the wells
already there - nine wellheads inside one 150 ft radius where every other pool map maxes at FOUR
(`wells_not_clustered` measures exactly that, scale-normalized). The cure was structural, not
positional: `_well_blocks()` takes a quarter's bbox, cuts out the bands its own streets and alleys
occupy, and grids each surviving BLOCK, siting each wellhead with `open_seat` (which consults
`_fits`) and refusing any seat with 3+ wells already inside the radius; a coverage gap-fill then
walks the machi ground and seats a well wherever the nearest is >78px off. **Three lessons worth
carrying: (1) derive the grid from the ways instead of hand-placing boxes, and a street reflow
moves the wells with it; (2) the gen reads the way list AT THE MOMENT IT RUNS, so every hand alley
and street had to be hoisted above the well block - a way declared later cannot be dodged; (3)
well courts are keep-outs, so wells and packed houses trade ground - the packed band swung 1,893
to 2,377 as the well count moved, and both have to be tuned together.**

**Everything outside the wall belongs to something.** The kiln works stood 600px out in open
field and the N gate market's nearest stall was 225px down the road.
`extramural_features_tethered` requires an outside feature to be within 900 ft of a gate, on a
road it hauls on, or at the wharf; `gate_markets_start_at_their_gate` puts the market's head at
the gate mouth (with a moat allowance - stalls cannot stand on the crossing).

**No dung at a samurai's front door.** A caravan yard sat 24px off the Nio Estate's gate.
`animal_yards_clear_of_compound_gates` measures to the GATE POINT (`gate_dir` names the side), so
a yard behind the back wall is ordinary city ground while the approach is protected.

**The frame carried dead margin** on the south and east because `crop_city(south=240, east=700)`
overrides outlived the layout they were added for. `map_frame_hugs_its_content` demands real drawn
content within 400 ft of every edge. **A per-side crop override is a liability the moment the map
is re-laid.**

**THE BIG ONE: the capital-tier check gap.** The GM asked "I don't see a cremation ground or
pauper's burial mound at all" and "I also don't see a mausoleum" - and the reason was systemic.
Every urban rule tested `scale == "city"` EXACTLY, and the capital tier, added later, inherited
nothing: **74 non-farm checks ran on a provincial city and were silently skipped on the capital**,
the entire funerary block among them. `URBAN = scale in ("city", "capital")` now covers both, with
the handful of genuinely city-specific rules (the wall-capacity model, which does not know a
castle eats 40% of the interior) left city-only and commented. A check that never runs looks
exactly like a check that passes - this is the third instance in this skill's history, and the
first to be found by the GM's eye rather than by a diagnostic.

**Interior ward gates are a KNOB, not a law** (GM): `meta(ward_gates=False)` turns the kido mesh
doctrine off for a map that does not use them, and Shiro Daika ships without them until the
placement rule is reworked. The declaration is explicit - a map that simply FORGOT its kido still
fails.

**The research question** ("would there be the same number and size of kiln works in a capital as
in a provincial city?") is answered in research/cities/capitals.md and encoded in
`capital_trade_counts_scaled`: four scaling classes, not one. Bathhouses and pawnshops multiply
at attested per-capita ratios; kilns and cremation grounds consolidate; theater and the domain
school are capital-only; the pauper's ground is fixed at one per seat by Song edict.

## THE GM's SECOND RENDER REVIEW (2026-08-10) - the check-gap audit and 16 more rules

The GM read the map again and sent defects in a stream. Every one got a check first, red against
the artifact, then the fix. The through-line of the whole round is one sentence: **a feature
defined by a relationship must be DERIVED from that relationship, and the check must be able to
run.** Two systemic findings dominated:

**1. The capital tier was running 116 fewer checks than a provincial city.** Every urban rule
tested `scale == "city"` EXACTLY, and the capital, added later, inherited nothing - which is why
the GM could see there was no cremation ground, no ossuary and no mausoleum on a city of 12,400
while the gate showed green. `URBAN = scale in ("city", "capital")` now covers both. What made
the audit trustworthy was classifying the residue rather than switching everything: the wall-
capacity model stays provincial (it does not know a castle eats 40% of the interior), the three
capital MOAT inversions were already documented as deliberate and were restored after my bulk
switch overrode them, the ward-seal pair honors `meta(ward_gates)`, and the farmland family is
scoped off a sheet that frames only the city. **Diagnostic worth keeping: run `gate()` on two
maps of different tiers and diff the check names that appear.**

**2. Moving geometry strands whatever was pinned to it.** The river's re-route had left the
towpath 100+px inland, a sluice on dry ground, the aqueduct's intake mid-channel and its basin
in the moat, the granary rows and jetties at an angle the bank no longer had. Six checks now
measure against the CURRENT geometry (`towpath_hugs_the_bank`, `sluice_gates_on_water`,
`sluice_gates_centered_on_their_channel`, `aqueduct_taps_water_lands_dry`,
`tanning_yards_on_water`, `waterside_works_follow_the_bank`), and the gen derives `BANK_ROT` and
every jetty angle from the polyline instead of carrying a constant.

**The calibration discipline that made the numbers defensible.** Three rules were set by
MEASURING the pool rather than picking: the extramural tether (every shipped works sits 225-1,382
ft from its wall; the flagged kiln stood at 1,563), the gate-market head (157-273 ft across
Tango, Minami and Nagahara), and the wash-trade band (18-48 ft). The funerary cap came from
RESEARCH instead, and overturned the existing draw: see research/cities/capitals.md.

**Six mistakes of my own, each worth more than the fix:**

- **A guard removed as "unreachable" on the evidence of live maps only.** The label-length test
  in the caption checks looked dead - until five regression fixtures stopped firing, because
  their legacy label records predate the text field and the gate now CRASHED before reaching each
  fixture's own check. **The corpus exists to replay shapes the live pool no longer produces.**
- **A threshold in pixels, not real feet.** The tanning band was three times stricter on a
  1 ft/px town than on the capital, and failed a town whose yard sits closer than the capital's.
- **A rule that judged before it could reach its own condition.** The street-reach check's outer
  window capped at 65px while the new perpendicular case needed 80.
- **A perpendicular test that compared the LINE OF SIGHT to the other street** rather than its
  bearing, so any two parallel streets 60px apart read as a failed junction.
- **...and then flagged free ends past junctions they already had**, which would have truncated
  five sound streets across Minami and Nagahara had I trusted it. The exclusion needs BOTH
  crossing and endpoint-touching, in both directions.
- **A corner-only box test**, when a caption wider than the wall band straddles the line with
  every corner clear. The same point-vs-footprint trap this skill has paid for before.

**One engine defect the checks found rather than the eye:** the gate guard/inspection caption was
pushed inward by a fixed radial offset that ignored the label's own 134px width, so on an east or
west gate the box straddled the rampart however far its centre went - and the adaptive fix then
read `M["wall"]` before `city_wall` records it, so the clash test passed at step 0. The caption
LADDER also never knew about the rampart at all; it does now.

## COMMERCIAL ROW DENSITY (2026-08-11)

The GM, on the north gate market: *"Is that the correct amount of space between gate market
buildings? No objection, they just look more spaced out than I expected."* Median gap between
neighboring shops was 84 ft - the wrong urban form, not a tuning error. The research and the
deliberate departure are in `research/cities/fabric.md`, "Machiya row density"; the engine side
is `frontage(dense=True)`.

Where it landed: N market 18 ft median gap, S 18 ft, SW 9 ft, E 48 ft (a loose roadside market at
the Fox-lands gate, which should stay loose). Shops and merchants on the map: 173 -> 182.

**The asks were trimmed to the ground truth at the same time.** Ten frontage runs were landing
under 60% of what they asked for; the refusals were block_polys reservations, crossing ways'
cleared bands and standing houses - i.e. the ground beside those streets is genuinely taken, not a
placement bug. Each was sliced to the count it actually seats (a prefix slice, so the drawn map is
byte-identical), and one run was deleted outright: the north gate market's INNER file, between the
road and the moat bank, had ~26 ft of usable ground after the road's band and the bank and placed
exactly zero. The market is the outer file plus the head pocket. Manifest now records 36 of 44
seats (82%) across 4 runs, against 129 of 283 (46%) across 17 before.

**Knock-on worth remembering:** the denser rows seated 4 more suburb dwellings than the budget band
allows. Taking them off the wharf hamlet turned `alleys_serve_buildings` red - that alley exists to
serve those households - so they came off the porters' rows on the towpath shore instead, which no
alley depends on. A trim in a fabric this tight is a siting decision, not an arithmetic one.

## OPEN QUEUE (GM items raised 2026-08-11, in the order they came in)

Recorded here rather than held in a session's head - this list is the contract.

1. ~~**Aqueduct captions adrift.**~~ **DONE 2026-08-11** - see `waterworks_captions_stand_at_their_point`; intake weir 195->39 ft, settling basin 348->40 ft, sluice captions 102 ft -> beside their gates. Originally: "The intake weir and the settling basin labels are really far away
   from the things they label... if a label can be moved closer because there is literally nothing
   between the label and the thing it is labeling, we should do it, up to some minimum distance."
   DIAGNOSED: all three aqueduct captions are hand-placed `s.label(...)` with `ref=None`, so they
   bypass the standoff ladder (which seats at LABEL_MIN_AIR = 5 px) AND escape
   `label_hugs_its_referent`, which only governs labels that declare a subject. FIX: a check that a
   caption naming a specific FEATURE must carry a referent (the caption-group vocabulary in
   `_LABEL_GROUP` is the test for "names a specific feature"), then convert these to
   `place_caption` so the ladder seats them.
2. ~~**The wharf's form.**~~ **DONE 2026-08-11** - the `quay()` glyph is written and drawn: a faced bank edge with three stepped landings and mooring posts, derived from the river's own line so a re-route carries the wharf with it. A jetty springing from the quay is a declared allowed pair, not a defect. RESEARCH, recorded in `research/cities/river-cities.md`: the pier is not the main event - a river's level moves feet across the year, so the working form is a revetted quay face with STEPPED landings (matou / gangi), right at every water level. Three piers for six granaries is fine; the bank is the unloading face. STILL TO DRAW: the quay edge and its steps. Originally: Is three piers right for six granaries and three warehouses, and is there
   a DOCK or quay structure distinct from the piers that the map should draw? Research and record,
   then draw whatever the research says is visible.
3. ~~**Flophouses.**~~ **DONE 2026-08-11** - `roadside_works_stand_on_their_road`, plus a bearing DERIVED from the way at draw time. Fixed on the capital and on Tango, Hirameki and Minami; Hoshizora carries a documented waiver (no seat in that town lets a 104 ft dormitory lie along its road). Originally: Max distance from the road they stand on, and ORIENTED to it - the one outside
   the southwest gate is ~300 ft off the road and level while the road is not. All nine currently
   record `rot: 0`.
4. ~~**Kiln works**~~ **DONE 2026-08-11** - same derivation; both capital kilns now lie at the road's 165 deg. Note the calibration: a kiln carries an ANGLE rule but no distance rule, because a nuisance works belongs out of town by its nature. Originally: must be slanted to the road's angle, like the dye works.
5. ~~**South crop too loose.**~~ **DONE 2026-08-11** - the cause was a caption, not the crop: `no_caption_holds_the_frame_open` now fails any label reaching more than 120 ft past the last STRUCTURE on its side (canopy counts as structure, so a wood's caption over its wood is fine). The Imperial road and towpath words moved up their own lines; south margin 305 ft -> **106 ft**. Originally: MEASURED: the crop is working (margin 36 px ~ 110 ft), and what holds
   the frame open is a CAPTION - "Imperial Road" at y2781 and "towpath" at y2772 float in empty
   ground 305 ft south of the last structure. Same root cause as item 1. Needs a rule that a
   caption may not be the only thing holding the frame open.
6. ~~**Samurai country estates**~~ **DONE 2026-08-11** - `capital_dir` corrected to northeast and
    the three walled country seats moved to the northeast approach; the standing question is now
    recorded in `settlements/cities.md` ("ASK THESE THREE BEFORE DRAWING ANYTHING") alongside water
    flow and clan. **ONE CONTRADICTION LEFT FOR THE GM:** the Imperial road on this map leaves to
    the NORTHWEST, so if the capital is northeast the road should too. Not re-routed on my own -
    moving an Imperial road moves the gate markets, the relay stables and the farrier with it.
    Originally: (northeast here, not
   northwest). GM: this is a standing question to ASK when making a city, alongside water-flow
   direction and clan - so it goes in the skill's always-ask list, gets a `capital_dir` meta, and
   gets a check keyed on it.
7. ~~**The street that stops just short.**~~ **DONE 2026-08-11.** The near-misser was a LANE, and
   `sr_enders` - the list of way-ends the check walks - held streets and alleys and **not lanes**,
   so a lane's ends were never examined by any test in that check. A check that never looks at a
   feature looks exactly like a check that passes. Two changes: lanes are walked now, and the
   alley exemption (a roji legitimately dead-ends inside the block it threads) is bounded by
   LENGTH - past 600 real ft a lane is a through-way and must close its junction. Frozen first as
   `pool/regressions/long_lane_stops_short_of_its_street_shiro_daika.json`, watched go red, then
   the lane at x1965 was run to the y1770 street it had been halting 90 ft short of.
   NOTE: the GM described this as being near the SOUTHWEST gate and at a strange tilt; the defect
   the check found is on the EAST side and perfectly vertical. Either the description was of this
   same junction from memory, or there is a second one - worth a look at the render before
   calling it closed.
8. ~~**`rowpack` records no shortfall**~~ **DONE 2026-08-11** - it records now, and the first version of that record was WRONG in an instructive way: rowpack walks an INDEX where pack and frontage POP, so handing `_shortfall` the whole list reported every run as asking exactly double what it was given. A run seating half its ask looked like one seating a quarter, and trimming to the reported figure just halved it again - a fixed point at 50%%, failing forever. Also calibrated: a run asking fewer than 8 is judged on whether ANYTHING landed, not on a percentage. Originally: (settlement-review, 2026-08-11), so
   `placement_runs_meet_their_ask` is blind to it: Jurojin's monzen flanks drew 1 and 0 of 40 and
   another row 4 of 24, all green. Make `rowpack` record exactly as `pack` does, then trim or seat
   what it reports.
9. **Settlement-review's other findings:** the Benten monzen is one-sided (a walled manor court
   holds the east flank) while its comment claims two files; the band street's comment still
   asserts a cure its trimmed ask no longer performs; the east gate market kept `spacing=32` and
   still reads dotted while its three siblings are dense; no gate market is captioned.
10. **One red check on the capital:** `city_well_density_sufficient` - two blocks at 27 and 29
    households per wellhead against a cap of 26. Everything tried and what it taught:
    - `open_seat(..., well=True)` finds nothing at 12, 10 or 8 px anywhere in either block. Before
      the packs run there are no dwellings for a well seat to validate against; after them the
      ground is full. That is the documented over-restrictive collision circle (CLAUDE.md, "CENTER
      vs FOOTPRINT" item 2), not genuinely full ground.
    - Tightening the derived per-quarter well grid DOES add wells, but the ones it adds land near
      existing wells and trip `wells_not_clustered` (5 inside a 150 ft radius) before the deficit
      clears. The two rules meet in the middle with one household of daylight between them.
    - Trimming the covering packs' asks changes NOTHING: both are capacity-bound, so they were
      already placing fewer than asked. Worth remembering before reaching for that lever again.
    The honest fix is upstream: make the placer test the rotated footprint it will actually draw so
    the circle can be replaced by a real overlap test (the item-3-then-item-2 order in CLAUDE.md).
    Until then this is one wellhead short in a warren, and it is left RED rather than waived - a
    waiver is for a place with a history, and "the packer would not seat a wellhead" is a defect.
11. **PADDY: DRAWN 2026-08-11, two checks outstanding.** One comb field on the open ground south
    of the rampart, tapped off the river's lower reach with the current (flow_deg 117.7), head gate
    at the tap and a second at the field, the fall running WITH the current so the drain returns
    downstream of its own intake, and the dry hem narrowed to clear the towpath. 155 plots. What is
    NOT done: the households that work it. Every seat - ringed, asked of open_seat, or placed
    directly against the placer at ten positions around the envelope - is refused, and the probe
    says why: **6 of 10 by the collision circle**, 3 by a corridor, 1 by a keep-out. Which is the
    SAME defect that blocks the wellheads. Originally: - the same patterns the provincial
    cities use: paddy blocks tied to the declared water flow, drainage ditches feeding the moat or
    the river DOWNSTREAM with the current, and feeder channels tapped so the water turns into them
    with the flow rather than against it.
