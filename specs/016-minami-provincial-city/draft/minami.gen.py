#!/usr/bin/env python3
"""Minami - the Fox Clan's southern provincial city, on the Hayakawa (Mode B, 1px = 3ft).

THE FOX SEAT. Minami province is the southernmost of the four Fox provinces, administered by the
NANKE lineage (l7r.md "Fox Lineages and Provinces"). The Fox are one small domain - 150,000 humans
over four provinces - so this seat is deliberately UNDER the tier average: 2,600 residents against
Tango's and Nagahara's 3,000.

EIGHT TEMPLE PRECINCTS, NOT TWO. This is the map's reason for existing. In Fox lands the question
is "which TEMPLES do X", not which merchant families: the Seven Temples hold usufruct over sections
of the Kitsune Mori, moneylending sits with Fukurokujin and Ebisu, wedding loans with Benten. So
Minami carries seven modest precincts for the seven Fortunes of Good Luck plus a slightly larger
Inari - eight compounds, every one SMALLER than the single great complex an ordinary clan's city
builds. They are scattered by TRADE rather than gathered into a rim-belt teramachi, because each is
an economic house sited where its business is. And because only the THREE BONDS (High Monk, Temple
Master, Chief of Discipline) take a vow of celibacy, the rest of each precinct's clergy are
hereditary householders living OUT among the laity - so every compound is ringed by its own temple
families (kind "monk_house", drawn identical to laborer houses). 48 such households citywide
against Nagahara's 5. See research/religion-and-death.md; the exception is declared to the gate via
meta(temple_exception="fox_structure").

THE RIVER RUNS DOWN THE WEST FLANK - the mirror of Nagahara, which sits on the Hayakawa's west bank
downstream in Crab lands. Same river, same name end to end (settlements/water.md's one-name rule),
flowing north -> south out of the Kitsune Mori toward the Crab. The moat covers the three landward
faces and taps the river above and below; the cargo canal shares the moat's downstream mouth.

NO IMPERIAL ROAD. The Imperial road through Minami - the waystation-less stretch the Fox keep
warded - passes miles to the east; this seat is served by ordinary clan roads (meta
imperial_road=False), so the road net simply leaves the map in two directions and nothing is
labeled Imperial.

TIMBER DOWNRIVER, CHARCOAL BY CART. Fox wealth is the forest: lumber goes down the Hayakawa in
rafts, while charcoal and Kitsune-Koh incense - light and high-value - go overland. So the working
ground inside the wall is log stacking and charcoal godowns (a declared budget line, not ambient
slack), the zaimokuya's yard sits on the bank outside the river gate, and the kilns are outside
the walls entirely where fire law puts them.

PEACEFUL WALL. A minor clan shielded by the wood and the Three Man Alliance, not by fortification:
meta(wall_defense="peaceful") - the sparser Xi'an crossfire spacing, the first map in the pool to
exercise that tier.

Quarters: NE = laborer terraces; SE = the governor's ward (yamen + six ministries + samurai);
SW = burakumin downstream, with the timber and charcoal ground; NW = merchants around the dock.
"""

import math
import os
import sys

# WORK IN PROGRESS - deliberately NOT under pool/, because test_villages.py globs pool/*/*.gen.py
# and gates every map it finds: a red map there breaks the suite for every other session. Move
# this file to pool/provincial-cities/ (and drop the SKILL path shim below) once it gates clean.
SKILL = "/gm-assistant/.clones/diagram-city/.claude/skills/diagram"
sys.path.insert(0, SKILL)
from citybudget import BudgetLine, CityProgram, budget_to_manifest, plan_city  # noqa: E402
from settlement import Settlement  # noqa: E402
from waterfields import paddy_grain  # noqa: E402

PLOT_ACROSS, ROW_STEP = paddy_grain(3)

s = Settlement(3200, 2700, seed=61)

