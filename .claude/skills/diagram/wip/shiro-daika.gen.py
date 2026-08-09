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
# a STREET, not a lane (021): the kashi quay street is real machi frontage - the brokers'
# row and warehouse fronts must satisfy businesses_front_streets like any other shops
s.street(BROKER_LANE, width=s.lw(15))
_CITY_BOUND = s.bound
s.bound = [[2020, 1560], [2560, 1560], [2560, 2140], [2020, 2140]]
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
s.street([(900, 2005), (1900, 2005)], width=s.lw(15))  # dropped south of the Temple of Inari's hall (992,1937)
s.street([(1040, 1256), (1040, 2080)], width=s.lw(15))  # x=1040 clears the Temple of Inari's hall (~x992)
s.street([(1800, 1300), (1800, 1540)], width=s.lw(15))  # stops at the Benten precinct's reserved ground
s.street([(1800, 1700), (1800, 2060)], width=s.lw(15))  # ...and resumes south of it (a precinct blocks a street; the walls are the dead end)
s.street([(2130, 1250), (2130, 1620)], width=s.lw(15))  # east of Kurogi (x1986-2094), stopping clear of the Temple of Ebisu (2127,1686)
s.street([(800, 1450), (800, 1930)], width=s.lw(15))
s.street([(460, 1375), (1240, 1375)], width=s.lw(15))  # y=1375: under the west band tail, over the kagi leg
s.street([(1560, 1390), (2340, 1390)], width=s.lw(15))  # threaded between Kurogi's south wall (y1372) and the Imperial Magistracy's north wall (y1407)

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
s.lane([(1990, 560), (1990, 1240)], width=7)  # stops ABOVE Kurogi's west wall (x1986)
s.lane([(1965, 1270), (1965, 1740)], width=7)  # the southern leg, west of Kurogi + the Benten precinct
s.lane([(790, 560), (790, 1350)], width=7)
s.lane([(1205, 1300), (1205, 1520)], width=7)  # the ote west flank's own lane

_YJ = ((2, -2), (-4, 2), (4, 4), (-2, -4), (0, 2), (3, -3))  # deterministic size jitter, no stream draw


def _yashiki(x: float, y: float, gate_dir: str, i: int) -> None:
    _w = 60 + _YJ[i % 6][0]
    _h = 50 + _YJ[i % 6][1]
    s.manor(x, y, _w, _h, None, gate_dir=gate_dir)


# north band: ONE row sharing the estates' line (gates south onto the y=475 lane). The
# wall and ring slant hard across y~270-450 here (vertices at (1082,290)/(1718,290) with
# the ring 30 inside), and the NW diagonal road owns the band's west half - both ate the
# planned second row, so the band runs east of the karamete corridor's flanks only.
for _i, _x in enumerate((1250, 1325, 1760, 1830)):
    _yashiki(_x, 430, "south", _i + 3)
# east band: a west file on the band lane (starting BELOW the Temple of Bishamon's ground
# at (1928,531)), a south file flanking the lane's lower leg around the reserved Benten
# precinct (~x1785-1915, y1570-1670), and east-side compounds in the lineage-estate gaps
for _i, _y in enumerate((673, 751, 829, 907, 985, 1063, 1141, 1219)):
    _yashiki(1925, _y, "east", _i)
for _i, _y in enumerate((1300, 1490, 1715)):
    _yashiki(1905, _y, "east", _i + 2)
for _i, _y in enumerate((1490, 1565)):
    _yashiki(2040, _y, "west", _i + 1)
for _i, _y in enumerate((595, 850, 1120, 1195)):
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
s.terrace(760, 1815, units=8)  # x=760: the wall/ring curve at this latitude runs x~635/678, so the ranges stand inside the patrol road
s.terrace(760, 1840, units=8)

