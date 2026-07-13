#!/usr/bin/env python3
"""Nagahara - a walled PROVINCIAL CITY on the Hayakawa river (diagram skill, Mode B, 1px = 3ft).

THE RIVER CITY (the norm - Tango is the exception): Nagahara sits on the WEST BANK of the
Hayakawa, which flows north -> south along its east flank. Per the historical pattern (imperial
China first, Japan agreeing - Xiangyang's Han-river face, Pingyao on the Fen, Okayama on the
Asahi): the trunk river NEVER runs through the walls (the Kaifeng flood lesson - the one great
city that let a river in was devastated seven times); instead the city stands ON the bank, the
river IS the water defense on its flank, and the dug moat covers the three landward faces,
tapping the river upstream (NE) and returning downstream (SE) so the current flushes it.

NO IMPERIAL ROAD: the Imperial highway passes ~10 miles north. A NORTH ROAD leaves the north
gate slanting slightly north-west to meet it (way off-map); the EAST ROAD crosses the Hayakawa
on a timber bridge at the river gate and runs south-east toward the southeastern counties.

The one way water enters the walls: a CARGO CANAL through a WATER GATE (the Suzhou Pan Gate
shuimen pattern - a grated arch with a sluice) to an in-city DOCK BASIN in the merchant
district. Outside the river gate, the WHARF suburb (the riverfront guan-xiang): jetties,
warehouses, the gate market. THE DEAD CROSS THE RIVER: the funerary complex sits on the far
bank (the moat's water set-back leaves no dry ground on the landward fringes, and carrying
the dead over the water suits the geography of the afterlife anyway).

Hayakawa county (see pool/hayakawa-magistracy) is named for the same river and feeds its
taxes to this city. Quarters: W = the samurai/government ward (yamen + 5 ministries behind a
kido-gated fence); NW = the temple neighborhood (Suitengu - the river! - and Ebisu, with the
Ministry of Rites); NE = laborer terraces; E-central = the merchant district around the dock;
SE = the burakumin neighborhood DOWNSTREAM (polluting trades below the city, historically
exact); S-central = laborer/servant rows. Samurai estates lie across the river (SE, per the
estate doctrine), commuting over the bridge.
"""
import math
import os
import random as _random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settlement import Settlement  # noqa: E402
from waterfields import BEAN_GREEN, BUND, build_comb  # noqa: E402

s = Settlement(3200, 2700, seed=47)
s.meta(name="Nagahara", scale="city", walled=True, population=3000, ftpx=3, imperial_road=False,
       clan="Crab", capital_dir="northeast")   # Crab city -> temples to Bishamon + Ebisu; estates toward Otosan Uchi (NE)

# ---- the rampart: a closed ring with a NORTH gate (the north road) and an EAST river gate
# (the bridge road), plus a WATER GATE south of the river gate where the cargo canal enters
CX, CY, RX, RY = 1480, 1330, 494, 460
NRING = 20
WALL = [(round(CX + RX * math.cos(-math.pi / 2 + 2 * math.pi * i / NRING)),
         round(CY + RY * math.sin(-math.pi / 2 + 2 * math.pi * i / NRING))) for i in range(NRING)]
NGATE, EGATE, WGATE_PT = WALL[0], WALL[5], WALL[6]
KIDO_SPOTS = [(1468, 1330, True), (1468, 1410, True), (1020, 1309, True), (1209, 1673, True)]
for kx, ky, kh in KIDO_SPOTS:
    if kh:
        s.block_polys.append([(kx - 25, ky - 38), (kx + 45, ky - 38), (kx + 45, ky + 26), (kx - 25, ky + 26)])
    else:
        s.block_polys.append([(kx - 38, ky - 25), (kx + 26, ky - 25), (kx + 26, ky + 45), (kx - 38, ky + 45)])
s.city_wall(WALL, gates=[NGATE, EGATE], guard_east=[NGATE], water_gates=[WGATE_PT],
            tower_skip=[(1012, 1296), (1212, 1686)])

# ---- the Hayakawa: north -> south along the east flank; the moat joins it at both ends
RIVER = [(2152, 445), (2136, 812), (2126, 1180), (2136, 1548), (2149, 1916), (2163, 2250)]
RIVER_W = s.river(RIVER)
MOAT = s.moat(WALL, gap=24, river=RIVER, river_cut=150)
RING = s.ring_road(WALL, inset=22)
s.bound = [list(p) for p in RING]
MARGIN = 96
s.set_view(CX - RX - 46 - MARGIN, CY - RY - 46 - MARGIN, 2 * (RX + 46 + MARGIN) + 320, 2 * (RY + 46 + MARGIN))

# ---- THE through-road (no Imperial spine - meta imperial_road=False): the north road comes
# down from the distant Imperial highway (off-map NW), enters the north gate, runs the spine
# to the central crossroads, turns east along the main street, leaves by the river gate, and
# crosses the Hayakawa bridge toward the southeastern counties - ONE route, both ends off-map
# (through-traffic is why the city is here; the bend at the crossroads is the market corner)
ROAD = [(1372, 606), (1406, 693), (1448, 778), (1480, 876), (1480, 1330),
        (1979, 1330), (2078, 1330), (2131, 1333), (2216, 1336), (2331, 1470), (2446, 1572), (2572, 1682)]