# THE POPULATION ARITHMETIC, which is not the same as an ordinary city's (feature 016).
# CityProgram.population is the LAY population - the castes in the budgets.md table. Minami's
# clergy are numerous enough that they can no longer hide inside the population tolerance the way
# Nagahara's five adept-monk households do: 8 precincts x 6 hereditary temple families = 48 real
# households, 240 residents. So the lay figure is set 240 BELOW the city's declared total, and the
# two add back up to the ~2,600 the GM asked for:
#     472 lay families + 48 temple families = 520 dwellings x 5 = 2,600 residents
LAY_POP = 2360
TEMPLE_PRECINCTS = 8
MONK_PER_PRECINCT = 6
MONK_HOUSES = TEMPLE_PRECINCTS * MONK_PER_PRECINCT  # 48
POP = LAY_POP + MONK_HOUSES * 5  # 2,600

s.meta(
    water_flow=90,  # DRAINAGE BEARING: the Hayakawa runs N -> S out of the Kitsune Mori (0=E, 90=S)
    name="Minami",
    scale="city",
    walled=True,
    population=POP,
    ftpx=3,
    wall_defense="peaceful",  # a minor clan behind the wood, not behind its rampart - the sparse tier
    imperial_road=False,  # the Imperial road through Minami passes miles east
    river_port=True,
    clan="Fox",
    capital_dir="northeast",  # Otosan Uchi lies far to the NE
    # The Fox have no two-patron structure to declare, so CLAN_FORTUNES carries no "fox" row and the
    # temple program is declared outright: the seven Fortunes of Good Luck plus Inari, the Fortune
    # of rice and of foxes and the clan's own.
    temple_fortunes=["Benten", "Bishamon", "Daikoku", "Ebisu", "Fukurokujin", "Hotei", "Inari", "Jurojin"],
    temple_exception="fox_structure",
)

# ---- BUDGET-FIRST wall sizing. Two extras lines beyond the standard program: the Inari precinct's
# uplift over its seven siblings (so "slightly larger" is a number on the sheet, not a claim in
# prose), and the in-wall timber/charcoal working ground (declared and DRAWN, never ambient slack).
BUDGET = plan_city(
    CityProgram(
        population=LAY_POP,
        river=True,
        temple_precincts=TEMPLE_PRECINCTS,
        temple_precinct_px2=3_400.0,  # ~30,600 sq ft, ~0.70 acre - modest against the 8,125 default
        monk_houses_per_precinct=float(MONK_PER_PRECINCT),
        extras=(
            BudgetLine("Inari precinct uplift", 1, 1_600.0, "the Inari precinct stands ~1.0 acre against its siblings' ~0.70 - the largest of the eight, still under an ordinary city's single complex"),
            BudgetLine("timber + charcoal working ground", 1, 8_000.0, "log stacking, sawpits and charcoal godowns inside the wall - the storage end of the Fox forest trade (the kilns are outside by fire law)"),
        ),
        aspect=0.93,
        nring=20,
    ),
    canvas=(3200, 2700),
)
s.meta(budget=budget_to_manifest(BUDGET))

# ---- the rampart: a closed ring with a NORTH gate (the clan road up toward Shinden Kitsune) and a
# WEST river gate (the bridge road), plus a water gate on the downstream (south) side of the river
# face where the cargo canal enters.
CX, CY, RX, RY = 1400, 1330, round(BUDGET.wall.rx), round(BUDGET.wall.ry)  # 431 x 400 from the budget
NRING = 20
WALL = [(round(CX + RX * math.cos(-math.pi / 2 + 2 * math.pi * i / NRING)), round(CY + RY * math.sin(-math.pi / 2 + 2 * math.pi * i / NRING))) for i in range(NRING)]
NGATE, WGATE, WGATE_PT = WALL[0], WALL[15], WALL[14]

# The samurai/government ward's fence, hoisted so its ground is reserved before any pack runs. It
# seals the SE quadrant: both ENDS abut solid rampart (on the wall's east face between vertices 4-5,
# and on its south face between 9-10), so the wall closes the other two sides and there is no
# walk-around gap. Entered from the commoner streets by kido.
WARD_FENCE = [(1818, 1270), (1430, 1270), (1430, 1640), (1520, 1716)]
KIDO_SPOTS = [(1430, 1330), (1793, 1270), (1430, 1470)]

s.city_wall(
    WALL,
    gates=[NGATE, WGATE],
    guard_east=[NGATE],
    water_gates=[WGATE_PT],
    ring_inset=22,
)

