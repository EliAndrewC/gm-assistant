#!/usr/bin/env python3
"""Kikuta - an average farming village, REGENERATED FROM SCRATCH on the feature-005 ROLL ENGINE.

Everything about this village except two fixed facts is ROLLED from the seed: the cluster's position and
shape, the internal lane skeleton (and so the headman's seat), the water source, the paddy grain and plot
texture, the field archetype and any land-use overlay. No coordinate below was chosen by hand - the knobs
pick them (`s.roll_village`), which is the whole point of the knob engine.

The two FIXED facts, both GM-set:
  1. NW-high -> the water falls to the SOUTH-EAST (`down_deg=45`).
  2. The Shrine to Benten is approached by a SEVEN-TORII sando, with the village burial ground in the same
     precinct (the priestess performs the funerary rites) - this is what keeps Kikuta Kikuta.

The seed was chosen only so the rolled combination lands a clean, gate-passing map; the combination itself
was not steered.
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, SKILL)
from settlement import Settlement, knob_rng  # noqa: E402

W, H = 3400, 3100
SEED = 41

# even the SPEC-level dials are rolled, not chosen: the household count (a village band) and whether the
# valley is fed by a tameike or a diverted stream.
HOUSEHOLDS = knob_rng(SEED, "households").randrange(46, 70)
WATER_KIND = "pond" if knob_rng(SEED, "water_kind").random() < 0.5 else "stream"

s = Settlement(W=W, H=H, seed=SEED)
s.meta(name="Kikuta", scale="village", ftpx=2, toscale=True, households=HOUSEHOLDS, down_deg=45, nucleated=True, field_footbridges=True, torii_expected=7, shrine_on_hill=False)

# ROLL the whole village. civic_shrine=False + frame=False: this gen supplies Kikuta's OWN sacred precinct
# (the Benten hall + its 7 torii + the burial ground) and crops the frame itself, AFTER placing them.
# lay_hinterland=False: defer the scrub/marsh scatter until AFTER the Benten precinct below registers its
# swept-ground clearings (the hall, the 7 torii, the burial ground), so the scrub reads cleared around them.
knobs = s.roll_village("Kikuta", households=HOUSEHOLDS, down_deg=45, water_kind=WATER_KIND, field_fall=1500, civic_shrine=False, frame=False, lay_hinterland=False)
print("rolled:", {k: v for k, v in knobs.items() if k not in ("cluster", "gateway", "field_bbox")})

# --- THE BENTEN PRECINCT (the one hand-sited thing, because the GM fixes it) -------------------------
# Sited RELATIVE to the rolled village: on the dry ground AWAY from the paddy, just beyond the cluster's
# downslope gateway, so the sando runs out of the village toward the off-map approach.
_ccx, _ccy, _cex, _cey = knobs["cluster"]
_fx0, _fy0, _fx1, _fy1 = knobs["field_bbox"]
_fcx, _fcy = (_fx0 + _fx1) / 2, (_fy0 + _fy1) / 2
_a0x, _a0y = _ccx - _fcx, _ccy - _fcy  # cluster-from-field: the "away from the paddy" direction
_al = math.hypot(_a0x, _a0y) or 1.0
_a0x, _a0y = _a0x / _al, _a0y / _al
_gx, _gy = knobs["gateway"]


_pts_solid = [(o["x"], o["y"]) for grp in ("houses", "wells") for o in s.M.get(grp, [])]
_rect_solid = [(o["x"], o["y"], o.get("w", 0.0) / 2 + 40, o.get("h", 0.0) / 2 + 40) for grp in ("groves", "village_groves") for o in s.M.get(grp, [])]


def _precinct_fits(bx, by, dx_, dy_):
    """The whole precinct - hall, the 7-torii sando running back toward the village, and the burial ground -
    must sit inside the canvas with room for its labels, off the paddy, and SET APART from the village fabric
    (the rolled houses, the windbreak grove and the wells are already down, so it has to find clear ground)."""
    pts = [(bx, by), (bx - dx_ * 290, by - dy_ * 290), (bx + dx_ * 150 + dy_ * 120, by + dy_ * 150 - dx_ * 120)]
    if not all(210 < px < W - 210 and 180 < py < H - 140 for px, py in pts):
        return False
    if any(_fx0 - 50 < px < _fx1 + 50 and _fy0 - 50 < py < _fy1 + 50 for px, py in pts):
        return False  # off the paddy
    if any(math.hypot(px - sx, py - sy) < 155 for px, py in pts for sx, sy in _pts_solid):
        return False  # clear of every house + well
    return not any(abs(px - gx) < gw and abs(py - gy) < gh for px, py in pts for gx, gy, gw, gh in _rect_solid)  # out of the groves


# sweep heading x distance for every seat where the whole precinct lands on clear, dry, on-canvas ground, and
# take the one CLOSEST to the village - set apart, but still plainly Kikuta's shrine rather than a lone hall
# stranded out in the scrub.
_cands = []
for _dist in (300, 400, 520, 660, 820, 1000, 1200):
    for _turn in range(0, 360, 12):
        _t = math.radians(_turn)
        _cx_, _cy_ = _a0x * math.cos(_t) - _a0y * math.sin(_t), _a0x * math.sin(_t) + _a0y * math.cos(_t)
        _b = (round(_gx + _cx_ * _dist), round(_gy + _cy_ * _dist))
        if _precinct_fits(_b[0], _b[1], _cx_, _cy_):
            _cands.append((math.hypot(_b[0] - _ccx, _b[1] - _ccy), _cx_, _cy_, _b))
if _cands:
    _cands.sort(key=lambda c: c[0])
    _ax, _ay, BEN = _cands[0][1], _cands[0][2], _cands[0][3]
else:  # pragma: no cover - the sweep finds a seat on any sane canvas
    _ax, _ay, BEN = _a0x, _a0y, (round(_gx + _a0x * 460), round(_gy + _a0y * 460))

# the 7 TORII march down the sando AWAY from the hall, back toward the village approach
_ux, _uy = -_ax, -_ay
_torii = [(round(BEN[0] + _ux * d), round(BEN[1] + _uy * d)) for d in range(58, 58 + 7 * 36, 36)]
s.shrine_hall(BEN[0], BEN[1], "Shrine to Benten", "(Sister Baika's care)", w=44, h=30, kind="shrine", primary=True, torii=_torii, graveyard=False)
s.shrine_well(round(BEN[0] - _uy * 46), round(BEN[1] + _ux * 46))  # the priestess's ablution well, beside the hall
# the village burial ground shares the precinct but stands clear of the hall + the sando
s.cemetery(round(BEN[0] + _ax * 96 - _uy * 104), round(BEN[1] + _ay * 96 + _ux * 104), 46, 32, parish=False, organic=True, label="village burial ground")  # resized 2026-07-19: a ~350-person village ground is ~0.1-0.25 acre (~92x64 ft at 2 ft/px), not 0.5+ - see settlements.md funerary anchors

s.hinterland()  # NOW lay the scrub + marsh - after the precinct's clearings are registered, so it reads swept around the shrine/torii/graves

s.crop_to_content(margin=40)
s.title("Kikuta")
print(s.finish(os.path.join(HERE, "kikuta-village")))
