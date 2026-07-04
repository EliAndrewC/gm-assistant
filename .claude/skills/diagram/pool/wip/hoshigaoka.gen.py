#!/usr/bin/env python3
"""Hoshigaoka ("Star Hill") - the water-first BASE CASE: one pond, one contiguous field.

A NEW village, purpose-built to nail the single-field case (the most common one - a broad
gentle valley holds one contiguous paddy expanse; multiple blocks are the TERRAIN-driven
variant for broken ground). Kikuta will be rebuilt later on this foundation WITH its
backstory second field (blighted, fallow since last summer, water shut at the sluice);
Hikari no Sato later still as a split multi-block village. Stage 1: the irrigation pond,
its single sluice, the comb supply network, the paddies grown between the ditch threads,
and the drain. No roads, farmhouses, shrine or monk plots yet - one layer at a time, each
approved by eye; checks/tests are backfilled at the END as ratchets (per the GM), so this
WIP lives outside pool/*.gen.py's test glob.

FIELD SIZING (population 350, ~70 households): a person eats ~1 koku/yr; pre-modern yields
~1.3 koku/tan; the village also eats coarse grain and pays ~45% tax in rice, so the paddy
runs ~0.8-1.0 tan gross per person -> ~280-350 tan = 69-86 acres, plus dry margins later.
Target ~75-90 acres of paddy on the 240-acre frame (1px = 2ft).

POND SIZING: sole-storage rule of thumb ~2,000-2,500 m3 per irrigated ha (typical depth
2-4 m); a stream-fed pond refilling 1-2x a season runs comfortably at ~1,200-1,500 m3/ha.
31.8 ha of paddy -> ~1.5 ha of pond surface (rx=145, ry=92 px) at ~3 m depth ~ 47,000 m3
~ 1,470 m3/ha + the feeder stream. See SKILL.md 'Water-first fields v2' for the grounding.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, SKILL)
from settlement import Settlement  # noqa: E402
import math  # noqa: E402

from waterfields import BEAN_GREEN, BUND, build_comb  # noqa: E402

W, H = 2420, 1560
POND = (420, 210, 145, 92)          # cx, cy, rx, ry - NW, uphill (valley-head tameike)
SLUICE = (513, 282)                 # the single outlet on the pond's downhill foot
SEED = 7

s = Settlement(W=W, H=H, seed=SEED)
s.meta(name="Hoshigaoka", scale="village", households=70, down_deg=45)   # NW-high -> downhill = SE (45 deg)

# Hoshigaoka slopes NW(high) -> SE(low); other provinces differ (Lion: S high; Dragon: N high;
# Unicorn: W high) - down_deg is the knob, nothing assumes SE. The pond is a keepout so the
# upslope dry fields do not grow over the water.
# field_fall CAPS the downhill march so the paddy is sized to the population (~83 acres) and BOUNDED
# within the frame - not grown to the map corner (which spilled it off the E edge). The frame is sized
# to hold the whole village + field + a low-side margin for the drain's outfall + brook to discharge.
net = build_comb(W, H, SLUICE, SEED, down_deg=45, field_fall=1230,
                 offtakes_a=(0.25, 0.55, 0.82), offtakes_b=(0.6,),   # SPARSER delivery net (~6-9 cols apart,
                 dry_keepout=[(POND[0], POND[1], POND[2] + 45)])     # the sparse pre-modern cascade, not a Meiji ditch-per-plot grid)

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

# paddies (the water is drawn OVER them, along their edges)
for p in net["plots"]:
    pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in p["poly"])
    s.add(f'<polygon points="{pts}" fill="{p["fill"]}" stroke="{BUND}" '
          f'stroke-width="2" stroke-linejoin="round"/>')

# AZEMAME: soybeans beaded along a fraction of the paddy bunds (sub-pixel, so symbolic)
beads = ''.join(f'<circle cx="{x}" cy="{y}" r="1.4" fill="{BEAN_GREEN}"/>'
                for x, y in net["bund_beans"])
s.add(f'<g opacity="0.85">{beads}</g>')

# the pond's FEEDER: a natural brook flowing IN from the map edge (water sources come from off-map, not
# out of nowhere). Recorded as a stream anchored offmap->pond so pond_fed_from_edge + stream_runs_off_edge
# validate it. Drawn BEFORE the pond so the pond covers the junction.
pcx, pcy, prx, pry = POND
s.stream([(pcx - 24, -12), (pcx - 14, 70), (pcx + 6, pcy - pry + 18)],
         frm={"kind": "offmap"}, to={"kind": "pond"}, width=9)
s.pond(pcx, pcy, prx, pry)

# the water network: head-race, tapering supply canals, delivery ditches, drain
def _draw_channel(pts, col, w0, w1):
    """Draw a watercourse. If w1 < w0 it TAPERS (a delivery ditch dwindling as it feeds the paddies) -
    split into stroked pieces of decreasing width; round caps soften the joins into a smooth narrowing."""
    if abs(w1 - w0) < 0.2:
        dd = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        s.add(f'<path d="{dd}" fill="none" stroke="{col}" stroke-width="{w0:.1f}" '
              f'stroke-linejoin="round" stroke-linecap="round" opacity="0.92"/>')
        return
    n, L = 7, len(pts)
    for k in range(n):
        piece = pts[k * (L - 1) // n: (k + 1) * (L - 1) // n + 1]
        if len(piece) < 2:
            continue
        wk = w0 + (w1 - w0) * (k + 0.5) / n
        dd = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in piece)
        s.add(f'<path d="{dd}" fill="none" stroke="{col}" stroke-width="{wk:.1f}" '
              f'stroke-linejoin="round" stroke-linecap="round" opacity="0.92"/>')


for c in sorted(net["channels"], key=lambda c: -c["w"]):
    _draw_channel(c["pts"], '#7C9EB0' if c["role"] == "drain" else '#6C9CBE',
                  c["w"], c.get("w_tail", c["w"]))

# the drain's OUTFALL empties into a natural valley BROOK that carries the runoff off the map downhill
# (water OUT, mirroring the pond's feeder = water IN). Only present when the field's low corner sits
# INSIDE the frame; on Hoshigaoka the paddy runs to the E map edge, so the drain discharges off-map
# directly (a brook from an edge-outfall would run back through the field). A field-extent pass that
# bounds the paddy within the frame (see SKILL.md) will bring the outfall in-frame and light the brook.
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
s.lane([(CX - 8, CY - 205), (CX + 6, CY - 70), (CX - 4, CY + 85), (CX + 4, CY + 245)],
       width=5, clearance=18, worn=True)
_fp = s._nearest_field_point(CX + 170, CY + 20)
s.lane([(CX + 2, CY + 30), ((CX + _fp[0]) / 2 + 12, (CY + 30 + _fp[1]) / 2 - 6), (_fp[0] - 6, _fp[1] + 2)],
       width=5, clearance=18, worn=True)
# The CONNECTING PATH to the wider world: a trodden dirt track (NOT a constructed road), worn into the
# ground by feet, wheelbarrows, packhorses, and porters heading down-valley to the nearest district / Imperial
# road (off-map). The main lane does NOT dead-end at the cluster edge - it continues out as this track.
s.lane([(CX + 4, CY + 245), (CX + 48, CY + 360), (CX + 78, CY + 490), (CX + 112, CY + 700),
        (CX + 138, CY + 860), (CX + 158, CY + 985)],
       width=6, clearance=18, worn=True, connector=True)   # runs OFF the bottom edge (H+), not stopping short
s.label(CX + 175, CY + 690, "to the road", 11, italic=True, color="#7A5A30")

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

# manifest: the field envelope + every watercourse, for the checks that come later
_env = [[round(x, 1), round(y, 1)] for x, y in net["envelope"]]
_exs = [p[0] for p in _env]
_eys = [p[1] for p in _env]
s.M["fields"].append({"name": "hoshigaoka-paddies", "kind": "paddy", "outline": _env,
                      "bbox": [min(_exs), min(_eys), max(_exs), max(_eys)]})
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

s.label(pcx, pcy - pry - 12, "irrigation pond", 11, italic=True, color="#5C7488")
s.title("Hoshigaoka (WIP: water + fields)")
s.compass()
s.finish(os.path.join(HERE, "hoshigaoka"))
print(f"paddy acres: {net['acres']:.1f}  plots: {len(net['plots'])}")
