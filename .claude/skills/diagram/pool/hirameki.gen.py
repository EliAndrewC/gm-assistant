#!/usr/bin/env python3
"""Hirameki - a WALLED border town (diagram skill, Mode B, town scale).

A county seat of ~1,200 (per budgets.md), drawn TO SCALE at the GM's town scale, 1px = 1ft
(the scale-ladder pass: the old bscale 0.82 grain implied ~1.3 ft/px and made this the one
town out of step with the others). Historically a Chinese walled county seat / Japanese
jokamachi keeps the urban castes - merchants, artisans, LABORERS, servants, and samurai -
INSIDE the walls, zoned around the magistrate's hilltop citadel; only the farmland/farmhouses,
the segregated burakumin neighborhood, and a small guan-xiang gate-market lie outside. The
surrounding farmers retreat inside during a raid. The hill's steep back defends the north
flank; the Imperial chrysanthemum field abuts the inside of the west rampart.

The 1 ft/px conversion grew every building ~22% linear, so the rampart grew with them (a wall
encloses what it must defend): the ring is the old ring scaled ~1.22x about the hill anchor,
the canvas deepened 1820 -> 2000 to keep the gate market and funerary ground outside the new
south face, and the fields took the Hoshizora treatment - patches 2-3x larger running off the
map edges (a town map draws only a slice of the county's farmland) at plot=66, one bunded
paddy ~0.1 acre, so a single plot visibly outsizes the 46x28 ft farmhouses.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settlement import Settlement  # noqa: E402

s = Settlement(2600, 2000, seed=77)
# downhill is SOUTH: the hill/manor sit in the north, so the land falls away southward and
# the streams flow north-to-south; irrigation channels must run downhill (tap upstream/north
# of where they feed each field)
# Clan: LION (current holder) - its patron fortunes are Bishamon + Daikoku. But Hirameki
# CHANGED HANDS during the Lion/Crane war, so its monasteries are special (override): the
# main one is to Bishamon (Lion's), and a much smaller, older one to Benten (Crane's) sits
# on the far side of town - a relic of Crane rule. Hence monastery_fortunes is set explicitly.
s.meta(name="Hirameki", scale="town", walled=True, torii_expected=5, downhill="south",
       clan="Lion", monastery_fortunes=["Bishamon", "Benten"], population=720, ftpx=1)   # residents DEPICTED (dwellings x5); urban housing full, most farms off-map - a slice of the ~1,200 county. ftpx=1 -> bscale 1.0

# ---- OUTSIDE the walls: streams + farm fields + farmhouses. TO SCALE at 1px=1ft: the
# patches run off the west / bottom edges (larger than drawn), plot=66 = ~0.1 acre/paddy.
s.stream([(250, -10), (175, 470), (255, 940), (160, 1400), (220, 2010)])
s.stream([(2430, -10), (2390, 560), (2460, 1100), (2400, 2010)])
OW1 = (270, 330, 570, 680)
OW2 = (-160, 940, 80, 1240)      # off the left edge; x1=100 keeps its farmhouse ring off the stream corridor
OE1, OE2 = (2000, 380, 2310, 750), (2040, 960, 2360, 1280)   # OE1 deliberately TALL vs the wide OS block (common_fields_vary_orientation)
OS = (620, 1730, 1040, 2090)      # SW of the gate, off the bottom edge (beside the road, not under it); y0 leaves a strip wide enough that a wall-side farm still fits its windward grove
# irrigation channels tap the streams to feed the on-map fields (the off-edge fields draw
# their water off-map); drawn before the fields so each field paints over the channel's end
s.channel((185, 430), (380, 540), {"kind": "stream"}, {"kind": "field", "name": "w1"})
s.channel((2390, 490), (2200, 600), {"kind": "stream"}, {"kind": "field", "name": "e1"})
s.channel((2448, 1030), (2210, 1140), {"kind": "stream"}, {"kind": "field", "name": "e2"})
for bb, nm in [(OW1, "w1"), (OW2, "w2"), (OE1, "e1"), (OE2, "e2"), (OS, "s1")]:
    s.paddy_field(bb, "", nm, amp=24, plot=66)

# ---- the hill (north) with the Magistrate's Manor on top (the citadel)
sx, sy = s.hill(1300, 480, 560, 360, steep=True)
s.manor(1300, 415, 360, 216, "Magistrate's Manor", gate_dir="south")   # gate faces the town below

# ---- the irregular rampart (anchored to the hill, climbing both flanks); the gate is
# south; the west face is a straight run the chrysanthemum field abuts flush
# the S/SE/E faces hug the built core (the monastery + laborer quarters) rather than
# enclosing empty corner space - a tighter line is cheaper to build (wall_hugs_the_town).
# The ring is the pre-rescale ring scaled ~1.22x about the hill anchor (1300,500): the same
# real wall, drawn at 1 ft/px instead of the old ~1.3 ft/px grain.
# NW face tucks IN toward the Benten pocket (two segments instead of one long diagonal):
# the straight line left a ~325 ft empty run beyond the hill base (wall_hugs_the_town)
WALL = [(930, 500), (860, 700), (700, 940), (560, 1060), (560, 1525),
        (665, 1610), (1055, 1647), (1300, 1720), (1545, 1647), (1910, 1525),
        (1925, 1160), (1855, 940), (1790, 500)]   # east face pulled to ~140 ft of the Bishamon precinct (wall_hugs_the_town)
s.wall(WALL, gate=(1300, 1720))
s.label(1300, 1780, "front gate (guard station + tower)", 11, italic=True, color="#3A352C")

# ---- INSIDE: chrysanthemum field (abuts west wall), monastery, the zoned urban core
CHRYS = (567, 1134, 788, 1476)   # the Imperial chrysanthemum field (x0, y0, x1, y1)
s.flower_field(CHRYS, "chrysanthemum field", amp=8, flat_west=True)
# main town monastery (to Bishamon, the Lion patron), on the east side. It has a long, clear
# approach south to the market cross-street, so it fronts a proper torii AVENUE (sando) of
# several arches rather than a single gate (monastery_torii_scale_with_space).
s.shrine_hall(1750, 1050, "Monastery of Bishamon", w=150, h=98, kind="monastery", primary=True,
              torii=[(1750, 1174), (1750, 1235), (1750, 1296), (1750, 1357)])
# the older, much smaller Benten monastery (Crane patron) on the OPPOSITE (west) side, inside
# the walls - a relic of the town's time under Crane rule. It is wedged hard against the west
# rampart and the Imperial chrysanthemum field, so there is room for only a SINGLE torii arch.
s.shrine_hall(700, 1010, "Monastery of Benten", w=60, h=40,
              kind="monastery", primary=False, torii=[(700, 1073)])

# street plan: the gate-to-yamen main avenue + a market cross-street (both fully built up).
# The laborer/servant quarters behind them are accessed off the cross-street and otherwise
# sit as deep tenement blocks with no street frontage (the poor can't afford it) - no
# speculative back-lanes that would dead-end empty, per `streets_have_buildings`.
MAIN = [(1300, 2020), (1300, 1788), (1300, 1470), (1300, 1160), (1300, 960)]   # runs out the gate, off the edge
# The market cross-street must start EAST of the Imperial chrysanthemum field: a public street
# cannot be cut through the protected Imperial planting. This is HIRAMEKI-SPECIFIC (it is the
# only town with a flower field inside its walls), so it stays a per-map invariant rather than
# a general check in check_village.py - hence the local assertion below, which fires on every
# regeneration if a future edit drifts the cross-street back over the field.
CROSS = [(849, 1400), (1300, 1388), (1837, 1403)]
assert CROSS[0][0] >= CHRYS[2] + 30, "market cross-street must start clear of the chrysanthemum field"
s.street(MAIN, width=28, main=True, label="main street")
s.street(CROSS, width=22)

# the town's THEATER STAGE - a roofed performance stage facing an open viewing ground - sited in the Benten
# monastery's precinct, just EAST of it (the NW diagonal rampart hems the ground directly north of Benten),
# facing WEST (rot=90) so its viewing ground opens toward the Benten hall, the audience gathered between
s.theater_stage(856, 1010, rot=90, label="theater stage")

# Big fixed-position buildings go DOWN FIRST, before the packs - the packs' _fits() then flows the small
# houses AROUND them (a pack placed first fills these spots and the big building lands on a house). The
# caravan INN + STABLES just inside the front gate (a county town needs the one; a walled town keeps it
# inside the rampart, fronting the main street, open ground by the stables for the wagon-train animals):
s.inn(1372, 1139, rot=90)   # tight to the main street: no room for a shop row in front (town_has_caravan_inn)
s.stables(1520, 1139)
# a MINORITY of the wealthy keep larger RESIDENCES (budgets.md town wealth tiers): a few VERY-RICH / RICH
# merchants in big homes near the commercial core, and the ~3 MASTER (rich) laborers in larger dwellings
# among the tenements - the rest live small (the house-size variety a county town shows, like a city).
for mx, my in [(975, 1169), (1840, 1315), (1034, 1557), (1422, 1600)]:
    s.building(mx, my, *s._dims("merchant_large"), "merchant_large")
for lx, ly in [(963, 1295), (1146, 1295), (1556, 1295)]:
    s.building(lx, ly, *s._dims("laborer_large"), "laborer_large")

# samurai neighborhood: lining the manor's approach, below the hill
s.pack((861, 964, 1764, 1183), ["samurai"] * 9, step=70)
s.label(1300, 952, "samurai neighborhood", 11, italic=True)

# merchants + shops FRONT the main avenue and the market cross-street (facing them)
s.frontage(MAIN, (["merchant"] * 3 + ["shop"]) * 6, width=28, spacing=56, rows=2)
s.frontage(CROSS, (["merchant"] * 2 + ["shop"]) * 6, width=22, spacing=56, rows=2)
# the laborers' and servants' dwellings fill the blocks flanking the core - those next to
# the cross-street face it; the rest are deep tenement blocks with no street frontage
s.pack((540, 1200, 1130, 1600), ["servant"] * 13 + ["laborer"] * 10, step=46, face_streets="fill")
s.pack((1450, 1200, 1860, 1530), ["laborer"] * 14, step=46, face_streets="fill")
s.label(1300, 1505, "merchant houses & shops", 10, italic=True, color="#5A4326")
s.label(800, 1560, "laborers' & servants' tenements", 9, italic=True, color="#5A4326")

# ---- OUTSIDE: a small guan-xiang gate-market, the segregated burakumin neighborhood, farm rings
s.pack((1080, 1810, 1540, 1980), ["merchant"] * 5 + ["shop"] * 5, step=56, face_streets=True)
s.label(1120, 1795, "gate market", 10, italic=True, color="#5A4326")
# the market flophouse (kichin-yado), OUTSIDE the gate beside the gate market: far-traveling
# peasants who reach the town after the gate shuts at dusk sleep here for a sen before market day
s.flophouse(1720, 1880)
s.pack((2130, 1700, 2330, 1950), ["burakumin"] * 12, step=46)
s.label(2230, 1680, "burakumin neighborhood", 11, italic=True, color="#6B4F2A")
# a noticeable minority of merchant houses keep a fireproof kura (rent-rice / bulk goods of the
# absentee landlords whose tenants farm the surrounding land), drawn AFTER the businesses exist
s.merchant_storehouses(6)
for bb in (OW1, OE1, OE2, OS):
    s.ring(bb, 11, 16, ["plain"])
    s.ring(bb, 9, 44, ["plain"])
    s.ring(bb, 7, 76, ["plain"])
    s.ring(bb, 5, 108, ["plain"])
# OW2 runs off the left edge: ring it too (densely, since most houses fall off-map) so its on-map
# strip still shows worked frontage at village density - farmers build close to even a partial field.
s.ring(OW2, 36, 14, ["plain"])
s.ring(OW2, 28, 38, ["plain"])
# OS presents a long on-map edge by the gate road: two extra close rings meet the worked-frontage density
s.ring(OS, 8, 30, ["plain"])
s.ring(OS, 6, 58, ["plain"])

# the graveyard in the Bishamon monastery's precinct (the Buddhist danka parish ground)
s.cemetery(1840, 1160, 88, 62, label="graveyard")               # the intramural parish ground, by the Bishamon monastery
s.cemetery(2080, 1420, 120, 88, label="common burial ground")    # the MAIN burial ground (a town of ~1,200 over centuries) - large, extramural, well clear of the paddy
# the cremation ground ADJOINS the external common ground (body burned, bones interred next door) -
# the extramural funerary complex; monk-run with burakumin assistants
s.cremation_ground(2100, 1513)

# draw the farmhouses, each with its threshing/drying yard (universal); LAST so every obstacle is known
s.farmsteads()

# communal WELLS among the dwellings (placed after them, in the open gaps); households share these, the
# rest draw from the irrigation pond/channels/stream. Placed AFTER farmsteads() so the FINAL house set
# is known: the threshing pass abandons the odd over-crowded farmhouse, and a well must never be left
# stranded beside one that is no longer there (wells_among_dwellings).
s.place_wells((80, 300, 2500, 1975), spacing=250, near=90)
# the set-apart Benten monastery (west, far from the houses) keeps its OWN ablution well (remote_shrine_has_own_well)
s.shrine_well(700, 1010)
# the Bishamon monastery also sits apart from the dwellings at the to-scale spacing
s.shrine_well(1750, 1050)

# ===== FIRE DEFENSE: a watch-tower =====
# Placed LAST, on a cleared seam the dense town already leaves between its building clusters - so it
# perturbs nothing and stands on an ACTUAL gap. A FIRE-WATCH TOWER (hinomi-yagura, the magistrate's
# bell-watch) stands in the tenement warren, watching its packed rooftops. WHY: settlements.md "Fire towers".
s.fire_tower(1730, 1515, label="fire-watch tower")   # in the east laborer warren, on its clearest interior seam

s.title("Hirameki")

HERE = os.path.dirname(os.path.abspath(__file__))
nb = {}
for b in s.M["buildings"]:
    nb[b["kind"]] = nb.get(b["kind"], 0) + 1
print("farmhouses:", len(s.M["houses"]), "| buildings:", nb, "| finish:", s.finish(os.path.join(HERE, "hirameki")))
