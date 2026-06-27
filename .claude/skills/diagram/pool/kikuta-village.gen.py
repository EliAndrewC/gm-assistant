#!/usr/bin/env python3
"""Kikuta - an average farming village (diagram skill, Mode B).

A thin spec on top of settlement.py. What makes Kikuta Kikuta: TWO staggered
common fields of differing orientation, a pond (tameike) water source feeding the
fields, a hill-top Benten shrine reached by 7 torii, a resident priestess with
tax-free plots, and post-blight fallow fields ringed by abandoned houses.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settlement import Settlement  # noqa: E402

s = Settlement(seed=23)
s.meta(name="Kikuta", scale="village", households=70, torii_expected=7,
       shrine_on_hill=True, fallow_implies_abandoned=True, has_pond=True)

# regions
WEST = (235, 460, 700, 740)
CENTRAL = (860, 478, 1165, 942)
MIDNORTH = (715, 185, 900, 320)
SW, SE = (250, 858, 452, 1010), (1262, 910, 1470, 1058)
POND = (378, 220, 96, 58)
HEADMAN = (1006, 430)

# water (drawn first so the fields paint over the channel ends): a tameike pond,
# channels from inside the pond to well inside each field
pcx, pcy, prx, pry = POND
s.pond(pcx, pcy, prx, pry, stream_curve=f'M{pcx},{pcy-pry} C{pcx-26},122 {pcx+30},80 {pcx-6},34')
s.channel((450, 228), (788, 250), {"kind": "pond"}, {"kind": "field", "name": "midnorth"})
s.channel((388, 260), (470, 520), {"kind": "pond"}, {"kind": "field", "name": "west"})
s.channel((440, 248), (945, 548), {"kind": "pond"}, {"kind": "field", "name": "central"})
s.lane([(845, 1175), (822, 1010), (800, 930), (760, 840), (706, 792)])

# fields
s.paddy_field(WEST, "WEST COMMON FIELD", "west", amp=54, taxfree=1)
s.paddy_field(CENTRAL, "CENTRAL COMMON FIELD", "central", amp=50, taxfree=2)
s.paddy_field(MIDNORTH, "", "midnorth", amp=30)
s.fallow_field(SW, "sw")
s.fallow_field(SE, "se")

# hill + Benten shrine + 7 torii
sx, sy = s.hill(1600, 605, 198, 152)
s.shrine(sx, sy)
s.torii_even([(1600, 748), (1470, 712), (1716, 672), (1486, 628), (1714, 600), (1556, 596), (sx, sy + 38)], 7)

# houses: headman largest; ring every field; fallow fields ring abandoned houses
s.headman(*HEADMAN)
# two-deep around the big fields (a ~70-household village is not a single necklace)
# the blight's abandoned houses first (before occupied rings can crowd them out), a
# small count so it stays "some"
s.ring(SW, 5, 18, ["abandoned"])
s.ring(SE, 5, 18, ["abandoned"])
# occupied farmhouses, two-deep around the big fields (a ~70-household village)
s.ring(WEST, 18, 20, ["plain"] * 7 + ["big"])
s.ring(WEST, 32, 54, ["plain"])
s.ring(CENTRAL, 20, 20, ["plain"] * 7 + ["big"])
s.ring(CENTRAL, 38, 54, ["plain"])
s.ring(MIDNORTH, 14, 16, ["plain"])
s.ring(MIDNORTH, 11, 50, ["plain"])
s.ring(SW, 6, 18, ["plain"])
s.ring(SE, 6, 18, ["plain"])

# labels
s.label(HEADMAN[0], 388, "Headman's House", 13, weight="bold")
s.label(807, 252, "small field (healthy)", 9, italic=True, color="#33301E")
s.label(sx, sy - 46, "Shrine to Benten", 13, weight="bold", color="#6B2A18")
s.label(sx, sy + 50, "Sister Baika's home", 9, italic=True, color="#6B2A18")
s.label(pcx, pcy - pry - 12, "irrigation pond", 11, italic=True, color="#5C7488")
s.label(pcx, pcy + 4, "(fed by the", 9, italic=True, color="#3A4A55")
s.label(pcx, pcy + 16, "northern stream)", 9, italic=True, color="#3A4A55")
s.label(345, 1030, "fallow - post-blight", 10, italic=True, color="#9C7A40")
s.label(1366, 1080, "fallow - post-blight", 10, italic=True, color="#9C7A40")
s.label(1006, 600, "Sister Baika's tax-free plots (vermillion)", 9, italic=True, color="#6B2A18")
s.label(305, 1120, "abandoned after the kumosaya", 10, "start", italic=True, color="#9A3A2A")

# communal WELLS among the dwellings (placed after them, in the open gaps); households share these,
# the rest draw from the irrigation pond/channels/stream
s.place_wells((160, 110, 1480, 1080), spacing=320, near=85)

s.title("Kikuta")
s.compass()

HERE = os.path.dirname(os.path.abspath(__file__))
print("placed houses:", s.finish(os.path.join(HERE, "kikuta-village")))
