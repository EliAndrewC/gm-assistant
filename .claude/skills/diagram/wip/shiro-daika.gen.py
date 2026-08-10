#!/usr/bin/env python3
"""Shiro Daika - the DOMAIN CAPITAL of the Daika house (diagram skill, Mode B, 1px = 3ft).

SKELETON (feature 019) + THE GROUND-RESERVING LAYER (feature 020). The map now carries the wall,
the moat, the river, the ways, the gates, the CASTLE - and every compound and public work that
must be sited BEFORE housing: the government ward on the ote-suji, the Imperial Magistrate's
compound, the eight lineage compounds, the two sovereign temples and the teramachi rim, the
wharf with its granaries and brokers' row, the towpath, and the aqueduct. All housing (the
rank-graded samurai districts, retainer terraces, commoner machi), the public wells, the fire
towers and the kido mesh are feature 021's - the packs flow around the ground reserved here.

THE HOUSE. Daika is a Bayushi vassal house of the SCORPION, seated here; Ubame county (see
pool/towns/ubame.gen.py) is one of its county seats, out in Moriguchi province, and the charcoal
road that leaves Ubame westward arrives at this city's EAST gate. Scorpion patron fortunes are
Benten and Jurojin, so the two sovereign temples are theirs.

THE WAYS (GM 2026-08-08, confirmed against the campaign map). The IMPERIAL ROAD enters at the
SOUTH gate, runs north through the city, and beyond the north gate bends NORTHWEST toward Shiro
Kyo. Two unlabeled domain trunk roads leave the other gates: EAST to the Fox lands and the
Kitsune Mori, SOUTHWEST into the heart of the domain. Only the Imperial road is named - an
ordinary road's course is already visible.

THE RIVER runs NORTHEAST -> SOUTHWEST past the city's southeast flank and off both edges. NO
TRUNK ROAD RUNS ALONGSIDE IT: water carried bulk far more cheaply than carts, so a highway
shadowing a navigable river is redundant, and the roads leave in the directions the water does
not serve. The bank carries the TOWPATH (the Chinese qiandao - upstream haulage, so it
supplements the boats rather than replacing them), running to the wharf and no further. See
research/cities/capitals.md, "A river gets a TOWPATH, not a road".

THE CASTLE sits in the ring (castle_seat="ring" - both traditions nest their citadel, so it is
the median form), north of center, with its OTE-MON FACING SOUTH onto the ceremonial approach
that runs down to the Imperial road's south gate. That is the jokamachi rule: the main road
passes the castle's FRONT, "to indicate the glory of the ruler". Its interior is BLANK and stays
blank - see Settlement.castle's docstring for the sync argument.

THE GRAIN IS IN TWO PLACES FOR TWO REASONS (settlements/capitals.md): the siege stock is inside
the castle (implied, never drawn); the working stipend-and-transhipment rice is the domain
granary at the wharf. The EMPEROR'S granaries are separate again - they face brigands, not
besiegers - and this map exercises imperial_granary_seat="wharf" (grain moves by boat).
"""

import math
import os
import sys

# Walk UP to the engine rather than counting directories: this map lives in wip/ while it is a
# draft and moves to pool/capitals/ when feature 021 makes it green, and a hard-coded depth
# breaks on exactly that move.
_D = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(_D, "settlement.py")):
    _D = os.path.dirname(_D)
sys.path.insert(0, _D)
from citybudget import CapitalProgram, budget_to_manifest, plan_capital  # noqa: E402
from settlement import Settlement  # noqa: E402

s = Settlement(3200, 3050, seed=61)
s.meta(
    water_flow=135,  # DRAINAGE BEARING: the land falls NE -> SW, the way the river runs (0=E, 90=S)
    name="Shiro Daika",
    scale="capital",
    walled=True,
    population=12_360,
    ftpx=3,
    wall_defense="siege",  # the Crab border lies south: built to survive a siege even after a long peace
    imperial_road=True,
    clan="Scorpion",
    capital_dir="northwest",  # Shiro Kyo, and the Imperial road beyond it
    # THE LINEAGE DECLARATION (feature 020). Bands track HOUSEHOLDS HOUSED, never the rank of the
    # head: the chargen weights ([house][[daika]]) give six chancellors (daika 19, hazama 16,
    # utsuro 15, tokiwa 14, anzu 12, kurogi 11) and three below the threshold (yodo 5, nio 4,
    # seki 4). kurogi is PROVINCIAL (seated in Moriguchi), so its chancellor keeps a capital
    # estate that is visibly smaller - most of the kurogi live around their own provincial city.
    # The ruling daika lineage has NO compound: its seat IS the castle.
    lineages={"hazama": "grand", "utsuro": "grand", "tokiwa": "grand", "anzu": "grand", "kurogi": "estate", "yodo": "house", "nio": "house", "seki": "house"},
    ruling_lineage="daika",
    # The gates' furniture, the wharf works, the towpath and the aqueduct are the only features
    # outside the rampart until feature 021 fills the interior - the frame reads sparse, not wrong.
    # temple doctrine (020): the rim BELTS the rampart as part of the defenses; the two
    # sovereign precincts are the "two great complexes" and the five modest rim temples are
    # lineage bodaiji (Hotei is Tokiwa's). "large" is the recognized exception slug.
    temple_exception="large",
    temple_fortunes=["Benten", "Bishamon", "Daikoku", "Ebisu", "Hotei", "Inari", "Jurojin"],
    # THE WIND (T021, research item 10): continental east-coast monsoon - winter NW is the
    # design wind (fire season, steadiest flow); nuisance trades sit in the lee-and-
    # downstream arc (S-SW riverward, below the wharf).
    wind_from="northwest",
    # INTERIOR WARD GATES: OFF for Shiro Daika (GM 2026-08-10). The doctrine (capitals.md:
    # kido at the block and lane mouths, no continuous ward fence) stands and the knob stays
    # for other cities - but the mesh this map derived wandered mid-street and read as neither
    # a wall nor a gate, so the capital ships without interior gates until the placement rule
    # is reworked. The rampart gates, the samurai ward's own seal and the castle stand as they were.
    ward_gates=False,
    waivers={
        "population_consistent_with_housing": "First-pass fabric at the settled wall: every band drew, but realized machi density leaves the census ~130 households short of 12,360/5; the GM (2026-08-10) deferred interior fullness to the fabric-first regeneration (future-work.md #2/#5) rather than grind the packs further this pass.",
        "city_no_large_empty_space": "The ~1.5-acre pockets that remain rotate to a new spot on every reflow because the first-pass packs under-fill the settled wall by ~8%; the stable cores are all claimed (the drill grounds, the moat firebreak, the rampart approach, the S-gate column ground) and the rotating residue is the same deferred-fullness gap (GM 2026-08-10, future-work.md #5).",
    },
    crop_outlier_ok="Outside the rampart the map carries only the gate furniture, the wharf works, the towpath and the aqueduct until feature 021 fills the interior; sparse outliers at this stage are the build order showing through, not a siting error.",
)

# ---- BUDGET-FIRST (feature 018): the wall is an OUTPUT of the declared program, never a guess.
# A capital cannot be sized from population the way a provincial city nearly can - a median castle
# alone is ~85% of an entire provincial city's interior.
BUDGET = plan_capital(CapitalProgram(population=12_360, river=True, castle_seat="ring", imperial_granary_seat="wharf"), canvas=(3200, 3050))
s.meta(budget=budget_to_manifest(BUDGET))

CX, CY = 1400, 1313
# the SETTLED rampart (021, GM 2026-08-10, third and final derivation - the wall-settles-first
# pass): packed-tight C_PACKED_CAPITAL 950 + CIRC 0.15 + the wharf-hamlet extramural ruling
# give required ~3.92M px^2; this 1110x1150 ellipse encloses it at ~+0.9%, recentered on the
# CASTLE AXIS (x=1400) so the Imperial road runs straight through both its gates again.
# History of the first wall: sized with Tango's C_PACKED
# (690 px2/family) and the capital's as-built machi delivers ~1,367 - so 57% of the packed
# cohort ended up outside the walls against the researched 30% suburb share. The budget now
# prices the in-wall packed line with C_PACKED_CAPITAL (1350, measured on this map's own
# fabric), required interior 4.23M px2, and this ellipse encloses it at ~+2%. The center
# moved SW (the castle now sits NE-of-center, the honmaru-at-the-back pattern) because the
# east is pinned by the river and the west by the canvas; the river's mid-course shifts
# ~140px east to keep the ~200px wall-to-river band the wharf chain needs.
RX, RY = 1110, 1150
NRING = 20
WALL = [(round(CX + RX * math.cos(-math.pi / 2 + 2 * math.pi * i / NRING)), round(CY + RY * math.sin(-math.pi / 2 + 2 * math.pi * i / NRING))) for i in range(NRING)]
NGATE, EGATE, SGATE, SWGATE = WALL[0], WALL[5], WALL[10], WALL[13]

# ---- the river: NE -> SW past the southeast flank, off both edges. Upstream (NE) first, which is
# the convention every junction-angle rule keys on.
# Held ~200px off the moat at its closest approach: the ring is 1,055x983 px of pushed-out wall,
# and the first cut ran the river straight through the southeast arc.
RIVER = [(3200, 640), (2960, 1100), (2640, 1720), (2260, 2380), (1900, 3120)]
s.river(RIVER)

# ---- the rampart and its four gates, then the moat and the patrol road inside it
s.city_wall(WALL, gates=[NGATE, EGATE, SGATE, SWGATE])
MOAT = s.moat(WALL, gap=26)
RING = s.ring_road(WALL, inset=30)
s.bound = [list(p) for p in RING]

# ---- THE WAYS. The Imperial road runs south gate -> north gate and bends NORTHWEST beyond it
# toward Shiro Kyo; its label sits OUTSIDE the wall, because inside the rampart the same roadway
# is a city street the city maintains, not an Imperial responsibility.
# THE KAGI-NO-TE. The first cut ran this road dead straight from gate to gate at x=1400 - and the
# castle stands on x=1400, so the roadbed crossed its moat, entered the ote-mon, ran 2,100 ft
# through the blank court and pierced the north rampart where there IS no gate. Invisible on the
# render only because the court fill is drawn over it (settlement-review, 2026-08-09).
#
# The fix is the historically right one rather than a nudge: the jokamachi rule is that the main
# road passes the castle's FRONT, not through it, and a castle town deliberately bends its highway
# rather than offering a mile-long straight run at the daimyo's gate - that bend is the kagi-no-te.
# So the road comes north to the castle's south front, turns west past it, and comes back to the
# north gate. The bend sits at y=1560 (feature 020 moved it south from 1420) so the ote-suji stub
# is long enough to carry three ministry compounds a side with the 14px office standoffs.
KAGI_Y = 1560
# ...with straight STUBS through the north gate (GM 2026-08-09: the old geometry bent AT the
# gate point, so the roadbed rode along the rampart stroke): the diagonal legs meet a short
# perpendicular run on each side of the gate, and the bed passes clean through the gap.
s.road(
    [
        (SGATE[0], 3095),
        (SGATE[0], SGATE[1]),
        (1400, KAGI_Y),
        (800, KAGI_Y),
        (800, 470),
        (1400, 300),
        (NGATE[0], NGATE[1]),
        (1400, 110),
        (1200, 92),
        (1040, 108),
        (860, 150),
        (660, 110),
        (500, 20),
        (460, -60),
    ],
    label="Imperial Road",
    label_xy=(SGATE[0] + 145, 2820),
)
# the same road is Imperial on BOTH sides of the city (GM 2026-08-09) - the run toward Shiro
# Kyo carries its own caption, tilted along the branch per the linear rule
s.label(1170, 66, "Imperial Road", 11, italic=True, color="#6E5B38", rot=195, linear=True)
s.road([(2387, 1390), (2385, 1313), (EGATE[0], EGATE[1]), (2820, 1240), (3200, 1150)])  # east, to the Fox lands - the first leg runs INSIDE the gate to join the ring road (gate_roads_join_the_ring)
# the karamete approach is the STRAIGHT CONTINUATION of the north gate's street (GM 2026-08-09:
# the first cut hung it off the diagonal mid-slope and the two beds read as overlapping roads):
# city gate -> due south -> the castle's rear gate, dead-ending at its moat and tower exactly as
# a castle-town street aimed at the works should, while the Imperial through-road leaves the
# street at the (1400, 300) junction and bends west around the castle front (the kagi-no-te).
s.road([(1400, 300), (1400, 520)])  # stops at the karamete tower's foot, as the ote-suji stops at the ote-mon's
s.road([(636, 1772), (664, 1844), (SWGATE[0], SWGATE[1]), (300, 2120), (0, 2200)])  # southwest, into the domain - the first leg runs INSIDE the gate to join the ring road (gate_roads_join_the_ring)

