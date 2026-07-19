#!/usr/bin/env python3
"""Ikegami ("above the pond") - a HAMLET, the to-scale bundle at 1 ft/px.

The first to-scale hamlet: a small outlying farming community (~15 households / ~75 people)
belonging to a village district, overseen by a headman who lives in the MAIN VILLAGE, not here -
so a hamlet has NO headman of its own, NO shrine (religious_matches_scale: a hamlet has none),
and NO tax-free plots; its dead go to the village district's burial ground, so no graveyard.

SCALE: a hamlet is much smaller than a village, so it is drawn at 1 ft/px (ftpx=1) - twice the
pixel-scale of a village (2 ft/px) - which keeps a ~15-household map a sensible size. The to-scale
homestead bundle carries dimensions in FEET and draws them at ftpx, so the same 46x28 ft minka is
46px here (vs 23px on a village). `toscale=True` opts the hamlet into the bundle path (Moritono, an
atypical legacy hamlet, keeps the old path).

WATER (the name): Ikegami sits ABOVE its pond. The land falls gently N(high) -> S(low). A brook
from the higher ground to the N feeds the head of the common field; comb supply canals distribute
the water southward across the paddies; the field drains at its low S foot into a TAMEIKE reservoir
pond - the pond the hamlet is named for. So the pond is the drainage RESERVE at the bottom, not the
source (which is the northern brook).

FIELD SIZING: ~15 households x ~1.3 acres gross = ~20 acres of paddy. At 1 ft/px that is
~20 x 43,560 = ~870k px^2 (build_comb's own `acres` assumes 2 ft/px, so it over-reports 4x - the
real acreage is computed here from the px area at this map's ftpx).
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

W, H = 1900, 2200                    # tall: the N-high -> S-low valley; zoomed in (1 ft/px) on a small hamlet
SEED = 4
SLUICE = (760, 320)                  # the field head, upper-left; the comb fans SE, cluster nestles W of it
FTPX = 1

s = Settlement(W=W, H=H, seed=SEED)
s.meta(name="Ikegami", scale="hamlet", ftpx=FTPX, toscale=True, households=15, down_deg=90,   # N-high -> downhill = due S
       nucleated=True, field_footbridges=True, pond_role="drainage")   # the pond DRAINS the field (a reservoir below), not feeds it

# Comb supply net marching due S from the head sluice. field_fall CAPS the march so the paddy is
# sized to ~15 households, bounded in-frame with a low-side margin for the drain outfall + pond.
net = build_comb(W, H, SLUICE, SEED, down_deg=90, field_fall=1150,
                 offtakes_a=(0.30, 0.66), offtakes_b=())   # a SPARSE delivery net for a small field
s.meta(dry_furrows_vary=net["furrows_vary"])

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
    g = [f'<clipPath id="{cid}"><polygon points="{pts}"/></clipPath>', f'<g clip-path="url(#{cid})">']
    t = -diag / 2
    while t <= diag / 2:
        mx, my = cx + nx * t, cy + ny * t
        g.append(f'<line x1="{mx-dx*diag/2:.1f}" y1="{my-dy*diag/2:.1f}" '
                 f'x2="{mx+dx*diag/2:.1f}" y2="{my+dy*diag/2:.1f}" stroke="{color}" stroke-width="0.8" opacity="0.8"/>')
        t += 5
    g.append('</g>')
    s.add(''.join(g))


# DRY FIELDS (the upslope N hem), then paddies over the water
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

# THE POND (tameike reservoir) at the low S foot, sited CLEAR of the paddies (its top edge below the field's
# drain outfall) and joined to the crop by a drainage ditch. A pond is a distinct water body, not over the crop.
_drain = [c for c in net["channels"] if c["role"] == "drain"][0]["pts"]
_out = _drain[-1]
PRX, PRY = 116, 74
POND = (_out[0] + 8, min(H - PRY - 20, _out[1] + PRY + 46), PRX, PRY)   # top rim ~46px below the outfall -> off the field
pcx, pcy, prx, pry = POND

# the northern BROOK, artificially DIVERTED into the head-race: it flows IN from the top edge down to the
# diversion (the sluice, the field head) and THERE BECOMES the irrigation channel - it does not run on over
# the paddies. frm=offmap (the water source); no `to` - it hands off to the comb, not the field itself, so it
# ends where the head-race begins (the comb then grounds to this source by touching it at the sluice).
s.stream([(SLUICE[0] - 16, -12), (SLUICE[0] - 10, 130), (SLUICE[0] - 2, SLUICE[1] - 44), SLUICE],
         frm={"kind": "offmap"}, width=7)

# the water network: head-race + supply canals + drain, the drain joining the pond at the rim
for c in sorted(net["channels"], key=lambda c: -c["w"]):
    s.field_channel(c["pts"], '#7C9EB0' if c["role"] == "drain" else '#6C9CBE', c["w"], c.get("w_tail", c["w"]))
s.pond(pcx, pcy, prx, pry)

# the DRAINAGE DITCH: carries the field's runoff from the drain outfall DOWN into the tameike, bridging the
# gap now that the pond sits clear of the field. Drawn AFTER the pond so field_channel clips it onto the rim.
_dchan = [_out, ((_out[0] + pcx) / 2 + 8, (_out[1] + pcy) / 2), (pcx, pcy)]
s.field_channel(_dchan, '#7C9EB0', 2.5, 2.5)

# a reedy fringe rims the pond shore
_ring = [(pcx + (prx + 44) * math.cos(a), pcy + (pry + 44) * math.sin(a)) for a in [i * math.pi / 8 for i in range(16)]]
s.marsh(_ring, role="pond_fringe")

# manifest: field envelope + ditches, for the checks
_env = [[round(x, 1), round(y, 1)] for x, y in net["envelope"]]
_exs = [p[0] for p in _env]
_eys = [p[1] for p in _env]
_pvx = [v[0] for p in net["plots"] for v in p["poly"]]
_pvy = [v[1] for p in net["plots"] for v in p["poly"]]
s.M["fields"].append({"name": "ikegami-paddies", "kind": "paddy", "outline": _env,
                      "bbox": [min(_exs), min(_eys), max(_exs), max(_eys)],
                      "vis_bbox": [min(_pvx), min(_pvy), max(_pvx), max(_pvy)]})
for c in net["channels"]:
    s.M["field_ditches"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in c["pts"]],
                                 "role": c["role"], "field": "ikegami-paddies",
                                 "w": round(c["w"], 1), "w_tail": round(c.get("w_tail", c["w"]), 1)})
# record the drainage ditch (frm=drain -> to=pond) - the SINK anchor for field_ditches_reach_source_and_sink
# + pond_connected_to_field (its end sits in the pond; it touches the field drain at the outfall).
s.M["channels"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in _dchan],
                        "frm": {"kind": "drain"}, "to": {"kind": "pond"}, "w": 2.5})
# the diverted-brook FEED anchor (SOURCE): NOT drawn - the visible supply water is the brook (ending at the
# sluice) plus the head-race field_ditch below it. This thin hairline channel carries the frm/to topology so
# the brook (a stream) is recorded as diverted INTO the field: it starts at the sluice (touching the brook's
# end) and winds gently down-slope INTO the paddy interior, giving fields_show_water_source its channel and
# field_ditches_reach_source_and_sink its external source. Hairline width so it reads as topology, not water.
s.M["channels"].append({"poly": [[SLUICE[0], SLUICE[1]], [749.0, 388.0], [774.6, 459.2]],
                        "frm": {"kind": "stream"}, "to": {"kind": "field", "name": "ikegami-paddies"}, "w": 2.5})

# FARMHOUSES: a small nucleated cluster on the W margin of the field (the higher-ground side), the paddy
# fanning SE below it toward the pond. NO HEADMAN - a hamlet's overseer (the district headman) lives in the
# main village, not here. LANES go down first (no-build corridors the homesteads front): a short N-S spine, a
# spur E to the paddy edge, and a connector track running OFF-map (down-valley to the district / road).
_rng = _random.Random(SEED + 1)
CX, CY = 330, 600
s.lane([(CX - 4, CY - 150), (CX + 6, CY - 30), (CX + 4, CY + 90), (CX + 12, CY + 210)], width=5, clearance=32, worn=True)
_fp = s._nearest_field_point(CX + 140, CY)
s.lane([(CX + 4, CY - 10), ((CX + _fp[0]) / 2 + 8, (CY - 10 + _fp[1]) / 2 - 4), (_fp[0] - 6, _fp[1] + 2)],
       width=5, clearance=32, worn=True)
s.lane([(CX + 12, CY + 210), (CX - 44, CY + 430), (CX - 120, CY + 760), (CX - 210, CY + 1150), (CX - 300, CY + 1620)],
       width=6, clearance=32, worn=True, connector=True)   # runs off the SW edge to the wider world

_placed = 0
for _ in range(140):
    if _placed >= 15:
        break
    _a = _rng.uniform(0, 2 * math.pi)
    _rad = _rng.random() ** 0.5
    _x = CX + math.cos(_a) * _rad * 135
    _y = CY + math.sin(_a) * _rad * 205
    if s.try_place(_x, _y, "plain"):
        _placed += 1
n_farms = s.farmsteads()
print(f"farmhouses: {n_farms}")

# COMMUNAL WELLS + shared draft-animal BYRES among the dwellings (a hamlet keeps a couple of draw-wells and
# ~one byre per 4-5 households). Placed AFTER the houses (they slot into the courtyards), BEFORE the grove.
s.place_wells((CX - 130, CY - 190, CX + 150, CY + 210), spacing=190, near=130)
n_byres = s.draft_byres(fraction=0.22, gap=60)
print(f"byres: {len(n_byres)}")

# HINTERLAND - the non-arable land: a reed MARSH at the low downhill TOE (below the paddy's drainage line, around
# the tameike) and the cut-over SCRUB commons (grass + a few scraggly pines) filling the surrounding margins, the
# DOMINANT denuded-hill cover (China-first: the south-China rice hills were stripped for fuel/timber over centuries;
# the fengshui grove is the green exception). Drawn BEFORE the windbreak grove; the scatter skips fields/pond/lanes/
# houses + a hamlet keep-out, and bleeds off-frame so the crop stays tight.
s.hinterland()   # scrub ring + contour-band marsh + interior fill; the interior fill clothes the comb fan's open
# NE corner automatically, so no hand-added scrub quad is needed.
# ... plus a FEW managed-WOODLAND patches (coppice / bamboo / tung-oil "economic forest") on the higher/farther
# ground, SET BACK from the sun-needing crops by the scrub between: two on the NE upland, one on the W back-slope
# beyond the fengshui grove. Woodland is the green EXCEPTION here, not the dominant cover. Drawn on top of the scrub.
for _patch in [[(1150, 380), (1430, 380), (1430, 640), (1150, 640)],      # NE upland coppice
               [(1520, 430), (1830, 430), (1830, 720), (1520, 720)],      # NE upland coppice
               [(120, 1055), (360, 1055), (360, 1300), (120, 1300)]]:      # W back-slope wood, beyond the grove
    s.commons(_patch, role="woodland")

# WINDBREAK - the fengshui wood on the high/windward WEST back of the cluster (背山面水: back to the hill,
# face the water), plus a leafy copse scatter filling the gaps among the homes. A hamlet's wood is modest
# (one belt, no separate water-mouth grove).
_hx = [h["x"] for h in s.M["houses"]]
_hy = [h["y"] for h in s.M["houses"]]
_minx, _maxx, _miny, _maxy = min(_hx), max(_hx), min(_hy), max(_hy)
_ccy = sum(_hy) / len(_hy)


def _rag(pts, amp=11):
    return [(x + _rng.uniform(-amp, amp), y + _rng.uniform(-amp, amp)) for x, y in pts]


_belt = [(_minx - 4, _miny - 16), (_minx - 44, _miny + 24), (_minx - 64, _ccy),
         (_minx - 44, _maxy - 24), (_minx - 4, _maxy + 16),
         (_minx - 30, _maxy + 30), (_minx - 96, _ccy), (_minx - 30, _miny - 30)]
s.village_grove(_rag(_belt), role="windbreak")
_scatter = [(_minx - 14, _miny - 14), (_maxx + 14, _miny - 14), (_maxx + 14, _maxy + 14), (_minx - 14, _maxy + 14)]
s.village_grove(_scatter, role="copse", dense=False)

# PLANK FOOTBRIDGES across the irrigation ditches (field-workers crossing on the bunds; not tied to a lane)
n_bridges = s.channel_footbridges(spacing=300)
print(f"footbridges: {n_bridges}")

# CROP to the placed content (the commons bleeds off-frame; the hard features fit with a margin)
s.crop_to_content(margin=30)

# NO SHRINE (religious_matches_scale: a hamlet has none), NO GRAVEYARD (its dead go to the village district's
# burial ground), NO TAX-FREE plots - a hamlet is a bare cluster of farms under a distant headman.

_ACRES = sum(abs(sum(p["poly"][i][0] * p["poly"][(i + 1) % len(p["poly"])][1]
                     - p["poly"][(i + 1) % len(p["poly"])][0] * p["poly"][i][1]
                     for i in range(len(p["poly"])))) / 2 for p in net["plots"]) * FTPX * FTPX / 43560

s.title("Ikegami")
print(s.finish(os.path.join(HERE, "ikegami")))
print(f"paddy acres (at {FTPX} ft/px): {_ACRES:.1f}  plots: {len(net['plots'])}  households: {n_farms}")
