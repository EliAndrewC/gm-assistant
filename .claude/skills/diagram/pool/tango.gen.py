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
        plus the city's in-wall BURAKUMIN neighbourhood (siege need).
  - NE: the LABORER neighbourhoods, gridded blocks of tight tenement rows.
  - SW: the MERCHANT district + a TEMPLE neighbourhood (Temples of Benten + Daikoku, the Crane
        patron fortunes) holding the Ministry of Rites that oversees them.
  - SE: the provincial GOVERNMENT (governor's mansion + five of the six ministries) and the
        SAMURAI neighbourhood, with a Temple of Bishamon (the warrior fortune) among them.
Wealthy samurai keep walled ESTATES of varying size outside the SE wall and commute in. All
six ministries (Rites, Revenue, Retainers, War, Works, Justice) appear; civic amenities ported
from the town tier: merchant-house kura, a market flophouse, an amphitheatre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settlement import Settlement  # noqa: E402

s = Settlement(3200, 2700, seed=71)
s.meta(name="Tango", scale="city", walled=True, agricultural_district=True)
s.bscale = 0.42

# ---- the closed rampart (a near-elliptical ring) sized to hug the city, with N and S gates
CX, CY, RX, RY = 1600, 1330, 840, 780
NRING = 22
WALL = [(round(CX + RX * math.cos(-math.pi / 2 + 2 * math.pi * i / NRING)),
         round(CY + RY * math.sin(-math.pi / 2 + 2 * math.pi * i / NRING))) for i in range(NRING)]
NGATE, SGATE = WALL[0], WALL[NRING // 2]
s.city_wall(WALL, gates=[NGATE, SGATE])
MOAT = s.moat(WALL, gap=42)
s.bound = [list(p) for p in WALL]            # placement stays inside the wall

# ---- the Imperial road (N-S spine, off both edges, through both gates), the moat-feeder, gates
s.road([(1600, -40), (1600, CY - RY), (1600, 1330), (1600, CY + RY), (1600, 2740)], label="Imperial Road")
_mnw = min(MOAT, key=lambda p: (p[0] - 1000) ** 2 + (p[1] - 740) ** 2)   # a moat vertex on the NW
s.stream([(640, -40), (740, 230), (850, 470), (_mnw[0], _mnw[1])])       # off-map NW source feeding the moat

# civic amenities placed FIRST, in the open central cross, so the dense packs flow around them
s.amphitheater(1450, 980, 68, label="amphitheater")          # a leisure ground near the centre
s.flophouse(1490, 1610, w=92, h=42)                          # market-day lodging in the merchant quarter


def grid(streets, width=18):
    for st in streets:
        s.street(st, width=width)


# ====================================================================== NW: agricultural
s.pond(1250, 1050, 74, 46)               # well inside the wall, between the fields and the burakumin lane
NW1, NW2 = (900, 960, 1130, 1140), (1190, 760, 1410, 930)
s.channel((1240, 1050), (1010, 1050), {"kind": "pond"}, {"kind": "field", "name": "nw1"})
s.channel((1250, 1015), (1300, 860), {"kind": "pond"}, {"kind": "field", "name": "nw2"})
s.paddy_field(NW1, "", "nw1", amp=22)
s.paddy_field(NW2, "", "nw2", amp=20)
s.ring(NW1, 7, 16, ["plain"])
s.ring(NW2, 7, 16, ["plain"])
s.label(1010, 590, "agricultural district", 11, italic=True, color="#5A6A2A")
# the in-wall burakumin neighbourhood (its lane reaches the Imperial road, wiring it to the grid)
grid([[(820, 1230), (1545, 1230)], [(1230, 1180), (1230, 1320)]])
s.pack((780, 1140, 1560, 1320), ["burakumin"] * 96, step=21, face_streets="fill")
s.label(1060, 1132, "burakumin neighbourhood", 11, italic=True, color="#6B4F2A")

# ====================================================================== NE: laborers (grid)
grid([[(1690, 800), (2140, 800)], [(1690, 1070), (2360, 1070)],
      [(1960, 700), (1960, 1270)], [(2150, 820), (2150, 1260)]])
s.pack((1640, 600, 2420, 1300), ["laborer"] * 520, step=19, face_streets="fill")
s.label(2010, 612, "laborer neighbourhoods", 11, italic=True, color="#5A4326")

# ====================================================================== SW: merchants + temple
s.street([(1550, 1500), (800, 1500)], width=22, main=True)   # main commercial avenue, wired to the road
grid([[(1550, 1720), (910, 1720)], [(1050, 1370), (1050, 1840)], [(1300, 1370), (1300, 1840)]], width=18)
# the temple neighbourhood (lower SW, INSIDE the wall): Benten + Daikoku with the Ministry of
# Rites that oversees them - placed BEFORE the merchant pack so it flows around them
s.shrine_hall(1150, 1846, "Temple of Benten", w=124, h=80, kind="temple", primary=True)
s.shrine_hall(1400, 1916, "Temple of Daikoku", w=124, h=80, kind="temple")
s.ministry(1280, 1968, "Ministry of Rites")
s.label(1000, 1840, "temple neighbourhood", 10, italic=True, color="#6B2A18")
s.pack((770, 1360, 1560, 1860), (["merchant"] * 4 + ["shop"]) * 84, step=28, face_streets="fill")
s.label(1120, 1372, "merchant district", 11, italic=True, color="#5A4326")

# ====================================================================== SE: government + samurai
# the governor's YAMEN - the grandest compound in the city (a whole city block; its dozens of
# interior buildings are a separate Mode A diagram), placed clear of the rampart in the SE
s.governor_mansion(1950, 1760, 280, 185, "Governor's Mansion", gate_dir="west")
s.shrine_hall(1700, 1650, "Temple of Bishamon", w=120, h=80, kind="temple")
# the five other ministries CLUSTER around the yamen (the government district), as in a Chinese
# provincial seat / Japanese castle town (Rites is apart, in the SW temple neighbourhood)
MINS = ["Ministry of Revenue", "Ministry of Retainers", "Ministry of War",
        "Ministry of Works", "Ministry of Justice"]
MIN_POS = [(1850, 1600), (2030, 1600), (2160, 1620), (2160, 1700), (2160, 1780)]
for (mx, my), name in zip(MIN_POS, MINS):
    s.ministry(mx, my, name)
# the samurai neighbourhood wraps the government compounds; a small street grid west of the yamen,
# clear of the ministries (which now column up the east side of the governor's compound)
grid([[(1680, 1780), (1800, 1780)], [(1680, 1980), (1800, 1980)], [(1740, 1700), (1740, 1990)]], width=18)
s.pack((1640, 1620, 2410, 2080), ["samurai"] * 200, step=28, face_streets="fill")
s.label(2090, 1612, "samurai neighbourhood", 11, italic=True, color="#3A352C")
# fill the band between the NE laborer quarter and the SE quarter (no large empty ground in a city)
s.pack((1660, 1330, 2400, 1560), ["laborer"] * 150, step=19, face_streets="fill")

# merchant-house kura, attached after the businesses are placed
s.merchant_storehouses(8)

# ====================================================================== OUTSIDE the walls
s.bound = None
# wealthy samurai walled estates - all to the SE, beyond the moat, SCATTERED and varying in size
EST = [(2660, 1630, 224, 148), (2920, 1590, 150, 100), (3100, 1720, 168, 112),
       (2620, 1880, 196, 130), (2920, 1900, 168, 112), (3120, 2060, 150, 100),
       (2700, 2220, 210, 140), (2980, 2280, 160, 106)]
for ex, ey, ew, eh in EST:
    s.manor(ex, ey, ew, eh, "")
s.label(2820, 1532, "samurai estates", 11, italic=True, color="#3A352C")
# surrounding farmland: large fields CLOSE to the city, irrigated from the MOAT, each ringed by
# the villagers' farmhouses; two run off the map edge (their houses ring the on-map part).
# Channels first, so each field paints over its end.
FARMS = [((-150, 760, 700, 1070), "fw1", (520, 920)), ((300, 1330, 680, 1640), "fw2", (470, 1480)),
         ((1000, -100, 1300, 500), "fn1", (1180, 280))]
for fbb, nm, fin in FARMS:                                   # channels first (each field paints over its end)
    mp = min(MOAT, key=lambda p: (p[0] - fin[0]) ** 2 + (p[1] - fin[1]) ** 2)
    s.channel((mp[0], mp[1]), fin, {"kind": "moat"}, {"kind": "field", "name": nm})
for fbb, nm, fin in FARMS:
    s.paddy_field(fbb, "", nm, amp=24)
    s.ring(fbb, 12, 18, ["plain"])
s.label(360, 690, "farmland (moat-irrigated; off-map beyond)", 10, italic=True, color="#5A6A2A")
# a gate market outside the south gate, beyond the moat
s.pack((1450, 2230, 1770, 2420), (["merchant"] * 2 + ["shop"]) * 4, step=46)
s.label(1610, 2222, "gate market", 10, italic=True, color="#5A4326")

s.title("Tango")
s.compass()

HERE = os.path.dirname(os.path.abspath(__file__))
nb = {}
for b in s.M["buildings"]:
    nb[b["kind"]] = nb.get(b["kind"], 0) + 1
print("farmhouses:", len(s.M["houses"]), "| buildings:", nb, "| total urban:", sum(nb.values()),
      "| estates:", len(s.M["manors"]), "| finish:", s.finish(os.path.join(HERE, "tango")))
