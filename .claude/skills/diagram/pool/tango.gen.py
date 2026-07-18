#!/usr/bin/env python3
"""Tango - a walled PROVINCIAL CITY (diagram skill, Mode B, city scale, 1px = 3ft).

Historical model: a Chinese walled provincial seat / Japanese jokamachi - a closed MOATED
rampart sized to hug the ~600-household city (a wall encloses what it must defend, no large
unused ground inside), with the Imperial road as the N-S spine and a connected GRID of city
streets dividing each quarter into blocks. Within a block the street-facing buildings front
the streets and the bulk of the housing packs into TIGHT ROWS behind them (the row-packing
doctrine - see settlements.md). The placement is bounded by the wall (s.bound), so the dense
quarters fill the ring's shape to the rampart.

TO SCALE at the GM's city scale, 1px = 3ft. The wall's semi-axes are 487x457px (~1,461 x
1,371 ft): ~59 walled hectares for ~3,000 people = ~51/ha - the LOW end of the real 100-250/ha
walled-settlement band, which is Tango's canon (an average provincial-city population with
above-average in-wall space per capita BECAUSE of its agricultural district). The first
1px=3ft pass kept the old 840x780 ring and produced a ~17/ha ghost town; the ring was then sized
to hug the city. Feature 006 (per-quarter density + no extramural commoners) revealed the hugged
ring had been meeting 3,000 partly by SPILLING ~12 dwellings past the wall, so the ring was
enlarged a hair (a uniform x1.015 from the earlier 480x450) - the GM's call: keep the round
3,000 and let the honest-inside figure meet it, rather than trim the declared population.

The four quarters (split by the road and an E-W axis) - same layout as ever:
  - NW: the (unusual, tunable - agricultural_district=True) AGRICULTURAL district - in-wall
        fields fed by an in-wall pond, plus the city's in-wall BURAKUMIN neighborhood (siege need).
  - NE: the LABORER neighborhoods - terrace bands behind the street frontage.
  - SW: the MERCHANT district + a TEMPLE neighborhood (Temples of Benten + Daikoku, the Crane
        patron fortunes) holding the Ministry of Rites that oversees them.
  - SE: the provincial GOVERNMENT (governor's mansion + five of the six ministries) and the
        SAMURAI neighborhood, with a Temple of Bishamon (the warrior fortune) among them.
Wealthy samurai keep walled ESTATES of varying size outside the SE wall and commute in. All
six ministries (Rites, Revenue, Retainers, War, Works, Justice) appear; civic amenities ported
from the town tier: merchant-house kura, a market flophouse, a theater stage (in the Benten precinct).
"""
import math
import os
import random as _random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from citybudget import CityProgram, budget_to_manifest, plan_city  # noqa: E402
from settlement import Settlement  # noqa: E402
from waterfields import BEAN_GREEN, BUND, build_comb  # noqa: E402

s = Settlement(3200, 2700, seed=162)
s.meta(name="Tango", scale="city", walled=True, agricultural_district=True, population=3000, ftpx=3,
       clan="Crane", capital_dir="southeast")   # Crane city -> Benten + Daikoku; estates toward Otosan Uchi (SE)   # ~600 dwellings x5; the shops/civic/government buildings are EXTRA, not housing. ftpx=3: the GM's provincial-city scale, 1px=3ft -> bscale 1/3 (a 46ft farmhouse = 15px)

# ---- feature 009: the SPACE BUDGET the wall answers to. Tango predates budget-first sizing and
# is the model's CALIBRATION ANCHOR: plan_city derives rx,ry = 487.4 x 457.3 for this program -
# the shipped 487x457 ring to +0.1% - so the hand-sized wall is kept verbatim and the budget is
# recorded for the city_wall_matches_budget gate (enclosure sits ~-0.25% off the required area).
BUDGET = plan_city(CityProgram(population=3000, agricultural_district=True, aspect=457 / 487, nring=22), canvas=(3200, 2700))
s.meta(budget=budget_to_manifest(BUDGET))

# ---- the closed rampart (a near-elliptical ring) sized to hug the city, with N and S gates
CX, CY, RX, RY = 1602, 1328, 487, 457
NRING = 22
WALL = [(round(CX + RX * math.cos(-math.pi / 2 + 2 * math.pi * i / NRING)),
         round(CY + RY * math.sin(-math.pi / 2 + 2 * math.pi * i / NRING))) for i in range(NRING)]