s.road(ROAD, label="north road", label_xy=(1600, 784))   # kept below the top frame edge (EY0 ~= 728)
s.bridge(2131, 1332, 4, RIVER_W + 26, 15)    # the Hayakawa bridge carries the through-road over the river

# ---- the cargo canal: river -> water gate -> dock basin (the Suzhou pattern)
CANAL = [(2119, 1489), (2032, 1482), (1950, 1473), (1865, 1468)]   # west end reaches INTO the dock basin (feeds it, like a street reaching the road)
s.canal(CANAL)
s.water_gate(1950, 1473, rot=8)
s.dock(1842, 1468, 54, 34)
s.bridge(1919, 1470, 95, 34, 12)             # the ring road bridges the canal just inside the wall

# civic amenities placed FIRST, so the dense packs flow around them.
s.flophouse(1397, 787, label_below=True)                     # outside the NORTH gate
s.flophouse(2038, 1259)                                      # outside the EAST gate, on the wharf
# N-gate caravan cluster, WEST of the spine just inside the gate: this side is naturally OPEN
# ground (the laborer warren packs EAST of the spine), so the stables gets its wagon-train berth
# without carving a hole in the housing. A small reservation keeps the cluster and the guard-house
# label ground clear of any stray placement.
s.block_polys.append([(1398, 918), (1462, 918), (1462, 1052), (1398, 1052)])
s.block_polys.append([(1556, 950), (1718, 950), (1718, 984), (1556, 984)])   # keep the N-gate guard-house label ground clear of the pack
s.stables(1425, 985, rot=90)   # kept >=75px W of the laborer pack (which starts ~x1504) so the animals have open ground
s.flophouse(1425, 940, label_below=True)
s.inn(1440, 1022)   # nudged E of the Ebisu graveyard label
# E-gate caravan cluster: a reserved pocket W of the gate furniture (which fills the E-wall
# strip), N of the main road - reserved up front so the NE laborer pack flows around it
s.block_polys.append([(1682, 1112), (1860, 1112), (1860, 1314), (1682, 1314)])
s.flophouse(1722, 1146, label_below=True)
s.inn(1722, 1192)
s.stables(1779, 1238, rot=90)


def grid(streets, width_ft=18):
    for st in streets:
        s.street(st, width=s.lw(width_ft))


def front(streets, kinds, width_ft=18, spacing=19, rows=1):
    # near-contiguous machiya frontage per the GM row-packing doctrine (see tango.gen.py)
    for st in streets:
        s.frontage(st, list(kinds), width=s.lw(width_ft), spacing=spacing, rows=rows, rowgap=2, jitter=1, setback=s.px(14))


def alleys(lst):
    for a in lst:
        s.alley(a)


# ---- WATER-FIRST COMB FIELDS (waterfields.build_comb - the settled paddy doctrine).
# The legacy paddy_field quilts (45-deg multicolor patchwork, organic blob outlines, no in-field
# water) are replaced by ONE comb per field: a sluice-fed head-race forking into supply canals,
# tapering delivery ditches, one drain collector, water-aligned cascade plots at ONE crop stage,
# azemame bund beads, and a dry-crop hem on the upslope margin. Params are 3 ft/px-scaled:
# plot_across 26px (~78 ft strips) and row_step (13,19) (~40-57 ft cascade rows) keep the real
# plot ~0.08 acre - the same grain the villages draw at 2 ft/px; canal spans sit in the
# 60-260px band so a city-fringe comb stays the size of the field it replaces.
def _pt_seg(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    ll = vx * vx + vy * vy or 1.0
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / ll))
    return math.hypot(px - ax - t * vx, py - ay - t * vy)


def _in_poly(x, y, poly):
    n = len(poly)
    j = n - 1
    c = False
    for i in range(n):
        if ((poly[i][1] > y) != (poly[j][1] > y)) and (x < (poly[j][0] - poly[i][0]) * (y - poly[i][1]) / (poly[j][1] - poly[i][1]) + poly[i][0]):
            c = not c
        j = i
    return c


def furrows(poly, colour, theta):
    """Stylised ridge/furrow lines within a dry-field plot (dry crops are row-cultivated)."""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    fcx, fcy = sum(xs) / len(xs), sum(ys) / len(ys)
    diag = math.hypot(max(xs) - min(xs), max(ys) - min(ys))
    dx, dy = math.cos(theta), math.sin(theta)
    nx, ny = -dy, dx
    cid = s._cid("dry")
    pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in poly)
    g = [f'<clipPath id="{cid}"><polygon points="{pts}"/></clipPath>', f'<g clip-path="url(#{cid})">']
    t = -diag / 2
    while t <= diag / 2:
        mx, my = fcx + nx * t, fcy + ny * t
        g.append(f'<line x1="{mx-dx*diag/2:.1f}" y1="{my-dy*diag/2:.1f}" '
                 f'x2="{mx+dx*diag/2:.1f}" y2="{my+dy*diag/2:.1f}" stroke="{colour}" stroke-width="0.8" opacity="0.8"/>')
        t += 5
    g.append('</g>')
    s.add(''.join(g))


