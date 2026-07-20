#!/usr/bin/env python3
"""Akagahara (赤ヶ原, "red plain") - a DISPERSED HAMLET on red-clay ground, the to-scale bundle at 1 ft/px.

A test map for the feature-005 `settlement_form="dispersed"` archetype (the kainyo strewn-farmstead
pattern): a hamlet of 15 households whose farmsteads are STREWN around the field's dry margins - RINGING
the paddy, each on its own dry patch nestled in its own yashikirin windbreak grove (there is no communal
wood). Like any hamlet it has NO headman of its own (its overseer, the district headman, lives in the
main village), NO shrine, NO tax-free plots, and NO graveyard (its dead go to the district burial ground).
The farms RING the field because a dispersed farm needs ~2x the margin room of a nucleated one (its own
grove + real spacing, no tight packing), so 15 will not fit strewn down one margin of a correctly-sized
(~20-acre) field - they dot the N + W + E dry edges instead. Placement hugs the smoothed field outline
(offset outward ~64px so each farm is field-adjacent); try_place drops any that land on the wet S toe.

THE NAME (赤 aka = red, 原 hara = plain/moor): Akagahara sits on iron-rich RED CLAY - the surrounding
non-arable ground (the cut-over hill margins, the dry-field soil, the back-slopes) reads red-brown,
the tell that names the place. A red-clay ground wash is laid UNDER the crops + scrub, so the paddy
green and the grass glyphs sit on red earth while the flooded field stays green.

SCALE: a hamlet is drawn at 1 ft/px (ftpx=1), twice the pixel-scale of a village, so the same 46x28 ft
minka is 46px here. `toscale=True` opts it into the to-scale homestead bundle path. The land falls
gently N(high) -> S(low); a northern brook feeds the comb head and the field drains S into a small
tameike reservoir at its low foot.
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

W, H = 1900, 2680                    # tall: the N-high -> S-low valley; zoomed in (1 ft/px). Roomy so 15 DISPERSED farms fit
SEED = 16
SLUICE = (760, 320)                  # the field head, upper-left; the comb fans S, farms strewn along the long W margin
FTPX = 1

s = Settlement(W=W, H=H, seed=SEED)
s.meta(name="Akagahara", scale="hamlet", ftpx=FTPX, toscale=True, households=15, down_deg=90,   # N-high -> downhill = due S
       nucleated=False, field_footbridges=True, pond_role="drainage")   # DISPERSED farmsteads; the pond DRAINS the field (a reservoir below)

# Comb supply net marching due S from the head sluice. field_fall sizes the paddy to ~15 households (~20 acres)
# and gives a LONG W margin so the 15 dispersed farmsteads (each ~2x a nucleated one's room) all fit.
# field_fall is sized to what the comb ACTUALLY fills (the plots stop at y~1665 whatever we declare). Declaring
# more (this was 1440) buys no rice - it only extends the field ENVELOPE ~180px past the last plot, and since
# the envelope is what house-adjacency is measured against, that phantom tail let the placement solver strand
# farmsteads well SOUTH of the visible paddy while still reading as "field-adjacent". Keep envelope ~= rice.
net = build_comb(W, H, SLUICE, SEED, down_deg=90, field_fall=1260,
                 offtakes_a=(0.32, 0.7), offtakes_b=())   # a SPARSE delivery net for a small field
s.meta(dry_furrows_vary=net["furrows_vary"])

s.field_polys.append([(round(x, 1), round(y, 1)) for x, y in net["envelope"]])
for _dp in net["dry_plots"]:
    s.block_polys.append(_dp["poly"])
s._nucleated = False   # DISPERSED: each strewn farmstead draws its OWN yashikirin windbreak grove (no communal wood)

# RED-CLAY GROUND (赤): a warm iron-red wash UNDER the whole map, so the bare hill margins + dry-field soil
# read red-brown (the tell that names Akagahara), while the flooded paddy + pond are drawn OVER it in green/
# blue. Laid first, before the crops. Kept slightly translucent so the parchment tooth still shows through.
RED_CLAY = '#C58A63'
s.add(f'<rect width="{W}" height="{H}" fill="{RED_CLAY}" opacity="0.5"/>')


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
s.M["fields"].append({"name": "akagahara-paddies", "kind": "paddy", "outline": _env,
                      "bbox": [min(_exs), min(_eys), max(_exs), max(_eys)],
                      "vis_bbox": [min(_pvx), min(_pvy), max(_pvx), max(_pvy)]})
for c in net["channels"]:
    s.M["field_ditches"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in c["pts"]],
                                 "role": c["role"], "field": "akagahara-paddies",
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
                        "frm": {"kind": "stream"}, "to": {"kind": "field", "name": "akagahara-paddies"}, "w": 2.5})

# FARMHOUSES: Akagahara is DISPERSED (feature 005 settlement_form) - its ~11 farmsteads are STREWN along the
# field's high W margin, each a standalone homestead nestled in its OWN yashikirin windbreak grove (drawn
# per-house since s._nucleated=False), rather than packed into one nucleus. NO HEADMAN (the district headman
# lives in the main village). A single CONNECTOR track winds S through the strewn farms and off-map. Sized to
# ~11 so the dispersed farms + their groves fit the margin (a dispersed farm needs ~2x a nucleated one's room).
_rng = _random.Random(SEED + 1)
s.lane([(345, 300), (318, 840), (292, 1440), (266, 2040), (242, 2560), (222, 2740)], width=6, clearance=30, worn=True, connector=True)   # winds S down the far-W back-slope (clear of the farm groves), off the bottom edge (H=2680)
s.meta(settlement_form="dispersed", grove_prevalence=0.6)   # ~60% of the strewn farms carry a grove (still clearly dispersed); the open-yard farms pack without shading a neighbor
# Strew the farms across the field's high W margin as a DEEP 2D scatter (`scatter_seeds`): the 165px adjacency
# band is wide enough to stagger them ~1.5 rows, so they read STREWN (an irregular scatter), NOT a single
# straight edge-line - plus a few at the N head by the sluice. The homesteads concentrate on the dry W margin -
# NOT because it is higher (the land falls due S, so the W margin sits at the same height as the rice due E of
# it) but because the comb's fan does not deliver water there: it is land at paddy elevation that stays
# unirrigated, hence buildable. None crowd the wet S toe, which is the genuinely low ground.
# Filtered to genuine field-adjacency, off the head-race, and ABOVE the visible paddy (no farm past the rice).
_env2 = list(net["envelope"])
# Measure adjacency against the DRAWN RICE, never the field envelope. The envelope carries an invisible
# TAIL past the last plot (it exists only to block houses), so a farm hugging that tail sits well SOUTH of
# the actual rice while still reading as "field-adjacent" - that is exactly how farms ended up stranded
# below the paddy. A point-cloud of the plot vertices is the honest test of "is this farm beside the rice".
_rice_pts = [(v[0], v[1]) for p in net["plots"] for v in p["poly"]]


def _beside_rice(_qx, _qy):
    """A farm sits BESIDE the rice it works: close to real rice, and not stranded below the field's local edge.

    Both halves are needed, and BOTH must be measured against the drawn plots. The field is a FAN, so its
    southern extent is x-dependent - a single global "north of the paddy's bbox bottom" cap passes farms that
    are far below the rice on the narrow W margin, which is exactly what went wrong here.
    """
    _near = [(_rx, _ry) for _rx, _ry in _rice_pts if abs(_rx - _qx) < 110 and abs(_ry - _qy) < 110]
    if not _near:
        return False
    # 60px, NOT the gate's 165px band: the homestead-bundle solver shifts a placed house by up to ~90px to fit
    # its yard/garden/grove, so a seed parked at the edge of the band lands stranded. Seed well inside it.
    if min(math.hypot(_qx - _rx, _qy - _ry) for _rx, _ry in _near) > 88:
        return False
    # Not below the field's LOCAL southern edge: some nearby rice must lie at (or south of) the farm's own
    # latitude. If every scrap of rice near a farm is well NORTH of it, that farm is hanging off the bottom
    # of the paddy - the "line of farmhouses stretching further south than the rice" artifact.
    return any(_ry > _qy - 20 for _rx, _ry in _near)


_fcx = sum(p[0] for p in _env2) / len(_env2)
_fcy = sum(p[1] for p in _env2) / len(_env2)
_seeds = []
for _rep in range(10):
    for _px, _py in _env2:
        _d = math.hypot(_px - _fcx, _py - _fcy) or 1.0
        _off = _rng.uniform(40, 86)   # VARIED depth so the farms STAGGER (a strewn scatter), not a straight edge-line
        _seeds.append((_px + (_px - _fcx) / _d * _off + _rng.uniform(-24, 24), _py + (_py - _fcy) / _d * _off + _rng.uniform(-24, 24)))
_seeds = [
    (_x, _y)
    for _x, _y in _seeds
    if not (540 < _x < 1560 and _y > 1430)  # off the low-middle S toe below the drain (marsh / low paddy / pond)
    and not (690 < _x < 830 and _y < 480)  # off the head-race corridor by the sluice (a farm's byre must not land on it)
    and _beside_rice(_x, _y)  # beside REAL rice, and never hanging off the paddy's southern edge
]
_rng.shuffle(_seeds)
_placed = 0
for _x, _y in _seeds:
    if _placed >= 15:
        break
    if s.try_place(_x, _y, "plain"):
        _placed += 1
n_farms = s.farmsteads()
print(f"farmhouses: {n_farms}")

# COMMUNAL WELLS + shared draft-animal BYRES among the dwellings (a hamlet keeps a couple of draw-wells and
# ~one byre per 4-5 households). Placed AFTER the houses (they slot into the courtyards), BEFORE the grove.
# wells serve the DENSE W-margin cluster (the E/N ring farms draw from the field ditches beside them); a
# bbox spanning the whole ring would scatter wells out over the paddy
_wf = [h for h in s.M["houses"] if h["x"] < 640]
_wx = sorted(h["x"] for h in _wf)
_wy = sorted(h["y"] for h in _wf)
s.place_wells((_wx[1] - 10, _wy[1] - 10, _wx[-2] + 10, _wy[-2] + 10), spacing=215, near=185)
n_byres = s.draft_byres(fraction=0.22, gap=60)
print(f"byres: {len(n_byres)}")

# HINTERLAND - the non-arable land: a reed MARSH at the low downhill TOE (below the paddy's drainage line, around
# the tameike) and the cut-over SCRUB commons (grass + a few scraggly pines) filling the surrounding margins, the
# DOMINANT denuded-hill cover (China-first: the south-China rice hills were stripped for fuel/timber over centuries;
# the fengshui grove is the green exception). Drawn BEFORE the windbreak grove; the scatter skips fields/pond/lanes/
# houses + a hamlet keep-out, and bleeds off-frame so the crop stays tight.
s.hinterland()   # scrub ring + contour-band marsh + interior fill; the interior fill clothes the comb fan's open
# corners (both the NE upland and the SW void by the drain) automatically, so no hand-added scrub quad is needed.
# ... plus a FEW managed-WOODLAND patches (coppice / bamboo / tung-oil "economic forest") on the higher/farther
# ground, SET BACK from the sun-needing crops by the scrub between: two on the NE upland, one on the W back-slope
# beyond the fengshui grove. Woodland is the green EXCEPTION here, not the dominant cover. Drawn on top of the scrub.
for _patch in [[(1240, 150), (1600, 150), (1600, 330), (1240, 330)],      # N upland coppice, ABOVE the field head
               [(1750, 400), (1880, 400), (1880, 820), (1750, 820)]]:      # far-E coppice, clear of the field's E edge
    # (positioned clear of the crops + the W-margin dispersed farms; no W back-slope wood - the farms + their
    #  per-house groves occupy that ground)
    s.commons(_patch, role="woodland")

# DISPERSED (feature 005): NO communal windbreak - each strewn farmstead carries its OWN yashikirin grove
# (drawn per-house by farmsteads() since s._nucleated=False), which IS the dispersed pattern's shelter. A
# communal wood or copse-scatter would only collide with the far-flung per-house groves + the field.

# PLANK FOOTBRIDGES across the irrigation ditches (field-workers crossing on the bunds; not tied to a lane)
n_bridges = s.channel_footbridges(spacing=300)
print(f"footbridges: {n_bridges}")

# CROP to the placed content (the commons bleeds off-frame; the hard features fit with a margin)
s.crop_to_content(margin=48)   # a touch wider so the strewn ring's edge wells sit inside the frame (and more red-clay margin shows)

# NO SHRINE (religious_matches_scale: a hamlet has none), NO GRAVEYARD (its dead go to the village district's
# burial ground), NO TAX-FREE plots - a hamlet is a bare cluster of farms under a distant headman.

_ACRES = sum(abs(sum(p["poly"][i][0] * p["poly"][(i + 1) % len(p["poly"])][1]
                     - p["poly"][(i + 1) % len(p["poly"])][0] * p["poly"][i][1]
                     for i in range(len(p["poly"])))) / 2 for p in net["plots"]) * FTPX * FTPX / 43560

s.title("Akagahara")
print(s.finish(os.path.join(HERE, "akagahara")))
print(f"paddy acres (at {FTPX} ft/px): {_ACRES:.1f}  plots: {len(net['plots'])}  households: {n_farms}")