NGATE, SGATE = WALL[0], WALL[NRING // 2]
s.city_wall(WALL, gates=[NGATE, SGATE], guard_east=[NGATE], tower_skip=[(2065, 1364), (1655, 1748)])   # the fence-END kido spots (E + SW ring-road gates): the gates keep their crossings, the towers slide a short way along the wall
MOAT = s.moat(WALL, gap=24)                  # the moat hugs the wall base (~72 ft out; real seats kept it close)
# a ring road (順城街) hugs the inside of the wall, leaving the wall-clear patrol zone; the quarters
# pack INSIDE it (s.bound = the ring loop), off the rampart
RING = s.ring_road(WALL, inset=22)
s.bound = [list(p) for p in RING]            # placement stays inside the ring road, off the wall

# ---- DECLARED QUARTERS (feature 006): the interior tiles into zoned regions so density is judged
# PER QUARTER. Tango splits at the road (x=CX) and the E-W axis (y=CY) into four wedges of the
# ring-inset ellipse; the NW wedge subdivides into the agricultural district (a reserve) above and
# the burakumin quarter (residential) below. Density is measured over housing-available ground, so
# the government wedge (mostly yamen + ministries) reads as a civic precinct, not under-built.
def _ipt(i, n=48, inset=24):
    a = -math.pi / 2 + 2 * math.pi * i / n
    return (CX + (RX - inset) * math.cos(a), CY + (RY - inset) * math.sin(a))


def _wedge(i0, i1, n=48):
    return [(CX, CY)] + [_ipt(i, n) for i in range(i0, i1 + 1)]


def _clip_h(poly, ys, keep_above):
    # Sutherland-Hodgman clip of a polygon to the half-plane y<=ys (keep_above) or y>=ys.
    out = []
    for k in range(len(poly)):
        x0, y0 = poly[k]
        x1, y1 = poly[(k + 1) % len(poly)]
        in0 = (y0 <= ys) if keep_above else (y0 >= ys)
        in1 = (y1 <= ys) if keep_above else (y1 >= ys)
        if in0:
            out.append((x0, y0))
        if in0 != in1:
            t = (ys - y0) / (y1 - y0)
            out.append((x0 + t * (x1 - x0), ys))
    return out


_NE = _wedge(0, 12)      # top -> right : the laborer warren
_SE = _wedge(12, 24)     # right -> bottom : the government / samurai ward
_SW = _wedge(24, 36)     # bottom -> left : the merchant district + temple neighborhood
_NW = _wedge(36, 48)     # left -> top : agricultural district (above) + burakumin (below)
s.quarter(_NE, "residential")
s.quarter(_SE, "mixed")
s.quarter(_SW, "mixed")
s.quarter(_clip_h(_NW, 1211, True), "reserve", kind="agricultural_district")
s.quarter(_clip_h(_NW, 1211, False), "residential")
# crop the rendered map tight to the walled city - a city map is about the city, not its
# countryside, so estates and farmland run off the edge. A ~90px margin past the moat leaves
# room for the title (top-left) and compass (top-right) above the rampart, plus a working
# fringe of moat-fed farmland.
MARGIN = 96
s.set_view(CX - RX - 46 - MARGIN, CY - RY - 46 - MARGIN, 2 * (RX + 46 + MARGIN), 2 * (RY + 46 + MARGIN))

# ---- the Imperial road (N-S spine, off both edges, through both gates), the moat-feeder, gates
# the label names the IMPERIAL road - placed OUTSIDE the north gate; inside the walls the same
# roadway is a city street (a city, not Imperial, responsibility), so the label must sit beyond a gate
IMPROAD = [(1602, 709), (1602, CY - RY), (1602, 1328), (1602, CY + RY), (1602, 1957)]
s.road(IMPROAD, label="Imperial Road", label_xy=(1704, 790))
_mnw = min(MOAT, key=lambda p: (p[0] - 1247) ** 2 + (p[1] - 993) ** 2)   # a moat vertex on the NW
s.stream([(922, 704), (1034, 841), (_mnw[0], _mnw[1])], width=s.px(66))   # off-map NW source feeding the moat - as WIDE as the moat (it must supply the moat's full flow)

# the WARD GATES' ground is reserved before anything builds: each kido + its guard box holds a
# fixed crossing on the samurai ward fence, but s.ward draws them near the END of the gen - long
# after the packs - so without these block_polys a row house lands under a guard box (the boxes
# hang W of a vertical kido, N of a horizontal one; reserved with a ~17px margin (a samurai_large's
# half-diagonal) so a footprint CENTER-test keeps whole footprints out). Also feeds tower_skip.
KIDO_SPOTS = [(1622, 1455, True), (1704, 1364, False), (1805, 1364, False),
              (1896, 1364, False), (2065, 1364, False), (1655, 1748, True)]
for kx, ky, kh in KIDO_SPOTS:
    if kh:
        s.block_polys.append([(kx - 25, ky - 38), (kx + 45, ky - 38), (kx + 45, ky + 26), (kx - 25, ky + 26)])
    else:
        s.block_polys.append([(kx - 38, ky - 25), (kx + 26, ky - 25), (kx + 26, ky + 45), (kx - 38, ky + 45)])

# civic amenities placed FIRST, so the dense packs flow around them.
# CARAVAN facilities just INSIDE each gate (a transit zone): a flophouse + a prominent INN + a
# STABLES with open ground for the wagon-trains' draft animals; plus a market flophouse OUTSIDE
# each gate for late arrivals who find the gate shut at dusk.
s.flophouse(1509, 780, label_below=True)                     # outside the NORTH gate
s.flophouse(1704, 1862)                                      # outside the SOUTH gate, by the gate market
# N-gate caravan cluster, EAST of the road inside the gate (the NW is the agri district's)
s.flophouse(1645, 991)
s.inn(1645, 1029)
s.stables(1643, 1066, rot=90)
# S-gate caravan cluster, WEST of the road inside the gate, below the temple neighborhood
s.flophouse(1574, 1620)
s.inn(1574, 1655)
s.stables(1574, 1687, rot=90)


def grid(streets, width_ft=18):
    for st in streets:
        s.street(st, width=s.lw(width_ft))


def front(streets, kinds, width_ft=18, spacing=19, rows=1):
    # rows of buildings parallel to and DIRECTLY against each street (the front row tight on the
    # street, deeper rows stacked behind it) - the machiya pattern: street line + tenement depth.
    # spacing ~19px vs an 16-18px storefront = near-CONTIGUOUS frontage (machiya shared party
    # walls; street frontage was taxed and precious), per the GM row-packing doctrine
    for st in streets:
        s.frontage(st, list(kinds), width=s.lw(width_ft), spacing=spacing, rows=rows, rowgap=2, jitter=1, setback=s.px(14))


def alleys(lst):
    # unpaved gravel roji subdividing the big street-blocks: the jammed interior housing is
    # reached by these, not the paved streets
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


# garden-green palette for the in-wall vegetable tract (vs the tan grain crops of a dry hem)
VEG_CROPS = {"daikon": ("#9FB86B", "#83A050"), "greens": ("#8FAE62", "#75954C"),
             "onions": ("#ADBC77", "#93A25C"), "beans": ("#A9B36A", "#8E9A50")}


def veg_tract(name, bbox, seed):
    """An in-wall kind="vegetable" GARDEN TRACT (settlements.md 'In-wall VEGETABLE tracts'):
    intensively-worked well/night-soil-fed garden ground worked by the surrounding quarters -
    no channel, no farmstead ring (the checks exempt kind != "paddy"). Drawn as a quilt of
    small furrowed plots, each row-cultivated to its own heading like fragmented dry holdings."""
    R = _random.Random(seed)
    x0, y0, x1, y1 = bbox
    rows = [y0]
    while rows[-1] < y1 - 30:
        rows.append(min(y1, rows[-1] + R.uniform(26, 40)))
    rows[-1] = y1
    prev = R.choice(list(VEG_CROPS))
    for i in range(len(rows) - 1):
        cuts = [x0, x1] if (x1 - x0) < 46 or R.random() < 0.4 else [x0, R.uniform(x0 + 22, x1 - 22), x1]
        for j in range(len(cuts) - 1):
            quad = [(cuts[j] + R.uniform(-2, 2), rows[i] + R.uniform(-2, 2)),
                    (cuts[j + 1] + R.uniform(-2, 2), rows[i] + R.uniform(-2, 2)),
                    (cuts[j + 1] + R.uniform(-2, 2), rows[i + 1] + R.uniform(-2, 2)),
                    (cuts[j] + R.uniform(-2, 2), rows[i + 1] + R.uniform(-2, 2))]
            if R.random() < 0.5:
                prev = R.choice(list(VEG_CROPS))
            fill, fur = VEG_CROPS[prev]
            pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in quad)
            s.add(f'<polygon points="{pts}" fill="{fill}" stroke="#A98C58" stroke-width="1.4" stroke-linejoin="round"/>')
            theta = (i * 0.9 + j * 1.5 + R.uniform(-0.15, 0.15)) % math.pi   # neighbours differ (family strips)
            furrows(quad, fur, theta)
            s.M["dry_plots"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in quad],
                                     "crop": prev, "theta": round(theta, 3)})
            s.dry_polys.append(quad)
    outline = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    s.field_polys.append(outline)
    s.M["fields"].append({"name": name, "kind": "vegetable", "outline": [[x, y] for x, y in outline],
                          "bbox": [x0, y0, x1, y1], "vis_bbox": [x0, y0, x1, y1]})