def comb_field(name, sluice, down_deg, seed, field_fall, canal_a, canal_b, offtakes_a,
               offtakes_b=(), dry_band=(14, 26), avoid=(), mirror_ym=None):
    """One comb-doctrine field: build the net, draw it, record the manifest. `avoid` lists
    polylines (moat / ring road) a dry-hem plot must not ride - a colliding plot is skipped
    (the hem is texture on the upslope margin, not load-bearing). `mirror_ym` flips the comb's
    CHIRALITY by computing it in a y-mirrored frame about that line and mirroring the geometry
    back: build_comb always spreads its wide (canal B) flank counterclockwise of the fall, and
    real combs came in both hands - the NW pocket needs the clockwise one. Returns (net,
    envelope, interior point) - the caller records the source channel + rings the farmhouses."""
    if mirror_ym is not None:
        sluice = (sluice[0], 2 * mirror_ym - sluice[1])
        down_deg = (-down_deg) % 360
    net = build_comb(3200, 2700, sluice, seed, down_deg=down_deg, field_fall=field_fall,
                     canal_a_len=canal_a, canal_b_len=canal_b, offtakes_a=offtakes_a,
                     offtakes_b=offtakes_b, plot_across=26, row_step=(13, 19), dry_band=dry_band)
    if mirror_ym is not None:
        def m(pts):
            return [(x, 2 * mirror_ym - y) for x, y in pts]
        net["envelope"] = m(net["envelope"])
        for p in net["plots"]:
            p["poly"] = m(p["poly"])
        for dp in net["dry_plots"]:
            dp["poly"] = m(dp["poly"])
            dp["theta"] = -dp["theta"]           # a furrow heading mirrors with the frame
        for c in net["channels"]:
            c["pts"] = m(c["pts"])
        net["bund_beans"] = m(net["bund_beans"])
        if net["brook"]:
            net["brook"] = m(net["brook"])
    env = [(round(x, 1), round(y, 1)) for x, y in net["envelope"]]
    s.field_polys.append([(p[0], p[1]) for p in env])
    for dp in net["dry_plots"]:
        if any(_pt_seg(x, y, ln[i][0], ln[i][1], ln[i + 1][0], ln[i + 1][1]) < 16
               for ln in avoid for (x, y) in dp["poly"] for i in range(len(ln) - 1)):
            continue                       # hem plot would ride the moat / ring road - skip it
        s.dry_polys.append(dp["poly"])   # footprint-aware: houses/yards/groves stay OFF the crop, not just centred off it
        pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in dp["poly"])
        s.add(f'<polygon points="{pts}" fill="{dp["fill"]}" stroke="#A98C58" stroke-width="1.4" stroke-linejoin="round"/>')
        furrows(dp["poly"], dp["furrow"], dp["theta"])
        s.M["dry_plots"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in dp["poly"]],
                                 "crop": dp["crop"], "theta": round(dp["theta"], 3)})
    for p in net["plots"]:
        pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in p["poly"])
        s.add(f'<polygon points="{pts}" fill="{p["fill"]}" stroke="{BUND}" stroke-width="2" stroke-linejoin="round"/>')
    beads = ''.join(f'<circle cx="{x}" cy="{y}" r="1.4" fill="{BEAN_GREEN}"/>' for x, y in net["bund_beans"])
    s.add(f'<g opacity="0.85">{beads}</g>')
    for c in sorted(net["channels"], key=lambda c: -c["w"]):
        s.field_channel(c["pts"], '#7C9EB0' if c["role"] == "drain" else '#6C9CBE', c["w"], c.get("w_tail", c["w"]))
    exs = [p[0] for p in env]
    eys = [p[1] for p in env]
    pvx = [v[0] for p in net["plots"] for v in p["poly"]]
    pvy = [v[1] for p in net["plots"] for v in p["poly"]]
    s.M["fields"].append({"name": name, "kind": "paddy", "outline": [[x, y] for x, y in env],
                          "bbox": [min(exs), min(eys), max(exs), max(eys)],
                          "vis_bbox": [min(pvx), min(pvy), max(pvx), max(pvy)]})
    for c in net["channels"]:
        s.M["field_ditches"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in c["pts"]],
                                     "role": c["role"], "field": name,
                                     "w": round(c["w"], 1), "w_tail": round(c.get("w_tail", c["w"]), 1)})
    return net, env, (round(sum(exs) / len(exs), 1), round(sum(eys) / len(eys), 1))


def plot_centroid(net, key):
    """Centroid of the plot chosen by `key` over plot centroids - a point guaranteed INSIDE the
    planted field (the envelope centroid of a curved fan can miss, and the water-source checks
    test the channel END with point_in_poly against the outline)."""
    cens = [(sum(v[0] for v in p["poly"]) / len(p["poly"]), sum(v[1] for v in p["poly"]) / len(p["poly"]))
            for p in net["plots"]]
    cx, cy = key(cens)
    return (round(cx, 1), round(cy, 1))