# ---- THE OTE-SUJI (feature 020): the ceremonial avenue from the castle's front gate south to the
# Imperial road at the kagi-no-te bend. Drawn as a road (M["roads"]) so the shared crossing source
# carries it over the castle moat, and UNLABELED - only the Imperial road is named.
# 45 REAL FEET (GM 2026-08-09, "it looks huge"): the first draft passed width=32 raw PIXELS -
# 96 ft at this scale, nearly 4x the Imperial highway - where the engine's convention is real
# feet through lw() (the road default is lw(26), the Tokaido's width). The honest ceremonial
# band is Edo's own grand avenues: Honcho-dori 13.8 m (~45 ft), Nihonbashi-dori 18.2 m (~60 ft)
# - and that is the SHOGUN'S capital, so a domain capital's ote-suji takes the Honcho class:
# 45 ft, still half again the 26 ft highway it meets. research/cities/capitals.md, "Street widths".
OTE_X = 1400
s.road([(OTE_X, 1240), (OTE_X, KAGI_Y)], width=s.lw(45))  # starts just south of the ote-mon's gate tower

# ---- THE CASTLE. North of center so the ceremonial approach has room to run south to the gate;
# ote-mon SOUTH, per the jokamachi rule that the main road passes the castle's front. Blank inside.
# the caption is "Shiro Daika" PLAIN: shiro already means castle, so "Shiro Daika Castle" reads
# "Castle Daika Castle" - the Mount-Fujiyama construction Constitution XI exists to catch. Town
# and castle sharing the name is the jokamachi reality (settlement-review, 2026-08-09).
# TWO GATES (GM 2026-08-09, researched): the ote-mon fronts south onto the ceremonial
# approach; the karamete-mon - the rear gate every castle kept, the sortie gate - opens north,
# its approach road bridging the castle's own moat to join the Imperial road's run to the
# city's north gate. research/cities/capitals.md, "A castle has TWO gates".
s.castle(
    1400, 880, 850, 700, label="Shiro Daika", gate_dir="south", karamete_dir="north"
)  # the castle keeps ITS axis (x=1400) - the resized wall re-centered SW, and the honmaru sits NE-of-center (the castle-at-the-back pattern); everything castle-anchored (ote-suji, ministries, karamete) reads from this axis, not from CX

# ---- the moat CIRCULATES river-to-river, every drawn drop moving NE -> SW (GM 2026-08-09,
# third cut - the second still ran its last leg up-screen). Like Minami and Nagahara the moat
# now connects to the river at BOTH ends; their moat feet touch the bank directly, this
# stand-off ring reaches it through two moat-width (66 ft, Tango's gauge) sluiced leats:
#   - the FEEDER taps the river's upper reach (downstream of the aqueduct's intake) and runs
#     monotonically down-map to the ring's east arc - every segment moves west and south, the
#     declared water_flow=135 bearing;
#   - the DRAIN leaves the ring's southeast arc and rejoins the river just below its bend,
#     approaching swept DOWNSTREAM, and the river there is genuinely lower ground than the arc.
# The towpath crosses the drain's mouth on a plank deck - a real towpath bridged every side
# drain it met, or the haulage teams could not pass.
FEED_TAP = (3080, 862)  # the river's west bank - upstream of the city, downstream of the aqueduct intake
s.stream([FEED_TAP, (2870, 875), (2650, 880), (MOAT[4][0], MOAT[4][1])], frm={"kind": "river"}, to={"kind": "moat"}, width=s.px(66))
# the boards sit a few steps DOWN their channel runs, not at the junctions (GM 2026-08-09: at a
# junction the local water direction is ambiguous, so the correctly-across board read as a
# coincidentally axis-aligned bar; astride the clear run, across-the-channel explains itself)
s.sluice_gate(
    3051, 863.8, rot=math.degrees(math.atan2(875 - FEED_TAP[1], 2870 - FEED_TAP[0])) + 90, label="sluice gate", label_xy=(3040, 818), span=26
)  # the intake board - the frame spans BANK TO BANK (posts on the abutments, the operator walks the crossbeam)
DRAIN_OUT = (MOAT[8][0], MOAT[8][1])
s.stream([DRAIN_OUT, (2000, 2460), (2172, 2557)], frm={"kind": "moat"}, to={"kind": "river"}, width=s.px(66))
s.sluice_gate(
    2018, 2408, rot=math.degrees(math.atan2(2460 - DRAIN_OUT[1], 2000 - DRAIN_OUT[0])) + 90, label="sluice gate", label_xy=(1986, 2372), span=26
)  # ON the drain's centerline (the old seat predated the drain's re-route - GM 2026-08-10)  # the outfall board, bank to bank like the intake
s.moat_flow(MOAT[4], MOAT[8])

# ---- THE AQUEDUCT (feature 020; rebuilt to the researched josui form, GM 2026-08-09). What
# the research says a josui IS (research/cities/capitals.md, "How a josui actually ran"): an
# intake WEIR on the river peeling off at a SHALLOW DOWNSTREAM angle (Hamura's nagewatashi
# weir); an OPEN earth cut - open-topped, hence water-blue between spoil banks - falling
# gently and continuously (Tamagawa: 92 m over 43 km, never a climb); a terminus at the city
# gate's waterworks head (Yotsuya Okido), the settling tank on the moat's OUTER bank; and
# BURIED wooden mains (mokuhi) beyond it, feeding cistern-wells (josui-ido) the residents
# bucket from - feature 021's, with the wells. The first draft ran the cut up-screen around
# the whole northeast and crossed the moat on a flume; the corrected route peels off
# downstream and falls straight to the EAST gate - short and direct because the river is
# near, where the real ones wound only to HOLD their gradient across long country.
s.aqueduct([(2962.4, 1047.9), (2790, 1130), (2660, 1215), (2554.4, 1294.2)])  # terminus pulled up its own line to land the settling basin CLEAR of the moat (it was IN the channel - GM 2026-08-10)
# the two ends carry the words the glyphs cannot (GM 2026-08-09): the river end is the INTAKE
# WEIR (the Hamura form - a barrier angled across part of the stream, shouldering water into
# the cut), and the gate end is the SETTLING BASIN, where silt drops before the buried mains
# All three aqueduct words share the duct's bearing and the same ~20px uphill offset from the
# channel line (GM 2026-08-09: the end labels were level while "aqueduct" lay along the cut).
s.label(2965, 985, "intake weir", 9, italic=True, color="#5E7A8A", rot=151, linear=True, full_tilt=True)
s.label(2612, 1196, "settling basin", 9, italic=True, color="#5E7A8A", rot=-33, linear=True, full_tilt=True)  # beside the terminus, clear of the rampart band (GM 2026-08-10)
s.label(2705, 1160, "aqueduct", 10, italic=True, color="#5E7A8A", rot=151, linear=True, full_tilt=True)

# ---- THE TOWPATH (feature 020): on the wharf's own (west) bank, coming up from downstream -
# upstream haulage is the whole reason it exists - and ending at the wharf, no further.
# ...ending AT the quay by the downstream landing stage (GM 2026-08-09: the old end stopped
# short of the jetty and hugged the waterline, reading as a line that dissolves into the
# river), and LABELED - the haulage path cannot explain itself at fit zoom
s.towpath([(1877, 3109), (2221, 2400)])  # the CURRENT river's bank, offset w/2+6 landward (the old pts predated the re-route - GM 2026-08-10)
s.label(2035, 2770, "towpath", 10, italic=True, color="#8A7050", rot=-64, linear=True, full_tilt=True)
s.bridge(2000.2, 2459.3, -32.5, 49, 4)  # the wharf shore path's plank over the moat drain (GM 2026-08-10: no way stands in water without a deck)
s.M["bridges"][-1]["foot"] = True
s.bridge(
    2150.9, 2545.1, -64.1, 28, 4
)  # the towpath's plank AT the computed towpath x drain crossing (the drain's river-to-river re-route moved the ford and the deck kept its old seat - review 2026-08-10); oblique span 22px water / sin(84 deg) + 6px bank rests
s.M["bridges"][-1]["foot"] = True  # a footplank on the haulage path, not a road deck

# ---- carry every way over the water it crosses. AFTER all roads and water, as bridges() requires:
# the south/east/southwest/north gates' moat crossings, the east road over the RIVER, and the
# ote-suji over the castle's own moat all take decks from the one shared source (feature 020).
s.bridges()

# ---- THE GOVERNMENT WARD (feature 020): the six domain ministries flanking the ote-suji in two
# files of three, the House Chancellery and the domain school continuing the same axis south of
# the kagi-no-te bend. Both anchor traditions converge on exactly this form - Beijing's Six
# Ministries lined the Corridor of a Thousand Steps outside Chengtianmen, and a jokamachi's
# offices spilled out of the ninomaru into the town (settlements/capitals.md, "The government
# ward"). Default ministry compound: 224x148 ft, the researched provincial size - a domain
# ministry is the same bureau of clerks and archives at a bigger desk.
# the files sit a ~21 ft setback off the avenue's edge - corridor frontage, not detached
# blocks; captions ON the glyphs (the estate rule applied to state offices, GM 2026-08-09 -
# a provincial city's smaller compounds keep theirs beside)
for i, nm in enumerate(("Rites", "Revenue", "Retainers")):
    s.ministry(1348, 1330 + 85 * i, f"Ministry of {nm}", label_inside=True)
for i, nm in enumerate(("War", "Works", "Justice")):
    s.ministry(1452, 1330 + 85 * i, f"Ministry of {nm}", label_inside=True)
# NO House Chancellery compound (GM 2026-08-09, researched): the council of lineage
# representatives meets IN the castle - Edo's Hyojosho and Roju sat within Edo castle, China's
# Grand Secretariat inside the palace. Executive ministries out, the ruler's council in; the
# chamber is part of the castle's implied goten. The DOMAIN SCHOOL is the hanko - a school of
# letters with a martial wing - so it takes the martial-hall vocabulary, not a ministry box.
s.hanko(1482, 1658)  # ~1 ha compound (size audit 2026-08-09) - shifted east so its wall clears the road