# ====================================================================== NW: agricultural
# ONLY the NW quarter carries in-wall fields (GM: tunable via agricultural_district=True -
# Tango is unusual but not unique in this). The tank pond sits at the quarter's HIGH NE corner
# (water enters the city from the high north, like the moat's feeder - a tameike is embanked
# on the high ground), and its sluice commands ONE comb paddy fanning SOUTH-WEST into the
# crescent pocket the ring road leaves. The pocket needs the comb's CLOCKWISE hand (the wide
# flank sweeping south, the fall marching down-left), so the comb is built mirrored
# (mirror_ym) - build_comb's fixed chirality would throw the wide flank north into the
# narrowing crescent. Params found by sweeping seeds/falls against the ACTUAL ring-road
# polyline (its chords cut inside the ideal ellipse) + the burakumin band at y1236.
# The district's second block is a kind="vegetable" GARDEN TRACT on the road flank.
s.pond(1497, 965, 38, 24)                # the in-wall tank, on the quarter's high NE corner
_net1, ENV_NW1, _c1 = comb_field("nw1", (1470, 978), 135, 99, 110, (95, 130), (55, 80), (0.35, 0.7),
                                 dry_band=(10, 18), avoid=(RING,), mirror_ym=1111)
_p1 = plot_centroid(_net1, lambda cs: min(cs, key=lambda c: (c[0] - _c1[0]) ** 2 + (c[1] - _c1[1]) ** 2))
topo_channel([(1482, 972), (1470, 978), _p1], {"kind": "pond"}, {"kind": "field", "name": "nw1"})
# the in-wall field's runoff leaves by a WATER GATE: a culvert from the drain's outfall under
# the ring road + rampart into the moat (drawn in the water block, so the wall renders over it -
# it reads as flowing beneath the masonry, which is what a real water gate did)
_dr1 = next(c["pts"] for c in _net1["channels"] if c["role"] == "drain")
_o1x, _o1y = _dr1[0] if _dr1[0][0] < _dr1[-1][0] else _dr1[-1]   # the outfall = the drain's WEST end
_mw = min(MOAT, key=lambda p: (p[0] - _o1x + 40) ** 2 + (p[1] - _o1y - 30) ** 2)   # moat rim W-SW of it
topo_channel([(_o1x, _o1y), (_mw[0], _mw[1])], {"kind": "drain"}, {"kind": "moat"})   # topology: the sink IS the moat
# ...but the VISIBLE ditch stops SHORT of the patrol road: the runoff drops into an implied
# UNDERGROUND stone conduit beneath the ring road, rampart and moat (GM: never draw the ditch
# running through the city wall - the water gate is underground)
_ucx, _ucy = _mw[0] - _o1x, _mw[1] - _o1y
_ucl = math.hypot(_ucx, _ucy) or 1.0
_lo, _hi = 0.0, 1.0
for _ in range(24):                              # where the culvert line meets the ring road loop
    _mt = (_lo + _hi) / 2
    if _in_poly(_o1x + _ucx * _mt, _o1y + _ucy * _mt, RING):
        _lo = _mt
    else:
        _hi = _mt
_te = max(0.15, _lo - 12.0 / _ucl)               # stop ~12px before the ring road bed
s.field_channel([(_o1x, _o1y), (_o1x + _ucx * _te, _o1y + _ucy * _te)], '#7C9EB0', 3.2, 3.2)
s.ring(('poly', ENV_NW1), 17, 14, ["plain"])
s.ring(('poly', ENV_NW1), 13, 42, ["plain"])
s.ring(('poly', ENV_NW1), 10, 70, ["plain"])
veg_tract("nw2", (1503, 1023, 1568, 1206), 72)
s.label(1338, 1123, "agricultural district", 10, italic=True, color="#5A6A2A")

# the in-wall burakumin neighborhood (its lane reaches the Imperial road, wiring it to the grid):
# two terrace strips flanking the E-W lane (row-packing doctrine), a few shops fronting the lane
BUR_ST = [[(1191, 1285), (1602, 1285)], [(1480, 1233), (1480, 1371)]]   # the vertical runs a full 50+ past the lane both ways (no dangling stub) and into the SW street   # the vertical continues into the SW x1480 street (end-to-end junction, no near-miss)
grid(BUR_ST)
# the burakumin draw from their OWN wells (status segregation extended to shared water) -
# placed before the rows so the strips break into courts around them
for wx, wy in [(1298, 1259), (1490, 1259), (1328, 1310), (1541, 1310), (1226, 1261), (1226, 1312), (1399, 1312), (1561, 1261), (1262, 1259), (1262, 1310), (1435, 1314)]:
    s.well_at(wx, wy)
front([BUR_ST[0]], ["shop"] * 5, spacing=42, rows=1)
s.rowpack((1198, 1233, 1582, 1273), (["burakumin"] + ["servant"]) * 18, court_every=3)
s.rowpack((1198, 1298, 1582, 1338), (["burakumin"] + ["servant"]) * 18, court_every=3)
s.label(1450, 1263, "burakumin", 10, italic=True, color="#6B4F2A")