def topo_channel(pts, frm, to, draw_w=0.0):
    """Record a water-topology channel through `pts` (source/sink grounding + the winds/hairline
    conventions) and register its no-build corridor so the farmstead rings avoid it - the checks
    treat a recorded channel exactly like a drawn one. A bend is added on the longest segment when
    the path runs too straight (channel_winds_gently wants a dug channel to wind 5-50px). Pass
    draw_w to also draw it (a visible culvert/runoff ditch); zero = topology only (the comb's own
    drawn head-race carries the visual)."""
    ax, ay = pts[0]
    bx, by = pts[-1]
    chord = math.hypot(bx - ax, by - ay) or 1.0
    dev = max(abs((py - ay) * (bx - ax) - (px - ax) * (by - ay)) / chord for px, py in pts[1:-1]) if len(pts) > 2 else 0.0
    if dev < 6:
        k = max(range(len(pts) - 1), key=lambda i: math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]))
        mx, my = (pts[k][0] + pts[k + 1][0]) / 2, (pts[k][1] + pts[k + 1][1]) / 2
        pts = list(pts[:k + 1]) + [(mx - 12 * (by - ay) / chord, my + 12 * (bx - ax) / chord)] + list(pts[k + 1:])
    poly = [[round(px, 1), round(py, 1)] for px, py in pts]
    s.M["channels"].append({"poly": poly, "frm": frm, "to": to, "w": draw_w or 2.5})
    s.corridors.append(([(px, py) for px, py in poly], 33))
    if draw_w:
        s.field_channel([(px, py) for px, py in poly], '#7C9EB0', draw_w, draw_w)


# ====================================================================== the street skeleton
# the through-road provides the N-S spine and the E main street; city streets hang off it.
# The yamen approach runs WEST from the crossroads through the ward's east kido.
WEST_ST = [(1158, 1330), (1478, 1330)]
grid([WEST_ST], width_ft=22)
SAM_ST = [(1480, 1330), (1480, 1721)]   # starts AT the central crossroads (where the road turns E) and runs down the ward's east flank to the S street
MER_V1 = [(1733, 1238), (1733, 1643)]
MER_V2 = [(1848, 1238), (1848, 1422)]
grid([SAM_ST, MER_V1, MER_V2])

# ====================================================================== W-central: temple neighborhood
# Suitengu (the river fortune - a river city prays to its water) + Ebisu (honest work and
# trade - the wharf's fortune), with the Ministry of Rites that oversees them
# Crab city -> the great temples are its two PATRON fortunes: EBISU here, BISHAMON in the
# samurai quarter (below). SUITENGU, the river fortune a river city honours, is a small wayside
# shrine among the smattering (unlabeled), NOT a great temple (city_temples_dedicated).
TEMPLE_LANE = [(1100, 1204), (1480, 1204)]   # the E-W temple-neighborhood street; Rites + Ebisu front it, it meets the spine
grid([TEMPLE_LANE], width_ft=18)
s.shrine_hall(1160, 1123, "Temple of Bishamon", w=100, h=64, kind="temple", label_below=True)   # a Crab patron (also the warrior fortune); nudged E so its W edge clears the ring road
s.shrine_hall(1388, 1123, "Temple of Ebisu", w=100, h=64, kind="temple", primary=True, label_below=True)   # the other Crab patron
s.cemetery(1135, 1238, 44, 32, label="graveyard")   # Bishamon's danka parish ground, S of the hall (kept clear of the temple lane)
s.cemetery(1388, 1049, 44, 32, label="graveyard", label_above=True)   # Ebisu's danka parish ground, N of the hall
s.ministry(1273, 1240, "Ministry of Rites", w=s.px(140), h=s.px(95))
s.theater_stage(1273, 1001, w=s.px(190), h=s.px(132), rot=0, label="theater stage")   # N-central, opens S; clear of the ring road
for sx, sy in [(1236, 1098), (1273, 1134), (1236, 1171)]:   # small wayside shrines (one is Suitengu, the river fortune) - clustered clear of the graveyards
    s.small_shrine(sx, sy)
s.label(1273, 1296, "temple neighborhood", 9, italic=True, color="#6B2A18")

# ====================================================================== W: the samurai/government ward
# the government + samurai occupy the SW quadrant, WEST of the spine (the merchant district is
# east of it) - sealed by a ward fence that abuts the wall on the W and the SW, entered from the
# commoner side by two kido on the east fence.
GOV_AVE2 = [(1090, 1410), (1480, 1410)]   # the government avenue; meets the spine (SAM_ST) at x1480, W end kept >46px clear of the ring bed
grid([GOV_AVE2])
s.governor_mansion(1273, 1544, s.px(436), s.px(366), "Governor's Mansion", gate_dir="north")
MINS = ["Ministry of Revenue", "Ministry of Retainers", "Ministry of War",
        "Ministry of Works", "Ministry of Justice"]
MIN_POS = [(1078, 1371), (1236, 1371), (1395, 1371), (1100, 1473), (1425, 1473)]   # 3 N of the avenue, 2 S, all fronting it
for (mx, my), name in zip(MIN_POS, MINS):
    s.ministry(mx, my, name, w=s.px(130), h=s.px(90))