# ---- the Hayakawa: north -> south down the WEST flank; the moat joins it at both ends. Points run
# UPSTREAM-FIRST (source before mouth) - both the junction tilts and the checks key on that order.
RIVER = [(806, 520), (812, 855), (818, 1190), (826, 1525), (836, 1860), (848, 2170)]
RIVER_W = s.river(RIVER)
MOAT = s.moat(WALL, gap=24, river=RIVER, river_cut=130)
RING = s.ring_road(WALL, inset=22)
s.bound = [list(p) for p in RING]

# ORDERING: the kido reservations must run AFTER the ring road is drawn - kido_reservation asks the
# engine for the seat s.ward will take, and that angle follows the lane the gate bars.
for kx, ky in KIDO_SPOTS:
    s.block_polys.append(s.kido_reservation(kx, ky, WARD_FENCE))


# ---- DECLARED QUARTERS: tile the interior into zoned wedges split at the crossroads.
def _qpt(i, n=48, inset=24):
    a = -math.pi / 2 + 2 * math.pi * i / n
    return (CX + (RX - inset) * math.cos(a), CY + (RY - inset) * math.sin(a))


def _qwedge(i0, i1, n=48):
    return [(CX, CY)] + [_qpt(i, n) for i in range(i0, i1 + 1)]


s.quarter(_qwedge(0, 12), "residential")  # NE laborer terraces
s.quarter(_qwedge(12, 24), "mixed")  # SE governor's ward + samurai
s.quarter(_qwedge(24, 36), "mixed")  # SW burakumin + the timber/charcoal ground
s.quarter(_qwedge(36, 48), "mixed")  # NW merchants + the dock

s.corridors.append((WARD_FENCE, 15))  # reserve the ward fence line before ANY pack

# ---- THE through-road: down from the north gate, along the spine to the central crossroads, then
# WEST out through the river gate and over the Hayakawa bridge - one route, both ends off-map.
ROAD = [
    (1352, 560),
    (1372, 700),
    (1390, 840),
    (1400, 930),
    (1400, 1330),
    (1000, 1330),
    (930, 1330),
    (860, 1332),
    (760, 1336),
    (620, 1344),
    (470, 1352),
    (330, 1360),
]
s.road(ROAD)  # unlabeled: only Imperial roads get labels, and this is a clan road

s.drum_tower(1330, 1370)  # the seat's timekeeping/curfew tower at the SW corner of the crossroads

# ---- TRADE WORKS, placed early so every later pack flows around them.
s.brewery(1560, 1130)  # NE quarter
s.dye_yard(1120, 1470)  # on the in-wall cargo canal, east of the dock basin
s.lumber_yard(905, 1455)  # the zaimokuya on the dry tongue between the moat outflow and the river
s.oil_press(1610, 1250)
s.pawnshop(1230, 1215)  # NW merchant quarter, by the lending temples
s.bathhouses([(1520, 1215), (1180, 1560)])
s.kiln(700, 1600)  # OUTSIDE the walls on the far bank, south of the bridge road
# the TANNING YARD on the Hayakawa's EAST bank, south of the wall - downstream of everything the
# city puts in the water (below the moat outfall, below the dock, below the dyer), same bank as the
# SW burakumin quarter so nobody crosses.
s.tanning_yard(880, 1830, rot=90, pits=12, water="stream")
s.bridge(818, 1332, 4, RIVER_W + 26, 15)  # the Hayakawa bridge carries the through-road over the river

# ---- the cargo canal: moat -> water gate -> dock basin. ONE mouth on the river: the canal hands
# off at the moat's downstream corner and the moat carries boats the last reach out.
CANAL = [MOAT[1], (1010, 1462), (1085, 1458)]
s.canal(CANAL)
s.water_gate(1010, 1462, rot=-8)
s.dock(1104, 1458, 54, 34)
s.bridge(1038, 1460, 95, 34, 12)  # the ring road bridges the canal just inside the wall