# ====================================================================== NE: laborers
# one E-W street (to a clean ring-road junction) + one N-S; shops + the wealthier "master"
# laborers front them, and the standard laborers pack into terrace BANDS behind the frontage
NE_ST = [[(1602, 1145), (2024, 1145)], [(1805, 1044), (1805, 1361)]]
grid(NE_ST)
# gravel roji subdivide the bands into machiya-block widths; drawn BEFORE wells and rows
alleys([[(1704, 1056), (1704, 1293)], [(1896, 1076), (1896, 1293)], [(1978, 1148), (1978, 1247)]])   # the third serves the east-arc terraces
s.frontage([(1602, 1145), (1967, 1145)], ["shop"] * 3 + ["laborer_large"] * 12, width=s.lw(18), spacing=17, rows=1, rowgap=2, jitter=1, setback=s.px(14), skip=NE_ST[0])   # stops short of the ring arc (a large corner was reaching the patrol bed)
front([NE_ST[1]], ["shop"] * 2 + ["laborer_large"] * 6, spacing=17, rows=1)
# the laborer warren is the DENSEST quarter, so it carries the most wells - the idobata courts
# the terraces break around; placed BEFORE the rows
s.place_wells((1704, 1008, 2008, 1247), spacing=58)
for wx, wy in [(1663, 1095), (1754, 1206), (1704, 1069), (1866, 1226), (1675, 1115), (1907, 1074), (1957, 1196), (1775, 1079), (1846, 1079), (1917, 1082), (1749, 1107), (1835, 1107), (1937, 1107), (1663, 1079), (1693, 1176), (1764, 1176), (1835, 1176), (1907, 1176), (1967, 1176), (1683, 1127), (1749, 1127), (1866, 1127), (1937, 1127)]:
    s.well_at(wx, wy)
s.fire_tower(1831, 1243, label=None)   # NE, amid the terraces (placed first; the rows flow around it)
for wx, wy in [(1673, 1209), (1791, 1218), (2000, 1222), (2006, 1328), (1729, 1176), (1766, 1245), (1645, 1235), (1965, 1247)]:
    s.well_at(wx, wy)   # extra idobata courts BEFORE the rows, splitting the flagged 28-77-household draw-points
for fan in ([(1817, 1046), (1813, 1023), (1821, 1062), (1882, 1021), (1880, 1058)],
            [(1969, 1265), (1953, 1243), (2014, 1249), (2018, 1206)],
            [(1851, 1249), (1820, 1249), (1881, 1247), (1851, 1182), (1813, 1184), (1884, 1182), (1820, 1155)],
            [(1501, 1330), (1470, 1358), (1509, 1424), (1545, 1435), (1470, 1328)],
            [(1545, 1438), (1470, 1432), (1423, 1427), (1549, 1381)],
            [(1742, 1272), (1786, 1272), (1748, 1258)]):   # the last fan splits the (1766,1245) draw-point the roji cadence pushed to 27 households (city_well_density_sufficient); candidates sit a court SW of it - anything nearer is inside the seam well's own berth
    for c in fan:
        if s.well_at(*c):
            break   # candidate fan: first clear spot wins (splits a 27-32-household draw-point)
s.rowpack((1720, 1003, 2013, 1135), (["laborer"] * 3 + ["servant"]) * 60, court_every=3)
s.rowpack((1622, 1153, 2054, 1247), (["laborer"] * 3 + ["servant"]) * 50, court_every=3)
s.rowpack((1622, 1251, 2054, 1298), (["laborer"] * 3 + ["servant"]) * 26, court_every=3)
s.label(1764, 1082, "laborer neighborhoods", 10, italic=True, color="#5A4326")

# fill the band between the NE laborer quarter and the samurai ward fence (no large empty
# ground in a city) - terraces between gravel lanes that continue down to the ward gates
alleys([[(1704, 1298), (1704, 1360)], [(1896, 1298), (1896, 1360)]])   # x1800 is a real street now
for wx in (1663, 1759, 1861, 1952):
    s.well_at(wx, 1338)
s.rowpack((1622, 1300, 2059, 1350), (["merchant_house"] * 4 + ["servant"]) * 40, court_every=3)

# ====================================================================== SW: merchants
# the main commercial avenue reaches from the road to the west ring road; two N-S streets
# hang off it. Storefronts line all three (near-contiguous machiya frontage); the merchant
# homes fill the blocks as terraces, with the wealthy WEST enclave spread out (estates +
# large homes with air between them - the variety/spread the budgets.md wealth bands demand).
AVENUE = [(1164, 1455), (1927, 1455)]
s.street(AVENUE, width=s.lw(22), main=True)
SW_ST = [[(1253, 1455), (1253, 1616)], [(1480, 1371), (1480, 1661)]]   # x1256 ends ON the ring; x1480 stops well clear of the S-gate furniture and its tucked inspection annex
grid(SW_ST)
# the temple neighborhood (lower SW, INSIDE the wall): Benten + Daikoku with the Ministry of
# Rites that oversees them - placed BEFORE the merchant rows so they flow around it
s.shrine_hall(1343, 1501, "Temple of Benten", w=100, h=64, kind="temple", primary=True, label_below=True)
s.block_polys.append([(1281, 1534), (1405, 1534), (1405, 1560), (1281, 1560)])   # reserve the 'Temple of Benten' label ground so the merchant pack does not land under it (post-scale, feature 006)
s.shrine_hall(1424, 1616, "Temple of Daikoku", w=100, h=64, kind="temple", torii=[(1481, 1616), (1481, 1570)])
s.ministry(1316, 1602, "Ministry of Rites", w=s.px(140), h=s.px(95))
# the city THEATER STAGE - in the Temple of Benten's precinct, EAST of it, its viewing ground
# opening west toward the hall (the troupe/festival venue belonging to the temple)
s.theater_stage(1448, 1503, w=s.px(190), h=s.px(132), rot=90, label="theater stage")
# Benten's + Daikoku's intramural TEMPLE GRAVEYARDS (danka parish grounds)
s.cemetery(1216, 1509, 46, 34, label="graveyard")
s.cemetery(1389, 1677, 56, 40, label="graveyard")
# a smattering of small wayside shrines dot the temple neighborhood (non-residential)
for sx, sy in [(1300, 1559), (1265, 1610), (1521, 1653), (1501, 1622)]:   # all four INSIDE the temple neighborhood, clustered AWAY from the theater stage (its facing check measures the nearest religious feature - keep Benten nearest) - the S-gate pocket is the furniture's ground
    s.small_shrine(sx, sy)
