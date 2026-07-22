#!/usr/bin/env python3
"""Kuwabata (榎田) - a POLDER-grid village (feature 005 US4 field_archetype='polder_grid').

A second field-GEOMETRY archetype: a rectilinear block on flat reclaimed LOW ground - a straight ditch-grid
module whose bays subdivide into a varied parcel patchwork - inside a perimeter dike (China-first: the wei-tian 圩田 polders of the
lower-Yangtze lake plains - the planned, surveyed opposite of the organic valley comb). Water enters the
high corner, a perimeter feeder supplies the grid, and it drains to the low corner; the village lines the
dry perimeter dike on the east side.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, SKILL)
from settlement import Settlement  # noqa: E402
import random as _random  # noqa: E402

from waterfields import build_polder  # noqa: E402

W, H = 2200, 2600
SEED = 21
ORIGIN = (360, 320)  # the high (NW) corner; the grid runs S (down) and E (across)

s = Settlement(W=W, H=H, seed=SEED)
s.meta(name="Kuwabata", scale="hamlet", ftpx=1, toscale=True, households=16, down_deg=90, terrain="low", field_archetype="mulberry_dike_fishpond", nucleated=True, field_footbridges=True)
s._nucleated = True

# TRUE SCALE (1 px = 1 ft): traditional dike-ponds were 0.4-0.6 ha oblongs with 6-10 m mulberry dikes
# (build_polder docstring, TRUE-SCALE SIZING) - so a 160 ft module, merge-heavy mix (most ponds 160x320
# ~0.48 ha, square ~2.4-mu minority), and 22 ft dike gaps.
net = build_polder(W, H, ORIGIN, SEED, down_deg=90, rows=10, cols=6, cell=160, parcel_mix=(0.10, 0.0, 0.60), gap=(11.0, 11.0), edge_wander=0.4)
s.field_polys.append([(round(x, 1), round(y, 1)) for x, y in net["envelope"]])
s.meta(dry_furrows_vary=False)

# the PERIMETER DIKE - the defining polder feature, an irregular hand-piled EARTHWORK BAND following the
# natural water edge in organic non-square bends (fish-scale polder 鱼鳞圩; see s.perimeter_dike +
# settlements.md 'Perimeter dike'). Drawn FIRST (a ground layer): the fields + ring canal draw ON TOP, so
# the ring reads running along the dike's inner toe and the inlet/outfall channels read as SLUICES cutting
# THROUGH the dike (water crosses the dike only there); the east-side houses draw on top later.
_env = net["envelope"]
s.perimeter_dike(_env, seed=SEED ^ 0x6D, gaps=net["dike_sluices"])

# the water SOURCE is a header reservoir (the wild water the inlet sluice draws from) sitting OUTSIDE
# the dike above the high (NW) corner - the feeder ring canal is charged through a sluice in the dike
_nw = net["envelope"][0]
s.draw_comb_field(net, "kuwabata-polder", {"kind": "pond", "pond": (_nw[0] + 44, _nw[1] - 104, 82.0, 54.0)})
# THE DIKE-POND SYSTEM: convert (almost) every cell to a fish pond rimmed by a mulberry dike (桑基魚塘)
import random as __r

# eligible="all": this map IS the wholesale-conversion end state (the ARCHETYPE), the rare case where a
# whole district went over to ponds and bought its grain in - so the ponds engulf the ordinary ground too,
# not just the low hollows. Everywhere else the overlay is topographically filtered. See research.md D2.
s.apply_land_use(net, "mulberry_fishpond", __r.Random(SEED ^ 0x55), fraction=0.9, eligible="all")

# the village lines the dry EAST perimeter dike
_rng = _random.Random(SEED ^ 0x3B)
_ex = max(p[0] for p in _env)
_fcy = sum(p[1] for p in _env) / len(_env)
CX, CY = _ex + 120, _fcy + 20  # hug the (edge-wandered) east dike a touch closer so >=5 houses ring the field
# reserve a WINDWARD GAP over the NORTHERN third of the cluster (a no-build strip east of the dike): the
# north houses shift east to leave room for the NW windbreak, while the south houses still hug the field
# (field_ringed). This is the only way to fit a west windbreak against an east-dike village facing the ponds.
_dike_e0 = max(p[0] for p in s.M["dikes"][0]["outline"])
s.block_polys.append([(_dike_e0, CY - 300), (_dike_e0 + 96, CY - 300), (_dike_e0 + 96, CY - 70), (_dike_e0, CY - 70)])
s.lane_skeleton("spine", CX, CY, 150, 300, clearance=34)
_seeds = s.cluster_seeds("elongated", CX, CY, 180, 320, 90, _rng)
_placed = 0
for _x, _y in _seeds:
    if _placed >= 16:
        break
    if s.try_place(_x, _y, "plain"):
        _placed += 1
n_farms = s.farmsteads()
print(f"farmhouses: {n_farms}")

_hs = s.M["houses"]
if _hs:
    _hx = sorted(h["x"] for h in _hs)
    _hy = sorted(h["y"] for h in _hs)
    s.place_wells((_hx[0] - 10, _hy[0] - 10, _hx[-1] + 10, _hy[-1] + 10), spacing=180, near=120)
# the fengshui WINDBREAK wraps the cluster's WINDWARD (NW) fringe - the cold winter monsoon blows from the
# NW (windward default), so the belt is an L covering the NORTH end AND the WEST side of the house strip
# (GM 2026-07-22: a purely-north belt left the west of the farmhouses exposed). The west arm sits in the
# gap between the houses and the dike, blocking the wind that crosses the ponds; both arms stay off the dike.
_hx0 = min(h["x"] - h["w"] / 2 for h in s.M["houses"])
_hx1 = max(h["x"] + h["w"] / 2 for h in s.M["houses"])
_hy0 = min(h["y"] - h["h"] / 2 for h in s.M["houses"])
_hy1 = max(h["y"] + h["h"] / 2 for h in s.M["houses"])
_warm0, _warm1 = _dike_e0 + 6, _dike_e0 + 92  # the west arm fills the reserved windward gap (north third)
_belt = [(_warm0, _hy0 - 96), (_hx1 + 46, _hy0 - 96), (_hx1 + 46, _hy0 - 44), (_warm1, _hy0 - 44), (_warm1, CY - 80), (_warm0, CY - 80)]  # L: north arm + west arm down the gap
s.village_grove(_belt, role="windbreak")
s.bridges()
if s.M.get("field_ditches"):
    # crossings CLUSTER on the settlement (east) side, sparse on the interior laterals, NONE on the unsettled
    # feeder / far toe / drain (research 2026-07-22, settlements.md 'Polder ring canal'): people cross to the
    # fields where they live and then walk the bund network, so plank counts are capped per ring side.
    s.channel_footbridges(spacing=320, seg_caps={"feeder": 0, "w_toe": 0, "drain": 0, "e_toe": 3, "lateral": 1})
s.hinterland(interior_fill=False)  # a polder is a SOLID block - no interior voids to clothe
s.crop_to_content(margin=44)
s.title("Kuwabata")
print(s.finish(os.path.join(HERE, "kuwabata")))
