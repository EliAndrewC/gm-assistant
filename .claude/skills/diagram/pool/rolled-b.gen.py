#!/usr/bin/env python3
"""Rolled-B - a village generated ENTIRELY from a seed (feature 005 US2, SC-004: zero hand-placed coords).

The spec is minimal: a name, a canvas, a seed, a household count, and the fall direction. Every knob
(cluster_position, cluster_shape, lane_skeleton, water_source_position, plot_size, plot_regularity,
grain_drift) is ROLLED from the seed and DRIVES the geometry through the resolvers - no coordinate in
this file was placed by hand. Its twin `rolled-b.gen.py` uses a different seed and rolls a visibly
different combination, which is the whole point of the knob engine.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, SKILL)
from settlement import Settlement  # noqa: E402

W, H = 2000, 2600
SEED = 8

s = Settlement(W=W, H=H, seed=SEED)
s.meta(name="Rolled-B", scale="hamlet", ftpx=1, toscale=True, households=18, field_footbridges=True)
knobs = s.roll_village("Rolled-B", households=18, down_deg=90, water_kind="pond", field_fall=1260)
print("rolled:", knobs)
print(s.finish(os.path.join(HERE, "rolled-b")))
