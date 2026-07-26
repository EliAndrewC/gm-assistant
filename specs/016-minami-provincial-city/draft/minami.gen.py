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
an economic house sited where its business is. Only the THREE BONDS take a vow of celibacy, so the
rest of each precinct's clergy are hereditary householders living OUT among the laity - every
compound is ringed by its own temple families (kind "monk_house", drawn identical to laborer
houses), 48 citywide against Nagahara's 5. And eight precincts do NOT get eight graveyards: these
are economic institutions holding forest usufruct, not eight parishes, so three of them keep the
city's shared burial grounds and the other five declare graveyard=False. See
research/religion-and-death.md; the exception is declared via meta(temple_exception="fox_structure").

THE RIVER RUNS DOWN THE WEST FLANK - the mirror of Nagahara, which sits on the Hayakawa's west bank
downstream in Crab lands. Same river, same name end to end (settlements/water.md's one-name rule),
flowing north -> south out of the Kitsune Mori toward the Crab. The moat covers the three landward
faces and taps the river above and below; the cargo canal shares the moat's downstream mouth.

NO IMPERIAL ROAD. The Imperial road through Minami - the waystation-less stretch the Fox keep
warded - passes miles to the east, so the road net simply leaves the map in two directions and
nothing is labeled Imperial.

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
SKILL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".claude", "skills", "diagram")
sys.path.insert(0, os.path.abspath(SKILL))
from citybudget import BudgetLine, CityProgram, budget_to_manifest, plan_city  # noqa: E402
from settlement import Settlement, moat_swept_tap  # noqa: E402
from waterfields import AZE, BEAN_GREEN, aze_w, build_comb, hem_on_paddy, paddy_grain  # noqa: E402

PLOT_ACROSS, ROW_STEP = paddy_grain(3)

s = Settlement(3200, 2700, seed=61)

# THE POPULATION ARITHMETIC, which is not an ordinary city's (feature 016). CityProgram.population
# is the LAY population - the castes in the budgets.md table. Minami's clergy are numerous enough
# that they can no longer hide inside the population tolerance the way Nagahara's five adept-monk
# households do: 8 precincts x 6 hereditary temple families = 48 real households, 240 residents. So
# the lay figure is set 240 BELOW the declared total and the two add back up:
#     472 lay families + 48 temple families = 520 dwellings x 5 = 2,600 residents
LAY_POP = 2360
TEMPLE_PRECINCTS = 8
MONK_PER_PRECINCT = 6
MONK_HOUSES = TEMPLE_PRECINCTS * MONK_PER_PRECINCT
POP = LAY_POP + MONK_HOUSES * 5

s.meta(
    water_flow=90,  # DRAINAGE BEARING: the Hayakawa runs N -> S out of the Kitsune Mori (0=E, 90=S)
    name="Minami",
    scale="city",
    walled=True,
    population=POP,
    ftpx=3,
    wall_defense="peaceful",  # a minor clan behind the wood, not behind its rampart - the sparse tier
    imperial_road=False,
    river_port=True,
    clan="Fox",
    capital_dir="northeast",
    temple_fortunes=["Benten", "Bishamon", "Daikoku", "Ebisu", "Fukurokujin", "Hotei", "Inari", "Jurojin"],
    temple_exception="fox_structure",
)

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

CX, CY, RX, RY = 1400, 1330, round(BUDGET.wall.rx), round(BUDGET.wall.ry)  # 431 x 400 from the budget
NRING = 20
WALL = [(round(CX + RX * math.cos(-math.pi / 2 + 2 * math.pi * i / NRING)), round(CY + RY * math.sin(-math.pi / 2 + 2 * math.pi * i / NRING))) for i in range(NRING)]
NGATE, WGATE, WGATE_PT = WALL[0], WALL[15], WALL[13]

# The samurai/government ward's fence, hoisted so its ground is reserved before any pack runs. Both
# ENDS abut solid rampart - on the wall's east face between vertices 4-5, and on its south face
# between 9-10 - so the wall closes the other two sides and there is no walk-around gap. Four kido:
# two where the commoner streets pierce it, two where the ring road crosses its ends.
WARD_FENCE = [(1820, 1286), (1420, 1306), (1420, 1660), (1455, 1718)]
KIDO_SPOTS = [(1420, 1330), (1420, 1450), (1798, 1287), (1443, 1700)]

s.city_wall(WALL, gates=[NGATE, WGATE], guard_east=[NGATE], water_gates=[WGATE_PT], ring_inset=22)

# ---- the Hayakawa: north -> south down the WEST flank. Points run UPSTREAM-FIRST (source before
# mouth) - both the junction tilts and the checks key on that order.
RIVER = [(806, 520), (812, 855), (818, 1190), (826, 1525), (836, 1860), (848, 2170)]
RIVER_W = s.river(RIVER)
MOAT = s.moat(WALL, gap=24, river=RIVER, river_cut=130)
RING = s.ring_road(WALL, inset=22)
s.bound = [list(p) for p in RING]

# ORDERING: the kido reservations run AFTER the ring road, because kido_reservation asks the engine
# for the seat s.ward will take and that angle follows the lane the gate bars.
for kx, ky in KIDO_SPOTS:
    s.block_polys.append(s.kido_reservation(kx, ky, WARD_FENCE))


def _qpt(i, n=48, inset=24):
    a = -math.pi / 2 + 2 * math.pi * i / n
    return (CX + (RX - inset) * math.cos(a), CY + (RY - inset) * math.sin(a))


def _qwedge(i0, i1, n=48):
    return [(CX, CY)] + [_qpt(i, n) for i in range(i0, i1 + 1)]