# alleys BEFORE the packs (each reserves its corridor; no block core sits >95px from a way)
s.alley([(640, 1408), (640, 1552)])  # the D5/west mid-band pocket (x=640: clear of the (700,1420) compound)
s.alley([(2495, 1070), (2640, 1070)])  # the east gate ward (its road runs ~y1170)
s.alley([(2385, 1690), (2520, 1520)])  # the wharf's upstream bank boxes
s.alley([(2500, 1255), (2640, 1255)])  # the east approach samurai seats
for _ax, _ay1 in ((700, 1845), (795, 1935), (910, 2010), (1180, 2095), (1300, 2095)):
    s.alley([(_ax, 1585), (_ax, _ay1)])  # each column stops short of the ring's southwest curve
s.alley([(1565, 1415), (1565, 2095)])  # runs up past the kagi to serve the magistracy flank
for _ax in (1655, 1690, 2000):  # east columns clear the hanko (x1415-1549) and the (1905,1715) compound
    s.alley([(_ax, 1585), (_ax, 2095)])
s.alley([(2200, 760), (2200, 1290)])
s.alley([(2300, 805), (2300, 1290)])  # both start below the NE wall's tower course
s.alley([(2260, 1270), (2260, 1590)])

# ---- T008: DETACHED SAMURAI (133 target) - the middle band, rowpacked at the loose samurai
# court pitch (the Tango idiom, which is what C_SPACED was measured from).
_SAM = ["samurai"] * 4 + ["samurai_large"]
s.district("moat-south detached band", "detached", [(615, 1268), (1145, 1268), (1145, 1370), (615, 1370)], rank_band="detached")
s.rowpack((620, 1275, 1140, 1362), _SAM * 10, court_every=8)
s.district("magistracy detached flank", "detached", [(1555, 1400), (1860, 1400), (1860, 1560), (1555, 1560)], rank_band="detached")
s.rowpack((1560, 1408, 1660, 1555), _SAM * 4, court_every=8)
s.rowpack((1808, 1408, 1852, 1555), _SAM * 2, court_every=8)
s.district("west detached pocket", "detached", [(470, 1400), (790, 1400), (790, 1745), (470, 1745)], rank_band="detached")
s.district("civic west detached", "detached", [(855, 1400), (1145, 1400), (1145, 1560), (855, 1560)], rank_band="detached")
s.district("east street detached", "detached", [(2140, 1250), (2385, 1250), (2385, 1425), (2140, 1425)], rank_band="detached")
s.rowpack((605, 1408, 785, 1555), _SAM * 5, court_every=8)
s.rowpack((475, 1440, 595, 1740), _SAM * 6, court_every=8)
s.rowpack((860, 1408, 1140, 1555), _SAM * 5, court_every=8)
s.rowpack((2145, 1255, 2380, 1420), _SAM * 4, court_every=8)

