#!/usr/bin/env python3
"""Kikuta - an average farming village (diagram skill, Mode B).

TO SCALE: 1 px = 2 ft (village scale). The plain farmhouse is 23x14 px (~46x28 ft,
the 8:5 minka); fields are sized so one bunded paddy terrace is bigger than a house,
and each farmstead is dropped as a whole HOMESTEAD BUNDLE (house + windward grove +
threshing yard + dooryard garden). Map is 1980x1320 px = 0.75 x 0.50 mi (~240 acres).

What makes Kikuta Kikuta: TWO staggered common fields of differing orientation, a
pond (tameike) water source feeding the fields, a hill-top Benten shrine reached by
7 torii, a resident priestess with tax-free plots, and post-blight fallow fields
ringed by abandoned houses.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settlement import Settlement  # noqa: E402

s = Settlement(W=1980, H=1320, seed=37)
s.meta(name="Kikuta", scale="village", households=70, torii_expected=7,
       shrine_on_hill=True, fallow_implies_abandoned=True, has_pond=True)

# regions (to-scale: the two commons are ~15 acres each)
WEST = (170, 500, 760, 900)
CENTRAL = (920, 470, 1350, 1030)
MIDNORTH = (770, 170, 1010, 380)
SW, SE = (250, 940, 470, 1130), (1380, 980, 1600, 1150)
POND = (430, 250, 110, 66)
HEADMAN = (1140, 500)

# water (drawn first so the fields paint over the channel ends): a tameike pond,
# channels from inside the pond to well inside each field
pcx, pcy, prx, pry = POND
s.pond(pcx, pcy, prx, pry, stream_curve=f'M{pcx},{pcy-pry} C{pcx-28},135 {pcx+32},88 {pcx-6},38')
# a tameike has ONE outlet sluice (hi): all the irrigation forks from a single point on the pond's SE foot,
# not three independent taps (see SKILL.md 'Irrigation topology')
OUTLET = (470, 312)   # the pond single sluice; every field is fed from here by water_field
s.lane([(930, 1310), (905, 1130), (878, 1040), (832, 940), (772, 884)])
# drainage (haisui): NW is uphill, so the valley sheds its water to the LOW SE - a drain stream leaves the
# fields' south-east foot and runs off the map's low edge (the honest downhill cue, not shading)

# fields
s.water_field(WEST, "WEST PADDIES", "west", OUTLET, (700, 1345), amp=58, taxfree=1, plot=34)
s.water_field(CENTRAL, "CENTRAL PADDIES", "central", OUTLET, (1330, 1345), amp=54, taxfree=2, plot=34)
s.water_field(MIDNORTH, "", "midnorth", OUTLET, (985, 500), amp=32, plot=34, drain_anchor={"kind": "field", "name": "central"})
s.fallow_field(SW, "sw")
s.fallow_field(SE, "se")


# hill + Benten shrine + 7 torii (east side)
sx, sy = s.hill(1740, 720, 200, 156)
s.shrine(sx, sy)
s.torii_even([(1740, 902), (1598, 852), (1878, 818), (1606, 760), (1874, 744), (1668, 730), (1792, 726)], 7)

# houses: headman (a modest compound, no grove for now); occupied bundles ring the commons;
# the blight's abandoned ruins around the fallow fields, then a few occupied bundles there too
s.headman(*HEADMAN, 40, 26)
s.ring(SW, 11, 24, ["abandoned"])
s.ring(SE, 11, 24, ["abandoned"])
# occupied homestead bundles - each is large (house + ~6:1 grove + yard + garden), so the counts
# are modest and the gaps generous (a dispersed farming village)
s.ring(WEST, 18, 32, ["plain"] * 7 + ["big"])
s.ring(WEST, 13, 92, ["plain"])
s.ring(CENTRAL, 19, 32, ["plain"] * 7 + ["big"])
s.ring(CENTRAL, 13, 92, ["plain"])
s.ring(MIDNORTH, 11, 28, ["plain"])
s.ring(SW, 7, 30, ["plain"])
s.ring(SE, 7, 30, ["plain"])

# labels
s.label(HEADMAN[0], 462, "Headman's House", 13, weight="bold")
s.label(888, 286, "small field (healthy)", 9, italic=True, color="#33301E")
s.label(sx, sy - 50, "Shrine to Benten", 13, weight="bold", color="#6B2A18")
s.label(sx, sy + 54, "Sister Baika's home", 9, italic=True, color="#6B2A18")
s.label(pcx, pcy - pry - 12, "irrigation pond", 11, italic=True, color="#5C7488")
s.label(pcx, pcy + 4, "(fed by the", 9, italic=True, color="#3A4A55")
s.label(pcx, pcy + 16, "northern stream)", 9, italic=True, color="#3A4A55")
s.label(360, 1150, "fallow - post-blight", 10, italic=True, color="#9C7A40")
s.label(1490, 1170, "fallow - post-blight", 10, italic=True, color="#9C7A40")
s.label(1150, 660, "Sister Baika's tax-free plots (vermillion)", 9, italic=True, color="#6B2A18")
s.label(330, 1240, "abandoned after the kumosaya", 10, "start", italic=True, color="#9A3A2A")

# the village burial ground, away to the NE - well clear of the shrine (kegare/death-pollution)
s.cemetery(1480, 340, 84, 58, label="village burial ground")

# draw the farmhouses (each a whole homestead bundle); LAST so every obstacle is known
s.farmsteads()

# communal WELLS among the FINAL dwellings (after farmsteads, so they sit among the placed houses)
s.place_wells((120, 110, 1660, 1250), spacing=240, r=5, near=90)

s.title("Kikuta")
s.compass()

HERE = os.path.dirname(os.path.abspath(__file__))
print("placed houses:", s.finish(os.path.join(HERE, "kikuta-village")))