s.quarter(_qwedge(0, 12), "residential")  # NE laborer terraces
s.quarter(_qwedge(12, 24), "mixed")  # SE governor's ward + samurai
s.quarter(_qwedge(24, 36), "mixed")  # SW burakumin + the timber/charcoal ground
s.quarter(_qwedge(36, 48), "mixed")  # NW merchants + the dock

s.corridors.append((WARD_FENCE, 22))

# ---- THE through-road: down from the north gate, along the spine to the central crossroads, then
# WEST out through the river gate and over the Hayakawa bridge - one route, both ends off-map.
ROAD = [(1352, 500), (1372, 690), (1390, 840), (1400, 930), (1400, 1330), (1000, 1330), (930, 1330), (860, 1332), (700, 1338), (480, 1348), (240, 1358)]
s.road(ROAD)

s.drum_tower(1366, 1386)  # the bell-and-drum tower at the SW corner of the central crossroads

# ---- TRADE WORKS, placed early so every later pack flows around them.
s.brewery(1520, 1230)
s.dye_yard(1162, 1596)  # on the in-wall cargo canal, north of the dock basin
s.lumber_yard(902, 1436)  # the zaimokuya on the dry strip below the wharf, clear of the water
s.oil_press(1548, 1300)
s.pawnshop(1290, 1300)  # NW merchant quarter, by the lending temples
s.bathhouses([(1436, 1176), (1250, 1400)])
s.kiln(640, 1180)  # OUTSIDE the walls on the far bank
s.tanning_yard(866, 1700, rot=90, pits=12, water="stream")  # east bank, DOWNSTREAM of dock, dyer and moat outfall
s.bridge(818, 1332, 4, RIVER_W + 26, 15)

# ---- the cargo canal: the moat's downstream corner -> water gate -> dock basin. ONE mouth on the
# river: the canal communicates with the MOAT and the moat's own outfall junction is the single
# navigation entrance (the Suzhou pattern).
CANAL = [MOAT[-2], (1051, 1565), (1128, 1572)]
s.canal(CANAL)
s.water_gate(1051, 1565, rot=152)
s.dock(1152, 1574, 54, 34)
s.bridge(1098, 1568, 84, 34, 12)  # the ring road bridges the canal just inside the wall

# ---- civic amenities placed FIRST so the dense packs flow around them.
s.flophouse(1330, 806, label_below=True)  # outside the NORTH gate
s.flophouse(900, 1268)  # outside the WEST river gate, on the wharf
s.block_polys.append([(1414, 952), (1512, 952), (1512, 1096), (1414, 1096)])
s.corridors.append(([(1450, 970), (1450, 1080)], 56))
s.flophouse(1450, 972, label_below=True)
s.inn(1452, 1052)
s.stables(1450, 1016, rot=90)
s.farrier(1508, 1010, rot=90)
s.block_polys.append([(1004, 1176), (1136, 1176), (1136, 1320), (1004, 1320)])
s.corridors.append(([(1040, 1200), (1040, 1300)], 50))
s.flophouse(1040, 1212, label_below=True)
s.inn(1040, 1256)
s.stables(1082, 1292, rot=90)


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
# Every free end lands ON the ring bed (a clean T) rather than a sliver short of it, and every
# street meets another - one connected network wired to the through-road.
CROSS_H = [(1130, 1150), (1670, 1150)]  # the northern E-W street, crossing the spine
MER_V = [(1200, 1090), (1200, 1330)]  # NW N-S, foot on the road
LAB_V = [(1600, 1078), (1600, 1150)]  # NE N-S, foot on the road
MAIN_E = [(1110, 1450), (1700, 1450)]  # the southern E-W street, piercing the ward fence at a kido
SW_V = [(1200, 1330), (1200, 1570)]  # SW N-S, head on the road
EAST_ST = [(1400, 1330), (1720, 1330)]  # the ward approach, piercing the fence at a kido
WARD_V = [(1650, 1330), (1650, 1450)]  # inside the ward, EAST_ST down to MAIN_E
grid([CROSS_H, MAIN_E], width_ft=22)
grid([MER_V, LAB_V, SW_V, EAST_ST, WARD_V])
# block-interior roji, laid with the streets so every quarter's terraces flow around them
alleys([[(1120, 1124), (1120, 1310)], [(1490, 1014), (1490, 1140)], [(1640, 1174), (1640, 1258)], [(1300, 1362), (1300, 1650)]])

# ====================================================================== THE EIGHT PRECINCTS
TW, TH = s.px(96), s.px(66)  # the seven siblings, ~0.70 acre drawn
IW, IH = s.px(118), s.px(80)  # Inari, the largest of the eight


def precinct(x, y, fortune, torii, w=TW, h=TH, primary=False, graveyard=False, label_below=True, torii_count=1):
    s.shrine_hall(x, y, f"Temple of {fortune}", w=w, h=h, kind="temple", primary=primary, graveyard=graveyard, label_below=label_below, torii=torii, torii_count=torii_count)
    # the caption's own ground, reserved BOTH ways: a block poly (which the packs centre-test) and
    # a corridor (which the fills honor). "Temple of Fukurokujin" is a wide box, so the band is
    # generous - labels_clear_of_other_buildings does not forgive a roof under the text.
    _ly = y + h / 2 + 15 if label_below else y - h / 2 - 15
    s.block_polys.append([(x - 62, _ly - 11), (x + 62, _ly - 11), (x + 62, _ly + 11), (x - 62, _ly + 11)])


