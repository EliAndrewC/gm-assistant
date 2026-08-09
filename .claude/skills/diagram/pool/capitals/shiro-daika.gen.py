#!/usr/bin/env python3
"""Shiro Daika - the DOMAIN CAPITAL of the Daika house (diagram skill, Mode B, 1px = 3ft).

THIS MAP IS A SKELETON, AND THAT IS THE INCREMENT, NOT A DEFECT (feature 019). It draws the
wall, the moat, the river, the ways, the gates and the CASTLE, and stops there. Everything that
fills a city - the rank-graded samurai districts, the commoner machi, the eight lineage
compounds, the two sovereign temples and the teramachi rim, the wharf with its granary and
brokers' row, the aqueduct, the kido mesh - is feature 020. The interior is meant to look empty
at this stage; the castle was built FIRST so the GM could judge its provisional bailey walls off
an early render rather than at the end of a long build.

THE HOUSE. Daika is a Bayushi vassal house of the SCORPION, seated here; Ubame county (see
pool/towns/ubame.gen.py) is one of its county seats, out in Moriguchi province, and the charcoal
road that leaves Ubame westward arrives at this city's EAST gate. Scorpion patron fortunes are
Benten and Jurojin, so the two sovereign temples will be theirs (feature 020).

THE WAYS (GM 2026-08-08, confirmed against the campaign map). The IMPERIAL ROAD enters at the
SOUTH gate, runs north through the city, and beyond the north gate bends NORTHWEST toward Shiro
Kyo. Two unlabeled domain trunk roads leave the other gates: EAST to the Fox lands and the
Kitsune Mori, SOUTHWEST into the heart of the domain. Only the Imperial road is named - an
ordinary road's course is already visible.

THE RIVER runs NORTHEAST -> SOUTHWEST past the city's southeast flank and off both edges. NO
TRUNK ROAD RUNS ALONGSIDE IT: water carried bulk far more cheaply than carts, so a highway
shadowing a navigable river is redundant, and the roads leave in the directions the water does
not serve. What belongs on the bank is a TOWPATH (the Chinese qiandao - upstream haulage, so it
supplements the boats rather than replacing them), and that is feature 020's, with the wharf it
serves. See research/cities/capitals.md, "A river gets a TOWPATH, not a road".

THE CASTLE sits in the ring (castle_seat="ring" - both traditions nest their citadel, so it is
the median form), north of center, with its OTE-MON FACING SOUTH onto the ceremonial approach
that runs down to the Imperial road's south gate. That is the jokamachi rule: the main road
passes the castle's FRONT, "to indicate the glory of the ruler". Its interior is BLANK and stays
blank - see Settlement.castle's docstring for the sync argument.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from citybudget import CapitalProgram, budget_to_manifest, plan_capital  # noqa: E402
from settlement import Settlement  # noqa: E402

s = Settlement(3200, 2700, seed=61)
s.meta(
    water_flow=135,  # DRAINAGE BEARING: the land falls NE -> SW, the way the river runs (0=E, 90=S)
    name="Shiro Daika",
    scale="capital",
    walled=True,
    population=12_360,
    ftpx=3,
    wall_defense="siege",  # the Crab border lies south: built to survive a siege even after a long peace
    imperial_road=True,
    clan="Scorpion",
    capital_dir="northwest",  # Shiro Kyo, and the Imperial road beyond it
    # A SKELETON has no fabric, so the four gates' furniture is the only thing out near the wall
    # and each station reads as an outlier holding the frame open. That is the skeleton showing
    # through, not a siting error - feature 020 fills the interior and they cease to be outliers.
    crop_outlier_ok="The four gates' inspection stations are the only features outside an empty interior at the SKELETON stage (feature 019 draws no fabric); feature 020 fills the quarters and they cease to be outliers.",
)

# ---- BUDGET-FIRST (feature 018): the wall is an OUTPUT of the declared program, never a guess.
# A capital cannot be sized from population the way a provincial city nearly can - a median castle
# alone is ~85% of an entire provincial city's interior.
BUDGET = plan_capital(CapitalProgram(population=12_360, river=True, castle_seat="ring", imperial_granary_seat="wharf"), canvas=(3200, 2700))
s.meta(budget=budget_to_manifest(BUDGET))

CX, CY = 1400, 1200
RX, RY = round(BUDGET.wall.rx), round(BUDGET.wall.ry)
NRING = 20
WALL = [(round(CX + RX * math.cos(-math.pi / 2 + 2 * math.pi * i / NRING)), round(CY + RY * math.sin(-math.pi / 2 + 2 * math.pi * i / NRING))) for i in range(NRING)]
NGATE, EGATE, SGATE, SWGATE = WALL[0], WALL[5], WALL[10], WALL[13]

# ---- the river: NE -> SW past the southeast flank, off both edges. Upstream (NE) first, which is
# the convention every junction-angle rule keys on.
# Held ~200px off the moat at its closest approach: the ring is 1,055x983 px of pushed-out wall,
# and the first cut ran the river straight through the southeast arc.
RIVER = [(3200, 700), (2900, 1150), (2500, 1750), (2100, 2300), (1800, 2700)]
s.river(RIVER)

# ---- the rampart and its four gates, then the moat and the patrol road inside it
s.city_wall(WALL, gates=[NGATE, EGATE, SGATE, SWGATE])
MOAT = s.moat(WALL, gap=26)
RING = s.ring_road(WALL, inset=30)
s.bound = [list(p) for p in RING]

# ---- THE WAYS. The Imperial road runs south gate -> north gate and bends NORTHWEST beyond it
# toward Shiro Kyo; its label sits OUTSIDE the wall, because inside the rampart the same roadway
# is a city street the city maintains, not an Imperial responsibility.
s.road([(SGATE[0], 2700), (SGATE[0], SGATE[1]), (NGATE[0], NGATE[1]), (1310, 150), (980, 0)], label="Imperial Road", label_xy=(SGATE[0] + 150, 2330))
s.road([(EGATE[0], EGATE[1]), (2820, 1130), (3200, 1040)])  # east, to the Fox lands
s.road([(SWGATE[0], SWGATE[1]), (300, 2010), (0, 2170)])  # southwest, into the domain

# ---- THE CASTLE. North of center so the ceremonial approach has room to run south to the gate;
# ote-mon SOUTH, per the jokamachi rule that the main road passes the castle's front. Blank inside.
s.castle(CX, 880, 850, 700, label="Shiro Daika Castle", gate_dir="south")

# ---- the moat CIRCULATES: a closed ring has no upstream end, so the gen names where its water
# enters and where it leaves. The land falls NE -> SW (water_flow=135), so it is fed on the
# northeast arc and drains from the southwest one.
s.moat_flow(MOAT[2], MOAT[12])

# ---- carry every way over the water it crosses. AFTER all roads and water, as bridges() requires.
s.bridges()

# (the Imperial-road farrier and its relay stables belong to feature 020's fabric - see below)

# ---- declared quarters: the interior tiled into zoned wedges split at the crossroads. At the
# skeleton stage these carry no housing - they are what feature 020's packs will fill.
s.quarter([(CX, CY), (CX, 243), (WALL[3][0], WALL[3][1]), (WALL[5][0], WALL[5][1])], "civic")  # NE: the castle's own ground
s.quarter([(CX, CY), (WALL[5][0], WALL[5][1]), (WALL[8][0], WALL[8][1]), (CX, WALL[10][1])], "mixed")  # SE
s.quarter([(CX, CY), (CX, WALL[10][1]), (WALL[13][0], WALL[13][1]), (WALL[15][0], WALL[15][1])], "mixed")  # SW
s.quarter([(CX, CY), (WALL[15][0], WALL[15][1]), (WALL[18][0], WALL[18][1]), (CX, 243)], "mixed")  # NW

# a SKELETON has no satellite features (gate markets, flophouses) to anchor the frame, so the
# aggressive 35px default would crop hard to the moat and leave the ways as stubs. A modest
# uniform margin shows each road running off the edge, and the south side carries the Imperial
# road caption, which finish() seats AFTER the crop and so cannot widen it itself.
s.crop_city(margin=140, south=240)
s.title("Shiro Daika")
s.finish(os.path.splitext(os.path.abspath(__file__))[0].replace(".gen", ""), png_width=4600)