# ---- T010: THE COMMONER MACHI (2,160 packed target: 960 laborer / 480 servant / 600
# merchant / 120 burakumin). Burakumin strips seat FIRST at the settlement edge (the two
# in-wall quarters of the counts table); the big machi packs then flow around them and
# around every standing compound, temple, precinct reservation and street.
s.district("southwest machi", "machi", [(615, 1575), (1395, 1575), (1395, 2110), (615, 2110)], rank_band=None)
s.district("southeast machi", "machi", [(1405, 1575), (2120, 1575), (2120, 2110), (1405, 2110)], rank_band=None)
s.district("east gate machi", "machi", [(2145, 635), (2405, 635), (2405, 1310), (2145, 1310)], rank_band=None)
s.district("east street machi", "machi", [(2140, 1420), (2385, 1420), (2385, 1620), (2140, 1620)], rank_band=None)
s.district("west rim machi", "machi", [(430, 750), (590, 750), (590, 1445), (430, 1445)], rank_band=None)
s.frontage([(620, 1770), (2180, 1770)], ["merchant", "merchant", "shop"] * 30, width=8, spacing=20, setback=14)
s.frontage([(900, 2005), (1900, 2005)], ["merchant", "shop"] * 15, width=8, spacing=20, setback=14)
s.frontage([(1040, 1290), (1040, 2070)], ["merchant"] * 20, width=8, spacing=21, setback=14)
s.frontage([(1800, 1710), (1800, 2050)], ["merchant"] * 10, width=8, spacing=21, setback=14)
s.rowpack((810, 1880, 990, 1990), (["burakumin"] * 3 + ["servant"]) * 27, court_every=3)
s.rowpack((1810, 1880, 1950, 1990), (["burakumin"] * 3 + ["servant"]) * 27, court_every=3)
# T011 first: the adept-monk houses by the two sovereign precincts (budget: 2.5/precinct) -
# seated BEFORE the big packs so the precinct-adjacent ground is theirs
s.rowpack((1700, 1585, 1780, 1660), ["monk_house"] * 3, court_every=3)
s.rowpack((1020, 1585, 1100, 1660), ["monk_house"] * 2, court_every=3)
_MIX = ["laborer", "laborer", "servant", "merchant_house"]  # interior rows; the BUSINESS merchants front the streets via s.frontage
s.rowpack((560, 1580, 1385, 2125), _MIX * 330, court_every=4)
s.rowpack((1415, 1580, 1930, 2125), _MIX * 260, court_every=4)
s.rowpack((2000, 1580, 2115, 2125), _MIX * 100, court_every=4)
s.rowpack((2150, 755, 2400, 1310), (["laborer", "merchant_house"]) * 200, court_every=4)
s.rowpack((2145, 1425, 2330, 1615), _MIX * 26, court_every=4)
s.rowpack((1740, 1295, 1852, 1385), _MIX * 8, court_every=4)
s.alley([(530, 770), (530, 1430)])  # the rim's access is an ALLEY (block-core way; it counts for reachability)
s.rowpack((442, 760, 505, 1155), _MIX * 9, court_every=4)
s.rowpack((442, 1250, 505, 1435), _MIX * 5, court_every=4)  # resumes south of the Temple of Daikoku (501,1200)
s.rowpack((548, 760, 588, 1435), _MIX * 14, court_every=4)


# ---- the SUBURBS (021): a capital houses part of its packed cohort OUTSIDE the wall - the
# kashi wharf suburb (its brokers and warehouse folk live at the landing) and the guan-xiang
# gate wards on the approach roads, both the lawful outside categories the commoner rule
# names. The packs honor s.bound, so each suburb temporarily owns its own bound box.
_CITY_BOUND2 = s.bound
# the wharf suburb: bank-aligned boxes between the MOAT's outer edge and the river, stepping
# down the diagonal shore with the broker street (the first cut boxed the whole quay and
# packed rows onto the moat band)
s.bound = [[2100, 1560], [2600, 1560], [2600, 2140], [2100, 2140]]
s.rowpack((2370, 1630, 2480, 1715), ["merchant_house", "laborer", "laborer"] * 8, court_every=4)
s.rowpack((2300, 1725, 2430, 1810), ["merchant_house", "laborer", "laborer"] * 14, court_every=4)
s.rowpack((2240, 1815, 2370, 1900), ["merchant_house", "laborer", "laborer"] * 14, court_every=4)
s.rowpack((2180, 1905, 2300, 2000), ["laborer", "laborer", "servant"] * 12, court_every=4)
s.rowpack((2130, 2000, 2250, 2070), ["laborer", "servant"] * 12, court_every=4)
s.rowpack((2430, 1565, 2555, 1645), ["merchant_house", "laborer"] * 8, court_every=4)
s.rowpack((2490, 1495, 2610, 1560), ["merchant_house", "laborer"] * 6, court_every=4)
s.rowpack((2080, 2075, 2210, 2135), ["laborer", "servant"] * 7, court_every=4)
# the gate wards, each hugging its approach road inside the guan-xiang reach
s.bound = [[1290, 2225], [1510, 2225], [1510, 2400], [1290, 2400]]
s.rowpack((1305, 2235, 1390, 2395), ["laborer", "merchant_house", "servant"] * 20, court_every=4)  # ends inside the guan-xiang reach; the Imperial Road caption keeps its seat below
s.rowpack((1412, 2235, 1495, 2340), ["laborer", "merchant_house", "servant"] * 16, court_every=4)
s.bound = [[2480, 1000], [2630, 1000], [2630, 1135], [2480, 1135]]
s.rowpack(
    (2495, 1012, 2615, 1128), ["laborer", "merchant_house"] * 20 + ["laborer"], court_every=4
)  # NOTE: the census closes EXACTLY at 2,472 (12,360/5); adjust ONE item here if fabric upstream moves