# ---- civic amenities placed FIRST so the dense packs flow around them.
s.flophouse(1352, 800, label_below=True)  # outside the NORTH gate
s.flophouse(915, 1268)  # outside the WEST river gate, on the wharf
# N-gate caravan cluster, EAST of the spine just inside the gate
s.block_polys.append([(1420, 950, ), (1478, 950), (1478, 1071), (1420, 1071)])
s.flophouse(1444, 963, label_below=True)
s.inn(1458, 1044)
s.stables(1444, 1011, rot=90)
s.farrier(1500, 1000, rot=90)
# W-gate caravan cluster, north of the main road just inside the river gate. Kept WEST of x1140 so
# it does not smother the merchant street at x1180 (the first draft's reserve ran to x1200 and the
# MER_V1 frontage placed 1 house of 32).
s.block_polys.append([(1005, 1150), (1130, 1150), (1130, 1300), (1005, 1300)])
s.flophouse(1040, 1178, label_below=True)
s.inn(1040, 1220)
s.stables(1076, 1262, rot=90)


def grid(streets, width_ft=18):
    for st in streets:
        s.street(st, width=s.lw(width_ft))


def front(streets, kinds, width_ft=18, spacing=19, rows=1):
    for st in streets:
        s.frontage(st, list(kinds), width=s.lw(width_ft), spacing=spacing, rows=rows, rowgap=2, jitter=1, setback=s.px(14))


def alleys(lst):
    for a in lst:
        s.alley(a)


# ====================================================================== the street skeleton
EAST_ST = [(1400, 1330), (1712, 1330)]  # the ward approach, east from the crossroads
grid([EAST_ST], width_ft=22)
NORTH_ST = [(1560, 1040), (1560, 1330)]
MER_V1 = [(1180, 1090), (1180, 1300)]
MER_V2 = [(1080, 1360), (1080, 1600)]
grid([NORTH_ST, MER_V1, MER_V2])

# ====================================================================== THE EIGHT PRECINCTS
# Each is a modest walled compound - SMALLER than either shipped city's complexes - sited where its
# TRADE is, with its hereditary temple families packed in the blocks around it. Sizes: the seven
# Fortunes at ~0.70 acre drawn, Inari the largest of the eight.
TW, TH = s.px(96), s.px(66)  # the seven siblings
IW, IH = s.px(118), s.px(80)  # Inari


def precinct(x, y, fortune, torii, w=TW, h=TH, primary=False, label_below=True):
    s.shrine_hall(x, y, f"Temple of {fortune}", w=w, h=h, kind="temple", primary=primary, label_below=label_below, torii=torii)


# --- NW: the LENDING temples, by the dock and the merchant district. Ebisu (honest commerce, the
# wharf's fortune) and Fukurokujin share the moneylending trade in Fox lands, so they sit together -
# the city's one genuine temple cluster, which is why the wayside shrines gather here.
precinct(1150, 1140, "Ebisu", [(1150, 1188)], primary=True)
precinct(1290, 1120, "Fukurokujin", [(1290, 1168)])
for sx, sy in [(1215, 1185), (1235, 1215), (1195, 1225)]:
    s.small_shrine(sx, sy)
s.label(1220, 1258, "temple lending quarter", 9, italic=True, color="#6B2A18")

# --- W: BENTEN by the river gate - the water fortune, and the temple that lends against a wedding
precinct(1075, 1330 - 90, "Benten", [(1075, 1288)], label_below=False)

# --- CENTRAL-N: INARI, the largest of the eight. The Fox clan's own fortune - rice and foxes - and
# the temple that keeps the Inari paddy reserve whose harvest Inari shrines buy Empire-wide.
precinct(1400, 1090, "Inari", [(1400, 1148)], w=IW, h=IH)

# --- NE: the laborer quarter's pair - Hotei and Jurojin
precinct(1640, 1090, "Hotei", [(1640, 1138)])
precinct(1740, 1210, "Jurojin", [(1740, 1258)])
for sx, sy in [(1690, 1160), (1706, 1128), (1666, 1196)]:
    s.small_shrine(sx, sy)

# --- SE: BISHAMON in the samurai ward - the warrior fortune. It takes the ward's NORTH-EAST
# corner rather than a seat among the ministries: the government avenue and the yamen's walled
# court own the middle of this quarter, and an arch may not stand in a compound wall.
precinct(1770, 1310, "Bishamon", [(1770, 1352)])

# --- SW: DAIKOKU by the timber and charcoal ground - the fortune of wealth and stores
precinct(1210, 1660, "Daikoku", [(1210, 1708)])