# --- NW: the LENDING temples, by the dock and the merchant district. Ebisu (honest commerce, the
# wharf's fortune) and Fukurokujin share the moneylending trade in Fox lands, so they sit together -
# the city's one genuine temple cluster, which is why the wayside shrines gather here.
precinct(1160, 1210, "Ebisu", [(1160, 1252)], primary=True, graveyard=True)
precinct(1310, 1206, "Fukurokujin", [(1310, 1248)])
for sx, sy in [(1240, 1258), (1258, 1288), (1224, 1290)]:
    s.small_shrine(sx, sy)

# --- W: BENTEN by the dock - the water fortune, and the temple that lends against a wedding
precinct(1082, 1512, "Benten", [(1082, 1548)])

# --- N-CENTRAL: INARI, the largest of the eight. The Fox clan's own fortune - rice and foxes - and
# the temple that keeps the Inari paddy reserve whose harvest Inari shrines buy Empire-wide.
precinct(1300, 1046, "Inari", [(1300, 1074), (1300, 1081), (1300, 1088), (1300, 1095), (1300, 1102), (1300, 1109), (1300, 1116)], w=IW, h=IH, graveyard=True, torii_count=7)

# --- NE: the laborer quarter's pair
precinct(1512, 1074, "Hotei", [(1512, 1116)])
precinct(1682, 1090, "Jurojin", [(1682, 1132)])
for sx, sy in [(1556, 1064), (1572, 1098), (1538, 1108)]:
    s.small_shrine(sx, sy)

# --- SE: BISHAMON in the samurai ward - the warrior fortune
precinct(1520, 1256, "Bishamon", [(1520, 1292)])

# --- SW: DAIKOKU by the timber and charcoal ground - the fortune of wealth and stores
precinct(1268, 1490, "Daikoku", [(1268, 1532)], graveyard=True)

# ---- THE SHARED BURIAL GROUNDS. Eight precincts do NOT get eight graveyards (the five above
# declare graveyard=False): they are economic institutions holding forest usufruct, not eight
# parishes, and burial ground is constrained by suitable LAND rather than by foundation count.
s.cemetery(1232, 1042, 46, 32, label="graveyard", label_above=True)  # Inari's
s.cemetery(1046, 1246, 42, 30, label="graveyard")  # Ebisu's
s.cemetery(1338, 1516, 42, 30, label="graveyard", label_above=True)  # Daikoku's

# ---- TEMPLE FAMILY HOUSING: 6 households per precinct, drawn identical to laborer houses.
for _tx, _ty in [(1104, 1176), (1366, 1170), (1064, 1428), (1372, 1090), (1470, 1132), (1728, 1156), (1560, 1170), (1200, 1548)]:
    s.pack((_tx - 36, _ty - 22, _tx + 36, _ty + 30), ["monk_house"] * MONK_PER_PRECINCT, step=15)

# ====================================================================== SE: the governor's ward
s.governor_mansion(1570, 1545, s.px(525), s.px(300), "Governor's Mansion", gate_dir="north")
MINS = ["Ministry of Revenue", "Ministry of Retainers", "Ministry of War", "Ministry of Works", "Ministry of Justice", "Ministry of Rites"]
MIN_POS = [(1490, 1358), (1600, 1358), (1710, 1358), (1520, 1412), (1690, 1412), (1175, 1096)]
for (mx, my), name in zip(MIN_POS, MINS, strict=True):
    s.ministry(mx, my, name, w=s.px(114), h=s.px(78))
    s.corridors.append(([(mx - 22, my), (mx + 22, my)], 34))
s.mausoleum(1500, 1630, 44, 32, label="Mausoleum", gate_dir="north", label_below=True)
_CIV_I0 = len(s.block_polys)
for _m in s.M["ministries"] + [s.M["governor_mansion"]]:
    s.block_polys.append([(_m["x"] - _m["w"] / 2 - 30, _m["y"] - _m["h"] / 2 - 30), (_m["x"] + _m["w"] / 2 + 30, _m["y"] - _m["h"] / 2 - 30), (_m["x"] + _m["w"] / 2 + 30, _m["y"] + _m["h"] / 2 + 30), (_m["x"] - _m["w"] / 2 - 30, _m["y"] + _m["h"] / 2 + 30)])
_CIV_I1 = len(s.block_polys)
for _m in s.M["mausoleums"]:
    s.block_polys.append([(_m["x"] - _m["w"] / 2 - 30, _m["y"] - _m["h"] / 2 - 30), (_m["x"] + _m["w"] / 2 + 30, _m["y"] - _m["h"] / 2 - 30), (_m["x"] + _m["w"] / 2 + 30, _m["y"] + _m["h"] / 2 + 30), (_m["x"] - _m["w"] / 2 - 30, _m["y"] + _m["h"] / 2 + 30)])
for _L in s.M["labels"]:
    if len(_L) > 5 and _L[5].startswith("Ministry"):
        s.block_polys.append([(_L[0] - 15, _L[1] - 12), (_L[2] + 15, _L[1] - 12), (_L[2] + 15, _L[3] + 12), (_L[0] - 15, _L[3] + 12)])
s.martial_hall(1700, 1500, label_xy=(1700, 1503))
s.dojos([(1452, 1408), (1740, 1420)])
front([MAIN_E], (["samurai_large"] + ["samurai"] * 2) * 8, spacing=19, rows=1)
s.rowpack((1462, 1312, 1780, 1344), ["samurai"] * 30, court_every=6, eave_ft=3)
s.rowpack((1462, 1596, 1712, 1670), ["samurai"] * 30, court_every=6, eave_ft=3)
s.pack((1452, 1312, 1782, 1672), (["samurai"] * 3 + ["samurai_large"]) * 120, step=11, face_streets="fill")
s.label(1580, 1300, "samurai neighborhood", 10, italic=True, color="#3A352C")
s.ward("samurai", WARD_FENCE, gates=KIDO_SPOTS)

