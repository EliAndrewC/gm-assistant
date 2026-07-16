#!/usr/bin/env python3
"""Kikuta - an average farming village, REBUILT on the water-first engine (diagram skill, Mode B).

The old Kikuta was hand-laid on the legacy `water_field`/`ring`/`hill` API; this is a full redo on the
`build_comb` water-first foundation (the same one Hoshigaoka and Hikari use). It is the NUCLEATED, pond-fed
single-field case: a tameike reservoir on the NW valley head, one contiguous comb-fan paddy marching downhill
to the SE, a clustered village on the high W margin sheltered by a COMMUNAL fengshui windbreak (not per-house
groves), the dry hatake margin + reed marsh + grazing-scrub satoyama ring, communal wells + shared byres, and
the plank footbridges across the ditches.

What KEEPS Kikuta Kikuta: the Shrine to Benten reached by a 7-TORII approach avenue (the old map put the 7 torii
on a hill ascent; on flat ground they line a straight sando leading to the hall), a resident priestess, and the
village burial ground kept well clear of the shrine. (No hill - the GM dropped the hill setup.)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, SKILL)
from settlement import Settlement  # noqa: E402
import math  # noqa: E402
import random as _random  # noqa: E402

from waterfields import BEAN_GREEN, BUND, build_comb  # noqa: E402

W, H = 2400, 1580
POND = (405, 240, 140, 90)          # cx, cy, rx, ry - NW valley-head tameike (uphill)
SLUICE = (490, 300)                 # the single outlet on the pond's downhill (SE) foot (on the rim, anchors the feed)
SEED = 41

s = Settlement(W=W, H=H, seed=SEED)
s.meta(name="Kikuta", scale="village", ftpx=2, households=70, down_deg=45,   # NW-high -> downhill = SE (45 deg)
       nucleated=True, field_footbridges=True, torii_expected=7, shrine_on_hill=False,
       has_pond=True, water_kind="pond", field_origin="organic")

# GRAIN DRIFT (feature 005): Kikuta's hatake grain leans +12deg off the fall-line - a real valley lets the
# ridge-along-contour furrows drift rather than holding one rigid angle (resolves the "uniform 45deg grain"
# residual). Pinned here (a designed village) and resolved through the knob engine to exercise pin -> value;
# it also makes grain_orient a distinct twin-detector axis from Hoshigaoka's straight grain.
s.pin_knob("grain_drift", 12)
GRAIN_DRIFT = s.resolve("grain_drift")

net = build_comb(W, H, SLUICE, SEED, down_deg=45, field_fall=1150,
                 offtakes_a=(0.26, 0.56, 0.83), offtakes_b=(0.6,),
                 dry_keepout=[(POND[0], POND[1], POND[2] + 45)], grain_drift=GRAIN_DRIFT)
s.meta(dry_furrows_vary=net["furrows_vary"])

s.field_polys.append([(round(x, 1), round(y, 1)) for x, y in net["envelope"]])
for _dp in net["dry_plots"]:
    s.block_polys.append(_dp["poly"])
s._nucleated = True                  # nucleated cluster -> compact bundles, sheltered by ONE communal windbreak


def furrows(poly, colour, theta):
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
                 f'x2="{mx+dx*diag/2:.1f}" y2="{my+dy*diag/2:.1f}" stroke="{colour}" stroke-width="0.8" opacity="0.8"/>')
        t += 5
    g.append('</g>')
    s.add(''.join(g))


# DRY FIELDS (upslope margin), then paddies over the water
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

# REED MARSH on the low SE toe (below the drainage line the wet-rice stops and reverts to reed wetland)
s.marsh([(1120, 1260), (2250, 1260), (2250, 500), (1500, 590)])

# the pond's FEEDER brook (water in from off-map), drawn before the pond so the pond covers the junction
pcx, pcy, prx, pry = POND
s.stream([(pcx - 20, -12), (pcx - 10, 74), (pcx + 8, pcy - pry + 18)],
         frm={"kind": "offmap"}, to={"kind": "pond"}, width=9)
s.pond(pcx, pcy, prx, pry)
# reedy fringe + NW catchment scrub around the valley-head reservoir
_ring = [(pcx + (prx + 56) * math.cos(a), pcy + (pry + 56) * math.sin(a)) for a in [i * math.pi / 8 for i in range(16)]]
s.marsh(_ring, role="pond_fringe")
s.commons([(70, 60), (250, 60), (250, 350), (70, 380)])   # NW catchment hill west of the pond

# the water network
for c in sorted(net["channels"], key=lambda c: -c["w"]):
    s.field_channel(c["pts"], '#7C9EB0' if c["role"] == "drain" else '#6C9CBE', c["w"], c.get("w_tail", c["w"]))
if net["brook"]:
    s.stream(net["brook"], frm={"kind": "drain"}, to={"kind": "offmap"}, width=9)
# Register the irrigation ditches on the manifest BEFORE the farmhouses, so the homestead solver's
# channel-avoidance (_rect_on_water) keeps every house + garden OFF the ditches. (Feature 005: the cross
# lane-skeleton packs the cluster nearer the field-edge channel than the old spine did, so the solver has
# to SEE the ditches at placement time - previously they were only recorded after farmsteads() ran.)
for c in net["channels"]:
    s.M["field_ditches"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in c["pts"]],
                                 "role": c["role"], "field": "kikuta-paddies",
                                 "w": round(c["w"], 1), "w_tail": round(c.get("w_tail", c["w"]), 1)})

# FARMHOUSES: Kikuta is a LINEAR village (feature 005 settlement_form=linear) - a RIBBON of homesteads
# strung along the field's high WEST margin, fronting the paddy, NOT a nucleated blob. This ribbon-vs-blob
# contrast with Hoshigaoka is the single biggest structural differentiator (research.md D5: a valley-edge
# track / levee strings the houses out). A SPINE street runs the ribbon's length; the headman anchors the
# high (N) head; the bundle solver hugs each homestead to the field edge as usual.
_rng = _random.Random(SEED + 1)
LINE0, LINE1 = (432, 452), (505, 1028)       # ribbon axis: N (high, by the pond) -> S, just W of the paddy edge
s.lane([LINE0, ((LINE0[0] + LINE1[0]) / 2 - 8, (LINE0[1] + LINE1[1]) / 2), LINE1], width=6, clearance=20, worn=True)   # the spine street
s.meta(lane_skeleton="spine")                # a linear village's lanes are a single spine along the ribbon
# a short SPUR crosses E from mid-ribbon to the paddy edge; the CONNECTOR track leaves S off-map from the foot
_fp = s._nearest_field_point(575, 720)
s.lane([(490, 705), ((490 + _fp[0]) / 2 + 8, (705 + _fp[1]) / 2 - 4), (_fp[0] - 6, _fp[1] + 2)], width=5, clearance=20, worn=True)
s.lane([(LINE1[0] + 2, LINE1[1] + 8), (LINE1[0] + 40, LINE1[1] + 170), (LINE1[0] + 74, LINE1[1] + 350), (LINE1[0] + 100, LINE1[1] + 520)],
       width=6, clearance=20, worn=True, connector=True)
s.headman(LINE0[0] + 30, LINE0[1] + 46)      # the headman anchors the HIGH (N) head of the ribbon
_seeds = s.line_seeds(LINE0, LINE1, 240, 74, _rng)
_placed = 1
for _x, _y in _seeds:
    if _placed >= 66:
        break
    if s.try_place(_x, _y, "plain"):
        _placed += 1
n_farms = s.farmsteads()
print(f"farmhouses: {n_farms}")

# wells: derive the bbox from the actual RIBBON of houses (a long thin band), so they stay among the dwellings
_wx = [h["x"] for h in s.M["houses"]]
_wy = [h["y"] for h in s.M["houses"]]
s.place_wells((min(_wx) - 6, min(_wy) + 12, max(_wx) + 6, max(_wy) - 12), spacing=170, near=200)
n_byres = s.draft_byres(fraction=0.2, gap=70)
print(f"byres: {len(n_byres)}")

# VILLAGE WINDBREAK - the communal fengshui forest (back belt + water-mouth cluster + leafy copse scatter)
_hx = [h["x"] for h in s.M["houses"]]
_hy = [h["y"] for h in s.M["houses"]]
_minx, _maxx, _miny, _maxy = min(_hx), max(_hx), min(_hy), max(_hy)
_ccx, _ccy = sum(_hx) / len(_hx), sum(_hy) / len(_hy)


def _rag(pts, amp=13):
    return [(x + _rng.uniform(-amp, amp), y + _rng.uniform(-amp, amp)) for x, y in pts]


def _interp(pts, n):
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


_belt_inner = [(_ccx - 30, _miny - 20), (_minx - 6, _miny + 34), (_minx - 14, _ccy),
               (_minx - 6, _maxy - 34), (_ccx - 30, _maxy + 20)]
_belt_outer = [(_ccx - 58, _maxy + 58), (_minx - 74, _maxy - 22), (_minx - 100, _ccy),
               (_minx - 74, _miny + 22), (_ccx - 58, _miny - 58)]
_arc = _interp(_belt_outer, 11)
_com_inner = [(x + 16, y) for x, y in _arc]
_com_outer = [(max(16, x - _rng.uniform(96, 150)), y + _rng.uniform(-16, 16)) for x, y in _arc]
s.commons(_com_inner + list(reversed(_com_outer)))
s.village_grove(_rag(_belt_inner) + _rag(_belt_outer), role="windbreak")
_wmx, _wmy = _ccx + 40, _maxy + 66
_wm = [(_wmx + 60 * math.cos(a), _wmy + 46 * math.sin(a)) for a in [i * math.pi / 3 for i in range(6)]]
s.village_grove(_rag(_wm), role="water_mouth")
_scatter = [(_minx - 18, _miny - 18), (_maxx + 18, _miny - 18), (_maxx + 18, _maxy + 18), (_minx - 18, _maxy + 18)]
s.village_grove(_scatter, role="copse", dense=False)

# manifest: field envelope + ditches + the pond->field feed anchor + the drain sink
_env = [[round(x, 1), round(y, 1)] for x, y in net["envelope"]]
_exs = [p[0] for p in _env]
_eys = [p[1] for p in _env]
_pvx = [v[0] for p in net["plots"] for v in p["poly"]]
_pvy = [v[1] for p in net["plots"] for v in p["poly"]]
s.M["fields"].append({"name": "kikuta-paddies", "kind": "paddy", "outline": _env,
                      "bbox": [min(_exs), min(_eys), max(_exs), max(_eys)],
                      "vis_bbox": [min(_pvx), min(_pvy), max(_pvx), max(_pvy)]})
# (field_ditches are registered earlier, before farmsteads(), so the solver avoids them - see above)
_hr = net["channels"][0]["pts"]
_fork = _hr[-1]
_din = (_fork[0] + 70 * math.cos(math.radians(45)), _fork[1] + 70 * math.sin(math.radians(45)))
_mid = ((SLUICE[0] + _din[0]) / 2 - 12, (SLUICE[1] + _din[1]) / 2 + 12)
s.M["channels"].append({"poly": [[round(SLUICE[0], 1), round(SLUICE[1], 1)],
                                 [round(_mid[0], 1), round(_mid[1], 1)], [round(_din[0], 1), round(_din[1], 1)]],
                        "frm": {"kind": "pond"}, "to": {"kind": "field", "name": "kikuta-paddies"}, "w": 2.5})
if not net["brook"]:
    _dr = [c for c in net["channels"] if c["role"] == "drain"][0]["pts"]
    s.M["channels"].append({"poly": [[round(_dr[-2][0], 1), round(_dr[-2][1], 1)],
                                     [round(_dr[-1][0], 1), round(_dr[-1][1], 1)]],
                            "frm": {"kind": "field", "name": "kikuta-paddies"}, "to": {"kind": "offmap"}, "w": 2.5})

n_bridges = s.channel_footbridges(spacing=320)
print(f"footbridges: {n_bridges}")

# GRAZING SCRUB - the dry upland ring (N up-valley head + SW back-slope behind the village)
s.commons([(620, 220), (930, 172), (1240, 152), (1500, 60), (2180, 60), (2180, 490),
           (1920, 240), (1560, 218), (1200, 228), (900, 250), (700, 258), (620, 262)], role="grazing")
s.commons([(80, 900), (250, 990), (430, 1035), (600, 960), (770, 980),
           (905, 1080), (1015, 1185), (1085, 1255), (80, 1255)], role="grazing")
s.commons([(1930, 118), (2170, 118), (2170, 300), (1930, 300)], role="woodland")
s.commons([(1500, 96), (1780, 96), (1780, 164), (1500, 164)], role="woodland")

# THE BENTEN SACRED PRECINCT (flat back-slope, SOUTH of the cluster, WEST of the paddy): the Shrine to Benten,
# its 7-TORII approach avenue, the priestess's ablution well, and - in the SAME precinct - the village burial
# ground (the Shinsei monk performs the funerary rites, so the graves sit by the shrine, not off on their own).
# The hall sits clear of every lane; the 7 torii march SOUTH down the sando toward the off-map approach (the
# flat-ground equivalent of the old winding hill ascent). This is a SET-APART precinct beyond the natural
# village content, so it is placed BEFORE crop_to_content, which then extends the frame to include it (the torii
# are crop drivers now, so the avenue is framed too). See settlements.md 'Shrines'.
BEN_HALL = (628, 1098)                                  # Benten hall, dry back-slope S of the cluster, clear of the windbreak grove's SW horn
_ux, _uy = -0.16, 0.99                                  # approach axis: nearly due S, a slight W lean
_torii = [(round(BEN_HALL[0] + _ux * d), round(BEN_HALL[1] + _uy * d)) for d in range(54, 54 + 7 * 34, 34)]
s.shrine_hall(BEN_HALL[0], BEN_HALL[1], "Shrine to Benten", "(Sister Baika's care)", w=44, h=30,
              kind="shrine", primary=True, torii=_torii, graveyard=False)
s.shrine_well(BEN_HALL[0] - 62, BEN_HALL[1])            # the priestess's ablution well, W of the hall
s.cemetery(730, 1120, 96, 66, parish=False, organic=True, label="village burial ground")   # in the precinct, SE of the hall

s.crop_to_content(margin=30)

s.title("Kikuta")
print("placed houses:", s.finish(os.path.join(HERE, "kikuta-village")))
print(f"paddy acres: {net['acres']:.1f}  plots: {len(net['plots'])}")