# ---- the shared burial grounds. EIGHT precincts do NOT get eight graveyards: these are economic
# institutions holding forest usufruct, not eight parishes, so the city's dead go to a few common
# grounds attached to the larger precincts (research/religion-and-death.md finding 4).
s.cemetery(1400, 1010, 46, 32, label="graveyard", label_above=True)  # Inari's
s.cemetery(1148, 1078, 42, 30, label="graveyard", label_above=True)  # Ebisu's
s.cemetery(1212, 1730, 42, 30, label="graveyard")  # Daikoku's

# ---- TEMPLE FAMILY HOUSING: 6 households per precinct, drawn identical to laborer houses. Placed
# before the packs so the warrens flow around them.
for _tx, _ty in [
    (1090, 1175),
    (1330, 1170),
    (1030, 1290),
    (1462, 1120),
    (1600, 1140),
    (1790, 1170),
    (1690, 1230),
    (1075, 1690),
]:
    s.pack((_tx - 34, _ty - 22, _tx + 34, _ty + 30), ["monk_house"] * MONK_PER_PRECINCT, step=15)

# ====================================================================== SE: the governor's ward
GOV_AVE = [(1440, 1450), (1800, 1450)]
grid([GOV_AVE])
s.governor_mansion(1620, 1580, s.px(400), s.px(330), "Governor's Mansion", gate_dir="north")
MINS = ["Ministry of Rites", "Ministry of Revenue", "Ministry of Retainers", "Ministry of War", "Ministry of Works", "Ministry of Justice"]
MIN_POS = [(1478, 1380), (1610, 1370), (1740, 1390), (1470, 1520), (1790, 1520), (1500, 1640)]
for (mx, my), name in zip(MIN_POS, MINS, strict=True):
    s.ministry(mx, my, name, w=s.px(120), h=s.px(84))
s.mausoleum(1700, 1660, 44, 32, label="Mausoleum", gate_dir="north", label_below=True)
_CIV_I0 = len(s.block_polys)
for _m in s.M["ministries"] + [s.M["governor_mansion"]]:
    s.block_polys.append([(_m["x"] - _m["w"] / 2 - 30, _m["y"] - _m["h"] / 2 - 30), (_m["x"] + _m["w"] / 2 + 30, _m["y"] - _m["h"] / 2 - 30), (_m["x"] + _m["w"] / 2 + 30, _m["y"] + _m["h"] / 2 + 30), (_m["x"] - _m["w"] / 2 - 30, _m["y"] + _m["h"] / 2 + 30)])
_CIV_I1 = len(s.block_polys)
for _L in s.M["labels"]:
    if len(_L) > 5 and _L[5].startswith("Ministry"):
        s.block_polys.append([(_L[0] - 15, _L[1] - 12), (_L[2] + 15, _L[1] - 12), (_L[2] + 15, _L[3] + 12), (_L[0] - 15, _L[3] + 12)])
s.martial_hall(1690, 1470, label_xy=(1690, 1473))
s.dojos([(1560, 1470), (1780, 1620)])
front([EAST_ST, GOV_AVE], (["samurai_large"] + ["samurai"] * 2) * 5, spacing=19, rows=1)
s.rowpack((1440, 1290, 1700, 1340), ["samurai"] * 24, court_every=6, eave_ft=3)  # the band between the ward's north fence and the government avenue
s.pack((1440, 1280, 1810, 1700), (["samurai"] * 3 + ["samurai_large"]) * 120, step=11, face_streets="fill")
s.label(1600, 1690, "samurai neighborhood", 10, italic=True, color="#3A352C")
s.ward("samurai", WARD_FENCE, gates=KIDO_SPOTS)

# ====================================================================== NE: the laborer quarter
LAB_H = [(1560, 1180), (1800, 1180)]
grid([LAB_H])
s.fire_tower(1520, 1090, label=None)
front([NORTH_ST], (["shop"] + ["laborer_large"] * 3) * 10, spacing=18, rows=1)
alleys([[(1680, 1010), (1680, 1180)]])
s.place_wells((1450, 980, 1800, 1300), spacing=58)
_lab = (["laborer"] * 3 + ["servant"]) * 120
s.rowpack((1450, 975, 1800, 1075), _lab, court_every=4, eave_ft=3)
s.rowpack((1450, 1200, 1800, 1300), _lab, court_every=4, eave_ft=3)
s.label(1600, 1300, "laborer neighborhoods", 10, italic=True, color="#5A4326")