s.mausoleum(1273, 1659, 44, 32, label="Mausoleum", gate_dir="north")   # the ruling clan's crypt, below the yamen
for _m in s.M["ministries"] + [s.M["governor_mansion"]]:
    s.block_polys.append([(_m["x"] - _m["w"] / 2 - 30, _m["y"] - _m["h"] / 2 - 30), (_m["x"] + _m["w"] / 2 + 30, _m["y"] - _m["h"] / 2 - 30),
                          (_m["x"] + _m["w"] / 2 + 30, _m["y"] + _m["h"] / 2 + 30), (_m["x"] - _m["w"] / 2 - 30, _m["y"] + _m["h"] / 2 + 30)])
# a ministry's italic label is WIDER than its footprint, so reserve the label's own ground (+ a
# house-half margin) before the samurai pack runs - else a packed house sits behind the label and
# reads as mislabelled (labels_clear_of_other_buildings). Read the boxes the ministry() calls just placed.
for _L in s.M["labels"]:
    if len(_L) > 5 and _L[5].startswith("Ministry"):
        s.block_polys.append([(_L[0] - 15, _L[1] - 12), (_L[2] + 15, _L[1] - 12), (_L[2] + 15, _L[3] + 12), (_L[0] - 15, _L[3] + 12)])
# lace the deep samurai block BEFORE packing so the packer reserves the lane corridors; ends
# stay inset off the ward wall so they do not trip the ward-gate / seal checks
# NO interior ward alleys: the ministries + the yamen fill most of the ward, and the samurai homes
# around them front the three ward streets (WEST_ST, GOV_AVE2, SAM_ST) directly - a deep service
# lane here would only shadow a street or run against a compound, serving too few to justify itself.
s.pack((1032, 1307, 1468, 1640), (["samurai"] * 3 + ["samurai_large"]) * 150, step=13, face_streets="fill")
s.label(1410, 1555, "samurai neighborhood", 10, italic=True, color="#3A352C")   # E of the governor's mansion among the ward's samurai, clear of the burakumin rows to the S
s.ward("samurai", [(995, 1309), (1468, 1309), (1468, 1594), (1191, 1700)],
       gates=[(1468, 1330, True), (1468, 1410, True), (1020, 1309, True), (1209, 1673, True)])   # 2 street kido + 2 ring-road kido
s.label(1428, 1316, "samurai ward gate", 9, italic=True, color="#5A4326")   # inside the ward by the E-fence kido, off the merchant frontage

# ====================================================================== N + NE: the LABORER quarter
# one big contiguous block E of the spine, laced with a street grid wired to the N-gate spine;
# master laborers front the streets, terraces pack the blocks; the E-gate caravan pocket is clear.
LAB_H = [(1480, 1114), (1882, 1114)]   # E end reaches the ring bed at a clean T-junction
LAB_V1, LAB_V2 = [(1618, 1010), (1618, 1282)], [(1848, 1197), (1848, 1282)]
grid([LAB_H, LAB_V1, LAB_V2])
s.fire_tower(1689, 1042, label=None)
front([LAB_V1, LAB_V2], (["shop"] + ["laborer_large"] * 3) * 8, spacing=18, rows=1)
# keep the rowpack rows HOMOGENEOUS (all small terraces): a rowpack sizes each row to its tallest
# house, so a stray laborer_large mid-row would inflate every row and gut capacity. The wealthier
# 'master' laborers (budgets.md's ~12.5% cohort) are seeded on the street frontage and topped up
# individually below, where a larger footprint drops into a gap without heightening a whole row.
_lab = (["laborer"] * 3 + ["servant"]) * 140
# the 1618-1848 street gap (230px) is too wide - lace a mid alley (BEFORE the packs) so no terrace is cut off
# one mid alley for the 1618-1848 street gap: it drops from just below the ring road (top end
# kept >46px clear of the ring bed at ~y957) to LAB_H. No lower stub - the ground S of LAB_H
# here is the reserved E-gate caravan pocket, so an alley there would serve nothing.
alleys([[(1733, 1022), (1733, 1114)]])
# coarse well courts AFTER the alleys (so no wellhead lands on the mid alley) and BEFORE the packs
# (so the terraces flow around them); tight spacing for the dense warren (~1 well per 10-20 households)
s.place_wells((1498, 941, 1908, 1282), spacing=64)
s.place_wells((1556, 1070, 1690, 1266), spacing=48)   # extra courts for the deep mid-strip between the x1618 street and x1530 column
s.rowpack((1498, 886, 1908, 1107), _lab, court_every=4, eave_ft=3)
s.rowpack((1498, 1123, 1908, 1282), _lab, court_every=4, eave_ft=3)
s.label(1635, 1153, "laborer neighborhoods", 10, italic=True, color="#5A4326")   # W of the E-gate caravan flophouse

