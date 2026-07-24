#!/usr/bin/env python3
"""Tanada (棚田) - a terraced HILL hamlet (feature 005 US4 field_archetype='contour_terraces').

The FIRST field-GEOMETRY archetype beyond the valley-bottom comb: stacked contour terraces stepping down
a hillside, the archetype for HILL ground where flat paddy is impossible (China-first: Yuanyang / Longsheng
rice terraces). Water enters at the high catchment, runs down a flank supply channel, and cascades terrace
to terrace to a drain at the foot; the hamlet sits on the dry low-flank shoulder beside the steps.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, SKILL)
from settlement import Settlement  # noqa: E402
import math  # noqa: E402
import random as _random  # noqa: E402

from waterfields import AZE, build_terraces  # noqa: E402

W, H = 1900, 2600
SEED = 5
TOP = (1050, 300)  # the high catchment; terraces step downhill (due S)

s = Settlement(W=W, H=H, seed=SEED)
s.meta(name="Tanada", scale="hamlet", ftpx=1, toscale=True, households=14, down_deg=90, terrain="hill", field_archetype="contour_terraces", nucleated=True, field_footbridges=True)

s._nucleated = True  # communal windbreak, no per-house groves
# n_terraces=32 keeps each step shallow (~44 ft deep) so a cell reads WIDER than deep; each step is then split
# along the contour into ~0.05-acre leveled cells (build_terraces + settlements.md 'Paddy cell size': a real
# terrace is a row of small paddies, Longsheng's largest is 0.62 mu / ~0.10 acre). ftpx=1 (a 1 ft/px hamlet).
net = build_terraces(W, H, TOP, SEED, down_deg=90, n_terraces=32, cross_width=760, fall=1400, ftpx=1)
s.field_polys.append([(round(x, 1), round(y, 1)) for x, y in net["envelope"]])
s.meta(dry_furrows_vary=False)

# the source: a small hillside tank just above the high catchment, feeding the flank supply channel
sluice = net["channels"][0]["pts"][0]
s.draw_comb_field(net, "tanada-terraces", {"kind": "pond", "pond": (sluice[0] - 4, sluice[1] - 62, 74.0, 48.0)})

# the RETAINING BUNDS - the stone/earth lip at each terrace's downhill edge, the defining terrace look
for bl in net["bund_lines"]:
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in bl)
    s.add(f'<polyline points="{pts}" fill="none" stroke="{AZE}" stroke-width="2.6" stroke-linejoin="round" opacity="0.95"/>')
s.M["terrace_bunds"] = [[[round(x, 1), round(y, 1)] for x, y in bl] for bl in net["bund_lines"]]  # for the contour_terraces check

# the hamlet sits on the dry LOW-FLANK shoulder (east side, t=+1), clear of the high-flank supply channel
_rng = _random.Random(SEED ^ 0x7A)
_env = net["envelope"]
_fcx = sum(p[0] for p in _env) / len(_env)
_fcy = sum(p[1] for p in _env) / len(_env)
_ex = max(p[0] for p in _env)  # the terraces' east flank
CX, CY = _ex + 165, _fcy + 40
s.lane_skeleton("spine", CX, CY, 150, 220, clearance=34)
_seeds = s.cluster_seeds("elongated", CX, CY, 190, 300, 90, _rng)
_placed = 0
for _x, _y in _seeds:
    if _placed >= 14:
        break
    if s.try_place(_x, _y, "plain"):
        _placed += 1
n_farms = s.farmsteads()
print(f"farmhouses: {n_farms}")

_hs = s.M["houses"]
if _hs:
    _hx = sorted(h["x"] for h in _hs)
    _hy = sorted(h["y"] for h in _hs)
    s.place_wells((_hx[0] - 10, _hy[0] - 10, _hx[-1] + 10, _hy[-1] + 10), spacing=175, near=118)
# a COMMUNAL windbreak on the cluster's high (north/windward) side, sheltering the hamlet
_belt = [(CX - 170, CY - 300), (CX + 170, CY - 300), (CX + 170, CY - 250), (CX - 170, CY - 250)]
s.village_grove(_belt, role="windbreak")
s.bridges()
if s.M.get("field_ditches"):
    s.channel_footbridges(spacing=300)
s.hinterland()
s.crop_to_content(margin=44)
s.title("Tanada")
print(s.finish(os.path.join(HERE, "tanada")))