s.label(1255, 1546, "temple neighborhood", 9, italic=True, color="#6B2A18")
s.frontage([(1159, 1455), (1602, 1455)], (["merchant"] * 3 + ["shop"]) * 20, width=s.lw(20), spacing=19, rows=2, rowgap=2, jitter=1, setback=s.px(14), skip=AVENUE)   # skip=AVENUE: the sub-segment must match the avenue's REGISTERED corridor or its own street rejects it
front(SW_ST, (["merchant"] * 3 + ["shop"]) * 12, width_ft=18, spacing=19, rows=2)
# a noticeable minority of merchant houses keep a fireproof kura - placed NOW, while the
# shopfronts still have open back lots (the terraces packed next would fill them)
s.merchant_storehouses(8)
# the merchants' HOMES: terraces in the north band (between the burakumin lane and the avenue,
# prime central ground) and the mid-block cores; the WEST enclave keeps its spread
alleys([[(1308, 1346), (1308, 1454)]])   # reaches the avenue bed; the x1480 through-street serves the band's east half
EST = [(1265, 1387, "south")]
for ex, ey, gd in EST:
    s.merchant_estate(ex, ey, gate_dir=gd)
for mx, my in [(1358, 1399), (1517, 1391)]:
    s.building(mx, my, *s._dims("merchant_large"), "merchant_large")
s.inn(1570, 1424)                        # the roadside inn anchoring the central road-market (before the terraces)
s.fire_tower(1237, 1350, label=None)   # west-central, on the strip between the burakumin lane and the merchant band (before the rows, which flow around it)
s.place_wells((1247, 1343, 1582, 1440), spacing=66)
for wx, wy in [(1328, 1399), (1521, 1394), (1393, 1427), (1466, 1429)]:
    s.well_at(wx, wy)   # split the west merchant band's overloaded draw-point
s.rowpack((1181, 1344, 1559, 1440), (["merchant_house"] * 5 + ["servant"]) * 40, court_every=3)   # reaches the west ring arc (the bound clips the taper)
# mid-block cores between the two SW streets: more merchant terraces
s.rowpack((1480, 1561, 1546, 1645), (["merchant_house"] * 5 + ["servant"]) * 12)
s.rowpack((1555, 1498, 1592, 1610), (["merchant_house"] * 3 + ["servant"]) * 8)   # the road flank south of the avenue
s.rowpack((1501, 1462, 1582, 1559), (["merchant_house"] * 5 + ["servant"]) * 10)
WEST_HOMES = (["merchant_large"] + ["merchant_house"] * 2 + ["servant"]) * 8
s.place_wells((1226, 1460, 1328, 1622), spacing=90)
s.pack((1191, 1466, 1343, 1693), (["merchant_large"] + ["merchant_house"] * 2 + ["servant"]) * 12, step=20, face_streets="fill")
s.label(1399, 1462, "merchant district", 10, italic=True, color="#5A4326")

# WELL COVERAGE passes, now the commoner housing is all down: any dwelling farther than a
# court-spacing from a well gets one dropped in the nearest clear court (place_wells near=
# mode + its coverage pass; grid placement consumes no RNG, so this perturbs nothing).
s.place_wells((1622, 993, 2069, 1358), spacing=52, near=46)   # NE laborer warren + the gap band
s.place_wells((1181, 1338, 1602, 1704), spacing=52, near=46)   # merchant district + temple neighborhood
s.place_wells((1191, 1226, 1602, 1343), spacing=52, near=46)   # burakumin strips

# ====================================================================== SE: government + samurai
# the governor's YAMEN - the grandest compound in the city (its dozens of interior buildings
# are a separate Mode A diagram) - with the five other ministries LINING the government avenue
# (Rites is apart, in the SW temple neighborhood), and the samurai neighborhood around them
grid([[(1927, 1455), (1927, 1582)]])   # the government avenue's E leg, wrapping the yamen
s.governor_mansion(1793, 1547, s.px(436), s.px(366), "Governor's Mansion", gate_dir="west")   # ~1.4 ha - modest for a provincial yamen, still the grandest compound by far
MINS = ["Ministry of Revenue", "Ministry of Retainers", "Ministry of War",
        "Ministry of Works", "Ministry of Justice"]
MIN_POS = [(1655, 1394), (1750, 1419), (1846, 1394), (1941, 1419), (1957, 1484)]   # staggered rows between fence and avenue; the upper row labels ABOVE (over the bare fence line), the lower row + Justice label BELOW (into their own block margins)
for (mx, my), name in zip(MIN_POS, MINS):
    s.ministry(mx, my, name, w=s.px(130), h=s.px(90))   # label side auto-picked (empty ground wins)
# Bishamon (the warrior fortune) in the samurai quarter SW corner, off the grid (no street
# runs up to it at this tight scale, so it needs no torii avenue); new hall in a former
# samurai compound - keeps NO burial ground
s.shrine_hall(1671, 1663, "Temple of Bishamon", w=s.px(200), h=s.px(140), kind="temple", graveyard=False, label_below=True)
s.block_polys.append([(1596, 1681), (1746, 1681), (1746, 1730), (1596, 1730)])   # keep the hall's below-label strip clear of the samurai packs (covers a large house's half-footprint past the box)
s.block_polys.append([(1623, 1625), (1719, 1625), (1719, 1700), (1623, 1700)])   # a ~14px apron around the hall itself - the scatter pack kept rolling a house onto its +4 check margin
# the ruling clan's walled MAUSOLEUM by the government quarter (the elite crypts)
s.mausoleum(1793, 1655, 44, 32, label="Mausoleum", gate_dir="north")   # the ward's SE corner, below the yamen

