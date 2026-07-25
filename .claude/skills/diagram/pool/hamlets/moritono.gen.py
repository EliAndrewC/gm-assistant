#!/usr/bin/env python3
"""Moritono ("forest gate") - a HAMLET beside the Shirin Forest, the to-scale bundle at 1 ft/px.

A small outlying farming hamlet (~16 households) under the Shirin Forest, redone under the water-first
to-scale rules (like Ikegami). What makes it a hamlet, not a village: NO headman of its own (it falls
under the village-district headman), NO village shrine, NO tax-free plot - a bare cluster of farms.

Its two DISTINCTIVE features survive the rebuild: the **Shirin Forest** filling the EAST (the high, wooded
ground), and the county magistrate's walled **hunting lodge** at the forest's edge - a samurai estate
ADJACENT to the hamlet, not part of it. WATER FLOWS EAST -> WEST: the land falls E(high, forest) -> W(low).
A brook out of the forest feeds a TAMEIKE reservoir (a source pond) at the field's E head; the comb supply
net distributes the water WESTWARD across the paddies; the field drains at its low W foot into a valley
brook off-map, and the un-reclaimed low toe is reed marsh.

SCALE: a hamlet is drawn at 1 ft/px (ftpx=1); the to-scale homestead bundle carries dims in FEET.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, SKILL)
from settlement import Settlement  # noqa: E402
import math  # noqa: E402
import random as _random  # noqa: E402

from waterfields import AZE, BEAN_GREEN, aze_w, build_comb  # noqa: E402

W, H = 2600, 1500                     # wide: the E-high(forest) -> W-low valley, water flowing E -> W
SEED = 44
FTPX = 1
POND = (1700, 800, 92, 58)            # cx, cy, rx, ry - the tameike at the E head (source), fed by the forest brook
SLUICE = (POND[0] - POND[2] + 8, POND[1] + 6)   # the single outlet on the pond's downhill (W) foot

s = Settlement(W=W, H=H, seed=SEED)
s.meta(
    water_flow=135,  # DRAINAGE BEARING: where this landscape sends its water (0=E, 90=S)
name="Moritono", scale="hamlet", ftpx=FTPX, toscale=True, households=16, down_deg=180,   # E-high -> downhill = due W
       nucleated=True, field_footbridges=True)   # pond_role defaults to "source" (the tameike FEEDS the field)

# Comb supply net marching due W from the head sluice; field_fall caps the paddy to ~16 households, bounded
# in-frame with a low-side (W) margin for the drain outfall + marsh, and the E head clear for the pond.
net = build_comb(W, H, SLUICE, SEED, down_deg=180, field_fall=1060,
                 offtakes_a=(0.30, 0.66), offtakes_b=(),          # a SPARSE delivery net for a small field
                 dry_keepout=[(POND[0], POND[1], POND[2] + 45)])   # the upslope dry hatake must not grow over the pond
s.meta(dry_furrows_vary=net["furrows_vary"])

s.field_polys.append([(round(x, 1), round(y, 1)) for x, y in net["envelope"]])
s.comb_base_fill(net, "moritono-paddies")   # field floor: no bare parchment at the canal junctions (paddy_fan_has_floor)
for _dp in net["dry_plots"]:
    s.block_polys.append(_dp["poly"])
s._nucleated = True


def furrows(poly, color, theta):
    """Stylised ridge/furrow lines within a dry-field plot (dry crops are row-cultivated)."""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    diag = math.hypot(max(xs) - min(xs), max(ys) - min(ys))
    dx, dy = math.cos(theta), math.sin(theta)
    nx, ny = -dy, dx
    cid = s._cid("dry")
    pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in poly)
    g = [f'<clipPath id="{cid}"><polygon points="{pts}"/></clipPath>', f'<g clip-path="url(#{cid})">']
    t = -diag / 2
    while t <= diag / 2:
        mx, my = cx + nx * t, cy + ny * t
        g.append(f'<line x1="{mx-dx*diag/2:.1f}" y1="{my-dy*diag/2:.1f}" '
                 f'x2="{mx+dx*diag/2:.1f}" y2="{my+dy*diag/2:.1f}" stroke="{color}" stroke-width="0.8" opacity="0.8"/>')
        t += 5
    g.append('</g>')
    s.add(''.join(g))


# DRY FIELDS (the upslope E hem), then paddies over the water
for p in net["dry_plots"]:
    pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in p["poly"])
    s.add(f'<polygon points="{pts}" fill="{p["fill"]}" stroke="#A98C58" stroke-width="1.4" stroke-linejoin="round"/>')
    furrows(p["poly"], p["furrow"], p["theta"])
    s.M["dry_plots"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in p["poly"]],
                             "crop": p["crop"], "theta": round(p["theta"], 3)})
for p in net["plots"]:
    pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in p["poly"])
    s.add(f'<polygon points="{pts}" fill="{p["fill"]}" stroke="{AZE}" stroke-width="{aze_w(s.ftpx):.2f}" stroke-linejoin="round"/>')

s.bund_junctions(net["plots"], "moritono-paddies")  # pile earth into every bund CROSSING (see Settlement.bund_junctions)
beads = ''.join(f'<circle cx="{x}" cy="{y}" r="1.4" fill="{BEAN_GREEN}"/>' for x, y in net["bund_beans"])
s.add(f'<g opacity="0.85">{beads}</g>')

# THE FOREST BROOK: a natural brook out of the Shirin Forest (off-map E, through the wood) that feeds the pond -
# the water source comes from the high wooded ground, not from nowhere. frm=forest (a source) -> to=pond. Drawn
# BEFORE the pond so the pond covers the junction. Runs in from the E, S of the manor, to the pond's E rim.
pcx, pcy, prx, pry = POND
s.stream([(W, 852), (2320, 842), (2080, 826), (1900, 814), (pcx + prx - 6, pcy + 2)],
         frm={"kind": "offmap"}, to={"kind": "pond"}, width=7)
s.pond(pcx, pcy, prx, pry)

# a reedy fringe rims the tameike shore (a reservoir in the hill/forest catchment)
_ring = [(pcx + (prx + 40) * math.cos(a), pcy + (pry + 40) * math.sin(a)) for a in [i * math.pi / 8 for i in range(16)]]
s.marsh(_ring, role="pond_fringe")

# the water network: head-race + supply canals + drain, marching W; the head-race's sluice end snaps onto the pond rim
for c in sorted(net["channels"], key=lambda c: -c["w"]):
    s.field_channel(c["pts"], '#7C9EB0' if c["role"] == "drain" else '#6C9CBE', c["w"], c.get("w_tail", c["w"]))

# the drain's OUTFALL empties into a valley BROOK carrying the runoff off-map DOWNHILL to the W (water OUT,
# mirroring the forest brook = water IN), present because the field's low W corner sits inside the frame.
if net["brook"]:
    s.stream(net["brook"], frm={"kind": "drain"}, to={"kind": "offmap"}, width=8)

# manifest: field envelope + ditches, for the checks
_env = [[round(x, 1), round(y, 1)] for x, y in net["envelope"]]
_exs = [p[0] for p in _env]
_eys = [p[1] for p in _env]
_pvx = [v[0] for p in net["plots"] for v in p["poly"]]
_pvy = [v[1] for p in net["plots"] for v in p["poly"]]
s.M["fields"].append({"name": "moritono-paddies", "kind": "paddy", "outline": _env,
                      "bbox": [min(_exs), min(_eys), max(_exs), max(_eys)],
                      "vis_bbox": [min(_pvx), min(_pvy), max(_pvx), max(_pvy)]})
for c in net["channels"]:
    s.M["field_ditches"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in c["pts"]],
                                 "role": c["role"], "field": "moritono-paddies",
                                 "w": round(c["w"], 1), "w_tail": round(c.get("w_tail", c["w"]), 1)})
# the pond->field FEED anchor (SOURCE): NOT drawn - the visible supply is the pond + head-race. This thin hairline
# channel carries the frm/to topology so the pond is recorded as feeding the field: it starts at the sluice (on
# the pond's W foot) and winds gently down-slope INTO the paddy interior, giving fields_show_water_source its
# channel and field_ditches_reach_source_and_sink its pond SOURCE. Interior end computed from the head-race fork.
_hr = net["channels"][0]["pts"]
_fork = _hr[-1]
_din = (_fork[0] - 70 * math.cos(math.radians(20)), _fork[1] - 70 * math.sin(math.radians(20)))
_mid = ((SLUICE[0] + _din[0]) / 2 - 4, (SLUICE[1] + _din[1]) / 2 + 20)
s.M["channels"].append({"poly": [[round(SLUICE[0], 1), round(SLUICE[1], 1)],
                                 [round(_mid[0], 1), round(_mid[1], 1)], [round(_din[0], 1), round(_din[1], 1)]],
                        "frm": {"kind": "pond"}, "to": {"kind": "field", "name": "moritono-paddies"}, "w": 2.5})

# THE SHIRIN FOREST fills the EAST behind an irregular tree-line (the high wooded ground). Blocks houses; it is
# the hamlet's woodland - so no separate managed-woodland patches are needed, the forest IS the wood. Drawn as a
# stand of individual trees at true canopy density (settlement._tree_stand), with a fringe of advance growth
# thinning out onto the scrub, so the wood's edge is made of trees rather than a ruled line. The frame reveals
# only ~110 ft of canopy past the tree line (FOREST_REVEAL_FT) - enough to read as a wood running off the map.
s.forest([(2262, -10), (2238, 118), (2276, 246), (2222, 372), (2258, 498), (2214, 624), (2270, 746),
          (2226, 874), (2278, 1002), (2232, 1128), (2264, 1256), (2224, 1384), (2270, 1510)],
         label="Shirin Forest", label_xy=(2320, 700))

# THE MAGISTRATE'S MANOR - a walled hunting lodge at the forest's edge, gate facing WEST toward the hamlet it
# oversees. A samurai estate ADJACENT to the hamlet, not part of it (only walls + gate + court; its interior is
# its own Mode A diagram).
s.manor(2070, 470, 240, 300, "Magistrate's Manor", "hunting lodge by the Shirin Forest", gate_dir="west")

# FARMHOUSES: a small nucleated cluster on the N margin of the field (clear of the E manor/pond/forest), the
# paddy fanning W below it toward the drain + marsh. NO HEADMAN - a hamlet's overseer lives in the main village.
# LANES first (no-build corridors the homesteads front): a short spine, a spur S to the paddy edge, and a
# connector track running OFF the W edge (down-valley to the district / road, away from the manor).
_rng = _random.Random(SEED + 1)
CX, CY = 950, 360
s.lane([(CX - 150, CY - 4), (CX - 30, CY + 8), (CX + 90, CY + 4), (CX + 210, CY + 12)], width=5, clearance=32, worn=True)
_fp = s._nearest_field_point(CX, CY + 150)
s.lane([(CX - 10, CY + 4), ((CX + _fp[0]) / 2 - 4, (CY + 4 + _fp[1]) / 2 + 8), (_fp[0] + 2, _fp[1] - 6)],
       width=5, clearance=32, worn=True)
s.lane([(CX - 150, CY - 4), (CX - 360, CY + 40), (CX - 700, CY + 96), (CX - 1050, CY + 150)],
       width=6, clearance=32, worn=True, connector=True)   # runs off the W edge to the wider world

_placed = 0
for _ in range(150):
    if _placed >= 16:
        break
    _a = _rng.uniform(0, 2 * math.pi)
    _rad = _rng.random() ** 0.5
    _x = CX + math.cos(_a) * _rad * 220
    _y = CY + math.sin(_a) * _rad * 120
    if s.try_place(_x, _y, "plain"):
        _placed += 1
n_farms = s.farmsteads()
print(f"farmhouses: {n_farms}")

# COMMUNAL WELLS + shared draft-animal BYRES among the dwellings.
s.place_wells((CX - 210, CY - 110, CX + 210, CY + 120), spacing=190, near=130)
n_byres = s.draft_byres(fraction=0.22, gap=60)
print(f"byres: {len(n_byres)}")

# HINTERLAND - the non-arable land: a reed MARSH at the low downhill (W) TOE (the un-reclaimed valley foot around
# the drain outfall) and the cut-over SCRUB commons filling the surrounding margins (China-first: mostly denuded
# scrub). The Shirin FOREST is the E woodland, so no separate coppice patches. Scatter skips fields/pond/lanes/
# houses/forest/manor + a hamlet keep-out, and bleeds off-frame so the crop stays tight. The scatter fills the E
# rough ground too (around the manor + between the pond and the forest), skipping the forest/manor/pond blocks.
s.hinterland()

# WINDBREAK - the communal fengshui wood (风水林) on the high/windward back of the cluster, plus a leafy
# copse among the homes. The belt is an L wrapping BOTH windward faces - a deep band across the N back
# and a shorter arm down the W flank - because the winter monsoon comes out of the NW (the `windward`
# default), so a north-only band leaves the west flank bare. Two sizing rules, both learned the hard way
# (GM 2026-07-25, when this belt read as three blobs behind 16 farmhouses):
#   1. SET BACK off the homesteads. The old outline ran its inner edge through the northern house row, so
#      most of the clumps it could have grown were rejected as landing on a house/yard/garden. The stand
#      grows BEHIND the houses (~45 ft clear), not among them - the copse is what fills the inner gaps.
#   2. DEEP enough for several clump rows. At ~30 ft the old band held ONE row of crowns; the belt wants
#      ~80-120 ft so the canopies overlap into a wall. Sized here to ~0.5 ha of footprint, in the band the
#      other 16-household hamlets sit in (Enokida 0.45 ha, Kuwabata 0.39) and under the research figure
#      for a modest back grove (<1 ha - settlements.md 'Village windbreak'). village_windbreak_scales_
#      with_cluster now gates this: canopy area >= 0.40x the roof area it shelters.
# The two communal WELLS stand inside the band and carve their own clearings out of it (village_grove
# keeps canopy off a wellhead), which is how a real draw-point sits in a back grove.
_hx0 = min(h["x"] - h["w"] / 2 for h in s.M["houses"])
_hx1 = max(h["x"] + h["w"] / 2 for h in s.M["houses"])
_hy0 = min(h["y"] - h["h"] / 2 for h in s.M["houses"])
_hy1 = max(h["y"] + h["h"] / 2 for h in s.M["houses"])


def _rag(pts, amp=11):
    return [(x + _rng.uniform(-amp, amp), y + _rng.uniform(-amp, amp)) for x, y in pts]


def _densify(pts, step=70):
    """Walk the outline dropping intermediate vertices, so _rag has enough points to make the edge ragged
    (a 6-vertex L jittered at its corners alone still reads as a ruled rectangle)."""
    out = []
    for i, p in enumerate(pts):
        q = pts[(i + 1) % len(pts)]
        n = max(1, int(math.hypot(q[0] - p[0], q[1] - p[1]) / step))
        out += [(p[0] + (q[0] - p[0]) * k / n, p[1] + (q[1] - p[1]) * k / n) for k in range(n)]
    return out


# the L: N band (y: -125..-45 off the top houses) + W arm (x: -115..-30 off the west houses), the arm
# stopping short of the connector lane's keep-out so no clump is dropped onto the track.
_belt = [(_hx0 - 115, _hy0 - 125), (_hx1 + 35, _hy0 - 125), (_hx1 + 35, _hy0 - 45),
         (_hx0 - 30, _hy0 - 45), (_hx0 - 30, _hy0 + 75), (_hx0 - 115, _hy0 + 75)]
s.village_grove(_rag(_densify(_belt)), role="windbreak")
# the dooryard copse fills the OPEN gaps among + around the homesteads (its scatter skips every building,
# yard, garden and lane), so it spans the cluster's full footprint rather than the house-center box.
_scatter = [(_hx0 - 40, _hy0 - 40), (_hx1 + 40, _hy0 - 40), (_hx1 + 40, _hy1 + 40), (_hx0 - 40, _hy1 + 40)]
s.village_grove(_scatter, role="copse", dense=False)

# PLANK FOOTBRIDGES across the irrigation ditches
n_bridges = s.channel_footbridges(spacing=300)
print(f"footbridges: {n_bridges}")

# THE OFFICIAL NOTICE BOARD (kosatsuba), auto-sited on a lane verge at the busiest node (GM
# 2026-07-24: every settlement tier posts the state's standing law - the ofuregaki reached the
# peasantry through this board via the settlement's literate reader; see settlements.md and
# settlement.place_kosatsuba). Placed BEFORE the crop so the frame contains it.
s.place_kosatsuba()
s.crop_to_content(margin=30)

# NO SHRINE, NO GRAVEYARD, NO TAX-FREE plots - a hamlet is a bare cluster of farms under a distant headman.

_ACRES = sum(abs(sum(p["poly"][i][0] * p["poly"][(i + 1) % len(p["poly"])][1]
                     - p["poly"][(i + 1) % len(p["poly"])][0] * p["poly"][i][1]
                     for i in range(len(p["poly"])))) / 2 for p in net["plots"]) * FTPX * FTPX / 43560

s.title("Moritono")
print(s.finish(os.path.join(HERE, "moritono")))
print(f"paddy acres (at {FTPX} ft/px): {_ACRES:.1f}  plots: {len(net['plots'])}  households: {n_farms}")