# ---- THE IMPERIAL MAGISTRATE'S COMPOUND (feature 020): FOREIGN SOVEREIGN GROUND - ~56 staff plus
# family, funded at 700 koku/yr for "manor maintenance, grounds, stable, fortified walls,
# ceremonial halls" (budgets.md). The manor form in its OWN ink, deep jade against the ministries'
# state violet, so it reads as not-of-the-domain; gate west, facing the government ward it works
# beside.
# captioned as the INSTITUTION, not the officeholder (settlement-review 2026-08-09; Ubame's
# sibling is "Magistrate's Manor" and capitals.md says "the Imperial Magistrate's compound")
# "Imperial Magistracy" - the institution, shortened so the caption fits INSIDE the court
s.manor(1720, 1445, 100, 75, "Imperial Magistracy", gate_dir="west", ink="#274D3D", label_inside=True)


# ---- THE LINEAGE COMPOUNDS (feature 020): eight named walled yashiki in the samurai ground,
# graded by households housed. The four grand chancellery estates flank the castle east and west
# (closest to the court = highest standing); kurogi - a full chancellor whose people live out in
# Moriguchi - takes a visibly smaller estate near the east gate; the three modest houses hold the
# band north of the castle. daika, the ninth, IS the castle.
def lineage_manor(x: float, y: float, w: float, h: float, name: str, gate_dir: str) -> None:
    # label INSIDE the blank court (GM 2026-08-09: the estate's contents live on its own Mode A
    # sheet, so the empty court is the label's ground - like a governor's mansion caption)
    s.manor(x, y, w, h, f"{name.title()} Estate", gate_dir=gate_dir, label_inside=True)
    s.M["manors"][-1]["lineage"] = name  # the field capital_lineage_compounds_labeled reads


lineage_manor(2035, 720, 158, 122, "hazama", "west")
lineage_manor(2075, 975, 152, 118, "utsuro", "west")
# the west pair stands WEST of the Imperial road's kagi-no-te leg (x=800) - the strip between
# that leg and the castle moat is too narrow for a grand estate. Tokiwa sits in the narrowing
# band between the ring road and the leg, trimmed a size so its corner clears the patrol road
# (ring_road_kept_clear runs at this tier since 2026-08-09; the grand band still steps >= 1.5x
# over kurogi's estate)
lineage_manor(700, 700, 140, 112, "tokiwa", "east")
lineage_manor(665, 975, 140, 110, "anzu", "east")
lineage_manor(2040, 1330, 108, 84, "kurogi", "west")
# the modest row sits south of the road's diagonal run to the north gate
lineage_manor(1150, 425, 76, 58, "yodo", "south")  # below the flattened diagonal to the north gate
lineage_manor(1520, 390, 72, 56, "nio", "south")  # east of the karamete approach road
lineage_manor(1660, 385, 70, 54, "seki", "south")

# ---- THE SOVEREIGN TEMPLES + THE TERAMACHI RIM (feature 020). Two sovereign temples with grand
# abbots - the head houses of domain-wide orders, dedicated to the Scorpion patrons Benten and
# Jurojin - stand in the fabric; the remaining temples BELT the inner face of the rampart as the
# teramachi rim, part of the defenses, rather than gathering in one quarter
# (settlements/capitals.md, "Placements that change").
# Benten, the PRIMARY sovereign temple, is pinned to the full 7-arch avenue (torii_count=7,
# Nagahara's donation-row stride): the per-temple roll gave the primary a 3-arch stub while its
# co-sovereign rolled 7, which read the declared hierarchy inverted (settlement-review 2026-08-09).
s.shrine_hall(1850, 1620, "Temple of Benten", w=s.px(150), h=s.px(100), kind="temple", primary=True, torii=[(1850, 1700), (1850, 1820)], torii_count=7)
# Jurojin's sando faces NORTH, toward the kagi-no-te road it serves (temple_torii_face_the_street,
# GM 2026-08-09 - the first cut marched the avenue away from the road, gateway behind the temple)
s.shrine_hall(950, 1620, "Temple of Jurojin", w=s.px(150), h=s.px(100), kind="temple", torii=[(950, 1583), (950, 1547)])
# THE PRECINCT IS RESERVED EVEN THOUGH ONLY THE HALL IS DRAWN (settlement-review 2026-08-09): a
# sovereign temple is a HEAD HOUSE - abbot's residence, order administration, library, the monks
# living inside the precinct (capitals.md, "a different program, not a scaled precinct") - and
# this is the ground-reserving feature, so the complex's ~390x300 ft ground is held NOW and
# feature 021 draws it. Both registries, like the castle: block_polys is center-tested by the
# packs, placed is distance-tested and stops a wide building overhanging the precinct.
s.precinct_interior(1850, 1620, rear="north")  # sando south (torii 1700/1820): program gathers north
s.precinct_interior(950, 1620, rear="south")  # sando north (torii 1583/1547): program gathers south


def rim_temple(idx: float, name: str) -> None:
    """A modest teramachi hall on the rampart's inner face, ~130px inside the wall ellipse -
    inside the ring road's patrol strip, spaced off the gates and the government axis. Each
    hall's torii approach marches INWARD, toward the city it serves - the rim faces the fabric,
    its back to the defenses."""
    a = -math.pi / 2 + 2 * math.pi * idx / NRING
    tx, ty = round(CX + (RX - 130) * math.cos(a)), round(CY + (RY - 130) * math.sin(a))
    ux, uy = -math.cos(a), -math.sin(a)
    s.shrine_hall(tx, ty, name, w=s.px(96), h=s.px(64), kind="temple", torii=[(tx + ux * 45, ty + uy * 45), (tx + ux * 95, ty + uy * 95)])
    s.cemetery(tx - ux * 42, ty - uy * 42, 20, 14, parish=True)  # the rim temple's own plot in its backstrip (closes the 020 graveyard claim)


rim_temple(2, "Temple of Bishamon")
rim_temple(7, "Temple of Ebisu")
rim_temple(11.5, "Temple of Inari")
rim_temple(15, "Temple of Daikoku")
rim_temple(17.5, "Temple of Hotei")

# ---- THE WHARF (feature 020): the collecting-and-disbursing end of the domain's rice, on the
# river outside the southeast arc - the Asakusa Okura / Kuramae model, a working chain from river
# to store: jetties and a dock basin at the bank, the DOMAIN granary behind the quay (stipend rice
# in, surplus shipping out), the brokers' row fronting the lane before it (MERCHANT, not state -
# the fudasashi pattern: the contracts and lending sit outside the Ministry of Retainers' narrow
# stipend function, and the brokers' money is what will build the theaters next door in 021).
# The EMPEROR'S granaries stand apart upstream (imperial_granary_seat="wharf"): a different
# threat model - brigands, not besiegers - so a stout row outside the castle, near the water the
# grain moves on.
# JETTIES ARE LANDING STAGES, NOT CAUSEWAYS (GM 2026-08-09: at 66 ft they reached past
# mid-river). A stage runs a boat-length into the stream and no further - the fairway stays
# clear by law (the log-boom research) - so ~39 ft into a 120 ft river, a third of the channel.
# One stage per granary complex end: barges tie up AT the kura frontage and unload straight in.
s.jetty(2303, 2265, rot=29.9, length=13)  # the domain row's upstream stage
s.jetty(2236, 2381, rot=25.9, length=13)  # this stage stands on the bend below the row - its own bearing, not the row's  # ...and its downstream one, just past the row's end
# the Emperor's complex gets its OWN landing (GM 2026-08-09: its grain moves by boat - that is
# the whole reason imperial_granary_seat="wharf" - so it does not borrow the domain quay 200 ft
# downstream; separate stores, separate barges, separate tally)
s.jetty(2405, 2089, rot=29.9, length=13)
# NO dock basin: the rectangular canal-head cut is Nagahara's in-city vocabulary and read as a
# floating blue square against this diagonal bank (GM 2026-08-09) - a riverside wharf is jetties
# and quay, not a basin. The granary rows stand ON the wharf, turned PARALLEL to the bank they
# load from, a cart's width off the water; captions plural, one per complex. These are the
# STAGING/working stores - the strategic siege stock is inside the castle, implied, and it would
# indeed be foolish to keep the domain's main reserve outside the walls.
# ...and the kura stand AT the quay (GM 2026-08-09: the first seat held them ~84 ft back "for
# flood", but the Kuramae anchor unloads barges STRAIGHT into the stores - the flood answer is
# the kura's own raised floor and the stone revetment, not distance; a granary you must
# porter sacks to has lost the wharf's whole point)
BANK_ROT = -60.1  # DERIVED from the river's current bearing at the wharf (119.9 deg): the
# rows lie ALONG the bank. Recompute this when the course moves - the first draw was cut to
# a -54 constant and stayed there when the channel shifted (GM 2026-08-10).
s.granary(2253, 2312, n=4, w=20, h=12, gap=8, label="domain granaries", append=True, rot=BANK_ROT)
s.granary(2368, 2121, n=3, w=20, h=12, gap=8, label="Imperial granaries", append=True, rot=BANK_ROT)  # a cart's width UP the bank - the row's ends were lapping the river's stroke
# the brokers' lane runs shore-parallel between the granaries and the quay; its frontage is the
# brokers' row. The wharf suburb is OUTSIDE the ring-road bound the urban packs honor, so the
# frontage places against the suburb's own ground and the bound is restored after.
BROKER_LANE = [(2330, 2120), (2220, 2280), (2135, 2410)]
# a STREET, not a lane (021): the kashi quay street is real machi frontage - the brokers'
# row and warehouse fronts must satisfy businesses_front_streets like any other shops
s.street(BROKER_LANE, width=s.lw(15))
_CITY_BOUND = s.bound
s.bound = [[1940, 1950], [2480, 1950], [2480, 2530], [1940, 2530]]
s.frontage(BROKER_LANE, (["merchant", "merchant", "shop"] * 4), width=8, spacing=19, rows=1, jitter=1, setback=14)
s.bound = _CITY_BOUND

# ---- BUDGET RECONCILIATION (feature 021, T002 - BEFORE any pack runs). From the recorded
# budget block: band targets yashiki 53 / detached 133 / terrace 79 (ranges of ~8 cells ->
# ~10 ranges) / packed 2,160 families; 2,472 dwellings total, of which ~2,430 in-wall and
# ~42-47 samurai households out-wall (SAMURAI_INWALL_FRAC) in the gate suburbs. Ground:
# wall interior 3,043,172 px^2 == the budget's required 3,043,258 px^2 (the wall IS the
# budget's output); standing 019/020 structures 736,580 px^2 (castle 598,000 dominant);
# housing gross need 2,092,330 px^2 + remaining civic ~65,000 px^2 against ~2,306,600 px^2
# free = ~5% slack. NO TARGET IS CAPPED - the packs aim at the full band numbers, and a
# pack that cannot seat its target is a siting bug to fix, not a target to trim (the
# Minami unmeetable-target lesson runs the OTHER way here, by design of the 018 budget).

# ===================== FEATURE 021: THE HOUSING FABRIC =====================
# DRAW ORDER: streets first (packs front them), then the walled yashiki band around the
# castle (each compound reserves its own ground), then detached / terraces / machi packs.

