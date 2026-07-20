#!/usr/bin/env python3
"""Enokida (榎田) - a POLDER-grid village (feature 005 US4 field_archetype='polder_grid').

A second field-GEOMETRY archetype: a rectilinear block of large regular paddies on flat reclaimed LOW
ground, an orthogonal ditch grid inside a perimeter dike (China-first: the wei-tian 圩田 polders of the
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

from waterfields import BUND, build_polder  # noqa: E402

W, H = 2200, 2600
SEED = 12
ORIGIN = (360, 320)  # the high (NW) corner; the grid runs S (down) and E (across)

s = Settlement(W=W, H=H, seed=SEED)
s.meta(name="Enokida", scale="hamlet", ftpx=1, toscale=True, households=16, down_deg=90, terrain="low", field_archetype="polder_grid", nucleated=True, field_footbridges=True)
s._nucleated = True

net = build_polder(W, H, ORIGIN, SEED, down_deg=90, rows=11, cols=6, cell=150)
s.field_polys.append([(round(x, 1), round(y, 1)) for x, y in net["envelope"]])
s.meta(dry_furrows_vary=False)

sluice = net["channels"][0]["pts"][0]
s.draw_comb_field(net, "enokida-polder", {"kind": "pond", "pond": (sluice[0] - 4, sluice[1] - 62, 82.0, 54.0)})

# the PERIMETER DIKE - a heavier bund ringing the reclaimed block, the defining polder look
_env = net["envelope"]
_dike = " ".join(f"{x:.1f},{y:.1f}" for x, y in _env)
s.add(f'<polyline points="{_dike}" fill="none" stroke="{BUND}" stroke-width="4.4" stroke-linejoin="round" opacity="0.95"/>')

# the village lines the dry EAST perimeter dike
_rng = _random.Random(SEED ^ 0x3B)
_ex = max(p[0] for p in _env)
_fcy = sum(p[1] for p in _env) / len(_env)
CX, CY = _ex + 150, _fcy + 20
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
_belt = [(CX - 160, CY - 380), (CX + 160, CY - 380), (CX + 160, CY - 330), (CX - 160, CY - 330)]
s.village_grove(_belt, role="windbreak")
s.bridges()
if s.M.get("field_ditches"):
    s.channel_footbridges(spacing=320)
s.hinterland(interior_fill=False)  # a polder is a SOLID block - no interior voids to clothe
s.crop_to_content(margin=44)
s.title("Enokida")
print(s.finish(os.path.join(HERE, "enokida")))
