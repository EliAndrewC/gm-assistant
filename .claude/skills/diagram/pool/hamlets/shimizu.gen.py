#!/usr/bin/env python3
"""Shimizu (clear water, pure spring) - a hamlet generated ENTIRELY from a seed (feature 005 US2,
SC-004: zero hand-placed coords).

The spec is minimal: a name, a canvas, a seed, a household count, and the fall direction. Every knob
(cluster_position, cluster_shape, lane_skeleton, water_source_position, plot_size, plot_regularity,
grain_drift) is ROLLED from the seed and DRIVES the geometry through the resolvers - no coordinate in
this file was placed by hand. Its sibling `honda.gen.py` uses a different seed and rolls a visibly
different combination, which is the whole point of the knob engine.

Named for its defining feature: the clean spring-fed pond at the head of the paddy fan, whose still
clear water also suits the lotus plots the seed rolled into the wettest bottom paddies.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, SKILL)
from settlement import Settlement  # noqa: E402

W, H = 2000, 2600
SEED = 7

s = Settlement(W=W, H=H, seed=SEED)
s.meta(name="Shimizu", scale="hamlet", ftpx=1, toscale=True, households=18, field_footbridges=True)
knobs = s.roll_village("Shimizu", households=18, down_deg=90, water_kind="pond", field_fall=1260)
print("rolled:", knobs)
print(s.finish(os.path.join(HERE, "shimizu")))
