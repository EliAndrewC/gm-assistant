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