# houses vary by rank: ~1-in-4 a large senior house; the wealthiest live on walled estates
# OUTSIDE the walls. Samurai keep DETACHED compounds with yards - pack, NOT rowpack (the
# scatter is the deliberate contrast with the commoner terraces).
SAM_MIX = (["samurai"] * 3 + ["samurai_large"]) * 6
front([[(1927, 1470), (1927, 1582)]], SAM_MIX[:18], spacing=18, rows=1)   # senior houses front the avenue's E leg
s.rowpack((1726, 1635, 2003, 1683), (["samurai"] * 5 + ["samurai_large"]) * 10, court_every=6)   # kumi-yashiki nagaya: junior-samurai row-barracks south of the yamen (courts thinned - the quarter keeps no public wells)
s.rowpack((1962, 1381, 2057, 1570), (["samurai"] * 5 + ["samurai_large"]) * 12, court_every=6)   # the east-arc barracks strip
s.rowpack((1704, 1689, 1882, 1734), (["samurai"] * 4 + ["samurai_large"]) * 11, court_every=6)   # the south strip below the mausoleum (bound clips it at the ring road)
s.corridors.append(([(1681, 1777), (1622, 1720), (1622, 1364), (2088, 1364)], 16))   # reserve the WARD FENCE line before the pack so no samurai house sits ON the fence (city_ward_fence_clear_of_structures)
s.pack((1624, 1377, 2084, 1742), (["samurai"] * 3 + ["samurai_large"]) * 150, step=11, face_streets="fill")
s.label(1762, 1691, "samurai neighborhood", 10, italic=True, color="#3A352C")
# the samurai/government WARD: a continuous earthwork fence (W + N), ends abutting the city
# wall, so the kido gates can't be walked around. The W leg jogs east below the quarter to
# abut SOLID wall clear of the S gate opening at x1600.
s.ward("samurai", [(1681, 1777), (1622, 1720), (1622, 1364), (2088, 1364)],
       gates=[(1622, 1455, True),                                   # the government avenue pierces the W fence
              (1704, 1364, False), (1805, 1364, False), (1896, 1364, False),   # the commoner lanes enter at kido gates
              (2065, 1364, False), (1655, 1748, True)])             # the RING ROAD crosses the fence (E and SW) - gated
s.label(1655, 1352, "samurai ward gate", 9, italic=True, color="#5A4326")

# ====================================================================== OUTSIDE the walls
s.bound = None
# wealthy samurai walled estates - all to the SE, beyond the moat, SCATTERED and varying in
# size (~1-1.5 real acres each). The inner ones STRADDLE the cropped SE edge (partly shown);
# the rest run off-map entirely (a city map is about the city, not its commuter belt).
EST = [(2201, 1470, 94, 62, "south"), (2160, 1622, 90, 60, "west"), (2104, 1785, 86, 58, "south"),   # straddle the edge
       (2313, 1561, 84, 56, "west"), (2363, 1724, 76, 50, "south"), (2262, 1896, 72, 48, "north")]    # off-map beyond
for ex, ey, ew, eh, gd in EST:
    s.manor(ex, ey, ew, eh, "", gate_dir=gd)
s.label(2160, 1549, "samurai estates", 10, italic=True, color="#3A352C")   # in the open ground between the straddling estates, off the moat
# surrounding farmland: large comb fields CLOSE to the city, irrigated from the MOAT, each
# ringed by the villagers' farmhouses; all run off the map edge. Each comb's SLUICE sits a
# stride outside the moat rim (computed from the actual moat polyline, so the tap self-corrects)
# with its fall direction pointing AWAY from the moat - the head-race visibly taps the moat and
# the paddies march downhill off the cropped view. The moat is fed from the NORTH (the stream),
# so each tap picks a moat vertex UPSTREAM (north) of the sluice, running WITH the current.
# fall directions carry a slight SOUTH bias (175/172/105) so each comb's ground sits DOWNSTREAM
# of its tap (moat_channels_flow_with_current: the moat is fed from the N, its water runs south)
MOAT_FARMS = [("fw1", (1074, 1200), 175, 73, 190, (160, 210), (95, 125), (0.35, 0.7)),
              ("fw2", (1155, 1632), 172, 74, 190, (145, 190), (85, 115), (0.4, 0.75)),
              ("fs1", (1328, 1805), 105, 75, 170, (125, 165), (85, 115), (0.4, 0.78))]
for nm, tap, dd, sd, ff, ca, cb, oa in MOAT_FARMS:
    upstream = [p for p in MOAT if p[1] < tap[1] - 20]       # moat vertices NORTH of the tap (upstream of the southward current)
    mp = min(upstream, key=lambda p: (p[0] - tap[0]) ** 2 + (p[1] - tap[1]) ** 2)
    _ol = math.hypot(mp[0] - CX, mp[1] - CY) or 1.0          # outward: away from the city centre
    sl = (round(mp[0] + 30 * (mp[0] - CX) / _ol), round(mp[1] + 30 * (mp[1] - CY) / _ol))
    s.field_channel([mp, sl], '#6C9CBE', 7, 7)               # the visible tap: moat rim -> sluice
    _net, _env, _cen = comb_field(nm, sl, dd, sd, ff, ca, cb, oa, avoid=(MOAT,))
    # source topology: ends at the SOUTHERNMOST plot's centroid - guaranteed inside the outline
    # (city_moat_irrigates_fields) and downstream of the tap (moat_channels_flow_with_current)
    _pd = plot_centroid(_net, lambda cs: max(cs, key=lambda c: c[1]))
    topo_channel([(mp[0], mp[1]), sl, _pd], {"kind": "moat"}, {"kind": "field", "name": nm})
    # sink topology: the collector's runoff leaves the cropped map (the drain marches off-view)
    _dr = next(c["pts"] for c in _net["channels"] if c["role"] == "drain")
    topo_channel([tuple(_dr[-2]), tuple(_dr[-1])], {"kind": "drain"}, {"kind": "offmap"})
    s.ring(('poly', _env), 28, 15, ["plain"])
    s.ring(('poly', _env), 22, 40, ["plain"])
# a field running off the NORTH edge - its water is implied off-map (the moat's own source side):
# the sluice sits above the cropped frame, so the comb's head shows only its canals entering the
# view; the fall is capped so the drain stays clear of the moat's north rim, and the collector
# EMPTIES INTO THE MOAT (the city's storm drain - the north field's runoff feeds the ring)
_netn, ENV_FN1, _cn = comb_field("fn1", (1878, 610), 90, 76, 90, (140, 180), (80, 110), (0.4, 0.8),
                                 avoid=(MOAT,))