s.bound = [[1300, 55], [1505, 55], [1505, 200], [1300, 200]]
s.rowpack((1408, 88, 1492, 192), ["laborer", "merchant_house"] * 8, court_every=4)  # the N gate ward, on the Shiro Kyo road
s.rowpack((1310, 95, 1392, 192), ["laborer", "merchant_house"] * 9, court_every=4)
# (no SW gate ward: the moat band and the diagonal approach road leave no clean ground
# within the guan-xiang reach - its households ride the S ward and the wharf instead)
s.bound = _CITY_BOUND2


# the suburbs are DISTRICTS like any fabric (the band-target check counts by district)
s.district("wharf suburb", "machi", [(2080, 1480), (2620, 1480), (2620, 2145), (2080, 2145)], rank_band=None)
s.district("south gate ward", "machi", [(1290, 2225), (1510, 2225), (1510, 2345), (1290, 2345)], rank_band=None)
s.district("east gate ward", "machi", [(2480, 1000), (2630, 1000), (2630, 1110), (2480, 1110)], rank_band=None)
s.district("north gate ward", "machi", [(1395, 55), (1505, 55), (1505, 200), (1395, 200)], rank_band=None)

# ---- the OUT-WALL SAMURAI (the budget's other 47: CAPITAL_SAMURAI_INWALL_FRAC leaves 15%
# of the cohort in country seats on the approaches - the Tango out-wall precedent; they
# count in the census but belong to NO rank district, so the in-wall band targets stand)
_CB3 = s.bound
s.bound = [[1420, 2350], [1580, 2350], [1580, 2470], [1420, 2470]]
s.rowpack((1428, 2360, 1494, 2465), _SAM * 4, court_every=8)  # east of the road, inside its 95px reach; the caption keeps the west seat
s.bound = [[2480, 1230], [2660, 1230], [2660, 1340], [2480, 1340]]
s.rowpack((2495, 1240, 2645, 1330), _SAM * 5, court_every=8)
s.bound = [[1180, 2350], [1270, 2350], [1270, 2460], [1180, 2460]]
s.rowpack((1190, 2360, 1262, 2455), _SAM * 2, court_every=8)
s.bound = _CB3


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
s.quarter([(1082, 290), (1400, 243), (1718, 290), (2005, 426), (1851, 504), (949, 504)], "samurai")  # north band
s.quarter([(1851, 504), (2005, 426), (2246, 608), (2378, 904), (2429, 1200), (2378, 1496), (2160, 1390), (1855, 1390), (1851, 1256)], "samurai")  # east band + gate machi rim
s.quarter([(949, 504), (795, 426), (568, 637), (422, 904), (371, 1200), (422, 1496), (560, 1390), (1150, 1390), (1150, 1290), (949, 1256)], "samurai")  # west band
s.quarter([(1315, 1290), (1560, 1290), (1560, 1720), (1315, 1720)], "civic")  # the government band proper
s.quarter(
    [(422, 1496), (568, 1763), (795, 1974), (1082, 2110), (1400, 2157), (1718, 2110), (2005, 1974), (2246, 1792), (2378, 1496), (2160, 1390), (1150, 1390), (560, 1390)], "mixed"
)  # the machi south

# the wharf works and the aqueduct now anchor the frame's east; a modest uniform margin still
# shows each road running off the edge, and the south side carries the Imperial road caption,
# which finish() seats AFTER the crop and so cannot widen it itself. The EAST margin is wide on
# purpose: the aqueduct's intake works on the river (~x3140) are the part of the system a reader
# traces first (spec 020, User Story 3), and the default crop cut them - plus the east road's
# river bridge - clean off the sheet.
s.crop_city(margin=140, south=240, east=700)
s.title("Shiro Daika")
s.finish(os.path.splitext(os.path.abspath(__file__))[0].replace(".gen", ""), png_width=4600)
