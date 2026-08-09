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

s = Settlement(3200, 2700, seed=61)
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
    crop_outlier_ok="Outside the rampart the map carries only the gate furniture, the wharf works, the towpath and the aqueduct until feature 021 fills the interior; sparse outliers at this stage are the build order showing through, not a siting error.",
)

# ---- BUDGET-FIRST (feature 018): the wall is an OUTPUT of the declared program, never a guess.
# A capital cannot be sized from population the way a provincial city nearly can - a median castle
# alone is ~85% of an entire provincial city's interior.
BUDGET = plan_capital(CapitalProgram(population=12_360, river=True, castle_seat="ring", imperial_granary_seat="wharf"), canvas=(3200, 2700))
s.meta(budget=budget_to_manifest(BUDGET))

CX, CY = 1400, 1200
RX, RY = round(BUDGET.wall.rx), round(BUDGET.wall.ry)
NRING = 20
WALL = [(round(CX + RX * math.cos(-math.pi / 2 + 2 * math.pi * i / NRING)), round(CY + RY * math.sin(-math.pi / 2 + 2 * math.pi * i / NRING))) for i in range(NRING)]
NGATE, EGATE, SGATE, SWGATE = WALL[0], WALL[5], WALL[10], WALL[13]

# ---- the river: NE -> SW past the southeast flank, off both edges. Upstream (NE) first, which is
# the convention every junction-angle rule keys on.
# Held ~200px off the moat at its closest approach: the ring is 1,055x983 px of pushed-out wall,
# and the first cut ran the river straight through the southeast arc.
RIVER = [(3200, 700), (2900, 1150), (2500, 1750), (2100, 2300), (1800, 2700)]
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
    [(SGATE[0], 2700), (SGATE[0], SGATE[1]), (SGATE[0], KAGI_Y), (800, KAGI_Y), (800, 470), (1400, 300), (NGATE[0], NGATE[1]), (1400, 140), (1180, 55), (980, 0)],
    label="Imperial Road",
    label_xy=(SGATE[0] + 150, 2330),
)
# the same road is Imperial on BOTH sides of the city (GM 2026-08-09) - the run toward Shiro
# Kyo carries its own caption, tilted along the branch per the linear rule
s.label(1170, 66, "Imperial Road", 11, italic=True, color="#6E5B38", rot=195, linear=True)
s.road([(2397, 1200), (EGATE[0], EGATE[1]), (2820, 1130), (3200, 1040)])  # east, to the Fox lands - the first leg runs INSIDE the gate to join the ring road (gate_roads_join_the_ring)
# the karamete approach is the STRAIGHT CONTINUATION of the north gate's street (GM 2026-08-09:
# the first cut hung it off the diagonal mid-slope and the two beds read as overlapping roads):
# city gate -> due south -> the castle's rear gate, dead-ending at its moat and tower exactly as
# a castle-town street aimed at the works should, while the Imperial through-road leaves the
# street at the (1400, 300) junction and bends west around the castle front (the kagi-no-te).
s.road([(1400, 300), (1400, 520)])  # stops at the karamete tower's foot, as the ote-suji stops at the ote-mon's
s.road([(594, 1745), (SWGATE[0], SWGATE[1]), (300, 2010), (0, 2170)])  # southwest, into the domain - the first leg runs INSIDE the gate to join the ring road (gate_roads_join_the_ring)

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
s.castle(CX, 880, 850, 700, label="Shiro Daika", gate_dir="south", karamete_dir="north")

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
FEED_TAP = (3080, 843)  # the river's west bank - upstream of the city, downstream of the aqueduct intake
s.stream([FEED_TAP, (2870, 875), (2650, 880), (MOAT[4][0], MOAT[4][1])], frm={"kind": "river"}, to={"kind": "moat"}, width=s.px(66))
# the boards sit a few steps DOWN their channel runs, not at the junctions (GM 2026-08-09: at a
# junction the local water direction is ambiguous, so the correctly-across board read as a
# coincidentally axis-aligned bar; astride the clear run, across-the-channel explains itself)
s.sluice_gate(
    3050, 848, rot=math.degrees(math.atan2(875 - FEED_TAP[1], 2870 - FEED_TAP[0])) + 90, label="sluice gate", label_xy=(3040, 818), span=26
)  # the intake board - the frame spans BANK TO BANK (posts on the abutments, the operator walks the crossbeam)
DRAIN_OUT = (MOAT[8][0], MOAT[8][1])
s.stream([DRAIN_OUT, (2065, 2180), (2062, 2325)], frm={"kind": "moat"}, to={"kind": "river"}, width=s.px(66))
s.sluice_gate(
    2029.1, 2028.6, rot=math.degrees(math.atan2(2180 - DRAIN_OUT[1], 2065 - DRAIN_OUT[0])) + 90, label="sluice gate", label_xy=(2014, 2046), span=26
)  # the outfall board, bank to bank like the intake
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
s.aqueduct([(2983, 989), (2790, 1063), (2620, 1125), (2510, 1168)])
# the two ends carry the words the glyphs cannot (GM 2026-08-09): the river end is the INTAKE
# WEIR (the Hamura form - a barrier angled across part of the stream, shouldering water into
# the cut), and the gate end is the SETTLING BASIN, where silt drops before the buried mains
# All three aqueduct words share the duct's bearing and the same ~20px uphill offset from the
# channel line (GM 2026-08-09: the end labels were level while "aqueduct" lay along the cut).
s.label(2952, 979, "intake weir", 9, italic=True, color="#5E7A8A", rot=160, linear=True, full_tilt=True)
s.label(2531, 1139, "settling basin", 9, italic=True, color="#5E7A8A", rot=160, linear=True, full_tilt=True)
s.label(2725, 1066, "aqueduct", 10, italic=True, color="#5E7A8A", rot=160, linear=True, full_tilt=True)

