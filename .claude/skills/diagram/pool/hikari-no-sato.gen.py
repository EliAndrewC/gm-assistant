#!/usr/bin/env python3
"""Hikari no Sato - a farming village (diagram skill, Mode B).

A second worked example proving the library generalizes. What makes Hikari
different from Kikuta: ONE enormous V-shaped common field (point/crook at the
bottom-center); the blight left an internal FALLOW PATCH in an upper arm (no
abandoned houses); a ring of smaller fields at the corners; NO pond - irrigation
is a stream diversion from off-map feeding the main field, which then feeds the
small fields field-to-field; the Benten village shrine is CENTRAL, in the crook
of the V (NOT on a hill), with only 2 torii; the headman's house sits just below
the shrine, close to the field and opposite the blight; and a second, still-tended
shrine to Bishamon stands in the southwest. (Villages have shrines, not temples.)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settlement import Settlement  # noqa: E402

s = Settlement(seed=38)
s.meta(name="Hikari no Sato", scale="village", households=70, torii_expected=2,
       shrine_on_hill=False, fallow_implies_abandoned=False, has_pond=False)

# the great V-shaped common field (point/crook at bottom-center; arms open upward)
MAIN = [(340, 250), (910, 760), (1480, 250), (1300, 300), (910, 540), (540, 300)]
FALLOW_PATCH = [(1080, 420), (1200, 435), (1190, 510), (1070, 495)]   # an upper arm, opposite the headman
NW = (150, 300, 350, 470)
NE = (1500, 300, 1690, 470)
SW = (320, 990, 540, 1130)
SE = (1280, 980, 1500, 1130)
HEADMAN = (910, 800)       # up by the field's southern point (the headman farms)
SHRINE = (910, 915)        # Benten, at the torii gateway on the southern approach (a recent addition)

# water FIRST (fields paint over the channel ends): a stream diversion from off-map
# (the channel enters from the top edge) feeds the main field, which then feeds the rest
s.channel((910, 28), (910, 650), {"kind": "offmap"}, {"kind": "field", "name": "main"})
s.channel((560, 400), (250, 385), {"kind": "field", "name": "main"}, {"kind": "field", "name": "nw"})
s.channel((1260, 400), (1595, 385), {"kind": "field", "name": "main"}, {"kind": "field", "name": "ne"})
s.channel((760, 560), (430, 1060), {"kind": "field", "name": "main"}, {"kind": "field", "name": "sw"})
s.channel((1060, 560), (1390, 1055), {"kind": "field", "name": "main"}, {"kind": "field", "name": "se"})
# the lane comes all the way up through the torii to the headman's doorstep
s.lane([(910, 1175), (910, 1090), (910, 995), (910, 958)])

# fields
s.paddy_field(MAIN, "HIKARI COMMON FIELD", "main", amp=46, taxfree=2,
              fallow_patch=FALLOW_PATCH, label_xy=(700, 470))
s.paddy_field(NW, "", "nw", amp=28)
s.paddy_field(NE, "", "ne", amp=30)
s.paddy_field(SW, "", "sw", amp=30)
s.paddy_field(SE, "", "se", amp=30)

# the Benten village shrine at the southern torii gateway (a recent addition, NOT on a hill)
s.shrine_hall(SHRINE[0], SHRINE[1], "Shrine to Benten",
              w=96, h=64, torii=[(910, 1000), (910, 1065)], primary=True)
# the still-tended Bishamon village shrine, southwest
s.shrine_hall(230, 980, "Shrine to Bishamon", "(still tended)", w=118, h=82)

# houses: headman largest; ring the V field and each small field
s.headman(*HEADMAN)
# two-deep around the great V field, plus a ring on each small field
s.ring(("poly", s.field_polys[0]), 40, 24, ["plain"] * 8 + ["big"])
s.ring(("poly", s.field_polys[0]), 18, 58, ["plain"])
for bb in (NW, NE, SW, SE):
    s.ring(bb, 12, 16, ["plain"])
s.ring(SW, 8, 44, ["plain"])   # extra ring on SW's open sides (the Bishamon shrine blocks its west)

# labels
s.label(806, 805, "Headman's House", 13, anchor="end", weight="bold")
s.label(1135, 408, "blight - fallow patch", 10, italic=True, color="#9C7A40")
s.label(950, 96, "from the hills (off-map)", 10, "start", italic=True, color="#5C7488")
s.label(700, 555, "shrine's tax-free plots (vermillion)", 9, italic=True, color="#6B2A18")

# the village burial ground, off at the east edge - well clear of both shrines (a Shinto shrine
# keeps death-pollution at arm's length)
s.cemetery(1620, 690, 82, 58, label="village burial ground")

# draw the farmhouses, each with its threshing/drying yard (universal); LAST so every obstacle is known
s.farmsteads()

# communal WELLS among the FINAL dwellings (after farmsteads, so they sit among the placed houses)
s.place_wells((140, 150, 1700, 1115), spacing=330, near=85)

s.title("Hikari no Sato")
s.compass()

HERE = os.path.dirname(os.path.abspath(__file__))
print("placed houses:", s.finish(os.path.join(HERE, "hikari-no-sato")))