_pn = plot_centroid(_netn, lambda cs: min(cs, key=lambda c: c[1]))   # a head plot, nearest the off-map source
topo_channel([(1878, 604), (1878, 610), _pn], {"kind": "offmap"}, {"kind": "field", "name": "fn1"})
_drn = next(c["pts"] for c in _netn["channels"] if c["role"] == "drain")
_dfx, _dfy = _drn[-1]
_mne = min(MOAT, key=lambda p: (p[0] - _dfx) ** 2 + (p[1] - _dfy - 90) ** 2)   # the moat rim S of the outfall (west of the funerary ground)
topo_channel([(_dfx, _dfy), (_mne[0], _mne[1])], {"kind": "drain"}, {"kind": "moat"}, draw_w=3.2)
s.ring(('poly', ENV_FN1), 28, 15, ["plain"])
s.ring(('poly', ENV_FN1), 22, 40, ["plain"])
# a gate market just outside the south gate, beyond the moat - stall rows FLANKING the road
s.frontage([(1602, 1856), (1602, 2003)], ["shop"] * 18, skip=IMPROAD, width=s.lw(26), spacing=19, rows=2, rowgap=2, jitter=1, setback=s.px(14))   # the guan-xiang gate market is transient SHOPS/stalls, not merchant residences (commoner DWELLINGS shelter inside the wall)
s.label(1685, 1909, "gate market", 10, italic=True, color="#5A4326")

# COMMERCIAL RIBBON along the Imperial road - a city ON a trade route lines its through-road
# with shops + traveler services (its prime frontage). The central road-market fills the block
# between the burakumin lane and the merchant avenue; a smaller row greets northern arrivals.
s.frontage([(1602, 1328), (1602, 1448)], (["shop"] + ["merchant"] * 2) * 5, skip=IMPROAD, both=False, width=s.lw(22), spacing=19, rows=2, rowgap=2, jitter=1, setback=s.px(14))
s.frontage([(1602, 978), (1602, 1039)], ["shop"] * 3, skip=IMPROAD, both=False, width=s.lw(22), spacing=19, rows=1, jitter=1, setback=s.px(14))
# EAST side - a thin shop row in the gap between the road and the NE/SE quarters
s.frontage([(1602, 1308), (1602, 1155)], (["shop"] + ["merchant"] * 3) * 2, skip=IMPROAD, both=False, width=s.lw(22), spacing=20, rows=1, jitter=1, setback=s.px(14))   # stops at the burakumin-lane latitude: the ministry labels own the flank below
s.label(1523, 1407, "road market", 9, italic=True, color="#5A4326")

# THE DEAD - a full funerary geography (centuries-old city; remains cremated, then interred):
#  - two intramural TEMPLE GRAVEYARDS (danka parish grounds), by Benten and by Daikoku (above)
#  - an in-wall burial ground in the agricultural district (NOT a temple parish ground)
#  - one extramural common BURIAL GROUND, west of the wall (the exempt outside graveyard)
#  - the ruling clan's walled MAUSOLEUM by the SE samurai/government quarter (above)
#  - the CREMATION GROUND + pauper OSSUARY mound outside the wall (monk-run, burakumin assistants)
s.cemetery(2160, 871, 90, 64, label="common burial ground")
s.cremation_ground(2160, 978)
s.ossuary(2170, 760)

s.bridges()   # spans the Imperial Road over the moat at the north and south gates

# draw the farmhouses, each with its threshing/drying yard (universal); LAST so every obstacle is known
s.farmsteads()

# ===== FIRE DEFENSE: watch-towers =====
# ONE AMID EACH major commoner quarter, on the cleared seams the dense city leaves - placed
# LAST so they perturb nothing. WHY: settlements.md "Fire towers".
s.fire_tower(1527, 1697, label=None)   # south, amid the rooftops it watches - the ONLY spot the full-obstacle scan
s.label(1527, 1674, "fire tower", 9, italic=True, color="#5A4326")   # ... left with label room (short text, placed ABOVE - the dense south has no 84px below-box anywhere)