# ---- THE TOWPATH (feature 020): on the wharf's own (west) bank, coming up from downstream -
# upstream haulage is the whole reason it exists - and ending at the wharf, no further.
# ...ending AT the quay by the downstream landing stage (GM 2026-08-09: the old end stopped
# short of the jetty and hugged the waterline, reading as a line that dissolves into the
# river), and LABELED - the haulage path cannot explain itself at fit zoom
s.towpath([(1774, 2681), (1924, 2481), (2074, 2281), (2216, 2103), (2292, 1990)])
s.label(2130, 2172, "towpath", 10, italic=True, color="#8A7050", rot=-53, linear=True, full_tilt=True)
s.bridge(
    2063, 2296, -53.1, 52, 4
)  # the towpath's plank over the drain - the OBLIQUE span (22px water / sin ~36 deg) plus a visible ~2px bank rest each side (a plank's short abutment, not a carried deck's LANDING_FT)
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


lineage_manor(2075, 700, 158, 122, "hazama", "west")
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
for _tpx, _tpy in ((1850, 1620), (950, 1620)):
    s.block_polys.append([(_tpx - 65, _tpy - 50), (_tpx + 65, _tpy - 50), (_tpx + 65, _tpy + 50), (_tpx - 65, _tpy + 50)])
    s.placed.append((_tpx, _tpy, 130, 100))


def rim_temple(idx: float, name: str) -> None:
    """A modest teramachi hall on the rampart's inner face, ~130px inside the wall ellipse -
    inside the ring road's patrol strip, spaced off the gates and the government axis. Each
    hall's torii approach marches INWARD, toward the city it serves - the rim faces the fabric,
    its back to the defenses."""
    a = -math.pi / 2 + 2 * math.pi * idx / NRING
    tx, ty = round(CX + (RX - 130) * math.cos(a)), round(CY + (RY - 130) * math.sin(a))
    ux, uy = -math.cos(a), -math.sin(a)
    s.shrine_hall(tx, ty, name, w=s.px(96), h=s.px(64), kind="temple", torii=[(tx + ux * 45, ty + uy * 45), (tx + ux * 95, ty + uy * 95)])


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
s.jetty(2384, 1875, rot=36, length=13)  # the domain row's upstream stage
s.jetty(2302, 1982, rot=36, length=13)  # ...and its downstream one, just past the row's end
# the Emperor's complex gets its OWN landing (GM 2026-08-09: its grain moves by boat - that is
# the whole reason imperial_granary_seat="wharf" - so it does not borrow the domain quay 200 ft
# downstream; separate stores, separate barges, separate tally)
s.jetty(2498, 1724, rot=36, length=13)
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
BANK_ROT = -54  # the river passes the wharf at ~126 deg; the rows lie along it
s.granary(2333, 1922, n=4, w=20, h=12, gap=8, label="domain granaries", append=True, rot=BANK_ROT)
s.granary(2465, 1741, n=3, w=20, h=12, gap=8, label="Imperial granaries", append=True, rot=BANK_ROT)
# the brokers' lane runs shore-parallel between the granaries and the quay; its frontage is the
# brokers' row. The wharf suburb is OUTSIDE the ring-road bound the urban packs honor, so the
# frontage places against the suburb's own ground and the bound is restored after.
BROKER_LANE = [(2410, 1730), (2300, 1890), (2215, 2020)]
s.lane(BROKER_LANE, width=8)
_CITY_BOUND = s.bound
s.bound = [[2020, 1560], [2560, 1560], [2560, 2140], [2020, 2140]]
s.frontage(BROKER_LANE, (["merchant", "merchant", "shop"] * 4), width=8, spacing=19, rows=1, jitter=1, setback=s.px(14))
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

# ---- declared quarters (feature 020 re-zone): the CIVIC quarter is the ground the government
# actually occupies - the ote-suji band south of the ote-mon, ministries to chancellery - not a
# wedge picked before the castle was placed. The four interior wedges split at the kagi-no-te
# junction, where the avenue meets the through-road, and carry no zone stronger than "mixed"
# until feature 021 packs them. Quarters are declarative overlays, so the civic band riding over
# the wedge seams is intentional.
s.quarter([(1240, 1279), (1560, 1279), (1560, 1732), (1240, 1732)], "civic")
s.quarter([(OTE_X, KAGI_Y), (CX, 243), (WALL[3][0], WALL[3][1]), (WALL[5][0], WALL[5][1])], "mixed")  # NE
s.quarter([(OTE_X, KAGI_Y), (WALL[5][0], WALL[5][1]), (WALL[8][0], WALL[8][1]), (CX, WALL[10][1])], "mixed")  # SE
s.quarter([(OTE_X, KAGI_Y), (CX, WALL[10][1]), (WALL[13][0], WALL[13][1]), (WALL[15][0], WALL[15][1])], "mixed")  # SW
s.quarter([(OTE_X, KAGI_Y), (WALL[15][0], WALL[15][1]), (WALL[18][0], WALL[18][1]), (CX, 243)], "mixed")  # NW

# the wharf works and the aqueduct now anchor the frame's east; a modest uniform margin still
# shows each road running off the edge, and the south side carries the Imperial road caption,
# which finish() seats AFTER the crop and so cannot widen it itself. The EAST margin is wide on
# purpose: the aqueduct's intake works on the river (~x3140) are the part of the system a reader
# traces first (spec 020, User Story 3), and the default crop cut them - plus the east road's
# river bridge - clean off the sheet.
s.crop_city(margin=140, south=240, east=700)
s.title("Shiro Daika")
s.finish(os.path.splitext(os.path.abspath(__file__))[0].replace(".gen", ""), png_width=4600)
