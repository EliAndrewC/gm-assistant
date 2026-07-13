#!/usr/bin/env python3
"""Hoshigaoka ("Star Hill") - the water-first BASE CASE: one pond, one contiguous field.

A village purpose-built to nail the single-field case (the most common one - a broad gentle
valley holds one contiguous paddy expanse; multiple blocks are the TERRAIN-driven variant for
broken ground). Built water-first, layer by layer, each approved by eye, with the checks/tests
backfilled as ratchets: the irrigation pond + sluice + comb supply net + paddies + drain; the
dry hatake margin, reed marsh, and the grazing-scrub satoyama ring; the nucleated farmhouse
cluster with its kura, threshing yards, kitchen gardens, shared draft-animal byres, and communal
wells; the fengshui windbreak grove; the earth-god shrine (with its own ablution well) at the
water-mouth and the back-slope graveyard; the lanes + connector track and the plank footbridges
across the ditches. (Kikuta was later rebuilt on this foundation; Hikari no Sato is the split
multi-block variant.)

FIELD SIZING (population 350, ~70 households): a person eats ~1 koku/yr; pre-modern yields
~1.3 koku/tan; the village also eats coarse grain and pays ~45% tax in rice, so the paddy
runs ~0.8-1.0 tan gross per person -> ~280-350 tan = 69-86 acres, plus dry margins later.
Target ~75-90 acres of paddy on the 240-acre frame (1px = 2ft).

POND SIZING: sole-storage rule of thumb ~2,000-2,500 m3 per irrigated ha (typical depth
2-4 m); a stream-fed pond refilling 1-2x a season runs comfortably at ~1,200-1,500 m3/ha.
31.8 ha of paddy -> ~1.5 ha of pond surface (rx=145, ry=92 px) at ~3 m depth ~ 47,000 m3
~ 1,470 m3/ha + the feeder stream. See settlements.md 'Water-first fields v2' for the grounding.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, SKILL)
from settlement import Settlement, edge_dist, point_in_poly  # noqa: E402
import math  # noqa: E402

from waterfields import BEAN_GREEN, BUND, build_comb  # noqa: E402

W, H = 2420, 1560
POND = (420, 210, 145, 92)          # cx, cy, rx, ry - NW, uphill (valley-head tameike)
SLUICE = (513, 282)                 # the single outlet on the pond's downhill foot
SEED = 7

s = Settlement(W=W, H=H, seed=SEED)
s.meta(name="Hoshigaoka", scale="village", ftpx=2, households=70, down_deg=45,   # NW-high -> downhill = SE (45 deg)
       nucleated=True,                                                   # a clustered village -> a COMMUNAL fengshui windbreak, not per-house groves
       field_footbridges=True)                                          # long irrigation ditches carry plank footbridges (long_ditches_have_a_footbridge)
# Hoshigaoka is a GENTLE valley, so its dry-field furrows FAN (the patchwork quilt) - the default. A steep /
# terraced village would pass build_comb(..., furrow_spread=~0.06) to converge the rows onto the contour, and
# record meta(dry_furrows_vary=False) so dry_plot_furrows_vary is not required. Recorded below from the net.

# Hoshigaoka slopes NW(high) -> SE(low); other provinces differ (Lion: S high; Dragon: N high;
# Unicorn: W high) - down_deg is the knob, nothing assumes SE. The pond is a keepout so the
# upslope dry fields do not grow over the water.
# field_fall CAPS the downhill march so the paddy is sized to the population (~83 acres) and BOUNDED
# within the frame - not grown to the map corner (which spilled it off the E edge). The frame is sized
# to hold the whole village + field + a low-side margin for the drain's outfall + brook to discharge.
net = build_comb(W, H, SLUICE, SEED, down_deg=45, field_fall=1230,
                 offtakes_a=(0.25, 0.55, 0.82), offtakes_b=(0.6,),   # SPARSER delivery net (~6-9 cols apart,
                 dry_keepout=[(POND[0], POND[1], POND[2] + 45)])     # the sparse pre-modern cascade, not a Meiji ditch-per-plot grid)
s.meta(dry_furrows_vary=net["furrows_vary"])   # gentle valley -> dry furrows FAN (the check requires it); a steep village would be False

# Register the water-first field footprints so the homestead solver sees them: the paddy
# envelope blocks houses AND provides field-adjacency; the dry-field plots are no-build
# (houses must not sit on standing crops); the pond is already a keepout ellipse via s.pond.
s.field_polys.append([(round(x, 1), round(y, 1)) for x, y in net["envelope"]])
for _dp in net["dry_plots"]:
    s.block_polys.append(_dp["poly"])
s._nucleated = True                  # China-leaning default: a tight nucleated cluster, no per-house grove


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
    g = [f'<clipPath id="{cid}"><polygon points="{pts}"/></clipPath>',
         f'<g clip-path="url(#{cid})">']
    t = -diag / 2
    while t <= diag / 2:
        mx, my = cx + nx * t, cy + ny * t
        g.append(f'<line x1="{mx-dx*diag/2:.1f}" y1="{my-dy*diag/2:.1f}" '
                 f'x2="{mx+dx*diag/2:.1f}" y2="{my+dy*diag/2:.1f}" '
                 f'stroke="{colour}" stroke-width="0.8" opacity="0.8"/>')
        t += 5
    g.append('</g>')
    s.add(''.join(g))


# DRY FIELDS first (upslope margin), then paddies over the water
for p in net["dry_plots"]:
    pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in p["poly"])
    s.add(f'<polygon points="{pts}" fill="{p["fill"]}" stroke="#A98C58" '
          f'stroke-width="1.4" stroke-linejoin="round"/>')
    furrows(p["poly"], p["furrow"], p["theta"])
    # record each dry plot (poly + furrow angle) so dry_plot_furrows_vary can verify neighbours differ
    s.M["dry_plots"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in p["poly"]],
                             "crop": p["crop"], "theta": round(p["theta"], 3)})

# paddies (the water is drawn OVER them, along their edges)
for p in net["plots"]:
    pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in p["poly"])
    s.add(f'<polygon points="{pts}" fill="{p["fill"]}" stroke="{BUND}" '
          f'stroke-width="2" stroke-linejoin="round"/>')

# AZEMAME: soybeans beaded along a fraction of the paddy bunds (sub-pixel, so symbolic)
beads = ''.join(f'<circle cx="{x}" cy="{y}" r="1.4" fill="{BEAN_GREEN}"/>'
                for x, y in net["bund_beans"])
s.add(f'<g opacity="0.85">{beads}</g>')

# REED MARSH on the low, downstream SE toe of the valley: below the paddy's drainage line the wet-rice
# cultivation stops, and the un-reclaimed valley floor stays reed WETLAND (wet rice is diked OUT of marsh -
# where reclamation ends, or the ground is too low/wet to manage, it reverts to marsh, NOT dry plain). A
# generous SE region; s.marsh SKIPS any point on the paddy, so the reeds ABUT the field's low edge and only
# fill the open ground beyond, feathering out and trailing off the SE map corner. See settlements.md 'Marsh'.
s.marsh([(1080, 1240), (2210, 1240), (2210, 470), (1450, 560)])

# the pond's FEEDER: a natural brook flowing IN from the map edge (water sources come from off-map, not
# out of nowhere). Recorded as a stream anchored offmap->pond so pond_fed_from_edge + stream_runs_off_edge
# validate it. Drawn BEFORE the pond so the pond covers the junction.
pcx, pcy, prx, pry = POND
s.stream([(pcx - 24, -12), (pcx - 14, 70), (pcx + 6, pcy - pry + 18)],
         frm={"kind": "offmap"}, to={"kind": "pond"}, width=9)
s.pond(pcx, pcy, prx, pry)

# AROUND THE POND (the valley-head reservoir sits IN the hill catchment - satoyama). (a) a REEDY FRINGE at the
# shallow shore (marsh role='pond_fringe' - a ring around the pond; s.marsh skips the open water + the dry
# fields, so reeds only rim the shore). (b) CATCHMENT SCRUB behind/west of the pond - the cut-over hill that
# feeds it (reuse the commons scrub: grass + brush + scraggly pine), bleeding off the NW corner. See settlements.md
# 'Marsh' + 'Village windbreak' (back-slope). Both drawn AFTER the pond so the reeds rim its edge.
_ring = [(pcx + (prx + 58) * math.cos(a), pcy + (pry + 58) * math.sin(a)) for a in [i * math.pi / 8 for i in range(16)]]
s.marsh(_ring, role="pond_fringe")
s.commons([(78, 58), (258, 58), (258, 344), (78, 372)])   # NW catchment hill, west of the pond (x<pond west edge), bleeds off the NW

# the water network: head-race, tapering supply canals, delivery ditches, drain. The channels go THROUGH the
# water block (s.field_channel) so they JOIN the pond + each other cleanly: each bed sits in the shared water
# group over the pond's rim edge, and the head-race's sluice end is snapped onto the rim (covers it -> clean gap).
for c in sorted(net["channels"], key=lambda c: -c["w"]):
    s.field_channel(c["pts"], '#7C9EB0' if c["role"] == "drain" else '#6C9CBE',
                    c["w"], c.get("w_tail", c["w"]))

# the drain's OUTFALL empties into a natural valley BROOK that carries the runoff off the map downhill
# (water OUT, mirroring the pond's feeder = water IN). Only present when the field's low corner sits
# INSIDE the frame; on Hoshigaoka the paddy runs to the E map edge, so the drain discharges off-map
# directly (a brook from an edge-outfall would run back through the field). A field-extent pass that
# bounds the paddy within the frame (see settlements.md) will bring the outfall in-frame and light the brook.
if net["brook"]:
    s.stream(net["brook"], frm={"kind": "drain"}, to={"kind": "offmap"}, width=9)

# FARMHOUSES: a nucleated cluster on the higher WEST margin (NW-high slope), below the pond and
# west of the paddy - houses grouped, paddy radiating downhill to the SE. Seed a rough disk of
# candidates; the bundle solver compacts each toward the nearest paddy bund and its neighbours,
# so the accepted homesteads pack into a nucleus hugging the field's high edge. Over-seed and cap
# at ~70 (the Chinese rice-village norm is 30-60 households; Hoshigaoka's ~70 sits just above it).
import random as _random  # noqa: E402

_rng = _random.Random(SEED + 1)
CX, CY = 400, 650                    # cluster centre on the higher W margin

# LANES go down BEFORE the houses - a lane lays a no-build corridor, so the homesteads FRONT it. They
# are UNPAVED trodden earth, NARROW (a single wheelbarrow/packhorse/porter track - China moved goods by
# wheelbarrow + shoulder-pole, not wide cart roads, so two carts could not pass) with no centre marking;
# a village could never afford paving. A nucleated village is
# laced with lanes: a main N-S spine through the cluster, and a spur east to the paddy edge that bridges
# the village to its fields (spur field-end computed from the field geometry, not hand-placed).
s.lane([(CX - 8, CY - 205), (CX + 6, CY - 70), (CX + 8, CY + 85), (CX + 16, CY + 245)],
       width=5, clearance=18, worn=True)
_fp = s._nearest_field_point(CX + 170, CY + 20)
# the spur STOPS at the field edge - a lane does not run through the flooded paddy (people cross into the
# fields on foot, along the earthen bunds). The plank bridges over the ditches are placed separately by
# channel_footbridges() and are NOT connected to any lane.
s.lane([(CX + 2, CY + 30), ((CX + _fp[0]) / 2 + 12, (CY + 30 + _fp[1]) / 2 - 6), (_fp[0] - 6, _fp[1] + 2)],
       width=5, clearance=18, worn=True)
# The CONNECTING PATH to the wider world: a trodden dirt track (NOT a constructed road), worn into the
# ground by feet, wheelbarrows, packhorses, and porters heading down-valley to the nearest district / Imperial
# road (off-map). The main lane does NOT dead-end at the cluster edge - it continues out as this track.
s.lane([(CX + 4, CY + 245), (CX + 48, CY + 360), (CX + 78, CY + 490), (CX + 112, CY + 700),
        (CX + 138, CY + 860), (CX + 158, CY + 985)],
       width=6, clearance=18, worn=True, connector=True)   # runs OFF the bottom edge (H+), not stopping short

s.headman(455, CY - 60)              # the largest homestead, fronting the head of the main lane
_placed = 1
for _ in range(240):
    if _placed >= 70:
        break
    _a = _rng.uniform(0, 2 * math.pi)
    _rad = _rng.random() ** 0.5
    _x = CX + math.cos(_a) * _rad * 165   # a concentrated disk; the placer then hugs each homestead to
    _y = CY + math.sin(_a) * _rad * 250   # the paddy edge and packs it ALONG the field, against neighbours
    if s.try_place(_x, _y, "plain"):
        _placed += 1
n_farms = s.farmsteads()
print(f"farmhouses: {n_farms}")

# COMMUNAL WELLS (井戸): every village keeps a few shared draw-wells among the dwellings - one per ~20-25
# households, the idobata (well-side) social hub. A farm beside the irrigation net can dip the ditch, but the
# houses set back from the water need a well. Scatter across the house-cluster bbox; `near` keeps each well
# AMONG the houses (never out in open country), and place_wells' coverage pass guarantees no dwelling is left
# dry. Placed AFTER the farmhouses (so the wells slot into the courtyards between them) and before the grove.
s.place_wells((228, 410, 670, 910), spacing=185, near=210)

# DRAFT-ANIMAL BYRES: shared ox / water-buffalo sheds standing in the courtyards among the homesteads (a
# buffalo was costly and shared, so ~one byre per 4-5 households, not one per farm). Scattered into clear gaps
# like the wells, each among the houses. AFTER the farmhouses + wells, BEFORE the grove (which skips them).
n_byres = s.draft_byres(fraction=0.2, gap=70)
print(f"byres: {len(n_byres)}")

# VILLAGE WINDBREAK - the Chinese fengshui forest (风水林), a COMMUNAL grove, NOT per-house yashikirin (a
# nucleated cluster shelters behind one village-scale wood). Sited per 背山面水 ("back to the hill, face the
# water"): the DENSE wood sits on the high/windward BACK, the FIELD/water side stays OPEN, and the village
# itself nestles in scattered bamboo + fruit (not bare ground). Three parts, IRREGULAR + terrain-following
# (village_grove fills an organic polygon, skipping clumps on houses/yards/gardens/paddy): (1) the 后龙林
# back-village BELT, a ragged crescent EMBRACING the high WEST edge + wrapping the NW/SW corners, nestled
# against the cluster; (2) the 水口林 WATER-MOUTH cluster at the low SE exit; (3) a leafy SCATTER of bamboo /
# fruit copses filling the open gaps among the houses. See settlements.md 'Village windbreak'.
_hx = [h["x"] for h in s.M["houses"]]
_hy = [h["y"] for h in s.M["houses"]]
_minx, _maxx, _miny, _maxy = min(_hx), max(_hx), min(_hy), max(_hy)
_ccx, _ccy = sum(_hx) / len(_hx), sum(_hy) / len(_hy)


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


# back-grove crescent geometry (shared by the belt AND the commons that abuts its back): a crescent embracing
# the WEST (high, windward) back, deepest in the middle, tapering into horns that wrap the NW + SW corners; the
# inner edge hugs the houses (clump-skipping keeps it off them), the outer edge bulges ~95 px west (~1-2 ha).
_belt_inner = [(_ccx - 30, _miny - 20), (_minx - 6, _miny + 34), (_minx - 14, _ccy),
               (_minx - 6, _maxy - 34), (_ccx - 30, _maxy + 20)]
_belt_outer = [(_ccx - 58, _maxy + 58), (_minx - 74, _maxy - 22), (_minx - 100, _ccy),
               (_minx - 74, _miny + 22), (_ccx - 58, _miny - 58)]

# FUEL-AND-FODDER COMMONS - drawn FIRST, UNDER the forest, so the grove's dense canopy overlaps its inner edge
# for a SEAMLESS abut (no bare gap). It is a ragged BAND that PARALLELS the grove's back at a jittered width
# (NOT a wedge/rhombus): the E edge underlaps the grove back, the W edge is ragged and follows the same curve
# out onto the far windward slope. The degraded, cut-over hill-ground (grass, brush, scraggly pines) - non-
# arable grazing, visually open + sparse, distinct from the dense grove. Toposequence: village -> back-grove ->
# fuel commons -> (off-map boundary). See settlements.md 'Village windbreak' / back-slope.
_arc = _interp(_belt_outer, 11)                       # densified grove-back curve (bottom -> top)
_com_inner = [(x + 16, y) for x, y in _arc]           # underlap the grove back a touch (hidden under the canopy)
_com_outer = [(max(16, x - _rng.uniform(96, 150)), y + _rng.uniform(-16, 16)) for x, y in _arc]   # ragged ~parallel W edge
s.commons(_com_inner + list(reversed(_com_outer)))

# (1) back-village belt ON TOP of the commons (its canopy blends over the scrub's inner edge)
s.village_grove(_rag(_belt_inner) + _rag(_belt_outer), role="windbreak")
# (2) water-mouth cluster at the low SE exit (by the connector track); an irregular blob, kept off the paddy
_wmx, _wmy = _ccx + 40, _maxy + 66
_wm = [(_wmx + 60 * math.cos(a), _wmy + 46 * math.sin(a)) for a in [i * math.pi / 3 for i in range(6)]]
s.village_grove(_rag(_wm), role="water_mouth")
# (3) leafy scatter: bamboo + dooryard fruit filling the OPEN gaps across the whole cluster (village_grove
# skips any clump on a house/yard/garden/paddy, so these settle into the bare ground between homes)
_scatter = [(_minx - 18, _miny - 18), (_maxx + 18, _miny - 18), (_maxx + 18, _maxy + 18), (_minx - 18, _maxy + 18)]
s.village_grove(_scatter, role="copse", dense=False)

# manifest: the field envelope + every watercourse, for the checks that come later
_env = [[round(x, 1), round(y, 1)] for x, y in net["envelope"]]
_exs = [p[0] for p in _env]
_eys = [p[1] for p in _env]
# vis_bbox = the extent of the DRAWN paddy plots (the envelope has an invisible tail past the last plot used
# only for house-blocking); crop_to_content frames to the visible plots, not that tail
_pvx = [v[0] for p in net["plots"] for v in p["poly"]]
_pvy = [v[1] for p in net["plots"] for v in p["poly"]]
s.M["fields"].append({"name": "hoshigaoka-paddies", "kind": "paddy", "outline": _env,
                      "bbox": [min(_exs), min(_eys), max(_exs), max(_eys)],
                      "vis_bbox": [min(_pvx), min(_pvy), max(_pvx), max(_pvy)]})
for c in net["channels"]:
    s.M["field_ditches"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in c["pts"]],
                                 "role": c["role"], "field": "hoshigaoka-paddies",
                                 "w": round(c["w"], 1), "w_tail": round(c.get("w_tail", c["w"]), 1)})
# ANCHOR the network for field_ditches_reach_source_and_sink: the pond FEEDS the head-race (external
# SOURCE) and the drain discharges to a runoff SINK. Water IN and water OUT, both traceable off the
# field - the check that a paddy system is not a closed loop. (The brook, when present, is the sink;
# where the field runs to the map edge the drain's own outfall is off-map, recorded here as the sink.)
_hr = net["channels"][0]["pts"]                       # the head-race, from the sluice on the pond
# the pond->field FEED anchor: this is NOT drawn (the visible water is drawn from net["channels"] above);
# it carries the frm/to topology for field_ditches_reach_source_and_sink, so it sits at the hairline width
# and winds gently from the pond (sluice) INTO the paddy interior (a point ~70px down-slope of the fork,
# well inside the field). The drain's SINK is the brook (a stream, to=offmap) that touches the drain.
_fork = _hr[-1]
_din = (_fork[0] + 70 * math.cos(math.radians(45)), _fork[1] + 70 * math.sin(math.radians(45)))
_mid = ((SLUICE[0] + _din[0]) / 2 - 12, (SLUICE[1] + _din[1]) / 2 + 12)   # a bend so it winds (not straight)
s.M["channels"].append({"poly": [[round(SLUICE[0], 1), round(SLUICE[1], 1)],
                                 [round(_mid[0], 1), round(_mid[1], 1)],
                                 [round(_din[0], 1), round(_din[1], 1)]],
                        "frm": {"kind": "pond"}, "to": {"kind": "field", "name": "hoshigaoka-paddies"}, "w": 2.5})
if not net["brook"]:                                  # field runs to the map edge -> drain outfall IS off-map
    _dr = [c for c in net["channels"] if c["role"] == "drain"][0]["pts"]
    s.M["channels"].append({"poly": [[round(_dr[-2][0], 1), round(_dr[-2][1], 1)],
                                     [round(_dr[-1][0], 1), round(_dr[-1][1], 1)]],
                            "frm": {"kind": "field", "name": "hoshigaoka-paddies"}, "to": {"kind": "offmap"}, "w": 2.5})

# PLANK FOOTBRIDGES across the irrigation ditches: standalone planks where field-workers cross a channel
# while walking the paddy bunds - NOT tied to any lane. Every long ditch stretch gets one about midway (the
# northern trunk along the top of the field gets several; each branch running into the paddy gets one; the
# channel next to the village gets one), spanning the ditch perpendicular. Called AFTER all field ditches.
n_bridges = s.channel_footbridges(spacing=320)
# The channel running N-S along the VILLAGE'S east edge sees heavy foot traffic, so it carries a SECOND plank
# on its NORTHERN stretch (beyond the midway one channel_footbridges placed) - the descending 'main' ditch.
_vc = next(d for d in s.M["field_ditches"]
           if d["role"] == "main" and abs(d["poly"][-1][1] - d["poly"][0][1]) > 150)
_vp = _vc["poly"]
_seg = [math.hypot(_vp[i + 1][0] - _vp[i][0], _vp[i + 1][1] - _vp[i][1]) for i in range(len(_vp) - 1)]
_t, _acc = 0.24 * sum(_seg), 0.0
for _i, _sl in enumerate(_seg):
    if _acc + _sl >= _t:
        _f = (_t - _acc) / _sl
        _ax, _ay = _vp[_i]
        _bx, _by = _vp[_i + 1]
        s.bridge(_ax + (_bx - _ax) * _f, _ay + (_by - _ay) * _f,
                 math.degrees(math.atan2(_by - _ay, _bx - _ax)) + 90, _vc["w"] + 15, 5.5)
        break
    _acc += _sl
print(f"footbridges: {n_bridges + 1}")

# GRAZING SCRUB fills the remaining DRY margins of the NW-high / SE-low valley into a CONTINUOUS upland ring
# (not isolated corner patches): everything above the irrigation command, and the back-slope behind the
# village, is un-terraced grass-and-scrub hill-grazing. role='grazing' = general marginal hill-grazing (not
# the windward fuel-commons), so it is exempt from commons_beyond_the_windbreak. Held OFF the crops: commons
# auto-skips the paddy, and the polygons are kept ABOVE the dry-field tops (ymin ~231-285) and WEST of the
# paddy edge so scrub never dots the rows. Two broad bands:
#   (a) the NORTH up-valley head - one band across the WHOLE top edge above the dry fields, from the pond
#       catchment east to the NE flank, which drops at the east edge to meet the SE reed marsh. The grass
#       hill climbs to the off-map ridge; the dry hatake fields are the cultivated hem of it.
#   (b) the SOUTH back-slope - the non-arable hill BEHIND the village (background 背山, off the water/field
#       front), below the fengshui grove and west of the paddy, down to the SW boundary. The graveyard +
#       earth-god shrine sit ON this scrub (drawn later, on top): burial + kegare belong on the waste back-slope.
# ORDER: this fill comes AFTER the farmhouses + groves (so it fills the gaps THEY leave) but BEFORE the
# graveyard + shrine (so those sit ON the scrubland, not on bare tan). See settlements.md 'Village windbreak'.
# the NORTH band's top edge DIPS over x630-1470 (a shallow clearing / col in the ridge line) so the map TITLE
# has a blank tan bay just right of the pond to sit in - the hills stand back a little at the valley mouth.
s.commons([(630, 215), (930, 170), (1230, 150), (1470, 58), (2160, 58), (2160, 475),
           (1905, 235), (1560, 215), (1200, 225), (900, 248), (700, 255), (630, 258)], role="grazing")   # NORTH up-valley grass hills
s.commons([(85, 895), (250, 988), (430, 1030), (600, 955), (770, 975),
           (900, 1075), (1010, 1180), (1080, 1250), (85, 1250)], role="grazing")   # SOUTH back-slope behind the village
# A FEW managed-WOODLAND patches (coppice / bamboo / tung-oil "economic forest") - the green EXCEPTION amid the
# cut-over grass hills (China-first: the hills are mostly denuded scrub, with a little managed wood). Sited on the
# open high ground CLEAR of the crops and never SHADING them: the sun is to the S, so trees cast shadows N - a
# patch stands north/beside the fields, never on their sunny south edge (gated by woodland_clear_of_crops). Both
# sit on the high N ridge ABOVE the dry-hatake fields, EAST of the title bay (x630-1470), and CLEAR of the fengshui
# grove on the W - the coppice is a DISTINCT stand from the protected grove (gated by woodland_clear_of_grove).
s.commons([(1910, 115), (2150, 115), (2150, 295), (1910, 295)], role="woodland")   # NE, east of the dry ribbon, above the paddy
s.commons([(1490, 95), (1770, 95), (1770, 162), (1490, 162)], role="woodland")     # N ridge above the dry fields

# CROP the frame to the placed content (BEFORE the title + the deferred small features, which drop into the
# framed space): the commons is a BLEED feature, so its outer scrub trails off the west edge = "more wild
# ground this way", while the hard features (village, fields, grove, pond) fit fully with a margin.
s.crop_to_content(margin=30)

# DEFERRED FEATURES drop into the cropped frame. VILLAGE SHRINE at the SE WATER-MOUTH ENTRANCE: the tutelary /
# earth-god shrine (土地庙) guards the feng-shui entry point where the connector track leaves for the road, set
# in the water-mouth grove that we already grew there, a small Shinto shrine fronted by a torii. SMALL (~30x24
# px ~ 275 m2, a touch bigger than a plain farmhouse) - a village earth-god shrine is a modest hall, NOT a
# temple. (kind='shrine' satisfies religious_matches_scale; graveyard=False - Shinto keeps kegare at arm's length.)
s.shrine_hall(392, 1074, "", w=30, h=24, kind="shrine", primary=True,
              torii=[(392, 1114)], graveyard=False)   # no label - the vermilion hall + torii read as a shrine
# VILLAGE GRAVEYARD on the SW BACK-SLOPE, behind the village and well AWAY from the pond (the water source -
# graves foul water) and off the field/water front (背山面水: the non-arable back side). The high NW back is
# taken by the sacred grove + the pond, so the graves sit on the clear lower-W slope below the grove. A village
# plot (parish=False, not a temple parish ground), set back from all water + kept >=120px from the shrine (kegare).
s.cemetery(178, 1030, 100, 70, parish=False, organic=True)   # no label - the marker rows read as a graveyard; organic = an irregular earthen plot, not a ruled rectangle
# The shrine sits APART from the village (past the graveyard at the water-mouth), beyond reach of the
# communal wells, so it keeps its OWN well for purification/ablution (temizu) - a remote shrine is watered by
# its own draw-point, not the village's (remote_shrine_has_own_well).
s.shrine_well(392, 1074)

s.title("Hoshigaoka")   # title placed AFTER everything, so it finds blank space in the framed window
s.finish(os.path.join(HERE, "hoshigaoka"))
print(f"paddy acres: {net['acres']:.1f}  plots: {len(net['plots'])}")