# ---- DETERMINISTIC TOP-UP (consumes no RNG): the seeded packs saturate wherever the streets,
# wells and compounds leave them, and every upstream edit re-rolls the totals - so the caste
# floors and the declared population are closed HERE: sweep a fixed grid over each quarter and
# try_building() into whatever gaps the FINAL layout left. Runs after farmsteads + the towers,
# so it sees every obstacle; it adapts across churn (fixed-coordinate hand-adds went stale on
# every re-roll). Ministries/the yamen keep their 14px stand-clear margin.
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
        if kind not in ("samurai", "samurai_large") and not _in_poly(gx, gy, WALL):
            return False                                     # a COMMONER dwelling never lands OUTSIDE the wall (feature 006); samurai are exempt (their country seats sit outside)
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
        if not all(abs(gx - px) >= (w_ + pw) / 2 + 3 or abs(gy - py) >= (h_ + ph) / 2 + 3
                   for (px, py, pw, ph) in s.placed):
            return False
        # s.placed stores (w,h) UNROTATED, so a street-facing pack house rotated ~45-135 deg
        # reaches past the box the test above clears against - test the true rotated AABBs too.
        # Religious halls join the sweep with a wider 8px berth: the no_structure_on_religious
        # gate grows each hall by 4px, and the first finer sweep seated a merchant_house 0.35px
        # inside Daikoku's grown corner
        for o, marg in [(o2, 3.0) for o2 in s.M["buildings"] + s.M["houses"]] + [(o2, 8.0) for o2 in s.M.get("religious", [])]:
            if "w" not in o or abs(gx - o["x"]) > 64 or abs(gy - o["y"]) > 64:
                continue
            oth = math.radians(o.get("rot", 0))
            oc, os_ = abs(math.cos(oth)), abs(math.sin(oth))
            if abs(gx - o["x"]) < (w_ + oc * o["w"] + os_ * o["h"]) / 2 + marg and abs(gy - o["y"]) < (h_ + os_ * o["w"] + oc * o["h"]) / 2 + marg:
                return False
        return True

    def door_clear(gx, gy, rot):
        # outward-facing-doors doctrine (2026-07-18): a gap-fill house still needs an UNBLOCKED
        # entrance. This is the gate's EXACT geometry (check_village city_house_doors_unblocked:
        # the door-probe band vs ROTATED neighbour corners) rather than s.open_face_rot - the
        # helper's conservative axis-aligned self.placed test cannot see a 90-degree frontage
        # house's true footprint (placed stores (w,h) unrotated), which is precisely where a fill
        # beside a street-facing row lands. Probe depth carries a 15% safety margin over the
        # gate's DOOR_CLEAR_FT so borderline float geometry never flips the verdict.
        dc = (7.0 / 3) * 1.15
        th = math.radians(rot)
        ux, uy = -math.sin(th), math.cos(th)
        vx, vy = -uy, ux
        fx, fy = gx + ux * h_ / 2, gy + uy * h_ / 2
        rr = math.hypot(w_, h_) / 2 + dc + 2
        for o in s.M["buildings"] + s.M["houses"]:
            if "w" not in o:
                continue
            if math.hypot(o["x"] - gx, o["y"] - gy) > rr + math.hypot(o["w"], o["h"]) / 2:
                continue
            oth = math.radians(o.get("rot", 0))
            c_, sn = math.cos(oth), math.sin(oth)
            corners = [(o["x"] + c_ * dx - sn * dy, o["y"] + sn * dx + c_ * dy)
                       for dx, dy in ((-o["w"] / 2, -o["h"] / 2), (o["w"] / 2, -o["h"] / 2),
                                      (o["w"] / 2, o["h"] / 2), (-o["w"] / 2, o["h"] / 2))]
            for d_ in (0.8, dc * 0.55, dc):
                for t_ in (-0.3 * w_, 0.0, 0.3 * w_):
                    if _in_poly(fx + ux * d_ + vx * t_, fy + uy * d_ + vy * t_, corners):
                        return False
        return True

    x0, y0, x1, y1 = region
    for pad in (7, 4, "exact"):       # tighter sweeps only when the padded pass leaves the floor unmet
        gy = y0
        while gy <= y1 and have < need:
            gx = x0
            while gx <= x1 and have < need:
                if ok(gx, gy) and (exact_clear(gx, gy) if pad == "exact" else s._fits(gx, gy, w_ + pad, h_ + pad)):
                    # door faces UP or DOWN only (90/270 would rotate the AABB out from under the
                    # axis-aligned clearance tests above); skip the spot when both faces are walled
                    orot = next((r_ for r_ in (0.0, 180.0) if door_clear(gx, gy, r_)), None)
                    if orot is not None:
                        s.building(gx, gy, w_, h_, kind, orot)
                        have += 1
                gx += 6
            gy += 7
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
top_up("samurai", (1635, 1384, 2071, 1734), 46, count_kinds=("samurai", "samurai_large"))   # 46 (was 40): the roji cadence thinned the SE government/samurai quarter to 0.28/1000px^2, under the 0.30 residential floor (city_residential_quarters_dense_enough) - a few more junior houses in the ward's gaps restore it
top_up("samurai", (1640, 1395, 2020, 1715), 53, count_kinds=("samurai", "samurai_large"))   # +7 constrained to the SE QUARTER WEDGE'S interior: the wider sweep above seats houses along the E arc OUTSIDE the quarter's inset-24 polygon (13 of the ward's samurai sit past it), which the per-quarter density counter cannot credit - only in-wedge seats lift 36 -> ~40 dwellings over the 0.30 floor
top_up("merchant_house", (1181, 1350, 1594, 1712), 120,
       count_kinds=("merchant", "merchant_house", "merchant_large"))   # 120 (was 112), region grown W to the row band's own x1181 edge + S to the ring taper: the pair cadence dropped the merchant caste to 102 vs its 105 band floor (~150 target, city_caste_counts_in_band); the finer 6x7 exact sweep finds the SW district's residual seats
top_up("merchant_house", (1632, 1302, 2050, 1348), 112,
       count_kinds=("merchant", "merchant_house", "merchant_large"))   # the SW district alone saturates ~3 short of the floor - the NE gap band (already a merchant_house terrace strip) takes the residue
_dw = (sum(1 for b in s.M["buildings"] if b["kind"] in DWELL)
       + sum(1 for h in s.M["houses"] if _inwall(h["x"], h["y"])))
if _dw < 562:   # population floor 558 (3000 x 0.93 / 5) + margin
    top_up("laborer", (1632, 1008, 2051, 1350),
           sum(1 for b in s.M["buildings"] if b["kind"] == "laborer") + (562 - _dw))
def _dwell_count():
    return (sum(1 for b in s.M["buildings"] if b["kind"] in DWELL)
            + sum(1 for h in s.M["houses"] if _inwall(h["x"], h["y"])))


# fallback quarters, in caste-band-headroom order, until the floor is met
for _kind, _region, _cap in (("servant", (1201, 1226, 1597, 1344), 155),   # the open W-central / burakumin-quarter band (servants interleave among the commoners) - no other servant region reached it, leaving it under-filled (feature 006)
                             ("servant", (1194, 1350, 1594, 1701), 150),
                             ("burakumin", (1201, 1229, 1597, 1342), 37),
                             ("samurai", (1635, 1384, 2071, 1734), 46),
                             ("servant", (1632, 1008, 2051, 1350), 152),
                             ("laborer", (1176, 1013, 1561, 1218), 290),   # the agri district's margins - its field hands live by the fields they work
                             ("servant", (1635, 1384, 2071, 1734), 152),  # servants staffed the samurai compounds - the quarter takes the last few
                             ("merchant_house", (1194, 1350, 1594, 1701), 120)):  # merchant band headroom (caste max ~195) absorbs any residue
    _dw = _dwell_count()
    if _dw >= 562:
        break
    top_up(_kind, _region, min(_cap, sum(1 for b in s.M["buildings"] if b["kind"] == _kind) + (562 - _dw)))

# the agricultural district's field hands draw from their own wells - the top-ups above can
# push homes past the burakumin band's 290px reach (city_neighborhoods_have_wells)
s.place_wells((1176, 993, 1561, 1226), spacing=56, near=88, coverage=False)   # FINE grid (the district is laced with field margins + channel corridors), each well gated to sit AMONG homes (near=88), coverage=False so the near-gate stays district-scoped (the global coverage pass would drop wells beside the samurai compounds)

s.title("Tango")

HERE = os.path.dirname(os.path.abspath(__file__))
nb = {}
for b in s.M["buildings"]:
    nb[b["kind"]] = nb.get(b["kind"], 0) + 1
print("farmhouses:", len(s.M["houses"]), "| buildings:", nb, "| total urban:", sum(nb.values()),
      "| estates:", len(s.M["manors"]), "| finish:", s.finish(os.path.join(HERE, "tango")))