# ====================================================================== E-central: merchants + the dock
MER_ST = [MER_V1, MER_V2]   # gridded in the skeleton
# storefronts line the main-street stretch of the through-road between the crossroads and
# the river gate (the road-market of a river city, inside the walls)
s.fire_tower(1768, 1519, label="fire tower")   # amid the merchant dwellings, before the packs
s.block_polys.append([(1738, 1500), (1798, 1500), (1798, 1548), (1738, 1548)])   # reserve the fire-tower + its label ground
# reserve the cargo-canal corridor and the walled merchant-estate court BEFORE the packs fill
# this ground: the Suzhou dock strip is a working waterway (no dwelling stands in it) and the
# estate's court is walled ground, so no pack house may land on either
s.block_polys.append([(1852, 1456), (1927, 1456), (1927, 1502), (1852, 1502)])   # canal mouth strip just inside the wall
s.block_polys.append([(1730, 1450), (1832, 1450), (1832, 1532), (1730, 1532)])   # merchant estate court at (1781,1491), 62x46, + a house-half margin
# seat a well in the far-E merchant block BEFORE the frontage/packs run, so it reserves its own
# court and the houses flow around it - the block is otherwise too dense to split its lone well's load
s.well_at(1888, 1400)
for _mrx, _mry in [(1590, 1401), (1590, 1643)]:
    s.block_polys.append([(_mrx - 22, _mry - 16), (_mrx + 22, _mry - 16), (_mrx + 22, _mry + 16), (_mrx - 22, _mry + 16)])
s.frontage([(1503, 1330), (1940, 1330)], (["merchant"] * 3 + ["shop"]) * 16, skip=ROAD,
           width=s.lw(26), spacing=19, rows=2, rowgap=2, jitter=1, setback=s.px(14))
front(MER_ST, (["merchant"] * 3 + ["shop"]) * 8, spacing=19, rows=1)
s.merchant_storehouses(8)
EST_M = [(1781, 1491, "south")]
for ex, ey, gd in EST_M:
    s.merchant_estate(ex, ey, gate_dir=gd)
_ML_SPOTS = [(1590, 1401), (1590, 1643)]
_mer = (["merchant_house"] * 3 + ["servant"] + ["laborer"]) * 110
_MER_COURT = 3
# west strip (1567-1733) lacks a street - lace an alley (BEFORE the packs) so the houses aren't cut off
alleys([[(1617, 1378), (1617, 1456)], [(1617, 1473), (1617, 1594)], [(1617, 1611), (1617, 1689)]])   # top stub pulled >46px clear of the main road
# coarse well courts AFTER the alleys (no wellhead on the x1617 lanes) and BEFORE the packs; tight
# spacing so the merchant warren is not left with over-burdened wells
s.place_wells((1554, 1351, 1915, 1693), spacing=64)
s.place_wells((1716, 1360, 1866, 1620), spacing=52)   # extra courts for the broken east merchant strip (MER_V1 / fire tower / estate leave sparse well ground)
s.rowpack((1567, 1352, 1915, 1456), _mer, court_every=_MER_COURT, eave_ft=3)
s.rowpack((1567, 1473, 1915, 1594), _mer, court_every=_MER_COURT, eave_ft=3)
s.rowpack((1567, 1611, 1915, 1689), _mer, court_every=_MER_COURT, eave_ft=3)
s.label(1722, 1351, "merchant district", 10, italic=True, color="#5A4326")

# ====================================================================== SE: burakumin (downstream)
# the polluting trades sit BELOW the city on the current - downstream placement is the
# historically exact site for them (tanners, dyers, the death-trades)
# the DOWNSTREAM (south) quarter: burakumin (the polluting trades below the city on the current)
# with servants; one big block spanning the south interior, laced by the S street
BUR_ST = [[(1300, 1723), (1641, 1723)]]   # W end pulled clear of the ring bed (which hugs close at the SW arc)
grid(BUR_ST)
s.fire_tower(1388, 1698, label=None)   # amid the downstream quarter, before the packs
s.place_wells((1258, 1666, 1650, 1778), spacing=56)
s.rowpack((1258, 1664, 1650, 1712), (["burakumin"] * 2 + ["servant"] * 2) * 55, court_every=6, eave_ft=3)
s.rowpack((1258, 1737, 1650, 1785), (["burakumin"] * 2 + ["servant"] * 2) * 55, court_every=6, eave_ft=3)
s.label(1439, 1670, "burakumin", 10, italic=True, color="#6B4F2A")

# ====================================================================== OUTSIDE the walls
s.bound = None
# the WHARF suburb (the riverfront guan-xiang) outside the river gate: jetties on the bank,
# warehouse-and-market rows along the quay, the gate market of a river city
for jy in (1199, 1293, 1392):
    s.jetty(2101, jy, rot=0, length=22)   # root on the river's WEST bank (~2101 = centerline 2126 - half-width 20 - 5px onto land), running E into the water
QUAY = [(2062, 1226), (2062, 1434)]
s.frontage(QUAY, (["merchant"] * 2 + ["shop"]) * 6, width=s.lw(18), spacing=19, rows=2, rowgap=2, jitter=1, setback=s.px(14))
s.label(2050, 1188, "wharf", 10, italic=True, color="#5A4326")

