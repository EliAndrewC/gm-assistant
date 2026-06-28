#!/usr/bin/env python3
"""Hoshizora - an unwalled town (diagram skill, Mode B, town scale).

A county seat of ~1,200 people / ~238 households. Per budgets.md the population is
~65% farmers, plus merchants (~24 hh), laborers (~29), servants (~13), burakumin
(~12), and samurai (~4: the magistrate and staff). The map represents ALL of these
(scaled down - others off-map - but every caste present and farmers the plurality):
a rural farm zone NW around a stream, a dense urban core of merchant/laborer/servant
buildings along the Imperial Road, the Magistrate's walled manor + samurai houses SW,
the segregated burakumin neighborhood NE, an amphitheater, barns ringed by hayfield/grazing
pasture SE, and a small forest. Unwalled.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settlement import Settlement  # noqa: E402

s = Settlement(2000, 1300, seed=78)
# EXCEPTION to the default 2-monasteries-per-town rule: Hoshizora is a quiet interior county
# seat in a historically uncontested area, and really has only the ONE town monastery (to
# Bishamon). Declared explicitly via monastery_fortunes so the gate knows it is intentional.
s.meta(name="Hoshizora", scale="town", walled=False, torii_expected=1, monastery_fortunes=["Bishamon"], population=600)   # residents DEPICTED (dwellings x5); urban housing full, most farms off-map - a slice of the ~1,200 county

# ---- terrain: a small forest (SE corner) and two grazing pastures, all running OFF
# the map edge (larger than drawn)
s.forest_patch([(1660, 950), (1860, 915), (2060, 1000), (2060, 1360), (1720, 1360), (1620, 1120)])
# southern hayfield - expanded up toward the amphitheater, off the bottom edge
s.pasture([(900, 1010), (1180, 1000), (1290, 900), (1540, 900), (1600, 1110), (1490, 1360), (910, 1360), (860, 1190)],
          label="hayfields & grazing", amp=32, label_xy=(1090, 1190))
# northern hayfield - in the empty top of the map, off the top edge, with hay barns
s.pasture((1060, -50, 1660, 240), label="hayfields", label_xy=(1300, 150))
for (bx, by) in [(1180, 140), (1420, 110), (1560, 185)]:
    s.building(bx, by, 84, 56, "barn")

# ---- the Imperial Road (SW -> NE spine), running off both edges
ROAD = [(-162, 1306), (140, 1130), (620, 850), (1100, 580), (1560, 350), (1900, 170), (2209, 6)]
s.road(ROAD, label="Imperial Road")

# ---- water: a stream running PARALLEL to the road, BETWEEN the field pairs (F1/F3
# northwest, F2/F4 southeast), off the left and top edges - never through a field.
# Irrigation channels tap it to feed the fields.
# five fields - three NW of the stream (incl. nw5, running OFF the left edge: a town
# has far more farmland than we draw), two SE
F1, F2 = (100, 90, 320, 245), (490, 390, 720, 560)
F3, F4 = (80, 295, 180, 395), (430, 620, 640, 760)
F5 = (-110, 280, 35, 470)   # only a sliver on the map, the rest off the left edge
s.stream([(-15, 640), (230, 500), (470, 360), (700, 210), (880, -15)])
s.channel((150, -5), (195, 175), {"kind": "offmap"}, {"kind": "field", "name": "nw1"})
s.channel((140, 220), (125, 360), {"kind": "field", "name": "nw1"}, {"kind": "field", "name": "nw3"})
s.channel((270, 195), (600, 470), {"kind": "field", "name": "nw1"}, {"kind": "field", "name": "nw2"})
s.channel((600, 530), (560, 690), {"kind": "field", "name": "nw2"}, {"kind": "field", "name": "nw4"})
for bb, nm, fa in [(F1, "nw1", 22), (F2, "nw2", 24), (F3, "nw3", 18), (F4, "nw4", 24), (F5, "nw5", 18)]:
    s.paddy_field(bb, "", nm, amp=fa)

# ---- the Shrine to Bishamon, by the stream
# a town's religious building is a monastery (not a village shrine), with a torii in front
s.shrine_hall(215, 800, "Monastery of Bishamon", w=132, h=86,
              kind="monastery", primary=True, torii=[(215, 892)], label_below=True)

# ---- the Magistrate's walled manor (county seat) - walls only; its interior
# (hall, stables, etc.) is the subject of a separate Mode A diagram. TILTED (rot=-30) so its front
# wall runs PARALLEL to the Imperial Road, which crosses NW-to-NE just past this SW edge; the gate
# (north side) opens onto that road. The tilted footprint reshuffles the dense town's seeded packs,
# which is why this map's seed (78) was chosen - it lands the depicted population back on its mark.
s.manor(500, 1120, 250, 180, "Magistrate's Manor", gate_dir="north", rot=-30)

# the market flophouse (kichin-yado) just off the road on the SW approach, where peasants
# travelling in for market day arrive - they sleep on straw for a sen a night
s.flophouse(345, 905)

# ---- the amphitheater + barns (the barns sit in the grazing pasture)
s.amphitheater(1320, 770, 82, label="amphitheater")
s.building(1080, 1110, 88, 58, "barn")
s.building(1330, 1150, 84, 56, "barn")
s.label(1200, 1058, "barns", 10, italic=True)

# ---- urban core, sized to the town's documented non-farmer households (budgets.md):
# ~24 merchant houses, ~14 shops, ~29 laborer dwellings, ~5 standalone servants. The
# BUSINESSES front the Imperial Road (the high street), each facing the roadbed; the
# laborers' and servants' housing sits back off the road, behind the shopfronts.
ROAD_CORE = [(470, 945), (760, 760), (1060, 600), (1360, 450), (1700, 278)]
s.frontage(ROAD_CORE, (["merchant"] * 3 + ["shop"]) * 11, width=26, setback=16, spacing=48, rows=2, skip=ROAD)
s.label(972, 586, "merchant houses & shops", 11, italic=True, color="#5A4326")
# laborers' and servants' housing, set back off the road behind the shopfronts (NW and SE)
s.pack((740, 235, 1320, 470), ["laborer"] * 24, step=42)
s.pack((1165, 705, 1580, 918), ["servant"] * 13 + ["laborer"] * 13, step=42)
s.label(1010, 224, "laborers' dwellings (set back off the road)", 10, italic=True, color="#5A4326")

# ---- the segregated burakumin neighborhood (NE edge)
s.pack((1700, 380, 1972, 700), ["burakumin"] * 12, step=44)
s.label(1832, 360, "burakumin neighborhood", 11, italic=True, color="#6B4F2A")

# ---- samurai houses, around the magistrate's manor (SW); their servants live within
# the manor/samurai compounds, not as separate huts
s.pack((620, 1010, 920, 1295), ["samurai"] * 7, step=58)
s.label(770, 1268, "samurai houses", 11, italic=True)   # over the cluster - kept above the bottom image edge (canvas H=1300)

# a noticeable minority of merchant houses keep a fireproof kura (the absentee landlords'
# rent-rice / bulk goods), drawn AFTER the businesses exist
s.merchant_storehouses(6)

# ---- farmhouses: the town's farmer majority (still the largest single group), packed several-deep
# around the fields - generously, since each needs room for its threshing yard (some get dropped)
for bb in (F1, F2, F3, F4):
    s.ring(bb, 17, 14, ["plain"])
    s.ring(bb, 15, 40, ["plain"])
    s.ring(bb, 13, 66, ["plain"])
    s.ring(bb, 11, 90, ["plain"])

# a caravan INN + STABLES on the Imperial Road through-route, with open ground beside the stables as a
# pasture for the wagon-train animals (oxen, horses) - like a provincial city's gate caravan facilities,
# but a county town needs only the ONE; it FRONTS the Imperial Road on the quiet SW approach (caravans pull up to it)
s.inn(276, 1116, rot=150)
s.stables(276, 1202, rot=150)

# the funerary ground BEHIND the monastery (N of it, away from the Imperial Road): the parish
# graveyard (Buddhist danka) right against the BACK of the hall (well clear of the stream to the N),
# with the cremation ground on the marginal
# western edge beyond it - clear of the dwellings. Both sit behind the hall so no one walks past
# the pyre to reach the monastery (gated by cremation_ground_not_between_temple_and_road).
s.cemetery(215, 705, 110, 80, label="graveyard", label_above=True)
# the cremation ground (monk-run, burakumin assistants) on the western marginal edge; its label
# sits ABOVE the glyph so it clears the long "Monastery of Bishamon" label just to the east
s.cremation_ground(95, 695, label_above=True)

# a MINORITY of the wealthy keep larger RESIDENCES (budgets.md town wealth tiers): a few VERY-RICH /
# RICH merchants in big homes. These sit in a tight band DIRECTLY BEHIND the storefronts (a short step
# off the road, ahead of the laborer warren further back) - the merchant family lives over/behind its
# own shop - and the ~3 MASTER (rich) laborers in larger dwellings at the edge of the warren. The rest
# live small (the house-size variety a county town shows, like a city). Hand-placed LAST in pre-cleared
# gaps so they perturb no seeded pack; the band reads cleanly: shops -> merchant homes -> gap -> laborers.
# Each is TILTED to the local road angle (~-27deg) so it lies PARALLEL to the storefronts directly in
# front of it - housing behind a shop shares the shop's orientation (merchant_housing_aligned_with_storefronts).
for mx, my, mr in [(1136, 433, -27), (1040, 481, -29), (880, 571, -29), (1260, 619, -27)]:
    s.building(mx, my, *s._dims("merchant_large"), "merchant_large", rot=mr)
for lx, ly in [(1328, 235), (740, 298)]:
    s.building(lx, ly, *s._dims("laborer_large"), "laborer_large")

# draw the farmhouses, each with its threshing/drying yard (universal); LAST so every obstacle is known
s.farmsteads()

# communal WELLS among the FINAL dwellings (placed after farmsteads so they sit among the houses)
s.place_wells((85, 110, 1930, 1260), spacing=290, near=85)

s.title("Hoshizora")
s.compass(1950, 50)

HERE = os.path.dirname(os.path.abspath(__file__))
nb = {}
for b in s.M["buildings"]:
    nb[b["kind"]] = nb.get(b["kind"], 0) + 1
print("farmhouses:", len(s.M["houses"]), "| buildings:", nb, "| finish:", s.finish(os.path.join(HERE, "hoshizora")))
