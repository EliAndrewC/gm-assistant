#!/usr/bin/env python3
"""Ueda ("upper paddy") - the first regular-village variant on the Hoshigaoka foundation.

Same single-field nucleated form as Hoshigaoka, but flowing NE-high -> SW-low (down_deg=135) for variance
(Hoshigaoka is NW-high). It also exercises the RANDOMIZED POPULATION: village_population() draws from the
~200-500 distribution (mode 350) off the map seed - SEED=3 draws 300 inhabitants (~60 households), so the
paddy, pond, and cluster are all sized DOWN from Hoshigaoka's 350. A NE->SW field grows down-and-left, so the
frame is TALLER than Hoshigaoka's landscape one (the SW toe needs the height). The NE valley-head pond is
drawn nudged W (flush with the dry-field strip) so it does not poke past the crop on the E; its N poke is the
intrinsic cost of a valley-head reservoir, which the crop advisory now exempts automatically (a field-sourcing
pond is hydrologically anchored). Where its head-race + inflow brook meet the pond, they are CLIPPED to the
pond edge so they JOIN the water at its rim instead of being drawn over it.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, SKILL)
from settlement import Settlement, village_population  # noqa: E402
import math      # noqa: E402
import random    # noqa: E402

from waterfields import BEAN_GREEN, BUND, build_comb  # noqa: E402

SEED = 3
POP = village_population(random.Random(SEED))        # 300 for SEED=3 (drawn from the 200-500, mode-350 distribution)
HOUSEHOLDS = round(POP / 5)                           # 60 (the "dwellings x5" rule)
FIELD_FALL = round(POP * 3.83)                        # ~1150; caps the SW march so paddy ~ POP*0.22 acres (~65 ac)

# a NE->SW field grows down-and-LEFT, so the frame is TALL (the SW toe needs the height); sized to hold the
# whole field + village + the low-side margin for the drain's outfall + brook.
W, H = 2200, 1900
PRX, PRY = round(145 * math.sqrt(POP / 350)), round(92 * math.sqrt(POP / 350))   # pond area scales with paddy area
POND = (W - 420, 210, PRX, PRY)                       # the NE valley-head ANCHOR: fixes the SLUICE + drives build_comb
SLUICE = (POND[0] - round(0.64 * PRX), POND[1] + round(0.78 * PRY))   # the single outlet on the pond's downhill foot
# The DRAWN pond is nudged ~157px WEST so its east edge sits flush with the dry-field strip - reclaiming the
# ~157px it used to poke past the crop (crop advisory). It STILL CONTAINS the sluice, so it feeds the field
# head exactly as before: the field, comb, and feed-anchor are untouched; only the pond glyph + its brook /
# fringe shift. A valley-head reservoir sitting right at the field head - hydrology stays sensible.
POND_DRAW = (POND[0] - 157, POND[1], PRX, PRY)

s = Settlement(W=W, H=H, seed=SEED)
s.meta(name="Ueda", scale="village", ftpx=2, households=HOUSEHOLDS, down_deg=135,   # NE-high -> downhill = SW (135 deg)
       nucleated=True, field_footbridges=True)
# (The pond is a valley-head reservoir feeding the field, so the crop advisory now exempts it automatically -
# no meta(crop_advisory=False) needed. It is drawn nudged W so its E edge is flush with the fields.)
print(f"Ueda: population {POP}, households {HOUSEHOLDS}, field_fall {FIELD_FALL}")

net = build_comb(W, H, SLUICE, SEED, down_deg=135, field_fall=FIELD_FALL,
                 offtakes_a=(0.25, 0.55, 0.82), offtakes_b=(0.6,),
                 dry_keepout=[(POND[0], POND[1], POND[2] + 45)])
s.meta(dry_furrows_vary=net["furrows_vary"])   # gentle valley -> dry furrows FAN

s.field_polys.append([(round(x, 1), round(y, 1)) for x, y in net["envelope"]])
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
    g = [f'<clipPath id="{cid}"><polygon points="{pts}"/></clipPath>',
         f'<g clip-path="url(#{cid})">']
    t = -diag / 2
    while t <= diag / 2:
        mx, my = cx + nx * t, cy + ny * t
        g.append(f'<line x1="{mx-dx*diag/2:.1f}" y1="{my-dy*diag/2:.1f}" '
                 f'x2="{mx+dx*diag/2:.1f}" y2="{my+dy*diag/2:.1f}" '
                 f'stroke="{color}" stroke-width="0.8" opacity="0.8"/>')
        t += 5
    g.append('</g>')
    s.add(''.join(g))


# DRY FIELDS first (upslope margin), then paddies over the water
for p in net["dry_plots"]:
    pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in p["poly"])
    s.add(f'<polygon points="{pts}" fill="{p["fill"]}" stroke="#A98C58" '
          f'stroke-width="1.4" stroke-linejoin="round"/>')
    furrows(p["poly"], p["furrow"], p["theta"])
    s.M["dry_plots"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in p["poly"]],
                             "crop": p["crop"], "theta": round(p["theta"], 3)})

for p in net["plots"]:
    pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in p["poly"])
    s.add(f'<polygon points="{pts}" fill="{p["fill"]}" stroke="{BUND}" '
          f'stroke-width="2" stroke-linejoin="round"/>')

beads = ''.join(f'<circle cx="{x}" cy="{y}" r="1.4" fill="{BEAN_GREEN}"/>'
                for x, y in net["bund_beans"])
s.add(f'<g opacity="0.85">{beads}</g>')

# REED MARSH on the low S/SW toe: below the paddy's drainage line + the genuinely low bottom-left corner
# (s.marsh skips paddy, so the reeds ABUT the field's low edge and only fill the wet ground beyond)
s.marsh([(150, 1900), (1520, 1900), (1430, 1640), (880, 1560), (360, 1640), (150, 1770)])

# the pond's FEEDER: a brook flowing IN from the top edge into the pond (drawn BEFORE the pond)
pcx, pcy, prx, pry = POND_DRAW
s.stream([(pcx + 24, -12), (pcx + 14, 70), (pcx - 6, pcy - pry + 18)],
         frm={"kind": "offmap"}, to={"kind": "pond"}, width=9)
s.pond(pcx, pcy, prx, pry)

# AROUND THE POND: a reedy fringe (the reservoir's wet margin). Its NE catchment hill is now past the tighter
# crop edge, so it is left implied by the fringe + the inflow brook rather than drawn as a clipped sliver.
_ring = [(pcx + (prx + 58) * math.cos(a), pcy + (pry + 58) * math.sin(a)) for a in [i * math.pi / 8 for i in range(16)]]
s.marsh(_ring, role="pond_fringe")


# the comb channels go THROUGH the water block (s.field_channel) so they JOIN the pond + each other cleanly:
# each bed sits in the shared water group over the pond's rim edge, and the sluice end is snapped onto the rim.
for c in sorted(net["channels"], key=lambda c: -c["w"]):
    s.field_channel(c["pts"], '#7C9EB0' if c["role"] == "drain" else '#6C9CBE',
                    c["w"], c.get("w_tail", c["w"]))

if net["brook"]:
    s.stream(net["brook"], frm={"kind": "drain"}, to={"kind": "offmap"}, width=9)

# manifest: the field envelope + watercourses, for the checks. vis_bbox = the drawn paddy plots (the envelope
# has an invisible tail past the last plot used only for house-blocking).
_env = [[round(x, 1), round(y, 1)] for x, y in net["envelope"]]
_exs = [p[0] for p in _env]
_eys = [p[1] for p in _env]
_pvx = [v[0] for p in net["plots"] for v in p["poly"]]
_pvy = [v[1] for p in net["plots"] for v in p["poly"]]
s.M["fields"].append({"name": "ueda-paddies", "kind": "paddy", "outline": _env,
                      "bbox": [min(_exs), min(_eys), max(_exs), max(_eys)],
                      "vis_bbox": [min(_pvx), min(_pvy), max(_pvx), max(_pvy)]})
for c in net["channels"]:
    s.M["field_ditches"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in c["pts"]],
                                 "role": c["role"], "field": "ueda-paddies",
                                 "w": round(c["w"], 1), "w_tail": round(c.get("w_tail", c["w"]), 1)})
# pond->field FEED anchor for field_ditches_reach_source_and_sink (water IN; the brook is the SINK, water OUT).
# Not drawn - carries the frm/to topology; winds from the sluice INTO the paddy along the fall (down_deg=135).
_hr = net["channels"][0]["pts"]
_fork = _hr[-1]
_din = (_fork[0] + 70 * math.cos(math.radians(135)), _fork[1] + 70 * math.sin(math.radians(135)))
_mid = ((SLUICE[0] + _din[0]) / 2 + 12, (SLUICE[1] + _din[1]) / 2 + 12)
s.M["channels"].append({"poly": [[round(SLUICE[0], 1), round(SLUICE[1], 1)],
                                 [round(_mid[0], 1), round(_mid[1], 1)],
                                 [round(_din[0], 1), round(_din[1], 1)]],
                        "frm": {"kind": "pond"}, "to": {"kind": "field", "name": "ueda-paddies"}, "w": 2.5})

# ===== STAGE 2: the NUCLEATED CLUSTER. Ueda = "UPPER PADDY" - the village's paddies are the UPPER (upslope)
# ones, so the dwellings sit DOWNSLOPE of them, facing up-valley toward the fields. On the NE-high slope that
# puts the cluster on the LOWER (SW) flank, hugging the field's SW-west edge, well above the marsh; the bulk of
# the paddy rises above it to the NE. (Name-informed siting - see settlements.md.) =====
_rng = random.Random(SEED + 1)
CX, CY = 790, 1030                   # cluster center on the LOWER/SW flank, downslope of the upper paddies

# LANES go down BEFORE the houses (a lane lays a no-build corridor the homesteads FRONT). A main ~N-S spine
# through the cluster, a spur E to the paddy edge (stops at the field - no lane runs through the paddy), and a
# connector track running OFF-map: it heads W (up the valley side toward the district road), ABOVE the SW marsh.
# the spine runs along the cluster's WEST side, so the homesteads pack EAST of it toward the field (the solver
# hugs each house to the nearest paddy bund; a spine down the middle would catch the houses it pulls east).
s.lane([(CX - 78, CY - 205), (CX - 66, CY - 65), (CX - 78, CY + 85), (CX - 68, CY + 235)],
       width=5, clearance=18, worn=True)
_fp = s._nearest_field_point(CX + 190, CY - 30)
s.lane([(CX - 40, CY - 25), ((CX + _fp[0]) / 2 + 4, (CY - 25 + _fp[1]) / 2 - 4), (_fp[0] - 6, _fp[1] + 2)],
       width=5, clearance=18, worn=True)
s.lane([(CX - 68, CY + 235), (CX - 340, CY + 310), (CX - 610, CY + 380), (CX - 870, CY + 420)],
       width=6, clearance=18, worn=True, connector=True)   # runs W OFF the left edge (x<0), above the SW marsh

s.headman(CX + 46, CY - 150)         # the largest homestead, fronting the head of the main spine
_placed = 1
for _ in range(220):
    if _placed >= HOUSEHOLDS:
        break
    _a = _rng.uniform(0, 2 * math.pi)
    _rad = _rng.random() ** 0.5
    _x = CX + math.cos(_a) * _rad * 155   # a concentrated disk; the bundle solver then hugs each homestead to
    _y = CY + math.sin(_a) * _rad * 240   # the nearest paddy bund and packs it against its neighbors
    if s.try_place(_x, _y, "plain"):
        _placed += 1
n_farms = s.farmsteads()
print(f"farmhouses: {n_farms}")

# house-cluster extents, reused below for the shrine, wells, grove, and graveyard siting.
_hx = [h["x"] for h in s.M["houses"]]
_hy = [h["y"] for h in s.M["houses"]]
_minx, _maxx, _miny, _maxy = min(_hx), max(_hx), min(_hy), max(_hy)
_ccx, _ccy = sum(_hx) / len(_hx), sum(_hy) / len(_hy)

# The VILLAGE SHRINE goes at the SW WATER-MOUTH (the feng-shui exit where the connector leaves and the drain
# runs to the marsh). Placed BEFORE the WELLS (so a well is never scattered onto the hall / under the torii -
# wells_clear_of_shrine_and_torii) AND before the grove (so the water-mouth wood grows a CLEARING around the
# hall + torii - shrine_clear_of_grove_trees / torii_clear_of_grove_trees). Small earth-god shrine
# (~30x24 px ~ 275 m2), no label, torii facing the village (N). graveyard=False (kegare).
s.shrine_hall(_minx + 30, _maxy + 58, "", w=30, h=24, kind="shrine", primary=True,
              torii=[(_minx + 30, _maxy + 20)], graveyard=False)

# ===== STAGE 4a: COMMUNAL WELLS + DRAFT-ANIMAL BYRES among the FINAL houses (after the shrine so they clear it,
# before the grove so it skips them). Wells one per ~20-25 households; byres ~one per 4-5 households. =====
s.place_wells((_minx - 12, _miny - 12, _maxx + 12, _maxy + 12), spacing=180, near=150)
s.draft_byres(fraction=0.2, gap=70)
# the set-apart shrine (south of the cluster) keeps its OWN ablution well beside it, clear of the hall + torii.
s.shrine_well(_minx + 30, _maxy + 58)

# ===== STAGE 3a: the VILLAGE WINDBREAK (fengshui 风水林) - a COMMUNAL grove. The cluster hugs the field on its
# E, so the OPEN face is E and the DENSE wood sits on the W BACK (belt), wrapping the NW/SW corners; a water-
# mouth cluster guards the low SW exit (where the connector leaves + water drains to the marsh); a copse
# scatter fills the gaps among the houses. See settlements.md 'Village windbreak'. =====


def _rag(pts, amp=13):
    """Jitter polygon vertices so an outline reads as ragged, terrain-following woodland, not a ruled wall."""
    return [(x + _rng.uniform(-amp, amp), y + _rng.uniform(-amp, amp)) for x, y in pts]


def _interp(pts, n):
    """Resample a polyline to n points (linear), so an offset band curve stays smooth, not angular."""
    segs = len(pts) - 1
    out = []
    for i in range(n):
        t = i * segs / (n - 1)
        k = min(int(t), segs - 1)
        ax, ay = pts[k]
        bx, by = pts[k + 1]
        f = t - k
        out.append((ax + (bx - ax) * f, ay + (by - ay) * f))
    return out


# back-grove crescent on the W back (deepest in the middle, horns wrapping the NW + SW corners); inner edge
# hugs the houses (clump-skipping keeps it off them), outer edge bulges ~95 px west.
_belt_inner = [(_ccx - 30, _miny - 20), (_minx - 6, _miny + 34), (_minx - 14, _ccy),
               (_minx - 6, _maxy - 34), (_ccx - 30, _maxy + 20)]
_belt_outer = [(_ccx - 58, _maxy + 58), (_minx - 74, _maxy - 22), (_minx - 100, _ccy),
               (_minx - 74, _miny + 22), (_ccx - 58, _miny - 58)]
# FUEL-AND-FODDER COMMONS behind the grove (drawn FIRST, UNDER the forest for a seamless abut): a ragged band
# paralleling the grove's back out onto the far windward slope. Toposequence: village -> back-grove -> commons.
_arc = _interp(_belt_outer, 11)
_com_inner = [(x + 16, y) for x, y in _arc]
_com_outer = [(max(16, x - _rng.uniform(96, 150)), y + _rng.uniform(-16, 16)) for x, y in _arc]
s.commons(_com_inner + list(reversed(_com_outer)))

s.village_grove(_rag(_belt_inner) + _rag(_belt_outer), role="windbreak")   # (1) the back-village belt
# (2) water-mouth cluster at the low SW exit (by the connector track + the drain toward the marsh)
_wmx, _wmy = _minx + 30, _maxy + 58
_wm = [(_wmx + 58 * math.cos(a), _wmy + 44 * math.sin(a)) for a in [i * math.pi / 3 for i in range(6)]]
s.village_grove(_rag(_wm), role="water_mouth")
# (3) leafy scatter: bamboo + dooryard fruit filling the OPEN gaps among the houses
_scatter = [(_minx - 18, _miny - 18), (_maxx + 18, _miny - 18), (_maxx + 18, _maxy + 18), (_minx - 18, _maxy + 18)]
s.village_grove(_scatter, role="copse", dense=False)

# ===== STAGE 3b: the SATOYAMA GRAZING MARGINS - the "empty" DRY high edges are un-terraced grass/scrub hill-
# grazing (role='grazing', exempt from commons_beyond_the_windbreak), filling the ring around the cultivated
# valley. Held OFF the crops (commons auto-skips the paddy; kept left of the field / above the dry-field tops).
# The big UPPER-LEFT (NW) above and left of the field is the up-valley grass head; it joins the NE pond-
# catchment across the field's top. Draw order: AFTER farmhouses + grove, BEFORE the (later) graveyard + shrine.
s.commons([(150, 110), (1080, 110), (980, 360), (740, 540), (430, 600), (150, 430)], role="grazing")     # NW upper grass head
s.commons([(120, 540), (480, 560), (450, 1050), (380, 1420), (120, 1500)], role="grazing")              # W/SW back-slope, down to the marsh
# A FEW managed-WOODLAND patches (coppice / bamboo "economic forest") on the high NW grass head above the paddy -
# the green EXCEPTION amid the cut-over grass (China-first: the hills are mostly denuded scrub, a little managed
# wood). Within the grass-head scrub, set back above the crops. Crowns draw on top of the scrub.
s.commons([(600, 140), (840, 140), (840, 300), (600, 300)], role="woodland")
s.commons([(890, 155), (1065, 155), (1065, 320), (890, 320)], role="woodland")

# ===== STAGE 4b: plank FOOTBRIDGES across the irrigation ditches (standalone, where field-workers cross while
# walking the bunds - NOT tied to any lane). Every long ditch stretch gets one about midway.
n_bridges = s.channel_footbridges(spacing=320)
print(f"footbridges: {n_bridges}")

# ===== STAGE 4d: the VILLAGE GRAVEYARD in the SHRINE's PRECINCT (its Shinsei monk performs the funerary rites,
# so the burial ground is the shrine's churchyard - village_graveyard_by_shrine). It sits in the clear ground
# SW of the water-mouth shrine, off the sacred hall + torii (cemetery_clear_of_shrine), south of the grove and
# north of the marsh, well clear of the far-E field. An organic (unsurveyed) earthen plot; no label.
s.cemetery(_wmx - 100, _wmy + 130, 100, 70, parish=False, organic=True)

# CROP the frame to the placed content (the title then drops into the framed space).
s.crop_to_content(margin=30)

s.title("Ueda")
s.finish(os.path.join(HERE, "ueda"))
print(f"paddy acres: {net['acres']:.1f}  plots: {len(net['plots'])}")
