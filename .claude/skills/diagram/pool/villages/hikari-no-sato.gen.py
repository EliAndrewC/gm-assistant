#!/usr/bin/env python3
"""Hikari no Sato - the water-first SPLIT (multi-block) VILLAGE (diagram skill, Mode B).

The multi-block variant of the water-first family (Hoshigaoka is the single-field base case): a village
whose paddy is SPLIT into two separate blocks by the local topology - a low central SPUR of higher ground
runs N->S down the valley, so the flat cultivable ground falls into a WEST block and an EAST block, one on
each flank, with the settlement + its shrines strung along the dry spur between them. Block count is
TERRAIN-driven; two blocks split by a spur is a normal, common pattern (Knapp).

WATER FLOWS N->S (`down_deg=90`, N-high -> S-low). Each block is its OWN `build_comb` fan (own sluice + seed):
a brook out of the northern hills is DIVERTED into each block's head-race at its N head, the comb distributes
the water southward, and each block drains at its low S foot into a valley brook off-map, the un-reclaimed low
toes reed marsh. (The old Hikari opened its V-field UPWARD with water entering from the top; reversed to the
downhill fan, the blocks now open SOUTHWARD - the split runs down the fall line, not across it.)

It stays a VILLAGE: a headman, the central Benten shrine (flat ground, on the spur), a second still-tended
Bishamon shrine (in the dry pocket below the E block, left of its toe marsh) with the burial ground in its
churchyard, communal wells, the fengshui windbreak.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, SKILL)
from settlement import Settlement  # noqa: E402
import math  # noqa: E402
import random as _random  # noqa: E402

from waterfields import BEAN_GREEN, BUND, build_comb  # noqa: E402

W, H = 2200, 1720
SEED = 38
FTPX = 2

s = Settlement(W=W, H=H, seed=SEED)
s.meta(name="Hikari no Sato", scale="village", ftpx=FTPX, households=70, down_deg=90,   # N-high -> downhill = due S
       nucleated=True, field_footbridges=True, torii_expected=2, shrine_on_hill=False,
       fallow_implies_abandoned=False, has_pond=False)   # stream-fed, no pond

_furrows_vary = True


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


def add_block(name, sluice, seed, field_fall, offtakes_a, canal_a_len, canal_b_len):
    """Lay one paddy BLOCK: a build_comb fan marching S from `sluice`, a brook DIVERTED into its head-race, the
    comb + drain drawn, the drain's outfall brook off-map S, and the manifest (field envelope + ditches + a
    stream->field feed anchor) recorded. Returns the net so the caller can site marsh etc. `canal_a_len` /
    `canal_b_len` are kept SHORT here so each fan stays NARROW - two side-by-side S-fans widen and would
    otherwise overlap, swallowing the central spur the cluster sits on."""
    net = build_comb(W, H, sluice, seed, down_deg=90, field_fall=field_fall,
                     offtakes_a=offtakes_a, offtakes_b=(),
                     canal_a_len=canal_a_len, canal_b_len=canal_b_len)
    s.field_polys.append([(round(x, 1), round(y, 1)) for x, y in net["envelope"]])
    for _dp in net["dry_plots"]:
        s.block_polys.append(_dp["poly"])
    for p in net["dry_plots"]:
        pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in p["poly"])
        s.add(f'<polygon points="{pts}" fill="{p["fill"]}" stroke="#A98C58" stroke-width="1.4" stroke-linejoin="round"/>')
        furrows(p["poly"], p["furrow"], p["theta"])
        s.M["dry_plots"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in p["poly"]],
                                 "crop": p["crop"], "theta": round(p["theta"], 3)})
    for p in net["plots"]:
        pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in p["poly"])
        s.add(f'<polygon points="{pts}" fill="{p["fill"]}" stroke="{BUND}" stroke-width="2" stroke-linejoin="round"/>')
    beads = ''.join(f'<circle cx="{x}" cy="{y}" r="1.4" fill="{BEAN_GREEN}"/>' for x, y in net["bund_beans"])
    s.add(f'<g opacity="0.85">{beads}</g>')
    # the northern BROOK diverted into the head-race at the sluice (from off-map hills, frm=offmap, no `to`)
    s.stream([(sluice[0] + 6, -12), (sluice[0] + 2, sluice[1] * 0.45), (sluice[0], sluice[1] - 30), sluice],
             frm={"kind": "offmap"}, width=7)
    # the water network: head-race + supply canals + drain, marching S - in the LATE water block
    # (late=True) like every comb net: this map's SECOND comb's plots drew over the first comb's
    # shared-block net (GM 2026-07-21, the Hoshizora canals-under-paddies audit; the late block
    # re-anchors past the last-drawn plots so both nets stay visible)
    for c in sorted(net["channels"], key=lambda c: -c["w"]):
        s.field_channel(c["pts"], '#7C9EB0' if c["role"] == "drain" else '#6C9CBE', c["w"], c.get("w_tail", c["w"]), late=True)
    # the drain's OUTFALL empties into a valley brook off-map S (water OUT)
    if net["brook"]:
        s.stream(net["brook"], frm={"kind": "drain"}, to={"kind": "offmap"}, width=8)
    # manifest: field envelope + ditches + a diverted-brook FEED anchor (SOURCE, undrawn hairline)
    _env = [[round(x, 1), round(y, 1)] for x, y in net["envelope"]]
    _exs = [p[0] for p in _env]
    _eys = [p[1] for p in _env]
    _pvx = [v[0] for p in net["plots"] for v in p["poly"]]
    _pvy = [v[1] for p in net["plots"] for v in p["poly"]]
    s.M["fields"].append({"name": name, "kind": "paddy", "outline": _env,
                          "bbox": [min(_exs), min(_eys), max(_exs), max(_eys)],
                          "vis_bbox": [min(_pvx), min(_pvy), max(_pvx), max(_pvy)]})
    for c in net["channels"]:
        s.M["field_ditches"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in c["pts"]],
                                     "role": c["role"], "field": name,
                                     "w": round(c["w"], 1), "w_tail": round(c.get("w_tail", c["w"]), 1)})
    _hr = net["channels"][0]["pts"]
    _fork = _hr[-1]
    _din = (_fork[0] + 40, _fork[1] + 70)
    _mid = ((sluice[0] + _din[0]) / 2 + 12, (sluice[1] + _din[1]) / 2)
    s.M["channels"].append({"poly": [[round(sluice[0], 1), round(sluice[1], 1)],
                                     [round(_mid[0], 1), round(_mid[1], 1)], [round(_din[0], 1), round(_din[1], 1)]],
                            "frm": {"kind": "stream"}, "to": {"kind": "field", "name": name}, "w": 2.5})
    return net


# WATER + FIELDS: the two blocks, split by the central N-S spur (the settlement sits on it). SYMMETRIC canals so
# the fan's low collector lands on the S edge (the drain-brook exits cleanly, not back through the field), and the
# two shapes DIFFER (the topology gave them different sub-valleys): the WEST block is TALL, the EAST block WIDE.
SLUICE_W = (500, 280)
SLUICE_E = (1660, 290)
net_w = add_block("hikari-west", SLUICE_W, SEED, field_fall=820, offtakes_a=(0.30, 0.62),
                  canal_a_len=(440, 560), canal_b_len=(440, 560))
net_e = add_block("hikari-east", SLUICE_E, SEED + 7, field_fall=470, offtakes_a=(0.34, 0.68),
                  canal_a_len=(700, 840), canal_b_len=(700, 840))
s.meta(dry_furrows_vary=True)

# reed MARSH at each block's low S toe (below the drainage line), around each drain outfall
for net in (net_w, net_e):
    _drain = [c for c in net["channels"] if c["role"] == "drain"][0]["pts"]
    _out = _drain[-1]
    _mp = [(_out[0] - 180, _out[1] - 20), (_out[0] + 180, _out[1] - 20), (_out[0] + 220, _out[1] + 200),
           (_out[0] - 220, _out[1] + 200)]
    s.marsh(_mp, role="toe")

# FARMHOUSES: a nucleated cluster on the dry central SPUR between the two blocks (the higher ground the fields
# leave free). Lanes first (no-build corridors): a N-S spine along the spur, spurs E + W to each block's edge,
# and a connector track off the S edge to the district / road.
_rng = _random.Random(SEED + 4)   # scatter re-seed (was SEED + 1): when the headman started getting a real
#   homestead bundle (yard + garden + grove, GM 2026-07-21) its larger reservation re-rolled the whole packing
#   sequence, and the +1/+2/+3 arrangements each left a grove clump on a lane / dry plot / sun corridor;
#   +4 packs clean (0 gate fails) with the headman kept at its designed spot at the head of the spur lane
CX, CY = 1120, 600         # centered on the dry spur between the tall W block and the wide E block
s.lane([(CX - 6, CY - 240), (CX + 6, CY - 90), (CX - 4, CY + 90), (CX + 8, CY + 250)], width=6, clearance=18, worn=True)
for _sx in (CX - 300, CX + 300):
    _fp = s._nearest_field_point(_sx, CY + 20)
    if _sx < CX:
        # WEST spur: bend NORTH over the barley hem (lanes_clear_of_dry_plots, GM 2026-07-21) - the
        # straight midpoint ran the path THROUGH the two dry plots at (822-929, 627-734); a trodden
        # path runs the baulk between/above the row crops, so it now skirts the hem's top edge and
        # drops to the paddy edge west of the plots.
        # ... and it STOPS at the dry hem's edge (lanes_clear_of_dry_plots, GM 2026-07-21): the
        # barley staircase descends SW from (712,495) to (899,759) with no >3px-clear baulk
        # through it, and routing around its foot fought the homestead packing on every seed - so
        # the field track ends where the crops begin, exactly as a real one does; past the hem the
        # farmers walk the plot baulks. (The paddy beyond is still reached: the W block's water
        # network and bunds run from the hem down.)
        s.lane([(CX - 6, CY + 10), (1020, 622), (940, 636)], width=5, clearance=18, worn=True)
    else:
        s.lane([(CX + 6, CY + 10), ((CX + _fp[0]) / 2, (CY + 10 + _fp[1]) / 2),
                (_fp[0] - 6, _fp[1])], width=5, clearance=18, worn=True)
s.lane([(CX + 8, CY + 250), (CX + 30, CY + 470), (CX + 20, CY + 720), (CX + 40, CY + 980), (CX + 26, CY + 1120)],
       width=6, clearance=18, worn=True, connector=True)

s.headman(CX - 40, CY - 150)          # the largest homestead, at the head of the spur lane
_placed = 1
for _ in range(500):
    if _placed >= 66:
        break
    _a = _rng.uniform(0, 2 * math.pi)
    _rad = _rng.random() ** 0.5
    _x = CX + math.cos(_a) * _rad * 255      # wide enough that the spur cluster's flanks reach BOTH blocks
    _y = CY + math.sin(_a) * _rad * 400
    if s.try_place(_x, _y, "plain"):
        _placed += 1
n_farms = s.farmsteads()
print(f"farmhouses: {n_farms}")

# THE BENTEN VILLAGE SHRINE - on the spur at the S gateway (flat ground, a recent addition, 2 torii). The HALL
# sits just WEST of the entrance track (a hall stands BESIDE the road, never on it), while its two torii straddle
# the track as the village's southern gateway - the road runs UNDER the arches (a real, common feature, which is
# why shrine_halls_clear_of_lanes exempts torii but not the hall). See settlements.md 'Shrines'.
# SIZES (GM 2026-07-21): both halls survived from before the village-shrine norms crystallized, at 96x64 /
# 118x82 px = 192x128 / 236x164 ft - small-MONASTERY footprints in a village (and the oversize Bishamon made
# the correctly-sized churchyard graveyard beside it read tiny). Resized to the pool norms: the primary
# Benten at Kikuta's showcase class (44x30 px ~ 490 m^2 - it holds the village's two-torii south gateway),
# the secondary Bishamon at the ordinary earth-god class (30x24 px ~ 275 m^2, the Ueda/Hoshigaoka size).
# Gated by village_shrine_footprint_within_norms (ceiling 600 m^2).
s.shrine_hall(CX - 40, CY + 540, "Shrine to Benten", w=44, h=30,
              torii=[(1144, CY + 630), (1141, CY + 695)], primary=True)   # torii ON the track (x on the lane centerline)
s.shrine_well(CX - 40, CY + 540)     # ablution well: pass the HALL CENTER - the ring search finds the nearest clear spot beside it
# the still-tended Bishamon village shrine, with the burial ground in its churchyard. It sits in the empty DRY
# pocket BELOW the E block and to the LEFT of that block's toe marsh - not at the far SW. The SW placement was
# the sole thing holding the S/W crop corner ~200px out over empty ground (the `crop_relocatable_singletons`
# GROUP advisory flagged the shrine + its graveyard as one movable precinct); relocating the whole precinct
# here lets the frame crop in to the fields. See settlements.md 'Crop advisory'.
BX, BY = 1600, 1180
s.shrine_hall(BX, BY, "Shrine to Bishamon", "(still tended)", w=30, h=24)
s.shrine_well(BX, BY)                 # ablution well: hall center in, ring search out (the legacy +85 offset only passed while the hall was oversized)

# RESERVE swept ground for both shrine precincts + the graveyard BEFORE the hinterland/commons scatter below,
# or the scrub covers them (the Benten hall + torii and Bishamon hall are placed above; the graveyard is drawn
# at ~line 222). Same footprints as those draw calls - keep the two in sync.
s.reserve_clearing(CX - 40, CY + 540, 44, 30, 58)   # Shrine to Benten
s.reserve_clearing(1144, CY + 630, 38, 28, 30)      # its two torii
s.reserve_clearing(1141, CY + 695, 38, 28, 30)
s.reserve_clearing(BX, BY, 30, 24, 58)              # Shrine to Bishamon
s.reserve_clearing(BX, BY - 110, 46, 32, 30)        # the village graveyard

# COMMUNAL WELLS + shared draft-animal BYRES among the dwellings
s.place_wells((CX - 210, CY - 300, CX + 210, CY + 320), spacing=260, near=110)
n_byres = s.draft_byres(fraction=0.2, gap=64)
print(f"byres: {len(n_byres)}")

# HINTERLAND - the cut-over SCRUB commons on the N up-valley head + the flanks + the central spur (denuded hills,
# China-first), and the reed marsh toes already placed. Plus a couple of managed-WOODLAND coppice patches on the
# high N ground, set back from the crops + off the grove.
s.hinterland(marsh=False)   # the block toe marshes (placed above) ARE the wet toes; skip the redundant full-width one
# the central SPUR between the blocks is inside the cultivated bbox, so the ring bands miss it - fill the dry spur
# margins (N + S of the cluster) with scrub too (the settlement's rough high ground). Skips houses/fields/water.
s.commons([(CX - 180, CY - 320), (CX + 190, CY - 320), (CX + 190, CY - 190), (CX - 180, CY - 190)], role="grazing")
s.commons([(CX - 210, CY + 620), (CX + 220, CY + 620), (CX + 260, CY + 980), (CX - 250, CY + 980)], role="grazing")
for _patch in [[(640, 20), (900, 20), (900, 96), (640, 96)],          # N up-valley coppice, clear of the grove belt
               [(1480, 20), (1740, 20), (1740, 96), (1480, 96)]]:
    s.commons(_patch, role="woodland")

# WINDBREAK - the fengshui wood on the high/windward N back of the cluster, plus a leafy copse among the homes.
_hx = [h["x"] for h in s.M["houses"]]
_hy = [h["y"] for h in s.M["houses"]]
_minx, _maxx, _miny, _maxy = min(_hx), max(_hx), min(_hy), max(_hy)
_ccx = sum(_hx) / len(_hx)


def _rag(pts, amp=11):
    return [(x + _rng.uniform(-amp, amp), y + _rng.uniform(-amp, amp)) for x, y in pts]


_belt = [(_minx - 16, _miny - 4), (_minx + 24, _miny - 44), (_ccx, _miny - 66),
         (_maxx - 24, _miny - 44), (_maxx + 16, _miny - 4),
         (_maxx + 28, _miny - 28), (_ccx, _miny - 96), (_minx - 28, _miny - 28)]
s.village_grove(_rag(_belt), role="windbreak")
_scatter = [(_minx + 34, _miny - 10), (_maxx - 34, _miny - 10), (_maxx - 34, _maxy - 10), (_minx + 34, _maxy - 10)]
s.village_grove(_scatter, role="copse", dense=False)   # inset off the block edges so no clump lands in a dry plot

# PLANK FOOTBRIDGES across the irrigation ditches
n_bridges = s.channel_footbridges(spacing=320)
print(f"footbridges: {n_bridges}")

# the village burial ground in the Bishamon shrine's churchyard, just N of the hall (moved with the precinct)
s.cemetery(BX, BY - 110, 46, 32, parish=False, organic=True)  # resized 2026-07-19: a ~350-person village ground is ~0.1-0.25 acre (~92x64 ft at 2 ft/px), not 0.5+ - see settlements.md funerary anchors

# BRIDGES carry every lane over the water it crosses (the connector track + spurs cross ditches/brooks)
s.bridges()

s.crop_to_content(margin=30)

_ACRES = sum(abs(sum(p["poly"][i][0] * p["poly"][(i + 1) % len(p["poly"])][1]
                     - p["poly"][(i + 1) % len(p["poly"])][0] * p["poly"][i][1]
                     for i in range(len(p["poly"])))) / 2
             for net in (net_w, net_e) for p in net["plots"]) * FTPX * FTPX / 43560

s.title("Hikari no Sato")
print(s.finish(os.path.join(HERE, "hikari-no-sato")))
print(f"paddy acres (at {FTPX} ft/px): {_ACRES:.1f}  households: {n_farms}")
