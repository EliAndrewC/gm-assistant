#!/usr/bin/env python3
"""Moritono - a hamlet (diagram skill, Mode B).

"Forest manor": a small farming hamlet beside the Shirin Forest, where the county
magistrate keeps a hunting lodge. What makes it a hamlet (not a village): far fewer
households, NO headman of its own (it falls under the village district headman), no
village shrine, and no tax-free plot. Its distinctive features are the Shirin Forest
filling the east and the magistrate's walled manor at the forest's edge - a samurai
estate adjacent to the hamlet, not part of it. A stream from the northern hills
cascades through the three small fields.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settlement import Settlement  # noqa: E402

s = Settlement(seed=44)
s.meta(name="Moritono", scale="hamlet", households=16)   # hamlet: no headman, no shrine, no tax-free

# three small paddies (SW), the forest (E), the magistrate's manor (by the forest)
NW = (360, 300, 560, 470)
SW = (340, 650, 530, 810)
S = (660, 880, 890, 1040)

# the Shirin Forest fills the east behind an irregular tree-line
s.forest([(1500, -10), (1452, 180), (1506, 400), (1448, 620), (1500, 840), (1462, 1060), (1492, 1190)],
         label="Shirin Forest", label_xy=(1660, 600))

# water: a forest brook feeds a reservoir pond (tameike) between the fields and the
# manor, which in turn irrigates the three fields
s.stream([(1830, 600), (1620, 608), (1410, 614), (1200, 616), (1000, 612)],
         frm={"kind": "forest"}, to={"kind": "pond"})   # forest brook (from off-map, through the forest) into the pond
s.pond(950, 612, 84, 54)
s.channel((898, 580), (460, 382), {"kind": "pond"}, {"kind": "field", "name": "nw"})
s.channel((904, 642), (432, 730), {"kind": "pond"}, {"kind": "field", "name": "sw"})
s.channel((928, 660), (772, 952), {"kind": "pond"}, {"kind": "field", "name": "s"})

# fields (small - no field-name labels)
s.paddy_field(NW, "", "nw", amp=26)
s.paddy_field(SW, "", "sw", amp=26)
s.paddy_field(S, "", "s", amp=28)

# the magistrate's walled hunting lodge, at the forest's edge
s.manor(1230, 380, 270, 330, "Magistrate's Manor", "hunting lodge by the Shirin Forest", gate_dir="west")

# peasant farmhouses ring the three fields (no headman in a hamlet)
s.ring(NW, 8, 16, ["plain"])
s.ring(SW, 8, 16, ["plain"])
s.ring(S, 9, 16, ["plain"])

# a couple of communal WELLS among the farmhouses (placed after them, so they sit in the open gaps);
# a hamlet's households share these, the rest draw from the irrigation pond/channels
s.place_wells((360, 320, 900, 1040), spacing=430, near=85)

s.label(950, 546, "irrigation pond", 10, italic=True, color="#5C7488")

# draw the farmhouses, each with its threshing/drying yard (universal); LAST so every obstacle is known
s.farmsteads()

s.title("Moritono")
s.compass()

HERE = os.path.dirname(os.path.abspath(__file__))
print("placed houses:", s.finish(os.path.join(HERE, "moritono")))