# ---- the machi STREET MESH (south half; the ote-suji, Imperial road and ring road are the
# spines already). Ordinary streets 15 real ft, the market cross main at 18 (Honcho-dori
# class stays the ote-suji's alone). Ends meet the ring road for circulation; the E-W pair
# at y=1350 stops clear of the government band (no street across the ministry fronts).
s.street([(620, 1770), (2180, 1770)], width=s.lw(18), main=True)  # ends short of the rampart's tower line
s.street([(880, 2005), (1799, 2005)], width=s.lw(15))  # dropped south of the Temple of Inari's hall (992,1937)
s.street([(1040, 1284), (1040, 2238)], width=s.lw(15))  # x=1040 clears the Temple of Inari's hall (~x992)
s.street([(1800, 1300), (1800, 1540)], width=s.lw(15))  # stops at the Benten precinct's reserved ground
s.street([(1800, 1700), (1800, 2236)], width=s.lw(15))  # ...and resumes south of it (a precinct blocks a street; the walls are the dead end)
s.street(
    [(2130, 1250), (2130, 1620), (2185, 1668), (2180, 1770)], width=s.lw(15)
)  # east of Kurogi; bends EAST around the Temple of Ebisu (2127,1686) to tie the NE grid into the y=1770 main street (021: streets_connected)
s.street([(800, 1560), (803.9, 2239.0)], width=s.lw(15))  # meets the y=1375 street
s.street([(329.6, 1376.0), (1240, 1375)], width=s.lw(15))  # west end lands on the ring's inner edge  # y=1375: under the west band tail, over the kagi leg
s.street([(1560, 1390), (2387, 1390)], width=s.lw(15))  # threaded between Kurogi's south wall (y1372) and the Imperial Magistracy's north wall (y1407)

# ---- the YASHIKI BAND (T007): 53 walled compounds of Ranks 8-12 wrap the castle N / E / W
# per the jokamachi law (rank = proximity to the court). The EIGHT lineage estates already
# stand in this band and count among the 53, so 45 anonymous compounds join them:
# 18 north (+ yodo/nio/seki = 21), 14 east (+ hazama/utsuro/kurogi = 17), 13 west
# (+ tokiwa/anzu = 15). Each fronts a band lane by its south/east/west gate; sizes jitter
# around the C_YASHIKI footprint (~60 x 50 px at 3 ft/px).
s.district("north yashiki band", "yashiki", [(1100, 268), (2010, 268), (2010, 505), (1100, 505)], rank_band="yashiki")
s.district("east yashiki band", "yashiki", [(1855, 555), (2165, 555), (2165, 1760), (1855, 1760)], rank_band="yashiki")
s.district("west yashiki band", "yashiki", [(590, 555), (945, 555), (945, 1460), (590, 1460)], rank_band="yashiki")
s.district("ote west yashiki flank", "yashiki", [(1150, 1290), (1315, 1290), (1315, 1540), (1150, 1540)], rank_band="yashiki")
s.district("ote east yashiki flank", "yashiki", [(1560, 1290), (1855, 1290), (1855, 1390), (1560, 1390)], rank_band="yashiki")
s.lane([(1140, 475), (1870, 475)], width=7)
s.lane([(1965, 1270), (1965, 1740)], width=7)  # the southern leg, west of Kurogi + the Benten precinct
s.lane([(1205, 1300), (1205, 1520)], width=7)  # the ote west flank's own lane

_YJ = ((2, -2), (-4, 2), (4, 4), (-2, -4), (0, 2), (3, -3))  # deterministic size jitter, no stream draw


def _yashiki(x: float, y: float, gate_dir: str, i: int) -> None:
    _w = 60 + _YJ[i % 6][0] + round(2 * s._hjit(x, y, 31.0)) - 1  # survey jitter: 42 plots in 6 exact
    _h = 50 + _YJ[i % 6][1] + round(2 * s._hjit(x, y, 32.0)) - 1  # size classes read stamped (review 2026-08-10)
    s.manor(x, y, _w, _h, None, gate_dir=gate_dir)


# north band: ONE row sharing the estates' line (gates south onto the y=475 lane). The
# wall and ring slant hard across y~270-450 here (vertices at (1082,290)/(1718,290) with
# the ring 30 inside), and the NW diagonal road owns the band's west half - both ate the
# planned second row, so the band runs east of the karamete corridor's flanks only.
for _i, _x in enumerate((1250, 1760, 1830, 1900)):  # x1325 went to the N caravan yard; the band keeps its count on the east end (GM 2026-08-10)
    _yashiki(_x, 430, "south", _i + 3)
# east band: a west file on the band lane (starting BELOW the Temple of Bishamon's ground
# at (1928,531)), a south file flanking the lane's lower leg around the reserved Benten
# precinct (~x1785-1915, y1570-1670), and east-side compounds in the lineage-estate gaps
for _i, _y in enumerate((673, 751, 829, 907, 985, 1063, 1141, 1219)):  # x1918: 7px clear of Hazama's west wall (x1925 shared it)
    _yashiki(1918, _y, "east", _i)
for _i, _y in enumerate((1300, 1490, 1715)):
    _yashiki(1905, _y, "east", _i + 2)
for _i, _y in enumerate((1490, 1565)):
    _yashiki(2040, _y, "west", _i + 1)
for _i, _y in enumerate((628, 850, 1120, 1195)):  # 628: the file's head clears the resized ring and Hazama's court
    _yashiki(2075, _y, "west", _i + 2)
# west band: an east file facing the lane, plus west-side compounds in the estate gaps
# (the file's head stays clear of the Temple of Hotei at (764,615))
for _i, _y in enumerate((592, 666, 740, 814, 888, 962, 1036, 1110, 1184, 1258)):
    _yashiki(860, _y, "west", _i + 1)
for _i, _y in enumerate((850, 1090, 1165, 1240, 1315, 1420)):  # the y=595 head slot died on the ring corridor + the Temple of Hotei
    _yashiki(700, _y, "east", _i + 4)
# the ote flanks: senior households as near the government band as the standoffs allow -
# a west file on its own lane, and a north file whose gates open south onto the threaded
# y=1390 street between Kurogi's walls and the Imperial Magistracy
for _i, _y in enumerate((1330, 1405, 1480)):
    _yashiki(1255, _y, "west", _i + 1)
for _i, _x in enumerate((1600, 1680)):  # x=1780 died on the x=1800 street
    _yashiki(_x, 1330, "south", _i + 2)

# ---- T009: RETAINER TERRACES (79 units target; 10 ranges of 8). The kumi-yashiki go where
# junior samurai serve: flanking the karamete approach (the castle guard), and inside each
# working gate (the gate watch). Placed BEFORE the machi packs so the rows flow around them.
s.district("karamete terraces", "terrace", [(1340, 290), (1460, 290), (1460, 440), (1340, 440)], rank_band="terrace")
for _ty in (352, 420):  # the left file starts lower - the NW diagonal road passes y~308 here
    s.terrace(1372, _ty, units=8, rot=90)
for _ty in (334, 399):
    s.terrace(1428, _ty, units=8, rot=90)
s.district("east gate terraces", "terrace", [(2225, 1130), (2290, 1130), (2290, 1270), (2225, 1270)], rank_band="terrace")
s.terrace(2255, 1148, units=8)
s.terrace(2255, 1252, units=8)
s.district("south gate terraces", "terrace", [(1325, 2050), (1475, 2050), (1475, 2120), (1325, 2120)], rank_band="terrace")
s.terrace(1352, 2085, units=8, rot=90)
s.terrace(1448, 2085, units=8, rot=90)
s.district("southwest gate terraces", "terrace", [(730, 1800), (790, 1800), (790, 1855), (730, 1855)], rank_band="terrace")
s.terrace(762, 1828, units=8, rot=90)  # vertical ranges: the only window between the x=740 alley and the x=800 street
s.terrace(775, 1828, units=8, rot=90)

# alleys BEFORE the packs (each reserves its corridor; no block core sits >95px from a way)
s.alley([(640, 1375), (640, 1552)])  # the D5/west mid-band pocket (x=640: clear of the (700,1420) compound)
# the east gate ward (its road runs ~y1170)
s.alley([(2305, 2080), (2440, 1910)])  # the wharf's upstream bank boxes
# the east approach samurai seats
s.alley([(530, 770), (530, 1430)])  # the west rim's spine (early: wells must not seat on its line)
s.alley([(740, 1585), (740, 1880)])  # stops short of the SW terrace window
s.alley([(880, 1560), (880, 2005)])  # runs THROUGH to the y2005 street (it stopped 23px short)  # snapped: kagi road leg to the ring's SW curve
s.alley([(1180, 1560), (1180, 2095)])
s.alley([(1300, 1560), (1300, 2112)])
s.alley([(1565, 1390), (1565, 2103)])  # runs up past the kagi to serve the magistracy flank
s.alley([(1655, 1585), (1655, 2090)])  # east columns clear the hanko (x1415-1549) and the (1905,1715) compound
# x1690 alley dropped: it ran through the (1690,1935) brewery; x1655 and the x1800 street cover the cores
s.alley([(2000, 1585), (2000, 1938)])  # stops inside the wall's south curve
s.alley([(2200, 760), (2200, 1290)])
s.alley([(2290, 891), (2290, 1290)])  # both start below the NE wall's tower course
s.alley([(2260, 1290), (2260, 1590)])

# the machi + suburb DISTRICTS, declared before the mesh and the packs (kido_mesh and
# the band checks read them; a mesh run before the declarations bars nothing)
s.district("southwest machi", "machi", [(552, 1570), (1395, 1570), (1395, 2110), (552, 2110)], rank_band=None)
s.district("southeast machi", "machi", [(1405, 1575), (2120, 1575), (2120, 2110), (1405, 2110)], rank_band=None)
s.district("east gate machi", "machi", [(1940, 550), (2405, 550), (2405, 1310), (1940, 1310)], rank_band=None)
s.district("east street machi", "machi", [(2140, 1420), (2385, 1420), (2385, 1725), (2140, 1725)], rank_band=None)
s.district("west rim machi", "machi", [(430, 750), (590, 750), (590, 1445), (430, 1445)], rank_band=None)
s.district("Benten monzen", "monzen", [(1762, 1636), (1938, 1636), (1938, 1855), (1762, 1855)], rank_band=None)
s.district(
    "Jurojin monzen", "monzen", [(820, 1478), (1120, 1478), (1120, 1585), (820, 1585)], rank_band=None
)  # the lay quarter strings ALONG the kagi road both ways from the sando mouth (Jurojin rolled the full 7-arch avenue, so it commands a full monzen)

s.district("wharf suburb", "machi", [(2020, 1940), (2540, 1940), (2540, 2545), (2020, 2545)], rank_band=None)
s.district("south gate ward", "machi", [(1028, 2590), (1625, 2590), (1625, 3042), (1028, 3042)], rank_band=None)
s.district("east gate ward", "machi", [(2440, 770), (2945, 770), (2945, 1495), (2440, 1495)], rank_band=None)
s.district("towpath shore", "machi", [(1548, 2530), (2100, 2530), (2100, 2885), (1548, 2885)], rank_band=None)
s.district("northeast riverside", "machi", [(2440, 770), (2760, 770), (2760, 1180), (2440, 1180)], rank_band=None)
s.district("west approach", "machi", [(52, 1978), (368, 1978), (368, 2442), (52, 2442)], rank_band=None)
s.district("southwest road wing", "machi", [(52, 1978), (368, 1978), (368, 2442), (52, 2442)], rank_band=None)
s.district("north gate ward", "machi", [(775, -60), (1655, -60), (1655, 172), (775, 172)], rank_band=None)

# ---- private dojos (count rolled from the samurai cohort - the 1-per-200 formula holds
# at this tier; the hanko is the capital's gain, not more private halls) and the walled
# MERCHANT ESTATES of the counts table, both seated before the packs
s.dojos([(1230, 1650), (760, 1680), (2250, 1175), (1610, 1480), (1000, 1480), (2200, 1520), (700, 1600), (1750, 1950)])
for _dj in s.M.get("dojos", []):
    _djx, _djy = _dj["x"], _dj["y"]
    s.block_polys.append([(_djx - 40, _djy - 40), (_djx + 40, _djy - 40), (_djx + 40, _djy + 40), (_djx - 40, _djy + 40)])
    s.placed.append((_djx, _djy, 64, 64))  # a dojo compound reserves its ground before the packs (the engine glyph alone did not)