# samurai ESTATES across the river to the NORTHEAST (toward Otosan Uchi - a samurai builds his
# country seat on the capital-facing side), N of the bridge road and clear of it, commuting in
# over the Hayakawa bridge. Sizes + gate_dir vary; the inner ones straddle the cropped edge.
EST = [(2239, 882, 94, 62, "south"), (2366, 950, 90, 60, "west"), (2234, 1036, 86, 58, "north"),
       (2382, 1088, 84, 56, "west"), (2262, 1192, 78, 52, "south"), (2423, 1222, 72, 48, "west")]
for ex, ey, ew, eh, gd in EST:
    s.manor(ex, ey, ew, eh, "", gate_dir=gd)
s.label(2315, 1296, "samurai estates", 10, italic=True, color="#3A352C")

# surrounding farmland: three large moat-fed combs on the landward faces; a river-fed comb on
# the far bank (its tap draws straight off the Hayakawa)
MOAT_FARMS = [("fw1", (974, 1066), 190, 21, 170, (150, 200), (90, 120), (0.35, 0.7)),
              ("fw2", (940, 1468), 168, 22, 180, (150, 200), (90, 120), (0.4, 0.75)),
              ("fs1", (1273, 1859), 130, 23, 170, (130, 170), (85, 115), (0.4, 0.78))]
for nm, tap, dd, sd, ff, ca, cb, oa in MOAT_FARMS:
    mp = min(MOAT, key=lambda p: (p[0] - tap[0]) ** 2 + (p[1] - tap[1]) ** 2)
    _ol = math.hypot(mp[0] - CX, mp[1] - CY) or 1.0
    sl = (round(mp[0] + 30 * (mp[0] - CX) / _ol), round(mp[1] + 30 * (mp[1] - CY) / _ol))
    s.field_channel([mp, sl], '#6C9CBE', 7, 7)
    _net, _env, _cen = comb_field(nm, sl, dd, sd, ff, ca, cb, oa, avoid=(MOAT,))
    _pd = plot_centroid(_net, lambda cs: max(cs, key=lambda c: c[1]))
    # pull the delivery endpoint a touch toward the field centroid so it lands a clear >=10px
    # INSIDE the outline (a bottom-row plot centroid can sit within a bund's width of the edge)
    _pd = (round(0.80 * _pd[0] + 0.20 * _cen[0], 1), round(0.80 * _pd[1] + 0.20 * _cen[1], 1))
    topo_channel([(mp[0], mp[1]), sl, _pd], {"kind": "moat"}, {"kind": "field", "name": nm})
    _dr = next(c["pts"] for c in _net["channels"] if c["role"] == "drain")
    topo_channel([tuple(_dr[-2]), tuple(_dr[-1])], {"kind": "drain"}, {"kind": "offmap"})
    s.ring(('poly', _env), 26, 15, ["plain"])
    s.ring(('poly', _env), 20, 40, ["plain"])
# THE DEAD CROSS THE RIVER: the funerary complex on the far bank, DOWNSTREAM (south) of the
# city and south of the bridge road - the polluting death-work kept below the city on the
# current, and bearing the dead over the water suits the geography of the afterlife. (The moat's
# water set-back leaves no dry landward fringe in the cropped view; the far bank's farmland runs
# on east beyond the frame.) Cremation set back >=130px from the bridge road, adjoining the
# external common ground.
# nudged W (and the pyre up) so their labels sit fully inside the right/bottom frame edge while
# the complex stays well clear of the river's east bank
s.cemetery(2360, 1765, 90, 64, label="common burial ground")
s.cremation_ground(2378, 1852)
s.ossuary(2360, 1682)

s.bridges()
s.farmsteads()

def top_up(kind, region, need, count_kinds=None):
    kinds = set(count_kinds or (kind,))
    have = sum(1 for b in s.M["buildings"] if b["kind"] in kinds)
    w_, h_ = s._dims(kind)
    gov = s.M.get("governor_mansion")
    civ = [(m["x"], m["y"], m["w"], m["h"]) for m in s.M.get("ministries", [])]
    if gov:
        civ.append((gov["x"], gov["y"], gov["w"], gov["h"]))
    labs = [tuple(lb[:4]) for lb in s.M.get("labels", [])]
    stab = [(b["x"], b["y"]) for b in s.M.get("buildings", []) if b.get("kind") == "stables"]

    def ok(gx, gy):
        if any(abs(gx - cx) <= (cw + w_) / 2 + 15 and abs(gy - cy) <= (ch + h_) / 2 + 15 for cx, cy, cw, ch in civ):
            return False                                     # ministries/yamen stand-clear margin
        if any((gx - sx) ** 2 + (gy - sy) ** 2 < 85 ** 2 for sx, sy in stab):
            return False                                     # the caravan stables' open ground
        return not any(min(x1_, gx + w_ / 2 + 2) - max(x0_, gx - w_ / 2 - 2) > 0
                       and min(y1_, gy + h_ / 2 + 2) - max(y0_, gy - h_ / 2 - 2) > 0
                       for x0_, y0_, x1_, y1_ in labs)       # placed label boxes stay readable
    def exact_clear(gx, gy):
        # _fits' circle test is conservative for rectangles (it rejects diagonal offsets whose
        # boxes do not actually meet), so the LAST sweep tests exact axis-aligned boxes + 3px -
        # but keeps a REAL berth from wellheads (city_wells_in_block_interiors wants the court open)
        if s._in_blocked(gx, gy) or s._near_corridor(gx, gy):
            return False
        if s.bound and not _in_poly(gx, gy, s.bound):
            return False
        if any(abs(gx - w2["x"]) < 26 and abs(gy - w2["y"]) < 26 for w2 in s.M.get("wells", [])):
            return False
        return all(abs(gx - px) >= (w_ + pw) / 2 + 3 or abs(gy - py) >= (h_ + ph) / 2 + 3
                   for (px, py, pw, ph) in s.placed)

    x0, y0, x1, y1 = region
    for pad in (7, 4, "exact"):       # tighter sweeps only when the padded pass leaves the floor unmet
        gy = y0
        while gy <= y1 and have < need:
            gx = x0
            while gx <= x1 and have < need:
                if ok(gx, gy) and (exact_clear(gx, gy) if pad == "exact" else s._fits(gx, gy, w_ + pad, h_ + pad)):
                    s.building(gx, gy, w_, h_, kind)
                    have += 1
                gx += 9
            gy += 10
        if have >= need:
            break
    return have