# ====================================================================== NE: the laborer quarter
s.block_polys.append([(1606, 1146), (1786, 1146), (1786, 1322), (1606, 1322)])
s.corridors.append(([(1660, 1232), (1730, 1232)], 62))
s.theater_stage(1694, 1232, w=s.px(210), h=s.px(146), rot=180, label="theater stage")
s.fire_tower(1636, 1076, label=None)
front([LAB_V], (["shop"] + ["laborer_large"] * 3) * 12, spacing=18, rows=1)

s.place_wells((1430, 980, 1790, 1300), spacing=54)
_lab = (["laborer"] * 4 + ["servant"]) * 140
s.rowpack((1424, 1000, 1780, 1058), _lab, court_every=5, eave_ft=3)
s.rowpack((1424, 1064, 1780, 1122), _lab, court_every=5, eave_ft=3)
s.rowpack((1424, 1170, 1596, 1226), _lab, court_every=5, eave_ft=3)
s.rowpack((1424, 1232, 1596, 1288), _lab, court_every=5, eave_ft=3)
s.rowpack((1610, 1156, 1790, 1200), _lab, court_every=5, eave_ft=3)
s.rowpack((1610, 1240, 1790, 1296), _lab, court_every=5, eave_ft=3)
s.label(1560, 1188, "laborer neighborhoods", 10, italic=True, color="#5A4326")

# ====================================================================== NW: merchants + the dock
s.fire_tower(1340, 1128, label="fire tower")

_n_est = s.merchant_estates([(1330, 1372, "north"), (1256, 1104, "east"), (1210, 1620, "east")])
_ML_SPOTS = [(1344, 1380), (1268, 1104)][_n_est - 1 :]
s.frontage([(1040, 1330), (1390, 1330)], (["merchant"] * 3 + ["shop"]) * 18, skip=ROAD, width=s.lw(26), spacing=19, rows=2, rowgap=2, jitter=1, setback=s.px(46))
front([MER_V], (["merchant"] * 3 + ["shop"]) * 10, spacing=19, rows=1)
s.place_wells((1044, 1034, 1380, 1300), spacing=54)
_mer = (["merchant_house"] * 3 + ["merchant"] + ["servant"]) * 130
s.rowpack((1044, 1040, 1140, 1096), _mer, court_every=5, eave_ft=3)
s.rowpack((1044, 1102, 1140, 1146), _mer, court_every=5, eave_ft=3)
s.rowpack((1216, 1040, 1382, 1096), _mer, court_every=5, eave_ft=3)
s.rowpack((1216, 1102, 1382, 1146), _mer, court_every=5, eave_ft=3)
s.rowpack((1044, 1170, 1382, 1226), _mer, court_every=5, eave_ft=3)
s.rowpack((1044, 1232, 1382, 1288), _mer, court_every=5, eave_ft=3)
s.merchant_storehouses(8)
s.label(1150, 1348, "merchant district", 10, italic=True, color="#5A4326")

# ====================================================================== SW: burakumin + timber ground
s.fire_tower(1150, 1400, label=None)
front([SW_V], (["burakumin"] + ["laborer"] * 2) * 14, spacing=19, rows=1)
s.place_wells((1020, 1360, 1390, 1680), spacing=54)
s.rowpack((1044, 1348, 1382, 1400), (["laborer"] * 3 + ["servant"] * 2 + ["burakumin"]) * 45, court_every=6, eave_ft=3)
s.rowpack((1044, 1404, 1382, 1440), (["laborer"] * 3 + ["servant"] * 2 + ["burakumin"]) * 45, court_every=6, eave_ft=3)
s.rowpack((1044, 1466, 1382, 1536), (["laborer"] * 2 + ["servant"] * 2 + ["burakumin"]) * 45, court_every=6, eave_ft=3)
s.rowpack((1044, 1542, 1382, 1604), (["laborer"] * 2 + ["servant"] * 2 + ["burakumin"]) * 45, court_every=6, eave_ft=3)
s.rowpack((1044, 1610, 1382, 1668), (["laborer"] * 2 + ["servant"] * 2 + ["burakumin"]) * 45, court_every=6, eave_ft=3)
s.label(1290, 1444, "burakumin", 10, italic=True, color="#6B4F2A")
# THE TIMBER AND CHARCOAL WORKING GROUND - the declared budget line, DRAWN as its kind rather than
# left as ambient slack: beaten earth with stacking rails, in the SE of the burakumin quarter where
# the raft cargo comes up from the landing.
s.animal_ground(1256, 1648, r=62, label="timber + charcoal ground")

# ====================================================================== OUTSIDE the walls
s.bound = None
# the WHARF suburb outside the river gate. The moat is CUT along the river face, so the strip
# between the east bank and the rampart is dry working ground - the raft landing for the Fox timber.
for jy in (1236, 1312, 1388):
    s.jetty(855, jy, rot=180, length=22)  # root ~14px onto the EAST bank, running WEST into the water