# ====================================================================== NW: merchants + the dock
s.fire_tower(1140, 1400, label="fire tower")
s.merchant_storehouses(7)
_n_est = s.merchant_estates([(1250, 1420, "east"), (1150, 1250, "east"), (1300, 1560, "south")])
s.frontage([(1060, 1330), (1390, 1330)], (["merchant"] * 3 + ["shop"]) * 14, skip=ROAD, width=s.lw(26), spacing=19, rows=2, rowgap=2, jitter=1, setback=s.px(14))
front([MER_V1, MER_V2], (["merchant"] * 3 + ["shop"]) * 8, spacing=19, rows=1)
s.place_wells((1030, 1080, 1370, 1300), spacing=58)
_mer = (["merchant_house"] * 2 + ["servant"] + ["laborer"]) * 110
s.rowpack((1030, 1080, 1370, 1300), _mer, court_every=4, eave_ft=3)
s.label(1180, 1360, "merchant district", 10, italic=True, color="#5A4326")

# ====================================================================== SW: burakumin + timber ground
BUR_ST = [[(1080, 1620), (1380, 1620)]]
grid(BUR_ST)
s.fire_tower(1300, 1600, label=None)
front(BUR_ST, (["burakumin"] + ["servant"]) * 12, spacing=19, rows=1)
s.place_wells((1050, 1560, 1400, 1720), spacing=56)
s.rowpack((1050, 1560, 1400, 1605), (["burakumin"] * 2 + ["servant"] * 2) * 50, court_every=6, eave_ft=3)
s.rowpack((1050, 1650, 1400, 1720), (["burakumin"] * 2 + ["servant"] * 2) * 50, court_every=6, eave_ft=3)
s.label(1220, 1545, "burakumin", 10, italic=True, color="#6B4F2A")
# THE TIMBER AND CHARCOAL WORKING GROUND - the declared budget line, DRAWN as its kind: beaten
# earth with the stacking rails, in the SW between the burakumin rows and the river wall.
s.animal_ground(1330, 1760, r=74, label="timber + charcoal ground")

# ====================================================================== OUTSIDE the walls
s.bound = None
for jx, jy in ((880, 1230), (880, 1315), (880, 1400)):
    s.jetty(jx, jy, rot=180, length=22)
QUAY = [(945, 1250), (945, 1420)]
s.frontage(QUAY, ["shop"] * 16, width=s.lw(18), spacing=19, rows=2, rowgap=2, jitter=1, setback=s.px(14))
s.label(955, 1215, "wharf", 10, italic=True, color="#5A4326")
s.frontage([(760, 1336), (900, 1332)], ["shop"] * 8, skip=ROAD, width=s.lw(22), spacing=18, rows=1, jitter=1, setback=s.px(15), fill=True)
s.frontage([(1352, 830), (1372, 700), (1390, 620)], ["shop"] * 14, skip=ROAD, width=s.lw(22), spacing=17, rows=1, jitter=1, setback=s.px(16), fill=True)
s.label(1290, 790, "gate market", 9, italic=True, color="#5A4326")

# samurai country estates: dispersed walled compounds NORTHEAST of the city, toward Otosan Uchi
EST = [
    (1930, 1080, 76, 48, "west", (2050, 1100)),
    (2130, 940, 84, 56, "south", (2200, 960)),
    (2300, 1150, 94, 62, "west", (2360, 1180)),
]
for ex, ey, ew, eh, gd, (_lx, _ly) in EST:
    s.manor(ex, ey, ew, eh, "", gate_dir=gd)
s.label(2100, 1240, "samurai estates", 10, italic=True, color="#3A352C")

s.bridges()
s.crop_city(margin=35)
s.title("Minami")

HERE = os.path.dirname(os.path.abspath(__file__))
nb = {}
for b in s.M["buildings"]:
    nb[b["kind"]] = nb.get(b["kind"], 0) + 1
print("farmhouses:", len(s.M["houses"]), "| buildings:", nb, "| total urban:", sum(nb.values()), "| estates:", len(s.M["manors"]), "| finish:", s.finish(os.path.join(HERE, "minami")))