s.theater_stage(2062, 1712, w=66, h=48, label="theater", kind="machi", rot=127)  # the entertainment quarter beside the wharf gate (the brokers' money builds the theaters)
s.theater_stage(1740, 1695, w=64, h=46, rot=-120, label=None)  # opens toward the Benten hall (its temple)
s.district("entertainment quarter", "entertainment", [(2000, 1620), (2115, 1620), (2115, 1800), (2000, 1800)], rank_band=None)
# market-day flophouses at the working gates, seated BEFORE the packs (the first seats
# landed on the moat band and the Shiro Kyo roadbed once the suburbs grew around them)
s.flophouse(1290, 2560)  # far enough out that its caption clears the moat band (GM 2026-08-10)
s.flophouse(2700, 1310)  # on the E gate road's south verge, inside the market's own strip
s.flophouse(1325, 80)
s.merchant_estates([(1330, 1830, "east"), (950, 1700, "south"), (1550, 1950, "north"), (1080, 1768, "south"), (1240, 1898, "east"), (1188, 1816, "west"), (1650, 1700, "south"), (1120, 1930, "north")])
# ---- the TRADE WORKS + GATE CARAVAN PROGRAM (the urban battery's full demand; all
# compounds seated BEFORE the packs). Nuisance trades take the lee-and-downstream arc
# (wind_from="northwest"): the dyer and both tanneries stand on the moat DRAIN south of
# the wharf, the kiln smokes outside the southwest wall.
# monk housing beside each rim temple + the teramachi cluster's wayside shrines
s.rowpack((2028, 462, 2080, 508), ["monk_house"] * 2, court_every=3)  # Bishamon's adepts NE of the hall, against the ring verge's adepts NE of the hall, against the ring verge
s.rowpack((2174, 1939, 2216, 1995), ["monk_house"] * 2, court_every=3)  # tucked between Ebisu and the connector's kido crossing
s.rowpack((990, 2166, 1042, 2226), ["monk_house"] * 3, court_every=3)
s.rowpack((464, 1268, 505, 1313), ["monk_house"] * 2, court_every=3)
s.rowpack((641, 545, 685, 587), ["monk_house"] * 2, court_every=3)  # west of the Hotei hall, under the ring curve
s.small_shrine(547, 1395)
s.small_shrine(681, 1565)
s.small_shrine(862, 2008)
s.small_shrine(619, 1635)
s.small_shrine(479, 1095)
s.brewery(1130, 1700)
s.brewery(1690, 1935)
s.oil_press(1000, 1690)
s.pawnshop(1245, 1690)
s.pawnshop(1874, 1786)  # the second commercial quarter's pawnshop (Edo ran one per ~400 residents; two drawn, the rest implied in the rows)
s.bathhouses([(900, 1750), (1278, 1980), (1668, 1740), (2060, 1640), (1080, 1860), (1550, 1830), (2250, 1050)])
s.dye_yard(2114.8, 2493.8, rot=29.4)
s.dye_yard(2049.9, 2403.7, rot=108.9)  # ...the dyers' row (Konya-machi): contiguous lots up the drain's west bank
s.dye_yard(2051.4, 2458.0, rot=29.4)
s.tanning_yard(2000.3, 2491.2, rot=29.4, water="stream")  # ON the moat drain's west bank (its wash water; the towpath owns the river bank here) - GM 2026-08-10
s.tanning_yard(2060.1, 2524.9, rot=29.4, water="stream")  # the pair shares the drain's downstream bank
s.kiln(268, 2166)
s.kiln(
    176, 2196
)  # the second works of the kiln quarter - beside the first, sharing the pit and the fuel road  # ON the SW approach road's outer leg (a kiln hauls fuel and clay by cart, so it stands on its haul road, not adrift in the fields - GM 2026-08-10)
# the in-wall doss-house needs a HUMBLE quarter around it (>=115px merchant/temple-free,
# research: the doya-gai sat among day-laborer rows) - the 4-mix machi has a merchant
# everywhere, so carve a laborer-only pocket and seat the doss at its heart
s.placed.append((1153, 2284, 46, 334))  # hold the doss seat before the rows fill in
s.placed.append((1837, 1352, 34, 24))  # keep the SE pasture verge clear (a lone well-less seat kept landing here)
s.rowpack((1045, 1920, 1305, 2040), ["laborer_large"] * 4 + ["laborer"] * 26)
s.flophouse(1153, 2284)  # the in-wall doss-house, deep in the laborer core
s.flophouse(386, 2204)  # outside the SW gate
# caravan facilities just inside each gate: inn + big stables (open ground kept by their
# own reserves; the packs flow around)
s.inn(1330, 300)
# the N caravan yard: beside its inn but OFF every estate's gate approach (GM 2026-08-10).
# The band between the ring road and the estate row is corridor-bound, so the engine picks
# the best clear seat in the wider gate quarter and the inn/flophouse keep it company.
# the N caravan yard stands OUTSIDE the gate with the market it feeds (GM 2026-08-10: it was
# on the Nio/Seki estates' gate approach, and the in-wall band between ring road and estate
# row is corridor-bound). Caravans halt outside the gate anyway - that is where the toll,
# the flophouses and the fodder are - so the yard joins the guan-xiang strip.
# the N caravan yard stays INSIDE the gate (city_gate_caravan_facilities: the inn, stables and
# flophouse serve arriving traffic within the walls) but OFF every estate's gate approach - the
# north band's compounds all gate SOUTH onto the y475 lane, so the yard takes the band's west
# end, past Yodo, where no compound faces it (GM 2026-08-10)
_ESTATE_GATES = [(1150, 454), (1250, 453), (1520, 418), (1660, 412), (1760, 453), (1830, 454)]
_yardseat = s.open_seat((1430, 225, 1560, 330), 100, 96, footprint=False, clear_of=_ESTATE_GATES) or (1470, 262)
s.stables(_yardseat[0], _yardseat[1])
s.placed.append((_yardseat[0], _yardseat[1], 100, 96))  # the N caravan yard - beside its inn at (1330,300), off the estate gates (GM 2026-08-10)
s.well(_yardseat[0] + 46, _yardseat[1] - 40)  # the yard's own trough water, pre-seeded (the dig path predates placed-reserves)
s.block_polys.append([(1505, 308), (1615, 308), (1615, 416), (1505, 416)])
s.placed.append((1560, 362, 112, 32))  # N caravan yard (uniform doctrine: every gate stables keeps open ground)
s.inn(2437, 1413)
s.stables(2426, 1241)
s.block_polys.append([(2371, 1188), (2481, 1188), (2481, 1298), (2371, 1298)])
s.placed.append((2426, 1241, 196, 228))  # the caravan yard keeps OPEN ground for the animals
s.inn(1330, 2368)
s.stables(1512, 2392)
s.block_polys.append([(1415, 2314), (1525, 2314), (1525, 2422), (1415, 2422)])
s.placed.append((1470, 2368, 112, 418))  # S caravan yard: open ground for the animals (crowd rule)
s.well(1458, 2416)  # the yard's public well - pre-seeded so the stables' own-well dig path (which predates placed-reserves) stays idle
s.flophouse(1455, 300)
s.flophouse(2421, 1343)
s.flophouse(1370, 2341)
s.flophouse(586, 1856)  # INSIDE the SW gate with its inn and stables (city_gate_caravan_facilities); seat computed clear of wall, ring, road and every solid
s.inn(629, 1938)
s.stables(673, 1915)
s.well(700, 1940)  # pre-seeded: the yard's own-well dig path was putting one on the SW gate road
s.block_polys.append([(521, 1896), (631, 1896), (631, 2004), (521, 2004)])
s.placed.append((576, 1950, 46, 338))  # SW caravan yard (uniform doctrine)
s.street([(1850, 1688), (1850, 1852)], width=s.lw(10))  # the Benten sando's monzen lane (the hall faces its own lane - capitals.md)
s.street([(950, 1482), (950, 1560)], width=s.lw(10))  # the Jurojin sando's monzen lane
s.frontage([(950, 1492), (950, 1550)], ["shop"] * 4, width=6, spacing=26, setback=9)  # the sando's own stalls
s.frontage([(1850, 1700), (1850, 1845)], ["merchant", "shop"] * 5, width=8, spacing=16, setback=-26, jitter=1)  # Benten monzen, west of the sando - frontage orients each seat to the way
s.frontage([(1850, 1845), (1850, 1700)], ["shop", "merchant"] * 5, width=8, spacing=16, setback=-26, jitter=1)  # ...and east of it (the reversed run puts the file on the far side, still facing in)
s.rowpack((918, 1462, 946, 1560), ["merchant", "shop"] * 10, court_every=6)  # Jurojin monzen flanks its north sando
s.rowpack((954, 1462, 982, 1560), ["shop", "merchant"] * 10, court_every=6)

s.rowpack((2135, 1818, 2280, 1925), ["laborer", "servant", "merchant_house"] * 10, court_every=8)
s.rowpack((2285, 1565, 2430, 1700), ["laborer", "merchant_house"] * 12, court_every=8)


# THE CASTLE'S FIREBREAK RING, slim (the wall-settles-first pass, GM 2026-08-10): the
# umamawari is a kept CLEAR BAND around the citadel's moat - ~65px (195 ft) of bare ground -
# not a district-scale waste; with the settled wall the interior packs tight around it and
# the slack check holds the whole map to <= 15% open.
s.commons([(880, 545), (948, 545), (948, 1235), (880, 1235)], role="pasture", render="bare")
s.commons([(640, 730), (784, 730), (784, 1240), (640, 1240)], role="pasture", render="bare")
s.commons([(1345, 265), (1555, 265), (1555, 430), (1345, 430)], role="pasture", render="bare")
s.commons([(1852, 545), (1922, 545), (1922, 1245), (1852, 1245)], role="pasture", render="bare")
s.commons([(950, 452), (1850, 452), (1850, 512), (950, 512)], role="pasture", render="bare")
s.commons([(1240, 1266), (1560, 1266), (1560, 1352), (1240, 1352)], role="muster ground", render="bare")  # the ote front's hirokoji
s.commons([(1918, 1478), (2000, 1478), (2000, 1588), (1918, 1588)], role="festival ground", render="bare")  # Benten's east green
s.commons([(1900, 1590), (1985, 1590), (1985, 1700), (1900, 1700)], role="festival ground", render="bare")
s.commons([(318, 1100), (438, 1100), (438, 1560), (318, 1560)], role="pasture", render="bare")  # the west verge inside the wall's tightest arc

# the thread street's west run fronts the government quarter's forecourt apron, and the
# band street's west run faces the rampart approach - both CLAIMED open ground, not slack
s.commons([(1290, 1398), (1553, 1398), (1553, 1448), (1290, 1448)], render="bare")
s.commons([(1000, 2242), (1270, 2242), (1270, 2338), (1000, 2338)], render="bare")
s.commons([(1355, 2244), (1595, 2244), (1595, 2336), (1355, 2336)], render="bare")  # the S-gate approach: the column ground where the Imperial road crosses the band street
s.commons([(1130, 2150), (1240, 2150), (1240, 2242), (1130, 2242)], render="bare")  # the infill block's open court - the collision-circle waste never lets rows take it