QUAY = [(908, 1188), (908, 1290)]
s.frontage(QUAY, ["shop"] * 16, skip=ROAD, width=s.lw(18), spacing=19, rows=2, rowgap=2, jitter=1, setback=s.px(30))
s.label(916, 1164, "wharf", 10, italic=True, color="#5A4326")
# the river gate's own approach-stall string, and the north gate's market
s.frontage([(700, 1382), (866, 1376)], ["shop"] * 8, skip=ROAD, width=s.lw(22), spacing=18, rows=1, jitter=1, setback=s.px(20), fill=True)
s.frontage([(1300, 828), (1318, 700), (1330, 624)], ["shop"] * 8, skip=ROAD, width=s.lw(22), spacing=17, rows=1, jitter=1, setback=s.px(20), fill=True)
s.label(1236, 790, "gate market", 9, italic=True, color="#5A4326")

# samurai country estates: dispersed walled compounds NORTHEAST of the city, toward Otosan Uchi.
EST = [(1960, 1010, 76, 48, "west", (2050, 1030)), (2170, 880, 84, 56, "south", (2240, 900)), (2340, 1100, 94, 62, "west", (2400, 1130))]
for ex, ey, ew, eh, gd, (_lx, _ly) in EST:
    s.manor(ex, ey, ew, eh, "", gate_dir=gd)
s.label(2010, 1070, "samurai estates", 10, italic=True, color="#3A352C")


# ====================================================================== WATER-FIRST COMB FIELDS
def _pt_seg(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    ll = vx * vx + vy * vy or 1.0
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / ll))
    return math.hypot(px - ax - t * vx, py - ay - t * vy)


def _in_poly(x, y, poly):
    n = len(poly)
    j = n - 1
    c = False
    for i in range(n):
        if ((poly[i][1] > y) != (poly[j][1] > y)) and (x < (poly[j][0] - poly[i][0]) * (y - poly[i][1]) / (poly[j][1] - poly[i][1]) + poly[i][0]):
            c = not c
        j = i
    return c


def furrows(poly, color, theta):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    fcx, fcy = sum(xs) / len(xs), sum(ys) / len(ys)
    diag = math.hypot(max(xs) - min(xs), max(ys) - min(ys))
    dx, dy = math.cos(theta), math.sin(theta)
    nx, ny = -dy, dx
    cid = s._cid("dry")
    pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in poly)
    g = [f'<clipPath id="{cid}"><polygon points="{pts}"/></clipPath>', f'<g clip-path="url(#{cid})">']
    t = -diag / 2
    while t <= diag / 2:
        mx, my = fcx + nx * t, fcy + ny * t
        g.append(f'<line x1="{mx - dx * diag / 2:.1f}" y1="{my - dy * diag / 2:.1f}" x2="{mx + dx * diag / 2:.1f}" y2="{my + dy * diag / 2:.1f}" stroke="{color}" stroke-width="0.8" opacity="0.8"/>')
        t += 5
    g.append('</g>')
    s.add(''.join(g))


def comb_field(name, sluice, down_deg, seed, field_fall, canal_a, canal_b, offtakes_a, offtakes_b=(), dry_band=(47, 88), avoid=(), dry_keepout=()):
    net = build_comb(3200, 2700, sluice, seed, down_deg=down_deg, field_fall=field_fall, canal_a_len=canal_a, canal_b_len=canal_b, offtakes_a=offtakes_a, offtakes_b=offtakes_b, plot_across=PLOT_ACROSS, row_step=ROW_STEP, dry_band=dry_band, dry_keepout=dry_keepout, grain=2 / 3)
    env = [(round(x, 1), round(y, 1)) for x, y in net["envelope"]]
    s.field_polys.append([(p[0], p[1]) for p in env])
    s.comb_base_fill(net, name, color="#CDB78C", full_envelope=True)
    _prior = [fld["outline"] for fld in s.M["fields"] if fld.get("kind") == "paddy"]
    for dp in net["dry_plots"]:
        if any(_pt_seg(x, y, ln[i][0], ln[i][1], ln[i + 1][0], ln[i + 1][1]) < 16 for ln in avoid for (x, y) in dp["poly"] for i in range(len(ln) - 1)):
            continue
        if any(hem_on_paddy(dp["poly"], _pol) for _pol in _prior):
            continue
        s.dry_polys.append(dp["poly"])
        pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in dp["poly"])
        s.add(f'<polygon points="{pts}" fill="{dp["fill"]}" stroke="#A98C58" stroke-width="1.4" stroke-linejoin="round"/>')
        furrows(dp["poly"], dp["furrow"], dp["theta"])
        s.M["dry_plots"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in dp["poly"]], "crop": dp["crop"], "theta": round(dp["theta"], 3)})
    for p in net["plots"]:
        pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in p["poly"])
        s.add(f'<polygon points="{pts}" fill="{p["fill"]}" stroke="{AZE}" stroke-width="{aze_w(s.ftpx):.2f}" stroke-linejoin="round"/>')
    s.bund_junctions(net["plots"], name)
    beads = ''.join(f'<circle cx="{x}" cy="{y}" r="1.4" fill="{BEAN_GREEN}"/>' for x, y in net["bund_beans"])
    s.add(f'<g opacity="0.85">{beads}</g>')
    for c in sorted(net["channels"], key=lambda c: -c["w"]):
        s.field_channel(c["pts"], '#7C9EB0' if c["role"] == "drain" else '#6C9CBE', c["w"], c.get("w_tail", c["w"]), late=True)
    exs = [p[0] for p in env]
    eys = [p[1] for p in env]
    pvx = [v[0] for p in net["plots"] for v in p["poly"]]
    pvy = [v[1] for p in net["plots"] for v in p["poly"]]
    s.M["fields"].append({"name": name, "kind": "paddy", "down_deg": down_deg, "outline": [[x, y] for x, y in env], "bbox": [min(exs), min(eys), max(exs), max(eys)], "vis_bbox": [min(pvx), min(pvy), max(pvx), max(pvy)], "plot_polys": [[[round(v[0], 1), round(v[1], 1)] for v in p["poly"]] for p in net["plots"]]})
    for c in net["channels"]:
        s.M["field_ditches"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in c["pts"]], "role": c["role"], "field": name, "w": round(c["w"], 1), "w_tail": round(c.get("w_tail", c["w"]), 1)})
    return net, env, (round(sum(exs) / len(exs), 1), round(sum(eys) / len(eys), 1))


