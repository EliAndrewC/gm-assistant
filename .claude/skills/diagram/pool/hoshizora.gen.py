#!/usr/bin/env python3
"""Hoshizora - an unwalled town (diagram skill, Mode B, town scale).

A county seat of ~1,200 people / ~238 households. Per budgets.md the population is
~65% farmers, plus merchants (~24 hh), laborers (~29), servants (~13), burakumin
(~12), and samurai (~4: the magistrate and staff). The map represents ALL of these
(scaled down - others off-map - but every caste present and farmers the plurality):
a rural farm zone NW around a stream, a dense urban core of merchant/laborer/servant
buildings along the Imperial Road, the Magistrate's walled manor + samurai houses SW,
the segregated burakumin neighborhood NE, a theater stage by the monastery, barns ringed by hayfield/grazing
pasture SE, and a small forest. Unwalled.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settlement import Settlement  # noqa: E402

s = Settlement(2000, 1300, seed=386)
# EXCEPTION to the default 2-monasteries-per-town rule: Hoshizora is a quiet interior county
# seat in a historically uncontested area, and really has only the ONE town monastery (to
# Bishamon). Declared explicitly via monastery_fortunes so the gate knows it is intentional.
s.meta(name="Hoshizora", scale="town", walled=False, torii_expected=1, monastery_fortunes=["Bishamon"], population=600, ftpx=1)   # residents DEPICTED (dwellings x5); urban housing full, most farms off-map - a slice of the ~1,200 county. ftpx=1: the GM's town scale, 1px=1ft

# ---- terrain: a small forest (SE corner) and two grazing pastures, all running OFF
# the map edge (larger than drawn)
s.forest_patch([(1660, 950), (1860, 915), (2060, 1000), (2060, 1360), (1720, 1360), (1620, 1120)])
# southern hayfield - expanded up toward the barns, off the bottom edge
s.pasture([(900, 1010), (1180, 1000), (1290, 900), (1540, 900), (1600, 1110), (1490, 1360), (910, 1360), (860, 1190)],
          label="hayfields & grazing", amp=32, label_xy=(1090, 1190))
# northern hayfield - in the empty top of the map, off the top edge, with hay barns
s.pasture((1060, -50, 1660, 240), label="hayfields", label_xy=(1300, 150))
for (bx, by) in [(1180, 140), (1420, 110), (1560, 185)]:
    s.building(bx, by, 84, 56, "barn")

# ---- the Imperial Road (SW -> NE spine), running off both edges
ROAD = [(-162, 1306), (140, 1130), (620, 850), (1100, 580), (1560, 350), (1900, 170), (2209, 6)]
s.road(ROAD, label="Imperial Road")

# ---- water: a stream running PARALLEL to the road, BETWEEN the fields (nw1/nw3
# northwest, nw2/nw4 southeast), off the left and top edges - never through a field.
# Irrigation channels tap it to feed the fields.
# FOUR fields, TO SCALE at 1px=1ft (the scale-ladder pass; they were 4-8x under area
# before): the two biggest RUN OFF the top / west edges - a town map shows only a
# SLICE of the county's farmland, so the drawn patches must read as parts of larger
# expanses continuing off-map, not self-contained garden plots. plot=66 puts one
# bunded paddy at ~0.1 acre (mid premodern range) so a single plot visibly outsizes
# the 46x28 ft farmhouses beside it - the relationship the scale audit checked.
F1 = (290, -50, 560, 220)                                  # runs OFF the top edge
F2 = (480, 405, 780, 610)
F4 = (370, 630, 645, 780)
F3P = [(-150, 85), (230, 85), (400, 330), (60, 510), (-150, 510)]   # hugs the stream, runs OFF the west edge
F6 = (1740, 720, 2060, 860)                                # a second farm pocket NE, runs OFF the east edge
s.stream([(-15, 640), (230, 500), (470, 360), (700, 210), (880, -15)])
s.channel((250, -10), (350, 60), {"kind": "offmap"}, {"kind": "field", "name": "nw1"})
s.channel((340, 130), (200, 150), {"kind": "field", "name": "nw1"}, {"kind": "field", "name": "nw3"})   # anchored DEEP in both fields: the organic outline wobble (amp 22/14) must never strand an endpoint
s.channel((520, 200), (580, 450), {"kind": "field", "name": "nw1"}, {"kind": "field", "name": "nw2"})
s.channel((600, 540), (560, 690), {"kind": "field", "name": "nw2"}, {"kind": "field", "name": "nw4"})
for bb, nm, fa in [(F1, "nw1", 22), (F2, "nw2", 24), (F3P, "nw3", 14), (F4, "nw4", 24), (F6, "ne1", 20)]:
    s.paddy_field(bb, "", nm, amp=fa, plot=66)

# ---- the Shrine to Bishamon, by the stream
# a town's religious building is a monastery (not a village shrine), with a torii in front
s.shrine_hall(215, 800, "Monastery of Bishamon", w=132, h=86,
              kind="monastery", primary=True, torii=[(215, 892)], label_below=True)

# ---- the Magistrate's walled manor (county seat) - walls only; its interior
# (hall, stables, etc.) is the subject of a separate Mode A diagram. TILTED (rot=-30) so its front
# wall runs PARALLEL to the Imperial Road, which crosses NW-to-NE just past this SW edge; the gate
# (north side) opens onto that road. The tilted footprint reshuffles the dense town's seeded packs,
# which is why this map's seed (386) was chosen - it lands the depicted population back on its mark.
s.manor(500, 1120, 250, 180, "Magistrate's Manor", gate_dir="north", rot=-30)

# the market flophouse (kichin-yado) just off the road on the SW approach, where peasants
# travelling in for market day arrive - they sleep on straw for a sen a night
s.flophouse(345, 905)

# ---- the THEATER STAGE - a roofed performance stage + open viewing ground - in the Bishamon monastery's
# precinct (just south of it), the festival/troupe venue belonging to the temple. A quiet county seat, so
# a modest stage. The barns sit in the grazing pasture (SE).
s.theater_stage(200, 990, w=120, h=84, rot=180, label="theater stage")   # rot=180: the monastery is NORTH, so the stage faces north (its viewing ground opens toward the hall, the audience between)
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
# a MINORITY of the wealthy keep larger RESIDENCES (budgets.md town wealth tiers): a few VERY-RICH / RICH
# merchants in big homes DIRECTLY BEHIND the storefronts (the merchant family lives over/behind its own
# shop), ahead of the laborer warren set further back. Derived from the ACTUAL shop positions (not fixed
# coords), so each home is behind the band and parallel to its shop under ANY seed; placed BEFORE the packs,
# which then flow AROUND them. The ~3 MASTER (rich) laborers get larger dwellings at the edge of the warren.
s.merchant_residences(4)
for lx, ly in [(1328, 235), (740, 298)]:
    s.building(lx, ly, *s._dims("laborer_large"), "laborer_large")
# laborers' and servants' housing, set back off the road behind the shopfronts (NW and SE)
s.pack((700, 195, 1140, 390), ["laborer"] * 18, step=42)   # pulled NW, well clear of the diagonal road (behind the merchant-residence band, with a gap); ~29 laborers total (budgets.md), not over
s.pack((1165, 705, 1580, 918), ["servant"] * 13 + ["laborer"] * 11, step=42)
s.label(1010, 224, "laborers' dwellings (set back off the road)", 10, italic=True, color="#5A4326")

# ---- the segregated burakumin neighborhood (NE edge). Set back a full 74+ ft behind the
# road frontage: the aligned-behind-storefronts rule treats any dwelling 15-74 ft directly
# behind a shop as row housing that must lie parallel, and this quarter is its own cluster,
# not part of the shopfront rows
s.pack((1720, 440, 1990, 660), ["burakumin"] * 12, step=44)
s.label(1850, 420, "burakumin neighborhood", 11, italic=True, color="#6B4F2A")

# ---- samurai houses, around the magistrate's manor (SW); their servants live within
# the manor/samurai compounds, not as separate huts
s.pack((620, 1010, 920, 1295), ["samurai"] * 7, step=58)
s.label(770, 1268, "samurai houses", 11, italic=True)   # over the cluster - kept above the bottom image edge (canvas H=1300)

# a noticeable minority of merchant houses keep a fireproof kura (the absentee landlords'
# rent-rice / bulk goods), drawn AFTER the businesses exist
s.merchant_storehouses(6)

# ---- farmhouses: the town's farmer majority (still the largest single group), packed several-deep
# around the fields - generously, since each needs room for its threshing yard (some get dropped).
# The west-edge field is a polygon: ring its recorded outline.
F3_OUTLINE = next(f["outline"] for f in s.M["fields"] if f["name"] == "nw3")
for bb in (F1, F2, ('poly', F3_OUTLINE), F4, F6):
    s.ring(bb, 44, 14, ["plain"])
    s.ring(bb, 38, 40, ["plain"])
    s.ring(bb, 30, 66, ["plain"])
    s.ring(bb, 24, 92, ["plain"])
    s.ring(bb, 18, 118, ["plain"])

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
# sits ABOVE the glyph so it clears the long "Monastery of Bishamon" label just to the east.
# Pushed S of the funerary/monastery band: the to-scale nw3 field's farmhouse ring reaches
# y~650 here, and the crematory must keep >120 ft clear of every dwelling
s.cremation_ground(85, 810, label_above=True)


# draw the farmhouses, each with its threshing/drying yard (universal); LAST so every obstacle is known
s.farmsteads()

# communal WELLS among the FINAL dwellings (placed after farmsteads so they sit among the houses)
s.place_wells((60, 30, 1980, 1270), spacing=220, near=100)   # grid widened to reach the off-edge fields' farms (top + NE pocket)
# the Bishamon monastery sits apart from the houses, so it keeps its OWN ablution well (remote_shrine_has_own_well)
s.shrine_well(215, 800)

s.title("Hoshizora")

HERE = os.path.dirname(os.path.abspath(__file__))
nb = {}
for b in s.M["buildings"]:
    nb[b["kind"]] = nb.get(b["kind"], 0) + 1
print("farmhouses:", len(s.M["houses"]), "| buildings:", nb, "| finish:", s.finish(os.path.join(HERE, "hoshizora")))