# the N band's two open cores are the garrison's drill grounds - CLAIMED working
# ground (samurai band; the housing budget has no seats for them and the ground is real)
s.commons([(1138, 256), (1268, 256), (1268, 338), (1138, 338)], render="bare")
s.commons([(1505, 253), (1637, 253), (1637, 330), (1505, 330)], render="bare")
s.commons([(1090, 1300), (1195, 1300), (1195, 1390), (1090, 1390)], render="bare")  # the shrunk detached file's freed strip - moat-side firebreak ground
s.commons([(1815, 355), (1925, 355), (1925, 440), (1815, 440)], render="bare")
s.commons([(535, 635), (640, 635), (640, 725), (535, 725)], render="bare")
s.commons([(830, 470), (945, 470), (945, 560), (830, 560)], render="bare")
s.commons([(2052, 1662), (2150, 1662), (2150, 1750), (2052, 1750)], render="bare")
s.commons([(1640, 1250), (1732, 1250), (1732, 1332), (1640, 1332)], render="bare")

_mseat = s.open_seat((1240, 1420, 1720, 1560), 62, 46) or (1466, 1530)
s.mausoleum(_mseat[0], _mseat[1], 58, 42, label="Ancestral Mausoleum", gate_dir="south")

s.frontage([(1210, 2210), (1580, 2210)], ["shop", "merchant", "laborer"] * 5, width=8, spacing=25, setback=18, jitter=1)  # the band street's north face - it had 1,140 ft bare on both sides
s.frontage([(1580, 2262), (1210, 2262)], ["laborer", "servant", "merchant_house"] * 5, width=8, spacing=25, setback=18, jitter=1)  # ...and its south face

# ---- T016: the kido MESH, before the packs (each gate reserves its ground; the mouths
# derive from the declared districts + streets via the shared machi_mouths source)
# ---- T015: fire towers over the dense fabric, placed first so the rows flow around them
# (research 021 item 5: the 1723 mandate - per-machi hinomi at the capital count ~10-15)
for _fx, _fy in ((850, 1650), (1200, 1900), (1600, 1900), (1900, 1780), (2250, 900), (2274, 1536), (495, 1100), (2300, 1830), (940, 1990), (1265, 1662), (905, 2275), (553, 1710)):
    s.fire_tower(_fx, _fy, label=None)
s.alley([(2115, 640), (2255, 640)])  # east of the x2075 yashiki file; ends inside the ring (wall's east arc is x~2300 here)
s.alley([(2190.8, 568.9), (2200, 1235)])  # the deep E machi block's roji (before the wells, so the well grid dodges them)

# ---- T013/T014: the PUBLIC WELLS, before the packs so the rows ring their courts.
for _hw in (
    (2240, 758),
    (2260, 622),
    (2210, 706),
    (2168, 700),
):
    if any((_w8["x"] - _hw[0]) ** 2 + (_w8["y"] - _hw[1]) ** 2 <= 50 * 50 for _w8 in s.M.get("wells", [])):
        continue  # one wellhead per 150 ft neighborhood (GM 2026-08-10: knots of 4-6 read wrong)
    s.well(_hw[0], _hw[1])  # hand-seeded court wells for the pockets the grids kept missing

# The josui-ido band first: cistern-wells on the gate road within ~600 ft of the settling
# basin (research item 4); dug draw-wells serve everything else.
# the deep-file quarters (the E gate machi's long rows, the mid-south strip) carry the most
# households per wellhead, so they get a second, tighter gap-fill pass of their own
for _dq in ((2150, 660, 2400, 1200), (1050, 1830, 1400, 1960), (1650, 1830, 2060, 1990), (2090, 1830, 2180, 1960), (2150, 1450, 2380, 1660)):
    for _dx in range(int(_dq[0]), int(_dq[2]), 40):
        for _dy in range(int(_dq[1]), int(_dq[3]), 40):
            if any((_w["x"] - _dx) ** 2 + (_w["y"] - _dy) ** 2 <= 70 * 70 for _w in s.M.get("wells", [])):
                continue
            _dseat = s.open_seat((_dx - 22, _dy - 22, _dx + 22, _dy + 22), 9, 9, well=True)
            if _dseat and sum(1 for _w in s.M.get("wells", []) if (_w["x"] - _dseat[0]) ** 2 + (_w["y"] - _dseat[1]) ** 2 <= 50 * 50) < 3:
                s.well(_dseat[0], _dseat[1])

s.place_wells(
    (2250, 1350, 2400, 1425), spacing=74, kind="cistern", coverage=False
)  # the josui-ido file inside the E gate, on the buried main from the new settling basin (laterals under the roji, research item 4)
# WELL GRIDS ARE DERIVED, NOT HAND-TUNED (GM 2026-08-10: 27 hand boxes, many overlapping,
# had knotted 4-7 wellheads together in several quarters). For each machi QUARTER we split
# its bbox at the streets and alleys that actually cross it and lay one grid per resulting
# BLOCK, inset off the beds - so wells sit in block interiors by construction, no two grids
# cover the same ground, and re-flowing a street moves the wells with it.
s.street([(1040, 2238.1), (2005.3, 2234.1)], width=s.lw(15))
# ways declared LATE (the machi roji) are hoisted here: the well grids read the way
# list at the moment they run, so an alley drawn after them cannot be dodged (GM
# 2026-08-10: wells sat on the S band roji for exactly this reason)
s.alley([(1741, 256), (1738, 348)])
s.alley([(535, 1470), (535, 1975)])  # the crescent's spine
s.alley([(500, 1767), (620, 1760)])
s.alley([(880, 2005), (879, 2274)])  # starts ON the y2005 street
s.alley([(1560, 2005), (1560, 2236)])
s.alley([(1760, 2005), (1766, 2235)])
s.alley([(1990, 1875), (1990, 2140)])
s.alley([(1900, 2008), (2100, 2008)])
s.alley([(1850, 2555), (2062, 2420)])  # the shore path serving the towpath-side porters' rows
s.alley([(1672, 2460), (1728, 2760)])  # the shore rows' spine (before its packs)


