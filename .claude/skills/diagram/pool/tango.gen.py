#!/usr/bin/env python3
"""Tango - a walled PROVINCIAL CITY (diagram skill, Mode B, city scale).

Historical model: a Chinese walled provincial seat / Japanese jokamachi - a closed MOATED
rampart sized to hug the ~600-household city (a wall encloses what it must defend, no large
unused ground inside), with the Imperial road as the N-S spine and a connected GRID of city
streets dividing each quarter into blocks. Within a block the street-facing buildings front
the streets and the bulk of the housing packs into TIGHT ROWS behind them. The placement is
bounded by the wall (s.bound), so the dense quarters fill the ring's shape to the rampart.

The four quarters (split by the road and an E-W axis):
  - NW: the (uncharacteristic) AGRICULTURAL district - in-wall fields fed by an in-wall pond,
        plus the city's in-wall BURAKUMIN neighborhood (siege need).
  - NE: the LABORER neighborhoods, gridded blocks of tight tenement rows.
  - SW: the MERCHANT district + a TEMPLE neighborhood (Temples of Benten + Daikoku, the Crane
        patron fortunes) holding the Ministry of Rites that oversees them.
  - SE: the provincial GOVERNMENT (governor's mansion + five of the six ministries) and the
        SAMURAI neighborhood, with a Temple of Bishamon (the warrior fortune) among them.
Wealthy samurai keep walled ESTATES of varying size outside the SE wall and commute in. All
six ministries (Rites, Revenue, Retainers, War, Works, Justice) appear; civic amenities ported
from the town tier: merchant-house kura, a market flophouse, an amphitheater.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settlement import Settlement  # noqa: E402

s = Settlement(3200, 2700, seed=71)
s.meta(name="Tango", scale="city", walled=True, agricultural_district=True, population=3000)   # ~600 dwellings x5; the shops/civic/government buildings are EXTRA, not housing
s.bscale = 0.42

# ---- the closed rampart (a near-elliptical ring) sized to hug the city, with N and S gates
CX, CY, RX, RY = 1600, 1330, 840, 780
NRING = 22
WALL = [(round(CX + RX * math.cos(-math.pi / 2 + 2 * math.pi * i / NRING)),
         round(CY + RY * math.sin(-math.pi / 2 + 2 * math.pi * i / NRING))) for i in range(NRING)]
NGATE, SGATE = WALL[0], WALL[NRING // 2]
s.city_wall(WALL, gates=[NGATE, SGATE])
MOAT = s.moat(WALL, gap=42)
# a ring road (順城街) hugs the inside of the wall, leaving the wall-clear patrol zone; the quarters
# pack INSIDE it (s.bound = the ring loop), off the rampart
RING = s.ring_road(WALL, inset=34)
s.bound = [list(p) for p in RING]            # placement stays inside the ring road, off the wall
# crop the rendered map tight to the walled city - a city map is about the city, not its
# countryside, so estates and farmland run off the edge. A ~50px margin past the moat leaves
# room for the title (top-left) and compass (top-right) above the rampart.
MARGIN = 50
s.set_view(CX - RX - 52 - MARGIN, CY - RY - 52 - MARGIN, 2 * (RX + 52 + MARGIN), 2 * (RY + 52 + MARGIN))

# ---- the Imperial road (N-S spine, off both edges, through both gates), the moat-feeder, gates
# the label names the IMPERIAL road - placed OUTSIDE the north gate; inside the walls the same
# roadway is a city street (a city, not Imperial, responsibility), so the label must sit beyond a gate
IMPROAD = [(1600, -40), (1600, CY - RY), (1600, 1330), (1600, CY + RY), (1600, 2740)]
s.road(IMPROAD, label="Imperial Road", label_xy=(1740, 478))
_mnw = min(MOAT, key=lambda p: (p[0] - 1000) ** 2 + (p[1] - 740) ** 2)   # a moat vertex on the NW
s.stream([(640, -40), (740, 230), (850, 470), (_mnw[0], _mnw[1])])       # off-map NW source feeding the moat

# civic amenities placed FIRST, in the open central cross, so the dense packs flow around them
s.amphitheater(1450, 1030, 102, label="amphitheater")        # a leisure ground near the center; a CITY amphitheater is larger than a town's (~50% bigger)
s.flophouse(1430, 484, w=92, h=42, label_below=True)         # outside the NORTH gate (arrivals from the north); labels below so its label stays below the cropped image's top edge
s.flophouse(1820, 2188, w=92, h=42)                          # outside the SOUTH gate, by the gate market
# CARAVAN facilities just INSIDE each gate (a transit zone): a flophouse + a prominent INN + a large
# STABLES with open ground around them for the wagon-trains' draft animals (oxen/horses) and crews.
# N gate (1600,550): in the open agrarian-edge between the fields (west) and the road, north of the amphitheater.
# the flophouse labels BELOW itself (south, into the cluster) so its label clears the gate guard house
# /inspection furniture just north of it, and the cluster sits low enough that the guard-house label
# (drawn at the gate) doesn't clip the flophouse roof
s.flophouse(1480, 672, w=88, h=42, label_below=True)
s.inn(1510, 762)
s.stables(1505, 847)
# S gate (1600,2110): stacked west of the road, east of the temple neighborhood, above the gate guard house.
# labels BELOW so its label clears the merchant estate to its north-west
s.flophouse(1530, 1830, w=88, h=42, label_below=True)
s.inn(1530, 1910)
s.stables(1530, 1988)


def grid(streets, width=18):
    for st in streets:
        s.street(st, width=width)


def front(streets, kinds, width=18, spacing=44, rows=1):
    # rows of buildings parallel to and DIRECTLY against each street (the front row tight on the
    # street, deeper rows stacked behind it) - the machiya pattern: street line + tenement depth
    for st in streets:
        s.frontage(st, list(kinds), width=width, spacing=spacing, rows=rows)


def alleys(lst):
    # unpaved gravel lanes subdividing the big street-blocks: the jammed interior housing is
    # reached by these, not the paved streets
    for a in lst:
        s.alley(a)


# ====================================================================== NW: agricultural
s.pond(1250, 1050, 74, 46)               # well inside the wall, between the fields and the burakumin lane
NW1, NW2 = (940, 985, 1130, 1140), (1130, 760, 1340, 930)
s.channel((1240, 1050), (1010, 1050), {"kind": "pond"}, {"kind": "field", "name": "nw1"})
s.channel((1250, 1015), (1300, 860), {"kind": "pond"}, {"kind": "field", "name": "nw2"})
s.paddy_field(NW1, "", "nw1", amp=22)
s.paddy_field(NW2, "", "nw2", amp=20)
s.ring(NW1, 7, 16, ["plain"])
s.ring(NW2, 7, 16, ["plain"])
s.label(1080, 1010, "agricultural district", 11, italic=True, color="#5A6A2A")
# the in-wall burakumin neighborhood (its lane reaches the Imperial road, wiring it to the grid)
# a FEW shops/stalls front the lane; the burakumin dwellings jam the block interior behind them
BUR_ST = [[(803, 1230), (1600, 1230)], [(1230, 1180), (1230, 1320)]]   # E-W lane reaches the road
grid(BUR_ST)
alleys([[(980, 1185), (980, 1310)], [(1400, 1185), (1400, 1310)]])   # gravel lanes BEFORE the buildings, clear of the NW field rings
front(BUR_ST, ["shop"] * 12, spacing=78, rows=1)
# the burakumin draw from their OWN wells (status segregation extended to shared water) - a couple
# serve the quarter; placed before the pack so the dwellings flow around them. The shallow lane-split
# quarter is too lane-laced for the grid, so the wells are hand-seeded into the courtyard gaps off
# the E-W lane (y1230) and the alleys (x980, x1400); well_at no-ops any candidate that isn't clear.
for wx, wy in [(870, 1288), (1100, 1288), (1500, 1288), (870, 1180), (1100, 1180), (1490, 1180)]:
    s.well_at(wx, wy)
s.pack((780, 1140, 1560, 1320), (["burakumin"] * 2 + ["servant"]) * 18, step=19, face_streets="fill")   # shallow quarter: fill it (servants INTERLEAVED, not starved at the end)
s.label(1180, 1255, "burakumin neighborhood", 11, italic=True, color="#6B4F2A")

# ====================================================================== NE: laborers (FEW streets, DEEP blocks)
# a laborer quarter is the LEAST mercantile: only a couple of through-streets (shops front them),
# and the laborer dwellings pack many rows DEEP into the block interiors behind the frontage
NE_ST = [[(1600, 950), (2280, 950)], [(2000, 690), (2000, 1290)]]    # 1 E-W + 1 N-S, crossing; E-W meets the Imperial road at x1600; N-S reaches the gap-fill alley below (y1290)
grid(NE_ST)
# gravel alleys subdivide the two big street-blocks into the fine warren the laborers pack into;
# placed BEFORE the buildings (so none sit on a lane) and clipped INSIDE the wall (the NE rampart curves in).
# ONE lane per block is enough to reach its interior: the WEST blocks share a single continuous
# vertical spine (x1810), so they carry no redundant horizontal cross-alley (a perpendicular arm the
# spine already reaches makes a lane that earns nothing); the EAST block keeps its own L.
alleys([[(1810, 950), (1810, 1290)], [(1810, 950), (1810, 740)],            # the west spine (full height, both west blocks)
        [(2190, 950), (2190, 1290)], [(2000, 1130), (2260, 1130)]])         # the east block's L
# the street-FRONTING laborer dwellings are the wealthier "master" (rich) laborers (~12.5% of the cohort
# per budgets.md): larger homes on the prime back-street frontage, with room on each side - the standard
# poorer laborers jam the block interiors behind them (below). A few shops front too.
front(NE_ST, ["shop"] * 8 + ["laborer_large"] * 28, spacing=46, rows=1)
# the laborer warren is the DENSEST quarter, so it carries the most wells - a communal well in the
# interior of each tenement cluster (off the lanes), the idobata around which the warren's life turned
s.place_wells((1660, 640, 2400, 1280), spacing=120)
# the dense WEST edge of the warren (x1720 column) is the busiest, so seed a couple more wells there
for wx, wy in [(1690, 1250), (1690, 770), (1840, 1300)]:
    s.well_at(wx, wy)
s.pack((1640, 600, 2420, 1300), (["laborer"] * 3 + ["servant"]) * 84, step=14, face_streets="core")   # laborers + their servants INTERLEAVED (~3:1), not laborers-then-a-starved-servant-tail
s.label(2010, 820, "laborer neighborhoods", 11, italic=True, color="#5A4326")

# ====================================================================== SW: merchants
# A mercantile quarter, but its HOUSING contrasts sharply with the laborers' (uniform, small, jammed):
# merchant homes are VARIED and SPREAD OUT. The EAST half keeps a fine commercial street grid with
# storefronts; the WEST half is a roomier enclave of the WEALTHY - walled estates and large homes with
# air between them. Sizes follow budgets.md's provincial-city merchant wealth bands (of ~600 households:
# very rich 8% -> walled estates, rich 12% -> large houses, poor+other 80% -> small/average houses).
AVENUE = [(1600, 1500), (828, 1500)]   # ONE object, reused for both s.street and the frontage below, so the frontage's `skip` matches the avenue's registered corridor and the storefronts sit TIGHT against it (a fresh literal would not match -> the storefronts would be blocked off the avenue by its own corridor)
s.street(AVENUE, width=22, main=True)   # main commercial avenue, reaches the road
SW_ST = [[(1010, 1500), (1010, 1830)], [(1300, 1370), (1300, 1920)]]   # two N-S streets off the avenue; x1300 fronts Rites
grid(SW_ST, width=18)   # deep TOP-TO-BOTTOM blocks (storefronts front the avenue + these), cores left for homes
# the temple neighborhood (lower SW, INSIDE the wall): Benten + Daikoku with the Ministry of
# Rites that oversees them - placed BEFORE the merchant pack so it flows around them
s.shrine_hall(1150, 1846, "Temple of Benten", w=124, h=80, kind="temple", primary=True)
s.shrine_hall(1418, 1916, "Temple of Daikoku", w=124, h=80, kind="temple")   # stands off the Ministry of Rites to its west (a government office must not abut a neighbor)
s.ministry(1290, 1952, "Ministry of Rites")   # nudged clear of the ring road (the SW ring runs just west of here)
# a smattering of small wayside shrines dot the temple neighborhood (non-residential), tucked in the
# gaps around the two temples - placed BEFORE the packs so the homes flow around them
for sx, sy in [(1145, 1900), (1190, 1930), (1340, 1860), (1400, 2000)]:
    s.small_shrine(sx, sy)
s.label(1040, 1840, "temple neighborhood", 10, italic=True, color="#6B2A18")
front([AVENUE] + SW_ST, (["merchant"] * 2 + ["shop"]) * 20, width=20, spacing=46, rows=2)
# Behind the storefronts, the merchants' HOMES - VARIED and SPREAD OUT (vs the laborers: uniform, small,
# jammed). Sizes follow budgets.md's provincial-city merchant wealth bands (of ~600 households: very rich
# 8% -> WALLED ESTATES, rich 12% -> LARGE houses, poor+other 80% -> small/average houses). A few WALLED
# ESTATES of the very-rich sit deep in the MIDDLE + EAST block cores (placed first; the home packs flow
# around them) - well clear of the west wall/moat, the temples below, and the streets' storefront bands.
# (x, y, gate_dir) - the gate must open onto OPEN ground, never into a neighbor; the estate abutting
# the Temple of Benten (below it) opens its gate NORTH instead of south into the temple.
EST = [(1155, 1635, "south"), (1155, 1740, "north"), (1460, 1635, "south"), (1460, 1775, "south")]
for ex, ey, gd in EST:
    s.merchant_estate(ex, ey, gate_dir=gd)
# large + small homes (+ the merchants' live-in servants), INTERLEAVED so the placed mix stays varied,
# packed LOOSELY (big step => air between houses) so the quarter reads roomier than the laborer warren.
HOMES = (["merchant_house"] * 3 + ["merchant_large"] + ["merchant_house"] * 2 + ["servant"] + ["merchant_house"] * 2 + ["servant"]) * 12
# the merchant quarter is wealthier (some homes have private wells), so fewer communal ones than the
# laborer warren - a scattering through the home blocks, clear of the estates and temples below
s.place_wells((800, 1580, 1540, 1840), spacing=150)
s.pack((770, 1560, 1560, 1860), HOMES, step=29, face_streets="fill")
# the merchant quarter EXTENDS NORTH into the band between the avenue and the burakumin lane - a provincial
# city is ~25% merchant (~150 of 600 households), too many to fit below the avenue alone, so this prime
# central ground (otherwise an odd empty gap by the road) fills with their small homes + live-in servants
s.place_wells((820, 1345, 1280, 1480), spacing=150)
s.pack((790, 1330, 1300, 1495), (["merchant_house"] * 4 + ["servant"]) * 28, step=18, face_streets="fill")
s.label(1120, 1600, "merchant district", 11, italic=True, color="#5A4326")

# ====================================================================== SE: government + samurai
# the governor's YAMEN - the grandest compound in the city (a whole city block; its dozens of
# interior buildings are a separate Mode A diagram), placed clear of the rampart in the SE
s.governor_mansion(1950, 1758, 248, 168, "Governor's Mansion", gate_dir="west")
# Bishamon (the warrior fortune) sits in the government district and FRONTS the western end of the
# government avenue - filling what would otherwise be a bare gated approach between the ward gate and
# the first ministry. Its torii still stands on the samurai-quarter street that runs up to it.
s.shrine_hall(1700, 1625, "Temple of Bishamon", w=120, h=80, kind="temple", torii=[(1740, 1712)])
# the five other ministries CLUSTER around the yamen (the government district), as in a Chinese
# provincial seat / Japanese castle town (Rites is apart, in the SW temple neighborhood)
MINS = ["Ministry of Revenue", "Ministry of Retainers", "Ministry of War",
        "Ministry of Works", "Ministry of Justice"]
# the government avenue: a planned city's offices FRONT its streets, so the ministries LINE an
# avenue around the yamen (an L wrapping its north + east), wired to the Imperial road on the west
grid([[(1600, 1550), (2150, 1550)], [(2150, 1550), (2150, 1863)]], width=18)   # avenue reaches the road (W) + flows into the ring road (S, at the SE wall)
MIN_POS = [(1830, 1600), (1960, 1600), (2090, 1600), (2210, 1636), (2205, 1720)]   # Works + Justice stand clear of each other (a government office must not abut its neighbor); Justice clear of the ring road
for (mx, my), name in zip(MIN_POS, MINS):
    s.ministry(mx, my, name)
# the samurai neighborhood wraps the government compounds; a small street grid west of the yamen,
# clear of the ministries (which now column up the east side of the governor's compound)
SAM_ST = [[(1600, 1780), (1800, 1780)], [(1680, 1980), (1800, 1980)], [(1740, 1700), (1740, 1980)]]   # E-W reaches the road, piercing the ward fence; x1740 ends AT the y1980 street
grid(SAM_ST, width=18)
# houses vary in size by rank: ~1-in-4 is a large senior house (samurai_large) among the small junior
# ones, mirroring budgets.md's provincial-city rank split (~25% senior R5-7 / ~75% junior R1-4). The
# wealthiest samurai live on walled country estates OUTSIDE the walls, not here. Senior houses front
# the streets prominently.
SAM_MIX = (["samurai"] * 3 + ["samurai_large"]) * 20
front(SAM_ST, SAM_MIX[:38], spacing=54, rows=2)
# samurai both FRONT the quarter's streets and FILL behind them (face_streets="fill"); a small
# city's ~300 samurai (~10% of 3,000, budgets.md) need ~60 households, most housed here (the rest in
# the governor's compound + the extramural estates). "core" was wrong - it skips the near-street band,
# but this quarter is laced with streets, so it left almost everything unbuilt.
s.pack((1610, 1600, 2440, 2110), (["samurai"] * 8 + ["samurai_large"]) * 96, step=12, face_streets="fill")
s.label(1850, 1990, "samurai neighborhood", 11, italic=True, color="#3A352C")
# the samurai/government WARD: a continuous earthwork fence (W + N), ends abutting the city wall,
# so the kido gates can't be walked around - the only ways in are the two gated street crossings.
# (A small city GATES its wards; continuous walled wards are a great-capital / Tang feature.)
# the W leg runs straight down at x1620, then JOGS east (below the samurai blocks) to abut SOLID wall
# at x1670 - clear of the south gate opening at x1600, so the fence end meets the rampart, not the gap.
s.ward("samurai", [(1670, 2096), (1620, 2040), (1620, 1535), (2401, 1535)],
       gates=[(1620, 1550, True), (1620, 1780, True),   # avenue + samurai street pierce the W fence
              (1810, 1535, False), (2000, 1535, False), (2190, 1535, False),   # the 3 commoner verticals enter the N fence at kido gates
              (2366, 1535, False), (1646, 2069, True)])   # the RING ROAD crosses the fence here (E and SW) - gate it so the ward's patrol stretch is sealed off from the commoners'
s.label(1648, 1524, "samurai ward gate", 9, italic=True, color="#5A4326")
# fill the band between the NE laborer quarter and the SE quarter (no large empty ground in a city)
# - laced with gravel alleys so the block is reachable (no giant cluster cut off from circulation)
# the three vertical lanes CONTINUE the NE laborer verticals above (same x, no gap) - lanes heading
# straight at each other with clear ground between should connect, not stop short (city_lanes_meet_when_aligned);
# their lower ends stop just NORTH of the ward fence (y1535), which legitimately blocks them
# the three verticals run all the way DOWN to the samurai ward fence (y1535) and end at KIDO GATES
# there (added to s.ward below) - the commoners' lanes pull in to the gates they pass through to work
# in the samurai quarter, rather than stopping a sliver short (city_lanes_reach_ward_gates)
alleys([[(2000, 1290), (2000, 1535)], [(1700, 1440), (2396, 1440)],   # x2000 meets the N-S laborer street (y1290) -> ward gate (y1535); the E-W lane runs EAST to MEET the ring road (~x2396), not stopping short of it
        [(1810, 1290), (1810, 1535)], [(2190, 1290), (2190, 1535)]])  # x1810/x2190 meet the NE alleys (y1290) -> ward gates (y1535)
# this gap-fill laborer band also needs wells - hand-seeded into the courtyards between the vertical
# alleys (x1810/x2000/x2190), in the strips above and below the y1440 cross-alley
for wx in (1700, 1825, 1910, 2040, 2130, 2270, 2350):
    for wy in (1390, 1490):
        s.well_at(wx, wy)
s.pack((1660, 1330, 2400, 1520), (["laborer"] * 3 + ["servant"]) * 60, step=14, face_streets="core")

# ====================================================================== OUTSIDE the walls
s.bound = None
# wealthy samurai walled estates - all to the SE, beyond the moat, SCATTERED and varying in size.
# The inner ones STRADDLE the cropped SE edge (partly shown) so the map signals several estates;
# the rest run off-map entirely (a city map is about the city, not its commuter belt).
EST = [(2600, 1500, 200, 130), (2540, 1700, 190, 124), (2470, 1900, 184, 120),   # straddle the edge
       (2330, 2180, 180, 116), (2860, 1620, 168, 112), (3060, 1780, 150, 100),    # off-map beyond
       (2900, 2000, 160, 106), (2780, 2240, 150, 100)]
for ex, ey, ew, eh in EST:
    s.manor(ex, ey, ew, eh, "")
s.label(2470, 1620, "samurai estates", 11, italic=True, color="#3A352C")   # kept off the right image edge
# surrounding farmland: large fields CLOSE to the city, irrigated from the MOAT, each ringed by the
# villagers' farmhouses; all run off the map edge (their houses ring the on-map part). The moat is fed
# from the NORTH (the stream), so its water flows SOUTH - each moat channel taps a vertex UPSTREAM
# (north) of its field so the channel runs WITH the current (never field-into-moat). The fields sit W,
# SW and S of the city - all downstream of their taps. Channels first, so each field paints over its end.
MOAT_FARMS = [((-200, 930, 640, 1210), "fw1", (470, 1060)), ((300, 1330, 680, 1640), "fw2", (470, 1480)),
              ((900, 2150, 1300, 2560), "fs1", (1100, 2320))]
for fbb, nm, fin in MOAT_FARMS:                              # channels first (each field paints over its end)
    upstream = [p for p in MOAT if p[1] < fin[1] - 20]       # moat vertices NORTH of the field (upstream of the southward current)
    mp = min(upstream, key=lambda p: (p[0] - fin[0]) ** 2 + (p[1] - fin[1]) ** 2)
    s.channel((mp[0], mp[1]), fin, {"kind": "moat"}, {"kind": "field", "name": nm})
# a field running off the NORTH edge - its water is implied off-map (the moat's own source side). It is
# NOT moat-fed: a field north of the moat is UPHILL of the southward current, so the moat cannot feed it.
NORTH_FARM = ((1000, -100, 1300, 500), "fn1", (1180, 280))
for fbb, nm, fin in MOAT_FARMS + [NORTH_FARM]:
    s.paddy_field(fbb, "", nm, amp=24)
    # ring the WHOLE field - most farmhouses fall off-map (the field is mostly off-edge), but enough
    # land on the on-map edge to show the worked frontage at ~village density. Farmers live outside
    # the walls, so these do NOT count toward the city's in-wall population.
    s.ring(fbb, 40, 15, ["plain"])
    s.ring(fbb, 34, 40, ["plain"])
# label the moat-irrigated farmland on the VISIBLE south field (fs1), which runs off the bottom edge -
# the old west placement (360,690) fell outside the cropped view entirely
s.label(1100, 2185, "farmland (moat-irrigated; off-map beyond)", 10, italic=True, color="#5A6A2A")
# a gate market just outside the south gate, beyond the moat - the rows nearest the gate fall
# inside the cropped view, the rest run off the south edge
s.pack((1450, 2175, 1770, 2400), (["merchant"] * 2 + ["shop"]) * 4, step=46)
s.label(1640, 2198, "gate market", 10, italic=True, color="#5A4326")

# deep-lot kura tucked behind shopfronts that have an open back lot (the narrow-front / deep-lot
# merchant compound) - placed last, once every business across the city is down
s.merchant_storehouses(10)

# COMMERCIAL RIBBON along the Imperial road - a city ON a trade route lines its through-road with
# shops + traveler services (its prime frontage), unlike a city with no road. Two road-markets fill
# the otherwise-dead road frontage: the MAIN one in the open block between the burakumin quarter and
# the merchant avenue, and a smaller one inside the N gate (greeting northern arrivals beside the
# caravan inn/stables). Placed LAST, after every quarter, so they flow into the gaps and perturb no
# RNG-seeded pack upstream (city_imperial_road_has_commerce).
s.inn(1410, 1372)                                                        # a roadside inn anchoring the central road-market
# WEST side - the central road-market block (between the burakumin quarter and the merchant avenue)
s.frontage([(1600, 1320), (1600, 1500)], (["shop"] * 2 + ["merchant"]) * 4, skip=IMPROAD, both=False, width=22, spacing=28, rows=2)
s.pack((1360, 1340, 1545, 1500), (["shop"] * 3 + ["merchant"] + ["shop"] * 2) * 4, step=28, face_streets="fill")
# WEST side - a smaller road-market just inside the N gate (greeting northern arrivals, beside the caravan inn/stables)
s.frontage([(1600, 585), (1600, 775)], ["shop"] * 6, skip=IMPROAD, both=False, width=22, spacing=30, rows=2)
# EAST side - a thin shop row in the gap between the road and the NE laborer quarter, making it a true
# two-sided market street (the frontage skips the laborer cross-street at y950 via collision avoidance)
s.frontage([(1600, 1500), (1600, 780)], (["shop"] * 3 + ["merchant"]) * 5, skip=IMPROAD, both=False, width=22, spacing=40, rows=1)
s.label(1452, 1440, "road market", 10, italic=True, color="#5A4326")

# the in-wall fields are REAL farmland: ring them with farmhouses at the same proportion a
# village/hamlet field gets (~12 per 1000px of edge), not the token few of a first ring. A
# SECOND, offset row (placed LAST, so it perturbs no earlier RNG-seeded placement) brings the
# in-wall agricultural district up to village density (city_interior_fields_farmhouse_density).
s.ring(NW1, 26, 18, ["plain"])
s.ring(NW1, 22, 46, ["plain"])
s.ring(NW2, 26, 18, ["plain"])
s.ring(NW2, 22, 46, ["plain"])

s.title("Tango")
s.compass()

HERE = os.path.dirname(os.path.abspath(__file__))
nb = {}
for b in s.M["buildings"]:
    nb[b["kind"]] = nb.get(b["kind"], 0) + 1
print("farmhouses:", len(s.M["houses"]), "| buildings:", nb, "| total urban:", sum(nb.values()),
      "| estates:", len(s.M["manors"]), "| finish:", s.finish(os.path.join(HERE, "tango")))
