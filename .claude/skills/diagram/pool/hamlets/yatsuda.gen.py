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
SKILL = os.path.dirname(os.path.dirname(HERE))
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

# n_bands=48 steps the valley floor down in ~42 ft cross-bunds, and each band splits across the width into
# ~0.05-acre leveled cells (build_ribbon + settlements.md 'Paddy cell size'). ftpx=1 (a 1 ft/px hamlet).
net = build_ribbon(W, H, TOP, SEED, down_deg=90, length=2000, width=300, n_bands=48, ftpx=1)
s.field_polys.append([(round(x, 1), round(y, 1)) for x, y in net["envelope"]])
s.meta(dry_furrows_vary=False)

sluice = net["channels"][0]["pts"][0]
s.draw_comb_field(net, "yatsuda-ribbon", {"kind": "pond", "pond": (sluice[0] - 4, sluice[1] - 62, 74.0, 48.0)})

# the hamlet lines the dry shoulder EAST of the narrow valley ribbon
_rng = _random.Random(SEED ^ 0x3B)
_env = net["envelope"]
_ex = max(p[0] for p in _env)
_fcy = (
    min(p[1] for p in _env) + max(p[1] for p in _env)
) / 2  # y-extent MIDPOINT, robust to envelope sampling density (the vertex MEAN shifts when the ribbon subdivides into more bands, which moved the cluster onto a lane)
CX, CY = _ex + 150, _fcy - 10
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
# the windbreak belt is derived from the ACTUAL house extents (not fixed CX/CY offsets), so it nestles against
# the cluster's north edge by construction and carries enough clumps regardless of how the cluster packs - the
# finer ribbon field shifted the cluster enough that the old fixed band drew too few clumps to count as embracing
_belt = [(_hx[0] - 24, _hy[0] - 92), (_hx[-1] + 24, _hy[0] - 92), (_hx[-1] + 24, _hy[0] + 28), (_hx[0] - 24, _hy[0] + 28)]
s.village_grove(_belt, role="windbreak")
s.bridges()
if s.M.get("field_ditches"):
    s.channel_footbridges(spacing=320)
s.hinterland()  # a narrow ribbon leaves plenty of dry valley-side ground to clothe
s.crop_to_content(margin=44)
s.title("Yatsuda")
print(s.finish(os.path.join(HERE, "yatsuda")))
