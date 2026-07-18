#!/usr/bin/env python3
"""Yatsuda (谷津田) - a RIBBON-VALLEY hamlet (feature 005 US4 field_archetype='ribbon_valley').

A second field-GEOMETRY archetype: a rectilinear block of large regular paddies on flat reclaimed LOW
ground, an orthogonal ditch grid inside a perimeter dike (China-first: the wei-tian 圩田 polders of the
lower-Yangtze lake plains - the planned, surveyed opposite of the organic valley comb). Water enters the
high corner, a perimeter feeder supplies the grid, and it drains to the low corner; the village lines the
dry perimeter dike on the east side.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, SKILL)
from settlement import Settlement  # noqa: E402
import random as _random  # noqa: E402

from waterfields import build_ribbon  # noqa: E402

W, H = 1700, 2800
SEED = 9
TOP = (820, 300)  # the valley head; the ribbon meanders S down the valley floor

s = Settlement(W=W, H=H, seed=SEED)
s.meta(name="Yatsuda", scale="hamlet", ftpx=1, toscale=True, households=16, down_deg=90, terrain="narrow_valley", field_archetype="ribbon_valley", nucleated=True, field_footbridges=True)
s._nucleated = True

net = build_ribbon(W, H, TOP, SEED, down_deg=90, length=2000, width=300, n_bands=24)
s.field_polys.append([(round(x, 1), round(y, 1)) for x, y in net["envelope"]])
s.meta(dry_furrows_vary=False)

sluice = net["channels"][0]["pts"][0]
s.draw_comb_field(net, "yatsuda-ribbon", {"kind": "pond", "pond": (sluice[0] - 4, sluice[1] - 62, 74.0, 48.0)})

# the hamlet lines the dry shoulder EAST of the narrow valley ribbon
_rng = _random.Random(SEED ^ 0x3B)
_env = net["envelope"]
_ex = max(p[0] for p in _env)
_fcy = sum(p[1] for p in _env) / len(_env)
CX, CY = _ex + 150, _fcy + 10
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
s.hinterland()  # a narrow ribbon leaves plenty of dry valley-side ground to clothe
s.crop_to_content(margin=44)
s.title("Yatsuda")
print(s.finish(os.path.join(HERE, "yatsuda")))
