#!/usr/bin/env python3
"""Hirameki - a WALLED border town (diagram skill, Mode B, town scale).

A county seat of ~1,200 (per budgets.md), drawn at TOWN scale: a LARGER canvas and a finer
building grain (s.bscale) than a village, so the rampart encloses the whole town proper.
Historically a Chinese walled county seat / Japanese jokamachi keeps the urban castes -
merchants, artisans, LABORERS, servants, and samurai - INSIDE the walls, zoned around the
magistrate's hilltop citadel; only the farmland/farmhouses, the segregated burakumin
neighborhood, and a small guan-xiang gate-market lie outside. The surrounding farmers retreat
inside during a raid. The hill's steep back defends the north flank; the Imperial
chrysanthemum field abuts the inside of the west rampart.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settlement import Settlement  # noqa: E402

s = Settlement(2600, 1820, seed=70)
# downhill is SOUTH: the hill/manor sit in the north, so the land falls away southward and
# the streams flow north-to-south; irrigation channels must run downhill (tap upstream/north
# of where they feed each field)
# Clan: LION (current holder) - its patron fortunes are Bishamon + Daikoku. But Hirameki
# CHANGED HANDS during the Lion/Crane war, so its monasteries are special (override): the
# main one is to Bishamon (Lion's), and a much smaller, older one to Benten (Crane's) sits
# on the far side of town - a relic of Crane rule. Hence monastery_fortunes is set explicitly.
s.meta(name="Hirameki", scale="town", walled=True, torii_expected=5, downhill="south",
       clan="Lion", monastery_fortunes=["Bishamon", "Benten"], population=720)   # residents DEPICTED (dwellings x5); urban housing full, most farms off-map - a slice of the ~1,200 county
s.bscale = 0.82   # town-scale building grain (denser than a village)

# ---- OUTSIDE the walls: streams + farm fields + farmhouses (one field runs off the edge)
s.stream([(250, -10), (175, 470), (255, 940), (160, 1400), (220, 1830)])
s.stream([(2430, -10), (2390, 560), (2460, 1100), (2400, 1830)])
OW1 = (250, 380, 510, 620)
OW2 = (-120, 1000, 110, 1280)     # off the left edge
OE1, OE2 = (1990, 440, 2270, 700), (2080, 980, 2360, 1240)
OS = (640, 1660, 1040, 1815)      # SW of the gate, off the bottom edge (beside the road, not under it)
# irrigation channels tap the streams to feed the on-map fields (the off-edge fields draw
# their water off-map); drawn before the fields so each field paints over the channel's end
s.channel((185, 430), (360, 560), {"kind": "stream"}, {"kind": "field", "name": "w1"})
s.channel((2390, 490), (2205, 620), {"kind": "stream"}, {"kind": "field", "name": "e1"})
s.channel((2448, 1030), (2215, 1160), {"kind": "stream"}, {"kind": "field", "name": "e2"})
for bb, nm in [(OW1, "w1"), (OW2, "w2"), (OE1, "e1"), (OE2, "e2"), (OS, "s1")]:
    s.paddy_field(bb, "", nm, amp=24)

# ---- the hill (north) with the Magistrate's Manor on top (the citadel)
sx, sy = s.hill(1300, 480, 560, 360, steep=True)
s.manor(1300, 415, 360, 216, "Magistrate's Manor", gate_dir="south")   # gate faces the town below

# ---- the irregular rampart (anchored to the hill, climbing both flanks); the gate is
# south; the west face is a straight run the chrysanthemum field abuts flush
# the S/SE/E faces hug the built core (the monastery + laborer quarters) rather than
# enclosing empty corner space - a tighter line is cheaper to build (wall_hugs_the_town).
# The south face rides just below the laborer blocks, dipping only at the center for a modest
# gate forecourt; the east face encloses the cross-street and east side, then tapers up to
# the Bishamon monastery and the hill.
WALL = [(1000, 500), (820, 720), (660, 960), (660, 1340),
        (780, 1410), (1100, 1440), (1300, 1500), (1500, 1440), (1800, 1340),
        (1850, 1040), (1800, 860), (1700, 500)]
s.wall(WALL, gate=(1300, 1500))
s.label(1300, 1560, "front gate (guard station + tower)", 11, italic=True, color="#3A352C")

# ---- INSIDE: chrysanthemum field (abuts west wall), monastery, the zoned urban core
CHRYS = (666, 1020, 880, 1300)   # the Imperial chrysanthemum field (x0, y0, x1, y1)
s.flower_field(CHRYS, "chrysanthemum field", amp=8, flat_west=True)
# main town monastery (to Bishamon, the Lion patron), on the east side. It has a long, clear
# approach south to the market cross-street, so it fronts a proper torii AVENUE (sando) of
# several arches rather than a single gate (monastery_torii_scale_with_space).
s.shrine_hall(1700, 950, "Monastery of Bishamon", w=150, h=98, kind="monastery", primary=True,
              torii=[(1700, 1052), (1700, 1102), (1700, 1152), (1700, 1202)])
# the older, much smaller Benten monastery (Crane patron) on the OPPOSITE (west) side, inside
# the walls - a relic of the town's time under Crane rule. It is wedged hard against the west
# rampart and the Imperial chrysanthemum field, so there is room for only a SINGLE torii arch.
s.shrine_hall(770, 940, "Monastery of Benten", w=60, h=40,
              kind="monastery", primary=False, torii=[(770, 998)])

# street plan: the gate-to-yamen main avenue + a market cross-street (both fully built up).
# The laborer/servant quarters behind them are accessed off the cross-street and otherwise
# sit as deep tenement blocks with no street frontage (the poor can't afford it) - no
# speculative back-lanes that would dead-end empty, per `streets_have_buildings`.
MAIN = [(1300, 1840), (1300, 1568), (1300, 1300), (1300, 1060), (1300, 870)]   # runs out the gate, off the edge
# The market cross-street must start EAST of the Imperial chrysanthemum field: a public street
# cannot be cut through the protected Imperial planting. This is HIRAMEKI-SPECIFIC (it is the
# only town with a flower field inside its walls), so it stays a per-map invariant rather than
# a general check in check_village.py - hence the local assertion below, which fires on every
# regeneration if a future edit drifts the cross-street back over the field.
CROSS = [(930, 1238), (1300, 1225), (1740, 1240)]
assert CROSS[0][0] >= CHRYS[2] + 30, "market cross-street must start clear of the chrysanthemum field"
s.street(MAIN, width=28, main=True, label="main street")
s.street(CROSS, width=22)

# the town's THEATER STAGE - a roofed performance stage facing an open viewing ground - sited in the Benten
# monastery's precinct, just EAST of it (the NW diagonal rampart hems the ground directly north of Benten),
# facing WEST (rot=90) so its viewing ground opens toward the Benten hall, the audience gathered between
s.theater_stage(920, 918, rot=90, label="theater stage")
# FIRE DEFENSE (a walled town's dense wooden core): a cleared FIREBREAK (hiyokechi/hirokoji) in the
# commercial heart, just north of the east cross-street's shops - too valuable to leave idle, it fills
# with removable market stalls, so the fire gap doubles as the market ground. Placed BEFORE the east
# packs so the laborers flow around it. A FIRE-WATCH TOWER (hinomi-yagura) stands among the laborer
# tenements: the magistrate's watchman rings its bell in a cadence that tells the town how near a blaze is.
s.firebreak(1610, 1126, 156, 112, label="firebreak (market ground)")
s.fire_tower(1600, 1320, label="fire-watch tower")

# Big fixed-position buildings go DOWN FIRST, before the packs - the packs' _fits() then flows the small
# houses AROUND them (a pack placed first fills these spots and the big building lands on a house). The
# caravan INN + STABLES just inside the front gate (a county town needs the one; a walled town keeps it
# inside the rampart, fronting the main street, open ground by the stables for the wagon-train animals):
s.inn(1398, 1024, rot=90)
s.stables(1510, 1024)
# a MINORITY of the wealthy keep larger RESIDENCES (budgets.md town wealth tiers): a few VERY-RICH / RICH
# merchants in big homes near the commercial core, and the ~3 MASTER (rich) laborers in larger dwellings
# among the tenements - the rest live small (the house-size variety a county town shows, like a city).
for mx, my in [(1034, 1048), (1772, 1168), (1082, 1366), (1400, 1402)]:
    s.building(mx, my, *s._dims("merchant_large"), "merchant_large")
for lx, ly in [(1024, 1152), (1174, 1152), (1510, 1152)]:
    s.building(lx, ly, *s._dims("laborer_large"), "laborer_large")

# samurai neighborhood: lining the manor's approach, below the hill
s.pack((940, 880, 1680, 1060), ["samurai"] * 9, step=58)
s.label(1300, 868, "samurai neighborhood", 11, italic=True)

# merchants + shops FRONT the main avenue and the market cross-street (facing them)
s.frontage(MAIN, (["merchant"] * 3 + ["shop"]) * 6, width=28, spacing=46, rows=2)
s.frontage(CROSS, (["merchant"] * 2 + ["shop"]) * 6, width=22, spacing=46, rows=2)
# the laborers' and servants' dwellings fill the blocks flanking the core - those next to
# the cross-street face it; the rest are deep tenement blocks with no street frontage
s.pack((700, 1090, 1150, 1550), ["servant"] * 13 + ["laborer"] * 13, step=42, face_streets="fill")
s.pack((1450, 1090, 1780, 1550), ["laborer"] * 17, step=42, face_streets="fill")
s.label(1300, 1330, "merchant houses & shops", 10, italic=True, color="#5A4326")
s.label(820, 1430, "laborers' & servants' tenements", 9, italic=True, color="#5A4326")

# ---- OUTSIDE: a small guan-xiang gate-market, the segregated burakumin neighborhood, farm rings
s.pack((1080, 1600, 1540, 1794), ["merchant"] * 5 + ["shop"] * 5, step=46, face_streets=True)
s.label(1300, 1600, "gate market", 10, italic=True, color="#5A4326")
# the market flophouse (kichin-yado), OUTSIDE the gate beside the gate market: far-traveling
# peasants who reach the town after the gate shuts at dusk sleep here for a sen before market day
s.flophouse(1690, 1690)
s.pack((2060, 1500, 2360, 1780), ["burakumin"] * 12, step=44)
s.label(2210, 1484, "burakumin neighborhood", 11, italic=True, color="#6B4F2A")
# a noticeable minority of merchant houses keep a fireproof kura (rent-rice / bulk goods of the
# absentee landlords whose tenants farm the surrounding land), drawn AFTER the businesses exist
s.merchant_storehouses(6)
for bb in (OW1, OE1, OE2, OS):
    s.ring(bb, 8, 16, ["plain"])
    s.ring(bb, 7, 48, ["plain"])
    s.ring(bb, 6, 80, ["plain"])
# OW2 runs off the left edge: ring it too (densely, since most houses fall off-map) so its on-map
# strip still shows worked frontage at village density - farmers build close to even a partial field.
s.ring(OW2, 30, 15, ["plain"])
s.ring(OW2, 24, 40, ["plain"])

# the graveyard in the Bishamon monastery's precinct (the Buddhist danka parish ground)
s.cemetery(1786, 1042, 88, 62, label="graveyard")               # the intramural parish ground, by the Bishamon monastery
s.cemetery(1895, 1255, 120, 88, label="common burial ground")    # the MAIN burial ground (a town of ~1,200 over centuries) - large, extramural, well clear of the paddy
# the cremation ground ADJOINS the external common ground (body burned, bones interred next door) -
# the extramural funerary complex; monk-run with burakumin assistants
s.cremation_ground(1915, 1348)

# draw the farmhouses, each with its threshing/drying yard (universal); LAST so every obstacle is known
s.farmsteads()

# communal WELLS among the dwellings (placed after them, in the open gaps); households share these, the
# rest draw from the irrigation pond/channels/stream. Placed AFTER farmsteads() so the FINAL house set
# is known: the threshing pass abandons the odd over-crowded farmhouse, and a well must never be left
# stranded beside one that is no longer there (wells_among_dwellings).
s.place_wells((80, 300, 2375, 1775), spacing=280, near=85)

s.title("Hirameki")
s.compass()

HERE = os.path.dirname(os.path.abspath(__file__))
nb = {}
for b in s.M["buildings"]:
    nb[b["kind"]] = nb.get(b["kind"], 0) + 1
print("farmhouses:", len(s.M["houses"]), "| buildings:", nb, "| finish:", s.finish(os.path.join(HERE, "hirameki")))