def _well_blocks(x0, y0, x1, y1, spacing, inset=30):
    """Lay one well grid per BLOCK: take the quarter's bbox, cut out the bands the streets and
    alleys crossing it occupy (bed half-width + inset), and grid each surviving rectangle."""

    def _free(lo, hi, bands):
        out, cur = [], lo
        for b0, b1 in sorted(bands):
            if b1 <= cur:
                continue
            if b0 > cur:
                out.append((cur, min(b0, hi)))
            cur = max(cur, b1)
            if cur >= hi:
                break
        if cur < hi:
            out.append((cur, hi))
        return [(a, b) for a, b in out if b - a >= 40]

    xb, yb = [], []
    for _w in s.M.get("town_streets", []) + s.M.get("alleys", []):
        _pts = _w["pts"]
        _hw = _w.get("w", 12) / 2 + inset
        for _i in range(len(_pts) - 1):
            (ax, ay), (bx, by) = _pts[_i], _pts[_i + 1]
            if abs(ax - bx) < 6 and x0 < ax < x1 and min(ay, by) < y1 and max(ay, by) > y0:
                xb.append((ax - _hw, ax + _hw))
            elif abs(ay - by) < 6 and y0 < ay < y1 and min(ax, bx) < x1 and max(ax, bx) > x0:
                yb.append((ay - _hw, ay + _hw))
            elif max(ax, bx) > x0 and min(ax, bx) < x1 and max(ay, by) > y0 and min(ay, by) < y1:
                # an OBLIQUE way (the shore paths, the diagonal roji): cut its whole span on
                # the axis it travels least, so no grid cell straddles its bed
                if abs(ax - bx) < abs(ay - by):
                    xb.append((min(ax, bx) - _hw, max(ax, bx) + _hw))
                else:
                    yb.append((min(ay, by) - _hw, max(ay, by) + _hw))
    for bx0, bx1 in _free(x0, x1, xb):
        for by0, by1 in _free(y0, y1, yb):
            # ONE wellhead per grid CELL, sited by the engine (open_seat consults _fits, so it
            # will not stand on a lane, a corridor or a roof the way a raw grid seat can), and
            # only where no well already serves that 150 ft neighborhood
            nx = max(1, int((bx1 - bx0) // spacing))
            ny = max(1, int((by1 - by0) // spacing))
            for _cx in range(nx):
                for _cy in range(ny):
                    cell = (
                        bx0 + (bx1 - bx0) * _cx / nx,
                        by0 + (by1 - by0) * _cy / ny,
                        bx0 + (bx1 - bx0) * (_cx + 1) / nx,
                        by0 + (by1 - by0) * (_cy + 1) / ny,
                    )
                    seat = s.open_seat(cell, 9, 9, well=True)
                    # the cluster rule allows up to FOUR wellheads inside a 150 ft radius; test
                    # the SEAT, not the cell center, or a dense quarter's cells all seat toward
                    # one corner and knot anyway (GM 2026-08-10)
                    if seat and sum(1 for _w in s.M.get("wells", []) if (_w["x"] - seat[0]) ** 2 + (_w["y"] - seat[1]) ** 2 <= 50 * 50) < 3:
                        s.well(seat[0], seat[1])


_WELL_QUARTERS = (
    # (x0, y0, x1, y1, cell) - DISJOINT quarters, cell sized so each wellhead serves ~15-20
    # households at that quarter's row density (machi ~1.15 dwellings/kpx2 -> ~96px cells;
    # the burakumin rows and doss pocket run court_every=3, roughly double, so ~68px).
    # Spacings are set from that arithmetic, never by nudging a multiplier (GM 2026-08-10).
    (615, 1575, 1395, 1830, 58),  # SW machi
    (615, 1830, 1395, 2040, 50),  # ...its southern burakumin/doss strip: ~2x the row density
    (1405, 1575, 2120, 1840, 58),  # SE machi
    (1405, 1840, 2120, 2040, 50),  # ...and its own dense southern strip
    (790, 2100, 1995, 2345, 50),  # the S band machi
    (2145, 635, 2405, 1250, 46),  # the E gate machi
    (2140, 1440, 2320, 1640, 60),  # the E street machi
    (430, 750, 590, 1445, 60),  # the W rim machi
    (445, 1450, 610, 2075, 60),  # the W crescent machi
    (1090, 1265, 1365, 1520, 63),  # the SW approach machi
    (1575, 1300, 1836, 1440, 63),  # the thread machi
    (2000, 1620, 2115, 1800, 60),  # the entertainment quarter
    (1762, 1636, 1938, 1855, 63),  # Benten's monzen
    (960, 1478, 1120, 1585, 63),  # Jurojin's monzen (east of the civic band)
    (1840, 1300, 1990, 1440, 60),  # the thread machi's east files
    (1900, 545, 1986, 640, 46),  # the N band's servant rows
    (395, 525, 482, 608, 48),  # the NW monk-house court
)
for _q in _WELL_QUARTERS:
    _well_blocks(*_q)


def _point_in(px, py, poly):
    inside = False
    for _i in range(len(poly)):
        x1, y1 = poly[_i]
        x2, y2 = poly[(_i + 1) % len(poly)]
        if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


# COVERAGE GAP-FILL: the per-quarter cells leave holes where a block's grid could not seat
# (a court, a fence corridor, a temple apron), and those holes are what leave one wellhead
# doing three blocks' work. Walk the machi ground on a lattice and seat a well wherever the
# nearest one is more than ~110px off, honoring the same 4-per-150ft ceiling.
for _gx in range(440, 2400, 42):
    for _gy in range(520, 2350, 42):
        if not any(_q2[0] <= _gx <= _q2[2] and _q2[1] <= _gy <= _q2[3] for _q2 in _WELL_QUARTERS):
            continue
        if any((_w["x"] - _gx) ** 2 + (_w["y"] - _gy) ** 2 <= 78 * 78 for _w in s.M.get("wells", [])):
            continue
        if any(  # never inside a samurai/civic district - that quarter draws from its own compound wells
            _d2.get("rank_band") in ("yashiki", "detached", "terrace") or _d2.get("kind") in ("yashiki", "detached", "terrace", "civic", "government")
            for _d2 in s.M.get("districts", [])
            if _point_in(_gx, _gy, _d2["poly"])
        ):
            continue
        _gseat = s.open_seat((_gx - 26, _gy - 26, _gx + 26, _gy + 26), 9, 9, well=True)
        if _gseat and sum(1 for _w in s.M.get("wells", []) if (_w["x"] - _gseat[0]) ** 2 + (_w["y"] - _gseat[1]) ** 2 <= 50 * 50) < 3:
            s.well(_gseat[0], _gseat[1])

# ---- T008: DETACHED SAMURAI (133 target) - the middle band, rowpacked at the loose samurai
# court pitch (the Tango idiom, which is what C_SPACED was measured from).
_SAM = ["samurai"] * 4 + ["samurai_large"]
s.district("moat-south detached band", "detached", [(615, 1268), (1145, 1268), (1145, 1392), (615, 1392)], rank_band="detached")
s.rowpack((620, 1275, 1140, 1362), _SAM * 15, court_every=8)
s.rowpack((1150, 1275, 1240, 1362), _SAM * 4, court_every=8)
s.rowpack((1470, 285, 1730, 415), _SAM * 12, court_every=8)  # the karamete-east shelf inside the ring curve
s.rowpack((900, 348, 1072, 386), _SAM * 5, court_every=8)  # the NW shelf between the ring and the diagonal road
s.district("magistracy detached flank", "detached", [(1555, 1290), (1865, 1290), (1865, 1560), (1555, 1560)], rank_band="detached")
s.rowpack((1560, 1408, 1660, 1555), _SAM * 4, court_every=8)
s.rowpack((1808, 1408, 1852, 1555), _SAM * 2, court_every=8)
s.district("west detached pocket", "detached", [(470, 1400), (790, 1400), (790, 1745), (470, 1745)], rank_band="detached")
s.district("civic west detached", "detached", [(855, 1400), (1145, 1400), (1145, 1560), (855, 1560)], rank_band="detached")
s.district("east street detached", "detached", [(2140, 1250), (2445, 1250), (2445, 1428), (2140, 1428)], rank_band="detached")
s.district("north band detached west", "detached", [(1060, 260), (1340, 260), (1340, 370), (1060, 370)], rank_band="detached")
s.district("north band detached east", "detached", [(1640, 260), (1840, 260), (1840, 362), (1640, 362)], rank_band="detached")
s.rowpack((1062, 266, 1335, 368), _SAM * 10, court_every=8)
s.rowpack((1852, 266, 1962, 372), _SAM * 8, court_every=8)
s.rowpack((930, 452, 1075, 548), _SAM * 8, court_every=8)  # officials' houses on the karamete's west shelf
s.rowpack((700, 430, 830, 520), _SAM * 6, court_every=8)  # ...and its west neighbor
s.rowpack(
    (1770, 520, 1910, 610), _SAM * 6, court_every=8
)  # the Bishamon ward's officials' file  # the N band's east shelf: officials' houses, in no rank district  # the tight wall's N band holes take the missing detached files
s.rowpack((1688, 268, 1832, 352), _SAM * 4, court_every=8)
s.district("west crescent machi", "machi", [(445, 1450), (625, 1450), (625, 2075), (445, 2075)], rank_band=None)
s.block_polys.append([(592, 1738), (662, 1738), (662, 1818), (592, 1818)])
s.placed.append((627, 1778, 70, 80))  # the crescent kido's crossing (reserved before the rows)
s.rowpack((450, 1460, 620, 2070), ["laborer", "servant", "merchant_house", "laborer"] * 42, court_every=8)
s.district("south band machi", "machi", [(790, 2050), (1995, 2050), (1995, 2345), (790, 2345)], rank_band=None)
s.block_polys.append([(895, 2245), (990, 2245), (990, 2340), (895, 2340)])  # Inari's backstrip stays lean (the temple rode the wall inward)


s.block_polys.append([(815, 2237), (2020, 2237), (2020, 2264), (815, 2264)])  # the band street's own corridor, held against the row pitch  # the band's own through-street

s.rowpack((800, 2100, 1330, 2320), ["laborer", "servant", "merchant_house", "laborer"] * 112, court_every=11)
s.rowpack((1350, 2100, 1985, 2320), ["laborer", "servant", "merchant_house", "laborer"] * 88, court_every=11)
s.rowpack((1060, 1270, 1360, 1515), ["laborer", "servant", "merchant_house"] * 34, court_every=10)  # the freed SW approach ground joins the machi
s.district("southwest approach machi", "machi", [(1055, 1265), (1365, 1265), (1365, 1520), (1055, 1520)], rank_band=None)
s.district("thread machi", "machi", [(1575, 1295), (1905, 1295), (1905, 1440), (1575, 1440)], rank_band=None)
s.rowpack((1590, 1402, 1858, 1438), ["merchant_house", "laborer"] * 12, court_every=8)  # the households behind the thread frontage (ends clear of the 1905 kido's reserve)
s.rowpack((1580, 1300, 1900, 1438), ["laborer", "servant", "merchant_house"] * 44, court_every=8)
s.frontage([(1595, 1390), (2130, 1390)], ["merchant", "shop"] * 13, width=8, spacing=21, setback=14)  # the thread street's own commerce
s.rowpack((1552, 1448, 1700, 1558), _SAM * 11, court_every=8)  # the magistracy flank keeps its detached files
s.district("east rim detached", "detached", [(2245, 1660), (2405, 1660), (2405, 1800), (2245, 1800)], rank_band="detached")
s.rowpack((2250, 1665, 2335, 1795), _SAM * 4, court_every=8)
s.rowpack((1565, 1300, 1660, 1435), _SAM * 6, court_every=8)  # the S band's cleared ground inside the new arc
s.rowpack((628, 1326, 772, 1362), _SAM * 3, court_every=8)
s.rowpack((628, 1390, 772, 1424), _SAM * 3, court_every=8)
s.rowpack((604, 1406, 790, 1556), _SAM * 8, court_every=8)
s.rowpack((475, 1440, 595, 1740), _SAM * 7, court_every=8)
s.rowpack((860, 1408, 1140, 1462), _SAM * 8, court_every=8)  # ends above the Jurojin monzen (021)
s.rowpack((652, 1302, 1040, 1386), _SAM * 16, court_every=8)  # the moat-south detached band fills its declared ground
s.rowpack((1188, 1596, 1224, 1714), _SAM * 3, court_every=8)  # the dojo's own file (a hall stands among the samurai it serves)
s.rowpack((2145, 1255, 2420, 1415), _SAM * 17, court_every=8)
s.rowpack((1860, 470, 1950, 650), _SAM * 7, court_every=8)  # the moat-corner pocket (east of the moat, west of the band lane)

s.bound = [list(p) for p in RING]  # HARD RESTORE: a ward block above lost its bound restore once, and every later pack silently clipped to that stale box ('UNVISITED' ground)

# ---- T010: THE COMMONER MACHI (2,160 packed target: 960 laborer / 480 servant / 600
# merchant / 120 burakumin). Burakumin strips seat FIRST at the settlement edge (the two
# in-wall quarters of the counts table); the big machi packs then flow around them and
# around every standing compound, temple, precinct reservation and street.
s.district("southwest machi", "machi", [(615, 1575), (1395, 1575), (1395, 2110), (615, 2110)], rank_band=None)
s.district("southeast machi", "machi", [(1405, 1575), (2120, 1575), (2120, 2110), (1405, 2110)], rank_band=None)
s.district("east gate machi", "machi", [(2145, 635), (2405, 635), (2405, 1310), (2145, 1310)], rank_band=None)
s.district("east street machi", "machi", [(2140, 1420), (2440, 1420), (2440, 1660), (2140, 1660)], rank_band=None)
s.block_polys.append([(2082, 1732), (2158, 1732), (2158, 1810), (2082, 1810)])
s.placed.append((2120, 1770, 82, 80))
s.block_polys.append([(2145, 1687), (2220, 1687), (2220, 1764), (2145, 1764)])
s.placed.append((2182, 1725, 80, 78))  # SE kido crossings held BEFORE every machi pack (order, not coordinates, was the bug)
s.district("west rim machi", "machi", [(430, 750), (590, 750), (590, 1445), (430, 1445)], rank_band=None)
s.frontage([(1400, 1600), (1400, 2090)], ["merchant", "shop"] * 16, width=8, spacing=22, setback=14)  # the Imperial road's in-machi commerce
s.frontage([(830, 1560), (1350, 1560)], ["merchant", "shop"] * 10, width=8, spacing=22, setback=14)  # the kagi leg
s.frontage([(620, 1770), (1355, 1770)], ["merchant", "merchant", "shop"] * 13, width=8, spacing=20, setback=14)
s.frontage([(1455, 1770), (2085, 1770)], ["merchant", "merchant", "shop"] * 12, width=8, spacing=20, setback=14)  # gap at the x=1405 kido mouth
s.frontage([(990, 2005), (1085, 2005)], ["merchant", "shop"] * 3, width=8, spacing=20, setback=14)
s.frontage([(1290, 2005), (1355, 2005)], ["shop"] * 3, width=8, spacing=20, setback=14)  # split around the doss pocket's face - no fancy shopfronts against the humble quarter
s.frontage([(1455, 2005), (1795, 2005)], ["merchant", "shop"] * 8, width=8, spacing=20, setback=14)
s.frontage([(1040, 1640), (1040, 2070)], ["merchant"] * 12, width=8, spacing=21, setback=14)  # starts below the x=1040 machi mouth
s.frontage([(1800, 1710), (1800, 2050)], ["merchant"] * 10, width=8, spacing=21, setback=14)
s.rowpack((775, 1838, 1020, 2016), (["burakumin"] * 5 + ["servant"] * 4) * 20, court_every=3)
s.rowpack((1792, 1848, 1995, 2016), (["burakumin"] * 5 + ["servant"] * 4) * 22, court_every=3)
# T011 first: the adept-monk houses by the two sovereign precincts (budget: 2.5/precinct) -
# seated BEFORE the big packs so the precinct-adjacent ground is theirs
s.rowpack((1700, 1585, 1780, 1660), ["monk_house"] * 3, court_every=3)
s.rowpack((1020, 1585, 1100, 1660), ["monk_house"] * 2, court_every=3)
_MIX = ["laborer", "laborer", "servant", "merchant_house"]  # lean interior mix; the wealth minority packs its own rows (a diluted mix cost ~180 families of ground)
_RICH = ["laborer_large", "laborer_large", "merchant_large"]
s.rowpack((640, 1600, 1080, 1660), _RICH * 14, court_every=6)  # the wealth rows front the machi's north streets
s.rowpack((1440, 1600, 1900, 1660), _RICH * 14, court_every=6)
s.rowpack((640, 1690, 1020, 1740), ["laborer_large"] * 24, court_every=6)
s.rowpack((2160, 940, 2390, 1000), ["laborer_large"] * 24, court_every=6)
s.rowpack((1440, 1690, 1900, 1740), ["laborer_large"] * 24, court_every=6)
s.rowpack((560, 1580, 1385, 2062), _MIX * 400, court_every=12)
s.rowpack((1415, 1580, 1930, 2062), _MIX * 330, court_every=12)
s.rowpack((1080, 2100, 1290, 2240), _MIX * 40, court_every=9)  # the S-band dead-core infill (021 endgame)
s.rowpack((2000, 1580, 2115, 2085), (["laborer", "laborer_large", "servant"]) * 28, court_every=6)  # the SE-east strip carries a wealth band (labL toward the 6% floor)
s.rowpack((1950, 560, 1978, 1310), ["laborer", "merchant_house"] * 40, court_every=6)
s.rowpack((2002, 560, 2430, 1310), (["laborer", "merchant_house"]) * 400, court_every=6)
s.rowpack((2145, 1425, 2330, 1615), _MIX * 26, court_every=6)
s.rowpack((2150, 1625, 2255, 1715), _MIX * 8, court_every=6)
s.rowpack((1740, 1295, 1852, 1385), _MIX * 8, court_every=6)
s.rowpack((432, 755, 512, 1155), _MIX * 22, court_every=6)
s.rowpack((440, 1250, 510, 1445), _MIX * 9, court_every=6)  # resumes south of the Temple of Daikoku (501,1200)
s.rowpack((550, 760, 598, 1445), _MIX * 18, court_every=6)


# 021 endgame: the last density pockets get their wells AFTER the packs, seated by the
# engine among the drawn courts (open_seat sees the court lanes and standing rows; the
# pre-pack grids tried first kept landing wells on the packs' own court lanes)
# ---- the SUBURBS (021): a capital houses part of its packed cohort OUTSIDE the wall - the
# kashi wharf suburb (its brokers and warehouse folk live at the landing) and the guan-xiang
# gate wards on the approach roads, both the lawful outside categories the commoner rule
# names. The packs honor s.bound, so each suburb temporarily owns its own bound box.
_CITY_BOUND2 = s.bound
# the wharf suburb: bank-aligned boxes between the MOAT's outer edge and the river, stepping
# down the diagonal shore with the broker street (the first cut boxed the whole quay and
# packed rows onto the moat band)
s.bound = [[2020, 1950], [2520, 1950], [2520, 2530], [2020, 2530]]
s.rowpack((2338, 2010, 2410, 2090), ["merchant_house", "laborer", "laborer"] * 5, court_every=3)
s.rowpack((2276, 2110, 2346, 2190), ["merchant_house", "laborer", "laborer"] * 5, court_every=3)
s.rowpack((2205, 2205, 2280, 2285), ["merchant_house", "laborer"] * 6, court_every=3)
s.rowpack((2135, 2300, 2225, 2372), ["laborer", "servant"] * 3, court_every=3)
s.rowpack((2092, 2400, 2152, 2467), ["laborer", "servant"] * 4, court_every=3)
# the TOWPATH SHORE (the haulage side of the wharf): porters' and boatmen's rows on the
# land between the wall's south arc and the river, within the wharf's own reach
s.bound = [[1560, 2540], [1810, 2540], [1810, 2880], [1560, 2880]]
s.rowpack((1580, 2560, 1790, 2740), ["laborer", "laborer", "servant"] * 9, court_every=6)
s.bound = [[1820, 2450], [2100, 2450], [2100, 2810], [1820, 2810]]
s.cemetery(1780, 2708, 84, 60, parish=False, label="common burial ground")
# THE FULL FUNERARY GEOGRAPHY (GM 2026-08-10: "I don't see a cremation ground or pauper's
# burial mound at all... I also don't see a mausoleum"). The whole funerary block was gated on
# scale in (village, town, city) and the capital tier skipped it - a city of 12,400 with no
# crematory, no ossuary and no clan crypt. Sited by the same doctrine the provincial cities
# follow: the crematory OUTSIDE the walls beyond a gate (smoke and pollution), the pauper
# ossuary beside it, both by the common burial ground on the way out; the clan's ancestral
# mausoleum INSIDE, by the government quarter, a walled crypt precinct.
s.cremation_ground(1848, 2790)
s.ossuary(1770, 2828)
s.rowpack((1850, 2492, 2024, 2740), ["laborer", "servant"] * 12, court_every=6)
# the gate wards, each hugging its approach road inside the guan-xiang reach
s.placed.append((1204, 2561, 22, 18))
s.placed.append((1204, 2585, 22, 18))
s.bound = [[1195, 2546], [1770, 2546], [1770, 2981], [1195, 2981]]
# (the x1205-1295 head block stays open: the relay yard takes it)
s.bound = [[2565, 1113], [3015, 1113], [3015, 1273], [2565, 1273]]
s.bound = [[2535, 753], [2815, 753], [2815, 1113], [2535, 1113]]

s.bound = [[1225, 53], [1430, 53], [1430, 135], [1225, 135]]
s.placed.append((1017, 115, 107, -9))
s.placed.append((1033, 63, 107, -9))  # the N market's scan-seated shops hold their ground before the ward rows
s.bound = [[860, 60], [1360, 60], [1360, 210], [860, 210]]
s.bound = [[1410, 35], [1810, 35], [1810, 160], [1410, 160]]
s.bound = [[895, 0], [1170, 182], [1170, 182], [895, 0]]
s.bound = [[895, 0], [1170, 0], [1170, 182], [895, 182]]
s.bound = [[250, 2180], [450, 2180], [450, 2310], [250, 2310]]
_SWB = s.bound
s.bound = [[220, 1990], [505, 1990], [505, 2430], [220, 2430]]
_MKB = s.bound
_MKB = s.bound
s.bound = [[280, 1830], [700, 1830], [700, 2210], [280, 2210]]
s.frontage([(650, 1885), (502, 1989), (320, 2105)], ["shop"] * 9, width=8, spacing=26, setback=20, jitter=1)  # SW gate market, on the road itself
s.bound = [[1310, 2470], [1490, 2470], [1490, 2860], [1310, 2860]]
s.frontage([(1400, 2487), (1400, 2830)], ["shop"] * 13, width=8, spacing=24, setback=20, jitter=1)  # S gate market, down the Imperial road
s.bound = [[830, 40], [1420, 40], [1420, 215], [830, 215]]  # the box must reach the GATE (x1400) or the strip's head is refused - the market has to start at the mouth (GM 2026-08-10)
s.frontage([(1400, 120), (1200, 92), (1000, 116)], ["shop"] * 13, width=8, spacing=24, setback=16, jitter=1)
s.frontage(
    [(1030, 150), (1210, 128), (1390, 152)], ["shop", "merchant"] * 7, width=8, spacing=22, setback=16, jitter=1
)  # the strip's inner file, between road and moat bank  # N gate market: the strip STARTS at the gate mouth and runs west along the road (GM 2026-08-10)
s.bound = [[2430, 1200], [2830, 1200], [2830, 1400], [2430, 1400]]
s.frontage([(2545, 1306), (2800, 1247)], ["shop"] * 9, width=8, spacing=32, setback=20, jitter=1)  # E gate market on the Fox-lands road
s.bound = _MKB
s.bound = _SWB  # guan-xiang shops strung along the SW approach road
s.bound = [[119, 1687], [391, 1687], [391, 2237], [119, 2237]]
s.bound = [[421, 2087], [766, 2087], [766, 2282], [421, 2282]]
s.bound = [[886, 2337], [1291, 2337], [1291, 2497], [886, 2497]]
s.bound = _CITY_BOUND2


# the suburbs are DISTRICTS like any fabric (the band-target check counts by district)

# ---- the OUT-WALL SAMURAI (the budget's other 47: CAPITAL_SAMURAI_INWALL_FRAC leaves 15%
# of the cohort in country seats on the approaches - the Tango out-wall precedent; they
# count in the census but belong to NO rank district, so the in-wall band targets stand)
# A COUNTRY SEAT IS A WALLED COMPOUND, NOT A ROW (GM 2026-08-10, and the settlement-review
# said the same of the first pass): the budget's out-wall samurai are landed retainers on the
# approaches, so they take walled estates with their own ground - the machi-form rowpacks that
# stood here read as suburb tenements with samurai labels, and left 24 free-standing samurai
# houses outside the walls where city_samurai_houses_inside_walls rightly wants none.
_CB3 = s.bound
# ...and they stand on the NORTHWEST approach, the road to Otosan Uchi: an out-wall estate
# faces the capital (city_estates_toward_capital), and the three vary in size the way three
# lineages' seats would. Seats computed clear of wall, moat, roads and every standing solid.
s.bound = [[120, 60], [700, 60], [700, 520], [120, 520]]
s.manor(260, 140, 118, 92, None, gate_dir="east")
s.manor(200, 360, 96, 74, None, gate_dir="east")
s.manor(460, 240, 78, 62, None, gate_dir="south")
s.bound = _CB3


# ---- the market-day flophouses at the working gates (outside, by the gate markets) and
# the merchant kura attached behind the shopfronts (counts table ~20)
# ---- T023: the RELAY (tenma) STABLES + FARRIER at the south gate market - the Imperial
# road's post service, largest class (a domain capital is a first-rank relay stop); iron
# shoeing per canon (the Imperial relay puts institutional demand on the forge)
s.stables(1248, 2320, rot=0)
s.farrier(1185, 2272, rot=0)
s.merchant_storehouses(count=20)

# ---- declared quarters (feature 020 re-zone): the CIVIC quarter is the ground the government
# actually occupies - the ote-suji band south of the ote-mon, ministries to chancellery - not a
# wedge picked before the castle was placed. The four interior wedges split at the kagi-no-te
# junction, where the avenue meets the through-road, and carry no zone stronger than "mixed"
# until feature 021 packs them. Quarters are declarative overlays, so the civic band riding over
# the wedge seams is intentional.
# 021 re-zone: a capital's quarters follow its FABRIC, not compass wedges - the old wedges
# averaged the castle moat into machi density and could never read right. Zones "castle"
# and "samurai" are exempt from the residential density body by the checks' own zone
# filter (senior compounds at C_YASHIKI are ~0.24 dwellings/1000px^2, legitimately under
# the machi floor); the south "mixed" wedge is where the density band bites.
s.quarter([(949, 504), (1851, 504), (1851, 1256), (949, 1256)], "castle")
s.quarter([(1057, 219), (1400, 163), (1743, 219), (2052, 383), (1851, 504), (949, 504)], "samurai")  # north band
s.quarter([(1851, 504), (2052, 383), (2246, 608), (2378, 904), (2510, 1313), (2378, 1496), (2160, 1390), (1855, 1390), (1851, 1256)], "samurai")  # east band + gate machi rim
s.quarter([(949, 504), (748, 383), (502, 637), (422, 904), (290, 1313), (422, 1496), (560, 1390), (1150, 1390), (1150, 1290), (949, 1256)], "samurai")  # west band
s.quarter([(1315, 1290), (1560, 1290), (1560, 1720), (1315, 1720)], "civic")  # the government band proper
s.quarter(
    [(422, 1496), (502, 1989), (748, 2243), (1057, 2407), (1400, 2463), (1743, 2407), (2052, 2243), (2246, 1792), (2378, 1496), (2160, 1390), (1150, 1390), (560, 1390)], "mixed"
)  # the machi south

# the wharf works and the aqueduct now anchor the frame's east; a modest uniform margin still
# shows each road running off the edge, and the south side carries the Imperial road caption,
# which finish() seats AFTER the crop and so cannot widen it itself. The EAST margin is wide on
# purpose: the aqueduct's intake works on the river (~x3140) are the part of the system a reader
# traces first (spec 020, User Story 3), and the default crop cut them - plus the east road's
# river bridge - clean off the sheet.
s.crop_city(
    margin=36
)  # ~110 real ft of edge (GM 2026-08-10: 400 ft of empty margin was too much)  # the south=240/east=700 overrides padded dead margin onto both flanks (GM 2026-08-10); the aggressive default frames the real content
s.title("Shiro Daika")
s.finish(os.path.splitext(os.path.abspath(__file__))[0].replace(".gen", ""), png_width=4600)