def plot_centroid(net, key, inset=0.15):
    cens = [(sum(v[0] for v in p["poly"]) / len(p["poly"]), sum(v[1] for v in p["poly"]) / len(p["poly"])) for p in net["plots"] if not p.get("filler")]
    cx, cy = key(cens)
    mx = sum(c[0] for c in cens) / len(cens)
    my = sum(c[1] for c in cens) / len(cens)
    return (round(cx + inset * (mx - cx), 1), round(cy + inset * (my - cy), 1))


def topo_channel(pts, frm, to, draw_w=0.0, col='#7C9EB0'):
    ax, ay = pts[0]
    bx, by = pts[-1]
    chord = math.hypot(bx - ax, by - ay) or 1.0
    dev = max(abs((py - ay) * (bx - ax) - (px - ax) * (by - ay)) / chord for px, py in pts[1:-1]) if len(pts) > 2 else 0.0
    if dev < 6:
        k = max(range(len(pts) - 1), key=lambda i: math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]))
        mx, my = (pts[k][0] + pts[k + 1][0]) / 2, (pts[k][1] + pts[k + 1][1]) / 2
        pts = list(pts[: k + 1]) + [(mx - 12 * (by - ay) / chord, my + 12 * (bx - ax) / chord)] + list(pts[k + 1 :])
    poly = [[round(px, 1), round(py, 1)] for px, py in pts]
    s.M["channels"].append({"poly": poly, "frm": frm, "to": to, "w": draw_w or 2.5, "drawn": bool(draw_w)})
    s.corridors.append(([(px, py) for px, py in poly], 33))
    if draw_w:
        s.field_channel([(px, py) for px, py in poly], col, draw_w, draw_w)


# the moat-fed combs on the three LANDWARD faces (the river face is the wharf's dry working ground)
# down_deg points AWAY from the wall on each face - a fan falls down the slope the moat sits on
# top of, so a bearing aimed back at the city grows the paddy over the rampart and the streets.
MOAT_FARMS = [
    ("fse1", (1740, 1660), 55, 21, 185, (165, 215), (100, 135), (0.35, 0.7)),  # SE face, falling SE - downstream of its own tap
    ("fne1", (1790, 1120), 345, 22, 180, (160, 210), (95, 130), (0.4, 0.75)),  # NE face, falling NNE
    ("fe1", (1900, 1450), 10, 38, 185, (165, 215), (100, 135), (0.4, 0.78)),  # E face, falling E
    ("fs1", (1420, 1800), 85, 39, 185, (155, 200), (95, 130), (0.4, 0.75)),  # S face, falling S
    ("fsw1", (1080, 1740), 120, 44, 175, (150, 195), (92, 125), (0.4, 0.75)),  # SW face, falling SSW
]
for nm, tap, dd, sd, ff, ca, cb, oa in MOAT_FARMS:
    mp = min(MOAT, key=lambda p: (p[0] - tap[0]) ** 2 + (p[1] - tap[1]) ** 2)
    _ol = math.hypot(mp[0] - CX, mp[1] - CY) or 1.0
    sl = (round(mp[0] + 30 * (mp[0] - CX) / _ol), round(mp[1] + 30 * (mp[1] - CY) / _ol))
    _mfl = s.M["moat_flow"]
    mp = moat_swept_tap(MOAT, _mfl["inlet"], _mfl["outlet"], sl, mp)
    s.field_channel([mp, sl], '#9CB4C8', 7, 7)
    s.sluice_gate(sl[0], sl[1], rot=math.degrees(math.atan2(sl[1] - mp[1], sl[0] - mp[0])) + 90)
    _net, _env, _cen = comb_field(nm, sl, dd, sd, ff, ca, cb, oa, avoid=(MOAT,))
    _pd = plot_centroid(_net, lambda cs: max(cs, key=lambda pc: pc[1]))
    _pd = (round(0.80 * _pd[0] + 0.20 * _cen[0], 1), round(0.80 * _pd[1] + 0.20 * _cen[1], 1))
    topo_channel([(mp[0], mp[1]), sl, _pd], {"kind": "moat"}, {"kind": "field", "name": nm})
    _dr = next(c["pts"] for c in _net["channels"] if c["role"] == "drain")
    topo_channel([tuple(_dr[-2]), tuple(_dr[-1])], {"kind": "drain", "name": nm}, {"kind": "offmap"})
    s.ring(('poly', _env), 26, 15, ["plain"])
    s.ring(('poly', _env), 20, 40, ["plain"])

# the FAR-BANK fan, tapped straight off the Hayakawa - the paddy country running on west beyond the
# frame (city_has_outside_farmland wants at least one field off the map edge).
_netw, ENV_FW, _cw = comb_field("fw1", (660, 940), 190, 43, 190, (170, 220), (105, 140), (0.4, 0.75), avoid=(MOAT,))
_pw = plot_centroid(_netw, lambda cs: max(cs, key=lambda c: c[0]))
topo_channel([(810, 920), (660, 940), _pw], {"kind": "river"}, {"kind": "field", "name": "fw1"})
s.field_channel([(810, 920), (660, 940)], '#9CB4C8', 7, 7)
s.sluice_gate(660, 940, rot=math.degrees(math.atan2(20, -150)) + 90)
_drw = next(c["pts"] for c in _netw["channels"] if c["role"] == "drain")
_dwx, _dwy = _drw[-1]
topo_channel([(_dwx, _dwy), (200, _dwy + 40)], {"kind": "drain", "name": "fw1"}, {"kind": "offmap"}, draw_w=4.0)
s.ring(('poly', ENV_FW), 24, 15, ["plain"])
s.ring(('poly', ENV_FW), 18, 40, ["plain"])