def _inwall(x, y):
    n = len(WALL)
    j = n - 1
    c = False
    for i in range(n):
        if ((WALL[i][1] > y) != (WALL[j][1] > y)) and (x < (WALL[j][0] - WALL[i][0]) * (y - WALL[i][1]) / (WALL[j][1] - WALL[i][1]) + WALL[i][0]):
            c = not c
        j = i
    return c

DWELL = ("laborer", "laborer_large", "servant", "burakumin", "merchant", "merchant_house",
         "merchant_large", "samurai", "samurai_large")


def _dwell_count():
    # no agricultural district here - a standard city counts URBAN dwellings only (its farmers
    # all live outside; the _inwall farm term is zero and kept only for symmetry with Tango)
    return (sum(1 for b in s.M["buildings"] if b["kind"] in DWELL)
            + sum(1 for h in s.M["houses"] if _inwall(h["x"], h["y"])))


top_up("samurai", (1032, 1307, 1470, 1600), 48, count_kinds=("samurai", "samurai_large"))
top_up("merchant_house", (1549, 1347, 1905, 1690), 160,
       count_kinds=("merchant", "merchant_house", "merchant_large"))
# seat the wealthier 'master' laborers (laborer_large) FIRST, into gaps in the warren, before the
# plain-laborer fill claims that room - ~12.5% of the laborer cohort per budgets.md
top_up("laborer_large", (1492, 882, 1905, 1290), 32)
top_up("laborer", (1492, 882, 1905, 1290), 305, count_kinds=("laborer", "laborer_large"))
top_up("servant", (1549, 1347, 1905, 1690), 90)
for _kind, _region, _cap in (("servant", (1492, 933, 1905, 1290), 130),
                             ("laborer", (1549, 1347, 1905, 1690), 260),
                             ("servant", (1232, 1677, 1624, 1720), 60),
                             ("burakumin", (1232, 1677, 1624, 1722), 40),
                             ("laborer", (1492, 882, 1905, 1290), 305),
                             ("servant", (1549, 1347, 1905, 1690), 150)):
    _dw = _dwell_count()
    if _dw >= 558:
        break
    top_up(_kind, _region, min(_cap, sum(1 for b in s.M["buildings"] if b["kind"] == _kind) + (558 - _dw)))



for _mx, _my in _ML_SPOTS:
    s.building(_mx, _my, *s._dims("merchant_large"), "merchant_large")

# FINE global well pass (Tango pattern): after every dwelling is placed, drop wells into the
# nearest clear COURT (near=46 gates each to sit among homes, so wellheads land in block
# interiors, not on lanes). This is what carries the well-density + neighborhoods-have-wells
# checks - the coarse per-quarter passes above only reserve the courts.
s.place_wells((1492, 933, 1908, 1290), spacing=42, near=48)    # laborer warren
s.place_wells((1549, 1347, 1915, 1693), spacing=42, near=48)   # merchant district
s.place_wells((1232, 1677, 1646, 1722), spacing=42, near=48)   # downstream burakumin strips
# a second offset sweep catches the dense pockets the first grid still leaves over-burdened
s.place_wells((1520, 950, 1908, 1290), spacing=46, near=48)    # laborer warren, offset
s.place_wells((1560, 1360, 1915, 1690), spacing=46, near=48)   # merchant district, offset

s.title("Nagahara")

HERE = os.path.dirname(os.path.abspath(__file__))
nb = {}
for b in s.M["buildings"]:
    nb[b["kind"]] = nb.get(b["kind"], 0) + 1
print("farmhouses:", len(s.M["houses"]), "| buildings:", nb, "| total urban:", sum(nb.values()),
      "| estates:", len(s.M["manors"]), "| finish:", s.finish(os.path.join(HERE, "nagahara")))
