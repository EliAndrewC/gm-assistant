#!/usr/bin/env python3
"""Nagahara - a walled PROVINCIAL CITY on the Hayakawa river (diagram skill, Mode B, 1px = 3ft).

THE RIVER CITY (the norm - Tango is the exception): Nagahara sits on the WEST BANK of the
Hayakawa, which flows north -> south along its east flank. Per the historical pattern (imperial
China first, Japan agreeing - Xiangyang's Han-river face, Pingyao on the Fen, Okayama on the
Asahi): the trunk river NEVER runs through the walls (the Kaifeng flood lesson - the one great
city that let a river in was devastated seven times); instead the city stands ON the bank, the
river IS the water defense on its flank, and the dug moat covers the three landward faces,
tapping the river upstream (NE) and returning downstream (SE) so the current flushes it; the
junction feet tilt WITH the current (inlet near-square, outlet swept downstream - s.moat's
default tilts; settlements.md "junction angles follow the current", GM 2026-07-24).

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
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from citybudget import CityProgram, budget_to_manifest, plan_city  # noqa: E402
from settlement import Settlement  # noqa: E402
from waterfields import BEAN_GREEN, BUND, build_comb, hem_on_paddy, paddy_grain  # noqa: E402

# Paddy CELL grain calibrated to a real-feet target (~0.05 acre) at this city's 3 ft/px (was hand-set 26px
# -> ~0.08 acre, at Bray's "large" ceiling). Subdivides the same fans into finer cells; the ~3,000 urban
# population and every dwelling count are untouched (a city's farmers are not in that figure). See
# waterfields.paddy_grain / settlements.md 'Paddy cell size'.
PLOT_ACROSS, ROW_STEP = paddy_grain(3)

s = Settlement(3200, 2700, seed=47)
s.meta(
    name="Nagahara", scale="city", walled=True, population=3000, ftpx=3, wall_defense="siege", imperial_road=False, clan="Crab", capital_dir="northeast"
)  # Crab city -> temples to Bishamon + Ebisu; estates toward Otosan Uchi (NE)

# ---- feature 009: BUDGET-FIRST wall sizing. The space budget is computed BEFORE anything is
# drawn and the wall comes from it - not hand-tuned. The pre-feature 494x460 ring enclosed ~21%
# more ground than this program justifies (the GM's "too much empty space", pinned as the
# city_budget_fires_on_the_too_empty_nagahara regression); the whole layout was similarity-
# shrunk x0.9083 about the wall center onto the derived ring.
BUDGET = plan_city(CityProgram(population=3000, river=True, aspect=460 / 494, nring=20), canvas=(3200, 2700))
s.meta(budget=budget_to_manifest(BUDGET))

# ---- the rampart: a closed ring with a NORTH gate (the north road) and an EAST river gate
# (the bridge road), plus a WATER GATE south of the river gate where the cargo canal enters
CX, CY, RX, RY = 1480, 1330, round(BUDGET.wall.rx), round(BUDGET.wall.ry)  # 449x418 from the budget
NRING = 20
WALL = [(round(CX + RX * math.cos(-math.pi / 2 + 2 * math.pi * i / NRING)), round(CY + RY * math.sin(-math.pi / 2 + 2 * math.pi * i / NRING))) for i in range(NRING)]
NGATE, EGATE, WGATE_PT = WALL[0], WALL[5], WALL[6]
KIDO_SPOTS = [(1469, 1330, True), (1469, 1403, True), (1062, 1311, True), (1234, 1660, True)]
for kx, ky, kh in KIDO_SPOTS:
    if kh:
        s.block_polys.append([(kx - 25, ky - 38), (kx + 45, ky - 38), (kx + 45, ky + 26), (kx - 25, ky + 26)])
    else:
        s.block_polys.append([(kx - 38, ky - 25), (kx + 26, ky - 25), (kx + 26, ky + 45), (kx - 38, ky + 45)])
s.city_wall(
    WALL,
    gates=[NGATE, EGATE],
    guard_east=[NGATE],
    water_gates=[WGATE_PT],
    ring_inset=22,  # match the ACTUAL ring road (inset 22 post-shrink): the gate guard houses +
    #                  inspection stations pull in to the patrol road's centerline, which also keeps
    #                  each inspection within the ~160px gate radius (at the stale default 34 the
    #                  N-gate inspection walked to 168px out and the E-gate one collided with the
    #                  sliding vertex-4 mural tower)
    tower_skip=[(1055, 1299), (1237, 1653)],
)

# ---- the Hayakawa: north -> south along the east flank; the moat joins it at both ends
RIVER = [(2090, 526), (2076, 859), (2067, 1194), (2076, 1528), (2088, 1862), (2100, 2166)]
RIVER_W = s.river(RIVER)
MOAT = s.moat(WALL, gap=24, river=RIVER, river_cut=136)  # river_cut scaled with the x0.9083 shrink
RING = s.ring_road(WALL, inset=22)
s.bound = [list(p) for p in RING]


# ---- DECLARED QUARTERS (feature 006): tile the interior into zoned wedges split at the crossroads
# (road x=CX, axis y=CY). NE = laborer (residential); SE = merchant + downstream burakumin (mixed);
# SW = the government/samurai ward (mixed - civic compounds + samurai housing); NW = the temple
# neighborhood plus its monzen-machi commoner pocket (mixed - a temple town had dense pilgrim/
# craftsman housing around the halls, which also fills the ground the first draft left empty).
def _qpt(i, n=48, inset=24):
    a = -math.pi / 2 + 2 * math.pi * i / n
    return (CX + (RX - inset) * math.cos(a), CY + (RY - inset) * math.sin(a))


def _qwedge(i0, i1, n=48):
    return [(CX, CY)] + [_qpt(i, n) for i in range(i0, i1 + 1)]


s.quarter(_qwedge(0, 12), "residential")  # NE laborer
s.quarter(_qwedge(12, 24), "mixed")  # SE merchant + burakumin
s.quarter(_qwedge(24, 36), "mixed")  # SW government/samurai ward
s.quarter(_qwedge(36, 48), "mixed")  # NW temple neighborhood + monzen
SAM_BND = [(1039, 1311), (1469, 1311), (1469, 1570), (1217, 1666)]
s.corridors.append((SAM_BND, 15))  # reserve the WARD FENCE line before ANY pack so no house (samurai or burakumin) sits ON it (city_ward_fence_clear_of_structures)
# FRAME: content-cropped at the END of the gen via s.crop_city() (GM 2026-07-23, second pass) - the
# frame hugs the moat ring + the kept satellites (gate markets, wharf, flophouses, the far-bank
# funerary complex, labels) and the fans CLIP at the edge. The interim hand frame (MARGIN=250 +320
# east) is superseded; see crop_city's docstring.

# ---- THE through-road (no Imperial spine - meta imperial_road=False): the north road comes
# down from the distant Imperial highway (off-map NW), enters the north gate, runs the spine
# to the central crossroads, turns east along the main street, leaves by the river gate, and
# crosses the Hayakawa bridge toward the southeastern counties - ONE route, both ends off-map
# (through-traffic is why the city is here; the bend at the crossroads is the market corner)
ROAD = [
    (1352, 596),
    (1382, 672),
    (1413, 751),
    (1451, 829),
    (1480, 918),
    (1480, 1330),
    (1933, 1330),
    (2023, 1330),
    (2071, 1333),
    (2149, 1335),
    (2253, 1457),
    (2357, 1550),
    (2472, 1650),
    (2560, 1727),
]  # both ends past the widened frame (616/2545)
s.road(ROAD)  # unlabeled: only Imperial roads get labels (SKILL.md labeling rules)
s.bridge(2071, 1332, 4, RIVER_W + 26, 15)  # the Hayakawa bridge carries the through-road over the river

# ---- the cargo canal: moat -> water gate -> dock basin (the Suzhou pattern). ONE mouth on the
# river, not two (GM 2026-07-23): the canal's original river tap at (2060,1474) sat 36 real ft
# beside the moat's downstream junction (2074,1462) and rode collinearly INSIDE the moat arm's
# stroke for the whole bank crossing - a smeared doubled channel with a sliver fork at the mouth.
# Historically the Suzhou-pattern cargo canal communicates with the MOAT, and the moat's own
# downstream river junction is the single navigation entrance - so the canal hands off at the
# moat's outfall-arm corner (MOAT[1], the SE bend the arm springs from; self-correcting if the
# wall ever resizes) and the moat carries boats the last reach to the river. Gated by
# city_canal_shares_moat_mouth; see settlements.md river-cities "one mouth on the river, not two".
CANAL = [MOAT[1], (1907, 1460), (1830, 1455)]  # east end ON the moat corner (the handoff confluence); west end reaches INTO the dock basin (feeds it, like a street reaching the road)
s.canal(CANAL)
s.water_gate(1907, 1460, rot=8)
s.dock(1809, 1455, 54, 34)
s.bridge(1879, 1457, 95, 34, 12)  # the ring road bridges the canal just inside the wall

# civic amenities placed FIRST, so the dense packs flow around them.
s.flophouse(1405, 837, label_below=True)  # outside the NORTH gate
s.flophouse(1987, 1266)  # outside the EAST gate, on the wharf
# N-gate caravan cluster, WEST of the spine just inside the gate: this side is naturally OPEN
# ground (the laborer warren packs EAST of the spine), so the stables gets its wagon-train berth
# without carving a hole in the housing. A small reservation keeps the cluster and the guard-house
# label ground clear of any stray placement.
s.block_polys.append([(1406, 956), (1464, 956), (1464, 1077), (1406, 1077)])
s.block_polys.append([(1549, 985), (1696, 985), (1696, 1016), (1549, 1016)])  # keep the N-gate guard-house label ground clear of the pack
s.flophouse(1430, 969, label_below=True)  # 7px up from the shrunk layout's seat so its below-label clears the stables' top edge (labels_clear_of_other_buildings)
s.inn(1444, 1050)  # nudged E of the Ebisu graveyard label
s.stables(1430, 1017, rot=90)  # kept >=75px W of the laborer pack (which starts ~x1504) so the animals have open ground; placed AFTER the flophouse + inn so its yard scatter skips them
# E-gate caravan cluster: a reserved pocket W of the gate furniture (which fills the E-wall
# strip), N of the main road - reserved up front so the NE laborer pack flows around it
s.block_polys.append([(1663, 1132), (1825, 1132), (1825, 1315), (1663, 1315)])
s.flophouse(1700, 1163, label_below=True)
s.inn(1700, 1205)
s.stables(1752, 1246, rot=90)


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


def furrows(poly, color, theta):
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
        g.append(f'<line x1="{mx - dx * diag / 2:.1f}" y1="{my - dy * diag / 2:.1f}" x2="{mx + dx * diag / 2:.1f}" y2="{my + dy * diag / 2:.1f}" stroke="{color}" stroke-width="0.8" opacity="0.8"/>')
        t += 5
    g.append('</g>')
    s.add(''.join(g))


def comb_field(name, sluice, down_deg, seed, field_fall, canal_a, canal_b, offtakes_a, offtakes_b=(), dry_band=(47, 88), avoid=(), mirror_ym=None, dry_keepout=()):
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
    net = build_comb(
        3200,
        2700,
        sluice,
        seed,
        down_deg=down_deg,
        field_fall=field_fall,
        canal_a_len=canal_a,
        canal_b_len=canal_b,
        offtakes_a=offtakes_a,
        offtakes_b=offtakes_b,
        plot_across=PLOT_ACROSS,
        row_step=ROW_STEP,
        dry_band=dry_band,
        dry_keepout=dry_keepout,
        grain=2 / 3,
    )  # 3 ft/px city: scale the carve's real-feet minimum-size thresholds (tuned at 2 ft/px) or the fan drops sectors/head plots/closers and shows parchment holes (paddy_fan_gapless)
    if mirror_ym is not None:

        def m(pts):
            return [(x, 2 * mirror_ym - y) for x, y in pts]

        net["envelope"] = m(net["envelope"])
        for p in net["plots"]:
            p["poly"] = m(p["poly"])
        for dp in net["dry_plots"]:
            dp["poly"] = m(dp["poly"])
            dp["theta"] = -dp["theta"]  # a furrow heading mirrors with the frame
        for c in net["channels"]:
            c["pts"] = m(c["pts"])
        net["bund_beans"] = m(net["bund_beans"])
        if net["brook"]:
            net["brook"] = m(net["brook"])
    env = [(round(x, 1), round(y, 1)) for x, y in net["envelope"]]
    s.field_polys.append([(p[0], p[1]) for p in env])
    # FIELD FLOOR (city grain): soil-tan under every plot/channel so the odd triangles at the
    # canal JUNCTIONS (head-race fork, outfall corner, confluences) read as the field's earthen
    # bund matrix, not the bare parchment background (the GM's "blank bits on the paddies"). See
    # tango.gen.py's comb_field for the full rationale; gated by city_paddy_fan_has_floor.
    s.comb_base_fill(net, name, color="#CDB78C", full_envelope=True)  # soil-tan floor over the FULL envelope: a tight-cropped city has no scrub, so edge junctions must be covered too
    _prior_paddies = [fld["outline"] for fld in s.M["fields"] if fld.get("kind") == "paddy"]  # fans recorded before this one (own entry is appended below, after this loop)
    for dp in net["dry_plots"]:
        if any(_pt_seg(x, y, ln[i][0], ln[i][1], ln[i + 1][0], ln[i + 1][1]) < 16 for ln in avoid for (x, y) in dp["poly"] for i in range(len(ln) - 1)):
            continue  # hem plot would ride the moat / ring road - skip it
        if any(hem_on_paddy(dp["poly"], _pol) for _pol in _prior_paddies):
            continue  # hem plot lands on a NEIGHBORING fan's rice (fans are placed blind to each other; Tango's fe2-into-fe1 incident) - dry_plots_clear_of_paddies
        s.dry_polys.append(dp["poly"])  # footprint-aware: houses/yards/groves stay OFF the crop, not just centered off it
        pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in dp["poly"])
        s.add(f'<polygon points="{pts}" fill="{dp["fill"]}" stroke="#A98C58" stroke-width="1.4" stroke-linejoin="round"/>')
        furrows(dp["poly"], dp["furrow"], dp["theta"])
        s.M["dry_plots"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in dp["poly"]], "crop": dp["crop"], "theta": round(dp["theta"], 3)})
    for p in net["plots"]:
        pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in p["poly"])
        s.add(f'<polygon points="{pts}" fill="{p["fill"]}" stroke="{BUND}" stroke-width="2" stroke-linejoin="round"/>')
    beads = ''.join(f'<circle cx="{x}" cy="{y}" r="1.4" fill="{BEAN_GREEN}"/>' for x, y in net["bund_beans"])
    s.add(f'<g opacity="0.85">{beads}</g>')
    for c in sorted(net["channels"], key=lambda c: -c["w"]):
        s.field_channel(
            c["pts"], '#7C9EB0' if c["role"] == "drain" else '#6C9CBE', c["w"], c.get("w_tail", c["w"]), late=True
        )  # the LATE water block: the city's moat/river opens the shared block EARLY, which would composite the whole ditch net UNDER the plots (invisible network + parchment pinstripes on the uncovered corridors). Since the Hoshizora canals-under-paddies audit (GM 2026-07-21) the late block RE-ANCHORS at every call, so multi-fan maps stay correct too; see settlements.md's late-water bullet
    exs = [p[0] for p in env]
    eys = [p[1] for p in env]
    pvx = [v[0] for p in net["plots"] for v in p["poly"]]
    pvy = [v[1] for p in net["plots"] for v in p["poly"]]
    s.M["fields"].append(
        {
            "name": name,
            "kind": "paddy",
            "outline": [[x, y] for x, y in env],
            "bbox": [min(exs), min(eys), max(exs), max(eys)],
            "vis_bbox": [min(pvx), min(pvy), max(pvx), max(pvy)],
            "plot_polys": [[[round(v[0], 1), round(v[1], 1)] for v in p["poly"]] for p in net["plots"]],
        }
    )  # the drawn paddy plot POLYGONS, so paddy_fan_gapless can see holes inside the fan ("plots" is taken: the polder checks record [along, cross] parcel spans there)
    for c in net["channels"]:
        s.M["field_ditches"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in c["pts"]], "role": c["role"], "field": name, "w": round(c["w"], 1), "w_tail": round(c.get("w_tail", c["w"]), 1)})
    return net, env, (round(sum(exs) / len(exs), 1), round(sum(eys) / len(eys), 1))


def plot_centroid(net, key, inset=0.15):
    """Centroid of the plot chosen by `key` over plot centroids - a point guaranteed INSIDE the
    planted field (the envelope centroid of a curved fan can miss, and the water-source checks
    test the channel END with point_in_poly against the outline). The result is then pulled `inset`
    of the way toward the field's MEAN centroid, so an EXTREMUM plot's centroid still clears the
    smoothed outline edge by the >=10px channel_field_anchored requires - the ~0.05-acre paddy
    calibration (GM 2026-07-22) shrank the edge cells, putting a raw extremum centroid on the hull."""
    cens = [
        (sum(v[0] for v in p["poly"]) / len(p["poly"]), sum(v[1] for v in p["poly"]) / len(p["poly"])) for p in net["plots"] if not p.get("filler")
    ]  # carve plots only: a filler tile hugging the drain rim can win the extremum and put the topo anchor outside the outline (channel_field_anchored)
    cx, cy = key(cens)
    mx = sum(c[0] for c in cens) / len(cens)
    my = sum(c[1] for c in cens) / len(cens)
    cx += inset * (mx - cx)
    cy += inset * (my - cy)
    return (round(cx, 1), round(cy, 1))


def topo_channel(pts, frm, to, draw_w=0.0, col='#7C9EB0'):
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
        pts = list(pts[: k + 1]) + [(mx - 12 * (by - ay) / chord, my + 12 * (bx - ax) / chord)] + list(pts[k + 1 :])
    poly = [[round(px, 1), round(py, 1)] for px, py in pts]
    s.M["channels"].append({"poly": poly, "frm": frm, "to": to, "w": draw_w or 2.5, "drawn": bool(draw_w)})  # drawn=False -> an implied underground conduit (no visible seam, no gate demanded)
    s.corridors.append(([(px, py) for px, py in poly], 33))
    if draw_w:
        s.field_channel([(px, py) for px, py in poly], col, draw_w, draw_w)


# ====================================================================== the street skeleton
# the through-road provides the N-S spine and the E main street; city streets hang off it.
# The yamen approach runs WEST from the crossroads through the ward's east kido.
WEST_ST = [(1188, 1330), (1478, 1330)]
grid([WEST_ST], width_ft=22)
SAM_ST = [
    (1480, 1330),
    (1480, 1726),
]  # starts AT the central crossroads (where the road turns E), runs down the ward's east flank, crosses the S street and Ts INTO the ring bed at (1480,1726) - the through-lane check wants a street either ON the ring centerline or >46px clear of it, and the S street sits 50+px above the crossing so no dangling stub is left
MER_V1 = [(1710, 1246), (1710, 1661)]  # S end lands ON the ring bed centerline (~(1710,1660.5)) for a clean T
MER_V2 = [(1792, 1246), (1792, 1414)]  # collinear under LAB_V2 (see below) - one continuous N-S line from LAB_H to the merchant blocks
grid([SAM_ST, MER_V1, MER_V2])

# ====================================================================== W-central: temple neighborhood
# Suitengu (the river fortune - a river city prays to its water) + Ebisu (honest work and
# trade - the wharf's fortune), with the Ministry of Rites that oversees them
# Crab city -> the great temples are its two PATRON fortunes: EBISU here, BISHAMON in the
# samurai quarter (below). SUITENGU, the river fortune a river city honors, is a small wayside
# shrine among the smattering (unlabeled), NOT a great temple (city_temples_dedicated).
TEMPLE_LANE = [
    (1073, 1216),
    (1480, 1216),
]  # the E-W temple-neighborhood street; Rites + Ebisu front it, it meets the spine; W end lands IN the ring bed (ring centerline x~1029.5 at y1204) so it makes a clean T, not a sliver-short stub (city_streets_meet_through_lanes)
grid([TEMPLE_LANE], width_ft=18)
s.shrine_hall(
    1189, 1142, "Temple of Bishamon", w=s.px(130), h=s.px(84), kind="temple", label_below=True, torii=[(1170, 1196)]
)  # a Crab patron (also the warrior fortune); nudged E so its W edge clears the ring road. ONE torii on the approach walk from the monzen lane (torii_count_canonical 1/3/7), threaded W of the fire tower and below the label
s.block_polys.append([(1120, 1158), (1258, 1158), (1258, 1189), (1120, 1189)])  # Bishamon's below-label band - the monzen pack seated a laborer under the text after the true-size reflow (2026-07-21)
s.shrine_hall(
    1396,
    1142,
    "Temple of Ebisu",
    w=s.px(130),
    h=s.px(84),
    kind="temple",
    primary=True,
    label_below=True,
    # Ebisu ROLLED the full 7-arch avenue (per-temple seeded roll, 2026-07-23 re-roll), so the
    # avenue geometry is authored: a COMPRESSED south sando at ~19px (57 ft) stride - the
    # donation-row look - ending at y1310, short of the samurai ward fence (~y1330). The naive
    # 44px single-point extension marched the arches across the fence onto the Ministry of War.
    torii=[(1396, 1196), (1396, 1215), (1396, 1234), (1396, 1253), (1396, 1272), (1396, 1291), (1396, 1310)],
)  # the other Crab patron. ONE torii on the approach walk from the monzen lane (torii_count_canonical 1/3/7)
s.cemetery(1167, 1246, 44, 32, label="graveyard")  # Bishamon's danka parish ground, S of the hall (kept clear of the temple lane)
s.cemetery(1396, 1075, 44, 32, label="graveyard", label_above=True)  # Ebisu's danka parish ground, N of the hall
s.ministry(1292, 1248, "Ministry of Rites", w=s.px(140), h=s.px(95))
s.theater_stage(1292, 1031, w=s.px(190), h=s.px(132), rot=0, label="theater stage")  # N-central, opens S; clear of the ring road
for sx, sy in [
    (1272, 1122),
    (1292, 1152),
    (1258, 1186),
]:  # small wayside shrines (one is Suitengu, the river fortune) - clustered clear of the graveyards; the first sits E of the monzen roji at x1250 (it rode the lane's bed at its old 1258 seat)
    s.small_shrine(sx, sy)
s.label(1292, 1299, "temple neighborhood", 9, italic=True, color="#6B2A18")

# MONZEN-MACHI: the temple town's commoner housing (pilgrims' inns, shrine craftsmen, their
# servants) packs the NW ground around the halls. A temple neighborhood was historically DENSE
# (Zenkoji, Ise, Naritasan monzen-machi), and this fills the quarter the first Nagahara draft left
# nearly empty - the exact lopsidedness feature 006 exists to catch.
# reserve the 'Temple of Ebisu' label grounds too (2026-07-21): the Ebisu torii's block-out shifted
# the quarter pack and a laborer house slid under the caption (labels_clear_of_other_buildings)
s.block_polys.append([(1338, 1163), (1454, 1163), (1454, 1185), (1338, 1185)])
# reserve the temple-neighborhood LABEL grounds so the monzen packs avoid them (labels draw last)
for _lx0, _ly0, _lx1, _ly1 in [
    (1133, 1172, 1247, 1194),  # 'Temple of Bishamon'
    (1138, 1263, 1197, 1281),  # 'graveyard'
    (1231, 1290, 1353, 1310),  # 'temple neighborhood'
    (1076, 1243, 1122, 1266),
]:  # a clear pocket beside the teahouse cluster (held the 'monzen' caption until GM 2026-07-21 dropped it as redundant with 'temple neighborhood'; the reservation stays so the quarter's packing does not re-roll)
    s.block_polys.append([(_lx0, _ly0), (_lx1, _ly0), (_lx1, _ly1), (_lx0, _ly1)])
s.fire_tower(
    1206, 1194, label=None
)  # the monzen's fire-watch, in an open court amid the terrace rows near the district centroid (keeps fire_tower_amid_its_district honest; >=5px off every house, clear of the graveyards and the curving west wall)
# NO monzen back-alley in the WEST column: after the budget-first shrink it is a ring-front
# sliver (Bishamon's stand-clear circle + the W ring arc leave ~2 dwellings there), and an alley
# that uniquely serves so few trips alleys_serve_buildings - the temple lane carries that flank.
# But the MID-BLOCK (between Bishamon and the theater) DOES need its roji now: the pair cadence
# (outward-facing doctrine, 2026-07-18) pushed the deep monzen rows >95px from the temple lane
# (the ring road is a patrol bed, not circulation), stranding a 30+ dwelling cluster
# (no_isolated_dwelling_cluster). One N-S lane from the ring bed (~y999.6 at x1250) down the
# Bishamon/theater seam serves the whole mid-block - 30+ unique dwellings over ~160px easily
# earns its length. Drawn BEFORE the packs so the terrace rows flow around it; the end stays
# >46px above the temple lane (a dead-end roji, not a near-miss junction).
alleys([[(1250, 1000), (1250, 1160)]])
s.block_polys.append(
    [(1246, 1054), (1338, 1054), (1338, 1078), (1246, 1078)]
)  # the 'theater stage' label's ground (a theater label may cover no building at all; the theater's own stand-clear circle only shields its middle)
s.place_wells((1082, 1105, 1271, 1300), spacing=58)
# FUNERAL TRADES cluster by the GRAVEYARD, not the halls (Edo gravestone cutters and
# coffin-makers sat by the burial grounds; China-first adds the joss-paper/spirit-money trade):
# two shopfronts flanking Bishamon's danka ground on the temple lane - a coffin-maker and a
# grave-marker stonecutter at map scale ARE the generic `shop` glyph; the story is placement.
# NO amulet/religious-goods shops anywhere in the city: charms, incense and lamp-oil are
# TEMPLE-DIRECT sales (a temple revenue stream), so no third-party storefront competes at the
# temple's own gate. rot=180 fronts them onto the lane (businesses_front_streets); placed
# BEFORE the lane's frontage row, which flows around them.
s.building(1133, 1229, *s._dims("shop"), "shop", 180)
s.building(1201, 1229, *s._dims("shop"), "shop", 180)
# the monzen lines its OWN street: pilgrim-quarter housing fronting the temple lane on both
# sides is the defining monzen-machi image (Zenkoji/Naritasan approach streets were solid
# house-fronts), and the pair-cadence reflow (2026-07-18) needs the frontage band's capacity -
# the deep rows alone no longer meet the budget's 600-dwelling promise. SHOPS LEAD THE LIST
# (2026-07-20): ~6 teahouses/eateries take the lane's WEST stretch - the modest gate-front
# refreshment cluster a `monzen` caption promises. Nagahara's worship traffic is REGIONAL (an
# ordinary provincial city, not a pilgrimage destination), so the gate economy stays a handful
# of teahouses, NOT a full monzen-machi strip. The rest stays SERVANT: the halls' and pilgrims'
# attendants (shop and servant are both label-exempt in labels_clear_of_other_buildings, so the
# row may run under the temples' name-boxes where a laborer house may not; servants also not in
# the poor set for poor_housing_mostly_interior). Shops are business frontage, not dwellings -
# the x5 population count is untouched and top_up re-seats the displaced servants in the caste
# bands. Placed AFTER the halls/ministry/graveyards (fixed seats), BEFORE the packs.
front([TEMPLE_LANE], ["shop"] * 6 + ["servant"] * 40, spacing=19, rows=1)
s.well_at(
    1320, 1080
)  # a seeded idobata for the theater-south strip's E end: the monzen roji reflow left its densest pocket drawing 30 households from one well (city_well_density_sufficient) - seated BEFORE the rows so the terrace breaks into a court around it
for _wc in [(1330, 1170), (1320, 1140), (1310, 1178)]:
    if s.well_at(*_wc):
        break  # candidate fan (first clear seat wins): a court in the Bishamon-pocket band's SE corner - the (1292,1098) draw-point serves ~30 households whose southern half (y1140-1193) needs its own idobata (city_well_density_sufficient); the hall and the wayside shrines guard everything further W
s.place_wells((1228, 1058, 1356, 1100), spacing=52)  # courts for the theater-south terrace strip
s.place_wells((1170, 957, 1395, 1003), spacing=56)  # courts for the ring-front strip N of the theater
s.place_wells((1360, 1232, 1458, 1298), spacing=56)  # courts for the temple-lane SE pocket
for _wc in [
    (1181, 1041),
    (1187, 1053),
    (1199, 1069),
    (1214, 1090),
    (1232, 1108),
    (1201, 1116),
    (1247, 1069),
]:  # a second seeded idobata INSIDE the swamped catchment (28 households, x1176-1318 y1038-1157, centroid ~1228,1090): the true-size temple reflow (2026-07-21) re-packed the warren and its densest well went back over the 26-household ceiling (city_well_density_sufficient). Candidate LIST per the well_at doctrine - the blocked spots no-op; a first single attempt at (1216,1178) sat outside the catchment and a second at (1181,1041) alone failed _fits
    if s.well_at(*_wc):
        break
s.rowpack((1082, 1114, 1160, 1303), (["laborer"] * 2 + ["laborer_large"] + ["servant"]) * 34, court_every=7, eave_ft=3)  # x0 rides the W ring arc (the bound clips what the curve disallows)
# south-strip y1 pulled to 1300: rowpack does not read corridors, so at y1 1310 the bottom row's
# eave clipped the ward-fence line at y1311 (city_ward_fence_clear_of_structures at (1161,1302));
# y0 1240 also claims the one open row between the graveyard label and the old 1265 edge
s.rowpack((1102, 1240, 1271, 1300), (["servant"] + ["laborer"] * 2 + ["laborer_large"]) * 28, court_every=7, eave_ft=3)
s.rowpack(
    (1221, 1105, 1344, 1200), (["laborer"] * 2 + ["servant"] + ["laborer_large"]) * 16, court_every=7, eave_ft=3
)  # the pocket N of the temple lane, E of Bishamon, W of the theater; y1 1200 (was 1190) - the lane's own frontage band in `lines` is the real stop, the extra depth recovers a pair-cadence row
s.rowpack(
    (1225, 1058, 1360, 1102), (["laborer"] * 2 + ["servant"] + ["laborer_large"]) * 12, court_every=7, eave_ft=3
)  # the strip between the theater's S face and the Bishamon pocket - open ground the budget-first ring can no longer afford to leave bare
s.rowpack((1165, 953, 1400, 1005), (["laborer"] * 2 + ["servant"] + ["laborer_large"]) * 16, court_every=7, eave_ft=3)  # the ring-front strip N of the theater, up against the NW ring arc
s.rowpack(
    (1358, 1228, 1462, 1300), (["laborer"] * 2 + ["servant"] + ["laborer_large"]) * 12, court_every=7, eave_ft=3
)  # the temple-lane SE pocket, between the Rites apron and the spine's frontage band
s.rowpack(
    (1130, 1012, 1258, 1102), (["laborer"] * 2 + ["servant"] + ["laborer_large"]) * 14, court_every=7, eave_ft=3
)  # the NW-arc wedge W of the theater, N of Bishamon (the ring bound clips its taper)
# NO "monzen" caption (GM 2026-07-21): the quarter already carries the "temple neighborhood" label,
# and its monzen-machi commerce pocket is part of that same named district - one caption per district,
# never a second caption for a sub-pocket of an already-labeled neighborhood.

# ====================================================================== W: the samurai/government ward
# the government + samurai occupy the SW quadrant, WEST of the spine (the merchant district is
# east of it) - sealed by a ward fence that abuts the wall on the W and the SW, entered from the
# commoner side by two kido on the east fence.
GOV_AVE2 = [(1126, 1403), (1480, 1403)]  # the government avenue; meets the spine (SAM_ST) at x1480, W end kept >46px clear of the ring bed
grid([GOV_AVE2])
s.governor_mansion(1292, 1524, s.px(436), s.px(366), "Governor's Mansion", gate_dir="north")
MINS = ["Ministry of Revenue", "Ministry of Retainers", "Ministry of War", "Ministry of Works", "Ministry of Justice"]
MIN_POS = [
    (1115, 1367),
    (1258, 1367),
    (1403, 1367),
    (1135, 1467),
    (1430, 1460),
]  # 3 N of the avenue, 2 S, all fronting it; Works sits 7px deeper off the avenue than Justice - its 30px scatter apron is marginally under the 30.7 a rotated samurai_large needs (see the phase-1 apron note), and the extra depth keeps the pack's avenue-band houses clear of the 14px office gap (city_government_offices_dont_abut)
for (mx, my), name in zip(MIN_POS, MINS, strict=True):
    s.ministry(mx, my, name, w=s.px(130), h=s.px(90))
s.mausoleum(
    1292, 1608, 44, 32, label="Mausoleum", gate_dir="north", label_below=True
)  # the ruling clan's crypt, below the yamen (clear of the diagonal SW ward fence). Label BELOW: the crypt sits directly under the governor's mansion, so a label above it would land on the governor (labels_clear_of_other_buildings); below drops it into the reserved margin between crypt and fence.
# civic stand-clear aprons, PHASE 1 (the scatter pack): 30px around ministries/yamen/mausoleum.
# 30 is load-bearing for the pack: face_streets rotates houses, and a rotated samurai_large's bbox
# reaches ~16.7px past its center, so city_government_offices_dont_abut (14px AABB gap) needs
# 30.7-. The mausoleum's wide apron ALSO holds the burakumin terrace rows off the ward fence's SW
# diagonal (rowpack does not read corridors). Phase 2 (below, before the top_up fills) swaps the
# ministry/yamen aprons down to 16: top_up places axis-aligned and its own ok() enforces a 15px
# AABB gap from every office, so the fills may use the tight N-fence and mansion-flank bands the
# budget-first ring can no longer afford to leave bare.
_CIV_I0 = len(s.block_polys)
for _m in s.M["ministries"] + [s.M["governor_mansion"]]:
    s.block_polys.append(
        [
            (_m["x"] - _m["w"] / 2 - 30, _m["y"] - _m["h"] / 2 - 30),
            (_m["x"] + _m["w"] / 2 + 30, _m["y"] - _m["h"] / 2 - 30),
            (_m["x"] + _m["w"] / 2 + 30, _m["y"] + _m["h"] / 2 + 30),
            (_m["x"] - _m["w"] / 2 - 30, _m["y"] + _m["h"] / 2 + 30),
        ]
    )
_CIV_I1 = len(s.block_polys)
for _m in s.M["mausoleums"]:
    s.block_polys.append(
        [
            (_m["x"] - _m["w"] / 2 - 30, _m["y"] - _m["h"] / 2 - 30),
            (_m["x"] + _m["w"] / 2 + 30, _m["y"] - _m["h"] / 2 - 30),
            (_m["x"] + _m["w"] / 2 + 30, _m["y"] + _m["h"] / 2 + 30),
            (_m["x"] - _m["w"] / 2 - 30, _m["y"] + _m["h"] / 2 + 30),
        ]
    )
# a ministry's italic label is WIDER than its footprint, so reserve the label's own ground (+ a
# house-half margin) before the samurai pack runs - else a packed house sits behind the label and
# reads as mislabelled (labels_clear_of_other_buildings). Read the boxes the ministry() calls just placed.
for _L in s.M["labels"]:
    if len(_L) > 5 and _L[5].startswith("Ministry"):
        s.block_polys.append([(_L[0] - 15, _L[1] - 12), (_L[2] + 15, _L[1] - 12), (_L[2] + 15, _L[3] + 12), (_L[0] - 15, _L[3] + 12)])
# reserve the narrow wedge where the SW diagonal fence dips closest to the packed rows near the
# governor: at corridor half-width 15 one pack house would seat here and clip the fence line
# (city_ward_fence_clear_of_structures). A small block here drops just that one house; the rest of
# the ward keeps the tighter 15px corridor, so overall samurai count stays >= 39.
s.block_polys.append(
    [(1362, 1581), (1472, 1581), (1472, 1622), (1362, 1622)]
)  # widened to also hold the 'burakumin' label's ground (its box sits on this reserve, just S of the fence diagonal), and W to x1362: corridors gate a candidate's CENTER only, so a ~93deg-rotated samurai_large seated at (1396,1615) - 1.8px past the 15px corridor - reached its long axis up through the fence line (city_ward_fence_clear_of_structures); the box holds pack centers off the whole diagonal stretch the corridor's center-test cannot
# lace the deep samurai block BEFORE packing so the packer reserves the lane corridors; ends
# stay inset off the ward wall so they do not trip the ward-gate / seal checks
# NO interior ward alleys: the ministries + the yamen fill most of the ward, and the samurai homes
# around them front the three ward streets (WEST_ST, GOV_AVE2, SAM_ST) directly - a deep service
# lane here would only shadow a street or run against a compound, serving too few to justify itself.
# junior-samurai ROW BARRACKS (kumi-yashiki nagaya, the Tango precedent) fill the two flank bands
# the scatter pack cannot reach - rowpack's tighter standoffs (5.8px ring edge, 13px street edge)
# use the ground between the civic aprons and the ring arc that the pack's corridor gates waste:
s.rowpack((1122, 1523, 1200, 1604), ["samurai"] * 24, court_every=6, eave_ft=3)  # W flank, below the Ministry of Works apron, riding the SW ring arc (the bound clips the taper)
s.rowpack(
    (1390, 1505, 1452, 1565), ["samurai"] * 20, court_every=6, eave_ft=3
)  # E flank, between the Ministry of Justice apron and the E ward fence (x1 1452 keeps every gable >4px off the fence at x1469; y1 1565 keeps the bottom row off the SW fence DIAGONAL, which leaves (1469,1570) heading down-left)
# senior samurai LINE the ward's own streets (city_samurai_partly_front_streets is the check's
# form of the same fact): a tight frontage row on the yamen approach + the government avenue
# seats houses the scatter pack's corridor gates waste ground on, and the pair-cadence reflow
# (2026-07-18) needs them to keep the neighborhood >= the ~39-house depiction floor
# (city_samurai_housing_sufficient) - the civic aprons and the fence corridor gate each seat,
# so only the real between-ministry gaps fill
front(
    [WEST_ST, GOV_AVE2], (["samurai_large"] + ["samurai"] * 2) * 5, spacing=19, rows=1
)  # the LARGE senior houses take the avenue frontage (rank fronts the yamen approach) - the frontage is also what reliably seats the >=3 larges city_samurai_housing_varied wants, now that the packed ward leaves the scatter no large-footprint gaps
# step 11 (the Tango value): with the ward's pack regions shrunk x0.825 in area but the house
# glyphs full-size, the usable ground is now two bands - W of the yamen (ring arc to the mansion's
# W apron) and E of it (mansion apron to the fence corridor at x1469-15; see the fence-corridor
# width 15 trade-off note above) - and the coarser step 13 scan stranded seats in both.
s.pack((1073, 1309, 1469, 1612), (["samurai"] * 3 + ["samurai_large"]) * 150, step=11, face_streets="fill")
s.label(
    1426, 1534, "samurai neighborhood", 10, italic=True, color="#3A352C"
)  # E of the governor's mansion among the ward's samurai (x1426: the label box's W edge must clear the mansion's E edge at x~1365), clear of the burakumin rows to the S
s.ward("samurai", [(1039, 1311), (1469, 1311), (1469, 1570), (1217, 1666)], gates=[(1469, 1330, True), (1469, 1403, True), (1062, 1311, True), (1234, 1660, True)])  # 2 street kido + 2 ring-road kido
s.label(1433, 1317, "samurai ward gate", 9, italic=True, color="#5A4326")  # inside the ward by the E-fence kido, off the merchant frontage

# ====================================================================== N + NE: the LABORER quarter
# one big contiguous block E of the spine, laced with a street grid wired to the N-gate spine;
# master laborers front the streets, terraces pack the blocks; the E-gate caravan pocket is clear.
LAB_H = [(1480, 1134), (1845, 1134)]  # E end reaches the ring bed at a clean T-junction
# LAB_V1 runs all the way S to the main street (a T at the road centerline - stopping in the
# 46px approach band reads as a dead-end sliver); LAB_V2 spans LAB_H down to MER_V2's top end,
# so the two collinear streets read as one continuous N-S line with no near-miss gap at either end
LAB_V1, LAB_V2 = (
    [(1605, 1039), (1605, 1330)],
    [(1792, 1134), (1792, 1246)],
)  # x1792 (not 1814): LAB_H runs on to the ring at x~1846, and a crossing within 50px of its end would read as a dangling stub
grid([LAB_H, LAB_V1, LAB_V2])
s.fire_tower(1670, 1068, label=None)
front(
    [LAB_V1, LAB_V2], (["shop"] + ["laborer_large"] * 3) * 10, spacing=18, rows=1
)  # items sized past the two streets' ~42 slots so the list never binds before the ground does (pair-cadence capacity)
# keep the rowpack rows HOMOGENEOUS (all small terraces): a rowpack sizes each row to its tallest
# house, so a stray laborer_large mid-row would inflate every row and gut capacity. The wealthier
# 'master' laborers (budgets.md's ~12.5% cohort) are seeded on the street frontage and topped up
# individually below, where a larger footprint drops into a gap without heightening a whole row.
_lab = (["laborer"] * 3 + ["servant"]) * 140
# the 1618-1848 street gap (230px) is too wide - lace a mid alley (BEFORE the packs) so no terrace is cut off
# one mid alley for the 1618-1848 street gap: it drops from just below the ring road (top end
# kept >46px clear of the ring bed at ~y957) to LAB_H. No lower stub - the ground S of LAB_H
# here is the reserved E-gate caravan pocket, so an alley there would serve nothing.
alleys([[(1710, 1000), (1710, 1134)]])  # top end lands ON the ring bed centerline (~y999.5 at x1710) - post-shrink the ring sits 45px from the old y1050 stub, inside the 46px must-meet band
# the SPINE'S in-wall leg carries house-fronts too (pair-cadence capacity, same rationale as
# the temple lane): the wealthier 'master' laborers take the prime road frontage (the real
# machiya pattern - budgets.md's ~12.5% cohort lining the best streets), plain laborers between
# them; the N-gate reserve, the monzen rows and the road's own corridor gate each seat. Poor
# on-street headroom is ample (47/227 vs the 50% ceiling before this row).
s.frontage(
    [(1480, 940), (1480, 1325)], (["laborer_large"] + ["laborer"] * 2) * 20, skip=ROAD, width=s.lw(26), spacing=19, rows=2, rowgap=2, jitter=1, setback=s.px(14)
)  # rows=2: the rear row seats back-to-back facing AWAY (the ura-dana pattern the engine's frontage doctrine draws), claiming the deep band the warren rows cannot phase into
# coarse well courts AFTER the alleys (so no wellhead lands on the mid alley) and BEFORE the packs
# (so the terraces flow around them); tight spacing for the dense warren (~1 well per 10-20 households)
# pre-reserved wells (the merchant-district pattern below): the warren's densest pockets - the
# west column against the spine and the deep mid-strip E of the x1710 alley - each need their own
# idobata court seated BEFORE the rows run, or the fine passes find no clear court and one well
# ends up serving 30-40 households (city_well_density_sufficient)
s.well_at(1515, 1170)
s.well_at(1515, 1250)
s.well_at(1745, 1062)
s.well_at(1770, 1112)
s.place_wells((1496, 977, 1869, 1286), spacing=64)
s.place_wells((1549, 1094, 1671, 1272), spacing=48)  # extra courts for the deep mid-strip between the x1618 street and x1530 column
for _wc in [(1550, 1165), (1562, 1180), (1540, 1152)]:
    if s.well_at(*_wc):
        break  # candidate fan: the spine's new house-fronts pushed the W-column draw-point at (1528,1201) to 42 households (bbox y1155-1242) - a court on its northern half splits the load (city_well_density_sufficient)
for _wc in [(1570, 1245), (1580, 1258), (1556, 1240)]:
    if s.well_at(*_wc):
        break  # candidate fan: the band's y1300 extension then left the (1545,1282) draw-point at 27 (centroid ~1543,1265) - one more court on the deep rows' seam
s.place_wells(
    (1490, 950, 1595, 1115), spacing=46
)  # a DENSER court grid over the N-gate's two swamped catchments (the (1528,1009)=28 and (1545,1090)=30 draw-points): the true-scale gate furniture (2026-07-22) shrank the guard house/tower and freed ground, so the N rows re-packed denser than the 64px grid could water (city_well_density_sufficient). Seeded BEFORE the rows so each terrace breaks into a court around it
s.rowpack(
    (1496, 927, 1878, 1127), _lab, court_every=4, eave_ft=3
)  # E edge extended to the ring corridor (court_every stays 4: the parameter sweep showed thinner courts LOSE houses here - row phase beats court count - and the idobata courts carry the well-density check)
s.rowpack(
    (1496, 1142, 1878, 1307), _lab, court_every=4, eave_ft=3
)  # y1 1307 (was 1286): the pair cadence costs the band a row vs the old uniform spacing, and the road's own 28px frontage band (rowpack reads it from `lines`, edge ceiling ~y1307.7) is what actually stops the rows - the extra depth lets the last pair seat
s.label(1621, 1169, "laborer neighborhoods", 10, italic=True, color="#5A4326")  # W of the E-gate caravan flophouse

# ====================================================================== E-central: merchants + the dock
MER_ST = [MER_V1, MER_V2]  # gridded in the skeleton
# storefronts line the main-street stretch of the through-road between the crossroads and
# the river gate (the road-market of a river city, inside the walls)
s.fire_tower(1742, 1502, label="fire tower")  # amid the merchant dwellings, before the packs
s.block_polys.append(
    [(1690, 1484), (1769, 1484), (1769, 1548), (1690, 1548)]
)  # reserve the fire-tower + its label ground (widened W/S 2026-07-19: with the estate resited south, the label's SW flank became packable row ground and a merchant house seated under the caption)
# reserve the cargo-canal corridor and the walled merchant-estate court BEFORE the packs fill
# this ground: the Suzhou dock strip is a working waterway (no dwelling stands in it) and the
# estate's court is walled ground, so no pack house may land on either
s.block_polys.append([(1818, 1444), (1886, 1444), (1886, 1486), (1818, 1486)])  # canal mouth strip just inside the wall
s.block_polys.append(
    [(1704, 1511), (1797, 1511), (1797, 1585), (1704, 1585)]
)  # merchant estate court at (1750,1548), 62x46, + a house-half margin - resited 2026-07-19: the old seat by the dock ran its wall into the dock basin / fire tower / merchant street (the estate-wall siting rules); this seat clears the street band (west wall 1719 vs the x1710 street), the tower (north wall 1522 vs the tower's y<=1509 band), and all water
# seat a well in the far-E merchant block BEFORE the frontage/packs run, so it reserves its own
# court and the houses flow around it - the block is otherwise too dense to split its lone well's load
s.well_at(1851, 1394)
# WHARF SHRINE to EBISU at the dock basin (2026-07-20): Ebisu is the fortune of fishermen and
# honest commerce, so the water economy's heart gets its own threshold shrine - wayside shrines
# historically stood exactly where a settlement's life turns (a landing, a crossing, a gate) -
# and it echoes the Temple of Ebisu across town. Unlabeled like the temple-quarter wayside
# cluster (the glyph reads; the dedication is flavor recorded here). Placed BEFORE the merchant
# frontage/packs; sited in the pocket BETWEEN the basin and the estate court, where its reserve
# block mostly overlaps ground the canal-strip + estate-court reserves already deny to housing
# (the 566-dwelling target is ground-limited, so the shrine must not eat open row seats) -
# clear of the dock/canal/water-gate footprints and of the x1792 street's end. It is EXTRA
# flavor - the 3 shrines by the temple cluster still carry city_temple_neighborhood_has_shrines.
s.small_shrine(1800, 1493)
for _mrx, _mry in [(1580, 1394), (1580, 1614)]:
    s.block_polys.append([(_mrx - 22, _mry - 16), (_mrx + 22, _mry - 16), (_mrx + 22, _mry + 16), (_mrx - 22, _mry + 16)])
s.frontage([(1501, 1330), (1898, 1330)], (["merchant"] * 3 + ["shop"]) * 16, skip=ROAD, width=s.lw(26), spacing=19, rows=2, rowgap=2, jitter=1, setback=s.px(14))
front(MER_ST, (["merchant"] * 3 + ["shop"]) * 8, spacing=19, rows=1)
s.merchant_storehouses(8)
# WALLED COMPOUND COUNT IS ROLLED, 1-3 per city (GM 2026-07-23): a gated compound is a GRANTED
# privilege - see MERCHANT_ESTATE_WEIGHTS (settlement.py) for the Edo-privileges reasoning and
# merchant_estates_match_roll for the gate. Seats 2-3 are the _ML_SPOTS very-rich homes, shifted
# west (1580 -> 1565) so the court wall clears the x1604 roji, gating EAST onto it; an unrolled
# seat keeps its unwalled large house (the _ML_SPOTS tail below).
_n_est = s.merchant_estates([(1750, 1548, "south"), (1565, 1394, "east"), (1565, 1614, "east")])
_ML_SPOTS = [(1580, 1394), (1580, 1614)][_n_est - 1 :]
_mer = (
    (["merchant_house"] * 2 + ["servant"] + ["laborer"]) * 130
)  # 2:1:1 (was 3:1:1): interleaving more servants/laborers between the merchant homes is what keeps the merchant-to-merchant nearest-neighbor spread >= 1.3x the laborer warren (city_merchant_housing_spread) while the rows themselves stay contiguous
_MER_COURT = 4  # 3->4: one more terrace row per block; the fine near=48 well passes still find the remaining courts
# west strip (1567-1733) lacks a street - lace an alley (BEFORE the packs) so the houses aren't cut off
alleys(
    [[(1604, 1380), (1604, 1656)]]
)  # ONE continuous roji (the old three segments left open mouths at the row-band boundaries where a top_up house corner could clip an alley end); top pulled >46px clear of the main road (centerline y1330, so the top must start at y>=1377 - the road-frontage rows fill the ground between, blocking any lanes-should-meet reading)
# coarse well courts AFTER the alleys (no wellhead on the x1617 lanes) and BEFORE the packs; tight
# spacing so the merchant warren is not left with over-burdened wells
s.place_wells((1494, 1349, 1875, 1660), spacing=64)
s.place_wells((1694, 1357, 1831, 1593), spacing=52)  # extra courts for the broken east merchant strip (MER_V1 / fire tower / estate leave sparse well ground)
# rowpack W edge at 1492 (was 1559): the band between SAM_ST and the x1604 alley was left bare by
# the similarity shrink (regions shrank x0.825 in area, glyphs did not) - the ward-gate kido
# reserves still hold the x1492-1514 strip open where the fence gates need their ground
s.rowpack(
    (1492, 1350, 1875, 1456), _mer, court_every=_MER_COURT, eave_ft=3
)  # y1 1456 (was 1444): the estate-court/canal reserves gate the deep spots individually, so the band may run to the canal strip - recovers a pair-cadence row
s.rowpack((1492, 1460, 1875, 1570), _mer, court_every=_MER_COURT, eave_ft=3)
s.rowpack((1492, 1585, 1875, 1656), _mer, court_every=_MER_COURT, eave_ft=3)  # y1 1656: BUR_ST (y1670) is drawn AFTER this pack, so the rows must keep its 12px frontage band clear by construction
s.rowpack((1640, 1657, 1875, 1676), _mer, court_every=_MER_COURT, eave_ft=3)  # the one extra row E of the S street's end (x1626), running to the SE ring arc
s.label(1700, 1349, "merchant district", 10, italic=True, color="#5A4326")

# ====================================================================== SE: burakumin (downstream)
# the polluting trades sit BELOW the city on the current - downstream placement is the
# historically exact site for them (tanners, dyers, the death-trades)
# the DOWNSTREAM (south) quarter: burakumin (the polluting trades below the city on the current)
# with servants; one big block spanning the south interior, laced by the S street
BUR_ST = [
    [(1317, 1670), (1626, 1670)]
]  # W end pulled clear of the ring bed (which hugs close at the SW arc); the whole street sits at y1670 so SAM_ST's run down to the ring at (1480,1726) crosses it 56px (>=50) before ending - no dangling intersection stub
grid(BUR_ST)
s.fire_tower(1396, 1650, label=None)  # amid the downstream quarter, before the packs (above the S street)
# idobata courts seated BEFORE the street frontage AND the rows (both flow around a placed
# well; AFTER the frontage no candidate clears its houses any more, and the whole strip S of
# the S frontage row is ring-road corridor, so no court can ever seat down there)
for _wc in [(1454, 1628), (1430, 1645), (1460, 1642)]:
    if s.well_at(*_wc):
        break  # the E court: the S street's house-fronts pushed the old (1526,1637) draw-point to 45 households
for _wc in [(1360, 1634), (1374, 1640), (1348, 1642)]:
    if s.well_at(*_wc):
        break  # the W court: the quarter's W half (x1302-1383, ~13 households on both sides of the street) still drew from the E court (29 > the 26 ceiling); seats between the fire tower's stand-clear and the mausoleum apron
# the S street carries its own house-fronts (pair-cadence capacity, same rationale as the
# temple lane): servant-heavy so the on-street poor stay a minority (poor_housing_mostly_interior)
front(
    BUR_ST, (["burakumin"] + ["servant"]) * 12, spacing=19, rows=1
)  # items sized past the street's ~32 slots so the list never binds before the ground does; burakumin-first keeps the quarter's own caste at its ~30-household budgets.md share (city_caste_counts_in_band) while servants stay under their 156 cap
s.place_wells((1278, 1630, 1634, 1737), spacing=56)
# top band x0 stays 1278: the ward-fence DIAGONAL crosses further west and rowpack does not read
# corridors - the mausoleum's 30px reserve is what actually keeps these rows off the fence line
s.rowpack((1278, 1626, 1634, 1660), (["burakumin"] * 2 + ["servant"] * 2) * 55, court_every=6, eave_ft=3)
s.rowpack(
    (1278, 1683, 1634, 1752), (["burakumin"] * 2 + ["servant"] * 2) * 55, court_every=6, eave_ft=3
)  # y1 1752 (was 1743): the ring bound clips what the SW arc disallows - the extra depth recovers a pair-cadence row
s.label(1443, 1612, "burakumin", 10, italic=True, color="#6B4F2A")

# ====================================================================== OUTSIDE the walls
s.bound = None
# the WHARF suburb (the riverfront guan-xiang) outside the river gate: jetties on the bank,
# warehouse-and-market rows along the quay, the gate market of a river city
for jx, jy in ((2044, 1211), (2044, 1296), (2044, 1386)):
    s.jetty(jx, jy, rot=0, length=22)  # root on the river's WEST bank (~2101 = centerline 2126 - half-width 20 - 5px onto land), running E into the water
QUAY = [(2009, 1236), (2009, 1424)]
s.frontage(
    QUAY, ["shop"] * 18, width=s.lw(18), spacing=19, rows=2, rowgap=2, jitter=1, setback=s.px(14)
)  # the riverfront wharf is warehouses/SHOPS, not merchant residences (commoner dwellings shelter inside the wall - feature 006)
s.label(1998, 1201, "wharf", 10, italic=True, color="#5A4326")

# a gate market (guan-xiang) OUTSIDE THE NORTH GATE too: the wharf is the river gate's market, but
# the north gate is on the road to the Imperial highway, so it grows its own smaller stall cluster
# (GM decision 2026-07-22 - a guan-xiang at every trafficked gate; flophouse-research.md). A short
# stall row flanks the NW-slanting north road just above the moat (y888), clear of the N-gate
# flophouse at (1405, 837).
s.frontage(
    [(1451, 829), (1418, 763)], ["shop"] * 9, skip=ROAD, width=s.lw(22), spacing=17, rows=1, jitter=1, setback=s.px(16)
)  # flanks the REAL north-road segment (two of its vertices) so the stalls sit clear of the road bed
s.label(1508, 806, "gate market", 9, italic=True, color="#5A4326")

# samurai country estates: DISPERSED walled compounds across the Hayakawa to the NORTHEAST (toward
# Otosan Uchi - a samurai builds his country seat on the capital-facing side), each a fortified country
# seat on its OWN land, SPREAD APART and mostly OFF-MAP (miles out) - NOT a cluster (that belt is the
# commercial suburb). They commute in over the bridge. See settlements.md 'Historical grounding'. Sizes
# + formal-gate direction vary; >= 200px apart (city_samurai_estates_dispersed), at most 3 shown.
# PADDY FIRST (GM 2026-07-23, Tango-recipe): the river-fed fne1 fan claims the far bank's northern
# ground; the gentry keep the leftover south half of the NE quadrant (capital_dir=northeast needs
# BOTH half-planes, so this strip between the fan and the wharf road is exactly their ground), one
# a fraction at the frame edge with its land running on.
EST = [
    (2160, 1230, 76, 48, "north", (2391, 1255)),  # lower NE, by the bridge road
    (2340, 1120, 84, 56, "west", (2391, 1120)),  # E, mid-strip
    (2500, 1270, 94, 62, "south", (2560, 1300)),
]  # E edge, a fraction at the frame
for ex, ey, ew, eh, gd, (_lx, _ly) in EST:
    s.manor(ex, ey, ew, eh, "", gate_dir=gd)
    # NO drawn driveway (GM 2026-07-23, Tango-recipe: the long worn drives read as fat roads; the
    # check doctrine says estate approach lanes are "not drawn at this scale"). Targets kept for record.
s.label(2337, 1305, "samurai estates", 10, italic=True, color="#3A352C")  # below the estate strip, above the wharf road

# surrounding farmland: three large moat-fed combs on the landward faces; a river-fed comb on
# the far bank (its tap draws straight off the Hayakawa)
MOAT_FARMS = [
    ("fw1", (1020, 1090), 190, 21, 170, (150, 200), (90, 120), (0.35, 0.7)),
    ("fw2", (990, 1455), 168, 22, 180, (150, 200), (90, 120), (0.4, 0.75)),
    ("fs1", (1292, 1811), 130, 38, 170, (130, 170), (85, 115), (0.4, 0.78)),
    ("fss1", (1650, 1800), 100, 39, 170, (120, 160), (80, 110), (0.4, 0.75)),  # S band E of fs1, falling S off-frame (GM 2026-07-23 rollout)
]  # fs1's local comb seed 23->38: post-shrink, seed 23's smoothed rim overran the westmost plot by 64px of unplanted claim (field_outline_matches_planting; the drain rim, not the canals - trimming canal spans moved nothing), while seed 38 plants the same footprint to within 34px
for nm, tap, dd, sd, ff, ca, cb, oa in MOAT_FARMS:
    mp = min(MOAT, key=lambda p: (p[0] - tap[0]) ** 2 + (p[1] - tap[1]) ** 2)
    _ol = math.hypot(mp[0] - CX, mp[1] - CY) or 1.0
    sl = (round(mp[0] + 30 * (mp[0] - CX) / _ol), round(mp[1] + 30 * (mp[1] - CY) / _ol))
    s.field_channel([mp, sl], '#9CB4C8', 7, 7)  # the visible tap, in the MOAT'S OWN water color (confluence, not crossing - GM 2026-07-23)
    s.sluice_gate(sl[0], sl[1], rot=math.degrees(math.atan2(sl[1] - mp[1], sl[0] - mp[0])) + 90)  # the intake gate AT the palette seam (tap water -> canal water)
    _net, _env, _cen = comb_field(nm, sl, dd, sd, ff, ca, cb, oa, avoid=(MOAT,))
    _pd = plot_centroid(_net, lambda cs: max(cs, key=lambda pc: pc[1]))
    # pull the delivery endpoint a touch toward the field centroid so it lands a clear >=10px
    # INSIDE the outline (a bottom-row plot centroid can sit within a bund's width of the edge)
    _pd = (round(0.80 * _pd[0] + 0.20 * _cen[0], 1), round(0.80 * _pd[1] + 0.20 * _cen[1], 1))
    topo_channel([(mp[0], mp[1]), sl, _pd], {"kind": "moat"}, {"kind": "field", "name": nm})
    _dr = next(c["pts"] for c in _net["channels"] if c["role"] == "drain")
    topo_channel([tuple(_dr[-2]), tuple(_dr[-1])], {"kind": "drain"}, {"kind": "offmap"})
    s.ring(('poly', _env), 26, 15, ["plain"])
    s.ring(('poly', _env), 20, 40, ["plain"])

# fnn1 + fnn2 - the north band fans flanking the north road (GM 2026-07-23 rollout: the wide frame
# opened bare ground above the moat). Both are fn1-pattern: off-map northern source (the high side
# that also feeds the river), falling S; fnn1 drains off the west frame, fnn2's shallow fall stops
# above the moat's top rim and its drain empties INTO the moat (the storm-drain pattern).
_netn1, ENV_FNN1, _cn1 = comb_field("fnn1", (1050, 608), 100, 41, 150, (120, 160), (75, 105), (0.4, 0.75), avoid=(MOAT,))
_pn1 = plot_centroid(_netn1, lambda cs: min(cs, key=lambda c: c[1]))
topo_channel([(1050, 602), (1050, 608), _pn1], {"kind": "offmap"}, {"kind": "field", "name": "fnn1"})
_drn1 = next(c["pts"] for c in _netn1["channels"] if c["role"] == "drain")
_dfx1, _dfy1 = _drn1[-1]
_mn1 = min(MOAT, key=lambda mp1: (mp1[0] - _dfx1 - 60) ** 2 + (mp1[1] - _dfy1 - 60) ** 2)  # rim SE of the outfall
topo_channel([(_dfx1, _dfy1), (_mn1[0], _mn1[1])], {"kind": "drain"}, {"kind": "moat"}, draw_w=4.0, col="#9CB4C8")  # the culvert mouth (fnn1) merges into the moat water
s.sluice_gate(_dfx1, _dfy1, rot=math.degrees(math.atan2(_mn1[1] - _dfy1, _mn1[0] - _dfx1)) + 90)  # the outfall gate at the drain -> culvert handoff
s.ring(('poly', ENV_FNN1), 24, 15, ["plain"])
s.ring(('poly', ENV_FNN1), 18, 40, ["plain"])
_netn2, ENV_FNN2, _cn2 = comb_field("fnn2", (1750, 608), 95, 42, 75, (110, 150), (60, 85), (0.4, 0.8), avoid=(MOAT,))
_pn2 = plot_centroid(_netn2, lambda cs: min(cs, key=lambda c: c[1]))
topo_channel([(1750, 602), (1750, 608), _pn2], {"kind": "offmap"}, {"kind": "field", "name": "fnn2"})
_drn2 = next(c["pts"] for c in _netn2["channels"] if c["role"] == "drain")
_dfx2, _dfy2 = _drn2[-1]
_mn2 = min(MOAT, key=lambda mp2: (mp2[0] - _dfx2) ** 2 + (mp2[1] - _dfy2 - 90) ** 2)
topo_channel([(_dfx2, _dfy2), (_mn2[0], _mn2[1])], {"kind": "drain"}, {"kind": "moat"}, draw_w=4.0, col="#9CB4C8")  # the culvert mouth merges into the moat water
s.sluice_gate(_dfx2, _dfy2, rot=math.degrees(math.atan2(_mn2[1] - _dfy2, _mn2[0] - _dfx2)) + 90)  # the outfall gate at the drain -> culvert handoff
s.ring(('poly', ENV_FNN2), 22, 15, ["plain"])
s.ring(('poly', ENV_FNN2), 16, 40, ["plain"])
# fne1 - the far-bank fan, tapped STRAIGHT OFF the Hayakawa (the river-fed comb the far bank always
# implied): sluice east of the bank, falling ESE off the east frame; its hem keeps off the estate
# strip below via dry_keepout. The river IS the source (channel anchor kind "river").
_nete1, ENV_FNE1, _ce1 = comb_field("fne1", (2130, 860), 20, 43, 140, (110, 150), (70, 95), (0.4, 0.75), avoid=(MOAT,), dry_keepout=((2160, 1230, 105), (2340, 1120, 115), (2500, 1270, 125)))
_pe1 = plot_centroid(_nete1, lambda cs: min(cs, key=lambda c: c[0]))
topo_channel([(2076, 859), (2130, 860), _pe1], {"kind": "river"}, {"kind": "field", "name": "fne1"})
s.field_channel([(2076, 859), (2130, 860)], '#9CB4C8', 7, 7)  # the visible tap, in the RIVER'S own water color (it carries river water; confluence, not crossing)
s.sluice_gate(2130, 860, rot=90.9)  # the river-intake gate at the seam (tap heading ~ due east)
_dre1 = next(c["pts"] for c in _nete1["channels"] if c["role"] == "drain")
_dfex, _dfey = _dre1[-1]
topo_channel([(_dfex, _dfey), (2560, _dfey - 38)], {"kind": "drain"}, {"kind": "offmap"}, draw_w=4.0)  # runoff off the east frame (gentle ENE bend, no hairpin)
s.ring(('poly', ENV_FNE1), 24, 15, ["plain"])
s.ring(('poly', ENV_FNE1), 18, 40, ["plain"])
# THE DEAD CROSS THE RIVER: the funerary complex on the far bank, DOWNSTREAM (south) of the
# city and south of the bridge road - the polluting death-work kept below the city on the
# current, and bearing the dead over the water suits the geography of the afterlife. (The moat's
# water set-back leaves no dry landward fringe in the cropped view; the far bank's farmland runs
# on east beyond the frame.) Cremation set back >=130px from the bridge road, adjoining the
# external common ground.
# nudged W (and the pyre up) so their labels sit fully inside the right/bottom frame edge while
# the complex stays well clear of the river's east bank
# burial set-back: the Hayakawa is a w40 stream in the manifest, so a BURIAL ground's corners must
# sit >= 20 + 140 = 160px off its centerline (water_setback caps at 140; cremation is exempt at 30).
# The shrunk view pulled the river's centerline to x~2080-2083 here, so cemetery/ossuary sit at
# x>=2290 - west corners ~2245, riverward margin ~162px - while their labels still end < x2391 (view edge)
s.cemetery(2292, 1725, 90, 64, parish=False, label="common burial ground")  # parish=False -> ORGANIC Japan-style plot (settlements.md 'shape of the common ground')
s.cremation_ground(2296, 1804)
s.ossuary(2290, 1650)

s.bridges()
s.farmsteads()
s.farm_wells()  # farm-belt wells: no farmstead >500 real ft from one, map-edge steadings exempt (farm_wells_within_reach)


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
        if not _in_poly(gx, gy, WALL):
            return False  # NO dwelling lands OUTSIDE the wall - commoners per feature 006, and free-standing samurai houses too (city_samurai_houses_inside_walls): the only extramural samurai residences are the walled country ESTATES, placed by hand. The old samurai exemption leaked 1 house past the SW arc here and 14 past Tango's SE arc (2026-07-20)
        if any(abs(gx - cx) <= (cw + w_) / 2 + 15 and abs(gy - cy) <= (ch + h_) / 2 + 15 for cx, cy, cw, ch in civ):
            return False  # ministries/yamen stand-clear margin
        if any((gx - sx) ** 2 + (gy - sy) ** 2 < 85**2 for sx, sy in stab):
            return False  # the caravan stables' open ground
        return not any(
            min(x1_, gx + w_ / 2 + 2) - max(x0_, gx - w_ / 2 - 2) > 0 and min(y1_, gy + h_ / 2 + 2) - max(y0_, gy - h_ / 2 - 2) > 0 for x0_, y0_, x1_, y1_ in labs
        )  # placed label boxes stay readable

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
        if not all(abs(gx - px) >= (w_ + pw) / 2 + 3 or abs(gy - py) >= (h_ + ph) / 2 + 3 for (px, py, pw, ph) in s.placed):
            return False
        # s.placed stores (w,h) UNROTATED, so a street-facing pack house rotated ~45-135 deg
        # reaches past the box the test above clears against (a -137deg samurai's bbox runs
        # ~11.2px from center vs the 6.65 stored) - test the true rotated AABBs too
        for o in s.M["buildings"] + s.M["houses"]:
            if "w" not in o or abs(gx - o["x"]) > 42 or abs(gy - o["y"]) > 42:
                continue
            oth = math.radians(o.get("rot", 0))
            oc, os_ = abs(math.cos(oth)), abs(math.sin(oth))
            if abs(gx - o["x"]) < (w_ + oc * o["w"] + os_ * o["h"]) / 2 + 3 and abs(gy - o["y"]) < (h_ + os_ * o["w"] + oc * o["h"]) / 2 + 3:
                return False
        return True

    def door_clear(gx, gy, rot):
        # outward-facing-doors doctrine (2026-07-18): a gap-fill house still needs an UNBLOCKED
        # entrance. This is the gate's EXACT geometry (check_village city_house_doors_unblocked:
        # the door-probe band vs ROTATED neighbor corners) rather than s.open_face_rot - the
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
            corners = [
                (o["x"] + c_ * dx - sn * dy, o["y"] + sn * dx + c_ * dy) for dx, dy in ((-o["w"] / 2, -o["h"] / 2), (o["w"] / 2, -o["h"] / 2), (o["w"] / 2, o["h"] / 2), (-o["w"] / 2, o["h"] / 2))
            ]
            for d_ in (0.8, dc * 0.55, dc):
                for t_ in (-0.3 * w_, 0.0, 0.3 * w_):
                    if _in_poly(fx + ux * d_ + vx * t_, fy + uy * d_ + vy * t_, corners):
                        return False
        return True

    x0, y0, x1, y1 = region
    for pad in (7, 4, "exact"):  # tighter sweeps only when the padded pass leaves the floor unmet
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
                gx += 5
            gy += 6
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


DWELL = ("laborer", "laborer_large", "servant", "burakumin", "merchant", "merchant_house", "merchant_large", "samurai", "samurai_large")


def _dwell_count():
    # no agricultural district here - a standard city counts URBAN dwellings only (its farmers
    # all live outside; the _inwall farm term is zero and kept only for symmetry with Tango)
    return sum(1 for b in s.M["buildings"] if b["kind"] in DWELL) + sum(1 for h in s.M["houses"] if _inwall(h["x"], h["y"]))


# top_up regions extended to the new ring bed (inset 22 from the 449x418 wall; the corridor's
# own 24px half-width self-limits the sweep) - the shrunk rowpack regions alone deliver ~120
# dwellings short of the budget's 600-dwelling promise, so the fills carry more of the load
# civic aprons, PHASE 2 (see the phase-1 comment at the ministries): the pack is done, so the
# ministry/yamen aprons drop 30 -> 16 and the axis-aligned top_up fills (whose ok() enforces its
# own 15px AABB office gap) may claim the N-fence band and the mansion's flanks.
# REPLACED IN PLACE, index for index: settlement's _poly_bboxes cache invalidates on list-LENGTH
# change only, so a del+append of the same count would leave every later bbox misaligned (dead
# blocks, overlapping houses); in-place substitution keeps the old 30px bboxes as a conservative
# (superset) pre-filter over the new 16px polys, which stays correct.
for _ci, _m in zip(range(_CIV_I0, _CIV_I1), s.M["ministries"] + [s.M["governor_mansion"]], strict=True):
    s.block_polys[_ci] = [
        (_m["x"] - _m["w"] / 2 - 16, _m["y"] - _m["h"] / 2 - 16),
        (_m["x"] + _m["w"] / 2 + 16, _m["y"] - _m["h"] / 2 - 16),
        (_m["x"] + _m["w"] / 2 + 16, _m["y"] + _m["h"] / 2 + 16),
        (_m["x"] - _m["w"] / 2 - 16, _m["y"] + _m["h"] / 2 + 16),
    ]
top_up(
    "samurai_large", (1100, 1315, 1455, 1600), 4
)  # city_samurai_housing_varied wants >=3 LARGE senior-rank houses; the pair-cadence ward pack seats only ~2, so the senior homes are topped up FIRST, while the ward still has large-footprint gaps. Region pulled INSIDE the ward proper: the wider samurai sweep's x1073 west edge is past the SW ring arc, where a large footprint's corner reaches the moat (samurai are wall-exempt in ok(), so nothing else stops it - no_structure_on_moat)
top_up(
    "samurai", (1073, 1309, 1471, 1620), 52, count_kinds=("samurai", "samurai_large")
)  # y1 1620 reaches the pocket S of the yamen, W of the mausoleum apron (the fence diagonal + mausoleum reserve gate the rest)
top_up("merchant_house", (1490, 1345, 1875, 1657), 160, count_kinds=("merchant", "merchant_house", "merchant_large"))
# seat the wealthier 'master' laborers (laborer_large) FIRST, into gaps in the warren, before the
# plain-laborer fill claims that room - ~12.5% of the laborer cohort per budgets.md
top_up("laborer_large", (1491, 923, 1878, 1294), 32)
top_up("laborer", (1491, 923, 1878, 1294), 305, count_kinds=("laborer", "laborer_large"))
top_up("servant", (1490, 1345, 1875, 1657), 90)
top_up(
    "burakumin", (1282, 1626, 1634, 1755), 30
)  # burakumin is a caste FLOOR (~30, city_caste_counts_in_band) - topped up UNCONDITIONALLY here, BEFORE the dwelling-total-capped loop below. Else a reflow that lets the servant/laborer fills reach the 566 cap first starves it: the 2026-07-22 true-scale gate furniture freed N-gate room and did exactly that, dropping burakumin to 20 (the in-loop sweep at the bottom never ran)
for _kind, _region, _cap in (
    ("servant", (1491, 923, 1878, 1294), 130),  # y0 923 (was 969): the warren's top strip against the N ring arc was outside every servant sweep
    ("laborer", (1490, 1345, 1875, 1657), 260),
    ("servant", (1282, 1626, 1630, 1740), 60),
    (
        "burakumin",
        (1282, 1626, 1634, 1755),
        40,
    ),  # y1 1755 (was 1740): the row band itself runs to 1752, so the sweep reaches the last row's gaps - seats lost to the temple-lane shop reflow (2026-07-20) are recovered here within the burakumin band
    ("laborer", (1082, 953, 1462, 1300), 260),  # the NW monzen pockets (west column, theater strips, temple-lane pocket)
    ("servant", (1073, 1309, 1471, 1600), 130),  # attendants' quarters tucked into the samurai ward's slivers (a 10x7 servant hut seats where no samurai house could)
    ("laborer", (1491, 923, 1878, 1294), 305),
    ("servant", (1082, 953, 1462, 1300), 150),
    ("servant", (1634, 1450, 1875, 1676), 170),  # the SE corner E of the S street's end, down to the ring arc
    ("servant", (1490, 1345, 1875, 1657), 150),
):
    _dw = _dwell_count()
    if _dw >= 566:
        break
    top_up(_kind, _region, min(_cap, sum(1 for b in s.M["buildings"] if b["kind"] == _kind) + (566 - _dw)))


for _mx, _my in _ML_SPOTS:
    s.building(_mx, _my, *s._dims("merchant_large"), "merchant_large")

# FINE global well pass (Tango pattern): after every dwelling is placed, drop wells into the
# nearest clear COURT (near=46 gates each to sit among homes, so wellheads land in block
# interiors, not on lanes). This is what carries the well-density + neighborhoods-have-wells
# checks - the coarse per-quarter passes above only reserve the courts.
s.place_wells((1491, 969, 1878, 1294), spacing=42, near=48)  # laborer warren
s.place_wells((1490, 1345, 1875, 1660), spacing=42, near=48)  # merchant district
s.place_wells((1282, 1626, 1634, 1740), spacing=42, near=48)  # downstream burakumin strips
s.place_wells((1082, 950, 1462, 1305), spacing=42, near=48)  # NW monzen terraces (incl. the new theater/ring-front/temple-lane pockets)
# a second offset sweep catches the dense pockets the first grid still leaves over-burdened
s.place_wells((1516, 985, 1869, 1294), spacing=46, near=48)  # laborer warren, offset
s.place_wells((1553, 1357, 1875, 1657), spacing=46, near=48)  # merchant district, offset
s.place_wells((1094, 962, 1450, 1298), spacing=46, near=48)  # NW monzen, offset

# ===== NEAR-RING FARMLAND: the extramural flat ground reads PACKED (feature 013) =====
# Nagahara is a well-sited provincial seat, so the flat ground just outside the wall is intensively
# worked. Fill the extramural band (inside the cropped view) with a quilt of dry/garden plots between
# the paddy fans - no water needed. near_ring_cropland auto-skips everything inside the wall, the fans,
# structures, estates, graves, the river, and the moat. Called last, after every structure + top-up.
# Default near_ring_density "dense". WHY: settlements.md "Near-ring farmland density".
# NEAR-RING PADDY IS COMB FIELDS ONLY (GM 2026-07-23, the Tango-recipe rollout). The ring's rice is
# the MOAT_FARMS combs + the river-fed far-bank fan - real irrigation deltas, the same paddy form as
# every village. REJECTED (recorded so it is never reinvented): the near_ring_cropland dry/garden tile
# quilt and near_ring_paddy's gridded square basins ("don't look like any rice paddy in any village or
# hamlet"). Coverage need not be total - the visible fans + open ground read as the head of paddy
# country continuing beyond the frame.

s.crop_city(west=100)  # the aggressive default (35px past the kept satellites: N gate market, far-bank
# funerary S/E, wharf); the WEST keeps a 100px farm band (no satellite anchors that flank and the GM
# called the left framing good).
s.title("Nagahara")

HERE = os.path.dirname(os.path.abspath(__file__))
nb = {}
for b in s.M["buildings"]:
    nb[b["kind"]] = nb.get(b["kind"], 0) + 1
print("farmhouses:", len(s.M["houses"]), "| buildings:", nb, "| total urban:", sum(nb.values()), "| estates:", len(s.M["manors"]), "| finish:", s.finish(os.path.join(HERE, "nagahara")))