# THE DEAD CROSS THE RIVER: the funerary complex on the far bank, DOWNSTREAM of the city and south
# of the bridge road. The moat's water set-back leaves no dry landward fringe, and bearing the dead
# over the water suits the geography of the afterlife. Burial set-back: the Hayakawa is a wide
# stream, so a burial ground's corners sit >= 160px off its centerline (cremation is exempt at 30).
s.cemetery(600, 1700, 92, 66, parish=False, label="common burial ground")
s.cremation_ground(604, 1800)
s.ossuary(596, 1614)

s.boundary_marker(742, 1358)  # ON the west road verge, where the road leaves clean ground
s.execution_ground(642, 1374, rot=6, label_above=True)

s.bridges()
s.farmsteads()
s.farm_wells()


# ====================================================================== the dwelling top-up
def top_up(kind, region, need, count_kinds=None):
    kinds = set(count_kinds or (kind,))
    have = sum(1 for b in s.M["buildings"] if b["kind"] in kinds)
    w_, h_ = s._dims(kind)
    gov = s.M.get("governor_mansion")
    civ = [(m["x"], m["y"], m["w"], m["h"]) for m in s.M.get("ministries", [])]
    if gov:
        civ.append((gov["x"], gov["y"], gov["w"], gov["h"]))
    labs = [tuple(lb[:4]) for lb in s.M.get("labels", [])]
    stab = [(b["x"], b["y"]) for b in s.M.get("buildings", []) if b.get("kind") == "stables"]

    def ok(gx, gy):
        if not _in_poly(gx, gy, WALL):
            return False
        if any(abs(gx - cx) <= (cw + w_) / 2 + 15 and abs(gy - cy) <= (ch + h_) / 2 + 15 for cx, cy, cw, ch in civ):
            return False
        if any((gx - sx) ** 2 + (gy - sy) ** 2 < 85**2 for sx, sy in stab):
            return False
        return not any(min(x1_, gx + w_ / 2 + 2) - max(x0_, gx - w_ / 2 - 2) > 0 and min(y1_, gy + h_ / 2 + 2) - max(y0_, gy - h_ / 2 - 2) > 0 for x0_, y0_, x1_, y1_ in labs)

    def exact_clear(gx, gy):
        if s._in_blocked(gx, gy) or s._near_corridor(gx, gy):
            return False
        if s.bound and not _in_poly(gx, gy, s.bound):
            return False
        if any(abs(gx - w2["x"]) < 26 and abs(gy - w2["y"]) < 26 for w2 in s.M.get("wells", [])):
            return False
        if not all(abs(gx - px) >= (w_ + pw) / 2 + 3 or abs(gy - py) >= (h_ + ph) / 2 + 3 for (px, py, pw, ph) in s.placed):
            return False
        for o in s.M["buildings"] + s.M["houses"]:
            if "w" not in o or abs(gx - o["x"]) > 42 or abs(gy - o["y"]) > 42:
                continue
            oth = math.radians(o.get("rot", 0))
            oc, os_ = abs(math.cos(oth)), abs(math.sin(oth))
            if abs(gx - o["x"]) < (w_ + oc * o["w"] + os_ * o["h"]) / 2 + 3 and abs(gy - o["y"]) < (h_ + os_ * o["w"] + oc * o["h"]) / 2 + 3:
                return False
        return True

    def door_clear(gx, gy, rot):
        dc = (7.0 / 3) * 1.15
        th = math.radians(rot)
        ux, uy = -math.sin(th), math.cos(th)
        vx, vy = -uy, ux
        fx, fy = gx + ux * h_ / 2, gy + uy * h_ / 2
        rr = math.hypot(w_, h_) / 2 + dc + 2
        for o in s.M["buildings"] + s.M["houses"]:
            if "w" not in o:
                continue
            if math.hypot(o["x"] - gx, o["y"] - gy) > rr + math.hypot(o["w"], o["h"]) / 2:
                continue
            oth = math.radians(o.get("rot", 0))
            c_, sn = math.cos(oth), math.sin(oth)
            corners = [(o["x"] + c_ * dx - sn * dy, o["y"] + sn * dx + c_ * dy) for dx, dy in ((-o["w"] / 2, -o["h"] / 2), (o["w"] / 2, -o["h"] / 2), (o["w"] / 2, o["h"] / 2), (-o["w"] / 2, o["h"] / 2))]
            for d_ in (0.8, dc * 0.55, dc):
                for t_ in (-0.3 * w_, 0.0, 0.3 * w_):
                    if _in_poly(fx + ux * d_ + vx * t_, fy + uy * d_ + vy * t_, corners):
                        return False
        return True

    x0, y0, x1, y1 = region
    for pad in (7, 4, "exact"):
        gy = y0
        while gy <= y1 and have < need:
            gx = x0
            while gx <= x1 and have < need:
                if ok(gx, gy) and (exact_clear(gx, gy) if pad == "exact" else s._fits(gx, gy, w_ + pad, h_ + pad)):
                    orot = next((r_ for r_ in (0.0, 180.0) if door_clear(gx, gy, r_)), None)
                    if orot is not None:
                        s.building(gx, gy, w_, h_, kind, orot)
                        have += 1
                gx += 5
            gy += 6
        if have >= need:
            break
    return have


DWELL = ("laborer", "laborer_large", "servant", "burakumin", "merchant", "merchant_house", "merchant_large", "samurai", "samurai_large", "monk_house")


def _dwell_count():
    return sum(1 for b in s.M["buildings"] if b["kind"] in DWELL)


# civic aprons, PHASE 2: the pack is done, so the ministry/yamen aprons drop 30 -> 16 and the
# axis-aligned fills (whose own ok() enforces a 15px AABB office gap) may claim the tight bands.
# Replaced IN PLACE, index for index - the _poly_bboxes cache invalidates on list LENGTH only.
for _ci, _m in zip(range(_CIV_I0, _CIV_I1), s.M["ministries"] + [s.M["governor_mansion"]], strict=True):
    s.block_polys[_ci] = [(_m["x"] - _m["w"] / 2 - 16, _m["y"] - _m["h"] / 2 - 16), (_m["x"] + _m["w"] / 2 + 16, _m["y"] - _m["h"] / 2 - 16), (_m["x"] + _m["w"] / 2 + 16, _m["y"] + _m["h"] / 2 + 16), (_m["x"] - _m["w"] / 2 - 16, _m["y"] + _m["h"] / 2 + 16)]

NE_Q = (1424, 968, 1790, 1258)
NW_Q = (1030, 1030, 1386, 1312)
SW_Q = (1044, 1366, 1386, 1660)
SE_Q = (1452, 1312, 1782, 1672)

_MERCH = ("merchant", "merchant_house", "merchant_large")
_LAB = ("laborer", "laborer_large")
# the wealthier 'master' cohort FIRST, into gaps the plain fill would otherwise claim (budgets.md
# puts ~12.5% of laborers in larger homes; city_laborer_housing_varied wants 6-20%)
top_up("samurai_large", SE_Q, 6)
top_up("laborer_large", NE_Q, 18)
top_up("laborer_large", SW_Q, 24)
# then each caste to its budgets.md target across every quarter that can hold it
for _kind, _regions, _target, _ck in (
    ("samurai", (SE_Q,), 52, ("samurai", "samurai_large")),
    ("merchant_house", (NW_Q, SW_Q), 130, _MERCH),
    ("burakumin", (SW_Q,), 26, ("burakumin",)),
    ("laborer", (NE_Q, SW_Q, NW_Q), 208, _LAB),
    ("servant", (NW_Q, NE_Q, SW_Q, SE_Q), 104, ("servant",)),
):
    for _region in _regions:
        if sum(1 for b in s.M["buildings"] if b["kind"] in _ck) >= _target:
            break
        top_up(_kind, _region, _target, count_kinds=_ck)
# the temple families, wherever a precinct's own pack could not seat all six
for _tx, _ty in [(1104, 1176), (1366, 1170), (1064, 1428), (1372, 1090), (1470, 1132), (1728, 1156), (1560, 1170), (1330, 1444)]:
    top_up("monk_house", (_tx - 60, _ty - 46, _tx + 60, _ty + 54), 48)
# whole-interior sweeps: the per-quarter regions leave ground stranded at their seams, and the
# budget promises 520 dwellings, so the last passes are limited by the ground and nothing else.
ALL_Q = (1032, 980, 1800, 1690)
top_up("merchant_house", ALL_Q, 130, count_kinds=_MERCH)
top_up("laborer", ALL_Q, 208, count_kinds=_LAB)
top_up("servant", ALL_Q, 104)
top_up("samurai", SE_Q, 52, count_kinds=("samurai", "samurai_large"))
top_up("burakumin", SW_Q, 26)
for _pass in range(2):
    top_up("merchant_house", ALL_Q, 130, count_kinds=_MERCH)
    top_up("servant", ALL_Q, 104)
    top_up("laborer", ALL_Q, 208, count_kinds=_LAB)

for _mx, _my in _ML_SPOTS:
    s.building(_mx, _my, *s._dims("merchant_large"), "merchant_large")

# FINE global well pass: after every dwelling is placed, drop wells into the nearest clear COURT.
s.place_wells((1424, 968, 1730, 1250), spacing=42, near=48)
s.place_wells(NW_Q, spacing=42, near=48)
s.place_wells(SW_Q, spacing=42, near=48)
s.place_wells((1440, 960, 1720, 1240), spacing=46, near=48)
s.place_wells((1020, 1020, 1382, 1300), spacing=46, near=48)
s.place_wells((1020, 1370, 1382, 1670), spacing=46, near=48)

s.crop_city(margin=30, west=70)
s.title("Minami")

# ===== THE OFFICIAL NOTICE BOARDS - a city draws the SET: the principal board at the central
# market node plus one on every main gate's approach. Only ONE carries the label.
s.kosatsuba(1424, 1348, rot=90)
s.kosatsuba(1384, 974, rot=78, label=None)  # the north gate's board, on the road verge inside
s.kosatsuba(1016, 1348, rot=0, label=None)  # the river gate's board

s.place_punishment_spot()

HERE = os.path.dirname(os.path.abspath(__file__))
nb = {}
for b in s.M["buildings"]:
    nb[b["kind"]] = nb.get(b["kind"], 0) + 1
print("farmhouses:", len(s.M["houses"]), "| buildings:", nb, "| total urban:", sum(nb.values()), "| dwellings:", _dwell_count(), "| finish:", s.finish(os.path.join(HERE, "minami")))
